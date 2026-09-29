"""stats.py testlari -- har bir estimator NASHR ETILGAN ishlangan misolga qarshi.

TEST FALSAFASI. Bu testlar `revix.stats` ni O'ZIGA QARSHI tekshirmaydi
(regression snapshot emas). Har bir birlamchi estimator uchun raqamli javobi
nashr etilgan MANBA topilgan va shu raqamga qarshi aniq tolerans bilan
assert qilingan. Manba har testda izohda ko'rsatilgan.

ISHLATILGAN NASHR ETILGAN MISOLLAR:
  [A]  Agresti, A., "An Introduction to Categorical Data Analysis", 2-nashr,
       §2.5.2, Table 2.7 (manba: Graubard, B.I. & Korn, E.L., Biometrics
       43:471-476, 1987). Cochran-Armitage trend.
  [CP] Clopper, C.J. & Pearson, E.S. (1934), Biometrika 26:404-413.
       Exact binomial interval -- TA'RIF bo'yicha tekshiriladi.
  [F]  Fagerland, M.W., Lydersen, S. & Laake, P. (2011), "Recommended
       confidence intervals for two independent binomial proportions",
       Statistical Methods in Medical Research 20(1):3-40, §4.2.3 tenglama (7)
       va Table 3 (ma'lumot: Perondi va boshq., 2004). Newcombe score CI.
  [N]  Farrow, M., "MAS3301/MAS8311 Biostatistics Part II: Survival",
       Newcastle University, Semester 2 2009-10, §5.2 / §5.3 / §6.3 / §6.4.
       KM + Greenwood + median + log-rank (varians jadvali bilan).
       KM ma'lumoti: Woolson, R.F. & Lachenbruch, P.A. (1980) skin-graft
       (manbada "slightly altered" deb belgilangan).
  [M]  MedCalc statistik dasturi qo'llanmasi, Kaplan-Meier sahifasi;
       ma'lumot: Freireich, E.J. va boshq., Blood 1963;21:699-716.
       Log-rank chi-square = 16.79, P < 0.0001, guruhlarda 9 va 21 event.
  [B]  Blakesley, R.E., Mazumdar, S., Dew, M.A., Houck, P.R., Tang, G.,
       Reynolds, C.F. III & Butters, M.A. (2009), "Comparisons of methods for
       multiple hypothesis testing in neuropsychological research",
       Neuropsychology 23(2):255-264, Table 1. Holm adjusted p-value'lar.

VALIDATSIYA QILINMAGAN (halol bayon):
  * `negative_binomial_rate_test` -- nashr etilgan ishlangan misol TOPILMADI.
    Faqat ichki izchillik va xususiyatlar tekshirilgan.
  * `rmst` / `rmst_difference` STANDARD ERROR'i -- nashr etilgan raqamli
    misol topilmadi. Nuqtaviy baho [N] dagi nashr etilgan KM jadvali ostidagi
    yuza bilan tekshirilgan (arifmetika testda ko'rsatilgan).
"""

import math
import warnings

import numpy as np
import pytest
from scipy import stats as sp

from revix import stats as S

# --- nashr etilgan ma'lumot to'plamlari -------------------------------------

# [N] §5.2 -- skin-graft ishdan chiqish vaqtlari (kun), n = 11.
# Nashr etilgan jadval: event'lar 16, 18, 19, 19, 22, 29, 37, 63, 93;
# censored 57, 60 (manbada qavs ichida).
SKIN_T = [16, 18, 19, 19, 22, 29, 37, 57, 60, 63, 93]
SKIN_E = [1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1]
# [N] §5.2 jadvalining Ŝ(t) ustuni:
SKIN_S_PUBLISHED = [0.909, 0.818, 0.636, 0.545, 0.455, 0.364, 0.182, 0.000]
SKIN_N_PUBLISHED = [11, 10, 9, 7, 6, 5, 2, 1]  # N_j ustuni
SKIN_D_PUBLISHED = [1, 1, 2, 1, 1, 1, 1, 1]  # d_j ustuni

# [N] §6.3 -- log-rank misoli. Control hammasi event; Drug'da * = censored.
FARROW_CTRL_T = [1, 1, 2, 2, 3, 4, 4, 5, 5, 8, 8, 8, 8, 11, 11, 12, 12]
FARROW_CTRL_E = [1] * 17
FARROW_DRUG_T = [6, 6, 6, 6, 7, 9, 10, 11, 11, 16, 17, 19, 20, 25, 32, 32]
FARROW_DRUG_E = [1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0]

# [N] §6.4 -- soddalashtirilgan (O-E)^2/E misoli.
FARROW2_G1_T = [10, 11, 12, 14, 16, 22]
FARROW2_G1_E = [1, 0, 0, 1, 0, 1]
FARROW2_G2_T = [13, 22, 26, 29, 35, 40]
FARROW2_G2_E = [1, 1, 0, 1, 0, 0]

# [M] -- Freireich va boshq. (1963) remission davomiyligi (hafta).
# 6-MP arm: 6, 6, 6, 6+, 7, 9+, 10, 10+, 11+, 13, 16, 17+, 19+, 20+, 22, 23,
#           25+, 32+, 32+, 34+, 35+   (+ = censored; 9 event, 12 censored)
MP_T = [6, 6, 6, 6, 7, 9, 10, 10, 11, 13, 16, 17, 19, 20, 22, 23, 25, 32, 32, 34, 35]
MP_E = [1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0]
# Placebo arm: hammasi event (n = 21, 21 event -- [M] "21 cases in group 2").
PLACEBO_T = [1, 1, 2, 2, 3, 4, 4, 5, 5, 8, 8, 8, 8, 11, 11, 12, 12, 15, 17, 22, 23]
PLACEBO_E = [1] * 21


# ===========================================================================
# 1. Cochran-Armitage trend testi -- H1 BIRLAMCHI TEST
# ===========================================================================


def test_cochran_armitage_matches_agresti_table_2_7():
    """[A] Agresti 2-nashr §2.5.2, Table 2.7 -- ona alkogol iste'moli.

    Jadval (Absent, Present, Total):
        0      17066 /  48 / 17114
        <1     14464 /  38 / 14502
        1-2      788 /   5 /   793
        3-5      126 /   1 /   127
        >=6       37 /   1 /    38
    Score'lar kategoriya o'rtalari: v = (0, 0.5, 1.5, 4.0, 7.0).
    NASHR ETILGAN natijalar (§2.5.2 matni):
        r = 0.0142,  M^2 = (32573)(0.0142)^2 = 6.6,  P = 0.01,
        M = 2.56 (Ha: rho > 0 uchun bir tomonlama P = 0.005).
    """
    successes = [48, 38, 5, 1, 1]
    totals = [17114, 14502, 793, 127, 38]
    scores = [0.0, 0.5, 1.5, 4.0, 7.0]

    res = S.cochran_armitage_trend(successes, totals, scores)

    # M = 2.56 (nashr etilgan, 2 kasr xonasi)
    assert res.statistic == pytest.approx(2.56, abs=0.01)
    # M^2 = 6.6 (nashr etilgan, 1 kasr xona)
    assert res.chi2 == pytest.approx(6.6, abs=0.05)
    # P = 0.01 (ikki tomonlama; nashr etilgan bir tomonlama 0.005)
    assert res.p_value == pytest.approx(0.01, abs=0.001)
    assert res.p_value / 2.0 == pytest.approx(0.005, abs=0.001)
    assert res.direction == "increasing"


