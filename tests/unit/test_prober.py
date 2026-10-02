"""prober.py testlari -- tasnif qarorlari, detection vaqti va pacing.

Bu testlar haqiqiy `sut.c` ni talab qilmaydi: test ichida yozilgan threadli
`SOCK_SEQPACKET` server protokolning (`docs/architecture/03-sut-protokoli.md`)
prober ko'radigan tomonini o'ynaydi. Sabab -- prober SPEC ga qarshi sinaladi,
parallel yozilayotgan implementatsiyaga qarshi emas.

Eng muhim test: `test_yangi_invocation_bilan_progress_reset_no_progress_EMAS`.
U jimgina downtime o'lchovini buzadigan race'ni yopadi.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time

import pytest

from revix import prober as pb
from revix.prober import PROBE_FIELDS, Prober, Target, parse_probe_reply
from revix.schema import CsvWriter, Emitter, JsonlWriter, mono_us


# --- test SUT'i -------------------------------------------------------------


class FakeSut:
    """Protokolning test dublikati (`sut-protocol/v1`, faqat `PROBE`).

    MUHIM farq: bu fake `progress`ni HAR JAVOBDA oshiradi, chunki testda
    determinizm kerak. Haqiqiy SUT bunday QILMAYDI (protokol §4.5: probe'ga
    javob berish progress'ni oshirmaydi -- aks holda o'lchov o'zini o'lchagan
    bo'lardi). Prober bu farqni ko'ra olmaydi: u faqat ketma-ket javoblardagi
    qiymatlarni taqqoslaydi, hisoblagich qanday o'sganini bilmaydi.
    """

    def __init__(self, path, *, mode="ok", progress=100, step=1,
                 invocation="a1" * 16, pid=4711, listen=True, reply=None):
        self.path = str(path)
        self.mode = mode
        self.progress = progress
        self.step = step
        self.invocation = invocation
        self.pid = pid
        self.reply = reply
        self.requests = 0
        self._held = []          # "silent" rejimda ochiq qoldirilgan ulanishlar
        self._stop = threading.Event()
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.sock.bind(self.path)
        if listen:
            self.sock.listen(16)
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()
        return self

    def restart(self, invocation=None, pid=None):
        """Restart: YANGI invocation, progress 0 dan (protokol §4.4)."""
        self.invocation = invocation or os.urandom(16).hex()
        self.pid = self.pid + 1 if pid is None else pid
        self.progress = 0

    def _serve(self):
        self.sock.settimeout(0.02)
        while not self._stop.is_set():
            try:
                conn, _ = self.sock.accept()
            except (TimeoutError, socket.timeout):
                continue
            except OSError:
                break
            self._handle(conn)

    def _handle(self, conn):
        try:
            conn.settimeout(0.5)
            try:
                conn.recv(4096)
            except OSError:
                return
            self.requests += 1
            if self.mode == "silent":
                # Accept bo'ldi (band a o'tdi), javob YO'Q -> band b buziladi.
                self._held.append(conn)
                return
            if self.mode == "close":
                return
            if self.mode == "raw":
                blob = (self.reply if isinstance(self.reply, bytes)
                        else str(self.reply).encode())
            else:
                self.progress += self.step
                blob = ("OK progress=%d pid=%d invocation=%s rss_kb=5120 mono_us=%d"
                        % (self.progress, self.pid, self.invocation, mono_us())).encode()
            try:
                conn.send(blob)
            except OSError:
                pass
        finally:
            if self.mode != "silent":
                try:
                    conn.close()
                except OSError:
                    pass

    def stop(self):
        self._stop.set()
        if self.thread is not None:
            self.thread.join(timeout=2.0)
        for c in self._held:
            try:
                c.close()
            except OSError:
                pass
        try:
            self.sock.close()
        except OSError:
            pass
        try:
            os.unlink(self.path)
        except OSError:
            pass


# --- §8.2 uchun ALOHIDA PROTSESSDAGI SUT ------------------------------------

_PROC_SUT_SRC = r"""
import os, socket, sys, time
path = sys.argv[1]
s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
s.bind(path)
s.listen(64)
print("ready", file=sys.stderr, flush=True)
progress = 100
inv = "a1" * 16
while True:
    try:
        conn, _ = s.accept()
    except OSError:
        break
    try:
        conn.recv(4096)
        progress += 1
        conn.send(("OK progress=%d pid=%d invocation=%s rss_kb=5120 mono_us=%d"
                   % (progress, os.getpid(), inv,
                      time.clock_gettime_ns(time.CLOCK_MONOTONIC) // 1000)).encode())
    except OSError:
        pass
    try:
        conn.close()
    except OSError:
        pass
"""


class ProcSut:
    """`FakeSut` ning ALOHIDA PROTSESSDAGI varianti -- §8.2 narx o'lchovi uchun.

    NEGA: `Prober.cost_report()` `time.process_time()` va
    `getrusage(RUSAGE_SELF)` ni o'qiydi; ikkisi ham PROTSESS bo'yicha, ya'ni
    protsessning BARCHA thread'larini qo'shadi. `FakeSut` esa prober bilan BIR
    protsessda thread sifatida ishlaydi -- demak uning accept tsikli
    prober'ning o'z narxi deb HISOBOTGA tushardi.

    O'LCHANGAN (2 s, 1 target, 10 Hz, python3.14.7, 3 takror):
      `FakeSut` thread sifatida -> process_time 1.24% / 1.27% / 1.24%,
                                   prober'ning O'Z thread'i 0.57% / 0.59% / 0.56%
      SUT alohida protsessda     -> process_time 0.61% / 0.60% / 0.61%
    Ya'ni eski rig'da §8.2 hisobotidagi raqamning ~55% i TEST SERVER'iga
    tegishli edi va budjet buzilishi SOXTA bo'lgan.

    Ishlab chiqarish topologiyasi aynan shunday: SUT -- `sut.c`, alohida
    protsess (`revixlab.slice`), prober esa `revixmon.slice` da bitta
    thread'li O'Z protsessi (§8.2). Budjetni o'lchaydigan test prober'dan
    boshqa hech narsani o'lchamasligi kerak, aks holda §8.2 ning
    "self-perturbation" bayonoti asbobning o'zi tufayli yolg'on bo'ladi.

    Protokolning prober ko'radigan tomoni `FakeSut` bilan bir xil
    (`sut-protocol/v1`: `PROBE` -> `OK progress=... pid=... invocation=...`),
    va `progress` har javobda oshadi -- `FakeSut` dagi bilan bir xil test
    soddalashtirishi.
    """

    def __init__(self, path):
        self.path = str(path)
        self.proc = None

    def start(self):
        self.proc = subprocess.Popen(
            [sys.executable, "-c", _PROC_SUT_SRC, self.path],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        # "ready" = bind + listen TUGADI. Busiz birinchi probe'lar
        # `conn_refused` bo'lib, narx butunlay boshqa kod yo'lida o'lchanardi.
        line = self.proc.stderr.readline()
        if line.strip() != b"ready":
            self.stop()
            raise AssertionError(f"protsess SUT ishga tushmadi: {line!r}")
        return self

    def stop(self):
        if self.proc is None:
            return
        self.proc.kill()
        self.proc.wait(timeout=5.0)
        try:
            self.proc.stderr.close()
        except OSError:
            pass
        self.proc = None
        try:
            os.unlink(self.path)
        except OSError:
            pass


@pytest.fixture
def sockdir():
    """Qisqa socket katalogi -- AF_UNIX yo'li 108 baytdan oshmasligi kerak."""
    d = tempfile.mkdtemp(prefix="revixp-")
    yield d
    shutil.rmtree(d, ignore_errors=True)


class Rig:
    """Prober + yozuvchilar + fayllarni o'qish."""

    def __init__(self, tmp_path, targets, **kw):
        self.csv_path = tmp_path / "probe.csv"
        self.events_path = tmp_path / "events.jsonl"
        self.csv = CsvWriter(str(self.csv_path), PROBE_FIELDS)
        self.events = JsonlWriter(str(self.events_path))
        em = Emitter("prober-test", "run-1", "sess-1", boot_id="boot-1")
        self.targets = [Target(n, str(s)) for n, s in targets]
        self.prober = Prober(self.targets, self.csv, self.events, em, **kw)

    def probe(self, index=0, n=1, cycle=None):
        out = []
        for i in range(n):
            out.append(self.prober.probe_and_record(self.targets[index],
                                                    cycle if cycle is not None else i + 1))
        return out

    def rows(self):
        self._flush()
        lines = self.csv_path.read_text().splitlines()
        head = lines[0].split(",")
        out = []
        for line in lines[1:]:
            out.append(dict(zip(head, line.split(","))))
        return out

    def header(self):
        self._flush()
        return self.csv_path.read_text().splitlines()[0].split(",")

    def _flush(self):
        # run() chiqishda CSV'ni yopadi -- o'sha holatda flush kerak emas.
        try:
            self.csv.flush()
        except ValueError:
            pass

    def records(self, record_type=None):
        recs = [json.loads(x) for x in self.events_path.read_text().splitlines()]
        if record_type is not None:
            recs = [r for r in recs if r["record_type"] == record_type]
        return recs

    def close(self):
        try:
            self.csv.close()
        except Exception:
            pass
        self.events.close()


@pytest.fixture
def rig(tmp_path):
    made = []

    def build(targets, **kw):
        r = Rig(tmp_path, targets, **kw)
        made.append(r)
        return r

    yield build
    for r in made:
        r.close()


# --- yopiq enum -------------------------------------------------------------


def test_outcome_enum_yopiq():
    assert set(pb.OUTCOMES) == set(pb.OUTCOME_CLAUSE)
    assert pb.OUTCOME_CLAUSE["ok"] is None
    # Har buzilish AYNAN bitta contract bandiga bog'langan (§2).
    for name in pb.OUTCOMES:
        if name != "ok":
            assert pb.OUTCOME_CLAUSE[name] in (pb.CLAUSE_A, pb.CLAUSE_B, pb.CLAUSE_C)


def test_muzlatilgan_parametrlar():
    assert pb.PROBE_HZ == 10.0
    assert pb.T_CONN_S == 0.050
    assert pb.T_RT_S == 0.050
    assert pb.K_F == 3


# --- band (a): ulanish ------------------------------------------------------


def test_normal_probe_ok_va_progress_delta_oshadi(rig, sockdir):
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), step=1, progress=100).start()
    try:
        r = rig([("sut", sut.path)])
        r.probe(n=3)
        rows = r.rows()
    finally:
        sut.stop()

    assert [x["outcome"] for x in rows] == ["ok", "ok", "ok"]
    assert [x["clause_failed"] for x in rows] == ["", "", ""]
    # Birinchi probe'da taqqoslash asosi yo'q -> delta BO'SH (0 emas).
    assert rows[0]["progress_delta"] == ""
    assert [int(x["progress_delta"]) for x in rows[1:]] == [1, 1]
    assert [int(x["progress_counter"]) for x in rows] == [101, 102, 103]
    assert {x["invocation_id_seen"] for x in rows} == {"a1" * 16}
    assert {int(x["sut_pid_seen"]) for x in rows} == {4711}
    assert all(int(x["rtt_us"]) > 0 for x in rows)
    assert all(int(x["conn_us"]) >= 0 for x in rows)
    assert [int(x["seq"]) for x in rows] == [1, 2, 3]
    assert [int(x["restart_seen"]) for x in rows] == [0, 0, 0]
    assert all(int(x["rss_kb_seen"]) == 5120 for x in rows)


def test_bind_qilingan_lekin_listen_qilmagan_socket_conn_refused(rig, sockdir):
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), listen=False)   # start() yo'q
    try:
        r = rig([("sut", sut.path)])
        r.probe()
        rows = r.rows()
    finally:
        sut.stop()
    assert rows[0]["outcome"] == "conn_refused"
    assert rows[0]["clause_failed"] == pb.CLAUSE_A
    assert rows[0]["err_reason"] == "ECONNREFUSED"
    assert rows[0]["mono_us_req"] == ""      # ulanish bo'lmadi
    assert rows[0]["progress_counter"] == ""


