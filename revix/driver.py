"""Trial orkestratsiyasi -- kampaniyani yurituvchi yagona jarayon.

Amalga oshiradigan shartnomalar:
  * docs/architecture/04-driver-va-analiz-shartnomasi.md §1 -- run katalogi,
    `run_meta.json` majburiy maydonlari, trial hodisalari ketma-ketligi va
    o'nta driver majburiyati (`driver-contract/v1`, §4.3 field nomlari);
  * PREREGISTRATION.md §1 (vaqt disiplinasi), §2-§6 (ta'riflar), §8.2
    (o'z perturbatsiyasi), §8.4 (randomizatsiya va washout), §9 (P1 dizayni),
  * §12 (disposition yopiq enum), §14 (data schema);
  * docs/architecture/00-pilot-topologiya.md §1 (cgroup topologiyasi va unit
    dial'lari), §2 (cheklash), §5 (trial jadvali), §6 (qurilish tartibi);
  * docs/architecture/01-muhit-tekshiruvlari.md §4 (`systemctl show` tuzog'i);
  * docs/architecture/03-sut-protokoli.md §5 (fault endpoint'lari).

Bu modul YANGI MEXANIZM IXTIRO QILMAYDI. Barcha mexanizm allaqachon bor va
unit-test qilingan: `schema` (envelope va yozuvchilar), `schedule` (dizayn,
washout, disposition), `units` (systemd), `cgroup` (PSI va cgroup), `guard`,
`prober`, `psi_sampler`, `pressure`. Driver -- faqat ORKESTRATSIYA YELIMI.


DIZAYN QOIDALARI (buzilmaydi)
=============================

 1. GUARD BIRINCHI START, OXIRGI STOP (shartnoma §1.3 majburiyat 1).
    Mexanizm: guard ALOHIDA transient systemd unit'i (`revix-guard.service`),
    driver'ning childi EMAS -- uning hayot tsiklini systemd ushlab turadi.
    Busiz nima buzilardi: qotib qolgan yoki o'lgan driver guard'ni ham o'ldirib,
    pressure'ni kuzatuvsiz qoldirardi va `systemd-oomd` foydalanuvchining
    brauzerini/editorini o'ldirardi. Himoya qiladi: SECURITY.md §(b),
    00-pilot-topologiya.md §3.1 (b).

 2. GUARD ISHGA TUSHMASA RUN BOSHLANMAYDI (majburiyat 2, FAIL-CLOSED).
    Mexanizm: `_verify_guard_live()` guard'ning O'Z oqimida (`guard.jsonl`)
    `guard_start` record'ini VA unit'ning `active` holatini talab qiladi;
    `guard.run()` ning 2-chiqish kodi (`watch_open_failed`) ham tutiladi.
    Busiz nima buzilardi: guard yiqilgan holda kampaniya ishlab ketardi va
    hech bir trial'da buni ko'rsatuvchi iz qolmasdi.

 3. HAR RUN BOSHIDA `units.clear_runtime_drop_ins()` (majburiyat 3).
    Mexanizm: run boshida, pre-flight'dan OLDIN chaqiriladi.
    Busiz nima buzilardi: oldingi run'ning `MemoryHigh=` runtime drop-in'i
    JIMGINA meros bo'lib, pressure dozasi boshqa bo'lib qolardi (§8
    kontaminatsiya).

 4. `units.require_clean()` PRE-FLIGHT (majburiyat 4).
    Mexanizm: drop-in tozalashdan KEYIN, slice dial'laridan OLDIN. Tartib
    muhim: dial'lar `SetUnitProperties` bilan qo'yiladi va slice'ni systemd'ga
    yuklaydi, demak ularni pre-flight'dan oldin qo'ysak pre-flight o'zimiz
    yaratgan holatdan yiqilardi.

 5. HAR TRIAL UCHUN AYNAN BITTA `trial_end` + disposition (majburiyat 5, §12).
    Mexanizm: `_run_trial()` ning `finally` bloki yagona `_emit_trial_end()`
    chaqiruvi; `Driver._ended` to'plami takroriy yozishni IMKONSIZ qiladi
    (ikkinchi urinish `DriverError`). Disposition `schedule.TrialFacts` +
    `schedule.explain_disposition()` dan keladi -- hukmdan emas, FAKTdan.
    Busiz nima buzilardi: jimgina eksklyuziya (§12 ning butun maqsadi).

 6. `schedule.TrialTimeline` INVARIANTLARI MAJBURLANADI (majburiyat 6).
    Mexanizm: timeline `__post_init__` da o'zi RAISE qiladi; driver uni
    OLDINDAN TEKSHIRMAYDI va JIMGINA TUZATMAYDI -- istisno yuqoriga chiqadi va
    run boshlanmaydi. Pressure cap = `systemd-oomd` himoyasi, afzallik emas.

 7. PROBER va `psi_sampler` `revixmon.slice` DA (majburiyat 7, §8.2).
    8. SUT/bystander/generator `revixlab.slice` DA (majburiyat 8).
    Mexanizm: har unit `Slice=` property'si bilan yaratiladi; slice nomlarida
    DASH YO'Q (dash systemd'da ierarxiya ajratuvchisi -- amendment v1.1, bu
    VALIDLIK xatosi edi, kosmetik emas). Busiz harness'ning PSI'si
    o'lchanayotgan slice'ning PSI'siga qo'shilib, §8.2 feedback artefaktini
    yaratardi.

 9. TRIAL QO'SHIMCHA VAQTI O'LCHANADI, TAXMIN QILINMAYDI (majburiyat 9, §9.4
    v1.3). Mexanizm: run boshida `_measure_overhead()` haqiqiy unit
    yaratish/dump/yig'ishtirish tsiklini (fault YO'Q, pressure YO'Q) o'lchaydi
    va natijani `run_meta.per_trial_overhead_s` ga yozadi; har trial o'zining
    qo'shimcha vaqtini `trial_end.overhead_us` da beradi. `--dry-run` da
    o'lchov bo'lmaydi va bu `per_trial_overhead_source` da OCHIQ yoziladi.

10. `--dry-run` HECH NARSA ISHGA TUSHIRMAYDI (majburiyat 10).
    Mexanizm: `main()` dry-run yo'lida `Platform` ni umuman yaratmaydi va
    faqat jadvalni chiqaradi. Busiz randomizatsiyani ko'zdan kechirish uchun
    eksperimentni ishga tushirish kerak bo'lardi.

11. MAVJUD RUN KATALOGI -- XATO (shartnoma §1). `datasets/` append-only
    (CONTRIBUTING.md §1.4). Mexanizm: `prepare_run_dir()` `os.mkdir` bilan
    yaratadi; katalog bo'lsa `RunDirExistsError`. Busiz ikki run bir-birining
    `events.jsonl` iga qo'shilib, `seq` oqimlari aralashib ketardi.

12. HAR RECORD'DA `stream == record_type`.
    Mexanizm: `_emit()` har doim `stream=record_type` beradi.
    NEGA: `validate._stream_key()` oqimni `(emitter, record_type)` juftligi
    bilan kalitlaydi (validate.py:302). Bitta oqimga ikki record turi
    yozilsa `seq` bo'shliqlari SOXTA ko'rinadi va §14.6 invariant 3 buziladi.

13. ISTISNO O'LCHOV TSIKLINI TO'XTATMAYDI, LEKIN HECH QACHON JIM EMAS.
    Mexanizm: har trial `try/except` ichida; istisno `harness_error` record'i
    VA `harness_error` disposition'iga aylanadi, keyin keyingi trial davom
    etadi. Run DARAJASIDAGI istisno (guard, pre-flight) esa run'ni boshlatmaydi.

14. PSI HECH QANDAY TA'RIFGA KIRMAYDI (CONTRIBUTING.md §1.5, §5).
    Driver PSI'ni FAQAT ikki joyda o'qiydi: (a) washout quiescence sharti
    (§8.4 qadam 3), (b) `env_snapshot` kovariatasi. Failure, VR yoki FR
    ta'rifiga -- HECH QACHON. Prober hech bir arm'ning qaror yo'liga
    ulanmaydi va probe narxi arm'lar bo'yicha bir xil.

15. `None` = O'LCHANMADI, `0` = O'LCHANGAN NOL. Har joyda. systemd'ning
    bo'sh timestamp'i (`0` yoki `UINT64_MAX`) `None` ga aylantiriladi --
    aks holda `reduce.compute_d_sd` ularni haqiqiy vaqt deb hisoblardi.

16. PRESSURE ESHIK ORTIDA. `--allow-pressure` berilmasa generator UMUMAN
    ishga tushmaydi va `P0` dan boshqa daraja bo'lgan jadval RAD ETILADI.
    NEGA: 00-pilot-topologiya.md §6 qadam 3 guard tasdiqlanishini qadam 4
    (pressure dosing) dan OLDIN talab qiladi -- "Retrofit qilinmaydi".
    Struktura bilan majburlanadi, diqqat bilan emas.

17. DOZA DIAL'I OSHKORA BERILADI, MEROS QILINMAYDI.
    Mexanizm: `_pressure_argv()` generatorga `--step-mb`, `--base-mb` va
    `--interval-ms` ni HAR DOIM beradi (`PRESSURE_STEP_MB`,
    `PRESSURE_BASE_MB`, `PRESSURE_INTERVAL_MS`), ya'ni `pressure.run_pi`
    ning `base = max(16, high_MiB - 2*step_mb)` avtomatik formulasiga ham,
    modul default'lariga ham TAYANMAYDI.
    NEGA: 10-pressure-dozalash.md §2.5 / OQ-2 aynan shu merosni o'lchadi --
    argv dial'ni bermaganda modul default'i `step_mb=16` ishlab,
    `base = 192 - 2*16 = 160 MiB` chiqadi va bu §2.2 ning D1 epizodida
    o'lchangan NOL-DOZA konfiguratsiyasi (erishilgan stall 114 namunada ham
    aynan 0.0000). Busiz nima buzilardi: `P1` va `P2` arm'lari 0.0000 stall
    bilan ishlab, PREREGISTRATION.md §9.3 ning UCH darajali dizayni jimgina
    BITTA darajaga (`P0` ga) qulardi va natija H1 ga qarshi dalil emas,
    ASBOB NUQSONI bo'lardi -- §9.2 ning "null ta'rif artefakti" ogohligining
    asbob tomonidagi analogi. Chiqishda buni ko'rsatuvchi hech narsa yo'q edi.
    Dial OSHKORA bo'lgani uchun `MemoryHigh` o'zgarsa baza JIMGINA o'zgarmaydi
    -- regressiya qulfi (`tests/unit/test_driver.py`) buni YIQITADI.
    `--memory-high` esa RUNTIME bayrog'i, demak uni test tutib qolmaydi:
    shu sababli `setup_run()` da `_require_nonzero_dose()` pre-flight'i bor
    va u run'ning HAQIQIY `MemoryHigh` idan arifmetikani hisoblab, nol doza
    bo'lsa `ZeroDoseError` bilan RUN'NI BOSHLATMAYDI (fail-closed, majburiyat
    4 bilan bir xil posture). `P0` bundan MUSTASNO -- uning nol dozasi §9.3
    ning "generator idle" sharti (§3.2), nuqson emas.


MUZLATILMAGAN, SHUNING UCHUN OCHIQ PARAMETR (hech biri jimgina tanlanmaydi)
==========================================================================
`--watchdog-sec`, `--timeout-start-sec`, `--memory-high`, pressure band
nishonlari: pre-registration ularni RAQAM bilan muzlatmagan. Hammasi
`run_meta.open_parameters` da `calibration_required` belgisi bilan yoziladi.
`step_mb` / `base_mb` ham o'sha yerda, lekin ular 10-pressure-dozalash.md
§2.6 da O'LCHANGAN, demak `calibration_required: false`.
`ramp_above_threshold_s` ham ENDI o'lchangan (§4.1, 29/29 epizodda 0.000 s),
demak uning belgisi ham `false` -- va u YANGI `calibration` bloki bilan
keladi, chunki "o'lchandi" da'vosi o'lchov, uning manbasi va rejaning
zaxirasini KO'RSATISHI kerak, boolean'ni aylantirish YETARLI EMAS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Sequence

from . import cgroup as cg
from . import schedule as sch
from . import units as U
from .schema import (
    DISPOSITIONS,
    Emitter,
    JsonlWriter,
    mono_us,
    new_run_id,
    read_boot_id,
    real_us,
)

DRIVER_VERSION = 1
# Amalga oshirilgan shartnoma bandlari. `v1.1` field nomlarini (§4.3) va
# `T_trial` ni (§5.4) belgiladi; guest generation markeri `v1.2` ga
# yozilmoqda va u shu yerda ALLAQACHON amalga oshirilgan (o'lchangan
# nosozlik kutib turmaydi).
DRIVER_CONTRACT = "driver-contract/v1.1"
DRIVER_CONTRACT_EXTRA = ("guest_generation_marker (driver-contract/v1.2 "
                         "uchun taklif qilingan)",)

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(PKG_DIR)

# --- run katalogi (shartnoma §1 -- fayl nomlari QAT'IY) ---------------------
EVENTS_FILE = "events.jsonl"
PROBE_FILE = "probe.csv"
PSI_FILE = "psi.csv"
GUARD_FILE = "guard.jsonl"
PRESSURE_FILE = "pressure.jsonl"
RUN_META_FILE = "run_meta.json"
RUN_FILES = (EVENTS_FILE, PROBE_FILE, PSI_FILE, GUARD_FILE, PRESSURE_FILE,
             RUN_META_FILE)
# Guard'ning trip fayli -- O'LCHOV ma'lumoti emas, SIGNAL. Shuning uchun u
# qat'iy olti faylning tashqarisida va alohida nomlanadi.
GUARD_TRIP_FILE = "guard.trip"

# --- unit nomlari (00-pilot-topologiya.md §1) -------------------------------
# Service nomlaridagi dash muammo emas -- faqat SLICE nomlari ierarxiya
# hosil qiladi (01-muhit-tekshiruvlari.md §2, empirik tasdiqlangan).
GUARD_UNIT = "revix-guard.service"
PSI_UNIT = "revix-psi.service"
PROBER_UNIT = "revix-prober.service"
SUT_UNIT = "revix-sut.service"
BYSTANDER_UNIT = "revix-bystander.service"
PRESS_UNIT = "revix-press.service"

LAB_SLICE = U.LAB_SLICE          # revixlab.slice -- o'lchanadigan scope
MON_SLICE = U.MON_SLICE          # revixmon.slice -- harness (HAQIQIY sibling)

# `env_snapshot` va `cgroup_events` scope yorliqlari.
SCOPE_LAB = "lab"
SCOPE_SUT = "sut"
SCOPE_BYSTANDER = "bystander"
SCOPE_PRESS = "press"
SCOPE_MON = "mon"
SCOPE_USER = "user"

# --- muzlatilgan o'lchov konstantalari -------------------------------------
# Bu yerda QAYTA ta'riflanmaydi -- faqat ko'chiriladi, manbasi yonida.
PROBE_PERIOD_US = 100_000        # §2 -- probe davri P = 100 ms (10 Hz)
FAULT_CLASS = "clean_crash"      # §9.3 -- P1 da yagona fault klassi
FAULT_KIND = "exit"              # 03-sut-protokoli.md §5 -- `exit` endpoint'i
FAULT_EXIT_CODE = 1              # §5 jadvali: `code=<int>` (default 1)
SUT_RATE_HZ = 2000               # 03-sut-protokoli.md §4 -- default ish tezligi

# --- P1 arm'lari (§9.3) ----------------------------------------------------
# Baseline B (`RestartSteps=`) P1 da ATAYLAB YO'Q: §9.3 ning sababi --
# B ning `RestartSec=10s` i 12 s xavfsiz pressure oynasidan oshadi.
# `StartLimitBurst=0` IKKALA arm'da (00-pilot-topologiya.md §1).
ARM_PROPERTIES: dict[str, dict[str, Any]] = {
    "A": {"Restart": "on-failure", "RestartSec": "100ms", "StartLimitBurst": 0},
    "no_action": {"Restart": "no", "StartLimitBurst": 0},
}
# `A` arm'ining siyosat kechikishi -- §14.4: `policy_delay_us` `L_dec` dan
# ALOHIDA yoziladi, aks holda sozlangan kutish vaqti "decision latency" deb
# hisoblanib soxta taqqoslash bo'lardi (§6.3).
ARM_POLICY_DELAY_US: dict[str, int | None] = {"A": 100_000, "no_action": None}

# --- pressure bandlari (§9.3) ----------------------------------------------
# §9.3 bandlarni ULUSH oralig'i bilan beradi, nishon RAQAMINI bermaydi.
#
# `P1 = 0.30` -- O'ZGARMADI. 02-guard-kalibratsiyasi.md §4 da erishilgan
# median 0.311 edi; 10-pressure-dozalash.md §3.3 uni BU mashinada qayta
# o'lchadi (13 epizod, epizod medianalarining medianasi 0.2810, xato -0.0190,
# 10/13 band ichida) -- ya'ni kodda turgan qiymat TO'G'RI.
#
# `P2 = 0.60` -- O'LCHANGAN qiymat; band MARKAZI (0.70) EMAS.
# NEGA: 10-pressure-dozalash.md §3.1 nishon->erishilgan xaritasini o'lchadi.
#   nishon 0.70 -> erishilgan p50 **0.8868** -- §9.3 ning 0.60-0.80 bandidan
#                  YUQORI, ya'ni OVER-DOZA (dose-02 `P2a`);
#   nishon 0.60 -> epizod medianalari 0.5726..0.9213, p50 **0.7023**,
#                  11 epizoddan **8 tasi** band ICHIDA (§3.4).
# Xarita CHIZIQLI EMAS va MONOTON HAM EMAS (0.40 -> 0.5253, lekin
# 0.45 -> 0.4833; 0.50 -> 0.5841, lekin 0.55 -> 0.5395), va boshqarish bu
# mashinada 02 §4 ning ±0.08 idan **~5.7× QO'POLROQ** (oniy oraliq 0.03-0.95,
# §3.5 / OQ-3). Demak 0.60 -- shu dial uchun EMPIRIK sozlama; uni mulohaza
# bilan qayta chiqarib olish MUMKIN EMAS. `MemoryHigh` o'zgarsa `base_mb`
# ham, bu nishon ham QAYTA O'LCHANISHI SHART (§3.6 ning tor oynasi, OQ-11).
# ESLATMA: §3.4 `P2` ning band ichida USHLAB TURILISHINI rad etadi (eng uzun
# uzluksiz 1.1 s) -- bu nishon masalasi emas, mexanizmning binarligi (§3.5).
PRESSURE_TARGET_RATE: dict[str, float] = {"P0": 0.0, "P1": 0.30, "P2": 0.60}
PRESSURE_LEVELS = tuple(PRESSURE_TARGET_RATE)

# --- doza dial'i (10-pressure-dozalash.md §2.6 -- O'LCHANGAN) --------------
# Dial generatorga OSHKORA beriladi (dizayn qoidasi 17), `run_pi` ning
# `base = max(16, high_MiB - 2*step_mb)` formulasidan MEROS QILINMAYDI.
#
# §2.2 ning o'lchangan dial sweep'i (`MemoryHigh=192M`, nishon 0.30):
#   step_mb=16 -> base 160 -> erishilgan p50 **0.0000**  (NOL doza, D1)
#   step_mb=8  -> base 176 -> erishilgan p50 0.0138      (D3)
#   step_mb=4  -> base 184 -> erishilgan p50 **0.3344**  (DOZA BOR, D2)
# Arifmetikasi -- generator overhead'i O'LCHANGAN 25.3 MiB (§2.2):
#   160 + 25.3 = 185.3 < 192  -> breach YO'Q      -> stall 0.0000
#   176 + 25.3 = 201.3 > 192  -> kichik overage   -> stall 0.0138
#   184 + 25.3 = 209.3 > 192  -> katta overage    -> stall 0.33
# Ya'ni dozaning haqiqiy knob'i `base_mb` ning `memory.high` dan oshishi
# (§2.4, OQ-1), blok hajmi yoki churn soni EMAS.
#
# Ishchi oyna TOR (§3.6): 184 -- 29 epizodda o'lchangan YAGONA ishlaydigan
# qiymat; 188 to'yinish berib guard'ni URDI
# (`user_full_rate2s_runaway` rate=0.9801962, kill_ok=true);
# 196 da ramp 12.217 s davom etib HOLD fazasi UMUMAN bo'lmadi va
# `ramp_above_threshold_s = 9.500 s` §9.4 invariant 2 ni BUZDI.
# Shuning uchun bu qiymatlar DERIVATSIYA QILINMAYDI, oshkora yoziladi.
PRESSURE_STEP_MB = 4
# `P0` ning bazasi 160 -- bu ATAYLAB nol-doza konfiguratsiyasi: §3.2 da
# generator tirik, 160 MiB rezident, `memory.events high` delta **0** va
# 98 namunada stall aynan 0.0000 (9.8/9.8 s band ichida). §9.3 ning
# "generator idle" sharti shu. `P1`/`P2` uchun 184 -- §2.6 ning dial'i.
PRESSURE_BASE_MB: dict[str, int] = {"P0": 160, "P1": 184, "P2": 184}
# Generator overhead'i, §2.2 da O'LCHANGAN (D1: memory.current max 185.3 MiB,
# touched_mb 160 -> 185.3 - 160 = 25.3 MiB). Bu yerda QAYTA ta'riflanmaydi --
# faqat ko'chiriladi; `base_mb + overhead > MemoryHigh_MiB` breach shartini
# AUDIT QILINADIGAN qiladi (regressiya qulfi shu munosabatni tekshiradi).
PRESSURE_OVERHEAD_MB = 25.3
# `ramp_above_threshold_s` ning O'LCHANGAN qiymati, 10-pressure-dozalash.md
# §4.1 dan KO'CHIRILADI (`PRESSURE_OVERHEAD_MB` bilan bir xil uslub: bu yerda
# QAYTA ta'riflanmaydi, faqat ko'chiriladi). Kalibrlangan dial'da
# (`base_mb=184`, `step_mb=4`, `MemoryHigh=192M`, `MemoryMax=2G`) 29
# epizoddan 29 tasida AYNAN 0.000 s: ramp tezligi min = p50 = max = 0.0000,
# ya'ni §8.4 ning quiescence chegarasi 0.05 dan yuqori birorta namuna YO'Q.
# NEGA bu alohida konstanta va NEGA `schedule.RAMP_ABOVE_THRESHOLD_S` ning
# o'zi yetarli emas: o'sha konstanta REJA, bu esa O'LCHOV. Ikkisini alohida
# saqlab, ularning AYIRMASI (`run_meta` da `plan_slack_s`) hisoblanadi --
# reja o'lchovdan qancha yuqori turgani JIMGINA emas, OSHKORA bo'ladi.
# Bu qiymat ZAXIRA YARATISH uchun kattalashtirilmaydi: avvalgi `3.0` aynan
# shunday (TAXMIN) paydo bo'lgan va §21.7 uni rad etgan.
RAMP_ABOVE_THRESHOLD_MEASURED_S = 0.000
# Control tik'i. §2.6 ning kalibrlangan qiymati 250 ms va u `pressure.py`
# ning hozirgi modul default'i bilan TASODIFAN bir xil -- shuning uchun u
# ham OSHKORA beriladi (dizayn qoidasi 17). NEGA: `step_mb` ning merosi
# nol doza berdi (OQ-2); `interval_ms` ning merosi bugun zararsiz, lekin
# `pressure.py` ning default'i o'zgarsa pilotning control tik'i JIMGINA
# ko'chardi va §3.5 ning duty cycle granularligi (250 ms tik, 2 s PSI
# oynasi, 4 MiB blok) boshqa bo'lib qolardi. Bir xil nuqson klassi.
PRESSURE_INTERVAL_MS = 250

# --- slice dial'lari (00-pilot-topologiya.md §1) ---------------------------
LAB_SLICE_PROPERTIES: dict[str, Any] = {
    "MemoryMax": "2G",           # kernel darajasidagi umumiy anonim shift
    "CPUQuota": "400%",          # desktop CPU starvation'dan himoya (12 yadro)
    "TasksMax": 256,             # fork bomb
}
MON_SLICE_PROPERTIES: dict[str, Any] = {
    # Harness'ning o'zi cheklanadi, lekin KENG: guard o'lishi mumkin emas.
    "MemoryMax": "512M",
    "TasksMax": 64,
}
# `MemoryHigh` -- PI controller'ning throttling chegarasi. 192M qiymati
# 02-guard-kalibratsiyasi.md §3 da O'LCHANGAN (high=192M, baza=184M, ramp
# tezligi median 0.000). U o'sha yerda `MemoryMax=1G` bilan o'lchangan edi.
# 10-pressure-dozalash.md §2.2 uni `MemoryMax=2G` ostida QAYTA o'lchadi va
# `192M` ning `base=184` juftligi qayta ishlab chiqarildi -- ya'ni `08` §12
# OQ-4 YOPILDI: nol doza `MemoryMax` ning artefakti EMAS, u `base_mb` dan
# keladi (§2.2 TALQIN). `calibration_required` SHUNDAY QOLADI, lekin sababi
# BOSHQA: OQ-11 -- `MemoryHigh` ning O'ZI optimallashtirilmagan, boshqa
# qiymatlari o'lchanmagan, va ishchi `base_mb` oynasi TOR (§3.6), demak
# boshqa `MemoryHigh` da `base_mb` QAYTADAN topilishi kerak bo'ladi.
# MUZLATILGAN: bu qiymat 00-pilot-topologiya.md §1 ga tegishli, bu yerda
# o'zgartirilmaydi.
DEFAULT_MEMORY_HIGH = "192M"

# Monitoring unit'lari uchun cheklovlar (scripts/guard-test.sh da ishlatilgan
# va tasdiqlangan qiymatlar).
MON_UNIT_MEMORY_MAX = "128M"
# Generator cheklovlari (00-pilot-topologiya.md §1).
PRESS_MEMORY_MAX = "1536M"       # 1.5G

# Muzlatilmagan, shuning uchun flag: §9.2 (i) `TimeoutStartSec` va (iv)
# watchdog miss -- IKKISI HAM oldindan aytilgan MEXANIZM. Ularning qiymati
# natijaga ta'sir qiladi, demak jimgina tanlanmaydi.
DEFAULT_WATCHDOG_SEC = "5s"
DEFAULT_TIMEOUT_START_SEC = "10s"

# Washout kuzatuvi uchun PSI namuna davri. §7/§8.4: tezlik oynasi >=2 s
# bo'lishi SHART (`cgroup.stall_fraction` <2 s da None qaytaradi), shuning
# uchun namuna davri 0.5 s va oyna >=2 s tanlanadi.
WASHOUT_POLL_S = 0.5
WASHOUT_RATE_WINDOW_US = 2_000_000

# Faza tsiklining drenaj davri: unit_state record'lari shu kadensda
# buferdan olinadi va yoziladi.
DRAIN_PERIOD_S = 0.05

# systemd job va `active` kutish chegaralari (o'lchov yo'lida EMAS).
JOB_TIMEOUT_S = 30.0
ACTIVE_TIMEOUT_S = 15.0

ARMED_RE = re.compile(r"^OK\s+armed=(\S+)")
# `OK progress=.. pid=.. invocation=.. rss_kb=.. mono_us=..` (protokol §3).
SUT_MONO_RE = re.compile(r"\bmono_us=(\d+)\b")


def _parse_sut_mono(reply: str | None) -> int | None:
    """SUT javobidan uning O'Z `mono_us` ini oladi (protokol §3).

    `mono_us` protokolda IXTIYORIY maydon (`prober.parse_probe_reply` uni
    talab qilmaydi), shuning uchun yo'q bo'lsa `None` -- o'lchanmadi, nol
    EMAS.
    """
    if not reply:
        return None
    m = SUT_MONO_RE.search(reply)
    return int(m.group(1)) if m else None


# ===========================================================================
# Xatolar
# ===========================================================================


class DriverError(RuntimeError):
    """Driver'ning barcha xatolari uchun asos."""


