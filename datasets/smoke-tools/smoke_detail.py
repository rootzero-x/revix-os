"""Timeline detail for smoke trials + the same quantities in calibration
episodes (open-params cal-01/02, part A, 13 s generator). READ-ONLY.
No VR/FR/downtime. Rates = guard algorithm (see smoke_analyze.py)."""
import csv, glob, io, json, os, statistics, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smoke_analyze import rates, spans, load_jsonl

def psi_rows(path):
    if path.endswith(".zst"):
        txt = subprocess.run(["zstd", "-dc", path], capture_output=True, check=True).stdout.decode()
        return list(csv.DictReader(io.StringIO(txt)))
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

def series(rows, scope, col="memory_full_total"):
    out = []
    for r in rows:
        t, v = r.get(f"{scope}__read_mono_us"), r.get(f"{scope}__{col}")
        if t and v:
            out.append((int(t), int(v)))
    return out

def window_facts(rows, user_r, lab_r, g0, g1, press, t_ref):
    """g0 = generator start, g1 = generator gone/stop (mono_us)."""
    rel = lambda x: None if x is None else round((x - t_ref) / 1e6, 3)
    us = [s for s in spans(user_r, 0.35, g0, g1 + 6_000_000)]
    longest = max(us, key=lambda s: s["len_s"]) if us else None
    first05 = next((t for t, r in user_r if g0 <= t <= g1 + 3e6 and r >= 0.05), None)
    first35 = next((t for t, r in user_r if g0 <= t <= g1 + 3e6 and r >= 0.35), None)
    last35 = max((t for t, r in user_r if g0 <= t <= g1 + 6e6 and r >= 0.35), default=None)
    inside = [r for t, r in user_r if longest and longest["start_us"] <= t <= longest["end_us"]]
    memc = [v for t, v in series(rows, "lab", "memory_current") if g0 + 3e6 <= t <= g1]
    swap = [v for t, v in series(rows, "lab", "memory_swap_current")]
    gp = [r for r in press if g0 - 1e6 <= r["mono_us"] <= g1 + 1e6]
    ramp = [r["mono_us"] for r in gp if r["record_type"] == "pressure_ramp"]
    samp = [r["mono_us"] for r in gp if r["record_type"] == "pressure_sample"]
    ts = sorted(r["mono_us"] for r in gp)
    after_ramp = [t for t in ts if ramp and t >= ramp[-1]]
    gaps = [(b - a) / 1e6 for a, b in zip(after_ramp, after_ramp[1:])]
    pi_rates = [r.get("slice_full_rate2s") for r in gp if r["record_type"] == "pressure_sample" and r.get("slice_full_rate2s") is not None]
    return {
        "gen_start": rel(g0), "gen_end": rel(g1), "gen_life_s": round((g1 - g0) / 1e6, 3),
        "first_user_ge_0.05_after_gen_start_s": None if first05 is None else round((first05 - g0) / 1e6, 3),
        "first_user_ge_0.35_after_gen_start_s": None if first35 is None else round((first35 - g0) / 1e6, 3),
        "last_user_ge_0.35_after_gen_end_s": None if last35 is None else round((last35 - g1) / 1e6, 3),
        "longest_user_span_ge_0.35_s": round(longest["len_s"], 3) if longest else 0.0,
        "longest_span_from": rel(longest["start_us"]) if longest else None,
        "longest_span_to": rel(longest["end_us"]) if longest else None,
        "min_user_rate_inside_longest_span": round(min(inside), 4) if inside else None,
        "lab_memory_current_MiB_median_pi": round(statistics.median(memc) / 2**20, 1) if memc else None,
        "lab_memory_current_MiB_max_pi": round(max(memc) / 2**20, 1) if memc else None,
        "lab_swap_current_max_run": max(swap) if swap else None,
        "gen_ramp_records": len(ramp), "gen_pi_samples": len(samp),
        "gen_ramp_end_after_start_s": round((ramp[-1] - g0) / 1e6, 3) if ramp else None,
        "gen_max_record_gap_after_ramp_s": round(max(gaps), 3) if gaps else None,
        "gen_pi_rate2s_median": round(statistics.median(pi_rates), 4) if pi_rates else None,
    }

