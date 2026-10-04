"""driver.py testlari -- o'nta majburiyatning REGRESSIYA QULFLARI.

USLUB QARORI: bu yerdagi testlarning deyarli hammasi HAQIQIY systemd TALAB
QILMAYDI, va bu ataylab. `tests/unit/test_units.py` systemd'ning O'ZINI
sinaydi (mock yo'q, chunki mock faqat bizning taxminimizni tekshirardi).
Driver esa systemd'ni sinamaydi -- u SIYOSATNI, ya'ni faza deadline'larini,
record ketma-ketligini, disposition mantiqini va "aynan bitta trial_end" ni
sinaydi. Shu siyosatni haqiqiy systemd bilan sinash 120 trial x 52 s = 1.7
soat talab qilardi va `00-pilot-topologiya.md` §6 bo'yicha pressure hali
TAQIQLANGAN. Shuning uchun `FakePlatform` -- `test_guard.py` ning `FakePsi`
si bilan AYNI usul: yon ta'sirlar almashtiriladi, QAROR sinaladi.

XAVFSIZLIK QOIDALARI (buzilmaydi):
  * Bu modul HECH QANDAY systemd unit'i yaratmaydi. Yagona tirik-bus testi
    (`test_zzz_...`) faqat O'QIYDI.
  * Agar kelajakda selftest unit'i kerak bo'lsa, prefiks `revixdrvtest-`
    va slice `revixdrvtest.slice` -- UMUMIY `revixselftest.slice` EMAS
    (bu sessiyada ikki agent aynan o'sha slice'da to'qnashdi), va HECH
    QACHON `revix-*`, `revixlab.slice` yoki `revixmon.slice` emas.
"""

import json
import os

import pytest

from revix import driver as D
from revix import schedule as sch
from revix import units as U

SELFTEST_GLOB = "revixdrvtest-*"
SELFTEST_SLICE = "revixdrvtest.slice"

UINT64_MAX = U.UINT64_MAX


# ===========================================================================
# Fake platforma -- barcha yon ta'sirlar, virtual soat
# ===========================================================================


class FakeWatcher:
    """`units.UnitWatcher` ning o'rni: navbatdan record beradi."""

    def __init__(self, unit, platform):
        self.unit = unit
        self.pf = platform
        self.started = False
        self.stopped = False

    def start(self, seed=True):
        self.started = True
        self.pf.calls.append(("watch", self.unit))
        # OBUNA = FAQAT KEYINGI record'lar. Haqiqiy `UnitWatcher` obunadan
        # OLDINGI o'tishlarni ko'rmaydi, demak fake ham ko'rmasligi kerak --
        # aks holda oldingi fazaning (masalan qo'shimcha vaqt o'lchovining)
        # record'lari trial'ga tushib, SOXTA invocation o'zgarishi yasardi.
        self.pf.state_queue[self.unit] = []
        return self

    def drain(self):
        out = self.pf.state_queue.get(self.unit, [])
        self.pf.state_queue[self.unit] = []
        return out

    def stop(self):
        self.stopped = True


class FakePlatform:
    """Virtual soat + yolg'on systemd/cgroup/socket.

    `calls` -- TARTIBLANGAN operatsiya jurnali. Majburiyat 1 va 3 aynan
    TARTIB haqida, demak tartibni tekshirish uchun jurnal kerak.
    """

    def __init__(
        self,
        tmp_path,
        *,
        guard_ok=True,
        guard_active="active",
        unit_start_us=400_000,
        unit_stop_us=200_000,
        dump_us=100_000,
        guest_generation=None,
        guest_generation_after=None,
        preflight_raises=False,
        real_jump_at_us=None,
        real_jump_us=0,
    ):
        self.tmp = tmp_path
        self.t = 1_000_000
        # Host uyqusi modeli (07 §7.7): mono `real_jump_at_us` dan o'tgach
        # CLOCK_REALTIME `real_jump_us` ga oldinga sakraydi, mono esa YO'Q.
        self.real_jump_at_us = real_jump_at_us
        self.real_jump_us = real_jump_us
        # Guard trip modeli (14 §11.4): `guard_trip_at_us` dan o'tganda (yoki
        # `guard_trip_on_probe` da driver'ning injeksiya oldidan PROBE
        # buyrug'ida) guard_event yoziladi va lab o'ldiriladi -- SUT o'lik,
        # socket ConnectionRefused beradi. `sut_dead_no_guard`: SUT guard'siz
        # o'lik (haqiqiy harness xatosi modeli).
        self.guard_trip_at_us = None
        self.guard_trip_on_probe = False
        self.guard_tripped = False
        self.sut_dead = False
        self.sut_dead_no_guard = False
        self.washouts = 0
        self.calls = []
        self.state_queue = {}
        self.guard_ok = guard_ok
        self.guard_active = guard_active
        self.unit_start_us = unit_start_us
        self.unit_stop_us = unit_stop_us
        self.dump_us = dump_us
        self.preflight_raises = preflight_raises
        self.started = {}
        self.start_mono = {}
        self.active = {}
        self.guard_log_path = None
        self.psi_total_value = 1_000
        self.mem_current = 100 * 1024 * 1024
        self.slice_props = {}
        self.drop_ins_cleared = 0
        self.teardowns = 0
        self.guard_sigkilled = False
        self.killed = []
        self.kill_mono_us = []
        self.sut_arm = None
        self._inv = 0
        self._restarts = {}
        self._guard_seq = {}
        self._prober_pid = 900
        self.run_id = "r"
        self.session_id = "s"
        self._probe_seq = {}
        self.probe_rows = []
        self.events_path = None
        self.probe_csv_path = None
        self._prober = None
        self._fault_mono_us = None
        self._gen = guest_generation or {
            "pid1_starttime_ticks": 111, "uptime_s": 500.0,
            "pid1_starttime_s": 1.11, "generation": "pid1:111",
            "comparable": True, "clk_tck": 100,
            "identity_key": "pid1_starttime_ticks",
        }
        self._gen_after = guest_generation_after
        self._gen_reads = 0

    # --- soat ---
    def mono_us(self):
        return self.t

    def real_us(self):
        return self.real_at(self.t)

    def real_at(self, mono):
        jump = (self.real_jump_us if self.real_jump_at_us is not None
                and mono >= self.real_jump_at_us else 0)
        return 1_700_000_000_000_000 + mono + jump

    def boot_id(self):
        return "boot-fake"

    def sleep(self, seconds):
        if seconds > 0:
            self.t += int(seconds * 1e6)
        if (self.guard_trip_at_us is not None and not self.guard_tripped
                and self.t >= self.guard_trip_at_us):
            self.trip_guard(self.guard_trip_at_us)

    def trip_guard(self, mono):
        self.guard_tripped = True
        _append_jsonl(self.guard_log_path, dict(_guard_rec(
            "guard_event", mono, self._gseq("guard_event"), self.run_id,
            self.session_id, reason="user_full_rate2s_runaway",
            detail={"rate": 0.9817, "limit": 0.98, "window_us": 2_099_975},
            action="kill_subtree", lab_cgroup=self.cgroup_path(D.LAB_SLICE),
            kill_ok=True, trip_index=1, suppressed_records=0),
            real_us=self.real_at(mono)))
        self.sut_dead = True
        if self.active.get(D.SUT_UNIT) == "active":
            self._push_state(D.SUT_UNIT, "failed", f"inv{self._inv}",
                             self._restarts.get(D.SUT_UNIT, 0),
                             active_exit=mono)
            self.active[D.SUT_UNIT] = "failed"

    def guest_generation(self):
        self._gen_reads += 1
        if self._gen_after is not None and self._gen_reads > 1:
            return dict(self._gen_after)
        return dict(self._gen)

    # --- systemd ---
    def clear_runtime_drop_ins(self):
        self.drop_ins_cleared += 1
        self.calls.append(("clear_drop_ins", None))
        return []

    def require_clean(self):
        self.calls.append(("require_clean", None))
        if self.preflight_raises:
            raise U.PreflightError({"problems": ["qoldiq unit: revix-sut.service"],
                                    "clean": False})
        return {"clean": True, "problems": []}

    def set_slice_properties(self, name, props):
        self.calls.append(("set_slice", name))
        self.slice_props[name] = dict(props)

    def start_transient(self, name, props):
        self.calls.append(("start", name))
        t0 = self.t
        self.t += self.unit_start_us
        self.started[name] = dict(props)
        self.start_mono[name] = t0
        if name == D.SUT_UNIT:
            self.sut_arm = props.get("Restart")
            self.sut_dead = False
            self._restarts[name] = 0
            self._inv += 1
            self._push_state(name, "active", f"inv{self._inv}", 0)
        if name == D.BYSTANDER_UNIT:
            self._push_state(name, "active", "invby", 0)
        if name == D.PROBER_UNIT:
            argv = props["ExecStart"]
            self.probe_csv_path = _flag_value(argv, "--csv")
            self.events_path = _flag_value(argv, "--events")
            tid = _flag_value(argv, "--trial-id")
            # Har trial uchun ALOHIDA jarayon -> alohida pid -> alohida
            # `emitter`, demak `seq` har jarayonda 1 dan boshlanadi va
            # `validate.check_seq` ni (emitter, record_type) bo'yicha
            # qanoatlantiradi.
            self._prober_pid += 1
            self.run_id = _flag_value(argv, "--run-id")
            self.session_id = _flag_value(argv, "--session-id")
            self._prober = {"trial_id": tid, "start": self.t}
            self._fault_mono_us = None
            self._probe_seq = {"sut": 0, "bystander": 0}
            _append_jsonl(self.events_path, self._probe_envelope(
                "prober_start", self.t, tid,
                targets=["sut", "bystander"], hz=10.0))
        if name == D.GUARD_UNIT:
            self.guard_log_path = _flag_value(props["ExecStart"], "--log")
            self.run_id = _flag_value(props["ExecStart"], "--run-id")
            self.session_id = _flag_value(props["ExecStart"], "--session-id")
            if self.guard_ok:
                _append_jsonl(self.guard_log_path, _guard_rec(
                    "guard_start", self.t, self._gseq("guard_start"), self.run_id,
                    self.session_id, watch_cgroup=self.user_cgroup(),
                    lab_cgroup=self.cgroup_path(D.LAB_SLICE)))
            self.active[name] = self.guard_active
        else:
            self.active[name] = "active"
        return {"unit": name, "job_path": f"/job/{name}",
                "mono_us_before_call": t0, "mono_us_after_call": self.t,
                "job_result": "done", "mono_us_job_removed": self.t}

    def stop(self, name):
        self.calls.append(("stop", name))
        self.t += self.unit_stop_us
        self.active[name] = "inactive"
        if name == D.PROBER_UNIT:
            self._flush_probes()
        if (name == D.GUARD_UNIT and self.guard_ok and self.guard_log_path
                and not self.guard_sigkilled):
            # Guard `finally` da `guard_stop` yozadi -- u guard to'g'ri
            # to'xtaganining yagona dalili (kontrakt §1.3-1).
            _append_jsonl(self.guard_log_path, dict(_guard_rec(
                "guard_stop", self.t, self._gseq("guard_stop"), self.run_id,
                self.session_id, tripped=False, iterations=100),
                real_us=self.real_us()))
        return {"unit": name, "job_result": "done"}

    def reset_failed(self, name):
        return True

    def active_state(self, name):
        return self.active.get(name)

    def wait_for_active(self, name, timeout_s):
        return {"ok": self.active.get(name) == "active",
                "active_state": self.active.get(name),
                "elapsed_us": 0, "polls": 1}

    def watcher(self, unit):
        return FakeWatcher(unit, self)

    def dump_unit_properties(self, name):
        self.t += self.dump_us
        # `alive_before`/`alive_after`/`dump_valid` -- 01-muhit §4 tuzog'i:
        # o'chgan unit uchun `systemctl show` rc=0 va TO'LIQ DEFAULT beradi
        # (systemd 257 da qayta tasdiqlangan: 286 tirik qator vs 263 default).
        # Liveness kalitlarisiz dump "tirik paytida olingan" deb isbotlanmaydi.
        return {"unit": name, "dump_valid": True, "load_state": "loaded",
                "alive_before": True, "alive_after": True,
                "source": "systemctl --user show",
                "property_count": 287, "properties": {"LoadState": "loaded"}}

    def teardown(self, units=(), **kw):
        """`units.teardown` ning default'lari MODELLANADI (smoke-01 nuqsoni).

        Haqiqiy funksiya default'da `cgroup.kill` ni `revixlab.slice` VA
        `revixmon.slice` ga qo'llaydi, keyin `revix-*` ni to'xtatadi. Guard
        `revixmon.slice` da, demak tirik guard SIGKILL oladi va
        `guard_stop` YOZILMAYDI. Avvalgi fake buni e'tiborsiz qoldirgani
        uchun `test_guard_birinchi_start_oxirgi_stop` nuqsonni ko'rmadi.
        """
        self.teardowns += 1
        slices = tuple(kw.get("slices", (D.LAB_SLICE, D.MON_SLICE)))
        kill = kw.get("kill", True)
        self.calls.append(("teardown", (tuple(units), slices, kill)))
        if (kill and D.MON_SLICE in slices
                and self.active.get(D.GUARD_UNIT) == "active"):
            self.calls.append(("kill", D.MON_SLICE))
            self.active[D.GUARD_UNIT] = "failed"
            self.guard_sigkilled = True
        return {"stopped": list(units), "errors": []}

    # --- cgroup ---
    def cgroup_path(self, slice_name):
        return f"/sys/fs/cgroup/fake/{slice_name}"

    def user_cgroup(self):
        return "/sys/fs/cgroup/fake/user@1000.service"

    def snapshot_cgroup(self, path):
        return {"memory_current": self.mem_current, "memory_peak": self.mem_current,
                "memory_swap_current": 0, "memory_events": {"oom_kill": 0},
                "cpu_stat": {"usage_usec": 1234}}

    def memory_events(self, path):
        return {"oom_kill": 0, "high": 0, "max": 0}

    def memory_current(self, path):
        return self.mem_current

    def kill_subtree(self, path):
        self.killed.append(path)
        self.kill_mono_us.append(self.t)
        self.calls.append(("kill", path))
        return True

    def meminfo(self):
        return {"MemAvailable": 7_000_000, "MemFree": 3_000_000,
                "Cached": 1_000_000, "SwapFree": 0, "MemTotal": 10_000_000}

    def vmstat(self):
        return {"oom_kill": 0}

    def psi_total(self, psi_path, kind="full"):
        # Deyarli o'zgarmas `total` -> tezlik ~0 -> quiescence.
        self.psi_total_value += 1
        return (self.t, self.psi_total_value)

    # --- SUT socket ---
    def sut_command(self, socket_path, command, timeout_s=0.5):
        if command == "PROBE" and self.guard_trip_on_probe and not self.guard_tripped:
            self.trip_guard(self.t)
        if self.sut_dead or self.sut_dead_no_guard:
            self.calls.append(("refused", command))
            return {"command": command, "reply": None, "errno": 111,
                    "error": "ConnectionRefusedError(111, 'Connection refused')"}
        if command == "PROBE":
            # Protokol §3: `OK progress=.. pid=.. invocation=.. mono_us=..`.
            # §4.5: probe'ga javob `progress` ni OSHIRMAYDI.
            self.calls.append(("probe", command))
            return {"command": command, "errno": None,
                    "reply": (f"OK progress=4000 pid=4711 "
                              f"invocation=inv{self._inv} rss_kb=5120 "
                              f"mono_us={self.t + 7}")}
        self.calls.append(("fault", command))
        self._fault_mono_us = self.t
        inv = f"inv{self._inv}"
        # Fault: SUT chiqadi (clean crash, exit 1).
        self._push_state(D.SUT_UNIT, "failed", inv, self._restarts[D.SUT_UNIT],
                         active_exit=self.t + 1_000)
        self.active[D.SUT_UNIT] = "failed"
        if self.sut_arm == "on-failure":
            self._restarts[D.SUT_UNIT] += 1
            self._inv += 1
            # systemd yangi invocation record'ida ham `ActiveExit` ni
            # SAQLAYDI (oxirgi marta `active` dan chiqqan vaqt).
            self._push_state(D.SUT_UNIT, "active", f"inv{self._inv}",
                             self._restarts[D.SUT_UNIT],
                             mono=self.t + 120_000,
                             active_exit=self.t + 1_000)
            self.active[D.SUT_UNIT] = "active"
        return {"command": command, "reply": "OK armed=exit", "errno": None}

    def _gseq(self, record_type):
        """`seq` HAR OQIM uchun alohida -- `schema.Emitter` shunday qiladi."""
        n = self._guard_seq.get(record_type, 0) + 1
        self._guard_seq[record_type] = n
        return n

    def _probe_envelope(self, rt, mono, tid, **payload):
        rec = {"schema_version": 1, "record_type": rt, "stream": rt,
               "run_id": self.run_id, "session_id": self.session_id,
               "boot_id": self.boot_id(),
               "trial_id": tid, "block_index": None, "seq": 1,
               "mono_us": mono, "real_us": self.real_us(),
               "emitter": f"prober:{self._prober_pid}"}
        rec.update(payload)
        return rec

    def _flush_probes(self):
        """Prober to'xtaganda uning CSV qatorlarini yozadi.

        Qatorlar HAQIQIY shaklda: 10 Hz, ikki target, `progress_counter`
        ustuni (xom nom), `seq` TARGET bo'yicha 1 dan. Fault'dan keyin
        `conn_refused`, arm A da esa restart'dan keyin yangi invocation
        bilan tiklanish -- ya'ni fixture `find_failure_onsets`,
        `window_throughput` va censoring yo'llarini HAQIQATAN yuritadi.
        """
        if not self._prober or not self.probe_csv_path:
            return
        tid = self._prober["trial_id"]
        t = self._prober["start"]
        fault = self._fault_mono_us
        restart_at = (fault + 120_000) if (
            fault is not None and self.sut_arm == "on-failure") else None
        rows = []
        while t <= self.t:
            for target in ("sut", "bystander"):
                self._probe_seq[target] += 1
                inv = "invby" if target == "bystander" else "inv1"
                ok = True
                if target == "sut" and fault is not None and t >= fault:
                    if restart_at is None or t < restart_at:
                        ok = False
                    else:
                        inv = "inv2"
                base = t if (inv != "inv2") else restart_at
                prog = int((t - (self._prober["start"] if inv != "inv2"
                                 else base)) / 500) + 1
                rows.append({
                    "mono_us_send": t, "mono_us_recv": t + 500 if ok else "",
                    # Haqiqiy prober `real_us_send` ni `mono_us_send` bilan
                    # BIR LAHZADA o'qiydi (prober.py:444-445); flush vaqtidagi
                    # soat soxta "soat uzilishi" yasardi.
                    "real_us_send": self.real_at(t),
                    "target": target,
                    "outcome": "ok" if ok else "conn_refused",
                    "clause_failed": "" if ok else "a_conn",
                    "rt_us": 300 if ok else "",
                    "rtt_us": 500 if ok else "",
                    "progress_counter": prog if ok else "",
                    "invocation_id_seen": inv if ok else "",
                    "sut_pid_seen": 4711 if ok else "",
                    "seq": self._probe_seq[target], "trial_id": tid,
                })
            t += 100_000
        self.probe_rows.extend(rows)
        _append_csv(self.probe_csv_path, rows)
        _append_jsonl(self.events_path, self._probe_envelope(
            "prober_stop", self.t, tid, probes=len(rows),
            cost={"cpu_total_s": 0.21, "elapsed_s": 40.1,
                  "core_percent": 0.52, "budget_percent": 1.0,
                  "budget_exceeded": False, "probes": len(rows),
                  "cpu_us_per_probe": 520.0}))
        self._prober = None

    def _push_state(self, unit, state, inv, nrestarts, *, mono=None,
                    active_exit=None):
        t = mono or self.t
        raw = {p: None for p in U.STATE_PROPS}
        raw.update({
            "unit": unit, "recv_mono_us": t, "recv_real_us": self.real_us(),
            "signal_iface": "org.freedesktop.systemd1.Unit",
            "changed_props": ["ActiveState"], "changed_count": 1,
            "snapshot_complete": True, "missing_props": None,
            "ActiveState": state, "SubState": "running" if state == "active" else "failed",
            "InvocationID": inv, "NRestarts": nrestarts,
            "Result": "success" if state == "active" else "exit-code",
            "StateChangeTimestampMonotonic": t,
            "ActiveEnterTimestampMonotonic": t if state == "active" else 0,
            "ActiveExitTimestampMonotonic": active_exit or 0,
            "InactiveExitTimestampMonotonic": t - 1_000 if state == "active" else 0,
            "InactiveEnterTimestampMonotonic": 0,
            "ExecMainStartTimestampMonotonic": t - 500 if state == "active" else 0,
            "ExecMainExitTimestampMonotonic": active_exit or 0,
            "ExecMainPID": 4711, "ExecMainCode": 1 if state != "active" else 0,
            "ExecMainStatus": 1 if state != "active" else 0,
        })
        self.state_queue.setdefault(unit, []).append(raw)

    # --- muhit faktlari ---
    def environment_facts(self):
        return {
            "git": {"commit": "deadbeef" * 5, "dirty": False, "is_repo": True},
            "host": {"hostname": "fake", "kernel": "6.6.87", "cpu_count": 12,
                     "boot_id": "boot-fake"},
            "oomd": {"active": "inactive", "limit_effective_percent": None},
            "repo_version": "0.1.0-dev",
            "modules": {"numpy": "2.0", "dbus": "mavjud"},
            "systemd_version": {"version": 257},
            "delegated_controllers": {"controllers": ["cpu", "memory", "pids"]},
            # Bu mashinada O'LCHANGAN shakl: bo'sh ro'yxatlar.
            "cpu_governor": {"governors": [], "drivers": [], "cpu_count": 0,
                             "os_cpu_count": 12},
            "memory": {"mem_total_kb": 10_000_000, "mem_available_kb": 7_000_000},
        }

    def close(self):
        self.calls.append(("close", None))


