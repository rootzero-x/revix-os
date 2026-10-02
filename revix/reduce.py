"""REVIX offline reducer -- xom record'lardan derived metrikalar.

PREREGISTRATION.md ni amalga oshiradi:
  * §1  -- barcha davomiylik CLOCK_MONOTONIC mikrosekundda
  * §4  -- Verified Recovery (VR), yettita band, yopiq invalidator enum,
           sensitivity sweep
  * §5  -- FR-A (birlamchi, oracle-free) va FR-B (ikkilamchi, matritsaga nisbatan)
  * §6  -- uchta downtime o'lchovi, right censoring, latency qoidalari
  * §12 -- trial disposition yopiq enum
  * §16 -- analiz to'plami `(disposition, disposition_source)` jufti bilan
           aniqlanadi (§16.2(B)), va eksklyuziya darajasi QAYSI to'plam
           ustida hisoblanganini nomlaydi (§16.4)
  * §17 -- §4 verifikatsiya oynasi pressure hold ICHIDA bo'lishi shart;
           oyna chiqib ketgan trial §4 ning kattaligini O'LCHAMAGAN
           (§17.4): ikki yangi `disposition_source` qiymati

QAT'IY QOIDALAR (buzilmaydi):

  1. **OFFLINE va PUR.** Bu modul o'lchanayotgan tizimga TEGMAYDI: `cgroup`,
     `psi_sampler`, socket, `/proc`, `/sys` -- hech biri import qilinmaydi va
     o'qilmaydi. Faqat fayldan o'qiydi, faylga yozadi.
  2. **DETERMINISTIK.** Bir xil xom kirish -> bir xil derived payload. Derived
     record'ning envelope'idagi `mono_us`/`real_us` -- reduksiya vaqti, O'LCHOV
     EMAS. Barcha o'lchov qiymatlari alohida, nomlangan field'larda.
  3. **XOM FAYL HECH QACHON TAHRIRLANMAYDI.** Derived ma'lumot qayta yaratiladi,
     xom -- yo'q. `reduce_run()` chiqish yo'llari kirish yo'llari bilan bir xil
     bo'lsa ishlamaydi (`ReductionError`).
  4. **TRIAL TASHLANMAYDI.** Har `trial_begin` uchun AYNAN bitta derived
     `trial_metrics` record chiqadi. Recovery bo'lmagan trial'larni tashlash --
     klassik yashirin bias (§6.2), shuning uchun u strukturaviy jihatdan
     imkonsiz: `reduce_run()` kirish va chiqish sonini tekshiradi, eksklyuziya
     esa faqat NOMLANGAN selektorlar (`select_primary`, `select_survival`)
     orqali va `(disposition, disposition_source)` jufti qayd etilgan holda
     bo'ladi (§16.2(B)). Selektor QAYSI trial'ni qaytarishini o'zgartiradi,
     record SONINI hech qachon o'zgartirmaydi.
  5. **PSI hech qanday ta'rifga kirmaydi** (§5 sirkulyarlik kafolati). Bu modul
     PSI qiymatlarini O'QIMAYDI ham: VR, FR va downtime ta'riflari PSI'ga
     bog'liq bo'lsa, "PSI gating FR ni kamaytiradi" tavtologiyaga aylanadi.
     PSI faqat prediktor/kovariata -- u tahlil bosqichida, ALOHIDA qo'shiladi.
  6. **Throughput bandi (§4.5) o'lchanmasa, VR TASDIQLANMAYDI.** Throughput
     bandi VR ni process-liveness'dan ajratadigan yagona narsa. Shuning uchun
     `R_ref` yoki oyna throughput'i o'lchanmasa natija `vr=True` emas,
     `vr=None` (aniqlanmagan) bo'ladi. Aks holda ma'lumot yetishmovchiligi
     jimgina liveness-only VR ga qulardi.
  7. **ANALIZ TO'PLAMI RUXSAT-RO'YXATI BILAN, RAD-RO'YXATI BILAN EMAS.**
     Maxrajga KIRADIGAN `(disposition, disposition_source)` juftlari
     `PRIMARY_DENOMINATOR_SOURCES` da OCHIQ sanaladi; chiqarilganlar
     ro'yxati YO'Q va bo'lmaydi. Ikki sabab, ikkisi ham strukturaviy:
       (i)  bitta ruxsat-to'plami o'zi bilan ajralib keta OLMAYDI, ikki
            ro'yxat esa keta oladi -- va ajralganda xato jimgina maxrajga
            trial qo'shish tomonga ketardi;
       (ii) kelajakda qo'shilgan har qanday yangi `disposition_source`
            AVTOMATIK ravishda chiqariladi va NOMLANADI, ya'ni u qo'shimcha
            o'zgarishsiz maxrajga TUSHIB KETMAYDI (fail-closed). §17.4 ning
            ikki yangi qiymati aynan shu yo'l bilan to'g'ri ishlandi.
     Shuning uchun `disposition`-ga asoslangan "birlamchi to'plam"
     konstantasi QAYTA TIKLANMAYDI: §16.2(B) dan keyin u ta'rifan yetarli
     emas.

XOM RECORD KONTRAKTI (mahalliy ta'rif -- `revix/schema.py` da record turlari
ta'riflanmagan, faqat envelope va yozuvchilar bor; qarang: modul oxiridagi
`RAW_CONTRACT`). Bu kontrakt markazda yarashtirilishi kerak.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Sequence

from .schema import DISPOSITIONS, SCHEMA_VERSION, Emitter, JsonlWriter

REDUCER_VERSION = 1

# --- muzlatilgan parametrlar (PREREGISTRATION.md §2, §4) ---------------------

P_US = 100_000            # probe davri P = 100 ms (§2)
K_F = 3                   # failure uchun ketma-ket contract buzilishi (§3)
PROBE_GAP_MAX_US = 2 * P_US   # > 2xP => trial censored, failed EMAS (§4)
THETA_DEFAULT = 0.8       # §4 parametrlar jadvali
W_STAB_PILOT_US = 8_000_000    # W_stab_pilot = 8 s (§4, oomd xavfsiz oynasi)
W_STAB_FULL_US = 60_000_000    # W_stab = 60 s (to'liq dizayn)
P_MIN_DEFAULT = 0.7       # Repairs() uchun (§5)

# Oldindan e'lon qilingan sensitivity sweep grid'i (§4).
# "Siz W ni natija chiqishi uchun tanlagansiz" e'tiroziga javob bitta raqam
# emas, butun egri chiziq. Grid XOM probe trace'lardan hisoblanadi --
# eksperiment qayta ishga tushirilMAYDI.
W_STAB_SWEEP_S = (8, 10, 30, 60, 120)
THETA_SWEEP = (0.5, 0.8, 0.95)

# VR invalidator'lari -- YOPIQ enum (§4).
INVALIDATORS = (
    "contract_fail",
    "invocation_changed",
    "nrestarts_changed",
    "oom_kill",
    "throughput_below_theta",
    "guard_fired",
)

# `throughput_below_theta` dan tashqari barcha invalidator'lar MONOTON: bir
# marta ishlagach, keyingi ma'lumot ularni bekor qilmaydi. Shuning uchun oyna
# horizon bilan kesilgan bo'lsa ham ular VR ni QAT'IY false qiladi.
MONOTONE_INVALIDATORS = tuple(i for i in INVALIDATORS if i != "throughput_below_theta")

# probe_sample.outcome -- yopiq enum (docs/architecture/03-sut-protokoli.md §8).
PROBE_OUTCOMES = ("ok", "conn_refused", "conn_timeout", "rt_timeout",
                  "bad_response", "no_progress")
PROBE_OUTCOME_OK = "ok"

# Xom record turlari (mahalliy kontrakt -- yuqoridagi izohni ko'ring).
RT_RUN_META = "run_meta"
RT_TRIAL_BEGIN = "trial_begin"
RT_TRIAL_END = "trial_end"
RT_PROBE = "probe_sample"
RT_ACTION = "action"
RT_ACTOR_SIGNAL = "actor_signal"
RT_UNIT_STATE = "unit_state"
RT_CGROUP_EVENTS = "cgroup_events"
RT_GUARD_EVENT = "guard_event"
RT_FAULT_INJECT = "fault_inject"
RT_FAULT_EFFECTIVE = "fault_effective"
RT_BASELINE_WINDOW = "baseline_window"
RT_ACTION_DEFER = "action_defer"

# Derived record turlari (XOM fayllarga hech qachon yozilmaydi).
DRT_EPISODE = "episode"
DRT_TRIAL = "trial_metrics"
DRT_SWEEP = "sweep_cell"
DRT_SUMMARY = "reduction_summary"

# `disposition_source` -- reducer'ning MAHALLIY yopiq enum'i. §12 ning
# disposition enum'i emas: bu `derive_disposition` yorliqni QAYSI FAKT asosida
# qo'yganini aytadi. Aynan shu beshta qiymat ishlab chiqariladi.
DISPOSITION_SOURCES = (
    "probe_gap",         # §4: probe uzilishi > 2xP -- instrumentatsiya yo'qoldi
    # §17.4(2) -- oyna pressure hold'dan yoki horizon'dan chiqib ketdi, demak
    # §4 ning kattaligi O'LCHANMADI. Bular `disposition_source` qiymatlari,
    # §12 ning `disposition` enum'iga TEGILMAYDI.
    "window_past_pressure",   # holat (a): T_h < t_up + W_stab <= T_trial
    "window_past_horizon",    # holat (b): t_up + W_stab > T_trial
    "down_at_horizon",   # §12: horizon down holatda tugadi -- xizmat qaytmadi
    "guard_event",       # §12: host guard trip qildi
    "trial_end",         # harness'ning o'z `trial_end.disposition` yorlig'i
    "derived",           # hech qanday maxsus fakt yo'q -> `complete`
)

# §17 oyna bo'sh-joy klassifikatsiyasi -- YOPIQ enum.
#
# NEGA (§17.2): §4 ning 1-bandi oynani `t_up` dan boshlaydi, v1.3 ning
# yarashtiruvchi arifmetikasi (`3 + 8 = 11 <= 12`) esa uni `t_inject` dan
# boshlagan, ya'ni jimgina `t_up = t_inject` (nol recovery vaqti) ni nazarda
# tutgan. Haqiqiy shart `t_up + W_stab_pilot <= T_h`, ya'ni `t_start <= 0.8 s`,
# holbuki §9.2 sekin start'ni oldindan MEXANIZM deb e'lon qiladi va
# `driver.py` `TimeoutStartSec = 10 s` ni default qilgan. Shuning uchun oyna
# joylashuvi har trial'da OCHIQ klassifikatsiya qilinadi.
WINDOW_INSIDE_HOLD = "inside_hold"        # holat (c): to'g'ri o'lchov
WINDOW_PAST_PRESSURE = "past_pressure"    # holat (a)
WINDOW_PAST_HORIZON = "past_horizon"      # holat (b)
WINDOW_NO_T_UP = "no_t_up"                # `t_up` yo'q -> oyna boshlanmadi
WINDOW_NOT_EVALUATED = "not_evaluated"    # `T_h` O'LCHANMAGAN -> (a)/(c) ajralmaydi
WINDOW_CONTAINMENTS = (
    WINDOW_INSIDE_HOLD, WINDOW_PAST_PRESSURE, WINDOW_PAST_HORIZON,
    WINDOW_NO_T_UP, WINDOW_NOT_EVALUATED,
)

# §17.4(2): oyna chiqib ketgan holatlar -> `disposition_source` qiymatlari.
WINDOW_CONTAINMENT_SOURCE = {
    WINDOW_PAST_PRESSURE: "window_past_pressure",
    WINDOW_PAST_HORIZON: "window_past_horizon",
}

# --- ikki analiz to'plami: NOMLARI MAJBURIY (§16.4) -------------------------
#
# NEGA (§16.4): §12 eksklyuziya darajasini NATIJA deb e'lon qiladi, va
# ikki xil to'plam ikki xil darajani beradi. §16.4 shuning uchun majburiy
# qoida qo'yadi: "har qanday ... berilgan eksklyuziya darajasi QAYSI to'plam
# ustida hisoblanganini NOMLASHI SHART ... Nomlanmagan eksklyuziya darajasi
# takrorlanuvchi EMAS". Shu sababli to'plam nomlari KONSTANTA -- hisobot
# maydonlari ularni matn sifatida takrorlamaydi.
SET_BINARY_DENOMINATOR = "binary_pvr_denominator"   # §10.1 binar P(VR) maxraji
SET_SURVIVAL = "survival_analysis_set"              # §6.2 KM/log-rank, k/n

# NEGA (§16.2(B)): BIRLAMCHI (binar `P(VR)`) ANALIZ TO'PLAMI `disposition`
# BILAN EMAS, `(disposition, disposition_source)` JUFTI BILAN ANIQLANADI.
#
# §12 ning `censored` yorlig'i ikki epistemologik jihatdan BOSHQA holatni
# bitta nom ostida birlashtiradi, va muzlatilgan matn ularni allaqachon
# boshqacha ishlaydi:
#
#   * `probe_gap`       -> instrumentatsiya yo'qoldi, natija KUZATILMADI.
#     §4: "Probe uzilishi > 2xP -> trial `censored`, `failed` EMAS.
#     Instrumentatsiya yo'qolishi hech qachon jimgina natijaga aylanmaydi."
#     => binar maxrajdan CHIQARILADI, lekin ulushi §12 bo'yicha beriladi.
#   * `down_at_horizon` -> xizmat qaytmadi, natija KUZATILDI: `false`.
#     §4 ning VR ta'rifi horizon bilan chegaralangan: "oynasi MAVJUD
#     BO'LSA". `t_up` paydo bo'lmagan trial uchun oyna mavjud emas, demak
#     `VR = false` -- TO'LIQ ANIQLANGAN, yetishmayotgan kuzatuv emas.
#     => binar maxrajga `VR = false` sifatida KIRADI.
#
# Ikkalasi ham §6.2 bo'yicha KM/log-rank va loop-rate ga censored DAVOMIYLIK
# sifatida kiradi -- §6.2 davomiylikni censor qiladi, binar natijani emas.
# Shuning uchun `SURVIVAL_DISPOSITIONS` va `select_survival` O'ZGARMAYDI.
#
# NEGA JUFT, MAPPING SHAKLIDA (§16.2(B)): jadval har `disposition` uchun
# RUXSAT ETILGAN `disposition_source` to'plamini OCHIQ sanaydi, demak
# (i) qoida call site'da bitta nom bilan o'qiladi
# (`enters_primary_denominator(...)`), (ii) yangi `disposition_source`
# qo'shilsa u avtomatik ravishda maxrajga TUSHMAYDI -- jadvalda yo'q qiymat
# fail-closed tarzda chiqariladi, (iii) §12 ning yopiq enum'iga TEGILMAYDI va
# yangi disposition qiymati YARATILMAYDI.
PRIMARY_DENOMINATOR_SOURCES: dict[str, frozenset[str]] = {
    # To'liq o'lchandi (§12) -- manbasidan qat'i nazar maxrajga kiradi.
    "complete": frozenset({"trial_end", "derived"}),
    # §16.2(B): faqat `down_at_horizon`. `probe_gap` KUZATILMAGAN natija,
    # `trial_end` esa harness `censored` dedi-yu sababini reducer ko'rmadi --
    # ikkisi ham fail-closed chiqariladi.
    #
    # §17.4(3): `window_past_pressure` va `window_past_horizon` HAM
    # chiqariladi -- natija kuzatilmagan, chunki §4 oynaning hold ICHIDA
    # bo'lishini TALAB qiladi ("sustained HOLD (<=12 s) ichida sig'ishi
    # kerak" + "pressure davom etayotganda tasdiqlangan recovery"). Ular bu
    # ruxsat-ro'yxatida YO'Q, demak avtomatik ravishda chiqariladi va
    # sabablari `"censored:window_past_pressure"` /
    # `"censored:window_past_horizon"` bo'lib NOMLANADI.
    #
    # NEGA RUXSAT-RO'YXATI (allow-list), ALOHIDA RAD-RO'YXATI EMAS: ikki
    # ro'yxat bir-biridan ajralib ketishi mumkin, ruxsat-ro'yxati esa
    # fail-closed -- §17 kabi yangi manba qo'shilganda u maxrajga JIMGINA
    # tushmaydi, qo'shimcha o'zgarishsiz chiqariladi. Chiqarilgan juftlarning
    # AYNAN qaysi bo'lishi test bilan qulflangan (butun kesma sanaladi).
    "censored": frozenset({"down_at_horizon"}),
    # §12: ochiq chiqariladi, lekin ulushi natija sifatida beriladi.
    "contaminated": frozenset(),
    "aborted_guard": frozenset(),
    # §12 bularning analiz holatini AYTMAYDI (§16.7-1) -> fail-closed.
    "washout_timeout": frozenset(),
    "harness_error": frozenset(),
}

# OLIB TASHLANDI -- `PRIMARY_DISPOSITIONS == ("complete",)`.
#
# §16.4 uni "to'g'ri savol, NOTO'G'RI javob" deb hukm qilgan edi: binar
# maxraj `complete` VA `down_at_horizon` ni o'z ichiga olishi kerak. U §16.2(B)
# amalga oshirilganda SHIM sifatida saqlangan edi -- qiymati o'zgartirilmagan
# holda, chunki uning YAGONA iste'molchisi (`revix/analyze.py`) boshqa agentga
# tegishli va qiymatni o'zgartirish o'sha modulning xatti-harakatini JIMGINA
# o'zgartirardi, §16.6 esa o'zgarish "ataylab qilingan qaror" bo'lishini
# talab qiladi. Iste'molchi `enters_primary_denominator()` ga ko'chgach,
# shim'ning vazifasi tugadi va u olib tashlandi.
#
# Nomni QAYTA TIKLAMANG: maxraj qoidasi `(disposition, disposition_source)`
# jufti bilan aniqlanadi (§16.2(B)), demak `disposition`-ga asoslangan har
# qanday konstanta ta'rifan yetarli emas.

# Kaplan-Meier / log-rank va loop-rate ga kiradigan disposition (§6.2):
# censored trial'lar KIRADI -- ularni tashlash tez ishdan chiqadigan arm'ni
# chiroyli ko'rsatadigan yashirin bias. §16.4: bu `SET_SURVIVAL` to'plami,
# ya'ni "analiz to'plami butun holda". §16 bu to'plamni O'ZGARTIRMAYDI.
SURVIVAL_DISPOSITIONS = ("complete", "censored")

# --- §20: `vr` ANIQLANGANLIGI -- maxrajning umumiy ta'rifi -------------------
#
# §20.2 ning qoidasi:
#
#   "Binar `P(VR)` maxraji -- §4 ning predikati ANIQLANGAN qiymat (`true`
#    yoki `false`) olgan trial'lar to'plami. `vr = None` -- sababi nima
#    bo'lishidan qat'i nazar -- maxrajdan TASHQARIDA, va sabab nomlanib
#    beriladi."
#
# Bu YANGI qoida emas, UMUMLASHTIRISH: §4 VR ni EPIZOD uchun ta'riflaydi
# ("Epizod `E` verified-recovered, agar ..."), demak epizod bo'lmasa
# predikat INSTANSIYALANMAYDI. §16.2(B) va §17.4 shundan KELIB CHIQADI.
# Yangi `disposition` qiymati KERAK EMAS va §12 ning yopiq enum'iga
# TEGILMAYDI -- qoida allaqachon mavjud `vr` maydoniga tayanadi.
#
# `vr = None` ning kodda NOMLANGAN sabablari (yopiq ro'yxat emas -- u
# `evaluate_vr` ning `reason` qiymatlaridan keladi, shuning uchun hisobot
# ularni sanab beradi, filtrlamaydi):
VR_REASON_NO_EPISODE = "no_episode"                   # §20.3 -- savol TUG'ILMAGAN
VR_REASON_R_REF_UNAVAILABLE = "r_ref_unavailable"     # §20.4 -- 5-band baholanmadi
VR_REASON_THROUGHPUT_UNMEASURABLE = "throughput_unmeasurable"   # §20.4
VR_REASON_WINDOW_TRUNCATED = "window_truncated"       # §17 -- nol bo'lishi SHART

# §20.3: `no_episode` -- v1.5 dan beri IKKALA to'plamdan ham chiqadigan
# BIRINCHI kategoriya, shuning uchun u alohida konstanta bilan nomlanadi.
#
# NEGA BU §6.2 GA ZID EMAS: §6.2 ning qoidasi "RECOVERY BO'LMAGAN
# trial'larni tashlash -- klassik yashirin bias" deydi, ya'ni u recovery
# KUTILAYOTGAN trial'lar haqida. `no_episode` da xizmat ishdan chiqmagan,
# demak hech qanday hodisa kutilayotgan EMAS edi; censored kuzatuv esa
# "hodisa `t` gacha sodir bo'lmadi" degan DA'VO va u hodisaning
# kutilayotgan bo'lishini talab qiladi. Bu yerda u kutilayotgan emas,
# demak censored kuzatuv chiqarish YOLG'ON da'vo bo'lardi. §6.2 ning
# qoidasi bu holatga YETIB BORMAYDI (§20.3).
SURVIVAL_EXCLUDED_VR_REASONS = frozenset({VR_REASON_NO_EPISODE})

# §20.3 / §20.4: IKKI HISOBOT SINFI, va ular BIRLASHTIRILMAYDI.
#
#   * injektor samaradorligi -- `no_episode`. §9.3 har trial'ga AYNAN BITTA
#     injeksiya beradi va P1 ning yagona fault'i `clean_crash`
#     (`exit(1)` / `SIGKILL` / `SIGSEGV`), ularning HAMMASI socket
#     contract'ini buzishi SHART. Demak muzlatilgan dizaynda `no_episode`
#     "injeksiya ISHLAMADI" degan ma'no beradi -- natija emas, TRIAL
#     NUQSONI. Nolga teng bo'lmagan daraja PILOTNI GATE QILADI, chunki
#     §9.2 ning to'rtala mexanizmi ham injeksiyaning ishlashini nazarda
#     tutadi.
#   * instrumentatsiya yo'qolishi -- `probe_gap` (§4) va 5-band
#     o'lchanmagan holatlar (§20.4). Bu yerda savol TUG'ILDI, javob
#     kuzatilmadi.
#
# Ular eksperimentning IKKI BOSHQA nuqson sinfi, shuning uchun bitta
# "eksklyuziya darajasi" ga qo'shib yuborish ma'lumotni YO'QOTADI.
METRIC_INJECTOR_EFFECTIVENESS = "injector_effectiveness"
METRIC_INSTRUMENTATION_LOSS = "instrumentation_loss"
INSTRUMENTATION_LOSS_VR_REASONS = frozenset({
    VR_REASON_R_REF_UNAVAILABLE, VR_REASON_THROUGHPUT_UNMEASURABLE,
})
INSTRUMENTATION_LOSS_SOURCES = frozenset({"probe_gap"})

# `_UNSET` -- "argument berilmadi", `None` dan FARQLI. §20.2 da `vr=None`
# MA'NOLI qiymat ("aniqlanmagan"), shuning uchun "berilmadi" ni `None` bilan
# ifodalash mumkin emas.
_UNSET: Any = object()


class ReductionError(Exception):
    """Reduksiya invarianti buzildi. Jimgina davom etilmaydi."""


# --- parametrlar ------------------------------------------------------------


@dataclass(frozen=True)
class Params:
    """Qayta hisoblanadigan parametrlar (§4).

    `w_stab_us`, `theta`, `p_min` -- pre-registration'da muzlatilgan, lekin
    ARGUMENT sifatida beriladi, chunki §4 sensitivity sweep'ni oldindan e'lon
    qilgan: bir xil xom trace'dan butun grid hisoblanadi.
    """

    w_stab_us: int = W_STAB_PILOT_US
    theta: float = THETA_DEFAULT
    p_min: float = P_MIN_DEFAULT
    probe_period_us: int = P_US
    k_f: int = K_F

    @property
    def probe_gap_max_us(self) -> int:
        return 2 * self.probe_period_us

    @property
    def window_slack_us(self) -> int:
        """Oyna qoplanishi uchun bitta probe davri yo'l qo'yiladi.

        Sabab: §6.1 probe kvantlashini (+-P) OCHIQ e'lon qilgan. Oxirgi probe
        oyna chegarasidan bir davr oldin bo'lsa, oynani "kesilgan" deb
        hisoblash sun'iy natija berardi.
        """
        return self.probe_period_us

    def as_dict(self) -> dict[str, Any]:
        return {
            "w_stab_us": self.w_stab_us,
            "theta": self.theta,
            "p_min": self.p_min,
            "probe_period_us": self.probe_period_us,
            "k_f": self.k_f,
        }


def sweep_grid(
    w_stab_s: Sequence[float] = W_STAB_SWEEP_S,
    thetas: Sequence[float] = THETA_SWEEP,
    base: Params | None = None,
) -> list[Params]:
    """Oldindan e'lon qilingan sweep grid'i (§4): W_stab x theta."""
    base = base or Params()
    out: list[Params] = []
    for w in w_stab_s:
        for th in thetas:
            out.append(Params(w_stab_us=int(round(w * 1_000_000)), theta=th,
                              p_min=base.p_min,
                              probe_period_us=base.probe_period_us,
                              k_f=base.k_f))
    return out


# --- xom ma'lumotni o'qish --------------------------------------------------


@dataclass(frozen=True)
class Probe:
    """Bitta probe namunasi (xom).

    `mono_us` = `mono_us_send` (§3: F_probe timestamp'i birinchi buzilgan
    probe'ning YUBORISH vaqti).
    """

    mono_us: int
    outcome: str
    progress: int | None
    invocation_id: str | None
    seq: int | None = None
    source_index: int | None = None

    @property
    def passed(self) -> bool:
        """Contract'dan o'tdimi (§2: a, b, c -- uchtasi ham).

        Prober uchala bandni `outcome` ga kodlaydi, demak bu yerda `ok`
        aynan "uchala band bajarildi" degani. `no_progress` = (c) buzildi.
        """
        return self.outcome == PROBE_OUTCOME_OK


def _as_int(v: Any) -> int | None:
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    try:
        return int(str(v).strip())
    except ValueError:
        return None


def _as_str(v: Any) -> str | None:
    if v is None or v == "":
        return None
    return str(v)


def load_jsonl(path: str) -> list[dict[str, Any]]:
    """JSONL faylni o'qiydi. Qismli oxirgi qator TASHLANMAYDI, xato qilinadi?

    Yo'q: `JsonlWriter` O_APPEND + line-delimited, demak crash'da faqat oxirgi
    qator qismli bo'lishi mumkin. Uni tashlaymiz LEKIN natijada qayd etamiz --
    jimgina yo'qotish bo'lmaydi (qaytarilgan ro'yxatning oxirida
    `__truncated_line__` marker record).
    """
    out: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines(keepends=True)
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        if not line.endswith("\n") and i == len(lines) - 1:
            # Qismli oxirgi qator: crash izi. Marker qo'yamiz.
            out.append({"record_type": "__truncated_line__", "source": path,
                        "index": i + 1, "raw": s})
            continue
        try:
            rec = json.loads(s)
        except json.JSONDecodeError as exc:
            out.append({"record_type": "__bad_json__", "source": path,
                        "index": i + 1, "error": str(exc), "raw": s})
            continue
        rec.setdefault("__source__", path)
        rec.setdefault("__index__", i + 1)
        out.append(rec)
    return out


PROBE_CSV_FIELDS = (
    "mono_us", "real_us", "seq", "trial_id", "mono_us_send", "mono_us_recv",
    "outcome", "progress", "invocation_id_seen", "pid_seen", "rt_us",
)


def load_probe_csv(path: str) -> list[dict[str, Any]]:
    """probe_sample CSV oqimini o'qiydi (yuqori tezlikli oqim CSV'da -- §8.1)."""
    out: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        for i, row in enumerate(csv.DictReader(fh)):
            rec: dict[str, Any] = dict(row)
            rec["record_type"] = RT_PROBE
            rec["__source__"] = path
            rec["__index__"] = i + 2   # sarlavha qatori 1
            out.append(rec)
    return out


def probe_from_record(rec: dict[str, Any]) -> Probe:
    """Xom record'dan `Probe`. `mono_us_send` afzal (§3)."""
    mono = _as_int(rec.get("mono_us_send"))
    if mono is None:
        mono = _as_int(rec.get("mono_us"))
    if mono is None:
        raise ReductionError(f"probe_sample da mono_us yo'q: {rec!r}")
    outcome = _as_str(rec.get("outcome")) or "bad_response"
    return Probe(
        mono_us=mono,
        outcome=outcome,
        progress=_as_int(rec.get("progress")),
        invocation_id=_as_str(rec.get("invocation_id_seen"))
        or _as_str(rec.get("invocation_id")),
        seq=_as_int(rec.get("seq")),
        source_index=_as_int(rec.get("__index__")),
    )


