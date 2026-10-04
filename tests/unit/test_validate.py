"""validate.py testlari -- HAR invariant uchun bitta test.

PREREGISTRATION.md §7: "Validator analizdan oldin o'tishi shart; o'tmagan run
analiz qilinmaydi." Demak validator jimgina o'tkazib yuborsa, butun
reproducibility zanjiri buziladi -- shuning uchun har invariant buzilishi
ALOHIDA sinaladi.

Har test toza run'dan boshlanadi (u XATOSIZ o'tishi kerak) va AYNAN BITTA
buzilish kiritadi.
"""
import gzip
import json
import os

import pytest

from revix import driver as D
from revix import reduce as R
from revix import validate as V
from revix.schedule import (DISPOSITION_RULES, Factor, TrialTimeline,
                            make_schedule)
from revix.schema import DISPOSITIONS

T0 = 1_000_000
P = R.P_US
REAL0 = 1_791_000_000_000_000   # CLOCK_REALTIME - CLOCK_MONOTONIC siljishi

# Bir yacheykali jadval: toza run'dagi YAGONA trial shu jadvaldan (§8.4).
SCHED = make_schedule([Factor("arm", ("A",)),
                       Factor("pressure_level", ("P1",))], 1, 12345)
TID = SCHED.trials[0].trial_id
# T_trial = t_pressure_off + w_stab_s + P (kontrakt v1.1 §5.2). Bu vaqtlar
# `HOLD_CAP_S` ga bog'liq (default hold_s = HOLD_CAP_S), shuning uchun ular
# QOTIRILMAYDI -- default `TrialTimeline` dan HISOBLANADI. Eski kod 12 s cap
# ning natijasini (32 s / 40.1 s) jimgina o'zida saqlardi; cap o'zgarganda
# fixture eski qiymatga qotib, formula testini yolg'on o'tkazmasligi kerak.
_TL = TrialTimeline()
T_PRESSURE_OFF_S = _TL.t_pressure_off
T_TRIAL_US = round((_TL.t_pressure_off + _TL.w_stab_s) * 1_000_000) + P
N_PROBES = T_TRIAL_US // 100_000 + 1   # k = 0..N-1 -> T0 .. T0 + T_TRIAL (har 100 ms)


# --- toza run quruvchi ------------------------------------------------------


class Builder:
    """`seq` har (emitter, record_type) uchun monotonik -- aynan schema.py
    dagi `Emitter` kabi, chunki validator bo'shliqni shu asosda tekshiradi."""

    def __init__(self, tid=None):
        self.records = []
        self.probes = []
        self._seq = {}
        self.tid = tid or TID

    def _env(self, rt, mono_us, trial_id, emitter, boot_id="boot1",
             schema_version=1):
        key = (emitter, rt)
        self._seq[key] = self._seq.get(key, 0) + 1
        return {
            "schema_version": schema_version, "record_type": rt,
            "stream": rt,       # kontrakt v1.1 §4.2-3: stream = record_type
            "run_id": "run1", "session_id": "sess1", "boot_id": boot_id,
            "trial_id": trial_id, "block_index": 0, "seq": self._seq[key],
            # real_us = REAL0 + mono_us: soatlar BIR XIL tezlikda yuradi
            # (haqiqiy guest'dagidek). Avval doimiy 0 edi -- bu "realtime
            # to'xtagan" degani, va `host_clock_discontinuity` uni to'g'ri
            # ravishda uzilish deb ko'radi.
            "mono_us": mono_us, "real_us": REAL0 + mono_us, "emitter": emitter,
        }

    def add(self, rt, mono_us=0, *, trial_id="__default__", emitter="driver:1",
            **payload):
        if trial_id == "__default__":
            trial_id = self.tid
        rec = self._env(rt, mono_us, trial_id, emitter)
        rec.update(payload)
        self.records.append(rec)
        return rec

    def probe(self, k, *, outcome="ok", progress=None, invocation="inv1",
              trial_id="__default__"):
        if trial_id == "__default__":
            trial_id = self.tid
        rec = self._env(R.RT_PROBE, T0 + k * P, trial_id, "prober:2")
        rec.update({"mono_us_send": T0 + k * P,
                    "real_us_send": REAL0 + T0 + k * P, "outcome": outcome,
                    "progress": progress, "invocation_id_seen": invocation,
                    "pid_seen": 4711, "rt_us": 900})
        self.probes.append(rec)
        return rec

    def run(self):
        return R.RawRun(records=[dict(r) for r in self.records],
                        probes=[dict(r) for r in self.probes],
                        sources=["<memory>"])


def timing(horizon_end_us, pressure_off_s=T_PRESSURE_OFF_S):
    """`trial_end.timing` (driver TrialTiming): T_h va horizon. `0` = hech
    qachon o'rnatilmagan (monotonic timestamp, o'lchangan nol EMAS)."""
    return {"begin_mono_us": T0, "pressure_off_mono_us":
            T0 + int(pressure_off_s * 1_000_000) if pressure_off_s else 0,
            "horizon_end_mono_us": horizon_end_us}


def gen(uptime, ticks=4242):
    """Guest generation markeri: PID 1 starttime + uptime o'qishi."""
    return {"pid1_starttime_ticks": ticks, "uptime_s": uptime}


def units_ok():
    """TIRIK paytida olingan dump (`units.dump_unit_properties` shakli)."""
    return {"revix-sut.service": {
        "unit": "revix-sut.service", "source": "systemctl --user show",
        "alive_before": True, "alive_after": True, "load_state": "loaded",
        "dump_valid": True, "systemctl_rc": 0, "property_count": 2,
        "properties": {"LoadState": "loaded", "MemoryMax": "67108864"}}}


def clean(sched=None, tid=None) -> Builder:
    """Barcha invariantlarni qanoatlantiradigan driver-to'liq run.

    Guard start -> prober start -> trial_begin -> baseline (10 x 100 ms) ->
    fault -> 3 buzilgan probe -> restart -> ok probe'lar -> trial_end
    (T0 + T_trial) -> prober stop -> guard stop. Bitta trial, bitta yacheyka.
    """
    sched = sched or SCHED
    tid = tid or sched.trials[0].trial_id
    st = next(t for t in sched.trials if t.trial_id == tid)
    arm, band = st.level("arm"), st.level("pressure_level")
    b = Builder(tid)
    b.add(R.RT_RUN_META, 0, trial_id=None, git_dirty=False, run_mode="pilot",
          preregistration_sha256="SYNTHETIC-FIXTURE-NOT-A-REAL-HASH",
          rng_seed=sched.seed, preregistration_version="synthetic",
          started_real_us=0, started_mono_us=0, git_commit="synthetic",
          schedule_digest=sched.digest(), schedule=sched.as_dict(),
          uname=None, systemd_version=None, cpu_model=None, cpu_count=4,
          mem_total_kb=None, cgroup_delegated_controllers=None,
          oomd_effective=None,
          governor=None, scaling_driver=None,    # WSL2: cpufreq sysfs yo'q
          python_version="3", module_versions={}, units_show=units_ok(),
          t_trial_us=T_TRIAL_US,
          t_trial_formula="t_pressure_off + w_stab_s + P",
          guest_generation=gen(1.0))
    b.add(V.RT_GUARD_START, 100_000, trial_id=None, emitter="guard:3",
          watch_cgroup="w", lab_cgroup="l")
    b.add("prober_start", T0 - 100_000, emitter="prober:2", hz=10)
    b.add(R.RT_TRIAL_BEGIN, T0, arm=arm, pressure_band=band,
          fault_class="clean_crash", position_in_block=st.position_in_block,
          planned_timeline=TrialTimeline().as_dict())
    b.add("env_snapshot", T0 + 1, guest_generation=gen(2.0))
    b.add(R.RT_UNIT_STATE, T0, active_state="active", result="success",
          n_restarts=0, invocation_id="inv1",
          active_enter_ts_mono_us=T0 - 500_000, active_exit_ts_mono_us=0,
          recv_mono_us=T0, ActiveEnterTimestampMonotonic=T0 - 500_000,
          ActiveExitTimestampMonotonic=0)
    for k in range(10):
        b.probe(k, progress=200 * (k + 1), invocation="inv1")
    b.add(R.RT_BASELINE_WINDOW, T0 + 900_000, mono_us_begin=T0,
          mono_us_end=T0 + 900_000)
    b.add(R.RT_FAULT_INJECT, T0 + 1_000_000, kind="exit",
          mono_us_before_call=T0 + 999_000, mono_us_after_call=T0 + 1_000_000)
    for k in range(10, 13):
        b.probe(k, outcome="conn_refused", progress=None, invocation=None)
    b.add(R.RT_ACTION, T0 + 1_250_000, action_id="a0", action_class="restart",
          policy_delay_us=100_000)
    for k in range(13, N_PROBES):
        b.probe(k, progress=200 * (k - 12), invocation="inv2")
    b.add(R.RT_UNIT_STATE, T0 + 1_300_000, active_state="active",
          result="success", n_restarts=1, invocation_id="inv2",
          active_enter_ts_mono_us=T0 + 1_300_000,
          active_exit_ts_mono_us=T0 + 1_000_000, recv_mono_us=T0 + 1_300_000,
          ActiveEnterTimestampMonotonic=T0 + 1_300_000,
          ActiveExitTimestampMonotonic=T0 + 1_000_000)
    b.add("env_snapshot", T0 + T_TRIAL_US - 1, guest_generation=gen(42.0))
    b.add(R.RT_TRIAL_END, T0 + T_TRIAL_US, disposition="complete",
          reason="synthetic", overhead_us=1_500_000,
          timing=timing(T0 + T_TRIAL_US))
    b.add("prober_stop", T0 + T_TRIAL_US + 50_000, emitter="prober:2")
    b.add(V.RT_GUARD_STOP, T0 + T_TRIAL_US + 1_000_000, trial_id=None,
          emitter="guard:3", tripped=False)
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
    assert f.trial_id == TID          # topish uchun kontekst bor


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
    lost = b.probes[5]["seq"]                         # 6 yo'qoldi
    b.probes[5]["seq"] = lost + 1000    # max_seq dan ham katta
    rep = V.validate_run(b.run())
    f = next(f for f in rep.findings if f.code == "seq_gap")
    assert f.severity == V.SEVERITY_ERROR
    assert f.stream == "prober:2/probe_sample"
    assert lost in f.detail["missing_seq"]
    assert f.detail["max_seq"] == lost + 1000
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
    assert f.trial_id == TID
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
        rows.append(f"{T0 + k * P},ok,{200 * (k + 1)},inv1,{k + 1},{TID}")
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


# ===========================================================================
# DRIVER CHIQISHI UCHUN QO'SHIMCHA INVARIANTLAR
#
# Har test toza (driver-to'liq) run'dan boshlanadi va AYNAN BITTA buzilish
# kiritadi. `clean()` driver nimani yozishi KERAKLIGINI ifodalaydi
# (kontrakt v1.1 §1-§5), shuning uchun u o'zi XATOSIZ o'tishi shart.
# ===========================================================================


def meta_of(b):
    return next(r for r in b.records if r["record_type"] == R.RT_RUN_META)


def recs(b, rt):
    return [r for r in b.records if r["record_type"] == rt]


def find(rep, code):
    return next(f for f in rep.findings if f.code == code)


def sched2():
    """Ikki yacheykali jadval (A / no_action) -- to'liq blok testlari uchun."""
    return make_schedule([Factor("arm", ("A", "no_action")),
                          Factor("pressure_level", ("P1",))], 1, 12345)


def tid_of(sched, arm):
    return next(t.trial_id for t in sched.trials if t.level("arm") == arm)


def test_toza_run_hech_qanday_finding_bermaydi():
    """Barcha yangi tekshiruvlar toza run'da JIM: na xato, na ogohlantirish."""
    rep = V.validate_run(clean().run())
    assert rep.findings == [], [str(f) for f in rep.findings]


# --- 9. envelope (§14.2) ----------------------------------------------------


def test_envelope_maydoni_yoq_bolsa_xato():
    b = clean()
    del recs(b, R.RT_TRIAL_END)[0]["real_us"]
    f = find(V.validate_run(b.run()), "envelope_field_missing")
    assert f.severity == V.SEVERITY_ERROR
    assert f.detail["field"] == "real_us"


def test_boot_id_yoq_record_endi_jimgina_otmaydi():
    """`check_boot_id` boot_id yo'q record'ni TASHLAYDI (§14.6-5 chetlab
    o'tiladi) -- envelope tekshiruvi shu teshikni yopadi."""
    b = clean()
    del recs(b, R.RT_UNIT_STATE)[0]["boot_id"]
    run = b.run()
    assert V.check_boot_id(run) == []              # eski tekshiruv ko'rmaydi
    f = find(V.validate_run(run), "envelope_field_missing")
    assert f.detail["field"] == "boot_id"


