"""sut.c testlari -- HAQIQIY socket ustidan, haqiqiy jarayon bilan.

Bu testlar `sut.c` ni KOMPILYATSIYA qiladi va ishga tushiradi. Mock yo'q:
tekshirilayotgan narsa -- wire protokol (`docs/architecture/03-sut-protokoli.md`,
sut-protocol/v1) va `progress` hisoblagichining semantikasi. Prober shu
spetsifikatsiyaga qarab mustaqil yozilgani uchun har qanday chetga chiqish
integratsiyani buzadi, mock esa aynan shuni yashirardi.

ENG MUHIM TEST: `test_probe_progressni_shishirmaydi`. PREREGISTRATION.md §4
ning 5-bandi (throughput >= theta * R_ref) VR ni process-liveness'dan
ajratadigan yagona narsa. Agar probe javobi progress'ni oshirsa, throughput
probe tezligini o'lchagan bo'lardi -- ya'ni o'lchov o'zini o'lchardi va butun
hissa qulardi.
"""
from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REVIX_DIR = ROOT / "revix"
SUT_BIN = REVIX_DIR / "sut"

# C toolchain'i bo'lmasa modul butunlay o'tkazib yuboriladi (sabab ko'rinadi).
_MISSING = [t for t in ("cc", "make") if shutil.which(t) is None]
if _MISSING:
    pytest.skip(
        "C toolchain yo'q (%s topilmadi) -- sut.c kompilyatsiya qilinmaydi"
        % ", ".join(_MISSING),
        allow_module_level=True,
    )

RATE_HZ_DEFAULT = 2000.0
CONNECT_TIMEOUT = 2.0