@dataclass
class RawRun:
    """Bitta run'ning xom record'lari. O'qish uchun, hisob uchun emas."""

    records: list[dict[str, Any]] = field(default_factory=list)
    probes: list[dict[str, Any]] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, jsonl_paths: Iterable[str],
             probe_csv_paths: Iterable[str] = ()) -> "RawRun":
        run = cls()
        for p in jsonl_paths:
            run.sources.append(p)
            for rec in load_jsonl(p):
                if rec.get("record_type") == RT_PROBE:
                    run.probes.append(rec)
                else:
                    run.records.append(rec)
        for p in probe_csv_paths:
            run.sources.append(p)
            run.probes.extend(load_probe_csv(p))
        return run

    def of_type(self, *types: str) -> list[dict[str, Any]]:
        t = set(types)
        return [r for r in self.records if r.get("record_type") in t]

    @property
    def run_meta(self) -> dict[str, Any] | None:
        metas = self.of_type(RT_RUN_META)
        return metas[0] if metas else None


# --- trial ko'rinishi -------------------------------------------------------


@dataclass
class Action:
    """Bitta recovery action (xom `action` record'idan)."""

    mono_us: int
    action_id: str | None
    action_class: str | None
    policy_delay_us: int | None
    deferred: bool
    raw: dict[str, Any]


@dataclass
class Trial:
    """Bitta trial'ning xom ko'rinishi -- derived hisob uchun kirish.

    `end_us` = horizon oxiri (`trial_end.mono_us`). Right censoring AYNAN shu
    nuqtada bo'ladi (§6.2), demak u trashlanmaydigan, majburiy field.
    """

    trial_id: str
    begin: dict[str, Any] | None
    end: dict[str, Any] | None
    probes: list[Probe]
    actions: list[Action]
    actor_signals: list[dict[str, Any]]
    unit_states: list[dict[str, Any]]
    cgroup_events: list[dict[str, Any]]
    guard_events: list[dict[str, Any]]
    fault_injects: list[dict[str, Any]]
    fault_effectives: list[dict[str, Any]]
    baseline_windows: list[dict[str, Any]]
    defers: list[dict[str, Any]]

    @property
    def block_index(self) -> int | None:
        if self.begin is not None:
            return _as_int(self.begin.get("block_index"))
        return None

    @property
    def arm(self) -> str | None:
        return _as_str((self.begin or {}).get("arm"))

    @property
    def pressure_band(self) -> str | None:
        return _as_str((self.begin or {}).get("pressure_band"))

    @property
    def disposition_raw(self) -> str | None:
        return _as_str((self.end or {}).get("disposition"))

    @property
    def start_us(self) -> int | None:
        if self.begin is not None:
            v = _as_int(self.begin.get("mono_us"))
            if v is not None:
                return v
        return self.probes[0].mono_us if self.probes else None

    @property
    def end_us(self) -> int | None:
        if self.end is not None:
            v = _as_int(self.end.get("mono_us"))
            if v is not None:
                return v
        # Horizon record'i yo'q: oxirgi kuzatilgan probe. Bu HOLAT validator
        # tomonidan xato deb belgilanadi (trial_end yo'q), lekin reduksiya
        # to'xtamaydi -- trial tashlanmaydi.
        return self.probes[-1].mono_us if self.probes else None

    @property
    def t_trial_us(self) -> int | None:
        a, b = self.start_us, self.end_us
        if a is None or b is None:
            return None
        return b - a

    @property
    def hold_end_us(self) -> int | None:
        """`T_h` -- pressure hold tugashi (§17.2). O'LCHANMASA `None`.

        Manba: `trial_end.timing.pressure_off_mono_us` (driver TrialTiming).
        `0` -- "hech qachon o'rnatilmagan" (trial erta uzilgan), demak u
        `None` ga aylantiriladi: `0` = "o'lchangan no'l" ma'nosini
        bildirmaydi, chunki bu MONOTONIC timestamp.

        Reducer bu qiymatni TAXMIN QILMAYDI: `TrialTimeline` dan qayta
        hisoblash rejalashtirilgan vaqtni o'lchangan vaqt deb yozish bo'lardi
        (2-qoida: o'lchov qiymatlari faqat o'lchangan joydan keladi).
        """
        timing = (self.end or {}).get("timing")
        if not isinstance(timing, dict):
            return None
        v = _as_int(timing.get("pressure_off_mono_us"))
        return v if v else None

    @property
    def horizon_end_us(self) -> int | None:
        """`T_trial` oxiri (§17.2). `timing` bo'lmasa `end_us` ga tushadi.

        `trial_end.mono_us` driver tomonidan `horizon_end_mono_us` ga
        o'rnatiladi, demak ikkisi mos keladi; `timing` ustun, chunki u
        OCHIQ nomlangan.
        """
        timing = (self.end or {}).get("timing")
        if isinstance(timing, dict):
            v = _as_int(timing.get("horizon_end_mono_us"))
            if v:
                return v
        return self.end_us


def split_trials(run: RawRun) -> list[Trial]:
    """Xom run'ni trial'larga bo'ladi.

    `guard_event` da `trial_id` YO'Q (guard mustaqil jarayon, §8.2), shuning
    uchun guard hodisalari MONOTONIC vaqt bo'yicha trial oynasiga bog'lanadi.
    Bu faqat bitta boot ichida to'g'ri -- shu sababli validator `boot_id`
    doimiyligini talab qiladi (§1).
    """
    begins = {(_as_str(r.get("trial_id")) or ""): r
              for r in run.of_type(RT_TRIAL_BEGIN)}
    ends: dict[str, dict[str, Any]] = {}
    for r in run.of_type(RT_TRIAL_END):
        tid = _as_str(r.get("trial_id")) or ""
        ends.setdefault(tid, r)

    order: list[str] = []
    for r in run.of_type(RT_TRIAL_BEGIN):
        tid = _as_str(r.get("trial_id")) or ""
        if tid not in order:
            order.append(tid)
    # trial_begin'i yo'q, lekin trial_end'i bor trial ham TASHLANMAYDI.
    for tid in ends:
        if tid not in order:
            order.append(tid)

    by_type: dict[str, list[dict[str, Any]]] = {}
    for r in run.records:
        by_type.setdefault(str(r.get("record_type")), []).append(r)

    probes_by_trial: dict[str, list[Probe]] = {}
    for rec in run.probes:
        tid = _as_str(rec.get("trial_id")) or ""
        probes_by_trial.setdefault(tid, []).append(probe_from_record(rec))
    for v in probes_by_trial.values():
        v.sort(key=lambda p: p.mono_us)

    def pick(rt: str, tid: str) -> list[dict[str, Any]]:
        out = [r for r in by_type.get(rt, [])
               if (_as_str(r.get("trial_id")) or "") == tid]
        out.sort(key=lambda r: (_as_int(r.get("mono_us")) or 0))
        return out

    trials: list[Trial] = []
    for tid in order:
        begin = begins.get(tid)
        end = ends.get(tid)
        acts = [
            Action(
                mono_us=_as_int(r.get("mono_us")) or 0,
                action_id=_as_str(r.get("action_id")),
                action_class=_as_str(r.get("action_class")),
                policy_delay_us=_as_int(r.get("policy_delay_us")),
                deferred=bool(r.get("deferred") or r.get("defer")
                              or r.get("action_class") == "defer"),
                raw=r,
            )
            for r in pick(RT_ACTION, tid)
        ]
        acts.sort(key=lambda a: a.mono_us)
        t = Trial(
            trial_id=tid,
            begin=begin,
            end=end,
            probes=probes_by_trial.get(tid, []),
            actions=acts,
            actor_signals=pick(RT_ACTOR_SIGNAL, tid),
            unit_states=pick(RT_UNIT_STATE, tid),
            cgroup_events=pick(RT_CGROUP_EVENTS, tid),
            guard_events=[],
            fault_injects=pick(RT_FAULT_INJECT, tid),
            fault_effectives=pick(RT_FAULT_EFFECTIVE, tid),
            baseline_windows=pick(RT_BASELINE_WINDOW, tid),
            defers=pick(RT_ACTION_DEFER, tid),
        )
        trials.append(t)

    # guard_event'ni vaqt bo'yicha bog'lash.
    guards = sorted(by_type.get(RT_GUARD_EVENT, []),
                    key=lambda r: (_as_int(r.get("mono_us")) or 0))
    for g in guards:
        gtid = _as_str(g.get("trial_id"))
        gt = _as_int(g.get("mono_us"))
        for t in trials:
            if gtid is not None and gtid == t.trial_id:
                t.guard_events.append(g)
                break
            a, b = t.start_us, t.end_us
            if gtid is None and gt is not None and a is not None and b is not None \
                    and a <= gt <= b:
                t.guard_events.append(g)
                break
    return trials


