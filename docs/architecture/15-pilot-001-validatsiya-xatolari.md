# 15 — `p1-pilot-001`: validator xatolarining ildiz sababi

Bu hujjat birinchi to'liq pilot run'i `p1-pilot-001` ning `validate`
xatolarini tahlil qiladi. **Faqat mexanika va yaroqlilik.** Bu yerda kod,
muzlatilgan matn va validator **o'zgartirilmadi**.

Belgilar: **FAKT** — o'lchandi yoki xom record'dan o'qildi (manba
ko'rsatilgan); **GIPOTEZA** — o'lchanmagan taxmin; **NATIJA** — muzlatilgan
qoidaning FAKT'larga qo'llanishi; **TALQIN** — xulosa; **CHEKLOV** — ayta
olmaydigan narsa.

**Branch:** `agent/pilot-ready` (`main` `4cbd1c6` ga fast-forward qilingan).
**Run:** `~/revix-runs/p1-pilot-001` (faqat o'qish uchun; katalog `dr-xr-xr-x`,
zaxira `~/revix-runs/_backup/p1-pilot-001.tar.zst`). Run katalogiga
**hech narsa yozilmadi**; tahlil chiqishi `~/pilotready-scratch/p1-001/` da.

---

## 0. OSHKORA E'LON — kim nimani ko'rdi

- **Orkestrator** pilot ishlayotgan paytda **har `(arm × pressure)`
  yacheykasi bo'yicha disposition sonlarini** chop etgan (uning o'z
  bayonoti). Pilotning disposition hisoblari orkestratorga shundan ma'lum.
- **Men** (shu tahlil davomida) quyidagilarni ko'rdim: (a) `validate.txt`
  ning to'liq matni; (b) `driver.json` dagi **run bo'yicha umumiy**
  disposition hisobi — `aborted_guard 10`, `censored 57`, `complete 53` —
  **yacheyka bo'yicha emas**; (c) `guard.jsonl` ning 10 ta `guard_event`
  i (hammasi `user_full_rate2s_runaway`); (d) uchta nomlangan trial'ning
  (`b007t001`, `b013t004`, `b010t001`) xom record'lari; (e) 120 trial
  bo'yicha **faqat yaroqlilik** klassifikatsiyasi (§3). Yaroqlilik
  klassifikatsiyasi §17 oynasining joylashuvini aniqlash uchun reducer'ning
  `t_up` ini ichkarida hisoblaydi; **men uni nomlangan uch trial'dan
  boshqasi uchun hisobot qilmayman**, va yacheyka bo'yicha `complete`
  maxrajlarini bermayman.
- **Bu tahlil ataylab yaroqlilikdan nariga o'tmaydi:** downtime,
  `t_up` taqsimoti, VR stavkasi, FR, p-qiymat, risk farqi yoki arm bo'yicha
  effekt bahosi **hisoblanmadi va hisobot qilinmaydi.**

---

## 1. FAKT — validator nima dedi

`python3 -m revix.validate` (`p1-pilot-001.pilot/validate.txt`): **4 xato,
3 ogohlantirish**, *"O'TMADI — bu run ANALIZ QILINMAYDI (§14.6)"*.

| trial | yacheyka | topilma | daraja |
|---|---|---|---|
| `b007t001` | A, P2 | `probe_gap` (492 256 µs > 2P) + driver `complete` | ERROR |
| `b007t001` | A, P2 | `window_outside_hold_complete` (`t_up + W_stab` `T_h` dan 0.391 s keyin) | ERROR |
| `b013t004` | A, P2 | `window_outside_hold_complete` (1.550 s keyin) | ERROR |
| `b010t001` | A, P2 | `action_without_invocation_change` (action `mono_us=19629521595`) | ERROR |
| `b009t000` | no_action, P1 | `probe_gap` 511 838 µs, disposition `censored` | WARNING (to'g'ri) |
| `b007t001`, `b013t004` | — | `disposition_cross_check`: driver `complete`, reducer `censored` (`probe_gap` / `window_past_pressure`) | WARNING |

Run'ning boshqa holati (FAKT, launcher/marker'lar): 120/120 `trial_end`,
`git_commit 4cbd1c6`, `git_dirty false`, seed 20261006, `schedule_digest
69ae399e…cb2dc` (`14` §13.2 dagi bilan bir xil), `preregistration/v1.12`
(`ccb6186e…`), `generator_window.lead_s 2.57`; `boot_id`, pid1 `653523`,
`real − mono` siljishi (`1791095870210148` oldin ham, keyin ham),
`oom_kill 0` o'zgarmagan; `clock-watch.log` da `|Δreal − Δmono|` ≤ 3 µs.

