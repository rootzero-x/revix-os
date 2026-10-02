"""REVIX buyruq qatori vositasi -- `doctor`, `status`, `health`, `events`,
`version`, `run`, `analyze`, `figures`.

Subkomanda'lar:
  doctor   -- muhit pre-flight tekshiruvi: bu mashinada eksperiment XAVFSIZ
              ishga tushirilishi mumkinmi, bo'lmasa -- aynan nima uchun
  status   -- joriy holat: revix unit'lari, lab/mon cgroup'lari, PSI tezliklari
  health   -- mashina uchun siqilgan sog'liq satri
  events   -- JSONL hodisa oqimini o'qiladigan shaklda chiqarish
  version  -- VERSION fayli, git commit, ishchi daraxt tozaligi
  run      -- driver (`revix.driver`): bitta run = bitta katalog
  analyze  -- offline analiz (`revix.analyze`): trial_metrics -> analysis.json
  figures  -- figuralar (`revix.figures`): analysis.json -> figures/<nom>.svg

DIZAYN QOIDALARI (buzilmaydi):

  1. **Har subkomanda `--json` ni qo'llaydi** va BARQAROR kalitlar chiqaradi.
     Inson uchun default, mashina uchun so'rov bo'yicha. JSON kalitlari ingliz
     tilida; kalit qo'shiladi, hech qachon qayta ishlatilmaydi (schema.py
     qoidasi).

  2. **`doctor` hech qachon jimgina o'tmaydi.** Har tekshiruv TO'RTTA narsani
     beradi: holat (PASS/WARN/FAIL), KUZATILGAN qiymat, KERAKLI qiymat va
     buzilsa NIMA BO'LADI. "Tekshirildi ✓" degan bo'sh javob yo'q -- aks holda
     tekshiruv ishonch beradi, lekin hech narsa isbotlamaydi.

  3. **FAIL-CLOSED** (guard.py bilan bir xil doktrina): tekshiruvning o'zi
     istisno tashlasa yoki qiymatni aniqlay olmasa, natija PASS emas, FAIL
     bo'ladi. Aniqlanmagan holat "hammasi yaxshi" deb hisoblanmaydi.

  4. **Tekshiruv yon ta'sir qoldirmaydi.** Yagona istisno -- `cgroup_write`:
     u HAQIQIY yozishni sinaydi (aks holda tekshiruv doim o'tardi va hech
     narsa isbotlamasdi) va o'zidan keyin `rmdir` bilan tozalaydi. Tozalash
     bajarilmasa -- bu qoldiq holat, demak WARN bo'lib ko'rinadi.

  5. **PSI tezligi HAR YERDA `total=` delta'sidan**, avgN dan EMAS
     (PREREGISTRATION.md §7). Sabab `sample_psi_rates()` ichida yozilgan.

  6. **`doctor` FAIL bo'lsa non-zero bilan chiqadi.** Bu uni skriptdan
     gate sifatida ishlatish mumkin qiladi -- pre-flight tekshiruvining butun
     ma'nosi shu.

  7. **`run` / `analyze` / `figures` -- faqat DELEGATSIYA.** Har handler o'z
     `Namespace`'ini argv ro'yxatiga aylantiradi va `revix.<modul>.main(argv)`
     ni chaqiradi; modulning ichki funksiya/dataclass/konstantalari import
     QILINMAYDI. NEGA: bog'lanish bitta funksiyaga tushadi, modulga flag
     qo'shilsa bu yerni o'zgartirish shart emas va aylanma import bo'lmaydi.
     Modul LAZY (handler ichida) import qilinadi: `figures.py` matplotlib'ni
     import qiladi, `doctor` esa aynan buzuq muhitni tashxis qilish uchun bor
     -- top-level import uni matplotlib yo'q mashinada ham yiqitardi.
     Modul yo'q bo'lsa -- aniq xabar va non-zero chiqish, traceback emas.

Bu fayldagi har bir chegara va kutilgan qiymat hujjatlangan EMPIRIK faktdan
olingan: `docs/architecture/01-muhit-tekshiruvlari.md` (muhit),
`docs/architecture/00-pilot-topologiya.md` (topologiya va xavfsizlik chegarasi),
`docs/architecture/02-guard-kalibratsiyasi.md` (o'lchangan chegaralar).
Taxmin bilan qo'yilgan qiymat yo'q.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from . import cgroup as cg
from .guard import DEFAULTS as GUARD_DEFAULTS
from .schema import ENVELOPE_FIELDS, SCHEMA_VERSION, mono_us, read_boot_id, real_us

# --- doimiy talablar --------------------------------------------------------

# Bu paket va repo ildizi. VERSION va git holati repo ildizidan o'qiladi.
PKG_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PKG_DIR)

REPORT_SCHEMA_VERSION = 1

# systemd >= 254: `RestartSteps=` + `RestartMaxDelaySec=` shu versiyada paydo
# bo'ldi va ular Baseline B ning O'ZI (README "Baseline'lar" jadvali).
# Ular bo'lmasa B arm'i umuman yo'q, ya'ni H2 kuchli baseline'siz qoladi.
MIN_SYSTEMD_VERSION = 254

MIN_PYTHON = (3, 11)

# Delegatsiya: `DelegateControllers=cpu memory pids` (01-muhit §1 da tasdiqlangan).
REQUIRED_CONTROLLERS = ("cpu", "memory", "pids")
# `io` shu mashinada delegated EMAS -> io.max yozilmaydi -> IO fault injection
# root yoki QEMU guest talab qiladi. Bu WARN, FAIL emas: P1 IO injection
# ishlatmaydi (00-pilot-topologiya §4).
OPTIONAL_CONTROLLERS = ("io",)

PSI_RESOURCES = cg.PSI_RESOURCES  # ("cpu", "io", "memory")

# Slice nomlari dash'siz: systemd slice nomida '-' IERARXIYA ajratuvchisi
# (01-muhit §2 -- amendment v1 -> v1.1).
LAB_SLICE = "revixlab.slice"
MON_SLICE = "revixmon.slice"

# Reja bo'yicha eksperiment shifti: revixlab.slice MemoryMax=2G
# (00-pilot-topologiya §1).
PLANNED_CEILING_KB = 2 * 1024 * 1024

# Guard'dan olingan, KALIBRATSIYA bilan aniqlangan qiymatlar
# (02-guard-kalibratsiyasi). Bu yerda qayta yozilmaydi -- bitta haqiqat manbasi.
GUARD_MEM_FLOOR_KB = int(GUARD_DEFAULTS["host_mem_available_min_kb"])
GUARD_SUSTAIN_MAX_S = float(GUARD_DEFAULTS["sustain_max_seconds"])
GUARD_SUSTAIN_RATE = float(GUARD_DEFAULTS["sustain_rate_threshold"])

# oomd ning sustained shartidan pastda qolish uchun majburiy pressure oynasi
# (00-pilot-topologiya §3.1 (a), PREREGISTRATION §4).
PRESSURE_WINDOW_MAX_S = 12.0

# PSI kvantlash: ichki yangilanish kadensi 2 s, `total` partiyalarda
# kreditlanadi -> <2 s oyna oniy tezlik EMAS (PREREGISTRATION §7).
MIN_RATE_WINDOW_S = 2.0

REQUIRED_MODULES = ("psutil", "dbus", "numpy", "scipy")
# IXTIYORIY modullar: yo'qligi na pilotni, na tahlilni to'xtatadi -- faqat
# `revix figures` figura chiqara olmaydi (04-driver-va-analiz-shartnomasi §3).
# `doctor` FAIL'i o'lchashni to'xtatadigan narsalar uchun ajratilgan, shuning
# uchun bular yo'q bo'lsa WARN, FAIL emas.
OPTIONAL_MODULES = ("matplotlib",)
# `dbus` import nomi; distributiv nomi boshqacha (`dbus-python`).
_MODULE_DISTS = {
    "psutil": ("psutil",),
    "dbus": ("dbus-python", "dbus_python"),
    "numpy": ("numpy",),
    "scipy": ("scipy",),
    "matplotlib": ("matplotlib",),
}

# Delegated subtree'da haqiqatan yozilishi kerak bo'lgan fayllar
# (01-muhit §3 jadvali).
CGROUP_WRITE_PROBES = (
    ("memory.max", "max"),
    ("memory.high", "max"),
    ("memory.swap.max", "0"),
    ("cgroup.kill", "1"),  # bo'sh cgroup'da hech kimni o'ldirmaydi
)

# --- holat markerlari -------------------------------------------------------

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
STATUSES = (PASS, WARN, FAIL)


@dataclass
class Check:
    """Bitta pre-flight tekshiruvining natijasi.

    `consequence` MAJBURIY va har doim to'ldiriladi -- PASS holatda ham.
    Sabab: tekshiruv nima uchun borligini o'qiyotgan odam ko'rishi kerak.
    Inson chiqishida u faqat WARN/FAIL da bosiladi, lekin JSON'da doim bor.
    """

    key: str
    title: str
    status: str
    observed: str
    required: str
    consequence: str
    detail: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"noma'lum holat: {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "status": self.status,
            "observed": self.observed,
            "required": self.required,
            "consequence": self.consequence,
            "detail": self.detail,
        }


# --- kichik yordamchilar ----------------------------------------------------


def _run(argv: list[str], timeout: float = 5.0) -> tuple[int, str, str]:
    """Buyruqni ishga tushiradi; HECH QACHON istisno tashlamaydi.

    (rc, stdout, stderr) qaytaradi. Buyruq topilmasa rc=127, timeout bo'lsa
    rc=124 -- shell konvensiyasi bilan bir xil, shunda chaqiruvchi sababni
    ajrata oladi.
    """
    try:
        p = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", f"buyruq topilmadi: {argv[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout {timeout}s: {' '.join(argv)}"
    except OSError as exc:  # noqa: BLE001 -- tekshiruv vositasi yiqilmaydi
        return 126, "", repr(exc)


def human_kb(kb: int | None) -> str:
    """kB ni odam o'qiydigan shaklga (meminfo birliklari)."""
    if kb is None:
        return "?"
    units = (("GiB", 1024 * 1024), ("MiB", 1024), ("kiB", 1))
    for name, div in units:
        if kb >= div:
            return f"{kb / div:.1f} {name}"
    return f"{kb} kiB"


def _fmt_rate(v: float | None) -> str:
    return "-" if v is None else f"{v:.3f}"


# Jadval sarlavhasi uchun qisqa resurs nomlari (ustun kengligi 11).
_RES_LABEL = {"cpu": "cpu", "io": "io", "memory": "mem"}


def _show_property(unit: str, props: list[str], user_bus: bool = False) -> dict[str, str]:
    """`systemctl show` natijasini dict sifatida qaytaradi.

    Topilmagan property `[not set]` yoki yo'q bo'ladi -- qiymat o'zgartirilmaydi,
    chunki `[not set]` ning o'zi ma'noli (oomd uchun: per-unit override yo'q).
    """
    argv = ["systemctl"]
    if user_bus:
        argv.append("--user")
    argv.append("show")
    argv.append(unit)
    for p in props:
        argv += ["-p", p]
    rc, out, _err = _run(argv)
    res: dict[str, str] = {}
    if rc != 0:
        return res
    for line in out.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            res[k.strip()] = v.strip()
    return res


def _read_version_file() -> str | None:
    t = cg.read_text(os.path.join(REPO_ROOT, "VERSION"))
    return t.strip() if t is not None else None


# --- git --------------------------------------------------------------------


def git_info() -> dict[str, Any]:
    """Repo holati: git bor-yo'qligi, commit, ishchi daraxt tozaligi.

    Confirmatory run TOZA daraxt talab qiladi -- aks holda natija qaysi kod
    bilan olinganini aytib bo'lmaydi va run reproducible emas.
    """
    info: dict[str, Any] = {
        "git_present": shutil.which("git") is not None,
        "is_repo": False,
        "commit": None,
        "commit_short": None,
        "dirty": None,
        "dirty_paths": [],
        "error": None,
    }
    if not info["git_present"]:
        info["error"] = "git binari topilmadi"
        return info
    rc, out, err = _run(["git", "-C", REPO_ROOT, "rev-parse", "HEAD"])
    if rc != 0:
        info["error"] = (err or out).strip() or f"rev-parse rc={rc}"
        return info
    info["is_repo"] = True
    info["commit"] = out.strip()
    info["commit_short"] = out.strip()[:7]
    rc, out, err = _run(["git", "-C", REPO_ROOT, "status", "--porcelain"])
    if rc != 0:
        info["error"] = (err or out).strip() or f"status rc={rc}"
        return info
    paths = [ln for ln in out.splitlines() if ln.strip()]
    info["dirty"] = bool(paths)
    info["dirty_paths"] = paths[:20]
    return info


