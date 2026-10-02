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


def _analyze_args(base_dir, paths, out, *, events=True):
    """`revix analyze` argv: --events (prober_stop narxi, §8.2) va --episodes
    (FR-A per-action/per-episode, §5) bilan."""
    args = ["--trials", paths["trials"], "--run-meta",
            os.path.join(base_dir, "run_meta.json"), "--out", str(out),
            "--episodes", paths["episodes"], "--sweep", paths["sweep"]]
    if events:
        args += ["--events", os.path.join(base_dir, "events.jsonl")]
    return args


def test_prober_stop_har_trial_uchun_narx_bilan_va_arm_ga_ulanadi(base_dir, tmp_path):
    """§8.2 per-trial narxning TRANSPORTI (analyze `--events` shu yo'ldan
    o'qiydi): `prober_stop` har trial uchun alohida emitter'dan, envelope'da
    `trial_id`, `cost.core_percent` bilan; arm `trials.jsonl` orqali ulanadi.
    reduce.py `prober_stop` ni O'QIMAYDI -- bu yagona yo'l."""
    paths = _reduced(base_dir, tmp_path)
    arm = {t["trial_id"]: t["arm"] for t in read_jsonl(paths["trials"])}
    stops = [r for r in read_jsonl(os.path.join(base_dir, "events.jsonl"))
             if r["record_type"] == "prober_stop"]
    assert len(stops) == len(arm) == 12
    assert {r["trial_id"] for r in stops} == set(arm)
    assert len({r["emitter"] for r in stops}) == 12      # har trial'ga o'z prober'i
    by_arm = {}
    for r in stops:
        assert r["cost"]["synthetic"] is True
        by_arm.setdefault(arm[r["trial_id"]], []).append(r["cost"]["core_percent"])
    assert set(by_arm) == {"A", "no_action"}
    assert all(len(v) == 6 and v == [S.SYNTHETIC_CORE_PERCENT] * 6
               for v in by_arm.values())
    starts = [r for r in read_jsonl(os.path.join(base_dir, "events.jsonl"))
              if r["record_type"] == "prober_start"]
    assert {r["trial_id"] for r in starts} == set(arm)   # §14.2: CSV <-> run
    assert V.validate_run_dir(base_dir).findings == []   # per-trial seq/emitter OK


def test_zanjir_analiz(base_dir, tmp_path):
    """reduce chiqishi -> `revix.analyze` -> analysis.json.

    `revix/analyze.py` yo'q bo'lsa test SKIP (bu qism ishga tushmagan --
    o'tgan deb hisoblanmaydi). `--events` va `--episodes` bilan: probe_cost
    bo'limi o'lchangan `prober_stop` narxidan to'ldiriladi.
    """
    analyze = pytest.importorskip("revix.analyze")
    paths = _reduced(base_dir, tmp_path)
    out = tmp_path / "analysis.json"
    rc = analyze.main(_analyze_args(base_dir, paths, out))
    assert rc in (0, None)
    a = json.load(open(out, encoding="utf-8"))
    assert a["schema_version"] == 1
    assert a["preregistration_sha256"] == S.SYNTHETIC_SHA
    assert a["n_trials"]["total"] == 12
    pc = a["probe_cost"]
    assert pc["budget_percent"] == S.PROBE_COST_BUDGET_PERCENT
    assert set(pc["by_arm"]) == {"A", "no_action"}
    for arm in pc["by_arm"].values():
        assert arm["core_percent"] == [S.SYNTHETIC_CORE_PERCENT] * 6


def _figdir(out_dir):
    """§3: figuralar `<out-dir>/figures/<nom>.svg` (+ yonida `<nom>.json`)."""
    return os.path.join(str(out_dir), "figures")


def _sidecar(out_dir, name):
    with open(os.path.join(_figdir(out_dir), name + ".json"),
              encoding="utf-8") as fh:
        return json.load(fh)


def test_zanjir_figura(base_dir, tmp_path):
    """analysis.json -> `revix.figures` (matplotlib kerak).

    §3 majburiy `probe_cost` figurasi: o'lchangan narx bilan CHIZILADI
    (placeholder EMAS). Assertion yumshatilmagan.
    """
    analyze = pytest.importorskip("revix.analyze")
    figures = pytest.importorskip("revix.figures")
    paths = _reduced(base_dir, tmp_path)
    out = tmp_path / "analysis.json"
    assert analyze.main(_analyze_args(base_dir, paths, out)) in (0, None)
    figdir = tmp_path / "figures"
    rc = figures.main(["--analysis", str(out), "--out-dir", str(figdir)])
    assert rc in (0, None)
    fd = _figdir(figdir)
    svgs = [f for f in os.listdir(fd) if f.endswith(".svg")]
    assert svgs and all(os.path.isfile(os.path.join(fd, s[:-4] + ".json"))
                        for s in svgs)
    sc = _sidecar(figdir, "probe_cost")
    assert sc["status"] != "placeholder", sc["placeholder_reason"]
    assert {a["arm"] for a in sc["data"]["arms"]} == {"A", "no_action"}
    assert all(a["n_unmeasured"] == 0 for a in sc["data"]["arms"])


