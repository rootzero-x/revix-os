"""REVIX offline analiz moduli -- `reduce.py` chiqishidan `analysis.json`.

`docs/architecture/04-driver-va-analiz-shartnomasi.md` §2 ni amalga oshiradi:
  * §2.1 -- kirish: `reduce.py` ning `trial_metrics` record'lari + `run_meta.json`
  * §2.2 -- chiqish: `analysis.json` ning QAT'IY sxemasi
  * §2.3 -- sakkizta analiz majburiyati; har biri uchun regressiya qulfi
            (`tests/unit/test_analyze.py`)

va `PREREGISTRATION.md` §10 dagi muzlatilgan analiz rejasini bajaradi:
  * §4   -- sensitivity sweep (`W_stab` x `theta`) natijasi jadval sifatida
  * §5   -- FR-A birlamchi (oracle-free); FR-B P1 da BERILMAYDI
  * §6   -- uchala downtime o'lchovi, right censoring tashlanmaydi
  * §10.1 -- Cochran-Armitage trend + Clopper-Pearson + Newcombe (BIRLAMCHI)
  * §10.2 -- Kaplan-Meier / log-rank / RMST; `t-test` va `mean ± SD` TAQIQLANGAN
  * §10.4 -- Holm-Bonferroni; P1 da BITTA birlamchi test
  * §11   -- falsifikatsiya mezoni va `tau = 8 s`
  * §12   -- disposition yopiq enum; eksklyuziya darajasi NATIJA sifatida

DIZAYN QOIDALARI (buzilmaydi):

  1. **QAT'IY OFFLINE va PUR.** Bu modul o'lchanayotgan tizimga TEGMAYDI:
     `systemd`, `cgroup`, `subprocess`, socket, `/proc`, `/sys` -- hech biri
     import qilinmaydi va o'qilmaydi. Faqat fayldan o'qiydi, faylga yozadi.
     Yagona vaqtga bog'liq xatti-harakat -- `generated_mono_us` shtampi.
  2. **DETERMINISTIK.** Bir xil kirish -> bayt-baytga bir xil `analysis.json`
     (`generated_mono_us` dan tashqari). Bootstrap RNG'si MUZLATILGAN urug'
     bilan seed qilinadi va urug' chiqishda qayd etiladi; aks holda CI'lar
     har ishga tushirishda siljib, "qayta hisoblash" tekshiruvi ma'nosiz
     bo'lardi.
  3. **STATISTIKA QAYTA YOZILMAYDI.** Har bir estimator `revix/stats.py` dan
     olinadi (§10.3: `statsmodels`/`lifelines` YO'Q, yangi bog'liqlik YO'Q).
     Bu modulda birorta statistik formula YO'Q -- u faqat MA'LUMOTNI
     YO'NALTIRADI va natijani §2.2 sxemasiga joylaydi.
  4. **TAQIQLANGAN STATISTIKA STRUKTURAVIY JIHATDAN IMKONSIZ.** `t-test`,
     `mean ± SD`, hazard ratio / Cox -- chiqish yozilishdan OLDIN
     `_assert_no_forbidden()` bilan tekshiriladi va topilsa `AnalysisError`.
     Testga tayanish yetarli emas: taqiq §10.2 da muzlatilgan, demak uni
     buzish XATO emas, SHARTNOMA BUZILISHI.
  5. **CENSORED KUZATUV TASHLANMAYDI** (§6.2). KM/log-rank/RMST censored
     trial'larni O'Z ICHIGA OLADI. Ularni tashlash tez ishdan chiqadigan
     arm'ni chiroyli ko'rsatadigan klassik yashirin bias.
  6. **`None` = "o'lchanmagan", `0` = "o'lchangan nol".** Hisoblab bo'lmagan
     narsa `warnings` ga tushadi va `None` bo'lib qoladi -- TAXMIN
     QILINMAYDI (§2.3 #6). NaN/inf hech qachon chiqishga yetib bormaydi:
     serializatsiya `allow_nan=False` bilan qilinadi.
  7. **`preregistration_sha256` KIRISH `run_meta` DAN KO'CHIRILADI**, hech
     qachon qayta hisoblanmaydi. Analiz hujjatni o'zi xesh qilsa, u
     "o'zi tekshirgan o'zi" bo'lardi. Xuddi shu qoida `t_trial_us` ga ham
     tegishli (shartnoma §5.4, `driver-contract/v1.1`): horizon DRIVER
     tomonidan hisoblanadi va `run_meta.t_trial_us` da yoziladi. Analiz uni
     QAYTA HISOBLAMAYDI va TAXMIN QILMAYDI -- `recovered_within_horizon:
     "k/n"` nisbati AYNAN shu horizon'ga nisbatan, va u raqamsiz o'qilmaydi.
  8. **EKSKLYUZIYA DARAJASI NATIJA** (§12), va u QAYSI TO'PLAM ustida
     hisoblanganini NOMLAYDI (§16.4). Ikki to'plam -- binar `P(VR)`
     maxraji va survival/`k/n` analiz to'plami -- ikki darajani beradi,
     va nomlanmagan daraja TAKRORLANUVCHI EMAS.
  9. **QAMROV OCHIQ YOZILADI** (§16.2(A), §16.5). Birlamchi trend testi
     va §11 ning `P0`-`P2` RMST kontrasti arm `A` ICHIDA hisoblanadi,
     arm'lar bo'ylab pool qilinMAYDI. Qamrov chiqishda ko'rsatiladi,
     chunki arm'siz yacheyka POOL QILINGAN natija deb o'qilishi mumkin.
 10. **TO'PLAM TANLOVI `reduce.py` NING QARORI.** Bu modul
     `reduce.select_primary` / `select_survival` ni chaqiradi va
     `disposition` yoki `disposition_source` bo'yicha O'ZI filtrlamaydi
     (§16.6: `reduce.py` ni tuzatish -- muzlatilgan matnga MOSLASHTIRISH,
     demak u YAKKA MANBA bo'lib qoladi). `included_in_primary` /
     `included_in_survival` field'lari O'QILMAYDI -- ikki manba ikki
     javob berardi.

SXEMA QO'SHIMCHALARI -- OCHIQ RO'YXAT (shartnoma §2.2 ning kalitlari
MAJBURIY MINIMUM deb o'qiladi, chunki §2.3 ning #4 va #8 majburiyatlari
§2.2 da ko'rinmagan kalitlarni talab qiladi; bu `agent/contract` uchun
amendment savoli, bu yerda O'ZBOSHIMCHALIK bilan hal qilinmaydi):

  * `primary.recovered_within_horizon`, `downtime.<m>.recovered_within_horizon`,
    `sensitivity.recovered_within_horizon` -- §2.3 #4 "HAR jadval `k/n` bilan
    birga" deydi, §2.2 esa bu kalitni faqat `survival.censoring` da ko'rsatadi.
  * `survival.km.by_arm.<arm>.quantiles` -- §2.3 #8 KM p90/p99 ning `nan`
    bo'lish holatini talab qiladi, §2.2 da kvantil uchun joy yo'q.
  * `survival.km.by_arm.<arm>.{n_total,n_censored,n_events}` -- `n`'siz KM
    egri chizig'i hisobot qilinmaydi (at-risk jadvali `figures.py` uchun).
  * `survival.rmst.difference.contrast` va
    `primary.risk_difference.contrast` -- belgisiz/nomsiz farq TALQIN
    QILINMAYDI.
  * `primary.arm`, `primary.scope`, `primary.cells[].arm`,
    `survival.km.by_pressure_band_scope`,
    `survival.rmst.by_pressure_band_scope` -- §16.2(A) ga ko'ra qamrov
    `analysis.json` da OCHIQ ko'rsatiladi. §2.2 ning `cells` sxemasi
    faqat `level` kaliti bilan yozilgani §16.2(A) da chalkashlikning
    manbai deb NOMLANGAN, shuning uchun arm yacheykaning O'ZIDA ham bor.
  * `exclusions.rate_set`, `exclusions.by_set.{binary_p_vr_denominator,
    survival_analysis_set}` -- §16.4 ning majburiy hisobot qoidasi.
  * `survival.logrank.by_pressure_band.contrast`,
    `survival.logrank.contrast` -- log-rank qaysi ikki guruh orasida
    ekani ko'rinmasa natija talqin qilinmaydi.
  * `time_unit` (yuqori daraja) -- `analysis.json` dagi BARCHA vaqt qiymati
    MIKROSEKUNDDA (§1 vaqt disiplinasi: har davomiylik `CLOCK_MONOTONIC`
    mikrosekundda). Sekundga aylantirish shartnoma ruxsat bermagan birlik
    o'zgarishi bo'lardi, shuning uchun `tau` ham mikrosekundda
    (`8 s = 8_000_000 us`, §11).
  * `primary.ci_level` -- CI darajasi yozilmasa figura "95%" deb da'vo
    qila olmaydi.
  * `downtime.<m>.ecdf = {x, y}` -- §10.2 "ECDF'lar TO'LIQ chizilib
    beriladi -- har qanday bitta testdan ishonchliroq". Egri chiziq
    INTERPOLYATSIYA QILINMAYDI va SILLIQLANMAYDI: u `1 - S(t)` step
    funksiyasi (censoring bor joyda Kaplan-Meier, censoring yo'q joyda bu
    oddiy ECDF ga AYNAN teng).
  * `survival.censoring.n_undetermined` -- §2.2 da `n_undetermined` faqat
    `fr_a` ostida bor, lekin u FR-A ning aniqlanmaganligi. VR ning
    aniqlanmaganligi ALOHIDA kategoriya: `reduce.py` `vr=None` ni aniq
    sabab bilan qaytaradi (`r_ref_unavailable`, `window_truncated`) va
    `None` HECH QACHON `False` emas. Bu §2.3 #6 ning eng muhim holati.
  * `probe_cost` -- §8.2 prober CPU narxini HAR TRIAL uchun, yadro
    foizida, va arm'lar bo'yicha BIR XIL ushlashni talab qiladi. Kalitlar
    `agent/contract` tomonidan ratifikatsiya qilingan (`driver-contract`
    v1.2 ga yozilmoqda): `budget_percent` va `by_arm.<arm>.core_percent`
    (PER-TRIAL ro'yxat, o'lchanmagan joyda `None`). `--events` berilmasa
    bo'lim UMUMAN chiqmaydi -- `figures.py` yo'qligini aniqlay oladi.
  * `false_recovery.fr_a.basis.source` -- qaysi denominator ishlatilgani
    (`--episodes` bormi yoki yo'qmi) HISOBOTDA ko'rinishi kerak.
  * `false_recovery.fr_a.basis` -- FR-A qaysi trial to'plamidan olingani
    auditga ochiq bo'lishi uchun (pastdagi "FR-A CHEKLOVI" ga qarang).
  * `multiplicity.uncorrected` -- §10.4 "exploratory deb belgilanadi"
    deydi, §2.2 da belgilash uchun joy yo'q.
  * `t_trial_us`, `t_trial_formula` -- shartnoma §5.4 (`driver-contract/v1.1`)
    talabi: `recovered_within_horizon: "k/n"` AYNAN shu horizon'ga nisbatan,
    demak raqam chiqishda bo'lmasa nisbat talqin qilinmaydi.
  * `run_id`, `session_id`, `preregistration_version`,
    `exclusions.{n_total,n_excluded,n_primary}` -- provenans va
    `exclusions.rate` ning auditi uchun.
  * `downtime.<m>` va `sensitivity.grid[].p_vr_by_level` ichki tuzilishi --
    §2.2 ularni `{}` deb qoldirgan, demak ichki tuzilish bu modulning
    qarori va yuqorida ta'riflangan.

IXTIYORIY KIRISHLAR -- NEGA IXTIYORIY va nima o'zgaradi:

  * `--episodes` (`reduce.py` ning `episodes.jsonl`). §5 FR-A ni HAR
    ACTION va HAR EPIZOD uchun ta'riflaydi, va per-action FR-A AYNAN shu
    faylda yashaydi (`EpisodeResult.actions[].fr_a`); §2.1 esa kirish
    sifatida faqat `trial_metrics` ni sanagan. BERILSA -- §5 ning
    haqiqiy ta'riflari hisoblanadi. BERILMASA -- faqat AYNAN YECHILADIGAN
    quyi to'plam: `n_episodes == 1` bo'lgan trial'da trial darajasidagi
    FR-A epizod darajasidagi FR-A ga AYNAN TENG (`_kleene_any` bitta
    element ustida), va `n_actions == 1` ham bo'lsa action darajasiga ham
    teng. Denominator u holda §2.2 so'ragandan TORROQ bo'ladi, lekin u
    O'LCHANGAN -- taxmin emas. Qaysi yo'l ishlatilgani HAR IKKI HOLATDA
    `false_recovery.fr_a.basis.source` da yoziladi.

  * `--events` (xom `events.jsonl`). §8.2 prober CPU narxini HAR TRIAL
    uchun, yadro foizida, va ARM'LAR BO'YICHA BIR XIL talab qiladi.
    `revix/prober.py` uni `cost_report()` da hisoblaydi
    (`core_percent`, `budget_percent = 1.0`) va `prober_stop` record'iga
    yozadi; `driver-contract/v1.1` §4.5(a) ga ko'ra driver HAR TRIAL
    uchun bitta prober jarayoni ishga tushiradi (`Prober.trial_id`
    jarayon boshida fiksa qilinadi, boshqaruv kanali yo'q), demak
    `prober_stop` har TRIAL uchun bir marta chiqadi va per-trial o'lchov
    manbada MAVJUD. LEKIN `revix/reduce.py` bu record turini UMUMAN
    o'qimaydi (unda `prober_stop` turi ham, `cost` so'zi ham yo'q) va
    narxni `trial_metrics` ga chiqarmaydi -- va `reduce.py`
    TAHRIRLANMAYDI. Shuning uchun transport shu yerda: `--events` xom
    fayldan `prober_stop` ni oladi, narxni `trial_id` bo'yicha yig'adi va
    arm'ga `trials.jsonl` orqali bog'laydi. Modul hali ham QAT'IY
    OFFLINE: fayl kiradi, hisoblanadi, fayl chiqadi. BERILMASA --
    `probe_cost` bo'limi UMUMAN chiqmaydi va sabab `warnings` da; narx
    TO'QILMAYDI, chunki o'lchanmagan narxni nol yoki budjet qiymati deb
    berish §8.2 ni tekshirilgandek ko'rsatardi.

VALIDATSIYA CHEKLOVI (CHEKLOV): bu modul xom run'ni O'ZI validatsiya
qilmaydi -- `revix/validate.py` xom record'larni talab qiladi, bu modul esa
derived `trial_metrics` ni oladi. §14.6 validator invariantlari analizdan
OLDIN o'tishi SHART, demak bu chaqiruvchining (`cli.py`) majburiyati.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import warnings as _warnings
from dataclasses import dataclass
from typing import Any, Callable, Sequence

import numpy as np

from . import stats as S
from .reduce import (
    DISPOSITION_SOURCES,
    DRT_EPISODE,
    DRT_SUMMARY,
    DRT_SWEEP,
    DRT_TRIAL,
    SET_BINARY_DENOMINATOR,
    SET_SURVIVAL,
    THETA_SWEEP,
    W_STAB_SWEEP_S,
    disposition_counts,
    enters_primary_denominator,
    primary_denominator_verdict,
    select_primary,
    select_survival,
    sweep_is_complete,
)

# NEGA `reduce.PRIMARY_DISPOSITIONS` IMPORT QILINMAYDI: §16.4 uni "to'g'ri
# savol, NOTO'G'RI javob" deb hukm qildi -- binar maxraj `complete` VA
# `censored:down_at_horizon` ni o'z ichiga oladi. `reduce.py` uni faqat
# import muvofiqligi uchun deprecated shim sifatida saqlab turadi; bu modul
# qoidani `reduce.enters_primary_denominator()` /
# `primary_denominator_verdict()` orqali SO'RAYDI, demak qoida BITTA joyda
# (`reduce.PRIMARY_DENOMINATOR_SOURCES`) qoladi va fail-closed bo'ladi.
from .schema import DISPOSITIONS, SCHEMA_VERSION, mono_us

# --- muzlatilgan parametrlar ------------------------------------------------

ANALYSIS_VERSION = "p1/v1"   # §2.2 `analysis_version`

ALPHA = 0.05                 # §10.1 / §11 -- 95% CI
CI_LEVEL = 1.0 - ALPHA       # chiqishda yoziladi: figura "95%" deb da'vo
                             # qilishi uchun daraja OSHKORA bo'lishi kerak
N_BOOT = 9999                # §10.2 BCa bootstrap resample soni

# §1 vaqt disiplinasi: `analysis.json` dagi BARCHA vaqt qiymati
# MIKROSEKUNDDA. Birlik chiqishda `time_unit` sifatida e'lon qilinadi --
# birliksiz son taqqoslanmaydi va sekundga aylantirish shartnoma ruxsat
# bermagan o'zgarish bo'lardi.
TIME_UNIT = "us"

# §9.3 -- P1 pressure darajalari, TARTIBLANGAN. Cochran-Armitage AYNAN shu
# tartibga tayanadi (§10.1: "P0 < P1 < P2 bo'ylab").
PRESSURE_LEVELS = ("P0", "P1", "P2")

# PREREGISTRATION.md §16.2(A) -- §10.1 ning birlamchi trend testi ARM `A`
# ICHIDA hisoblanadi, arm'lar bo'ylab POOL QILINMAYDI. Xuddi shu asos bilan
# §16.5 §11 ning `P0`-`P2` RMST kontrastini ham arm `A` ichiga qo'yadi.
#
# NEGA (§16.2(A) ning hal qiluvchi arifmetikasi): `no_action` arm
# `Restart=no`, demak `clean_crash` dan keyin xizmat hech qachon qaytmaydi,
# demak `P(VR) = 0` UCHALA pressure darajasida KONSTRUKSIYA BO'YICHA. Ikki
# arm'ni pool qilish uchala strataga BIR XIL nolni qo'shadi -- bu trend'ni
# SUSAYTIRADI va §11 ning `P(VR|P0) - P(VR|P2)` farqini `0 - 0 = 0` ga
# intiltiradi, ya'ni falsifikatsiya mezoni TRIVIAL ravishda qanoatlanadi.
# Pooling nafaqat keraksiz -- u TESTNI BUZADI.
#
# `no_action` yashirilmaydi: u §6.2 bo'yicha KM/log-rank ga va har
# jadvalning `k/n` qatoriga KIRADI, va §8.2 bo'yicha PSI atributsiyasi
# vazifasini bajaradi (trend yacheykasi vazifasini emas).
PRIMARY_ARM = "A"

# §11 -- RMST horizon'i: `tau = 8 s`, MIKROSEKUNDDA (§1). OLDINDAN
# belgilangan: ma'lumotga qarab tanlangan `tau` -- garden of forking paths
# (`stats.rmst` docstring'i).
TAU_RMST_US = 8_000_000.0

# §11 -- falsifikatsiya mezoni. Ikki chegara ham QAT'IY tengsizlik:
# `p == 0.05` yoki `upper == 0.15` falsifikatsiya QILMAYDI.
TREND_P_THRESHOLD = 0.05
NEWCOMBE_UPPER_THRESHOLD = 0.15
FALSIFICATION_RULE = "trend p>0.05 AND newcombe_upper<0.15"

# §2.2 -- shartnoma AYNAN shu satrni talab qiladi.
FR_B_REASON_P1 = "no calibration matrix (P1)"

# Xom record turi (`revix/prober.py` yozadi). `reduce.py` da bu tur YO'Q,
# shuning uchun nomi shu yerda mahalliy ta'riflanadi -- `reduce.RAW_CONTRACT`
# faqat hujjat va uni hech narsa validatsiya qilmaydi.
RT_PROBER_STOP = "prober_stop"

MULTIPLICITY_METHOD = "holm_bonferroni"          # §10.4
PRIMARY_ENDPOINT = "P(VR) trend across pressure levels"   # §2.2
PRIMARY_TEST = "cochran_armitage_trend"                   # §2.2
PRIMARY_FAULT_CLASS = "clean_crash"                       # §9.3 / §10.4

# §10.2 -- "median, p90, p99 + BCa bootstrap CI".
QUANTILES: tuple[tuple[str, float], ...] = (
    ("median", 0.50),
    ("p90", 0.90),
    ("p99", 0.99),
)

# §6.1 -- UCHALA downtime o'lchovi HAR DOIM beriladi.
# (chiqish nomi, `trial_metrics` qiymat field'i, `trial_metrics` censoring
#  field'i yoki `None` -- reducer bu o'lchov uchun flag bermaydi).
DOWNTIME_MEASURES: tuple[tuple[str, str, str | None], ...] = (
    ("d_sd", "d_sd_us", "d_sd_censored"),
    ("d_probe", "d_probe_us", "d_probe_censored"),
    ("d_eff", "d_eff_us", None),
)

# NEGA: `D_eff` -- `[t_fault_effective, horizon]` oynasi ustidagi integral
# (§6.1), demak u TA'RIFAN horizon bilan kesilgan va reducer unga censoring
# flag'i BERMAYDI. Shuning uchun uning kvantillari KESILGAN o'lchovning
# kvantillari -- bu `note` sifatida ochiq yoziladi, jimgina "to'liq
# taqsimot" deb ko'rsatilmaydi.
D_EFF_NOTE = ("D_eff is horizon-truncated by construction (PREREGISTRATION.md "
              "§6.1 integral domain) and reduce.py emits no censoring flag for "
              "it; quantiles are those of the truncated measure")

# Bootstrap urug'i -- MUZLATILGAN. Determinizm (qoida 2) uchun shart, va
# chiqishda `rng_seed` sifatida qayd etiladi.
BOOTSTRAP_SEED = 1

# §10.2 taqiqi va §2.3 #1 -- chiqishda BU SATRLAR HECH QACHON bo'lmaydi.
FORBIDDEN_TOKENS: tuple[str, ...] = (
    "t-test", "t_test", "ttest",
    "mean ± sd", "mean +- sd", "mean+-sd", "mean_sd", "mean ± s.d.",
    "std_dev", "stdev", "standard deviation",
)

# §2.3 #2 -- `proportional_hazards_checked` false bo'lsa HR/Cox umuman
# PAYDO BO'LMAYDI. (`proportional_hazards_checked` kalitining o'zi bu
# ro'yxatning birorta elementini O'Z ICHIGA OLMAYDI -- ataylab.)
HAZARD_TOKENS: tuple[str, ...] = (
    "hazard_ratio", "hazard ratio", "hazard-ratio",
    "cox", "schoenfeld", "\"hr\"", "'hr'",
)


class AnalysisError(Exception):
    """Analiz invarianti buzildi. Jimgina davom etilmaydi."""


# --- warnings jurnali (§2.3 #6) --------------------------------------------


@dataclass(frozen=True)
class AnalysisWarning:
    """Hisoblab bo'lmagan narsa. `code` mashina uchun, `message` odam uchun."""

    code: str
    where: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "where": self.where, "message": self.message}