---

## 2. Savol 1 — driver'ning `complete` i qayerdan keladi

### 2.1 FAKT — kod

- `schedule.explain_disposition(TrialFacts)` — `DISPOSITION_RULES` jadvali,
  birinchi mos qoida yutadi: `harness_error` → `guard_fired` →
  `unsolicited_kill` / `foreign_oom_kill` / `bystander_lost_contract` →
  `washout_timed_out` → **`probe_gap_exceeded`** → **`horizon_ended_down`**
  → `measured` (= `complete`).
- `TrialFacts` da **sakkizta** fakt bor; ular orasida **§17 oynasining
  hold ichida bo'lishi haqida fakt YO'Q** (`revix/schedule.py`,
  `class TrialFacts`).
- `driver._collect_facts`: `probe_gap_exceeded = prober_state not in
  ("active",)` — ya'ni **prober jarayoni horizon'da tirik emasligi**, probe
  qatorlaridagi haqiqiy uzilish EMAS. Docstring'ning o'zi:
  *"Driver probe QATORLARINI KO'RMAYDI … `reduce.probe_gaps` haqiqiy
  uzilishlarni AVTORITET ravishda topadi va `derive_disposition` ni
  `censored` ga olib keladi — ikki yo'l bir-birini qoplaydi."*
- Shartnoma (`04` §8.1, interim qoida, v1.2): *"Avtoritet — driver'ning
  `trial_end.disposition` i"*; *"`reduce.derive_disposition()` —
  kross-tekshiruv, avtoritet emas"*; *"Kelishmovchilik validator topilmasi
  sifatida chiqadi"*.

### 2.2 FAKT — ikki trial'ning xom record'lari (`trial_begin` dan sekundlar)

**`b007t001` (A, P2, blokdagi o'rni 1):** `trial_end.facts` — hammasi
`false`, `matched_rules ["measured"]`, prober va SUT horizon'da `active`.
Probe uzilishi **baseline ichida, bosimdan OLDIN** (generator 17.43 s da
boshlanadi): SUT probe'lari 8.191, 8.291, 8.391 s da `rt_timeout`, keyingi
probe 8.884 s da; prober `probe_overrun late_us 391959` yozgan (8.884 s).
Ya'ni uzilish = 8.391 → 8.884 s = **492 256 µs**. Injeksiya 23.001 s,
restart action 23.002 s, `actor_signal` (yangi invocation `active`)
25.351 s; validator/reducer `t_up` = **25.391 s**; `T_h` = 33.0 s ⇒
`25.391 + 8.0 = 33.391 > 33.0` (**0.391 s**).

**`b013t004` (A, P2, o'rni 4):** facts hammasi `false`, `["measured"]`.
Probe uzilishi yo'q. Injeksiya 23.065 s, action 23.066 s, `actor_signal`
26.342 s; `t_up` = **26.550 s** ⇒ `34.550 > 33.0` (**1.550 s**).

### 2.3 NATIJA — muzlatilgan matn nima deydi

- §4: *"**Probe uzilishi > 2×P** → trial `censored`, **`failed` emas**."*
- §12 jadvali: `censored` — *"probe uzilishi >2×P, yoki horizon down
  holatda tugadi"*.
- §14.6(4): *"trial ichida probe uzilishi > 2×P yo'q (aks holda trial
  `censored`)"*; va *"Validatsiyadan o'tmagan run analiz qilinmaydi."*
- §17.4(1): *"Oynasi hold ichida bo'lmagan trial §4 ning kattaligini
  O'LCHAMAGAN. U `complete` + `VR = false` deb yozilMAYDI"*; §17.4(2):
  `window_past_pressure` uchun *"`disposition` ikkalasida ham
  **`censored`**"*.
- §17.4(5): *"har `complete` trial uchun `t_up + W_stab_pilot ≤ T_h`
  **bajarilgan bo'lishi shart**. Bajarilmagan bo'lsa va trial `complete`
  deb yozilgan bo'lsa — bu **validator xatosi**, jimgina o'tkazilmaydi."*

Qo'llanishi: `b007t001` ikki sabab bilan, `b013t004` bitta sabab bilan
§4/§12/§17.4 bo'yicha `censored` bo'lishi kerak edi; ular `complete` deb
yozilgan, va §14.6(4) va §17.4(5) aynan bu holatni **validator xatosi**
deb belgilaydi.

### 2.4 Hukm: **DRIVER NUQSONI** (validator to'g'ri ishlagan)

- **Yo'q fakt:** §17.4 ning oyna sharti `TrialFacts` da umuman ifodalanmagan
  — driver `t_up` ni hisoblamaydi, demak `window_past_pressure` ni hech
  qachon `censored` qila olmaydi. §17.4(2) bu qiymatni `disposition` ga
  qo'yadi, `disposition` esa (shartnoma bo'yicha) driver'niki.
