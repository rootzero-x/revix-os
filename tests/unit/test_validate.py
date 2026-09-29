"""validate.py testlari -- HAR invariant uchun bitta test.

PREREGISTRATION.md §7: "Validator analizdan oldin o'tishi shart; o'tmagan run
analiz qilinmaydi." Demak validator jimgina o'tkazib yuborsa, butun
reproducibility zanjiri buziladi -- shuning uchun har invariant buzilishi
ALOHIDA sinaladi.

Har test toza run'dan boshlanadi (u XATOSIZ o'tishi kerak) va AYNAN BITTA
buzilish kiritadi.
"""
import json

import pytest

from revix import reduce as R
from revix import validate as V
from revix.schema import DISPOSITIONS

T0 = 1_000_000
P = R.P_US


# --- toza run quruvchi ------------------------------------------------------


class Builder:
    """`seq` har (emitter, record_type) uchun monotonik -- aynan schema.py
    dagi `Emitter` kabi, chunki validator bo'shliqni shu asosda tekshiradi."""

    def __init__(self):
        self.records = []
        self.probes = []
        self._seq = {}

    def _env(self, rt, mono_us, trial_id, emitter, boot_id="boot1",
             schema_version=1):
        key = (emitter, rt)
        self._seq[key] = self._seq.get(key, 0) + 1
        return {
            "schema_version": schema_version, "record_type": rt,
            "run_id": "run1", "session_id": "sess1", "boot_id": boot_id,
            "trial_id": trial_id, "block_index": 0, "seq": self._seq[key],
            "mono_us": mono_us, "real_us": 0, "emitter": emitter,
        }

    def add(self, rt, mono_us=0, *, trial_id="t0", emitter="driver:1", **payload):
        rec = self._env(rt, mono_us, trial_id, emitter)
        rec.update(payload)
        self.records.append(rec)
        return rec

    def probe(self, k, *, outcome="ok", progress=None, invocation="inv1",
              trial_id="t0"):
        rec = self._env(R.RT_PROBE, T0 + k * P, trial_id, "prober:2")
        rec.update({"mono_us_send": T0 + k * P, "outcome": outcome,
                    "progress": progress, "invocation_id_seen": invocation,
                    "pid_seen": 4711, "rt_us": 900})
        self.probes.append(rec)
        return rec

    def run(self):
        return R.RawRun(records=[dict(r) for r in self.records],
                        probes=[dict(r) for r in self.probes],
                        sources=["<memory>"])


def clean() -> Builder:
    """Barcha invariantlarni qanoatlantiradigan minimal run.

    10 x 100 ms baseline -> fault -> 3 buzilgan probe -> restart -> 17 ok probe.
    """
    b = Builder()
    b.add(R.RT_RUN_META, 0, trial_id=None, git_dirty=False, run_mode="pilot",
          preregistration_sha256="0b1fdd18783bd27b22d0d64291eea657",
          rng_seed=12345)
    b.add(R.RT_TRIAL_BEGIN, T0, arm="A", pressure_band="P1",
          fault_class="clean_crash")
    b.add(R.RT_UNIT_STATE, T0, active_state="active", result="success",
          n_restarts=0, invocation_id="inv1",
          active_enter_ts_mono_us=T0 - 500_000, active_exit_ts_mono_us=0)
    for k in range(10):
        b.probe(k, progress=200 * (k + 1), invocation="inv1")
    b.add(R.RT_FAULT_INJECT, T0 + 1_000_000, kind="exit",
          mono_us_before_call=T0 + 999_000, mono_us_after_call=T0 + 1_000_000)
    for k in range(10, 13):
        b.probe(k, outcome="conn_refused", progress=None, invocation=None)
    b.add(R.RT_ACTION, T0 + 1_250_000, action_id="a0", action_class="restart",
          policy_delay_us=100_000)
    for k in range(13, 30):
        b.probe(k, progress=200 * (k - 12), invocation="inv2")
    b.add(R.RT_UNIT_STATE, T0 + 1_300_000, active_state="active",
          result="success", n_restarts=1, invocation_id="inv2",
          active_enter_ts_mono_us=T0 + 1_300_000,
          active_exit_ts_mono_us=T0 + 1_000_000)
    b.add(R.RT_TRIAL_END, T0 + 3_000_000, disposition="complete")
    return b


