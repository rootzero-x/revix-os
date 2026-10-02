"""Uchdan-uchga zanjir testi: sintetik run -> validate -> reduce -> analiz.

PREREGISTRATION.md §14.6: "Validatsiyadan o'tmagan run analiz qilinmaydi."
Bu testlar zanjirning O'ZI ishlashini sinaydi va -- eng muhimi -- validator
HAQIQATAN darvoza ekanini: noto'g'ri run reducer'dan jimgina o'tib ketadi
(reduce.py units_show, guard va envelope'ni o'qimaydi), uni faqat validator
to'xtatadi.

DIQQAT: barcha ma'lumot SINTETIK (`tests/integration/synthetic.py`). Hech qanday
eksperiment ishga tushirilmagan; bu testlar HECH QANDAY natijani da'vo qilmaydi.

Zanjir tartibi: validate (DARVOZA) -> reduce -> yana validate (reduce xom
faylga tegmaganini tasdiqlash) -> analiz/figura (modul bo'lsa).
"""
import hashlib
import json
import os
import shutil

import pytest

from revix import reduce as R
from revix import validate as V
from tests.integration import synthetic as S

RAW_FILES = ("events.jsonl", "probe.csv", "guard.jsonl", "pressure.jsonl",
             "psi.csv", "run_meta.json")


@pytest.fixture(scope="module")
def base_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("synthetic") / "run"
    S.write_run(str(d))
    return str(d)


@pytest.fixture
def run_dir(base_dir, tmp_path):
    """Har test O'Z nusxasida: buzish testlari bir-birini ifloslantirmaydi."""
    d = tmp_path / "run"
    shutil.copytree(base_dir, d)
    return str(d)


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def error_codes(rep):
    return {f.code for f in rep.errors}


# --- fayl darajasidagi buzish yordamchilari ---------------------------------


def read_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path, recs):
    with open(path, "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")


def edit_events(d, fn, name="events.jsonl"):
    p = os.path.join(d, name)
    recs = read_jsonl(p)
    out = fn(recs)
    write_jsonl(p, recs if out is None else out)


def edit_run_meta(d, fn):
    """run_meta IKKI joyda (json + events): ikkalasini bir xil o'zgartiradi."""
    p = os.path.join(d, "run_meta.json")
    with open(p, encoding="utf-8") as fh:
        meta = json.load(fh)
    fn(meta)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, sort_keys=True)

    def ev(recs):
        for r in recs:
            if r["record_type"] == "run_meta":
                fn(r)
    edit_events(d, ev)


def edit_probe_csv(d, fn):
    p = os.path.join(d, "probe.csv")
    with open(p, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    out = fn(lines)
    with open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines if out is None else out) + "\n")


# --- 1. toza sintetik run zanjirdan o'tadi ----------------------------------


def test_sintetik_run_katalogi_kontrakt_tartibida_yoziladi(base_dir):
    assert sorted(os.listdir(base_dir)) == sorted(RAW_FILES)
    meta = json.load(open(os.path.join(base_dir, "run_meta.json"),
                          encoding="utf-8"))
    assert meta["synthetic_fixture"] is True       # aniq sintetik
    assert meta["run_id"].startswith("synthetic-")
    assert meta["preregistration_sha256"] == S.SYNTHETIC_SHA
    assert meta["governor"] is None                # WSL2: o'lchanmadi


def test_zanjir_toza_run_validatsiyadan_otadi(base_dir):
    run, load_findings = V.load_run_dir(base_dir)
    assert load_findings == []
    rep = V.validate_run(run)
    assert rep.findings == [], [str(f) for f in rep.findings]
    assert rep.ok is True
    assert rep.n_trials == 12


def test_zanjir_cli_toza_run_nol_qaytaradi(base_dir, capsys):
    assert V.main(["--run-dir", base_dir]) == 0
    assert "O'TDI" in capsys.readouterr().out