# --- throughput -------------------------------------------------------------


def window_throughput(
    probes: Sequence[Probe], lo_us: int, hi_us: int
) -> tuple[float | None, str, dict[str, Any]]:
    """Oynadagi throughput (iter/s) -- `Delta progress / Delta t`.

    PREREGISTRATION.md §4.5 va docs/architecture/03-sut-protokoli.md §4:
    `progress` har ish tsikli iteratsiyasida aynan 1 ga oshadi va restart'da
    0 dan boshlanadi. Shuning uchun throughput FAQAT bitta invocation ichida
    hisoblanadi -- aks holda restart progress'ni nolga tushirib, soxta manfiy
    tezlik berardi.
    """
    sel = [p for p in probes
           if lo_us <= p.mono_us <= hi_us and p.passed and p.progress is not None]
    if len(sel) < 2:
        return None, "insufficient_probes", {"n": len(sel)}
    inv = sel[-1].invocation_id
    same = [p for p in sel if p.invocation_id == inv]
    if len(same) < 2:
        return None, "insufficient_probes", {"n": len(same), "invocation_id": inv}
    dt = same[-1].mono_us - same[0].mono_us
    if dt <= 0:
        return None, "zero_interval", {"dt_us": dt}
    dprog = same[-1].progress - same[0].progress   # type: ignore[operator]
    if dprog < 0:
        # Bitta invocation ichida progress kamaymaydi (protokol §4.1).
        return None, "progress_regressed", {"d_progress": dprog}
    rate = dprog * 1_000_000.0 / dt
    return rate, "ok", {"dt_us": dt, "d_progress": dprog, "n": len(same),
                        "invocation_id": inv}


def fault_effective_us(trial: Trial) -> tuple[int | None, str]:
    """`t_fault_effective` -- birinchi contract buzilishi yoki birinchi
    `oom_kill` o'sishi (§3).

    OCHIQ CHEKLOV (§3): bu KUZATUV, xizmat qachon nosog'lom bo'lgani haqidagi
    ground truth emas. Probe davri (100 ms) -- e'lon qilingan noaniqlik
    chegarasi.
    """
    if trial.fault_effectives:
        v = _as_int(trial.fault_effectives[0].get("mono_us"))
        if v is not None:
            return v, "fault_effective_record"

    inject_us: int | None = None
    if trial.fault_injects:
        r = trial.fault_injects[0]
        inject_us = (_as_int(r.get("mono_us_after_call"))
                     or _as_int(r.get("mono_us"))
                     or _as_int(r.get("mono_us_before_call")))

    lo = inject_us if inject_us is not None else (trial.start_us or 0)
    first_fail = next((p.mono_us for p in trial.probes
                       if p.mono_us >= lo and not p.passed), None)
    first_oom = _first_oom_increase_us(trial, lo)
    cands = [c for c in (first_fail, first_oom) if c is not None]
    if cands:
        src = "first_contract_fail" if min(cands) == first_fail else "first_oom_kill"
        return min(cands), src
    if inject_us is not None:
        return inject_us, "inject_bracket"
    return None, "unavailable"


def _oom_series(trial: Trial, scope: str | None = None) -> list[tuple[int, int]]:
    """SUT cgroup'ining `memory.events.oom_kill` kumulyativ namunalari."""
    out: list[tuple[int, int]] = []
    for r in trial.cgroup_events:
        if scope is not None and _as_str(r.get("scope")) not in (None, scope):
            continue
        t = _as_int(r.get("mono_us"))
        v = _as_int(r.get("oom_kill"))
        if t is not None and v is not None:
            out.append((t, v))
    out.sort()
    return out


def _first_oom_increase_us(trial: Trial, lo_us: int) -> int | None:
    series = _oom_series(trial)
    prev: int | None = None
    for t, v in series:
        if prev is not None and v > prev and t >= lo_us:
            return t
        prev = v
    return None


def reference_throughput(trial: Trial, t_fault_us: int | None
                         ) -> tuple[float | None, str, dict]:
    """`R_ref` -- SHU trial'ning fault'dan oldingi throughput'i (§4.5).

    `R_ref` trial'lar bo'ylab o'rtacha OLINMAYDI: §4.5 aynan "shu trial'ning"
    deydi. Aks holda trial'lar orasidagi drift (cache holati, DVFS, termal)
    throughput bandiga kirib ketardi.
    """
    if trial.baseline_windows:
        b = trial.baseline_windows[0]
        lo = _as_int(b.get("mono_us_begin"))
        hi = _as_int(b.get("mono_us_end"))
        if lo is not None and hi is not None:
            r, st, d = window_throughput(trial.probes, lo, hi)
            if r is not None:
                d["source"] = "baseline_window"
                return r, st, d
    lo = trial.start_us
    if lo is None:
        return None, "no_probes", {}
    hi = t_fault_us if t_fault_us is not None else (trial.end_us or lo)
    # Fault boshlangan probe'ning O'ZI baseline'ga kirmaydi.
    r, st, d = window_throughput(trial.probes, lo, max(lo, hi - 1))
    d["source"] = "pre_fault_probes"
    return r, st, d


# --- Verified Recovery (§4) -------------------------------------------------


@dataclass(frozen=True)
class VrResult:
    """§4 ning yettita bandining natijasi.

    `vr` UCH QIYMATLI:
      * `True`  -- oyna to'liq kuzatilgan va hech bir invalidator ishlamagan;
      * `False` -- kamida bitta invalidator ishlagan (yoki xizmat qaytmagan);
      * `None`  -- ANIQLANMAGAN: oyna horizon bilan kesilgan, yoki throughput
                   bandi o'lchanmagan. `None` hech qachon `False` ga
                   aylantirilmaydi -- ma'lumot yetishmovchiligi natijaga
                   aylanmaydi (§4 probe uzilishi qoidasining ruhi).

    `invalidators` -- FAQAT QAT'IY invalidator'lar: ular VR=false ni
    o'rnatadi. `provisional_invalidators` -- kuzatilgan, lekin hali qat'iy
    emas (kesilgan oynada o'lchangan throughput: qolgan qism o'rtachani
    ko'tarishi mumkin). Ikkisi aralashtirilmaydi, aks holda `invalidators` ni
    filtrlagan tahlil o'lchanmagan da'voni haqiqat deb olardi.
    """

    vr: bool | None
    reason: str
    invalidators: tuple[str, ...]
    provisional_invalidators: tuple[str, ...]
    anchor_us: int | None
    anchor_source: str
    t_up_us: int | None
    window_end_us: int | None
    window_complete: bool
    n_window_probes: int
    n_window_failing: int
    throughput: float | None
    throughput_status: str
    throughput_ratio: float | None
    r_ref: float | None
    r_ref_status: str
    unverified_clauses: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_vr(
    trial: Trial,
    anchor_us: int | None,
    params: Params,
    *,
    anchor_source: str = "action",
    r_ref: float | None = None,
    r_ref_status: str = "unknown",
) -> VrResult:
    """Verified Recovery -- PREREGISTRATION.md §4, YETTITA band.

    Epizod E verified-recovered, agar `[t_up, t_up + W_stab]` oynasi mavjud
    bo'lsa va unda:
      1. `t_up` = E ning oxirgi action'idan keyingi birinchi contract'dan
         o'tgan probe;
      2. oynadagi HAR BIR probe contract'dan o'tadi   -> `contract_fail`;
      3. `InvocationID` o'zgarmaydi (yashirin restart) -> `invocation_changed`;
      4. `NRestarts` o'zgarmaydi                       -> `nrestarts_changed`;
      5. oyna throughput'i >= `theta * R_ref`          -> `throughput_below_theta`;
      6. SUT cgroup'da yangi `oom_kill` yo'q            -> `oom_kill`;
      7. host guard ishlamagan                         -> `guard_fired`.

    5-BAND VR NI PROCESS-LIVENESS'DAN AJRATADIGAN YAGONA NARSA (§4, §9.2-iii).
    Qaytgan lekin 5% throughput'da ishlayotgan xizmat recovered EMAS. Busiz
    butun hissa "process tirikmi?" ga qulaydi -- shuning uchun bu band
    o'lchanmasa natija `vr=True` emas, `vr=None` bo'ladi.

    PSI bu funksiyaga KIRMAYDI va kirmasligi kerak (§5 sirkulyarlik kafolati:
    PSI faqat prediktor).
    """
    W = params.w_stab_us
    if anchor_us is None:
        return VrResult(
            vr=None, reason="no_anchor", invalidators=(),
            provisional_invalidators=(), anchor_us=None,
            anchor_source=anchor_source, t_up_us=None, window_end_us=None,
            window_complete=False, n_window_probes=0, n_window_failing=0,
            throughput=None, throughput_status="not_evaluated",
            throughput_ratio=None, r_ref=r_ref, r_ref_status=r_ref_status,
            unverified_clauses=("1", "2", "3", "4", "5", "6", "7"))

    after = [p for p in trial.probes if p.mono_us >= anchor_us]
    if not after:
        # Anchor'dan keyin HECH QANDAY probe yo'q: instrumentatsiya tugagan,
        # natija emas.
        return VrResult(
            vr=None, reason="no_probe_data", invalidators=(),
            provisional_invalidators=(), anchor_us=anchor_us,
            anchor_source=anchor_source, t_up_us=None, window_end_us=None,
            window_complete=False, n_window_probes=0, n_window_failing=0,
            throughput=None, throughput_status="not_evaluated",
            throughput_ratio=None, r_ref=r_ref, r_ref_status=r_ref_status,
            unverified_clauses=("1", "2", "3", "4", "5", "6", "7"))

    # 1-band: t_up.
    t_up_probe = next((p for p in after if p.passed), None)
    if t_up_probe is None:
        # Xizmat horizon ichida umuman qaytmadi -> contract_fail. Bu QAT'IY
        # natija (monoton): kuzatilgan barcha probe'lar buzilgan.
        n_fail = len(after)
        return VrResult(
            vr=False, reason="no_up_probe", invalidators=("contract_fail",),
            provisional_invalidators=(), anchor_us=anchor_us,
            anchor_source=anchor_source, t_up_us=None, window_end_us=None,
            window_complete=True, n_window_probes=len(after),
            n_window_failing=n_fail, throughput=None,
            throughput_status="not_evaluated", throughput_ratio=None,
            r_ref=r_ref, r_ref_status=r_ref_status, unverified_clauses=())

    t_up = t_up_probe.mono_us
    win_end = t_up + W
    win = [p for p in trial.probes if t_up <= p.mono_us <= win_end]
    last_probe_us = trial.probes[-1].mono_us
    window_complete = last_probe_us >= win_end - params.window_slack_us

    invalidators: list[str] = []
    unverified: list[str] = []

    # 2-band: oynadagi har bir probe contract'dan o'tadi.
    n_fail = sum(1 for p in win if not p.passed)
    if n_fail:
        invalidators.append("contract_fail")

    # 3-band: InvocationID o'zgarmaydi (yashirin restart yo'q).
    inv0 = t_up_probe.invocation_id
    seen_inv = {p.invocation_id for p in win if p.invocation_id is not None}
    if inv0 is None and not seen_inv:
        unverified.append("3")
    elif len(seen_inv - {inv0}) > 0:
        invalidators.append("invocation_changed")

    # 4-band: NRestarts o'zgarmaydi.
    nrs = [_as_int(r.get("n_restarts")) for r in trial.unit_states
           if (_as_int(r.get("mono_us")) or -1) >= t_up
           and (_as_int(r.get("mono_us")) or -1) <= win_end]
    nrs = [n for n in nrs if n is not None]
    if not nrs:
        unverified.append("4")
    elif max(nrs) != min(nrs):
        invalidators.append("nrestarts_changed")

    # 6-band: SUT cgroup'da yangi oom_kill yo'q.
    oom = _oom_series(trial)
    if not oom:
        unverified.append("6")
    else:
        inside = [v for t, v in oom if t_up <= t <= win_end]
        before = [v for t, v in oom if t < t_up]
        base = before[-1] if before else (inside[0] if inside else None)
        if inside and base is not None and max(inside) > base:
            invalidators.append("oom_kill")
        elif not inside:
            unverified.append("6")

    # 7-band: host guard ishlamagan.
    if trial.guard_events:
        invalidators.append("guard_fired")

    # 5-band: throughput >= theta * R_ref. VR NI LIVENESS'DAN AJRATADIGAN BAND.
    thr_hi = min(win_end, last_probe_us)
    thr, thr_status, _thr_d = window_throughput(trial.probes, t_up, thr_hi)
    ratio: float | None = None
    if thr is not None and r_ref is not None and r_ref > 0:
        ratio = thr / r_ref
        if ratio < params.theta:
            invalidators.append("throughput_below_theta")

    # QAT'IY (definitive) va SHARTLI (provisional) invalidator'lar.
    # Monoton invalidator bir marta ishlagach qat'iy. `throughput_below_theta`
    # esa faqat oyna TO'LIQ kuzatilgan bo'lsa qat'iy -- kesilgan oynadagi
    # o'rtacha keyinchalik ko'tarilishi mumkin.
    monotone = tuple(i for i in invalidators if i in MONOTONE_INVALIDATORS)
    thr_fired = "throughput_below_theta" in invalidators
    thr_definitive = thr_fired and window_complete
    definitive = set(monotone) | ({"throughput_below_theta"} if thr_definitive
                                  else set())
    ordered = tuple(i for i in INVALIDATORS if i in definitive)
    provisional = tuple(i for i in INVALIDATORS
                        if i in invalidators and i not in definitive)

    if monotone:
        # Monoton invalidator'ni keyingi ma'lumot bekor qilmaydi -> QAT'IY false.
        #
        # NEGA BU §20.4(2) NI BUZMAYDI: §4 ning VR'i YETTITA bandning
        # KONYUNKSIYASI, va konyunksiya bitta konyunkt yolg'on bo'lsa
        # yolg'on -- 5-bandni baholash SHART emas. Taqiq `vr = True` ga
        # tegishli: 1-4 bandlar ustida "VR = true" yozish VR ni
        # liveness-only ta'rifga tushiradi va §9.2 ning ogohlantirgan
        # artefaktini YARATADI. `False` da bunday xavf yo'q.
        vr: bool | None = False
        reason = "invalidated"
    elif r_ref is None or r_ref <= 0:
        vr, reason = None, "r_ref_unavailable"
        unverified.append("5")
    elif thr is None:
        vr, reason = None, "throughput_unmeasurable"
        unverified.append("5")
    elif not window_complete:
        # Oyna horizon bilan kesilgan: throughput bandi hali QAT'IY emas
        # (qolgan qism o'rtachani ko'tarishi mumkin).
        vr, reason = None, "window_truncated"
    elif thr_definitive:
        vr, reason = False, "invalidated"
    elif ratio is None:
        # FAIL-CLOSED QO'RIQCHI -- §20.4(2) ning QAT'IY taqiqi:
        # "1-4 bandlar ustida VR hisoblash QAT'IYAN TAQIQLANADI."
        #
        # Yuqoridagi elif-zanjiri bu holatga yetib kelishga YO'L QO'YMAYDI
        # (`r_ref` va `thr` ikkisi ham mavjud bo'lsa `ratio` hisoblanadi),
        # demak bu shox hozir ERISHIB BO'LMAYDIGAN. U ataylab shunday
        # qoldiriladi: taqiq ENDI zanjirning TARTIBIDAN kelib chiqmaydi,
        # balki STRUKTURAVIY bo'ladi. Kelajakda zanjir qayta tartiblansa
        # yoki yangi shox qo'shilsa, 5-bandsiz `True` chiqishi mumkin
        # bo'lardi -- bu qo'riqcha o'sha yo'lni yopadi va `None` ni
        # NOMLANGAN sabab bilan qaytaradi.
        #
        # §4: "5-band VR ni process-liveness'dan ajratadigan narsa ...
        # Busiz butun hissa 'process tirikmi?' ga qulaydi."
        # §9.2: "liveness-only VR ta'rifi ehtimol null pilot beradi, va bu
        # null -- TA'RIF ARTEFAKTI, H1 ga qarshi dalil EMAS."
        vr, reason = None, "throughput_unmeasurable"
        unverified.append("5")
    else:
        vr, reason = True, "verified"

    return VrResult(
        vr=vr,
        reason=reason,
        invalidators=ordered,
        provisional_invalidators=provisional,
        anchor_us=anchor_us,
        anchor_source=anchor_source,
        t_up_us=t_up,
        window_end_us=win_end,
        window_complete=window_complete,
        n_window_probes=len(win),
        n_window_failing=n_fail,
        throughput=thr,
        throughput_status=thr_status,
        throughput_ratio=ratio,
        r_ref=r_ref,
        r_ref_status=r_ref_status,
        unverified_clauses=tuple(sorted(set(unverified))),
    )


