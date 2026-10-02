#!/usr/bin/env bash
# mmdebstrap customize-hook: nondeterminizmni normalizatsiya qiladi.
#
# BU SKRIPT BAJARILMADI, sabab: guard kalibratsiyasi davom etmoqda.
#
# $1 = rootfs yo'li.
#
# Bu 09-iso-qurilishi.md §3.1 R5. MUHIM: bu hook image'ni bit-reproducible
# QILMAYDI. U faqat ENG YIRIK va osongina olib tashlanadigan nondeterminizm
# manbalarini yopadi. Qolgan manbalar §3.2 N1-N6 da sanalgan va ularni
# BIZ HAL QILMAYMIZ.

set -euo pipefail

ROOTFS="${1:?rootfs path berilmadi (argument 1)}"
: "${SOURCE_DATE_EPOCH:?SOURCE_DATE_EPOCH kerak}"

echo "[hook-90] normalizatsiya (SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH)"

# --- (1) apt va dpkg keshlari -----------------------------------------------
# NEGA: `/var/lib/apt/lists/*` arxivdan yuklab olingan indekslar -- ular
# yuklab olish vaqtini va mirror javobini aks ettiradi. Image ichida ular
# KERAK EMAS (guest offline ishlaydi), va ular eng katta nondeterminizm
# manbai. CHEKLOV: `/var/lib/dpkg/*` O'CHIRILMAYDI -- u dpkg uchun zarur
# (§3.2 N2: uning tartibga bog'liqligi QOLADI).
rm -rf "$ROOTFS/var/lib/apt/lists"/* \
       "$ROOTFS/var/cache/apt/archives"/*.deb \
       "$ROOTFS/var/cache/apt"/*.bin
mkdir -p "$ROOTFS/var/lib/apt/lists/partial" "$ROOTFS/var/cache/apt/archives/partial"

# --- (2) log'lar ------------------------------------------------------------
# NEGA: `/var/log/dpkg.log`, `apt/*.log`, `bootstrap.log` da TIMESTAMP bor --
# har build'da boshqa. Ularning mazmuni manifest'da (20-record-manifest.sh)
# allaqachon aks etgan, demak yo'qotilgan provenance yo'q.
find "$ROOTFS/var/log" -type f -delete 2>/dev/null || true

# --- (3) machine-id ---------------------------------------------------------
# NEGA BO'SH, O'CHIRILMAGAN: bo'sh `/etc/machine-id` -- systemd uchun
# "first boot" signali; u boot'da yangi id generatsiya qiladi. Fayl butunlay
# yo'q bo'lsa ba'zi unit'lar `ConditionFirstBoot=` ni boshqacha baholaydi.
# CHEKLOV (§3.2 N4): demak IMAGE bir xil bo'lsa ham BOOTED TIZIM bir xil
# emas. Image reproducibility'si va runtime identity'si ikki alohida narsa.
: > "$ROOTFS/etc/machine-id"
rm -f "$ROOTFS/var/lib/dbus/machine-id"
ln -sf /etc/machine-id "$ROOTFS/var/lib/dbus/machine-id"

# --- (4) tasodifiy urug'lar va kalitlar -------------------------------------
# NEGA: `random-seed` va SSH host kalitlari har build'da BOSHQA -- va ular
# image'ga tushsa, bir xil kalitli ko'p guest paydo bo'ladi (xavfsizlik
# muammosi) hamda determinizm buziladi.
rm -f "$ROOTFS/var/lib/systemd/random-seed" \
      "$ROOTFS/etc/ssh/ssh_host_"*_key \
      "$ROOTFS/etc/ssh/ssh_host_"*_key.pub

# --- (5) resolv.conf --------------------------------------------------------
# NEGA: mmdebstrap build host'ining `resolv.conf` ini chroot ichiga
# ko'chiradi -- ya'ni build host'ining DNS serverlari image'ga TUSHADI.
# Bu ham nondeterminizm, ham provenance oqishi.
rm -f "$ROOTFS/etc/resolv.conf"
ln -sf /run/systemd/resolve/stub-resolv.conf "$ROOTFS/etc/resolv.conf"

# --- (6) mtime'larni qotirish -----------------------------------------------
# NEGA: squashfs `-all-time` bilan mtime'larni baribir bir xil qiladi, lekin
# BU YERDA ham qotirish `tar`/`rsync` yoki qo'lda inspeksiya natijasini ham
# barqaror qiladi, va `find -newer` asosidagi har qanday keyingi qadam
# nondeterministik bo'lib qolmaydi.
# `/opt/revix/.git` CHIQARIB TASHLANADI: git obyektlari mtime'ga qaramaydi,
# lekin index mtime'ga QARAYDI -- uni qotirish `git status` ni butun
# daraxtni qayta hash qilishga majbur qiladi, va eng yomoni, index
# nomuvofiqligi `git status --porcelain` ni NOBO'SH qilishi mumkin ->
# doctor #18 git_clean WARN. Shuning uchun .git tegilmaydi.
find "$ROOTFS" -path "$ROOTFS/opt/revix/.git" -prune -o \
     -print0 | xargs -0r touch --no-dereference --date="@$SOURCE_DATE_EPOCH"

echo "[hook-90] tayyor"