- **Noto'g'ri fakt:** `probe_gap_exceeded` §4 ning ta'rifini (probe
  qatorlari orasidagi > 2P) emas, prober jarayonining horizon'dagi holatini
  o'lchaydi. `b007t001` da prober tirik edi, demak fakt `false`.
- **Validator noto'g'ri ishlamadi:** u §14.6(4) va §17.4(5) ni so'zma-so'z
  bajardi, va reducer xuddi shu ikki trial'ni mustaqil ravishda `censored`
  (`probe_gap`, `window_past_pressure`) deb chiqardi.
- **Muzlatilgan matnda haqiqiy noaniqlik bormi?** Pre-registration'ning
  o'zida — **yo'q**: §4, §12, §14.6(4), §17.4(2), (5) bir xil narsani
  aytadi. Noaniqlik **implementatsiya shartnomasida** (`04` §8.1): u
  disposition avtoritetini driver'ga beradi, lekin driver'dan §4 ning
  probe faktini va §17.4 ning oyna faktini hisoblashni talab qilmaydi —
  `_collect_facts` ning docstring'i ikkalasini reducer'ga qoldiradi. Bu
  "ikki yo'l bir-birini qoplaydi" taxmini §17.4(5) ning *"`complete` deb
  yozilgan bo'lsa — validator xatosi"* qoidasi bilan **birga yashay
  olmaydi**: qoplash reducer'da bo'ladi, rad etish esa run darajasida.
- **TALQIN:** bu klass `14` dagi smoke'larda ko'rinmagan, chunki 25 ta
  smoke trial'ning birortasida ham `complete` + oyna/uzilish kombinatsiyasi
  bo'lmagan (validator 0 xato bergan) — `P2` da kech `t_up` bilan tugagan
  `A` trial'i smoke'da `complete` bo'lmagan.

---

## 3. Savol 2 — `b010t001` da nima bo'ldi

### 3.1 FAKT — timeline (A, P2, o'rni 1; `trial_begin` = 19 606 498 539 µs)

| s | hodisa |
|---|---|
| 23.022 | `fault_inject` (`OK armed=exit`) |
| 23.023 | SUT invocation `8bafb3bc` `failed` (`ActiveExitTimestamp` = 23.023) |
| 23.145 | systemd restart → yangi invocation **`ca2a0c11`**, `NRestarts 1`, holat `activating/start` |
| 23.023 | **action 1** (`mono_us` = `t_issue` = 23.023, invocation `ca2a0c11`) |
| 23.146 → 27.134 | `ca2a0c11` **`activating/start` da qoladi — hech qachon `active` bo'lmaydi** |
| 27.133 | **guard** `user_full_rate2s_runaway` (0.98055 / 0.98, `kill_subtree`) |
| 27.134–27.135 | `ca2a0c11` `failed`, `Result signal` (`ExecMainExitTimestamp` 27.134, `ExecMainStatus 9`); bystander `failed/signal` |
| 27.396 | systemd restart → **`c50262b1`**, `NRestarts 2` |
| 23.023 | **action 2** (`mono_us` = `t_issue` = **23.023** — action 1 bilan BIR XIL; `t_begin` 27.135, `t_exec` 27.395) |
| 27.420 | `c50262b1` `active`, `actor_signal` |
| 41.1 | `trial_end`: **`aborted_guard`** (`guard_fired`, `unsolicited_kill`, `bystander_lost_contract`) |

### 3.2 Sabab (FAKT, kod)

