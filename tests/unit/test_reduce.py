"""reduce.py testlari -- METRIKA TA'RIFLARINING to'g'riligi.

Bu testlar hech qanday eksperiment ishga tushirmaydi. Ular QO'LDA QURILGAN
kichik record oqimlarini ma'lum to'g'ri javoblar bilan taqqoslaydi, chunki
REVIX ning ilmiy hissasi o'lchov: reducer xato bo'lsa, natija xato bo'ladi.

Har fixture izohida kutilgan javob VA uning qo'lda hisobi bor -- test
"o'zini o'zi tasdiqlaydigan" bo'lmasligi kerak.

Fixture'larning umumiy geometriyasi:
  P = 100 ms, probe k ning vaqti  t_k = T0 + k*100_000 us
  baseline: k = 0..99 (10 s), progress har probe'da +200 => R_ref = 2000 iter/s
"""
import json
import os

import pytest

from revix import reduce as R
from revix.schema import DISPOSITIONS

T0 = 1_000_000
P = R.P_US
BASELINE_N = 100          # k = 0..99  (10 s)
FULL_STEP = 200           # +200/probe = 2000 iter/s
R_REF = 2000.0


# --- fixture quruvchi -------------------------------------------------------


class Builder:
    """Xom record oqimini quradi. `seq` har (emitter, record_type) uchun
    monotonik -- validator bo'shliqni aynan shu asosda tekshiradi."""

    def __init__(self, trial_id="t0"):
        self.trial_id = trial_id
        self.records = []
        self.probes = []
        self._seq = {}

    def _env(self, rt, mono_us, trial_id, emitter):
        key = (emitter, rt)
        self._seq[key] = self._seq.get(key, 0) + 1
        return {
            "schema_version": 1, "record_type": rt, "run_id": "run1",
            "session_id": "sess1", "boot_id": "boot1", "trial_id": trial_id,
            "block_index": 0, "seq": self._seq[key], "mono_us": mono_us,
            "real_us": 0, "emitter": emitter,
        }

    def add(self, rt, mono_us=0, *, trial_id=..., emitter="driver:1", **payload):
        tid = self.trial_id if trial_id is ... else trial_id
        rec = self._env(rt, mono_us, tid, emitter)
        rec.update(payload)
        self.records.append(rec)
        return rec

    def probe(self, k, outcome="ok", progress=None, invocation="inv1",
              *, trial_id=...):
        tid = self.trial_id if trial_id is ... else trial_id
        rec = self._env(R.RT_PROBE, T0 + k * P, tid, "prober:2")
        rec.update({"mono_us_send": T0 + k * P, "mono_us_recv": T0 + k * P + 900,
                    "outcome": outcome, "progress": progress,
                    "invocation_id_seen": invocation, "pid_seen": 4711,
                    "rt_us": 900})
        self.probes.append(rec)
        return rec

    def unit_state(self, mono_us, *, active_state="active", n_restarts=0,
                   invocation="inv1", enter=None, exit_=None, result="success"):
        return self.add(R.RT_UNIT_STATE, mono_us, active_state=active_state,
                        result=result, n_restarts=n_restarts,
                        invocation_id=invocation,
                        active_enter_ts_mono_us=enter,
                        active_exit_ts_mono_us=exit_)

    def oom(self, mono_us, count=0, scope="sut"):
        return self.add(R.RT_CGROUP_EVENTS, mono_us, scope=scope, oom_kill=count)

    def run(self):
        return R.RawRun(records=list(self.records), probes=list(self.probes),
                        sources=[])


def _baseline(b, invocation="inv1"):
    """k = 0..99, hammasi ok, progress +200 => R_ref = 2000 iter/s."""
    for k in range(BASELINE_N):
        b.probe(k, progress=FULL_STEP * (k + 1), invocation=invocation)
    return FULL_STEP * BASELINE_N     # k=99 dagi progress = 20000


