#!/usr/bin/env bash
# open-params kalibratsiyasi runner'i -- docs/architecture/13-ochiq-parametrlar-kalibratsiyasi.md
#
# TARTIB (10-pressure-dozalash.md §8.1 bilan bir xil):
#   pre-check -> marker pre -> pre-flight (toza) -> doctor (leftover_state)
#   -> slice dial'lari -> kernel tasdig'i -> SUT build -> GUARD (birinchi,
#   tiriklik tasdiqlanadi, FAIL-CLOSED) -> sampler -> controller (revixmon)
#   -> sampler stop -> GUARD stop (oxirgi) -> marker post -> teardown
#   -> drop-in tozalash -> post-flight (oom_kill, swap, doctor leftover_state)
#
# QULF: bu skript ~/.revix-exclusive ni OLMAYDI va BO'SHATMAYDI -- qulf
# butun o'lchov fazasi davomida (smoke + to'liq run) operator tomonidan
# ushlanadi. Skript faqat qulf O'ZIMIZDA ekanini tekshiradi (fail-closed).
#
# Hech bir o'lchanadigan jarayon shell'dan tug'ilmaydi: SUT/generator
# `revixlab.slice` da, guard/sampler/controller `revixmon.slice` da,
# hammasi `systemd-run --user` orqali. Shell faqat uy ishlarini qiladi.
set -u

RUN_ID="${RUN_ID:?RUN_ID kerak}"
WORK="${WORK:-$HOME/openparams-work}"
RUNS="${RUNS:-$HOME/revix-runs}"
PARTS="${PARTS:-A,B}"
A_EP="${A_EP:-24}"
B_MIN="${B_MIN:-48}"
B_MAXEP="${B_MAXEP:-16}"
A_COUNTS="${A_COUNTS:-}"
SEED="${SEED:-20261003}"
GIT_COMMIT="${GIT_COMMIT:-unknown}"
OUT="$RUNS/$RUN_ID"
UID_N="$(id -u)"
U_CG="/sys/fs/cgroup/user.slice/user-$UID_N.slice/user@$UID_N.service"
LAB_CG="$U_CG/revixlab.slice"
MON_CG="$U_CG/revixmon.slice"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$UID_N}"
BUS="unix:path=$XDG_RUNTIME_DIR/bus"
# Guard/sampler chegarasi: eng yomon holat (A: 3*A_EP*~60 s, B: 3*B_MAXEP*~45 s) + 600 s.
TOTAL=$(( 3*A_EP*60 + 3*B_MAXEP*45 + 600 ))

say() { echo "[$(date -u +%H:%M:%S)] $*"; }

marker() {
  local label="$1" out="$2"
  {
    echo "label=$label"
    echo "wall_utc=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
    echo "boot_id=$(cat /proc/sys/kernel/random/boot_id)"
    echo "uptime=$(cut -d' ' -f1 /proc/uptime)"
    echo "pid1_starttime_ticks=$(awk '{print $22}' /proc/1/stat)"
    echo "loadavg=$(cat /proc/loadavg)"
    echo "mem_available_kb=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)"
    echo "swap_free_kb=$(awk '/^SwapFree:/{print $2}' /proc/meminfo)"
    echo "vmstat_oom_kill=$(awk '/^oom_kill /{print $2}' /proc/vmstat)"
    echo "lab_swap_current=$(cat "$LAB_CG/memory.swap.current" 2>/dev/null || echo NA)"
    echo "lab_memory_events=$(tr '\n' ' ' < "$LAB_CG/memory.events" 2>/dev/null || echo NA)"
    echo "revix_units=$(systemctl --user list-units 'revix*' --all --no-legend --plain 2>/dev/null | tr '\n' ';')"
    echo "failed_units=$(systemctl --user list-units --state=failed --no-legend --plain 2>/dev/null | tr '\n' ';')"
    echo "interference=$(pgrep -x -l 'VBoxHeadless|mmdebstrap|mksquashfs|pytest' 2>/dev/null | tr '\n' ';')"
    echo "lock_holder=$(cat "$HOME/.revix-exclusive/holder" 2>/dev/null || echo NONE)"
    echo "journal_oom_hits=$(journalctl -b 0 --no-pager 2>/dev/null | grep -Eic 'oomd|out of memory|invoked oom' || true)"
  } > "$out"
  say "marker $label"; cat "$out"
}