def test_cochran_armitage_equals_n_times_squared_correlation():
    """CA statistikasining ayniyati: z^2 = N * r^2 (r -- Pearson korrelyatsiya).

    [A] §2.5.1 M^2 = (N-1) r^2 ni beradi; CA z^2 = N r^2. Katta N da ular
    farq qilmaydi, lekin ayniyat implementatsiyani mustaqil tekshiradi.
    """
    successes = [48, 38, 5, 1, 1]
    totals = [17114, 14502, 793, 127, 38]
    scores = np.array([0.0, 0.5, 1.5, 4.0, 7.0])
    res = S.cochran_armitage_trend(successes, totals, scores)

    # Individual-darajali ma'lumotni qayta tiklab r ni mustaqil hisoblaymiz.
    x, y = [], []
    for s, k, n in zip(scores, successes, totals):
        x.extend([s] * n)
        y.extend([1] * k + [0] * (n - k))
    r = float(np.corrcoef(x, y)[0, 1])
    n_total = len(x)

    assert r == pytest.approx(0.0142, abs=0.0001)  # [A]: r = 0.0142
    assert res.chi2 == pytest.approx(n_total * r * r, rel=1e-9)
    assert (n_total - 1) * r * r == pytest.approx(6.6, abs=0.05)  # [A]: M^2 = 6.6


def test_cochran_armitage_direction_and_sign_flip():
    """Yo'nalish H1 uchun muhim: P(VR) pressure bilan KAMAYISHI kutiladi."""
    # Kamayuvchi proporsiya (P0 -> P2 -- REVIX'da kutilgan shakl)
    dec = S.cochran_armitage_trend([19, 14, 8], [20, 20, 20])
    assert dec.direction == "decreasing"
    assert dec.statistic < 0
    assert dec.p_value < 0.05

    # Score'larni teskari qilish belgini almashtiradi, |z| ni saqlaydi.
    flipped = S.cochran_armitage_trend([19, 14, 8], [20, 20, 20], scores=[2, 1, 0])
    assert flipped.direction == "increasing"
    assert flipped.statistic == pytest.approx(-dec.statistic, rel=1e-12)
    assert flipped.p_value == pytest.approx(dec.p_value, rel=1e-12)

    # Tekis proporsiya -> z ~ 0
    flat = S.cochran_armitage_trend([10, 10, 10], [20, 20, 20])
    assert flat.statistic == pytest.approx(0.0, abs=1e-12)
    assert flat.p_value == pytest.approx(1.0, abs=1e-9)


def test_cochran_armitage_rejects_invalid_input():
    with pytest.raises(ValueError, match="kamida 3"):
        S.cochran_armitage_trend([5, 3], [10, 10])
    with pytest.raises(ValueError, match="uzunligi teng"):
        S.cochran_armitage_trend([5, 3, 1], [10, 10])
    with pytest.raises(ValueError, match="successes <= totals"):
        S.cochran_armitage_trend([11, 3, 1], [10, 10, 10])
    with pytest.raises(ValueError, match="bir xil"):
        S.cochran_armitage_trend([0, 0, 0], [10, 10, 10])
    with pytest.raises(ValueError, match="scores uzunligi"):
        S.cochran_armitage_trend([5, 3, 1], [10, 10, 10], scores=[0, 1])


# ===========================================================================
# 2. Clopper-Pearson exact CI
# ===========================================================================


@pytest.mark.parametrize("k,n", [(3, 10), (15, 148), (7, 34), (1, 29), (81, 263)])
def test_clopper_pearson_satisfies_defining_tail_equations(k, n):
    """[CP] Clopper & Pearson (1934) TA'RIFI: interval exact binomial dumlarni

    aynan alpha/2 ga tenglashtiradi:
        P(X >= k | p = L) = alpha/2   va   P(X <= k | p = U) = alpha/2.
    Bu formula emas, TA'RIF bo'yicha tekshiruv -- implementatsiyaning Beta
    kvantil yozuviga mustaqil.
    """
    alpha = 0.05
    ci = S.clopper_pearson(k, n, alpha=alpha)
    assert sp.binom.sf(k - 1, n, ci.lower) == pytest.approx(alpha / 2.0, abs=1e-10)
    assert sp.binom.cdf(k, n, ci.upper) == pytest.approx(alpha / 2.0, abs=1e-10)
    assert ci.lower <= k / n <= ci.upper


def test_clopper_pearson_boundary_closed_form():
    """k = 0 va k = n uchun yopiq shakl (nashr etilgan, ko'p manbada):

        k = 0 -> L = 0,  U = 1 - (alpha/2)^(1/n)
        k = n -> L = (alpha/2)^(1/n),  U = 1
    n = 20, alpha = 0.05 uchun U = 1 - 0.025^(1/20) = 0.1684334709830854.
    """
    ci0 = S.clopper_pearson(0, 20, alpha=0.05)
    assert ci0.lower == 0.0
    assert ci0.upper == pytest.approx(1.0 - 0.025 ** (1 / 20), abs=1e-12)
    assert ci0.upper == pytest.approx(0.168433, abs=1e-6)

    ci20 = S.clopper_pearson(20, 20, alpha=0.05)
    assert ci20.upper == 1.0
    assert ci20.lower == pytest.approx(0.025 ** (1 / 20), abs=1e-12)
    assert ci20.lower == pytest.approx(0.831567, abs=1e-6)


def test_clopper_pearson_is_wider_than_wald():
    """CP KONSERVATIV: Wald interval'dan KENGROQ.

    Wald [0, 1] dan chiqishi mumkin (k = 3, n = 20 da pastki chegara manfiy),
    shuning uchun kenglik qisilgan Wald bilan taqqoslanadi. Ushlab qolinmagan
    Wald esa allaqachon buzilgan -- shuning uchun §10.1 CP ni talab qiladi.
    """
    for k, n in ((3, 20), (10, 20), (1, 10), (45, 50)):
        cp = S.clopper_pearson(k, n)
        p = k / n
        half = 1.959963984540054 * math.sqrt(p * (1 - p) / n)
        wald_lo, wald_hi = max(0.0, p - half), min(1.0, p + half)
        assert (cp.upper - cp.lower) > (wald_hi - wald_lo), f"k={k} n={n}"
        assert cp.lower >= 0.0 and cp.upper <= 1.0