def build_restart_trial(step_after, *, n_after=96, fail_k=(100, 105),
                        action_us=T0 + 10_450_000, invocation2="inv2",
                        hidden_at=None, drop=(), disposition="complete",
                        trial_end_us=None):
    """Standart trial: 10 s baseline -> fault -> 5 buzilgan probe -> restart ->
    `step_after` progress qadami bilan qayta ishga tushish.

    `step_after=200` toza recovery (100% throughput),
    `step_after=60`  brownout (30%), `step_after=140` brownout (70%).
    """
    b = Builder()
    b.add(R.RT_TRIAL_BEGIN, T0, arm="A", pressure_band="P2",
          fault_class="clean_crash")
    b.unit_state(T0, n_restarts=0, invocation="inv1",
                 enter=T0 - 1_000_000, exit_=0)
    b.oom(T0, 0)
    base_progress = _baseline(b)
    assert base_progress == 20_000

    b.add(R.RT_FAULT_INJECT, T0 + 10_000_000, kind="exit",
          mono_us_before_call=T0 + 9_999_000,
          mono_us_after_call=T0 + 10_000_000)
    for k in range(*fail_k):
        b.probe(k, outcome="conn_refused", progress=None, invocation=None)

    b.add(R.RT_ACTION, action_us, action_id="a0", action_class="restart",
          policy_delay_us=100_000)
    b.unit_state(T0 + 10_500_000, n_restarts=1, invocation=invocation2,
                 enter=T0 + 10_500_000, exit_=T0 + 10_000_000)
    b.oom(T0 + 10_500_000, 0)

    first = fail_k[1]
    inv = invocation2
    prog = 0
    for i in range(n_after):
        k = first + i
        if hidden_at is not None and k == hidden_at:
            inv = "inv3"          # YASHIRIN restart: action record'i YO'Q
            prog = 0
        prog += step_after
        if k in drop:
            continue
        b.probe(k, progress=prog, invocation=inv)

    last_k = first + n_after - 1
    b.unit_state(T0 + 18_000_000, n_restarts=1, invocation=invocation2,
                 enter=T0 + 10_500_000, exit_=T0 + 10_000_000)
    b.oom(T0 + 18_000_000, 0)
    end_us = trial_end_us if trial_end_us is not None else T0 + (last_k + 1) * P
    b.add(R.RT_TRIAL_END, end_us, disposition=disposition)
    return b


def reduce_one(builder, params=None):
    run = builder.run()
    trials = R.split_trials(run)
    assert len(trials) == 1
    return R.reduce_trial(trials[0], params or R.Params())


# --- 1. toza recovery -------------------------------------------------------


def test_toza_recovery_vr_true_fr_a_false():
    """Toza recovery: VR true, FR-A false.

    Qo'lda hisob: R_ref = 19800/9.9 s = 2000 iter/s. t_detect = T0+10.0 s
    (birinchi buzilgan probe, §3). t_up = T0+10.5 s (action'dan keyingi birinchi
    o'tgan probe). Oyna [10.5, 18.5] s: barcha probe ok, invocation inv2
    o'zgarmaydi, NRestarts=1 doimiy, oom yo'q, guard yo'q, throughput
    16000/8 s = 2000 = 1.0*R_ref >= 0.8*R_ref  => VR TRUE.
    Aktor `active` da'vo qildi, lekin VR true => FR-A FALSE.
    """
    payload, eps = reduce_one(build_restart_trial(FULL_STEP))
    assert payload["r_ref"] == pytest.approx(R_REF)
    assert payload["n_episodes"] == 1
    ep = eps[0]
    assert ep.t_detect_us == T0 + 10_000_000
    assert ep.t_up_us == T0 + 10_500_000
    assert ep.window_end_us == T0 + 18_500_000
    assert ep.window_complete is True
    assert ep.throughput == pytest.approx(R_REF)
    assert ep.throughput_ratio == pytest.approx(1.0)
    assert ep.invalidators == ()
    assert ep.vr is True
    assert ep.vr_reason == "verified"
    assert ep.unverified_clauses == ()       # 3,4,6 bandlar HAM tekshirildi
    assert ep.actor_success_signal is True
    assert ep.fr_a is False
    assert payload["vr"] is True
    assert payload["fr_a"] is False
    assert payload["disposition"] == "complete"
    assert payload["included_in_primary"] is True
    # §6.1 D_probe: oxirgi o'tgan probe (T0+9.9 s) -> oynaning birinchi probe'i.
    assert payload["d_probe_us"] == 600_000
    assert payload["d_probe_censored"] is False
    assert payload["d_sd_us"] == 500_000
    # §6.3 time_to_first_up = t_up - t_detect
    assert payload["time_to_first_up_us"] == 500_000
    assert payload["time_to_first_up_censored"] is False
    assert payload["time_to_vr_censored"] is False


def test_toza_recoveryda_d_eff_faqat_buzilgan_probe_larni_hisoblaydi():
    """5 buzilgan probe x P = 500 ms; brownout hadi nol (r = R_ref)."""
    payload, _ = reduce_one(build_restart_trial(FULL_STEP))
    assert payload["n_failing_probes"] == 5
    assert payload["d_eff_failing_us"] == pytest.approx(5 * P)
    assert payload["d_eff_brownout_us"] == pytest.approx(0.0)
    assert payload["d_eff_us"] == pytest.approx(500_000.0)


# --- 2. KANONIK false recovery ---------------------------------------------


