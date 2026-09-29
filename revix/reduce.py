"""REVIX offline reducer -- xom record'lardan derived metrikalar.

PREREGISTRATION.md ni amalga oshiradi:
  * §1  -- barcha davomiylik CLOCK_MONOTONIC mikrosekundda
  * §4  -- Verified Recovery (VR), yettita band, yopiq invalidator enum,
           sensitivity sweep
  * §5  -- FR-A (birlamchi, oracle-free) va FR-B (ikkilamchi, matritsaga nisbatan)
  * §6  -- uchta downtime o'lchovi, right censoring, latency qoidalari
  * §12 -- trial disposition yopiq enum

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
     esa faqat NOMLANGAN selektorlar (`select_primary`) orqali va `disposition`
     qayd etilgan holda bo'ladi.
  5. **PSI hech qanday ta'rifga kirmaydi** (§5 sirkulyarlik kafolati). Bu modul
     PSI qiymatlarini O'QIMAYDI ham: VR, FR va downtime ta'riflari PSI'ga
     bog'liq bo'lsa, "PSI gating FR ni kamaytiradi" tavtologiyaga aylanadi.
     PSI faqat prediktor/kovariata -- u tahlil bosqichida, ALOHIDA qo'shiladi.
  6. **Throughput bandi (§4.5) o'lchanmasa, VR TASDIQLANMAYDI.** Throughput
     bandi VR ni process-liveness'dan ajratadigan yagona narsa. Shuning uchun
     `R_ref` yoki oyna throughput'i o'lchanmasa natija `vr=True` emas,
     `vr=None` (aniqlanmagan) bo'ladi. Aks holda ma'lumot yetishmovchiligi
     jimgina liveness-only VR ga qulardi.

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

# Birlamchi analizga kiradigan disposition (§12).
PRIMARY_DISPOSITIONS = ("complete",)
# Kaplan-Meier / log-rank va loop-rate ga kiradigan disposition (§6.2):
# censored trial'lar KIRADI -- ularni tashlash tez ishdan chiqadigan arm'ni
# chiroyli ko'rsatadigan yashirin bias.
SURVIVAL_DISPOSITIONS = ("complete", "censored")


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


def derive_disposition(trial: Trial, gaps: list[dict[str, Any]],
                       down_at_horizon: bool) -> tuple[str, str, bool]:
    """Har trial'ga AYNAN BITTA disposition (§12) -- jimgina eksklyuziya yo'q.

    Ustunlik tartibi (reducer avtoritetligi faqat OBYEKTIV log faktlarida):
      1. `aborted_guard`   -- guard trip qilgan (log fakt);
      2. xom `contaminated` / `washout_timeout` / `harness_error` saqlanadi --
         bu holatlarni faqat harness biladi;
      3. `censored`        -- probe uzilishi > 2xP (§4) YOKI horizon down
                              holatda tugadi (§12);
      4. xom `censored`;
      5. `complete`.

    PROBE UZILISHI HECH QACHON `failed` EMAS (§4): instrumentatsiya yo'qolishi
    jimgina natijaga aylanmaydi.
    """
    raw = trial.disposition_raw
    conflict = False
    if trial.guard_events:
        final, src = "aborted_guard", "guard_event"
    elif raw in ("contaminated", "washout_timeout", "harness_error"):
        final, src = raw, "trial_end"
    elif gaps:
        final, src = "censored", "probe_gap"
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

    disposition, disp_src, disp_conflict = derive_disposition(
        trial, gaps, down_at_horizon)

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

    vr_first = episodes[0].vr if episodes else None
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
        "preregistration_sections": ["4", "5", "6", "12"],
        "arm": trial.arm,
        "pressure_band": trial.pressure_band,
        "params": params.as_dict(),

        "disposition": disposition,
        "disposition_raw": trial.disposition_raw,
        "disposition_source": disp_src,
        "disposition_conflict": disp_conflict,
        "included_in_primary": disposition in PRIMARY_DISPOSITIONS,
        "included_in_survival": disposition in SURVIVAL_DISPOSITIONS,
        "exclusion_reason": (None if disposition in PRIMARY_DISPOSITIONS
                             else disposition),

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

        "n_episodes": len(episodes),
        "episode_ids": [e.episode_id for e in episodes],
        "n_actions": len(trial.actions),
        "n_invocations": len(invs),
        "n_restarts_delta": n_restarts_delta,
        "loop_rate_per_s": loop_rate,
        "loop_detected": loop_detected,

        "vr": vr_first,
        "vr_any": vr_any,
        "vr_reason": episodes[0].vr_reason if episodes else "no_episode",
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
    """Birlamchi analizga kiradigan trial'lar (§12: faqat `complete`).

    Eksklyuziya JIMGINA bo'lmasligi uchun bu selektor NOMLANGAN va alohida:
    reducer hech qachon trial'ni chiqishdan olib tashlamaydi.
    """
    return [r for r in trial_records if r.get("disposition") in PRIMARY_DISPOSITIONS]


def select_survival(trial_records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Kaplan-Meier / log-rank va loop-rate uchun (§6.2: censored KIRADI)."""
    return [r for r in trial_records if r.get("disposition") in SURVIVAL_DISPOSITIONS]


def disposition_counts(trial_records: Iterable[dict[str, Any]]) -> dict[str, int]:
    """§12: yuqori eksklyuziya darajasi O'ZI natija -- yashirilmaydi."""
    counts = {d: 0 for d in DISPOSITIONS}
    for r in trial_records:
        d = str(r.get("disposition"))
        counts[d] = counts.get(d, 0) + 1
    return counts


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
    summary = {
        "derived": True,
        "reducer_version": REDUCER_VERSION,
        "params": params.as_dict(),
        "n_trials_in": len(trials),
        "n_trials_out": len(out_trials),
        "n_episodes": len(out_eps),
        "n_sweep_cells": len(out_sweep),
        "disposition_counts": disposition_counts(out_trials),
        "n_primary": len(select_primary(out_trials)),
        "n_survival": len(select_survival(out_trials)),
        "recovered_within_horizon": sum(1 for r in out_trials if r["vr"] is True),
        "vr_undetermined": sum(1 for r in out_trials if r["vr"] is None),
        # §6.2: har jadvalda "T_trial ichida recovered: k/n" beriladi.
        "recovered_k_of_n": [sum(1 for r in select_primary(out_trials)
                                 if r["vr"] is True),
                             len(select_primary(out_trials))],
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
        print(f"T_trial ichida recovered: "
              f"{s['recovered_k_of_n'][0]}/{s['recovered_k_of_n'][1]}  "
              f"(VR aniqlanmagan: {s['vr_undetermined']})")
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