def test_zanjir_figura_narxsiz_prober_stop_korinadigan_placeholder(tmp_path):
    """Manfiy tomon: `prober_stop` da `cost` YO'Q -> probe_cost figurasi
    ANIQ yorliqli placeholder bo'ladi va narx TO'QILMAYDI (jimgina nol yoki
    budjet qiymati emas)."""
    analyze = pytest.importorskip("revix.analyze")
    figures = pytest.importorskip("revix.figures")
    d = str(tmp_path / "nocost")
    S.write_run(d, with_cost=False)
    paths = _reduced(d, tmp_path)
    out = tmp_path / "analysis.json"
    analyze.main(_analyze_args(d, paths, out))
    a = json.load(open(out, encoding="utf-8"))
    vals = [v for arm in (a.get("probe_cost") or {}).get("by_arm", {}).values()
            for v in arm["core_percent"]]
    assert all(v is None for v in vals)                  # to'qilgan raqam yo'q
    figdir = tmp_path / "figures"
    figures.main(["--analysis", str(out), "--out-dir", str(figdir)])
    sc = _sidecar(figdir, "probe_cost")
    assert sc["status"] == "placeholder"
    assert sc["placeholder_reason"]
    assert sc["data"] is None
    assert os.path.isfile(os.path.join(_figdir(figdir), "probe_cost.svg"))     # yorliqli placeholder chizilgan


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


# --- 4. xom oqimda bystander: reducerga BITTA unit/target beriladi ---------


def _add_bystander(d):
    """Xom oqimga bystander unit_state va probe qatorlari qo'shadi."""
    def f(recs):
        seqs = [r["seq"] for r in recs if r["emitter"] == "driver:1"
                and r["record_type"] == "unit_state"]
        n = max(seqs)
        extra = []
        for r in [r for r in recs if r["record_type"] == "unit_state"]:
            n += 1
            q = dict(r, unit=S.BYSTANDER, seq=n, n_restarts=7, NRestarts=7)
            extra.append(q)
        return recs + extra
    edit_events(d, f)

    def g(lines):
        head, rows = lines[0], lines[1:]
        cols = head.split(",")
        ti, si, qi = cols.index("target"), cols.index("trial_id"), cols.index("seq")
        extra = []
        for ln in rows[:3]:
            c = ln.split(",")
            c[ti] = "bystander"
            extra.append(",".join(c))
        return lines + extra
    edit_probe_csv(d, g)


def test_xom_oqimda_bystander_filtrsiz_rad_etiladi(run_dir):
    _add_bystander(run_dir)
    rep = V.validate_run_dir(run_dir)
    assert {"unit_state_units_mixed", "probe_targets_mixed"} <= error_codes(rep)


def test_xom_oqimda_bystander_sut_filtri_bilan_otadi(run_dir):
    _add_bystander(run_dir)
    rep = V.validate_run_dir(run_dir, sut_unit=S.SUT, sut_target="sut")
    assert rep.findings == [], [str(f) for f in rep.findings]
    assert V.main(["--run-dir", run_dir, "--sut-unit", S.SUT,
                   "--sut-target", "sut"]) == 0


def test_xom_oqimda_bystander_reducer_ko_rinishi_sut_ga_filtrlanadi(run_dir, tmp_path):
    """Nega `--sut-unit`/`--sut-target` kerak: filtrlanmagan reduksiya bystander
    NRestarts'ini SUT'nikiga aralashtiradi; filtrlangan ko'rinish toza run
    bilan AYNAN bir xil `trial_metrics` beradi."""
    clean_run, _ = V.load_run_dir(run_dir)
    want = {t["__trial_id__"]: (t["n_restarts_delta"], t["n_invocations"], t["vr"])
            for t in R.reduce_run(clean_run).trials}
    _add_bystander(run_dir)
    run, _ = V.load_run_dir(run_dir)
    raw = {t["__trial_id__"]: (t["n_restarts_delta"], t["n_invocations"], t["vr"])
           for t in R.reduce_run(run).trials}
    assert raw != want                                   # aralashgan: buzilgan
    view = V.reducer_view(run, S.SUT, "sut")
    got = {t["__trial_id__"]: (t["n_restarts_delta"], t["n_invocations"], t["vr"])
           for t in R.reduce_run(view).trials}
    assert got == want
    assert V.validate_run(run, sut_unit=S.SUT, sut_target="sut").ok
    assert not V.validate_run(run).ok                    # bayroqsiz: rad


# --- 5. §17: verifikatsiya oynasi pressure hold ICHIDA (v1.6/v1.7) ---------

ENTERING_PAIRS = {("complete", "trial_end"), ("complete", "derived"),
                  ("censored", "down_at_horizon")}


