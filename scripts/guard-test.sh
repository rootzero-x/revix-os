#!/usr/bin/env bash
# REVIX guard integratsiya testi.
#
# MAQSAD: guard'ning haqiqiy memory pressure ostida chegarani belgilangan vaqt
# ichida aniqlab, revixlab.slice subtree'sini o'ldirishini TASDIQLASH.
#
# Reja bo'yicha bu test keyingi HAR BIR qadamni gate qiladi: guard to'g'ri
# ishlamasa hech qanday pressure eksperimenti o'tkazilmaydi.
#
# XAVFSIZLIK: pressure davomiyligi oomd ning 20 s sustained shartidan ANCHA
# qisqa (default 8 s), va IKKI mustaqil vaqt chegarasi bor:
#   1) generator'ning o'z --max-seconds
#   2) systemd RuntimeMaxSec=
# Ular chegaraga bog'liq emas, demak PSI qanday bo'lishidan qat'i nazar
# pressure to'xtaydi.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${OUT:-$(mktemp -d)}"
WATCH="${WATCH:-user}"          # user | lab
PRESS_SECONDS="${PRESS_SECONDS:-8}"
RUNTIME_MAX="${RUNTIME_MAX:-12}"
CAP_MB="${CAP_MB:-768}"
CHUNK_MB="${CHUNK_MB:-32}"
MODE="${MODE:-ramp}"
TARGET_RATE="${TARGET_RATE:-0.5}"
BASE_MB="${BASE_MB-}"   # bo'sh = modul memory.high dan avtomatik aniqlaydi
STEP_MB="${STEP_MB:-16}"
OBS_SECONDS="${OBS_SECONDS:-22}"
FULL_AVG10="${FULL_AVG10:-85.0}"
SOME_AVG10="${SOME_AVG10:-90.0}"
RATE2S="${RATE2S:-0.98}"   # modul default'i bilan mos
SUSTAIN_RATE="${SUSTAIN_RATE:-0.35}"
SUSTAIN_MAX="${SUSTAIN_MAX:-15.0}"   # modul default'i bilan MOS (guard.py DEFAULTS)

U="$(python3 -c 'from revix import cgroup as c; print(c.user_service_cgroup())')"
LAB="$U/revixlab.slice"
MON="$U/revixmon.slice"
case "$WATCH" in
  user) WATCH_CG="$U" ;;
  lab)  WATCH_CG="$LAB" ;;
  *) echo "WATCH user|lab bo'lishi kerak" >&2; exit 2 ;;
esac

echo "OUT=$OUT"
echo "kuzatiladi: $WATCH ($WATCH_CG)"
echo "runaway chegaralari: full_avg10=$FULL_AVG10 some_avg10=$SOME_AVG10 rate2s=$RATE2S"
echo "davomiylik: >=${SUSTAIN_RATE} tezlik, ${SUSTAIN_MAX}s dan uzoq -> trip"
echo "pressure: mode=$MODE ${PRESS_SECONDS}s, cap ${CAP_MB}M, RuntimeMaxSec=${RUNTIME_MAX}s"
[ "$MODE" = pi ] && echo "  PI nishon: $TARGET_RATE, baza ${BASE_MB}M, qadam ${STEP_MB}M"
echo

# --- pre-flight -------------------------------------------------------------
echo "--- pre-flight ---"
if systemctl --user --quiet is-active revix-press.service 2>/dev/null; then
  echo "XATO: revix-press.service allaqachon ishlayapti" >&2; exit 1
fi
python3 - "$OUT" "$LAB" <<'PY'
import json, sys
from revix import cgroup as cg
out, lab = sys.argv[1], sys.argv[2]
mi = cg.meminfo()
base = {
    "mem_available_kb": mi.get("MemAvailable"),
    "mem_free_kb": mi.get("MemFree"),
    "vmstat_oom_kill": cg.vmstat().get("oom_kill"),
    "lab_memory_events": cg.read_keyed(f"{lab}/memory.events"),
    "user_memory_pressure": cg.parse_psi(cg.read_text(f"{cg.user_service_cgroup()}/memory.pressure")),
}
json.dump(base, open(f"{out}/baseline.json", "w"), indent=2)
print("  MemAvailable kB:", base["mem_available_kb"])
print("  vmstat oom_kill:", base["vmstat_oom_kill"])
PY
CLAUDE_PIDS="$(pgrep -f 'claude-desktop --type=renderer' | tr '\n' ' ')"
CHROME_PIDS="$(pgrep -f 'chrome --type=renderer' | head -3 | tr '\n' ' ')"
echo "  kuzatiladigan Claude renderer PID'lar: $CLAUDE_PIDS"
echo "  kuzatiladigan Chrome renderer PID'lar: $CHROME_PIDS"

