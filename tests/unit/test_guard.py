"""guard.py testlari -- chegara mantiqi va FAIL-CLOSED xatti-harakati.

Bu testlar haqiqiy pressure yaratmaydi. Ular guard'ning QARORINI sinaydi,
chunki guard integratsiya testidan oldin qarorlari to'g'ri bo'lishi kerak.
"""
import json

import pytest

from revix.guard import DEFAULTS, Guard
from revix.schema import Emitter, JsonlWriter


class FakePsi:
    """Boshqarilgan PSI qiymatlarini qaytaradi. Har sample'da vaqt oshadi."""

    def __init__(self, samples, t0=0, dt_us=100_000):
        self.samples = list(samples)
        self.t = t0
        self.dt = dt_us
        self.calls = 0

    def sample(self):
        self.calls += 1
        self.t += self.dt
        s = self.samples[min(self.calls - 1, len(self.samples) - 1)]
        if isinstance(s, Exception):
            raise s
        return self.t, s

    def close(self):
        pass


def psi(full_avg10=0.0, some_avg10=0.0, full_total=0):
    return {
        "some": {"avg10": some_avg10, "avg60": 0.0, "avg300": 0.0, "total": 0},
        "full": {"avg10": full_avg10, "avg60": 0.0, "avg300": 0.0, "total": full_total},
    }


def make_guard(tmp_path, thresholds=None):
    lab = tmp_path / "lab"
    lab.mkdir()
    log = tmp_path / "guard.jsonl"
    trip = tmp_path / "trip.json"
    w = JsonlWriter(str(log))
    em = Emitter("guard-test", "r", "s", boot_id="b")
    th = dict(DEFAULTS)
    if thresholds:
        th.update(thresholds)
    g = Guard(str(lab), str(tmp_path / "watch"), w, em, str(trip), th)
    return g, w, log, trip, lab


def records(log):
    return [json.loads(x) for x in log.read_text().splitlines()]


def test_chegaradan_past_trip_qilmaydi(tmp_path):
    g, w, log, trip, lab = make_guard(tmp_path)
    p = FakePsi([psi(full_avg10=1.0, some_avg10=5.0)] * 5)
    for _ in range(5):
        g.check_psi(p, check_avg=True)
    w.close()
    assert not g.tripped
    assert not trip.exists()
    assert [r for r in records(log) if r["record_type"] == "guard_event"] == []


def test_full_avg10_chegarasida_trip(tmp_path):
    g, w, log, trip, lab = make_guard(tmp_path, {"user_full_avg10_max": 15.0})
    g.check_psi(FakePsi([psi(full_avg10=15.0)]), check_avg=True)
    w.close()
    assert g.tripped
    ev = [r for r in records(log) if r["record_type"] == "guard_event"]
    assert len(ev) == 1
    assert ev[0]["reason"] == "user_full_avg10_runaway"
    assert ev[0]["detail"]["avg10"] == 15.0


def test_some_avg10_chegarasida_trip(tmp_path):
    g, w, log, trip, lab = make_guard(tmp_path, {"user_some_avg10_max": 40.0})
    g.check_psi(FakePsi([psi(some_avg10=40.1)]), check_avg=True)
    w.close()
    assert g.tripped
    assert [r["reason"] for r in records(log) if r["record_type"] == "guard_event"] == ["user_some_avg10_runaway"]


def test_avg_tekshirilmasa_avg10_ni_kormaydi(tmp_path):
    """check_avg=False bo'lsa faqat tezlik tekshiriladi -- avgN 2 s kadensda
    yangilanadi, demak 10 Hz da tekshirish ma'nosiz."""
    g, w, log, trip, lab = make_guard(tmp_path)
    g.check_psi(FakePsi([psi(full_avg10=99.0)]), check_avg=False)
    w.close()
    assert not g.tripped


