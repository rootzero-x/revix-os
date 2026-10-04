"""p1-pilot-001: VALIDITY classification only (read-only). For every trial:
probe gap > 2P (validate.check_probe_gaps logic) and §17 window containment
(validate._trial_window). No VR/FR/downtime/rates. Writes nothing into the
run dir."""
import collections, json, sys
sys.path.insert(0, sys.argv[2])
from revix import validate as V, reduce as R
run_dir = sys.argv[1]
run, load_f = V.load_run_dir(run_dir)
rv = V.reducer_view(run, "revix-sut.service", "sut")
prm = R.Params(probe_period_us=R.P_US, w_stab_us=V._run_w_stab_us(rv))
lim = 2 * R.P_US
rows = []
for t in R.split_trials(rv):
    gaps = [(a.mono_us, b.mono_us, b.mono_us - a.mono_us)
            for a, b in zip(t.probes, t.probes[1:]) if b.mono_us - a.mono_us > lim]
    w = V._trial_window(t, prm)
    b = t.begin or {}
    t0 = R._as_int(b.get("mono_us"))
    rows.append({
        "trial_id": t.trial_id, "arm": b.get("arm"), "band": b.get("pressure_band"),
        "disp": t.disposition_raw,
        "gaps": [{"from_rel_s": round((a - t0) / 1e6, 3), "to_rel_s": round((c - t0) / 1e6, 3),
                  "gap_us": g} for a, c, g in gaps],
        "window": w.status,
        "slack_to_hold_us": w.slack_to_hold_us,
        "t_up_rel_s": None if w.t_up_us is None else round((w.t_up_us - t0) / 1e6, 3),
        "T_h_rel_s": None if w.hold_end_us is None else round((w.hold_end_us - t0) / 1e6, 3),
    })
out = {"by_trial": rows}
cells = collections.defaultdict(lambda: collections.Counter())
for r in rows:
    c = cells[f'{r["arm"]}/{r["band"]}']
    c["trials"] += 1
    viol_win = r["window"] in (R.WINDOW_PAST_PRESSURE, R.WINDOW_PAST_HORIZON)
    viol_gap = bool(r["gaps"])
    if viol_gap: c["probe_gap_any_disp"] += 1
    if viol_win: c["window_outside_any_disp"] += 1
    if r["disp"] == "complete" and viol_gap: c["COMPLETE_with_probe_gap"] += 1
    if r["disp"] == "complete" and viol_win: c["COMPLETE_with_window_outside"] += 1
    if r["window"] == R.WINDOW_NOT_EVALUATED and r["disp"] == "complete": c["COMPLETE_window_not_evaluated"] += 1
out["by_cell"] = {k: dict(v) for k, v in sorted(cells.items())}
out["window_statuses"] = sorted({r["window"] for r in rows})
print(json.dumps(out, indent=1))