# --- PSI namuna olish -------------------------------------------------------


def psi_file_path(scope_root: str, resource: str) -> str:
    """Scope ildizi + resurs -> PSI fayl yo'li.

    Host uchun `/proc/pressure/<res>`, cgroup uchun `<cgroup>/<res>.pressure`.
    """
    if scope_root == "/proc/pressure":
        return f"/proc/pressure/{resource}"
    return f"{scope_root}/{resource}.pressure"


def sample_psi_rates(
    scopes: dict[str, str],
    interval_s: float = MIN_RATE_WINDOW_S,
    resources: tuple[str, ...] = PSI_RESOURCES,
) -> dict[str, dict[str, Any]]:
    """Scope'lar bo'yicha PSI stall tezligini `total=` delta'sidan o'lchaydi.

    NEGA `avgN` EMAS (PREREGISTRATION.md §7 -- muzlatilgan qaror):

      * `avgN` eksponensial silliqlangan va 2 s kadensda yangilanadi. Pressure
        boshlanganidan keyin haqiqiy qiymatga yetishi uchun ~10 s kerak, va
        pressure to'xtagandan keyin ham sekin pasayadi. Ya'ni `avgN` "hozir"
        ni ko'rsatmaydi -- u "so'nggi o'n soniya, silliqlangan" ni ko'rsatadi.
      * `total=` monotonik mikrosekund akkumulyator. Ikki o'qish orasidagi
        aniq stall ulushi: (total(b) - total(a)) / (b - a). Silliqlash yo'q,
        oyna mos kelmasligi yo'q.

    Oyna >= 2 s bo'lishi SHART: PSI ichki kadensi 2 s va `total` partiyalarda
    kreditlanadi, demak qisqaroq oyna oniy tezlik emas. `cg.stall_fraction`
    bu shartni o'zi ushlaydi va <2 s uchun None qaytaradi -- shuning uchun
    bu yerda ham interval majburan >= 2 s ga ko'tariladi.

    Har scope o'z o'qish timestamp'ini oladi: turli scope'lar turli vaqtda
    o'qiladi va ularni bir vaqtda deb ko'rsatish xato bo'lardi (§7).

    `avgN` baribir qaytariladi -- arzon deployed gate aynan shuni o'qiydi,
    demak u ikkilamchi o'lchov sifatida qiziq (§7). Lekin u TEZLIK emas.
    """
    interval_s = max(interval_s, MIN_RATE_WINDOW_S)

    # 1-faza: barcha fayllarni ochamiz (fd bir marta, keyin pread -- cgroup.py).
    handles: dict[tuple[str, str], cg.PsiFile] = {}
    errors: dict[str, dict[str, str]] = {}
    for scope, root in scopes.items():
        for res in resources:
            path = psi_file_path(root, res)
            try:
                handles[(scope, res)] = cg.PsiFile(path)
            except OSError as exc:
                errors.setdefault(scope, {})[res] = repr(exc)

    try:
        first: dict[tuple[str, str], tuple[int, dict]] = {}
        for k, fh in handles.items():
            try:
                first[k] = fh.sample()
            except (OSError, ValueError) as exc:
                errors.setdefault(k[0], {})[k[1]] = repr(exc)

        time.sleep(interval_s)

        out: dict[str, dict[str, Any]] = {}
        for scope, root in scopes.items():
            scope_out: dict[str, Any] = {
                "root": root,
                "resources": {},
                "errors": errors.get(scope, {}),
            }
            for res in resources:
                k = (scope, res)
                if k not in handles or k not in first:
                    scope_out["resources"][res] = None
                    continue
                try:
                    t1, psi1 = handles[k].sample()
                except (OSError, ValueError) as exc:
                    scope_out["errors"][res] = repr(exc)
                    scope_out["resources"][res] = None
                    continue
                t0, psi0 = first[k]
                entry: dict[str, Any] = {"window_us": t1 - t0}
                for kind in ("some", "full"):
                    a = psi0.get(kind)
                    b = psi1.get(kind)
                    if a is None or b is None:
                        entry[f"{kind}_rate"] = None
                        entry[f"{kind}_avg10"] = None
                        continue
                    entry[f"{kind}_rate"] = cg.stall_fraction(
                        int(a["total"]), int(b["total"]), t0, t1
                    )
                    # avgN IKKILAMCHI -- tezlik emas (§7). Nom shu bilan belgili.
                    entry[f"{kind}_avg10"] = float(b["avg10"])
                    entry[f"{kind}_total_us"] = int(b["total"])
                scope_out["resources"][res] = entry
            out[scope] = scope_out
        return out
    finally:
        for fh in handles.values():
            fh.close()


def default_scopes() -> dict[str, str]:
    """Status/health uchun scope'lar: host, user@UID.service, revixlab.slice.

    `revixmon.slice` (harness) ataylab QO'SHILMAYDI kovariata sifatida --
    lekin status uni alohida ko'rsatadi, chunki uning tirikligi muhim.
    """
    scopes: dict[str, str] = {"host": "/proc/pressure"}
    try:
        user = cg.user_service_cgroup()
    except RuntimeError:
        return scopes
    scopes[f"user@{os.getuid()}.service"] = user
    lab = f"{user}/{LAB_SLICE}"
    if os.path.isdir(lab):
        scopes[LAB_SLICE] = lab
    return scopes


# ===========================================================================
# doctor tekshiruvlari
# ===========================================================================


def check_systemd_version() -> Check:
    """systemd >= 254 -- `RestartSteps=` / `RestartMaxDelaySec=` uchun."""
    key, title = "systemd_version", "systemd versiyasi"
    consequence = (
        "systemd < 254 da `RestartSteps=` va `RestartMaxDelaySec=` yo'q -> "
        "Baseline B (systemd native exponential backoff) o'lchanmaydi, "
        "demak H2 kuchli baseline'siz qoladi."
    )
    required = f">= {MIN_SYSTEMD_VERSION}"
    rc, out, err = _run(["systemctl", "--version"])
    if rc != 0:
        return Check(key, title, FAIL, f"systemctl ishlamadi (rc={rc})", required,
                     consequence, {"rc": rc, "stderr": err.strip()[:400]})
    line = out.splitlines()[0].strip() if out.strip() else ""
    m = re.search(r"\bsystemd\s+(\d+)", line)
    if not m:
        # FAIL-CLOSED: versiyani aniqlay olmasak, o'tgan deb hisoblamaymiz.
        return Check(key, title, FAIL, f"versiya aniqlanmadi: {line!r}", required,
                     consequence, {"raw": line})
    ver = int(m.group(1))
    status = PASS if ver >= MIN_SYSTEMD_VERSION else FAIL
    return Check(key, title, status, line, required, consequence,
                 {"version": ver, "raw": line})


def check_cgroup_v2() -> Check:
    """cgroup v2 unified ierarxiyasi (`stat -fc %T /sys/fs/cgroup` = cgroup2fs)."""
    key, title = "cgroup_v2", "cgroup v2 unified"
    required = "cgroup2 (stat -fc %T = cgroup2fs)"
    consequence = (
        "cgroup v1 da `memory.pressure`, `cgroup.kill` va unified delegatsiya "
        "yo'q -> butun harness (pressure, guard teardown, per-cgroup PSI) "
        "ishlamaydi."
    )
    fstype = None
    mounts = cg.read_text("/proc/self/mounts")
    if mounts is not None:
        for line in mounts.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[1] == cg.CGROUP_ROOT:
                fstype = parts[2]
                break
    if fstype is None:
        return Check(key, title, FAIL, f"{cg.CGROUP_ROOT} mount topilmadi", required,
                     consequence, {})
    status = PASS if fstype == "cgroup2" else FAIL
    return Check(key, title, status, f"{fstype} ({cg.CGROUP_ROOT})", required,
                 consequence, {"fstype": fstype})


def _user_controllers() -> tuple[list[str], str | None, str | None]:
    """user@UID.service cgroup'ining controllers/subtree_control ro'yxati.

    Ground truth `cgroup.controllers` faylida, `systemctl show
    DelegateControllers` da emas: birinchisi haqiqatan mavjud bo'lgan,
    ikkinchisi so'ralgan konfiguratsiya.
    """
    try:
        user = cg.user_service_cgroup()
    except RuntimeError as exc:
        return [], None, repr(exc)
    ctrl = cg.read_text(f"{user}/cgroup.controllers")
    if ctrl is None:
        return [], user, f"{user}/cgroup.controllers o'qilmadi"
    return ctrl.split(), user, None


def check_delegated_controllers() -> Check:
    """`cpu memory pids` delegated bo'lishi shart."""
    key, title = "delegated_controllers", "Delegated controller'lar"
    required = " ".join(REQUIRED_CONTROLLERS)
    consequence = (
        "delegatsiya bo'lmasa transient user unit'lar `MemoryMax=`/`CPUQuota=`/"
        "`TasksMax=` qabul qilmaydi va delegated subtree'ga yozib bo'lmaydi -> "
        "pilot privilegiyasiz ishlamaydi (root/QEMU guest talab qiladi)."
    )
    ctrl, user, err = _user_controllers()
    if err is not None:
        return Check(key, title, FAIL, err, required, consequence,
                     {"cgroup": user})
    missing = [c for c in REQUIRED_CONTROLLERS if c not in ctrl]
    show = _show_property(f"user@{os.getuid()}.service",
                          ["Delegate", "DelegateControllers"])
    subtree = cg.read_text(f"{user}/cgroup.subtree_control")
    detail = {
        "cgroup": user,
        "cgroup_controllers": ctrl,
        "cgroup_subtree_control": (subtree or "").split(),
        "missing": missing,
        "systemctl_Delegate": show.get("Delegate"),
        "systemctl_DelegateControllers": show.get("DelegateControllers"),
    }
    status = PASS if not missing else FAIL
    observed = " ".join(ctrl) if ctrl else "(bo'sh)"
    if missing:
        observed += f"  -- YETMAYDI: {' '.join(missing)}"
    return Check(key, title, status, observed, required, consequence, detail)


def check_io_delegation() -> Check:
    """`io` delegatsiyasi -- IXTIYORIY. Bu mashinada YO'Q va bu WARN."""
    key, title = "io_delegation", "io controller delegatsiyasi"
    required = f"{' '.join(OPTIONAL_CONTROLLERS)} (ixtiyoriy -- P1 ishlatmaydi)"
    consequence = (
        "`io` delegated emas -> `io.max` yozilmaydi, demak IO fault injection "
        "root yoki QEMU guest talab qiladi. `io.pressure` BARIBIR o'qiladi, "
        "shuning uchun IO PSI o'lchash privilegiyasiz ishlaydi."
    )
    ctrl, user, err = _user_controllers()
    if err is not None:
        return Check(key, title, FAIL, err, required, consequence, {"cgroup": user})
    has_io = "io" in ctrl
    # `io.pressure` io controller o'chiq bo'lsa ham o'qiladi (01-muhit §3).
    io_psi_readable = False
    if user:
        t = cg.read_text(f"{user}/io.pressure")
        if t is not None:
            try:
                cg.parse_psi(t)
                io_psi_readable = True
            except ValueError:
                io_psi_readable = False
    detail = {
        "io_delegated": has_io,
        "io_pressure_readable": io_psi_readable,
        "consequence_scope": "IO fault injection root/guest talab qiladi",
    }
    if has_io:
        return Check(key, title, PASS, "io delegated", required, consequence, detail)
    observed = "io delegated EMAS"
    if io_psi_readable:
        observed += "; io.pressure o'qiladi (IO PSI o'lchanadi)"
    return Check(key, title, WARN, observed, required, consequence, detail)