def renumber_probes(b):
    """Probe'larni qayta raqamlaydi.

    Prober qotib qolganda o'tkazib yuborilgan deadline uchun record YOZILMAYDI,
    demak VAQT bo'shligi bo'ladi, lekin `seq` UZLUKSIZ qoladi. Shu holatni
    modellash uchun probe uzilishi testlari seq'ni qayta raqamlaydi -- aks
    holda test `seq_gap` ni ham qo'zg'atib, aynan nimani sinayotgani
    noaniq bo'lardi.
    """
    for i, pr in enumerate(b.probes, start=1):
        pr["seq"] = i
    return b


def codes(rep, severity=None):
    return [f.code for f in rep.findings
            if severity is None or f.severity == severity]


# --- 0. toza run o'tadi -----------------------------------------------------


def test_toza_run_otadi():
    rep = V.validate_run(clean().run())
    assert rep.findings == [], [str(f) for f in rep.findings]
    assert rep.ok is True
    assert rep.n_trials == 1
    assert rep.run_mode == "pilot"


# --- 1. trial_begin <-> trial_end ------------------------------------------


def test_trial_begin_end_siz_aniqlanadi():
    b = clean()
    b.records = [r for r in b.records if r["record_type"] != R.RT_TRIAL_END]
    rep = V.validate_run(b.run())
    assert "trial_begin_without_end" in codes(rep, V.SEVERITY_ERROR)
    assert rep.ok is False
    f = next(f for f in rep.findings if f.code == "trial_begin_without_end")
    assert f.trial_id == "t0"          # topish uchun kontekst bor


def test_trial_end_begin_siz_aniqlanadi():
    b = clean()
    b.records = [r for r in b.records if r["record_type"] != R.RT_TRIAL_BEGIN]
    rep = V.validate_run(b.run())
    assert "trial_end_without_begin" in codes(rep, V.SEVERITY_ERROR)
    assert rep.ok is False


def test_trial_begin_takrori_aniqlanadi():
    b = clean()
    b.add(R.RT_TRIAL_BEGIN, T0 + 10, arm="A", pressure_band="P1")
    rep = V.validate_run(b.run())
    assert "trial_begin_duplicate" in codes(rep, V.SEVERITY_ERROR)


# --- 2. AYNAN BITTA disposition, yopiq enumdan (§12) ----------------------


def test_disposition_yoq_aniqlanadi():
    b = clean()
    for r in b.records:
        if r["record_type"] == R.RT_TRIAL_END:
            r["disposition"] = None
    rep = V.validate_run(b.run())
    assert "disposition_missing" in codes(rep, V.SEVERITY_ERROR)
    assert rep.ok is False


def test_disposition_ikkitasi_aniqlanadi():
    b = clean()
    b.add("trial_disposition", T0 + 3_100_000, disposition="censored")
    rep = V.validate_run(b.run())
    f = next(f for f in rep.findings if f.code == "disposition_duplicate")
    assert f.severity == V.SEVERITY_ERROR
    assert f.detail["dispositions"] == ["complete", "censored"]
    assert rep.ok is False


def test_disposition_enumdan_tashqari_aniqlanadi():
    """`failed` yopiq enumda YO'Q (§12) -- va bu tasodifiy emas: probe uzilishi
    hech qachon `failed` bo'lmaydi (§4)."""
    assert "failed" not in DISPOSITIONS
    b = clean()
    for r in b.records:
        if r["record_type"] == R.RT_TRIAL_END:
            r["disposition"] = "failed"
    rep = V.validate_run(b.run())
    assert "disposition_unknown" in codes(rep, V.SEVERITY_ERROR)
    assert rep.ok is False


# --- 3. seq bo'shliqlari (jimgina yo'qolgan record) -----------------------


def test_seq_boshligi_aniqlanadi():
    b = clean()
    lost = b.probes[5]["seq"]                         # 6..105 yo'qoldi
    b.probes[5]["seq"] = lost + 100
    rep = V.validate_run(b.run())
    f = next(f for f in rep.findings if f.code == "seq_gap")
    assert f.severity == V.SEVERITY_ERROR
    assert f.stream == "prober:2/probe_sample"
    assert lost in f.detail["missing_seq"]
    assert f.detail["max_seq"] == lost + 100
    assert rep.ok is False


def test_seq_boshligi_yoqolgan_birinchi_recordni_ham_tutadi():
    """Oqimning BIRINCHI record'i yo'qolsa ham bo'shliq (1 dan boshlanadi)."""
    b = clean()
    b.probes = b.probes[1:]
    rep = V.validate_run(b.run())
    f = next(f for f in rep.findings if f.code == "seq_gap")
    assert f.detail["missing_seq"] == [1]