teardown() {
  ( cd "$WORK" && python3 -c 'import json; from revix import units; print("teardown:", json.dumps(units.teardown()))' ) 2>&1 | tail -1
}
clear_dropins() {
  ( cd "$WORK" && python3 -c 'import json; from revix import units; print("removed:", json.dumps(units.clear_runtime_drop_ins()))' ) 2>&1 | tail -1
}
preflight() {
  ( cd "$WORK" && python3 -c 'import json; from revix import units; print(json.dumps(units.preflight()))' )
}
doctor_leftover() {
  ( cd "$WORK" && python3 -m revix.cli doctor --json 2>/dev/null ) | python3 -c '
import json, sys
r = json.load(sys.stdin)
for c in r.get("checks", []):
    if c.get("key") == "leftover_state":
        print("doctor leftover_state:", c.get("status"), "|", c.get("observed"))
        break
else:
    print("doctor leftover_state: TOPILMADI")
'
}

# --- 0. qulf va muhit ---------------------------------------------------------
case "$(cat "$HOME/.revix-exclusive/holder" 2>/dev/null)" in
  open-params*) ;;
  *) echo "ABORT: ~/.revix-exclusive qulfi bizda emas"; exit 75;;
esac
[ -d "$OUT" ] && { echo "ABORT: $OUT allaqachon bor (append-only)"; exit 1; }
mkdir -p "$OUT"
exec > >(tee -a "$OUT/runner.log") 2>&1
trap 'say "EXIT trap: teardown"; teardown; clear_dropins' EXIT

say "RUN $RUN_ID  parts=$PARTS A_EP=$A_EP A_COUNTS=$A_COUNTS SEED=$SEED B_MIN=$B_MIN B_MAXEP=$B_MAXEP total=${TOTAL}s commit=$GIT_COMMIT"
read -r L1 _ < /proc/loadavg
if python3 -c "import sys; sys.exit(0 if float('$L1') < 0.3 else 1)"; then
  say "loadavg1=$L1 < 0.3"
else
  echo "ABORT: loadavg1=$L1 >= 0.3"; exit 76
fi
if pgrep -x 'VBoxHeadless|mmdebstrap|mksquashfs' >/dev/null; then
  echo "ABORT: begona og'ir jarayon: $(pgrep -x -l 'VBoxHeadless|mmdebstrap|mksquashfs' | tr '\n' ';')"; exit 77
fi
echo "$GIT_COMMIT" > "$OUT/git_commit.txt"
marker pre "$OUT/marker-pre.txt"

# --- 1. pre-flight --------------------------------------------------------------
teardown >/dev/null; clear_dropins >/dev/null
PF=$(preflight); say "preflight: $PF"
case "$PF" in *'"clean": true'*) ;; *) echo "ABORT: pre-flight toza emas"; exit 1;; esac
doctor_leftover | tee "$OUT/doctor-pre.txt"

# --- 2. slice dial'lari (10 §1.1 bilan bir xil, MemoryMax=2G) ------------------
systemctl --user set-property --runtime revixlab.slice \
  MemoryMax=2G MemoryHigh=192M MemorySwapMax=0 TasksMax=256 CPUQuota=400% \
  || { echo "ABORT: set-property lab"; exit 1; }
systemctl --user set-property --runtime revixmon.slice MemoryMax=512M TasksMax=64 \
  || { echo "ABORT: set-property mon"; exit 1; }
systemctl --user start revixlab.slice revixmon.slice; sleep 0.3
{
  systemctl --user show revixlab.slice -p MemoryMax -p MemoryHigh -p MemorySwapMax -p TasksMax -p CPUQuotaPerSecUSec
  echo "kernel: memory.max=$(cat "$LAB_CG/memory.max") memory.high=$(cat "$LAB_CG/memory.high") memory.swap.max=$(cat "$LAB_CG/memory.swap.max") pids.max=$(cat "$LAB_CG/pids.max") cpu.max=$(cat "$LAB_CG/cpu.max")"
} | tee "$OUT/slice-props.txt"
grep -q 'memory.high=201326592' "$OUT/slice-props.txt" && grep -q 'memory.max=2147483648' "$OUT/slice-props.txt" \
  || { echo "ABORT: kernel dial'i kutilgandek emas"; exit 1; }

# --- 3. SUT build (ext4 nusxada) ---------------------------------------------
make -C "$WORK/revix" all 2>&1 | tail -2
ls -l "$WORK/revix/sut" || { echo "ABORT: sut yo'q"; exit 1; }
cc --version | head -1

