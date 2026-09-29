"""systemd transient unit boshqaruvchisi -- yaratish, kuzatish, yig'ishtirish.

Bu modulda EKSPERIMENT SIYOSATI YO'Q. U arm'lar, pressure darajalari yoki
trial jadvali haqida hech narsa bilmaydi. U faqat systemd bilan gaplashadi va
o'lchov uchun yaroqli ma'lumot qaytaradi. Siyosat driver'da.

DIZAYN QARORLARI (empirik asosda -- docs/architecture/01-muhit-tekshiruvlari.md):

  * D-Bus `StartTransientUnit`, `systemd-run` fork qilish EMAS.
    Sabab ikkita: (a) har trial'da fork/exec narxi o'lchov yo'lida bo'lardi;
    (b) D-Bus job natijasini (`JobRemoved` -> `done`/`failed`/`timeout`)
    sinxron qaytaradi, demak "start chaqirig'i qaytdi" va "start haqiqatan
    tugadi" ni aralashtirmaydi.

  * `~/.config/systemd/user/` ga HECH QANDAY fayl yozilmaydi. Barcha
    property'lar transient (`StartTransientUnit`) yoki runtime-only
    (`SetUnitProperties(runtime=True)` -> /run/.../user.control). Persistent
    drop-in qoldirish keyingi run'ni jimgina kontaminatsiya qilardi.

  * VAQT: systemd'ning `*TimestampMonotonic` qiymatlari YAGONA avtoritet vaqt
    bazasi (PREREGISTRATION.md §1). Harness'ning o'z qabul vaqti ALOHIDA
    `recv_mono_us` field'ida yoziladi. Ikkisi hech qachon aralashtirilmaydi:
    aks holda D-Bus yetkazish kechikishi o'lchov ichida YASHIRINIB qolardi va
    `L_det`/`D_sd` shu kechikish miqdorida buzilardi. Ikki field bo'lgani uchun
    kechikish ko'rinadi va kerak bo'lsa hisobotda beriladi.

  * SLICE NOMLASH TUZOG'I: systemd'da slice nomidagi `-` ierarxiya
    ajratuvchisi, ya'ni `a-b.slice` avtomatik `a.slice/a-b.slice` bo'ladi.
    Shuning uchun eksperiment slice'lari `revixlab.slice` / `revixmon.slice`
    (dash'siz) -- ular HAQIQIY SIBLING bo'lishi shart, aks holda harness PSI'si
    o'lchanayotgan slice PSI'siga qo'shilib ketardi (PREREGISTRATION.md §8.2).
    Service nomlaridagi dash muammo emas. HECH NARSA QAYTA NOMLANMAYDI.

  * Ikki alohida D-Bus ulanishi:
      - `bus`        -> faqat bloklovchi chaqiruvlar (chaqiruvchi thread'da)
      - `signal_bus` -> faqat signal qabul qilish (GLib loop thread'da)
    Sabab: bitta ulanishda bir thread blocking call qilayotganda boshqasi
    dispatch qilishi libdbus'da yaxshi ma'lum flakiness manbasi. Signal
    handler'i HECH QANDAY D-Bus chaqirig'i qilmaydi -- u faqat signal
    payload'ini cache'ga qo'shadi, demak yetkazish yo'li qisqa va o'lchov
    kechikishi minimal.

PROPERTY NOMLARI -- IKKI OILA, ARALASHTIRILMAYDI:
  * `...Sec` (do'stona nom, masalan `RestartSec`) -> qiymat SEKUNDDA
    (son) yoki systemd vaqt satrida (`"100ms"`, `"8s"`, `"infinity"`).
  * `...USec` (D-Bus nomi, masalan `RestartUSec`) -> qiymat MIKROSEKUNDDA
    (butun son), konversiya qilinmaydi.
  Nomaʼlum property nomi JIMGINA TASHLANMAYDI -- istisno tashlanadi. Jimgina
  tashlangan `MemoryMax=` butun cheklash rejimini yo'q qilardi.
"""

from __future__ import annotations

import fnmatch
import os
import re
import shutil
import subprocess
import threading
import time
from collections import deque
from typing import Any, Callable, Iterable, Mapping, Sequence

from . import cgroup as cg
from .schema import mono_us, real_us

# --- D-Bus manzillari -------------------------------------------------------

BUS_NAME = "org.freedesktop.systemd1"
MANAGER_PATH = "/org/freedesktop/systemd1"
MANAGER_IFACE = "org.freedesktop.systemd1.Manager"
UNIT_IFACE = "org.freedesktop.systemd1.Unit"
SERVICE_IFACE = "org.freedesktop.systemd1.Service"
PROPS_IFACE = "org.freedesktop.DBus.Properties"

# --- REVIX nomlari (PREREGISTRATION.md amendment v1 -> v1.1) ----------------
# DASH YO'Q. Ko'ring: modul docstring'idagi "SLICE NOMLASH TUZOG'I".

LAB_SLICE = "revixlab.slice"
MON_SLICE = "revixmon.slice"
UNIT_PREFIX = "revix-"
UNIT_GLOB = "revix-*"

UINT64_MAX = 2**64 - 1

# --- o'lchov uchun muhim property to'plamlari -------------------------------
# PREREGISTRATION.md §3 (F_sd detektori) va §6.1 (D_sd) aynan shu qiymatlarga
# tayanadi, demak ularning BARCHASI har unit_state record'ida bo'lishi kerak.

UNIT_TIMESTAMP_PROPS = (
    "InactiveExitTimestampMonotonic",
    "ActiveEnterTimestampMonotonic",
    "ActiveExitTimestampMonotonic",
    "InactiveEnterTimestampMonotonic",
    "ConditionTimestampMonotonic",
)
SERVICE_TIMESTAMP_PROPS = (
    "ExecMainStartTimestampMonotonic",
    "ExecMainExitTimestampMonotonic",
)
MONOTONIC_TIMESTAMP_PROPS = UNIT_TIMESTAMP_PROPS + SERVICE_TIMESTAMP_PROPS

UNIT_STATE_PROPS = (
    "ActiveState",
    "SubState",
    "InvocationID",
    # StateChangeTimestampMonotonic talab qilingan yettilikda yo'q, lekin u
    # "bu o'tish AYNAN QACHON bo'ldi" degan yagona qiymat, demak
    # recv_mono_us - StateChangeTimestampMonotonic to'g'ridan-to'g'ri D-Bus
    # yetkazish kechikishini beradi. Bepul, shuning uchun yoziladi.
    "StateChangeTimestampMonotonic",
) + UNIT_TIMESTAMP_PROPS

SERVICE_STATE_PROPS = (
    "NRestarts",
    "Result",
    "ExecMainPID",
    "ExecMainCode",
    "ExecMainStatus",
) + SERVICE_TIMESTAMP_PROPS

STATE_PROPS = UNIT_STATE_PROPS + SERVICE_STATE_PROPS

# systemd job natijalari (JobRemoved ning oxirgi argumenti).
JOB_RESULT_OK = "done"


# --- xatolar ----------------------------------------------------------------


class UnitsError(RuntimeError):
    """units.py ning barcha xatolari uchun asos."""


class NoDBusError(UnitsError):
    """Foydalanuvchi D-Bus sessiyasi yo'q yoki python-dbus mavjud emas."""


class NoSuchUnitError(UnitsError):
    """Unit systemd'ga yuklanmagan (mavjud emas yoki --collect bilan o'chgan)."""


class UnitNotAliveError(UnitsError):
    """Property dump TIRIK bo'lmagan unit ustida urinildi.

    Bu maxsus xato turi, chunki bu holat JIMGINA yolg'on ma'lumot beradi:
    `systemctl show` mavjud bo'lmagan unit uchun rc=0 va TO'LIQ DEFAULT
    to'plamini chiqaradi (tekshirilgan: LoadState=not-found, MemoryMax=infinity,
    RestartSteps=0). Ya'ni dump haqiqiy qiymatlarga o'xshab ko'rinadi, lekin
    ishlagan unit'ga aloqasi yo'q.
    """


class JobFailedError(UnitsError):
    """systemd job 'done' dan boshqa natija bilan tugadi."""

    def __init__(self, unit: str, job_path: str, result: str) -> None:
        super().__init__(f"{unit}: job {job_path} natijasi {result!r} (kutilgan 'done')")
        self.unit = unit
        self.job_path = job_path
        self.result = result


class PreflightError(UnitsError):
    """Qoldiq holat topildi -- run boshlanmaydi."""

    def __init__(self, report: dict[str, Any]) -> None:
        super().__init__("pre-flight muvaffaqiyatsiz: " + "; ".join(report["problems"]))
        self.report = report


