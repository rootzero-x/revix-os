#!/usr/bin/env bash
# V2 smoke sequence (14 §10). Stops at the first criterion/machinery breach.
set -u
S="$(dirname "$(readlink -f "$0")")"
RUNS="$HOME/revix-runs"
SEQ=(
"smoke-08-A-P2 A P2 20261011"
"smoke-09-noaction-P2 no_action P2 20261012"
"smoke-10-A-P2 A P2 20261013"
"smoke-11-noaction-P2 no_action P2 20261014"
"smoke-12-A-P2 A P2 20261015"
"smoke-13-noaction-P2 no_action P2 20261016"
"smoke-14-noaction-P1 no_action P1 20261017"
"smoke-15-A-P1 A P1 20261018"
"smoke-16-A-P0 A P0 20261019"
"smoke-17-noaction-P0 no_action P0 20261020"
)
for row in "${SEQ[@]}"; do
  set -- $row
  "$S/smoke_trial_v2.sh" "$1" "$2" "$3" "$4" > "$RUNS/$1.console.txt" 2>&1
  python3 - "$RUNS/$1" <<'PY'
import json, sys
r = sys.argv[1]; s = r + ".pilotready"
a = json.load(open(s + "/analysis.json")); t = a["trials"][0] if a["trials"] else {}
pre = json.load(open(s + "/marker-pre.json")); post = json.load(open(s + "/marker-post.json"))
val = open(s + "/validate.txt").read()
lv = t.get("pressure_level")
span35 = t.get("longest_user_span_ge_0.35_s")
sp05 = max([x["len_s"] for x in t.get("user_rate_spans_ge_0.05", [])], default=0.0)
trip = [g for g in a["guard_records"] if g["record_type"] == "guard_event"]
problems = []
if a["n_trial_end"] != 1: problems.append("trial_end!=1")
if "NATIJA: O'TDI" not in val: problems.append("validate_failed")
for k in ("boot_id", "pid1_starttime_ticks"):
    if pre[k] != post[k]: problems.append(k + "_changed")
if abs(post["real_minus_mono_us"] - pre["real_minus_mono_us"]) > 1000: problems.append("clock_offset_changed")
if pre["oom_kill"] != post["oom_kill"]: problems.append("oom_kill_changed")
if "PASS" not in open(s + "/leftover-post.txt").read(): problems.append("leftover_not_pass")
if trip: problems.append("guard_trip")
if t.get("disposition") == "aborted_guard": problems.append("aborted_guard")
if lv == "P2" and (span35 is None or span35 > 14.0): problems.append("span35>14")
print(json.dumps({"run": r.split("/")[-1], "disp": t.get("disposition"), "span35": span35, "span05_max": sp05,
                  "guard": [g["record_type"] for g in a["guard_records"]], "offset_d": post["real_minus_mono_us"] - pre["real_minus_mono_us"],
                  "problems": problems}))
sys.exit(1 if problems else 0)
PY
  rc=$?
  if [ $rc -ne 0 ]; then echo "STOP after $1"; exit 1; fi
done
echo "SEQUENCE COMPLETE"
