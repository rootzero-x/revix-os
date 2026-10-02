#!/usr/bin/env bash
# REVIX image: QEMU test rejasi.
#
# BU SKRIPT BAJARILMADI, sabab: guard kalibratsiyasi davom etmoqda.
# Qo'shimcha sabab: /dev/kvm ga kirish YO'Q (pastga qarang).
#
# ==========================================================================
# AKSELERATSIYA -- o'lchangan holat
# ==========================================================================
# FAKT (07-wsl-muhit-tekshiruvlari.md §1.2 #16 va §1.3 #16, SHU mashinada):
#     crw-rw---- 1 root kvm 10, 232 /dev/kvm     <- device node BOR
#     lsmod -> kvm_amd, kvm                      <- modullar yuklangan
#     id -> `kvm` guruhida EMAS
#     test -r / test -w -> IKKISI HAM "not"
#     doctor #16 kvm_access -> WARN "mavjud, lekin ruxsat yo'q"
# 07 §8 jadvali xulosa qiladi: "QEMU lab hozir mumkin emas."
#
# INSTALLATION.md §4 "Shu mashinada KVM tekshirilgan" deydi -- lekin u
# AVVALGI mashinaga (01 §8, ACL `user:rootzero:rw-`) ishora qiladi. Bu
# 07 §9 ning OQ-4 ochiq savoli.
#
# CHEKLOV (JIDDIY): KVM'siz QEMU TCG emulyatsiyasiga tushadi. TCG'da timing
# 10-30x sekin va NOLINEAR. PREREGISTRATION.md §6 (downtime va latency) va
# §1 (vaqt disiplinasi) o'lchovlari TCG ostida HAQIQIY EMAS.
#
# QOIDA: `revix doctor` ning `kvm_access` tekshiruvi HOST'da PASS bermaguncha
# guest'da BIRORTA TIMING o'lchovi o'tkazilmaydi. TCG'da faqat FUNKSIONAL
# smoke (boot bo'ladimi, doctor ishlaydimi) mumkin, va natija TIMING
# sifatida YOZILMAYDI.
# ==========================================================================

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./config.sh
. "$HERE/config.sh"
# shellcheck source=./lib/common.sh
. "$HERE/lib/common.sh"

require_not_root
require_clean_env

ISO_PATH="$OUT_DIR/$ISO_NAME"
[ -f "$ISO_PATH" ] || die "ISO yo'q: $ISO_PATH -- avval bash iso/build-all.sh"

# --- akseleratsiya qarori ---------------------------------------------------
ACCEL="tcg"
TIMING_VALID="no"
if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
  ACCEL="kvm"
  TIMING_VALID="yes"
  log "/dev/kvm: o'qiladi+yoziladi -> accel=kvm, timing o'lchovi QONUNIY"
else
  warn "/dev/kvm ga kirish YO'Q -> accel=tcg."
  warn "TCG'da timing 10-30x sekin va nolinear -> PREREGISTRATION.md §6/§1 o'lchovlari HAQIQIY EMAS."
  warn "Bu rejimda FAQAT funksional smoke mumkin. Natija TIMING sifatida YOZILMAYDI (09 §6.1)."
fi

# --- QEMU parametrlari ------------------------------------------------------
#
# NEGA -m 6144: doctor #10 memory_headroom >= 3.4 GiB MemAvailable talab
#   qiladi (revix/cli.py: PLANNED_CEILING_KB = 2 GiB shift +
#   GUARD_MEM_FLOOR_KB guard poli), va cli.py yana +1 GiB "qulay zaxira"
#   hisoblaydi. 4 GiB bilan tekshiruv CHEGARADA turadi; 6 GiB zaxira
#   qoldiradi.
# NEGA -smp 4: CPUQuota=400% siyosati (00-pilot-topologiya.md §2) kamida
#   4 vCPU ni nazarda tutadi. 07 §8: host'da 12 vCPU, lekin hammasini
#   guest'ga berish host'dagi experiment/guard-recal ni buzadi.
# NEGA alohida virtio disk: IO fault injection (dm-delay/dm-flakey, fault
#   class 6) YOZILADIGAN blok qurilmani talab qiladi; live ISO read-only.
#   Bu aynan image'ning ilmiy sababi (09 §1).
# NEGA -nographic: image HEADLESS (09 §7). GUI guest'da fon yuk kiritadi va
#   PREREGISTRATION.md §8 confound nazoratini buzadi.
VM_MEM_MB="${VM_MEM_MB:-6144}"
VM_SMP="${VM_SMP:-4}"
SCRATCH="$OUT_DIR/scratch.qcow2"