# --- D-Bus import: modul import vaqtida yiqilmasligi kerak ------------------
# Tests va analiz vositalari units.py ni D-Bus'siz mashinada ham import
# qilishi kerak (masalan reduce.py faqat nomlarni ishlatadi).

_dbus: Any = None
_dbus_import_error: str | None = None
try:  # pragma: no cover -- muhitga bog'liq
    import dbus as _dbus_mod

    _dbus = _dbus_mod
except Exception as exc:  # noqa: BLE001
    _dbus_import_error = repr(exc)


def dbus_available() -> bool:
    """python-dbus import qilinganmi."""
    return _dbus is not None


def session_bus_address() -> str | None:
    """Foydalanuvchi sessiya bus manzili, yoki None."""
    addr = os.environ.get("DBUS_SESSION_BUS_ADDRESS")
    if addr:
        return addr
    xdg = os.environ.get("XDG_RUNTIME_DIR")
    if xdg and os.path.exists(f"{xdg}/bus"):
        return f"unix:path={xdg}/bus"
    return None


def user_bus_reason() -> str | None:
    """Foydalanuvchi bus'idan foydalanib bo'lmasligining sababi, yoki None.

    Test'lar shu satrni skip sababi sifatida ko'rsatadi -- jimgina o'tib
    ketilmaydi, chunki "test o'tdi" va "test ishlamadi" bir xil ko'rinmasligi
    kerak.
    """
    if _dbus is None:
        return f"python-dbus import qilinmadi: {_dbus_import_error}"
    if session_bus_address() is None:
        return "foydalanuvchi D-Bus sessiyasi yo'q (DBUS_SESSION_BUS_ADDRESS / $XDG_RUNTIME_DIR/bus)"
    return None


# --- GLib loop: process bo'yicha BITTA thread -------------------------------
# Bir nechta ulanish GLib ning DEFAULT main context'iga bog'lanadi. Uni ikki
# thread'dan iterate qilish xato bo'lardi, shuning uchun loop process bo'yicha
# bitta va ref-hisobsiz (daemon thread, process bilan o'ladi).

_glib_lock = threading.Lock()
_glib_loop: Any = None
_glib_thread: threading.Thread | None = None


def _ensure_glib_loop() -> None:
    global _glib_loop, _glib_thread
    with _glib_lock:
        if _glib_thread is not None and _glib_thread.is_alive():
            return
        from gi.repository import GLib  # kech import

        _glib_loop = GLib.MainLoop()
        _glib_thread = threading.Thread(
            target=_glib_loop.run, name="revix-dbus-loop", daemon=True
        )
        _glib_thread.start()
        # Loop haqiqatan aylanayotganiga ishonch: aks holda birinchi signal
        # dispatch qilinmay qolishi mumkin.
        for _ in range(200):
            if _glib_loop.is_running():
                return
            time.sleep(0.001)


# --- qiymat konvertorlari ---------------------------------------------------

_BYTE_SUFFIX = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
_TIME_SUFFIX_US = {
    "us": 1,
    "usec": 1,
    "ms": 1_000,
    "msec": 1_000,
    "s": 1_000_000,
    "sec": 1_000_000,
    "second": 1_000_000,
    "seconds": 1_000_000,
    "min": 60_000_000,
    "m": 60_000_000,
    "h": 3_600_000_000,
}
_INFINITY = ("infinity", "max", "inf")


def parse_bytes(value: Any) -> int:
    """Bayt qiymatini uint64 ga aylantiradi.

    None / "infinity" / "max" -> UINT64_MAX (systemd uchun "cheklov yo'q").
    Suffikslar 1024-asosli (systemd'ning K/M/G/T bilan bir xil).
    """
    if value is None:
        return UINT64_MAX
    if isinstance(value, bool):
        raise UnitsError(f"bayt qiymati bool bo'lishi mumkin emas: {value!r}")
    if isinstance(value, int):
        if value < 0:
            raise UnitsError(f"manfiy bayt qiymati: {value!r}")
        return value
    if isinstance(value, float):
        return int(value)
    s = str(value).strip()
    if s.lower() in _INFINITY:
        return UINT64_MAX
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([KMGT]?)i?B?", s, re.IGNORECASE)
    if not m:
        raise UnitsError(f"bayt qiymati tanilmadi: {value!r}")
    return int(float(m.group(1)) * _BYTE_SUFFIX[m.group(2).upper()])


def parse_time_us(value: Any) -> int:
    """Vaqt qiymatini mikrosekundga aylantiradi.

    SON -> SEKUND (systemd'ning `...Sec=` semantikasi bilan bir xil).
    SATR -> systemd vaqt satri: "100ms", "8s", "1min", "500us", "infinity".
    None / "infinity" -> UINT64_MAX.

    DIQQAT: bu funksiya faqat DO'STONA (`...Sec`) nomlar uchun. `...USec`
    nomlari to'g'ridan-to'g'ri mikrosekund qabul qiladi va bu yerga kelmaydi --
    aks holda 100000 (µs) 100000 sekund deb o'qilardi.
    """
    if value is None:
        return UINT64_MAX
    if isinstance(value, bool):
        raise UnitsError(f"vaqt qiymati bool bo'lishi mumkin emas: {value!r}")
    if isinstance(value, (int, float)):
        if value < 0:
            raise UnitsError(f"manfiy vaqt qiymati: {value!r}")
        return int(round(value * 1_000_000))
    s = str(value).strip().lower()
    if s in _INFINITY:
        return UINT64_MAX
    total = 0
    pos = 0
    matched = False
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*([a-z]*)", s):
        if m.start() != pos:
            break
        pos = m.end()
        num, suf = m.group(1), m.group(2)
        if suf == "":
            mult = 1_000_000  # suffikssiz = sekund (systemd bilan bir xil)
        elif suf in _TIME_SUFFIX_US:
            mult = _TIME_SUFFIX_US[suf]
        else:
            raise UnitsError(f"vaqt suffiksi tanilmadi: {suf!r} ({value!r})")
        total += int(round(float(num) * mult))
        matched = True
    if not matched or pos != len(s):
        raise UnitsError(f"vaqt qiymati tanilmadi: {value!r}")
    return total


def parse_cpu_quota_us_per_sec(value: Any) -> int:
    """`CPUQuota=` ni `CPUQuotaPerSecUSec` ga aylantiradi.

    SON yoki "400%" -> FOIZ. 400% = sekundiga 4 s CPU = 4_000_000 µs.
    Bu mashinada tekshirilgan: `--property=CPUQuota=400%` ->
    `CPUQuotaPerSecUSec=4s`.
    """
    if value is None:
        return UINT64_MAX
    if isinstance(value, str):
        s = value.strip()
        if s.lower() in _INFINITY:
            return UINT64_MAX
        s = s.rstrip("%").strip()
        pct = float(s)
    else:
        pct = float(value)
    if pct < 0:
        raise UnitsError(f"manfiy CPUQuota: {value!r}")
    return int(round(pct / 100.0 * 1_000_000))


def parse_tasks_max(value: Any) -> int:
    if value is None:
        return UINT64_MAX
    if isinstance(value, str):
        if value.strip().lower() in _INFINITY:
            return UINT64_MAX
        return int(value)
    return int(value)


class _Omit:
    """Property'ni butunlay YUBORMASLIK kerakligini bildiruvchi sentinel."""

    def __repr__(self) -> str:  # pragma: no cover
        return "<omit>"


OMIT = _Omit()


def _collect_mode(value: Any) -> Any:
    """`Collect=True` -> `CollectMode=inactive-or-failed` (systemd-run --collect).

    ⚠️ systemd'da `CollectMode=no` QIYMATI YO'Q -- enum faqat `inactive` va
    `inactive-or-failed`. Bu mashinada tasdiqlangan:
    `StartTransientUnit(..., CollectMode="no")` ->
    `org.freedesktop.DBus.Error.InvalidArgs: Invalid CollectMode setting: no`.
    "Yig'ishtirmaslik" = property'ni UMUMAN YUBORMASLIK, shuning uchun
    `Collect=False` sentinel qaytaradi.
    """
    if isinstance(value, bool):
        return "inactive-or-failed" if value else OMIT
    s = str(value)
    if s in ("no", "off", "false"):
        return OMIT
    if s not in ("inactive", "inactive-or-failed"):
        raise UnitsError(
            f"CollectMode qiymati tanilmadi: {value!r} "
            f"(systemd faqat 'inactive' va 'inactive-or-failed' ni biladi)"
        )
    return s