# --- FR-A (§5, birlamchi, oracle-free) --------------------------------------


def actor_success_signal(trial: Trial, lo_us: int, hi_us: int | None
                         ) -> tuple[bool | None, str]:
    """`actor_success_signal` -- AKTORNING O'Z DA'VOSI (§5 FR-A).

    systemd uchun: unit `active` holatiga yetdi (`Type=notify` da `READY=1`
    qabul qilindi). REVIX uchun: engine `state=RECOVERED` chiqardi.

    Ikkala operand ham LOG'LANGAN FAKT. Oracle yo'q, fault-class label yo'q,
    matritsa yo'q -- FR-A ning butun mohiyati shu.
    """
    hi = hi_us if hi_us is not None else (trial.end_us or lo_us)

    for r in trial.actor_signals:
        t = _as_int(r.get("mono_us"))
        if t is None or not (lo_us <= t <= hi):
            continue
        if bool(r.get("success")):
            return True, "actor_signal_record"

    saw_state = False
    for r in trial.unit_states:
        t = _as_int(r.get("mono_us"))
        if t is None or not (lo_us <= t <= hi):
            continue
        saw_state = True
        st = _as_str(r.get("active_state"))
        if st == "active":
            return True, "unit_state_active"
        if _as_str(r.get("engine_state")) == "RECOVERED":
            return True, "engine_recovered"

    if trial.actor_signals or saw_state:
        return False, "no_claim_in_interval"
    return None, "no_actor_data"


def fr_a(actor_claim: bool | None, vr: bool | None) -> bool | None:
    """FR-A -- muddatidan oldin muvaffaqiyat (§5, BIRLAMCHI, oracle-free).

        FR_A = 1  <=>  actor_success_signal == true  AND  VR == false

    Uch qiymatli Kleene mantiqi: `None` (aniqlanmagan) hech qachon `False` ga
    aylantirilmaydi, aks holda aniqlanmagan VR jimgina "false recovery yo'q"
    deb hisoblanardi.

    Loyihaning qoidasi (§5): dizayn shunday bo'lishi kerak-ki, reviewer FR-B ni
    butunlay chiqarib tashlasa ham, FR-A yolg'on maqolani ko'tara oladi.
    """
    if actor_claim is False:
        return False
    if vr is True:
        return False
    if actor_claim is None or vr is None:
        return None
    return True   # actor_claim True, vr False


def _kleene_any(vals: Iterable[bool | None]) -> bool | None:
    vals = list(vals)
    if any(v is True for v in vals):
        return True
    if any(v is None for v in vals):
        return None
    return False


# --- FR-B (§5, ikkilamchi, matritsaga nisbatan) -----------------------------


