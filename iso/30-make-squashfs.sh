#!/usr/bin/env bash
# REVIX image build, qadam 30: rootfs -> squashfs.
#
# BU SKRIPT BAJARILMADI, sabab: guard kalibratsiyasi davom etmoqda.
#
# Vosita: `mksquashfs` (squashfs-tools).
# NEGA squashfs: live-boot aynan `live/filesystem.squashfs` ni kutadi, va
# siqilgan read-only rootfs ISO hajmini sezilarli kamaytiradi.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./config.sh
. "$HERE/config.sh"
# shellcheck source=./lib/common.sh
. "$HERE/lib/common.sh"

require_not_root
require_sde
require_disk "$OUT_DIR" 10
require_tools mksquashfs
[ -d "$ROOTFS_DIR" ] || die "rootfs yo'q: $ROOTFS_DIR -- avval 10-build-rootfs.sh"
[ -f "$OUT_DIR/manifest.txt" ] || die "manifest yo'q -- avval 20-record-manifest.sh"

SQUASH="$STAGE_DIR/live/filesystem.squashfs"
SORTFILE="$WORK_DIR/sortfile.txt"
mkdir -p "$STAGE_DIR/live" "$WORK_DIR"

# --- deterministik fayl tartibi ---------------------------------------------
#
# NEGA sort fayli: mksquashfs default'da fayllarni `readdir` tartibida
# joylaydi, va `readdir` tartibi FAYL TIZIMIGA bog'liq -- ya'ni bir xil
# rootfs boshqa mashinada boshqa squashfs beradi. `-sort` fayli tartibni
# OSHKORA qiladi (09-iso-qurilishi.md §3.1 R4).
#
# NEGA LC_ALL=C: locale'ga bog'liq sort boshqa mashinada boshqa tartib
# beradi. Bu determinizmning eng jimgina buziladigan joyi.
#
# Format: `<yo'l> <priority>`. Hamma faylga bir xil priority (0) beriladi,
# demak tartibni FAYL RO'YXATINING O'ZI belgilaydi.
log "deterministik sort fayli: $SORTFILE"
( cd "$ROOTFS_DIR" && find . -print | LC_ALL=C sort ) \
  | sed 's/^\.\///; s/$/ 0/' > "$SORTFILE"
log "  yo'llar soni: $(wc -l < "$SORTFILE")"

# --- determinizm bayroqlari -------------------------------------------------
#
# -all-time / -mkfs-time : barcha mtime va superblock vaqtini
#   SOURCE_DATE_EPOCH ga qotiradi. Busiz har build boshqa timestamp beradi.
# -no-exports : NFS export jadvali inode tartibiga bog'liq -> olib tashlanadi.
# -no-duplicates : dedup natijasi skan tartibiga bog'liq -> o'chiriladi.
#   NARXI: image kattalashadi. Determinizm foydasiga qabul qilindi.
# -processors 1 : ko'p oqimli siqish bloklarni nondeterministik tartibda
#   yozishi mumkin. NARXI: build sekinroq.
# -no-progress : chiqish log'i determinizmga ta'sir qilmaydi, lekin
#   taqqoslanadigan log beradi.
log "mksquashfs -> $SQUASH (comp=$SQUASHFS_COMP)"
log "BU QADAM BAJARILMADI (guard kalibratsiyasi davom etmoqda)."

if [ "${REVIX_ISO_CONFIRM:-}" != "yes" ]; then
  die "to'xtatildi (fail-closed). Bajarish uchun: REVIX_ISO_CONFIRM=yes"
fi

rm -f "$SQUASH"
# shellcheck disable=SC2086  # SQUASHFS_DETERMINISM ataylab bo'linadi
mksquashfs "$ROOTFS_DIR" "$SQUASH" \
  -comp "$SQUASHFS_COMP" \
  -sort "$SORTFILE" \
  -all-time "$SOURCE_DATE_EPOCH" \
  -mkfs-time "$SOURCE_DATE_EPOCH" \
  $SQUASHFS_DETERMINISM \
  -no-progress

# --- live-boot uchun kernel va initrd ---------------------------------------
#
# NEGA squashfs'dan TASHQARIDA: bootloader ularni ISO9660 dan to'g'ridan-
# to'g'ri o'qiydi -- squashfs hali mount qilinmagan paytda.
#
# NEGA `cp` + aniq nom: live-boot/GRUB konfiguratsiyasi aniq fayl nomini
# kutadi, va versiyali nom (`vmlinuz-6.x.y-amd64`) har kernel yangilanishida
# bootloader konfiguratsiyasini buzardi.
KERNEL_SRC="$(find "$ROOTFS_DIR/boot" -maxdepth 1 -name 'vmlinuz-*' | LC_ALL=C sort | tail -1)"
INITRD_SRC="$(find "$ROOTFS_DIR/boot" -maxdepth 1 -name 'initrd.img-*' | LC_ALL=C sort | tail -1)"
[ -n "$KERNEL_SRC" ] || die "rootfs/boot ichida vmlinuz-* topilmadi -> linux-image o'rnatilmagan"
[ -n "$INITRD_SRC" ] || die "rootfs/boot ichida initrd.img-* topilmadi -> initramfs-tools ishlamagan"

cp -a "$KERNEL_SRC" "$STAGE_DIR/live/vmlinuz"
cp -a "$INITRD_SRC" "$STAGE_DIR/live/initrd.img"
touch --date="@$SOURCE_DATE_EPOCH" "$STAGE_DIR/live/vmlinuz" "$STAGE_DIR/live/initrd.img"

log "kernel: $(basename "$KERNEL_SRC")"
log "initrd: $(basename "$INITRD_SRC")"
# CHEKLOV (09 §3.2 N1): initramfs bit-reproducible EMAS. `update-initramfs`
# cpio'ni ishga tushgan tizimdagi modul to'plamidan yig'adi va modul tartibi
# `find` natijasiga bog'liq. SOURCE_DATE_EPOCH gzip header'ini tuzatadi,
# cpio TARTIBINI tuzatmaydi. Bu Debian'ning OCHIQ reproducible-builds
# muammosi; biz hal qilmaymiz va hal qilgandek ko'rsatmaymiz.
log "OGOHLIK: initrd bit-reproducible emas (09 §3.2 N1) -- bu CHEKLOV, nuqson emas"

log "squashfs sha256: $(sha256_of "$SQUASH")"
log "Keyingi qadam: bash iso/40-make-iso.sh"
