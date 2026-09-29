"""REVIX statistik moduli -- PREREGISTRATION.md §10 ning bajarilishi.

Bu modul `statsmodels` va `lifelines`ga TAYANMAYDI. Faqat `numpy` va `scipy`.
Sabab pre-registration §10.3 da muzlatilgan: self-contained artifact reviewer
uchun tejalgan mehnatdan qimmatroq. Har bir estimator NASHR ETILGAN ishlangan
misolga qarshi test qilinadi -- `tests/unit/test_stats.py`.

DIZAYN QOIDALARI (buzilmaydi):
  1. Pre-registration §10 -- SPETSIFIKATSIYA. Bu modul unga xizmat qiladi,
     uni qayta talqin qilmaydi.
  2. `t-test` YO'Q. `mean ± SD` YO'Q. Recovery-time taqsimotlari og'ir dumli,
     ehtimol bimodal va o'ngdan censored -- §10.2.
  3. Cox / hazard ratio YO'Q. Bu modulda Cox regressiyasi ATAYIN yo'q, chunki
     proportional hazards deyarli aniq buziladi (fiksa restart kechikishlari
     step hazard yaratadi). HR bermaslikning eng ishonchli yo'li -- uni
     hisoblay olmaslik.
  4. Har bir public funksiya: nima hisoblaydi, qanday farazlarga tayanadi,
     QACHON YAROQSIZ, va qaysi nashr etilgan misolga qarshi tekshirilgan.
  5. Censoring tashlanmaydi -- §6.2. KM/log-rank/RMST uni to'g'ri ishlaydi.

VALIDATSIYA HOLATI (halol bayon -- batafsili test faylida):
  * validated: cochran_armitage_trend, clopper_pearson, wilson_ci,
    newcombe_diff_ci, kaplan_meier (Greenwood bilan), km_quantile, logrank,
    holm_bonferroni.
  * qisman validated: rmst / rmst_difference -- nuqtaviy baho nashr etilgan KM
    jadvali ostidagi yuza bilan tekshirilgan, LEKIN standard error uchun
    nashr etilgan raqamli misol topilmadi.
  * scipy'ga suyanadi (mustaqil implementatsiyaga qarshi cross-check):
    cliffs_delta, bootstrap_ci, fisher_exact_2x2, mann_whitney_u,
    kruskal_wallis.
  * VALIDATED EMAS: negative_binomial_rate_test -- nashr etilgan ishlangan
    misol topilmadi. O'z docstring'ida ochiq belgilangan.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np
from scipy import stats

__all__ = [
    # proporsiyalar / trend -- H1
    "ProportionCI",
    "RiskDifferenceCI",
    "TrendResult",
    "FisherResult",
    "clopper_pearson",
    "wilson_ci",
    "newcombe_diff_ci",
    "cochran_armitage_trend",
    "fisher_exact_2x2",
    # survival -- H2
    "KMResult",
    "LogRankResult",
    "RMSTResult",
    "RMSTDifference",
    "kaplan_meier",
    "km_quantile",
    "logrank",
    "rmst",
    "rmst_difference",
    # nonparametrik effect size
    "BootstrapCI",
    "CliffsDelta",
    "bootstrap_ci",
    "cliffs_delta",
    "mann_whitney_u",
    "kruskal_wallis",
    # count'lar
    "RateTestResult",
    "negative_binomial_rate_test",
    # multiplicity
    "HolmResult",
    "holm_bonferroni",
]


# --- ichki yordamchilar ------------------------------------------------------


def _as_surv(times, events) -> tuple[np.ndarray, np.ndarray]:
    """`(times, events)` ni tekshiradi va float/int massivlarga aylantiradi.

    `events`: 1 = event (masalan VR yuz berdi), 0 = right-censored.
    """
    t = np.asarray(times, dtype=float).ravel()
    e = np.asarray(events, dtype=float).ravel()
    if t.size != e.size:
        raise ValueError(f"times va events uzunligi teng bo'lishi kerak: {t.size} != {e.size}")
    if t.size == 0:
        raise ValueError("bo'sh namuna")
    if not np.all(np.isfinite(t)):
        raise ValueError("times ichida NaN/inf bor -- censoring 0/1 event flag bilan beriladi")
    if np.any(t < 0):
        raise ValueError("times manfiy bo'lishi mumkin emas")
    if not np.all(np.isin(e, (0.0, 1.0))):
        raise ValueError("events faqat 0 (censored) yoki 1 (event) bo'lishi kerak")
    return t, e.astype(int)


def _z(alpha: float) -> float:
    """Ikki tomonlama `alpha` uchun normal kvantil. `alpha` tekshiriladi."""
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha (0, 1) oralig'ida bo'lishi kerak, berilgani: {alpha}")
    return float(stats.norm.isf(alpha / 2.0))


def _check_count(k: int, n: int) -> tuple[int, int]:
    k, n = int(k), int(n)
    if n <= 0:
        raise ValueError(f"n > 0 bo'lishi kerak, berilgani: {n}")
    if not 0 <= k <= n:
        raise ValueError(f"0 <= k <= n bo'lishi kerak, berilgani: k={k}, n={n}")
    return k, n


# --- natija tiplari ---------------------------------------------------------


@dataclass(frozen=True)
class ProportionCI:
    """Bitta proporsiya va uning confidence interval'i."""

    estimate: float
    lower: float
    upper: float
    k: int
    n: int
    alpha: float
    method: str


@dataclass(frozen=True)
class RiskDifferenceCI:
    """Risk difference (p1 - p2) va uning confidence interval'i."""

    difference: float
    lower: float
    upper: float
    p1: float
    p2: float
    alpha: float
    method: str


@dataclass(frozen=True)
class TrendResult:
    """Cochran-Armitage trend testi natijasi."""

    statistic: float  # z (belgisi bilan -- yo'nalishni saqlaydi)
    chi2: float  # z**2, 1 df
    p_value: float  # ikki tomonlama
    direction: str  # "increasing" | "decreasing" | "flat"
    scores: np.ndarray = field(repr=False)
    proportions: np.ndarray = field(repr=False)


@dataclass(frozen=True)
class FisherResult:
    """Fisher exact testi (2x2) natijasi."""

    odds_ratio: float
    p_value: float
    alternative: str


@dataclass(frozen=True)
class KMResult:
    """Kaplan-Meier step funksiyasi.

    Massivlar UNIKAL EVENT vaqtlari bo'yicha, o'sish tartibida. Censoring
    vaqtlari qatorda ko'rinmaydi, lekin `at_risk` ni to'g'ri kamaytiradi.
    """

    times: np.ndarray  # unikal event vaqtlari
    survival: np.ndarray  # S(t) shu vaqtlarda (event'dan KEYIN)
    at_risk: np.ndarray  # n_i -- t_i dan sal oldin risk ostidagilar
    n_events: np.ndarray  # d_i
    variance: np.ndarray  # Greenwood var(S(t_i))
    std_err: np.ndarray  # sqrt(variance)
    n_total: int
    n_censored: int

    def survival_at(self, t: float) -> float:
        """`S(t)` -- step funksiya, o'ngdan uzluksiz (`t_i <= t` bo'yicha ko'paytma).

        `t` birinchi event'dan oldin bo'lsa 1.0 qaytaradi.
        """
        idx = int(np.searchsorted(self.times, float(t), side="right"))
        return 1.0 if idx == 0 else float(self.survival[idx - 1])


@dataclass(frozen=True)
class LogRankResult:
    """Log-rank testi natijasi (2 guruh, 1 df)."""

    statistic: float  # chi-square
    p_value: float
    observed_a: float
    expected_a: float
    observed_b: float
    expected_b: float
    variance: float  # sum v_j (hypergeometric)


@dataclass(frozen=True)
class RMSTResult:
    """Restricted mean survival time, `tau` horizon'igacha."""

    rmst: float
    std_err: float
    variance: float
    tau: float
    n_events_used: int


@dataclass(frozen=True)
class RMSTDifference:
    """RMST farqi (A - B) -- H2 uchun BOSH effect measure."""

    difference: float
    std_err: float
    lower: float
    upper: float
    p_value: float
    tau: float
    rmst_a: RMSTResult
    rmst_b: RMSTResult


@dataclass(frozen=True)
class BootstrapCI:
    """Bootstrap confidence interval."""

    estimate: float
    lower: float
    upper: float
    alpha: float
    n_boot: int
    method: str  # haqiqatda ishlatilgan metod ("bca" yoki "percentile")
    method_requested: str


