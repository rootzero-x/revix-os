#!/usr/bin/env bash
# REVIX image build, qadam 40: bootloader + ISO.
#
# BU SKRIPT BAJARILMADI, sabab: guard kalibratsiyasi davom etmoqda.
#
# Vositalar: grub-mkstandalone (EFI), isolinux/syslinux (BIOS), xorriso (ISO).
#
# NEGA hybrid (BIOS + UEFI): QEMU'ni ham SeaBIOS, ham OVMF bilan ishlatish
# mumkin, va benchmark PORTATIV bo'lishi kerak
# (docs/research/04-novelty-statement.md C4). Bitta yo'lni tanlash image'ni
# o'quvchining firmware'iga bog'laydi (09-iso-qurilishi.md §2.4).
#
# NEGA xorriso, genisoimage EMAS: xorriso `--modification-date=` ni qabul
# qiladi -- ISO9660 Primary Volume Descriptor'dagi timestamp'ni
# SOURCE_DATE_EPOCH ga qotirish uchun MAJBURIY. genisoimage'da bu
# ekvivalent yo'q, demak u bilan ISO hech qachon takrorlanmaydi.
# Qolaversa live-build ning o'zi ham aynan xorriso'ni chaqiradi.

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
require_ext4_out "$OUT_DIR"
require_disk "$OUT_DIR" 8
require_tools xorriso
[ -f "$STAGE_DIR/live/filesystem.squashfs" ] || die "squashfs yo'q -- avval 30-make-squashfs.sh"

ISO_PATH="$OUT_DIR/$ISO_NAME"

# --- kernel buyruq satri ----------------------------------------------------
#
# boot=live        : live-boot initramfs skripti shunga qarab ishlaydi.
# components       : live-config'ga sozlashga ruxsat (foydalanuvchi, host).
# console=ttyS0    : image HEADLESS (09 §7) -- serial console orqali.
#                    NEGA: GUI guest'da fon yuk kiritadi va
#                    PREREGISTRATION.md §8 confound nazoratini buzadi.
# systemd.unified_cgroup_hierarchy=1 : doctor #2 cgroup_v2.
#                    NEGA oshkora: Debian trixie default'da shunday, lekin
#                    default'ga TAYANMAYDI -- u o'zgarishi mumkin va
#                    o'zgarsa harness UMUMAN ishlamaydi
#                    (doctor #2 consequence: "v1 da memory.pressure,
#                    cgroup.kill, delegatsiya yo'q -> harness ishlamaydi").
# psi=1            : NEGA oshkora: ba'zi kernel konfiguratsiyalarida PSI
#                    `CONFIG_PSI_DEFAULT_DISABLED=y` bilan qurilgan va
#                    runtime'da `psi=1` talab qiladi. PSI -- loyihaning
#                    MARKAZIY o'zgaruvchisi (PREREGISTRATION.md §7), demak
#                    uni tasodifga qoldirmaymiz. Bayroq keraksiz bo'lsa
#                    kernel uni jimgina e'tiborsiz qoldiradi.
KCMDLINE="boot=live components quiet console=ttyS0,115200n8 systemd.unified_cgroup_hierarchy=1 psi=1"

# --- BIOS: isolinux ---------------------------------------------------------
make_shared_dir "$STAGE_DIR/isolinux"
# NEGA binarlar ROOTFS'dan olinadi, build host'idan EMAS: shunda bootloader
# ham pinned snapshot'dan keladi va manifest to'liq bo'ladi (09 §2.4).
#
# TUZATISH (bug #4): eski kod bu yerda `find "$ROOTFS_DIR/usr/lib"` qilib
# `cp -a` bilan ko'chirardi. Ikki sabab bilan ishlamaydi:
#   (1) rootfs tashqi uid 100000 ga tegishli -> `find` 0700 kataloglarda
#       "Permission denied" beradi va `set -o pipefail` ostida qadam o'ladi;
#   (2) `cp -a` egalikni saqlashga urinadi -> oddiy foydalanuvchi uchun
#       `chown` rad etiladi -> `cp` rc != 0 -> `set -e` qadamni o'ldiradi.
# Shuning uchun binarlar 30-qadamda, namespace ICHIDA chiqarilib
# `$WORK_DIR/bootloader` ga 0644 bilan qo'yiladi (iso/lib/ns-squashfs.sh).
BL_DIR="$WORK_DIR/bootloader"
[ -d "$BL_DIR" ] || die "bootloader binarlari yo'q: $BL_DIR -- avval 30-make-squashfs.sh"
for f in isolinux.bin ldlinux.c32 libcom32.c32 libutil.c32 menu.c32; do
  [ -r "$BL_DIR/$f" ] || die "bootloader komponenti o'qilmadi: $BL_DIR/$f"
  cp "$BL_DIR/$f" "$STAGE_DIR/isolinux/$f"
  chmod 0644 "$STAGE_DIR/isolinux/$f"
done

cat > "$STAGE_DIR/isolinux/isolinux.cfg" <<EOF
SERIAL 0 115200
UI menu.c32
PROMPT 0
TIMEOUT 50
DEFAULT revix

LABEL revix
  MENU LABEL REVIX research appliance (live)
  LINUX /live/vmlinuz
  INITRD /live/initrd.img
  APPEND ${KCMDLINE}
EOF

# --- UEFI: grub -------------------------------------------------------------
mkdir -p "$STAGE_DIR/boot/grub" "$STAGE_DIR/EFI/boot"
cat > "$STAGE_DIR/boot/grub/grub.cfg" <<EOF
set timeout=5
set default=0
serial --unit=0 --speed=115200
terminal_input serial console
terminal_output serial console

menuentry "REVIX research appliance (live)" {
    linux /live/vmlinuz ${KCMDLINE}
    initrd /live/initrd.img
}
EOF