def test_stream_record_type_dan_farq_qilsa_xato():
    b = clean()
    recs(b, R.RT_ACTION)[0]["stream"] = "events"
    f = find(V.validate_run(b.run()), "stream_not_record_type")
    assert f.severity == V.SEVERITY_ERROR


def test_umumiy_oqim_seq_bosh_oqim_kaliti_bilan_hisoblanadi():
    """Driver bitta `events` oqimiga hamma turni yozsa va seq'ni UMUMIY
    hisoblasa, `stream` maydoni bo'yicha kalit soxta `seq_gap` bermaydi --
    lekin kontrakt v1.1 §4.2-3 buzilgani baribir XATO."""
    b = clean()
    n = 0
    for r in b.records:
        if r["emitter"] == "driver:1":
            n += 1
            r["stream"] = "events"
            r["seq"] = n
    rep = V.validate_run(b.run())
    assert "seq_gap" not in codes(rep)
    assert "stream_not_record_type" in codes(rep, V.SEVERITY_ERROR)


def test_guard_boshqa_run_id_bilan_yozilsa_xato():
    """guard.py `--run-id` berilmasa yangi uuid oladi (§1: bitta run = bitta
    katalog)."""
    b = clean()
    recs(b, V.RT_GUARD_START)[0]["run_id"] = "boshqa-run"
    f = find(V.validate_run(b.run()), "run_id_mismatch")
    assert f.severity == V.SEVERITY_ERROR
    assert f.detail["emitter"] == "guard:3"


def test_guard_session_id_adhoc_bolsa_xato():
    b = clean()
    for r in b.records:
        if r["emitter"] == "guard:3":
            r["session_id"] = "adhoc"
    assert "session_id_mismatch" in codes(V.validate_run(b.run()),
                                          V.SEVERITY_ERROR)


def test_guard_boshqa_boot_id_bilan_xato():
    """Guard atributsiyasi monotonic vaqt bo'yicha va faqat bitta boot ichida
    haqiqiy (§14.7). `check_boot_id` guard'ni session bo'yicha ajratadi va
    driver bilan solishtirmaydi -- run_meta bilan solishtirish buni yopadi."""
    b = clean()
    for r in b.records:
        if r["emitter"] == "guard:3":
            r["session_id"] = "adhoc"          # eski tekshiruv ko'rmasligi uchun
            r["boot_id"] = "boot-boshqa"
    run = b.run()
    assert V.check_boot_id(run) == []
    f = find(V.validate_run(run), "boot_id_run_meta_mismatch")
    assert f.severity == V.SEVERITY_ERROR


# --- 10. run_meta (§1.1) ----------------------------------------------------


def test_run_meta_maydoni_kaliti_yoq_bolsa_xato():
    b = clean()
    del meta_of(b)["python_version"]
    f = find(V.validate_run(b.run()), "run_meta_field_missing")
    assert f.severity == V.SEVERITY_ERROR
    assert f.detail["field"] == "python_version"


def test_run_meta_none_olchanmadi_halol_va_xato_emas():
    """WSL2: cpufreq sysfs yo'q -> governor/scaling_driver o'lchanmaydi.
    `None` (o'lchanmadi) validatsiya xatosi EMAS; kalit yo'qligi esa xato."""
    b = clean()
    m = meta_of(b)
    assert m["governor"] is None and m["scaling_driver"] is None
    rep = V.validate_run(b.run())
    assert rep.findings == []
    del m["governor"]                       # endi YOZILMAGAN
    assert find(V.validate_run(b.run()), "run_meta_field_missing"
                ).detail["field"] == "governor"


def test_run_meta_identifikatsiya_maydoni_none_bolsa_xato():
    b = clean()
    meta_of(b)["git_commit"] = None
    f = find(V.validate_run(b.run()), "run_meta_field_null")
    assert f.detail["field"] == "git_commit"
    assert f.severity == V.SEVERITY_ERROR


def test_run_meta_rng_seed_butun_son_bolishi_shart():
    b = clean()
    meta_of(b)["rng_seed"] = "12345"
    assert "run_meta_field_invalid" in codes(V.validate_run(b.run()),
                                             V.SEVERITY_ERROR)


def test_t_trial_us_yoq_bolsa_xato():
    b = clean()
    del meta_of(b)["t_trial_us"]
    f = find(V.validate_run(b.run()), "run_meta_field_missing")
    assert f.detail["field"] == "t_trial_us"


def test_t_trial_us_formuladan_farq_qilsa_xato():
    """T_trial = t_pressure_off + w_stab_s + P (kontrakt v1.1 §5.2): jimgina
    konstanta emas, timeline'dan HISOBLANADI."""
    b = clean()
    # total_s ni 'horizon' qilib olish
    meta_of(b)["t_trial_us"] = round(TrialTimeline().total_s * 1_000_000)
    rep = V.validate_run(b.run())
    assert "t_trial_formula_mismatch" in codes(rep, V.SEVERITY_ERROR)
    assert "trial_horizon_mismatch" in codes(rep, V.SEVERITY_ERROR)


def test_run_mode_yoq_bolsa_xato():
    """run_mode noma'lum bo'lsa confirmatory run'ning dirty daraxti faqat
    ogohlantirish bo'lib qolardi (fail-open)."""
    b = clean()
    del meta_of(b)["run_mode"]
    rep = V.validate_run(b.run())
    assert "run_mode_missing" in codes(rep, V.SEVERITY_ERROR)
    assert "run_mode_missing" not in codes(V.validate_run(b.run(),
                                                          run_mode="pilot"))


def test_run_mode_yopiq_enumdan_tashqari_xato():
    b = clean()
    meta_of(b)["run_mode"] = "exploratory"
    assert "run_mode_unknown" in codes(V.validate_run(b.run()),
                                       V.SEVERITY_ERROR)


def test_confirmatory_run_pilot_sifatida_tekshirilmaydi():
    b = clean()
    meta_of(b)["run_mode"] = "confirmatory"
    rep = V.validate_run(b.run(), run_mode="pilot")
    assert "run_mode_downgrade" in codes(rep, V.SEVERITY_ERROR)
    assert "run_mode_downgrade" not in codes(V.validate_run(b.run()))


# --- 10b. units_show: TIRIK dump (01-muhit §4) ---------------------------------


def test_units_show_oldin_va_keyin_tirik_dump_otadi():
    assert V.validate_run(clean().run()).findings == []


def test_units_show_ochgan_unit_dumpi_xato():
    """`systemctl show` o'chgan unit uchun rc=0 va DEFAULT'lar qaytaradi."""
    b = clean()
    d = meta_of(b)["units_show"]["revix-sut.service"]
    d.update(alive_after=False, dump_valid=False)
    rep = V.validate_run(b.run())
    fs = [f for f in rep.findings if f.code == "units_show_dead"]
    assert {f.detail["field"] for f in fs} == {"alive_after", "dump_valid"}
    assert all(f.severity == V.SEVERITY_ERROR for f in fs)


def test_units_show_default_lari_haqiqiyga_oxshasa_ham_xato():
    """dump_valid=True deyilgan, lekin properties `LoadState=not-found`,
    `MemoryMax=infinity` -- ichki ziddiyat."""
    b = clean()
    d = meta_of(b)["units_show"]["revix-sut.service"]
    d["properties"] = {"LoadState": "not-found", "MemoryMax": "infinity"}
    d["load_state"] = "not-found"
    f = [f for f in V.validate_run(b.run()).findings
         if f.code == "units_show_not_loaded"]
    assert {x.detail["field"] for x in f} == {"load_state",
                                              "properties.LoadState"}


def test_units_show_tirikligi_isbotlanmagan_dump_xato():
    """Liveness kalitlari umuman yo'q: fail-closed."""
    b = clean()
    d = meta_of(b)["units_show"]["revix-sut.service"]
    for k in ("alive_before", "alive_after", "dump_valid"):
        del d[k]
    fs = [f for f in V.validate_run(b.run()).findings
          if f.code == "units_show_unverifiable"]
    assert len(fs) == 3


def test_units_show_bosh_bolsa_xato():
    b = clean()
    meta_of(b)["units_show"] = {}
    assert "units_show_empty" in codes(V.validate_run(b.run()),
                                       V.SEVERITY_ERROR)


def test_units_show_royxat_shakli_ham_qabul_qilinadi():
    b = clean()
    meta_of(b)["units_show"] = list(meta_of(b)["units_show"].values())
    assert V.validate_run(b.run()).findings == []


# --- 10c. jadval va digest ---------------------------------------------------


def test_schedule_digest_schedule_py_bilan_mos():
    """validate.py kanonik shakli schedule.Schedule.digest() dan uzoqlashsa
    BU test ushlaydi."""
    for seed in (1, 12345):
        s = make_schedule([Factor("arm", ("A", "no_action")),
                           Factor("pressure_level", ("P0", "P1", "P2"))],
                          3, seed)
        assert V.schedule_digest_of(s.as_dict()) == s.digest()


def test_schedule_matn_shaklida_ham_qabul_qilinadi():
    """Kontrakt: `schedule.to_json()` dan -- matn yoki parse qilingan obyekt."""
    b = clean()
    meta_of(b)["schedule"] = SCHED.to_json()
    assert V.validate_run(b.run()).findings == []


def test_schedule_digest_mos_kelmasa_xato():
    b = clean()
    meta_of(b)["schedule_digest"] = "0" * 64
    f = find(V.validate_run(b.run()), "schedule_digest_mismatch")
    assert f.severity == V.SEVERITY_ERROR
    assert f.detail["recomputed"] == SCHED.digest()


def test_schedule_qolda_ozgartirilsa_xato():
    b = clean()
    meta_of(b)["schedule"]["n_blocks"] = 2
    rep = V.validate_run(b.run())
    assert "schedule_digest_mismatch" in codes(rep, V.SEVERITY_ERROR)
    assert "schedule_design_violation" in codes(rep, V.SEVERITY_ERROR)


def test_rng_seed_jadval_seed_idan_farq_qilsa_xato():
    b = clean()
    meta_of(b)["rng_seed"] = 999
    assert "rng_seed_mismatch" in codes(V.validate_run(b.run()),
                                        V.SEVERITY_ERROR)


def test_schedule_buzuq_tuzilma_xato():
    b = clean()
    meta_of(b)["schedule"] = {"x": 1}
    assert "schedule_malformed" in codes(V.validate_run(b.run()),
                                         V.SEVERITY_ERROR)


def test_schedule_seeddan_tiklanmasa_ogohlantirish():
    """Digest to'g'ri (jadval o'zi izchil), lekin seed'dan boshqacha chiqadi:
    barqarorlikni schedule.py kafolatlaydi -- OGOHLANTIRISH, xato emas."""
    b = clean(sched=sched2(), tid=tid_of(sched2(), "A"))
    s = meta_of(b)["schedule"]
    s["trials"] = list(reversed(s["trials"]))
    for i, t in enumerate(s["trials"]):
        t["position_in_block"] = i      # tartib o'zgardi, dizayn hamon to'liq
    meta_of(b)["schedule_digest"] = V.schedule_digest_of(s)
    rep = V.validate_run(b.run())
    assert "schedule_not_reproducible" in codes(rep, V.SEVERITY_WARNING)
    assert "schedule_digest_mismatch" not in codes(rep)


# --- 11. trial to'plami jadvalga mos (§8.4) ---------------------------------


def test_bosh_run_otmaydi():
    rep = V.validate_run(R.RawRun())
    assert "run_without_trials" in codes(rep, V.SEVERITY_ERROR)
    assert "validator_internal_error" not in codes(rep)
    assert rep.ok is False


def test_jadvalda_yoq_trial_xato():
    b = clean()
    b.add(R.RT_TRIAL_BEGIN, T0 + 50_000_000, trial_id="ghost", arm="A",
          pressure_band="P1", fault_class="clean_crash", position_in_block=0,
          planned_timeline=TrialTimeline().as_dict())
    b.add(R.RT_TRIAL_END, T0 + 51_000_000, trial_id="ghost",
          disposition="censored")
    f = find(V.validate_run(b.run()), "trial_not_in_schedule")
    assert f.detail["trial_ids"] == ["ghost"]


def test_bajarilmagan_trial_va_yacheyka_soni_xato():
    """Ikki yacheykali jadval, faqat bittasi bajarilgan: to'liq blok dizayni
    buzildi va yacheykadagi trial soni dizaynnikiga teng emas."""
    sc = sched2()
    rep = V.validate_run(clean(sched=sc, tid=tid_of(sc, "A")).run())
    f = find(rep, "schedule_trial_missing")
    assert f.detail["trial_ids"] == [tid_of(sc, "no_action")]
    g = find(rep, "cell_count_mismatch")
    assert g.detail["expected_per_cell"] == 1
    assert {"cell": ["no_action", "P1"], "n": 0, "expected": 1} in g.detail["cells"]