def _flag_value(argv, flag):
    for i, a in enumerate(argv):
        if a == flag and i + 1 < len(argv):
            return argv[i + 1]
    return None


def _append_jsonl(path, record):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def _guard_rec(rt, mono, seq, run_id, session_id, **payload):
    """Guard record'i -- `trial_id` YO'Q (§8.2: mustaqil jarayon)."""
    rec = {"schema_version": 1, "record_type": rt, "stream": rt,
           "run_id": run_id, "session_id": session_id, "boot_id": "boot-fake",
           "trial_id": None, "block_index": None, "seq": seq,
           "mono_us": mono, "real_us": 1_700_000_000_000_000 + mono,
           "emitter": "guard:777"}
    rec.update(payload)
    return rec


PROBE_CSV_COLUMNS = (
    "mono_us_send", "mono_us_recv", "real_us_send", "target", "outcome",
    "clause_failed", "rt_us", "rtt_us", "progress_counter",
    "invocation_id_seen", "sut_pid_seen", "seq", "trial_id",
)


def _append_csv(path, rows):
    import os as _os
    new = not _os.path.exists(path) or _os.path.getsize(path) == 0
    with open(path, "a", encoding="utf-8", newline="") as fh:
        if new:
            fh.write(",".join(PROBE_CSV_COLUMNS) + "\n")
        for r in rows:
            fh.write(",".join(str(r.get(c, "")) for c in PROBE_CSV_COLUMNS)
                     + "\n")


def make_driver(tmp_path, *, only=("P0", "A"), blocks=1, platform=None,
                allow_pressure=False, **pf_kw):
    run_dir = D.prepare_run_dir(str(tmp_path / "run"))
    pf = platform or FakePlatform(tmp_path, **pf_kw)
    cfg = D.DriverConfig(run_dir=run_dir, seed=11, blocks=blocks,
                         only=tuple(only), allow_pressure=allow_pressure,
                         sut_binary="/nonexistent/sut")
    schedule = sch.p1_schedule(11, n_blocks=blocks)
    drv = D.Driver(cfg, pf, schedule, sch.TrialTimeline())
    return drv, pf, run_dir


def events(run_dir):
    path = os.path.join(run_dir, D.EVENTS_FILE)
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path, encoding="utf-8").read().splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def _require_strict_validator():
    """`validate.py` ning kengaytirilgan tekshiruvlarini talab qiladi.

    `validate_run_dir` va `reducer_view` bu branch'dan KEYIN qo'shilgan
    (agent/validate). Ular yo'q bo'lsa test O'TDI deb ko'rsatilmaydi --
    SABABI bilan skip qilinadi, chunki skip qilingan test "o'tgan" EMAS
    (CONTRIBUTING.md §1.2).
    """
    from revix import validate as V
    missing = [n for n in ("validate_run_dir", "reducer_view")
               if not hasattr(V, n)]
    if missing:
        pytest.skip(f"validate.py da yo'q: {missing} "
                    "(agent/validate bu branch'dan keyin qo'shdi)")
    return V


def of_type(recs, rt):
    return [r for r in recs if r.get("record_type") == rt]


# ===========================================================================
# T_trial -- hisoblanadi, hech qachon hardcode qilinmaydi
# ===========================================================================


def test_t_trial_muzlatilgan_timeline_xususiyatlaridan_hisoblanadi():
    tl = sch.TrialTimeline()
    # Formula: t_pressure_off + w_stab_s + P.
    assert D.t_trial_us(tl) == round((tl.t_pressure_off + tl.w_stab_s) * 1e6) \
        + D.PROBE_PERIOD_US
    # Muzlatilgan default'larda aynan 41.1 s: hold_cap_s = 13 s (preregistration/v1.11, §17.5 O3).
    # Bu YAGONA literal pin -- qiymatning o'zi uchun; qolgan testlar uni timeline'dan
    # hisoblaydi, shunda cap yana siljisa ular jimgina eskirmaydi.
    assert D.t_trial_us(tl) == 41_100_000
    # Invariant: eng erta oyna sig'adi va horizon washout ichiga kirmaydi.
    assert round(tl.t_verify_end_earliest * 1e6) <= D.t_trial_us(tl)
    assert D.t_trial_us(tl) <= round(tl.total_s * 1e6)


def test_t_trial_invariant_buzilsa_istisno_tashlanadi():
    # Qisqa hold -> `t_pressure_off + w_stab` `total_s` dan oshadi.
    tl = sch.TrialTimeline(hold_s=11.0, injection_offset_s=3.0, w_stab_s=8.0,
                           washout_s=15.0)
    with pytest.raises(D.DriverError, match="invariantni buzdi"):
        D.t_trial_us(tl, probe_period_us=20_000_000)


def test_probe_davri_muzlatilgan_qiymat_bilan_mos():
    # §2: P = 100 ms. Boshqa modullar bilan bir xil bo'lishi SHART, aks holda
    # censoring chegarasi (2xP) va horizon jimgina farq qilardi.
    from revix import prober
    from revix import reduce as R
    assert D.PROBE_PERIOD_US == R.P_US
    assert D.PROBE_PERIOD_US == int(1e6 / prober.PROBE_HZ)


# ===========================================================================
# Majburiyat 6 -- TrialTimeline invariantlari MAJBURLANADI
# ===========================================================================


def test_timeline_pressure_cap_invarianti_driver_tomonidan_yumshatilmaydi():
    # hold > cap: `TrialTimeline` O'ZI raise qiladi. Driver uni tutmaydi,
    # tuzatmaydi va ogohlantirishga aylantirmaydi. QULFLANGAN NARSA shu
    # QOIDA, cap'ning bugungi raqami EMAS.
    #
    # NEGA literal emas, `HOLD_CAP_S + delta`: bu yerda avval `hold_s=13.0`
    # "rad etiladigan qiymat" deb yozilgan edi. `PREREGISTRATION.md` §17.5
    # O3 qarori cap'ni 12 s dan 13 s ga ko'chirgach 13.0 QONUNIY bo'ldi --
    # ya'ni test eski cap'ga qotib qolib, qoidani UMUMAN tekshirmay
    # qolardi. Konstantadan hisoblangan qiymat cap qayerda bo'lsa ham
    # "cap'dan yuqori" bo'lib qoladi, demak ikkinchi marta eskirmaydi.
    #
    # `ramp_above_threshold_s=0.0` OSHKORA beriladi: aks holda ikkinchi
    # invariant (`hold_s + ramp <= guard_sustain_window_s`) BIRINCHI
    # qulashi mumkin va test o'zi nomlagan invariantni emas, boshqasini
    # tekshirardi. `match` ham shu uchun -- xabar BIRINCHI invariantning.
    with pytest.raises(sch.PressureCapExceeded, match="sustained pressure-on"):
        sch.TrialTimeline(hold_s=sch.HOLD_CAP_S + 0.1,
                          ramp_above_threshold_s=0.0)


def test_hold_cap_muzlatilgan_qiymati_va_chegaraning_OZI_qonuniy():
    """§17.5 ning O3 qarori: `hold_cap_s` 12 s dan 13 s ga ko'chdi.

    NEGA literal pin HAM kerak: yuqoridagi test cap'ning QAYERDA
    turganini tekshirmaydi -- u faqat "cap'dan yuqori rad etiladi" ni
    qulflaydi, va cap jimgina surilsa ham o'tib ketadi. Muzlatilgan
    QIYMATNING o'zi alohida qulflanadi, aks holda amendment'siz siljish
    hech qaysi testga urilmaydi. Bu fayl uslubi aynan shunday
    (`PROBE_PERIOD_US` va `t_trial_us` ning muzlatilgan qiymatlari
    literal bilan pin qilinadi).

    Ikkinchi tasdiq chegaraning SEMANTIKASI haqida: cap "oshmaydi",
    "yetmaydi" EMAS -- `hold_s == hold_cap_s` QONUNIY, demak §17.5 ning
    13 s li qarori amalda ishlatilishi mumkin.
    """
    assert sch.HOLD_CAP_S == 13.0
    tl = sch.TrialTimeline(hold_s=sch.HOLD_CAP_S)
    assert tl.hold_s == sch.HOLD_CAP_S
    assert tl.hold_s + tl.ramp_above_threshold_s <= sch.GUARD_SUSTAIN_WINDOW_S


def test_timeline_guard_sustain_invarianti_majburlanadi():
    with pytest.raises(sch.PressureCapExceeded):
        sch.TrialTimeline(hold_s=12.0, ramp_above_threshold_s=5.0)


def test_driver_timeline_istisnosini_yutmaydi(tmp_path):
    run_dir = D.prepare_run_dir(str(tmp_path / "run"))
    pf = FakePlatform(tmp_path)
    cfg = D.DriverConfig(run_dir=run_dir, seed=1, blocks=1, only=("P0", "A"))
    schedule = sch.p1_schedule(1, n_blocks=1)
    # W_stab hold ichiga sig'maydi -> ScheduleError, va u DRIVER'ga emas,
    # chaqiruvchiga chiqadi.
    #
    # Qiymat KONSTANTALARDAN hisoblanadi, literal emas: invariant
    # `injection_offset_s + w_stab_s <= hold_s`, demak trigger
    # `hold_cap - injection_offset` dan YUQORI bo'lishi kerak. Bu yerda
    # avval `w_stab_s=10.0` literal turgan edi va u `hold_cap_s` 12 s da
    # ishlardi; §17.5 O3 cap'ni 13 s ga ko'chirgach 3 + 10 = 13 <= 13
    # bo'lib, test SUKUT BILAN hech narsani tekshirmay qoldi (DID NOT
    # RAISE). Bu `hold_s=13.0` literali bilan AYNI nuqson klassi.
    w_stab_sigmaydi = sch.HOLD_CAP_S - sch.INJECTION_OFFSET_S + 0.1
    with pytest.raises(sch.ScheduleError):
        D.Driver(cfg, pf, schedule,
                 sch.TrialTimeline(w_stab_s=w_stab_sigmaydi))


# ===========================================================================
# Majburiyat 11 -- mavjud run katalogi XATO
# ===========================================================================


def test_mavjud_run_katalogiga_yozish_xato(tmp_path):
    path = str(tmp_path / "run")
    D.prepare_run_dir(path)
    with pytest.raises(D.RunDirExistsError):
        D.prepare_run_dir(path)


def test_mavjud_run_katalogi_main_dan_ham_rad_etiladi(tmp_path, capsys):
    path = str(tmp_path / "run")
    os.makedirs(path)
    rc = D.main(["--run-dir", path, "--seed", "3", "--blocks", "1",
                 "--only", "P0,A", "--json"])
    assert rc == 2
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert out["error_type"] == "RunDirExistsError"


# ===========================================================================
# Majburiyat 10 -- --dry-run HECH NARSA ishga tushirmaydi
# ===========================================================================


def test_dry_run_hech_narsa_ishga_tushirmaydi(tmp_path, capsys):
    path = str(tmp_path / "run")
    rc = D.main(["--run-dir", path, "--seed", "7", "--blocks", "2",
                 "--only", "P0,A", "--dry-run", "--json"])
    assert rc == 0
    report = json.loads(capsys.readouterr().out)
    assert report["dry_run"] is True
    assert report["n_trials_selected"] == 2
    assert report["per_trial_overhead_source"] == "not_measured_dry_run"
    # Katalog HAM yaratilmaydi: dry-run faylga tegmaydi.
    assert not os.path.exists(path)


def test_dry_run_jadvalni_va_digestni_chiqaradi(tmp_path):
    schedule = sch.p1_schedule(5, n_blocks=2)
    tl = sch.TrialTimeline()
    rep = D.dry_run_report(schedule, tl, D.select_trials(schedule, ()))
    assert rep["schedule_digest"] == schedule.digest()
    assert rep["n_trials_total"] == 12
    assert len(rep["trials"]) == 12
    assert rep["t_trial_formula"] == D.T_TRIAL_FORMULA


def test_dry_run_pressure_eshigidan_otmaydi(tmp_path, capsys):
    # --dry-run da pressure tekshiruvi SHART EMAS: hech narsa ishga
    # tushmaydi, demak jadvalni ko'zdan kechirish har doim mumkin.
    rc = D.main(["--run-dir", str(tmp_path / "r"), "--seed", "1",
                 "--blocks", "1", "--dry-run", "--json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["n_trials_selected"] == 6


# ===========================================================================
# Majburiyat 2 -- guard ishga tushmasa RUN BOSHLANMAYDI
# ===========================================================================


def test_guard_ishga_tushmasa_run_boshlanmaydi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path, guard_ok=False)
    with pytest.raises(D.GuardStartError):
        drv.run()
    recs = events(run_dir)
    # ENG MUHIM TEKSHIRUV: hech qanday trial BOSHLANMAGAN.
    assert of_type(recs, "trial_begin") == []
    assert of_type(recs, "trial_end") == []
    assert of_type(recs, "fault_inject") == []
    # Xato JIM qolmaydi.
    assert of_type(recs, "harness_error")


def test_guard_unit_failed_bolsa_run_boshlanmaydi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path, guard_active="failed")
    with pytest.raises(D.GuardStartError):
        drv.run()
    assert of_type(events(run_dir), "trial_begin") == []


def test_guard_watch_open_failed_hodisasi_fail_closed(tmp_path):
    log = tmp_path / "guard.jsonl"
    _append_jsonl(str(log), {"record_type": "guard_start", "mono_us": 1})
    _append_jsonl(str(log), {"record_type": "guard_event",
                             "reason": "watch_open_failed", "mono_us": 2})
    res = D.verify_guard_live(str(log), lambda: "active", timeout_s=0.0,
                              sleep=lambda s: None)
    assert res["ok"] is False
    assert res["reason"] == "guard_fatal_event"