def test_zanjir_reduce_validatsiyadan_keyin_va_xom_fayl_ozgarmaydi(
        base_dir, tmp_path):
    before = {n: sha(os.path.join(base_dir, n)) for n in RAW_FILES}

    run, _ = V.load_run_dir(base_dir)
    gate = V.validate_run(run)
    assert gate.ok                                  # DARVOZA

    out = R.reduce_run(run, sweep=True)
    paths = R.write_output(out, str(tmp_path / "derived"), run)

    # §6.2: trial tashlanmaydi.
    assert out.summary["n_trials_in"] == out.summary["n_trials_out"] == 12
    assert sum(out.summary["disposition_counts"].values()) == 12
    # Adapter ishladi: throughput o'lchanadi, VR jimgina None bo'lmagan.
    assert out.summary["vr_undetermined"] == 0
    # §14.5: derived alohida fayllarda, envelope bilan.
    for key in ("trials", "episodes", "summary", "sweep"):
        assert os.path.isfile(paths[key])
    trials = read_jsonl(paths["trials"])
    assert len(trials) == 12
    assert {t["record_type"] for t in trials} == {"trial_metrics"}
    assert all(t["run_id"] == S.RUN_ID and t["boot_id"] == S.BOOT_ID
               for t in trials)

    # Reduce xom fayllarga TEGMADI (§14.5-2) va validatsiya o'zgarmadi.
    assert {n: sha(os.path.join(base_dir, n)) for n in RAW_FILES} == before
    run2, _ = V.load_run_dir(base_dir)
    assert V.validate_run(run2).as_dict() == gate.as_dict()


def test_zanjir_filtrlangan_smoke_run_ogohlantirish_bilan_otadi(tmp_path):
    """`--only A,P0`: jadval to'liq yoziladi, bajarilgan qism `only` da."""
    d = tmp_path / "smoke"
    S.write_run(str(d), only=("A", "P0"))
    rep = V.validate_run_dir(str(d))
    assert rep.ok, [str(f) for f in rep.errors]
    assert [f.code for f in rep.warnings] == ["run_filtered"]
    assert rep.n_trials == 2


def test_zanjir_validate_run_dir_va_validate_run_bir_xil(base_dir):
    run, load_findings = V.load_run_dir(base_dir)
    assert V.validate_run_dir(base_dir).as_dict() == \
        V.validate_run(run).as_dict()


# --- 2. analiz va figura: modul bo'lmasa HALOL skip --------------------------


def _reduced(base_dir, tmp_path):
    run, _ = V.load_run_dir(base_dir)
    assert V.validate_run(run).ok
    out = R.reduce_run(run, sweep=True)
    return R.write_output(out, str(tmp_path / "derived"), run)


def test_zanjir_analiz(base_dir, tmp_path):
    """reduce chiqishi -> `revix.analyze` -> analysis.json.

    `revix/analyze.py` parallel yoziladi; yo'q bo'lsa test SKIP (bu qism
    ishga tushmagan -- o'tgan deb hisoblanmaydi). CLI delegatsiyasi
    (`revix analyze`) bergan argv bilan chaqiriladi.
    """
    analyze = pytest.importorskip("revix.analyze")
    paths = _reduced(base_dir, tmp_path)
    out = tmp_path / "analysis.json"
    rc = analyze.main(["--trials", paths["trials"], "--run-meta",
                       os.path.join(base_dir, "run_meta.json"),
                       "--out", str(out)])
    assert rc in (0, None)
    a = json.load(open(out, encoding="utf-8"))
    assert a["schema_version"] == 1
    assert a["preregistration_sha256"] == S.SYNTHETIC_SHA
    assert a["n_trials"]["total"] == 12