def test_trial_arm_jadvaldan_farq_qilsa_xato():
    """Randomizatsiya o'rniga driver tanlovi."""
    b = clean()
    recs(b, R.RT_TRIAL_BEGIN)[0]["arm"] = "no_action"
    f = find(V.validate_run(b.run()), "trial_schedule_mismatch")
    assert f.trial_id == TID
    assert any("arm" in m for m in f.detail["mismatches"])


def test_trial_pozitsiyasi_jadvaldan_farq_qilsa_xato():
    b = clean()
    recs(b, R.RT_TRIAL_BEGIN)[0]["position_in_block"] = 7
    assert "trial_schedule_mismatch" in codes(V.validate_run(b.run()),
                                              V.SEVERITY_ERROR)


# --- 12. trial hodisalari ketma-ketligi (§1.2) ------------------------------


def _drop(b, rt):
    b.records = [r for r in b.records if r["record_type"] != rt]


def test_baseline_window_yoq_bolsa_xato():
    """Yo'q bo'lsa reduce.py R_ref ni JIMGINA fault'dan oldingi probe'lardan
    oladi -- §4.5 ta'rifi o'zgaradi."""
    b = clean()
    _drop(b, R.RT_BASELINE_WINDOW)
    f = find(V.validate_run(b.run()), "trial_event_missing")
    assert f.detail["missing"] == ["baseline_window"]


def test_fault_inject_yoq_bolsa_xato():
    b = clean()
    _drop(b, R.RT_FAULT_INJECT)
    f = find(V.validate_run(b.run()), "trial_event_missing")
    assert f.detail["missing"] == ["fault_inject"]


def test_action_ham_defer_ham_yoq_bolsa_xato():
    b = clean()
    _drop(b, R.RT_ACTION)
    f = find(V.validate_run(b.run()), "trial_event_missing")
    assert f.detail["missing"] == ["action|action_defer"]


def test_no_action_arm_da_action_talab_qilinmaydi():
    """§9.3: `no_action` (Restart=no) -- action ta'rifiga ko'ra yo'q."""
    sc = sched2()
    b = clean(sched=sc, tid=tid_of(sc, "no_action"))
    _drop(b, R.RT_ACTION)
    assert "trial_event_missing" not in codes(V.validate_run(b.run()))


def test_erta_toxtagan_trial_toliq_toplam_talab_qilmaydi():
    """aborted_guard: baseline/fault bo'lmasligi mumkin."""
    b = clean()
    _drop(b, R.RT_BASELINE_WINDOW)
    _drop(b, R.RT_FAULT_INJECT)
    recs(b, R.RT_TRIAL_END)[0]["disposition"] = "aborted_guard"
    assert "trial_event_missing" not in codes(V.validate_run(b.run()))


def test_fault_inject_ikki_marta_xato():
    b = clean()
    extra = dict(recs(b, R.RT_FAULT_INJECT)[0])
    extra["seq"] = 99
    b.records.append(extra)
    assert "trial_event_duplicate" in codes(V.validate_run(b.run()),
                                            V.SEVERITY_ERROR)


def test_hodisa_trial_oynasidan_tashqarida_bolsa_xato():
    """Driver UnitWatcher buferini keyin yozib, yozish vaqti bilan
    belgilasa -- hodisa trial_end'dan keyin chiqadi."""
    b = clean()
    r = recs(b, R.RT_UNIT_STATE)[-1]
    r["mono_us"] = r["recv_mono_us"] = T0 + 90_000_000
    f = find(V.validate_run(b.run()), "trial_event_outside_window")
    assert f.detail["by_record_type"] == {"unit_state": 1}


def test_baseline_fault_dan_keyin_tugasa_xato():
    b = clean()
    recs(b, R.RT_BASELINE_WINDOW)[0]["mono_us_end"] = T0 + 1_500_000
    recs(b, R.RT_BASELINE_WINDOW)[0]["mono_us"] = T0 + 1_500_000
    assert "baseline_after_fault" in codes(V.validate_run(b.run()),
                                           V.SEVERITY_ERROR)


def test_baseline_window_boshi_oxiridan_keyin_bolsa_xato():
    b = clean()
    recs(b, R.RT_BASELINE_WINDOW)[0]["mono_us_begin"] = T0 + 900_000
    assert "baseline_window_invalid" in codes(V.validate_run(b.run()),
                                              V.SEVERITY_ERROR)


def test_action_fault_dan_oldin_bolsa_xato():
    b = clean()
    recs(b, R.RT_ACTION)[0]["mono_us"] = T0 + 500_000
    assert "action_before_fault" in codes(V.validate_run(b.run()),
                                          V.SEVERITY_ERROR)


def test_fault_bracket_buzuq_bolsa_xato():
    b = clean()
    r = recs(b, R.RT_FAULT_INJECT)[0]
    r["mono_us_before_call"], r["mono_us_after_call"] = (
        r["mono_us_after_call"], r["mono_us_before_call"])
    assert "fault_inject_bracket_invalid" in codes(V.validate_run(b.run()),
                                                   V.SEVERITY_ERROR)


def test_env_snapshot_yoq_bolsa_faqat_ogohlantirish():
    b = clean()
    _drop(b, "env_snapshot")
    rep = V.validate_run(b.run())
    assert codes(rep, V.SEVERITY_WARNING) == ["env_snapshot_missing"]
    assert rep.ok is True


def test_trial_qoshimcha_vaqti_yoq_bolsa_ogohlantirish():
    """§1.3-9: o'lchanadi va yoziladi. Hisobot ma'lumoti -- natija
    yaroqliligini to'smaydi, lekin jimgina ham qolmaydi."""
    b = clean()
    del recs(b, R.RT_TRIAL_END)[0]["overhead_us"]
    rep = V.validate_run(b.run())
    assert codes(rep, V.SEVERITY_WARNING) == ["trial_overhead_missing"]
    assert rep.ok is True


def test_trial_qoshimcha_vaqti_manfiy_bolsa_xato():
    b = clean()
    recs(b, R.RT_TRIAL_END)[0]["overhead_us"] = -5
    assert "trial_overhead_invalid" in codes(V.validate_run(b.run()),
                                             V.SEVERITY_ERROR)


def test_trial_davomiyligi_t_trial_dan_farq_qilsa_xato():
    """Censoring nuqtasi (§6.2) qayd etilgan horizon bo'lishi SHART."""
    b = clean()
    recs(b, R.RT_TRIAL_END)[0]["mono_us"] = T0 + 10_000_000
    assert "trial_horizon_mismatch" in codes(V.validate_run(b.run()),
                                             V.SEVERITY_ERROR)


def test_erta_toxtagan_aborted_guard_horizon_xatosi_emas():
    b = clean()
    e = recs(b, R.RT_TRIAL_END)[0]
    e["mono_us"] = T0 + 10_000_000
    e["disposition"] = "aborted_guard"
    assert "trial_horizon_mismatch" not in codes(V.validate_run(b.run()))


# --- 12b. planned_timeline -- TrialTimeline invariantlari ------------------


def _timeline(b, **over):
    pt = recs(b, R.RT_TRIAL_BEGIN)[0]["planned_timeline"]
    pt.update(over)
    return pt


def test_planned_timeline_pressure_cap_buzilsa_xato():
    """hold_s=50 -- oomd 20 s sustained'da foydalanuvchi ilovasini o'ldiradi."""
    b = clean()
    _timeline(b, hold_s=50.0)
    f = find(V.validate_run(b.run()), "planned_timeline_invalid")
    assert "PressureCapExceeded" in f.message
    assert f.detail["n_trials"] == 1


def test_planned_timeline_ozi_ichki_izchil_lekin_muzlatilgan_capdan_yuqori():
    """Driver `hold_cap_s=100` bilan izchil, lekin XAVFLI timeline yozdi:
    cap yozilgan qiymatga emas, MUZLATILGAN konstantaga nisbatan."""
    b = clean()
    big = TrialTimeline(hold_s=50.0, hold_cap_s=100.0,
                        guard_sustain_window_s=100.0).as_dict()
    recs(b, R.RT_TRIAL_BEGIN)[0]["planned_timeline"] = big
    assert "planned_timeline_cap_exceeded" in codes(V.validate_run(b.run()),
                                                    V.SEVERITY_ERROR)


def _self_consistent(b, hold_s, ramp_above=0.0):
    """Driver `hold_cap_s=hold_s` bilan ICHKI izchil timeline yozdi: u o'z
    cap'ini o'zi belgilaydi, shuning uchun `TrialTimeline` buni qabul qiladi
    va faqat validatorning MUZLATILGAN cap'ga nisbatan tekshiruvi ushlaydi."""
    tl = TrialTimeline(hold_s=hold_s, hold_cap_s=hold_s,
                       ramp_above_threshold_s=ramp_above)
    recs(b, R.RT_TRIAL_BEGIN)[0]["planned_timeline"] = tl.as_dict()
    return tl


def test_validator_hold_capni_schedule_dagi_konstantadan_oladi():
    """MEXANIZM testi (`HOLD_CAP_S` orqali, literalsiz): validator cap'ni
    o'zida qayta yozmaydi, `schedule.HOLD_CAP_S` ga bog'liq. Shuning uchun
    cap qaysi qiymatga o'zgarsa ham shu test o'zgarishsiz to'g'ri qoladi:
    `HOLD_CAP_S` o'zi qabul, undan 0.5 s ortig'i rad."""
    import revix.schedule as S
    assert V.HOLD_CAP_S == S.HOLD_CAP_S

    ok = clean()
    _self_consistent(ok, V.HOLD_CAP_S)
    assert "planned_timeline_cap_exceeded" not in codes(V.validate_run(ok.run()))

    bad = clean()
    _self_consistent(bad, V.HOLD_CAP_S + 0.5)
    f = find(V.validate_run(bad.run()), "planned_timeline_cap_exceeded")
    assert f.severity == V.SEVERITY_ERROR
    assert "§9.4-1" in f.message


def test_muzlatilgan_hold_cap_13_soniya_literal():
    """QIYMAT testi (literal `13.0`): §17.5 O3 muzlatgan raqamning o'zi.
    `hold_s = 13.0` qabul, `hold_s = 13.5` rad. Mexanizm testidan farqi:
    u cap qiymati o'zgarsa ham o'tadi, bu esa cap o'zgarsa DARHOL qizaradi --
    ya'ni cap'ni kimdir jimgina qaytarsa (12.0 ga) yoki ko'tarsa, ushlaydi.

    DIQQAT: `agent/holdcap` (`schedule.HOLD_CAP_S = 13.0`) merge qilinmaguncha
    bu test QIZARISHI KUTILADI va to'g'ri."""
    assert V.HOLD_CAP_S == 13.0

    ok = clean()
    _self_consistent(ok, 13.0)
    assert "planned_timeline_cap_exceeded" not in codes(V.validate_run(ok.run()))
    assert "planned_timeline_invalid" not in codes(V.validate_run(ok.run()))

    # (a) driver o'z cap'ini 13.5 qilgan: validator muzlatilgan cap'dan ushlaydi
    bad = clean()
    _self_consistent(bad, 13.5)
    assert "planned_timeline_cap_exceeded" in codes(V.validate_run(bad.run()),
                                                    V.SEVERITY_ERROR)

    # (b) driver default cap'ni qoldirgan: TrialTimeline'ning o'zi rad etadi
    bad2 = clean()
    _timeline(bad2, hold_s=13.5)
    f = find(V.validate_run(bad2.run()), "planned_timeline_invalid")
    assert "PressureCapExceeded" in f.message


def test_ikkinchi_invariant_hold_plyus_ramp_guard_oynasidan_oshsa_xato():
    """§9.4-2 `hold_s + ramp_above_threshold_s <= 15 s` validatorda MAJBURLANADI
    (guard'ning `sustain_max`). `HOLD_CAP_S` orqali ifodalangan: hold cap'da
    turganda ramp'ning yuqori qismi `15 - HOLD_CAP_S` dan oshsa -- xato."""
    g = V.GUARD_SUSTAIN_WINDOW_S
    room = g - V.HOLD_CAP_S

    ok = clean()      # chegarada: hold + ramp == 15 -- hali xato EMAS
    recs(ok, R.RT_TRIAL_BEGIN)[0]["planned_timeline"] = TrialTimeline(
        ramp_above_threshold_s=room).as_dict()
    assert "planned_timeline_cap_exceeded" not in codes(V.validate_run(ok.run()))

    bad = clean()     # driver guard oynasini o'zi 100 s qilib izchil yozdi
    recs(bad, R.RT_TRIAL_BEGIN)[0]["planned_timeline"] = TrialTimeline(
        ramp_above_threshold_s=room + 0.5,
        guard_sustain_window_s=100.0).as_dict()
    f = find(V.validate_run(bad.run()), "planned_timeline_cap_exceeded")
    assert "§9.4-2" in f.message


