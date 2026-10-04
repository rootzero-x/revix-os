# 17 — `p1-pilot-002`: validatsiya xatosi va validator'ning ustuvorlikka ko'rligi

Bu hujjat ikkinchi pilot run'i `p1-pilot-002` ning `revix.validate`
natijasini (1 xato, 23 ogohlantirish) tahlil qiladi. **Faqat mexanika va
yaroqlilik.** Kod, muzlatilgan matn va validator **o'zgartirilmadi**;
birorta trial yoki bosim ishga tushirilmadi.

Belgilar: **FAKT** — o'lchandi yoki xom record'dan/koddan o'qildi (manba
ko'rsatilgan); **GIPOTEZA** — o'lchanmagan taxmin; **NATIJA** — muzlatilgan
qoidaning FAKT'larga qo'llanishi; **TALQIN** — xulosa; **CHEKLOV** — ayta
olmaydigan narsa.

**Branch:** `agent/pilot-ready` (`main` `8deaaf0` ga fast-forward qilingan).
**Run'lar:** `~/revix-runs/p1-pilot-002` va `~/revix-runs/p1-pilot-001`
(ikkalasi faqat o'qish uchun, katalog `dr-xr-xr-x`). Run kataloglariga
**hech narsa yozilmadi**; tahlil chiqishi `~/pilotready-scratch/p12/` da
(`gate.json`, skriptlar).

---

## 0. OSHKORA E'LON — kim nimani ko'rdi

- **Orkestrator** **ikkala** pilotning **har `(arm × pressure)` yacheykasi
  bo'yicha disposition sonlarini** ko'rgan (uning o'z bayonoti). Demak
  quyidagi har qanday darvoza qarori ikkala run'ning yacheyka hisoblari
  ma'lum bo'lgandan **keyin** qabul qilinadi.
- **Men** faqat o'zim ochgan narsani ko'rdim:
  (a) `p1-pilot-002` ning `validate.txt` to'liq matni, `launcher.log`,
  boshlang'ich/yakuniy marker'lar, `clock-watch` xulosasi, `run_meta` ning
  kalit maydonlari, va `driver.json` dagi **run bo'yicha umumiy** hisob —
  `aborted_guard 9`, `censored 70`, `complete 41` (yacheyka bo'yicha
  **emas**);
  (b) probe uzilishi bor **24 trial** ning har biri uchun: `trial_id`,
  blok, yacheyka, disposition, `reason`, `matched_rules`, uzilishlarning
  vaqti va `probe_overrun` soni (§5). Bu — shu 24 trial uchun yacheyka ×
  disposition ma'lumoti; boshqa 96 trial uchun yacheyka bo'yicha hisob
  **ko'rmadim va hisoblamadim**;
  (c) `b010t005` ning probe'dan boshqa record'lari (timeline, §2.3);
  (d) ikkala run'da `guard_event` × disposition kesishmasi (§3): har
  guard_event'li trial `aborted_guard`; `contaminated`, `washout_timeout`,
  `harness_error` disposition'i va `harness_error` record'i ikkala run'da
  ham **0**. `p1-pilot-001` uchun bu run bo'yicha `aborted_guard` sonini
  ko'rsatadi — u `15` §0 da allaqachon e'lon qilingan; men uni
  `p1-pilot-002` ning soni bilan **solishtirmayman** (v1.13, 0.5);
  (e) `p1-pilot-001`: validator'ning xotirada qayta ishlatilgan natijasi va
  uning ikki uzilishli trial'i (`15` dan ma'lum).
- **Ko'rmadim / hisoblamadim:** 120 trial bo'yicha yacheyka × disposition
  jadvali; `t_up`, downtime, VR, FR, recovery, p-qiymat, effekt — **hech
  biri**; uzilishsiz `censored` trial'larning sababi; `pressure.jsonl`,
  `psi.csv`; guest disk IO, `dmesg`, host holati vaqt bo'yicha; fsync
  davomiyligi (o'lchanmagan, §5.3).

---

## 1. FAKT — validator nima dedi

`~/revix-runs/p1-pilot-002/validate.txt` va xotirada qayta ishlatilgan
`validate_run_dir(..., sut_unit="revix-sut.service", sut_target="sut")`
(o'zgartirilmagan kod, `8deaaf0`) bir xil natija beradi:

| | soni | kodlar |
|---|---|---|
| xato | **1** | `probe_gap` — `b010t005`, disposition `aborted_guard`, 1 uzilish, **678 119 µs** |
| ogohlantirish | **23** | hammasi `probe_gap`, hammasi `censored` |

Run'ning boshqa holati (FAKT, oldin o'qilgan): 120/120 `trial_end`; driver
rc 0; `wall_s 6792`; `git_commit 8deaaf0`, `git_dirty False`;
`boot_id` va pid1 o'zgarmagan; `real_minus_mono` +2 µs; `oom_kill` 0 → 0;
`clock-watch` `|Δreal − Δmono|` ≤ 9 µs; `run_meta.disposition_facts.method
= post_window_reducer_facts`.

---

## 2. Savol 1 — `check_probe_gaps` §4, §12 va ustuvorlik bilan mosmi

### 2.1 FAKT — kod (`revix/validate.py`)

```python
# :615  check_probe_gaps
        disp = t.disposition_raw
        sev = SEVERITY_ERROR if disp != "censored" else SEVERITY_WARNING   # :632
```

`check_probe_coverage` (:2316) boshlang'ich/oxirgi qoplam uzilishi uchun
aynan shu shaklni ishlatadi: `sev = SEVERITY_WARNING if disp == "censored"
else SEVERITY_ERROR` (:2356). Demak **`censored` dan boshqa har
disposition** — `complete` ham, `aborted_guard`, `contaminated`,
`washout_timeout`, `harness_error` ham — uzilish bo'lsa **XATO**.

### 2.2 FAKT — muzlatilgan jumlalar (`PREREGISTRATION.md` v1.13)

1. **§4, invalidator'lar** (:2999–3004): yopiq enum
   *"`contract_fail`, … `throughput_below_theta`, `guard_fired`"*, va
   darhol: *"**Probe uzilishi > 2×P** → trial `censored`, **`failed`
   emas**. Instrumentatsiya yo'qolishi hech qachon jimgina natijaga
   aylanmaydi."*
2. **§12** (:3486): *"`contaminated` va `aborted_guard` trial'lar
   birlamchi analizdan chiqariladi, LEKIN ularning ulushi natija sifatida
   beriladi."* Jadval: `aborted_guard` = *"host guard ishga tushdi"*; va
   *"Har trial'ga **aynan bitta** disposition."*
3. **§6.2** (:3112): *"censored trial'lar Kaplan–Meier / log-rank
   analiziga **kiradi**"*.
4. **§14.6(4)** (:3593): *"trial ichida probe uzilishi > 2×P yo'q (aks
   holda trial `censored`)"*; §14.6 oxiri: *"Validatsiyadan o'tmagan run
   analiz qilinmaydi."*
5. **v1.12 izohi** (:785–788): *"`aborted_guard` … birlamchi analizdan
   **chiqariladi** (§12; §16.2(B) — birlamchi to'plam `(disposition,
   disposition_source)` bilan aniqlanadi va `aborted_guard` unga
   kirmaydi)."*
6. **v1.13 amendment log** (:1058–1059): istisno yo'li nuqsoni
   *"trial'ga §12 ning ustuvorligi (`aborted_guard`) o'rniga
   `harness_error` yoziladi"* — ya'ni muzlatilgan matn `aborted_guard`
   ning boshqa disposition'lardan **ustunligini** nuqson mezoni sifatida
   ishlatgan.
7. **Shartnoma `04` §8.1** (:1610–1640): avtoritet — driver'ning
   `trial_end.disposition` i, u `schedule.explain_disposition()` dan;
   `schedule.DISPOSITION_RULES` tartibi: `harness_error` → `guard_fired` →
   uch `contaminated` fakti → `washout_timed_out` → `probe_gap_exceeded` →
   `window_outside_hold` → `horizon_ended_down` → `measured`. Kodning izohi
   (`schedule.py:743–748`, muzlatilgan matn **emas**): eksklyuziya sababi
   censoring'dan ustun bo'lishi shart, *"aks holda chiqarilishi kerak
   bo'lgan trial "censored" yorlig'i ostida analizga kirib ketardi"*.

### 2.3 FAKT — `b010t005` (`no_action/P2`, blok 10, o'rni 5)

`trial_begin` dan sekundlar (probe'dan boshqa record'lar):

| t (s) | record |
|---|---|
| 0.000 | `trial_begin` |
| 0.066 | `prober_start` |
| **5.066 → 5.744** | **probe uzilishi, 678 119 µs** (baseline ichida) |
| 5.414, 5.744 | `probe_overrun` ×2 |
| 15.000 | `baseline_window` |
| 23.646 | `fault_inject` (`exit`) |
| 27.275 | `guard_event` — `kill_subtree`, `user_full_rate2s_runaway` |
| 41.100 | `trial_end`: `reason guard_fired`, `aborted_guard`, `matched_rules = [guard_fired, bystander_lost_contract, probe_gap_exceeded, horizon_ended_down, measured]` |

- Uzilish injeksiyadan **18 s oldin** va guard'dan **22 s oldin**.
- Driver uzilishni **ko'rgan**: `probe_gap_exceeded` `matched_rules` da
  bor; disposition'ni undan oldingi qoida (`guard_fired`) bergan. Ikkinchi
  mustaqil eksklyuziya fakti ham bor: `bystander_lost_contract`
  (`contaminated`).

### 2.4 NATIJA

- **§12 + §16.2(B) + v1.12 izohi:** guard ishlagan trial — `aborted_guard`,
  birlamchi to'plamdan chiqariladi. `b010t005` aynan shunday.
- **§4 ning maqsad jumlasi** (*"jimgina natijaga aylanmaydi"*): chiqarilgan
  trial natijaga **umuman** aylanmaydi; uzilish `matched_rules` da yozilgan
  — jimgina emas.
- **§14.6(4) ning so'zma-so'z o'qilishi:** uzilish bor, trial `censored`
  emas ⇒ invariant buzilgan. **Faqat shu qavs** qat'iyroq o'qishni
  so'zma-so'z qo'llab-quvvatlaydi.
- So'zma-so'z o'qish bilan guard + uzilish trial'i uchun **muvofiq
  disposition yo'q**: `aborted_guard` §14.6(4) ni buzadi; `censored` §12 ning
  ta'rifini (*"host guard ishga tushdi"*) buzadi va §6.2 bo'yicha guard
  o'ldirgan trial'ni KM ga **kiritadi** — §12 ning *"birlamchi analizdan
  chiqariladi"* jumlasiga teskari.

### 2.5 Hukm

**Orkestrator o'qishi TASDIQLANDI, bitta tuzatish bilan.** Validator
ustuvorlikka ko'r: §12, §16.2(B), v1.12 izohi, `04` §8.1 va
`schedule.DISPOSITION_RULES` bilan **mos emas**. **Lekin** "qat'iyroq
o'qishni qo'llovchi muzlatilgan jumla yo'q" degan da'vo **rad etiladi**:
§14.6(4) ning qavsi so'zma-so'z aynan validator qilgan narsani aytadi, va
validator docstring'i §4 ni so'zma-so'z keltiradi. To'g'riroq ifoda:
**validator §14.6(4) ni so'zma-so'z amalga oshiradi; §14.6(4) ning o'zi
ustuvorlikni hisobga olmaydi va guard + uzilish trial'i uchun §12 bilan
ziddiyatga kiradi.** Ustuvorlik **tartibi** `PREREGISTRATION.md` da tartiblangan
ro'yxat sifatida yozilmagan — u `schedule.py` va `04` §8.1 da; muzlatilgan
matnda faqat uning **oqibati** (`aborted_guard` chiqariladi) va v1.13 ning
nuqson mezoni (:1059) bor. Demak validator'ni tuzatish — §14.6(4) ni
**ma'lumotdan keyin talqin qilish** (§6).

---

## 3. Savol 2 — `revix/validate.py` ning har disposition'ga bog'liq tekshiruvi

`MEASURED_DISPOSITIONS = ("complete", "censored")` (:156).

| tekshiruv (qator) | shart | `aborted_guard` / `contaminated` / `washout_timeout` / `harness_error` da | ustuvorlikka mos? |
|---|---|---|---|
| `check_probe_gaps` (:615, :632) | uzilish va disp ≠ `censored` ⇒ XATO | **XATO** | **YO'Q** — ko'r |
| `check_probe_coverage` → `probe_coverage_gap` (:2356) | chegaradagi uzilish va disp ≠ `censored` ⇒ XATO | **XATO** | **YO'Q** — ko'r (ikkala pilotda 0 marta ishlagan) |
| `check_probe_coverage` → `trial_without_probes` (:2339) | faqat `complete` | jim | ha |
| `check_window_containment` (:1986) | faqat `complete` | jim | ha — `window_outside_hold` `probe_gap` dan keyin |
| `check_guard_stream` → `guard_event_not_reflected` (:2470) | oynada guard_event va disp ∈ {complete, censored} ⇒ XATO | jim | **yumshoq**: guard_event'li `contaminated`/`washout_timeout` ni ushlamaydi, holbuki `guard_fired` ulardan ustun. FAKT: ikkala run'da har guard_event'li trial `aborted_guard` — ta'siri **0** |
| `check_harness_errors` (:2483) | `harness_error` record'i ⇒ disp `harness_error` | `aborted_guard` + harness record ⇒ XATO | ha — `schedule` tartibida `harness_error` birinchi; `reduce` tartibi boshqacha, lekin `04` §8.1 bo'yicha driver avtoritet. Ikkala run'da harness record **0** |
| `check_disposition_cross_check` (:2259) | driver ≠ reducer ⇒ OGOHLANTIRISH | ogohlantirish | ha — `04` §8.1, 3-qoida |
| `check_trial_events` (:1831), `check_trial_overhead` (:1927), `sut_unit_state_missing` (:2252) | faqat MEASURED | jim | ha — chiqarilgan trial to'liq o'lchov talab qilmaydi |
| `check_trial_horizon` (:2079, :2094) | erta tugash faqat `aborted_guard`, `harness_error` uchun ruxsat | `contaminated`/`washout_timeout` erta tugasa XATO | ehtimol ha — erta tugash guard va harness istisnosiga xos; driver'ning erta yopish yo'llari bu tahlilda **tekshirilmadi**. Ikkala run'da `contaminated`/`washout_timeout` 0 — ta'siri 0 |
| `check_actions` (:645) | disposition'dan **mustaqil** | har action tekshiriladi | ha — §14.6(6) *"har `action` uchun"*; bu disposition masalasi emas, log yaxlitligi |

**NATIJA:** ustuvorlikka ko'r **faqat ikkitasi** — `probe_gap` va
`probe_coverage_gap`, ikkalasi bir xil `disp != "censored"` shakli bilan.
Bittasi teskari yo'nalishda yumshoq (`guard_event_not_reflected`), lekin u
xato **yaratmaydi**, faqat ushlamaydi; ikkala pilotda ta'siri 0.

---

## 4. Savol 3 — ikkala pilot bo'yicha ustuvorlikka mos tekshiruv

**Usul (FAKT):** `~/pilotready-scratch/p12/p12_gate.py` — `revix.validate`
`8deaaf0` dan import qilinadi, `validate_run_dir` **o'zgartirilmagan** holda
bir marta, keyin **faqat xotirada** `check_probe_gaps` va
`check_probe_coverage` almashtirilgan holda ikkinchi marta ishlatiladi.
Almashtirish: asl topilmalar olinadi, faqat og'irlik qayta beriladi —
**XATO faqat disposition `complete` bo'lsa** (`DISPOSITION_RULES` da
`probe_gap_exceeded` dan **past** turgan yagona disposition), aks holda
ogohlantirish. `validate.py` fayli tahrirlanmadi.

| run | asl | ustuvorlikka mos | verdikti o'zgargan trial'lar |
|---|---|---|---|
| `p1-pilot-001` | **O'TMADI** — 4 xato (`action_without_invocation_change` 1, `probe_gap` 1, `window_outside_hold_complete` 2), 3 ogohl. | **O'TMADI** — aynan o'sha 4 xato, 3 ogohl. | **0** |
| `p1-pilot-002` | **O'TMADI** — 1 xato, 23 ogohl. | **O'TADI** — 0 xato, 24 ogohl. | **1** — `b010t005` (XATO → ogohl.) |

**Ustuvorlikda oldin turgan disposition + uzilish (FAKT):**

- `p1-pilot-002`: **faqat `b010t005`** (`aborted_guard`). Qolgan 23 uzilishli
  trial — `censored`, `reason probe_gap_exceeded`.
- `p1-pilot-001`: **yo'q**. Uning ikki uzilishli trial'i — `b007t001`
  (`complete`) va `b009t000` (`censored`, `reason horizon_ended_down`).

**`p1-pilot-001` ning har xatosi joyida qoladi (NATIJA):**

| trial | kod | nega ustuvorlik tuzatishi unga tegmaydi |
|---|---|---|
| `b007t001` | `probe_gap` + `window_outside_hold_complete` | disposition `complete` — har o'qishda XATO |
| `b013t004` | `window_outside_hold_complete` | `complete`; tekshiruv allaqachon faqat `complete` uchun |
| `b010t001` | `action_without_invocation_change` | `aborted_guard`, lekin §14.6(6) disposition'dan mustaqil; sabab — eskirgan `ActiveExitTimestamp` (`15` §3) |

Demak ustuvorlik tuzatishi `p1-pilot-001` ni **qutqarmaydi**.

**Muqobil variant (NATIJA, `gate.json` dagi `matched_rules` dan):**
og'irlikni disposition'ga emas, **faktga** bog'lash — "uzilish bor ⇒
`probe_gap_exceeded` `matched_rules` da bo'lishi shart, va disposition
`complete` emas". Bu qat'iyroq: chiqarilgan trial'dagi uzilish yozilmay
qolsa ham ushlaydi. `p1-pilot-002` da 24 uzilishli trial'ning **hammasida**
`probe_gap_exceeded` bor ⇒ 0 xato. `p1-pilot-001` da `b009t000` da u
**yo'q** (eski driver nuqsoni, `15` §2) ⇒ xatolar **4 dan 5 ga** ortadi,
xatoli trial'lar 3 dan 4 ga. Bu variant ham `p1-pilot-001` ni qutqarmaydi —
aksincha.

---

## 5. Savol 4 — 23 ogohlantirish

### 5.1 FAKT — turlari

Hammasi **bitta tur**: `probe_gap`, og'irlik ogohlantirish, disposition
`censored`, `reason probe_gap_exceeded` (23 tasining hammasida).
`probe_coverage_gap` — 0. Trial'lar: `b003t005`, `b011t000`, `b011t005`,
`b012t003`, `b012t004`, `b013t000`, `b014t000`, `b014t001`, `b014t003`,
`b014t004`, `b014t005`, `b016t003`, `b016t004`, `b016t005`, `b017t000`,
`b017t001`, `b017t002`, `b018t001`, `b018t002`, `b018t003`, `b018t004`,
`b018t005`, `b019t000`. Eng katta uzilish 4 689 678 µs (`b016t003`).
`b017t001` va `b019t000` da `window_outside_hold` ham mos keldi, lekin
`probe_gap_exceeded` undan oldin turadi.

### 5.2 NATIJA — birortasi aslida xatomi

**Yo'q.** §4 va §14.6(4) uzilishli trial'ni `censored` qilishni talab
qiladi — 23 tasi `censored`, va aynan shu qoida bo'yicha. Muzlatilgan
matnning hech bir jumlasi bunday trial'ni run'ni yiqitadigan xato deb
atamaydi.

### 5.3 FAKT — mexanika (yaroqlilik, natija emas)

24 uzilishli trial (23 + `b010t005`) bo'yicha:

- **68 ta** uzilish > 2P; shu trial'larda **101 ta** `probe_overrun` record'i.
- **Blok bo'yicha** (trial soni): 3:1, 10:1, 11:2, 12:2, 13:1, 14:5,
  16:3, 17:3, 18:5, 19:1 ⇒ 0–9 bloklarda **1**, 10–19 bloklarda **23**.
- **Yacheyka bo'yicha** (trial soni, `b010t005` bilan): `A/P0` 3,
  `A/P1` 5, `A/P2` 6, `no_action/P0` 5, `no_action/P1` 2, `no_action/P2` 3.
- **Faza:** 68 uzilishdan **55 tasi** shu trial'ning `prober_start` idan
  `k × 5 s` dan keyin **0.0–0.3 s** ichida boshlanadi (`k` = 1…8). Bir
  trial ichidagi ketma-ket uzilish juftlarining **31/44** tasi orasidagi
  masofa `5 s` karralisidan ≤ 0.25 s farq qiladi. 0.1 s donadorlikda tekis
  taqsimotda 0.0–0.3 s oralig'iga tushish ulushi taxminan 4/50.
  `b010t005`: `prober_start` 0.066 s, uzilish 5.066 s da — aniq **5.000 s**.
- **Kod:** prober har trial uchun qayta ishga tushadi
  (`driver._start_prober`, :3197); u `probe_sample` ni `schema.CsvWriter`
  orqali yozadi (`prober.py:653`, :886), va `CsvWriter.write` har
  `flush_interval_s = 5.0` s da **o'lchov tsikli ichida sinxron**
  `flush()` + `os.fsync()` qiladi (`schema.py:118`, :147–150).
- `revix/schema.py` va `revix/prober.py` `4cbd1c6` (`p1-pilot-001`) va
  `8deaaf0` (`p1-pilot-002`) orasida **bir xil** (`git diff --stat` bo'sh;
  oxirgi o'zgarish `b712f6d`, ikkalasining ajdodi). `p1-pilot-001` da
  uzilishli trial 2 ta edi (`15` dan ma'lum). Bu instrument kodi haqidagi
  fakt, natijalar solishtiruvi emas.

**GIPOTEZA:** uzilishlarning asosiy qismi prober'ning **o'z** CSV
fayliga 5 s lik sinxron `fsync` ning cho'zilishi; u kech bloklarda
paydo bo'lgan, demak sabab kod emas, muhit (guest disk / host IO yoki fayl
hajmi). **O'lchanmagan:** `fsync` davomiyligi, disk IO, host holati vaqt
bo'yicha. 13 uzilish bu fazaga tushmaydi — ularning sababi noma'lum.
Validator uzilishni `probe_sample` vaqtlaridan topadi; fsync'ning o'zi
hech qayerga yozilmaydi.

### 5.4 TALQIN

23 ogohlantirish validator nuqsoni emas. Lekin 120 trial'dan 24 tasida
(20%) instrumentatsiya yo'qolgan, yo'qotish instrumentning o'zi bilan
fazaga bog'langan va barcha olti yacheykada uchraydi. Bu muzlatilgan qoida
bo'yicha `censored` bilan to'g'ri ishlanadi, lekin uni hisobotda **alohida
yaroqlilik bandi** sifatida yacheyka jadvali bilan berish kerak (v1.13 0.5
ning 7-bandi yacheyka jadvalini majburiy qiladi). Uning natijaga ta'sirini
men baholamadim.

---

## 6. Savol 5 — variantlar

### 6.1 Qoidalar (iqtibos)

- **v1.13 (0.6)** (:133–141): *"Agar `p1-pilot-002` ham validatsiyadan
  o'tmasa. U §14.6 bo'yicha **analiz qilinmaydi**; xuddi `p1-pilot-001`
  kabi **saqlanadi, yaroqsiz deb belgilanadi, o'chirilmaydi** … **Uchinchi
  run yangi amendment'siz (v1.14 yoki keyingi) O'TKAZILMAYDI** — u
  amendment uchinchi run'dan **oldin** merge qilinadi va tag qilinadi."*
- **v1.13 (0.5)**: `p1-pilot-002` — *"analiz qilinishi mumkin bo'lgan
  YAGONA pilot run'i"*; `p1-pilot-001` hech qachon birlashtirilmaydi va
  solishtirilmaydi.
- **v1.13, V-B ning rad etilishi** (:277): validator'ni yoki `04` ning
  avtoritet qoidasini *"**ma'lumot ko'rilgandan keyin** o'zgartirish
  kerak"* … *"Darvoza ma'lumotdan keyin yumshatiladi"*.
- **§14.6:** *"Validatsiyadan o'tmagan run analiz qilinmaydi."*

**NATIJA:** v1.13 ostida `p1-pilot-002` **hozir** yaroqsiz — (0.6) buning
oqibatini oldindan belgilagan. Quyidagi har variant **v1.14 amendment'ini**
talab qiladi.

### 6.2 Variantlar

| # | variant | muzlatilgan matn / v1.13 nima deydi | narxi |
|---|---|---|---|
| **(a)** | v1.14: validator og'irligini `DISPOSITION_RULES` ustuvorligiga bog'lash (`probe_gap`, `probe_coverage_gap`: XATO faqat `complete` da, yoki §4 dagi fakt varianti), keyin mavjud `p1-pilot-002` ni qayta validatsiya qilish | (0.6) `p1-pilot-002` muvaffaqiyatsiz bo'lsa uni yaroqsiz deb **oldindan** belgilagan; (a) shu oqibatni run ko'rilgandan **keyin** o'zgartiradi. Shakli — V-B: darvoza ma'lumotdan keyin o'zgaradi. Farqi (TALQIN): V-B xom ma'lumotni qayta tasniflab disposition'larni o'zgartirardi; (a) birorta disposition'ni o'zgartirmaydi, bitta trial'ning **og'irligini** o'zgartiradi, u chiqarilgan holda qoladi, va tuzatish validator'ni §12/§16.2(B) bilan **mos qiladi** | Darvoza o'zgarishining run'ga ta'siri qarordan oldin **to'liq ma'lum** (O'TMADI → O'TADI) — bias xavfi shaklan maksimal. Orkestrator ikkala run'ning yacheyka sonlarini ko'rgan. 23 uzilishli `censored` trial va fsync mexanizmi (§5) qoladi. Vaqt narxi kichik |
| **(b)** | v1.14 (merge + tag), keyin uchinchi run; `p1-pilot-002` yaroqsiz qoladi | (0.6) aynan shu yo'lni ko'zda tutadi; (0.5) ning "yagona run" qoidasi v1.14 da qayta belgilanadi; uchala run hech qachon birlashtirilmaydi | ~6800 s wall + VM + lock; uchinchi qayta o'tkazish qarori ham hisoblar ko'rilgandan keyin. **Validator o'zgarmasa** takrorlanish ehtimoli quyida; **o'zgarsa**, darvoza baribir o'zgaradi — lekin u baholaydigan ma'lumotdan **oldin** |
| **(c1)** | `p1-pilot-002` yaroqsiz, uchinchi run yo'q; P1 pilot yaroqli run'siz yakunlanadi | (0.6) ga so'zma-so'z mos | analiz qilinadigan pilot yo'q; ikki yaroqsiz run hisobot qilinadi |
| **(c2)** | v1.14: validator tuzatishi **va** prober yozuvini o'zgartirish (masalan, fsync'ni o'lchov tsiklidan chiqarish), smoke bilan, keyin uchinchi run | instrument pilotlar orasida o'zgaradi — v1.14 da asoslash kerak; §5.3 gipotezasi avval **o'lchanishi** kerak (fsync davomiyligi) | eng ko'p ish; instrument o'zgarishi va qo'shimcha smoke; 20% uzilish yo'qotishini kamaytirishi mumkin (GIPOTEZA) |
| **(c3)** | (a) ni faqat "sezgirlik" sifatida, asosiy hukm "yaroqsiz" qolgan holda | (0.6) *"analiz qilinmaydi"* — yaroqsiz run'ning har qanday analizi, sezgirlik ham, taqiqlangan; `p1-pilot-001` uchun sezgirlik/takrorlash sifatida ishlatish (V-C) ham rad etilgan (v1.13, 3.3-band) | ruxsat yo'q |

### 6.3 (b) — validator o'zgarmasa, takrorlanish bahosi

Tuzatilgan driver `probe_gap_exceeded` ni `reduce.probe_gaps` dan oladi
(`8deaaf0`), demak `complete` + uzilish **konstruksiya bo'yicha**
bo'lmaydi; o'zgarmagan validator uchinchi run'da **faqat** chiqarilgan
trial'dagi uzilishdan yiqiladi. Faqat `p1-pilot-002` ning `aborted_guard`
trial'lari asosida (orkestrator so'ragan sanoq):

- uzilishli `aborted_guard`: **1 / 9** ⇒ `p̂ = 0.111`, Clopper–Pearson 95%
  `[0.0028, 0.4825]` (arifmetika, o'lchangan stavka emas);
- agar uchinchi run'da ham 9 ta `aborted_guard` bo'lsa, kamida bittasida
  uzilish ehtimoli `1 − (1 − p)^9`: nuqta **0.65**, interval chegaralari
  bilan **0.025 … 0.997**.

**CHEKLOV:** bu baho amalda **ma'lumot bermaydi** — interval deyarli butun
[0, 1] ni qoplaydi; `aborted_guard` soni uchinchi run'da noma'lum; va
uzilishlar **statsionar emas** (23/24 trial 10–19 bloklarda, §5.3).
**TALQIN:** o'zgarmagan validator bilan uchinchi run takroriy yiqilishdan
himoyalanmagan, va yiqilsa (0.6) bo'yicha to'rtinchi amendment kerak bo'ladi.

### 6.4 Har variantda nima oshkora e'lon qilinishi shart

1. **Darvoza ikkinchi muvaffaqiyatsizlikdan keyin o'zgartirilmoqda** —
   (a) da `p1-pilot-002` ning o'zi uchun, (b)/(c2) da validator o'zgarsa,
   keyingi run uchun. Bu jumla aynan shunday yoziladi.
2. Kim nimani ko'rdi: orkestrator — ikkala run'ning yacheyka hisoblari;
   bu tahlil — §0.
3. O'zgarmagan validator ostida `p1-pilot-002` **O'TMADI** (1 xato) — bu
   fakt hisobotdan olib tashlanmaydi.
4. Validator diff'i (ikki qator, §2.1), uning muzlatilgan asosi (§2.2) va
   §14.6(4) ning so'zma-so'z o'qilishi u bilan ziddiyatda ekani.
5. Tuzatishning ikkala run bo'yicha ta'siri: `p1-pilot-002` da 1 trial,
   `p1-pilot-001` da 0 (fakt varianti bilan +1 xato) — ya'ni u `p1-pilot-001`
   ni qutqarmaydi.
6. 24 uzilishli trial, ularning blok va yacheyka taqsimoti, va fsync
   gipotezasi — tuzatishdan **mustaqil** yaroqlilik bandi.
7. (b)/(c2) uchun: uchinchi run qarori ham hisoblar ko'rilgandan keyin;
   run'lar hech qachon birlashtirilmaydi.

---

## 7. TALQIN (qaror emas)

- Validator nuqsoni haqiqiy: u ustuvorlikka ko'r va guard + uzilish
  trial'ini hech qanday disposition bilan o'tkaza olmaydi. Uning tuzatilishi
  muzlatilgan §12/§16.2(B) bilan izchil.
- Lekin xatoni muzlatilgan matnning o'zi (§14.6(4)) qo'llaydi, va v1.13 bu
  holatning oqibatini oldindan yozgan. Shuning uchun (a) **texnik
  jihatdan to'g'ri**, lekin **protsedura jihatidan** V-B bilan bir xil
  shakldagi qaror; uni tanlash faqat 6.4 dagi to'liq e'lon bilan
  himoyalanadi va bias xavfi nolga tushmaydi.
- (b) validator tuzatilmasa nima bo'lishini nazorat qilmaydi; tuzatilsa,
  darvoza o'zgarishi o'lchanadigan ma'lumotdan oldin bo'ladi — bu (a) dan
  tozaroq, narxi bir run.
- Qaysi variant tanlansa ham, §5 dagi 20% instrumentatsiya yo'qotishi
  alohida masala, va u uchinchi run'da ham takrorlanishi mumkin (GIPOTEZA).

## 8. CHEKLOV

- Ustuvorlik tartibi muzlatilgan matnda tartiblangan ro'yxat sifatida yo'q;
  §2.5 hukmi `04` §8.1 va kodga tayanadi.
- Xotiradagi qayta validatsiya faqat ikki tekshiruvning og'irligini
  o'zgartiradi; v1.14 da yozilgan haqiqiy validator boshqacha bo'lishi
  mumkin (masalan, `guard_event_not_reflected` ni ham kuchaytirsa).
- fsync gipotezasi o'lchanmagan; 68 uzilishdan 13 tasining sababi noma'lum.
- 6.3 dagi baho bir run'ning 9 trial'iga asoslangan va statsionarlikni faraz
  qiladi, holbuki ma'lumot bunga qarshi.
- Natijaga oid hech narsa hisoblanmadi (§0).

## 9. Fayllar

| fayl | nima |
|---|---|
| `~/pilotready-scratch/p12/p12_gate.py`, `gate.json` | asl va ustuvorlikka mos validatsiya, uzilishli trial'lar |
| `~/pilotready-scratch/p12/p12_fsync.py` | fsync simulyatsiyasi (yaqinlashuv; §5.3 da ishlatilmadi — konstruktor vaqti noma'lum) |
| `revix/validate.py` :615, :632, :2316, :2356, :2402, :2470, :2483 | tekshiruvlar |
| `revix/schema.py` :118, :147–150; `revix/prober.py` :653, :886 | 5 s fsync |
| `PREREGISTRATION.md` :133–141, :277, :785–788, :1059, :3003, :3112, :3486, :3593 | iqtiboslar |
| `docs/architecture/04-driver-va-analiz-shartnomasi.md` §8.1 | avtoritet va tartib |

---

## 10. Tuzatish (variant (a)) — spetsifikatsiya va KUTILGAN natija, isbotdan OLDIN

Orkestrator qarori: **(a)**, validator'ning ustuvorlik bilan ishlashini
**ikki yo'nalishda simmetrik** tuzatish; uchinchi run yo'q; `v1.14`
amendment'i alohida yoziladi (`PREREGISTRATION.md` ga bu branch tegmaydi).
Bu bo'lim kod o'zgarishidan va har qanday isbot ishga tushirilishidan
**oldin** commit qilinadi.

**Tamoyil.** Probe uzilishi **o'lchangan natija da'vosini** — `complete` ni —
bekor qiladi. U trial'ni natija analizidan allaqachon chiqaradigan va
muzlatilgan tartibda uzilish qoidasidan **oldin** turadigan disposition'ga
zid kela olmaydi (`schedule.DISPOSITION_RULES`, `reduce.derive_disposition`,
`04` §8.1). §14.6(4) va §12 shu tartib ostida **birga** o'qiladi —
`p1-pilot-002` dan keyin qabul qilingan qaror; §14.6(4) kodda qayta
ifodalanmaydi.

**Spetsifikatsiya (hozir belgilanadi, verdikt ko'rib emas):**

1. `check_probe_gaps`, `check_probe_coverage` (`probe_coverage_gap`):
   **XATO faqat `complete` da**; boshqa har disposition'da **OGOHLANTIRISH**
   (uzilish baribir hisobot qilinadi).
2. `guard_event_not_reflected`: trial oynasida guard_event bo'lsa
   disposition `aborted_guard` yoki undan oldin turgan `harness_error`
   bo'lishi shart; **boshqa har disposition** (`contaminated`,
   `washout_timeout` ham) — XATO.
3. Auditdagi boshqa tekshiruvlar o'zgarmaydi; shu tamoyil bo'yicha noto'g'ri
   tartiblangan narsa topilsa — faqat hisobot.

**Usul.** `git archive` bilan validator nusxasi (`revix/` paketi)
`~/pilotready-scratch/p13/<before|after>/` ga; `python3 -m revix.validate
--run-dir <run> --sut-unit revix-sut.service --sut-target sut --json`
(launcher `pilot-run2.sh` bilan bir xil argumentlar); chiqish faqat
`~/pilotready-scratch/p13/` ga; pilot kataloglari faqat o'qiladi.
"Oldin" — `2849896` (o'zgarmagan validator), "keyin" — oxirgi kod commit'i.

**KUTILGAN (oldindan yozildi):**

| run | oldin | keyin |
|---|---|---|
| `p1-pilot-001` | 4 xato (`action_without_invocation_change` 1, `probe_gap` 1 — `b007t001`, `window_outside_hold_complete` 2), 3 ogohl. (`disposition_cross_check` 2, `probe_gap` 1 — `b009t000`) | **o'zgarmaydi**: 4 xato, 3 ogohl., xuddi shu kodlar va trial'lar |
| `p1-pilot-002` | 1 xato (`probe_gap` — `b010t005`), 23 ogohl. (`probe_gap`) | **0 xato, 24 ogohl.** (`probe_gap`) |

`guard_event_not_reflected` va `probe_coverage_gap` — ikkala run'da, oldin
ham keyin ham **0**. O'zgaradigan **yagona** topilma: `b010t005` ning
`probe_gap` i, XATO → OGOHLANTIRISH.

**To'xtash qoidasi.** Boshqa har qanday farq (son, kod, trial yoki
og'irlik) bo'lsa — to'xtayman va orkestratorga xabar beraman; kod commit
qilinmaydi.
