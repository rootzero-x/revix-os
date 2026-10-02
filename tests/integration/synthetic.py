"""Sintetik run katalogi yozuvchisi -- integratsiya testlari uchun.

DIQQAT -- BU MA'LUMOT SINTETIK. Hech qanday eksperiment ishga tushirilmagan va
hech qanday natija mavjud emas. Bu yerdagi raqamlar (probe vaqtlari, progress,
outcome) tasodifiy EMAS, lekin hech narsani O'LCHAMAGAN: ular faqat
`events.jsonl` + `probe.csv` + `guard.jsonl` + `pressure.jsonl` + `psi.csv` +
`run_meta.json` zanjiri (kontrakt `driver-contract/v1.1` §1) ishlashini sinash
uchun shartnoma shaklida yasalgan. Pressure darajasi bu yerda natijaga
ta'sir QILMAYDI: har `A` trial bir xil tarzda tiklanadi, har `no_action`
trial tiklanmaydi. Hech qaysi son H1 ga dalil emas.

Yozish haqiqiy `schema.Emitter`/`JsonlWriter`/`CsvWriter` orqali bo'ladi (envelope
va yozuvchilar ham sinaladi) va barcha monotonic vaqtlar SINTETIK soat bilan
beriladi (`mono=` argumenti) -- shuning uchun natija deterministik.

Maydon nomlari: `reduce.py` runtime'da o'qiydiganlar va kontrakt v1.1 §4.3
jadvali (`pressure_band`, `unit_state` da xom systemd nomlari + snake_case,
`progress_counter` ustuni, ...). `trial_id`/`block_index` ENVELOPE'da.
"""
from __future__ import annotations

import json
import os
from typing import Any

from revix.prober import PROBE_FIELDS
from revix.schedule import Schedule, TrialTimeline, p1_schedule
from revix.schema import CsvWriter, Emitter, JsonlWriter

RUN_ID = "synthetic-run-0001"
SESSION_ID = "synthetic-session-0001"
BOOT_ID = "synthetic-boot-0001"
SYNTHETIC_SHA = "SYNTHETIC-FIXTURE-NOT-A-REAL-HASH"
SEED = 20260101

P = 100_000                       # probe davri, us
T_TRIAL_US = 40_100_000           # kontrakt v1.1 §5.2 (TrialTimeline() default'lari)
GUEST_START_TICKS = 123456        # sintetik PID 1 starttime
TRIAL_SPACING_US = 60_000_000     # trial'lar orasidagi sintetik vaqt
FIRST_TRIAL_US = 10_000_000
GUARD_START_US = 1_000_000
SUT = "revix-sut.service"
BYSTANDER = "revix-bystander.service"
SYNTHETIC_REAL_BASE_US = 1_700_000_000_000_000


def gen(uptime_s: float, ticks: int = GUEST_START_TICKS) -> dict[str, Any]:
    return {"pid1_starttime_ticks": ticks, "uptime_s": uptime_s}


def units_dump(unit: str) -> dict[str, Any]:
    """`units.dump_unit_properties` shakli: TIRIK unit dump'i (sintetik)."""
    return {"unit": unit, "source": "systemctl --user show",
            "alive_before": True, "alive_after": True, "load_state": "loaded",
            "dump_valid": True, "systemctl_rc": 0, "systemctl_stderr": None,
            "mono_us_dump_begin": 1, "mono_us_dump_end": 2,
            "property_count": 2,
            "properties": {"LoadState": "loaded", "MemoryMax": "SYNTHETIC"}}


