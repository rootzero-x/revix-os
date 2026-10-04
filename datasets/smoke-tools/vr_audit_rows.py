#!/usr/bin/env python3
"""VR implementatsiya auditi uchun FAQAT O'QIYDIGAN yordamchi (docs/architecture/18).

Hech narsa yozmaydi: barcha chiqish stdout'ga. Kirish -- run katalogining
NUSXASI (`RAW`) va reduksiya chiqishining NUSXASI (`DER`, `reduced/` va
`view-probe.csv` bor katalog). Run katalogiga yoki derived katalogga
tegilmaydi.

Bu skript `P(VR)` ni arm/band bo'yicha HISOBLAMAYDI va chop etmaydi; effekt,
downtime yoki time-to-VR statistikasini bermaydi. U faqat (i) nomlangan
trial'larning xom probe qatorlarini, (ii) mexanik sabablar bo'yicha
sonlarni, (iii) §4 ning mustaqil minimal qayta hisobini NOMLANGAN trial'lar
uchun chiqaradi.

Ishlatish (guest'da, repo PYTHONPATH'da):
  python3 vr_audit_rows.py RAW DER cells
  python3 vr_audit_rows.py RAW DER inject  TID [TID...]
  python3 vr_audit_rows.py RAW DER p0
  python3 vr_audit_rows.py RAW DER rref
  python3 vr_audit_rows.py RAW DER window  TID [TID...]
  python3 vr_audit_rows.py RAW DER vr      TID [TID...]
  python3 vr_audit_rows.py RAW DER overlap
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, defaultdict

P_US = 100_000
K_F = 3
W_US = 8_000_000
T_RT_US = 50_000


def load_events(raw):
    recs = []
    with open(os.path.join(raw, "events.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs


def load_probes(path, target="sut"):
    out = defaultdict(list)
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if target is not None and row.get("target") not in (target, None, ""):
                continue
            out[row["trial_id"]].append(row)
    for v in out.values():
        v.sort(key=lambda r: int(r["mono_us_send"]))
    return out


def i(v):
    return None if v in (None, "") else int(v)


class Ctx:
    def __init__(self, raw, der):
        self.raw, self.der = raw, der
        self.recs = load_events(raw)
        self.cells, self.begin, self.end = {}, {}, {}
        self.by = defaultdict(lambda: defaultdict(list))
        self.overruns = []          # probe_overrun (trial_id bo'yicha)
        for r in self.recs:
            rt = r.get("record_type")
            tid = r.get("trial_id")
            if rt == "trial_begin":
                self.cells[tid] = (r["arm"], r["pressure_band"], r["block_index"])
                self.begin[tid] = r
            elif rt == "trial_end":
                self.end[tid] = r
            if tid is not None:
                self.by[tid][rt].append(r)
        self.sut = load_probes(os.path.join(raw, "probe.csv"), "sut")
        self.bys = load_probes(os.path.join(raw, "probe.csv"), "bystander")
        self.trials = {}
        self.eps = defaultdict(list)
        tp = os.path.join(der, "reduced", "trials.jsonl")
        if os.path.exists(tp):
            for line in open(tp, encoding="utf-8"):
                t = json.loads(line)
                self.trials[t["trial_id"]] = t
            for line in open(os.path.join(der, "reduced", "episodes.jsonl"),
                             encoding="utf-8"):
                e = json.loads(line)
                self.eps[e["trial_id"]].append(e)

    def b0(self, tid):
        return int(self.begin[tid]["mono_us"])

    def inject_us(self, tid):
        fi = self.by[tid].get("fault_inject") or []
        return i(fi[0].get("mono_us_after_call")) if fi else None

    def rel(self, tid, us):
        return None if us is None else round((us - self.b0(tid)) / 1e6, 3)


def fmt_row(ctx, tid, r, ref_us=None):
    t = int(r["mono_us_send"])
    d = "" if ref_us is None else f"{(t - ref_us) / 1000:+9.1f}ms"
    return (f"  t={ctx.rel(tid, t):7.3f}s {d} seq={r['seq']:>4} cyc={r['cycle']:>4} "
            f"{r['outcome']:<12} cl={r['clause_failed'] or '-':<10} "
            f"conn={r['conn_us'] or '-':>6} rt={r['rt_us'] or '-':>6} "
            f"pid={r['sut_pid_seen'] or '-':>6} inv={(r['invocation_id_seen'] or '-')[:8]} "
            f"rs={r['restart_seen'] or '-'} fs={r['fail_streak'] or '-'} "
            f"err={r['err_reason'] or '-'}")


def runs_of_failures(rows):
    """Ketma-ket buzilgan SUT probe seriyalari: (start_idx, length)."""
    out, k, n = [], 0, len(rows)
    while k < n:
        if rows[k]["outcome"] == "ok":
            k += 1
            continue
        j = k
        while j < n and rows[j]["outcome"] != "ok":
            j += 1
        out.append((k, j - k))
        k = j
    return out


def cmd_cells(ctx, _args):
    for tid, c in sorted(ctx.cells.items()):
        print(tid, *c)


def cmd_inject(ctx, args):
    for tid in args:
        inj = ctx.inject_us(tid)
        print(f"== {tid} {ctx.cells[tid]} inject(after_call)={ctx.rel(tid, inj)}s")
        rows = ctx.sut[tid]
        for r in rows:
            t = int(r["mono_us_send"])
            if inj - 500_000 <= t <= inj + 1_500_000:
                print(fmt_row(ctx, tid, r, inj))
        for rt in ("action", "unit_state"):
            for a in ctx.by[tid].get(rt, []):
                t = i(a.get("mono_us"))
                if t is not None and inj - 500_000 <= t <= inj + 1_500_000:
                    keys = ("active_state", "sub_state", "result", "n_restarts",
                            "invocation_id", "active_enter_ts_mono_us",
                            "active_exit_ts_mono_us", "unit", "t_exec_mono_us")
                    extra = {k: a.get(k) for k in keys if a.get(k) is not None}
                    for k in ("active_enter_ts_mono_us", "active_exit_ts_mono_us",
                              "t_exec_mono_us"):
                        if extra.get(k):
                            extra[k] = f"{(int(extra[k]) - inj) / 1000:+.1f}ms"
                    if "invocation_id" in extra:
                        extra["invocation_id"] = str(extra["invocation_id"])[:8]
                    print(f"  [{rt}] t={ctx.rel(tid, t)}s {(t - inj) / 1000:+.1f}ms {extra}")
        for o in ctx.by[tid].get("probe_overrun", []):
            t = i(o.get("mono_us"))
            if inj - 500_000 <= t <= inj + 1_500_000:
                print(f"  [probe_overrun] t={ctx.rel(tid, t)}s late_us={o.get('late_us')} "
                      f"skipped={o.get('skipped_cycles')}")


def cmd_p0(ctx, _args):
    """A/P0: injeksiyadan keyingi eng uzun ketma-ket buzilish seriyasi va
    reducer'ning vr_reason'i. Sonlar MEXANIK (vr qiymati emas)."""
    tab = Counter()
    for tid, c in sorted(ctx.cells.items()):
        if c[:2] != ("A", "P0"):
            continue
        inj = ctx.inject_us(tid)
        rows = ctx.sut[tid]
        if inj is None:
            print(tid, "no fault_inject")
            continue
        post = [r for r in rows if int(r["mono_us_send"]) >= inj - P_US]
        rr = runs_of_failures(post)
        first = rr[0] if rr else None
        first_len = first[1] if first else 0
        all_runs = runs_of_failures(rows)
        pre = [L for (k, L) in all_runs if int(rows[k]["mono_us_send"]) < inj and L >= K_F]
        t = ctx.trials.get(tid, {})
        eps = ctx.eps.get(tid, [])
        on = [ctx.rel(tid, e["onset_us"]) for e in eps]
        a = ctx.by[tid].get("action", [])
        rst = [round((i(x.get("t_exec_mono_us") or x.get("mono_us")) - inj) / 1000, 1) for x in a]
        # injeksiyadan keyingi birinchi o'tgan probe (yangi invocation'da)
        up = next((r for r in post if r["outcome"] == "ok"
                   and int(r["mono_us_send"]) > inj and r["restart_seen"] == "1"), None)
        up_ms = None if up is None else round((int(up["mono_us_send"]) - inj) / 1000, 1)
        print(f"{tid} first_post_inject_run={first_len} "
              f"outcomes={[r['outcome'] for r in post[first[0]:first[0]+first[1]]] if first else []} "
              f"first_ok_new_inv=+{up_ms}ms restart_exec={rst} "
              f"pre_inject_runs>=k_f={pre} reducer_vr_reason={t.get('vr_reason')} "
              f"episode_onsets={on} disp={t.get('disposition')}/{t.get('disposition_source')}")
        tab[(first_len >= K_F, t.get("vr_reason"))] += 1
    print("(first_post_inject_run>=k_f, reducer vr_reason) ->", dict(tab))


def cmd_rref(ctx, _args):
    """`progress` ning reducerga yetib borishi: uchta ko'rinish taqqoslanadi."""
    vp = os.path.join(ctx.der, "view-probe.csv")
    with open(vp, encoding="utf-8", newline="") as fh:
        hdr = next(csv.reader(fh))
    print("view-probe.csv header has 'progress':", "progress" in hdr,
          "| has 'progress_counter':", "progress_counter" in hdr)
    with open(os.path.join(ctx.raw, "probe.csv"), encoding="utf-8", newline="") as fh:
        rhdr = next(csv.reader(fh))
    print("raw probe.csv header has 'progress':", "progress" in rhdr,
          "| has 'progress_counter':", "progress_counter" in rhdr)
    sys.path.insert(0, os.environ.get("REVIX_REPO", "."))
    from revix import reduce as R
    from revix import validate as V

    # (1) reducer CLI ko'rgan narsa: view-probe.csv -> load_probe_csv
    rows = R.load_probe_csv(vp)
    ok = [r for r in rows if r.get("outcome") == "ok"]
    print("(1) CSV round trip: ok rows", len(ok), "with progress readable:",
          sum(1 for r in ok if R._as_int(r.get("progress")) is not None))
    # (2) validator ko'rgan narsa: load_run_dir (+_adapt_probe_row) -> reducer_view
    run, _f = V.load_run_dir(ctx.raw)
    view = V.reducer_view(run, "revix-sut.service", "sut")
    vok = [p for p in view.probes if p.get("outcome") == "ok"]
    print("(2) validator in-memory view: ok rows", len(vok), "with progress readable:",
          sum(1 for p in vok if R._as_int(p.get("progress")) is not None))
    print("    probe count view(2) vs csv(1):", len(view.probes), len(rows))
    # field-by-field comparison of the two views on the fields reduce reads
    key = lambda p: (p.get("trial_id"), str(p.get("mono_us_send")))
    m = {key(p): p for p in view.probes}
    diff = Counter()
    for r in rows:
        p = m.get(key(r))
        if p is None:
            diff["missing_in_view"] += 1
            continue
        for f in ("outcome", "invocation_id_seen", "mono_us_send", "trial_id",
                  "progress_counter", "seq"):
            if str(p.get(f) if p.get(f) is not None else "") != (r.get(f) or ""):
                diff[f] += 1
        if R._as_int(p.get("progress")) != R._as_int(r.get("progress")):
            diff["progress(as read by reduce)"] += 1
    print("    per-field disagreements csv(1) vs view(2):", dict(diff))
    # (3) R_ref availability in each view -- STATUS only, no VR.
    st1, st2 = Counter(), Counter()
    run1 = R.RawRun.load([os.path.join(ctx.der, "view-events.jsonl")], [vp])
    for t in R.split_trials(run1):
        tf, _ = R.fault_effective_us(t)
        st1[R.reference_throughput(t, tf)[1]] += 1
    for t in R.split_trials(view):
        tf, _ = R.fault_effective_us(t)
        r, s, d = R.reference_throughput(t, tf)
        st2[(s, d.get("source"))] += 1
    print("(3) R_ref status, reducer CLI input (csv round trip):", dict(st1))
    print("    R_ref status, validator in-memory view:          ", dict(st2))
    bw_thr = Counter(str(b.get("throughput")) for b in ctx.recs
                     if b.get("record_type") == "baseline_window")
    print("    raw baseline_window.throughput values:", dict(bw_thr))


