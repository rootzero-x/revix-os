#!/usr/bin/env bash
# 14 §12.1: two-trial run; SUT killed from OUTSIDE ~22 s into trial 1.
set -u
NAME=smoke-19-noaction-P0-x2; SEED=20261022
WORK="$HOME/pilotready-work"; RUNS="$HOME/revix-runs"; RUN="$RUNS/$NAME"; SIDE="$RUNS/$NAME.pilotready"
S="$HOME/pilotready-scratch"
grep -q '^pilot-ready ' "$HOME/.revix-exclusive/holder" 2>/dev/null || { echo "LOCK NOT HELD"; exit 9; }
[ -e "$RUN" ] && { echo "exists"; exit 9; }
mkdir -p "$SIDE"
source <(sed -n '/^marker() {/,/^}/p; /^leftover() {/,/^}/p' "$S/smoke_trial_v2.sh")
pgrep -a 'VBoxHeadless|mmdebstrap|mksquashfs' && { echo HEAVY; exit 9; }
marker pre | tee "$SIDE/marker-pre.json"; leftover | tee "$SIDE/leftover-pre.txt"
# external killer
python3 - "$RUN/events.jsonl" > "$SIDE/external-kill.json" 2>&1 <<'PY' &
import json, os, subprocess, sys, time
p = sys.argv[1]
t_end = time.monotonic() + 120
mono0 = None
while time.monotonic() < t_end and mono0 is None:
    if os.path.exists(p):
        for line in open(p):
            if '"trial_begin"' in line:
                r = json.loads(line)
                if r.get("record_type") == "trial_begin":
                    mono0 = r["mono_us"]; tid = r.get("trial_id"); break
    time.sleep(0.05)
if mono0 is None:
    print(json.dumps({"error": "no trial_begin"})); sys.exit(1)
target = mono0 + 22_000_000
while time.clock_gettime_ns(time.CLOCK_MONOTONIC) // 1000 < target:
    time.sleep(0.005)
t_kill = time.clock_gettime_ns(time.CLOCK_MONOTONIC) // 1000
rc = subprocess.run(["systemctl", "--user", "kill", "--signal=SIGKILL", "revix-sut.service"]).returncode
print(json.dumps({"trial_id": tid, "trial_begin_mono_us": mono0, "kill_mono_us": t_kill,
                  "kill_rel_s": (t_kill - mono0) / 1e6, "systemctl_rc": rc,
                  "note": "external SIGKILL, simulates smoke-13 path, NOT a guard trip"}))
PY
KPID=$!
cd "$WORK"; git rev-parse HEAD > "$SIDE/git_commit.txt"; git status --porcelain > "$SIDE/git_status.txt"
python3 -m revix.cli run --run-dir "$RUN" --seed "$SEED" --blocks 2 --only no_action,P0 --allow-pressure --json > "$SIDE/driver.json" 2> "$SIDE/driver.stderr"
echo "driver rc=$?" | tee "$SIDE/driver.rc"
wait $KPID; cat "$SIDE/external-kill.json"
marker post | tee "$SIDE/marker-post.json"; leftover | tee "$SIDE/leftover-post.txt"
systemctl --user list-units 'revix*' --all --no-legend | tee "$SIDE/units-post.txt"
python3 -m revix.validate --run-dir "$RUN" --sut-unit revix-sut.service --sut-target sut > "$SIDE/validate.txt" 2>&1; echo "validate rc=$?" >> "$SIDE/validate.txt"
tail -6 "$SIDE/validate.txt"
python3 "$S/smoke_analyze.py" "$RUN" --json "$SIDE/analysis.json" > /dev/null 2> "$SIDE/analysis.stderr"; echo "analysis rc=$?"