def test_2s_tezlik_chegarasida_trip(tmp_path):
    """total= delta'sidan olingan 2 s tezlik avgN dan tezroq signal."""
    g, w, log, trip, lab = make_guard(tmp_path, {"user_full_rate2s_max": 0.25, "sustain_rate_threshold": 99.0})
    # 100 ms qadamlar; 2 s dan keyin total 600_000 us oshadi -> 0.30 tezlik
    samples = [psi(full_total=30_000 * i) for i in range(25)]
    p = FakePsi(samples, dt_us=100_000)
    for _ in range(25):
        g.check_psi(p, check_avg=False)
    w.close()
    ev = [r for r in records(log) if r["record_type"] == "guard_event"]
    assert ev, "2 s tezlik chegarasi trip qilishi kerak edi"
    assert ev[0]["reason"] == "user_full_rate2s_runaway"
    assert ev[0]["detail"]["rate"] >= 0.25
    assert ev[0]["detail"]["window_us"] >= 2_000_000


def test_2s_dan_qisqa_oynada_tezlik_hisoblanmaydi(tmp_path):
    """Kvantlash qoidasi: <2 s oyna oniy tezlik emas."""
    g, w, log, trip, lab = make_guard(tmp_path, {"user_full_rate2s_max": 0.01, "sustain_rate_threshold": 99.0})
    # faqat 5 x 100 ms = 500 ms tarix
    samples = [psi(full_total=90_000 * i) for i in range(5)]
    p = FakePsi(samples, dt_us=100_000)
    for _ in range(5):
        g.check_psi(p, check_avg=False)
    w.close()
    assert not g.tripped, "2 s oyna to'lmagan holda trip bo'lmasligi kerak"


def test_fail_closed_psi_oqilmasa_trip(tmp_path):
    """PSI o'qilmasa 'hammasi yaxshi' deb hisoblanMAYDI."""
    g, w, log, trip, lab = make_guard(tmp_path)
    g.check_psi(FakePsi([OSError("qurilma yo'q")]), check_avg=True)
    w.close()
    assert g.tripped
    assert [r["reason"] for r in records(log) if r["record_type"] == "guard_event"] == ["psi_read_failed"]


def test_fail_closed_psi_tolik_emas_trip(tmp_path):
    g, w, log, trip, lab = make_guard(tmp_path)
    only_some = {"some": {"avg10": 0.0, "avg60": 0.0, "avg300": 0.0, "total": 0}}
    g.check_psi(FakePsi([only_some]), check_avg=True)
    w.close()
    assert g.tripped
    assert [r["reason"] for r in records(log) if r["record_type"] == "guard_event"] == ["psi_incomplete"]


def test_trip_cgroup_kill_ga_yozadi(tmp_path):
    g, w, log, trip, lab = make_guard(tmp_path)
    g.trip("test", {})
    w.close()
    assert (lab / "cgroup.kill").read_text() == "1", "subtree kill urinilishi kerak"
    ev = [r for r in records(log) if r["record_type"] == "guard_event"][0]
    assert ev["action"] == "kill_subtree"
    assert ev["kill_ok"] is True


def test_trip_fayli_yoziladi(tmp_path):
    g, w, log, trip, lab = make_guard(tmp_path)
    g.trip("sabab_x", {"qiymat": 7})
    w.close()
    d = json.loads(trip.read_text())
    assert d["reason"] == "sabab_x"
    assert d["detail"]["qiymat"] == 7
    assert "mono_us" in d


def test_trip_fayli_birinchi_sababni_saqlaydi(tmp_path):
    """TAHRIRLANDI -- avval bu test `test_trip_idempotent` edi va buzilgan
    xatti-harakatni qulflab turardi:

        assert [e["action"] for e in ev] == ["kill_subtree", "already_tripped"]

    Ya'ni u «ikkinchi trip O'LDIRMAYDI» ni TALAB qilardi.

    O'LCHOV (08-guard-rekalibratsiya.md §17) shu talabni rad etdi:

        guard_event total=3257  kill_subtree=1  already_tripped=3256
        guard.jsonl: 1751702 bayt (1.67 MiB)
        guard_stop: tripped=true iterations=3499 elapsed_s=349.900166559

    «Yagona haqiqiy kill ... Shundan keyin 2, 3 va 4-epizodlarda pressure
    `full avg10` 95.73 ga chiqdi ..., lekin birorta kill bo'lmadi.»
    Mustaqil takrorlash (235 s): `kill_subtree=1  already_tripped=1941`.

    Testdan OLIB TASHLANMADI, QAYTA MAQSAD BERILDI: u endi haqiqatan
    idempotent bo'lishi kerak narsani -- `trip_file` ni -- tekshiradi.
    `trip_file` trial'ning disposition sababi (`PREREGISTRATION.md` §12),
    demak u epizodni BOSHLAGAN sababni saqlashi kerak. Takror kill'ning
    o'zi `test_ikkinchi_trip_yana_oldiradi` da tekshiriladi.
    """
    g, w, log, trip, lab = make_guard(tmp_path)
    g.trip("birinchi", {})
    g.trip("ikkinchi", {})
    w.close()
    assert json.loads(trip.read_text())["reason"] == "birinchi", "trip fayli birinchi sababni saqlaydi"