def window_rows(ctx, tid, t_up):
    return [r for r in ctx.sut[tid] if t_up <= int(r["mono_us_send"]) <= t_up + W_US]


def gaps(rows, lim=2 * P_US):
    out = []
    for a, b in zip(rows, rows[1:]):
        d = int(b["mono_us_send"]) - int(a["mono_us_send"])
        if d > lim:
            out.append((int(a["mono_us_send"]), int(b["mono_us_send"]), d))
    return out


def cmd_window(ctx, args):
    for tid in args:
        t = ctx.trials[tid]
        eps = ctx.eps[tid]
        inj = ctx.inject_us(tid)
        print(f"== {tid} {ctx.cells[tid]} inject={ctx.rel(tid, inj)}s "
              f"T_h={ctx.rel(tid, t.get('t_hold_end_us'))}s "
              f"disp={t['disposition']}/{t['disposition_source']}")
        for e in eps:
            print(f"  episode {e['episode_id']} onset={ctx.rel(tid, e['onset_us'])} "
                  f"anchor={ctx.rel(tid, e['anchor_us'])}({e['anchor_source']}) "
                  f"t_up={ctx.rel(tid, e['t_up_us'])} wend={ctx.rel(tid, e['window_end_us'])} "
                  f"n_win={e['n_window_probes']} n_fail={e['n_window_failing']} "
                  f"inval={e['invalidators']} reason={e['vr_reason']}")
        e = eps[0]
        on = e["onset_us"]
        rows = ctx.sut[tid]
        print("  -- episode-defining run (onset +/-) --")
        for r in rows:
            if on - 300_000 <= int(r["mono_us_send"]) <= on + 600_000:
                print(fmt_row(ctx, tid, r, inj))
        tu = e["t_up_us"]
        if tu is None:
            continue
        w = window_rows(ctx, tid, tu)
        print(f"  -- window failing probes ({sum(1 for r in w if r['outcome'] != 'ok')}"
              f"/{len(w)}), ms from t_up --")
        for r in w:
            if r["outcome"] != "ok":
                print(fmt_row(ctx, tid, r, tu))
                # same-cycle bystander row
                b = [x for x in ctx.bys[tid] if x["cycle"] == r["cycle"]]
                for x in b:
                    print("     bystander same cycle:", x["outcome"], "rt", x["rt_us"],
                          "conn", x["conn_us"], "err", x["err_reason"])
        invs = Counter(r["invocation_id_seen"][:8] for r in w if r["invocation_id_seen"])
        pids = Counter(r["sut_pid_seen"] for r in w if r["sut_pid_seen"])
        print(f"  window invocations={dict(invs)} pids={dict(pids)} "
              f"restart_seen={sum(1 for r in w if r['restart_seen'] == '1')}")
        print(f"  window probe gaps >2P: {[(ctx.rel(tid, a), d) for a, _b, d in gaps(w)]}")
        ov = [o for o in ctx.by[tid].get("probe_overrun", [])
              if tu - 300_000 <= int(o["mono_us"]) <= tu + W_US + 300_000]
        print(f"  probe_overrun in window: {[(ctx.rel(tid, int(o['mono_us'])), o.get('late_us')) for o in ov]}")
        us = [(ctx.rel(tid, i(u['mono_us'])), u.get('active_state'), u.get('n_restarts'),
               (u.get('invocation_id') or '')[:8]) for u in ctx.by[tid].get('unit_state', [])
              if tu <= i(u['mono_us']) <= tu + W_US and (u.get('unit') in (None, 'revix-sut.service'))]
        print(f"  SUT unit_state in window: {us[:12]}{' ...' if len(us) > 12 else ''}")


