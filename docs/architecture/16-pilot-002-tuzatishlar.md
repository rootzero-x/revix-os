# 16 — `p1-pilot-002` uchun driver tuzatishlari: holat va TO'XTASH sababi

Belgilar: **FAKT** / **GIPOTEZA** / **NATIJA** / **TALQIN** / **CHEKLOV**
(`15` dagidek). Asos: `15` §2.4, §3.2; `preregistration/v1.13` 3-band.

## 0. Qisqa holat

| tuzatish (v1.13 3.1) | holat |
|---|---|
| 3. `t_issue` vaqt manbai | **bajarildi**, test bilan (`agent/pilot-ready`) |
| 1. §17.4 oyna fakti (reducer funksiyalari bilan) | **prototip yozildi, TO'XTATILDI** — repo'ning §1.5 regressiya qulfi bilan to'qnashadi (§2) |
| 2. §4 probe fakti (reducer sharti bilan) | prototipda; xuddi shu qulf (§2) |
| oflayn replay (v1.13 3.2(2)) | **bajarildi** prototip mantig'i bilan — faqat nomlangan uch trial o'zgaradi (§3) |
| smoke partiyasi, `04` revizya yozuvi, VM handshake | **boshlanmadi** — kod yakuniy emas |

## 1. FAKT — `t_issue` tuzatishi

`driver.exit_ts_candidate(payload)`: odatda `active_exit_ts_mono_us`
(avvalgidek); **faqat** `exec_main_start > active_exit` va
`exec_main_exit ≥ exec_main_start` bo'lsa (eng so'nggi asosiy jarayon
eskirgan `ActiveExit` dan keyin boshlanib chiqqan) —
`exec_main_exit_ts_mono_us`. `_note_unit_state` exit vaqtini `max` bilan
saqlaydi (yangi invocation'ning birinchi record'i eski `ActiveExit` ni
olib yuradi va aniqroq qiymatni bosib o'tmasligi kerak).

**systemd xatti-harakati, dalil (`b010t001`, `trial_begin` dan):** guard
o'ldirgan, hech qachon `active` bo'lmagan invocation `ca2a0c11` ning
record'ida `ActiveExitTimestampMonotonic` 23.023 s (oldingi invocation'niki),
`InactiveExitTimestampMonotonic` 23.024 s, `ExecMainStartTimestampMonotonic`
23.144 s, `ExecMainExitTimestampMonotonic` 27.134 s, `ExecMainCode 2`,
`ExecMainStatus 9`. `ActiveExitTimestamp` faqat `active` dan chiqishda
yangilanadi.

**Testlar** (`tests/unit/test_driver.py`; fixture
`tests/unit/data_p1_pilot_001_b010t001.json` — `b010t001` ning SUT
`unit_state`, `action`, `trial_begin` record'lari, maydonlar to'plami,
`p1-pilot-001` ning nusxasidan): haqiqiy `_note_unit_state` record'lar ustida
yuritiladi → action `t_issue` lari **19629521595, 19633632690** (avval
ikkalasi 19629521595); `exit_ts_candidate` ning to'rt holati. Tuzatishsiz
**2 test yiqiladi** (153 passed), tuzatish bilan 155 passed.

## 2. TO'XTASH SABABI — §1.5 regressiya qulfi

**FAKT.** `tests/unit/test_driver.py::test_driver_VR_va_FR_tariflarini_CHAQIRMAYDI`
(commit `6827b57`, *"PSI failure, VR yoki FR ta'rifiga KIRMAYDI
(CONTRIBUTING.md §1.5)"*) AST bo'yicha tekshiradi: driver
`evaluate_vr`, `fr_a`, `evaluate_fr_b`, `window_throughput`,
`reduce_trial`, **`build_episodes`** ni chaqirmaydi va **`reduce` ni
umuman import qilmaydi** — izoh: *"ta'riflar o'lchovdan KEYIN va
o'lchovdan TASHQARIDA qolishi kerak"*.

**FAKT.** v1.13 3.1(1) esa driver oyna faktini *"reducer'ning o'z
funksiyalari bilan (`build_episodes` → `classify_window_containment`)"*
hisoblashini va *"ikkinchi, mustaqil `t_up` ta'rifi yozilmasligini"*
talab qiladi; 3.1(2) probe faktini *"reducer/validator ishlatadigan
shartning o'zi bilan"*. Prototip (`agent/pilot-ready-facts-proto`,
`fca71ac`) aynan shuni qiladi va qulf testini **yiqitadi**
(`AssertionError: build_episodes`).

