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
    # §16.2(B): sabab MANBANI nomlaydi -- kuzatilMAGAN natija (`probe_gap`)
    # kuzatilgan no'l-hodisadan (`down_at_horizon`) ajralishi SHART.
    assert payload["exclusion_reason"] == "censored:probe_gap"
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
    # §6.2: censored trial KM/log-rank ga kiradi.
    assert p["included_in_survival"] is True
    assert R.select_survival(out.trials) == [p]
    # §16.2(B) (v1.5): `down_at_horizon` -- KUZATILGAN NO'L-HODISA, demak u
    # binar maxrajga HAM `VR = false` sifatida KIRADI. Oldin bu assert
    # `select_primary(...) == []` edi -- o'sha §16.4 "NOTO'G'RI javob" deb
    # hukm qilgan qiymatning ifodasi.
    assert R.select_primary(out.trials) == [p]
    assert p["included_in_primary"] is True
    assert p["exclusion_reason"] is None
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
    # §16.2(B): ikki `censored` trial'ning MANBALARI boshqa -- biri
    # `down_at_horizon` (maxrajga kiradi), biri `probe_gap` (kirmaydi), demak
    # maxraj n = 2 (complete + down_at_horizon), k = 1.
    # Oldin bu [1, 1] edi, chunki `down_at_horizon` chiqarilgan edi (§16.4).
    assert out.summary["recovered_k_of_n"] == [1, 2]     # "T_trial ichida k/n"
    assert out.summary["recovered_k_of_n_set"] == R.SET_BINARY_DENOMINATOR
    # §6.2 / §16.4: analiz to'plami uchun `k/n` maxraji UCHALASINI oladi.
    # k = 2, chunki `probe_gap` trial'ining o'zida VR true (uzilish oynadan
    # tashqarida), lekin u binar MAXRAJGA kirmaydi (§4: natija kuzatilmadi) --
    # aynan shu sababli ikki to'plam ikki xil `k/n` beradi va NOMLANISHI shart.
    assert out.summary["recovered_k_of_n_analysis_set"] == [2, 3]


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


# --- 15. §16 hukmi: analiz to'plami (disposition, disposition_source) jufti --
#
# Bu bo'lim REGRESSIYA QULFI: PREREGISTRATION.md §16.2(B) hukmini kelajakdagi
# o'zgarish JIMGINA bekor qila olmasligi uchun. §16.3 nega muhimligini
# aytadi: `P2` ostida qaytmagan arm `A` trial'i AYNAN H1 oldindan aytgan
# natija (§9.2 mexanizmlari i, ii, iv), demak uni maxrajdan chiqarish
# "null natijani dunyodan emas, EKSKLYUZIYADAN" yaratishi mumkin.


def build_no_action_never_recovers(trial_id="t0", *, arm="no_action"):
    """`no_action` arm: injeksiya + `Restart=no` -> hech qachon qaytmaydi.

    ACTION RECORD YO'Q (arm hech narsa qilmaydi), demak §4.1 anchor'i
    onset bo'ladi (`anchor_source="onset"`). Horizon down holatda tugaydi.
    """
    b = Builder(trial_id)
    b.add(R.RT_TRIAL_BEGIN, T0, arm=arm, pressure_band="P2",
          fault_class="clean_crash")
    b.unit_state(T0, n_restarts=0, invocation="inv1",
                 enter=T0 - 1_000_000, exit_=0)
    b.oom(T0, 0)
    _baseline(b)
    b.add(R.RT_FAULT_INJECT, T0 + 10_000_000, kind="exit",
          mono_us_after_call=T0 + 10_000_000)
    for k in range(100, 151):                    # 51 buzilgan probe, qaytish yo'q
        b.probe(k, outcome="conn_refused", progress=None, invocation=None)
    b.unit_state(T0 + 12_000_000, active_state="failed", result="exit-code",
                 n_restarts=0, invocation="inv1",
                 enter=T0 - 1_000_000, exit_=T0 + 10_000_000)
    b.add(R.RT_TRIAL_END, T0 + 15_100_000, disposition="censored")
    return b


def test_down_at_horizon_binar_maxrajga_vr_false_sifatida_kiradi():
    """§16.2(B): `censored` + `down_at_horizon` -> maxrajga KIRADI, `VR=false`.

    §4 ning VR ta'rifi horizon bilan chegaralangan: oyna "MAVJUD BO'LSA".
    `t_up` umuman paydo bo'lmagan trial uchun oyna mavjud EMAS, demak
    `VR = false` -- TO'LIQ ANIQLANGAN, yetishmayotgan kuzatuv emas.
    """
    out = R.reduce_run(build_never_recovers().run())
    p = out.trials[0]
    assert (p["disposition"], p["disposition_source"]) == ("censored",
                                                           "down_at_horizon")
    assert p["vr"] is False                     # `None` EMAS -- aniqlangan
    assert p["vr_reason"] == "no_up_probe"
    assert p["included_in_primary"] is True
    assert p["exclusion_reason"] is None
    assert R.enters_primary_denominator("censored", "down_at_horizon") is True
    assert R.select_primary(out.trials) == [p]


def test_probe_gap_binar_maxrajdan_chiqariladi_va_sabab_manbani_nomlaydi():
    """§16.2(B) + §4: instrumentatsiya yo'qolishi jimgina natijaga aylanmaydi.

    `probe_gap` -> natija KUZATILMADI -> binar maxrajdan chiqariladi, LEKIN
    sabab manbani NOMLAYDI (§16.4: nomsiz eksklyuziya takrorlanuvchi emas).
    """
    drop = tuple(range(130, 141))                # 1.1 s uzilish > 2xP
    out = R.reduce_run(build_restart_trial(FULL_STEP, drop=drop).run())
    p = out.trials[0]
    assert (p["disposition"], p["disposition_source"]) == ("censored",
                                                           "probe_gap")
    assert p["included_in_primary"] is False
    assert p["exclusion_reason"] == "censored:probe_gap"
    assert "probe_gap" in p["exclusion_reason"]   # MANBA nomlangan
    assert R.enters_primary_denominator("censored", "probe_gap") is False
    assert R.select_primary(out.trials) == []
    # §6.2: davomiylik censored, binar natija emas -> survival'ga KIRADI.
    assert R.select_survival(out.trials) == [p]


def test_toliq_no_action_yacheykasi_bosh_birlamchi_toplam_BERMAYDI():
    """§16.1 + §16.2(B): BU HUKM AYNAN SHU HOLAT UCHUN MAVJUD.

    `no_action` arm `Restart=no` bo'lgani uchun `clean_crash` dan keyin HECH
    QACHON qaytmaydi, demak HAR DOIM horizon down holatda tugaydi. Eski
    qoida ostida yacheykaning BARCHA trial'lari birlamchi to'plamdan chiqib
    ketardi (§16.1: "60 trial ham birlamchi to'plamdan chiqadi").
    """
    recs, probes = [], []
    for i in range(5):
        b = build_no_action_never_recovers(f"t{i}")
        recs.extend(b.records)
        probes.extend(b.probes)
    out = R.reduce_run(R.RawRun(records=recs, probes=probes, sources=[]))
    assert out.summary["n_trials_in"] == out.summary["n_trials_out"] == 5
    primary = R.select_primary(out.trials)
    assert len(primary) == 5                     # BO'SH EMAS -- hukmning mohiyati
    assert all(r["arm"] == "no_action" for r in primary)
    # Konstruksiya bo'yicha `P(VR) = 0`, lekin MAXRAJ bor: 0/5, 0/0 EMAS.
    assert all(r["vr"] is False for r in primary)
    assert out.summary["recovered_k_of_n"] == [0, 5]
    assert out.summary["exclusion_rate_binary_pvr_denominator"] == 0.0


def test_ikki_eksklyuziya_darajasi_ALOHIDA_va_IKKALASI_HAM_NOMLANGAN():
    """§16.4: eksklyuziya darajasi QAYSI to'plam ustida hisoblanganini
    NOMLASHI SHART; nomlanmagan daraja natija sifatida BERILMAYDI.

    Fixture: 1 complete + 1 down_at_horizon + 1 probe_gap + 1 aborted_guard.
      * binar maxraj             -> complete + down_at_horizon = 2/4 kiradi,
                                    eksklyuziya 2/4 = 0.5
      * survival analiz to'plami -> complete + 2 censored = 3/4 kiradi,
                                    eksklyuziya 1/4 = 0.25
    Ikki to'plam -> IKKI XIL daraja, shuning uchun nom MAJBURIY.
    """
    guard_b = build_restart_trial(FULL_STEP)
    guard_b.add(R.RT_GUARD_EVENT, T0 + 12_000_000, trial_id=None,
                emitter="guard:9", reason="sustained_pressure",
                action="kill_subtree")
    recs, probes = [], []
    builders = (build_restart_trial(FULL_STEP),
                build_never_recovers(),
                build_restart_trial(FULL_STEP, drop=tuple(range(130, 141))),
                guard_b)
    for i, b in enumerate(builders):
        for r in b.records:
            r = dict(r)
            r["trial_id"] = f"t{i}"
            recs.append(r)
        for r in b.probes:
            r = dict(r)
            r["trial_id"] = f"t{i}"
            probes.append(r)
    out = R.reduce_run(R.RawRun(records=recs, probes=probes, sources=[]))
    s = out.summary
    assert s["n_trials_in"] == s["n_trials_out"] == 4

    # Ikki daraja ALOHIDA maydonlarda va har biri O'Z NOMINI ko'taradi.
    assert set(s["exclusions"]) == {R.SET_BINARY_DENOMINATOR, R.SET_SURVIVAL}
    eb = s["exclusions"][R.SET_BINARY_DENOMINATOR]
    es = s["exclusions"][R.SET_SURVIVAL]
    assert eb["analysis_set"] == R.SET_BINARY_DENOMINATOR
    assert es["analysis_set"] == R.SET_SURVIVAL

    assert (eb["n_total"], eb["n_included"], eb["n_excluded"]) == (4, 2, 2)
    assert eb["exclusion_rate"] == pytest.approx(0.5)
    assert (es["n_total"], es["n_included"], es["n_excluded"]) == (4, 3, 1)
    assert es["exclusion_rate"] == pytest.approx(0.25)

    # Ikki daraja HAR XIL -- aynan shu sababli §16.4 nomni majburiy qiladi.
    assert eb["exclusion_rate"] != es["exclusion_rate"]

    # Skalyar maydon nomlari ham to'plamni NOMLAYDI.
    assert s["exclusion_rate_binary_pvr_denominator"] == pytest.approx(0.5)
    assert s["exclusion_rate_survival_analysis_set"] == pytest.approx(0.25)

    # Sabablar MANBA bilan: probe_gap va aborted_guard ajratiladi.
    assert eb["reasons"]["censored:probe_gap"] == 1
    assert eb["reasons"]["aborted_guard:guard_event"] == 1
    assert "censored:down_at_horizon" not in eb["reasons"]   # KIRGAN, chiqmagan

    # §16.2(B): juft bo'yicha hisobot `censored` ning ikki ma'nosini ajratadi.
    assert s["disposition_source_counts"]["censored:probe_gap"] == 1
    assert s["disposition_source_counts"]["censored:down_at_horizon"] == 1


