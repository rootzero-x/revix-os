# 14 — Real driver bilan birinchi smoke trial'lar: mashina ishlaydimi

Bu hujjat pilotdan **oldingi** oxirgi qadamni yozadi: `13` §6.3 va §8 dagi
uch muammoni tuzatish va **real** `revix.driver` bilan birinchi trial'larni
ishga tushirish. **Smoke trial'lar tadqiqot ma'lumoti EMAS:** ular faqat
mashinaning (driver, guard, generator, validator) ishlashini tekshiradi.
Bu yerda VR, FR, downtime yoki birorta birlamchi kattalik **hisoblanmaydi**
va hech bir natija gipotezalar haqida dalil sifatida o'qilmaydi.

Belgilar (`13` bilan bir xil):

- **FAKT** — o'lchandi, buyruq va chiqish keltirilgan;
- **GIPOTEZA** — o'lchanmagan taxmin;
- **NATIJA** — oldindan e'lon qilingan qoidaning FAKT'larga qo'llanishi;
- **TALQIN** — FAKT'dan xulosa (o'lchov emas);
- **CHEKLOV** — bu yerda o'lchab yoki kafolatlab bo'lmaydigan narsa.

**Branch:** `agent/pilot-ready`. **Commit'lar:** `cb8d16d` (1-qism),
`1978a0e` (teardown tuzatishi, §3.1). **Mashina:** WSL2, kernel
`6.6.87.2-microsoft-standard-WSL2`, `boot_id=4ea15279-acba-44ff-a533-6d7cd11924e5`,
pid1 starttime `653523`, Python `3.14.7`, `preregistration/v1.11`
(`bf6a02d9…66d1e`).

---

## 0. Qisqa xulosa

| # | savol | javob |
|---|---|---|
| 1 | Generator `WorkingDirectory` siz ishga tushadimi? | **Yo'q** (FAKT, §1). Tuzatildi; smoke'da 7/7 trial'da generator ishga tushdi |
| 2 | Host uyqusi validator'da ko'rinadimi? | Endi **ha**: yangi `host_clock_discontinuity` (ERROR, §2) |
| 3 | Driver har trial'da soatlarni yetarli yozadimi? | **Ha** (§2.4) |
| 4 | Birinchi real trial `validate` dan o'tdimi? | **Yo'q** — guard teardown'da SIGKILL olardi (§3.1). Tuzatildi; keyingi 6/6 run **O'TDI** |
| 5 | **`P2` da guard trip qiladimi?** | **Ha, 2/2 `P2` trial'da `sustained_pressure`**, `sustained_s` 15.10 / 15.00, trial boshidan 33.63 / 33.55 s da. `P1` da yo'q (2/2) |
| 6 | Sabab | Guard kuzatadigan 2 s stall tezligi `≥ 0.35` da **uzluksiz 15.4 / 14.9 s** turdi: generator ramp'i rejadagi hold'dan **1.4 s oldin** 0.35 dan oshadi va generator to'xtagach 2 s oyna yana **0.4–0.8 s** ushlab turadi (§5) |
| 7 | Frozen invariantga ta'siri | §9.4 invariant 2 ning `ramp_above_threshold_s = 0.000` **rejalashtirilgan 5 s ramp oynasida** o'lchanganda **2.0–2.1 s** chiqdi (§4.3, §6) — orkestrator qarori kerak |

> **Eng muhim gap:** loyihalangan pilot (generator `ramp_s + hold_s = 18 s`,
> kalibrlangan `P2` dial'i, guard `0.35 / 15 s`) **`P2` ma'lumotini bera
> olmasligi** mumkin: o'lchangan ikki `P2` trial'ining ikkalasi ham
> `aborted_guard` bo'ldi, va bu tasodif emas — tezlik 15 s davomida bir
> marta ham `0.35` dan pastga tushmadi (minimum 0.377 / 0.382). n = 2.

---

## 1. `driver._pressure_properties()` — `WorkingDirectory` yo'q edi

### 1.1 FAKT — kod o'qishi

`_pressure_argv()` `[self.cfg.python, "-m", "revix.pressure", ...]` quradi.
`-m` paketni `sys.path[0]` = joriy katalogdan qidiradi; repo `pip install`
qilinmaydi (`INSTALLATION.md` §3). Qo'shni unit'lar `WorkingDirectory`
beradi: `_mon_unit_properties()` (guard, psi_sampler, prober) va
`_sut_properties()` (SUT, bystander) — ikkalasi `self.cfg.repo_root`.
Generator unit'ida bu kalit **yo'q** edi.

### 1.2 FAKT — tuzatishdan OLDIN guest'da tasdiqlandi (qulf bilan)

`systemctl --user show-environment` da `PYTHON*` o'zgaruvchilari soni **0**;
`cd / && python3 -c "import revix"` → `ModuleNotFoundError`. Transient unit'lar
`revixlab.slice` da (`datasets/smoke-tools/wd-a.out`, `wd-b.out`):

```
$ systemd-run --user --slice=revixlab.slice --unit=revix-wdcheck-a --collect --wait --pipe \
    -p MemoryMax=256M -p MemorySwapMax=0 /usr/bin/python3 -m revix.pressure --help
/usr/bin/python3: Error while finding module specification for 'revix.pressure'
  (ModuleNotFoundError: No module named 'revix')
Finished with result: exit-code   Main processes terminated with: code=exited, status=1/FAILURE   (rc=1)
$ systemd-run ... --unit=revix-wdcheck-a2 ... python3 -c "import os,sys; print(os.getcwd()); ..."
/home/snowden      ['', '/usr/lib/python314.zip']
$ systemd-run ... --unit=revix-wdcheck-b ... -p WorkingDirectory=$HOME/pilotready-work \
    /usr/bin/python3 -m revix.pressure --help
usage: python3 -m revix.pressure [-h] [--mode {ramp,pi}] ...   (rc=0, status=0/SUCCESS)
```

Keyin `systemctl --user stop revixlab.slice`; `revix doctor --json`
`leftover_state` **PASS**.

**TALQIN.** Driver'ning `start_transient` job'i `done` bo'ladi (jarayon
ishga tushadi va ~50 ms da o'ladi), demak bu nuqson pilotda trial'ni
yiqitmasdan **jimgina "pressure yo'q"** yasardi.

### 1.3 Tuzatish va boshqa unit'lar

- `_pressure_properties()` ga `"WorkingDirectory": self.cfg.repo_root`
  (qo'shni unit'lar bilan aynan bir xil). Regressiya testlari:
  `test_pressure_unit_WorkingDirectory_repo_root` va
  `test_har_python_modul_unit_WorkingDirectory_bilan_ishga_tushadi` — to'liq
  fake trial'da `start_transient` ga yuborilgan **har** `-m revix.*` unit
  (guard, psi_sampler, prober, generator) `WorkingDirectory == repo_root`.
- **Guard, psi_sampler, prober — joyida** (`_mon_unit_properties`, FAKT
  kod o'qishi va yuqoridagi test). **SUT/bystander** — `ExecStart` mutlaq
  yo'l, `WorkingDirectory` ham bor.
- **FAKT (smoke):** 7 ta real trial'ning hammasida generator `pressure_start`
  yozdi (trial boshidan 15.076–15.098 s da).

---

## 2. Yangi validator tekshiruvi `host_clock_discontinuity`

### 2.1 Muammo (FAKT, `07` §7.7, `13` §0A.1)

Host uyqusida guest `CLOCK_MONOTONIC` uyquni sanamaydi, `CLOCK_REALTIME`
sanaydi: `A-P2-22` ning ikki ketma-ket yozuvi — `mono_us` 6 472 198 275 →
6 478 211 141 (**Δmono 6.012866 s**), `real_us` 1 791 060 253 618 540 →
1 791 102 348 421 289 (**Δreal 42 094.802749 s**), `boot_id` o'zgarmadi.
`validate.py` da `real_us` va `mono_us` ni solishtiruvchi tekshiruv yo'q edi.

### 2.2 FAKT — qonuniy tarqalish (chegarani tanlash uchun)

`datasets/smoke-tools/clockspread.py` `~/revix-runs` dagi **barcha**
yozish-lahzali soat oqimlarini o'qidi (JSONL envelope'lar `emitter` bo'yicha
fayl tartibida, `psi.csv` `mono_us/real_us`, `probe.csv`
`mono_us_send/real_us_send`): **72 402** ketma-ket juft
(`clockspread-revix-runs.txt`).

| to'plam | juftlar | max `|Δreal − Δmono|` |
|---|---|---|
| hammasi, `cal-01` siz | 42 359 | **0.000206 s** (`tstart-P1/psi.csv`) |
| `cal-01`, birinchi sakrashdan oldin | 29 806 | **0.000386 s** |
| `cal-01` uyqu oynasi | — | +1699.598, +94.312, +6371.122, +42 088.129, +0.661 s (`psi.csv`); +42 088.790 va +8165.032 s (`events.jsonl`) |
| global kvantillar | 72 402 | p50 0.000001, p99 0.000040, p99.9 0.000099 s |

804 s lik bo'shliqli guard juftlarida ham `|d| ≤ 5 µs`. Guest'da NTP daemon
**yo'q** (`systemd-timesyncd`, `chrony`, `ntp`, `ntpsec` — `inactive`;
`timedatectl NTP=no`), faqat `hv_utils.timesync_implicit=1`.