def test_clopper_pearson_rejects_invalid_input():
    with pytest.raises(ValueError, match="n > 0"):
        S.clopper_pearson(0, 0)
    with pytest.raises(ValueError, match="k <= n"):
        S.clopper_pearson(5, 3)
    with pytest.raises(ValueError, match="alpha"):
        S.clopper_pearson(1, 10, alpha=0.0)


# ===========================================================================
# 3. Newcombe/Wilson-score risk difference CI -- H1 BIRLAMCHI EFFECT SIZE
# ===========================================================================


def test_newcombe_diff_matches_fagerland_table_3():
    """[F] Fagerland, Lydersen & Laake (2011) Table 3 (Perondi va boshq. 2004).

    Adrenalin yuqori vs standart doza RCT'si, bolalarda yurak to'xtashi:
        standart doza  p1 = 7/34 = 0.21
        yuqori doza    p2 = 1/34 = 0.029
        farq           0.18
    NASHR ETILGAN "Newcombe hybrid score" 95% CI: Lower 0.019, Upper 0.34
    (uzunlik 0.32). Manba 2 kasr xonaga yumaloqlaydi, tolerans shunga mos.
    """
    res = S.newcombe_diff_ci(7, 34, 1, 34, alpha=0.05)

    assert res.difference == pytest.approx(0.18, abs=0.005)
    assert res.lower == pytest.approx(0.019, abs=0.001)
    assert res.upper == pytest.approx(0.34, abs=0.005)
    assert (res.upper - res.lower) == pytest.approx(0.32, abs=0.005)
    # [F] matni: Santner-Snell'dan tashqari hamma interval nolni chiqaradi.
    assert res.lower > 0.0


def test_newcombe_diff_is_not_the_wald_interval():
    """Newcombe interval NAIVE WALD EMAS -- bu farq metodning mohiyati.

    Wald 0/n yacheykada nol kenglik beradi (buzilgan); Newcombe bermaydi.
    """
    res = S.newcombe_diff_ci(0, 20, 0, 20)
    # Wald: SE = 0, demak interval [0, 0] -- ma'nosiz.
    assert res.difference == 0.0
    assert res.lower < 0.0 < res.upper

    # Ekstremal ajralish: 20/20 vs 0/20. Wald yana 0 kenglik berardi.
    ext = S.newcombe_diff_ci(20, 20, 0, 20)
    assert ext.difference == 1.0
    assert ext.lower > 0.5
    assert ext.upper == pytest.approx(1.0, abs=1e-12)


def test_newcombe_diff_stays_in_range_and_is_antisymmetric():
    for k1, n1, k2, n2 in [(0, 5, 5, 5), (5, 5, 0, 5), (1, 3, 2, 40), (19, 20, 8, 20)]:
        r = S.newcombe_diff_ci(k1, n1, k2, n2)
        assert -1.0 <= r.lower <= r.difference <= r.upper <= 1.0
        rev = S.newcombe_diff_ci(k2, n2, k1, n1)
        assert rev.difference == pytest.approx(-r.difference, rel=1e-12)
        assert rev.lower == pytest.approx(-r.upper, rel=1e-12, abs=1e-12)
        assert rev.upper == pytest.approx(-r.lower, rel=1e-12, abs=1e-12)


def test_wilson_ci_never_leaves_unit_interval():
    for n in (5, 20, 100):
        for k in range(n + 1):
            w = S.wilson_ci(k, n)
            assert 0.0 <= w.lower <= k / n <= w.upper <= 1.0


# ===========================================================================
# 4. Fisher exact (yupqa qobiq)
# ===========================================================================


def test_fisher_exact_wrapper_matches_scipy_directly():
    res = S.fisher_exact_2x2(19, 20, 8, 20)
    direct = sp.fisher_exact([[19, 1], [8, 12]])
    assert res.p_value == pytest.approx(float(direct.pvalue), rel=1e-12)
    assert res.odds_ratio == pytest.approx(float(direct.statistic), rel=1e-12)
    assert res.p_value < 0.05


# ===========================================================================
# 5. Kaplan-Meier + Greenwood
# ===========================================================================


def test_kaplan_meier_matches_farrow_skin_graft_table():
    """[N] §5.2 -- to'liq nashr etilgan KM jadvali (Woolson & Lachenbruch 1980).

    Nashr etilgan ustunlar (t_j, N_j, d_j, Ŝ(t)):
        16  11  0-cens  1  0.909
        18  10          1  0.818
        19   9          2  0.636
        22   7          1  0.545
        29   6          1  0.455
        37   5  (+2 c)  1  0.364
        63   2          1  0.182
        93   1          1  0.000
    """
    km = S.kaplan_meier(SKIN_T, SKIN_E)

    assert list(km.times) == [16, 18, 19, 22, 29, 37, 63, 93]
    assert list(km.at_risk) == SKIN_N_PUBLISHED
    assert list(km.n_events) == SKIN_D_PUBLISHED
    assert km.n_total == 11
    assert km.n_censored == 2
    np.testing.assert_allclose(km.survival, SKIN_S_PUBLISHED, atol=0.0005)


def test_greenwood_variance_matches_farrow_published_numbers():
    """[N] §5.2 -- Greenwood yig'indisi va standard error nashr etilgan.

    Manba matni: "var log{-log[Ŝ(25)]} ~= (1/log(Ŝ)^2) * sum_{i=1..5} ..."
    va yig'indi aynan 0.0758 deb chop etilgan; shuningdek
    "s.e.[Ŝ(25)] = 0.150".

    Ŝ(25) = 0.545 (t = 22 va t = 29 orasida), demak yig'indi t = 22 gacha.
    """
    km = S.kaplan_meier(SKIN_T, SKIN_E)
    idx22 = int(np.nonzero(km.times == 22)[0][0])

    # Greenwood kumulyativ yig'indisi = var / S^2
    gw_sum = km.variance[idx22] / km.survival[idx22] ** 2
    assert gw_sum == pytest.approx(0.0758, abs=0.00005)  # [N]: 0.0758

    assert km.std_err[idx22] == pytest.approx(0.150, abs=0.0005)  # [N]: 0.150
    assert km.survival_at(25) == pytest.approx(0.545, abs=0.0005)  # [N]: 0.545

    # Qo'lda: 1/(11*10) + 1/(10*9) + 2/(9*7) + 1/(7*6)
    hand = 1 / 110 + 1 / 90 + 2 / 63 + 1 / 42
    assert gw_sum == pytest.approx(hand, rel=1e-12)


def test_km_survival_at_is_right_continuous_step():
    km = S.kaplan_meier(SKIN_T, SKIN_E)
    assert km.survival_at(0) == 1.0
    assert km.survival_at(15.9) == 1.0
    assert km.survival_at(16) == pytest.approx(0.909, abs=0.0005)
    assert km.survival_at(17.9) == pytest.approx(0.909, abs=0.0005)
    assert km.survival_at(1000) == pytest.approx(0.0, abs=1e-12)


