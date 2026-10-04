# 18 — `p1-pilot-002`: VR implementatsiyasining auditi (xom qatorlar muzlatilgan ta'rifga qarshi)

Bu hujjat `p1-pilot-002` ning birinchi real-ma'lumotli reduksiyasida
(`~/revix-runs/p1-pilot-002.derived3/`) arm `A` ning `vr` qiymatlari
**o'lchovmi yoki implementatsiya artefaktimi** degan savolga javob beradi.
**Faqat mexanika.** Kod, test va muzlatilgan matn **o'zgartirilmadi**;
birorta trial, bosim yoki pytest ishga tushirilmadi. Hujjat tadqiqot
gipotezalari (H1, H2) haqida **hech qanday xulosa chiqarmaydi**.

Belgilar: **FAKT** — xom record'dan, koddan yoki muzlatilgan matndan
o'qildi (manba ko'rsatilgan); **GIPOTEZA** — o'lchanmagan taxmin;
**NATIJA** — muzlatilgan qoidaning FAKT'larga qo'llanishi; **TALQIN** —
xulosa; **CHEKLOV** — ayta olmaydigan narsa.

**Branch:** `agent/vr-audit` (`main` `5a6ecb5` dan; `PREREGISTRATION.md`
v1.14, sha256 `06f1d52c…1810`).
**Ma'lumot:** `~/revix-runs/p1-pilot-002` (faqat o'qish) va
`~/revix-runs/p1-pilot-002.derived3/` — ikkalasi guest'da
`~/vraudit-scratch/{raw,derived3}/` ga **nusxalandi**, tahlil faqat
nusxada. Nusxa xomga bayt-bayt teng (`probe.csv` sha256 `f0e1a736…a8b`,
`events.jsonl` `686014f9…2b7` — ikkala joyda bir xil). Run va derived
kataloglariga **hech narsa yozilmadi**.
**Qulf:** ish paytida `~/.revix-exclusive` boshqa agentda edi
(`iso-dash gui-build`); bu audit faqat arxivlangan nusxa ustida yengil,
faqat-o'qish Python ishlatdi.
**Yordamchi:** `datasets/smoke-tools/vr_audit_rows.py` (faqat o'qiydi,
stdout'ga yozadi; §10).

---

## 0. OSHKORA E'LON — kim nimani ko'rdi, trial'lar qanday tanlandi

- **Orkestrator** reduksiya chiqishini va **har `(arm × pressure)`
  yacheykasi bo'yicha tally'larni** ko'rgan (brief'dagi o'z bayoni: `A/P0`
  da 20/20 `vr = None`; `A/P1`, `A/P2` da aniqlangan `vr` ning hammasi
  `False`, `contract_fail` 32 dan 29 da). Bu hujjat o'sha tally'larni
  **takrorlamaydi va kengaytirmaydi**.