### 2.3 NATIJA — qoida

- Namunalar: **yozish lahzasida** o'qilgan `(mono, real)` juftlari, mono
  bo'yicha tartiblangan va birlashtirilgan (hamma jarayon bir xil kernel
  soatini o'qiydi): envelope'li JSONL record'lar, `trial_end` uchun
  `mono_us_record_written` + `real_us`, probe qatorlari
  `mono_us_send` + `real_us_send`. Driver o'tgan vaqt bilan yozadigan
  turlar (`trial_begin`, `env_snapshot`, `baseline_window`, `fault_inject`,
  `cgroup_events`, `unit_state`, `action`, `actor_signal`; `trial_end` ning
  envelope `mono_us` i horizon, washout'dan ~15 s oldin) soat namunasi
  **emas**: ularning `real − mono` i yozish kechikishi qadar sun'iy katta.
- Ketma-ket juftda **`|Δreal − Δmono| > 1.0 s` → ERROR**, bitta finding
  barcha sakrashlar va ular tushgan trial'lar bilan.
- **1.0 s:** qonuniy max'dan **2590×** yuqori, 11.7 soatlik hodisadan
  **42 088×** past, va `13` §0A.3 dagi controller'ning runtime chegarasi
  (`> 1 s ⇒ FAIL-CLOSED`) bilan bir xil.
- Bu **yaroqlilik qoidasi, ta'rif emas**: metrika, disposition, muzlatilgan
  ta'rif o'zgarmaydi (test: uyquli va uyqusiz sintetik run'ning
  `reduce_run(...).trials` i aynan teng).

**FAKT — tarixiy run'larga qo'llanishi:** `~/revix-runs` dagi 28 katalogdan
**faqat `open-params-cal-01`** belgilandi (2 sakrash, max 42 088.790 s);
qolgan 27 tasi toza. Smoke run'larning hammasida finding **yo'q**, va
trial'lar oldidan/keyin o'lchangan `real − mono` siljishi 0 yoki −1 µs
o'zgardi (§4.4).

Testlar (`tests/unit/test_validate.py`): cal-01 ning aynan o'sha raqamlaridan
(`jump_us == 42 088 789 883`); hold ichidagi uyqu → faqat shu finding va
trial ko'rsatiladi; chegara (386 µs, 0.999999 s, 1.000000 s o'tadi; 1.000001 s
va −5 s ushlanadi); orqaga sanalgan turlar soxta finding bermaydi; faqat probe
qatorlaridan ham ushlanadi. `tests/unit/test_driver.py`: fake soat hold
ichida realtime'ni +42 088.789883 s ga sakratadi — driver `complete` beradi,
validator run'ni rad etadi va trial'ni ko'rsatadi.

Yo'l-yo'lakay ikki fixture tuzatildi: `test_validate.Builder` `real_us = 0`
(doimiy — "realtime to'xtagan") o'rniga `REAL0 + mono_us`; `FakePlatform`
probe qatorlarining `real_us_send` ini flush vaqtidan emas, yuborish vaqtidan
oladi. Driver'da `_emit` endi `real_us` ni ham `Platform` dan oladi (mono
bilan bir xil sabab; ishlab chiqarishda bir xil funksiya).

### 2.4 Driver yozadigan soatlar yetarlimi (topshiriq 3)

