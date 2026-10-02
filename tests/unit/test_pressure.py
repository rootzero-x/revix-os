"""pressure.py testlari -- churn tartibi, tezlik oynasi va EPIZOD CHEGARASI.

Bu testlar xotira ajratadi, lekin JUDA KICHIK (bir necha MB) va cgroup
chegarasi yo'q -- ular mexanizmni sinaydi, pressure yaratmaydi.

Epizod chegarasi testlari HECH QANDAY xotira ajratmaydi va HECH QANDAY
pressure yaratmaydi: sekin ajratish soxta soat va soxta blok bilan taqlid
qilinadi (pastdagi FakeClock / SlowBlock). NEGA TAQLID: 08-guard-rekalibratsiya.md
§5 ning holatini haqiqatan qayta yaratish `memory.high` ostida jonli
pressure epizodini talab qilardi -- bu guest'ni iflos qiladi va `experiment/`
ishiga aralashadi.
"""
import json

from revix.pressure import Allocator, Deadline, PressureGenerator
from revix.schema import Emitter, JsonlWriter


# --- epizod chegarasi uchun asboblar ----------------------------------------


class FakeClock:
    """Boshqarilgan monoton soat. Faqat biz uni surganda yuradi."""

    def __init__(self, t0: float = 1000.0) -> None:
        self.t = t0

    def monotonic(self) -> float:
        return self.t

    def sleep(self, d: float) -> None:
        self.t += max(0.0, d)

    def advance(self, d: float) -> None:
        self.t += d


class SlowBlock:
    """mmap o'rnini bosuvchi: HAR SAHIFAGA TEGISH soatni surib yuboradi.

    08 §5 ning sababini aynan modellaydi: `memory.high` dan oshganda kernel
    ajratuvchi task'ni reclaim throttling bilan uxlatadi, demak bitta sahifa
    fault'i soniyalarga cho'zilishi mumkin va bu uyqu SIGTERM bilan uzilmaydi.
    """

    def __init__(self, size: int, clock: FakeClock, per_page_s: float) -> None:
        self._size = size
        self._clock = clock
        self._per_page = per_page_s
        self.touches = 0

    def __len__(self) -> int:
        return self._size

    def __setitem__(self, off: int, val: int) -> None:
        self.touches += 1
        self._clock.advance(self._per_page)

    def close(self) -> None:
        pass


class FakePsiSource:
    """O'sib boruvchi `full total` beradi; hech qanday faylga tegmaydi."""

    def __init__(self, clock: FakeClock) -> None:
        self._clock = clock
        self._total = 0

    def sample(self):
        self._total += 100_000
        row = {"avg10": 0.0, "avg60": 0.0, "avg300": 0.0, "total": self._total}
        return int(self._clock.t * 1e6), {"some": dict(row), "full": dict(row)}

    def close(self) -> None:
        pass


def _bounded_generator(tmp_path, monkeypatch, clock, per_page_s, blocks):
    """Soxta soat, soxta mmap va soxta PSI bilan generator yasaydi."""
    from revix import pressure as pmod

    class _FakeTime:
        monotonic = staticmethod(clock.monotonic)
        sleep = staticmethod(clock.sleep)

    class _FakeMmap:
        @staticmethod
        def mmap(fd, size):
            b = SlowBlock(size, clock, per_page_s)
            blocks.append(b)
            return b

    monkeypatch.setattr(pmod, "time", _FakeTime)
    monkeypatch.setattr(pmod, "mmap", _FakeMmap)
    # oom_score_adj va cgroup o'qishlari testga aloqasi yo'q.
    monkeypatch.setattr(pmod, "set_oom_score_adj", lambda value=1000: None)
    monkeypatch.setattr(pmod.cg, "own_cgroup", lambda: "/test")

    log = tmp_path / "pressure.jsonl"
    w = JsonlWriter(str(log))
    em = Emitter("pressure-test", "r", "s", boot_id="b")
    gen = PressureGenerator("/sof/cgroup", w, em)
    monkeypatch.setattr(gen, "_open_psi",
                        lambda: setattr(gen, "_psi", FakePsiSource(clock)))
    return gen, w, log


def _stop_record(log):
    for line in log.read_text().splitlines():
        r = json.loads(line)
        if r["record_type"] == "pressure_stop":
            return r
    raise AssertionError("pressure_stop yozuvi yo'q")


