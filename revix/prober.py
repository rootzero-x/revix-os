"""REVIX o'lchov prober'i -- failure va Verified Recovery ta'riflarining ASBOBI.

Bu fayl `PREREGISTRATION.md` §2 (service contract), §3 (failure detektori
`F_probe`) va `docs/architecture/03-sut-protokoli.md` §8 (prober shartlari) ni
amalga oshiradi. Loyihaning ilmiy hissasi o'lchov bo'lgani uchun, bu fayldagi
qaror mantiqi -- eksperimentning o'zi. Shuning uchun har bir tasnif qarori
yopiq enum'dan chiqadi va hech qanday holat jimgina "yaxshi" deb hisoblanmaydi.

DIZAYN QOIDALARI (buzilmaydi):

  1. **Absolut `CLOCK_MONOTONIC` deadline'lar.** `sleep(P)` ISHLATILMAYDI:
     u har tsiklda probe'ning o'z vaqtini (connect + round-trip + serializatsiya)
     davrga qo'shadi, ya'ni haqiqiy davr P dan katta bo'ladi va xato YIG'ILADI.
     `D_probe` ±P kvantlash bilan beriladi (§6.1) -- agar davr sekin-asta
     siljisa, kvantlash chegarasi yolg'on bo'lardi. Shuning uchun keyingi
     deadline hisoblanadi va faqat QOLGAN vaqt uxlanadi; kechikilsa faza
     saqlanib butun P karralari bilan oldinga siljiydi (grid P ga tekis
     qoladi, demak yo'qolgan tsikllar butun P sifatida sanaladi).

  2. **Har probe'da YANGI ulanish** (`03-sut-protokoli.md` §1). Ulanish qayta
     ishlatilsa contract'ning (a) bandi -- "socket `T_conn` ichida accept
     qiladi" -- umuman o'lchanmagan bo'lardi.

  3. **Tasnif yopiq enum** (`OUTCOMES`): `ok`, `conn_refused`, `conn_timeout`,
     `rt_timeout`, `bad_response`, `no_progress`. Yangi holat qo'shilmaydi;
     tanilmagan holat istisno bo'ladi, jimgina `ok` bo'lmaydi.

  4. **`invocation` o'zgarsa `progress` kamayishi NORMAL** -- restart 0 dan
     boshlaydi (protokol §4.4). Bu holat `no_progress` DEYILMAYDI. Aks holda
     restart'dan keyingi birinchi probe soxta failure bo'lib, downtime
     o'lchovi jimgina buzilardi. Bu shu fayldagi eng kritik shart.

  5. **Instrumentatsiya xatosi service failure EMAS.** Prober o'zi socket
     ocholmasa (ENOMEM/ENOBUFS/EMFILE -- pressure ostida real xavf), yoki
     yo'l/huquq xato bo'lsa (EACCES/ENOTSOCK) -- bu `conn_refused` deb
     YOZILMAYDI. U `harness_error` bo'ladi, ketma-ket buzilish hisoblagichiga
     TEGMAYDI va CSV'ga qator yozilmaydi. Aks holda xotira siqilishi
     prober'ning o'z xatosini "xizmat ishdan chiqdi" deb ko'rsatib, natijani
     aynan H1 foydasiga siljitardi (§8.1 dagi yashirin o'zgaruvchi).

  6. **Hech qachon istisnodan yiqilmaydi.** Muvaffaqiyatsiz probe -- ma'lumot,
     xato emas. Kutilmagan istisno `harness_error` sifatida yoziladi va tsikl
     davom etadi (§4: instrumentatsiya yo'qolishi hech qachon jimgina
     natijaga aylanmaydi).

  7. **Qaror yo'liga ulanmaydi** (§5 sirkulyarlik kafolati 2). Prober faqat
     o'lchaydi va yozadi; hech bir arm'ning harakatini tanlamaydi, uchala
     arm'da bir xil ishlaydi va o'z narxini o'zi hisobotda beradi (§8.2).

Ikki target probe qilinadi: SUT va **bystander**. Bystander -- spillover
detektori: u contract'ni yo'qotsa, trial'da collateral damage bo'lgan va
disposition `contaminated` bo'ladi (§12).

--------------------------------------------------------------------------
`probe_sample` CSV ustunlari (`PROBE_FIELDS`, fiksa sxema, tartib muhim)
--------------------------------------------------------------------------
  mono_us_send        probe boshlanishi (connect'dan OLDIN), CLOCK_MONOTONIC us.
                      Bu probe'ning kanonik vaqti va `t_detect` manbai (§3).
  mono_us_req         connect tugagandan keyin, PROBE yuborilishidan oldin.
                      Bo'sh = ulanish bo'lmadi.
  mono_us_recv        javob olingan vaqt. Bo'sh = javob kelmadi.
  real_us_send        CLOCK_REALTIME, FAQAT tashqi log bilan bog'lash uchun (§1).
  target              target nomi (`sut`, `bystander`, ...).
  outcome             yopiq enum: OUTCOMES.
  clause_failed       buzilgan contract bandi: a_conn | b_response | c_progress.
                      `ok` da bo'sh.
  conn_us             connect davomiyligi (muvaffaqiyatsizlikda ham o'lchanadi).
  rt_us               PROBE -> javob davomiyligi (T_rt shu bandga qo'llanadi).
  rtt_us              mono_us_recv - mono_us_send (to'liq probe narxi).
  progress_counter    javobdagi `progress` (u64).
  progress_delta      oldingi probe'dan farq. Bo'sh = taqqoslanmaydi
                      (birinchi probe yoki yangi invocation).
  invocation_id_seen  javobdagi `invocation` -- restart race'ini yopadi (§8).
  sut_pid_seen        javobdagi `pid`.
  rss_kb_seen         javobdagi `rss_kb` (ixtiyoriy maydon).
  sut_mono_us         SUT ning o'z CLOCK_MONOTONIC vaqti (clock skew tekshiruvi).
  restart_seen        1 = bu probe yangi invocation'ni ko'rdi.
  fail_streak         shu target uchun ketma-ket buzilish soni (0 = ok).
  errno               socket errno (bo'lsa).
  err_reason          `bad_response` sababi yoki errno nomi.
  resp_len            javob baytlari soni.
  cycle               probe tsikli indeksi (bir tsiklda har target bir marta).
  seq                 TARGET bo'yicha monotonik -- bo'shliq = yo'qolgan qator.
  trial_id            driver o'rnatadigan trial identifikatori.

CSV'da `run_id`/`boot_id` yo'q (psi_sample bilan bir uslub): 10 Hz × 2 target
da ular faylni ~70 MB ga oshirardi. Fayl `prober_start` record'i orqali
run'ga bog'lanadi -- u envelope'da `run_id`, `boot_id`, `csv_path` ni beradi.
"""

