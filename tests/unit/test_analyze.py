"""analyze.py testlari -- SHARTNOMA MAJBURIYATLARINING regressiya qulflari.

Bu testlar hech qanday eksperiment ishga tushirmaydi va HECH QANDAY HAQIQIY
MA'LUMOTGA tayanmaydi: REVIX da hali birorta run bo'lmagan. Shuning uchun
barcha fixture'lar QO'LDA QURILGAN va ATAYLAB SINTETIK (`SYNTH-` prefiksli
`trial_id`, yumaloq mikrosekund qiymatlari). Ulardagi birorta son natija
sifatida o'qilmasligi kerak.

Testlar nimani himoya qiladi:
  * `docs/architecture/04-driver-va-analiz-shartnomasi.md` §2.2 -- `analysis.json`
    sxemasi;
  * shu faylning §2.3 dagi SAKKIZTA analiz majburiyati -- har biri uchun
    alohida qulf, nomida majburiyat raqami bor;
  * `PREREGISTRATION.md` §11 -- falsifikatsiya qoidasining AYNAN chegaralari.

`revix/stats.py` o'z estimatorlarini NASHR ETILGAN misollarga qarshi
tekshiradi. Bu fayl ularni qayta tekshirmaydi; u `analyze.py` ning O'Z
hisoblarini -- yacheyka sonlari, `k/n` satrlari, eksklyuziya darajasi,
falsifikatsiya qarori va kvantil marshruti -- QO'LDA HISOBLANGAN javoblarga
qarshi tekshiradi. Har bir kutilgan qiymat o'z docstring'ida hisoblab
ko'rsatilgan: test "o'zini o'zi tasdiqlaydigan" bo'lmasligi kerak.
"""
import json
import math

import pytest

from revix import analyze as A
from revix import stats as S

# Kichik `n_boot` -- test tezligi uchun. Bu CI ning KENGLIGIGA ta'sir qiladi,
# lekin bu testlar CI qiymatini emas, MARSHRUTNI va bayroqlarni tekshiradi.
N_BOOT_TEST = 299

SEC = 1_000_000          # 1 s mikrosekundda (§1 vaqt disiplinasi)

# Shartnoma §5.4 (`driver-contract/v1.1`): T_trial = 32.0 + 8.0 + 0.1 = 40.1 s.
# Bu yerda u DRIVER hisoblagan qiymat sifatida fixture'ga beriladi -- analiz
# uni qayta hisoblamaydi.
T_TRIAL_US = 40_100_000


# --- fixture quruvchilar ---------------------------------------------------


def run_meta(**over):
    """Sintetik `run_meta.json` (§1.1 ning analizga tegishli qismi)."""
    meta = {
        "run_id": "SYNTH-run",
        "session_id": "SYNTH-sess",
        "boot_id": "SYNTH-boot",
        "preregistration_sha256": "SYNTHETIC-NOT-A-REAL-DIGEST",
        "preregistration_version": "preregistration/v1.3",
        "t_trial_us": T_TRIAL_US,
        "t_trial_formula": "t_pressure_off + w_stab_s + P = 32.0 + 8.0 + 0.1",
    }
    meta.update(over)
    return meta


def trial(trial_id, *, arm="A", pressure_band="P0", disposition="complete",
          vr=True, fr_a=False, n_episodes=1, n_actions=1,
          time_to_vr_us=2 * SEC, time_to_vr_censored=False,
          d_sd_us=1 * SEC, d_sd_censored=False,
          d_probe_us=2 * SEC, d_probe_censored=False,
          d_eff_us=3.0 * SEC, fr_b=None, **over):
    """Bitta `trial_metrics` record'i -- AYNAN `reduce.reduce_trial` field
    nomlari bilan (envelope `reduce.write_output` qo'shadigan shaklda).

    Bu yerda sanab o'tilgan field nomlari `analyze.py` ISTE'MOL QILADIGAN
    to'plam: ular `reduce.py` ning chiqishi bilan bitta joyda taqqoslanadi.
    """
    rec = {
        # envelope (`schema.Emitter.envelope`)
        "schema_version": 1,
        "record_type": "trial_metrics",
        "stream": "trial_metrics",
        "run_id": "SYNTH-run",
        "session_id": "SYNTH-sess",
        "boot_id": "SYNTH-boot",
        "trial_id": trial_id,
        "block_index": 0,
        "seq": 1,
        "mono_us": 0,
        "real_us": 0,
        "emitter": "reduce:1",
        # payload (`reduce.reduce_trial`)
        "derived": True,
        "arm": arm,
        "pressure_band": pressure_band,
        "disposition": disposition,
        "disposition_conflict": False,
        "has_trial_begin": True,
        "has_trial_end": True,
        "exclusion_reason": None if disposition == "complete" else disposition,
        "vr": vr,
        "fr_a": fr_a,
        "fr_b": fr_b if fr_b is not None else {
            "computed": False, "value": None,
            "reason": "not_computed: no Repairs() matrix", "detail": {}},
        "n_episodes": n_episodes,
        "n_actions": n_actions,
        "time_to_vr_us": time_to_vr_us,
        "time_to_vr_censored": time_to_vr_censored,
        "d_sd_us": d_sd_us,
        "d_sd_censored": d_sd_censored,
        "d_probe_us": d_probe_us,
        "d_probe_censored": d_probe_censored,
        "d_eff_us": d_eff_us,
    }
    rec.update(over)
    return rec


def cells_to_trials(counts, *, arm="A", disposition="complete"):
    """`{"P0": (k, n), ...}` -> trial ro'yxati. `k` ta `vr=True`, qolgani
    `vr=False`. Faqat yacheyka sonlari muhim bo'lgan testlar uchun."""
    out = []
    i = 0
    for lvl, (k, n) in counts.items():
        for j in range(n):
            out.append(trial(f"SYNTH-{lvl}-{i}", arm=arm, pressure_band=lvl,
                             disposition=disposition, vr=(j < k)))
            i += 1
    return out


def sweep_cell(trial_id, w_stab_s, theta, *, vr=True, vr_reason="verified",
               disposition="complete"):
    return {
        "schema_version": 1, "record_type": "sweep_cell", "stream": "sweep_cell",
        "run_id": "SYNTH-run", "session_id": "SYNTH-sess",
        "boot_id": "SYNTH-boot", "trial_id": trial_id, "block_index": 0,
        "seq": 1, "mono_us": 0, "real_us": 0, "emitter": "reduce:1",
        "derived": True,
        "w_stab_us": int(w_stab_s * SEC), "w_stab_s": float(w_stab_s),
        "theta": float(theta), "vr": vr, "vr_reason": vr_reason,
        "disposition": disposition,
    }


def full_sweep(trial_id, *, truncated_from_s=None):
    """Oldindan e'lon qilingan TO'LIQ grid (5 x 3 = 15) bitta trial uchun.

    `truncated_from_s` berilsa, shu `W_stab` dan boshlab yacheykalar
    `reduce.py` ning kesilgan-oyna natijasini (`vr=None`,
    `vr_reason="window_truncated"`) oladi.
    """
    out = []
    for w in A.W_STAB_SWEEP_S:
        for th in A.THETA_SWEEP:
            trunc = truncated_from_s is not None and w >= truncated_from_s
            out.append(sweep_cell(
                trial_id, w, th,
                vr=(None if trunc else True),
                vr_reason=("window_truncated" if trunc else "verified")))
    return out


def build(trials, *, sweep=None, meta=None, n_boot=N_BOOT_TEST):
    return A.build_analysis(trials, meta or run_meta(), sweep,
                            n_boot=n_boot, generated_mono_us=123456)


def warn_codes(obj):
    return {w["code"] for w in obj["warnings"]}


# --- 1. §2.2 sxemasi -------------------------------------------------------