def independent_vr(ctx, tid, with_progress):
    """§4 ning MUSTAQIL minimal qayta hisobi (reduce.py import qilinmaydi).

    Epizod: §3 -- k_f=3 ketma-ket buzilish, onset = birinchi buzilgan probe.
    Anchor (§4.1): onset'dan keyingi OXIRGI action (horizon ichida), action
    bo'lmasa onset. t_up: anchor'dan keyingi birinchi `ok` probe.
    Oyna [t_up, t_up+8s]: 2 -- har probe ok; 3 -- invocation bir xil;
    4 -- SUT unit_state.n_restarts o'zgarmas; 6 -- cgroup oom_kill;
    7 -- guard; 5 -- throughput >= 0.8 R_ref, R_ref = baseline_window
    ichidagi bitta invocation'ning (Δprogress/Δt).
    """
    rows = ctx.sut[tid]
    rr = runs_of_failures(rows)
    eps = [k for (k, L) in rr if L >= K_F]
    if not eps:
        return {"vr": None, "reason": "no_episode"}
    k0 = eps[0]
    onset = int(rows[k0]["mono_us_send"])
    end_us = int(ctx.end[tid]["mono_us"])
    acts = sorted(i(a.get("mono_us")) for a in ctx.by[tid].get("action", [])
                  if i(a.get("mono_us")) >= onset)
    anchor = acts[-1] if acts else onset
    up = next((r for r in rows if int(r["mono_us_send"]) >= anchor and r["outcome"] == "ok"), None)
    res = {"onset_s": ctx.rel(tid, onset), "anchor_s": ctx.rel(tid, anchor),
           "anchor_src": "action" if acts else "onset"}
    if up is None:
        res.update(vr=False, reason="no_up_probe", inval=["contract_fail"])
        return res
    tu = int(up["mono_us_send"])
    w = window_rows(ctx, tid, tu)
    inval = []
    nfail = sum(1 for r in w if r["outcome"] != "ok")
    if nfail:
        inval.append("contract_fail")
    if len({r["invocation_id_seen"] for r in w if r["invocation_id_seen"]}) > 1:
        inval.append("invocation_changed")
    nr = [i(u.get("n_restarts")) for u in ctx.by[tid].get("unit_state", [])
          if u.get("unit") in (None, "revix-sut.service")
          and tu <= i(u["mono_us"]) <= tu + W_US and i(u.get("n_restarts")) is not None]
    if nr and max(nr) != min(nr):
        inval.append("nrestarts_changed")
    if ctx.by[tid].get("guard_event"):
        inval.append("guard_fired")
    cg = [(i(c["mono_us"]), i(c.get("oom_kill"))) for c in ctx.by[tid].get("cgroup_events", [])]
    r_ref = None
    if with_progress:
        bw = ctx.by[tid]["baseline_window"][0]
        lo, hi = i(bw["mono_us_begin"]), i(bw["mono_us_end"])
        sel = [r for r in rows if lo <= int(r["mono_us_send"]) <= hi and r["outcome"] == "ok"]
        if sel:
            inv = sel[-1]["invocation_id_seen"]
            sel = [r for r in sel if r["invocation_id_seen"] == inv]
        if len(sel) >= 2:
            r_ref = ((int(sel[-1]["progress_counter"]) - int(sel[0]["progress_counter"])) * 1e6
                     / (int(sel[-1]["mono_us_send"]) - int(sel[0]["mono_us_send"])))
    thr = None
    if with_progress:
        okw = [r for r in w if r["outcome"] == "ok"]
        if okw:
            inv = okw[-1]["invocation_id_seen"]
            okw = [r for r in okw if r["invocation_id_seen"] == inv]
        if len(okw) >= 2:
            thr = ((int(okw[-1]["progress_counter"]) - int(okw[0]["progress_counter"])) * 1e6
                   / (int(okw[-1]["mono_us_send"]) - int(okw[0]["mono_us_send"])))
    res.update(t_up_s=ctx.rel(tid, tu), n_win=len(w), n_fail=nfail, inval=inval,
               cgroup_oom_samples=len(cg), band5_evaluable=(thr is not None and bool(r_ref)))
    if with_progress:
        # ATAYLAB: 5-band qo'shilgan holdagi `vr` qiymati CHOP ETILMAYDI --
        # audit "haqiqiy" qiymatni aytmaydi (18 §0). Faqat 5-band
        # baholanadigan-baholanmasligi va monoton invalidator'lar.
        res["monotone_invalidated"] = bool(inval)
        return res
    if inval:
        res.update(vr=False, reason="invalidated")
    else:
        res.update(vr=None, reason="r_ref_or_throughput_unavailable")
    return res


