#!/usr/bin/env python3
"""open-params kalibratsiyasi -- tahlil va 13 §0 qoidasining qo'llanishi.

Kirish: run katalogi (`open-params-measure.py` chiqishi; `.zst` fayllar
ham o'qiladi). Chiqish: inson uchun jadval (stdout) va `summary.json`.

Bu skript HECH QANDAY tizim holatiga tegmaydi -- faqat fayl o'qiydi.
Qoida (F, U, grid, taklif formulasi) 13-hujjatning §0 bo'limidan AYNAN
ko'chirilgan; u o'lchovdan oldin commit qilingan (812c989).
"""
from __future__ import annotations

import csv
import io
import json
import math
import os
import subprocess
import sys
from collections import Counter, defaultdict
from typing import Any

# --- 13 §0 qoidasi (o'zgartirilmaydi) ----------------------------------------
F = 3.0
W0_S = 5.0                      # o'lchov paytidagi WatchdogSec
NOMINAL_PERIOD_S = W0_S / 2     # sut.c: WATCHDOG_USEC/2
DEFAULT_TIMEOUT_START_S = 10
DEFAULT_WATCHDOG_S = 5
T_TRIAL_S = 41.1
T_INJECT_S = 23.0
RESTART_SEC_S = 0.1
W_STAB_S = 8.0
P_S = 0.1
T_PRESSURE_OFF_S = 33.0
U_START_S = round(T_TRIAL_S - (T_INJECT_S + RESTART_SEC_S), 6)   # 18.0
POLL_INTERVAL_LIMIT_S = 1.0     # §0.5(2)
MIN_A_EPISODES = 24             # §0.5(3)
MIN_B_STARTS = 48
D_PROBE_MAX_DOC10_S = 2.2       # 10 §7.2 (P2 max) -- o'lchanmagan, keltirilgan
QUIESCENCE_RATE = 0.05


def pct(xs: list[float], q: float) -> float | None:
    """10 §6 ning tstart.py dagi pct() bilan bir xil (chiziqli interpolyatsiya)."""
    if not xs:
        return None
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    i = q * (len(s) - 1)
    lo = int(i)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def open_text(path: str) -> io.TextIOBase:
    if os.path.exists(path):
        return open(path, encoding="utf-8")
    if os.path.exists(path + ".zst"):
        data = subprocess.run(["zstd", "-dc", path + ".zst"], check=True,
                              capture_output=True).stdout
        return io.StringIO(data.decode("utf-8"))
    raise FileNotFoundError(path)


def read_jsonl(path: str) -> list[dict[str, Any]]:
    try:
        with open_text(path) as fh:
            return [json.loads(l) for l in fh if l.strip()]
    except FileNotFoundError:
        return []


def fnum(v: str) -> int | None:
    return int(v) if v not in ("", None) else None


def stats(xs: list[float]) -> dict[str, Any]:
    return {"n": len(xs), "min": min(xs) if xs else None,
            "p50": pct(xs, 0.5), "p90": pct(xs, 0.9), "p99": pct(xs, 0.99),
            "max": max(xs) if xs else None}


def rates_2s(samples: list[tuple[int, int]]) -> list[tuple[int, float]]:
    """(t_us, total_us) -> (t_us, eng tor >=2 s oynadagi stall ulushi)."""
    out = []
    j = 0
    for i, (t, tot) in enumerate(samples):
        # j ni eng kech (t - t_j >= 2 s) ga suramiz
        while j + 1 < i and t - samples[j + 1][0] >= 2_000_000:
            j += 1
        if i > 0 and t - samples[j][0] >= 2_000_000:
            out.append((t, (tot - samples[j][1]) / (t - samples[j][0])))
    return out