def test_kill_muvaffaqiyatsiz_bolsa_ham_yiqilmaydi(tmp_path):
    """Guard hech qachon istisnodan yiqilmaydi."""
    log = tmp_path / "g.jsonl"
    w = JsonlWriter(str(log))
    em = Emitter("g", "r", "s", boot_id="b")
    g = Guard(str(tmp_path / "yoq" / "bunday" / "katalog"), str(tmp_path), w, em, None, dict(DEFAULTS))
    g.trip("sabab", {})   # istisno tashlamasligi kerak
    w.close()
    ev = [r for r in records(log) if r["record_type"] == "guard_event"][0]
    assert ev["kill_ok"] is False


def test_host_mem_available_chegarasi(tmp_path):
    """Haqiqiy /proc/meminfo bilan: chegarani juda baland qo'yib trip'ni tekshirish."""
    g, w, log, trip, lab = make_guard(tmp_path, {"host_mem_available_min_kb": 10**12})
    g.check_host()
    w.close()
    reasons = [r["reason"] for r in records(log) if r["record_type"] == "guard_event"]
    assert "host_mem_available" in reasons


def test_host_normal_chegarada_trip_qilmaydi(tmp_path):
    g, w, log, trip, lab = make_guard(tmp_path, {"host_mem_available_min_kb": 1})
    g.check_host()
    w.close()
    assert not g.tripped


def test_cheklangan_cgroup_oom_host_oom_deb_hisoblanmaydi(tmp_path, monkeypatch):
    """revixlab ichidagi cgroup OOM ham global vmstat oom_kill ni oshiradi.
    Guard buni host xavfi deb XATO talqin qilmasligi kerak, aks holda kutilgan
    fault class 3 (leak_oom) har safar noto'g'ri trip keltirardi."""
    from revix import cgroup as cgmod
    from revix import guard as gmod

    lab = tmp_path / "lab"; lab.mkdir()
    (lab / "memory.events").write_text("oom_kill 0\n")
    monkeypatch.setattr(gmod.cg, "vmstat", lambda: {"oom_kill": 0})
    w = JsonlWriter(str(tmp_path / "g.jsonl"))
    g = Guard(str(lab), str(tmp_path), w, Emitter("g", "r", "s", boot_id="b"),
              None, {**DEFAULTS, "host_mem_available_min_kb": 1})

    # Lab ichida 2 ta OOM: global ham 2 ga oshadi, lekin hammasi lab'dan.
    (lab / "memory.events").write_text("oom_kill 2\n")
    monkeypatch.setattr(gmod.cg, "vmstat", lambda: {"oom_kill": 2})
    g.check_host()
    w.close()
    assert not g.tripped, "cheklangan cgroup OOM trip qilmasligi kerak"


def test_lab_tashqarisidagi_oom_trip_qiladi(tmp_path, monkeypatch):
    from revix import guard as gmod

    lab = tmp_path / "lab"; lab.mkdir()
    (lab / "memory.events").write_text("oom_kill 0\n")
    monkeypatch.setattr(gmod.cg, "vmstat", lambda: {"oom_kill": 0})
    w = JsonlWriter(str(tmp_path / "g.jsonl"))
    g = Guard(str(lab), str(tmp_path), w, Emitter("g", "r", "s", boot_id="b"),
              None, {**DEFAULTS, "host_mem_available_min_kb": 1})

    # Global 3 ga oshdi, lekin lab'dan faqat 1 -> 2 tasi TASHQARIDA.
    (lab / "memory.events").write_text("oom_kill 1\n")
    monkeypatch.setattr(gmod.cg, "vmstat", lambda: {"oom_kill": 3})
    g.check_host()
    w.close()
    ev = [json.loads(x) for x in (tmp_path / "g.jsonl").read_text().splitlines()
          if json.loads(x)["record_type"] == "guard_event"]
    assert ev and ev[0]["reason"] == "kernel_oom_kill_outside_lab"
    assert ev[0]["detail"]["outside"] == 2


