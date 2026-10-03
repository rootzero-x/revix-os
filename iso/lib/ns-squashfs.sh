#!/usr/bin/env bash
# User namespace ICHIDA bajariladigan qadam 30 ishi.
#
# Bu fayl `lib/common.sh:ns_run` orqali, mmdebstrap BILAN AYNAN BIR XIL uid
# map ostida (ichki 0 -> tashqi 100000) chaqiriladi.
#
# ==========================================================================
# NEGA bu alohida fayl mavjud -- TUZATISH (11-iso-qurilish-jurnali.md, bug #4)
# ==========================================================================
# 09-iso-qurilishi.md §2 zanjiri `mmdebstrap` -> `mksquashfs` ni ODDIY
# FOYDALANUVCHI sifatida bajarishni nazarda tutgan edi. Bu ishlamaydi, va
# sabab o'lchangan:
#
#   `mmdebstrap --mode=unshare` yozgan rootfs tashqi tomondan uid 100000 ga
#   tegishli, va uning ichida oddiy foydalanuvchi O'QIY OLMAYDIGAN joylar
#   bor:
#       /root                  drwx------   (0700)
#       /etc/ssh               kalitlar, 0600
#       /boot/initrd.img-*     -rw-------   (0600)
#       /etc/shadow            0640 root:shadow
#
# Oqibati IKKI xil, va ikkinchisi birinchisidan YOMONROQ:
#   (a) `find` va `mksquashfs` "Permission denied" beradi -> qadam o'ladi;
#   (b) agar xato YUTILSA (masalan `|| true` bilan), squashfs JIMGINA
#       to'liqsiz bo'ladi VA undagi egalik 100000 bo'lib qoladi -- ya'ni
#       boot qilgan tizimda `/root` egasi `nobody` bo'lardi va buni faqat
#       guest ichida, ancha keyin sezardik.
#
# NEGA namespace ichida: ichki uid 0 == rootfs egasi, demak hamma narsa
# o'qiladi VA `mksquashfs` egalikni 0:0 deb YOZADI -- aynan kerak bo'lgan
# natija. Bu `sudo` TALAB QILMAYDI: 09 §2.1 ning "root'siz build" sharti
# buzilmaydi, chunki biz hali ham privilegiyasiz user namespace ichidamiz.

set -euo pipefail

: "${ROOTFS_DIR:?ROOTFS_DIR kerak}"
: "${STAGE_DIR:?STAGE_DIR kerak}"
: "${WORK_DIR:?WORK_DIR kerak}"
: "${SOURCE_DATE_EPOCH:?SOURCE_DATE_EPOCH kerak}"
: "${SQUASHFS_COMP:?SQUASHFS_COMP kerak}"
: "${SQUASHFS_DETERMINISM:?SQUASHFS_DETERMINISM kerak}"

SQUASH="$STAGE_DIR/live/filesystem.squashfs"
SORTFILE="$WORK_DIR/sortfile.txt"

echo "[ns-30] namespace ichida: uid=$(id -u) (rootfs egasi bilan mos)"

# --- deterministik fayl tartibi ---------------------------------------------
#
# NEGA namespace ichida: `find` 0700 kataloglarga (`/root`) KIRISHI kerak,
# aks holda sort fayli TO'LIQSIZ bo'ladi va mksquashfs ularni tartibsiz
# joylaydi -- determinizm (09 §3.1 R4) jimgina buziladi.
# NEGA LC_ALL=C: locale'ga bog'liq sort boshqa mashinada boshqa tartib
# beradi.
# TUZATISH (11-iso-qurilish-jurnali.md, bug #11): `mksquashfs -sort` fayl
# formati `<yo'l> <priority>` bo'lib, oxirgi bo'shliqdan keyingi qismni
# priority deb o'qiydi -- ya'ni ICHIDA BO'SHLIQ bo'lgan yo'lni IFODALAB
# BO'LMAYDI. Haqiqiy xato:
#
#   Sort file ".../sortfile.txt", can't find priority in entry
#   "usr/lib/python3/dist-packages/scipy/io/tests/data/Transparent Busy.ani 0",
#   EOL or match failure
#   FATAL ERROR: Failed to read sort file
#
# Bu formatning QATTIQ cheklovi, bizning xatomiz emas: `-sort` da quoting
# yoki escaping mexanizmi YO'Q.
#
# O'LCHANGAN: butun rootfs'da (32758 yo'l) bo'shliqli yo'l AYNAN BITTA --
# `scipy` ning test fixture'i `Transparent Busy.ani`.
#
# QAROR: bo'shliqli yo'llar sort faylidan CHIQARILADI, lekin HAR BIRI
# log'ga OSHKORA yoziladi (jimgina tashlab ketilmaydi -- loyiha qoidasi).
# NEGA bu determinizmni deyarli buzmaydi: sort faylida bo'lmagan fayl
# mksquashfs'da default priority 0 oladi -- ro'yxatdagilar bilan AYNAN BIR
# XIL. Demak farq faqat shu bitta faylning bir xil prioritetli guruh
# ICHIDAGI o'rnida, va u scan tartibiga tushadi.
# NEGA fayl IMAGE'dan chiqarilmaydi: u `python3-scipy` paketining qismi;
# uni o'chirish dpkg integrity'sini va manifest'ning to'g'riligini buzardi.
# CHEKLOV: demak `09` §3.1 R4 ning "to'liq oshkora tartib" da'vosi 32758
# yo'ldan 32757 tasi uchun amal qiladi, hammasi uchun emas.
ALLPATHS="$WORK_DIR/filelist.txt"
( cd "$ROOTFS_DIR" && find . -print | LC_ALL=C sort ) \
  | sed 's/^\.\///' > "$ALLPATHS"