log "BU QADAM BAJARILMADI (guard kalibratsiyasi davom etmoqda)."
if [ "${REVIX_ISO_CONFIRM:-}" != "yes" ]; then
  die "to'xtatildi (fail-closed). Bajarish uchun: REVIX_ISO_CONFIRM=yes"
fi

require_tools grub-mkstandalone mkfs.vfat mmd mcopy

# NEGA grub-mkstandalone: barcha modulni va grub.cfg ni BITTA EFI binariga
# yig'adi -> ISO ichida alohida /boot/grub modul daraxti kerak emas, demak
# determinizm yuzasi kichikroq.
# CHEKLOV (09 §3.2 N5): grub-mkstandalone ichiga memdisk cpio joylaydi;
# SOURCE_DATE_EPOCH bilan deterministik bo'lishi KUTILADI, lekin biz
# tekshirmadik -- bu GIPOTEZA.
grub-mkstandalone \
  --format=x86_64-efi \
  --output="$WORK_DIR/bootx64.efi" \
  --locales="" --fonts="" \
  "boot/grub/grub.cfg=$STAGE_DIR/boot/grub/grub.cfg"

# EFI boot image: FAT. NEGA aniq hajm va -i (volume id): mkfs.vfat
# default'da TASODIFIY volume id va JORIY VAQTni yozadi -> determinizm yo'q.
# `-i` volume id'ni qotiradi; hajm esa oshkora beriladi.
#
# TUZATISH (11-iso-qurilish-jurnali.md, bug #3): eski kod hajmni QO'LDA
# `2048` (KiB) deb yozgan edi. O'lchangan haqiqat:
#       $ grub-mkstandalone --format=x86_64-efi ... -o bootx64.efi
#       $ stat -c %s bootx64.efi   ->  3817472  (3728 KiB)
# ya'ni EFI binari FAT image'dan QARIYB IKKI BARAVAR KATTA va `mcopy`
# "disk full" bilan o'lardi. Qo'lda yozilgan hajm grub versiyasi o'zgarishi
# bilan yana jimgina buziladi, shuning uchun hajm BINARIDAN HISOBLANADI.
#
# NEGA determinizm buzilmaydi: hajm faqat binarining o'lchamiga bog'liq
# funksiya (vaqtga yoki tasodifga emas). 1024 KiB ga yuqoriga yaxlitlash
# bir xil binari uchun HAR DOIM bir xil hajm beradi.
# NEGA +512 KiB zaxira: FAT32/FAT16 superblock, FAT jadvallari va root
# katalog yozuvlari joy egallaydi -- fayl hajmiga TENG image sig'maydi.
EFI_IMG="$STAGE_DIR/EFI/boot/efiboot.img"
EFI_BIN_KB=$(( ( $(stat -c %s "$WORK_DIR/bootx64.efi") + 1023 ) / 1024 ))
EFI_IMG_KB=$(( ( (EFI_BIN_KB + 512 + 1023) / 1024 ) * 1024 ))
log "EFI binari: ${EFI_BIN_KB} KiB -> FAT image: ${EFI_IMG_KB} KiB (binaridan hisoblandi)"
rm -f "$EFI_IMG"
mkfs.vfat -C "$EFI_IMG" "$EFI_IMG_KB" -n REVIXEFI -i "$(printf '%08x' $(( SOURCE_DATE_EPOCH & 0xFFFFFFFF )))"
mmd -i "$EFI_IMG" ::/EFI ::/EFI/BOOT
mcopy -i "$EFI_IMG" "$WORK_DIR/bootx64.efi" ::/EFI/BOOT/BOOTX64.EFI
cp -a "$WORK_DIR/bootx64.efi" "$STAGE_DIR/EFI/boot/bootx64.efi"

# --- ISO --------------------------------------------------------------------
#
# --modification-date : ISO9660 PVD timestamp'i -> SOURCE_DATE_EPOCH.
#   MAJBURIY, aks holda ISO hech qachon takrorlanmaydi (09 §3.1 R3).
# -isohybrid-mbr      : BIOS yuklanishi uchun MBR.
# -eltorito-alt-boot ... -e : UEFI yo'li.
# -J -r -joliet-long  : Joliet + Rock Ridge -- uzun nomlar.
ISO_MOD_DATE="$(date -u -d "@$SOURCE_DATE_EPOCH" +%Y%m%d%H%M%S00)"
# TUZATISH (bug #4): avvalgidek `find "$ROOTFS_DIR/usr/lib"` emas -- 30-qadam
# uni namespace ichida allaqachon chiqargan (yuqoridagi izohga qarang).
ISOHYBRID_MBR="$BL_DIR/isohdpfx.bin"
[ -r "$ISOHYBRID_MBR" ] || die "isohdpfx.bin o'qilmadi: $ISOHYBRID_MBR -- avval 30-make-squashfs.sh"

rm -f "$ISO_PATH"
xorriso -as mkisofs \
  -iso-level 3 \
  -o "$ISO_PATH" \
  -volid "$ISO_VOLID" \
  --modification-date="$ISO_MOD_DATE" \
  -isohybrid-mbr "$ISOHYBRID_MBR" \
  -b isolinux/isolinux.bin \
    -c isolinux/boot.cat \
    -no-emul-boot -boot-load-size 4 -boot-info-table \
  -eltorito-alt-boot \
    -e EFI/boot/efiboot.img \
    -no-emul-boot -isohybrid-gpt-basdat \
  -J -r -joliet-long \
  "$STAGE_DIR"

log "ISO: $ISO_PATH"
log "ISO sha256: $(sha256_of "$ISO_PATH")"
log "Keyingi qadam: bash iso/50-fingerprint.sh"
