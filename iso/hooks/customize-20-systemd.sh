#!/usr/bin/env bash
# mmdebstrap customize-hook: systemd / cgroup / live boot sozlamalari.
#
# BU SKRIPT BAJARILMADI, sabab: guard kalibratsiyasi davom etmoqda.
#
# $1 = rootfs yo'li.
#
# Har bir sozlama AYNAN BIR `revix doctor` tekshiruvi yoki
# 00-pilot-topologiya.md §4 bandi uchun. "Shunday qilish yaxshi" degan
# umumiy sabab bo'yicha hech narsa qo'shilmaydi.

set -euo pipefail

ROOTFS="${1:?rootfs path berilmadi (argument 1)}"
MEASURE_USER="${REVIX_MEASURE_USER:-revix}"
MEASURE_UID="${REVIX_MEASURE_UID:-1000}"

echo "[hook-20] systemd va cgroup sozlamalari"

# --- (1) o'lchov foydalanuvchisi --------------------------------------------
#
# NEGA root EMAS: butun harness privilegiyasiz ishlashga mo'ljallangan
# (INSTALLATION.md §1: "P1 uchun root kerak emas. Bu dizayn qarori, tasodif
# emas"; docs/research/04-novelty-statement.md C4). Image root bilan
# ishlatilsa, u da'vo IMAGE ICHIDA buziladi va `user@UID.service` ierarxiyasi
# (doctor #6 psi_cgroup) umuman tug'ilmaydi.
chroot "$ROOTFS" /usr/sbin/useradd \
  --create-home --shell /bin/bash \
  --uid "$MEASURE_UID" "$MEASURE_USER" 2>/dev/null || true

# NEGA parolsiz autologin: image headless (09 §7) va serial console orqali
# ishlatiladi; smoke test interaktiv parol so'rasa avtomatlashtirilmaydi.
# CHEKLOV: bu image'ni ISHONCHSIZ TARMOQQA chiqarish uchun YAROQSIZ qiladi.
# U tadqiqot appliance'i, deployment artifact'i EMAS (09 §0).
chroot "$ROOTFS" /usr/bin/passwd -d "$MEASURE_USER" 2>/dev/null || true
mkdir -p "$ROOTFS/etc/systemd/system/serial-getty@ttyS0.service.d"
cat > "$ROOTFS/etc/systemd/system/serial-getty@ttyS0.service.d/10-autologin.conf" <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin ${MEASURE_USER} --noclear %I \$TERM
EOF

# --- (1b) root yo'li va diagnostika huquqlari ------------------------------
#
# TUZATISH (11-iso-qurilish-jurnali.md, bug #13). Birinchi boot'da
# o'lchangan: image ichida root bo'lishning HECH QANDAY yo'li yo'q edi.
# Sabab va oqibatlari `iso/config.sh` dagi PKGS_TOOLS izohida.
#
# NEGA NOPASSWD: image HEADLESS va serial console orqali avtomatlashtirilgan
# ishlatiladi (09 §7); interaktiv parol so'rovi smoke test'ni ham, kampaniya
# skriptini ham bloklaydi. Parolsiz autologin allaqachon shu sababga tayanadi.
# CHEKLOV: bu image'ni ishonchsiz tarmoqqa chiqarish uchun YAROQSIZ qiladi.
install -d -m 0750 "$ROOTFS/etc/sudoers.d"
printf '%s ALL=(ALL) NOPASSWD: ALL\n' "$MEASURE_USER" \
  > "$ROOTFS/etc/sudoers.d/90-revix"
chmod 0440 "$ROOTFS/etc/sudoers.d/90-revix"

# NEGA `adm` va `systemd-journal`: root'siz `journalctl -u user@1000.service`
# "No journal files were opened due to insufficient permissions" beradi --
# ya'ni nosozlikni image ICHIDA diagnostika qilib bo'lmaydi. Birinchi
# boot'da aynan shu to'siqqa urildik.
chroot "$ROOTFS" /usr/sbin/usermod -aG adm,systemd-journal "$MEASURE_USER" 2>/dev/null || true

