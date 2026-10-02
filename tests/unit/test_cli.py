"""cli.py testlari -- `doctor`, `status`, `health`, `events`, `version`,
`run`, `analyze`, `figures`.

Bu testlar MUHITNI SOXTALASHTIRMAYDI: `doctor` shu mashinada haqiqatan ishga
tushiriladi va natijasi mustaqil o'qilgan ground truth bilan taqqoslanadi.
Sabab: doctor'ning butun qiymati u HAQIQIY muhitni aytishida. Soxta muhitga
qarshi o'tgan test hech narsa isbotlamaydi.

Yagona soxtalashtirish -- chiqish kodi testi: FAIL holatini majburlash uchun
`cli.CHECKS` registriga soxta TEKSHIRUV NATIJASI qo'yiladi (muhit emas).

Yon ta'sir: `doctor` bitta throwaway cgroup yaratadi va o'chiradi. Test uning
tozalanganini alohida tekshiradi.

`run` / `analyze` / `figures` testlari ISTISNO: bu uch subkomanda faqat argv
yasab `revix.driver` / `revix.analyze` / `revix.figures` ning `main(argv)` ini
chaqiradi, o'sha modullar esa boshqa agent'larda yoziladi va bu worktree'da
BO'LMASLIGI mumkin. Shuning uchun test ularga TAYANMAYDI: `sys.modules` ga soxta
modul qo'yiladi va handler yasagan argv ro'yxati tekshiriladi. Bu delegatsiya
shartnomasini sinaydi (modulning ichki mantig'ini emas) -- modul keyin paydo
bo'lsa ham testlar o'zgarishsiz o'tadi. `check_python_modules` mantig'i ham
`_module_version` ni almashtirib sinaladi (muhitga bog'liq bo'lmasligi uchun);
haqiqiy muhitga qarshi tekshiruv alohida.
"""
from __future__ import annotations

import contextlib
import importlib
import io
import json
import os
import subprocess
import sys

import pytest

from revix import cgroup as cg
from revix import cli


# --- umumiy fixture'lar -----------------------------------------------------
#
# `status` va `health` PSI tezligi uchun >= 2 s uxlaydi (PSI kadensi 2 s --
# qisqaroq oyna oniy tezlik emas). Shuning uchun har biri MODUL bo'yicha
# BIR MARTA, va aynan CLI orqali ishlatiladi -- shunda bitta ishga tushirish
# ham "well-formed JSON", ham shakl testlariga xizmat qiladi.


def _cli_capture(argv: list[str]) -> tuple[int, str]:
    """`cli.main` ni chaqiradi va stdout'ni qaytaradi (fixture'da ham ishlaydi)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli.main(argv)
    return rc, buf.getvalue()


def _cli_json(argv: list[str]) -> tuple[int, dict]:
    rc, out = _cli_capture(argv)
    return rc, json.loads(out)


@pytest.fixture(scope="module")
def doctor_run() -> tuple[int, dict]:
    """`doctor --json` bir marta: u subprocess chaqiradi va cgroup yaratadi."""
    return _cli_json(["doctor", "--json"])


@pytest.fixture()
def doctor_json(doctor_run) -> dict:
    return doctor_run[1]


@pytest.fixture(scope="module")
def status_run() -> tuple[int, dict]:
    return _cli_json(["status", "--json"])


@pytest.fixture(scope="module")
def health_run() -> tuple[int, dict]:
    return _cli_json(["health", "--json"])


@pytest.fixture()
def status_json(status_run) -> dict:
    return status_run[1]


@pytest.fixture()
def health_json(health_run) -> dict:
    return health_run[1]


def _run_cli(argv: list[str], capsys) -> tuple[int, str]:
    rc = cli.main(argv)
    return rc, capsys.readouterr().out


# ===========================================================================
# doctor -- JSON shakli
# ===========================================================================


def test_doctor_json_shu_mashinada_ishlaydi_va_toliq(doctor_run):
    """`doctor --json` shu mashinada ishlaydi va well-formed JSON beradi."""
    rc, rep = doctor_run
    assert rc in (0, 1)
    assert rep["tool"] == "revix doctor"
    assert rep["report_schema_version"] == cli.REPORT_SCHEMA_VERSION
    for key in ("summary", "checks", "host", "revix_version", "mono_us", "real_us"):
        assert key in rep, f"hisobotda {key} yo'q"
    keys = [c["key"] for c in rep["checks"]]
    assert len(keys) == len(set(keys)), f"kalitlar takrorlandi: {keys}"
    assert set(keys) == set(cli.EXPECTED_CHECK_KEYS), (
        f"kutilgan kalitlar to'plami mos kelmadi; "
        f"yetmaydi={set(cli.EXPECTED_CHECK_KEYS) - set(keys)}, "
        f"ortiqcha={set(keys) - set(cli.EXPECTED_CHECK_KEYS)}"
    )


def test_doctor_json_global_flag_ham_ishlaydi(capsys):
    """`revix --json doctor` shakli ham qo'llanishi kerak."""
    rc, out = _run_cli(["--json", "doctor"], capsys)
    assert rc in (0, 1)
    assert json.loads(out)["tool"] == "revix doctor"


def test_har_tekshiruv_holat_va_uchta_maydonni_beradi(doctor_json):
    """Har tekshiruv: PASS/WARN/FAIL + observed + required + consequence."""
    for c in doctor_json["checks"]:
        assert c["status"] in ("PASS", "WARN", "FAIL"), c
        for field in ("observed", "required", "consequence"):
            assert field in c, f"{c['key']}: {field} yo'q"
            assert isinstance(c[field], str), f"{c['key']}: {field} satr emas"
            assert c[field].strip(), f"{c['key']}: {field} bo'sh"
        assert isinstance(c["detail"], dict)


def test_summary_tekshiruvlar_bilan_mos(doctor_json):
    s = doctor_json["summary"]
    checks = doctor_json["checks"]
    assert s["total"] == len(checks)
    assert s["pass"] == sum(1 for c in checks if c["status"] == "PASS")
    assert s["warn"] == sum(1 for c in checks if c["status"] == "WARN")
    assert s["fail"] == sum(1 for c in checks if c["status"] == "FAIL")
    assert s["ok"] is (s["fail"] == 0)


def test_doctor_inson_chiqishi_har_tekshiruvni_korsatadi(capsys):
    rc, out = _run_cli(["doctor"], capsys)
    assert rc in (0, 1)
    for key in cli.EXPECTED_CHECK_KEYS:
        assert key in out, f"inson chiqishida {key} yo'q"
    assert "XULOSA" in out
    assert "kerak:" in out