def test_km_reduces_to_one_minus_ecdf_without_censoring():
    """XUSUSIYAT: censoring bo'lmasa KM aynan 1 - ECDF."""
    rng = np.random.default_rng(11)
    x = np.round(rng.exponential(3.0, 60), 3)
    km = S.kaplan_meier(x, np.ones(60, dtype=int))
    for t in np.linspace(0, x.max() * 1.1, 37):
        ecdf = float(np.mean(x <= t))
        assert km.survival_at(t) == pytest.approx(1.0 - ecdf, abs=1e-12)

    # Ties bilan ham (kvantlangan D_probe -- §6.1 aynan shunday)
    y = np.array([1, 1, 2, 2, 2, 5, 5, 9], dtype=float)
    km2 = S.kaplan_meier(y, np.ones(8, dtype=int))
    for t in (0.5, 1, 1.5, 2, 4, 5, 8, 9, 20):
        assert km2.survival_at(t) == pytest.approx(1.0 - np.mean(y <= t), abs=1e-12)


def test_km_zero_variance_convention_at_s_equals_zero():
    """KONVENSIYA (docstring'da e'lon qilingan): n_i == d_i hadi 0 deb olinadi.

    Natijada S = 0 nuqtasida std_err = 0 (NaN emas).
    """
    km = S.kaplan_meier(SKIN_T, SKIN_E)
    assert km.survival[-1] == 0.0
    assert km.std_err[-1] == 0.0
    assert np.all(np.isfinite(km.std_err))


def test_km_median_matches_published_values():
    """[N] §5.3: skin-graft median = 29 kun.

    [M] / Freireich (1963): 6-MP median remission 23 hafta, placebo 8 hafta.
    """
    assert S.km_quantile(S.kaplan_meier(SKIN_T, SKIN_E), 0.5) == 29.0
    assert S.km_quantile(S.kaplan_meier(MP_T, MP_E), 0.5) == 23.0
    assert S.km_quantile(S.kaplan_meier(PLACEBO_T, PLACEBO_E), 0.5) == 8.0


def test_km_median_is_nan_when_curve_never_reaches_half():
    """Og'ir censoring: median ANIQLANMAGAN -> nan, oxirgi vaqt EMAS."""
    t = [1, 2, 3, 4, 5, 6, 7, 8]
    e = [1, 0, 0, 0, 0, 0, 0, 0]
    assert math.isnan(S.km_quantile(S.kaplan_meier(t, e), 0.5))


def test_km_rejects_invalid_input():
    with pytest.raises(ValueError, match="uzunligi teng"):
        S.kaplan_meier([1, 2, 3], [1, 1])
    with pytest.raises(ValueError, match="0 .*censored"):
        S.kaplan_meier([1, 2], [1, 2])
    with pytest.raises(ValueError, match="manfiy"):
        S.kaplan_meier([-1, 2], [1, 1])
    with pytest.raises(ValueError, match="bo'sh namuna"):
        S.kaplan_meier([], [])


# ===========================================================================
# 6. Log-rank
# ===========================================================================


def test_logrank_matches_farrow_published_example():
    """[N] §6.3 -- to'liq nashr etilgan log-rank jadvali va natijasi.

    NASHR ETILGAN: O1 = 17, E1 = 8.5, V = 4.634, W = (17-8.5)^2/4.634 = 15.6.

    OGOHLIK: manba E1 ni 8.5 ga YUMALOQLAB so'ng kvadratga ko'taradi, shuning
    uchun 15.6 beradi. Aniq E1 = 8.5244 bilan W = 15.49. Ikkalasi ham
    tekshiriladi, chunki farq faqat yumaloqlashdan.
    """
    res = S.logrank(FARROW_CTRL_T, FARROW_CTRL_E, FARROW_DRUG_T, FARROW_DRUG_E)

    assert res.observed_a == 17.0  # [N]: O1 = 17
    assert res.expected_a == pytest.approx(8.5, abs=0.03)  # [N]: E1 = 8.5
    assert res.variance == pytest.approx(4.634, abs=0.003)  # [N]: V = 4.634

    # Manbaning arifmetikasini aynan qaytaramiz: (17 - 8.5)^2 / 4.634
    assert (17.0 - 8.5) ** 2 / 4.634 == pytest.approx(15.6, abs=0.05)
    # O'z statistikamiz aniq E1 bilan hisoblangan
    assert res.statistic == pytest.approx(
        (res.observed_a - res.expected_a) ** 2 / res.variance, rel=1e-12
    )
    assert res.statistic == pytest.approx(15.5, abs=0.15)
    assert res.p_value < 0.001

    # O1 + O2 = E1 + E2 ayniyati ([N] §6.4 da ko'rsatilgan)
    assert res.observed_a + res.observed_b == pytest.approx(
        res.expected_a + res.expected_b, rel=1e-12
    )


def test_logrank_observed_expected_match_farrow_simplified_example():
    """[N] §6.4 -- soddalashtirilgan misol: O1 = 3, O2 = 3, E1 = 1.54, E2 = 4.46,

    W* = (3-1.54)^2/1.54 + (3-4.46)^2/4.46 = 1.86.
    Bu test `logrank` ning O/E buxgalteriyasini (`v_j`dan mustaqil) tekshiradi.
    """
    res = S.logrank(FARROW2_G1_T, FARROW2_G1_E, FARROW2_G2_T, FARROW2_G2_E)

    assert res.observed_a == 3.0
    assert res.observed_b == 3.0
    assert res.expected_a == pytest.approx(1.54, abs=0.005)  # [N]: 1.54
    assert res.expected_b == pytest.approx(4.46, abs=0.005)  # [N]: 4.46

    w_star = (res.observed_a - res.expected_a) ** 2 / res.expected_a + (
        res.observed_b - res.expected_b
    ) ** 2 / res.expected_b
    assert w_star == pytest.approx(1.86, abs=0.01)  # [N]: W* = 1.86


def test_logrank_matches_medcalc_freireich_chi_square():
    """[M] MedCalc qo'llanmasi, Freireich va boshq. Blood 1963;21:699-716.

    NASHR ETILGAN: "9 cases in group 1 and 21 cases in group 2 presented the
    outcome of interest. The Chi-squared statistic was 16.79 with associated
    P-value of less than 0.0001."
    """
    res = S.logrank(MP_T, MP_E, PLACEBO_T, PLACEBO_E)

    assert res.observed_a == 9.0  # [M]: guruh 1 da 9 event
    assert res.observed_b == 21.0  # [M]: guruh 2 da 21 event
    assert res.statistic == pytest.approx(16.79, abs=0.005)  # [M]: 16.79
    assert res.p_value < 0.0001  # [M]: P < 0.0001


def test_logrank_identical_groups_gives_p_near_one():
    """XUSUSIYAT: bir xil guruhlar -> O = E, chi2 = 0, p = 1."""
    t = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    e = [1, 1, 0, 1, 1, 0, 1, 1, 1, 0]
    res = S.logrank(t, e, t, e)
    assert res.statistic == pytest.approx(0.0, abs=1e-20)
    assert res.p_value == pytest.approx(1.0, abs=1e-12)
    assert res.observed_a == pytest.approx(res.expected_a, rel=1e-12)