def test_eksklyuziya_darajasi_nomsiz_toplam_uchun_BERILMAYDI():
    """§16.4: nomlanmagan to'plam ustida daraja hisoblanmaydi -- fail-closed."""
    with pytest.raises(R.ReductionError, match="analiz to'plami"):
        R.exclusion_report([], analysis_set="primary")


def test_notogri_disposition_source_jimgina_maxrajga_TUSHMAYDI():
    """FAIL-CLOSED (§16.2(B)): jadvalda yo'q juft -> CHIQARILADI + NOMLANGAN.

    Juft bilan aniqlangan to'plamda noma'lum manba -- noma'lum juft. U
    jimgina maxrajga tushsa, §16.2(B) hukmi kelajakda yangi manba qo'shilishi
    bilan JIMGINA buzilardi.
    """
    for bad in ("sentinel_future_source", "", None, "DOWN_AT_HORIZON"):
        assert R.enters_primary_denominator("censored", bad) is False
        reason = R.primary_exclusion_reason("censored", bad)
        assert reason is not None
        assert "unknown_source" in reason and str(bad) in reason
    # Noma'lum `disposition` ham xuddi shunday: chiqariladi va nomlanadi.
    assert R.enters_primary_denominator("failed", "down_at_horizon") is False
    assert "unknown_disposition" in R.primary_exclusion_reason(
        "failed", "down_at_horizon")
    # Selektor ham xuddi shu qoidani ishlatadi (yagona manba).
    recs = [{"disposition": "censored", "disposition_source": "future_source",
             "vr": False},
            {"disposition": "censored", "disposition_source": "down_at_horizon",
             "vr": False}]
    assert R.select_primary(recs) == [recs[1]]


def test_derive_disposition_ishlab_chiqaradigan_HAR_MANBA_ochiq_ishlanadi():
    """`DISPOSITION_SOURCES` ning har qiymati jadvalda OCHIQ hal qilinadi.

    §16.2(B) juftga tayanadi, demak "ishlanmagan manba" degan holat
    qolmasligi SHART: har (disposition, source) jufti uchun verdict aniq va
    kirmasa sabab NOMLANGAN.
    """
    assert set(R.DISPOSITION_SOURCES) == {"probe_gap", "down_at_horizon",
                                          "guard_event", "trial_end",
                                          "derived",
                                          # §17.4(2) -- v1.6 da qo'shilgan
                                          "window_past_pressure",
                                          "window_past_horizon"}
    assert set(R.PRIMARY_DENOMINATOR_SOURCES) == set(DISPOSITIONS)
    for disp in DISPOSITIONS:
        for src in R.DISPOSITION_SOURCES:
            inc, reason = R.primary_denominator_verdict(disp, src)
            assert isinstance(inc, bool)
            assert (reason is None) is inc        # kirdi <=> sabab yo'q
            if not inc:
                assert src in reason and disp in reason
    # Maxrajga kiradigan juftlar -- AYNAN §16.2(B) aytgan to'plam.
    entering = {(d, s) for d in DISPOSITIONS for s in R.DISPOSITION_SOURCES
                if R.enters_primary_denominator(d, s)}
    assert entering == {("complete", "trial_end"), ("complete", "derived"),
                        ("censored", "down_at_horizon")}


def test_select_survival_OZGARMADI_complete_va_censored():
    """§16.4: analiz to'plami (`("complete","censored")`) -- togri, tegilmaydi.

    §6.2 DAVOMIYLIKNI `T_trial` da censor qiladi, binar natijani EMAS,
    shuning uchun `probe_gap` ham, `down_at_horizon` ham bu yerda qoladi va
    `disposition_source` bu to'plamga TA'SIR QILMAYDI.
    """
    assert R.SURVIVAL_DISPOSITIONS == ("complete", "censored")
    recs = [{"disposition": "complete", "disposition_source": "trial_end"},
            {"disposition": "censored", "disposition_source": "probe_gap"},
            {"disposition": "censored", "disposition_source": "down_at_horizon"},
            {"disposition": "censored", "disposition_source": "trial_end"},
            {"disposition": "aborted_guard", "disposition_source": "guard_event"},
            {"disposition": "contaminated", "disposition_source": "trial_end"},
            {"disposition": "washout_timeout", "disposition_source": "trial_end"},
            {"disposition": "harness_error", "disposition_source": "trial_end"}]
    assert R.select_survival(recs) == recs[:4]


def test_n_trials_in_va_out_teng_qoladi_eksklyuziya_faqat_selektorda():
    """4-qoida + §6.2: selektor QAYSI trial'ni qaytarishini o'zgartiradi,
    record SONINI hech qachon o'zgartirmaydi."""
    recs, probes = [], []
    builders = (build_restart_trial(FULL_STEP),
                build_never_recovers(),
                build_no_action_never_recovers(),
                build_restart_trial(FULL_STEP, drop=tuple(range(130, 141))))
    for i, b in enumerate(builders):
        for r in b.records:
            r = dict(r)
            r["trial_id"] = f"t{i}"
            recs.append(r)
        for r in b.probes:
            r = dict(r)
            r["trial_id"] = f"t{i}"
            probes.append(r)
    out = R.reduce_run(R.RawRun(records=recs, probes=probes, sources=[]))
    assert out.summary["n_trials_in"] == 4
    assert out.summary["n_trials_out"] == 4
    assert len(out.trials) == 4
    # Har trial'da AYNAN BITTA disposition va juftning ikkala a'zosi bor (§12).
    for r in out.trials:
        assert r["disposition"] in DISPOSITIONS
        assert r["disposition_source"] in R.DISPOSITION_SOURCES
    # Eksklyuziya faqat selektor ichida: chiqish soni = kirish soni.
    assert (out.summary["exclusions"][R.SET_BINARY_DENOMINATOR]["n_total"]
            == out.summary["n_trials_out"])


def test_PRIMARY_DISPOSITIONS_OLIB_TASHLANDI_va_qaytarilmaydi():
    """§16.4: `PRIMARY_DISPOSITIONS` -- "to'g'ri savol, NOTO'G'RI javob".

    Bu test oldin shim'ning MAVJUDLIGINI qulflardi (yagona iste'molchi
    `revix/analyze.py` hali ko'chmagan edi, va §16.6 jimgina o'zgarishni
    taqiqlaydi). Iste'molchi `enters_primary_denominator()` ga ko'chgach
    shim olib tashlandi, demak qulf TESKARIGA aylanadi: nom QAYTA
    TIKLANMASLIGI kerak.

    Nega kuchliroq: §16.2(B) dan keyin maxraj `(disposition,
    disposition_source)` jufti bilan aniqlanadi, demak `disposition`-ga
    asoslangan har qanday konstanta TA'RIFAN yetarli emas -- uni qaytarish
    7-qoidaning (i) bandini, ya'ni "bitta ruxsat-to'plami" invariantini
    buzadi.
    """
    assert not hasattr(R, "PRIMARY_DISPOSITIONS")
    # Qoida qayerda yashaydi -- OCHIQ: juft bilan ishlaydigan predikat.
    assert R.enters_primary_denominator("censored", "down_at_horizon") is True
    assert R.enters_primary_denominator("censored", "probe_gap") is False
    # 7-qoida: RUXSAT-ro'yxati bor, RAD-ro'yxati YO'Q -- ikkinchisi paydo
    # bo'lsa ikkisi ajralib ketishi mumkin bo'lardi.
    assert isinstance(R.PRIMARY_DENOMINATOR_SOURCES, dict)
    assert all(isinstance(v, frozenset)
               for v in R.PRIMARY_DENOMINATOR_SOURCES.values())
    assert not [n for n in dir(R) if "EXCLUDED_SOURCES" in n]
    # Modul manba kodida ham nom qolmadi (izohlar olib tashlangan holda) --
    # `test_analyze.py` dagi migratsiya qulfining aynasi.
    src = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))), "revix", "reduce.py")
    code = "\n".join(
        line.split("#")[0] for line in
        open(src, encoding="utf-8").read().splitlines())
    assert "PRIMARY_DISPOSITIONS" not in code


# --- 16. §17 hukmi: oyna pressure hold ICHIDA bo'lishi shart ----------------
#
# REGRESSIYA QULFI. §17.2 ning arifmetikasi muzlatilgan qiymatlardan:
# §4 ning 1-bandi oynani `t_up` dan boshlaydi, v1.3 ning yarashtiruvchi
# arifmetikasi (`3 + 8 = 11 <= 12`) esa `t_inject` dan, ya'ni jimgina nol
# recovery vaqtini nazarda tutgan. Haqiqiy shart `t_up + W_stab <= T_h`.
# §17.3: holat (a) ustun had va u H1 GA QARSHI ishlaydi, demak u soxta
# FALSIFIKATSIYA yaratishi mumkin -- shuning uchun bu testlar bor.

# Geometriya (build_restart_trial): t_up = T0 + 10.5 s, W_stab_pilot = 8 s.
T_UP_ABS = T0 + 10_500_000
WIN_END_ABS = T_UP_ABS + 8_000_000          # = T0 + 18.5 s