def test_socket_fayli_yoq_bolsa_conn_refused(rig, sockdir):
    r = rig([("sut", os.path.join(sockdir, "yoq.sock"))])
    r.probe()
    rows = r.rows()
    assert rows[0]["outcome"] == "conn_refused"
    assert rows[0]["err_reason"] == "ENOENT"
    # mono_us_send har doim bor: u t_detect manbai (§3).
    assert int(rows[0]["mono_us_send"]) > 0


# --- band (b): javob --------------------------------------------------------


def test_javob_bermaydigan_server_rt_timeout(rig, sockdir):
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), mode="silent").start()
    try:
        r = rig([("sut", sut.path)])
        t0 = time.monotonic()
        r.probe()
        elapsed = time.monotonic() - t0
        rows = r.rows()
    finally:
        sut.stop()
    assert rows[0]["outcome"] == "rt_timeout"
    assert rows[0]["clause_failed"] == pb.CLAUSE_B
    # Ulanish bo'ldi (band a o'tdi), javob kelmadi.
    assert int(rows[0]["mono_us_req"]) > 0
    assert rows[0]["mono_us_recv"] == ""
    assert int(rows[0]["rt_us"]) >= 45_000        # ~T_rt = 50 ms
    # T_rt ABSOLUT deadline: send+recv jami 2xT_rt ga cho'zilmaydi.
    assert elapsed < 0.09


