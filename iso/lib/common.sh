# REVIX image build -- umumiy fail-closed tekshiruvlar.
#
# Bu fayl `source` qilinadi, bajarilmaydi.
#
# Loyiha qoidasi: tekshiruvning O'ZI xato bersa natija PASS emas, FAIL
# bo'ladi. Bu `revix/cli.py:collect_checks()` dagi aynan shu prinsip:
# "FAIL-CLOSED: tekshiruvning O'ZI istisno tashlasa, natija PASS emas, FAIL
# bo'ladi. Aks holda doctor'dagi bug jimgina 'hammasi yaxshi' ga aylanardi."
#
# shellcheck shell=bash

set -euo pipefail

# --- log --------------------------------------------------------------------

log()  { printf '[revix-iso] %s\n' "$*"; }
warn() { printf '[revix-iso] OGOHLIK: %s\n' "$*" >&2; }
die()  { printf '[revix-iso] XATO: %s\n' "$*" >&2; exit 1; }

# --- 1. root sifatida ishga tushirishni rad etish ---------------------------

# NEGA: 00-pilot-topologiya.md §4 prinsipi -- "barcha privilegiyali
# operatsiyalar BITTA qisqa, ko'rib chiqiladigan setup skriptida, sessiyaga
# bir marta ishlaydi va har trial'da hech narsa qilmaydi". Build uchun ham
# shu disiplina: faqat 00-host-prepare.sh root bilan ishlaydi, qolgan
# hamma qadam mmdebstrap --mode=unshare orqali ROOT'SIZ bajariladi (09 §2.1).
require_not_root() {
  if [ "$(id -u)" -eq 0 ]; then
    die "bu skript root sifatida ishga tushirilmaydi (00 §4 prinsipi). Faqat iso/00-host-prepare.sh root talab qiladi."
  fi
}

# --- 2. eksperiment davom etayotgan bo'lsa ishga tushmaslik -----------------

# NEGA: `revix/units.py:1506 preflight()` / `require_clean()` mantig'ining
# shell'dagi qayta yozilishi. units.py docstring'i sababni aytadi:
#
#   "qoldiq unit yoki cgroup JIMGINA keyingi run'ga qo'shilib ketardi --
#    eski memory.current, eski NRestarts, eski failed holat. O'lchov
#    hissasi bo'lgan loyihada bu jimgina kontaminatsiya, demak run
#    boshlanmaydi."
#
# Build uchun sabab teskari tomondan bir xil: build guest'ning xotira, disk
# va CPU'sini to'yintiradi, demak jonli o'lchovni BUZADI. Qat'iy rad etish
# mezonlari units.py bilan BIR XIL (00-pilot-topologiya.md §2):
#   * `revix-*` ga mos YUKLANGAN unit;
#   * `revixlab.slice` / `revixmon.slice` -- unit YOKI cgroup katalogi.
#
# Qo'shimcha: scripts/guard-test.sh pre-flight'i `revix-press.service` ni
# alohida tekshiradi -- shu ham qo'shildi.
REVIX_UNIT_GLOB="revix-*"
REVIX_LAB_SLICE="revixlab.slice"
REVIX_MON_SLICE="revixmon.slice"

# user@UID.service cgroup yo'li. revix/cgroup.py:user_service_cgroup() ning
# shell ekvivalenti; modul mavjud bo'lsa modulning o'zidan olinadi, chunki
# yo'lni ikki joyda ikki xil hisoblash -- jimgina divergensiya manbai.
revix_user_cgroup() {
  local uid cg
  uid="$(id -u)"
  if [ -n "${REPO_SRC:-}" ] && [ -f "${REPO_SRC}/revix/cgroup.py" ]; then
    if cg="$(cd "$REPO_SRC" && python3 -c 'from revix import cgroup as c; print(c.user_service_cgroup())' 2>/dev/null)"; then
      printf '%s\n' "$cg"
      return 0
    fi
  fi
  printf '/sys/fs/cgroup/user.slice/user-%s.slice/user@%s.service\n' "$uid" "$uid"
}

require_clean_env() {
  local problems=() cg

  # (a) YUKLANGAN unit'lar. `--all` yuklangan, lekin faol bo'lmaganini ham
  # ko'rsatadi -- units.py list_units() bilan bir xil qamrov.
  if command -v systemctl >/dev/null 2>&1; then
    local units
    units="$(systemctl --user list-units "$REVIX_UNIT_GLOB" "$REVIX_LAB_SLICE" "$REVIX_MON_SLICE" \
               --all --no-legend 2>/dev/null || true)"
    if [ -n "$units" ]; then
      while IFS= read -r line; do
        [ -n "$line" ] || continue
        problems+=("qoldiq unit: $line")
      done <<< "$units"
    fi
    # guard-test.sh pre-flight'ining aynan tekshiruvi.
    if systemctl --user --quiet is-active revix-press.service 2>/dev/null; then
      problems+=("revix-press.service ISHLAYAPTI")
    fi
  else
    # FAIL-CLOSED: systemctl bo'lmasa tekshiruv bajarilmadi, demak "toza" deb
    # ayta olmaymiz.
    die "systemctl topilmadi -- eksperiment holatini tekshirib bo'lmaydi, build rad etiladi (fail-closed)"
  fi

  # (b) cgroup kataloglari. 07 §4.4 o'lchagan holat: distro qayta ishga
  # tushgandan keyin BO'SH cgroup katalogi QOLADI va preflight() uni
  # bloklovchi deb sanaydi. Biz ham xuddi shunday sanaymiz.
  cg="$(revix_user_cgroup)"
  local sl
  for sl in "$REVIX_LAB_SLICE" "$REVIX_MON_SLICE"; do
    if [ -d "$cg/$sl" ]; then
      problems+=("qoldiq cgroup: $cg/$sl")
    fi
  done

  if [ "${#problems[@]}" -gt 0 ]; then
    printf '[revix-iso] XATO: REVIX eksperimenti davom etmoqda yoki qoldiq holat bor.\n' >&2
    printf '[revix-iso]   %s\n' "${problems[@]}" >&2
    printf '[revix-iso] Build RAD ETILDI: image qurilishi guest xotira/disk/CPU sini to\xe2\x80\x99yintiradi\n' >&2
    printf '[revix-iso] va jonli o\xe2\x80\x99lchovni buzadi (revix/units.py require_clean(), 00-pilot-topologiya.md \xc2\xa72).\n' >&2
    exit 1
  fi
  log "pre-flight: toza (revix-* unit yo'q, revixlab/revixmon cgroup yo'q)"
}