def _set_timing(builder, *, hold_end_us=None, horizon_end_us=None):
    """`trial_end.timing` ni o'rnatadi -- driver `TrialTiming` ni shunday yozadi.

    `horizon_end_us` berilsa `trial_end.mono_us` ham o'sha nuqtaga ko'chadi,
    aks holda horizon ikki xil joyda ikki xil bo'lib qolardi.
    """
    for rec in builder.records:
        if rec["record_type"] == R.RT_TRIAL_END:
            timing = {}
            if hold_end_us is not None:
                timing["pressure_off_mono_us"] = hold_end_us
            if horizon_end_us is not None:
                timing["horizon_end_mono_us"] = horizon_end_us
                rec["mono_us"] = horizon_end_us
            rec["timing"] = timing
    return builder


def build_late_recovery(up_k=210, end_k=220, *, last_fails=False,
                        hold_end_us=None, arm="A", band="P2", trial_id="t0"):
    """Xizmat KECH qaytadi: `t_up + W_stab` horizon'dan oshib ketadi.

    §9.2 (i) `TimeoutStartSec` oshib ketishi -- oldindan AYTILGAN mexanizm,
    `driver.py` esa `TimeoutStartSec = 10 s` ni default qilgan (§16.10), ya'ni
    bu holat dizayn o'zi kutgan holat.
    """
    b = Builder(trial_id)
    b.add(R.RT_TRIAL_BEGIN, T0, arm=arm, pressure_band=band,
          fault_class="clean_crash")
    b.unit_state(T0, n_restarts=0, invocation="inv1",
                 enter=T0 - 1_000_000, exit_=0)
    b.oom(T0, 0)
    _baseline(b)
    b.add(R.RT_FAULT_INJECT, T0 + 10_000_000, kind="exit",
          mono_us_after_call=T0 + 10_000_000)
    for k in range(100, up_k):
        b.probe(k, outcome="conn_refused", progress=None, invocation=None)
    b.add(R.RT_ACTION, T0 + (up_k - 1) * P, action_id="a0",
          action_class="restart")
    b.unit_state(T0 + up_k * P, n_restarts=1, invocation="inv2",
                 enter=T0 + up_k * P, exit_=T0 + 10_000_000)
    b.oom(T0 + up_k * P, 0)
    prog = 0
    for k in range(up_k, end_k):
        prog += FULL_STEP
        if last_fails and k == end_k - 1:
            b.probe(k, outcome="conn_refused", progress=None, invocation=None)
        else:
            b.probe(k, progress=prog, invocation="inv2")
    end_us = T0 + end_k * P
    rec = b.add(R.RT_TRIAL_END, end_us, disposition="complete")
    timing = {"horizon_end_mono_us": end_us}
    if hold_end_us is not None:
        timing["pressure_off_mono_us"] = hold_end_us
    rec["timing"] = timing
    return b


def test_holat_c_oyna_hold_ichida_bolsa_complete_qoladi():
    """§17.3 holat (c): `t_up + W <= T_h` -> to'g'ri o'lchov, hech narsa o'zgarmaydi.

    Qo'lda hisob: t_up = T0+10.5 s, W = 8 s => oyna oxiri T0+18.5 s;
    T_h = T0+19.0 s => 18.5 <= 19.0 => hold ICHIDA, bo'sh joy +0.5 s.
    """
    b = _set_timing(build_restart_trial(FULL_STEP), hold_end_us=T0 + 19_000_000)
    payload, _ = reduce_one(b)
    assert payload["t_up_us"] == T_UP_ABS
    assert payload["vr_window_end_us"] == WIN_END_ABS
    assert payload["window_containment"] == R.WINDOW_INSIDE_HOLD
    assert payload["window_inside_hold"] is True
    assert payload["window_slack_to_hold_us"] == 500_000
    assert payload["disposition"] == "complete"
    assert payload["disposition_source"] == "trial_end"
    assert payload["included_in_primary"] is True
    assert payload["vr"] is True


def test_holat_a_oyna_pressure_dan_chiqsa_censored_window_past_pressure():
    """§17.3 holat (a) + §17.4: oyna hold'dan chiqdi -> §4 kattaligi O'LCHANMADI.

    Qo'lda hisob: oyna oxiri T0+18.5 s, T_h = T0+17.0 s => 18.5 > 17.0,
    oshib ketish -1.5 s; horizon T0+20.1 s => oyna horizon ICHIDA, demak
    (b) emas, (a).

    BU ENG MUHIM HOLAT (§17.3): hozirgi kod bu trial'ni `complete` deb
    yozib, 2- va 5-bandlarni QISMAN PRESSURE'SIZ baholardi => VR osonlashadi
    => trend susayadi => §11 soxta FALSIFIKATSIYA berishi mumkin.
    """
    b = _set_timing(build_restart_trial(FULL_STEP), hold_end_us=T0 + 17_000_000)
    payload, _ = reduce_one(b)
    assert payload["window_containment"] == R.WINDOW_PAST_PRESSURE
    assert payload["window_inside_hold"] is False
    assert payload["window_slack_to_hold_us"] == -1_500_000
    # §17.4(2): `disposition` -- `censored`, `disposition_source` -- yangi qiymat.
    assert payload["disposition"] == "censored"
    assert payload["disposition_source"] == "window_past_pressure"
    # §12 ning yopiq enum'iga TEGILMADI.
    assert payload["disposition"] in DISPOSITIONS
    assert "window_past_pressure" not in DISPOSITIONS
    # §17.4(1),(3): binar maxrajdan chiqariladi, sabab manbani NOMLAYDI.
    assert payload["included_in_primary"] is False
    assert payload["exclusion_reason"] == "censored:window_past_pressure"
    # §17.4(3): §6.2 bo'yicha KM/log-rank ga censored davomiylik sifatida KIRADI.
    assert payload["included_in_survival"] is True


def test_holat_b_oyna_horizon_dan_chiqsa_censored_window_past_horizon():
    """§17.3 holat (b): `t_up + W > T_trial` -> haqiqiy administrativ censoring.

    Qo'lda hisob: t_up = T0+21.0 s (k=210), W = 8 s => oyna oxiri T0+29.0 s;
    horizon T0+22.0 s => 29.0 > 22.0 => oyna HORIZON'dan chiqdi.

    Hozirgi kod bu trial'ni `complete` + `VR = false` deb yozardi, ya'ni
    haqiqiy censoring'ni KUZATILGAN muvaffaqiyatsizlik deb yozardi (§17.3(b)).
    """
    out = R.reduce_run(build_late_recovery().run())
    p = out.trials[0]
    assert p["t_up_us"] == T0 + 21_000_000
    assert p["vr_window_end_us"] == T0 + 29_000_000
    assert p["t_horizon_end_us"] == T0 + 22_000_000
    assert p["window_containment"] == R.WINDOW_PAST_HORIZON
    assert p["window_slack_to_horizon_us"] == -7_000_000
    assert p["disposition"] == "censored"
    assert p["disposition_source"] == "window_past_horizon"
    assert p["included_in_primary"] is False
    assert p["exclusion_reason"] == "censored:window_past_horizon"
    assert p["included_in_survival"] is True
    assert R.select_primary(out.trials) == []
    assert R.select_survival(out.trials) == [p]


def test_holat_b_T_h_SIZ_HAM_aniqlanadi():
    """(b) `T_h` ni TALAB QILMAYDI -- faqat `T_trial` kerak (§17.2 arifmetikasi).

    Shuning uchun u `timing.pressure_off_mono_us` yozilmagan run'da ham
    ushlanadi, ya'ni §17.4 eski ma'lumotda ham kuchda qoladi.
    """
    b = build_late_recovery()
    for rec in b.records:
        if rec["record_type"] == R.RT_TRIAL_END:
            rec["timing"].pop("pressure_off_mono_us", None)
    payload, _ = reduce_one(b)
    assert payload["t_hold_end_us"] is None
    assert payload["window_containment"] == R.WINDOW_PAST_HORIZON
    assert payload["disposition_source"] == "window_past_horizon"
    assert payload["included_in_primary"] is False


# ===========================================================================
# ⚠ TARTIB QULFI -- §17.4 ning markaziy testi. Buni o'chirmang, yumshatmang.
#    U tartib argumentini EHTIMOLIY dalildan KO'RSATILGAN dalilga aylantiradi:
#    bir xil fixture ustida ikki tartib ikki TESKARI natija beradi.
# ===========================================================================


