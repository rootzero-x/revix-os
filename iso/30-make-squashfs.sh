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
# TUZATISH (bug #8): guest build o'rtasida qayta ishga tushgan bo'lsa,
# oldingi qadamning natijasi yo'q yoki yarim -- davom etish JIMGINA
# buzilgan image berardi (lib/common.sh:require_same_generation).
require_same_generation
require_disk "$OUT_DIR" 10
require_tools mksquashfs unshare
[ -d "$ROOTFS_DIR" ] || die "rootfs yo'q: $ROOTFS_DIR -- avval 10-build-rootfs.sh"
[ -f "$OUT_DIR/manifest.txt" ] || die "manifest yo'q -- avval 20-record-manifest.sh"

prepare_build_dirs

SQUASH="$STAGE_DIR/live/filesystem.squashfs"
SORTFILE="$WORK_DIR/sortfile.txt"

# --- determinizm bayroqlari -------------------------------------------------
#
# SOURCE_DATE_EPOCH (env) : barcha mtime va superblock vaqtini qotiradi.
#   TUZATISH (bug #10): avval bu `-all-time`/`-mkfs-time` CLI bayroqlari
#   bilan qilinardi, lekin squashfs-tools 4.7.5 env BILAN BIRGA berilgan
#   bayroqlarni RAD ETADI ("FATAL ERROR: SOURCE_DATE_EPOCH and command line
#   options can't be used at the same time"). Endi faqat env ishlatiladi;
#   o'lchangan tasdiq va semantika farqi iso/lib/ns-squashfs.sh da.
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

# TUZATISH (bug #4): sort fayli, mksquashfs, kernel/initrd ko'chirish va
# bootloader binarlarini chiqarish -- HAMMASI user namespace ICHIDA
# bajariladi. Sababi va o'lchangan dalillari: iso/lib/ns-squashfs.sh
# sarlavhasida. Qisqasi: rootfs tashqi uid 100000 ga tegishli va ichida
# 0700/0600 joylar bor (`/root`, `initrd.img`), demak oddiy foydalanuvchi
# sifatida qadam ishlamaydi -- va jimgina ishlagandek ko'rinsa, squashfs
# ichidagi egalik 100000 bo'lib qolardi.
export ROOTFS_DIR STAGE_DIR WORK_DIR SOURCE_DATE_EPOCH SQUASHFS_COMP SQUASHFS_DETERMINISM
ns_run bash "$HERE/lib/ns-squashfs.sh"

[ -f "$SQUASH" ] || die "squashfs yaratilmadi: $SQUASH"
[ -f "$STAGE_DIR/live/vmlinuz" ] || die "vmlinuz stage'ga ko'chirilmadi"
[ -f "$STAGE_DIR/live/initrd.img" ] || die "initrd.img stage'ga ko'chirilmadi"
# FAIL-CLOSED: namespace ichida yozilgan fayllar TASHQARIDAN o'qilishi
# SHART, aks holda 40-qadam (xorriso) o'ladi. Oshkora tekshiramiz.
for f in "$SQUASH" "$STAGE_DIR/live/vmlinuz" "$STAGE_DIR/live/initrd.img"; do
  [ -r "$f" ] || die "'$f' tashqaridan o'qilmaydi -> 40-qadam ishlamaydi (bug #4 qaytdi)"
done
log "sortfile yo'llar soni: $(wc -l < "$SORTFILE")"
log "kernel/initrd stage'da, tashqaridan o'qiladi"
# CHEKLOV (09 §3.2 N1): initramfs bit-reproducible EMAS. `update-initramfs`
# cpio'ni ishga tushgan tizimdagi modul to'plamidan yig'adi va modul tartibi
# `find` natijasiga bog'liq. SOURCE_DATE_EPOCH gzip header'ini tuzatadi,
# cpio TARTIBINI tuzatmaydi. Bu Debian'ning OCHIQ reproducible-builds
# muammosi; biz hal qilmaymiz va hal qilgandek ko'rsatmaymiz.
log "OGOHLIK: initrd bit-reproducible emas (09 §3.2 N1) -- bu CHEKLOV, nuqson emas"

log "squashfs sha256: $(sha256_of "$SQUASH")"
log "Keyingi qadam: bash iso/40-make-iso.sh"