**TALQIN.** Bu ikki talab bir vaqtda bajarilmaydi: `t_up` ni hisoblash
uchun `build_episodes` kerak (u ichida `evaluate_vr` / `window_throughput`
ni chaqiradi), qulf esa driver'da buni taqiqlaydi. Mazmunan:
- **PSI sirkulyarligi yo'q:** prototip PSI'ni o'qimaydi; hisoblash probe,
  `unit_state`, `fault_inject`, `baseline_window`, `action` record'lariga
  tayanadi (reducer bilan bir xil).
- **Qayta aloqa yo'q:** faktlar trial oynasi yopilgandan keyin (prober
  to'xtagan, horizon o'tgan) hisoblanadi va faqat `trial_end.facts` ga
  tushadi; washout, keyingi trial va jadval ularga bog'liq emas (`run()`
  disposition bo'yicha tarmoqlanmaydi). Prober arm qaror yo'liga ulanmaydi
  (§5 kafolat 2).
- **Lekin** qulfning matni — *"reduce import qilinmaydi"*,
  *"`build_episodes` chaqirilmaydi"* — so'zma-so'z buziladi. Uni
  o'zgartirish §1.5 qo'riqchisini o'zgartirish; bu topshiriq *"ishlab
  o'tish o'rniga hisobot qiling"* deydi, shuning uchun to'xtadim.

**Variantlar (qaror orkestratorniki):**

| # | nima | narx |
|---|---|---|
| Q1 | Qulfni **toraytirish**: `reduce` importi va `build_episodes` / `probe_gaps` / `classify_window_containment` faqat bitta post-oyna funksiyasida (`measured_trial_facts`) ruxsat; AST testi boshqa joyda chaqirilishini taqiqlashni davom ettiradi, `evaluate_vr`/`fr_a`/`evaluate_fr_b`/`reduce_trial` to'g'ridan-to'g'ri chaqiruvi taqiqligicha qoladi; PSI fakti taqiqi saqlanadi | v1.13 3.1 so'zma-so'z bajariladi; §1.5 qo'riqchisi o'zgaradi (yozma asos bilan); prototip tayyor |
| Q2 | Driver faktlarni `python3 -m revix.reduce`-uslubidagi alohida jarayonda hisoblatadi | qulfni **chetlab o'tish** — tavsiya qilmayman |
| Q3 | Probe faktini driver'da `reduce` siz (ketma-ket `mono_us_send` farqi `> 2P`) va testda `reduce.probe_gaps` ga tenglik bilan; oyna fakti uchun baribir Q1 yoki boshqa yo'l kerak | v1.13 3.1(2) "o'sha shart" ni test bilan, konstruksiya bilan emas, ta'minlaydi; oyna muammosini hal qilmaydi |
| Q4 | Analiz uchun avtoritet disposition'ni reducer'ga o'tkazish (`04` §8.1), p1-pilot-002 dan **oldin** e'lon qilib | v1.13 3-bandiga zid (u driver tuzatishini tanlagan); amendment kerak |

## 3. NATIJA — oflayn replay (`p1-pilot-001`, faqat o'qish)

Skript `datasets/smoke-tools/p1_replay.py`; kod — prototip branch'ining
`revix/` daraxti (`git archive agent/pilot-ready-facts-proto`), chiqish
`~/pilotready-scratch/proto/replay.json`; run katalogi `dr-xr-xr-x` qoldi.
Har trial: yozilgan `trial_end.facts` + prototipning ikki fakti
(`probe_gap_exceeded` OR, `window_outside_hold`) → `explain_disposition`.