def test_oyna_holati_down_at_horizon_dan_OLDIN_klassifikatsiya_qilinadi():
    """§17.4 ning TARTIB qulfi -- bu test bo'lmasa hukm JIMGINA bekor bo'ladi.

    `down_at_horizon` faqat `not probes[-1].passed` ga qaraydi, demak u
    "xizmat qaytdi, keyin yana yiqildi" va "oyna kesildi" holatlarini HAM
    ushlaydi. Agar u OLDIN tekshirilsa, bu trial `censored:down_at_horizon`
    bo'lardi -- va o'sha juft §16.2(B) bo'yicha binar maxrajga KIRADI,
    ya'ni §17.4(1) ("oynasi hold ichida bo'lmagan trial `VR = false` deb
    yozilMAYDI va maxrajga kiritilMAYDI") buzilardi.

    Fixture: oyna horizon'dan chiqadi VA oxirgi probe buzilgan, demak
    IKKI shart bir vaqtda to'g'ri -- aynan shu ustma-ustlik tartibni
    KUZATILADIGAN qiladi.

    Ikkinchi qism -- MEXANIK KONTRFAKT: `derive_disposition` ayni shu
    trial'da oyna argumentisiz (eski tartibning aynasi) chaqiriladi va
    natija teskari bo'lishi KO'RSATILADI. Ya'ni "tartib muhim" degan da'vo
    mulohaza emas, o'lchov.
    """
    out = R.reduce_run(build_late_recovery(last_fails=True).run())
    p = out.trials[0]
    # Ikki shart HAM bajarilgan:
    assert p["down_at_horizon"] is True
    assert p["window_containment"] == R.WINDOW_PAST_HORIZON
    # ... lekin OYNA holati yutadi (§17.4), demak trial CHIQARILADI.
    assert p["disposition_source"] == "window_past_horizon"
    assert p["disposition_source"] != "down_at_horizon"
    assert p["included_in_primary"] is False
    assert p["exclusion_reason"] == "censored:window_past_horizon"

    # --- MEXANIK KONTRFAKT: bir xil trial, ikki tartib ---------------------
    trial = R.split_trials(build_late_recovery(last_fails=True).run())[0]
    prm = R.Params()
    gaps = R.probe_gaps(trial, prm)
    down = bool(trial.probes) and not trial.probes[-1].passed
    assert down is True

    # (1) ESKI tartib = oyna klassifikatsiyasi YO'Q (`window=None`).
    old_disp, old_src, _ = R.derive_disposition(trial, gaps, down)
    assert (old_disp, old_src) == ("censored", "down_at_horizon")
    assert R.enters_primary_denominator(old_disp, old_src) is True   # KIRARDI
    # Va KIRGANDA `VR` nima bo'lardi -- `False`, ya'ni aynan §17.4(1) ning
    # taqiqlagani: kuzatilmagan natija kuzatilgan muvaffaqiyatsizlik bo'lib.
    assert p["vr"] is False

    # (2) YANGI tartib = oyna klassifikatsiyasi BOR.
    window = R.classify_window_containment(
        p["t_up_us"], prm, hold_end_us=trial.hold_end_us,
        horizon_end_us=trial.horizon_end_us)
    new_disp, new_src, _ = R.derive_disposition(trial, gaps, down, window)
    assert (new_disp, new_src) == ("censored", "window_past_horizon")
    assert R.enters_primary_denominator(new_disp, new_src) is False   # CHIQADI

    # Ikki tartib TESKARI javob beradi -- da'vo shu bilan ko'rsatilgan.
    assert (R.enters_primary_denominator(old_disp, old_src)
            is not R.enters_primary_denominator(new_disp, new_src))
    assert p["exclusion_reason"] == "censored:window_past_horizon"
    # Eski tartib bo'lsa bu juft maxrajga KIRARDI -- shuni ham qulflaymiz.
    assert R.enters_primary_denominator("censored", "down_at_horizon") is True
    assert R.enters_primary_denominator("censored", "window_past_horizon") is False


def test_t_up_bolmasa_down_at_horizon_O_ZGARMAYDI():
    """§17 `no_t_up` holatiga TEGMAYDI: §16.2(B) hukmi kuchda qoladi.

    `t_up` umuman paydo bo'lmasa oyna BOSHLANMAYDI, demak §17.3 ning uch
    holatidan hech biri qo'llanmaydi va trial §16.2(B) bo'yicha maxrajga
    `VR = false` sifatida kiradi.
    """
    out = R.reduce_run(build_no_action_never_recovers().run())
    p = out.trials[0]
    assert p["t_up_us"] is None
    assert p["window_containment"] == R.WINDOW_NO_T_UP
    assert p["window_inside_hold"] is None          # `False` EMAS
    assert p["disposition_source"] == "down_at_horizon"
    assert p["included_in_primary"] is True
    assert p["vr"] is False


def test_window_truncated_endi_binar_maxrajga_TUSHMAYDI():
    """§16.8 -> §17.4: kesilgan oyna `vr=None` beradi, u maxrajda QOLMAYDI.

    v1.5 da bu OCHIQ savol edi va `vr_undetermined_in_binary_denominator`
    uni faqat KO'RSATARDI. §17.4 undan keyin: kesilgan oyna
    `window_past_horizon`, demak chiqariladi va hisoblagich NOLGA tushadi --
    ya'ni hisoblagich endi diagnostika emas, TIRIK ASSERTION.
    """
    out = R.reduce_run(build_late_recovery().run())
    p = out.trials[0]
    assert p["vr"] is None
    assert p["vr_reason"] == "window_truncated"      # oyna kesildi
    assert p["included_in_primary"] is False         # ... lekin maxrajda YO'Q
    assert out.summary["vr_undetermined_in_binary_denominator"] == 0
    assert out.summary["vr_undetermined_in_binary_denominator_by_reason"] == {}


def test_T_h_olchanmasa_oyna_holati_not_evaluated_va_JIM_QOLMAYDI():
    """`T_h` o'lchanmasa (a) va (c) AJRALMAYDI -> `None`, `False` emas.

    `None` = "o'lchanmadi" disiplinasi: `inside_hold = False` deb yozish
    kuzatilmagan narsani natija deb yozish bo'lardi, `True` deb yozish esa
    §17.4 ni jimgina chetlab o'tish. Shuning uchun uchinchi qiymat, va
    §17.4(5) validatori tekshira olmaydigan trial'lar soni OCHIQ beriladi.
    """
    out = R.reduce_run(build_restart_trial(FULL_STEP).run())   # `timing` YO'Q
    p = out.trials[0]
    assert p["t_hold_end_us"] is None
    assert p["window_containment"] == R.WINDOW_NOT_EVALUATED
    assert p["window_inside_hold"] is None
    assert p["window_slack_to_hold_us"] is None
    # Klassifikatsiya qilinmagani uchun disposition O'ZGARMAYDI.
    assert p["disposition"] == "complete"
    # ... lekin fakt JIM QOLMAYDI (§12: yashirilmaydi).
    assert out.summary["n_window_containment_not_evaluated"] == 1
    assert out.summary["window_containment_counts"][R.WINDOW_NOT_EVALUATED] == 1


def test_oyna_kirishlari_validator_uchun_record_DA_bor():
    """§17.4(5): validator `t_up + W_stab_pilot <= T_h` ni tekshirishi SHART.

    Shuning uchun har operand record'da bor va validator reducer'ning
    verdict'iga ishonishi shart emas -- u arifmetikani QAYTA hisoblay oladi.
    """
    b = _set_timing(build_restart_trial(FULL_STEP), hold_end_us=T0 + 17_000_000)
    payload, _ = reduce_one(b)
    for key in ("t_up_us", "vr_window_end_us", "w_stab_us", "t_hold_end_us",
                "t_horizon_end_us", "window_containment", "window_inside_hold",
                "window_slack_to_hold_us", "window_slack_to_horizon_us"):
        assert key in payload, key
    # Operandlardan verdict QAYTA hisoblanadi -- ikkisi mos keladi.
    assert payload["w_stab_us"] == 8_000_000               # W_stab_pilot (§4)
    assert (payload["t_up_us"] + payload["w_stab_us"]
            == payload["vr_window_end_us"])
    recomputed = payload["vr_window_end_us"] <= payload["t_hold_end_us"]
    assert recomputed is payload["window_inside_hold"]
    assert recomputed is False                              # §17.4(5) buzilishi
    assert (payload["t_hold_end_us"] - payload["vr_window_end_us"]
            == payload["window_slack_to_hold_us"])


def test_classify_window_containment_arifmetikasi_ANIQ_slack_qoshilmaydi():
    """§17.2 arifmetikasi aniq: tenglik ichida, +1 us tashqarida.

    `evaluate_vr` oyna QOPLANISHI uchun bitta probe davri yo'l qo'yadi
    (§6.1 kvantlashi), lekin bu YERDA slack QO'SHILMAYDI: §17.2 ning sharti
    muzlatilgan qiymatlardan olingan, demak unga slack qo'shish muzlatilgan
    cheklovni jimgina KENGAYTIRISH bo'lardi.
    """
    prm = R.Params()                                  # W_stab_pilot = 8 s
    t_up = 1_000_000
    win_end = t_up + 8_000_000
    horizon = win_end + 10_000_000

    # Tenglik -> ICHIDA (§17.4 shartni `<=` bilan yozadi).
    w = R.classify_window_containment(t_up, prm, hold_end_us=win_end,
                                      horizon_end_us=horizon)
    assert (w.status, w.inside_hold, w.slack_to_hold_us) == (
        R.WINDOW_INSIDE_HOLD, True, 0)
    # Bir mikrosekund kam -> TASHQARIDA. Probe davri (100 ms) slack BERILMAYDI.
    w = R.classify_window_containment(t_up, prm, hold_end_us=win_end - 1,
                                      horizon_end_us=horizon)
    assert (w.status, w.inside_hold, w.slack_to_hold_us) == (
        R.WINDOW_PAST_PRESSURE, False, -1)
    w = R.classify_window_containment(t_up, prm,
                                      hold_end_us=win_end - prm.probe_period_us,
                                      horizon_end_us=horizon)
    assert w.status == R.WINDOW_PAST_PRESSURE          # slack YO'Q
    # (b) (a) dan USTUN: ikkisi ham to'g'ri bo'lganda `past_horizon` yutadi.
    w = R.classify_window_containment(t_up, prm, hold_end_us=win_end - 1,
                                      horizon_end_us=win_end - 1)
    assert w.status == R.WINDOW_PAST_HORIZON
    # `t_up` yo'q -> hech qanday holat qo'llanmaydi.
    w = R.classify_window_containment(None, prm, hold_end_us=win_end,
                                      horizon_end_us=horizon)
    assert (w.status, w.inside_hold, w.window_end_us) == (
        R.WINDOW_NO_T_UP, None, None)
    # Yopiq enum: boshqa status chiqmaydi.
    assert w.status in R.WINDOW_CONTAINMENTS


