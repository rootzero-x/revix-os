"""REVIX run validator -- analizdan OLDIN majburiy o'tadigan tekshiruv.

PREREGISTRATION.md §7 (reproducibility) va §12 (disposition) ga tayanadi:

    "Validator analizdan oldin o'tishi shart; o'tmagan run analiz qilinmaydi."

Shuning uchun bu fayl xato holatida MUVAFFAQIYAT QAYTARMAYDI: har xato
`Finding(severity="error")` sifatida chiqadi va `main()` nolga teng bo'lmagan
kod bilan tugaydi.

TEKSHIRILADIGAN INVARIANTLAR:
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

Bu invariantlar pre-registration'ning ruhini bajaradi: o'lchov ma'lumotining
jimgina yo'qolishi natijaga aylanmasligi kerak.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from typing import Any

from .schema import DISPOSITIONS, SCHEMA_VERSION
from .reduce import (
    P_US,
    RT_ACTION,
    RT_PROBE,
    RT_RUN_META,
    RT_TRIAL_BEGIN,
    RT_TRIAL_END,
    RawRun,
    _as_int,
    _as_str,
    split_trials,
)

# Ma'lum schema versiyalari. Tarix qayta yozilmaydi (schema.py): yangi versiya
# qo'shilsa SHU YERGA qo'shiladi, eskisi olib tashlanmaydi.
KNOWN_SCHEMA_VERSIONS = (SCHEMA_VERSION,)

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"

# Confirmatory run: §7 -- `git_dirty` false bo'lishi SHART.
CONFIRMATORY_MODES = ("confirmatory",)


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
    """Oqim kaliti: `(emitter, record_type)`.

    OGOHLANTIRISH (schema bo'shligi): `Emitter.envelope()` `stream` argumentini
    OLADI lekin record'ga YOZMAYDI. Shuning uchun oqim yorlig'i bilvosita
    `record_type` orqali taxmin qilinadi. Agar bitta emitter turli
    `record_type` larni BITTA oqimga yozsa, bu tekshiruv soxta bo'shliq
    ko'rsatadi -- markazda `stream` ni envelope'ga qo'shish kerak.
    """
    em = _as_str(rec.get("emitter"))
    rt = _as_str(rec.get("record_type"))
    if em is None or rt is None or rt.startswith("__"):
        return None
    return (em, rt)


def check_seq(run: RawRun) -> list[Finding]:
    """Oqimda `seq` bo'shliqlari yo'q.

    Bo'shliq = JIMGINA YO'QOLGAN RECORD. schema.py: "seq har OQIM uchun
    alohida monotonik, shunda validator bo'shliqni aniqlaydi. Bu jimgina
    ma'lumot yo'qolishini imkonsiz qiladi."
    """
    out: list[Finding] = []
    streams: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for rec in run.records:
        k = _stream_key(rec)
        if k is None or _as_int(rec.get("seq")) is None:
            continue
        streams.setdefault(k, []).append(rec)

    # probe CSV oqimida `emitter` yo'q -- fayl bo'yicha guruhlanadi.
    for rec in run.probes:
        s = _as_int(rec.get("seq"))
        if s is None:
            continue
        k = _stream_key(rec)
        if k is None:
            k = (f"csv:{rec.get('__source__')}", RT_PROBE)
        streams.setdefault(k, []).append(rec)

    for (em, rt), recs in sorted(streams.items()):
        seen: dict[int, dict[str, Any]] = {}
        for rec in recs:
            s = _as_int(rec.get("seq"))
            if s is None:
                continue
            if s in seen:
                out.append(Finding(
                    "seq_duplicate", SEVERITY_ERROR,
                    f"seq takrorlandi: {s}",
                    stream=f"{em}/{rt}", record_type=rt, seq=s,
                    trial_id=_as_str(rec.get("trial_id")),
                    source=_as_str(rec.get("__source__")),
                    index=_as_int(rec.get("__index__"))))
            else:
                seen[s] = rec
        if not seen:
            continue
        hi = max(seen)
        missing = [s for s in range(1, hi + 1) if s not in seen]
        if missing:
            out.append(Finding(
                "seq_gap", SEVERITY_ERROR,
                f"oqimda {len(missing)} ta record yo'qolgan "
                f"(1..{hi} dan): {missing[:20]}"
                + (" ..." if len(missing) > 20 else ""),
                stream=f"{em}/{rt}", record_type=rt,
                source=_as_str(recs[0].get("__source__")),
                detail={"missing_seq": missing[:200], "n_missing": len(missing),
                        "max_seq": hi}))
    return out


def check_probe_gaps(run: RawRun, probe_period_us: int = P_US) -> list[Finding]:
    """Trial ichida probe uzilishi > 2xP bo'lsa, trial `censored` bo'lishi SHART.

    §4: "Probe uzilishi > 2xP -> trial `censored`, `failed` EMAS.
    Instrumentatsiya yo'qolishi hech qachon jimgina natijaga aylanmaydi."
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
        sev = SEVERITY_ERROR if disp != "censored" else SEVERITY_WARNING
        msg = (f"{len(gaps)} ta probe uzilishi > 2xP ({lim} us), eng katta "
               f"{max(g for _a, _b, g in gaps)} us; disposition={disp!r}")
        if sev == SEVERITY_ERROR:
            msg += " -- §4 ga ko'ra 'censored' bo'lishi SHART"
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


# --- yig'ma tekshiruv -------------------------------------------------------


def validate_run(run: RawRun, *, run_mode: str | None = None,
                 probe_period_us: int = P_US) -> Report:
    """Barcha invariantlarni tekshiradi va HAR buzilishni qaytaradi.

    Birinchi xatoda to'xtamaydi: run'ni tuzatish uchun to'liq ro'yxat kerak.
    """
    findings: list[Finding] = []
    findings += check_read_errors(run)
    findings += check_run_meta(run, run_mode)
    findings += check_schema_version(run)
    findings += check_boot_id(run)
    findings += check_trial_pairs(run)
    findings += check_dispositions(run)
    findings += check_seq(run)
    findings += check_probe_gaps(run, probe_period_us)
    findings += check_actions(run)

    meta = run.run_meta or {}
    mode = run_mode or _as_str(meta.get("run_mode")) or _as_str(meta.get("mode"))
    return Report(findings=findings, n_records=len(run.records),
                  n_probes=len(run.probes), n_trials=len(split_trials(run)),
                  sources=list(run.sources), run_mode=mode)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="REVIX run validator -- o'tmagan run ANALIZ QILINMAYDI (§7)")
    ap.add_argument("--jsonl", action="append", default=[],
                    help="xom JSONL fayli; takrorlanadi")
    ap.add_argument("--probe-csv", action="append", default=[],
                    help="probe_sample CSV fayli; takrorlanadi")
    ap.add_argument("--run-mode", default=None,
                    choices=["pilot", "confirmatory"],
                    help="run_meta dagi qiymatni bosib o'tadi")
    ap.add_argument("--probe-period-ms", type=float, default=P_US / 1000.0)
    ap.add_argument("--json", action="store_true", help="JSON hisobot")
    args = ap.parse_args(argv)

    if not args.jsonl and not args.probe_csv:
        ap.error("kamida bitta --jsonl yoki --probe-csv kerak")

    run = RawRun.load(args.jsonl, args.probe_csv)
    rep = validate_run(run, run_mode=args.run_mode,
                       probe_period_us=int(round(args.probe_period_ms * 1000)))

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
                            else "O'TMADI -- bu run ANALIZ QILINMAYDI (§7)"))
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
