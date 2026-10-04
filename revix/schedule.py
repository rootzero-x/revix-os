"""Eksperiment dizayni -- randomizatsiya, washout, disposition, trial jadvali.

PREREGISTRATION.md ni amalga oshiradi:
  * §8.4 -- randomized complete block design va washout ketma-ketligi;
  * §9.3 -- faktorlar va arm'lar (P1);
  * §9.4 -- pressure dosing va trial jadvali;
  * §12  -- yopiq disposition enum;
  * §6.2 -- o'ngdan censoring (censored trial TASHLANMAYDI).

DIZAYN QOIDASI (buzilmaydi): bu modul SOF MANTIQ, NOL IO.
Hech qanday systemd, cgroup, socket, fayl, `time.sleep` yoki soat o'qishi yo'q.

Sabab: REVIX ning ilmiy hissasi o'lchov, ya'ni eksperiment DIZAYNI --
mahsulotning o'zi. Dizaynda jimgina xato butun kampaniyani qiymatsiz qiladi,
demak dizayn to'liq va arzon test qilinadigan bo'lishi kerak. Agar bu modul
mashinaning holatini o'qisa, uni faqat shu mashinada, faqat shu holatda
sinab ko'rish mumkin bo'lardi. Shuning uchun BAJARISH alohida modulda:
bu modul faqat NIMA qilinishi kerakligini hisoblaydi, hech narsa qilmaydi.

Washout nima uchun `total=` dan olingan INTERVAL tezliklarini ishlatadi
(`avgN` emas) -- ko'ring `WashoutPolicy`. Qisqasi: bu o'lchov qarori
washout'ni ~300 s dan 15 s ga tushiradi, ya'ni kampaniya vaqtidan bir
daraja.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import random
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from .schema import DISPOSITIONS

SCHEDULE_VERSION = 1

# RNG nomi jadvalga yoziladi: takrorlanuvchanlik SEED va ALGORITM juftligiga
# bog'liq, faqat seed'ga emas. Algoritm o'zgarsa digest o'zgaradi va bu
# aniqlanadi -- jimgina boshqa randomizatsiya bo'lib qolmaydi.
RNG_NAME = "python-random-mt19937"

# --- muzlatilgan vaqt konstantalari -----------------------------------------
# Har birining yonida uni muzlatgan bo'lim turadi. Bu qiymatlar shu yerda
# QAYTA ta'riflanmaydi -- faqat ko'chiriladi.

R_REF_BASELINE_S = 10.0        # §9.4 -- fault'dan oldingi throughput o'lchovi
RAMP_S = 5.0                   # §9.4 -- PI controller nishonga chiqadi
# §9.4 invariant 1. PREREGISTRATION.md §17.5 ning O3 variantiga ko'ra
# **12.0 -> 13.0** (v1.11 amendment; qaror loyiha egasiniki, §17.5 ni ko'ring).
#
# NEGA 12 YETMADI. §17.2 ning arifmetikasi:
#     0.1 (RestartSec) + t_start + 0.1 (probe kvantlashi)
#         <= hold_cap_s - (injection_offset 3 + W_stab 8)
# 12 s da bu `t_start <= 0.8 s` beradi. Kalibrlangan dozada O'LCHANGAN
# `p90(t_start)`: `P0` 0.0481 s, `P2` 0.7863 s, lekin **`P1` 0.9543 s** --
# budjetdan 19.3% KATTA (docs/architecture/10-pressure-dozalash.md §6.5).
# `P1` §9.3 da to'laqonli yacheyka (dizaynning uchdan biri), demak nuqson
# haqiqiy va §17.5 ning qarori MAJBURIY edi.
#
# QAYSI BUDJET AMAL QILADI -- ungated'i. §17.2 gated budjetni (`+D_f = 300 ms`,
# §3 ning `k_f = 3`) FAQAT *"agar action `F_probe` ga gate qilinsa"* beradi.
# §9.3 P1 ning arm'larini `A` (`Restart=on-failure`, `RestartSec=100ms` --
# restart'ni systemd O'ZI qiladi, qaror yo'lida harness yo'q) va `no_action`
# (`Restart=no`) deb muzlatadi; ikkisi ham `F_probe` ga gate QILINMAGAN.
# Probe'ga gate qilinadigan aktor -- arm C, va uni §13 muzlatmaydi
# (*"o'z pre-registration'ini talab qiladi"*), §0 esa P1 qamrovidan
# CHIQARADI. Demak `P1` ni boshqaradigan budjet 13 s da `t_start <= 1.8 s`.
#
# NEGA AYNAN 13 -- eng kichik ishlaydigan qadam. Qaror qiluvchi band `P1`:
# o'lchangan **max 1.4807 s** (budjetdan 18% past), p99 1.3948 s (22% past)
# -- §6.2 jadvali, §10.1 da takrorlangan. 12.5 s da ungated budjet 1.3 s
# bo'lardi va `P1` ning MAKSIMUMI 1.4807 s undan OSHADI, ya'ni 13.0 --
# boshqaruvchi budjetni qaror qiluvchi bandning o'lchangan maksimumida
# qanoatlantiradigan eng kichik yarim-sekundlik qadam. Muzlatilgan qiymatga
# eng KICHIK o'zgarish.
#
# KELAJAK UCHUN CHEKLOV (test bilan qo'yilgan, da'vo emas). Gated arifmetika
# 13 s da `t_start <= 1.5 s` beradi, ya'ni `P1` max'iga qarshi zaxira faqat
# 1.5 - 1.4807 = 0.0193 s (1.3%). §12.4 esa 1.7% zaxirani *"o'lchov
# shovqinidan kichik"* deb baholaydi. Shuning uchun bu cap probe'ga gate
# qilinadigan arm'ga (arm C) **MEROS QILIB BERILMAYDI**: u §13 bo'yicha o'z
# pre-registration'ida arifmetikani QAYTA hisoblashi shart.
#
# NIMA CHEKLAYDI -- 12 s ni yaratgan sabab EMAS. 12 s `systemd-oomd` ning
# 20 s sustained oynasidan kelgan; `systemd-oomd` bu host'da binary, unit
# va config darajasida YO'Q (o'lchangan:
# docs/architecture/07-wsl-muhit-tekshiruvlari.md §6.4, kill authority yo'q).
# Qiymatni endi §9.4 **invariant 2** cheklaydi:
#     hold_s + ramp_above_threshold_s <= 15 s   (guard'ning `sustain_max`)
# `ramp_above_threshold_s` kalibrlangan `base_mb = 184` da 29 epizoddan
# **29 tasida 0.000 s** (§4.1), demak `13 + 0.000 = 13 <= 15` -- 2 s zaxira.
# §6.5 ning *"15 s gacha oshirish invariant 2 ni buzmaydi"* kuzatuvi to'g'ri,
# lekin 15 s zaxirani NOLGA tushirardi; 13 s 2 s zaxira qoldiradi.
HOLD_CAP_S = 13.0
INJECTION_OFFSET_S = 3.0       # §9.4 -- injeksiya hold'ga 3 s kirgach
W_STAB_PILOT_S = 8.0           # §4   -- pilot stabilizatsiya oynasi
T_Q_S = 5.0                    # §8.4 -- quiescence davomiyligi
T_W_S = 15.0                   # §8.4 -- washout qattiq poli
T_W_MAX_S = 120.0              # §8.4 -- washout cap -> washout_timeout
WASHOUT_PLANNED_S = 20.0       # §9.4 -- rejalashtirilgan washout (>=20 s)

# guard.py DEFAULTS["sustain_max_seconds"] bilan bir xil bo'lishi SHART.
# Guard 0.35 tezlikni 15 s davomida ko'rsa slice'ni o'ldiradi, ya'ni
# chegaradan yuqori pressure 15 s dan oshadigan jadval O'Z trial'larini
# `aborted_guard` ga aylantiradi. Bu xavfsizlik emas, isrof.
GUARD_SUSTAIN_WINDOW_S = 15.0

# Ramp'ning guard chegarasidan YUQORI o'tadigan qismi. §9.4 ramp'ni 5 s deb
# beradi, lekin ramp boshida tezlik nolga yaqin -- guard'ning hisoblagichi
# faqat chegaradan oshgandan keyin yuradi.
#
# Oldingi qiymat 3.0 TAXMIN edi (guard.py kalibratsiyasining "<=3 s" budjeti)
# va u faqat `hold_cap_s = 12` bilan birga ma'noga ega edi: `12 + 3 = 15`
# guard oynasini AYNAN to'ldiradi, zaxira nol. `hold_cap_s = 13` da o'sha
# taxmin invariant 2 ni buzardi, demak u shu o'zgarish bilan BIRGA
# yangilanishi shart.
#
# §9.4 bu qiymatni dosing kalibratsiyasidan olishni talab qiladi, taxmin
# qilishni emas -- va kalibratsiya BAJARILDI: `base_mb = 184` da, ya'ni doza
# haqiqatan yetkazilgan yagona konfiguratsiyada, `ramp_above_threshold_s`
# 29 epizoddan **29 tasida aynan 0.000 s**; ramp tezligi min=p50=max=0.0000,
# ya'ni §8.4 ning quiescence chegarasi 0.05 ga yaqinlashmadi ham
# (docs/architecture/10-pressure-dozalash.md §4.1). §4.2 esa invariantni
# allaqachon `12 + 0.000 = 12 <= 15` deb yozadi -- ya'ni hujjat
# kalibratsiyadan beri 0.000 ni ishlatgan, KOD esa yangilanmagan. Bu
# o'zgarish shu bo'shliqni yopadi; u YANGI muzlatilgan qiymat qarori
# EMAS, eskirgan konstantani o'lchov bilan almashtirish.
#
# OCHIQ BO'SHLIQ (ataylab yopilmagan). `validate.py` REJALASHTIRILGAN
# `ramp_above_threshold_s` ni (`planned_timeline` dagi qiymatni)
# tekshiradi, trial'da O'LCHANGAN qiymatni emas. Reja 0.0 bo'lgani uchun
# rejada zaxira QOLMAYDI: haqiqiy run nolga teng bo'lmagan ramp bersa, u
# yutilmaydi -- reja BUZILGAN bo'ladi. Konstanta ATAYLAB to'ldirilmaydi:
# to'ldirish taxmin bo'lardi, va aynan taxmin oldingi 3.0 ning nuqsoni
# edi. To'g'ri yechim -- driver har trial'da o'lchangan ramp qismini
# yozishi va validator uni rejaga qarshi tekshirishi; bu ALOHIDA ish
# bandi va bu yerda bajarilmaydi.
RAMP_ABOVE_THRESHOLD_S = 0.0

# ε va quiescence chegarasi pre-registration'da RAQAM bilan muzlatilmagan
# (§8.4 faqat "baseline ±ε" va "quiescence chegarasidan past" deydi).
# Shuning uchun ular sozlanadigan parametr, va default qiymatlar
# kalibratsiyadan keyin aniqlanishi kerak.
MEMORY_EPSILON_BYTES = 32 * 1024 * 1024
QUIESCENCE_RATE = 0.05


# --- xatolar ----------------------------------------------------------------


class ScheduleError(ValueError):
    """Dizayn parametrlari o'zaro ziddiyatli."""