def test_brownout_30_foiz_vr_false_fr_a_true():
    """Xizmat qaytdi, LEKIN 30% throughput'da, theta=0.8 => VR false, FR-A TRUE.

    BU KANONIK FALSE-RECOVERY HOLATI VA METRIKANING BUTUN MA'NOSI
    (PREREGISTRATION.md §4.5, §9.2-iii): 5-band bo'lmasa VR process-liveness'ga
    qulaydi va bu holat "recovered" deb hisoblanardi.

    Qo'lda hisob: oynadagi throughput = 60 progress / 100 ms = 600 iter/s;
    600/2000 = 0.30 < 0.80 => `throughput_below_theta`. Boshqa invalidator yo'q,
    oyna to'liq => VR FALSE. Aktor `active` da'vo qildi => FR-A TRUE.
    """
    payload, eps = reduce_one(build_restart_trial(60))
    ep = eps[0]
    assert ep.throughput == pytest.approx(600.0)
    assert ep.throughput_ratio == pytest.approx(0.30)
    assert ep.invalidators == ("throughput_below_theta",)
    assert ep.vr is False
    assert ep.window_complete is True        # aniqlanmagan EMAS, QAT'IY false
    assert ep.actor_success_signal is True
    assert ep.fr_a is True
    assert payload["vr"] is False
    assert payload["fr_a"] is True
    # Xizmat "up", demak horizon down holatda tugamadi => complete, censored emas.
    assert payload["disposition"] == "complete"
    assert payload["included_in_primary"] is True
    # VR hech qachon qanoatlantirilmadi => time-to-VR va D_probe CENSORED,
    # lekin trial TASHLANMAYDI (§6.2).
    assert payload["d_probe_censored"] is True
    assert payload["time_to_vr_censored"] is True


def test_brownout_vr_faqat_throughput_bandi_sababli_false():
    """Liveness-only ta'rif ostida bu trial "recovered" bo'lardi.

    Isbot: barcha boshqa oltita band bajarilgan (invalidator ro'yxatida faqat
    `throughput_below_theta`), va contract buzilishi oynada nol.
    """
    _payload, eps = reduce_one(build_restart_trial(60))
    ep = eps[0]
    assert ep.invalidators == ("throughput_below_theta",)
    assert all(i not in ep.invalidators for i in R.MONOTONE_INVALIDATORS)


# --- 3. yashirin restart ----------------------------------------------------


def test_yashirin_restart_oynada_vr_false():
    """Stabilizatsiya oynasi ichida `InvocationID` o'zgardi => VR false (§4.3).

    Yashirin restart uchun ACTION RECORD YO'Q, demak anchor qayta
    hisoblanMAYDI: oyna ichida ikki xil invocation ko'rinadi va
    `invocation_changed` ishlaydi. Contract'dan esa hamma probe o'tadi --
    ya'ni faqat 3-band bu holatni tutadi.
    """
    payload, eps = reduce_one(build_restart_trial(FULL_STEP, hidden_at=140))
    ep = eps[0]
    assert ep.anchor_us == T0 + 10_450_000          # anchor o'zgarmadi
    assert "invocation_changed" in ep.invalidators
    assert ep.vr is False
    assert ep.vr_reason == "invalidated"
    assert ep.n_window_failing == 0                 # contract buzilmadi
    assert payload["vr"] is False
    # Aktor muvaffaqiyat da'vo qilgan + VR false => FR-A true.
    assert payload["fr_a"] is True


# --- 4. probe uzilishi ------------------------------------------------------


def test_probe_uzilishi_censored_failed_emas():
    """Probe uzilishi > 2xP => trial `censored`, `failed` EMAS (§4).

    Instrumentatsiya yo'qolishi hech qachon jimgina natijaga aylanmaydi.
    """
    assert "failed" not in DISPOSITIONS            # enum'da "failed" YO'Q
    drop = tuple(range(130, 141))                  # 1.1 s uzilish
    payload, _ = reduce_one(build_restart_trial(FULL_STEP, drop=drop))
    assert payload["probe_gap_max_us"] > 2 * P
    assert payload["disposition"] == "censored"
    assert payload["disposition_raw"] == "complete"
    assert payload["disposition_source"] == "probe_gap"
    assert payload["disposition_conflict"] is True
    assert payload["included_in_primary"] is False
    # Censored trial KM/log-rank va loop-rate ga KIRADI (§6.2).
    assert payload["included_in_survival"] is True


# --- 5. horizon down holatda tugadi ----------------------------------------