# ===========================================================================
# oomd -- eng muhim tekshiruv
# ===========================================================================


def _oomd_ground_truth() -> dict[str, str]:
    """oomd holatini cli'dan MUSTAQIL o'qiydi (to'g'ridan-to'g'ri systemctl)."""
    uid = os.getuid()
    p = subprocess.run(
        ["systemctl", "show", f"user@{uid}.service",
         "-p", "ManagedOOMMemoryPressure",
         "-p", "ManagedOOMMemoryPressureLimit"],
        capture_output=True, text=True, check=False, timeout=10,
    )
    out: dict[str, str] = {}
    for line in p.stdout.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            out[k.strip()] = v.strip()
    a = subprocess.run(["systemctl", "is-active", "systemd-oomd.service"],
                       capture_output=True, text=True, check=False, timeout=10)
    out["is_active"] = a.stdout.strip()
    return out


def test_oomd_mustaqil_oqilgan_haqiqatga_mos(doctor_json):
    """oomd tekshiruvi systemctl'dan mustaqil o'qilgan qiymatlarni aks ettiradi."""
    truth = _oomd_ground_truth()
    check = next(c for c in doctor_json["checks"] if c["key"] == "oomd")
    d = check["detail"]
    assert d["managed_oom_memory_pressure"] == truth.get("ManagedOOMMemoryPressure")
    assert d["pressure_limit_raw"] == truth.get("ManagedOOMMemoryPressureLimit")
    assert d["oomd_active"] is (truth["is_active"] == "active")
    assert d["kill_authority"] is (
        truth["is_active"] == "active"
        and truth.get("ManagedOOMMemoryPressure") == "kill"
    )


def _oomd_detail(doctor_json) -> dict:
    return next(c for c in doctor_json["checks"] if c["key"] == "oomd")["detail"]


def test_oomd_kill_authority_bor_bolsa_hujjatlangan_konfiguratsiya_boladi(doctor_json):
    """oomd kill authority BOR bo'lsa, hujjatlangan konfiguratsiya aniqlanadi.

    Bu MUHIT REGRESSIYA qulfining 1-yarmi: `docs/architecture/01-muhit-tekshiruvlari.md`
    §7 doctor uchun spetsifikatsiya. Agar bu test yiqilsa, mashina o'zgargan
    va guard kalibratsiyasi qayta ko'rilishi kerak -- jimgina o'tib ketmasligi
    KERAK.
        ManagedOOMMemoryPressure=kill
        ManagedOOMMemoryPressureLimit=50%
        DefaultMemoryPressureDurationSec=20s

    Kill authority YO'Q mashinada (masalan systemd-oomd o'rnatilmagan) bu yerda
    tekshiriladigan narsa yo'q -- test SKIP bo'ladi. Lekin jimgina emas: qulfning
    2-yarmi (`test_oomd_yoqligi_MUHIT_HUJJATIDA_qayd_etilgan`) aynan shu holatda
    ishlaydi va muhit yozuvi bo'lmasa YIQILADI.
    """
    d = _oomd_detail(doctor_json)
    if d["kill_authority"] is not True:
        pytest.skip(
            "bu mashinada oomd kill authority yo'q (etalon mashinadan farq): "
            f"managed_oom_memory_pressure={d.get('managed_oom_memory_pressure')!r}, "
            f"oomd_active={d.get('oomd_active')!r}; qulfning 2-yarmi "
            "(test_oomd_yoqligi_MUHIT_HUJJATIDA_qayd_etilgan) tekshiradi"
        )
    assert d["managed_oom_memory_pressure"] == "kill"
    assert d["pressure_limit_percent"] == pytest.approx(50.0, abs=0.01)
    assert d["duration_effective_s"] == pytest.approx(20.0, abs=0.01)
    assert d["duration_source"] == "oomd.conf"
    assert d["risk"] == "high-mitigated"
    assert d["mitigation"] == cli.OOMD_MITIGATION


# `agent/envcheck` yozadigan muhit yozuvi (WSL mashinasi).
WSL_MUHIT_HUJJATI = os.path.join(
    cli.REPO_ROOT, "docs", "architecture", "07-wsl-muhit-tekshiruvlari.md")


def test_oomd_yoqligi_MUHIT_HUJJATIDA_qayd_etilgan(doctor_json):
    """oomd kill authority YO'Q bo'lsa, bu muhit yozuvida qayd etilgan bo'lishi SHART.

    MUHIT REGRESSIYA qulfining 2-yarmi. Asl sabab o'zgarmagan: mashina
    o'zgargan bo'lsa, guard kalibratsiyasi (02-guard-kalibratsiyasi) qayta
    ko'rilishi kerak -- jimgina o'tib ketmasligi KERAK. Shuning uchun oomd'siz
    mashinada test faqat "yo'q" deb o'tmaydi: u yo'qligi
    `docs/architecture/07-wsl-muhit-tekshiruvlari.md` da YOZIB QO'YILGANINI talab
    qiladi (`systemd-oomd` eslatilishi yetarli). Yozilmagan bo'lsa -- YIQILADI.
    """
    d = _oomd_detail(doctor_json)
    if d["kill_authority"] is True:
        pytest.skip("oomd kill authority bor: qulfning 1-yarmi ishlaydi "
                    "(test_oomd_kill_authority_bor_bolsa_hujjatlangan_konfiguratsiya_boladi)")
    rel = os.path.relpath(WSL_MUHIT_HUJJATI, cli.REPO_ROOT)
    tomonlama = (
        "oomd kill authority YO'Q (mashina etalon mashinadan farq qiladi: "
        f"oomd_active={d.get('oomd_active')!r}, "
        f"managed_oom_memory_pressure={d.get('managed_oom_memory_pressure')!r}) "
        "va bu muhit yozuvida qayd etilmagan. Guard kalibratsiyasi "
        "(02-guard-kalibratsiyasi) QAYTA o'tkazilishi kerak, bosim "
        "eksperimentidan OLDIN. "
    )
    assert os.path.isfile(WSL_MUHIT_HUJJATI), (
        tomonlama + f"Muhit yozuvi fayli yo'q: {rel}")
    with open(WSL_MUHIT_HUJJATI, encoding="utf-8", errors="replace") as fh:
        matn = fh.read()
    assert "systemd-oomd" in matn, (
        tomonlama + f"{rel} mavjud, lekin `systemd-oomd` yo'qligi unda qayd etilmagan")