def test_logrank_is_symmetric_in_group_order():
    a = S.logrank(MP_T, MP_E, PLACEBO_T, PLACEBO_E)
    b = S.logrank(PLACEBO_T, PLACEBO_E, MP_T, MP_E)
    assert a.statistic == pytest.approx(b.statistic, rel=1e-12)
    assert a.variance == pytest.approx(b.variance, rel=1e-12)
    assert a.observed_a == b.observed_b
    assert a.expected_a == pytest.approx(b.expected_b, rel=1e-12)


def test_logrank_fails_loud_when_no_informative_event():
    """FAIL-LOUD: informativ event bo'lmasa p = 1.0 EMAS, NaN."""
    res = S.logrank([5, 6], [0, 0], [7, 8], [0, 0])
    assert math.isnan(res.statistic)
    assert math.isnan(res.p_value)


# ===========================================================================
# 7. RMST -- H2 BOSH EFFECT MEASURE
# ===========================================================================


def test_rmst_equals_area_under_published_km_table():
    """[N] §5.2 dagi NASHR ETILGAN Ŝ(t) ustuni ostidagi yuza.

    S = 1 [0,16), 0.909 [16,18), 0.818 [18,19), 0.636 [19,22),
        0.545 [22,29), 0.455 [29,37), 0.364 [37,63), 0.182 [63,93).

    tau = 37:
        16*1 + 2*0.909 + 1*0.818 + 3*0.636 + 7*0.545 + 8*0.455 = 27.999
    tau = 93:
        27.999 + 26*0.364 + 30*0.182 = 42.923

    Nashr etilgan S 3 kasr xonaga yumaloqlangan, shuning uchun tolerans
    yumaloqlash xatosini qamrab oladi. Bu ARIFMETIKA nashr etilgan ustun
    ustida bajarilgan -- o'z implementatsiyamizga qarshi emas.
    """
    hand37 = 16 * 1 + 2 * 0.909 + 1 * 0.818 + 3 * 0.636 + 7 * 0.545 + 8 * 0.455
    hand93 = hand37 + 26 * 0.364 + 30 * 0.182
    assert hand37 == pytest.approx(27.999, abs=1e-9)
    assert hand93 == pytest.approx(42.923, abs=1e-9)

    assert S.rmst(SKIN_T, SKIN_E, 37).rmst == pytest.approx(hand37, abs=0.01)
    assert S.rmst(SKIN_T, SKIN_E, 93).rmst == pytest.approx(hand93, abs=0.02)

    # Aniq kasrlar bilan (yumaloqlanmagan) -- tau = 37 da aynan 28.
    assert S.rmst(SKIN_T, SKIN_E, 37).rmst == pytest.approx(28.0, abs=1e-12)


def test_rmst_analytic_std_err_agrees_with_nonparametric_bootstrap():
    """RMST STANDARD ERROR uchun MUSTAQIL cross-check (nashr etilgan raqam emas).

    Greenwood asosidagi delta-metod SE'si uchun nashr etilgan raqamli misol
    topilmadi, shuning uchun uni butunlay boshqa yo'l bilan -- nonparametrik
    bootstrap standart og'ishi bilan -- taqqoslaymiz. Ikki usul bir xil
    formuladan kelmaydi, demak bu ma'noli tekshiruv.

    OGOHLIK: bu NASHR ETILGAN VALIDATSIYA EMAS. Ikkala usul ham asimptotik.
    """
    rng = np.random.default_rng(99)
    cases = [
        (np.asarray(SKIN_T, float), np.asarray(SKIN_E), 63.0),
        (np.asarray(MP_T, float), np.asarray(MP_E), 23.0),
    ]
    # Sintetik: censoring bilan o'rtacha kattalikdagi namuna
    lifetime = rng.exponential(5.0, 80)
    censor = rng.exponential(12.0, 80)
    cases.append(
        (np.minimum(lifetime, censor), (lifetime <= censor).astype(int), 8.0)
    )

    for t, e, tau in cases:
        analytic = S.rmst(t, e, tau)
        n = t.size
        boots = []
        # Ba'zi resample'lar tau ga yetmaydi va (to'g'ri) ogohlantiradi --
        # bu bootlab olishning tabiiy oqibati, testning mavzusi emas.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            for _ in range(1500):
                idx = rng.integers(0, n, n)
                boots.append(S.rmst(t[idx], e[idx], tau).rmst)
        boot_sd = float(np.std(boots, ddof=1))
        assert analytic.std_err == pytest.approx(boot_sd, rel=0.15), (
            f"tau={tau}: analitik SE {analytic.std_err} vs bootstrap SD {boot_sd}"
        )


def test_rmst_equals_sample_mean_when_no_censoring_and_tau_is_max():
    """XUSUSIYAT: censoring yo'q va tau = max(t) -> RMST = namuna o'rtachasi.

    Sabab: int_0^tau (1 - ECDF(u)) du = mean(min(T, tau)) = mean(T).
    """
    for x in (
        np.array([2.0, 3, 5, 7, 11]),
        np.array([2.0, 3, 5, 7, 11, 11]),  # ties
        np.array([1.5, 1.5, 1.5]),
        np.round(np.random.default_rng(5).exponential(4.0, 50), 4),
    ):
        r = S.rmst(x, np.ones(x.size, dtype=int), float(x.max()))
        assert r.rmst == pytest.approx(float(x.mean()), rel=1e-12)


def test_rmst_is_mean_of_truncated_times_without_censoring():
    """Umumiyroq: censoring yo'q -> RMST(tau) = mean(min(T, tau)), har tau da."""
    x = np.array([2.0, 3, 5, 7, 11, 11, 20])
    e = np.ones(x.size, dtype=int)
    for tau in (1.0, 2.0, 4.5, 11.0, 15.0, 20.0):
        assert S.rmst(x, e, tau).rmst == pytest.approx(
            float(np.mean(np.minimum(x, tau))), rel=1e-12
        )


def test_rmst_is_monotone_nondecreasing_in_tau():
    prev = -1.0
    for tau in (5, 10, 20, 30, 37, 50, 63, 93):
        cur = S.rmst(SKIN_T, SKIN_E, tau).rmst
        assert cur >= prev
        prev = cur


def test_rmst_warns_when_tau_exceeds_last_observation():
    with pytest.warns(RuntimeWarning, match="BIASED"):
        S.rmst(SKIN_T, SKIN_E, 200.0)


def test_rmst_rejects_invalid_tau():
    for bad in (0.0, -1.0, float("inf"), float("nan")):
        with pytest.raises(ValueError, match="tau"):
            S.rmst(SKIN_T, SKIN_E, bad)