def test_planned_timeline_maydoni_yoq_bolsa_default_ga_tushmaydi():
    b = clean()
    del _timeline(b)["hold_s"]
    f = find(V.validate_run(b.run()), "planned_timeline_incomplete")
    assert f.detail["missing"] == ["hold_s"]


def test_planned_timeline_hosila_qiymati_mos_kelmasa_xato():
    b = clean()
    _timeline(b, total_s=1.0)
    f = find(V.validate_run(b.run()), "planned_timeline_derived_mismatch")
    assert f.detail["fields"] == ["total_s"]


def test_planned_timeline_son_bolmasa_xato():
    b = clean()
    _timeline(b, hold_s="12")
    assert "planned_timeline_invalid" in codes(V.validate_run(b.run()),
                                               V.SEVERITY_ERROR)


def test_as_dict_da_yoq_t_w_maydonlari_majburiy_emas():
    """`TrialTimeline.as_dict()` t_w_s/t_w_max_s ni BERMAYDI: tabiiy driver
    shu bilan yozadi va u XATO bo'lmasligi kerak."""
    assert "t_w_s" not in TrialTimeline().as_dict()
    assert V.validate_run(clean().run()).findings == []


def test_planned_timeline_yoq_bolsa_xato():
    b = clean()
    del recs(b, R.RT_TRIAL_BEGIN)[0]["planned_timeline"]
    f = find(V.validate_run(b.run()), "record_field_missing")
    assert f.detail["field"] == "planned_timeline"


# --- 13. maydon nomlari (kontrakt v1.1 §4.3, §14.4) ------------------------


def test_pressure_level_pressure_band_ornida_bolsa_xato():
    """reduce.py `pressure_band` o'qiydi: `pressure_level` bo'lsa strata
    jimgina None bo'ladi va birlamchi endpoint (§10.1) yo'qoladi."""
    b = clean()
    r = recs(b, R.RT_TRIAL_BEGIN)[0]
    r["pressure_level"] = r.pop("pressure_band")
    f = find(V.validate_run(b.run()), "record_field_missing")
    assert f.detail["field"] == "pressure_band"
    assert "pressure_level" in f.message


def test_trial_id_payload_emas_envelope_dan_olinadi():
    """trial_id/block_index ENVELOPE maydonlari: validator ularni payload
    ichidan qidirmaydi."""
    assert V.RECORD_FIELD_RULES[R.RT_TRIAL_BEGIN][0] == (
        "arm", "pressure_band", "fault_class", "position_in_block",
        "planned_timeline")
    assert V.validate_run(clean().run()).findings == []


def test_unit_state_systemd_timestamp_yoq_bolsa_xato():
    b = clean()
    del recs(b, R.RT_UNIT_STATE)[0]["ActiveEnterTimestampMonotonic"]
    f = find(V.validate_run(b.run()), "record_field_missing")
    assert f.detail["field"] == "ActiveEnterTimestampMonotonic"


def test_unit_state_snake_case_alias_yoq_bolsa_xato():
    """Xom nomlarni qoldirib snake_case ni qo'shmaslik reduce.py ni D_sd ni
    hisoblay olmaydigan qiladi."""
    b = clean()
    del recs(b, R.RT_UNIT_STATE)[0]["n_restarts"]
    f = find(V.validate_run(b.run()), "record_field_missing")
    assert f.detail["field"] == "n_restarts"


def test_unit_state_recv_mono_us_yoq_bolsa_xato():
    """§14.4: systemd timestamp'lari VA qabul vaqti ALOHIDA -- D-Bus
    yetkazish kechikishi ko'rinishi uchun."""
    b = clean()
    recs(b, R.RT_UNIT_STATE)[0]["recv_mono_us"] = None
    f = find(V.validate_run(b.run()), "record_field_missing")
    assert f.detail["field"] == "recv_mono_us"


def test_unit_state_envelope_mono_us_qabul_vaqti_bolishi_shart():
    b = clean()
    r = recs(b, R.RT_UNIT_STATE)[0]
    r["recv_mono_us"] = r["mono_us"] + 5
    assert "unit_state_mono_not_recv" in codes(V.validate_run(b.run()),
                                               V.SEVERITY_ERROR)


def test_action_policy_delay_us_yoq_bolsa_xato():
    """§6.3: L_dec dan ALOHIDA yozilmasa soxta taqqoslash."""
    b = clean()
    del recs(b, R.RT_ACTION)[0]["policy_delay_us"]
    f = find(V.validate_run(b.run()), "record_field_missing")
    assert f.detail["field"] == "policy_delay_us"


def test_defer_qilingan_actionda_policy_delay_talab_qilinmaydi():
    b = clean()
    r = recs(b, R.RT_ACTION)[0]
    r["deferred"] = True
    r["policy_delay_us"] = None
    for p in b.probes:
        p["invocation_id_seen"] = "inv1" if p["outcome"] == "ok" else None
    for u in recs(b, R.RT_UNIT_STATE):
        u["invocation_id"], u["n_restarts"] = "inv1", 0
    assert "record_field_missing" not in codes(V.validate_run(b.run()))


def _actor_signal(b, **kw):
    payload = {"success": True, "source": "unit_state"}
    payload.update(kw)
    return b.add(R.RT_ACTOR_SIGNAL, T0 + 1_320_000, **payload)


def test_actor_signal_toliq_bolsa_otadi():
    b = clean()
    _actor_signal(b)
    assert V.validate_run(b.run()).findings == []


def test_actor_signal_success_yoq_bolsa_xato():
    """FR-A ning birlamchi operandi: yo'q bo'lsa `bool(None)` = False --
    false recovery jimgina yo'qoladi."""
    b = clean()
    r = _actor_signal(b)
    del r["success"]
    f = find(V.validate_run(b.run()), "record_field_missing")
    assert f.detail["field"] == "success"


def test_actor_signal_success_matn_bolsa_xato():
    """`bool("false")` True: FR-A ni jimgina buzadi."""
    b = clean()
    _actor_signal(b, success="false")
    assert "actor_signal_success_invalid" in codes(V.validate_run(b.run()),
                                                   V.SEVERITY_ERROR)


def test_actor_signal_manbasi_yoq_bolsa_xato():
    b = clean()
    r = _actor_signal(b)
    del r["source"]
    f = find(V.validate_run(b.run()), "record_field_missing")
    assert f.detail["field"] == "source"
    r["actor_signal_source"] = "unit_state"          # muqobil nom ham qabul
    assert V.validate_run(b.run()).findings == []


def test_cgroup_events_oom_kill_yoq_bolsa_xato():
    b = clean()
    b.add(R.RT_CGROUP_EVENTS, T0 + 2_000_000, scope="sut")
    f = find(V.validate_run(b.run()), "record_field_missing")
    assert f.detail["field"] == "oom_kill"


# --- 14. probe -------------------------------------------------------------


def test_probe_outcome_yoq_bolsa_xato():
    """reduce.py yo'q outcome ni JIMGINA 'bad_response' deb oladi."""
    b = clean()
    b.probes[3]["outcome"] = None
    f = find(V.validate_run(b.run()), "probe_outcome_unknown")
    assert f.severity == V.SEVERITY_ERROR


def test_probe_outcome_yopiq_enumdan_tashqari_xato():
    b = clean()
    b.probes[3]["outcome"] = "ok_lekin_sekin"
    assert "probe_outcome_unknown" in codes(V.validate_run(b.run()),
                                            V.SEVERITY_ERROR)


def test_ok_probe_da_progress_oqilmasa_xato():
    """§4.5: throughput bandi o'lchanmaydi -> VR jimgina None."""
    b = clean()
    b.probes[20]["progress"] = None
    f = find(V.validate_run(b.run()), "probe_progress_unreadable")
    assert f.detail["n"] == 1 and f.detail["with_progress_counter"] == 0


def test_progress_counter_bor_lekin_progress_yoq_adapter_qollanmagan():
    b = clean()
    b.probes[20]["progress_counter"] = b.probes[20]["progress"]
    b.probes[20]["progress"] = None
    f = find(V.validate_run(b.run()), "probe_progress_unreadable")
    assert f.detail["with_progress_counter"] == 1
    assert "normalise_probe_row" in f.message


def test_noma_lum_trial_id_li_probe_xato():
    """split_trials bunday probe'ni JIMGINA tashlaydi."""
    b = clean()
    b.probe(500, trial_id="ghost")
    f = find(V.validate_run(b.run()), "probe_trial_unknown")
    assert f.trial_id == "ghost"


def test_trial_ichida_bir_nechta_probe_target_xato():
    b = clean()
    for p in b.probes:
        p["target"] = "sut"
    b.probes[7]["target"] = "bystander"
    f = find(V.validate_run(b.run()), "probe_targets_mixed")
    assert f.detail["targets"] == ["bystander", "sut"]


def test_probe_vaqti_yoq_bolsa_xato_va_validator_yiqilmaydi():
    """Fail-closed: split_trials ReductionError ko'taradi -- istisno xatoga
    aylanadi, validator o'zi yiqilmaydi."""
    b = clean()
    del b.probes[2]["mono_us_send"]
    del b.probes[2]["mono_us"]
    rep = V.validate_run(b.run())
    assert "probe_time_missing" in codes(rep, V.SEVERITY_ERROR)
    assert "validator_internal_error" in codes(rep, V.SEVERITY_ERROR)
    assert rep.ok is False


def test_probe_oxirgi_probe_dan_trial_endgacha_uzilish_xato():
    """Prober trial o'rtasida o'ldi: ketma-ket probe orasida uzilish yo'q,
    `check_probe_gaps` ko'rmaydi -- lekin horizon (§6.2) trial_end'da."""
    b = clean()
    b.probes = b.probes[:300]
    run = b.run()
    assert V.check_probe_gaps(run) == []
    f = find(V.validate_run(run), "probe_coverage_gap")
    assert f.severity == V.SEVERITY_ERROR
    assert f.detail["gaps"][0]["where"] == "trailing"
    assert "censored" in f.message


def test_probe_qoplami_uzilishi_censored_bolsa_ogohlantirish():
    b = clean()
    b.probes = b.probes[:300]
    recs(b, R.RT_TRIAL_END)[0]["disposition"] = "censored"
    rep = V.validate_run(b.run())
    assert "probe_coverage_gap" in codes(rep, V.SEVERITY_WARNING)
    assert rep.ok is True


def test_probe_boshlanishi_baseline_dan_keyin_kech_bolsa_xato():
    b = clean()
    b.probes = b.probes[5:]
    renumber_probes(b)
    f = find(V.validate_run(b.run()), "probe_coverage_gap")
    assert f.detail["gaps"][0]["where"] == "leading"


def test_complete_trialda_bitta_ham_probe_yoq_xato():
    b = clean()
    b.probes = []
    f = find(V.validate_run(b.run()), "trial_without_probes")
    assert f.severity == V.SEVERITY_ERROR


def test_prober_start_yoq_bolsa_csv_run_ga_bogllanmagan():
    """§14.2: CSV oqimlari `<stream>_start` orqali run'ga bog'lanadi."""
    b = clean()
    _drop(b, "prober_start")
    f = find(V.validate_run(b.run()), "prober_start_missing")
    assert f.severity == V.SEVERITY_ERROR


def test_prober_stop_yoq_bolsa_ogohlantirish():
    b = clean()
    _drop(b, "prober_stop")
    rep = V.validate_run(b.run())
    assert codes(rep, V.SEVERITY_WARNING) == ["prober_stop_missing"]
    assert rep.ok is True


def test_har_trial_uchun_alohida_prober_normal_holat():
    """Kontrakt v1.1 §4.5-a: har trial'ga alohida prober jarayoni. Bitta
    uzluksiz prober KUTILMAYDI -- ikkinchi prober'ning ikkinchi
    prober_start/stop juftligi xato emas."""
    b = clean()
    b.add("prober_start", T0 + 50_000_000, emitter="prober:9", trial_id=None)
    b.add("prober_stop", T0 + 51_000_000, emitter="prober:9", trial_id=None)
    assert V.validate_run(b.run()).findings == []


# --- 14b. CSV probe oqimida seq: per-trial prober, per-target oqim ----------