`driver._note_unit_state` chiqayotgan invocation'ning exit vaqtini
`active_exit_ts_mono_us` dan **birinchi navbatda** oladi
(`… or exec_main_exit_ts_mono_us or recv_mono_us`). systemd
`ActiveExitTimestamp` ni faqat unit **`active` dan chiqqanda** yangilaydi;
`ca2a0c11` hech qachon `active` bo'lmagani uchun maydon eski qiymatda
(23.023) qoldi, holbuki o'sha record'da `exec_main_exit_ts_mono_us` =
27.134 bor edi. Shuning uchun action 2 ning `t_issue` i action 1 niki bilan
**teng** bo'lib qoldi.

`validate.check_actions` action `k` uchun invocation o'zgarishini
`(a_k.mono_us, a_{k+1}.mono_us]` oynasida qidiradi. Ikki action'ning
`mono_us` i teng ⇒ action 1 ning oynasi **bo'sh** ⇒ xato. Action 2 ning
oynasi (`(23.023, horizon]`) ikkala o'zgarishni ham o'z ichiga oladi.

### 3.3 Hukm

- Bu **guard kill → systemd restart** yo'li (`14` §13.3 smoke-24 dagidek),
  lekin bitta farq bilan: guard SUT'ni **start paytida** (`activating`)
  o'ldirdi. Poyga emas; deterministik timestamp nuqsoni.
- **Driver nuqsoni**: `t_issue` uchun eskirgan `ActiveExitTimestamp`.
- **Validator qoidasining mosligi:** §14.6(6) *"har `action` uchun mos
  invocation o'zgarishi yoki ochiq `action_defer`"* **mazmunan bajarilgan**
  — ikki action, ikki invocation o'zgarishi (`ca2a0c11`, `c50262b1`).
  Validator xatosi buzilgan record vaqtining natijasi (ikki action bir xil
  `mono_us` bilan), ya'ni rad etish **to'g'ri yo'nalishda** (noto'g'ri
  yozilgan record), lekin u haqiqiy "ta'sirsiz action" ni ko'rsatmaydi.
- Trial `aborted_guard` — §12 bo'yicha birlamchi analizdan chiqariladi;
  xato disposition'ga ta'sir qilmaydi, faqat run'ni yiqitadi.

---

## 4. Savol 3 — qolgan trial'lar yaroqlilik bo'yicha izchilmi

**Usul (FAKT):** `datasets/smoke-tools/p1_validity.py` — validator'ning
o'zi ishlatadigan funksiyalar (`validate.reducer_view` SUT bo'yicha,
`reduce.split_trials`, `check_probe_gaps` ning `> 2P` sharti,
`validate._trial_window` → `classify_window_containment`), run katalogi
faqat o'qiladi. Ikki shart **driver `complete` deb yozgan har trial'ga**
qo'llandi.

| yacheyka | `complete` + probe uzilishi > 2P | `complete` + oyna hold'dan tashqarida |
|---|---|---|
| A / P0 | 0 | 0 |
| A / P1 | 0 | 0 |
| **A / P2** | **1** (`b007t001`) | **2** (`b007t001`, `b013t004`) |
| no_action / P0 | 0 | 0 |
| no_action / P1 | 0 | 0 |
| no_action / P2 | 0 | 0 |

- **NATIJA:** yuqoridagi ikki trial'dan boshqa birorta `complete` trial ham bu ikki
  shart bo'yicha noto'g'ri `complete` emas. Oyna holati
  `not_evaluated` bo'lgan `complete` trial **yo'q** (`T_h` hammasida
  yozilgan).
- `complete` bo'lmagan trial'larda probe uzilishi faqat `b009t000` da
  (no_action/P1, `censored`, 30.149 → 30.661 s) — driver uni horizon down
  sababli to'g'ri `censored` qilgan; validator ogohlantirish berdi.
- **Mavjud boshqa yaroqlilik tekshiruvlari** (validator'ning qolgan 30+
  tekshiruvi, jumladan `probe_coverage`, `host_clock_discontinuity`,
  `guest_generation`, `trial_timing`) — **xato yo'q**.
- **CHEKLOV:** `complete` bo'lmagan trial'lar uchun oyna holati bu yerda
  hisobot qilinmaydi (ular `complete` emas, demak §17.4(5) ularga
  qo'llanmaydi; §17.4(4) ning yacheyka jadvali — analiz bosqichining
  hisoboti, bu tahlilning emas).

---

## 5. Savol 4 — variantlar va ularning narxi

### 5.1 Qoidalar (iqtibos)