class RunDirExistsError(DriverError):
    """Run katalogi allaqachon mavjud -- `datasets/` append-only."""


class GuardStartError(DriverError):
    """Guard ishga tushmadi -> run BOSHLANMAYDI (majburiyat 2, fail-closed)."""


class PressureNotAllowedError(DriverError):
    """Pressure `--allow-pressure` bo'lmaganda talab qilindi.

    00-pilot-topologiya.md §6: guard tasdiqlanishi (qadam 3) pressure dosing
    kalibratsiyasidan (qadam 4) OLDIN bo'lishi SHART. "Retrofit qilinmaydi."
    """


class ZeroDoseError(DriverError):
    """Dial nol doza beradi -> run BOSHLANMAYDI (majburiyat 4, fail-closed).

    10-pressure-dozalash.md §2.2 ning arifmetikasi: doza FAQAT
    `base_mb + overhead > MemoryHigh_MiB` bo'lganda yetkaziladi. Shart
    buzilsa generator tirik, rezident va JIM bo'ladi -- erishilgan stall
    aynan 0.0000 (§2.2 D1, 114 namuna).

    NEGA OGOHLANTIRISH EMAS, XATO: nol doza bilan run ~2.5 soat ishlaydi va
    oxirida null beradi; o'sha null H1 ga qarshi dalilga AYNAN O'XSHAYDI,
    lekin u asbob nuqsoni (§2.5, PREREGISTRATION.md §9.2 ning analogi).
    `--memory-high` RUNTIME bayrog'i, demak regressiya testi `--memory-high
    256M` ni tutib qolmaydi: 184+25.3 = 209.3 < 256 -> breach YO'Q. Bu
    teshikni faqat run'ning HAQIQIY `MemoryHigh` idan hisoblangan pre-flight
    yopadi. Posture `guard.py` va `units.require_clean()` bilan bir xil.

    NEGA PER-TRIAL EMAS, RUN DARAJASIDA: trial ichidagi istisno har pressure
    trial'ini `harness_error` disposition'iga aylantirardi (qoida 13), ya'ni
    konfiguratsiya nuqsoni 120 ta eksklyuziyaga va asbob tomonidan
    boshqariladigan eksklyuziya tezligiga aylanardi -- §12 ning butun
    maqsadiga zid.
    """


class PreregistrationMissingError(DriverError):
    """`PREREGISTRATION.md` o'qilmadi -> run'ni ta'riflarga bog'lab bo'lmaydi.

    §14.4 `preregistration_sha256` ni MAJBURIY deb beradi. Hash'siz run
    "qaysi ta'riflar ostida o'lchangani" ni aytib bermaydi, demak u ilmiy
    jihatdan qiymatsiz -- shuning uchun bu ogohlantirish emas, xato.
    """


class OnlyFilterError(DriverError):
    """`--only` spetsifikatsiyasi jadvalga mos kelmadi (fail-closed)."""


class GuestRestartError(DriverError):
    """Guest (WSL) qayta ishga tushdi -> kampaniya DARHOL to'xtaydi.

    NEGA BU ALOHIDA XATO VA NEGA U FATAL: bu mashinada o'lchangan (envcheck)
    -- WSL distro'si oxirgi klient chiqqandan ~10-15 s keyin to'xtaydi va
    qayta ko'tarilganda `CLOCK_MONOTONIC` NOLGA QAYTADI, lekin
    `/proc/sys/kernel/random/boot_id` O'ZGARMAYDI.

    PREREGISTRATION.md §1 barcha davomiylikni `CLOCK_MONOTONIC` da
    muzlatgan va `boot_id` ni "monotonic qiymatlar faqat bitta boot ichida
    taqqoslanadi" shartining YAGONA tekshiruvi deb bergan; §14.6 invariant 5
    aynan shu. Guest restart'i bu himoyani BUTUNLAY chetlab o'tadi: barcha
    davomiylik ma'nosiz bo'ladi va HECH BIR mavjud invariant buni ko'rmaydi.
    Ya'ni bu eng yomon turdagi nosozlik -- VALIDATSIYADAN O'TADIGAN,
    JIMGINA YOLG'ON raqamlar.

    Shuning uchun PID 1 ning `starttime` i alohida "guest generation"
    markeri sifatida `run_meta` ga VA har `env_snapshot` ga yoziladi, va
    uning o'zgarishi run'ni to'xtatadi: restart'dan keyingi ma'lumotni
    undan oldingisiga QO'SHIB BO'LMAYDI.
    """


# ===========================================================================
# 1. SOF YORDAMCHILAR -- systemd, cgroup va soat TALAB QILMAYDI
# ===========================================================================
#
# NEGA ALOHIDA: bu funksiyalar o'lchov validligini belgilaydi (T_trial,
# field nomlari, jadval filtri), demak ularni ARZON va TO'LIQ sinash kerak.
# Agar ular Platform ichida bo'lsa, ularni faqat haqiqiy systemd'li
# mashinada sinab ko'rish mumkin bo'lardi. Bu `schedule.py` bilan bir xil
# usul.


T_TRIAL_FORMULA = (
    "T_trial = TrialTimeline.t_pressure_off + TrialTimeline.w_stab_s + P   "
    "(P = probe davri 100 ms, PREREGISTRATION.md §2); "
    "invariant: t_verify_end_earliest <= T_trial <= total_s"
)


def t_trial_us(
    timeline: sch.TrialTimeline, probe_period_us: int = PROBE_PERIOD_US
) -> int:
    """Recovery horizon `T_trial`, mikrosekund (`driver-contract/v1.1` §5.4).

    PREREGISTRATION.md `T_trial` uchun RAQAM BERMAYDI, lekin censoring (§6.2),
    `loop_rate` (§6.4) va `censored` disposition (§12) unga tayanadi. Shuning
    uchun u MUZLATILGAN timeline xususiyatlaridan HISOBLANADI, hech qachon
    jimgina konstanta sifatida yozilmaydi:

        T_trial = t_pressure_off + w_stab_s + P

    NEGA shunday:
      * `t_pressure_off` -- VR oynasining ENG KECH qonuniy BOSHLANISHI: §9.4
        analizni ERISHILGAN pressure ustida qurgan, demak pressure o'chgandan
        keyin boshlangan `t_up` treatment ta'sirini yo'qotgan bo'ladi.
      * `+ w_stab_s` -- §4 oynaning TO'LIQ kuzatilishini talab qiladi. Kesilgan
        oyna `reduce.evaluate_vr` da `vr=None, reason="window_truncated"`
        beradi, va `None` hech qachon `False` ga aylantirilmaydi (§5 Kleene
        mantiqi). Ya'ni qisqa horizon eksperimentni jimgina "aniqlanmagan" ga
        aylantirardi -- null natija emas, NATIJASIZLIK.
      * `+ P` -- `reduce.Params.window_slack_us` aynan bitta probe davri
        bo'sh joy beradi, va §6.1 probe kvantlashini (+-P) OCHIQ e'lon qilgan.

    Invariant TEKSHIRILADI va buzilsa ISTISNO (ogohlantirish emas): horizon
    `t_verify_end_earliest` dan qisqa bo'lsa ENG ERTA oyna ham sig'maydi;
    `total_s` dan uzun bo'lsa horizon washout ichiga kirib, bizning O'Z
    `cgroup.kill` imiz o'lchov ichida ko'rinardi.
    """
    value = round((timeline.t_pressure_off + timeline.w_stab_s) * 1e6) + probe_period_us
    lo = round(timeline.t_verify_end_earliest * 1e6)
    hi = round(timeline.total_s * 1e6)
    if not (lo <= value <= hi):
        raise DriverError(
            f"T_trial={value} us invariantni buzdi: "
            f"t_verify_end_earliest={lo} us <= T_trial <= total_s={hi} us "
            f"({T_TRIAL_FORMULA})"
        )
    return value


def t_recovery_window_us(
    timeline: sch.TrialTimeline, probe_period_us: int = PROBE_PERIOD_US
) -> int:
    """Injeksiyadan horizon oxirigacha kuzatilgan vaqt (ma'lumot sifatida).

    `T_trial` trial BOSHIDAN o'lchanadi (shunda `reduce.Trial.t_trial_us` =
    `trial_end.mono_us - trial_begin.mono_us` bo'ladi). Bu yordamchi esa
    fault'dan KEYINGI kuzatuv oynasini beradi -- §4 ning "oyna sig'adimi"
    savoli aynan shu qiymatga tegishli.
    """
    return t_trial_us(timeline, probe_period_us) - round(timeline.t_inject * 1e6)


def parse_only(spec: str | None) -> tuple[str, ...]:
    """`--only P0,A` -> `("P0", "A")`. Bo'sh token tashlanadi."""
    if not spec:
        return ()
    return tuple(t.strip() for t in spec.split(",") if t.strip())


def select_trials(
    schedule: sch.Schedule, only: Sequence[str] = ()
) -> tuple[sch.Trial, ...]:
    """`--only` filtri: KESISHMA semantikasi (barcha token mos kelishi SHART).

    `--only P0,A` -> faqat `(arm=A, pressure_level=P0)` yacheykasi, ya'ni
    smoke trial'lar. FAIL-CLOSED ikki joyda:
      * jadvalda umuman bo'lmagan token -> `OnlyFilterError`;
      * filtr natijasi bo'sh -> `OnlyFilterError`.
    Busiz nima buzilardi: imlo xatosi (`--only p0`) jimgina NOL trial'lik
    run yaratib, "run tugadi" deb ko'rinardi.

    Jadvalning O'ZI o'zgarmaydi: `run_meta.schedule` va `schedule_digest`
    HAR DOIM to'liq jadvalga tegishli, shunda randomizatsiya tekshirilishi
    mumkin bo'ladi (§8.4). Filtr alohida yoziladi.
    """
    if not only:
        return schedule.trials
    known: set[Any] = set()
    for f in schedule.factors:
        known.update(f.levels)
    unknown = [t for t in only if t not in known]
    if unknown:
        raise OnlyFilterError(
            f"--only da jadvalda yo'q daraja(lar): {unknown}; "
            f"mavjud darajalar: {sorted(map(str, known))}"
        )
    out = tuple(
        t for t in schedule.trials if all(tok in t.cell for tok in only)
    )
    if not out:
        raise OnlyFilterError(
            f"--only {list(only)} hech bir yacheykaga mos kelmadi "
            "(darajalar turli faktorlardan bo'lishi kerak)"
        )
    return out


def prepare_run_dir(path: str) -> str:
    """Run katalogini YARATADI. Mavjud bo'lsa -- XATO (shartnoma §1).

    `os.makedirs(exist_ok=False)`: `datasets/` append-only (CONTRIBUTING.md
    §1.4). Mavjud katalogga yozish ikki run'ning `events.jsonl` ini
    aralashtirib, `seq` oqimlarini buzardi va `boot_id` invariantini
    (§14.6 invariant 5) yolg'on qilardi.
    """
    full = os.path.abspath(path)
    if os.path.exists(full):
        raise RunDirExistsError(
            f"run katalogi allaqachon mavjud: {full} -- datasets/ append-only "
            "(CONTRIBUTING.md §1.4); yangi katalog nomini bering"
        )
    os.makedirs(full, exist_ok=False)
    return full


def preregistration_info(repo_root: str = REPO_ROOT) -> dict[str, Any]:
    """`PREREGISTRATION.md` ning sha256'i va versiya satri (§14.4 MAJBURIY).

    Hash FAYL BAYTLARIDAN olinadi (matn normalizatsiyasi YO'Q): normalizatsiya
    qilsak, satr oxiri o'zgargan fayl bir xil hash berib, "qaysi ta'riflar
    ostida" savoliga yolg'on javob bo'lardi.
    """
    path = os.path.join(repo_root, "PREREGISTRATION.md")
    try:
        with open(path, "rb") as fh:
            blob = fh.read()
    except OSError as exc:
        raise PreregistrationMissingError(
            f"PREREGISTRATION.md o'qilmadi ({path}): {exc!r}. "
            "§14.4 `preregistration_sha256` ni MAJBURIY deb beradi."
        ) from exc
    version = None
    m = re.search(rb"\|\s*\*\*Versiya\*\*\s*\|\s*`([^`]+)`", blob)
    if m:
        version = m.group(1).decode("utf-8", "replace")
    return {
        "preregistration_path": os.path.relpath(path, repo_root),
        "preregistration_sha256": hashlib.sha256(blob).hexdigest(),
        "preregistration_version": version,
        "preregistration_bytes": len(blob),
    }


def parse_guest_generation(
    pid1_stat: str | None, uptime: str | None, clk_tck: int = 100
) -> dict[str, Any]:
    """PID 1 ning `starttime` idan "guest generation" markerini yasaydi.

    `/proc/1/stat` ning 22-maydoni (`starttime`) -- PID 1 boot'dan keyin
    necha clock tick'da ishga tushgani; `/proc/uptime` esa guest'ning
    joriy yoshini beradi. Guest qayta ko'tarilganda `pid1_boot_age_s`
    (uptime - starttime/CLK_TCK) va `uptime_s` IKKISI HAM nolga qaytadi,
    `boot_id` esa O'ZGARMAYDI.

    IDENTIKLIK KALITI -- `pid1_starttime_ticks`, VA FAQAT U. `uptime_s` ham
    yoziladi (inson o'qishi uchun), lekin taqqoslashga KIRMAYDI: u har
    sekundda o'zgaradi, demak uni identiklikka qo'shish doimiylik
    tekshiruvini HAR TRIAL'da soxta ravishda yiqitardi. `validate.py`
    tomoni ham aynan shu kalitni taqqoslaydi -- ikki tomon bir-biridan
    uzoqlashmasligi uchun nom AYNAN shunday.

    O'qib bo'lmasa `None` (o'lchanmadi, nol EMAS) va `comparable=False` --
    fail-closed: taqqoslanmaydigan marker bilan "o'zgarmadi" degan xulosa
    chiqarilmaydi.

    `pid1_stat` ning 2-maydoni (comm) qavs ichida va BO'SH JOY tutishi
    mumkin, shuning uchun parse OXIRGI ')' dan keyin bo'linadi -- aks holda
    maydon indekslari siljib ketardi.
    """
    out: dict[str, Any] = {
        "pid1_starttime_ticks": None,
        "uptime_s": None,
        "pid1_starttime_s": None,
        "generation": None,
        "comparable": False,
        "clk_tck": clk_tck,
        "identity_key": "pid1_starttime_ticks",
    }
    if uptime:
        try:
            out["uptime_s"] = float(uptime.split()[0])
        except (ValueError, IndexError):
            out["uptime_s"] = None
    if pid1_stat:
        idx = pid1_stat.rfind(")")
        tail = pid1_stat[idx + 1:].split() if idx >= 0 else []
        # stat maydonlari 1-asosli; comm'dan keyingi birinchi maydon 3 (state),
        # demak `starttime` (22) = tail[22 - 3] = tail[19].
        if len(tail) > 19 and clk_tck > 0:
            try:
                ticks = int(tail[19])
            except ValueError:
                ticks = None
            if ticks is not None:
                out["pid1_starttime_ticks"] = ticks
                out["pid1_starttime_s"] = ticks / float(clk_tck)
    if out["pid1_starttime_ticks"] is not None:
        out["generation"] = f"pid1:{out['pid1_starttime_ticks']}"
        out["comparable"] = True
    return out


def guest_generation_changed(
    before: dict[str, Any], after: dict[str, Any]
) -> tuple[bool, str]:
    """Marker o'zgardimi (FAIL-CLOSED).

    Taqqoslanadigan YAGONA kalit -- `pid1_starttime_ticks`. `uptime_s`
    ATAYLAB e'tiborga olinmaydi: u har sekundda o'sadi, demak uni
    taqqoslashga qo'shish har trial'da soxta "o'zgardi" berardi.

    Taqqoslab bo'lmasa (`comparable=False` yoki kalit `None`) -> "o'zgardi"
    DEB HISOBLANADI. Sabab guard'ning 3-qoidasi bilan bir xil: o'qilmagan
    kuzatuv "yaxshi" deb hisoblanmaydi. Guest restart'i jimgina yolg'on
    raqam beradi, demak noaniqlik to'xtatish tomoniga hal qilinadi.
    """
    key = "pid1_starttime_ticks"
    if not before.get("comparable") or not after.get("comparable"):
        return True, "guest_generation_unreadable"
    if before.get(key) is None or after.get(key) is None:
        return True, "guest_generation_unreadable"
    if before.get(key) != after.get(key):
        return True, "pid1_starttime_changed"
    return False, "unchanged"


def _none_if_empty(value: Any) -> Any:
    """Bo'sh to'plam/satrni `None` ga aylantiradi (`None` = O'LCHANMADI).

    NEGA KERAK: `cli.check_cpu_governor()` bu mashinada `{"governors": [],
    "drivers": [], "cpu_count": 0}` beradi -- `doctor` konteksida bu
    to'g'ri ("nol CPU cpufreq interfeysini ko'rsatadi"), LEKIN
    `run_meta.governor` boshqa savolga javob beradi: "run davomida qaysi
    governor kuchda edi". Bu mashinada o'lchangan javob -- O'LCHANMADI
    (`/sys/.../cpufreq` yo'q, `thermal_zone*` yo'q). Bo'sh ro'yxat yoki `0`
    esa O'LCHOV kabi o'qilardi, ya'ni to'qima bo'lardi
    (PREREGISTRATION.md §15.4, §8.5).
    """
    if value is None:
        return None
    if isinstance(value, (list, tuple, set, dict, str)) and len(value) == 0:
        return None
    return value