def check_psi_host() -> Check:
    """`/proc/pressure/{cpu,io,memory}` o'qilishi va sxemasi."""
    key, title = "psi_host", "Host PSI (/proc/pressure)"
    required = "cpu, io, memory -- o'qiladi va parse bo'ladi"
    consequence = (
        "host PSI bo'lmasa pressure'ni o'lchab bo'lmaydi -> H1 ning tushuntiruvchi "
        "o'zgaruvchisi yo'q, demak eksperimentning ma'nosi qolmaydi."
    )
    ok: list[str] = []
    bad: dict[str, str] = {}
    for res in PSI_RESOURCES:
        t = cg.read_text(f"/proc/pressure/{res}")
        if t is None:
            bad[res] = "o'qilmadi (CONFIG_PSI=n?)"
            continue
        try:
            cg.parse_psi(t)
            ok.append(res)
        except ValueError as exc:
            bad[res] = f"sxema tanilmadi: {exc}"
    status = PASS if not bad else FAIL
    observed = ", ".join(ok) if ok else "hech biri"
    if bad:
        observed += "  -- BUZUQ: " + ", ".join(f"{k}: {v}" for k, v in bad.items())
    return Check(key, title, status, observed, required, consequence,
                 {"ok": ok, "bad": bad})


def check_psi_cgroup() -> Check:
    """Per-cgroup `*.pressure` o'qilishi (user@UID.service scope'ida)."""
    key, title = "psi_cgroup", "Per-cgroup PSI (*.pressure)"
    required = "user@UID.service da cpu/io/memory.pressure o'qiladi"
    consequence = (
        "per-cgroup PSI bo'lmasa guard `user@UID.service` ni kuzata olmaydi va "
        "asosiy scope (`revixlab.slice`) atributsiyasi yo'qoladi -- "
        "PREREGISTRATION §7 ning asosiy o'lchovi aynan shu."
    )
    try:
        user = cg.user_service_cgroup()
    except RuntimeError as exc:
        return Check(key, title, FAIL, repr(exc), required, consequence, {})
    ok: list[str] = []
    bad: dict[str, str] = {}
    for res in PSI_RESOURCES:
        path = f"{user}/{res}.pressure"
        t = cg.read_text(path)
        if t is None:
            bad[res] = f"o'qilmadi: {path}"
            continue
        try:
            cg.parse_psi(t)
            ok.append(res)
        except ValueError as exc:
            bad[res] = f"sxema tanilmadi: {exc}"
    status = PASS if not bad else FAIL
    observed = ", ".join(f"{r}.pressure" for r in ok) if ok else "hech biri"
    if bad:
        observed += "  -- BUZUQ: " + ", ".join(f"{k}: {v}" for k, v in bad.items())
    return Check(key, title, status, observed, required, consequence,
                 {"cgroup": user, "ok": ok, "bad": bad})


# --- oomd -------------------------------------------------------------------

# systemd `ManagedOOMMemoryPressureLimit` ni D-Bus'da UINT32 shkalasida beradi:
# UINT32_MAX = 100%. Shu mashinada 50% konfiguratsiyasi 2147483648 (= 2^31)
# bo'lib ko'rindi, va 2^31 / UINT32_MAX = 0.5000000001 -> 50%.
# Eski/boshqa versiyalar "50.00%" satri berishi mumkin, shuning uchun ikkisi
# ham qo'llanadi.
_UINT32_MAX = 4294967295


def parse_oom_pressure_limit(raw: str | None) -> float | None:
    """`ManagedOOMMemoryPressureLimit` ni foizga aylantiradi.

    Satr `%` bilan tugasa -- to'g'ridan-to'g'ri foiz. Butun son bo'lsa --
    UINT32_MAX shkalasi. 0 "per-unit override yo'q" degani (oomd.conf
    default'i qo'llanadi) va 0.0 sifatida qaytariladi -- chaqiruvchi shu
    holatni alohida ishlaydi.
    """
    if raw is None:
        return None
    raw = raw.strip()
    if not raw or raw == "[not set]":
        return None
    if raw.endswith("%"):
        try:
            return float(raw[:-1])
        except ValueError:
            return None
    try:
        n = int(raw)
    except ValueError:
        return None
    if n < 0:
        return None
    return round(n / _UINT32_MAX * 100.0, 4)


def parse_duration_sec(raw: str | None) -> float | None:
    """systemd davomiyligini soniyaga aylantiradi ("20s", "1min 30s", "500ms")."""
    if raw is None:
        return None
    raw = raw.strip()
    if not raw or raw in ("[not set]", "infinity"):
        return None
    if raw == "0":
        return 0.0
    mult = {
        "us": 1e-6, "usec": 1e-6,
        "ms": 1e-3, "msec": 1e-3,
        "s": 1.0, "sec": 1.0, "second": 1.0, "seconds": 1.0,
        "m": 60.0, "min": 60.0, "minute": 60.0, "minutes": 60.0,
        "h": 3600.0, "hr": 3600.0, "hour": 3600.0, "hours": 3600.0,
    }
    total = 0.0
    found = False
    for num, unit in re.findall(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]*)", raw):
        u = unit.lower()
        if u == "":
            # Birlik yo'q -> soniya deb qabul qilinadi (systemd konvensiyasi).
            total += float(num)
            found = True
            continue
        if u not in mult:
            return None
        total += float(num) * mult[u]
        found = True
    return total if found else None


def _oomd_conf_defaults() -> dict[str, str]:
    """`oomd.conf` ning EFFEKTIV qiymatlari.

    `systemd-analyze cat-config` fayllarni ustuvorlik tartibida birlashtiradi;
    oxirgi izohlanmagan tayinlash g'olib bo'ladi. Buyruq bo'lmasa fayllar
    qo'lda o'qiladi (fallback), chunki oomd chegarasi eng muhim tekshiruv
    bo'lib, uni bitta subprocess'ga bog'lab qo'yish mo'rt bo'lardi.
    """
    keys = ("DefaultMemoryPressureDurationSec", "DefaultMemoryPressureLimit")
    out: dict[str, str] = {}

    def absorb(text: str) -> None:
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            if "=" not in line:
                continue
            k, _, v = line.partition("=")
            k = k.strip()
            if k in keys:
                out[k] = v.strip()

    rc, stdout, _err = _run(["systemd-analyze", "cat-config", "systemd/oomd.conf"])
    if rc == 0 and stdout.strip():
        absorb(stdout)
        return out

    # Fallback: ustuvorlik tartibida (past -> yuqori), keyingisi ustidan yozadi.
    candidates = [
        "/usr/lib/systemd/oomd.conf",
        "/etc/systemd/oomd.conf",
    ]
    for d in ("/usr/lib/systemd/oomd.conf.d", "/run/systemd/oomd.conf.d",
              "/etc/systemd/oomd.conf.d"):
        try:
            for name in sorted(os.listdir(d)):
                if name.endswith(".conf"):
                    candidates.append(os.path.join(d, name))
        except OSError:
            pass
    for path in candidates:
        t = cg.read_text(path)
        if t is not None:
            absorb(t)
    return out


def oomd_state() -> dict[str, Any]:
    """oomd holati va user@UID.service ga nisbatan EFFEKTIV chegaralari."""
    uid = os.getuid()
    unit = f"user@{uid}.service"
    rc_a, out_a, _ = _run(["systemctl", "is-active", "systemd-oomd.service"])
    rc_e, out_e, _ = _run(["systemctl", "is-enabled", "systemd-oomd.service"])
    props = _show_property(
        unit,
        [
            "ManagedOOMMemoryPressure",
            "ManagedOOMMemoryPressureLimit",
            "ManagedOOMMemoryPressureDurationUSec",
            "ManagedOOMSwap",
            "ManagedOOMPreference",
            "ManagedOOMKills",
        ],
    )
    conf = _oomd_conf_defaults()

    active_raw = out_a.strip() or f"rc={rc_a}"
    mode = props.get("ManagedOOMMemoryPressure")

    limit_unit = parse_oom_pressure_limit(props.get("ManagedOOMMemoryPressureLimit"))
    limit_default = parse_oom_pressure_limit(conf.get("DefaultMemoryPressureLimit"))
    # Per-unit 0 => "belgilanmagan" => oomd.conf default'i qo'llanadi.
    if limit_unit is None or limit_unit == 0.0:
        limit_eff = limit_default
        limit_src = "oomd.conf"
    else:
        limit_eff = limit_unit
        limit_src = unit

    dur_unit = props.get("ManagedOOMMemoryPressureDurationUSec")
    dur_unit_s = None
    if dur_unit and dur_unit != "[not set]":
        dur_unit_s = parse_duration_sec(dur_unit)
    dur_default_s = parse_duration_sec(conf.get("DefaultMemoryPressureDurationSec"))
    if dur_unit_s is not None:
        dur_eff, dur_src = dur_unit_s, unit
    else:
        dur_eff, dur_src = dur_default_s, "oomd.conf"

    return {
        "unit": unit,
        "oomd_active": active_raw == "active",
        "oomd_active_raw": active_raw,
        "oomd_enabled_raw": out_e.strip() or f"rc={rc_e}",
        "managed_oom_memory_pressure": mode,
        "managed_oom_swap": props.get("ManagedOOMSwap"),
        "managed_oom_preference": props.get("ManagedOOMPreference"),
        "managed_oom_kills": props.get("ManagedOOMKills"),
        "pressure_limit_raw": props.get("ManagedOOMMemoryPressureLimit"),
        "pressure_limit_percent": limit_eff,
        "pressure_limit_source": limit_src,
        "duration_raw_unit": dur_unit,
        "duration_default_raw": conf.get("DefaultMemoryPressureDurationSec"),
        "duration_effective_s": dur_eff,
        "duration_source": dur_src,
        "kill_authority": (active_raw == "active" and mode == "kill"),
        "oomd_conf": conf,
    }


OOMD_MITIGATION = (
    "YUMSHATISH: har pressure epizodi <= 12 s (oomd ning sustained shartidan "
    "kam) + >= 20 s quiescence, VA mustaqil guard (`python3 -m revix.guard`) "
    "2 s tezlik >= 0.35 holati 15 s davom etsa `revixlab.slice/cgroup.kill` ga "
    "yozadi."
)


def check_oomd() -> Check:
    """⚠️ ENG MUHIM TEKSHIRUV -- oomd foydalanuvchi sessiyasini o'ldirishi.

    Bu xavf gipoteza emas, tekshirilgan fakt (01-muhit §7):
        ManagedOOMMemoryPressure=kill, limit 50%, DurationSec=20s
    PSI IERARXIK -> `revixlab.slice` ichidagi stall yuqoriga `user@UID.service`
    ga tarqaladi. Nishon brauzer, editor, IDE, GNOME sessiyasi -- yoki ishlab
    chiqish vositasi bo'lishi mumkin (00-pilot-topologiya §3.1).

    TASNIF MANTIQI:
      * kill authority yo'q                        -> PASS
      * kill authority bor, duration > guard 15 s  -> WARN (yumshatish HAQIQIY)
      * kill authority bor, duration <= guard 15 s -> FAIL (yumshatish YO'Q:
        guard oomd'dan oldin ulgurmaydi, ya'ni 12 s oyna kafolat bermaydi)
      * duration aniqlanmadi                       -> FAIL (fail-closed)
    """
    key, title = "oomd", "systemd-oomd kill authority"
    st = oomd_state()
    required = (
        f"kill authority bo'lsa: oomd duration > {GUARD_SUSTAIN_MAX_S:g} s "
        f"(guard sustain chegarasi), pressure oynasi <= {PRESSURE_WINDOW_MAX_S:g} s"
    )
    consequence = (
        "oomd `user@UID.service` avlodini o'ldirish huquqiga ega va PSI "
        "ierarxik -> ehtiyotsiz pressure eksperimenti BRAUZERINGIZNI, "
        "EDITORINGIZNI yoki BUTUN DESKTOP SESSIYANGIZNI o'ldiradi. "
        + OOMD_MITIGATION
    )
    dur = st["duration_effective_s"]
    lim = st["pressure_limit_percent"]

    parts = [f"oomd {st['oomd_active_raw']} (enabled={st['oomd_enabled_raw']})"]
    parts.append(f"{st['unit']}: ManagedOOMMemoryPressure={st['managed_oom_memory_pressure']}")
    parts.append(
        "limit=" + ("?" if lim is None else f"{lim:g}%")
        + f" [{st['pressure_limit_source']}, raw={st['pressure_limit_raw']}]"
    )
    parts.append(
        "duration=" + ("?" if dur is None else f"{dur:g}s")
        + f" [{st['duration_source']}]"
    )
    observed = "; ".join(parts)

    detail = dict(st)
    detail["guard_sustain_max_s"] = GUARD_SUSTAIN_MAX_S
    detail["pressure_window_max_s"] = PRESSURE_WINDOW_MAX_S
    detail["mitigation"] = OOMD_MITIGATION

    if not st["kill_authority"]:
        detail["risk"] = "low"
        return Check(key, title, PASS,
                     observed + " -- kill authority YO'Q", required, consequence, detail)

    if dur is None:
        # FAIL-CLOSED: oomd ning sustained oynasini bilmasak, 12 s oynasi
        # yetarli ekanini ISBOTLAY OLMAYMIZ.
        detail["risk"] = "unknown"
        return Check(key, title, FAIL,
                     observed + " -- duration ANIQLANMADI", required, consequence, detail)

    if dur <= GUARD_SUSTAIN_MAX_S:
        detail["risk"] = "critical"
        return Check(
            key, title, FAIL,
            observed + f" -- duration {dur:g}s <= guard sustain "
                       f"{GUARD_SUSTAIN_MAX_S:g}s, guard ULGURMAYDI",
            required, consequence, detail)

    detail["risk"] = "high-mitigated"
    detail["margin_s"] = dur - GUARD_SUSTAIN_MAX_S
    return Check(key, title, WARN,
                 observed + f" -- KILL AUTHORITY BOR (zaxira "
                            f"{dur - GUARD_SUSTAIN_MAX_S:g}s)",
                 required, consequence, detail)