# --- DAVOMIYLIK himoyasi (asosiy oomd qarshi mexanizm) ----------------------
#
# Kalibratsiya ko'rsatdi: desktop bo'sh turganda user@ PSI ~= lab PSI, demak
# pilotning P2 bandi (60-80%) user@ ni ham shu darajaga ko'taradi. Oniy
# chegarada trip qiluvchi guard har bir P2 trial'ini o'ldirardi. Shuning uchun
# asosiy himoya davomiylik: >=35% pressure 13 s dan uzoq -> trip.


def test_mojallangan_eksperiment_bandi_trip_QILMAYDI(tmp_path):
    """P2 bandi (~70% stall) 12 s ichida trip qilmasligi KERAK -- aks holda
    eksperiment imkonsiz bo'ladi."""
    g, w, log, trip, lab = make_guard(tmp_path)
    # 70% stall, 100 ms qadam, 11 s davomida (pressure shifti 12 s)
    n = 110
    samples = [psi(full_total=70_000 * i) for i in range(n)]
    p = FakePsi(samples, dt_us=100_000)
    for _ in range(n):
        g.check_psi(p, check_avg=True)
    w.close()
    assert not g.tripped, "mo'ljallangan pressure bandi trip qilmasligi kerak"


def test_juda_uzoq_davom_etgan_pressure_trip_qiladi(tmp_path):
    """Qotib qolgan generator: 70% stall 15 s dan uzoq -> trip."""
    g, w, log, trip, lab = make_guard(tmp_path)
    n = 180   # 18 s (sustain chegarasi 15 s)
    samples = [psi(full_total=70_000 * i) for i in range(n)]
    p = FakePsi(samples, dt_us=100_000)
    for _ in range(n):
        g.check_psi(p, check_avg=True)
    w.close()
    ev = [r for r in records(log) if r["record_type"] == "guard_event"]
    assert ev, "15 s dan uzoq pressure trip qilishi kerak"
    assert ev[0]["reason"] == "sustained_pressure"
    assert ev[0]["detail"]["sustained_s"] >= 15.0
    # oomd ning 20 s shartidan oldin trip qilgan bo'lishi kerak
    assert ev[0]["detail"]["sustained_s"] < 20.0, "oomd dan oldin ushlashi kerak"


def test_pressure_tushsa_davomiylik_hisoblagichi_tiklanadi(tmp_path):
    """Ikki qisqa pressure epizodi bitta uzun epizod deb hisoblanmasligi kerak."""
    g, w, log, trip, lab = make_guard(tmp_path)
    total = 0
    samples = []
    # 12 s yuqori (70%) -- 15 s chegarasidan past
    for _ in range(120):
        total += 70_000
        samples.append(psi(full_total=total))
    # 3 s past (0%) -> hisoblagich tiklanadi
    for _ in range(30):
        samples.append(psi(full_total=total))
    # yana 12 s yuqori
    for _ in range(120):
        total += 70_000
        samples.append(psi(full_total=total))
    p = FakePsi(samples, dt_us=100_000)
    for _ in range(len(samples)):
        g.check_psi(p, check_avg=False)
    w.close()
    assert not g.tripped, "tanaffusdan keyin hisoblagich tiklanishi kerak edi"