def _early_pressure_off(d):
    """Birinchi `A` (raw `complete`) trial'ning T_h sini t_up + W_stab dan
    OLDINGA suradi: oyna hold'dan chiqadi (§17.3(a))."""
    def f(recs):
        for r in recs:
            if (r["record_type"] == "trial_end"
                    and r["disposition"] == "complete"):
                b = next(x for x in recs if x["record_type"] == "trial_begin"
                         and x["trial_id"] == r["trial_id"])
                r["timing"]["pressure_off_mono_us"] = b["mono_us"] + 6_000_000
                return
    edit_events(d, f)


def test_zanjir_toza_run_reducer_faqat_uchta_juft_maxrajga_kiradi(base_dir):
    """Allow-list: faqat uchta (disposition, source) juft binar maxrajga
    kiradi; boshqa har juft chiqariladi va NOMLANADI (`unknown_source` yo'q)."""
    run, _ = V.load_run_dir(base_dir)
    out = R.reduce_run(run)
    entered = {(t["disposition"], t["disposition_source"])
               for t in out.trials if t["included_in_primary"]}
    assert entered and entered <= ENTERING_PAIRS
    for t in out.trials:
        assert "unknown_source" not in str(t["exclusion_reason"])
    assert out.summary["n_window_containment_not_evaluated"] == 0
    assert out.summary["window_containment_counts"]["inside_hold"] == 6
    assert out.summary["window_containment_counts"]["past_pressure"] == 0


def test_zanjir_oyna_holddan_chiqqan_complete_validatordan_otmaydi(run_dir):
    """Reducer trial'ni `censored:window_past_pressure` qilib CHIQARADI (u
    tashlamaydi), lekin xom `trial_end` `complete` deb qolgan -- bu §17.4-5
    bo'yicha validator XATOSI: o'lchanmagan narsa o'lchov deb yozilgan."""
    _early_pressure_off(run_dir)
    run, _ = V.load_run_dir(run_dir)
    rep = V.validate_run(run)
    assert rep.ok is False
    assert "window_outside_hold_complete" in error_codes(rep)
    out = R.reduce_run(run)                          # reducer tushunadi
    hit = [t for t in out.trials
           if t["disposition_source"] == "window_past_pressure"]
    assert len(hit) == 1 and hit[0]["disposition"] == "censored"
    assert hit[0]["included_in_primary"] is False
    assert "window_past_pressure" in hit[0]["exclusion_reason"]
    assert out.summary["n_trials_out"] == 12         # trial tashlanmadi
    assert V.main(["--run-dir", run_dir]) == 1


def test_zanjir_Th_olchanmagan_run_ogohlantirish_bilan_otadi(run_dir):
    """`pressure_off_mono_us = 0` ("hech qachon o'rnatilmagan"): hukm
    to'qilmaydi, validator xato bermaydi, lekin soni ko'rinadi va reducer
    summary'si bilan mos."""
    def f(recs):
        for r in recs:
            if r["record_type"] == "trial_end":
                r["timing"]["pressure_off_mono_us"] = 0
    edit_events(run_dir, f)
    rep = V.validate_run_dir(run_dir)
    assert rep.ok is True, [str(x) for x in rep.errors]
    w = next(x for x in rep.warnings
             if x.code == "window_containment_not_evaluated")
    run, _ = V.load_run_dir(run_dir)
    out = R.reduce_run(run)
    # validator faqat raw `complete` trial'larni sanaydi (6 ta A trial);
    # reducer summary'si `no_t_up` bo'lmaganlarini: kamida shular.
    assert w.detail["n"] == 6
    assert out.summary["n_window_containment_not_evaluated"] >= 6


# --- 6. §20 (v1.8): maxraj va survival a'zoligi disposition'dan KELIB CHIQMAYDI ---


def test_zanjir_a_zolik_predikatlardan_hosil_boladi_dispositiondan_emas(base_dir):
    """Validator reason matnlariga tayanmaydi; bu test iste'molchi tomonidan
    §20 ni hujjatlaydi: binar maxrajga kirgan trial'da `vr` aniqlangan,
    survival a'zoligi `enters_survival_set(disposition, vr_reason)` bilan mos,
    chiqarilgan trial'da nomlangan sabab bor (va `unknown_source` emas)."""
    run, _ = V.load_run_dir(base_dir)
    for t in R.reduce_run(run).trials:
        if t["included_in_primary"]:
            assert t["vr"] is not None
            assert t["exclusion_reason"] is None
        else:
            assert t["exclusion_reason"]
            assert "unknown_source" not in t["exclusion_reason"]
        assert t["included_in_survival"] is R.enters_survival_set(
            t["disposition"], t["vr_reason"])
        if not t["included_in_survival"]:
            assert t["survival_exclusion_reason"]
        # `censored` bo'lish survival a'zoligini o'z-o'zidan belgilamaydi:
        # shuning uchun `("complete","censored")` ga tenglik QILINMAYDI.