- §14.6: *"Validatsiyadan o'tmagan run analiz qilinmaydi."* — butun run.
- §14.5(2): *"Derived record'lar alohida fayllarda va raw'dan qayta
  yaratiladi. Raw fayllar derived maydon qo'shish uchun HECH QACHON
  tahrirlanmaydi."*
- §16.10(3): *"Hech qanday P1 natijasi ko'rilgandan keyin
  o'zgartirilMAYDI. Post-hoc o'zgarish **run'ni bekor qiladi**,
  parametrni emas."* — matn **ochiq parametrlar** haqida; harness kodi
  haqida emas, lekin ruhi: ma'lumotdan keyingi o'zgarish run'ni yangi
  run qiladi.
- `DEVELOPMENT.md` §7: *"Agar ma'lumot yig'ilgandan keyin o'zgarish kerak
  bo'lsa — **eski ma'lumot eski ta'riflar ostida qayta hisoblanadi**"*.
- v1.12 0-band presedenti: ma'lumot ko'rilgandan keyingi qaror — oshkora
  e'lon bilan, *"ko'r tanlangan"* da'vosisiz.
- `04` §8.1: driver avtoritet, reducer kross-tekshiruv (interim qoida).

### 5.2 Variantlar

**V-A. Driver tuzatiladi, butun pilot `p1-pilot-002` sifatida qayta
o'tkaziladi** (seed 20261006, yangi katalog; `p1-pilot-001` saqlanadi va
**yaroqsiz** deb belgilanadi, o'chirilmaydi).

- Tuzatish (taklif, bajarilmagan): (1) driver §4 ning probe faktini
  prober oqimidan (yoki `probe.csv` dan) haqiqiy `> 2P` uzilish sifatida
  hisoblaydi; (2) driver §17.4 ning oyna faktini reducer bilan **bir xil**
  funksiya (`build_episodes` → `classify_window_containment`) bilan
  hisoblaydi va `window_past_pressure`/`_horizon` ni `censored` qiladi;
  (3) `t_issue` — chiqayotgan invocation hech qachon `active` bo'lmagan
  bo'lsa `exec_main_exit_ts` / `inactive_exit_ts`; har biri uchun
  regressiya testi va real smoke.
- **Muzlatilgan ta'riflar o'zgarmaydi** — tuzatish §4 va §17.4(2) ni
  **implementatsiya qiladi**. Shuning uchun §16.10(3) ning harfi
  qo'llanmaydi (parametr emas), lekin qayta o'tkazish qarori
  **pilot-001 ning disposition sonlari (orkestrator, yacheyka bo'yicha;
  men, umumiy) ko'rilgandan keyin** qabul qilinadi — **oshkora e'lon
  majburiy** (v1.12 0-band uslubida, yangi amendment v1.13): nima
  ko'rilgan, nega qayta o'tkazilmoqda (yaroqlilik, natija emas), va
  pilot-002 ning qaysi run ekanligi **oldindan** e'lon qilinadi.