# --- qoldiq holat -----------------------------------------------------------


def leftover_state() -> dict[str, Any]:
    """Oldingi run'dan qolgan unit va cgroup'lar.

    Bloklovchi (pre-flight run'ni TO'XTATADI, 00-pilot-topologiya §2):
      * `revix-*` unit'lar
      * `revixlab.slice` / `revixmon.slice` cgroup'lari

    Ogohlantiruvchi: boshqa `revix*` unit yoki cgroup. Ular ro'yxatda
    emas, lekin parallel faoliyat belgisi -- jimgina o'tkazib yuborilmaydi.

    `revixdoctor-*` cgroup'lari BU tekshiruvning o'z throwaway probe'i
    (`check_cgroup_write`) va ataylab chiqarib tashlanadi -- aks holda doctor
    o'zini qoldiq deb ko'rsatardi.
    """
    uid = os.getuid()
    res: dict[str, Any] = {
        "blocking_units": [],
        "advisory_units": [],
        "blocking_cgroups": [],
        "advisory_cgroups": [],
        "unit_query_ok": False,
        "unit_query_error": None,
    }
    rc, out, err = _run(
        ["systemctl", "--user", "list-units", "revix*", "--all",
         "--no-legend", "--plain"]
    )
    if rc == 0:
        res["unit_query_ok"] = True
        for line in out.splitlines():
            parts = line.split()
            if not parts:
                continue
            name = parts[0]
            if name.startswith("revix-"):
                res["blocking_units"].append(name)
            else:
                res["advisory_units"].append(name)
    else:
        res["unit_query_error"] = (err or out).strip()[:300] or f"rc={rc}"

    try:
        user = cg.user_service_cgroup(uid)
    except RuntimeError as exc:
        res["cgroup_error"] = repr(exc)
        return res
    res["user_cgroup"] = user
    for name in (LAB_SLICE, MON_SLICE):
        if os.path.isdir(f"{user}/{name}"):
            res["blocking_cgroups"].append(name)
    try:
        for name in sorted(os.listdir(user)):
            if not name.startswith("revix"):
                continue
            if name in (LAB_SLICE, MON_SLICE):
                continue
            if name.startswith("revixdoctor-"):
                continue  # doctor'ning o'z probe'i
            if os.path.isdir(f"{user}/{name}"):
                res["advisory_cgroups"].append(name)
    except OSError as exc:
        res["cgroup_error"] = repr(exc)
    return res


def check_leftover_state() -> Check:
    """Qoldiq `revix-*` unit / `revixlab|revixmon.slice` cgroup'lari."""
    key, title = "leftover_state", "Qoldiq holat (pre-flight blokirovkasi)"
    required = f"revix-* unit yo'q; {LAB_SLICE}/{MON_SLICE} cgroup'lari yo'q"
    consequence = (
        "qoldiq unit yoki cgroup bo'lsa run BOSHLANMAYDI: oldingi run'ning "
        "holati (memory.max, xotira iste'moli, tirik jarayonlar) o'lchovni "
        "ifloslantiradi va trial'lar mustaqil bo'lmaydi "
        "(00-pilot-topologiya §2)."
    )
    st = leftover_state()
    if not st["unit_query_ok"]:
        # FAIL-CLOSED: qoldiq bor-yo'qligini bilmasak, toza deb hisoblamaymiz.
        return Check(key, title, FAIL,
                     f"unit ro'yxati o'qilmadi: {st.get('unit_query_error')}",
                     required, consequence, st)
    blocking = st["blocking_units"] + st["blocking_cgroups"]
    advisory = st["advisory_units"] + st["advisory_cgroups"]
    if blocking:
        return Check(key, title, FAIL, "BLOKLOVCHI qoldiq: " + ", ".join(blocking),
                     required, consequence, st)
    if advisory:
        return Check(key, title, WARN,
                     "revix-* yo'q, lekin boshqa revix* obyekt bor: "
                     + ", ".join(advisory),
                     required, consequence, st)
    return Check(key, title, PASS, "qoldiq yo'q (unit ham, cgroup ham)",
                 required, consequence, st)


# --- cgroup yozish ----------------------------------------------------------


def check_cgroup_write() -> Check:
    """Delegated subtree'da HAQIQIY yozishni sinaydi va tozalaydi.

    Fayl mavjudligini tekshirish YETARLI EMAS: fayl bor bo'lib, yozishda
    EACCES/EROFS berishi mumkin. Tekshiruv haqiqiy yozishni bajarmasa, u doim
    o'tadi va hech narsa isbotlamaydi.

    Throwaway cgroup `user@UID.service` ning to'g'ridan-to'g'ri childi sifatida
    `mkdir` bilan yaratiladi (systemd unit'siz -- unit yaratish qoldiq holat
    xavfi tug'diradi), keyin `rmdir` bilan o'chiriladi. `cgroup.kill` ga 1
    yozish bo'sh cgroup'da hech kimni o'ldirmaydi.
    """
    key, title = "cgroup_write", "Delegated cgroup'ga yozish"
    required = ", ".join(f for f, _ in CGROUP_WRITE_PROBES) + " -- yoziladi"
    consequence = (
        "bu fayllar yozilmasa: `memory.max`/`memory.high` yo'q -> pressure "
        "dosing yo'q; `memory.swap.max` yo'q -> swap thrash xavfi; "
        "`cgroup.kill` yo'q -> guard teardown va washout mexanizmi yo'q, "
        "ya'ni eksperiment xavfsiz to'xtatilmaydi."
    )
    try:
        user = cg.user_service_cgroup()
    except RuntimeError as exc:
        return Check(key, title, FAIL, repr(exc), required, consequence, {})

    name = f"revixdoctor-{os.getpid()}-{os.urandom(3).hex()}"
    path = f"{user}/{name}"
    detail: dict[str, Any] = {"probe_cgroup": path, "writes": {},
                              "created": False, "cleaned_up": None}
    try:
        os.mkdir(path)
    except OSError as exc:
        detail["mkdir_error"] = repr(exc)
        return Check(key, title, FAIL,
                     f"throwaway cgroup yaratilmadi: {exc.strerror or exc}",
                     required, consequence, detail)
    detail["created"] = True
    failed: list[str] = []
    try:
        for fname, value in CGROUP_WRITE_PROBES:
            fpath = f"{path}/{fname}"
            if not os.path.exists(fpath):
                detail["writes"][fname] = "fayl yo'q"
                failed.append(fname)
                continue
            ok = cg.write_text(fpath, value)
            detail["writes"][fname] = "ok" if ok else "yozilmadi"
            if not ok:
                failed.append(fname)
        # Yangi childda per-cgroup PSI ham o'qilishi kerak.
        psi_txt = cg.read_text(f"{path}/memory.pressure")
        psi_ok = False
        if psi_txt is not None:
            try:
                cg.parse_psi(psi_txt)
                psi_ok = True
            except ValueError:
                psi_ok = False
        detail["child_memory_pressure_readable"] = psi_ok
        if not psi_ok:
            failed.append("memory.pressure")
    finally:
        try:
            os.rmdir(path)
            detail["cleaned_up"] = True
        except OSError as exc:
            detail["cleaned_up"] = False
            detail["cleanup_error"] = repr(exc)

    if failed:
        return Check(key, title, FAIL,
                     "yozilmadi/o'qilmadi: " + ", ".join(failed),
                     required, consequence, detail)
    if detail["cleaned_up"] is not True:
        return Check(key, title, WARN,
                     f"hammasi yozildi, lekin probe cgroup o'chmadi: {path}",
                     required, consequence, detail)
    return Check(key, title, PASS,
                 "hammasi yozildi va probe cgroup tozalandi",
                 required, consequence, detail)


# --- resurs zaxirasi --------------------------------------------------------


def check_memory_headroom() -> Check:
    """MemAvailable reja bo'yicha shift + guard poli uchun yetarlimi."""
    key, title = "memory_headroom", "Xotira zaxirasi"
    need_kb = PLANNED_CEILING_KB + GUARD_MEM_FLOOR_KB
    comfort_kb = need_kb + 1024 * 1024  # +1 GiB qulay zaxira
    required = (
        f">= {human_kb(need_kb)} MemAvailable "
        f"({human_kb(PLANNED_CEILING_KB)} shift + {human_kb(GUARD_MEM_FLOOR_KB)} guard poli)"
    )
    consequence = (
        "zaxira yetmasa: guard `host_mem_available` chegarasida darhol trip "
        "qiladi (har trial `aborted_guard`), yoki kernel global OOM killer "
        "eksperiment tashqarisidagi jarayonni o'ldiradi."
    )
    mi = cg.meminfo()
    avail = mi.get("MemAvailable")
    total = mi.get("MemTotal")
    if avail is None:
        return Check(key, title, FAIL, "/proc/meminfo dan MemAvailable o'qilmadi",
                     required, consequence, {"meminfo_keys": len(mi)})
    detail = {
        "mem_available_kb": avail,
        "mem_total_kb": total,
        "required_kb": need_kb,
        "planned_ceiling_kb": PLANNED_CEILING_KB,
        "guard_floor_kb": GUARD_MEM_FLOOR_KB,
        "comfort_kb": comfort_kb,
    }
    observed = f"MemAvailable={human_kb(avail)} (MemTotal={human_kb(total)})"
    if avail < need_kb:
        return Check(key, title, FAIL, observed, required, consequence, detail)
    if avail < comfort_kb:
        return Check(key, title, WARN,
                     observed + f" -- zaxira yupqa (< {human_kb(comfort_kb)})",
                     required, consequence, detail)
    return Check(key, title, PASS, observed, required, consequence, detail)


def check_swap_headroom() -> Check:
    """Swap holati: eksperiment `MemorySwapMax=0`, lekin HOST swap'i muhim."""
    key, title = "swap_headroom", "Swap holati"
    required = "swap mavjud va tinch holatda deyarli ishlatilmagan (< 10%)"
    consequence = (
        "swap allaqachon band bo'lsa host xotira siqilishida -> reclaim "
        "sekinlashadi, timing o'lchovi DVFS/IO bilan aralashadi va guard "
        "`host_mem_available` da trip qilishi mumkin. Swap butunlay yo'q "
        "bo'lsa reclaim yo'li qisqa: kernel OOM killer'ga tezroq yetiladi."
    )
    mi = cg.meminfo()
    total = mi.get("SwapTotal")
    free = mi.get("SwapFree")
    if total is None or free is None:
        return Check(key, title, FAIL, "/proc/meminfo dan SwapTotal/SwapFree o'qilmadi",
                     required, consequence, {})
    used = total - free
    pct = (used / total * 100.0) if total > 0 else 0.0
    detail = {"swap_total_kb": total, "swap_free_kb": free,
              "swap_used_kb": used, "swap_used_percent": round(pct, 2),
              "lab_swap_policy": "MemorySwapMax=0 (00-pilot-topologiya §2)"}
    if total == 0:
        return Check(key, title, WARN, "swap yo'q (SwapTotal=0)",
                     required, consequence, detail)
    observed = (f"SwapTotal={human_kb(total)}, ishlatilgan {human_kb(used)} "
                f"({pct:.1f}%)")
    status = PASS if pct < 10.0 else WARN
    return Check(key, title, status, observed, required, consequence, detail)