- **Men ko'rgan narsa:**
  1. `trials.jsonl` va `episodes.jsonl` ning sxemasi; birinchi qator
     sifatida `b000t000` (`no_action/P1`) ning to'liq record'i.
  2. `A/P0` ning **20 trial'i** uchun injeksiya atrofidagi ketma-ket
     buzilgan probe soni, reducer'ning `vr_reason`'i va disposition'i
     (`p0` buyrug'i); va **uch** trial'ning xom qatorlari: `b000t002`
     (blok tartibida birinchi `no_episode` `A/P0` trial'i), `b003t001`
     (3-blokning `A/P0` trial'i — 3-blok pastdagi tanlovda ham bor), va
     `b001t002` (blok tartibida birinchi epizodli `A/P0` trial'i).
  3. **`contract_fail` trial'lari — inspeksiyadan OLDIN `trial_id` bo'yicha
     tanlandi.** Faqat `trial_begin` dagi `(arm, pressure_band, block)`
     ko'rilgan holda qoida qo'yildi: `A/P1` dan 3- va 13-blok, `A/P2` dan
     7- va 17-blok ⇒ **`b003t004`, `b013t000`, `b007t001`, `b017t001`**;
     zaxira qoidasi: tanlangan trial'da `contract_fail` bo'lmasa, o'sha
     yacheykaning keyingi bloki olinadi. `b007t001` da `contract_fail`
     **yo'q** chiqdi (`r_ref_unavailable`, oynada 0 buzilish) ⇒ zaxira
     **`b008t005`** (`A/P2`). `b007t001` savol 2/4 da dalil sifatida
     qoldi. **CHEKLOV:** tanlov qoidasi va zaxira qoidasi faqat menda
     yozilgan edi; ularning inspeksiyadan oldin qo'yilganini tasdiqlovchi
     tashqi yozuv **yo'q**.
  4. Arm `A` ning `contract_fail` bilan yakunlangan **29 oynasi** —
     faqat mexanik ustunlar (buzilgan probe soni, eng uzun ketma-ket seriya,
     uzilish va `probe_overrun` soni; `overlap` buyrug'i). Ular uchun xom
     qatorlar to'liq chop etilmadi (nomlangan to'rttadan tashqari).
  5. Butun run bo'yicha SUT probe'lari: `outcome` sonlari, baseline
     oynalaridagi buzilishlar, `T_rt`/`T_conn` dan oshgan `ok` qatorlar,
     `cgroup_events` shakli.
  6. Mexanik `vr = None` sabablari yacheyka bo'yicha (brief buni
     ruxsat etadi): §3.1.
- **Tasodifan ko'rganim, va hisobotga KIRITILMAGANI:**
  (a) `analysis.json` ning `warnings` ro'yxati va `primary` bo'limi
  chop etildi — undagi `A` yacheykalari bo'yicha `k/n` va CI'ni ko'rdim;
  ular bu yerda **berilmaydi** (orkestratorda bor). (b) Tadqiqot paytida
  yordamchi skriptning birinchi versiyasi **`b007t001` va `b001t002`** uchun
  `progress_counter` bilan 5-bandni qo'shib hisoblangan `vr` qiymatini chop
  etdi. Bu qiymat **berilmaydi** — audit "haqiqiy" qiymatni aytmaydi;
  commit qilingan skript endi bu qiymatni chop etmaydi.
- **Hisoblamadim:** `P(VR)` arm/band bo'yicha, risk farqi, p-qiymat,
  downtime yoki time-to-VR taqsimoti, effekt bahosi; `pressure.jsonl`,
  `psi.csv`.

---

## 1. Qisqa hukm

| # | savol | hukm |
|---|---|---|
| 1 | `A/P0` dagi `no_episode` | **dizaynning o'z xossasi** (§3 detektori `D_f = 300 ms` dan qisqa uzilishni ko'rmaydi). Lekin bu §20.3 ning *"`no_episode` = injeksiya ishlamadi"* asosiga **ZID** — §2.5 |
| 2 | `r_ref_unavailable` | **defekt** — reduksiya zanjirida: `progress` maydoni CSV round trip'ida tushib qoldi; 120/120 trial'da `R_ref = None`. Ta'rif ham, ma'lumot ham sabab emas |
| 3 | oynadagi `contract_fail` | **muzlatilgan matnga sodiq** (haqiqiy §2(b) buzilishi: SUT `T_rt` ichida javob bermadi); lekin 29 dan 8 oynada hukm faqat `k_f` dan qisqa seriyalarga tayanadi — **dizaynning o'z xossasi** (§3 va §4.2 asimmetriyasi) |
| 4 | reducer VR §4 ga sodiqmi | nomlangan 7 trial'da mustaqil qayta hisob bilan **to'liq mos**; `evaluate_vr`/`build_episodes` da defekt topilmadi. `vr = None (r_ref_unavailable)` — savol 2 defektining oqibati, `evaluate_vr` niki emas |
| 5 | prober shovqini confound sifatida | bu run'da **`contract_fail` ni hech bir oynada hal qilmaydi** (0/29); `rt_timeout` larning sababi qatorlardan **aniqlab bo'lmaydi** |

---

## 2. Savol 1 — `A/P0` dagi `no_episode`

### 2.1 FAKT — muzlatilgan qoidalar

- §3 (`PREREGISTRATION.md:3476`): *"`k_f = 3` → `D_f = 300 ms`. Sabab:
  bitta probe'dagi shovqinni (scheduling jitter, socket backlog) failure
  deb hisoblamaslik."* `F_probe` — *"contract `k_f` marta ketma-ket
  buzildi"*.
- §4 (`:3502`): VR **epizod `E` uchun** ta'riflanadi; `t_up` *"`E` ning
  oxirgi action'idan keyingi birinchi contract'dan o'tgan probe"*.
- §16.2(B) (`:4532`) aniqlanmagan failure haqida **gapirmaydi** — u
  `down_at_horizon` (kuzatilgan `false`) va `probe_gap` (kuzatilmagan)
  ni ajratadi. Epizodsiz trial'ni §20.3 (`:6100`) hal qiladi: *"Epizod
  bo'lmasa §4 ning predikati instansiyalanmaydi … `None` — halol qiymat"*,
  binar maxrajdan **va** KM/log-rank'dan chiqariladi.
- §20.3 (`:6139`) ning asosi: *"SUT o'ldirilsa contract **buzilishi
  shart** (socket accept qilmaydi). Demak muzlatilgan P1 dizaynida
  `no_episode` **injeksiya ishlamaganini** bildiradi"*; va (`:6147`)
  noldan farqli daraja *"fault injektori o'z ishini bajarmayotganini
  bildiradi va **pilotni gate qiladi**"*.

### 2.2 FAKT — kod

`reduce.find_failure_onsets` (`revix/reduce.py:1340`) faqat uzunligi
`≥ k_f` bo'lgan buzilish seriyasini onset deb oladi (trace oxirida uzilgan
seriyadan tashqari); `build_episodes` (`:1425`) faqat shu onset'lardan
epizod quradi; epizod bo'lmasa `reduce_trial` `vr_reason = "no_episode"`
yozadi (`:2032`–`:2034`).

### 2.3 FAKT — xom qatorlar (SUT probe'lari; vaqt injeksiyaning `mono_us_after_call` idan)

**`b000t002` (`A/P0`, `no_episode`):**

| probe | vaqt | outcome |
|---|---|---|
| seq 230 | −52.1 ms | `ok` (pid 49667, inv `a9ee1a5d`) |
| seq 231 | +47.9 ms | `conn_refused` (`ECONNREFUSED`), `fail_streak` 1 |
| seq 232 | +147.9 ms | `conn_refused`, `fail_streak` 2 |
| seq 233 | +247.9 ms | `ok`, **yangi** pid 49679, inv `e6c3f286`, `restart_seen = 1` |

`unit_state`: `ActiveExit` +0.9 ms, `Result=exit-code`; `auto-restart`
taymeri `NRestarts` 0→1 bilan **+162.3 ms** da; `sub_state=start`
+163.9 ms; `active` (`ActiveEnter`) **+198.5 ms**. `action`: `t_exec`
+162.7 ms.

**`b003t001` (`A/P0`, `no_episode`):** seq 231 (+51.7 ms) va 232
(+151.7 ms) `conn_refused`, seq 233 (+251.6 ms) `ok`, yangi invocation
`e31da3f0`, `restart_seen = 1`. `ActiveExit` +1.2 ms → taymer +211.9 ms →
`ActiveEnter` **+242.0 ms**.

**`b001t002` (`A/P0`, epizod bor, `r_ref_unavailable`):** seq 231–233
(+47.2, +147.2, +247.2 ms) — **uchta** `conn_refused`, seq 234
(+347.2 ms) `ok`, yangi invocation `770291ec`. `ActiveExit` +1.0 ms →
taymer **+299.5 ms** → `ActiveEnter` **+321.3 ms**.

**20 ta `A/P0` trial bo'yicha (`p0` buyrug'i):** injeksiyadan keyingi
birinchi buzilish seriyasi **10 trial'da aynan 2** ta `conn_refused` —
**hammasi** `no_episode`; **10 trial'da 3 yoki 4** ta — **hammasi**
epizodli (`r_ref_unavailable`). Istisno yo'q (`(seriya ≥ k_f, vr_reason)`
→ `(False, no_episode): 10`, `(True, r_ref_unavailable): 10`). Injeksiyadan
oldin `≥ k_f` seriya hech birida yo'q. Har 20 trial'da `fault_inject`
`sut_ack = "OK armed=exit"`, `action` (systemd restart) va probe ko'rgan
yangi invocation bor.