def test_seq_takrori_aniqlanadi():
    b = clean()
    b.probes[5]["seq"] = b.probes[4]["seq"]
    rep = V.validate_run(b.run())
    assert "seq_duplicate" in codes(rep, V.SEVERITY_ERROR)
    assert rep.ok is False


def test_har_oqim_mustaqil_hisoblanadi():
    """`driver` va `prober` oqimlari alohida: biri 1..n, boshqasi 1..m."""
    rep = V.validate_run(clean().run())
    assert "seq_gap" not in codes(rep)


# --- 4. probe uzilishi > 2xP -> trial `censored` bo'lishi SHART (§4) ------


def test_probe_uzilishi_disposition_censored_bolmasa_xato():
    b = clean()
    b.probes = [p for p in b.probes
                if not (T0 + 20 * P <= p["mono_us_send"] <= T0 + 24 * P)]
    renumber_probes(b)
    rep = V.validate_run(b.run())
    f = next(f for f in rep.findings if f.code == "probe_gap")
    assert f.severity == V.SEVERITY_ERROR
    assert "censored" in f.message
    assert f.detail["limit_us"] == 2 * P
    assert f.detail["disposition"] == "complete"
    assert rep.ok is False


def test_probe_uzilishi_censored_bolsa_faqat_ogohlantirish():
    """Uzilish qayd etilgan va trial `censored` -> run analiz qilinishi mumkin.

    Instrumentatsiya yo'qolishi natijaga aylanmaydi, LEKIN jimgina ham
    qolmaydi: ogohlantirish chiqadi.
    """
    b = clean()
    b.probes = [p for p in b.probes
                if not (T0 + 20 * P <= p["mono_us_send"] <= T0 + 24 * P)]
    renumber_probes(b)
    for r in b.records:
        if r["record_type"] == R.RT_TRIAL_END:
            r["disposition"] = "censored"
    rep = V.validate_run(b.run())
    assert "probe_gap" in codes(rep, V.SEVERITY_WARNING)
    assert "probe_gap" not in codes(rep, V.SEVERITY_ERROR)
    assert rep.ok is True


def test_ikki_p_gacha_uzilish_xato_emas():
    """Chegarada: aynan 2xP uzilish -- hali xato emas."""
    b = clean()
    b.probes = [p for p in b.probes if p["mono_us_send"] != T0 + 20 * P]
    renumber_probes(b)
    rep = V.validate_run(b.run())
    assert "probe_gap" not in codes(rep)


# --- 5. boot_id sessiya ichida doimiy (§1) --------------------------------


def test_boot_id_ozgarishi_aniqlanadi():
    """Monotonic qiymatlar faqat bitta boot ichida taqqoslanadi."""
    b = clean()
    for r in b.records:
        if r["record_type"] == R.RT_TRIAL_END:
            r["boot_id"] = "boot2"
    rep = V.validate_run(b.run())
    f = next(f for f in rep.findings if f.code == "boot_id_inconsistent")
    assert f.severity == V.SEVERITY_ERROR
    assert f.detail["boot_ids"] == ["boot1", "boot2"]
    assert rep.ok is False


# --- 6. har action uchun invocation o'zgarishi yoki oshkora defer ---------


def test_tasirsiz_action_aniqlanadi():
    b = clean()
    # Invocation o'zgarmaydi: restart'dan keyin ham inv1.
    for p in b.probes:
        p["invocation_id_seen"] = "inv1" if p["outcome"] == "ok" else None
    for r in b.records:
        if r["record_type"] == R.RT_UNIT_STATE:
            r["invocation_id"] = "inv1"
            r["n_restarts"] = 0
    rep = V.validate_run(b.run())
    f = next(f for f in rep.findings
             if f.code == "action_without_invocation_change")
    assert f.severity == V.SEVERITY_ERROR
    assert f.trial_id == "t0"
    assert f.detail["action_id"] == "a0"
    assert rep.ok is False


def test_oshkora_defer_action_xato_emas():
    b = clean()
    for p in b.probes:
        p["invocation_id_seen"] = "inv1" if p["outcome"] == "ok" else None
    for r in b.records:
        if r["record_type"] == R.RT_UNIT_STATE:
            r["invocation_id"] = "inv1"
            r["n_restarts"] = 0
        if r["record_type"] == R.RT_ACTION:
            r["deferred"] = True
    rep = V.validate_run(b.run())
    assert "action_without_invocation_change" not in codes(rep)
    assert rep.ok is True