from __future__ import annotations

import argparse
import errno
import os
import resource
import signal
import socket
import sys
import time
import traceback
from typing import Any

from .schema import CsvWriter, Emitter, JsonlWriter, mono_us, new_run_id, real_us

# --- muzlatilgan parametrlar (PREREGISTRATION.md §2, §3) ---------------------

PROBE_HZ = 10.0          # P = 100 ms
T_CONN_S = 0.050         # contract bandi (a)
T_RT_S = 0.050           # contract bandi (b)
K_F = 3                  # F_probe: ketma-ket buzilish soni -> D_f = 300 ms
MAX_MSG = 4096           # protokol §1
PROBE_REQUEST = b"PROBE"
PROBE_COST_BUDGET_PERCENT = 1.0   # §8.2: >1% yadro bo'lsa sekinlashtiriladi

# --- yopiq enum'lar ---------------------------------------------------------

OUTCOMES = (
    "ok",
    "conn_refused",
    "conn_timeout",
    "rt_timeout",
    "bad_response",
    "no_progress",
)

# Contract bandlari (PREREGISTRATION.md §2). Detection record qaysi BAND
# buzilganini yozadi -- "failure" so'zi mexanizmni yo'qotmasligi uchun.
CLAUSE_A = "a_conn"        # socket T_conn ichida accept qiladi
CLAUSE_B = "b_response"    # to'g'ri formatdagi javob T_rt ichida keladi
CLAUSE_C = "c_progress"    # progress oldingi probe'dan qat'iy katta

OUTCOME_CLAUSE = {
    "ok": None,
    "conn_refused": CLAUSE_A,
    "conn_timeout": CLAUSE_A,
    "rt_timeout": CLAUSE_B,
    "bad_response": CLAUSE_B,
    "no_progress": CLAUSE_C,
}

PROBE_FIELDS = (
    "mono_us_send",
    "mono_us_req",
    "mono_us_recv",
    "real_us_send",
    "target",
    "outcome",
    "clause_failed",
    "conn_us",
    "rt_us",
    "rtt_us",
    "progress_counter",
    "progress_delta",
    "invocation_id_seen",
    "sut_pid_seen",
    "rss_kb_seen",
    "sut_mono_us",
    "restart_seen",
    "fail_streak",
    "errno",
    "err_reason",
    "resp_len",
    "cycle",
    "seq",
    "trial_id",
)

# Har probe'da `dict.fromkeys(PROBE_FIELDS)` 24 ta kalitni QAYTA xeshlab yangi
# jadval quradi; tayyor shablonning `copy()`si jadvalni ko'chiradi -- o'lchangan
# farq 855 ns -> 160 ns (python3.14, 200k iteratsiya, thread_time).
#
# NEGA (§8.2 "probe narxi budjeti"): prober'ning CPU'si o'lchanayotgan tizimdan
# O'G'IRLANGAN CPU. Har probe'da tejalgan har bir mikrosekund self-perturbation
# budjetiga qaytadi, demak bu yerda "kichik" tejash ham qonuniy.
#
# Shablon O'QILADIGAN holatda qoladi: `copy()` har probe'ga MUSTAQIL dict
# beradi, demak qatorlar bir-birining qiymatini ko'rmaydi. Shablonning o'zi
# hech qachon yozilmaydi.
_ROW_TEMPLATE = dict.fromkeys(PROBE_FIELDS)

# --- errno tasnifi ----------------------------------------------------------
# Bu jadval qaror: qaysi errno XIZMAT haqida gapiradi va qaysisi PROBER
# haqida. Ikkinchisi hech qachon contract buzilishi deb yozilmaydi (dizayn
# qoidasi 5).