def _exec_lines(value: Any) -> list[tuple[str, list[str], bool]]:
    """`ExecStart` qiymatini `a(sasb)` ko'rinishiga keltiradi.

    Qabul qiladi:
      ["/bin/sleep", "30"]                -> bitta exec satri
      [["/bin/a","x"], ["/bin/b","y"]]    -> ketma-ket bir nechta satr
      [("/bin/a", ["/bin/a","x"], False)] -> to'liq (path, argv, ignore) uchligi

    SATR QABUL QILINMAYDI: "sleep 30" ni bo'lish qo'shtirnoq xatolarini
    yashirar edi, va exec argv'i o'lchanadigan narsaning o'zi.
    """
    if isinstance(value, str):
        raise UnitsError(
            "ExecStart satr bo'lishi mumkin emas -- argv ro'yxatini bering "
            "(masalan ['/bin/sleep', '30'])"
        )
    if not isinstance(value, Sequence) or not value:
        raise UnitsError(f"ExecStart ro'yxat bo'lishi kerak: {value!r}")
    if all(isinstance(x, str) for x in value):
        argv = [str(x) for x in value]
        return [(argv[0], argv, False)]
    out: list[tuple[str, list[str], bool]] = []
    for item in value:
        if isinstance(item, str):
            raise UnitsError(f"ExecStart aralash ro'yxat: {value!r}")
        seq = list(item)
        if len(seq) == 3 and isinstance(seq[1], Sequence) and not isinstance(seq[1], str):
            out.append((str(seq[0]), [str(a) for a in seq[1]], bool(seq[2])))
        else:
            argv = [str(a) for a in seq]
            out.append((argv[0], argv, False))
    return out


# --- property jadvali -------------------------------------------------------
# (do'stona nom) -> (D-Bus nomi, D-Bus turi kodi, konvertor)
# Turi kodlari: s=string, b=bool, u=uint32, t=uint64, i=int32,
#               as=string massivi, exec=a(sasb)

_PROP_TABLE: dict[str, tuple[str, str, Callable[[Any], Any]]] = {}


def _reg(friendly: str, dbus_name: str, kind: str, conv: Callable[[Any], Any]) -> None:
    _PROP_TABLE[friendly] = (dbus_name, kind, conv)


# cgroup cheklovlari
for _n in ("MemoryMax", "MemoryHigh", "MemoryLow", "MemoryMin", "MemorySwapMax",
           "MemoryZSwapMax"):
    _reg(_n, _n, "t", parse_bytes)
_reg("TasksMax", "TasksMax", "t", parse_tasks_max)
_reg("CPUQuota", "CPUQuotaPerSecUSec", "t", parse_cpu_quota_us_per_sec)
_reg("CPUQuotaPerSecUSec", "CPUQuotaPerSecUSec", "t", int)
_reg("CPUQuotaPeriodSec", "CPUQuotaPeriodUSec", "t", parse_time_us)
_reg("CPUWeight", "CPUWeight", "t", int)
_reg("Slice", "Slice", "s", str)
_reg("Delegate", "Delegate", "b", bool)
_reg("OOMPolicy", "OOMPolicy", "s", str)
_reg("OOMScoreAdjust", "OOMScoreAdjust", "i", int)
_reg("Nice", "Nice", "i", int)

# restart / cheklov siyosati
_reg("Restart", "Restart", "s", str)
_reg("RestartMode", "RestartMode", "s", str)
_reg("RestartSec", "RestartUSec", "t", parse_time_us)
_reg("RestartUSec", "RestartUSec", "t", int)
_reg("RestartSteps", "RestartSteps", "u", int)
_reg("RestartMaxDelaySec", "RestartMaxDelayUSec", "t", parse_time_us)
_reg("RestartMaxDelayUSec", "RestartMaxDelayUSec", "t", int)
_reg("StartLimitBurst", "StartLimitBurst", "u", int)
_reg("StartLimitIntervalSec", "StartLimitIntervalUSec", "t", parse_time_us)

# vaqt chegaralari
for _n, _d in (
    ("WatchdogSec", "WatchdogUSec"),
    ("TimeoutStartSec", "TimeoutStartUSec"),
    ("TimeoutStopSec", "TimeoutStopUSec"),
    ("TimeoutAbortSec", "TimeoutAbortUSec"),
    ("RuntimeMaxSec", "RuntimeMaxUSec"),
):
    _reg(_n, _d, "t", parse_time_us)
    _reg(_d, _d, "t", int)

# exec muhiti
_reg("ExecStart", "ExecStart", "exec", _exec_lines)
_reg("ExecStartPre", "ExecStartPre", "exec", _exec_lines)
_reg("ExecStopPost", "ExecStopPost", "exec", _exec_lines)
_reg("Environment", "Environment", "as", lambda v: [str(x) for x in v])
_reg("WorkingDirectory", "WorkingDirectory", "s", str)
_reg("Type", "Type", "s", str)
_reg("NotifyAccess", "NotifyAccess", "s", str)
_reg("RemainAfterExit", "RemainAfterExit", "b", bool)
_reg("KillMode", "KillMode", "s", str)
_reg("KillSignal", "KillSignal", "s", str)

# unit meta
_reg("Description", "Description", "s", str)
_reg("Collect", "CollectMode", "s", _collect_mode)
_reg("CollectMode", "CollectMode", "s", _collect_mode)
_reg("AddRef", "AddRef", "b", bool)

# journald oqimlari -- PREREGISTRATION §3.4: o'lchov ma'lumoti journald'dan
# O'TMAYDI (rate-limit uni jimgina yo'qotardi), shuning uchun driver bu
# property'lar orqali oqimlarni o'chirishi/faylga yo'naltirishi kerak.
for _n in ("StandardInput", "StandardOutput", "StandardError", "SyslogIdentifier"):
    _reg(_n, _n, "s", str)

SUPPORTED_PROPERTIES = tuple(sorted(_PROP_TABLE))


def _variant(kind: str, value: Any) -> Any:
    d = _dbus
    if kind == "s":
        return d.String(value)
    if kind == "b":
        return d.Boolean(value)
    if kind == "u":
        return d.UInt32(value)
    if kind == "t":
        return d.UInt64(value)
    if kind == "i":
        return d.Int32(value)
    if kind == "as":
        return d.Array([d.String(x) for x in value], signature="s")
    if kind == "exec":
        return d.Array(
            [
                d.Struct(
                    (
                        d.String(path),
                        d.Array([d.String(a) for a in argv], signature="s"),
                        d.Boolean(ignore),
                    )
                )
                for path, argv, ignore in value
            ],
            signature="(sasb)",
        )
    raise UnitsError(f"ichki xato: property turi tanilmadi {kind!r}")


def encode_properties(props: Mapping[str, Any]) -> Any:
    """Do'stona property dict'ini D-Bus `a(sv)` ga aylantiradi.

    Nomaʼlum nom ISTISNO tashlaydi. Jimgina tashlash -- masalan `MemoryMax=`
    ni yo'qotish -- butun cheklash rejimini yo'q qilib, eksperimentni
    o'ldiruvchi validlik xatosi bo'lardi. Allaqachon `dbus.*` turi berilgan
    qiymat o'zgartirilmasdan o'tadi (qo'lda kengaytirish uchun eshik).
    """
    if _dbus is None:
        raise NoDBusError(f"python-dbus yo'q: {_dbus_import_error}")
    out = []
    for name, value in props.items():
        if value is None and name not in _PROP_TABLE:
            raise UnitsError(f"property nomi tanilmadi: {name!r}")
        if type(value).__module__.startswith("dbus"):
            out.append((_dbus.String(name), value))
            continue
        entry = _PROP_TABLE.get(name)
        if entry is None:
            raise UnitsError(
                f"property nomi tanilmadi: {name!r}. Qo'llab-quvvatlanadigan "
                f"nomlar: {', '.join(SUPPORTED_PROPERTIES)}. Boshqa property "
                f"kerak bo'lsa qiymatni dbus.* turida bering."
            )
        dbus_name, kind, conv = entry
        if value is None and kind in ("s", "as", "exec", "b", "u", "i"):
            # `None` faqat "cheklov yo'q" ma'nosida (uint64 chegaralari) mantiqiy.
            # Satr/argv uchun `str(None)` -> "None" bo'lib, systemd'ga
            # ma'nosiz qiymat ketardi.
            raise UnitsError(f"{name}: None qiymati bu property uchun ma'nosiz")
        converted = conv(value)
        if converted is OMIT:
            continue   # `Collect=False` -- systemd'da "no" qiymati yo'q
        out.append((_dbus.String(dbus_name), _variant(kind, converted)))
    return _dbus.Array(out, signature="(sv)")


# --- D-Bus qiymatlarini oddiy Python'ga aylantirish -------------------------