# --- CPU --------------------------------------------------------------------


def _cpufreq_values(fname: str) -> list[str]:
    base = "/sys/devices/system/cpu"
    vals: list[str] = []
    try:
        names = sorted(n for n in os.listdir(base) if re.fullmatch(r"cpu\d+", n))
    except OSError:
        return vals
    for n in names:
        t = cg.read_text(f"{base}/{n}/cpufreq/{fname}")
        if t is not None:
            vals.append(t.strip())
    return vals


def check_cpu_governor() -> Check:
    """`powersave` + `amd-pstate-epp` -- TIMING CONFOUND (PREREGISTRATION §8.5).

    Bu hech qachon FAIL emas: validlik masalasi, xavfsizlik emas. Lekin jimgina
    o'tkazib yuborilmaydi -- sustained yuk chastotani pasaytiradi, demak yuk
    ostidagi response-time o'lchovi kontentsiya bilan DVFS ni ARALASHTIRADI.
    """
    key, title = "cpu_governor", "CPU governor / scaling driver"
    required = "performance (aks holda chastota kovariata sifatida log'lanadi)"
    consequence = (
        "`powersave` + DVFS: sustained yuk chastotani pasaytiradi, demak yuk "
        "ostidagi latency o'lchovi kontentsiya va DVFS ni aralashtiradi. "
        "Yumshatish: blok ichida randomizatsiya + har trial chegarasida "
        "`scaling_cur_freq` log'lash; chastota arm bo'yicha tizimli farq qilsa "
        "timing taqqoslashlari HAQIQIY EMAS (PREREGISTRATION §8.5). "
        "`performance` root talab qiladi."
    )
    govs = _cpufreq_values("scaling_governor")
    drvs = _cpufreq_values("scaling_driver")
    detail = {
        "governors": sorted(set(govs)),
        "drivers": sorted(set(drvs)),
        "cpu_count": len(govs),
        "os_cpu_count": os.cpu_count(),
    }
    if not govs:
        return Check(key, title, WARN, "cpufreq interfeysi yo'q (VM yoki driver yo'q)",
                     required, consequence, detail)
    uniq_g = sorted(set(govs))
    uniq_d = sorted(set(drvs)) or ["?"]
    observed = (f"governor={','.join(uniq_g)}, driver={','.join(uniq_d)} "
                f"({len(govs)}/{os.cpu_count()} CPU)")
    if uniq_g == ["performance"]:
        return Check(key, title, PASS, observed, required, consequence, detail)
    return Check(key, title, WARN, observed + " -- DVFS timing confound",
                 required, consequence, detail)


# --- toolchain --------------------------------------------------------------


def check_toolchain_cc() -> Check:
    """`cc` -- `sut.c` ni kompilyatsiya qilish uchun (Makefile: `CC ?= cc`)."""
    key, title = "toolchain_cc", "C kompilyator (cc)"
    required = "`cc` PATH'da (revix/Makefile: CC ?= cc)"
    consequence = (
        "kompilyator bo'lmasa `sut.c` qurilmaydi -> SUT yo'q -> eksperiment "
        "o'lchaydigan xizmatning o'zi yo'q."
    )
    cc = shutil.which("cc")
    detail: dict[str, Any] = {
        "cc": cc,
        "gcc": shutil.which("gcc"),
        "clang": shutil.which("clang"),
    }
    if cc is None:
        return Check(key, title, FAIL, "`cc` topilmadi", required, consequence, detail)
    rc, out, _err = _run([cc, "--version"])
    ver = out.splitlines()[0].strip() if rc == 0 and out.strip() else "(versiya o'qilmadi)"
    detail["version_line"] = ver
    return Check(key, title, PASS, f"{cc} -- {ver}", required, consequence, detail)


def check_python_version() -> Check:
    key, title = "python_version", "Python versiyasi"
    required = ">= " + ".".join(str(x) for x in MIN_PYTHON)
    consequence = (
        "kod `from __future__ import annotations` + zamonaviy tip sintaksisidan "
        "foydalanadi va 3.11 dan pastda ishga tushmaydi."
    )
    v = sys.version_info
    observed = f"{v.major}.{v.minor}.{v.micro} ({sys.executable})"
    status = PASS if (v.major, v.minor) >= MIN_PYTHON else FAIL
    return Check(key, title, status, observed, required, consequence,
                 {"version": [v.major, v.minor, v.micro], "executable": sys.executable})


def _module_version(name: str) -> str | None:
    """Modul versiyasi; modul yo'q bo'lsa `None`, versiya noma'lum bo'lsa "mavjud".

    `find_spec` ishlatiladi, IMPORT emas: scipy/numpy/matplotlib importi
    sekundlarga cho'zilishi mumkin va pre-flight tekshiruvi tez bo'lishi kerak.
    """
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ValueError):
        return None
    if spec is None:
        return None
    for dist in _MODULE_DISTS.get(name, (name,)):
        try:
            return importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            continue
    return "mavjud"


def check_python_modules() -> Check:
    """MAJBURIY: `psutil`, `dbus`, `numpy`, `scipy`. IXTIYORIY: `matplotlib`.

    Majburiy modul yo'q -> FAIL (o'lchash yoki tahlil to'xtaydi). Faqat
    ixtiyoriy modul yo'q -> WARN: `revix figures` ishlamaydi, lekin pilot va
    tahlil to'xtamaydi, shuning uchun FAIL (gate) bo'lmaydi.

    `found`/`missing` kalitlari FAQAT majburiy modullar haqida va oldingi
    ma'nosini saqlaydi; ixtiyoriylar alohida `optional_found`/`optional_missing`
    da (kalit qo'shiladi, qayta ishlatilmaydi).
    """
    key, title = "python_modules", "Python modullari"
    required = (
        f"{', '.join(REQUIRED_MODULES)} (majburiy); "
        f"{', '.join(OPTIONAL_MODULES)} (ixtiyoriy)"
    )
    consequence = (
        "`numpy`/`scipy` yo'q -> statistik tahlil (PREREGISTRATION §10) "
        "ishlamaydi; `psutil` yo'q -> jarayon/resurs o'lchovi yo'q; `dbus` "
        "yo'q -> systemd unit holatini D-Bus orqali o'qib bo'lmaydi; "
        "`matplotlib` yo'q -> `revix figures` figura chiqara olmaydi (pilot va "
        "tahlil to'xtamaydi, shuning uchun bu faqat WARN)."
    )
    found: dict[str, str | None] = {n: _module_version(n) for n in REQUIRED_MODULES}
    missing = [n for n, v in found.items() if v is None]
    optional_found: dict[str, str | None] = {
        n: _module_version(n) for n in OPTIONAL_MODULES}
    optional_missing = [n for n, v in optional_found.items() if v is None]

    present = [f"{k}={v}" for k, v in {**found, **optional_found}.items()
               if v is not None]
    observed = ", ".join(present) or "hech biri"
    if missing:
        observed += "  -- YETMAYDI: " + ", ".join(missing)
    if optional_missing:
        observed += "  -- ixtiyoriy yetmaydi: " + ", ".join(optional_missing)
    if missing:
        status = FAIL
    elif optional_missing:
        status = WARN
    else:
        status = PASS
    return Check(key, title, status, observed, required, consequence,
                 {"found": found, "missing": missing,
                  "optional_found": optional_found,
                  "optional_missing": optional_missing})


# --- KVM --------------------------------------------------------------------


def check_kvm_access() -> Check:
    """`/dev/kvm` -- kelgusi QEMU lab'i uchun.

    GURUH A'ZOLIGI TEKSHIRILMAYDI (u yolg'on manfiy beradi): shu mashinada
    foydalanuvchi `kvm` guruhida EMAS, lekin ACL yozuvi (`user:rootzero:rw-`)
    orqali huquqi bor (01-muhit §8). Shuning uchun haqiqiy savol -- kernel
    ruxsat beradimi, va unga `os.access()` javob beradi: u haqiqiy uid bilan
    ACL'ni ham hisobga olgan to'liq tekshiruv qiladi.

    Hech qachon FAIL emas: P1 privilegiyasiz host'da ishlaydi, KVM faqat
    "root kerak = guest'ga tegishli" bandi uchun.
    """
    key, title = "kvm_access", "/dev/kvm (kelgusi QEMU lab'i)"
    required = "/dev/kvm o'qish+yozish mumkin (ACL yoki guruh orqali)"
    consequence = (
        "KVM bo'lmasa root talab qiladigan fault klasslari (io.max, dm-flakey, "
        "tc netem, cpuset, scaling_governor) izolyatsiyalangan guest'da "
        "ishlamaydi -> ular umuman o'lchanmaydi. P1 uchun SHART EMAS."
    )
    detail: dict[str, Any] = {"path": "/dev/kvm", "exists": os.path.exists("/dev/kvm")}
    if not detail["exists"]:
        return Check(key, title, WARN, "/dev/kvm yo'q (KVM modul yuklanmagan?)",
                     required, consequence, detail)
    accessible = os.access("/dev/kvm", os.R_OK | os.W_OK)
    detail["accessible"] = accessible

    # Guruh a'zoligi -- FAQAT ma'lumot uchun (qaror ACL asosida).
    try:
        import grp

        gids = set(os.getgroups())
        detail["in_kvm_group"] = grp.getgrnam("kvm").gr_gid in gids
    except (KeyError, OSError, ImportError):
        detail["in_kvm_group"] = None

    # ACL yozuvi -- kuzatilgan qiymatga qo'shiladi, mavjud bo'lsa.
    acl_entries: list[str] = []
    if shutil.which("getfacl"):
        rc, out, _err = _run(["getfacl", "-p", "/dev/kvm"])
        if rc == 0:
            user_name = None
            try:
                import pwd

                user_name = pwd.getpwuid(os.getuid()).pw_name
            except (KeyError, ImportError):
                pass
            for line in out.splitlines():
                line = line.strip()
                if user_name and line.startswith(f"user:{user_name}:"):
                    acl_entries.append(line)
    detail["acl_entries"] = acl_entries

    bits = []
    if acl_entries:
        bits.append("ACL: " + "; ".join(acl_entries))
    if detail["in_kvm_group"] is not None:
        bits.append("kvm guruhida: " + ("ha" if detail["in_kvm_group"] else "yo'q"))
    suffix = ("  [" + ", ".join(bits) + "]") if bits else ""

    if accessible:
        return Check(key, title, PASS, "o'qish+yozish mumkin" + suffix,
                     required, consequence, detail)
    return Check(key, title, WARN, "mavjud, lekin ruxsat yo'q" + suffix,
                 required, consequence, detail)


# --- repo -------------------------------------------------------------------


def check_git_present() -> Check:
    key, title = "git_present", "git va repo"
    required = "git binari bor va REPO_ROOT git repozitoriysi"
    consequence = (
        "git bo'lmasa run'ni kod versiyasiga bog'lab bo'lmaydi -> natija "
        "reproducible emas va `run_meta` da commit yozilmaydi."
    )
    info = git_info()
    if not info["git_present"]:
        return Check(key, title, FAIL, "git topilmadi", required, consequence, info)
    if not info["is_repo"]:
        return Check(key, title, FAIL,
                     f"{REPO_ROOT} git repo emas: {info['error']}",
                     required, consequence, info)
    return Check(key, title, PASS,
                 f"git bor, HEAD={info['commit_short']} ({REPO_ROOT})",
                 required, consequence, info)


def check_git_clean() -> Check:
    """Ishchi daraxt tozaligi.

    WARN, FAIL emas: pilot iflos daraxtda ishga tushishi mumkin (u
    exploratory). CONFIRMATORY run toza daraxt talab qiladi -- bu chegara
    confirmatory driver'ida majburlanadi, doctor esa faktni bildiradi.
    """
    key, title = "git_clean", "Ishchi daraxt tozaligi"
    required = "toza daraxt (confirmatory run uchun MAJBURIY)"
    consequence = (
        "iflos daraxtda olingan natija hech qanday commit'ga mos kelmaydi -> "
        "confirmatory run REPRODUCIBLE EMAS va pre-registration'ning kod "
        "hash'iga bog'lash sharti buziladi."
    )
    info = git_info()
    if not info["git_present"] or not info["is_repo"]:
        return Check(key, title, FAIL,
                     f"aniqlanmadi: {info['error']}", required, consequence, info)
    if info["dirty"]:
        n = len(info["dirty_paths"])
        return Check(key, title, WARN,
                     f"IFLOS ({n}{'+' if n >= 20 else ''} o'zgargan yo'l), "
                     f"HEAD={info['commit_short']}",
                     required, consequence, info)
    return Check(key, title, PASS, f"toza, HEAD={info['commit_short']}",
                 required, consequence, info)