def test_analysis_json_sxemasi_shartnomada_korsatilgan_kalitlarga_ega():
    """§2.2 ning HAR BIR kaliti va ichma-ichligi mavjud va turi to'g'ri."""
    obj = build(cells_to_trials({"P0": (18, 20), "P1": (14, 20),
                                 "P2": (8, 20)}))
    for key in ("schema_version", "analysis_version", "preregistration_sha256",
                "generated_mono_us", "n_trials", "primary", "survival",
                "false_recovery", "downtime", "sensitivity", "multiplicity",
                "exclusions", "warnings", "time_unit", "t_trial_us"):
        assert key in obj, key

    assert obj["analysis_version"] == "p1/v1"
    assert obj["time_unit"] == "us"           # §1 vaqt disiplinasi
    assert isinstance(obj["generated_mono_us"], int)
    assert set(obj["n_trials"]) >= {"total", "by_disposition"}
    assert obj["n_trials"]["total"] == 60

    p = obj["primary"]
    assert p["endpoint"] == "P(VR) trend across pressure levels"
    assert p["test"] == "cochran_armitage_trend"
    assert p["direction"] in ("decreasing", "increasing", "none")
    assert p["falsification_rule"] == "trend p>0.05 AND newcombe_upper<0.15"
    assert isinstance(p["cells"], list) and len(p["cells"]) == 3
    for c in p["cells"]:
        assert set(c) == {"level", "k", "n", "p_hat", "ci_lower", "ci_upper",
                          "ci_method"}
        assert c["ci_method"] == "clopper_pearson"
    assert set(p["risk_difference"]) == {"estimate", "ci_lower", "ci_upper",
                                         "ci_method", "contrast"}
    assert p["risk_difference"]["ci_method"] == "newcombe"
    # §11 mezoni AYNAN `P(VR|P0) - P(VR|P2)` haqida.
    assert p["risk_difference"]["contrast"] == "P0-P2"
    assert p["ci_level"] == pytest.approx(0.95)

    s = obj["survival"]
    assert set(s) >= {"km", "logrank", "rmst", "proportional_hazards_checked",
                      "censoring"}
    assert set(s["logrank"]) == {"chi2", "p_value", "observed", "expected"}
    assert set(s["rmst"]) >= {"tau", "by_arm", "difference"}
    # §11 `tau = 8 s`, lekin §1 bo'yicha MIKROSEKUNDDA.
    assert s["rmst"]["tau"] == 8_000_000.0
    assert set(s["censoring"]) >= {"n_censored", "n_undetermined",
                                   "recovered_within_horizon"}
    for arm_curve in s["km"]["by_arm"].values():
        assert set(arm_curve) >= {"times", "survival", "at_risk",
                                  "greenwood_var"}

    fr = obj["false_recovery"]
    assert set(fr["fr_a"]) >= {"per_action", "per_episode", "n_undetermined"}
    assert set(fr["fr_b"]) >= {"computed", "reason"}

    assert set(obj["downtime"]) == {"d_sd", "d_probe", "d_eff"}
    assert set(obj["sensitivity"]) >= {"w_stab", "theta", "grid"}
    assert obj["sensitivity"]["w_stab"] == [8.0, 10.0, 30.0, 60.0, 120.0]
    assert obj["sensitivity"]["theta"] == [0.5, 0.8, 0.95]
    assert set(obj["multiplicity"]) >= {"method", "family", "adjusted"}
    assert obj["multiplicity"]["method"] == "holm_bonferroni"
    assert set(obj["exclusions"]) >= {"rate", "by_reason"}
    assert isinstance(obj["warnings"], list)


def test_yacheykada_p_hat_aynan_k_n_ga_teng():
    """`p_hat != k/n` bo'lgan yacheyka figurada BAYROQLANADI (tuzatilmaydi),
    shuning uchun u strukturaviy jihatdan imkonsiz bo'lishi kerak."""
    obj = build(cells_to_trials({"P0": (17, 20), "P1": (13, 19),
                                 "P2": (7, 18)}))
    for c in obj["primary"]["cells"]:
        assert c["p_hat"] == pytest.approx(c["k"] / c["n"])
    assert [c["k"] for c in obj["primary"]["cells"]] == [17, 13, 7]
    assert [c["n"] for c in obj["primary"]["cells"]] == [20, 19, 18]


def test_barcha_vaqt_qiymatlari_mikrosekundda():
    """§1: birlik bitta va OSHKORA. `tau` ham mikrosekundda.

    QO'LDA HISOB. Fixture'da `time_to_vr_us = 2_000_000` (2 s). KM event
    vaqti shu qiymatda bo'lishi kerak -- 2.0 (sekund) EMAS.
    """
    obj = build([trial("SYNTH-1", time_to_vr_us=2 * SEC)])
    assert obj["time_unit"] == "us"
    assert obj["survival"]["km"]["by_arm"]["A"]["times"] == [2_000_000.0]
    assert obj["survival"]["rmst"]["tau"] == 8_000_000.0
    assert obj["downtime"]["d_probe"]["unit"] == "us"