def plain(value: Any) -> Any:
    """`dbus.*` qiymatini JSON'ga yozilishi mumkin Python qiymatiga aylantiradi."""
    if _dbus is not None:
        if isinstance(value, _dbus.ByteArray):
            return bytes(value).hex()
        if isinstance(value, _dbus.Boolean):
            return bool(value)
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        # `ay` (bayt massivi) -> hex satr. InvocationID aynan shunday keladi.
        # Bo'sh `ay` -> "" (bo'sh satr), [] EMAS: unit hali ishga tushmagan
        # bo'lsa InvocationID bo'sh bo'ladi va u satr turida qolishi kerak.
        if _is_byte_array(value):
            return bytes(int(b) for b in value).hex()
        return [plain(v) for v in value]
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    if isinstance(value, (bytes, bytearray)):
        return bytes(value).hex()
    if value is None:
        return None
    return str(value)


def _is_byte_array(value: Any) -> bool:
    if _dbus is None:
        return False
    if isinstance(value, _dbus.Array):
        try:
            return str(value.signature) == "y"
        except Exception:  # noqa: BLE001
            return False
    return False


# --- unit nomi -> D-Bus obyekt yo'li ----------------------------------------


def bus_label_escape(s: str) -> str:
    """systemd'ning `bus_label_escape()` ining aynan nusxasi.

    a-zA-Z dan boshqa hamma narsa `_XX` (hex) ga aylanadi; raqamlar faqat
    BIRINCHI belgi bo'lganda qochiriladi. `_` ning o'zi ham qochiriladi.
    Tasdiq: `revixselftest-explore1.service` ->
    `revixselftest_2dexplore1_2eservice` (bu mashinada kuzatilgan yo'l).
    """
    out = []
    for i, ch in enumerate(s):
        if ("A" <= ch <= "Z") or ("a" <= ch <= "z") or (i > 0 and "0" <= ch <= "9"):
            out.append(ch)
        else:
            out.append("_%02x" % (ord(ch) & 0xFF))
    return "".join(out)


def unit_object_path(name: str) -> str:
    """Unit nomidan D-Bus obyekt yo'lini HISOBLAYDI (systemd'ga so'rov yubormasdan).

    Bu muhim: watcher unit HALI YARATILMASDAN OLDIN signal match'ini
    o'rnatishi mumkin bo'ladi, demak eng birinchi holat o'tishi ham
    o'tkazib yuborilmaydi. `GetUnit()` ni kutish o'lchov boshini yo'qotardi.
    """
    return f"/org/freedesktop/systemd1/unit/{bus_label_escape(name)}"


# --- SystemdUser ------------------------------------------------------------


