"""REVIX record schema va yozuvchilar.

PREREGISTRATION.md §1 (vaqt disiplinasi) va §14 (data schema) ni amalga oshiradi.

Asosiy qoidalar:
  * Barcha davomiylik CLOCK_MONOTONIC mikrosekundda. CLOCK_REALTIME faqat
    inson o'qishi uchun, hisob-kitobda ISHLATILMAYDI.
  * Har record'da boot_id -- monotonic qiymatlar faqat bir boot ichida
    taqqoslanadi, va bu field shu shartni tekshirib bo'ladigan qiladi.
  * Har oqimda seq monotonik hisoblagich -- bo'shliqlar aniqlanadi.
  * JSONL: bitta write() oldindan serializatsiya qilingan bytes, O_APPEND.
    fsync DAVRIY, hech qachon har qatorda -- har qatorda fsync o'lchanayotgan
    tizimga IO kiritadi.
  * Tarix qayta yozilmaydi: field qo'shiladi, hech qachon qayta ishlatilmaydi.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Iterable

SCHEMA_VERSION = 1

# --- vaqt -------------------------------------------------------------------


def mono_us() -> int:
    """CLOCK_MONOTONIC, mikrosekund. Barcha davomiylik hisobining asosi."""
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC) // 1000


def real_us() -> int:
    """CLOCK_REALTIME, mikrosekund. FAQAT inson o'qishi va tashqi log bog'lash
    uchun. Hech qanday davomiylik hisobida ishlatilmaydi."""
    return time.clock_gettime_ns(time.CLOCK_REALTIME) // 1000


def read_boot_id() -> str:
    """Joriy boot identifikatori.

    Monotonic timestamp'lar faqat bitta boot ichida taqqoslanadi. Bu qiymat
    har record'ga yoziladi, shunda validator taqqoslanuvchanlikni tekshiradi.
    """
    with open("/proc/sys/kernel/random/boot_id", "r") as fh:
        return fh.read().strip()


def new_run_id() -> str:
    return uuid.uuid4().hex


# --- JSONL ------------------------------------------------------------------


class JsonlWriter:
    """Append-only JSONL yozuvchi.

    Crash-safe: line-delimited va O_APPEND, demak qismli oxirgi qator
    tashlanadi va undan oldingi record'lar yo'qolmaydi.

    fsync davriy (fsync_interval_s), har qatorda emas -- aks holda o'lchanayotgan
    tizimga IO kiritilardi.
    """

    def __init__(self, path: str, fsync_interval_s: float = 5.0) -> None:
        self.path = path
        self._fsync_interval_s = fsync_interval_s
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        self._fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        self._last_fsync = time.monotonic()

    def write(self, record: dict[str, Any]) -> None:
        # Oldindan serializatsiya qilinadi, keyin BITTA write() -- qism-qism
        # yozish qatorni bo'lib yuborishi mumkin.
        blob = (json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
        os.write(self._fd, blob)
        now = time.monotonic()
        if now - self._last_fsync >= self._fsync_interval_s:
            os.fsync(self._fd)
            self._last_fsync = now

    def flush(self) -> None:
        os.fsync(self._fd)
        self._last_fsync = time.monotonic()

    def close(self) -> None:
        if self._fd >= 0:
            try:
                os.fsync(self._fd)
            finally:
                os.close(self._fd)
                self._fd = -1

    def __enter__(self) -> "JsonlWriter":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# --- CSV --------------------------------------------------------------------


class CsvWriter:
    """Fiksa sxemali yuqori tezlikli oqimlar uchun CSV yozuvchi.

    probe_sample va psi_sample 10 Hz da ishlaydi: ~1-2M qator. JSONL ~5-10x
    bayt va ~3-5x parse vaqti talab qilardi, va serializatsiyaga ketgan CPU --
    eksperimentdan o'g'irlangan CPU.

    Yo'q qiymat bo'sh maydon sifatida yoziladi (NaN yoki 0 emas -- ular
    haqiqiy o'lchov bilan aralashib ketardi).
    """

    def __init__(self, path: str, fieldnames: Iterable[str], flush_interval_s: float = 5.0) -> None:
        self.path = path
        self.fieldnames = list(fieldnames)
        self._flush_interval_s = flush_interval_s
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        is_new = not os.path.exists(path) or os.path.getsize(path) == 0
        self._fh = open(path, "a", buffering=1 << 16, newline="")
        if is_new:
            self._fh.write(",".join(self.fieldnames) + "\n")
        self._last_flush = time.monotonic()

    def write(self, row: dict[str, Any]) -> None:
        out = []
        for name in self.fieldnames:
            v = row.get(name)
            if v is None:
                out.append("")
            elif isinstance(v, float):
                out.append(repr(v))
            elif isinstance(v, str):
                # Vergul/qo'shtirnoq/yangi qator bo'lsa qochirish.
                if any(c in v for c in ',"\n\r'):
                    out.append('"' + v.replace('"', '""') + '"')
                else:
                    out.append(v)
            else:
                out.append(str(v))
        self._fh.write(",".join(out) + "\n")
        now = time.monotonic()
        if now - self._last_flush >= self._flush_interval_s:
            self._fh.flush()
            os.fsync(self._fh.fileno())
            self._last_flush = now

    def flush(self) -> None:
        self._fh.flush()
        os.fsync(self._fh.fileno())
        self._last_flush = time.monotonic()

    def close(self) -> None:
        if not self._fh.closed:
            try:
                self._fh.flush()
                os.fsync(self._fh.fileno())
            finally:
                self._fh.close()

    def __enter__(self) -> "CsvWriter":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# --- envelope ---------------------------------------------------------------


class Emitter:
    """Record envelope'ini qo'yadi va oqim bo'yicha seq hisoblagichini yuritadi.

    seq har OQIM uchun alohida monotonik, shunda validator bo'shliqni
    (yo'qolgan record'ni) aniqlaydi. Bu jimgina ma'lumot yo'qolishini
    imkonsiz qiladi.
    """

    def __init__(
        self,
        name: str,
        run_id: str,
        session_id: str,
        boot_id: str | None = None,
    ) -> None:
        self.name = name
        self.run_id = run_id
        self.session_id = session_id
        self.boot_id = boot_id if boot_id is not None else read_boot_id()
        self.pid = os.getpid()
        self._seq: dict[str, int] = {}

    def next_seq(self, stream: str) -> int:
        n = self._seq.get(stream, 0) + 1
        self._seq[stream] = n
        return n

    def envelope(
        self,
        record_type: str,
        *,
        stream: str | None = None,
        trial_id: str | None = None,
        block_index: int | None = None,
        mono: int | None = None,
    ) -> dict[str, Any]:
        stream = stream or record_type
        return {
            "schema_version": SCHEMA_VERSION,
            "record_type": record_type,
            # stream RECORD'DA SAQLANADI: seq oqim bo'yicha monotonik, demak
            # validator bo'shliqni topish uchun qaysi oqim ekanini bilishi SHART.
            # Busiz u record_type ni proksi sifatida ishlatishga majbur bo'ladi
            # va bitta oqimga ikki xil record yozilsa soxta bo'shliq ko'rsatadi.
            "stream": stream,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "boot_id": self.boot_id,
            "trial_id": trial_id,
            "block_index": block_index,
            "seq": self.next_seq(stream),
            "mono_us": mono if mono is not None else mono_us(),
            "real_us": real_us(),
            "emitter": f"{self.name}:{self.pid}",
        }

    def record(self, record_type: str, payload: dict[str, Any], **kw: Any) -> dict[str, Any]:
        """Envelope + payload. Payload envelope field'larini bosib o'tolmaydi."""
        env = self.envelope(record_type, **kw)
        clash = set(payload) & set(env)
        if clash:
            raise ValueError(f"payload envelope field'larini bosib o'tdi: {sorted(clash)}")
        env.update(payload)
        return env


ENVELOPE_FIELDS = (
    "schema_version",
    "record_type",
    "stream",
    "run_id",
    "session_id",
    "boot_id",
    "trial_id",
    "block_index",
    "seq",
    "mono_us",
    "real_us",
    "emitter",
)

# Trial disposition -- YOPIQ enum (PREREGISTRATION.md §12).
# Har trial'ga AYNAN bittasi. Bu jimgina eksklyuziyaning oldini oladi.
DISPOSITIONS = (
    "complete",
    "censored",
    "contaminated",
    "aborted_guard",
    "washout_timeout",
    "harness_error",
)