def csv_run(rows):
    """rows: [(target, trial_id, seq)] -- fayldagi tartibda."""
    probes = [{"record_type": R.RT_PROBE, "__source__": "run/probe.csv",
               "__index__": i + 2, "target": t, "trial_id": tid, "seq": s,
               "mono_us_send": T0 + i * P, "outcome": "ok", "progress": i}
              for i, (t, tid, s) in enumerate(rows)]
    return R.RawRun(records=[], probes=probes, sources=["run/probe.csv"])


def test_csv_har_trialda_seq_1_dan_qayta_boshlansa_xato_emas():
    rows = [("sut", "a", s) for s in (1, 2, 3)] + [("sut", "b", s) for s in (1, 2, 3)]
    assert V.check_seq(csv_run(rows)) == []


def test_csv_target_oqimlari_mustaqil_seq_takror_emas():
    """prober.py: seq TARGET bo'yicha. Ikki target bir faylda: ikkalasi 1..n."""
    rows = []
    for s in (1, 2, 3):
        rows += [("sut", "a", s), ("bystander", "a", s)]
    assert V.check_seq(csv_run(rows)) == []


def test_csv_uzluksiz_prober_davomi_xato_emas():
    rows = [("sut", "a", s) for s in (1, 2, 3)] + [("sut", "b", s) for s in (4, 5, 6)]
    assert V.check_seq(csv_run(rows)) == []


def test_csv_trial_ichida_seq_boshligi_xato():
    rows = [("sut", "a", s) for s in (1, 2, 4)]
    f = next(f for f in V.check_seq(csv_run(rows)) if f.code == "seq_gap")
    assert f.detail["missing_seq"] == [3]


def test_csv_yangi_trial_boshidagi_qatorlar_yoqolsa_xato():
    rows = [("sut", "a", s) for s in (1, 2, 3)] + [("sut", "b", s) for s in (3, 4, 5)]
    assert any(f.code == "seq_gap" for f in V.check_seq(csv_run(rows)))


def test_csv_birinchi_guruh_1_dan_boshlanmasa_xato():
    rows = [("sut", "a", s) for s in (2, 3)]
    f = next(f for f in V.check_seq(csv_run(rows)) if f.code == "seq_gap")
    assert f.detail["missing_seq"] == [1]


def test_csv_takroriy_seq_xato():
    rows = [("sut", "a", s) for s in (1, 2, 2, 3)]
    assert any(f.code == "seq_duplicate" for f in V.check_seq(csv_run(rows)))


# --- 15. guard oqimi --------------------------------------------------------


def _guard_event(b, mono, **kw):
    payload = {"reason": "sustained_pressure", "action": "kill_subtree"}
    payload.update(kw)
    return b.add(V.RT_GUARD_EVENT, mono, trial_id=None, emitter="guard:3",
                 **payload)


def test_guard_start_yoq_bolsa_xato():
    """Kontrakt §1.3-2: guard ishga tushmasa run boshlanmaydi."""
    b = clean()
    _drop(b, V.RT_GUARD_START)
    f = find(V.validate_run(b.run()), "guard_start_missing")
    assert f.severity == V.SEVERITY_ERROR


def test_guard_stop_yoq_bolsa_xato():
    b = clean()
    _drop(b, V.RT_GUARD_STOP)
    assert "guard_stop_missing" in codes(V.validate_run(b.run()),
                                         V.SEVERITY_ERROR)


def test_guard_event_da_trial_id_bolsa_xato():
    """`trial_id` yo'qligi TO'G'RI (§14.7); u BOR bo'lsa xato."""
    b = clean()
    r = _guard_event(b, 50)
    r["trial_id"] = TID
    f = find(V.validate_run(b.run()), "guard_event_has_trial_id")
    assert f.severity == V.SEVERITY_ERROR


def test_guard_event_trial_id_siz_bolishi_xato_emas():
    b = clean()
    _guard_event(b, 50)                  # hech bir trial oynasida emas
    rep = V.validate_run(b.run())
    assert "guard_event_has_trial_id" not in codes(rep)
    assert codes(rep, V.SEVERITY_WARNING) == ["guard_event_unattributed"]
    assert rep.ok is True


def test_guard_birinchi_start_bolmasa_xato():
    b = clean()
    recs(b, V.RT_GUARD_START)[0]["mono_us"] = T0 + 10
    assert "guard_not_first" in codes(V.validate_run(b.run()),
                                      V.SEVERITY_ERROR)


def test_guard_oxirgi_stop_bolmasa_xato():
    b = clean()
    recs(b, V.RT_GUARD_STOP)[0]["mono_us"] = T0 + 100
    assert "guard_not_last" in codes(V.validate_run(b.run()),
                                     V.SEVERITY_ERROR)


def test_guard_ishlagan_trial_complete_bolsa_xato():
    """Driver o'z xavfsizlik guard'ining ishlaganini ko'rmagan."""
    b = clean()
    _guard_event(b, T0 + 5_000_000)
    f = find(V.validate_run(b.run()), "guard_event_not_reflected")
    assert f.trial_id == TID


def test_guard_ishlagan_trial_aborted_guard_bolsa_otadi():
    b = clean()
    _guard_event(b, T0 + 5_000_000)
    recs(b, R.RT_TRIAL_END)[0]["disposition"] = "aborted_guard"
    rep = V.validate_run(b.run())
    assert "guard_event_not_reflected" not in codes(rep)
    assert rep.ok is True, [str(f) for f in rep.findings]


# --- 16. harness_error --------------------------------------------------------


def test_harness_error_bor_trial_complete_bolsa_xato():
    """§12: instrument xatosi trial'ni birlamchi analizga kiritmasligi kerak."""
    b = clean()
    b.add(V.RT_HARNESS_ERROR, T0 + 2_000_000, emitter="prober:2",
          where="probe", error="OSError")
    f = find(V.validate_run(b.run()), "harness_error_not_reflected")
    assert f.trial_id == TID


def test_harness_error_disposition_harness_error_bolsa_otadi():
    b = clean()
    b.add(V.RT_HARNESS_ERROR, T0 + 2_000_000, emitter="prober:2", where="probe")
    recs(b, R.RT_TRIAL_END)[0]["disposition"] = "harness_error"
    assert "harness_error_not_reflected" not in codes(V.validate_run(b.run()))


def test_trial_siz_harness_error_ogohlantirish():
    b = clean()
    b.add(V.RT_HARNESS_ERROR, T0 + 2_000_000, emitter="prober:2",
          trial_id=None, where="probe")
    rep = V.validate_run(b.run())
    assert codes(rep, V.SEVERITY_WARNING) == ["harness_error_unattributed"]
    assert rep.ok is True


# --- 17. FAIL-CLOSED ----------------------------------------------------------


def test_tekshiruv_ichidagi_istisno_xato_boladi(monkeypatch):
    def boom(run):
        raise RuntimeError("sinov istisnosi")

    monkeypatch.setattr(V, "check_envelope", boom)
    rep = V.validate_run(clean().run())
    f = find(rep, "validator_internal_error")
    assert f.severity == V.SEVERITY_ERROR
    assert f.detail["check"] == "envelope"
    assert rep.ok is False


def test_istisno_boshqa_tekshiruvlarni_toxtatmaydi(monkeypatch):
    monkeypatch.setattr(V, "check_envelope",
                        lambda run: (_ for _ in ()).throw(ValueError("x")))
    b = clean()
    _drop(b, R.RT_TRIAL_END)
    got = codes(V.validate_run(b.run()), V.SEVERITY_ERROR)
    assert "validator_internal_error" in got
    assert "trial_begin_without_end" in got


def test_cli_oqib_bolmaydigan_kirish_2_qaytaradi(tmp_path, capsys):
    rc = V.main(["--jsonl", str(tmp_path / "yoq.jsonl")])
    assert rc == 2
    assert "O'TMADI" in capsys.readouterr().out


def test_cli_oqib_bolmaydigan_kirish_json(tmp_path, capsys):
    rc = V.main(["--jsonl", str(tmp_path / "yoq.jsonl"), "--json"])
    assert rc == 2
    assert json.loads(capsys.readouterr().out)["ok"] is False


def test_cli_run_dir_yoq_bolsa_otmaydi(tmp_path, capsys):
    rc = V.main(["--run-dir", str(tmp_path / "yoq"), "--json"])
    rep = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert any(f["code"] == "run_dir_missing" for f in rep["findings"])


def test_cli_run_dir_jsonl_bilan_aralashmaydi(tmp_path):
    with pytest.raises(SystemExit):
        V.main(["--run-dir", str(tmp_path), "--jsonl", "x.jsonl"])


# --- 18. guest generation markeri (boot_id bu hostda YETARLI EMAS) -----------


def _snapshots(b):
    return recs(b, "env_snapshot")


def test_marker_run_meta_da_yoq_bolsa_xato():
    b = clean()
    del meta_of(b)["guest_generation"]
    f = find(V.validate_run(b.run()), "run_meta_field_missing")
    assert f.detail["field"] == "guest_generation"


def test_marker_env_snapshot_da_yoq_bolsa_xato():
    b = clean()
    del _snapshots(b)[0]["guest_generation"]
    f = find(V.validate_run(b.run()), "record_field_missing")
    assert (f.detail["record_type"], f.detail["field"]) == (
        "env_snapshot", "guest_generation")


def test_marker_uptime_ozgarishi_restart_emas():
    """Uptime uzluksiz o'sadi: identifikator PID 1 starttime, uptime emas."""
    b = clean()
    assert _snapshots(b)[0]["guest_generation"]["uptime_s"] != \
        _snapshots(b)[1]["guest_generation"]["uptime_s"]
    assert V.validate_run(b.run()).findings == []


def test_guest_restart_boot_id_ozgarmasa_ham_xato():
    """agent/envcheck o'lchagan: WSL restart'ida boot_id O'ZGARMAYDI, lekin
    PID 1 starttime o'zgaradi (CLOCK_MONOTONIC noldan boshlanadi)."""
    b = clean()
    _snapshots(b)[1]["guest_generation"] = gen(3.0, ticks=999)
    run = b.run()
    assert V.check_boot_id(run) == []              # eski invariant JIM
    f = find(V.validate_run(run), "guest_restarted")
    assert f.severity == V.SEVERITY_ERROR
    assert "TAQQOSLANMAYDI" in f.message
    assert f.detail["first_changed_trial"] == TID


def test_marker_skalyar_shaklda_ham_ishlaydi():
    b = clean()
    meta_of(b)["guest_generation"] = "starttime:4242"
    for r in _snapshots(b):
        r["guest_generation"] = "starttime:4242"
    assert V.validate_run(b.run()).findings == []
    _snapshots(b)[1]["guest_generation"] = "starttime:7"
    assert "guest_restarted" in codes(V.validate_run(b.run()), V.SEVERITY_ERROR)


def test_marker_starttime_kaliti_topilmasa_xato():
    b = clean()
    meta_of(b)["guest_generation"] = {"uptime_s": 5.0}
    assert "guest_generation_unreadable" in codes(V.validate_run(b.run()),
                                                  V.SEVERITY_ERROR)


def two_trials(offset=60_000_000):
    """Ikki ketma-ket trial (A va no_action), bitta run, vaqt tartibida."""
    sc = sched2()
    first, second = sorted((tid_of(sc, "A"), tid_of(sc, "no_action")))
    b1, b2 = clean(sc, first), clean(sc, second)
    keys = ("mono_us", "mono_us_send", "recv_mono_us", "mono_us_begin",
            "mono_us_end", "mono_us_before_call", "mono_us_after_call",
            "active_enter_ts_mono_us", "active_exit_ts_mono_us",
            "ActiveEnterTimestampMonotonic", "ActiveExitTimestampMonotonic",
            # Realtime ham BIRGA siljiydi: 60 s keyin yozilgan record'ning
            # devor soati ham 60 s keyin (aks holda bu soat uzilishi).
            "real_us", "real_us_send")

    def shifted(r):
        r = dict(r)
        for k in keys:
            if isinstance(r.get(k), int) and r[k] > 0:
                r[k] += offset
        if isinstance(r.get("timing"), dict):
            r["timing"] = {k: (v + offset if v else v)
                           for k, v in r["timing"].items()}
        return r

    skip = (R.RT_RUN_META, V.RT_GUARD_START)
    merged = Builder(first)
    merged.records = b1.records[:-1]
    merged.records += [shifted(r) for r in b2.records[:-1]
                       if r["record_type"] not in skip]
    merged.records.append(shifted(b2.records[-1]))        # guard_stop
    merged.probes = b1.probes + [shifted(p) for p in b2.probes]
    for lst in (merged.records, merged.probes):
        n = {}
        for r in lst:
            k = (r["emitter"], r["stream"])
            n[k] = n.get(k, 0) + 1
            r["seq"] = n[k]
    return merged, first, second