def test_davomiylik_avgN_emas_total_dan_hisoblanadi(tmp_path):
    """avgN pressure to'xtagandan keyin sekin pasayadi. Agar davomiylik avgN dan
    hisoblansa, pressure tugagandan keyin ham soxta davomiylik yig'ilardi."""
    g, w, log, trip, lab = make_guard(tmp_path)
    samples = []
    total = 0
    # 5 s haqiqiy pressure. 60% tezlik: sustain chegarasidan (35%) yuqori,
    # lekin runaway chegarasidan (90%) past -- shunda faqat davomiylik mantiqi
    # sinaladi.
    for _ in range(50):
        total += 60_000
        samples.append(psi(full_total=total, full_avg10=80.0))
    # 20 s pressure YO'Q, lekin avg10 hali baland (sekin pasayish taqlidi)
    for _ in range(200):
        samples.append(psi(full_total=total, full_avg10=60.0))
    p = FakePsi(samples, dt_us=100_000)
    for _ in range(len(samples)):
        g.check_psi(p, check_avg=False)   # avg tekshirilmaydi, faqat davomiylik
    w.close()
    assert not g.tripped, (
        "avg10 baland bo'lsa ham, total o'smasa davomiylik yig'ilmasligi kerak"
    )


def test_tezlik_oynasi_eng_tor_2s_ni_tanlaydi(tmp_path):
    """Oyna 2..8 s orasida suzsa, tezlik silliqlanib guard sekinlashardi.
    Eng tor >=2 s oyna tanlanishi kerak."""
    g, w, log, trip, lab = make_guard(tmp_path, {"user_full_rate2s_max": 99.0,
                                                 "sustain_rate_threshold": 99.0})
    # 8 s tarix yig'amiz
    samples = [psi(full_total=10_000 * i) for i in range(80)]
    p = FakePsi(samples, dt_us=100_000)
    for _ in range(80):
        g.check_psi(p, check_avg=False)
    # Tarix 3 x 2s = 6 s bilan cheklangan; eng tor oyna ~2.0-2.1 s bo'lishi kerak
    t_now = p.t
    old = None
    for h in reversed(g._hist):
        if t_now - h[0] >= 2_000_000:
            old = h
            break
    assert old is not None
    win = (t_now - old[0]) / 1e6
    assert 2.0 <= win < 2.3, f"oyna eng tor >=2s bo'lishi kerak, {win:.2f}s bo'ldi"
    w.close()


# --- HIMOYA BIR MARTALIK EMAS (dizayn qoidasi 6) ----------------------------
#
# O'lchov (08-guard-rekalibratsiya.md §17): `tripped` hech qachon tiklanmasdi,
# demak `cgroup.kill` bitta guard jarayoniga BIR MARTA tushardi -- 350 s da
# 1 kill va 3256 `already_tripped`. `00-pilot-topologiya.md` §3.1(b) va
# `SECURITY.md` §2(b) bitta guard jarayonini butun 120-trial kampaniyasiga
# qo'yadi, demak birinchi `aborted_guard` trial'idan keyin qolgan 119 trial
# himoyasiz qolardi. `scripts/guard-test.sh` da bu KO'RINMAYDI, chunki u har
# run'da yangi guard jarayoni yaratadi.


def test_ikkinchi_trip_yana_oldiradi(tmp_path):
    """Birinchidan KEYINGI trip ham `cgroup.kill` ga yozishi KERAK."""
    g, w, log, trip, lab = make_guard(tmp_path)

    g.trip("birinchi", {})
    assert (lab / "cgroup.kill").read_text() == "1"

    # Faylni olib tashlaymiz: ikkinchi kill uni QAYTA yaratishi kerak.
    (lab / "cgroup.kill").unlink()
    g.trip("ikkinchi", {})
    w.close()

    assert (lab / "cgroup.kill").exists(), (
        "ikkinchi trip ham subtree'ni o'ldirishi kerak (08 §17)"
    )
    assert (lab / "cgroup.kill").read_text() == "1"
    ev = [r for r in records(log) if r["record_type"] == "guard_event"]
    assert [e["action"] for e in ev] == ["kill_subtree", "kill_subtree"]
    assert all(e["kill_ok"] is True for e in ev)