| | natija |
|---|---|
| `b007t001` | `complete` → **`censored`** (`probe_gap_exceeded`; `window_outside_hold` ham mos) |
| `b013t004` | `complete` → **`censored`** (`window_outside_hold`) |
| `b010t001` | `aborted_guard` → `aborted_guard`; action 2 `t_issue` 19629521595 → **19633632690** (ikki action turli) |
| disposition o'zgarishi, yacheyka bo'yicha | **A/P2: `complete → censored` 2**; qolgan 5 yacheyka: **0**; jami 120 trial |
| validator'ning ikki sharti replay'dan keyin | buzilish **0** (probe uzilishli trial'lar `censored`, `complete` + oyna tashqarida yo'q) |
| action `t_issue` o'zgarishi | faqat `b010t001` ning 2-action'i; eski mantiq barcha yozilgan `t_issue` larni **aynan** qayta chiqaradi (0 nomuvofiqlik) |

`b010t001` ning yangi vaqtlari bilan `check_actions` oynalari: action 1
`(23.023, 27.134]` — `ca2a0c11` (23.145 s) ichida; action 2
`(27.134, horizon]` — `c50262b1` (27.396 s) ichida.

**NATIJA:** v1.13 3.2(2) ning oldindan yozilgan kutilmasi prototip mantig'i
bilan **bajariladi** — boshqa hech bir trial o'zgarmaydi.

## 4. FAKT — testlar

To'liq `tests/`: o'zgarishdan oldin (`7b41ca7`) **1122 passed, 1 skipped**;
`t_issue` tuzatishi bilan **1124 passed, 1 skipped** (`bccd118` ga fast-forward'dan keyin
ham 1124 passed, 1 skipped).

## 5. CHEKLOV va keyingi qadam

- Smoke partiyasi, `04` revizya yozuvi va VM handshake **boshlanmadi**:
  ular yakuniy kodni talab qiladi.
- Replay prototip mantig'i bilan bajarildi; yakuniy kod Q1 bo'yicha
  qabul qilinsa, xuddi shu replay yakuniy kod bilan qayta bajariladi.
- Smoke hech qachon ko'rsatmagan klasslar (`15` §5.2 CHEKLOV) o'z kuchida.

---

## 6. Q1 — qaror va yakuniy implementatsiya (`f576c79`)