def test_zanjir_figura(base_dir, tmp_path):
    """analysis.json -> `revix.figures` (matplotlib kerak)."""
    analyze = pytest.importorskip("revix.analyze")
    figures = pytest.importorskip("revix.figures")
    paths = _reduced(base_dir, tmp_path)
    out = tmp_path / "analysis.json"
    analyze.main(["--trials", paths["trials"], "--run-meta",
                  os.path.join(base_dir, "run_meta.json"), "--out", str(out)])
    figdir = tmp_path / "figures"
    rc = figures.main(["--analysis", str(out), "--out-dir", str(figdir)])
    assert rc in (0, None)
    svgs = [f for f in os.listdir(figdir) if f.endswith(".svg")]
    assert svgs and all(os.path.isfile(figdir / (s[:-4] + ".json")) for s in svgs)


# --- 3. NEGATIV zanjir: noto'g'ri run validator'dan o'tmaydi ----------------


def _drop_first_trial_end(d):
    edit_events(d, lambda recs: _remove_first(recs, "trial_end"))


def _remove_first(recs, rt):
    for i, r in enumerate(recs):
        if r["record_type"] == rt:
            return recs[:i] + recs[i + 1:]
    raise AssertionError(rt)


def _empty_guard(d):
    open(os.path.join(d, "guard.jsonl"), "w").close()


def _dead_unit(d):
    def f(m):
        m["units_show"][S.SUT].update(alive_after=False, dump_valid=False,
                                      load_state="not-found")
        m["units_show"][S.SUT]["properties"]["LoadState"] = "not-found"
    edit_run_meta(d, f)


def _swap_arm(d):
    def f(recs):
        for r in recs:
            if r["record_type"] == "trial_begin":
                r["arm"] = "no_action" if r["arm"] == "A" else "A"
                return
    edit_events(d, f)


def _guest_restart(d):
    def f(recs):
        last = [r for r in recs if r["record_type"] == "env_snapshot"][-2:]
        for r in last:
            r["guest_generation"] = S.gen(3.0, ticks=S.GUEST_START_TICKS + 99)
    edit_events(d, f)


def _guard_other_boot(d):
    def f(recs):
        for r in recs:
            r["boot_id"] = "synthetic-boot-OTHER"
            r["session_id"] = "adhoc"
    edit_events(d, f, "guard.jsonl")


def _rename_progress_column(d):
    edit_probe_csv(d, lambda lines: [
        lines[0].replace("progress_counter", "progress_cnt")] + lines[1:])


def _cut_probes(d):
    """`A` arm'dagi (raw `complete`) birinchi trial'ning 6 qatorini o'chiradi:
    >2xP uzilish (`complete` trial uchun XATO) va seq bo'shlig'i."""
    arm_a = next(r["trial_id"] for r in read_jsonl(os.path.join(d, "events.jsonl"))
                 if r["record_type"] == "trial_begin" and r["arm"] == "A")

    def f(lines):
        idx = [i for i, ln in enumerate(lines) if ln.endswith("," + arm_a)]
        lo = idx[0] + 20
        return lines[:lo] + lines[lo + 6:]
    edit_probe_csv(d, f)


def _hold_too_long(d):
    def f(recs):
        for r in recs:
            if r["record_type"] == "trial_begin":
                r["planned_timeline"]["hold_s"] = 50.0
                return
    edit_events(d, f)


def _dirty_confirmatory(d):
    def f(m):
        m["git_dirty"] = True
        m["run_mode"] = "confirmatory"
    edit_run_meta(d, f)


def _drop_schedule_digest(d):
    edit_run_meta(d, lambda m: m.update(schedule_digest="0" * 64))


def _remove_run_meta_json(d):
    os.remove(os.path.join(d, "run_meta.json"))


def _remove_probe_csv(d):
    os.remove(os.path.join(d, "probe.csv"))


def _drop_baseline(d):
    edit_events(d, lambda recs: _remove_first(recs, "baseline_window"))


def _garbage_events(d):
    with open(os.path.join(d, "events.jsonl"), "wb") as fh:
        fh.write(b"\xff\xfe\x00\x80 not utf-8 \xc3\x28\n")