class PressureCapExceeded(ScheduleError):
    """Pressure-on vaqti xavfsizlik chegarasidan oshadi.

    Bu XOHISH emas, QATTIQ cheklov. Tarixiy sabab: `systemd-oomd` 20 s
    sustained pressure ko'rsa foydalanuvchining ilovalarini o'ldiradi (12 s
    cap shundan kelgan). Bu host'da oomd YO'Q (07 §6.4), shuning uchun HOZIRGI
    chegaralovchi -- §9.4 2-invariant (`hold_s + ramp_above_threshold_s <=
    guard sustain_max`) va §15.3 ning shartnomaviy chegarasi; cap 13 s
    (preregistration/v1.11, §17.5 O3). Ko'ring revix/guard.py.
    """


class CampaignTooLong(ScheduleError):
    """Kampaniyaning baholangan davomiyligi berilgan chegaradan oshadi."""


# ===========================================================================
# 1. Randomized complete block design (§8.4, §9.3)
# ===========================================================================

# Level qiymatlari JSON'ga tushishi kerak, chunki jadval `run_meta` ga
# yoziladi va digest bilan bog'lanadi. Serializatsiya qilinmaydigan level
# jimgina boshqa jadvalga olib kelardi.
LEVEL_TYPES = (str, int, float, bool)


@dataclass(frozen=True)
class Factor:
    """Bitta eksperimental faktor va uning darajalari (§9.3).

    Faktor to'plami ERKIN: P1 da ikkita (`arm`, `pressure_level`), lekin
    confirmatory eksperiment `fault_class` va `pressure_pulse_duration`
    qo'shadi (§13). Shuning uchun dizayn boshidan n-o'lchovli faktorial.
    """

    name: str
    levels: tuple[Any, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "levels", tuple(self.levels))
        if not isinstance(self.name, str) or not self.name:
            raise ScheduleError("faktor nomi bo'sh bo'lmagan str bo'lishi kerak")
        if not self.levels:
            raise ScheduleError(f"faktor {self.name!r} darajasiz")
        for lv in self.levels:
            if not isinstance(lv, LEVEL_TYPES):
                raise ScheduleError(
                    f"faktor {self.name!r} darajasi JSON'ga tushmaydi: {lv!r}"
                )
        if len(set(self.levels)) != len(self.levels):
            raise ScheduleError(f"faktor {self.name!r} darajalari takrorlanadi")

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "levels": list(self.levels)}


