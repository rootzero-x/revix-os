#!/usr/bin/env bash
# REVIX image build -- *** YAGONA PRIVILEGIYALI SKRIPT ***
#
# BU SKRIPT BAJARILMADI, sabab: guard kalibratsiyasi davom etmoqda.
#
# ==========================================================================
# NEGA faqat BITTA skript privilegiyali
# ==========================================================================
# 00-pilot-topologiya.md §4 prinsipi:
#
#   "barcha privilegiyali operatsiyalar BITTA qisqa, ko'rib chiqiladigan
#    setup skriptida, sessiyaga bir marta ishlaydi va HAR TRIAL'DA HECH
#    NARSA QILMAYDI -> o'lchov davomida hech qanday root process tirik emas."
#
# Build zanjiri uchun shu prinsip aynan qo'llanadi: bu skript build'ga BIR
# MARTA ishlaydi, qolgan hamma qadam (10..50) `mmdebstrap --mode=unshare`
# orqali ROOT'SIZ bajariladi (09-iso-qurilishi.md §2.1).
#
# Shu skript qiladigan narsalarning hammasi INSTALLATION.md §4 va
# 00-pilot-topologiya.md §4 ning "Root kerak" ro'yxatida ALLAQACHON bor:
#   * paket o'rnatish
#   * /dev/kvm ruxsati
# Ya'ni yangi privilegiya yuzasi qo'shilmaydi.
#
# ==========================================================================
# OGOHLIK: bu skript `sudo` ishlatadi va `sudo -n` shu mashinada parol
# so'raydi (07-wsl-muhit-tekshiruvlari.md §4.5 FAKT). Demak u NAZORATSIZ
# ishlamaydi -- bu 00 §4 ning ataylab qo'yilgan xususiyati, nuqsoni emas.
# ==========================================================================

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./config.sh
. "$HERE/config.sh"
# shellcheck source=./lib/common.sh
. "$HERE/lib/common.sh"

# Bu YAGONA skript require_not_root() ni chaqirMAYDI.
# Lekin u ham eksperiment holatini tekshiradi: `apt-get install` ham disk va
# CPU iste'mol qiladi va journald'ga yozadi.
require_clean_env

# --- build host'ida kerak bo'ladigan paketlar -------------------------------
#
# NEGA har biri:
#   mmdebstrap  -- rootfs bootstrap, --mode=unshare bilan ROOT'SIZ (09 §2.1).
#                  live-build o'rniga tanlandi: lb build root talab qiladi.
#   uidmap      -- `newuidmap`/`newgidmap`; mmdebstrap --mode=unshare uchun
#                  user namespace mapping'i shunga tayanadi. Busiz unshare
#                  rejimi ishlamaydi va build root'ga qaytishga majbur bo'ladi.
#   squashfs-tools -- mksquashfs (qadam 30).
#   xorriso     -- ISO yig'ish (qadam 40). genisoimage EMAS: unda
#                  `--modification-date=` ekvivalenti yo'q, demak ISO9660
#                  PVD timestamp'ini SOURCE_DATE_EPOCH ga qotirib bo'lmaydi
#                  (09 §2.4).
#   mtools, dosfstools -- EFI boot image'i (FAT) uchun.
#   qemu-system-x86, ovmf -- faqat 99-qemu-smoke.sh uchun (test, build emas).
#   diffoscope  -- 09 §3.2 G7: ikki ISO'ni solishtirish. U BIT-IDENTIKLIKNI
#                  DA'VO QILMAYDI, balki farqni KO'RSATADI.
HOST_PKGS=(
  mmdebstrap uidmap
  squashfs-tools xorriso
  mtools dosfstools
  qemu-system-x86 ovmf
  diffoscope
  git jq coreutils
)

log "o'rnatiladigan host paketlari: ${HOST_PKGS[*]}"
log "BU QADAM BAJARILMADI (guard kalibratsiyasi davom etmoqda) -- quyidagi buyruq hujjat sifatida."

if [ "${REVIX_ISO_CONFIRM:-}" != "yes" ]; then
  cat >&2 <<'MSG'
[revix-iso] TO'XTATILDI (fail-closed).

Bu skript paket o'rnatadi va /dev/kvm ruxsatini o'zgartiradi -- ya'ni
privilegiyali va qaytarilishi qiyin qadamlar. U FAQAT oshkora tasdiq bilan
ishlaydi:

    REVIX_ISO_CONFIRM=yes bash iso/00-host-prepare.sh

NEGA: 00-pilot-topologiya.md §4 -- privilegiyali qadam nazoratsiz
ishlamasligi SHART. `sudo -n` shu mashinada parol so'raydi (07 §4.5), va bu
qo'shimcha qulf o'sha disiplinani skriptning o'zida takrorlaydi.
MSG
  exit 1
fi

# --- (1) paket o'rnatish ----------------------------------------------------
log "apt-get update + install"
sudo apt-get update
sudo apt-get install --no-install-recommends -y "${HOST_PKGS[@]}"