def test_oyna_eksklyuziyasi_arm_x_pressure_YACHEYKASI_boyicha_beriladi():
    """§17.4(4): daraja `(arm x pressure)` bo'yicha ALOHIDA, nomi bilan.

    *"`P2` yacheykasida to'plangan yuqori daraja -- o'zi NATIJA: u 'dizayn
    qiziqtirgan yacheykani o'lchay olmadi' degan ma'noni beradi."*

    Fixture: A|P0 -> 1 to'g'ri; A|P2 -> 2 oynasi chiqib ketgan trial.
    Agregat daraja 2/3 = 0.667, lekin `P2` yacheykasida 2/2 = 1.0 va `P0` da
    0.0 -- agregat o'sha to'planishni YASHIRADI.
    """
    recs, probes = [], []
    builders = [
        ("t0", _set_timing(build_restart_trial(FULL_STEP),
                           hold_end_us=T0 + 19_000_000), "A", "P0"),
        ("t1", _set_timing(build_restart_trial(FULL_STEP),
                           hold_end_us=T0 + 17_000_000), "A", "P2"),
        ("t2", build_late_recovery(trial_id="t2"), "A", "P2"),
    ]
    for tid, b, arm, band in builders:
        for r in b.records:
            r = dict(r)
            r["trial_id"] = tid
            if r["record_type"] == R.RT_TRIAL_BEGIN:
                r["arm"], r["pressure_band"] = arm, band
            recs.append(r)
        for r in b.probes:
            r = dict(r)
            r["trial_id"] = tid
            probes.append(r)
    out = R.reduce_run(R.RawRun(records=recs, probes=probes, sources=[]))
    assert out.summary["n_trials_in"] == out.summary["n_trials_out"] == 3

    w = out.summary["window_containment"]
    # §16.4: obyekt O'ZIDA ikki nomni ko'taradi -- qaysi to'plam, qaysi maxraj.
    assert w["analysis_set"] == R.SET_BINARY_DENOMINATOR
    assert w["rate_denominator"] == "all_trials_in_cell"
    assert w["disposition_sources"] == ["window_past_pressure",
                                        "window_past_horizon"]
    assert w["n_window_excluded"] == 2
    assert w["window_exclusion_rate"] == pytest.approx(2 / 3)

    # Yacheyka bo'yicha: to'planish KO'RINADI.
    p0, p2 = w["by_cell"]["A|P0"], w["by_cell"]["A|P2"]
    assert (p0["arm"], p0["pressure_band"]) == ("A", "P0")
    assert p0["n_window_excluded"] == 0
    assert p0["window_exclusion_rate"] == pytest.approx(0.0)
    assert p0["n_inside_hold"] == 1
    assert (p2["arm"], p2["pressure_band"]) == ("A", "P2")
    assert p2["n_window_past_pressure"] == 1
    assert p2["n_window_past_horizon"] == 1
    assert p2["n_window_excluded"] == 2
    assert p2["window_exclusion_rate"] == pytest.approx(1.0)
    # Har yacheyka HAM o'z nomini ko'taradi (§16.4).
    assert p2["analysis_set"] == R.SET_BINARY_DENOMINATOR
    assert p2["rate_denominator"] == "all_trials_in_cell"

    # Agregat daraja yacheyka darajasini YASHIRADI -- shuning uchun ikkisi ham.
    assert p2["window_exclusion_rate"] != w["window_exclusion_rate"]

    # Umumiy eksklyuziya hisoboti ham yacheyka bo'yicha beriladi (§17.4(4)).
    eb = out.summary["exclusions"][R.SET_BINARY_DENOMINATOR]
    assert eb["by_cell"]["A|P2"]["n_excluded"] == 2
    assert eb["by_cell"]["A|P2"]["exclusion_rate"] == pytest.approx(1.0)
    assert eb["by_cell"]["A|P0"]["exclusion_rate"] == pytest.approx(0.0)
    assert eb["by_cell"]["A|P2"]["reasons"] == {
        "censored:window_past_pressure": 1,
        "censored:window_past_horizon": 1,
    }
    # §6.2: ikkisi ham survival to'plamiga KIRADI, demak u yerda daraja 0.
    es = out.summary["exclusions"][R.SET_SURVIVAL]
    assert es["by_cell"]["A|P2"]["n_excluded"] == 0
    # Oyna holatlari sanog'i (yopiq enum, nol bilan to'ldirilgan).
    assert out.summary["window_containment_counts"] == {
        R.WINDOW_INSIDE_HOLD: 1, R.WINDOW_PAST_PRESSURE: 1,
        R.WINDOW_PAST_HORIZON: 1, R.WINDOW_NO_T_UP: 0,
        R.WINDOW_NOT_EVALUATED: 0,
    }


def test_probe_gap_oyna_holatidan_USTUN():
    """TARTIB: uzilish > 2xP bo'lsa `t_up` ning o'zi artefakt bo'lishi mumkin.

    §4 probe uzilishiga O'Z hukmini beradi, shuning uchun oyna joylashuvini
    ishonchsiz trace'dan hisoblab, unga yorliq qo'yish noto'g'ri bo'lardi.
    """
    b = _set_timing(build_restart_trial(FULL_STEP, drop=tuple(range(130, 141))),
                    hold_end_us=T0 + 17_000_000)
    payload, _ = reduce_one(b)
    assert payload["window_containment"] == R.WINDOW_PAST_PRESSURE  # hisoblandi
    assert payload["disposition_source"] == "probe_gap"             # §4 USTUN
    assert payload["exclusion_reason"] == "censored:probe_gap"
    assert payload["included_in_primary"] is False


def test_guard_va_kontaminatsiya_oyna_holatidan_USTUN():
    """TARTIB: `aborted_guard` (§4 7-band) va kontaminatsiya (§6.2) ustun.

    §6.2 asosi: eksklyuziya sababi censoring'dan ustun bo'lishi SHART, aks
    holda chiqarilishi kerak trial `censored` yorlig'i ostida analizga
    kirib ketardi.
    """
    g = _set_timing(build_restart_trial(FULL_STEP), hold_end_us=T0 + 17_000_000)
    g.add(R.RT_GUARD_EVENT, T0 + 12_000_000, trial_id=None, emitter="guard:9",
          reason="sustained_pressure", action="kill_subtree")
    payload, _ = reduce_one(g)
    assert payload["window_containment"] == R.WINDOW_PAST_PRESSURE
    assert payload["disposition"] == "aborted_guard"
    assert payload["disposition_source"] == "guard_event"

    c = _set_timing(build_restart_trial(FULL_STEP, disposition="contaminated"),
                    hold_end_us=T0 + 17_000_000)
    payload, _ = reduce_one(c)
    assert payload["window_containment"] == R.WINDOW_PAST_PRESSURE
    assert payload["disposition"] == "contaminated"
    assert payload["disposition_source"] == "trial_end"


def test_yangi_juftlar_maxrajdan_chiqariladi_toplam_AYNAN_ozgarmadi():
    """§17.4(3): ikki yangi juft chiqariladi; kiradigan to'plam O'ZGARMADI.

    Ruxsat-ro'yxati (allow-list) fail-closed: yangi manba qo'shilgani bilan
    maxrajga kiradigan juftlar to'plami o'zgarmadi, ya'ni §16.2(B) ning
    hukmi ham, §17.4 ning hukmi ham bir vaqtda kuchda.
    """
    for src in ("window_past_pressure", "window_past_horizon"):
        assert R.enters_primary_denominator("censored", src) is False
        assert R.primary_exclusion_reason("censored", src) == f"censored:{src}"
        # Manba NOMLANGAN -- "unknown" emas, ya'ni ataylab hal qilingan.
        assert "unknown" not in R.primary_exclusion_reason("censored", src)
    entering = {(d, s) for d in DISPOSITIONS for s in R.DISPOSITION_SOURCES
                if R.enters_primary_denominator(d, s)}
    assert entering == {("complete", "trial_end"), ("complete", "derived"),
                        ("censored", "down_at_horizon")}
    # `SURVIVAL_DISPOSITIONS` manbadan MUSTAQIL -> ikkisi ham survival'da.
    recs = [{"disposition": "censored", "disposition_source": s}
            for s in ("window_past_pressure", "window_past_horizon")]
    assert R.select_survival(recs) == recs


def test_vr_undetermined_sabab_boyicha_ochiq_beriladi():
    """`vr=None` sabablari BUTUN run bo'yicha sanab beriladi -- yashirilmaydi.

    v1.6 da bu test `no_episode` trial'ining MAXRAJDA ekanini qayd etardi,
    chunki §16 ham, §17 ham unga javob bermagan edi. **§20.3 unga javob
    berdi:** epizod bo'lmasa §4 ning predikati instansiyalanmaydi, demak
    trial maxrajdan CHIQADI (`included_in_primary is False`). Shuning uchun
    bu test endi maxrajga kirishni emas, SABABNING OCHIQ BERILISHINI
    qulflaydi -- ma'lumot yo'qolmaganini.
    """
    out = R.reduce_run(build_pure_brownout().run())
    p = out.trials[0]
    assert p["window_containment"] == R.WINDOW_NO_T_UP
    assert p["vr"] is None
    assert p["vr_reason"] == "no_episode"
    # §20.3: maxrajdan CHIQADI (v1.6 da `True` edi).
    assert p["included_in_primary"] is False
    # §20.2 invarianti: maxrajda `vr=None` qolmaydi.
    assert out.summary["vr_undetermined_in_binary_denominator"] == 0
    assert out.summary["vr_undetermined_in_binary_denominator_by_reason"] == {}
    # ... lekin sabab BUTUN run hisobotida ko'rinadi -- yashirilmaydi (§12).
    by_reason = out.summary["vr_undetermined_counts_by_reason"]
    assert by_reason == {"no_episode": 1}
    # §17 ga tegishli sabab (`window_truncated`) bu fixture'da yo'q.
    assert "window_truncated" not in by_reason


def test_oyna_hukmi_trial_sonini_OZGARTIRMAYDI():
    """4-qoida: §17 selektor qaytaradigan trial'ni o'zgartiradi, SONINI emas."""
    recs, probes = [], []
    builders = (_set_timing(build_restart_trial(FULL_STEP),
                            hold_end_us=T0 + 19_000_000),
                _set_timing(build_restart_trial(FULL_STEP),
                            hold_end_us=T0 + 17_000_000),
                build_late_recovery(),
                build_no_action_never_recovers())
    for i, b in enumerate(builders):
        for r in b.records:
            r = dict(r)
            r["trial_id"] = f"t{i}"
            recs.append(r)
        for r in b.probes:
            r = dict(r)
            r["trial_id"] = f"t{i}"
            probes.append(r)
    out = R.reduce_run(R.RawRun(records=recs, probes=probes, sources=[]))
    assert out.summary["n_trials_in"] == out.summary["n_trials_out"] == 4
    assert len(out.trials) == 4
    for r in out.trials:
        assert r["disposition"] in DISPOSITIONS
        assert r["disposition_source"] in R.DISPOSITION_SOURCES
        assert r["window_containment"] in R.WINDOW_CONTAINMENTS
    # 2 chiqarildi (oyna), 2 kirdi (inside_hold + no_t_up).
    assert out.summary["window_containment"]["n_window_excluded"] == 2
    assert len(R.select_primary(out.trials)) == 2
    assert len(R.select_survival(out.trials)) == 4
    assert out.summary["vr_undetermined_in_binary_denominator"] == 0