@pytest.fixture(scope="session")
def sut_bin() -> str:
    proc = subprocess.run(
        ["make", "-C", str(REVIX_DIR), "all"],
        capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        pytest.fail("make muvaffaqiyatsiz (rc=%d):\n%s\n%s"
                    % (proc.returncode, proc.stdout, proc.stderr))
    assert SUT_BIN.is_file(), "make o'tdi, lekin binar yo'q: %s" % SUT_BIN
    return str(SUT_BIN)


class Sut:
    """Bitta SUT jarayoni + uning socket'i. Teardown har doim o'ldiradi."""

    def __init__(self, bin_path: str, env_extra: dict | None = None,
                 sock_path: str | None = None):
        # mkdtemp ataylab: sun_path 108 bayt bilan cheklangan, pytest'ning
        # tmp_path yo'llari uzun bo'lib ketishi mumkin.
        self.dir = tempfile.mkdtemp(prefix="revixsut-")
        self.sock_path = sock_path or os.path.join(self.dir, "s.sock")
        assert len(self.sock_path) < 100, "socket yo'li sun_path uchun uzun"

        env = dict(os.environ)
        # Meros qolgan systemd muhiti testni buzmasin.
        for key in ("INVOCATION_ID", "NOTIFY_SOCKET", "WATCHDOG_USEC",
                    "REVIX_SUT_CONFIG", "REVIX_SUT_RATE_HZ",
                    "REVIX_SUT_DELAY_READY_MS"):
            env.pop(key, None)
        env["REVIX_SUT_SOCKET"] = self.sock_path
        env.update(env_extra or {})

        self._errfile = open(os.path.join(self.dir, "stderr.log"), "w+b")
        self.proc = subprocess.Popen(
            [bin_path], env=env,
            stdout=subprocess.DEVNULL, stderr=self._errfile,
        )

    # --- hayot tsikli ---
    def wait_socket(self, timeout: float = 5.0) -> "Sut":
        """Socket paydo bo'lib, javob bera boshlashini kutadi.

        INFO ishlatiladi, PROBE emas: INFO READY'dan oldin ham javob beradi,
        ya'ni `slow_start` testi ham shu kutishdan foydalanadi.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            rc = self.proc.poll()
            if rc is not None:
                raise AssertionError(
                    "SUT ishga tushmadi: rc=%s stderr=%r" % (rc, self.stderr()))
            if os.path.exists(self.sock_path):
                try:
                    if self.request("INFO").startswith("OK "):
                        return self
                except OSError:
                    pass
            time.sleep(0.005)
        raise AssertionError("SUT %.1fs ichida javob bermadi" % timeout)

    def stop(self) -> None:
        try:
            if self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait(timeout=2)
        finally:
            self._errfile.close()
            shutil.rmtree(self.dir, ignore_errors=True)

    # --- protokol ---
    def request(self, msg: str, timeout: float = CONNECT_TIMEOUT) -> str:
        """Bitta so'rov-javob YANGI ulanishda (protokol §1)."""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        sock.settimeout(timeout)
        try:
            sock.connect(self.sock_path)
            sock.send(msg.encode("ascii"))
            return sock.recv(4096).decode("ascii")
        finally:
            sock.close()

    def probe(self) -> dict:
        return parse_ok(self.request("PROBE"))

    def progress(self) -> int:
        return int(self.probe()["progress"])

    def stderr(self) -> str:
        self._errfile.flush()
        pos = self._errfile.tell()
        self._errfile.seek(0)
        data = self._errfile.read()
        self._errfile.seek(pos)
        return data.decode("utf-8", "replace")


def parse_ok(resp: str) -> dict:
    assert "\n" not in resp, "javobda satr oxiri bo'lmasligi kerak: %r" % resp
    parts = resp.split(" ")
    assert parts[0] == "OK", "OK kutilgan edi: %r" % resp
    fields = {}
    for part in parts[1:]:
        key, _, value = part.partition("=")
        assert _ == "=", "key=value kutilgan edi: %r" % resp
        fields[key] = value
    return fields


@pytest.fixture
def sut(sut_bin):
    """SUT fabrikasi. Teardown BARCHA yaratilganlarni o'ldiradi."""
    started: list[Sut] = []

    def factory(wait: bool = True, sock_path: str | None = None, **env) -> Sut:
        node = Sut(sut_bin, env, sock_path=sock_path)
        started.append(node)
        return node.wait_socket() if wait else node

    try:
        yield factory
    finally:
        for node in started:
            node.stop()


# --- transport va so'rovlar ------------------------------------------------


def test_socket_rejimi_0600(sut):
    node = sut()
    mode = os.stat(node.sock_path).st_mode & 0o777
    assert mode == 0o600, "protokol §1: rejim 0600, olindi %o" % mode


def test_info_proto_1(sut):
    fields = parse_ok(sut().request("INFO"))
    assert fields["proto"] == "1"
    assert fields["impl"]
    assert int(fields["progress"]) >= 0
    assert int(fields["uptime_us"]) > 0


def test_probe_javobi_togri_formatda(sut):
    node = sut()
    fields = node.probe()
    assert set(fields) == {"progress", "pid", "invocation", "rss_kb", "mono_us"}
    assert int(fields["pid"]) == node.proc.pid
    assert int(fields["progress"]) >= 0
    assert int(fields["rss_kb"]) > 0
    assert int(fields["mono_us"]) > 0
    assert len(fields["invocation"]) == 32


def test_notanish_buyruq(sut):
    node = sut()
    assert node.request("BOGUS") == "ERR unknown_command"
    assert node.request("probe") == "ERR unknown_command"      # katta harf shart
    assert node.request("PROBE EXTRA JUNK").startswith("OK ")  # toqatlilik
    assert node.request("FAULT") == "ERR bad_args"             # kind yo'q
    assert node.request("FAULT nosuch_kind") == "ERR bad_args"


# --- progress semantikasi (PREREGISTRATION.md §4.5 ning asosi) -------------


def test_progress_qatiy_osadi(sut):
    node = sut(REVIX_SUT_RATE_HZ="2000")
    first = node.progress()
    time.sleep(0.2)
    second = node.progress()
    assert second > first, "progress qat'iy o'suvchi bo'lishi kerak"
    # 200 ms x 2000 Hz ~ 400. Yuk ostida kamayishi mumkin, lekin oshmasligi
    # kerak (deadline'lar quvib yetmaydi).
    assert 1 <= second - first <= 2 * 400


def test_probe_progressni_shishirmaydi(sut):
    """Probe'ga javob berish progress'ni OSHIRMAYDI (protokol §4.5).

    Past tezlik (50 Hz = 20 ms davr) ataylab tanlangan: 20 ta tez probe
    o'n millisekundlarda bajariladi, ya'ni "har probe +1" xatosi (+20)
    o'tgan vaqtdan kelib chiqadigan o'sishdan (~0-2) keskin farq qiladi.
    """
    rate = 50.0
    node = sut(REVIX_SUT_RATE_HZ=str(int(rate)))
    samples = [node.probe() for _ in range(20)]

    delta_progress = int(samples[-1]["progress"]) - int(samples[0]["progress"])
    # SUT ning O'Z soatidan (mono_us) olinamiz -- test jarayonining
    # scheduling jitter'i o'lchovga kirmasin.
    elapsed_us = int(samples[-1]["mono_us"]) - int(samples[0]["mono_us"])
    expected = elapsed_us / 1e6 * rate

    assert delta_progress <= expected + 3, (
        "progress o'tgan vaqtdan tez o'sdi: delta=%d, kutilgan<=%.2f "
        "(elapsed=%d us) -- probe javobi hisoblagichni oshirayotganga o'xshaydi"
        % (delta_progress, expected + 3, elapsed_us))
    assert delta_progress < 20, (
        "delta (%d) probe soniga (20) yaqin -- hisoblagich probe'larni "
        "sanayotganga o'xshaydi" % delta_progress)


def test_invocation_env_dan_echo_qilinadi(sut):
    inv = "0123456789abcdef0123456789abcdef"
    node = sut(INVOCATION_ID=inv)
    assert node.probe()["invocation"] == inv
    assert parse_ok(node.request("INFO"))["invocation"] == inv


def test_invocation_yoq_bolsa_32_nol(sut):
    assert sut().probe()["invocation"] == "0" * 32


# --- fault endpoint'lari ---------------------------------------------------


FAULT_ARMED_RE = r"^FAULT ARMED %s mono_us=\d+$"


def assert_armed_stderr(node: Sut, kind: str) -> None:
    lines = [ln for ln in node.stderr().splitlines() if ln.startswith("FAULT ")]
    assert len(lines) == 1, "fault stderr'ga AYNAN bitta satr yozadi: %r" % lines
    assert re.match(FAULT_ARMED_RE % kind, lines[0]), lines[0]


def test_fault_exit_avval_javob_keyin_chiqish(sut):
    node = sut()
    # Javob AVVAL keladi: recv _exit dan oldin navbatga qo'yilgan bo'lishi
    # kerak, aks holda harness fault qabul qilinganini bilmaydi (protokol §5).
    assert node.request("FAULT exit code=3") == "OK armed=exit"
    assert node.proc.wait(timeout=3) == 3
    assert_armed_stderr(node, "exit")


def test_fault_exit_yaroqsiz_kod(sut):
    node = sut()
    assert node.request("FAULT exit code=abc") == "ERR bad_args"
    assert node.proc.poll() is None, "yaroqsiz argument fault'ni QUROLLANTIRMAYDI"
    assert node.request("PROBE").startswith("OK ")


def test_fault_sigkill_self(sut):
    node = sut()
    assert node.request("FAULT sigkill_self") == "OK armed=sigkill_self"
    assert node.proc.wait(timeout=3) == -9
    assert_armed_stderr(node, "sigkill_self")


def test_fault_stop_progress_fail_silent(sut):
    """Ish tsikli o'ladi, socket esa javob berishda davom etadi."""
    node = sut(REVIX_SUT_RATE_HZ="2000")
    assert node.request("FAULT stop_progress") == "OK armed=stop_progress"
    assert_armed_stderr(node, "stop_progress")

    time.sleep(0.15)            # tsikl to'xtaganiga kafolat
    frozen = node.progress()
    time.sleep(0.2)
    assert node.progress() == frozen, "stop_progress'dan keyin progress qotadi"
    assert node.proc.poll() is None, "jarayon tirik qolishi kerak (fail-silent)"
    assert parse_ok(node.request("INFO"))["proto"] == "1"


# --- ishga tushish / to'xtash ---------------------------------------------


def test_delay_ready_not_ready_qaytaradi(sut):
    """`slow_start`: socket accept qiladi, PROBE esa `ERR not_ready`."""
    node = sut(REVIX_SUT_DELAY_READY_MS="1000")
    assert node.request("PROBE") == "ERR not_ready"
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        if node.request("PROBE").startswith("OK "):
            break
        time.sleep(0.05)
    else:
        raise AssertionError("READY kechikishdan keyin ham kelmadi")


def test_sigterm_toza_chiqish(sut):
    node = sut()
    node.proc.terminate()
    assert node.proc.wait(timeout=3) == 0, "SIGTERM -> kod 0 (protokol §6)"
    assert not os.path.exists(node.sock_path), "socket o'chirilishi kerak"


def test_eski_socket_ustiga_ishga_tushadi(sut):
    """Stale socket bind'ni buzmasligi kerak (restart o'lchovi uchun kritik)."""
    node = sut()
    node.proc.kill()            # unlink qilmasdan o'lish (crash'ga taqlid)
    node.proc.wait(timeout=3)
    assert os.path.exists(node.sock_path), "kill socket faylini qoldiradi"

    second = sut(sock_path=node.sock_path)
    assert second.request("PROBE").startswith("OK ")


def test_yaroqsiz_config_ready_dan_oldin_chiqadi(sut):
    node = sut(wait=False, REVIX_SUT_CONFIG="/nonexistent/revix-sut.conf")
    assert node.proc.wait(timeout=3) != 0, "misconfiguration -> nolga teng emas"
    assert not os.path.exists(node.sock_path)
    assert "CONFIG ERROR" in node.stderr()


def test_yaroqli_config_oqiladi(sut, tmp_path):
    cfg = tmp_path / "sut.conf"
    cfg.write_text("# izoh\nrate_hz=500\nwork_unit_rounds=64\n")
    node = sut(REVIX_SUT_CONFIG=str(cfg))
    first = node.probe()
    time.sleep(0.4)
    second = node.probe()
    elapsed_s = (int(second["mono_us"]) - int(first["mono_us"])) / 1e6
    delta = int(second["progress"]) - int(first["progress"])
    # 500 Hz: config env'dan keyin o'qiladi, ya'ni ustun.
    assert delta <= elapsed_s * 500 + 5
    assert delta > 0