**Qaror (orkestrator, loyiha egasining delegatsiyasi bo'yicha):** Q1 — §1.5
qulfi **toraytiriladi** va toraytirishning o'zi **qulflanadi**.

**FAKT — kod:**
- `driver.measured_trial_facts` — yagona post-oyna funksiyasi; `reduce`
  **faqat shu funksiya ichida** import qilinadi. Kirish: shu trial'ning
  setup'dan oldingi ofsetlardan keyin yozilgan `events.jsonl`,
  `guard.jsonl`, `probe.csv` qatorlari (validator'ning `reducer_view`
  filtri bilan). Chiqish: `probe_gap_exceeded` (`reduce.probe_gaps`) va
  `window_outside_hold` (`reduce.classify_window_containment` holati
  `window_past_pressure` / `window_past_horizon`).
- Chaqiruv `run_trial` da, `PROBER_UNIT` to'xtatilgandan va
  `horizon_end_mono_us` belgilangandan keyin, washout'dan oldin; natija
  `_collect_facts(measured=)` → `TrialFacts` → `explain_disposition` →
  `trial_end`.
- `schedule.TrialFacts.window_outside_hold` (default `False`);
  `DISPOSITION_RULES` da `("window_outside_hold", …, "censored")` —
  `probe_gap_exceeded` dan keyin, `horizon_ended_down` dan oldin.
  **Ishlatadigan tarmoq:** `explain_disposition` ning shu qoidasi; u faqat
  harness / guard / kontaminatsiya / washout / probe-gap qoidalari mos
  kelmaganda yutadi va natija `censored`.
- `run_meta.disposition_facts`: `method: post_window_reducer_facts`,
  `driver_function: revix.driver.measured_trial_facts`, `reducer_module`,
  `reducer_functions`, `since: preregistration/v1.13 … 3.1-band`,
  `t_issue_source`. `p1-pilot-001` da bu maydon **yo'q** — ikki run shu
  bilan ajraladi. `SCHEMA_VERSION` o'zgarmadi (faqat payload maydoni).

**FAKT — qulflar (`tests/unit/test_driver.py`):**
- `test_driver_VR_va_FR_tariflarini_CHAQIRMAYDI` — toraytirildi:
  `build_episodes`, `probe_gaps`, `split_trials`, `fault_effective_us`,
  `reference_throughput`, `classify_window_containment` faqat
  `measured_trial_facts` ichida; `evaluate_vr`, `fr_a`, `evaluate_fr_b`,
  `reduce_trial`, `window_throughput` **hech qayerda** to'g'ridan-to'g'ri
  chaqirilmaydi; `reduce` modul darajasida import qilinmaydi; PSI fakti
  yo'q. Docstring nima, nega, kim qaror qilgani va v1.13 3.1 ni yozadi.
- **Yangi** `test_measured_facts_faqat_trial_end_ga_oqadi` (AST): yagona
  chaqiruv joyi `run_trial`; u `PROBER_UNIT` stop va horizon
  belgilanishidan **keyingi** qatorda; `measured` `run_trial` da faqat
  `_collect_facts(measured=)` da o'qiladi; `_collect_facts` ichida faqat
  ikki fakt kalitidan o'qiladi; washout, pressure, lab/SUT/prober start,
  injeksiya, guard, overhead, setup, teardown, `_note_unit_state`,
  `_emit_action` va boshqa 20 ta boshqaruv funksiyasi bu nomlarning
  (`measured`, `measured_trial_facts`, `window_outside_hold`,
  `probe_gap_exceeded`, `facts_kw`, `verdict`, `_disposition_counts`, …)
  **hech birini** o'qimaydi; `_washout` faqat `trial` ni oladi; `run()`
  `run_trial` natijasini faqat `summary["trials"].append` ga beradi.
- Haqiqiy record'lardan testlar: `b007t001` (probe uzilishi + oyna) va
  `b013t004` (oyna) → `censored`; validator'ning o'z ikki tekshiruvi xuddi
  shu fixture'da bir xil javob beradi.

**TAN OLINADI (oshkora):** `build_episodes` → `evaluate_vr` /
`window_throughput` zanjiri endi driver'ning **post-oyna** qadamida
ishlaydi — ya'ni VR oynasi mantig'i driver jarayoni ichida bajariladi. Shu
sababli driver va reducer'ning disposition'i (bu ikki fakt bo'yicha)
**konstruksiya bo'yicha** mos.

### 6.1 Skeptik reviewer nimaga e'tiroz bildiradi — va dalil

| e'tiroz | dalil / javob |
|---|---|
| "Asbob natija ta'rifini o'z ichiga oldi — o'lchov natijaga moslasha oladi" | Faktlar trial oynasi yopilgandan keyin hisoblanadi va faqat `trial_end` ga oqadi; washout, generator, guard, SUT/prober start, injeksiya vaqti va keyingi trial ularni o'qimaydi (AST testi). Jadval seed'dan oldindan qotgan (`schedule_digest`). |
| "PSI endi disposition'ga kirdi (§1.5 sirkulyarligi)" | `measured_trial_facts` PSI'ni o'qimaydi (kirish: `events.jsonl` / `guard.jsonl` / `probe.csv`); `psi.csv` ochilmaydi; `TrialFacts` da PSI fakti yo'qligi testda qoldi. |
| "Safeguard ma'lumot ko'rilgandan keyin bo'shatildi" | Ha — oshkora: p1-pilot-001 dan keyin, v1.13 0-band e'loni bilan. Toraytirish **bitta funksiya** bilan chegaralangan va AST bilan qulflangan; ruxsat etilgan chaqiruvlar muzlatilgan matn (§4, §17.4(2),(5)) talab qilgan faktlarni hisoblaydi, yangi qoida yo'q. |
| "Driver o'z `t_up` ta'rifini yozdi" | Yo'q: `t_up` reducer'ning `build_episodes` idan; driver'da mustaqil ta'rif yo'q; replay validator bilan mos (§7). |
| "Bu disposition'larni qulay tomonga o'zgartiradi" | Yo'nalish muzlatilgan matnda: §17.4(2) va §4 — `censored`. p1-pilot-001 replay: faqat ikki `complete → censored` (A/P2), qolgan 118 o'zgarishsiz. |
| "`t_issue` tuzatishi o'lchangan vaqtlarni o'zgartiradi" | Faqat `ActiveExit` eskirgan holatda; replay: 1 action (`b010t001` #2); eski mantiq yozilgan barcha `t_issue` larni aynan qayta chiqaradi. |
| "Validator endi ma'nosiz (driver bilan bir xil)" | Validator o'zgartirilmadi; u hamon xom ma'lumotdan mustaqil qayta hisoblaydi va §14.6 darvozasini ushlab turadi. |

## 7. NATIJA — oflayn replay, YAKUNIY kod bilan

`datasets/smoke-tools/p1_replay.py` endi yakuniy `driver.measured_trial_facts`
ni chaqiradi (shu trial record'lari + guard record'lari, probe qatorlari);
`p1-pilot-001` faqat o'qildi (`dr-xr-xr-x`). Natija §3 dagi bilan **aynan
bir xil**:

| | natija |
|---|---|
| `b007t001` | `complete` → `censored` (`probe_gap_exceeded`; oyna `past_pressure`) |
| `b013t004` | `complete` → `censored` (`window_outside_hold`) |
| `b010t001` | `aborted_guard` (o'zgarmadi); action 2 `t_issue` 19629521595 → 19633632690 |
| o'zgargan disposition | A/P2: 2; boshqa yacheykalar: 0 (120 trial) |
| validator'ning ikki sharti replay'dan keyin | 0 buzilish |
| eski `t_issue` mantig'i vs yozilgan | 0 nomuvofiqlik |

**To'liq `tests/`:** `7842c25` da **1124 passed, 1 skipped**; `f576c79` da
**1131 passed, 1 skipped**.

## 8. OLDINDAN qayd etilgan smoke mezoni (trial'lardan OLDIN commit qilindi)

> Bu bo'lim birorta yangi trial'dan **oldin** commit qilinadi va keyin
> **o'zgartirilmaydi**.

**Kod:** `agent/pilot-ready` ning shu commit'i (`main` `bccd118` + uch
tuzatish), ext4 clone, `git_dirty: false`. **Kirish nuqtasi:**
`python3 -m revix.cli run --run-dir … --seed … --blocks 1 --only <arm>,<band>
--allow-pressure`; har run'dan keyin `python3 -m revix.validate --run-dir …
--sut-unit revix-sut.service --sut-target sut`.

| # | run | arm, band | seed |
|---|---|---|---|
| 1 | `smoke-26-A-P2` | A, P2 | 20261041 |
| 2 | `smoke-27-noaction-P2` | no_action, P2 | 20261042 |
| 3 | `smoke-28-A-P2` | A, P2 | 20261043 |
| 4 | `smoke-29-noaction-P2` | no_action, P2 | 20261044 |
| 5 | `smoke-30-A-P2` | A, P2 | 20261045 |
| 6 | `smoke-31-A-P2` | A, P2 | 20261046 |
| 7 | `smoke-32-A-P1` | A, P1 | 20261047 |
| 8 | `smoke-33-A-P0` | A, P0 | 20261048 |

**Mezon (orkestrator bergan, aynan):** har run `validate` dan **0 xato**
bilan o'tadi, **aynan bitta** `trial_end`, **sustain trip yo'q**,
**`harness_error` yo'q**. `P2` dagi runaway `aborted_guard` — e'lon
qilingan kutilma, xato emas. Qo'shimcha: `boot_id`, pid1, `real − mono`
siljishi o'zgarmagan, `oom_kill` o'zgarmagan, `leftover_state` PASS,
`run_meta.disposition_facts` bor. **Birinchi buzilishda to'xtatiladi** va
hisobot qilinadi; tuzatish jonli tizimga qarshi sinov-xato bilan
takrorlanmaydi.

**Oldindan aytilgan CHEKLOV:** 8 trial'da §4 probe uzilishi yoki §17.4
oyna holati **yuzaga kelishi kafolatlanmagan** (p1-pilot-001 da A/P2 dagi
20 trial'dan 2 tasida); yuzaga kelmasa, bu yo'llar faqat unit test va
oflayn replay bilan tekshirilgan bo'ladi.

---

## 9. NATIJA — smoke partiyasi (§8 mezoni BAJARILDI)

**Ketma-ketlik (FAKT):** VM handshake — `READY FOR VM SHUTDOWN` `main` ga
yuborildi; host'da `VirtualBoxVM` (3 PID) `2026-10-04T13:37:45Z` da yo'qoldi
(faqat bo'sh `VBoxSVC` qoldi; VirtualBox Windows host'da ishlaydi, shuning
uchun tekshiruv PowerShell `Get-Process` bilan, guest `pgrep` emas). Qulf
`13:37:57Z` — `13:46:09Z`; olishda `loadavg1` 0.04. Kod `7ae27f7` (ext4
clone, `git_dirty: false`), kirish nuqtasi `revix.cli run … --allow-pressure`.

| run | disposition | guard | eng uzun `≥ 0.35` / `≥ 0.05` | post-oyna faktlari (`measured`) | action `t_issue` | validate |
|---|---|---|---|---|---|---|
| smoke-26 A,P2 | `complete` | trip yo'q | 5.1 / 13.4 s | gap yo'q, `inside_hold` | 1 ta | 0 xato |
| smoke-27 no_action,P2 | `censored` (`horizon_ended_down`) | trip yo'q | 10.7 / 14.7 s | gap yo'q, `inside_hold` | — | 0 xato |
| smoke-28 A,P2 | `complete` | trip yo'q | 9.1 / 14.7 s | gap yo'q, `inside_hold` | 1 ta | 0 xato |
| smoke-29 no_action,P2 | `censored` (`horizon_ended_down`) | trip yo'q | 8.9 / 14.8 s | gap yo'q, `no_t_up` | — | 0 xato |
| smoke-30 A,P2 | `complete` | trip yo'q | 13.5 / 14.8 s | gap yo'q, `inside_hold` | 1 ta | 0 xato |
| smoke-31 A,P2 | `complete` | trip yo'q | 9.7 / 14.8 s | gap yo'q, `inside_hold` | 1 ta | 0 xato |
| smoke-32 A,P1 | `complete` | trip yo'q | 6.4 / 7.7 s | gap yo'q, `inside_hold` | 1 ta | 0 xato |
| smoke-33 A,P0 | `complete` | trip yo'q | 0.0 / 0.0 s | gap yo'q, `no_t_up` | 1 ta | 0 xato |

- **Mezon:** 8/8 `validate` **0 xato** (yagona ogohlantirish `run_filtered`),
  har birida **bitta** `trial_end`, **sustain trip 0**, **`harness_error` 0**
  ⇒ **§8 mezoni BAJARILDI.**
- Post-flight 8/8: `boot_id` va pid1 `653523` o'zgarmagan, `real − mono`
  siljishi 0/+1 µs, `oom_kill` 0 → 0, lab swap max 0, `leftover_state` PASS;
  oxirida `revix*` unit 0. Har `run_meta` da `disposition_facts.method =
  post_window_reducer_facts`; har `trial_end.facts` da
  `window_outside_hold`.
- **Kuzatuv (talqin qilinmaydi):** smoke-30 ning `≥ 0.35` oralig'i 13.5 s
  (guard chegarasi 15 s; V2 smoke'larida max 13.0 s edi).

**CHEKLOV — jonli ishlatilMAGAN yo'llar:** bu partiyada (a) §4 probe
uzilishi, (b) §17.4 oyna hold'dan tashqarida, (c) eskirgan `ActiveExit`
(restart qilingan SUT `active` ga yetmay o'lishi), (d) runaway guard trip va
undan keyingi istisno yo'li **yuzaga kelmadi**. Bu to'rt yo'l faqat unit
testlar (haqiqiy p1-pilot-001 record'laridan) va oflayn replay bilan
tekshirilgan. 120 trial'lik run smoke ko'rsatmagan klassni ochishi mumkin
(`15` §5.2).

**04 revizya yozuvi:** shu revizyadan keyingi `sha256` —
`778134ae4f6116e5db5c9027853c709d8baa517033aab9303088bd025d2ed2c1`
(oldingi `f514394e…18ff`).