@pytest.mark.parametrize("reply,reason", [
    ("GARBAGE", "no_ok_prefix"),
    ("ERR not_ready", "err:not_ready"),
    ("OK pid=1 invocation=ab", "missing:progress"),
    ("OK progress=x pid=1 invocation=ab", "bad_int:progress"),
    ("OK progress=1 pid=1 invocation=zz", "bad_hex:invocation"),
    ("OK progress=1 pid=1", "missing:invocation"),
    ("OK progress=1 pid=1 invocation", "bad_token"),
    (b"\xff\xfe\x01", "not_ascii"),
])
def test_axlat_javob_bad_response(rig, sockdir, reply, reason):
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), mode="raw", reply=reply).start()
    try:
        r = rig([("sut", sut.path)])
        r.probe()
        rows = r.rows()
    finally:
        sut.stop()
    assert rows[0]["outcome"] == "bad_response"
    assert rows[0]["clause_failed"] == pb.CLAUSE_B
    assert rows[0]["err_reason"] == reason


def test_javobsiz_yopilgan_ulanish_bad_response(rig, sockdir):
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), mode="close").start()
    try:
        r = rig([("sut", sut.path)])
        r.probe()
        rows = r.rows()
    finally:
        sut.stop()
    assert rows[0]["outcome"] == "bad_response"
    assert rows[0]["err_reason"] == "eof"