log "BU QADAM BAJARILMADI (guard kalibratsiyasi davom etmoqda)."
log "Quyidagi buyruqlar HUJJAT sifatida -- ular bajarilmadi."

cat <<EOF

--- (1) scratch disk (IO fault injection uchun) ---
qemu-img create -f qcow2 "$SCRATCH" 20G

--- (2) boot ---
qemu-system-x86_64 \\
  -machine q35,accel=${ACCEL} -cpu host -smp ${VM_SMP} -m ${VM_MEM_MB} \\
  -cdrom "$ISO_PATH" \\
  -drive file="$SCRATCH",if=virtio,format=qcow2 \\
  -nographic -serial mon:stdio

--- (3) guest ICHIDA, SHU TARTIBDA ---
# Qabul mezoni: 0 FAIL. Bu mezon MASHINA tomonidan tekshiriladi.
revix doctor --json | tee /tmp/doctor.json
jq '[.checks[]|select(.status=="FAIL")]|length' /tmp/doctor.json    # => 0

# SUT build'i (-Werror toza bo'lishi SHART -- revix/Makefile izohi:
# "SUT o'lchov asbobi. Ogohlantirishlar ... o'lchov xatosiga aylanadi")
make -C ${INSTALL_PREFIX}/revix all

# unit suite
cd ${INSTALL_PREFIX} && python3 -m pytest tests/ -q

# >>> GUARD TESTI <<<  00-pilot-topologiya.md §6 qadam 3 -- GATE.
# "3-qadam 4-qadamdan oldin bajarilishi shart. Retrofit qilinmaydi."
# Guest YANGI mashina, demak host'ning guard kalibratsiyasi MEROS
# QILINMAYDI (07 "Xulosa -- build tartibi": "Har qanday pressure
# eksperimentidan oldin guard testi va pressure dosing kalibratsiyasi bu
# mashinada QAYTA bajarilishi shart").
cd ${INSTALL_PREFIX} && bash scripts/guard-test.sh

# smoke trial (1 trial, P0) -- 00 §6 qadam 6
cd ${INSTALL_PREFIX} && python3 -m revix.driver --dry-run --help
cd ${INSTALL_PREFIX} && python3 -m revix.validate --help

--- (4) io delegatsiyasini tekshirish (GIPOTEZA G5, fault class 6) ---
# doctor #4 io_delegation PASS bo'lishi KERAK (host'da WARN edi, 07 §1.3 #4).
jq '.checks[]|select(.key=="io_delegation")' /tmp/doctor.json
cat /sys/fs/cgroup/cgroup.subtree_control        # `io` ko'rinishi KERAK

--- (5) PID 1 barqarorligi (GIPOTEZA G8) ---
# 07 §4.4: WSL'da PID 1 ~10-15 s idle'dan keyin QAYTA ishga tushadi va
# boot_id O'ZGARMAYDI -> transient unit'lar o'ladi. 04-shartnoma §1.4 shu
# sababli guest_generation.pid1_starttime_ticks ni majburiy qildi.
# Guest'da bu marker butun kampaniya davomida O'ZGARMASLIGI kerak.
awk '{print \$22}' /proc/1/stat                   # kampaniya boshida va oxirida

EOF

cat <<'MSG'
[revix-iso] INTEGRITY:
  Hech qanday guest boot qilinmadi. `revix doctor` image ichida ishga
  tushirilmadi. Yuqoridagi "=> 0" kutilgan qiymat, O'LCHANGAN natija EMAS.
  Barcha mezonlar GIPOTEZA (09-iso-qurilishi.md §8).
MSG

exit 0