- **Narx:** ~1.9 soat (pilot-001 wall 6754 s) + tuzatish va smoke.
  Bir xil seed ⇒ bir xil jadval (`69ae399e…`), bu forking-paths xavfini
  kamaytiradi (tartibni tanlash imkoni yo'q).
- **Bir xil klassning qaytalanish ehtimoli** (faqat §4 dagi yaroqlilik
  sonlaridan): tuzatishsiz — yuqori: `complete` + oyna tashqarida 2/120,
  `complete` + uzilish 1/120, eskirgan `t_issue` 1/120, ya'ni pilot-001 da
  3 trial uchta mustaqil yo'l bilan run'ni yiqitdi; bitta trial ham
  yetarli. Tuzatish bilan bu uch klass **to'g'ri disposition'ga
  aylanadi** (`censored`, `censored`, to'g'ri action vaqti) va validator
  ularni rad etmaydi. **CHEKLOV:** 120 trial'lik birinchi run yangi
  klasslarni ochdi (smoke run'lari ularni ko'rsatmagan) — pilot-002 ham
  hali ko'rilmagan klassni ochishi mumkin; ehtimolini baholab bo'lmaydi.

**V-B. pilot-001 oflayn qayta tasniflanadi** (raw o'zgarmaydi; derived
disposition reducer'dan).

- Reducer allaqachon `(disposition, disposition_source)` ni derived
  faylga yozadi (§16.2(B)); `b007t001` → `censored:probe_gap`,
  `b013t004` → `censored:window_past_pressure`, `b010t001` →
  `aborted_guard` (o'zgarmaydi). Natija §17.4(2) bo'yicha **muzlatilgan
  matn talab qilgan** qiymatlar — bu yerda tanlov erkinligi yo'q.
- **Lekin** run hamon §14.6 ni o'tmaydi: validator raw `trial_end` ga
  qaraydi va `04` §8.1 driver'ni avtoritet qiladi. O'tishi uchun
  (a) validator'ni yoki (b) `04` ning avtoritet qoidasini **ma'lumot
  ko'rilgandan keyin** o'zgartirish kerak (raw'ni tahrirlash §14.5(2)
  bo'yicha taqiqlangan). Bu harness'ni **natija ko'rilgandan keyin**
  o'zgartirish — `DEVELOPMENT.md` §7 ruhida *"eski ma'lumot eski ta'riflar
  ostida"* qayta hisoblanadi (ta'riflar o'zgarmaydi), lekin yaroqlilik
  darvozasi o'zgaradi; amendment (v1.13) va oshkora e'lon majburiy.
  `b010t001` ning action vaqti ham derived yo'lda qayta hisoblanishi yoki
  validator'ning `aborted_guard` trial'larida bir xil `mono_us` li
  action'larga munosabati o'zgartirilishi kerak — bu **qo'shimcha erkinlik
  darajasi**.
- **Narx:** vaqt arzon; ishonchlilik qimmat — reviewer *"run o'z
  darvozasidan o'tmagan, darvoza keyin yumshatilgan"* deydi. Tanlov
  erkinligi kichik (uchta trial, hammasi `A/P2`, qiymatlari §17.4(2) bilan
  belgilangan), lekin nol emas.

**V-C. V-A + V-B birga:** pilot-002 birlamchi; pilot-001 ning oflayn
qayta tasnifi **sezgirlik/izchillik** tekshiruvi sifatida (oldindan e'lon
qilinadi, birlamchi emas). Narx: V-A niki; foyda — ikki run'ning
yaroqlilik klasslari solishtiriladi (natijalar emas).

**V-D. pilot-001 dan uchta trial'ni chiqarib tahlil qilish** — §14.6
run darajasidagi darvoza; trial'ni tanlab olib tashlash muzlatilgan
qoidada **yo'q**. Tavsiya qilinmaydi.

### 5.3 TALQIN (qaror emas)

V-A muzlatilgan ta'riflarga ham, §14.6 darvozasiga ham tegmaydigan yagona
variant; uning narxi — vaqt va qayta o'tkazish qarorining oshkora e'loni.
V-B tezroq, lekin darvozani ma'lumotdan keyin o'zgartiradi. Ikkalasida
ham uchala driver nuqsoni (§2.4, §3.3) **tuzatilishi kerak** — aks holda
keyingi har run xuddi shu klasslarga duch keladi.

---

## 6. CHEKLOV

- `b007t001` dagi baseline ichidagi uzilishning (8.19–8.88 s, prober 0.39 s
  kechikkan, SUT 3 × `rt_timeout`, generator hali ishlamagan) **sababi
  o'lchanmagan**. GIPOTEZA: host/VM darajasidagi qisqa to'xtash; soat
  tekshiruvi (`≤ 3 µs`) 1 s dan qisqa muzlashni ko'rmaydi (v1.12 4.4).
- Driver nuqsonlari kod o'qish va xom record'dan aniqlandi; tuzatish
  yozilmadi va sinalmadi.
- Yaroqlilik klassifikatsiyasi reducer'ning `t_up` iga tayanadi (validator
  ham shunga tayanadi); `t_up` ning o'zi bu yerda baholanmadi.
- `driver.json` dagi umumiy disposition sonlarini ko'rganim (§0) — oshkora.

## 7. Fayllar

- `datasets/smoke-tools/p1_validity.py` — yaroqlilik klassifikatsiyasi
  skripti (faqat o'qiydi). Uning to'liq chiqishi (`validity.json`, har
  trial uchun `t_up`) **commit qilinmadi** — natija bilan bog'liq ma'lumot.
- Pilot run va uning `validate.txt` i guest'da: `~/revix-runs/p1-pilot-001`,
  `~/revix-runs/p1-pilot-001.pilot/`.