### 2.4 NATIJA

1. Injektor **ishladi**: SUT chiqdi (`Result=exit-code`), contract
   **buzildi** (`conn_refused`), systemd qayta ishga tushirdi, prober yangi
   invocation'ni ko'rdi. `no_episode` ning sababi — uzilishning **2 probe**
   (`< k_f = 3`) davom etgani, ya'ni `D_f = 300 ms` dan qisqaligi.
   **Muzlatilgan detektor bu uzilishni ko'ra olmaydi.**
2. Uzilish uzunligi asosan **`t_start` emas**, systemd'ning restart
   taymeri kechikishi bilan belgilanadi: nomlangan uch trial'da
   `start → active` 20–35 ms, lekin `RestartSec = 100 ms` taymeri
   +162, +212, +300 ms da ishladi. Probe grid'ining fazasi (birinchi
   buzilgan probe injeksiyadan ~+48–52 ms keyin) bilan birga, bu 2 yoki 3
   buzilgan probe'ni tanlaydi. (Uch trial — dalil; men `A/P0` uchun
   uzilish taqsimotini **bermayman**.)
3. Demak `A/P0` ning `no_episode` qismi uchun pre-registered VR
   **konstruksiya bo'yicha aniqlanmagan** — bu **dizayn xossasi, bug
   emas**: §3 detektori va §4 predikati to'g'ri ishlaydi, faqat ularning
   kesishmasi `RestartSec = 100 ms` dagi tez restart'ni "epizod" deb
   tanimaydi.

### 2.5 🔴 ZIDDIYAT — §20.3 ning asosi bu ma'lumotda bajarilmaydi

§20.3 `no_episode` ni *"injeksiya ishlamadi — trial nuqsoni"* deb talqin
qiladi va noldan farqli darajani **pilot gate**'i qiladi. Yuqoridagi
FAKT'lar bu talqinning **asosini** (*"SUT o'ldirilsa contract buzilishi
shart"* ⇒ epizod) inkor etadi: contract buzildi, lekin `k_f` dan kam
probe davomida. **Asos noto'g'ri, gate qoidasi esa matnda turibdi.**
Qoidaning so'zma-so'z qo'llanishi `p1-pilot-002` ni gate qiladi (`A/P0`
da `no_episode` 10). Bu hujjat buni **hal qilmaydi** — bu egasining
qarori; men faqat ziddiyatni qayd etaman.

### 2.6 TALQIN — `P(VR | P0)` endi nimani anglatadi, va trend testiga oqibati

- **Hozirgi reduksiyada** `A/P0` da binar maxraj **bo'sh**: 10 trial
  `no_episode` (dizayn), 10 trial `r_ref_unavailable` (savol 2 defekti).
  Shuning uchun `analysis.json` §10.1 trend testini hisoblanmaydi deb
  ogohlantiradi.
- **Savol 2 defekti tuzatilgan taqdirda ham**, §20.2/§20.3 bo'yicha
  `P(VR | P0)` = `P(VR | P0, crash uzilishi ≥ k_f probe)` — ya'ni faqat
  restart taymeri sekinroq ishlagan `P0` trial'lari ustidagi **shartli**
  kattalik. Maxrajga kirish **natijaga yaqin o'zgaruvchi** (restart
  kechikishi) bilan tanlanadi.
- **Mexanik asimmetriya (FAKT, §4.4 dagi sonlar):** `P0` da epizod faqat
  crash uzilishidan kelib chiqadi; `P1`/`P2` da esa epizod pressure
  ostidagi `rt_timeout` seriyasidan ham paydo bo'ladi — arm `A` dagi
  epizodli trial'larning **16 tasida** birinchi epizod onset'i
  **injeksiyadan OLDIN**, **1 tasida** (`b003t004`) crash 2 probe bilan
  ko'rinmay qolib, epizod keyingi `rt_timeout` seriyasidan. Ya'ni
  trend'ning uch strata'sida **maxrajga kirish qoidasi mexanik jihatdan
  bir xil emas** — §20.7(a) aynan *"trend strataları bo'ylab turli
  kattaliklar"* ni bias deb ataydi. Bu yo'nalish yoki kattalik haqida
  **hech narsa demaydi**; men uni baholamayman.

**Hukm (savol 1):** **dizaynning o'z xossasi.** `no_episode` — muzlatilgan
`k_f = 3` detektorining `RestartSec = 100 ms` dagi qisqa uzilishga
ko'rligi; implementatsiya ta'rifni to'g'ri bajaradi. Shu bilan birga
§20.3 ning *"injektor ishlamadi"* asosi ma'lumot bilan inkor etiladi va
uning gate qoidasi ochiq ziddiyat sifatida qoladi (§2.5).

---

## 3. Savol 2 — `r_ref_unavailable`

### 3.1 FAKT — ko'lam

- `trials.jsonl`: **120/120** trial'da `r_ref = null`,
  `r_ref_status = "insufficient_probes"`, `r_ref_detail = {"n": 0,
  "source": "pre_fault_probes"}` — ya'ni `baseline_window` yo'li ham,
  zaxira yo'l ham **nol** probe topdi.
- Mexanik `vr = None` sabablari (arm `A`): `A/P0` — `no_episode` 10,
  `r_ref_unavailable` 10; `A/P1` — `r_ref_unavailable` 6; `A/P2` —
  `r_ref_unavailable` 2. `no_action` da `vr = None` yo'q.
