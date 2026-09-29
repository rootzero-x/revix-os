"""cgroup v2 va PSI o'qish/yozish yordamchilari.

PREREGISTRATION.md §7 ni amalga oshiradi.

Asosiy qarorlar (tekshirilgan asosda -- docs/architecture/01-muhit-tekshiruvlari.md):
  * `total=` (monotonik mikrosekund akkumulyator) ASOSIY pressure o'lchovi.
    avgN eksponensial silliqlangan va 2 s kadensda yangilanadi, demak
    atributsiya uchun yaroqsiz. avgN ham yoziladi (arzon deployed gate aynan
    shuni o'qiydi), lekin analizda ikkilamchi.
  * PSI poll trigger ISHLATILMAYDI: privilegiyasiz oyna 2 s karrasi bo'lishi
    shart (kernel 7.1.5 da tasdiqlangan: 500ms/1000ms -> EINVAL).
  * fd bir marta ochiladi va har namunada pread(fd, 0) qilinadi -- har
    namunada qayta ochish syscall va dentry narxini qo'shardi.

KVANTLASH OGOHLIGI: PSI ichki yangilanish kadensi 2 s va `total` partiyalarda
kreditlanadi. Bitta 100 ms delta 0 o'qib, keyin sakrashi mumkin. 100 ms delta
ONIY TEZLIK EMAS. Tezlik uchun >=2 s oyna ishlatiladi.
"""

from __future__ import annotations

import os
import re
from typing import Any

CGROUP_ROOT = "/sys/fs/cgroup"

# PSI resurslari va ularning "full" satri bor-yo'qligi.
# cpu.pressure da "full" satri bor, lekin root cgroup'da doim 0.
PSI_RESOURCES = ("cpu", "io", "memory")

_PSI_LINE = re.compile(
    r"^(some|full)\s+avg10=([\d.]+)\s+avg60=([\d.]+)\s+avg300=([\d.]+)\s+total=(\d+)\s*$"
)


# --- yo'llar ----------------------------------------------------------------


def own_cgroup() -> str:
    """Joriy jarayonning cgroup yo'li (cgroup v2, "/" dan boshlanadi)."""
    with open("/proc/self/cgroup", "r") as fh:
        for line in fh:
            # cgroup v2: "0::/path"
            if line.startswith("0::"):
                return line.strip()[3:]
    raise RuntimeError("cgroup v2 yo'li topilmadi (/proc/self/cgroup da '0::' yo'q)")


def user_service_cgroup(uid: int | None = None) -> str:
    """user@UID.service cgroup yo'li (CGROUP_ROOT ga nisbatan emas, absolut).

    Bu oomd kuzatadigan va kill authority'ga ega scope -- guard aynan shuni
    kuzatadi (docs/architecture/00-pilot-topologiya.md §3.1).
    """
    if uid is None:
        uid = os.getuid()
    path = f"{CGROUP_ROOT}/user.slice/user-{uid}.slice/user@{uid}.service"
    if not os.path.isdir(path):
        raise RuntimeError(f"user@{uid}.service cgroup topilmadi: {path}")
    return path


def user_child(name: str, uid: int | None = None) -> str:
    """user@UID.service ning to'g'ridan-to'g'ri childi.

    DIQQAT: slice nomida '-' ierarxiya ajratuvchisi. 'a-b.slice' ->
    'a.slice/a-b.slice'. Shuning uchun revixlab/revixmon dash'siz nomlangan
    (PREREGISTRATION.md amendment v1 -> v1.1).
    """
    return f"{user_service_cgroup(uid)}/{name}"


# --- oddiy o'qish/yozish ----------------------------------------------------


def read_text(path: str) -> str | None:
    """Faylni o'qiydi; mavjud bo'lmasa yoki ruxsat bo'lmasa None.

    None qaytarish o'lchov yo'qolganini bildiradi va u shu tarzda log'lanadi --
    0 bilan almashtirilmaydi, chunki 0 haqiqiy o'lchov qiymati.
    """
    try:
        with open(path, "r") as fh:
            return fh.read()
    except (FileNotFoundError, PermissionError, OSError):
        return None


def read_int(path: str) -> int | None:
    t = read_text(path)
    if t is None:
        return None
    t = t.strip()
    if not t or t == "max":
        return None
    try:
        return int(t)
    except ValueError:
        return None


def read_keyed(path: str) -> dict[str, int]:
    """'kalit qiymat' satrlaridan iborat faylni o'qiydi (memory.stat, memory.events)."""
    t = read_text(path)
    out: dict[str, int] = {}
    if t is None:
        return out
    for line in t.splitlines():
        parts = line.split()
        if len(parts) == 2:
            try:
                out[parts[0]] = int(parts[1])
            except ValueError:
                pass
    return out


def write_text(path: str, value: str) -> bool:
    """Yozadi; muvaffaqiyat bo'lsa True. Istisno tashlamaydi -- chaqiruvchi
    (ayniqsa guard) hech qachon yozish xatosidan yiqilmasligi kerak."""
    try:
        with open(path, "w") as fh:
            fh.write(value)
        return True
    except OSError:
        return False