def cmd_vr(ctx, args):
    for tid in args:
        e = ctx.eps[tid][0] if ctx.eps[tid] else None
        red = (None if e is None else
               {"vr": e["vr"], "reason": e["vr_reason"], "inval": e["invalidators"],
                "onset_s": ctx.rel(tid, e["onset_us"]), "anchor_s": ctx.rel(tid, e["anchor_us"]),
                "anchor_src": e["anchor_source"], "t_up_s": ctx.rel(tid, e["t_up_us"]),
                "n_win": e["n_window_probes"], "n_fail": e["n_window_failing"]})
        print(f"== {tid} {ctx.cells[tid]}")
        print("  episodes.jsonl (first)    :", red)
        print("  independent, no progress  :", independent_vr(ctx, tid, False))
        print("  independent, progress_counter used (vr NOT printed):",
              independent_vr(ctx, tid, True))


def cmd_overlap(ctx, _args):
    """Q5: contract_fail oynalaridagi buzilgan probe'lar va prober tomoni
    uzilishlari/overrun'lari ustma-ust tushishi -- SON sifatida."""
    n_win = n_win_ov = n_win_only_near = n_sub_kf = 0
    n_fail_tot = n_fail_near = 0
    kinds = Counter()
    near = Counter()
    other = Counter()
    origin = Counter()
    per = []
    gap_trials_total = 0
    # Arm A: birinchi epizod onset'ining injeksiyaga nisbatan joyi (mexanik).
    for tid, eps in sorted(ctx.eps.items()):
        if ctx.cells[tid][0] != "A" or not eps:
            continue
        inj = ctx.inject_us(tid)
        on = eps[0]["onset_us"]
        if inj is None:
            origin["no_fault_inject"] += 1
        elif on < inj:
            origin["onset_before_inject"] += 1
        elif on <= inj + 2 * P_US:
            origin["onset_at_crash(<=inject+2P)"] += 1
        else:
            origin["onset_after_crash(>inject+2P)"] += 1
    for tid, eps in sorted(ctx.eps.items()):
        if ctx.cells[tid][0] != "A":
            continue
        e = eps[0]
        if "contract_fail" not in (e.get("invalidators") or []) or e["t_up_us"] is None:
            continue
        n_win += 1
        tu = e["t_up_us"]
        w = window_rows(ctx, tid, tu)
        g = gaps(w)
        ov = [int(o["mono_us"]) for o in ctx.by[tid].get("probe_overrun", [])]
        fails = [r for r in w if r["outcome"] != "ok"]
        max_run = max((L for _k, L in runs_of_failures(w)), default=0)
        n_sub_kf += max_run < K_F
        th = ctx.trials[tid].get("t_hold_end_us")
        touched = False
        all_near = bool(fails)
        for r in fails:
            t = int(r["mono_us_send"])
            kinds[r["outcome"]] += 1
            # "yaqin": buzilgan probe 2xP gap chetida yoki overrun record'i
            # +/- 2P ichida.
            in_gap = any(a - 2 * P_US <= t <= b + 2 * P_US for a, b, _d in g)
            in_ov = any(abs(t - o) <= 2 * P_US for o in ov)
            near[(r["outcome"], in_gap, in_ov)] += 1
            touched |= (in_gap or in_ov)
            all_near &= (in_gap or in_ov)
            n_fail_tot += 1
            n_fail_near += (in_gap or in_ov)
            other["restart_seen=1"] += r["restart_seen"] == "1"
            other["rt_deadline_on_send"] += r["err_reason"] == "rt_deadline_on_send"
            other["after_T_h"] += (th is not None and t > th)
        other["windows_with_inv_change"] += len({r["invocation_id_seen"] for r in w
                                                 if r["invocation_id_seen"]}) > 1
        n_win_ov += touched
        n_win_only_near += all_near
        per.append((tid, len(fails), max_run, len(g),
                    sum(1 for o in ov if tu <= o <= tu + W_US), touched, all_near))
    print("arm A first-episode onset vs injection:", dict(origin))
    print("per window: (trial, n_fail, max_consecutive_fail, n_gaps>2P, n_overrun, any_near, all_near)")
    for p in per:
        print("  ", p)
    print("arm A first-episode windows with contract_fail:", n_win)
    print("  max consecutive failing run in window < k_f:", n_sub_kf)
    print("  >=1 failing probe within 2P of a >2P gap or probe_overrun:", n_win_ov)
    print("  ALL failing probes within 2P of a gap/overrun:", n_win_only_near)
    print(f"failing probes in those windows: {n_fail_tot}, near gap/overrun: {n_fail_near}")
    print("failing-probe outcomes in those windows:", dict(kinds))
    print("(outcome, near_gap, near_overrun) ->", dict(near))
    print("other checks on failing probes:", dict(other))
    # rt_timeout rows anywhere vs gaps anywhere (whole run, SUT target)
    rt = 0
    rt_near = 0
    for tid, rows in ctx.sut.items():
        g = gaps(rows)
        ov = [int(o["mono_us"]) for o in ctx.by[tid].get("probe_overrun", [])]
        gap_trials_total += bool(g)
        for r in rows:
            if r["outcome"] == "rt_timeout":
                rt += 1
                t = int(r["mono_us_send"])
                if any(a - 2 * P_US <= t <= b + 2 * P_US for a, b, _d in g) or \
                        any(abs(t - o) <= 2 * P_US for o in ov):
                    rt_near += 1
    print(f"whole run: SUT rt_timeout rows={rt}, of which near gap/overrun={rt_near}; "
          f"trials with any >2P SUT gap={gap_trials_total}")


CMDS = {"cells": cmd_cells, "inject": cmd_inject, "p0": cmd_p0, "rref": cmd_rref,
        "window": cmd_window, "vr": cmd_vr, "overlap": cmd_overlap}

if __name__ == "__main__":
    raw, der, cmd, *rest = sys.argv[1:]
    CMDS[cmd](Ctx(raw, der), rest)
