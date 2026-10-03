#!/usr/bin/env python3
"""open-params kalibratsiyasi -- o'lchov controller'i.

Hujjat: docs/architecture/13-ochiq-parametrlar-kalibratsiyasi.md (§0 -- qoida,
o'lchovdan OLDIN commit qilingan). Bu skript QOIDANI qo'llamaydi; u faqat
o'lchaydi va xom yozuvlarni chiqaradi. Qoida `open-params-analyze.py` da.

QAYERDA ISHLAYDI: `systemd-run --user --slice=revixmon.slice` ichida
(`open-params-run.sh` ishga tushiradi). Shell'dan to'g'ridan-to'g'ri
ishga tushirilmaydi -- pastdagi `_require_mon_slice()` buni tekshiradi.

IKKI QISM:
  A (watchdog) -- har epizodda YANGI SUT unit'i (driver'ning property
     to'plami, `WatchdogSec=5s`), 6 s pressure'dan oldin, generator 13 s,
     keyin §8.4 quiescence (>= 20 s). 20 Hz poller
     `WatchdogTimestampMonotonic` ni (systemd ping'ni QABUL QILGAN vaqt)
     yozadi. Fault injeksiya YO'Q.
  B (t_start) -- generator 13 s; ramp'dan keyin (3 s) generator tirik
     ekan ketma-ket SUT start -> READY -> o'qish -> stop, epizodda <= 4.

SUT va generator `units.SystemdUser.start_transient` (D-Bus
`StartTransientUnit`) orqali `revixlab.slice` da -- driver bilan bir xil yo'l.

Driver'dan bitta ATAYLAB og'ish: generator unit'iga `WorkingDirectory`
beriladi. `driver._pressure_properties()` uni bermaydi, va
`python3 -m revix.pressure` user manager'ning default ishchi katalogida
($HOME) `revix` paketini topmaydi. Bu og'ish natijaga ta'sir qilmaydi
(argv va cheklovlar aynan driver'niki) va 13-hujjatda qayd etiladi.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import socket
import sys
import threading
import time
from typing import Any

WORK = os.environ.get("OPEN_PARAMS_WORK") or os.path.expanduser("~/openparams-work")
sys.path.insert(0, WORK)

from revix import cgroup as cg  # noqa: E402
from revix import driver as D  # noqa: E402
from revix import schedule as sch  # noqa: E402
from revix import units as U  # noqa: E402
from revix.schema import mono_us, real_us  # noqa: E402

LAB = U.LAB_SLICE
SUT_UNIT = D.SUT_UNIT            # revix-sut.service
PRESS_UNIT = D.PRESS_UNIT        # revix-press.service
GUARD_UNIT = D.GUARD_UNIT        # revix-guard.service
BANDS = ("P0", "P1", "P2")

GEN_MAX_SECONDS = 13.0           # 13 §0.8: generatorning butun umri <= 13 s
GEN_RUNTIME_MAX = f"{int(GEN_MAX_SECONDS) + 2}s"   # driver formulasi int(max)+2
A_PRE_S = 6.0                    # A: pressure'dan oldingi kuzatuv
B_RAMP_WAIT_S = 3.0              # B: ramp (~2.6 s, 10 §4.1) tugashini kutish
B_STARTS_PER_EP = 4
QUIESCE_MIN_S = 20.0             # 13 §0.8 va schedule.WASHOUT_PLANNED_S
POLL_HZ = 20.0
WASHOUT_POLL_S = D.WASHOUT_POLL_S            # 0.5 s
RATE_WINDOW_US = D.WASHOUT_RATE_WINDOW_US    # 2 s


class Abort(RuntimeError):
    """Fail-closed: run to'xtaydi, sabab yoziladi."""


# --- kichik yordamchilar ----------------------------------------------------

def jdump(fh, rec: dict[str, Any]) -> None:
    fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    fh.flush()


def read_boot_id() -> str:
    with open("/proc/sys/kernel/random/boot_id") as f:
        return f.read().strip()