class WarningLog:
    """`warnings` ro'yxati.

    NEGA ALOHIDA SINF: §2.3 #6 "hisoblab bo'lmagan narsa `warnings` ga, va
    TAXMIN QILINMAYDI". Agar har hisob o'z joyida `try/except: pass` qilsa,
    yo'qolgan o'lchov jimgina nolga aylanardi. Bu jurnal har bir hisobga
    MAJBURAN beriladi, shuning uchun "hisoblab bo'lmadi" yozilmasligi uchun
    maxsus harakat kerak bo'ladi -- teskarisi emas.
    """

    def __init__(self) -> None:
        self._items: list[AnalysisWarning] = []
        self._seen: set[tuple[str, str, str]] = set()

    def add(self, code: str, where: str, message: str) -> None:
        key = (code, where, message)
        if key in self._seen:
            return
        self._seen.add(key)
        self._items.append(AnalysisWarning(code, where, message))

    def codes(self) -> list[str]:
        return [w.code for w in self._items]

    def as_list(self) -> list[dict[str, str]]:
        return [w.as_dict() for w in self._items]

    def __len__(self) -> int:
        return len(self._items)


def _capture(fn: Callable[[], Any], log: WarningLog, where: str,
             code: str = "stats_warning") -> Any:
    """`stats.py` ning `RuntimeWarning` larini `warnings` ga ko'chiradi.

    NEGA: `stats.rmst` `tau` oxirgi kuzatilgan vaqtdan katta bo'lsa
    "RMST BIASED" deb ogohlantiradi, `stats.bootstrap_ci` esa BCa degenerativ
    bo'lsa percentile'ga qaytganini aytadi. Bu ogohlantirishlar stderr'da
    yo'qolsa, natija soxta aniqlik bilan o'qilardi.
    """
    with _warnings.catch_warnings(record=True) as caught:
        _warnings.simplefilter("always")
        out = fn()
    for c in caught:
        log.add(code, where, str(c.message))
    return out


# --- son yordamchilari ------------------------------------------------------


def _f(x: Any) -> float | None:
    """`float` yoki `None`. NaN/inf -> `None`.

    NEGA: `None` = "o'lchanmagan". `NaN` JSON'da YAROQSIZ (va `allow_nan=False`
    bilan serializatsiya rad etiladi), `0.0` esa "o'lchangan nol" degan SOXTA
    da'vo bo'lardi.
    """
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _flist(a: Any) -> list[float]:
    """numpy massivini JSON'ga yaroqli `float` ro'yxatiga aylantiradi."""
    seq = a.tolist() if hasattr(a, "tolist") else list(a)
    return [float(v) for v in seq]


def _ilist(a: Any) -> list[int]:
    seq = a.tolist() if hasattr(a, "tolist") else list(a)
    return [int(v) for v in seq]


def _k_of_n(records: Sequence[dict[str, Any]]) -> str:
    """§6.2 / §2.3 #4 -- "`T_trial` ichida recovered: k/n".

    `k` = `vr is True` bo'lgan trial soni; `n` = SHU JADVALGA kirgan trial
    soni. `vr is None` (aniqlanmagan) `k` ga KIRMAYDI -- aks holda
    ma'lumot yetishmovchiligi recovery sifatida hisoblanardi.
    """
    k = sum(1 for r in records if r.get("vr") is True)
    return f"{k}/{len(records)}"


# --- kirish ----------------------------------------------------------------


