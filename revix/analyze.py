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
  8. **EKSKLYUZIYA DARAJASI NATIJA** (§12). `exclusions` bloki sababga
     ko'ra ajratilib beriladi; jimgina eksklyuziya YO'Q.

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
    foizida, va arm'lar bo'yicha BIR XIL ushlashni talab qiladi. Manba
    zanjiri hozir UZILGAN (pastdagi PROBE_COST CHEKLOVI), shuning uchun
    bo'lim CHIQARILMAYDI va sabab `warnings` da beriladi.
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

FR-A CHEKLOVI (CHEKLOV, natija emas): §5 FR-A ni HAR ACTION va HAR EPIZOD
uchun talab qiladi, lekin per-action/per-epizod FR-A `reduce.py` ning
`episodes.jsonl` ida yashaydi -- §2.1 esa kirish sifatida faqat
`trial_metrics` ni beradi. Shuning uchun bu modul faqat AYNAN YECHILADIGAN
quyi to'plamdan hisoblaydi: `n_episodes == 1` bo'lgan trial'da trial
darajasidagi FR-A epizod darajasidagi FR-A ga AYNAN TENG (`_kleene_any`
bitta element ustida -- `reduce.build_episodes`), va `n_actions == 1` ham
bo'lsa action darajasiga ham teng. Yechilmagan trial'lar `warnings` da
SANAB BERILADI va denominatorga kirmaydi. Taxmin qilinmaydi.

PROBE_COST CHEKLOVI (FAKT, tekshirilgan): §8.2 prober narxini har trial
uchun talab qiladi, `revix/prober.py` esa uni `cost_report()` da
(`core_percent`, `budget_percent = 1.0`) hisoblaydi va `prober_stop`
record'iga yozadi. LEKIN zanjir IKKI joyda uzilgan:
  (a) `revix/reduce.py` `prober_stop` ni UMUMAN o'qimaydi (unda shunday
      record turi ham, `cost` so'zi ham yo'q) va `trial_metrics` ga narx
      field'i CHIQARMAYDI;
  (b) `prober.cost_report()` o'z docstring'ida "har RUN'da o'lchanadi"
      deydi va `prober_stop` run oxirida BIR MARTA chiqadi -- demak
      per-trial ro'yxat manbada ham mavjud emas.