def pid1_starttime() -> int:
    with open("/proc/1/stat") as f:
        data = f.read()
    # comm qavslar ichida bo'shliq bo'lishi mumkin -- oxirgi ')' dan keyin.
    rest = data[data.rindex(")") + 2:].split()
    return int(rest[19])         # 22-maydon (1-asosli), state = 3-maydon


def psi_totals(path: str) -> tuple[int | None, int | None]:
    """(some_total_us, full_total_us)."""
    txt = cg.read_text(path)
    if txt is None:
        return None, None
    try:
        p = cg.parse_psi(txt)
    except ValueError:
        return None, None
    some = p.get("some", {}).get("total")
    full = p.get("full", {}).get("total")
    return (int(some) if some is not None else None,
            int(full) if full is not None else None)


def vmstat_oom_kill() -> int | None:
    return cg.vmstat().get("oom_kill")


def _require_mon_slice() -> str:
    own = cg.own_cgroup()
    if "/revixmon.slice/" not in own + "/":
        raise Abort(f"controller revixmon.slice da emas: {own!r} "
                    "(systemd-run --user --slice=revixmon.slice orqali ishga tushiring)")
    return own


# --- property to'plamlari (driver.py dan, o'zgartirilmasdan) ---------------

def sut_properties(sock: str) -> dict[str, Any]:
    """`driver.Driver._sut_properties(arm='no_action', bystander=False)` bilan bir xil."""
    props: dict[str, Any] = {
        "Description": "REVIX sut (open-params calibration)",
        "Slice": LAB,
        "Type": "notify",
        "ExecStart": [os.path.join(WORK, "revix", "sut")],
        "WorkingDirectory": WORK,
        "Environment": [
            f"REVIX_SUT_SOCKET={sock}",
            f"REVIX_SUT_RATE_HZ={D.SUT_RATE_HZ}",
        ],
        "MemoryMax": "256M",
        "MemorySwapMax": 0,
        "TasksMax": 64,
        "WatchdogSec": D.DEFAULT_WATCHDOG_SEC,
        "TimeoutStartSec": D.DEFAULT_TIMEOUT_START_SEC,
        "Collect": True,
        "StandardOutput": "null",
        "StandardError": "null",
    }
    props.update(D.arm_properties("no_action"))
    D.check_restart_steps_pairing(props)
    return props


def pressure_argv(level: str, lab_cg: str, log: str, run_id: str,
                  episode_id: str) -> list[str]:
    """`driver.Driver._pressure_argv()` bilan bir xil dial."""
    return [
        sys.executable, "-m", "revix.pressure",
        "--mode", "pi",
        "--cgroup", lab_cg,
        "--target-rate", f"{D.pressure_target_rate(level)}",
        "--step-mb", f"{D.PRESSURE_STEP_MB}",
        "--base-mb", f"{D.pressure_base_mb(level)}",
        "--interval-ms", f"{D.PRESSURE_INTERVAL_MS}",
        "--max-seconds", f"{GEN_MAX_SECONDS:.3f}",
        "--log", log,
        "--run-id", run_id,
        "--session-id", episode_id,
    ]


def pressure_properties(argv: list[str]) -> dict[str, Any]:
    """`driver.Driver._pressure_properties()` + WorkingDirectory (modul izohi)."""
    return {
        "Description": "REVIX pressure generator (open-params calibration)",
        "Slice": LAB,
        "ExecStart": argv,
        "WorkingDirectory": WORK,
        "MemoryMax": D.PRESS_MEMORY_MAX,
        "MemorySwapMax": 0,
        "RuntimeMaxSec": GEN_RUNTIME_MAX,
        "OOMPolicy": "continue",
        "Collect": True,
        "StandardOutput": "null",
        "StandardError": "null",
    }


# --- poller: 20 Hz, o'z D-Bus ulanishi bilan --------------------------------