# --- registr ----------------------------------------------------------------

# Tartib inson chiqishidagi tartib. `leftover_state` `cgroup_write` DAN OLDIN
# turadi, chunki cgroup_write o'z throwaway cgroup'ini yaratadi.
CHECKS: tuple[Callable[[], Check], ...] = (
    check_systemd_version,
    check_cgroup_v2,
    check_delegated_controllers,
    check_io_delegation,
    check_psi_host,
    check_psi_cgroup,
    check_oomd,
    check_leftover_state,
    check_cgroup_write,
    check_memory_headroom,
    check_swap_headroom,
    check_cpu_governor,
    check_toolchain_cc,
    check_python_version,
    check_python_modules,
    check_kvm_access,
    check_git_present,
    check_git_clean,
)

# BARQAROR kalitlar -- JSON iste'molchilari shu ro'yxatga tayanadi.
# Kalit qo'shiladi, hech qachon qayta ishlatilmaydi va olib tashlanmaydi.
EXPECTED_CHECK_KEYS: tuple[str, ...] = (
    "systemd_version",
    "cgroup_v2",
    "delegated_controllers",
    "io_delegation",
    "psi_host",
    "psi_cgroup",
    "oomd",
    "leftover_state",
    "cgroup_write",
    "memory_headroom",
    "swap_headroom",
    "cpu_governor",
    "toolchain_cc",
    "python_version",
    "python_modules",
    "kvm_access",
    "git_present",
    "git_clean",
)


def collect_checks(checks: tuple[Callable[[], Check], ...] | None = None) -> list[Check]:
    """Barcha tekshiruvlarni bajaradi.

    FAIL-CLOSED: tekshiruvning O'ZI istisno tashlasa, natija PASS emas, FAIL
    bo'ladi. Aks holda doctor'dagi bug jimgina "hammasi yaxshi" ga aylanardi --
    aynan pre-flight tekshiruvi oldini olishi kerak bo'lgan holat.
    """
    out: list[Check] = []
    for fn in (checks if checks is not None else CHECKS):
        try:
            out.append(fn())
        except Exception as exc:  # noqa: BLE001 -- fail-closed
            out.append(
                Check(
                    key=getattr(fn, "__name__", "unknown").removeprefix("check_"),
                    title=f"{getattr(fn, '__name__', 'unknown')} (istisno)",
                    status=FAIL,
                    observed=f"tekshiruv istisno tashladi: {exc!r}",
                    required="tekshiruv xatosiz bajarilishi",
                    consequence=(
                        "doctor bu shartni tekshira olmadi, demak muhit xavfsiz "
                        "deb HISOBLANMAYDI (fail-closed)."
                    ),
                    detail={"exception": repr(exc)},
                )
            )
    return out


def host_facts() -> dict[str, Any]:
    u = os.uname()
    return {
        "hostname": u.nodename,
        "kernel": u.release,
        "machine": u.machine,
        "uid": os.getuid(),
        "cpu_count": os.cpu_count(),
        "own_cgroup": _safe(cg.own_cgroup),
        "boot_id": _safe(read_boot_id),
    }


def _safe(fn: Callable[[], Any]) -> Any:
    try:
        return fn()
    except Exception:  # noqa: BLE001
        return None


def build_report(checks: list[Check]) -> dict[str, Any]:
    """Tekshiruvlar ro'yxatidan to'liq JSON hisobot.

    `summary.ok` = FAIL yo'q. Chiqish kodi AYNAN shu maydondan olinadi
    (`exit_code_for`), shunda inson va mashina bir xil xulosani ko'radi.
    """
    counts = {PASS: 0, WARN: 0, FAIL: 0}
    for c in checks:
        counts[c.status] += 1
    git = git_info()
    return {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "record_schema_version": SCHEMA_VERSION,
        "tool": "revix doctor",
        "revix_version": _read_version_file(),
        "git_commit": git.get("commit"),
        "git_dirty": git.get("dirty"),
        "mono_us": mono_us(),
        "real_us": real_us(),
        "host": host_facts(),
        "summary": {
            "total": len(checks),
            "pass": counts[PASS],
            "warn": counts[WARN],
            "fail": counts[FAIL],
            "ok": counts[FAIL] == 0,
        },
        "checks": [c.to_dict() for c in checks],
    }


def exit_code_for(report: dict[str, Any]) -> int:
    """0 -- FAIL yo'q; 1 -- kamida bitta FAIL."""
    return 0 if report.get("summary", {}).get("ok") else 1


# ===========================================================================
# inson uchun chiqish
# ===========================================================================


def term_width(default: int = 100) -> int:
    try:
        w = shutil.get_terminal_size(fallback=(default, 24)).columns
    except OSError:
        w = default
    return max(80, min(w, 120))


_KEY_W = 22
_MARK_W = 7  # "[PASS] "


def _wrap_field(label: str, text: str, width: int, indent: int) -> list[str]:
    """`label: text` ni `indent` ustuniga tekislab o'raydi."""
    prefix = " " * indent
    body = f"{label}{text}" if label else text
    lines = textwrap.wrap(body, width=max(40, width - indent),
                          subsequent_indent=" " * len(label),
                          break_long_words=False, break_on_hyphens=False)
    return [prefix + ln for ln in lines] or [prefix]


def format_check_human(c: Check, width: int) -> list[str]:
    """Bitta tekshiruv -- tekislangan ustunlar bilan.

    Birinchi satr: `[HOLAT] kalit  kuzatilgan`. Keyin `kerak:` satri, va
    faqat WARN/FAIL da `!!` bilan natija satri -- PASS holatda natija satri
    shovqin bo'lardi (lekin JSON'da doim bor).
    """
    indent = _MARK_W + _KEY_W + 1
    head = f"[{c.status}] {c.key.ljust(_KEY_W)} "
    obs = textwrap.wrap(c.observed, width=max(40, width - indent),
                        break_long_words=False, break_on_hyphens=False) or [""]
    lines = [head + obs[0]]
    for extra in obs[1:]:
        lines.append(" " * indent + extra)
    lines += _wrap_field("kerak: ", c.required, width, indent)
    if c.status != PASS:
        lines += _wrap_field("!! ", c.consequence, width, indent)
    return lines


def oomd_banner(check: Check, width: int) -> list[str]:
    """oomd kill authority bo'lsa BALAND ogohlik.

    Bu loyihaning 1-raqamli xavfi (00-pilot-topologiya §3.1) va u jadval
    ichidagi bir qatorga yashirilmaydi.
    """
    d = check.detail
    if not d.get("kill_authority"):
        return []
    rule = "!" * width
    dur = d.get("duration_effective_s")
    lim = d.get("pressure_limit_percent")
    body = [
        "OGOHLIK: systemd-oomd foydalanuvchi sessiyasi ustidan KILL huquqiga EGA.",
        f"  {d.get('unit')}: ManagedOOMMemoryPressure="
        f"{d.get('managed_oom_memory_pressure')}, "
        f"limit={'?' if lim is None else f'{lim:g}%'}, "
        f"sustained={'?' if dur is None else f'{dur:g}s'} "
        f"[{d.get('duration_source')}]",
        "  PSI IERARXIK: revixlab.slice ichidagi stall yuqoriga user@UID.service",
        "  ga tarqaladi. Guard'siz pressure eksperimenti BRAUZERINGIZNI,",
        "  EDITORINGIZNI yoki BUTUN DESKTOP SESSIYANGIZNI o'ldirishi mumkin.",
    ]
    body.append(f"  Xavf darajasi: {d.get('risk')}")
    for ln in textwrap.wrap(OOMD_MITIGATION, width=width - 2):
        body.append("  " + ln)
    return [rule] + body + [rule]


def render_doctor_human(report: dict[str, Any]) -> str:
    width = term_width()
    h = report["host"]
    out: list[str] = []
    out.append("REVIX doctor -- muhit pre-flight tekshiruvi")
    out.append(
        f"  mashina : {h['hostname']} | kernel {h['kernel']} | "
        f"{h['cpu_count']} CPU | uid {h['uid']}"
    )
    ver = report.get("revix_version") or "?"
    commit = report.get("git_commit") or "?"
    dirty = report.get("git_dirty")
    dirty_s = "iflos" if dirty else ("toza" if dirty is False else "?")
    out.append(f"  revix   : {ver} | commit {commit[:7]} ({dirty_s})")
    out.append("")

    checks = [Check(**c) for c in report["checks"]]
    for c in checks:
        if c.key == "oomd":
            banner = oomd_banner(c, width)
            if banner:
                out.append("")
                out += banner
                out.append("")
            break

    out.append("-" * width)
    for c in checks:
        out += format_check_human(c, width)
    out.append("-" * width)

    s = report["summary"]
    verdict = "XULOSA: muhit TAYYOR" if s["ok"] else "XULOSA: muhit TAYYOR EMAS"
    out.append(f"{verdict} -- {s['pass']} PASS, {s['warn']} WARN, {s['fail']} FAIL")
    if s["fail"]:
        out.append("FAIL bo'lgan tekshiruvlar: "
                   + ", ".join(c.key for c in checks if c.status == FAIL))
    if s["warn"]:
        out.append("WARN bo'lgan tekshiruvlar: "
                   + ", ".join(c.key for c in checks if c.status == WARN))
    out.append("Chiqish kodi: " + ("0 (FAIL yo'q)" if s["ok"] else "1 (FAIL bor)"))
    return "\n".join(out)


# ===========================================================================
# subkomanda: doctor
# ===========================================================================


def cmd_doctor(args: argparse.Namespace, want_json: bool) -> int:
    report = build_report(collect_checks())
    if want_json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=False))
    else:
        print(render_doctor_human(report))
    return exit_code_for(report)


# ===========================================================================
# subkomanda: status
# ===========================================================================


def list_revix_units() -> dict[str, Any]:
    """`revix*` user unit'lari (holat bilan)."""
    rc, out, err = _run(
        ["systemctl", "--user", "list-units", "revix*", "--all",
         "--no-legend", "--plain"]
    )
    res: dict[str, Any] = {"ok": rc == 0, "error": None, "units": []}
    if rc != 0:
        res["error"] = (err or out).strip()[:300] or f"rc={rc}"
        return res
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 4:
            res["units"].append({
                "name": parts[0], "load": parts[1],
                "active": parts[2], "sub": parts[3],
            })
        elif parts:
            res["units"].append({"name": parts[0], "load": None,
                                 "active": None, "sub": None})
    return res


def cgroup_procs(path: str) -> list[dict[str, Any]]:
    """cgroup subtree'idagi jarayonlar (pid + comm)."""
    procs: list[dict[str, Any]] = []
    for root, _dirs, files in os.walk(path):
        if "cgroup.procs" not in files:
            continue
        t = cg.read_text(os.path.join(root, "cgroup.procs"))
        if not t:
            continue
        for line in t.split():
            try:
                pid = int(line)
            except ValueError:
                continue
            comm = cg.read_text(f"/proc/{pid}/comm")
            procs.append({
                "pid": pid,
                "comm": comm.strip() if comm else None,
                "cgroup": os.path.relpath(root, path) if root != path else ".",
            })
    return procs


def slice_state(name: str) -> dict[str, Any]:
    """Lab/mon slice holati: mavjudmi, kim ichida, o'lchov snapshot'i."""
    res: dict[str, Any] = {"name": name, "exists": False, "path": None,
                           "procs": [], "snapshot": None}
    try:
        path = cg.user_child(name)
    except RuntimeError as exc:
        res["error"] = repr(exc)
        return res
    res["path"] = path
    if not os.path.isdir(path):
        return res
    res["exists"] = True
    res["procs"] = cgroup_procs(path)
    res["snapshot"] = cg.snapshot_cgroup(path)
    return res


