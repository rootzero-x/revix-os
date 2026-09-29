"""schedule.py testlari -- eksperiment dizayni.

Bu modul sof mantiq, demak dizaynni EKSHAUSTIV sinash mumkin: yacheyka
balansi, seed takrorlanuvchanligi, disposition totalligi va washout holat
mashinasi hech qanday mashina holatiga bog'liq emas.

Bu testlarning maqsadi kod ishlashini ko'rsatish emas -- PREREGISTRATION.md
dagi dizayn ta'riflari kodda AYNAN bajarilganini ko'rsatish. Dizaynda
jimgina xato butun kampaniyani qiymatsiz qiladi.
"""
import itertools

import pytest

from revix.schedule import (
    DISPOSITION_RULES,
    EXCLUDED_DISPOSITIONS,
    FACT_FIELDS,
    P1_BLOCKS,
    P1_FACTORS,
    PRIMARY_ANALYSIS_DISPOSITIONS,
    T_Q_S,
    T_W_MAX_S,
    T_W_S,
    CampaignTooLong,
    Factor,
    PressureCapExceeded,
    ScheduleError,
    TrialFacts,
    TrialTimeline,
    WashoutMachine,
    WashoutObservation,
    WashoutPolicy,
    assign_disposition,
    enters_primary_analysis,
    estimate_campaign,
    explain_disposition,
    full_factorial,
    make_schedule,
    p1_schedule,
    washout_start,
    washout_step,
)
from revix.schema import DISPOSITIONS

# ===========================================================================
# 1. Randomized complete block design (§8.4, §9.3)
# ===========================================================================


def test_p1_dizayni_120_trial_beradi():
    """§9.3: 3 pressure × 2 arm × 20 blok = 120 trial."""
    sch = p1_schedule(seed=1)
    assert sch.cells_per_block == 6
    assert sch.n_blocks == P1_BLOCKS
    assert sch.n_trials == 120


def test_har_yacheyka_blokda_aynan_bir_marta():
    """"Complete block" ta'rifi: blok = har yacheykadan AYNAN BITTA trial."""
    sch = p1_schedule(seed=7, n_blocks=12)
    all_cells = set(sch.cells())
    for b in range(sch.n_blocks):
        block = sch.block(b)
        assert len(block) == sch.cells_per_block
        cells = [t.cell for t in block]
        assert len(set(cells)) == len(cells), f"blok {b} da takrorlangan yacheyka"
        assert set(cells) == all_cells, f"blok {b} to'liq emas"


def test_balans_n_blokda_yacheykaga_n_replika():
    """§8.4: `n` blok ⇒ yacheykaga aynan `n` replika. Balans buzilsa
    yacheyka proporsiyalari taqqoslanmaydigan bo'ladi."""
    for n in (1, 2, 5, 20, 37):
        sch = p1_schedule(seed=99, n_blocks=n)
        counts = sch.cell_counts()
        assert len(counts) == 6
        assert set(counts.values()) == {n}
        assert sch.n_trials == 6 * n


def test_blok_ichidagi_tartib_bloklar_boylab_farq_qiladi():
    """Randomizatsiya blok ICHIDA: tartib bloklar bo'ylab farq qiladi,
    lekin multiset aynan bir xil (aks holda blok to'liq bo'lmaydi)."""
    sch = p1_schedule(seed=2024, n_blocks=20)
    orders = [tuple(t.cell for t in sch.block(b)) for b in range(sch.n_blocks)]
    assert len(set(orders)) > 1, "hech bir blok aralashtirilmagan"
    multisets = {tuple(sorted(o)) for o in orders}
    assert len(multisets) == 1, "bloklarning multiset'i bir xil emas"


def test_bir_xil_seed_bayt_bayt_bir_xil_jadval():
    """§8.4: seed `run_meta` da saqlanadi, demak randomizatsiya AYNAN
    qayta tiklanishi kerak."""
    a = p1_schedule(seed=31337)
    b = p1_schedule(seed=31337)
    assert a.to_json() == b.to_json()
    assert a.digest() == b.digest()
    assert a.trials == b.trials


def test_boshqa_seed_boshqa_tartib():
    a = p1_schedule(seed=1)
    b = p1_schedule(seed=2)
    assert a.digest() != b.digest()
    assert [t.cell for t in a.trials] != [t.cell for t in b.trials]
    # Lekin dizayn o'zgarmaydi: balans va to'liqlik saqlanadi.
    assert a.cell_counts() == b.cell_counts()


