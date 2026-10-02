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


# --- regression-lock: parametrli fault'larda data race yo'q ----------------
#
# NEGA: ThreadSanitizer takroriy `FAULT leak` / `FAULT block_fifo` da main
# thread'ning parametr yozishini ish thread'ining o'qishi bilan poygada
# ko'rsatgan. Ta'siri yo'q edi, lekin o'lchov asbobida "ma'lum shovqin" bazasi
# TSan'ning YANGI poygasini ko'rinmas qiladi. Quyidagi testlar TSan bilan
# alohida (vaqtinchalik papkada) yig'adi -- revix/sut ga TEGMAYDI.

TSAN_FLAGS = ["-O2", "-Wall", "-Wextra", "-Werror", "-std=c11", "-pthread",
              "-fsanitize=thread", "-g"]


@pytest.fixture(scope="session")
def tsan_bin():
    outdir = tempfile.mkdtemp(prefix="revixselftest-tsan-")
    out = os.path.join(outdir, "sut_tsan")
    proc = subprocess.run(
        ["cc"] + TSAN_FLAGS + ["-o", out, str(REVIX_DIR / "sut.c")],
        capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        shutil.rmtree(outdir, ignore_errors=True)
        pytest.skip("TSan bilan yig'ib bo'lmadi (runtime yo'q?): %s"
                    % proc.stderr.strip()[:200])
    try:
        yield out
    finally:
        shutil.rmtree(outdir, ignore_errors=True)


def _tsan_node(tsan_bin: str) -> Sut:
    node = Sut(tsan_bin, {"REVIX_SUT_RATE_HZ": "2000"})
    try:
        return node.wait_socket()
    except AssertionError as exc:
        node.stop()
        pytest.skip("TSan binar'i ishga tushmadi (yadro ASLR?): %s" % exc)


def _tsan_races(node: Sut) -> list:
    node.proc.terminate()
    node.proc.wait(timeout=5)
    return [ln for ln in node.stderr().splitlines() if "data race" in ln]


def test_takroriy_fault_leak_data_race_bermaydi(tsan_bin):
    node = _tsan_node(tsan_bin)
    try:
        assert node.request("FAULT leak rate_mb_s=4") == "OK armed=leak"
        time.sleep(0.3)             # leak_thread tezlikni o'qib bo'lsin
        # Takroriy fault: javob baribir `OK armed=leak` (idempotent).
        assert node.request("FAULT leak rate_mb_s=8") == "OK armed=leak"
        time.sleep(0.3)
        races = _tsan_races(node)
        assert races == [], "TSan data race: %r\n%s" % (races, node.stderr())
    finally:
        node.stop()


def test_takroriy_fault_block_fifo_data_race_bermaydi(tsan_bin):
    node = _tsan_node(tsan_bin)
    try:
        fifo = os.path.join(node.dir, "f.fifo")
        os.mkfifo(fifo)
        assert node.request("FAULT block_fifo path=" + fifo) == "OK armed=block_fifo"
        time.sleep(0.3)             # ish thread'i open() ichida bloklangan
        assert node.request("FAULT block_fifo path=" + fifo) == "OK armed=block_fifo"
        time.sleep(0.3)
        races = _tsan_races(node)
        assert races == [], "TSan data race: %r\n%s" % (races, node.stderr())
    finally:
        node.stop()


def test_takroriy_fault_block_fifo_birinchi_yolni_saqlaydi(sut):
    """Takroriy `FAULT block_fifo` yo'lni QAYTA yozmaydi (birinchi yo'l qoladi).

    NEGA: TSan ish thread'i `open()` ichida bloklanganini poyga oynasida
    ko'rmaydi, shuning uchun data-race testi bu fix'ni eski kodda ushlamaydi.
    Bu test xatti-harakat orqali qulflaydi: ish thread'i yozuvchi kelib
    yopgandan keyin g_fifo_path ni QAYTA o'qiydi -- yo'l qayta yozilgan
    bo'lsa u B'da, aks holda A'da kutib turadi.
    """
    node = sut(REVIX_SUT_RATE_HZ="2000")
    path_a = os.path.join(node.dir, "a.fifo")
    path_b = os.path.join(node.dir, "b.fifo")
    os.mkfifo(path_a)
    os.mkfifo(path_b)
    assert node.request("FAULT block_fifo path=" + path_a) == "OK armed=block_fifo"
    assert node.request("FAULT block_fifo path=" + path_b) == "OK armed=block_fifo"

    def reader_waiting(path: str) -> bool:
        """O_NONBLOCK yozuvchi faqat o'quvchi open() da kutayotgan bo'lsa ochiladi."""
        try:
            fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
        except OSError:             # ENXIO: o'quvchi yo'q
            return False
        os.close(fd)
        return True

    deadline = time.monotonic() + 3.0
    while not reader_waiting(path_a):   # birinchi ochish: o'quvchi A'da
        assert time.monotonic() < deadline, "ish thread'i A'ni ochmadi"
        time.sleep(0.01)
    time.sleep(0.3)                     # EOF -> thread yo'lni qayta o'qidi
    assert reader_waiting(path_a), "birinchi yo'l (A) saqlanishi kerak"
    assert not reader_waiting(path_b), "takroriy fault yo'lni B ga almashtirdi"


# --- regression-lock: Makefile bayroqlarni kuzatadi ------------------------
#
# NEGA: make faqat fayl vaqtlariga qaraydi. Stamp'siz sanitizer bilan
# yig'ilgan `sut` keyingi oddiy `make all` da qayta ishlatilib, sut_bin
# fixture'iga TSan/ASan binar'ini "haqiqiy SUT" qilib uzatardi. SUT vaqt
# etalon'i, shuning uchun bu hech qanday signalsiz o'lchovni buzardi.
# Haqiqiy kompilyator o'rniga SANAYDIGAN wrapper ishlatiladi: sanitizer
# runtime'iga bog'liq emas va "qayta yig'ildimi" savoliga aniq javob beradi.


def _make_sandbox():
    """Makefile + sut.c nusxasi va CC wrapper'i. (papka, wrapper, log) qaytaradi."""
    root = tempfile.mkdtemp(prefix="revixselftest-make-")
    shutil.copy(REVIX_DIR / "Makefile", root)
    shutil.copy(REVIX_DIR / "sut.c", root)
    log = os.path.join(root, "cc.log")
    wrapper = os.path.join(root, "cc-count")
    with open(wrapper, "w") as fh:
        fh.write('#!/bin/sh\necho "$*" >> "%s"\nexec cc "$@"\n' % log)
    os.chmod(wrapper, 0o755)
    return root, wrapper, log


def _make_all(root: str, wrapper: str, *extra: str) -> None:
    env = dict(os.environ)
    env.pop("EXTRA_CFLAGS", None)   # muhit bayrog'i sinovni buzmasin
    proc = subprocess.run(
        ["make", "-C", root, "CC=" + wrapper] + list(extra) + ["all"],
        capture_output=True, text=True, timeout=120, env=env,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def _compiles(log: str) -> list:
    with open(log) as fh:
        return fh.read().splitlines()


def test_makefile_bayroq_ozgarsa_qayta_yigadi():
    root, wrapper, log = _make_sandbox()
    try:
        _make_all(root, wrapper)
        assert len(_compiles(log)) == 1

        _make_all(root, wrapper)
        assert len(_compiles(log)) == 1, "bayroq bir xil -- qayta yig'ilmasligi kerak"

        _make_all(root, wrapper, "EXTRA_CFLAGS=-DREVIX_SELFTEST_MARK")
        lines = _compiles(log)
        assert len(lines) == 2, "EXTRA_CFLAGS o'zgardi -- qayta yig'ilishi shart"
        assert "-DREVIX_SELFTEST_MARK" in lines[-1]

        # Eskirgan (stale) yo'l: sanitizer-uslubidagi binar'dan keyin oddiy
        # `make all` AYNAN qayta yig'ishi kerak -- jimgina qayta ishlatmasligi.
        _make_all(root, wrapper, "EXTRA_CFLAGS=")
        lines = _compiles(log)
        assert len(lines) == 3, "bayroq tozalandi -- eski binar qayta ishlatildi"
        assert "-DREVIX_SELFTEST_MARK" not in lines[-1]

        _make_all(root, wrapper, "EXTRA_CFLAGS=")
        assert len(_compiles(log)) == 3

        # Manba o'zgarsa qayta yig'ish hamon ishlaydi (stamp buni buzmagan).
        future = time.time() + 5
        os.utime(os.path.join(root, "sut.c"), (future, future))
        _make_all(root, wrapper, "EXTRA_CFLAGS=")
        assert len(_compiles(log)) == 4
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_makefile_clean_stamp_ham_ochiradi():
    root, wrapper, log = _make_sandbox()
    try:
        _make_all(root, wrapper)
        assert os.path.exists(os.path.join(root, "sut"))
        subprocess.run(["make", "-C", root, "clean"], check=True,
                       capture_output=True, timeout=60)
        leftovers = [n for n in os.listdir(root)
                     if n == "sut" or n.startswith("sut.flags")]
        assert leftovers == [], "clean binar va stamp'ni olib tashlashi kerak"
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_makefile_cflags_ozgarmagan_va_werror_saqlangan():
    text = (REVIX_DIR / "Makefile").read_text()
    assert "CFLAGS := -O2 -Wall -Wextra -Werror -std=c11 -pthread\n" in text
    assert "-Wno-" not in text, "ogohlantirishni o'chirish taqiqlangan"