def test_ikki_ketma_ket_toza_trial_otadi():
    b, _first, _second = two_trials()
    rep = V.validate_run(b.run())
    assert rep.findings == [], [str(f) for f in rep.findings]
    assert rep.n_trials == 2


def test_guest_restart_qaysi_trialga_tushgani_va_nechtasi_saqlangani():
    b, first, second = two_trials()
    for r in _snapshots(b):
        if r["trial_id"] == second:
            r["guest_generation"] = gen(2.0, ticks=77)
    f = find(V.validate_run(b.run()), "guest_restarted")
    assert f.trial_id == second
    assert f.detail["trials_before_restart"] == [first]
    assert f.detail["trials_from_restart"] == [second]


def test_monotonic_vaqt_orqaga_ketsa_xato_markersiz_ham():
    """Zaxira: marker bo'lmasa ham ikkinchi trial birinchisining ichiga
    tushsa (origin reset) ushlanadi."""
    b, _first, _second = two_trials(offset=10_000_000)
    assert "monotonic_origin_regression" in codes(V.validate_run(b.run()),
                                                  V.SEVERITY_ERROR)


# --- 19. --only (driver filtri) ------------------------------------------------


def test_only_filtri_bilan_qisman_run_ogohlantirish_bilan_otadi():
    """Smoke run (`--only A`): jadval TO'LIQ yoziladi, bajarilgan qism `only`
    da. Bu to'liq dizayn emas -- ogohlantirish, lekin xato emas."""
    sc = sched2()
    b = clean(sc, tid_of(sc, "A"))
    meta_of(b)["only"] = ["A"]
    meta_of(b)["n_trials_total"] = 2
    meta_of(b)["n_trials_selected"] = 1
    rep = V.validate_run(b.run())
    assert codes(rep, V.SEVERITY_WARNING) == ["run_filtered"]
    assert rep.ok is True


def test_only_filtrdan_tashqari_trial_bajarilsa_xato():
    sc = sched2()
    b = clean(sc, tid_of(sc, "no_action"))
    meta_of(b)["only"] = ["A"]
    f = find(V.validate_run(b.run()), "trial_not_in_schedule")
    assert tid_of(sc, "no_action") in f.detail["in_schedule_but_filtered"]


def test_n_trials_selected_filtrga_mos_bolishi_shart():
    sc = sched2()
    b = clean(sc, tid_of(sc, "A"))
    meta_of(b)["only"] = ["A"]
    meta_of(b)["n_trials_selected"] = 2
    assert "run_meta_trial_counts_mismatch" in codes(V.validate_run(b.run()),
                                                     V.SEVERITY_ERROR)


def test_run_meta_json_va_events_nusxasi_farq_qilsa_xato(tmp_path):
    """Driver run_meta'ni ikki joyga yozadi: ular farq qilsa xato."""
    b = clean()
    d = tmp_path / "run"
    d.mkdir()
    with open(d / "events.jsonl", "w", encoding="utf-8") as fh:
        for r in b.records:
            fh.write(json.dumps(r) + "\n")
    skip = set(V.ENVELOPE_FIELDS)
    payload = {k: v for k, v in meta_of(b).items() if k not in skip}
    (d / "run_meta.json").write_text(json.dumps(payload), encoding="utf-8")
    (d / "guard.jsonl").write_text("", encoding="utf-8")
    (d / "probe.csv").write_text("mono_us_send,outcome\n", encoding="utf-8")
    assert "run_meta_copies_differ" not in codes(V.validate_run_dir(str(d)))
    payload["rng_seed"] = 1
    (d / "run_meta.json").write_text(json.dumps(payload), encoding="utf-8")
    assert "run_meta_copies_differ" in codes(V.validate_run_dir(str(d)),
                                             V.SEVERITY_ERROR)


def test_trial_end_trial_begindan_oldin_bolsa_xato():
    b = clean()
    recs(b, R.RT_TRIAL_END)[0]["mono_us"] = T0 - 1
    assert "trial_window_invalid" in codes(V.validate_run(b.run()),
                                           V.SEVERITY_ERROR)


def test_units_show_dump_dict_bolmasa_xato():
    b = clean()
    meta_of(b)["units_show"] = {"revix-sut.service": "LoadState=loaded"}
    assert "units_show_malformed" in codes(V.validate_run(b.run()),
                                           V.SEVERITY_ERROR)
    meta_of(b)["units_show"] = "systemctl show matni"
    assert "units_show_malformed" in codes(V.validate_run(b.run()),
                                           V.SEVERITY_ERROR)


def test_only_hech_bir_yacheykaga_mos_kelmasa_xato():
    b = clean()
    meta_of(b)["only"] = ["P9"]
    assert "run_only_invalid" in codes(V.validate_run(b.run()), V.SEVERITY_ERROR)
    meta_of(b)["only"] = "A"             # ro'yxat emas
    assert "run_only_invalid" in codes(V.validate_run(b.run()), V.SEVERITY_ERROR)


# --- 20. reducerga beriladigan ko'rinish: BITTA unit / BITTA target -----------


def _add_bystander_units(b):
    """Xom oqimga bystander unit_state qo'shadi (xom oqimda QONUNIY)."""
    for k, (nrs, inv) in enumerate([(0, "by-inv-1"), (3, "by-inv-2")]):
        b.add(R.RT_UNIT_STATE, T0 + 500_000 + k * 700_000, unit="revix-bystander.service",
              active_state="active", result="success", n_restarts=nrs,
              invocation_id=inv, active_enter_ts_mono_us=T0, active_exit_ts_mono_us=0,
              recv_mono_us=T0 + 500_000 + k * 700_000,
              ActiveEnterTimestampMonotonic=T0, ActiveExitTimestampMonotonic=0)
    for r in recs(b, R.RT_UNIT_STATE):
        r.setdefault("unit", "revix-sut.service")
        r["recv_mono_us"] = r["mono_us"]


def test_unit_state_bir_nechta_unit_reducerga_berilsa_xato():
    """Bystander NRestarts/InvocationID SUT'nikiga aralashadi (§4 band 3-4)."""
    b = clean()
    _add_bystander_units(b)
    f = find(V.validate_run(b.run()), "unit_state_units_mixed")
    assert f.severity == V.SEVERITY_ERROR
    assert f.detail["units"] == ["revix-bystander.service", "revix-sut.service"]


def test_xom_oqimda_ikki_unit_sut_unit_filtri_bilan_otadi():
    """Xom `events.jsonl` ikkala unit'ni saqlashi qonuniy; filtrlangan
    ko'rinish yagona unit. Xom oqimdagi seq filtr tufayli teshilmaydi."""
    b = clean()
    _add_bystander_units(b)
    rep = V.validate_run(b.run(), sut_unit="revix-sut.service")
    assert rep.findings == [], [str(f) for f in rep.findings]


def test_sut_unit_filtri_boshqa_unit_nomi_bilan_sut_unit_state_yoq():
    b = clean()
    _add_bystander_units(b)
    rep = V.validate_run(b.run(), sut_unit="boshqa.service")
    assert find(rep, "sut_unit_state_missing").trial_id == TID


def test_unit_maydoni_yoq_unit_state_filtrda_tashlanadi_va_xato_beradi():
    b = clean()
    rep = V.validate_run(b.run(), sut_unit="revix-sut.service")
    assert "sut_unit_state_missing" in codes(rep, V.SEVERITY_ERROR)


def test_bystander_nrestarts_filtrsiz_vr_tekshiruvini_buzadi():
    """Nega bu xato: aralashgan ko'rinishda bystander NRestarts SUT'ning
    `action_without_invocation_change` tekshiruvini yashiradi."""
    b = clean()
    for p in b.probes:
        p["invocation_id_seen"] = "inv1" if p["outcome"] == "ok" else None
    for r in recs(b, R.RT_UNIT_STATE):
        r["invocation_id"], r["n_restarts"] = "inv1", 0
    _add_bystander_units(b)
    mixed = V.validate_run(b.run())
    assert "action_without_invocation_change" not in codes(mixed)   # yashirilgan
    view = V.validate_run(b.run(), sut_unit="revix-sut.service")
    assert "action_without_invocation_change" in codes(view, V.SEVERITY_ERROR)


def test_probe_target_filtri_bilan_xom_oqimdagi_bystander_otadi():
    b = clean()
    for p in b.probes:
        p["target"] = "sut"
    extra = []
    for p in b.probes[:5]:
        q = dict(p)
        q["target"] = "bystander"
        extra.append(q)
    b.probes += extra
    assert "probe_targets_mixed" in codes(V.validate_run(b.run()),
                                          V.SEVERITY_ERROR)
    rep = V.validate_run(b.run(), sut_target="sut")
    assert "probe_targets_mixed" not in codes(rep)


def test_cli_sut_unit_va_sut_target_bayroqlari(tmp_path, capsys):
    b = clean()
    _add_bystander_units(b)
    p = _write(tmp_path, b)
    assert V.main(["--jsonl", p]) == 1
    capsys.readouterr()
    assert V.main(["--jsonl", p, "--sut-unit", "revix-sut.service"]) == 0


# --- 21. disposition cross-check va ogohlantirish matni -----------------------


def test_driver_va_reducer_disposition_farq_qilsa_ogohlantirish():
    """Raw `complete`, lekin horizon down holatda tugagan -> reducer
    `censored`. Driver avtoritet (§12): xato emas, ko'rinadigan ogohlantirish."""
    b = clean()
    for k in range(N_PROBES - 3, N_PROBES):
        b.probes[k]["outcome"] = "conn_refused"
        b.probes[k]["progress"] = None
        b.probes[k]["invocation_id_seen"] = None
    f = find(V.validate_run(b.run()), "disposition_cross_check")
    assert f.severity == V.SEVERITY_WARNING
    assert f.detail["driver"] == "complete" and f.detail["reducer"] == "censored"


def test_disposition_mos_kelsa_cross_check_jim():
    assert "disposition_cross_check" not in codes(V.validate_run(clean().run()))


def test_overhead_ogohlantirishi_buzilgan_majburiyatni_nomlaydi():
    b = clean()
    del recs(b, R.RT_TRIAL_END)[0]["overhead_us"]
    f = find(V.validate_run(b.run()), "trial_overhead_missing")
    assert f.severity == V.SEVERITY_WARNING
    assert "§1.3 majburiyat 9" in f.message
    assert "o'lchanadi va yoziladi" in f.message


def test_t_trial_tolerantligi_bitta_probe_davri():
    """§6.1 ochiq e'lon qilgan +-P: bitta davrgacha farq xato emas."""
    assert V.T_TRIAL_TOLERANCE_US == R.P_US
    b = clean()
    recs(b, R.RT_TRIAL_END)[0]["mono_us"] = T0 + T_TRIAL_US + P
    assert "trial_horizon_mismatch" not in codes(V.validate_run(b.run()))
    recs(b, R.RT_TRIAL_END)[0]["mono_us"] = T0 + T_TRIAL_US + P + 1
    assert "trial_horizon_mismatch" in codes(V.validate_run(b.run()),
                                             V.SEVERITY_ERROR)


# --- 22. §17.4-5: verifikatsiya oynasi pressure hold ICHIDA (v1.6) -----------
#
# clean(): t_up = T0 + 1.3 s, W_stab = 8 s -> oyna oxiri T0 + 9.3 s;
# T_h = T0 + t_pressure_off (default timeline'dan), T_trial = T0 + T_TRIAL_US.


def _set_timing(b, **kw):
    t = recs(b, R.RT_TRIAL_END)[0]["timing"]
    t.update(kw)
    return t


def test_oyna_hold_ichida_complete_otadi():
    rep = V.validate_run(clean().run())
    assert rep.findings == []


def test_oyna_hold_dan_chiqsa_complete_xato():
    """t_up + W_stab > T_h: §4 kattaligi O'LCHANMAGAN, `complete` bo'lolmaydi."""
    b = clean()
    _set_timing(b, pressure_off_mono_us=T0 + 6_000_000)       # 9.3 s > 6 s
    f = find(V.validate_run(b.run()), "window_outside_hold_complete")
    assert f.severity == V.SEVERITY_ERROR
    assert f.detail["window_containment"] == "past_pressure"
    assert f.detail["slack_to_hold_us"] < 0
    assert f.trial_id == TID