# Xizmat ulanishni qabul qilmadi: socket yo'q yoki rad etildi.
CONN_REFUSED_ERRNOS = frozenset({
    errno.ECONNREFUSED,   # bind qilingan lekin listen qilmagan yoki o'lgan
    errno.ENOENT,         # socket fayli yo'q (SIGTERM'da o'chirilgan)
    errno.ECONNRESET,
    errno.ECONNABORTED,
    errno.ENOTCONN,
    errno.ESHUTDOWN,
    errno.EPIPE,
})

# Xizmat listen qiladi, lekin accept qilib yetishmadi (backlog to'la) ->
# bu "T_conn ichida accept qilmadi" ning aynan o'zi.
CONN_TIMEOUT_ERRNOS = frozenset({
    errno.ETIMEDOUT,
    errno.EAGAIN,
    errno.EINPROGRESS,
    errno.EALREADY,
})

# PROBER ning o'z muammosi -> harness_error, contract buzilishi EMAS.
INSTRUMENT_ERRNOS = frozenset({
    errno.ENOMEM,          # pressure ostida real: socket ajratilmadi
    errno.ENOBUFS,
    errno.EMFILE,          # prober fd tugatdi
    errno.ENFILE,
    errno.EACCES,          # socket huquqi / yo'l xatosi -> konfiguratsiya
    errno.EPERM,
    errno.ENOTSOCK,
    errno.EAFNOSUPPORT,
    errno.ENAMETOOLONG,
    errno.ENOTDIR,
    errno.ELOOP,
})

_HEX = frozenset("0123456789abcdefABCDEF")


class ProbeInstrumentError(Exception):
    """Prober'ning O'Z xatosi -- xizmat contract'i haqida hech narsa demaydi."""


# --- javob parseri ----------------------------------------------------------


def parse_probe_reply(blob: bytes) -> tuple[dict[str, Any] | None, str | None]:
    """`OK ...` javobini parse qiladi.

    Qaytadi: (maydonlar, None) yoki (None, sabab). Sabab `bad_response`
    qatoriga `err_reason` sifatida yoziladi -- "noto'g'ri javob" ning NEGA
    ekani post-hoc tahlilda tiklanishi kerak.

    Qat'iylik qarori: o'lchov uchun ZARUR maydonlar (`progress`, `pid`,
    `invocation`) yo'q yoki yaroqsiz bo'lsa -> `bad_response`. Ixtiyoriy
    maydonlar (`rss_kb`, `mono_us`) yo'q bo'lsa javob YAROQLI hisoblanadi:
    ular contract bandi (b) ga kirmaydi va ularni talab qilish parallel
    yozilgan `sut.c` ga qarshi soxta failure yaratish xavfini tug'dirardi.

    `invocation` uzunligi tekshirilmaydi (protokol hex32 deydi, lekin
    identiklik taqqoslash uchun uzunlik ahamiyatsiz) -- faqat hex bo'lishi
    shart, chunki hex bo'lmagan qiymat parse xatosini yashirardi.
    """
    if not blob:
        # Peer javob bermay ulanishni yopdi (EOF). Band (a) o'tdi, (b) yo'q.
        return None, "eof"
    try:
        text = blob.decode("ascii")
    except UnicodeDecodeError:
        return None, "not_ascii"
    # Protokol satr oxirini yubormaydi, lekin kelsa ham o'lchov buzilmasin:
    # argumentsiz `split()` bo'sh joy YUGURIKLARI bo'yicha bo'ladi va chetdagi
    # bo'sh joyni (shu jumladan satr oxirlarini: LF va CRLF) o'zi tashlaydi --
    # `strip()` ORTIQCHA edi va faqat qo'shimcha satr nusxasini yaratardi
    # (o'lchangan: 278 ns -> 217 ns, python3.14). Natija bayt-bayt bir xil.
    # NEGA: §8.2 budjeti -- har probe'da bajarilmagan ish o'lchanayotgan
    # tizimga qaytgan CPU.
    parts = text.split()
    if not parts:
        return None, "empty"
    head = parts[0]
    if head == "ERR":
        # Protokol darajasida to'g'ri, lekin YAROQLI javob emas: yopiq enum'da
        # alohida holat yo'q, shuning uchun bad_response + sabab saqlanadi.
        return None, "err:" + (parts[1] if len(parts) > 1 else "?")
    if head != "OK":
        return None, "no_ok_prefix"

    kv: dict[str, str] = {}
    for tok in parts[1:]:
        key, sep, val = tok.partition("=")
        if not sep or not key:
            return None, "bad_token"
        kv[key] = val

    out: dict[str, Any] = {}
    for name in ("progress", "pid"):
        raw = kv.get(name)
        if raw is None:
            return None, f"missing:{name}"
        try:
            out[name] = int(raw, 10)
        except ValueError:
            return None, f"bad_int:{name}"
    if out["progress"] < 0:
        return None, "negative:progress"

    inv = kv.get("invocation")
    if inv is None:
        return None, "missing:invocation"
    if not inv or not set(inv) <= _HEX:
        return None, "bad_hex:invocation"
    out["invocation"] = inv

    for name in ("rss_kb", "mono_us"):
        raw = kv.get(name)
        if raw is None:
            continue
        try:
            out[name] = int(raw, 10)
        except ValueError:
            out[name] = None   # ixtiyoriy maydon -- javobni yaroqsiz qilmaydi
    return out, None


