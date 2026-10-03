#!/usr/bin/env bash
# REVIX image build, qadam 10: rootfs (source -> build -> rootfs).
#
# BU SKRIPT BAJARILMADI, sabab: guard kalibratsiyasi davom etmoqda.
#
# Vosita: `mmdebstrap --mode=unshare` -- ROOT'SIZ.
# NEGA mmdebstrap, live-build EMAS (09-iso-qurilishi.md §2.1):
#   * `lb build` ROOT talab qiladi (chroot egaligi, mknod, mount);
#     mmdebstrap user namespace ichida ishlaydi va root talab QILMAYDI.
#     Shu bilan build vaqtidagi privilegiyali operatsiyalar soni NOLGA
#     tushadi -- 00-pilot-topologiya.md §4 prinsipining to'g'ridan-to'g'ri
#     qo'llanilishi.
#   * mmdebstrap SOURCE_DATE_EPOCH ni tushunadi va apt'ni shunga sozlaydi.
#   * snapshot.debian.org oddiy `deb` satri sifatida beriladi -> pinning
#     hech qanday wrapper talab qilmaydi (§3.1 R1).
#   * hook'lar ko'rinadigan shell fayllar -> ko'rib chiqish yuzasi kichik.
#
# QABUL QILINGAN NARX (09 §2.1): mmdebstrap live image QURMAYDI. U faqat
# rootfs beradi; live-boot, squashfs, bootloader va xorriso qadamlarini biz
# o'zimiz yig'amiz (qadam 30, 40). Bu ko'proq kod va ko'proq xato ehtimoli.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./config.sh
. "$HERE/config.sh"
# shellcheck source=./lib/common.sh
. "$HERE/lib/common.sh"

require_not_root
require_clean_env
require_sde
require_ext4_out "$OUT_DIR"
# TUZATISH (bug #1, #2): mmdebstrap --mode=unshare ning uid map'i
# foydalanuvchining o'z uid'ini map QILMAYDI, demak (a) build yo'li
# namespace ichidan yetib boriladigan va (b) build kataloglari ichkaridagi
# root uchun yozilishi mumkin bo'lishi SHART.
# lib/common.sh:prepare_build_dirs() / require_userns_path() ga qarang.
prepare_build_dirs
# TUZATISH (bug #8): guest build o'rtasida qayta ishga tushishi mumkin
# (07 §4.4). Generatsiya SHU YERDA qayd etiladi; keyingi har bir qadam
# uni tekshiradi va o'zgargan bo'lsa RAD ETADI.
record_generation
require_userns_path "$OUT_DIR"
require_userns_path "$WORK_DIR"
require_disk "$OUT_DIR" "$MIN_FREE_GB"
require_tools mmdebstrap git unshare

# --- manba repo tekshiruvi --------------------------------------------------
#
# NEGA bu yerda tekshiriladi: image ichidagi `.git` doctor #17/#18
# (git_present/git_clean) ning yagona asosi, va u esa 0 FAIL qabul
# mezonining shartidir (09 §4.1). Manba repo buzuq bo'lsa, buni ISO
# qurilgandan KEYIN emas, HOZIR bilish kerak.
[ -d "$REPO_SRC/.git" ] || [ -f "$REPO_SRC/.git" ] \
  || die "REPO_SRC '$REPO_SRC' git repozitoriysi emas"
# TUZATISH (bug #5): clone namespace ICHIDA bajariladi, demak manba repo
# ham namespace ichidan o'qilishi SHART. Tekshiruv BU YERDA, chunki xato
# aks holda paket o'rnatish tugagandan keyin, ~20 daqiqa yo'qotib chiqadi.
require_userns_readable "$REPO_SRC"
SRC_COMMIT="$(git -C "$REPO_SRC" rev-parse HEAD)"
SRC_DIRTY="$(test -z "$(git -C "$REPO_SRC" status --porcelain)" && echo no || echo YES)"
log "manba repo: $REPO_SRC"
log "  commit=$SRC_COMMIT dirty=$SRC_DIRTY"
if [ "$SRC_DIRTY" = "YES" ]; then
  # OGOHLIK, XATO emas: doctor'ning git_clean tekshiruvi ham WARN beradi,
  # FAIL emas -- "pilot iflos daraxtda ishga tushishi mumkin (u exploratory).
  # CONFIRMATORY run toza daraxt talab qiladi" (revix/cli.py:check_git_clean).
  # Image ichidagi clone HEAD'da bo'ladi, demak IMAGE ichida daraxt toza
  # bo'ladi -- lekin u manbadagi commit qilinmagan o'zgarishlarni
  # O'Z ICHIGA OLMAYDI. Bu farq fingerprint'ga yoziladi.
  warn "manba daraxt IFLOS: image faqat HEAD ($SRC_COMMIT) ni oladi, commit qilinmagan o'zgarishlar KIRMAYDI"