**Ha.** FAKT (smoke run'lar): har envelope'da `mono_us` va `real_us`; har
trial'da yozish-lahzali juftlar — probe qatorlari (10 Hz, ikki target,
trial'ga 822), generator record'lari (~4 Hz), va `trial_end` ning
`mono_us_record_written` + `real_us` (washout'dan keyin). Inson uchun:
`trial_begin.real_us − trial_begin.mono_us` va `trial_end.real_us −
trial_end.mono_us_record_written` farqi trial ichidagi uyquni ko'rsatadi.

**CHEKLOV:** driver uyquni **runtime'da** sezmaydi (guest generation'dan
farqli o'laroq run'ni to'xtatmaydi) — u faqat validatsiyada ushlanadi.
Runtime tekshiruvi (`13` §0A.3 controller'idagidek, har trial chegarasida
`real − mono` siljishi > 1 s ⇒ run to'xtaydi) qo'shilmadi; bu orkestratorga
taklif.

---

## 3. Smoke protokoli

- **Qulf:** `~/.revix-exclusive` — `2026-10-04T09:01:30Z` (faqat §1.2
  tekshiruvi, keyin bo'shatildi), `09:15:03Z` (smoke-01; pytest uchun
  bo'shatildi), `09:19:50Z` → oxirgi tekshiruvdan keyin bo'shatildi
  (`09:27:54Z` da yo'q). Qulf ostida pytest **ishga tushirilmadi**.
- Har trial oldidan: `loadavg1` 0.08–0.42, `VBoxHeadless|mmdebstrap|mksquashfs`
  yo'q (Windows'da faqat bo'sh `VBoxSVC`), `leftover_state` PASS. Distro
  fon `wsl.exe -e /bin/sleep` bilan tirik ushlandi.
- Bajarish: ext4 `~/pilotready-work` — branch'ning `git clone` i (toza
  daraxt, `git_dirty: false`, commit `run_meta` da), `make -C revix` (SUT).
- Buyruq (`datasets/smoke-tools/smoke_trial.sh`):
  `python3 -m revix.driver --run-dir ~/revix-runs/<nom> --seed 20261004 --blocks 1 --only <arm>,<band> --allow-pressure --json`,
  keyin `python3 -m revix.validate --run-dir … --sut-unit revix-sut.service --sut-target sut`.
- **`revix run` emas, nega:** `cli.cmd_run` driver'ga faqat `--run-dir`,
  `--seed`, `--blocks`, `--only`, `--dry-run`, `--json` uzatadi
  (`revix/cli.py:2244`) — `--allow-pressure` ham, `--run-mode` ham yo'q
  (kod o'qishi). Ya'ni `revix run` bilan `P1/P2` `PressureNotAllowedError`
  beradi, `P0` esa generatorsiz ishlaydi. Dry-run `revix run` orqali
  bajarildi: `T_trial=41.100 s`, `qo'shimcha vaqt: not_measured_dry_run`,
  hech narsa ishga tushmadi.
- Har trial oldidan va keyin: `boot_id`, `/proc/1/stat` 22-maydon,
  `real_us − mono_us`, `oom_kill` (`pilotready/marker-*.json`).

### 3.1 FAKT — birinchi real trial `validate` dan O'TMADI: guard SIGKILL

`smoke-01-noaction-P0` (commit `cb8d16d`): driver `rc=0`, disposition
`censored`, lekin `validate` → **`ERROR guard_stop_missing`**. `guard.jsonl`
da faqat `guard_start`. Journal:

```
revix-guard.service: Main process exited, code=killed, status=9/KILL
revix-guard.service: Failed with result 'signal'.
Removed slice revixmon.slice
```

Sabab (kod): `_teardown_run` `self.pf.teardown()` ni **default'lari bilan
guard'dan OLDIN** chaqirardi; `units.teardown` default'da `cgroup.kill` ni
ikkala slice'ga — guard turgan `revixmon.slice` ga ham — qo'llaydi. Ya'ni
"guard OXIRGI" (majburiyat 1) amalda "guard lab bilan bir vaqtda SIGKILL"
edi va **har** run rad etilardi. Fake platforma `teardown` argumentlarini
e'tiborsiz qoldirgani uchun mavjud test buni ko'rmagan.

**Tuzatish (`1978a0e`):** (1) lab slice + guard'dan boshqa unit'lar (`kill`
faqat `revixlab.slice`), (2) guard SIGTERM bilan oxirgi, (3) qolgani
default'lar bilan (guard to'xtamasa shu yerda o'ldiriladi). Fake endi
`units.teardown` default'larini modellaydi; tuzatishsiz `test_driver.py`
→ 4 failed, tuzatish bilan → hammasi o'tadi. Shundan keyin trial qaytadan
(`smoke-02`) — bu ko'r-ko'rona takror emas, tuzatilgan nuqsondan keyingi
birinchi o'tish.

---

## 4. FAKT — trial'lar

Hammasi `--blocks 1 --seed 20261004`, har run'da **bitta** trial.

### 4.1 Disposition, guard, validate

| run | arm, band | disposition (qoida) | `trial_end` | `guard.jsonl` | validate |
|---|---|---|---|---|---|
| `smoke-01-noaction-P0` | no_action, P0 | `censored` (`horizon_ended_down`) | 1 | faqat `guard_start` | **O'TMADI** (`guard_stop_missing`) |
| `smoke-02-noaction-P0` | no_action, P0 | `censored` (`horizon_ended_down`) | 1 | start, stop (`tripped=false`, 567 iter) | **O'TDI** (0 xato, 1 ogohl.) |
| `smoke-03-A-P0` | A, P0 | `complete` (`measured`) | 1 | start, stop (`false`) | **O'TDI** |
| `smoke-04-noaction-P1` | no_action, P1 | `censored` (`horizon_ended_down`) | 1 | start, stop (`false`) | **O'TDI** |
| `smoke-05-noaction-P2` | no_action, P2 | **`aborted_guard`** (`guard_fired`) | 1 | start, **`guard_event sustained_pressure`** (`rate 0.5469`, `sustained_s 15.099967`, `kill_ok true`), stop (`tripped=true`) | **O'TDI** |
| `smoke-06-A-P1` | A, P1 | `complete` (`measured`) | 1 | start, stop (`false`) | **O'TDI** |
| `smoke-07-A-P2` | A, P2 | **`aborted_guard`** (`guard_fired`) | 1 | start, **`guard_event sustained_pressure`** (`rate 0.3792`, `sustained_s 15.000007`, `kill_ok true`), stop (`tripped=true`) | **O'TDI** |

Yagona ogohlantirish har run'da `run_filtered` (`--only`, 1/6 trial — kutilgan).
`no_action` da `censored` — `Restart=no` + fault ⇒ horizon'da SUT down
(§6.2 qoidasi bo'yicha mashina shuni berishi kerak). `smoke-05` matched
rules: `guard_fired, bystander_lost_contract, horizon_ended_down, measured`;
`smoke-07`: `guard_fired, unsolicited_kill, bystander_lost_contract, measured`
(guard'ning `kill_subtree` i bystander'ni va SUT'ni o'ldirdi).

### 4.2 Guard-relevant stall tezligi

Tezlik guard'ning o'z algoritmi bilan qayta qurildi (`psi.csv` `user` scope =
`user@1000.service/memory.pressure full`, eng tor `≥ 2 s` oyna,
`cgroup.stall_fraction`); vaqtlar `trial_begin` dan.

| run | eng uzun uzluksiz `≥ 0.35` | `≥ 0.35` oralig'i | `≥ 0.05` oraliqlari | max tezlik | `≥ 0.98` |
|---|---|---|---|---|---|
| smoke-02 / 03 (P0) | 0 | — | — | 0.0000 | 0 |
| smoke-04 (no_action P1) | **2.7 s** | 18.647–21.347 (+ 6 qisqa) | 17.847–22.047, … (5 bo'lak, eng uzuni 4.2 s) | 0.8939 | 0 |
| smoke-06 (A P1) | **2.3 s** | 18.54–20.84 (+ 2 qisqa) | 4 bo'lak, eng uzuni 5.0 s | 0.8783 | 0 |
| **smoke-05 (no_action P2)** | **15.4 s** | **18.544–33.945** (bitta) | 17.844–34.644 (16.8 s) | 0.9600 | 0 |
| **smoke-07 (A P2)** | **14.9 s** (guard o'zi 15.000 s) | **18.647–33.547** (bitta) | 17.947–34.347 (16.4 s) | 0.9307 | 0 |

`P2` da 15 s lik oraliq ichida tezlikning **minimumi 0.3773 / 0.3818** —
bir marta ham `0.35` dan pastga tushmagan. `user_full_rate2s_max = 0.98`
ga hech qachon yetmadi (max 0.96).

### 4.3 `ramp_above_threshold_s` — kuzatilgani

| o'qish | P0 | P1 (04 / 06) | P2 (05 / 07) |
|---|---|---|---|
| `10` §4 usuli: generatorning **o'z ramp oynasi** (`pressure_start`..oxirgi `pressure_ramp`), lab 2 s tezlik `> 0.05` | 0.0 | **0.0 / 0.0** | **0.0 / 0.0** |
| **Rejalashtirilgan 5 s ramp oynasi** `[15.0, 20.0] s`, lab `> 0.05` | 0.0 | **2.0 / 2.1 s** | **2.1 / 2.0 s** |
| xuddi shu, `user` scope | 0.0 | 2.1 / 2.1 s | 2.1 / 2.0 s |

Generatorning o'z ramp'i `pressure_start` dan 2.245–2.580 s da tugaydi
(`P0` 2.245–2.264, `P1/P2` 2.564–2.580), so'ng PI fazasi — lekin trial
timeline'idagi ramp **5 s**. Ya'ni ikki o'lchov ikki xil oynada: kalibratsiya
qiymati `0.000` generator ramp'iga tegishli, invariant 2 esa timeline ramp'iga.

### 4.4 Qo'shimcha vaqt, yaroqlilik, post-flight

| kattalik | qiymat (6 o'tgan run) |
|---|---|
| `trial_end.overhead_s` (`wall − TrialTimeline.total_s`, `total_s = 53.0`) | **3.247–3.268 s** |
| trial `wall_us` | 56.247–56.268 s |
| uning tarkibi | setup 0.060–0.072 s (trial_begin'dan **oldin**, `wall` ga kirmaydi), horizon 41.1 s, dump 0.055–0.060 s, washout **15.012–15.015 s** (`complete`, §8.4 ning 15 s poli), teardown 0.003–0.017 s |
| `run_meta.per_trial_overhead_s` (`measure_overhead`, preflight tsikli) | **0.0** (o'lchangan setup+teardown 0.083 s < rejalashtirilgan preflight 5 s) |
| butun 1-trial'lik driver run'i | 56.967–57.071 s |
| prober CPU (`prober_stop.cost`) | 0.355–0.439 % yadro |
| `boot_id`, pid1 (`653523`) | oldin = keyin, 7/7 |
| `real − mono` siljishining o'zgarishi | 0 µs (6 run), −1 µs (smoke-06) |
| `/proc/vmstat oom_kill` | 0 → 0, 7/7 |
| lab `memory.swap.current` (psi.csv, butun run max) | **0**, 7/7 |
| `revix doctor --json` `leftover_state` | **PASS** oldin va keyin, 7/7 |

**TALQIN (qo'shimcha vaqt):** `overhead_s ≈ 3.25 s` asosan ta'rif farqi:
`total_s = 53` washout'ni `pressure_off` (33 s) dan 20 s deb oladi, driver
esa horizon'ni 41.1 s gacha kuzatadi va keyin washout 15.0 s davom etadi
(41.1 + 15.0 = 56.1). Haqiqiy faza-tashqari narx (setup + dump + teardown)
≈ **0.13–0.15 s/trial**. **CHEKLOV:** `estimate_campaign` preflight
tsiklidan `0.0` oladi, ya'ni kampaniya bahosi (`per_trial_s = 53.0`)
o'lchangan trial wall'idan (~56.3 s) ~3.3 s/trial past; 120 trial'da bu
~6.6 daqiqa.

---

## 5. ASOSIY SAVOL — `P2` va guard: aniq timeline

### 5.1 FAKT — `trial_begin` dan sekundlar

| hodisa | smoke-05 (no_action P2) | smoke-07 (A P2) | reja |
|---|---|---|---|
| generator `pressure_start` | 15.076 | 15.078 | 15.0 (ramp boshi) |
| generator o'z ramp'i tugadi (oxirgi `pressure_ramp`) | 17.646 | 17.646 | — |
| user tezligi `≥ 0.05` | **17.844** | **17.947** | — |
| user tezligi `≥ 0.35` (guard sustain taymeri boshi) | **18.544** | **18.647** | **20.0 (hold boshi)** |
| fault inject | 23.001 | **23.353** (bracket 0.180 s) | 23.0 |
| SUT `active` (restart, A) | — | 24.026 (NRestarts 1) | — |
| rejalashtirilgan `pressure_off` | 33.0 | 33.0 | 33.0 |
| generator `pressure_stop` (`elapsed 18.050 / 18.042 s`, o'z `max_seconds`) | 33.127 | 33.120 | — |
| **guard trip** `sustained_pressure` | **33.634** | **33.553** | — |
| oxirgi `≥ 0.35` | 33.945 (+0.818 s gen'dan keyin) | 33.547 (+0.427 s) | — |
| horizon (`trial_end.mono_us`) | 41.1 | 41.1 | 41.1 |

Guard'ning kill'i ikkala trial'da **pressure o'chgandan keyin** (generator
yo'qolgach 0.43–0.51 s) — 2 s oynaning qoldig'ida. smoke-07 da guard
SUT'ni o'ldirdi va arm `A` (`Restart=on-failure`) uni **33.884 s** da
qayta ko'tardi (`NRestarts 2`, `unsolicited_kill = true`).

### 5.2 FAKT — kalibratsiya epizodlari bilan taqqoslash

Bir xil skript (`smoke_detail.py`) `open-params-cal-01/02` ning **A** qismi
(13 s generator, SUT bor, bystander/prober yo'q) epizodlariga qo'llandi
(`datasets/smoke-tools/detail-smoke-vs-calibration.json`):

| kattalik | cal P2 (n=24) min / p50 / max | smoke P2 (05 / 07) | cal P1 (n=24) | smoke P1 (04 / 06) |
|---|---|---|---|---|
| generator umri, s | 13.146 / 13.248 / 13.282 | 18.050 / 18.042 | 13.15–13.25 | 18.04 / 18.06 |
| gen start → user `≥ 0.35`, s | 3.545 / 3.661 / 4.600 | 3.468 / 3.569 | 3.60–3.98 | 3.549 / 3.460 |
| gen tugashi → oxirgi `≥ 0.35`, s | −1.487 / +0.375 / +1.083 | +0.818 / +0.427 | −7.87…+1.05 | −0.093 / −2.902 |
| **eng uzun uzluksiz `≥ 0.35`, s** | **3.2 / 4.3 / 9.0** | **15.4 / 14.9** | 1.4 / 1.65 / 2.9 | 2.7 / 2.3 |
| o'sha oraliqdagi min tezlik | 0.351 / 0.358 / 0.388 | 0.377 / 0.382 | — | 0.366 / 0.377 |
| generator ramp'dan keyingi eng katta record bo'shlig'i, s | 3.276 / 4.497 / 5.858 | **9.445 / 11.504** | 1.41–3.11 | 2.416 / 2.116 |
| generator PI namunalari | 10 / 14.5 / 19 | **3 / 6** | 26–31 | 42 / 43 |
| lab `memory.current` PI'da (median), MiB | 195.1 / 196.0 / 196.8 | 196.9 / 197.6 | 193.4–194.4 | 194.5 / 194.5 |

**TALQIN.** Ikki mexanizm qo'shiladi: (a) **arifmetika** — gen start'dan
`≥ 0.35` gacha ~3.5 s, gen tugagach ~0.4–0.8 s qoldiq, demak uzluksiz oraliq
`≈ umr − 3.1…2.7 s`; 18 s da bu **14.9–15.4 s**, 13 s da ~10 s. (b) **nazorat
yo'qolishi** — kalibratsiyaning 13 s epizodlarida `P2` tezligi PI tsiklida
0.35 dan pastga **tushib turgan** (eng uzun oraliq ≤ 9.0 s), smoke'da esa
**bir marta ham** tushmagan; generator record'lari orasida 9.4–11.5 s bo'shliq
(kalibratsiyada ≤ 5.9 s). Ya'ni 18 s ning o'zi yetarli sabab, (b) esa
oraliqni uzish imkoniyatini yo'qotadi. **GIPOTEZA (o'lchanmagan):** (b) pilot
topologiyasining farqidan (bystander lab'da, prober 10 Hz) — lab
`memory.current` farqi atigi ~1–1.5 MiB. n = 2 dan bu ajratilmaydi.

### 5.3 NATIJA

- **`P2`: 2/2 trial `aborted_guard`, trip 15.000–15.100 s sustain'da.**
  Kalibrlangan nishon 0.60 guard'ning 0.35 chegarasidan yuqori, va pilot
  timeline'ida bu tezlik 15 s dan uzoq uzluksiz turadi. §12 bo'yicha
  `aborted_guard` analizdan chiqariladi ⇒ loyihalangan pilot **`P2`
  yacheykalari uchun ma'lumot bermasligi** kutiladi (n = 2, ikkala arm).
- **`P1`: 2/2 trial guard'siz** (eng uzun oraliq 2.3–2.7 s).
- `user_full_rate2s_max = 0.98`: smoke'da yetilmadi (max 0.96, n = 2 `P2`,
  shu jumladan bitta bosim ostidagi restart). `13` §6.3 ning 2/7 i bilan
  ziddiyat yo'q — n kichik.

---

## 6. Variantlar (TALQIN — orkestrator qaroriga; hech biri qo'llanmadi)

**Frozen matn qaysi o'qishni qo'llaydi.** §9.4: *"pre-flight → R_ref 10 s →
ramp 5 s → hold, injeksiya hold'ga 3 s kirgach → pressure off"*; jadval
ostidagi izoh: *"`hold_cap_s` cheklovi faqat HOLD ga tegishli, ramp+hold ga
emas. Aks holda `hold ≤ 13 − 5 = 8 s` bo'lardi, lekin injeksiya(3 s) +
`W_stab`(8 s) = 11 s"*. `schedule.TrialTimeline` ham `pressure_on_s = 18.0`,
`sustained_pressure_on_s = 13.0` beradi (`run_meta.timeline`). Demak frozen
matn **generator umri = `ramp_s + hold_s` = 18 s** o'qishini qo'llaydi —
driver aynan shuni qiladi. Shu bilan birga Amendment v1.10→v1.11 (1.5)
guard qayta kalibratsiyasini kerak emas deb shunday asoslaydi:
*"`ramp_above_threshold_s = 0` bo'lgani uchun sustain taymeri faqat hold
ichida boshlanishi mumkin"*. **FAKT:** taymer hold boshidan **1.35–1.46 s
OLDIN** boshlandi (18.544 / 18.647 s), va rejalashtirilgan ramp oynasidagi
o'lchangan qiymat 2.0–2.1 s (§4.3). Ya'ni (1.5) ning faktik asosi pilot
timeline'ida bajarilmaydi, va invariant 2 timeline ramp'i bo'yicha o'lchansa
`13 + 2.1 = 15.1 > 15`.

| # | variant | kutiladigan `≥ 0.35` oraliq (§5.2 arifmetikasi) | narxi |
|---|---|---|---|
| V0 | **Hech narsa o'zgarmaydi** | 14.9–15.4 s (o'lchangan) | `P2` ⇒ `aborted_guard` (2/2); `P2` yacheykalari bo'sh, 3×2 dizayn amalda `P0/P1` ga qisqaradi; frozen §9.4 invariant 2 o'lchov bilan buzilgan holda qoladi |
| V1 | **Topshiriqdagi nomzod:** generator umri `= hold_s` (13 s), ramp boshidan | ~10 s (cal: max 9.0 s) | Generator ~28.1 s da to'xtaydi, `pressure_off` esa 33 s: injeksiya 23 s + `W_stab` 8 s oynasining ~3 s i **bosimsiz** — §17.4-5 (`window_past_pressure` / `window_outside_hold_complete`), ya'ni `P1/P2` trial'larining ko'pi `censored` bo'ladi; `pressure_off` ni ham 28 s ga surish aynan §9.4 rad etgan `hold ≤ 8 s` o'qishi (`3 + 8 = 11 > 8`). **Frozen matnga zid**; amendment kerak va u ham ziddiyatni hal qilmaydi |
| V2 | Generatorni ramp fazasi **ichida kechroq** boshlash: `start = hold_start − R` (`R ≈ 2.6 s` = o'z ramp'i), `max_seconds = hold_s + R`, `pressure_off` 33 s da qoladi | ~12.9 s (20.9 → 33.8), zaxira ~2.1 s | Timeline raqamlari (5/13/33/41.1) o'zgarmaydi va (1.5) ning premisasi (taymer faqat hold'da) **qayta bajariladi**; lekin driver'ning generator boshlanish nuqtasi o'zgaradi — `ramp 5 s` ning ma'nosi ("bosim ko'tariladigan 5 s") talqin qilinadi, demak **amendment yoki kamida aniq e'lon** kerak; `R` o'lchangan (2.245–2.580 s), lekin zaxira 2 s guard tik'i va 0.4–0.8 s qoldiqqa nisbatan tor; `P2` nazorati (§5.2 (b)) hal bo'lmaydi |
| V3 | `P2` dozasini pasaytirish (nishon yoki `base_mb`) | noma'lum | §9.3 `P2` bandi 60–80% — 0.35 dan yuqori; dial §2.6 da muzlatilgan; ishchi oyna tor (`10` §3.6). Qayta kalibratsiya, va 15 s chegarasi baribir nazoratning tebranishiga bog'liq qoladi |
| V4 | Guard chegaralari (`0.35 / 15 s`) | — | **Taqiqlangan**: xavfsizlik mexanizmi; ko'rib chiqilmaydi |

Mening fikrim (TALQIN, qaror emas): V2 frozen raqamlarni saqlagan holda
v1.11 (1.5) ning faktik premisasini tiklaydigan yagona variant, lekin u ham
§9.4 ning `ramp 5 s` iborasini talqin qiladi va o'lchangan zaxira ~2 s, n = 2.
Har qanday variantdan keyin `P2` smoke'i qayta bajarilishi kerak.

---

## 7. Boshqa topilmalar (FAKT, kim egasi ko'rsatilgan)

1. **`revix run` pilotni ishga tushira olmaydi** (`revix/cli.py`, mening
   faylim emas): `--allow-pressure` va `--run-mode` uzatilmaydi (§3).
2. **`--run-mode smoke` validator'dan o'tmaydi:** driver `choices=("pilot",
   "smoke", "confirmatory")`, `validate.RUN_MODES = ("pilot", "confirmatory")`
   va `04` §1.1 shartnomasi ham `pilot | confirmatory`. Smoke'lar shuning
   uchun default `pilot` bilan yozildi; `datasets/smoke-*` nomi ularni
   ajratadi. Driver'dagi `smoke` tanlovi shartnomadan og'ish — o'zgartirmadim.
3. **Bosim ostida injeksiya kechikdi:** smoke-07 (A, P2) da `fault_inject`
   23.353 s da (reja 23.0), `FAULT` buyrug'i bracket'i **0.180 s** (boshqa
   trial'larda 107–160 µs). §17 budjetining `t_up − t_inject` hisobiga
   ta'siri bu hujjatda baholanmadi.
4. **Guard kill'i arm `A` restart'ini to'xtatmaydi:** smoke-07 da guard SUT'ni
   33.556 s da o'ldirdi, systemd uni 33.884 s da qayta ko'tardi (bosim o'chgan
   edi). Disposition `aborted_guard` — to'g'ri.
5. **`P2` generator nazorati:** §5.2 (b) — 9.4–11.5 s record bo'shliqlari.
6. Kampaniya bahosi o'lchangan trial wall'idan past (§4.4 CHEKLOV).

---

## 8. CHEKLOV

- **n kichik:** har yacheykadan bitta trial; `P2` xulosasi **2 trial** dan
  (har arm'dan bittadan). "Har `P2` trial'i trip qiladi" deb da'vo qilinmaydi
  — 2/2 va mexanizm (§5.2) shuni kutishga asos beradi.
- Smoke trial'lar `--blocks 1 --only`: to'liq blok randomizatsiyasi emas;
  trial'lar orasida washout'dan keyin yangi run (guard qayta ishga tushadi).
- Guard tezligi `psi.csv` dan **qayta qurildi** (10 Hz, guard'ning o'z
  namunalari emas); guard'ning o'z `sustained_s` i (15.10 / 15.00) bilan mos.
- `ramp_above_threshold_s` ikki o'qishda berildi; qaysi biri §9.4 niki —
  §6 da TALQIN, qaror orkestratorniki.
- Bitta mashina, bitta kernel, VM'siz host, bitta seed.
- `host_clock_discontinuity`: 1 s dan qisqa muzlash ushlanmaydi; guest
  restart'ida u ham yonadi (birlamchi finding `guest_restarted`); realtime'ni
  host > 1 s qadam bilan tuzatsa run rad etiladi (o'lchangan ma'lumotda yo'q).

## 9. Fayllar va qayta ishlab chiqarish

- Kod: `revix/driver.py` (`_pressure_properties`, `_emit`, `_teardown_run`),
  `revix/validate.py` (`check_host_clock_discontinuity`, `_clock_samples`,
  `HOST_CLOCK_DISCONTINUITY_US`, `CLOCK_BACKDATED_RECORD_TYPES`); testlar
  `tests/unit/test_driver.py`, `tests/unit/test_validate.py`.
- Ma'lumot: `datasets/smoke-01-noaction-P0` … `smoke-07-A-P2` — run
  fayllari (`*.zst`, `guard.jsonl` ochiq), `pilotready/` da marker'lar,
  driver chiqishi, validate hisoboti, `analysis.json`.
- Asboblar: `datasets/smoke-tools/` — `smoke_trial.sh` (trial + pre/post),
  `smoke_analyze.py`, `smoke_detail.py`, `clockspread.py`, `summ.py`;
  natijalar `detail-smoke-vs-calibration.json`, `clockspread-revix-runs.txt`,
  `wd-a.out`/`wd-b.out`.
- Qayta tekshirish: `zstd -d` bilan ochib,
  `python3 -m revix.validate --run-dir <dir> --sut-unit revix-sut.service --sut-target sut`;
  `python3 datasets/smoke-tools/smoke_analyze.py <dir>`.

---

## 10. V2 — OLDINDAN qayd etilgan mezon (yangi trial'lardan OLDIN commit qilindi)

> Bu bo'lim V2 kodi yozilishidan va birorta yangi trial ishga
> tushirilishidan **OLDIN** yozildi va o'z commit'ida qayd etildi. Keyingi
> commit'larda **o'zgartirilmaydi**; natija §11 da alohida yoziladi.

**Qaror (orkestrator, 2026-10-04):** §6 ning **V2** varianti. Generator
`hold_start − R` da boshlanadi va `hold_s + R` ishlaydi, ya'ni
`pressure_off` da (33.0 s) chiqadi. `R` — generatorning **o'z o'lchangan
ramp'i**, **2.57 s** (§5.1: `pressure_start` → oxirgi `pressure_ramp`
17.646 − 15.076 = 2.570 s va 17.646 − 15.078 = 2.568 s). `R` nomli
konstanta, sozlanmaydi. Barcha band'lar (P0/P1/P2) va arm'lar uchun bir xil.
`schedule.py` va frozen matn o'zgarmaydi; faqat `revix/driver.py`.

**Muvaffaqiyat mezoni (orkestrator bergan, aynan):** yangi smoke
trial'larning **`P2`** dagilarida (a) **birorta ham trial `aborted_guard`
bilan tugamaydi** va (b) guard tezligi `≥ 0.35` bo'lgan **eng uzun uzluksiz
oraliq ≤ 14 s**.

- (b) ning o'lchovi — §4.2 dagi bilan aynan bir xil:
  `datasets/smoke-tools/smoke_analyze.py` ning
  `longest_user_span_ge_0.35_s` maydoni (`psi.csv` `user` scope,
  guard algoritmi: eng tor `≥ 2 s` oyna, uzunlik = oxirgi − birinchi
  namuna, oyna `[trial_begin, horizon + 30 s]`).
- **To'xtash qoidasi:** birorta `P2` trial'i trip qilsa YOKI biror oraliq
  14 s dan oshsa — **qolgan barcha trial'lar to'xtatiladi** va hisobot
  yoziladi. `R`, dial yoki boshqa hech narsa o'zgartirilib qayta
  urinilmaydi.
- Mashina talablari (avvalgidek, mezonga qo'shimcha): har trial'da
  `trial_end` = 1, `validate` O'TDI, `boot_id`/pid1/`real − mono` siljishi
  o'zgarmagan (aks holda trial tashlanadi va yoziladi), post-flight
  (`oom_kill` o'zgarmagan, lab swap 0, `leftover_state` PASS).

**Trial'lar va tartib (oldindan qotirilgan):** har biri alohida run,
`--blocks 1`, `--allow-pressure`, default `--run-mode pilot`, har trial
uchun boshqa seed:

| # | run | arm, band | seed |
|---|---|---|---|
| 1 | `smoke-08-A-P2` | A, P2 | 20261011 |
| 2 | `smoke-09-noaction-P2` | no_action, P2 | 20261012 |
| 3 | `smoke-10-A-P2` | A, P2 | 20261013 |
| 4 | `smoke-11-noaction-P2` | no_action, P2 | 20261014 |
| 5 | `smoke-12-A-P2` | A, P2 | 20261015 |
| 6 | `smoke-13-noaction-P2` | no_action, P2 | 20261016 |
| 7 | `smoke-14-noaction-P1` | no_action, P1 | 20261017 |
| 8 | `smoke-15-A-P1` | A, P1 | 20261018 |
| 9 | `smoke-16-A-P0` | A, P0 | 20261019 |
| 10 | `smoke-17-noaction-P0` | no_action, P0 | 20261020 |

`P1`/`P0` — regressiya tekshiruvi (mezonga kirmaydi, lekin ular ham trip
qilsa yoki validate'dan o'tmasa — to'xtatiladi va yoziladi). VR, FR,
downtime yoki birlamchi kattalik **hisoblanmaydi**.

---

## 11. V2 natijasi — mezon BAJARILMADI, ketma-ketlik to'xtatildi

> §10 o'zgartirilmadi. Kod: `11fca44` (V2 + `revix run` bayroqlari).
> Qulf `2026-10-04T09:50:49Z` — `09:57:15Z`. Trial'lar `revix run ...
> --allow-pressure` orqali (yangi uzatish ishladi). Har trial oldidan/keyin
> `boot_id`, pid1 `653523`, `real − mono` siljishi (o'zgarish −1…+1 µs) va
> `oom_kill` (0 → 0) o'zgarmadi; lab swap max 0; `leftover_state` PASS.

### 11.1 FAKT — `P2` trial'lari (tartib §10 dagidek)

| # | run | disposition (driver) | guard | eng uzun `≥ 0.35` | `≥ 0.35` ning ≥ 1 s oraliqlari | eng uzun `≥ 0.05` | max tezlik | validate |
|---|---|---|---|---|---|---|---|---|
| 1 | smoke-08-A-P2 | `complete` | trip yo'q | **6.1 s** | 21.04–25.54, 27.24–33.34 | 14.7 s | 0.9364 | O'TDI |
| 2 | smoke-09-noaction-P2 | `censored` (`horizon_ended_down`) | trip yo'q | **7.4 s** | 21.04–25.54, 27.04–34.44 | 8.5 s | 0.9622 | O'TDI |
| 3 | smoke-10-A-P2 | `complete` | trip yo'q | **5.0 s** | 21.05–26.05, 27.25–29.55, 30.35–32.25 | 14.6 s | 0.9004 | O'TDI |
| 4 | smoke-11-noaction-P2 | `censored` (`horizon_ended_down`) | trip yo'q | **13.0 s** | 20.95–33.95 | 14.3 s | 0.9697 | O'TDI |
| 5 | smoke-12-A-P2 | `complete` | trip yo'q | **5.1 s** | 20.97–26.07, 27.17–28.77, 29.87–34.17 | 14.7 s | 0.8790 | O'TDI |
| 6 | **smoke-13-noaction-P2** | **`harness_error`** (reducer: `aborted_guard`) | **`user_full_rate2s_runaway`**, `rate 0.9817`, `limit 0.98`, `window_us 2099975`, `kill_ok true`, trial boshidan **22.526 s** | 2.1 s (kill bilan kesildi) | 20.95–23.05 | 2.7 s | 0.9814 | O'TDI (2 ogohl.) |

`trial_end` har run'da **1** ta. `smoke-11` ning tahlili birinchi urinishda
**tahlil skriptining** xatosi bilan yiqildi (`smoke_analyze.py`: PI
namunalarining bir qismida `slice_full_rate2s = None`, filtrlangan ro'yxat
filtrlanmagan uzunlik bilan indekslangan) — ketma-ketlik oldindan yozilgan
qoida bo'yicha to'xtadi; trial ma'lumotiga tegilmadi, skript tuzatildi
(`_median`), 08–11 qayta tahlil qilindi va qolgan trial'lar o'sha tartib
va seed'lar bilan davom ettirildi. Bu tuzatish o'lchov yoki dial'ni
o'zgartirmaydi.

### 11.2 FAKT — V2 oynasi ishladi

| kattalik | 6 trial (min–max) | reja |
|---|---|---|
| generator `pressure_start` | 17.494–17.547 s | 17.43 s |
| generator o'z ramp'i tugadi | 20.056–20.115 s | 20.0 s (hold boshi) |
| user `≥ 0.35` birinchi marta | 20.946–21.051 s | hold ichida |
| `ramp_above_threshold_s`, rejalashtirilgan ramp oynasi `[15, 20] s` (lab va user) | **0.0** (6/6) | 0.0 |
| generator chiqishi (`pressure_stop`, 5 tugagan trial) | 33.075–33.245 s (`elapsed` 15.568–15.697 s, `overrun` 0.000–0.127 s) | 33.0 s |
| `trial_end.overhead_s` (5 tugagan trial) | 3.242–3.278 s | — |

Ya'ni v1.11 (1.5) ning premisasi — *"sustain taymeri faqat hold ichida
boshlanishi mumkin"* — bu 6 trial'da **bajarildi**, va
`validate.check_planned_timeline` o'tdi (reja o'zgarmagan:
`13 + 0.0 ≤ 15`; u o'lchovni emas, rejani tekshiradi — §4.3 CHEKLOVI o'z
kuchida).

### 11.3 NATIJA — §10 mezoni

- **(b) eng uzun `≥ 0.35` oraliq ≤ 14 s: 6/6 da bajarildi** (5.0–13.0 s;
  `smoke-13` kill bilan 2.1 s da kesilgan). `sustained_pressure` trip'i
  **0/6** (V2 dan oldin 2/2).
- **(a) "birorta `P2` trial'i `aborted_guard` bilan tugamaydi" va to'xtash
  qoidasi "birorta `P2` trial'i trip qilsa": BAJARILMADI.** `smoke-13` da
  guard **runaway** chegarasi (`user_full_rate2s_max = 0.98`) bo'yicha trip
  qildi. Driver bu trial'ga `harness_error` yozdi (§11.4), reducer
  hosilasi `aborted_guard` — har ikkala o'qishda ham bu trial `P2`
  ma'lumotini bermaydi va guard ishga tushdi.
- **To'xtash qoidasi qo'llandi:** 6-trial'dan keyin ketma-ketlik
  to'xtatildi; `P1` (14, 15) va `P0` (16, 17) regressiya trial'lari
  **bajarilmadi**. `R`, dial va boshqa hech narsa o'zgartirilmadi va qayta
  urinilmadi.

### 11.4 FAKT — `smoke-13` timeline va driver nuqsoni

`trial_begin` dan: generator 17.525 s, o'z ramp'i 20.105 s da tugadi, user
`≥ 0.05` 20.351 s, `≥ 0.35` 20.951 s, **guard trip 22.526 s**
(`user_full_rate2s_runaway`, 0.9817 / 0.98, oyna 2.1 s), SUT `failed /
signal` 22.528 s (guard'ning `kill_subtree` i), driver injeksiyasi 23.001 s
da — SUT allaqachon o'lik: `FAULT exit code=1` → `ConnectionRefusedError
(111)` → `DriverError("SUT fault ack bermadi ...")`. Driver run'ni
`trial_end` (horizon 23.004 s), washout'**siz** yopdi (`washout.state =
null`), driver run wall 23.8 s.

**Driver nuqsoni (mening faylim, TUZATILMADI — to'xtash qoidasi):**
`run_trial` ning istisno yo'li `_collect_facts` ni chaqirmaydi, demak
`guard_fired` hech qachon tekshirilmaydi va §12 ning ustuvorligi
(`aborted_guard` > `harness_error`) o'rniga `harness_error` yoziladi;
validator buni faqat **ogohlantirish** (`disposition_cross_check`) sifatida
ko'rsatadi. Shu yo'lda washout ham o'tkazib yuboriladi — ko'p trial'lik
run'da keyingi trial washout'siz boshlanardi (bu yerda run bitta trial'lik
edi, post-flight toza). Taklif: istisno yo'lida ham guard oqimini
(`guard_events_in_window`) o'qib `guard_fired` ni faktga qo'shish va
washout'ni `finally` ga o'tkazish — orkestrator ruxsati bilan.

### 11.5 TALQIN (o'lchov emas)

- V2 **o'zi maqsad qilgan mexanizmni** (sustain, 15 s) yo'q qildi: 0/6
  trip, eng uzun oraliq 5.0–13.0 s. Lekin `smoke-11` ning 13.0 s i
  mezondan atigi 1.0 s past — PI nazorati tebranmagan trial'larda oraliq
  `≈ 33.9 − 20.95 ≈ 13 s` ga yaqinlashadi, ya'ni zaxira tor.
- Trip qilgan mexanizm **boshqa**: runaway (0.98), PI fazasining birinchi
  ~2.4 s ida (hold boshidan 2.5 s keyin), `no_action` arm'ida, restart'siz.
  `P2` dagi max tezlik: V2 dan oldin 0.96 / 0.93, V2 da 0.879–0.981 —
  ya'ni kalibrlangan `P2` dial'i pilot topologiyasida runaway chegarasiga
  **yaqin** ishlaydi (`13` §6.3 ham B-`P2` da 2/7 trip ko'rgan). V2 buni
  keltirib chiqardimi yoki yo'qmi — **o'lchanmagan** (n kichik, V2 dan
  oldin faqat 2 trial).
- Kutiladigan stavka bahosi (taxmin, CHEKLOV: n = 6): `P2` trial'larining
  1/6 i runaway bilan yo'qoladi.

### 11.6 CHEKLOV

- `P2`: 6 trial (3 + 3), `P1`/`P0` regressiyasi bajarilmagan.
- Guard tezligi `psi.csv` dan qayta qurilgan (10 Hz); runaway guard'ning
  o'z namunasida 0.9817, `psi.csv` da max 0.9814.
- `smoke-13` ning disposition'i driver nuqsoni tufayli `harness_error`.

### 11.7 Mezon bo'yicha yakuniy bayonot (orkestrator so'rovi bilan qo'shildi)

- **§10 mezoni o'zining so'zma-so'z matni bo'yicha** (*"birorta `P2`
  trial'i `aborted_guard` bilan tugamaydi"*, to'xtash qoidasi *"birorta
  `P2` trial'i trip qilsa"*) **BAJARILMADI**: `smoke-13` da guard ishga
  tushdi.
- **Mezonning maqsadi** — V2 nishonga olgan **sustain** mexanizmi
  (`0.35 / 15 s`) — **bajarildi**: `sustained_pressure` trip'i 0/6 (V2 dan
  oldin 2/2), eng uzun oraliq 13.0 s.
- Yagona muvaffaqiyatsizlik **boshqa mexanizm**: runaway chegarasi
  (`user_full_rate2s_max = 0.98`, rate 0.9817). Xuddi shu qoida
  kalibratsiyada ham ikki marta ishlagan (`13` §6.3: 0.9802 va 0.9889).
- §10 matni o'zgartirilmadi va qayta ta'riflanmaydi. Orkestrator qarori:
  V2 saqlanadi, dial va guard'ga tegilmaydi, `P2` dagi kutiladigan yo'qotish
  keyingi amendment'da exclusion rate sifatida oldindan e'lon qilinadi.

## 12. Driver istisno yo'li tuzatildi (orkestrator ruxsati bilan)

**Tuzatish (`revix/driver.py`):**

1. Injeksiyadan oldin guard oqimi o'qiladi (`trial_begin` .. hozir); guard
   allaqachon ishlagan bo'lsa injeksiya **qilinmaydi**,
   `trial_end.detail.fault = {"skipped": true, "reason":
   "guard_fired_before_injection", "guard_events": [...]}`, trial oddiy
   yo'ldan davom etadi va `_collect_facts` -> `guard_fired` -> §12 bo'yicha
   `aborted_guard`.
2. Trial ichidagi istisnoda guard oqimi o'qiladi: guard ishlagan bo'lsa
   (poyga — guard tekshiruvdan keyin, `FAULT` dan oldin) trial **xuddi shu
   `_collect_facts` yo'lidan** tasniflanadi (`aborted_guard`), istisno
   `trial_end.detail.exception_after_guard_trip` da yoziladi va
   `harness_error` record'i yozilmaydi (u validator'da disposition'ni
   `harness_error` ga majburlardi). Guard ishlamagan bo'lsa — `harness_error`
   (avvalgidek).
3. Washout **`finally` da, har yo'lda**. Istisno yo'lida avval prober
   to'xtatiladi va trial oynasi shu lahzada yopiladi (washout oynadan
   tashqarida — oddiy yo'l bilan bir xil ma'no). Washout'ning o'zi
   yiqilsa — `washout_timeout` (`washout.reason = "washout_exception: ..."`).
   Har trial'da aynan bitta `trial_end` saqlanadi.

**Testlar (fake):** guard injeksiyadan oldin, guard injeksiya paytida
(istisno), guard injeksiyadan keyin, guard'siz haqiqiy harness xatosi,
istisnodan keyin ikkinchi trial toza boshlanishi, washout'ning o'zi
yiqilishi — har birida washout bajarilgani (`trial_end.washout`, lab
`cgroup.kill`) tekshiriladi. Tuzatishsiz 5 tasi yiqiladi.

### 12.1 Empirik tekshiruv — OLDINDAN yozilgan reja va kutilgan natija

- Run `smoke-18-noaction-P0-x2`: `revix run --blocks 2 --only no_action,P0
  --allow-pressure --seed 20261021` (ikki trial).
- Birinchi trial'ning `trial_begin` idan **~22.0 s** keyin SUT unit'i
  **harness TASHQARISIDAN** o'ldiriladi:
  `systemctl --user kill --signal=SIGKILL revix-sut.service`. Bu smoke-13
  ning yo'lini (injeksiya o'lik SUT'ga, `ConnectionRefused`) **simulyatsiya
  qiladi; bu guard trip EMAS** — guard oqimida `guard_event` bo'lmasligi
  kerak.
- **Kutilgan:** 1-trial `harness_error` (guard ishlamagan, istisno —
  haqiqiy harness yo'li), `trial_end` 1 ta, `washout.state = complete`,
  prober to'xtatilgan; 2-trial toza boshlanadi (setup xatosiz) va
  injeksiya bilan oxiriga yetadi (`no_action` P0 da odatdagi natija
  `censored` / `horizon_ended_down`); run `validate` dan o'tadi;
  post-flight toza.

### 12.2 FAKT — `smoke-18-noaction-P0-x2` (commit `9c98e7f`): kutilganidan FARQ

Qulf ~`10:09Z` (pre-marker real_us 1791108520641943) — `10:12:28Z` (olishda `loadavg1` 0.30). Tashqi kill
1-trial boshidan **22.004 s** da (`systemctl --user kill --signal=SIGKILL
revix-sut.service`, rc 0; journal: `status=9/KILL`). `guard.jsonl`:
faqat `guard_start`, `guard_stop` — **guard trip yo'q** (kutilgandek).

| | kutilgan (§12.1) | o'lchangan |
|---|---|---|
| 1-trial disposition | `harness_error` | **`harness_error`** (matched: `harness_error, washout_timed_out, measured`) |
| injeksiya | `ConnectionRefused` | `fault_inject` 23.001 s, `error ConnectionRefusedError(111)` |
| `trial_end` soni | 1 + 1 | **1 + 1** |
| prober to'xtatildi | ha | ha, 23.054 s (trial oynasi 23.001 s da yopildi) |
| **1-trial washout** | `complete` | **`washout_timeout`**, `reason t_w_max`, 120.118 s, `memory_baseline 177651712` (169.4 MiB) |
| 2-trial | toza boshlanadi va tugaydi | setup xatosiz, injeksiya 23.001 s, `censored` (`horizon_ended_down`), washout `complete` 15.014 s |
| validate | O'TDI | **O'TDI** (0 xato, faqat `run_filtered`) |
| post-flight | toza | `boot_id`/pid1 o'zgarmagan, `real − mono` −1 µs, `oom_kill` 0, lab swap 0, `leftover_state` PASS |

**Sabab (FAKT):** istisno `pressure_off` dan (33 s) OLDIN — generator
(P0, 160 MiB) hali tirik edi. `_washout` `memory.current` baseline'ini o'z
boshida o'qiydi: 169.4 MiB; `cgroup.kill` dan keyin lab 0.1 MiB, ya'ni §8.4
ning "baseline ±32 MiB" sharti hech qachon bajarilmadi va washout 120 s
cap'da `washout_timeout` bilan tugadi. Talab bajarildi ("washout
yakunlangan YOKI oshkora yiqilgan"), lekin bu artefakt: har bunday trial
120 s yo'qotardi. Oddiy yo'lda generator `pressure_off` da to'xtatiladi,
shuning uchun bu u yerda ko'rinmaydi.

**Tuzatish:** istisno yo'lida, generator hali to'xtatilmagan bo'lsa, u
washout'dan OLDIN to'xtatiladi (`detail.pressure.stopped_early_mono_us`).
Regressiya testi (fake, ikki holat) tuzatishsiz yiqiladi.

### 12.3 Empirik qayta tekshiruv — OLDINDAN yozilgan

`smoke-19-noaction-P0-x2`, xuddi shu protokol (seed 20261022). **Kutilgan:**
1-trial `harness_error`, washout **`complete`**, generator kill'dan oldin
to'xtatilgan; 2-trial toza va tugaydi; validate O'TDI; post-flight toza.
Agar 1-trial washout yana `washout_timeout` bo'lsa — to'xtatiladi va
yoziladi.

### 12.4 FAKT — `smoke-19-noaction-P0-x2` (commit `1a40263`): kutilgandek

Qulf `10:15:55Z` — `10:17:40Z` (`loadavg1` 0.34). Tashqi kill 1-trial
boshidan **22.001 s** da (rc 0, journal `status=9/KILL`); `guard.jsonl`:
faqat `guard_start`, `guard_stop` — guard trip yo'q. **Bu guard trip emas,
smoke-13 yo'lining tashqi simulyatsiyasi.**

| | kutilgan (§12.3) | o'lchangan |
|---|---|---|
| 1-trial disposition | `harness_error` | **`harness_error`** (matched: `harness_error, measured`) |
| injeksiya | `ConnectionRefused` | 23.001 s, `ConnectionRefusedError(111)`, `sut_ack null` |
| generator washout'dan oldin to'xtatildi | ha | **ha**, 23.341 s (`stopped_early_mono_us`) |
| 1-trial washout | `complete` | **`complete`**, 15.013 s, baseline 0.67 MiB (700416 B) |
| prober | to'xtatilgan | 23.056 s; trial oynasi 23.001 s da yopildi |
| `trial_end` soni | 1 + 1 | **1 + 1** |
| 2-trial | toza boshlanadi va tugaydi | setup 0.045 s xatosiz, injeksiya 23.001 s (`OK armed=exit`), `censored` (`horizon_ended_down`), washout `complete` 15.014 s |
| validate | O'TDI | **O'TDI** (0 xato, faqat `run_filtered`; 225 record, 1282 probe) |
| post-flight | toza | `boot_id`/pid1 `653523` o'zgarmagan, `real − mono` −1 µs, `oom_kill` 0, lab swap 0, `leftover_state` PASS, `revix*` unit 0 |

**NATIJA:** istisno yo'li endi (a) guard'siz holatda `harness_error`
beradi, (b) washout'ni yakunlaydi, (c) prober va generatorni to'xtatadi,
(d) keyingi trial'ni toza boshlaydi. Guard sababli istisno yo'li
(`aborted_guard`) faqat fake testlarda tekshirildi — real guard trip'ini
qasddan yaratish uchun dial yoki guard'ga tegish kerak bo'lardi, bu esa
taqiqlangan. **CHEKLOV:** 1-trial `overhead_s = 0.0` (wall 38.4 s <
`total_s` 53) — ta'rif bo'yicha (`max(0, wall − total_s)`), o'lchov emas.

---

## 13. v1.12 preshartlari: `open_parameters` va regressiya smoke'i

### 13.1 `run_meta.open_parameters` (v1.12 1-band, §16.10(1); commit `65b902f`)

`watchdog_sec`, `memory_high`, `timeout_start_sec` va `t_trial_s` endi har
biri: `value` (amaldagi, CLI flag'idan), `frozen_value`, `matches_frozen`,
`frozen_in = "preregistration/v1.12"`, `frozen_section`, `source`,
`calibration_required: false`, `rule_satisfied`, `calibration` (run_id'lar
va hujjatdan ko'chirilgan raqamlar — nomli konstantalar, runtime'da
hisoblanmaydi) va §16.10(5) `mechanism_statement` bilan yoziladi.

| parametr | qiymat | `rule_satisfied` | kalibratsiya `run_id` lari | manba |
|---|---|---|---|---|
| `watchdog_sec` | 5s | **true** | `open-params-cal-01`, `-02` (A qism faqat shularda; `cal-03` — faqat B) | `13` §0.5, §2.2, §6.1 |
| `memory_high` | 192M | **true** | `dose-01-dial`, `dose-02-bands`, `dose-03-p2sweep`; qayta: `cal-01/02/03` | `10` §2.2, §2.6; `13` §4; `limitation` — OQ-11 |
| `timeout_start_sec` | 10s | **false** — `frozen_as: pre_data_default_documented_deviation`, `deviation` → v1.12 1.3-band | `open-params-cal-02`, `-03` (24/24/20 < 48, `rule_proposal: null`) | `13` §3.1, §6.2 |
| `t_trial_s` | 41.1 | true (formula) | — | v1.12 1.4 |

**FAKT:** `open_parameters` ni faqat `revix/driver.py` va
`tests/unit/test_driver.py` o'qiydi (`grep`); `validate.py` va `analyze.py`
unga tegmaydi — validate natijasi o'zgarmadi (quyidagi 6 run). `SCHEMA_VERSION`
siljimaydi: `04` shartnomasi uni faqat yangi record turi yoki enum qiymati
uchun siljitadi.

### 13.2 FAKT — pilot jadvali MUZLATILDI (dry-run, hech narsa ishga tushmadi)

`python3 -m revix.cli run --run-dir … --seed 20261006 --dry-run [--json]`
(`65b902f`; seed **20261006** — pilot seed'i, hech bir smoke'da
ishlatilmagan):

| | |
|---|---|
| `schedule_digest` | **`69ae399edbb20b5a0271d4b6657a3b5c1ec45b61b19a04a2bf9e0b6e8decb2dc`** |
| `rng` | `python-random-mt19937`, seed 20261006 |
| bloklar / trial | 20 / **120** (`cells_per_block` 6) |
| yacheykalar | `A/P0` 20, `A/P1` 20, `A/P2` 20, `no_action/P0` 20, `no_action/P1` 20, `no_action/P2` 20 |
| 0-blok tartibi | `no_action/P1`, `no_action/P2`, `A/P0`, `A/P2`, `no_action/P0`, `A/P1` |
| `T_trial` | 41.100 s; generator 17.43–33.00 s (15.57 s; reja 18.0 s, R 2.57 s) |
| baho | 1.77 soat (eng yomon 5.10 soat), qo'shimcha vaqt `not_measured_dry_run` |

To'liq chiqish: `datasets/smoke-tools/pilot-dryrun-20261006.json`
(sha256 `0e3a3c63…15a3`) va `.txt`.

### 13.3 FAKT — regressiya smoke'i (v1.12 9.4-band)

Kod `65b902f` (= `main` `ebf0e7e` + 13.1), ext4 clone, `git_dirty: false`.
Kirish nuqtasi: **`python3 -m revix.cli run --run-dir … --seed … --blocks 1
--only <arm>,<band> --allow-pressure`** (CLI uzatishi ishladi). Qulf
`10:27:29Z` — `10:33:40Z`. Har run `run_meta`: `preregistration/v1.12`,
sha256 `ccb6186e…4ad2` (= tag `v0.1.12-preregistration`),
`generator_window.lead_s 2.57`, `open_parameters` hammasi
`matches_frozen: true`.

| run | arm, band | seed | disposition | guard | eng uzun `≥ 0.35` | eng uzun `≥ 0.05` | validate |
|---|---|---|---|---|---|---|---|
| smoke-20 | A, P0 | 20261031 | `complete` | trip yo'q | 0.0 s | 0.0 s | O'TDI |
| smoke-21 | no_action, P0 | 20261032 | `censored` (`horizon_ended_down`) | trip yo'q | 0.0 s | 0.0 s | O'TDI |
| smoke-22 | A, P1 | 20261033 | `complete` | trip yo'q | 2.6 s | 6.5 s | O'TDI |
| smoke-23 | no_action, P1 | 20261034 | `censored` (`horizon_ended_down`) | trip yo'q | 9.0 s | 10.3 s | O'TDI |
| smoke-24 | A, P2 | 20261035 | **`aborted_guard`** (`guard_fired`; matched + `unsolicited_kill`, `bystander_lost_contract`) | **`user_full_rate2s_runaway`**, rate 0.98004 / 0.98, oyna 2.000 s, trial boshidan **29.23 s** — injeksiyadan (23.056 s) **keyin**, restart'dan (24.345 s) 4.9 s keyin | 9.6 s | 10.8 s | O'TDI |
| smoke-25 | no_action, P2 | 20261036 | `censored` (`horizon_ended_down`) | trip yo'q | 4.6 s | 5.9 s | O'TDI |

- `trial_end` har run'da **1**; validate har run'da 0 xato, yagona
  ogohlantirish `run_filtered`.
- **`sustained_pressure` trip'i 0/6.** smoke-24 dagi runaway trip — v1.12
  3-bandning e'lon qilingan kutilmasi; trial §12 bo'yicha `aborted_guard`,
  istisno yo'li ishga tushmadi (injeksiya oldin bo'lgan), washout
  `complete` 15.011 s; guard kill'idan keyin arm `A` SUT'ni 29.366 s da
  qayta ko'tardi.
- Rejadagi ramp oynasida `ramp_above_threshold_s` (user) **0.0** (6/6);
  generator 17.493–17.516 s da boshlandi, o'z ramp'i 19.723–20.080 s da
  tugadi, `pressure_stop` 33.076–33.182 s (smoke-24 da guard o'ldirgani
  uchun yo'q).
- `trial_end.overhead_s` 3.243–3.327 s; washout 6/6 `complete`
  (15.011–15.015 s).
- **Post-flight 6/6:** `boot_id` va pid1 `653523` o'zgarmagan, `real −
  mono` siljishi −1…+1 µs, `oom_kill` 0 → 0, lab swap max 0,
  `leftover_state` PASS; oxirida `revix*` unit 0.

**CHEKLOV:** har yacheykadan bitta trial; `P1` uchun bu V2 ning real driver
bilan birinchi o'lchovi (n = 2: oraliqlar 2.6 / 9.0 s).