def test_seed_va_rng_jadvalda_qayd_etiladi():
    """Takrorlanuvchanlik seed VA algoritm juftligiga bog'liq."""
    sch = p1_schedule(seed=555)
    d = sch.as_dict()
    assert d["seed"] == 555
    assert d["rng"] == "python-random-mt19937"
    assert d["schedule_version"] == 1
    assert d["n_trials"] == 120


def test_uch_faktorli_faktorial_dizayn():
    """§13: confirmatory eksperiment `fault_class` va
    `pressure_pulse_duration` qo'shadi -- dizayn n-o'lchovli bo'lishi kerak."""
    factors = (
        Factor("arm", ("A", "B", "no_action")),
        Factor("pressure_level", ("P0", "P1", "P2")),
        Factor("pressure_pulse_duration_s", (2, 6, 12)),
        Factor("fault_class", ("clean_crash", "leak_oom")),
    )
    sch = make_schedule(factors, n_blocks=3, seed=4)
    assert sch.cells_per_block == 3 * 3 * 3 * 2  # 54
    assert sch.n_trials == 54 * 3
    assert set(sch.cell_counts().values()) == {3}
    assert sch.factor_names == (
        "arm",
        "pressure_level",
        "pressure_pulse_duration_s",
        "fault_class",
    )
    # Har trial har faktordan bitta daraja oladi.
    t = sch.trials[0]
    assert set(t.levels_dict) == set(sch.factor_names)


def test_bitta_faktor_ham_ishlaydi():
    sch = make_schedule((Factor("arm", ("A", "no_action")),), n_blocks=4, seed=0)
    assert sch.cells_per_block == 2
    assert sch.n_trials == 8


def test_bloklarni_kengaytirish_prefiksni_ozgartirmaydi():
    """Har blok MUSTAQIL seed oladi, demak 20 -> 30 blokka uzaytirish
    birinchi 20 blokni o'zgartirmaydi va yig'ilgan ma'lumot yaroqli qoladi."""
    short = p1_schedule(seed=8, n_blocks=20)
    long = p1_schedule(seed=8, n_blocks=30)
    assert long.n_trials == 180
    assert long.trials[: short.n_trials] == short.trials


def test_trial_id_unikal_va_tartib_vaqt_tartibi():
    sch = p1_schedule(seed=11, n_blocks=20)
    ids = [t.trial_id for t in sch.trials]
    assert len(set(ids)) == len(ids)
    # Leksikografik tartib = bajarish tartibi (log'larni saralashda muhim).
    assert ids == sorted(ids)
    assert [(t.block_index, t.position_in_block) for t in sch.trials] == sorted(
        (t.block_index, t.position_in_block) for t in sch.trials
    )
    for b in range(sch.n_blocks):
        block = sch.block(b)
        assert [t.position_in_block for t in block] == list(range(len(block)))


def test_trial_as_dict_darajalarni_yozadi():
    sch = p1_schedule(seed=3, n_blocks=1)
    d = sch.trials[0].as_dict()
    assert set(d) == {"trial_id", "block_index", "position_in_block", "arm",
                      "pressure_level"}
    assert d["arm"] in ("A", "no_action")
    assert d["pressure_level"] in ("P0", "P1", "P2")


def test_full_factorial_deterministik():
    cells = full_factorial(P1_FACTORS)
    assert len(cells) == 6
    assert cells[0] == {"arm": "A", "pressure_level": "P0"}
    assert full_factorial(P1_FACTORS) == cells


@pytest.mark.parametrize(
    "factors,n_blocks,seed",
    [
        ((), 2, 1),                                             # faktor yo'q
        ((Factor("arm", ("A",)), Factor("arm", ("B",))), 2, 1),  # takroriy nom
        ((Factor("arm", ("A",)),), 0, 1),                       # blok yo'q
        ((Factor("arm", ("A",)),), -1, 1),
        ((Factor("arm", ("A",)),), 2, "seed"),                   # seed str
    ],
)
def test_yaroqsiz_dizayn_parametrlari_rad_etiladi(factors, n_blocks, seed):
    with pytest.raises(ScheduleError):
        make_schedule(factors, n_blocks, seed)