def _read_jsonl(path: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AnalysisError(
                    f"{path}:{lineno} JSON parse xatosi: {exc}") from exc
            if not isinstance(rec, dict):
                raise AnalysisError(f"{path}:{lineno} record obyekt emas")
            out.append(rec)
    return out


def load_trials(path: str) -> list[dict[str, Any]]:
    """`reduce.write_output` ning `trials.jsonl` ini o'qiydi (§2.1).

    FAIL-CLOSED: birorta `trial_metrics` topilmasa `AnalysisError`. Bo'sh
    analizni jimgina chiqarish -- "hech qanday trial yo'q" degan natijaga
    o'xshab ketardi, lekin u ma'lumot yo'qolishi bo'lardi.
    """
    recs = _read_jsonl(path)
    trials = [r for r in recs if r.get("record_type") == DRT_TRIAL]
    if not trials:
        raise AnalysisError(
            f"{path}: birorta '{DRT_TRIAL}' record topilmadi "
            f"({len(recs)} record o'qildi)")
    return trials


def load_sweep(path: str) -> list[dict[str, Any]]:
    """`reduce.write_output` ning `sweep.jsonl` ini o'qiydi (§4 sweep)."""
    recs = _read_jsonl(path)
    cells = [r for r in recs if r.get("record_type") == DRT_SWEEP]
    if not cells:
        raise AnalysisError(
            f"{path}: birorta '{DRT_SWEEP}' record topilmadi "
            f"({len(recs)} record o'qildi)")
    return cells


def load_episodes(path: str) -> list[dict[str, Any]]:
    """`reduce.write_output` ning `episodes.jsonl` ini o'qiydi.

    §5 FR-A ni HAR ACTION va HAR EPIZOD uchun ta'riflaydi, va per-action
    FR-A AYNAN shu faylda yashaydi (`EpisodeResult.actions[].fr_a`).
    Shartnoma §2.1 uni kirish sifatida sanamagan -- `--episodes` ixtiyoriy
    va u berilmasa `trial_metrics` dan AYNAN YECHILADIGAN quyi to'plam
    ishlatiladi (`false_recovery_section` docstring'i).
    """
    recs = _read_jsonl(path)
    eps = [r for r in recs if r.get("record_type") == DRT_EPISODE]
    if not eps:
        raise AnalysisError(
            f"{path}: birorta '{DRT_EPISODE}' record topilmadi "
            f"({len(recs)} record o'qildi)")
    return eps


def load_events(path: str) -> list[dict[str, Any]]:
    """Run'ning `events.jsonl` idan FAQAT `prober_stop` record'larini oladi.

    NEGA XOM EVENT FAYLI O'QILADI: §8.2 prober CPU narxini HAR TRIAL uchun
    talab qiladi va `prober.py` uni `prober_stop` ga yozadi
    (`cost_report()` -> `cost.core_percent`, `cost.budget_percent`), lekin
    `reduce.py` `prober_stop` ni UMUMAN o'qimaydi va narxni
    `trial_metrics` ga chiqarmaydi -- va `reduce.py` TAHRIRLANMAYDI.
    Shuning uchun transport shu yerda: fayldan o'qiladi, hisoblanadi,
    faylga yoziladi -- modul hali ham QAT'IY OFFLINE (qoida 1).

    `driver-contract/v1.1` §4.5(a): driver HAR TRIAL uchun bitta prober
    jarayoni ishga tushiradi (`Prober.trial_id` jarayon boshida fiksa
    qilinadi va boshqaruv kanali yo'q), demak `prober_stop` har TRIAL
    uchun bir marta chiqadi va envelope'ida shu trial'ning `trial_id` si
    bo'ladi. Per-trial o'lchov manbada MAVJUD.

    FAYL BERILGAN, LEKIN `prober_stop` YO'Q bo'lsa -- BO'SH ro'yxat
    qaytariladi, `AnalysisError` EMAS.

    NEGA XATO EMAS: §2.3 #6 "hisoblab bo'lmagan narsa `warnings` ga, va
    taxmin qilinmaydi" deydi -- hisoblab bo'lmaslik XATO emas. Narx manbasi
    bo'sh bo'lsa `probe_cost` bo'limi chiqmaydi va sabab `warnings` ga
    tushadi (`probe_cost_events_empty`), xuddi `--sweep` berilmaganda
    `sensitivity.grid` bo'sh qolgani kabi.
    NEGA JIMGINA HAM EMAS: `None` (bayroq berilmagan) va `[]` (bayroq
    berilgan, lekin fayl bo'sh) `probe_cost_section` da AJRATILADI -- bu
    ikkinchisi "noto'g'ri faylni ko'rsatdingiz" ning signali va O'Z
    `warnings` kodiga ega.
    """
    recs = _read_jsonl(path)
    return [r for r in recs if r.get("record_type") == RT_PROBER_STOP]


def load_reduction_summary(path: str) -> dict[str, Any]:
    """`reduce.write_output` ning `reduction_summary.jsonl` ini o'qiydi.

    NEGA KERAK: `reduce_run` §16.4 ning ikki eksklyuziya darajasini
    (`exclusion_rate_binary_pvr_denominator`,
    `exclusion_rate_survival_analysis_set`), `summary["exclusions"][<set>]`
    obyektlarini (har biri O'Z `analysis_set` nomi bilan),
    `disposition_source_counts` ni va
    `vr_undetermined_in_binary_denominator` ni O'ZI hisoblaydi. Ikki
    mustaqil sanoq yo'li ikki xil raqam berishi mumkin, va eksklyuziya
    darajasi NATIJA (§12) -- demak reducer'ning raqami AVTORITET.

    Fayl bitta `reduction_summary` record'ini o'z ichiga oladi; bir
    nechtasi bo'lsa OXIRGISI olinadi (`JsonlWriter` append-only).
    """
    recs = _read_jsonl(path)
    rows = [r for r in recs if r.get("record_type") == DRT_SUMMARY]
    if not rows:
        raise AnalysisError(
            f"{path}: birorta '{DRT_SUMMARY}' record topilmadi "
            f"({len(recs)} record o'qildi)")
    return rows[-1]


def load_run_meta(path: str) -> dict[str, Any]:
    """`run_meta.json` -- BITTA obyekt (§1.1)."""
    with open(path, "r", encoding="utf-8") as fh:
        try:
            meta = json.load(fh)
        except json.JSONDecodeError as exc:
            raise AnalysisError(f"{path}: JSON parse xatosi: {exc}") from exc
    if not isinstance(meta, dict):
        raise AnalysisError(f"{path}: run_meta obyekt bo'lishi kerak")
    return meta


# --- kirish invariantlari --------------------------------------------------


def check_inputs(trials: Sequence[dict[str, Any]], log: WarningLog) -> None:
    """Analizdan OLDINGI struktura tekshiruvlari.

    Bu `revix/validate.py` NING O'RNINI BOSMAYDI (modul docstring'idagi
    VALIDATSIYA CHEKLOVI): validator xom record'larni talab qiladi. Bu yerda
    faqat derived kirishning o'zida ko'rinadigan buzilishlar tutiladi.
    """
    for r in trials:
        d = r.get("disposition")
        if d not in DISPOSITIONS:
            raise AnalysisError(
                f"trial {r.get('trial_id')!r}: disposition yopiq enumdan "
                f"tashqarida (§12): {d!r}")
    # §16.2(B) -- birlamchi to'plam `(disposition, disposition_source)` jufti
    # bilan aniqlanadi. Tanlovni `reduce.select_primary` qiladi, lekin
    # `disposition_source` yo'q bo'lsa eksklyuziya hisoboti ikki `censored`
    # turini AJRATA OLMAYDI (§16.4: nomlanmagan daraja takrorlanuvchi emas).
    n_no_src = sum(1 for r in trials if not r.get("disposition_source"))
    if n_no_src:
        log.add("disposition_source_missing", "exclusions",
                f"{n_no_src}/{len(trials)} trial'da `disposition_source` yo'q "
                "-- §16.2(B) ning ikki `censored` turi (`down_at_horizon` "
                "kuzatilgan no'l-hodisa, `probe_gap` kuzatilmagan) "
                "AJRATILMAYDI; eksklyuziya hisoboti shu darajada KAMROQ "
                "aniq bo'ladi. Taxmin qilinmaydi")
    n_conflict = sum(1 for r in trials if r.get("disposition_conflict"))
    if n_conflict:
        log.add("disposition_conflict", "n_trials",
                f"{n_conflict} trial: reducer xom disposition bilan derived "
                "disposition o'rtasida ziddiyat qayd etdi (reduce.py "
                "`disposition_source` ga qarang)")
    n_no_begin = sum(1 for r in trials if r.get("has_trial_begin") is False)
    n_no_end = sum(1 for r in trials if r.get("has_trial_end") is False)
    if n_no_begin:
        log.add("missing_trial_begin", "n_trials",
                f"{n_no_begin} trial `trial_begin` record'isiz")
    if n_no_end:
        log.add("missing_trial_end", "n_trials",
                f"{n_no_end} trial `trial_end` record'isiz (§1.3 #5 buzilgan)")

    # §12: FR-B P1 da BERILMAYDI. Kirishda hisoblangan FR-B bo'lsa -- bu
    # `analysis_version = p1/v1` bilan ziddiyat, jimgina yutilmaydi.
    bad = [r.get("trial_id") for r in trials
           if isinstance(r.get("fr_b"), dict) and r["fr_b"].get("computed")]
    if bad:
        raise AnalysisError(
            "kirishda hisoblangan FR-B bor, lekin PREREGISTRATION.md §5 ga "
            f"ko'ra P1 da FR-B BERILMAYDI (trial: {bad[:5]}); "
            f"analysis_version={ANALYSIS_VERSION} bu natijani chiqara olmaydi")


# --- §11 birlamchi endpoint ------------------------------------------------


def primary_section(primary_trials: Sequence[dict[str, Any]],
                    log: WarningLog) -> dict[str, Any]:
    """§10.1 + §11 -- BIRLAMCHI endpoint: `P(VR)` ning pressure bo'ylab trendi.

      * test: Cochran-Armitage trend `P0 < P1 < P2` bo'ylab (§10.1);
      * har yacheyka: Clopper-Pearson EXACT CI (§10.1);
      * effect size: risk difference + Newcombe CI (§10.1);
      * `falsified`: trend `p > 0.05` VA `P(VR|P0) - P(VR|P2)` uchun 95%
        Newcombe CI ning YUQORI chegarasi `< 0.15` (§11).

    NEGA `vr is None` DENOMINATORGA KIRMAYDI: `reduce.py` `vr=None` ni
    "aniqlanmagan" sifatida qaytaradi (throughput bandi o'lchanmadi yoki
    oyna kesildi). Uni muvaffaqiyatsizlik deb hisoblash -- ma'lumot
    yetishmovchiligini natijaga aylantirish; muvaffaqiyat deb hisoblash --
    liveness-only VR ga qulash (§4.5). Shuning uchun u SANAB `warnings` ga
    beriladi va `n` dan tashqarida qoladi.

    NEGA TENG MASOFALI SCORE'LAR: §10.1 trend uchun score tanlovini
    muzlatmagan, §9.4 esa uzluksiz erishilgan pressure'ni "qo'llab-quvvatlovchi,
    birlamchi emas" model uchun talab qiladi. Ma'lumotdan olingan score --
    forking path; teng masofali 0,1,2 Cochran-Armitage ning standart
    konvensiyasi va ma'lumotga BOG'LIQ EMAS.

    QAMROV -- ARM `A` ICHIDA (§16.2(A)). `PRIMARY_ARM` izohida sabab
    to'liq yozilgan. Qamrov chiqishda OCHIQ ko'rsatiladi (`primary.arm` va
    har yacheykaning `arm` maydoni), chunki §2.2 ning `cells` sxemasi
    faqat `level` kaliti bilan yozilgan va arm'siz yacheyka POOL QILINGAN
    natija deb o'qilishi mumkin -- §16.2(A) chalkashlikning manbai aynan
    shu ekanini aytadi.

    MAXRAJ -- `reduce.select_primary` NING QARORI (§16.2(B), §16.4). Bu
    funksiya `disposition` yoki `disposition_source` bo'yicha O'ZI
    tanlamaydi: u `build_analysis` bergan to'plamni oladi. §16.2(B) ga
    ko'ra `disposition_source == "down_at_horizon"` trial'lari maxrajga
    `VR = false` sifatida KIRADI (xizmat qaytmadi -- kuzatilgan
    NO'L-HODISA, §4 ning oynasi MAVJUD EMAS, demak to'liq aniqlangan),
    `"probe_gap"` esa KIRMAYDI (instrumentatsiya yo'qoldi -- kuzatilmagan).
    Bu farqni `reduce.py` beradi va u YAKKA MANBA; bu yerda qayta
    hisoblanmaydi (§16.6: `reduce.py` ni tuzatish muzlatilgan matnga
    MOSLASHTIRISH).
    """
    cells: list[dict[str, Any]] = []
    counts: dict[str, tuple[int, int]] = {}
    used: list[dict[str, Any]] = []

    # §16.2(A) -- trend FAQAT arm `A` ustida.
    arm_rows = [r for r in primary_trials if r.get("arm") == PRIMARY_ARM]
    n_other = len(primary_trials) - len(arm_rows)
    if n_other:
        log.add("primary_scope_other_arms_excluded", "primary",
                f"{n_other}/{len(primary_trials)} birlamchi trial arm "
                f"`{PRIMARY_ARM}` dan tashqarida -- §16.2(A) ga ko'ra trend "
                "testi arm ichida hisoblanadi (pooling `P(VR|P0)-P(VR|P2)` "
                "ni `0-0=0` ga intiltirib falsifikatsiya mezonini TRIVIAL "
                "qilardi). Bu trial'lar KM/log-rank, loop-rate va har "
                "jadvalning `k/n` qatorida QOLADI (§6.2) va §8.2 ning PSI "
                "atributsiyasi uchun ishlatiladi -- yashirilmaydi")
    if not arm_rows:
        log.add("primary_arm_empty", "primary",
                f"arm `{PRIMARY_ARM}` da birorta birlamchi trial yo'q -- "
                "§10.1 ning birlamchi testi HISOBLANMAYDI")

    for lvl in PRESSURE_LEVELS:
        rows = [r for r in arm_rows if r.get("pressure_band") == lvl]
        measured = [r for r in rows if r.get("vr") is not None]
        undet = len(rows) - len(measured)
        if undet:
            log.add("vr_undetermined", f"primary.cells.{lvl}",
                    f"{undet}/{len(rows)} trial: `vr` aniqlanmagan (None) -- "
                    "denominatorga KIRMAYDI, taxmin qilinmaydi")
        k = sum(1 for r in measured if r["vr"] is True)
        n = len(measured)
        counts[lvl] = (k, n)
        used.extend(measured)
        if n == 0:
            log.add("level_empty", f"primary.cells.{lvl}",
                    f"{lvl} darajasida o'lchangan trial yo'q -- proporsiya va "
                    "CI hisoblanmaydi")
            cells.append({"level": lvl, "arm": PRIMARY_ARM,
                          "k": 0, "n": 0, "p_hat": None,
                          "ci_lower": None, "ci_upper": None,
                          "ci_method": "clopper_pearson"})
            continue
        ci = S.clopper_pearson(k, n, ALPHA)
        # `p_hat` AYNAN `k/n` -- shu nisbatdan boshqa hech narsa emas.
        # NEGA to'g'ridan-to'g'ri: `p_hat != k/n` bo'lgan yacheyka figurada
        # BELGILANADI (tuzatilmaydi), shuning uchun u strukturaviy jihatdan
        # imkonsiz bo'lishi kerak, estimator'ga ishonishga emas.
        cells.append({"level": lvl, "arm": PRIMARY_ARM, "k": k, "n": n,
                      "p_hat": k / n,
                      "ci_lower": _f(ci.lower), "ci_upper": _f(ci.upper),
                      "ci_method": "clopper_pearson"})

    # --- Cochran-Armitage trend (BIRLAMCHI test, §10.1) ---
    statistic: float | None = None
    p_value: float | None = None
    direction: str | None = None
    ks = [counts[l][0] for l in PRESSURE_LEVELS]
    ns = [counts[l][1] for l in PRESSURE_LEVELS]
    if all(n > 0 for n in ns):
        try:
            trend = S.cochran_armitage_trend(ks, ns)
        except ValueError as exc:
            log.add("trend_not_computable", "primary.test", str(exc))
        else:
            statistic = _f(trend.statistic)
            p_value = _f(trend.p_value)
            # `stats.TrendResult.direction` "flat" beradi, §2.2 enumi esa
            # "none" -- SHARTNOMA sxemasi normativ, shuning uchun
            # moslashtiriladi. (`agent/contract` uchun amendment savoli.)
            direction = {"increasing": "increasing",
                         "decreasing": "decreasing",
                         "flat": "none"}[trend.direction]
    else:
        log.add("trend_not_computable", "primary.test",
                "Cochran-Armitage uchun uchala pressure darajasi ham bo'sh "
                f"bo'lmasligi kerak (n = {ns})")

    # --- effect size: risk difference P(VR|P0) - P(VR|P2) (§10.1, §11) ---
    contrast = f"{PRESSURE_LEVELS[0]}-{PRESSURE_LEVELS[-1]}"
    rd: dict[str, Any] = {"estimate": None, "ci_lower": None, "ci_upper": None,
                          "ci_method": "newcombe", "contrast": contrast}
    rd_upper: float | None = None
    k0, n0 = counts[PRESSURE_LEVELS[0]]
    k2, n2 = counts[PRESSURE_LEVELS[-1]]
    if n0 > 0 and n2 > 0:
        nc = S.newcombe_diff_ci(k0, n0, k2, n2, ALPHA)
        rd_upper = _f(nc.upper)
        rd = {"estimate": _f(nc.difference), "ci_lower": _f(nc.lower),
              "ci_upper": rd_upper, "ci_method": "newcombe",
              # §11 mezoni AYNAN `P(VR|P0) - P(VR|P2)` haqida -- nomsiz
              # farq talqin qilinmaydi.
              "contrast": contrast}
    else:
        log.add("risk_difference_not_computable", "primary.risk_difference",
                f"{PRESSURE_LEVELS[0]} va {PRESSURE_LEVELS[-1]} ning ikkisi "
                f"ham bo'sh bo'lmasligi kerak (n = {n0}, {n2})")

    # --- §11 falsifikatsiya mezoni ---
    if p_value is None or rd_upper is None:
        falsified: bool | None = None
        log.add("falsification_not_evaluable", "primary.falsified",
                "trend p-value yoki Newcombe yuqori chegarasi hisoblanmadi, "
                "demak §11 mezoni BAHOLANMAYDI -- `false` deb berish "
                "'falsifikatsiya qilinmadi' degan o'lchanmagan da'vo bo'lardi")
    else:
        falsified = bool(p_value > TREND_P_THRESHOLD
                         and rd_upper < NEWCOMBE_UPPER_THRESHOLD)

    return {
        "endpoint": PRIMARY_ENDPOINT,
        "test": PRIMARY_TEST,
        # §16.2(A) -- QAMROV OCHIQ. Arm'siz yacheyka pooling deb o'qilardi.
        "arm": PRIMARY_ARM,
        "scope": (f"within arm {PRIMARY_ARM} (PREREGISTRATION.md §16.2(A)); "
                  "not pooled across arms"),
        "statistic": statistic,
        "p_value": p_value,
        "direction": direction,
        "cells": cells,
        "ci_level": CI_LEVEL,
        "risk_difference": rd,
        "falsified": falsified,
        "falsification_rule": FALSIFICATION_RULE,
        # §2.3 #4 -- har jadval `k/n` bilan birga.
        "recovered_within_horizon": _k_of_n(used),
    }


# --- §10.2 survival --------------------------------------------------------


def _surv_arrays(records: Sequence[dict[str, Any]], log: WarningLog,
                 where: str) -> tuple[list[float], list[int], int]:
    """`time_to_vr` -> `(times_s, events, n_skipped)`.

    §6.2: CENSORED KUZATUV TASHLANMAYDI -- `event = 0` bo'lib KM/log-rank ga
    KIRADI. Tashlanadigan yagona narsa -- `time_to_vr_us is None`, ya'ni
    O'LCHANMAGAN kuzatuv (epizod yo'q); u `warnings` da sanaladi.
    """
    times: list[float] = []
    events: list[int] = []
    skipped = 0
    for r in records:
        t = r.get("time_to_vr_us")
        if t is None:
            skipped += 1
            continue
        tv = _f(t)
        if tv is None or tv < 0.0:
            skipped += 1
            log.add("time_to_vr_invalid", where,
                    f"trial {r.get('trial_id')!r}: time_to_vr_us={t!r} -- "
                    "yaroqsiz, tashlab ketildi")
            continue
        # §1: MIKROSEKUNDDA qoldiriladi. `tau` ham mikrosekundda
        # (`TAU_RMST_US`), demak birlik o'zgarishi YO'Q.
        times.append(tv)
        events.append(0 if r.get("time_to_vr_censored") else 1)
    if skipped:
        log.add("time_to_vr_missing", where,
                f"{skipped} trial: `time_to_vr_us` o'lchanmagan (None) -- "
                "survival analiziga kirmaydi")
    return times, events, skipped


def _km_quantiles(times: Sequence[float], events: Sequence[int],
                  log: WarningLog, where: str, *, n_boot: int,
                  seed_path: list[int]) -> dict[str, Any]:
    """KM kvantillari + §2.3 #8 fallback.

    §2.3 #8: "p90/p99 KM'dan `nan` bo'lsa -- CENSORED BO'LMAGAN qism ustida
    BCa bootstrap". Bu `stats.km_quantile` ning HUJJATLASHTIRILGAN cheklovi:
    egri chiziq `1 - q` gacha tushmasa u `nan` qaytaradi (oxirgi kuzatilgan
    vaqtni median deb ko'rsatmaydi). Fallback har doim `source` va
    `warnings` da AYTILADI.
    """
    km = S.kaplan_meier(times, events)
    out: dict[str, Any] = {}
    for i, (name, q) in enumerate(QUANTILES):
        est = _f(S.km_quantile(km, q))
        entry = _quantile_entry_from_km(est)
        if est is None:
            unc = [t for t, e in zip(times, events) if e == 1]
            log.add("km_quantile_nan", f"{where}.{name}",
                    f"KM egri chizig'i {name} ga ({1.0 - q:.2f} survival) "
                    "tushmadi -- §2.3 #8 bo'yicha CENSORED BO'LMAGAN qism "
                    f"ustida BCa bootstrap'ga qaytiladi (n_uncensored={len(unc)})")
            entry = _bootstrap_quantile(
                unc, q, log, f"{where}.{name}", n_boot=n_boot,
                seed_path=seed_path + [i], source="bca_bootstrap_uncensored",
                note=("fallback from Kaplan-Meier: km_quantile returned nan "
                      "(documented limitation of stats.km_quantile); computed "
                      "on the uncensored portion only, per §2.3 #8"))
        out[name] = entry
    return out


def _quantile_entry_from_km(est: float | None) -> dict[str, Any]:
    """KM'dan olingan kvantil. CI YO'Q -- ochiq bayon.

    NEGA CI YO'Q: `stats.py` KM kvantili uchun confidence interval bermaydi
    (Brookmeyer-Crowley yoki shunga o'xshash metod u yerda YO'Q), va §10.3
    "dependency qo'shmasdan" deydi. `stats.bootstrap_ci` esa o'z
    docstring'ida CENSORED ma'lumot uchun YARAMAYDI deb yozilgan. Soxta CI
    berish o'rniga `None` beriladi.
    """
    return {
        "estimate": est,
        "source": "kaplan_meier" if est is not None else None,
        "ci_lower": None, "ci_upper": None, "ci_method": None,
        "ci_basis": None, "n_boot": None, "rng_seed": None,
        "note": ("no confidence interval: stats.py provides no censoring-aware "
                 "quantile CI (e.g. Brookmeyer-Crowley) and BCa bootstrap is "
                 "invalid under censoring" if est is not None else None),
    }


def _quantile_fn(q: float) -> Callable[..., Any]:
    """`np.quantile` ning vektorlashgan qobig'i (scipy `axis` ni talab qiladi)."""

    def f(x: Any, axis: int = -1) -> Any:
        return np.quantile(x, q, axis=axis)

    return f


def _bootstrap_quantile(values: Sequence[float], q: float, log: WarningLog,
                        where: str, *, n_boot: int, seed_path: list[int],
                        source: str, note: str | None,
                        ci_basis: str = "uncensored_subsample"
                        ) -> dict[str, Any]:
    """§10.2 -- kvantil + BCa bootstrap CI.

    `stats.bootstrap_ci` BCa degenerativ bo'lsa percentile'ga qaytadi va
    natijaning `method` maydonida AYNAN ishlatilgan metodni beradi; shu
    maydon hisobotga ko'chiriladi (soxta "BCa" yorlig'i YO'Q).
    """
    empty = {"estimate": None, "source": None, "ci_lower": None,
             "ci_upper": None, "ci_method": None, "ci_basis": None,
             "n_boot": None, "rng_seed": None, "note": note}
    if len(values) == 0:
        log.add("bootstrap_no_data", where,
                "bootstrap uchun kuzatuv yo'q -- kvantil hisoblanmaydi")
        return empty
    point = _f(np.quantile(np.asarray(values, dtype=float), q))
    if len(values) < 2:
        log.add("bootstrap_n_too_small", where,
                f"n={len(values)} -- bootstrap CI hisoblanmaydi (jackknife "
                "kamida 2 kuzatuv talab qiladi); nuqtaviy baho CI'siz beriladi")
        return {"estimate": point, "source": source, "ci_lower": None,
                "ci_upper": None, "ci_method": None, "ci_basis": ci_basis,
                "n_boot": None, "rng_seed": None, "note": note}
    rng = np.random.default_rng([BOOTSTRAP_SEED, *seed_path])
    try:
        bca = _capture(
            lambda: S.bootstrap_ci(np.asarray(values, dtype=float),
                                   _quantile_fn(q), alpha=ALPHA,
                                   n_boot=n_boot, method="bca", rng=rng),
            log, where, code="bootstrap_warning")
    except (ValueError, RuntimeError) as exc:
        log.add("bootstrap_failed", where,
                f"BCa bootstrap hisoblanmadi: {exc}")
        return {"estimate": point, "source": source, "ci_lower": None,
                "ci_upper": None, "ci_method": None, "ci_basis": ci_basis,
                "n_boot": None, "rng_seed": None, "note": note}
    if bca.method != bca.method_requested:
        log.add("bootstrap_method_fallback", where,
                f"so'ralgan metod {bca.method_requested!r}, ishlatilgani "
                f"{bca.method!r} -- hisobotda ISHLATILGANI beriladi")
    return {
        "estimate": _f(bca.estimate), "source": source,
        "ci_lower": _f(bca.lower), "ci_upper": _f(bca.upper),
        "ci_method": bca.method, "ci_basis": ci_basis,
        "n_boot": int(bca.n_boot),
        "rng_seed": [BOOTSTRAP_SEED, *seed_path],
        "note": note,
    }


_EMPTY_KM = {"times": [], "survival": [], "at_risk": [], "greenwood_var": [],
             "n_events": [], "n_total": 0, "n_censored": 0, "quantiles": {}}


def _km_group(groups: dict[str, list[dict[str, Any]]], where_prefix: str,
              log: WarningLog, *, n_boot: int, seed_tag: int
              ) -> tuple[dict[str, dict[str, Any]],
                         dict[str, tuple[list[float], list[int]]]]:
    """Guruhlangan trial'lar -> `{label: KM bloki}` va `{label: (times, events)}`.

    Guruhlash o'qi ERKIN: `by_arm` (§10.2) va `by_pressure_band`
    (shartnoma §2.10, §11 uchun) AYNAN BIR XIL shaklda chiqadi, shuning
    uchun bir funksiya. Shakl bir xil bo'lmasa figura ikki xil o'qish yo'li
    yozishga majbur bo'lardi.
    """
    out: dict[str, dict[str, Any]] = {}
    arrays: dict[str, tuple[list[float], list[int]]] = {}
    for gi, label in enumerate(sorted(groups)):
        where = f"{where_prefix}.{label}"
        times, events, _sk = _surv_arrays(groups[label], log, where)
        if not times:
            log.add("km_no_data", where,
                    "o'lchangan time-to-VR yo'q -- KM egri chizig'i "
                    "hisoblanmaydi")
            out[label] = dict(_EMPTY_KM)
            continue
        arrays[label] = (times, events)
        km = S.kaplan_meier(times, events)
        out[label] = {
            "times": _flist(km.times),
            "survival": _flist(km.survival),
            "at_risk": _ilist(km.at_risk),
            "greenwood_var": _flist(km.variance),
            "n_events": _ilist(km.n_events),
            "n_total": int(km.n_total),
            "n_censored": int(km.n_censored),
            "quantiles": _km_quantiles(times, events, log, where,
                                       n_boot=n_boot,
                                       seed_path=[seed_tag, gi]),
        }
    return out, arrays


def _logrank_pair(arrays: dict[str, tuple[list[float], list[int]]],
                  a: str, b: str, where: str, log: WarningLog
                  ) -> dict[str, Any]:
    """Ikki guruh orasida log-rank. `stats.logrank` AYNAN ikkitasini oladi."""
    empty = {"chi2": None, "p_value": None, "observed": {}, "expected": {},
             "contrast": f"{a}-{b}"}
    if a not in arrays or b not in arrays:
        log.add("logrank_not_computable", where,
                f"log-rank uchun `{a}` va `{b}` ning IKKISI ham kerak; "
                f"o'lchangan guruhlar: {sorted(arrays)}")
        return empty
    lr = _capture(lambda: S.logrank(arrays[a][0], arrays[a][1],
                                    arrays[b][0], arrays[b][1]), log, where)
    out = {
        "chi2": _f(lr.statistic), "p_value": _f(lr.p_value),
        "observed": {a: _f(lr.observed_a), b: _f(lr.observed_b)},
        "expected": {a: _f(lr.expected_a), b: _f(lr.expected_b)},
        "contrast": f"{a}-{b}",
    }
    if out["p_value"] is None:
        log.add("logrank_degenerate", where,
                "log-rank statistikasi aniqlanmagan (varians nol yoki "
                "event yo'q)")
    return out


def _rmst_group(arrays: dict[str, tuple[list[float], list[int]]],
                where_prefix: str, log: WarningLog) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for label in sorted(arrays):
        t, e = arrays[label]
        where = f"{where_prefix}.{label}"
        try:
            res = _capture(lambda: S.rmst(t, e, TAU_RMST_US), log, where)
        except ValueError as exc:
            log.add("rmst_not_computable", where, str(exc))
            out[label] = {"estimate": None, "se": None}
            continue
        out[label] = {"estimate": _f(res.rmst), "se": _f(res.std_err)}
    return out


def _rmst_pair(arrays: dict[str, tuple[list[float], list[int]]],
               a: str, b: str, where: str, log: WarningLog,
               code_prefix: str) -> dict[str, Any]:
    """`a - b` RMST farqi. `contrast` HAR DOIM beriladi (shartnoma §2.8:
    nomsiz/belgisiz farq TALQIN QILINMAYDI)."""
    empty = {"contrast": f"{a}-{b}", "tau": TAU_RMST_US, "estimate": None,
             "se": None, "ci_lower": None, "ci_upper": None}
    if a not in arrays or b not in arrays:
        log.add(f"{code_prefix}_not_computable", where,
                f"RMST farqi uchun `{a}` va `{b}` ning IKKISI ham kerak; "
                f"o'lchangan guruhlar: {sorted(arrays)}")
        return empty
    try:
        rd = _capture(lambda: S.rmst_difference(arrays[a], arrays[b],
                                                TAU_RMST_US, ALPHA),
                      log, where)
    except ValueError as exc:
        log.add(f"{code_prefix}_not_computable", where, str(exc))
        return empty
    out = {"contrast": f"{a}-{b}", "tau": TAU_RMST_US,
           "estimate": _f(rd.difference), "se": _f(rd.std_err),
           "ci_lower": _f(rd.lower), "ci_upper": _f(rd.upper)}
    if out["se"] in (None, 0.0):
        log.add(f"{code_prefix}_degenerate", where,
                "RMST farqining standard error'i nol yoki aniqlanmagan -- "
                "CI MA'NOSIZ, talqin qilinmaydi")
    return out


def survival_section(survival_trials: Sequence[dict[str, Any]],
                     log: WarningLog, *, n_boot: int) -> dict[str, Any]:
    """§10.2 -- KM time-to-VR, log-rank, RMST (`tau = 8 s` = 8_000_000 us).

    §2.3 #3 -- CENSORED TRIAL'LAR KIRADI. Kirish to'plami
    `reduce.select_survival` bilan tanlanadi (`complete` + `censored`), chunki
    §6.2 ularni tashlashni ATAYLAB taqiqlaydi: tashlash tez ishdan chiqadigan
    arm'ni chiroyli ko'rsatadi. §16.2(B): `down_at_horizon` HAM, `probe_gap`
    HAM bu yerga CENSORED DAVOMIYLIK sifatida kiradi -- §6.2 davomiylikni
    censor qiladi, binar natijani emas.

    §2.3 #2 -- `proportional_hazards_checked` HAR DOIM `false`: `stats.py` da
    Schoenfeld residual testi YO'Q (ataylab -- modul docstring'i qoida 3),
    demak HR/Cox CHIQARILMAYDI. §10.2: "Schoenfeld residual'lari
    tekshirilmasa, HR berilmaydi."

    IKKI GURUHLASH O'QI -- IKKISI HAM KERAK, ular BOSHQA SAVOLGA javob
    beradi (§16.5, shartnoma §2.10):

      * `by_arm` (§10.2) -- taqdimot va stratifikatsiya birligi.
        `A` vs `no_action` log-rank §8.2 ning ATRIBUTSIYA savoliga javob
        beradi ("restart PSI ni oshirdimi yoki fault'ning o'zi?"), H1 ga
        EMAS.
      * `by_pressure_band` (§11) -- `ARM A ICHIDA`. §11 ning fail-slow
        bandi AYNAN `P0` va `P2` orasidagi time-to-VR RMST farqini
        (`tau = 8 s`) nomlaydi. §16.5 uni §16.2(A) bilan BIR XIL asos
        bilan arm `A` ichiga qo'yadi: `no_action` da time-to-VR uchala
        darajada ta'rifan mavjud emas, demak u yerda kontrast BO'SH, va
        pool qilish §16.2(A) dagi aynan o'sha susaytirish bo'lardi.

    KM egri chiziqlari pressure bo'yicha ham BERILADI, chunki
    `pressure_difference` HOSILA qiymat: egri chiziqlar berilmasa uni
    TEKSHIRIB BO'LMAYDI (shartnoma §2.10).
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    for r in survival_trials:
        groups.setdefault(str(r.get("arm")), []).append(r)

    by_arm, arm_arrays = _km_group(groups, "survival.km.by_arm", log,
                                   n_boot=n_boot, seed_tag=1)

    # --- log-rank, arm bo'yicha (§10.2 / §8.2 atributsiyasi) ---
    arms = sorted(arm_arrays)
    if len(arms) == 2:
        logrank = _logrank_pair(arm_arrays, arms[0], arms[1],
                                "survival.logrank", log)
    else:
        logrank = {"chi2": None, "p_value": None, "observed": {},
                   "expected": {}, "contrast": None}
        log.add("logrank_not_computable", "survival.logrank",
                f"log-rank AYNAN ikki guruh talab qiladi, topilgani: {arms}")

    rmst_by_arm = _rmst_group(arm_arrays, "survival.rmst.by_arm", log)
    if len(arms) == 2:
        diff = _rmst_pair(arm_arrays, arms[0], arms[1],
                          "survival.rmst.difference", log, "rmst_difference")
    else:
        diff = {"contrast": None, "tau": TAU_RMST_US, "estimate": None,
                "se": None, "ci_lower": None, "ci_upper": None}
        log.add("rmst_difference_not_computable", "survival.rmst.difference",
                f"RMST farqi AYNAN ikki guruh talab qiladi, topilgani: {arms}")

    # --- pressure o'qi, ARM `A` ICHIDA (§16.5, shartnoma §2.10) ---
    arm_a = [r for r in survival_trials if r.get("arm") == PRIMARY_ARM]
    if not arm_a:
        log.add("pressure_contrast_arm_empty", "survival.rmst",
                f"arm `{PRIMARY_ARM}` da survival trial yo'q -- §11 ning "
                "fail-slow mezoni uchun pressure kontrasti HISOBLANMAYDI")
    pgroups: dict[str, list[dict[str, Any]]] = {}
    for r in arm_a:
        band = r.get("pressure_band")
        if band in PRESSURE_LEVELS:
            pgroups.setdefault(str(band), []).append(r)
    km_by_band, band_arrays = _km_group(
        pgroups, "survival.km.by_pressure_band", log, n_boot=n_boot,
        seed_tag=3)
    rmst_by_band = _rmst_group(band_arrays,
                               "survival.rmst.by_pressure_band", log)
    lo, hi = PRESSURE_LEVELS[0], PRESSURE_LEVELS[-1]
    logrank_by_band = _logrank_pair(band_arrays, lo, hi,
                                    "survival.logrank.by_pressure_band", log)
    pressure_difference = _rmst_pair(
        band_arrays, lo, hi, "survival.rmst.pressure_difference", log,
        "rmst_pressure_difference")

    # §11 ning 20% chegarasi: mezon "95% CI 20% OSHISHNI chiqarib tashlasa"
    # deydi, lekin 20% NIMAGA NISBATAN ekanini (`RMST(P0)` gami, boshqa
    # miqdorgami) §11 AYTMAYDI. Transport beriladi, HUKM berilmaydi --
    # chegarani bu yerda tanlash muzlatilgan mezonni qayta yozish bo'lardi.
    if pressure_difference["estimate"] is not None:
        log.add("fail_slow_threshold_reference_unspecified",
                "survival.rmst.pressure_difference",
                "§11 ning fail-slow mezoni '95% CI 20% oshishni chiqarib "
                "tashlasa' deydi, lekin 20% QAYSI miqdorga nisbatan ekani "
                "§11 da yozilmagan (masalan `RMST(P0)` ning 20% imi). "
                "Kontrast (estimate/se/CI) BERILADI, lekin HUKM "
                "(`fail_slow_supported`) HISOBLANMAYDI -- chegarani bu "
                "yerda tanlash muzlatilgan mezonni qayta yozish bo'lardi. "
                "PREREGISTRATION/shartnoma uchun ochiq savol")
    else:
        # Shartnoma §3.1 degradatsiya qoidasi: figura "§11 fail-slow
        # criterion not evaluable" deb yozadi va ARM kontrastini uning
        # O'RNIGA KO'RSATMAYDI.
        log.add("fail_slow_not_evaluable",
                "survival.rmst.pressure_difference",
                "§11 ning fail-slow mezoni BAHOLANMAYDI: `P0`-`P2` "
                f"pressure kontrasti arm `{PRIMARY_ARM}` ichida "
                "hisoblanmadi. Shartnoma §3.1 ga ko'ra figura buni AYTADI "
                "va arm kontrastini uning O'RNIGA KO'RSATMAYDI")

    n_censored = sum(1 for r in survival_trials
                     if r.get("time_to_vr_us") is not None
                     and bool(r.get("time_to_vr_censored")))
    # §2.3 #6 ning ENG MUHIM holati: `vr=None` -- ALOHIDA kategoriya.
    # `reduce.py` uni aniq sabab bilan qaytaradi (`r_ref_unavailable`,
    # `window_truncated`) va `None` HECH QACHON `False` emas. Agar
    # aniqlanmagan trial "recovered emas" ga qo'shilsa, ma'lumot
    # yetishmovchiligi natijaga aylanardi.
    n_undetermined = sum(1 for r in survival_trials if r.get("vr") is None)
    if n_undetermined:
        log.add("vr_undetermined", "survival.censoring",
                f"{n_undetermined}/{len(survival_trials)} survival trial: "
                "`vr` aniqlanmagan (None) -- ALOHIDA kategoriya, "
                "'recovered emas' ga QO'SHILMAYDI")
    band_scope = (f"within arm {PRIMARY_ARM} "
                  "(PREREGISTRATION.md §16.5); not pooled across arms")
    return {
        "km": {"by_arm": by_arm, "by_pressure_band": km_by_band,
               "by_pressure_band_scope": band_scope},
        "logrank": dict(logrank, by_pressure_band=logrank_by_band),
        "rmst": {"tau": TAU_RMST_US, "by_arm": rmst_by_arm,
                 "difference": diff,
                 "by_pressure_band": rmst_by_band,
                 "pressure_difference": pressure_difference,
                 "by_pressure_band_scope": band_scope},
        # §2.3 #2 -- tekshirilmagan, demak HR/Cox CHIQMAYDI.
        "proportional_hazards_checked": False,
        "censoring": {"n_censored": n_censored,
                      "n_undetermined": n_undetermined,
                      "recovered_within_horizon": _k_of_n(survival_trials)},
    }


# --- §5 false recovery -----------------------------------------------------


def _fr_a_rate(rows: Sequence[dict[str, Any]]) -> float | None:
    """FR-A ulushi. `fr_a is None` KIRMAYDI (`None` -> `False` aylanmaydi)."""
    usable = [r for r in rows if r.get("fr_a") is not None]
    if not usable:
        return None
    return sum(1 for r in usable if r["fr_a"] is True) / len(usable)


def _fr_a_from_episodes(primary_trials: Sequence[dict[str, Any]],
                        episodes: Sequence[dict[str, Any]],
                        log: WarningLog) -> dict[str, Any]:
    """§5 -- HAQIQIY per-action va per-epizod FR-A `episodes.jsonl` dan.

    §5: "Har action uchun va har epizod uchun hisoblanadi (epizod
    darajasida = >=1 FR-A action)." `reduce.build_episodes` aynan shuni
    yozadi: `EpisodeResult.fr_a` = epizod darajasi,
    `EpisodeResult.actions[].fr_a` = action darajasi.

    Epizodlar `trial_id` bo'yicha BIRLAMCHI trial to'plamiga qisqartiriladi
    (§12: faqat `complete` birlamchi analizga kiradi). Boshqa disposition'ga
    tegishli epizodlar jimgina kirmaydi -- ular sanalib `warnings` ga
    beriladi.

    `None` (aniqlanmagan) na numeratorga, na denominatorga kirmaydi.
    """
    primary_ids = {r.get("trial_id") for r in primary_trials}
    mine = [e for e in episodes if e.get("trial_id") in primary_ids]
    foreign = len(episodes) - len(mine)
    if foreign:
        log.add("fr_a_episodes_outside_primary", "false_recovery.fr_a",
                f"{foreign}/{len(episodes)} epizod birlamchi bo'lmagan "
                "trial'ga tegishli -- FR-A birlamchi to'plamdan hisoblanadi "
                "(§12), demak ular kirmaydi")

    ep_vals = [e.get("fr_a") for e in mine]
    ac_vals: list[Any] = []
    n_no_actions = 0
    for e in mine:
        acts = e.get("actions")
        if not isinstance(acts, list):
            n_no_actions += 1
            continue
        if not acts:
            # `no_action` arm: epizodda action YO'Q (reduce.py anchor'ni
            # onset'ga qo'yadi). Bu "FR-A = 0" EMAS -- action bo'lmasa
            # per-action FR-A ta'riflanmagan, demak u sanalmaydi.
            n_no_actions += 1
            continue
        for a in acts:
            if isinstance(a, dict):
                ac_vals.append(a.get("fr_a"))
    if n_no_actions:
        log.add("fr_a_episode_without_action", "false_recovery.fr_a.per_action",
                f"{n_no_actions}/{len(mine)} epizodda action yo'q (masalan "
                "`no_action` arm) -- per-action FR-A u yerda TA'RIFLANMAGAN "
                "va denominatorga kirmaydi; nol deb olinmaydi")

    def rate(vals: Sequence[Any], where: str, label: str) -> float | None:
        usable = [v for v in vals if v is not None]
        n_undet = len(vals) - len(usable)
        if n_undet:
            log.add("fr_a_undetermined", where,
                    f"{n_undet}/{len(vals)} {label}: FR-A aniqlanmagan "
                    "(None) -- VR yoki aktor da'vosi o'lchanmagan; "
                    "denominatorga kirmaydi")
        if not usable:
            log.add("fr_a_not_computable", where,
                    f"o'lchangan {label} yo'q -- FR-A HISOBLANMAYDI")
            return None
        return sum(1 for v in usable if v is True) / len(usable)

    per_episode = rate(ep_vals, "false_recovery.fr_a.per_episode", "epizod")
    per_action = rate(ac_vals, "false_recovery.fr_a.per_action", "action")
    return {
        "per_action": _f(per_action),
        "per_episode": _f(per_episode),
        # §2.2 `n_undetermined` -- EPIZOD darajasida aniqlanmaganlar soni
        # (FR-A ning birlamchi birligi §5 ga ko'ra epizod).
        "n_undetermined": sum(1 for v in ep_vals if v is None),
        "basis": {
            "source": "episodes.jsonl (--episodes)",
            "trial_set": "primary (disposition == complete)",
            "n_trials": len(primary_trials),
            "n_episodes": len(mine),
            "n_actions": len(ac_vals),
            "n_resolvable_per_episode": sum(1 for v in ep_vals
                                            if v is not None),
            "n_resolvable_per_action": sum(1 for v in ac_vals
                                           if v is not None),
        },
    }


def false_recovery_section(primary_trials: Sequence[dict[str, Any]],
                           log: WarningLog,
                           episodes: Sequence[dict[str, Any]] | None = None
                           ) -> dict[str, Any]:
    """§5 -- FR-A (BIRLAMCHI, oracle-free) va FR-B (P1 da BERILMAYDI).

    `fr_b.computed = false`, `reason = "no calibration matrix (P1)"` --
    §2.2 AYNAN shu satrni talab qiladi, va §5 sababini beradi: `Repairs()`
    kalibratsiya eksperimentidan keladi, u esa P1 da hali yo'q. Nol qaytarish
    "false recovery yo'q" degan O'LCHANMAGAN da'vo bo'lardi.

    IKKI YO'L, va qaysi biri ishlatilgani `fr_a.basis.source` da YOZILADI:

      1. `episodes` BERILGAN (`--episodes`): §5 ning HAQIQIY ta'riflari --
         per-action FR-A `EpisodeResult.actions[].fr_a` dan, per-epizod
         FR-A `EpisodeResult.fr_a` dan. Bu §2.2 talab qilgan narsa.
      2. `episodes` BERILMAGAN: faqat AYNAN YECHILADIGAN quyi to'plam
         (modul docstring'idagi FR-A CHEKLOVI). Denominator §2.2 so'ragandan
         TORROQ, lekin u o'lchangan -- taxmin emas.

    NEGA IKKINCHI YO'L SAQLANADI: `--episodes` siz ishga tushirilgan run
    ham himoya qilinadigan narsa chiqarishi kerak, hech narsa emas. Va
    `basis` IKKI HOLATDA HAM beriladi -- qaysi denominator ishlatilgani
    reviewer birinchi so'raydigan narsa.
    """
    if episodes is not None:
        return {
            "fr_a": _fr_a_from_episodes(primary_trials, episodes, log),
            "fr_b": {"computed": False, "reason": FR_B_REASON_P1},
        }
    log.add("fr_a_episodes_absent", "false_recovery.fr_a",
            "`--episodes` berilmagan: §5 ning per-action/per-epizod FR-A si "
            "`episodes.jsonl` da (`EpisodeResult.actions[].fr_a`). "
            "`trial_metrics` dan faqat AYNAN YECHILADIGAN quyi to'plam "
            "hisoblanadi (`n_episodes == 1`, per-action uchun yana "
            "`n_actions == 1`) -- denominator §2.2 so'ragandan TORROQ, va "
            "u `fr_a.basis` da yozilgan")
    n_total = len(primary_trials)
    n_undetermined = sum(1 for r in primary_trials if r.get("fr_a") is None)
    if n_undetermined:
        log.add("fr_a_undetermined", "false_recovery.fr_a",
                f"{n_undetermined}/{n_total} trial: FR-A aniqlanmagan (None) "
                "-- VR yoki aktor da'vosi o'lchanmagan; denominatorga kirmaydi")

    ep_rows = [r for r in primary_trials if r.get("n_episodes") == 1]
    ac_rows = [r for r in ep_rows if r.get("n_actions") == 1]
    n_skip_ep = n_total - len(ep_rows)
    n_skip_ac = n_total - len(ac_rows)
    if n_skip_ep:
        log.add("fr_a_per_episode_unresolvable", "false_recovery.fr_a.per_episode",
                f"{n_skip_ep}/{n_total} trial `n_episodes != 1` -- per-epizod "
                "FR-A `trial_metrics` dan AYNAN yechilmaydi (u "
                "`episodes.jsonl` da; §2.1 uni kirish sifatida bermaydi). "
                "Bu trial'lar denominatorga KIRMAYDI, taxmin qilinmaydi")
    if n_skip_ac:
        log.add("fr_a_per_action_unresolvable", "false_recovery.fr_a.per_action",
                f"{n_skip_ac}/{n_total} trial `n_episodes != 1` yoki "
                "`n_actions != 1` -- per-action FR-A `trial_metrics` dan "
                "AYNAN yechilmaydi (u `episodes.jsonl` da). Bu trial'lar "
                "denominatorga KIRMAYDI, taxmin qilinmaydi")

    per_episode = _fr_a_rate(ep_rows)
    per_action = _fr_a_rate(ac_rows)
    if per_episode is None:
        log.add("fr_a_per_episode_not_computable",
                "false_recovery.fr_a.per_episode",
                "aynan yechiladigan trial yo'q -- FR-A per-epizod "
                "HISOBLANMAYDI")
    if per_action is None:
        log.add("fr_a_per_action_not_computable",
                "false_recovery.fr_a.per_action",
                "aynan yechiladigan trial yo'q -- FR-A per-action "
                "HISOBLANMAYDI")

    return {
        "fr_a": {
            "per_action": _f(per_action),
            "per_episode": _f(per_episode),
            "n_undetermined": n_undetermined,
            "basis": {
                "source": "trials.jsonl exactly-resolvable subset "
                          "(no --episodes)",
                "trial_set": "primary (disposition == complete)",
                "n_trials": n_total,
                "n_resolvable_per_action": sum(
                    1 for r in ac_rows if r.get("fr_a") is not None),
                "n_resolvable_per_episode": sum(
                    1 for r in ep_rows if r.get("fr_a") is not None),
            },
        },
        # §5 -- P1 da Repairs() YO'Q, demak FR-B BERILMAYDI.
        "fr_b": {"computed": False, "reason": FR_B_REASON_P1},
    }


# --- §6.1 downtime ---------------------------------------------------------


def _ecdf(km: Any) -> dict[str, Any] | None:
    """§10.2 -- TO'LIQ ECDF: `F(t) = 1 - S(t)`, step funksiya.

    NEGA KM'DAN: `D_sd` va `D_probe` CENSORED bo'lishi mumkin (§6.2), va
    censored kuzatuvni tashlab oddiy ECDF chizish tez ishdan chiqadigan
    arm'ni chiroyli ko'rsatardi. Censoring BO'LMAGANDA `1 - S(t)` oddiy
    ECDF ga AYNAN teng, demak bu umumlashtirish, almashtirish emas.

    NEGA INTERPOLYATSIYA YO'Q: faqat KUZATILGAN event vaqtlari va ularda
    sakrash qiymatlari beriladi. Silliqlangan egri chiziq o'lchanmagan
    oraliqda qiymat BOR deb da'vo qilardi.
    """
    if km.times.size == 0:
        return None
    return {
        "x": _flist(km.times),
        "y": [1.0 - v for v in _flist(km.survival)],
        "method": "1 - kaplan_meier (step function; equals the plain ECDF "
                  "when nothing is censored)",
    }


def downtime_section(primary_trials: Sequence[dict[str, Any]],
                     log: WarningLog, *, n_boot: int) -> dict[str, Any]:
    """§6.1 -- `D_sd`, `D_probe`, `D_eff`: UCHALASI HAM HAR DOIM beriladi.

    §6.1 ning sababi ochiq: `D_sd` eng chalg'ituvchi (`active` lekin 20%
    throughput'dagi xizmat NOL downtime ko'rsatadi), `D_eff` esa brownout'ni
    ham hisoblaydigan yagona o'lchov. Faqat bittasini berish -- tanlov orqali
    natijani boshqarish.

    Kvantil hisobi (§10.2 "median, p90, p99 + BCa bootstrap CI"):
      1. Nuqtaviy baho Kaplan-Meier dan olinadi, chunki `D_sd` va `D_probe`
         CENSORED bo'lishi mumkin (§6.2) va `stats.bootstrap_ci` o'z
         docstring'ida censored ma'lumot uchun YARAMAYDI deb yozilgan.
      2. KM `nan` qaytarsa -- §2.3 #8 bo'yicha CENSORED BO'LMAGAN qism
         ustida BCa bootstrap, va bu `source` da AYTILADI.
    """
    out: dict[str, Any] = {}
    for mi, (name, value_field, censor_field) in enumerate(DOWNTIME_MEASURES):
        where = f"downtime.{name}"
        vals: list[float] = []
        cens: list[bool] = []
        rows: list[dict[str, Any]] = []
        missing = 0
        for r in primary_trials:
            v = _f(r.get(value_field))
            if v is None or v < 0.0:
                missing += 1
                continue
            vals.append(v)
            cens.append(bool(r.get(censor_field)) if censor_field else False)
            rows.append(r)
        if missing:
            log.add("downtime_missing", where,
                    f"{missing}/{len(primary_trials)} trial: "
                    f"`{value_field}` o'lchanmagan (None) -- jadvalga "
                    "kirmaydi, nol deb olinmaydi")
        note = D_EFF_NOTE if censor_field is None else None
        block: dict[str, Any] = {
            "unit": TIME_UNIT,
            "n": len(vals),
            "n_censored": (sum(1 for c in cens if c)
                           if censor_field is not None else None),
            "n_missing": missing,
            "censoring_flag": censor_field,
            "recovered_within_horizon": _k_of_n(rows),
            "note": note,
        }
        if not vals:
            log.add("downtime_no_data", where,
                    "o'lchangan qiymat yo'q -- kvantillar HISOBLANMAYDI")
            log.add("ecdf_not_computable", where,
                    "o'lchangan qiymat yo'q -- ECDF HISOBLANMAYDI va "
                    "chiqarilmaydi")
            for q_name, _q in QUANTILES:
                block[q_name] = {
                    "estimate": None, "source": None, "ci_lower": None,
                    "ci_upper": None, "ci_method": None, "ci_basis": None,
                    "n_boot": None, "rng_seed": None, "note": None}
            out[name] = block
            continue

        events = [0 if c else 1 for c in cens]
        km = S.kaplan_meier(vals, events)
        uncensored = [v for v, c in zip(vals, cens) if not c]
        any_censored = any(cens)

        # §10.2 -- "ECDF'lar TO'LIQ chizilib beriladi".
        ecdf = _ecdf(km)
        if ecdf is None:
            log.add("ecdf_not_computable", where,
                    "birorta event vaqti yo'q (hammasi censored) -- ECDF "
                    "HISOBLANMAYDI va chiqarilmaydi; silliqlangan egri "
                    "chiziq TO'QILMAYDI")
        else:
            block["ecdf"] = ecdf
        for qi, (q_name, q) in enumerate(QUANTILES):
            est = _f(S.km_quantile(km, q))
            if est is None:
                log.add("km_quantile_nan", f"{where}.{q_name}",
                        f"KM egri chizig'i {q_name} ga tushmadi -- §2.3 #8 "
                        "bo'yicha CENSORED BO'LMAGAN qism ustida BCa "
                        f"bootstrap (n_uncensored={len(uncensored)})")
                block[q_name] = _bootstrap_quantile(
                    uncensored, q, log, f"{where}.{q_name}", n_boot=n_boot,
                    seed_path=[2, mi, qi],
                    source="bca_bootstrap_uncensored",
                    note=("fallback from Kaplan-Meier: km_quantile returned "
                          "nan (documented limitation of stats.km_quantile); "
                          "computed on the uncensored portion only, per "
                          "§2.3 #8"))
                continue
            # Nuqtaviy baho KM'dan (censoring'ni to'g'ri ishlaydi); CI esa
            # faqat censored BO'LMAGAN qismdan olinadi, va bu AYTILADI.
            ci = _bootstrap_quantile(
                uncensored, q, log, f"{where}.{q_name}", n_boot=n_boot,
                seed_path=[2, mi, qi], source="kaplan_meier",
                note=("point estimate from Kaplan-Meier; BCa interval "
                      "computed on the uncensored portion only, because "
                      "stats.bootstrap_ci is invalid under censoring"
                      if any_censored else
                      "no censored observations: BCa interval uses the full "
                      "sample"),
                ci_basis=("uncensored_subsample" if any_censored
                          else "full_sample"))
            ci["estimate"] = est
            ci["source"] = "kaplan_meier"
            if any_censored:
                log.add("quantile_ci_uncensored_only", f"{where}.{q_name}",
                        f"{sum(1 for c in cens if c)} censored kuzatuv bor: "
                        "nuqtaviy baho KM'dan, CI esa FAQAT censored "
                        "bo'lmagan qismdan -- CI shu sababli ANIQ EMAS")
            block[q_name] = ci
        out[name] = block
    return out


# --- §8.2 probe narxi ------------------------------------------------------

# §8.2 -- prober narxi budjeti: bir yadroning 1% i. Bu qiymat
# `prober.PROBE_COST_BUDGET_PERCENT` da ham bor va IKKI JOYDA BIR XIL
# bo'lishi SHART.
#
# NEGA TAKRORLANADI, import qilinmaydi: qoida 1 bo'yicha `analyze.py`
# o'lchov modullarini (`prober`, `cgroup`, `psi_sampler`, `units`) import
# QILMAYDI -- offline analizning `/proc` o'qiydigan moduldan bog'liqligi
# bo'lmasligi kerak.
# NEGA IZOH YETARLI EMAS: ikki joyda muzlatilgan qiymat bir joyda
# o'zgarsa, chiqishdagi budjet jimgina noto'g'ri bo'lardi. Shuning uchun
# `tests/unit/test_analyze.py` da regressiya QULFI bor: u `prober.py` ni
# MATN sifatida o'qib qiymatni taqqoslaydi (import qilmaydi).
PROBE_COST_BUDGET_PERCENT = 1.0


def probe_cost_section(trials: Sequence[dict[str, Any]],
                       log: WarningLog,
                       prober_stops: Sequence[dict[str, Any]] | None = None
                       ) -> dict[str, Any] | None:
    """§8.2 -- prober narxi, yadro foizida, arm bo'yicha, PER TRIAL.

    §8.2 prober narxini HAR TRIAL uchun o'lchashni va ARM'LAR BO'YICHA BIR
    XIL ushlashni talab qiladi: aks holda "C tezroq" degan natija prober
    narxining farqi bo'lib chiqishi mumkin, va bu H2 ni o'ldiradigan
    e'tiroz.

    IKKI MANBA, shu tartibda:
      1. `prober_stops` (`--events`) -- ASOSIY. `driver-contract/v1.1`
         §4.5(a): driver HAR TRIAL uchun bitta prober jarayoni ishga
         tushiradi, demak `prober_stop` har trial uchun bir marta chiqadi
         va envelope'ida shu trial'ning `trial_id` si bor; payload'ining
         `cost` qismi `prober.cost_report()` (`core_percent`,
         `budget_percent`). Arm'ga bog'lanish `trials.jsonl` orqali.
      2. `trial_metrics["probe_cost"]` -- agar `reduce.py` kelajakda narxni
         o'zi chiqarsa. Hozir CHIQARMAYDI (`prober_stop` turi u yerda yo'q).

    Ikkisi ham bo'lmasa `None` qaytariladi va sabab `warnings` ga tushadi.
    NARX TO'QILMAYDI -- o'lchanmagan narxni nol yoki budjet qiymati deb
    berish §8.2 ni tekshirilgandek ko'rsatardi.
    """
    # trial_id -> core_percent. `prober_stop` ASOSIY manba.
    cost_by_tid: dict[Any, float | None] = {}
    source: str | None = None
    budget: float = PROBE_COST_BUDGET_PERCENT

    if prober_stops is not None and len(prober_stops) == 0:
        # Bayroq BERILGAN, lekin faylda `prober_stop` YO'Q -- bu `None`
        # (bayroq berilmagan) dan BOSHQA holat va o'z kodiga ega: ehtimol
        # noto'g'ri fayl ko'rsatilgan, yoki driver `--report-cost` siz
        # ishlagan.
        log.add("probe_cost_events_empty", "probe_cost",
                f"`--events` berilgan, lekin faylda birorta "
                f"`{RT_PROBER_STOP}` record topilmadi. §8.2 narxi "
                "HISOBLANMAYDI va bo'lim chiqarilmaydi -- narx TO'QILMAYDI. "
                "Tekshiring: fayl yo'li to'g'rimi, va driver prober'ni "
                "`--report-cost` bilan ishga tushirdimi")

    if prober_stops:
        source = f"events.jsonl {RT_PROBER_STOP}.cost (--events)"
        dup = 0
        no_tid = 0
        budgets: set[float] = set()
        for rec in prober_stops:
            tid = rec.get("trial_id")
            if tid is None:
                no_tid += 1
                continue
            cost = rec.get("cost")
            if not isinstance(cost, dict):
                cost = {}
            if tid in cost_by_tid:
                dup += 1
            cost_by_tid[tid] = _f(cost.get("core_percent"))
            b = _f(cost.get("budget_percent"))
            if b is not None:
                budgets.add(b)
        if no_tid:
            log.add("probe_cost_no_trial_id", "probe_cost",
                    f"{no_tid} `{RT_PROBER_STOP}` record'ida `trial_id` yo'q "
                    "-- trial'ga va arm'ga bog'lanmaydi, hisobga olinmaydi "
                    "(`driver-contract/v1.1` §4.5(a): driver har trial uchun "
                    "bitta prober ishga tushiradi, demak `trial_id` BO'LISHI "
                    "SHART)")
        if dup:
            log.add("probe_cost_duplicate_trial_id", "probe_cost",
                    f"{dup} `{RT_PROBER_STOP}` record'i allaqachon "
                    "ko'rilgan `trial_id` ni takrorladi -- OXIRGISI "
                    "olinadi; §4.5(a) har trial uchun BITTA prober "
                    "jarayonini talab qiladi")
        # Manbadagi budjet muzlatilgan qiymatdan farq qilsa -- jimgina
        # qolmaydi: bu §8.2 ning chegarasi o'zgargani demakdir.
        for b in sorted(budgets):
            if abs(b - PROBE_COST_BUDGET_PERCENT) > 1e-9:
                log.add("probe_cost_budget_mismatch", "probe_cost.budget_percent",
                        f"manbadagi `budget_percent` = {b}, bu modulda "
                        f"muzlatilgani = {PROBE_COST_BUDGET_PERCENT} -- "
                        "MANBADAGISI beriladi, chunki o'lchov shunga "
                        "nisbatan qilingan")
        if len(budgets) == 1:
            budget = budgets.pop()
        elif len(budgets) > 1:
            log.add("probe_cost_budget_inconsistent",
                    "probe_cost.budget_percent",
                    f"manbada bir nechta `budget_percent` qiymati: "
                    f"{sorted(budgets)} -- bu modulda muzlatilgani "
                    "beriladi")

    # Ikkinchi manba: `reduce.py` kelajakda narxni chiqarsa.
    inline = 0
    for r in trials:
        pc = r.get("probe_cost")
        if isinstance(pc, dict) and r.get("trial_id") not in cost_by_tid:
            cost_by_tid[r.get("trial_id")] = _f(pc.get("core_percent"))
            inline += 1
    if inline:
        source = (f"{source} + trial_metrics.probe_cost" if source
                  else "trial_metrics.probe_cost")

    if not cost_by_tid:
        log.add("probe_cost_absent", "probe_cost",
                "§8.2 narxi uchun manba yo'q. `prober.py` narxni "
                f"`cost_report()` da hisoblaydi va `{RT_PROBER_STOP}` ga "
                "yozadi (`driver-contract/v1.1` §4.5(a): har TRIAL uchun "
                "bitta prober jarayoni, demak per-trial o'lchov manbada "
                "MAVJUD), lekin `reduce.py` bu record turini O'QIMAYDI va "
                "narxni `trial_metrics` ga CHIQARMAYDI. `--events` bilan "
                "xom `events.jsonl` ni bering. Bo'lim CHIQARILMAYDI -- narx "
                "TO'QILMAYDI")
        return None

    by_arm: dict[str, dict[str, Any]] = {}
    n_missing = 0
    for r in trials:
        arm = str(r.get("arm"))
        tid = r.get("trial_id")
        if tid in cost_by_tid:
            val = cost_by_tid[tid]
        else:
            val = None
            n_missing += 1
        by_arm.setdefault(arm, {"core_percent": []})["core_percent"].append(val)
    if n_missing:
        log.add("probe_cost_partial", "probe_cost",
                f"{n_missing}/{len(trials)} trial uchun narx o'lchovi yo'q "
                "-- ro'yxatda `null` bo'lib qoladi, taxmin qilinmaydi")
    n_orphan = len(set(cost_by_tid) - {r.get("trial_id") for r in trials})
    if n_orphan:
        log.add("probe_cost_orphan", "probe_cost",
                f"{n_orphan} narx o'lchovining `trial_id` si trials "
                "kirishida topilmadi -- arm'ga bog'lanmaydi, jadvalga "
                "kirmaydi")
    return {"budget_percent": budget, "by_arm": by_arm, "source": source}


# --- §4 sensitivity sweep --------------------------------------------------


def sensitivity_section(sweep_cells: Sequence[dict[str, Any]] | None,
                        trials: Sequence[dict[str, Any]],
                        log: WarningLog,
                        t_trial_us: int | None = None) -> dict[str, Any]:
    """§4 -- oldindan e'lon qilingan `W_stab` x `theta` grid'i.

    §2.3 #7: `W_stab > horizon` bo'lgan yacheyka `note` bilan BELGILANADI.
    Busiz sweep egri chizig'ining pasayishi FIZIK natija bo'lib ko'rinardi
    -- lekin u HORIZON ARTEFAKTI.

    `note` IKKI MUSTAQIL manbadan qo'yiladi va BIRI YETARLI:
      (a) STRUKTURAVIY -- `W_stab > t_trial_us` (shartnoma §5.4 horizon'i,
          `run_meta` dan KO'CHIRILGAN). Bu ma'lumotga BOG'LIQ EMAS, demak
          yacheykada birorta trial bo'lmasa ham belgilanadi;
      (b) KUZATILGAN -- `reduce.py` shu yacheykada `vr=None` va
          `vr_reason="window_truncated"` qaytardi.
    `t_trial_us` berilmasa (a) ishlamaydi va sabab `warnings` da bo'ladi --
    horizon TAXMIN QILINMAYDI.

    §10.4: sweep EXPLORATORY -- u Holm oilasiga KIRMAYDI (`multiplicity`).
    """
    grid: list[dict[str, Any]] = []
    declared = {"w_stab": [float(w) for w in W_STAB_SWEEP_S],
                "theta": [float(t) for t in THETA_SWEEP]}
    used_all: list[dict[str, Any]] = []

    if t_trial_us is None:
        log.add("sweep_horizon_unknown", "sensitivity",
                "`t_trial_us` yo'q -- `W_stab > horizon` ni STRUKTURAVIY "
                "tekshirish mumkin emas; `note` faqat `reduce.py` ning "
                "`window_truncated` natijasidan qo'yiladi (§2.3 #7)")

    if not sweep_cells:
        log.add("sweep_absent", "sensitivity",
                "sweep kirishi berilmagan (`--sweep`) -- §4 grid'i "
                "HISOBLANMAYDI, taxmin qilinmaydi")
        return {**declared, "grid": [], "recovered_within_horizon": "0/0"}

    if not sweep_is_complete(sweep_cells):
        log.add("sweep_incomplete", "sensitivity",
                "kirish sweep'i oldindan e'lon qilingan to'liq grid'ni "
                f"({len(W_STAB_SWEEP_S)} x {len(THETA_SWEEP)}) qoplamaydi")

    by_id = {r.get("trial_id"): r for r in trials}
    buckets: dict[tuple[float, float], list[dict[str, Any]]] = {}
    orphan = 0
    for c in sweep_cells:
        tid = c.get("trial_id")
        if tid not in by_id:
            orphan += 1
            continue
        # §16.2(B): to'plam `(disposition, disposition_source)` JUFTI bilan
        # aniqlanadi. Sweep yacheykasi `disposition_source` ni O'ZI
        # yozmaydi, shuning uchun u SHU trial'ning record'idan olinadi --
        # sweep bir xil xom trace'ning qayta hisobi, demak manba bir xil.
        # NEGA `reduce.enters_primary_denominator`: qoida BITTA joyda
        # (`reduce.PRIMARY_DENOMINATOR_SOURCES`) yashaydi va fail-closed --
        # yangi `disposition_source` qiymati (§17: `window_past_pressure`,
        # `window_past_horizon`) avtomatik ravishda maxrajga TUSHMAYDI.
        # Deprecated `PRIMARY_DISPOSITIONS` konstantasi §16.4 da "to'g'ri
        # savol, NOTO'G'RI javob" deb hukm qilingan va BU MODULDA
        # ishlatilmaydi.
        if not enters_primary_denominator(c.get("disposition"),
                                          by_id[tid].get("disposition_source")):
            continue
        key = (round(float(c["w_stab_s"]), 6), round(float(c["theta"]), 6))
        buckets.setdefault(key, []).append(c)
    if orphan:
        log.add("sweep_orphan_cells", "sensitivity",
                f"{orphan} sweep yacheykasining `trial_id` si trials "
                "kirishida topilmadi -- pressure darajasi bilan "
                "bog'lanmaydi, jadvalga kirmaydi")

    for w_s in declared["w_stab"]:
        for th in declared["theta"]:
            cells = buckets.get((round(w_s, 6), round(th, 6)), [])
            notes: list[str] = []
            # (a) STRUKTURAVIY -- ma'lumotga bog'liq emas (§2.3 #7).
            if t_trial_us is not None and w_s * 1_000_000.0 > float(t_trial_us):
                notes.append(
                    f"W_stab > T_trial: W_stab = {w_s} s exceeds the trial "
                    f"horizon T_trial = {t_trial_us} us, so the stabilisation "
                    "window cannot be fully observed; reduce.py returns "
                    "vr=None (window_truncated) and a fall in P(VR) here "
                    "would be a horizon artefact, not a physical result")
            if not cells:
                notes.append("no sweep cells for this (W_stab, theta) in the "
                             "input")
            n_trunc = sum(1 for c in cells
                          if c.get("vr") is None
                          and c.get("vr_reason") == "window_truncated")
            if n_trunc:
                # (b) KUZATILGAN -- `reduce.py` ning o'z natijasi.
                notes.append(
                    f"window_truncated for {n_trunc}/{len(cells)} trial(s): "
                    "reduce.py returned vr=None, so these are excluded from "
                    "the denominator (never counted as a failed VR)")
            n_other_none = sum(1 for c in cells
                               if c.get("vr") is None
                               and c.get("vr_reason") != "window_truncated")
            if n_other_none:
                notes.append(
                    f"vr undetermined for {n_other_none} further trial(s) for "
                    "reasons other than window truncation (e.g. r_ref "
                    "unavailable); also excluded from the denominator")
            p_vr: dict[str, Any] = {}
            for lvl in PRESSURE_LEVELS:
                rows = [c for c in cells
                        if by_id[c["trial_id"]].get("pressure_band") == lvl]
                measured = [c for c in rows if c.get("vr") is not None]
                k = sum(1 for c in measured if c["vr"] is True)
                n = len(measured)
                p_vr[lvl] = {"k": k, "n": n,
                             "p_hat": (k / n) if n else None,
                             "n_undetermined": len(rows) - n}
            used_all.extend(cells)
            grid.append({"w_stab": w_s, "theta": th, "p_vr_by_level": p_vr,
                         "note": " | ".join(notes) if notes else None})

    return {**declared, "grid": grid,
            "recovered_within_horizon": _k_of_n(used_all)}


# --- §10.4 multiplicity ----------------------------------------------------


def multiplicity_section(primary: dict[str, Any],
                         log: WarningLog) -> dict[str, Any]:
    """§10.4 -- Holm-Bonferroni pre-registered BIRLAMCHI testlar oilasida.

    P1 da BITTA fault class (`clean_crash`) bor (§9.3), demak BITTA birlamchi
    test, demak Holm tuzatishi p-value'ni O'ZGARTIRMAYDI. Bu baribir
    hisoblanadi va yoziladi: oila §10.4 da MUZLATILGAN va keyinchalik
    "bitta test edi, tuzatish kerak emas" deb POST-HOC asoslanmasligi kerak.

    `uncorrected` -- §10.4 "scope/Delta sweep'lari EXPLORATORY deb
    belgilanadi". Pre-registered ikkilamchi natijalar (RMST, log-rank) ham
    shu ro'yxatda, lekin `label` bilan FARQLANADI: ular exploratory emas,
    lekin Holm oilasiga ham kirmaydi.
    """
    p = primary.get("p_value")
    family: list[dict[str, Any]] = [{
        "name": f"primary: {PRIMARY_ENDPOINT} ({PRIMARY_FAULT_CLASS})",
        "test": PRIMARY_TEST,
        "fault_class": PRIMARY_FAULT_CLASS,
        "p_value": p,
        "preregistration_section": "10.1",
    }]
    if p is None:
        log.add("multiplicity_not_computable", "multiplicity",
                "birlamchi test p-value'si hisoblanmadi -- Holm tuzatishi "
                "BAJARILMAYDI")
        adjusted: list[float | None] = [None]
    else:
        adjusted = [_f(v) for v in S.holm_bonferroni([p], ALPHA).adjusted.tolist()]
    return {
        "method": MULTIPLICITY_METHOD,
        "family": family,
        "adjusted": adjusted,
        "uncorrected": [
            {"name": "sensitivity: W_stab x theta sweep",
             "label": "exploratory", "preregistration_section": "4"},
            {"name": "survival: log-rank between arms",
             "label": "prespecified_secondary",
             "preregistration_section": "10.2"},
            {"name": f"survival: RMST difference at tau = {TAU_RMST_US} us (8 s)",
             "label": "prespecified_secondary",
             "preregistration_section": "11"},
            {"name": "downtime: d_sd / d_probe / d_eff quantiles",
             "label": "prespecified_secondary",
             "preregistration_section": "10.2"},
        ],
    }


# --- §12 eksklyuziya -------------------------------------------------------


# §17.4(2) -- oyna hold'dan yoki horizon'dan chiqib ketgan trial'lar.
# `disposition` ikkalasida ham `censored`, va IKKALASI binar maxrajdan
# chiqariladi (natija KUZATILMAGAN, `false` emas), lekin §6.2 bo'yicha
# KM/log-rank ga censored davomiylik sifatida KIRADI.
#
# NEGA ALOHIDA RO'YXAT: §17.4(4) ularning darajasini `(arm x pressure)`
# yacheykasi bo'yicha ALOHIDA berishni talab qiladi, chunki "`P2`
# yacheykasida to'plangan yuqori daraja -- O'ZI NATIJA: u 'dizayn
# qiziqtirgan yacheykani o'lchay olmadi' degan ma'noni beradi".
WINDOW_FIT_SOURCES = ("window_past_pressure", "window_past_horizon")


def _detailed_reasons(rows: Sequence[dict[str, Any]]) -> dict[str, int]:
    """`disposition:disposition_source` bo'yicha sanoq.

    NEGA `disposition` YETARLI EMAS (§16.2(B)): §12 ning `censored` yorlig'i
    IKKI epistemologik jihatdan boshqa holatni birlashtiradi --
    `down_at_horizon` (xizmat qaytmadi: KUZATILGAN no'l-hodisa) va
    `probe_gap` (instrumentatsiya yo'qoldi: KUZATILMAGAN). §16.2(B) ularni
    binar maxrajda boshqacha ishlaydi, demak eksklyuziya hisoboti ham
    ularni AJRATISHI kerak -- aks holda daraja takrorlanuvchi bo'lmaydi.
    """
    out: dict[str, int] = {}
    for r in rows:
        d = str(r.get("disposition"))
        src = r.get("disposition_source")
        key = f"{d}:{src}" if src else d
        out[key] = out.get(key, 0) + 1
    return out


def _window_fit_by_cell(trials: Sequence[dict[str, Any]],
                        log: WarningLog) -> dict[str, Any]:
    """§17.4(4) -- `window_past_*` darajasi `(arm x pressure)` yacheykasi
    bo'yicha, §16.4 ning nomlash qoidasi bilan.

    §17.4(4): "`P2` yacheykasida to'plangan yuqori daraja -- O'ZI NATIJA:
    u 'dizayn qiziqtirgan yacheykani o'lchay olmadi' degan ma'noni
    beradi", va §12 ning "yuqori eksklyuziya darajasi yashirilmaydi"
    qoidasi ostida yashirilmaydi. Agregat daraja bu xabarni YO'Q QILADI:
    uchala darajada tekis tarqalgan 10% va faqat `P2` da to'plangan 30%
    bir xil agregat berishi mumkin, lekin ikkinchisi dizayn nuqsoni.
    """
    cells: dict[str, dict[str, Any]] = {}
    worst: tuple[float, str] | None = None
    for r in trials:
        arm = str(r.get("arm"))
        band = str(r.get("pressure_band"))
        key = f"{arm}:{band}"
        cell = cells.setdefault(key, {
            "arm": arm, "pressure_band": band, "n_total": 0,
            "n_window_past": 0, "rate": None,
            "by_source": {s: 0 for s in WINDOW_FIT_SOURCES},
        })
        cell["n_total"] += 1
        src = r.get("disposition_source")
        if src in WINDOW_FIT_SOURCES:
            cell["n_window_past"] += 1
            cell["by_source"][src] += 1
    for key, cell in cells.items():
        n = cell["n_total"]
        cell["rate"] = (cell["n_window_past"] / n) if n else None
        if cell["rate"]:
            if worst is None or cell["rate"] > worst[0]:
                worst = (cell["rate"], key)
    # TRANZITSIYA holati -- jim qolmaydi: §17 ning ikki qiymati hali
    # `reduce.DISPOSITION_SOURCES` ga qo'shilmagan bo'lsa,
    # `reduce.primary_denominator_verdict` ularni
    # `unknown_source(...)` deb nomlaydi. Natija BIR XIL (fail-closed,
    # maxrajdan chiqadi), lekin sabab satri boshqacha bo'ladi -- va
    # hisobot satrlari o'zgarsa buni bilish kerak.
    not_in_reducer = [s for s in WINDOW_FIT_SOURCES
                      if s not in DISPOSITION_SOURCES]
    if not_in_reducer and any(
            r.get("disposition_source") in not_in_reducer for r in trials):
        log.add("window_fit_source_not_in_reducer_enum",
                "exclusions.window_fit_by_cell",
                f"{not_in_reducer} hali `reduce.DISPOSITION_SOURCES` da "
                "yo'q, demak `reduce.primary_denominator_verdict` ularni "
                "`unknown_source(...)` deb nomlaydi. NATIJA BIR XIL "
                "(§17.4(3): maxrajdan fail-closed chiqadi, KM/log-rank ga "
                "kiradi), lekin sabab SATRI reducer §17 ni qo'shgandan "
                "keyin o'zgaradi")
    if worst is not None:
        log.add("window_fit_exclusions_present", "exclusions.window_fit_by_cell",
                "§17 ning oyna-sig'ish eksklyuziyasi mavjud: eng yuqori "
                f"daraja `{worst[1]}` yacheykasida ({worst[0]:.3f}). "
                "§17.4(4): `P2` da to'plangan yuqori daraja O'ZI NATIJA -- "
                "u dizayn qiziqtirgan yacheykani o'lchay olmaganini "
                "bildiradi, va yashirilmaydi")
    return {
        "analysis_set": "binary_p_vr_denominator_exclusions_window_fit",
        "description": ("rate of disposition_source in "
                        f"{list(WINDOW_FIT_SOURCES)} per (arm x pressure) "
                        "cell (PREREGISTRATION.md §17.4(4)); these are "
                        "excluded from the binary denominator because the "
                        "§4 window was not observed, and enter KM/log-rank "
                        "as censored durations (§6.2)"),
        "sources": list(WINDOW_FIT_SOURCES),
        "by_cell": dict(sorted(cells.items())),
    }


def _unknown_sources(trials: Sequence[dict[str, Any]],
                     log: WarningLog) -> dict[str, int]:
    """Reducer'ning enum'ida YO'Q `disposition_source` qiymatlari.

    NEGA HISOBOTGA: yangi qiymat (§17 ning ikkitasi kabi) bu modul
    bilmaganda ham `reduce.primary_denominator_verdict` uni FAIL-CLOSED
    chiqaradi -- bu to'g'ri, lekin JIM bo'lmasligi kerak. Aks holda
    "noma'lum sabab bilan chiqarilgan trial'lar" nomsiz bucket'da
    yo'qolardi, va §16.4 ga ko'ra nomsiz eksklyuziya natija sifatida
    berilmaydi.
    """
    known = set(DISPOSITION_SOURCES) | set(WINDOW_FIT_SOURCES)
    out: dict[str, int] = {}
    for r in trials:
        src = r.get("disposition_source")
        if src and src not in known:
            out[str(src)] = out.get(str(src), 0) + 1
    if out:
        log.add("disposition_source_unrecognised", "exclusions",
                f"`reduce.DISPOSITION_SOURCES` da yo'q manba qiymat(lar)i: "
                f"{dict(sorted(out.items()))}. `reduce."
                "primary_denominator_verdict` ularni FAIL-CLOSED chiqaradi "
                "(to'g'ri), lekin ular NOMLANADI -- nomsiz bucket'ga "
                "qo'yilmaydi")
    return dict(sorted(out.items()))


def exclusions_section(trials: Sequence[dict[str, Any]],
                       primary_trials: Sequence[dict[str, Any]],
                       survival_trials: Sequence[dict[str, Any]],
                       log: WarningLog,
                       reduction_summary: dict[str, Any] | None = None
                       ) -> dict[str, Any]:
    """§12 + §16.4 -- IKKI eksklyuziya darajasi, har biri TO'PLAMINI NOMLAB.

    §12: "`contaminated` va `aborted_guard` trial'lar birlamchi analizdan
    chiqariladi, LEKIN ularning ulushi natija sifatida beriladi. Yuqori
    eksklyuziya darajasi O'ZI natija -- yashirilmaydi."

    §16.4 ning MAJBURIY HISOBOT QOIDASI: "Har qanday ... `analysis.json` da
    berilgan eksklyuziya darajasi QAYSI to'plam ustida hisoblanganini
    NOMLASHI SHART -- binar `P(VR)` maxraji, yoki survival/`k/n` analiz
    to'plami. Nomlanmagan eksklyuziya darajasi TAKRORLANUVCHI EMAS va
    natija sifatida berilmaydi." Ikki to'plam ikki darajani beradi, demak
    bitta `rate` maydoni O'ZI yetarli emas.

    TO'PLAMLAR BU YERDA QAYTA HISOBLANMAYDI: ular `reduce.select_primary`
    va `reduce.select_survival` ning qarori va u YAKKA MANBA (§16.6). Bu
    funksiya faqat SANAYDI va NOMLAYDI.
    """
    total = len(trials)
    # NEGA `id()` va `trial_id` EMAS: selektorlar AYNAN shu dict
    # obyektlarini qaytaradi (oddiy list comprehension), demak `id()`
    # to'plam a'zoligini XATOSIZ beradi. `trial_id` bo'yicha solishtirish
    # takrorlangan yoki yo'q `trial_id` da jimgina xato berardi -- va
    # eksklyuziya darajasi NATIJA (§12), demak u taxminga tayanmaydi.
    primary_ids = {id(r) for r in primary_trials}
    survival_ids = {id(r) for r in survival_trials}
    ex_primary = [r for r in trials if id(r) not in primary_ids]
    ex_survival = [r for r in trials if id(r) not in survival_ids]

    # §16.4 -- reducer'ning raqami AVTORITET. `reduce_run` ikki darajani
    # O'ZI hisoblaydi; ikki mustaqil sanoq yo'li ikki xil raqam berishi
    # mumkin, va eksklyuziya darajasi NATIJA (§12).
    summary_rates: dict[str, float | None] = {}
    summary_blocks: dict[str, Any] = {}
    if reduction_summary is not None:
        summary_rates = {
            "binary_p_vr_denominator":
                _f(reduction_summary.get(
                    "exclusion_rate_binary_pvr_denominator")),
            "survival_analysis_set":
                _f(reduction_summary.get(
                    "exclusion_rate_survival_analysis_set")),
        }
        raw = reduction_summary.get("exclusions")
        if isinstance(raw, dict):
            summary_blocks = {
                "binary_p_vr_denominator": raw.get(SET_BINARY_DENOMINATOR),
                "survival_analysis_set": raw.get(SET_SURVIVAL),
            }
    else:
        log.add("reduction_summary_absent", "exclusions",
                "`--reduction-summary` berilmagan: §16.4 ning ikki "
                "eksklyuziya darajasi `reduce_run` ning "
                "`exclusion_rate_binary_pvr_denominator` / "
                "`exclusion_rate_survival_analysis_set` maydonlarida "
                "AVTORITET tarzda bor. Bu yerda ular `reduce.select_primary` "
                "/ `select_survival` qaytargan to'plamlar ustida QAYTA "
                "SANALDI -- tanlov qoidasi baribir reducer'ning, lekin "
                "sanoq yo'li IKKITA. Darajalar NATIJA (§12), demak "
                "reducer'ning raqamini bering")

    def block(name: str, desc: str, included: Sequence[dict[str, Any]],
              excluded: Sequence[dict[str, Any]]) -> dict[str, Any]:
        own = (len(excluded) / total) if total else None
        auth = summary_rates.get(name)
        if auth is not None and own is not None and abs(auth - own) > 1e-12:
            # Jimgina qolmaydi: ikki sanoq yo'li farq qilsa, kirish
            # fayllari BIR XIL reduksiyadan kelmagan bo'lishi mumkin.
            log.add("exclusion_rate_mismatch", f"exclusions.by_set.{name}",
                    f"reducer'ning darajasi {auth}, bu yerda sanalgani "
                    f"{own} -- MANBADAGISI (reducer) beriladi. Sabab "
                    "ehtimol kirish fayllari bir xil reduksiyadan emas")
        return {
            "set": name,
            "description": desc,
            # Reducer'ning raqami bo'lsa U beriladi; bo'lmasa o'z sanog'i.
            "rate": auth if auth is not None else own,
            "rate_source": ("reduction_summary" if auth is not None
                            else "recounted_in_analyze"),
            "rate_recounted_here": own,
            "n_total": total,
            "n_included": len(included),
            "n_excluded": len(excluded),
            "by_reason": _detailed_reasons(excluded),
            "reducer_block": summary_blocks.get(name),
        }

    # Eski (shartnoma §2.2) shakl: `by_reason` faqat `disposition` bo'yicha.
    by_reason: dict[str, int] = {}
    for r in ex_primary:
        # §16.2(B) -- sabab `reduce.primary_denominator_verdict` dan
        # keladi, bu yerda qayta hisoblanmaydi. `exclusion_reason`
        # field'i eski reduksiyada `disposition` bo'lishi mumkin.
        _inc, named = primary_denominator_verdict(
            r.get("disposition"), r.get("disposition_source"))
        reason = (str(named).split(":", 1)[0] if named
                  else str(r.get("disposition")))
        by_reason[reason] = by_reason.get(reason, 0) + 1

    return {
        # Shartnoma §2.2 `rate` kalitini talab qiladi; §16.4 esa nomlanmagan
        # darajani taqiqlaydi -- shuning uchun `rate_set` uni NOMLAYDI.
        "rate": (len(ex_primary) / total) if total else None,
        "rate_set": "binary_p_vr_denominator",
        "by_reason": by_reason,
        "n_total": total,
        "n_excluded": len(ex_primary),
        "n_primary": len(primary_trials),
        "by_set": {
            "binary_p_vr_denominator": block(
                "binary_p_vr_denominator",
                "denominator of the binary P(VR) endpoint (§10.1); "
                "membership decided by reduce.select_primary, which per "
                "§16.2(B) admits disposition_source == 'down_at_horizon' "
                "as an observed VR = false and excludes 'probe_gap' as "
                "unobserved",
                primary_trials, ex_primary),
            "survival_analysis_set": block(
                "survival_analysis_set",
                "analysis set for survival / loop-rate / recovered k-of-n "
                "tables (§6.2); membership decided by "
                "reduce.select_survival; censored durations are included, "
                "never dropped",
                survival_trials, ex_survival),
        },
        # §17.4(4) -- `(arm x pressure)` yacheykasi bo'yicha, agregat
        # DARAJA EMAS: `P2` da to'plangan yuqori daraja O'ZI natija.
        "window_fit_by_cell": _window_fit_by_cell(trials, log),
        # §16.2(B) / §17: noma'lum manba NOMLANADI, nomsiz bucket'ga
        # qo'yilmaydi.
        "unrecognised_disposition_sources": _unknown_sources(trials, log),
        # Reducer'ning `disposition:source` sanog'i (bor bo'lsa).
        "disposition_source_counts": (
            (reduction_summary or {}).get("disposition_source_counts")),
    }


# --- taqiqlangan statistika qulfi (§2.3 #1, #2) ----------------------------


def _assert_no_forbidden(obj: dict[str, Any]) -> None:
    """§2.3 #1 va #2 -- STRUKTURAVIY qulf, testga qo'shimcha.

    §10.2 `t-test` va `mean ± SD` ni TAQIQLAYDI, va
    `proportional_hazards_checked` false bo'lsa HR/Cox UMUMAN paydo
    bo'lmasligi kerak. Bu tekshiruv chiqish YOZILISHDAN OLDIN ishlaydi:
    taqiq muzlatilgan, demak uni buzish xato emas, SHARTNOMA BUZILISHI.
    """
    blob = json.dumps(obj, ensure_ascii=False, allow_nan=False).lower()
    hits = [t for t in FORBIDDEN_TOKENS if t in blob]
    if hits:
        raise AnalysisError(
            f"chiqishda TAQIQLANGAN statistika satri bor (§10.2, §2.3 #1): "
            f"{hits}")
    checked = bool(obj.get("survival", {}).get("proportional_hazards_checked"))
    if not checked:
        hz = [t for t in HAZARD_TOKENS if t in blob]
        if hz:
            raise AnalysisError(
                "proportional_hazards_checked=false, lekin chiqishda hazard "
                f"ratio / Cox izi bor (§2.3 #2, §10.2): {hz}")


# --- yig'ish ---------------------------------------------------------------


def build_analysis(trials: Sequence[dict[str, Any]],
                   run_meta: dict[str, Any],
                   sweep_cells: Sequence[dict[str, Any]] | None = None,
                   *,
                   episodes: Sequence[dict[str, Any]] | None = None,
                   prober_stops: Sequence[dict[str, Any]] | None = None,
                   reduction_summary: dict[str, Any] | None = None,
                   n_boot: int = N_BOOT,
                   generated_mono_us: int | None = None) -> dict[str, Any]:
    """`analysis.json` obyektini quradi -- §2.2 sxemasi AYNAN shu tartibda.

    `generated_mono_us=None` bo'lsa `schema.mono_us()` dan olinadi (§1 vaqt
    disiplinasi). Test uchun qiymat berish mumkin -- shunda chiqish TO'LIQ
    deterministik bo'ladi (qoida 2).
    """
    log = WarningLog()
    check_inputs(trials, log)

    primary_trials = select_primary(trials)
    survival_trials = select_survival(trials)
    if not primary_trials:
        log.add("no_primary_trials", "primary",
                "birorta `complete` trial yo'q -- birlamchi analiz "
                "HISOBLANMAYDI (§12)")
    if not survival_trials:
        log.add("no_survival_trials", "survival",
                "birorta `complete`/`censored` trial yo'q -- KM/log-rank/RMST "
                "HISOBLANMAYDI (§6.2)")

    sha = run_meta.get("preregistration_sha256")
    if not sha:
        log.add("preregistration_sha256_missing", "preregistration_sha256",
                "kirish `run_meta` da `preregistration_sha256` yo'q -- u "
                "KO'CHIRILADI, hech qachon qayta hisoblanmaydi (§1.1)")

    # Shartnoma §5.4 (`driver-contract/v1.1`): horizon driver tomonidan
    # HISOBLANADI (`t_pressure_off + w_stab_s + P`) va `run_meta` da keladi.
    # Bu yerda qayta hisoblanmaydi -- `recovered_within_horizon` ni o'qish
    # uchun o'quvchiga AYNAN shu raqam kerak.
    t_trial_us = run_meta.get("t_trial_us")
    if t_trial_us is None:
        log.add("t_trial_us_missing", "t_trial_us",
                "kirish `run_meta` da `t_trial_us` yo'q (shartnoma §5.4) -- "
                "`recovered_within_horizon` nisbati qaysi horizon'ga "
                "nisbatan ekani NOMA'LUM qoladi; TAXMIN QILINMAYDI")

    primary = primary_section(primary_trials, log)
    survival = survival_section(survival_trials, log, n_boot=n_boot)
    false_recovery = false_recovery_section(primary_trials, log, episodes)
    downtime = downtime_section(primary_trials, log, n_boot=n_boot)
    sensitivity = sensitivity_section(sweep_cells, trials, log,
                                      None if t_trial_us is None
                                      else int(t_trial_us))
    multiplicity = multiplicity_section(primary, log)
    exclusions = exclusions_section(trials, primary_trials, survival_trials,
                                    log, reduction_summary)

    # §16.8 / §17 -- BIRINCHI TRIALDAN OLDINGI BLOKER: binar maxrajda
    # `vr is None` bo'lgan trial bo'lmasligi kerak. Maxrajga kirish
    # "natija KUZATILDI" degani; `vr=None` esa "o'lchanmadi". Ikkisi bir
    # vaqtda to'g'ri bo'lishi mumkin emas.
    vr_undet_denom = None
    if reduction_summary is not None:
        vr_undet_denom = reduction_summary.get(
            "vr_undetermined_in_binary_denominator")
    own_undet = sum(1 for r in primary_trials if r.get("vr") is None)
    if vr_undet_denom is None:
        vr_undet_denom = own_undet
    if vr_undet_denom:
        log.add("vr_undetermined_in_binary_denominator", "n_trials",
                f"{vr_undet_denom} trial binar `P(VR)` maxrajida, LEKIN "
                "`vr` aniqlanmagan (None). Maxrajga kirish 'natija "
                "KUZATILDI' degani, `vr=None` esa 'o'lchanmadi' -- ikkisi "
                "bir vaqtda to'g'ri BO'LA OLMAYDI. §16.8/§17 bu holatni "
                "BIRINCHI TRIALDAN OLDIN hal qilinishi shart bo'lgan "
                "BLOKER deb belgilaydi. Bu trial'lar yacheyka "
                "denominatoriga KIRMAYDI (taxmin qilinmaydi), lekin "
                "nomuvofiqlik O'ZI qayd etiladi")
    probe_cost = probe_cost_section(trials, log, prober_stops)

    obj: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "analysis_version": ANALYSIS_VERSION,
        # §1.1 / qoida 7 -- KIRISH `run_meta` dan ko'chiriladi.
        "preregistration_sha256": sha,
        "preregistration_version": run_meta.get("preregistration_version"),
        "generated_mono_us": (int(generated_mono_us)
                              if generated_mono_us is not None else mono_us()),
        # §1 -- `analysis.json` dagi BARCHA vaqt qiymati mikrosekundda.
        "time_unit": TIME_UNIT,
        "run_id": run_meta.get("run_id"),
        "session_id": run_meta.get("session_id"),
        # Shartnoma §5.4 -- horizon KO'CHIRILADI, qayta hisoblanmaydi.
        "t_trial_us": (int(t_trial_us) if t_trial_us is not None else None),
        "t_trial_formula": run_meta.get("t_trial_formula"),
        "n_trials": {"total": len(trials),
                     "by_disposition": disposition_counts(trials),
                     # §16.8/§17 bloker -- qiymat chiqishda KO'RINADI,
                     # faqat `warnings` da emas.
                     "vr_undetermined_in_binary_denominator":
                         int(vr_undet_denom) if vr_undet_denom is not None
                         else None},
        "primary": primary,
        "survival": survival,
        "false_recovery": false_recovery,
        "downtime": downtime,
        "sensitivity": sensitivity,
        "multiplicity": multiplicity,
        "exclusions": exclusions,
        "warnings": log.as_list(),
    }
    # §8.2 -- manba zanjiri uzilgan bo'lsa bo'lim UMUMAN chiqmaydi, shunda
    # `figures.py` yo'qligini ANIQLAY OLADI va placeholder chizadi.
    if probe_cost is not None:
        obj["probe_cost"] = probe_cost
    _assert_no_forbidden(obj)
    return obj


# --- yozish ----------------------------------------------------------------


def _assert_not_input(out_path: str, inputs: Sequence[str]) -> None:
    """Kirish fayli USTIGA yozilmaydi (`reduce._assert_not_raw` bilan bir xil
    qoida: derived ma'lumot qayta yaratiladi, kirish -- yo'q)."""
    op = os.path.realpath(out_path)
    for i in inputs:
        if i and os.path.realpath(i) == op:
            raise AnalysisError(
                f"chiqish yo'li kirish fayli bilan bir xil: {out_path!r}")


def write_analysis(obj: dict[str, Any], path: str) -> str:
    """`analysis.json` ni yozadi.

    `allow_nan=False` -- NaN/inf JSON'da YAROQSIZ va soxta aniqlik berardi
    (qoida 6). Qiymat o'lchanmagan bo'lsa `null`, NaN emas.
    """
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    blob = json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(blob + "\n")
    return path


# --- CLI -------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="REVIX offline analiz "
                    "(04-driver-va-analiz-shartnomasi.md §2, "
                    "PREREGISTRATION.md §10)")
    ap.add_argument("--trials", required=True,
                    help="reduce.py ning trials.jsonl (trial_metrics)")
    ap.add_argument("--run-meta", required=True, help="run_meta.json")
    ap.add_argument("--out", required=True, help="analysis.json")
    ap.add_argument("--sweep", default=None,
                    help="reduce.py ning sweep.jsonl (ixtiyoriy, §4 grid'i)")
    ap.add_argument("--episodes", default=None,
                    help="reduce.py ning episodes.jsonl (ixtiyoriy): §5 ning "
                         "per-action/per-epizod FR-A si shu faylda")
    ap.add_argument("--events", default=None,
                    help="xom events.jsonl (ixtiyoriy): §8.2 prober narxi "
                         "`prober_stop.cost` dan olinadi")
    ap.add_argument("--reduction-summary", default=None,
                    help="reduce.py ning reduction_summary.jsonl "
                         "(ixtiyoriy): §16.4 ning ikki eksklyuziya "
                         "darajasi AVTORITET tarzda shu yerda")
    ap.add_argument("--json", action="store_true",
                    help="analysis.json ni stdout'ga ham yozadi")
    args = ap.parse_args(argv)

    try:
        _assert_not_input(args.out, [args.trials, args.run_meta, args.sweep,
                                     args.episodes, args.events,
                                     args.reduction_summary])
        trials = load_trials(args.trials)
        meta = load_run_meta(args.run_meta)
        sweep = load_sweep(args.sweep) if args.sweep else None
        episodes = load_episodes(args.episodes) if args.episodes else None
        stops = load_events(args.events) if args.events else None
        rsum = (load_reduction_summary(args.reduction_summary)
                if args.reduction_summary else None)
        obj = build_analysis(trials, meta, sweep, episodes=episodes,
                             prober_stops=stops, reduction_summary=rsum)
        write_analysis(obj, args.out)
    except AnalysisError as exc:
        sys.stderr.write(f"analiz xatosi: {exc}\n")
        return 2

    if args.json:
        json.dump(obj, sys.stdout, indent=2, ensure_ascii=False,
                  allow_nan=False)
        sys.stdout.write("\n")
    else:
        p = obj["primary"]
        print(f"trial: {obj['n_trials']['total']}  "
              f"birlamchi: {obj['exclusions']['n_primary']}  "
              f"eksklyuziya: {obj['exclusions']['rate']}")
        print(f"disposition: {obj['n_trials']['by_disposition']}")
        print(f"{p['test']}: statistic={p['statistic']} p={p['p_value']} "
              f"direction={p['direction']}")
        print(f"risk difference (P0-P2): {p['risk_difference']['estimate']} "
              f"[{p['risk_difference']['ci_lower']}, "
              f"{p['risk_difference']['ci_upper']}] (newcombe)")
        print(f"falsified ({p['falsification_rule']}): {p['falsified']}")
        print(f"T_trial ichida recovered: {p['recovered_within_horizon']}")
        print(f"warnings: {len(obj['warnings'])}")
        print(f"  out: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