# --- 4. GUARD BIRINCHI ----------------------------------------------------------
systemd-run --user --slice=revixmon.slice --unit=revix-guard --collect \
  --working-directory="$WORK" \
  -p MemoryMax=128M -p MemorySwapMax=0 -p RuntimeMaxSec=$((TOTAL+300))s \
  -p StandardOutput=null -p StandardError=null \
  python3 -m revix.guard --watch-cgroup "$U_CG" --lab-cgroup "$LAB_CG" \
    --log "$OUT/guard.jsonl" --trip-file "$OUT/trip.json" \
    --run-id "$RUN_ID" --session-id open-params --max-seconds "$TOTAL" >/dev/null 2>&1
for i in $(seq 1 30); do
  grep -q '"guard_start"' "$OUT/guard.jsonl" 2>/dev/null && break; sleep 0.5
done
if systemctl --user --quiet is-active revix-guard.service && grep -q '"guard_start"' "$OUT/guard.jsonl"; then
  say "guard FAOL (is-active + guard_start yozuvi)"
else
  echo "ABORT (FAIL-CLOSED): guard ishga tushmadi -> hech narsa boshlanmaydi"; exit 1
fi

# --- 5. sampler -------------------------------------------------------------------
systemd-run --user --slice=revixmon.slice --unit=revix-psi --collect \
  --working-directory="$WORK" \
  -p MemoryMax=128M -p MemorySwapMax=0 -p RuntimeMaxSec=$((TOTAL+300))s \
  -p StandardOutput=null -p StandardError=null \
  python3 -m revix.psi_sampler --with-host --with-user \
    --scope "lab=$LAB_CG" --scope "mon=$MON_CG" \
    --csv "$OUT/psi.csv" --events "$OUT/sampler.jsonl" --hz 10 \
    --max-seconds "$TOTAL" --run-id "$RUN_ID" --session-id open-params >/dev/null 2>&1
sleep 0.5
systemctl --user --quiet is-active revix-psi.service || { echo "ABORT: sampler"; exit 1; }
say "sampler FAOL"

# --- 6. controller (revixmon.slice, --wait) ----------------------------------------
say "controller boshlandi"
systemd-run --user --slice=revixmon.slice --unit=revix-opmeas --collect --wait \
  --working-directory="$WORK" \
  -p MemoryMax=256M -p MemorySwapMax=0 -p RuntimeMaxSec=$((TOTAL+120))s \
  -E OPEN_PARAMS_WORK="$WORK" -E XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
  -E DBUS_SESSION_BUS_ADDRESS="$BUS" \
  python3 "$WORK/scripts/open-params-measure.py" --out "$OUT" --run-id "$RUN_ID" \
    --parts "$PARTS" --a-episodes "$A_EP" --b-min-starts "$B_MIN" \
    --b-max-episodes "$B_MAXEP" --a-counts "$A_COUNTS" --seed "$SEED" > "$OUT/controller.stdout" 2>&1
CRC=$?
say "controller tugadi rc=$CRC"; tail -5 "$OUT/controller.stdout"
grep '"controller_end"\|"abort"\|"error"' "$OUT/events.jsonl" | tail -3

# --- 7. sampler, keyin GUARD (oxirgi) -------------------------------------------
systemctl --user stop revix-psi.service 2>/dev/null
systemctl --user stop revix-guard.service 2>/dev/null
for i in $(seq 1 30); do systemctl --user --quiet is-active revix-guard.service || break; sleep 1; done
say "guard to'xtadi; trip fayli: $( [ -e "$OUT/trip.json" ] && echo BOR || echo YO\'Q )"
grep -c '"guard_event"' "$OUT/guard.jsonl" | sed 's/^/guard_event yozuvlari: /'
tail -1 "$OUT/guard.jsonl" | cut -c1-400

# --- 8. post ----------------------------------------------------------------------
marker post "$OUT/marker-post.txt"
say "post-flight (teardown'dan OLDIN): oom_kill=$(awk '/^oom_kill /{print $2}' /proc/vmstat) lab_swap_current=$(cat "$LAB_CG/memory.swap.current" 2>/dev/null || echo NA)"
trap - EXIT
teardown; clear_dropins
PF=$(preflight); say "preflight (keyin): $PF"
doctor_leftover | tee "$OUT/doctor-post.txt"
diff <(grep -E '^(boot_id|pid1_starttime_ticks)=' "$OUT/marker-pre.txt") \
     <(grep -E '^(boot_id|pid1_starttime_ticks)=' "$OUT/marker-post.txt") \
  && say "boot_id va pid1_starttime O'ZGARMADI" || say "!!! guest O'ZGARDI"
diff <(grep '^vmstat_oom_kill=' "$OUT/marker-pre.txt") <(grep '^vmstat_oom_kill=' "$OUT/marker-post.txt") \
  && say "vmstat oom_kill O'ZGARMADI" || say "!!! oom_kill O'ZGARDI"
exit "$CRC"