def test_ixtiyoriy_maydonlar_yoq_bolsa_javob_yaroqli(rig, sockdir):
    # rss_kb/mono_us contract bandi (b) ga kirmaydi -- ularni talab qilish
    # parallel yozilgan sut.c ga qarshi soxta failure yaratardi.
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), mode="raw",
                  reply="OK progress=7 pid=9 invocation=" + "b" * 32).start()
    try:
        r = rig([("sut", sut.path)])
        r.probe()
        rows = r.rows()
    finally:
        sut.stop()
    assert rows[0]["outcome"] == "ok"
    assert int(rows[0]["progress_counter"]) == 7
    assert rows[0]["rss_kb_seen"] == ""


# --- band (c): progress -----------------------------------------------------


def test_progress_qotib_qolsa_no_progress(rig, sockdir):
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), step=0, progress=500).start()
    try:
        r = rig([("sut", sut.path)])
        r.probe(n=3)
        rows = r.rows()
    finally:
        sut.stop()
    # Birinchi probe baseline beradi, keyingilari band (c) ni buzadi.
    assert [x["outcome"] for x in rows] == ["ok", "no_progress", "no_progress"]
    assert [x["clause_failed"] for x in rows] == ["", pb.CLAUSE_C, pb.CLAUSE_C]
    assert [x["progress_delta"] for x in rows[1:]] == ["0", "0"]
    assert [int(x["fail_streak"]) for x in rows] == [0, 1, 2]


def test_yangi_invocation_bilan_progress_reset_no_progress_EMAS(rig, sockdir):
    """Shu fayldagi ENG KRITIK test (protokol §8, PREREGISTRATION.md §3).

    Restart progress'ni 0 ga tiklaydi. Agar prober buni `no_progress` deb
    yozsa, restart'dan keyingi birinchi probe soxta buzilish bo'lib, downtime
    o'lchovi jimgina buzilardi.
    """
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), step=1, progress=1000).start()
    try:
        r = rig([("sut", sut.path)])
        r.probe(n=2)
        old_inv = sut.invocation
        sut.restart()                      # yangi invocation, progress 0 dan
        r.probe(n=2)
        rows = r.rows()
    finally:
        sut.stop()

    assert [x["outcome"] for x in rows] == ["ok", "ok", "ok", "ok"]
    assert int(rows[1]["progress_counter"]) == 1002
    # Restart'dan keyingi birinchi probe: progress KAMAYDI, lekin ok.
    assert int(rows[2]["progress_counter"]) == 1
    assert int(rows[2]["restart_seen"]) == 1
    # Delta invocation'lar orasida TAQQOSLANMAYDI -> bo'sh, 0 emas.
    assert rows[2]["progress_delta"] == ""
    assert rows[2]["invocation_id_seen"] != old_inv
    # Yangi invocation ichida delta yana normal ishlaydi.
    assert int(rows[3]["progress_delta"]) == 1
    assert int(rows[3]["restart_seen"]) == 0
    # Va hech qanday buzilish hisoblanmagan.
    assert [int(x["fail_streak"]) for x in rows] == [0, 0, 0, 0]
    assert r.records("detection") == []