def test_churn_avval_ajratadi_keyin_boshatadi():
    """Tartib muhim: bo'shat->ajrat bo'lsa memory.high dan hech qachon oshmaydi
    va pressure umuman bo'lmaydi. Bu test shu regressiyani qulflaydi."""
    a = Allocator()
    block = 1 << 20  # 1 MB
    a.add(block)
    assert len(a.blocks) == 1

    # Ajratish paytida blok soni VAQTINCHA oshishi kerak.
    seen = []
    orig_add = a.add

    def spy_add(n, deadline=None):
        orig_add(n, deadline)
        seen.append(len(a.blocks))

    a.add = spy_add  # type: ignore[method-assign]
    a.churn(1, block)
    # add chaqirilganda 2 blok bo'lgan (vaqtincha oshish), keyin 1 ga qaytgan
    assert seen == [2], f"ajratish paytida vaqtincha oshish kutildi, {seen} bo'ldi"
    assert len(a.blocks) == 1, "churn'dan keyin blok soni o'zgarmasligi kerak"
    a.release_all()


def test_churn_umumiy_hajmni_oshirmaydi():
    """Churn o'sishsiz bo'lishi kerak, aks holda MemoryMax'ga yetib OOM bo'ladi."""
    a = Allocator()
    block = 1 << 20
    for _ in range(4):
        a.add(block)
    before = a.touched_bytes
    a.churn(10, block)
    assert a.touched_bytes == before, "churn net o'sish bermasligi kerak"
    a.release_all()


def test_churn_bosh_allocator_da_ishlaydi():
    """Birinchi churn'da bo'shatiladigan eski blok yo'q -- yiqilmasligi kerak.

    Bo'sh allocator'dan churn barqaror holatga intiladi: birinchi ajratish
    saqlanadi, keyingilari almashtiriladi. Haqiqiy ishlatishda baza allaqachon
    ajratilgan bo'ladi, shuning uchun bu chegaraviy holat.
    """
    a = Allocator()
    block = 1 << 20
    n = a.churn(2, block)
    assert n == 2, "ikkala churn ham bajarilishi kerak"
    assert len(a.blocks) == 1, "churn barqaror holatga intiladi"
    assert a.touched_bytes == block
    a.release_all()


def test_release_all_hisobni_tiklaydi():
    a = Allocator()
    a.add(1 << 20)
    a.release_all()
    assert a.touched_bytes == 0
    assert a.blocks == []


# --- EPIZOD CHEGARASI -------------------------------------------------------
#
# O'lchov (08-guard-rekalibratsiya.md §5): `--max-seconds 5` +
# `RuntimeMaxSec=7s` bilan epizod 0.35 chegarasidan yuqorida 16.3 s turdi
# (run C5), va uni to'xtatgan yagona narsa guard'ning `cgroup.kill` i bo'ldi.
# Sabab: `--max-seconds` faqat tsikl boshida tekshirilardi, bitta `add()`
# ichidagi reclaim throttling uyqusini esa hech biri cheklamasdi.
#
# Quyidagi testlar shu regressiyani qulflaydi. Ular pressure YARATMAYDI.


def test_sekin_ajratish_epizodni_chegaradan_uzaytirmaydi(tmp_path, monkeypatch):
    """Bitta ajratish chegaradan OSHIB bloklasa ham epizod cho'zilmaydi.

    Taqlid: har sahifaga tegish 1 s bloklaydi, chunk 32 MiB = 8192 sahifa,
    ya'ni tuzatishdan OLDIN birinchi `add()` ning o'zi 8192 s ketardi va
    `--max-seconds 5` hech qachon ko'rilmasdi (08 §5).
    """
    clock = FakeClock()
    blocks: list[SlowBlock] = []
    gen, w, log = _bounded_generator(tmp_path, monkeypatch, clock,
                                     per_page_s=1.0, blocks=blocks)
    max_seconds = 5.0
    gen.run_ramp(chunk_mb=32, interval_ms=250.0, max_seconds=max_seconds,
                 cap_mb=1024)
    w.close()
    elapsed = clock.t - 1000.0

    # Chegara + BITTA sahifa: qoldiq cheklanmagan oyna aynan shu (bitta
    # uzilmas page fault), undan ko'pi emas.
    assert elapsed <= max_seconds + 1.0, (
        f"epizod {elapsed} s davom etdi, chegara {max_seconds} s"
    )
    # Blok CHALA tegilgan bo'lishi kerak: tsikl chegarada uzilgani isboti.
    assert blocks, "ajratish bo'lishi kerak edi"
    assert blocks[0].touches <= 6, (
        f"chegaradan keyin ko'pi bilan bitta sahifa, {blocks[0].touches} bo'ldi"
    )
    assert blocks[0].touches < 8192, "butun blok tegilmasligi kerak"

    rec = _stop_record(log)
    assert rec["max_seconds"] == max_seconds
    assert rec["overrun_s"] <= 1.0, "oshib ketish bitta sahifadan katta emas"


