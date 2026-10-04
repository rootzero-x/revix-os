"""REVIX run validator -- analizdan OLDIN majburiy o'tadigan tekshiruv.

PREREGISTRATION.md §14.6 (validator invariantlari), §14.2 (envelope), §14.4
(majburliy maydonlar), §12 (disposition) va docs/architecture/04-driver-va-
analiz-shartnomasi.md (driver-contract/v1.1: §1 run katalogi, §1.3 driver
majburiyatlari, §4 maydon nomlari, §5 T_trial) ga tayanadi:

    "Validatsiyadan o'tmagan run analiz qilinmaydi."   (§14.6)

DIZAYN QOIDALARI (buzilmaydi):

  1. **FAIL-CLOSED.** O'qib bo'lmagan kirish va tekshiruv ICHIDAGI istisno --
     O'TMADI, hech qachon "o'tdi" emas. `validate_run` istisno ko'tarmaydi:
     istisno `validator_internal_error` xatosiga aylanadi; `main()` o'qib
     bo'lmagan kirishda 2 qaytaradi.
  2. **`None` = o'lchanmadi, kalit YO'Q = yozilmadi.** Ikkalasi ajratiladi:
     `governor: null` (WSL2 da cpufreq sysfs yo'q) -- halol "o'lchanmadi";
     `governor` kaliti yo'qligi -- driver uni yozmagan, ya'ni XATO.
  3. Har yangi invariant o'zini himoya qiladigan muzlatilgan bandni
     `NEGA:` qatorida ko'rsatadi. Bandsiz tekshiruv qo'shilmaydi.
  4. Mavjud tekshiruv zaiflashtirilmaydi va takrorlanmaydi: yangi tekshiruv
     faqat eskisi KO'RMAYDIGAN narsani ko'radi.
  5. `error` analizni to'sadi, `warning` to'sMAYDI. Bu model o'zgarmaydi.
  6. Validator xom faylga YOZMAYDI va tizimga TEGMAYDI: faqat o'qiydi.
  7. Takroriy buzilishlar (120 trial) guruhlanadi, lekin hech biri
     yashirilmaydi: `detail` da trial/qator ro'yxati qoladi.

TEKSHIRILADIGAN INVARIANTLAR (§14.6, 1-8 -- asl ro'yxat):
  1. `trial_begin_without_end` / `trial_end_without_begin`
  2. `disposition_missing` / `disposition_duplicate` / `disposition_unknown`
     -- har trial'ga AYNAN BITTA, yopiq enumdan (§12)
  3. `seq_gap` / `seq_duplicate` -- oqimda bo'shliq = jimgina yo'qolgan record
  4. `probe_gap` -- trial ichida > 2xP uzilish bo'lsa, trial `censored`
     bo'lishi SHART (§4)
  5. `boot_id_inconsistent` -- monotonic qiymatlar faqat bitta boot ichida
     taqqoslanadi (§1)
  6. `action_without_invocation_change` -- har `action` uchun invocation
     o'zgarishi yoki oshkora `defer`
  7. `git_dirty` -- confirmatory run uchun XATO, pilot uchun OGOHLANTIRISH (§7)
  8. `schema_version_unknown` -- har record uchun

DRIVER CHIQISHI UCHUN QO'SHIMCHA INVARIANTLAR (har birining NEGA'si o'z
funksiyasida):
  9.  envelope: `envelope_field_missing`, `stream_not_record_type`,
      `run_id_mismatch`, `session_id_mismatch`, `boot_id_run_meta_mismatch`
 10.  run_meta: `run_meta_field_missing/_null/_invalid`, `run_mode_*`,
      `units_show_*` (TIRIK dump), `schedule_*`, `rng_seed_mismatch`,
      `t_trial_*`
 11.  trial to'plami: `run_without_trials`, `trial_not_in_schedule`,
      `schedule_trial_missing`, `trial_schedule_mismatch`,
      `cell_count_mismatch`
 12.  trial ketma-ketligi: `trial_event_missing/_duplicate/_outside_window`,
      `baseline_*`, `fault_inject_bracket_invalid`, `action_before_fault`,
      `planned_timeline_*`, `trial_overhead_*`, `env_snapshot_missing`
 13.  maydonlar: `record_field_missing`, `actor_signal_success_invalid`,
      `unit_state_mono_not_recv`
 14.  probe: `probe_outcome_unknown`, `probe_progress_unreadable`,
      `probe_trial_unknown`, `probe_targets_mixed`, `trial_without_probes`,
      `probe_coverage_gap`, `prober_start_missing`
 15.  guard oqimi: `guard_start/stop_missing`, `guard_event_has_trial_id`,
      `guard_not_first/_last`, `guard_event_not_reflected`
 16.  `harness_error_not_reflected`
 17.  PREREGISTRATION.md v1.6 §17.4-5: `window_outside_hold_complete` (xato),
      `window_containment_not_evaluated` (ogohlantirish), `trial_timing_invalid`
 18.  YANGI (agent/pilot-ready, v1.11 dan keyin): `host_clock_discontinuity`
      -- ketma-ket yozish-lahzali soat namunalari orasida |Δreal − Δmono| > 1 s
      (host uyqusi; boot_id va guest generation uni ko'rmaydi). Yaroqlilik
      qoidasi, ta'rif emas -- metrika va disposition'ga tegmaydi.

Bu invariantlar pre-registration'ning ruhini bajaradi: o'lchov ma'lumotining
jimgina yo'qolishi natijaga aylanmasligi kerak.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import itertools
import json
import math
import os
import sys
import traceback
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Iterator

from .reduce import (
    P_US,
    PROBE_OUTCOMES,
    RT_ACTION,
    RT_ACTION_DEFER,
    RT_ACTOR_SIGNAL,
    RT_BASELINE_WINDOW,
    RT_CGROUP_EVENTS,
    RT_FAULT_EFFECTIVE,
    RT_FAULT_INJECT,
    RT_GUARD_EVENT,
    RT_PROBE,
    RT_RUN_META,
    RT_TRIAL_BEGIN,
    RT_TRIAL_END,
    RT_UNIT_STATE,
    Params,
    RawRun,
    _as_int,
    _as_str,
    WINDOW_NOT_EVALUATED,
    WINDOW_PAST_HORIZON,
    WINDOW_PAST_PRESSURE,
    W_STAB_PILOT_US,
    build_episodes,
    classify_window_containment,
    derive_disposition,
    fault_effective_us,
    probe_gaps,
    reference_throughput,
    split_trials,
)
from .schedule import (
    GUARD_SUSTAIN_WINDOW_S,
    HOLD_CAP_S,
    Factor,
    ScheduleError,
    TrialTimeline,
    make_schedule,
)
from .schema import DISPOSITIONS, ENVELOPE_FIELDS, SCHEMA_VERSION

# Ma'lum schema versiyalari. Tarix qayta yozilmaydi (schema.py): yangi versiya
# qo'shilsa SHU YERGA qo'shiladi, eskisi olib tashlanmaydi.
KNOWN_SCHEMA_VERSIONS = (SCHEMA_VERSION,)

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"

# Confirmatory run: §7 -- `git_dirty` false bo'lishi SHART.
CONFIRMATORY_MODES = ("confirmatory",)
RUN_MODES = ("pilot", "confirmatory")      # YOPIQ enum (CLI choices bilan bir xil)

# --- driver chiqishi uchun konstantalar --------------------------------------

# Qo'shimcha record turlari (reduce.py ularni o'qimaydi, lekin kontrakt
# §1.2 / §14.3 da bor).
RT_ENV_SNAPSHOT = "env_snapshot"
RT_GUARD_START = "guard_start"
RT_GUARD_STOP = "guard_stop"
RT_PROBER_START = "prober_start"
RT_PROBER_STOP = "prober_stop"
RT_HARNESS_ERROR = "harness_error"

# Trial'ning to'liq o'lchangan bo'lishi SHART bo'lgan disposition'lari: ular
# analizga (birlamchi yoki survival) KIRADI (§6.2, §12). Boshqa disposition'lar
# erta to'xtagan bo'lishi mumkin va to'liq hodisa to'plami talab qilinmaydi.
MEASURED_DISPOSITIONS = ("complete", "censored")

# --- disposition ustuvorligi: probe uzilishi va guard hodisasi --------------
#
# §14.6(4): "trial ichida probe uzilishi > 2×P yo'q (aks holda trial
# `censored`)". §12: "`contaminated` va `aborted_guard` trial'lar birlamchi
# analizdan chiqariladi". Bu ikki jumla `schedule.DISPOSITION_RULES` ning
# ustuvorlik tartibi ostida BIRGA o'qiladi (`reduce.derive_disposition`,
# `04` §8.1: avtoritet -- driver'ning `schedule.explain_disposition()` i).
# Bu o'qish `p1-pilot-002` validatsiyadan o'tmaganidan KEYIN qabul qilingan
# (docs/architecture/17 §2.5, §10); `v1.14` amendment'i uni qayd etadi.
#
# Tamoyil: probe uzilishi O'LCHANGAN NATIJA DA'VOSINI -- `complete` ni --
# bekor qiladi. U trial'ni natija analizidan allaqachon chiqaradigan va
# tartibda uzilish qoidasidan (`probe_gap_exceeded`) OLDIN turadigan
# disposition'ga (`harness_error`, `aborted_guard`, `contaminated`,
# `washout_timeout`) zid kela olmaydi; `censored` -- uzilish qoidasining o'z
# chiqishi. Shu disposition'larda uzilish OGOHLANTIRISH bo'lib hisobot
# qilinadi (jimgina emas); `complete` da va disposition yo'q/noma'lum bo'lsa
# (fail-closed) -- XATO.
GAP_WARNING_DISPOSITIONS = ("harness_error", "aborted_guard", "contaminated",
                            "washout_timeout", "censored")
#
# Teskari yo'nalish, xuddi shu tartib: trial oynasida guard ishlagan bo'lsa
# (`guard_fired`) disposition `aborted_guard` yoki tartibda undan OLDIN
# turgan yagona `harness_error` bo'lishi SHART. Boshqa HAR disposition --
# `contaminated` va `washout_timeout` ham -- guard'ning ustunligini buzadi.
GUARD_REFLECTED_DISPOSITIONS = ("harness_error", "aborted_guard")

# `no_action` arm (§9.3: `Restart=no`) da action BO'LMASLIGI ta'rifiga kiradi.
NO_ACTION_ARMS = ("no_action",)

# Dizayn faktori nomi -> record maydoni nomi. Faqat nomi farq qiladiganlar;
# qolgani o'sha nom. Manba: kontrakt v1.1 §4.3 (`reduce.Trial.pressure_band`
# aynan shuni o'qiydi, `schedule.P1_FACTORS` esa `pressure_level` deydi).
FACTOR_FIELD = {"pressure_level": "pressure_band"}

# Trial qo'shimcha vaqti (§1.3-9, §9.4 v1.3) uchun maydon nomi kontraktda
# RAQAMLANMAGAN. Birligi nomida: `_us` mikrosekund, `_s` sekund. Kontraktda
# bitta nom muzlatilgach bu tuple bittagacha qisqartiriladi.
TRIAL_OVERHEAD_FIELDS = ("overhead_us", "trial_overhead_us",
                         "overhead_s", "trial_overhead_s")

# Guest generation markeri (PID 1 ning `starttime` i). NEGA bor: `boot_id` bu
# mashinada (WSL2) guest restart'ida O'ZGARMAYDI -- agent/envcheck o'lchagan:
# oxirgi `wsl.exe` klienti chiqqandan keyin distro 10.3-15.3 s da to'xtaydi,
# transient unit ~26 s dan keyin yo'q (`LoadState=not-found`), PID 1 `etimes`
# 7 s vs VM uptime 551 s, user manager PID 241 -> 238; shu restart ichida
# `boot_id` AYNAN bir xil qoldi. Restart'da CLOCK_MONOTONIC noldan boshlanadi.
# Demak `check_boot_id` (§14.6-5) bu hostda YETARLI EMAS va marker uni
# ortiqcha deb O'CHIRIB BO'LMAYDI.
GUEST_MARKER_FIELD = "guest_generation"
# Marker dict bo'lsa, uning IDENTIFIKATORI shu kalitlardan biri (uptime kabi
# uzluksiz o'zgaradigan o'qishlar identifikator EMAS va e'tiborga olinmaydi).
GUEST_STARTTIME_KEYS = ("pid1_starttime_ticks", "starttime_ticks",
                        "pid1_starttime", "starttime")

# T_trial formulasi bilan o'lchangan horizon orasidagi ruxsat: bitta probe
# davri P. NEGA: kontrakt v1.1 §5.4-5 "aynan" deydi, lekin haqiqiy soat bilan
# aynan tenglikka erishib bo'lmaydi. PREREGISTRATION.md §6.1 probe kvantlashini
# (+-P) OCHIQ e'lon qilgan va uni jimgina "tuzatmaydi": horizon ham shu
# aniqlik bilan o'lchanadi, demak bitta probe davri -- qulaylik emas, §6.1
# ning o'zi e'lon qilgan noaniqlik chegarasi. Koordinator tomonidan qabul
# qilingan qaror.
T_TRIAL_TOLERANCE_US = P_US

# Envelope'da None bo'lishi MUMKIN bo'lmagan maydonlar (§14.2). `trial_id` va
# `block_index` run-darajasidagi record'larda (guard, run_meta) None -- bu
# TO'G'RI. `schema_version` alohida `check_schema_version` da.
ENVELOPE_REQUIRED = tuple(f for f in ENVELOPE_FIELDS
                          if f not in ("schema_version", "trial_id",
                                       "block_index"))

# run_meta (§1.1 + v1.1): kalit BO'LISHI shart.
# Identifikatsiya/reproducibility maydonlari: None ham XATO (o'lchanmaydigan
# narsa emas, yozilishi shart bo'lgan narsa).
# `preregistration_sha256` va `git_dirty` bu yerda YO'Q: ularni mavjud
# `check_run_meta` allaqachon tekshiradi (takrorlanmaydi).
RUN_META_IDENTITY = (
    "run_id", "session_id", "boot_id", "started_real_us", "started_mono_us",
    "preregistration_version", "git_commit", "rng_seed", "schedule_digest",
    "schedule", "units_show", "run_mode", "t_trial_us", "t_trial_formula",
    GUEST_MARKER_FIELD,
)
# Muhit tavsifi: None = "o'lchanmadi" HALOL (WSL2 da governor/scaling_driver).
RUN_META_MEASURED = (
    "uname", "systemd_version", "cpu_model", "cpu_count", "mem_total_kb",
    "cgroup_delegated_controllers", "oomd_effective", "governor",
    "scaling_driver", "python_version", "module_versions",
)
RUN_META_INT_FIELDS = ("started_real_us", "started_mono_us", "rng_seed",
                       "t_trial_us", "cpu_count", "mem_total_kb")

# record_type -> (None bo'lmasligi SHART maydonlar, KALITI bo'lishi SHART
# maydonlar [qiymati None bo'lishi mumkin]). Nomlar -- reduce.py/validate.py
# RUNTIME'da o'qiydiganlar (RAW_CONTRACT hujjat, validator emas: kontrakt
# v1.1 §4.1) va §14.4. `trial_id`/`block_index` ENVELOPE'da, payload'da emas.
RECORD_FIELD_RULES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    RT_TRIAL_BEGIN: (("arm", "pressure_band", "fault_class",
                      "position_in_block", "planned_timeline"), ()),
    # §14.4: systemd'ning O'Z timestamp'lari VA harness'ning qabul
    # `recv_mono_us` i ALOHIDA maydonlar.
    RT_UNIT_STATE: (("recv_mono_us",),
                    ("ActiveEnterTimestampMonotonic",
                     "ActiveExitTimestampMonotonic", "active_state",
                     "n_restarts", "invocation_id", "result",
                     "active_enter_ts_mono_us", "active_exit_ts_mono_us")),
    RT_ACTION: (("action_id", "action_class", "policy_delay_us"), ()),
    RT_ACTION_DEFER: (("action_id", "reason"), ()),
    RT_ACTOR_SIGNAL: (("success",), ()),
    RT_CGROUP_EVENTS: (("oom_kill", "scope"), ()),
    RT_FAULT_INJECT: (("mono_us_before_call", "mono_us_after_call", "kind"), ()),
    RT_BASELINE_WINDOW: (("mono_us_begin", "mono_us_end"), ()),
    RT_GUARD_EVENT: (("reason", "action"), ()),
    RT_ENV_SNAPSHOT: ((GUEST_MARKER_FIELD,), ()),
}

# trial_begin..trial_end oralig'ida YOZILISHI shart bo'lgan harness record'lari.
# Prober record'lari (prober_start/stop, detection, ...) bu ro'yxatda YO'Q:
# per-trial prober jarayoni oldingi trial'ning washout'ida ishga tushadi
# (kontrakt v1.1 §4.5-a), demak uning record'lari trial_begin'dan OLDIN bo'ladi.
HARNESS_TRIAL_TYPES = (
    RT_BASELINE_WINDOW, RT_FAULT_INJECT, RT_FAULT_EFFECTIVE, RT_ACTION,
    RT_ACTION_DEFER, RT_ACTOR_SIGNAL, RT_UNIT_STATE, RT_CGROUP_EVENTS,
    RT_ENV_SNAPSHOT,
)


@dataclass(frozen=True)
class Finding:
    """Bitta invariant buzilishi.

    Har finding'da buzilishni TOPISH uchun yetarli kontekst bo'lishi kerak:
    fayl, qator, oqim, trial, seq. Aks holda 120 trial'lik run'da xatoni
    qidirish imkonsiz.
    """

    code: str
    severity: str
    message: str
    trial_id: str | None = None
    stream: str | None = None
    record_type: str | None = None
    source: str | None = None
    index: int | None = None
    seq: int | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __str__(self) -> str:
        loc = []
        if self.source:
            loc.append(f"{self.source}:{self.index}" if self.index else self.source)
        if self.trial_id:
            loc.append(f"trial={self.trial_id}")
        if self.stream:
            loc.append(f"stream={self.stream}")
        if self.seq is not None:
            loc.append(f"seq={self.seq}")
        where = "  [" + ", ".join(loc) + "]" if loc else ""
        return f"{self.severity.upper():7s} {self.code}: {self.message}{where}"


@dataclass
class Report:
    findings: list[Finding]
    n_records: int
    n_probes: int
    n_trials: int
    sources: list[str]
    run_mode: str | None

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == SEVERITY_ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == SEVERITY_WARNING]

    @property
    def ok(self) -> bool:
        """Run analiz qilinishi mumkinmi. Bitta xato ham yetarli emas."""
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "n_errors": len(self.errors),
            "n_warnings": len(self.warnings),
            "n_records": self.n_records,
            "n_probes": self.n_probes,
            "n_trials": self.n_trials,
            "run_mode": self.run_mode,
            "sources": list(self.sources),
            "findings": [f.as_dict() for f in self.findings],
        }


# --- alohida tekshiruvlar ---------------------------------------------------


def check_schema_version(run: RawRun) -> list[Finding]:
    """Har record'da MA'LUM `schema_version` bo'lishi kerak.

    Noma'lum versiya -- ma'noni taxmin qilib tahlil qilish xavfi; shuning
    uchun bu xato, ogohlantirish emas.
    """
    out: list[Finding] = []
    for rec in list(run.records) + list(run.probes):
        rt = str(rec.get("record_type"))
        if rt.startswith("__"):
            continue   # o'qish markerlari alohida tekshiriladi
        if rt == RT_PROBE and "schema_version" not in rec:
            # CSV oqimida envelope yo'q (fiksa sxemali yuqori tezlikli oqim,
            # schema.py CsvWriter). Bu holat XATO emas.
            if str(rec.get("__source__", "")).endswith(".csv"):
                continue
        sv = _as_int(rec.get("schema_version"))
        if sv is None or sv not in KNOWN_SCHEMA_VERSIONS:
            out.append(Finding(
                "schema_version_unknown", SEVERITY_ERROR,
                f"noma'lum schema_version: {rec.get('schema_version')!r} "
                f"(ma'lum: {list(KNOWN_SCHEMA_VERSIONS)})",
                trial_id=_as_str(rec.get("trial_id")), record_type=rt,
                source=_as_str(rec.get("__source__")),
                index=_as_int(rec.get("__index__")),
                seq=_as_int(rec.get("seq")),
            ))
    return out


def check_read_errors(run: RawRun) -> list[Finding]:
    """Qismli/buzilgan qatorlar. Jimgina tashlanmaydi."""
    out: list[Finding] = []
    for rec in list(run.records) + list(run.probes):
        rt = str(rec.get("record_type"))
        if rt == "__truncated_line__":
            out.append(Finding("truncated_line", SEVERITY_WARNING,
                               "qismli oxirgi qator (crash izi) tashlandi",
                               source=_as_str(rec.get("source")),
                               index=_as_int(rec.get("index"))))
        elif rt == "__bad_json__":
            out.append(Finding("bad_json", SEVERITY_ERROR,
                               f"JSON parse xatosi: {rec.get('error')}",
                               source=_as_str(rec.get("source")),
                               index=_as_int(rec.get("index"))))
    return out


def check_boot_id(run: RawRun) -> list[Finding]:
    """Sessiya ichida `boot_id` DOIMIY (§1).

    Monotonic qiymatlar faqat bitta boot ichida taqqoslanadi. Boot o'zgargan
    bo'lsa barcha davomiylik hisoblari ma'nosiz -- shuning uchun xato.
    """
    out: list[Finding] = []
    by_session: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for rec in run.records:
        if str(rec.get("record_type")).startswith("__"):
            continue
        sid = _as_str(rec.get("session_id"))
        bid = _as_str(rec.get("boot_id"))
        if sid is None or bid is None:
            continue
        by_session.setdefault(sid, {}).setdefault(bid, []).append(rec)
    for sid, boots in by_session.items():
        if len(boots) > 1:
            for bid, recs in sorted(boots.items())[1:]:
                r = recs[0]
                out.append(Finding(
                    "boot_id_inconsistent", SEVERITY_ERROR,
                    f"session_id={sid!r} ichida bir nechta boot_id: "
                    f"{sorted(boots)} -- monotonic qiymatlar taqqoslanmaydi",
                    record_type=_as_str(r.get("record_type")),
                    source=_as_str(r.get("__source__")),
                    index=_as_int(r.get("__index__")),
                    detail={"session_id": sid, "boot_ids": sorted(boots),
                            "offending_boot_id": bid},
                ))
    return out


def check_trial_pairs(run: RawRun) -> list[Finding]:
    """Har `trial_begin` ning `trial_end` i bor (va teskarisi)."""
    out: list[Finding] = []
    begins: dict[str, dict[str, Any]] = {}
    ends: dict[str, dict[str, Any]] = {}
    for rec in run.of_type(RT_TRIAL_BEGIN):
        tid = _as_str(rec.get("trial_id")) or ""
        if tid in begins:
            out.append(Finding("trial_begin_duplicate", SEVERITY_ERROR,
                               f"trial_begin takrorlandi: {tid!r}", trial_id=tid,
                               source=_as_str(rec.get("__source__")),
                               index=_as_int(rec.get("__index__"))))
        begins.setdefault(tid, rec)
    for rec in run.of_type(RT_TRIAL_END):
        tid = _as_str(rec.get("trial_id")) or ""
        ends.setdefault(tid, rec)
    for tid, rec in begins.items():
        if tid not in ends:
            out.append(Finding(
                "trial_begin_without_end", SEVERITY_ERROR,
                f"trial_begin ning trial_end i yo'q: {tid!r} -- horizon "
                "noma'lum, right censoring hisoblanmaydi",
                trial_id=tid, record_type=RT_TRIAL_BEGIN,
                source=_as_str(rec.get("__source__")),
                index=_as_int(rec.get("__index__"))))
    for tid, rec in ends.items():
        if tid not in begins:
            out.append(Finding(
                "trial_end_without_begin", SEVERITY_ERROR,
                f"trial_end ning trial_begin i yo'q: {tid!r}",
                trial_id=tid, record_type=RT_TRIAL_END,
                source=_as_str(rec.get("__source__")),
                index=_as_int(rec.get("__index__"))))
    return out


def check_dispositions(run: RawRun) -> list[Finding]:
    """Har trial'ga AYNAN BITTA disposition, YOPIQ enumdan (§12).

    "Bu jimgina eksklyuziyaning oldini oladi" -- shuning uchun nol yoki ikkita
    disposition ham xato.
    """
    out: list[Finding] = []
    claims: dict[str, list[dict[str, Any]]] = {}
    for rec in run.of_type(RT_TRIAL_END, "trial_disposition"):
        if rec.get("disposition") is None:
            continue
        tid = _as_str(rec.get("trial_id")) or ""
        claims.setdefault(tid, []).append(rec)

    known = {_as_str(r.get("trial_id")) or ""
             for r in run.of_type(RT_TRIAL_BEGIN, RT_TRIAL_END)}
    for tid in sorted(known):
        got = claims.get(tid, [])
        if not got:
            out.append(Finding(
                "disposition_missing", SEVERITY_ERROR,
                f"trial {tid!r} da disposition yo'q -- §12 AYNAN bitta talab "
                "qiladi", trial_id=tid))
            continue
        if len(got) > 1:
            out.append(Finding(
                "disposition_duplicate", SEVERITY_ERROR,
                f"trial {tid!r} da {len(got)} ta disposition: "
                f"{[r.get('disposition') for r in got]}",
                trial_id=tid,
                source=_as_str(got[-1].get("__source__")),
                index=_as_int(got[-1].get("__index__")),
                detail={"dispositions": [_as_str(r.get('disposition'))
                                         for r in got]}))
        for rec in got:
            d = _as_str(rec.get("disposition"))
            if d not in DISPOSITIONS:
                out.append(Finding(
                    "disposition_unknown", SEVERITY_ERROR,
                    f"disposition yopiq enumda yo'q: {d!r} "
                    f"(ruxsat etilgan: {list(DISPOSITIONS)})",
                    trial_id=tid, record_type=_as_str(rec.get("record_type")),
                    source=_as_str(rec.get("__source__")),
                    index=_as_int(rec.get("__index__"))))
    return out


def _stream_key(rec: dict[str, Any]) -> tuple[str, str] | None:
    """Oqim kaliti: `(emitter, stream)`.

    `schema.Emitter.envelope()` `stream` ni record'ga YOZADI (schema.py:219,
    `ENVELOPE_FIELDS` da ham bor) va `seq` shu oqim bo'yicha monotonik
    (§14.2). Shuning uchun kalit `stream` maydonidan olinadi.

    ORQAGA MOSLIK: `stream` yo'q record uchun `record_type` proksi sifatida
    ishlatiladi (eski fixture'lar). Bunday record `check_envelope` da baribir
    XATO beradi, demak proksi faqat qo'shimcha diagnostika. Kontrakt v1.1
    §4.2-3: har record uchun `stream == record_type`; bu `check_envelope`
    da `stream_not_record_type` sifatida MAJBURLANADI -- bitta emitter ikki
    `record_type` ni bitta oqimga yozsa soxta `seq` bo'shlig'i chiqar edi.
    """
    em = _as_str(rec.get("emitter"))
    rt = _as_str(rec.get("record_type"))
    if em is None or rt is None or rt.startswith("__"):
        return None
    return (em, _as_str(rec.get("stream")) or rt)


def _seq_findings(label: str, rt: str, seqs: list[tuple[int, dict[str, Any]]],
                  *, expect_start: int | None) -> list[Finding]:
    """Bitta oqim uchun duplicate va bo'shliqlar.

    `expect_start=None` -- bosh tekshirilmaydi (faqat [min..max] ichidagi
    teshiklar). Aks holda `expect_start` dan boshlanishi SHART.
    """
    out: list[Finding] = []
    seen: dict[int, dict[str, Any]] = {}
    for s, rec in seqs:
        if s in seen:
            out.append(Finding(
                "seq_duplicate", SEVERITY_ERROR, f"seq takrorlandi: {s}",
                stream=label, record_type=rt, seq=s,
                trial_id=_as_str(rec.get("trial_id")),
                source=_as_str(rec.get("__source__")),
                index=_as_int(rec.get("__index__"))))
        else:
            seen[s] = rec
    if not seen:
        return out
    lo = expect_start if expect_start is not None else min(seen)
    hi = max(seen)
    missing = [s for s in range(lo, hi + 1) if s not in seen]
    if missing:
        first = next(iter(seen.values()))
        out.append(Finding(
            "seq_gap", SEVERITY_ERROR,
            f"oqimda {len(missing)} ta record yo'qolgan "
            f"({lo}..{hi} dan): {missing[:20]}"
            + (" ..." if len(missing) > 20 else ""),
            stream=label, record_type=rt,
            source=_as_str(first.get("__source__")),
            detail={"missing_seq": missing[:200], "n_missing": len(missing),
                    "max_seq": hi}))
    return out


def check_seq(run: RawRun) -> list[Finding]:
    """Oqimda `seq` bo'shliqlari yo'q.

    Bo'shliq = JIMGINA YO'QOLGAN RECORD. schema.py: "seq har OQIM uchun
    alohida monotonik, shunda validator bo'shliqni aniqlaydi. Bu jimgina
    ma'lumot yo'qolishini imkonsiz qiladi."

    CSV probe oqimi: envelope yo'q, `seq` TARGET bo'yicha monotonik
    (prober.py: `Target.stream = probe_sample:<target>`) va kontrakt v1.1
    §4.5-a ga ko'ra HAR TRIAL uchun alohida prober jarayoni -- ya'ni `seq`
    har trial'da 1 dan qayta boshlanadi. Shuning uchun CSV oqimi
    `(fayl, target, trial_id)` bo'yicha tekshiriladi: guruh ichida teshik
    bo'lmasligi, birinchi guruh 1 dan boshlanishi, keyingisi 1 dan (yangi
    prober) YOKI oldingi guruhning davomidan boshlanishi SHART.
    """
    out: list[Finding] = []
    streams: dict[tuple[str, str], list[tuple[int, dict[str, Any]]]] = {}
    for rec in run.records:
        k = _stream_key(rec)
        s = _as_int(rec.get("seq"))
        if k is None or s is None:
            continue
        streams.setdefault(k, []).append((s, rec))

    # (fayl, target) -> trial_id -> [(seq, rec)], birinchi uchrash tartibida.
    csv_streams: dict[tuple[str, str], dict[str, list[tuple[int, dict[str, Any]]]]] = {}
    for rec in run.probes:
        s = _as_int(rec.get("seq"))
        if s is None:
            continue
        k = _stream_key(rec)
        if k is not None:                       # JSONL probe (envelope bor)
            streams.setdefault(k, []).append((s, rec))
            continue
        ck = (str(rec.get("__source__")), _as_str(rec.get("target")) or "")
        csv_streams.setdefault(ck, {}).setdefault(
            _as_str(rec.get("trial_id")) or "", []).append((s, rec))

    for (em, st), seqs in sorted(streams.items()):
        rt = _as_str(seqs[0][1].get("record_type")) or st
        out += _seq_findings(f"{em}/{st}", rt, seqs, expect_start=1)

    for (src, target), groups in sorted(csv_streams.items()):
        prev_max: int | None = None
        for tid, seqs in groups.items():
            label = f"csv:{src}/{RT_PROBE}:{target or '-'}/{tid or '-'}"
            lo = min(s for s, _r in seqs)
            hi = max(s for s, _r in seqs)
            if prev_max is None:
                es: int | None = 1                   # birinchi guruh 1 dan
            elif lo == 1 or lo == prev_max + 1:
                es = None                            # yangi prober / davom
            else:                                    # bosh qator(lar) yo'qolgan
                es = prev_max + 1 if lo > prev_max + 1 else 1
            out += _seq_findings(label, RT_PROBE, seqs, expect_start=es)
            prev_max = hi
    return out


def check_probe_gaps(run: RawRun, probe_period_us: int = P_US) -> list[Finding]:
    """Trial ichida probe uzilishi > 2xP: `complete` da XATO, aks holda OGOHLANTIRISH.

    §4: "Probe uzilishi > 2xP -> trial `censored`, `failed` EMAS.
    Instrumentatsiya yo'qolishi hech qachon jimgina natijaga aylanmaydi."
    §14.6(4) va §12 ustuvorlik tartibi ostida birga o'qiladi
    (`GAP_WARNING_DISPOSITIONS` izohi): uzilish `complete` ning o'lchangan
    natija da'vosini bekor qiladi; `censored` va uzilish qoidasidan oldin
    turadigan, trial'ni allaqachon chiqaradigan disposition'larda u
    ogohlantirish sifatida hisobot qilinadi.
    """
    out: list[Finding] = []
    lim = 2 * probe_period_us
    for t in split_trials(run):
        gaps = []
        for a, b in zip(t.probes, t.probes[1:]):
            g = b.mono_us - a.mono_us
            if g > lim:
                gaps.append((a.mono_us, b.mono_us, g))
        if not gaps:
            continue
        disp = t.disposition_raw
        sev = (SEVERITY_WARNING if disp in GAP_WARNING_DISPOSITIONS
               else SEVERITY_ERROR)
        msg = (f"{len(gaps)} ta probe uzilishi > 2xP ({lim} us), eng katta "
               f"{max(g for _a, _b, g in gaps)} us; disposition={disp!r}")
        if sev == SEVERITY_ERROR:
            msg += " -- §4 ga ko'ra 'censored' bo'lishi SHART"
        elif disp != "censored":
            msg += (" -- disposition uzilish qoidasidan OLDIN turadi va trial'ni "
                    "allaqachon chiqaradi (§12 ustuvorligi)")
        out.append(Finding("probe_gap", sev, msg, trial_id=t.trial_id,
                           record_type=RT_PROBE,
                           detail={"gaps": [{"prev_mono_us": a, "next_mono_us": b,
                                             "gap_us": g} for a, b, g in gaps[:50]],
                                   "limit_us": lim, "disposition": disp}))
    return out


def check_actions(run: RawRun) -> list[Finding]:
    """Har `action` uchun invocation o'zgarishi YOKI oshkora `defer`.

    Sabab: action yuborilgan, lekin hech narsa o'zgarmagan bo'lsa -- yo action
    bajarilmagan (harness xatosi), yo u oshkora DEFER qilingan. Ikkinchisi
    qonuniy, lekin YOZILISHI kerak, aks holda "action bo'ldi lekin ta'siri
    yo'q" jimgina yo'qoladi.
    """
    out: list[Finding] = []
    for t in split_trials(run):
        defer_ids = {_as_str(r.get("action_id")) for r in t.defers}
        for k, a in enumerate(t.actions):
            if a.deferred or (a.action_id is not None and a.action_id in defer_ids):
                continue
            hi = (t.actions[k + 1].mono_us if k + 1 < len(t.actions)
                  else (t.end_us if t.end_us is not None else a.mono_us))
            if _invocation_changed(t, a.mono_us, hi):
                continue
            out.append(Finding(
                "action_without_invocation_change", SEVERITY_ERROR,
                f"action (mono_us={a.mono_us}, class={a.action_class!r}) dan "
                "keyin invocation o'zgarishi yo'q va oshkora defer ham yo'q",
                trial_id=t.trial_id, record_type=RT_ACTION,
                source=_as_str(a.raw.get("__source__")),
                index=_as_int(a.raw.get("__index__")),
                detail={"action_id": a.action_id, "mono_us": a.mono_us,
                        "window_us": [a.mono_us, hi]}))
    return out


def _invocation_changed(trial: Any, lo_us: int, hi_us: int) -> bool:
    """`(lo, hi]` oynasida invocation (yoki NRestarts) o'zgardimi."""
    before = [p.invocation_id for p in trial.probes
              if p.mono_us <= lo_us and p.invocation_id]
    for r in trial.unit_states:
        t = _as_int(r.get("mono_us"))
        v = _as_str(r.get("invocation_id"))
        if t is not None and v and t <= lo_us:
            before.append(v)
    base = before[-1] if before else None

    after: list[str] = [p.invocation_id for p in trial.probes
                        if lo_us < p.mono_us <= hi_us and p.invocation_id]
    nrs_before = [n for n in (_as_int(r.get("n_restarts"))
                              for r in trial.unit_states
                              if (_as_int(r.get("mono_us")) or -1) <= lo_us)
                  if n is not None]
    nrs_after = [n for n in (_as_int(r.get("n_restarts"))
                             for r in trial.unit_states
                             if lo_us < (_as_int(r.get("mono_us")) or -1) <= hi_us)
                 if n is not None]
    for r in trial.unit_states:
        t = _as_int(r.get("mono_us"))
        v = _as_str(r.get("invocation_id"))
        if t is not None and v and lo_us < t <= hi_us:
            after.append(v)
    if base is not None and any(v != base for v in after):
        return True
    if base is None and after:
        return True
    if nrs_before and nrs_after and max(nrs_after) > max(nrs_before):
        return True
    return False