def test_invocation_ozgarmasa_progress_kamayishi_no_progress(rig, sockdir):
    """Teskari tomon: yuqoridagi qoida "kamayishni hech qachon belgilamaydi"
    degani EMAS. Bir xil invocation ichida kamayish -- band (c) buzilishi."""
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), step=0, progress=500).start()
    try:
        r = rig([("sut", sut.path)])
        r.probe()
        sut.progress = 400          # invocation O'ZGARMAYDI
        r.probe()
        rows = r.rows()
    finally:
        sut.stop()
    assert rows[1]["outcome"] == "no_progress"
    assert int(rows[1]["progress_delta"]) == -100
    assert int(rows[1]["restart_seen"]) == 0


def test_nol_invocation_da_pid_restart_guvohi(rig, sockdir):
    """systemd'siz ishga tushirishda invocation 32 nol bo'ladi (protokol §3).
    O'sha holatda pid o'zgarishi restart'ning yagona guvohi."""
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), step=1, progress=900,
                  invocation="0" * 32).start()
    try:
        r = rig([("sut", sut.path)])
        r.probe(n=2)
        sut.restart(invocation="0" * 32)    # nol invocation, yangi pid
        r.probe()
        rows = r.rows()
    finally:
        sut.stop()
    assert [x["outcome"] for x in rows] == ["ok", "ok", "ok"]
    assert int(rows[2]["restart_seen"]) == 1
    assert rows[2]["progress_delta"] == ""


# --- detection (F_probe, §3) ------------------------------------------------


def test_uch_ketma_ket_buzilishda_detection_BIRINCHI_probe_vaqti(rig, sockdir):
    r = rig([("sut", os.path.join(sockdir, "yoq.sock"))])
    r.probe(n=2)
    assert r.records("detection") == []          # k_f = 3 dan oldin yo'q
    r.probe(n=1)
    dets = r.records("detection")
    assert len(dets) == 1
    rows = r.rows()
    d = dets[0]
    # t_detect = BIRINCHI buzilgan probe, uchinchisi emas.
    assert d["t_detect_mono_us"] == int(rows[0]["mono_us_send"])
    assert d["t_detect_mono_us"] != int(rows[2]["mono_us_send"])
    assert d["confirm_mono_us"] == int(rows[2]["mono_us_send"])
    assert d["clause_failed"] == pb.CLAUSE_A
    assert d["first_outcome"] == "conn_refused"
    assert d["streak_outcomes"] == ["conn_refused"] * 3
    assert d["k_f"] == 3
    assert d["detector"] == "F_probe"
    assert d["first_fail_seq"] == 1
    assert d["target"] == "sut"
    # Epizodga AYNAN bitta detection: buzilish davom etsa takrorlanmaydi.
    r.probe(n=3)
    assert len(r.records("detection")) == 1


def test_ok_probe_ketma_ketlikni_tiklaydi(rig, sockdir):
    path = os.path.join(sockdir, "sut.sock")
    r = rig([("sut", path)])
    r.probe(n=2)                                 # server yo'q -> 2 buzilish
    sut = FakeSut(path, step=1).start()
    try:
        r.probe(n=1)                             # ok -> hisoblagich tiklanadi
    finally:
        sut.stop()
    assert r.records("detection") == []
    r.probe(n=3)                                 # yangi epizod: 3 buzilish
    dets = r.records("detection")
    assert len(dets) == 1
    rows = r.rows()
    assert [x["outcome"] for x in rows[:3]] == ["conn_refused", "conn_refused", "ok"]
    assert [int(x["fail_streak"]) for x in rows] == [1, 2, 0, 1, 2, 3]
    # t_detect yangi epizodning birinchi buzilgan probe'i (4-qator).
    assert dets[0]["t_detect_mono_us"] == int(rows[3]["mono_us_send"])


def test_contract_qaytganda_epizod_yopilishi_qayd_etiladi(rig, sockdir):
    path = os.path.join(sockdir, "sut.sock")
    r = rig([("sut", path)])
    r.probe(n=3)
    assert len(r.records("detection")) == 1
    sut = FakeSut(path, step=1).start()
    try:
        r.probe(n=1)
    finally:
        sut.stop()
    restored = r.records("contract_restored")
    assert len(restored) == 1
    rows = r.rows()
    assert restored[0]["t_up_mono_us"] == int(rows[3]["mono_us_send"])
    assert restored[0]["failing_probes"] == 3
    assert restored[0]["t_detect_mono_us"] == int(rows[0]["mono_us_send"])