# --- guard (BIRINCHI ishga tushadi) ----------------------------------------
echo; echo "--- guard ishga tushiriladi (revixmon.slice) ---"
systemd-run --user --slice=revixmon.slice --unit=revix-guard \
  --working-directory="$REPO" --collect \
  --property=MemoryMax=128M --property=MemorySwapMax=0 \
  python3 -m revix.guard \
    --watch-cgroup "$WATCH_CG" --lab-cgroup "$LAB" \
    --log "$OUT/guard.jsonl" --trip-file "$OUT/trip.json" \
    --session-id guard-test --max-seconds "$OBS_SECONDS" \
    --user-full-avg10-max "$FULL_AVG10" \
    --user-some-avg10-max "$SOME_AVG10" \
    --user-full-rate2s-max "$RATE2S" \
    --sustain-rate-threshold "$SUSTAIN_RATE" \
    --sustain-max-seconds "$SUSTAIN_MAX" >/dev/null 2>&1
sleep 0.5
systemctl --user --quiet is-active revix-guard.service || { echo "XATO: guard ishga tushmadi" >&2; exit 1; }
echo "  guard faol"

# --- sampler ---------------------------------------------------------------
echo "--- psi_sampler ishga tushiriladi (revixmon.slice) ---"
systemd-run --user --slice=revixmon.slice --unit=revix-sampler \
  --working-directory="$REPO" --collect \
  --property=MemoryMax=128M --property=MemorySwapMax=0 \
  python3 -m revix.psi_sampler --with-host --with-user \
    --scope "lab=$LAB" --scope "mon=$MON" \
    --csv "$OUT/psi.csv" --events "$OUT/sampler.jsonl" \
    --hz 10 --max-seconds "$OBS_SECONDS" --session-id guard-test >/dev/null 2>&1
sleep 2   # pressure'dan oldingi baza namunalari
echo "  sampler faol, 2 s baza yig'ildi"

# --- pressure --------------------------------------------------------------
echo "--- pressure generatori ishga tushiriladi (revixlab.slice) ---"
T0=$(date +%s.%N)
systemd-run --user --slice=revixlab.slice --unit=revix-press \
  --working-directory="$REPO" --collect \
  --property=MemorySwapMax=0 --property=RuntimeMaxSec="${RUNTIME_MAX}s" \
  --property=OOMPolicy=continue \
  python3 -m revix.pressure --mode "$MODE" \
    --cgroup "$LAB" --cap-mb "$CAP_MB" --chunk-mb "$CHUNK_MB" \
    --target-rate "$TARGET_RATE" ${BASE_MB:+--base-mb "$BASE_MB"} --step-mb "$STEP_MB" \
    --interval-ms 200 --max-seconds "$PRESS_SECONDS" \
    --log "$OUT/pressure.jsonl" --session-id guard-test >/dev/null 2>&1
echo "  pressure faol"

# --- kutish ----------------------------------------------------------------
for i in $(seq 1 "$((RUNTIME_MAX + 4))"); do
  if ! systemctl --user --quiet is-active revix-press.service 2>/dev/null; then break; fi
  sleep 1
done
T1=$(date +%s.%N)
echo "  pressure tugadi, $(python3 -c "print(f'{$T1-$T0:.1f}')") s"

# --- guard/sampler tugashini kutish ---------------------------------------
echo "--- guard/sampler tugashini kutish ---"
for i in $(seq 1 "$((OBS_SECONDS + 6))"); do
  a=0
  systemctl --user --quiet is-active revix-guard.service 2>/dev/null && a=1
  systemctl --user --quiet is-active revix-sampler.service 2>/dev/null && a=1
  [ "$a" = 0 ] && break
  sleep 1
done

# --- teardown --------------------------------------------------------------
echo "--- teardown ---"
echo 1 > "$LAB/cgroup.kill" 2>/dev/null || true
systemctl --user stop revix-press.service revix-guard.service revix-sampler.service 2>/dev/null || true
systemctl --user reset-failed 2>/dev/null || true
echo "  tozalandi"

# --- tekshiruv -------------------------------------------------------------
echo; echo "--- post-flight tekshiruv ---"
for p in $CLAUDE_PIDS; do
  kill -0 "$p" 2>/dev/null && echo "  Claude PID $p TIRIK" || echo "  ❌ Claude PID $p O'LDI"
done
for p in $CHROME_PIDS; do
  kill -0 "$p" 2>/dev/null && echo "  Chrome PID $p TIRIK" || echo "  ❌ Chrome PID $p O'LDI"
done
echo "  oomd journal xabarlari (oxirgi 2 daqiqa):"
journalctl --since "2 min ago" -u systemd-oomd --no-pager -q 2>/dev/null | tail -5 || echo "    (o'qilmadi yoki yo'q)"

echo; echo "NATIJALAR: $OUT"