def check_run_meta(run: RawRun, run_mode: str | None = None) -> list[Finding]:
    """`run_meta` mavjudligi va `git_dirty` (§7).

    §7: "`git_dirty` flag -- confirmatory run uchun `false` bo'lishi shart."
    Pilot uchun bu OGOHLANTIRISH: pilot ishlab chiqish davomida ishlaydi va
    P1 ma'lumotlari confirmatory analizga qo'shilmaydi (§13).
    """
    out: list[Finding] = []
    metas = run.of_type(RT_RUN_META)
    if not metas:
        out.append(Finding("run_meta_missing", SEVERITY_ERROR,
                           "run_meta record yo'q -- preregistration_sha256, "
                           "seed va git_dirty tekshirilmaydi"))
        return out
    if len(metas) > 1:
        out.append(Finding("run_meta_duplicate", SEVERITY_WARNING,
                           f"{len(metas)} ta run_meta record",
                           source=_as_str(metas[-1].get("__source__")),
                           index=_as_int(metas[-1].get("__index__"))))
    meta = metas[0]
    mode = run_mode or _as_str(meta.get("run_mode")) or _as_str(meta.get("mode"))
    dirty = meta.get("git_dirty")
    if dirty is None:
        out.append(Finding("git_dirty_missing", SEVERITY_ERROR,
                           "run_meta.git_dirty yo'q -- reproducibility "
                           "tekshirilmaydi (§7)",
                           source=_as_str(meta.get("__source__")),
                           index=_as_int(meta.get("__index__"))))
    elif bool(dirty):
        confirmatory = mode in CONFIRMATORY_MODES
        out.append(Finding(
            "git_dirty", SEVERITY_ERROR if confirmatory else SEVERITY_WARNING,
            f"run_meta.git_dirty == true (run_mode={mode!r}) -- "
            + ("confirmatory run uchun false bo'lishi SHART (§7)"
               if confirmatory
               else "pilot run uchun ruxsat, lekin qayd etiladi (§7)"),
            source=_as_str(meta.get("__source__")),
            index=_as_int(meta.get("__index__")),
            detail={"run_mode": mode}))
    if not _as_str(meta.get("preregistration_sha256")):
        out.append(Finding(
            "preregistration_sha256_missing", SEVERITY_ERROR,
            "run_meta.preregistration_sha256 yo'q -- qaysi ta'riflar ostida "
            "o'lchangani aniqlanmaydi (PREREGISTRATION.md sarlavhasi)",
            source=_as_str(meta.get("__source__")),
            index=_as_int(meta.get("__index__"))))
    return out