def run_meta_payload(sched: Schedule, only: tuple[str, ...] = ()) -> dict[str, Any]:
    selected = [t for t in sched.trials if all(o in t.cell for o in only)]
    return {
        "synthetic_fixture": True,
        "run_id": RUN_ID, "session_id": SESSION_ID, "boot_id": BOOT_ID,
        "run_mode": "pilot",
        "started_real_us": SYNTHETIC_REAL_BASE_US, "started_mono_us": 0,
        "preregistration_sha256": SYNTHETIC_SHA,
        "preregistration_version": "synthetic",
        "git_commit": "synthetic-fixture-no-commit", "git_dirty": False,
        "rng_seed": sched.seed, "schedule_digest": sched.digest(),
        "schedule": json.loads(sched.to_json()),
        "only": list(only), "n_trials_total": sched.n_trials,
        "n_trials_selected": len(selected),
        "uname": "synthetic", "systemd_version": None, "cpu_model": None,
        "cpu_count": 4, "mem_total_kb": None,
        "cgroup_delegated_controllers": None, "oomd_effective": None,
        # WSL2: cpufreq sysfs yo'q -> o'lchanmadi (None), yozilmagan emas.
        "governor": None, "scaling_driver": None,
        "python_version": "synthetic", "module_versions": {},
        "t_trial_us": T_TRIAL_US,
        "t_trial_formula": "t_pressure_off + w_stab_s + P",
        "guest_generation": gen(1.0),
        "timeline": TrialTimeline().as_dict(),
        "units_show": {SUT: units_dump(SUT), BYSTANDER: units_dump(BYSTANDER)},
    }