def test_rmst_difference_on_freireich_data():
    """[M] Freireich ma'lumotlari, tau = 23 hafta (oxirgi umumiy event vaqti).

    6-MP arm SEKINROQ relapse qiladi, demak time-to-relapse RMST'i KATTA.
    Nashr etilgan RMST raqami yo'q, shuning uchun bu test YO'NALISH va
    ichki izchillikni tekshiradi, nashr etilgan qiymatni emas.
    """
    res = S.rmst_difference((MP_T, MP_E), (PLACEBO_T, PLACEBO_E), tau=23.0)

    assert res.difference > 0.0
    assert res.rmst_a.rmst > res.rmst_b.rmst
    # placebo'da censoring yo'q va tau = max -> RMST = o'rtacha
    assert res.rmst_b.rmst == pytest.approx(float(np.mean(PLACEBO_T)), rel=1e-12)
    assert res.std_err == pytest.approx(
        math.hypot(res.rmst_a.std_err, res.rmst_b.std_err), rel=1e-12
    )
    assert res.lower > 0.0  # CI nolni chiqaradi
    assert res.p_value < 0.001
    assert res.lower < res.difference < res.upper


def test_rmst_difference_is_antisymmetric():
    ab = S.rmst_difference((MP_T, MP_E), (PLACEBO_T, PLACEBO_E), tau=20.0)
    ba = S.rmst_difference((PLACEBO_T, PLACEBO_E), (MP_T, MP_E), tau=20.0)
    assert ab.difference == pytest.approx(-ba.difference, rel=1e-12)
    assert ab.std_err == pytest.approx(ba.std_err, rel=1e-12)
    assert ab.lower == pytest.approx(-ba.upper, rel=1e-12)
    assert ab.p_value == pytest.approx(ba.p_value, rel=1e-12)


def test_rmst_difference_zero_for_identical_groups():
    res = S.rmst_difference((SKIN_T, SKIN_E), (SKIN_T, SKIN_E), tau=63.0)
    assert res.difference == pytest.approx(0.0, abs=1e-12)
    assert res.p_value == pytest.approx(1.0, abs=1e-12)


def test_rmst_difference_rejects_bad_group_shape():
    with pytest.raises(ValueError, match="group_a"):
        S.rmst_difference(SKIN_T, (SKIN_T, SKIN_E), tau=10.0)
    with pytest.raises(ValueError, match="group_b"):
        S.rmst_difference((SKIN_T, SKIN_E), SKIN_T, tau=10.0)


# ===========================================================================
# 8. Cliff's delta
# ===========================================================================


def test_cliffs_delta_matches_mann_whitney_identity():
    """Ties bo'lmaganda ayniyat: delta = 2*U/(n_a*n_b) - 1.

    U -- `scipy.stats.mannwhitneyu` statistikasi. Bu MUSTAQIL
    implementatsiyaga qarshi cross-check (Cliff 1993; Vargha & Delaney 2000).
    """
    rng = np.random.default_rng(7)
    for na, nb, shift in ((30, 25, 0.8), (10, 10, 0.0), (7, 40, -1.5), (50, 3, 2.0)):
        a = rng.normal(0.0, 1.0, na)
        b = rng.normal(shift, 1.0, nb)
        u = float(sp.mannwhitneyu(a, b, alternative="two-sided").statistic)
        cd = S.cliffs_delta(a, b, n_boot=200, rng=1)
        assert cd.delta == pytest.approx(2.0 * u / (na * nb) - 1.0, rel=1e-12, abs=1e-12)
        assert cd.a12 == pytest.approx(u / (na * nb), rel=1e-12, abs=1e-12)


def test_cliffs_delta_handles_ties_correctly():
    """Ties (kvantlangan D_probe) delta'ga 0 qo'shadi, +-1 emas."""
    a = np.array([1.0, 2.0, 3.0])
    b = np.array([2.0, 2.0, 2.0])
    # a > b: 3 ta (3>2 x3); a < b: 3 ta (1<2 x3); ties: 3 ta
    cd = S.cliffs_delta(a, b, n_boot=200, rng=1)
    assert cd.delta == pytest.approx(0.0, abs=1e-12)


def test_cliffs_delta_complete_separation():
    a = np.array([10.0, 11, 12])
    b = np.array([1.0, 2, 3])
    assert S.cliffs_delta(a, b, n_boot=200, rng=1).delta == pytest.approx(1.0)
    assert S.cliffs_delta(b, a, n_boot=200, rng=1).delta == pytest.approx(-1.0)
    assert S.cliffs_delta(a, b, n_boot=200, rng=1).a12 == pytest.approx(1.0)


def test_cliffs_delta_bootstrap_ci_brackets_point_estimate():
    rng = np.random.default_rng(19)
    a = rng.normal(0.0, 1.0, 40)
    b = rng.normal(1.0, 1.0, 40)
    for method in ("percentile", "bca"):
        cd = S.cliffs_delta(a, b, n_boot=600, method=method, rng=3)
        assert cd.lower <= cd.delta <= cd.upper
        assert -1.0 <= cd.lower and cd.upper <= 1.0
        assert cd.upper < 0.0  # b aniq kattaroq -> delta manfiy va CI nolni chiqaradi


def test_cliffs_delta_rejects_invalid_input():
    with pytest.raises(ValueError, match="bo'sh"):
        S.cliffs_delta([], [1, 2])
    with pytest.raises(ValueError, match="NaN"):
        S.cliffs_delta([1.0, float("nan")], [1, 2])
    with pytest.raises(ValueError, match="method"):
        S.cliffs_delta([1, 2], [3, 4], method="jackknife")


# ===========================================================================
# 9. Bootstrap CI (BCa)
# ===========================================================================


def test_bootstrap_ci_covers_known_parameter_at_roughly_nominal_rate():
    """SINTETIK coverage tekshiruvi: ma'lum parametr ~95% da qoplanishi kerak.

    Tez bo'lishi uchun kichik: 200 takrorlash, n = 40, n_boot = 199.
    Monte Carlo xatosi ~ +-3%, shuning uchun chegara keng (0.85..1.00) --
    test coverage FALOKATLI buzilganini ushlaydi, aniqlikni o'lchamaydi.
    """
    rng = np.random.default_rng(2024)
    true_mean = 5.0
    hits = 0
    reps = 200
    for _ in range(reps):
        x = rng.normal(true_mean, 2.0, 40)
        ci = S.bootstrap_ci(x, np.mean, alpha=0.05, n_boot=199, rng=rng)
        if ci.lower <= true_mean <= ci.upper:
            hits += 1
    coverage = hits / reps
    assert 0.85 <= coverage <= 1.0, f"coverage {coverage} nominal 0.95 dan juda uzoq"


def test_bootstrap_ci_median_and_quantiles_bracket_the_estimate():
    rng = np.random.default_rng(31)
    x = rng.exponential(2.0, 200)

    def p90(a, axis=-1):
        return np.quantile(a, 0.90, axis=axis)

    for stat in (np.median, p90):
        ci = S.bootstrap_ci(x, stat, n_boot=999, rng=5)
        assert ci.lower <= ci.estimate <= ci.upper
        assert ci.method == "bca"
        assert ci.method_requested == "bca"