NEGATIVE = [
    ("trial_end_yoq", _drop_first_trial_end, "trial_begin_without_end"),
    ("trial_end_yoq_disposition", _drop_first_trial_end, "disposition_missing"),
    ("guard_yoq", _empty_guard, "guard_start_missing"),
    ("o'chgan_unit_dumpi", _dead_unit, "units_show_dead"),
    ("arm_jadvaldan_farq", _swap_arm, "trial_schedule_mismatch"),
    ("guest_restart", _guest_restart, "guest_restarted"),
    ("guard_boshqa_boot", _guard_other_boot, "boot_id_run_meta_mismatch"),
    ("progress_ustuni_yoq", _rename_progress_column, "probe_progress_unreadable"),
    ("probe_uzilishi", _cut_probes, "probe_gap"),
    ("probe_seq_boshligi", _cut_probes, "seq_gap"),
    ("hold_cap_buzildi", _hold_too_long, "planned_timeline_invalid"),
    ("dirty_confirmatory", _dirty_confirmatory, "git_dirty"),
    ("digest_buzildi", _drop_schedule_digest, "schedule_digest_mismatch"),
    ("run_meta_json_yoq", _remove_run_meta_json, "run_dir_file_missing"),
    ("probe_csv_yoq", _remove_probe_csv, "run_dir_file_missing"),
    ("baseline_yoq", _drop_baseline, "trial_event_missing"),
    ("utf8_emas", _garbage_events, "run_dir_unreadable"),
]


@pytest.mark.parametrize("mutate,code", [(m, c) for _n, m, c in NEGATIVE],
                         ids=[n for n, _m, _c in NEGATIVE])
def test_negativ_zanjir_buzilgan_run_validatsiyadan_otmaydi(run_dir, mutate, code):
    """DARVOZA ishlaydi: har buzilgan run `ok=False` va kutilgan xato bilan."""
    mutate(run_dir)
    rep = V.validate_run_dir(run_dir)
    assert rep.ok is False
    assert code in error_codes(rep), [str(f) for f in rep.findings][:8]


def test_negativ_zanjir_cli_nolga_teng_bolmagan_kod(run_dir, capsys):
    _empty_guard(run_dir)
    assert V.main(["--run-dir", run_dir]) == 1
    assert "O'TMADI" in capsys.readouterr().out


def test_negativ_zanjir_dirty_pilot_ogohlantirish_otadi(run_dir):
    """Pilot uchun dirty daraxt faqat OGOHLANTIRISH (§14.6-8)."""
    edit_run_meta(run_dir, lambda m: m.update(git_dirty=True))
    rep = V.validate_run_dir(run_dir)
    assert rep.ok is True
    assert [f.code for f in rep.warnings] == ["git_dirty"]


@pytest.mark.parametrize("mutate", [_dead_unit, _empty_guard, _rename_progress_column],
                         ids=["o'chgan_unit", "guard_yoq", "progress_ustuni"])
def test_reducer_bu_nuqsonlarni_kormaydi_faqat_validator_toxtatadi(run_dir, mutate):
    """Nega darvoza kerak: reduce.py units_show/guard_start/envelope'ni
    O'QIMAYDI -- buzilgan run uni jimgina o'tib, chiqish ishlab chiqaradi.
    (Faqat `progress_ustuni` VR ni None qiladi; qolgan ikkisida reducer
    chiqishi to'liq va sog'lom ko'rinadi.)"""
    mutate(run_dir)
    run, _ = V.load_run_dir(run_dir)
    if mutate is _rename_progress_column:
        for p in run.probes:                 # adapter qo'llanmagan holat
            p.pop("progress", None)
    out = R.reduce_run(run)                  # istisno YO'Q
    assert out.summary["n_trials_in"] == out.summary["n_trials_out"] == 12
    assert V.validate_run(run).ok is False   # lekin validator to'xtatadi


def test_fail_closed_bosh_katalog_otmaydi(tmp_path):
    d = tmp_path / "bosh"
    d.mkdir()
    rep = V.validate_run_dir(str(d))
    assert rep.ok is False
    assert "run_dir_file_missing" in error_codes(rep)
    assert "validator_internal_error" not in error_codes(rep)