def _null_invocation(value: str) -> bool:
    """`invocation` ma'lumot tashimaydimi?

    Protokol §3: `$INVOCATION_ID` yo'q bo'lsa SUT 32 ta nol yuboradi. Bunday
    qiymat restart'ni AJRATA OLMAYDI, shuning uchun bu holatda pid zaxira
    guvoh bo'ladi (`Target.restart_seen`).
    """
    return set(value) <= {"0"}


# --- target holati ----------------------------------------------------------


class Target:
    """Bitta probe target'ining holati va ketma-ket buzilish hisoblagichi."""

    def __init__(self, name: str, socket_path: str) -> None:
        self.name = name
        self.socket_path = socket_path
        # seq TARGET bo'yicha alohida oqim: ilmiy birlik -- shu target'ning
        # probe trace'i, va §4 dagi "probe uzilishi > 2xP -> censored"
        # qarori aynan shu trace'dagi bo'shliqqa qaraydi.
        self.stream = f"probe_sample:{name}"
        self.prev_progress: int | None = None
        self.prev_invocation: str | None = None
        self.prev_pid: int | None = None
        self.fail_streak = 0
        self.detected = False
        self.first_fail: dict[str, Any] | None = None
        self.streak_outcomes: list[str] = []

    def restart_seen(self, invocation: str, pid: int) -> bool:
        """Bu javob YANGI invocation'danmi?

        Shunday bo'lsa `progress` ning kamayishi normal (protokol §4.4) va
        `no_progress` DEYILMAYDI.

        `invocation` nol bo'lsa (systemd'siz ishga tushirish) u restart haqida
        hech narsa demaydi -- o'sha holatda pid o'zgarishi yagona guvoh.
        Systemd ostida `INVOCATION_ID` har restart'da o'zgaradi, demak bu
        zaxira yo'l asosiy qarorni hech qachon o'zgartirmaydi.
        """
        if self.prev_invocation is None:
            return False
        if invocation != self.prev_invocation:
            return True
        if _null_invocation(invocation) and pid != self.prev_pid:
            return True
        return False


# --- prober -----------------------------------------------------------------