# Bo'shliqli yo'llarni OSHKORA ko'rsatamiz.
if grep -q ' ' "$ALLPATHS"; then
  echo "[ns-30] OGOHLIK: sort faylidan chiqarilgan bo'shliqli yo'llar (mksquashfs -sort formati ularni ifodalay olmaydi):"
  grep ' ' "$ALLPATHS" | sed 's/^/[ns-30]   /'
  echo "[ns-30]   jami chiqarildi: $(grep -c ' ' "$ALLPATHS")"
fi

grep -v ' ' "$ALLPATHS" | sed 's/$/ 0/' > "$SORTFILE"
echo "[ns-30] filelist yo'llar soni:  $(wc -l < "$ALLPATHS")"
echo "[ns-30] sortfile yo'llar soni:  $(wc -l < "$SORTFILE")"

# --- squashfs ---------------------------------------------------------------
#
# TUZATISH (11-iso-qurilish-jurnali.md, bug #10): eski kod `-all-time` va
# `-mkfs-time` ni SOURCE_DATE_EPOCH BILAN BIRGA berardi. squashfs-tools
# 4.7.5 buni RAD ETADI (haqiqiy chiqish):
#
#   FATAL ERROR: SOURCE_DATE_EPOCH and command line options can't be used
#                at the same time to set timestamp(s)
#
# SABAB: 4.7.x SOURCE_DATE_EPOCH ni O'ZI qo'llab-quvvatlaydi va takroriy
# CLI bayroqlarini ziddiyat deb sanaydi. `09` §3.1 R3 esa IKKISINI ham
# berishni yozgan -- u yozilganda bu tekshiruv hali yo'q edi.
#
# YECHIM: env o'zgaruvchisining O'ZI ishlatiladi (u `iso/config.sh` da
# export qilinadi -- YAGONA haqiqat manbai saqlanadi, §3.3 buzilmaydi).
#
# O'LCHANGAN TASDIQ (soxta daraxt ustida, /var/tmp/sqtest):
#   * faqat env bilan ikki build, 2 s oraliq bilan -> BIT-IDENTIK
#         7c07400cea16aa036f697a0fdee750815a4761c297978dbd351829131815b89f
#         7c07400cea16aa036f697a0fdee750815a4761c297978dbd351829131815b89f
#   * superblock: "Creation or last append time Thu Oct 1 05:00:00 2026"
#     = SOURCE_DATE_EPOCH. Ya'ni `-mkfs-time` ning vazifasi BAJARILADI.
#
# CHEKLOV -- SEMANTIKA FARQI, oshkora yoziladi:
#   `-all-time` barcha mtime'ni MAJBURAN o'rnatadi; SOURCE_DATE_EPOCH esa
#   ularni CLAMP qiladi (epoch'dan KEYINGI vaqtlar epoch'ga tushadi,
#   OLDINGILAR o'z joyida qoladi). O'lchangan:
#         a.txt  mtime 2020-09-13 (< epoch) -> 2020-09-13 SAQLANDI
#         b.txt  mtime 2033      (> epoch) -> 2026-10-01 CLAMP bo'ldi
#   NEGA BU YERDA EKVIVALENT: `customize-90-normalize.sh` allaqachon
#   BARCHA faylni (pseudo-fs'lardan tashqari) aynan SOURCE_DATE_EPOCH ga
#   qotiradi, va normalizatsiyadan chetda qolgan yagona narsa -- build
#   paytida yaratilgan `/dev` node'lari, ularning vaqti epoch'dan KEYIN,
#   demak ular CLAMP bo'ladi. Natijada image ichidagi har bir mtime
#   SOURCE_DATE_EPOCH ga teng -- `-all-time` bilan bir xil natija.
rm -f "$SQUASH"
# shellcheck disable=SC2086  # SQUASHFS_DETERMINISM ataylab bo'linadi
SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH" \
mksquashfs "$ROOTFS_DIR" "$SQUASH" \
  -comp "$SQUASHFS_COMP" \
  -sort "$SORTFILE" \
  $SQUASHFS_DETERMINISM \
  -no-progress