# NEGA linger: `user@UID.service` login sessiyasidan MUSTAQIL tirik
# bo'lishi kerak. Busiz serial sessiya uzilganda user manager va u bilan
# birga barcha transient `revix-*` unit'lar o'ladi -- aynan
# 07-wsl-muhit-tekshiruvlari.md §4.4 da o'lchangan nosozlikning takrori.
mkdir -p "$ROOTFS/var/lib/systemd/linger"
: > "$ROOTFS/var/lib/systemd/linger/$MEASURE_USER"

# --- (2) cgroup delegatsiyasi -----------------------------------------------
#
# doctor #3 delegated_controllers (`cpu memory pids` MAJBURIY) va
# doctor #4 io_delegation.
#
# NEGA `io` qo'shiladi: FAKT (07 §1.3 #4) -- host'da
# `/sys/fs/cgroup/cgroup.controllers` = `cpuset cpu io memory hugetlb pids rdma`,
# lekin `cgroup.subtree_control` = `cpu memory pids`; `io` rootdan pastga
# yoqilmagan, shuning uchun `io.max` YOZILMAYDI.
# PREREGISTRATION.md §0 shu sababli "Nazorat qilinadigan IO stall"ni
# qamrovdan chiqaradi, va INSTALLATION.md §4 uni **fault class 6** deb
# nomlaydi. Guest'da biz root'miz -> `io` ni yoqamiz -> fault class 6
# OCHILADI. Bu image'ning asosiy ilmiy sababi (09 §1).
#
# GIPOTEZA (09 §8 G5): bu sozlama guest'da ishlaydi. O'lchovi: doctor #4
# io_delegation PASS va `revixlab.slice/io.max` ga yozish rc=0.
install -D -m 0644 \
  "${REVIX_PACKAGING_DIR:?}/systemd/user@.service.d/10-revix-delegate.conf" \
  "$ROOTFS/etc/systemd/system/user@.service.d/10-revix-delegate.conf"

install -D -m 0644 "${REVIX_PACKAGING_DIR}/systemd/revix-io-delegate.service" \
  "$ROOTFS/etc/systemd/system/revix-io-delegate.service"
chroot "$ROOTFS" /usr/bin/systemctl enable revix-io-delegate.service

# --- (3) swap ---------------------------------------------------------------
#
# doctor #11 swap_headroom. revix/cli.py:check_swap_headroom() kodi o'qildi:
# `if total == 0: return ... WARN` -- ya'ni swap yo'qligi FAIL emas, WARN.
# Demak 0-FAIL qabul mezoni swap'ga BOG'LIQ EMAS.
# Shunga qaramay swapfile qo'shiladi, chunki o'sha tekshiruvning
# `consequence` matni sababni aytadi: "Swap butunlay yo'q bo'lsa reclaim
# yo'li qisqa: kernel OOM killer'ga tezroq yetiladi." Guard'ning qoldiq
# riski shundan oshadi.
# Eksperiment slice'ining o'z siyosati o'zgarmaydi: `MemorySwapMax=0`
# (00-pilot-topologiya.md §2).
install -D -m 0644 "${REVIX_PACKAGING_DIR}/systemd/revix-swapfile.service" \
  "$ROOTFS/etc/systemd/system/revix-swapfile.service"
chroot "$ROOTFS" /usr/bin/systemctl enable revix-swapfile.service

# --- (4) system slice shabloni -- O'RNATILADI, YOQILMAYDI -------------------
#
# NEGA o'rnatiladi: 00-pilot-topologiya.md §4 va SECURITY.md §4.1 harness'ni
# system slice'ga ko'chirishni "oomd kill scope'idan butunlay chiqish --
# guard'ning qoldiq riskini yopadigan YAGONA to'liq yechim" deb nomlaydi.
# NEGA YOQILMAYDI: bu o'lchov topologiyasining o'zgarishi, demak
# PREREGISTRATION.md §15 muhit fingerprint'iga ta'sir qiladi. Qaror frozen
# hujjat egasiniki, meniki emas (09 §7).
install -D -m 0644 "${REVIX_PACKAGING_DIR}/systemd/revix-harness.slice" \
  "$ROOTFS/etc/systemd/system/revix-harness.slice"