def test_oomd_kill_authority_WARN_sifatida_baland_korinadi(doctor_json):
    """kill authority + zaxira bor -> WARN (FAIL emas: yumshatish haqiqiy)."""
    check = next(c for c in doctor_json["checks"] if c["key"] == "oomd")
    d = check["detail"]
    if not d["kill_authority"]:
        assert check["status"] == "PASS"
        return
    dur = d["duration_effective_s"]
    if dur is None or dur <= cli.GUARD_SUSTAIN_MAX_S:
        assert check["status"] == "FAIL"
    else:
        assert check["status"] == "WARN"
    # Xavf jadvaldagi bir qatorga yashirilmaydi -- baland banner chiqadi.
    obj = cli.Check(**check)
    banner = cli.oomd_banner(obj, 100)
    assert banner, "kill authority bor, lekin banner chiqmadi"
    joined = "\n".join(banner)
    assert "OGOHLIK" in joined
    assert "guard" in joined
    assert "12 s" in joined


def test_oomd_limit_uint32_shkalasida_ochiriladi():
    """`ManagedOOMMemoryPressureLimit` UINT32 shkalasida beriladi."""
    assert cli.parse_oom_pressure_limit("2147483648") == pytest.approx(50.0, abs=0.001)
    assert cli.parse_oom_pressure_limit("4294967295") == pytest.approx(100.0, abs=0.001)
    assert cli.parse_oom_pressure_limit("0") == 0.0
    assert cli.parse_oom_pressure_limit("60.00%") == 60.0
    assert cli.parse_oom_pressure_limit("[not set]") is None
    assert cli.parse_oom_pressure_limit(None) is None
    assert cli.parse_oom_pressure_limit("abc") is None


def test_davomiylik_parsi():
    assert cli.parse_duration_sec("20s") == 20.0
    assert cli.parse_duration_sec("500ms") == pytest.approx(0.5)
    assert cli.parse_duration_sec("1min 30s") == pytest.approx(90.0)
    assert cli.parse_duration_sec("30") == 30.0
    assert cli.parse_duration_sec("infinity") is None
    assert cli.parse_duration_sec("[not set]") is None
    assert cli.parse_duration_sec(None) is None


# ===========================================================================
# chiqish kodi -- SOXTA TEKSHIRUV NATIJASI bilan (muhit soxtalashtirilmaydi)
# ===========================================================================


def _fake(key: str, status: str) -> cli.Check:
    return cli.Check(
        key=key, title="soxta", status=status,
        observed="soxta kuzatuv", required="soxta talab",
        consequence="soxta natija",
    )


def test_exit_code_fail_bolsa_non_zero():
    rep = cli.build_report([_fake("x", cli.PASS), _fake("y", cli.FAIL)])
    assert rep["summary"]["ok"] is False
    assert cli.exit_code_for(rep) != 0


def test_exit_code_fail_bolmasa_nol():
    rep = cli.build_report([_fake("x", cli.PASS), _fake("y", cli.WARN)])
    assert rep["summary"]["ok"] is True
    assert cli.exit_code_for(rep) == 0


def test_cli_doctor_soxta_FAIL_da_non_zero(monkeypatch, capsys):
    """CLI darajasida: registrga soxta FAIL qo'yilsa rc != 0."""
    monkeypatch.setattr(cli, "CHECKS", (lambda: _fake("injected", cli.FAIL),))
    rc, out = _run_cli(["doctor", "--json"], capsys)
    rep = json.loads(out)
    assert rc == 1
    assert rep["summary"]["fail"] == 1
    assert rep["checks"][0]["key"] == "injected"


def test_cli_doctor_soxta_WARN_da_nol(monkeypatch, capsys):
    monkeypatch.setattr(cli, "CHECKS", (lambda: _fake("injected", cli.WARN),))
    rc, _out = _run_cli(["doctor", "--json"], capsys)
    assert rc == 0


def test_tekshiruv_istisnosi_FAIL_ga_aylanadi(monkeypatch):
    """FAIL-CLOSED: tekshiruvdagi bug jimgina PASS bo'lmaydi."""

    def broken() -> cli.Check:
        raise RuntimeError("buzildi")

    broken.__name__ = "check_broken"
    checks = cli.collect_checks((broken,))
    assert len(checks) == 1
    assert checks[0].status == cli.FAIL
    assert "buzildi" in checks[0].observed
    assert checks[0].consequence.strip()


def test_notogri_holat_qabul_qilinmaydi():
    with pytest.raises(ValueError):
        cli.Check("k", "t", "OK", "o", "r", "c")


# ===========================================================================
# cgroup yozish tekshiruvi -- throwaway cgroup tozalanishi SHART
# ===========================================================================


def test_cgroup_write_tekshiruvi_ozidan_keyin_tozalaydi(doctor_json):
    check = next(c for c in doctor_json["checks"] if c["key"] == "cgroup_write")
    d = check["detail"]
    if not d.get("created"):
        # Yaratilmagan bo'lsa FAIL bo'lishi kerak -- jimgina o'tmasligi shart.
        assert check["status"] == "FAIL"
        return
    assert d["cleaned_up"] is True, f"probe cgroup qoldi: {d.get('probe_cgroup')}"
    assert not os.path.isdir(d["probe_cgroup"])


def test_revixdoctor_probe_qoldiqlari_yoq(doctor_json):
    """user@UID.service da hech qanday `revixdoctor-*` cgroup qolmasligi kerak."""
    user = cg.user_service_cgroup()
    left = [n for n in os.listdir(user) if n.startswith("revixdoctor-")]
    assert left == [], f"qoldiq probe cgroup'lar: {left}"


# ===========================================================================
# status
# ===========================================================================


def test_status_json_shakli(status_json):
    rep = status_json
    assert rep["tool"] == "revix status"
    for key in ("units", "slices", "psi", "host"):
        assert key in rep
    assert set(rep["slices"]) == {cli.LAB_SLICE, cli.MON_SLICE}
    for name, st in rep["slices"].items():
        assert st["name"] == name
        assert isinstance(st["exists"], bool)