# §9.3 -- P1 faktorlari. Fault faqat `clean_crash`, demak u faktor EMAS
# (bitta darajali faktor dizaynga hech narsa qo'shmaydi, lekin yacheyka
# sonini chalg'ituvchi qiladi). Confirmatory'da u faktor bo'ladi.
P1_FACTORS = (
    Factor("arm", ("A", "no_action")),
    Factor("pressure_level", ("P0", "P1", "P2")),
)
P1_BLOCKS = 20  # §9.3 -- 3 × 2 × 20 = 120 trial


@dataclass(frozen=True)
class Trial:
    """Bitta trial deskriptori -- jadvaldagi tartiblangan element.

    `levels` juftliklar tuple'i sifatida saqlanadi (dict emas): frozen
    dataclass ichidagi dict o'zgarmaslikni yolg'on qilardi, va juftliklar
    tuple'i hashlanadi, ya'ni yacheykani to'g'ridan-to'g'ri sanash mumkin.
    """

    trial_id: str
    block_index: int
    position_in_block: int
    levels: tuple[tuple[str, Any], ...]

    @property
    def levels_dict(self) -> dict[str, Any]:
        return dict(self.levels)

    @property
    def cell(self) -> tuple[Any, ...]:
        """Yacheyka identifikatori -- faktor tartibidagi daraja qiymatlari."""
        return tuple(v for _, v in self.levels)

    def level(self, name: str) -> Any:
        return dict(self.levels)[name]

    def as_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "trial_id": self.trial_id,
            "block_index": self.block_index,
            "position_in_block": self.position_in_block,
        }
        d.update(self.levels)
        return d


@dataclass(frozen=True)
class Schedule:
    """Randomized complete block jadvali (§8.4).

    Blok = har `(faktor × faktor × ...)` yacheykadan AYNAN BITTA trial,
    blok ICHIDA seeded RNG bilan aralashtirilgan. `n` blok ⇒ yacheykaga
    `n` replika, va blok sekin drift'ni (kun vaqti, cache holati, termal)
    o'ziga singdiradi -- drift blok ichidagi taqqoslashga emas, bloklar
    ORASIDAGI farqqa tushadi.

    `seed` jadvalda saqlanadi (va `run_meta` ga yoziladi), demak
    randomizatsiya aynan qayta tiklanadi. `digest` -- kanonik JSON'ning
    sha256'i: jadval boshqa mashinada boshqacha chiqsa, bu darhol ko'rinadi.
    """

    factors: tuple[Factor, ...]
    n_blocks: int
    seed: int
    trials: tuple[Trial, ...]

    @property
    def factor_names(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.factors)

    @property
    def cells_per_block(self) -> int:
        n = 1
        for f in self.factors:
            n *= len(f.levels)
        return n

    @property
    def n_trials(self) -> int:
        return len(self.trials)

    def block(self, index: int) -> tuple[Trial, ...]:
        return tuple(t for t in self.trials if t.block_index == index)

    def cells(self) -> tuple[tuple[Any, ...], ...]:
        """Barcha yacheykalar, deterministik tartibda (randomizatsiyasiz)."""
        return tuple(itertools.product(*(f.levels for f in self.factors)))

    def cell_counts(self) -> dict[tuple[Any, ...], int]:
        """Yacheyka -> trial soni. Balanslangan dizaynda hammasi `n_blocks`."""
        counts: dict[tuple[Any, ...], int] = {c: 0 for c in self.cells()}
        for t in self.trials:
            counts[t.cell] = counts.get(t.cell, 0) + 1
        return counts

    def as_dict(self) -> dict[str, Any]:
        return {
            "schedule_version": SCHEDULE_VERSION,
            "rng": RNG_NAME,
            "seed": self.seed,
            "n_blocks": self.n_blocks,
            "cells_per_block": self.cells_per_block,
            "n_trials": self.n_trials,
            "factors": [f.as_dict() for f in self.factors],
            "trials": [t.as_dict() for t in self.trials],
        }

    def to_json(self) -> str:
        """Kanonik serializatsiya. Digest va taqqoslash uchun yagona shakl."""
        return json.dumps(
            self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )

    def digest(self) -> str:
        return hashlib.sha256(self.to_json().encode()).hexdigest()


def full_factorial(factors: Sequence[Factor]) -> tuple[dict[str, Any], ...]:
    """To'liq faktorial yacheykalar, deterministik tartibda.

    §8.4 "complete block" ta'rifining asosi: blok aynan shu to'plamning
    bitta permutatsiyasi.
    """
    names = [f.name for f in factors]
    out = []
    for combo in itertools.product(*(f.levels for f in factors)):
        out.append(dict(zip(names, combo)))
    return tuple(out)


def _block_rng(seed: int, block_index: int) -> random.Random:
    """Blokka xos RNG.

    Har blok MUSTAQIL seed oladi (global oqimdan emas). Foydasi: kampaniyani
    20 blokdan 30 ga uzaytirish birinchi 20 blokning tartibini O'ZGARTIRMAYDI,
    demak yarim yig'ilgan ma'lumot yaroqsiz bo'lib qolmaydi.
    """
    return random.Random(f"revix-schedule:v{SCHEDULE_VERSION}:{seed}:{block_index}")


def make_schedule(
    factors: Sequence[Factor],
    n_blocks: int,
    seed: int,
) -> Schedule:
    """Randomized complete block jadvalini tuzadi (§8.4).

    Blok ichida aralashtirish -- seeded, demak takrorlanuvchi. Bloklar
    orasida aralashtirish YO'Q: blok tartibi vaqt tartibi, va blok
    indeksi analizda stratifikatsiya o'zgaruvchisi (§10.2).
    """
    factors = tuple(factors)
    if not factors:
        raise ScheduleError("kamida bitta faktor kerak")
    names = [f.name for f in factors]
    if len(set(names)) != len(names):
        raise ScheduleError(f"faktor nomlari takrorlanadi: {names}")
    if not isinstance(n_blocks, int) or isinstance(n_blocks, bool) or n_blocks < 1:
        raise ScheduleError("n_blocks >= 1 butun son bo'lishi kerak")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ScheduleError("seed butun son bo'lishi kerak (jadvalda saqlanadi)")

    cells = full_factorial(factors)
    # trial_id kengligi yacheyka/blok sonidan kelib chiqadi, shunda
    # leksikografik tartib = vaqt tartibi (log'larni saralashda muhim).
    bw = max(3, len(str(n_blocks - 1)))
    pw = max(3, len(str(len(cells) - 1)))

    trials: list[Trial] = []
    for b in range(n_blocks):
        order = list(cells)
        _block_rng(seed, b).shuffle(order)
        for pos, levels in enumerate(order):
            trials.append(
                Trial(
                    trial_id=f"b{b:0{bw}d}t{pos:0{pw}d}",
                    block_index=b,
                    position_in_block=pos,
                    levels=tuple((n, levels[n]) for n in names),
                )
            )
    return Schedule(factors=factors, n_blocks=n_blocks, seed=seed, trials=tuple(trials))