def test_oyna_horizon_dan_chiqsa_complete_xato_Th_siz_ham():
    """(b) T_h ni TALAB QILMAYDI: T_h o'lchanmagan bo'lsa ham aniqlanadi."""
    b = clean()
    _set_timing(b, pressure_off_mono_us=0, horizon_end_mono_us=T0 + 8_000_000)
    recs(b, R.RT_TRIAL_END)[0]["mono_us"] = T0 + 8_000_000
    for r in b.records:                  # trial_end'dan keyingi hodisalarni olib tashlash
        if r["record_type"] in ("env_snapshot",) and r["mono_us"] > T0 + 8_000_000:
            r["mono_us"] = T0 + 7_999_999
    b.probes = [p for p in b.probes if p["mono_us_send"] <= T0 + 8_000_000]
    f = find(V.validate_run(b.run()), "window_outside_hold_complete")
    assert f.detail["window_containment"] == "past_horizon"


def test_oyna_chegarada_teng_hold_ichida_hisoblanadi():
    """§17.4 shartni `<=` bilan yozadi: t_up + W == T_h -- hali XATO EMAS."""
    b = clean()
    _set_timing(b, pressure_off_mono_us=T0 + 1_300_000 + 8_000_000)
    assert "window_outside_hold_complete" not in codes(V.validate_run(b.run()))
    _set_timing(b, pressure_off_mono_us=T0 + 1_300_000 + 8_000_000 - 1)
    assert "window_outside_hold_complete" in codes(V.validate_run(b.run()),
                                                   V.SEVERITY_ERROR)


def test_Th_olchanmagan_bolsa_hukm_toqilmaydi_faqat_ogohlantirish():
    """`pressure_off_mono_us == 0` -- "hech qachon o'rnatilmagan", o'lchangan
    nol EMAS: disposition o'zgarmaydi, lekin soni ko'rinadi."""
    b = clean()
    _set_timing(b, pressure_off_mono_us=0)
    rep = V.validate_run(b.run())
    f = find(rep, "window_containment_not_evaluated")
    assert f.severity == V.SEVERITY_WARNING
    assert f.detail["n"] == 1
    assert "window_outside_hold_complete" not in codes(rep)
    assert rep.ok is True


def test_timing_yoq_bolsa_ham_hukm_toqilmaydi():
    b = clean()
    del recs(b, R.RT_TRIAL_END)[0]["timing"]
    rep = V.validate_run(b.run())
    assert "window_containment_not_evaluated" in codes(rep, V.SEVERITY_WARNING)
    assert rep.ok is True


def test_censored_trial_oyna_tekshiruviga_kirmaydi():
    """§17.4-5 faqat `complete` ga tegishli: reducer `censored` qiladi, xato yo'q."""
    b = clean()
    _set_timing(b, pressure_off_mono_us=T0 + 6_000_000)
    recs(b, R.RT_TRIAL_END)[0]["disposition"] = "censored"
    rep = V.validate_run(b.run())
    assert "window_outside_hold_complete" not in codes(rep)


def test_cross_check_oyna_holatini_reducer_bilan_bir_xil_beradi():
    """Cross-check endi `WindowContainment` ni uzatadi: reducer `censored:
    window_past_pressure` desa, validator ham shuni hosil qiladi (stale
    qo'ng'iroq bo'lsa 'complete:derived' deb haqiqiy farqni yashirardi)."""
    b = clean()
    _set_timing(b, pressure_off_mono_us=T0 + 6_000_000)
    f = find(V.validate_run(b.run()), "disposition_cross_check")
    assert f.detail == {"driver": "complete", "reducer": "censored",
                        "reducer_source": "window_past_pressure"}
    # va aynan reducerning o'zi bilan mos:
    out = R.reduce_run(b.run())
    t = out.trials[0]
    assert (t["disposition"], t["disposition_source"]) == (
        "censored", "window_past_pressure")


def test_oyna_w_stab_run_meta_timeline_dan_olinadi():
    """Kengroq W_stab (60 s) bilan oyna hold'ga (HOLD_CAP_S) sig'maydi."""
    b = clean()
    meta_of(b)["timeline"] = dict(TrialTimeline().as_dict(), w_stab_s=60.0)
    f = find(V.validate_run(b.run()), "window_outside_hold_complete")
    assert f.detail["w_stab_us"] == 60_000_000


def test_timing_pressure_off_trial_oynasidan_tashqarida_xato():
    b = clean()
    _set_timing(b, pressure_off_mono_us=T0 - 5)
    f = find(V.validate_run(b.run()), "trial_timing_invalid")
    assert f.severity == V.SEVERITY_ERROR


def test_timing_horizon_trial_end_mono_us_ga_teng_bolishi_shart():
    b = clean()
    _set_timing(b, horizon_end_mono_us=T0 + 30_000_000)
    assert "trial_timing_invalid" in codes(V.validate_run(b.run()),
                                           V.SEVERITY_ERROR)


def test_timing_nol_hech_qachon_ornatilmagan_xato_emas():
    b = clean()
    _set_timing(b, pressure_off_mono_us=0, horizon_end_mono_us=0)
    assert "trial_timing_invalid" not in codes(V.validate_run(b.run()))


# --- host soat uzilishi (YANGI tekshiruv, 14-smoke-trial-natijalari.md §2) ---

# 07 §7.7 / 13 §0A.1: open-params-cal-01 events.jsonl, A-P2-22 ning ikki
# ketma-ket yozuvi (host uyqusi). O'LCHANGAN raqamlar, o'zgartirilmagan.
SLEEP_MONO = (6_472_198_275, 6_478_211_141)
SLEEP_REAL = (1_791_060_253_618_540, 1_791_102_348_421_289)


def _shift_real_after(b, mono_from, jump_us):
    """`mono_from` dan keyingi har namunaning realtime'iga `jump_us` qo'shadi
    (mono o'zgarmaydi) -- host uyqusining aynan o'zi."""
    for r in b.records + b.probes:
        m = r.get("mono_us_send", r.get("mono_us"))
        if isinstance(m, int) and m >= mono_from:
            if isinstance(r.get("real_us"), int):
                r["real_us"] += jump_us
            if isinstance(r.get("real_us_send"), int):
                r["real_us_send"] += jump_us
    return b


def test_soat_uzilishi_haqiqiy_uyqu_raqamlaridan_xato():
    """Ikki record -- cal-01 dagi AYNAN o'sha mono/real qiymatlar."""
    b = Builder()
    a = b.add("generator_heartbeat", SLEEP_MONO[0], trial_id=None)
    c = b.add("generator_heartbeat", SLEEP_MONO[1], trial_id=None)
    a["real_us"], c["real_us"] = SLEEP_REAL
    out = V.check_host_clock_discontinuity(b.run())
    assert [f.code for f in out] == ["host_clock_discontinuity"]
    f = out[0]
    assert f.severity == V.SEVERITY_ERROR
    j = f.detail["jumps"][0]
    assert j["d_mono_us"] == 6_012_866
    assert j["d_real_us"] == 42_094_802_749
    assert j["jump_us"] == 42_088_789_883          # 11.69 soat


def test_soat_uzilishi_trial_ichida_runni_rad_etadi_va_trialni_korsatadi():
    """Uyqu hold ichida: FAQAT shu finding, boshqa hech narsa o'zgarmaydi."""
    b = _shift_real_after(clean(), T0 + 20_000_000, 42_088_789_883)
    rep = V.validate_run(b.run())
    assert codes(rep) == ["host_clock_discontinuity"], [str(f) for f in rep.findings]
    assert not rep.ok
    f = find(rep, "host_clock_discontinuity")
    assert f.detail["trials_affected"] == [TID]
    assert f.detail["n_jumps"] == 1
    assert f.trial_id == TID


def test_soat_uzilishi_disposition_va_metrikaga_tegmaydi():
    """Yaroqlilik qoidasi, ta'rif EMAS: reducer ko'rinishi bir xil."""
    clean_run = clean().run()
    slept = _shift_real_after(clean(), T0 + 20_000_000, 42_088_789_883).run()
    # Reducer (sintetik fixture) ikkala run uchun AYNAN bir xil chiqish
    # beradi: tekshiruv faqat validatorda, metrika yo'lida emas.
    assert R.reduce_run(clean_run).trials == R.reduce_run(slept).trials


@pytest.mark.parametrize("jump_us,flagged", [
    (386, False),           # o'lchangan qonuniy max (cal-01 psi.csv)
    (999_999, False),
    (1_000_000, False),     # chegara: > 1 s, >= emas
    (1_000_001, True),
    (-5_000_000, True),     # realtime orqaga qadam
])
def test_soat_uzilishi_chegarasi(jump_us, flagged):
    b = _shift_real_after(clean(), T0 + 20_000_000, jump_us)
    got = "host_clock_discontinuity" in codes(V.validate_run(b.run()))
    assert got is flagged


def test_soat_uzilishi_orqaga_sanalgan_record_turlarini_hisoblamaydi():
    """Driver `trial_end` ni horizon mono bilan, real'ni washout'dan keyin
    yozadi (~20 s) -- bu soat uzilishi EMAS. Yozish-lahzali juft
    `mono_us_record_written` + `real_us` ishlatiladi."""
    b = clean()
    te = recs(b, R.RT_TRIAL_END)[0]
    te["real_us"] += 20_000_000                     # washout'dan keyin yozildi
    te["mono_us_record_written"] = te["mono_us"] + 20_000_000
    for rt in ("unit_state", "actor_signal", "env_snapshot"):
        for r in recs(b, rt):
            r["real_us"] += 3_000_000              # kech drenaj
    assert "host_clock_discontinuity" not in codes(V.validate_run(b.run()))
    # ...lekin yozish-lahzali juft ham uzilgan bo'lsa -- tutiladi.
    te["mono_us_record_written"] = te["mono_us"]
    assert "host_clock_discontinuity" in codes(V.validate_run(b.run()))


def test_soat_uzilishi_probe_csv_qatorlaridan_ham_tutiladi():
    """Faqat probe qatorlari (CSV oqimi): uyqu prober ishlayotganda."""
    b = clean()
    b.records = [r for r in b.records if r["record_type"] == R.RT_RUN_META]
    _shift_real_after(b, T0 + 15 * P, 3_000_000)
    out = V.check_host_clock_discontinuity(b.run())
    assert out and out[0].detail["jumps"][0]["before"]["record_type"] == R.RT_PROBE


# --- disposition ustuvorligi: probe uzilishi va guard hodisasi (17 §10) ------
#
# `p1-pilot-002` dan keyin qabul qilingan qaror (docs/architecture/17 §10):
# §14.6(4) va §12 `schedule.DISPOSITION_RULES` tartibi ostida BIRGA o'qiladi.
# Probe uzilishi o'lchangan natija da'vosini (`complete`) bekor qiladi --
# XATO; trial'ni allaqachon chiqaradigan yoki `censored` disposition'da --
# OGOHLANTIRISH. Teskari yo'nalish: guard ishlagan trial faqat
# `aborted_guard` yoki undan oldin turgan `harness_error` bo'lishi mumkin.