def _ts_or_none(value: Any) -> int | None:
    """systemd monotonic timestamp'ini normalizatsiya qiladi.

    systemd qo'yilmagan timestamp uchun `0`, cheksizlik uchun `UINT64_MAX`
    beradi. IKKISI HAM o'lchov EMAS, demak `None`.
    Busiz nima buzilardi: `reduce.compute_d_sd` `UINT64_MAX` ni haqiqiy
    `ActiveExit` vaqti deb olib, downtime'ni astronomik qilardi.
    """
    if value is None:
        return None
    try:
        v = int(value)
    except (TypeError, ValueError):
        return None
    if v == 0 or v >= U.UINT64_MAX:
        return None
    return v


# `unit_state` payload'idagi snake_case alias'lar -> systemd property nomlari.
# NEGA ALIAS KERAK: `units.UnitWatcher` XOM systemd nomlarini beradi
# (`ActiveState`, `NRestarts`, ...), lekin `reduce.py` ISH VAQTIDA snake_case
# nomlarni o'qiydi: `active_state` (reduce.py:886), `n_restarts`
# (reduce.py:770, :1523), `invocation_id` (reduce.py:1520),
# `active_enter_ts_mono_us` / `active_exit_ts_mono_us` (reduce.py:1341-1342).
# Alias bo'lmasa `compute_d_sd` NOL downtime, `evaluate_vr` ning 4-bandi
# "tekshirilmagan" bo'lib qolardi -- ya'ni JIMGINA o'lchov yo'qolishi.
# XOM nomlar HAM saqlanadi (`systemd` kalitida): §1 systemd'ning O'Z
# `*TimestampMonotonic` qiymatlarini AVTORITET deb beradi.
UNIT_STATE_ALIASES: tuple[tuple[str, str], ...] = (
    ("active_state", "ActiveState"),
    ("sub_state", "SubState"),
    ("result", "Result"),
    ("n_restarts", "NRestarts"),
    ("invocation_id", "InvocationID"),
    ("active_enter_ts_mono_us", "ActiveEnterTimestampMonotonic"),
    ("active_exit_ts_mono_us", "ActiveExitTimestampMonotonic"),
    ("inactive_enter_ts_mono_us", "InactiveEnterTimestampMonotonic"),
    ("inactive_exit_ts_mono_us", "InactiveExitTimestampMonotonic"),
    ("state_change_ts_mono_us", "StateChangeTimestampMonotonic"),
    ("exec_main_start_ts_mono_us", "ExecMainStartTimestampMonotonic"),
    ("exec_main_exit_ts_mono_us", "ExecMainExitTimestampMonotonic"),
)
UNIT_STATE_TS_ALIASES = tuple(
    a for a, _ in UNIT_STATE_ALIASES if a.endswith("_mono_us")
)
UNIT_STATE_PLAIN_ALIASES: tuple[tuple[str, str], ...] = (
    ("exec_main_pid", "ExecMainPID"),
    ("exec_main_code", "ExecMainCode"),
    ("exec_main_status", "ExecMainStatus"),
)

# `siginfo` kodlari (`ExecMainCode`): 1=CLD_EXITED, 2=CLD_KILLED, 3=CLD_DUMPED.
CLD_KILLED = 2
SIGKILL = 9


def unit_state_payload(raw: dict[str, Any], scope: str) -> dict[str, Any]:
    """`units.UnitWatcher` record'ini `unit_state` payload'iga aylantiradi.

    Qaytadigan payload'da UCHALASI ham bor:
      * snake_case alias'lar -- `reduce.py` ish vaqtida o'qiydigan nomlar
        (normalizatsiya qilingan: bo'sh timestamp -> `None`);
      * XOM systemd nomlari, `U.STATE_PROPS` ning hammasi, AYNAN systemd
        bergandek -- §1 bo'yicha ular AVTORITET qiymatlar. Ular record'ning
        YUQORI DARAJASIDA turadi (ichki dict'da EMAS): `validate.py` ning
        `RECORD_FIELD_RULES[unit_state]` aynan `ActiveEnterTimestampMonotonic`
        va `ActiveExitTimestampMonotonic` kalitlarini RECORD'da qidiradi, va
        ichki dict'ga yashirish ularni "yo'q" qilardi.
      * `recv_mono_us` ALOHIDA -- §14.4: harness qabul vaqti systemd'ning
        o'z vaqtidan alohida qolishi SHART, aks holda D-Bus yetkazish
        kechikishi o'lchov ichida yashirinib `L_det`/`D_sd` ni buzardi.

    Envelope field'lari (`trial_id`, `block_index`, `mono_us`, `real_us`, ...)
    payload'ga QO'YILMAYDI -- `Emitter.record()` to'qnashuvda istisno tashlaydi
    (schema.py:236). systemd nomlari CamelCase, demak to'qnashuv yo'q.
    """
    out: dict[str, Any] = {
        "unit": raw.get("unit"),
        "scope": scope,
        "recv_mono_us": raw.get("recv_mono_us"),
        "recv_real_us": raw.get("recv_real_us"),
        "signal_iface": raw.get("signal_iface"),
        "changed_props": raw.get("changed_props"),
        "changed_count": raw.get("changed_count"),
        "snapshot_complete": raw.get("snapshot_complete"),
        "missing_props": raw.get("missing_props"),
    }
    # XOM qiymatlar BIRINCHI va YUQORI DARAJADA: normalizatsiya QILINMAYDI,
    # aynan systemd bergandek (§1 -- AVTORITET baza).
    for prop in U.STATE_PROPS:
        out[prop] = raw.get(prop)
    for alias, prop in UNIT_STATE_ALIASES:
        v = raw.get(prop)
        out[alias] = _ts_or_none(v) if alias.endswith("_mono_us") else v
    for alias, prop in UNIT_STATE_PLAIN_ALIASES:
        out[alias] = raw.get(prop)
    return out


def unsolicited_kill_seen(payload: dict[str, Any]) -> bool:
    """`unit_state` payload'i BIZ YUBORMAGAN `SIGKILL` ni ko'rsatadimi (§12).

    Driver horizon ICHIDA hech qachon `SIGKILL` yubormaydi: bizning yagona
    kill'imiz washout'ning `cgroup.kill` i va u horizon TUGAGANDAN KEYIN
    bo'ladi (§8.4 qadam 1). Shuning uchun horizon ichidagi `CLD_KILLED/9`
    bizdan EMAS -> `contaminated`.
    """
    try:
        code = int(payload.get("exec_main_code") or 0)
        status = int(payload.get("exec_main_status") or 0)
    except (TypeError, ValueError):
        return False
    return code == CLD_KILLED and status == SIGKILL


def _events_delta(before: dict[str, int], after: dict[str, int]
                  ) -> dict[str, Any]:
    keys = sorted(set(before) | set(after))
    return {
        "memory_events": {k: int(after.get(k, 0)) for k in keys},
        "memory_events_before": {k: int(before.get(k, 0)) for k in keys},
        "memory_events_delta": {
            k: int(after.get(k, 0)) - int(before.get(k, 0)) for k in keys},
    }


def cgroup_events_payload(
    before: dict[str, dict[str, int]],
    after: dict[str, dict[str, int]],
    *,
    scope: str = SCOPE_SUT,
) -> dict[str, Any]:
    """`cgroup_events` payload'i -- `memory.events` delta'lari (§1.2).

    TRIAL'GA AYNAN BITTA RECORD, va u AYNAN SUT scope'iga tegishli. Sabab
    ikkita, ikkisi ham majburlangan:

      1. `reduce._oom_series(trial)` SCOPE FILTRISIZ chaqiriladi
         (reduce.py:780) va `oom_kill` kalitiga ega BARCHA `cgroup_events`
         record'larini BITTA kumulyativ qatorga qo'shadi. Har scope uchun
         alohida record yozilsa, qator lab/sut/bystander manbalaridan
         aralashib, `v > prev` taqqoslashi ma'nosiz bo'lardi -- ya'ni §4
         ning 6-bandi (`oom_kill` invalidator'i) YOLG'ON ishlardi.
      2. `validate.RECORD_FIELD_RULES[cgroup_events]` `oom_kill` ni HAR
         record'da NOL BO'LMAGAN qiymat sifatida talab qiladi, demak
         "bu scope'da kalit yo'q" yechimi ham o'tmaydi.

    Boshqa scope'lar YO'QOLMAYDI: ularning kumulyativ qiymatlari va
    delta'lari shu record'ning `other_scopes` kalitida, va to'liq
    `memory.stat`/`cpu.stat` bilan birga har trial chegarasidagi
    `env_snapshot` da (§8.3 kovariatalari). `other_scopes` ichidagi
    `oom_kill` `_oom_series` uchun KO'RINMAYDI, chunki u faqat yuqori
    darajadagi kalitni o'qiydi.
    """
    payload: dict[str, Any] = {"scope": scope}
    payload.update(_events_delta(before.get(scope, {}), after.get(scope, {})))
    payload["oom_kill"] = int(after.get(scope, {}).get("oom_kill", 0))
    payload["oom_kill_delta"] = payload["memory_events_delta"].get("oom_kill", 0)
    payload["other_scopes"] = {
        s: _events_delta(before.get(s, {}), after.get(s, {}))
        for s in sorted(set(before) | set(after)) if s != scope
    }
    return payload


def normalise_probe_row(row: dict[str, Any]) -> dict[str, Any]:
    """`probe.csv` qatorini reducer KIRISH chegarasida moslashtiradi.

    MUAMMO (va nega bu eng xavfli field nomi): `prober.py` ustunni
    `progress_counter` deb yozadi (prober.py:153) -- va PREREGISTRATION.md
    §14.4 AYNAN shu nomni majburiy deb MUZLATGAN. Lekin
    `reduce.probe_from_record` `rec.get("progress")` ni o'qiydi
    (reduce.py:298). Moslashtirilmasa:
        `Probe.progress is None` -> `window_throughput()` -> None
        -> `R_ref` yo'q -> `evaluate_vr()` -> `vr=None,
           reason="r_ref_unavailable"` HAR TRIAL uchun
        -> birlamchi endpoint (§11) hisoblanmaydi -> pilot QIYMATSIZ.

    Nega moslashtirish SHU YERDA: xom `probe.csv` ustun nomlari muzlatilgan va
    `datasets/` append-only (CONTRIBUTING.md §1.4), demak faylni tahrirlash
    TAQIQLANGAN. `reduce.py` ham tahrirlanmaydi. Qoladigan yagona to'g'ri joy
    -- reducer KIRISHIDAGI driver'ga tegishli adapter:

        rows   = reduce.load_probe_csv(path)          # xom, tegilmagan
        probes = [driver.normalise_probe_row(r) for r in rows]
        run    = reduce.RawRun(records=..., probes=probes, sources=[...])

    Adapter `progress` ni QO'SHADI, `progress_counter` ni SAQLAYDI, mavjud
    `progress` ni HECH QACHON bosib o'tmaydi va HECH BIR QIYMATNI
    O'ZGARTIRMAYDI.
    """
    out = dict(row)
    if out.get("progress") in (None, ""):
        pc = out.get("progress_counter")
        if pc not in (None, ""):
            out["progress"] = pc
    return out


def normalise_probe_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """`normalise_probe_row` ning ro'yxat shakli."""
    return [normalise_probe_row(r) for r in rows]


# Reducer KIRISHIDA faqat SHU target/unit qoladi. Qiymatlar `prober.py` ning
# `--target sut=...` yorligi va `revix-sut.service` nomi bilan bir xil.
REDUCER_PROBE_TARGET = "sut"
REDUCER_UNIT = SUT_UNIT