def build_never_recovers():
    """Baseline -> fault -> horizon oxirigacha buzilgan. Action bor, natija yo'q."""
    b = Builder()
    b.add(R.RT_TRIAL_BEGIN, T0, arm="A", pressure_band="P2",
          fault_class="clean_crash")
    b.unit_state(T0, n_restarts=0, invocation="inv1",
                 enter=T0 - 1_000_000, exit_=0)
    b.oom(T0, 0)
    _baseline(b)
    b.add(R.RT_FAULT_INJECT, T0 + 10_000_000, kind="exit",
          mono_us_after_call=T0 + 10_000_000)
    for k in range(100, 151):                     # 51 buzilgan probe
        b.probe(k, outcome="conn_refused", progress=None, invocation=None)
    b.add(R.RT_ACTION, T0 + 10_450_000, action_id="a0", action_class="restart")
    b.unit_state(T0 + 12_000_000, active_state="failed", result="timeout",
                 n_restarts=1, invocation="inv2",
                 enter=T0 + 10_500_000, exit_=T0 + 10_000_000)
    b.add(R.RT_TRIAL_END, T0 + 15_100_000, disposition="censored")
    return b


def test_horizon_down_holatda_tugadi_downtime_censored_trial_tashlanmaydi():
    """Horizon tugadi, xizmat hali down => downtime `T_trial` da CENSORED.

    Qo'lda hisob: oxirgi o'tgan probe T0+9.9 s, horizon T0+15.1 s
    => D_probe = 5_200_000 us (censored). t_detect = T0+10.0 s
    => time_to_vr = 5_100_000 us (censored).

    Recovery bo'lmagan trial'larni TASHLASH klassik yashirin bias (§6.2) --
    shuning uchun trial chiqishda bor va survival analiziga kiradi.
    """
    run = build_never_recovers().run()
    out = R.reduce_run(run)
    assert out.summary["n_trials_in"] == out.summary["n_trials_out"] == 1
    p = out.trials[0]
    assert p["vr"] is False
    assert p["vr_reason"] == "no_up_probe"
    assert "contract_fail" in p["invalidators"]
    assert p["down_at_horizon"] is True
    assert p["disposition"] == "censored"
    assert p["d_probe_us"] == 5_200_000
    assert p["d_probe_censored"] is True
    assert p["time_to_vr_us"] == 5_100_000
    assert p["time_to_vr_censored"] is True
    assert p["time_to_first_up_censored"] is True
    # §6.2: censored trial KM/log-rank ga kiradi, birlamchi binar analizga yo'q.
    assert p["included_in_survival"] is True
    assert R.select_survival(out.trials) == [p]
    assert R.select_primary(out.trials) == []
    assert out.summary["disposition_counts"]["censored"] == 1


def test_trial_hech_qachon_tashlanmaydi():
    """Uchta har xil natijali trial -> uchta derived record."""
    recs, probes = [], []
    for i, b in enumerate((build_restart_trial(FULL_STEP),
                           build_never_recovers(),
                           build_restart_trial(FULL_STEP,
                                               drop=tuple(range(130, 141))))):
        for r in b.records:
            r = dict(r)
            r["trial_id"] = f"t{i}"
            recs.append(r)
        for r in b.probes:
            r = dict(r)
            r["trial_id"] = f"t{i}"
            probes.append(r)
    out = R.reduce_run(R.RawRun(records=recs, probes=probes, sources=[]))
    assert out.summary["n_trials_in"] == 3
    assert out.summary["n_trials_out"] == 3
    assert len(out.trials) == 3
    assert out.summary["disposition_counts"]["complete"] == 1
    assert out.summary["disposition_counts"]["censored"] == 2
    assert out.summary["recovered_k_of_n"] == [1, 1]     # "T_trial ichida k/n"


# --- 6. D_sd nol, D_eff haqiqiy (brownout) ---------------------------------


def build_pure_brownout():
    """Restart YO'Q, unit hech qachon `active` dan chiqmaydi, lekin throughput
    30% ga tushadi. `D_sd` uchun eng chalg'ituvchi holat (§6.1)."""
    b = Builder()
    b.add(R.RT_TRIAL_BEGIN, T0, arm="A", pressure_band="P2",
          fault_class="pressure")
    b.unit_state(T0, n_restarts=0, invocation="inv1",
                 enter=T0 - 1_000_000, exit_=0)
    b.oom(T0, 0)
    _baseline(b)
    b.add(R.RT_FAULT_INJECT, T0 + 10_000_000, kind="pressure",
          mono_us_after_call=T0 + 10_000_000)
    prog = 20_000
    for k in range(100, 200):
        prog += 60                              # 600 iter/s = 0.3 * R_ref
        b.probe(k, progress=prog, invocation="inv1")
    b.unit_state(T0 + 19_000_000, n_restarts=0, invocation="inv1",
                 enter=T0 - 1_000_000, exit_=0)
    b.oom(T0 + 19_000_000, 0)
    b.add(R.RT_TRIAL_END, T0 + 20_000_000, disposition="complete")
    return b