def test_alohida_defer_recordi_ham_qabul_qilinadi():
    b = clean()
    for p in b.probes:
        p["invocation_id_seen"] = "inv1" if p["outcome"] == "ok" else None
    for r in b.records:
        if r["record_type"] == R.RT_UNIT_STATE:
            r["invocation_id"] = "inv1"
            r["n_restarts"] = 0
    b.add(R.RT_ACTION_DEFER, T0 + 1_260_000, action_id="a0",
          reason="pressure_gate")
    rep = V.validate_run(b.run())
    assert "action_without_invocation_change" not in codes(rep)
    assert rep.ok is True


def test_nrestarts_oshishi_ham_action_tasirini_tasdiqlaydi():
    b = clean()
    for p in b.probes:
        p["invocation_id_seen"] = "inv1" if p["outcome"] == "ok" else None
    # invocation o'zgarmadi, lekin NRestarts oshdi.
    rep = V.validate_run(b.run())
    assert "action_without_invocation_change" not in codes(rep)


# --- 7. run_meta.git_dirty (§7) -------------------------------------------


def test_git_dirty_confirmatory_run_uchun_xato():
    b = clean()
    for r in b.records:
        if r["record_type"] == R.RT_RUN_META:
            r["git_dirty"] = True
            r["run_mode"] = "confirmatory"
    rep = V.validate_run(b.run())
    f = next(f for f in rep.findings if f.code == "git_dirty")
    assert f.severity == V.SEVERITY_ERROR
    assert rep.ok is False


def test_git_dirty_pilot_run_uchun_ogohlantirish():
    """Pilot ishlab chiqish davomida ishlaydi; P1 ma'lumotlari confirmatory
    analizga qo'shilmaydi (§13) -- shuning uchun ogohlantirish."""
    b = clean()
    for r in b.records:
        if r["record_type"] == R.RT_RUN_META:
            r["git_dirty"] = True
    rep = V.validate_run(b.run())
    f = next(f for f in rep.findings if f.code == "git_dirty")
    assert f.severity == V.SEVERITY_WARNING
    assert rep.ok is True


def test_run_mode_argumenti_run_metani_bosib_otadi():
    b = clean()
    for r in b.records:
        if r["record_type"] == R.RT_RUN_META:
            r["git_dirty"] = True
    rep = V.validate_run(b.run(), run_mode="confirmatory")
    assert next(f for f in rep.findings
                if f.code == "git_dirty").severity == V.SEVERITY_ERROR
    assert rep.ok is False


def test_git_dirty_yoq_bolsa_xato():
    b = clean()
    for r in b.records:
        if r["record_type"] == R.RT_RUN_META:
            del r["git_dirty"]
    rep = V.validate_run(b.run())
    assert "git_dirty_missing" in codes(rep, V.SEVERITY_ERROR)


def test_run_meta_yoq_bolsa_xato():
    b = clean()
    b.records = [r for r in b.records if r["record_type"] != R.RT_RUN_META]
    rep = V.validate_run(b.run())
    assert "run_meta_missing" in codes(rep, V.SEVERITY_ERROR)
    assert rep.ok is False


def test_preregistration_sha256_yoq_bolsa_xato():
    """Qaysi ta'riflar ostida o'lchangani aniqlanmasa, run qiymatsiz."""
    b = clean()
    for r in b.records:
        if r["record_type"] == R.RT_RUN_META:
            del r["preregistration_sha256"]
    rep = V.validate_run(b.run())
    assert "preregistration_sha256_missing" in codes(rep, V.SEVERITY_ERROR)


# --- 8. schema_version har record uchun ma'lum -----------------------------


def test_nomalum_schema_version_aniqlanadi():
    b = clean()
    b.records[3]["schema_version"] = 99
    rep = V.validate_run(b.run())
    f = next(f for f in rep.findings if f.code == "schema_version_unknown")
    assert f.severity == V.SEVERITY_ERROR
    assert f.index == b.records[3].get("__index__")
    assert rep.ok is False


def test_schema_version_yoq_bolsa_aniqlanadi():
    b = clean()
    del b.probes[2]["schema_version"]
    rep = V.validate_run(b.run())
    assert "schema_version_unknown" in codes(rep, V.SEVERITY_ERROR)


