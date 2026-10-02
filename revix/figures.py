"""REVIX figura generatori -- FAQAT `analysis.json` dan SVG + sidecar JSON.

docs/architecture/04-driver-va-analiz-shartnomasi.md (driver-contract/v1.1)
ni amalga oshiradi:
  * §2.2 -- `analysis.json` sxemasi (bu modul uning ISTE'MOLCHISI)
  * §2.3 #9, §5 -- `t_trial_us` (recovery horizon) analizdan olinadi va
            `recovered_within_horizon: k/n` yonida figurada yoziladi
  * §2.3 -- hisoblab bo'lmagan narsa `warnings` ga, `W_stab > horizon`
            yacheykasi `note` bilan; figura ularni YASHIRMAYDI
  * §3   -- majburiy figuralar, `figures/<nom>.svg` + `figures/<nom>.json`,
            oq-qora chop etishda o'qiladigan uslub

PREREGISTRATION.md ga tayanadi:
  * §4   -- `W_stab` x `theta` sensitivity sweep (heatmap)
  * §6.1 -- uchta downtime o'lchovi `D_sd`, `D_probe`, `D_eff` -- HAMMASI
  * §6.2 -- har jadval/figura "T_trial ichida recovered: k/n" bilan birga
  * §8.2 -- probe narxi budjeti (>1% yadro)
  * §10.1-§10.2 -- nima chizilishi mumkin va NIMA CHIZILMAYDI
  * §11  -- birlamchi endpoint va falsifikatsiya qoidasi
  * §12  -- disposition yopiq enum; eksklyuziya ulushi NATIJA

QAT'IY QOIDALAR (buzilmaydi):

  1. **FAQAT `analysis.json`.** Bu modul xom ma'lumotga -- `probe.csv`,
     `events.jsonl`, `reduce.py` chiqishiga -- TEGMAYDI, `revix` paketidan
     hech narsa import qilmaydi. NEGA: figura analizdan uzoqlasha olmasligi
     uchun yagona mexanizm shu (§3). Fayl nomi aynan `analysis.json` bo'lishi
     va tarkibi §2.2 sxemasiga mos kelishi shart; aks holda `FiguresInputError`.
  2. **HAR FIGURA IKKI FAYL:** `<nom>.svg` va `<nom>.json`. Sidecar --
     figurani hosil qilgan AYNAN raqamlar. NEGA: figura ko'z bilan emas,
     raqam bilan tekshirilishi kerak (§3). Strukturaviy kafolat: chizish
     funksiyalari `analysis.json` ni ko'rmaydi, faqat tayyor `model` ni
     (= sidecar) oladi, demak sidecar'da bo'lmagan raqam chizilmaydi.
  3. **OQ-QORA CHOP ETISHDA O'QILADI.** Faqat qora/kulrang; qatorlar marker
     va chiziq turi bilan farqlanadi, rang bilan EMAS (§3 uslub qoidasi).
  4. **YO'Q QIYMAT YO'Q QIYMATDIR.** `None` = "o'lchanmagan", `0` = "o'lchangan
     nol". `None` interpolyatsiya qilinmaydi, nolga aylantirilmaydi, chiziq
     u orqali tortilmaydi; "missing" deb CHIZILADI va sidecar `missing` ga
     yoziladi. `nan`/`inf` ham "yo'q" hisoblanadi. NEGA: soxta aniqlik yo'q
     (§2.3 #6).
  5. **FIGURA STATISTIKA HISOBLAMAYDI.** CI, p-qiymat, kvantil, ECDF -- hammasi
     analizdan tayyor keladi. Figura faqat tasodifiy nomuvofiqlikni (masalan
     `p_hat != k/n`) `problems` sifatida SATH QILADI. NEGA: figura ichida ikkinchi
     analiz yozilsa, u birinchisidan uzoqlashadi -- aynan §3 oldini olmoqchi
     bo'lgan narsa. Cox/HR hech qachon chizilmaydi (§10.2), `mean ± SD` ham.
  6. **`warnings` VA `note` YASHIRILMAYDI.** `analysis.json["warnings"]` ning
     soni har figurada ko'rsatiladi (jim tushirib qoldirilmaydi), figuraga
     tegishlilari matni bilan; sweep yacheykasining `note`i yacheykaning
     o'zida belgilanadi va izohi figura tagida beriladi.
  7. **DETERMINISTIK.** Bir xil `analysis.json` -> bir xil sidecar (va bir xil
     SVG: vaqt tamg'asi yo'q, `svg.hashsalt` qotirilgan). Modul soat
     o'qimaydi; `generated_mono_us` analizdan o'tkaziladi.
  8. **Yagona yangi bog'liqlik: matplotlib** (§3 allaqachon talab qiladi).
     `Agg` backend ANIQ o'rnatiladi, pyplot ishlatilmaydi (global holat yo'q).
     seaborn/plotly/pandas -- yo'q. Import dangasa: matplotlib bo'lmasa ham
     `import revix.figures` ishlaydi, `main()` aniq xabar bilan to'xtaydi.
  9. **K/N HAR DOIM YO'LDOSH, O'Z HORIZON'I BILAN.** `recovered_within_horizon:
     k/n` (§6.2) survival va downtime figuralarida ko'rsatiladi, yonida
     `T_trial = <soniya>` (`analysis.json["t_trial_us"]` dan; NEGA: horizon'siz
     k/n ma'nosiz). Analizda bo'lmasa -- "not provided", taxmin YO'Q.
 10. **vr=None -- ALOHIDA KATEGORIYA.** Aniqlanmagan (undetermined) soni "recovered
     emas"ga QO'SHILMAYDI (o'lchanmagan narsani natijaga aylantirmaslik).

ISTE'MOL QILINADIGAN KALITLAR (§2.2) -- figura bo'yicha:

  p_vr_vs_pressure   primary.{endpoint,test,statistic,p_value,direction,
                     cells[level,k,n,p_hat,ci_lower,ci_upper,ci_method],
                     risk_difference{estimate,ci_lower,ci_upper,ci_method},
                     falsified,falsification_rule}
  km_time_to_vr      survival.km.by_arm.<arm>.{times,survival,at_risk,
                     greenwood_var}, survival.logrank.{chi2,p_value,observed,
                     expected}, survival.rmst.{tau,by_arm,difference},
                     survival.proportional_hazards_checked,
                     survival.censoring.{n_censored,recovered_within_horizon},
                     t_trial_us
  downtime_ecdf      downtime.{d_sd,d_probe,d_eff}.{median,p90,p99},
                     survival.censoring.recovered_within_horizon, t_trial_us
  sensitivity_heatmap sensitivity.{w_stab,theta,grid[w_stab,theta,
                     p_vr_by_level,note]}, t_trial_us
  exclusion_breakdown n_trials.{total,by_disposition}, exclusions.{rate,
                     by_reason}
  probe_cost         probe_cost.{budget_percent,by_arm.<arm>.core_percent}

§2.2 SXEMASIDA YO'Q, LEKIN FIGURA TALAB QILADIGAN KALITLAR (ochiq savollar --
hisobotda; bu modul ularni ixtiro QILMAYDI, faqat mavjud bo'lsa ISTE'MOL
qiladi, bo'lmasa figurada "missing/not provided" deb ko'rsatadi):

  a. `survival.time_unit` / `downtime.time_unit` / `time_unit` ("s"|"ms"|"us")
     -- vaqt o'qining birligi. Yo'q bo'lsa o'q "unit not stated" deb yoziladi
     (birlik TAXMIN QILINMAYDI).
  b. `downtime.<m>.{median,p90,p99}` shakli: son YOKI
     {estimate|value, ci_lower, ci_upper, ci_method}. §2.2 faqat `{}` deydi.
  c. `downtime.<m>.ecdf = {"x": [...], "y": [...]}` -- ECDF nuqtalari. Usiz
     "downtime_ecdf" faqat ma'lum kvantillarni (0.5/0.9/0.99) chizadi,
     ECDF chizig'i INTERPOLYATSIYA qilib tortilmaydi.
  d. `downtime.<m>.recovered_within_horizon` (bo'lmasa survival.censoring dan).
  d2. `survival.censoring.n_undetermined` -- vr=None soni (bo'lmasa "not provided").
  d3. `t_trial_us` v1.1 §2.3 #9 da nomlangan, lekin §2.2 JSON bloki uni ko'rsatmaydi;
     bu modul uni YUQORI DARAJADAGI kalit deb o'qiydi.
  e. `probe_cost` bo'limi (§8.2) -- §2.2 da umuman yo'q. Nomlar `prober.py` ning
     `core_percent` / `budget_percent` maydonlariga mos.
  f. `primary.ci_level`, `primary.risk_difference.contrast` (RD qaysi
     darajalar ayirmasi) -- bo'lmasa figura 95% yoki P0-P2 deb TAXMIN QILMAYDI.

Chiqish kodi: 0 -- hamma figura yozildi (placeholder'lar ham, ular ogohlantirish
va `--json` da `status` bilan ko'rinadi); 1 -- kirish rad etildi / chizish
xatosi / matplotlib yo'q; 2 -- argparse (noto'g'ri flag).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import re
import sys
import textwrap
from typing import Any, Callable

FIGURES_VERSION = 1
CONTRACT = "driver-contract/v1 §3"
ANALYSIS_FILENAME = "analysis.json"
SUPPORTED_SCHEMA_VERSION = 1

# §3 majburiy figuralar (P1 uchun tegishlilari) -- tartib qat'iy.
FIGURE_NAMES = (
    "p_vr_vs_pressure",
    "km_time_to_vr",
    "downtime_ecdf",
    "sensitivity_heatmap",
    "exclusion_breakdown",
    "probe_cost",
)

# §12 yopiq enum. `schema.DISPOSITIONS` bilan bir xil bo'lishi TEST bilan
# tekshiriladi (import qilinmaydi -- 1-qoida).
DISPOSITIONS = (
    "complete",
    "censored",
    "contaminated",
    "aborted_guard",
    "washout_timeout",
    "harness_error",
)
# §12: faqat shu ikkitasi birlamchi analizdan CHIQARILADI (ulushi natija).
EXCLUDED_FROM_PRIMARY = ("contaminated", "aborted_guard")

# §6.1 uchta o'lchov; D_probe -- asosiy.
DOWNTIME_MEASURES = ("d_sd", "d_probe", "d_eff")
DOWNTIME_LABELS = {"d_sd": "D_sd", "d_probe": "D_probe (primary)", "d_eff": "D_eff"}
# (kalit, ECDF o'qidagi kumulyativ ehtimol) -- median/p90/p99 (§10.2)
DOWNTIME_QUANTILES = (("median", 0.5), ("p90", 0.9), ("p99", 0.99))

# §4: pilot parametrlari (heatmap'da birlamchi yacheyka belgilanadi).
PILOT_W_STAB_S = 8.0
PRIMARY_THETA = 0.8
# §8.2: probe narxi budjeti -- `prober.PROBE_COST_BUDGET_PERCENT` bilan bir xil.
PROBE_COST_BUDGET_PERCENT = 1.0

_UNIT_LABELS = {"s": "s", "ms": "ms", "us": "µs"}
_UNIT_UNSTATED = "unit not stated in analysis.json"

# Figura bo'yicha "tegishli warning" kalit so'zlari (kichik harfda qidiriladi).
# §2.2 `warnings` ning ichki tuzilishini belgilamaydi, shuning uchun mezon --
# matn/`section`/`figure` maydonidagi kalit so'z. Tegishli bo'lmagan warning ham
# JIM tushirilmaydi: soni har figurada ko'rsatiladi.
_WARN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "p_vr_vs_pressure": (
        "primary", "p(vr)", "p_vr", "trend", "cochran", "risk_difference",
        "risk difference", "newcombe", "clopper", "falsif", "multiplicity",
        "holm",
    ),
    "km_time_to_vr": (
        "survival", "kaplan", "km", "logrank", "log-rank", "rmst", "censor",
        "hazard", "proportional", "cox", "greenwood", "time_to_vr",
    ),
    "downtime_ecdf": (
        "downtime", "d_sd", "d_probe", "d_eff", "bca", "bootstrap", "ecdf",
        "quantile", "p90", "p99", "median",
    ),
    "sensitivity_heatmap": (
        "sensitivity", "w_stab", "theta", "sweep", "horizon", "grid",
    ),
    "exclusion_breakdown": (
        "exclusion", "disposition", "contaminated", "aborted_guard",
        "excluded", "n_trials",
    ),
    "probe_cost": ("probe_cost", "probe cost", "prober", "overrun", "budget"),
}

# --- uslub konstantalari -----------------------------------------------------

FS_TITLE = 10.0
FS_SUB = 7.5
FS_MAIN = 7.5
FS_SMALL = 6.5
_LEFT_IN = 0.85
_RIGHT_IN = 0.30
_TOP_IN = 0.80
_XAXIS_IN = 0.80
_MARGIN_IN = 0.14
_MISSING_LINES_MAX = 4        # figura ostida; to'liq ro'yxat sidecar `missing` da
_TEXT_WRAP_FACTOR = 0.58     # DejaVu Sans o'rtacha belgi kengligi / shrift o'lchami

# Oq-qora uchun qatorlar: marker + chiziq turi + to'ldirish; rang faqat kulrang.
_SERIES_STYLES = (
    {"marker": "o", "ls": "-", "mfc": "black", "color": "black"},
    {"marker": "s", "ls": "--", "mfc": "white", "color": "black"},
    {"marker": "^", "ls": "-.", "mfc": "0.55", "color": "0.15"},
    {"marker": "D", "ls": ":", "mfc": "white", "color": "0.30"},
    {"marker": "v", "ls": (0, (5, 1, 1, 1, 1, 1)), "mfc": "black", "color": "0.30"},
    {"marker": "P", "ls": (0, (1, 3)), "mfc": "0.80", "color": "0.15"},
)
_DOWNTIME_STYLES = {
    "d_sd": {"marker": "o", "ls": "--", "mfc": "white", "color": "0.15", "lw": 1.2},
    "d_probe": {"marker": "s", "ls": "-", "mfc": "black", "color": "black", "lw": 1.8},
    "d_eff": {"marker": "^", "ls": ":", "mfc": "0.60", "color": "0.30", "lw": 1.6},
}

_RC = {
    "svg.fonttype": "none",              # matn <text> bo'lib qoladi: tekshirsa bo'ladi
    "svg.hashsalt": "revix-figures-v1",  # deterministik ID'lar
    "font.family": "sans-serif",
    "font.size": 8.0,
    "axes.edgecolor": "black",
    "axes.labelcolor": "black",
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "xtick.color": "black",
    "ytick.color": "black",
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "text.color": "black",
    "legend.frameon": False,
    "legend.fontsize": 7.0,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "hatch.linewidth": 0.6,
}


# --- xatolar -----------------------------------------------------------------


class FiguresInputError(Exception):
    """Kirish `analysis.json` emas yoki §2.2 sxemasiga mos emas -- rad etiladi."""


class FiguresDependencyError(Exception):
    """matplotlib mavjud emas. Stub/vendor QILINMAYDI -- aniq xabar beriladi."""


# --- kirish: faqat analysis.json ---------------------------------------------


def load_analysis(path: str) -> tuple[dict[str, Any], str]:
    """`analysis.json` ni o'qiydi; (obyekt, fayl baytlarining sha256) qaytaradi.

    BU MODULNING YAGONA KIRISH NUQTASI. Rad etadi (FiguresInputError):
      * fayl nomi aynan `analysis.json` emas (`probe.csv`, `events.jsonl`,
        `trial_metrics.jsonl`, `analysis.json.bak` ...);
      * JSON obyekt emas, yoki xom record (`record_type` bor) ko'rinishida;
      * `schema_version` != 1 yoki `analysis_version` yo'q.
    NEGA nom VA tarkib birgalikda: faqat nom bo'yicha tekshiruv `cp events.jsonl
    analysis.json` bilan aldanardi; faqat tarkib bo'yicha esa noto'g'ri fayl
    o'qishga urinish allaqachon sodir bo'lgan bo'lardi.
    """
    if os.path.basename(path) != ANALYSIS_FILENAME:
        raise FiguresInputError(
            f"faqat '{ANALYSIS_FILENAME}' o'qiladi (§3), berilgani: "
            f"'{os.path.basename(path)}'. Xom ma'lumot (probe.csv, events.jsonl, "
            f"reduce.py chiqishi) figura moduliga berilmaydi.")
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise FiguresInputError(f"'{path}' o'qilmadi: {exc}") from exc
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise FiguresInputError(f"'{path}' yaroqli JSON emas: {exc}") from exc
    if not isinstance(obj, dict):
        raise FiguresInputError(f"'{path}': JSON obyekt kutilgan (§2.2)")
    if "record_type" in obj:
        raise FiguresInputError(
            f"'{path}' xom hodisa record'iga o'xshaydi (record_type="
            f"{obj.get('record_type')!r}), analysis.json emas")
    if obj.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise FiguresInputError(
            f"schema_version={obj.get('schema_version')!r}; qo'llab-quvvatlanadi: "
            f"{SUPPORTED_SCHEMA_VERSION} (§2.2)")
    if not isinstance(obj.get("analysis_version"), str):
        raise FiguresInputError("'analysis_version' (str) yo'q: analysis.json emas (§2.2)")
    return obj, hashlib.sha256(raw).hexdigest()


# --- kichik yordamchilar -----------------------------------------------------


def _num(x: Any) -> float | None:
    """Chekli son yoki None. bool, nan, inf, str -- "yo'q" (4-qoida)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return None
    f = float(x)
    return f if math.isfinite(f) else None


def _int(x: Any) -> int | None:
    """Manfiy bo'lmagan butun yoki None."""
    if isinstance(x, bool):
        return None
    if isinstance(x, int):
        return x if x >= 0 else None
    if isinstance(x, float) and math.isfinite(x) and x >= 0 and x == int(x):
        return int(x)
    return None


def _str(x: Any) -> str | None:
    return x if isinstance(x, str) and x != "" else None


def _label(x: Any, default: str) -> str:
    if isinstance(x, bool):
        return default
    if isinstance(x, (str, int)) and str(x) != "":
        return str(x)
    return default


def _get(d: Any, *keys: str) -> Any:
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _numlist(xs: Any) -> list[float | None] | None:
    if not isinstance(xs, list):
        return None
    return [_num(v) for v in xs]


def _fmt(x: float | None, spec: str = ".3g") -> str:
    return "missing" if x is None else format(x, spec)


def _natural_key(s: str) -> tuple:
    return tuple(int(p) if p.isdigit() else p for p in re.split(r"(\d+)", s))


def _parse_kn(raw: Any) -> dict[str, Any] | None:
    """`recovered_within_horizon` "k/n" -> {"raw","k","n"}; yo'q bo'lsa None."""
    if not isinstance(raw, str) or raw.strip() == "":
        return None
    m = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+)\s*", raw)
    return {"raw": raw, "k": int(m.group(1)) if m else None,
            "n": int(m.group(2)) if m else None}


def _time_unit(an: dict, section: str) -> dict[str, Any]:
    """Vaqt o'qi birligi: faqat analizda e'lon qilingan bo'lsa (a. ochiq savol)."""
    for cand in (_get(an, section, "time_unit"), an.get("time_unit")):
        if isinstance(cand, str) and cand in _UNIT_LABELS:
            return {"stated": True, "unit": cand, "label": _UNIT_LABELS[cand]}
    return {"stated": False, "unit": None, "label": _UNIT_UNSTATED}


_AXIS_PER_SECOND = {"s": 1.0, "ms": 1e3, "us": 1e6}


def _horizon(an: dict, unit: dict[str, Any] | None = None) -> dict[str, Any]:
    """Recovery horizon `T_trial` (driver-contract/v1.1 §5, §2.3 #9).

    `analysis.json["t_trial_us"]` dan OLINADI, hech qachon taxmin qilinmaydi.
    NEGA: `recovered_within_horizon: k/n` (§6.2) o'z horizon'isiz ma'nosiz.
    `axis_value` -- faqat vaqt o'qining birligi e'lon qilingan bo'lsa (aks holda
    o'qqa nuqta qo'yish birlikni taxmin qilishni talab qilardi).
    """
    us = _int(an.get("t_trial_us"))
    sec = None if us is None else us / 1e6
    axis = None
    if sec is not None and unit is not None and unit["stated"]:
        axis = sec * _AXIS_PER_SECOND[unit["unit"]]
    return {"t_trial_us": us, "seconds": sec, "axis_value": axis}


def _horizon_text(h: dict[str, Any]) -> str:
    if h["seconds"] is None:
        return "T_trial not provided in analysis.json (t_trial_us missing)"
    return f"T_trial = {h['seconds']:g} s"


def _empty_prep() -> dict[str, Any]:
    return {"placeholder": None, "data": None, "missing": [], "notes": [],
            "problems": [], "text_main": [], "extra": {}}


def _placeholder(reason: str) -> dict[str, Any]:
    p = _empty_prep()
    p["placeholder"] = reason
    return p


# --- warnings: yashirilmaydi (6-qoida) ----------------------------------------


def _warning_text(w: Any) -> str:
    if isinstance(w, str):
        return w
    if isinstance(w, dict):
        for k in ("message", "msg", "text", "reason"):
            if isinstance(w.get(k), str):
                return w[k]
        return json.dumps(w, sort_keys=True, ensure_ascii=False)
    return json.dumps(w, sort_keys=True, ensure_ascii=False, default=str)


def _warning_scope(w: Any) -> str:
    """Kalit so'z qidiriladigan matn: warning matni + `section/key/path/code`."""
    parts = [_warning_text(w)]
    if isinstance(w, dict):
        for k in ("section", "key", "path", "code", "measure", "figure"):
            v = w.get(k)
            if isinstance(v, str):
                parts.append(v)
    return " ".join(parts).lower()


def _warnings_for(an: dict, name: str) -> dict[str, Any]:
    ws = an.get("warnings")
    items = ws if isinstance(ws, list) else []
    relevant: list[str] = []
    for w in items:
        tagged = isinstance(w, dict) and (
            w.get("figure") == name
            or (isinstance(w.get("figures"), list) and name in w["figures"]))
        scope = _warning_scope(w)
        if tagged or any(k in scope for k in _WARN_KEYWORDS.get(name, ())):
            relevant.append(_warning_text(w))
    return {"total": len(items), "relevant": relevant}


# =============================================================================
# 1. PREPARE: analysis.json -> model (sidecar). Chizish faqat shu model'dan.
# =============================================================================


def _prep_p_vr_vs_pressure(an: dict) -> dict[str, Any]:
    """§10.1 / §11: P(VR) pressure darajalari bo'yicha, har yacheyka CI bilan."""
    prim = an.get("primary")
    if not isinstance(prim, dict):
        return _placeholder("analysis.json has no 'primary' object (§2.2)")
    raw = prim.get("cells")
    if not isinstance(raw, list) or not raw:
        return _placeholder("primary.cells is missing or empty: nothing to draw")

    out = _empty_prep()
    cells: list[dict[str, Any]] = []
    for i, c in enumerate(raw):
        if not isinstance(c, dict):
            out["problems"].append(f"primary.cells[{i}] is not an object; skipped")
            continue
        level = _label(c.get("level"), f"cell{i}")
        k, n = _int(c.get("k")), _int(c.get("n"))
        p, lo, hi = _num(c.get("p_hat")), _num(c.get("ci_lower")), _num(c.get("ci_upper"))
        absent = [f for f, v in (("k", k), ("n", n), ("p_hat", p),
                                 ("ci_lower", lo), ("ci_upper", hi)) if v is None]
        if absent:
            out["missing"].append({"where": f"primary.cells[{level}]", "fields": absent})
        # Nomuvofiqlikni SATH qiladi, tuzatmaydi (5-qoida).
        if k is not None and n is not None:
            if k > n:
                out["problems"].append(f"{level}: k={k} > n={n}")
            elif n > 0 and p is not None and abs(p - k / n) > 1e-6:
                out["problems"].append(
                    f"{level}: p_hat={p:.6g} differs from k/n={k}/{n}={k / n:.6g}")
            elif n == 0 and p is not None:
                out["problems"].append(f"{level}: n=0 but p_hat={p:.6g} is given")
        if p is not None and lo is not None and hi is not None and not (
                lo - 1e-9 <= p <= hi + 1e-9):
            out["problems"].append(f"{level}: p_hat={p:.6g} lies outside CI [{lo:.6g}, {hi:.6g}]")
        cells.append({
            "level": level, "x": len(cells), "k": k, "n": n, "p_hat": p,
            "ci_lower": lo, "ci_upper": hi, "ci_method": _str(c.get("ci_method")),
            "point_drawn": p is not None,
            "ci_drawn": p is not None and lo is not None and hi is not None,
        })
    if not cells:
        return _placeholder("primary.cells has no usable cell objects")

    rd_raw = prim.get("risk_difference")
    rd = None
    if isinstance(rd_raw, dict):
        rd = {"estimate": _num(rd_raw.get("estimate")),
              "ci_lower": _num(rd_raw.get("ci_lower")),
              "ci_upper": _num(rd_raw.get("ci_upper")),
              "ci_method": _str(rd_raw.get("ci_method")),
              "contrast": _str(rd_raw.get("contrast"))}
        if None in (rd["estimate"], rd["ci_lower"], rd["ci_upper"]):
            out["missing"].append({"where": "primary.risk_difference",
                                   "fields": [f for f in ("estimate", "ci_lower", "ci_upper")
                                              if rd[f] is None]})
    else:
        out["missing"].append({"where": "primary.risk_difference", "fields": ["<whole object>"]})

    falsified = prim.get("falsified") if isinstance(prim.get("falsified"), bool) else None
    stat, pval = _num(prim.get("statistic")), _num(prim.get("p_value"))
    for field, val in (("statistic", stat), ("p_value", pval)):
        if val is None:
            out["missing"].append({"where": "primary", "fields": [field]})
    ci_level = prim.get("ci_level")
    ci_level = ci_level if isinstance(ci_level, (str, int, float)) and not isinstance(
        ci_level, bool) else None

    out["data"] = {
        "endpoint": _str(prim.get("endpoint")),
        "test": _str(prim.get("test")),
        "statistic": stat, "p_value": pval,
        "direction": _str(prim.get("direction")),
        "ci_level": ci_level,
        "cells": cells,
        "risk_difference": rd,
        "falsified": falsified,
        "falsification_rule": _str(prim.get("falsification_rule")),
    }
    d = out["data"]
    out["text_main"].append(
        f"{d['test'] or 'trend test (name not provided)'}: statistic = {_fmt(stat)}, "
        f"p = {_fmt(pval)}, direction = {d['direction'] or 'missing'}")
    if rd is not None:
        contrast = f", contrast: {rd['contrast']}" if rd["contrast"] else \
            ", contrast not stated in analysis.json"
        out["text_main"].append(
            f"risk difference = {_fmt(rd['estimate'])}  CI [{_fmt(rd['ci_lower'])}, "
            f"{_fmt(rd['ci_upper'])}]  ({rd['ci_method'] or 'method not provided'}"
            f"{contrast})")
    else:
        out["text_main"].append("risk difference: missing (not provided by analysis.json)")
    fals = "missing" if falsified is None else ("true" if falsified else "false")
    rule = f"   rule: {d['falsification_rule']}" if d["falsification_rule"] else ""
    out["text_main"].append(f"falsified (§11): {fals}{rule}")
    return out


def _prep_km_time_to_vr(an: dict) -> dict[str, Any]:
    """§10.2: Kaplan-Meier time-to-VR har arm uchun + log-rank + RMST."""
    surv = an.get("survival")
    by_arm = _get(surv, "km", "by_arm")
    if not isinstance(surv, dict) or not isinstance(by_arm, dict) or not by_arm:
        return _placeholder("analysis.json has no survival.km.by_arm: nothing to draw")

    out = _empty_prep()
    unit = _time_unit(an, "survival")
    if not unit["stated"]:
        out["notes"].append("time unit is not stated in analysis.json "
                            "(no 'time_unit' key): axis shows raw values")

    arms: list[dict[str, Any]] = []
    for arm in sorted(by_arm):
        a = by_arm[arm]
        if not isinstance(a, dict):
            out["missing"].append({"where": f"survival.km.by_arm[{arm}]",
                                   "fields": ["<whole object>"]})
            continue
        times, sv = _numlist(a.get("times")), _numlist(a.get("survival"))
        at_risk, gw = _numlist(a.get("at_risk")), _numlist(a.get("greenwood_var"))
        reason = None
        if times is None or sv is None:
            reason = "times/survival missing"
        elif len(times) == 0:
            reason = "no event times (all trials censored, or arm empty)"
        elif len(times) != len(sv):
            reason = f"len(times)={len(times)} != len(survival)={len(sv)}"
        elif None in times or None in sv:
            reason = "times/survival contain missing values (not interpolated)"
        elif any(t2 < t1 for t1, t2 in zip(times, times[1:])):
            reason = "times are not non-decreasing"
        if at_risk is not None and times is not None and len(at_risk) != len(times):
            out["problems"].append(f"{arm}: len(at_risk)={len(at_risk)} != len(times)={len(times)}")
        if reason is not None:
            out["missing"].append({"where": f"survival.km.by_arm[{arm}]", "fields": [reason]})
            arms.append({"arm": str(arm), "drawn": False, "reason": reason,
                         "times": times, "survival": sv, "at_risk": at_risk,
                         "greenwood_var": gw, "drawn_x": None, "drawn_y": None})
            continue
        # S(0)=1: KM konvensiyasi (stats.KMResult.survival_at, birinchi event'dan oldin
        # 1.0). Bu qo'shilgan NUQTA sidecar'da ochiq ko'rsatiladi.
        x0 = min(0.0, times[0])
        arms.append({"arm": str(arm), "drawn": True, "reason": None,
                     "times": times, "survival": sv, "at_risk": at_risk,
                     "greenwood_var": gw,
                     "drawn_x": [x0] + times, "drawn_y": [1.0] + sv,
                     "anchor_added": {"x": x0, "y": 1.0}})

    lr = _get(surv, "logrank")
    logrank = None
    if isinstance(lr, dict):
        logrank = {
            "chi2": _num(lr.get("chi2")), "p_value": _num(lr.get("p_value")),
            "observed": {str(k): _num(v) for k, v in lr["observed"].items()}
            if isinstance(lr.get("observed"), dict) else None,
            "expected": {str(k): _num(v) for k, v in lr["expected"].items()}
            if isinstance(lr.get("expected"), dict) else None,
        }
    else:
        out["missing"].append({"where": "survival.logrank", "fields": ["<whole object>"]})

    rm = _get(surv, "rmst")
    rmst = None
    if isinstance(rm, dict):
        diff = rm.get("difference")
        rmst = {
            "tau": _num(rm.get("tau")),
            "by_arm": {str(k): {"estimate": _num(_get(v, "estimate")), "se": _num(_get(v, "se"))}
                       for k, v in sorted(rm["by_arm"].items())}
            if isinstance(rm.get("by_arm"), dict) else None,
            "difference": {k: _num(diff.get(k)) for k in ("estimate", "se", "ci_lower", "ci_upper")}
            if isinstance(diff, dict) else None,
        }
    else:
        out["missing"].append({"where": "survival.rmst", "fields": ["<whole object>"]})

    ph = surv.get("proportional_hazards_checked")
    ph = ph if isinstance(ph, bool) else None
    cens = _get(surv, "censoring")
    n_cens = _int(_get(cens, "n_censored"))
    recovered = _parse_kn(_get(cens, "recovered_within_horizon"))
    # vr=None (aniqlanmagan) -- ALOHIDA kategoriya: "recovered emas" ga QO'SHILMAYDI
    # (reduce.py: None hech qachon False ga aylantirilmaydi). §2.2 da bu son yo'q;
    # bo'lsa (`censoring.n_undetermined`) alohida ko'rsatiladi, bo'lmasa "not provided".
    n_undet = _int(_get(cens, "n_undetermined"))
    horizon = _horizon(an, unit)

    out["data"] = {
        "time_unit": unit, "arms": arms, "logrank": logrank, "rmst": rmst,
        "proportional_hazards_checked": ph,
        "censoring": {"n_censored": n_cens, "n_undetermined": n_undet},
        "horizon": horizon,
    }
    out["extra"]["recovered_within_horizon"] = recovered

    # --- figura tagidagi matn (hammasi analizdan, taxminsiz) ---
    if logrank is not None:
        out["text_main"].append(
            f"log-rank: chi2 = {_fmt(logrank['chi2'])}, p = {_fmt(logrank['p_value'])}")
    if rmst is not None:
        tau = _fmt(rmst["tau"])
        tail = f" {unit['label']}" if unit["stated"] else ""
        if rmst["by_arm"]:
            per = "; ".join(f"{k} = {_fmt(v['estimate'])} (SE {_fmt(v['se'])})"
                            for k, v in rmst["by_arm"].items())
            out["text_main"].append(f"RMST (tau = {tau}{tail}): {per}")
        df = rmst["difference"]
        if df is not None:
            out["text_main"].append(
                f"RMST difference = {_fmt(df['estimate'])} (SE {_fmt(df['se'])})  "
                f"CI [{_fmt(df['ci_lower'])}, {_fmt(df['ci_upper'])}]")
        else:
            out["text_main"].append("RMST difference: missing")
    rec_txt = recovered["raw"] if recovered else "not provided"
    out["text_main"].append(
        f"recovered within horizon: {rec_txt}  ({_horizon_text(horizon)})   "
        f"censored trials kept in KM: {'missing' if n_cens is None else n_cens} (§6.2)")
    out["text_main"].append(
        "VR undetermined (vr=None, own category; not counted as recovered or failed): "
        f"{'not provided' if n_undet is None else n_undet}")
    if horizon["seconds"] is None:
        out["missing"].append({"where": "analysis.json", "fields": ["t_trial_us"]})
    if ph is None:
        out["text_main"].append("proportional_hazards_checked: missing; hazard ratio is not drawn")
    else:
        out["text_main"].append(
            f"proportional_hazards_checked = {'true' if ph else 'false'}; "
            "hazard ratio is never drawn (§10.2)")
    return out


def _quantile(v: Any) -> dict[str, Any] | None:
    """Kvantil qiymati: son YOKI {estimate|value|point, ci_lower, ci_upper, ci_method}."""
    if isinstance(v, dict):
        est = next((_num(v[k]) for k in ("estimate", "value", "point") if k in v), None)
        lo, hi = _num(v.get("ci_lower")), _num(v.get("ci_upper"))
        ci = v.get("ci")
        if lo is None and hi is None and isinstance(ci, list) and len(ci) == 2:
            lo, hi = _num(ci[0]), _num(ci[1])
        if est is None:
            return None
        return {"estimate": est, "ci_lower": lo, "ci_upper": hi,
                "ci_method": _str(v.get("ci_method"))}
    est = _num(v)
    return None if est is None else {"estimate": est, "ci_lower": None, "ci_upper": None,
                                     "ci_method": None}


def _prep_downtime_ecdf(an: dict) -> dict[str, Any]:
    """§6.1: D_sd, D_probe, D_eff -- uchalasi; median/p90/p99 + BCa CI (§10.2)."""
    dt = an.get("downtime")
    if not isinstance(dt, dict):
        return _placeholder("analysis.json has no 'downtime' object (§2.2)")

    out = _empty_prep()
    unit = _time_unit(an, "downtime")
    if not unit["stated"]:
        out["notes"].append("time unit is not stated in analysis.json "
                            "(no 'time_unit' key): axis shows raw values")
    fallback_rec = _parse_kn(_get(an, "survival", "censoring", "recovered_within_horizon"))

    measures: list[dict[str, Any]] = []
    any_quantile = False
    any_ecdf = False
    for m in DOWNTIME_MEASURES:
        raw = dt.get(m)
        if m not in dt:
            out["missing"].append({"where": f"downtime.{m}", "fields": ["<key absent>"]})
        elif not isinstance(raw, dict) or not raw:
            out["missing"].append({"where": f"downtime.{m}", "fields": ["<empty>"]})
        raw = raw if isinstance(raw, dict) else {}
        qs: dict[str, Any] = {}
        for qname, prob in DOWNTIME_QUANTILES:
            q = _quantile(raw.get(qname))
            qs[qname] = None if q is None else dict(q, prob=prob)
            if q is None and raw:
                out["missing"].append({"where": f"downtime.{m}.{qname}", "fields": ["estimate"]})
            elif q is not None:
                any_quantile = True
                if q["ci_lower"] is None or q["ci_upper"] is None:
                    out["missing"].append({"where": f"downtime.{m}.{qname}",
                                           "fields": ["ci_lower/ci_upper"]})
        ecdf = None
        e = raw.get("ecdf")
        if isinstance(e, dict):
            ex, ey = _numlist(e.get("x")), _numlist(e.get("y"))
            if (ex is None or ey is None or len(ex) != len(ey) or len(ex) == 0
                    or None in ex or None in ey
                    or any(b < a for a, b in zip(ex, ex[1:]))
                    or any(not 0.0 <= v <= 1.0 for v in ey)):
                out["problems"].append(
                    f"downtime.{m}.ecdf is malformed (x/y missing, unequal, unsorted or "
                    "outside [0,1]); ECDF line not drawn")
            else:
                ecdf = {"x": ex, "y": ey}
                any_ecdf = True
        rec = _parse_kn(raw.get("recovered_within_horizon"))
        measures.append({
            "measure": m, "label": DOWNTIME_LABELS[m], "n": _int(raw.get("n")),
            "quantiles": qs, "ecdf": ecdf, "recovered_within_horizon": rec,
            "has_data": ecdf is not None or any(v is not None for v in qs.values()),
        })

    if not any_quantile and not any_ecdf:
        return dict(_placeholder("downtime has no median/p90/p99 and no ECDF for any of "
                                 "d_sd, d_probe, d_eff"), notes=out["notes"])

    if not any_ecdf:
        out["notes"].append(
            "analysis.json provides no per-trial ECDF (downtime.<measure>.ecdf): only the "
            "summary quantiles (cumulative probability 0.5 / 0.9 / 0.99) are drawn; no ECDF "
            "line is interpolated through them")
    recovered = fallback_rec
    horizon = _horizon(an, unit)
    if horizon["seconds"] is None:
        out["missing"].append({"where": "analysis.json", "fields": ["t_trial_us"]})
    out["data"] = {"time_unit": unit, "measures": measures, "ecdf_available": any_ecdf,
                   "horizon": horizon}
    out["extra"]["recovered_within_horizon"] = recovered
    rec_txt = recovered["raw"] if recovered else "not provided"
    out["text_main"].append(
        f"recovered within horizon: {rec_txt}  ({_horizon_text(horizon)})  (§6.2: downtime "
        "summaries are conditional on recovery within the horizon; censored trials are not hidden)")
    for ms in measures:
        own = ms["recovered_within_horizon"]
        if own is not None:
            out["text_main"].append(f"{ms['label']}: recovered within horizon {own['raw']}")
    return out


def _by_level_value(v: Any) -> dict[str, Any]:
    if isinstance(v, dict):
        p = next((_num(v[k]) for k in ("p_hat", "p_vr", "value") if k in v), None)
        return {"p_vr": p, "k": _int(v.get("k")), "n": _int(v.get("n"))}
    return {"p_vr": _num(v), "k": None, "n": None}


def _prep_sensitivity_heatmap(an: dict) -> dict[str, Any]:
    """§4: W_stab x theta sweep -- har pressure darajasi uchun alohida panel."""
    sens = an.get("sensitivity")
    grid = _get(sens, "grid")
    if not isinstance(sens, dict) or not isinstance(grid, list) or not grid:
        return _placeholder("analysis.json has no sensitivity.grid (§2.2): nothing to draw")

    out = _empty_prep()
    seen: dict[tuple[float, float], dict[str, Any]] = {}
    level_set: set[str] = set()
    for i, g in enumerate(grid):
        if not isinstance(g, dict):
            out["problems"].append(f"sensitivity.grid[{i}] is not an object; skipped")
            continue
        w, th = _num(g.get("w_stab")), _num(g.get("theta"))
        if w is None or th is None:
            out["problems"].append(f"sensitivity.grid[{i}] lacks numeric w_stab/theta; skipped")
            continue
        if (w, th) in seen:
            out["problems"].append(
                f"sensitivity.grid has duplicate cell (w_stab={w:g}, theta={th:g}); first kept")
            continue
        by = g.get("p_vr_by_level")
        by = by if isinstance(by, dict) else {}
        note = g.get("note")
        note = None if note is None else (note if isinstance(note, str) else json.dumps(
            note, sort_keys=True, ensure_ascii=False))
        seen[(w, th)] = {"by": {str(k): _by_level_value(v) for k, v in by.items()},
                         "note": note if note != "" else None}
        level_set.update(str(k) for k in by)

    if not seen:
        return _placeholder("sensitivity.grid has no usable cells")
    prim_cells = _get(an, "primary", "cells")
    ordered = [str(c.get("level")) for c in prim_cells if isinstance(c, dict)
               and c.get("level") is not None] if isinstance(prim_cells, list) else []
    levels = [lv for lv in dict.fromkeys(ordered) if lv in level_set]
    levels += sorted(level_set - set(levels), key=_natural_key)
    if not levels:
        return _placeholder("sensitivity.grid cells carry no p_vr_by_level values")

    def declared(key: str) -> list[float]:
        v = sens.get(key)
        return [x for x in (_numlist(v) or []) if x is not None]
    w_axis = sorted(set(declared("w_stab")) | {w for w, _ in seen})
    th_axis = sorted(set(declared("theta")) | {t for _, t in seen})

    horizon = _horizon(an)
    note_idx: dict[str, int] = {}
    note_cells: dict[str, list[list[float]]] = {}
    cells: list[dict[str, Any]] = []
    for w in w_axis:
        for th in th_axis:
            rec = seen.get((w, th))
            if rec is None:
                out["missing"].append({"where": f"sensitivity.grid[w_stab={w:g}, theta={th:g}]",
                                       "fields": ["<cell absent from grid>"]})
                cells.append({"w_stab": w, "theta": th, "has_cell": False, "note": None,
                              "note_index": None, "by_level": {}})
                continue
            note = rec["note"]
            # §2.3 #7: W_stab > horizon yacheykasi `note` bilan belgilanishi SHART.
            # Analiz belgilamagan bo'lsa -- figura buni tuzatmaydi, SATH qiladi.
            if horizon["seconds"] is not None and w > horizon["seconds"] and note is None:
                out["problems"].append(
                    f"W_stab={w:g} s > T_trial={horizon['seconds']:g} s but cell "
                    f"(theta={th:g}) carries no note (§2.3 #7)")
            if note is not None:
                note_idx.setdefault(note, len(note_idx) + 1)
                note_cells.setdefault(note, []).append([w, th])
            by_level = {}
            for lv in levels:
                v = rec["by"].get(lv)
                if v is None or v["p_vr"] is None:
                    out["missing"].append({
                        "where": f"sensitivity.grid[w_stab={w:g}, theta={th:g}].p_vr_by_level[{lv}]",
                        "fields": ["p_vr"]})
                by_level[lv] = v if v is not None else {"p_vr": None, "k": None, "n": None}
            cells.append({"w_stab": w, "theta": th, "has_cell": True, "note": note,
                          "note_index": note_idx.get(note) if note is not None else None,
                          "by_level": by_level})

    notes_list = [{"index": i, "text": t, "cells": note_cells[t]}
                  for t, i in sorted(note_idx.items(), key=lambda kv: kv[1])]
    out["data"] = {
        "w_stab_s": w_axis, "theta": th_axis, "levels": levels, "cells": cells,
        "cell_notes": notes_list,
        "pilot": {"w_stab": PILOT_W_STAB_S, "theta": PRIMARY_THETA,
                  "in_grid": (PILOT_W_STAB_S, PRIMARY_THETA) in seen},
        "horizon": horizon,
    }
    out["text_main"].append(
        f"{_horizon_text(horizon)}: a cell with W_stab > horizon cannot be verified and is "
        "flagged by the analysis note [n] (drawn as n/a, never as 0 or interpolated)")
    if horizon["seconds"] is None:
        out["missing"].append({"where": "analysis.json", "fields": ["t_trial_us"]})
    for n in notes_list:
        where = ", ".join(f"W_stab={w:g} s/theta={t:g}" for w, t in n["cells"])
        out["notes"].append(f"[{n['index']}] cell note ({where}): {n['text']}")
    if out["data"]["pilot"]["in_grid"]:
        out["text_main"].append(
            "bold border: pre-registered pilot parameters W_stab = 8 s, theta = 0.8 (§4)")
    return out


def _prep_exclusion_breakdown(an: dict) -> dict[str, Any]:
    """§12: disposition bo'yicha trial'lar va eksklyuziya ulushi -- NATIJA sifatida."""
    n_tr, exc = an.get("n_trials"), an.get("exclusions")
    by_disp = _get(n_tr, "by_disposition")
    if not isinstance(n_tr, dict) or not isinstance(by_disp, dict):
        return _placeholder("analysis.json has no n_trials.by_disposition (§2.2)")

    out = _empty_prep()
    total = _int(n_tr.get("total"))
    counts = {str(k): _int(v) for k, v in by_disp.items()}
    known_sum = sum(v for v in counts.values() if v is not None)
    accounted = total is not None and all(v is not None for v in counts.values()) \
        and known_sum == total
    if total is None:
        out["missing"].append({"where": "n_trials", "fields": ["total"]})
    elif not accounted:
        out["problems"].append(
            f"n_trials.by_disposition sums to {known_sum} but n_trials.total = {total}: "
            "dispositions absent from by_disposition are drawn as missing, not as 0")
    rows = []
    for d in list(DISPOSITIONS) + sorted(set(counts) - set(DISPOSITIONS)):
        in_enum = d in DISPOSITIONS
        if d in counts:
            c = counts[d]
            if c is None:
                out["missing"].append({"where": f"n_trials.by_disposition[{d}]",
                                       "fields": ["count (not a non-negative integer)"]})
        elif accounted:
            c = 0     # total to'liq hisoblangan: yo'q kalit = mantiqiy nol (taxmin emas)
        else:
            c = None
            out["missing"].append({"where": f"n_trials.by_disposition[{d}]",
                                   "fields": ["<key absent>"]})
        if not in_enum:
            out["problems"].append(f"disposition '{d}' is not in the closed §12 enum")
        rows.append({"disposition": d, "count": c, "in_enum": in_enum,
                     "excluded_from_primary": d in EXCLUDED_FROM_PRIMARY,
                     "absent_key_inferred_zero": d not in counts and c == 0})

    rate = _num(_get(exc, "rate"))
    if not isinstance(exc, dict) or rate is None:
        out["missing"].append({"where": "exclusions", "fields": ["rate"]})
    elif not 0.0 <= rate <= 1.0:
        out["problems"].append(f"exclusions.rate={rate:g} is outside [0, 1]")
    br_raw = _get(exc, "by_reason")
    by_reason = []
    if isinstance(br_raw, dict):
        for r in sorted(br_raw):
            v = _num(br_raw[r])
            by_reason.append({"reason": str(r), "value": v})
            if v is None:
                out["missing"].append({"where": f"exclusions.by_reason[{r}]", "fields": ["value"]})
    else:
        out["missing"].append({"where": "exclusions", "fields": ["by_reason"]})
    if rate is not None and rate > 0 and isinstance(br_raw, dict) and not br_raw:
        out["problems"].append("exclusions.rate > 0 but exclusions.by_reason is empty")

    out["data"] = {
        "total": total, "sum_of_listed_counts": known_sum,
        "sum_matches_total": accounted, "by_disposition": rows,
        "exclusion_rate": rate, "by_reason": by_reason,
        "by_reason_provided": isinstance(br_raw, dict),
    }
    pct = "missing" if rate is None else f"{rate * 100:.1f}%"
    out["text_main"].append(
        f"exclusion rate: {pct} (reported as a result, §12); hatched = excluded from the "
        "primary analysis (contaminated, aborted_guard)")
    return out


def _prep_probe_cost(an: dict) -> dict[str, Any]:
    """§8.2: prober CPU narxi, arm bo'yicha, yadro foizida; budjet chizig'i bilan."""
    pc = an.get("probe_cost")
    by_arm = _get(pc, "by_arm")
    if not isinstance(pc, dict) or not isinstance(by_arm, dict) or not by_arm:
        return _placeholder(
            "analysis.json has no 'probe_cost.by_arm' section: §2.2 does not define it, "
            "so the prober CPU cost (§8.2) cannot be drawn")

    out = _empty_prep()
    budget = _num(pc.get("budget_percent"))
    budget_src = "analysis.json"
    if budget is None:
        budget, budget_src = PROBE_COST_BUDGET_PERCENT, "§8.2 frozen value (not in analysis.json)"
    arms = []
    for arm in sorted(by_arm):
        a = by_arm[arm]
        vals = _get(a, "core_percent")
        if isinstance(vals, (int, float)) and not isinstance(vals, bool):
            vals = [vals]
        vals = _numlist(vals)
        if vals is None:
            out["missing"].append({"where": f"probe_cost.by_arm[{arm}]",
                                   "fields": ["core_percent"]})
            arms.append({"arm": str(arm), "values": None, "n_total": None,
                         "n_unmeasured": None, "n_over_budget": None})
            continue
        measured = [v for v in vals if v is not None]
        n_un = len(vals) - len(measured)
        if n_un:
            out["missing"].append({"where": f"probe_cost.by_arm[{arm}].core_percent",
                                   "fields": [f"{n_un} unmeasured value(s)"]})
        arms.append({"arm": str(arm), "values": vals, "n_total": len(vals),
                     "n_unmeasured": n_un,
                     "n_over_budget": sum(1 for v in measured if v > budget)})
    if all(a["values"] is None or not any(v is not None for v in a["values"]) for a in arms):
        return dict(_placeholder("probe_cost.by_arm carries no measured core_percent values"),
                    missing=out["missing"])
    out["data"] = {"budget_percent": budget, "budget_source": budget_src,
                   "unit": "percent of one CPU core", "arms": arms}
    out["text_main"].append(
        f"budget: {budget:g}% of one core ({budget_src}); above it the prober is slowed down "
        "and the cost must be equal across arms (§8.2)")
    return out


_PREPARE: dict[str, Callable[[dict], dict[str, Any]]] = {
    "p_vr_vs_pressure": _prep_p_vr_vs_pressure,
    "km_time_to_vr": _prep_km_time_to_vr,
    "downtime_ecdf": _prep_downtime_ecdf,
    "sensitivity_heatmap": _prep_sensitivity_heatmap,
    "exclusion_breakdown": _prep_exclusion_breakdown,
    "probe_cost": _prep_probe_cost,
}

_TITLES = {
    "p_vr_vs_pressure": ("P(VR) versus pressure level",
                         "dose-response, per-level proportion with exact CI"),
    "km_time_to_vr": ("Kaplan-Meier time to verified recovery",
                      "S(t) = P(not yet verified-recovered at t), per arm; censored trials included"),
    "downtime_ecdf": ("Downtime: D_sd, D_probe, D_eff",
                      "all three nested measures (§6.1); BCa CI on median, p90, p99"),
    "sensitivity_heatmap": ("Sensitivity sweep: P(VR) over W_stab x theta",
                            "pre-registered grid (§4); one panel per pressure level"),
    "exclusion_breakdown": ("Trial dispositions and exclusions",
                            "closed enum (§12); the exclusion rate is itself a result"),
    "probe_cost": ("Prober CPU cost per arm",
                   "one point per trial, % of one core, against the §8.2 budget"),
}


# =============================================================================
# 2. ASSEMBLE: sidecar (model) = data + ko'rinadigan matn
# =============================================================================


def _short_hash(h: Any) -> str:
    return h[:12] + "…" if isinstance(h, str) and len(h) > 12 else (h or "not provided")


def _assemble(name: str, prep: dict[str, Any], an: dict, analysis_sha256: str) -> dict[str, Any]:
    warn = _warnings_for(an, name)
    status = "placeholder" if prep["placeholder"] else (
        "partial" if (prep["missing"] or prep["problems"]) else "ok")
    small: list[str] = []
    for n in prep["notes"]:
        small.append(f"NOTE: {n}")
    for p in prep["problems"]:
        small.append(f"DATA PROBLEM: {p}")
    if prep["missing"]:
        shown = prep["missing"][:_MISSING_LINES_MAX]
        flat = "; ".join(f"{m['where']}: {', '.join(m['fields'])}" for m in shown)
        more = len(prep["missing"]) - len(shown)
        tail = f"; ... and {more} more (full list: sidecar 'missing')" if more > 0 else ""
        small.append(f"MISSING {len(prep['missing'])} (drawn as missing, never interpolated): "
                     f"{flat}{tail}")
    if warn["total"]:
        small.append(f"analysis.json warnings: {warn['total']} in total, "
                     f"{len(warn['relevant'])} relevant to this figure")
    for w in warn["relevant"]:
        small.append(f"WARNING: {w}")
    small.append(
        f"source: {ANALYSIS_FILENAME} sha256 {_short_hash(analysis_sha256)}   "
        f"analysis_version = {an.get('analysis_version')}   "
        f"preregistration_sha256 = {_short_hash(an.get('preregistration_sha256'))}   "
        f"figure = {name} (figures.py v{FIGURES_VERSION})")

    model: dict[str, Any] = {
        "figure": name,
        "figures_version": FIGURES_VERSION,
        "contract": CONTRACT,
        "source": {
            "file": ANALYSIS_FILENAME,
            "sha256": analysis_sha256,
            "schema_version": an.get("schema_version"),
            "analysis_version": an.get("analysis_version"),
            "preregistration_sha256": an.get("preregistration_sha256")
            if isinstance(an.get("preregistration_sha256"), str) else None,
            "generated_mono_us": _int(an.get("generated_mono_us")),
        },
        "status": status,
        "placeholder_reason": prep["placeholder"],
        "title": _TITLES[name][0],
        "subtitle": _TITLES[name][1],
        "data": prep["data"],
        "missing": prep["missing"],
        "notes": prep["notes"],
        "problems": prep["problems"],
        "analysis_warnings": {"total": warn["total"], "relevant": warn["relevant"]},
        "text": {"main": prep["text_main"], "small": small},
    }
    if "recovered_within_horizon" in prep["extra"]:
        model["recovered_within_horizon"] = prep["extra"]["recovered_within_horizon"]
    return model


# =============================================================================
# 3. DRAW: faqat model'dan. `analysis.json` bu yerda ko'rinmaydi (2-qoida).
# =============================================================================


def _load_matplotlib():
    """matplotlib'ni dangasa import qiladi; `Agg` ANIQ o'rnatiladi (8-qoida)."""
    try:
        import matplotlib
        matplotlib.use("Agg", force=True)
        from matplotlib import rc_context
        from matplotlib.colors import Normalize, LinearSegmentedColormap
        from matplotlib.figure import Figure
        from matplotlib.lines import Line2D
        from matplotlib.patches import Rectangle
        from matplotlib.cm import ScalarMappable
    except ImportError as exc:   # stub/vendor QILINMAYDI
        raise FiguresDependencyError(
            f"matplotlib kerak (§3 allaqachon talab qiladi), import bo'lmadi: {exc}") from exc
    return {"rc_context": rc_context, "Figure": Figure, "Line2D": Line2D,
            "Rectangle": Rectangle, "Normalize": Normalize, "ScalarMappable": ScalarMappable,
            "LinearSegmentedColormap": LinearSegmentedColormap}


def _wrap(lines: list[str], fs: float, width_in: float) -> list[str]:
    cpl = max(40, int((width_in - 2 * _MARGIN_IN) * 72 / (fs * _TEXT_WRAP_FACTOR)))
    out: list[str] = []
    for ln in lines:
        out.extend(textwrap.wrap(ln, width=cpl, subsequent_indent="    ",
                                 break_long_words=False, break_on_hyphens=False) or [""])
    return out


def _new_figure(mpl: dict, model: dict, width_in: float, axes_h_in: float):
    """Figura + matn bloklari; (fig, gridspec chegaralari) qaytaradi.

    Matn bloklari (main, small) o'qdan PASTDA joylashadi va soni o'zgaruvchan,
    shuning uchun figura balandligi ularga moslab hisoblanadi -- matn o'qni
    yoki ma'lumotni yopib qo'ymasligi uchun.
    """
    main = _wrap(model["text"]["main"], FS_MAIN, width_in)
    small = _wrap(model["text"]["small"], FS_SMALL, width_in)
    line = lambda fs: fs * 1.32 / 72.0   # noqa: E731
    text_h = 0.08 + sum(line(FS_SMALL) for _ in small) + (0.05 if main else 0.0) \
        + sum(line(FS_MAIN) for _ in main)
    fig_h = _TOP_IN + axes_h_in + _XAXIS_IN + text_h
    fig = mpl["Figure"](figsize=(width_in, fig_h), facecolor="white")
    x = _MARGIN_IN / width_in
    y = 0.08
    for ln in reversed(small):
        fig.text(x, y / fig_h, ln, fontsize=FS_SMALL, va="bottom", ha="left", color="black")
        y += line(FS_SMALL)
    y += 0.05 if main else 0.0
    for ln in reversed(main):
        fig.text(x, y / fig_h, ln, fontsize=FS_MAIN, va="bottom", ha="left", color="black")
        y += line(FS_MAIN)
    fig.text(x, 1 - 0.10 / fig_h, model["title"], fontsize=FS_TITLE, fontweight="bold",
             va="top", ha="left", color="black")
    fig.text(x, 1 - 0.34 / fig_h, model["subtitle"], fontsize=FS_SUB, va="top", ha="left",
             color="0.25")
    box = {"left": _LEFT_IN / width_in, "right": 1 - _RIGHT_IN / width_in,
           "bottom": (y + _XAXIS_IN) / fig_h, "top": 1 - _TOP_IN / fig_h}
    return fig, box


def _style_axes(ax) -> None:
    ax.tick_params(direction="out", length=3, width=0.8, color="black")


def _to_svg(fig, model: dict) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="svg", metadata={
        "Date": None, "Creator": f"revix.figures v{FIGURES_VERSION}",
        "Title": f"{model['figure']}: {model['title']}"})
    return buf.getvalue().decode("utf-8")


def _draw_placeholder(mpl: dict, model: dict) -> str:
    """Ma'lumot yo'q: figura "chizilmadi" deb AYTADI -- bo'sh o'q ko'rsatilmaydi."""
    model = dict(model, text={"main": [], "small": model["text"]["small"]})
    fig, box = _new_figure(mpl, model, 6.6, 1.2)
    ax = fig.add_axes([box["left"], box["bottom"], box["right"] - box["left"],
                       box["top"] - box["bottom"]])
    ax.set_axis_off()
    reason = "\n".join(textwrap.wrap(model.get("placeholder_reason") or "unspecified", 90))
    ax.text(0.5, 0.5, f"NOT DRAWN: no data in analysis.json\n{reason}", ha="center",
            va="center", fontsize=8.5, color="black", transform=ax.transAxes,
            bbox={"boxstyle": "square,pad=0.6", "fc": "white", "ec": "0.3", "ls": "--", "lw": 0.9})
    return _to_svg(fig, model)


def _draw_p_vr_vs_pressure(mpl: dict, model: dict) -> str:
    d = model["data"]
    cells = d["cells"]
    fig, box = _new_figure(mpl, model, 6.6, 2.9)
    ax = fig.add_subplot(1, 1, 1)
    fig.subplots_adjust(**box)
    _style_axes(ax)
    n = len(cells)
    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(0.0, 1.06)
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_ylabel("P(VR)  [proportion verified-recovered]")
    ax.set_xlabel("pressure level (ordered; spacing is not to scale)")
    ax.set_xticks([c["x"] for c in cells])
    ax.set_xticklabels([c["level"] if c["point_drawn"] else f"{c['level']}\n(missing)"
                        for c in cells])
    # Nuqtalarni faqat BEVOSITA qo'shni, mavjud nuqtalar orasida ulaydi: yo'q
    # qiymat orqali chiziq tortish = interpolyatsiya (4-qoida).
    run: list[dict] = []
    runs: list[list[dict]] = []
    for c in cells:
        if c["point_drawn"]:
            run.append(c)
        else:
            if run:
                runs.append(run)
            run = []
    if run:
        runs.append(run)
    for r in runs:
        if len(r) > 1:
            ax.plot([c["x"] for c in r], [c["p_hat"] for c in r], ls="-", lw=1.0,
                    color="0.35", zorder=2)
    for c in cells:
        if not c["point_drawn"]:
            ax.text(c["x"], 0.5, "missing", ha="center", va="center", fontsize=8,
                    rotation=90, color="0.25")
            continue
        if c["ci_drawn"]:
            # errorbar(yerr=) EMAS: p_hat CI dan tashqarida bo'lsa (analiz xatosi) u
            # manfiy yerr bilan yiqiladi; biz berilgan chekkalarni AYNAN chizamiz.
            ax.plot([c["x"], c["x"]], [c["ci_lower"], c["ci_upper"]], color="black", lw=1.2,
                    zorder=3)
            for edge in (c["ci_lower"], c["ci_upper"]):
                ax.plot([c["x"] - 0.05, c["x"] + 0.05], [edge, edge], color="black", lw=1.2,
                        zorder=3)
        ax.plot([c["x"]], [c["p_hat"]], marker="o", ms=7, mfc="black", mec="black",
                ls="none", zorder=4)
        kn = f"{c['k']}/{c['n']}" if c["k"] is not None and c["n"] is not None else "k/n missing"
        ax.annotate(kn, (c["x"], c["p_hat"]), xytext=(9, -3), textcoords="offset points",
                    fontsize=7.5, ha="left", va="center", color="black")
    methods = sorted({c["ci_method"] for c in cells if c["ci_method"]})
    lvl = f"{d['ci_level']} " if d["ci_level"] is not None else ""
    ax.text(0.99, 0.02, f"whiskers: {lvl}CI ({', '.join(methods) if methods else 'method not provided'})",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=6.5, color="0.25")
    return _to_svg(fig, model)


def _draw_km_time_to_vr(mpl: dict, model: dict) -> str:
    d = model["data"]
    fig, box = _new_figure(mpl, model, 6.8, 3.2)
    ax = fig.add_subplot(1, 1, 1)
    fig.subplots_adjust(**box)
    _style_axes(ax)
    xmax = 0.0
    handles = []
    for i, a in enumerate(d["arms"]):
        st = _SERIES_STYLES[i % len(_SERIES_STYLES)]
        if not a["drawn"]:
            handles.append(mpl["Line2D"]([], [], ls="none", marker=st["marker"], mfc="none",
                                         mec="0.6", color="0.6",
                                         label=f"{a['arm']}  (missing: {a['reason']})"))
            continue
        xs, ys = a["drawn_x"], a["drawn_y"]
        xmax = max(xmax, xs[-1])
        ax.step(xs, ys, where="post", color=st["color"], ls=st["ls"], lw=1.4, zorder=2)
        ax.plot(a["times"], a["survival"], ls="none", marker=st["marker"], ms=4.5,
                mfc=st["mfc"], mec=st["color"], zorder=3)
        handles.append(mpl["Line2D"]([], [], color=st["color"], ls=st["ls"], lw=1.4,
                                     marker=st["marker"], ms=4.5, mfc=st["mfc"],
                                     mec=st["color"], label=a["arm"]))
    hz = d["horizon"]["axis_value"]
    if hz is not None:
        xmax = max(xmax, hz)
        ax.axvline(hz, color="black", ls="--", lw=0.9, zorder=1)
        ax.text(hz, 0.02, " T_trial", ha="right", va="bottom", fontsize=7, rotation=90,
                color="black")
    tau = d["rmst"]["tau"] if d["rmst"] else None
    if tau is not None:
        xmax = max(xmax, tau)
        ax.axvline(tau, color="0.4", ls=":", lw=0.9, zorder=1)
        ax.text(tau, 1.025, "tau", ha="center", va="bottom", fontsize=7, color="0.25")
    ax.set_xlim(0.0, xmax * 1.04 if xmax > 0 else 1.0)
    ax.set_ylim(0.0, 1.06)
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_ylabel("S(t)  [P(not yet verified-recovered)]")
    ax.set_xlabel(f"time to VR ({d['time_unit']['label']})")
    if handles:
        ax.legend(handles=handles, loc="lower left", handlelength=3.2, borderaxespad=0.3)
    return _to_svg(fig, model)


def _draw_downtime_ecdf(mpl: dict, model: dict) -> str:
    d = model["data"]
    fig, box = _new_figure(mpl, model, 6.8, 3.3)
    ax = fig.add_subplot(1, 1, 1)
    fig.subplots_adjust(**box)
    _style_axes(ax)
    handles = []
    xmax = 0.0
    for ms in d["measures"]:
        st = _DOWNTIME_STYLES[ms["measure"]]
        if not ms["has_data"]:
            handles.append(mpl["Line2D"]([], [], ls="none", marker=st["marker"], mfc="none",
                                         mec="0.6", color="0.6",
                                         label=f"{ms['label']}  (missing: not provided)"))
            continue
        if ms["ecdf"] is not None:
            ax.step(ms["ecdf"]["x"], ms["ecdf"]["y"], where="post", color=st["color"],
                    ls=st["ls"], lw=st["lw"], zorder=2)
            xmax = max(xmax, ms["ecdf"]["x"][-1])
        for qname, _prob in DOWNTIME_QUANTILES:
            q = ms["quantiles"][qname]
            if q is None:
                continue
            xmax = max(xmax, q["estimate"], q["ci_upper"] or 0.0)
            if q["ci_lower"] is not None and q["ci_upper"] is not None:
                ax.plot([q["ci_lower"], q["ci_upper"]], [q["prob"], q["prob"]],
                        color=st["color"], ls=st["ls"], lw=1.1, zorder=3)
                for edge in (q["ci_lower"], q["ci_upper"]):
                    ax.plot([edge, edge], [q["prob"] - 0.012, q["prob"] + 0.012],
                            color=st["color"], lw=1.1, zorder=3)
            ax.plot([q["estimate"]], [q["prob"]], ls="none", marker=st["marker"], ms=6,
                    mfc=st["mfc"], mec=st["color"], mew=1.1, zorder=4)
        handles.append(mpl["Line2D"]([], [], color=st["color"], ls=st["ls"], lw=st["lw"],
                                     marker=st["marker"], ms=6, mfc=st["mfc"], mec=st["color"],
                                     label=ms["label"]))
    ax.set_xlim(0.0, xmax * 1.06 if xmax > 0 else 1.0)
    ax.set_ylim(0.0, 1.04)
    ax.set_yticks([0.0, 0.25, 0.5, 0.75, 0.9, 0.99])
    ax.set_yticklabels(["0", "0.25", "0.5", "0.75", "0.9", "0.99"])
    ax.set_ylabel("cumulative probability" + ("" if d["ecdf_available"]
                                              else "  (quantile levels only)"))
    ax.set_xlabel(f"downtime ({d['time_unit']['label']})")
    ax.text(0.99, 0.02, "markers: median / p90 / p99;  bars: BCa CI where provided",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=6.5, color="0.25")
    if handles:
        ax.legend(handles=handles, loc="center right", handlelength=3.2, borderaxespad=0.3,
                  bbox_to_anchor=(1.0, 0.35))
    return _to_svg(fig, model)


def _gray(p: float) -> str:
    """p in [0,1] -> kulrang (0 oq-ga yaqin, 1 to'q): oq-qora chopda ham ajraladi."""
    return str(round(1.0 - 0.78 * min(max(p, 0.0), 1.0), 4))


def _draw_sensitivity_heatmap(mpl: dict, model: dict) -> str:
    d = model["data"]
    levels, ws, ths = d["levels"], d["w_stab_s"], d["theta"]
    npan = len(levels)
    width = max(6.8, 2.5 * npan + 1.4)
    fig, box = _new_figure(mpl, model, width, 0.5 * len(ws) + 1.0)
    box["right"] = 1 - 0.75 / width              # colorbar yorlig'i sig'ishi uchun
    gs = fig.add_gridspec(1, npan + 1, width_ratios=[1.0] * npan + [0.06], wspace=0.30, **box)
    by_key = {(c["w_stab"], c["theta"]): c for c in d["cells"]}
    Rect = mpl["Rectangle"]
    for j, lv in enumerate(levels):
        ax = fig.add_subplot(gs[0, j])
        _style_axes(ax)
        ax.set_xlim(-0.5, len(ths) - 0.5)
        ax.set_ylim(len(ws) - 0.5, -0.5)          # eng kichik W_stab tepada
        ax.set_title(lv, fontsize=8.5, loc="left")
        ax.set_xticks(range(len(ths)))
        ax.set_xticklabels([f"{t:g}" for t in ths])
        ax.set_xlabel("theta  (fraction of R_ref)")
        ax.set_yticks(range(len(ws)))
        ax.set_yticklabels([f"{w:g}" for w in ws] if j == 0 else [])
        if j == 0:
            ax.set_ylabel("W_stab (s)")
        for s in ("left", "bottom"):
            ax.spines[s].set_visible(False)
        for yi, w in enumerate(ws):
            for xi, th in enumerate(ths):
                c = by_key[(w, th)]
                v = c["by_level"].get(lv) if c["has_cell"] else None
                p = v["p_vr"] if v else None
                mark = f" [{c['note_index']}]" if c["note_index"] is not None else ""
                if p is None:
                    ax.add_patch(Rect((xi - 0.5, yi - 0.5), 1, 1, fc="white", ec="0.5", lw=0.6,
                                      hatch="////"))
                    label = ("no cell" if not c["has_cell"] else "n/a") + mark
                    ax.text(xi, yi, label, ha="center", va="center", fontsize=6.5,
                            color="black",
                            bbox={"boxstyle": "square,pad=0.15", "fc": "white", "ec": "none"})
                else:
                    ax.add_patch(Rect((xi - 0.5, yi - 0.5), 1, 1, fc=_gray(p), ec="white",
                                      lw=1.0))
                    kn = f"\n{v['k']}/{v['n']}" if v["k"] is not None and v["n"] is not None else ""
                    ax.text(xi, yi, f"{p:.2f}{mark}{kn}", ha="center", va="center",
                            fontsize=6.5, color="white" if p > 0.55 else "black")
        pil = d["pilot"]
        if pil["w_stab"] in ws and pil["theta"] in ths:
            ax.add_patch(Rect((ths.index(pil["theta"]) - 0.5, ws.index(pil["w_stab"]) - 0.5),
                              1, 1, fill=False, ec="black", lw=2.2, zorder=5))
    cax = fig.add_subplot(gs[0, npan])
    cmap = mpl["LinearSegmentedColormap"].from_list("revix_gray", [_gray(0.0), _gray(1.0)])
    sm = mpl["ScalarMappable"](norm=mpl["Normalize"](0.0, 1.0), cmap=cmap)
    cb = fig.colorbar(sm, cax=cax)
    cb.set_label("P(VR)", fontsize=7.5)
    cb.outline.set_linewidth(0.6)
    cax.tick_params(labelsize=7, length=2)
    return _to_svg(fig, model)


def _draw_exclusion_breakdown(mpl: dict, model: dict) -> str:
    d = model["data"]
    rows, reasons = d["by_disposition"], d["by_reason"]
    nb = max(len(rows), len(reasons), 1)
    fig, box = _new_figure(mpl, model, 7.4, max(2.0, 0.34 * nb + 0.6))
    box["left"] = 1.55 / 7.4                       # uzun disposition nomlari sig'ishi uchun
    gs = fig.add_gridspec(1, 2, width_ratios=[3.0, 2.2], wspace=0.55, **box)
    Rect = mpl["Rectangle"]

    ax = fig.add_subplot(gs[0, 0])
    _style_axes(ax)
    ys = list(range(len(rows)))
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.set_yticks(ys)
    ax.set_yticklabels([r["disposition"] for r in rows])
    top = max([r["count"] for r in rows if r["count"] is not None] + [1])
    ax.set_xlim(0, top * 1.22)
    ax.set_xlabel("number of trials")
    tot = "missing" if d["total"] is None else str(d["total"])
    ax.set_title(f"by disposition (total N = {tot})", fontsize=8.5, loc="left")
    for y, r in zip(ys, rows):
        if r["count"] is None:
            ax.text(top * 0.02, y, "missing", va="center", ha="left", fontsize=7, color="0.25")
            continue
        ax.add_patch(Rect((0, y - 0.32), r["count"], 0.64, fc="0.78" if not r["excluded_from_primary"]
                          else "white", ec="black", lw=0.9,
                          hatch="////" if r["excluded_from_primary"] else None))
        ax.text(r["count"] + top * 0.02, y, str(r["count"]), va="center", ha="left", fontsize=7.5)

    ax2 = fig.add_subplot(gs[0, 1])
    _style_axes(ax2)
    ax2.set_title("exclusions by reason", fontsize=8.5, loc="left")
    if not reasons:
        ax2.set_axis_off()
        why = "by_reason is empty" if d["by_reason_provided"] else "by_reason: missing"
        ax2.text(0.0, 0.5, why, transform=ax2.transAxes, fontsize=7.5, va="center", ha="left",
                 color="0.25")
    else:
        ax2.set_ylim(len(reasons) - 0.5, -0.5)
        ax2.set_yticks(range(len(reasons)))
        ax2.set_yticklabels([r["reason"] for r in reasons])
        topr = max([r["value"] for r in reasons if r["value"] is not None] + [1e-9])
        ax2.set_xlim(0, topr * 1.25)
        ax2.set_xlabel("value as given in analysis.json")
        for y, r in enumerate(reasons):
            if r["value"] is None:
                ax2.text(topr * 0.02, y, "missing", va="center", ha="left", fontsize=7,
                         color="0.25")
                continue
            ax2.add_patch(Rect((0, y - 0.32), r["value"], 0.64, fc="0.78", ec="black", lw=0.9))
            ax2.text(r["value"] + topr * 0.02, y, f"{r['value']:g}", va="center", ha="left",
                     fontsize=7.5)
    return _to_svg(fig, model)


def _draw_probe_cost(mpl: dict, model: dict) -> str:
    d = model["data"]
    arms = d["arms"]
    fig, box = _new_figure(mpl, model, max(6.0, 1.2 * len(arms) + 3.0), 2.9)
    ax = fig.add_subplot(1, 1, 1)
    fig.subplots_adjust(**box)
    _style_axes(ax)
    budget = d["budget_percent"]
    allv = [v for a in arms if a["values"] for v in a["values"] if v is not None]
    ymax = max([budget * 1.3] + [v * 1.12 for v in allv])
    ax.set_xlim(-0.6, len(arms) - 0.4)
    ax.set_ylim(0.0, ymax)
    ax.axhline(budget, color="black", ls="--", lw=1.0, zorder=1)
    ax.text(len(arms) - 0.42, budget, f"budget {budget:g}% ", ha="right", va="bottom",
            fontsize=6.5, color="black", clip_on=False)
    ax.set_ylabel("prober CPU  (% of one core)")
    ax.set_xlabel("arm")
    labels = []
    for i, a in enumerate(arms):
        if a["values"] is None:
            labels.append(f"{a['arm']}\n(missing)")
            continue
        meas = [v for v in a["values"] if v is not None]
        for k, v in enumerate(a["values"]):
            if v is None:
                continue
            # Faqat arm o'qi bo'ylab deterministik siljish (y qiymat o'zgarmaydi).
            x = i + ((k % 9) - 4) * 0.05
            over = v > budget
            ax.plot([x], [v], ls="none", marker="X" if over else "o", ms=5.5 if over else 5,
                    mfc="black" if over else "white", mec="black", mew=0.9, zorder=3)
        extra = f", {a['n_unmeasured']} unmeasured" if a["n_unmeasured"] else ""
        labels.append(f"{a['arm']}\nover budget {a['n_over_budget']}/{len(meas)}{extra}")
    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels(labels)
    ax.legend(handles=[
        mpl["Line2D"]([], [], ls="none", marker="o", mfc="white", mec="black", label="within budget"),
        mpl["Line2D"]([], [], ls="none", marker="X", mfc="black", mec="black", label="over budget"),
    ], loc="lower right", borderaxespad=0.3)
    return _to_svg(fig, model)


_DRAW: dict[str, Callable[[dict, dict], str]] = {
    "p_vr_vs_pressure": _draw_p_vr_vs_pressure,
    "km_time_to_vr": _draw_km_time_to_vr,
    "downtime_ecdf": _draw_downtime_ecdf,
    "sensitivity_heatmap": _draw_sensitivity_heatmap,
    "exclusion_breakdown": _draw_exclusion_breakdown,
    "probe_cost": _draw_probe_cost,
}


# --- ommaviy API -------------------------------------------------------------


def build_figure(name: str, analysis: dict[str, Any],
                 analysis_sha256: str) -> tuple[str, dict[str, Any]]:
    """Bitta figura: (svg matni, sidecar model). Fayl yozmaydi."""
    if name not in _PREPARE:
        raise ValueError(f"noma'lum figura: {name!r}; mavjud: {', '.join(FIGURE_NAMES)}")
    mpl = _load_matplotlib()
    model = _assemble(name, _PREPARE[name](analysis), analysis, analysis_sha256)
    with mpl["rc_context"](_RC):
        svg = (_draw_placeholder if model["status"] == "placeholder" else _DRAW[name])(mpl, model)
    return svg, model


def _write_atomic(path: str, text: str) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


def sidecar_text(model: dict[str, Any]) -> str:
    # allow_nan=False: _num() nan/inf ni allaqachon None qilgan; bu -- kafolat.
    return json.dumps(model, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def render_figures(analysis: dict[str, Any], analysis_sha256: str, out_dir: str,
                   only: list[str] | None = None) -> list[dict[str, Any]]:
    """`<out_dir>/figures/<nom>.{svg,json}` ni yozadi; har figura uchun xulosa qaytaradi.

    Figuralar qayta yaratiladi (derived ma'lumot -- `datasets/` append-only qoidasi
    xom ma'lumotga tegishli). Bitta figura chizilmasa qolganlari davom etadi, xato
    `status="error"` bilan QAYD etiladi (jim tushmaydi).
    """
    names = [n for n in FIGURE_NAMES if only is None or n in only]
    fig_dir = os.path.join(out_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)
    results: list[dict[str, Any]] = []
    for name in names:
        svg_path = os.path.join(fig_dir, f"{name}.svg")
        json_path = os.path.join(fig_dir, f"{name}.json")
        try:
            svg, model = build_figure(name, analysis, analysis_sha256)
            # Avval sidecar, keyin SVG: SVG bor bo'lsa sidecar ham albatta bor.
            _write_atomic(json_path, sidecar_text(model))
            _write_atomic(svg_path, svg)
        except FiguresDependencyError:
            raise
        except Exception as exc:   # noqa: BLE001 -- har xato figura bo'yicha qayd etiladi
            results.append({"name": name, "status": "error", "error": repr(exc),
                            "svg": None, "json": None, "reason": None,
                            "n_missing": None, "n_problems": None})
            continue
        results.append({"name": name, "status": model["status"], "svg": svg_path,
                        "json": json_path, "error": None,
                        "reason": model["placeholder_reason"],
                        "n_missing": len(model["missing"]),
                        "n_problems": len(model["problems"])})
    return results


# --- CLI ---------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="revix figures",
        description="REVIX figuralari: analysis.json -> figures/<nom>.svg + <nom>.json "
                    "(docs/architecture/04-driver-va-analiz-shartnomasi.md §3)")
    ap.add_argument("--analysis", required=True, metavar="PATH",
                    help=f"{ANALYSIS_FILENAME} (yagona kirish; xom ma'lumot rad etiladi)")
    ap.add_argument("--out-dir", required=True, metavar="DIR",
                    help="chiqish katalogi; figures/ shu ostida yaratiladi")
    ap.add_argument("--only", action="append", choices=FIGURE_NAMES, metavar="NAME",
                    help="faqat shu figurani chizadi; takrorlanadi. Mavjud: "
                         + ", ".join(FIGURE_NAMES))
    ap.add_argument("--json", action="store_true",
                    help="xulosani stdout'ga JSON qilib yozadi")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        analysis, sha = load_analysis(args.analysis)
        results = render_figures(analysis, sha, args.out_dir, args.only)
    except (FiguresInputError, FiguresDependencyError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    summary = {
        "analysis_sha256": sha,
        "analysis_version": analysis.get("analysis_version"),
        "out_dir": os.path.join(args.out_dir, "figures"),
        "analysis_warnings_total": len(analysis["warnings"])
        if isinstance(analysis.get("warnings"), list) else 0,
        "figures": results,
    }
    for r in results:
        if r["status"] == "placeholder":
            print(f"WARN: {r['name']}: chizilmadi (placeholder) -- {r['reason']}", file=sys.stderr)
        elif r["status"] == "error":
            print(f"FAIL: {r['name']}: {r['error']}", file=sys.stderr)
    if args.json:
        json.dump(summary, sys.stdout, indent=2, sort_keys=True, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        by = {s: sum(1 for r in results if r["status"] == s)
              for s in ("ok", "partial", "placeholder", "error")}
        print(f"figuralar: {len(results)}  ok: {by['ok']}  partial: {by['partial']}  "
              f"placeholder: {by['placeholder']}  xato: {by['error']}")
        for r in results:
            print(f"  {r['name']}: {r['status']}"
                  + (f"  (missing: {r['n_missing']}, problems: {r['n_problems']})"
                     if r["status"] in ("ok", "partial") else ""))
        print(f"  katalog: {summary['out_dir']}")
    return 1 if any(r["status"] == "error" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