# --- (4b) dashboard (revix/gui.py) -- boot'da o'zi ishga tushadi ------------
#
# NEGA: image headless; foydalanuvchi ISO'ni boot qilgach dashboard'ni
# qo'lda `--host ... --allow-remote` bilan ishga tushirishni bilishi shart
# bo'lmasligi kerak. Unit'ning BARCHA qarorlari (system manager, User=revix,
# default loopback, remote faqat kernel cmdline `revix.dashboard=remote`
# bilan, o'lchovga ta'siri) unit faylining o'z izohida.
#
# NEGA FAIL-CLOSED tekshiruv: unit `User=revix`, `/run/user/1000`,
# `user@1000.service` ni QATTIQ yozadi (system unit'da `User=` uchun
# specifier yo'q). MEASURE_USER/MEASURE_UID o'zgartirilsa unit JIMGINA
# noto'g'ri foydalanuvchining bus'iga ulanardi -- build'ni shu yerda to'xtatamiz.
if [ "$MEASURE_USER" != "revix" ] || [ "$MEASURE_UID" != "1000" ]; then
  echo "[hook-20] XATO: revix-dashboard.service User=revix/UID 1000 ni qattiq yozadi," >&2
  echo "[hook-20]       lekin MEASURE_USER=$MEASURE_USER MEASURE_UID=$MEASURE_UID (fail-closed)" >&2
  exit 1
fi
# NEGA system manager (`/etc/systemd/system`), user manager EMAS: dashboard
# `user@1000.service` ichida tug'ilsa o'lchov scope'ini ifloslantiradi va
# `revix-*` glob'i (iso/lib/common.sh REVIX_UNIT_GLOB) uni qoldiq unit deb
# rad etadi. Asoslash unit faylida (1) bo'lim.
install -D -m 0644 "${REVIX_PACKAGING_DIR}/systemd/revix-dashboard.service"   "$ROOTFS/etc/systemd/system/revix-dashboard.service"
chroot "$ROOTFS" /usr/bin/systemctl enable revix-dashboard.service
# NEGA user manager papkasida NUSXA YO'Q -- tekshiriladi: u bo'lsa
# `systemctl --user list-units "revix-*"` uni ushlaydi.
if [ -e "$ROOTFS/etc/systemd/user/revix-dashboard.service" ]; then
  echo "[hook-20] XATO: revix-dashboard.service user manager papkasida (revix-* glob'iga tushadi)" >&2
  exit 1
fi

# --- (4c) grafik sessiya (revix.gui=1) -- uchinchi boot bandi ----------------
#
# NEGA: foydalanuvchi dashboard'ni VirtualBox oynasining ichida ko'rishni
# so'radi. Asoslash va barcha qarorlar unit faylining o'z izohida
# (`packaging/systemd/revix-gui.service`). Bu YERDA muhimi: ikkita mavjud band
# (default va `revix.dashboard=remote`) O'ZGARMASLIGI shart.
#   * unit YOQILADI (`enable`), lekin `ConditionKernelCommandLine=revix.gui=1`
#     uni faqat uchinchi bandda ishga tushiradi; boshqa bandlarda `skipped`.
#   * `seatd` paketi postinst'da o'zini `multi-user.target` ga YOQIB qo'yadi --
#     bu default bandlarda yangi ishlayotgan servis bo'lardi. Shuning uchun
#     uni `disable` qilamiz va u FAQAT `revix-gui.service` ning `Wants=` i
#     orqali ishga tushadi. Quyida tekshiriladi (fail-closed).
install -D -m 0644 "${REVIX_PACKAGING_DIR}/systemd/revix-gui.service" \
  "$ROOTFS/etc/systemd/system/revix-gui.service"
chroot "$ROOTFS" /usr/bin/systemctl enable revix-gui.service
chroot "$ROOTFS" /usr/bin/systemctl disable seatd.service
# `Wants=` Condition'dan OLDIN bajariladi: faqat `disable` YETARLI EMAS edi -- default bandda seatd
# baribir ishga tushdi (o'lchandi). Drop-in uni ham kernel buyruq satriga bog'laydi.
install -D -m 0644 "${REVIX_PACKAGING_DIR}/systemd/seatd.service.d/10-revix-gui.conf" \
  "$ROOTFS/etc/systemd/system/seatd.service.d/10-revix-gui.conf"