def main(run_dir: str) -> dict[str, Any]:
    ev = read_jsonl(os.path.join(run_dir, "events.jsonl"))
    ts_rows = read_jsonl(os.path.join(run_dir, "tstart.jsonl"))
    press = read_jsonl(os.path.join(run_dir, "pressure.jsonl"))
    ustate = read_jsonl(os.path.join(run_dir, "unitstate.jsonl"))
    guard = read_jsonl(os.path.join(run_dir, "guard.jsonl"))

    poll: dict[str, list[dict[str, Any]]] = defaultdict(list)
    poll_t0: list[int] = []
    with open_text(os.path.join(run_dir, "wdpoll.csv")) as fh:
        for r in csv.DictReader(fh):
            t0 = int(r["t0_us"])
            poll_t0.append(t0)
            if r["episode"]:
                poll[r["episode"]].append(r)

    by_ep: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for e in ev:
        if "episode" in e:
            by_ep[e["episode"]][e["record_type"]] = e
    ctrl_start = next((e for e in ev if e["record_type"] == "controller_start"), {})
    ctrl_end = next((e for e in ev if e["record_type"] == "controller_end"), {})
    aborts = [e for e in ev if e["record_type"] in ("abort", "error", "guest_changed",
                                                     "guard_problem", "postflight_failed")]

    # pressure.jsonl: session_id = episode id
    pr_by_ep: dict[str, dict[str, Any]] = defaultdict(lambda: {"ramp": []})
    for r in press:
        sid = r.get("session_id")
        rt = r.get("record_type")
        if rt == "pressure_start":
            pr_by_ep[sid]["start"] = r
        elif rt == "pressure_ramp":
            pr_by_ep[sid]["ramp"].append(r)
        elif rt == "pressure_stop":
            pr_by_ep[sid]["stop"] = r

    out: dict[str, Any] = {"run_dir": run_dir, "rule_commit": "812c989",
                           "controller_status": ctrl_end.get("status"),
                           "aborts": aborts}

    # --- poller rezolyutsiyasi (§0.5(2)) --------------------------------------
    poll_t0.sort()
    a_eps = sorted(k for k in by_ep if k.startswith("A-"))
    max_int_a = 0
    for eid in a_eps:
        rows = [r for r in poll.get(eid, []) if r["loaded"] == "1"]
        ts = [int(r["t0_us"]) for r in rows]
        for a, b in zip(ts, ts[1:]):
            max_int_a = max(max_int_a, b - a)
    out["poll"] = {"samples": len(poll_t0),
                   "max_interval_all_s": ctrl_end.get("poll_max_interval_us", 0) / 1e6
                   if ctrl_end else None,
                   "max_interval_A_unit_polls_s": max_int_a / 1e6,
                   "errors": ctrl_end.get("poll_errors")}

    # --- A: watchdog ------------------------------------------------------------
    wd_events = []
    A: dict[str, dict[str, Any]] = {}
    gaps_all: dict[str, list[dict[str, Any]]] = defaultdict(list)
    g2 = []
    doses: dict[str, list[dict[str, Any]]] = defaultdict(list)
    post_stall_end: dict[str, list[float]] = defaultdict(list)
    tstart_A: dict[str, list[float]] = defaultdict(list)
    for eid in a_eps:
        e = by_ep[eid]
        band = e["episode_begin"]["band"]
        valid = "episode_end" in e and e["episode_end"].get("postflight", {}).get("ok")
        sut = e.get("sut_started", {})
        if sut.get("t_start_s") is not None:
            tstart_A[band].append(sut["t_start_s"])
        rows = sorted(poll.get(eid, []), key=lambda r: int(r["t0_us"]))
        unit_rows = [r for r in rows if r["loaded"] == "1"]
        for r in rows:
            if r["result"] == "watchdog":
                wd_events.append({"episode": eid, "t0_us": r["t0_us"]})
        for u in ustate:
            if u.get("episode") == eid and u.get("Result") == "watchdog":
                wd_events.append({"episode": eid, "unitstate": True,
                                  "recv_mono_us": u.get("recv_mono_us")})
        # ping qiymatlari
        vals: list[int] = []
        init = sut.get("watchdog_ts_initial_us")
        if init:
            vals.append(int(init))
        for r in unit_rows:
            v = fnum(r["wd_ts_us"])
            if v and (not vals or v != vals[-1]):
                if vals and v < vals[-1]:
                    continue        # monotonlik buzilishi -- yozilmaydi (bo'lmasligi kerak)
                vals.append(v)
        st = sut.get("state") or {}
        ae = st.get("ActiveEnterTimestampMonotonic")
        if init and ae:
            g2.append((int(init) - int(ae)) / 1e6)
        pr = pr_by_ep.get(eid, {})
        gs = (pr.get("start") or {}).get("mono_us") or e.get("generator_started", {}).get("mono_us_call")
        ge = (pr.get("stop") or {}).get("mono_us") or e.get("generator_gone", {}).get("gen_gone_mono_us")
        ramp_end = (pr["ramp"][-1]["mono_us"] if pr.get("ramp") else gs)
        # lab total= bo'yicha har oraliq uchun pressured belgisi
        lt = [(int(r["t0_us"]), int(r["lab_full_total"])) for r in rows if r["lab_full_total"]]

        def total_at(t: int) -> int | None:
            best = None
            for tt, tot in lt:
                if tt <= t:
                    best = tot
                else:
                    break
            return best
        eg = []
        for i in range(1, len(vals)):
            a, b = vals[i - 1], vals[i]
            g = (b - a) / 1e6
            if gs and ge:
                phase = "pre" if b <= gs else ("post" if a >= ge else "during")
            else:
                phase = "unknown"
            ta, tb = total_at(a), total_at(b)
            pressured = (ta is not None and tb is not None and tb > ta)
            rec = {"episode": eid, "band": band, "i": i, "gap_s": g,
                   "delta_s": g - NOMINAL_PERIOD_S,
                   "kind": "arm_to_first" if i == 1 and init else "ping",
                   "phase": phase, "pressured": pressured, "valid_episode": bool(valid)}
            eg.append(rec)
            gaps_all[band].append(rec)
        # erishilgan doza (PI fazasi): 2 s tezliklarning medianasi
        dose = None
        if gs and ge:
            rr = [x for t, x in rates_2s(lt) if ramp_end <= t <= ge]
            dose = pct(rr, 0.5) if rr else None
            # pressure'dan keyin oxirgi stall o'sishi
            after = [(t, tot) for t, tot in lt if t >= ge]
            last_inc = None
            for (t1, x1), (t2, x2) in zip(after, after[1:]):
                if x2 > x1:
                    last_inc = t2
            post_stall_end[band].append(((last_inc - ge) / 1e6) if last_inc else 0.0)
        ev_b = e["episode_begin"].get("lab_events", {})
        ev_g = e.get("generator_gone", {}).get("lab_events", {})
        tot_b = e.get("generator_started", {}).get("lab_full_total_before")
        tot_g = e.get("generator_gone", {}).get("lab_full_total_after")
        doses[band].append({"episode": eid, "part": "A", "dose_p50": dose,
                            "high_delta": (ev_g.get("high", 0) - ev_b.get("high", 0))
                            if ev_g and ev_b else None,
                            "lab_full_total_delta_us": (tot_g - tot_b)
                            if (tot_g is not None and tot_b is not None) else None,
                            "overrun_s": (pr.get("stop") or {}).get("overrun_s"),
                            "pressure_stop": "stop" in pr})
        A[eid] = {"band": band, "valid": bool(valid), "pings": len(vals) - 1 if vals else 0,
                  "max_gap_s": max((x["gap_s"] for x in eg), default=None),
                  "final_result": ((e.get("episode_end") or {}).get("final_state") or {}).get("Result"),
                  "quiescence": e.get("quiescence", {}).get("state"),
                  "quiescence_elapsed_s": e.get("quiescence", {}).get("elapsed_s")}

    a_band: dict[str, Any] = {}
    for band in ("P0", "P1", "P2"):
        eps = [k for k, v in A.items() if v["band"] == band]
        valid_eps = [k for k in eps if A[k]["valid"]]
        g = [x for x in gaps_all[band] if x["valid_episode"]]
        pings = [x["gap_s"] for x in g if x["kind"] == "ping"]
        during = [x["gap_s"] for x in g if x["kind"] == "ping" and x["phase"] == "during"]
        post = [x["delta_s"] for x in g if x["kind"] == "ping" and x["phase"] == "post"]
        dl = [x["delta_s"] for x in g]
        mg = max((x["gap_s"] for x in g), default=None)
        md = max(dl, default=None)
        a_band[band] = {
            "episodes": len(eps), "valid_episodes": len(valid_eps),
            "gaps_total": len(g), "ping_gaps": stats(pings),
            "ping_gaps_during_pressure": stats(during),
            "pressured_gaps": sum(1 for x in g if x["pressured"]),
            "arm_to_first": stats([x["gap_s"] for x in g if x["kind"] == "arm_to_first"]),
            "max_gap_s": mg, "max_delta_s": md,
            "post_pressure_max_delta_s": max(post, default=None),
            "W_over_max_gap": (W0_S / mg) if mg else None,
            "halfW_over_max_delta": ((W0_S / 2) / md) if md and md > 0 else None,
            "final_results": dict(Counter(A[k]["final_result"] for k in eps)),
            "quiescence_states": dict(Counter(A[k]["quiescence"] for k in eps)),
            "quiescence_elapsed_s": stats([A[k]["quiescence_elapsed_s"] for k in eps
                                           if A[k]["quiescence_elapsed_s"] is not None]),
            "post_pressure_last_stall_increment_s": stats(post_stall_end[band]),
        }
    out["A"] = {"bands": a_band, "watchdog_results": wd_events,
                "g2_initial_wd_minus_active_enter_s": stats(g2)}

    # --- B: t_start ---------------------------------------------------------------
    b_band: dict[str, Any] = {}
    all_ts: list[float] = []
    timeouts = 0
    for band in ("P0", "P1", "P2"):
        rows = [r for r in ts_rows if r["band"] == band]
        q = [r for r in rows if r.get("qualifying")]
        tsv = [r["t_start_s"] for r in q if r["t_start_s"] is not None]
        fails = [r for r in rows if r["t_start_s"] is None or r.get("result") not in ("success", None)]
        timeouts += sum(1 for r in rows if r.get("result") == "timeout"
                        or r.get("job_result") == "timeout")
        all_ts += [r["t_start_s"] for r in rows if r["t_start_s"] is not None]
        up = [r["sut_uptime_us"] / 1e6 for r in q if r.get("sut_uptime_us") is not None]
        mx = max(tsv) if tsv else None
        b_band[band] = {
            "starts": len(rows), "qualifying": len(q), "failures": len(fails),
            "results": dict(Counter((r.get("active_state"), r.get("result")) for r in rows)),
            "t_start": stats(tsv),
            "timeout_over_max": (DEFAULT_TIMEOUT_START_S / mx) if mx else None,
            "le_0_8": sum(1 for t in tsv if t <= 0.8),
            "sut_uptime": stats(up),
            "episodes": len({r["episode"] for r in rows}),
        }
    for band, xs in tstart_A.items():
        all_ts += xs
    out["B"] = {"bands": b_band,
                "A_prepressure_starts": {b: stats(x) for b, x in tstart_A.items()}}

    # --- doza / memory_high qayta-ishlab-chiqarish tekshiruvi ---------------------
    for eid, e in by_ep.items():
        if not eid.startswith("B-") or "generator_gone" not in e:
            continue
        band = e["episode_begin"]["band"]
        ev_b = e["episode_begin"].get("lab_events", {})
        ev_g = e["generator_gone"].get("lab_events", {})
        tot_b = e.get("generator_started", {}).get("lab_full_total_before")
        tot_g = e["generator_gone"].get("lab_full_total_after")
        pr = pr_by_ep.get(eid, {})
        doses[band].append({"episode": eid, "part": "B", "dose_p50": None,
                            "high_delta": (ev_g.get("high", 0) - ev_b.get("high", 0))
                            if ev_g and ev_b else None,
                            "lab_full_total_delta_us": (tot_g - tot_b)
                            if (tot_g is not None and tot_b is not None) else None,
                            "overrun_s": (pr.get("stop") or {}).get("overrun_s"),
                            "pressure_stop": "stop" in pr})
    mh: dict[str, Any] = {}
    mh_ok = True
    for band in ("P0", "P1", "P2"):
        d = doses[band]
        n = len(d)
        pos = sum(1 for x in d if (x["high_delta"] or 0) > 0 and (x["lab_full_total_delta_us"] or 0) > 0)
        zero = sum(1 for x in d if (x["high_delta"] or 0) == 0 and (x["lab_full_total_delta_us"] or 0) == 0)
        dp = [x["dose_p50"] for x in d if x["dose_p50"] is not None]
        ov = [x["overrun_s"] for x in d if x["overrun_s"] is not None]
        if band == "P0":
            ok = n > 0 and zero == n
        else:
            ok = n > 0 and pos / n >= 0.9
        mh_ok = mh_ok and ok
        mh[band] = {"episodes": n, "dosed": pos, "zero": zero, "ok": ok,
                    "dose_p50_episode_medians": stats(dp),
                    "pressure_stop_written": sum(1 for x in d if x["pressure_stop"]),
                    "overrun_s": stats(ov)}
    out["memory_high_check"] = {"bands": mh, "ok": mh_ok}

    # --- guard -----------------------------------------------------------------------
    out["guard"] = {"guard_events": sum(1 for g in guard if g.get("record_type") == "guard_event"),
                    "guard_stop": next((g for g in reversed(guard)
                                        if g.get("record_type") == "guard_stop"), None)}

    # --- 13 §0.5 qoidasi ---------------------------------------------------------------
    m_start = max(all_ts) if all_ts else None
    all_deltas = [x["delta_s"] for b in gaps_all for x in gaps_all[b] if x["valid_episode"]]
    m_wd = max(all_deltas) if all_deltas else None
    rule: dict[str, Any] = {"F": F, "U_start_s": U_START_S}
    # timeout_start_sec
    reasons = []
    if timeouts:
        reasons.append(f"Result=timeout {timeouts} marta -- senzura (§0.5(1))")
    nq = {b: b_band[b]["qualifying"] for b in b_band}
    if any(v < MIN_B_STARTS for v in nq.values()):
        reasons.append(f"B namunasi yetarli emas: {nq} (< {MIN_B_STARTS}, §0.5(3))")
    if m_start is None:
        reasons.append("t_start o'lchanmadi")
    if not reasons:
        L = F * m_start
        cl = math.ceil(L)
        if cl <= U_START_S:
            prop = max(DEFAULT_TIMEOUT_START_S, cl)
            rule["timeout_start_sec"] = {"M_start_s": m_start, "L_s": L, "ceil_L": cl,
                                         "U_s": U_START_S, "proposal_s": prop,
                                         "margin_vs_M": prop / m_start}
        else:
            rule["timeout_start_sec"] = {"M_start_s": m_start, "L_s": L, "ceil_L": cl,
                                         "U_s": U_START_S, "proposal_s": None,
                                         "conflict": "ceil(L) > U"}
    else:
        rule["timeout_start_sec"] = {"M_start_s": m_start, "proposal_s": None,
                                     "reasons": reasons}
    # watchdog_sec
    reasons = []
    if wd_events:
        reasons.append(f"Result=watchdog {len(wd_events)} marta -- senzura (§0.5(1))")
    pmax = out["poll"]["max_interval_A_unit_polls_s"]
    if pmax is None or pmax >= POLL_INTERVAL_LIMIT_S:
        reasons.append(f"poller max interval {pmax} s >= {POLL_INTERVAL_LIMIT_S} s (§0.5(2))")
    nv = {b: a_band[b]["valid_episodes"] for b in a_band}
    if any(v < MIN_A_EPISODES for v in nv.values()):
        reasons.append(f"A namunasi yetarli emas: {nv} (< {MIN_A_EPISODES}, §0.5(3))")
    if m_wd is None:
        reasons.append("watchdog oraliqlari o'lchanmadi")
    if not reasons:
        u_wd = U_START_S - (m_start or 0.0)
        L = 2 * F * m_wd
        cl = max(1, math.ceil(L))
        if cl <= u_wd:
            prop = max(DEFAULT_WATCHDOG_S, cl)
            rule["watchdog_sec"] = {"M_wd_delta_s": m_wd, "L_s": L, "ceil_L": cl,
                                    "U_s": u_wd, "proposal_s": prop,
                                    "halfW_over_M_wd": (prop / 2) / m_wd if m_wd > 0 else None}
        else:
            rule["watchdog_sec"] = {"M_wd_delta_s": m_wd, "L_s": L, "ceil_L": cl,
                                    "U_s": u_wd, "proposal_s": None,
                                    "conflict": "ceil(L) > U"}
    else:
        rule["watchdog_sec"] = {"M_wd_delta_s": m_wd, "proposal_s": None,
                                "reasons": reasons}
    # T_trial (§0.7)
    if m_start is not None:
        a_chk = T_INJECT_S + RESTART_SEC_S + m_start + W_STAB_S + P_S
        b_chk = T_INJECT_S + D_PROBE_MAX_DOC10_S + W_STAB_S + P_S
        rule["t_trial"] = {"value_s": T_TRIAL_S,
                           "check_a_s": a_chk, "check_a_ok": a_chk <= T_TRIAL_S,
                           "check_b_s": b_chk, "check_b_ok": b_chk <= T_TRIAL_S,
                           "proposal_s": T_TRIAL_S if (a_chk <= T_TRIAL_S and b_chk <= T_TRIAL_S) else None}
    rule["memory_high"] = {"proposal": "192M" if mh_ok else None}
    out["rule"] = rule
    return out