@dataclass(frozen=True)
class CliffsDelta:
    """Cliff's delta va uning bootstrap CI'si."""

    delta: float
    lower: float
    upper: float
    a12: float  # Vargha-Delaney A12 = (delta + 1) / 2
    alpha: float
    n_boot: int
    method: str


@dataclass(frozen=True)
class RateTestResult:
    """Overdispersion'ga chidamli rate taqqoslash natijasi."""

    rate_a: float
    rate_b: float
    rate_ratio: float
    rate_difference: float
    dispersion: float  # Pearson phi (quasi-Poisson)
    statistic: float  # log(RR) uchun z
    p_value: float
    log_rr_std_err: float
    rr_lower: float
    rr_upper: float
    diff_lower: float  # bootstrap
    diff_upper: float
    n_boot: int
    model: str


@dataclass(frozen=True)
class HolmResult:
    """Holm-Bonferroni ko'p testli tuzatish."""

    adjusted: np.ndarray
    reject: np.ndarray
    alpha: float
    n_tests: int


# --- 1. Proporsiyalar va trend (H1 birlamchi endpoint) ----------------------


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> ProportionCI:
    """Clopper-Pearson EXACT binomial confidence interval (har yacheyka uchun).

    PREREGISTRATION.md §10.1: "Har yacheyka proporsiyasi uchun Clopper-Pearson
    exact CI".

    NIMA HISOBLAYDI. Ikki bir tomonlama exact binomial testni invertiradi:
        lower  L: P(X >= k | p = L) = alpha/2
        upper  U: P(X <= k | p = U) = alpha/2
    Bu Beta kvantillari orqali yopiq ko'rinishda yechiladi:
        L = Beta(alpha/2; k, n-k+1),   U = Beta(1-alpha/2; k+1, n-k)
    Chegara holatlari: k = 0 -> L = 0, k = n -> U = 1.

    FARAZLAR. n ta mustaqil Bernoulli sinov, o'zgarmas p. REVIX'da bu har bir
    (arm, pressure strata) yacheykasi ichida randomizatsiya va washout
    tufayli maqbul -- §8.4.

    QACHON YAROQSIZ.
      * Trial'lar bir-biriga bog'liq bo'lsa (masalan page cache warm/cold
        oqishi -- §8.3). Unda blok ichida hisoblanadi, blokdan kesib o'tmaydi.
      * Bu interval KONSERVATIV: haqiqiy coverage >= 1-alpha, odatda kattaroq.
        Shuning uchun u NUQTAVIY bahoning aniqligini ko'rsatadi, hipoteza
        testi sifatida ishlatilmaydi (test uchun Fisher / Cochran-Armitage).
      * Risk difference uchun ISHLATILMAYDI -- `newcombe_diff_ci` ga qarang.

    VALIDATSIYA. Clopper, C.J. & Pearson, E.S. (1934), Biometrika 26:404-413 --
    ta'rif bo'yicha: test binomial dum ehtimolliklari aynan alpha/2 ga
    tengligini tekshiradi. Qo'shimcha: k=0 uchun yopiq shakl
    U = 1 - (alpha/2)^(1/n) (n=20, alpha=0.05 -> 0.168433).
    """
    k, n = _check_count(k, n)
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha (0, 1) oralig'ida bo'lishi kerak, berilgani: {alpha}")
    lo = 0.0 if k == 0 else float(stats.beta.ppf(alpha / 2.0, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))
    return ProportionCI(
        estimate=k / n, lower=lo, upper=hi, k=k, n=n, alpha=alpha, method="clopper-pearson"
    )


def wilson_ci(k: int, n: int, alpha: float = 0.05) -> ProportionCI:
    """Wilson score confidence interval bitta proporsiya uchun.

    NIMA HISOBLAYDI. Score (Rao) testini invertiradi:
        centre = (k + z^2/2) / (n + z^2)
        half   = z * sqrt( n*p*(1-p) + z^2/4 ) / (n + z^2)
    bu yerda p = k/n, z = normal (1-alpha/2) kvantili.

    NEGA KERAK. Bu `newcombe_diff_ci` ning QURILISH BLOKI. Wald interval'dan
    farqli: [0, 1] dan chiqmaydi, k = 0 yoki k = n da ham yig'ilib qolmaydi.

    QACHON YAROQSIZ. Juda kichik n va ekstremal p da coverage tebranadi
    (diskretlik). Yacheykani HISOBOT qilish uchun §10.1 Clopper-Pearson'ni
    talab qiladi; Wilson bu yerda faqat risk difference uchun oraliq qadam.

    VALIDATSIYA. Wilson, E.B. (1927), JASA 22:209-212. Formula ko'rinishi:
    Fagerland, M.W., Lydersen, S. & Laake, P. (2011), "Recommended confidence
    intervals for two independent binomial proportions", Statistical Methods in
    Medical Research 20(1):3-40, §4.2.3. Raqamli tekshiruv `newcombe_diff_ci`
    testi orqali (Wilson chegaralari unga to'g'ridan-to'g'ri kiradi).
    """
    k, n = _check_count(k, n)
    z = _z(alpha)
    p = k / n
    denom = n + z * z
    centre = (k + z * z / 2.0) / denom
    half = z * math.sqrt(n * p * (1.0 - p) + z * z / 4.0) / denom
    return ProportionCI(
        estimate=p,
        lower=max(0.0, centre - half),
        upper=min(1.0, centre + half),
        k=k,
        n=n,
        alpha=alpha,
        method="wilson-score",
    )


def newcombe_diff_ci(
    k1: int, n1: int, k2: int, n2: int, alpha: float = 0.05
) -> RiskDifferenceCI:
    """Newcombe/Wilson-score CI RISK DIFFERENCE (p1 - p2) uchun.

    PREREGISTRATION.md §10.1: "Effect size: risk difference + Newcombe/Wilson-score
    CI (birlamchi, downtime argumenti uchun eng talqin qilinadigan)". §11 ning
    falsifikatsiya sharti aynan bu interval'ning YUQORI chegarasiga bog'liq,
    demak bu funksiya xato bo'lsa, falsifikatsiya qaroriga ham xato tushadi.

    NIMA HISOBLAYDI. Bu NAIVE WALD INTERVAL EMAS. Har bir proporsiya uchun
    Wilson score interval (l_i, u_i) olinadi va "square-and-add" (MOVER)
    usulida birlashtiriladi:
        lower = (p1 - p2) - sqrt( (p1 - l1)^2 + (u2 - p2)^2 )
        upper = (p1 - p2) + sqrt( (p2 - l2)^2 + (u1 - p1)^2 )
    E'tibor bering: chap chegara p1 ning CHAP masofasi va p2 ning O'NG
    masofasini oladi (va aksincha). Bu almashtirish -- metodning mohiyati.

    FARAZLAR. Ikki MUSTAQIL binomial namuna. REVIX'da pressure stratalari
    alohida trial'lar, demak mustaqil.

    QACHON YAROQSIZ.
      * Paired/matched dizaynda (bir xil blok ichida bir xil SUT instansi
        takroran o'lchansa) -- bu holda Newcombe'ning PAIRED metodi kerak,
        bu funksiya emas.
      * Interval [-1, 1] dan chiqmaydi, lekin p1 = p2 = 0 yoki 1 bo'lganda
        juda keng bo'ladi -- bu to'g'ri xatti-harakat, yashirilmaydi.

    VALIDATSIYA. Newcombe, R.G. (1998), "Interval estimation for the difference
    between independent proportions: comparison of eleven methods", Statistics
    in Medicine 17:873-890 -- "method 10" (score, continuity correction'siz).
    Formula va raqamli misol: Fagerland, Lydersen & Laake (2011), Statistical
    Methods in Medical Research 20(1):3-40, §4.2.3 tenglama (7) va Table 3
    (Perondi va boshq. 2004 ma'lumotlari, 7/34 vs 1/34): difference 0.18,
    95% CI (0.019, 0.34).
    """
    k1, n1 = _check_count(k1, n1)
    k2, n2 = _check_count(k2, n2)
    p1, p2 = k1 / n1, k2 / n2
    w1 = wilson_ci(k1, n1, alpha)
    w2 = wilson_ci(k2, n2, alpha)
    diff = p1 - p2
    lo = diff - math.hypot(p1 - w1.lower, w2.upper - p2)
    hi = diff + math.hypot(p2 - w2.lower, w1.upper - p1)
    return RiskDifferenceCI(
        difference=diff,
        lower=max(-1.0, lo),
        upper=min(1.0, hi),
        p1=p1,
        p2=p2,
        alpha=alpha,
        method="newcombe-score",
    )


