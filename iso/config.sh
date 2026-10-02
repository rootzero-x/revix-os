# REVIX research appliance image -- YAGONA pinning manbai.
#
# Bu fayl `source` qilinadi, bajarilmaydi. Barcha `iso/*.sh` skriptlari
# aynan shu fayldan qiymat oladi.
#
# NEGA yagona manba: ikki skript ikki xil SOURCE_DATE_EPOCH yoki ikki xil
# snapshot timestamp ishlatsa, determinizm JIMGINA buziladi va buni faqat
# `diffoscope` ko'rsatadi. Bitta sourced fayl bu xato sinfini butunlay yopadi
# (docs/architecture/09-iso-qurilishi.md §3.3).
#
# shellcheck shell=bash

# --- suite va arxiv ---------------------------------------------------------

# NEGA trixie (Debian 13), bookworm EMAS: INSTALLATION.md §2 systemd >= 254
# talab qiladi, chunki `RestartSteps=` va `RestartMaxDelaySec=` v254 dan
# mavjud va "Baseline B butunlay shunga tayanadi". bookworm'da systemd 252 --
# Baseline B o'lchanmaydi, demak image ilmiy jihatdan foydasiz.
# NEGA Kali EMAS: Kali'da vaqt bo'yicha indekslangan o'zgarmas snapshot arxivi
# yo'q, demak §3.1 R1 ta'minlanmaydi. Qolaversa README.md ochiq aytadi: REVIX
# "Kali Linux moslashtirmasi emas" (09 §2.2).
SUITE="${SUITE:-trixie}"
ARCH="${ARCH:-amd64}"

# NEGA snapshot: paket to'plamini VAQTGA qotirish uchun yagona yo'l. Oddiy
# mirror ikki hafta ichida boshqa versiyalarni beradi va manifest mos
# kelmaydi (09 §3.1 R1).
#
# CHEKLOV (09 §3.2 N7): snapshot.debian.org -- uchinchi tomon xizmati. Uning
# retention'i va mavjudligi bizning nazoratimizda EMAS. Pinned URL o'zgarmas
# BO'LISHI KERAK, lekin bu KAFOLAT emas.
SNAPSHOT_TS="${SNAPSHOT_TS:-20261001T000000Z}"
SNAPSHOT_BASE="${SNAPSHOT_BASE:-http://snapshot.debian.org/archive/debian}"
MIRROR="${MIRROR:-${SNAPSHOT_BASE}/${SNAPSHOT_TS}}"

# SOURCE_DATE_EPOCH SNAPSHOT_TS dan HOSIL QILINADI, qo'lda yozilmaydi.
# NEGA: epoch snapshot'dan keyin bo'lsa, arxivdagi Release faylining
# Valid-Until mantiqi va fayl mtime'lari bir-biriga mos kelmaydi (09 §3.3).
if [ -z "${SOURCE_DATE_EPOCH:-}" ]; then
  _sde_iso="${SNAPSHOT_TS:0:4}-${SNAPSHOT_TS:4:2}-${SNAPSHOT_TS:6:2}T${SNAPSHOT_TS:9:2}:${SNAPSHOT_TS:11:2}:${SNAPSHOT_TS:13:2}Z"
  SOURCE_DATE_EPOCH="$(date -u -d "$_sde_iso" +%s)"
  unset _sde_iso
fi
export SOURCE_DATE_EPOCH

# --- yo'llar ----------------------------------------------------------------

# NEGA ext4 HOME, /mnt/* EMAS: 07-wsl-muhit-tekshiruvlari.md §7.2 -- FAKT:
# /mnt/c = 9p/drvfs, 98% to'la, 10 G bo'sh; ext4 root'da 951 G. Build'ga
# ~25 G kerak, va /mnt/c ni to'ldirish Windows tomonini buzadi.
# scripts/sync-to-ext4.sh ayni shu fail-closed qoidani allaqachon qo'llaydi.
OUT_DIR="${OUT_DIR:-$HOME/revix-iso}"
WORK_DIR="${WORK_DIR:-$OUT_DIR/work}"
ROOTFS_DIR="${ROOTFS_DIR:-$WORK_DIR/rootfs}"
STAGE_DIR="${STAGE_DIR:-$WORK_DIR/stage}"

ISO_NAME="${ISO_NAME:-revix-appliance-${SUITE}-${SNAPSHOT_TS}.iso}"
ISO_VOLID="${ISO_VOLID:-REVIX_APPLIANCE}"

# Build'ning o'zi uchun minimal bo'sh joy (GiB).
# rootfs ~3 G + apt cache ~1 G + squashfs ~1.5 G + ISO ~2 G + zaxira.
MIN_FREE_GB="${MIN_FREE_GB:-25}"