def test_k_f_sozlanadi_va_chetlashish_qayd_etiladi(rig, sockdir):
    r = rig([("sut", os.path.join(sockdir, "yoq.sock"))], k_f=2)
    r.probe(n=2)
    assert len(r.records("detection")) == 1
    assert r.records("detection")[0]["k_f"] == 2
    assert r.prober.frozen_deviation() == {"k_f": 2}


# --- ikki target (bystander = spillover detektori) --------------------------


def test_bystander_mustaqil_kuzatiladi(rig, sockdir):
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), step=1).start()
    try:
        r = rig([("sut", sut.path),
                 ("bystander", os.path.join(sockdir, "yoq.sock"))])
        for _ in range(3):
            r.probe(index=0)
            r.probe(index=1)
        rows = r.rows()
    finally:
        sut.stop()

    sut_rows = [x for x in rows if x["target"] == "sut"]
    by_rows = [x for x in rows if x["target"] == "bystander"]
    assert all(x["outcome"] == "ok" for x in sut_rows)
    assert all(x["outcome"] == "conn_refused" for x in by_rows)
    # seq HAR TARGET uchun alohida oqim -> bo'shliq target bo'yicha aniqlanadi.
    assert [int(x["seq"]) for x in sut_rows] == [1, 2, 3]
    assert [int(x["seq"]) for x in by_rows] == [1, 2, 3]
    dets = r.records("detection")
    assert len(dets) == 1 and dets[0]["target"] == "bystander"


# --- instrumentatsiya xatosi service failure EMAS ---------------------------


def test_instrumentatsiya_xatosi_contract_buzilishi_emas(rig, sockdir, monkeypatch):
    """ENOMEM (pressure ostida real xavf) `conn_refused` deb yozilmaydi.

    Aks holda prober'ning o'z xatosi "xizmat ishdan chiqdi" bo'lib, natijani
    aynan H1 foydasiga siljitardi (PREREGISTRATION.md §8.1).
    """
    r = rig([("sut", os.path.join(sockdir, "yoq.sock"))])

    def boom(*a, **kw):
        raise OSError(pb.errno.ENOMEM, "Cannot allocate memory")

    monkeypatch.setattr(pb.socket, "socket", boom)
    out = r.probe(n=2)
    monkeypatch.undo()

    assert out == [None, None]
    assert r.rows() == []                       # qator YOZILMAYDI
    errs = r.records("harness_error")
    assert len(errs) == 2
    assert "ENOMEM" in errs[0]["error"] or "Cannot allocate" in errs[0]["error"]
    # Ketma-ket buzilish hisoblagichi TEGILMAYDI -> soxta detection yo'q.
    assert r.targets[0].fail_streak == 0
    assert r.records("detection") == []
    assert r.prober.harness_errors == 2


def test_csv_yozish_xatosi_tsiklni_toxtatmaydi(rig, sockdir):
    r = rig([("sut", os.path.join(sockdir, "yoq.sock"))])

    def boom(row):
        raise OSError("disk")

    r.csv.write = boom
    row = r.prober.probe_and_record(r.targets[0], 1)
    assert row is not None and row["outcome"] == "conn_refused"
    assert len(r.records("harness_error")) == 1


# --- pacing -----------------------------------------------------------------