def cochran_armitage_trend(
    successes: Sequence[int],
    totals: Sequence[int],
    scores: Sequence[float] | None = None,
) -> TrendResult:
    """Cochran-Armitage trend testi -- H1 UCHUN BIRLAMCHI TEST.

    PREREGISTRATION.md §10.1: "Birlamchi test: Cochran-Armitage trend testi
    P0 < P1 < P2 bo'ylab. Sabab: tartibni ishlatadi (pairwise'dan ancha
    kuchli), va 'P(VR) pressure bilan monoton kamayadi' -- 'yuqori < past' dan
    kuchliroq, ko'proq falsifiable da'vo."

    NIMA HISOBLAYDI. Tartiblangan exposure darajalariga `scores` (s_i) beriladi
    va muvaffaqiyat proporsiyasining shu score'lar bo'ylab CHIZIQLI trendi
    tekshiriladi:
        N = sum n_i,  K = sum k_i,  p = K / N
        T   = sum s_i * (k_i - n_i * p)
        Sxx = sum n_i * s_i^2 - (sum n_i * s_i)^2 / N
        Var = p * (1 - p) * Sxx
        z   = T / sqrt(Var),   chi2 = z^2  (1 df)
    `scores=None` bo'lsa teng masofali 0, 1, 2, ... ishlatiladi.
    `z` BELGISI saqlanadi: z > 0 -> proporsiya score bilan O'SADI.

    FARAZLAR.
      * Darajalar TARTIBLANGAN va `scores` bu tartibning mazmunli masshtabini
        beradi. Score tanlovi natijaga TA'SIR QILADI -- shuning uchun REVIX'da
        score'lar oldindan (pre-registration'da) belgilanadi, ma'lumotdan keyin
        tanlanmaydi.
      * Har yacheyka ichida mustaqil Bernoulli sinovlar.
      * Asimptotik normal taqsimot. Kichik n da p-value taxminiy.

    QACHON YAROQSIZ.
      * Trend MONOTON lekin chiziqli bo'lmasa (masalan P0 = P1 >> P2) test
        kuchini yo'qotadi -- lekin darajani buzmaydi.
      * Trend NOMONOTON bo'lsa (V shakli) test null'ni topmaydi va bu ATAYIN:
        §10.1 chiziqli trend da'vosini sinaydi, "biror farq bor" ni emas.
      * 3 dan kam daraja bo'lsa trend testi ma'nosiz -- bu funksiya xato
        qaytaradi. 2x2 uchun `fisher_exact_2x2` ishlatiladi (§10.1).
      * `n_i` juda kichik bo'lsa (yacheykada 5 dan kam kutilgan event) exact
        permutatsiya varianti kerak. P1 da n = 20/daraja -- asimptotik
        yaqinlashish maqbul, lekin bu ADMITTED limitation.

    VALIDATSIYA. Armitage, P. (1955), Biometrics 11:375-386; Cochran, W.G.
    (1954), Biometrics 10:417-451. Raqamli misol: Agresti, A., "An Introduction
    to Categorical Data Analysis", 2-nashr, §2.5.2, Table 2.7 (Graubard & Korn
    1987, ona alkogol iste'moli va chaqaloq malformatsiyasi), score'lar
    (0, 0.5, 1.5, 4.0, 7.0): nashr etilgan r = 0.0142, M = 2.56,
    M^2 = 6.6, P = 0.01.
    """
    k = np.asarray(successes, dtype=float).ravel()
    n = np.asarray(totals, dtype=float).ravel()
    if k.size != n.size:
        raise ValueError(f"successes va totals uzunligi teng bo'lishi kerak: {k.size} != {n.size}")
    if k.size < 3:
        raise ValueError(
            "trend testi uchun kamida 3 tartiblangan daraja kerak "
            f"(berilgani: {k.size}); 2x2 uchun fisher_exact_2x2 ishlatiladi"
        )
    if np.any(n <= 0):
        raise ValueError("har bir darajada totals > 0 bo'lishi kerak")
    if np.any(k < 0) or np.any(k > n):
        raise ValueError("0 <= successes <= totals bo'lishi kerak")

    if scores is None:
        s = np.arange(k.size, dtype=float)
    else:
        s = np.asarray(scores, dtype=float).ravel()
        if s.size != k.size:
            raise ValueError(f"scores uzunligi darajalar soniga teng bo'lishi kerak: {s.size} != {k.size}")
    if np.unique(s).size < 2:
        raise ValueError("scores kamida ikki xil qiymatga ega bo'lishi kerak")

    N = float(n.sum())
    K = float(k.sum())
    pbar = K / N
    if pbar in (0.0, 1.0):
        # Hamma yacheyka bir xil -- trend aniqlanmaydi. Yashirmaymiz.
        raise ValueError(
            "barcha darajalarda proporsiya bir xil (0 yoki 1) -- trend testi aniqlanmagan"
        )
    T = float(np.sum(s * (k - n * pbar)))
    sxx = float(np.sum(n * s * s) - (np.sum(n * s) ** 2) / N)
    var = pbar * (1.0 - pbar) * sxx
    if var <= 0.0:
        raise ValueError("trend statistikasining variansi nolga teng -- score'lar degenerativ")
    z = T / math.sqrt(var)
    chi2 = z * z
    p = float(2.0 * stats.norm.sf(abs(z)))
    if z > 0:
        direction = "increasing"
    elif z < 0:
        direction = "decreasing"
    else:
        direction = "flat"
    return TrendResult(
        statistic=z,
        chi2=chi2,
        p_value=p,
        direction=direction,
        scores=s,
        proportions=k / n,
    )


def fisher_exact_2x2(
    k1: int, n1: int, k2: int, n2: int, alternative: str = "two-sided"
) -> FisherResult:
    """Fisher exact testi 2x2 jadval uchun -- `scipy.stats.fisher_exact` ustida yupqa qobiq.

    PREREGISTRATION.md §10.1: "2x2 uchun Fisher exact (yoki ko'proq power uchun
    Barnard)". Bu qobiq (k, n) juftliklarini 2x2 jadvalga aylantiradi, chunki
    harness ma'lumotni shu ko'rinishda beradi:
        [[k1, n1-k1], [k2, n2-k2]]

    FARAZLAR. Mustaqil namunalar; marginal'lar shartlangan (conditional exact).

    QACHON YAROQSIZ.
      * >2 daraja bo'lsa ishlatilmaydi -- H1 birlamchi testi
        `cochran_armitage_trend`.
      * Fisher exact KONSERVATIV (marginal'larni shartlaydi). §10.1 Barnard'ni
        ko'proq power uchun eslatadi; u bu modulda YO'Q va bu ochiq cheklov.

    VALIDATSIYA. `scipy.stats.fisher_exact` -- scipy'ning o'z test suite'i.
    Bu yerda faqat shakl o'zgartiriladi, statistika qayta yozilmaydi.
    """
    k1, n1 = _check_count(k1, n1)
    k2, n2 = _check_count(k2, n2)
    table = [[k1, n1 - k1], [k2, n2 - k2]]
    res = stats.fisher_exact(table, alternative=alternative)
    return FisherResult(
        odds_ratio=float(res.statistic), p_value=float(res.pvalue), alternative=alternative
    )


# --- 2. Survival (H2 / downtime, right censoring bilan) ---------------------