def smoke(run_dir):
    ev = load_jsonl(os.path.join(run_dir, "events.jsonl"))
    press = load_jsonl(os.path.join(run_dir, "pressure.jsonl"))
    guard = load_jsonl(os.path.join(run_dir, "guard.jsonl"))
    rows = psi_rows(os.path.join(run_dir, "psi.csv"))
    user_r, lab_r = rates(series(rows, "user")), rates(series(rows, "lab"))
    b = next(r for r in ev if r["record_type"] == "trial_begin")
    t0 = b["mono_us"]
    g0 = next(r["mono_us"] for r in press if r["record_type"] == "pressure_start")
    g1 = next(r["mono_us"] for r in press if r["record_type"] == "pressure_stop")
    out = {"run": os.path.basename(run_dir.rstrip("/")), "arm": b.get("arm"), "level": b.get("pressure_level")}
    out.update(window_facts(rows, user_r, lab_r, g0, g1, press, t0))
    trip = next((g for g in guard if g["record_type"] == "guard_event"), None)
    out["guard_trip_rel_s"] = round((trip["mono_us"] - t0) / 1e6, 3) if trip else None
    out["guard_trip_detail"] = trip.get("detail") if trip else None
    fi = next((r for r in ev if r["record_type"] == "fault_inject"), None)
    out["fault_inject_rel_s"] = round((fi["mono_us"] - t0) / 1e6, 3) if fi else None
    out["fault_bracket_us"] = fi.get("bracket_us") if fi else None
    us = [r for r in ev if r["record_type"] == "unit_state" and r.get("trial_id") and r.get("unit") == "revix-sut.service"]
    out["sut_states"] = [(round((r["mono_us"] - t0) / 1e6, 3), r.get("active_state"), r.get("result"), r.get("n_restarts")) for r in us]
    by = [r for r in ev if r["record_type"] == "unit_state" and r.get("trial_id") and r.get("unit") == "revix-bystander.service"]
    out["bystander_states"] = [(round((r["mono_us"] - t0) / 1e6, 3), r.get("active_state"), r.get("result")) for r in by]
    te = next(r for r in ev if r["record_type"] == "trial_end")
    out["trial_end_disposition"] = te["disposition"]
    out["planned_pressure_off_rel_s"] = round((te["timing"]["pressure_off_mono_us"] - t0) / 1e6, 3)
    return out

def calib(run_dir, band="P2", part="A"):
    ev = load_jsonl(os.path.join(run_dir, "events.jsonl")) if os.path.exists(os.path.join(run_dir, "events.jsonl")) else []
    press = load_jsonl(os.path.join(run_dir, "pressure.jsonl"))
    rows = psi_rows(os.path.join(run_dir, "psi.csv"))
    user_r, lab_r = rates(series(rows, "user")), rates(series(rows, "lab"))
    eps = {}
    for r in ev:
        k = r.get("episode")
        if not k or r.get("part") != part or r.get("band") != band:
            continue
        eps.setdefault(k, {})[r["record_type"]] = r
    out = []
    for k, d in sorted(eps.items()):
        if "generator_started" not in d or "generator_gone" not in d or "episode_end" not in d:
            continue
        g0 = d["generator_started"]["mono_us"]
        g1 = d["generator_gone"].get("gen_gone_mono_us") or d["generator_gone"]["mono_us"]
        f = window_facts(rows, user_r, lab_r, g0, g1, press, g0)
        f["episode"] = os.path.basename(run_dir.rstrip("/")) + ":" + k
        out.append(f)
    return out

if __name__ == "__main__":
    res = {"smoke": [smoke(d) for d in sys.argv[1:] if "smoke-" in d],
           "calibration": []}
    for d in sys.argv[1:]:
        if "open-params-cal" in d:
            for band in ("P1", "P2"):
                for e in calib(d, band):
                    e["band"] = band
                    res["calibration"].append(e)
    print(json.dumps(res, indent=1, default=str))