# --- 3. chiqish yo'li ext4'da bo'lishi ---------------------------------------

# NEGA: 07 §7.2 FAKT -- /mnt/c = 9p/drvfs, 98% to'la, 10 G bo'sh; append
# latency ext4 dan ~100x sekin. scripts/sync-to-ext4.sh ayni shu fail-closed
# tekshiruvini qiladi: "DEST yoki RUNS drvfs ustida. O'lchov ext4'da bo'lishi
# SHART." Build uchun qo'shimcha sabab: 10 G build'ga YETMAYDI va /mnt/c ni
# to'ldirish Windows tomonini buzadi.
require_ext4_out() {
  local path="$1" fstype
  case "$path" in
    /mnt/*|/media/*)
      die "chiqish yo'li drvfs/9p ustida ($path). Image ext4 HOME'da qurilishi SHART (07 §7.2)." ;;
  esac
  mkdir -p "$path"
  fstype="$(stat -fc %T "$path")"
  case "$fstype" in
    ext2/ext3|ext4|xfs|btrfs|tmpfs) log "chiqish fs: $fstype ($path)" ;;
    9p|fuseblk|msdos|vfat|ntfs)
      die "chiqish fs '$fstype' ($path) -- determinizm va performance uchun yaroqsiz (07 §7.2)." ;;
    *)
      # FAIL-CLOSED: tanimagan fs -> ruxsat berilmaydi.
      die "chiqish fs '$fstype' ($path) tanilmadi -- fail-closed, build rad etiladi." ;;
  esac
}

# --- 4. disk zaxirasi -------------------------------------------------------

require_disk() {
  local path="$1" need_gb="$2" avail_kb avail_gb
  avail_kb="$(df -Pk "$path" | awk 'NR==2 {print $4}')"
  [ -n "$avail_kb" ] || die "df '$path' uchun bo'sh joyni aniqlay olmadi (fail-closed)"
  avail_gb=$(( avail_kb / 1024 / 1024 ))
  if [ "$avail_gb" -lt "$need_gb" ]; then
    die "yetarli disk yo'q: $path da ${avail_gb} GiB bo'sh, kerak >= ${need_gb} GiB (rootfs + apt cache + squashfs + ISO)"
  fi
  log "disk: ${avail_gb} GiB bo'sh ($path), kerak >= ${need_gb} GiB"
}

# --- 5. SOURCE_DATE_EPOCH majburiy ------------------------------------------

require_sde() {
  [ -n "${SOURCE_DATE_EPOCH:-}" ] \
    || die "SOURCE_DATE_EPOCH o'rnatilmagan -- determinizm yo'q (09 §3.3)"
  case "$SOURCE_DATE_EPOCH" in
    ''|*[!0-9]*) die "SOURCE_DATE_EPOCH butun son bo'lishi kerak: '$SOURCE_DATE_EPOCH'" ;;
  esac
  log "SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH ($(date -u -d "@$SOURCE_DATE_EPOCH" +%Y-%m-%dT%H:%M:%SZ))"
}

# --- 6. kerakli vositalar ---------------------------------------------------

require_tools() {
  local missing=() t
  for t in "$@"; do
    command -v "$t" >/dev/null 2>&1 || missing+=("$t")
  done
  if [ "${#missing[@]}" -gt 0 ]; then
    printf '[revix-iso] XATO: vositalar topilmadi: %s\n' "${missing[*]}" >&2
    printf '[revix-iso] Avval `bash iso/00-host-prepare.sh` ni bajaring (u YAGONA privilegiyali qadam).\n' >&2
    exit 1
  fi
}

# --- 7. yordamchi -----------------------------------------------------------

sha256_of() {
  sha256sum "$1" | awk '{print $1}'
}

# Deterministik tartiblash: LC_ALL=C MAJBURIY.
# NEGA: locale'ga bog'liq `sort` boshqa mashinada boshqa tartib beradi, demak
# squashfs ichidagi fayl tartibi o'zgaradi va determinizm (09 §3.1 R4) yo'q.
sorted_find() {
  ( cd "$1" && find . -print | LC_ALL=C sort )
}