def kaplan_meier(times, events) -> KMResult:
    """Kaplan-Meier product-limit estimator + GREENWOOD variansi.

    PREREGISTRATION.md §10.2: "Birlamchi: Kaplan-Meier time-to-VR har arm
    uchun ... censoring'ni to'g'ri ishlaydigan yagona oila." §6.2: censored
    trial'lar analizga KIRADI, tashlanmaydi.

    NIMA HISOBLAYDI. Unikal event vaqtlari t_1 < ... < t_m bo'yicha:
        S(t) = prod_{t_i <= t} (1 - d_i / n_i)
    bu yerda n_i = t_i dan sal OLDIN risk ostidagilar soni (ya'ni
    `times >= t_i`), d_i = t_i dagi event'lar soni (ties to'g'ri ishlanadi).
    Greenwood variansi:
        var(S(t)) = S(t)^2 * sum_{t_i <= t} d_i / (n_i * (n_i - d_i))

    KONVENSIYA (ochiq e'lon qilinadi). Oxirgi event vaqtida n_i == d_i
    bo'lsa Greenwood hadi 0/0 ga aylanadi. Bu holda had 0 deb olinadi,
    demak S = 0 nuqtasida std_err = 0. Bu "0 * inf -> 0" yechimi; muqobil
    konvensiya NaN berardi. Interval'lar shu nuqtada MA'NOSIZ -- ishlatilmaydi.

    FARAZLAR.
      * Censoring NONINFORMATIVE: censor bo'lish ehtimoli survival vaqtiga
        bog'liq emas. REVIX'da censoring MEXANIK -- horizon T_trial tugaydi
        (§6.2) -- demak administrative censoring, bu faraz maqbul.
      * Trial'lar mustaqil.

    QACHON YAROQSIZ.
      * Censoring informative bo'lsa (masalan guard aynan sekin recovery'larda
        trip qilsa). Shuning uchun §12 `aborted_guard` ni ALOHIDA disposition
        qiladi va birlamchi analizdan chiqaradi -- lekin ulushi beriladi.
      * Left truncation / interval censoring bu implementatsiyada YO'Q.
      * Event va censoring bir xil vaqtga tushsa, konvensiya: event OLDIN
        (censored kuzatuv shu vaqtda risk ostida hisoblanadi). Bu standart
        konvensiya, `D_probe` kvantlanishi (±P, §6.1) uni muhim qiladi.

    VALIDATSIYA. Kaplan, E.L. & Meier, P. (1958), JASA 53:457-481; Greenwood, M.
    (1926). Raqamli misol: Farrow, M., "MAS3301/MAS8311 Biostatistics Part II:
    Survival", Newcastle University, 2009-10, §5.2 (Woolson & Lachenbruch 1980
    skin-graft ma'lumotlari, n=11): nashr etilgan S = 0.909, 0.818, 0.636,
    0.545, 0.455, 0.364, 0.182, 0.000; Greenwood yig'indisi t=22 gacha
    0.0758; se[S(25)] = 0.150.
    """
    t, e = _as_surv(times, events)
    ev_times = np.unique(t[e == 1])
    m = ev_times.size
    surv = np.empty(m)
    at_risk = np.empty(m, dtype=np.int64)
    n_ev = np.empty(m, dtype=np.int64)
    gw = np.empty(m)  # Greenwood kumulyativ yig'indisi

    s = 1.0
    acc = 0.0
    for i, u in enumerate(ev_times):
        n_i = int(np.count_nonzero(t >= u))
        d_i = int(np.count_nonzero((t == u) & (e == 1)))
        s *= 1.0 - d_i / n_i
        if n_i > d_i:
            acc += d_i / (n_i * (n_i - d_i))
        # n_i == d_i bo'lsa had 0/0 -> 0 (yuqoridagi KONVENSIYA)
        surv[i] = s
        at_risk[i] = n_i
        n_ev[i] = d_i
        gw[i] = acc

    var = surv**2 * gw
    return KMResult(
        times=ev_times,
        survival=surv,
        at_risk=at_risk,
        n_events=n_ev,
        variance=var,
        std_err=np.sqrt(var),
        n_total=int(t.size),
        n_censored=int(np.count_nonzero(e == 0)),
    )


def km_quantile(km: KMResult, q: float = 0.5) -> float:
    """KM egri chizig'idan `q`-kvantil (standart konvensiya).

    `q = 0.5` -> median survival time: `S(t) <= 1 - q` bo'ladigan eng KICHIK
    kuzatilgan event vaqti. Egri chiziq `1 - q` gacha tushmasa `nan`
    qaytaradi -- bu "median aniqlanmagan" ning halol ifodasi, oxirgi
    kuzatilgan vaqtni median deb ko'rsatish EMAS.

    FARAZLAR / QACHON YAROQSIZ. `kaplan_meier` bilan bir xil. Og'ir censoring
    ostida yuqori kvantillar (p90, p99) ko'pincha aniqlanmaydi -- shuning
    uchun §10.2 ularni censored BO'LMAGAN qism ustida bootstrap bilan
    so'raydi (`bootstrap_ci`), KM'dan emas.

    VALIDATSIYA. Farrow (2009-10) §5.3, skin-graft misoli: nashr etilgan
    median = 29 kun. Freireich va boshq. (1963) 6-MP ma'lumotlari: nashr
    etilgan median remission 23 hafta (6-MP) va 8 hafta (placebo).
    """
    if not 0.0 < q < 1.0:
        raise ValueError(f"q (0, 1) oralig'ida bo'lishi kerak, berilgani: {q}")
    target = 1.0 - q
    hit = np.nonzero(km.survival <= target + 1e-12)[0]
    if hit.size == 0:
        return float("nan")
    return float(km.times[hit[0]])


def logrank(times_a, events_a, times_b, events_b) -> LogRankResult:
    """Log-rank (Mantel-Cox) testi -- ikki survival taqsimotini taqqoslash.

    PREREGISTRATION.md §10.2: KM + log-rank -- birlamchi oila.

    NIMA HISOBLAYDI. Birlashgan unikal event vaqtlari t_j bo'yicha
    2x2 jadvallar ketma-ketligi (Mantel-Haenszel). Har t_j da:
        n_aj, n_bj -- risk ostidagilar; d_j = d_aj + d_bj
        e_aj = d_j * n_aj / n_j                      (kutilgan)
        v_j  = d_j * (n_aj/n_j) * (n_bj/n_j) * (n_j - d_j) / (n_j - 1)
    Statistika:
        chi2 = (O_a - E_a)^2 / sum v_j,   1 df
    `v_j` -- HYPERGEOMETRIC varians (ties uchun to'g'ri). Soddalashtirilgan
    (O-E)^2/E shakli ATAYIN ishlatilmaydi: u konservativ va p-value'ni
    siljitadi.

    FARAZLAR.
      * Noninformative censoring (yuqoriga qarang).
      * Test PROPORTIONAL HAZARDS ostida eng kuchli, LEKIN uni TALAB QILMAYDI:
        null gipoteza "taqsimotlar teng". Non-proportional hazard ostida ham
        DARAJASI to'g'ri, faqat kuchi pasayadi.

    QACHON YAROQSIZ / QANDAY YANGLISHTIRADI.
      * Hazard'lar KESISHSA (crossing survival curves) log-rank haqiqiy
        farqni o'tkazib yuborishi mumkin -- REVIX'da bu EHTIMOLLI, chunki
        fiksa `RestartSec` step hazard yaratadi (§10.2). Shuning uchun
        log-rank yolg'iz ishlatilmaydi: EFFECT MEASURE `rmst_difference`,
        va ECDF'lar to'liq chiziladi.
      * Log-rank p-value EFFECT SIZE bermaydi. Undan hazard ratio
        CHIQARILMAYDI -- §10.2 bo'yicha HR taqiqlangan.
      * Blok effekti bo'lsa stratifikatsiyalangan log-rank kerak; bu
        implementatsiyada YO'Q (§10.2 blok uchun Wilcoxon signed-rank ni
        ham eslatadi).

    VALIDATSIYA. Mantel, N. (1966), Cancer Chemother Rep 50:163-170; Peto &
    Peto (1972), JRSS A 135:185-207.
    Raqamli misol 1: Farrow, M., "MAS3301/MAS8311 Biostatistics Part II:
    Survival", Newcastle University, 2009-10, §6.3: nashr etilgan O1 = 17,
    E1 = 8.5, V = 4.634, W = 15.6.
    Raqamli misol 2: MedCalc statistik dasturi qo'llanmasi (Kaplan-Meier
    sahifasi), Freireich va boshq., Blood 1963;21:699-716 ma'lumotlari:
    nashr etilgan chi-square = 16.79, P < 0.0001, guruhlarda 9 va 21 event.
    """
    ta, ea = _as_surv(times_a, events_a)
    tb, eb = _as_surv(times_b, events_b)
    ev = np.unique(np.concatenate([ta[ea == 1], tb[eb == 1]]))

    obs_a = exp_a = obs_b = exp_b = 0.0
    var = 0.0
    for u in ev:
        n_a = float(np.count_nonzero(ta >= u))
        n_b = float(np.count_nonzero(tb >= u))
        n_j = n_a + n_b
        d_a = float(np.count_nonzero((ta == u) & (ea == 1)))
        d_b = float(np.count_nonzero((tb == u) & (eb == 1)))
        d_j = d_a + d_b
        if d_j == 0.0 or n_j < 2.0:
            # n_j < 2: varians hadi aniqlanmagan, informatsiya ham yo'q.
            continue
        obs_a += d_a
        obs_b += d_b
        exp_a += d_j * n_a / n_j
        exp_b += d_j * n_b / n_j
        var += d_j * (n_a / n_j) * (n_b / n_j) * (n_j - d_j) / (n_j - 1.0)

    if var <= 0.0:
        # Hech qanday informativ event yo'q (masalan bitta guruhda event yo'q
        # va risk to'plamlari kesishmaydi). FAIL-LOUD: NaN qaytaramiz, 1.0 emas.
        return LogRankResult(
            statistic=float("nan"),
            p_value=float("nan"),
            observed_a=obs_a,
            expected_a=exp_a,
            observed_b=obs_b,
            expected_b=exp_b,
            variance=var,
        )
    chi2 = (obs_a - exp_a) ** 2 / var
    return LogRankResult(
        statistic=float(chi2),
        p_value=float(stats.chi2.sf(chi2, 1)),
        observed_a=obs_a,
        expected_a=exp_a,
        observed_b=obs_b,
        expected_b=exp_b,
        variance=float(var),
    )