fi

# --- ish kataloglari --------------------------------------------------------
#
# TUZATISH (bug #2): eski kod `mkdir -p "$ROOTFS_DIR"` qilib uni OSHKORA
# yaratardi. Natijada katalog egasi tashqi uid 1000 bo'lar, namespace
# ichidagi root (tashqi 100000) esa unga YOZA OLMAS edi. Shuning uchun:
#   * ROOTFS_DIR mmdebstrap'ning O'ZI yaratadi (oldindan yaratilmaydi);
#   * uning ota-katalogi (WORK_DIR) 0777 bo'ladi, ya'ni namespace ichidagi
#     root yozishi, tashqi foydalanuvchi esa o'qishi mumkin.
# Eski rootfs'ni o'chirish ham namespace ICHIDA bajariladi: fayllar tashqi
# uid 100000 ga tegishli va 0700 kataloglar bor -- tashqaridan `rm -rf`
# "Permission denied" beradi.
if [ -e "$ROOTFS_DIR" ]; then
  log "eski rootfs o'chiriladi (namespace ichida): $ROOTFS_DIR"
  ns_run rm -rf "$ROOTFS_DIR"
fi

# --- apt pinning: snapshot --------------------------------------------------
#
# NEGA Check-Valid-Until=false: snapshot arxividagi `Release` fayli
# o'zining `Valid-Until` muddatini allaqachon o'tkazib yuborgan bo'ladi
# (snapshot -- muzlatilgan nusxa). Busiz apt arxivni rad etadi va pinning
# umuman ishlamaydi. Bu imzo tekshiruvini O'CHIRMAYDI -- faqat muddat
# tekshiruvini (09 §3.1 R1).
APT_OPTS=(
  '--aptopt=Acquire::Check-Valid-Until "false"'
  '--aptopt=Acquire::Retries "3"'
  '--aptopt=APT::Install-Recommends "false"'
  '--aptopt=APT::Install-Suggests "false"'
)

# NEGA --variant=important: minbase'dan kattaroq (systemd uchun kerak),
# lekin standard'dan kichik -- o'lchovga aralashadigan fon xizmatlari
# qo'shilmasin. PREREGISTRATION.md §8 confound nazorati: image ichida
# kutilmagan fon yuki bo'lmasligi kerak.
#
# NEGA --hook-dir YO'Q, hook'lar aniq nomlari bilan beriladi: tartib
# MUHIM va katalogdagi tartib locale'ga bog'liq bo'lishi mumkin
# (determinizm, 09 §3.1 R4).
# Hook'lar mmdebstrap'ning unshare namespace'i ichida ishlaydi (u yerda biz
# MAPPED root'miz -- shuning uchun `chown` ishlaydi va shuning uchun butun
# build root'siz bo'ladi). Ularga kerakli qiymatlar env orqali uzatiladi.
# NEGA env, argument emas: hook satrlari mmdebstrap tomonidan shell'ga
# beriladi, demak uzun argument ro'yxati quoting xatolariga olib keladi.
export REVIX_REPO_SRC="$REPO_SRC"
export REVIX_SRC_COMMIT="$SRC_COMMIT"
export REVIX_INSTALL_PREFIX="$INSTALL_PREFIX"
export REVIX_MEASURE_USER="$MEASURE_USER"
export REVIX_MEASURE_UID="$MEASURE_UID"
export REVIX_PACKAGING_DIR="$REPO_SRC/packaging"
export REVIX_OOMD_INSTALLED="$OOMD_INSTALLED"

log "mmdebstrap: suite=$SUITE arch=$ARCH mirror=$MIRROR"
log "BU QADAM BAJARILMADI (guard kalibratsiyasi davom etmoqda)."

if [ "${REVIX_ISO_CONFIRM:-}" != "yes" ]; then
  die "to'xtatildi (fail-closed). Bajarish uchun: REVIX_ISO_CONFIRM=yes"
fi

mmdebstrap \
  --mode=unshare \
  --format=directory \
  --variant=important \
  --arch="$ARCH" \
  "${APT_OPTS[@]}" \
  --include="$(printf '%s' "$PKGS_ALL" | tr -s ' ' ',')" \
  --customize-hook="$HERE/hooks/customize-10-revix.sh \"\$1\"" \
  --customize-hook="$HERE/hooks/customize-20-systemd.sh \"\$1\"" \
  --customize-hook="$HERE/hooks/customize-90-normalize.sh \"\$1\"" \
  "$SUITE" \
  "$ROOTFS_DIR" \
  "deb $MIRROR $SUITE main"

log "rootfs tayyor: $ROOTFS_DIR"
log "Keyingi qadam: bash iso/20-record-manifest.sh"