@pytest.mark.parametrize(
    "name,levels",
    [
        ("", ("A",)),              # bo'sh nom
        ("arm", ()),               # daraja yo'q
        ("arm", ("A", "A")),       # takroriy daraja
        ("arm", ({"a": 1},)),      # JSON'ga tushmaydi
    ],
)
def test_yaroqsiz_faktor_rad_etiladi(name, levels):
    with pytest.raises(ScheduleError):
        Factor(name, levels)


# ===========================================================================
# 2. Washout holat mashinasi (§8.4)
# ===========================================================================

BASE = 100 * 1024 * 1024  # slice memory.current baseline


def obs(elapsed_s, *, kill=True, mem=BASE, slice_rate=0.0, host_rate=0.0):
    return WashoutObservation(
        elapsed_s=elapsed_s,
        kill_issued=kill,
        memory_current=mem,
        slice_stall_rate=slice_rate,
        host_stall_rate=host_rate,
    )


def test_yaxshi_kuzatuvlarda_washout_complete_ga_yetadi():
    """§8.4 ketma-ketligi to'liq bajarilsa washout yakunlanadi."""
    m = WashoutMachine(BASE)
    assert m.state == "kill_subtree"
    for t in range(0, 15):
        p = m.observe(obs(float(t)))
        assert not p.done, f"t={t} da erta yakunlandi"
    p = m.observe(obs(15.0))
    assert p.done
    assert p.state == "complete"
    assert not p.timed_out


def test_kill_bolmasa_ilgarilamaydi():
    """§8.4 qadam 1: atomik subtree kill BIRINCHI."""
    m = WashoutMachine(BASE)
    for t in (0.0, 5.0, 10.0):
        p = m.observe(obs(t, kill=False))
        assert p.state == "kill_subtree"
        assert p.reason == "kill_pending"
    p = m.observe(obs(11.0))
    assert p.state == "quiescence"  # kill + memory bitta kuzatuvda o'tadi


def test_memory_baseline_ga_qaytmasa_kutadi():
    """§8.4 qadam 2: `memory.current` baseline ±ε ga qaytishi."""
    pol = WashoutPolicy(memory_epsilon_bytes=1024)
    m = WashoutMachine(BASE, pol)
    p = m.observe(obs(0.0, mem=BASE + 50 * 1024 * 1024))
    assert p.state == "memory_baseline"
    assert p.reason == "memory_above_baseline"
    p = m.observe(obs(1.0, mem=BASE + 512))  # ε ichida
    assert p.state == "quiescence"


def test_memory_oqilmasa_fail_closed():
    """O'qilmagan o'lchov "yaxshi" deb hisoblanmaydi (guard qoidasi 3)."""
    m = WashoutMachine(BASE)
    p = m.observe(obs(0.0, mem=None))
    assert p.state == "memory_baseline"
    assert p.reason == "memory_unreadable"


def test_tq_bitta_namuna_bilan_qanoatlanmaydi():
    """§8.4 qadam 3: `T_q = 5 s` DAVOMIDA past bo'lishi kerak.

    Bitta tinch namuna, hatto elapsed > T_q bo'lsa ham, quiescence'ni
    qanoatlantirmaydi -- aks holda oldingi trial'ning holati sizib o'tardi.
    """
    m = WashoutMachine(BASE)
    m.observe(obs(0.0, slice_rate=0.9, host_rate=0.9))  # shovqinli
    p = m.observe(obs(10.0))  # BITTA tinch namuna, elapsed 10 > T_q = 5
    assert p.state == "quiescence"
    assert p.quiet_for_s == 0.0
    assert p.reason == "quiescence_building"
    p = m.observe(obs(15.0))  # 5 s sustained -> pol ham bajarildi
    assert p.state == "complete"


def test_quiescence_uzilsa_oyna_noldan_boshlanadi():
    """`T_q` -- "5 s davomida", "jami 5 s" emas."""
    m = WashoutMachine(BASE)
    for t in (0.0, 1.0, 2.0, 3.0, 4.0):
        p = m.observe(obs(t))
        assert p.state == "quiescence"
    p = m.observe(obs(5.0, slice_rate=0.9))  # uzilish
    assert p.state == "quiescence"
    assert p.quiet_for_s == 0.0
    assert p.reason == "not_quiescent"
    for t in (6.0, 7.0, 8.0, 9.0, 10.0):
        p = m.observe(obs(t))
        assert p.state == "quiescence", f"t={t}: oyna qayta boshlanmadi"
    p = m.observe(obs(11.0))  # 6.0 dan 5 s
    assert p.state == "floor"