- `r_ref_unavailable` faqat **monoton invalidator ishlamagan** epizodda
  ko'rinadi: `evaluate_vr` avval monoton invalidator'larni tekshiradi
  (`reduce.py:1061`), keyin `r_ref` ni (`:1072`). Shuning uchun bu
  reduksiyada **`vr = True` ga yetib bo'lmaydi**: har epizod yo
  `invalidated`, yo `r_ref_unavailable`.

### 3.2 FAKT — qoida va uning kirishi

- §4.5 (`PREREGISTRATION.md:3508`): *"oyna throughput'i ≥ `θ · R_ref`,
  `R_ref` = shu trial'ning fault'dan oldingi throughput'i"*; §9.4
  jadvali: *"`R_ref` baseline 10 s"* (`trial_begin` dan 5.0–15.0 s).
- `reduce.reference_throughput` (`reduce.py:850`) `baseline_window`
  oynasida `window_throughput` (`:762`) ni chaqiradi; u faqat
  `p.passed and p.progress is not None` probe'larni oladi.
- `Probe.progress` = `rec.get("progress")` (`reduce.py:507`). Prober esa
  ustunni **`progress_counter`** deb yozadi (`revix/prober.py:153`,
  `PROBE_FIELDS`), va §14.4 aynan shu nomni muzlatgan. Kontrakt `04` §4.5
  (normativ) moslashtirishni **reduksiya kirishida** talab qiladi:
  `driver.normalise_probe_row` (`revix/driver.py:1021`) — uning izohi
  oqibatni oldindan yozgan: *"`R_ref` yo'q → `vr=None,
  reason="r_ref_unavailable"` HAR TRIAL uchun"*.

### 3.3 FAKT — uch ko'rinishning taqqoslanishi (`rref` buyrug'i)

| ko'rinish | `ok` qator | `progress` o'qiladigan | `R_ref` holati (120 trial) |
|---|---|---|---|
| xom `probe.csv` | — | ustun yo'q (`progress_counter` bor) | — |
| **validator**: `validate.load_run_dir` → `reducer_view` (xotirada) | 37 052 | **37 052** | `ok`, manba `baseline_window`: **120** |
| **reducer CLI kirishi**: `view-probe.csv` → `reduce.load_probe_csv` | 37 052 | **0** | `insufficient_probes`: **120** |

- Ikki ko'rinishda probe soni bir xil (48 973 SUT qatori); reducer o'qiydigan
  maydonlar (`outcome`, `invocation_id_seen`, `mono_us_send`, `trial_id`,
  `seq`, `progress_counter`) bo'yicha **farq 0**; yagona farq —
  `progress` (37 054 qator: barcha `ok` + `progress_counter` li 2
  `no_progress`).
- **Mexanizm:** `validate.load_run_dir` har probe'ga `_adapt_probe_row`
  orqali `progress` ni **qo'shadi** (`revix/validate.py:2569`–`:2578`,
  `:2652`–`:2653`). `reducer_view` (`:2335`) faqat qator filtrlaydi
  (SUT `unit_state`, `target == "sut"`), **maydon tashlamaydi**.
  `pilot_reduce.py` esa ko'rinishni
  `csv.DictWriter(f, fieldnames=list(PROBE_FIELDS), extrasaction="ignore")`
  bilan yozadi (28-qator; fayl sha256 `88822f7e…b304`) — `progress`
  `PROBE_FIELDS` da **yo'q**, demak u **jimgina tashlanadi**; so'ng
  `python -m revix.reduce --probe-csv` `RawRun.load` → `load_probe_csv`
  yo'li bilan o'qiydi, u adapter qo'llamaydi.
- **Validator buni ko'rmadi:** `check_probe_fields` ning
  `probe_progress_unreadable` tekshiruvi (`validate.py:2180`, aynan shu
  holat uchun yozilgan) validator'ning **o'z** moslashtirilgan
  ko'rinishida ishlaydi — reducer'ga berilgan CSV'da emas.
- `baseline_window.throughput = null` (120/120) — bu **dizayn**: driver
  throughput hisoblamaydi (`driver.py:2824`–`:2829`), reducer uni o'zi
  hisoblaydi.
- Baseline oynalarida 16 ta `> 2P` uzilish (12 trial) bor, lekin
  `R_ref` = `Δprogress/Δt` oyna chetlaridan; validator ko'rinishida 120/120
  `ok` — ya'ni uzilishlar ham, qoplama qoidasi ham sabab **emas**.

### 3.4 NATIJA — oqibatlar (qiymat emas, artefakt turi)

Bitta tushib qolgan maydon quyidagilarning **hammasini** buzadi
(hammasi `R_ref` ga yoki `vr = True` ga bog'liq):

1. §4.5 band 5 — hech bir trial'da baholanmaydi; `vr = True` erishib
   bo'lmaydigan;
2. §6.1 `D_eff` — 120/120 da `d_eff_status = "r_ref_unavailable"`
   (u §11(b) davom etish mezonining kirishi);
3. time-to-VR — `vr = True` yo'q ⇒ har kuzatuv horizon'da censored;
   `analysis.json` KM kvantillari, log-rank va RMST farqini degenerat deb
   ogohlantiradi (`n_uncensored = 0`);
4. §4 sensitivity sweep (`sweep.jsonl`) — har katakda `R_ref` yo'q.

Bularning **qiymati** haqida hech narsa demayman; faqat ular hozirgi
ko'rinishda **o'lchov emas, kirish artefakti**.

**Hukm (savol 2):** **defekt** — reduksiya zanjirida (`pilot_reduce.py`
ning CSV round trip'i `progress` ni tashladi; `revix.reduce` CLI yo'lida
kontrakt `04` §4.5 adapteri yo'q). Ma'lumotda sabab yo'q (xomda
`progress_counter` 37 052/37 052 `ok` qatorda bor), ta'rifda ham yo'q.
Validator va reducer **bir xil ko'rinishni ko'rmagan**.

---

## 4. Savol 3 — oynadagi `contract_fail`

### 4.1 FAKT — "contract failure" qoidasi va reducer

- §2 (`PREREGISTRATION.md:3459`–`:3460`): (a) socket `T_conn = 50 ms`
  ichida accept; (b) *"to'g'ri formatdagi javob `T_rt` ichida keladi"*,
  `T_rt = 50 ms`; (c) `progress_counter` oldingi probe'dan qat'iy katta.
- §4.2 (`:3505`): *"oynadagi **har bir** probe contract'dan o'tadi"*;
  invalidator `contract_fail`.
- Prober: `T_rt` — ulanish tugagan lahzadan absolut deadline
  (`prober.py:487`); `recv` vaqt tugasa `rt_timeout`,
  `err_reason = "rt_deadline"` (`:494`–`:499`); yangi invocation'da
  `progress` kamayishi `no_progress` **deyilmaydi** (`restart_seen`,
  docstring 4-qoida). Reducer: `Probe.passed ⇔ outcome == "ok"`;
  `evaluate_vr` oynadagi har `not passed` ni sanaydi (`reduce.py:1000`).

### 4.2 FAKT — nomlangan to'rt trial'ning oynasi (vaqt `t_up` dan)

**`b003t004` (`A/P1`, `censored`/`window_past_pressure`).** Crash
(+50, +150 ms da 2 `conn_refused`) epizod bermadi; epizod — 25.051 s dagi
5 ta `rt_timeout` seriyasi (anchor = onset), `t_up` 25.551 s. Oynada
**4/81** buzilgan: +2600.0, +2700.0, +2800.0, +2900.0 ms — 4 ta ketma-ket
`rt_timeout` (`rt` 50 142–50 161 µs, `conn` 70–97 µs). Shu tsikllarda
bystander `ok` (`rt` 116–134 µs). Oynada bitta invocation/pid, uzilish va
`probe_overrun` yo'q.

**`b013t000` (`A/P1`, `censored`/`probe_gap`).** Epizod — crash (23.092 s
dan 6 `conn_refused`), `t_up` 24.292 s. Oynada **3/78**: +200.0 ms (1
`rt_timeout`); +5656.7 va +5723.2 ms (2 ketma-ket `rt_timeout`). Ikkinchi
juftdan oldin SUT probe'lari orasida **357 ms uzilish** (29.592 → 29.949 s)
va **`probe_overrun`** (29.949 s, `late_us` 256 638); o'sha tsiklda
bystander `ok`, lekin `rt` 15 698 µs.

**`b008t005` (`A/P2`, `complete`; `b007t001` ning zaxirasi).** Epizod —
crash (23.111 s dan 7 `conn_refused`), `t_up` 24.311 s. Oynada **17/80**,
hammasi `rt_timeout`: +500; +2500, +2600.6; +3500…+3902.5 (5);
+4500…+5103.5 (7); +5500, +5600.6 ms — seriyalar 1, 2, 5, 7, 2. 17 dan
**15** tsiklda bystander ham `rt_timeout`. Uzilish va overrun yo'q.

**`b017t001` (`A/P2`, `censored`/`probe_gap`).** Birinchi epizod onset'i
**injeksiyadan oldin** (21.689 s, 3 `rt_timeout`, ular orasida 257 ms
interval); anchor — systemd restart action'i 23.148 s; crash'dan keyin
~2 s `conn_refused`; `t_up` 25.189 s. Oynada **2/76**: +7300.0 ms (bystander
`ok`) va +7900.0 ms (33.088 s — `T_h` = 33.0 s dan **keyin**; bystander
ham `rt_timeout`). Oynada ikki uzilish (25.288 s, 245.5 ms; 30.288 s,
590.3 ms) va uch overrun bor, lekin buzilgan probe'lar ulardan uzoqda.

### 4.3 FAKT — 29 oyna bo'yicha (arm `A`, birinchi epizod, `overlap` buyrug'i)

- Buzilgan probe'lar: **284**, **hammasi `rt_timeout`**,
  `err_reason = "rt_deadline"` (hech biri `rt_deadline_on_send` emas);
  `rt_us` diapazoni butun run'da 50 111–50 522 µs.
- `conn_refused`, `conn_timeout`, `bad_response`, `no_progress` — oynalarda
  **0**. Buzilgan qatorlarda `restart_seen = 1` — **0**. Oynalarda
  invocation o'zgarishi — **0**. Bystander qatorlari reducer kirishida yo'q
  (nomlangan oynalarda reducer'ning `n_window_probes` i xom SUT qatorlari
  soniga teng: 81, 78, 80, 76).
- 29 dan **8 oynada** eng uzun ketma-ket buzilish seriyasi **`< k_f`**
  (faqat 1–2 lik seriyalar); 21 oynada kamida bitta `≥ k_f` seriya.
- 2 buzilgan probe `T_h` dan keyin (pressure o'chgandan keyin):
  `b002t000` (`censored`/`window_past_pressure`) va `b017t001`
  (`censored`/`probe_gap`; `window_containment = past_pressure`) — ikkala
  oyna §17.4 ning (a) holati, ikkala trial ham binar maxrajdan tashqarida.

### 4.4 FAKT — epizod qaysi hodisadan

Arm `A` ning epizodli trial'larida birinchi epizod onset'i: **31** — crash
lahzasida (`≤ inject + 2P`), **16** — injeksiyadan **oldin**, **1** —
crash'dan keyin (`b003t004`), **2** — `fault_inject` yo'q (`b006t000`,
`b009t004`, ikkalasi `aborted_guard`). 16 ta "oldin" holatning **16 tasida**
anchor — injeksiyadan keyingi oxirgi restart action'i, va `t_up`
injeksiyadan keyin — ya'ni baholangan oyna crash'dan keyingi restart
oynasi.

### 4.5 NATIJA va TALQIN

- **NATIJA:** oynadagi `contract_fail` §2(b) ning **haqiqiy** buzilishi:
  ulanish tez o'rnatildi (a bajarildi), lekin javob `T_rt` ichida kelmadi;
  bu restart'dan keyingi birinchi probe emas (u `t_up` ning o'zi va `ok`),
  bystander qatori emas, boshqa invocation'ning probe'i emas, overrun
  `failure` deb yozilgan emas (overrun alohida record, probe qatori
  emas). Reducer buni §4.2 ning so'zma-so'z qoidasi bilan sanaydi.
- **TALQIN (prober tomoni kechikishi `rt_timeout` yaratadimi):** prober
  `recv` ni socket timeout (poll) bilan kutadi. Javob deadline'dan oldin
  kelgan bo'lsa, prober kechroq uyg'onganda ham poll uni tayyor deb
  qaytaradi — demak sof prober kechikishi `rt_timeout` emas, **kech `ok`**
  beradi. Bunga run'ning o'zida dalil bor: `rt_us` 50 056, 50 081 va
  50 210 µs bo'lgan **3 qator `ok`** deb yozilgan (§7.2). Shuning uchun
  `rt_timeout` — "javob prober qayta tekshirgan lahzagacha kelmagan"
  degan kuzatuv. **CHEKLOV:** bu CPython/Linux poll semantikasiga
  tayangan talqin, run'da o'lchanmagan; SUT va prober'ni bir vaqtda
  to'xtatgan umumiy host stall'ini qatorlar ajrata olmaydi.
- **Dizayn xossasi:** §3 bitta-ikki probe'lik buzilishni *"shovqin"* deb
  failure hisoblamaydi (`k_f = 3`), §4.2 esa oynada **bitta** buzilishni
  invalidator qiladi. 8/29 oynada `vr = False` faqat §3 ning o'zi shovqin
  deb ataydigan seriyalarga tayanadi (`b013t000`, `b017t001` shular
  jumlasidan). Bu implementatsiya xatosi emas — ikki muzlatilgan bandning
  asimmetriyasi.

**Hukm (savol 3):** **muzlatilgan matnga sodiq** — `contract_fail` haqiqiy
§2(b) buzilishi va reducer §4.2 ni aynan bajaradi; **qo'shimcha ravishda
dizaynning o'z xossasi:** 8/29 oynadagi hukm faqat `k_f` dan qisqa
seriyalarga tayanadi.

---

## 5. Savol 4 — reducer'ning VR'i §4 ga sodiqmi

### 5.1 FAKT — mustaqil qayta hisob

`vr_audit_rows.py vr` — `revix.reduce` ni **import qilmaydi**; xom SUT
qatorlaridan §3/§4 bo'yicha: epizod = birinchi `≥ k_f` seriya; anchor =
onset'dan keyingi **oxirgi** action (bo'lmasa onset); `t_up` = anchor'dan
keyingi birinchi `ok`; oyna `[t_up, t_up + 8 s]`; bandlar 2 (har probe
`ok`), 3 (invocation bitta), 4 (SUT `unit_state.n_restarts`), 6
(`cgroup_events`), 7 (`guard_event`); band 5 ikki variantda: `progress`
siz (reducer ko'rgan kirish) va `progress_counter` bilan (faqat
"baholanadimi" chop etiladi).

| trial | yacheyka | `episodes.jsonl` | mustaqil (`progress` siz) | mos |
|---|---|---|---|---|
| `b003t004` | A/P1 | onset 25.051, anchor onset, `t_up` 25.551, 81/4, `contract_fail`, `False` | aynan shu | ✓ |
| `b013t000` | A/P1 | 23.092, onset, 24.292, 78/3, `contract_fail`, `False` | aynan shu | ✓ |
| `b008t005` | A/P2 | 23.111, onset, 24.311, 80/17, `contract_fail`, `False` | aynan shu | ✓ |
| `b017t001` | A/P2 | 21.689, **action 23.148**, 25.189, 76/2, `contract_fail`, `False` | aynan shu | ✓ |
| `b007t001` | A/P2 | 23.151, onset, 24.051, 80/0, `None` `r_ref_unavailable` | `None` (band 5 baholanmaydi) | ✓ |
| `b001t002` | A/P0 | 23.048, onset, 23.348, 81/0, `None` `r_ref_unavailable` | `None` (band 5 baholanmaydi) | ✓ |
| `b000t002` | A/P0 | epizod yo'q, `no_episode` | `no_episode` | ✓ |

`progress_counter` bilan band 5 yettitaning epizodli oltitasida
**baholanadigan** bo'ladi; to'rt `contract_fail` trial'ida monoton
invalidator baribir ishlaydi, demak ularning `vr = False` band 5 dan
**mustaqil**. `b007t001` va `b001t002` uchun natijaviy qiymat **berilmaydi**
(§0).

### 5.2 FAKT — anchor tafsiloti

Arm `A` da `action.mono_us` = systemd restart'ining `t_issue` i (≈ chiqish
lahzasi, injeksiyadan ~+1 ms), u birinchi buzilgan probe'dan **oldin**.
`build_episodes` faqat `mono_us ≥ onset` action'larni epizodniki deb oladi
(`reduce.py:1451`), shuning uchun odatiy crash epizodida
`anchor_source = "onset"`. Tekshiruv: onset-anchor'li 30 arm-`A` epizodning
**29 tasida** action va onset orasida probe **yo'q** va action'dan keyingi
birinchi `ok` = reducer'ning `t_up` i; 1 tasida (`b003t004`) action
**boshqa** (aniqlanmagan crash) hodisaga tegishli. Bu run'da §4.1 ga
nisbatan **ta'siri nol**.

### 5.3 TALQIN — matn jim joylar (bu run'da ta'siri yo'q, lekin ochiq)

1. **Trial darajasidagi `vr` = birinchi epizod** (`reduce.py:2032`).
   Muzlatilgan matn bir trial'dagi bir nechta yoki injeksiyadan oldingi
   epizodni qanday yig'ishni **aytmaydi** (§4 epizod bo'yicha, §10.1 trial
   bo'yicha). 16 "oldin" epizodda anchor qoidasi oynani crash'dan keyingi
   restart'ga ko'chiradi (§4.4), `b003t004` da esa baholangan epizod crash
   emas. **Aniqlab bo'lmaydi** (matndan).
2. **Band 4 va 6 "unverified" bo'lsa ham `vr = True` mumkin.** 4-band
   uchun oynada SUT `unit_state` record'i ko'pincha yo'q (record'lar faqat
   o'zgarishda); 6-band uchun `cgroup_events` trial'ga **bitta** (41.1 s,
   horizon), ya'ni oyna ichida emas (arm `A` da `oom_kill_delta = 0` butun
   trial bo'yicha). `evaluate_vr` ularni `unverified_clauses` ga yozadi,
   lekin `True` ni bloklamaydi. §20.4(2) faqat band 5 ni taqiqlaydi;
   §20.7 (`:6264`) esa *"`vr` tasdiqlab aniqlangan bo'lishi shart"* deydi.
   Bu run'da `True` ga yetib bo'lmagani uchun (§3.1) **ta'siri nol**;
   savol 2 tuzatilgach dolzarb bo'ladi. **Aniqlab bo'lmaydi** (matn
   bir ma'noli emas).

**Hukm (savol 4):** **muzlatilgan matnga sodiq** — nomlangan 7 trial'da
`evaluate_vr`/`build_episodes` mustaqil qayta hisob bilan har maydonda mos;
defekt topilmadi. `r_ref_unavailable` — savol 2 dagi kirish defektining
oqibati. 5.3 dagi ikki nuqta — matn jim, **aniqlab bo'lmaydi**.

---

## 6. Savol 5 — prober tomoni shovqini confound sifatida

### 6.1 FAKT — ustma-ust tushish (sonlar)

"Yaqin" = buzilgan probe `> 2P` SUT uzilishining chetidan `2P` ichida
yoki `probe_overrun` record'idan `±2P` ichida.

| o'lchov | son |
|---|---|
| `contract_fail` bilan arm `A` oynalari | 29 |
| shu oynalarda `> 2P` uzilish bor oynalar | 4 (jami 5 uzilish) |
| kamida bitta buzilgan probe uzilish/overrun'ga yaqin oyna | **3** (`b011t005`, `b012t004`, `b013t000`) |
| **barcha** buzilgan probe'lari yaqin bo'lgan oyna (ya'ni hukm faqat shularga tayangan) | **0** |
| oynalardagi buzilgan probe'lar / ulardan yaqin | 284 / **7** |
| butun run: SUT `rt_timeout` / ulardan yaqin | 705 / **16** |
| butun run: SUT uzilishi bor trial'lar | 24 (`17` §5.3 bilan mos) |
| **baseline oynalari** (pressure yo'q, 120 trial × 10 s): SUT probe / buzilgan | 11 907 / **0** |
| baseline oynalarida `> 2P` uzilish / `probe_overrun` | 16 (12 trial) / 27 (101 dan) |

### 6.2 NATIJA va CHEKLOV

- Baseline'da 16 uzilish va 27 overrun bo'lgani holda **birorta** buzilgan
  probe yo'q: qatorlarda prober stall'i (`17` §5.3 ning 5 s fsync
  GIPOTEZA'si bilan bog'langan uzilishlar) **o'z-o'zidan** `rt_timeout`
  bermagani ko'rinadi.
- `contract_fail` oynalarida hech bir oynaning hukmi faqat uzilish/overrun
  yonidagi probe'larga tayanmaydi (0/29). Yaqin 7 probe — 3 oynada,
  ularning har birida boshqa buzilgan probe'lar ham bor.
- **CHEKLOV:** `rt_timeout` ning **sababi** (SUT'ning o'z stall'i, slice
  bo'ylab memory stall, yoki host stall) qatorlardan **aniqlab
  bo'lmaydi**; bystander SUT bilan bir slice'da (`revixlab.slice`,
  `00-pilot-topologiya.md`), demak u toza nazorat emas. fsync davomiyligi
  o'lchanmagan (`17` §5.3). Men sabab haqida xulosa chiqarmayman.

**Hukm (savol 5):** **aniqlab bo'lmaydi** (sabab) — lekin bu run'da prober
uzilishi/overrun'i bilan ustma-ust tushish `contract_fail` ni **hech bir
oynada hal qilmaydi** (0/29, 7/284 probe).

---

## 7. Boshqa kuzatuvlar (qisqa)

### 7.1 FAKT — `no_action` va birlamchi maxraj

`no_action` trial'lari §16.2(B) bo'yicha `down_at_horizon` orqali binar
maxrajga kiradi (`b000t000`: `included_in_primary = true`). §16.2(A)
bo'yicha esa trend testiga **yacheyka bermaydi**; `analysis.json` buni
`primary_scope_other_arms_excluded` ogohlantirishi bilan bajaradi. Matn
bilan mos; audit savoli yo'q.

### 7.2 FAKT — `T_conn`/`T_rt` dan oshgan `ok` qatorlar

Butun run'da 5 SUT qatori `ok`, lekin o'lchangan `rt_us > 50 000` (3:
50 056, 50 081, 50 210 µs) yoki `conn_us > 50 000` (2: 51 142,
134 364 µs). Prober §2 ni socket timeout bilan tasniflaydi va o'lchangan
davomiylikni `T_rt`/`T_conn` bilan **solishtirmaydi**. 2 tasi allaqachon
`contract_fail` bo'lgan oynada (`b005t000`, `b019t002`), 3 tasi birinchi
epizod oynasidan tashqarida ⇒ bu run'da **birorta `vr` ga ta'siri yo'q**.
O'lchangan davomiylik prober'ning o'z kechikishini ham o'z ichiga olgani
uchun bu SUT buzilishimi — **aniqlab bo'lmaydi**.

### 7.3 FAKT — injeksiyadan oldingi `no_progress`

`b017t001` da injeksiyadan oldin 2 ta `no_progress` (22.588, 22.688 s;
bir invocation, `progress_delta ≤ 0`) — §2(c) ning haqiqiy buzilishi;
oynadan tashqarida.

---

## 8. Pilot natijalari o'quvchisiga nima aytilishi SHART

1. **`derived3` reduksiyasida `R_ref` 120/120 trial'da yo'q** — sabab
   reduksiya zanjiridagi defekt (`progress` maydoni CSV round trip'ida
   tushib qoldi), ma'lumot emas. Shu sababli band 5, `D_eff`, time-to-VR
   (KM/log-rank/RMST) va sensitivity sweep bu chiqishda **o'lchov emas**;
   `vr = True` bu reduksiyada **erishib bo'lmaydigan** edi.
2. Validator va reducer **bir xil ko'rinishni ko'rmagan**: validator
   `progress` ni o'zi qo'shgan xotiradagi ko'rinishni tekshirgan.
3. `A/P0` dagi 10 `no_episode` — injektor nuqsoni **emas**: crash
   `k_f = 3` dan qisqa (2 probe) uzilish berdi va muzlatilgan detektor uni
   ko'rmaydi. Bu §20.3 ning *"injeksiya ishlamadi"* talqiniga va uning
   pilot gate qoidasiga **zid**; hal qilinmagan.
4. `P0` da VR (defekt tuzatilgan taqdirda ham) faqat crash uzilishi
   `≥ 3` probe bo'lgan trial'lar ustida aniqlanadi; `P1`/`P2` da esa epizod
   pressure ostidagi `rt_timeout` seriyasidan ham tug'iladi (arm `A` da 16
   "injeksiyadan oldin", 1 "crash'dan keyin"). Strata'lar bo'ylab maxrajga
   kirish qoidasi mexanik jihatdan bir xil emas.
5. Oynadagi `contract_fail` — §2(b) ning haqiqiy buzilishi (javob 50 ms
   ichida kelmadi; 284/284 `rt_timeout`), restart, bystander yoki
   overrun artefakti emas; lekin 8/29 oynada hukm faqat `k_f` dan qisqa
   seriyalarga tayanadi (§3/§4.2 asimmetriyasi).
6. Prober uzilishlari bu run'da `contract_fail` hukmini hech bir oynada
   hal qilmaydi; `rt_timeout` larning sababi aniqlanmagan.
7. Trial darajasidagi `vr` = birinchi epizod, va band 4/6 "unverified"
   bo'lsa ham `True` mumkin — muzlatilgan matn ikkalasida ham jim.
8. Bu audit **hech bir gipoteza haqida xulosa chiqarmaydi**; orkestrator
   yacheyka tally'larini ko'rgan, auditor esa `analysis.json` dagi `A`
   yacheykalarining `k/n` ini tasodifan ko'rgan (§0).

---

## 9. CHEKLOV

- Nomlangan trial'lar 7 ta; 29 oyna faqat mexanik ustunlar bilan ko'rildi.
- Tanlov qoidasining inspeksiyadan oldinligi tashqi yozuv bilan
  tasdiqlanmaydi (§0).
- Poll semantikasi haqidagi TALQIN (§4.5) run'da o'lchanmagan.
- `rt_timeout` va uzilishlar sababi o'lchanmagan; fsync davomiyligi,
  `pressure.jsonl`, `psi.csv`, host holati ko'rilmadi.
- `pilot_reduce.py` repo'da emas (orkestrator scratchpad'ida); uning
  mazmuni sha256 bilan qayd etildi.
- Natijaga oid hech narsa hisoblanmadi va berilmadi.

## 10. Fayllar va buyruqlar

| fayl | nima |
|---|---|
| `datasets/smoke-tools/vr_audit_rows.py` | yordamchi: `cells`, `inject`, `p0`, `rref`, `window`, `vr`, `overlap` (faqat o'qiydi) |
| `~/vraudit-scratch/raw/`, `~/vraudit-scratch/derived3/` | guest'dagi nusxalar |
| `revix/reduce.py` :507, :762, :850, :921, :1000, :1061, :1072, :1340, :1425, :1451, :2032 | `progress` o'qilishi, throughput, `R_ref`, VR, epizod |
| `revix/validate.py` :2180, :2335, :2569–:2578, :2652–:2653 | adapter, `reducer_view`, `probe_progress_unreadable` |
| `revix/prober.py` :153, :487, :494–:499 | `progress_counter`, `T_rt` deadline |
| `revix/driver.py` :1021, :2824–:2829 | `normalise_probe_row`, `baseline_window.throughput` |
| `revix/sut.c` :438–:470 | `FAULT exit`: javob, keyin `_exit` |
| `docs/architecture/04-driver-va-analiz-shartnomasi.md` §4.4–§4.5 | adapter kontrakti |
| `PREREGISTRATION.md` :3459–:3460, :3476, :3502–:3508, :3531, :4532, :6100–:6150, :6152–:6183, :6264 | iqtiboslar |

Buyruqlar (guest, `W` = worktree'ning `/mnt/c/...` yo'li):

```
python3 $W/datasets/smoke-tools/vr_audit_rows.py raw derived3 p0
python3 $W/datasets/smoke-tools/vr_audit_rows.py raw derived3 inject b000t002 b003t001 b001t002
REVIX_REPO=$W python3 $W/datasets/smoke-tools/vr_audit_rows.py raw derived3 rref
python3 $W/datasets/smoke-tools/vr_audit_rows.py raw derived3 window b003t004 b013t000 b007t001 b008t005 b017t001
python3 $W/datasets/smoke-tools/vr_audit_rows.py raw derived3 vr b003t004 b013t000 b008t005 b017t001 b007t001 b001t002 b000t002
python3 $W/datasets/smoke-tools/vr_audit_rows.py raw derived3 overlap
```