class Poller(threading.Thread):
    """`WatchdogTimestampMonotonic` + holat + PSI `total=` ni 20 Hz da yozadi.

    `WatchdogTimestamp` `PropertiesChanged` signali bilan e'lon qilinmaydi,
    shuning uchun polling. Har namuna o'zining boshlanish va tugash
    `mono_us` ini yozadi -- poller'ning o'z kechikishi KO'RINADI.
    """

    FIELDS = ("t0_us", "t1_us", "episode", "loaded", "wd_ts_us", "active",
              "sub", "result", "nrestarts", "lab_some_total", "lab_full_total",
              "host_full_total", "err")

    def __init__(self, out_csv: str, lab_cg: str) -> None:
        super().__init__(daemon=True)
        self.sd = U.SystemdUser(connect_signals=False)
        self.lab_psi = f"{lab_cg}/memory.pressure"
        self.fh = open(out_csv, "w", buffering=1)
        self.fh.write(",".join(self.FIELDS) + "\n")
        self.episode = ""
        # D-Bus faqat unit MAVJUD bo'lishi kutilganda: yuklanmagan unit
        # yo'liga `Get` systemd'da not-found stub yuklaydi -- poller o'lchov
        # obyektini o'zi yaratmasin.
        self.poll_unit = False
        self._stop_ev = threading.Event()
        self.n = 0
        self.max_interval_us = 0
        self.errors = 0

    def stop(self) -> None:
        self._stop_ev.set()

    def _get(self, iface: str, prop: str) -> Any:
        return self.sd.get_property(SUT_UNIT, iface, prop)

    def run(self) -> None:
        period = 1.0 / POLL_HZ
        nxt = time.monotonic()
        last_t0 = None
        while not self._stop_ev.is_set():
            t0 = mono_us()
            loaded: int | None = None
            wd = act = sub = res = nr = None
            err = ""
            if self.poll_unit:
                loaded = 1
                try:
                    wd = int(self._get(U.SERVICE_IFACE, "WatchdogTimestampMonotonic"))
                    act = str(self._get(U.UNIT_IFACE, "ActiveState"))
                    sub = str(self._get(U.UNIT_IFACE, "SubState"))
                    res = str(self._get(U.SERVICE_IFACE, "Result"))
                    nr = int(self._get(U.SERVICE_IFACE, "NRestarts"))
                except U.NoSuchUnitError:
                    loaded = 0
                except Exception as exc:  # noqa: BLE001 -- yoziladi, yashirilmaydi
                    err = type(exc).__name__
                    self.errors += 1
            ls, lf = psi_totals(self.lab_psi)
            _, hf = psi_totals("/proc/pressure/memory")
            t1 = mono_us()
            row = (t0, t1, self.episode, loaded, wd, act, sub, res, nr, ls, lf, hf, err)
            self.fh.write(",".join("" if v is None else str(v) for v in row) + "\n")
            self.n += 1
            if last_t0 is not None:
                self.max_interval_us = max(self.max_interval_us, t0 - last_t0)
            last_t0 = t0
            nxt += period
            d = nxt - time.monotonic()
            if d > 0:
                time.sleep(d)
            else:
                nxt = time.monotonic()
        self.fh.close()
        self.sd.close()


# --- controller --------------------------------------------------------------

