"""Nazorat qilinadigan memory pressure generatori.

MEXANIZM: anonim xotira ajratiladi va har sahifasiga tegiladi. Slice'da
`memory.high` qo'yilgan bo'lsa, undan oshgan qism kernel'ni uzluksiz reclaim
qilishga majbur qiladi -- bu PSI memory pressure'ini OSHIRADI, lekin hech kimni
O'LDIRMAYDI. Aynan shu kerak: fault class 4 (`host_mem_pressure`) kill'siz
pressure bo'lishi shart, aks holda u fault class 3 (`leak_oom`) ga aylanib
qoladi va ikki fault klassi aralashadi.

XAVFSIZLIK (buzilmaydi):
  * HAR DOIM `systemd-run --user --slice=revixlab.slice` orqali ishga tushadi.
    To'g'ridan-to'g'ri Bash'dan ishga tushirilsa Claude desktop scope ichida
    tug'iladi va oomd ishlab chiqish sessiyasini o'ldiradi
    (docs/architecture/01-muhit-tekshiruvlari.md §6).
  * `MemorySwapMax=0` -- 5.5 GiB swap to'lib host-wide IO yaratishini oldini oladi.
  * Ichki `--max-seconds` qattiq chegara + systemd `RuntimeMaxSec=`. IKKI
    mustaqil chegara, chunki generator trial'dan uzoq yashamasligi KERAK.
    Ikkisi ham SAQLANADI; farq shundaki endi ikkisi ham MAJBURLANADIGAN
    bo'ldi, tavsiyaviy emas -- pastdagi EPIZOD CHEGARASI ga qarang.
  * `oom_score_adj = 1000` -- kernel global OOM killer boshqa hech narsani emas,
    AVVAL generatorni tanlaydi. (Oshirish privilegiyasiz mumkin; pasaytirish yo'q.)
  * Guard mustaqil ishlaydi va bu jarayonni istalgan paytda o'ldirishi mumkin.

EPIZOD CHEGARASI -- `--max-seconds` nega endi haqiqiy chegara:
  O'LCHOV (08-guard-rekalibratsiya.md §5): `--max-seconds 5` +
  `RuntimeMaxSec=7s` bilan epizod `sustain_rate_threshold = 0.35` dan yuqorida
  **16.3 s** turdi (run C5); epizodni to'xtatgan yagona narsa guard'ning
  `cgroup.kill` i bo'ldi. `RuntimeMaxSec=` SIGTERM yubordi, lekin jarayon 10 s
  keyin SIGKILL bilan o'ldi. Shu bilan `TESTING.md` §3 ning «ikki vaqt
  chegarasi guard'ga TAYANMAYDI» da'vosi bu mashinada rad etildi va
  `SECURITY.md` §2 ning qatlamli himoyasi bitta qatlamga tushdi.

  SABAB (§5, kod o'qishidan -- mexanizm o'lchanmadi): `--max-seconds` faqat
  tsikl boshida tekshirilardi, ajratish ichida emas. `memory.high` dan oshganda
  kernel ajratuvchi task'ni reclaim throttling bilan uxlatadi va bu uyqu
  SIGTERM bilan uzilmaydi, demak ikki chegara ham faqat ajratishlar ORASIDA
  tekshirilardi, bittasining ICHIDAGI vaqtni esa hech biri cheklamasdi.

  YECHIM: cheklanmagan kutish `add()` chaqiruvida emas, uning ichidagi
  SAHIFAGA TEGISH tsiklida. Shuning uchun `Deadline` har sahifaga tegishdan
  OLDIN tekshiriladi (`Allocator._touch`), va deadline o'tgan bo'lsa tsikl
  darhol uziladi. Sahifaga tegish -- bu mexanizmda bloklashi mumkin bo'lgan
  YAGONA amal, demak endi bloklashi mumkin bo'lgan har bir amaldan oldin
  deadline tekshiriladi. Bu `02` §3 ning dizayniga mos: blok hajmi impuls
  kattaligini boshqaradigan knob bo'lib qoladi, chegara esa impuls ichida
  majburlanadi -- ya'ni DOZA o'zgarmaydi.

  QOLDIQ CHEKLANMAGAN OYNA -- halol bayon: bitta sahifaga tegish (bitta page
  fault) boshlangandan keyin uni foydalanuvchi fazosidan uzish MUMKIN EMAS.
  Reclaim throttling uyqusining uzunligi BU HUJJATDA O'LCHANMAGAN (§5:
  «mexanizm o'lchanmadi»), demak epizod chegarasi
  `max_seconds + bitta uzilmas page fault` bo'ladi. Bu avvalgi oyna
  (bitta blokning MING sahifasi, 32 MiB uchun 8192 ta) o'rniga bitta
  sahifa -- ya'ni ANCHA kichik, lekin qat'iy ma'noda hamon cheklanmagan.
  Kichikroq cheklanmagan oyna ham cheklanmagan: bu kafolat emas, chegara.
  Haqiqiy oshib ketish har epizodda `pressure_stop.overrun_s` da QAYD
  ETILADI, demak u endi taxmin emas, o'lchov bo'ladi.

PI CONTROLLER: nishon -- slice'ning `total=` dan olingan 2 s oynadagi stall
ulushi (PREREGISTRATION.md §7: `total` asosiy o'lchov, avgN kechikadi).
Controller SEKIN: PSI 2 s kadensda yangilanadi, demak tez sozlash faqat
tebranish keltiradi.
"""