class SystemdUser:
    """Foydalanuvchi systemd manager'i bilan ishlaydigan ulanish.

    Ikki ulanish: `bus` (bloklovchi chaqiruvlar) va `signal_bus` (signallar,
    GLib loop thread'ida dispatch qilinadi). Ko'ring: modul docstring'i.
    """

    def __init__(self, *, connect_signals: bool = True) -> None:
        reason = user_bus_reason()
        if reason:
            raise NoDBusError(reason)
        self.bus = _dbus.SessionBus(private=True)
        _no_exit_on_disconnect(self.bus)
        self.manager = _dbus.Interface(
            self.bus.get_object(BUS_NAME, MANAGER_PATH), MANAGER_IFACE
        )
        self.signal_bus: Any = None
        self._subscribed = False
        # job yo'li -> (natija, qabul mono_us). Signal chaqiruvdan OLDIN
        # kelishi mumkin, shuning uchun natijalar so'ralishini kutmasdan
        # saqlanadi (poyga yo'q).
        self._job_results: dict[str, tuple[str, int]] = {}
        self._job_cv = threading.Condition()
        self._job_order: deque[str] = deque(maxlen=512)
        # Unit obyekt yo'li nom'dan DETERMINISTIK (bus_label_escape), shuning
        # uchun cache'lash xavfsiz -- unit o'chib qayta yaratilsa ham yo'l
        # o'zgarmaydi. Cache har `Get` oldidagi `GetUnit` round-trip'ini
        # yo'q qiladi (polling narxi ikki barobar kamayadi).
        self._path_cache: dict[str, str] = {}
        self._closed = False
        if connect_signals:
            self._ensure_signal_bus()

    # --- ulanishlar ---
    def _ensure_signal_bus(self) -> Any:
        if self.signal_bus is not None:
            return self.signal_bus
        _ensure_glib_loop()
        from dbus.mainloop.glib import DBusGMainLoop

        # Mainloop AYNAN shu ulanishga beriladi, global default o'zgartirilmaydi:
        # units.py ni import qilish process'ning boshqa D-Bus foydalanuvchilariga
        # ta'sir qilmasligi kerak.
        self.signal_bus = _dbus.SessionBus(mainloop=DBusGMainLoop(), private=True)
        _no_exit_on_disconnect(self.signal_bus)
        self.signal_bus.add_signal_receiver(
            self._on_job_removed,
            signal_name="JobRemoved",
            dbus_interface=MANAGER_IFACE,
            bus_name=BUS_NAME,
            path=MANAGER_PATH,
        )
        self.subscribe()
        return self.signal_bus

    def subscribe(self) -> None:
        """`Manager.Subscribe()` -- systemd signallarni faqat obunachi bo'lsa yuboradi."""
        if self._subscribed:
            return
        bus = self.signal_bus if self.signal_bus is not None else self.bus
        mgr = _dbus.Interface(bus.get_object(BUS_NAME, MANAGER_PATH), MANAGER_IFACE)
        try:
            mgr.Subscribe()
        except _dbus.DBusException as exc:
            # "Client is already subscribed" -- xato emas.
            if "already subscribed" not in (exc.get_dbus_message() or "").lower():
                raise
        self._subscribed = True

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for b in (self.signal_bus, self.bus):
            if b is None:
                continue
            try:
                b.close()
            except Exception:  # noqa: BLE001 -- yopishdagi xato yashiriladi
                pass

    def __enter__(self) -> "SystemdUser":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --- job natijalari ---
    def _on_job_removed(self, _job_id: Any, job_path: Any, _unit: Any, result: Any) -> None:
        t = mono_us()
        p = str(job_path)
        with self._job_cv:
            if p not in self._job_results and len(self._job_order) == self._job_order.maxlen:
                old = self._job_order[0]
                self._job_results.pop(old, None)
            self._job_order.append(p)
            self._job_results[p] = (str(result), t)
            self._job_cv.notify_all()

    def wait_job(self, job_path: str, timeout_s: float = 30.0) -> tuple[str | None, int | None]:
        """`JobRemoved` ni kutadi. (natija, qabul mono_us) yoki (None, None)."""
        deadline = time.monotonic() + timeout_s
        with self._job_cv:
            while True:
                got = self._job_results.get(job_path)
                if got is not None:
                    return got
                left = deadline - time.monotonic()
                if left <= 0:
                    return (None, None)
                self._job_cv.wait(left)

    # --- unit yaratish ---
    def start_transient(
        self,
        name: str,
        properties: Mapping[str, Any],
        *,
        mode: str = "fail",
        wait: bool = True,
        timeout_s: float = 30.0,
        require_done: bool = True,
    ) -> dict[str, Any]:
        """Transient unit yaratadi va (xohlasa) job tugashini kutadi.

        Qaytadigan dict IKKI TOMONLI BRACKET beradi: `mono_us_before_call` va
        `mono_us_after_call`. PREREGISTRATION.md §3 injeksiya vaqtini aynan
        shunday bracket qilishni talab qiladi -- "chaqiruv qaytdi" bitta
        nuqta emas, INTERVAL, va u shunday yoziladi.

        `mono_us_job_removed` -- systemd job'i tugagani ANIQLANGAN vaqt
        (harness qabul vaqti). Unit'ning o'z avtoritet vaqtlari uchun
        `read_state()` yoki `UnitWatcher` ishlatiladi.
        """
        if wait:
            self._ensure_signal_bus()
        encoded = encode_properties(properties)
        aux = _dbus.Array([], signature="(sa(sv))")
        t0 = mono_us()
        try:
            job = self.manager.StartTransientUnit(name, mode, encoded, aux)
        except _dbus.DBusException as exc:
            t1 = mono_us()
            raise UnitsError(
                f"StartTransientUnit({name!r}) muvaffaqiyatsiz: "
                f"{exc.get_dbus_name()}: {exc.get_dbus_message()} "
                f"[mono_us {t0}..{t1}]"
            ) from exc
        t1 = mono_us()
        out: dict[str, Any] = {
            "unit": name,
            "job_path": str(job),
            "mono_us_before_call": t0,
            "mono_us_after_call": t1,
            "job_result": None,
            "mono_us_job_removed": None,
        }
        if wait:
            result, tj = self.wait_job(str(job), timeout_s=timeout_s)
            out["job_result"] = result
            out["mono_us_job_removed"] = tj
            if result is None:
                raise UnitsError(
                    f"{name}: job {job} {timeout_s}s ichida tugamadi (JobRemoved kelmadi)"
                )
            if require_done and result != JOB_RESULT_OK:
                raise JobFailedError(name, str(job), result)
        return out

    # --- oddiy unit operatsiyalari ---
    def _job_call(
        self,
        method: str,
        name: str,
        mode: str,
        *,
        wait: bool,
        timeout_s: float,
        require_done: bool,
    ) -> dict[str, Any]:
        if wait:
            self._ensure_signal_bus()
        t0 = mono_us()
        try:
            job = getattr(self.manager, method)(name, mode)
        except _dbus.DBusException as exc:
            if _is_no_such_unit(exc):
                raise NoSuchUnitError(f"{name}: yuklanmagan ({exc.get_dbus_name()})") from exc
            raise UnitsError(
                f"{method}({name!r}) muvaffaqiyatsiz: "
                f"{exc.get_dbus_name()}: {exc.get_dbus_message()}"
            ) from exc
        t1 = mono_us()
        out: dict[str, Any] = {
            "unit": name,
            "job_path": str(job),
            "mono_us_before_call": t0,
            "mono_us_after_call": t1,
            "job_result": None,
            "mono_us_job_removed": None,
        }
        if wait:
            result, tj = self.wait_job(str(job), timeout_s=timeout_s)
            out["job_result"] = result
            out["mono_us_job_removed"] = tj
            if require_done and result is not None and result != JOB_RESULT_OK:
                raise JobFailedError(name, str(job), result)
        return out

    def start_unit(
        self, name: str, *, mode: str = "fail", wait: bool = True, timeout_s: float = 30.0
    ) -> dict[str, Any]:
        """Mavjud unit'ni (masalan slice'ni) ishga tushiradi."""
        return self._job_call("StartUnit", name, mode, wait=wait, timeout_s=timeout_s,
                              require_done=True)

    def stop(
        self,
        name: str,
        *,
        mode: str = "replace",
        wait: bool = True,
        timeout_s: float = 30.0,
        missing_ok: bool = True,
    ) -> dict[str, Any] | None:
        """Unit'ni to'xtatadi. `missing_ok` -> yo'q unit uchun None qaytaradi.

        Job natijasi tekshirilmaydi: to'xtatishda `Restart=` sababli job
        'canceled' bo'lishi mumkin, va bu teardown uchun xato emas.
        """
        try:
            return self._job_call("StopUnit", name, mode, wait=wait, timeout_s=timeout_s,
                                  require_done=False)
        except NoSuchUnitError:
            if missing_ok:
                return None
            raise

    def reset_failed(self, name: str, *, missing_ok: bool = True) -> bool:
        """Bitta unit uchun `reset-failed`.

        Manager darajasidagi `ResetFailed()` ATAYLAB ishlatilmaydi -- u
        foydalanuvchining BARCHA failed unit'larini tozalardi, ya'ni biz
        tegishimiz kerak bo'lmagan jonli muhitni o'zgartirardi.
        """
        try:
            self.manager.ResetFailedUnit(name)
            return True
        except _dbus.DBusException as exc:
            if missing_ok and _is_no_such_unit(exc):
                return False
            raise UnitsError(
                f"ResetFailedUnit({name!r}): {exc.get_dbus_name()}: {exc.get_dbus_message()}"
            ) from exc

    def reset_failed_pattern(self, pattern: str) -> list[str]:
        """Glob'ga mos failed unit'larni reset qiladi. Reset qilinganlar ro'yxati."""
        done = []
        for u in self.list_units(pattern):
            if u["active_state"] == "failed" or u["sub_state"] == "failed":
                if self.reset_failed(u["unit"]):
                    done.append(u["unit"])
        return done

    def set_unit_properties(
        self, name: str, properties: Mapping[str, Any], *, runtime: bool = True
    ) -> None:
        """`set-property --runtime` semantikasi (D-Bus `SetUnitProperties`).

        `runtime=True` -> drop-in FAQAT /run/user/UID/systemd/user.control/ da
        yaratiladi, `~/.config/systemd/user/` ga hech narsa yozilmaydi.
        Persistent drop-in keyingi run'ni jimgina kontaminatsiya qilardi.
        """
        try:
            self.manager.SetUnitProperties(name, bool(runtime), encode_properties(properties))
        except _dbus.DBusException as exc:
            if _is_no_such_unit(exc):
                raise NoSuchUnitError(
                    f"{name}: SetUnitProperties uchun unit yuklanmagan"
                ) from exc
            raise UnitsError(
                f"SetUnitProperties({name!r}): {exc.get_dbus_name()}: {exc.get_dbus_message()}"
            ) from exc

    def reload(self) -> None:
        """`daemon-reload`. Runtime drop-in o'chirilgandan keyin kerak."""
        self.manager.Reload()

    # --- kuzatish ---
    def get_unit_path(self, name: str) -> str:
        """Yuklangan unit'ning obyekt yo'li. Yuklanmagan bo'lsa NoSuchUnitError."""
        try:
            return str(self.manager.GetUnit(name))
        except _dbus.DBusException as exc:
            if _is_no_such_unit(exc):
                raise NoSuchUnitError(f"{name}: yuklanmagan") from exc
            raise UnitsError(
                f"GetUnit({name!r}): {exc.get_dbus_name()}: {exc.get_dbus_message()}"
            ) from exc

    def unit_loaded(self, name: str) -> bool:
        """Unit systemd'ga YUKLANGANMI (avtoritet tekshiruv).

        `systemctl show` bu savolga javob BERMAYDI: u yo'q unit uchun ham
        rc=0 va default'lar chiqaradi.
        """
        try:
            self.get_unit_path(name)
            return True
        except NoSuchUnitError:
            return False

    def list_units(self, pattern: str | None = None) -> list[dict[str, Any]]:
        """Glob'ga mos YUKLANGAN unit'lar (systemctl --user list-units --all bilan bir xil)."""
        patterns = _dbus.Array([_dbus.String(pattern)] if pattern else [], signature="s")
        raw = self.manager.ListUnitsByPatterns(_dbus.Array([], signature="s"), patterns)
        out = []
        for row in raw:
            out.append(
                {
                    "unit": str(row[0]),
                    "description": str(row[1]),
                    "load_state": str(row[2]),
                    "active_state": str(row[3]),
                    "sub_state": str(row[4]),
                    "object_path": str(row[6]),
                }
            )
        return out

    def get_property(self, name: str, iface: str, prop: str) -> Any:
        path = self._path_cache.get(name)
        if path is None:
            path = self.get_unit_path(name)   # avtoritet: mavjudlikni ham tekshiradi
            self._path_cache[name] = path
        obj = self.bus.get_object(BUS_NAME, path)
        try:
            return plain(_dbus.Interface(obj, PROPS_IFACE).Get(iface, prop))
        except _dbus.DBusException as exc:
            # Cache'langan yo'l bo'yicha o'qish yiqilsa -- unit o'chgan bo'lishi
            # mumkin. `GetUnit` bilan AVTORITET javob olinadi (yoki
            # NoSuchUnitError), taxmin qilinmaydi.
            self._path_cache.pop(name, None)
            self.get_unit_path(name)
            raise UnitsError(
                f"Get({name!r}, {iface!r}, {prop!r}): "
                f"{exc.get_dbus_name()}: {exc.get_dbus_message()}"
            ) from exc

    def active_state(self, name: str) -> str | None:
        """`ActiveState`, yoki unit yuklanmagan bo'lsa None.

        None va "inactive" FARQ QILADI: None = unit umuman yo'q (masalan
        --collect bilan o'chgan), "inactive" = unit bor lekin ishlamayapti.
        Ularni aralashtirish o'lchovni buzardi.
        """
        try:
            return str(self.get_property(name, UNIT_IFACE, "ActiveState"))
        except NoSuchUnitError:
            return None

    def is_active(self, name: str) -> bool:
        return self.active_state(name) == "active"

    def read_state(self, name: str) -> dict[str, Any]:
        """Unit + Service holat property'larining to'liq to'plami.

        Ikki `GetAll` (Unit va Service) -- 16 ta alohida `Get` dan arzon.
        Qaytadigan dict UnitWatcher record'i bilan AYNAN BIR XIL shaklda,
        shunda polling va signal yo'llari taqqoslanadigan bo'ladi.
        """
        path = self.get_unit_path(name)
        props = _dbus.Interface(self.bus.get_object(BUS_NAME, path), PROPS_IFACE)
        recv = mono_us()
        unit_all = props.GetAll(UNIT_IFACE)
        try:
            svc_all = props.GetAll(SERVICE_IFACE)
        except _dbus.DBusException:
            svc_all = {}  # slice/target -- Service interfeysi yo'q
        snap: dict[str, Any] = {}
        for k, v in unit_all.items():
            snap[str(k)] = v
        for k, v in svc_all.items():
            snap[str(k)] = v
        return _state_record(name, snap, recv, iface=None, changed=None)