def test_host_tezligi_ham_hisobga_olinadi():
    """§8.4: slice VA host -- ikkisi ham chegaradan past bo'lishi kerak."""
    m = WashoutMachine(BASE)
    for t in range(0, 7):
        p = m.observe(obs(float(t), slice_rate=0.0, host_rate=0.9))
        assert p.state == "quiescence"
        assert p.reason == "not_quiescent"


def test_stall_tezligi_oqilmasa_fail_closed():
    m = WashoutMachine(BASE)
    for t in range(0, 7):
        p = m.observe(obs(float(t), slice_rate=None))
        assert p.state == "quiescence"
        assert p.reason == "not_quiescent"


def test_qattiq_pol_T_w_kutiladi():
    """§8.4 qadam 4: qattiq pol `T_w = 15 s`.

    Quiescence 5 s da bajarilsa ham, washout 15 s dan oldin yakunlanmaydi.
    """
    m = WashoutMachine(BASE)
    for t in range(0, 6):
        m.observe(obs(float(t)))
    assert m.state == "floor"  # T_q bajarildi
    for t in (6.0, 10.0, 14.9):
        p = m.observe(obs(t))
        assert p.state == "floor"
        assert p.reason == "floor_pending"
    assert m.observe(obs(T_W_S)).state == "complete"


def test_cap_da_washout_timeout():
    """§8.4: cap `T_w_max = 120 s` -> `washout_timeout` (§12)."""
    m = WashoutMachine(BASE)
    p = m.observe(obs(0.0, slice_rate=0.9))
    assert p.state == "quiescence"
    p = m.observe(obs(T_W_MAX_S - 0.1, slice_rate=0.9))
    assert not p.timed_out
    p = m.observe(obs(T_W_MAX_S, slice_rate=0.9))
    assert p.timed_out
    assert p.state == "washout_timeout"
    assert p.reason == "t_w_max"
    # Va bu disposition'ga aynan bir xil nom bilan tushadi.
    assert p.state in DISPOSITIONS


def test_cap_qanoatlangan_shartlardan_ham_ustun():
    """Cap shartsiz: `T_w_max` dan keyingi kuzatuv washout'ni yakunlay
    olmaydi, chunki cap'dan oshgan washout keyingi trial'ning baseline'i
    haqidagi taxminni allaqachon buzgan."""
    p = washout_start(BASE)
    p = washout_step(p, obs(0.0))
    p = washout_step(p, obs(6.0))
    assert p.state == "floor"
    p = washout_step(p, obs(T_W_MAX_S))  # hamma shart bajarilgan, lekin cap
    assert p.timed_out


def test_terminal_holat_idempotent():
    m = WashoutMachine(BASE)
    for t in range(0, 16):
        m.observe(obs(float(t)))
    assert m.done
    p = m.observe(obs(200.0, slice_rate=0.9))  # cap'dan oshgan, shovqinli
    assert p.state == "complete", "terminal holat o'zgardi"


def test_washout_step_progress_ni_ozgartirmaydi():
    """Sof funksiya: kirish holati o'zgarmaydi."""
    p0 = washout_start(BASE)
    p1 = washout_step(p0, obs(0.0))
    assert p0.state == "kill_subtree"
    assert p1 is not p0
    assert p1.state == "quiescence"


def test_yaroqsiz_washout_policy_rad_etiladi():
    with pytest.raises(ScheduleError):
        WashoutPolicy(t_q_s=20.0, t_w_s=15.0)       # T_q > T_w
    with pytest.raises(ScheduleError):
        WashoutPolicy(t_w_s=200.0, t_w_max_s=120.0)  # T_w > T_w_max
    with pytest.raises(ScheduleError):
        WashoutPolicy(quiescence_rate=0.0)
    with pytest.raises(ScheduleError):
        washout_start(-1)


def test_washout_default_parametrlari_muzlatilgan_qiymatlar():
    pol = WashoutPolicy()
    assert (pol.t_q_s, pol.t_w_s, pol.t_w_max_s) == (5.0, 15.0, 120.0)
    assert (T_Q_S, T_W_S, T_W_MAX_S) == (5.0, 15.0, 120.0)


# ===========================================================================
# 3. Disposition -- yopiq enum, total funksiya (§12)
# ===========================================================================