def _assert_all_finite(node, path="$"):
    """Daraxtdagi har bir `float` chekli bo'lishi kerak (`None` ruxsat)."""
    if isinstance(node, dict):
        for k, v in node.items():
            _assert_all_finite(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _assert_all_finite(v, f"{path}[{i}]")
    elif isinstance(node, float):
        assert math.isfinite(node), path


def test_chiqish_haqiqiy_json_nan_yetib_bormaydi():
    """`NaN` JSON'da YAROQSIZ va soxta aniqlik berardi -- `null` beriladi.

    `n = 1`/daraja -- ATAYLAB degenerativ kirish: bootstrap BCa u yerda
    aniqlanmaydi va `stats.py` `nan` qaytarishi mumkin. Shunda ham chiqishda
    `NaN` BO'LMAYDI.
    """
    obj = build(cells_to_trials({"P0": (1, 1), "P1": (0, 1), "P2": (0, 1)}))
    blob = json.dumps(obj, allow_nan=False)      # NaN bo'lsa ValueError
    _assert_all_finite(json.loads(blob))


# --- 2. Majburiyat #1: `t-test` / `mean ± SD` CHIQMAYDI --------------------


def test_majburiyat_1_taqiqlangan_statistika_chiqishda_yoq():
    """§10.2 `t-test` va `mean ± SD` ni TAQIQLAYDI (§2.3 #1)."""
    obj = build(cells_to_trials({"P0": (18, 20), "P1": (14, 20),
                                 "P2": (8, 20)}),
                sweep=full_sweep("SYNTH-P0-0"))
    blob = json.dumps(obj, ensure_ascii=False).lower()
    for token in A.FORBIDDEN_TOKENS:
        assert token not in blob, token


def test_majburiyat_1_taqiqlangan_satr_kirsa_yozishdan_oldin_rad_etiladi():
    """Qulf STRUKTURAVIY: testga emas, `_assert_no_forbidden` ga tayanadi."""
    obj = build(cells_to_trials({"P0": (1, 2), "P1": (1, 2), "P2": (0, 2)}))
    obj["warnings"].append({"code": "x", "where": "y",
                            "message": "reported as mean ± SD"})
    with pytest.raises(A.AnalysisError, match="TAQIQLANGAN"):
        A._assert_no_forbidden(obj)


# --- 3. Majburiyat #2: HR/Cox faqat PH tekshirilgan bo'lsa -----------------


def test_majburiyat_2_proportional_hazards_tekshirilmagan_demak_hr_yoq():
    """§10.2: "Schoenfeld residual'lari tekshirilmasa, HR berilmaydi."

    P1 da `stats.py` da PH testi YO'Q (ataylab), demak
    `proportional_hazards_checked` HAR DOIM `false` va chiqishda hazard
    ratio / Cox izi UMUMAN bo'lmaydi.
    """
    obj = build(cells_to_trials({"P0": (18, 20), "P1": (14, 20),
                                 "P2": (8, 20)}))
    assert obj["survival"]["proportional_hazards_checked"] is False
    blob = json.dumps(obj, ensure_ascii=False).lower()
    for token in A.HAZARD_TOKENS:
        assert token not in blob, token


def test_majburiyat_2_hr_qoshilsa_yozishdan_oldin_rad_etiladi():
    obj = build(cells_to_trials({"P0": (1, 2), "P1": (1, 2), "P2": (0, 2)}))
    obj["survival"]["hazard_ratio"] = {"estimate": 1.0}
    with pytest.raises(A.AnalysisError, match="hazard"):
        A._assert_no_forbidden(obj)


# --- 4. Majburiyat #3: censored trial KM/log-rank ga KIRADI ----------------


def test_majburiyat_3_censored_trial_km_ga_kiradi_tashlanmaydi():
    """§6.2: censored trial'larni tashlash KLASSIK YASHIRIN BIAS.

    QO'LDA HISOB. Arm `A` da 4 trial: time-to-VR = 1, 2, 3, 4 s; to'rtinchisi
    CENSORED (`disposition=censored`, `time_to_vr_censored=True`).
    KM event vaqtlari = {1, 2, 3} s. `at_risk` = 4, 3, 2 -- ya'ni censored
    kuzatuv birinchi uchta nuqtada ham RISK OSTIDA sanaladi. Agar u
    tashlangan bo'lsa `at_risk` = 3, 2, 1 bo'lardi.
    """
    trials = [
        trial("SYNTH-a1", time_to_vr_us=1 * SEC),
        trial("SYNTH-a2", time_to_vr_us=2 * SEC),
        trial("SYNTH-a3", time_to_vr_us=3 * SEC),
        trial("SYNTH-a4", time_to_vr_us=4 * SEC, disposition="censored",
              vr=None, time_to_vr_censored=True),
    ]
    obj = build(trials)
    km = obj["survival"]["km"]["by_arm"]["A"]
    assert km["n_total"] == 4            # censored KIRDI
    assert km["n_censored"] == 1
    # §1: MIKROSEKUNDDA (`time_unit`).
    assert km["times"] == [1.0 * SEC, 2.0 * SEC, 3.0 * SEC]
    assert km["at_risk"] == [4, 3, 2]    # tashlangan bo'lsa [3, 2, 1] bo'lardi
    # `vr=None` -- ALOHIDA kategoriya, "recovered emas" ga qo'shilmaydi.
    assert obj["survival"]["censoring"]["n_undetermined"] == 1
    assert obj["survival"]["censoring"]["n_censored"] == 1


def test_majburiyat_3_censored_trial_logrank_ga_ham_kiradi():
    """Log-rank ikki arm ustida ishlaydi va censored kuzatuv `n` ni oshiradi.

    QO'LDA HISOB. Har arm'da 3 trial. `no_action` arm'ining uchinchisi
    censored. Log-rank ning kutilgan hodisalari YIG'INDISI kuzatilganlarga
    teng bo'lishi kerak: `O_a + O_b == E_a + E_b` (Mantel-Haenszel
    identiteti). Bu identitet censored kuzatuv `at_risk` ga kirgani uchun
    saqlanadi.
    """
    trials = [
        trial("SYNTH-a1", arm="A", time_to_vr_us=1 * SEC),
        trial("SYNTH-a2", arm="A", time_to_vr_us=2 * SEC),
        trial("SYNTH-a3", arm="A", time_to_vr_us=3 * SEC),
        trial("SYNTH-n1", arm="no_action", time_to_vr_us=4 * SEC),
        trial("SYNTH-n2", arm="no_action", time_to_vr_us=5 * SEC),
        trial("SYNTH-n3", arm="no_action", time_to_vr_us=6 * SEC,
              disposition="censored", vr=None, time_to_vr_censored=True),
    ]
    obj = build(trials)
    lr = obj["survival"]["logrank"]
    assert set(lr["observed"]) == {"A", "no_action"}
    o = lr["observed"]["A"] + lr["observed"]["no_action"]
    e = lr["expected"]["A"] + lr["expected"]["no_action"]
    assert o == pytest.approx(e)
    assert o == pytest.approx(5.0)       # 6 kuzatuv, 1 censored => 5 event
    assert obj["survival"]["km"]["by_arm"]["no_action"]["n_censored"] == 1
    # `censored` disposition birlamchi analizdan chiqadi, survival'ga KIRADI.
    assert obj["exclusions"]["by_reason"] == {"censored": 1}
    assert obj["survival"]["censoring"]["n_censored"] == 1


# --- 5. Majburiyat #4: har jadval `k/n` bilan birga ------------------------


def test_majburiyat_4_har_jadval_recovered_within_horizon_bilan_birga():
    """§6.2 / §2.3 #4: har jadvalda "`T_trial` ichida recovered: k/n".

    QO'LDA HISOB. 6 `complete` trial, ulardan 4 tasi `vr=True` =>
    birlamchi jadval uchun `4/6`. Survival jadvaliga shu 6 trial kiradi
    (censored yo'q) => `4/6`. Downtime jadvallari ham birlamchi
    to'plamdan => `4/6`.
    """
    trials = ([trial(f"SYNTH-t{i}", vr=True) for i in range(4)]
              + [trial(f"SYNTH-f{i}", vr=False) for i in range(2)])
    obj = build(trials, sweep=full_sweep("SYNTH-t0"))
    assert obj["primary"]["recovered_within_horizon"] == "4/6"
    assert obj["survival"]["censoring"]["recovered_within_horizon"] == "4/6"
    for name in ("d_sd", "d_probe", "d_eff"):
        assert obj["downtime"][name]["recovered_within_horizon"] == "4/6"
    assert "recovered_within_horizon" in obj["sensitivity"]


def test_majburiyat_4_vr_none_recovered_sifatida_hisoblanmaydi():
    """`vr=None` -- aniqlanmagan, demak `k` ga KIRMAYDI."""
    trials = [trial("SYNTH-1", vr=True), trial("SYNTH-2", vr=None),
              trial("SYNTH-3", vr=False)]
    obj = build(trials)
    # Birlamchi yacheyka denominatoridan ham chiqadi: o'lchangani 2 ta.
    assert obj["primary"]["recovered_within_horizon"] == "1/2"
    assert obj["primary"]["cells"][0]["k"] == 1
    assert obj["primary"]["cells"][0]["n"] == 2
    assert "vr_undetermined" in warn_codes(obj)


# --- 6. Majburiyat #5: eksklyuziya darajasi NATIJA sifatida ----------------


def test_majburiyat_5_eksklyuziya_darajasi_sababga_kora_natija_sifatida():
    """§12: yuqori eksklyuziya darajasi O'ZI natija -- yashirilmaydi.

    QO'LDA HISOB. 10 trial: 6 `complete`, 2 `contaminated`,
    1 `aborted_guard`, 1 `censored`. Birlamchi analizga faqat `complete`
    kiradi (§12), demak eksklyuziya darajasi = 4/10 = 0.4.
    """
    trials = ([trial(f"SYNTH-c{i}") for i in range(6)]
              + [trial(f"SYNTH-x{i}", disposition="contaminated", vr=None)
                 for i in range(2)]
              + [trial("SYNTH-g", disposition="aborted_guard", vr=False)]
              + [trial("SYNTH-s", disposition="censored", vr=None,
                       time_to_vr_censored=True)])
    obj = build(trials)
    ex = obj["exclusions"]
    assert ex["rate"] == pytest.approx(0.4)
    assert ex["by_reason"] == {"contaminated": 2, "aborted_guard": 1,
                               "censored": 1}
    assert ex["n_total"] == 10 and ex["n_excluded"] == 4 and ex["n_primary"] == 6
    # §12 yopiq enum TO'LIQ beriladi -- nol ham ko'rinadi, yashirilmaydi.
    bd = obj["n_trials"]["by_disposition"]
    assert bd["complete"] == 6 and bd["contaminated"] == 2
    assert bd["aborted_guard"] == 1 and bd["censored"] == 1
    assert bd["washout_timeout"] == 0 and bd["harness_error"] == 0


# --- 7. Majburiyat #6: hisoblab bo'lmagan narsa `warnings` ga --------------


def test_majburiyat_6_trend_hisoblanmasa_warnings_ga_tushadi_taxmin_qilinmaydi():
    """§2.3 #6: hisoblab bo'lmagan narsa `warnings` ga, TAXMIN QILINMAYDI.

    `P2` darajasida o'lchangan trial yo'q => Cochran-Armitage uchta
    darajani talab qiladi, demak trend HISOBLANMAYDI. `p_value` `None`
    bo'ladi (0.0 EMAS), va §11 mezoni BAHOLANMAYDI (`falsified = None`,
    `False` EMAS -- `False` "falsifikatsiya qilinmadi" degan o'lchanmagan
    da'vo bo'lardi).
    """
    obj = build(cells_to_trials({"P0": (5, 10), "P1": (4, 10)}))
    p = obj["primary"]
    assert p["p_value"] is None
    assert p["statistic"] is None
    assert p["direction"] is None
    assert p["falsified"] is None
    assert p["falsified"] is not False
    assert {"trend_not_computable", "level_empty",
            "falsification_not_evaluable"} <= warn_codes(obj)
    # Multiplicity ham taxmin qilmaydi.
    assert obj["multiplicity"]["adjusted"] == [None]
    assert "multiplicity_not_computable" in warn_codes(obj)


def test_majburiyat_6_olchanmagan_downtime_nol_deb_olinmaydi():
    """`d_sd_us=None` -- o'lchanmagan. Nol deb olinsa median siljirdi."""
    trials = [trial("SYNTH-1", d_sd_us=None),
              trial("SYNTH-2", d_sd_us=4 * SEC),
              trial("SYNTH-3", d_sd_us=6 * SEC)]
    obj = build(trials)
    assert obj["downtime"]["d_sd"]["n"] == 2
    assert obj["downtime"]["d_sd"]["n_missing"] == 1
    assert "downtime_missing" in warn_codes(obj)


def test_majburiyat_6_fr_a_per_action_yechilmasa_none_va_warning():
    """FR-A per-action `episodes.jsonl` da; `n_actions != 1` bo'lsa
    `trial_metrics` dan AYNAN yechilmaydi => denominatorga kirmaydi."""
    trials = [trial("SYNTH-1", n_episodes=1, n_actions=3, fr_a=True),
              trial("SYNTH-2", n_episodes=1, n_actions=3, fr_a=False)]
    obj = build(trials)
    fa = obj["false_recovery"]["fr_a"]
    assert fa["per_action"] is None
    assert fa["per_episode"] == pytest.approx(0.5)   # 1/2 epizod darajasida
    assert fa["basis"]["n_resolvable_per_action"] == 0
    assert fa["basis"]["n_resolvable_per_episode"] == 2
    assert {"fr_a_per_action_unresolvable",
            "fr_a_per_action_not_computable"} <= warn_codes(obj)


def test_majburiyat_6_fr_a_none_false_ga_aylanmaydi():
    """`fr_a=None` -- aniqlanmagan; `n_undetermined` da sanaladi."""
    trials = [trial("SYNTH-1", fr_a=True), trial("SYNTH-2", fr_a=None),
              trial("SYNTH-3", fr_a=False)]
    fa = build(trials)["false_recovery"]["fr_a"]
    assert fa["n_undetermined"] == 1
    assert fa["per_episode"] == pytest.approx(0.5)   # 1 / 2 o'lchangan
    assert fa["basis"]["n_resolvable_per_episode"] == 2


# --- 8. Majburiyat #7: `W_stab > horizon` yacheykasi `note` bilan ----------


def test_majburiyat_7_w_stab_horizondan_katta_yacheyka_note_bilan_belgilanadi():
    """§2.3 #7: `reduce.py` u yerda `vr=None` (`window_truncated`) qaytaradi.

    QO'LDA HISOB. Sintetik sweep: `W_stab >= 30 s` yacheykalari kesilgan.
    Grid 5 x 3 = 15 yacheyka. `W_stab in {8, 10}` -> `note is None`;
    `W_stab in {30, 60, 120}` -> `note` da "W_stab > horizon" bor va
    denominator NOL (kesilgan yacheyka `n` ga kirmaydi).
    """
    t = trial("SYNTH-1")
    obj = build([t], sweep=full_sweep("SYNTH-1", truncated_from_s=30))
    grid = {(c["w_stab"], c["theta"]): c for c in obj["sensitivity"]["grid"]}
    assert len(grid) == 15
    for th in (0.5, 0.8, 0.95):
        for w in (8.0, 10.0):
            assert grid[(w, th)]["note"] is None
            assert grid[(w, th)]["p_vr_by_level"]["P0"] == {
                "k": 1, "n": 1, "p_hat": 1.0, "n_undetermined": 0}
        for w in (30.0, 60.0, 120.0):
            note = grid[(w, th)]["note"]
            assert note is not None and "window_truncated" in note, (w, th)
            cell = grid[(w, th)]["p_vr_by_level"]["P0"]
            assert cell == {"k": 0, "n": 0, "p_hat": None,
                            "n_undetermined": 1}
        # 60 va 120 `T_trial = 40.1 s` dan ham katta => STRUKTURAVIY note ham.
        for w in (60.0, 120.0):
            assert "W_stab > T_trial" in grid[(w, th)]["note"]


def test_majburiyat_7_w_stab_t_trial_dan_katta_bolsa_note_STRUKTURAVIY():
    """`note` ma'lumotga BOG'LIQ EMAS: horizon `run_meta` dan keladi.

    QO'LDA HISOB. `T_trial = 40.1 s` (shartnoma §5.4). Oldindan e'lon
    qilingan grid'da `W_stab in {8, 10, 30}` horizon'dan KICHIK,
    `{60, 120}` esa KATTA. Shuning uchun 60 va 120 yacheykalari `vr`
    qiymatidan QAT'I NAZAR `note` oladi -- aks holda figura `W_stab > T_trial`
    ni belgilanmagan deb BAYROQLARDI.
    """
    t = trial("SYNTH-1")
    # Barcha yacheyka `vr=True` -- ya'ni `window_truncated` SIGNALI YO'Q.
    obj = build([t], sweep=full_sweep("SYNTH-1"))
    grid = {(c["w_stab"], c["theta"]): c for c in obj["sensitivity"]["grid"]}
    for th in (0.5, 0.8, 0.95):
        for w in (8.0, 10.0, 30.0):
            assert grid[(w, th)]["note"] is None, (w, th)
        for w in (60.0, 120.0):
            note = grid[(w, th)]["note"]
            assert note is not None and "W_stab > T_trial" in note, (w, th)
            assert str(T_TRIAL_US) in note


def test_majburiyat_7_t_trial_yoq_bolsa_strukturaviy_tekshiruv_taxmin_qilmaydi():
    meta = run_meta()
    del meta["t_trial_us"]
    obj = build([trial("SYNTH-1")], sweep=full_sweep("SYNTH-1"), meta=meta)
    assert "sweep_horizon_unknown" in warn_codes(obj)
    grid = {(c["w_stab"], c["theta"]): c for c in obj["sensitivity"]["grid"]}
    # Horizon noma'lum => STRUKTURAVIY note qo'yilmaydi (taxmin yo'q).
    assert grid[(120.0, 0.8)]["note"] is None


def test_majburiyat_7_sweep_berilmasa_grid_taxmin_qilinmaydi():
    obj = build([trial("SYNTH-1")], sweep=None)
    assert obj["sensitivity"]["grid"] == []
    assert obj["sensitivity"]["w_stab"] == [8.0, 10.0, 30.0, 60.0, 120.0]
    assert "sweep_absent" in warn_codes(obj)


def test_sweep_toliq_bolmasa_warning_beriladi():
    obj = build([trial("SYNTH-1")],
                sweep=[sweep_cell("SYNTH-1", 8, 0.8)])
    assert "sweep_incomplete" in warn_codes(obj)


# --- 9. Majburiyat #8: KM kvantili `nan` -> BCa (censored bo'lmagan qism) --


def test_majburiyat_8_km_p90_nan_bolsa_bca_bootstrap_ga_qaytadi():
    """§2.3 #8 -- `stats.km_quantile` ning HUJJATLASHTIRILGAN cheklovi.

    QO'LDA HISOB. `d_probe` = 1, 2, 3, 4, 5 s; OXIRGISI censored.
    KM event vaqtlari = {1, 2, 3, 4} s:
        t=1: n=5, d=1 -> S=0.8
        t=2: n=4, d=1 -> S=0.6
        t=3: n=3, d=1 -> S=0.4
        t=4: n=2, d=1 -> S=0.2
    `median`: S <= 0.5 bo'ladigan eng kichik vaqt -> 3 s = 3_000_000 us.
    `p90`: S <= 0.1 ga EGRI CHIZIQ TUSHMAYDI (min S = 0.2) -> `nan` ->
    §2.3 #8 bo'yicha censored BO'LMAGAN qism {1, 2, 3, 4} ustida BCa.
    `np.quantile([1,2,3,4], 0.9)` chiziqli interpolyatsiya:
    0.9*(4-1) = 2.7 -> 3 + 0.7*(4-3) = 3.7 s = 3_700_000 us.
    """
    vals = [1, 2, 3, 4, 5]
    trials = [trial(f"SYNTH-{i}", d_probe_us=v * SEC,
                    d_probe_censored=(v == 5))
              for i, v in enumerate(vals)]
    d = build(trials)["downtime"]["d_probe"]
    assert d["n"] == 5 and d["n_censored"] == 1

    assert d["median"]["estimate"] == pytest.approx(3 * SEC)
    assert d["median"]["source"] == "kaplan_meier"

    for q in ("p90", "p99"):
        assert d[q]["source"] == "bca_bootstrap_uncensored"
        assert d[q]["note"] is not None and "km_quantile" in d[q]["note"]
    assert d["p90"]["estimate"] == pytest.approx(3.7 * SEC)
    assert d["p99"]["estimate"] == pytest.approx(3.97 * SEC)
    assert "km_quantile_nan" in warn_codes(build(trials))


def test_majburiyat_8_censored_yoq_bolsa_fallback_ham_yoq():
    """Censoring bo'lmasa KM `nan` bermaydi, demak fallback ishlamaydi.

    QO'LDA HISOB. `d_probe` = 1, 2, 3 s, hammasi event.
        t=1: n=3,d=1 -> S=2/3;  t=2: n=2,d=1 -> S=1/3;  t=3: n=1,d=1 -> S=0
    median: S <= 0.5 -> 2 s. p90/p99: S <= 0.1 -> 3 s.
    """
    trials = [trial(f"SYNTH-{i}", d_probe_us=v * SEC)
              for i, v in enumerate((1, 2, 3))]
    d = build(trials)["downtime"]["d_probe"]
    assert d["n_censored"] == 0
    assert d["median"]["estimate"] == pytest.approx(2 * SEC)
    assert d["p90"]["estimate"] == pytest.approx(3 * SEC)
    assert d["p99"]["estimate"] == pytest.approx(3 * SEC)
    for q in ("median", "p90", "p99"):
        assert d[q]["source"] == "kaplan_meier"
        assert d[q]["ci_basis"] == "full_sample"
    assert "km_quantile_nan" not in warn_codes(build(trials))


def test_majburiyat_8_km_kvantili_survival_blokida_ham_fallback_qiladi():
    """KM time-to-VR p90 ham `nan` bo'lishi mumkin -- u ham AYTILADI."""
    trials = [trial("SYNTH-1", time_to_vr_us=1 * SEC),
              trial("SYNTH-2", time_to_vr_us=2 * SEC, disposition="censored",
                    vr=None, time_to_vr_censored=True)]
    obj = build(trials)
    q = obj["survival"]["km"]["by_arm"]["A"]["quantiles"]
    # Event bitta (t=1 s), S = 0 -> median = 1 s, p90/p99 ham 1 s (S=0 <= 0.1).
    assert q["median"]["estimate"] == pytest.approx(1 * SEC)
    assert q["median"]["source"] == "kaplan_meier"
    assert q["median"]["ci_lower"] is None   # censoring-aware CI stats.py da yo'q


# --- 10. FR-B: P1 da BERILMAYDI, AYNAN shu sabab bilan ---------------------


def test_fr_b_hisoblanmaydi_va_sabab_shartnomada_korsatilgan_aynan_satr():
    """§2.2 AYNAN `"no calibration matrix (P1)"` ni talab qiladi (§5)."""
    obj = build(cells_to_trials({"P0": (1, 2), "P1": (1, 2), "P2": (0, 2)}))
    fr_b = obj["false_recovery"]["fr_b"]
    assert fr_b["computed"] is False
    assert fr_b["computed"] is not None       # soxta `None` emas, aniq `False`
    assert fr_b["reason"] == "no calibration matrix (P1)"
    assert "value" not in fr_b                # soxta nol BERILMAYDI


def test_kirishda_hisoblangan_fr_b_bolsa_analiz_rad_etiladi():
    """§5: P1 da `Repairs()` YO'Q. Kirishda FR-B bo'lsa -- versiya ziddiyati."""
    t = trial("SYNTH-1", fr_b={"computed": True, "value": False,
                               "reason": "computed", "detail": {}})
    with pytest.raises(A.AnalysisError, match="FR-B"):
        build([t])


# --- 11. §11 falsifikatsiya qoidasi ---------------------------------------


def test_birlamchi_test_cochran_armitage_qolda_hisoblangan_z_bilan():
    """§10.1 BIRLAMCHI test -- qo'lda hisoblangan statistika.

    QO'LDA HISOB. k = 20, 10, 0; n = 20, 20, 20; score = 0, 1, 2.
        N = 60, K = 30, p = 0.5
        T   = 0*(20-10) + 1*(10-10) + 2*(0-10) = -20
        Sxx = (20*0 + 20*1 + 20*4) - (20*0+20*1+20*2)^2/60
            = 100 - 3600/60 = 100 - 60 = 40
        Var = 0.5*0.5*40 = 10
        z   = -20/sqrt(10) = -6.32456,  chi2 = z^2 = 40.0
    `z < 0` => proporsiya score bilan KAMAYADI => `direction = "decreasing"`.
    """
    obj = build(cells_to_trials({"P0": (20, 20), "P1": (10, 20),
                                 "P2": (0, 20)}))
    p = obj["primary"]
    assert p["statistic"] == pytest.approx(-20.0 / math.sqrt(10.0), rel=1e-12)
    assert p["statistic"] == pytest.approx(-6.3245553, rel=1e-6)
    assert p["p_value"] < 1e-6
    assert p["direction"] == "decreasing"
    # Trend AHAMIYATLI => §11 ning birinchi bandi bajarilmaydi.
    assert p["falsified"] is False


def test_falsifikatsiya_trend_null_va_tor_ci_bolsa_ISHLAYDI():
    """§11: trend `p > 0.05` VA Newcombe yuqori chegarasi `< 0.15`.

    QO'LDA HISOB. Uchala darajada 190/200 (p = 0.95), demak trend AYNAN
    yassi: T = 0 => z = 0 => p = 1.0 > 0.05 ✓.
    Newcombe (190/200 vs 190/200): difference = 0. Wilson(190/200, 95%),
    z = 1.9599639845, z^2 = 3.8414588207:
        z^2/n   = 0.0192072941,  1 + z^2/n = 1.0192072941
        markaz  = 0.95 + z^2/2n = 0.95 + 0.0096036471 = 0.9596036471
        ildiz   = 0.95*0.05/200 + z^2/(4*200^2)
                = 0.0002375000 + 0.0000240091 = 0.0002615091
        yarim   = z*sqrt(0.0002615091) = 0.0316950549
        lower   = 0.9279085922/1.0192072941 = 0.9104218519
        upper   = 0.9912987020/1.0192072941 = 0.9726173544
    upper_diff = hypot(0.95 - 0.9104218519, 0.9726173544 - 0.95)
               = hypot(0.0395781481, 0.0226173544) = 0.0455848059 < 0.15 ✓
    => `falsified is True`.

    `n = 200`/daraja ATAYLAB P1 ning `n = 20` idan katta: §11 ning halol
    power bayonoti aynan shuni aytadi -- `n = 20` da 15 punktli effekt
    INKOR QILINMAYDI (keyingi test).
    """
    obj = build(cells_to_trials({"P0": (190, 200), "P1": (190, 200),
                                 "P2": (190, 200)}))
    p = obj["primary"]
    assert p["p_value"] == pytest.approx(1.0)
    assert p["direction"] == "none"          # `stats` "flat" -> §2.2 "none"
    assert p["risk_difference"]["estimate"] == pytest.approx(0.0)
    assert p["risk_difference"]["ci_upper"] == pytest.approx(0.0455848059,
                                                             abs=1e-9)
    assert p["falsified"] is True


def test_falsifikatsiya_n_20_da_yassi_trend_ham_H1_ni_yolgonga_chiqarmaydi():
    """§11 ning HALOL POWER BAYONOTI -- oldindan qabul qilingan o'qish.

    QO'LDA HISOB. Uchala darajada 18/20 (p = 0.9), trend yassi => p = 1.0.
    Wilson(18/20, 95%), z = 1.9599639845, z^2 = 3.8414588207:
        z^2/n   = 0.1920729410,  1 + z^2/n = 1.1920729410
        markaz  = 0.9 + z^2/40 = 0.9 + 0.0960364705 = 0.9960364705
        ildiz   = 0.9*0.1/20 + z^2/1600
                = 0.0045000000 + 0.0024009118 = 0.0069009118
        yarim   = z*sqrt(0.0069009118) = 0.1628175923
        lower   = 0.8332188782/1.1920729410 = 0.6989663548
        upper   = 1.1588540628/1.1920729410 = 0.9721335188
    upper_diff = hypot(0.9 - 0.6989663548, 0.9721335188 - 0.9)
               = hypot(0.2010336452, 0.0721335188) = 0.2135831713  >= 0.15
    => `falsified is False`: null pilot FAQAT KATTA effektni inkor qiladi
    (§11), va bu natijadan keyin qayta talqin qilinmaydi.

    Yacheyka CI'si ham tekshiriladi: Clopper-Pearson 95% (18/20) =
    (0.6830, 0.9877) -- nashr etilgan exact binomial interval. Bu
    `analyze.py` ning `k` va `n` ni TO'G'RI TARTIBDA uzatganini qulflaydi
    (almashtirilsa interval butunlay boshqa bo'lardi).
    """
    obj = build(cells_to_trials({"P0": (18, 20), "P1": (18, 20),
                                 "P2": (18, 20)}))
    p = obj["primary"]
    assert p["p_value"] == pytest.approx(1.0)
    assert p["risk_difference"]["ci_upper"] == pytest.approx(0.2135831713,
                                                             abs=1e-9)
    assert p["falsified"] is False
    c0 = p["cells"][0]
    assert c0["ci_lower"] == pytest.approx(0.6830, abs=5e-5)
    assert c0["ci_upper"] == pytest.approx(0.9877, abs=5e-5)


class _FakeTrend:
    def __init__(self, p):
        self.statistic, self.chi2, self.p_value = 0.0, 0.0, p
        self.direction = "flat"


class _FakeRd:
    def __init__(self, upper):
        self.difference, self.lower, self.upper = 0.0, -upper, upper
        self.p1 = self.p2 = 0.5


def _falsified_with(monkeypatch, p, upper):
    """§11 qarorini AYNAN chegarada sinash uchun ikki estimator almashtiriladi.

    NEGA ALMASHTIRILADI: `p == 0.05` yoki `upper == 0.15` ni beradigan
    butun son `k/n` juftligi yo'q, lekin §11 ikki QAT'IY tengsizlikni
    muzlatgan. Chegarani sinamasdan `>=` / `>` xatosi testdan o'tib ketardi.
    """
    monkeypatch.setattr(A.S, "cochran_armitage_trend",
                        lambda *a, **k: _FakeTrend(p))
    monkeypatch.setattr(A.S, "newcombe_diff_ci",
                        lambda *a, **k: _FakeRd(upper))
    trials = cells_to_trials({"P0": (1, 2), "P1": (1, 2), "P2": (0, 2)})
    return A.primary_section(trials, A.WarningLog())["falsified"]


@pytest.mark.parametrize("p,upper,expected", [
    (0.0500001, 0.1499999, True),    # ikkisi ham shartni bajaradi
    (0.0499999, 0.1499999, False),   # p chegaradan PAST  -> trend ahamiyatli
    (0.0500000, 0.1499999, False),   # p AYNAN 0.05        -> `>` qat'iy
    (0.0500001, 0.1500001, False),   # upper chegaradan YUQORI
    (0.0500001, 0.1500000, False),   # upper AYNAN 0.15    -> `<` qat'iy
    (0.0499999, 0.1500001, False),   # ikkisi ham bajarilmaydi
])
def test_falsifikatsiya_chegara_holatlari_qatiy_tengsizlik(monkeypatch, p,
                                                           upper, expected):
    """§11: "p > 0.05" VA "yuqori chegara < 0.15" -- IKKISI HAM QAT'IY."""
    assert _falsified_with(monkeypatch, p, upper) is expected


def test_falsifikatsiya_qoidasi_satri_aynan_shartnomadagidek():
    assert A.FALSIFICATION_RULE == "trend p>0.05 AND newcombe_upper<0.15"
    assert A.TREND_P_THRESHOLD == 0.05
    assert A.NEWCOMBE_UPPER_THRESHOLD == 0.15


# --- 12. downtime: UCHALASI HAM har doim ----------------------------------


def test_uchala_downtime_olchovi_har_doim_beriladi():
    """§6.1: `D_sd`, `D_probe`, `D_eff` -- hammasi beriladi.

    Faqat bittasini berish tanlov orqali natijani boshqarish bo'lardi:
    `D_sd` `active` lekin 20% throughput'dagi xizmatga NOL downtime beradi.
    """
    obj = build([trial("SYNTH-1"), trial("SYNTH-2", d_sd_us=0,
                                         d_eff_us=5.0 * SEC)])
    for name in ("d_sd", "d_probe", "d_eff"):
        block = obj["downtime"][name]
        assert block["unit"] == "us"
        for q, _ in A.QUANTILES:
            assert q in block
            assert set(block[q]) >= {"estimate", "source", "ci_lower",
                                     "ci_upper", "ci_method"}
    # `d_sd_us = 0` -- O'LCHANGAN NOL, `None` emas: jadvalga kiradi.
    assert obj["downtime"]["d_sd"]["n"] == 2
    assert obj["downtime"]["d_sd"]["n_missing"] == 0


def test_d_eff_censoring_flagi_yoq_demak_note_bilan_beriladi():
    """`reduce.py` `D_eff` uchun censoring flag'i BERMAYDI -- ochiq aytiladi."""
    obj = build([trial("SYNTH-1"), trial("SYNTH-2")])
    d_eff = obj["downtime"]["d_eff"]
    assert d_eff["censoring_flag"] is None
    assert d_eff["n_censored"] is None
    assert d_eff["note"] is not None and "horizon-truncated" in d_eff["note"]
    assert obj["downtime"]["d_probe"]["censoring_flag"] == "d_probe_censored"


def test_downtime_ecdf_step_funksiya_interpolyatsiya_yoq():
    """§10.2: "ECDF'lar TO'LIQ chizilib beriladi".

    QO'LDA HISOB. `d_probe` = 1, 2, 3 s, hammasi event.
        S(1s) = 2/3, S(2s) = 1/3, S(3s) = 0
    `F = 1 - S` = 1/3, 2/3, 1. Nuqtalar soni = event vaqtlari soni = 3:
    oraliqda QO'SHIMCHA nuqta YO'Q (interpolyatsiya qilinmaydi).
    """
    trials = [trial(f"SYNTH-{i}", d_probe_us=v * SEC)
              for i, v in enumerate((1, 2, 3))]
    e = build(trials)["downtime"]["d_probe"]["ecdf"]
    assert e["x"] == [1.0 * SEC, 2.0 * SEC, 3.0 * SEC]
    assert e["y"] == pytest.approx([1 / 3, 2 / 3, 1.0])
    assert len(e["x"]) == len(e["y"]) == 3
    assert "kaplan_meier" in e["method"]


def test_downtime_ecdf_censored_kuzatuvni_hisobga_oladi():
    """Censored kuzatuv `at_risk` ni kamaytiradi => `F` sakrashlari o'zgaradi.

    QO'LDA HISOB. `d_probe` = 1, 2, 3 s; UCHINCHISI censored.
        t=1: n=3, d=1 -> S = 2/3
        t=2: n=2, d=1 -> S = 1/3
    Event vaqti faqat IKKITA (3 s censored), demak `F` = 1/3, 2/3 va u
    1.0 ga YETMAYDI -- bu to'g'ri: 3 s dan keyin nima bo'lgani o'lchanmagan.
    """
    trials = [trial(f"SYNTH-{i}", d_probe_us=v * SEC,
                    d_probe_censored=(v == 3))
              for i, v in enumerate((1, 2, 3))]
    e = build(trials)["downtime"]["d_probe"]["ecdf"]
    assert e["x"] == [1.0 * SEC, 2.0 * SEC]
    assert e["y"] == pytest.approx([1 / 3, 2 / 3])
    assert max(e["y"]) < 1.0


def test_downtime_ecdf_hisoblanmasa_chiqarilmaydi_va_warnings_ga_tushadi():
    """Hamma kuzatuv censored => event vaqti yo'q => ECDF TO'QILMAYDI."""
    trials = [trial(f"SYNTH-{i}", d_probe_us=v * SEC, d_probe_censored=True)
              for i, v in enumerate((1, 2))]
    obj = build(trials)
    assert "ecdf" not in obj["downtime"]["d_probe"]
    assert "ecdf_not_computable" in warn_codes(obj)


def test_downtime_kvantili_shartnomadagi_ichki_shaklga_ega():
    """Har kvantil obyekt: `{estimate, ci_lower, ci_upper, ci_method}`."""
    trials = [trial(f"SYNTH-{i}", d_probe_us=v * SEC)
              for i, v in enumerate((1, 2, 3, 4, 5))]
    obj = build(trials)
    for name in ("d_sd", "d_probe", "d_eff"):
        for q, _ in A.QUANTILES:
            entry = obj["downtime"][name][q]
            assert isinstance(entry, dict)
            assert {"estimate", "ci_lower", "ci_upper",
                    "ci_method"} <= set(entry)


# --- 12b. §8.2 probe narxi: zanjir uzilgan, TO'QILMAYDI -------------------


def test_probe_cost_zanjir_uzilgan_bolim_chiqarilmaydi_va_sabab_warnings_da():
    """§8.2 narxni talab qiladi, lekin `reduce.py` uni CHIQARMAYDI.

    FAKT (tekshirilgan): `prober.cost_report()` `core_percent` va
    `budget_percent` beradi va `prober_stop` ga yozadi, lekin `reduce.py`
    `prober_stop` ni o'qimaydi -- `trial_metrics` da narx YO'Q. Nol yoki
    budjet qiymati berish §8.2 ni tekshirilgandek ko'rsatardi.
    """
    obj = build([trial("SYNTH-1"), trial("SYNTH-2")])
    assert "probe_cost" not in obj
    assert "probe_cost_absent" in warn_codes(obj)


def test_probe_cost_kirishda_bolsa_arm_boyicha_beriladi():
    """Zanjir tuzatilsa transport ISHLAYDI -- bu yerda sintetik kirish bilan.

    §8.2 narx arm'lar bo'yicha BIR XIL ushlanishini talab qiladi, shuning
    uchun u arm bo'yicha, per-trial ro'yxat sifatida beriladi.
    """
    trials = [
        trial("SYNTH-a1", arm="A",
              probe_cost={"core_percent": 0.4, "budget_percent": 1.0}),
        trial("SYNTH-a2", arm="A",
              probe_cost={"core_percent": 0.5, "budget_percent": 1.0}),
        trial("SYNTH-n1", arm="no_action",
              probe_cost={"core_percent": None, "budget_percent": 1.0}),
    ]
    obj = build(trials)
    pc = obj["probe_cost"]
    assert pc["budget_percent"] == 1.0       # §8.2: bir yadroning 1%
    assert pc["by_arm"]["A"]["core_percent"] == [0.4, 0.5]
    # O'lchanmagan qiymat `None` bo'lib qoladi -- nol deb olinmaydi.
    assert pc["by_arm"]["no_action"]["core_percent"] == [None]
    assert "probe_cost_absent" not in warn_codes(obj)


def test_probe_cost_qisman_bolsa_warning_beriladi():
    trials = [trial("SYNTH-1", probe_cost={"core_percent": 0.4}),
              trial("SYNTH-2")]
    obj = build(trials)
    assert "probe_cost_partial" in warn_codes(obj)
    assert obj["probe_cost"]["by_arm"]["A"]["core_percent"] == [0.4, None]


# --- 13. multiplicity ------------------------------------------------------


def test_multiplicity_holm_bonferroni_p1_da_bitta_birlamchi_test():
    """§10.4: P1 da bitta fault class => BITTA birlamchi test.

    QO'LDA HISOB. m = 1 => Holm adjusted p = min(1, 1*p) = p. Tuzatish
    baribir hisoblanadi, chunki oila §10.4 da MUZLATILGAN -- "bitta test
    edi" post-hoc asos bo'lmasligi kerak.
    """
    obj = build(cells_to_trials({"P0": (20, 20), "P1": (10, 20),
                                 "P2": (0, 20)}))
    m = obj["multiplicity"]
    assert m["method"] == "holm_bonferroni"
    assert len(m["family"]) == 1
    assert m["family"][0]["fault_class"] == "clean_crash"
    assert m["adjusted"] == [pytest.approx(obj["primary"]["p_value"])]
    labels = {u["name"]: u["label"] for u in m["uncorrected"]}
    assert labels["sensitivity: W_stab x theta sweep"] == "exploratory"
    assert any(v == "prespecified_secondary" for v in labels.values())


# --- 14. provenans: ko'chiriladi, qayta hisoblanmaydi ---------------------


def test_preregistration_sha256_kirishdan_kochiriladi_qayta_hisoblanmaydi():
    obj = build([trial("SYNTH-1")],
                meta=run_meta(preregistration_sha256="SYNTH-DIGEST-XYZ"))
    assert obj["preregistration_sha256"] == "SYNTH-DIGEST-XYZ"
    assert obj["preregistration_version"] == "preregistration/v1.3"


def test_preregistration_sha256_yoq_bolsa_warning_va_null():
    meta = run_meta()
    del meta["preregistration_sha256"]
    obj = build([trial("SYNTH-1")], meta=meta)
    assert obj["preregistration_sha256"] is None
    assert "preregistration_sha256_missing" in warn_codes(obj)


def test_t_trial_us_kirishdan_kochiriladi_qayta_hisoblanmaydi():
    """Shartnoma §5.4: horizon DRIVER hisoblaydi. `k/n` shunga nisbatan."""
    obj = build([trial("SYNTH-1")])
    assert obj["t_trial_us"] == T_TRIAL_US
    assert "32.0 + 8.0 + 0.1" in obj["t_trial_formula"]


def test_t_trial_us_yoq_bolsa_warning_va_null_taxmin_qilinmaydi():
    meta = run_meta()
    del meta["t_trial_us"]
    obj = build([trial("SYNTH-1")], meta=meta)
    assert obj["t_trial_us"] is None
    assert "t_trial_us_missing" in warn_codes(obj)


# --- 15. determinizm, kirish invariantlari, CLI --------------------------


def test_analiz_deterministik_bir_xil_kirish_bir_xil_chiqish():
    """Qoida 2: bootstrap urug'i MUZLATILGAN, demak CI'lar siljimaydi."""
    trials = [trial(f"SYNTH-{i}", d_probe_us=(i + 1) * SEC,
                    d_probe_censored=(i == 4)) for i in range(5)]
    a = json.dumps(build(trials), sort_keys=True)
    b = json.dumps(build(trials), sort_keys=True)
    assert a == b


def test_disposition_yopiq_enumdan_tashqarida_bolsa_rad_etiladi():
    """§12 yopiq enum. Noma'lum disposition jimgina o'tib ketmaydi."""
    with pytest.raises(A.AnalysisError, match="yopiq enum"):
        build([trial("SYNTH-1", disposition="failed")])


def test_trial_metrics_record_topilmasa_rad_etiladi(tmp_path):
    p = tmp_path / "trials.jsonl"
    p.write_text(json.dumps({"record_type": "episode"}) + "\n",
                 encoding="utf-8")
    with pytest.raises(A.AnalysisError, match="trial_metrics"):
        A.load_trials(str(p))


def test_chiqish_kirish_fayli_ustiga_yozilmaydi(tmp_path):
    t = tmp_path / "trials.jsonl"
    t.write_text("", encoding="utf-8")
    with pytest.raises(A.AnalysisError, match="kirish fayli"):
        A._assert_not_input(str(t), [str(t)])


def test_main_analysis_json_yozadi_va_sweep_ni_qabul_qiladi(tmp_path, capsys):
    """CLI shartnomasi: `--trials`, `--run-meta`, `--out`, `--sweep`, `--json`."""
    trials = cells_to_trials({"P0": (5, 6), "P1": (4, 6), "P2": (2, 6)})
    tp = tmp_path / "trials.jsonl"
    tp.write_text("".join(json.dumps(r) + "\n" for r in trials),
                  encoding="utf-8")
    mp = tmp_path / "run_meta.json"
    mp.write_text(json.dumps(run_meta()), encoding="utf-8")
    sp = tmp_path / "sweep.jsonl"
    sp.write_text("".join(json.dumps(c) + "\n"
                          for c in full_sweep("SYNTH-P0-0",
                                              truncated_from_s=60)),
                  encoding="utf-8")
    out = tmp_path / "analysis.json"

    rc = A.main(["--trials", str(tp), "--run-meta", str(mp),
                 "--out", str(out), "--sweep", str(sp), "--json"])
    assert rc == 0
    assert out.exists()
    obj = json.loads(out.read_text(encoding="utf-8"))
    assert obj["analysis_version"] == "p1/v1"
    assert obj["n_trials"]["total"] == 18
    assert len(obj["sensitivity"]["grid"]) == 15
    # `--json` stdout'ga ham AYNAN shu obyektni beradi.
    assert json.loads(capsys.readouterr().out) == obj


def test_main_json_bayrogisiz_ham_ishlaydi(tmp_path):
    trials = cells_to_trials({"P0": (5, 6), "P1": (4, 6), "P2": (2, 6)})
    tp = tmp_path / "trials.jsonl"
    tp.write_text("".join(json.dumps(r) + "\n" for r in trials),
                  encoding="utf-8")
    mp = tmp_path / "run_meta.json"
    mp.write_text(json.dumps(run_meta()), encoding="utf-8")
    out = tmp_path / "analysis.json"
    assert A.main(["--trials", str(tp), "--run-meta", str(mp),
                   "--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["sensitivity"]["grid"] == []


def test_main_analiz_xatosida_2_qaytaradi(tmp_path, capsys):
    tp = tmp_path / "trials.jsonl"
    tp.write_text(json.dumps(trial("SYNTH-1", disposition="failed")) + "\n",
                  encoding="utf-8")
    mp = tmp_path / "run_meta.json"
    mp.write_text(json.dumps(run_meta()), encoding="utf-8")
    rc = A.main(["--trials", str(tp), "--run-meta", str(mp),
                 "--out", str(tmp_path / "analysis.json")])
    assert rc == 2
    assert "analiz xatosi" in capsys.readouterr().err


# --- 16. modul PUR va OFFLINE --------------------------------------------


def test_analiz_offline_olchov_modullarini_import_qilmaydi():
    """Qoida 1: `cgroup`, `psi_sampler`, `subprocess`, `systemd` YO'Q."""
    src = (__import__("pathlib").Path(A.__file__)).read_text(encoding="utf-8")
    body = src.split('"""', 2)[2]      # modul docstring'idan keyingi qism
    for banned in ("import subprocess", "from . import cgroup",
                   "from . import psi_sampler", "from . import prober",
                   "from . import units", "import socket"):
        assert banned not in body, banned


def test_analiz_psi_ni_oqimaydi():
    """§5 sirkulyarlik kafolati: PSI hech qanday ta'rifga KIRMAYDI.

    Kirishda PSI maydoni bo'lsa ham chiqishda PSI izi bo'lmaydi.
    """
    obj = build([trial("SYNTH-1", psi_full_total_us=999_999),
                 trial("SYNTH-2", psi_full_total_us=111_111)])
    blob = json.dumps(obj).lower()
    assert "psi" not in blob
    assert "999999" not in blob and "111111" not in blob


def test_stats_modulidagi_funksiyalar_qayta_yozilmagan():
    """Qoida 3: `analyze.py` da birorta statistik formula YO'Q.

    Ishlatilgan estimatorlar `stats.py` ning public API'sidan: ularning
    nomlari `stats.__all__` da bo'lishi SHART.
    """
    used = ("clopper_pearson", "newcombe_diff_ci", "cochran_armitage_trend",
            "kaplan_meier", "km_quantile", "logrank", "rmst",
            "rmst_difference", "bootstrap_ci", "holm_bonferroni")
    for name in used:
        assert name in S.__all__, name
        assert f"S.{name}(" in (__import__("pathlib").Path(A.__file__)
                                ).read_text(encoding="utf-8"), name