def _no_exit_on_disconnect(bus: Any) -> None:
    """libdbus'ning "disconnect bo'lsa process'ni o'ldirish" xatti-harakatini o'chiradi.

    ⚠️ AGAR BU QILINMASA: libdbus private bus ulanishlarini
    `exit_on_disconnect=TRUE` bilan yaratadi. Ulanish yopilganda (yoki bus
    yo'qolganda) main loop `Disconnected` xabarini dispatch qiladi va libdbus
    BUTUN PROCESS'ni `exit(1)` bilan o'ldiradi -- stdout flush qilinmaydi, hech
    qanday Python istisnosi ko'rinmaydi, atexit ishlamaydi.

    Bu aynan shu yerda kuzatilgan: `SystemdUser.close()` pytest process'ini
    RC=1 bilan, hech qanday xabar qoldirmasdan o'ldirdi. Driver uchun bu
    fatal bo'lardi -- harness o'lchov o'rtasida jimgina yo'qolib, trial
    `harness_error` ham deb yozilmasdi. Guard mustaqil jarayon bo'lgani uchun
    tirik qolardi, lekin ma'lumot yo'qolardi.
    """
    try:
        bus.set_exit_on_disconnect(False)
    except Exception:  # noqa: BLE001 -- eski dbus-python'da metod bo'lmasligi mumkin
        pass


def _is_no_such_unit(exc: Any) -> bool:
    n = exc.get_dbus_name() or ""
    if n in (
        "org.freedesktop.systemd1.NoSuchUnit",
        "org.freedesktop.systemd1.LoadFailed",
        "org.freedesktop.DBus.Error.UnknownObject",
    ):
        return True
    msg = (exc.get_dbus_message() or "").lower()
    return "not loaded" in msg or "no such unit" in msg


# --- unit_state record ------------------------------------------------------


def _state_record(
    unit: str,
    snap: Mapping[str, Any],
    recv_mono: int,
    *,
    iface: str | None,
    changed: Sequence[str] | None,
) -> dict[str, Any]:
    """`unit_state` payload'ini yasaydi.

    VAQT DISIPLINASI (PREREGISTRATION.md §1, §8):
      * `*TimestampMonotonic` -- systemd'ning O'ZI bergan, AVTORITET qiymatlar.
        Barcha davomiylik (D_sd, L_det_sd) SHULARDAN hisoblanadi.
      * `recv_mono_us` -- harness signalni QABUL QILGAN vaqt. ALOHIDA field,
        chunki aks holda D-Bus yetkazish kechikishi o'lchov ichida yashirinib,
        latency raqamlarini shu kechikish miqdorida buzardi. Ikki field bo'lsa
        kechikish KO'RINADI.
      * `snapshot_complete=False` -> ba'zi field'lar hali hech qachon
        ko'rinmagan (seed bo'lmagan watcher). Yo'q qiymat None, 0 EMAS:
        0 haqiqiy timestamp qiymati.
    """
    rec: dict[str, Any] = {
        "unit": unit,
        "recv_mono_us": recv_mono,
        "recv_real_us": real_us(),
        "signal_iface": iface,
        # Faqat O'LCHANADIGAN field'larning o'zgargani yoziladi. systemd bitta
        # o'tishda ~22 property nomini yuboradi va ularning ko'pi bizga
        # tegishli emas; to'liq ro'yxat har record'ni bir necha yuz bayt
        # kattalashtirardi. Umumiy soni `changed_count` da qoladi.
        "changed_props": (
            sorted(p for p in changed if p in STATE_PROPS) if changed is not None else None
        ),
        "changed_count": len(changed) if changed is not None else None,
    }
    missing = []
    for p in STATE_PROPS:
        if p in snap:
            rec[p] = plain(snap[p])
        else:
            rec[p] = None
            missing.append(p)
    rec["snapshot_complete"] = not missing
    rec["missing_props"] = missing or None
    return rec


class UnitWatcher:
    """Bitta unit uchun `PropertiesChanged` obunasi -> `unit_state` record'lar.

    NEGA CACHE: systemd bitta holat o'tishida IKKI signal yuboradi -- biri
    `...Unit` interfeysida (ActiveState, SubState, InvocationID, Unit
    timestamp'lari), biri `...Service` interfeysida (NRestarts, Result,
    ExecMain*). Har signalni alohida yozsak, har record yarim bo'sh bo'lardi
    va analiz ikki oqimni qo'lda birlashtirishga majbur bo'lardi. Shuning
    uchun watcher merged snapshot yuritadi va HAR record to'liq field
    to'plamini beradi.

    Bu qiymatlarni QARIB QOLMASLIK bilan xavfsiz, chunki bu mashinada
    tekshirilgan: Unit signali har marta BARCHA Unit timestamp'larini,
    Service signali har marta BARCHA ExecMain*/NRestarts/Result ni
    qiymatlari bilan yuboradi (invalidated ro'yxatida faqat Exec* va
    Conditions bor, bizga kerak bo'lmagan field'lar).

    Handler ichida HECH QANDAY D-Bus chaqirig'i yo'q -- faqat payload merge.
    Shuning uchun `recv_mono_us` haqiqatan qabul vaqtiga yaqin.
    """

    def __init__(
        self,
        systemd: SystemdUser,
        unit: str,
        *,
        sink: Callable[[dict[str, Any]], None] | None = None,
        max_buffer: int = 8192,
    ) -> None:
        self.systemd = systemd
        self.unit = unit
        self.object_path = unit_object_path(unit)
        self.sink = sink
        self.records: deque[dict[str, Any]] = deque(maxlen=max_buffer)
        self.dropped = 0
        self.sink_errors = 0
        self.signals_seen = 0
        self._snap: dict[str, Any] = {}
        self._cv = threading.Condition()
        self._match: Any = None
        self._started = False

    # --- hayot tsikli ---
    def start(self, *, seed: bool = True) -> "UnitWatcher":
        """Obunani o'rnatadi.

        Match birinchi, seed keyin: obyekt yo'li unit nomidan HISOBLANADI
        (`unit_object_path`), demak unit hali yaratilmagan bo'lsa ham obuna
        bo'lish mumkin va eng birinchi o'tish o'tkazib yuborilmaydi.
        """
        if self._started:
            return self
        bus = self.systemd._ensure_signal_bus()
        self._match = bus.add_signal_receiver(
            self._on_properties_changed,
            signal_name="PropertiesChanged",
            dbus_interface=PROPS_IFACE,
            bus_name=BUS_NAME,
            path=self.object_path,
        )
        self._started = True
        if seed:
            self.seed()
        return self

    def seed(self) -> bool:
        """Snapshot'ni joriy holat bilan to'ldiradi (chaqiruvchi thread'da).

        Signal payload'lari faqat O'ZGARGAN field'larni beradi, demak seed
        bo'lmasa birinchi record'lar yarim bo'sh bo'lardi. Unit hali yo'q
        bo'lsa False.
        """
        try:
            base = self.systemd.read_state(self.unit)
        except NoSuchUnitError:
            return False
        with self._cv:
            for p in STATE_PROPS:
                if base.get(p) is not None or p in ("ActiveState", "SubState"):
                    self._snap[p] = base[p]
        return True

    def stop(self) -> None:
        if not self._started:
            return
        try:
            self.systemd.signal_bus.remove_signal_receiver(
                self._match,
                signal_name="PropertiesChanged",
                dbus_interface=PROPS_IFACE,
                bus_name=BUS_NAME,
                path=self.object_path,
            )
        except Exception:  # noqa: BLE001 -- obunani olib tashlash xatosi yashiriladi
            pass
        self._started = False

    def __enter__(self) -> "UnitWatcher":
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.stop()

    # --- signal ---
    def _on_properties_changed(self, iface: Any, changed: Any, invalidated: Any) -> None:
        # BIRINCHI QATOR: qabul vaqti. Har qanday ish shundan keyin.
        recv = mono_us()
        name = str(iface)
        if name not in (UNIT_IFACE, SERVICE_IFACE):
            return  # Job va boshqa interfeyslar bu record turiga tegishli emas
        self.signals_seen += 1
        changed_names = []
        with self._cv:
            for k, v in changed.items():
                k = str(k)
                changed_names.append(k)
                if k in STATE_PROPS:
                    self._snap[k] = v
            rec = _state_record(
                self.unit, self._snap, recv, iface=name, changed=changed_names
            )
            if len(self.records) == self.records.maxlen:
                self.dropped += 1  # JIMGINA yo'qolmaydi -- hisoblanadi
            self.records.append(rec)
            self._cv.notify_all()
        if self.sink is not None:
            try:
                self.sink(rec)
            except Exception:  # noqa: BLE001 -- sink xatosi loop thread'ini o'ldirmaydi
                self.sink_errors += 1

    # --- o'qish ---
    def drain(self) -> list[dict[str, Any]]:
        with self._cv:
            out = list(self.records)
            self.records.clear()
            return out

    def snapshot(self) -> list[dict[str, Any]]:
        with self._cv:
            return list(self.records)

    def mark(self) -> int:
        """Joriy bufer uzunligi -- `wait_for(since=...)` uchun kursor.

        NEGA KERAK: `wait_for` default'da BUTUN buferni qidiradi, chunki
        harakat va `wait_for` chaqirig'i orasida kelgan record'ni o'tkazib
        yuborish o'lchovni yo'qotardi. Lekin unit yaratilishida ham
        `ActiveState=inactive` record'lari bo'ladi, demak "to'xtadi" ni
        kutayotgan kod eski record'ni topib, mutlaqo boshqa vaqtni o'qib
        olardi. To'g'ri naqsh:  idx = w.mark();  <harakat>;  w.wait_for(p, since=idx)
        """
        with self._cv:
            return len(self.records)

    def wait_for(
        self,
        predicate: Callable[[dict[str, Any]], bool],
        timeout_s: float = 10.0,
        *,
        since: int = 0,
    ) -> dict[str, Any] | None:
        """Predikatga mos record kelishini kutadi.

        `since` -- `mark()` dan olingan kursor; undan oldingi record'lar
        e'tiborga olinmaydi.
        """
        deadline = time.monotonic() + timeout_s
        seen = since
        with self._cv:
            while True:
                items = list(self.records)
                for rec in items[seen:]:
                    if predicate(rec):
                        return rec
                seen = len(items)
                left = deadline - time.monotonic()
                if left <= 0:
                    return None
                self._cv.wait(left)