class Prober:
    def __init__(
        self,
        targets: list[Target],
        csv: CsvWriter,
        events: JsonlWriter | None,
        emitter: Emitter,
        *,
        hz: float = PROBE_HZ,
        t_conn_s: float = T_CONN_S,
        t_rt_s: float = T_RT_S,
        k_f: int = K_F,
        trial_id: str | None = None,
    ) -> None:
        self.targets = targets
        self.csv = csv
        self.events = events
        self.emitter = emitter
        self.period_s = 1.0 / hz
        self.hz = hz
        self.t_conn_s = t_conn_s
        self.t_rt_s = t_rt_s
        self.k_f = k_f
        # Driver ish vaqtida o'rnatadi; har qatorga va har record'ga tushadi.
        self.trial_id = trial_id
        self._stop = False
        self.probes = 0
        self.harness_errors = 0
        self.overruns = 0
        self.skipped_cycles = 0
        self.emit_errors = 0
        self.detections = 0
        self.counts: dict[tuple[str, str], int] = {}
        self._cost_begin = _cost_snapshot()

    # --- yozish (hech qachon yiqilmaydi) ---
    def _emit(self, record_type: str, payload: dict[str, Any]) -> None:
        """Hodisa record'i. Log xatosi o'lchov tsiklini TO'XTATMAYDI.

        Lekin jimgina ham qolmaydi: yutilgan xato sanaladi va `prober_stop`
        da beriladi, aks holda yo'qolgan detection record'i ko'rinmas bo'lardi.
        """
        if self.events is None:
            return
        try:
            self.events.write(self.emitter.record(
                record_type, payload, stream=record_type, trial_id=self.trial_id))
        except Exception:  # noqa: BLE001
            self.emit_errors += 1

    def _harness_error(self, target: str | None, cycle: int | None, exc: BaseException) -> None:
        """Kutilmagan istisno -> ma'lumot, ketma-ket buzilishga TEGMAYDI.

        Instrumentatsiya xatosi service failure sifatida yozilsa, u soxta
        downtime yaratardi. Driver bu record'ni ko'rib trial'ga `harness_error`
        disposition beradi (§12) -- ya'ni xato ko'rinadi, lekin natijaga
        aylanmaydi.
        """
        self.harness_errors += 1
        self._emit("harness_error", {
            "where": "probe",
            "target": target,
            "cycle": cycle,
            "error": repr(exc),
            "traceback": traceback.format_exc(limit=6),
        })

    # --- bitta probe ---
    def probe_once(self, tgt: Target) -> dict[str, Any]:
        """Bitta probe: YANGI ulanish, PROBE, javob, uchala contract bandi.

        Qaytadi: CSV qatori (yozilmaydi). `ProbeInstrumentError` ni ko'tarishi
        mumkin -- u contract buzilishi EMAS (dizayn qoidasi 5).
        """
        row: dict[str, Any] = _ROW_TEMPLATE.copy()
        row["target"] = tgt.name
        row["trial_id"] = self.trial_id
        row["seq"] = self.emitter.next_seq(tgt.stream)
        t0 = mono_us()
        row["mono_us_send"] = t0
        row["real_us_send"] = real_us()

        sock = None
        try:
            # --- band (a): T_conn ichida ulanish ---------------------------
            # Har probe'da yangi socket: aks holda accept vaqti o'lchanmaydi.
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
                sock.settimeout(self.t_conn_s)
                sock.connect(tgt.socket_path)
            except TimeoutError:
                row["conn_us"] = mono_us() - t0
                row["errno"] = errno.ETIMEDOUT
                row["err_reason"] = "conn_deadline"
                return self._settle(row, "conn_timeout")
            except OSError as exc:
                row["conn_us"] = mono_us() - t0
                row["errno"] = exc.errno
                row["err_reason"] = errno.errorcode.get(exc.errno or 0, "unknown")
                if exc.errno in INSTRUMENT_ERRNOS:
                    raise ProbeInstrumentError(
                        f"connect({tgt.socket_path}) instrumentatsiya xatosi: {exc!r}") from exc
                if exc.errno in CONN_TIMEOUT_ERRNOS:
                    return self._settle(row, "conn_timeout")
                if exc.errno in CONN_REFUSED_ERRNOS:
                    return self._settle(row, "conn_refused")
                # Tanilmagan errno jimgina `conn_refused` bo'lmaydi: u
                # harness_error sifatida ko'rinadi va jadval yangilanadi.
                raise ProbeInstrumentError(
                    f"tasniflanmagan connect errno {exc.errno}: {exc!r}") from exc

            t_conn = mono_us()
            row["mono_us_req"] = t_conn
            row["conn_us"] = t_conn - t0

            # --- band (b): T_rt ichida to'g'ri formatdagi javob ------------
            # T_rt ham ABSOLUT deadline: send va recv uchun alohida timeout
            # qo'yilsa, eng yomon holatda 2xT_rt kutilardi va band (b)
            # amalda 100 ms bo'lib qolardi.
            try:
                sock.settimeout(self.t_rt_s)
                sock.send(PROBE_REQUEST)
                left = self.t_rt_s - (mono_us() - t_conn) / 1e6
                if left <= 0:
                    row["rt_us"] = mono_us() - t_conn
                    row["errno"] = errno.ETIMEDOUT
                    row["err_reason"] = "rt_deadline_on_send"
                    return self._settle(row, "rt_timeout")
                sock.settimeout(left)
                blob = sock.recv(MAX_MSG)
            except TimeoutError:
                row["rt_us"] = mono_us() - t_conn
                row["errno"] = errno.ETIMEDOUT
                row["err_reason"] = "rt_deadline"
                return self._settle(row, "rt_timeout")
            except OSError as exc:
                row["rt_us"] = mono_us() - t_conn
                row["errno"] = exc.errno
                row["err_reason"] = errno.errorcode.get(exc.errno or 0, "unknown")
                if exc.errno in INSTRUMENT_ERRNOS:
                    raise ProbeInstrumentError(
                        f"recv({tgt.name}) instrumentatsiya xatosi: {exc!r}") from exc
                # Ulanish o'rnatilgandan keyin uzilish: band (a) o'tdi,
                # band (b) yaroqli javob bermadi.
                return self._settle(row, "bad_response")

            t_recv = mono_us()
            row["mono_us_recv"] = t_recv
            row["rt_us"] = t_recv - t_conn
            row["rtt_us"] = t_recv - t0
            row["resp_len"] = len(blob)

            fields, why = parse_probe_reply(blob)
            if fields is None:
                row["err_reason"] = why
                return self._settle(row, "bad_response")

            progress = fields["progress"]
            invocation = fields["invocation"]
            pid = fields["pid"]
            row["progress_counter"] = progress
            row["invocation_id_seen"] = invocation
            row["sut_pid_seen"] = pid
            row["rss_kb_seen"] = fields.get("rss_kb")
            row["sut_mono_us"] = fields.get("mono_us")

            # --- band (c): progress qat'iy oshdimi -------------------------
            restart = tgt.restart_seen(invocation, pid)
            row["restart_seen"] = 1 if restart else 0
            outcome = "ok"
            if tgt.prev_progress is None or restart:
                # Taqqoslash asosi yo'q (birinchi probe) yoki yangi
                # invocation (hisoblagich 0 dan boshlandi). Delta BO'SH
                # qoldiriladi -- 0 yozilsa u haqiqiy "hech qanday ish
                # bajarilmadi" bilan aralashib ketardi.
                row["progress_delta"] = None
            else:
                delta = progress - tgt.prev_progress
                row["progress_delta"] = delta
                if delta <= 0:
                    # Kamayish HAM shu yerga tushadi: invocation o'zgarmagan
                    # holda kamayish protokol buzilishi, lekin yopiq enum'da
                    # u ham band (c) ning buzilishi.
                    outcome = "no_progress"
            tgt.prev_progress = progress
            tgt.prev_invocation = invocation
            tgt.prev_pid = pid
            return self._settle(row, outcome)
        finally:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass

    def _settle(self, row: dict[str, Any], outcome: str) -> dict[str, Any]:
        if outcome not in OUTCOME_CLAUSE:
            raise ProbeInstrumentError(f"yopiq enum'dan tashqari outcome: {outcome!r}")
        row["outcome"] = outcome
        row["clause_failed"] = OUTCOME_CLAUSE[outcome]
        return row

    # --- ketma-ket buzilish va detection ---
    def track(self, tgt: Target, row: dict[str, Any]) -> None:
        """`F_probe` detektori: `k_f` ketma-ket buzilish -> `detection`.

        `t_detect` -- BIRINCHI buzilgan probe'ning `mono_us_send`i, uchinchisi
        emas (§3). Aks holda har bir detection latency `(k_f-1)·P = 200 ms`
        ga soxta siljigan bo'lardi.
        """
        outcome = row["outcome"]
        if outcome == "ok":
            if tgt.detected:
                # Epizod yopildi. Bu KUZATUV record'i: VR ni prober
                # hisoblamaydi (u W_stab, NRestarts va oom_kill ni ham talab
                # qiladi -- §4), driver hisoblaydi.
                self._emit("contract_restored", {
                    "target": tgt.name,
                    "t_up_mono_us": row["mono_us_send"],
                    "t_detect_mono_us": (tgt.first_fail or {}).get("mono_us_send"),
                    "failing_probes": tgt.fail_streak,
                    "t_up_seq": row["seq"],
                })
            tgt.fail_streak = 0
            tgt.detected = False
            tgt.first_fail = None
            tgt.streak_outcomes = []
            row["fail_streak"] = 0
            return

        tgt.fail_streak += 1
        row["fail_streak"] = tgt.fail_streak
        if tgt.fail_streak == 1:
            tgt.first_fail = {
                "mono_us_send": row["mono_us_send"],
                "outcome": outcome,
                "clause_failed": row["clause_failed"],
                "seq": row["seq"],
                "errno": row["errno"],
                "err_reason": row["err_reason"],
            }
            tgt.streak_outcomes = []
        tgt.streak_outcomes.append(outcome)

        if tgt.fail_streak >= self.k_f and not tgt.detected:
            tgt.detected = True     # epizodga BITTA detection
            self.detections += 1
            first = tgt.first_fail or {}
            now = mono_us()
            self._emit("detection", {
                "detector": "F_probe",
                "target": tgt.name,
                "k_f": self.k_f,
                # t_detect = BIRINCHI buzilgan probe (§3).
                "t_detect_mono_us": first.get("mono_us_send"),
                "first_fail_seq": first.get("seq"),
                "first_outcome": first.get("outcome"),
                "clause_failed": first.get("clause_failed"),
                "first_errno": first.get("errno"),
                "first_err_reason": first.get("err_reason"),
                "streak_outcomes": list(tgt.streak_outcomes),
                "confirm_seq": row["seq"],
                "confirm_mono_us": row["mono_us_send"],
                # Sanity: to'g'ri paced probe'da ~ (k_f-1)·P bo'lishi kerak.
                "confirm_lag_us": (
                    None if first.get("mono_us_send") is None
                    else now - int(first["mono_us_send"])
                ),
                "invocation_id_seen": row["invocation_id_seen"],
                "sut_pid_seen": row["sut_pid_seen"],
            })

    def probe_and_record(self, tgt: Target, cycle: int | None = None) -> dict[str, Any] | None:
        """probe + kuzatuv + CSV. Hech qanday istisno tsiklni to'xtatmaydi."""
        try:
            row = self.probe_once(tgt)
        except Exception as exc:  # noqa: BLE001
            # Instrumentatsiya xatosi: qator YOZILMAYDI (o'lchov bo'lmadi) va
            # fail_streak TEGILMAYDI. seq bo'shligi qoladi -- bu ataylab:
            # yo'qolgan probe ko'rinadigan bo'lishi kerak.
            self._harness_error(tgt.name, cycle, exc)
            return None
        row["cycle"] = cycle
        try:
            self.track(tgt, row)
        except Exception as exc:  # noqa: BLE001
            self._harness_error(tgt.name, cycle, exc)
        try:
            self.csv.write(row)
        except Exception as exc:  # noqa: BLE001
            self._harness_error(tgt.name, cycle, exc)
        self.probes += 1
        key = (tgt.name, row["outcome"])
        self.counts[key] = self.counts.get(key, 0) + 1
        return row

    # --- asosiy tsikl ---
    def run(self, max_seconds: float | None = None) -> int:
        try:
            signal.signal(signal.SIGTERM, self._on_signal)
            signal.signal(signal.SIGINT, self._on_signal)
        except ValueError:
            # Asosiy oqim emas (test/embedded ishlatish). To'xtatish `stop()`
            # orqali bo'ladi.
            pass

        self._cost_begin = _cost_snapshot()
        self._emit("prober_start", {
            "targets": {t.name: t.socket_path for t in self.targets},
            "hz": self.hz,
            "period_s": self.period_s,
            "t_conn_s": self.t_conn_s,
            "t_rt_s": self.t_rt_s,
            "k_f": self.k_f,
            "frozen": {"hz": PROBE_HZ, "t_conn_s": T_CONN_S,
                       "t_rt_s": T_RT_S, "k_f": K_F},
            "frozen_deviation": self.frozen_deviation(),
            "outcomes": list(OUTCOMES),
            "csv_path": self.csv.path,
            "csv_fields": list(PROBE_FIELDS),
            "pid": os.getpid(),
        })

        period = self.period_s
        start = time.monotonic()
        # ABSOLUT deadline. sleep(period) probe narxini davrga qo'shib
        # drift yig'adi -- modul docstring'idagi 1-qoida.
        next_deadline = start
        cycle = 0
        try:
            while not self._stop:
                if max_seconds is not None and time.monotonic() - start >= max_seconds:
                    break
                cycle += 1
                for tgt in self.targets:
                    self.probe_and_record(tgt, cycle)
                    if self._stop:
                        break

                next_deadline += period
                now = time.monotonic()
                late = now - next_deadline
                if late >= period:
                    # BUTUN slot yo'qoldi (masalan ikki target ham T_conn+T_rt
                    # ni to'liq kutdi). Fazani SAQLAB butun P karralari bilan
                    # sakraymiz: grid P ga tekis qolsa, yo'qolgan tsikllar
                    # butun P sifatida sanaladi va §6.1 dagi ±P kvantlash
                    # bayonoti kuchda qoladi. Deadline'ni `monotonic()` ga
                    # tiklash fazani buzardi va kvantlashni tahlil qilib
                    # bo'lmas edi.
                    missed = int(late // period)
                    next_deadline += missed * period
                    self.overruns += 1
                    self.skipped_cycles += missed
                    self._emit("probe_overrun", {
                        "cycle": cycle,
                        "skipped_cycles": missed,
                        "late_us": int(late * 1e6),
                    })
                    # Bu yo'lda `_emit` IO qildi va `next_deadline` siljidi ->
                    # `now` eskirdi, shuning uchun QAYTA o'qiladi.
                    now = time.monotonic()
                # Kichik kechikish (< P) uchun deadline SILJITILMAYDI: keyingi
                # tsikl darhol boshlanadi va grid o'z-o'zidan tuzatiladi.
                # Mikrosekundlik kechikish uchun butun namuna tashlanmaydi.
                #
                # `time.monotonic()` QAYTA chaqirilmaydi: yuqoridagi `now` shu
                # tsikl uchun yetarli -- oddiy yo'lda u bilan bu qator orasida
                # faqat bitta float taqqoslash bor. Bu tsiklga bitta
                # `clock_gettime` ni yo'q qiladi (§8.2 budjeti). Faza
                # O'ZGARMAYDI: sleep davomiyligi ABSOLUT `next_deadline` dan
                # chiqadi, `now` dan emas (dizayn qoidasi 1).
                delay = next_deadline - now
                if delay > 0:
                    time.sleep(delay)
        finally:
            cost = self.cost_report()
            self._emit("prober_stop", {
                "cycles": cycle,
                "probes": self.probes,
                "detections": self.detections,
                "harness_errors": self.harness_errors,
                "overruns": self.overruns,
                "skipped_cycles": self.skipped_cycles,
                "emit_errors": self.emit_errors,
                "outcome_counts": {f"{n}:{o}": c for (n, o), c in sorted(self.counts.items())},
                "cost": cost,
            })
            # Flush: chiqishda hech qanday o'lchov buferda qolmaydi.
            try:
                self.csv.close()
            except Exception:  # noqa: BLE001
                pass
            if self.events is not None:
                try:
                    self.events.flush()
                except Exception:  # noqa: BLE001
                    pass
        return 0

    def stop(self) -> None:
        self._stop = True

    def _on_signal(self, _signum: int, _frame: object) -> None:
        # Faqat flag: signal handler ichida IO qilinmaydi.
        self._stop = True

    # --- §8.2 probe narxi ---
    def frozen_deviation(self) -> dict[str, Any]:
        """Muzlatilgan parametrdan chetlashish -- jimgina qolmasligi kerak."""
        dev: dict[str, Any] = {}
        if abs(self.hz - PROBE_HZ) > 1e-9:
            dev["hz"] = self.hz
        if abs(self.t_conn_s - T_CONN_S) > 1e-9:
            dev["t_conn_s"] = self.t_conn_s
        if abs(self.t_rt_s - T_RT_S) > 1e-9:
            dev["t_rt_s"] = self.t_rt_s
        if self.k_f != K_F:
            dev["k_f"] = self.k_f
        return dev

    def cost_report(self) -> dict[str, Any]:
        """Prober'ning O'Z CPU narxi (PREREGISTRATION.md §8.2).

        Budjet: bir yadroning >1% bo'lsa prober sekinlashtiriladi, va narx
        arm'lar bo'yicha bir xil ushlanadi. Shuning uchun u har run'da
        o'lchanadi va `prober_stop` record'iga yoziladi -- da'vo qilinmaydi.
        """
        now = _cost_snapshot()
        b = self._cost_begin
        wall = now["wall_s"] - b["wall_s"]
        cpu = now["cpu_s"] - b["cpu_s"]
        frac = (cpu / wall) if wall > 0 else None
        return {
            "elapsed_s": wall,
            "cpu_user_s": now["utime_s"] - b["utime_s"],
            "cpu_sys_s": now["stime_s"] - b["stime_s"],
            "cpu_total_s": cpu,
            "core_fraction": frac,
            "core_percent": (frac * 100.0) if frac is not None else None,
            "probes": self.probes,
            "cpu_us_per_probe": (cpu * 1e6 / self.probes) if self.probes else None,
            "budget_percent": PROBE_COST_BUDGET_PERCENT,
            "budget_exceeded": (
                None if frac is None else (frac * 100.0) > PROBE_COST_BUDGET_PERCENT
            ),
            "max_rss_kb": now["max_rss_kb"],
        }


def _cost_snapshot() -> dict[str, float]:
    ru = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "wall_s": time.monotonic(),
        # process_time = user + sys, uxlash hisoblanmaydi.
        "cpu_s": time.process_time(),
        "utime_s": ru.ru_utime,
        "stime_s": ru.ru_stime,
        "max_rss_kb": float(ru.ru_maxrss),
    }