from __future__ import annotations

import argparse
import mmap
import os
import signal
import sys
import time

from . import cgroup as cg
from .schema import Emitter, JsonlWriter, mono_us, new_run_id

PAGE = 4096
RATE_WINDOW_US = 2_000_000


class Deadline:
    """Epizodning absolut monoton qattiq chegarasi.

    NEGA ALOHIDA SINF: avvalgi kod `time.monotonic() - start >= max_seconds` ni
    har tsiklda qayta yozardi va shu sababli chegarani UNUTISH oson edi --
    aynan shunday bo'ldi: `run_pi` ning baza ramp tsikli chegarani umuman
    tekshirmasdi. Bitta obyekt ajratishning eng ichki tsiklidan asosiy
    tsiklgacha UZATILADI, demak chegarani tekshirmaydigan yo'l qolmaydi.
    """

    def __init__(self, seconds: float, start: float | None = None) -> None:
        self.start = time.monotonic() if start is None else start
        self.seconds = seconds
        self.at = self.start + seconds

    def expired(self) -> bool:
        return time.monotonic() >= self.at

    def remaining(self) -> float:
        """Chegaragacha qolgan vaqt; o'tib ketgan bo'lsa 0.0."""
        return max(0.0, self.at - time.monotonic())


def set_oom_score_adj(value: int = 1000) -> int | None:
    """Kernel OOM killer uchun o'zini eng jozibador nishon qilib qo'yadi.

    Privilegiyasiz faqat OSHIRISH mumkin, demak bu ishlaydi. Muvaffaqiyatsiz
    bo'lsa None qaytaradi -- bu halokat emas, lekin qayd etiladi.
    """
    try:
        with open("/proc/self/oom_score_adj", "w") as fh:
            fh.write(str(value))
        return value
    except OSError:
        return None