# --- wait-for-active --------------------------------------------------------


def wait_for_active(
    systemd: SystemdUser,
    name: str,
    *,
    timeout_s: float = 10.0,
    poll_s: float = 0.01,
) -> dict[str, Any]:
    """Unit `active` bo'lishini kutadi. Timeout'da istisno tashlamaydi.

    Bu SOZLASH/XAVFSIZLIK yordamchisi, O'LCHOV YO'LI EMAS. O'lchov uchun
    `UnitWatcher` (signal) ishlatiladi -- polling har so'rovda D-Bus
    round-trip qiladi va uning narxi §8.2 probe-narx budjetiga kirardi.

    Qaytadi: {"ok", "active_state", "elapsed_us", "polls"}.
    Timeout XATO EMAS -- u O'LCHOV NATIJASI (masalan §9.2 (i)
    `TimeoutStartSec` mexanizmi), demak chaqiruvchi uni yozishi kerak.
    """
    t0 = mono_us()
    deadline = time.monotonic() + timeout_s
    polls = 0
    state: str | None = None
    while True:
        polls += 1
        state = systemd.active_state(name)
        if state == "active":
            return {"ok": True, "active_state": state, "elapsed_us": mono_us() - t0,
                    "polls": polls}
        if state in ("failed",):
            return {"ok": False, "active_state": state, "elapsed_us": mono_us() - t0,
                    "polls": polls}
        if time.monotonic() >= deadline:
            return {"ok": False, "active_state": state, "elapsed_us": mono_us() - t0,
                    "polls": polls}
        time.sleep(poll_s)


# --- property dump (run_meta uchun) -----------------------------------------


_SHOW_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)=(.*)$")


def parse_systemctl_show(text: str) -> dict[str, str]:
    """`systemctl show` chiqishini dict'ga aylantiradi.

    Ba'zi qiymatlar (StatusText va sh.k.) yangi qator o'z ichiga oladi, demak
    har qatorni `K=V` deb hisoblash noto'g'ri bo'lardi -- kalitga o'xshamagan
    qator oldingi qiymatga qo'shiladi.
    """
    out: dict[str, str] = {}
    last: str | None = None
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()   # chiqishning oxiridagi "\n" artefakti, qiymat emas
    for line in lines:
        m = _SHOW_KEY.match(line)
        if m:
            last = m.group(1)
            out[last] = m.group(2)
        elif last is not None:
            out[last] += "\n" + line
    return out