def reducer_input(
    records: Iterable[dict[str, Any]],
    probe_rows: Iterable[dict[str, Any]],
    *,
    target: str = REDUCER_PROBE_TARGET,
    unit: str = REDUCER_UNIT,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Xom oqimlarni reducer KIRISHIGA moslashtiradi: SUT'ga FILTRLAYDI.

    MUAMMO (jimgina korruptsiya): `reduce.split_trials` probe'larni FAQAT
    `trial_id` bo'yicha guruhlaydi (reduce.py:453) va `unit_state` ni ham
    faqat trial bo'yicha (reduce.py:488). Lekin §8.2 har trial'da
    BYSTANDER'ni ham probe qilishni talab qiladi (spillover detektori),
    demak `probe.csv` da IKKI target, `events.jsonl` da esa IKKI unit
    bo'ladi. Filtrsiz berilsa:
      * bystander probe'lari SUT'ning throughput qatoriga tushadi ->
        `R_ref`, `D_probe`, `D_eff` buziladi;
      * bystander'ning `NRestarts` / `InvocationID` SUT'ning qiymatlariga
        aralashadi -> §4 ning 3- va 4-bandlari (VR invalidator'lari)
        yolg'on ishlaydi.
    Ya'ni BIRLAMCHI ENDPOINT boshqa xizmatdan hisoblanardi.

    NEGA XOM OQIM BARIBIR IKKALASINI SAQLAYDI (va saqlashi SHART):
    bystander trace'i §12 ning `contaminated` disposition'i uchun DALIL va
    keyinchalik §5 ning `harm_indicator` ta'rifi uchun yagona manba;
    `datasets/` esa append-only (CONTRIBUTING.md §1.4), demak xom faylni
    filtrlab qayta yozish TAQIQLANGAN. Shuning uchun filtr AYNAN shu yerda
    -- reducer kirishida, xom ma'lumotga TEGMASDAN.

    `target` va `unit` qatorlarda QOLADI, shunda filtr tekshirilishi mumkin
    (yashirin emas). Ishlatilishi:

        recs  = reduce.load_jsonl(f"{run}/events.jsonl")
        rows  = reduce.load_probe_csv(f"{run}/probe.csv")
        r, p  = driver.reducer_input(recs, rows)
        run_  = reduce.RawRun(records=r, probes=p, sources=[...])
    """
    out_probes: list[dict[str, Any]] = []
    for row in probe_rows:
        t = row.get("target")
        # `target` yo'q bo'lsa qator TASHLANMAYDI: eski/boshqa manbadagi
        # CSV'da ustun bo'lmasligi mumkin, va jimgina tashlash ma'lumot
        # yo'qotish bo'lardi. Faqat ANIQ boshqa target chiqariladi.
        if t in (None, "", target):
            out_probes.append(normalise_probe_row(row))
    out_records: list[dict[str, Any]] = []
    for rec in records:
        if rec.get("record_type") == "unit_state":
            u = rec.get("unit")
            if u not in (None, "", unit):
                continue
        out_records.append(rec)
    return out_records, out_probes


def check_restart_steps_pairing(props: dict[str, Any]) -> None:
    """`RestartSteps=` va `RestartMaxDelaySec=` JUFTLIGINI majburlaydi.

    O'LCHANGAN TUZOQ (systemd 257, envcheck): `RestartSteps=` ni
    `RestartMaxDelaySec=` siz qo'ysa systemd uni QABUL QILADI,
    `systemctl show` uni QAYTARADI, lekin systemd uni ISHLATMAYDI --
    journal'da "Service has RestartSteps= but no RestartMaxDelaySec=
    setting. Ignoring." va interval 1.03 s da qoladi.

    Ya'ni property KUCHDA DEK O'QILADI, lekin hech narsa qilmaydi. Bu
    01-muhit-tekshiruvlari.md §4 hujjatlashtirgan sinfning IKKINCHI misoli:
    `systemctl show` YOLG'ON gapiradi. Shuning uchun juftlik KODDA
    majburlanadi, read-back'ga ISHONILMAYDI.

    P1 Baseline B ni ishlatmaydi (§9.3), lekin confirmatory eksperiment
    ishlatadi -- va o'sha paytda bu tekshiruv jimgina yo'qolgan backoff
    siyosatini oldini oladi.
    """
    has_steps = "RestartSteps" in props
    has_max = any(k in props for k in
                  ("RestartMaxDelaySec", "RestartMaxDelayUSec"))
    if has_steps != has_max:
        raise DriverError(
            "RestartSteps= va RestartMaxDelaySec= FAQAT JUFT ishlatiladi: "
            f"RestartSteps={'bor' if has_steps else 'yo`q'}, "
            f"RestartMaxDelaySec={'bor' if has_max else 'yo`q'}. "
            "systemd 257 bittasini jimgina E'TIBORSIZ qoldiradi, lekin "
            "`systemctl show` uni baribir ko'rsatadi (o'lchangan)."
        )


def arm_properties(arm: str) -> dict[str, Any]:
    """Arm nomidan systemd property'lari (§9.3). Noma'lum arm -> istisno."""
    try:
        props = dict(ARM_PROPERTIES[arm])
    except KeyError:
        raise DriverError(
            f"P1 da bunday arm yo'q: {arm!r} (mavjud: {sorted(ARM_PROPERTIES)}); "
            "Baseline B §9.3 bo'yicha P1 da ATAYLAB yo'q"
        ) from None
    check_restart_steps_pairing(props)
    return props


def pressure_target_rate(level: str) -> float:
    """Pressure darajasidan PI nishoni. Noma'lum daraja -> istisno."""
    try:
        return PRESSURE_TARGET_RATE[level]
    except KeyError:
        raise DriverError(
            f"bunday pressure darajasi yo'q: {level!r} "
            f"(mavjud: {sorted(PRESSURE_TARGET_RATE)})"
        ) from None


def pressure_base_mb(level: str) -> int:
    """Pressure darajasidan rezident baza (MiB). Noma'lum daraja -> istisno.

    NEGA ALOHIDA FUNKSIYA: `pressure_target_rate` bilan bir xil fail-closed
    shakl -- noma'lum daraja JIMGINA default'ga tushmaydi. 10-pressure-
    dozalash.md §2.5 / OQ-2 ning nuqsoni aynan jim default edi.
    """
    try:
        return PRESSURE_BASE_MB[level]
    except KeyError:
        raise DriverError(
            f"bunday pressure darajasi yo'q: {level!r} "
            f"(mavjud: {sorted(PRESSURE_BASE_MB)})"
        ) from None


def memory_high_mib(spec: str) -> float:
    """`MemoryHigh=` spetsifikatsiyasidan MiB.

    NEGA KERAK: doza sharti MiB da yoziladi (`pressure.run_pi` bazani
    `high // (1 << 20)` bilan hisoblaydi), demak `base_mb` ni `MemoryHigh`
    bilan taqqoslash uchun bir xil birlik kerak. systemd 1024 asosini
    ishlatadi (`K/M/G/T`); suffiks bo'lmasa qiymat BAYT.
    """
    s = str(spec).strip()
    mult = {"K": 1.0 / 1024, "M": 1.0, "G": 1024.0, "T": 1024.0 * 1024.0}
    try:
        if s and s[-1].upper() in mult:
            return float(s[:-1]) * mult[s[-1].upper()]
        return float(s) / (1 << 20)
    except ValueError:
        raise DriverError(f"MemoryHigh tushunarsiz: {spec!r}") from None


def pressure_dose_arithmetic(level: str, memory_high: str) -> dict[str, Any]:
    """§2.2 ning doza arifmetikasi -- HISOBLANADI, taxmin qilinmaydi.

    NEGA BU FUNKSIYA BOR: 10-pressure-dozalash.md §2.5 ning eng xavfli
    jihati nol dozaning CHIQISHDA iz qoldirmasligi edi -- `P1`/`P2` arm'lari
    0.0000 stall bilan ishlardi va `run_meta` ham, trial oqimi ham buni
    ko'rsatmasdi. `--memory-high` esa RUNTIME bayrog'i, demak uni regressiya
    testi tutib qolmaydi: `--memory-high 256M` da `184 + 25.3 = 209.3 < 256`
    va doza yana 0.0000 bo'lardi. Shuning uchun breach sharti har run'da
    HISOBLANADI va `run_meta.open_parameters.base_mb` ga yoziladi.

    Bu funksiya HECH NARSANI TO'XTATMAYDI va jimgina tuzatmaydi -- u faqat
    FAKTni yozadi (dizayn qoidasi 15: `None` = o'lchanmadi).

    `breach_expected` `False` bo'lishi `P0` da NORMAL (§3.2 -- generator
    idle, atayin nol doza), `P1`/`P2` da esa OQ-2 ning qaytganini bildiradi.
    """
    base_mb = pressure_base_mb(level)
    high_mib = memory_high_mib(memory_high)
    margin = base_mb + PRESSURE_OVERHEAD_MB - high_mib
    return {
        "level": level,
        "base_mb": base_mb,
        "step_mb": PRESSURE_STEP_MB,
        "memory_high_mib": high_mib,
        "overhead_mb": PRESSURE_OVERHEAD_MB,
        "projected_memory_current_mb": base_mb + PRESSURE_OVERHEAD_MB,
        "breach_margin_mb": round(margin, 4),
        "breach_expected": margin > 0.0,
        "ramp_free_expected": base_mb < high_mib,
        "dose_expected": margin > 0.0 and pressure_target_rate(level) > 0.0,
    }


def dry_run_report(
    schedule: sch.Schedule,
    timeline: sch.TrialTimeline,
    selected: Sequence[sch.Trial],
    *,
    only: Sequence[str] = (),
    probe_period_us: int = PROBE_PERIOD_US,
) -> dict[str, Any]:
    """`--dry-run` chiqishi: jadval + hisoblangan vaqtlar, IJRO YO'Q.

    Qo'shimcha vaqt O'LCHANMAGANI ochiq yoziladi (majburiyat 9): dry-run
    hech narsa ishga tushirmaydi, demak o'lchash ham mumkin emas, demak
    baho faqat PASTKI CHEGARA.
    """
    est = sch.estimate_campaign(schedule, timeline, per_trial_overhead_s=0.0)
    return {
        "dry_run": True,
        "driver_version": DRIVER_VERSION,
        "driver_contract": DRIVER_CONTRACT,
        "rng_seed": schedule.seed,
        "rng": sch.RNG_NAME,
        "n_blocks": schedule.n_blocks,
        "schedule_digest": schedule.digest(),
        "n_trials_total": schedule.n_trials,
        "n_trials_selected": len(selected),
        "only": list(only),
        "cells_per_block": schedule.cells_per_block,
        "cell_counts": {"/".join(map(str, c)): n
                        for c, n in schedule.cell_counts().items()},
        "timeline": timeline.as_dict(),
        "t_trial_us": t_trial_us(timeline, probe_period_us),
        "t_trial_formula": T_TRIAL_FORMULA,
        "t_recovery_window_us": t_recovery_window_us(timeline, probe_period_us),
        "campaign_estimate": est.as_dict(),
        "per_trial_overhead_source": "not_measured_dry_run",
        "trials": [t.as_dict() for t in selected],
    }


def verify_guard_live(
    guard_log_path: str,
    active_state: Callable[[], str | None],
    *,
    timeout_s: float = 10.0,
    poll_s: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Guard TIRIK va KUZATAYOTGANINI tasdiqlaydi (majburiyat 2, FAIL-CLOSED).

    Guard'ning O'Z oqimidan (`guard.jsonl`) `guard_start` record'i talab
    qiladi. NEGA unit holati yetarli emas: `guard.run()` PSI faylini ocholmasa
    `watch_open_failed` sababi bilan trip qilib 2 kod bilan CHIQADI
    (guard.py:299) -- ya'ni unit bir lahza `active` bo'lib, keyin o'ladi.
    Faqat `is-active` ni tekshirish shu poygada "guard ishlayapti" deb
    yolg'on javob berardi.

    Qaytadi: `{"ok": bool, "reason": str, ...}`. Istisno TASHLAMAYDI --
    chaqiruvchi (run yo'li) uni `GuardStartError` ga aylantiradi, shunda
    tekshiruvning o'zi testda arzon bo'ladi.
    """
    deadline = now() + timeout_s
    started = False
    fatal: dict[str, Any] | None = None
    state: str | None = None
    records_seen = 0
    while True:
        state = active_state()
        for rec in _read_jsonl_tail(guard_log_path):
            records_seen += 1
            rt = rec.get("record_type")
            if rt == "guard_start":
                started = True
            elif rt == "guard_event" and rec.get("reason") in (
                "watch_open_failed", "psi_read_failed", "psi_incomplete",
                "meminfo_unreadable",
            ):
                fatal = rec
        if fatal is not None:
            return {"ok": False, "reason": "guard_fatal_event",
                    "active_state": state, "event": fatal,
                    "records_seen": records_seen}
        if state == "failed":
            return {"ok": False, "reason": "guard_unit_failed",
                    "active_state": state, "records_seen": records_seen}
        if started and state == "active":
            return {"ok": True, "reason": "guard_start_and_active",
                    "active_state": state, "records_seen": records_seen}
        if now() >= deadline:
            return {
                "ok": False,
                "reason": ("guard_start_record_missing" if not started
                           else "guard_unit_not_active"),
                "active_state": state,
                "records_seen": records_seen,
                "timeout_s": timeout_s,
            }
        sleep(poll_s)


def _read_jsonl_tail(path: str) -> list[dict[str, Any]]:
    """JSONL faylni o'qiydi; yo'q bo'lsa bo'sh ro'yxat.

    Qismli oxirgi qator JIMGINA tashlanadi: bu fayl BOSHQA jarayonga tegishli
    (guard) va u hozir yozayotgan bo'lishi mumkin. To'liq o'qish `reduce.py`
    ning ishi -- bu yerda faqat tirik-yo'qlik tekshiruvi.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError:
        return []
    out: list[dict[str, Any]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict):
            out.append(rec)
    return out


def guard_events_in_window(
    guard_log_path: str, lo_mono_us: int, hi_mono_us: int
) -> list[dict[str, Any]]:
    """Trial oynasiga tushgan `guard_event` record'lari (§12 `aborted_guard`).

    `guard_event` da `trial_id` YO'Q va BO'LMASLIGI KERAK -- guard mustaqil
    jarayon (§8.2), atributsiya MONOTONIC vaqt bo'yicha (§14.7). Bu aynan
    `reduce.split_trials` ning qoidasi (reduce.py:509), demak driver va
    reducer bir xil hodisani bir xil trial'ga bog'laydi.
    """
    out = []
    for rec in _read_jsonl_tail(guard_log_path):
        if rec.get("record_type") != "guard_event":
            continue
        t = rec.get("mono_us")
        if isinstance(t, int) and lo_mono_us <= t <= hi_mono_us:
            out.append(rec)
    return out


# ===========================================================================
# 2. PLATFORMA -- BARCHA yon ta'sirlar shu yerda
# ===========================================================================
#
# NEGA: driver mantiqini (faza deadline'lari, disposition, record ketma-ketligi,
# aynan bitta trial_end) systemd'li mashina TALAB QILMASDAN sinash kerak.
# Testda bu klassning o'rniga fake qo'yiladi -- `test_guard.py` ning `FakePsi`
# si bilan bir xil usul. Har metod 1-5 qator: mantiq bu yerda YO'Q.


class Platform:
    """Haqiqiy systemd + cgroup + socket + soat."""

    def __init__(self) -> None:
        self.systemd = U.SystemdUser()

    # --- soat ---
    def mono_us(self) -> int:
        return mono_us()

    def real_us(self) -> int:
        return real_us()

    def boot_id(self) -> str:
        return read_boot_id()

    def guest_generation(self) -> dict[str, Any]:
        """Guest generation markeri -- `boot_id` TUTMAYDIGAN restart uchun."""
        return parse_guest_generation(
            cg.read_text("/proc/1/stat"),
            cg.read_text("/proc/uptime"),
            clk_tck=os.sysconf("SC_CLK_TCK"),
        )

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)

    # --- systemd ---
    def clear_runtime_drop_ins(self) -> list[str]:
        return U.clear_runtime_drop_ins(systemd=self.systemd)

    def require_clean(self) -> dict[str, Any]:
        return U.require_clean(systemd=self.systemd)

    def set_slice_properties(self, name: str, props: dict[str, Any]) -> None:
        # runtime=True -> drop-in FAQAT /run/user/UID/systemd/user.control/ da;
        # `~/.config/systemd/user/` ga hech narsa yozilmaydi (units.py:919).
        self.systemd.set_unit_properties(name, props, runtime=True)

    def start_transient(self, name: str, props: dict[str, Any]) -> dict[str, Any]:
        return self.systemd.start_transient(name, props, timeout_s=JOB_TIMEOUT_S)

    def stop(self, name: str) -> dict[str, Any] | None:
        return self.systemd.stop(name, timeout_s=JOB_TIMEOUT_S)

    def reset_failed(self, name: str) -> bool:
        return self.systemd.reset_failed(name)

    def active_state(self, name: str) -> str | None:
        return self.systemd.active_state(name)

    def wait_for_active(self, name: str, timeout_s: float) -> dict[str, Any]:
        return U.wait_for_active(self.systemd, name, timeout_s=timeout_s)

    def watcher(self, unit: str) -> Any:
        # seed=True VA match obunasi unit YARATILISHIDAN OLDIN: obyekt yo'li
        # nomdan hisoblanadi, demak eng birinchi o'tish o'tkazib yuborilmaydi
        # (units.py:1165).
        return U.UnitWatcher(self.systemd, unit)

    def dump_unit_properties(self, name: str) -> dict[str, Any]:
        # require_alive=True -- 01-muhit-tekshiruvlari.md §4 tuzog'i: o'chgan
        # unit uchun `systemctl show` rc=0 va TO'LIQ DEFAULT beradi.
        return U.dump_unit_properties(name, systemd=self.systemd,
                                      require_alive=True)

    def teardown(self, units: Sequence[str] = (), **kw: Any) -> dict[str, Any]:
        return U.teardown(systemd=self.systemd, units=list(units), **kw)

    # --- cgroup ---
    def cgroup_path(self, slice_name: str) -> str:
        return cg.user_child(slice_name)

    def user_cgroup(self) -> str:
        return cg.user_service_cgroup()

    def snapshot_cgroup(self, path: str) -> dict[str, Any]:
        return cg.snapshot_cgroup(path)

    def memory_events(self, path: str) -> dict[str, int]:
        return cg.read_keyed(f"{path}/memory.events")

    def memory_current(self, path: str) -> int | None:
        return cg.read_int(f"{path}/memory.current")

    def kill_subtree(self, path: str) -> bool:
        self.last_kill_mono_us = self.mono_us()
        return cg.kill_subtree(path)

    def meminfo(self) -> dict[str, int]:
        return cg.meminfo()

    def vmstat(self) -> dict[str, int]:
        return cg.vmstat()

    def psi_total(self, psi_path: str, kind: str = "full") -> tuple[int, int] | None:
        """(mono_us, total) -- `total=` akkumulyatori (§7 ASOSIY o'lchov)."""
        text = cg.read_text(psi_path)
        if text is None:
            return None
        try:
            psi = cg.parse_psi(text)
        except ValueError:
            return None
        row = psi.get(kind)
        if row is None:
            return None
        return self.mono_us(), int(row["total"])

    # --- SUT socket (03-sut-protokoli.md §1) ---
    def sut_command(self, socket_path: str, command: str,
                    timeout_s: float = 0.5) -> dict[str, Any]:
        """Bitta so'rov-javob. `SOCK_SEQPACKET` -- xabar chegarasi saqlanadi.

        Har chaqiruvda YANGI ulanish: protokol §1 "har ulanish bitta
        so'rov-javob".
        """
        out: dict[str, Any] = {"command": command, "reply": None, "errno": None}
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        try:
            sock.settimeout(timeout_s)
            sock.connect(socket_path)
            sock.send(command.encode("ascii"))
            out["reply"] = sock.recv(4096).decode("ascii", "replace")
        except OSError as exc:
            out["errno"] = getattr(exc, "errno", None)
            out["error"] = repr(exc)
        finally:
            try:
                sock.close()
            except OSError:
                pass
        return out

    # --- muhit faktlari (run_meta uchun) ---
    def environment_facts(self) -> dict[str, Any]:
        """`cli.py` ning yordamchilari.

        KECH IMPORT ataylab: `revix/cli.py` `revix run` subcommand'ini
        qo'shganda `driver` ni import qiladi, demak modul darajasidagi
        `from .cli import ...` AYLANMA import yaratardi (cli -> driver -> cli,
        va `cli` yarim initsializatsiya qilingan holatda bo'lardi). Funksiya
        ichidagi import bu aylanani butunlay yo'q qiladi.
        """
        from . import cli  # noqa: PLC0415 -- yuqoridagi izohni ko'ring

        return {
            "git": cli.git_info(),
            "host": cli.host_facts(),
            "oomd": cli.oomd_state(),
            "repo_version": cli._read_version_file(),
            "modules": cli.check_python_modules().detail.get("found", {}),
            "systemd_version": cli.check_systemd_version().detail,
            "delegated_controllers": cli.check_delegated_controllers().detail,
            "cpu_governor": cli.check_cpu_governor().detail,
            "memory": cli.check_memory_headroom().detail,
        }

    def close(self) -> None:
        self.systemd.close()


# ===========================================================================
# 3. DRIVER
# ===========================================================================


@dataclass
class TrialTiming:
    """Bitta trial'ning O'LCHANGAN vaqtlari (majburiyat 9).

    Hech bir qiymat taxmin qilinmaydi: har biri `mono_us()` dan olingan
    ikki nuqtaning ayirmasi.
    """

    begin_mono_us: int
    setup_us: int = 0
    baseline_start_mono_us: int = 0
    pressure_off_mono_us: int = 0
    horizon_end_mono_us: int = 0
    washout_us: int = 0
    teardown_us: int = 0
    dump_us: int = 0
    end_mono_us: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "begin_mono_us": self.begin_mono_us,
            "setup_us": self.setup_us,
            "baseline_start_mono_us": self.baseline_start_mono_us,
            "pressure_off_mono_us": self.pressure_off_mono_us,
            "horizon_end_mono_us": self.horizon_end_mono_us,
            "washout_us": self.washout_us,
            "teardown_us": self.teardown_us,
            "dump_us": self.dump_us,
            "end_mono_us": self.end_mono_us,
            "wall_us": self.end_mono_us - self.begin_mono_us,
        }


@dataclass
class DriverConfig:
    """Run sozlamalari. Muzlatilmagan qiymatlar SHU YERDA, oshkora."""

    run_dir: str
    seed: int
    blocks: int = sch.P1_BLOCKS
    only: tuple[str, ...] = ()
    session_id: str = "p1"
    run_mode: str = "pilot"
    allow_pressure: bool = False
    memory_high: str = DEFAULT_MEMORY_HIGH
    watchdog_sec: str = DEFAULT_WATCHDOG_SEC
    timeout_start_sec: str = DEFAULT_TIMEOUT_START_SEC
    sut_binary: str | None = None
    python: str = sys.executable
    repo_root: str = REPO_ROOT
    runtime_dir: str | None = None
    max_hours: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_dir": self.run_dir, "seed": self.seed, "blocks": self.blocks,
            "only": list(self.only), "session_id": self.session_id,
            "run_mode": self.run_mode, "allow_pressure": self.allow_pressure,
            "memory_high": self.memory_high, "watchdog_sec": self.watchdog_sec,
            "timeout_start_sec": self.timeout_start_sec,
            "sut_binary": self.sut_binary, "python": self.python,
            "repo_root": self.repo_root, "max_hours": self.max_hours,
        }


class Driver:
    """Trial orkestratsiyasi. Yon ta'sirlar FAQAT `platform` orqali."""

    def __init__(
        self,
        config: DriverConfig,
        platform: Platform,
        schedule: sch.Schedule,
        timeline: sch.TrialTimeline,
        *,
        run_id: str | None = None,
        washout_policy: sch.WashoutPolicy = sch.DEFAULT_WASHOUT_POLICY,
        probe_period_us: int = PROBE_PERIOD_US,
    ) -> None:
        self.cfg = config
        self.pf = platform
        self.schedule = schedule
        # Timeline KONSTRUKTORDA tekshirilgan: `TrialTimeline.__post_init__`
        # oltita invariantni O'ZI majburlaydi (majburiyat 6). Driver uni
        # qayta tekshirmaydi va JIMGINA TUZATMAYDI.
        self.timeline = timeline
        self.probe_period_us = probe_period_us
        # `t_trial_us()` invariant buzilsa ISTISNO tashlaydi -> run boshlanmaydi.
        self.t_trial_us = t_trial_us(timeline, probe_period_us)
        self.washout_policy = washout_policy
        self.selected = select_trials(schedule, config.only)

        self.run_id = run_id or new_run_id()
        self.boot_id = platform.boot_id()
        # Guest generation markeri run BOSHIDA olinadi va har trial
        # chegarasida QAYTA tekshiriladi (GuestRestartError docstring'i).
        self.guest_generation = platform.guest_generation()
        self.em = Emitter("driver", self.run_id, config.session_id,
                          boot_id=self.boot_id)

        self.run_dir = config.run_dir
        self.events_path = os.path.join(self.run_dir, EVENTS_FILE)
        self.probe_path = os.path.join(self.run_dir, PROBE_FILE)
        self.psi_path = os.path.join(self.run_dir, PSI_FILE)
        self.guard_path = os.path.join(self.run_dir, GUARD_FILE)
        self.pressure_path = os.path.join(self.run_dir, PRESSURE_FILE)
        self.meta_path = os.path.join(self.run_dir, RUN_META_FILE)
        self.trip_path = os.path.join(self.run_dir, GUARD_TRIP_FILE)

        self.writer = JsonlWriter(self.events_path)
        self.lab_cgroup: str | None = None
        self.mon_cgroup: str | None = None
        self.units_show: dict[str, Any] = {}
        self.measured_overhead_s: float | None = None
        self.overhead_detail: dict[str, Any] = {
            "source": "not_measured", "measurements": []}
        # Majburiyat 5 ning STRUKTURAVIY qulfi: trial_id bir marta yoziladi.
        self._ended: set[str] = set()
        self._began: set[str] = set()
        self._disposition_counts: dict[str, int] = {d: 0 for d in DISPOSITIONS}
        self._trial_overheads: list[float] = []
        self._guard_started = False
        self._psi_started = False

    # --- yozish -------------------------------------------------------------

    def _emit(
        self,
        record_type: str,
        payload: dict[str, Any],
        *,
        trial: sch.Trial | None = None,
        mono: int | None = None,
    ) -> dict[str, Any]:
        """Bitta record. `stream == record_type` HAR DOIM (dizayn qoidasi 12).

        VAQT MANBASI YAGONA: `mono` berilmasa `platform.mono_us()` ishlatiladi,
        `schema.mono_us()` NING O'ZI EMAS. NEGA: `Emitter.envelope()` ning
        default'i `schema.mono_us()` ga to'g'ridan-to'g'ri boradi, ya'ni
        platformani CHETLAB O'TADI. Ishlab chiqarishda ikkisi bir xil
        funksiya, lekin chetlab o'tish driver'ning vaqt disiplinasini ikki
        manbaga bo'lardi (§1) -- va bu aynan shunday aniqlandi: fake soat
        ostida `env_snapshot` record'lari trial oynasidan tashqarida chiqib,
        `validate.check_trial_events` ni yiqitdi.
        """
        rec = self.em.record(
            record_type,
            payload,
            stream=record_type,
            trial_id=trial.trial_id if trial is not None else None,
            block_index=trial.block_index if trial is not None else None,
            mono=mono if mono is not None else self.pf.mono_us(),
        )
        self.writer.write(rec)
        return rec

    def _harness_error(
        self, where: str, exc: BaseException, *, trial: sch.Trial | None = None
    ) -> None:
        """Istisno -> `harness_error` record. HECH QACHON JIM EMAS (qoida 13)."""
        try:
            self._emit(
                "harness_error",
                {"where": where, "error": repr(exc),
                 "error_type": type(exc).__name__},
                trial=trial,
            )
        except Exception:  # noqa: BLE001 -- log xatosi o'lchovni to'xtatmaydi
            pass

    # --- unit property to'plamlari -----------------------------------------

    def _sut_socket(self, name: str) -> str:
        base = self.cfg.runtime_dir or os.environ.get("XDG_RUNTIME_DIR") \
            or f"/run/user/{os.getuid()}"
        return f"{base.rstrip('/')}/revix-{name}.sock"

    def _sut_binary(self) -> str:
        return self.cfg.sut_binary or os.path.join(
            self.cfg.repo_root, "revix", "sut")

    def _mon_unit_properties(self, argv: list[str], *,
                             runtime_max_sec: float) -> dict[str, Any]:
        """`revixmon.slice` dagi harness unit'i (majburiyat 7).

        `StandardOutput/Error=null`: §3.4 -- 10 Hz oqim journald rate-limit'ga
        tushib JIMGINA yo'qolardi, shuning uchun hech qanday o'lchov
        ma'lumoti journald'dan O'TMAYDI.
        """
        return {
            "Description": "REVIX harness",
            "Slice": MON_SLICE,
            "MemoryMax": MON_UNIT_MEMORY_MAX,
            "MemorySwapMax": 0,
            "WorkingDirectory": self.cfg.repo_root,
            "ExecStart": argv,
            "Collect": True,
            "RuntimeMaxSec": f"{int(runtime_max_sec)}s",
            "StandardOutput": "null",
            "StandardError": "null",
        }

    def _sut_properties(self, arm: str, *, bystander: bool) -> dict[str, Any]:
        """SUT yoki bystander unit'i (00-pilot-topologiya.md §1, majburiyat 8).

        Bystander HECH QACHON fault qilinmaydi -- u spillover detektori.
        Shuning uchun uning `Restart=no`: agar u o'lsa, biz BUNI KO'RISHIMIZ
        kerak, qayta ko'tarilishi esa aynan shu signalni yashirardi.
        """
        name = "bystander" if bystander else "sut"
        props: dict[str, Any] = {
            "Description": f"REVIX {name}",
            "Slice": LAB_SLICE,
            "Type": "notify",
            "ExecStart": [self._sut_binary()],
            "WorkingDirectory": self.cfg.repo_root,
            "Environment": [
                f"REVIX_SUT_SOCKET={self._sut_socket(name)}",
                f"REVIX_SUT_RATE_HZ={SUT_RATE_HZ}",
            ],
            "MemoryMax": "128M" if bystander else "256M",
            "MemorySwapMax": 0,
            "TasksMax": 64,
            "WatchdogSec": self.cfg.watchdog_sec,
            "TimeoutStartSec": self.cfg.timeout_start_sec,
            "Collect": True,
            "StandardOutput": "null",
            "StandardError": "null",
        }
        if bystander:
            props.update({"Restart": "no", "StartLimitBurst": 0})
        else:
            props.update(arm_properties(arm))
        # To'liq to'plam ustida yana bir marta: arm property'lari qo'shilgandan
        # keyin ham juftlik buzilmasligi kerak (o'lchangan systemd 257 tuzog'i).
        check_restart_steps_pairing(props)
        return props

    def _prober_argv(self, trial: sch.Trial) -> list[str]:
        return [
            self.cfg.python, "-m", "revix.prober",
            "--target", f"sut={self._sut_socket('sut')}",
            "--target", f"bystander={self._sut_socket('bystander')}",
            "--csv", self.probe_path,
            "--events", self.events_path,
            "--run-id", self.run_id,
            "--session-id", self.cfg.session_id,
            # Prober'ning `trial_id` i JARAYON BOSHIDA qotadi (prober.py:370)
            # va uni ish vaqtida o'zgartirish kanali YO'Q. Shuning uchun HAR
            # TRIAL uchun ALOHIDA prober jarayoni: aks holda bitta trial_id
            # barcha qatorlarga tushib, `reduce.split_trials` (reduce.py:453)
            # 119 trial'ni probe'siz qoldirardi.
            "--trial-id", trial.trial_id,
            # §8.2: prober'ning O'Z CPU'si trial bo'yicha o'lchanadi va yadro
            # foizida beriladi (>1% bo'lsa sekinlashtiriladi), va arm'lar
            # bo'yicha BIR XIL ushlanadi. Raqamlar `prober_stop.cost` da
            # `events.jsonl` ga tushadi -- stderr'da emas (`StandardError=null`,
            # §3.4), demak ular `analyze.py` ning `probe_cost` figurasi uchun
            # trial_id bilan birga oqimda qoladi.
            "--report-cost",
        ]

    def _psi_argv(self) -> list[str]:
        return [
            self.cfg.python, "-m", "revix.psi_sampler",
            "--with-host", "--with-user",
            "--scope", f"lab={self.lab_cgroup}",
            "--scope", f"mon={self.mon_cgroup}",
            "--csv", self.psi_path,
            "--events", self.events_path,
            "--run-id", self.run_id,
            "--session-id", self.cfg.session_id,
        ]

    def _guard_argv(self) -> list[str]:
        return [
            self.cfg.python, "-m", "revix.guard",
            "--lab-cgroup", str(self.lab_cgroup),
            "--watch-cgroup", self.pf.user_cgroup(),
            "--log", self.guard_path,
            "--trip-file", self.trip_path,
            "--run-id", self.run_id,
            "--session-id", self.cfg.session_id,
        ]

    def _pressure_argv(self, level: str, max_seconds: float) -> list[str]:
        """Generator argv'i. DOZA DIAL'I OSHKORA (dizayn qoidasi 17).

        `--step-mb` va `--base-mb` ATAYLAB IKKISI HAM beriladi.

        NEGA IKKISI HAM, bittasi emas: `pressure.run_pi` bazani
        `base = max(16, high_MiB - 2*step_mb)` bilan O'ZI chiqaradi, ya'ni
        baza `MemoryHigh` ga BOG'LIQ. 10-pressure-dozalash.md §3.6 ishchi
        oynani o'lchadi va u TOR -- 29 epizodda faqat `base_mb=184` ishladi,
        188 guard'ni urdi, 196 §9.4 invariant 2 ni buzdi. Demak `MemoryHigh`
        o'zgarganda formula bazani JIMGINA boshqa qiymatga ko'chirardi, va
        aynan shu mexanizm OQ-2 nuqsonini tug'dirdi: dial berilmaganda modul
        default'i `step_mb=16` ishlab, `base = 192 - 2*16 = 160 MiB`, ya'ni
        §2.2 ning D1 epizodida o'lchangan NOL-DOZA konfiguratsiyasi
        (erishilgan stall 114 namunada ham aynan 0.0000).

        `--interval-ms` HAM beriladi. Modul default'i (250 ms) §2.6 ning
        kalibrlangan qiymatiga TASODIFAN teng, demak bugun nuqson yo'q --
        lekin bu aynan `step_mb` ning merosi bilan bir xil klass: default
        o'zgarsa pilotning control tik'i JIMGINA ko'chardi. Meros
        QOLDIRILMAYDI.
        """
        return [
            self.cfg.python, "-m", "revix.pressure",
            "--mode", "pi",
            "--cgroup", str(self.lab_cgroup),
            "--target-rate", f"{pressure_target_rate(level)}",
            # §2.6 ning kalibrlangan dial'i -- derivatsiya qilinmaydi va
            # modul default'laridan MEROS QILINMAYDI.
            "--step-mb", f"{PRESSURE_STEP_MB}",
            "--base-mb", f"{pressure_base_mb(level)}",
            "--interval-ms", f"{PRESSURE_INTERVAL_MS}",
            "--max-seconds", f"{max_seconds:.3f}",
            "--log", self.pressure_path,
            "--run-id", self.run_id,
            "--session-id", self.cfg.session_id,
        ]

    def _pressure_properties(self, max_seconds: float) -> dict[str, Any]:
        return {
            "Description": "REVIX pressure generator",
            "Slice": LAB_SLICE,
            "ExecStart": self._pressure_argv("P0", max_seconds),  # o'rniga qo'yiladi
            "MemoryMax": PRESS_MEMORY_MAX,
            "MemorySwapMax": 0,
            # Generator trial'dan UZOQ YASHAMAYDI (00-pilot-topologiya.md §2).
            "RuntimeMaxSec": f"{int(max_seconds) + 2}s",
            "OOMPolicy": "continue",
            "Collect": True,
            "StandardOutput": "null",
            "StandardError": "null",
        }

    # --- run darajasi -------------------------------------------------------

    def setup_run(self) -> dict[str, Any]:
        """Run boshlanishi: majburiyat 3, 4, keyin slice dial'lari.

        TARTIB MUHIM va shunday izohlangan:
          1. `clear_runtime_drop_ins()` -- oldingi run'ning `MemoryHigh=` i
             meros bo'lmasligi uchun (majburiyat 3);
          2. `require_clean()` -- qoldiq unit/cgroup jimgina kontaminatsiya
             qilmasligi uchun (majburiyat 4);
          3. DOZA PRE-FLIGHT'i (`_require_nonzero_dose()`) -- dial'lar
             systemd'ga YUKLANISHIDAN OLDIN: nol doza bilan run boshlanmasin
             va rad etilgan run slice'da hech qanday holat qoldirmasin;
          4. slice dial'lari -- 2 dan KEYIN, chunki `SetUnitProperties`
             slice'ni systemd'ga yuklaydi va pre-flight o'zimiz yaratgan
             holatdan yiqilardi.
        """
        removed = self.pf.clear_runtime_drop_ins()
        preflight = self.pf.require_clean()
        self.lab_cgroup = self.pf.cgroup_path(LAB_SLICE)
        self.mon_cgroup = self.pf.cgroup_path(MON_SLICE)
        lab_props = dict(LAB_SLICE_PROPERTIES)
        lab_props["MemoryHigh"] = self.cfg.memory_high
        # Arifmetika slice'ga HAQIQATAN yuboriladigan `MemoryHigh` dan
        # hisoblanadi, `DEFAULT_MEMORY_HIGH` dan EMAS -- `--memory-high`
        # runtime bayrog'i (ZeroDoseError docstring'i).
        dose = self._require_nonzero_dose(lab_props["MemoryHigh"])
        self.pf.set_slice_properties(LAB_SLICE, lab_props)
        self.pf.set_slice_properties(MON_SLICE, dict(MON_SLICE_PROPERTIES))
        return {
            "removed_drop_ins": removed,
            "preflight": preflight,
            "lab_slice_properties": lab_props,
            "mon_slice_properties": dict(MON_SLICE_PROPERTIES),
            "lab_cgroup": self.lab_cgroup,
            "mon_cgroup": self.mon_cgroup,
            "dose_preflight": dose,
        }

    def _require_nonzero_dose(self, memory_high: str) -> dict[str, Any]:
        """Jadvaldagi HAR BIR dozalangan band haqiqatan doza berishi SHART.

        `P0` ATAYLAB tekshirilmaydi: uning `breach_expected: false` i
        TO'G'RI va §9.3 ning "generator idle" sharti (§3.2 -- generator
        tirik, 160 MiB rezident, `memory.events high` delta 0). Shart faqat
        `target_rate > 0` bo'lgan bandlarga qo'yiladi.

        Faqat JADVALDAGI bandlar tekshiriladi (`--only` filtridan keyin):
        `--only P0,A` run'i `P1`/`P2` ning dial'i buzilgani uchun rad
        etilmasligi kerak -- u ularni ishlatmaydi.

        Xato xabari ARIFMETIKANI ko'rsatadi, quruq rad etishni emas:
        operator `projected_memory_current_mb` ni `MemoryHigh` ga qarshi
        ko'rib, nima o'lchanishi kerakligini biladi (§2.6, OQ-11).

        CHEKLOV -- shart FAQAT `breach_expected`: `ramp_free_expected`
        (`base_mb < MemoryHigh_MiB`, §2.4/§4.1) bu yerda RAD ETISH sharti
        EMAS. Demak `MemoryHigh` `base_mb` dan PAST bo'lsa (masalan 176M:
        184+25.3 = 209.3 > 176, lekin 184 > 176) run BOSHLANADI, holbuki
        §3.6 da `base=196 > high=192` ramp'ni 12.217 s cho'zib §9.4
        invariant 2 ni buzgan. Bu yo'l jim EMAS -- `ramp_free_expected`
        `run_meta.open_parameters.base_mb.dose_arithmetic` ga yoziladi va
        regressiya qulfi uni default konfiguratsiyada tutadi -- lekin
        runtime'da to'xtatilmaydi. Shartni kengaytirish qarori
        `driver.py` egasiniki (hisobotda qayd etilgan).
        """
        levels = sorted({str(t.level("pressure_level")) for t in self.selected})
        arithmetic = {
            level: pressure_dose_arithmetic(level, memory_high)
            for level in levels
        }
        broken = [
            a for level, a in sorted(arithmetic.items())
            if pressure_target_rate(level) > 0.0 and not a["breach_expected"]
        ]
        if broken:
            detail = "; ".join(
                f"{a['level']}: base_mb={a['base_mb']} + overhead "
                f"{a['overhead_mb']} = {a['projected_memory_current_mb']} MiB "
                f"<= MemoryHigh {a['memory_high_mib']} MiB "
                f"(zaxira {a['breach_margin_mb']:+} MiB)"
                for a in broken
            )
            raise ZeroDoseError(
                "dial NOL doza beradi, run boshlanmaydi -- "
                f"{detail}. memory.high buzilmaydi, demak erishilgan stall "
                "aynan 0.0000 bo'lardi (10-pressure-dozalash.md §2.2 D1) va "
                "§9.3 ning uch darajali dizayni bitta darajaga qulardi; "
                "natija H1 ga qarshi dalil emas, ASBOB NUQSONI bo'lardi "
                "(§2.5, OQ-2). MemoryHigh o'zgargan bo'lsa base_mb QAYTA "
                "O'LCHANISHI kerak -- ishchi oyna tor (§3.6, OQ-11)."
            )
        return {
            "memory_high": memory_high,
            "levels_checked": levels,
            "arithmetic": arithmetic,
        }

    def start_guard(self) -> dict[str, Any]:
        """Guard BIRINCHI ishga tushadi va TIRIKLIGI tasdiqlanadi (1, 2).

        `RuntimeMaxSec` kampaniyaning ENG YOMON holatidan uzun qo'yiladi:
        bu guard'ning himoyasini CHEKLAMAYDI, faqat driver butunlay yo'qolib
        ketsa guard abadiy qolmasligini ta'minlaydi.
        """
        est = sch.estimate_campaign(
            self.schedule, self.timeline,
            per_trial_overhead_s=self.measured_overhead_s or 0.0)
        runtime_max = est.worst_case_total_s + 600.0
        argv = self._guard_argv()
        props = self._mon_unit_properties(argv, runtime_max_sec=runtime_max)
        props["Description"] = "REVIX safety guard"
        job = self.pf.start_transient(GUARD_UNIT, props)
        self._guard_started = True
        check = verify_guard_live(
            self.guard_path, lambda: self.pf.active_state(GUARD_UNIT),
            timeout_s=ACTIVE_TIMEOUT_S, sleep=self.pf.sleep)
        if not check["ok"]:
            raise GuardStartError(
                f"guard ishga tushmadi ({check['reason']}): run BOSHLANMAYDI "
                f"(fail-closed, 04-...-shartnomasi.md §1.3 majburiyat 2); "
                f"detallar: {check}"
            )
        return {"job": job, "check": check, "runtime_max_sec": runtime_max,
                "argv": argv}

    def start_psi_sampler(self) -> dict[str, Any]:
        """psi_sampler guard'dan KEYIN, prober'dan OLDIN (majburiyat 7)."""
        est = sch.estimate_campaign(
            self.schedule, self.timeline,
            per_trial_overhead_s=self.measured_overhead_s or 0.0)
        argv = self._psi_argv()
        props = self._mon_unit_properties(
            argv, runtime_max_sec=est.worst_case_total_s + 600.0)
        props["Description"] = "REVIX psi sampler"
        job = self.pf.start_transient(PSI_UNIT, props)
        self._psi_started = True
        return {"job": job, "argv": argv}

    def measure_overhead(self) -> dict[str, Any]:
        """Trial qo'shimcha vaqtini O'LCHAYDI (majburiyat 9, §9.4 v1.3).

        §9.4: "Haqiqiy trial vaqti bundan katta (unit yaratish/yo'q qilish,
        D-Bus round-trip, ma'lumot flush). Bu qo'shimcha O'LCHANADI, TAXMIN
        QILINMAYDI."

        Shuning uchun bu yerda HAQIQIY tsikl bajariladi: lab unit'lari
        yaratiladi, property'lari TIRIK paytida dump qilinadi, keyin
        yig'ishtiriladi. FAULT YO'Q, PRESSURE YO'Q -- demak bu o'lchov
        xavfsiz va 00-pilot-topologiya.md §6 ning qadam 3/4 tartibini
        buzmaydi.

        Qo'shimcha vaqt `estimate_campaign()` ning ta'rifida beriladi:
        fazalar yig'indisidan OSHGAN qism, ya'ni o'lchangan setup+teardown
        minus rejalashtirilgan `preflight_s`.
        """
        t0 = self.pf.mono_us()
        dump: dict[str, Any] = {}
        try:
            self._start_lab_units("A")
            t_up = self.pf.mono_us()
            for unit in (SUT_UNIT, BYSTANDER_UNIT):
                dump[unit] = self.pf.dump_unit_properties(unit)
            t_dump = self.pf.mono_us()
        finally:
            self._stop_lab_units()
        t1 = self.pf.mono_us()
        measured_s = (t1 - t0) / 1e6
        overhead_s = max(0.0, measured_s - self.timeline.preflight_s)
        self.measured_overhead_s = overhead_s
        self.units_show.update(dump)
        self.overhead_detail = {
            "source": "measured_preflight_cycle",
            "measured_setup_teardown_s": measured_s,
            "setup_us": t_up - t0,
            "dump_us": t_dump - t_up,
            "teardown_us": t1 - t_dump,
            "planned_preflight_s": self.timeline.preflight_s,
            "per_trial_overhead_s": overhead_s,
            "note": ("o'lchov: fault YO'Q, pressure YO'Q; `estimate_campaign` "
                     "ta'rifi bo'yicha fazalar yig'indisidan oshgan qism"),
        }
        return self.overhead_detail

    def run_meta_payload(self, setup: dict[str, Any],
                         guard: dict[str, Any] | None,
                         psi: dict[str, Any] | None) -> dict[str, Any]:
        """`run_meta` -- shartnoma §1.1 ning MAJBURIY maydonlari.

        CHEKLOV -- `ramp_above_threshold_s` faqat REJA sifatida tekshiriladi,
        O'LCHOV sifatida EMAS, va reja endi NOL:

          * `validate.check_planned_timeline` (`revix/validate.py:1602`)
            har `trial_begin.planned_timeline` dan `hold_s +
            ramp_above_threshold_s <= GUARD_SUSTAIN_WINDOW_S` ni
            tekshiradi. Bu REJALASHTIRILGAN qiymat, ya'ni
            `schedule.RAMP_ABOVE_THRESHOLD_S` ning ko'chirmasi.
          * Driver har trial uchun HAQIQIY ramp'ning quiescence
            chegarasidan yuqori qismini (10-pressure-dozalash.md §4 ning
            o'lchov usuli: `pressure_start` .. oxirgi `pressure_ramp`
            oynasida `psi.csv` ning 2 s oynali `full` tezligi > 0.05
            bo'lgan namunalari) HECH QAYERGA yozmaydi.
          * Demak reja 0.000 s bo'lganda `plan_slack_s = 0.0`: biror
            trial'da ramp chegaradan yuqoriga chiqsa, validator buni
            KO'RMAYDI -- taqqoslash uchun o'lchangan qiymat yo'q. Xavf
            gipotetik emas: §3.6 da `base_mb=196` ramp'ni 12.217 s cho'zib
            `ramp_above_threshold_s = 9.500 s` bergan, ya'ni §9.4
            invariant 2 ni buzgan konfiguratsiya O'LCHANGAN.

        TO'G'RI tuzatish -- driver per-trial O'LCHANGAN ramp qiymatini
        record'ga yozsin (masalan `trial_end` yoki `pressure_summary` da),
        va `validate` uni REJAGA qarshi solishtirsin. Bu ALOHIDA ish
        bandi: yangi o'lchov yo'li, yangi payload maydoni va validator
        tekshiruvi kerak, demak bu funksiyaning qamrovidan TASHQARIDA va
        bu yerda BAJARILMADI (hisobotda qayd etilgan).

        NIMA QILINMADI va NEGA: `RAMP_ABOVE_THRESHOLD_S` ni zaxira uchun
        0.000 dan YUQORI qo'yish bu bo'shliqni YOPMAYDI -- u faqat
        validatorning chegarasini o'lchanmagan taxmin bilan surardi.
        Avvalgi `3.0` AYNAN shunday paydo bo'lgan (o'z izohida `TAXMIN`)
        va `PREREGISTRATION.md` §21.7 uni rad etgan. Bir xil nuqsonni
        takrorlash tuzatish emas.
        """
        facts = self.pf.environment_facts()
        prereg = preregistration_info(self.cfg.repo_root)
        est = sch.estimate_campaign(
            self.schedule, self.timeline,
            per_trial_overhead_s=self.measured_overhead_s or 0.0,
            max_hours=self.cfg.max_hours)
        host = facts.get("host", {})
        mem = facts.get("memory", {}) or {}
        git = facts.get("git", {}) or {}
        payload: dict[str, Any] = {
            "driver_version": DRIVER_VERSION,
            "driver_contract": DRIVER_CONTRACT,
            "schema_version": None,  # envelope beradi; bu yerda joy egallamaydi
            "run_mode": self.cfg.run_mode,
            "started_real_us": self.pf.real_us(),
            "started_mono_us": self.pf.mono_us(),
            "rng_seed": self.schedule.seed,
            "rng": sch.RNG_NAME,
            "schedule_digest": self.schedule.digest(),
            "schedule": json.loads(self.schedule.to_json()),
            "only": list(self.cfg.only),
            "n_trials_total": self.schedule.n_trials,
            "n_trials_selected": len(self.selected),
            "git_commit": git.get("commit"),
            "git_dirty": git.get("dirty"),
            "git_detail": git,
            "uname": host,
            "cpu_count": host.get("cpu_count"),
            "cpu_model": (facts.get("cpu_governor") or {}).get("cpu_model"),
            "mem_total_kb": mem.get("mem_total_kb"),
            "mem_available_kb": mem.get("mem_available_kb"),
            "systemd_version": facts.get("systemd_version"),
            "cgroup_delegated_controllers": facts.get("delegated_controllers"),
            "oomd_effective": facts.get("oomd"),
            # §15.4 NORMATIV: bu mashinada `None` (o'lchanmadi), `[]`/`0` EMAS.
            # `_none_if_empty` docstring'ida sabab to'liq yozilgan.
            "governor": _none_if_empty(
                (facts.get("cpu_governor") or {}).get("governors")),
            "scaling_driver": _none_if_empty(
                (facts.get("cpu_governor") or {}).get("drivers")),
            "cpu_governor_detail": facts.get("cpu_governor"),
            "thermal_c": None,
            "dvfs_measurable": False,
            "dvfs_source": "cpufreq/thermal_zone sysfs mavjud emas (o'lchangan)",
            "boot_id_note": (
                "WSL guest qayta ishga tushganda CLOCK_MONOTONIC nolga "
                "qaytadi, lekin boot_id O'ZGARMAYDI (o'lchangan) -- shuning "
                "uchun guest_generation markeri alohida yoziladi"),
            "guest_generation": self.guest_generation,
            "pid1_starttime_ticks": self.guest_generation.get(
                "pid1_starttime_ticks"),
            "pid1_starttime_s": self.guest_generation.get("pid1_starttime_s"),
            "uptime_s_at_start": self.guest_generation.get("uptime_s"),
            "python_version": sys.version,
            "module_versions": facts.get("modules"),
            "repo_version": facts.get("repo_version"),
            "timeline": self.timeline.as_dict(),
            # T_trial HISOBLANADI, hech qachon jimgina konstanta emas.
            "t_trial_us": self.t_trial_us,
            "t_trial_formula": T_TRIAL_FORMULA,
            "t_recovery_window_us": t_recovery_window_us(
                self.timeline, self.probe_period_us),
            "probe_period_us": self.probe_period_us,
            "washout_policy": {
                "t_q_s": self.washout_policy.t_q_s,
                "t_w_s": self.washout_policy.t_w_s,
                "t_w_max_s": self.washout_policy.t_w_max_s,
                "quiescence_rate": self.washout_policy.quiescence_rate,
                "memory_epsilon_bytes": self.washout_policy.memory_epsilon_bytes,
            },
            "campaign_estimate": est.as_dict(),
            "per_trial_overhead_s": self.measured_overhead_s,
            "per_trial_overhead": self.overhead_detail,
            "slice_setup": setup,
            "guard_start": guard,
            "psi_sampler_start": psi,
            "arms": {k: dict(v) for k, v in ARM_PROPERTIES.items()},
            "arm_policy_delay_us": dict(ARM_POLICY_DELAY_US),
            "pressure_target_rate": dict(PRESSURE_TARGET_RATE),
            "pressure_step_mb": PRESSURE_STEP_MB,
            "pressure_base_mb": dict(PRESSURE_BASE_MB),
            "pressure_interval_ms": PRESSURE_INTERVAL_MS,
            "pressure_allowed": self.cfg.allow_pressure,
            "fault_class": FAULT_CLASS,
            "fault_kind": FAULT_KIND,
            "config": self.cfg.as_dict(),
            "units_show": self.units_show,
            "run_files": list(RUN_FILES),
            # Muzlatilmagan parametrlar OSHKORA: hech biri jimgina tanlanmadi.
            "open_parameters": {
                "memory_high": {
                    "value": self.cfg.memory_high,
                    "source": "docs/architecture/02-guard-kalibratsiyasi.md §3 "
                              "(high=192M, MemoryMax=1G bilan o'lchangan); "
                              "docs/architecture/10-pressure-dozalash.md §2.2 "
                              "uni MemoryMax=2G ostida QAYTA o'lchadi va "
                              "base=184 juftligini qayta ishlab chiqardi "
                              "(08 §12 OQ-4 yopildi)",
                    # SHUNDAY QOLADI, lekin sababi boshqa: OQ-11 -- MemoryHigh
                    # ning O'ZI optimallashtirilmagan va ishchi base_mb oynasi
                    # TOR (§3.6), demak boshqa MemoryHigh base_mb ni qaytadan
                    # topishni TALAB QILADI.
                    "calibration_required": True,
                },
                "watchdog_sec": {
                    "value": self.cfg.watchdog_sec,
                    "source": "muzlatilmagan; §9.2 (iv) watchdog miss MEXANIZM, "
                              "demak qiymat natijaga ta'sir qiladi",
                    "calibration_required": True,
                },
                "timeout_start_sec": {
                    "value": self.cfg.timeout_start_sec,
                    "source": "muzlatilmagan; §9.2 (i) TimeoutStartSec MEXANIZM",
                    "calibration_required": True,
                },
                "pressure_target_rate": {
                    "value": dict(PRESSURE_TARGET_RATE),
                    "source": "§9.3 bandlar (P1 20-35%, P2 60-80%); "
                              "docs/architecture/10-pressure-dozalash.md §3.1 "
                              "nishon->erishilgan xaritasini O'LCHADI: P1=0.30 "
                              "-> epizod medianalarining medianasi 0.2810 "
                              "(10/13 band ichida, §3.3); P2=0.60 -> 0.7023 "
                              "(8/11 band ichida, §3.4); avvalgi P2=0.70 "
                              "-> 0.8868, ya'ni band USTIDA (over-doza)",
                    # Nishonlar endi IKKISI HAM o'lchangan (§3.1), lekin xarita
                    # chiziqli emas va monoton emas, boshqarish ~5.7× qo'polroq
                    # (OQ-3) -- qiymatlar EMPIRIK. MemoryHigh o'zgarsa qayta
                    # o'lchanadi (OQ-11).
                    "calibration_required": False,
                },
                # OQ-2 ning tuzatilishi: dial endi OSHKORA argv'da (qoida 17).
                "step_mb": {
                    "value": PRESSURE_STEP_MB,
                    "source": "docs/architecture/10-pressure-dozalash.md §2.2 "
                              "dial sweep'i (step_mb=16 -> base 160 -> "
                              "erishilgan 0.0000 NOL doza; step_mb=8 -> 176 -> "
                              "0.0138; step_mb=4 -> 184 -> 0.3344) va §2.6 ning "
                              "kalibrlangan dial'i; OQ-2",
                    "calibration_required": False,
                },
                "base_mb": {
                    "value": dict(PRESSURE_BASE_MB),
                    "source": "docs/architecture/10-pressure-dozalash.md §2.6 "
                              f"(P0=160 §3.2, P1=P2=184 §2.2 D2); overhead "
                              f"{PRESSURE_OVERHEAD_MB} MiB O'LCHANGAN (§2.2), "
                              "demak 184+25.3=209.3 > 192 breach, "
                              "160+25.3=185.3 < 192 breach YO'Q; ishchi oyna "
                              "TOR -- 184 yagona ishlaydigan qiymat, 188 guard "
                              "trip, 196 §9.4 invariant 2 ni buzdi (§3.6); "
                              "OQ-2",
                    "calibration_required": False,
                    # Breach sharti SHU RUN ning `MemoryHigh` i bilan
                    # HISOBLANADI, hardcode qilinmaydi. `--memory-high`
                    # runtime bayrog'i, demak regressiya testi uni tutib
                    # qolmaydi -- bu yerda nol doza KO'RINADI (§2.5).
                    "dose_arithmetic": {
                        level: pressure_dose_arithmetic(
                            level, self.cfg.memory_high)
                        for level in PRESSURE_LEVELS
                    },
                },
                "interval_ms": {
                    "value": PRESSURE_INTERVAL_MS,
                    "source": "docs/architecture/10-pressure-dozalash.md §2.6 "
                              "(kalibrlangan control tik'i; pressure.py ning "
                              "modul default'i bilan TASODIFAN bir xil, demak "
                              "oshkora beriladi -- qoida 17); §3.5: 250 ms tik "
                              "+ 2 s PSI oynasi + 4 MiB blok granularligi "
                              "bandni UZLUKSIZ ushlash uchun qo'pol (OQ-3)",
                    "calibration_required": False,
                },
                "ramp_above_threshold_s": {
                    "value": self.timeline.ramp_above_threshold_s,
                    "source": "schedule.RAMP_ABOVE_THRESHOLD_S -- §9.4 bu qiymatni "
                              "dosing kalibratsiyasidan olishni talab qiladi va "
                              "u ENDI OLINDI: docs/architecture/"
                              "10-pressure-dozalash.md §4.1 kalibrlangan dial'da "
                              "(base_mb=184, step_mb=4, MemoryHigh=192M, "
                              "MemoryMax=2G) 29 epizoddan 29 tasida AYNAN "
                              "0.000 s O'LCHADI (ramp tezligi "
                              "min=p50=max=0.0000, §8.4 ning quiescence "
                              "chegarasi 0.05 dan yuqori namuna YO'Q), §4.2 esa "
                              "§9.4 invariant 2 ni son bilan yozadi; bu "
                              "PREREGISTRATION.md §21.7 ning \"nol dozadagi "
                              "qiymat kalibratsiya EMAS\" e'tirozini YOPADI, "
                              "chunki o'lchov HAQIQIY doza ostida "
                              "(erishilgan p50 0.223..0.921) bajarilgan; "
                              "avvalgi 3.0 esa o'z izohida TAXMIN deb "
                              "belgilangan edi",
                    # O'LCHANDI, demak belgi YECHILADI. Boolean'ning O'ZI
                    # yetarli emas -- `base_mb.dose_arithmetic` bilan bir xil
                    # uslubda, da'vo SHU RUN ning timeline'idan HISOBLANADI.
                    "calibration_required": False,
                    "calibration": {
                        "measured_s": RAMP_ABOVE_THRESHOLD_MEASURED_S,
                        "measured_in": "docs/architecture/"
                                       "10-pressure-dozalash.md §4.1",
                        "measured_episodes": 29,
                        "measured_episodes_at_value": 29,
                        "measured_dial": {
                            "base_mb": PRESSURE_BASE_MB["P2"],
                            "step_mb": PRESSURE_STEP_MB,
                            "memory_high": self.cfg.memory_high,
                        },
                        "planned_s": self.timeline.ramp_above_threshold_s,
                        # REJA MINUS O'LCHOV. 0.0 = rejada zaxira YO'Q, ya'ni
                        # o'lchangan ramp 0.000 s dan OSHSA reja buziladi --
                        # pastdagi CHEKLOV (`run_meta_payload`) aynan shu
                        # haqida. Zaxira YARATISH uchun konstanta
                        # kattalashtirilmaydi.
                        "plan_slack_s": (self.timeline.ramp_above_threshold_s
                                         - RAMP_ABOVE_THRESHOLD_MEASURED_S),
                        # §9.4 invariant 2 ning zaxirasi -- SHU timeline'dan.
                        "guard_sustain_headroom_s": (
                            self.timeline.guard_sustain_window_s
                            - (self.timeline.hold_s
                               + self.timeline.ramp_above_threshold_s)),
                    },
                },
            },
        }
        payload.pop("schema_version")
        payload.update(prereg)
        return payload

    def write_run_meta(self, payload: dict[str, Any]) -> None:
        """`run_meta` IKKI joyga: `run_meta.json` VA `events.jsonl` record'i.

        NEGA IKKISI: shartnoma §1 `run_meta.json` ni bitta obyekt deb beradi,
        §14.3 esa `run_meta` ni harness RECORD turi deb sanaydi va
        `validate.check_run_meta` uni JSONL oqimidan qidiradi
        (validate.py:478). Bittasini tushirib qoldirish yo shartnomani, yo
        validatorni buzardi.
        """
        with open(self.meta_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        self._emit("run_meta", payload)
        self.writer.flush()

    # --- lab unit'lari ------------------------------------------------------

    def _start_lab_units(self, arm: str) -> dict[str, Any]:
        """SUT + bystander `revixlab.slice` da (majburiyat 8).

        Tartib: bystander BIRINCHI, SUT keyin. NEGA: bystander hech qachon
        fault qilinmaydi va u pressure boshlanishidan oldin barqaror bo'lishi
        kerak -- u spillover detektori, demak uning holati fault'ga EMAS,
        faqat atrof-muhitga javob berishi kerak.
        """
        out: dict[str, Any] = {}
        for unit, bystander in ((BYSTANDER_UNIT, True), (SUT_UNIT, False)):
            props = self._sut_properties(arm, bystander=bystander)
            out[unit] = {"job": self.pf.start_transient(unit, props),
                         "properties_sent": _jsonable(props)}
        for unit in (BYSTANDER_UNIT, SUT_UNIT):
            out[unit]["active"] = self.pf.wait_for_active(unit, ACTIVE_TIMEOUT_S)
        return out

    def _stop_lab_units(self) -> dict[str, Any]:
        """Lab unit'larini yig'ishtiradi (idempotent)."""
        return self.pf.teardown(
            units=[PRESS_UNIT, SUT_UNIT, BYSTANDER_UNIT],
            unit_patterns=(), slices=(), kill=False, reset_failed=True)

    # --- trial --------------------------------------------------------------

    def run_trial(self, trial: sch.Trial, index: int) -> dict[str, Any]:
        """Bitta trial. AYNAN BITTA `trial_end` kafolatlanadi (majburiyat 5).

        VAQT TUZILISHI -- SETUP RECORD OYNASIDAN TASHQARIDA, va bu QARORNING
        SABABI:

            [setup: unit'lar + prober ko'tariladi]   <- trial_begin'dan OLDIN
            trial_begin (t0)
            t0 .. t0+preflight_s            sog'lom kuzatuv (fault yo'q)
            t0+preflight_s .. +baseline_s   R_ref oynasi
            .. +ramp_s                      pressure ramp
            .. +hold_s                      hold; injeksiya hold'ga 3 s kirgach
            t0 + T_trial                    horizon oxiri = trial_end.mono_us
            [washout]                       <- trial_end oynasidan TASHQARIDA

        NEGA setup `trial_begin` dan OLDIN:
          (a) Prober SUT `active` bo'lgandan KEYIN ishga tushishi SHART
              (`_start_prober` docstring'i: aks holda `conn_refused`
              probe'lari `find_failure_onsets` uchun SOXTA failure onset
              yasaydi va `reduce` ning `vr` i -- `episodes[0].vr` --
              fault epizodini emas, soxta epizodni o'qib qoladi);
          (b) lekin prober `trial_begin` dan KEYIN ishga tushsa, trial
              boshida probe'siz oraliq qolardi, ya'ni YETAKCHI BO'SHLIQ
              (validator uni rad etadi; `reduce.probe_gaps` esa ko'rmaydi --
              shartnoma §1.2 dagi ochiq ziddiyat).
        Ikkisini bir vaqtda qanoatlantiradigan yagona tartib: setup
        record oynasidan OLDIN tugaydi, `t0` esa prober allaqachon
        probe qilayotgan paytda belgilanadi. Setup narxi o'lchanadi
        (`timing.setup_us`) va majburiyat 9 ga kiradi.
        """
        arm = str(trial.level("arm"))
        level = str(trial.level("pressure_level"))
        facts_kw: dict[str, bool] = {}
        anomalies: list[str] = []
        timing = TrialTiming(begin_mono_us=0)
        washout: dict[str, Any] = {"state": None, "observations": 0}
        detail: dict[str, Any] = {}
        watchers: dict[str, Any] = {}
        ev_before: dict[str, dict[str, int]] = {}
        host_before: dict[str, Any] = {}
        setup_error: BaseException | None = None

        # --- SETUP: record oynasidan TASHQARIDA ---------------------------
        try:
            if level != "P0" and not self.cfg.allow_pressure:
                raise PressureNotAllowedError(
                    f"trial {trial.trial_id} pressure darajasi {level}, lekin "
                    "--allow-pressure berilmagan"
                )
            # Kuzatuvchilar unit YARATILISHIDAN OLDIN: obyekt yo'li nomdan
            # hisoblanadi, demak eng birinchi o'tish ham ko'rinadi
            # (units.py:1165) -- F_sd detektori hech narsa yo'qotmaydi.
            for unit, scope in ((SUT_UNIT, SCOPE_SUT),
                                (BYSTANDER_UNIT, SCOPE_BYSTANDER)):
                w = self.pf.watcher(unit)
                w.start(seed=False)
                watchers[unit] = (w, scope)
            ev_before = self._memory_events_snapshot()
            host_before = {"vmstat": self.pf.vmstat(),
                           "meminfo": self.pf.meminfo()}
            t_setup0 = self.pf.mono_us()
            detail["lab"] = self._start_lab_units(arm)
            detail["prober"] = self._start_prober(trial)
            timing.setup_us = self.pf.mono_us() - t_setup0
        except Exception as exc:  # noqa: BLE001
            setup_error = exc

        # Setup fazasidagi `unit_state` record'lari `trial_id=None` bilan
        # yoziladi. NEGA: ularning avtoritet vaqti (`recv_mono_us`)
        # `trial_begin` dan OLDIN -- unit'lar record oynasi ochilishidan
        # oldin ko'tarildi. Trial'ga bog'lansa, ular
        # `[trial_begin, trial_end]` oynasidan tashqarida qolib,
        # `validate.check_trial_events` ning `trial_event_outside_window`
        # xatosini berardi, va §1.2 dagi hodisa tartibi ma'nosiz bo'lardi.
        # Ma'lumot YO'QOLMAYDI: record oqimda qoladi, faqat trial'ga
        # kirmaydi (`reduce.split_trials` `trial_id` bo'yicha ajratadi).
        self._drain_watchers(watchers, None)

        # --- RECORD OYNASI boshlanadi -------------------------------------
        # `trial_begin` setup yiqilsa HAM yoziladi: aks holda trial
        # ma'lumotdan BUTUNLAY yo'qolardi, va §14.6 invariant 1 (har
        # `trial_begin` ning `trial_end` i bor) "trial umuman yo'q" holatini
        # TUTMAYDI. Yo'qolgan trial -- jimgina eksklyuziyaning eng yomon
        # shakli (§12).
        timing.begin_mono_us = self.pf.mono_us()
        self._emit_trial_begin(trial, index, arm, level, timing.begin_mono_us)
        try:
            if setup_error is not None:
                raise setup_error
            self._drain_watchers(watchers, trial)
            self._emit_env_snapshot(trial, "trial_begin", index,
                                    mono=timing.begin_mono_us)

            # --- faza deadline'lari (absolut, monotonic) -------------------
            base = timing.begin_mono_us + round(self.timeline.preflight_s * 1e6)
            timing.baseline_start_mono_us = base
            self._wait_until(base, watchers, trial)

            # --- R_ref baseline (§9.4, 10 s) -------------------------------
            baseline_end = base + round(self.timeline.baseline_s * 1e6)
            self._wait_until(baseline_end, watchers, trial)
            self._emit(
                "baseline_window",
                {
                    "mono_us_begin": base,
                    "mono_us_end": baseline_end,
                    # Throughput'ni DRIVER HISOBLAMAYDI: `progress` probe
                    # oqimida (prober'ning CSV'si), va `reduce.window_throughput`
                    # uni AYNAN shu oynada hisoblaydi. None = o'lchanmadi
                    # (nol EMAS).
                    "throughput": None,
                    "throughput_source": "reduce.window_throughput(baseline_window)",
                    "duration_us": baseline_end - base,
                },
                trial=trial, mono=baseline_end,
            )

            # --- ramp + pressure (§9.4) ------------------------------------
            ramp_start = baseline_end
            hold_start = ramp_start + round(self.timeline.ramp_s * 1e6)
            pressure_off = hold_start + round(self.timeline.hold_s * 1e6)
            if self.cfg.allow_pressure:
                detail["pressure"] = self._start_pressure(
                    trial, level, (pressure_off - ramp_start) / 1e6)
            else:
                detail["pressure"] = {
                    "started": False,
                    "reason": "pressure_not_allowed (00-pilot-topologiya.md §6)",
                }
            self._wait_until(
                hold_start + round(self.timeline.injection_offset_s * 1e6),
                watchers, trial)

            # --- injeksiya (§3, 03-sut-protokoli.md §5) --------------------
            detail["fault"] = self._inject_fault(trial)

            # --- hold oxiri: pressure o'chadi ------------------------------
            self._wait_until(pressure_off, watchers, trial)
            timing.pressure_off_mono_us = pressure_off
            if self.cfg.allow_pressure:
                self.pf.stop(PRESS_UNIT)

            # --- horizon: T_trial gacha kuzatuv davom etadi ----------------
            # `pressure_off` dan keyin yana `w_stab_s + P`: §4 VR oynasining
            # TO'LIQ kuzatilishini talab qiladi, va `t_pressure_off` oynaning
            # eng kech qonuniy BOSHLANISHI (`t_trial_us` docstring'i).
            horizon_end = timing.begin_mono_us + self.t_trial_us
            self._wait_until(horizon_end, watchers, trial)
            timing.horizon_end_mono_us = horizon_end

            # --- horizon HOLATI instrumentatsiya to'xtashidan OLDIN --------
            # NEGA shu tartibda: `horizon_ended_down` va
            # `probe_gap_exceeded` faktlari horizon NUQTASIDAGI holatga
            # tegishli (§6.2). Prober to'xtatilgandan keyin o'qisak, uning
            # holati HAR DOIM `inactive` bo'lib, har trial soxta `censored`
            # bo'lardi.
            state = self._sut_state
            state["sut_state_at_horizon"] = self.pf.active_state(SUT_UNIT)
            state["prober_state_at_horizon"] = self.pf.active_state(PROBER_UNIT)
            state["bystander_state_at_horizon"] = self.pf.active_state(
                BYSTANDER_UNIT)

            # --- horizon tugadi: instrumentatsiya to'xtaydi ----------------
            # Prober horizon'dan KEYIN to'xtatiladi -> OXIRGI bo'shliq
            # bo'lmaydi (validator uni rad etadi).
            self.pf.stop(PROBER_UNIT)
            self._drain_watchers(watchers, trial)
            self._emit_env_snapshot(trial, "trial_end", index,
                                    mono=horizon_end)
            ev_after = self._memory_events_snapshot()
            self._emit_cgroup_events(trial, ev_before, ev_after, horizon_end)
            host_after = {"vmstat": self.pf.vmstat(),
                          "meminfo": self.pf.meminfo()}

            # --- faktlar (§12) ---------------------------------------------
            facts_kw, fact_detail = self._collect_facts(
                trial, timing, watchers, host_before, host_after,
                ev_before, ev_after)
            detail["facts"] = fact_detail
            anomalies.extend(fact_detail.get("anomalies", []))

            # --- property dump TIRIK unit'lar ustida (§1.1) ----------------
            t_dump0 = self.pf.mono_us()
            detail["units_show"] = self._dump_live_units()
            timing.dump_us = self.pf.mono_us() - t_dump0

            # --- washout (§8.4) --------------------------------------------
            t_w0 = self.pf.mono_us()
            washout = self._washout(trial)
            timing.washout_us = self.pf.mono_us() - t_w0
            facts_kw["washout_timed_out"] = bool(washout.get("timed_out"))

        except Exception as exc:  # noqa: BLE001 -- qoida 13
            self._harness_error(f"trial:{trial.trial_id}", exc, trial=trial)
            facts_kw["harness_error"] = True
            detail["exception"] = repr(exc)
        finally:
            t_t0 = self.pf.mono_us()
            try:
                # HORIZON'DAN KEYINGI record'lar `trial_id=None` bilan
                # yoziladi. NEGA: washout'ning `cgroup.kill` i SUT'ni
                # o'ldiradi, va bu o'tishni trial'ga bog'lash BIZNING O'Z
                # kill'imizni o'lchov ichida ko'rsatardi -- `compute_d_sd`
                # soxta downtime, `down_at_horizon` soxta censoring berardi.
                # `reduce.split_trials` (reduce.py:453) `trial_id` bo'yicha
                # ajratadi, demak None record'lar trial'ga kirmaydi, lekin
                # ma'lumot YO'QOLMAYDI -- u oqimda qoladi.
                self._drain_watchers(watchers, None)
                for w, _scope in watchers.values():
                    w.stop()
            except Exception as exc:  # noqa: BLE001
                self._harness_error("watcher_stop", exc, trial=trial)
            try:
                self._stop_lab_units()
            except Exception as exc:  # noqa: BLE001
                self._harness_error("lab_teardown", exc, trial=trial)
            timing.teardown_us = self.pf.mono_us() - t_t0
            timing.end_mono_us = self.pf.mono_us()
            if not timing.horizon_end_mono_us:
                timing.horizon_end_mono_us = timing.end_mono_us
            verdict = self._emit_trial_end(
                trial, timing, facts_kw, washout, anomalies, detail)
        return verdict

    def _emit_trial_begin(self, trial: sch.Trial, index: int, arm: str,
                          level: str, mono: int) -> None:
        """`trial_begin` (shartnoma §1.2 va `driver-contract/v1.1` §4.3).

        `trial_id` va `block_index` FAQAT ENVELOPE'da -- payload'da bo'lsa
        `Emitter.record()` istisno tashlaydi (schema.py:236). Shuning uchun
        `schedule.Trial.as_dict()` HECH QACHON payload sifatida berilmaydi:
        u ikkala kalitni ham o'z ichiga oladi (schedule.py:179).
        """
        self._began.add(trial.trial_id)
        self._emit(
            "trial_begin",
            {
                "arm": arm,
                # `reduce.Trial.pressure_band` AYNAN shu nomni o'qiydi
                # (reduce.py:389); `pressure_level` -- `schedule` dagi faktor
                # nomi (shartnoma §1.2). Ikkisi ham yoziladi, qiymat BIR XIL,
                # shunda nom moslashuvi ma'lumotda KO'RINADI.
                "pressure_band": level,
                "pressure_level": level,
                "fault_class": FAULT_CLASS,
                "position_in_block": trial.position_in_block,
                "trial_index": index,
                "levels": trial.levels_dict,
                "planned_timeline": self.timeline.as_dict(),
                "t_trial_us": self.t_trial_us,
                "t_trial_formula": T_TRIAL_FORMULA,
                "pressure_target_rate": pressure_target_rate(level),
                "arm_properties": arm_properties(arm),
                "policy_delay_us": ARM_POLICY_DELAY_US.get(arm),
            },
            trial=trial, mono=mono,
        )

    def _emit_trial_end(
        self,
        trial: sch.Trial,
        timing: TrialTiming,
        facts_kw: dict[str, bool],
        washout: dict[str, Any],
        anomalies: Sequence[str],
        detail: dict[str, Any],
    ) -> dict[str, Any]:
        """AYNAN BITTA `trial_end` + AYNAN BITTA disposition (§12).

        Takroriy chaqiruv `DriverError` tashlaydi: majburiyat 5 ni DIQQAT
        bilan emas, STRUKTURA bilan ta'minlaymiz.

        Envelope `mono_us` = horizon oxiri, ya'ni `trial_begin.mono_us +
        T_trial` (setup overrun bo'lmagan holatda). NEGA shunday: bu
        `reduce.Trial.end_us` ning manbasi (reduce.py:406) va right censoring
        AYNAN shu nuqtada bo'ladi (§6.2). Record'ning O'ZI washout'dan keyin
        yoziladi (chunki `washout_timeout` disposition'i §12 enum'ida bor),
        shuning uchun yozish vaqti ALOHIDA field'da beriladi -- vaqt
        TO'QILMAYDI, ikkisi ham ko'rinadi.
        """
        if trial.trial_id in self._ended:
            raise DriverError(
                f"trial {trial.trial_id} uchun ikkinchi trial_end urinishi -- "
                "§12 AYNAN bittani talab qiladi"
            )
        self._ended.add(trial.trial_id)
        facts = sch.TrialFacts(**facts_kw)
        verdict = sch.explain_disposition(facts)
        self._disposition_counts[verdict.disposition] = (
            self._disposition_counts.get(verdict.disposition, 0) + 1)

        overhead_s = max(
            0.0,
            (timing.end_mono_us - timing.begin_mono_us) / 1e6
            - self.timeline.total_s,
        )
        self._trial_overheads.append(overhead_s)
        payload = {
            "disposition": verdict.disposition,
            "reason": verdict.rule,
            "matched_rules": list(verdict.matched_rules),
            "facts": facts.as_dict(),
            "anomalies": list(anomalies),
            "washout": washout,
            "timing": timing.as_dict(),
            "mono_us_record_written": self.pf.mono_us(),
            "t_trial_planned_us": self.t_trial_us,
            "t_trial_actual_us": timing.horizon_end_mono_us - timing.begin_mono_us,
            # Majburiyat 9: har trial O'Z qo'shimcha vaqtini beradi.
            "overhead_us": round(overhead_s * 1e6),
            "overhead_s": overhead_s,
            "overhead_definition": ("wall - TrialTimeline.total_s "
                                    "(estimate_campaign ta'rifi)"),
            "detail": detail,
        }
        self._emit("trial_end", payload, trial=trial,
                   mono=timing.horizon_end_mono_us)
        self.writer.flush()
        return {"trial_id": trial.trial_id,
                "disposition": verdict.disposition,
                "rule": verdict.rule,
                "overhead_s": overhead_s}

    # --- trial ichidagi qadamlar -------------------------------------------

    def _start_prober(self, trial: sch.Trial) -> dict[str, Any]:
        """Prober -- `revixmon.slice` da, SUT `active` BO'LGANDAN KEYIN.

        TARTIB QARORI VA UNING SABABI (shartnomada ko'rsatilgan tartibdan
        chetlashish, shuning uchun OCHIQ yoziladi):

        Prober SUT'dan OLDIN ishga tushsa, uning birinchi probe'lari
        `conn_refused` bo'ladi va ular shu trial'ning `trial_id` i bilan
        yoziladi. `reduce.find_failure_onsets` k_f=3 ketma-ket buzilishni
        FAILURE ONSET deb oladi, demak trial boshida SOXTA epizod paydo
        bo'lardi. `reduce.reduce_trial` esa `vr` ni `episodes[0].vr` dan
        oladi (reduce.py:1609) -- ya'ni birlamchi endpoint fault epizodini
        emas, SOXTA epizodni o'qib qolardi. Bu ma'lumot ixtiro qilish bo'lardi.

        Xavfsizlik tartibi (guard BIRINCHI, pressure OXIRGI) buzilmaydi; va
        birinchi unit o'tishi yo'qolmaydi, chunki F_sd detektori
        `UnitWatcher` orqali unit YARATILISHIDAN OLDIN obuna bo'ladi.
        """
        argv = self._prober_argv(trial)
        props = self._mon_unit_properties(
            argv, runtime_max_sec=self.timeline.worst_case_total_s + 60.0)
        props["Description"] = f"REVIX prober {trial.trial_id}"
        return {"job": self.pf.start_transient(PROBER_UNIT, props),
                "argv": argv}

    def _start_pressure(self, trial: sch.Trial, level: str,
                        max_seconds: float) -> dict[str, Any]:
        """Generator `revixlab.slice` da (majburiyat 8).

        `--allow-pressure` BO'LMASA bu metod CHAQIRILMAYDI (dizayn qoidasi 16).
        """
        if not self.cfg.allow_pressure:
            raise PressureNotAllowedError(
                "pressure generatori --allow-pressure bo'lmaganda talab qilindi")
        props = self._pressure_properties(max_seconds)
        props["ExecStart"] = self._pressure_argv(level, max_seconds)
        job = self.pf.start_transient(PRESS_UNIT, props)
        dump = None
        try:
            dump = self.pf.dump_unit_properties(PRESS_UNIT)
            self.units_show[PRESS_UNIT] = dump
        except Exception as exc:  # noqa: BLE001
            self._harness_error("pressure_dump", exc, trial=trial)
        # `step_mb` / `base_mb` HAR TRIALDA yoziladi, nafaqat `run_meta` da.
        # NEGA: 10-pressure-dozalash.md §2.5 ning eng xavfli jihati -- nol
        # doza chiqishda HECH QANDAY iz qoldirmasligi edi. Dial trial
        # record'ida bo'lsa, `P1`/`P2` ning nol dozasi oqimdan KO'RINADI.
        return {"started": True, "level": level,
                "target_rate": pressure_target_rate(level),
                "step_mb": PRESSURE_STEP_MB,
                "base_mb": pressure_base_mb(level),
                "interval_ms": PRESSURE_INTERVAL_MS,
                "max_seconds": max_seconds, "job": job,
                "units_show_valid": (dump or {}).get("dump_valid")}

    def _inject_fault(self, trial: sch.Trial) -> dict[str, Any]:
        """`FAULT exit code=1` -> `fault_inject` (§3, protokol §5).

        §3 injeksiya vaqtini IKKI TOMONDAN bracket qilishni talab qiladi:
        harness'ning `mono_us_before_call` / `mono_us_after_call`, VA SUT'ning
        o'z "fault armed" record'i. SUT tomoni bu yerda javobdagi
        `OK armed=<kind>` bilan olinadi.

        SUT tomonini qanday olamiz: injeksiyadan DARHOL OLDIN O'Z ulanishida
        bitta `PROBE` yuborilади va javobdagi `mono_us` -- SUT'ning O'Z
        soati -- `sut_mono_us_before` sifatida yoziladi.
          * protokol §4.5 kafolatlaydi: probe'ga javob berish `progress` ni
            OSHIRMAYDI, demak prober'ning kuzatuvi buzilmaydi;
          * bu trial'ga BITTA qo'shimcha ulanish, ya'ni arm'lar bo'yicha
            AYNI narx (§8.2 probe narxi bir xil ushlanadi);
          * bu XULOSA emas, SUT'ning o'z o'lchovi.

        QOLGAN CHEKLOV, ochiq yoziladi: bu BIR TOMONLAMA namuna
        (injeksiyadan oldin), protokol §5 ning `stderr` dagi
        `FAULT ARMED <kind> mono_us=<u64>` satri EMAS. O'sha satr
        saqlanmaydi, chunki `StandardError=null` (§3.4: o'lchov ma'lumoti
        journald'dan o'tmaydi) va run katalogi olti faylga MUZLATILGAN
        (shartnoma §1). Shuning uchun `sut_mono_us` = `None` -- jimgina nol
        yozilmaydi -- va `sut_mono_us_before` uning o'rnini TO'LIQ
        bosmaydi.
        """
        sock = self._sut_socket("sut")
        pre = self.pf.sut_command(sock, "PROBE")
        sut_before = _parse_sut_mono(pre.get("reply"))
        cmd = f"FAULT {FAULT_KIND} code={FAULT_EXIT_CODE}"
        t0 = self.pf.mono_us()
        res = self.pf.sut_command(sock, cmd)
        t1 = self.pf.mono_us()
        reply = res.get("reply") or ""
        m = ARMED_RE.match(reply.strip())
        payload = {
            "fault_id": f"{trial.trial_id}:f0",
            # `kind` = protokol §5 endpoint nomi. `reduce.evaluate_fr_b` bu
            # field'ni fault KLASSI uchun zaxira sifatida o'qiydi
            # (reduce.py:1550), lekin `trial_begin.fault_class` HAR DOIM
            # yozilgani uchun o'sha zaxira yo'liga yetib bo'lmaydi.
            "kind": FAULT_KIND,
            "fault_class": FAULT_CLASS,
            "params": {"code": FAULT_EXIT_CODE},
            "command": cmd,
            "mono_us_before_call": t0,
            "mono_us_after_call": t1,
            "bracket_us": t1 - t0,
            "sut_ack": reply or None,
            "sut_armed": m.group(1) if m else None,
            # SUT'ning O'Z soati, injeksiyadan DARHOL OLDIN (protokol §3).
            "sut_mono_us_before": sut_before,
            "sut_probe_reply": pre.get("reply"),
            # `stderr` dagi `FAULT ARMED` satri saqlanmaydi -> o'lchanmadi.
            "sut_mono_us": None,
            "sut_mono_us_source": (
                "pre_injection_probe" if sut_before is not None
                else "unavailable"),
            "sut_mono_us_limitation": (
                "bir tomonlama namuna (injeksiyadan oldin); protokol §5 ning "
                "stderr `FAULT ARMED mono_us=` satri StandardError=null va "
                "muzlatilgan olti faylli katalog sababli saqlanmaydi"),
            "errno": res.get("errno"),
            "error": res.get("error"),
        }
        self._emit("fault_inject", payload, trial=trial, mono=t1)
        if m is None:
            raise DriverError(
                f"SUT fault ack bermadi: {res!r} -- injeksiya tasdiqlanmagan, "
                "demak trial o'lchovi ishonchsiz"
            )
        return payload

    def _emit_env_snapshot(self, trial: sch.Trial, phase: str,
                           index: int, mono: int | None = None) -> None:
        """`env_snapshot` -- §8.3 va §8.5 kovariatalari.

        `revixmon.slice` snapshot'i §8.2 ning "harness'ning o'z `CPUUsageNSec`
        / `MemoryPeak` log'lanadi" talabini bajaradi (`cpu_stat` va
        `memory_peak` `cgroup.snapshot_cgroup` ichida).

        VAQT: `mono` -- snapshot TEGISHLI bo'lgan trial CHEGARASI (trial
        boshi yoki horizon oxiri), `mono_us_read` esa o'qish AMALDA qachon
        tugagani. NEGA ikkisi alohida: chegara kuzatuvini chegaraning O'Z
        instantida o'qib bo'lmaydi -- cgroup fayllarini o'qish vaqt oladi,
        demak o'qish vaqti horizon'dan bir necha yuz mikrosekund KEYIN
        bo'ladi va record `[trial_begin, trial_end]` oynasidan chiqib
        ketardi (`validate.check_trial_events`). Bu §14.4 ning
        `unit_state` da ishlatilgan naqshi bilan AYNI: avtoritet vaqt va
        qabul/o'qish vaqti aralashtirilmaydi, ikkisi ham yoziladi.
        """
        scopes: dict[str, Any] = {}
        for scope, path in self._scope_paths().items():
            try:
                scopes[scope] = self.pf.snapshot_cgroup(path)
            except Exception as exc:  # noqa: BLE001
                scopes[scope] = {"error": repr(exc)}
        mi = self.pf.meminfo()
        self._emit(
            "env_snapshot",
            {
                "phase": phase,
                # §8.3: trial indeksi monoton drift testi uchun kovariata.
                "trial_index": index,
                "scopes": scopes,
                "host": {
                    "mem_available_kb": mi.get("MemAvailable"),
                    "mem_free_kb": mi.get("MemFree"),
                    "cached_kb": mi.get("Cached"),
                    "swap_free_kb": mi.get("SwapFree"),
                    "vmstat_oom_kill": self.pf.vmstat().get("oom_kill"),
                },
                # §8.5 har trial chegarasida per-CPU `scaling_cur_freq` va
                # `thermal_zone*/temp` ni talab qiladi. Bu mashinada IKKISI
                # HAM YO'Q (o'lchangan: `scaling_cur_freq` 0 ta moslik,
                # `/sys/class/thermal/` da faqat `cooling_device*`). Shuning
                # uchun kalitlar MAVJUD va qiymati `None` -- "o'lchanmadi".
                # Kalitni butunlay tushirib qoldirish BOSHQA da'vo bo'lardi
                # ("bu kovariata umuman mavjud emas"), va bo'sh ro'yxat yoki 0
                # esa O'LCHOV kabi o'qilardi (§15.4).
                "cpu_freq_khz": None,
                "thermal_c": None,
                "dvfs_source": "cpufreq/thermal_zone sysfs mavjud emas",
                # Guest generation markeri HAR chegarada: kampaniya o'rtasidagi
                # restart MA'LUMOTDA ko'rinadi, faqat oxirida emas.
                "guest_generation": self.pf.guest_generation(),
                # O'qish AMALDA qachon tugadi (chegara vaqtidan ALOHIDA).
                "mono_us_read": self.pf.mono_us(),
            },
            trial=trial, mono=mono,
        )

    def _scope_paths(self) -> dict[str, str]:
        lab = str(self.lab_cgroup)
        return {
            SCOPE_LAB: lab,
            SCOPE_SUT: f"{lab}/{SUT_UNIT}",
            SCOPE_BYSTANDER: f"{lab}/{BYSTANDER_UNIT}",
            SCOPE_PRESS: f"{lab}/{PRESS_UNIT}",
            SCOPE_MON: str(self.mon_cgroup),
            SCOPE_USER: self.pf.user_cgroup(),
        }

    def _memory_events_snapshot(self) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for scope, path in self._scope_paths().items():
            try:
                out[scope] = self.pf.memory_events(path)
            except Exception:  # noqa: BLE001 -- o'qilmasa bo'sh (None semantikasi)
                out[scope] = {}
        return out

    def _emit_cgroup_events(self, trial: sch.Trial,
                            before: dict[str, dict[str, int]],
                            after: dict[str, dict[str, int]],
                            mono: int) -> None:
        """Trial'ga AYNAN BITTA `cgroup_events`, SUT scope'i uchun.

        Sababi `cgroup_events_payload` docstring'ida: `reduce._oom_series`
        scope filtrisiz ishlaydi va aralash qator §4 ning 6-bandini yolg'on
        qilardi; boshqa scope'lar `other_scopes` da va `env_snapshot` da.
        """
        self._emit("cgroup_events",
                   cgroup_events_payload(before, after, scope=SCOPE_SUT),
                   trial=trial, mono=mono)

    def _dump_live_units(self) -> dict[str, Any]:
        """Property dump'i FAQAT TIRIK unit ustida (01-...-tekshiruvlari §4).

        O'chgan unit uchun `systemctl show` rc=0 va 268 qatorlik DEFAULT
        beradi, ya'ni dump haqiqiy qiymatlarga O'XSHAYDI. `require_alive=True`
        shu holatda `UnitNotAliveError` tashlaydi; biz uni tutamiz va
        `dump_valid=False` sifatida QAYD etamiz -- jimgina default yozilmaydi.
        """
        out: dict[str, Any] = {}
        for unit in (SUT_UNIT, BYSTANDER_UNIT, PROBER_UNIT, GUARD_UNIT,
                     PSI_UNIT, LAB_SLICE, MON_SLICE):
            if unit in self.units_show and \
                    self.units_show[unit].get("dump_valid"):
                continue
            try:
                dump = self.pf.dump_unit_properties(unit)
            except Exception as exc:  # noqa: BLE001
                dump = {"unit": unit, "dump_valid": False, "error": repr(exc)}
            out[unit] = {"dump_valid": dump.get("dump_valid"),
                         "load_state": dump.get("load_state")}
            self.units_show[unit] = dump
        return out

    # --- kuzatuvchi drenaji -------------------------------------------------

    def _drain_watchers(self, watchers: dict[str, Any],
                        trial: sch.Trial | None) -> int:
        """`unit_state` record'larini buferdan olib yozadi.

        NEGA SINK EMAS, DRENAJ: `UnitWatcher` sink'ini GLib loop THREAD'i
        chaqiradi. Sink'dan yozsak, `Emitter._seq` va `JsonlWriter` ikki
        thread'dan ishlatilardi va `seq` tartibi buzilib, §14.6 invariant 3
        (bo'shliq yo'q) soxta ishlardi. Shuning uchun yozish FAQAT asosiy
        thread'da, drenaj orqali. Kechikish o'lchovni buzmaydi: envelope
        `mono_us` = `recv_mono_us`, va systemd'ning O'Z timestamp'lari
        alohida field'larda qoladi (§14.4).
        """
        n = 0
        for key, value in watchers.items():
            w, scope = value
            if not hasattr(w, "drain"):
                continue
            for raw in w.drain():
                payload = unit_state_payload(raw, scope)
                self._emit("unit_state", payload, trial=trial,
                           mono=payload.get("recv_mono_us"))
                n += 1
                if trial is not None:
                    self._note_unit_state(trial, scope, payload)
        return n

    def _note_unit_state(self, trial: sch.Trial, scope: str,
                         payload: dict[str, Any]) -> None:
        """`action` / `actor_signal` ni KUZATILGAN o'tishdan chiqaradi.

        P1 da AKTOR systemd'ning o'zi (`Restart=on-failure`), driver hech
        qanday action YUBORMAYDI. Shuning uchun `action` record'i
        KUZATUVdan tug'iladi: yangi `InvocationID` = restart bajarildi.

        `no_action` arm'ida (`Restart=no`) `action` record'i YOZILMAYDI --
        `reduce.build_episodes` bu holatni ochiq qo'llab-quvvatlaydi
        (reduce.py:1197: action bo'lmasa onset anchor bo'ladi). Agar
        `no_action` da baribir invocation o'zgarsa, bu ANOMALIYA va shunday
        qayd etiladi (VR ni §4 ning 3-bandi baribir bekor qiladi).
        """
        state = self._sut_state
        if scope == SCOPE_BYSTANDER:
            # Bystander -- spillover detektori: u HECH QACHON fault
            # qilinmaydi, demak horizon ichida `active` dan chiqishi
            # KONTAMINATSIYA signalidir (§12).
            st = payload.get("active_state")
            if st is not None and st != "active":
                state["bystander_broke"] = True
            if unsolicited_kill_seen(payload):
                state["bystander_broke"] = True
            return
        if scope != SCOPE_SUT:
            return
        inv = payload.get("invocation_id")
        arm = str(trial.level("arm"))
        if unsolicited_kill_seen(payload):
            # Horizon ichida BIZ hech qachon SIGKILL yubormaymiz (washout'ning
            # `cgroup.kill` i horizon TUGAGANDAN keyin), demak bu bizdan emas.
            state["unsolicited_kill"] = True
        if payload.get("active_state") not in (None, "active"):
            # Chiqayotgan invocation'ning exit vaqti -- `action` ning
            # `t_issue` i uchun YAGONA to'g'ri manba (yangi invocation'ning
            # record'ida `ActiveExit` BO'SH bo'ladi).
            state["last_exit_ts"] = (
                payload.get("active_exit_ts_mono_us")
                or payload.get("exec_main_exit_ts_mono_us")
                or payload.get("recv_mono_us"))
        if inv and state["invocation"] and inv != state["invocation"]:
            # `action` uchun CHIQISH DALILI SHART: restart ta'rifan unit
            # `active` dan chiqqanidan keyin bo'ladi. Dalil bo'lmasa bu
            # "restart" emas, kuzatuvdagi bo'shliq -- va dalilsiz action
            # yozish `validate.check_actions` ni (validate.py:406) yiqitardi,
            # chunki action vaqti yangi invocation record'ining vaqtiga teng
            # bo'lib qolardi. Shuning uchun ANOMALIYA, action EMAS.
            exit_evidence = (state.get("last_exit_ts")
                             or payload.get("active_exit_ts_mono_us")
                             or payload.get("exec_main_exit_ts_mono_us"))
            state["restarts"] += 1
            if exit_evidence is None:
                state["anomalies"].append(
                    "invocation_changed_without_observed_exit")
            elif arm == "A":
                self._emit_action(trial, payload, state["restarts"],
                                  exit_evidence)
            else:
                state["anomalies"].append("invocation_changed_in_no_action")
        if inv:
            state["invocation"] = inv
        if payload.get("active_state") == "active" and inv \
                and inv not in state["active_claimed"]:
            state["active_claimed"].add(inv)
            if state["restarts"] > 0 and arm == "A":
                self._emit_actor_signal(trial, payload, state["restarts"])

    def _emit_action(self, trial: sch.Trial, payload: dict[str, Any],
                     n: int, t_issue: int) -> None:
        """`action` -- systemd'ning restart'i (§14.4, shartnoma §1.2).

        `mono_us` = eski invocation'ning `ActiveExitTimestampMonotonic` i,
        ya'ni systemd `Restart=` qarorini AYNAN qachon qabul qilgan vaqti
        (t_issue). NEGA eng kech emas: `validate.check_actions` har `action`
        dan KEYIN invocation o'zgarishini talab qiladi (validate.py:406),
        demak action vaqti yangi invocation'ning record'laridan QAT'IY oldin
        bo'lishi kerak. `t_begin`/`t_exec` alohida field'larda.

        `policy_delay_us` (`RestartSec`) `L_dec` dan ALOHIDA -- §6.3 soxta
        taqqoslashning oldini oladi (`L_dec` ni `reduce` hisoblaydi).
        """
        arm = str(trial.level("arm"))
        # `t_issue` -- CHIQAYOTGAN invocation'ning exit vaqti, chaqiruvchi
        # tomonidan DALIL sifatida berilgan. NEGA yangi record'ning
        # `recv_mono_us` i ishlatilMAYDI: u yangi `unit_state` record'ining
        # vaqtiga AYNAN TENG bo'lardi, va o'sha holatda
        # `validate._invocation_changed` ning `lo < t` sharti
        # qanoatlanmay, HAR action uchun `action_without_invocation_change`
        # xatosi chiqardi (bu o'lchangan, taxmin emas).
        self._emit(
            "action",
            {
                "action_id": f"{trial.trial_id}:a{n}",
                "actor": "systemd",
                "action_class": "restart",
                "deferred": False,
                "t_issue_mono_us": t_issue,
                "t_begin_mono_us": payload.get("inactive_exit_ts_mono_us"),
                "t_exec_mono_us": payload.get("exec_main_start_ts_mono_us"),
                "policy_delay_us": ARM_POLICY_DELAY_US.get(arm),
                "policy_delay_source": "systemd RestartSec (arm property)",
                "invocation_id": payload.get("invocation_id"),
                "n_restarts": payload.get("n_restarts"),
                "restart_index": n,
            },
            trial=trial, mono=t_issue,
        )

    def _emit_actor_signal(self, trial: sch.Trial, payload: dict[str, Any],
                           n: int) -> None:
        """`actor_signal` -- AKTORNING O'Z DA'VOSI (§5 FR-A birlamchi operandi).

        systemd uchun da'vo: unit `active` holatiga yetdi, ya'ni `Type=notify`
        da `READY=1` qabul qilindi. §14.4 manbani (`actor_signal_source`)
        yozishni SHART qiladi; `reduce.RAW_CONTRACT` esa uni `source` deb
        nomlaydi -- IKKISI HAM yoziladi, qiymat bir xil.
        """
        src = "systemd_unit_active"
        self._emit(
            "actor_signal",
            {
                "success": True,
                "source": src,
                "actor_signal_source": src,
                "actor": "systemd",
                "action_id": f"{trial.trial_id}:a{n}",
                "invocation_id": payload.get("invocation_id"),
                "active_enter_ts_mono_us": payload.get(
                    "active_enter_ts_mono_us"),
            },
            trial=trial,
            mono=(payload.get("active_enter_ts_mono_us")
                  or payload.get("recv_mono_us")),
        )

    # --- faza kutishi -------------------------------------------------------

    def _wait_until(self, deadline_mono_us: int, watchers: dict[str, Any],
                    trial: sch.Trial | None) -> None:
        """Absolut monotonic deadline'gacha kutadi, oraliqda drenaj qiladi.

        ABSOLUT deadline (nisbiy `sleep` emas): nisbiy kutish har fazada
        drift yig'ib, `t_inject` ni rejadan uzoqlashtirardi (§1 vaqt
        disiplinasi).
        """
        self._drain_watchers(watchers, trial)
        while True:
            now = self.pf.mono_us()
            left = (deadline_mono_us - now) / 1e6
            if left <= 0:
                break
            self.pf.sleep(min(DRAIN_PERIOD_S, left))
            self._drain_watchers(watchers, trial)

    # --- washout (§8.4) -----------------------------------------------------

    def _washout(self, trial: sch.Trial) -> dict[str, Any]:
        """MUZLATILGAN washout ketma-ketligi (§8.4).

        Holat mashinasi `schedule.WashoutMachine` da va u SOF: biz faqat
        KUZATUV beramiz. O'qilmagan kuzatuv `None` bo'ladi va FAIL-CLOSED
        ishlanadi -- "o'qilmadi" hech qachon "tinch" deb hisoblanmaydi.

        Tezliklar `total=` delta'sidan, oyna >=2 s: `cgroup.stall_fraction`
        qisqa oynada `None` qaytaradi va biz uni SHUNDAY qoldiramiz. 100 ms
        delta ONIY TEZLIK EMAS (§7, PSI 2 s kadensda partiyalarda kreditlanadi).
        """
        lab = str(self.lab_cgroup)
        baseline = self.pf.memory_current(lab)
        if baseline is None:
            # Baseline o'qilmasa §8.4 qadam 2 ni TEKSHIRIB BO'LMAYDI, va
            # "tekshirilmagan" ni "o'tdi" deb hisoblash jimgina kontaminatsiya
            # bo'lardi. Shuning uchun fail-closed: washout_timeout.
            return {"state": sch.WASHOUT_TIMEOUT, "timed_out": True,
                    "reason": "memory_baseline_unreadable", "observations": 0}
        machine = sch.WashoutMachine(baseline, self.washout_policy)
        kill_ok = self.pf.kill_subtree(lab)
        t0 = self.pf.mono_us()
        lab_psi = f"{lab}/memory.pressure"
        host_psi = "/proc/pressure/memory"
        hist: dict[str, list[tuple[int, int]]] = {"lab": [], "host": []}
        n = 0
        last = machine.progress
        while not machine.progress.terminal:
            self.pf.sleep(WASHOUT_POLL_S)
            now = self.pf.mono_us()
            rates = {}
            for key, path in (("lab", lab_psi), ("host", host_psi)):
                s = self.pf.psi_total(path)
                rate = None
                if s is not None:
                    hist[key].append(s)
                    old = None
                    for h in reversed(hist[key]):
                        if s[0] - h[0] >= WASHOUT_RATE_WINDOW_US:
                            old = h
                            break
                    if old is not None:
                        rate = cg.stall_fraction(old[1], s[1], old[0], s[0])
                rates[key] = rate
            last = machine.observe(sch.WashoutObservation(
                elapsed_s=(now - t0) / 1e6,
                kill_issued=bool(kill_ok),
                memory_current=self.pf.memory_current(lab),
                slice_stall_rate=rates["lab"],
                host_stall_rate=rates["host"],
            ))
            n += 1
        return {
            "state": last.state,
            "timed_out": machine.timed_out,
            "done": machine.done,
            "reason": last.reason,
            "elapsed_s": last.elapsed_s,
            "quiet_for_s": last.quiet_for_s,
            "memory_baseline": baseline,
            "kill_ok": kill_ok,
            "observations": n,
        }

    # --- faktlar (§12) ------------------------------------------------------

    def _collect_facts(
        self,
        trial: sch.Trial,
        timing: TrialTiming,
        watchers: dict[str, Any],
        host_before: dict[str, Any],
        host_after: dict[str, Any],
        ev_before: dict[str, dict[str, int]],
        ev_after: dict[str, dict[str, int]],
    ) -> tuple[dict[str, bool], dict[str, Any]]:
        """Trial faktlari -- HAMMASI LOG'LANGAN KUZATUVDAN (§12).

        Driver HECH QANDAY VR/FR qarorini qabul qilmaydi: u faqat §12 ning
        faktlarini to'playdi, disposition esa `schedule.explain_disposition`
        dan keladi. Bu ataylab: VR ta'rifi `reduce.py` da, o'lchovdan KEYIN
        va o'lchovdan TASHQARIDA (CONTRIBUTING.md §1.5).
        """
        lo, hi = timing.begin_mono_us, timing.horizon_end_mono_us
        state = self._sut_state
        detail: dict[str, Any] = {"anomalies": list(state["anomalies"])}

        # aborted_guard: guard'ning O'Z oqimidan, MONOTONIC vaqt bo'yicha.
        events = guard_events_in_window(self.guard_path, lo, hi)
        detail["guard_events"] = events
        guard_fired = bool(events)

        # contaminated (a): biz yubormagan SIGKILL.
        unsolicited = bool(state["unsolicited_kill"])

        # contaminated (b): BIZ CHEKLAMAGAN cgroup'da oom_kill. Global
        # o'sishdan lab subtree'sining O'Z o'sishini AYIRAMIZ -- cheklangan
        # cgroup'dagi OOM kutilgan natija, kontaminatsiya emas (§12).
        g0 = (host_before.get("vmstat") or {}).get("oom_kill")
        g1 = (host_after.get("vmstat") or {}).get("oom_kill")
        lab0 = (ev_before.get(SCOPE_LAB) or {}).get("oom_kill", 0)
        lab1 = (ev_after.get(SCOPE_LAB) or {}).get("oom_kill", 0)
        foreign = False
        if isinstance(g0, int) and isinstance(g1, int):
            outside = (g1 - g0) - (lab1 - lab0)
            detail["oom_kill_outside_lab"] = outside
            foreign = outside > 0
        else:
            detail["oom_kill_outside_lab"] = None

        # contaminated (c): bystander spillover detektori buzildi.
        by_oom = (ev_after.get(SCOPE_BYSTANDER) or {}).get("oom_kill", 0) - \
            (ev_before.get(SCOPE_BYSTANDER) or {}).get("oom_kill", 0)
        by_state = state.get("bystander_state_at_horizon")
        bystander_lost = bool(by_oom > 0 or state["bystander_broke"]
                              or by_state not in ("active", None))
        detail["bystander"] = {"oom_kill_delta": by_oom,
                              "active_state_at_horizon": by_state,
                              "transitions_seen": state["bystander_broke"]}

        # censored (a): instrumentatsiya yo'qolishi. Driver probe
        # QATORLARINI KO'RMAYDI (ular prober'ning CSV'sida), shuning uchun u
        # faqat KUZATADIGAN narsani aytadi: prober horizon oxirigacha tirik
        # qolmadi. `reduce.probe_gaps` haqiqiy uzilishlarni AVTORITET
        # ravishda topadi va `derive_disposition` ni `censored` ga olib keladi
        # (reduce.py:1440) -- ikki yo'l bir-birini qoplaydi.
        prober_state = state["prober_state_at_horizon"]
        probe_gap = prober_state not in ("active",)
        detail["prober_active_state_at_horizon"] = prober_state

        # censored (b): horizon xizmat DOWN holatda tugadi (§6.2). F_sd
        # detektori bo'yicha; `reduce` buni probe oqimidan mustaqil
        # ravishda ham aniqlaydi (`down_at_horizon`).
        sut_state = state["sut_state_at_horizon"]
        down = sut_state != "active"
        detail["sut_active_state_at_horizon"] = sut_state

        # Guest restart TRIAL ICHIDA bo'lgan bo'lsa: shu trial `harness_error`,
        # va keyingi chegara tekshiruvi butun run'ni to'xtatadi. Trial'ni
        # `complete` deb yozish uning monotonic vaqtlarini haqiqiy deb
        # ko'rsatardi -- restart'dan keyin ular haqiqiy EMAS.
        gen_now = self.pf.guest_generation()
        gen_changed, gen_why = guest_generation_changed(
            self.guest_generation, gen_now)
        detail["guest_generation"] = {"at_run_start": self.guest_generation,
                                      "at_trial_end": gen_now,
                                      "changed": gen_changed,
                                      "reason": gen_why}
        if gen_changed:
            detail["anomalies"].append(f"guest_generation:{gen_why}")

        facts_kw = {
            "harness_error": gen_changed,
            "guard_fired": guard_fired,
            "unsolicited_kill": unsolicited,
            "foreign_oom_kill": foreign,
            "bystander_lost_contract": bystander_lost,
            "probe_gap_exceeded": probe_gap,
            "horizon_ended_down": down,
        }
        return facts_kw, detail

    # --- kampaniya ----------------------------------------------------------

    @property
    def _sut_state(self) -> dict[str, Any]:
        if not hasattr(self, "__sut_state"):
            self.__reset_sut_state()
        return getattr(self, "__sut_state")

    def __reset_sut_state(self) -> None:
        setattr(self, "__sut_state", {
            "invocation": None,
            "restarts": 0,
            "active_claimed": set(),
            "anomalies": [],
            "unsolicited_kill": False,
            "bystander_broke": False,
            "sut_state_at_horizon": None,
            "prober_state_at_horizon": None,
            "bystander_state_at_horizon": None,
            "last_exit_ts": None,
        })

    def run(self) -> dict[str, Any]:
        """Butun kampaniya. Guard BIRINCHI start, OXIRGI stop (majburiyat 1)."""
        summary: dict[str, Any] = {
            "run_id": self.run_id, "run_dir": self.run_dir,
            "n_trials": len(self.selected), "trials": [],
            "dispositions": {}, "ok": False,
        }
        guard: dict[str, Any] | None = None
        psi: dict[str, Any] | None = None
        try:
            setup = self.setup_run()
            # TARTIB: guard BIRINCHI (majburiyat 1), qo'shimcha vaqt o'lchovi
            # KEYIN. NEGA shunday va nega teskarisi XATO: `measure_overhead()`
            # `revixlab.slice` da haqiqiy unit yaratadi, ya'ni u O'LCHOV
            # EMAS, IJRO. Uni guard'dan oldin bajarish lab slice'ida
            # kuzatuvsiz jarayon yaratardi va majburiyat 1 ni buzardi
            # (pressure yo'q bo'lsa ham: majburiyat "guard birinchi" deydi,
            # "guard pressure'dan oldin" demaydi).
            guard = self.start_guard()        # BIRINCHI
            psi = self.start_psi_sampler()
            # Qo'shimcha vaqt O'LCHANADI (majburiyat 9). Guard'ning
            # `RuntimeMaxSec` i bu o'lchovni KUTMAYDI: u `worst_case_total_s`
            # dan hisoblanadi (har trial uchun washout cap 120 s), ya'ni
            # o'lchangan qo'shimchadan bir necha baravar katta zaxira.
            self.measure_overhead()
            self.write_run_meta(self.run_meta_payload(setup, guard, psi))
            for i, trial in enumerate(self.selected):
                # Guest generation tekshiruvi HAR TRIAL CHEGARASIDA, trial
                # boshlanishidan OLDIN. O'zgargan bo'lsa run QATTIQ to'xtaydi:
                # restart'dan keyingi ma'lumotni undan oldingisiga qo'shib
                # bo'lmaydi (GuestRestartError docstring'i).
                gen = self.pf.guest_generation()
                changed, why = guest_generation_changed(
                    self.guest_generation, gen)
                if changed:
                    summary["guest_restart"] = {
                        "reason": why, "before": self.guest_generation,
                        "after": gen, "at_trial": trial.trial_id,
                        "trial_index": i,
                    }
                    raise GuestRestartError(
                        f"guest generation o'zgardi ({why}) trial "
                        f"{trial.trial_id} dan OLDIN: barcha monotonic "
                        "davomiylik taqqoslanmas bo'ldi, kampaniya to'xtadi. "
                        f"oldin={self.guest_generation} keyin={gen}"
                    )
                self.__reset_sut_state()
                summary["trials"].append(self.run_trial(trial, i))
            summary["ok"] = True
        except Exception as exc:  # noqa: BLE001
            self._harness_error("run", exc)
            summary["error"] = repr(exc)
            summary["error_type"] = type(exc).__name__
            raise
        finally:
            summary["dispositions"] = {
                k: v for k, v in self._disposition_counts.items() if v}
            if self._trial_overheads:
                summary["per_trial_overhead_s_measured"] = {
                    "n": len(self._trial_overheads),
                    "min": min(self._trial_overheads),
                    "max": max(self._trial_overheads),
                    "mean": sum(self._trial_overheads) / len(self._trial_overheads),
                }
            self._teardown_run()
        return summary

    def _teardown_run(self) -> None:
        """Teskari tartib: pressure -> lab -> prober -> psi -> GUARD OXIRGI.

        Guard OXIRGI to'xtatiladi (majburiyat 1): undan oldin to'xtatilsa,
        yig'ishtirish davomidagi qoldiq pressure kuzatuvsiz qolardi.
        """
        for unit in (PRESS_UNIT, SUT_UNIT, BYSTANDER_UNIT, PROBER_UNIT,
                     PSI_UNIT):
            try:
                self.pf.stop(unit)
            except Exception as exc:  # noqa: BLE001
                self._harness_error(f"teardown:{unit}", exc)
        try:
            self.pf.teardown()
        except Exception as exc:  # noqa: BLE001
            self._harness_error("teardown:slices", exc)
        if self._guard_started:
            try:
                self.pf.stop(GUARD_UNIT)        # OXIRGI
            except Exception as exc:  # noqa: BLE001
                self._harness_error("teardown:guard", exc)
        try:
            self.pf.clear_runtime_drop_ins()
        except Exception as exc:  # noqa: BLE001
            self._harness_error("teardown:drop_ins", exc)
        try:
            self.writer.close()
        except Exception:  # noqa: BLE001
            pass


def _jsonable(value: Any) -> Any:
    """Property dict'ini JSON'ga tushadigan shaklga keltiradi."""
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return {k: str(v) for k, v in dict(value).items()}


# ===========================================================================
# 4. CLI -- MUZLATILGAN INTERFEYS
# ===========================================================================


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="revix-driver",
        description="REVIX trial orkestratsiyasi (driver-contract/v1)")
    ap.add_argument("--run-dir", required=True,
                    help="run katalogi; MAVJUD bo'lsa XATO (datasets/ append-only)")
    ap.add_argument("--seed", type=int, required=True,
                    help="randomizatsiya seed'i (run_meta ga yoziladi)")
    ap.add_argument("--blocks", type=int, default=sch.P1_BLOCKS,
                    help=f"blok soni (default {sch.P1_BLOCKS}, §9.3)")
    ap.add_argument("--only", default=None, metavar="SPEC",
                    help="faktor darajalari, vergul bilan (masalan P0,A) -- smoke")
    ap.add_argument("--dry-run", action="store_true",
                    help="hech narsa ishga tushirmaydi, jadvalni chiqaradi")
    ap.add_argument("--json", action="store_true", help="JSON chiqish")
    # Muzlatilmagan parametrlar -- hammasi run_meta.open_parameters ga tushadi.
    ap.add_argument("--session-id", default="p1")
    ap.add_argument("--run-mode", default="pilot",
                    choices=("pilot", "smoke", "confirmatory"))
    ap.add_argument("--allow-pressure", action="store_true",
                    help="pressure generatorini yoqadi; 00-pilot-topologiya.md "
                         "§6 bo'yicha FAQAT guard tasdiqlangandan keyin")
    ap.add_argument("--memory-high", default=DEFAULT_MEMORY_HIGH)
    ap.add_argument("--watchdog-sec", default=DEFAULT_WATCHDOG_SEC)
    ap.add_argument("--timeout-start-sec", default=DEFAULT_TIMEOUT_START_SEC)
    ap.add_argument("--sut-binary", default=None)
    ap.add_argument("--max-hours", type=float, default=None,
                    help="baholangan kampaniya shundan uzun bo'lsa ishga tushmaydi")
    return ap


def main(argv: list[str] | None = None) -> int:
    """`guard`/`prober`/`pressure`/`reduce` bilan bir xil naqsh.

    `revix/cli.py` ning `revix run` i aynan shu `main(argv)` ni chaqiradi va
    ichki detallarga TEGMAYDI -- shuning uchun bu imzo MUZLATILGAN.
    """
    args = build_parser().parse_args(argv)
    only = parse_only(args.only)

    try:
        schedule = sch.p1_schedule(args.seed, n_blocks=args.blocks)
        # Timeline O'ZI invariantlarni majburlaydi (majburiyat 6): biz
        # oldindan tekshirmaymiz va jimgina tuzatmaymiz.
        timeline = sch.TrialTimeline()
        selected = select_trials(schedule, only)
    except (sch.ScheduleError, DriverError) as exc:
        return _fail(exc, args.json)

    if args.dry_run:
        # Majburiyat 10: HECH NARSA ishga tushmaydi -- `Platform` ham
        # yaratilmaydi, run katalogi ham tegilmaydi.
        report = dry_run_report(schedule, timeline, selected, only=only)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print(render_dry_run(report))
        return 0

    levels = {str(t.level("pressure_level")) for t in selected}
    if not args.allow_pressure and levels - {"P0"}:
        return _fail(
            PressureNotAllowedError(
                f"jadvalda P0 dan boshqa pressure darajalari bor: "
                f"{sorted(levels - {'P0'})}; --allow-pressure berilmagan. "
                "00-pilot-topologiya.md §6: guard tasdiqlanishi (qadam 3) "
                "pressure dosing kalibratsiyasidan (qadam 4) OLDIN."),
            args.json)

    try:
        run_dir = prepare_run_dir(args.run_dir)
    except RunDirExistsError as exc:
        return _fail(exc, args.json)

    cfg = DriverConfig(
        run_dir=run_dir, seed=args.seed, blocks=args.blocks, only=only,
        session_id=args.session_id, run_mode=args.run_mode,
        allow_pressure=args.allow_pressure, memory_high=args.memory_high,
        watchdog_sec=args.watchdog_sec,
        timeout_start_sec=args.timeout_start_sec,
        sut_binary=args.sut_binary, max_hours=args.max_hours,
    )
    try:
        platform = Platform()
    except U.UnitsError as exc:
        return _fail(exc, args.json)

    try:
        driver = Driver(cfg, platform, schedule, timeline)
    except Exception as exc:  # noqa: BLE001
        platform.close()
        return _fail(exc, args.json)

    try:
        summary = driver.run()
    except GuardStartError as exc:
        # FAIL-CLOSED (majburiyat 2): guard ishga tushmasa run BOSHLANMAYDI.
        return _fail(exc, args.json, code=2)
    except GuestRestartError as exc:
        # Guest restart'i: `boot_id` tutmaydigan monotonic uzilish. Alohida
        # chiqish kodi (3), chunki bu "xato" emas, MA'LUMOT CHEGARASI --
        # run'ni davom ettirish mumkin emas, lekin yig'ilgan qism yaroqli.
        return _fail(exc, args.json, code=3)
    except Exception as exc:  # noqa: BLE001
        return _fail(exc, args.json, code=1)
    finally:
        platform.close()

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(render_summary(summary))
    return 0 if summary.get("ok") else 1


def _fail(exc: BaseException, want_json: bool, code: int = 2) -> int:
    """Xatoni OSHKORA chiqaradi. Jimgina 0 qaytarilmaydi."""
    if want_json:
        print(json.dumps({"ok": False, "error": str(exc),
                          "error_type": type(exc).__name__},
                         indent=2, ensure_ascii=False))
    else:
        print(f"XATO ({type(exc).__name__}): {exc}", file=sys.stderr)
    return code


def render_dry_run(report: dict[str, Any]) -> str:
    est = report["campaign_estimate"]
    lines = [
        f"REVIX dry-run  ({report['driver_contract']})",
        f"  seed={report['rng_seed']}  rng={report['rng']}  "
        f"bloklar={report['n_blocks']}",
        f"  schedule_digest={report['schedule_digest']}",
        f"  trial: {report['n_trials_selected']} / {report['n_trials_total']}"
        + (f"   (--only {','.join(report['only'])})" if report["only"] else ""),
        f"  T_trial={report['t_trial_us'] / 1e6:.3f} s   "
        f"(fault'dan keyin {report['t_recovery_window_us'] / 1e6:.3f} s)",
        f"  formula: {report['t_trial_formula']}",
        f"  baho: {est['total_hours']:.2f} soat "
        f"(eng yomon {est['worst_case_hours']:.2f} soat); "
        f"qo'shimcha vaqt: {report['per_trial_overhead_source']}",
        "  HECH NARSA ISHGA TUSHIRILMADI (majburiyat 10).",
        "",
        "  blok  joy  arm        pressure",
    ]
    for t in report["trials"]:
        lines.append(
            f"  {t['block_index']:>4}  {t['position_in_block']:>3}  "
            f"{str(t.get('arm')):<10} {t.get('pressure_level')}")
    return "\n".join(lines)


def render_summary(summary: dict[str, Any]) -> str:
    lines = [
        f"REVIX run {summary['run_id']}",
        f"  katalog: {summary['run_dir']}",
        f"  trial: {len(summary['trials'])} / {summary['n_trials']}",
        "  disposition: " + (", ".join(
            f"{k}={v}" for k, v in sorted(summary["dispositions"].items()))
            or "(yo'q)"),
    ]
    oh = summary.get("per_trial_overhead_s_measured")
    if oh:
        lines.append(
            f"  o'lchangan qo'shimcha vaqt: n={oh['n']} "
            f"min={oh['min']:.2f}s mean={oh['mean']:.2f}s max={oh['max']:.2f}s")
    if summary.get("error"):
        lines.append(f"  XATO: {summary['error']}")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