def test_bir_xil_sabab_bilan_har_trip_oldiradi(tmp_path, monkeypatch):
    """Bir xil sabab takrorlanganda ham kill HAR SAFAR bajariladi.

    Yozuv throttle qilinadi, KILL esa hech qachon: throttling himoyaga tegsa,
    08 §17 ning defekti boshqa shaklda qaytib kelardi.
    """
    from revix import guard as gmod

    kills = []

    def fake_kill(path):
        kills.append(path)
        return True

    monkeypatch.setattr(gmod.cg, "kill_subtree", fake_kill)
    g, w, log, trip, lab = make_guard(tmp_path)
    for _ in range(50):
        g.trip("sustained_pressure", {"rate": 0.9})
    w.close()

    assert len(kills) == 50, f"har trip o'ldirishi kerak, {len(kills)} bo'ldi"
    ev = [r for r in records(log) if r["record_type"] == "guard_event"]
    assert len(ev) == 1, f"50 trip bitta yozuvga siqilishi kerak, {len(ev)} bo'ldi"


def test_takroriy_triplar_cheklanmagan_yozuv_bermaydi(tmp_path):
    """Bitta epizod mingta yozuv yozmasligi kerak.

    O'lchov (08 §17): 350 s da 3256 ortiqcha yozuv, 1.67 MiB; 2.5 soatlik
    kampaniyada ~84 000 yozuv va ~43 MiB bo'lardi.
    """
    g, w, log, trip, lab = make_guard(tmp_path)
    for _ in range(3256):
        g.trip("user_full_rate2s_runaway", {"rate": 0.99})
    w.close()
    ev = [r for r in records(log) if r["record_type"] == "guard_event"]
    assert len(ev) == 1, f"bitta epizod bitta yozuv bermoqda, {len(ev)} bo'ldi"
    assert ev[0]["suppressed_records"] == 0, "birinchi yozuvda bosilgan yo'q"
    # Hodisa JIM QOLMAYDI: bosilgan yozuvlar soni xulosada bor.
    summary = g.trip_summary()
    assert len(summary) == 1
    assert summary[0]["trips"] == 3256
    assert summary[0]["suppressed_records"] == 3255


def test_davriy_xulosa_bosilgan_yozuvlar_sonini_olib_otadi(tmp_path, monkeypatch):
    """Throttle oynasi o'tgach yozuv qaytadi va bosilganlar sonini aytadi."""
    from revix import guard as gmod

    g, w, log, trip, lab = make_guard(tmp_path)
    for _ in range(5):
        g.trip("sustained_pressure", {})
    # Oyna o'tdi deb hisoblaymiz.
    monkeypatch.setattr(gmod, "TRIP_RECORD_INTERVAL_S", 0.0)
    g.trip("sustained_pressure", {})
    w.close()
    ev = [r for r in records(log) if r["record_type"] == "guard_event"]
    assert len(ev) == 2, f"davriy xulosa kutildi, {len(ev)} yozuv bo'ldi"
    assert ev[0]["suppressed_records"] == 0
    assert ev[1]["suppressed_records"] == 4, "bosilgan 4 yozuv olib o'tilishi kerak"
    assert ev[1]["trip_index"] == 6


def test_throttle_boshqa_sababli_tripni_yashirmaydi(tmp_path):
    """Throttle haqiqiy IKKINCHI tripni -- boshqa SABAB bilan -- yashirmasligi
    kerak.

    08 §17: birinchi kill `user_full_rate2s_runaway` bo'ldi, keyingi
    epizodlarda `user_full_avg10_runaway` va `user_some_avg10_runaway` ham
    qayd etildi. Agar throttle sababni hisobga olmasa, aynan shu yangi
    sabablar jim qolardi.
    """
    g, w, log, trip, lab = make_guard(tmp_path)
    for _ in range(100):
        g.trip("user_full_rate2s_runaway", {"rate": 0.99})
    g.trip("user_full_avg10_runaway", {"avg10": 95.73})
    for _ in range(100):
        g.trip("user_full_rate2s_runaway", {"rate": 0.99})
    g.trip("user_some_avg10_runaway", {"avg10": 96.0})
    w.close()

    ev = [r for r in records(log) if r["record_type"] == "guard_event"]
    reasons = [e["reason"] for e in ev]
    assert reasons == ["user_full_rate2s_runaway",
                       "user_full_avg10_runaway",
                       "user_some_avg10_runaway"], (
        f"yangi sabab darhol yozilishi kerak, {reasons} bo'ldi"
    )