# ===========================================================================
# DRIVER CHIQISHI UCHUN QO'SHIMCHA INVARIANTLAR
#
# Yuqoridagi tekshiruvlar §14.6 ning 8 bandini qamraydi, lekin ular driver
# nimani YOZMAGANINI ko'rmaydi: yo'q maydon `None` bo'lib o'qiladi va `None`
# loyihada "o'lchanmadi" degani (CONTRIBUTING.md §4). Quyidagilar aynan shu
# jimgina siljishlarni ushlaydi.
# ===========================================================================


def _is_csv(rec: dict[str, Any]) -> bool:
    return str(rec.get("__source__", "")).endswith(".csv")


def _is_enveloped(rec: dict[str, Any]) -> bool:
    """Envelope talab qilinadigan record (CSV va o'qish markerlari tashqari)."""
    return not str(rec.get("record_type")).startswith("__") and not _is_csv(rec)


def _num(v: Any) -> float | None:
    """Chekli son yoki None. `bool` son EMAS (True == 1 jimgina o'tmasin)."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)) and math.isfinite(v):
        return float(v)
    return None


def _where(rec: dict[str, Any]) -> dict[str, Any]:
    return {"source": _as_str(rec.get("__source__")),
            "index": _as_int(rec.get("__index__"))}


def _locs(recs: list[dict[str, Any]], n: int = 5) -> list[dict[str, Any]]:
    return [{"record_type": _as_str(r.get("record_type")),
             "trial_id": _as_str(r.get("trial_id")), **_where(r)}
            for r in recs[:n]]


def _all_recs(run: RawRun) -> Iterator[dict[str, Any]]:
    yield from run.records
    yield from run.probes


def _trial_ids(run: RawRun) -> set[str]:
    return {t for t in (_as_str(r.get("trial_id"))
                        for r in run.of_type(RT_TRIAL_BEGIN, RT_TRIAL_END)) if t}


def _by_trial(run: RawRun) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for r in run.records:
        t = _as_str(r.get("trial_id"))
        if t is None or str(r.get("record_type")).startswith("__"):
            continue
        out.setdefault(t, []).append(r)
    return out


def _mono(rec: dict[str, Any] | None) -> int | None:
    return _as_int(rec.get("mono_us")) if rec else None


def _first(recs: list[dict[str, Any]], rt: str) -> dict[str, Any] | None:
    xs = sorted((r for r in recs if r.get("record_type") == rt),
                key=lambda r: _mono(r) or 0)
    return xs[0] if xs else None


# --- envelope va run identifikatsiyasi --------------------------------------


def check_envelope(run: RawRun) -> list[Finding]:
    """Har JSONL record'da §14.2 envelope'i to'liq, va `stream == record_type`.

    NEGA: §14.2 envelope'ni "har JSONL record'da" talab qiladi. Mavjud
    tekshiruvlar buni KO'RMAYDI va jimgina o'tkazib yuboradi: `check_boot_id`
    `boot_id` yo'q record'ni `continue` bilan tashlaydi (§14.6-5 chetlab
    o'tiladi), `check_seq` `seq`/`emitter` yo'q record'ni tashlaydi (§14.6-3
    chetlab o'tiladi). Kontrakt v1.1 §4.2-3: `stream = record_type` -- aks
    holda `_stream_key` soxta `seq` bo'shlig'i ko'rsatadi.
    CSV oqimi (envelope yo'q) §14.2 bo'yicha ochiq ozod.
    """
    out: list[Finding] = []
    miss: dict[str, list[dict[str, Any]]] = {}
    bad_stream: list[dict[str, Any]] = []
    for rec in _all_recs(run):
        if not _is_enveloped(rec):
            continue
        for f in ENVELOPE_REQUIRED:
            v = rec.get(f)
            if v is None or v == "" or (
                    f in ("seq", "mono_us", "real_us") and _as_int(v) is None):
                miss.setdefault(f, []).append(rec)
        st, rt = _as_str(rec.get("stream")), _as_str(rec.get("record_type"))
        if st is not None and rt is not None and st != rt:
            bad_stream.append(rec)
    for f, recs in sorted(miss.items()):
        out.append(Finding(
            "envelope_field_missing", SEVERITY_ERROR,
            f"envelope maydoni yo'q yoki yaroqsiz: {f!r} -- {len(recs)} ta "
            "record (§14.2)", record_type=_as_str(recs[0].get("record_type")),
            **_where(recs[0]),
            detail={"field": f, "n": len(recs),
                    "by_record_type": dict(Counter(
                        str(r.get("record_type")) for r in recs)),
                    "first": _locs(recs)}))
    if bad_stream:
        out.append(Finding(
            "stream_not_record_type", SEVERITY_ERROR,
            f"{len(bad_stream)} ta record'da stream != record_type -- "
            "kontrakt v1.1 §4.2-3: stream = record_type; aks holda bitta "
            "oqimga ikki tur yozilib soxta seq bo'shlig'i chiqadi",
            record_type=_as_str(bad_stream[0].get("record_type")),
            **_where(bad_stream[0]),
            detail={"n": len(bad_stream), "first": _locs(bad_stream)}))
    return out


def check_run_identity(run: RawRun) -> list[Finding]:
    """Barcha record'lar `run_meta` bilan BIR run/sessiya/boot'ga tegishli.

    NEGA: guard mustaqil jarayon va `guard.py` `--run-id` berilmasa YANGI
    uuid, `--session-id` berilmasa "adhoc" oladi. Bunday guard record'lari
    boshqa run/sessiyaga tegishli: `check_boot_id` ularni `session_id` bo'yicha
    guruhlaydi va driver bilan HECH QACHON solishtirmaydi. Lekin guard
    atributsiyasi MONOTONIC vaqt bo'yicha va faqat bitta boot ichida haqiqiy
    (§14.7), demak `boot_id` run_meta bilan AYNAN bir xil bo'lishi SHART
    (§14.6-5). `run_id` -- kontrakt §1: bitta run = bitta katalog.
    """
    meta = run.run_meta
    if meta is None:
        return []                    # `run_meta_missing` allaqachon xato
    codes = {"run_id": "run_id_mismatch", "session_id": "session_id_mismatch",
             "boot_id": "boot_id_run_meta_mismatch"}
    out: list[Finding] = []
    bad: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for rec in _all_recs(run):
        if not _is_enveloped(rec):
            continue
        for f in codes:
            want, got = _as_str(meta.get(f)), _as_str(rec.get(f))
            if want is None or got is None or got == want:
                continue
            bad.setdefault((f, got, str(rec.get("emitter"))), []).append(rec)
    for (f, got, em), recs in sorted(bad.items()):
        out.append(Finding(
            codes[f], SEVERITY_ERROR,
            f"{f}={got!r} run_meta dagi {_as_str(meta.get(f))!r} bilan mos "
            f"emas (emitter={em}, {len(recs)} ta record) -- boshqa run/boot "
            "ma'lumoti aralashgan, monotonic atributsiya ma'nosiz",
            record_type=_as_str(recs[0].get("record_type")), **_where(recs[0]),
            detail={"field": f, "got": got, "want": _as_str(meta.get(f)),
                    "emitter": em, "n": len(recs), "first": _locs(recs)}))
    return out


# --- run_meta ---------------------------------------------------------------


def _resolve_mode(run: RawRun, override: str | None) -> str | None:
    meta = run.run_meta or {}
    return override or _as_str(meta.get("run_mode")) or _as_str(meta.get("mode"))


def check_run_mode(run: RawRun, run_mode: str | None = None) -> list[Finding]:
    """`run_mode` mavjud, yopiq enumdan, va confirmatory pasaytirilmagan.

    NEGA: §14.6-8 `git_dirty` uchun confirmatory (XATO) va pilot
    (OGOHLANTIRISH) ni ajratadi. `run_mode` noma'lum bo'lsa mavjud
    `check_run_meta` uni "confirmatory emas" deb oladi va confirmatory run
    ning dirty daraxti faqat ogohlantirish bo'lib qoladi -- FAIL-OPEN.
    Kontrakt v1.1 §1.1 `run_mode` ni majburiy qildi. `--run-mode pilot` bilan
    confirmatory run'ni yumshoq tekshirish ham shu teshik.
    """
    meta = run.run_meta
    if meta is None:
        return []
    out: list[Finding] = []
    loc = _where(meta)
    declared = _as_str(meta.get("run_mode")) or _as_str(meta.get("mode"))
    if run_mode is not None and run_mode not in RUN_MODES:
        out.append(Finding("run_mode_unknown", SEVERITY_ERROR,
                           f"run_mode argumenti yopiq enumda yo'q: {run_mode!r} "
                           f"({list(RUN_MODES)})", **loc))
    if declared is None and run_mode is None:
        out.append(Finding(
            "run_mode_missing", SEVERITY_ERROR,
            "run_meta.run_mode yo'q -- confirmatory/pilot ajratib bo'lmaydi, "
            "git_dirty qattiqligi aniqlanmaydi (§14.6-8)", **loc))
    elif declared is not None and declared not in RUN_MODES:
        out.append(Finding("run_mode_unknown", SEVERITY_ERROR,
                           f"run_meta.run_mode yopiq enumda yo'q: {declared!r} "
                           f"({list(RUN_MODES)})", **loc))
    if (run_mode is not None and declared in CONFIRMATORY_MODES
            and run_mode not in CONFIRMATORY_MODES):
        out.append(Finding(
            "run_mode_downgrade", SEVERITY_ERROR,
            f"run_meta confirmatory deydi, lekin tekshiruv {run_mode!r} "
            "sifatida so'raldi -- confirmatory run yumshoq qoidalar bilan "
            "tekshirilmaydi", **loc,
            detail={"declared": declared, "requested": run_mode}))
    return out


def check_run_meta_fields(run: RawRun) -> list[Finding]:
    """§1.1 dagi har maydon: KALIT yo'q = XATO, `None` = "o'lchanmadi".

    NEGA: kontrakt §1.1 + v1.1 majburiy maydonlar ro'yxatini beradi va §14.4
    reproducibility maydonlarini ("`git_commit`, `rng_seed`, `boot_id`")
    majburiy qiladi. Kalit yo'qligi -- driver yozmagan; `None` -- driver
    o'lchay olmagan (WSL2 da `governor`/`scaling_driver`: cpufreq sysfs yo'q).
    Ikkalasini aralashtirish halol "o'lchanmadi" ni validatsiya xatosiga
    aylantirardi YOKI yozilmagan maydonni jimgina o'tkazardi. Identifikatsiya
    maydonlarida (`run_id`, `schedule`, `t_trial_us`, ...) `None` ham XATO.
    """
    meta = run.run_meta
    if meta is None:
        return []
    out: list[Finding] = []
    loc = _where(meta)
    for f in RUN_META_IDENTITY + RUN_META_MEASURED:
        if f not in meta:
            out.append(Finding(
                "run_meta_field_missing", SEVERITY_ERROR,
                f"run_meta da {f!r} KALITI yo'q (§1.1): None = o'lchanmadi, "
                "kalit yo'q = yozilmadi", **loc, detail={"field": f}))
        elif meta[f] is None and f in RUN_META_IDENTITY:
            out.append(Finding(
                "run_meta_field_null", SEVERITY_ERROR,
                f"run_meta.{f} None -- bu identifikatsiya/reproducibility "
                "maydoni, 'o'lchanmadi' bo'lishi mumkin emas (§14.4)",
                **loc, detail={"field": f}))
    for f in RUN_META_INT_FIELDS:
        v = meta.get(f)
        if v is not None and (isinstance(v, (bool, str)) or _as_int(v) is None):
            out.append(Finding("run_meta_field_invalid", SEVERITY_ERROR,
                               f"run_meta.{f} butun son emas: {v!r}", **loc,
                               detail={"field": f, "value": repr(v)}))
    for f, typ, tn in (("schedule_digest", str, "str"),
                       ("t_trial_formula", str, "str"),
                       ("module_versions", dict, "dict")):
        v = meta.get(f)
        if v is not None and not isinstance(v, typ):
            out.append(Finding("run_meta_field_invalid", SEVERITY_ERROR,
                               f"run_meta.{f} {tn} emas: {v!r}", **loc,
                               detail={"field": f, "value": repr(v)}))
    tt = meta.get("t_trial_us")
    if (tt is not None and not isinstance(tt, (bool, str))
            and _as_int(tt) is not None and _as_int(tt) <= 0):
        out.append(Finding("run_meta_field_invalid", SEVERITY_ERROR,
                           f"run_meta.t_trial_us musbat bo'lishi kerak: {tt!r}",
                           **loc, detail={"field": "t_trial_us"}))
    tf = meta.get("t_trial_formula")
    if isinstance(tf, str) and not tf.strip():
        out.append(Finding("run_meta_field_invalid", SEVERITY_ERROR,
                           "run_meta.t_trial_formula bo'sh matn", **loc,
                           detail={"field": "t_trial_formula"}))
    return out


def _iter_unit_dumps(units_show: Any) -> list[tuple[str, Any]] | None:
    if isinstance(units_show, dict):
        return [(str(k), v) for k, v in units_show.items()]
    if isinstance(units_show, list):
        return [(str(d.get("unit")) if isinstance(d, dict) and d.get("unit")
                 else f"[{i}]", d) for i, d in enumerate(units_show)]
    return None


def check_units_show(run: RawRun) -> list[Finding]:
    """`units_show` har dump'i unit TIRIK paytida olingan.

    NEGA: 01-muhit-tekshiruvlari.md §4 -- o'chgan unit uchun `systemctl show`
    rc=0 va TO'LIQ DEFAULT'lar qaytaradi (`LoadState=not-found`,
    `MemoryMax=infinity`, `RestartSteps=0`); ular haqiqiy qiymatga o'xshaydi.
    §14.4 har unit'ning TIRIK dump'ini majburiy qiladi.
    `units.dump_unit_properties` `alive_before`/`alive_after`/`dump_valid`/
    `load_state` ni yozadi -- bu yerda ular TEKSHIRILADI. Liveness kalitlari
    umuman yo'q dump ham o'tmaydi: tirik ekanligi isbotlanmagan (fail-closed).
    """
    meta = run.run_meta
    if meta is None or "units_show" not in meta or meta["units_show"] is None:
        return []                     # run_meta_field_missing/_null xato beradi
    loc = _where(meta)
    dumps = _iter_unit_dumps(meta["units_show"])
    if dumps is None:
        return [Finding("units_show_malformed", SEVERITY_ERROR,
                        "units_show dict (unit -> dump) yoki ro'yxat emas",
                        **loc)]
    if not dumps:
        return [Finding("units_show_empty", SEVERITY_ERROR,
                        "units_show bo'sh -- birorta unit dump'i yo'q (§14.4)",
                        **loc)]
    out: list[Finding] = []

    def bad(code: str, unit: str, msg: str, **detail: Any) -> None:
        out.append(Finding(code, SEVERITY_ERROR, f"[{unit}] {msg}", **loc,
                           detail={"unit": unit, **detail}))

    for unit, d in dumps:
        if not isinstance(d, dict):
            bad("units_show_malformed", unit, "dump dict emas")
            continue
        props = d.get("properties")
        for k in ("alive_before", "alive_after", "dump_valid"):
            if k not in d:
                bad("units_show_unverifiable", unit,
                    f"{k!r} yo'q -- dump unit TIRIK paytida olingani "
                    "isbotlanmagan (01-muhit §4)", field=k)
            elif d[k] is not True:
                bad("units_show_dead", unit,
                    f"{k}={d[k]!r} -- unit tirik emas, `systemctl show` "
                    "DEFAULT'lar qaytargan bo'lishi mumkin (01-muhit §4)",
                    field=k, value=repr(d[k]))
        states = [("load_state", d.get("load_state"))] if "load_state" in d else []
        if isinstance(props, dict) and "LoadState" in props:
            states.append(("properties.LoadState", props["LoadState"]))
        if not states:
            bad("units_show_unverifiable", unit,
                "load_state ham, properties.LoadState ham yo'q")
        for name, v in states:
            if v != "loaded":
                bad("units_show_not_loaded", unit,
                    f"{name}={v!r} (kutilgan 'loaded') -- yo'q unit "
                    "default'lari", field=name, value=repr(v))
        if "systemctl_rc" in d and d["systemctl_rc"] != 0:
            bad("units_show_dead", unit,
                f"systemctl_rc={d['systemctl_rc']!r}", field="systemctl_rc")
        if not isinstance(props, dict) or not props:
            bad("units_show_empty", unit, "properties bo'sh yoki yo'q")
    return out


# --- jadval (schedule) -------------------------------------------------------


def _canonical_json(obj: Any) -> str:
    """`schedule.Schedule.to_json` bilan AYNAN bir xil kanonik shakl.

    Ikkisi uzoqlashsa `test_schedule_digest_schedule_py_bilan_mos` ushlaydi.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def schedule_digest_of(schedule_obj: Any) -> str:
    return hashlib.sha256(_canonical_json(schedule_obj).encode()).hexdigest()


def _parse_schedule(meta: dict[str, Any] | None
                    ) -> tuple[dict[str, Any] | None, str | None]:
    """`run_meta.schedule` -> dict. `schedule.to_json()` matni ham qabul."""
    if meta is None or meta.get("schedule") is None:
        return None, None
    raw = meta["schedule"]
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError as exc:
            return None, f"schedule JSON matni parse bo'lmadi: {exc}"
    if not isinstance(raw, dict):
        return None, f"schedule dict emas: {type(raw).__name__}"
    need = ("schedule_version", "rng", "seed", "n_blocks", "cells_per_block",
            "n_trials", "factors", "trials")
    miss = [k for k in need if k not in raw]
    if miss:
        return None, f"schedule da kalitlar yo'q: {miss}"
    return raw, None


def _schedule_design_problems(s: dict[str, Any]) -> list[str]:
    """Jadvalning ichki izchilligi: RCBD (§8.4) -- har blok har yacheykadan BITTA."""
    probs: list[str] = []
    factors = s["factors"]
    names = [f["name"] for f in factors]
    grid = list(itertools.product(*(f["levels"] for f in factors)))
    nb, cpb, nt = s["n_blocks"], s["cells_per_block"], s["n_trials"]
    trials = s["trials"]
    if cpb != len(grid):
        probs.append(f"cells_per_block={cpb} != faktorlar ko'paytmasi {len(grid)}")
    if nt != len(trials) or nt != nb * len(grid):
        probs.append(f"n_trials={nt}, len(trials)={len(trials)}, "
                     f"n_blocks*cells={nb * len(grid)} -- teng emas")
    ids = [t["trial_id"] for t in trials]
    if len(set(ids)) != len(ids):
        probs.append("trial_id takrorlangan")
    per_block: dict[int, Counter] = {}
    for t in trials:
        if t["block_index"] not in range(nb):
            probs.append(f"{t['trial_id']}: block_index={t['block_index']} "
                         f"[0,{nb}) dan tashqari")
        if t["position_in_block"] not in range(len(grid)):
            probs.append(f"{t['trial_id']}: position_in_block "
                         f"{t['position_in_block']} diapazondan tashqari")
        cell = tuple(t.get(n) for n in names)
        if cell not in grid:
            probs.append(f"{t['trial_id']}: yacheyka {cell} faktor "
                         "darajalarida yo'q")
        per_block.setdefault(t["block_index"], Counter())[cell] += 1
    for b in range(nb):
        c = per_block.get(b, Counter())
        if any(c.get(cell, 0) != 1 for cell in grid) or sum(c.values()) != len(grid):
            probs.append(f"blok {b} to'liq emas: har yacheykadan AYNAN bitta "
                         "bo'lishi kerak (§8.4)")
    return probs


def check_schedule(run: RawRun) -> list[Finding]:
    """`schedule_digest` qayta hisoblanadi; jadval izchil va seed bilan mos.

    NEGA: §14.4 `rng_seed` ni majburiy qiladi; kontrakt §1.1 to'liq jadval VA
    uning digest'ini. Digest qayta hisoblanmasa u shunchaki yozilgan matn:
    driver boshqa jadval bajarib, eskisini yozib qo'ysa -- randomizatsiya
    (§8.4) jimgina buziladi. Jadval `rng_seed` dan qayta tiklanadi: mos
    kelmasa (RNG/Python versiyasi o'zgardi yoki qo'lda tahrirlangan) --
    OGOHLANTIRISH (barqarorlik shartini bu validator emas, schedule.py
    kafolatlaydi).
    """
    meta = run.run_meta
    sched, err = _parse_schedule(meta)
    if meta is None or (sched is None and err is None):
        return []                     # run_meta_missing / field_null xato beradi
    loc = _where(meta)
    if sched is None:
        return [Finding("schedule_malformed", SEVERITY_ERROR, err or "", **loc)]
    out: list[Finding] = []
    try:
        probs = _schedule_design_problems(sched)
    except (KeyError, TypeError, ValueError) as exc:
        return [Finding("schedule_malformed", SEVERITY_ERROR,
                        f"jadval tuzilishi buzuq: {exc!r}", **loc)]
    if probs:
        out.append(Finding("schedule_design_violation", SEVERITY_ERROR,
                           f"{len(probs)} ta dizayn buzilishi (§8.4 RCBD): "
                           f"{probs[:3]}", **loc, detail={"problems": probs[:50]}))
    want, got = _as_str(meta.get("schedule_digest")), schedule_digest_of(sched)
    if want is not None and want != got:
        out.append(Finding(
            "schedule_digest_mismatch", SEVERITY_ERROR,
            "run_meta.schedule_digest yozilgan jadvalning sha256'iga mos "
            "emas -- jadval yoki digest o'zgartirilgan", **loc,
            detail={"recorded": want, "recomputed": got}))
    seed = _as_int(meta.get("rng_seed"))
    if seed is not None and seed != _as_int(sched.get("seed")):
        out.append(Finding(
            "rng_seed_mismatch", SEVERITY_ERROR,
            f"run_meta.rng_seed={seed} jadvalning seed'iga "
            f"({sched.get('seed')!r}) teng emas", **loc))
    try:
        regen = make_schedule(
            [Factor(f["name"], tuple(f["levels"])) for f in sched["factors"]],
            sched["n_blocks"], sched["seed"])
        if regen.to_json() != _canonical_json(sched):
            out.append(Finding(
                "schedule_not_reproducible", SEVERITY_WARNING,
                "jadval seed'dan qayta tiklanganda boshqacha chiqdi "
                "(RNG algoritmi/versiyasi yoki qo'lda tahrir)", **loc))
    except (ScheduleError, KeyError, TypeError, ValueError) as exc:
        out.append(Finding("schedule_malformed", SEVERITY_ERROR,
                           f"jadvalni qayta tiklab bo'lmadi: {exc!r}", **loc))
    return out


def check_trial_set(run: RawRun) -> list[Finding]:
    """Bajarilgan trial'lar to'plami jadvalga (va `--only` filtriga) AYNAN mos.

    NEGA: §8.4 randomized complete block -- har blok har yacheykadan bitta.
    Jadvaldan tashqari trial yoki bajarilmagan trial dizaynni jimgina
    o'zgartiradi (jimgina eksklyuziya -- §12 ning aynan oldini olmoqchi
    bo'lgan narsa). Bajarilgan trial'ning arm/pressure/blok/pozitsiyasi
    jadvaldagidan farq qilsa, randomizatsiya o'rniga driver tanlovi bo'ladi.
    Yacheykadagi trial soni dizayn aytganidek (`n_blocks`) bo'lishi SHART.
    Trial umuman yo'q run ham o'tmaydi (bo'sh fayl "toza" emas).

    `--only` (driver): `run_meta.schedule` HAR DOIM to'liq jadval, bajarilgan
    qism esa `run_meta.only` bilan oshkora yoziladi. Kutilgan to'plam =
    `driver.select_trials` semantikasi (barcha token trial yacheykasida).
    Filtrlangan run to'liq dizayn EMAS: `run_filtered` ogohlantirishi.
    """
    ids = _trial_ids(run)
    if not ids:
        return [Finding("run_without_trials", SEVERITY_ERROR,
                        "run'da birorta trial_begin/trial_end yo'q")]
    meta = run.run_meta
    sched, _err = _parse_schedule(meta)
    if sched is None or meta is None:
        return []                     # schedule_* xatolari allaqachon bor
    try:
        names = [f["name"] for f in sched["factors"]]
        by_id = {t["trial_id"]: t for t in sched["trials"]}
        grid = list(itertools.product(*(f["levels"] for f in sched["factors"])))
        n_blocks = int(sched["n_blocks"])
    except (KeyError, TypeError, ValueError):
        return []
    out: list[Finding] = []
    only = meta.get("only") or []
    if not isinstance(only, list):
        return [Finding("run_only_invalid", SEVERITY_ERROR,
                        f"run_meta.only ro'yxat emas: {only!r}", **_where(meta))]

    def cell_of(t: dict[str, Any]) -> tuple[Any, ...]:
        return tuple(t.get(n) for n in names)

    selected = {tid: t for tid, t in by_id.items()
                if all(tok in cell_of(t) for tok in only)}
    if only:
        out.append(Finding(
            "run_filtered", SEVERITY_WARNING,
            f"run --only {only} bilan filtrlangan: {len(selected)}/"
            f"{len(by_id)} trial -- to'liq blok dizayni EMAS (§8.4)",
            **_where(meta), detail={"only": only}))
        if not selected:
            out.append(Finding("run_only_invalid", SEVERITY_ERROR,
                               f"--only {only} jadvaldagi hech bir yacheykaga "
                               "mos kelmaydi", **_where(meta)))
    for key, want in (("n_trials_total", len(by_id)),
                      ("n_trials_selected", len(selected))):
        got = _as_int(meta.get(key))
        if meta.get(key) is not None and got != want:
            out.append(Finding(
                "run_meta_trial_counts_mismatch", SEVERITY_ERROR,
                f"run_meta.{key}={meta.get(key)!r}, jadval/filtrdan hisoblangan "
                f"{want}", **_where(meta), detail={"field": key, "want": want}))
    extra = sorted(ids - set(selected))
    if extra:
        out.append(Finding(
            "trial_not_in_schedule", SEVERITY_ERROR,
            f"{len(extra)} ta trial jadvalda (yoki --only tanlovida) yo'q: "
            f"{extra[:10]}", detail={
                "trial_ids": extra[:200],
                "in_schedule_but_filtered": [e for e in extra if e in by_id][:200]}))
    absent = sorted(set(selected) - ids)
    if absent:
        out.append(Finding("schedule_trial_missing", SEVERITY_ERROR,
                           f"jadvaldagi {len(absent)} ta trial bajarilmagan: "
                           f"{absent[:10]} -- to'liq blok dizayni buzildi",
                           detail={"trial_ids": absent[:200]}))
    begins: dict[str, dict[str, Any]] = {}
    for r in run.of_type(RT_TRIAL_BEGIN):
        begins.setdefault(_as_str(r.get("trial_id")) or "", r)
    counts: Counter = Counter()
    for tid, b in sorted(begins.items()):
        st = by_id.get(tid)
        if st is None:
            continue
        mism: list[str] = []
        if _as_int(b.get("block_index")) not in (None, st["block_index"]):
            mism.append(f"block_index {b.get('block_index')!r} != {st['block_index']}")
        pib = _as_int(b.get("position_in_block"))
        if pib is not None and pib != st["position_in_block"]:
            mism.append(f"position_in_block {pib} != {st['position_in_block']}")
        cell: list[Any] = []
        for n in names:
            f = FACTOR_FIELD.get(n, n)
            got = b.get(f)
            if got is not None and got != st.get(n):
                mism.append(f"{f} {got!r} != jadval {st.get(n)!r}")
            cell.append(got)
            alias = b.get(n) if n != f else None
            if alias is not None and alias != st.get(n):
                mism.append(f"{n} {alias!r} != jadval {st.get(n)!r}")
        if mism:
            out.append(Finding("trial_schedule_mismatch", SEVERITY_ERROR,
                               f"trial jadvalga mos emas: {mism}", trial_id=tid,
                               record_type=RT_TRIAL_BEGIN, **_where(b),
                               detail={"mismatches": mism}))
        if all(c is not None for c in cell):
            counts[tuple(cell)] += 1
    expected: Counter = Counter(cell_of(t) for t in selected.values())
    bad_cells = {c: counts.get(c, 0) for c in grid
                 if counts.get(c, 0) != expected.get(c, 0)}
    bad_cells.update({c: n for c, n in counts.items() if c not in grid})
    if bad_cells:
        out.append(Finding(
            "cell_count_mismatch", SEVERITY_ERROR,
            f"{len(bad_cells)} ta yacheykada trial soni dizaynnikiga "
            f"({n_blocks}) teng emas", detail={
                "expected_per_cell": n_blocks,
                "cells": [{"cell": list(c), "n": n, "expected": expected.get(c, 0)}
                          for c, n in sorted(bad_cells.items(), key=str)]}))
    return out


def check_guest_generation(run: RawRun) -> list[Finding]:
    """Guest generation markeri `run_meta` da va har `env_snapshot` da BIR XIL.

    NEGA: PREREGISTRATION.md §1 barcha davomiylikni CLOCK_MONOTONIC da
    muzlatgan va `boot_id` ni "monotonic qiymatlar faqat bitta boot ichida
    taqqoslanadi" shartining kafolati qilgan (§14.6-5; §8.2 guard
    atributsiyasi ham shunga tayanadi). Lekin bu mashinada `boot_id` guest
    (WSL2) restart'ida O'ZGARMAS -- agent/envcheck o'lchagan: oxirgi klient
    chiqqandan keyin distro 10.3-15.3 s da to'xtaydi, transient unit ~26 s
    dan keyin `LoadState=not-found`, PID 1 `etimes` 7 s vs VM uptime 551 s,
    user manager PID 241 -> 238, `boot_id` esa AYNAN bir xil. Restart'da
    CLOCK_MONOTONIC noldan boshlanadi: run ikki taqqoslab bo'lmaydigan vaqt
    manbasini o'z ichiga oladi va `check_boot_id` JIM o'tadi -- ya'ni
    validatsiyadan o'tadigan, jimgina yolg'on raqamlar. Marker (PID 1 ning
    `/proc/1/stat` starttime'i) shu teshikni yopadi. U `check_boot_id` ning
    ORTIQCHA nusxasi EMAS: `boot_id` yetarli emasligi o'lchangan, shuning
    uchun bu tekshiruvni o'chirmang. Har `env_snapshot` markerni olib
    yurgani uchun uzilish QAYSI trial'ga tushgani ko'rinadi: undan oldingi
    trial'lar saqlanadi, keyingilari taqqoslanmaydi.
    """
    meta = run.run_meta
    if meta is None or meta.get(GUEST_MARKER_FIELD) is None:
        return []                  # run_meta_field_missing/_null xato beradi
    loc = _where(meta)

    def ident(v: Any) -> str | None:
        if isinstance(v, dict):
            for k in GUEST_STARTTIME_KEYS:
                if v.get(k) is not None:
                    return _canonical_json(v[k])
            return None
        return None if v in (None, "") else _canonical_json(v)

    ref = ident(meta[GUEST_MARKER_FIELD])
    if ref is None:
        return [Finding(
            "guest_generation_unreadable", SEVERITY_ERROR,
            f"run_meta.{GUEST_MARKER_FIELD} dan PID 1 starttime ajratib "
            f"bo'lmadi (kutilgan kalitlar: {list(GUEST_STARTTIME_KEYS)}) -- "
            "restart aniqlanmaydi", **loc)]
    out: list[Finding] = []
    order: list[str] = []
    for r in run.of_type(RT_TRIAL_BEGIN):
        t = _as_str(r.get("trial_id"))
        if t and t not in order:
            order.append(t)
    snaps = [r for r in run.records if r.get("record_type") == RT_ENV_SNAPSHOT
             and r.get(GUEST_MARKER_FIELD) is not None]
    unreadable = [r for r in snaps if ident(r[GUEST_MARKER_FIELD]) is None]
    if unreadable:
        out.append(Finding(
            "guest_generation_unreadable", SEVERITY_ERROR,
            f"{len(unreadable)} ta env_snapshot da {GUEST_MARKER_FIELD} "
            "starttime'i o'qilmaydi", record_type=RT_ENV_SNAPSHOT,
            **_where(unreadable[0])))
    changed = [r for r in snaps if ident(r[GUEST_MARKER_FIELD]) not in (None, ref)]
    if changed:
        first = changed[0]
        first_tid = _as_str(first.get("trial_id"))
        bad_tids = sorted({t for t in (_as_str(r.get("trial_id")) for r in changed) if t})
        if first_tid in order:
            i = order.index(first_tid)
            survived, lost = order[:i], order[i:]
        else:
            survived, lost = [], order
        out.append(Finding(
            "guest_restarted", SEVERITY_ERROR,
            f"GUEST (WSL) QAYTA ISHGA TUSHGAN: {GUEST_MARKER_FIELD} run "
            f"davomida o'zgardi ({ref} -> {ident(first[GUEST_MARKER_FIELD])}), "
            "boot_id o'zgarmagan bo'lsa ham CLOCK_MONOTONIC noldan "
            "boshlangan -- uzilishdan keyingi monotonic timestamp'lar "
            "oldingilar bilan TAQQOSLANMAYDI. Saqlangan trial'lar: "
            f"{len(survived)}, taqqoslanmaydigan: {len(lost)}",
            trial_id=first_tid, record_type=RT_ENV_SNAPSHOT, **_where(first),
            detail={"reference": ref, "n_changed_snapshots": len(changed),
                    "first_changed_trial": first_tid,
                    "trials_before_restart": survived,
                    "trials_from_restart": lost,
                    "trials_with_changed_marker": bad_tids}))
    return out


def check_monotonic_order(run: RawRun) -> list[Finding]:
    """Ketma-ket trial'lar monotonic vaqtda o'sadi va kesishmaydi.

    NEGA: `check_guest_generation` markerga tayanadi; bu uning MARKERSIZ
    zaxirasi. Guest restart'ida CLOCK_MONOTONIC noldan boshlanadi (yuqoridagi
    o'lchov), demak keyingi trial'ning `trial_begin.mono_us` oldingisining
    `trial_end.mono_us` idan KICHIK bo'lib qoladi. Trial'lar ketma-ket
    bajariladi va `trial_id` tartibi = vaqt tartibi (schedule.make_schedule),
    shuning uchun bu tartib buzilsa -- vaqt manbai uzilgan YOKI trial'lar
    kesishgan.
    """
    begin: dict[str, int] = {}
    end: dict[str, int] = {}
    for r in run.of_type(RT_TRIAL_BEGIN):
        m = _mono(r)
        if m is not None:
            begin.setdefault(_as_str(r.get("trial_id")) or "", m)
    for r in run.of_type(RT_TRIAL_END):
        m = _mono(r)
        if m is not None:
            end.setdefault(_as_str(r.get("trial_id")) or "", m)
    ids = sorted(t for t in begin if t)
    out: list[Finding] = []
    for a, b in zip(ids, ids[1:]):
        if begin[b] <= begin[a] or (a in end and end[a] > begin[b]):
            out.append(Finding(
                "monotonic_origin_regression", SEVERITY_ERROR,
                f"trial {b!r} ({begin[b]}) trial {a!r} dan "
                f"({begin[a]}..{end.get(a)}) KEYIN boshlanmagan -- monotonic "
                "vaqt orqaga ketdi (guest restart?) yoki trial'lar kesishdi",
                trial_id=b, record_type=RT_TRIAL_BEGIN,
                detail={"previous": a, "previous_begin_us": begin[a],
                        "previous_end_us": end.get(a), "begin_us": begin[b]}))
    return out


# --- host soat uzilishi (YANGI tekshiruv, agent/pilot-ready) ------------------

# |Δreal_us − Δmono_us| chegarasi ketma-ket ikki soat namunasi orasida.
# MA'LUMOTDAN tanlangan (docs/architecture/14-smoke-trial-natijalari.md §2):
#   * qonuniy tarqalish: ~/revix-runs dagi barcha yozish-lahzali oqimlar
#     (JSONL envelope'lar emitter bo'yicha, psi.csv, probe.csv) -- 72 402
#     ketma-ket juft; uyqu oynasidan tashqarida max |d| = 0.000386 s
#     (open-params-cal-01 psi.csv), cal-01 siz max 0.000206 s. Guest'da NTP
#     daemon yo'q (timesyncd/chrony/ntp inactive), faqat hv_utils timesync;
#     804 s lik bo'shliqli guard juftlarida ham |d| <= 5 us.
#   * host uyqusi (07 §7.7, 13 §0A.1): psi.csv da +1699.6, +94.3, +6371.1,
#     +42 088.1 va +0.661 s sakrashlar; events.jsonl da bitta juft
#     Δmono 6.0 s, Δreal 42 094.8 s (d = +42 088.8 s).
#   * 1.0 s = qonuniy max'dan 2590x yuqori, 11.7 soatlik hodisadan 42 088x
#     past, va open-params controller'ining runtime chegarasi bilan bir xil
#     (13 §0A.3: "> 1 s => FAIL-CLOSED").
HOST_CLOCK_DISCONTINUITY_US = 1_000_000

# Driver bu record turlarini envelope `mono_us` i YOZISH LAHZASI EMAS
# (o'tgan hodisa vaqti) bilan yozadi -- `driver._emit(..., mono=...)`:
# trial_begin/env_snapshot/baseline_window/fault_inject/cgroup_events
# (faza chegarasi), unit_state (`recv_mono_us`), action (`t_issue`),
# actor_signal (systemd `ActiveEnterTimestampMonotonic`), trial_end
# (horizon, washout'dan ~15-20 s OLDIN). Ularning `real_us` i esa yozish
# lahzasida olinadi, demak `real_us - mono_us` yozish kechikishi qadar
# SUN'IY katta -- soat namunasi EMAS. `trial_end` uchun yozish lahzasi
# payload'da bor (`mono_us_record_written`) va o'sha juft ishlatiladi.
CLOCK_BACKDATED_RECORD_TYPES = (
    "trial_begin", "env_snapshot", "baseline_window", "fault_inject",
    "cgroup_events", "unit_state", "action", "actor_signal",
)


def _clock_samples(run: RawRun) -> list[tuple[int, int, dict[str, Any]]]:
    """Bir lahzada o'qilgan (mono_us, real_us) juftlari, mono bo'yicha.

    Manbalar: (1) envelope'li JSONL record'lar, `CLOCK_BACKDATED_RECORD_TYPES`
    dan tashqari (`schema.Emitter.envelope` avval mono, keyin real o'qiydi);
    (2) `trial_end` -- `mono_us_record_written` + `real_us`; (3) probe
    qatorlari -- `mono_us_send` + `real_us_send` (prober.py ularni ketma-ket
    o'qiydi), CSV'da `real_us_send` bo'lmasa envelope `mono_us`/`real_us`.
    Har jarayon bir xil kernel soatlarini o'qiydi, shuning uchun
    `real - mono` siljishi GLOBAL va namunalar birlashtirilib mono bo'yicha
    tartiblanadi.
    """
    out: list[tuple[int, int, dict[str, Any]]] = []
    for rec in run.records:
        rt = rec.get("record_type")
        if not isinstance(rt, str) or rt.startswith("__"):
            continue
        if rt in CLOCK_BACKDATED_RECORD_TYPES:
            continue
        mono_v = (rec.get("mono_us_record_written") if rt == RT_TRIAL_END
                  else rec.get("mono_us"))
        real_v = rec.get("real_us")
        if isinstance(mono_v, bool) or isinstance(real_v, bool):
            continue
        mono, real = _as_int(mono_v), _as_int(real_v)
        if mono is None or real is None:
            continue
        out.append((mono, real, rec))
    for pr in run.probes:
        mono, real = _as_int(pr.get("mono_us_send")), _as_int(pr.get("real_us_send"))
        if mono is None or real is None:
            mono, real = _as_int(pr.get("mono_us")), _as_int(pr.get("real_us"))
        if mono is None or real is None:
            continue
        out.append((mono, real, pr))
    out.sort(key=lambda s: s[0])
    return out


def check_host_clock_discontinuity(
    run: RawRun, threshold_us: int = HOST_CLOCK_DISCONTINUITY_US
) -> list[Finding]:
    """Host uyqusi / VM muzlashi: `|Δreal_us − Δmono_us| > 1 s` -> XATO.

    YANGI TEKSHIRUV (agent/pilot-ready, PREREGISTRATION v1.11 dan keyin).
    Bu YAROQLILIK qoidasi, TA'RIF EMAS: hech qanday metrika, disposition
    yoki muzlatilgan ta'rifni o'zgartirmaydi, faqat soati uzilgan run'ni
    analizdan oldin rad etadi (§14.6 "validatsiyadan o'tmagan run analiz
    qilinmaydi").

    NEGA: §1 barcha davomiylikni CLOCK_MONOTONIC da muzlatgan va
    taqqoslanuvchanlikni `boot_id` (§14.6-5) bilan, guest restart'ini
    `check_guest_generation` bilan himoya qiladi. Windows host uyquga
    ketsa WSL2 VM muzlaydi: guest CLOCK_MONOTONIC uyquni SANAMAYDI,
    CLOCK_REALTIME esa uyg'ongach host'ga tenglashadi. O'LCHANGAN
    (07 §7.7, 13 §0A.1, open-params-cal-01): `boot_id` O'ZGARMADI, PID 1
    o'sha paytda o'zgarmadi, mono +6.0 s, real +42 094.8 s (11.7 soat).
    Ya'ni `check_boot_id` ham, `check_guest_generation` ham, `check_seq`
    ham uyquni KO'RMAYDI -- trial ichidagi 11.7 soatlik muzlash mono
    vaqtda ko'rinmas. Uyqudan o'tgan trial'ning muhiti (host yuki, VM
    tiklanishi, uyg'onishdan keyingi guest init restart'i) o'lchanmagan;
    uni mono ma'lumotdan ajratib bo'lmaydi. Yagona iz -- ikki soat
    orasidagi siljish, va har envelope ikkalasini ham yozadi.

    Qoida: `_clock_samples` (yozish lahzasidagi juftlar, mono bo'yicha)
    ichida ketma-ket ikki namuna uchun `|Δreal − Δmono| > threshold_us`.
    Ishora ikkala tomonga: musbat = uyqu/muzlash, manfiy = realtime orqaga
    qadam. Barcha sakrashlar BITTA finding'da (qoida 7), har biri qaysi
    trial oynasiga tushgani bilan.

    CHEKLOV: (a) 1 s dan qisqa muzlash tutilmaydi; (b) yozish-lahzali
    namuna bo'lmagan oraliqda sakrash joyi faqat ikki namuna orasida
    aniqlanadi; (c) guest restart'ida (mono nolga qaytadi) bu tekshiruv ham
    yonadi -- u holda birlamchi finding `guest_restarted` /
    `monotonic_origin_regression`; (d) host realtime'ni > 1 s qadam bilan
    tuzatsa (hv_utils timesync) run ham rad etiladi -- fail-closed
    yo'nalish, o'lchangan ma'lumotda bunday hodisa YO'Q.
    """
    samples = _clock_samples(run)
    jumps: list[dict[str, Any]] = []
    for (m0, r0, a), (m1, r1, b) in zip(samples, samples[1:]):
        d = (r1 - r0) - (m1 - m0)
        if abs(d) > threshold_us:
            jumps.append({
                "mono_us_before": m0, "mono_us_after": m1,
                "real_us_before": r0, "real_us_after": r1,
                "d_mono_us": m1 - m0, "d_real_us": r1 - r0, "jump_us": d,
                "before": {"record_type": _as_str(a.get("record_type")),
                           **_where(a)},
                "after": {"record_type": _as_str(b.get("record_type")),
                          **_where(b)},
            })
    if not jumps:
        return []
    begin: dict[str, int] = {}
    end: dict[str, int] = {}
    for r in run.of_type(RT_TRIAL_BEGIN):
        m = _mono(r)
        t = _as_str(r.get("trial_id"))
        if m is not None and t:
            begin.setdefault(t, m)
    for r in run.of_type(RT_TRIAL_END):
        m = _mono(r)
        t = _as_str(r.get("trial_id"))
        if m is not None and t:
            end.setdefault(t, m)
    affected: set[str] = set()
    for j in jumps:
        hit = sorted(t for t, b0 in begin.items()
                     if b0 <= j["mono_us_after"]
                     and end.get(t, 2 ** 63) >= j["mono_us_before"])
        j["trials_spanning"] = hit
        affected.update(hit)
    worst = max(jumps, key=lambda j: abs(j["jump_us"]))
    first = jumps[0]
    return [Finding(
        "host_clock_discontinuity", SEVERITY_ERROR,
        f"{len(jumps)} ta soat uzilishi: ketma-ket namunalar orasida "
        f"|Δreal − Δmono| > {threshold_us / 1e6:g} s (eng kattasi "
        f"{worst['jump_us'] / 1e6:+.3f} s, Δmono {worst['d_mono_us'] / 1e6:.3f} s) "
        "-- host uyqusi / VM muzlashi yoki realtime qadami; boot_id va guest "
        "generation buni KO'RMAYDI. Run RAD ETILADI (yaroqlilik qoidasi, "
        f"metrika emas). Ta'sirlangan trial'lar: {sorted(affected) or '(trial oynasidan tashqarida)'}",
        trial_id=(first["trials_spanning"][0] if first["trials_spanning"]
                  else None),
        record_type=first["after"].get("record_type"),
        source=first["after"].get("source"),
        index=first["after"].get("index"),
        detail={"threshold_us": threshold_us, "n_jumps": len(jumps),
                "n_samples": len(samples), "jumps": jumps[:100],
                "trials_affected": sorted(affected),
                "max_abs_jump_us": abs(worst["jump_us"])})]


# --- maydonlar ---------------------------------------------------------------


def _is_deferred(rec: dict[str, Any]) -> bool:
    """`reduce.split_trials` dagi defer talqini bilan bir xil."""
    return bool(rec.get("deferred") or rec.get("defer")
                or rec.get("action_class") == "defer")


def check_record_fields(run: RawRun) -> list[Finding]:
    """Reducer/validator RUNTIME'da o'qiydigan maydonlar yozilgan.

    NEGA: `reduce.py` yo'q maydonni `None` deb o'qiydi (`_as_int`/`_as_str`),
    `None` esa "o'lchanmadi" -- ya'ni noto'g'ri nomlangan maydon jimgina
    "o'lchanmadi" bo'lib, masalan `pressure_band` yo'q bo'lsa birlamchi
    endpoint (§10.1) stratifikatsiyasi yo'qoladi. Kontrakt v1.1 §1.3-11:
    maydon nomi §4.3 jadvaliga AYNAN mos bo'lishi shart. §14.4:
    `action.policy_delay_us` L_dec'dan ALOHIDA (§6.3); `actor_signal.success`
    FR-A (§5) ning birlamchi operandi va manbasi (`source`) yozilishi SHART;
    `unit_state` da systemd'ning o'z timestamp'lari VA `recv_mono_us` alohida.
    Nomlar `RAW_CONTRACT` dan EMAS (u hujjat, kontrakt v1.1 §4.1), runtime'da
    o'qiladiganlardan.
    """
    out: list[Finding] = []
    miss: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    bad_success: list[dict[str, Any]] = []
    bad_mono: list[dict[str, Any]] = []
    for rec in run.records:
        rt = str(rec.get("record_type"))
        if rt not in RECORD_FIELD_RULES:
            continue
        nonnull, keyed = RECORD_FIELD_RULES[rt]
        for f in nonnull:
            if rt == RT_ACTION and f == "policy_delay_us" and _is_deferred(rec):
                continue          # defer qilingan action'da siyosat kechikishi yo'q
            if rec.get(f) is None:
                miss.setdefault((rt, f, "null" if f in rec else "absent"),
                                []).append(rec)
        for f in keyed:
            if f not in rec:
                miss.setdefault((rt, f, "absent"), []).append(rec)
        if rt == RT_ACTOR_SIGNAL:
            if rec.get("source") is None and rec.get("actor_signal_source") is None:
                miss.setdefault((rt, "source", "absent"), []).append(rec)
            v = rec.get("success")
            if v is not None and not isinstance(v, bool):
                bad_success.append(rec)
        if rt == RT_UNIT_STATE:
            a, b = _as_int(rec.get("recv_mono_us")), _as_int(rec.get("mono_us"))
            if a is not None and b is not None and a != b:
                bad_mono.append(rec)
    for (rt, f, kind), recs in sorted(miss.items()):
        hint = ""
        if rt == RT_TRIAL_BEGIN and f == "pressure_band" and any(
                "pressure_level" in r for r in recs):
            hint = (" (record'da `pressure_level` bor, lekin reduce.py "
                    "`pressure_band` o'qiydi -- kontrakt v1.1 §4.3)")
        if rt == RT_ACTOR_SIGNAL and f == "source":
            hint = " (`source` yoki `actor_signal_source`, §14.4)"
        tids = sorted({t for t in (_as_str(r.get("trial_id")) for r in recs) if t})
        out.append(Finding(
            "record_field_missing", SEVERITY_ERROR,
            f"{rt}.{f} {'None' if kind == 'null' else 'KALITI yoq'} -- "
            f"{len(recs)} ta record{hint}",
            trial_id=tids[0] if tids else None, record_type=rt,
            **_where(recs[0]),
            detail={"record_type": rt, "field": f, "kind": kind,
                    "n": len(recs), "trial_ids": tids[:50],
                    "first": _locs(recs)}))
    if bad_success:
        out.append(Finding(
            "actor_signal_success_invalid", SEVERITY_ERROR,
            f"{len(bad_success)} ta actor_signal.success bool emas -- "
            "reduce.py `bool(...)` qiladi: 'false' matni True bo'lib FR-A ni "
            "jimgina buzadi (§5)", record_type=RT_ACTOR_SIGNAL,
            **_where(bad_success[0]), detail={"first": _locs(bad_success)}))
    if bad_mono:
        out.append(Finding(
            "unit_state_mono_not_recv", SEVERITY_ERROR,
            f"{len(bad_mono)} ta unit_state da envelope mono_us != recv_mono_us "
            "-- reduce.py oyna a'zoligini mono_us bilan hisoblaydi; u qabul "
            "vaqti bo'lishi SHART (kontrakt v1.1 §4.3)",
            record_type=RT_UNIT_STATE, **_where(bad_mono[0]),
            detail={"first": _locs(bad_mono)}))
    return out


def check_planned_timeline(run: RawRun, probe_period_us: int = P_US) -> list[Finding]:
    """Har `trial_begin.planned_timeline` `TrialTimeline` invariantlarini
    qanoatlantiradi va `run_meta.t_trial_us` bilan izchil.

    NEGA: kontrakt §1.3-6: `TrialTimeline` invariantlari MAJBURLANADI --
    "pressure cap = oomd himoyasi, afzallik emas" (§9.4: hold <= HOLD_CAP_S,
    hold + ramp_above_threshold <= 15 s). `HOLD_CAP_S` qiymati bu yerda
    QAYTA YOZILMAYDI -- `schedule.py` dan import qilinadi (§17.5 O3: oomd
    bu muhitda yo'q, hold'ni endi 2-invariant chegaralaydi). `TrialTimeline`
    o'z cap'larini parametr sifatida oladi, shuning uchun driver `hold_cap_s=100` bilan
    ichki izchil, lekin XAVFLI timeline yozishi mumkin: bu yerda cap'lar
    MUZLATILGAN konstantalarga (`schedule.HOLD_CAP_S`, `GUARD_SUSTAIN_WINDOW_S`)
    nisbatan tekshiriladi, yozilgan qiymatlarga emas. Yetishmayotgan maydon
    jimgina default bo'lmaydi. Kontrakt v1.1 §5.2: T_trial = t_pressure_off
    + w_stab_s + P va t_verify_end_earliest <= T_trial <= total_s.

    CHEKLOV -- 2-invariant REJA qiymatiga qarshi tekshiriladi, O'LCHANGANIGA
    EMAS: `hold_s + ramp_above_threshold_s <= 15 s` da `ramp_above_threshold_s`
    `planned_timeline` dagi yozilgan (rejalashtirilgan) qiymat. Validator
    trial'da HAQIQATAN o'lchangan ramp'ning chegaradan yuqori qismini
    ko'rmaydi, chunki driver uni yozmaydi. Reja qiymati 0.0 (kalibratsiya:
    29 epizoddan 29 tasida 0.000 s, docs/architecture/10-pressure-dozalash.md
    §4.1), demak hold = HOLD_CAP_S da rejada ZAXIRA YO'Q va haqiqiy ramp
    rejadan oshsa -- guard `aborted_guard` qiladigan trial -- validator buni
    ushlamaydi. Zaxira QO'SHILMAYDI (to'ldirilgan konstanta yangi taxmin
    bo'lardi); davosi -- driver har trial uchun o'lchangan ramp'ni yozishi va
    validatorning uni rejaga qarshi tekshirishi (alohida ish, bu yerda
    amalga oshirilmagan).
    """
    init = [f.name for f in dataclasses.fields(TrialTimeline)]
    default = TrialTimeline().as_dict()
    required = [n for n in init if n in default]
    meta = run.run_meta or {}
    raw_tt = meta.get("t_trial_us")
    t_trial = (None if isinstance(raw_tt, (bool, str)) else _as_int(raw_tt))
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    detail_by: dict[tuple[str, str], dict[str, Any]] = {}

    def add(code: str, msg: str, rec: dict[str, Any], **detail: Any) -> None:
        groups.setdefault((code, msg), []).append(rec)
        detail_by[(code, msg)] = detail

    for rec in run.of_type(RT_TRIAL_BEGIN):
        pt = rec.get("planned_timeline")
        if pt is None:
            continue                  # record_field_missing xato beradi
        if not isinstance(pt, dict):
            add("planned_timeline_invalid", "planned_timeline dict emas", rec)
            continue
        gone = [n for n in required if n not in pt]
        if gone:
            add("planned_timeline_incomplete",
                f"planned_timeline da maydonlar yo'q: {gone} (default'ga "
                "jimgina tushmaydi)", rec, missing=gone)
            continue
        kw = {n: _num(pt[n]) for n in init if n in pt}
        badt = [n for n, v in kw.items() if v is None]
        if badt:
            add("planned_timeline_invalid",
                f"planned_timeline maydonlari son emas: {badt}", rec)
            continue
        try:
            tl = TrialTimeline(**kw)  # type: ignore[arg-type]
        except ScheduleError as exc:
            add("planned_timeline_invalid",
                f"TrialTimeline invarianti buzildi: {type(exc).__name__}: {exc}",
                rec)
            continue
        if tl.hold_cap_s > HOLD_CAP_S or tl.hold_s > HOLD_CAP_S:
            add("planned_timeline_cap_exceeded",
                f"hold_s={tl.hold_s}/hold_cap_s={tl.hold_cap_s} muzlatilgan "
                f"cap {HOLD_CAP_S} s dan oshadi (§9.4-1; cap'ni endi oomd emas, "
                "§9.4 2-invariant va guard `sustain_max` chegaralaydi, "
                "§17.5 O3)", rec)
        if (tl.guard_sustain_window_s > GUARD_SUSTAIN_WINDOW_S
                or tl.hold_s + tl.ramp_above_threshold_s > GUARD_SUSTAIN_WINDOW_S):
            add("planned_timeline_cap_exceeded",
                f"hold_s + ramp_above_threshold_s = "
                f"{tl.hold_s + tl.ramp_above_threshold_s} s yoki guard oynasi "
                f"{tl.guard_sustain_window_s} s muzlatilgan "
                f"{GUARD_SUSTAIN_WINDOW_S} s dan oshadi (§9.4-2)", rec)
        wrong = []
        for k, v in tl.as_dict().items():
            if k in pt and k not in init:
                s = _num(pt[k])
                if s is None or abs(s - v) > 1e-9:
                    wrong.append(k)
        if wrong:
            add("planned_timeline_derived_mismatch",
                f"hosila qiymatlar qayta hisoblangandan farq qiladi: {wrong}",
                rec, fields=wrong)
        if t_trial is not None:
            want = (tl.t_pressure_off + tl.w_stab_s) * 1e6 + probe_period_us
            if abs(t_trial - want) > 1.0:
                add("t_trial_formula_mismatch",
                    f"run_meta.t_trial_us={t_trial} != t_pressure_off + w_stab_s "
                    f"+ P = {want:.0f} us (kontrakt v1.1 §5.2)", rec)
            if not (tl.t_verify_end_earliest * 1e6 <= t_trial <= tl.total_s * 1e6):
                add("t_trial_out_of_bounds",
                    f"t_trial_us={t_trial} [{tl.t_verify_end_earliest * 1e6:.0f}, "
                    f"{tl.total_s * 1e6:.0f}] oralig'idan tashqari (§5.2)", rec)
    out: list[Finding] = []
    for (code, msg), recs in sorted(groups.items()):
        tids = sorted({t for t in (_as_str(r.get("trial_id")) for r in recs) if t})
        out.append(Finding(
            code, SEVERITY_ERROR, f"{msg} -- {len(recs)} ta trial",
            trial_id=tids[0] if tids else None, record_type=RT_TRIAL_BEGIN,
            **_where(recs[0]),
            detail={"n_trials": len(recs), "trial_ids": tids[:200],
                    **detail_by[(code, msg)]}))
    return out


# --- trial ketma-ketligi -----------------------------------------------------


def check_trial_events(run: RawRun) -> list[Finding]:
    """Trial hodisalari kontrakt §1.2 tartibida: `trial_begin` -> ... ->
    `trial_end`, kerakli hodisalar bor.

    NEGA: §1.2 har trial uchun ketma-ketlikni beradi. `baseline_window` yo'q
    bo'lsa `reduce.reference_throughput` JIMGINA "fault'dan oldingi probe"
    larga o'tadi -- `R_ref` ta'rifi (§4.5: "shu trial'ning fault'dan oldingi
    throughput'i") o'zgaradi. `fault_inject` yo'q bo'lsa `t_inject` (§3)
    yo'q. `action` ham, `action_defer` ham yo'q bo'lsa action jimgina
    yo'qolgan (`check_actions` faqat BOR action'ni tekshiradi). `no_action`
    arm (§9.3, Restart=no) action'dan ozod. Hodisalar [trial_begin,
    trial_end] dan tashqarida bo'lsa horizon (§6.2) ma'nosiz. Faqat
    `complete`/`censored` trial to'liq to'plam talab qiladi: erta to'xtagan
    (aborted_guard, harness_error) trial uchun talab qilib bo'lmaydi.
    """
    out: list[Finding] = []
    for tid, recs in sorted(_by_trial(run).items()):
        begin, end = _first(recs, RT_TRIAL_BEGIN), _first(recs, RT_TRIAL_END)
        disp = _as_str(end.get("disposition")) if end else None
        types = Counter(str(r.get("record_type")) for r in recs)

        def bad(code: str, msg: str, rec: dict[str, Any] | None = None,
                **detail: Any) -> None:
            out.append(Finding(code, SEVERITY_ERROR, msg, trial_id=tid,
                               record_type=_as_str((rec or {}).get("record_type")),
                               **_where(rec or {}), detail=detail))

        lo, hi = _mono(begin), _mono(end)
        if lo is not None and hi is not None:
            if hi <= lo:
                bad("trial_window_invalid",
                    f"trial_end.mono_us ({hi}) <= trial_begin.mono_us ({lo})", end)
            else:
                outside = [r for r in recs
                           if r.get("record_type") in HARNESS_TRIAL_TYPES
                           and _mono(r) is not None
                           and not (lo <= _mono(r) <= hi)]  # type: ignore[operator]
                if outside:
                    bad("trial_event_outside_window",
                        f"{len(outside)} ta hodisa [trial_begin, trial_end] "
                        "dan tashqarida (§1.2 tartibi buzildi)", outside[0],
                        by_record_type=dict(Counter(
                            str(r.get("record_type")) for r in outside)),
                        window=[lo, hi], first=_locs(outside))
        bw, fi = _first(recs, RT_BASELINE_WINDOW), _first(recs, RT_FAULT_INJECT)
        for rt in (RT_BASELINE_WINDOW, RT_FAULT_INJECT):
            if types[rt] > 1:
                bad("trial_event_duplicate",
                    f"{rt} {types[rt]} marta -- trial'ga bittadan (§9.3, §1.2)",
                    _first(recs, rt), duplicated=rt)
        if end is not None and disp in MEASURED_DISPOSITIONS:
            gone = [rt for rt in (RT_BASELINE_WINDOW, RT_FAULT_INJECT)
                    if types[rt] == 0]
            arm = _as_str(begin.get("arm")) if begin else None
            if (begin is not None and arm not in NO_ACTION_ARMS
                    and types[RT_ACTION] + types[RT_ACTION_DEFER] == 0):
                gone.append("action|action_defer")
            if gone:
                bad("trial_event_missing",
                    f"disposition={disp!r} trial'da hodisalar yo'q: {gone} "
                    "(§1.2)", end, missing=gone, arm=arm)
            if types[RT_ENV_SNAPSHOT] < 2:
                out.append(Finding(
                    "env_snapshot_missing", SEVERITY_WARNING,
                    f"env_snapshot {types[RT_ENV_SNAPSHOT]} ta (trial boshida "
                    "va oxirida 2 ta kerak, §1.2) -- kovariatalar (§8.3) "
                    "to'liq emas", trial_id=tid))
        if bw is not None:
            b, e = _as_int(bw.get("mono_us_begin")), _as_int(bw.get("mono_us_end"))
            if b is not None and e is not None and b >= e:
                bad("baseline_window_invalid",
                    f"baseline_window begin ({b}) >= end ({e})", bw)
            before = _as_int(fi.get("mono_us_before_call")) if fi else None
            if e is not None and before is not None and e > before:
                bad("baseline_after_fault",
                    f"baseline_window fault'dan KEYIN tugaydi ({e} > {before}) "
                    "-- R_ref 'fault'dan oldingi' emas (§4.5)", bw)
        if fi is not None:
            before = _as_int(fi.get("mono_us_before_call"))
            after = _as_int(fi.get("mono_us_after_call"))
            if before is not None and after is not None and before > after:
                bad("fault_inject_bracket_invalid",
                    f"mono_us_before_call ({before}) > mono_us_after_call "
                    f"({after}) -- t_inject bracket'i buzuq (§3)", fi)
            acts = [r for r in recs
                    if r.get("record_type") in (RT_ACTION, RT_ACTION_DEFER)
                    and _mono(r) is not None]
            if before is not None and acts:
                first_act = min(acts, key=lambda r: _mono(r) or 0)
                if (_mono(first_act) or 0) < before:
                    bad("action_before_fault",
                        f"action ({_mono(first_act)}) fault'dan ({before}) OLDIN "
                        "-- sabab-oqibat tartibi buzuq", first_act)
    return out


def check_trial_overhead(run: RawRun) -> list[Finding]:
    """Har o'lchangan trial'ning qo'shimcha vaqti yozilgan.

    NEGA: kontrakt §1.3-9 va §9.4 v1.3: unit yaratish/yo'q qilish, D-Bus
    round-trip, flush -- bu qo'shimcha "o'lchanadi, taxmin qilinmaydi".
    Yo'q bo'lsa kampaniya bahosi (`schedule.estimate_campaign`) taxminga
    tayanadi. OGOHLANTIRISH: bu hisobot ma'lumoti, o'lchov natijasining
    yaroqliligi emas -- uni yo'qotish uchun ikki soatlik kampaniyani analizdan
    to'sish nomutanosib. Lekin YOZILGAN qiymat yaroqsiz (manfiy/son emas)
    bo'lsa -- buzuq ma'lumot, XATO. Maydon nomi kontraktda raqamlanmagan
    (`TRIAL_OVERHEAD_FIELDS`).
    """
    out: list[Finding] = []
    for end in run.of_type(RT_TRIAL_END):
        if _as_str(end.get("disposition")) not in MEASURED_DISPOSITIONS:
            continue
        tid = _as_str(end.get("trial_id"))
        present = [(f, end[f]) for f in TRIAL_OVERHEAD_FIELDS
                   if end.get(f) is not None]
        if not present:
            out.append(Finding(
                "trial_overhead_missing", SEVERITY_WARNING,
                "trial_end da qo'shimcha vaqt yo'q -- bajarilmagan majburiyat: "
                "driver-contract §1.3 majburiyat 9 (\"trial qo'shimcha vaqti "
                "o'lchanadi va yoziladi\", §9.4 v1.3). Yo'qotilgan da'vo: "
                "kampaniya davomiyligini o'lchangan ma'lumotdan aytib "
                "bo'lmaydi, faqat taxmin; o'lchov natijalari yaroqli "
                f"qoladi (maydon: {list(TRIAL_OVERHEAD_FIELDS)})",
                trial_id=tid, record_type=RT_TRIAL_END, **_where(end)))
            continue
        for f, v in present:
            n = _num(v)
            if n is None or n < 0:
                out.append(Finding(
                    "trial_overhead_invalid", SEVERITY_ERROR,
                    f"trial_end.{f}={v!r} manfiy bo'lmagan son emas",
                    trial_id=tid, record_type=RT_TRIAL_END, **_where(end)))
    return out


def _run_w_stab_us(run: RawRun) -> int:
    """Run'ning W_stab si (us): `run_meta.timeline.w_stab_s`, aks holda pilot."""
    tl = (run.run_meta or {}).get("timeline")
    v = _num(tl.get("w_stab_s")) if isinstance(tl, dict) else None
    return int(round(v * 1_000_000)) if v is not None and v > 0 else W_STAB_PILOT_US


def _trial_window(trial: Any, prm: Params) -> Any:
    """Trial'ning §17 oyna klassifikatsiyasi -- `reduce_trial` bilan AYNI
    operandlar va AYNI funksiya (`classify_window_containment`), shuning
    uchun validator va reducer bir xil savolga javob beradi."""
    t_fault, _src = fault_effective_us(trial)
    r_ref, r_st, _d = reference_throughput(trial, t_fault)
    eps = build_episodes(trial, prm, r_ref, r_st)
    return classify_window_containment(
        eps[0].t_up_us if eps else None, prm,
        hold_end_us=trial.hold_end_us, horizon_end_us=trial.horizon_end_us)


def check_window_containment(run: RawRun, probe_period_us: int = P_US) -> list[Finding]:
    """`complete` trial'ning verifikatsiya oynasi pressure hold ICHIDA.

    NEGA (PREREGISTRATION.md v1.6 §17.4-5): har `complete` trial uchun
    `t_up + W_stab_pilot <= T_h` bo'lishi SHART; buzilgan holat `complete`
    deb yozilgan bo'lsa -- validator XATOSI. §4 1-band oynani `t_up` dan
    boshlaydi, v1.3 ning `3 + 8 = 11 <= 12` arifmetikasi esa uni `t_inject`
    dan boshlagan (jimgina nol recovery vaqti). Oynasi hold'dan chiqqan trial
    §4 ning kattaligini O'LCHAMAGAN: 2- va 5-bandlar qisman bosimsiz
    baholanadi, VR osonlashadi, trend susayadi va §11 qoidasi YOLG'ON
    FALSIFIKATSIYA chiqarishi mumkin. Buni `complete` deb yozish -- o'lchanmagan
    narsani o'lchov deb yozish, ya'ni §14.6 to'xtatishi kerak bo'lgan xato.

    Holatlar (`reduce.WINDOW_CONTAINMENTS`): `past_pressure` va `past_horizon`
    + raw `complete` = XATO. `T_h` o'lchanmagan (`not_evaluated`: nol
    "hech qachon o'rnatilmagan" demak, o'lchangan nol EMAS) -- hukm
    TO'QILMAYDI: reducer kabi disposition o'zgarmaydi, lekin soni
    OGOHLANTIRISH bilan ko'rsatiladi (`summary["n_window_containment_not_
    evaluated"]` ning validator tomoni). `T_h`/`T_trial` -- `trial_end.timing.
    pressure_off_mono_us` / `horizon_end_mono_us`.
    """
    prm = Params(probe_period_us=probe_period_us, w_stab_us=_run_w_stab_us(run))
    out: list[Finding] = []
    not_eval: list[str] = []
    for t in split_trials(run):
        if t.disposition_raw != "complete" or t.end is None:
            continue
        w = _trial_window(t, prm)
        if w.status in (WINDOW_PAST_PRESSURE, WINDOW_PAST_HORIZON):
            out.append(Finding(
                "window_outside_hold_complete", SEVERITY_ERROR,
                f"'complete' trial'ning oynasi hold'dan chiqqan "
                f"({w.status}): t_up={w.t_up_us} + W_stab={w.w_stab_us} = "
                f"{w.window_end_us} > "
                f"{'T_trial ' + str(w.horizon_end_us) if w.status == WINDOW_PAST_HORIZON else 'T_h ' + str(w.hold_end_us)} "
                "-- §4 kattaligi o'lchanmagan, §17.4(5): `complete` bo'lishi "
                "mumkin emas (sustained hold ichida sig'ishi shart)",
                trial_id=t.trial_id, record_type=RT_TRIAL_END,
                **_where(t.end),
                detail={"window_containment": w.status, "t_up_us": w.t_up_us,
                        "window_end_us": w.window_end_us,
                        "w_stab_us": w.w_stab_us, "hold_end_us": w.hold_end_us,
                        "horizon_end_us": w.horizon_end_us,
                        "slack_to_hold_us": w.slack_to_hold_us,
                        "slack_to_horizon_us": w.slack_to_horizon_us}))
        elif w.status == WINDOW_NOT_EVALUATED:
            not_eval.append(t.trial_id)
    if not_eval:
        out.append(Finding(
            "window_containment_not_evaluated", SEVERITY_WARNING,
            f"{len(not_eval)} ta 'complete' trial'da T_h o'lchanmagan "
            "(`trial_end.timing.pressure_off_mono_us` yo'q yoki 0): oyna hold "
            "ichidami -- ANIQLANMAGAN, hukm to'qilmadi (§17.4-5)",
            trial_id=not_eval[0],
            detail={"n": len(not_eval), "trial_ids": not_eval[:200]}))
    return out


def check_trial_timing(run: RawRun) -> list[Finding]:
    """`trial_end.timing` ichki izchil: T_h trial ichida, horizon `mono_us` ga teng.

    NEGA: §17.4-5 tekshiruvi `T_h` ga tayanadi; bema'ni `T_h` (trial'dan
    oldin/horizon'dan keyin) har qanday oynani "hold ichida" yoki "tashqarida"
    qilib ko'rsatadi. `0` -- "hech qachon o'rnatilmagan" (monotonic
    timestamp), o'lchangan nol emas: tekshirilmaydi. Reducer
    `horizon_end_mono_us` ni `trial_end.mono_us` bilan bir deb oladi
    (reduce.Trial.horizon_end_us), ikkisi farq qilsa censoring nuqtasi ikki xil.
    """
    out: list[Finding] = []
    for tid, recs in sorted(_by_trial(run).items()):
        begin, end = _first(recs, RT_TRIAL_BEGIN), _first(recs, RT_TRIAL_END)
        timing = end.get("timing") if end else None
        if not isinstance(timing, dict):
            continue
        lo, hi = _mono(begin), _mono(end)
        h = _as_int(timing.get("pressure_off_mono_us"))
        he = _as_int(timing.get("horizon_end_mono_us"))
        probs: list[str] = []
        if h and lo is not None and hi is not None and not (lo < h <= hi):
            probs.append(f"pressure_off_mono_us={h} [{lo}, {hi}] dan tashqari")
        if he and hi is not None and he != hi:
            probs.append(f"horizon_end_mono_us={he} != trial_end.mono_us={hi}")
        if h and he and h > he:
            probs.append(f"pressure_off_mono_us={h} > horizon_end_mono_us={he}")
        if probs:
            out.append(Finding(
                "trial_timing_invalid", SEVERITY_ERROR,
                f"trial_end.timing izchil emas: {probs}", trial_id=tid,
                record_type=RT_TRIAL_END, **_where(end or {}),
                detail={"problems": probs}))
    return out


def check_trial_horizon(run: RawRun) -> list[Finding]:
    """`trial_end.mono_us - trial_begin.mono_us` `t_trial_us` ga mos.

    NEGA: kontrakt v1.1 §5.4-5: `trial_end` aynan `trial_begin + T_trial` da
    (yoki aborted_guard/harness_error bo'lsa OLDIN). `reduce.Trial.end_us`
    aynan shuni right-censoring nuqtasi (§6.2) deb oladi: horizon
    qayd etilgan `t_trial_us` bilan mos bo'lmasa, jimgina boshqa horizon
    ostida censor qilingan bo'ladi.
    """
    meta = run.run_meta or {}
    raw = meta.get("t_trial_us")
    if raw is None or isinstance(raw, (bool, str)) or _as_int(raw) is None:
        return []                      # run_meta_field_* xato beradi
    tt = int(raw)
    out: list[Finding] = []
    early_ok = ("aborted_guard", "harness_error")
    for tid, recs in sorted(_by_trial(run).items()):
        begin, end = _first(recs, RT_TRIAL_BEGIN), _first(recs, RT_TRIAL_END)
        lo, hi = _mono(begin), _mono(end)
        if lo is None or hi is None or hi <= lo or end is None:
            continue
        real = hi - lo
        disp = _as_str(end.get("disposition"))
        too_long = real > tt + T_TRIAL_TOLERANCE_US
        too_short = real < tt - T_TRIAL_TOLERANCE_US and disp not in early_ok
        if too_long or too_short:
            out.append(Finding(
                "trial_horizon_mismatch", SEVERITY_ERROR,
                f"trial davomiyligi {real} us, run_meta.t_trial_us={tt} "
                f"(tolerans {T_TRIAL_TOLERANCE_US} us, disposition={disp!r}) "
                "-- censoring nuqtasi qayd etilgan horizon emas (§6.2)",
                trial_id=tid, record_type=RT_TRIAL_END, **_where(end),
                detail={"realized_us": real, "t_trial_us": tt}))
    return out


# --- probe ------------------------------------------------------------------


def check_probe_fields(run: RawRun) -> list[Finding]:
    """Probe qatorlari reducer o'qiy oladigan va trial'larga bog'lanadigan.

    NEGA: `reduce.probe_from_record` yo'q `outcome` ni JIMGINA `bad_response`
    (ya'ni buzilgan probe) deb oladi -- o'qilmagan qator soxta downtime
    yaratadi; yopiq enum (03-sut-protokoli §8) tashqarisidagi qiymat ham
    buzilgan hisoblanadi. `ok` probe'da `progress` o'qilmasa §4.5
    throughput bandi o'lchanmaydi va VR jimgina `None` bo'ladi (kontrakt
    v1.1 §4.4-2a: `progress_counter` -> `progress` adapteri). Noma'lum
    `trial_id` li probe `split_trials` da JIMGINA tashlanadi. Bir trial'da
    bir nechta `target` bo'lsa reduce.py ularni aralashtiradi (uzilish va
    throughput hisobi buziladi) -- hozirgi reduce.py target'ni ajratmaydi.
    """
    known = _trial_ids(run)
    out: list[Finding] = []
    no_time: list[dict[str, Any]] = []
    bad_outcome: list[dict[str, Any]] = []
    no_prog: list[dict[str, Any]] = []
    orphan: dict[str, list[dict[str, Any]]] = {}
    for rec in run.probes:
        if (_as_int(rec.get("mono_us_send")) is None
                and _as_int(rec.get("mono_us")) is None):
            no_time.append(rec)
        oc = _as_str(rec.get("outcome"))
        if oc not in PROBE_OUTCOMES:
            bad_outcome.append(rec)
        elif oc == "ok" and _as_int(rec.get("progress")) is None:
            no_prog.append(rec)
        tid = _as_str(rec.get("trial_id"))
        if tid is not None and tid not in known:
            orphan.setdefault(tid, []).append(rec)
    if no_time:
        out.append(Finding(
            "probe_time_missing", SEVERITY_ERROR,
            f"{len(no_time)} ta probe'da mono_us_send/mono_us yo'q",
            record_type=RT_PROBE, **_where(no_time[0]),
            detail={"n": len(no_time), "first": _locs(no_time)}))
    if bad_outcome:
        out.append(Finding(
            "probe_outcome_unknown", SEVERITY_ERROR,
            f"{len(bad_outcome)} ta probe'da outcome yo'q yoki yopiq enumda "
            f"yo'q (reduce.py buni jimgina 'bad_response' deb oladi); "
            f"ruxsat: {list(PROBE_OUTCOMES)}", record_type=RT_PROBE,
            **_where(bad_outcome[0]),
            detail={"n": len(bad_outcome), "values": sorted(
                {str(r.get("outcome")) for r in bad_outcome})[:20],
                "first": _locs(bad_outcome)}))
    if no_prog:
        raw = sum(1 for r in no_prog
                  if _as_int(r.get("progress_counter")) is not None)
        out.append(Finding(
            "probe_progress_unreadable", SEVERITY_ERROR,
            f"{len(no_prog)} ta 'ok' probe'da `progress` o'qilmaydi -- "
            "throughput bandi (§4.5) o'lchanmaydi, VR None bo'ladi"
            + (f"; {raw} tasida `progress_counter` bor: reduksiya kirishida "
               "`normalise_probe_row` adapteri qo'llanmagan (kontrakt v1.1 §4.5)"
               if raw else ""),
            record_type=RT_PROBE, **_where(no_prog[0]),
            detail={"n": len(no_prog), "with_progress_counter": raw,
                    "first": _locs(no_prog)}))
    for tid, recs in sorted(orphan.items()):
        out.append(Finding(
            "probe_trial_unknown", SEVERITY_ERROR,
            f"{len(recs)} ta probe trial_id={tid!r} bilan, lekin bunday trial "
            "yo'q -- split_trials ularni jimgina tashlaydi",
            trial_id=tid, record_type=RT_PROBE, **_where(recs[0]),
            detail={"n": len(recs)}))
    return out


def check_probe_targets(run: RawRun, sut_target: str | None = None) -> list[Finding]:
    """Reducerga beriladigan probe'lar BITTA target'dan.

    NEGA: `reduce.split_trials` probe'larni FAQAT `trial_id` bo'yicha
    guruhlaydi: bystander probe'lari SUT'nikiga aralashib uzilish (§4),
    throughput (§4.5) va downtime (§6.1) hisobini buzadi. Xom `probe.csv`
    ikkala target'ni saqlashi MUMKIN; reducerga beriladigan ko'rinish esa
    bitta target bo'lishi SHART (`reducer_view`, `--sut-target`). Qoida
    `unit_state_units_mixed` bilan bir xil.
    """
    targets: dict[str, set[str]] = {}
    for rec in run.probes:
        tid, tg = _as_str(rec.get("trial_id")), _as_str(rec.get("target"))
        if tid is not None and tg is not None:
            targets.setdefault(tid, set()).add(tg)
    out: list[Finding] = []
    for tid, tg in sorted(targets.items()):
        if len(tg) > 1:
            out.append(Finding(
                "probe_targets_mixed", SEVERITY_ERROR,
                f"trial'da bir nechta probe target: {sorted(tg)} -- "
                "reduce.py target'ni ajratmaydi, uzilish/throughput hisobi "
                "aralashadi (reducerga beriladigan kirishni bitta target'ga "
                "filtrlang: --sut-target)", trial_id=tid, record_type=RT_PROBE,
                detail={"targets": sorted(tg)}))
    return out


def check_unit_state_units(run: RawRun, sut_unit: str | None = None) -> list[Finding]:
    """Reducerga beriladigan `unit_state` lar BITTA unit'dan.

    NEGA: `reduce.split_trials` `unit_state` ni FAQAT trial bo'yicha
    guruhlaydi. Bystander unit'ning `NRestarts` va `InvocationID` qiymatlari
    SUT'nikiga aralashsa, §4 verified-recovery ning 3-bandi (InvocationID
    o'zgarmaydi) va 4-bandi (NRestarts o'zgarmaydi) -- `evaluate_vr` va
    `_invocation_changed` -- yolg'on `invocation_changed`/`nrestarts_changed`
    beradi yoki haqiqiyni yashiradi. Xom `events.jsonl` ikkala unit'ni
    saqlashi QONUNIY (`unit` maydoni bilan ajraladi); reducerga beriladigan
    ko'rinish esa bitta unit bo'lishi SHART. Nomi va og'irligi
    `probe_targets_mixed` bilan bir xil. `sut_unit` berilsa, har o'lchangan
    trial'da shu unit'ning `unit_state` i bo'lishi ham tekshiriladi
    (aks holda 3-4 bandlar jimgina `unverified` bo'ladi).
    """
    units: dict[str, set[str]] = {}
    for r in run.of_type(RT_UNIT_STATE):
        tid, u = _as_str(r.get("trial_id")), _as_str(r.get("unit"))
        if tid is not None and u is not None:
            units.setdefault(tid, set()).add(u)
    out: list[Finding] = []
    for tid, us in sorted(units.items()):
        if len(us) > 1:
            out.append(Finding(
                "unit_state_units_mixed", SEVERITY_ERROR,
                f"trial'da bir nechta unit'ning unit_state i: {sorted(us)} -- "
                "reduce.py unit'ni ajratmaydi, NRestarts/InvocationID "
                "aralashadi (§4 band 3-4); reducerga beriladigan kirishni "
                "SUT unit'iga filtrlang: --sut-unit", trial_id=tid,
                record_type=RT_UNIT_STATE, detail={"units": sorted(us)}))
    if sut_unit is not None:
        for e in run.of_type(RT_TRIAL_END):
            tid = _as_str(e.get("trial_id"))
            if (_as_str(e.get("disposition")) in MEASURED_DISPOSITIONS
                    and tid is not None and sut_unit not in units.get(tid, set())):
                out.append(Finding(
                    "sut_unit_state_missing", SEVERITY_ERROR,
                    f"o'lchangan trial'da {sut_unit!r} ning unit_state i yo'q "
                    "(`unit` maydoni yo'q yoki boshqa unit) -- §4 band 3-4 "
                    "o'lchanmaydi", trial_id=tid, record_type=RT_UNIT_STATE))
    return out


def check_disposition_cross_check(run: RawRun,
                                  probe_period_us: int = P_US) -> list[Finding]:
    """Driver disposition'i `reduce.derive_disposition` bilan solishtiriladi.

    NEGA: §12 -- driver yozgan `trial_end.disposition` AVTORITET
    (`schedule.explain_disposition` orqali), `reduce.derive_disposition` esa
    tekshiruv. Ikkisi bir trial'da farq qilsa (masalan raw `complete`, lekin
    horizon down holatda tugagan -> reducer `censored` deydi) yashirin
    nomuvofiqlik ko'rinadigan bo'ladi. Ma'lum ochiq savol:
    `schedule.DISPOSITION_RULES` `harness_error` ni `aborted_guard` dan
    yuqori qo'yadi, reducer teskarisi. Bu OGOHLANTIRISH: qaysi biri haqiqat
    ekani kontraktda (v1.2) hal qilinadi, validator tanlamaydi.

    §17.4: reducer oyna holatini (`window_past_pressure`/`window_past_horizon`
    -> `censored`) hisobga oladi; shu sababli validator ham AYNI
    `WindowContainment` ni uzatadi, aks holda reducer ko'rgan farq driver
    xatosi bo'lib ko'rinardi. Raw `complete` + oyna hold'dan chiqqan holat
    bu yerda ogohlantirish, `check_window_containment` da esa XATO.
    """
    prm = Params(probe_period_us=probe_period_us, w_stab_us=_run_w_stab_us(run))
    out: list[Finding] = []
    for t in split_trials(run):
        raw = t.disposition_raw
        if t.end is None or raw is None:
            continue
        down = bool(t.probes) and not t.probes[-1].passed
        # §17.4: oyna holati `reduce_trial` bilan AYNI operandlardan beriladi;
        # aks holda (a)/(b) trial'lar uchun soxta farq chiqardi.
        final, src, _c = derive_disposition(t, probe_gaps(t, prm), down,
                                            _trial_window(t, prm))
        if final != raw:
            out.append(Finding(
                "disposition_cross_check", SEVERITY_WARNING,
                f"driver disposition={raw!r}, reducer hosilasi={final!r} "
                f"(manba: {src}) -- ikkisi farq qiladi (driver avtoritet, §12)",
                trial_id=t.trial_id, record_type=RT_TRIAL_END,
                detail={"driver": raw, "reducer": final, "reducer_source": src}))
    return out


def reducer_view(run: RawRun, sut_unit: str | None = None,
                 sut_target: str | None = None) -> RawRun:
    """Reducerga BERILADIGAN ko'rinish: faqat SUT unit_state va SUT probe.

    Xom oqim ikkala unit/target'ni saqlaydi (seq/envelope tekshiruvlari
    TO'LIQ xom oqimda ishlaydi, aks holda filtr sun'iy seq bo'shlig'i
    yaratardi). Hisob tekshiruvlari esa reducer ko'radigan narsada.
    `unit`/`target` maydoni yo'q record filtrlanganda tashlanadi.
    """
    recs = [r for r in run.records
            if not (sut_unit is not None and r.get("record_type") == RT_UNIT_STATE
                    and _as_str(r.get("unit")) != sut_unit)]
    prbs = [p for p in run.probes
            if not (sut_target is not None and _as_str(p.get("target")) != sut_target)]
    return RawRun(records=recs, probes=prbs, sources=list(run.sources))


def check_probe_coverage(run: RawRun, probe_period_us: int = P_US) -> list[Finding]:
    """Probe trace trial chegaralarigacha uzluksiz va bo'sh emas.

    NEGA: §14.6-4 / §4 "trial ichida probe uzilishi > 2xP -> censored".
    Mavjud `check_probe_gaps` faqat ketma-ket IKKI probe orasini ko'radi, shu
    sababli prober trial o'rtasida o'lsa (oxirgi probe'dan trial_end'gacha
    uzilish) yoki trial'da bitta ham probe bo'lmasa -- uzilish ko'rinmaydi va
    trial `complete` bo'lib o'tib ketadi. Horizon `trial_end.mono_us` (§6.2,
    kontrakt §4.3): reducer downtime'ni shu nuqtagacha hisoblaydi, demak
    probe'lar shu nuqtagacha qoplashi SHART. Bosh chegara -- `baseline_window`
    boshi (o'lchov boshlanishi; preflight o'lchov emas). Jazo mavjud
    `probe_gap` bilan bir xil: disposition `GAP_WARNING_DISPOSITIONS` da
    bo'lsa OGOHLANTIRISH, aks holda (`complete`, noma'lum) XATO.
    """
    out: list[Finding] = []
    lim = 2 * probe_period_us
    for t in split_trials(run):
        if t.end is None:
            continue
        disp = t.disposition_raw
        hi = _as_int(t.end.get("mono_us"))
        if not t.probes:
            if disp == "complete":
                out.append(Finding(
                    "trial_without_probes", SEVERITY_ERROR,
                    "'complete' trial'da BITTA ham probe yo'q -- butun trial "
                    "bo'yicha instrumentatsiya yo'qolgan (§4: 'censored' "
                    "bo'lishi SHART)", trial_id=t.trial_id,
                    record_type=RT_PROBE))
            continue
        gaps: list[dict[str, Any]] = []
        if t.baseline_windows:
            b = _as_int(t.baseline_windows[0].get("mono_us_begin"))
            if b is not None and t.probes[0].mono_us - b > lim:
                gaps.append({"where": "leading", "from_us": b,
                             "to_us": t.probes[0].mono_us,
                             "gap_us": t.probes[0].mono_us - b})
        if hi is not None and hi - t.probes[-1].mono_us > lim:
            gaps.append({"where": "trailing", "from_us": t.probes[-1].mono_us,
                         "to_us": hi, "gap_us": hi - t.probes[-1].mono_us})
        if gaps:
            sev = (SEVERITY_WARNING if disp in GAP_WARNING_DISPOSITIONS
                   else SEVERITY_ERROR)
            msg = (f"probe qoplami trial chegarasida uzilgan "
                   f"({[g['where'] for g in gaps]}, > 2xP = {lim} us); "
                   f"disposition={disp!r}")
            if sev == SEVERITY_ERROR:
                msg += " -- §4 ga ko'ra 'censored' bo'lishi SHART"
            out.append(Finding("probe_coverage_gap", sev, msg,
                               trial_id=t.trial_id, record_type=RT_PROBE,
                               detail={"gaps": gaps, "limit_us": lim,
                                       "disposition": disp}))
    return out


def check_prober_stream(run: RawRun) -> list[Finding]:
    """CSV probe oqimi `prober_start` orqali run'ga bog'langan.

    NEGA: §14.2 -- "CSV oqimlarida envelope yo'q; ular `<stream>_start`
    record'i orqali run'ga bog'lanadi". `prober_start` yo'q bo'lsa CSV
    qatorlari qaysi run/boot'ga tegishli ekani noma'lum (monotonic
    qiymatlar faqat bitta boot ichida, §1). Kontrakt v1.1 §4.5-a: har trial
    uchun alohida prober jarayoni -- shuning uchun bir nechta start/stop
    juftligi NORMAL (bitta prober kutilmaydi). `prober_stop` `finally` da
    yoziladi; yo'qligi -- prober o'ldirilgan, CSV buferining oxiri
    yo'qolgan bo'lishi mumkin: OGOHLANTIRISH (yo'qotish probe qoplami
    tekshiruvida alohida ko'rinadi).
    """
    if not run.probes:
        return []
    starts, stops = run.of_type(RT_PROBER_START), run.of_type(RT_PROBER_STOP)
    if not starts:
        return [Finding(
            "prober_start_missing", SEVERITY_ERROR,
            "probe qatorlari bor, lekin birorta prober_start yo'q -- CSV run'ga "
            "bog'lanmagan (§14.2)", record_type=RT_PROBER_START)]
    if len(stops) < len(starts):
        return [Finding(
            "prober_stop_missing", SEVERITY_WARNING,
            f"{len(starts)} ta prober_start, lekin {len(stops)} ta "
            "prober_stop -- prober to'g'ri to'xtamagan (CSV oxiri yo'qolgan "
            "bo'lishi mumkin)", record_type=RT_PROBER_STOP)]
    return []


# --- guard va harness xatolari ----------------------------------------------


def check_guard_stream(run: RawRun) -> list[Finding]:
    """Guard oqimi: start/stop bor, `trial_id` YO'Q, birinchi/oxirgi, hisobga olingan.

    NEGA: kontrakt §1.3-1,2: guard BIRINCHI start, OXIRGI stop; ishga
    tushmasa run boshlanmaydi (fail-closed) -- guard_start yo'q run'da
    xavfsizlik chegarasi ishlaganiga dalil yo'q. `guard_event` da `trial_id`
    YO'Q -- bu TO'G'RI (§14.7, §8.2: guard mustaqil jarayon); `trial_id`
    bo'lsa u mustaqil emas. Atributsiya MONOTONIC vaqt bo'yicha (reduce.
    split_trials), shuning uchun u trial oynasiga tushadi: oynasida guard
    ishlagan trial'ning raw disposition'i `GUARD_REFLECTED_DISPOSITIONS`
    (`aborted_guard` yoki tartibda undan oldin turgan `harness_error`) dan
    boshqa bo'lsa -- `contaminated`/`washout_timeout` ham -- driver o'z
    xavfsizlik guard'ining ishlaganini ko'rmagan yoki §12 ustuvorligini
    buzgan (kill_subtree dan keyingi yozuvlar axlat). Oynadan tashqaridagi
    guard_event atributsiya qilinmaydi: OGOHLANTIRISH.
    """
    out: list[Finding] = []
    starts, stops = run.of_type(RT_GUARD_START), run.of_type(RT_GUARD_STOP)
    events = run.of_type(RT_GUARD_EVENT)
    if not starts:
        out.append(Finding("guard_start_missing", SEVERITY_ERROR,
                           "guard_start yo'q -- guard ishlaganiga dalil yo'q "
                           "(kontrakt §1.3-1,2: fail-closed)",
                           record_type=RT_GUARD_START))
    if not stops:
        out.append(Finding("guard_stop_missing", SEVERITY_ERROR,
                           "guard_stop yo'q -- guard to'g'ri to'xtamagan yoki "
                           "log tugamagan", record_type=RT_GUARD_STOP))
    for e in events:
        if _as_str(e.get("trial_id")) is not None:
            out.append(Finding(
                "guard_event_has_trial_id", SEVERITY_ERROR,
                f"guard_event da trial_id={e.get('trial_id')!r} -- guard "
                "mustaqil jarayon, trial_id bo'lmasligi TO'G'RI (§14.7)",
                record_type=RT_GUARD_EVENT, **_where(e)))
    begins = [m for m in (_mono(r) for r in run.of_type(RT_TRIAL_BEGIN))
              if m is not None]
    ends = [m for m in (_mono(r) for r in run.of_type(RT_TRIAL_END))
            if m is not None]
    gs = [m for m in (_mono(r) for r in starts) if m is not None]
    ge = [m for m in (_mono(r) for r in stops) if m is not None]
    if gs and begins and min(gs) >= min(begins):
        out.append(Finding("guard_not_first", SEVERITY_ERROR,
                           f"guard_start ({min(gs)}) birinchi trial_begin "
                           f"({min(begins)}) dan OLDIN emas (kontrakt §1.3-1)",
                           record_type=RT_GUARD_START))
    if ge and ends and max(ge) <= max(ends):
        out.append(Finding("guard_not_last", SEVERITY_ERROR,
                           f"guard_stop ({max(ge)}) oxirgi trial_end ({max(ends)}) "
                           "dan KEYIN emas (kontrakt §1.3-1)",
                           record_type=RT_GUARD_STOP))
    windows: list[tuple[str, int, int, str | None]] = []
    for tid, recs in _by_trial(run).items():
        b, e = _first(recs, RT_TRIAL_BEGIN), _first(recs, RT_TRIAL_END)
        lo, hi = _mono(b), _mono(e)
        if lo is not None and hi is not None and e is not None:
            windows.append((tid, lo, hi, _as_str(e.get("disposition"))))
    unattributed: list[dict[str, Any]] = []
    flagged: dict[str, list[dict[str, Any]]] = {}
    flagged_disp: dict[str, str | None] = {}
    for g in events:
        t = _mono(g)
        if t is None:
            continue
        hit = next(((tid, d) for tid, lo, hi, d in windows if lo <= t <= hi), None)
        if hit is None:
            unattributed.append(g)
        elif hit[1] not in GUARD_REFLECTED_DISPOSITIONS:
            flagged.setdefault(hit[0], []).append(g)
            flagged_disp[hit[0]] = hit[1]
    for tid, gl in sorted(flagged.items()):
        out.append(Finding(
            "guard_event_not_reflected", SEVERITY_ERROR,
            f"trial oynasida {len(gl)} ta guard_event, lekin raw disposition="
            f"{flagged_disp[tid]!r} -- 'aborted_guard' (yoki undan oldin "
            "turgan 'harness_error') bo'lishi SHART (§12 ustuvorligi)",
            trial_id=tid, record_type=RT_GUARD_EVENT, **_where(gl[0]),
            detail={"disposition": flagged_disp[tid]}))
    if unattributed:
        out.append(Finding(
            "guard_event_unattributed", SEVERITY_WARNING,
            f"{len(unattributed)} ta guard_event birorta trial oynasiga "
            "tushmaydi", record_type=RT_GUARD_EVENT, **_where(unattributed[0]),
            detail={"first": _locs(unattributed)}))
    return out


def check_harness_errors(run: RawRun) -> list[Finding]:
    """`harness_error` record'i bor trial'ning disposition'i `harness_error`.

    NEGA: §12 `harness_error` -- harness istisnosi; prober.py: "Driver bu
    record'ni ko'rib trial'ga harness_error disposition beradi". Aks holda
    instrument xatosi bo'lgan trial `complete` bo'lib birlamchi analizga
    kiradi. Trial'ga bog'lanmagan harness_error: OGOHLANTIRISH.
    """
    disp: dict[str, str | None] = {}
    for e in run.of_type(RT_TRIAL_END):
        disp.setdefault(_as_str(e.get("trial_id")) or "",
                        _as_str(e.get("disposition")))
    out: list[Finding] = []
    per: dict[str, list[dict[str, Any]]] = {}
    free: list[dict[str, Any]] = []
    for r in run.of_type(RT_HARNESS_ERROR):
        tid = _as_str(r.get("trial_id"))
        (free if tid is None else per.setdefault(tid, [])).append(r)
    for tid, recs in sorted(per.items()):
        if disp.get(tid) != "harness_error":
            out.append(Finding(
                "harness_error_not_reflected", SEVERITY_ERROR,
                f"{len(recs)} ta harness_error, lekin trial disposition="
                f"{disp.get(tid)!r} (§12: 'harness_error' bo'lishi kerak)",
                trial_id=tid, record_type=RT_HARNESS_ERROR, **_where(recs[0])))
    if free:
        out.append(Finding(
            "harness_error_unattributed", SEVERITY_WARNING,
            f"{len(free)} ta harness_error trial'ga bog'lanmagan",
            record_type=RT_HARNESS_ERROR, **_where(free[0])))
    return out


# ===========================================================================
# run katalogi (kontrakt §1) va yig'ma tekshiruv
# ===========================================================================

RUN_DIR_REQUIRED = ("events.jsonl", "probe.csv", "guard.jsonl", "run_meta.json")
RUN_DIR_OPTIONAL = ("pressure.jsonl", "psi.csv")


def _adapt_probe_row(rec: dict[str, Any]) -> None:
    """`progress_counter` -> `progress` (kontrakt v1.1 §4.5), faqat QO'SHADI.

    reduce.py `progress` o'qiydi, prober `progress_counter` yozadi. Xom kalit
    O'CHIRILMAYDI va mavjud `progress` USTIGA yozilmaydi. Validator reducer
    ko'radigan narsani tekshirishi uchun shu moslashtirish bu yerda ham bor
    (driver `normalise_probe_row` i paydo bo'lganda ikkisi bir xil bo'lishi
    kerak).
    """
    if rec.get("progress") in (None, "") and rec.get("progress_counter") not in (None, ""):
        rec["progress"] = rec["progress_counter"]


def load_run_dir(run_dir: str) -> tuple[RawRun, list[Finding]]:
    """Run katalogini `RawRun` ga o'qiydi. Kutilgan muammolar Finding bo'ladi.

    NEGA: `RawRun.load` `run_meta.json` ni (bitta obyekt, JSONL emas)
    o'qimaydi -- uni qo'shmasdan `run_meta_missing` chiqardi. Yo'q/buzuq
    fayl FAIL-CLOSED: xato Finding, jimgina o'tkazib yuborish emas.
    `datasets/` append-only: bu funksiya hech narsaga YOZMAYDI.
    """
    findings: list[Finding] = []
    run = RawRun()
    if not os.path.isdir(run_dir):
        return run, [Finding("run_dir_missing", SEVERITY_ERROR,
                             f"run katalogi yo'q: {run_dir!r}", source=run_dir)]
    paths = {n: os.path.join(run_dir, n)
             for n in RUN_DIR_REQUIRED + RUN_DIR_OPTIONAL}
    for n, p in paths.items():
        if not os.path.isfile(p):
            findings.append(Finding(
                "run_dir_file_missing",
                SEVERITY_ERROR if n in RUN_DIR_REQUIRED else SEVERITY_WARNING,
                f"{n} yo'q (kontrakt §1)", source=p))
    meta_rec: dict[str, Any] | None = None
    if os.path.isfile(paths["run_meta.json"]):
        p = paths["run_meta.json"]
        try:
            with open(p, "r", encoding="utf-8") as fh:
                obj = json.load(fh)
            if not isinstance(obj, dict):
                raise ValueError("run_meta.json obyekt emas")
            if obj.get("record_type") not in (None, RT_RUN_META):
                raise ValueError(f"record_type={obj.get('record_type')!r}")
            meta_rec = dict(obj)
            meta_rec["record_type"] = RT_RUN_META
            meta_rec.setdefault("__source__", p)
            meta_rec.setdefault("__index__", 1)
        except (OSError, ValueError) as exc:
            findings.append(Finding("run_meta_unreadable", SEVERITY_ERROR,
                                    f"run_meta.json o'qib bo'lmadi: {exc}",
                                    source=p))
    jsonl = [paths[n] for n in ("events.jsonl", "guard.jsonl", "pressure.jsonl")
             if os.path.isfile(paths[n])]
    csvs = [paths["probe.csv"]] if os.path.isfile(paths["probe.csv"]) else []
    try:
        run = RawRun.load(jsonl, csvs)
    except Exception as exc:  # noqa: BLE001 -- fail-closed
        findings.append(Finding("run_dir_unreadable", SEVERITY_ERROR,
                                f"kirishni o'qib bo'lmadi: {exc!r}",
                                source=run_dir))
        run = RawRun()
    if meta_rec is not None:
        # Driver run_meta'ni IKKI joyga yozadi: `run_meta.json` (payload) va
        # `events.jsonl` record'i (envelope bilan). Ikkisi bo'lsa envelope'li
        # nusxa ishlatiladi, `.json` esa u bilan SOLISHTIRILADI: farq qilsa
        # qaysi biri haqiqat ekani noma'lum.
        ev = [r for r in run.records if r.get("record_type") == RT_RUN_META]
        if ev:
            skip = set(ENVELOPE_FIELDS)
            a = {k: v for k, v in meta_rec.items()
                 if k not in skip and not k.startswith("__")}
            b = {k: v for k, v in ev[0].items()
                 if k not in skip and not k.startswith("__")}
            if a != b:
                diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
                findings.append(Finding(
                    "run_meta_copies_differ", SEVERITY_ERROR,
                    "run_meta.json events.jsonl dagi run_meta record'idan "
                    f"farq qiladi: {diff[:10]}", source=paths["run_meta.json"],
                    detail={"fields": diff[:50]}))
        else:
            run.records.insert(0, meta_rec)
            run.sources.insert(0, paths["run_meta.json"])
    for pr in run.probes:
        _adapt_probe_row(pr)
    return run, findings


def _safe(name: str, fn: Callable[..., list[Finding]], *args: Any,
          **kw: Any) -> list[Finding]:
    """FAIL-CLOSED o'ram: tekshiruv ichidagi istisno = xato, o'tish emas."""
    try:
        return list(fn(*args, **kw))
    except Exception as exc:  # noqa: BLE001
        return [Finding(
            "validator_internal_error", SEVERITY_ERROR,
            f"{name} tekshiruvi istisno bilan to'xtadi: {exc!r} -- tekshirib "
            "bo'lmagan run O'TMAYDI",
            detail={"check": name, "traceback": traceback.format_exc(limit=8)})]


# --- yig'ma tekshiruv -------------------------------------------------------


def validate_run(run: RawRun, *, run_mode: str | None = None,
                 probe_period_us: int = P_US, sut_unit: str | None = None,
                 sut_target: str | None = None) -> Report:
    """Barcha invariantlarni tekshiradi va HAR buzilishni qaytaradi.

    Birinchi xatoda to'xtamaydi: run'ni tuzatish uchun to'liq ro'yxat kerak.
    Istisno ko'tarmaydi: har tekshiruv `_safe` ichida, istisno = xato.

    `sut_unit`/`sut_target`: xom oqim bir nechta unit/target saqlashi
    mumkin; hisob tekshiruvlari (probe, action, unit_state) reducerga
    BERILADIGAN ko'rinishda (`reducer_view`) ishlaydi. Berilmasa, run
    aynan reducerga beriladigan narsa deb olinadi.
    """
    rv = reducer_view(run, sut_unit, sut_target)
    checks: list[tuple[str, Callable[..., list[Finding]], tuple[Any, ...]]] = [
        ("read_errors", check_read_errors, (run,)),
        ("run_meta", check_run_meta, (run, run_mode)),
        ("run_mode", check_run_mode, (run, run_mode)),
        ("run_meta_fields", check_run_meta_fields, (run,)),
        ("units_show", check_units_show, (run,)),
        ("schedule", check_schedule, (run,)),
        ("envelope", check_envelope, (run,)),
        ("run_identity", check_run_identity, (run,)),
        ("guest_generation", check_guest_generation, (run,)),
        ("monotonic_order", check_monotonic_order, (run,)),
        ("host_clock_discontinuity", check_host_clock_discontinuity, (run,)),
        ("schema_version", check_schema_version, (run,)),
        ("boot_id", check_boot_id, (run,)),
        ("trial_pairs", check_trial_pairs, (run,)),
        ("trial_set", check_trial_set, (run,)),
        ("dispositions", check_dispositions, (run,)),
        ("record_fields", check_record_fields, (run,)),
        ("planned_timeline", check_planned_timeline, (run, probe_period_us)),
        ("trial_events", check_trial_events, (run,)),
        ("trial_overhead", check_trial_overhead, (run,)),
        ("trial_horizon", check_trial_horizon, (run,)),
        ("trial_timing", check_trial_timing, (run,)),
        ("seq", check_seq, (run,)),
        ("probe_fields", check_probe_fields, (rv,)),
        ("probe_targets", check_probe_targets, (rv, sut_target)),
        ("unit_state_units", check_unit_state_units, (rv, sut_unit)),
        ("probe_gaps", check_probe_gaps, (rv, probe_period_us)),
        ("probe_coverage", check_probe_coverage, (rv, probe_period_us)),
        ("window_containment", check_window_containment, (rv, probe_period_us)),
        ("disposition_cross_check", check_disposition_cross_check,
         (rv, probe_period_us)),
        ("prober_stream", check_prober_stream, (run,)),
        ("actions", check_actions, (rv,)),
        ("guard_stream", check_guard_stream, (run,)),
        ("harness_errors", check_harness_errors, (run,)),
    ]
    findings: list[Finding] = []
    for name, fn, args in checks:
        findings += _safe(name, fn, *args)

    mode = _resolve_mode(run, run_mode)
    try:
        n_trials = len(split_trials(run))
    except Exception:  # noqa: BLE001 -- sabab tekshiruvlarda allaqachon xato
        n_trials = len(_trial_ids(run))
    return Report(findings=findings, n_records=len(run.records),
                  n_probes=len(run.probes), n_trials=n_trials,
                  sources=list(run.sources), run_mode=mode)


def validate_run_dir(run_dir: str, *, run_mode: str | None = None,
                     probe_period_us: int = P_US, sut_unit: str | None = None,
                     sut_target: str | None = None) -> Report:
    """Run katalogini o'qiydi va tekshiradi (o'qish muammolari ham xato)."""
    run, load_findings = load_run_dir(run_dir)
    rep = validate_run(run, run_mode=run_mode, probe_period_us=probe_period_us,
                       sut_unit=sut_unit, sut_target=sut_target)
    rep.findings[:0] = load_findings
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="REVIX run validator -- o'tmagan run ANALIZ QILINMAYDI (§14.6)")
    ap.add_argument("--run-dir", default=None,
                    help="run katalogi (kontrakt §1): events.jsonl, probe.csv, "
                         "guard.jsonl, pressure.jsonl, psi.csv, run_meta.json")
    ap.add_argument("--jsonl", action="append", default=[],
                    help="xom JSONL fayli; takrorlanadi")
    ap.add_argument("--probe-csv", action="append", default=[],
                    help="probe_sample CSV fayli; takrorlanadi")
    ap.add_argument("--run-mode", default=None,
                    choices=["pilot", "confirmatory"],
                    help="run_meta dagi qiymatni bosib o'tadi")
    ap.add_argument("--sut-unit", default=None,
                    help="reducerga beriladigan unit_state ko'rinishi: faqat shu "
                         "`unit` (xom oqim boshqa unit'ni saqlashi mumkin)")
    ap.add_argument("--sut-target", default=None,
                    help="reducerga beriladigan probe ko'rinishi: faqat shu "
                         "`target`")
    ap.add_argument("--probe-period-ms", type=float, default=P_US / 1000.0)
    ap.add_argument("--json", action="store_true", help="JSON hisobot")
    args = ap.parse_args(argv)

    if not args.jsonl and not args.probe_csv and not args.run_dir:
        ap.error("kamida bitta --run-dir, --jsonl yoki --probe-csv kerak")
    if args.run_dir and (args.jsonl or args.probe_csv):
        ap.error("--run-dir bilan --jsonl/--probe-csv aralashtirilmaydi")

    period = int(round(args.probe_period_ms * 1000))
    try:
        if args.run_dir:
            rep = validate_run_dir(args.run_dir, run_mode=args.run_mode,
                                   probe_period_us=period,
                                   sut_unit=args.sut_unit,
                                   sut_target=args.sut_target)
        else:
            run = RawRun.load(args.jsonl, args.probe_csv)
            rep = validate_run(run, run_mode=args.run_mode,
                               probe_period_us=period, sut_unit=args.sut_unit,
                               sut_target=args.sut_target)
    except Exception as exc:  # noqa: BLE001 -- FAIL-CLOSED: o'qib bo'lmadi = O'TMADI
        if args.json:
            json.dump({"ok": False, "error": repr(exc)}, sys.stdout, indent=2)
            sys.stdout.write("\n")
        else:
            print(f"O'TMADI -- kirishni o'qib bo'lmadi: {exc!r}")
        return 2

    if args.json:
        json.dump(rep.as_dict(), sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        for f in rep.findings:
            print(str(f))
        print(f"\nrecord: {rep.n_records}  probe: {rep.n_probes}  "
              f"trial: {rep.n_trials}  run_mode: {rep.run_mode}")
        print(f"xato: {len(rep.errors)}  ogohlantirish: {len(rep.warnings)}")
        print("NATIJA: " + ("O'TDI -- analiz qilinishi mumkin" if rep.ok
                            else "O'TMADI -- bu run ANALIZ QILINMAYDI (§14.6)"))
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