def test_epizod_chegarasi_run_pi_da_ham_amal_qiladi(tmp_path, monkeypatch):
    """Bir xil chegara `pi` rejimida ham: pilot aynan shu rejimda ishlaydi.

    08 §5 `ramp` ni o'lchadi, lekin sabab rejimdan mustaqil va §11 ning
    invariantlari `pi` rejimiga tegishli -- faqat `ramp` tuzatilsa pilot
    yo'li tuzatilmagan qolardi.
    """
    clock = FakeClock()
    blocks: list[SlowBlock] = []
    gen, w, log = _bounded_generator(tmp_path, monkeypatch, clock,
                                     per_page_s=1.0, blocks=blocks)
    max_seconds = 5.0
    gen.run_pi(target_rate=0.3, max_seconds=max_seconds, cap_mb=1024,
               step_mb=16, interval_ms=250.0, base_mb=256)
    w.close()
    elapsed = clock.t - 1000.0

    assert elapsed <= max_seconds + 1.0, (
        f"pi epizodi {elapsed} s davom etdi, chegara {max_seconds} s"
    )
    rec = _stop_record(log)
    assert rec["overrun_s"] <= 1.0


def test_baza_ramp_tsikli_chegarani_tekshiradi(tmp_path, monkeypatch):
    """`run_pi` ning baza ramp tsikli avval chegarani UMUMAN tekshirmasdi.

    Baza nishoni juda katta qo'yilgan: tuzatishdan oldin bu tsikl control
    tsikliga yetmasdan ham `max_seconds` dan oshib ketardi, chunki
    `max_seconds` faqat control tsiklida ko'rilardi.
    """
    clock = FakeClock()
    blocks: list[SlowBlock] = []
    gen, w, log = _bounded_generator(tmp_path, monkeypatch, clock,
                                     per_page_s=0.5, blocks=blocks)
    gen.run_pi(target_rate=0.3, max_seconds=3.0, cap_mb=8192,
               step_mb=16, interval_ms=250.0, base_mb=8192)
    w.close()
    assert clock.t - 1000.0 <= 3.0 + 0.5, "baza ramp fazasi chegaralanmagan"


def test_otgan_deadline_bilan_hech_qanday_sahifaga_tegilmaydi(tmp_path, monkeypatch):
    """Chegara allaqachon o'tgan bo'lsa tegish tsikli umuman boshlanmaydi.

    Bu `Deadline` ning tekshiruvi tegishdan OLDIN turganini qulflaydi --
    keyin tursa, har blok bitta sahifaga ortiqcha tegardi.
    """
    clock = FakeClock()
    blocks: list[SlowBlock] = []
    _bounded_generator(tmp_path, monkeypatch, clock, per_page_s=1.0,
                       blocks=blocks)
    a = Allocator()
    expired = Deadline(-1.0, clock.monotonic())
    a.add(1 << 20, expired)
    assert blocks[0].touches == 0, "o'tgan chegara bilan tegish bo'lmasligi kerak"
    assert a.churn(5, 1 << 20, expired) == 0, "churn o'tgan chegarada ishlamaydi"


def test_retouch_vaqt_bilan_ham_cheklanadi(tmp_path, monkeypatch):
    """`retouch` ning yagona chegarasi BAYT budjeti edi, vaqt chegarasi yo'q.

    `run_ramp` shiftga (`cap_mb`) yetgandan keyin aynan shu yo'lda qoladi
    (08 §5 ning C5 run'i uzun epizod bergan holat), demak bu tsikl ham
    vaqt bilan cheklanishi kerak.
    """
    clock = FakeClock()
    blocks: list[SlowBlock] = []
    _bounded_generator(tmp_path, monkeypatch, clock, per_page_s=1.0,
                       blocks=blocks)
    a = Allocator()
    a.add(4 << 20)                      # chegarasiz: to'liq tegiladi
    full = blocks[0].touches
    assert full == (4 << 20) // 4096, "chegarasiz butun blok tegilishi kerak"

    limit = Deadline(2.0, clock.monotonic())
    a.retouch(4 << 20, limit)
    # 2 s / 1 s per sahifa = ko'pi bilan 2 sahifa, ustiga bitta qoldiq
    assert blocks[0].touches - full <= 3, "retouch vaqt bilan cheklanmagan"