def write_run(run_dir: str, *, n_blocks: int = 2, seed: int = SEED,
              only: tuple[str, ...] = ()) -> Schedule:
    """Kontrakt §1 tartibidagi sintetik run katalogini yozadi.

    `run_dir` allaqachon bo'lsa -- xato (`datasets/` append-only, §1).
    """
    os.makedirs(run_dir, exist_ok=False)
    sched = p1_schedule(seed, n_blocks)
    trials = [t for t in sched.trials if all(o in t.cell for o in only)]
    j = lambda n: os.path.join(run_dir, n)  # noqa: E731
    drv = Emitter("driver", RUN_ID, SESSION_ID, boot_id=BOOT_ID)
    drv.pid = 1
    grd = Emitter("guard", RUN_ID, SESSION_ID, boot_id=BOOT_ID)
    grd.pid = 2
    prs = Emitter("pressure", RUN_ID, SESSION_ID, boot_id=BOOT_ID)
    prs.pid = 3
    tl = TrialTimeline().as_dict()

    payload = run_meta_payload(sched, only)
    with open(j("run_meta.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")

    ev = JsonlWriter(j("events.jsonl"))
    gw = JsonlWriter(j("guard.jsonl"))
    pw = JsonlWriter(j("pressure.jsonl"))
    cw = CsvWriter(j("probe.csv"), PROBE_FIELDS)
    # psi.csv: faqat sarlavha -- bu yerda psi_sample QIYMATI o'ylab topilmaydi.
    CsvWriter(j("psi.csv"), ("mono_us", "scope", "some_total", "full_total")).close()

    def emit(w, em, rt, mono, trial=None, block=None, **kw):
        w.write(em.record(rt, kw, stream=rt, trial_id=trial,
                          block_index=block, mono=mono))

    try:
        emit(ev, drv, "run_meta", 0, **{k: v for k, v in payload.items()
                                        if k not in ("run_id", "session_id", "boot_id")})
        emit(gw, grd, "guard_start", GUARD_START_US, watch_cgroup="synthetic",
             lab_cgroup="synthetic", thresholds={})
        last_end = GUARD_START_US
        for i, t in enumerate(trials):
            t0 = FIRST_TRIAL_US + i * TRIAL_SPACING_US
            tid, blk, arm = t.trial_id, t.block_index, t.level("arm")
            level = t.level("pressure_level")
            at = lambda s: t0 + int(round(s * 1_000_000))  # noqa: E731
            e = lambda rt, mono, **kw: emit(ev, drv, rt, mono, tid, blk, **kw)  # noqa: E731

            pe = Emitter("prober", RUN_ID, SESSION_ID, boot_id=BOOT_ID)
            pe.pid = 1000 + i            # har trial'ga alohida prober jarayoni
            emit(ev, pe, "prober_start", at(3.9), tid, blk, hz=10.0,
                 targets={"sut": "synthetic"})
            e("trial_begin", t0, arm=arm, pressure_band=level,
              fault_class="clean_crash", position_in_block=t.position_in_block,
              planned_timeline=dict(tl))
            e("env_snapshot", t0 + 1, guest_generation=gen(10.0 + i))

            def unit(mono, state, nrs, inv, enter, exit_, result="success"):
                e("unit_state", mono, unit=SUT, recv_mono_us=mono,
                  recv_real_us=SYNTHETIC_REAL_BASE_US + mono,
                  ActiveState=state, active_state=state, NRestarts=nrs,
                  n_restarts=nrs, InvocationID=inv, invocation_id=inv,
                  ActiveEnterTimestampMonotonic=enter,
                  active_enter_ts_mono_us=enter,
                  ActiveExitTimestampMonotonic=exit_,
                  active_exit_ts_mono_us=exit_, Result=result, result=result)

            inv1, inv2 = f"synthetic-inv-{tid}-1", f"synthetic-inv-{tid}-2"
            unit(at(0.5), "active", 0, inv1, at(0.1), 0)
            e("baseline_window", at(15.0), mono_us_begin=at(5.0),
              mono_us_end=at(15.0), throughput=200.0)
            t_fault = at(23.0)
            e("fault_inject", t_fault, mono_us_before_call=t_fault - 1_000,
              mono_us_after_call=t_fault, fault_id=f"synthetic-{tid}",
              kind="clean_crash", params={})
            if arm == "A":
                t_act = t_fault + 250_000
                e("action", t_act, action_id=f"{tid}-a0", actor="systemd",
                  action_class="restart", policy_delay_us=100_000,
                  t_issue=t_act, t_begin=t_act, t_exec=t_act + 5_000)
                t_up = t_fault + 350_000
                unit(t_up, "active", 1, inv2, t_up, t_fault)
                e("actor_signal", t_up + 1, success=True, source="unit_state")
            else:
                unit(t_fault + 5_000, "failed", 0, inv1, at(0.1), t_fault,
                     result="exit-code")
            e("cgroup_events", at(1.0), scope="sut", oom_kill=0)
            e("cgroup_events", at(39.0), scope="sut", oom_kill=0)
            e("env_snapshot", t0 + T_TRIAL_US - 1, guest_generation=gen(50.0 + i))

            # --- probe.csv (prober yozadi): per-trial seq, per-target oqim ---
            n_probes = 0
            k = 0
            seq = 0
            while at(4.0) + k * P <= t0 + T_TRIAL_US:
                ts = at(4.0) + k * P
                seq += 1
                down = ts >= t_fault and (arm != "A" or ts < t_fault + 350_000)
                if down:
                    outcome, pc, inv = "conn_refused", None, None
                else:
                    restarted = arm == "A" and ts >= t_fault + 350_000
                    base = (t_fault + 350_000) if restarted else at(4.0)
                    outcome = "ok"
                    pc = 20 * ((ts - base) // P + 1)
                    inv = inv2 if restarted else inv1
                cw.write({"mono_us_send": ts, "mono_us_req": ts + 50,
                          "mono_us_recv": None if down else ts + 900,
                          "real_us_send": SYNTHETIC_REAL_BASE_US + ts,
                          "target": "sut", "outcome": outcome,
                          "clause_failed": "a_conn" if down else None,
                          "rt_us": None if down else 800,
                          "progress_counter": pc, "invocation_id_seen": inv,
                          "cycle": seq, "seq": seq, "trial_id": tid})
                k += 1
                n_probes += 1
            emit(ev, pe, "prober_stop", t0 + T_TRIAL_US + 20_000, tid, blk,
                 cycles=n_probes, probes=n_probes)

            if level != "P0":              # P0 = generator idle
                emit(pw, prs, "pressure_start", at(15.0), mode="synthetic")
                emit(pw, prs, "pressure_stop", at(32.0))
            disp = "complete" if arm == "A" else "censored"
            e("trial_end", t0 + T_TRIAL_US, disposition=disp,
              reason="synthetic", overhead_us=1_500_000, overhead_s=1.5)
            last_end = t0 + T_TRIAL_US
        emit(gw, grd, "guard_stop", last_end + 1_000_000, tripped=False,
             iterations=0)
    finally:
        for w in (ev, gw, pw):
            w.close()
        cw.close()
    return sched