def p1_schedule(seed: int, n_blocks: int = P1_BLOCKS) -> Schedule:
    """P1 pilot jadvali (§9.3): 2 arm × 3 pressure × 20 blok = 120 trial."""
    return make_schedule(P1_FACTORS, n_blocks, seed)


# ===========================================================================
# 2. Washout policy -- sof holat mashinasi (§8.4)
# ===========================================================================

WASHOUT_KILL = "kill_subtree"
WASHOUT_MEMORY = "memory_baseline"
WASHOUT_QUIESCENCE = "quiescence"
WASHOUT_FLOOR = "floor"
WASHOUT_COMPLETE = "complete"
WASHOUT_TIMEOUT = "washout_timeout"

WASHOUT_STATES = (
    WASHOUT_KILL,
    WASHOUT_MEMORY,
    WASHOUT_QUIESCENCE,
    WASHOUT_FLOOR,
    WASHOUT_COMPLETE,
    WASHOUT_TIMEOUT,
)
WASHOUT_TERMINAL = (WASHOUT_COMPLETE, WASHOUT_TIMEOUT)


@dataclass(frozen=True)
class WashoutPolicy:
    """Washout parametrlari (§8.4).

    NEGA `total=` dan olingan INTERVAL tezliklari, `avgN` emas:

    `avgN` -- eksponensial silliqlangan o'rtacha, 2 s kadensda yangilanadi
    (§7). Silliqlash pressure to'xtagandan keyin ham SEKIN pasayadi: `avg300`
    ning vaqt konstantasi 300 s, demak `avg300` quiescence chegarasidan pastga
    tushishini kutish washout'ni ~300 s qilardi. 120 trial × 300 s ≈ 10 soat
    faqat washout -- kampaniyaning o'zidan (≈2.5 soat) uzunroq, ya'ni bir
    daraja farq.

    `total=` monotonik akkumulyator, demak
        stall_fraction(t1,t2) = (total(t2) − total(t1)) / (t2 − t1)
    aynan `[t1,t2]` oynasiga tegishli: silliqlash yo'q, o'tmish yo'q. Oldingi
    trial'ning holati keyingi oynaga SIZIB O'TMAYDI. Shuning uchun washout
    15 s ga tushadi (§8.4). Bu o'lchov qaroridan (§7: `total` asosiy) kelib
    chiqqan to'g'ridan-to'g'ri dizayn foydasi.

    OGOHLIK (§7): tezlik oynasi >=2 s bo'lishi kerak -- PSI ichki kadensi 2 s
    va `total` partiyalarda kreditlanadi, demak 100 ms delta oniy tezlik
    EMAS. Bu policy tezlikni O'ZI hisoblamaydi, chaqiruvchi beradi; oyna
    kengligi chaqiruvchining javobgarligi.
    """

    t_q_s: float = T_Q_S
    t_w_s: float = T_W_S
    t_w_max_s: float = T_W_MAX_S
    quiescence_rate: float = QUIESCENCE_RATE
    memory_epsilon_bytes: int = MEMORY_EPSILON_BYTES

    def __post_init__(self) -> None:
        if not (0.0 < self.t_q_s <= self.t_w_s <= self.t_w_max_s):
            raise ScheduleError("0 < T_q <= T_w <= T_w_max bo'lishi kerak")
        if self.quiescence_rate <= 0.0:
            raise ScheduleError("quiescence_rate > 0 bo'lishi kerak")
        if self.memory_epsilon_bytes < 0:
            raise ScheduleError("memory_epsilon_bytes >= 0 bo'lishi kerak")


DEFAULT_WASHOUT_POLICY = WashoutPolicy()


@dataclass(frozen=True)
class WashoutObservation:
    """Chaqiruvchi beradigan kuzatuv. Bu modul HECH NARSA o'qimaydi.

    `elapsed_s` -- washout boshidan o'tgan vaqt (monotonic, §1).
    `kill_issued` -- `cgroup.kill` ga 1 yozilgani TASDIQLANDI (§8.4 qadam 1).
    `memory_current` -- slice'ning `memory.current` (bayt).
    `slice_stall_rate` / `host_stall_rate` -- `total=` dan olingan interval
    tezliklari [0,1].

    `None` qiymat "o'qilmadi" degani va FAIL-CLOSED ishlanadi: o'qilmagan
    o'lchov "yaxshi" deb hisoblanmaydi (guard.py qoidasi 3 bilan bir xil).
    """

    elapsed_s: float
    kill_issued: bool = False
    memory_current: int | None = None
    slice_stall_rate: float | None = None
    host_stall_rate: float | None = None


@dataclass(frozen=True)
class WashoutProgress:
    """Washout holati. O'zgarmas: `washout_step` YANGI holat qaytaradi.

    Sof funksional shakl ataylab: holat mashinasini sinash uchun mashina
    kerak emas, faqat qiymatlar. Bu §8.4 ni ekshaustiv test qilishga
    imkon beradi.
    """

    state: str = WASHOUT_KILL
    memory_baseline: int | None = None
    quiet_since_s: float | None = None
    quiet_for_s: float = 0.0
    elapsed_s: float = 0.0
    reason: str | None = None

    @property
    def done(self) -> bool:
        return self.state == WASHOUT_COMPLETE

    @property
    def timed_out(self) -> bool:
        return self.state == WASHOUT_TIMEOUT

    @property
    def terminal(self) -> bool:
        return self.state in WASHOUT_TERMINAL


def washout_start(memory_baseline: int) -> WashoutProgress:
    """Washout boshlanishi (§8.4 qadam 1 kutilmoqda).

    `memory_baseline` -- trial oldidan o'lchangan slice `memory.current`.
    Majburiy: baseline bo'lmasa §8.4 qadam 2 ni tekshirish IMKONSIZ, va
    "tekshirilmagan" ni "o'tdi" deb hisoblash jimgina kontaminatsiya
    bo'lardi.
    """
    if memory_baseline is None or memory_baseline < 0:
        raise ScheduleError("memory_baseline manfiy bo'lmagan bayt bo'lishi kerak")
    return WashoutProgress(state=WASHOUT_KILL, memory_baseline=memory_baseline)


def _is_quiet(obs: WashoutObservation, policy: WashoutPolicy) -> bool:
    """Slice VA host stall tezliklari chegaradan past (§8.4 qadam 3).

    IKKISI ham: slice tinch, lekin host emas -- keyingi trial'ning baseline'i
    hali ifloslangan, chunki host stall SUT'ning ishiga ta'sir qiladi.
    O'qilmagan tezlik tinch DEB HISOBLANMAYDI (fail-closed).
    """
    for rate in (obs.slice_stall_rate, obs.host_stall_rate):
        if rate is None or rate >= policy.quiescence_rate:
            return False
    return True