# --- CLI --------------------------------------------------------------------


def default_sut_socket() -> str:
    """Protokol §1: `$REVIX_SUT_SOCKET`, aks holda /run/user/<uid>/."""
    env = os.environ.get("REVIX_SUT_SOCKET")
    if env:
        return env
    return f"/run/user/{os.getuid()}/revix-sut.sock"


def parse_targets(specs: list[str]) -> list[Target]:
    out: list[Target] = []
    seen: set[str] = set()
    for spec in specs:
        name, sep, path = spec.partition("=")
        if not sep or not name or not path:
            raise ValueError(f"--target NOM=SOCKET formatida bo'lishi kerak: {spec!r}")
        if name in seen:
            raise ValueError(f"target nomi takrorlandi: {name!r}")
        seen.add(name)
        out.append(Target(name, path))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="REVIX o'lchov prober'i (10 Hz, SOCK_SEQPACKET)")
    ap.add_argument("--target", action="append", default=[], metavar="NOM=SOCKET",
                    help="takrorlanadi; masalan sut=/run/user/1000/revix-sut.sock "
                         "va bystander=/run/user/1000/revix-bystander.sock")
    ap.add_argument("--csv", required=True, help="probe_sample CSV yo'li")
    ap.add_argument("--events", required=True,
                    help="JSONL: detection / harness_error / start / stop")
    ap.add_argument("--hz", type=float, default=PROBE_HZ)
    ap.add_argument("--t-conn-ms", type=float, default=T_CONN_S * 1000.0)
    ap.add_argument("--t-rt-ms", type=float, default=T_RT_S * 1000.0)
    ap.add_argument("--k-f", type=int, default=K_F)
    ap.add_argument("--max-seconds", type=float, default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--session-id", default="adhoc")
    ap.add_argument("--trial-id", default=None)
    ap.add_argument("--report-cost", action="store_true",
                    help="chiqishda o'z CPU narxini stderr'ga yozadi (§8.2)")
    args = ap.parse_args(argv)

    specs = list(args.target) or [f"sut={default_sut_socket()}"]
    try:
        targets = parse_targets(specs)
    except ValueError as exc:
        ap.error(str(exc))
        return 2   # pragma: no cover -- ap.error chiqib ketadi

    if not any(t.name == "bystander" for t in targets):
        # Bystander -- spillover detektori (§5 harm_indicator). Uni tushirib
        # qoldirish qonuniy (masalan smoke test), lekin JIM bo'lmasligi kerak.
        print("OGOHLIK: bystander target berilmadi -- spillover o'lchanmaydi",
              file=sys.stderr)

    csv = CsvWriter(args.csv, PROBE_FIELDS)
    events = JsonlWriter(args.events)
    em = Emitter("prober", args.run_id or new_run_id(), args.session_id)
    prober = Prober(
        targets, csv, events, em,
        hz=args.hz,
        t_conn_s=args.t_conn_ms / 1000.0,
        t_rt_s=args.t_rt_ms / 1000.0,
        k_f=args.k_f,
        trial_id=args.trial_id,
    )
    dev = prober.frozen_deviation()
    if dev:
        print(f"OGOHLIK: muzlatilgan parametrdan chetlashish: {dev}", file=sys.stderr)
    try:
        rc = prober.run(max_seconds=args.max_seconds)
        if args.report_cost:
            c = prober.cost_report()
            pct = c["core_percent"]
            print(
                "[prober] narx: cpu={:.4f}s wall={:.3f}s yadro={:.3f}% "
                "(budjet {:.1f}%) probes={} cpu/probe={:.0f}us{}".format(
                    c["cpu_total_s"], c["elapsed_s"], pct or 0.0,
                    c["budget_percent"], c["probes"], c["cpu_us_per_probe"] or 0.0,
                    "  BUDJETDAN OSHDI" if c["budget_exceeded"] else "",
                ),
                file=sys.stderr,
            )
        return rc
    finally:
        events.close()


if __name__ == "__main__":
    sys.exit(main())