def test_csv_probe_oqimida_envelope_talab_qilinmaydi(tmp_path):
    """Yuqori tezlikli CSV oqimida envelope YO'Q (schema.py CsvWriter) --
    bu xato emas."""
    csv_path = tmp_path / "probes.csv"
    rows = ["mono_us_send,outcome,progress,invocation_id_seen,seq,trial_id"]
    for k in range(3):
        rows.append(f"{T0 + k * P},ok,{200 * (k + 1)},inv1,{k + 1},t0")
    csv_path.write_text("\n".join(rows) + "\n")
    run = R.RawRun.load([], [str(csv_path)])
    assert "schema_version_unknown" not in codes(V.validate_run(run))


# --- 9. buzilgan/qismli qatorlar -----------------------------------------


def test_qismli_oxirgi_qator_ogohlantirish(tmp_path):
    """Crash'da qismli oxirgi qator tashlanadi, LEKIN qayd etiladi."""
    p = tmp_path / "raw.jsonl"
    b = clean()
    with open(p, "w", encoding="utf-8") as fh:
        for r in b.records:
            fh.write(json.dumps(r) + "\n")
        for r in b.probes:
            fh.write(json.dumps(r) + "\n")
        fh.write('{"record_type": "probe_sam')     # qismli
    run = R.RawRun.load([str(p)])
    rep = V.validate_run(run)
    assert "truncated_line" in codes(rep, V.SEVERITY_WARNING)
    assert rep.ok is True


def test_buzilgan_json_xato(tmp_path):
    p = tmp_path / "raw.jsonl"
    b = clean()
    with open(p, "w", encoding="utf-8") as fh:
        for r in b.records:
            fh.write(json.dumps(r) + "\n")
        fh.write("{not json}\n")
        for r in b.probes:
            fh.write(json.dumps(r) + "\n")
    rep = V.validate_run(R.RawRun.load([str(p)]))
    assert "bad_json" in codes(rep, V.SEVERITY_ERROR)
    assert rep.ok is False


# --- 10. CLI: nolga teng bo'lmagan kod va --json --------------------------


def _write(tmp_path, b, name="raw.jsonl"):
    p = tmp_path / name
    with open(p, "w", encoding="utf-8") as fh:
        for r in b.records:
            fh.write(json.dumps(r) + "\n")
        for r in b.probes:
            fh.write(json.dumps(r) + "\n")
    return str(p)


def test_cli_toza_runda_nol_qaytaradi(tmp_path, capsys):
    rc = V.main(["--jsonl", _write(tmp_path, clean())])
    assert rc == 0
    assert "O'TDI" in capsys.readouterr().out


def test_cli_xatoda_nolga_teng_bolmagan_kod(tmp_path, capsys):
    b = clean()
    b.records = [r for r in b.records if r["record_type"] != R.RT_TRIAL_END]
    rc = V.main(["--jsonl", _write(tmp_path, b)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "O'TMADI" in out
    assert "trial_begin_without_end" in out


def test_cli_json_hisobot(tmp_path, capsys):
    b = clean()
    b.probes[5]["seq"] += 50
    rc = V.main(["--jsonl", _write(tmp_path, b), "--json"])
    assert rc == 1
    rep = json.loads(capsys.readouterr().out)
    assert rep["ok"] is False
    assert rep["n_errors"] >= 1
    assert rep["n_trials"] == 1
    assert any(f["code"] == "seq_gap" for f in rep["findings"])
    # Har finding'da topish uchun kontekst bor.
    f = next(f for f in rep["findings"] if f["code"] == "seq_gap")
    assert set(f) >= {"code", "severity", "message", "stream", "detail"}


def test_cli_kirish_bolmasa_xato():
    with pytest.raises(SystemExit):
        V.main([])


# --- 11. hisobot tuzilishi -----------------------------------------------


def test_hisobotda_har_buzilish_alohida_beriladi():
    """Birinchi xatoda to'xtamaydi -- run'ni tuzatish uchun to'liq ro'yxat
    kerak."""
    b = clean()
    b.records = [r for r in b.records if r["record_type"] != R.RT_TRIAL_END]
    b.records[2]["schema_version"] = 7
    b.probes[3]["seq"] += 9
    rep = V.validate_run(b.run())
    got = set(codes(rep, V.SEVERITY_ERROR))
    assert {"trial_begin_without_end", "disposition_missing",
            "schema_version_unknown", "seq_gap"} <= got
    assert str(rep.findings[0]).startswith(("ERROR", "WARNING"))