# --- 17. §20 hukmi: maxrajga kirish ANIQLANGANLIK bilan belgilanadi ---------
#
# §20.2: "Binar `P(VR)` maxraji -- §4 ning predikati ANIQLANGAN qiymat
# (`true` yoki `false`) olgan trial'lar to'plami. `vr = None` -- sababi nima
# bo'lishidan qat'i nazar -- maxrajdan TASHQARIDA, va sabab nomlanib
# beriladi."
#
# §16.2(B) va §17.4 shundan KELIB CHIQADI: §4 VR ni EPIZOD uchun
# ta'riflaydi, demak epizod bo'lmasa predikat INSTANSIYALANMAYDI.


def build_r_ref_unavailable(trial_id="t0", *, arm="A", band="P0"):
    """Epizod BOR, lekin `R_ref` o'lchanmagan -> `vr=None`, 5-band baholanmadi.

    `progress` yozilmagan, demak throughput hisoblanmaydi. §20.4: savol
    TUG'ILDI (xizmat ishdan chiqdi), javob KUZATILMADI.
    """
    b = Builder(trial_id)
    b.add(R.RT_TRIAL_BEGIN, T0, arm=arm, pressure_band=band,
          fault_class="clean_crash")
    b.unit_state(T0, n_restarts=0, invocation="inv1", enter=T0, exit_=0)
    b.oom(T0, 0)
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
    return b


def test_no_episode_IKKALA_toplamdan_ham_chiqariladi():
    """§20.3: `no_episode` -- v1.5 dan beri IKKALA to'plamdan chiqqan BIRINCHI.

    `build_pure_brownout`: throughput 30% ga tushadi, LEKIN har probe
    contract'dan O'TADI => onset yo'q => epizod yo'q => §4 ning predikati
    INSTANSIYALANMAYDI (`t_up` ta'rifi `E` ga bog'liq, `E` esa yo'q).

    NEGA SURVIVAL'DAN HAM: §6.2 ning qoidasi "RECOVERY BO'LMAGAN
    trial'larni tashlash" haqida, ya'ni recovery KUTILAYOTGAN trial'lar
    haqida. Bu yerda xizmat ishdan chiqmagan, demak hodisa kutilayotgan
    EMAS edi; censored kuzatuv "hodisa `t` gacha sodir bo'lmadi" degan
    DA'VO va u hodisaning kutilayotgan bo'lishini talab qiladi -- demak
    censored kuzatuv chiqarish YOLG'ON da'vo bo'lardi. §6.2 bu holatga
    YETIB BORMAYDI (§20.3).
    """
    out = R.reduce_run(build_pure_brownout().run())
    p = out.trials[0]
    assert p["vr"] is None
    assert p["vr_reason"] == R.VR_REASON_NO_EPISODE
    assert p["n_episodes"] == 0
    # `vr_reason == "no_episode"` <=> epizod yo'q (ikki ifoda bir xil fakt).
    assert (p["vr_reason"] == R.VR_REASON_NO_EPISODE) is (p["n_episodes"] == 0)

    # IKKALA to'plamdan ham tashqarida:
    assert p["included_in_primary"] is False
    assert p["included_in_survival"] is False
    assert R.select_primary(out.trials) == []
    assert R.select_survival(out.trials) == []

    # Ikki sabab HAM nomlangan, va ikkisi ham `disposition` ni EMAS,
    # predikatning aniqlanmaganligini ko'rsatadi (§20.3).
    assert p["exclusion_reason"] == "vr_undetermined:no_episode"
    assert p["survival_exclusion_reason"] == "vr_undetermined:no_episode"
    # `disposition` o'zi hali ham `complete` -- §20.8 ochiq bo'shliq, va
    # aynan shu sababli sabab `disposition` dan OLINMAYDI.
    assert p["disposition"] == "complete"

    # Trial TASHLANMADI (4-qoida): record chiqishda bor.
    assert out.summary["n_trials_in"] == out.summary["n_trials_out"] == 1


def test_r_ref_unavailable_maxrajdan_chiqadi_LEKIN_survivalga_KIRADI():
    """§20.4: savol TUG'ILDI, 5-band baholanmadi -> maxrajdan tashqari, KM ga IN.

    §20.4(3): `no_episode` dan FARQLI, bu yerda hodisa KUTILAYOTGAN edi
    (xizmat ishdan chiqdi). `D_probe` ning OXIRI aniqlanmaydi, demak trial
    horizon'da CENSORED sifatida kiradi -- §6.2 ning qoidasi aynan shu
    holatga YETIB BORADI.
    """
    out = R.reduce_run(build_r_ref_unavailable().run())
    p = out.trials[0]
    assert p["r_ref"] is None
    assert p["vr"] is None
    assert p["vr_reason"] == R.VR_REASON_R_REF_UNAVAILABLE
    assert p["n_episodes"] == 1                  # epizod BOR -- savol tug'ildi
    assert "5" in p["unverified_clauses"]        # 5-band baholanmadi

    # Binar maxrajdan CHIQADI, sabab NOMLANGAN (§20.2).
    assert p["included_in_primary"] is False
    assert p["exclusion_reason"] == "vr_undetermined:r_ref_unavailable"
    assert R.select_primary(out.trials) == []

    # ... LEKIN KM/log-rank ga KIRADI, censored davomiylik sifatida (§20.4(3)).
    assert p["included_in_survival"] is True
    assert p["survival_exclusion_reason"] is None
    assert R.select_survival(out.trials) == [p]
    assert p["time_to_vr_censored"] is True
    assert p["d_probe_censored"] is True


def test_no_episode_va_r_ref_unavailable_FARQLI_ishlanadi():
    """§20.3 va §20.4 IKKI BOSHQA da'vo -- bir xil ishlanmasligi SHART.

    Ikkisi ham `vr=None` va ikkisi ham binar maxrajdan tashqarida, LEKIN
    survival to'plamida ular AJRALADI. Bu test aynan o'sha farqni qulflaydi,
    ya'ni kimdir ikkisini bitta qoidaga yig'sa test yiqiladi.
    """
    recs, probes = [], []
    for tid, b in (("t0", build_pure_brownout()),
                   ("t1", build_r_ref_unavailable("t1"))):
        for r in b.records:
            r = dict(r)
            r["trial_id"] = tid
            recs.append(r)
        for r in b.probes:
            r = dict(r)
            r["trial_id"] = tid
            probes.append(r)
    out = R.reduce_run(R.RawRun(records=recs, probes=probes, sources=[]))
    ne = next(r for r in out.trials
              if r["vr_reason"] == R.VR_REASON_NO_EPISODE)
    rr = next(r for r in out.trials
              if r["vr_reason"] == R.VR_REASON_R_REF_UNAVAILABLE)

    # Bir xil: ikkisi ham `vr=None`, ikkisi ham maxrajdan tashqarida.
    assert ne["vr"] is rr["vr"] is None
    assert ne["included_in_primary"] is rr["included_in_primary"] is False
    # FARQLI: survival to'plami ularni ajratadi (§20.3 vs §20.4(3)).
    assert ne["included_in_survival"] is False
    assert rr["included_in_survival"] is True
    assert R.select_survival(out.trials) == [rr]
    # Ikki survival sababi ham nomlangan va BIR XIL EMAS.
    assert ne["survival_exclusion_reason"] == "vr_undetermined:no_episode"
    assert rr["survival_exclusion_reason"] is None


def test_enters_survival_set_qoidasi_yagona_joyda():
    """§20.3: survival a'zoligi `enters_survival_set()` da, YAGONA joyda."""
    assert R.SURVIVAL_EXCLUDED_VR_REASONS == frozenset({"no_episode"})
    # `no_episode` -- YAGONA chekinish; qolgan `vr=None` sabablari KIRADI.
    assert R.enters_survival_set("complete", "no_episode") is False
    assert R.enters_survival_set("censored", "no_episode") is False
    for reason in ("verified", "invalidated", "no_up_probe",
                   R.VR_REASON_R_REF_UNAVAILABLE,
                   R.VR_REASON_THROUGHPUT_UNMEASURABLE,
                   R.VR_REASON_WINDOW_TRUNCATED, None):
        assert R.enters_survival_set("complete", reason) is True
        assert R.enters_survival_set("censored", reason) is True
    # §12: to'plamdan tashqaridagi disposition'lar kirmaydi (o'zgarmadi).
    for disp in ("contaminated", "aborted_guard", "washout_timeout",
                 "harness_error"):
        assert R.enters_survival_set(disp, "verified") is False


def test_KONYUNKSIYA_probe_gap_vr_true_bolsa_HAM_chiqariladi():
    """§20.2 + §4: ANIQLANGANLIK juftning O'RNINI BOSMAYDI.

    `probe_gap` trial'ining `vr` i `True` bo'lishi MUMKIN -- uzilish oynadan
    tashqarida bo'lsa predikat aniqlanadi. §4 esa u trial'ni shunda ham
    `censored`, NATIJA emas deb hukm qiladi: "Instrumentatsiya yo'qolishi
    hech qachon jimgina natijaga aylanmaydi."

    Demak faqat aniqlanganlikka tayanish §4 ni BUZARDI, va faqat juftga
    tayanish §20.2 ni buzardi -- ikkisi ham ZARUR.
    """
    drop = tuple(range(130, 141))
    out = R.reduce_run(build_restart_trial(FULL_STEP, drop=drop).run())
    p = out.trials[0]
    assert p["vr"] is True                       # predikat ANIQLANGAN
    assert p["disposition_source"] == "probe_gap"
    assert p["included_in_primary"] is False     # ... lekin §4 chiqaradi
    assert p["exclusion_reason"] == "censored:probe_gap"
    # Juft sababi USTUN -- `vr` aniqlangan, demak `vr_undetermined` emas.
    assert "vr_undetermined" not in p["exclusion_reason"]
    # Predikat darajasida ikki shartni ALOHIDA tekshirish:
    assert R.enters_primary_denominator("censored", "probe_gap",
                                        vr=True) is False      # juft yo'q
    assert R.enters_primary_denominator("complete", "derived",
                                        vr=None,
                                        vr_reason="no_episode") is False
    assert R.enters_primary_denominator("complete", "derived",
                                        vr=True) is True       # ikkisi ham bor
    assert R.enters_primary_denominator("complete", "derived",
                                        vr=False) is True      # `false` ANIQLANGAN