def test_pacing_10hz_va_drift_yigmaydi(rig, sockdir):
    """~2 s da probe soni 10 Hz ga yaqin, xato YIG'ILMAYDI va narx §8.2 budjetida.

    `sleep(P)` ishlatilsa har tsiklda probe narxi qo'shilib, ideal gridga
    nisbatan chetlashish monoton o'sardi. Absolut deadline'da chetlashish
    faqat scheduler jitter'i bo'lib qoladi.

    SUT bu testda ALOHIDA PROTSESSDA (`ProcSut`), `FakeSut` thread'ida emas.
    NEGA (§8.2): shu test probe narxi budjetini ham tekshiradi, va
    `cost_report()` protsess bo'yicha CPU o'qiydi -- bir protsessdagi test
    server'ining accept tsikli prober'ning narxi deb hisoblanardi va budjet
    buzilishi SOXTA chiqardi (raqamlar `ProcSut` docstring'ida). Pacing
    bayonotlari server turiga bog'liq emas; `ProcSut` ustiga u ishlab
    chiqarish topologiyasini (`sut.c` alohida protsess) o'ynaydi.
    """
    sut = ProcSut(os.path.join(sockdir, "sut.sock")).start()
    try:
        r = rig([("sut", sut.path)])
        r.prober.run(max_seconds=2.0)
        rows = r.rows()
    finally:
        sut.stop()

    n = len(rows)
    assert 17 <= n <= 23, f"10 Hz da ~20 probe kutilgan, {n} bo'ldi"
    sends = [int(x["mono_us_send"]) for x in rows]
    gaps = sorted(sends[i + 1] - sends[i] for i in range(n - 1))
    median = gaps[len(gaps) // 2]
    assert 90_000 <= median <= 112_000, f"median davr {median} us"

    # Ideal griddan chetlashish: trend bo'lmasligi kerak.
    dev = [sends[i] - sends[0] - i * 100_000 for i in range(n)]
    assert max(abs(d) for d in dev) < 50_000
    mean_i = (n - 1) / 2.0
    mean_d = sum(dev) / n
    denom = sum((i - mean_i) ** 2 for i in range(n))
    slope = sum((i - mean_i) * (dev[i] - mean_d) for i in range(n)) / denom
    assert abs(slope) < 1500, f"drift trendi {slope:.0f} us/tsikl"

    stop = r.records("prober_stop")
    assert len(stop) == 1
    assert stop[0]["probes"] == n
    # emit_errors > 0 = record jimgina yo'qolgan (masalan payload envelope
    # field'ini bosib o'tdi). Bu hech qachon 0 dan boshqa bo'lmasligi kerak.
    assert stop[0]["emit_errors"] == 0
    assert stop[0]["harness_errors"] == 0
    # §8.2: o'z narxi yadroning 1% dan past bo'lishi kerak. Bu PROBER'ning
    # narxi -- shuning uchun SUT yuqorida alohida protsessda.
    cost = stop[0]["cost"]
    assert cost["core_percent"] is not None
    print(f"\n[probe narxi] core={cost['core_percent']:.3f}% "
          f"cpu={cost['cpu_total_s']:.4f}s probes={cost['probes']} "
          f"cpu/probe={cost['cpu_us_per_probe']:.0f}us")
    assert cost["core_percent"] < 1.0, cost


def test_davr_sigmasa_yoqolgan_tsikllar_qayd_etiladi(rig, sockdir):
    """Probe davrga sig'masa, yo'qolgan tsikl JIMGINA qolmaydi.

    50 Hz (20 ms) da javob bermaydigan target har probe'da ~50 ms oladi, ya'ni
    har tsiklda butun slot yo'qoladi. seq faqat yozilgan qatorlarda oshadi,
    demak yo'qolgan tsikl seq bo'shligi qoldirmaydi -- uni `probe_overrun`
    record'i ko'rinadigan qiladi.
    """
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), mode="silent").start()
    try:
        r = rig([("sut", sut.path)], hz=50.0)
        t0 = time.monotonic()
        r.prober.run(max_seconds=0.5)
        elapsed = time.monotonic() - t0
    finally:
        sut.stop()
    assert elapsed < 1.0
    assert r.prober.overruns > 0
    assert r.prober.skipped_cycles > 0
    ovr = r.records("probe_overrun")
    assert ovr and all(x["skipped_cycles"] >= 1 for x in ovr)
    stop = r.records("prober_stop")[0]
    assert stop["skipped_cycles"] == r.prober.skipped_cycles
    assert stop["emit_errors"] == 0


def test_stop_tsiklni_toxtatadi_va_flush_qiladi(rig, sockdir):
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), step=1).start()
    try:
        r = rig([("sut", sut.path)])
        th = threading.Thread(target=r.prober.run, kwargs={"max_seconds": 10.0})
        th.start()
        time.sleep(0.4)
        r.prober.stop()
        th.join(timeout=3.0)
        assert not th.is_alive()
    finally:
        sut.stop()
    # CSV chiqishda yopilgan -> flush() siz ham o'qiladi.
    lines = r.csv_path.read_text().splitlines()
    assert len(lines) >= 3
    assert len(r.records("prober_stop")) == 1
    assert r.records("prober_start")[0]["k_f"] == 3


# --- CSV sxemasi ------------------------------------------------------------


def test_csv_ustunlari_hujjatlangani_bilan_bir_xil(rig, sockdir):
    r = rig([("sut", os.path.join(sockdir, "yoq.sock"))])
    r.probe()
    assert r.header() == list(PROBE_FIELDS)
    # Vazifa talab qilgan minimal to'plam.
    required = {"mono_us_send", "mono_us_recv", "target", "outcome", "rtt_us",
                "progress_counter", "progress_delta", "invocation_id_seen",
                "sut_pid_seen", "seq", "trial_id"}
    assert required <= set(PROBE_FIELDS)
    # Har ustun modul docstring'ida hujjatlangan.
    doc = pb.__doc__ or ""
    for name in PROBE_FIELDS:
        assert name in doc, f"{name} hujjatlanmagan"


