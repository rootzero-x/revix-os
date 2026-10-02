#!/usr/bin/env bash
# mmdebstrap customize-hook: REVIX harness'ini rootfs ichiga o'rnatadi.
#
# BU SKRIPT BAJARILMADI, sabab: guard kalibratsiyasi davom etmoqda.
#
# $1 = rootfs yo'li (chroot EMAS -- oddiy katalog, host'dan ko'rinadi).
# Hook mmdebstrap'ning unshare namespace'i ichida ishlaydi, u yerda biz
# MAPPED root'miz -- shuning uchun `chown` ishlaydi va butun build root'siz
# bo'ladi (09-iso-qurilishi.md §2.1).
#
# Bu hook ishning o'zini QILMAYDI -- u `packaging/install-revix.sh` ni
# chaqiradi. NEGA: "revix qanday o'rnatiladi" degan savolning javobi BITTA
# joyda bo'lishi kerak, aks holda image va qo'lda o'rnatish divergensiya
# qiladi (09 §5).

set -euo pipefail

ROOTFS="${1:?rootfs path berilmadi (argument 1)}"

: "${REVIX_REPO_SRC:?REVIX_REPO_SRC kerak}"
: "${REVIX_PACKAGING_DIR:?REVIX_PACKAGING_DIR kerak}"

echo "[hook-10] revix -> $ROOTFS${REVIX_INSTALL_PREFIX:-/opt/revix}"

REVIX_ROOTFS="$ROOTFS" \
REVIX_FROM_IMAGE_BUILD=yes \
  bash "$REVIX_PACKAGING_DIR/install-revix.sh"