def test_status_psi_total_delta_ishlatadi_avgN_emas(status_json):
    """§7: tezlik `total=` delta'sidan, oyna >= 2 s."""
    psi = status_json["psi"]
    assert psi["method"] == "total_delta"
    assert psi["interval_s"] >= cli.MIN_RATE_WINDOW_S
    assert "avgN" in psi["why_not_avgN"]
    assert "host" in psi["scopes"]
    mem = psi["scopes"]["host"]["resources"]["memory"]
    assert mem is not None, "host memory PSI o'qilmadi"
    # Oyna >= 2 s bo'lgani uchun tezlik hisoblangan bo'lishi kerak.
    assert mem["window_us"] >= 2_000_000
    for kind in ("some", "full"):
        rate = mem[f"{kind}_rate"]
        assert rate is not None, f"{kind}_rate None (oyna {mem['window_us']} us)"
        assert 0.0 <= rate <= 1.05, rate
        # avgN ham bor, lekin u IKKILAMCHI va alohida nomda.
        assert f"{kind}_avg10" in mem


def test_status_json_cli_dan_well_formed(status_run):
    """`status --json` CLI orqali: rc=0 va well-formed JSON."""
    rc, rep = status_run
    assert rc == 0
    assert rep["tool"] == "revix status"


def test_status_inson_chiqishi(status_json):
    text = cli.render_status_human(status_json)
    assert "PSI" in text
    assert "§7" in text
    assert cli.LAB_SLICE in text
    assert cli.MON_SLICE in text


def test_psi_yol_yasash():
    assert cli.psi_file_path("/proc/pressure", "memory") == "/proc/pressure/memory"
    assert cli.psi_file_path("/x/y.slice", "io") == "/x/y.slice/io.pressure"


# ===========================================================================
# health
# ===========================================================================


def test_health_json_shakli(health_json):
    rep = health_json
    assert rep["tool"] == "revix health"
    assert rep["status"] in ("ok", "warn", "fail")
    for key in ("psi", "memory", "oomd_risk", "leftover", "problems", "warnings"):
        assert key in rep
    assert isinstance(rep["problems"], list)
    assert isinstance(rep["warnings"], list)
    assert rep["status"] == ("fail" if rep["problems"]
                            else ("warn" if rep["warnings"] else "ok"))
    o = rep["oomd_risk"]
    assert o["guard_sustain_max_s"] == cli.GUARD_SUSTAIN_MAX_S
    assert isinstance(o["kill_authority"], bool)
    m = rep["memory"]
    assert m["required_kb"] == cli.PLANNED_CEILING_KB + cli.GUARD_MEM_FLOOR_KB


def test_health_json_cli_dan_well_formed(health_run):
    """`health --json` CLI orqali: well-formed, va `fail` da rc=1."""
    rc, rep = health_run
    assert rc == (1 if rep["status"] == "fail" else 0)
    assert rep["tool"] == "revix health"


def test_health_inson_satri_siqilgan(health_json):
    text = cli.render_health_human(health_json)
    first = text.splitlines()[0]
    assert first.startswith("REVIX health:")
    assert "MemAvailable=" in first
    assert "oomd=" in first
    assert "qoldiq=" in first


# ===========================================================================
# events
# ===========================================================================


def _fixture_stream(tmp_path, truncated: bool = True):
    """Kichik JSONL oqimi; oxirgi qator ataylab QISMLI."""
    recs = [
        {"schema_version": 1, "record_type": "guard_start", "seq": 1,
         "mono_us": 1000, "emitter": "guard:1", "watch_cgroup": "/x"},
        {"schema_version": 1, "record_type": "guard_event", "seq": 2,
         "mono_us": 2000, "emitter": "guard:1", "reason": "sustained_pressure",
         "detail": {"rate": 0.42}},
        {"schema_version": 1, "record_type": "guard_event", "seq": 3,
         "mono_us": 3000, "emitter": "guard:1", "reason": "lab_swap_used",
         "detail": {"swap_current": 4096}},
        {"schema_version": 1, "record_type": "guard_stop", "seq": 4,
         "mono_us": 4000, "emitter": "guard:1", "tripped": True},
    ]
    body = "".join(json.dumps(r) + "\n" for r in recs)
    if truncated:
        # Qismli oxirgi qator: fsync DAVRIY, demak crash'da bu NORMAL.
        body += '{"schema_version":1,"record_type":"guard_ev'
    p = tmp_path / "events.jsonl"
    p.write_text(body)
    return p, recs


def test_events_oqimni_parse_qiladi(tmp_path):
    path, recs = _fixture_stream(tmp_path)
    res = cli.read_events(str(path))
    assert res["count"] == len(recs)
    assert res["matched"] == len(recs)
    assert res["types"] == {"guard_start": 1, "guard_event": 2, "guard_stop": 1}


def test_events_qismli_oxirgi_qatorga_bardosh_beradi(tmp_path, capsys):
    """JSONL append-only: yarim yozilgan oxirgi qator XATO EMAS."""
    path, recs = _fixture_stream(tmp_path, truncated=True)
    res = cli.read_events(str(path))
    assert res["truncated_tail"] is True
    assert res["bad_lines"] == []
    assert res["count"] == len(recs)
    # CLI ham yiqilmaydi va rc=0 qaytaradi.
    rc, out = _run_cli(["events", str(path)], capsys)
    assert rc == 0
    assert "qismli" in out


def test_events_ortadagi_buzuq_qator_xato(tmp_path, capsys):
    """O'rtadagi buzuq qator -- HAQIQIY ma'lumot yo'qolishi, jim o'tmaydi."""
    p = tmp_path / "bad.jsonl"
    p.write_text(
        '{"record_type":"a","seq":1}\n'
        'BU JSON EMAS\n'
        '{"record_type":"b","seq":2}\n'
    )
    res = cli.read_events(str(p))
    assert res["count"] == 2
    assert [b["line"] for b in res["bad_lines"]] == [2]
    assert res["truncated_tail"] is False
    rc, out = _run_cli(["events", str(p)], capsys)
    assert rc == 1
    assert "2-qator buzuq" in out


def test_events_type_filtri(tmp_path, capsys):
    path, _recs = _fixture_stream(tmp_path)
    res = cli.read_events(str(path), types={"guard_event"})
    assert res["matched"] == 2
    assert {r["record_type"] for r in res["records"]} == {"guard_event"}
    # `--type` bir necha marta VA vergul bilan.
    rc, out = _run_cli(["events", str(path), "--type", "guard_event", "--json"], capsys)
    assert rc == 0
    rep = json.loads(out)
    assert rep["matched"] == 2
    assert rep["filter_types"] == ["guard_event"]

    rc, out = _run_cli(
        ["events", str(path), "--type", "guard_start,guard_stop", "--json"], capsys)
    rep = json.loads(out)
    assert rep["matched"] == 2
    assert rep["filter_types"] == ["guard_start", "guard_stop"]