def test_trial_id_ish_vaqtida_ornatiladi(rig, sockdir):
    r = rig([("sut", os.path.join(sockdir, "yoq.sock"))])
    r.probe()
    r.prober.trial_id = "t-0042"
    r.probe(n=2)
    rows = r.rows()
    assert rows[0]["trial_id"] == ""
    assert rows[1]["trial_id"] == "t-0042"
    # Detection record'i ham trial'ga bog'lanadi.
    assert r.records("detection")[0]["trial_id"] == "t-0042"


# --- parser -----------------------------------------------------------------


def test_parse_probe_reply_normal():
    f, why = parse_probe_reply(
        b"OK progress=18452 pid=4711 invocation=" + b"6b" * 16
        + b" rss_kb=5120 mono_us=884213771")
    assert why is None
    assert f["progress"] == 18452 and f["pid"] == 4711
    assert f["rss_kb"] == 5120 and f["mono_us"] == 884213771


def test_parse_probe_reply_satr_oxiri_bilan_ham_ishlaydi():
    f, why = parse_probe_reply(b"OK progress=1 pid=2 invocation=ff\n")
    assert why is None and f["progress"] == 1


def test_parse_probe_reply_bosh_xabar_eof():
    assert parse_probe_reply(b"") == (None, "eof")


def test_parse_probe_reply_notanish_maydon_yaroqli():
    # Protokol maydon QO'SHISHI mumkin (schema.py: field qo'shiladi, qayta
    # ishlatilmaydi) -- notanish maydon javobni yaroqsiz qilmaydi.
    f, why = parse_probe_reply(b"OK progress=1 pid=2 invocation=ff kelajak=7")
    assert why is None and f["progress"] == 1


def test_parse_targets_format():
    ts = pb.parse_targets(["sut=/a.sock", "bystander=/b.sock"])
    assert [t.name for t in ts] == ["sut", "bystander"]
    assert [t.socket_path for t in ts] == ["/a.sock", "/b.sock"]
    with pytest.raises(ValueError):
        pb.parse_targets(["sut"])
    with pytest.raises(ValueError):
        pb.parse_targets(["sut=/a.sock", "sut=/b.sock"])


def test_cost_report_yadro_ulushini_beradi(rig, sockdir):
    r = rig([("sut", os.path.join(sockdir, "yoq.sock"))])
    r.probe(n=2)
    time.sleep(0.05)
    c = r.prober.cost_report()
    assert c["probes"] == 2
    assert c["elapsed_s"] > 0
    assert c["core_percent"] is not None and c["core_percent"] >= 0
    assert c["budget_percent"] == 1.0
    assert c["budget_exceeded"] in (True, False)


# --- CLI --------------------------------------------------------------------


def test_main_max_seconds_bilan_ishlaydi(tmp_path, sockdir, capsys):
    sut = FakeSut(os.path.join(sockdir, "sut.sock"), step=1).start()
    try:
        rc = pb.main([
            "--target", f"sut={sut.path}",
            "--target", f"bystander={os.path.join(sockdir, 'yoq.sock')}",
            "--csv", str(tmp_path / "p.csv"),
            "--events", str(tmp_path / "e.jsonl"),
            "--max-seconds", "0.35",
            "--report-cost",
        ])
    finally:
        sut.stop()
    assert rc == 0
    err = capsys.readouterr().err
    assert "[prober] narx:" in err
    lines = (tmp_path / "p.csv").read_text().splitlines()
    assert lines[0] == ",".join(PROBE_FIELDS)
    assert len(lines) >= 3
    recs = [json.loads(x) for x in (tmp_path / "e.jsonl").read_text().splitlines()]
    types = {x["record_type"] for x in recs}
    assert {"prober_start", "prober_stop", "detection"} <= types
    stop = [x for x in recs if x["record_type"] == "prober_stop"][0]
    assert stop["emit_errors"] == 0 and stop["harness_errors"] == 0
    assert stop["outcome_counts"]["bystander:conn_refused"] >= 3
    # Detection bystander uchun: spillover detektori jim qolmaydi.
    det = [x for x in recs if x["record_type"] == "detection"]
    assert [x["target"] for x in det] == ["bystander"]


def test_bystander_yoq_bolsa_ogohlantiradi(tmp_path, sockdir, capsys):
    pb.main([
        "--target", f"sut={os.path.join(sockdir, 'yoq.sock')}",
        "--csv", str(tmp_path / "p.csv"),
        "--events", str(tmp_path / "e.jsonl"),
        "--max-seconds", "0.05",
    ])
    assert "bystander" in capsys.readouterr().err