def test_guard_start_recordi_bolmasa_active_yetarli_emas(tmp_path):
    # Unit `active`, lekin guard O'Z oqimiga hech narsa yozmagan: bu
    # `guard.run()` ning 2-kodli chiqishidagi poyga. Fail-closed.
    res = D.verify_guard_live(str(tmp_path / "yoq.jsonl"), lambda: "active",
                              timeout_s=0.0, sleep=lambda s: None)
    assert res["ok"] is False
    assert res["reason"] == "guard_start_record_missing"


def test_guard_tirik_bolsa_tasdiqlanadi(tmp_path):
    log = tmp_path / "guard.jsonl"
    _append_jsonl(str(log), {"record_type": "guard_start", "mono_us": 1})
    res = D.verify_guard_live(str(log), lambda: "active", timeout_s=1.0,
                              sleep=lambda s: None)
    assert res["ok"] is True


# ===========================================================================
# Majburiyat 1 -- guard BIRINCHI start, OXIRGI stop
# ===========================================================================


def test_guard_birinchi_start_oxirgi_stop(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    starts = [n for k, n in pf.calls if k == "start"]
    stops = [n for k, n in pf.calls if k == "stop"]
    assert starts[0] == D.GUARD_UNIT, starts
    assert stops[-1] == D.GUARD_UNIT, stops
    # psi_sampler guard'dan KEYIN (majburiyat 7 tartibi).
    assert starts.index(D.PSI_UNIT) > starts.index(D.GUARD_UNIT)


def test_guard_teardown_kill_ostida_qolmaydi_va_guard_stop_yozadi(tmp_path):
    """REGRESSIYA (smoke-01, 14 §3.1): guard SIGTERM bilan OXIRGI to'xtaydi.

    Haqiqiy run'da `_teardown_run` `units.teardown()` ni default'lari bilan
    guard'dan OLDIN chaqirib `revixmon.slice` ni `cgroup.kill` qilardi:
    journal `revix-guard.service: ... status=9/KILL`, `guard_stop` yo'q,
    `validate` -> `guard_stop_missing` ERROR -- har run'da.
    """
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    assert pf.guard_sigkilled is False
    i_guard = pf.calls.index(("stop", D.GUARD_UNIT))
    # Guard to'xtatilishidan OLDINGI har teardown mon slice'ga TEGMAYDI.
    for c in pf.calls[:i_guard]:
        if c[0] == "teardown" and c[1][2]:
            assert D.MON_SLICE not in c[1][1], c
    # ...va guard'dan KEYIN mon slice baribir yig'ishtiriladi.
    assert any(c[0] == "teardown" and D.MON_SLICE in c[1][1] and c[1][2]
               for c in pf.calls[i_guard:]), pf.calls[i_guard:]
    guard_recs = [json.loads(x) for x in
                  open(os.path.join(run_dir, D.GUARD_FILE), encoding="utf-8")]
    assert guard_recs[-1]["record_type"] == "guard_stop"


def test_guard_driverning_childi_emas_balki_systemd_uniti(tmp_path):
    """Qotib qolgan driver guard'ni o'chira olmasligi SHART.

    Mexanizm: guard `start_transient` bilan ALOHIDA unit sifatida
    yaratiladi, `subprocess` bilan emas. Shuning uchun uni systemd ushlab
    turadi va driver'ning o'limi guard'ni o'ldirmaydi.
    """
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    assert D.GUARD_UNIT in pf.started
    props = pf.started[D.GUARD_UNIT]
    assert props["Slice"] == D.MON_SLICE        # majburiyat 7
    assert props["ExecStart"][1:3] == ["-m", "revix.guard"]
    # RuntimeMaxSec bor, lekin kampaniyadan UZUN -- himoyani cheklamaydi.
    assert props["RuntimeMaxSec"].endswith("s")
    assert int(props["RuntimeMaxSec"][:-1]) > drv.timeline.total_s


# ===========================================================================
# Majburiyat 3 va 4 -- drop-in tozalash va pre-flight, SHU TARTIBDA
# ===========================================================================


def test_run_boshida_runtime_drop_inlar_tozalanadi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    assert pf.drop_ins_cleared >= 1
    kinds = [k for k, _ in pf.calls]
    assert kinds[0] == "clear_drop_ins"


def test_drop_in_tozalash_preflightdan_va_slice_diallaridan_oldin(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    order = [k for k, _ in pf.calls]
    i_clear = order.index("clear_drop_ins")
    i_pre = order.index("require_clean")
    i_slice = order.index("set_slice")
    assert i_clear < i_pre < i_slice, order[:6]


def test_preflight_yiqilsa_run_boshlanmaydi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path, preflight_raises=True)
    with pytest.raises(U.PreflightError):
        drv.run()
    assert of_type(events(run_dir), "trial_begin") == []


def test_slice_diallari_topologiya_bilan_mos(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    lab = pf.slice_props[D.LAB_SLICE]
    assert lab["MemoryMax"] == "2G"
    assert lab["CPUQuota"] == "400%"
    assert lab["TasksMax"] == 256
    assert lab["MemoryHigh"] == D.DEFAULT_MEMORY_HIGH
    # Slice nomlarida DASH YO'Q (amendment v1.1 -- validlik xatosi edi).
    assert "-" not in D.LAB_SLICE.split(".")[0]
    assert "-" not in D.MON_SLICE.split(".")[0]


# ===========================================================================
# Majburiyat 5 -- AYNAN BITTA trial_end + disposition
# ===========================================================================


def test_har_trial_uchun_aynan_bitta_trial_end(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path, blocks=2)
    drv.run()
    recs = events(run_dir)
    begins = of_type(recs, "trial_begin")
    ends = of_type(recs, "trial_end")
    assert len(begins) == 2
    assert len(ends) == 2
    by_trial = {}
    for r in ends:
        by_trial.setdefault(r["trial_id"], []).append(r)
    assert all(len(v) == 1 for v in by_trial.values()), by_trial
    assert {r["trial_id"] for r in begins} == set(by_trial)
    for r in ends:
        assert r["disposition"] in sch.DISPOSITIONS


def test_ikkinchi_trial_end_urinishi_strukturaviy_ravishda_imkonsiz(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    trial = drv.selected[0]
    timing = D.TrialTiming(begin_mono_us=1_000, horizon_end_mono_us=2_000,
                           end_mono_us=2_000)
    drv._emit_trial_end(trial, timing, {}, {}, [], {})
    with pytest.raises(D.DriverError, match="ikkinchi trial_end"):
        drv._emit_trial_end(trial, timing, {}, {}, [], {})


def test_trial_ichidagi_istisno_harness_error_disposition_beradi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)

    def boom(*a, **kw):
        raise RuntimeError("ataylab")

    drv._inject_fault = boom
    drv.run()
    recs = events(run_dir)
    ends = of_type(recs, "trial_end")
    assert len(ends) == 1
    assert ends[0]["disposition"] == "harness_error"
    # Istisno JIM qolmaydi.
    errs = of_type(recs, "harness_error")
    assert any("ataylab" in r["error"] for r in errs)


def test_istisno_olchov_tsiklini_toxtatmaydi(tmp_path):
    """Bitta trial yiqilsa, qolganlari davom etadi (dizayn qoidasi 13)."""
    drv, pf, run_dir = make_driver(tmp_path, blocks=3)
    calls = {"n": 0}
    real = drv._inject_fault

    def flaky(trial):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("ikkinchi trial'da xato")
        return real(trial)

    drv._inject_fault = flaky
    drv.run()
    ends = of_type(events(run_dir), "trial_end")
    assert len(ends) == 3
    dispositions = [e["disposition"] for e in ends]
    assert dispositions[1] == "harness_error"


def test_disposition_faktlardan_chiqadi_hukmdan_emas(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    trial = drv.selected[0]
    timing = D.TrialTiming(begin_mono_us=1, horizon_end_mono_us=2, end_mono_us=2)
    out = drv._emit_trial_end(trial, timing, {"guard_fired": True}, {}, [], {})
    assert out["disposition"] == "aborted_guard"
    rec = of_type(events(run_dir), "trial_end")[0]
    assert rec["reason"] == "guard_fired"
    assert rec["facts"]["guard_fired"] is True
    assert "guard_fired" in rec["matched_rules"]


# ===========================================================================
# trial_end.mono_us = trial_begin.mono_us + T_trial (censoring nuqtasi)
# ===========================================================================


def test_trial_end_mono_us_begin_plus_t_trial(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    recs = events(run_dir)
    b = of_type(recs, "trial_begin")[0]
    e = of_type(recs, "trial_end")[0]
    assert e["mono_us"] - b["mono_us"] == drv.t_trial_us == D.t_trial_us(sch.TrialTimeline())
    # Record washout'dan KEYIN yozilgan, lekin vaqt TO'QILMAGAN: yozish
    # vaqti alohida field'da va u horizon'dan KEYIN.
    assert e["mono_us_record_written"] > e["mono_us"]
    assert e["t_trial_actual_us"] == drv.t_trial_us


def test_horizon_pressure_offdan_keyin_w_stab_qadar_davom_etadi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    e = of_type(events(run_dir), "trial_end")[0]
    timing = e["timing"]
    tail = timing["horizon_end_mono_us"] - timing["pressure_off_mono_us"]
    assert tail == round(drv.timeline.w_stab_s * 1e6) + D.PROBE_PERIOD_US


# ===========================================================================
# Majburiyat 9 -- qo'shimcha vaqt O'LCHANADI, taxmin qilinmaydi
# ===========================================================================


def test_qoshimcha_vaqt_olchanadi_taxmin_qilinmaydi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    detail = drv.measure_overhead()
    assert detail["source"] == "measured_preflight_cycle"
    # O'lchov HAQIQIY soatdan: fake platformaning har operatsiyasi vaqt
    # sarflaydi, va o'lchangan qiymat aynan shu sarfga teng.
    expected_us = (2 * pf.unit_start_us + 2 * pf.dump_us)
    assert detail["setup_us"] == 2 * pf.unit_start_us
    assert detail["dump_us"] == 2 * pf.dump_us
    assert detail["measured_setup_teardown_s"] * 1e6 >= expected_us
    assert detail["planned_preflight_s"] == drv.timeline.preflight_s


def test_qoshimcha_vaqt_sekin_setupda_noldan_katta(tmp_path):
    # Setup rejalashtirilgan `preflight_s` dan UZUN bo'lsa, qo'shimcha vaqt
    # `estimate_campaign` ta'rifi bo'yicha noldan katta bo'ladi.
    drv, pf, run_dir = make_driver(tmp_path, unit_start_us=4_000_000)
    detail = drv.measure_overhead()
    assert detail["per_trial_overhead_s"] > 0
    assert detail["per_trial_overhead_s"] == pytest.approx(
        detail["measured_setup_teardown_s"] - drv.timeline.preflight_s)
    assert drv.measured_overhead_s == detail["per_trial_overhead_s"]


def test_run_meta_qoshimcha_vaqtni_olchangan_sifatida_yozadi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    meta = json.load(open(os.path.join(run_dir, D.RUN_META_FILE),
                          encoding="utf-8"))
    assert meta["per_trial_overhead"]["source"] == "measured_preflight_cycle"
    assert meta["per_trial_overhead_s"] is not None
    assert meta["campaign_estimate"]["per_trial_overhead_s"] == \
        meta["per_trial_overhead_s"]


def test_har_trial_ozining_qoshimcha_vaqtini_beradi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    e = of_type(events(run_dir), "trial_end")[0]
    assert e["overhead_us"] >= 0
    assert "estimate_campaign" in e["overhead_definition"]
    # Setup vaqti O'LCHANGAN, nol emas.
    assert e["timing"]["setup_us"] > 0
    assert e["timing"]["washout_us"] > 0


# ===========================================================================
# Field nomlari -- `reduce.py` ISH VAQTIDA o'qiydigan nomlar
# ===========================================================================


def test_trial_begin_pressure_band_nomini_yozadi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    b = of_type(events(run_dir), "trial_begin")[0]
    # `reduce.Trial.pressure_band` AYNAN shu nomni o'qiydi.
    assert b["pressure_band"] == "P0"
    # `schedule` dagi faktor nomi ham yoziladi -- moslashuv KO'RINADI.
    assert b["pressure_level"] == "P0"
    assert b["arm"] == "A"
    assert b["fault_class"] == "clean_crash"
    assert b["position_in_block"] is not None


def test_trial_id_va_block_index_faqat_envelopeda(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    for r in events(run_dir):
        # Envelope field'lari bir marta bor; payload ularni bosib o'tolmaydi
        # (`Emitter.record` istisno tashlaydi), demak bu tekshiruv aynan
        # shu kafolatning regressiya qulfi.
        assert "trial_id" in r
        assert "block_index" in r


def test_schedule_trial_as_dict_payload_sifatida_berilmaydi(tmp_path):
    """`Trial.as_dict()` da `trial_id` VA `block_index` bor -> to'qnashuv."""
    drv, pf, run_dir = make_driver(tmp_path)
    trial = drv.selected[0]
    with pytest.raises(ValueError, match="envelope"):
        drv._emit("trial_begin", trial.as_dict(), trial=trial)


def test_reduce_trial_begindan_arm_va_bandni_oqiydi(tmp_path):
    from revix import reduce as R
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    run = R.RawRun(records=events(run_dir))
    trials = R.split_trials(run)
    assert len(trials) == 1
    assert trials[0].arm == "A"
    assert trials[0].pressure_band == "P0"
    assert trials[0].disposition_raw in sch.DISPOSITIONS
    assert trials[0].t_trial_us == drv.t_trial_us


def test_unit_state_xom_va_snake_case_nomlarni_IKKISINI_HAM_saqlaydi():
    raw = {p: None for p in U.STATE_PROPS}
    raw.update({
        "unit": "revix-sut.service", "recv_mono_us": 777, "recv_real_us": 1,
        "signal_iface": "iface", "changed_props": ["ActiveState"],
        "changed_count": 1, "snapshot_complete": True, "missing_props": None,
        "ActiveState": "active", "Result": "success", "NRestarts": 2,
        "InvocationID": "abc", "ActiveEnterTimestampMonotonic": 500,
        "ActiveExitTimestampMonotonic": 400,
    })
    p = D.unit_state_payload(raw, "sut")
    # `reduce.py` o'qiydigan nomlar.
    assert p["active_state"] == "active"
    assert p["result"] == "success"
    assert p["n_restarts"] == 2
    assert p["invocation_id"] == "abc"
    assert p["active_enter_ts_mono_us"] == 500
    assert p["active_exit_ts_mono_us"] == 400
    # XOM systemd nomlari YUQORI DARAJADA saqlanadi (§1 -- AVTORITET).
    # Ichki dict'ga yashirish `validate.RECORD_FIELD_RULES[unit_state]` ni
    # yiqitardi: u aynan shu kalitlarni RECORD'da qidiradi.
    assert p["ActiveEnterTimestampMonotonic"] == 500
    assert p["NRestarts"] == 2
    assert all(prop in p for prop in U.STATE_PROPS)
    # Qabul vaqti ALOHIDA (§14.4).
    assert p["recv_mono_us"] == 777


def test_unit_state_bosh_timestampni_None_qiladi():
    raw = {p: None for p in U.STATE_PROPS}
    raw.update({"ActiveExitTimestampMonotonic": 0,
                "ActiveEnterTimestampMonotonic": UINT64_MAX,
                "InactiveEnterTimestampMonotonic": 12345})
    p = D.unit_state_payload(raw, "sut")
    # 0 = qo'yilmagan, UINT64_MAX = cheksiz: IKKISI HAM o'lchov EMAS.
    assert p["active_exit_ts_mono_us"] is None
    assert p["active_enter_ts_mono_us"] is None
    assert p["inactive_enter_ts_mono_us"] == 12345
    # XOM qiymat O'ZGARTIRILMAYDI: alias normalizatsiya qilinadi, xom nom yo'q.
    assert p["ActiveExitTimestampMonotonic"] == 0
    assert p["ActiveEnterTimestampMonotonic"] == UINT64_MAX


def test_unit_state_envelope_mono_us_recv_mono_us_ga_teng(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    states = of_type(events(run_dir), "unit_state")
    assert states
    for r in states:
        assert r["mono_us"] == r["recv_mono_us"]


def test_cgroup_events_trialga_bitta_record_va_FAQAT_sut_scope(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    recs = of_type(events(run_dir), "cgroup_events")
    # `reduce._oom_series` scope filtrisiz ishlaydi va `oom_kill` kalitiga
    # ega BARCHA record'ni BITTA kumulyativ qatorga qo'shadi -> trial'ga
    # bitta record, va u SUT scope'iga tegishli.
    assert len(recs) == 1
    assert recs[0]["scope"] == D.SCOPE_SUT
    assert recs[0]["oom_kill"] is not None
    # Boshqa scope'lar YO'QOLMAYDI.
    assert D.SCOPE_LAB in recs[0]["other_scopes"]
    assert D.SCOPE_BYSTANDER in recs[0]["other_scopes"]


def test_cgroup_events_payload_deltani_hisoblaydi():
    before = {"sut": {"oom_kill": 1, "high": 5}, "lab": {"oom_kill": 1}}
    after = {"sut": {"oom_kill": 3, "high": 9}, "lab": {"oom_kill": 2}}
    p = D.cgroup_events_payload(before, after)
    assert p["scope"] == "sut"
    assert p["oom_kill"] == 3
    assert p["oom_kill_delta"] == 2
    assert p["memory_events_delta"]["high"] == 4
    # Lab'ning `oom_kill` i `other_scopes` ichida -> `_oom_series` uchun
    # KO'RINMAYDI (u faqat yuqori darajadagi kalitni o'qiydi).
    assert p["other_scopes"]["lab"]["memory_events_delta"]["oom_kill"] == 1
    assert "oom_kill" not in p["other_scopes"]["lab"]


def test_actor_signal_manbani_IKKI_nomda_yozadi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    sig = of_type(events(run_dir), "actor_signal")
    assert sig, "arm A da restart kuzatilishi kerak"
    for r in sig:
        assert r["success"] is True
        # §14.4 `actor_signal_source` ni SHART qiladi; `reduce.RAW_CONTRACT`
        # esa `source` deb nomlaydi -> ikkisi ham, qiymat bir xil.
        assert r["source"] == r["actor_signal_source"]


def test_action_recordi_arm_A_da_yoziladi_no_actionda_YOZILMAYDI(tmp_path):
    drv_a, pf_a, dir_a = make_driver(tmp_path / "a", only=("P0", "A"))
    drv_a.run()
    assert of_type(events(dir_a), "action")

    drv_n, pf_n, dir_n = make_driver(tmp_path / "n", only=("P0", "no_action"))
    drv_n.run()
    # §9.3: `no_action` arm'ida (`Restart=no`) hech qanday action yuborilmaydi.
    # `reduce.build_episodes` bu holatni ochiq qo'llab-quvvatlaydi.
    assert of_type(events(dir_n), "action") == []
    assert of_type(events(dir_n), "actor_signal") == []


def test_action_policy_delay_l_dec_dan_alohida(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    a = of_type(events(run_dir), "action")[0]
    # §14.4/§6.3: sozlangan kutish vaqti ALOHIDA field, `L_dec` emas.
    assert a["policy_delay_us"] == 100_000
    assert a["action_class"] == "restart"
    assert a["actor"] == "systemd"
    assert a["deferred"] is False
    # t_issue / t_begin / t_exec alohida (shartnoma §1.2).
    assert "t_issue_mono_us" in a and "t_begin_mono_us" in a \
        and "t_exec_mono_us" in a


def test_baseline_window_oynani_beradi_throughputni_HISOBLAMAYDI(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    b = of_type(events(run_dir), "baseline_window")[0]
    assert b["mono_us_end"] - b["mono_us_begin"] == \
        round(drv.timeline.baseline_s * 1e6)
    # Throughput probe oqimida; driver uni hisoblamaydi -> None (nol EMAS).
    assert b["throughput"] is None
    assert "reduce.window_throughput" in b["throughput_source"]


def test_fault_inject_ikki_tomonli_bracket_beradi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    f = of_type(events(run_dir), "fault_inject")[0]
    assert f["mono_us_after_call"] >= f["mono_us_before_call"]
    assert f["kind"] == "exit"
    assert f["fault_class"] == "clean_crash"
    assert f["params"] == {"code": 1}
    # SUT tomoni: protokol §5 `OK armed=<kind>`.
    assert f["sut_armed"] == "exit"
    # SUT'ning O'Z soati injeksiyadan DARHOL OLDINGI `PROBE` dan (§3).
    assert f["sut_mono_us_before"] is not None
    assert f["sut_mono_us_source"] == "pre_injection_probe"
    # `stderr` dagi `FAULT ARMED mono_us=` satri saqlanmaydi -> None, va
    # qolgan cheklov OCHIQ yoziladi (jimgina nol yozilmaydi).
    assert f["sut_mono_us"] is None
    assert f["sut_mono_us_limitation"]


def test_injeksiyadan_oldingi_probe_progressni_oshirmaydi(tmp_path):
    """Protokol §4.5: probe'ga javob `progress` ni OSHIRMAYDI.

    Shuning uchun injeksiyadan oldingi namuna prober'ning kuzatuvini
    buzmaydi va arm'lar bo'yicha AYNI narx (§8.2).
    """
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    kinds = [c for k, c in pf.calls if k in ("probe", "fault")]
    # Trial'ga AYNAN bitta qo'shimcha PROBE va bitta FAULT.
    assert kinds.count("PROBE") == 1
    assert sum(1 for k in kinds if k.startswith("FAULT")) == 1


def test_sut_mono_us_parse():
    assert D._parse_sut_mono("OK progress=5 pid=1 invocation=ab "
                             "rss_kb=10 mono_us=884213771") == 884213771
    # `mono_us` protokolda IXTIYORIY -> yo'q bo'lsa None (nol EMAS).
    assert D._parse_sut_mono("OK progress=5 pid=1 invocation=ab") is None
    assert D._parse_sut_mono(None) is None


def test_fault_ack_bolmasa_trial_harness_error(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    pf.sut_command = lambda *a, **kw: {"command": "x", "reply": "ERR internal",
                                       "errno": None}
    drv.run()
    e = of_type(events(run_dir), "trial_end")[0]
    assert e["disposition"] == "harness_error"


def test_probe_satri_progress_counterdan_progress_qoshadi():
    row = {"mono_us_send": "100", "outcome": "ok", "progress_counter": "42",
           "invocation_id_seen": "abc", "trial_id": "b000t000"}
    out = D.normalise_probe_row(row)
    # `reduce.probe_from_record` AYNAN `progress` ni o'qiydi.
    assert out["progress"] == "42"
    # Xom ustun SAQLANADI (§14.4 `progress_counter` ni muzlatgan).
    assert out["progress_counter"] == "42"
    # Qiymat O'ZGARTIRILMAYDI, faqat nom qo'shiladi.
    assert out["outcome"] == "ok"


def test_probe_satri_mavjud_progressni_bosib_otmaydi():
    row = {"progress": "7", "progress_counter": "42"}
    assert D.normalise_probe_row(row)["progress"] == "7"


def test_probe_satri_bosh_progress_counterni_qoshmaydi():
    assert D.normalise_probe_row({"progress_counter": ""}).get("progress") \
        in (None, "")


def test_normalise_probe_row_reduce_bilan_ishlaydi():
    from revix import reduce as R
    row = D.normalise_probe_row(
        {"mono_us_send": "100", "outcome": "ok", "progress_counter": "42",
         "invocation_id_seen": "abc"})
    p = R.probe_from_record(row)
    # Moslashtirilmasa bu AYNAN `None` bo'lardi va `R_ref` yo'qolardi.
    assert p.progress == 42
    assert p.passed is True


# ===========================================================================
# Envelope -- `stream == record_type` (soxta seq bo'shligi bo'lmasligi uchun)
# ===========================================================================


def test_har_recordda_stream_record_typega_teng(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path, blocks=2)
    drv.run()
    recs = events(run_dir)
    assert recs
    for r in recs:
        assert r["stream"] == r["record_type"], r


def test_seq_har_record_turi_boyicha_boshliqsiz(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path, blocks=2)
    drv.run()
    # `validate._stream_key` oqimni (emitter, record_type) bilan kalitlaydi:
    # har jarayon (driver, har trial'ning prober'i) o'z oqimini yuritadi.
    streams = {}
    for r in events(run_dir):
        streams.setdefault((r["emitter"], r["stream"]), []).append(r["seq"])
    for key, seqs in streams.items():
        assert sorted(seqs) == list(range(1, len(seqs) + 1)), key


def test_validator_driver_oqimida_xato_topmaydi(tmp_path):
    """Haqiqiy validator TO'LIQ driver oqimi ustida: emitter regressiya qulfi.

    `sut_unit` / `sut_target` BERILADI, chunki xom oqim IKKALA unit va
    IKKALA target'ni saqlaydi va bu QONUNIY: bystander trace'i §12 ning
    `contaminated` disposition'i uchun dalil. Hisob tekshiruvlari esa
    reducerga BERILADIGAN ko'rinishda ishlaydi (`validate.reducer_view`),
    va u bizning `driver.reducer_input()` bilan AYNI filtrni qo'llaydi.
    """
    V = _require_strict_validator()
    drv, pf, run_dir = make_driver(tmp_path, blocks=2)
    drv.run()
    assert os.path.exists(os.path.join(run_dir, D.PROBE_FILE)), \
        "fixture probe oqimini yozishi SHART"
    assert os.path.exists(os.path.join(run_dir, D.GUARD_FILE)), \
        "fixture guard oqimini yozishi SHART"
    # `validate_run_dir` BUTUN katalogni (olti faylni) o'qiydi -- guard
    # oqimi alohida faylda (§1), demak faqat `events.jsonl` ni berish
    # `guard_start_missing` ga olib kelardi.
    rep = V.validate_run_dir(run_dir, run_mode="pilot",
                             sut_unit=D.SUT_UNIT, sut_target="sut")
    codes = {f.code for f in rep.errors}
    assert not codes, [str(f) for f in rep.errors]


def test_trial_ichidagi_host_uyqusi_driver_oqimidan_RAD_ETILADI(tmp_path):
    """Majburiyat (14 §1.3): driver yozgan soatlar uyquni ko'rsatishga yetadi.

    Fake soat trial o'rtasida (hold fazasida) realtime'ni 07 §7.7 ning
    o'lchangan miqdoriga (+42 088.789883 s, mono o'zgarmaydi) sakratadi.
    `boot_id` va guest generation o'zgarmaydi -- aynan haqiqiy holat.
    Driver o'zi hech narsa sezmaydi (disposition `complete`), lekin
    validator run'ni rad etadi va aynan shu trial'ni ko'rsatadi.
    """
    V = _require_strict_validator()
    drv, pf, run_dir = make_driver(tmp_path, blocks=1)
    pf.real_jump_us = 42_088_789_883      # 07 §7.7: Δreal − Δmono
    pf.real_jump_at_us = None             # run boshida sakrash YO'Q
    t_trial0 = {}
    orig = drv._emit_trial_begin

    def _begin(trial, index, arm, level, mono):
        # Birinchi trial boshlanishidan 20 s keyin (hold ichida) uyqu.
        t_trial0.setdefault(trial.trial_id, mono)
        if len(t_trial0) == 1:
            pf.real_jump_at_us = mono + 20_000_000
        return orig(trial, index, arm, level, mono)

    drv._emit_trial_begin = _begin
    summary = drv.run()
    assert summary["ok"] and set(summary["dispositions"]) == {"complete"}
    rep = V.validate_run_dir(run_dir, run_mode="pilot",
                             sut_unit=D.SUT_UNIT, sut_target="sut")
    errs = [f for f in rep.errors]
    assert [f.code for f in errs] == ["host_clock_discontinuity"], \
        [str(f) for f in errs]
    f = errs[0]
    first_tid = next(iter(t_trial0))
    assert f.detail["trials_affected"][0] == first_tid
    assert f.detail["max_abs_jump_us"] == 42_088_789_883
    # Har trial'ning trial_end'i yozish-lahzali juftni olib yuradi.
    for te in of_type(events(run_dir), "trial_end"):
        assert isinstance(te["mono_us_record_written"], int)
        assert isinstance(te["real_us"], int)


def test_validator_sut_filtrisiz_aralashuvni_RAD_ETADI(tmp_path):
    """Filtrsiz xom katalog RAD ETILISHI kerak -- bu kutilgan xatti-harakat.

    Bu `reducer_input()` filtrining ZARURLIGINI isbotlaydi: bystander
    oqimi filtrsiz reducerga yetib borsa, §4 ning 3-4 bandlari va
    throughput hisobi buziladi.
    """
    V = _require_strict_validator()
    drv, pf, run_dir = make_driver(tmp_path, blocks=1)
    drv.run()
    rep = V.validate_run_dir(run_dir, run_mode="pilot")   # filtr YO'Q
    codes = {f.code for f in rep.errors}
    # Probe oqimida ikki target bor (bystander -- §8.2 spillover detektori),
    # demak filtrsiz reducerga berilgan kirish RAD ETILADI.
    assert "probe_targets_mixed" in codes
    # `unit_state` aralashuvi bu fixture'da YUZAGA KELMAYDI, chunki sog'lom
    # bystander record oynasi ichida hech qanday o'tish bermaydi -- aralashuv
    # faqat bystander buzilganda paydo bo'ladi, va o'sha holat `contaminated`
    # disposition'ining o'zi. Filtr baribir SHART: u holatga bog'liq
    # bo'lmasligi kerak.
    # Filtr BILAN -- xato yo'q. Ayni ma'lumot, ayni validator.
    ok = V.validate_run_dir(run_dir, run_mode="pilot",
                            sut_unit=D.SUT_UNIT, sut_target="sut")
    assert not ok.errors, [str(f) for f in ok.errors]


def test_reducer_input_validator_bilan_bir_xil_filtrni_qoladi(tmp_path):
    """`driver.reducer_input` va `validate.reducer_view` AYNI natijani beradi."""
    from revix import reduce as R
    V = _require_strict_validator()
    drv, pf, run_dir = make_driver(tmp_path, blocks=1)
    drv.run()
    recs = events(run_dir)
    rows = R.load_probe_csv(os.path.join(run_dir, D.PROBE_FILE))
    mine_r, mine_p = D.reducer_input(recs, rows)
    theirs = V.reducer_view(R.RawRun(records=recs, probes=rows),
                            D.SUT_UNIT, "sut")
    assert len(mine_r) == len(theirs.records)
    assert len(mine_p) == len(theirs.probes)
    assert {r.get("unit") for r in mine_r
            if r["record_type"] == "unit_state"} == {D.SUT_UNIT}
    assert {p["target"] for p in mine_p} == {"sut"}


# ===========================================================================
# run_meta -- shartnoma §1.1 majburiy maydonlari
# ===========================================================================


def test_run_meta_majburiy_maydonlar(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    meta = json.load(open(os.path.join(run_dir, D.RUN_META_FILE),
                          encoding="utf-8"))
    for key in ("preregistration_sha256", "preregistration_version",
                "git_commit", "git_dirty", "rng_seed", "schedule_digest",
                "uname", "systemd_version", "cpu_count",
                "cgroup_delegated_controllers", "oomd_effective",
                "governor", "scaling_driver", "python_version",
                "module_versions", "units_show", "schedule", "run_mode",
                "started_real_us", "started_mono_us", "t_trial_us",
                "t_trial_formula"):
        assert key in meta, key
    assert meta["t_trial_us"] == D.t_trial_us(sch.TrialTimeline())
    assert meta["rng_seed"] == 11
    assert meta["schedule_digest"] == drv.schedule.digest()


def test_run_meta_prereg_hashi_fayl_baytlaridan(tmp_path):
    info = D.preregistration_info()
    assert len(info["preregistration_sha256"]) == 64
    assert info["preregistration_version"].startswith("preregistration/")


def test_governor_va_scaling_driver_None_bosh_royxat_emas(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    meta = json.load(open(os.path.join(run_dir, D.RUN_META_FILE),
                          encoding="utf-8"))
    # §15.4 NORMATIV: bu mashinada o'lchash IMKONSIZ -> None.
    # Bo'sh ro'yxat yoki 0 O'LCHOV kabi o'qilardi.
    assert meta["governor"] is None
    assert meta["scaling_driver"] is None
    assert meta["dvfs_measurable"] is False
    # `doctor` ning xom shakli ham saqlanadi -- ma'lumot yo'qolmaydi.
    assert meta["cpu_governor_detail"]["os_cpu_count"] == 12


def test_none_if_empty_faqat_boshni_None_qiladi():
    assert D._none_if_empty([]) is None
    assert D._none_if_empty("") is None
    assert D._none_if_empty({}) is None
    assert D._none_if_empty(0) == 0          # O'LCHANGAN NOL saqlanadi
    assert D._none_if_empty(["powersave"]) == ["powersave"]


def test_env_snapshot_olchanmagan_kovariatalarni_None_bilan_YOZADI(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    snaps = of_type(events(run_dir), "env_snapshot")
    assert len(snaps) == 2          # trial boshida va oxirida
    for s in snaps:
        # Kalit MAVJUD va None: tushirib qoldirish BOSHQA da'vo bo'lardi.
        assert "cpu_freq_khz" in s and s["cpu_freq_khz"] is None
        assert "thermal_c" in s and s["thermal_c"] is None
        assert s["dvfs_source"]
        # §8.2: harness'ning O'Z sarfi (`revixmon.slice`) ham yoziladi.
        assert D.SCOPE_MON in s["scopes"]
        assert "cpu_stat" in s["scopes"][D.SCOPE_MON]


def test_run_meta_ikki_joyga_yoziladi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    # Fayl (shartnoma §1) VA record (§14.3 + validate.check_run_meta).
    assert os.path.exists(os.path.join(run_dir, D.RUN_META_FILE))
    assert len(of_type(events(run_dir), "run_meta")) == 1


def test_run_meta_ochiq_parametrlarni_kalibratsiya_talab_qiladi_deb_belgilaydi(
        tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    meta = json.load(open(os.path.join(run_dir, D.RUN_META_FILE),
                          encoding="utf-8"))
    op = meta["open_parameters"]
    # v1.12 (1-band) dan beri uchalasi MUZLATILGAN: `calibration_required`
    # False. Lekin `timeout_start_sec` KALIBRLANGAN EMAS -- buni
    # `rule_satisfied` aytadi (alohida test pastda).
    for key in ("memory_high", "watchdog_sec", "timeout_start_sec"):
        assert op[key]["calibration_required"] is False
        assert op[key]["frozen_in"] == "preregistration/v1.12"
        assert op[key]["source"]
    assert op["memory_high"]["rule_satisfied"] is True
    assert op["watchdog_sec"]["rule_satisfied"] is True
    assert op["timeout_start_sec"]["rule_satisfied"] is False
    # O'LCHANDI, demak belgi YECHILDI (10-pressure-dozalash.md §2.6, §3.1).
    # `None` = o'lchanmadi, `0`/`False` = o'lchangan -- dizayn qoidasi 15.
    # `ramp_above_threshold_s` SHU RO'YXATGA KO'CHDI: §4.1 uni HAQIQIY doza
    # ostida 29/29 epizodda 0.000 s deb o'lchadi. Batafsil tasdiqlar
    # `test_run_meta_ramp_above_threshold_OLCHANGAN_deb_yoziladi` da.
    for key in ("pressure_target_rate", "step_mb", "base_mb", "interval_ms",
                "ramp_above_threshold_s"):
        assert op[key]["calibration_required"] is False
        assert op[key]["source"]


def test_run_meta_ramp_above_threshold_OLCHANGAN_deb_yoziladi(tmp_path):
    """Yashil test YOLG'ONNI himoya qilmasligi SHART.

    Avval shu faylda `op["ramp_above_threshold_s"]["calibration_required"]
    is True` tasdiqlanardi va test O'TARDI -- lekin da'vo NOTO'G'RI edi:
    kalibratsiya `docs/architecture/10-pressure-dozalash.md` §4.1 da
    BAJARILGAN (HAQIQIY doza ostida, 29 epizoddan 29 tasida 0.000 s), va
    §4.2 dan buyon invariant 2 shu 0.000 bilan yozilmoqda. O'tib turgan
    test noto'g'ri da'voni QULFLAB qo'ygan edi -- nuqsonning yomon yarmi
    shu.

    Boolean'ni `False` ga aylantirish YETARLI EMAS: `run_meta` ni
    o'qiydigan odam (a) qiymat o'lchanganini, (b) QAYERDA o'lchanganini,
    (c) rejada qancha zaxira qolganini ko'rishi kerak. Shuning uchun
    `calibration` bloki tekshiriladi, va zaxira HISOBLANADI -- matndan
    o'qilmaydi.
    """
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    meta = json.load(open(os.path.join(run_dir, D.RUN_META_FILE),
                          encoding="utf-8"))
    op = meta["open_parameters"]["ramp_above_threshold_s"]
    assert op["calibration_required"] is False
    # Provenance `source` ning O'ZIDA ham bo'lishi kerak -- `calibration`
    # blokini o'qimagan vosita ham manbani ko'radi.
    assert "10-pressure-dozalash.md" in op["source"]
    assert "§4.1" in op["source"]

    cal = op["calibration"]
    # (a) + (b): o'lchov, uning manbasi va epizod soni.
    assert cal["measured_s"] == 0.0
    assert cal["measured_episodes"] == 29
    assert cal["measured_episodes_at_value"] == 29
    assert "10-pressure-dozalash.md" in cal["measured_in"]
    assert "§4.1" in cal["measured_in"]
    # O'lchov QAYSI dial'da bajarilgan -- driver'ning O'Z qiymatlaridan,
    # hardcode qilinmaydi (§4.1: base_mb=184, step_mb=4).
    assert cal["measured_dial"]["base_mb"] == D.PRESSURE_BASE_MB["P2"]
    assert cal["measured_dial"]["step_mb"] == D.PRESSURE_STEP_MB
    assert cal["measured_dial"]["memory_high"] == drv.cfg.memory_high

    # (c) ZAXIRA: reja minus o'lchov, HISOBLANADI.
    assert cal["planned_s"] == pytest.approx(sch.RAMP_ABOVE_THRESHOLD_S)
    assert cal["plan_slack_s"] == pytest.approx(
        cal["planned_s"] - cal["measured_s"])
    # Reja o'lchovdan PAST bo'lishi mumkin emas: bu oldindan buzilgan
    # reja bo'lardi. 0.0 = zaxira YO'Q, va bu `run_meta_payload`
    # docstring'idagi CHEKLOV'ning aynan predmeti.
    assert cal["plan_slack_s"] >= 0.0

    # §9.4 invariant 2 ning zaxirasi SHU run'ning timeline'idan.
    tl = meta["timeline"]
    assert cal["guard_sustain_headroom_s"] == pytest.approx(
        tl["guard_sustain_window_s"]
        - (tl["hold_s"] + tl["ramp_above_threshold_s"]))
    assert cal["guard_sustain_headroom_s"] >= 0.0


# ===========================================================================
# Guest generation -- `boot_id` TUTMAYDIGAN monotonic uzilish
# ===========================================================================


def test_guest_generation_pid1_statdan_parse_qilinadi():
    # `/proc/1/stat`: 1=pid, 2=comm (QAVS ICHIDA, bo'sh joy bo'lishi mumkin),
    # 3=state ... 22=starttime. Parse OXIRGI ')' dan keyin bo'linadi.
    tail = ["S"] + [str(i) for i in range(4, 22)] + ["19153", "extra"]
    stat = "1 (systemd with space) " + " ".join(tail)
    g = D.parse_guest_generation(stat, "199.91 1500.0", clk_tck=100)
    assert g["pid1_starttime_ticks"] == 19153
    assert g["pid1_starttime_s"] == pytest.approx(191.53)
    assert g["uptime_s"] == pytest.approx(199.91)
    assert g["comparable"] is True
    assert g["identity_key"] == "pid1_starttime_ticks"


def test_guest_generation_haqiqiy_proc_1_statni_oqiydi():
    """Haqiqiy `/proc/1/stat` ustida parse ishlashi SHART."""
    if not os.path.exists("/proc/1/stat"):
        pytest.skip("/proc/1/stat yo'q (Linux emas)")
    g = D.parse_guest_generation(open("/proc/1/stat").read(),
                                 open("/proc/uptime").read(),
                                 clk_tck=os.sysconf("SC_CLK_TCK"))
    assert g["comparable"] is True
    assert g["pid1_starttime_ticks"] >= 0
    # PID 1 guest uptime'idan kechikib boshlangan bo'lsa, bu guest
    # restart'ining IZI (o'lchangan xatti-harakat) -- parse buni ko'rsatadi.
    assert g["pid1_starttime_s"] <= g["uptime_s"] + 1.0


def test_guest_generation_oqilmasa_fail_closed():
    g = D.parse_guest_generation(None, None)
    assert g["generation"] is None
    assert g["comparable"] is False
    changed, why = D.guest_generation_changed(g, g)
    # O'qilmagan marker "o'zgarmadi" DEB HISOBLANMAYDI (guard qoidasi 3).
    assert changed is True
    assert why == "guest_generation_unreadable"


def test_guest_generation_ozgarishi_aniqlanadi():
    a = {"pid1_starttime_ticks": 100, "comparable": True, "uptime_s": 500.0}
    b = {"pid1_starttime_ticks": 7, "comparable": True, "uptime_s": 10.0}
    assert D.guest_generation_changed(a, a) == (False, "unchanged")
    assert D.guest_generation_changed(a, b)[0] is True
    assert D.guest_generation_changed(a, b)[1] == "pid1_starttime_changed"


def test_uptime_identiklikka_KIRMAYDI():
    """`uptime_s` har sekundda o'sadi -> identiklikka kirsa HAR trial
    soxta "o'zgardi" berardi. Shuning uchun u ATAYLAB e'tiborsiz."""
    a = {"pid1_starttime_ticks": 55, "comparable": True, "uptime_s": 10.0}
    b = {"pid1_starttime_ticks": 55, "comparable": True, "uptime_s": 9999.0}
    assert D.guest_generation_changed(a, b) == (False, "unchanged")


def test_guest_restart_kampaniyani_toxtatadi(tmp_path):
    after = {"pid1_starttime_ticks": 9, "uptime_s": 5.0,
             "pid1_starttime_s": 0.09, "generation": "pid1:9",
             "comparable": True, "clk_tck": 100}
    drv, pf, run_dir = make_driver(tmp_path, blocks=3,
                                   guest_generation_after=after)
    with pytest.raises(D.GuestRestartError):
        drv.run()
    # Restart'dan keyingi ma'lumot oldingisiga QO'SHILMAYDI: run to'xtaydi.
    assert of_type(events(run_dir), "trial_begin") == []
    assert of_type(events(run_dir), "harness_error")


def test_guest_generation_run_metaga_va_har_env_snapshotga_yoziladi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    meta = json.load(open(os.path.join(run_dir, D.RUN_META_FILE),
                          encoding="utf-8"))
    assert meta["guest_generation"]["comparable"] is True
    assert meta["guest_generation"]["pid1_starttime_ticks"] == 111
    assert meta["pid1_starttime_ticks"] == 111
    assert meta["boot_id_note"]
    snaps = of_type(events(run_dir), "env_snapshot")
    assert len(snaps) >= 2          # har o'lchangan trial uchun kamida ikki
    for s in snaps:
        assert s["guest_generation"]["pid1_starttime_ticks"] == 111


# ===========================================================================
# Pressure eshigi -- struktura bilan majburlanadi
# ===========================================================================


def test_P0_dan_boshqa_daraja_allow_pressuresiz_rad_etiladi(tmp_path, capsys):
    rc = D.main(["--run-dir", str(tmp_path / "run"), "--seed", "4",
                 "--blocks", "1", "--only", "P2", "--json"])
    assert rc == 2
    out = json.loads(capsys.readouterr().out)
    assert out["error_type"] == "PressureNotAllowedError"
    # Katalog HAM yaratilmaydi: rad etish prepare_run_dir'dan OLDIN.
    assert not os.path.exists(str(tmp_path / "run"))


def test_P0_run_generatorni_umuman_ishga_tushirmaydi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    assert D.PRESS_UNIT not in pf.started
    e = of_type(events(run_dir), "trial_end")[0]
    assert e["detail"]["pressure"]["started"] is False


def test_pressure_generatorini_bevosita_chaqirish_ham_rad_etiladi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    with pytest.raises(D.PressureNotAllowedError):
        drv._start_pressure(drv.selected[0], "P2", 10.0)


# ===========================================================================
# Doza dial'i -- OQ-2 ning regressiya QULFLARI
# (docs/architecture/10-pressure-dozalash.md §2 va §3)
#
# NEGA BU BO'LIM BOR: §2.5 ni o'lchov shunday topdi -- `_pressure_argv`
# generatorga dial bermaganida pilot `pressure.py` ning default'ini
# (`step_mb=16`) meros qilib, `base = 192 - 2*16 = 160 MiB` da ishlagan va
# bu §2.2 ning D1 epizodida O'LCHANGAN nol-doza konfiguratsiyasi
# (erishilgan stall 114 namunada ham aynan 0.0000). Oqibati: `P1` va `P2`
# arm'lari 0.0000 doza bilan ishlab, PREREGISTRATION.md §9.3 ning UCH
# darajali dizayni jimgina BITTA darajaga qulardi -- natija H1 ga qarshi
# dalil emas, ASBOB NUQSONI bo'lardi, va chiqishda buni ko'rsatuvchi hech
# narsa yo'q edi. Shuning uchun qulflar LITERALNI emas, MUNOSABATNI ham
# tekshiradi.
# ===========================================================================


def _mib(spec):
    """systemd hajm spetsifikatsiyasidan MiB.

    `pressure.run_pi` bazani MiB da hisoblaydi (`high // (1 << 20)`), demak
    qulf ham aynan o'sha birlikda tekshirishi kerak.
    """
    s = str(spec).strip()
    mult = {"K": 1.0 / 1024, "M": 1.0, "G": 1024.0}
    if s and s[-1].upper() in mult:
        return float(s[:-1]) * mult[s[-1].upper()]
    return float(s) / (1 << 20)


def _run_pi_derived_base_mb(high_mib, step_mb):
    """`pressure.run_pi` ning O'Z avtomatik formulasi (pressure.py:375):

        base = max(16, (high // (1 << 20)) - 2 * step_mb)

    Bu yerda QAYTA YOZILGANI ataylab: OQ-2 ning nuqsoni aynan SHU formulaga
    jim tayanishdan kelib chiqqan, demak qulf uni O'ZI hisoblab, driver
    bergan oshkora bazaga TENG BO'LMASLIGINI talab qiladi.
    """
    return max(16, int(high_mib) - 2 * int(step_mb))


def test_pressure_argv_P1_va_P2_kalibrlangan_dialni_beradi(tmp_path):
    """§2.6: `step_mb=4`, `base_mb=184` -- IKKISI HAM argv'da."""
    drv, pf, run_dir = make_driver(tmp_path)
    drv.setup_run()
    for level in ("P1", "P2"):
        argv = drv._pressure_argv(level, 17.0)
        assert _flag_value(argv, "--step-mb") == "4", level
        assert _flag_value(argv, "--base-mb") == "184", level
        # §2.2 D2: step_mb=4 + base_mb=184 -> erishilgan p50 0.3344.
        assert "--step-mb" in argv and "--base-mb" in argv, level


def test_pressure_argv_interval_ms_ni_ham_MEROS_QOLDIRMAYDI(tmp_path):
    """§2.6: control tik'i 250 ms -- OSHKORA, modul default'idan EMAS.

    Bugun qiymatlar teng, demak nuqson yo'q. Qulf TENGLIKKA tayanmaydi:
    u argv'da bayroq BORLIGINI va qiymatning kalibrlangan 250 ms ekanini
    talab qiladi, shuning uchun `pressure.py` ning default'i o'zgarsa ham
    pilotning tik'i o'zgarmaydi -- `step_mb` merosi bilan bir xil klass.
    """
    import inspect

    from revix import pressure as P

    drv, pf, run_dir = make_driver(tmp_path)
    drv.setup_run()
    for level in D.PRESSURE_LEVELS:
        argv = drv._pressure_argv(level, 17.0)
        assert "--interval-ms" in argv, level
        assert _flag_value(argv, "--interval-ms") == "250", level
    assert D.PRESSURE_INTERVAL_MS == 250
    # Bugun modul default'i bilan BIR XIL -- bu FAKT yoziladi, unga
    # TAYANILMAYDI. Teng bo'lmasa ham argv kalibrlangan qiymatni beradi.
    module_default = inspect.signature(
        P.PressureGenerator.run_pi).parameters["interval_ms"].default
    assert module_default == 250.0


def test_pressure_argv_P0_olchangan_nol_doza_bazasini_beradi(tmp_path):
    """§3.2: `P0` ATAYLAB nol doza -- `base_mb=160`, nishon 0.0.

    `P0` da nol doza NUQSON EMAS, u §9.3 ning "generator idle" sharti:
    generator tirik, 160 MiB rezident, `memory.events high` delta 0 va
    98 namunada stall aynan 0.0000 (9.8/9.8 s band ichida).
    """
    drv, pf, run_dir = make_driver(tmp_path)
    drv.setup_run()
    argv = drv._pressure_argv("P0", 17.0)
    assert _flag_value(argv, "--base-mb") == "160"
    assert _flag_value(argv, "--step-mb") == "4"
    assert _flag_value(argv, "--target-rate") == "0.0"


def test_doza_argvsi_NOL_DOZA_konfiguratsiyasiga_qayta_tusha_olmaydi(tmp_path):
    """ENG MUHIM QULF: literalni emas, MUNOSABATNI ushlaydi.

    To'rtta shart, hammasi driver'ning O'Z qiymatlaridan hisoblanadi
    (`MemoryHigh` slice property'sidan, `step_mb`/`base_mb` argv'dan):

      1. dial OSHKORA argv'da -- `run_pi` bazani UMUMAN derivatsiya
         qilmaydi (`base_mb is not None` yo'li, pressure.py:367);
      2. baza `run_pi` ning MODUL DEFAULT'i bilan chiqadigan qiymatga TENG
         EMAS (`max(16, high_MiB - 2*16)` = bugun 160 MiB) -- bu §2.2 ning
         D1 epizodida O'LCHANGAN nol-doza konfiguratsiyasi;
      3. `base_mb + overhead > MemoryHigh_MiB` -- §2.2 ning breach sharti,
         ya'ni doza HAQIQATAN yetkaziladi (overhead 25.3 MiB O'LCHANGAN);
      4. `base_mb < MemoryHigh_MiB` -- §2.4 / §4.1 ning "ramp bepul" sharti
         (`base=184` da `ramp_above_threshold_s` 29/29 epizodda 0.000 s;
         `base=196` da ramp 12.217 s davom etib §9.4 invariant 2 ni buzdi).

    ESLATMA (§2.1): `base=184` AYNAN `step_mb=4` da formuladan ham chiqadi,
    shuning uchun 2-shart `step_mb` ning argv'dagi qiymatini EMAS, modul
    DEFAULT'ini ishlatadi -- nol doza aynan o'sha merosdan kelgan.

    NIMANI TUTADI: `MemoryHigh` ni 192M dan boshqa qiymatga o'zgartirib
    `base_mb` ni qayta o'lchamaslik. Masalan `MemoryHigh=256M` da
    `184 + 25.3 = 209.3 < 256` -> breach YO'Q -> yana 0.0000 doza; 3-shart
    o'sha o'zgarishda YIQILADI, pilot esa jimgina null bermaydi. Shuningdek
    `--base-mb` ni argv'dan olib tashlash (1-shart) va bazani nol-doza
    qiymatiga qaytarish (2-shart) ham tutiladi.
    """
    import inspect

    from revix import pressure as P

    step_default = inspect.signature(
        P.PressureGenerator.run_pi).parameters["step_mb"].default
    drv, pf, run_dir = make_driver(tmp_path)
    setup = drv.setup_run()
    # `MemoryHigh` driver'ning O'ZI slice'ga qo'ygan qiymatdan olinadi --
    # test uni hardcode QILMAYDI.
    high_mib = _mib(setup["lab_slice_properties"]["MemoryHigh"])
    for level in ("P1", "P2"):
        argv = drv._pressure_argv(level, 17.0)
        assert "--step-mb" in argv and "--base-mb" in argv, (
            f"{level}: dial argv'da yo'q -> run_pi bazani O'ZI chiqaradi "
            "-> OQ-2 qaytdi")
        base_mb = int(_flag_value(argv, "--base-mb"))
        zero_dose = _run_pi_derived_base_mb(high_mib, step_default)
        assert base_mb != zero_dose, (
            f"{level}: baza modul default'i bilan chiqadigan nol-doza "
            f"qiymatiga teng ({zero_dose} MiB) -- OQ-2 qaytdi")
        assert base_mb + D.PRESSURE_OVERHEAD_MB > high_mib, (
            f"{level}: {base_mb} + {D.PRESSURE_OVERHEAD_MB} <= {high_mib} "
            "MiB -> memory.high buzilmaydi -> O'LCHANGAN 0.0000 doza "
            "(10-pressure-dozalash.md §2.2)")
        assert base_mb < high_mib, (
            f"{level}: baza ({base_mb}) MemoryHigh ({high_mib} MiB) dan past "
            "bo'lishi SHART, aks holda ramp bepul bo'lmaydi (§2.4, §4.1)")


def test_modul_defaulti_bilan_derivatsiya_OLCHANGAN_NOL_DOZANI_beradi():
    """Qulfning ASOSI: dial berilmasa nima bo'lardi -- o'lchov bilan.

    §2.2 ning jadvali (`MemoryHigh=192M`, nishon 0.30):
      step_mb=16 -> base 160 -> erishilgan p50 0.0000 (D1, NOL doza)
      step_mb=8  -> base 176 -> erishilgan p50 0.0138 (D3)
      step_mb=4  -> base 184 -> erishilgan p50 0.3344 (D2, DOZA BOR)
    """
    import inspect

    from revix import pressure as P

    # Modul default'i KODDAN o'qiladi, test uni taxmin qilmaydi.
    step_default = inspect.signature(
        P.PressureGenerator.run_pi).parameters["step_mb"].default
    assert step_default == 16
    high_mib = _mib(D.DEFAULT_MEMORY_HIGH)
    assert high_mib == 192.0
    assert _run_pi_derived_base_mb(high_mib, step_default) == 160
    # 160 + 25.3 = 185.3 < 192 -> breach YO'Q -> 0.0000 (§2.2 D1).
    assert 160 + D.PRESSURE_OVERHEAD_MB < high_mib
    # 184 + 25.3 = 209.3 > 192 -> breach BOR -> 0.33 (§2.2 D2).
    assert D.PRESSURE_BASE_MB["P1"] + D.PRESSURE_OVERHEAD_MB > high_mib
    assert D.PRESSURE_BASE_MB["P2"] + D.PRESSURE_OVERHEAD_MB > high_mib
    # `P0` ning bazasi esa AYNAN nol-doza qiymati -- bu ATAYLAB (§3.2).
    assert D.PRESSURE_BASE_MB["P0"] == 160


def test_P2_nishoni_olchangan_0_60_band_markazi_EMAS():
    """§3.1: nishon 0.70 -> erishilgan 0.8868 (band USTIDA, over-doza);
    nishon 0.60 -> epizod medianalari 0.5726..0.9213, p50 0.7023, 8/11
    band ichida (§3.4). Xarita chiziqli emas va monoton emas, demak bu
    EMPIRIK qiymat -- mulohaza bilan qayta chiqarib olinmaydi.
    """
    assert D.PRESSURE_TARGET_RATE["P2"] == 0.60
    # `P1` O'ZGARMADI: §3.3 da erishilgan p50 0.2810 (xato -0.0190).
    assert D.PRESSURE_TARGET_RATE["P1"] == 0.30
    assert D.PRESSURE_TARGET_RATE["P0"] == 0.0
    # §9.3 bandlari -- nishonlar band ICHIDA bo'lishi SHART.
    assert 0.60 <= D.PRESSURE_TARGET_RATE["P2"] <= 0.80
    assert 0.20 <= D.PRESSURE_TARGET_RATE["P1"] <= 0.35
    # Nishon argv'ga aynan shu qiymat bilan tushadi.
    assert D.pressure_target_rate("P2") == 0.60


def test_pressure_base_mb_notogri_daraja_uchun_jim_default_bermaydi():
    """FAIL-CLOSED: OQ-2 ning nuqsoni JIM DEFAULT edi, shu takrorlanmaydi."""
    assert sorted(D.PRESSURE_BASE_MB) == sorted(D.PRESSURE_TARGET_RATE)
    with pytest.raises(D.DriverError):
        D.pressure_base_mb("P3")


def test_run_meta_doza_arifmetikasini_HISOBLAB_yozadi(tmp_path):
    """`run_meta.open_parameters.base_mb.dose_arithmetic` -- §2.2 ning
    breach sharti har run'da hisoblanadi.

    NEGA KERAK: `--memory-high` RUNTIME bayrog'i, demak yuqoridagi
    regressiya qulfi uni tutib qolmaydi. Nol doza hech bo'lmaganda
    CHIQISHDA ko'rinishi SHART -- §2.5 ning eng xavfli jihati aynan
    izning yo'qligi edi.
    """
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    meta = json.load(open(os.path.join(run_dir, D.RUN_META_FILE),
                          encoding="utf-8"))
    arith = meta["open_parameters"]["base_mb"]["dose_arithmetic"]
    assert set(arith) == set(D.PRESSURE_LEVELS)
    # §2.2 arifmetikasi: 184 + 25.3 = 209.3 > 192 -> breach -> doza BOR.
    for level in ("P1", "P2"):
        a = arith[level]
        assert a["projected_memory_current_mb"] == pytest.approx(209.3)
        assert a["memory_high_mib"] == 192.0
        assert a["breach_expected"] is True
        assert a["ramp_free_expected"] is True
        assert a["dose_expected"] is True
        assert a["breach_margin_mb"] == pytest.approx(17.3)
    # `P0` da breach YO'Q va bu ATAYLAB (§3.2 -- generator idle).
    p0 = arith["P0"]
    assert p0["projected_memory_current_mb"] == pytest.approx(185.3)
    assert p0["breach_expected"] is False
    assert p0["dose_expected"] is False


def test_doza_arifmetikasi_memory_high_ozgarsa_NOL_DOZANI_oshkor_qiladi():
    """`--memory-high` bilan dial buzilsa, FAKT yoziladi (jim emas).

    Bu test qulfning TESHIGINI hujjatlashtiradi: runtime bayrog'i test
    vaqtida ko'rinmaydi, shuning uchun `dose_expected` oqimga tushadi.
    """
    ok = D.pressure_dose_arithmetic("P1", "192M")
    assert ok["breach_expected"] is True and ok["dose_expected"] is True
    # 184 + 25.3 = 209.3 < 256 -> breach YO'Q -> O'LCHANGAN 0.0000 doza.
    broken = D.pressure_dose_arithmetic("P1", "256M")
    assert broken["breach_expected"] is False
    assert broken["dose_expected"] is False
    assert broken["breach_margin_mb"] < 0
    # Baza `MemoryHigh` dan yuqori bo'lsa ramp bepul bo'lmaydi (§2.4, §3.6).
    over = D.pressure_dose_arithmetic("P1", "176M")
    assert over["ramp_free_expected"] is False


def test_nol_doza_dialida_RUN_BOSHLANMAYDI(tmp_path):
    """FAIL-CLOSED pre-flight: `--memory-high` ni test tutib qolmaydi.

    `--memory-high 256M` da `184 + 25.3 = 209.3 < 256` -> breach YO'Q ->
    O'LCHANGAN 0.0000 doza. Bu run ~2.5 soat ishlab, H1 ga qarshi dalilga
    AYNAN O'XSHAGAN null berardi (§2.5). Shuning uchun ogohlantirish emas,
    `ZeroDoseError` -- va u slice dial'lari YUKLANISHIDAN OLDIN otiladi.
    """
    run_dir = D.prepare_run_dir(str(tmp_path / "run"))
    pf = FakePlatform(tmp_path)
    cfg = D.DriverConfig(run_dir=run_dir, seed=11, blocks=1,
                         only=("P2", "A"), allow_pressure=True,
                         sut_binary="/nonexistent/sut", memory_high="256M")
    drv = D.Driver(cfg, pf, sch.p1_schedule(11, n_blocks=1),
                   sch.TrialTimeline())
    with pytest.raises(D.ZeroDoseError) as exc:
        drv.setup_run()
    msg = str(exc.value)
    # Xabar ARIFMETIKANI ko'rsatadi, quruq rad etishni emas.
    assert "P2" in msg and "209.3" in msg and "256.0" in msg
    assert "base_mb=184" in msg
    # Dial'lar systemd'ga YUKLANMADI -- rad etilgan run holat qoldirmaydi.
    assert not any(k == "set_slice" for k, _ in pf.calls), pf.calls


def test_P0_run_nol_doza_preflightidan_OTADI(tmp_path):
    """`P0` ning nol dozasi §9.3 ning "generator idle" sharti (§3.2).

    Shuning uchun pre-flight faqat `target_rate > 0` bandlarga qo'yiladi --
    aks holda u har `P0` run'ini rad etardi.
    """
    drv, pf, run_dir = make_driver(tmp_path)
    setup = drv.setup_run()
    dose = setup["dose_preflight"]
    assert dose["levels_checked"] == ["P0"]
    assert dose["arithmetic"]["P0"]["breach_expected"] is False
    assert D.pressure_target_rate("P0") == 0.0


def test_nol_doza_preflighti_FAQAT_jadvaldagi_bandlarni_tekshiradi(tmp_path):
    """`--only P0,A` run'i `P1`/`P2` ning dial'i uchun rad etilmaydi.

    NEGA: u ularni ishlatmaydi. Pre-flight `--only` filtridan KEYINGI
    jadvalga qaraydi.
    """
    run_dir = D.prepare_run_dir(str(tmp_path / "run"))
    pf = FakePlatform(tmp_path)
    cfg = D.DriverConfig(run_dir=run_dir, seed=11, blocks=1,
                         only=("P0", "A"), sut_binary="/nonexistent/sut",
                         memory_high="256M")
    drv = D.Driver(cfg, pf, sch.p1_schedule(11, n_blocks=1),
                   sch.TrialTimeline())
    setup = drv.setup_run()     # 256M bo'lsa ham RAD ETILMAYDI
    assert setup["dose_preflight"]["levels_checked"] == ["P0"]


def test_nol_doza_preflighti_RAMP_shartini_tekshirmaydi_QAYD_ETILGAN(tmp_path):
    """CHEKLOV hujjatlashtiriladi, yashirilmaydi.

    Pre-flight sharti FAQAT `breach_expected`. `MemoryHigh=176M` da
    `184 + 25.3 = 209.3 > 176` -> breach BOR, demak run BOSHLANADI --
    lekin `base_mb=184 > 176` va §2.4/§4.1 ning "ramp bepul" sharti
    BUZILADI (§3.6: `base=196 > high=192` ramp'ni 12.217 s cho'zib §9.4
    invariant 2 ni buzgan).

    Bu test o'sha xatti-harakatni QULFLAYDI, ya'ni kelajakda shart
    kengaytirilsa test o'zgarishi kerak bo'ladi -- jimgina o'zgarmaydi.
    Yo'l jim emas: `ramp_free_expected` oqimga tushadi.
    """
    run_dir = D.prepare_run_dir(str(tmp_path / "run"))
    pf = FakePlatform(tmp_path)
    cfg = D.DriverConfig(run_dir=run_dir, seed=11, blocks=1,
                         only=("P1", "A"), allow_pressure=True,
                         sut_binary="/nonexistent/sut", memory_high="176M")
    drv = D.Driver(cfg, pf, sch.p1_schedule(11, n_blocks=1),
                   sch.TrialTimeline())
    setup = drv.setup_run()        # RAD ETILMAYDI -- bu hozirgi shart
    a = setup["dose_preflight"]["arithmetic"]["P1"]
    assert a["breach_expected"] is True        # shart bajarildi
    assert a["ramp_free_expected"] is False    # LEKIN ramp bepul emas
    # FAKT oqimda: operator buni run_meta'dan ko'radi.
    assert a["base_mb"] > a["memory_high_mib"]


def test_nol_doza_preflighti_HAQIQIY_memory_highdan_hisoblaydi(tmp_path):
    """Arifmetika slice'ga yuboriladigan qiymatdan, konstantadan EMAS."""
    drv, pf, run_dir = make_driver(tmp_path, only=("P1", "A"),
                                   allow_pressure=True)
    setup = drv.setup_run()
    dose = setup["dose_preflight"]
    assert dose["memory_high"] == setup["lab_slice_properties"]["MemoryHigh"]
    assert dose["levels_checked"] == ["P1"]
    a = dose["arithmetic"]["P1"]
    assert a["memory_high_mib"] == 192.0
    assert a["projected_memory_current_mb"] == pytest.approx(209.3)
    assert a["breach_expected"] is True


def test_memory_high_mib_systemd_1024_asosini_ishlatadi():
    assert D.memory_high_mib("192M") == 192.0
    assert D.memory_high_mib("2G") == 2048.0
    assert D.memory_high_mib("1024K") == 1.0
    assert D.memory_high_mib("201326592") == 192.0     # suffikssiz = BAYT
    with pytest.raises(D.DriverError):
        D.memory_high_mib("katta")


def test_pressure_dial_trial_recordida_ham_korinadi(tmp_path):
    """§2.5: nol doza chiqishda HECH QANDAY iz qoldirmasligi eng xavfli
    jihati edi. Dial `detail.pressure` da bo'lsa oqimdan KO'RINADI.
    """
    drv, pf, run_dir = make_driver(tmp_path, only=("P2", "A"),
                                   allow_pressure=True)
    drv.setup_run()
    detail = drv._start_pressure(drv.selected[0], "P2", 17.0)
    assert detail["step_mb"] == 4
    assert detail["base_mb"] == 184
    assert detail["target_rate"] == 0.60
    argv = pf.started[D.PRESS_UNIT]["ExecStart"]
    assert _flag_value(argv, "--step-mb") == "4"
    assert _flag_value(argv, "--base-mb") == "184"


def test_pressure_unit_WorkingDirectory_repo_root(tmp_path):
    """REGRESSIYA: generator unit'i `WorkingDirectory` siz edi.

    Guest'da O'LCHANDI (14-smoke-trial-natijalari.md §1): user manager
    unit'i `$HOME` da boshlanadi, `PYTHON*` muhiti yo'q, demak
    `python3 -m revix.pressure` -> `No module named 'revix'`, exit 1.
    """
    drv, pf, run_dir = make_driver(tmp_path, only=("P2", "A"),
                                   allow_pressure=True)
    drv.setup_run()
    drv._start_pressure(drv.selected[0], "P2", 17.0)
    props = pf.started[D.PRESS_UNIT]
    assert props["WorkingDirectory"] == drv.cfg.repo_root
    assert drv._pressure_properties(17.0)["WorkingDirectory"] == \
        drv.cfg.repo_root


def test_V2_generator_hold_start_minus_R_da_boshlanib_pressure_offda_chiqadi(
        tmp_path):
    """V2 (14 §10): generator `hold_start - R` da, `hold_s + R` ishlaydi.

    Avval generator ramp fazasi boshida (15 s) va 18 s ishlardi -- guard
    2/2 `P2` trial'ida `sustained_pressure` bilan trip qildi (14 §5).
    Frozen timeline O'ZGARMAYDI: injeksiya va `pressure_off` joyida.
    """
    drv, pf, run_dir = make_driver(tmp_path, only=("P2", "A"),
                                   allow_pressure=True)
    drv.run()
    tl = drv.timeline
    R = D.GENERATOR_OWN_RAMP_S
    assert R == 2.57
    recs = events(run_dir)
    t0 = of_type(recs, "trial_begin")[0]["mono_us"]
    start_rel = (pf.start_mono[D.PRESS_UNIT] - t0) / 1e6
    assert start_rel == pytest.approx(tl.t_hold_start - R, abs=1e-3)
    argv = pf.started[D.PRESS_UNIT]["ExecStart"]
    assert float(_flag_value(argv, "--max-seconds")) == pytest.approx(
        tl.hold_s + R, abs=1e-3)
    assert pf.started[D.PRESS_UNIT]["RuntimeMaxSec"] == \
        f"{int(tl.hold_s + R) + 2}s"
    # Injeksiya va pressure_off frozen joyida.
    fi = of_type(recs, "fault_inject")[0]
    assert (fi["mono_us_before_call"] - t0) / 1e6 >= tl.t_inject
    te = of_type(recs, "trial_end")[0]
    assert te["timing"]["pressure_off_mono_us"] - t0 == round(
        tl.t_pressure_off * 1e6)
    w = te["detail"]["pressure"]["window"]
    assert w["lead_s"] == R
    assert w["planned_stop_mono_us"] - w["planned_start_mono_us"] == round(
        (tl.hold_s + R) * 1e6)


def test_V2_run_meta_reja_va_haqiqiy_generator_oynasini_yozadi(tmp_path):
    """`run_meta.timeline` REJA (pressure_on_s = 18) bo'lib qoladi, yonida
    generatorning haqiqiy oynasi (15.57 s)."""
    drv, pf, run_dir = make_driver(tmp_path, only=("P2", "A"),
                                   allow_pressure=True)
    drv.run()
    meta = of_type(events(run_dir), "run_meta")[0]
    assert meta["timeline"] == sch.TrialTimeline().as_dict()
    assert meta["timeline"]["pressure_on_s"] == 18.0
    gw = meta["generator_window"]
    assert gw["planned_pressure_on_s"] == 18.0
    assert gw["generator_on_s"] == pytest.approx(15.57)
    assert gw["start_s"] == pytest.approx(17.43)
    assert gw["stop_s"] == 33.0
    assert "14-smoke-trial-natijalari.md" in gw["lead_source"]


def test_V2_lead_ramp_fazasidan_uzun_bolsa_run_boshlanmaydi():
    tl = sch.TrialTimeline()
    with pytest.raises(D.DriverError, match="ramp fazasi"):
        D.generator_window(tl, lead_s=tl.ramp_s + 0.01)
    with pytest.raises(D.DriverError):
        D.generator_window(tl, lead_s=-0.1)


def test_V2_planned_timeline_validatordan_otadi(tmp_path):
    """`check_planned_timeline` (frozen invariantlar) V2 dan keyin ham o'tadi."""
    V = _require_strict_validator()
    drv, pf, run_dir = make_driver(tmp_path, only=("P2", "A"),
                                   allow_pressure=True)
    drv.run()
    from revix import reduce as R
    run = R.RawRun(records=events(run_dir))
    assert V.check_planned_timeline(run) == []


def test_har_python_modul_unit_WorkingDirectory_bilan_ishga_tushadi(tmp_path):
    """`-m revix.<modul>` bilan boshlanadigan HAR unit repo root'da.

    Guard, psi_sampler, prober (`_mon_unit_properties`) va generator --
    to'liq trial davomida `start_transient` ga yuborilgan HAQIQIY property
    to'plami tekshiriladi, ya'ni yangi unit qo'shilsa ham qulf ishlaydi.
    """
    drv, pf, run_dir = make_driver(tmp_path, only=("P1", "A"),
                                   allow_pressure=True)
    drv.run()
    py_units = {name: props for name, props in pf.started.items()
                if "-m" in list(props.get("ExecStart") or [])}
    assert set(py_units) >= {D.GUARD_UNIT, D.PSI_UNIT, D.PROBER_UNIT,
                             D.PRESS_UNIT}, sorted(py_units)
    for name, props in py_units.items():
        assert props.get("WorkingDirectory") == drv.cfg.repo_root, name


# ===========================================================================
# --only filtri -- FAIL-CLOSED
# ===========================================================================


def test_only_filtri_kesishma_semantikasi():
    s = sch.p1_schedule(3, n_blocks=2)
    assert len(D.select_trials(s, ())) == 12
    assert len(D.select_trials(s, ("P0",))) == 4
    assert len(D.select_trials(s, ("P0", "A"))) == 2


def test_only_notogri_daraja_jim_bosh_run_bermaydi():
    s = sch.p1_schedule(3, n_blocks=2)
    with pytest.raises(D.OnlyFilterError, match="jadvalda yo'q"):
        D.select_trials(s, ("p0",))
    with pytest.raises(D.OnlyFilterError, match="mos kelmadi"):
        D.select_trials(s, ("P0", "P1"))


def test_only_jadval_digestini_ozgartirmaydi(tmp_path):
    s = sch.p1_schedule(3, n_blocks=2)
    before = s.digest()
    D.select_trials(s, ("P0", "A"))
    assert s.digest() == before


def test_parse_only():
    assert D.parse_only(None) == ()
    assert D.parse_only("") == ()
    assert D.parse_only("P0, A ,") == ("P0", "A")


# ===========================================================================
# Arm konfiguratsiyasi (§9.3)
# ===========================================================================


def test_P1_da_faqat_ikki_arm_baseline_B_YOQ():
    assert set(D.ARM_PROPERTIES) == {"A", "no_action"}
    assert D.arm_properties("A")["Restart"] == "on-failure"
    assert D.arm_properties("A")["RestartSec"] == "100ms"
    assert D.arm_properties("no_action")["Restart"] == "no"
    # `StartLimitBurst=0` IKKALA arm'da.
    assert D.arm_properties("A")["StartLimitBurst"] == 0
    assert D.arm_properties("no_action")["StartLimitBurst"] == 0
    with pytest.raises(D.DriverError, match="ATAYLAB yo'q"):
        D.arm_properties("B")


def test_restart_steps_juftligi_kodda_majburlanadi():
    # O'LCHANGAN TUZOQ: `RestartSteps=` `RestartMaxDelaySec=` siz QABUL
    # QILINADI va `systemctl show` uni ko'rsatadi, lekin systemd uni
    # E'TIBORSIZ qoldiradi. Read-back yolg'on gapiradi -> kodda tekshiriladi.
    with pytest.raises(D.DriverError, match="FAQAT JUFT"):
        D.check_restart_steps_pairing({"RestartSteps": 4})
    with pytest.raises(D.DriverError, match="FAQAT JUFT"):
        D.check_restart_steps_pairing({"RestartMaxDelaySec": "8s"})
    D.check_restart_steps_pairing({"RestartSteps": 4,
                                   "RestartMaxDelaySec": "8s"})
    D.check_restart_steps_pairing({})


def test_sut_va_bystander_lab_slicega_generator_ham(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    for unit in (D.SUT_UNIT, D.BYSTANDER_UNIT):
        assert pf.started[unit]["Slice"] == D.LAB_SLICE
    assert pf.started[D.PROBER_UNIT]["Slice"] == D.MON_SLICE
    assert pf.started[D.PSI_UNIT]["Slice"] == D.MON_SLICE


def test_sut_dial_lari_topologiya_bilan_mos(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    sut = pf.started[D.SUT_UNIT]
    assert sut["MemoryMax"] == "256M"
    assert sut["MemorySwapMax"] == 0
    assert sut["TasksMax"] == 64
    assert sut["Type"] == "notify"
    assert sut["WatchdogSec"]
    assert isinstance(sut["ExecStart"], list)      # argv shakli SHART
    by = pf.started[D.BYSTANDER_UNIT]
    assert by["MemoryMax"] == "128M"
    # Bystander HECH QACHON qayta ko'tarilmaydi -- u spillover detektori.
    assert by["Restart"] == "no"


def test_prober_har_trial_uchun_alohida_va_report_cost_bilan(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path, blocks=2)
    drv.run()
    starts = [n for k, n in pf.calls if k == "start"]
    assert starts.count(D.PROBER_UNIT) == 2       # har trial uchun bittadan
    argv = pf.started[D.PROBER_UNIT]["ExecStart"]
    assert "--trial-id" in argv
    assert argv[argv.index("--trial-id") + 1] == drv.selected[-1].trial_id
    # §8.2: probe narxi o'lchanadi va `prober_stop` orqali oqimga tushadi.
    assert "--report-cost" in argv
    # Ikki target: SUT va bystander (spillover detektori).
    assert argv.count("--target") == 2


def test_prober_SUT_active_bolgandan_KEYIN_ishga_tushadi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    starts = [n for k, n in pf.calls if k == "start"]
    # Prober SUT'dan OLDIN ishga tushsa, birinchi probe'lari conn_refused
    # bo'lib, `find_failure_onsets` SOXTA epizod yasardi va `reduce` ning
    # `vr` i (episodes[0].vr) fault epizodini EMAS, o'sha soxta epizodni
    # o'qib qolardi.
    assert starts.index(D.SUT_UNIT) < starts.index(D.PROBER_UNIT)
    assert starts.index(D.BYSTANDER_UNIT) < starts.index(D.SUT_UNIT)


def test_journaldga_hech_qanday_olchov_malumoti_oqmaydi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    for unit in (D.GUARD_UNIT, D.PSI_UNIT, D.PROBER_UNIT, D.SUT_UNIT,
                 D.BYSTANDER_UNIT):
        props = pf.started[unit]
        assert props["StandardOutput"] == "null"
        assert props["StandardError"] == "null"


# ===========================================================================
# Washout (§8.4)
# ===========================================================================


def test_washout_muzlatilgan_ketma_ketlikni_bajaradi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    e = of_type(events(run_dir), "trial_end")[0]
    w = e["washout"]
    assert w["kill_ok"] is True
    assert w["state"] == sch.WASHOUT_COMPLETE
    assert w["elapsed_s"] >= sch.T_W_S          # qattiq pol
    assert w["quiet_for_s"] >= sch.T_Q_S        # quiescence davomiyligi
    # Atomik subtree kill lab slice'ga qo'llanadi.
    assert any("revixlab.slice" in p for p in pf.killed)


def test_washout_memory_baseline_oqilmasa_fail_closed(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    pf.memory_current = lambda path: None
    w = drv._washout(drv.selected[0])
    assert w["timed_out"] is True
    assert w["reason"] == "memory_baseline_unreadable"


def test_washout_timeout_disposition_washout_timeout_beradi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv._washout = lambda trial: {"state": sch.WASHOUT_TIMEOUT,
                                  "timed_out": True, "observations": 3}
    drv.run()
    e = of_type(events(run_dir), "trial_end")[0]
    assert e["disposition"] == "washout_timeout"


def test_washout_kill_horizon_TUGAGANDAN_KEYIN(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    e = of_type(events(run_dir), "trial_end")[0]
    # Bizning O'Z `cgroup.kill` imiz o'lchov oynasi ICHIDA bo'lsa, u soxta
    # downtime (`compute_d_sd`) va soxta `down_at_horizon` berardi.
    assert pf.kill_mono_us
    assert min(pf.kill_mono_us) >= e["mono_us"]
    assert e["washout"]["observations"] > 0


# ===========================================================================
# Disposition faktlari (§12)
# ===========================================================================


def test_no_action_arm_horizon_down_bilan_tugaydi_va_censored(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path, only=("P0", "no_action"))
    drv.run()
    e = of_type(events(run_dir), "trial_end")[0]
    # `Restart=no` + clean crash -> horizon down holatda tugadi -> §6.2
    # bo'yicha `censored` (TASHLANMAYDI, KM/log-rank ga kiradi).
    assert e["facts"]["horizon_ended_down"] is True
    assert e["disposition"] == "censored"


def test_arm_A_restartdan_keyin_active_va_complete(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path, only=("P0", "A"))
    drv.run()
    e = of_type(events(run_dir), "trial_end")[0]
    assert e["facts"]["horizon_ended_down"] is False
    assert e["disposition"] == "complete"


def test_guard_hodisasi_trial_oynasida_aborted_guard_beradi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    orig = pf.sut_command

    def with_trip(socket_path, command, timeout_s=0.5):
        if command == "PROBE":
            return orig(socket_path, command, timeout_s)
        _append_jsonl(pf.guard_log_path, _guard_rec(
            "guard_event", pf.t, pf._gseq("guard_event"), pf.run_id, pf.session_id,
            reason="sustained_pressure", action="kill_subtree",
            detail={}, lab_cgroup="x", kill_ok=True))
        return orig(socket_path, command, timeout_s)

    pf.sut_command = with_trip
    drv.run()
    e = of_type(events(run_dir), "trial_end")[0]
    assert e["disposition"] == "aborted_guard"
    assert e["detail"]["facts"]["guard_events"]


def test_guard_hodisasi_oyna_tashqarisida_hisoblanmaydi(tmp_path):
    log = tmp_path / "g.jsonl"
    _append_jsonl(str(log), {"record_type": "guard_event", "mono_us": 50,
                             "reason": "x"})
    _append_jsonl(str(log), {"record_type": "guard_event", "mono_us": 500,
                             "reason": "y"})
    got = D.guard_events_in_window(str(log), 100, 400)
    assert got == []
    got2 = D.guard_events_in_window(str(log), 40, 400)
    assert [g["reason"] for g in got2] == ["x"]


def test_biz_yubormagan_sigkill_contaminated_deb_belgilanadi():
    assert D.unsolicited_kill_seen(
        {"exec_main_code": 2, "exec_main_status": 9}) is True
    # Clean crash (exit 1) kontaminatsiya EMAS -- u bizning fault'imiz.
    assert D.unsolicited_kill_seen(
        {"exec_main_code": 1, "exec_main_status": 1}) is False
    assert D.unsolicited_kill_seen({}) is False


def test_prober_horizongacha_tirik_qolmasa_censored(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    orig = pf.active_state

    def dead_prober(name):
        if name == D.PROBER_UNIT:
            return "failed"
        return orig(name)

    pf.active_state = dead_prober
    drv.run()
    e = of_type(events(run_dir), "trial_end")[0]
    # Instrumentatsiya yo'qolishi HECH QACHON `failed` emas -> `censored` (§4).
    assert e["facts"]["probe_gap_exceeded"] is True
    assert e["disposition"] == "censored"


def test_bystander_oom_kill_contaminated_beradi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    calls = {"n": 0}

    def events_fn(path):
        calls["n"] += 1
        if D.BYSTANDER_UNIT in path and calls["n"] > 6:
            return {"oom_kill": 1}
        return {"oom_kill": 0}

    pf.memory_events = events_fn
    drv.run()
    e = of_type(events(run_dir), "trial_end")[0]
    assert e["facts"]["bystander_lost_contract"] is True
    assert e["disposition"] == "contaminated"


def test_cheklangan_cgroupdagi_oom_kill_kontaminatsiya_EMAS(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    # Global oom_kill o'sdi, lekin lab'ning O'Z o'sishi bilan BIR XIL ->
    # ya'ni OOM biz cheklagan cgroup'da bo'ldi -> kutilgan natija.
    seq = {"n": 0}

    def vm():
        seq["n"] += 1
        return {"oom_kill": 0 if seq["n"] <= 1 else 1}

    def ev(path):
        if path.endswith(D.LAB_SLICE):
            return {"oom_kill": 0 if seq["n"] <= 1 else 1}
        return {"oom_kill": 0}

    pf.vmstat = vm
    pf.memory_events = ev
    drv.run()
    e = of_type(events(run_dir), "trial_end")[0]
    assert e["facts"]["foreign_oom_kill"] is False


# ===========================================================================
# CLI -- MUZLATILGAN interfeys
# ===========================================================================


def test_main_imzosi_va_bayroqlari():
    p = D.build_parser()
    opts = {a.dest for a in p._actions}
    for dest in ("run_dir", "seed", "blocks", "only", "dry_run", "json"):
        assert dest in opts
    # `revix run` AYNAN shu argv ni quradi.
    args = p.parse_args(["--run-dir", "/x", "--seed", "0", "--blocks", "0",
                         "--only", "P0", "--dry-run", "--json"])
    assert args.seed == 0 and args.blocks == 0
    assert args.dry_run is True and args.json is True


def test_blocks_defaulti_P1_dizayni():
    args = D.build_parser().parse_args(["--run-dir", "/x", "--seed", "1"])
    assert args.blocks == sch.P1_BLOCKS == 20


def test_main_json_bayrogi_bilan_xatoni_JSON_qaytaradi(tmp_path, capsys):
    rc = D.main(["--run-dir", str(tmp_path / "r"), "--seed", "1",
                 "--blocks", "0", "--json"])
    assert rc == 2
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert out["error_type"] == "ScheduleError"


def test_main_dry_run_json_siz_ham_ishlaydi(tmp_path, capsys):
    rc = D.main(["--run-dir", str(tmp_path / "r"), "--seed", "2",
                 "--blocks", "1", "--only", "P0,A", "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "HECH NARSA ISHGA TUSHIRILMADI" in out
    assert f"T_trial={D.t_trial_us(sch.TrialTimeline()) / 1e6:.3f} s" in out


# ===========================================================================
# Run katalogi tuzilishi
# ===========================================================================


def test_run_katalogi_fayl_nomlari_qatiy():
    assert D.RUN_FILES == ("events.jsonl", "probe.csv", "psi.csv",
                           "guard.jsonl", "pressure.jsonl", "run_meta.json")


def test_har_oqim_oz_fayliga_yoziladi(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    assert drv.events_path.endswith(D.EVENTS_FILE)
    assert drv.probe_path.endswith(D.PROBE_FILE)
    assert drv.psi_path.endswith(D.PSI_FILE)
    assert drv.guard_path.endswith(D.GUARD_FILE)
    assert drv.pressure_path.endswith(D.PRESSURE_FILE)
    # Prober va psi_sampler AYNAN shu yo'llarga yozishi uchun argv'da
    # ko'rsatiladi.
    assert drv.probe_path in pf.started[D.PROBER_UNIT]["ExecStart"]
    assert drv.psi_path in pf.started[D.PSI_UNIT]["ExecStart"]
    assert drv.guard_path in pf.started[D.GUARD_UNIT]["ExecStart"]


def test_trial_hodisalari_ketma_ketligi_shartnoma_1_2_boyicha(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    # Prober record'lari ATAYLAB `trial_begin` dan OLDIN: per-trial prober
    # jarayoni setup fazasida ishga tushadi (record oynasidan tashqarida).
    order = [r["record_type"] for r in events(run_dir)
             if r["record_type"] not in ("run_meta", "unit_state",
                                         "harness_error", "prober_start",
                                         "prober_stop")]
    assert order[0] == "trial_begin"
    assert order[-1] == "trial_end"
    for rt in ("env_snapshot", "baseline_window", "fault_inject",
               "cgroup_events"):
        assert rt in order, rt
    assert order.index("baseline_window") < order.index("fault_inject")
    assert order.index("fault_inject") < order.index("trial_end")


# ===========================================================================
# PSI sirkulyarlik ta'qiqi (CONTRIBUTING.md §1.5)
# ===========================================================================


def test_driver_VR_va_FR_tariflarini_CHAQIRMAYDI():
    """PSI failure, VR yoki FR ta'rifiga KIRMAYDI (CONTRIBUTING.md §1.5).

    Tekshiruv AST ustida, MATN ustida emas: bu nomlar docstring'larda izoh
    sifatida uchraydi, va matn qidiruvi o'sha izohlarga yiqilardi -- ya'ni
    test o'zining hujjatidan qo'rqib yolg'on signal berardi.
    """
    import ast
    src = open(os.path.join(os.path.dirname(D.__file__), "driver.py"),
               encoding="utf-8").read()
    tree = ast.parse(src)
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                called.add(f.id)
            elif isinstance(f, ast.Attribute):
                called.add(f.attr)
    for forbidden in ("evaluate_vr", "fr_a", "evaluate_fr_b",
                      "window_throughput", "reduce_trial", "build_episodes"):
        assert forbidden not in called, forbidden
    # `reduce` MODUL DARAJASIDA import QILINMAYDI: ta'riflar o'lchovdan
    # KEYIN va o'lchovdan TASHQARIDA qolishi kerak.
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
    assert "reduce" not in imported
    # `TrialFacts` da PSI ga tegishli fakt YO'Q.
    assert not any("psi" in f or "stall" in f for f in sch.FACT_FIELDS)


def test_washout_tezligi_faqat_2s_dan_katta_oynadan():
    # <2 s oyna ONIY TEZLIK EMAS: `stall_fraction` None qaytaradi va biz
    # uni SHUNDAY qoldiramiz (fail-closed -> tinch deb hisoblanmaydi).
    from revix import cgroup as cg
    assert cg.stall_fraction(0, 100, 0, 1_000_000) is None
    assert D.WASHOUT_RATE_WINDOW_US >= 2_000_000


# ===========================================================================
# Oxirgi tekshiruv -- hech qanday qoldiq yo'q
# ===========================================================================


def test_zzz_hech_qanday_selftest_qoldigi_qolmadi():
    """Bu modul HECH QANDAY unit yaratmaydi -- shuni tasdiqlaydi.

    `user_bus_reason()` bo'lsa tekshiruv o'tkazib yuboriladi, lekin SABABI
    ko'rinadi: "o'tdi" va "umuman ishlamadi" bir xil ko'rinmasligi kerak.
    """
    reason = U.user_bus_reason()
    if reason is not None:
        pytest.skip(f"user D-Bus yo'q: {reason}")
    sd = U.SystemdUser(connect_signals=False)
    try:
        assert sd.list_units(SELFTEST_GLOB) == []
        assert sd.list_units(SELFTEST_SLICE) == []
        assert U.list_runtime_drop_ins([SELFTEST_GLOB, SELFTEST_SLICE]) == []
    finally:
        sd.close()


# ===========================================================================
# Reducer kirishi -- SUT'ga FILTRLANADI (bystander korruptsiyasining qulfi)
# ===========================================================================


def test_reducer_kirishi_bystander_probelarini_chiqaradi():
    rows = [
        {"target": "sut", "progress_counter": "10", "mono_us_send": "100",
         "outcome": "ok", "trial_id": "t0"},
        {"target": "bystander", "progress_counter": "999",
         "mono_us_send": "101", "outcome": "ok", "trial_id": "t0"},
    ]
    _, probes = D.reducer_input([], rows)
    assert [p["target"] for p in probes] == ["sut"]
    # Filtr TEKSHIRILADIGAN: `target` ustuni qatorda QOLADI.
    assert probes[0]["target"] == "sut"
    # Nom moslashuvi ham shu yerda bajariladi.
    assert probes[0]["progress"] == "10"


def test_reducer_kirishi_bystander_unit_statelarini_chiqaradi():
    recs = [
        {"record_type": "unit_state", "unit": D.SUT_UNIT, "n_restarts": 1},
        {"record_type": "unit_state", "unit": D.BYSTANDER_UNIT,
         "n_restarts": 7},
        {"record_type": "trial_begin", "arm": "A"},
    ]
    out, _ = D.reducer_input(recs, [])
    units = [r.get("unit") for r in out if r["record_type"] == "unit_state"]
    assert units == [D.SUT_UNIT]
    # Boshqa record turlari TEGILMAYDI.
    assert any(r["record_type"] == "trial_begin" for r in out)


def test_reducer_kirishi_target_ustuni_bolmagan_qatorni_tashlamaydi():
    # Ustun yo'q bo'lsa jimgina tashlash MA'LUMOT YO'QOTISH bo'lardi;
    # faqat ANIQ boshqa target chiqariladi.
    _, probes = D.reducer_input([], [{"progress_counter": "5"}])
    assert len(probes) == 1


def test_reducer_kirishi_xom_oqimni_OZGARTIRMAYDI(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)
    drv.run()
    raw = events(run_dir)
    before = len(raw)
    out, _ = D.reducer_input(raw, [])
    # Xom ro'yxat joyida o'zgarmaydi: `datasets/` append-only.
    assert len(raw) == before
    # Bystander'ning `unit_state` lari XOM oqimda QOLADI -- ular §12 ning
    # `contaminated` disposition'i uchun DALIL.
    assert any(r.get("unit") == D.BYSTANDER_UNIT for r in raw
               if r["record_type"] == "unit_state")
    assert not any(r.get("unit") == D.BYSTANDER_UNIT for r in out
                   if r["record_type"] == "unit_state")


def test_reducer_kirishi_bilan_R_ref_hisoblanadi():
    """Filtrsiz bystander progress'i SUT'ning throughput qatoriga tushardi."""
    from revix import reduce as R
    rows = [
        {"target": "sut", "trial_id": "t0", "mono_us_send": "1000000",
         "outcome": "ok", "progress_counter": "100",
         "invocation_id_seen": "a"},
        {"target": "bystander", "trial_id": "t0", "mono_us_send": "1050000",
         "outcome": "ok", "progress_counter": "900000",
         "invocation_id_seen": "b"},
        {"target": "sut", "trial_id": "t0", "mono_us_send": "2000000",
         "outcome": "ok", "progress_counter": "2100",
         "invocation_id_seen": "a"},
    ]
    _, probes = D.reducer_input([], rows)
    objs = [R.probe_from_record(p) for p in probes]
    thr, status, _ = R.window_throughput(objs, 0, 10_000_000)
    assert status == "ok"
    # 2000 iteratsiya / 1 s = 2000 iter/s (SUT'ning REAL tezligi).
    assert thr == pytest.approx(2000.0)


def test_action_chiqish_dalilisiz_yozilmaydi(tmp_path):
    """Invocation o'zgardi, lekin `active` dan chiqish KUZATILMADI.

    Bu "restart" emas, kuzatuvdagi bo'shliq. Dalilsiz `action` yozish
    `validate.check_actions` ni yiqitardi (action vaqti yangi record'ning
    vaqtiga teng bo'lib qolardi).
    """
    drv, pf, run_dir = make_driver(tmp_path)
    trial = drv.selected[0]
    state = drv._sut_state
    state["invocation"] = "inv_old"
    payload = {"active_state": "active", "invocation_id": "inv_new",
               "recv_mono_us": 5_000, "n_restarts": 1,
               "active_exit_ts_mono_us": None,
               "exec_main_exit_ts_mono_us": None}
    drv._note_unit_state(trial, D.SCOPE_SUT, payload)
    assert of_type(events(run_dir), "action") == []
    assert "invocation_changed_without_observed_exit" in state["anomalies"]


# ===========================================================================
# Istisno yo'li: guard trip -> aborted_guard, washout HAR yo'lda (14 §11.4)
# ===========================================================================


def _trip_guard_at_rel(drv, pf, rel_s):
    """Birinchi trial boshidan `rel_s` s da guard trip qiladi (fake)."""
    orig = drv._emit_trial_begin
    seen = []

    def _begin(trial, index, arm, level, mono):
        if not seen:
            pf.guard_trip_at_us = mono + round(rel_s * 1e6)
        seen.append(trial.trial_id)
        return orig(trial, index, arm, level, mono)

    drv._emit_trial_begin = _begin


def _assert_washout_ran(pf, run_dir, n_trials):
    ends = of_type(events(run_dir), "trial_end")
    assert len(ends) == n_trials
    for te in ends:
        assert te["washout"]["state"] is not None, te["washout"]
        assert te["timing"]["washout_us"] > 0
    lab = pf.cgroup_path(D.LAB_SLICE)
    assert pf.killed.count(lab) >= n_trials        # har trial'da cgroup.kill


def test_guard_injeksiyadan_OLDIN_trip_injeksiya_qilinmaydi_aborted_guard(
        tmp_path):
    """smoke-13 holati: guard 22.5 s da, injeksiya 23.0 s da edi."""
    V = _require_strict_validator()
    drv, pf, run_dir = make_driver(tmp_path, only=("P2", "no_action"),
                                   allow_pressure=True)
    _trip_guard_at_rel(drv, pf, 22.5)
    summary = drv.run()
    assert [t["disposition"] for t in summary["trials"]] == ["aborted_guard"]
    recs = events(run_dir)
    assert of_type(recs, "fault_inject") == []           # injeksiya YO'Q
    assert not any(c == ("fault", "FAULT exit code=1") for c in pf.calls)
    te = of_type(recs, "trial_end")[0]
    f = te["detail"]["fault"]
    assert f["skipped"] is True
    assert f["reason"] == "guard_fired_before_injection"
    assert f["guard_events"][0]["reason"] == "user_full_rate2s_runaway"
    assert of_type(recs, "harness_error") == []
    _assert_washout_ran(pf, run_dir, 1)
    rep = V.validate_run_dir(run_dir, run_mode="pilot",
                             sut_unit=D.SUT_UNIT, sut_target="sut")
    assert not rep.errors, [str(x) for x in rep.errors]


def test_guard_injeksiya_paytida_trip_istisno_aborted_guard_bolib_qoladi(
        tmp_path):
    """Poyga: guard oldindan tekshiruvdan KEYIN, FAULT dan OLDIN ishlaydi
    -> FAULT ConnectionRefused -> DriverError. Disposition `aborted_guard`
    (§12), `harness_error` emas; istisno trial_end'da yoziladi."""
    V = _require_strict_validator()
    drv, pf, run_dir = make_driver(tmp_path, only=("P2", "no_action"),
                                   allow_pressure=True)
    pf.guard_trip_on_probe = True
    summary = drv.run()
    assert [t["disposition"] for t in summary["trials"]] == ["aborted_guard"]
    recs = events(run_dir)
    te = of_type(recs, "trial_end")[0]
    x = te["detail"]["exception_after_guard_trip"]
    assert x["classified_as"] == "consequence_of_guard_trip"
    assert "fault ack" in x["error"]
    assert te["facts"]["guard_fired"] is True
    assert te["facts"]["harness_error"] is False
    assert of_type(recs, "harness_error") == []
    _assert_washout_ran(pf, run_dir, 1)
    rep = V.validate_run_dir(run_dir, run_mode="pilot",
                             sut_unit=D.SUT_UNIT, sut_target="sut")
    assert not rep.errors, [str(x) for x in rep.errors]


def test_guard_injeksiyadan_KEYIN_trip_aborted_guard_va_washout(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path, only=("P2", "A"),
                                   allow_pressure=True)
    _trip_guard_at_rel(drv, pf, 30.0)
    summary = drv.run()
    assert [t["disposition"] for t in summary["trials"]] == ["aborted_guard"]
    recs = events(run_dir)
    assert len(of_type(recs, "fault_inject")) == 1        # injeksiya bo'ldi
    _assert_washout_ran(pf, run_dir, 1)


def test_haqiqiy_harness_xatosi_guardsiz_harness_error_qoladi_washout_bilan(
        tmp_path):
    """Guard ishlamagan: SUT o'zi javob bermaydi -> `harness_error`."""
    drv, pf, run_dir = make_driver(tmp_path, only=("P2", "no_action"),
                                   allow_pressure=True)
    pf.sut_dead_no_guard = True
    summary = drv.run()
    assert [t["disposition"] for t in summary["trials"]] == ["harness_error"]
    recs = events(run_dir)
    assert len(of_type(recs, "harness_error")) == 1
    te = of_type(recs, "trial_end")[0]
    assert "exception_after_guard_trip" not in te["detail"]
    _assert_washout_ran(pf, run_dir, 1)


def test_istisnodan_keyin_keyingi_trial_toza_boshlanadi(tmp_path):
    """Ikki trial: birinchisida guard injeksiyadan oldin; ikkinchisi
    oldingisining washout'i va prober to'xtatilishidan KEYIN boshlanadi."""
    V = _require_strict_validator()
    drv, pf, run_dir = make_driver(tmp_path, only=("P0", "no_action"),
                                   blocks=2, allow_pressure=True)
    _trip_guard_at_rel(drv, pf, 22.5)
    summary = drv.run()
    disp = [t["disposition"] for t in summary["trials"]]
    assert disp[0] == "aborted_guard" and disp[1] != "aborted_guard", disp
    assert disp[1] in ("censored", "complete")
    _assert_washout_ran(pf, run_dir, 2)
    # Ikkinchi prober start'idan oldin birinchisi to'xtatilgan va lab kill.
    starts = [i for i, c in enumerate(pf.calls) if c == ("start", D.PROBER_UNIT)]
    stops = [i for i, c in enumerate(pf.calls) if c == ("stop", D.PROBER_UNIT)]
    kills = [i for i, c in enumerate(pf.calls)
             if c == ("kill", pf.cgroup_path(D.LAB_SLICE))]
    assert len(starts) == 2
    assert any(starts[0] < s < starts[1] for s in stops)
    assert any(starts[0] < k < starts[1] for k in kills)
    rep = V.validate_run_dir(run_dir, run_mode="pilot",
                             sut_unit=D.SUT_UNIT, sut_target="sut")
    assert not rep.errors, [str(x) for x in rep.errors]


def test_washout_ozi_yiqilsa_washout_timeout(tmp_path):
    drv, pf, run_dir = make_driver(tmp_path)

    def boom(path):
        raise OSError("memory.current o'qilmadi")
    pf.memory_current = boom
    summary = drv.run()
    assert [t["disposition"] for t in summary["trials"]] == ["washout_timeout"]
    te = of_type(events(run_dir), "trial_end")[0]
    assert te["washout"]["timed_out"] is True
    assert "washout_exception" in te["washout"]["reason"]


@pytest.mark.parametrize("mode", ["guard_on_probe", "dead_no_guard"])
def test_istisno_yolida_generator_washoutdan_OLDIN_toxtatiladi(tmp_path, mode):
    """REGRESSIYA (smoke-18, 14 §12.2): istisno pressure_off dan OLDIN --
    generator tirik edi, washout baseline'i 169.4 MiB bilan o'qildi va
    120 s cap'da `washout_timeout` bo'ldi. Generator kill'dan OLDIN
    to'xtatilishi SHART."""
    drv, pf, run_dir = make_driver(tmp_path, only=("P2", "no_action"),
                                   allow_pressure=True)
    setattr(pf, "guard_trip_on_probe" if mode == "guard_on_probe"
            else "sut_dead_no_guard", True)
    drv.run()
    i_stop = pf.calls.index(("stop", D.PRESS_UNIT))
    i_kill = pf.calls.index(("kill", pf.cgroup_path(D.LAB_SLICE)))
    assert i_stop < i_kill, pf.calls
    te = of_type(events(run_dir), "trial_end")[0]
    assert te["detail"]["pressure"]["stopped_early_mono_us"] > 0
    assert te["washout"]["state"] == "complete"


# ===========================================================================
# §16.10 muzlatilgan qiymatlar run_meta'da (v1.12, 1-band; preshart 3)
# ===========================================================================


def _open_params(tmp_path, **cfg_kw):
    run_dir = D.prepare_run_dir(str(tmp_path / "run"))
    pf = FakePlatform(tmp_path)
    cfg = D.DriverConfig(run_dir=run_dir, seed=11, blocks=1, only=("P0", "A"),
                         sut_binary="/nonexistent/sut", **cfg_kw)
    drv = D.Driver(cfg, pf, sch.p1_schedule(11, n_blocks=1),
                   sch.TrialTimeline())
    drv.run()
    meta = json.load(open(os.path.join(run_dir, D.RUN_META_FILE),
                          encoding="utf-8"))
    return meta["open_parameters"], meta


def test_open_parameters_muzlatilgan_qiymatlar_va_run_idlar(tmp_path):
    op, meta = _open_params(tmp_path)
    wd = op["watchdog_sec"]
    assert (wd["value"], wd["frozen_value"], wd["matches_frozen"]) == (
        "5s", "5s", True)
    # A qism FAQAT cal-01 va cal-02 (cal-03 -- faqat B).
    assert wd["calibration"]["run_ids"] == ["open-params-cal-01",
                                            "open-params-cal-02"]
    assert "open-params-cal-03" not in wd["calibration"]["run_ids"]
    c = wd["calibration"]
    assert (c["M_wd_delta_s"], c["max_gap_s"], c["halfW_over_M_wd"]) == (
        0.1170, 2.6170, 21.38)
    assert c["episodes"] == {"P0": 24, "P1": 24, "P2": 24}
    assert c["result_watchdog"] == 0 and c["F"] == 3
    assert "13-ochiq-parametrlar-kalibratsiyasi.md" in wd["source"]
    assert "5 s" in wd["mechanism_statement"]

    mh = op["memory_high"]
    assert (mh["value"], mh["frozen_value"], mh["matches_frozen"]) == (
        "192M", "192M", True)
    assert mh["calibration"]["run_ids"] == ["dose-01-dial", "dose-02-bands",
                                            "dose-03-p2sweep"]
    assert mh["calibration"]["reproduced_in"] == [
        "open-params-cal-01", "open-params-cal-02", "open-params-cal-03"]
    assert "10-pressure-dozalash.md §2.2" in mh["source"]
    assert "13-ochiq-parametrlar-kalibratsiyasi.md §4" in mh["source"]
    assert "OQ-11" in mh["limitation"]          # cheklov KO'RINADI

    tt = op["t_trial_s"]
    assert tt["frozen_value"] == 41.1 and tt["matches_frozen"] is True
    assert meta["t_trial_us"] == 41_100_000


def test_open_parameters_timeout_start_sec_KALIBRLANGAN_deb_korinmaydi(
        tmp_path):
    """v1.12 1.3: qoida TAKLIF BERMAGAN (24/24/20 < 48). run_meta'ning
    o'zini o'qigan odam buni kalibrlangan qiymat deb O'YLAMASLIGI kerak."""
    op, _ = _open_params(tmp_path)
    ts = op["timeout_start_sec"]
    assert ts["value"] == "10s" and ts["frozen_value"] == "10s"
    assert ts["rule_satisfied"] is False
    assert ts["frozen_as"] == "pre_data_default_documented_deviation"
    assert "1.3-band" in ts["deviation"]
    assert "TAKLIF BERMAGAN" in ts["deviation"]
    assert "KALIBRLANGAN qiymat EMAS" in ts["deviation"]
    c = ts["calibration"]
    assert c["run_ids"] == ["open-params-cal-02", "open-params-cal-03"]
    assert c["qualifying_starts"] == {"P0": 24, "P1": 24, "P2": 20}
    assert c["required_per_band"] == 48
    assert c["rule_proposal"] is None
    assert (c["M_start_s"], c["timeout_over_max"], c["result_timeout"]) == (
        0.9614, 10.40, 0)
    tails = {t["max_t_start_s"]: t["timeout_over_max"]
             for t in c["other_observed_tails"]}
    assert tails == {1.7030: 5.87, 1.4807: 6.75}


def test_open_parameters_flag_muzlatilgandan_farq_qilsa_KORINADI(tmp_path):
    op, _ = _open_params(tmp_path, watchdog_sec="7s",
                         timeout_start_sec="20s")
    assert op["watchdog_sec"]["value"] == "7s"
    assert op["watchdog_sec"]["matches_frozen"] is False
    assert op["timeout_start_sec"]["matches_frozen"] is False
    assert op["memory_high"]["matches_frozen"] is True


def test_open_parameters_hech_qaysi_kalibrlangan_parametr_rule_satisfied_siz_emas(
        tmp_path):
    """`calibration_required: False` bo'lgan §16.10 yozuvlarining har biri
    `rule_satisfied` ni OSHKORA beradi -- jim default yo'q."""
    op, _ = _open_params(tmp_path)
    for key in ("memory_high", "watchdog_sec", "timeout_start_sec",
                "t_trial_s"):
        assert isinstance(op[key]["rule_satisfied"], bool), key
        assert op[key]["frozen_in"] == D.PREREG_FROZEN_IN