# Manba repo: default -- shu skript joylashgan repo. Image ichiga CLONE
# qilinadi (packaging/install-revix.sh), rsync EMAS.
# NEGA clone: 07 §4.3 o'lchagan FAIL aynan worktree'ning `.git` POINTER fayli
# sababli bo'lgan -> `git rev-parse` "not a git repository" -> doctor
# git_present/git_clean FAIL (07 §1.2 #17,#18). `git clone --no-hardlinks`
# to'liq mustaqil .git katalogini beradi (09 §5.2a).
REPO_SRC="${REPO_SRC:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# Image ichidagi o'rnatish yo'li va o'lchov foydalanuvchisi.
INSTALL_PREFIX="${INSTALL_PREFIX:-/opt/revix}"
MEASURE_USER="${MEASURE_USER:-revix}"
MEASURE_UID="${MEASURE_UID:-1000}"

# --- paket to'plami ---------------------------------------------------------

# NEGA har bir guruh alohida: har paket AYNAN BIR doctor tekshiruvi yoki
# INSTALLATION.md §2 chegarasi uchun. "Yangiroq yaxshiroq" degan umumiy
# tavsiya bo'yicha hech narsa qo'shilmaydi.

# Minimal ishlaydigan tizim + live boot zanjiri.
PKGS_BASE="systemd systemd-sysv dbus init"
# NEGA linux-image-amd64: CONFIG_PSI=y va cgroup v2 (INSTALLATION.md §2).
# O'z kernel QURILMAYDI -- yangi o'lchanmagan o'zgaruvchi kiritadi (09 §2.3).
PKGS_KERNEL="linux-image-${ARCH}"
# NEGA live-boot + initramfs-tools: rootfs squashfs ustidan ko'tariladi.
PKGS_LIVE="live-boot initramfs-tools"
# NEGA bu paketlar rootfs ICHIDA: grub-mkstandalone va isolinux binarlari
# image'dan olinadi, build host'idan EMAS -- shunda bootloader ham pinned
# snapshot'dan keladi va fingerprint to'liq bo'ladi.
PKGS_BOOT="grub-efi-${ARCH}-bin grub-common syslinux-common isolinux"

# doctor #13 toolchain_cc + revix/Makefile (CC ?= cc, -std=c11 -pthread).
PKGS_TOOLCHAIN="build-essential"
# doctor #14 python_version (trixie -> 3.13 >= 3.11) va #15 python_modules.
# NEGA apt, pip EMAS: INSTALLATION.md §3 -- "pip install, setup.py yoki
# pyproject.toml YO'Q -- bu ataylab". Va apt paketi pinned snapshot'dan
# keladi, demak manifest'da versiyasi ko'rinadi; pip wheel'i ko'rinmaydi.
PKGS_PYTHON="python3 python3-pytest python3-psutil python3-dbus python3-systemd python3-yaml python3-numpy python3-scipy"
# doctor #17/#18 git_present/git_clean -> git MAJBURIY (09 §5.1).
PKGS_REPO="git ca-certificates"
# Guest ichidagi diagnostika va privilegiyali tier vositalari.
# NEGA dmsetup/iproute2: fault class 6 va tc netem -- "root kerak =
# guest'ga tegishli" (00-pilot-topologiya.md §4).
PKGS_TOOLS="procps util-linux kmod less jq ca-certificates dmsetup iproute2 acl"

PKGS_ALL="${PKGS_BASE} ${PKGS_KERNEL} ${PKGS_LIVE} ${PKGS_BOOT} ${PKGS_TOOLCHAIN} ${PKGS_PYTHON} ${PKGS_REPO} ${PKGS_TOOLS}"

# NEGA systemd-oomd ATAYLAB YO'Q: 09 §4.4. Image'da desktop sessiyasi yo'q,
# demak oomd himoya qiladigan narsa yo'q; oomd o'rnatilsa u slice'larni
# o'ldirib O'LCHOVNING O'ZIGA aralashadi. Guard (revix/guard.py) mustaqil va
# 00 §6 qadam 3 bo'yicha baribir sinaladi. Bu qaror fingerprint'ga yoziladi.
OOMD_INSTALLED="no"

# --- determinizm bayroqlari -------------------------------------------------

# mksquashfs: -all-time/-mkfs-time mtime'larni SOURCE_DATE_EPOCH ga qotiradi;
# -no-exports NFS export jadvalini (tartibga bog'liq) olib tashlaydi;
# -no-duplicates dedup natijasining tartibga bog'liqligini yo'qotadi;
# -processors 1 ko'p oqimli siqishning tartib nondeterminizmini olib tashlaydi.
SQUASHFS_COMP="${SQUASHFS_COMP:-xz}"
SQUASHFS_DETERMINISM="-no-exports -no-duplicates -processors 1"
