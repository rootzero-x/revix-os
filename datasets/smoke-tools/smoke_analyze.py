"""Smoke-trial machinery report (agent/pilot-ready). READ-ONLY.

Reports ONLY harness facts: disposition, trial_end count, guard records,
timeline of pressure relative to trial_begin, guard-relevant stall-rate
spans, observed ramp-above-threshold, per-trial overhead. It does NOT compute
VR, FR, downtime or any primary quantity.

Rates replicate revix/guard.py exactly: 2 s window = NEWEST sample at least
2 s older (narrowest >= 2 s window), history kept 3*2 s, rate =
d(total)/d(t) (cgroup.stall_fraction). Applied to psi.csv's `user` scope
(what the guard watches: user@UID.service memory.pressure full) and `lab`.

Usage: python3 smoke_analyze.py <run_dir> [--json out.json]
"""
import csv, json, os, sys

RATE_WINDOW_US = 2_000_000
SUSTAIN_THR = 0.35       # guard.DEFAULTS sustain_rate_threshold
QUIET_THR = 0.05         # §8.4 quiescence / 10 §4 ramp threshold
SUSTAIN_MAX_S = 15.0     # guard.DEFAULTS sustain_max_seconds
RUNAWAY = 0.98           # guard.DEFAULTS user_full_rate2s_max


def load_jsonl(p):
    out = []
    if not os.path.exists(p):
        return out
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def rates(samples):
    """samples: [(t_us, total_us)] -> [(t_us, rate)] like guard.check_psi."""
    hist, out = [], []
    for t, tot in samples:
        hist.append((t, tot))
        cutoff = t - 3 * RATE_WINDOW_US
        hist = [h for h in hist if h[0] >= cutoff]
        old = None
        for h in reversed(hist):
            if t - h[0] >= RATE_WINDOW_US:
                old = h
                break
        if old is not None:
            dt = t - old[0]
            out.append((t, (tot - old[1]) / dt if dt >= RATE_WINDOW_US else None))
    return [(t, r) for t, r in out if r is not None]


def spans(rs, thr, lo, hi):
    """Contiguous runs of rate >= thr inside [lo, hi]; guard-style length
    (t_last - t_first, the value guard compares to sustain_max_seconds)."""
    out, cur = [], None
    for t, r in rs:
        if t < lo or t > hi:
            continue
        if r >= thr:
            if cur is None:
                cur = [t, t, r]
            else:
                cur[1] = t
                cur[2] = max(cur[2], r)
        else:
            if cur is not None:
                out.append(cur)
            cur = None
    if cur is not None:
        out.append(cur)
    return [{"start_us": a, "end_us": b, "len_s": (b - a) / 1e6, "max_rate": m}
            for a, b, m in out]