def test_d_sd_nol_korsatadi_d_eff_haqiqiy_downtime_korsatadi():
    """§6.1 ning asosiy natijasi: `active` lekin 30% throughput'dagi xizmat
    `D_sd` bo'yicha NOL downtime ko'rsatadi, `D_eff` esa haqiqiy.

    Qo'lda hisob: `ActiveExit` yo'q => D_sd = 0. Contract buzilmagan
    (progress qat'iy o'sadi) => D_probe = 0 va n_failing = 0. Brownout
    integrali: 99 interval x 100_000 us x (1 - 600/2000) = 99 x 70_000
    = 6_930_000 us.
    """
    payload, eps = reduce_one(build_pure_brownout())
    assert eps == []                        # failure onset yo'q
    assert payload["d_sd_us"] == 0          # ORTIQCHA KREDIT
    assert payload["d_sd_censored"] is False
    assert payload["n_failing_probes"] == 0
    assert payload["d_probe_us"] == 0       # probe ham ko'rmaydi
    assert payload["d_eff_failing_us"] == pytest.approx(0.0)
    assert payload["d_eff_brownout_us"] == pytest.approx(6_930_000.0)
    assert payload["d_eff_us"] == pytest.approx(6_930_000.0)
    assert payload["d_eff_us"] > payload["d_sd_us"]
    assert payload["d_eff_window_us"] == [T0 + 10_000_000, T0 + 20_000_000]


# --- 7. sensitivity sweep --------------------------------------------------


def build_sweep_trial():
    """70% brownout, probe'lar T0+21 s gacha -- W=8 va W=10 oynalari qoplanadi,
    W=30/60/120 esa horizon bilan kesiladi."""
    return build_restart_trial(140, n_after=106)   # k = 105..210 (T0+21.0 s)


def test_sweep_ayni_trace_theta_boyicha_har_xil_vr_beradi():
    """Bir xil XOM trace: theta=0.5 da VR true, theta=0.95 da VR false.

    Qo'lda hisob: oyna throughput'i 140/100 ms = 1400 iter/s;
    1400/2000 = 0.70. 0.70 >= 0.50 (true), 0.70 < 0.80 (false),
    0.70 < 0.95 (false). Eksperiment QAYTA ISHGA TUSHIRILMAYDI (§4).
    """
    trial = R.split_trials(build_sweep_trial().run())[0]
    cells = {(c["w_stab_s"], c["theta"]): c for c in R.sweep_trial(trial)}
    assert cells[(8.0, 0.5)]["vr"] is True
    assert cells[(8.0, 0.8)]["vr"] is False
    assert cells[(8.0, 0.95)]["vr"] is False
    assert cells[(8.0, 0.8)]["invalidators"] == ["throughput_below_theta"]


def test_sweep_toliq_grid_chiqaradi():
    """Oldindan e'lon qilingan grid: 5 x 3 = 15 yacheyka, bo'sh joy yo'q."""
    trial = R.split_trials(build_sweep_trial().run())[0]
    cells = R.sweep_trial(trial)
    assert len(cells) == len(R.W_STAB_SWEEP_S) * len(R.THETA_SWEEP) == 15
    assert R.sweep_is_complete(cells) is True
    assert {c["w_stab_s"] for c in cells} == {8.0, 10.0, 30.0, 60.0, 120.0}
    assert {c["theta"] for c in cells} == {0.5, 0.8, 0.95}


def test_sweep_kesilgan_oyna_none_beradi_false_emas():
    """`W_stab` horizon'dan uzun bo'lsa VR ANIQLANMAGAN (None), `False` emas.

    Aks holda sweep egri chizig'i pasayardi -- lekin bu fizik natija emas,
    horizon artefakti bo'lardi.
    """
    trial = R.split_trials(build_sweep_trial().run())[0]
    cells = {(c["w_stab_s"], c["theta"]): c for c in R.sweep_trial(trial)}
    assert cells[(10.0, 0.5)]["vr"] is True          # 10 s oyna hali qoplangan
    for w in (30.0, 60.0, 120.0):
        assert cells[(w, 0.5)]["vr"] is None
        assert cells[(w, 0.5)]["vr_reason"] == "window_truncated"
        assert cells[(w, 0.5)]["fr_a"] is None       # None -> False AYLANMAYDI


def test_sweep_w_stab_uzun_bolsa_monoton_invalidator_hali_ham_qatiy():
    """Kesilgan oynada ham MONOTON invalidator VR ni qat'iy false qiladi.

    `invocation_changed` bir marta ishlagach keyingi ma'lumot uni bekor
    qilmaydi, demak `None` (aniqlanmagan) emas, `False`.
    """
    b = build_restart_trial(FULL_STEP, hidden_at=140, n_after=106)
    trial = R.split_trials(b.run())[0]
    cells = {(c["w_stab_s"], c["theta"]): c for c in R.sweep_trial(trial)}
    assert cells[(120.0, 0.8)]["vr"] is False
    assert cells[(120.0, 0.8)]["invalidators"] == ["invocation_changed"]