Shuning uchun `probe_cost` bo'limi TO'QILMAYDI. `_probe_cost_section()`
`trial_metrics` da `probe_cost` field'ini IZLAYDI va topilsa bo'limni
chiqaradi; topilmasa bo'lim yo'q va sabab `warnings` da. Field nomi hali
MUZLATILMAGAN -- bu `agent/contract` va `agent/driver` uchun ochiq savol.

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
    DRT_SWEEP,
    DRT_TRIAL,
    PRIMARY_DISPOSITIONS,
    THETA_SWEEP,
    W_STAB_SWEEP_S,
    disposition_counts,
    select_primary,
    select_survival,
    sweep_is_complete,
)
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
    """
    cells: list[dict[str, Any]] = []
    counts: dict[str, tuple[int, int]] = {}
    used: list[dict[str, Any]] = []

    for lvl in PRESSURE_LEVELS:
        rows = [r for r in primary_trials if r.get("pressure_band") == lvl]
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
            cells.append({"level": lvl, "k": 0, "n": 0, "p_hat": None,
                          "ci_lower": None, "ci_upper": None,
                          "ci_method": "clopper_pearson"})
            continue
        ci = S.clopper_pearson(k, n, ALPHA)
        # `p_hat` AYNAN `k/n` -- shu nisbatdan boshqa hech narsa emas.
        # NEGA to'g'ridan-to'g'ri: `p_hat != k/n` bo'lgan yacheyka figurada
        # BELGILANADI (tuzatilmaydi), shuning uchun u strukturaviy jihatdan
        # imkonsiz bo'lishi kerak, estimator'ga ishonishga emas.
        cells.append({"level": lvl, "k": k, "n": n,
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


def survival_section(survival_trials: Sequence[dict[str, Any]],
                     log: WarningLog, *, n_boot: int) -> dict[str, Any]:
    """§10.2 -- KM time-to-VR har arm uchun, log-rank, RMST (`tau = 8 s`).

    §2.3 #3 -- CENSORED TRIAL'LAR KIRADI. Kirish to'plami
    `reduce.select_survival` bilan tanlanadi (`complete` + `censored`), chunki
    §6.2 ularni tashlashni ATAYLAB taqiqlaydi: tashlash tez ishdan chiqadigan
    arm'ni chiroyli ko'rsatadi.

    §2.3 #2 -- `proportional_hazards_checked` HAR DOIM `false`: `stats.py` da
    Schoenfeld residual testi YO'Q (ataylab -- modul docstring'i qoida 3),
    demak HR/Cox CHIQARILMAYDI. §10.2: "Schoenfeld residual'lari
    tekshirilmasa, HR berilmaydi."

    GURUHLASH -- OCHIQ QAROR: §2.2 `by_arm` deydi va §10.2 "har arm uchun"
    deydi, shuning uchun guruhlash `arm` bo'yicha. §11 ning fail-slow
    bandida esa RMST farqi `P0` va `P2` ORASIDA so'raladi -- unga §2.2 da
    JOY YO'Q. Bu modul sxemani harfiga ko'ra bajaradi va yetishmayotgan
    slotni `warnings` da NOMLAYDI; ziddiyat bu yerda hal qilinmaydi.
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    for r in survival_trials:
        arm = r.get("arm")
        groups.setdefault(str(arm), []).append(r)

    by_arm: dict[str, dict[str, Any]] = {}
    arrays: dict[str, tuple[list[float], list[int]]] = {}
    for gi, arm in enumerate(sorted(groups)):
        where = f"survival.km.by_arm.{arm}"
        times, events, _sk = _surv_arrays(groups[arm], log, where)
        if not times:
            log.add("km_no_data", where,
                    "o'lchangan time-to-VR yo'q -- KM egri chizig'i "
                    "hisoblanmaydi")
            by_arm[arm] = {"times": [], "survival": [], "at_risk": [],
                           "greenwood_var": [], "n_events": [],
                           "n_total": 0, "n_censored": 0, "quantiles": {}}
            continue
        arrays[arm] = (times, events)
        km = S.kaplan_meier(times, events)
        by_arm[arm] = {
            "times": _flist(km.times),
            "survival": _flist(km.survival),
            "at_risk": _ilist(km.at_risk),
            "greenwood_var": _flist(km.variance),
            "n_events": _ilist(km.n_events),
            "n_total": int(km.n_total),
            "n_censored": int(km.n_censored),
            "quantiles": _km_quantiles(times, events, log, where,
                                       n_boot=n_boot, seed_path=[1, gi]),
        }

    # --- log-rank (§10.2) ---
    logrank: dict[str, Any] = {"chi2": None, "p_value": None,
                               "observed": {}, "expected": {}}
    arms = sorted(arrays)
    if len(arms) == 2:
        a, b = arms
        lr = _capture(lambda: S.logrank(arrays[a][0], arrays[a][1],
                                        arrays[b][0], arrays[b][1]),
                      log, "survival.logrank")
        logrank = {
            "chi2": _f(lr.statistic), "p_value": _f(lr.p_value),
            "observed": {a: _f(lr.observed_a), b: _f(lr.observed_b)},
            "expected": {a: _f(lr.expected_a), b: _f(lr.expected_b)},
        }
        if logrank["p_value"] is None:
            log.add("logrank_degenerate", "survival.logrank",
                    "log-rank statistikasi aniqlanmagan (varians nol yoki "
                    "event yo'q)")
    else:
        log.add("logrank_not_computable", "survival.logrank",
                f"log-rank AYNAN ikki guruh talab qiladi, topilgani: {arms}")

    # --- RMST (§10.2 effect measure, §11 tau = 8 s) ---
    rmst_by_arm: dict[str, dict[str, Any]] = {}
    for arm in arms:
        t, e = arrays[arm]
        try:
            res = _capture(lambda: S.rmst(t, e, TAU_RMST_US),
                           log, f"survival.rmst.by_arm.{arm}")
        except ValueError as exc:
            log.add("rmst_not_computable", f"survival.rmst.by_arm.{arm}",
                    str(exc))
            rmst_by_arm[arm] = {"estimate": None, "se": None}
            continue
        rmst_by_arm[arm] = {"estimate": _f(res.rmst), "se": _f(res.std_err)}

    diff: dict[str, Any] = {"estimate": None, "se": None, "ci_lower": None,
                            "ci_upper": None, "contrast": None}
    if len(arms) == 2:
        a, b = arms
        try:
            rd = _capture(lambda: S.rmst_difference(arrays[a], arrays[b],
                                                    TAU_RMST_US, ALPHA),
                          log, "survival.rmst.difference")
        except ValueError as exc:
            log.add("rmst_difference_not_computable", "survival.rmst.difference",
                    str(exc))
        else:
            diff = {"estimate": _f(rd.difference), "se": _f(rd.std_err),
                    "ci_lower": _f(rd.lower), "ci_upper": _f(rd.upper),
                    "contrast": f"{a} - {b}"}
            if diff["se"] in (None, 0.0):
                log.add("rmst_difference_degenerate",
                        "survival.rmst.difference",
                        "RMST farqining standard error'i nol yoki aniqlanmagan "
                        "-- CI MA'NOSIZ, talqin qilinmaydi")
    else:
        log.add("rmst_difference_not_computable", "survival.rmst.difference",
                f"RMST farqi AYNAN ikki guruh talab qiladi, topilgani: {arms}")

    # §11 ning pressure kontrasti uchun §2.2 da slot YO'Q -- hal qilinmaydi.
    log.add("schema_gap_rmst_pressure_contrast", "survival.rmst",
            "PREREGISTRATION.md §11 fail-slow bandi `P0` va `P2` orasidagi "
            "time-to-VR RMST farqini (tau = 8 s) talab qiladi, lekin "
            "04-driver-va-analiz-shartnomasi.md §2.2 sxemasida u uchun slot "
            "yo'q (`rmst.by_arm` arm bo'yicha). Bu yerda HISOBLANMAYDI va "
            "TAXMIN QILINMAYDI -- shartnoma amendment savoli")

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
    return {
        "km": {"by_arm": by_arm},
        "logrank": logrank,
        "rmst": {"tau": TAU_RMST_US, "by_arm": rmst_by_arm,
                 "difference": diff},
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


def false_recovery_section(primary_trials: Sequence[dict[str, Any]],
                           log: WarningLog) -> dict[str, Any]:
    """§5 -- FR-A (BIRLAMCHI, oracle-free) va FR-B (P1 da BERILMAYDI).

    `fr_b.computed = false`, `reason = "no calibration matrix (P1)"` --
    §2.2 AYNAN shu satrni talab qiladi, va §5 sababini beradi: `Repairs()`
    kalibratsiya eksperimentidan keladi, u esa P1 da hali yo'q. Nol qaytarish
    "false recovery yo'q" degan O'LCHANMAGAN da'vo bo'lardi.

    `per_action` / `per_episode` uchun modul docstring'idagi FR-A CHEKLOVI'ga
    qarang: faqat AYNAN YECHILADIGAN quyi to'plam ishlatiladi.
    """
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

# §8.2 -- prober narxi budjeti: bir yadroning 1% i
# (`prober.PROBE_COST_BUDGET_PERCENT`). Bu yerda PROBER'dan import
# qilinMAYDI: qoida 1 bo'yicha `analyze.py` o'lchov modullarini import
# qilmaydi. Qiymat MUZLATILGAN va ikki joyda bir xil bo'lishi kerak -- bu
# `agent/contract` uchun ochiq savol.
PROBE_COST_BUDGET_PERCENT = 1.0


def probe_cost_section(trials: Sequence[dict[str, Any]],
                       log: WarningLog) -> dict[str, Any] | None:
    """§8.2 -- prober narxi, yadro foizida, arm bo'yicha.

    §8.2 prober narxini HAR TRIAL uchun o'lchashni va ARM'LAR BO'YICHA BIR
    XIL ushlashni talab qiladi (aks holda "C tezroq" degan natija prober
    narxining farqi bo'lib chiqishi mumkin).

    ZANJIR TEKSHIRILDI va UZILGAN (modul docstring'idagi PROBE_COST
    CHEKLOVI): `reduce.py` `prober_stop` ni o'qimaydi va `trial_metrics` ga
    narx chiqarmaydi. Shuning uchun bu funksiya `trial_metrics` da
    `probe_cost` field'ini IZLAYDI; topilmasa `None` qaytaradi va sabab
    `warnings` ga tushadi. NARX TO'QILMAYDI -- o'lchanmagan narxni nol yoki
    budjet qiymati deb berish §8.2 ni tekshirilgandek ko'rsatardi.
    """
    have = [r for r in trials if isinstance(r.get("probe_cost"), dict)]
    if not have:
        log.add("probe_cost_absent", "probe_cost",
                "`trial_metrics` da `probe_cost` field'i yo'q: `prober.py` "
                "narxni `cost_report()` da hisoblaydi va `prober_stop` ga "
                "yozadi, lekin `reduce.py` `prober_stop` ni O'QIMAYDI va "
                "narxni `trial_metrics` ga CHIQARMAYDI. Qo'shimcha: "
                "`prober_stop` run oxirida BIR MARTA chiqadi, demak §8.2 "
                "talab qilgan PER-TRIAL ro'yxat manbada ham yo'q. Bo'lim "
                "CHIQARILMAYDI -- narx TO'QILMAYDI")
        return None
    by_arm: dict[str, dict[str, Any]] = {}
    for r in trials:
        arm = str(r.get("arm"))
        pc = r.get("probe_cost")
        val = _f(pc.get("core_percent")) if isinstance(pc, dict) else None
        by_arm.setdefault(arm, {"core_percent": []})["core_percent"].append(val)
    n_missing = sum(1 for r in trials
                    if not isinstance(r.get("probe_cost"), dict))
    if n_missing:
        log.add("probe_cost_partial", "probe_cost",
                f"{n_missing}/{len(trials)} trial uchun `probe_cost` yo'q -- "
                "ro'yxatda `null` bo'lib qoladi, taxmin qilinmaydi")
    return {"budget_percent": PROBE_COST_BUDGET_PERCENT, "by_arm": by_arm}


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
        if c.get("disposition") not in PRIMARY_DISPOSITIONS:
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


def exclusions_section(trials: Sequence[dict[str, Any]],
                       primary_trials: Sequence[dict[str, Any]]
                       ) -> dict[str, Any]:
    """§12 -- eksklyuziya darajasi NATIJA sifatida, sababga ko'ra ajratilgan.

    §12: "`contaminated` va `aborted_guard` trial'lar birlamchi analizdan
    chiqariladi, LEKIN ularning ulushi natija sifatida beriladi. Yuqori
    eksklyuziya darajasi O'ZI natija -- yashirilmaydi."
    """
    total = len(trials)
    excluded = [r for r in trials
                if r.get("disposition") not in PRIMARY_DISPOSITIONS]
    by_reason: dict[str, int] = {}
    for r in excluded:
        reason = r.get("exclusion_reason") or str(r.get("disposition"))
        by_reason[reason] = by_reason.get(reason, 0) + 1
    return {
        "rate": (len(excluded) / total) if total else None,
        "by_reason": by_reason,
        "n_total": total,
        "n_excluded": len(excluded),
        "n_primary": len(primary_trials),
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
    false_recovery = false_recovery_section(primary_trials, log)
    downtime = downtime_section(primary_trials, log, n_boot=n_boot)
    sensitivity = sensitivity_section(sweep_cells, trials, log,
                                      None if t_trial_us is None
                                      else int(t_trial_us))
    multiplicity = multiplicity_section(primary, log)
    exclusions = exclusions_section(trials, primary_trials)
    probe_cost = probe_cost_section(trials, log)

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
                     "by_disposition": disposition_counts(trials)},
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
    ap.add_argument("--json", action="store_true",
                    help="analysis.json ni stdout'ga ham yozadi")
    args = ap.parse_args(argv)

    try:
        _assert_not_input(args.out, [args.trials, args.run_meta, args.sweep])
        trials = load_trials(args.trials)
        meta = load_run_meta(args.run_meta)
        sweep = load_sweep(args.sweep) if args.sweep else None
        obj = build_analysis(trials, meta, sweep)
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