class Allocator:
    """Anonim xotira bloklarini ushlab turadi va ularga tegadi.

    mmap ishlatiladi (bytearray emas), chunki bu aniq anonim sahifalar beradi
    va Python'ning ichki allokatori aralashmaydi -- ya'ni ajratilgan hajm
    o'lchanadigan bo'lib qoladi.
    """

    def __init__(self) -> None:
        self.blocks: list[mmap.mmap] = []
        self.touched_bytes = 0

    @staticmethod
    def _touch(m: mmap.mmap, deadline: Deadline | None) -> int:
        """`m` ning har sahifasiga tegadi; deadline o'tsa DARHOL uziladi.

        NEGA HAR SAHIFADAN OLDIN: 08 §5 ga ko'ra bloklashi mumkin bo'lgan
        yagona amal -- sahifaga tegish (page fault reclaim throttling ichiga
        tushishi mumkin, va bu uyqu SIGTERM bilan uzilmaydi). Deadline
        bloklashi mumkin bo'lgan har bir amaldan OLDIN tekshirilsa, tsikl
        chegaradan keyin ko'pi bilan BITTA sahifa qo'shimcha ishlaydi.

        QOLDIQ: allaqachon boshlangan page fault'ni uzish mumkin emas (modul
        izohi, EPIZOD CHEGARASI). Shuning uchun bu chegara, kafolat emas.

        Qaytaradi: tegilgan bayt (deadline uzsa, so'ralgandan kichik).
        """
        spent = 0
        for off in range(0, len(m), PAGE):
            if deadline is not None and deadline.expired():
                break
            m[off] = 1
            spent += PAGE
        return spent

    def add(self, size_bytes: int, deadline: Deadline | None = None) -> int:
        """Anonim blok ajratadi va unga tegadi. Qaytaradi: tegilgan bayt.

        `touched_bytes` MAP QILINGAN hajmni hisoblaydi, tegilganini emas:
        `cap_mb` va PI bazasi rezident nishon bo'lib qoladi va `churn()` ning
        «net o'sish yo'q» invarianti o'zgarmaydi. Chala tegilgan blok faqat
        deadline epizodni uzgan paytda, ya'ni allaqachon to'xtash yo'lida
        bo'lganda paydo bo'ladi.
        """
        m = mmap.mmap(-1, size_bytes)
        # Har sahifaga tegish: ajratish o'zi sahifa bermaydi, faqat tegish beradi.
        spent = self._touch(m, deadline)
        self.blocks.append(m)
        self.touched_bytes += size_bytes
        return spent

    def retouch(self, bytes_budget: int, deadline: Deadline | None = None) -> None:
        """Mavjud bloklarga qayta tegib, ularni issiq ushlaydi.

        Reclaim qilingan sahifalarni qaytarib olishga majbur qiladi -- bu
        ajratishni to'xtatmasdan pressure'ni ushlab turish usuli.

        NEGA DEADLINE SHU YERDA HAM: bu tsikl ham sahifaga tegadi, demak u ham
        reclaim throttling ichida uxlashi mumkin. Avval uning yagona chegarasi
        BAYT budjeti edi (08 §5: `run_ramp` shiftga yetgandan keyin aynan shu
        yo'lda qoladi), vaqt chegarasi yo'q edi.
        """
        if not self.blocks:
            return
        spent = 0
        for m in self.blocks:
            for off in range(0, len(m), PAGE):
                if deadline is not None and deadline.expired():
                    return
                m[off] = 1
                spent += PAGE
                if spent >= bytes_budget:
                    return

    def churn(self, n_blocks: int, block_bytes: int,
              deadline: Deadline | None = None) -> int:
        """AJRAT, keyin eng eskisini BO'SHAT. Tartib muhim.

        NEGA BU TARTIB: pressure `memory.high` dan OSHGANDA paydo bo'ladi.
          * bo'shat->ajrat: current hech qachon high dan oshmaydi -> pressure YO'Q
          * ajrat->bo'shat: har churn high dan blok hajmicha VAQTINCHA oshadi
            -> boshqariladigan pressure impulsi, keyin darhol qaytariladi

        Demak:
          * blok HAJMI  -> bitta impulsning stall kattaligi
          * churn SONI  -> tik'dagi duty cycle
        Ikkisi birgalikda 2 s oynadagi o'rtacha stall ulushini boshqaradi.

        O'lchangan sabab (docs/architecture/02-guard-kalibratsiyasi.md):
        anonim xotira + MemorySwapMax=0 bilan reclaim hech narsa bo'shata
        olmaydi, demak high dan uzluksiz oshish ~0.98 stall beradi va o'rta
        band yo'q. Impuls + duty cycle o'rta bandni qaytaradi.

        DEADLINE: har blokdan OLDIN tekshiriladi va `add()` ichiga uzatiladi.
        NEGA BLOK HAJMI BO'LINMAYDI: `02` §3 ga ko'ra blok hajmi bitta impuls
        stall kattaligining knob'i, ya'ni DOZA parametri. Uni bo'lish dozani
        o'zgartirardi (va `pop(0)` semantikasini buzardi). Shuning uchun
        chegara blokni bo'lmasdan, blok ICHIDA -- sahifa granularligida --
        majburlanadi. Doza o'zgarmaydi, chegara esa majburlanadigan bo'ladi.

        Qaytaradi: haqiqatan churn qilingan blok soni.
        """
        done = 0
        for _ in range(n_blocks):
            if deadline is not None and deadline.expired():
                return done
            try:
                # AVVAL ajratamiz -> high dan oshadi
                self.add(block_bytes, deadline)
            except (MemoryError, OSError):
                return done
            if len(self.blocks) > 1:           # KEYIN eng eskisini bo'shatamiz
                old = self.blocks.pop(0)
                old_bytes = len(old)
                try:
                    old.close()
                except (BufferError, ValueError):
                    pass
                self.touched_bytes -= old_bytes
            done += 1
        return done

    def release_all(self) -> None:
        for m in self.blocks:
            try:
                m.close()
            except (BufferError, ValueError):
                pass
        self.blocks.clear()
        self.touched_bytes = 0


