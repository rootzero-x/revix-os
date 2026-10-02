#!/usr/bin/env bash
# REVIX image build -- orkestratsiya (qadam 10 -> 50).
#
# BU SKRIPT BAJARILMADI, sabab: guard kalibratsiyasi davom etmoqda.
#
# NEGA alohida orkestrator: har qadam MUSTAQIL ishga tushirilishi mumkin
# bo'lishi kerak (qayta urinish, qismiy qayta qurish), lekin TARTIB
# majburiy. Orkestrator tartibni bir joyda qotiradi.
#
# NEGA 00-host-prepare.sh BU YERDA CHAQIRILMAYDI: u YAGONA privilegiyali
# skript va u NAZORAT ostida, alohida, bir marta ishlashi kerak
# (00-pilot-topologiya.md §4). Uni orkestratorga qo'shish privilegiyali
# qadamni "build'ning bir qismi" ga aylantirardi -- aynan §4 oldini
# olmoqchi bo'lgan narsa.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./config.sh
. "$HERE/config.sh"
# shellcheck source=./lib/common.sh
. "$HERE/lib/common.sh"

require_not_root
require_clean_env
require_sde
require_ext4_out "$OUT_DIR"
require_disk "$OUT_DIR" "$MIN_FREE_GB"

cat <<EOF
[revix-iso] REVIX research appliance image
[revix-iso]   QAMROV: Debian + REVIX o'lchov harness'i. Adaptive recovery
[revix-iso]   engine YO'Q (PREREGISTRATION.md §0, §13). Bu tadqiqot
[revix-iso]   appliance'i, "REVIX OS" EMAS (09-iso-qurilishi.md §0).
[revix-iso]
[revix-iso]   suite=$SUITE arch=$ARCH snapshot=$SNAPSHOT_TS
[revix-iso]   SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH
[revix-iso]   OUT_DIR=$OUT_DIR
EOF

if [ "${REVIX_ISO_CONFIRM:-}" != "yes" ]; then
  cat >&2 <<'MSG'

[revix-iso] TO'XTATILDI (fail-closed).

Build guest'ning xotira, disk va CPU sini TO'YINTIRADI. Agar bu mashinada
REVIX o'lchovi (guard kalibratsiyasi, pressure dosing, pilot) davom
etayotgan bo'lsa, build O'SHA O'LCHOVNI BUZADI -- va o'lchov qayta
takrorlanmaydi.

pre-flight tekshiruvi (revix/units.py require_clean() mantig'i) toza
chiqdi, lekin u FAQAT qoldiq unit va cgroup'ni ko'radi; u boshqa
worktree'da ishlayotgan tahlilni yoki host tomonidagi kampaniyani
KO'RMAYDI.

Shuning uchun oshkora tasdiq kerak:

    REVIX_ISO_CONFIRM=yes bash iso/build-all.sh
MSG
  exit 1
fi

for step in \
  10-build-rootfs.sh \
  20-record-manifest.sh \
  30-make-squashfs.sh \
  40-make-iso.sh \
  50-fingerprint.sh
do
  log "=== $step ==="
  bash "$HERE/$step"
done

log "=== tugadi ==="
log "ISO:         $OUT_DIR/$ISO_NAME"
log "manifest:    $OUT_DIR/manifest.txt"
log "fingerprint: $OUT_DIR/build-fingerprint.json"
log "checksum:    $OUT_DIR/SHA256SUMS"
log ""
log "Keyingi qadam: bash iso/99-qemu-smoke.sh"
log "DIQQAT: image boot bo'lishi va doctor 0 FAIL berishi -- GIPOTEZA (09 §8)."