def test_events_limit_va_bosh_fayl(tmp_path, capsys):
    path, _ = _fixture_stream(tmp_path)
    res = cli.read_events(str(path), limit=2)
    assert res["matched"] == 4 and len(res["records"]) == 2

    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    res = cli.read_events(str(empty))
    assert res["count"] == 0 and res["bad_lines"] == [] and not res["truncated_tail"]
    rc, _out = _run_cli(["events", str(empty)], capsys)
    assert rc == 0


def test_events_yoq_fayl(tmp_path, capsys):
    rc, out = _run_cli(["events", str(tmp_path / "yoq.jsonl")], capsys)
    assert rc == 2
    assert "FileNotFoundError" in out


def test_events_inson_chiqishi_payloadni_korsatadi(tmp_path, capsys):
    path, _ = _fixture_stream(tmp_path)
    rc, out = _run_cli(["events", str(path), "--full"], capsys)
    assert rc == 0
    assert "guard_start" in out
    assert "sustained_pressure" in out
    assert "turlar:" in out


# ===========================================================================
# version
# ===========================================================================


def test_version_VERSION_faylini_beradi(capsys):
    expected = open(os.path.join(cli.REPO_ROOT, "VERSION")).read().strip()
    rc, out = _run_cli(["version", "--json"], capsys)
    assert rc == 0
    rep = json.loads(out)
    assert rep["version"] == expected
    assert rep["record_schema_version"] == 1
    assert rep["repo_root"] == cli.REPO_ROOT
    # git holati: commit va dirty flag.
    assert rep["git_commit_short"] is None or len(rep["git_commit_short"]) == 7
    assert rep["git_dirty"] in (True, False, None)


def test_version_inson_chiqishi(capsys):
    expected = open(os.path.join(cli.REPO_ROOT, "VERSION")).read().strip()
    rc, out = _run_cli(["version"], capsys)
    assert rc == 0
    assert expected in out
    assert "commit :" in out


# ===========================================================================
# kichik yordamchilar
# ===========================================================================


def test_human_kb():
    assert cli.human_kb(None) == "?"
    assert cli.human_kb(0) == "0 kiB"
    assert cli.human_kb(512) == "512.0 kiB"
    assert cli.human_kb(2048) == "2.0 MiB"
    assert cli.human_kb(2 * 1024 * 1024) == "2.0 GiB"


def test_talablar_hujjatdan_olingan():
    """Chegaralar guard'dan/hujjatdan olinadi, qayta yozilmaydi."""
    from revix.guard import DEFAULTS

    assert cli.GUARD_SUSTAIN_MAX_S == DEFAULTS["sustain_max_seconds"]
    assert cli.GUARD_MEM_FLOOR_KB == DEFAULTS["host_mem_available_min_kb"]
    assert cli.GUARD_SUSTAIN_RATE == DEFAULTS["sustain_rate_threshold"]
    assert cli.MIN_SYSTEMD_VERSION == 254
    assert cli.PRESSURE_WINDOW_MAX_S == 12.0
    assert cli.MIN_RATE_WINDOW_S == 2.0
    # Slice nomlari dash'siz (01-muhit §2 -- amendment v1 -> v1.1).
    assert "-" not in cli.LAB_SLICE.removesuffix(".slice")
    assert "-" not in cli.MON_SLICE.removesuffix(".slice")


def test_format_check_human_tekislangan():
    c = _fake("kalit", cli.WARN)
    lines = cli.format_check_human(c, 100)
    assert lines[0].startswith("[WARN] kalit")
    assert any("kerak:" in ln for ln in lines)
    assert any("!!" in ln for ln in lines), "WARN da natija satri bo'lishi kerak"
    # PASS da natija satri bosilmaydi (shovqin), lekin JSON'da bor.
    lines = cli.format_check_human(_fake("kalit", cli.PASS), 100)
    assert not any("!!" in ln for ln in lines)
    assert _fake("kalit", cli.PASS).consequence


def test_noaniq_subkomanda_xato():
    with pytest.raises(SystemExit):
        cli.main(["yoq-bunday-komanda"])
    with pytest.raises(SystemExit):
        cli.main([])


# ===========================================================================
# run / analyze / figures -- argv delegatsiyasi (modullar BO'LMASLIGI mumkin)
# ===========================================================================


class _SoxtaModul:
    """`revix.<modul>` o'rnini bosadi: `main(argv)` ga kelgan argv'ni yozib oladi."""

    def __init__(self, rc=0):
        self.rc = rc
        self.calls: list[list[str]] = []

    def main(self, argv=None):
        self.calls.append(list(argv))
        return self.rc


# subkomanda -> (modul, MINIMAL to'g'ri argv, minimal holatda kutilgan modul argv'i)
_MINIMAL = {
    "run": (
        "driver",
        ["run", "--run-dir", "/d/r1", "--seed", "42"],
        ["--run-dir", "/d/r1", "--seed", "42"],
    ),
    "analyze": (
        "analyze",
        ["analyze", "--trials", "t.jsonl", "--run-meta", "m.json", "--out", "a.json"],
        ["--trials", "t.jsonl", "--run-meta", "m.json", "--out", "a.json"],
    ),
    "figures": (
        "figures",
        ["figures", "--analysis", "a.json", "--out-dir", "figs"],
        ["--analysis", "a.json", "--out-dir", "figs"],
    ),
}
_HANDLERS = {"run": "cmd_run", "analyze": "cmd_analyze", "figures": "cmd_figures"}


@pytest.fixture()
def soxta(monkeypatch):
    """Uchala modulga soxta `main` qo'yadi; {modul_nomi: _SoxtaModul} qaytaradi."""
    fakes = {name: _SoxtaModul() for name in ("driver", "analyze", "figures")}
    for name, fake in fakes.items():
        monkeypatch.setitem(sys.modules, f"revix.{name}", fake)
    return fakes


def _json_oldin(argv: list[str]) -> list[str]:
    """`revix <cmd> ... --json` -> `revix --json <cmd> ...`."""
    assert argv[-1] == "--json"
    return ["--json"] + argv[:-1]