def washout_step(
    progress: WashoutProgress,
    obs: WashoutObservation,
    policy: WashoutPolicy = DEFAULT_WASHOUT_POLICY,
) -> WashoutProgress:
    """Washout holat mashinasining bitta qadami (§8.4).

    Ketma-ketlik MUZLATILGAN va shu tartibda:
      1. `cgroup.kill` -- atomik subtree kill (chaqiruvchi bajaradi);
      2. `memory.current` baseline ±ε ga qaytishi;
      3. slice VA host stall tezliklari quiescence chegarasidan past,
         `T_q = 5 s` DAVOMIDA (bitta namuna yetarli EMAS);
      4. qattiq pol `T_w = 15 s` (washout boshidan);
      cap `T_w_max = 120 s` -> `washout_timeout`, trial chiqariladi (§12).

    Cap BIRINCHI tekshiriladi: §8.4 cap'ni shartsiz deb beradi. Ya'ni
    `T_w_max` dan keyin kelgan kuzatuv washout'ni yakunlay olmaydi, hatto
    barcha shartlar bajarilgan bo'lsa ham. Bu qat'iyroq o'qish, va
    qat'iylik bu yerda to'g'ri tomon: cap'dan oshgan washout keyingi
    trial'ning baseline'i haqidagi taxminni allaqachon buzgan.

    Bir kuzatuv bir nechta qadamdan o'tishi mumkin (masalan kill + memory),
    lekin qadam 3 ta'rifan bitta kuzatuvda o'tib bo'lmaydi: `T_q` oynasi
    >=2 kuzatuvni talab qiladi.
    """
    if progress.terminal:
        return progress  # idempotent: terminal holat o'zgarmaydi

    if obs.elapsed_s >= policy.t_w_max_s:
        return WashoutProgress(
            state=WASHOUT_TIMEOUT,
            memory_baseline=progress.memory_baseline,
            quiet_since_s=progress.quiet_since_s,
            quiet_for_s=progress.quiet_for_s,
            elapsed_s=obs.elapsed_s,
            reason="t_w_max",
        )

    state = progress.state
    quiet_since = progress.quiet_since_s
    quiet_for = progress.quiet_for_s
    reason = None

    if state == WASHOUT_KILL:
        if obs.kill_issued:
            state = WASHOUT_MEMORY
        else:
            reason = "kill_pending"

    if state == WASHOUT_MEMORY:
        base = progress.memory_baseline
        cur = obs.memory_current
        if cur is None:
            reason = "memory_unreadable"  # fail-closed: ilgarilamaydi
        elif abs(cur - base) <= policy.memory_epsilon_bytes:
            state = WASHOUT_QUIESCENCE
            quiet_since = None
            quiet_for = 0.0
        else:
            reason = "memory_above_baseline"

    if state == WASHOUT_QUIESCENCE:
        if _is_quiet(obs, policy):
            if quiet_since is None:
                quiet_since = obs.elapsed_s
            quiet_for = obs.elapsed_s - quiet_since
            if quiet_for >= policy.t_q_s:
                state = WASHOUT_FLOOR
            else:
                reason = "quiescence_building"
        else:
            # Uzilish -> oyna NOLDAN boshlanadi. `T_q` "5 s davomida",
            # "jami 5 s" emas.
            quiet_since = None
            quiet_for = 0.0
            reason = "not_quiescent"

    if state == WASHOUT_FLOOR:
        if obs.elapsed_s >= policy.t_w_s:
            state = WASHOUT_COMPLETE
        else:
            reason = "floor_pending"

    return WashoutProgress(
        state=state,
        memory_baseline=progress.memory_baseline,
        quiet_since_s=quiet_since,
        quiet_for_s=quiet_for,
        elapsed_s=obs.elapsed_s,
        reason=reason,
    )


class WashoutMachine:
    """`washout_step` ustidagi yupqa qobiq -- oxirgi holatni eslab turadi.

    Mantiq bu yerda YO'Q: u `washout_step` da, chunki sof funksiya sinashga
    arzon. Bu klass faqat chaqiruvchining qulayligi uchun.
    """

    def __init__(
        self, memory_baseline: int, policy: WashoutPolicy = DEFAULT_WASHOUT_POLICY
    ) -> None:
        self.policy = policy
        self.progress = washout_start(memory_baseline)
        self.history: list[WashoutProgress] = [self.progress]

    def observe(self, obs: WashoutObservation) -> WashoutProgress:
        self.progress = washout_step(self.progress, obs, self.policy)
        self.history.append(self.progress)
        return self.progress

    @property
    def state(self) -> str:
        return self.progress.state

    @property
    def done(self) -> bool:
        return self.progress.done

    @property
    def timed_out(self) -> bool:
        return self.progress.timed_out


# ===========================================================================
# 3. Disposition -- yopiq enum, total funksiya (§12, §6.2)
# ===========================================================================


@dataclass(frozen=True)
class TrialFacts:
    """Bitta trial haqida KUZATILGAN faktlar (da'volar emas).

    Har bir field log'langan hodisaga mos keladi, ya'ni disposition
    hukmdan emas, ma'lumotdan chiqadi:

    `harness_error`            -- harness istisnosi (§12).
    `guard_fired`              -- host guard trip qildi (§4 invalidator, §12).
    `unsolicited_kill`         -- biz yubormagan SIGKILL (§12).
    `foreign_oom_kill`         -- biz CHEKLAMAGAN cgroup'da oom_kill (§12).
                                  Cheklangan cgroup'dagi oom_kill kutilgan
                                  natija, kontaminatsiya emas.
    `bystander_lost_contract`  -- bystander xizmat buzildi (§12).
    `washout_timed_out`        -- washout `T_w_max` ichida yakunlanmadi (§8.4).
    `probe_gap_exceeded`       -- probe uzilishi > 2×P (§4, §12).
    `window_outside_hold`      -- §17 oynasi (`t_up + W_stab_pilot`) pressure hold
                                  (`T_h`) yoki horizon'dan chiqqan (§17.4(1)-(2):
                                  "`disposition` ikkalasida ham `censored`";
                                  §17.4(5)). Default `False` -- avvalgi har
                                  qanday fakt to'plamining disposition'i O'ZGARMAYDI.
    `horizon_ended_down`       -- horizon xizmat down holatda tugadi (§6.2).
    """

    harness_error: bool = False
    guard_fired: bool = False
    unsolicited_kill: bool = False
    foreign_oom_kill: bool = False
    bystander_lost_contract: bool = False
    washout_timed_out: bool = False
    probe_gap_exceeded: bool = False
    window_outside_hold: bool = False
    horizon_ended_down: bool = False

    @property
    def contaminated(self) -> bool:
        return (
            self.unsolicited_kill
            or self.foreign_oom_kill
            or self.bystander_lost_contract
        )

    def as_dict(self) -> dict[str, bool]:
        return {name: getattr(self, name) for name in FACT_FIELDS}