def test_bootstrap_ci_falls_back_to_percentile_when_bca_degenerate():
    """Degenerativ holat JIMGINA o'tmaydi: ogohlantirish + method maydoni."""
    with pytest.warns(RuntimeWarning, match="BCa interval degenerativ"):
        ci = S.bootstrap_ci([1.0] * 20, np.mean, n_boot=200, rng=1)
    assert ci.method == "percentile"
    assert ci.method_requested == "bca"
    assert ci.lower == pytest.approx(1.0)
    assert ci.upper == pytest.approx(1.0)


def test_bootstrap_ci_is_reproducible_with_same_seed():
    x = np.random.default_rng(8).exponential(1.0, 60)
    a = S.bootstrap_ci(x, np.median, n_boot=499, rng=123)
    b = S.bootstrap_ci(x, np.median, n_boot=499, rng=123)
    assert a.lower == b.lower and a.upper == b.upper


def test_bootstrap_ci_rejects_invalid_arguments():
    x = [1.0, 2.0, 3.0, 4.0]
    with pytest.raises(ValueError, match="alpha"):
        S.bootstrap_ci(x, np.mean, alpha=1.0)
    with pytest.raises(ValueError, match="n_boot"):
        S.bootstrap_ci(x, np.mean, n_boot=10)
    with pytest.raises(ValueError, match="method"):
        S.bootstrap_ci(x, np.mean, method="wild")


def test_bootstrap_ci_accepts_two_sample_statistic():
    rng = np.random.default_rng(17)
    a = rng.normal(0.0, 1.0, 40)
    b = rng.normal(2.0, 1.0, 40)

    def diff_of_medians(x, y, axis=-1):
        return np.median(x, axis=axis) - np.median(y, axis=axis)

    ci = S.bootstrap_ci((a, b), diff_of_medians, n_boot=999, rng=9)
    assert ci.upper < 0.0
    assert ci.lower <= ci.estimate <= ci.upper


# ===========================================================================
# 10. Overdispersion'ga chidamli rate testi -- VALIDATED EMAS
# ===========================================================================


def test_rate_test_docstring_declares_it_is_not_an_nb_mle():
    """HALOLLIK GUARD: docstring'dagi ogohlantirish jimgina olib tashlanmasin.

    Bu test "test" emas, MAJBURIYAT: funksiya nomi negative binomial'ni
    aytadi, lekin implementatsiya quasi-Poisson. Docstring shuni aytishi
    SHART.
    """
    doc = " ".join((S.negative_binomial_rate_test.__doc__ or "").split())
    assert "NEGATIVE BINOMIAL (NB2) MLE EMAS" in doc
    assert "QUASI-POISSON" in doc
    assert "NASHR ETILGAN ISHLANGAN MISOL TOPILMADI" in doc
    assert "VALIDATED EMAS" in doc
    assert S.negative_binomial_rate_test(
        [1, 1, 1], 1.0, [2, 2, 2], 1.0, n_boot=200, rng=1
    ).model == "quasi-poisson+bootstrap"


def test_rate_test_reduces_to_closed_form_poisson_wald_when_phi_clamped():
    """phi = 1 da test AYNAN klassik Poisson log-rate-ratio Wald testiga qaytadi.

    Har birlikda count bir xil bo'lsa Pearson qoldiqlari nol, phi -> 0, va
    konservativ qisish phi = 1 beradi. Unda:
        SE[log RR] = sqrt(1/Y_a + 1/Y_b),   z = log(RR) / SE
    Bu yopiq shakl testda QO'LDA hisoblanadi.
    """
    ya = [3] * 10  # Y_a = 30, exposure 10 -> rate 3
    yb = [1] * 10  # Y_b = 10, exposure 10 -> rate 1
    res = S.negative_binomial_rate_test(ya, 1.0, yb, 1.0, n_boot=200, rng=1)

    assert res.dispersion == pytest.approx(1.0, abs=1e-12)
    assert res.rate_a == pytest.approx(3.0)
    assert res.rate_b == pytest.approx(1.0)
    assert res.rate_ratio == pytest.approx(3.0)

    se_hand = math.sqrt(1.0 / 30.0 + 1.0 / 10.0)
    z_hand = math.log(3.0) / se_hand
    assert res.log_rr_std_err == pytest.approx(se_hand, rel=1e-12)
    assert res.statistic == pytest.approx(z_hand, rel=1e-12)
    assert res.p_value == pytest.approx(2.0 * sp.norm.sf(abs(z_hand)), rel=1e-12)
    assert res.rr_lower == pytest.approx(math.exp(math.log(3.0) - 1.959963984540054 * se_hand), rel=1e-9)


def test_rate_test_detects_overdispersion_and_widens_the_interval():
    """Overdispersed count'larda phi > 1 va interval Poisson'dan KENGROQ.

    Bu H2 uchun muhim: Poisson bo'lganda p-value soxta kichik bo'lardi.
    """
    rng = np.random.default_rng(101)
    # NB2: mean ~ 5, varians ~ 5 + 5^2/2 -> aniq overdispersed
    ya = rng.negative_binomial(2, 2 / 7, 60)
    yb = rng.negative_binomial(2, 2 / 7, 60)
    res = S.negative_binomial_rate_test(ya, 1.0, yb, 1.0, n_boot=300, rng=2)

    assert res.dispersion > 1.5, f"phi = {res.dispersion} overdispersion'ni sezmadi"
    poisson_se = math.sqrt(1.0 / ya.sum() + 1.0 / yb.sum())
    assert res.log_rr_std_err > poisson_se
    assert res.log_rr_std_err == pytest.approx(
        math.sqrt(res.dispersion) * poisson_se, rel=1e-12
    )


def test_rate_test_dispersion_is_near_one_for_poisson_counts():
    rng = np.random.default_rng(202)
    ya = rng.poisson(8.0, 300)
    yb = rng.poisson(8.0, 300)
    res = S.negative_binomial_rate_test(ya, 1.0, yb, 1.0, n_boot=200, rng=3)
    assert 1.0 <= res.dispersion < 1.3


def test_rate_test_respects_exposure():
    """`loop_rate = Delta NRestarts / T_trial` -- exposure bo'linishi to'g'ri."""
    res = S.negative_binomial_rate_test([6] * 5, 2.0, [3] * 5, 1.0, n_boot=200, rng=1)
    assert res.rate_a == pytest.approx(3.0)  # 30 / 10
    assert res.rate_b == pytest.approx(3.0)  # 15 / 5
    assert res.rate_ratio == pytest.approx(1.0)
    assert res.p_value == pytest.approx(1.0)


