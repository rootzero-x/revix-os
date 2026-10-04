"""Offline, read-only replay of the three fixes over p1-pilot-001.
Reports only disposition changes per cell and action-timestamp changes.
No VR/FR/downtime/rates."""
import collections, json, sys
sys.path.insert(0, sys.argv[2])
from revix import validate as V, reduce as R, schedule as S
from revix import driver as D
run_dir = sys.argv[1]
run, _ = V.load_run_dir(run_dir)
rv = V.reducer_view(run, D.SUT_UNIT, "sut")
prm = R.Params(probe_period_us=R.P_US, w_stab_us=V._run_w_stab_us(rv))
outside = set(R.WINDOW_CONTAINMENT_SOURCE)
changes = collections.Counter()
per_cell = collections.defaultdict(collections.Counter)
named = {}
viol_after = []
for t in R.split_trials(rv):
    b = t.begin or {}; e = t.end or {}
    cell = f'{b.get("arm")}/{b.get("pressure_band")}'
    rec_f = dict(e.get("facts") or {})
    # YAKUNIY driver kodi: D.measured_trial_facts, faqat shu trial record'lari.
    tid = t.trial_id
    m = D.measured_trial_facts(
        [r for r in run.records if r.get("trial_id") == tid
         or r.get("record_type") in ("guard_event", "guard_start", "guard_stop")],
        [p for p in run.probes if p.get("trial_id") == tid], tid,
        pressure_off_mono_us=t.hold_end_us, horizon_end_mono_us=t.horizon_end_us,
        probe_period_us=R.P_US, w_stab_us=prm.w_stab_us)
    gaps = m["probe_gaps"]
    class _W: pass
    w = _W(); w.status = m["window_containment"]
    new_f = dict(rec_f)
    new_f["probe_gap_exceeded"] = bool(rec_f.get("probe_gap_exceeded")) or bool(gaps)
    new_f["window_outside_hold"] = w.status in outside
    v_old = S.explain_disposition(S.TrialFacts(**{k: rec_f.get(k, False) for k in S.FACT_FIELDS if k != "window_outside_hold"})) if "window_outside_hold" in S.FACT_FIELDS else None
    v_new = S.explain_disposition(S.TrialFacts(**{k: new_f.get(k, False) for k in S.FACT_FIELDS}))
    rec_disp = e.get("disposition")
    per_cell[cell]["trials"] += 1
    if v_new.disposition != rec_disp:
        per_cell[cell][f"{rec_disp}->{v_new.disposition}"] += 1
    if t.trial_id in ("b007t001", "b013t004", "b010t001"):
        named[t.trial_id] = {"recorded": rec_disp, "replayed": v_new.disposition, "rule": v_new.rule,
                             "matched": list(v_new.matched_rules), "gap": bool(gaps), "window": w.status}
    # would validator's two checks pass with the replayed disposition?
    if gaps and v_new.disposition != "censored": viol_after.append((t.trial_id, "probe_gap_not_censored"))
    if v_new.disposition == "complete" and w.status in outside: viol_after.append((t.trial_id, "window_complete"))
# action replay (t_issue)
act_diff = []; act_old_mismatch = []
for t in R.split_trials(run):
    b = t.begin or {}
    if b.get("arm") != "A": continue
    acts = sorted(t.actions, key=lambda a: a.raw.get("restart_index") or 0)
    inv = None; last_old = None; last_new = None; k = 0
    for u in sorted([r for r in t.unit_states if r.get("unit") == D.SUT_UNIT], key=lambda r: r.get("__index__") or 0):
        if u.get("active_state") not in (None, "active"):
            last_old = u.get("active_exit_ts_mono_us") or u.get("exec_main_exit_ts_mono_us") or u.get("recv_mono_us")
            c = D.exit_ts_candidate(u)
            last_new = (c if last_new is None or c is None else max(last_new, c)) or last_new
        v = u.get("invocation_id")
        if v and inv and v != inv:
            ev_old = last_old or u.get("active_exit_ts_mono_us") or u.get("exec_main_exit_ts_mono_us")
            ev_new = last_new or u.get("active_exit_ts_mono_us") or u.get("exec_main_exit_ts_mono_us")
            rec = acts[k].raw.get("t_issue_mono_us") if k < len(acts) else None
            if rec != ev_old: act_old_mismatch.append((t.trial_id, k + 1, rec, ev_old))
            if ev_new != ev_old: act_diff.append((t.trial_id, k + 1, ev_old, ev_new))
            k += 1
        if v: inv = v
print(json.dumps({"named": named, "changed_by_cell": {c: {k: v for k, v in cnt.items() if "->" in k} for c, cnt in sorted(per_cell.items())},
                  "n_trials": sum(c["trials"] for c in per_cell.values()),
                  "validator_two_checks_violations_after_replay": viol_after,
                  "action_t_issue_changes": [(a, b, round((c-0)/1, 0), d) for a, b, c, d in act_diff],
                  "old_logic_vs_recorded_mismatches": act_old_mismatch}, indent=1, default=str))