FACT_FIELDS = (
    "harness_error",
    "guard_fired",
    "unsolicited_kill",
    "foreign_oom_kill",
    "bystander_lost_contract",
    "washout_timed_out",
    "probe_gap_exceeded",
    "window_outside_hold",
    "horizon_ended_down",
)

# USTUVORLIK -- oshkora, tartiblangan va TOTAL (§12).
#
# Qoidalar yuqoridan pastga tekshiriladi, BIRINCHI moslik yutadi, va
# oxirgi qoida shartsiz. Demak "hech biri mos kelmadi" holati mavjud
# EMAS, va "ikkitasi qaytdi" holati ham mavjud emas -- funksiya bitta
# qiymat qaytaradi. §12 ning butun maqsadi shu: jimgina eksklyuziya
# imkonsiz bo'lishi.
#
# Tartibning ASOSI (ehtimol emas, sabab zanjiri):
#   1. `harness_error` -- harness o'zi ishlamagan bo'lsa, boshqa hech bir
#      kuzatuvga ishonib bo'lmaydi. Eng yuqori.
#   2. `aborted_guard` -- guard trial'ni to'xtatgan; undan keyingi har
#      qanday o'lchov artefakt. Xavfsizlik aralashuvi o'lchovdan ustun.
#   3. `contaminated` -- trial DAVOMIDA o'lchovning o'zi buzilgan.
#   4. `washout_timeout` -- trial'dan KEYINGI protsedura buzilgan.
#   5. `censored` -- o'lchovning QONUNIY natijasi: §6.2 bo'yicha censored
#      trial analizga KIRADI. Shuning uchun u eng past: eksklyuziya
#      sababi censoring'dan ustun bo'lishi SHART, aks holda chiqarilishi
#      kerak bo'lgan trial "censored" yorlig'i ostida analizga kirib
#      ketardi.
#   6. `complete` -- shartsiz qoldiq.
DispositionRule = tuple[str, Callable[["TrialFacts"], bool], str]

DISPOSITION_RULES: tuple[DispositionRule, ...] = (
    ("harness_error", lambda f: f.harness_error, "harness_error"),
    ("guard_fired", lambda f: f.guard_fired, "aborted_guard"),
    ("unsolicited_kill", lambda f: f.unsolicited_kill, "contaminated"),
    ("foreign_oom_kill", lambda f: f.foreign_oom_kill, "contaminated"),
    ("bystander_lost_contract", lambda f: f.bystander_lost_contract, "contaminated"),
    ("washout_timed_out", lambda f: f.washout_timed_out, "washout_timeout"),
    ("probe_gap_exceeded", lambda f: f.probe_gap_exceeded, "censored"),
    # §17.4(2): oyna hold'dan chiqqan trial `censored` (p1-pilot-001 da bu
    # fakt YO'Q edi -- `docs/architecture/15-...` §2.4). `probe_gap` dan KEYIN,
    # `horizon_ended_down` dan OLDIN -- `reduce.derive_disposition` tartibi.
    ("window_outside_hold", lambda f: f.window_outside_hold, "censored"),
    ("horizon_ended_down", lambda f: f.horizon_ended_down, "censored"),
    ("measured", lambda f: True, "complete"),
)

# Import paytidagi struktura tekshiruvi: qoida jadvali YOPIQ enum bilan
# aynan bir xil to'plamni qoplashi kerak. `assert` emas -- `python -O`
# uni o'chirib yuborardi, va bu tekshiruv o'chirilmasligi kerak.
_RULE_OUTPUTS = {d for _, _, d in DISPOSITION_RULES}
if _RULE_OUTPUTS != set(DISPOSITIONS):
    raise RuntimeError(
        "disposition qoidalari yopiq enum bilan mos kelmaydi: "
        f"qoidalar={sorted(_RULE_OUTPUTS)} enum={sorted(DISPOSITIONS)}"
    )
if DISPOSITION_RULES[-1][1](TrialFacts()) is not True:
    raise RuntimeError("oxirgi disposition qoidasi shartsiz bo'lishi kerak")


@dataclass(frozen=True)
class DispositionVerdict:
    """Disposition + uni bergan qoida + MOS KELGAN barcha qoidalar.

    `matched_rules` diagnostika uchun: trial nega chiqarilgani bitta
    yorliqdan ko'proq ma'lumot bo'lishi mumkin (masalan guard trip
    qildi VA probe uzildi). Yorliq bitta, lekin sabablar yozilib qoladi.
    """

    disposition: str
    rule: str
    matched_rules: tuple[str, ...]


def assign_disposition(facts: TrialFacts) -> str:
    """Kuzatilgan faktlar -> AYNAN BITTA disposition (§12).

    Total: qoida jadvalining oxirgi elementi shartsiz, demak har qanday
    fakt kombinatsiyasi qiymat qaytaradi. Yagona: birinchi moslik yutadi.
    """
    for _, pred, disposition in DISPOSITION_RULES:
        if pred(facts):
            return disposition
    # Yetib bo'lmaydi: oxirgi qoida shartsiz (import paytida tekshirilgan).
    raise RuntimeError("disposition qoidalari total emas")


def explain_disposition(facts: TrialFacts) -> DispositionVerdict:
    """`assign_disposition` + qaysi qoidalar mos kelgani (§12 hisoboti)."""
    matched = tuple(name for name, pred, _ in DISPOSITION_RULES if pred(facts))
    for name, pred, disposition in DISPOSITION_RULES:
        if pred(facts):
            return DispositionVerdict(disposition, name, matched)
    raise RuntimeError("disposition qoidalari total emas")


# §12: `contaminated` va `aborted_guard` birlamchi analizdan CHIQARILADI,
# lekin ularning ulushi natija sifatida beriladi. `censored` esa §6.2
# bo'yicha analizga KIRADI -- tashlanmaydi, ishlanadi.
#
# NEGA NOM O'ZGARDI (§16.4): bu konstantaning QIYMATI to'g'ri, lekin nomi
# chalg'ituvchi edi. §16.4 jadvali: *"to'g'ri, lekin nomi `ANALYSIS_SET`
# bo'lishi kerak edi; `PRIMARY` so'zi uni §10.1 ning birlamchi testi bilan
# chalkashtiradi."* U javob beradigan savol -- **analiz to'plami butun
# holda**: §6.2 ning Kaplan-Meier / log-rank, loop-rate va har jadvaldagi
# `recovered within T_trial: k/n` qatoriga kiradigan trial'lar.
#
# U javob BERMAYDIGAN savol -- §10.1 ning binar `P(VR)` MAXRAJI. O'sha
# maxraj §16.2(B) bo'yicha `disposition` bilan EMAS, `(disposition,
# disposition_source)` JUFTI bilan aniqlanadi (`censored` + `down_at_horizon`
# kiradi, `censored` + `probe_gap` kirmaydi) va u `revix/reduce.py` ning
# `enters_primary_denominator()` funksiyasida yashaydi. Bu modul
# `disposition_source` ni KO'RMAYDI, demak u savolga javob bera OLMAYDI.
ANALYSIS_SET_DISPOSITIONS = ("complete", "censored")

