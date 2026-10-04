#!/usr/bin/env bash
# v1.12 9.4 regression smoke (merged code + open_parameters), real entry point.
# Stops at the first machinery problem. A P2 runaway trip is the declared
# expectation (v1.12 3-band), not a failure; a sustained_pressure trip is.
set -u
S="$(dirname "$(readlink -f "$0")")"
RUNS="$HOME/revix-runs"
SEQ=(
"smoke-20-A-P0 A P0 20261031"
"smoke-21-noaction-P0 no_action P0 20261032"
"smoke-22-A-P1 A P1 20261033"
"smoke-23-noaction-P1 no_action P1 20261034"
"smoke-24-A-P2 A P2 20261035"
"smoke-25-noaction-P2 no_action P2 20261036"
)
for row in "${SEQ[@]}"; do
  set -- $row
  "$S/smoke_trial_v2.sh" "$1" "$2" "$3" "$4" > "$RUNS/$1.console.txt" 2>&1
  python3 - "$RUNS/$1" <<'PY'
import json, sys
r = sys.argv[1]; s = r + ".pilotready"
problems = []
try:
    a = json.load(open(s + "/analysis.json")); t = a["trials"][0] if a["trials"] else {}
except Exception as exc:
    print(json.dumps({"run": r.split("/")[-1], "problems": ["analysis_failed: %r" % exc]})); sys.exit(1)
pre = json.load(open(s + "/marker-pre.json")); post = json.load(open(s + "/marker-post.json"))
val = open(s + "/validate.txt").read()
lv = t.get("pressure_level")
trips = [g for g in a["guard_records"] if g["record_type"] == "guard_event"]
reasons = sorted({g.get("reason") for g in trips})
if a["n_trial_end"] != 1: problems.append("trial_end!=1")
if "NATIJA: O'TDI" not in val: problems.append("validate_failed")
for k in ("boot_id", "pid1_starttime_ticks"):
    if pre[k] != post[k]: problems.append(k + "_changed")
if abs(post["real_minus_mono_us"] - pre["real_minus_mono_us"]) > 1000: problems.append("clock_offset_changed")
if pre["oom_kill"] != post["oom_kill"]: problems.append("oom_kill_changed")
if "PASS" not in open(s + "/leftover-post.txt").read(): problems.append("leftover_not_pass")
if "sustained_pressure" in reasons: problems.append("SUSTAIN_TRIP")
if trips and lv != "P2": problems.append("guard_trip_outside_P2")
if trips and lv == "P2" and reasons != ["user_full_rate2s_runaway"]: problems.append("unexpected_guard_reason")
if t.get("disposition") == "harness_error": problems.append("harness_error")
if lv == "P2" and trips and t.get("disposition") != "aborted_guard": problems.append("guard_trip_not_aborted_guard")
sp35 = t.get("longest_user_span_ge_0.35_s")
sp05 = max([x["len_s"] for x in t.get("user_rate_spans_ge_0.05", [])], default=0.0)
print(json.dumps({"run": r.split("/")[-1], "disp": t.get("disposition"), "reason": t.get("reason"),
                  "span35": sp35, "span05_max": sp05, "guard": [g["record_type"] for g in a["guard_records"]],
                  "guard_reasons": reasons, "offset_d": post["real_minus_mono_us"] - pre["real_minus_mono_us"],
                  "problems": problems}))
sys.exit(1 if problems else 0)
PY
  if [ $? -ne 0 ]; then echo "STOP after $1"; exit 1; fi
done
echo "SEQUENCE COMPLETE"