def _binom_p_ge(k: int, n: int, p: float) -> float:
    """P(X >= k) binomial (n, p). Aniq, dependency'siz."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return sum(math.comb(n, i) * (p ** i) * ((1.0 - p) ** (n - i))
               for i in range(k, n + 1))


def clopper_pearson_lower(k: int, n: int, alpha: float = 0.05) -> float:
    """Clopper-Pearson pastki chegarasi (FR-B ning Repairs() matritsasi uchun).

    MARKAZIY IMPLEMENTATSIYA: `revix.stats.clopper_pearson`. Bu yerda faqat
    o'ram qoldirilgan.

    TARIX: bu funksiya avval shu faylda mustaqil yozilgan edi, chunki
    `revix/stats.py` hali mavjud emas edi. Ikki implementatsiya keyin
    solishtirildi va 7 ta sinov nuqtasida suzuvchi nuqta aniqligida mos keldi
    (eng katta farq 1.7e-16) -- ya'ni mustaqil qayta hosil qilish orqali
    tasdiqlandi. Dublikat olib tashlandi: ikki nusxa vaqt o'tib bir-biridan
    uzoqlashadi va qaysi biri haqiqiy ekani noaniq bo'lib qoladi.
    """
    from .stats import clopper_pearson
    return clopper_pearson(k, n, alpha).lower


@dataclass(frozen=True)
class RepairsMatrix:
    """`Repairs()` matritsasi (§5).

    EMPIRIK KALIBRLANADI, farmon bilan belgilanmaydi:

        Repairs(f) = { a : ClopperPearson_lower95( P^(VR|f,a) ) >= p_min }

    Kalibratsiya `VR` dan foydalanadi -- u contract asosida va oracle-free --
    demak sirkulyarlik yo'q.

    P1 DA BU MATRITSA MAVJUD EMAS (kalibratsiya eksperimenti hali yo'q).
    """

    p_min: float
    allowed: dict[str, frozenset[str]]
    provenance: str
    lower_bounds: dict[str, dict[str, float]] = field(default_factory=dict)

    @classmethod
    def from_calibration(
        cls,
        counts: dict[tuple[str, str], tuple[int, int]],
        p_min: float = P_MIN_DEFAULT,
        provenance: str = "unknown",
        alpha: float = 0.05,
    ) -> "RepairsMatrix":
        """`counts[(fault_class, action_class)] = (n_vr, n_trials)`."""
        allowed: dict[str, set[str]] = {}
        bounds: dict[str, dict[str, float]] = {}
        for (f, a), (k, n) in sorted(counts.items()):
            lb = clopper_pearson_lower(k, n, alpha)
            bounds.setdefault(f, {})[a] = lb
            allowed.setdefault(f, set())
            if lb >= p_min:
                allowed[f].add(a)
        return cls(p_min=p_min,
                   allowed={f: frozenset(a) for f, a in allowed.items()},
                   provenance=provenance, lower_bounds=bounds)


@dataclass(frozen=True)
class FrBResult:
    """FR-B natijasi. `computed=False` bo'lsa `value` HAR DOIM `None`.

    Soxta raqam qaytarilmaydi: matritsa yo'q bo'lganda 0 qaytarish "false
    recovery yo'q" degan da'vo bo'lardi, va bu o'lchanmagan.
    """

    computed: bool
    value: bool | None
    reason: str
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


FR_B_NOT_COMPUTED_NO_MATRIX = FrBResult(
    computed=False,
    value=None,
    reason="not_computed: no Repairs() matrix",
    detail={"note": "PREREGISTRATION.md §5 -- P1 da Repairs() hisoblanmaydi "
                    "(kalibratsiya eksperimenti hali yo'q), demak P1 da FR-B "
                    "BERILMAYDI. Faqat FR-A."},
)


def evaluate_fr_b(
    action_class: str | None,
    injected_fault_class: str | None,
    harm_indicator: bool | None,
    matrix: RepairsMatrix | None,
) -> FrBResult:
    """FR-B -- action/fault mos kelmasligi (§5, IKKILAMCHI, matrix-relative).

        FR_B = 1  <=>  action_class not in Repairs(injected_fault_class)
                       OR  harm_indicator == true

    `harm_indicator` O'LCHANADI, da'vo qilinmaydi (§5).

    P1 da `Repairs()` HISOBLANMAYDI, demak bu funksiya `matrix=None` bilan
    chaqirilganda AYNIQSA raqam qaytarmaydi: `FrBResult(computed=False,
    value=None, ...)`.
    """
    if matrix is None:
        return FR_B_NOT_COMPUTED_NO_MATRIX
    if injected_fault_class is None or action_class is None:
        return FrBResult(False, None,
                         "not_computed: missing action_class or fault_class",
                         {"action_class": action_class,
                          "injected_fault_class": injected_fault_class})
    if injected_fault_class not in matrix.allowed:
        return FrBResult(False, None,
                         "not_computed: fault class absent from Repairs()",
                         {"injected_fault_class": injected_fault_class,
                          "provenance": matrix.provenance})
    mismatch = action_class not in matrix.allowed[injected_fault_class]
    val = _kleene_any([mismatch, harm_indicator])
    if val is None:
        return FrBResult(False, None,
                         "not_computed: harm_indicator unmeasured",
                         {"action_mismatch": mismatch,
                          "provenance": matrix.provenance})
    return FrBResult(True, bool(val), "computed",
                     {"action_mismatch": mismatch,
                      "harm_indicator": harm_indicator,
                      "p_min": matrix.p_min,
                      "provenance": matrix.provenance})


# --- epizodlar --------------------------------------------------------------


def find_failure_onsets(probes: Sequence[Probe], k_f: int
                        ) -> list[tuple[int, int | None]]:
    """Contract buzilishi seriyalari -> failure onset indekslari.

    `F_probe` (§3): contract `k_f` marta KETMA-KET buzildi; timestamp esa
    BIRINCHI buzilgan probe'ning `mono_us_send`. `k_f = 3` sababi: bitta
    probe'dagi shovqinni (scheduling jitter, socket backlog) failure deb
    hisoblamaslik.

    Qaytadi: `(onset_index, confirm_index | None)`. `confirm_index=None` --
    seriya trace oxirida uzildi va `k_f` ga yetmadi: tasdiqlanmagan, lekin
    JIMGINA TASHLANMAYDI (horizon down holatda tugagan bo'lishi mumkin).
    """
    onsets: list[tuple[int, int | None]] = []
    i, n = 0, len(probes)
    while i < n:
        if probes[i].passed:
            i += 1
            continue
        j = i
        while j < n and not probes[j].passed:
            j += 1
        if j - i >= k_f:
            onsets.append((i, i + k_f - 1))
        elif j >= n:
            onsets.append((i, None))
        i = j
    return onsets


@dataclass
class EpisodeResult:
    """Bitta epizodning derived natijasi (§4, §5, §6)."""

    episode_id: str
    index: int
    onset_us: int
    t_detect_us: int
    t_detect_confirmed_us: int | None
    detector: str
    last_pass_before_us: int | None
    anchor_us: int | None
    anchor_source: str
    n_actions: int
    vr: bool | None
    vr_reason: str
    invalidators: tuple[str, ...]
    provisional_invalidators: tuple[str, ...]
    t_up_us: int | None
    window_end_us: int | None
    window_complete: bool
    n_window_probes: int
    n_window_failing: int
    throughput: float | None
    throughput_ratio: float | None
    throughput_status: str
    unverified_clauses: tuple[str, ...]
    time_to_first_up_us: int | None
    time_to_first_up_censored: bool
    d_probe_us: int | None
    d_probe_censored: bool
    actor_success_signal: bool | None
    actor_signal_source: str
    fr_a: bool | None
    actions: list[dict[str, Any]]
    closed_us: int

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["invalidators"] = list(self.invalidators)
        d["provisional_invalidators"] = list(self.provisional_invalidators)
        d["unverified_clauses"] = list(self.unverified_clauses)
        return d


def _last_pass_before(probes: Sequence[Probe], t_us: int) -> int | None:
    out = None
    for p in probes:
        if p.mono_us >= t_us:
            break
        if p.passed:
            out = p.mono_us
    return out


def build_episodes(trial: Trial, params: Params, r_ref: float | None,
                   r_ref_status: str) -> list[EpisodeResult]:
    """Epizodlarni qurib, har biri uchun VR va FR-A hisoblaydi.

    Epizod = failure onset'dan boshlanib, VR olinmaguncha (yoki horizon
    tugamaguncha) davom etadigan interval. §4.1 t_up ni epizodning OXIRGI
    action'iga bog'laydi, shuning uchun loop (takroriy restart) bir epizod
    ichida qoladi va oxirgi urinish bo'yicha baholanadi.

    Yashirin restart (action record'i YO'Q, lekin `InvocationID` o'zgargan)
    qayta anchor QILMAYDI -- u 3-bandni buzadi, ya'ni `invocation_changed`.
    Aynan shu narsa "oynada yashirin restart" holatini VR=false qiladi.
    """
    onsets = find_failure_onsets(trial.probes, params.k_f)
    trial_end = trial.end_us or (trial.probes[-1].mono_us if trial.probes else 0)
    episodes: list[EpisodeResult] = []
    cursor_us = -1
    idx = 0

    for (i_onset, i_conf) in onsets:
        onset_us = trial.probes[i_onset].mono_us
        if onset_us <= cursor_us:
            # Ochiq epizod ichidagi qayta buzilish: yangi epizod emas, chunki
            # epizod hali tuzatilmagan (§4.1 oxirgi action bo'yicha baholash).
            continue

        acts = [a for a in trial.actions if a.mono_us >= onset_us]
        if acts:
            anchor = acts[0].mono_us
            anchor_source = "action"
            while True:
                vr = evaluate_vr(trial, anchor, params, anchor_source=anchor_source,
                                 r_ref=r_ref, r_ref_status=r_ref_status)
                limit = vr.window_end_us if vr.vr is True else trial_end
                nxt = next((a.mono_us for a in acts
                            if a.mono_us > anchor
                            and (limit is None or a.mono_us <= limit)), None)
                if nxt is None:
                    break
                anchor = nxt
        else:
            # Action yo'q (masalan `no_action` arm). §4.1 action nazarda tutadi;
            # action bo'lmasa onset anchor bo'ladi va bu OCHIQ qayd etiladi.
            anchor = onset_us
            anchor_source = "onset"
            vr = evaluate_vr(trial, anchor, params, anchor_source=anchor_source,
                             r_ref=r_ref, r_ref_status=r_ref_status)

        ep_actions_raw = [a for a in acts if a.mono_us <= anchor]
        per_action: list[dict[str, Any]] = []
        for k, a in enumerate(ep_actions_raw):
            a_vr = evaluate_vr(trial, a.mono_us, params, anchor_source="action",
                               r_ref=r_ref, r_ref_status=r_ref_status)
            nxt_us = (ep_actions_raw[k + 1].mono_us
                      if k + 1 < len(ep_actions_raw) else None)
            claim, claim_src = actor_success_signal(trial, a.mono_us, nxt_us)
            per_action.append({
                "action_id": a.action_id,
                "action_class": a.action_class,
                "mono_us": a.mono_us,
                "policy_delay_us": a.policy_delay_us,
                "deferred": a.deferred,
                # §6.3: L_dec = t_action_issue - t_detect. `policy_delay_us`
                # ALOHIDA field -- sozlangan kutish vaqtini "decision latency"
                # deb hisoblash soxta taqqoslash.
                "l_dec_us": a.mono_us - trial.probes[i_onset].mono_us,
                "vr": a_vr.vr,
                "vr_reason": a_vr.reason,
                "invalidators": list(a_vr.invalidators),
                "provisional_invalidators": list(a_vr.provisional_invalidators),
                "actor_success_signal": claim,
                "actor_signal_source": claim_src,
                "fr_a": fr_a(claim, a_vr.vr),
            })

        if per_action:
            claim = _kleene_any([p["actor_success_signal"] for p in per_action
                                 if p["mono_us"] == anchor])
            claim_src = next((p["actor_signal_source"] for p in per_action
                              if p["mono_us"] == anchor), "no_actor_data")
            ep_fr_a = _kleene_any([p["fr_a"] for p in per_action])
        else:
            claim, claim_src = actor_success_signal(trial, onset_us, None)
            ep_fr_a = fr_a(claim, vr.vr)

        t_detect = trial.probes[i_onset].mono_us
        t_conf = trial.probes[i_conf].mono_us if i_conf is not None else None
        lpb = _last_pass_before(trial.probes, onset_us)

        # §6.3: time_to_first_up = t_up - t_detect. "Verification latency"
        # achievement metrikasi sifatida BERILMAYDI -- muvaffaqiyatli VR uchun
        # u ta'rifan W_stab ga teng.
        if vr.t_up_us is not None:
            ttfu, ttfu_cens = vr.t_up_us - t_detect, False
        else:
            ttfu, ttfu_cens = trial_end - t_detect, True

        # §6.1 D_probe: failure'dan oldingi oxirgi o'tgan probe -> VR shartini
        # QANOATLANTIRUVCHI oynaning birinchi probe'i. VR olinmasa -> horizon
        # `T_trial` da censored (§6.2), TASHLANMAYDI.
        start = lpb if lpb is not None else (trial.start_us or onset_us)
        if vr.vr is True and vr.t_up_us is not None:
            d_probe, d_cens = vr.t_up_us - start, False
        else:
            d_probe, d_cens = trial_end - start, True

        closed = (vr.window_end_us if (vr.vr is True and vr.window_end_us)
                  else trial_end)
        episodes.append(EpisodeResult(
            episode_id=f"{trial.trial_id}:e{idx}",
            index=idx,
            onset_us=onset_us,
            t_detect_us=t_detect,
            t_detect_confirmed_us=t_conf,
            detector="probe",
            last_pass_before_us=lpb,
            anchor_us=vr.anchor_us,
            anchor_source=vr.anchor_source,
            n_actions=len(per_action),
            vr=vr.vr,
            vr_reason=vr.reason,
            invalidators=vr.invalidators,
            provisional_invalidators=vr.provisional_invalidators,
            t_up_us=vr.t_up_us,
            window_end_us=vr.window_end_us,
            window_complete=vr.window_complete,
            n_window_probes=vr.n_window_probes,
            n_window_failing=vr.n_window_failing,
            throughput=vr.throughput,
            throughput_ratio=vr.throughput_ratio,
            throughput_status=vr.throughput_status,
            unverified_clauses=vr.unverified_clauses,
            time_to_first_up_us=ttfu,
            time_to_first_up_censored=ttfu_cens,
            d_probe_us=d_probe,
            d_probe_censored=d_cens,
            actor_success_signal=claim,
            actor_signal_source=claim_src,
            fr_a=ep_fr_a,
            actions=per_action,
            closed_us=closed,
        ))
        cursor_us = closed if vr.vr is True else trial_end
        idx += 1

    return episodes


# --- downtime (§6.1, §6.2) --------------------------------------------------


@dataclass
class Downtime:
    d_sd_us: int | None
    d_sd_censored: bool
    d_sd_cycles: int
    d_probe_us: int | None
    d_probe_censored: bool
    d_eff_us: float | None
    d_eff_failing_us: float
    d_eff_brownout_us: float
    d_eff_window_us: tuple[int, int] | None
    d_eff_status: str
    n_failing_probes: int

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.d_eff_window_us is not None:
            d["d_eff_window_us"] = list(self.d_eff_window_us)
        return d


def compute_d_sd(trial: Trial) -> tuple[int | None, bool, int]:
    """`D_sd` -- `ActiveExitTimestampMonotonic` -> keyingi
    `ActiveEnterTimestampMonotonic` (§6.1, D-Bus, mikrosekund).

    NIMANI KO'RMAYDI (§6.1, ochiq e'lon): ORTIQCHA KREDIT -- `active` "to'g'ri
    xizmat qilayapti" degani EMAS. `active` lekin 20% throughput'dagi xizmat
    `D_sd` bo'yicha NOL downtime ko'rsatadi. Shuning uchun `D_sd` asosiy
    o'lchov emas, va `D_eff` bilan birga beriladi.
    """
    end_us = trial.end_us
    exits: list[int] = []
    enters: list[int] = []
    for r in trial.unit_states:
        x = _as_int(r.get("active_exit_ts_mono_us"))
        e = _as_int(r.get("active_enter_ts_mono_us"))
        if x is not None and x > 0:
            exits.append(x)
        if e is not None and e > 0:
            enters.append(e)
    if not trial.unit_states:
        return None, False, 0
    start = trial.start_us or 0
    uexits = sorted({x for x in exits if (end_us is None or x <= end_us)
                     and x >= start})
    if not uexits:
        return 0, False, 0
    total = 0
    censored = False
    cycles = 0
    for x in uexits:
        nxt = min((e for e in enters if e > x), default=None)
        cycles += 1
        if nxt is None or (end_us is not None and nxt > end_us):
            # Horizon down holatda tugadi -> T_trial da censored (§6.2).
            if end_us is not None:
                total += max(0, end_us - x)
            censored = True
        else:
            total += nxt - x
    return total, censored, cycles


def compute_d_eff(trial: Trial, params: Params, r_ref: float | None,
                  lo_us: int | None, hi_us: int | None
                  ) -> tuple[float | None, float, float, str, int]:
    """`D_eff = P * n_failing_probes + integral max(0, 1 - r(t)/R_ref) dt` (§6.1).

    `D_eff` -- BROWNOUT'ni ham hisoblaydigan yagona o'lchov, va §6.1 ga ko'ra
    "C ning B dan halol ustun kelishi eng ehtimoliy joyi".

    IKKI OCHIQ TALQIN QARORI (pre-registration ularni ko'rsatmagan, shuning
    uchun bu yerda OCHIQ yozilади va natijada qayd etiladi):

      (a) INTEGRAL DOMENI: `[t_fault_effective, horizon]`. Baseline oynasini
          qo'shish integrand'ni ~0 qilardi (r ~ R_ref), lekin domenni oshkora
          qilmasa -- takrorlanmaydigan bo'lardi. Domen natijada
          `d_eff_window_us` sifatida beriladi.
      (b) IKKI HAD USTMA-UST TUSHMAYDI: integral FAQAT ikkita ketma-ket
          O'TGAN probe orasidagi intervallar bo'yicha olinadi. Buzilgan
          probe'lar allaqachon `P * n_failing` hadida hisoblangan; ularni
          integralda ham hisoblash ikki marta hisoblash bo'lardi.
    """
    if not trial.probes:
        return None, 0.0, 0.0, "no_probes", 0
    lo = lo_us if lo_us is not None else trial.probes[0].mono_us
    hi = hi_us if hi_us is not None else trial.probes[-1].mono_us
    win = [p for p in trial.probes if lo <= p.mono_us <= hi]
    n_fail = sum(1 for p in win if not p.passed)
    term_fail = float(n_fail * params.probe_period_us)
    if r_ref is None or r_ref <= 0:
        return None, term_fail, 0.0, "r_ref_unavailable", n_fail
    term_brown = 0.0
    for a, b in zip(win, win[1:]):
        if not (a.passed and b.passed):
            continue
        if a.progress is None or b.progress is None:
            continue
        if a.invocation_id != b.invocation_id:
            continue   # restart: progress 0 dan boshlanadi, tezlik ma'nosiz
        dt = b.mono_us - a.mono_us
        if dt <= 0:
            continue
        r = (b.progress - a.progress) * 1_000_000.0 / dt
        term_brown += max(0.0, 1.0 - r / r_ref) * dt
    return term_fail + term_brown, term_fail, term_brown, "ok", n_fail


# --- disposition (§12) ------------------------------------------------------


@dataclass(frozen=True)
class WindowContainment:
    """§4 verifikatsiya oynasi pressure hold ICHIDA joylashdimi (§17).

    Barcha field'lar `None` bo'lishi mumkin va `None` = "O'LCHANMADI",
    `0` = "o'lchangan no'l" -- modulning disiplinasi. `inside_hold` uch
    qiymatli: `True` / `False` / `None` (aniqlanmagan), chunki `T_h`
    o'lchanmagan bo'lsa savol javobsiz qoladi va `False` deb YOZILMAYDI.
    """

    status: str
    t_up_us: int | None
    window_end_us: int | None
    w_stab_us: int
    hold_end_us: int | None
    horizon_end_us: int | None
    inside_hold: bool | None
    # `T_h - (t_up + W_stab)`: musbat = bo'sh joy bor, manfiy = oshib ketdi.
    # §17.4(5) validatori aynan shu kattalikni tekshiradi.
    slack_to_hold_us: int | None
    slack_to_horizon_us: int | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_window_containment(
    t_up_us: int | None,
    params: Params,
    *,
    hold_end_us: int | None,
    horizon_end_us: int | None,
) -> WindowContainment:
    """§17.3 ning uch holatini (a)/(b)/(c) ga ajratadi.

    §17.2 arifmetikasi (hammasi MUZLATILGAN qiymatlardan):

        oyna boshi  = `t_up`            (§4, 1-band -- `t_inject` EMAS)
        oyna oxiri  = `t_up + W_stab`   (§4)
        hold oxiri  = `T_h`             (§9.4: t_h + hold_cap_s)
        horizon     = `T_trial`

        (c) `t_up + W <= T_h`                -> `inside_hold`   -- to'g'ri
        (a) `T_h < t_up + W <= T_trial`      -> `past_pressure` -- §17.3(a)
        (b) `t_up + W > T_trial`             -> `past_horizon`  -- §17.3(b)

    (b) BIRINCHI tekshiriladi, chunki §17.3 jadvalida (a) ning sharti
    `... <= T_trial` bilan chegaralangan, ya'ni ikki shart o'zaro istisno
    bo'lishi uchun (b) ustun. Va (b) `T_h` ni TALAB QILMAYDI, demak `T_h`
    o'lchanmagan run'da ham aniqlanadi.

    NEGA `window_slack_us` ISHLATILMAYDI: `evaluate_vr` oyna QOPLANISHI
    uchun bitta probe davri yo'l qo'yadi (§6.1 kvantlashi). Bu yerda esa
    savol boshqa -- oyna MUZLATILGAN hold chegarasiga sig'dimi. §17.2
    arifmetikasi aniq va muzlatilgan qiymatlardan olingan, demak unga
    slack qo'shish muzlatilgan cheklovni JIMGINA kengaytirish bo'lardi.
    Tenglik (`==`) hold ichida hisoblanadi, chunki §17.4 shartni `<=`
    bilan yozadi.
    """
    W = params.w_stab_us
    if t_up_us is None:
        # Oyna umuman BOSHLANMADI (§4: oyna "mavjud bo'lsa"). Bu §16.2(B)
        # ning `down_at_horizon` holati -- §17 unga TEGMAYDI.
        return WindowContainment(
            status=WINDOW_NO_T_UP, t_up_us=None, window_end_us=None,
            w_stab_us=W, hold_end_us=hold_end_us,
            horizon_end_us=horizon_end_us, inside_hold=None,
            slack_to_hold_us=None, slack_to_horizon_us=None)

    win_end = t_up_us + W
    slack_hold = (hold_end_us - win_end) if hold_end_us is not None else None
    slack_hor = (horizon_end_us - win_end) if horizon_end_us is not None else None

    if horizon_end_us is not None and win_end > horizon_end_us:
        status, inside = WINDOW_PAST_HORIZON, False
    elif hold_end_us is None:
        # `T_h` o'lchanmagan: (a) va (c) ni AJRATIB BO'LMAYDI. `False` deb
        # yozish kuzatilmagan narsani natija deb yozish bo'lardi, `True` deb
        # yozish esa §17.4 ni jimgina chetlab o'tish bo'lardi -> `None`.
        status, inside = WINDOW_NOT_EVALUATED, None
    elif win_end > hold_end_us:
        status, inside = WINDOW_PAST_PRESSURE, False
    else:
        status, inside = WINDOW_INSIDE_HOLD, True

    return WindowContainment(
        status=status, t_up_us=t_up_us, window_end_us=win_end, w_stab_us=W,
        hold_end_us=hold_end_us, horizon_end_us=horizon_end_us,
        inside_hold=inside, slack_to_hold_us=slack_hold,
        slack_to_horizon_us=slack_hor)


def derive_disposition(trial: Trial, gaps: list[dict[str, Any]],
                       down_at_horizon: bool,
                       window: WindowContainment | None = None,
                       ) -> tuple[str, str, bool]:
    """Har trial'ga AYNAN BITTA disposition (§12) -- jimgina eksklyuziya yo'q.

    Ustunlik tartibi (reducer avtoritetligi faqat OBYEKTIV log faktlarida):
      1. `aborted_guard`   -- guard trip qilgan (log fakt);
      2. xom `contaminated` / `washout_timeout` / `harness_error` saqlanadi --
         bu holatlarni faqat harness biladi;
      3. `censored` + `probe_gap`  -- probe uzilishi > 2xP (§4);
      4. `censored` + `window_past_pressure` / `window_past_horizon` --
         oyna hold'dan yoki horizon'dan chiqdi (§17.4);
      5. `censored` + `down_at_horizon` -- horizon down holatda tugadi (§12);
      6. xom `censored`;
      7. `complete`.

    PROBE UZILISHI HECH QACHON `failed` EMAS (§4): instrumentatsiya yo'qolishi
    jimgina natijaga aylanmaydi.

    NEGA OYNA HOLATI `down_at_horizon` DAN OLDIN (§17.4): `down_at_horizon`
    faqat `not probes[-1].passed` ga qaraydi, demak u (i) xizmat qaytib,
    keyin yana yiqilgan va (ii) xizmat shunday kech qaytgan-ki oyna kesilgan
    (`evaluate_vr` -> `window_truncated`) holatlarini HAM ushlaydi. §17.4
    bularni `window_past_*` deb belgilaydi. Agar `down_at_horizon` oldin
    tekshirilsa, ular `censored:down_at_horizon` bo'lib qolardi -- va o'sha
    juft §16.2(B) bo'yicha binar maxrajga KIRADI, ya'ni §17.4(1) ("oynasi
    hold ichida bo'lmagan trial `VR = false` deb yozilMAYDI va maxrajga
    kiritilMAYDI") JIMGINA bekor bo'lardi. Shuning uchun tartib teskari.

    NEGA OYNA HOLATI `probe_gap` DAN KEYIN: uzilish > 2xP bo'lsa `t_up` ning
    o'zi uzilish artefakti bo'lishi mumkin, demak oyna joylashuvini ishonchsiz
    trace'dan hisoblash noto'g'ri. §4 probe uzilishiga O'Z hukmini beradi.

    NEGA guard/kontaminatsiyadan KEYIN: `aborted_guard` -- host xavfsizlik
    hodisasi (§4 7-band VR ni darhol false qiladi), va §6.2 asosida
    kontaminatsiya censoring'dan USTUN bo'lishi shart, aks holda
    chiqarilishi kerak trial `censored` yorlig'i ostida analizga kirardi.
    """
    raw = trial.disposition_raw
    conflict = False
    win_status = window.status if window is not None else WINDOW_NOT_EVALUATED
    win_src = WINDOW_CONTAINMENT_SOURCE.get(win_status)
    if trial.guard_events:
        final, src = "aborted_guard", "guard_event"
    elif raw in ("contaminated", "washout_timeout", "harness_error"):
        final, src = raw, "trial_end"
    elif gaps:
        final, src = "censored", "probe_gap"
    elif win_src is not None:
        # §17.4(1)-(2): §4 ning kattaligi O'LCHANMADI -> `censored`, chunki
        # §4 `censored` ni "kuzatmagan narsani natija deb yozmaymiz"
        # ma'nosida ishlatadi (§16.2(B) dagi asos). §12 ning yopiq enum'iga
        # TEGILMAYDI -- bu `disposition_source`, `disposition` emas.
        final, src = "censored", win_src
    elif down_at_horizon:
        final, src = "censored", "down_at_horizon"
    elif raw == "censored":
        final, src = "censored", "trial_end"
    elif raw in DISPOSITIONS:
        final, src = raw, "trial_end"
    else:
        final, src = "complete", "derived"
    if raw is not None and raw != final:
        conflict = True
    return final, src, conflict


# --- birlamchi analiz to'plami: (disposition, disposition_source) jufti -----
#
# §16.2(B) hukmi. Bu uchta funksiya -- qoidaning YAGONA manbasi: `reduce_trial`
# ning `included_in_primary` / `exclusion_reason` maydonlari ham, `select_primary`
# selektori ham, `reduce_run` ning eksklyuziya darajalari ham shu yerdan
# hisoblanadi, demak ular bir-biridan AJRALIB KETA OLMAYDI.


def primary_denominator_verdict(
    disposition: str | None,
    disposition_source: str | None,
    *,
    vr: bool | None | Any = _UNSET,
    vr_reason: str | None = None,
) -> tuple[bool, str | None]:
    """Trial binar `P(VR)` maxrajiga kiradimi + KIRMASA NOMLANGAN SABAB.

    MAXRAJGA KIRISH -- IKKI ZARUR SHARTNING KONYUNKSIYASI:

      1. **§20.2 ANIQLANGANLIK:** `vr` tasdiqlab aniqlangan (`True` yoki
         `False`). `vr is None` -- sababi nima bo'lishidan qat'i nazar --
         CHIQARILADI, va sabab `vr_undetermined:<vr_reason>` deb nomlanadi.
      2. **§16.2(B) JUFT:** `(disposition, disposition_source)`
         `PRIMARY_DENOMINATOR_SOURCES` ruxsat-ro'yxatida bor.

    NEGA IKKISI HAM ZARUR, biri ikkinchisini O'RNINI BOSMAYDI (§20.2 +
    §4): `probe_gap` trial'ining `vr` i `True` BO'LISHI MUMKIN -- uzilish
    oynadan tashqarida bo'lsa predikat aniqlanadi -- va §4 u trial'ni
    shunda ham `censored`, NATIJA emas deb hukm qiladi
    ("Instrumentatsiya yo'qolishi hech qachon jimgina natijaga
    aylanmaydi"). Demak faqat aniqlanganlikka tayanish §4 ni buzardi.
    Teskarisi ham: `no_episode` trial'ining jufti (`complete`/`derived`)
    ruxsat etilgan, lekin predikat INSTANSIYALANMAGAN, demak faqat juftga
    tayanish §20.2 ni buzardi.

    NEGA SABABLAR TARTIBI shunday: ikkisi bir vaqtda to'g'ri bo'lsa JUFT
    sababi beriladi (masalan `censored:probe_gap`), chunki u §4 darajasidagi
    HUKM, `vr` ning aniqlanmaganligi esa ko'pincha uning OQIBATI. To'liq
    ma'lumot yo'qolmaydi: record'da `vr_reason` ALOHIDA maydon sifatida
    qoladi.

    `vr` BERILMASA (`_UNSET`) faqat 2-shart tekshiriladi -- bu
    ORQAGA MUVOFIQLIK uchun va u YARIM javob: a'zolikni hal qiladigan
    chaqiruvchi `vr` ni BERISHI shart (`select_primary` beradi).

    FAIL-CLOSED. Jadvalda yo'q har qanday juft -- CHIQARILADI, va sabab
    manbani NOMLAYDI, demak u jim qolmaydi.

    NEGA ISTISNO EMAS, NOMLANGAN EKSKLYUZIYA (§16.6 + 4-qoida): noma'lum
    `disposition_source` da `raise` qilish `reduce_trial` ni ichidan
    yiqitardi, ya'ni BUTUN run reduksiyasi to'xtardi va 119 to'g'ri trial
    HAM chiqishga tushmasdi -- bu aynan §6.2 ning "trial tashlanmaydi"
    strukturaviy kafolatini buzish bo'lardi. Shuning uchun noma'lum juft
    maxrajdan chiqariladi, LEKIN har record'da nomlangan sabab qoladi va
    `reduce_run` uni eksklyuziya hisobotida ko'rsatadi.

    NEGA BU §17.4 NING TARTIB QULFINI ORTIQCHA QILMAYDI -- VA U
    FAQAT QISMAN YUMSHATADI (o'lchangan, taxmin qilinmagan):

      * Oyna kesilib `vr` ANIQLANMAGAN qolsa (`window_truncated`), 20.2 ning
        aniqlanganlik sharti trial'ni O'ZI chiqaradi, demak a'zolik
        oyna-va-`down_at_horizon` tartibiga CHIDAMLI; tartib faqat
        BERILADIGAN SABABNI belgilaydi.
      * LEKIN oyna horizon'dan chiqib, oxirgi probe BUZILGAN bo'lsa, oyna
        ichida monoton invalidator ishlaydi va `vr = False` -- ANIQLANGAN,
        demak 20.2 uni CHIQARMAYDI. Bunday trial'ni faqat §17.4 ning JUFT
        qoidasi chiqaradi, ya'ni u yerda TARTIB A'ZOLIKNI belgilaydi.

    Demak tartib qulfi endpoint uchun hali ham YUK KO'TARADI, va §16.4
    bilan §20 ikkisi ham sababning nomlanishini talab qiladi. Tartib va
    uning testi SAQLANADI. (Ikki shox
    `test_20_2_tartibga_chidamlilik_FAQAT_vr_None_shoxida_amal_qiladi` da
    o'lchanadi.)
    """
    disp = disposition if disposition in DISPOSITIONS else None
    src_known = disposition_source in DISPOSITION_SOURCES

    if disp is None:
        return False, f"unknown_disposition({disposition}):{disposition_source}"
    if not src_known:
        # §16.2(B) juftga tayanadi: manba noma'lum bo'lsa juft ham noma'lum.
        return False, f"{disp}:unknown_source({disposition_source})"
    if disposition_source not in PRIMARY_DENOMINATOR_SOURCES[disp]:
        # Nomlangan eksklyuziya: o'quvchi KUZATILMAGAN natijani (`probe_gap`)
        # KUZATILGAN no'l-hodisadan (`down_at_horizon`) ajrata olishi SHART
        # (§16.2(B) jadvali), shuning uchun sabab manbani o'z ichiga oladi.
        # JUFT sababi USTUN -- yuqoridagi docstring'ni ko'ring.
        return False, f"{disp}:{disposition_source}"
    # §20.2: juft ruxsat etdi, lekin predikat ANIQLANGAN bo'lishi ham SHART.
    if vr is not _UNSET and vr is None:
        return False, f"vr_undetermined:{vr_reason}"
    return True, None


def enters_primary_denominator(disposition: str | None,
                               disposition_source: str | None,
                               *,
                               vr: bool | None | Any = _UNSET,
                               vr_reason: str | None = None) -> bool:
    """Trial binar `P(VR)` maxrajiga kiradimi (`SET_BINARY_DENOMINATOR`).

    §16.2(B) jufti VA §20.2 aniqlanganligi -- ikkisi ham zarur. `vr`
    berilmasa faqat juft tekshiriladi (yarim javob, orqaga muvofiqlik).
    """
    return primary_denominator_verdict(disposition, disposition_source,
                                       vr=vr, vr_reason=vr_reason)[0]


def primary_exclusion_reason(disposition: str | None,
                             disposition_source: str | None,
                             *,
                             vr: bool | None | Any = _UNSET,
                             vr_reason: str | None = None) -> str | None:
    """Maxrajdan chiqarilish sababi, NOMLANGAN holda; kirsa `None`."""
    return primary_denominator_verdict(disposition, disposition_source,
                                       vr=vr, vr_reason=vr_reason)[1]


def enters_survival_set(disposition: str | None,
                        vr_reason: str | None = None) -> bool:
    """KM/log-rank va loop-rate to'plamiga kiradimi (§6.2, §20.3).

    §6.2: censored trial'lar KIRADI. §20.3 ning YAGONA chekinishi --
    `no_episode`: unda hodisa KUTILAYOTGAN emas edi, demak censored
    kuzatuv ("hodisa `t` gacha sodir bo'lmadi") YOLG'ON da'vo bo'lardi.
    `r_ref_unavailable` / `throughput_unmeasurable` esa KIRADI (§20.4(3)):
    u yerda xizmat ishdan chiqqan, hodisa kutilayotgan edi, faqat `D_probe`
    ning OXIRI aniqlanmaydi -- bu haqiqiy right censoring.
    """
    if disposition not in SURVIVAL_DISPOSITIONS:
        return False
    return vr_reason not in SURVIVAL_EXCLUDED_VR_REASONS


def probe_gaps(trial: Trial, params: Params) -> list[dict[str, Any]]:
    """Trial ichidagi probe uzilishlari > 2xP (§4)."""
    out: list[dict[str, Any]] = []
    lim = params.probe_gap_max_us
    for a, b in zip(trial.probes, trial.probes[1:]):
        gap = b.mono_us - a.mono_us
        if gap > lim:
            out.append({"prev_mono_us": a.mono_us, "next_mono_us": b.mono_us,
                        "gap_us": gap, "limit_us": lim})
    return out


# --- trial reduksiyasi ------------------------------------------------------


def reduce_trial(trial: Trial, params: Params, *,
                 repairs: RepairsMatrix | None = None
                 ) -> tuple[dict[str, Any], list[EpisodeResult]]:
    """Bitta trial -> derived `trial_metrics` payload + epizodlar.

    Bu funksiya HECH QACHON `None` qaytarmaydi va hech qachon trial'ni
    "tashlamaydi": recovery bo'lmagan trial'larni tashlash klassik yashirin
    bias (§6.2). Eksklyuziya faqat `included_in_primary` flag'i va NOMLANGAN
    selektorlar orqali bo'ladi.
    """
    t_fault, t_fault_src = fault_effective_us(trial)
    r_ref, r_ref_status, r_ref_detail = reference_throughput(trial, t_fault)
    episodes = build_episodes(trial, params, r_ref, r_ref_status)
    gaps = probe_gaps(trial, params)
    trial_end = trial.end_us
    start = trial.start_us

    down_at_horizon = bool(trial.probes) and not trial.probes[-1].passed

    # §17: oyna pressure hold ICHIDA joylashdimi. `t_up` birinchi epizoddan
    # olinadi -- aynan `vr` va `time_to_vr` hisoblanadigan epizod, demak
    # klassifikatsiya payload'ning binar natijasi bilan BIR XIL oynaga
    # tegishli.
    window = classify_window_containment(
        episodes[0].t_up_us if episodes else None,
        params,
        hold_end_us=trial.hold_end_us,
        horizon_end_us=trial.horizon_end_us,
    )

    disposition, disp_src, disp_conflict = derive_disposition(
        trial, gaps, down_at_horizon, window)

    # §4 ning predikati -- BIRINCHI epizod bo'yicha (payload'ning `vr` i).
    # §20.2 maxrajni shu qiymatning ANIQLANGANLIGIGA bog'laydi, shuning
    # uchun u verdict'dan OLDIN hisoblanishi shart.
    vr_first = episodes[0].vr if episodes else None
    vr_first_reason = (episodes[0].vr_reason if episodes
                       else VR_REASON_NO_EPISODE)

    # §16.2(B) JUFT + §20.2 ANIQLANGANLIK -- ikki zarur shartning
    # konyunksiyasi, BITTA joyda hisoblanadi, demak flag va sabab
    # bir-biriga zid bo'lishi IMKONSIZ.
    in_primary, primary_excl_reason = primary_denominator_verdict(
        disposition, disp_src, vr=vr_first, vr_reason=vr_first_reason)
    in_survival = enters_survival_set(disposition, vr_first_reason)
    survival_excl_reason = survival_exclusion_reason(
        disposition, disp_src, vr_first_reason)

    d_sd, d_sd_cens, d_sd_cycles = compute_d_sd(trial)
    d_eff_lo = t_fault if t_fault is not None else start
    d_eff, d_eff_fail, d_eff_brown, d_eff_status, n_failing = compute_d_eff(
        trial, params, r_ref, d_eff_lo, trial_end)

    # §6.2: trial_downtime = horizon ichidagi epizod downtime'larining
    # yig'indisi; horizon down holatda tugasa -> T_trial da censored.
    if episodes:
        d_probe = sum(e.d_probe_us or 0 for e in episodes)
        d_probe_cens = any(e.d_probe_censored for e in episodes)
    else:
        d_probe, d_probe_cens = 0, False

    dt = Downtime(
        d_sd_us=d_sd, d_sd_censored=d_sd_cens, d_sd_cycles=d_sd_cycles,
        d_probe_us=d_probe, d_probe_censored=d_probe_cens,
        d_eff_us=d_eff, d_eff_failing_us=d_eff_fail,
        d_eff_brownout_us=d_eff_brown,
        d_eff_window_us=((d_eff_lo, trial_end)
                         if d_eff_lo is not None and trial_end is not None else None),
        d_eff_status=d_eff_status, n_failing_probes=n_failing,
    )

    # §6.4 loop: loop_rate = Delta NRestarts / T_trial;
    # loop_detected = 1 <=> T_trial ichida >=5 invocation VA barchasi VR dan
    # o'tmagan.
    invs = {p.invocation_id for p in trial.probes if p.invocation_id}
    for r in trial.unit_states:
        v = _as_str(r.get("invocation_id"))
        if v:
            invs.add(v)
    nrs = [n for n in (_as_int(r.get("n_restarts")) for r in trial.unit_states)
           if n is not None]
    n_restarts_delta = (max(nrs) - min(nrs)) if nrs else None
    t_trial_us = trial.t_trial_us
    loop_rate = None
    if n_restarts_delta is not None and t_trial_us:
        loop_rate = n_restarts_delta / (t_trial_us / 1_000_000.0)
    vr_values = [e.vr for e in episodes]
    loop_detected = bool(len(invs) >= 5 and not any(v is True for v in vr_values))

    # `vr_first` / `vr_first_reason` YUQORIDA hisoblangan (§20.2 verdict'i
    # ularga tayanadi) -- bu yerda QAYTA hisoblanmaydi, aks holda ikki
    # qiymat ajralib ketishi mumkin bo'lardi.
    vr_any = _kleene_any(vr_values) if episodes else None
    fr_a_trial = _kleene_any([e.fr_a for e in episodes]) if episodes else None

    # §6.2: time-to-VR right censoring. VR hodisasi horizon ichida bo'lmasa,
    # kuzatuv CENSORED -- TASHLANMAYDI (Kaplan-Meier / log-rank ga kiradi).
    if episodes and episodes[0].vr is True and episodes[0].window_end_us is not None:
        time_to_vr = episodes[0].window_end_us - episodes[0].t_detect_us
        time_to_vr_cens = False
    elif episodes and trial_end is not None:
        time_to_vr = trial_end - episodes[0].t_detect_us
        time_to_vr_cens = True
    else:
        time_to_vr, time_to_vr_cens = None, True

    fr_b = evaluate_fr_b(
        action_class=(trial.actions[0].action_class if trial.actions else None),
        injected_fault_class=_as_str((trial.begin or {}).get("fault_class"))
        or _as_str((trial.fault_injects[0] if trial.fault_injects else {}).get("kind")),
        harm_indicator=(None if not trial.begin
                        else trial.begin.get("harm_indicator")),
        matrix=repairs,
    )

    payload: dict[str, Any] = {
        "derived": True,
        "reducer_version": REDUCER_VERSION,
        "preregistration_sections": ["4", "5", "6", "12", "16", "17", "20"],
        "arm": trial.arm,
        "pressure_band": trial.pressure_band,
        "params": params.as_dict(),

        "disposition": disposition,
        "disposition_raw": trial.disposition_raw,
        "disposition_source": disp_src,
        "disposition_conflict": disp_conflict,
        # §16.2(B): to'plam `(disposition, disposition_source)` jufti bilan
        # aniqlanadi -- `disposition` bilan EMAS. `exclusion_reason` MANBANI
        # NOMLAYDI, demak o'quvchi kuzatilMAGAN natijani (`censored:probe_gap`)
        # kuzatilgan no'l-hodisadan (`censored:down_at_horizon`, maxrajga
        # KIRADI) ajrata oladi.
        # §20.2: a'zolik IKKI zarur shartning konyunksiyasi -- juft RUXSAT
        # etishi VA `vr` ANIQLANGAN bo'lishi. `vr_reason` alohida maydon
        # bo'lib qoladi, demak `exclusion_reason` bitta sababni bersa ham
        # to'liq ma'lumot yo'qolmaydi.
        "included_in_primary": in_primary,
        # §20.3: `no_episode` IKKALA to'plamdan ham chiqadi -- shuning uchun
        # bu flag endi `disposition` dan EMAS, `enters_survival_set()` dan.
        "included_in_survival": in_survival,
        "exclusion_reason": primary_excl_reason,
        "survival_exclusion_reason": survival_excl_reason,
        # §16.4: eksklyuziya darajasi QAYSI to'plam ustida hisoblanganini
        # NOMLASHI SHART -- shuning uchun record'ning o'zi to'plam nomini
        # ko'taradi va `exclusion_reason` hech qachon nomsiz qolmaydi.
        "primary_analysis_set": SET_BINARY_DENOMINATOR,
        "survival_analysis_set": SET_SURVIVAL,

        "t_trial_us": t_trial_us,
        "trial_begin_us": start,
        "trial_end_us": trial_end,
        "has_trial_begin": trial.begin is not None,
        "has_trial_end": trial.end is not None,
        "t_fault_effective_us": t_fault,
        "t_fault_effective_source": t_fault_src,
        "r_ref": r_ref,
        "r_ref_status": r_ref_status,
        "r_ref_detail": r_ref_detail,

        "n_probes": len(trial.probes),
        "n_probes_failing": sum(1 for p in trial.probes if not p.passed),
        "probe_gaps": gaps,
        "probe_gap_max_us": max((g["gap_us"] for g in gaps), default=0),
        "down_at_horizon": down_at_horizon,

        # --- §17: oyna bo'sh-joy KIRISHLARI ochiq beriladi ------------------
        # §17.4(5) validator shartini (`t_up + W_stab_pilot <= T_h`) tekshirish
        # uchun kerak bo'lgan HAR BIR operand shu yerda, hisoblangan verdict
        # bilan BIRGA: validator reducer'ning javobiga ishonishi shart emas,
        # u operandlardan o'zi qayta hisoblay oladi.
        "window_containment": window.status,
        "window_inside_hold": window.inside_hold,     # None = o'lchanmadi
        "t_up_us": window.t_up_us,
        "vr_window_end_us": window.window_end_us,
        "w_stab_us": window.w_stab_us,
        "t_hold_end_us": window.hold_end_us,          # None = o'lchanmadi
        "t_horizon_end_us": window.horizon_end_us,
        "window_slack_to_hold_us": window.slack_to_hold_us,
        "window_slack_to_horizon_us": window.slack_to_horizon_us,

        "n_episodes": len(episodes),
        "episode_ids": [e.episode_id for e in episodes],
        "n_actions": len(trial.actions),
        "n_invocations": len(invs),
        "n_restarts_delta": n_restarts_delta,
        "loop_rate_per_s": loop_rate,
        "loop_detected": loop_detected,

        "vr": vr_first,
        "vr_any": vr_any,
        # §20.2: sabab NOMLANGAN maydon -- maxrajdan chiqarilish qarori
        # shu qiymatga tayanadi, demak u yagona joydan keladi.
        "vr_reason": vr_first_reason,
        # §20.4(2): 5-band (throughput) BAHOLANDIMI. `vr=True` hech qachon
        # 5-bandsiz chiqmaydi (quyidagi fail-closed qo'riqchi), lekin
        # auditor buni RECORD'DAN ko'rishi kerak, kodni o'qimasdan.
        "vr_band5_evaluated": (episodes[0].throughput_ratio is not None
                               if episodes else False),

        "invalidators": list(episodes[0].invalidators) if episodes else [],
        "provisional_invalidators": (list(episodes[0].provisional_invalidators)
                                     if episodes else []),
        "unverified_clauses": sorted({c for e in episodes
                                      for c in e.unverified_clauses}),
        "fr_a": fr_a_trial,
        "fr_b": fr_b.as_dict(),

        "time_to_first_up_us": (episodes[0].time_to_first_up_us
                                if episodes else None),
        "time_to_first_up_censored": (episodes[0].time_to_first_up_censored
                                      if episodes else True),
        "time_to_vr_us": time_to_vr,
        "time_to_vr_censored": time_to_vr_cens,
    }
    payload.update(dt.as_dict())
    return payload, episodes


# --- sensitivity sweep (§4) -------------------------------------------------


def sweep_trial(trial: Trial, grid: Sequence[Params] | None = None,
                *, repairs: RepairsMatrix | None = None) -> list[dict[str, Any]]:
    """Oldindan e'lon qilingan sensitivity sweep (§4).

    `W_stab in {8,10,30,60,120} s` x `theta in {0.5,0.8,0.95}` -- XOM probe
    trace'lardan POST-HOC hisoblanadi, eksperiment QAYTA ISHGA TUSHIRILMAYDI.

    Sabab (§4): "siz `W` ni natija chiqishi uchun tanlagansiz" -- har qanday
    shu turdagi metrikaga birinchi hujum. Javob bitta raqam emas, BUTUN EGRI
    CHIZIQ. Shuning uchun §8 xom trace'larni saqlashni talab qiladi va shuning
    uchun bu funksiya xom trace'dan boshqa hech narsaga muhtoj emas.

    `W_stab` horizon'dan uzun bo'lsa (masalan 120 s ~75 s trial'da) oyna
    kesiladi va natija `vr=None` bo'ladi -- `False` EMAS. Aks holda sweep
    egri chizig'i horizon artefakti bo'lardi.
    """
    grid = list(grid) if grid is not None else sweep_grid()
    out: list[dict[str, Any]] = []
    for params in grid:
        payload, _eps = reduce_trial(trial, params, repairs=repairs)
        out.append({
            "derived": True,
            "reducer_version": REDUCER_VERSION,
            "preregistration_sections": ["4"],
            "w_stab_us": params.w_stab_us,
            "w_stab_s": params.w_stab_us / 1_000_000.0,
            "theta": params.theta,
            "vr": payload["vr"],
            "vr_any": payload["vr_any"],
            "vr_reason": payload["vr_reason"],
            "invalidators": payload["invalidators"],
            "provisional_invalidators": payload["provisional_invalidators"],
            "fr_a": payload["fr_a"],
            "disposition": payload["disposition"],
            "d_probe_us": payload["d_probe_us"],
            "d_probe_censored": payload["d_probe_censored"],
            "d_eff_us": payload["d_eff_us"],
            "time_to_vr_us": payload["time_to_vr_us"],
            "time_to_vr_censored": payload["time_to_vr_censored"],
            "r_ref": payload["r_ref"],
            "unverified_clauses": payload["unverified_clauses"],
        })
    return out


def sweep_is_complete(cells: Sequence[dict[str, Any]],
                      w_stab_s: Sequence[float] = W_STAB_SWEEP_S,
                      thetas: Sequence[float] = THETA_SWEEP) -> bool:
    """Sweep chiqishi TO'LIQ grid'ni qoplaydimi (§4)."""
    want = {(round(float(w), 6), round(float(t), 6))
            for w in w_stab_s for t in thetas}
    got = {(round(float(c["w_stab_s"]), 6), round(float(c["theta"]), 6))
           for c in cells}
    return want <= got


# --- selektorlar (eksklyuziya faqat NOMLANGAN bo'ladi) ----------------------


def select_primary(trial_records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Binar `P(VR)` maxrajiga kiradigan trial'lar -- `SET_BINARY_DENOMINATOR`.

    §16.2(B): to'plam `(disposition, disposition_source)` JUFTI bilan
    aniqlanadi. `censored` + `down_at_horizon` KIRADI (`VR = false`,
    kuzatilgan no'l-hodisa); `censored` + `probe_gap` KIRMAYDI (natija
    kuzatilmadi, §4).

    §20.2: va `vr` ANIQLANGAN bo'lishi SHART. `vr is None` -- sababi nima
    bo'lishidan qat'i nazar -- chiqariladi (`no_episode`,
    `r_ref_unavailable`, `throughput_unmeasurable`, `window_truncated`).
    Ikki shart KONYUNKSIYA: biri ikkinchisining o'rnini bosmaydi.

    Eksklyuziya JIMGINA bo'lmasligi uchun bu selektor NOMLANGAN va alohida:
    reducer hech qachon trial'ni chiqishdan olib tashlamaydi.
    """
    return [r for r in trial_records
            if enters_primary_denominator(r.get("disposition"),
                                          r.get("disposition_source"),
                                          vr=r.get("vr"),
                                          vr_reason=r.get("vr_reason"))]


def select_survival(trial_records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Kaplan-Meier / log-rank va loop-rate uchun (§6.2: censored KIRADI).

    §16 BU TO'PLAMNI O'ZGARTIRMAGAN (§16.4: `("complete", "censored")` --
    "to'g'ri"). §6.2 DAVOMIYLIKNI `T_trial` da censor qiladi, binar natijani
    emas, shuning uchun `probe_gap` ham, `down_at_horizon` ham bu yerda
    censored davomiylik sifatida qoladi -- `disposition_source` bu to'plamga
    TA'SIR QILMAYDI.

    §20.3 BITTA chekinish qo'shdi -- `no_episode` IKKALA to'plamdan ham
    chiqadi (v1.5 dan beri birinchi shunday kategoriya), chunki u yerda
    hodisa KUTILAYOTGAN emas edi va censored kuzatuv chiqarish yolg'on
    da'vo bo'lardi. Qoida `enters_survival_set()` da, YAGONA joyda.
    """
    return [r for r in trial_records
            if enters_survival_set(r.get("disposition"), r.get("vr_reason"))]


def disposition_counts(trial_records: Iterable[dict[str, Any]]) -> dict[str, int]:
    """§12: yuqori eksklyuziya darajasi O'ZI natija -- yashirilmaydi."""
    counts = {d: 0 for d in DISPOSITIONS}
    for r in trial_records:
        d = str(r.get("disposition"))
        counts[d] = counts.get(d, 0) + 1
    return counts


def disposition_source_counts(trial_records: Iterable[dict[str, Any]]
                              ) -> dict[str, int]:
    """§16.2(B): juft bilan aniqlangan to'plam juft bo'yicha HISOBOT talab qiladi.

    `disposition_counts` o'zi yetarli emas: u `censored:probe_gap` ni
    `censored:down_at_horizon` dan ajratmaydi, holbuki ularning biri
    maxrajga kiradi, ikkinchisi yo'q. Kalit -- `"<disposition>:<source>"`.
    """
    counts: dict[str, int] = {}
    for r in trial_records:
        key = f"{r.get('disposition')}:{r.get('disposition_source')}"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def cell_key(record: dict[str, Any]) -> str:
    """`(arm x pressure)` yacheyka kaliti (§17.4(4), §9.3 panjarasi).

    `None` -> `"None"`: yacheykani YO'Q qilib tashlamaydi, chunki `arm` yoki
    `pressure_band` yozilmagan trial ham hisobotda KO'RINISHI shart (4-qoida:
    trial tashlanmaydi).
    """
    return f"{record.get('arm')}|{record.get('pressure_band')}"


def _cell_rows(trial_records: Sequence[dict[str, Any]]
               ) -> dict[str, list[dict[str, Any]]]:
    cells: dict[str, list[dict[str, Any]]] = {}
    for r in trial_records:
        cells.setdefault(cell_key(r), []).append(r)
    return {k: cells[k] for k in sorted(cells)}


def _count_by(values: Iterable[Any]) -> dict[str, int]:
    """Tartiblangan sanoq lug'ati (deterministik chiqish -- 2-qoida)."""
    out: dict[str, int] = {}
    for v in values:
        out[str(v)] = out.get(str(v), 0) + 1
    return dict(sorted(out.items()))


def window_containment_counts(trial_records: Iterable[dict[str, Any]]
                              ) -> dict[str, int]:
    """§17.3: uch holat (a)/(b)/(c) + ikki aniqlanmagan holat bo'yicha sanoq.

    Yopiq enum ustida nol bilan to'ldiriladi, demak holat KO'RINMAY
    qolmaydi: nol -- "o'lchangan no'l", kalit yo'qligi emas.
    """
    counts = {s: 0 for s in WINDOW_CONTAINMENTS}
    for r in trial_records:
        s = str(r.get("window_containment"))
        counts[s] = counts.get(s, 0) + 1
    return counts


def exclusion_report(trial_records: Sequence[dict[str, Any]], *,
                     analysis_set: str) -> dict[str, Any]:
    """Bitta analiz to'plami uchun eksklyuziya hisoboti -- NOMI BILAN (§16.4).

    §12: *"Yuqori eksklyuziya darajasi o'zi natija -- yashirilmaydi."*
    §16.4: *"Har qanday maqolada, jadvalda yoki `analysis.json` da berilgan
    eksklyuziya darajasi QAYSI to'plam ustida hisoblanganini NOMLASHI
    SHART ... Nomlanmagan eksklyuziya darajasi takrorlanuvchi emas va natija
    sifatida berilmaydi."*

    Shuning uchun qaytarilgan obyektning O'ZIDA `analysis_set` kaliti bor:
    daraja hisobotdan nusxalab olinsa ham nomi birga ketadi.

    `rate` -- `None` bo'lmaydi faqat `n_total > 0` bo'lsa; `n_total == 0` da
    `None` ("o'lchanmadi"), `0.0` EMAS ("o'lchangan no'l") -- modulning
    `None`/`0` disiplinasi.
    """
    if analysis_set not in (SET_BINARY_DENOMINATOR, SET_SURVIVAL):
        raise ReductionError(f"nomsiz/noma'lum analiz to'plami: {analysis_set!r}")

    # §17.4(4): daraja `(arm x pressure)` yacheykasi bo'yicha HAM beriladi --
    # agregat daraja `P2` da to'plangan eksklyuziyani YASHIRADI, holbuki
    # aynan o'sha to'planish NATIJA ("dizayn qiziqtirgan yacheykani o'lchay
    # olmadi"). Rekursiya bitta bo'g'in: har yacheyka o'z `by_cell` ini
    # bermaydi. Agregat va yacheyka sanoqlari BITTA funksiyadan keladi,
    # demak ular bir-biridan ajralib keta olmaydi.
    by_cell: dict[str, Any] = {}
    for key, rows in _cell_rows(trial_records).items():
        sub = _exclusion_counts(rows, analysis_set)
        sub.update({"analysis_set": analysis_set, "cell": key,
                    "arm": rows[0].get("arm"),
                    "pressure_band": rows[0].get("pressure_band")})
        by_cell[key] = sub

    out = _exclusion_counts(trial_records, analysis_set)
    out.update({"analysis_set": analysis_set, "by_cell": by_cell})
    return out


def survival_exclusion_reason(disposition: str | None,
                              disposition_source: str | None,
                              vr_reason: str | None = None) -> str | None:
    """Survival to'plamidan chiqarilish sababi, NOMLANGAN holda (§16.4, §20.3)."""
    if enters_survival_set(disposition, vr_reason):
        return None
    if vr_reason in SURVIVAL_EXCLUDED_VR_REASONS:
        # §20.3: sabab `disposition` EMAS -- `complete:derived` deb yozish
        # chalg'ituvchi bo'lardi, chunki trial `disposition` i sababli
        # chiqmaydi, PREDIKAT INSTANSIYALANMAGANI sababli chiqadi.
        return f"vr_undetermined:{vr_reason}"
    return f"{disposition}:{disposition_source}"


def _exclusion_counts(rows: Sequence[dict[str, Any]],
                      analysis_set: str) -> dict[str, Any]:
    """Bitta yacheyka uchun sanoq (yordamchi -- `exclusion_report` ichida)."""
    inc = (select_primary(rows) if analysis_set == SET_BINARY_DENOMINATOR
           else select_survival(rows))
    n_total, n_inc = len(rows), len(inc)
    n_exc = n_total - n_inc
    inc_ids = {id(r) for r in inc}
    reasons: dict[str, int] = {}
    for r in rows:
        if id(r) in inc_ids:
            continue
        reason = (primary_exclusion_reason(r.get("disposition"),
                                           r.get("disposition_source"),
                                           vr=r.get("vr"),
                                           vr_reason=r.get("vr_reason"))
                  if analysis_set == SET_BINARY_DENOMINATOR
                  else survival_exclusion_reason(r.get("disposition"),
                                                 r.get("disposition_source"),
                                                 r.get("vr_reason")))
        reasons[str(reason)] = reasons.get(str(reason), 0) + 1
    return {
        "n_total": n_total,
        "n_included": n_inc,
        "n_excluded": n_exc,
        "exclusion_rate": (n_exc / n_total) if n_total else None,
        "reasons": dict(sorted(reasons.items())),
    }


def injector_effectiveness_report(trial_records: Sequence[dict[str, Any]]
                                  ) -> dict[str, Any]:
    """§20.3: `no_episode` darajasi -- INJEKTOR SAMARADORLIGI metrikasi.

    §9.3 har trial'ga AYNAN BITTA injeksiya beradi, P1 ning yagona fault'i
    `clean_crash` (`exit(1)` / `SIGKILL` / `SIGSEGV`), va SUT o'ldirilsa
    socket contract buzilishi SHART. Demak muzlatilgan P1 dizaynida
    `no_episode` NATIJA emas, **injeksiya ishlamaganini** bildiradi -- trial
    NUQSONI.

    §20.3 ning muzlatilgan hisobot qoidasi: daraja `(arm x pressure)`
    bo'yicha ALOHIDA beriladi, INJEKTOR SAMARADORLIGI deb nomlanadi, va
    boshqa eksklyuziyalar bilan BIRLASHTIRILMAYDI. Nolga teng bo'lmagan
    daraja PILOTNI GATE QILADI, chunki §9.2 ning to'rtala mexanizmi ham
    injeksiyaning ishlashini nazarda tutadi.

    Shuning uchun obyekt `metric` nomini VA `must_not_pool_with` ni
    ko'taradi: birlashtirish taqiqi MASHINA O'QIY OLADIGAN shaklda, izohda
    emas.
    """
    def counts(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
        n_total = len(rows)
        n_ne = sum(1 for r in rows
                   if r.get("vr_reason") == VR_REASON_NO_EPISODE)
        return {
            "n_total": n_total,
            "n_no_episode": n_ne,
            # `None` = o'lchanmadi (trial yo'q), `0.0` = o'lchangan no'l.
            "no_episode_rate": (n_ne / n_total) if n_total else None,
            "injection_effective_rate": ((n_total - n_ne) / n_total
                                         if n_total else None),
            "gates_pilot": n_ne > 0,
        }

    by_cell: dict[str, Any] = {}
    for key, rows in _cell_rows(trial_records).items():
        sub = counts(rows)
        sub.update({"cell": key, "arm": rows[0].get("arm"),
                    "pressure_band": rows[0].get("pressure_band"),
                    "metric": METRIC_INJECTOR_EFFECTIVENESS,
                    "rate_denominator": "all_trials_in_cell"})
        by_cell[key] = sub

    out = counts(trial_records)
    out.update({
        "metric": METRIC_INJECTOR_EFFECTIVENESS,
        "rate_denominator": "all_trials_in_cell",
        "vr_reasons": [VR_REASON_NO_EPISODE],
        # §20.3: "boshqa eksklyuziyalar bilan birlashtirilmaydi".
        "must_not_pool_with": [METRIC_INSTRUMENTATION_LOSS],
        "excluded_from": [SET_BINARY_DENOMINATOR, SET_SURVIVAL],
        "by_cell": by_cell,
    })
    return out


def instrumentation_loss_report(trial_records: Sequence[dict[str, Any]]
                                ) -> dict[str, Any]:
    """§20.4(4): instrumentatsiya yo'qolishi -- `probe_gap` + 5-band o'lchanmagan.

    Bu sinfda savol TUG'ILDI, javob KUZATILMADI. §4 ning `probe_gap` i va
    §20.4 ning `r_ref_unavailable` / `throughput_unmeasurable` i bir xil
    epistemologik sinfda, shuning uchun BIRGA beriladi -- va `no_episode`
    bilan BIRLASHTIRILMAYDI, chunki u boshqa nuqson sinfi (injeksiya
    ishlamadi, §20.3).

    FARQ (§20.4(3)): bu sinf KM/log-rank ga KIRADI (hodisa kutilayotgan
    edi, faqat `D_probe` ning oxiri aniqlanmaydi -- haqiqiy right
    censoring), `no_episode` esa kirmaydi.
    """
    def counts(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
        n_total = len(rows)
        n_gap = sum(1 for r in rows if r.get("disposition_source")
                    in INSTRUMENTATION_LOSS_SOURCES)
        n_band5 = sum(1 for r in rows if r.get("vr_reason")
                      in INSTRUMENTATION_LOSS_VR_REASONS)
        n_loss = n_gap + n_band5
        return {
            "n_total": n_total,
            "n_probe_gap": n_gap,
            "n_band5_unmeasured": n_band5,
            "n_instrumentation_loss": n_loss,
            "instrumentation_loss_rate": (n_loss / n_total) if n_total else None,
        }

    by_cell: dict[str, Any] = {}
    for key, rows in _cell_rows(trial_records).items():
        sub = counts(rows)
        sub.update({"cell": key, "arm": rows[0].get("arm"),
                    "pressure_band": rows[0].get("pressure_band"),
                    "metric": METRIC_INSTRUMENTATION_LOSS,
                    "rate_denominator": "all_trials_in_cell"})
        by_cell[key] = sub

    out = counts(trial_records)
    out.update({
        "metric": METRIC_INSTRUMENTATION_LOSS,
        "rate_denominator": "all_trials_in_cell",
        "vr_reasons": sorted(INSTRUMENTATION_LOSS_VR_REASONS),
        "disposition_sources": sorted(INSTRUMENTATION_LOSS_SOURCES),
        "must_not_pool_with": [METRIC_INJECTOR_EFFECTIVENESS],
        "excluded_from": [SET_BINARY_DENOMINATOR],   # survival'ga KIRADI
        "by_cell": by_cell,
    })
    return out


def window_containment_report(trial_records: Sequence[dict[str, Any]]
                              ) -> dict[str, Any]:
    """§17.4(4): oyna eksklyuziyasining `(arm x pressure)` bo'yicha darajasi.

    §17.4(4): *"Ularning darajasi `(arm x pressure)` yacheykasi bo'yicha
    ALOHIDA beriladi, va §16.4 ning nomlash qoidasi qo'llanadi. **`P2`
    yacheykasida to'plangan yuqori daraja -- o'zi NATIJA:** u "dizayn
    qiziqtirgan yacheykani o'lchay olmadi" degan ma'noni beradi, va §12 ning
    "Yuqori eksklyuziya darajasi o'zi natija -- yashirilmaydi" qoidasi ostida
    yashirilmaydi."*

    Shuning uchun obyekt O'ZIDA ikkita nomni ko'taradi: qaysi ANALIZ
    TO'PLAMIDAN chiqarilgani (`analysis_set`) va daraja qaysi MAXRAJ ustida
    hisoblangani (`rate_denominator`). §16.4 nomsiz darajani natija deb
    bermaslikni talab qiladi, demak ikkisi ham majburiy.

    `not_evaluated` ALOHIDA sanaladi: u eksklyuziya EMAS, balki `T_h`
    o'lchanmagani -- ya'ni §17.4(5) validator sharti tekshirilmagani.
    Nol bo'lmagan `n_not_evaluated` -- jim qolmasligi kerak bo'lgan fakt.
    """
    sources = (WINDOW_CONTAINMENT_SOURCE[WINDOW_PAST_PRESSURE],
               WINDOW_CONTAINMENT_SOURCE[WINDOW_PAST_HORIZON])

    def counts(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
        n_total = len(rows)
        per_src = {s: sum(1 for r in rows
                          if r.get("disposition_source") == s) for s in sources}
        n_win = sum(per_src.values())
        return {
            "n_total": n_total,
            "n_window_past_pressure": per_src[sources[0]],
            "n_window_past_horizon": per_src[sources[1]],
            "n_window_excluded": n_win,
            "window_exclusion_rate": (n_win / n_total) if n_total else None,
            "n_inside_hold": sum(1 for r in rows
                                 if r.get("window_containment")
                                 == WINDOW_INSIDE_HOLD),
            "n_not_evaluated": sum(1 for r in rows
                                   if r.get("window_containment")
                                   == WINDOW_NOT_EVALUATED),
            "n_no_t_up": sum(1 for r in rows
                             if r.get("window_containment") == WINDOW_NO_T_UP),
        }

    by_cell: dict[str, Any] = {}
    for key, rows in _cell_rows(trial_records).items():
        sub = counts(rows)
        sub.update({"cell": key, "arm": rows[0].get("arm"),
                    "pressure_band": rows[0].get("pressure_band"),
                    "analysis_set": SET_BINARY_DENOMINATOR,
                    "rate_denominator": "all_trials_in_cell"})
        by_cell[key] = sub

    out = counts(trial_records)
    out.update({
        "analysis_set": SET_BINARY_DENOMINATOR,
        "rate_denominator": "all_trials_in_cell",
        "disposition_sources": list(sources),
        "by_cell": by_cell,
    })
    return out


# --- run reduksiyasi va yozish ---------------------------------------------


@dataclass
class ReductionOutput:
    trials: list[dict[str, Any]]
    episodes: list[dict[str, Any]]
    sweep: list[dict[str, Any]]
    summary: dict[str, Any]


def reduce_run(run: RawRun, params: Params | None = None, *,
               sweep: bool = False,
               grid: Sequence[Params] | None = None,
               repairs: RepairsMatrix | None = None) -> ReductionOutput:
    """Butun run'ni reduksiya qiladi.

    STRUKTURAVIY KAFOLAT: `n_trials_in == n_trials_out`. Recovery bo'lmagan
    trial'ni tashlash (§6.2 dagi klassik yashirin bias) shu tekshiruv bilan
    IMKONSIZ qilinadi -- mos kelmasa `ReductionError`.
    """
    params = params or Params()
    trials = split_trials(run)
    out_trials: list[dict[str, Any]] = []
    out_eps: list[dict[str, Any]] = []
    out_sweep: list[dict[str, Any]] = []

    for t in trials:
        payload, eps = reduce_trial(t, params, repairs=repairs)
        payload["__trial_id__"] = t.trial_id
        payload["__block_index__"] = t.block_index
        out_trials.append(payload)
        for e in eps:
            d = e.as_dict()
            d.update({"derived": True, "reducer_version": REDUCER_VERSION,
                      "preregistration_sections": ["4", "5", "6"],
                      "params": params.as_dict(),
                      "__trial_id__": t.trial_id,
                      "__block_index__": t.block_index})
            out_eps.append(d)
        if sweep:
            for cell in sweep_trial(t, grid, repairs=repairs):
                cell["__trial_id__"] = t.trial_id
                cell["__block_index__"] = t.block_index
                out_sweep.append(cell)

    if len(out_trials) != len(trials):
        raise ReductionError(
            f"trial yo'qoldi: kirish {len(trials)}, chiqish {len(out_trials)}")

    meta = run.run_meta or {}
    primary_trials = select_primary(out_trials)
    survival_trials = select_survival(out_trials)
    # §16.4: IKKI to'plam -> IKKI eksklyuziya darajasi, va har biri o'z nomini
    # ko'taradi. Nomsiz daraja natija sifatida BERILMAYDI.
    excl_binary = exclusion_report(out_trials,
                                   analysis_set=SET_BINARY_DENOMINATOR)
    excl_survival = exclusion_report(out_trials, analysis_set=SET_SURVIVAL)
    excl_window = window_containment_report(out_trials)
    # §20.3 / §20.4(4): IKKI BOSHQA nuqson sinfi, IKKI ALOHIDA hisobot.
    # Ular bir-biriga qo'shilmaydi -- har biri `must_not_pool_with` ni
    # o'zida ko'taradi.
    injector = injector_effectiveness_report(out_trials)
    instr_loss = instrumentation_loss_report(out_trials)
    summary = {
        "derived": True,
        "reducer_version": REDUCER_VERSION,
        "params": params.as_dict(),
        "n_trials_in": len(trials),
        "n_trials_out": len(out_trials),
        "n_episodes": len(out_eps),
        "n_sweep_cells": len(out_sweep),
        "disposition_counts": disposition_counts(out_trials),
        # §16.2(B): juft bo'yicha hisobot -- `censored:probe_gap` va
        # `censored:down_at_horizon` bir xil `disposition` ostida yashirinmaydi.
        "disposition_source_counts": disposition_source_counts(out_trials),
        "n_primary": len(primary_trials),
        "n_survival": len(survival_trials),

        # --- §16.4: IKKI EKSKLYUZIYA DARAJASI, IKKALASI HAM NOMLANGAN ------
        # Nomlar `SET_BINARY_DENOMINATOR` / `SET_SURVIVAL` konstantalaridan
        # keladi, demak maydon nomi bilan obyekt ichidagi `analysis_set` nomi
        # AJRALIB KETMAYDI. Ikkalasi bir funksiyadan (`exclusion_report`)
        # hisoblanadi, demak ularning ta'rifi ham ajralib keta olmaydi.
        "exclusions": {
            SET_BINARY_DENOMINATOR: excl_binary,
            SET_SURVIVAL: excl_survival,
        },
        # Skalyar sifatida ko'chirib olinadigan daraja HAM nomni o'z maydon
        # nomida ko'taradi -- §16.4: "Nomlanmagan eksklyuziya darajasi
        # takrorlanuvchi emas va natija sifatida berilmaydi."
        "exclusion_rate_binary_pvr_denominator": excl_binary["exclusion_rate"],
        "exclusion_rate_survival_analysis_set": excl_survival["exclusion_rate"],

        # --- §17.4(4): oyna eksklyuziyasi, `(arm x pressure)` bo'yicha -----
        # `P2` da to'plangan yuqori daraja O'ZI NATIJA, demak u agregat
        # ichida yashirilmaydi: `by_cell` har yacheyka uchun alohida daraja
        # beradi va har biri `analysis_set` + `rate_denominator` nomlarini
        # ko'taradi (§16.4).
        "window_containment": excl_window,
        "window_exclusion_rate_binary_pvr_denominator":
            excl_window["window_exclusion_rate"],
        "window_containment_counts": window_containment_counts(out_trials),
        # §17.4(5): `T_h` o'lchanmagan trial'da oyna sharti TEKSHIRILMAGAN.
        # Bu eksklyuziya emas, lekin jim qolmasligi kerak -- validator
        # shartini bajarib bo'lmaydigan trial'lar soni.
        "n_window_containment_not_evaluated": excl_window["n_not_evaluated"],

        # --- §20.3 / §20.4(4): IKKI SINF, HECH QACHON POOL QILINMAYDI -----
        "injector_effectiveness": injector,
        "instrumentation_loss": instr_loss,
        "no_episode_rate_injector_effectiveness": injector["no_episode_rate"],
        "instrumentation_loss_rate": instr_loss["instrumentation_loss_rate"],
        # §20.3: nolga teng bo'lmagan `no_episode` darajasi PILOTNI GATE
        # QILADI -- bu flag o'sha hukmni mashina o'qiydigan qiladi.
        "pilot_gated_by_injector_effectiveness": injector["gates_pilot"],

        "recovered_within_horizon": sum(1 for r in out_trials if r["vr"] is True),
        "vr_undetermined": sum(1 for r in out_trials if r["vr"] is None),
        # §20.2: `vr = None` ning sabablari BUTUN run bo'yicha -- maxrajdan
        # chiqarilgach ma'lumot yo'qolmasligi uchun. `no_episode` shu yerda
        # ko'rinadi (va injektor hisobotida alohida).
        "vr_undetermined_counts_by_reason": _count_by(
            r["vr_reason"] for r in out_trials if r["vr"] is None),
        # §20.2 dan keyin bu son STRUKTURAVIY ravishda NOL: aniqlanganlik
        # maxrajning ZARUR sharti, demak `vr = None` trial maxrajga
        # kira OLMAYDI. Shuning uchun u endi diagnostika ham, ochiq
        # savolning ko'rsatkichi ham emas -- §20.2 ning kuchda ekanini
        # tekshiradigan TIRIK INVARIANT. Nolga teng bo'lmasa, qoida
        # buzilgan.
        #
        # Saqlanadi, chunki uni hisoblash arzon va u bitta sonda butun
        # §16.2(B) + §17.4 + §20.2 zanjirini tekshiradi.
        "vr_undetermined_in_binary_denominator": sum(
            1 for r in primary_trials if r["vr"] is None),
        "vr_undetermined_in_binary_denominator_by_reason": _count_by(
            (r["vr_reason"] for r in primary_trials if r["vr"] is None)),
        # §6.2: har jadvalda "T_trial ichida recovered: k/n" beriladi.
        # `recovered_k_of_n` -- binar maxraj ustida (§10.1); §16.4 ga ko'ra
        # `k/n` jadvallari ANALIZ TO'PLAMI ustida ham beriladi, shuning uchun
        # ikkinchisi alohida va NOMLANGAN maydonda.
        "recovered_k_of_n_set": SET_BINARY_DENOMINATOR,
        "recovered_k_of_n": [sum(1 for r in primary_trials if r["vr"] is True),
                             len(primary_trials)],
        "recovered_k_of_n_analysis_set": [
            sum(1 for r in survival_trials if r["vr"] is True),
            len(survival_trials)],
        "fr_a_true": sum(1 for r in out_trials if r["fr_a"] is True),
        "fr_b_computed": any(r["fr_b"]["computed"] for r in out_trials),
        "sweep_complete": (sweep_is_complete(out_sweep) if sweep else False),
        "raw_schema_version": SCHEMA_VERSION,
        "preregistration_sha256": meta.get("preregistration_sha256"),
        "raw_run_id": meta.get("run_id"),
        "raw_session_id": meta.get("session_id"),
        "sources": list(run.sources),
    }
    return ReductionOutput(out_trials, out_eps, out_sweep, summary)


def _assert_not_raw(out_path: str, inputs: Sequence[str]) -> None:
    """XOM fayl HECH QACHON derived field bilan tahrirlanmaydi.

    Derived ma'lumot qayta yaratiladi, xom -- yo'q (§7 reproducibility:
    `datasets/` append-only, xom hech qachon ustiga yozilmaydi).
    """
    op = os.path.realpath(out_path)
    for i in inputs:
        if os.path.realpath(i) == op:
            raise ReductionError(
                f"chiqish yo'li xom kirish fayli bilan bir xil: {out_path!r} -- "
                "xom ma'lumot ustiga yozilmaydi")


def write_output(out: ReductionOutput, out_dir: str, run: RawRun,
                 *, prefix: str = "") -> dict[str, str]:
    """Derived record'larni ALOHIDA fayllarga yozadi."""
    os.makedirs(out_dir, exist_ok=True)
    meta = run.run_meta or {}
    run_id = str(meta.get("run_id") or "unknown")
    session_id = str(meta.get("session_id") or "unknown")
    boot_id = str(meta.get("boot_id") or "unknown")
    # boot_id run_meta'dan olinadi -- `read_boot_id()` /proc ni o'qiydi va
    # reducer PUR bo'lishi kerak.
    em = Emitter("reduce", run_id, session_id, boot_id=boot_id)

    paths = {
        "episodes": os.path.join(out_dir, f"{prefix}episodes.jsonl"),
        "trials": os.path.join(out_dir, f"{prefix}trials.jsonl"),
        "summary": os.path.join(out_dir, f"{prefix}reduction_summary.jsonl"),
    }
    if out.sweep:
        paths["sweep"] = os.path.join(out_dir, f"{prefix}sweep.jsonl")
    for p in paths.values():
        _assert_not_raw(p, run.sources)

    def emit(path: str, rt: str, rows: Iterable[dict[str, Any]]) -> None:
        with JsonlWriter(path) as w:
            for row in rows:
                row = dict(row)
                tid = row.pop("__trial_id__", None)
                bidx = row.pop("__block_index__", None)
                w.write(em.record(rt, row, stream=rt, trial_id=tid,
                                  block_index=bidx))

    emit(paths["episodes"], DRT_EPISODE, out.episodes)
    emit(paths["trials"], DRT_TRIAL, out.trials)
    if "sweep" in paths:
        emit(paths["sweep"], DRT_SWEEP, out.sweep)
    emit(paths["summary"], DRT_SUMMARY, [out.summary])
    return paths


# --- CLI --------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="REVIX offline reducer (PREREGISTRATION.md §4, §5, §6)")
    ap.add_argument("--jsonl", action="append", default=[], required=False,
                    help="xom JSONL fayli; takrorlanadi")
    ap.add_argument("--probe-csv", action="append", default=[],
                    help="probe_sample CSV fayli; takrorlanadi")
    ap.add_argument("--out-dir", required=True, help="derived record'lar katalogi")
    ap.add_argument("--w-stab", type=float, default=W_STAB_PILOT_US / 1e6,
                    help="stabilizatsiya oynasi, sekund (default: pilot 8 s)")
    ap.add_argument("--theta", type=float, default=THETA_DEFAULT)
    ap.add_argument("--p-min", type=float, default=P_MIN_DEFAULT)
    ap.add_argument("--probe-period-ms", type=float, default=P_US / 1000.0)
    ap.add_argument("--k-f", type=int, default=K_F)
    ap.add_argument("--sweep", action="store_true",
                    help="oldindan e'lon qilingan W_stab x theta sweep'ini chiqaradi")
    ap.add_argument("--prefix", default="")
    ap.add_argument("--json", action="store_true",
                    help="reduksiya xulosasini stdout'ga JSON qilib yozadi")
    args = ap.parse_args(argv)

    if not args.jsonl:
        ap.error("kamida bitta --jsonl kerak")

    params = Params(
        w_stab_us=int(round(args.w_stab * 1_000_000)),
        theta=args.theta,
        p_min=args.p_min,
        probe_period_us=int(round(args.probe_period_ms * 1000)),
        k_f=args.k_f,
    )
    run = RawRun.load(args.jsonl, args.probe_csv)
    out = reduce_run(run, params, sweep=args.sweep)
    paths = write_output(out, args.out_dir, run, prefix=args.prefix)
    if args.json:
        json.dump({"summary": out.summary, "paths": paths}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        s = out.summary
        print(f"trial: {s['n_trials_out']}/{s['n_trials_in']}  "
              f"epizod: {s['n_episodes']}  sweep: {s['n_sweep_cells']}")
        print(f"disposition: {s['disposition_counts']}")
        print(f"disposition:source: {s['disposition_source_counts']}")
        print(f"T_trial ichida recovered [{s['recovered_k_of_n_set']}]: "
              f"{s['recovered_k_of_n'][0]}/{s['recovered_k_of_n'][1]}  "
              f"(VR aniqlanmagan: {s['vr_undetermined']}, "
              f"maxrajda: {s['vr_undetermined_in_binary_denominator']})")
        print(f"T_trial ichida recovered [{SET_SURVIVAL}]: "
              f"{s['recovered_k_of_n_analysis_set'][0]}"
              f"/{s['recovered_k_of_n_analysis_set'][1]}")
        # §16.4: eksklyuziya darajasi HAR DOIM to'plam nomi bilan chiqadi.
        for set_name in (SET_BINARY_DENOMINATOR, SET_SURVIVAL):
            e = s["exclusions"][set_name]
            print(f"eksklyuziya [{e['analysis_set']}]: "
                  f"{e['n_excluded']}/{e['n_total']} "
                  f"(rate={e['exclusion_rate']})  sabablar: {e['reasons']}")
        # §17.4(4): oyna eksklyuziyasi yacheyka bo'yicha -- `P2` da
        # to'planishi O'ZI NATIJA, demak agregat bilan birga chiqadi.
        w = s["window_containment"]
        print(f"oyna joylashuvi: {s['window_containment_counts']}  "
              f"(tekshirilmagan: {s['n_window_containment_not_evaluated']})")
        print(f"oyna eksklyuziyasi [{w['analysis_set']} / "
              f"{w['rate_denominator']}]: {w['n_window_excluded']}"
              f"/{w['n_total']} (rate={w['window_exclusion_rate']})")
        for key, c in w["by_cell"].items():
            print(f"  {key}: past_pressure={c['n_window_past_pressure']} "
                  f"past_horizon={c['n_window_past_horizon']} "
                  f"/{c['n_total']} (rate={c['window_exclusion_rate']})")
        # §20.3 / §20.4(4): IKKI SINF ALOHIDA chiqadi va QO'SHILMAYDI.
        inj, il = s["injector_effectiveness"], s["instrumentation_loss"]
        print(f"[{inj['metric']}] no_episode: {inj['n_no_episode']}"
              f"/{inj['n_total']} (rate={inj['no_episode_rate']})  "
              f"pilot gate: {'GATED' if inj['gates_pilot'] else 'ok'}")
        for key, c in inj["by_cell"].items():
            print(f"  {key}: no_episode={c['n_no_episode']}/{c['n_total']} "
                  f"(rate={c['no_episode_rate']})")
        print(f"[{il['metric']}] probe_gap={il['n_probe_gap']} "
              f"band5_unmeasured={il['n_band5_unmeasured']} "
              f"/{il['n_total']} (rate={il['instrumentation_loss_rate']})")
        print(f"  (bu ikki sinf QO'SHILMAYDI -- §20.3/§20.4: "
              f"{inj['metric']} != {il['metric']})")
        print(f"vr aniqlanmagan sabablari: "
              f"{s['vr_undetermined_counts_by_reason']}  "
              f"maxrajda (§20.2 invarianti, 0 bo'lishi shart): "
              f"{s['vr_undetermined_in_binary_denominator']}")
        for k, v in paths.items():
            print(f"  {k}: {v}")
    return 0


# --- xom record kontrakti (mahalliy ta'rif) ---------------------------------
#
# `revix/schema.py` envelope va yozuvchilarni beradi, LEKIN record turlarini
# ta'riflamaydi. PREREGISTRATION.md da ham "§8 data schema" yo'q (§8 --
# confound nazorati). Shuning uchun reducer o'qiydigan kontrakt SHU YERDA
# mahalliy ta'riflanadi va markazda yarashtirilishi kerak.
RAW_CONTRACT: dict[str, tuple[str, ...]] = {
    RT_RUN_META: ("git_dirty", "run_mode", "preregistration_sha256", "rng_seed"),
    RT_TRIAL_BEGIN: ("trial_id", "block_index", "arm", "pressure_band",
                     "fault_class", "mono_us"),
    RT_TRIAL_END: ("trial_id", "disposition", "mono_us"),
    RT_PROBE: ("trial_id", "seq", "mono_us_send", "mono_us_recv", "outcome",
               "progress", "invocation_id_seen", "pid_seen", "rt_us"),
    RT_ACTION: ("trial_id", "action_id", "action_class", "mono_us",
                "policy_delay_us", "deferred"),
    RT_ACTOR_SIGNAL: ("trial_id", "mono_us", "source", "success"),
    RT_UNIT_STATE: ("trial_id", "mono_us", "active_state", "result",
                    "n_restarts", "invocation_id",
                    "active_enter_ts_mono_us", "active_exit_ts_mono_us"),
    RT_CGROUP_EVENTS: ("trial_id", "mono_us", "scope", "oom_kill"),
    RT_GUARD_EVENT: ("mono_us", "reason", "action"),
    RT_FAULT_INJECT: ("trial_id", "kind", "mono_us_before_call",
                      "mono_us_after_call"),
    RT_FAULT_EFFECTIVE: ("trial_id", "mono_us", "source"),
    RT_BASELINE_WINDOW: ("trial_id", "mono_us_begin", "mono_us_end"),
    RT_ACTION_DEFER: ("trial_id", "action_id", "mono_us", "reason"),
}


if __name__ == "__main__":
    sys.exit(main())