# DEPRECATED alias -- eski nom buzilmasligi uchun saqlanadi (§16.4 nomni
# o'zgartirishni TALAB qilmaydi, faqat chalkashlikni nomlaydi). Yangi kod
# `ANALYSIS_SET_DISPOSITIONS` ni ishlatadi.
PRIMARY_ANALYSIS_DISPOSITIONS = ANALYSIS_SET_DISPOSITIONS

EXCLUDED_DISPOSITIONS = tuple(
    d for d in DISPOSITIONS if d not in ANALYSIS_SET_DISPOSITIONS
)


def enters_analysis_set(disposition: str) -> bool:
    """Trial ANALIZ TO'PLAMIGA kiradimi (§6.2, §12, §16.4).

    Bu -- survival / loop-rate / `k/n` to'plami, §10.1 ning binar `P(VR)`
    MAXRAJI EMAS. Maxraj uchun: `revix.reduce.enters_primary_denominator()`,
    u `(disposition, disposition_source)` juftini talab qiladi (§16.2(B)).
    """
    if disposition not in DISPOSITIONS:
        raise ScheduleError(f"yopiq enumda yo'q disposition: {disposition!r}")
    return disposition in ANALYSIS_SET_DISPOSITIONS


def enters_primary_analysis(disposition: str) -> bool:
    """DEPRECATED alias -> `enters_analysis_set()` (§16.4: nom chalg'ituvchi)."""
    return enters_analysis_set(disposition)


# ===========================================================================
# 4. Trial jadvali (§9.4)
# ===========================================================================


@dataclass(frozen=True)
class TrialTimeline:
    """Bitta trial'ning REJALASHTIRILGAN vaqt jadvali (§9.4).

    pre-flight -> `R_ref` baseline (10 s) -> ramp (5 s) -> hold (injeksiya
    hold'ga 3 s kirgach) -> pressure off -> washout.

    XAVFSIZLIK INVARIANTI (qattiq cheklov, xohish emas): sustained
    pressure-on vaqti `hold_cap_s` dan oshmaydi. Cheklov buzilsa parametr
    to'plami QABUL QILINMAYDI -- ogohlantirish emas, istisno.

    NIMA UCHUN bu cheklov bor -- va nima uni BUGUN cheklaydi. Tarixan
    `hold_cap_s = 12 s` ni `systemd-oomd` yaratgan: u 20 s sustained memory
    pressure ko'rsa `user@UID.service` ichidagi eng yirik iste'molchini
    o'ldiradi, ya'ni foydalanuvchining brauzerini yoki butun desktop
    sessiyasini. Bu host'da `systemd-oomd` YO'Q -- binary, unit va config
    darajasida o'rnatilmagan, kill authority yo'q (o'lchangan:
    docs/architecture/07-wsl-muhit-tekshiruvlari.md §6.4). Demak 12 s ni
    yaratgan sabab bu muhitda AMAL QILMAYDI, va `hold_cap_s` §17.5 ning O3
    variantiga ko'ra 13 s ga ko'tarildi (HOLD_CAP_S ning izohini ko'ring).
    Cap'ning O'ZI saqlanadi: §15.3 uni shartnomaviy asosda talab qiladi va
    oomd MAVJUD bo'lgan host'da yana 1-raqamli xavf bo'ladi.

    Qiymatni bugun cheklaydigan invariant -- IKKINCHISI:
    `hold_s + ramp_above_threshold_s` guard'ning sustain oynasidan (15 s)
    oshmasligi kerak. Aks holda TO'G'RI ishlagan trial ham guard'ni
    qo'zg'atib `aborted_guard` bo'lardi -- xavfsizlik buzilmaydi, lekin
    trial isrof bo'ladi va eksklyuziya darajasi sun'iy ravishda oshadi.
    Kalibrlangan dial'da `ramp_above_threshold_s = 0.000 s` (29/29 epizod,
    10-pressure-dozalash.md §4.1), demak `13 + 0.000 = 13 <= 15`: 2 s zaxira.
    """

    preflight_s: float = 5.0
    baseline_s: float = R_REF_BASELINE_S
    ramp_s: float = RAMP_S
    hold_s: float = HOLD_CAP_S
    injection_offset_s: float = INJECTION_OFFSET_S
    w_stab_s: float = W_STAB_PILOT_S
    washout_s: float = WASHOUT_PLANNED_S
    hold_cap_s: float = HOLD_CAP_S
    ramp_above_threshold_s: float = RAMP_ABOVE_THRESHOLD_S
    guard_sustain_window_s: float = GUARD_SUSTAIN_WINDOW_S
    t_w_s: float = T_W_S
    t_w_max_s: float = T_W_MAX_S

    def __post_init__(self) -> None:
        for name in ("baseline_s", "ramp_s", "hold_s", "w_stab_s", "washout_s"):
            if getattr(self, name) <= 0:
                raise ScheduleError(f"{name} > 0 bo'lishi kerak")
        for name in ("preflight_s", "injection_offset_s", "ramp_above_threshold_s"):
            if getattr(self, name) < 0:
                raise ScheduleError(f"{name} >= 0 bo'lishi kerak")

        # --- XAVFSIZLIK: pressure cap (§9.4 1-invariant) ---
        if self.hold_s > self.hold_cap_s:
            raise PressureCapExceeded(
                f"sustained pressure-on {self.hold_s} s > cap {self.hold_cap_s} s "
                "(cap'ni endi oomd emas, §9.4 2-invariant va guard sustain_max "
                "chegaralaydi; §17.5 O3)"
            )
        if self.ramp_above_threshold_s > self.ramp_s:
            raise ScheduleError(
                "ramp_above_threshold_s ramp_s dan katta bo'lishi mumkin emas"
            )
        if self.hold_s + self.ramp_above_threshold_s > self.guard_sustain_window_s:
            raise PressureCapExceeded(
                f"chegaradan yuqori pressure "
                f"{self.hold_s + self.ramp_above_threshold_s} s > guard sustain "
                f"oynasi {self.guard_sustain_window_s} s -- guard har trial'ni "
                "aborted_guard qilardi"
            )

        # --- §4: W_stab_pilot pressure oynasi ICHIGA sig'ishi kerak ---
        if self.injection_offset_s + self.w_stab_s > self.hold_s:
            raise ScheduleError(
                f"injeksiya (+{self.injection_offset_s} s) + W_stab "
                f"({self.w_stab_s} s) hold ({self.hold_s} s) ichiga sig'maydi; "
                "§4 stabilizatsiya oynasi pressure ostida o'tishini talab qiladi"
            )

        # --- §8.4: washout poli va cap ---
        if self.washout_s < self.t_w_s:
            raise ScheduleError(
                f"washout {self.washout_s} s < qattiq pol T_w {self.t_w_s} s"
            )
        if self.washout_s > self.t_w_max_s:
            raise ScheduleError(
                f"rejalashtirilgan washout {self.washout_s} s > cap "
                f"T_w_max {self.t_w_max_s} s"
            )

    # --- fazalar (trial boshidan, sekund) ---

    @property
    def t_baseline_start(self) -> float:
        return self.preflight_s

    @property
    def t_ramp_start(self) -> float:
        return self.t_baseline_start + self.baseline_s

    @property
    def t_hold_start(self) -> float:
        return self.t_ramp_start + self.ramp_s

    @property
    def t_inject(self) -> float:
        """§9.4 -- injeksiya hold'ga `injection_offset_s` kirgach."""
        return self.t_hold_start + self.injection_offset_s

    @property
    def t_verify_end_earliest(self) -> float:
        """`W_stab` oynasining ENG ERTA tugashi.

        Haqiqiy oyna `t_up` dan boshlanadi, `t_inject` dan emas, va
        `t_up >= t_inject` (detection + action kechikishi). Demak bu
        pastki chegara: invariant "eng yaxshi holatda sig'adi" ni
        tekshiradi, "har doim sig'adi" ni EMAS. Bu cheklov ochiq
        yoziladi, yumshatilmaydi.
        """
        return self.t_inject + self.w_stab_s

    @property
    def t_pressure_off(self) -> float:
        return self.t_hold_start + self.hold_s

    @property
    def t_washout_start(self) -> float:
        return self.t_pressure_off

    @property
    def sustained_pressure_on_s(self) -> float:
        """Nishonda ushlangan vaqt (tarixan oomd kriteriyasi uchun; hozir guard sustain_max uchun)."""
        return self.hold_s

    @property
    def pressure_on_s(self) -> float:
        """Generator YONIQ turgan umumiy vaqt (ramp + hold).

        Bu oomd kriteriyasi EMAS (ramp boshida stall ~0), lekin
        log'langan generator ish vaqti sifatida beriladi.
        """
        return self.ramp_s + self.hold_s

    @property
    def total_s(self) -> float:
        return self.t_washout_start + self.washout_s

    @property
    def worst_case_total_s(self) -> float:
        """Washout cap'ga (`T_w_max`) cho'zilsa -- rejalash uchun."""
        return self.t_washout_start + self.t_w_max_s

    def phases(self) -> tuple[tuple[str, float, float], ...]:
        """(nom, boshlanish, tugash) -- tartiblangan, bo'shliqsiz."""
        return (
            ("preflight", 0.0, self.t_baseline_start),
            ("baseline_r_ref", self.t_baseline_start, self.t_ramp_start),
            ("ramp", self.t_ramp_start, self.t_hold_start),
            ("hold", self.t_hold_start, self.t_pressure_off),
            ("washout", self.t_washout_start, self.total_s),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "preflight_s": self.preflight_s,
            "baseline_s": self.baseline_s,
            "ramp_s": self.ramp_s,
            "hold_s": self.hold_s,
            "injection_offset_s": self.injection_offset_s,
            "w_stab_s": self.w_stab_s,
            "washout_s": self.washout_s,
            "hold_cap_s": self.hold_cap_s,
            "ramp_above_threshold_s": self.ramp_above_threshold_s,
            "guard_sustain_window_s": self.guard_sustain_window_s,
            "t_inject_s": self.t_inject,
            "t_pressure_off_s": self.t_pressure_off,
            "sustained_pressure_on_s": self.sustained_pressure_on_s,
            "pressure_on_s": self.pressure_on_s,
            "total_s": self.total_s,
        }