# `p1-pilot-002` `b010t005` (no_action/P2) ning HAQIQIY qiymatlari: driver
# yozgan `trial_begin`/`baseline_window`/`trial_end`/`guard_event` va 407 ta
# SUT probe qatorining yuborish vaqtlari va natijalari (`trial_begin` ga
# nisbatan, mikrosekund, aniq). Faqat shu tekshiruvlar o'qiydigan maydonlar
# olingan; manba -- `~/revix-runs/p1-pilot-002` (faqat o'qish), ajratish
# skripti 17 §11 da.
B010T005 = {
    "begin_mono_us": 29628374213,
    "baseline_us": (5000000, 15000000),
    "end_us": 41100000,
    "disposition": "aborted_guard",
    "reason": "guard_fired",
    "matched_rules": ("guard_fired", "bystander_lost_contract", "probe_gap_exceeded", "horizon_ended_down", "measured"),
    "guard_event_us": 27274918,
    "guard_reason": "user_full_rate2s_runaway",
    "probe_outcomes": (  # (outcome, birinchi indeks, oxirgi indeks)
        ("ok", 0, 207),
        ("rt_timeout", 208, 208),
        ("ok", 209, 220),
        ("rt_timeout", 221, 232),
        ("conn_refused", 233, 406),
    ),
    "probe_offsets_us": (  # 407 qator
        65757, 165875, 265884, 365869, 465878, 565893, 665874, 765883, 865865,
        965871, 1065866, 1165885, 1265881, 1365869, 1465871, 1565868, 1665865,
        1765865, 1865877, 1965959, 2065903, 2165884, 2265878, 2365861,
        2465870, 2565870, 2665881, 2765868, 2865859, 2965890, 3065856,
        3165863, 3265889, 3365867, 3465866, 3565861, 3665861, 3765868,
        3865882, 3965866, 4065865, 4165903, 4265868, 4365877, 4465868,
        4565893, 4665872, 4765868, 4865874, 4965871, 5065877, 5743996,
        5744529, 5765859, 5865873, 5965873, 6065874, 6165905, 6265869,
        6365874, 6465920, 6565874, 6665867, 6765853, 6865884, 6965879,
        7065863, 7165873, 7265921, 7365896, 7465862, 7565868, 7665954,
        7765895, 7865886, 7965867, 8065866, 8165899, 8265878, 8365887,
        8465863, 8565868, 8665861, 8765859, 8865861, 8965871, 9065867,
        9165873, 9265859, 9365875, 9465864, 9565875, 9665861, 9765843,
        9865846, 9965854, 10065886, 10165888, 10265902, 10365917, 10465868,
        10565870, 10665874, 10765885, 10865886, 10965879, 11065883, 11165886,
        11265865, 11365865, 11465863, 11565876, 11665876, 11765871, 11865894,
        11965871, 12065882, 12165864, 12265872, 12365874, 12465904, 12565955,
        12665904, 12765880, 12865915, 12965933, 13065911, 13165947, 13265906,
        13365875, 13465872, 13565927, 13665912, 13765888, 13865870, 13965867,
        14065901, 14165877, 14265874, 14365862, 14465878, 14565887, 14665854,
        14765875, 14865882, 14965882, 15065890, 15165870, 15265871, 15365868,
        15465881, 15565896, 15665869, 15765870, 15865898, 15965883, 16065878,
        16165876, 16265875, 16365875, 16465878, 16565900, 16665893, 16765866,
        16865913, 16965886, 17065886, 17165892, 17265876, 17365900, 17465892,
        17565892, 17665986, 17765874, 17865898, 17965875, 18065874, 18165867,
        18265886, 18365877, 18465887, 18565930, 18665877, 18765873, 18865881,
        18965886, 19065873, 19165895, 19265878, 19365879, 19465876, 19565882,
        19665876, 19765870, 19865884, 19965887, 20065863, 20165873, 20265878,
        20365901, 20465884, 20565888, 20665861, 20765866, 20865875, 20965876,
        21065877, 21165867, 21265870, 21365927, 21465876, 21565874, 21665858,
        21765879, 21865877, 21965868, 22065871, 22165872, 22265863, 22365863,
        22465862, 22565874, 22665882, 22765880, 22865843, 22965885, 23066505,
        23165894, 23265875, 23366458, 23465853, 23565874, 23665870, 23765893,
        23865931, 23965888, 24065895, 24165886, 24265881, 24365894, 24465891,
        24565898, 24665888, 24765900, 24865875, 24965881, 25065874, 25165868,
        25265872, 25365918, 25465904, 25565883, 25665874, 25765896, 25865971,
        25965886, 26065878, 26165884, 26265880, 26365874, 26465876, 26565890,
        26665900, 26765906, 26865875, 26965937, 27065857, 27165915, 27265879,
        27365902, 27465953, 27565902, 27665923, 27765893, 27865931, 27965917,
        28065984, 28165870, 28265917, 28365932, 28465943, 28565953, 28665945,
        28765957, 28865969, 28965986, 29065920, 29165940, 29265937, 29365948,
        29465956, 29565948, 29665948, 29765936, 29865953, 29965947, 30065935,
        30166022, 30267819, 30365957, 30465970, 30565920, 30665957, 30765951,
        30865959, 30965967, 31065961, 31165928, 31265946, 31365949, 31465940,
        31565949, 31665994, 31765993, 31865959, 31965946, 32066050, 32165965,
        32265971, 32365937, 32465998, 32566000, 32665939, 32766004, 32865973,
        32965927, 33065982, 33165943, 33265967, 33365913, 33465925, 33565974,
        33665950, 33765935, 33865950, 33965980, 34065965, 34165949, 34265928,
        34365970, 34465957, 34565931, 34665927, 34765950, 34865941, 34965939,
        35065953, 35165934, 35265961, 35365959, 35465947, 35565955, 35665911,
        35765933, 35865961, 35965957, 36065953, 36165943, 36265943, 36365969,
        36465946, 36565954, 36665924, 36765931, 36866034, 36965942, 37065947,
        37165959, 37265955, 37366003, 37465947, 37565945, 37665953, 37765954,
        37865931, 37965968, 38065951, 38165924, 38265953, 38365926, 38465954,
        38565935, 38665936, 38765959, 38865945, 38965961, 39065935, 39165975,
        39265955, 39365947, 39465961, 39565946, 39665945, 39766027, 39865934,
        39965979, 40065946, 40165962, 40265959, 40365939, 40465955, 40565964,
        40665961, 40765924, 40865929, 40965939, 41065953,
    ),
}


def _b010t005_run(disposition=None):
    d = B010T005
    b0 = d["begin_mono_us"]
    outcome = {}
    for name, lo, hi in d["probe_outcomes"]:
        for i in range(lo, hi + 1):
            outcome[i] = name
    probes = [{"record_type": R.RT_PROBE, "stream": R.RT_PROBE,
               "trial_id": "b010t005", "target": "sut", "seq": i + 1,
               "mono_us": b0 + o, "mono_us_send": b0 + o,
               "outcome": outcome[i]}
              for i, o in enumerate(d["probe_offsets_us"])]

    def rec(rt, off, **kw):
        r = {"record_type": rt, "stream": rt, "trial_id": "b010t005",
             "mono_us": b0 + off}
        r.update(kw)
        return r

    lo, hi = d["baseline_us"]
    records = [
        rec(R.RT_TRIAL_BEGIN, 0, arm="no_action", pressure_band="P2"),
        rec(R.RT_BASELINE_WINDOW, hi, mono_us_begin=b0 + lo,
            mono_us_end=b0 + hi),
        rec(R.RT_TRIAL_END, d["end_us"],
            disposition=disposition or d["disposition"], reason=d["reason"],
            matched_rules=list(d["matched_rules"])),
        rec(V.RT_GUARD_EVENT, d["guard_event_us"], trial_id=None,
            reason=d["guard_reason"], action="kill_subtree"),
    ]
    return R.RawRun(records=records, probes=probes, sources=["<b010t005>"])


def test_b010t005_haqiqiy_uzilish_aborted_guard_da_ogohlantirish():
    """17 §2.3: uzilish 5.066 -> 5.744 s (baseline'da), guard 27.275 s da;
    driver uzilishni ko'rgan (`probe_gap_exceeded` `matched_rules` da) va
    disposition'ni undan oldin turgan `guard_fired` bergan."""
    run = _b010t005_run()
    gaps = V.check_probe_gaps(run)
    assert [(f.code, f.severity, f.trial_id) for f in gaps] == [
        ("probe_gap", V.SEVERITY_WARNING, "b010t005")]
    assert [g["gap_us"] for g in gaps[0].detail["gaps"]] == [678_119]
    assert gaps[0].detail["disposition"] == "aborted_guard"
    assert V.check_probe_coverage(run) == []
    assert "guard_event_not_reflected" not in [
        f.code for f in V.check_guard_stream(run)]


def test_b010t005_haqiqiy_recordlar_complete_deb_yozilsa_ikki_xato():
    """Xuddi shu xom record'lar, lekin `complete` da'vosi: uzilish ham, guard
    ham uni bekor qiladi -- ikki yo'nalish bir trial'da."""
    run = _b010t005_run("complete")
    assert [f.severity for f in V.check_probe_gaps(run)] == [V.SEVERITY_ERROR]
    f = next(f for f in V.check_guard_stream(run)
             if f.code == "guard_event_not_reflected")
    assert f.severity == V.SEVERITY_ERROR
    assert f.detail["disposition"] == "complete"


def _b007t001_run(disposition):
    """`p1-pilot-001` `b007t001` ning HAQIQIY record'lari (test_driver bilan
    umumiy fixture); `trial_end` ning disposition'i parametr."""
    path = os.path.join(os.path.dirname(__file__),
                        "data_p1_pilot_001_b007t001.json.gz")
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        d = json.load(fh)
    te = d["recorded_trial_end"]
    end = {"record_type": "trial_end", "trial_id": "b007t001",
           "mono_us": te["mono_us"], "timing": te["timing"],
           "disposition": disposition}
    run = R.RawRun(records=d["records"] + [end],
                   probes=[D.normalise_probe_row(p) for p in d["probe_rows"]])
    return V.reducer_view(run, D.SUT_UNIT, "sut")


def test_b007t001_haqiqiy_complete_uzilish_hali_ham_xato():
    """Tuzatish `complete` ni yumshatmaydi: `p1-pilot-001` ning `b007t001`
    xatosi (492 256 us, 15 §2.2) joyida qoladi."""
    gaps = V.check_probe_gaps(_b007t001_run("complete"))
    assert [(f.code, f.severity, f.trial_id) for f in gaps] == [
        ("probe_gap", V.SEVERITY_ERROR, "b007t001")]
    assert gaps[0].detail["gaps"][0]["gap_us"] == 492_256
    assert "censored" in gaps[0].message


def _with_inner_gap(disp):
    b = clean()
    b.probes = [p for p in b.probes
                if not (T0 + 20 * P <= p["mono_us_send"] <= T0 + 24 * P)]
    renumber_probes(b)
    recs(b, R.RT_TRIAL_END)[0]["disposition"] = disp
    return b


@pytest.mark.parametrize("disp", DISPOSITIONS)
def test_probe_uzilishi_ogirligi_har_disposition_uchun(disp):
    """XATO faqat `complete` da; qolgan BESHTASIDA ogohlantirish, uzilish
    baribir hisobot qilinadi."""
    f = find(V.validate_run(_with_inner_gap(disp).run()), "probe_gap")
    assert f.detail["disposition"] == disp
    assert f.severity == (V.SEVERITY_ERROR if disp == "complete"
                          else V.SEVERITY_WARNING)


@pytest.mark.parametrize("disp", DISPOSITIONS)
def test_probe_qoplami_uzilishi_ogirligi_har_disposition_uchun(disp):
    b = clean()
    b.probes = b.probes[:300]               # prober trial o'rtasida o'ldi
    recs(b, R.RT_TRIAL_END)[0]["disposition"] = disp
    f = find(V.validate_run(b.run()), "probe_coverage_gap")
    assert f.detail["disposition"] == disp
    assert f.severity == (V.SEVERITY_ERROR if disp == "complete"
                          else V.SEVERITY_WARNING)


def test_probe_uzilishi_disposition_yoq_bolsa_xato():
    """Fail-closed: disposition yo'q -- natija da'vosi ham, chiqarish ham
    isbotlanmagan, demak uzilish XATO bo'lib qoladi."""
    b = _with_inner_gap("complete")
    del recs(b, R.RT_TRIAL_END)[0]["disposition"]
    f = find(V.validate_run(b.run()), "probe_gap")
    assert f.severity == V.SEVERITY_ERROR


@pytest.mark.parametrize("disp", ("contaminated", "washout_timeout"))
def test_guard_ishlagan_trial_contaminated_yoki_washout_timeout_bolsa_xato(disp):
    """`guard_fired` tartibda `contaminated` va `washout_timeout` dan OLDIN:
    guard ishlagan trial bu disposition'larni ololmaydi."""
    b = clean()
    _guard_event(b, T0 + 5_000_000)
    recs(b, R.RT_TRIAL_END)[0]["disposition"] = disp
    f = find(V.validate_run(b.run()), "guard_event_not_reflected")
    assert f.severity == V.SEVERITY_ERROR
    assert f.trial_id == TID
    assert f.detail["disposition"] == disp


@pytest.mark.parametrize("disp", DISPOSITIONS)
def test_guard_ishlagan_trial_har_disposition_uchun(disp):
    b = clean()
    _guard_event(b, T0 + 5_000_000)
    recs(b, R.RT_TRIAL_END)[0]["disposition"] = disp
    errs = codes(V.validate_run(b.run()), V.SEVERITY_ERROR)
    assert ("guard_event_not_reflected" in errs) == (
        disp not in ("aborted_guard", "harness_error"))


def test_ustuvorlik_toplamlari_disposition_rules_tartibidan_kelib_chiqadi():
    """Ikki to'plam qo'lda yozilgan, lekin `schedule.DISPOSITION_RULES`
    tartibidan CHIQARILADIGAN to'plam bilan aynan teng bo'lishi shart:
    tartib o'zgarsa bu test validator'ni ham qayta ko'rishga majbur qiladi."""
    names = [n for n, _p, _d in DISPOSITION_RULES]

    def upto(rule):
        return {d for _n, _p, d in DISPOSITION_RULES[:names.index(rule) + 1]}

    assert set(V.GAP_WARNING_DISPOSITIONS) == upto("probe_gap_exceeded")
    assert set(V.GUARD_REFLECTED_DISPOSITIONS) == upto("guard_fired")
    assert set(DISPOSITIONS) - set(V.GAP_WARNING_DISPOSITIONS) == {"complete"}