def kill_subtree(cgroup_path: str) -> bool:
    """cgroup.kill ga 1 yozib butun subtree'ni atomik o'ldiradi.

    Bu washout va guard teardown uchun asosiy mexanizm. Privilegiyasiz
    ishlashi bu mashinada tasdiqlangan
    (docs/architecture/01-muhit-tekshiruvlari.md §3).
    """
    return write_text(f"{cgroup_path}/cgroup.kill", "1")


# --- PSI --------------------------------------------------------------------


def parse_psi(text: str) -> dict[str, dict[str, float | int]]:
    """PSI fayl mazmunini {'some': {...}, 'full': {...}} ga aylantiradi.

    Kutilmagan satrlar jimgina tashlanmaydi -- ular xato sifatida ko'rinishi
    kerak, aks holda sxema o'zgarganda o'lchov jimgina buziladi.
    """
    out: dict[str, dict[str, float | int]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _PSI_LINE.match(line)
        if not m:
            raise ValueError(f"PSI satri tanilmadi: {line!r}")
        kind, a10, a60, a300, total = m.groups()
        out[kind] = {
            "avg10": float(a10),
            "avg60": float(a60),
            "avg300": float(a300),
            "total": int(total),
        }
    return out


class PsiFile:
    """Bitta PSI faylini ochiq fd bilan o'qiydi.

    fd bir marta ochiladi; har namunada pread(fd, 0). 10 Hz x 4 scope x 3
    resurs = 120 o'qish/sekund, demak har namunada open/close qilish sezilarli
    syscall va dentry yuki bo'lardi.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self._fd = os.open(path, os.O_RDONLY)

    def sample(self) -> tuple[int, dict[str, dict[str, float | int]]]:
        """(o'qish vaqti mono_us, psi dict) qaytaradi.

        O'qish vaqti HAR SCOPE UCHUN alohida qaytariladi: turli scope'lar turli
        vaqtda o'qiladi va ularni bir vaqtda deb ko'rsatish xato bo'lardi
        (PREREGISTRATION.md §7).
        """
        from .schema import mono_us  # kech import: schema cgroup'ga bog'liq emas

        t = mono_us()
        raw = os.pread(self._fd, 4096, 0).decode()
        return t, parse_psi(raw)

    def close(self) -> None:
        if self._fd >= 0:
            os.close(self._fd)
            self._fd = -1

    def __enter__(self) -> "PsiFile":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def stall_fraction(total_a: int, total_b: int, mono_a_us: int, mono_b_us: int) -> float | None:
    """[a, b] oralig'idagi aniq stall ulushi `total=` delta'sidan.

        (total(b) - total(a)) / (b - a)

    Silliqlash yo'q, oyna mos kelmasligi yo'q -- shuning uchun bu avgN dan
    atributsiya uchun qat'iy yaxshiroq.

    Oyna <2 s bo'lsa None qaytaradi: PSI 2 s kadensda partiyalarda kreditlanadi,
    demak qisqaroq oyna oniy tezlik emas va shunday talqin qilinmasligi kerak.
    """
    dt = mono_b_us - mono_a_us
    if dt < 2_000_000:
        return None
    if dt <= 0:
        return None
    return (total_b - total_a) / dt


# --- host holati ------------------------------------------------------------


def meminfo() -> dict[str, int]:
    """/proc/meminfo, kB da."""
    out: dict[str, int] = {}
    t = read_text("/proc/meminfo")
    if t is None:
        return out
    for line in t.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        parts = v.split()
        if parts:
            try:
                out[k.strip()] = int(parts[0])
            except ValueError:
                pass
    return out


def vmstat() -> dict[str, int]:
    """/proc/vmstat. Guard `oom_kill` ni shu yerdan kuzatadi."""
    return read_keyed("/proc/vmstat")


def host_psi(resource: str) -> dict[str, dict[str, float | int]] | None:
    t = read_text(f"/proc/pressure/{resource}")
    return parse_psi(t) if t is not None else None


def snapshot_cgroup(cgroup_path: str) -> dict[str, Any]:
    """Bir cgroup uchun o'lchov snapshot'i (env_snapshot record uchun)."""
    return {
        "memory_current": read_int(f"{cgroup_path}/memory.current"),
        "memory_peak": read_int(f"{cgroup_path}/memory.peak"),
        "memory_swap_current": read_int(f"{cgroup_path}/memory.swap.current"),
        "memory_max": read_int(f"{cgroup_path}/memory.max"),
        "memory_high": read_int(f"{cgroup_path}/memory.high"),
        "memory_events": read_keyed(f"{cgroup_path}/memory.events"),
        "memory_swap_events": read_keyed(f"{cgroup_path}/memory.swap.events"),
        "memory_stat": read_keyed(f"{cgroup_path}/memory.stat"),
        "cpu_stat": read_keyed(f"{cgroup_path}/cpu.stat"),
    }