# --- kernel va initrd -------------------------------------------------------
#
# NEGA squashfs'dan TASHQARIDA: bootloader ularni ISO9660 dan to'g'ridan-
# to'g'ri o'qiydi -- squashfs hali mount qilinmagan paytda.
# NEGA namespace ichida: Debian `initrd.img-*` ni 0600 root:root qilib
# yozadi, demak tashqaridan `cp` UMUMAN o'qiy olmaydi.
KERNEL_SRC="$(find "$ROOTFS_DIR/boot" -maxdepth 1 -name 'vmlinuz-*' | LC_ALL=C sort | tail -1)"
INITRD_SRC="$(find "$ROOTFS_DIR/boot" -maxdepth 1 -name 'initrd.img-*' | LC_ALL=C sort | tail -1)"
[ -n "$KERNEL_SRC" ] || { echo "[ns-30] XATO: vmlinuz-* topilmadi -> linux-image o'rnatilmagan" >&2; exit 1; }
[ -n "$INITRD_SRC" ] || { echo "[ns-30] XATO: initrd.img-* topilmadi -> initramfs-tools ishlamagan" >&2; exit 1; }

# NEGA `cp` (`cp -a` EMAS) + oshkora `chmod 0644`:
#   (1) `cp -a` egalikni saqlashga urinadi -- bu namespace ichida ishlaydi,
#       lekin natija 100000 ga tegishli 0600 fayl bo'ladi va keyingi qadam
#       (40-make-iso.sh, xorriso) ODDIY FOYDALANUVCHI sifatida uni O'QIY
#       OLMAYDI. Bu aynan bug #4 ning ikkinchi yarmi.
#   (2) ISO9660 egalik va rejimni baribir SAQLAMAYDI, demak hech qanday
#       provenance yo'qolmaydi.
cp "$KERNEL_SRC" "$STAGE_DIR/live/vmlinuz"
cp "$INITRD_SRC" "$STAGE_DIR/live/initrd.img"
chmod 0644 "$STAGE_DIR/live/vmlinuz" "$STAGE_DIR/live/initrd.img"
touch --date="@$SOURCE_DATE_EPOCH" "$STAGE_DIR/live/vmlinuz" "$STAGE_DIR/live/initrd.img"

echo "[ns-30] kernel: $(basename "$KERNEL_SRC")"
echo "[ns-30] initrd: $(basename "$INITRD_SRC")"

# --- 40-qadam uchun bootloader binarlari ------------------------------------
#
# NEGA BU YERDA, 40-make-iso.sh da emas: binarlar rootfs ICHIDAN olinadi
# (09 §2.4 -- shunda bootloader ham pinned snapshot'dan keladi), va
# `$ROOTFS_DIR/usr/lib` ostidagi `find` tashqaridan 0700 kataloglarda
# to'xtaydi. Ularni namespace ichida bir marta chiqarib, 0644 qilib
# qo'yamiz -- keyin 40-qadam ularni oddiy foydalanuvchi sifatida ishlatadi.
BL_DIR="$WORK_DIR/bootloader"
rm -rf "$BL_DIR"
mkdir -p "$BL_DIR"
for f in isolinux.bin ldlinux.c32 libcom32.c32 libutil.c32 menu.c32 isohdpfx.bin; do
  src="$(find "$ROOTFS_DIR/usr/lib" -name "$f" -type f 2>/dev/null | LC_ALL=C sort | head -1)"
  if [ -z "$src" ]; then
    echo "[ns-30] XATO: bootloader komponenti topilmadi: $f (rootfs'da isolinux/syslinux-common bormi?)" >&2
    exit 1
  fi
  cp "$src" "$BL_DIR/$f"
  chmod 0644 "$BL_DIR/$f"
  echo "[ns-30]   bootloader: $f <- ${src#"$ROOTFS_DIR"}"
done
chmod 0777 "$BL_DIR"

echo "[ns-30] tayyor"