def all_fact_combinations():
    """Fakt fazasining TO'LIQ sanog'i: 8 bool -> 256 kombinatsiya."""
    for combo in itertools.product((False, True), repeat=len(FACT_FIELDS)):
        yield TrialFacts(**dict(zip(FACT_FIELDS, combo)))


def oracle(f):
    """Testning MUSTAQIL ustuvorlik ta'rifi.

    Ataylab qo'lda yozilgan: agar kod va bu oracle bir xil javob bersa,
    ustuvorlik tasodifan emas, ataylab shunday.
    """
    if f.harness_error:
        return "harness_error"
    if f.guard_fired:
        return "aborted_guard"
    if f.unsolicited_kill or f.foreign_oom_kill or f.bystander_lost_contract:
        return "contaminated"
    if f.washout_timed_out:
        return "washout_timeout"
    if f.probe_gap_exceeded or f.horizon_ended_down:
        return "censored"
    return "complete"


def test_disposition_total_butun_fakt_fazasi_boylab():
    """§12: har trial'ga AYNAN BITTA disposition.

    256 kombinatsiyaning HAMMASI yopiq enumdan bitta qiymat qaytaradi.
    Bu jimgina eksklyuziyani imkonsiz qiladigan mexanizm.
    """
    n = 0
    for facts in all_fact_combinations():
        d = assign_disposition(facts)
        assert d in DISPOSITIONS, f"yopiq enumdan tashqarida: {d}"
        assert d == oracle(facts), f"{facts.as_dict()} -> {d}"
        n += 1
    assert n == 2 ** len(FACT_FIELDS) == 256


def test_har_disposition_erishiladigan():
    """Yopiq enumning har bir a'zosi qandaydir fakt to'plamidan chiqadi.
    Erishilmaydigan disposition -- o'lik ta'rif."""
    seen = {assign_disposition(f) for f in all_fact_combinations()}
    assert seen == set(DISPOSITIONS)


def test_qoida_jadvali_yopiq_enum_bilan_mos():
    assert {d for _, _, d in DISPOSITION_RULES} == set(DISPOSITIONS)
    # Oxirgi qoida shartsiz -> "hech biri mos kelmadi" holati mavjud emas.
    assert DISPOSITION_RULES[-1][1](TrialFacts()) is True


def test_faktsiz_trial_complete():
    assert assign_disposition(TrialFacts()) == "complete"


def test_guard_abort_probe_uzilishidan_ustun():
    """Ustuvorlik: guard aralashuvi o'lchov natijasidan ustun -- guard
    trip qilgandan keyingi har qanday o'lchov artefakt."""
    f = TrialFacts(guard_fired=True, probe_gap_exceeded=True)
    assert assign_disposition(f) == "aborted_guard"
    v = explain_disposition(f)
    assert v.rule == "guard_fired"
    assert "probe_gap_exceeded" in v.matched_rules  # sabab yo'qolmaydi


def test_harness_error_hammadan_ustun():
    f = TrialFacts(**{name: True for name in FACT_FIELDS})
    assert assign_disposition(f) == "harness_error"
    assert len(explain_disposition(f).matched_rules) == len(DISPOSITION_RULES)


def test_kontaminatsiya_censoring_dan_ustun():
    """§6.2: censored trial analizga KIRADI. Demak eksklyuziya sababi
    censoring'dan ustun bo'lishi SHART -- aks holda chiqarilishi kerak
    bo'lgan trial "censored" yorlig'i ostida analizga kirib ketardi."""
    f = TrialFacts(foreign_oom_kill=True, probe_gap_exceeded=True)
    assert assign_disposition(f) == "contaminated"
    assert not enters_primary_analysis("contaminated")
    assert enters_primary_analysis("censored")


def test_washout_timeout_censoring_dan_ustun():
    f = TrialFacts(washout_timed_out=True, horizon_ended_down=True)
    assert assign_disposition(f) == "washout_timeout"


@pytest.mark.parametrize("field", ["probe_gap_exceeded", "horizon_ended_down"])
def test_censored_ikki_yoli(field):
    """§6.2 va §12: probe uzilishi >2×P, yoki horizon down holatda tugadi."""
    assert assign_disposition(TrialFacts(**{field: True})) == "censored"


@pytest.mark.parametrize(
    "field", ["unsolicited_kill", "foreign_oom_kill", "bystander_lost_contract"]
)
def test_kontaminatsiyaning_uch_manbasi(field):
    f = TrialFacts(**{field: True})
    assert assign_disposition(f) == "contaminated"
    assert f.contaminated