# --- (2) unprivileged user namespace --------------------------------------
# NEGA tekshiriladi: `mmdebstrap --mode=unshare` unprivileged userns'ga
# tayanadi. O'chirilgan bo'lsa build root'ga qaytishga majbur bo'lardi, va
# o'sha paytda 00 §4 prinsipi buziladi. Shuning uchun bu TEKSHIRUV, avtomatik
# "tuzatish" emas: sysctl'ni o'zgartirish tizim siyosatini o'zgartiradi va
# bu qaror foydalanuvchiniki.
userns_ok=1
if [ -r /proc/sys/kernel/unprivileged_userns_clone ]; then
  if [ "$(cat /proc/sys/kernel/unprivileged_userns_clone)" != "1" ]; then
    userns_ok=0
  fi
fi
if [ -r /proc/sys/user/max_user_namespaces ]; then
  if [ "$(cat /proc/sys/user/max_user_namespaces)" = "0" ]; then
    userns_ok=0
  fi
fi
if [ "$userns_ok" -ne 1 ]; then
  warn "unprivileged user namespace O'CHIRILGAN -> mmdebstrap --mode=unshare ishlamaydi."
  warn "Tuzatishni QO'LDA qiling (tizim siyosati qarori):"
  warn "  sysctl -w kernel.unprivileged_userns_clone=1"
  warn "  sysctl -w user.max_user_namespaces=10000"
  die "build rad etiladi: root'siz bootstrap imkonsiz (00 §4 prinsipi buzilardi)"
fi
log "unprivileged user namespace: ruxsat etilgan"

# --- (3) /dev/kvm ruxsati ---------------------------------------------------
#
# FAKT (07-wsl-muhit-tekshiruvlari.md §1.2 #16, §1.3 #16, shu mashinada
# o'lchangan):
#     crw-rw---- 1 root kvm 10, 232 /dev/kvm     <- device node BOR
#     lsmod -> kvm_amd, kvm                       <- modullar yuklangan
#     id -> `kvm` guruhida EMAS
#     test -r / test -w -> IKKISI HAM "not"
#     doctor #16 kvm_access -> WARN "mavjud, lekin ruxsat yo'q"
# 07 §8 jadvali: "QEMU lab hozir mumkin emas."
#
# CHEKLOV (09 §6.1): KVM'siz QEMU TCG emulyatsiyasiga tushadi. TCG'da timing
# 10-30x sekin va nolinear, demak PREREGISTRATION.md §6 downtime/latency
# o'lchovlari va §1 vaqt disiplinasi TCG ostida HAQIQIY EMAS.
# QOIDA: doctor'ning kvm_access tekshiruvi PASS bermaguncha guest'da birorta
# TIMING o'lchovi o'tkazilmaydi.
if [ -e /dev/kvm ]; then
  if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
    log "/dev/kvm: allaqachon o'qiladi+yoziladi"
  else
    log "/dev/kvm: ruxsat yo'q -> ACL qo'shiladi (guruh o'zgarishi relogin talab qiladi)"
    # NEGA ACL afzal: `usermod -aG kvm` yangi login sessiyasini talab qiladi;
    # ACL darhol kuchga kiradi. revix/cli.py:check_kvm_access() docstring'i
    # ham aynan shuni aytadi: qaror ACL asosida, guruh a'zoligi faqat
    # ma'lumot uchun (chunki guruh tekshiruvi yolg'on manfiy beradi).
    sudo setfacl -m "u:$(id -un):rw" /dev/kvm
    sudo usermod -aG kvm "$(id -un)" || warn "usermod muvaffaqiyatsiz -- ACL yetarli bo'lishi kerak"
  fi
else
  warn "/dev/kvm YO'Q -- KVM modul yuklanmagan. QEMU TCG'ga tushadi."
  warn "Bu holda guest'da FAQAT funksional smoke mumkin; TIMING o'lchovi QILINMAYDI (09 §6.1)."
fi

# --- (4) natijani qayd etish ------------------------------------------------
mkdir -p "$OUT_DIR"
{
  printf 'host-prepare: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'kernel: %s\n' "$(uname -r)"
  printf 'kvm_readable: %s\n' "$([ -r /dev/kvm ] && echo yes || echo no)"
  printf 'kvm_writable: %s\n' "$([ -w /dev/kvm ] && echo yes || echo no)"
  printf 'mmdebstrap: %s\n' "$(mmdebstrap --version 2>&1 | head -1)"
  printf 'xorriso: %s\n' "$(xorriso --version 2>&1 | head -1)"
  printf 'mksquashfs: %s\n' "$(mksquashfs -version 2>&1 | head -1)"
} > "$OUT_DIR/host-prepare.txt"

log "tayyor. Qayd: $OUT_DIR/host-prepare.txt"
log "Keyingi qadam: bash iso/build-all.sh"