def test_rate_test_bootstrap_difference_ci_brackets_observed_difference():
    rng = np.random.default_rng(303)
    ya = rng.poisson(6.0, 60)
    yb = rng.poisson(2.0, 60)
    res = S.negative_binomial_rate_test(ya, 1.0, yb, 1.0, n_boot=1500, rng=4)
    assert res.diff_lower <= res.rate_difference <= res.diff_upper
    assert res.diff_lower > 0.0  # rate_a aniq kattaroq


def test_rate_test_zero_count_group_is_nan_not_silent():
    """Bitta guruhda count 0 -> log RR aniqlanmagan. NaN, soxta raqam emas."""
    res = S.negative_binomial_rate_test([2, 3, 1], 1.0, [0, 0, 0], 1.0, n_boot=200, rng=1)
    assert math.isnan(res.statistic)
    assert math.isnan(res.p_value)
    assert res.rate_b == 0.0
    # bootstrap farqi hali ma'noli
    assert res.diff_lower > 0.0


def test_rate_test_rejects_invalid_input():
    with pytest.raises(ValueError, match="uzunligi teng"):
        S.negative_binomial_rate_test([1, 2], [1.0, 1.0, 1.0], [1], 1.0)
    with pytest.raises(ValueError, match="manfiy bo'lmagan"):
        S.negative_binomial_rate_test([-1, 2], 1.0, [1, 1], 1.0)
    with pytest.raises(ValueError, match="exposure musbat"):
        S.negative_binomial_rate_test([1, 2], 0.0, [1, 1], 1.0)
    with pytest.raises(ValueError, match="bo'sh namuna"):
        S.negative_binomial_rate_test([], 1.0, [1, 1], 1.0)


# ===========================================================================
# 11. Holm-Bonferroni
# ===========================================================================


def test_holm_matches_blakesley_table_1():
    """[B] Blakesley va boshq. (2009), Neuropsychology 23(2):255-264, Table 1.

    NASHR ETILGAN qator (Observed -> Holm):
        0.3587 -> 0.4096
        0.1663 -> 0.4096
        0.1365 -> 0.4096
        0.0117 -> 0.0470

    OGOHLIK: manba kuzatilgan p'larni 4 kasr xonaga yumaloqlagan. Shu
    yumaloqlangan p'lardan aniq Holm arifmetikasi 4*0.0117 = 0.0468 va
    3*0.1365 = 0.4095 beradi. Nashr etilgan 0.0470 / 0.4096 yumaloqlanmagan
    p'lardan kelgan (Bonferroni ustuni ham xuddi shunday 0.0470 ni beradi).
    Shuning uchun tolerans 3e-4.
    """
    observed = [0.3587, 0.1663, 0.1365, 0.0117]
    published_holm = [0.4096, 0.4096, 0.4096, 0.0470]

    res = S.holm_bonferroni(observed, alpha=0.05)

    np.testing.assert_allclose(res.adjusted, published_holm, atol=3e-4)
    assert list(res.reject) == [False, False, False, True]
    assert res.n_tests == 4

    # Manbaning Bonferroni ustuni: 1.0000, 0.6653, 0.5462, 0.0470 -- Holm
    # hech qachon Bonferroni'dan katta bo'lmasligini tekshiradi.
    bonferroni = np.minimum(np.asarray(observed) * 4, 1.0)
    assert np.all(res.adjusted <= bonferroni + 1e-12)
    np.testing.assert_allclose(bonferroni, [1.0000, 0.6653, 0.5462, 0.0468], atol=3e-4)


def test_holm_adjusted_p_values_are_monotone_in_the_sorted_order():
    rng = np.random.default_rng(77)
    for _ in range(50):
        p = rng.random(8)
        adj = S.holm_bonferroni(p).adjusted
        order = np.argsort(p, kind="stable")
        assert np.all(np.diff(adj[order]) >= -1e-15)


def test_holm_is_never_weaker_than_bonferroni():
    rng = np.random.default_rng(78)
    for _ in range(50):
        p = rng.random(6)
        adj = S.holm_bonferroni(p).adjusted
        bonf = np.minimum(p * p.size, 1.0)
        assert np.all(adj <= bonf + 1e-12)


def test_holm_single_test_is_the_identity():
    res = S.holm_bonferroni([0.031])
    assert res.adjusted[0] == pytest.approx(0.031)
    assert bool(res.reject[0]) is True


def test_holm_controls_fwer_under_complete_null():
    """XUSUSIYAT: barcha null rost bo'lsa, family-wise xato darajasi <= alpha.

    Mustaqil U(0,1) p-value'lar (to'liq null). 3000 takrorlash, m = 4,
    alpha = 0.05. Monte Carlo SE ~ 0.004, shuning uchun chegara 0.065.
    """
    rng = np.random.default_rng(4242)
    alpha = 0.05
    reps = 3000
    family_errors = 0
    for _ in range(reps):
        p = rng.random(4)
        if np.any(S.holm_bonferroni(p, alpha=alpha).reject):
            family_errors += 1
    fwer = family_errors / reps
    assert fwer <= 0.065, f"FWER {fwer} > alpha {alpha}"
    # Holm konservativ bo'lmasligini ham tekshiramiz (Bonferroni'ga yaqin)
    assert fwer >= 0.03


def test_holm_rejects_invalid_input():
    with pytest.raises(ValueError, match="bo'sh"):
        S.holm_bonferroni([])
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        S.holm_bonferroni([0.5, 1.5])
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        S.holm_bonferroni([0.5, float("nan")])
    with pytest.raises(ValueError, match="alpha"):
        S.holm_bonferroni([0.5], alpha=1.5)


# ===========================================================================
# 12. Pre-registration muvofiqligi -- §10.2 taqiqlari kodda ham bajarilgan
# ===========================================================================


def test_module_exposes_no_ttest_and_no_cox_hazard_ratio():
    """§10.2: t-test ISHLATILMAYDI, Cox / hazard ratio ISHLATILMAYDI.

    Eng ishonchli kafolat -- bu funksiyalar modulda MAVJUD BO'LMASLIGI.
    Bu test kelajakda kimdir "qulaylik uchun" qo'shib qo'yishini ushlaydi.
    """
    banned = ("ttest", "t_test", "cox", "hazard_ratio", "hazardratio", "mean_sd")
    public = [n for n in dir(S) if not n.startswith("_")]
    for name in public:
        low = name.lower()
        for bad in banned:
            assert bad not in low, f"taqiqlangan API: {name} (§10.2)"


def test_all_public_functions_have_docstrings_with_validity_limits():
    """§ dizayn qoidasi 4: har bir public funksiya QACHON YAROQSIZ ni aytadi."""
    import inspect

    for name in S.__all__:
        obj = getattr(S, name)
        if not inspect.isfunction(obj):
            continue  # dataclass'lar
        doc = obj.__doc__ or ""
        assert len(doc) > 200, f"{name}: docstring juda qisqa"
        assert "QACHON YAROQSIZ" in doc or "VALIDATSIYA" in doc, (
            f"{name}: docstring yaroqsizlik shartlarini yoki validatsiyani aytmaydi"
        )