def dump_unit_properties(
    name: str,
    *,
    systemd: SystemdUser | None = None,
    require_alive: bool = True,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    """`run_meta` uchun unit'ning BARCHA property'larini JONLI obyektdan dump qiladi.

    FAQAT `systemctl --user show` (unit fayli yoki bizning niyatimiz emas) --
    shunda YOZILGAN narsa AYNAN ISHLAGAN narsa bo'ladi. Bizning property
    dict'imizni yozish "nima yubordik" ni yozardi, "systemd nima qabul qildi"
    ni emas; ular farq qilishi mumkin (masalan qiymat yumaloqlanishi).

    ⚠️ TUZOQ (docs/architecture/01-muhit-tekshiruvlari.md §4, bu yerda qayta
    tasdiqlangan): `--collect`/`CollectMode=` bilan tugagan unit YO'QOLADI, va
    `systemctl show` undan keyin rc=0 bilan TO'LIQ DEFAULT to'plamini
    chiqaradi (`LoadState=not-found`, `MemoryMax=infinity`, `RestartSteps=0`).
    Bu haqiqiy qiymatlarga o'xshab ko'rinadi. Shuning uchun:
      * dump faqat unit TIRIK paytida chaqirilishi kerak;
      * mavjudlik dump'dan OLDIN VA KEYIN tekshiriladi (unit dump o'rtasida
        o'chib qolsa ham ko'rinadi);
      * `dump_valid` va `load_state` HAR DUMP'ga yoziladi, demak yaroqsiz
        dump analizda jimgina haqiqiy deb o'tmaydi.
    """
    own = systemd is None
    sd = systemd or SystemdUser(connect_signals=False)
    try:
        alive_before = sd.unit_loaded(name)
        t0 = mono_us()
        proc = subprocess.run(
            ["systemctl", "--user", "show", "--no-pager", name],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        t1 = mono_us()
        alive_after = sd.unit_loaded(name)
    finally:
        if own:
            sd.close()
    props = parse_systemctl_show(proc.stdout)
    load_state = props.get("LoadState")
    valid = bool(alive_before and alive_after and load_state == "loaded" and proc.returncode == 0)
    out = {
        "unit": name,
        "source": "systemctl --user show",
        "alive_before": alive_before,
        "alive_after": alive_after,
        "load_state": load_state,
        "dump_valid": valid,
        "systemctl_rc": proc.returncode,
        "systemctl_stderr": proc.stderr.strip() or None,
        "mono_us_dump_begin": t0,
        "mono_us_dump_end": t1,
        "property_count": len(props),
        "properties": props,
    }
    if require_alive and not valid:
        raise UnitNotAliveError(
            f"{name}: property dump TIRIK unit talab qiladi "
            f"(alive_before={alive_before}, alive_after={alive_after}, "
            f"load_state={load_state!r}). `systemctl show` yo'q unit uchun "
            f"DEFAULT'larni qaytaradi va ular haqiqiy qiymatlarga o'xshaydi."
        )
    return out


# --- runtime drop-in'lar ----------------------------------------------------


def user_control_dir() -> str:
    """`set-property --runtime` drop-in'lari joylashadigan katalog."""
    xdg = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return f"{xdg}/systemd/user.control"


def list_runtime_drop_ins(patterns: Iterable[str] = (UNIT_GLOB, LAB_SLICE, MON_SLICE)) -> list[str]:
    """Glob'larga mos runtime drop-in kataloglari.

    Bular qoldiq holat: `SetUnitProperties(runtime=True)` o'zidan keyin
    `<unit>.d/` qoldiradi va u unit to'xtaganda O'CHMAYDI (bu mashinada
    tekshirilgan). Keyingi run slice'ni ishga tushirsa, oldingi run'ning
    `MemoryHigh=` i JIMGINA qo'llanardi.
    """
    d = user_control_dir()
    out = []
    try:
        entries = sorted(os.listdir(d))
    except OSError:
        return out
    for e in entries:
        if not e.endswith(".d"):
            continue
        unit = e[:-2]
        if any(fnmatch.fnmatch(unit, p) for p in patterns):
            out.append(f"{d}/{e}")
    return out


def clear_runtime_drop_ins(
    patterns: Iterable[str] = (UNIT_GLOB, LAB_SLICE, MON_SLICE),
    *,
    systemd: SystemdUser | None = None,
    reload: bool = True,
) -> list[str]:
    """Qoldiq runtime drop-in'larni o'chiradi. O'chirilganlar ro'yxati.

    `reload=True` -> `daemon-reload`, aks holda hali yuklangan unit eski
    drop-in qiymatini ushlab turardi. Reload O'LCHOV YO'LIDA EMAS (faqat run
    boshi/oxiri), shuning uchun narxi ahamiyatsiz.
    """
    removed = []
    for path in list_runtime_drop_ins(patterns):
        try:
            shutil.rmtree(path)
            removed.append(path)
        except OSError:
            pass
    if removed and reload:
        own = systemd is None
        sd = systemd or SystemdUser(connect_signals=False)
        try:
            sd.reload()
        except Exception:  # noqa: BLE001 -- tozalash reload xatosidan yiqilmaydi
            pass
        finally:
            if own:
                sd.close()
    return removed


# --- pre-flight -------------------------------------------------------------


def preflight(
    *,
    systemd: SystemdUser | None = None,
    unit_patterns: Sequence[str] = (UNIT_GLOB,),
    slices: Sequence[str] = (LAB_SLICE, MON_SLICE),
    check_drop_ins: bool = True,
    strict_drop_ins: bool = False,
) -> dict[str, Any]:
    """Qoldiq holat tekshiruvi. `{"clean": bool, "problems": [...], ...}`.

    NEGA: qoldiq unit yoki cgroup JIMGINA keyingi run'ga qo'shilib ketardi --
    eski `memory.current`, eski `NRestarts`, eski failed holat. O'lchov
    hissasi bo'lgan loyihada bu jimgina kontaminatsiya, demak run boshlanmaydi.

    Qat'iy rad etish mezonlari (docs/architecture/00-pilot-topologiya.md §2):
      * `revix-*` ga mos YUKLANGAN unit;
      * `revixlab.slice` / `revixmon.slice` (unit YOKI cgroup katalogi).

    Runtime drop-in'lar alohida `stale_drop_ins` ro'yxatida beriladi va
    default'da rad etmaydi: eksperimentning O'ZI ularni yaratadi
    (`set-property --runtime`), demak ular normal holatda `clear_runtime_drop_ins()`
    bilan tozalanadi, xato holati emas. Siyosat driver'da -- shuning uchun
    `strict_drop_ins` bayrog'i bor, lekin default qiymat siyosat qo'ymaydi.
    """
    own = systemd is None
    sd = systemd or SystemdUser(connect_signals=False)
    try:
        found_units: list[dict[str, Any]] = []
        seen = set()
        for pat in list(unit_patterns) + list(slices):
            for u in sd.list_units(pat):
                if u["unit"] in seen:
                    continue
                seen.add(u["unit"])
                found_units.append(u)
    finally:
        if own:
            sd.close()

    found_cgroups = []
    for sl in slices:
        try:
            path = cg.user_child(sl)
        except RuntimeError:
            continue
        if os.path.isdir(path):
            found_cgroups.append(path)

    stale_drop_ins = list_runtime_drop_ins(
        list(unit_patterns) + list(slices)
    ) if check_drop_ins else []

    problems = []
    for u in found_units:
        problems.append(f"qoldiq unit: {u['unit']} ({u['load_state']}/{u['active_state']})")
    for c in found_cgroups:
        problems.append(f"qoldiq cgroup: {c}")
    if strict_drop_ins:
        for d in stale_drop_ins:
            problems.append(f"qoldiq runtime drop-in: {d}")

    return {
        "clean": not problems,
        "problems": problems,
        "units": found_units,
        "cgroups": found_cgroups,
        "stale_drop_ins": stale_drop_ins,
        "unit_patterns": list(unit_patterns),
        "slices": list(slices),
        "mono_us": mono_us(),
    }


def require_clean(**kw: Any) -> dict[str, Any]:
    """`preflight()` va toza bo'lmasa `PreflightError`."""
    report = preflight(**kw)
    if not report["clean"]:
        raise PreflightError(report)
    return report


# --- teardown ---------------------------------------------------------------


def teardown(
    *,
    systemd: SystemdUser | None = None,
    units: Sequence[str] = (),
    unit_patterns: Sequence[str] = (UNIT_GLOB,),
    slices: Sequence[str] = (LAB_SLICE, MON_SLICE),
    kill: bool = True,
    reset_failed: bool = True,
    clear_drop_ins: bool = False,
    timeout_s: float = 15.0,
) -> dict[str, Any]:
    """Idempotent yig'ishtirish. IKKI MARTA CHAQIRISH XAVFSIZ.

    Tartib ahamiyatli:
      1. `cgroup.kill` -- ATOMIK subtree kill BIRINCHI. Shunda to'xtatish
         davomida hech bir jarayon fork qilib qutulib qolmaydi. Bu mexanizm
         privilegiyasiz ishlashi tekshirilgan
         (docs/architecture/01-muhit-tekshiruvlari.md §3).
      2. service'larni to'xtatish (`Restart=` qayta ko'tarmasligi uchun
         kill'dan keyin).
      3. slice'larni to'xtatish -- bo'sh slice O'ZI o'chmaydi, `loaded/active`
         bo'lib qoladi va keyingi pre-flight'ni to'g'ri ravishda yiqitadi.
      4. `reset-failed` -- faqat MOS unit'lar uchun, manager darajasida emas.

    Har qadam yo'q unit/cgroup'ni bosib o'tadi, shuning uchun takroriy
    chaqiruv xatosiz o'tadi.
    """
    own = systemd is None
    sd = systemd or SystemdUser(connect_signals=False)
    result: dict[str, Any] = {
        "mono_us_begin": mono_us(),
        "killed": [],
        "stopped": [],
        "reset": [],
        "removed_drop_ins": [],
        "errors": [],
    }
    try:
        # 1. atomik subtree kill
        if kill:
            for sl in slices:
                try:
                    path = cg.user_child(sl)
                except RuntimeError:
                    continue
                if os.path.isdir(path):
                    ok = cg.kill_subtree(path)
                    result["killed"].append({"cgroup": path, "ok": ok})

        # 2. service'lar: aniq nomlar + glob'ga mos yuklanganlar
        targets: list[str] = []
        for u in units:
            if u not in targets:
                targets.append(u)
        for pat in unit_patterns:
            try:
                for u in sd.list_units(pat):
                    if u["unit"] not in targets:
                        targets.append(u["unit"])
            except Exception as exc:  # noqa: BLE001
                result["errors"].append(f"list_units({pat!r}): {exc!r}")
        for u in targets:
            if u.endswith(".slice"):
                continue  # slice'lar 3-qadamda
            try:
                if sd.stop(u, timeout_s=timeout_s) is not None:
                    result["stopped"].append(u)
            except Exception as exc:  # noqa: BLE001
                result["errors"].append(f"stop({u!r}): {exc!r}")

        # 3. slice'lar -- eng oxirida, shunda childlar allaqachon ketgan
        for sl in list(slices) + [u for u in targets if u.endswith(".slice")]:
            try:
                if sd.stop(sl, timeout_s=timeout_s) is not None:
                    result["stopped"].append(sl)
            except Exception as exc:  # noqa: BLE001
                result["errors"].append(f"stop({sl!r}): {exc!r}")

        # 4. reset-failed
        if reset_failed:
            for u in targets:
                try:
                    if sd.reset_failed(u):
                        result["reset"].append(u)
                except Exception as exc:  # noqa: BLE001
                    result["errors"].append(f"reset_failed({u!r}): {exc!r}")
            for pat in unit_patterns:
                try:
                    result["reset"].extend(sd.reset_failed_pattern(pat))
                except Exception as exc:  # noqa: BLE001
                    result["errors"].append(f"reset_failed_pattern({pat!r}): {exc!r}")

        if clear_drop_ins:
            result["removed_drop_ins"] = clear_runtime_drop_ins(
                list(unit_patterns) + list(slices), systemd=sd
            )
    finally:
        if own:
            sd.close()
    result["mono_us_end"] = mono_us()
    return result