def render(s: dict[str, Any]) -> str:
    L = []
    f = lambda v, d=4: "-" if v is None else (f"{v:.{d}f}" if isinstance(v, float) else str(v))  # noqa: E731
    L.append(f"run: {s['run_dir']}  controller: {s['controller_status']}")
    L.append(f"aborts/errors: {len(s['aborts'])}")
    L.append(f"poll: {s['poll']}")
    L.append("\nA -- watchdog oraliqlari (ping, barcha fazalar)")
    L.append("band  ep(valid) gaps  n_ping   p50     p90     p99     max   | during n  max   | W/maxg  maxdelta (W/2)/maxd  postmaxd")
    for b, v in s["A"]["bands"].items():
        pg, du = v["ping_gaps"], v["ping_gaps_during_pressure"]
        L.append(f"{b:4}  {v['episodes']:2}({v['valid_episodes']:2})   {v['gaps_total']:4}  {pg['n']:5}  "
                 f"{f(pg['p50'])} {f(pg['p90'])} {f(pg['p99'])} {f(pg['max'])} | {du['n']:5} {f(du['max'])} | "
                 f"{f(v['W_over_max_gap'],2)}   {f(v['max_delta_s'])}  {f(v['halfW_over_max_delta'],2)}  {f(v['post_pressure_max_delta_s'])}")
        L.append(f"      final_results={v['final_results']} quiescence={v['quiescence_states']} "
                 f"arm->first={v['arm_to_first']['n']}/{f(v['arm_to_first']['max'])} "
                 f"post_last_stall_inc={v['post_pressure_last_stall_increment_s']}")
    L.append(f"watchdog Result yozuvlari: {s['A']['watchdog_results']}")
    L.append(f"G2 (initial WD - ActiveEnter): {s['A']['g2_initial_wd_minus_active_enter_s']}")
    L.append("\nB -- t_start (qualifying)")
    for b, v in s["B"]["bands"].items():
        t = v["t_start"]
        L.append(f"{b}: starts={v['starts']} q={v['qualifying']} ep={v['episodes']} fail={v['failures']} "
                 f"min={f(t['min'])} p50={f(t['p50'])} p90={f(t['p90'])} p99={f(t['p99'])} max={f(t['max'])} "
                 f"10s/max={f(v['timeout_over_max'],2)} <=0.8={v['le_0_8']} results={v['results']}")
        L.append(f"    sut_uptime={v['sut_uptime']}")
    L.append(f"A pre-pressure starts: {s['B']['A_prepressure_starts']}")
    L.append(f"\nmemory_high check: {json.dumps(s['memory_high_check'], default=str)}")
    L.append(f"guard: events={s['guard']['guard_events']}")
    L.append(f"\nRULE: {json.dumps(s['rule'], indent=1, default=str)}")
    return "\n".join(L)


if __name__ == "__main__":
    summary = main(sys.argv[1])
    print(render(summary))
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w") as fh:
            json.dump(summary, fh, indent=1, default=str)