# ===========================================================================
# 5. Kampaniya bahosi (§9.4)
# ===========================================================================


@dataclass(frozen=True)
class CampaignEstimate:
    """Kampaniyaning baholangan wall-clock davomiyligi.

    Maqsadi: tasodifiy 40 soatlik kampaniya ISHGA TUSHIRISHDAN OLDIN
    tutilishi, keyin emas. §9.4 P1 uchun ≈2.5 soat deb beradi.
    """

    n_trials: int
    n_blocks: int
    per_trial_s: float
    per_trial_overhead_s: float
    total_s: float
    total_hours: float
    worst_case_total_s: float
    worst_case_hours: float
    pressure_on_total_s: float
    sustained_pressure_on_total_s: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_trials": self.n_trials,
            "n_blocks": self.n_blocks,
            "per_trial_s": self.per_trial_s,
            "per_trial_overhead_s": self.per_trial_overhead_s,
            "total_s": self.total_s,
            "total_hours": self.total_hours,
            "worst_case_total_s": self.worst_case_total_s,
            "worst_case_hours": self.worst_case_hours,
            "pressure_on_total_s": self.pressure_on_total_s,
            "sustained_pressure_on_total_s": self.sustained_pressure_on_total_s,
        }


def estimate_campaign(
    schedule: Schedule,
    timeline: TrialTimeline | None = None,
    per_trial_overhead_s: float = 0.0,
    max_hours: float | None = None,
) -> CampaignEstimate:
    """Jadval + trial jadvali -> baholangan davomiylik (§9.4).

    `per_trial_overhead_s` -- §9.4 dagi ≈75 s/trial fazalar yig'indisidan
    (default parametrlarda 53 s: hold 12 -> 13 s, §17.5 O3) katta, va farq
    §9.4 da band-band yozilmagan (unit reset, D-Bus so'rovlari, cache
    tegishi, log flush).
    Shuning uchun u AYRIM parametr: baho jimgina to'ldirilmaydi,
    chaqiruvchi qo'shimchani oshkora beradi.

    `worst_case_*` washout har trial'da `T_w_max` ga cho'zilsa: bu
    yuqori chegara, chunki washout shartga bog'liq va faqat pastdan
    (`T_w`) qat'iy.
    """
    if timeline is None:
        timeline = TrialTimeline()
    if per_trial_overhead_s < 0:
        raise ScheduleError("per_trial_overhead_s >= 0 bo'lishi kerak")

    n = schedule.n_trials
    per_trial = timeline.total_s + per_trial_overhead_s
    total = per_trial * n
    worst = (timeline.worst_case_total_s + per_trial_overhead_s) * n
    est = CampaignEstimate(
        n_trials=n,
        n_blocks=schedule.n_blocks,
        per_trial_s=per_trial,
        per_trial_overhead_s=per_trial_overhead_s,
        total_s=total,
        total_hours=total / 3600.0,
        worst_case_total_s=worst,
        worst_case_hours=worst / 3600.0,
        pressure_on_total_s=timeline.pressure_on_s * n,
        sustained_pressure_on_total_s=timeline.sustained_pressure_on_s * n,
    )
    if max_hours is not None and est.total_hours > max_hours:
        raise CampaignTooLong(
            f"baholangan kampaniya {est.total_hours:.2f} soat > chegara "
            f"{max_hours} soat ({n} trial × {per_trial:.1f} s)"
        )
    return est