def test_kill_natijasi_ozgarsa_yozuv_bosilmaydi(tmp_path, monkeypatch):
    """`kill_ok` True -> False o'zgarishi mustaqil hodisa va yashirilmaydi.

    Aks holda himoyaning buzilishi (cgroup yo'qoldi yoki yozish xato berdi)
    throttle ostida jim qolardi -- bu 08 §17 ning defektining xuddi shunday
    jim shakli bo'lardi.
    """
    from revix import guard as gmod

    ok = [True]
    monkeypatch.setattr(gmod.cg, "kill_subtree", lambda path: ok[0])
    g, w, log, trip, lab = make_guard(tmp_path)
    for _ in range(20):
        g.trip("sustained_pressure", {})
    ok[0] = False
    g.trip("sustained_pressure", {})
    w.close()

    ev = [r for r in records(log) if r["record_type"] == "guard_event"]
    assert [e["kill_ok"] for e in ev] == [True, False], (
        f"kill natijasining o'zgarishi yozilishi kerak, {ev} bo'ldi"
    )


def test_guard_stop_trip_xulosasini_yozadi(tmp_path, monkeypatch):
    """Bosilgan yozuvlar `guard_stop` da yopiladi -- epizod jim qolmaydi."""
    from revix import guard as gmod

    watch = tmp_path / "watch"
    watch.mkdir()
    (watch / "memory.pressure").write_text(
        "some avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
        "full avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
    )
    g, w, log, trip, lab = make_guard(tmp_path, {"host_mem_available_min_kb": 1})
    g.watch_cgroup = str(watch)
    monkeypatch.setattr(gmod.cg, "kill_subtree", lambda path: True)
    for _ in range(10):
        g.trip("sustained_pressure", {})
    g.run(max_seconds=0.0)
    w.close()

    stop = [r for r in records(log) if r["record_type"] == "guard_stop"]
    assert stop, "guard_stop yozuvi bo'lishi kerak"
    summary = stop[-1]["trip_summary"]
    assert any(s["reason"] == "sustained_pressure" and s["trips"] == 10
               and s["suppressed_records"] == 9 for s in summary), summary


# --- FAIL-CLOSED o'zgarmadi (dizayn qoidasi 3) ------------------------------


def test_fail_closed_kutilmagan_istisno_ham_trip(tmp_path, monkeypatch):
    """Asosiy tsiklning har qanday istisnosi trip'ga aylanishi kerak.

    08 §14.1 guard'ning fail-closed xatti-harakatini TASDIQLAGAN; bu test
    takror kill va yozuv throttle qo'shilgandan keyin ham o'zgarmaganini
    qulflaydi.
    """
    from revix import guard as gmod

    watch = tmp_path / "watch"
    watch.mkdir()
    (watch / "memory.pressure").write_text(
        "some avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
        "full avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"
    )
    g, w, log, trip, lab = make_guard(tmp_path, {"host_mem_available_min_kb": 1})
    g.watch_cgroup = str(watch)
    monkeypatch.setattr(gmod.cg, "kill_subtree", lambda path: True)

    def boom(*a, **k):
        raise RuntimeError("kutilmagan")

    monkeypatch.setattr(g, "check_psi", boom)
    rc = g.run(max_seconds=0.25)
    w.close()

    assert g.tripped, "kutilmagan istisno trip qilishi kerak"
    assert rc == 1
    reasons = [r["reason"] for r in records(log) if r["record_type"] == "guard_event"]
    assert "guard_exception" in reasons


def test_fail_closed_kuzatish_ochilmasa_trip(tmp_path):
    """Kuzatish mumkin bo'lmasa eksperiment boshlanmasligi kerak."""
    g, w, log, trip, lab = make_guard(tmp_path)
    rc = g.run(max_seconds=1.0)   # watch_cgroup mavjud emas
    w.close()
    assert rc == 2
    assert g.tripped
    reasons = [r["reason"] for r in records(log) if r["record_type"] == "guard_event"]
    assert reasons == ["watch_open_failed"]
