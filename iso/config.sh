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

# NEGA ext4, /mnt/* EMAS: 07-wsl-muhit-tekshiruvlari.md §7.2 -- FAKT:
# /mnt/c = 9p/drvfs, 98% to'la, 10 G bo'sh; ext4 root'da 951 G. Build'ga
# ~25 G kerak, va /mnt/c ni to'ldirish Windows tomonini buzadi.
# scripts/sync-to-ext4.sh ayni shu fail-closed qoidani allaqachon qo'llaydi.
#
# TUZATISH (11-iso-qurilish-jurnali.md, bug #1): avval bu yerda
# `$HOME/revix-iso` yozilgan edi va build BIRINCHI qadamda o'ldi:
#
#   E: cannot create /home/snowden/revix-iso: Permission denied
#
# SABAB (o'lchangan, taxmin emas): `mmdebstrap --mode=unshare` uid map'ini
# /etc/subuid dan BITTA satr bilan quradi -- `/usr/bin/mmdebstrap:1469`:
#       push @result, ["u", 0, $subid, $num_subid];
# ya'ni namespace ichidagi uid 0 -> tashqi uid 100000, va
# FOYDALANUVCHINING O'Z uid'i (1000) UMUMAN MAP QILINMAYDI. Tasdiq:
#       $ unshare --user --map-auto --setuid 0 -- cat /proc/self/uid_map
#                0     100000      65536
# Demak namespace ichida `/home/snowden` egasi `nobody` bo'lib ko'rinadi, va
# uning rejimi `drwx------` -> namespace ICHIDA UMUMAN O'TIB BO'LMAYDI.
# $HOME 0700 bo'lgani uchun u `--mode=unshare` bilan PRINSIPIAL ravishda
# yaroqsiz; bu rejim yoki konfiguratsiya emas, STRUKTURA muammosi.
#
# NEGA /var/tmp: ota-katalog `drwxrwxrwt` (1777), demak namespace ichidan
# o'tish mumkin; fs ext4 (`stat -fc %T /var/tmp` -> ext2/ext3) va 951 G bo'sh
# -- ya'ni §7.2 ning ASL sababi (ext4, drvfs emas) buzilmaydi. $HOME'ning
# o'zini `chmod o+x` qilish YECHIM EMAS: u foydalanuvchining shaxsiy
# katalogi va uning rejimini o'zgartirish build skriptining ishi emas.
OUT_DIR="${OUT_DIR:-/var/tmp/revix-iso}"
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
#
# TUZATISH (11-iso-qurilish-jurnali.md, bug #12): `libpam-systemd` va
# `dbus-user-session` QO'SHILDI. Birinchi boot'da O'LCHANGAN natija:
#
#   $ systemctl status user@1000.service
#     Active: failed (Result: exit-code)
#     Process: 610 ExecStart=/usr/lib/systemd/systemd --user
#              (code=exited, status=1/FAILURE)
#     Error: code: 49 (Protocol driver not attached)
#   $ dpkg -l libpam-systemd
#     un  libpam-systemd <none>   <- UMUMAN O'RNATILMAGAN
#   $ echo $XDG_RUNTIME_DIR
#     (bo'sh)
#
# va shundan `revix doctor` da BEShTA FAIL kelib chiqdi -- hammasi bitta
# ildizdan:
#   delegated_controllers, io_delegation, psi_cgroup, cgroup_write
#     -> RuntimeError('user@1000.service cgroup topilmadi: ...')
#   leftover_state
#     -> "Failed to connect to user scope bus via local transport:
#         $DBUS_SESSION_BUS_ADDRESS and $XDG_RUNTIME_DIR not defined"
#
# NEGA bu HAL QILUVCHI: loyihaning BUTUN o'lchov qamrovi
# `user@UID.service` ierarxiyasi ichida yashaydi (00-pilot-topologiya.md §1:
# `revixlab.slice`/`revixmon.slice` `user@UID.service` ostida;
# `revix/cgroup.py:user_service_cgroup()` shu yo'lni hisoblaydi). U
# ishga tushmasa image BOOT BO'LADI, lekin BIRORTA trial o'tkaza OLMAYDI --
# ya'ni "ISO boot bo'ldi" rost bo'lib, image baribir FOYDASIZ bo'lardi.
#
# NEGA `libpam-systemd`: `pam_systemd.so` login paytida logind sessiyasini
# yaratadi va `XDG_RUNTIME_DIR` (`/run/user/1000`) ni o'rnatadi. Usiz
# `systemd --user` o'z runtime katalogini topa olmaydi.
# NEGA `dbus-user-session`: `user@UID.service` ichidagi session bus --
# `revix/units.py` transient unit'larni `systemd-run --user` orqali
# yaratadi, u esa session bus'ni talab qiladi.
# NEGA `--variant=important` ularni O'ZI tortib kelmadi: ikkisi ham
# Priority: optional/standard, demak "important" to'plamiga kirmaydi.
PKGS_BASE="systemd systemd-sysv dbus init libpam-systemd dbus-user-session"
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
#
# TUZATISH (11-iso-qurilish-jurnali.md, bug #16 va #17): `python3-gi` va
# `python3-matplotlib` QO'SHILDI. Ikkisi ham image ICHIDA, `pytest` bilan
# o'lchandi -- taxmin emas.
#
# NEGA python3-gi (bug #16) -- 12 ta ERROR:
#     E  ModuleNotFoundError: No module named 'gi'
#     revix/units.py:231: ModuleNotFoundError
#   `revix/units.py` D-Bus signal'larini kuzatish uchun GLib main loop'ini
#   (PyGObject) ishlatadi. U BUTUN `tests/unit/test_units.py` ni
#   yiqitadi -- ya'ni transient unit yaratish, `RestartSteps=` round-trip,
#   `preflight()`/`teardown()` -- harness'ning YADROSI sinalmay qoladi.
#   `python3-dbus` YETARLI EMAS: u alohida bog'liqlik.
#
# NEGA python3-matplotlib (bug #17) -- 2 ta FAILED:
#     tests/integration/test_chain.py::test_zanjir_figura
#     (test docstring: "analysis.json -> `revix.figures` (matplotlib kerak)")
#   `revix/cli.py` matplotlib'ni OPTIONAL_MODULES ga qo'yadi, demak
#   `doctor` uni yo'q bo'lsa faqat WARN qiladi -- lekin TEST SUITE uni
#   TALAB qiladi. Qabul mezoni (09 §4) `pytest tests/ -q` ni ham o'z
#   ichiga oladi, shuning uchun u image'da bo'lishi SHART.
#   Yon foyda: doctor #15 `python_modules` WARN -> PASS.
PKGS_PYTHON="python3 python3-pytest python3-psutil python3-dbus python3-gi python3-systemd python3-yaml python3-numpy python3-scipy python3-matplotlib"
# doctor #17/#18 git_present/git_clean -> git MAJBURIY (09 §5.1).
PKGS_REPO="git ca-certificates"
# Guest ichidagi diagnostika va privilegiyali tier vositalari.
# NEGA dmsetup/iproute2: fault class 6 va tc netem -- "root kerak =
# guest'ga tegishli" (00-pilot-topologiya.md §4).
#
# TUZATISH (bug #13): `sudo` QO'SHILDI. Birinchi boot'da o'lchangan holat:
# image ichida ROOT BO'LISHNING HECH QANDAY YO'LI YO'Q edi -- `sudo`
# o'rnatilmagan, root paroli Debian default'i bo'yicha QULFLANGAN (`*`),
# va `customize-20-systemd.sh` faqat O'LCHOV foydalanuvchisining parolini
# bo'shatadi (`passwd -d revix`).
#
# NEGA bu image'ning BUTUN asosiga zid: 09-iso-qurilishi.md §1 image'ni
# aynan "privilegiyali tier'larni ochish" uchun asoslaydi --
# 00-pilot-topologiya.md §4 ro'yxati: `io.max`, `dm-delay`/`dm-flakey`,
# `tc netem`, cgroup `cpuset` pinning, `drop_caches`, harness'ni system
# slice'ga ko'chirish. Ularning HAMMASI root talab qiladi. Root'siz image
# "root kerak = guest'ga tegishli" prinsipini BAJARMAYDI, ya'ni o'zining
# yagona ilmiy sababini bajarmaydi.
# Qo'shimcha: root'siz `journalctl -u user@1000.service` ham o'qilmaydi,
# demak nosozlikni image ICHIDA diagnostika qilib bo'lmaydi -- bu birinchi
# boot'da aynan shunday bo'ldi.
#
# CHEKLOV (oshkora, yashirilmaydi): `sudo` NOPASSWD bilan sozlanadi va
# o'lchov foydalanuvchisi parolsiz autologin qiladi. Bu image'ni ISHONCHSIZ
# TARMOQQA chiqarish uchun MUTLAQO YAROQSIZ qiladi. U tadqiqot
# appliance'i, deployment artifact'i EMAS (09 §0). Bu `customize-20`
# dagi parolsiz autologin uchun allaqachon yozilgan ogohlikning davomi.
PKGS_TOOLS="procps util-linux kmod less jq ca-certificates dmsetup iproute2 acl sudo"

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