def status_report(interval_s: float) -> dict[str, Any]:
    scopes = default_scopes()
    return {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "tool": "revix status",
        "mono_us": mono_us(),
        "real_us": real_us(),
        "host": host_facts(),
        "units": list_revix_units(),
        "slices": {n: slice_state(n) for n in (LAB_SLICE, MON_SLICE)},
        "psi": {
            "method": "total_delta",
            "why_not_avgN": (
                "avgN eksponensial silliqlangan va 2 s kadensda yangilanadi -- "
                "atributsiya uchun yaroqsiz (PREREGISTRATION.md §7). Tezlik "
                "`total=` delta'sidan olinadi."
            ),
            "interval_s": max(interval_s, MIN_RATE_WINDOW_S),
            "scopes": sample_psi_rates(scopes, interval_s),
        },
    }


def render_status_human(rep: dict[str, Any]) -> str:
    width = term_width()
    out: list[str] = ["REVIX status", "-" * width]

    out.append("UNIT'LAR (revix*)")
    u = rep["units"]
    if not u["ok"]:
        out.append(f"  ! ro'yxat o'qilmadi: {u['error']}")
    elif not u["units"]:
        out.append("  (revix* unit yo'q)")
    else:
        out.append(f"  {'unit':<40} {'load':<8} {'active':<10} sub")
        for x in u["units"]:
            out.append(f"  {x['name']:<40} {str(x['load']):<8} "
                       f"{str(x['active']):<10} {x['sub']}")

    out.append("")
    out.append("CGROUP'LAR")
    for name, st in rep["slices"].items():
        if st.get("error"):
            out.append(f"  {name:<18} ! {st['error']}")
            continue
        if not st["exists"]:
            out.append(f"  {name:<18} mavjud emas")
            continue
        snap = st["snapshot"] or {}
        cur = snap.get("memory_current")
        mx = snap.get("memory_max")
        out.append(
            f"  {name:<18} mavjud | {len(st['procs'])} jarayon | "
            f"memory.current={human_kb(cur // 1024 if cur else cur)} | "
            f"memory.max={'max' if mx is None else human_kb(mx // 1024)}"
        )
        for p in st["procs"][:12]:
            out.append(f"      pid {p['pid']:<8} {p['comm'] or '?':<20} {p['cgroup']}")
        if len(st["procs"]) > 12:
            out.append(f"      ... +{len(st['procs']) - 12} jarayon")

    psi = rep["psi"]
    out.append("")
    out.append(f"PSI -- {psi['interval_s']:g} s oyna, `total=` delta'sidan "
               f"(avgN EMAS: PREREGISTRATION.md §7)")
    hdr = (f"  {'scope':<22}"
           + "".join(f"{_RES_LABEL.get(r, r) + '.' + k:>11}"
                     for r in PSI_RESOURCES
                     for k in ("some", "full")))
    out.append(hdr)
    for scope, data in psi["scopes"].items():
        row = f"  {scope:<22}"
        for r in PSI_RESOURCES:
            e = data["resources"].get(r)
            for k in ("some", "full"):
                row += f"{_fmt_rate(None if e is None else e.get(f'{k}_rate')):>11}"
        out.append(row)
        if data.get("errors"):
            for r, msg in data["errors"].items():
                out.append(f"      ! {r}: {msg}")
    out.append("-" * width)
    return "\n".join(out)


def cmd_status(args: argparse.Namespace, want_json: bool) -> int:
    rep = status_report(args.interval)
    if want_json:
        print(json.dumps(rep, indent=2, ensure_ascii=False))
    else:
        print(render_status_human(rep))
    return 0


# ===========================================================================
# subkomanda: health
# ===========================================================================


def health_report(interval_s: float = MIN_RATE_WINDOW_S) -> dict[str, Any]:
    """Siqilgan sog'liq: PSI, xotira zaxirasi, oomd xavfi, qoldiq holat.

    `doctor` ning to'liq to'plamini takrorlamaydi -- u RUN paytida arzon
    takror o'qish uchun mo'ljallangan (doctor `cgroup_write` kabi yon ta'sirli
    tekshiruvlarni ham bajaradi; health hech nima yozmaydi).
    """
    scopes = default_scopes()
    psi = sample_psi_rates(scopes, interval_s, resources=("memory", "cpu", "io"))
    mi = cg.meminfo()
    avail = mi.get("MemAvailable")
    need = PLANNED_CEILING_KB + GUARD_MEM_FLOOR_KB
    oom = oomd_state()
    left = leftover_state()

    user_scope = f"user@{os.getuid()}.service"
    user_mem = (psi.get(user_scope, {}).get("resources", {}) or {}).get("memory")
    user_mem_full = user_mem.get("full_rate") if user_mem else None

    problems: list[str] = []
    warnings: list[str] = []

    if avail is None:
        problems.append("MemAvailable o'qilmadi")
    elif avail < need:
        problems.append(f"MemAvailable {human_kb(avail)} < kerak {human_kb(need)}")
    elif avail < need + 1024 * 1024:
        warnings.append(f"xotira zaxirasi yupqa: {human_kb(avail)}")

    blocking = left["blocking_units"] + left["blocking_cgroups"]
    advisory = left["advisory_units"] + left["advisory_cgroups"]
    if not left["unit_query_ok"]:
        problems.append("qoldiq unit ro'yxati o'qilmadi (fail-closed)")
    if blocking:
        problems.append("qoldiq holat: " + ", ".join(blocking))
    if advisory:
        warnings.append("boshqa revix* obyektlar: " + ", ".join(advisory))

    dur = oom["duration_effective_s"]
    if oom["kill_authority"]:
        if dur is None:
            problems.append("oomd kill authority, duration ANIQLANMADI")
        elif dur <= GUARD_SUSTAIN_MAX_S:
            problems.append(
                f"oomd duration {dur:g}s <= guard sustain {GUARD_SUSTAIN_MAX_S:g}s")
        else:
            lim = oom["pressure_limit_percent"]
            lim_s = "?" if lim is None else f"{lim:g}%"
            warnings.append(
                f"oomd kill authority (limit {lim_s}, {dur:g}s) -- guard MAJBURIY")

    if user_mem_full is not None and user_mem_full >= GUARD_SUSTAIN_RATE:
        warnings.append(
            f"{user_scope} memory.full tezligi {user_mem_full:.3f} >= "
            f"guard sustain chegarasi {GUARD_SUSTAIN_RATE:g} -- mashina "
            f"allaqachon pressure ostida")

    status = "fail" if problems else ("warn" if warnings else "ok")
    return {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "tool": "revix health",
        "mono_us": mono_us(),
        "real_us": real_us(),
        "status": status,
        "problems": problems,
        "warnings": warnings,
        "psi": {
            "method": "total_delta",
            "interval_s": max(interval_s, MIN_RATE_WINDOW_S),
            "user_memory_full_rate": user_mem_full,
            "scopes": psi,
        },
        "memory": {
            "mem_available_kb": avail,
            "mem_total_kb": mi.get("MemTotal"),
            "required_kb": need,
            "swap_total_kb": mi.get("SwapTotal"),
            "swap_free_kb": mi.get("SwapFree"),
        },
        "oomd_risk": {
            "kill_authority": oom["kill_authority"],
            "mode": oom["managed_oom_memory_pressure"],
            "limit_percent": oom["pressure_limit_percent"],
            "duration_s": dur,
            "guard_sustain_max_s": GUARD_SUSTAIN_MAX_S,
            "mitigated": bool(oom["kill_authority"]) and dur is not None
                         and dur > GUARD_SUSTAIN_MAX_S,
        },
        "leftover": left,
    }


def render_health_human(rep: dict[str, Any]) -> str:
    m = rep["memory"]
    o = rep["oomd_risk"]
    left = rep["leftover"]
    n_left = len(left["blocking_units"]) + len(left["blocking_cgroups"])
    rate = rep["psi"]["user_memory_full_rate"]
    if o["kill_authority"]:
        oomd_s = ("kill/"
                  + ("?" if o["duration_s"] is None else f"{o['duration_s']:g}s")
                  + ("/yumshatilgan" if o["mitigated"] else "/YUMSHATILMAGAN"))
    else:
        oomd_s = "kill authority yo'q"
    left_s = "yo'q" if n_left == 0 else str(n_left)
    line = (
        f"REVIX health: {rep['status'].upper()}"
        f" | psi(user,mem.full)={_fmt_rate(rate)}"
        f" | MemAvailable={human_kb(m['mem_available_kb'])}"
        f" (kerak {human_kb(m['required_kb'])})"
        f" | oomd={oomd_s}"
        f" | qoldiq={left_s}"
    )
    out = [line]
    for p in rep["problems"]:
        out.append(f"  FAIL  {p}")
    for w in rep["warnings"]:
        out.append(f"  WARN  {w}")
    return "\n".join(out)


def cmd_health(args: argparse.Namespace, want_json: bool) -> int:
    rep = health_report(args.interval)
    if want_json:
        print(json.dumps(rep, indent=2, ensure_ascii=False))
    else:
        print(render_health_human(rep))
    # `fail` da non-zero: health skriptdan gate sifatida ishlatilishi mumkin.
    return 1 if rep["status"] == "fail" else 0


# ===========================================================================
# subkomanda: events
# ===========================================================================

def read_events(path: str, types: set[str] | None = None,
                limit: int | None = None) -> dict[str, Any]:
    """JSONL hodisa oqimini o'qiydi.

    QISMLI OXIRGI QATOR TOLERANT: JSONL append-only va yozuvchi
    (`schema.JsonlWriter`) fsync'ni DAVRIY qiladi, demak jarayon o'lganda
    oxirgi qator yarim yozilgan bo'lishi MUTLAQO NORMAL. U tashlanadi va
    `truncated_tail: true` bilan qayd etiladi -- xato emas.

    O'RTADAGI buzuq qator -- BOSHQA gap: bu haqiqiy ma'lumot yo'qolishi va
    `bad_lines` ga tushadi hamda chiqish kodini non-zero qiladi. Ikkisini
    farqlamaslik jimgina ma'lumot yo'qolishiga yo'l qo'yardi.
    """
    res: dict[str, Any] = {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "tool": "revix events",
        "file": path,
        "count": 0,
        "total_lines": 0,
        "matched": 0,
        "types": {},
        "truncated_tail": False,
        "bad_lines": [],
        "records": [],
    }
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            raw_lines = fh.readlines()
    except OSError as exc:
        res["error"] = repr(exc)
        return res

    n = len(raw_lines)
    res["total_lines"] = n
    for i, raw in enumerate(raw_lines):
        is_last = i == n - 1
        stripped = raw.strip()
        if not stripped:
            continue
        # Oxirgi qatorda "\n" bo'lmasa -- u yarim yozilgan bo'lishi mumkin.
        try:
            rec = json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            if is_last:
                res["truncated_tail"] = True
            else:
                res["bad_lines"].append({"line": i + 1,
                                         "preview": stripped[:120]})
            continue
        if not isinstance(rec, dict):
            if is_last and not raw.endswith("\n"):
                res["truncated_tail"] = True
            else:
                res["bad_lines"].append({"line": i + 1,
                                         "preview": stripped[:120]})
            continue
        res["count"] += 1
        rt = rec.get("record_type")
        res["types"][rt] = res["types"].get(rt, 0) + 1
        if types is not None and rt not in types:
            continue
        res["matched"] += 1
        if limit is None or len(res["records"]) < limit:
            res["records"].append(rec)
    res["filter_types"] = sorted(types) if types else None
    return res


def render_events_human(res: dict[str, Any], full: bool = False) -> str:
    if res.get("error"):
        return f"! {res['file']}: {res['error']}"
    width = term_width()
    out = [f"REVIX events: {res['file']}",
           f"  {res['total_lines']} qator, {res['count']} record, "
           f"{res['matched']} filtrdan o'tdi"
           + (f", filtr: {','.join(res['filter_types'])}" if res.get("filter_types") else "")]
    if res["truncated_tail"]:
        out.append("  (oxirgi qator qismli -- tashlandi; JSONL append-only, "
                   "bu normal)")
    for b in res["bad_lines"]:
        out.append(f"  ! {b['line']}-qator buzuq: {b['preview']}")
    out.append("-" * width)
    out.append(f"  {'seq':>6} {'mono_us':>16} {'record_type':<20} {'emitter':<16} payload")
    for rec in res["records"]:
        # Envelope maydonlari ustunlarda ko'rsatiladi; qolgani payload.
        # Ro'yxat schema.py dan olinadi -- bu yerda takrorlanmaydi.
        payload = {k: v for k, v in rec.items() if k not in ENVELOPE_FIELDS}
        blob = " ".join(
            f"{k}={v if isinstance(v, (int, float, str)) and not isinstance(v, bool) else json.dumps(v, ensure_ascii=False, separators=(',', ':'))}"
            for k, v in payload.items()
        )
        if not full and len(blob) > max(20, width - 64):
            blob = blob[: max(20, width - 67)] + "..."
        out.append(
            f"  {str(rec.get('seq', '')):>6} {str(rec.get('mono_us', '')):>16} "
            f"{str(rec.get('record_type', '')):<20} "
            f"{str(rec.get('emitter', '')):<16} {blob}"
        )
    if res["types"]:
        out.append("-" * width)
        out.append("  turlar: " + ", ".join(
            f"{k}={v}" for k, v in sorted(res["types"].items(), key=lambda x: str(x[0]))))
    return "\n".join(out)