@pytest.mark.parametrize("cmd", sorted(_MINIMAL))
def test_yangi_subkomanda_parse_qilinadi_va_handlerga_ulanadi(cmd):
    _mod, argv, _expected = _MINIMAL[cmd]
    args = cli.build_parser().parse_args(argv)
    assert args.cmd == cmd
    assert args.func is getattr(cli, _HANDLERS[cmd])


@pytest.mark.parametrize("cmd", sorted(_MINIMAL))
def test_yangi_subkomanda_majburiy_flagsiz_xato(cmd, capsys, soxta):
    """Har majburiy flag yo'qolsa argparse SystemExit(2) beradi va modulga yetmaydi."""
    mod, argv, _expected = _MINIMAL[cmd]
    flags = [i for i, a in enumerate(argv) if a.startswith("--")]
    assert flags, "test o'zi bo'sh qolmasligi kerak"
    for i in flags:
        cut = argv[:i] + argv[i + 2:]  # shu flag va uning qiymatini olib tashlash
        with pytest.raises(SystemExit) as ei:
            cli.main(cut)
        assert ei.value.code == 2, f"{cmd}: {argv[i]} siz rc=2 kutilgan edi"
    assert soxta[mod].calls == []
    capsys.readouterr()


@pytest.mark.parametrize("cmd", sorted(_MINIMAL))
def test_yangi_subkomanda_yordam_matni_flaglarni_korsatadi(cmd, capsys):
    _mod, argv, _expected = _MINIMAL[cmd]
    with pytest.raises(SystemExit) as ei:
        cli.main([cmd, "--help"])
    assert ei.value.code == 0
    out = capsys.readouterr().out
    for flag in (a for a in argv if a.startswith("--")):
        assert flag in out, f"{cmd} --help da {flag} yo'q"
    assert "--json" in out


def test_run_yordam_matni_ixtiyoriy_flaglarni_korsatadi(capsys):
    with pytest.raises(SystemExit):
        cli.main(["run", "--help"])
    out = capsys.readouterr().out
    for flag in ("--blocks", "--only", "--dry-run"):
        assert flag in out
    with pytest.raises(SystemExit):
        cli.main(["analyze", "--help"])
    out = capsys.readouterr().out
    for flag in ("--sweep", "--episodes", "--events", "--reduction-summary"):
        assert flag in out
    with pytest.raises(SystemExit):
        cli.main(["figures", "--help"])
    assert "--only" in capsys.readouterr().out


def test_run_argv_minimal(soxta):
    rc = cli.main(_MINIMAL["run"][1])
    assert rc == 0
    assert soxta["driver"].calls == [["--run-dir", "/d/r1", "--seed", "42"]]


def test_run_argv_barcha_ixtiyoriy_flaglar_bilan(soxta):
    cli.main(["run", "--run-dir", "/d/r1", "--seed", "42", "--blocks", "3",
              "--only", "arm=B", "--dry-run", "--json"])
    assert soxta["driver"].calls == [[
        "--run-dir", "/d/r1", "--seed", "42", "--blocks", "3",
        "--only", "arm=B", "--dry-run", "--json",
    ]]


def test_run_ixtiyoriy_flaglar_faqat_berilganda_chiqadi(soxta):
    """Berilmagan ixtiyoriy flag argv'da BO'LMASLIGI shart (modul default'i ishlaydi)."""
    cli.main(["run", "--run-dir", "/d/r1", "--seed", "7", "--blocks", "2"])
    assert soxta["driver"].calls[-1] == ["--run-dir", "/d/r1", "--seed", "7",
                                         "--blocks", "2"]
    cli.main(["run", "--run-dir", "/d/r1", "--seed", "7", "--dry-run"])
    assert soxta["driver"].calls[-1] == ["--run-dir", "/d/r1", "--seed", "7",
                                         "--dry-run"]
    cli.main(["run", "--run-dir", "/d/r1", "--seed", "7", "--only", "X"])
    assert soxta["driver"].calls[-1] == ["--run-dir", "/d/r1", "--seed", "7",
                                         "--only", "X"]
    for call in soxta["driver"].calls:
        assert "--json" not in call


def test_run_nol_qiymatlar_yoqolmaydi(soxta):
    """`--seed 0` va `--blocks 0` falsy, lekin berilgan: `is not None` bilan uzatiladi."""
    cli.main(["run", "--run-dir", "/d/r1", "--seed", "0", "--blocks", "0"])
    assert soxta["driver"].calls == [["--run-dir", "/d/r1", "--seed", "0",
                                      "--blocks", "0"]]


def test_run_seed_va_blocks_butun_son_bolishi_shart(soxta, capsys):
    with pytest.raises(SystemExit) as ei:
        cli.main(["run", "--run-dir", "/d/r1", "--seed", "abc"])
    assert ei.value.code == 2
    with pytest.raises(SystemExit) as ei:
        cli.main(["run", "--run-dir", "/d/r1", "--seed", "1", "--blocks", "x"])
    assert ei.value.code == 2
    assert soxta["driver"].calls == [], "yaroqsiz kiritma modulga yetib bormasligi kerak"
    capsys.readouterr()


def test_analyze_argv_minimal_va_sweep(soxta):
    cli.main(_MINIMAL["analyze"][1])
    assert soxta["analyze"].calls[-1] == ["--trials", "t.jsonl", "--run-meta", "m.json",
                                          "--out", "a.json"]
    cli.main(_MINIMAL["analyze"][1] + ["--sweep", "sw.jsonl"])
    assert soxta["analyze"].calls[-1] == ["--trials", "t.jsonl", "--run-meta", "m.json",
                                          "--out", "a.json", "--sweep", "sw.jsonl"]
    cli.main(_MINIMAL["analyze"][1] + ["--sweep", "sw.jsonl", "--json"])
    assert soxta["analyze"].calls[-1] == ["--trials", "t.jsonl", "--run-meta", "m.json",
                                          "--out", "a.json", "--sweep", "sw.jsonl",
                                          "--json"]