def test_birlamchi_analiz_toplami():
    """§12: `contaminated` va `aborted_guard` chiqariladi; §6.2: `censored`
    kiradi."""
    assert set(PRIMARY_ANALYSIS_DISPOSITIONS) == {"complete", "censored"}
    assert set(EXCLUDED_DISPOSITIONS) == {
        "contaminated",
        "aborted_guard",
        "washout_timeout",
        "harness_error",
    }
    assert set(PRIMARY_ANALYSIS_DISPOSITIONS) | set(EXCLUDED_DISPOSITIONS) == set(
        DISPOSITIONS
    )


def test_enum_tashqarisidagi_disposition_rad_etiladi():
    with pytest.raises(ScheduleError):
        enters_primary_analysis("failed")  # §4: "failed" disposition YO'Q


# ===========================================================================
# 4. Trial jadvali (§9.4)
# ===========================================================================


def test_p1_jadvali_default_qiymatlari():
    """§9.4: pre-flight -> R_ref 10 s -> ramp 5 s -> hold, injeksiya +3 s."""
    tl = TrialTimeline()
    assert tl.baseline_s == 10.0
    assert tl.ramp_s == 5.0
    assert tl.hold_s == 12.0
    assert tl.injection_offset_s == 3.0
    assert tl.w_stab_s == 8.0
    assert tl.t_ramp_start == tl.preflight_s + 10.0
    assert tl.t_hold_start == tl.t_ramp_start + 5.0
    assert tl.t_inject == tl.t_hold_start + 3.0
    assert tl.t_pressure_off == tl.t_hold_start + 12.0
    assert tl.t_washout_start == tl.t_pressure_off
    assert tl.sustained_pressure_on_s == 12.0
    assert tl.pressure_on_s == 17.0  # generator yoniq (ramp + hold)
    assert tl.total_s == tl.t_pressure_off + tl.washout_s


def test_fazalar_boshliqsiz_va_tartibli():
    tl = TrialTimeline()
    ph = tl.phases()
    assert [p[0] for p in ph] == [
        "preflight",
        "baseline_r_ref",
        "ramp",
        "hold",
        "washout",
    ]
    assert ph[0][1] == 0.0
    for a, b in zip(ph, ph[1:]):
        assert a[2] == b[1], "fazalar orasida bo'shliq yoki ustma-ustlik"
    assert ph[-1][2] == tl.total_s


def test_w_stab_oynasi_pressure_ichiga_sigadi():
    """§4: `W_stab_pilot = 8 s` oomd xavfsizlik oynasi ichida sig'ishi kerak."""
    tl = TrialTimeline()
    assert tl.t_verify_end_earliest <= tl.t_pressure_off


def test_uzun_hold_pressure_cap_ni_buzadi():
    """XAVFSIZLIK: sustained pressure-on <= 12 s. Bu qattiq cheklov --
    oomd 20 s sustained'da foydalanuvchi ilovalarini o'ldiradi."""
    with pytest.raises(PressureCapExceeded):
        TrialTimeline(hold_s=12.5)
    with pytest.raises(PressureCapExceeded):
        TrialTimeline(hold_s=20.0)
    # Cap'ni oshirib yuborish ham boshqa invariantga urinadi (guard oynasi).
    with pytest.raises(PressureCapExceeded):
        TrialTimeline(hold_s=20.0, hold_cap_s=25.0)


def test_uzun_ramp_qismi_guard_oynasini_buzadi():
    """hold + chegaradan yuqori ramp <= guard sustain oynasi (15 s), aks
    holda to'g'ri trial ham `aborted_guard` bo'lardi."""
    with pytest.raises(PressureCapExceeded):
        TrialTimeline(hold_s=12.0, ramp_above_threshold_s=4.0)
    # 12 + 3 = 15 -- aynan chegarada, qabul qilinadi.
    assert TrialTimeline(hold_s=12.0, ramp_above_threshold_s=3.0).hold_s == 12.0


def test_ramp_above_threshold_ramp_dan_katta_bolmaydi():
    with pytest.raises(ScheduleError):
        TrialTimeline(ramp_s=2.0, ramp_above_threshold_s=3.0)