def test_kesilgan_oynada_throughput_invalidatori_QATIY_emas():
    """Kesilgan oynada o'lchangan throughput `invalidators` ga KIRMAYDI.

    Sabab: `invalidators` ni filtrlagan tahlil o'lchanmagan da'voni haqiqat
    deb olardi. U `provisional_invalidators` da beriladi, va `vr` = None.
    """
    b = build_restart_trial(60, n_after=106)          # 30% brownout
    trial = R.split_trials(b.run())[0]
    cells = {(c["w_stab_s"], c["theta"]): c for c in R.sweep_trial(trial)}
    done = cells[(8.0, 0.8)]                          # oyna qoplangan
    cut = cells[(120.0, 0.8)]                         # oyna kesilgan
    assert done["vr"] is False
    assert done["invalidators"] == ["throughput_below_theta"]
    assert done["provisional_invalidators"] == []
    assert cut["vr"] is None
    assert cut["invalidators"] == []
    assert cut["provisional_invalidators"] == ["throughput_below_theta"]


# --- 8. FR-B matritsasiz ---------------------------------------------------


def test_fr_b_matritsasiz_hisoblanmaydi():
    """P1 da `Repairs()` YO'Q => FR-B raqam BERMAYDI (§5)."""
    res = R.evaluate_fr_b("restart", "clean_crash", False, None)
    assert res.computed is False
    assert res.value is None
    assert res.reason.startswith("not_computed")
    assert "Repairs" in res.reason


def test_fr_b_trial_recordida_ham_hisoblanmagan():
    payload, _ = reduce_one(build_restart_trial(60))
    assert payload["fr_b"]["computed"] is False
    assert payload["fr_b"]["value"] is None
    assert payload["fr_b"]["value"] is not False      # soxta 0 EMAS


def test_fr_b_matritsa_bilan_ishlaydi():
    """Matritsa berilganda FR-B hisoblanadi va `harm_indicator` OR bilan
    qo'shiladi (§5)."""
    m = R.RepairsMatrix.from_calibration(
        {("clean_crash", "restart"): (20, 20),
         ("clean_crash", "kill"): (2, 20)},
        p_min=0.7, provenance="cal-run-1")
    assert m.allowed["clean_crash"] == frozenset({"restart"})
    ok = R.evaluate_fr_b("restart", "clean_crash", False, m)
    assert (ok.computed, ok.value) == (True, False)
    bad = R.evaluate_fr_b("kill", "clean_crash", False, m)
    assert (bad.computed, bad.value) == (True, True)
    harm = R.evaluate_fr_b("restart", "clean_crash", True, m)
    assert (harm.computed, harm.value) == (True, True)
    # harm_indicator o'lchanmagan va action to'g'ri => ANIQLANMAGAN, 0 emas.
    unk = R.evaluate_fr_b("restart", "clean_crash", None, m)
    assert (unk.computed, unk.value) == (False, None)


def test_clopper_pearson_pastki_chegarasi():
    """Nashr etilgan ishlangan misol (§10.3 talab qiladi):
    20/20 uchun 95% CI pastki chegarasi = 0.025**(1/20) = 0.8316."""
    assert R.clopper_pearson_lower(20, 20) == pytest.approx(0.025 ** (1 / 20),
                                                            abs=1e-9)
    assert R.clopper_pearson_lower(0, 20) == 0.0
    # 8/10 uchun ma'lum qiymat (Clopper-Pearson, alpha=0.05): 0.4439
    assert R.clopper_pearson_lower(8, 10) == pytest.approx(0.4439, abs=5e-4)


# --- 9. loop aniqlash ------------------------------------------------------


def test_loop_detected_besh_invocation_va_barchasi_vr_dan_otmagan():
    """§6.4: loop_detected <=> T_trial ichida >=5 invocation VA barchasi VR dan
    o'tmagan."""
    b = Builder()
    b.add(R.RT_TRIAL_BEGIN, T0, arm="A", pressure_band="P2")
    b.unit_state(T0, n_restarts=0, invocation="inv1", enter=T0 - 1_000_000,
                 exit_=0)
    _baseline(b)
    b.add(R.RT_FAULT_INJECT, T0 + 10_000_000, kind="exit",
          mono_us_after_call=T0 + 10_000_000)
    k = 100
    for i in range(5):
        for _ in range(3):                    # 3 buzilgan probe (k_f)
            b.probe(k, outcome="conn_refused", progress=None, invocation=None)
            k += 1
        b.add(R.RT_ACTION, T0 + k * P, action_id=f"a{i}", action_class="restart")
        b.probe(k, progress=200, invocation=f"inv{i + 2}")   # bitta ok probe
        k += 1
        b.unit_state(T0 + k * P, n_restarts=i + 1, invocation=f"inv{i + 2}",
                     enter=T0 + k * P, exit_=T0 + (k - 1) * P)
    b.add(R.RT_TRIAL_END, T0 + k * P, disposition="censored")
    payload, _ = reduce_one(b)
    assert payload["n_invocations"] >= 5
    assert payload["n_restarts_delta"] == 5
    assert payload["loop_detected"] is True
    assert payload["vr_any"] is not True
    assert payload["loop_rate_per_s"] == pytest.approx(
        5 / (payload["t_trial_us"] / 1e6))