def test_analyze_episodes_va_events_argv_tartibi(soxta):
    """Tartib qat'iy: --sweep, --episodes, --events, --json (CLI'da qanday berilganidan qat'i nazar)."""
    base = ["--trials", "t.jsonl", "--run-meta", "m.json", "--out", "a.json"]
    cli.main(_MINIMAL["analyze"][1] + ["--episodes", "ep.jsonl"])
    assert soxta["analyze"].calls[-1] == base + ["--episodes", "ep.jsonl"]
    cli.main(_MINIMAL["analyze"][1] + ["--events", "ev.jsonl"])
    assert soxta["analyze"].calls[-1] == base + ["--events", "ev.jsonl"]
    cli.main(_MINIMAL["analyze"][1] + ["--episodes", "ep.jsonl", "--events", "ev.jsonl"])
    assert soxta["analyze"].calls[-1] == base + [
        "--episodes", "ep.jsonl", "--events", "ev.jsonl"]
    # CLI'da teskari tartibda berilsa ham modul argv'i bir xil tartibda.
    cli.main(["--json"] + _MINIMAL["analyze"][1]
             + ["--events", "ev.jsonl", "--episodes", "ep.jsonl",
                "--sweep", "sw.jsonl"])
    assert soxta["analyze"].calls[-1] == base + [
        "--sweep", "sw.jsonl", "--episodes", "ep.jsonl",
        "--events", "ev.jsonl", "--json"]


def test_analyze_reduction_summary_argv_tartibi(soxta):
    """--reduction-summary --events dan KEYIN, --json dan OLDIN turadi."""
    base = ["--trials", "t.jsonl", "--run-meta", "m.json", "--out", "a.json"]
    cli.main(_MINIMAL["analyze"][1] + ["--reduction-summary", "rs.jsonl"])
    assert soxta["analyze"].calls[-1] == base + ["--reduction-summary", "rs.jsonl"]
    # Hamma ixtiyoriy flag, CLI'da teskari tartibda; modul argv'i qat'iy tartibda.
    cli.main(["--json"] + _MINIMAL["analyze"][1]
             + ["--reduction-summary", "rs.jsonl", "--events", "ev.jsonl",
                "--episodes", "ep.jsonl", "--sweep", "sw.jsonl"])
    assert soxta["analyze"].calls[-1] == base + [
        "--sweep", "sw.jsonl", "--episodes", "ep.jsonl", "--events", "ev.jsonl",
        "--reduction-summary", "rs.jsonl", "--json"]


def test_analyze_episodes_va_events_majburiy_emas(soxta):
    cli.main(_MINIMAL["analyze"][1])
    call = soxta["analyze"].calls[-1]
    for flag in ("--sweep", "--episodes", "--events", "--reduction-summary",
                 "--json"):
        assert flag not in call


def test_figures_argv_minimal(soxta):
    cli.main(_MINIMAL["figures"][1])
    assert soxta["figures"].calls == [["--analysis", "a.json", "--out-dir", "figs"]]


def test_figures_only_takrorlanadi_va_tartib_saqlanadi(soxta):
    cli.main(_MINIMAL["figures"][1] + ["--only", "km_time_to_vr",
                                       "--only", "p_vr_vs_pressure"])
    assert soxta["figures"].calls == [[
        "--analysis", "a.json", "--out-dir", "figs",
        "--only", "km_time_to_vr", "--only", "p_vr_vs_pressure",
    ]]
    cli.main(_MINIMAL["figures"][1] + ["--only", "probe_cost", "--json"])
    assert soxta["figures"].calls[-1] == [
        "--analysis", "a.json", "--out-dir", "figs", "--only", "probe_cost", "--json"]


@pytest.mark.parametrize("cmd", sorted(_MINIMAL))
def test_json_ikkala_joyda_ishlaydi(cmd, soxta):
    """`revix <cmd> --json` va `revix --json <cmd>` bir xil argv beradi; flagsiz -- `--json` yo'q."""
    mod, argv, expected = _MINIMAL[cmd]
    cli.main(argv)
    assert soxta[mod].calls[-1] == expected
    assert "--json" not in soxta[mod].calls[-1]

    cli.main(argv + ["--json"])
    after = soxta[mod].calls[-1]
    cli.main(_json_oldin(argv + ["--json"]))
    before = soxta[mod].calls[-1]
    assert after == before == expected + ["--json"]


def test_modul_chiqish_kodi_ozgartirilmay_uzatiladi(soxta):
    for rc in (0, 1, 3):
        soxta["driver"].rc = rc
        assert cli.main(_MINIMAL["run"][1]) == rc


def test_modul_none_qaytarsa_nol(soxta):
    soxta["analyze"].rc = None
    assert cli.main(_MINIMAL["analyze"][1]) == 0


def test_modul_argparse_xatosi_butun_songa_aylanadi(soxta, capsys):
    """Modulning o'z `ap.error()` i (SystemExit) `cli.main` dan butun son sifatida chiqadi."""

    def main_exit(code):
        def _main(argv=None):
            raise SystemExit(code)
        return _main

    soxta["driver"].main = main_exit(2)
    assert cli.main(_MINIMAL["run"][1]) == 2
    soxta["driver"].main = main_exit(None)
    assert cli.main(_MINIMAL["run"][1]) == 0
    soxta["driver"].main = main_exit("modul xabari")
    assert cli.main(_MINIMAL["run"][1]) == 1
    assert "modul xabari" in capsys.readouterr().err


@pytest.mark.parametrize("cmd", sorted(_MINIMAL))
def test_modul_yoq_bolsa_toza_xato_va_non_zero(cmd, monkeypatch, capsys):
    """Modul yo'q -> aniq o'zbekcha xabar (stderr), rc=127, traceback YO'Q."""
    mod, argv, _expected = _MINIMAL[cmd]
    # `None` -- sys.modules da "import halted": modul bor-yo'qligidan qat'i nazar
    # (boshqa agent'ning moduli keyin paydo bo'lsa ham) ModuleNotFoundError beradi.
    monkeypatch.setitem(sys.modules, f"revix.{mod}", None)
    rc = cli.main(argv)
    cap = capsys.readouterr()
    assert rc == cli.EXIT_MODULE_UNAVAILABLE
    assert rc not in (0, 1, 2)
    assert cap.out == ""
    assert f"revix.{mod}" in cap.err
    assert "topilmadi" in cap.err
    assert "revix doctor" in cap.err
    assert "Traceback" not in cap.err


@pytest.mark.parametrize("cmd", sorted(_MINIMAL))
def test_modul_yoq_bolsa_json_rejimida_barqaror_hisobot(cmd, monkeypatch, capsys):
    mod, argv, _expected = _MINIMAL[cmd]
    monkeypatch.setitem(sys.modules, f"revix.{mod}", None)
    rc = cli.main(argv + ["--json"])
    rep = json.loads(capsys.readouterr().out)
    assert rc == cli.EXIT_MODULE_UNAVAILABLE
    assert rep["report_schema_version"] == cli.REPORT_SCHEMA_VERSION
    assert rep["tool"] == f"revix {cmd}"
    assert rep["ok"] is False
    assert rep["error"] == "module_unavailable"
    assert rep["module"] == f"revix.{mod}"
    assert rep["detail"].strip()


