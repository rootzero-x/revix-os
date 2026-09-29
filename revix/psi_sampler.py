"""PSI namuna oluvchi -- bir necha scope'ni 10 Hz da o'qiydi.

PREREGISTRATION.md §7 ni amalga oshiradi:
  * 4 scope x 3 resurs x {some, full}
  * `total=` asosiy o'lchov; avgN ham yoziladi (ikkilamchi)
  * HAR SCOPE UCHUN ALOHIDA o'qish timestamp'i -- turli scope'lar turli vaqtda
    o'qiladi va ularni bir vaqtda deb ko'rsatish xato bo'lardi
  * fd bir marta ochiladi, har namunada pread(fd, 0)

Bu jarayon revixmon.slice da ishlaydi -- kovariata sifatida ishlatiladigan
hech bir scope ichida emas (PREREGISTRATION.md §8.2).
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
import time

from . import cgroup as cg
from .schema import CsvWriter, Emitter, JsonlWriter, mono_us, new_run_id


def build_fields(scopes: list[str]) -> list[str]:
    f = ["mono_us", "real_us", "seq", "trial_id"]
    for s in scopes:
        f.append(f"{s}__read_mono_us")
        for res in cg.PSI_RESOURCES:
            for kind in ("some", "full"):
                f.append(f"{s}__{res}_{kind}_total")
                f.append(f"{s}__{res}_{kind}_avg10")
        # cgroup scope'lari uchun qo'shimcha o'lchovlar
        f.append(f"{s}__memory_current")
        f.append(f"{s}__memory_swap_current")
    return f


class Sampler:
    def __init__(self, scopes: dict[str, str], csv: CsvWriter, events: JsonlWriter | None,
                 emitter: Emitter) -> None:
        self.scopes = scopes
        self.csv = csv
        self.events = events
        self.emitter = emitter
        self._files: dict[tuple[str, str], cg.PsiFile] = {}
        self._stop = False
        self.trial_id: str | None = None

    def open_all(self) -> None:
        for name, path in self.scopes.items():
            for res in cg.PSI_RESOURCES:
                p = f"{path}/{res}.pressure" if not path.startswith("/proc") else f"{path}/{res}"
                try:
                    self._files[(name, res)] = cg.PsiFile(p)
                except OSError:
                    # Yo'q scope jimgina tashlanmaydi: bo'sh maydon sifatida
                    # yoziladi va shu holat hodisa sifatida qayd etiladi.
                    if self.events is not None:
                        self.events.write(self.emitter.record(
                            "psi_scope_unavailable", {"scope": name, "resource": res, "path": p},
                            stream="psi_scope_unavailable"))

    def sample_once(self) -> dict:
        row: dict = {"mono_us": mono_us(), "real_us": None,
                     "seq": self.emitter.next_seq("psi_sample"),
                     "trial_id": self.trial_id}
        from .schema import real_us
        row["real_us"] = real_us()
        for name, path in self.scopes.items():
            read_t = None
            for res in cg.PSI_RESOURCES:
                pf = self._files.get((name, res))
                if pf is None:
                    continue
                try:
                    t, psi = pf.sample()
                except (OSError, ValueError):
                    continue
                if read_t is None:
                    read_t = t
                for kind in ("some", "full"):
                    d = psi.get(kind)
                    if d is None:
                        continue
                    row[f"{name}__{res}_{kind}_total"] = d["total"]
                    row[f"{name}__{res}_{kind}_avg10"] = d["avg10"]
            row[f"{name}__read_mono_us"] = read_t
            if not path.startswith("/proc"):
                row[f"{name}__memory_current"] = cg.read_int(f"{path}/memory.current")
                row[f"{name}__memory_swap_current"] = cg.read_int(f"{path}/memory.swap.current")
        return row

    def run(self, hz: float, max_seconds: float | None) -> int:
        signal.signal(signal.SIGTERM, self._on_sig)
        signal.signal(signal.SIGINT, self._on_sig)
        self.open_all()
        if self.events is not None:
            self.events.write(self.emitter.record(
                "sampler_start", {"scopes": self.scopes, "hz": hz,
                                  "own_cgroup": cg.own_cgroup(), "pid": os.getpid()},
                stream="sampler_start"))
        period = 1.0 / hz
        start = time.monotonic()
        # Absolut deadline: sleep(period) drift yig'adi.
        nxt = time.monotonic()
        n = 0
        try:
            while not self._stop:
                if max_seconds is not None and time.monotonic() - start >= max_seconds:
                    break
                self.csv.write(self.sample_once())
                n += 1
                nxt += period
                d = nxt - time.monotonic()
                if d > 0:
                    time.sleep(d)
                else:
                    nxt = time.monotonic()
        finally:
            for pf in self._files.values():
                pf.close()
            self.csv.close()
            if self.events is not None:
                self.events.write(self.emitter.record(
                    "sampler_stop", {"samples": n, "elapsed_s": time.monotonic() - start},
                    stream="sampler_stop"))
                self.events.flush()
        return 0

    def _on_sig(self, _s: int, _f: object) -> None:
        self._stop = True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="REVIX PSI namuna oluvchi")
    ap.add_argument("--scope", action="append", default=[], metavar="NOM=YOL",
                    help="takrorlanadi; masalan lab=/sys/fs/cgroup/.../revixlab.slice")
    ap.add_argument("--with-host", action="store_true", help="host=/proc/pressure qo'shadi")
    ap.add_argument("--with-user", action="store_true", help="user=user@UID.service qo'shadi")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--events", default=None)
    ap.add_argument("--hz", type=float, default=10.0)
    ap.add_argument("--max-seconds", type=float, default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--session-id", default="adhoc")
    args = ap.parse_args(argv)

    scopes: dict[str, str] = {}
    if args.with_host:
        scopes["host"] = "/proc/pressure"
    if args.with_user:
        scopes["user"] = cg.user_service_cgroup()
    for s in args.scope:
        name, _, path = s.partition("=")
        if not path:
            ap.error(f"--scope NOM=YOL formatida bo'lishi kerak: {s!r}")
        scopes[name] = path
    if not scopes:
        ap.error("kamida bitta scope kerak")

    fields = build_fields(list(scopes))
    csv = CsvWriter(args.csv, fields)
    events = JsonlWriter(args.events) if args.events else None
    em = Emitter("psi_sampler", args.run_id or new_run_id(), args.session_id)
    try:
        return Sampler(scopes, csv, events, em).run(args.hz, args.max_seconds)
    finally:
        if events:
            events.close()


if __name__ == "__main__":
    sys.exit(main())