def _rmst_from_km(km: KMResult, tau: float) -> tuple[float, float, int]:
    """KM natijasidan RMST va uning variansini hisoblaydi. `(rmst, var, k)`."""
    keep = km.times <= tau
    t_keep = km.times[keep]
    s_keep = km.survival[keep]

    # RMST = int_0^tau S(u) du. S [0, t_1) da 1, so'ng har intervalda
    # oxirgi event'dan keyingi qiymat. Step funksiya -- to'rtburchaklar.
    edges = np.concatenate(([0.0], t_keep, [float(tau)]))
    heights = np.concatenate(([1.0], s_keep))
    widths = np.diff(edges)
    area = float(np.sum(heights * widths))

    # Varians (Greenwood asosidagi delta metod):
    #   var(RMST) = sum_{t_i <= tau} A_i^2 * d_i / (n_i * (n_i - d_i))
    # bu yerda A_i = int_{t_i}^{tau} S(u) du.
    # Izoh: heights/edges dan A_i ni kumulyativ ayirish bilan olamiz.
    #   A_i = area - int_0^{t_i} S(u) du   (S(t_i) dan keyingi qiymat bilan)
    cum = np.cumsum(heights * widths)  # int_0^{edges[j+1]}
    var = 0.0
    idx = np.nonzero(keep)[0]
    for j, i in enumerate(idx):
        n_i = float(km.at_risk[i])
        d_i = float(km.n_events[i])
        if n_i <= d_i:
            continue  # 0/0 hadi -- KM'dagi bir xil konvensiya
        a_i = area - float(cum[j])  # int_{t_i}^{tau} S(u) du
        var += a_i * a_i * d_i / (n_i * (n_i - d_i))
    return area, float(var), int(idx.size)


def rmst(times, events, tau: float) -> RMSTResult:
    """Restricted mean survival time (RMST) `tau` horizon'igacha, SE bilan.

    PREREGISTRATION.md §10.2: "Effect measure: RMST difference tau horizon'ga
    qadar -- non-proportional hazard ostida haqiqiy, va to'g'ridan-to'g'ri
    'tau sekund ichida tejalgan kutilgan downtime' sifatida o'qiladi. Bu
    mavjud eng yaxshi statistik tanlov va H2 ga to'g'ridan-to'g'ri javob
    beradi."

    NIMA HISOBLAYDI.
        RMST(tau) = int_0^tau S(u) du,  S -- Kaplan-Meier step funksiyasi.
    Varians -- Greenwood asosidagi delta metod:
        var = sum_{t_i <= tau} A_i^2 * d_i / (n_i * (n_i - d_i)),
        A_i = int_{t_i}^{tau} S(u) du
    `n_i == d_i` hadlar tashlanadi (KM'dagi bir xil konvensiya).

    TALQIN. RMST -- "tau ichida kutilgan tirik (ya'ni hali down) vaqt".
    Time-to-VR uchun: RMST kichikroq = TEZROQ recovery. Shuning uchun
    `rmst_difference(P0, P2)` MANFIY bo'lsa, P2 sekinroq.

    FARAZLAR.
      * `tau` OLDINDAN belgilanadi (§11: tau = 8 s). Ma'lumotga qarab
        tanlangan tau -- garden of forking paths.
      * Noninformative censoring.
      * `tau` risk to'plami bo'sh bo'lmagan oraliqda bo'lishi kerak.

    QACHON YAROQSIZ / OGOHLIK.
      * `tau` oxirgi kuzatilgan vaqtdan KATTA bo'lsa, KM egri chizig'i u
        yerda aniqlanmagan. Bu implementatsiya S ni oxirgi ma'lum qiymatda
        CHO'ZADI, bu esa BIASED -- funksiya bunda ogohlantirish beradi.
        To'g'ri yechim: tau <= min(max(times_a), max(times_b)).
      * Varians formulasi asimptotik. Kichik n (P1 da 20/daraja) da CI
        nominal coverage'dan chetlashishi mumkin -- shuning uchun §10.2
        bootstrap variantini ham talab qiladi.
      * SE uchun NASHR ETILGAN raqamli misol topilmadi -- modul boshidagi
        "VALIDATSIYA HOLATI" ga qarang.

    VALIDATSIYA (qisman). Royston, P. & Parmar, M.K.B. (2013), BMC Medical
    Research Methodology 13:152; Klein, J.P. & Moeschberger, M.L. (2003),
    "Survival Analysis", 2-nashr §4.5 (RMST va uning variansi).
    Nuqtaviy baho Farrow (2009-10) §5.2 dagi NASHR ETILGAN KM jadvali
    ostidagi yuza bilan tekshirilgan (arifmetika test faylida ko'rsatilgan).
    STANDARD ERROR nashr etilgan raqamga qarshi tekshirilMAGAN.
    """
    tau = float(tau)
    if not math.isfinite(tau) or tau <= 0.0:
        raise ValueError(f"tau musbat va chekli bo'lishi kerak, berilgani: {tau}")
    t, e = _as_surv(times, events)
    if tau > float(t.max()):
        warnings.warn(
            f"tau={tau} oxirgi kuzatilgan vaqtdan ({t.max()}) katta: KM egri chizig'i "
            "oxirgi qiymatda cho'ziladi va RMST BIASED bo'ladi",
            RuntimeWarning,
            stacklevel=2,
        )
    km = kaplan_meier(t, e)
    area, var, k = _rmst_from_km(km, tau)
    return RMSTResult(
        rmst=area, std_err=math.sqrt(var), variance=var, tau=tau, n_events_used=k
    )


def rmst_difference(
    group_a: tuple, group_b: tuple, tau: float, alpha: float = 0.05
) -> RMSTDifference:
    """RMST farqi (A - B) -- H2 UCHUN BOSH EFFECT MEASURE.

    PREREGISTRATION.md §10.2 va §11: "fail-slow shakli qo'llab-quvvatlanmaydi,
    agar P0 va P2 orasidagi time-to-VR RMST farqi (tau = 8 s) uchun 95% CI
    20% oshishni chiqarib tashlasa."

    ARGUMENTLAR. `group_a` va `group_b` -- `(times, events)` juftliklari.

    NIMA HISOBLAYDI.
        diff = RMST_a(tau) - RMST_b(tau)
        SE   = sqrt( var_a + var_b )        (guruhlar MUSTAQIL)
        CI   = diff +- z_{alpha/2} * SE
        p    = 2 * (1 - Phi(|diff| / SE))
    Bu pairwise farq, HAZARD RATIO EMAS. Uni "tau ichida tejalgan (yoki
    yo'qotilgan) kutilgan downtime sekundlari" sifatida o'qish mumkin.

    FARAZLAR. `rmst` bilan bir xil, plus: ikki guruh MUSTAQIL. Paired
    (blok ichida) taqqoslash uchun bu funksiya YARAMAYDI -- §10.2 unda
    Wilcoxon signed-rank ni talab qiladi.

    QACHON YAROQSIZ. `tau` ikki guruhning HAR IKKISIDA ham qo'llab
    quvvatlanishi kerak: `tau <= min(max(times_a), max(times_b))`. Aks holda
    bir guruhda ekstrapolyatsiya bo'ladi -- funksiya ogohlantiradi.
    Normal yaqinlashish kichik n da taxminiy; §10.2 bootstrap variantini
    ham talab qiladi.

    VALIDATSIYA. `rmst` bilan bir xil (qisman -- SE uchun nashr etilgan
    raqam yo'q). Farq va SE ning yig'ilish qoidasi: Royston & Parmar (2013).
    """
    if not (isinstance(group_a, (tuple, list)) and len(group_a) == 2):
        raise ValueError("group_a (times, events) juftligi bo'lishi kerak")
    if not (isinstance(group_b, (tuple, list)) and len(group_b) == 2):
        raise ValueError("group_b (times, events) juftligi bo'lishi kerak")
    z = _z(alpha)
    a = rmst(group_a[0], group_a[1], tau)
    b = rmst(group_b[0], group_b[1], tau)
    diff = a.rmst - b.rmst
    se = math.sqrt(a.variance + b.variance)
    if se > 0.0:
        stat = diff / se
        p = float(2.0 * stats.norm.sf(abs(stat)))
    else:
        p = float("nan")
    return RMSTDifference(
        difference=diff,
        std_err=se,
        lower=diff - z * se,
        upper=diff + z * se,
        p_value=p,
        tau=float(tau),
        rmst_a=a,
        rmst_b=b,
    )