def test_w_stab_sigmasa_rad_etiladi():
    """§4: injeksiya + W_stab hold ichiga sig'ishi kerak."""
    with pytest.raises(ScheduleError):
        TrialTimeline(injection_offset_s=6.0)          # 6 + 8 > 12
    with pytest.raises(ScheduleError):
        TrialTimeline(w_stab_s=10.0)                   # 3 + 10 > 12
    with pytest.raises(ScheduleError):
        TrialTimeline(hold_s=8.0, ramp_above_threshold_s=0.0)  # 3 + 8 > 8


def test_washout_poli_va_cap_tekshiriladi():
    """§8.4: qattiq pol `T_w = 15 s`, cap `T_w_max = 120 s`."""
    with pytest.raises(ScheduleError):
        TrialTimeline(washout_s=14.0)
    with pytest.raises(ScheduleError):
        TrialTimeline(washout_s=121.0)
    assert TrialTimeline(washout_s=T_W_S).washout_s == 15.0


@pytest.mark.parametrize(
    "kw",
    [
        {"baseline_s": 0.0},
        {"ramp_s": -1.0},
        {"hold_s": 0.0},
        {"w_stab_s": 0.0},
        {"preflight_s": -1.0},
        {"injection_offset_s": -1.0},
    ],
)
def test_manfiy_yoki_nol_davomiylik_rad_etiladi(kw):
    with pytest.raises(ScheduleError):
        TrialTimeline(**kw)


def test_jadval_as_dict_serializatsiya_qilinadi():
    d = TrialTimeline().as_dict()
    assert d["hold_s"] == 12.0
    assert d["sustained_pressure_on_s"] == 12.0
    assert d["total_s"] == 52.0


# ===========================================================================
# 5. Kampaniya bahosi (§9.4)
# ===========================================================================


def test_kampaniya_bahosi_p1():
    """§9.4: 120 trial. Default fazalar yig'indisi 52 s/trial."""
    sch = p1_schedule(seed=1)
    tl = TrialTimeline()
    est = estimate_campaign(sch, tl)
    assert est.n_trials == 120
    assert est.n_blocks == 20
    assert est.per_trial_s == 52.0
    assert est.total_s == pytest.approx(6240.0)
    assert est.total_hours == pytest.approx(6240.0 / 3600.0)
    assert est.sustained_pressure_on_total_s == pytest.approx(120 * 12.0)
    assert est.pressure_on_total_s == pytest.approx(120 * 17.0)


def test_qoshimcha_vaqt_oshkora_beriladi():
    """§9.4 ≈75 s/trial deydi; farq band-band yozilmagan, demak baho
    jimgina to'ldirilmaydi -- chaqiruvchi oshkora beradi."""
    sch = p1_schedule(seed=1)
    est = estimate_campaign(sch, TrialTimeline(), per_trial_overhead_s=23.0)
    assert est.per_trial_s == 75.0
    assert est.total_hours == pytest.approx(75.0 * 120 / 3600.0)
    assert est.total_hours == pytest.approx(2.5)


def test_eng_yomon_holat_T_w_max_bilan_hisoblanadi():
    sch = p1_schedule(seed=1)
    tl = TrialTimeline()
    est = estimate_campaign(sch, tl)
    assert est.worst_case_total_s == pytest.approx(
        (tl.t_washout_start + T_W_MAX_S) * 120
    )
    assert est.worst_case_hours > est.total_hours


def test_juda_uzun_kampaniya_ishga_tushishdan_oldin_tutiladi():
    """Tasodifiy 40 soatlik kampaniya OLDIN tutilishi kerak, keyin emas."""
    big = p1_schedule(seed=1, n_blocks=500)   # 3000 trial
    with pytest.raises(CampaignTooLong):
        estimate_campaign(big, TrialTimeline(), max_hours=4.0)
    # P1 esa chegaradan o'tadi.
    est = estimate_campaign(p1_schedule(seed=1), TrialTimeline(), max_hours=4.0)
    assert est.total_hours < 4.0


def test_kampaniya_bahosi_default_jadval_bilan():
    est = estimate_campaign(p1_schedule(seed=1))
    assert est.per_trial_s == TrialTimeline().total_s
    assert est.as_dict()["n_trials"] == 120


def test_manfiy_qoshimcha_vaqt_rad_etiladi():
    with pytest.raises(ScheduleError):
        estimate_campaign(p1_schedule(seed=1), per_trial_overhead_s=-1.0)
