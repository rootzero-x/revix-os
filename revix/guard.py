"""REVIX xavfsizlik guard'i -- MUSTAQIL jarayon.

Vazifasi bitta: pressure eksperimenti `systemd-oomd` ni qo'zg'atib
foydalanuvchining ilovalarini (brauzer, editor, desktop sessiyasi) o'ldirishiga
YO'L QO'YMASLIK.

Bu xavf gipoteza emas, tasdiqlangan:
  /usr/lib/systemd/system/user@.service.d/10-oomd-user-service-defaults.conf
      ManagedOOMMemoryPressure=kill
      ManagedOOMMemoryPressureLimit=50%
  oomd.conf: DefaultMemoryPressureDurationSec=20s
PSI ierarxik, demak revixlab.slice ichidagi stall yuqoriga user@UID.service
ga tarqaladi.

DIZAYN QOIDALARI (buzilmaydi):
  1. MUSTAQIL jarayon. Driver'dan alohida ishga tushadi, driver'ga hech qanday
     bog'liqligi yo'q. Qotib qolgan driver guard'ni o'chira olmasligi kerak.
  2. Birinchi start, oxirgi stop.
  3. FAIL-CLOSED. PSI o'qilmasa, chegara noaniq bo'lsa yoki kutilmagan istisno
     bo'lsa -- TRIP qiladi. Xato holatda "hammasi yaxshi" deb hisoblamaydi.
  4. Repo'dagi eng sodda fayl. Bu yerda ayyorlik qilinmaydi.
  5. Hech qachon istisnodan yiqilmaydi: yozish xatolari yutiladi, asosiy tsikl
     har qanday istisnoni trip'ga aylantiradi.

PRIVILEGIYA CHEKLOVI (halol bayon): guard'ning o'zini oomd/OOM killer'dan
himoya qilish uchun oom_score_adj ni PASAYTIRISH kerak, bu esa privilegiya
talab qiladi. Privilegiyasiz faqat OSHIRISH mumkin. Shuning uchun guard
kichik xotira izi bilan ishlaydi (oomd eng yirik iste'molchini tanlaydi),
lekin bu KAFOLAT emas. To'liq kafolat uchun harness system slice'ga
ko'chirilishi kerak (ManagedOOMMemoryPressure=auto) -- sudo talab qiladi.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time

from . import cgroup as cg
from .schema import Emitter, JsonlWriter, mono_us, new_run_id

# --- chegaralar -------------------------------------------------------------
# Konservativ: oomd 50% da 20 s sustained'da o'ldiradi. Biz ancha oldin
# to'xtatamiz, chunki noto'g'ri trip (trial yo'qoladi) noto'g'ri o'tkazib
# yuborishdan (foydalanuvchi ilovasi o'ladi) ancha arzon.

# Chegaralar KALIBRATSIYA bilan aniqlangan, taxmin bilan emas.
# Ko'ring: docs/architecture/02-guard-kalibratsiyasi.md
#
# ASOSIY TOPILMA: desktop bo'sh turganda user@UID.service PSI'si revixlab.slice
# PSI'siga DEYARLI TENG (o'lchangan: 11.05 vs 11.41). Sabab -- PSI `full` faqat
# non-idle task'larni hisoblaydi; Claude/Chrome idle bo'lganda yagona non-idle
# task generator bo'ladi.
#
# Natijasi: pilotning P2 bandi (60-80% slice stall) user@ ni ham 60-80% ga
# ko'taradi. Agar guard oniy pressure'da trip qilsa, u HAR BIR P2 trial'ini
# o'ldiradi va eksperimentni imkonsiz qiladi.
#
# Shuning uchun guard'ning asosiy himoyasi oniy chegara EMAS, balki oomd ning
# o'z kriteriyasini aks ettiruvchi DAVOMIYLIK chegarasi:
#   oomd:  avg10 >=50%, 20 s davomida        -> kill
#   guard: 2s tezlik >=35%, 15 s davomida     -> kill
#
# 15 s tanlangan: pilot hold <=12 s + ramp <=3 s = eng yomon holatda 15 s, demak
# TO'G'RI ishlayotgan trial hech qachon trip qilmaydi. Qotib qolgan generator
# esa 15 s da to'xtatiladi.
#
# Zaxira KATTA, chunki ikki soat boshqacha yuradi: oomd ning hisoblagichi avg10
# 50% dan oshgandan keyin boshlanadi, avg10 esa haqiqiy tezlikka yetishi uchun
# ~10 s kerak. Ya'ni 0.6 tezlikda qotgan generator uchun oomd ~28-30 s da
# ishlardi; guard 15 s da to'xtatadi.
#
# Oniy chegaralar RUNAWAY tutuvchi sifatida qoladi -- to'liq qotish holati.
DEFAULTS = {
    # Davomiylik himoyasi (ASOSIY). Tezlik `total=` dan olinadi, avgN emas:
    # avgN pressure to'xtagandan keyin ham sekin pasayadi va soxta davomiylik
    # yig'ardi.
    "sustain_rate_threshold": 0.35,
    "sustain_max_seconds": 15.0,
    # Oniy runaway tutuvchilar -- mo'ljallangan eksperiment bandidan YUQORI.
    "user_full_avg10_max": 85.0,
    "user_some_avg10_max": 90.0,
    "user_full_rate2s_max": 0.98,   # o'lchandi: qonuniy burst 0.93 ga chiqadi
    # host bo'sh xotirasi (kB). Kernel global OOM killer'dan uzoq turish.
    "host_mem_available_min_kb": 1_500_000,
}

POLL_HZ = 10.0  # `total` namunasi
AVG_CHECK_HZ = 1.0  # avgN tekshiruvi (avgN 2 s kadensda yangilanadi)
RATE_WINDOW_US = 2_000_000  # PSI kvantlash sababli <2 s oyna ma'nosiz


class Guard:
    def __init__(
        self,
        lab_cgroup: str,
        watch_cgroup: str,
        writer: JsonlWriter,
        emitter: Emitter,
        trip_file: str | None,
        thresholds: dict[str, float],
    ) -> None:
        self.lab_cgroup = lab_cgroup
        self.watch_cgroup = watch_cgroup
        self.writer = writer
        self.emitter = emitter
        self.trip_file = trip_file
        self.th = thresholds
        self.tripped = False
        self._stop = False
        # `total` tarixining halqasi: (mono_us, full_total)
        self._hist: list[tuple[int, int]] = []
        self._oom_kill_baseline = cg.vmstat().get("oom_kill", 0)
        # Lab cgroup'ining O'Z oom_kill hisobi. Cheklangan cgroup OOM ham
        # global /proc/vmstat oom_kill ni oshiradi, demak global o'sishni
        # lab'ning o'z o'sishidan AYIRISH kerak -- aks holda kutilgan,
        # cheklangan OOM (fault class 3) host OOM deb xato talqin qilinardi.
        self._lab_oom_baseline = cg.read_keyed(
            f"{lab_cgroup}/memory.events").get("oom_kill", 0)
        # Chegaradan yuqori pressure UZLUKSIZ boshlangan vaqt (mono_us).
        # Pressure chegaradan pastga tushsa tiklanadi.
        self._sustain_since: int | None = None

    # --- yozish (hech qachon yiqilmaydi) ---
    def _emit(self, record_type: str, payload: dict) -> None:
        try:
            self.writer.write(self.emitter.record(record_type, payload, stream=record_type))
        except Exception:  # noqa: BLE001 -- guard log xatosidan yiqilmaydi
            pass

    # --- TRIP ---
    def trip(self, reason: str, detail: dict) -> None:
        """Eksperiment subtree'sini o'ldiradi va hodisani qayd etadi.

        Idempotent: takroriy trip qayd etiladi, lekin kill qayta urinilmaydi
        (subtree allaqachon o'lgan).
        """
        first = not self.tripped
        self.tripped = True
        killed = None
        if first:
            killed = cg.kill_subtree(self.lab_cgroup)
        self._emit(
            "guard_event",
            {
                "reason": reason,
                "detail": detail,
                "action": "kill_subtree" if first else "already_tripped",
                "lab_cgroup": self.lab_cgroup,
                "kill_ok": killed,
            },
        )
        if first and self.trip_file:
            try:
                with open(self.trip_file, "w") as fh:
                    json.dump(
                        {"reason": reason, "detail": detail, "mono_us": mono_us()}, fh
                    )
            except OSError:
                pass
        # Guard TO'XTAMAYDI: keyingi buzilishlarni ham kuzatishda davom etadi,
        # chunki kill'dan keyin ham qoldiq pressure bo'lishi mumkin.

    # --- tekshiruvlar ---
    def check_psi(self, psi_file: cg.PsiFile, check_avg: bool) -> None:
        try:
            t, psi = psi_file.sample()
        except Exception as exc:  # noqa: BLE001
            # FAIL-CLOSED: PSI o'qilmasa, xavfsiz deb hisoblanmaydi.
            self.trip("psi_read_failed", {"error": repr(exc)})
            return

        full = psi.get("full")
        some = psi.get("some")
        if full is None or some is None:
            self.trip("psi_incomplete", {"psi": psi})
            return

        # 2 s oynadagi tezlik. ENG TOR >=2 s oyna tanlanadi (eng eski emas) --
        # aks holda oyna 2..8 s orasida suzib, tezlik silliqlanib qolardi va
        # guard sekinlashardi. (Bu xato kalibratsiyada 4.9 s oyna sifatida
        # ko'rindi.)
        self._hist.append((t, int(full["total"])))
        cutoff = t - 3 * RATE_WINDOW_US
        self._hist = [h for h in self._hist if h[0] >= cutoff]
        old = None
        for h in reversed(self._hist):          # eng yangidan eskiga
            if t - h[0] >= RATE_WINDOW_US:
                old = h
                break
        rate = None
        if old is not None:
            rate = cg.stall_fraction(old[1], int(full["total"]), old[0], t)
            if rate is not None and rate >= self.th["user_full_rate2s_max"]:
                self.trip(
                    "user_full_rate2s_runaway",
                    {"rate": rate, "limit": self.th["user_full_rate2s_max"],
                     "window_us": t - old[0]},
                )

        # DAVOMIYLIK himoyasi -- asosiy oomd qarshi mexanizm.
        self._check_sustain(t, rate)

        if check_avg:
            if full["avg10"] >= self.th["user_full_avg10_max"]:
                self.trip("user_full_avg10_runaway",
                          {"avg10": full["avg10"], "limit": self.th["user_full_avg10_max"]})
            if some["avg10"] >= self.th["user_some_avg10_max"]:
                self.trip("user_some_avg10_runaway",
                          {"avg10": some["avg10"], "limit": self.th["user_some_avg10_max"]})

    def _check_sustain(self, t: int, rate: float | None) -> None:
        """Chegaradan yuqori pressure juda uzoq davom etsa trip qiladi.

        Bu oomd ning o'z kriteriyasini aks ettiradi (>=50%, 20 s) lekin qat'iyroq
        (>=35%, 13 s), demak oomd hech qachon o'z chegarasiga yetmaydi.

        `rate` (total= dan, 2 s oyna) ishlatiladi, avgN emas: avgN pressure
        to'xtagandan keyin sekin pasayadi va soxta davomiylik yig'ardi.
        """
        if rate is None:
            return
        if rate >= self.th["sustain_rate_threshold"]:
            if self._sustain_since is None:
                self._sustain_since = t
            elif (t - self._sustain_since) / 1e6 >= self.th["sustain_max_seconds"]:
                self.trip("sustained_pressure",
                          {"rate": rate,
                           "threshold": self.th["sustain_rate_threshold"],
                           "sustained_s": (t - self._sustain_since) / 1e6,
                           "limit_s": self.th["sustain_max_seconds"]})
                self._sustain_since = t   # qayta hisoblash, takroriy spam bo'lmasin
        else:
            self._sustain_since = None

    def check_host(self) -> None:
        mi = cg.meminfo()
        avail = mi.get("MemAvailable")
        if avail is None:
            self.trip("meminfo_unreadable", {})
        elif avail < self.th["host_mem_available_min_kb"]:
            self.trip("host_mem_available", {"available_kb": avail,
                                             "limit_kb": self.th["host_mem_available_min_kb"]})

        # Global OOM o'sishini lab'ning o'z (cheklangan) OOM o'sishidan ayiramiz.
        # Faqat lab tashqarisidagi OOM host xavfini bildiradi.
        oom = cg.vmstat().get("oom_kill")
        lab_oom = cg.read_keyed(f"{self.lab_cgroup}/memory.events").get("oom_kill", 0)
        if oom is not None:
            global_delta = oom - self._oom_kill_baseline
            lab_delta = lab_oom - self._lab_oom_baseline
            outside = global_delta - lab_delta
            if outside > 0:
                self.trip("kernel_oom_kill_outside_lab",
                          {"global_delta": global_delta, "lab_delta": lab_delta,
                           "outside": outside, "oom_kill": oom, "lab_oom_kill": lab_oom})
            self._oom_kill_baseline = oom
            self._lab_oom_baseline = lab_oom

        # Slice'da swap ishlatilishi -- konfiguratsiya xatosi.
        # MemorySwapMax=0 bo'lishi kerak; nolga teng bo'lmagan qiymat
        # 5.5 GiB swap to'lib host-wide IO yaratilishi xavfini bildiradi.
        swap = cg.read_int(f"{self.lab_cgroup}/memory.swap.current")
        if swap is not None and swap > 0:
            self.trip("lab_swap_used", {"swap_current": swap})

    # --- asosiy tsikl ---
    def run(self, max_seconds: float | None = None) -> int:
        signal.signal(signal.SIGTERM, self._on_signal)
        signal.signal(signal.SIGINT, self._on_signal)

        watch_psi = f"{self.watch_cgroup}/memory.pressure"
        self._emit(
            "guard_start",
            {
                "watch_cgroup": self.watch_cgroup,
                "lab_cgroup": self.lab_cgroup,
                "thresholds": self.th,
                "poll_hz": POLL_HZ,
                "own_cgroup": cg.own_cgroup(),
                "pid": os.getpid(),
                "oom_kill_baseline": self._oom_kill_baseline,
                "lab_oom_kill_baseline": self._lab_oom_baseline,
                "sustain_design": "oomd: avg10>=50%/20s -> guard: rate2s>=35%/15s",
            },
        )

        try:
            psi_file = cg.PsiFile(watch_psi)
        except OSError as exc:
            # FAIL-CLOSED: kuzatish mumkin bo'lmasa, eksperiment boshlanmasligi
            # kerak. Subtree'ni o'ldirib xato bilan chiqamiz.
            self.trip("watch_open_failed", {"path": watch_psi, "error": repr(exc)})
            self.writer.flush()
            return 2

        start = time.monotonic()
        period = 1.0 / POLL_HZ
        avg_every = max(1, int(POLL_HZ / AVG_CHECK_HZ))
        host_every = avg_every  # host tekshiruvi ham 1 Hz
        i = 0
        # Absolut deadline: sleep(period) drift yig'adi.
        next_deadline = time.monotonic()
        try:
            while not self._stop:
                if max_seconds is not None and time.monotonic() - start >= max_seconds:
                    break
                try:
                    self.check_psi(psi_file, check_avg=(i % avg_every == 0))
                    if i % host_every == 0:
                        self.check_host()
                except Exception as exc:  # noqa: BLE001
                    # FAIL-CLOSED: kutilmagan istisno ham trip.
                    self.trip("guard_exception", {"error": repr(exc)})
                i += 1
                next_deadline += period
                delay = next_deadline - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
                else:
                    # Kechikib qoldik -- deadline'ni tiklaymiz va qayd etamiz.
                    next_deadline = time.monotonic()
        finally:
            psi_file.close()
            self._emit("guard_stop", {"tripped": self.tripped,
                                      "iterations": i,
                                      "elapsed_s": time.monotonic() - start})
            self.writer.flush()
        return 1 if self.tripped else 0

    def _on_signal(self, signum: int, _frame: object) -> None:
        self._stop = True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="REVIX xavfsizlik guard'i (mustaqil jarayon)")
    ap.add_argument("--lab-cgroup", default=None,
                    help="o'ldiriladigan cgroup (default: user@UID.service/revixlab.slice)")
    ap.add_argument("--watch-cgroup", default=None,
                    help="kuzatiladigan cgroup (default: user@UID.service)")
    ap.add_argument("--log", required=True, help="JSONL log fayli")
    ap.add_argument("--trip-file", default=None, help="trip bo'lganda yoziladigan fayl")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--session-id", default="adhoc")
    ap.add_argument("--max-seconds", type=float, default=None,
                    help="shu vaqtdan keyin to'xtash (test uchun)")
    for k, v in DEFAULTS.items():
        ap.add_argument(f"--{k.replace('_', '-')}", type=float, default=v)
    args = ap.parse_args(argv)

    lab = args.lab_cgroup or cg.user_child("revixlab.slice")
    watch = args.watch_cgroup or cg.user_service_cgroup()
    th = {k: getattr(args, k) for k in DEFAULTS}

    writer = JsonlWriter(args.log)
    emitter = Emitter("guard", args.run_id or new_run_id(), args.session_id)
    guard = Guard(lab, watch, writer, emitter, args.trip_file, th)
    try:
        return guard.run(max_seconds=args.max_seconds)
    finally:
        writer.close()


if __name__ == "__main__":
    sys.exit(main())
