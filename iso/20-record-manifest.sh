#!/usr/bin/env bash
# REVIX image build, qadam 20: paket manifest'i.
#
# BU SKRIPT BAJARILMADI, sabab: guard kalibratsiyasi davom etmoqda.
#
# NEGA bu qadam alohida va MAJBURIY:
# PREREGISTRATION.md §14.4 `run_meta` ning majburiy maydonlarini
# (`preregistration_sha256`, `git_commit`, `git_dirty`, ...) bitta sabab
# bilan asoslaydi: "reproducibility". `scripts/sync-to-ext4.sh` ham shu
# sababni yozadi: ".git bo'lmasa o'lchov tekshirilishi mumkin bo'lgan
# commit'ga bog'lanmaydi."
#
# Image uchun shartni KENGAYTIRAMIZ: run faqat kodga emas, BUTUN MUHITGA
# bog'lanishi kerak. Manifest -- shu bog'lanishning mashina tomonidan
# tekshiriladigan qismi (09-iso-qurilishi.md §3.1 R2).
#
# Manifest ISO'ning checksum'i YONIDA commit qilinadi, demak keyingi
# o'quvchi "aynan qaysi paket to'plami bilan o'lchangan" savoliga hujjatdan
# emas, FAYLDAN javob oladi.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./config.sh
. "$HERE/config.sh"
# shellcheck source=./lib/common.sh
. "$HERE/lib/common.sh"

require_not_root
require_sde
[ -d "$ROOTFS_DIR" ] || die "rootfs yo'q: $ROOTFS_DIR -- avval 10-build-rootfs.sh"

MANIFEST="$OUT_DIR/manifest.txt"
mkdir -p "$OUT_DIR"

log "manifest yoziladi: $MANIFEST"

# NEGA `dpkg-query --admindir`: rootfs ichida chroot QILMASDAN o'qiydi.
# chroot root talab qilishi mumkin; --admindir talab qilmaydi. Bu 09 §2.1
# ning "root'siz build" talabi bilan mos.
#
# NEGA LC_ALL=C sort: locale'ga bog'liq sort boshqa mashinada boshqa tartib
# beradi -> manifest ikki build'da `diff` qilib bo'lmas holga keladi
# (09 §3.1 R4).
{
  printf '# REVIX research appliance -- paket manifest\n'
  printf '#\n'
  printf '# BU MANIFEST QURILMAGAN IMAGE UCHUN EMAS: u faqat haqiqiy build\n'
  printf '# natijasida to\xe2\x80\x99ldiriladi. Agar siz bu faylni bo\xe2\x80\x99sh ko\xe2\x80\x99rsangiz,\n'
  printf '# image qurilmagan.\n'
  printf '#\n'
  printf '# suite              = %s\n' "$SUITE"
  printf '# arch               = %s\n' "$ARCH"
  printf '# snapshot_ts        = %s\n' "$SNAPSHOT_TS"
  printf '# mirror             = %s\n' "$MIRROR"
  printf '# source_date_epoch  = %s\n' "$SOURCE_DATE_EPOCH"
  printf '# oomd_installed     = %s   (09 \xc2\xa74.4 -- ATAYLAB)\n' "$OOMD_INSTALLED"
  printf '#\n'
  printf '# format: package\\tversion\\tarch\n'
  LC_ALL=C dpkg-query --admindir="$ROOTFS_DIR/var/lib/dpkg" \
    -W -f='${Package}\t${Version}\t${Architecture}\n' \
    | LC_ALL=C sort
} > "$MANIFEST"

PKG_COUNT="$(grep -cv '^#' "$MANIFEST" || true)"
log "paket soni: $PKG_COUNT"

# --- ahamiyatga ega versiyalarni ALOHIDA tekshirish -------------------------
#
# NEGA: INSTALLATION.md §2 jadvali har chegarani AYNAN BIR imkoniyat uchun
# qo'yadi. Ularni ISO qurilgandan keyin `doctor` bilan tekshirish ham mumkin,
# lekin unda build'ga soatlar ketgan bo'ladi. Shuning uchun fail-closed
# tekshiruv SHU YERDA.
check_floor() {
  local pkg="$1" want="$2" why="$3" got
  got="$(awk -v p="$pkg" -F'\t' '$1==p {print $2}' "$MANIFEST" | head -1)"
  if [ -z "$got" ]; then
    die "manifest'da '$pkg' yo'q -- $why"
  fi
  log "  $pkg = $got (kerak >= $want)"
  # NEGA `dpkg --compare-versions`: Debian versiya tartibini TO'G'RI
  # bilgan yagona vosita; qo'lda satr taqqoslash epoch va `~` bilan
  # buziladi.
  if ! dpkg --compare-versions "$got" ge "$want"; then
    die "$pkg $got < $want -- $why"
  fi
}

# systemd >= 254: INSTALLATION.md §2 -- "`RestartSteps=` va
# `RestartMaxDelaySec=` v254 dan mavjud. Baseline B BUTUNLAY shunga
# tayanadi: `RestartSteps=` bo'lmasa systemd native exponential backoff yo'q
# va kuchli baseline yo'qoladi."
check_floor systemd 254 "Baseline B o'lchanmaydi (INSTALLATION.md §2)"

# python3 >= 3.11: INSTALLATION.md §2, PREREGISTRATION.md.
# NEGA `python3` paketi versiyasi suite'ning Python versiyasini kuzatadi.
check_floor python3 3.11 "harness ishga tushmaydi (INSTALLATION.md §2)"

# NEGA awk, grep EMAS: manifest ustunlari TAB bilan ajratilgan, va shell
# manba faylida tab belgisi ko'rinmas hamda tasodifan space'ga aylanishi
# mumkin. `awk -F'\t'` ustunni aniq oladi va bu xato sinfini yopadi.
has_pkg() {
  awk -v p="$1" -F'\t' '$1==p {found=1} END {exit !found}' "$MANIFEST"
}

# python_modules (doctor #15): psutil, dbus, numpy, scipy -- MAVJUDLIK
# tekshiruvi (versiya chegarasi hujjatlarda yo'q).
for p in python3-psutil python3-dbus python3-numpy python3-scipy; do
  has_pkg "$p" || die "manifest'da '$p' yo'q -> doctor #15 python_modules FAIL bo'ladi"
done
log "  python3-{psutil,dbus,numpy,scipy}: bor"

# git (doctor #17/#18): run_meta.git_commit / git_dirty MAJBURIY
# (04-driver-va-analiz-shartnomasi.md §1.1).
has_pkg git \
  || die "manifest'da 'git' yo'q -> doctor #17 git_present FAIL -> run_meta.git_commit yozilmaydi"
log "  git: bor"

# build-essential (doctor #13): revix/Makefile `CC ?= cc`.
has_pkg build-essential \
  || die "manifest'da 'build-essential' yo'q -> sut.c qurilmaydi (doctor #13)"
log "  build-essential: bor"

# systemd-oomd ATAYLAB yo'q (09 §4.4).
if has_pkg systemd-oomd; then
  die "manifest'da 'systemd-oomd' BOR -- bu ATAYLAB bo'lmasligi kerak (09 §4.4)"
fi
log "  systemd-oomd: yo'q (ATAYLAB, 09 §4.4)"

printf '%s  manifest.txt\n' "$(sha256_of "$MANIFEST")" > "$OUT_DIR/manifest.txt.sha256"
log "manifest sha256: $(sha256_of "$MANIFEST")"
log "Keyingi qadam: bash iso/30-make-squashfs.sh"