def test_toza_recoveryda_loop_aniqlanmaydi():
    payload, _ = reduce_one(build_restart_trial(FULL_STEP))
    assert payload["loop_detected"] is False
    assert payload["n_invocations"] == 2


# --- 10. guard va oom invalidator'lari ------------------------------------


def test_guard_ishlagan_bolsa_vr_false_va_disposition_aborted_guard():
    """7-band + §12: guard trip qilsa VR false va trial `aborted_guard`.

    `guard_event` da `trial_id` YO'Q (guard mustaqil jarayon, §8.2) --
    monotonic vaqt bo'yicha bog'lanadi.
    """
    b = build_restart_trial(FULL_STEP)
    b.add(R.RT_GUARD_EVENT, T0 + 12_000_000, trial_id=None,
          emitter="guard:9", reason="sustained_pressure", action="kill_subtree")
    payload, eps = reduce_one(b)
    assert "guard_fired" in eps[0].invalidators
    assert eps[0].vr is False
    assert payload["disposition"] == "aborted_guard"
    assert payload["included_in_primary"] is False


def test_oom_kill_oynada_vr_false():
    """6-band: oynada yangi `memory.events.oom_kill` => VR false."""
    b = build_restart_trial(FULL_STEP)
    b.oom(T0 + 14_000_000, 1)
    payload, eps = reduce_one(b)
    assert "oom_kill" in eps[0].invalidators
    assert eps[0].vr is False
    assert payload["fr_a"] is True


# --- 11. R_ref va throughput bandining majburiyligi -----------------------


def test_r_ref_bolmasa_vr_aniqlanmagan_true_emas():
    """Throughput bandi o'lchanmasa VR TASDIQLANMAYDI (§4.5).

    Busiz ma'lumot yetishmovchiligi jimgina liveness-only VR ga qulardi.
    """
    b = Builder()
    b.add(R.RT_TRIAL_BEGIN, T0, arm="A", pressure_band="P0")
    b.unit_state(T0, n_restarts=0, invocation="inv1", enter=T0, exit_=0)
    b.oom(T0, 0)
    # progress YOZILMAGAN => throughput o'lchanmaydi
    for k in range(0, 5):
        b.probe(k, progress=None, invocation="inv1")
    for k in range(5, 8):
        b.probe(k, outcome="conn_refused", progress=None, invocation=None)
    b.add(R.RT_ACTION, T0 + 8 * P, action_id="a0", action_class="restart")
    for k in range(8, 200):
        b.probe(k, progress=None, invocation="inv2")
    b.unit_state(T0 + 10 * P, n_restarts=1, invocation="inv2",
                 enter=T0 + 8 * P, exit_=T0 + 5 * P)
    b.oom(T0 + 10 * P, 0)
    b.add(R.RT_TRIAL_END, T0 + 200 * P, disposition="complete")
    payload, eps = reduce_one(b)
    assert payload["r_ref"] is None
    assert eps[0].vr is None
    assert eps[0].vr_reason == "r_ref_unavailable"
    assert "5" in eps[0].unverified_clauses
    assert payload["fr_a"] is None            # None -> False AYLANMAYDI


def test_r_ref_shu_trialdan_olinadi():
    """§4.5: `R_ref` = SHU trial'ning fault'dan oldingi throughput'i."""
    payload, _ = reduce_one(build_restart_trial(FULL_STEP))
    assert payload["r_ref"] == pytest.approx(R_REF)
    assert payload["r_ref_detail"]["source"] == "pre_fault_probes"
    assert payload["t_fault_effective_source"] == "first_contract_fail"
    assert payload["t_fault_effective_us"] == T0 + 10_000_000


# --- 12. PSI hech qanday ta'rifga kirmaydi (§5 sirkulyarlik) --------------


def test_reducer_psi_ni_oqimaydi():
    """§5 muzlatilgan kafolat #1: PSI failure, VR yoki FR ta'rifiga kirmaydi.

    Strukturaviy tekshiruv: reduce.py da `psi` so'zi faqat izohlarda uchraydi,
    va modul `cgroup`/`psi_sampler` ni import qilmaydi (offline va pur).
    """
    import revix.reduce as mod
    src = open(mod.__file__, encoding="utf-8").read()
    code_lines = []
    in_doc = False
    for line in src.splitlines():
        s = line.strip()
        if s.startswith('"""') and s.count('"""') == 1:
            in_doc = not in_doc
            continue
        if in_doc or s.startswith("#"):
            continue
        code_lines.append(line)
    code = "\n".join(code_lines)
    # Sanity: izohlarni olib tashlash butun modulni yo'q qilmadi.
    assert "def evaluate_vr(" in code
    assert "def compute_d_eff(" in code
    assert "psi" not in code.lower(), "PSI ta'rifga kirib ketdi (§5 buzildi)"
    assert "from . import cgroup" not in src
    assert "import cgroup" not in code