class PressureGenerator:
    def __init__(
        self,
        cgroup_path: str,
        writer: JsonlWriter | None,
        emitter: Emitter | None,
    ) -> None:
        self.cgroup_path = cgroup_path
        self.writer = writer
        self.emitter = emitter
        self.alloc = Allocator()
        self._stop = False
        self._psi: cg.PsiFile | None = None
        self._hist: list[tuple[int, int]] = []

    def _emit(self, rt: str, payload: dict) -> None:
        if self.writer is None or self.emitter is None:
            return
        try:
            self.writer.write(self.emitter.record(rt, payload, stream=rt))
        except Exception:  # noqa: BLE001
            pass

    def _open_psi(self) -> None:
        p = f"{self.cgroup_path}/memory.pressure"
        self._psi = cg.PsiFile(p)

    def current_rate(self) -> tuple[float | None, int]:
        """Slice'ning 2 s oynadagi `full` stall ulushi va joriy total."""
        assert self._psi is not None
        t, psi = self._psi.sample()
        total = int(psi["full"]["total"])
        self._hist.append((t, total))
        cutoff = t - 3 * RATE_WINDOW_US
        self._hist = [h for h in self._hist if h[0] >= cutoff]
        # ENG TOR >=2 s oyna (eng eski emas): aks holda oyna suzib, PI
        # controller silliqlangan, kechikkan signalga qarab ishlardi.
        old = None
        for h in reversed(self._hist):
            if t - h[0] >= RATE_WINDOW_US:
                old = h
                break
        if old is None:
            return None, total
        return cg.stall_fraction(old[1], total, old[0], t), total

    def run_ramp(self, chunk_mb: int, interval_ms: float, max_seconds: float,
                 cap_mb: int) -> int:
        """Tez ramp: guard'ni sinash uchun. Nishon yo'q, faqat o'sish.

        Guard testi uchun aynan shu kerak -- boshqarilmagan o'sish PSI ni
        ishonchli ko'taradi, demak guard'ning javob berishini aniq sinaydi.
        """
        self._open_psi()
        adj = set_oom_score_adj(1000)
        self._emit("pressure_start", {"mode": "ramp", "chunk_mb": chunk_mb,
                                      "interval_ms": interval_ms,
                                      "cap_mb": cap_mb,
                                      "max_seconds": max_seconds,
                                      "oom_score_adj": adj,
                                      "cgroup": self.cgroup_path,
                                      "own_cgroup": cg.own_cgroup()})
        start = time.monotonic()
        period = interval_ms / 1000.0
        # Epizodning qattiq chegarasi. Ajratishning ENG ICHKI tsikligacha
        # uzatiladi -- 08 §5 ning sababi aynan shu yerda tugatiladi.
        limit = Deadline(max_seconds, start)
        next_tick = time.monotonic()
        try:
            while not self._stop:
                if limit.expired():
                    break
                if self.alloc.touched_bytes < cap_mb * 1024 * 1024:
                    self.alloc.add(chunk_mb * 1024 * 1024, limit)
                else:
                    # Shiftga yetdik -- issiq ushlash uchun qayta tegamiz.
                    self.alloc.retouch(chunk_mb * 1024 * 1024, limit)
                rate, total = self.current_rate()
                self._emit("pressure_sample", {"mode": "ramp",
                                               "touched_mb": self.alloc.touched_bytes // (1 << 20),
                                               "slice_full_rate2s": rate,
                                               "slice_full_total": total})
                next_tick += period
                d = next_tick - time.monotonic()
                if d > 0:
                    # NEGA min(): tik uyqusi chegaradan OSHIB ketmasligi kerak,
                    # aks holda chegara uyqu uzunligicha kechikardi.
                    time.sleep(min(d, limit.remaining()))
                else:
                    next_tick = time.monotonic()
        finally:
            self._finish(start, limit)
        return 0

    def run_pi(self, target_rate: float, max_seconds: float, cap_mb: int,
               step_mb: int = 16, interval_ms: float = 250.0,
               kp: float = 12.0, ki: float = 3.0,
               base_mb: int | None = None) -> int:
        """PI controller: slice stall ulushini nishon bandida ushlaydi.

        BOSHQARISH O'ZGARUVCHISI: tik'dagi churn bloklari soni (ajratish
        tezligi), ajratilgan hajm EMAS. Ko'ring: Allocator.churn().

        SEKIN sozlash ataylab: PSI 2 s kadensda yangilanadi, demak tez reaksiya
        faqat tebranish (va o'lchovda artefakt) keltiradi.

        Stall bu mexanizmda BURSTY: churn tik'lari orasida stall nolga tushadi.
        Nishon 2 s oynadagi O'RTACHA stall ulushi. Bu PSI ning o'z ta'rifiga
        (vaqt ulushi) mos, lekin treatment silliq emas -- va ERISHILGAN ulush
        har namunada log'lanadi, ya'ni analiz mo'ljallangan emas, haqiqiy
        qiymatdan foydalanadi (PREREGISTRATION.md §9.4).
        """
        self._open_psi()
        adj = set_oom_score_adj(1000)
        block = step_mb * (1 << 20)
        # Baza memory.high dan BIR OZ PAST bo'lishi kerak: ramp bepul bo'ladi
        # (stall yo'q), va pressure faqat churn impulslaridan keladi.
        if base_mb is not None:
            base = base_mb
        else:
            high = cg.read_int(f"{self.cgroup_path}/memory.high")
            if high is None:
                base = min(cap_mb, 128)
            else:
                # high dan ~2 blok past: churn impulsi high dan oshadi, baza esa yo'q
                base = max(16, (high // (1 << 20)) - 2 * step_mb)
        self._emit("pressure_start", {"mode": "pi", "target_rate": target_rate,
                                      "max_seconds": max_seconds, "cap_mb": cap_mb,
                                      "kp": kp, "ki": ki, "step_mb": step_mb,
                                      "base_mb": base, "oom_score_adj": adj,
                                      "cgroup": self.cgroup_path,
                                      "own_cgroup": cg.own_cgroup()})
        start = time.monotonic()
        period = interval_ms / 1000.0
        # Bir xil chegara mexanizmi `run_ramp` bilan: NEGA ikkisida ham --
        # 08 §5 `run_ramp` ni o'lchadi, lekin sabab (ajratish ichidagi
        # throttling uyqusi) rejimdan mustaqil, va pilot aynan `pi` rejimida
        # ishlaydi (§11). Faqat `run_ramp` tuzatilsa pilot yo'li
        # tuzatilmagan qolardi.
        limit = Deadline(max_seconds, start)
        integral = 0.0
        nxt = time.monotonic()
        try:
            # Bazani ajratamiz: memory.high dan oshishi KERAK, aks holda churn
            # ajratishlari reclaim yo'liga tushmaydi va pressure bo'lmaydi.
            #
            # LEKIN bu faza uzluksiz ~0.93 stall beradi (anonim xotira +
            # swap=0 bilan reclaim hech narsa bo'shata olmaydi). Uzluksiz
            # yuqori stall guard'ning runaway chegarasini uradi, shuning uchun
            # bloklar orasida PAUZA qo'yiladi -- stall bo'linadi va 2 s oynadagi
            # o'rtacha chegaradan past qoladi.
            # Baza endi memory.high dan past, demak ramp stall bermaydi.
            # Kichik pauza faqat PSI oynasi to'lishi uchun.
            ramp_pause = 0.05
            # NEGA BU TSIKLDA HAM `limit`: avval bu tsikl chegarani UMUMAN
            # tekshirmasdi -- `max_seconds` faqat quyidagi control tsiklida
            # ko'rilardi. Baza ajratishi throttling'ga tushsa (02 §3: baza
            # `memory.high` ga yaqin), epizod control tsikliga YETMASDAN ham
            # chegaradan oshib ketardi. Bu 08 §5 ning ikkinchi, o'lchanmagan
            # yo'li.
            while self.alloc.touched_bytes < base * (1 << 20) and not self._stop:
                if limit.expired():
                    break
                self.alloc.add(block, limit)
                r, tot = self.current_rate()
                self._emit("pressure_ramp",
                           {"touched_mb": self.alloc.touched_bytes // (1 << 20),
                            "target_base_mb": base,
                            "slice_full_rate2s": r, "slice_full_total": tot})
                time.sleep(min(ramp_pause, limit.remaining()))
            while not self._stop:
                if limit.expired():
                    break
                rate, total = self.current_rate()
                churned = 0
                if rate is None:
                    # 2 s oyna hali to'lmagan: o'rtacha churn bilan boshlaymiz.
                    churned = self.alloc.churn(2, block, limit)
                    err = None
                else:
                    err = target_rate - rate
                    integral = max(-5.0, min(5.0, integral + err * period))
                    effort = kp * err + ki * integral
                    n = int(max(0.0, effort))
                    if n > 0:
                        churned = self.alloc.churn(n, block, limit)
                    # n == 0 bo'lsa: hech narsa ajratmaymiz -> stall tushadi.
                self._emit("pressure_sample",
                           {"mode": "pi",
                            "touched_mb": self.alloc.touched_bytes // (1 << 20),
                            "slice_full_rate2s": rate,
                            "slice_full_total": total,
                            "err": err, "integral": integral,
                            "churned_blocks": churned})
                nxt += period
                d = nxt - time.monotonic()
                if d > 0:
                    time.sleep(min(d, limit.remaining()))
                else:
                    nxt = time.monotonic()
        finally:
            self._finish(start, limit)
        return 0

    def _finish(self, start: float, limit: Deadline | None = None) -> None:
        """Epizodni yopadi va OSHIB KETISHNI qayd etadi.

        NEGA `overrun_s`: 08 §5 ning oshib ketishi (5 s so'rov -> 16.3 s)
        generator log'idan EMAS, keyin `psi.csv` dan qayta hisoblash bilan
        topilgan -- generator o'z log tsiklini to'xtatgani uchun. Endi
        chegaradan qancha oshganini epizodning O'ZI yozadi, demak qoldiq
        cheklanmagan oyna (modul izohi) taxmin emas, o'lchov bo'ladi.
        `None` = o'lchanmagan (chegara berilmagan), `0` = o'lchangan nol.
        """
        mb = self.alloc.touched_bytes // (1 << 20)
        self.alloc.release_all()
        if self._psi is not None:
            self._psi.close()
        elapsed = time.monotonic() - start
        overrun: float | None = None
        limit_s: float | None = None
        if limit is not None:
            limit_s = limit.seconds
            overrun = max(0.0, elapsed - limit.seconds)
        self._emit("pressure_stop", {"touched_mb_at_stop": mb,
                                     "elapsed_s": elapsed,
                                     "max_seconds": limit_s,
                                     "overrun_s": overrun})
        if self.writer is not None:
            self.writer.flush()

    def install_signals(self) -> None:
        def _h(_s: int, _f: object) -> None:
            self._stop = True
        signal.signal(signal.SIGTERM, _h)
        signal.signal(signal.SIGINT, _h)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="REVIX memory pressure generatori")
    ap.add_argument("--mode", choices=("ramp", "pi"), default="ramp")
    ap.add_argument("--cgroup", default=None,
                    help="PSI o'qiladigan cgroup (default: o'zining cgroup'i)")
    ap.add_argument("--target-rate", type=float, default=0.3, help="pi rejimi uchun")
    ap.add_argument("--chunk-mb", type=int, default=32)
    ap.add_argument("--step-mb", type=int, default=16)
    ap.add_argument("--interval-ms", type=float, default=250.0)
    ap.add_argument("--cap-mb", type=int, default=1024, help="ajratish shifti")
    ap.add_argument("--base-mb", type=int, default=None,
                    help="pi rejimi uchun rezident baza (memory.high dan yuqori bo'lishi kerak)")
    ap.add_argument("--max-seconds", type=float, required=True,
                    help="QATTIQ chegara; systemd RuntimeMaxSec= ga qo'shimcha")
    ap.add_argument("--log", default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--session-id", default="adhoc")
    args = ap.parse_args(argv)

    cgroup = args.cgroup or f"{cg.CGROUP_ROOT}{cg.own_cgroup()}"
    writer = JsonlWriter(args.log) if args.log else None
    emitter = Emitter("pressure", args.run_id or new_run_id(), args.session_id) if writer else None

    gen = PressureGenerator(cgroup, writer, emitter)
    gen.install_signals()
    try:
        if args.mode == "ramp":
            return gen.run_ramp(args.chunk_mb, args.interval_ms, args.max_seconds, args.cap_mb)
        return gen.run_pi(args.target_rate, args.max_seconds, args.cap_mb,
                          args.step_mb, args.interval_ms, base_mb=args.base_mb)
    finally:
        if writer:
            writer.close()


if __name__ == "__main__":
    sys.exit(main())