# --- 3. Nonparametrik effect size'lar --------------------------------------


def _cliffs_delta_point(a: np.ndarray, b: np.ndarray) -> float:
    """Cliff's delta nuqtaviy bahosi. O(n log n), ties to'g'ri ishlanadi."""
    bs = np.sort(b)
    nb = bs.size
    # a_i dan KICHIK b'lar soni va a_i dan KATTA b'lar soni
    lt_b = np.searchsorted(bs, a, side="left")  # b < a_i
    le_b = np.searchsorted(bs, a, side="right")  # b <= a_i
    n_gt = float(lt_b.sum())  # #(a > b)
    n_lt = float((nb - le_b).sum())  # #(a < b)
    return (n_gt - n_lt) / (a.size * nb)


def cliffs_delta(
    a,
    b,
    alpha: float = 0.05,
    n_boot: int = 9999,
    method: str = "percentile",
    rng=None,
) -> CliffsDelta:
    """Cliff's delta va uning bootstrap confidence interval'i.

    PREREGISTRATION.md §10.2: "Ikkilamchi (censored bo'lmagan qism ustida):
    Mann-Whitney U, Kruskal-Wallis + Dunn; effect size Cliff's delta / A12
    bootstrap CI bilan."

    NIMA HISOBLAYDI.
        delta = ( #{a_i > b_j} - #{a_i < b_j} ) / (n_a * n_b)
    Ya'ni "tasodifiy a tasodifiy b'dan katta bo'lish ehtimoli" minus teskarisi.
    Diapazon [-1, 1]; 0 -- stokastik tenglik; 1 -- to'liq ajralish (hamma a
    hamma b'dan katta). Vargha-Delaney A12 = (delta + 1) / 2 ham qaytariladi.

    CI. Stratifikatsiyalangan nonparametrik bootstrap: a va b MUSTAQIL
    resample qilinadi, so'ng `method` ("percentile" yoki "bca") bo'yicha
    interval olinadi. Default "percentile": delta chegaralarga (+-1) yaqin
    bo'lganda BCa ning acceleration bahosi degenerativ bo'lib qoladi, va
    REVIX'da to'liq ajralish (P0 hammasi tez, P2 hammasi sekin) REAL imkoniyat.

    FARAZLAR. Mustaqil namunalar. Taqsimot shakli haqida FARAZ YO'Q -- shuning
    uchun bu og'ir dumli, bimodal downtime uchun mos (§10.2).

    QACHON YAROQSIZ -- MUHIM.
      * CENSORED kuzatuvlarni TO'G'RI ISHLAMAYDI. Censored qiymat "kamida
        shuncha" degani, lekin bu funksiya uni oddiy son deb oladi va
        NATIJANI SILJITADI. §10.2 uni ATAYIN faqat "censored bo'lmagan qism
        ustida" ikkilamchi metrika sifatida belgilaydi. Censoring bor joyda
        `rmst_difference` ishlatiladi.
      * delta = +-1 bo'lsa bootstrap CI degenerativ bo'ladi (barcha resample
        bir xil) -- bu haqiqiy holat, yashirilmaydi.

    VALIDATSIYA. Cliff, N. (1993), Psychological Bulletin 114:494-509;
    Vargha, A. & Delaney, H.D. (2000), J Educ Behav Stat 25:101-132.
    Raqamli tekshiruv: ties bo'lmaganda ayniyat
    delta = 2 * U / (n_a * n_b) - 1, bu yerda U -- `scipy.stats.mannwhitneyu`
    statistikasi (mustaqil implementatsiyaga qarshi cross-check).
    """
    a = np.asarray(a, dtype=float).ravel()
    b = np.asarray(b, dtype=float).ravel()
    if a.size == 0 or b.size == 0:
        raise ValueError("ikki namuna ham bo'sh bo'lmasligi kerak")
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        raise ValueError("NaN/inf qiymatlar qabul qilinmaydi")
    method = method.lower()
    if method not in ("percentile", "bca"):
        raise ValueError(f"method 'percentile' yoki 'bca' bo'lishi kerak, berilgani: {method}")

    delta = _cliffs_delta_point(a, b)
    gen = np.random.default_rng(rng)

    def _stat(x, y):
        # `vectorized=False`: scipy har chaqiruvda 1-D massiv beradi. Sekinroq,
        # lekin scipy'ning batch shakllariga taqlid qilishdan ANCHA ishonchli.
        return _cliffs_delta_point(np.asarray(x, dtype=float), np.asarray(y, dtype=float))

    used = method
    if method == "bca":
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = stats.bootstrap(
                (a, b),
                _stat,
                vectorized=False,
                paired=False,
                n_resamples=int(n_boot),
                confidence_level=1.0 - alpha,
                method="BCa",
                random_state=gen,
            )
        lo, hi = float(res.confidence_interval.low), float(res.confidence_interval.high)
        if not (math.isfinite(lo) and math.isfinite(hi)):
            used = "percentile"
    if used == "percentile":
        na, nb = a.size, b.size
        boots = np.empty(int(n_boot))
        for i in range(int(n_boot)):
            boots[i] = _cliffs_delta_point(
                a[gen.integers(0, na, na)], b[gen.integers(0, nb, nb)]
            )
        lo = float(np.quantile(boots, alpha / 2.0))
        hi = float(np.quantile(boots, 1.0 - alpha / 2.0))

    return CliffsDelta(
        delta=delta,
        lower=lo,
        upper=hi,
        a12=(delta + 1.0) / 2.0,
        alpha=alpha,
        n_boot=int(n_boot),
        method=used,
    )