# --- 13. fayl chiqishi: xom hech qachon tahrirlanmaydi --------------------


def test_derived_alohida_fayllarga_yoziladi(tmp_path):
    raw = tmp_path / "raw.jsonl"
    b = build_restart_trial(FULL_STEP)
    with open(raw, "w", encoding="utf-8") as fh:
        for rec in b.records:
            fh.write(json.dumps(rec) + "\n")
        for rec in b.probes:
            fh.write(json.dumps(rec) + "\n")
    b.add(R.RT_RUN_META, 0, trial_id=None, git_dirty=False, run_mode="pilot",
          preregistration_sha256="deadbeef")
    run = R.RawRun.load([str(raw)])
    assert len(run.probes) == len(b.probes)
    out = R.reduce_run(run, sweep=True)
    paths = R.write_output(out, str(tmp_path / "derived"), run)
    for key in ("episodes", "trials", "sweep", "summary"):
        assert os.path.exists(paths[key])
        assert os.path.realpath(paths[key]) != os.path.realpath(str(raw))
    eps = [json.loads(x) for x in
           open(paths["episodes"], encoding="utf-8").read().splitlines()]
    assert len(eps) == 1
    assert eps[0]["record_type"] == "episode"
    assert eps[0]["vr"] is True
    assert eps[0]["derived"] is True
    # Xom fayl O'ZGARMADI: derived field qo'shilmadi.
    for line in open(raw, encoding="utf-8").read().splitlines():
        assert "derived" not in json.loads(line)


def test_xom_fayl_ustiga_yozish_rad_etiladi(tmp_path):
    """Derived ma'lumot qayta yaratiladi, xom -- yo'q."""
    d = tmp_path / "dir"
    d.mkdir()
    raw = d / "episodes.jsonl"          # chiqish nomi bilan bir xil
    raw.write_text("")
    run = R.RawRun(records=[], probes=[], sources=[str(raw)])
    out = R.reduce_run(run)
    with pytest.raises(R.ReductionError, match="xom"):
        R.write_output(out, str(d), run)


def test_probe_csv_oqimi_oqiladi(tmp_path):
    """Yuqori tezlikli probe oqimi CSV'da keladi (schema.py CsvWriter)."""
    csv_path = tmp_path / "probes.csv"
    rows = ["mono_us_send,outcome,progress,invocation_id_seen,seq,trial_id"]
    for k in range(3):
        rows.append(f"{T0 + k * P},ok,{200 * (k + 1)},inv1,{k + 1},t0")
    csv_path.write_text("\n".join(rows) + "\n")
    run = R.RawRun.load([], [str(csv_path)])
    assert len(run.probes) == 3
    p = R.probe_from_record(run.probes[0])
    assert (p.mono_us, p.passed, p.progress, p.invocation_id) == (T0, True, 200,
                                                                  "inv1")


# --- 14. parametrlashtirish va determinizm --------------------------------


def test_parametrlar_argument_va_muzlatilgan_qiymatlar_default():
    """§4: `W_stab`, `theta`, `p_min` argument, lekin default'lar muzlatilgan."""
    p = R.Params()
    assert p.w_stab_us == 8_000_000        # W_stab_pilot = 8 s
    assert p.theta == 0.8
    assert p.p_min == 0.7
    assert p.probe_period_us == 100_000
    assert p.k_f == 3
    assert R.W_STAB_FULL_US == 60_000_000
    assert R.INVALIDATORS == ("contract_fail", "invocation_changed",
                              "nrestarts_changed", "oom_kill",
                              "throughput_below_theta", "guard_fired")


def test_reduksiya_deterministik():
    """Bir xil xom kirish -> bir xil derived payload (envelope'siz)."""
    b = build_restart_trial(60)
    a1, _ = reduce_one(b)
    a2, _ = reduce_one(b)
    assert json.dumps(a1, sort_keys=True) == json.dumps(a2, sort_keys=True)


def test_w_stab_kichik_bolsa_oyna_qisqa_va_vr_tezroq_tasdiqlanadi():
    payload, eps = reduce_one(build_restart_trial(FULL_STEP),
                              R.Params(w_stab_us=1_000_000))
    assert eps[0].window_end_us == T0 + 11_500_000
    assert eps[0].vr is True
    assert payload["time_to_vr_us"] == 1_500_000
