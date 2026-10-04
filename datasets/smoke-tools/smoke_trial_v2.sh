#!/usr/bin/env bash
# One smoke trial with the REAL driver (agent/pilot-ready). Requires the
# exclusive lock to be held by pilot-ready (checked, never taken here).
# Usage: smoke_trial.sh <name> <arm> <level> <seed>
set -u
NAME="$1"; ARM="$2"; LEVEL="$3"; SEED="$4"
WORK="$HOME/pilotready-work"
RUNS="$HOME/revix-runs"
RUN="$RUNS/$NAME"
SIDE="$RUNS/$NAME.pilotready"
S="$(dirname "$(readlink -f "$0")")"

grep -q '^pilot-ready ' "$HOME/.revix-exclusive/holder" 2>/dev/null || { echo "LOCK NOT HELD BY pilot-ready"; exit 9; }
[ -e "$RUN" ] && { echo "run dir exists: $RUN"; exit 9; }
mkdir -p "$SIDE"

marker() {
python3 - "$1" <<'EOF'
import json, os, sys, time
d = {}
d["phase"] = sys.argv[1]
d["boot_id"] = open("/proc/sys/kernel/random/boot_id").read().strip()
d["pid1_starttime_ticks"] = int(open("/proc/1/stat").read().rsplit(")", 1)[1].split()[19])
m = time.clock_gettime_ns(time.CLOCK_MONOTONIC) // 1000
r = time.clock_gettime_ns(time.CLOCK_REALTIME) // 1000
d["mono_us"], d["real_us"], d["real_minus_mono_us"] = m, r, r - m
d["oom_kill"] = int([l.split()[1] for l in open("/proc/vmstat") if l.startswith("oom_kill ")][0])
d["loadavg"] = open("/proc/loadavg").read().strip()
d["uptime_s"] = float(open("/proc/uptime").read().split()[0])
print(json.dumps(d))
EOF
}

leftover() {
  ( cd "$WORK" && python3 -m revix.cli doctor --json 2>/dev/null ) | python3 -c '
import json,sys
d=json.load(sys.stdin)
for c in d.get("checks") or d.get("results") or []:
    if c.get("key")=="leftover_state": print(c.get("status"), "|", c.get("observed"))'
}

echo "== pre"
pgrep -a 'VBoxHeadless|mmdebstrap|mksquashfs' && { echo "HEAVY PROCESS PRESENT"; exit 9; }
marker pre | tee "$SIDE/marker-pre.json"
leftover | tee "$SIDE/leftover-pre.txt"
systemctl --user list-units 'revix*' --all --no-legend | tee "$SIDE/units-pre.txt"

echo "== run $NAME arm=$ARM level=$LEVEL seed=$SEED"
cd "$WORK"
git rev-parse HEAD > "$SIDE/git_commit.txt"
git status --porcelain > "$SIDE/git_status.txt"
T0=$(date +%s.%N)
python3 -m revix.cli run --run-dir "$RUN" --seed "$SEED" --blocks 1 \
    --only "$ARM,$LEVEL" --allow-pressure --json > "$SIDE/driver.json" 2> "$SIDE/driver.stderr"
RC=$?
T1=$(date +%s.%N)
echo "driver rc=$RC wall_s=$(python3 -c "print(round($T1-$T0,3))")" | tee "$SIDE/driver.rc"
head -c 3000 "$SIDE/driver.json"; echo; tail -5 "$SIDE/driver.stderr"

echo "== post"
marker post | tee "$SIDE/marker-post.json"
leftover | tee "$SIDE/leftover-post.txt"
systemctl --user list-units 'revix*' --all --no-legend | tee "$SIDE/units-post.txt"
ls /sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/ | grep revix | tee "$SIDE/cgroups-post.txt"
python3 -m revix.validate --run-dir "$RUN" --sut-unit revix-sut.service --sut-target sut \
    > "$SIDE/validate.txt" 2>&1
echo "validate rc=$?" | tee -a "$SIDE/validate.txt"
grep -E "^(ERROR|WARNING)|NATIJA|xato:" "$SIDE/validate.txt" | head -40
python3 "$S/smoke_analyze.py" "$RUN" --json "$SIDE/analysis.json" > /dev/null 2> "$SIDE/analysis.stderr"
echo "analysis rc=$?"
ls -la "$RUN"