def cmd_events(args: argparse.Namespace, want_json: bool) -> int:
    types: set[str] | None = None
    if args.type:
        types = set()
        for t in args.type:
            types.update(x.strip() for x in t.split(",") if x.strip())
    res = read_events(args.file, types=types, limit=args.limit)
    if want_json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(render_events_human(res, full=args.full))
    if res.get("error"):
        return 2
    # Qismli OXIRGI qator xato EMAS; o'rtadagi buzuq qator -- XATO.
    return 1 if res["bad_lines"] else 0


# ===========================================================================
# subkomanda: version
# ===========================================================================


def version_report() -> dict[str, Any]:
    git = git_info()
    v = sys.version_info
    return {
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "tool": "revix version",
        "version": _read_version_file(),
        "version_file": os.path.join(REPO_ROOT, "VERSION"),
        "record_schema_version": SCHEMA_VERSION,
        "git_commit": git.get("commit"),
        "git_commit_short": git.get("commit_short"),
        "git_dirty": git.get("dirty"),
        "git_error": git.get("error"),
        "python": f"{v.major}.{v.minor}.{v.micro}",
        "repo_root": REPO_ROOT,
    }


def cmd_version(args: argparse.Namespace, want_json: bool) -> int:
    rep = version_report()
    if want_json:
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return 0
    dirty = rep["git_dirty"]
    dirty_s = "IFLOS" if dirty else ("toza" if dirty is False else "?")
    print(f"revix {rep['version'] or '?'}")
    print(f"  commit : {rep['git_commit_short'] or '?'} ({dirty_s})")
    print(f"  schema : {rep['record_schema_version']}")
    print(f"  python : {rep['python']}")
    print(f"  repo   : {rep['repo_root']}")
    if rep["git_error"]:
        print(f"  ! git  : {rep['git_error']}")
    return 0


# ===========================================================================
# subkomanda'lar: run, analyze, figures -- DELEGATSIYA
# ===========================================================================
#
# Bu uch handler hech narsani O'ZI bajarmaydi: `Namespace` -> argv ro'yxati ->
# `revix.<modul>.main(argv)`. Modulning ichki funksiyalari/dataclass'lari/
# konstantalari BU YERGA import qilinmaydi (qoida 7, fayl boshidagi docstring).
#
# Chiqish kodi: modul qaytargan kod O'ZGARTIRILMASDAN uzatiladi (modul o'z
# "yomon" holatini o'zi biladi). Yagona kod, uni BU YER hosil qiladi --
# EXIT_MODULE_UNAVAILABLE: modul ishga tushmadi ham.

# 127 -- `_run()` dagi "buyruq topilmadi" shell konvensiyasi bilan bir xil.
# 1 emas: 1 modul ISHLADI va yomon natija topdi degani; 2 emas: argparse
# xatosi uchun band. Chaqiruvchi "ishlamadi" va "ishladi, lekin yomon" ni
# ajrata olishi kerak.
EXIT_MODULE_UNAVAILABLE = 127


def _module_unavailable(cmd: str, target: str, reason: str, want_json: bool) -> int:
    """Modul ishga tushmadi: aniq xabar + `EXIT_MODULE_UNAVAILABLE`, traceback YO'Q."""
    hint = "qaysi modul yetishmayotganini `revix doctor` ko'rsatadi"
    if want_json:
        print(json.dumps({
            "report_schema_version": REPORT_SCHEMA_VERSION,
            "tool": f"revix {cmd}",
            "ok": False,
            "error": "module_unavailable",
            "module": target,
            "detail": reason,
        }, indent=2, ensure_ascii=False))
    else:
        print(f"revix {cmd}: {reason}", file=sys.stderr)
        print(f"  ({hint})", file=sys.stderr)
    return EXIT_MODULE_UNAVAILABLE


def _delegate(cmd: str, module: str, argv: list[str], want_json: bool) -> int:
    """`revix.<module>.main(argv)` ni LAZY import qilib chaqiradi.

    LAZY (modul darajasida emas): `figures.py` matplotlib'ni import qiladi va
    `revix doctor` matplotlib yo'q mashinada ham ishlashi SHART -- u aynan
    buzuq muhitni tashxis qilish uchun bor.

    Import muvaffaqiyatsizligi uch xil bo'ladi va uchalasi ham aniq xabar
    beradi: modulning O'ZI yo'q; modul bor, lekin uning bog'liqligi (masalan
    matplotlib) yo'q; modul `main` ni bermaydi (shartnoma buzilgan).
    """
    target = f"{__package__ or 'revix'}.{module}"
    try:
        mod = importlib.import_module(target)
    except ModuleNotFoundError as exc:
        if exc.name == target:
            reason = f"`{target}` moduli topilmadi"
        else:
            reason = (f"`{target}` import qilinmadi: `{exc.name}` moduli "
                      f"yetishmayapti")
        return _module_unavailable(cmd, target, reason, want_json)
    except ImportError as exc:
        return _module_unavailable(
            cmd, target, f"`{target}` import qilinmadi: {exc}", want_json)

    entry = getattr(mod, "main", None)
    if not callable(entry):
        return _module_unavailable(
            cmd, target,
            f"`{target}` da `main(argv)` yo'q (shartnoma buzilgan)", want_json)

    try:
        rc = entry(argv)
    except SystemExit as exc:
        # Modulning argparse'i `ap.error()` -> SystemExit(2). Handler butun
        # son qaytaradi; `main()` shartnomasi shu.
        if exc.code is None:
            return 0
        if isinstance(exc.code, int):
            return exc.code
        print(exc.code, file=sys.stderr)
        return 1
    return 0 if rc is None else int(rc)


def cmd_run(args: argparse.Namespace, want_json: bool) -> int:
    argv = ["--run-dir", args.run_dir, "--seed", str(args.seed)]
    if args.blocks is not None:
        argv += ["--blocks", str(args.blocks)]
    if args.only is not None:
        argv += ["--only", args.only]
    if args.dry_run:
        argv.append("--dry-run")
    if want_json:
        argv.append("--json")
    return _delegate("run", "driver", argv, want_json)


def cmd_analyze(args: argparse.Namespace, want_json: bool) -> int:
    argv = ["--trials", args.trials, "--run-meta", args.run_meta,
            "--out", args.out]
    if args.sweep is not None:
        argv += ["--sweep", args.sweep]
    if want_json:
        argv.append("--json")
    return _delegate("analyze", "analyze", argv, want_json)


def cmd_figures(args: argparse.Namespace, want_json: bool) -> int:
    argv = ["--analysis", args.analysis, "--out-dir", args.out_dir]
    for name in args.only or []:
        argv += ["--only", name]
    if want_json:
        argv.append("--json")
    return _delegate("figures", "figures", argv, want_json)


# ===========================================================================
# argparse
# ===========================================================================


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true",
                        help="hisobotni JSON sifatida chiqarish (barqaror kalitlar)")

    ap = argparse.ArgumentParser(
        prog="revix",
        description="REVIX -- Linux xizmat recovery'ini o'lchash harness'i",
    )
    ap.add_argument("--json", action="store_true", dest="json_global",
                    help="`revix --json <cmd>` shakli ham qo'llanadi")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="<cmd>")

    p = sub.add_parser("doctor", parents=[common],
                       help="muhit pre-flight tekshiruvi (FAIL bo'lsa rc=1)")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("status", parents=[common],
                       help="revix unit'lari, lab/mon cgroup'lari, PSI tezliklari")
    p.add_argument("--interval", type=float, default=MIN_RATE_WINDOW_S,
                   help=f"PSI tezlik oynasi, s (min {MIN_RATE_WINDOW_S:g} -- "
                        f"PSI kadensi 2 s)")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("health", parents=[common],
                       help="siqilgan sog'liq satri (status=fail bo'lsa rc=1)")
    p.add_argument("--interval", type=float, default=MIN_RATE_WINDOW_S,
                   help=f"PSI tezlik oynasi, s (min {MIN_RATE_WINDOW_S:g})")
    p.set_defaults(func=cmd_health)

    p = sub.add_parser("events", parents=[common],
                       help="JSONL hodisa oqimini chiqarish")
    p.add_argument("file", help="JSONL fayl")
    p.add_argument("--type", action="append", default=None, metavar="RECORD_TYPE",
                   help="faqat shu record_type (bir necha marta yoki vergul bilan)")
    p.add_argument("--limit", type=int, default=None,
                   help="ko'rsatiladigan record soni")
    p.add_argument("--full", action="store_true",
                   help="payload'ni qisqartirmaslik")
    p.set_defaults(func=cmd_events)

    p = sub.add_parser("version", parents=[common],
                       help="VERSION fayli, git commit, daraxt tozaligi")
    p.set_defaults(func=cmd_version)

    # run / analyze / figures: flag'lar argv'ga aylantirilib `revix.<modul>.main`
    # ga uzatiladi (cmd_run va h.k.). Qiymatlar bu yerda talqin QILINMAYDI --
    # ularning ma'nosi va tekshiruvi modulniki.
    p = sub.add_parser(
        "run", parents=[common],
        help="driver: bitta run = bitta katalog (`--dry-run` jadvalni chiqaradi)",
        description="`revix.driver` ni ishga tushiradi. Bayroqlar o'zgartirilmay "
                    "uzatiladi. Mavjud run katalogiga yozilmaydi (datasets/ "
                    "append-only).")
    p.add_argument("--run-dir", required=True, metavar="PATH",
                   help="run katalogi (yangi bo'lishi shart: mavjud katalog xato)")
    p.add_argument("--seed", type=int, required=True, metavar="INT",
                   help="randomizatsiya urug'i (run_meta.json'dagi rng_seed)")
    p.add_argument("--blocks", type=int, default=None, metavar="INT",
                   help="bloklar soni (berilmasa -- driver'ning default'i)")
    p.add_argument("--only", default=None, metavar="SPEC",
                   help="jadvalning bir qismi (SPEC sintaksisi driver'niki, "
                        "o'zgartirilmay uzatiladi)")
    p.add_argument("--dry-run", action="store_true",
                   help="hech narsa ishga tushirmaydi, faqat jadvalni chiqaradi")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser(
        "analyze", parents=[common],
        help="offline analiz: trial_metrics + run_meta -> analysis.json",
        description="`revix.analyze` ni ishga tushiradi (qat'iy offline). "
                    "Bayroqlar o'zgartirilmay uzatiladi.")
    p.add_argument("--trials", required=True, metavar="PATH",
                   help="reduce.py chiqargan trial_metrics JSONL")
    p.add_argument("--run-meta", required=True, metavar="PATH",
                   help="run_meta.json")
    p.add_argument("--out", required=True, metavar="PATH",
                   help="analysis.json chiqish yo'li")
    p.add_argument("--sweep", default=None, metavar="PATH",
                   help="sezgirlik sweep kiritmasi (ixtiyoriy)")
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser(
        "figures", parents=[common],
        help="figuralar: analysis.json -> <out-dir>/<nom>.svg (+ .json)",
        description="`revix.figures` ni ishga tushiradi (matplotlib kerak; yo'q "
                    "bo'lsa aniq xabar bilan non-zero chiqadi). Faqat "
                    "analysis.json o'qiladi.")
    p.add_argument("--analysis", required=True, metavar="PATH",
                   help="analysis.json")
    p.add_argument("--out-dir", required=True, metavar="DIR",
                   help="figuralar katalogi")
    p.add_argument("--only", action="append", default=None, metavar="NAME",
                   help="faqat shu figura (bir necha marta berish mumkin)")
    p.set_defaults(func=cmd_figures)
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    want_json = bool(getattr(args, "json", False) or getattr(args, "json_global", False))
    return int(args.func(args, want_json))


if __name__ == "__main__":
    sys.exit(main())
