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