def main(run_dir, json_out=None):
    ev = load_jsonl(os.path.join(run_dir, "events.jsonl"))
    guard = load_jsonl(os.path.join(run_dir, "guard.jsonl"))
    press = load_jsonl(os.path.join(run_dir, "pressure.jsonl"))
    rows = []
    pcsv = os.path.join(run_dir, "psi.csv")
    if os.path.exists(pcsv):
        with open(pcsv, encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))

    def series(scope):
        s = []
        for r in rows:
            t, v = r.get(f"{scope}__read_mono_us"), r.get(f"{scope}__memory_full_total")
            if t and v:
                s.append((int(t), int(v)))
        return s

    user_r, lab_r, host_r = rates(series("user")), rates(series("lab")), rates(series("host"))
    begins = [r for r in ev if r.get("record_type") == "trial_begin"]
    ends = [r for r in ev if r.get("record_type") == "trial_end"]
    report = {"run_dir": run_dir, "n_trial_begin": len(begins), "n_trial_end": len(ends),
              "guard_records": [{k: g.get(k) for k in ("record_type", "mono_us", "reason",
                                                       "detail", "action", "kill_ok",
                                                       "tripped", "trip_summary",
                                                       "iterations", "elapsed_s")}
                                for g in guard],
              "harness_errors": [{k: r.get(k) for k in ("where", "error", "trial_id", "mono_us")}
                                 for r in ev if r.get("record_type") == "harness_error"],
              "psi_rows": len(rows), "trials": []}
    meta = next((r for r in ev if r.get("record_type") == "run_meta"), {})
    report["per_trial_overhead_preflight"] = meta.get("per_trial_overhead")
    tl = meta.get("timeline") or {}
    for b in begins:
        tid = b.get("trial_id")
        t0 = b["mono_us"]
        e = next((x for x in ends if x.get("trial_id") == tid), None)
        p = (e or {}).get("detail", {}).get("pressure") or {}
        T = {"trial_begin": 0.0}
        ramp_start = t0 + round((tl.get("preflight_s", 5) + tl.get("baseline_s", 10)) * 1e6)
        hold_start = ramp_start + round(tl.get("ramp_s", 5) * 1e6)
        p_off = hold_start + round(tl.get("hold_s", 13) * 1e6)
        horizon = (e or {}).get("mono_us")
        # generator records inside this trial (by mono window, generator has no trial_id)
        hi = (e or {}).get("mono_us_record_written") or (horizon or t0) + 200_000_000
        gp = [r for r in press if t0 - 5_000_000 <= r["mono_us"] <= hi]
        g_start = next((r["mono_us"] for r in gp if r["record_type"] == "pressure_start"), None)
        g_ramps = [r["mono_us"] for r in gp if r["record_type"] == "pressure_ramp"]
        g_pi = [r for r in gp if r["record_type"] == "pressure_sample" and r.get("mode") == "pi"]
        g_stop = next((r for r in gp if r["record_type"] == "pressure_stop"), None)
        rel = lambda x: None if x is None else round((x - t0) / 1e6, 3)
        T.update({"planned_ramp_start": rel(ramp_start), "planned_hold_start": rel(hold_start),
                  "planned_pressure_off": rel(p_off), "horizon(trial_end.mono_us)": rel(horizon),
                  "generator_pressure_start": rel(g_start),
                  "generator_last_ramp_record": rel(g_ramps[-1] if g_ramps else None),
                  "generator_first_pi_sample": rel(g_pi[0]["mono_us"] if g_pi else None),
                  "generator_pressure_stop": rel(g_stop["mono_us"] if g_stop else None)})
        fi = next((r for r in ev if r.get("record_type") == "fault_inject" and r.get("trial_id") == tid), None)
        T["fault_inject"] = rel(fi["mono_us"]) if fi else None
        acts = [r for r in ev if r.get("record_type") == "action" and r.get("trial_id") == tid]
        sigs = [r for r in ev if r.get("record_type") == "actor_signal" and r.get("trial_id") == tid]
        T["action_t_issue"] = [rel(a["mono_us"]) for a in acts]
        T["actor_signal_active"] = [rel(s["mono_us"]) for s in sigs]
        lo_w, hi_w = t0, (horizon or p_off) + 30_000_000
        us = spans(user_r, SUSTAIN_THR, lo_w, hi_w)
        us05 = spans(user_r, QUIET_THR, lo_w, hi_w)
        ls = spans(lab_r, SUSTAIN_THR, lo_w, hi_w)
        ls05 = spans(lab_r, QUIET_THR, lo_w, hi_w)
        relspan = lambda sp: [{"from_s": rel(s["start_us"]), "to_s": rel(s["end_us"]),
                               "len_s": round(s["len_s"], 3), "max_rate": round(s["max_rate"], 4)}
                              for s in sp]
        u_in = [r for t, r in user_r if lo_w <= t <= hi_w]
        # observed ramp-above-threshold: 10 §4 method (generator's own ramp window)
        # and the timeline reading (planned 5 s ramp window), lab 2 s rate > 0.05
        def above(rs, a, b, thr=QUIET_THR):
            pts = [(t, r) for t, r in rs if a <= t <= b]
            if len(pts) < 2:
                return None
            tot = 0
            for (t1, r1), (t2, _r2) in zip(pts, pts[1:]):
                if r1 > thr:
                    tot += t2 - t1
            return round(tot / 1e6, 3)
        ramp_gen = above(lab_r, g_start, g_ramps[-1]) if (g_start and g_ramps) else None
        ramp_plan = above(lab_r, ramp_start, hold_start)
        ramp_plan_user = above(user_r, ramp_start, hold_start)
        tr = {
            "trial_id": tid, "arm": b.get("arm"), "pressure_level": b.get("pressure_level"),
            "disposition": (e or {}).get("disposition"), "reason": (e or {}).get("reason"),
            "matched_rules": (e or {}).get("matched_rules"),
            "facts": (e or {}).get("facts"), "anomalies": (e or {}).get("anomalies"),
            "overhead_s": (e or {}).get("overhead_s"), "timing": (e or {}).get("timing"),
            "washout": (e or {}).get("washout"),
            "pressure_detail": {k: p.get(k) for k in ("started", "level", "target_rate",
                                                      "base_mb", "step_mb", "max_seconds",
                                                      "units_show_valid", "reason")},
            "timeline_rel_s": T,
            "user_rate_spans_ge_0.35": relspan(us),
            "user_rate_spans_ge_0.05": relspan(us05),
            "lab_rate_spans_ge_0.35": relspan(ls),
            "lab_rate_spans_ge_0.05": relspan(ls05),
            "user_rate_max": round(max(u_in), 4) if u_in else None,
            "user_rate_n_ge_runaway_0.98": sum(1 for r in u_in if r >= RUNAWAY),
            "longest_user_span_ge_0.35_s": max((s["len_s"] for s in us), default=0.0),
            "guard_sustain_limit_s": SUSTAIN_MAX_S,
            "ramp_above_threshold_s_generator_ramp_window(10§4)": ramp_gen,
            "ramp_above_threshold_s_planned_ramp_window_lab": ramp_plan,
            "ramp_above_threshold_s_planned_ramp_window_user": ramp_plan_user,
            "generator_stop": {k: (g_stop or {}).get(k) for k in ("elapsed_s", "max_seconds", "overrun_s", "touched_mb_at_stop")},
            "generator_pi_samples": len(g_pi),
            "generator_pi_rate_median": (sorted(x["slice_full_rate2s"] for x in g_pi if x.get("slice_full_rate2s") is not None)[len(g_pi)//2] if g_pi else None),
        }
        report["trials"].append(tr)
    txt = json.dumps(report, indent=1, ensure_ascii=False, default=str)
    if json_out:
        with open(json_out, "w", encoding="utf-8") as fh:
            fh.write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    a = sys.argv[1:]
    out = None
    if "--json" in a:
        i = a.index("--json"); out = a[i + 1]; del a[i:i + 2]
    main(a[0], out)