# `Conflicts=getty@tty1.service` ham Condition'dan OLDIN ishlaydi (default bandda tty1 login yo'qoldi --
# o'lchandi); shuning uchun getty@tty1'ga teskari Condition drop-in'i qo'yiladi.
install -D -m 0644 "${REVIX_PACKAGING_DIR}/systemd/getty@tty1.service.d/10-revix-gui.conf" \
  "$ROOTFS/etc/systemd/system/getty@tty1.service.d/10-revix-gui.conf"
if [ -e "$ROOTFS/etc/systemd/system/multi-user.target.wants/seatd.service" ]; then
  echo "[hook-20] XATO: seatd.service multi-user.target'ga yoqilgan -- default bandlar o'zgarardi" >&2
  exit 1
fi
if [ -e "$ROOTFS/etc/systemd/user/revix-gui.service" ]; then
  echo "[hook-20] XATO: revix-gui.service user manager papkasida (revix-* glob'iga tushadi)" >&2
  exit 1
fi

# --- (5) systemd-oomd ATAYLAB YO'Q ------------------------------------------
#
# 09 §4.4 ni to'liq o'qing. Qisqasi: (a) image'da desktop sessiyasi yo'q --
# oomd himoya qiladigan narsa yo'q; (b) oomd o'rnatilsa u slice'larni
# o'ldirib O'LCHOVNING O'ZIGA aralashadi; (c) guard mustaqil va 00 §6
# qadam 3 bo'yicha baribir sinaladi.
# CHEKLOV: demak image `01`/`00` tasvirlagan "oomd armed desktop" muhitini
# QAYTA ISHLAB CHIQARMAYDI. 04-novelty-statement.md C4 ning o'sha da'vosini
# sinash HOST'da qoladi.
# Qaror fingerprint'ga yoziladi (50-fingerprint.sh).
if chroot "$ROOTFS" /usr/bin/dpkg-query -W systemd-oomd >/dev/null 2>&1; then
  echo "[hook-20] XATO: systemd-oomd o'rnatilgan -- bu ATAYLAB bo'lmasligi kerak (09 §4.4)" >&2
  exit 1
fi

# --- (6) o'lchovga aralashadigan fon xizmatlarini o'chirish ------------------
#
# NEGA: PREREGISTRATION.md §8 confound nazorati. Davriy ravishda uyg'onadigan
# timer'lar CPU va IO pressure kiritadi, bu esa trial ichidagi PSI
# o'lchovini (§7 `total=` akkumulyatori) ifloslantiradi -- va u loyihaning
# MARKAZIY o'zgaruvchisi.
for u in apt-daily.timer apt-daily-upgrade.timer \
         fstrim.timer man-db.timer e2scrub_all.timer \
         systemd-tmpfiles-clean.timer; do
  chroot "$ROOTFS" /usr/bin/systemctl disable "$u" 2>/dev/null || true
  chroot "$ROOTFS" /usr/bin/systemctl mask "$u" 2>/dev/null || true
done

# NEGA journald volatile + cheklangan: 00-pilot-topologiya.md §3.4
# "journald flooding" ni xavf deb sanaydi. Volatile storage diskka yozishni
# (va u bilan IO pressure'ni) olib tashlaydi.
mkdir -p "$ROOTFS/etc/systemd/journald.conf.d"
cat > "$ROOTFS/etc/systemd/journald.conf.d/10-revix.conf" <<'EOF'
[Journal]
Storage=volatile
RuntimeMaxUse=256M
RateLimitIntervalSec=0
RateLimitBurst=0
EOF

# --- (7) live boot ----------------------------------------------------------
# NEGA `boot=live`: live-boot initramfs squashfs'ni root sifatida ko'taradi.
# Kernel buyruq satri 40-make-iso.sh da bootloader konfiguratsiyasida.
echo "revix-appliance" > "$ROOTFS/etc/hostname"
cat > "$ROOTFS/etc/hosts" <<'EOF'
127.0.0.1	localhost
127.0.1.1	revix-appliance
::1		localhost ip6-localhost ip6-loopback
EOF

echo "[hook-20] tayyor"