def _import_module_almashtir(monkeypatch, target: str, exc: BaseException):
    """`importlib.import_module(target)` istisno tashlasin; qolganlari haqiqiy."""
    real = importlib.import_module

    def fake(name, package=None):
        if name == target:
            raise exc
        return real(name, package)

    monkeypatch.setattr(importlib, "import_module", fake)


def test_bogliqlik_yoq_bolsa_toza_xato_matplotlib(monkeypatch, capsys):
    """`revix.figures` bor, lekin matplotlib yo'q -> modulning o'zi emas, BOG'LIQLIK nomi aytiladi."""
    _import_module_almashtir(
        monkeypatch, "revix.figures",
        ModuleNotFoundError("No module named 'matplotlib'", name="matplotlib"))
    rc = cli.main(_MINIMAL["figures"][1])
    err = capsys.readouterr().err
    assert rc == cli.EXIT_MODULE_UNAVAILABLE
    assert "matplotlib" in err
    assert "yetishmayapti" in err
    assert "Traceback" not in err


def test_boshqa_import_xatosi_ham_toza_xato(monkeypatch, capsys):
    _import_module_almashtir(
        monkeypatch, "revix.driver",
        ImportError("cannot import name 'x' from 'revix.schema'"))
    rc = cli.main(_MINIMAL["run"][1])
    err = capsys.readouterr().err
    assert rc == cli.EXIT_MODULE_UNAVAILABLE
    assert "cannot import name" in err
    assert "Traceback" not in err


def test_main_siz_modul_toza_xato(monkeypatch, capsys):
    class MainSiz:
        pass

    monkeypatch.setitem(sys.modules, "revix.analyze", MainSiz())
    rc = cli.main(_MINIMAL["analyze"][1])
    err = capsys.readouterr().err
    assert rc == cli.EXIT_MODULE_UNAVAILABLE
    assert "main(argv)" in err


def test_cli_import_qilinganda_ogir_modullar_yuklanmaydi():
    """LAZY import: `import revix.cli` matplotlib'ni ham, uch modulni ham yuklamaydi.

    Aks holda matplotlib yo'q mashinada `revix doctor` ham yiqilardi -- pre-flight
    vositasi aynan buzuq muhitni tashxis qilish uchun bor. Toza subprocess:
    pytest jarayoni bu modullarni allaqachon yuklagan bo'lishi mumkin.
    """
    code = (
        "import sys; import revix.cli; "
        "bad = [m for m in ('matplotlib', 'revix.driver', 'revix.analyze', "
        "'revix.figures') if m in sys.modules]; "
        "print(','.join(bad)); sys.exit(1 if bad else 0)"
    )
    p = subprocess.run([sys.executable, "-c", code], cwd=cli.REPO_ROOT,
                       capture_output=True, text=True, timeout=60, check=False)
    assert p.returncode == 0, (
        f"top-level import qilingan: {p.stdout.strip()} {p.stderr[-300:]}")


# ===========================================================================
# doctor: matplotlib IXTIYORIY (WARN), majburiy modullar FAIL
# ===========================================================================


def _versiyalar(yoq: set[str]):
    return lambda name: None if name in yoq else "1.0"


def test_matplotlib_yoq_bolsa_WARN_va_gate_ochiq(monkeypatch):
    monkeypatch.setattr(cli, "_module_version", _versiyalar({"matplotlib"}))
    c = cli.check_python_modules()
    assert c.status == cli.WARN
    assert "matplotlib" in c.observed
    assert c.detail["missing"] == []
    assert c.detail["optional_missing"] == ["matplotlib"]
    assert c.detail["optional_found"] == {"matplotlib": None}
    assert "WARN" in c.consequence
    # WARN gate'ni yopmaydi: o'lchash ham, tahlil ham matplotlib'siz ishlaydi.
    rep = cli.build_report([c])
    assert rep["summary"]["ok"] is True
    assert cli.exit_code_for(rep) == 0


def test_majburiy_modul_yoq_bolsa_FAIL(monkeypatch):
    for yoq in ({"numpy"}, {"psutil", "dbus"}, {"scipy", "matplotlib"}):
        monkeypatch.setattr(cli, "_module_version", _versiyalar(yoq))
        c = cli.check_python_modules()
        assert c.status == cli.FAIL, yoq
        assert set(c.detail["missing"]) == yoq - {"matplotlib"}
        assert cli.exit_code_for(cli.build_report([c])) == 1


def test_hamma_modul_bor_bolsa_PASS(monkeypatch):
    monkeypatch.setattr(cli, "_module_version", _versiyalar(set()))
    c = cli.check_python_modules()
    assert c.status == cli.PASS
    assert c.detail["missing"] == [] and c.detail["optional_missing"] == []
    assert set(c.detail["found"]) == set(cli.REQUIRED_MODULES)
    assert set(c.detail["optional_found"]) == set(cli.OPTIONAL_MODULES)


def test_matplotlib_majburiy_emas_ixtiyoriy():
    assert "matplotlib" in cli.OPTIONAL_MODULES
    assert "matplotlib" not in cli.REQUIRED_MODULES
    assert set(cli.REQUIRED_MODULES) == {"psutil", "dbus", "numpy", "scipy"}


def test_python_modules_haqiqiy_muhitda_mustaqil_find_spec_bilan_mos(doctor_json):
    """Haqiqiy muhit: python_modules natijasi mustaqil `find_spec` bilan mos."""
    import importlib.util

    c = next(c for c in doctor_json["checks"] if c["key"] == "python_modules")
    mpl_bor = importlib.util.find_spec("matplotlib") is not None
    assert (c["detail"]["optional_found"]["matplotlib"] is not None) is mpl_bor
    if c["detail"]["missing"]:
        assert c["status"] == "FAIL"
    elif not mpl_bor:
        assert c["status"] == "WARN"
    else:
        assert c["status"] == "PASS"


def test_EXPECTED_CHECK_KEYS_CHECKS_bilan_mos():
    """Registr va barqaror kalitlar ro'yxati bir-biridan uzoqlashmasligi kerak."""
    keys = [fn.__name__.removeprefix("check_") for fn in cli.CHECKS]
    assert keys == list(cli.EXPECTED_CHECK_KEYS)
    assert len(set(keys)) == len(keys)
    assert "python_modules" in keys