def test_vr_None_HAR_QANDAY_sabab_bilan_maxrajdan_chiqariladi():
    """§20.2: "sababi nima bo'lishidan qat'i nazar" -- fixture'lar bo'ylab.

    Har `vr=None` sababi uchun: maxrajdan tashqarida VA sabab NOMLANGAN.
    """
    builders = {
        R.VR_REASON_NO_EPISODE: build_pure_brownout(),
        R.VR_REASON_R_REF_UNAVAILABLE: build_r_ref_unavailable(),
        R.VR_REASON_WINDOW_TRUNCATED: build_late_recovery(),
    }
    seen = set()
    for want_reason, b in builders.items():
        out = R.reduce_run(b.run())
        p = out.trials[0]
        assert p["vr"] is None, want_reason
        assert p["vr_reason"] == want_reason
        assert p["included_in_primary"] is False, want_reason
        assert p["exclusion_reason"] is not None, want_reason
        # Sabab NOMLANGAN: yo juft sababi, yo `vr_undetermined:<reason>`.
        assert (want_reason in p["exclusion_reason"]
                or p["exclusion_reason"].startswith("censored:")), want_reason
        # §20.2 invarianti: maxrajda `vr=None` QOLMAYDI.
        assert out.summary["vr_undetermined_in_binary_denominator"] == 0
        assert out.summary["vr_undetermined_in_binary_denominator_by_reason"] == {}
        # Sabab BUTUN run bo'yicha hisobotda ko'rinadi (ma'lumot yo'qolmaydi).
        assert out.summary["vr_undetermined_counts_by_reason"] == {want_reason: 1}
        seen.add(want_reason)
    assert seen == set(builders)


def _two_orders(builder):
    """Bir xil trial ustida ESKI (oynasiz) va YANGI (oynali) yorliq + a'zolik."""
    trial = R.split_trials(builder.run())[0]
    prm = R.Params()
    gaps = R.probe_gaps(trial, prm)
    down = bool(trial.probes) and not trial.probes[-1].passed
    p = R.reduce_run(builder.run()).trials[0]
    old = R.derive_disposition(trial, gaps, down)[:2]
    window = R.classify_window_containment(
        p["t_up_us"], prm, hold_end_us=trial.hold_end_us,
        horizon_end_us=trial.horizon_end_us)
    new = R.derive_disposition(trial, gaps, down, window)[:2]
    kw = {"vr": p["vr"], "vr_reason": p["vr_reason"]}
    return p, old, new, (R.enters_primary_denominator(*old, **kw),
                         R.enters_primary_denominator(*new, **kw))


def test_20_2_tartibga_chidamlilik_FAQAT_vr_None_shoxida_amal_qiladi():
    """§20.2 maxrajni tartibga chidamli qiladi -- LEKIN FAQAT `vr=None` bo'lsa.

    §20.2 ning oqibati odatda shunday ta'riflanadi: "kesilgan oyna `vr` ni
    aniqlanmagan qoldiradi, demak trial qaysi yorliq olishidan qat'i nazar
    chiqariladi". Bu **ikki shoxdan faqat bittasida** to'g'ri, va bu test
    ikkisini ham o'lchaydi:

      (1) oyna horizon'dan chiqdi, oxirgi probe O'TDI
          -> `vr = None` (`window_truncated`)
          -> §20.2 ning aniqlanganlik sharti O'ZI chiqaradi
          -> a'zolik TARTIBGA CHIDAMLI, faqat SABAB farq qiladi;

      (2) oyna horizon'dan chiqdi, oxirgi probe BUZILDI
          -> oyna ichida monoton invalidator ishlaydi
          -> `vr = False` -- ANIQLANGAN, demak §20.2 uni CHIQARMAYDI
          -> trial'ni faqat §17.4 ning JUFT qoidasi chiqaradi
          -> a'zolik TARTIBGA CHIDAMLI **EMAS**.

    Demak `TARTIB QULFI` testi faqat beriladigan sabab uchun emas, (2)
    shoxida ENDPOINT A'ZOLIGI uchun ham yuk ko'taradi. U SAQLANADI.
    """
    # --- (1) `vr = None`: a'zolik chidamli, sabab esa yo'q ----------------
    p, old, new, (in_old, in_new) = _two_orders(build_late_recovery())
    assert p["vr"] is None
    assert p["vr_reason"] == R.VR_REASON_WINDOW_TRUNCATED
    assert in_old is in_new is False          # a'zolik CHIDAMLI
    kw = {"vr": p["vr"], "vr_reason": p["vr_reason"]}
    r_old = R.primary_exclusion_reason(*old, **kw)
    r_new = R.primary_exclusion_reason(*new, **kw)
    assert r_old != r_new                     # ... SABAB esa farq qiladi
    assert r_old == "vr_undetermined:window_truncated"
    assert r_new == "censored:window_past_horizon"
    # Eski yorliqda juft O'ZI ruxsat etardi -- chiqargan narsa §20.2.
    assert R.enters_primary_denominator(*old) is True

    # --- (2) `vr = False`: a'zolik tartibga CHIDAMLI EMAS -----------------
    p2, old2, new2, (in_old2, in_new2) = _two_orders(
        build_late_recovery(last_fails=True))
    assert p2["vr"] is False                  # ANIQLANGAN -> §20.2 chiqarmaydi
    assert p2["vr_reason"] == "invalidated"
    assert old2 == ("censored", "down_at_horizon")
    assert new2 == ("censored", "window_past_horizon")
    assert in_old2 is True                    # eski tartib: maxrajga KIRARDI
    assert in_new2 is False                   # yangi tartib: CHIQADI
    assert in_old2 is not in_new2             # TARTIB a'zolikni belgilaydi
    # Haqiqiy reduksiya yangi tartibni ishlatadi, demak trial chiqariladi.
    assert p2["included_in_primary"] is False
    assert p2["exclusion_reason"] == "censored:window_past_horizon"


# ===========================================================================
# §20.4(2) -- QAT'IY TAQIQ: VR 1-4 bandlar ustida HISOBLANMAYDI
# ===========================================================================


def test_vr_true_HECH_QACHON_5_bandsiz_chiqmaydi():
    """§20.4(2) + §4: 5-band baholanmasa `vr = True` CHIQMAYDI.

    §4: "5-band VR ni process-liveness'dan ajratadigan narsa ... Busiz
    butun hissa 'process tirikmi?' ga qulaydi."
    §9.2: "liveness-only VR ta'rifi ehtimol null pilot beradi, va bu null --
    TA'RIF ARTEFAKTI, H1 ga qarshi dalil EMAS."

    AUDIT NATIJASI (manfiy, lekin foydali): `evaluate_vr` ning HECH BIR
    yo'li 5-bandsiz `True` qaytarmaydi -- `True` ga yetish uchun `r_ref`
    ham, oyna throughput'i ham, to'liq oyna ham kerak. `False` esa 5-bandsiz
    chiqishi MUMKIN va bu TO'G'RI: §4 ning VR'i yettita bandning
    KONYUNKSIYASI, demak bitta konyunkt yolg'on bo'lsa natija yolg'on.
    Taqiq `True` ga tegishli, `False` ga emas.
    """
    builders = (build_restart_trial(FULL_STEP),          # vr=True
                build_restart_trial(60),                 # vr=False (brownout)
                build_never_recovers(),                  # vr=False (no_up_probe)
                build_no_action_never_recovers(),         # vr=False
                build_r_ref_unavailable(),               # vr=None
                build_pure_brownout(),                   # vr=None
                build_late_recovery(),                   # vr=None
                build_restart_trial(FULL_STEP, hidden_at=140),
                build_restart_trial(FULL_STEP, drop=tuple(range(130, 141))))
    n_true = 0
    for b in builders:
        payload, eps = reduce_one(b)
        for ep in eps:
            if ep.vr is True:
                n_true += 1
                # 5-band HAQIQATAN baholangan:
                assert ep.throughput is not None
                # `throughput_ratio` faqat `r_ref is not None and r_ref > 0`
                # bo'lganda hisoblanadi, demak u 5-bandning BAHOLANGANIGA
                # yetarli guvoh.
                assert ep.throughput_ratio is not None
                assert ep.window_complete is True
                assert "5" not in ep.unverified_clauses
                assert ep.throughput_status != "not_evaluated"
        if payload["vr"] is True:
            assert payload["vr_band5_evaluated"] is True
    assert n_true >= 1          # test bo'sh emas


def test_5_band_olchanmasa_vr_None_va_sabab_NOMLANGAN():
    """§20.4(1): `r_ref` yo'q -> `vr=None`, `True` ham `False` ham EMAS.

    `False` deb yozish ham xato bo'lardi: u kuzatilmagan narsani kuzatilgan
    muvaffaqiyatsizlik deb yozish bo'lardi (§20.4 ni `probe_gap` bilan bir
    sinfga qo'yadi -- savol tug'ildi, javob kuzatilmadi).
    """
    payload, eps = reduce_one(build_r_ref_unavailable())
    assert eps[0].vr is None
    assert eps[0].vr is not False
    assert eps[0].vr_reason == R.VR_REASON_R_REF_UNAVAILABLE
    assert "5" in eps[0].unverified_clauses
    assert payload["vr_band5_evaluated"] is False
    assert payload["fr_a"] is None               # `None` -> `False` AYLANMAYDI