def bootstrap_ci(
    data,
    statistic: Callable,
    alpha: float = 0.05,
    n_boot: int = 9999,
    method: str = "bca",
    rng=None,
) -> BootstrapCI:
    """BCa bootstrap confidence interval -- median / p90 / p99 uchun.

    PREREGISTRATION.md §10.2: "median, p90, p99 + BCa bootstrap CI -- dum
    xatti-harakati muhim; p99 downtime operatorlar uchun ahamiyatli."

    IMPLEMENTATSIYA -- OCHIQ BAYON. Bu funksiya `scipy.stats.bootstrap` ustida
    qobiq. §10.3 scipy'ni "bootstrap'ni qoplaydi" deb belgilaydi, shuning
    uchun BCa arifmetikasi qayta yozilMAYDI: scipy'ning implementatsiyasi
    o'z test suite'iga ega va reviewer uchun ishonchliroq.

    NIMA HISOBLAYDI. BCa (bias-corrected and accelerated) interval: bias
    tuzatish z0 (bootstrap taqsimotida original bahodan past ulush orqali) va
    acceleration a (jackknife orqali) bilan percentile interval'ni siljitadi.

    FALLBACK -- JIMGINA EMAS. Degenerativ holatlarda (masalan barcha qiymat
    bir xil, yoki statistic = min/max) BCa aniqlanmagan bo'ladi va scipy NaN
    qaytaradi. Bu holda percentile interval'ga qaytamiz va natijaning
    `method` maydoni "percentile" bo'ladi -- `method_requested` esa
    so'ralganini saqlaydi. HISOBOTDA aynan `method` beriladi.

    ARGUMENTLAR.
      data      -- bitta namuna (1-D array-like) yoki namunalar ketma-ketligi.
      statistic -- callable. `axis` nomli argumenti bo'lsa scipy uni
                   vektorlashgan deb qabul qiladi (masalan `np.median`).
      method    -- "bca" (default) yoki "percentile" / "basic".

    FARAZLAR. Kuzatuvlar i.i.d. (yoki hech bo'lmasa exchangeable). Bootstrap
    namuna taqsimotini EMPIRIK taqsimot bilan almashtiradi -- demak dumdagi
    kvantillar (p99) uchun n kichik bo'lsa interval ISHONCHSIZ.

    QACHON YAROQSIZ.
      * n kichik va statistic ekstremal kvantil bo'lsa (p99, n = 20 -- P1 dagi
        aynan holat): bootstrap p99 uchun eng ko'pi bilan namunadagi
        maksimumni ko'radi. Bu ochiq cheklov, §10.2 shu sababli ECDF'larni
        to'liq chizishni talab qiladi.
      * CENSORED ma'lumot uchun YARAMAYDI. Censoring bor joyda KM/RMST.
      * Bog'liq (blok ichida korrelyatsiyalangan) kuzatuvlar uchun block
        bootstrap kerak -- bu yerda YO'Q.

    VALIDATSIYA. Efron, B. (1987), JASA 82:171-185 (BCa);
    Efron & Tibshirani (1993), "An Introduction to the Bootstrap".
    Implementatsiya `scipy.stats.bootstrap(method="BCa")` -- scipy'ning o'z
    testlari. Bu modul qo'shimcha ravishda SINTETIK coverage tekshiruvini
    bajaradi (ma'lum parametr nominal darajaga yaqin qoplanishi).
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha (0, 1) oralig'ida bo'lishi kerak, berilgani: {alpha}")
    if int(n_boot) < 100:
        raise ValueError(f"n_boot >= 100 bo'lishi kerak, berilgani: {n_boot}")
    requested = method.lower()
    scipy_method = {"bca": "BCa", "percentile": "percentile", "basic": "basic"}.get(requested)
    if scipy_method is None:
        raise ValueError(
            f"method 'bca', 'percentile' yoki 'basic' bo'lishi kerak, berilgani: {method}"
        )

    samples = (np.asarray(data, dtype=float),) if _is_single_sample(data) else tuple(
        np.asarray(s, dtype=float) for s in data
    )
    for s in samples:
        if s.size == 0:
            raise ValueError("bo'sh namuna")
    gen = np.random.default_rng(rng)
    point = float(statistic(*samples))

    def _run(m: str):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return stats.bootstrap(
                samples,
                statistic,
                n_resamples=int(n_boot),
                confidence_level=1.0 - alpha,
                method=m,
                random_state=gen,
            )

    res = _run(scipy_method)
    lo = float(res.confidence_interval.low)
    hi = float(res.confidence_interval.high)
    used = requested
    if not (math.isfinite(lo) and math.isfinite(hi)):
        if requested == "bca":
            warnings.warn(
                "BCa interval degenerativ (NaN) -- percentile'ga qaytildi; "
                "natijaning method maydoni 'percentile'",
                RuntimeWarning,
                stacklevel=2,
            )
            res = _run("percentile")
            lo = float(res.confidence_interval.low)
            hi = float(res.confidence_interval.high)
            used = "percentile"
    return BootstrapCI(
        estimate=point,
        lower=lo,
        upper=hi,
        alpha=alpha,
        n_boot=int(n_boot),
        method=used,
        method_requested=requested,
    )


def _is_single_sample(data) -> bool:
    """`data` bitta namunami (1-D) yoki namunalar ketma-ketligimi?"""
    if isinstance(data, np.ndarray):
        if data.ndim == 1:
            return True
        if data.ndim == 2:
            return False
        raise ValueError(f"data 1-D yoki 2-D bo'lishi kerak, berilgani ndim={data.ndim}")
    if isinstance(data, (list, tuple)):
        if len(data) == 0:
            raise ValueError("bo'sh namuna")
        return not any(isinstance(x, (list, tuple, np.ndarray)) for x in data)
    raise ValueError("data array-like (yoki array-like'lar ketma-ketligi) bo'lishi kerak")


def mann_whitney_u(a, b, alternative: str = "two-sided"):
    """Mann-Whitney U testi -- `scipy.stats.mannwhitneyu` ustida yupqa qobiq.

    PREREGISTRATION.md §10.2 da IKKILAMCHI test, faqat CENSORED BO'LMAGAN
    qism ustida. Censoring bor joyda log-rank / RMST ishlatiladi.

    QACHON YAROQSIZ. Censored ma'lumot bilan -- natija siljiydi. Shuningdek
    U testi "stokastik tenglik" ni sinaydi; taqsimotlar kesishsa (bimodal
    downtime -- §10.2 buni kutadi) u farqni o'tkazib yuborishi mumkin.

    VALIDATSIYA. `scipy.stats.mannwhitneyu` -- scipy'ning o'z testlari.
    """
    return stats.mannwhitneyu(a, b, alternative=alternative)


def kruskal_wallis(*groups):
    """Kruskal-Wallis H testi -- `scipy.stats.kruskal` ustida yupqa qobiq.

    PREREGISTRATION.md §10.2 da IKKILAMCHI test (>2 arm uchun), faqat
    censored bo'lmagan qism ustida. Post-hoc Dunn testi bu modulda YO'Q --
    kerak bo'lsa Holm bilan tuzatilgan pairwise Mann-Whitney ishlatiladi.

    QACHON YAROQSIZ. `mann_whitney_u` bilan bir xil sabablar.

    VALIDATSIYA. `scipy.stats.kruskal` -- scipy'ning o'z testlari.
    """
    return stats.kruskal(*groups)


# --- 4. Count'lar (restart / loop soni) ------------------------------------


def negative_binomial_rate_test(
    counts_a,
    exposure_a,
    counts_b,
    exposure_b,
    alpha: float = 0.05,
    n_boot: int = 9999,
    rng=None,
) -> RateTestResult:
    """Overdispersion'ga chidamli RATE taqqoslash (restart / loop soni).

    ################ VALIDATSIYA OGOHLANTIRISHI -- O'QING ################
    Bu funksiya TO'LIQ NEGATIVE BINOMIAL (NB2) MLE EMAS, nomiga qaramay.
    Nom PREREGISTRATION.md §10.2 dagi atamani saqlab turadi
    ("Restart/loop soni: negative binomial ... yoki tezlik farqining
    nonparametrik bootstrap'i") -- ikkinchi variant amalga oshirilgan.

    AMALDA NIMA QILINADI -- ikkita mustaqil javob:
      (1) QUASI-POISSON (dispersion bilan masshtablangan) log-rate-ratio
          Wald testi. Var(Y_i) = phi * mu_i deb faraz qiladi (NB2 dagi
          mu + alpha*mu^2 EMAS). phi Pearson chi-square orqali:
              phi = (1/(N-2)) * sum_i (y_i - mu_i)^2 / mu_i
          log rate ratio SE'si Poisson SE'sini sqrt(phi) ga ko'paytiradi:
              SE = sqrt( phi * (1/Y_a + 1/Y_b) )
          phi ~ 1 bo'lsa bu aynan klassik Poisson rate-ratio testiga
          qaytadi -- bu xususiyat test qilingan.
      (2) RATE DIFFERENCE uchun NONPARAMETRIK BOOTSTRAP CI (birlik
          bo'yicha resample, taqsimot haqida faraz YO'Q).

    NEGA NB2 MLE EMAS. NB2 MLE kichik n (P1 da 20 trial/daraja) da dispersion
    parametrini beqaror baholaydi va konvergensiya muammolari beradi;
    quasi-Poisson yopiq shaklda, konvergensiyasiz va Poisson'dan kengroq
    interval beradi. Bu O'RNIGA QO'YISH ATAYIN va shu yerda e'lon qilingan --
    jimgina kuchsizroq testga o'tish EMAS. Raqamlar hisobotda
    `model="quasi-poisson+bootstrap"` bilan beriladi.

    VALIDATSIYA HOLATI: BU FUNKSIYA UCHUN NASHR ETILGAN ISHLANGAN MISOL
    TOPILMADI. Faqat ichki izchillik tekshirilgan (phi=1 da Poisson Wald
    testiga qaytishi, phi ning overdispersion'ni sezishi, bootstrap CI
    coverage'i). Boshqa estimator'lardan farqli, bu VALIDATED EMAS.
    #####################################################################

    ARGUMENTLAR.
      counts_*   -- har bir birlikdagi (trial) hodisa soni, masalan
                    `Delta NRestarts`.
      exposure_* -- shu birlikning kuzatuv vaqti (masalan T_trial, sekund).
                    `loop_rate = Delta NRestarts / T_trial` -- §6.4.

    QACHON YAROQSIZ.
      * Nol count juda ko'p bo'lsa (zero-inflation) na quasi-Poisson na NB2
        to'g'ri emas -- zero-inflated model kerak. REVIX'da bu EHTIMOLLI
        (ko'p trial'da 1 restart), shuning uchun (2) bootstrap CI
        BIRLAMCHI o'qilishi kerak.
      * Bir guruhda umumiy count 0 bo'lsa log rate ratio aniqlanmagan --
        statistic/p NaN bo'ladi, bootstrap farqi esa hali ma'noli.
      * Underdispersion (phi < 1) bo'lsa phi 1.0 ga QISILADI (konservativ):
        Poisson'dan tor interval berish reviewer oldida himoya qilinmaydi.
    """
    ya = np.asarray(counts_a, dtype=float).ravel()
    yb = np.asarray(counts_b, dtype=float).ravel()
    ea = np.asarray(exposure_a, dtype=float).ravel()
    eb = np.asarray(exposure_b, dtype=float).ravel()
    if ea.size == 1:
        ea = np.full(ya.size, float(ea[0]))
    if eb.size == 1:
        eb = np.full(yb.size, float(eb[0]))
    for name, y, ex in (("a", ya, ea), ("b", yb, eb)):
        if y.size != ex.size:
            raise ValueError(f"guruh {name}: counts va exposure uzunligi teng bo'lishi kerak")
        if y.size == 0:
            raise ValueError(f"guruh {name}: bo'sh namuna")
        if np.any(y < 0) or np.any(~np.isfinite(y)):
            raise ValueError(f"guruh {name}: counts manfiy bo'lmagan chekli son bo'lishi kerak")
        if np.any(ex <= 0) or np.any(~np.isfinite(ex)):
            raise ValueError(f"guruh {name}: exposure musbat va chekli bo'lishi kerak")
    z = _z(alpha)

    tot_a, tot_b = float(ya.sum()), float(yb.sum())
    exp_a, exp_b = float(ea.sum()), float(eb.sum())
    rate_a, rate_b = tot_a / exp_a, tot_b / exp_b

    # Pearson dispersion (guruh bo'yicha o'z rate'i bilan fit qilingan model).
    mu = np.concatenate([ea * rate_a, eb * rate_b])
    y_all = np.concatenate([ya, yb])
    dof = y_all.size - 2
    if dof > 0 and np.all(mu > 0):
        phi = float(np.sum((y_all - mu) ** 2 / mu) / dof)
    else:
        phi = 1.0
    phi = max(phi, 1.0)  # underdispersion'da konservativ

    if tot_a > 0.0 and tot_b > 0.0:
        se_log = math.sqrt(phi * (1.0 / tot_a + 1.0 / tot_b))
        log_rr = math.log(rate_a / rate_b)
        stat = log_rr / se_log
        p = float(2.0 * stats.norm.sf(abs(stat)))
        rr_lo = math.exp(log_rr - z * se_log)
        rr_hi = math.exp(log_rr + z * se_log)
        rr = rate_a / rate_b
    else:
        se_log = float("nan")
        stat = float("nan")
        p = float("nan")
        rr_lo = rr_hi = float("nan")
        rr = float("nan") if tot_b == 0.0 else 0.0

    # Rate difference uchun nonparametrik bootstrap (percentile).
    gen = np.random.default_rng(rng)
    na, nb = ya.size, yb.size
    boots = np.empty(int(n_boot))
    for i in range(int(n_boot)):
        ia = gen.integers(0, na, na)
        ib = gen.integers(0, nb, nb)
        boots[i] = ya[ia].sum() / ea[ia].sum() - yb[ib].sum() / eb[ib].sum()
    d_lo = float(np.quantile(boots, alpha / 2.0))
    d_hi = float(np.quantile(boots, 1.0 - alpha / 2.0))

    return RateTestResult(
        rate_a=rate_a,
        rate_b=rate_b,
        rate_ratio=rr,
        rate_difference=rate_a - rate_b,
        dispersion=phi,
        statistic=stat,
        p_value=p,
        log_rr_std_err=se_log,
        rr_lower=rr_lo,
        rr_upper=rr_hi,
        diff_lower=d_lo,
        diff_upper=d_hi,
        n_boot=int(n_boot),
        model="quasi-poisson+bootstrap",
    )


# --- 5. Multiplicity -------------------------------------------------------


def holm_bonferroni(pvalues, alpha: float = 0.05) -> HolmResult:
    """Holm-Bonferroni step-down tuzatish.

    PREREGISTRATION.md §10.4: "Pre-registered per-class birlamchi testlar
    bo'ylab Holm-Bonferroni. P1 da bitta fault class bor (clean_crash), demak
    bitta birlamchi test; scope/Delta sweep'lari exploratory deb belgilanadi."

    NIMA HISOBLAYDI. p-value'lar o'sish tartibida p_(1) <= ... <= p_(m):
        p_adj_(i) = max_{j <= i} min( 1, (m - j + 1) * p_(j) )
    Tashqi `max` -- MONOTONLIKNI majburlaydi (kumulyativ maksimum): tartib
    bo'yicha keyingi adjusted p-value hech qachon oldingisidan kichik
    bo'lmaydi. `reject` = (p_adj <= alpha).

    NEGA HOLM VA BONFERRONI EMAS. Holm har qanday bog'liqlik ostida FWER ni
    alpha da nazorat qiladi (Bonferroni kabi), LEKIN qat'iy kuchliroq --
    hech qachon kamroq gipoteza rad etmaydi.

    FARAZLAR. Hech qanday. Testlar orasidagi bog'liqlik haqida faraz YO'Q.

    QACHON YAROQSIZ / OGOHLIK.
      * Holm FWER ni nazorat qiladi, FDR ni EMAS. Ko'p exploratory test uchun
        FDR (Benjamini-Hochberg) mos bo'lardi -- bu modulda ATAYIN yo'q,
        chunki §10.4 faqat pre-registered BIRLAMCHI testlar oilasiga
        tuzatish qo'yadi; exploratory natijalar tuzatilmaydi va
        EXPLORATORY deb belgilanadi.
      * Bu funksiyaga POST-HOC tanlangan test to'plamini berish -- garden of
        forking paths. Oila §10.4 da MUZLATILGAN.

    VALIDATSIYA. Holm, S. (1979), Scandinavian Journal of Statistics
    6(2):65-70 (protsedura); Wright, S.P. (1992), Biometrics 48:1005-1013
    (adjusted p-value shakli).
    Raqamli misol: Blakesley, R.E., Mazumdar, S., Dew, M.A., Houck, P.R.,
    Tang, G., Reynolds, C.F. III & Butters, M.A. (2009), "Comparisons of
    methods for multiple hypothesis testing in neuropsychological research",
    Neuropsychology 23(2):255-264, Table 1: kuzatilgan p = (0.3587, 0.1663,
    0.1365, 0.0117) -> Holm adjusted (0.4096, 0.4096, 0.4096, 0.0470).
    """
    p = np.asarray(pvalues, dtype=float).ravel()
    if p.size == 0:
        raise ValueError("bo'sh p-value ro'yxati")
    if np.any(~np.isfinite(p)) or np.any(p < 0.0) or np.any(p > 1.0):
        raise ValueError("p-value'lar [0, 1] oralig'idagi chekli sonlar bo'lishi kerak")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha (0, 1) oralig'ida bo'lishi kerak, berilgani: {alpha}")

    m = p.size
    order = np.argsort(p, kind="stable")
    ranked = p[order]
    weights = (m - np.arange(m)).astype(float)  # m, m-1, ..., 1
    adj_sorted = np.minimum(np.maximum.accumulate(weights * ranked), 1.0)
    adjusted = np.empty(m)
    adjusted[order] = adj_sorted
    return HolmResult(
        adjusted=adjusted,
        reject=adjusted <= alpha,
        alpha=alpha,
        n_tests=m,
    )