class Controller:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.out = args.out
        self.run_id = args.run_id
        self.sd = U.SystemdUser()
        self.lab_cg = cg.user_child(LAB)
        self.sock = os.path.join(os.environ.get("XDG_RUNTIME_DIR")
                                 or f"/run/user/{os.getuid()}", "revix-sut.sock")
        self.events = open(os.path.join(self.out, "events.jsonl"), "a")
        self.units_fh = open(os.path.join(self.out, "unitstate.jsonl"), "a")
        self.tstart_fh = open(os.path.join(self.out, "tstart.jsonl"), "a")
        self.press_log = os.path.join(self.out, "pressure.jsonl")
        self.boot0 = read_boot_id()
        self.pid1_0 = pid1_starttime()
        self.oom0 = vmstat_oom_kill()
        self.dumped: set[str] = set()
        self.poller: Poller | None = None

    # -- yozuv --
    def emit(self, kind: str, **payload: Any) -> None:
        rec = {"record_type": kind, "run_id": self.run_id,
               "mono_us": mono_us(), "real_us": real_us()}
        rec.update(payload)
        jdump(self.events, rec)

    # -- fail-closed tekshiruvlar --
    def check_guest(self, where: str) -> dict[str, Any]:
        b, p = read_boot_id(), pid1_starttime()
        ok = (b == self.boot0 and p == self.pid1_0)
        info = {"where": where, "boot_id": b, "pid1_starttime": p, "ok": ok}
        if not ok:
            self.emit("guest_changed", **info)
            raise Abort(f"guest o'zgardi ({where}): boot_id {self.boot0}->{b}, "
                        f"pid1 {self.pid1_0}->{p} -- partiya tashlanadi")
        return info

    def check_guard(self, where: str) -> None:
        st = self.sd.active_state(GUARD_UNIT)
        trip = os.path.exists(os.path.join(self.out, "trip.json"))
        if st != "active" or trip:
            self.emit("guard_problem", where=where, state=st, trip_file=trip)
            raise Abort(f"guard holati {st!r}, trip_file={trip} ({where}) -- FAIL-CLOSED")

    def postflight_episode(self, where: str) -> dict[str, Any]:
        oom = vmstat_oom_kill()
        swap = cg.read_int(f"{self.lab_cg}/memory.swap.current")
        ok = (oom == self.oom0 and swap == 0)
        info = {"where": where, "vmstat_oom_kill": oom,
                "vmstat_oom_kill_at_start": self.oom0,
                "lab_swap_current": swap, "ok": ok}
        if not ok:
            self.emit("postflight_failed", **info)
            raise Abort(f"post-flight buzildi ({where}): {info}")
        return info

    # -- unit yordamchilari --
    def _rm_sock(self) -> None:
        try:
            os.unlink(self.sock)
        except OSError:
            pass

    def start_sut(self) -> dict[str, Any]:
        self._rm_sock()
        props = sut_properties(self.sock)
        out: dict[str, Any] = {"properties_sent": U.plain(props) if hasattr(U, "plain") else None}
        try:
            job = self.sd.start_transient(SUT_UNIT, props, timeout_s=30.0,
                                          require_done=False)
            out["job"] = job
        except Exception as exc:  # noqa: BLE001
            out["start_error"] = repr(exc)
            return out
        try:
            st = self.sd.read_state(SUT_UNIT)
            out["state"] = st
            ie = st.get("InactiveExitTimestampMonotonic") or 0
            ae = st.get("ActiveEnterTimestampMonotonic") or 0
            out["t_start_s"] = ((ae - ie) / 1e6) if (ae and ie and ae >= ie) else None
            try:
                out["watchdog_ts_initial_us"] = int(self.sd.get_property(
                    SUT_UNIT, U.SERVICE_IFACE, "WatchdogTimestampMonotonic"))
                out["watchdog_usec"] = int(self.sd.get_property(
                    SUT_UNIT, U.SERVICE_IFACE, "WatchdogUSec"))
                out["timeout_start_usec"] = int(self.sd.get_property(
                    SUT_UNIT, U.SERVICE_IFACE, "TimeoutStartUSec"))
            except Exception as exc:  # noqa: BLE001
                out["wd_read_error"] = repr(exc)
        except U.NoSuchUnitError:
            out["state"] = None
            out["t_start_s"] = None
        return out

    def sut_info(self) -> tuple[int | None, str]:
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            s.settimeout(2.0)
            s.connect(self.sock)
            s.sendall(b"INFO\n")
            buf = s.recv(4096).decode(errors="replace")
            s.close()
            for tok in buf.split():
                if tok.startswith("uptime_us="):
                    return int(tok.split("=", 1)[1]), buf.strip()[:200]
            return None, buf.strip()[:200]
        except (OSError, ValueError) as exc:
            return None, f"ERR {exc!r}"

    def stop_sut(self) -> dict[str, Any]:
        final = None
        try:
            final = self.sd.read_state(SUT_UNIT)
        except U.NoSuchUnitError:
            final = None
        job = self.sd.stop(SUT_UNIT, timeout_s=30.0)
        try:
            self.sd.reset_failed(SUT_UNIT)
        except Exception:  # noqa: BLE001
            pass
        self._rm_sock()
        return {"final_state_before_stop": final, "stop_job": job}

    def dump_once(self, band: str, part: str) -> None:
        key = f"{part}:{band}"
        if key in self.dumped:
            return
        try:
            d = U.dump_unit_properties(SUT_UNIT, systemd=self.sd)
            keep = {k: d["properties"].get(k) for k in (
                "Type", "NotifyAccess", "WatchdogUSec", "TimeoutStartUSec",
                "Restart", "StartLimitBurst", "MemoryMax", "MemorySwapMax",
                "TasksMax", "Slice", "ControlGroup", "WatchdogSignal",
                "CollectMode", "ExecStart", "Environment")}
            self.emit("sut_properties_live", band=band, part=part,
                      dump_valid=d["dump_valid"], load_state=d["load_state"],
                      properties=keep)
            self.dumped.add(key)
        except Exception as exc:  # noqa: BLE001
            self.emit("sut_properties_live", band=band, part=part,
                      error=repr(exc))

    def start_generator(self, band: str, episode_id: str) -> dict[str, Any]:
        argv = pressure_argv(band, self.lab_cg, self.press_log, self.run_id,
                             episode_id)
        props = pressure_properties(argv)
        t0 = mono_us()
        job = self.sd.start_transient(PRESS_UNIT, props, timeout_s=30.0)
        return {"argv": argv, "job": job, "mono_us_call": t0}

    def gen_active(self) -> bool:
        st = self.sd.active_state(PRESS_UNIT)
        return st in ("active", "activating", "reloading")

    def wait_generator_gone(self, cap_s: float) -> dict[str, Any]:
        t0 = time.monotonic()
        last = None
        while time.monotonic() - t0 < cap_s:
            last = self.sd.active_state(PRESS_UNIT)
            if last not in ("active", "activating", "reloading", "deactivating"):
                break
            time.sleep(0.1)
        end = mono_us()
        forced = False
        if last in ("active", "activating", "reloading", "deactivating"):
            # Chegara ishlamadi: majburan to'xtatamiz va YOZAMIZ.
            self.sd.stop(PRESS_UNIT, timeout_s=15.0)
            forced = True
        return {"gen_gone_mono_us": end, "last_state": last, "forced_stop": forced}

    def quiescence(self, mem_base: int) -> dict[str, Any]:
        """§8.4 WashoutMachine + >= 20 s pol. `kill_issued` = generator yo'q."""
        machine = sch.WashoutMachine(mem_base)
        t0 = mono_us()
        hist: dict[str, list[tuple[int, int]]] = {"lab": [], "host": []}
        paths = {"lab": f"{self.lab_cg}/memory.pressure",
                 "host": "/proc/pressure/memory"}
        first_quiet_lab_s = None
        n = 0
        while True:
            time.sleep(WASHOUT_POLL_S)
            now = mono_us()
            rates: dict[str, float | None] = {}
            for key, path in paths.items():
                _, full = psi_totals(path)
                rate = None
                if full is not None:
                    hist[key].append((now, full))
                    old = None
                    for h in reversed(hist[key]):
                        if now - h[0] >= RATE_WINDOW_US:
                            old = h
                            break
                    if old is not None:
                        rate = cg.stall_fraction(old[1], full, old[0], now)
                rates[key] = rate
            elapsed = (now - t0) / 1e6
            if (first_quiet_lab_s is None and rates["lab"] is not None
                    and rates["lab"] < sch.QUIESCENCE_RATE):
                first_quiet_lab_s = elapsed
            prog = machine.observe(sch.WashoutObservation(
                elapsed_s=elapsed, kill_issued=True,
                memory_current=cg.read_int(f"{self.lab_cg}/memory.current"),
                slice_stall_rate=rates["lab"], host_stall_rate=rates["host"]))
            n += 1
            if prog.timed_out:
                break
            if prog.done and elapsed >= QUIESCE_MIN_S:
                break
        p = machine.progress
        return {"state": p.state, "done": p.done, "timed_out": p.timed_out,
                "elapsed_s": p.elapsed_s, "quiet_for_s": p.quiet_for_s,
                "reason": p.reason, "observations": n, "memory_baseline": mem_base,
                "first_lab_rate_below_quiescence_s": first_quiet_lab_s}

    def lab_events(self) -> dict[str, int]:
        return cg.read_keyed(f"{self.lab_cg}/memory.events")

    # -- A: watchdog epizodi --
    def episode_a(self, band: str, idx: int, rnd: int) -> None:
        eid = f"A-{band}-{idx:02d}"
        guest = self.check_guest(eid)
        self.check_guard(eid)
        ev0 = self.lab_events()
        watcher = U.UnitWatcher(self.sd, SUT_UNIT)
        watcher.start(seed=False)
        assert self.poller is not None
        self.poller.episode = eid
        self.emit("episode_begin", part="A", band=band, episode=eid, round=rnd,
                  guest=guest, lab_events=ev0)
        sut = self.start_sut()
        self.poller.poll_unit = True
        self.emit("sut_started", part="A", band=band, episode=eid, **{
            k: v for k, v in sut.items() if k != "properties_sent"})
        if sut.get("state", {}) and (sut.get("state") or {}).get("ActiveState") == "active":
            self.dump_once(band, "A")
        time.sleep(A_PRE_S)
        mem_base = cg.read_int(f"{self.lab_cg}/memory.current") or 0
        _, full0 = psi_totals(f"{self.lab_cg}/memory.pressure")
        gen = self.start_generator(band, eid)
        self.emit("generator_started", part="A", band=band, episode=eid,
                  target_rate=D.pressure_target_rate(band),
                  base_mb=D.pressure_base_mb(band), step_mb=D.PRESSURE_STEP_MB,
                  max_seconds=GEN_MAX_SECONDS, runtime_max=GEN_RUNTIME_MAX,
                  job=gen["job"], mono_us_call=gen["mono_us_call"],
                  lab_full_total_before=full0)
        gone = self.wait_generator_gone(GEN_MAX_SECONDS + 4.0)
        _, full1 = psi_totals(f"{self.lab_cg}/memory.pressure")
        ev1 = self.lab_events()
        self.emit("generator_gone", part="A", band=band, episode=eid, **gone,
                  lab_full_total_after=full1, lab_events=ev1)
        q = self.quiescence(mem_base)
        self.emit("quiescence", part="A", band=band, episode=eid, **q)
        info_up, info_raw = self.sut_info()
        self.poller.poll_unit = False
        time.sleep(2.0 / POLL_HZ)        # poller'ning joriy o'qishi tugasin
        stop = self.stop_sut()
        self.poller.episode = ""
        recs = watcher.drain()
        watcher.stop()
        for r in recs:
            r["episode"] = eid
            jdump(self.units_fh, r)
        pf = self.postflight_episode(eid)
        self.emit("episode_end", part="A", band=band, episode=eid,
                  sut_info_uptime_us=info_up, sut_info=info_raw,
                  final_state=stop["final_state_before_stop"],
                  unit_state_records=len(recs), watcher_dropped=watcher.dropped,
                  lab_events_end=self.lab_events(), postflight=pf)

    # -- B: t_start epizodi --
    def episode_b(self, band: str, idx: int, rnd: int) -> int:
        eid = f"B-{band}-{idx:02d}"
        guest = self.check_guest(eid)
        self.check_guard(eid)
        ev0 = self.lab_events()
        assert self.poller is not None
        self.poller.episode = eid        # B da faqat PSI total= (unit poll'i yo'q)
        self.emit("episode_begin", part="B", band=band, episode=eid, round=rnd,
                  guest=guest, lab_events=ev0)
        mem_base = cg.read_int(f"{self.lab_cg}/memory.current") or 0
        _, full0 = psi_totals(f"{self.lab_cg}/memory.pressure")
        gen = self.start_generator(band, eid)
        self.emit("generator_started", part="B", band=band, episode=eid,
                  target_rate=D.pressure_target_rate(band),
                  base_mb=D.pressure_base_mb(band), step_mb=D.PRESSURE_STEP_MB,
                  max_seconds=GEN_MAX_SECONDS, runtime_max=GEN_RUNTIME_MAX,
                  job=gen["job"], mono_us_call=gen["mono_us_call"],
                  lab_full_total_before=full0)
        time.sleep(B_RAMP_WAIT_S)
        k = 0
        qualifying = 0
        while k < B_STARTS_PER_EP and self.gen_active():
            _, pre_full = psi_totals(f"{self.lab_cg}/memory.pressure")
            gen_pre = self.gen_active()
            sut = self.start_sut()
            up, raw = (None, "(start bo'lmadi)")
            st = sut.get("state") or {}
            if st.get("ActiveState") == "active":
                up, raw = self.sut_info()
                self.dump_once(band, "B")
            _, post_full = psi_totals(f"{self.lab_cg}/memory.pressure")
            gen_post = self.gen_active()
            stop = self.stop_sut()
            k += 1
            rec = {
                "run_id": self.run_id, "part": "B", "band": band,
                "episode": eid, "k": k, "mono_us": mono_us(),
                "t_start_s": sut.get("t_start_s"),
                "job_result": (sut.get("job") or {}).get("job_result"),
                "start_error": sut.get("start_error"),
                "active_state": st.get("ActiveState"),
                "sub_state": st.get("SubState"), "result": st.get("Result"),
                "invocation": (st.get("InvocationID") or "")[:32] if isinstance(
                    st.get("InvocationID"), str) else st.get("InvocationID"),
                "inactive_exit_us": st.get("InactiveExitTimestampMonotonic"),
                "active_enter_us": st.get("ActiveEnterTimestampMonotonic"),
                "exec_main_start_us": st.get("ExecMainStartTimestampMonotonic"),
                "watchdog_ts_initial_us": sut.get("watchdog_ts_initial_us"),
                "watchdog_usec": sut.get("watchdog_usec"),
                "timeout_start_usec": sut.get("timeout_start_usec"),
                "sut_uptime_us": up, "sut_info": raw,
                "pre_full_total": pre_full, "post_full_total": post_full,
                "total_delta": (post_full - pre_full)
                if (pre_full is not None and post_full is not None) else None,
                "generator_active_pre": gen_pre, "generator_active_post": gen_post,
                "final_result": (stop.get("final_state_before_stop") or {}).get("Result"),
            }
            # 13 §0.5(3): P1/P2 da faqat PRESSURED start (lab full total=
            # oshdi) sanaladi; P0 da generator tirik paytida boshlangan start.
            if band == "P0":
                rec["qualifying"] = bool(gen_pre)
            else:
                rec["qualifying"] = (rec["total_delta"] or 0) > 0
            qualifying += int(rec["qualifying"])
            jdump(self.tstart_fh, rec)
        gone = self.wait_generator_gone(GEN_MAX_SECONDS + 4.0)
        _, full1 = psi_totals(f"{self.lab_cg}/memory.pressure")
        ev1 = self.lab_events()
        self.emit("generator_gone", part="B", band=band, episode=eid, **gone,
                  lab_full_total_after=full1, lab_events=ev1, starts=k)
        q = self.quiescence(mem_base)
        self.emit("quiescence", part="B", band=band, episode=eid, **q)
        self.poller.episode = ""
        pf = self.postflight_episode(eid)
        self.emit("episode_end", part="B", band=band, episode=eid, starts=k,
                  qualifying=qualifying, postflight=pf)
        return qualifying

    # -- run --
    def run(self) -> int:
        a = self.args
        own = _require_mon_slice()
        self.emit("controller_start", own_cgroup=own, boot_id=self.boot0,
                  pid1_starttime=self.pid1_0, vmstat_oom_kill=self.oom0,
                  args=vars(a), work=WORK, python=sys.executable,
                  gen_max_seconds=GEN_MAX_SECONDS, gen_runtime_max=GEN_RUNTIME_MAX,
                  sut_properties=U.plain(sut_properties(self.sock)) if hasattr(U, "plain") else None,
                  dial={b: {"target_rate": D.pressure_target_rate(b),
                            "base_mb": D.pressure_base_mb(b),
                            "step_mb": D.PRESSURE_STEP_MB,
                            "interval_ms": D.PRESSURE_INTERVAL_MS} for b in BANDS},
                  lab_memory_high=cg.read_text(f"{self.lab_cg}/memory.high"),
                  lab_memory_max=cg.read_text(f"{self.lab_cg}/memory.max"),
                  lab_swap_max=cg.read_text(f"{self.lab_cg}/memory.swap.max"))
        self.check_guard("start")
        self.poller = Poller(os.path.join(self.out, "wdpoll.csv"), self.lab_cg)
        self.poller.start()
        status = "ok"
        try:
            if "A" in a.parts:
                for rnd in range(a.a_episodes):
                    order = list(BANDS)
                    random.Random(a.seed * 1000 + rnd).shuffle(order)
                    for band in order:
                        self.episode_a(band, rnd + 1, rnd)
            if "B" in a.parts:
                counts = {b: 0 for b in BANDS}
                eps = {b: 0 for b in BANDS}
                rnd = 0
                while any(counts[b] < a.b_min_starts and eps[b] < a.b_max_episodes
                          for b in BANDS):
                    order = list(BANDS)
                    random.Random(a.seed * 1000 + 500 + rnd).shuffle(order)
                    for band in order:
                        if counts[band] >= a.b_min_starts or eps[band] >= a.b_max_episodes:
                            continue
                        eps[band] += 1
                        counts[band] += self.episode_b(band, eps[band], rnd)
                    rnd += 1
                self.emit("b_counts", starts=counts, episodes=eps)
        except Abort as exc:
            status = f"abort: {exc}"
            self.emit("abort", reason=str(exc))
        except Exception as exc:  # noqa: BLE001
            status = f"error: {exc!r}"
            self.emit("error", reason=repr(exc))
        finally:
            try:
                self.sd.stop(PRESS_UNIT, timeout_s=15.0)
            except Exception:  # noqa: BLE001
                pass
            try:
                self.sd.stop(SUT_UNIT, timeout_s=15.0)
            except Exception:  # noqa: BLE001
                pass
            self.poller.stop()
            self.poller.join(timeout=5.0)
            self.emit("controller_end", status=status, poll_samples=self.poller.n,
                      poll_max_interval_us=self.poller.max_interval_us,
                      poll_errors=self.poller.errors)
        return 0 if status == "ok" else 3


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--parts", default="A,B")
    ap.add_argument("--a-episodes", type=int, default=24)
    ap.add_argument("--b-min-starts", type=int, default=48)
    ap.add_argument("--b-max-episodes", type=int, default=16)
    ap.add_argument("--seed", type=int, default=20261003)
    a = ap.parse_args(argv)
    a.parts = [p.strip() for p in a.parts.split(",") if p.strip()]
    os.makedirs(a.out, exist_ok=True)
    return Controller(a).run()


if __name__ == "__main__":
    sys.exit(main())