# ===========================================================================
# §20.3 / §20.4(4) -- IKKI SINF, HECH QACHON POOL QILINMAYDI
# ===========================================================================


def test_injektor_samaradorligi_yacheyka_boyicha_va_pilotni_GATE_qiladi():
    """§20.3: `no_episode` darajasi INJEKTOR SAMARADORLIGI deb nomlanadi.

    §9.3 har trial'ga aynan bitta injeksiya beradi va P1 ning yagona
    fault'i `clean_crash`, u contract'ni buzishi SHART. Demak `no_episode`
    "injeksiya ISHLAMADI" degan ma'no beradi -- natija emas, TRIAL NUQSONI,
    va nolga teng bo'lmagan daraja PILOTNI GATE QILADI (§9.2 ning to'rtala
    mexanizmi injeksiyaning ishlashini nazarda tutadi).

    Fixture: A|P0 -> 1 to'g'ri trial; A|P2 -> 2 `no_episode`.
    Agregat 2/3, lekin `P2` da 2/2 = 1.0 -- to'planish KO'RINADI.
    """
    recs, probes = [], []
    spec = (("t0", build_restart_trial(FULL_STEP), "A", "P0"),
            ("t1", build_pure_brownout(), "A", "P2"),
            ("t2", build_pure_brownout(), "A", "P2"))
    for tid, b, arm, band in spec:
        for r in b.records:
            r = dict(r)
            r["trial_id"] = tid
            if r["record_type"] == R.RT_TRIAL_BEGIN:
                r["arm"], r["pressure_band"] = arm, band
            recs.append(r)
        for r in b.probes:
            r = dict(r)
            r["trial_id"] = tid
            probes.append(r)
    out = R.reduce_run(R.RawRun(records=recs, probes=probes, sources=[]))
    inj = out.summary["injector_effectiveness"]

    assert inj["metric"] == R.METRIC_INJECTOR_EFFECTIVENESS
    assert inj["rate_denominator"] == "all_trials_in_cell"
    assert inj["vr_reasons"] == ["no_episode"]
    assert inj["n_no_episode"] == 2
    assert inj["no_episode_rate"] == pytest.approx(2 / 3)
    assert inj["injection_effective_rate"] == pytest.approx(1 / 3)
    # §20.3: IKKALA to'plamdan ham chiqadi.
    assert set(inj["excluded_from"]) == {R.SET_BINARY_DENOMINATOR,
                                         R.SET_SURVIVAL}
    # PILOT GATE -- mashina o'qiydigan hukm.
    assert inj["gates_pilot"] is True
    assert out.summary["pilot_gated_by_injector_effectiveness"] is True
    assert out.summary["no_episode_rate_injector_effectiveness"] == pytest.approx(
        2 / 3)

    # Yacheyka bo'yicha: `P2` da to'planish ko'rinadi, agregat uni yashiradi.
    p0, p2 = inj["by_cell"]["A|P0"], inj["by_cell"]["A|P2"]
    assert (p0["n_no_episode"], p0["n_total"]) == (0, 1)
    assert p0["no_episode_rate"] == pytest.approx(0.0)
    assert p0["gates_pilot"] is False
    assert (p2["n_no_episode"], p2["n_total"]) == (2, 2)
    assert p2["no_episode_rate"] == pytest.approx(1.0)
    assert p2["gates_pilot"] is True
    assert p2["metric"] == R.METRIC_INJECTOR_EFFECTIVENESS
    assert p2["no_episode_rate"] != inj["no_episode_rate"]

    # Nol daraja -> gate YO'Q (flag haqiqatan darajaga bog'liq).
    clean = R.reduce_run(build_restart_trial(FULL_STEP).run())
    assert clean.summary["injector_effectiveness"]["no_episode_rate"] == (
        pytest.approx(0.0))
    assert clean.summary["pilot_gated_by_injector_effectiveness"] is False


def test_ikki_nuqson_sinfi_ALOHIDA_va_POOL_QILINMAYDI():
    """§20.3 / §20.4(4): injektor samaradorligi va instrumentatsiya yo'qolishi.

    Ular eksperimentning IKKI BOSHQA nuqson sinfi:
      * `no_episode`                -> injeksiya ishlamadi (trial nuqsoni)
      * `probe_gap` + 5-band yo'q   -> javob kuzatilmadi (instrumentatsiya)
    Bitta "eksklyuziya darajasi" ga qo'shib yuborish ma'lumotni YO'QOTADI,
    shuning uchun taqiq MASHINA O'QIYDIGAN shaklda qulflanadi.

    Fixture: 1 `no_episode` + 1 `probe_gap` + 1 `r_ref_unavailable` + 1 toza.
    """
    recs, probes = [], []
    spec = (("t0", build_restart_trial(FULL_STEP)),
            ("t1", build_pure_brownout()),
            ("t2", build_restart_trial(FULL_STEP,
                                       drop=tuple(range(130, 141)))),
            ("t3", build_r_ref_unavailable("t3")))
    for tid, b in spec:
        for r in b.records:
            r = dict(r)
            r["trial_id"] = tid
            recs.append(r)
        for r in b.probes:
            r = dict(r)
            r["trial_id"] = tid
            probes.append(r)
    out = R.reduce_run(R.RawRun(records=recs, probes=probes, sources=[]))
    inj = out.summary["injector_effectiveness"]
    il = out.summary["instrumentation_loss"]

    # Ikki sinf ALOHIDA maydonlarda, har biri O'Z nomi bilan.
    assert inj["metric"] != il["metric"]
    assert inj["metric"] == R.METRIC_INJECTOR_EFFECTIVENESS
    assert il["metric"] == R.METRIC_INSTRUMENTATION_LOSS

    # Sanoqlar: 1 `no_episode`; 1 `probe_gap` + 1 `r_ref_unavailable`.
    assert inj["n_no_episode"] == 1
    assert il["n_probe_gap"] == 1
    assert il["n_band5_unmeasured"] == 1
    assert il["n_instrumentation_loss"] == 2
    assert inj["no_episode_rate"] == pytest.approx(1 / 4)
    assert il["instrumentation_loss_rate"] == pytest.approx(2 / 4)

    # POOL QILISH TAQIQI -- izohda emas, maydonda.
    assert il["metric"] in inj["must_not_pool_with"]
    assert inj["metric"] in il["must_not_pool_with"]
    # Sinflar KESISHMAYDI: `no_episode` instrumentatsiya sinfida YO'Q.
    assert R.VR_REASON_NO_EPISODE not in il["vr_reasons"]
    assert R.VR_REASON_R_REF_UNAVAILABLE not in inj["vr_reasons"]

    # §20.4(3) farqi hisobotda ham ko'rinadi: instrumentatsiya yo'qolishi
    # survival'dan CHIQARILMAYDI, injektor nuqsoni esa CHIQARILADI.
    assert il["excluded_from"] == [R.SET_BINARY_DENOMINATOR]
    assert R.SET_SURVIVAL in inj["excluded_from"]

    # Maxraj: faqat toza trial (1/4).
    assert len(R.select_primary(out.trials)) == 1
    # Survival: toza + `probe_gap` + `r_ref_unavailable` = 3/4. `probe_gap`
    # trial'i §6.2 bo'yicha censored DAVOMIYLIK sifatida kiradi (manba bu
    # to'plamga ta'sir qilmaydi), `no_episode` esa YAGONA chiqqan (§20.3).
    assert len(R.select_survival(out.trials)) == 3
    assert out.summary["vr_undetermined_in_binary_denominator"] == 0
    assert out.summary["vr_undetermined_counts_by_reason"] == {
        "no_episode": 1, "r_ref_unavailable": 1,
    }
    # §20.2: `k/n` maxraji endi `vr=None` dan toza.
    assert out.summary["recovered_k_of_n"] == [1, 1]


def test_20_2_dan_keyin_maxrajda_vr_None_QOLMAYDI_invariant():
    """§20.2 TIRIK INVARIANTI: `vr_undetermined_in_binary_denominator == 0`.

    Barcha fixture'lar aralashmasi ustida. Bu son nolga teng bo'lmasa,
    §16.2(B) + §17.4 + §20.2 zanjirining biri buzilgan.
    """
    recs, probes = [], []
    spec = (build_restart_trial(FULL_STEP),
            build_restart_trial(60),
            build_never_recovers(),
            build_no_action_never_recovers(),
            build_pure_brownout(),
            build_r_ref_unavailable(),
            build_late_recovery(),
            build_restart_trial(FULL_STEP, drop=tuple(range(130, 141))))
    for i, b in enumerate(spec):
        for r in b.records:
            r = dict(r)
            r["trial_id"] = f"t{i}"
            recs.append(r)
        for r in b.probes:
            r = dict(r)
            r["trial_id"] = f"t{i}"
            probes.append(r)
    out = R.reduce_run(R.RawRun(records=recs, probes=probes, sources=[]))
    assert out.summary["n_trials_in"] == out.summary["n_trials_out"] == 8
    assert len(out.trials) == 8
    # Har maxraj a'zosining `vr` i ANIQLANGAN.
    for r in R.select_primary(out.trials):
        assert r["vr"] is not None
        assert isinstance(r["vr"], bool)
        assert r["exclusion_reason"] is None
    assert out.summary["vr_undetermined_in_binary_denominator"] == 0
    assert out.summary["vr_undetermined_in_binary_denominator_by_reason"] == {}
    # Har chiqarilgan trial'ning sababi NOMLANGAN (§12, §16.4, §20.2).
    inc = {id(r) for r in R.select_primary(out.trials)}
    for r in out.trials:
        if id(r) not in inc:
            assert r["exclusion_reason"]
    # `no_episode` -- IKKALA to'plamdan ham chiqqan YAGONA kategoriya.
    surv = {id(r) for r in R.select_survival(out.trials)}
    both_out = [r for r in out.trials
                if id(r) not in inc and id(r) not in surv
                and r["disposition"] in R.SURVIVAL_DISPOSITIONS]
    assert [r["vr_reason"] for r in both_out] == [R.VR_REASON_NO_EPISODE]
