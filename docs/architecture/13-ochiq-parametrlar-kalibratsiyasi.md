# 13 — Ochiq parametrlar kalibratsiyasi: `WatchdogSec`, `TimeoutStartSec`, `MemoryHigh`, `T_trial`

Bu hujjat `PREREGISTRATION.md` §16.10 ning **muzlatilmagan parametrlari**
uchun o'lchov va **taklif** beradi. Qiymatni muzlatish — orkestrator va
keyingi amendment'ning ishi; bu hujjat hech qanday muzlatilgan matnni
o'zgartirmaydi.

Belgilar (`08` va `10` dagi bilan bir xil, bitta qo'shimcha bilan):

- **FAKT** — o'lchandi, buyruq va chiqish keltirilgan;
- **GIPOTEZA** — o'lchovdan oldin qilingan, o'lchov bilan tekshiriladigan taxmin;
- **NATIJA** — oldindan e'lon qilingan qoidaning FAKT'larga qo'llanishi;
- **TALQIN** — FAKT'dan nima kelib chiqishi (o'lchov emas, xulosa);
- **CHEKLOV** — bu muhitda o'lchab bo'lmaydigan yoki kafolatlab bo'lmaydigan narsa.

**Branch:** `experiment/open-params`. **Run ID (oldindan belgilangan):**
`open-params-cal-01`.

---

## 0. QOIDA — o'lchovdan OLDIN yozilgan va alohida commit qilingan

> **Bu bo'lim birorta o'lchov bajarilishidan OLDIN yozildi va o'z commit'ida
> (o'z vaqt belgisi bilan) qayd etildi.** O'lchovlar va ularning natijalari
> keyingi commit'larda keladi. O'quvchi `git log -- docs/architecture/13-ochiq-parametrlar-kalibratsiyasi.md`
> orqali qoidaning ma'lumotdan oldin turganini tekshira oladi. Quyidagi
> matn keyingi commit'larda **o'zgartirilmaydi**; agar qoidaning biror
> joyi ma'lumotga qo'llab bo'lmaydigan bo'lib chiqsa, bu §0 ni tahrirlash
> bilan emas, natija bo'limida **ochiq og'ish** sifatida yoziladi.

### 0.1 Nima uchun qoida kerak (§16.10 ning o'z so'zi bilan)

§16.10: bu qiymatlar *"kutilgan natijani yarata oladi"*. `TimeoutStartSec`
§9.2 mexanizm **(i)** ni, `WatchdogSec` mexanizm **(iv)** ni **belgilaydi**:
kichik qiymat pressure'ning o'zidan `Result=timeout` / `Result=watchdog`
yasaydi (soxta pressure effekti), katta qiymat dizayn oldindan aytgan
mexanizmni yo'q qiladi. Shuning uchun qiymat **natijaga qarab emas,
oldindan qo'yilgan qoidaga qarab** tanlanadi.

### 0.2 O'lchanadigan kattaliklar (ta'riflar)

- **`t_start`** — `ActiveEnterTimestampMonotonic − InactiveExitTimestampMonotonic`
  (`10` §6.1 va `08` §15 bilan aynan bir xil), SUT unit'i driver'ning
  property to'plami bilan ishga tushirilganda: `revix/driver.py`
  `_sut_properties()` (`Type=notify`, `WatchdogSec=5s`,
  `TimeoutStartSec=10s`, `MemoryMax=256M`, `MemorySwapMax=0`,
  `TasksMax=64`, `Collect`) + `no_action` arm'i (`Restart=no`,
  `StartLimitBurst=0`).
- **`M_start`** — shu run'dagi **barcha** `t_start` namunalarining
  maksimumi (uchala band, A va B qism). Start `Result=timeout` bilan
  yiqilsa, namuna `≥ 10 s` deb **senzuralangan** hisoblanadi.
- **Watchdog oralig'i `g`** — bitta SUT invocation'ining
  `WatchdogTimestampMonotonic` qiymatining ketma-ket ikki **turli**
  qiymati orasidagi farq (systemd ping'ni **qabul qilgan** vaqt — ya'ni
  aynan watchdog qarori tayanadigan vaqt). SUT ping'ni ish tsiklidan
  `WATCHDOG_USEC/2` da yuboradi va keyingi muddatni yuborish lahzasidan
  hisoblaydi (`revix/sut.c` `work_loop`: `wd_next_us = now + wd_period_us`),
  demak nominal oraliq `W/2 = 2.5 s`.
- **Ortiqcha `δ = g − W₀/2`** (`W₀ = 5 s`, ya'ni `δ = g − 2.5 s`) — ish
  tsiklining ping muddatidan **kechikishi** (starvation). Watchdog miss
  sharti: `g > W` ⇔ `δ > W/2`. Ya'ni miss'ni `g` ning o'zi emas, **`δ`**
  belgilaydi, va `W/max(g)` nisbati shu dizaynda **2 dan oshishi mumkin
  emas** (har doim `g ≥ ~W/2`). Shuning uchun qoida `δ` ga qo'llanadi;
  `W/max(g)` ham topshiriq talab qilgani uchun beriladi.
- **`M_wd`** — shu run'dagi barcha oraliqlarning (uchala band, pressure
  oldi / davomida / keyin, arm→birinchi ping oralig'i ham) **`max(δ)`**.

**GIPOTEZA G1 (o'lchovdan oldin):** `δ` ning taqsimoti ping davriga
(`W/2`) bog'liq emas — u ish tsiklining bloklanish epizodining "qoldiq
uzunligi", davr esa bloklanishga ta'sir qilmaydi. Shu taxmin `W₀ = 5 s`
da o'lchangan `M_wd` ni boshqa `W` ga ko'chirishga ruxsat beradi.
**Bu o'lchanmaydi** (faqat `W₀ = 5 s` o'lchanadi) va CHEKLOV sifatida
natijada qayta yoziladi.

### 0.3 Xavfsizlik koeffitsiyenti `F = 3` — loyihaning o'z presedenti

`F` ni men o'ylab topmayman, loyihaning **aynan shu parametr uchun**
yozgan talabidan olaman:

- `10-pressure-dozalash.md` §10.2 (OQ-8): *"`WatchdogSec` o'sha
  maksimumning **kamida 2–3 karrasi** bo'lishi kerak, aks holda §9.2 ning
  (iv) mexanizmi **asbob artefakti** sifatida ishga tushadi"*. Men
  oraliqning **yuqori** chetini — **`F = 3`** — olaman, chunki §16.10
  xavfning birinchi yo'nalishi sifatida *yaratilgan* natijani ko'rsatadi
  va namuna kichik (`10` §6.5 CHEKLOV: *"`p99` n=24 da amalda `max` ga
  yaqin, demak u taqsimot bahosi emas"*).
- Bir xil `F` **ikkala** parametrga qo'llanadi: §16.10 ning 2-qoidasi
  (arm/darajalar bo'ylab bir xillik) ruhida, ikki mexanizmga ikki xil
  zaxira berish o'zi mexanizmlararo taqqoslashni yaratardi.
- Hisobot uslubi `08`/`10` niki: zaxira `qiymat / o'lchangan` ko'paytma
  sifatida (`16.65×`, `1.02×`, `6.75×` kabi), 2 xona aniqlikda.

Taqqoslash uchun (qoidaga **kirmaydi**): `10` §10.1 `10 s / 1.4807 s =
6.75×` zaxirani *"xavfsiz"* deb baholagan; `sut.c` ning ping davri
`W/2` systemd konvensiyasining `2×` zaxirasi — u **nominal davrga**
tegishli, starvation'ga emas.

### 0.4 Yuqori chegara `U` — muzlatilgan timeline'dan arifmetika (o'lchov emas)

Mexanizm trial ichida **kuzatilishi** uchun u `T_trial` dan oldin yuz
berishi kerak. `schedule.TrialTimeline()` ning default'i va `driver.t_trial_us`
bo'yicha: `t_inject = 5 + 10 + 5 + 3 = 23.0 s`, `RestartSec = 0.1 s`
(arm `A`), `T_trial = 41.1 s`. Shuning uchun:

- **(i):** restart start job'i `t_inject + 0.1` da boshlanadi va eng
  kechi `+ TimeoutStartSec` da `Result=timeout` beradi ⇒
  **`U_start = 41.1 − 23.1 = 18.0 s`**.
- **(iv):** restart'dan keyin watchdog `READY=1` da qurollanadi
  (GIPOTEZA G2, quyida); eng erta miss `t_inject + 0.1 + t_start + W` da
  ⇒ **`U_wd = 18.0 − M_start`** s.

`U` dan katta qiymat mexanizmni trial oynasida **mavjud bo'lmaydigan**
qiladi — §16.10 ning ikkinchi xavfi.

**GIPOTEZA G2:** `Type=notify` xizmatida systemd watchdog'ni `READY=1`
qabul qilingandan keyin qurollaydi (boshlang'ich `WatchdogTimestampMonotonic`
≈ `ActiveEnterTimestampMonotonic`). O'lchovda tekshiriladi; noto'g'ri
chiqsa natijada yoziladi.

### 0.5 Qaror qoidasi (har ikki parametr uchun bir xil shakl)

```
v_default : TimeoutStartSec = 10 s,  WatchdogSec = 5 s   (driver.py, ma'lumotdan OLDIN)
L_start   = F * M_start                    (F = 3)
L_wd      = 2 * F * M_wd                   (shart W/2 >= F * M_wd)
grid      = butun sekund
taklif    = max(v_default, ceil(L))   agar ceil(L) <= U
          = TAKLIF YO'Q, ZIDDIYAT     agar ceil(L) >  U   (orkestratorga; men yo'nalish tanlamayman)
```

Qo'shimcha qat'iy shartlar (har biri buzilsa **o'sha parametr uchun
taklif berilmaydi**, sabab yoziladi):

1. **Senzura.** Run davomida birorta `Result=watchdog` bo'lsa, `M_wd`
   `> 2.5 s` bilan senzuralangan — bu ma'lumotdan `watchdog_sec` chiqmaydi
   (kattaroq `W` bilan qayta o'lchov kerak). Birorta `Result=timeout`
   bo'lsa — `timeout_start_sec` uchun xuddi shunday.
2. **Rezolyutsiya (A qism).** Poller'ning ketma-ket ikki o'qishi orasidagi
   eng katta interval **< 1.0 s** bo'lishi shart (ping'lar ≥ ~2.5 s
   oralig'ida, demak bunda birorta ping o'tkazib yuborilmaydi). Buzilsa
   yoki `WatchdogTimestampMonotonic` umuman yangilanmasa — A qism
   **to'xtatiladi**, `watchdog_sec` uchun taklif yo'q.
3. **Namuna hajmi.** A: har bandda **≥ 24** yaroqli epizod. B: har bandda
   **≥ 48** start, `P1`/`P2` da ular **PRESSURED** bo'lishi kerak
   (`10` §6.1 qoidasi: start oralig'ida `lab` `full total=` haqiqatan
   oshgan).
4. **Yaroqlilik.** `boot_id` yoki `/proc/1/stat` 22-maydoni run boshidagidan
   farq qilsa — o'sha partiya (epizod) **tashlanadi** va yoziladi. Guard
   trip bo'lgan epizod tashlanadi va yoziladi. Har pressure epizodidan
   keyin: `/proc/vmstat oom_kill` o'zgarmagan, `lab memory.swap.current = 0`;
   run oxirida `revix doctor --json` ning `leftover_state` = PASS.
5. **Bir qiymat.** `M` uchala band bo'ylab olinadi ⇒ bitta qiymat barcha
   arm va darajalar uchun (§16.10(2)).

### 0.6 Qoida qaysi tomonga xato qiladi (ochiq e'lon)

Qoida default'ni **hech qachon pasaytirmaydi** va uni faqat kalibratsiya
zaxirasi talab qilganda ko'taradi. Demak u **(i) va (iv) ni pressure'ning
o'zidan ishga tushirishni QIYINLASHTIRISH tomoniga** xato qiladi
(mexanizm uchun false-negative), **hech qachon ularni yaratish tomoniga
emas**. Oqibat, §16.10(5) talab qilgan bayonot shaklida:

> **"Mexanizm (i) ning mavjudligi `TimeoutStartSec` ning muzlatilgan
> qiymati bilan belgilangan; mexanizm (iv) ning mavjudligi `WatchdogSec`
> ning muzlatilgan qiymati bilan belgilangan."** Kalibrlangan dozada
> (i) uchun start kalibratsiyaning eng yomon `t_start` idan kamida `F`
> marta sekin bo'lishi, (iv) uchun ish tsikli kalibratsiyaning eng katta
> kechikishidan kamida `F` marta uzoq bloklanishi kerak. Shuning uchun
> pilotda (i)/(iv) ning **yo'qligi** bu mexanizmlar haqida **ma'lumot
> bermaydi** (parametr tanlovi bilan belgilangan), ularning **paydo
> bo'lishi** esa pilot sharoiti kalibratsiyadan `F×` dan ortiq chetga
> chiqqanini bildiradi — va §11(c) ga tayanilsa, shu bayonot va muzlatilgan
> qiymat hisobotda **majburiy**.

Nega default saqlanadi va "eng kichik qiymat" tanlanmaydi: default'lar
`driver.py` da **har qanday ma'lumotdan oldin** yozilgan, demak ularni
saqlash natija bo'yicha tanlov emas. Qiymatni kalibratsiya maksimumining
`F×` iga **tushirish** esa mexanizmni chegaraga eng yaqin joyga qo'yish
bo'lardi — aynan §16.10 ning birinchi xavfi.

### 0.7 `MemoryHigh` va `T_trial` uchun qoida

- **`memory_high`:** yangi kalibratsiya **rejalashtirilmaydi**. Qaror
  `10` §2.2 ni §16.10(6) ga qarshi o'qishdan chiqadi: agar `10` §2.2
  `192M` ni **`MemoryMax=2G` ostida o'lchagan** bo'lsa (ko'chirmagan),
  6-qoida bajarilgan. Shu run'da `192M` ham ishlatiladi va
  **qayta-ishlab-chiqarish tekshiruvi** sifatida (kalibratsiya emas)
  yoziladi: `P1`/`P2` epizodlarining **≥ 90%** ida `memory.events high`
  delta `> 0` va `lab full total=` delta `> 0`, `P0` da ikkalasi `0`.
  Bajarilmasa — `memory_high` uchun taklif yo'q, sabab yoziladi.
- **`T_trial`:** qiymat **o'lchovdan chiqarilmaydi**: formula
  `t_pressure_off + w_stab_s + P = 33 + 8 + 0.1 = 41.1 s` (`driver-contract/v1.2`).
  Tekshiriladi: (a) `t_inject + 0.1 + M_start + w_stab + P ≤ 41.1`;
  (b) `10` §7.2 ning `max(D_probe)` bilan `t_inject + max(D_probe) +
  w_stab + P ≤ 41.1`; (c) A qismda generator to'xtaganidan `lab` 2 s
  stall tezligi `< 0.05` ga tushguncha o'tgan vaqt va pressure'dan keyingi
  `δ`. (a)–(b) bajarilsa 41.1 s taklif qilinadi; (c) hisobot uchun.
  §17.3 tengsizligi **qayta hisoblanmaydi** (v1.11 amendment'ining 4-bandi).

### 0.8 Protokol (oldindan qotirilgan)

- **Dial:** `MemoryMax=2G`, `MemoryHigh=192M`, `MemorySwapMax=0`,
  `TasksMax=256`, `CPUQuota=400%` (slice); generator `--mode pi
  --step-mb 4 --base-mb {P0:160, P1:184, P2:184} --target-rate
  {0.0, 0.30, 0.60} --chunk-mb 32 --interval-ms 250` (`driver.py`
  `PRESSURE_*`), `MemoryMax=1536M`, `OOMPolicy=continue`.
- **Epizod chegarasi:** `--max-seconds 13` **va** `RuntimeMaxSec=15s`
  (driver formulasi `int(max)+2`); ya'ni generatorning butun umri
  (ramp ham) ≤ 13 s — `schedule.HOLD_CAP_S` ning eng qat'iy o'qishi.
- **Quiescence:** generator to'xtagandan keyin **≥ 20 s** va
  `schedule.WashoutMachine` (§8.4: `memory.current` baseline ±32 MiB,
  `lab` VA host 2 s tezligi `< 0.05` 5 s davomida, pol 15 s, cap 120 s).
- **A (watchdog):** har epizodda **yangi** SUT unit'i; pressure'dan
  oldin 6 s; generator (13 s); quiescence; SUT to'xtatiladi. Poller
  `revixmon.slice` da, **20 Hz**, `WatchdogTimestampMonotonic`,
  `ActiveState`, `Result`, `NRestarts` va `lab`/host `memory.pressure`
  `total=` ni yozadi; `units.UnitWatcher` holat o'tishlarini yozadi.
  Fault injeksiya **YO'Q**. Har bandda 24 epizod.
- **B (`t_start`):** generator (13 s) ramp'dan keyin (3 s) generator
  tirik ekan ketma-ket start → `READY` → o'qish → stop; har bandda
  ≥ 48 start (epizodda 4 tagacha, ko'pi bilan 16 epizod).
- **Bandlar tartibi:** har "raund" ichida `P0/P1/P2` tartibi qotirilgan
  seed (`20261003`) bilan aralashtiriladi — vaqt bo'yicha drift bandga
  confound bo'lmasin.
- **Hamma narsa** `systemd-run --user` orqali: SUT va generator
  `revixlab.slice` da, guard, sampler, poller/controller `revixmon.slice`
  da. Guard birinchi, oxirgi to'xtaydi, fail-closed.
- **Statistika:** p50/p90/p99 — chiziqli interpolyatsiya (`10` §6 ning
  `tstart.py` dagi `pct()` bilan bir xil); `max` — namunaning o'zi.
- Bu **pilot trial emas**: `revix run` yo'q, fault yo'q, VR/FR/downtime
  yoki birlamchi endpoint hisoblanmaydi (§16.10(3), §21).

---

## 0A. OG'ISH — `cal-01` host uyqusi bilan uzildi (bu bo'lim `cal-02` dan OLDIN commit qilindi)

> §0 **o'zgartirilmadi**. Bu bo'lim uzilishdan keyin, `cal-02` ishga
> tushirilishidan **oldin** yozildi. Yozish paytida `cal-01` dan men faqat
> **epizod sonlari**, **soat sakrashlari** va **guest belgilari**ni o'qidim;
> watchdog oraliqlari va `t_start` natijalariga **qaralmadi**.

### 0A.1 FAKT — nima bo'ldi

- Windows host uyquga ketdi va WSL VM ni muzlatdi. Guest monotonic soati
  uyquni sanamaydi, real soat sanaydi; shuning uchun `boot_id`
  (`4ea15279-acba-44ff-a533-6d7cd11924e5`) **o'zgarmadi** va controller'ning
  `boot_id`/pid1 tekshiruvi uyquni **ko'rmadi**.
- `psi.csv` (10 Hz, `mono_us` + `real_us`) qo'shni qatorlarida
  `|Δreal − Δmono| > 0.2 s` bo'lgan **5 ta sakrash** (mono 0.1 s, real):
  `6463.779 s` da **+1699.7 s**, `6468.779 s` da **+94.4 s**,
  `6469.779 s` da **+6371.2 s** (uchalasi `A-P0-21` ichida),
  `6472.479 s` da **+42 088.2 s** va `6472.679 s` da **+0.761 s**
  (ikkalasi `A-P2-22` ichida). Birinchi sakrashdan oldin 24 758 qator
  bo'yicha eng katta `|Δreal − Δmono|` = **0.000386 s**.
- `events.jsonl` da `A-P2-22` ning ikki ketma-ket yozuvi: `mono_us`
  6472198275 → 6478211141 (**6.0 s**), `real_us` 1791060253618540 →
  1791102348421289 (**42 094.8 s = 11.7 soat**) — orkestrator o'lchagan
  raqam bilan mos.
- Uyg'ongandan keyin oxirgi yozuv mono `6482.228 s` (`wdpoll.csv`), keyin
  guest'ning **PID 1 qayta ishga tushdi**: `/proc/1/stat` 22-maydon
  `156737 → 653523`, `/sbin/init` start vaqti `2026-10-04 13:26:45`
  (mahalliy), user manager `13:26:48`. Ya'ni run'ni uyquning o'zi emas,
  uyqudan keyingi **guest init restart'i** o'ldirdi (`07` §7.6 ning
  xatti-harakati). Orkestratorning "guest'da hech narsa sezmadi" degan
  bahosi `boot_id` uchun to'g'ri, **pid1 uchun emas**.
- Qoldiq: `revix*` unit **yo'q**; `revixlab.slice`/`revixmon.slice` ostida
  7 ta **bo'sh** cgroup katalogi qoldi (`revix-sut`, `revix-press`,
  `revix-psi`, `revix-opmeas`, `revix-guard`) — `units.teardown()` va
  `rmdir` bilan o'chirildi; keyin `units.preflight()` `clean: true`,
  `revix doctor --json` `leftover_state` **PASS**, `oom_kill 0`,
  `memory.swap.current` ikkala slice'da **0**, runtime/persistent drop-in
  **yo'q**.
- `cal-01` ning B qismi **umuman boshlanmadi** (`tstart.jsonl` 0 bayt):
  bosim ostidagi `t_start` `cal-01` da **o'lchanmagan**. A qismdagi har
  epizodning SUT start'i bosimdan **oldin** (bosimsiz) — u B ning o'rnini
  bosmaydi.

### 0A.2 Chiqarish mezoni — YAGONA, natijaga qaramasdan

Epizod **chiqariladi** faqat agar uning `episode_begin..episode_end`
oralig'i (tugamagan bo'lsa — cheksiz) `psi.csv` dagi `|Δreal − Δmono| >
0.2 s` sakrashini kesib o'tsa, yoki u tugamagan bo'lsa. Boshqa hech qanday
mezon yo'q; epizodlar marja qulayligiga qarab **tanlanmaydi**.

`cal-01` da: 63 ta tugagan A epizodi; `A-P0-21` sakrashni kesib o'tadi,
`A-P2-22` tugamagan ⇒ **yaroqli: `P0` 20, `P1` 21, `P2` 21** (§0.5(3)
maqsadi 24). Yetishmaydi: **`P0` 4, `P1` 3, `P2` 3**, va B qism to'liq.

### 0A.3 `cal-02` — faqat yetishmagan qism

- `open-params-cal-02`: A — `--a-counts P0:4,P1:3,P2:3`, seed `20261004`
  (protokol §0.8 bilan aynan bir xil, faqat sonlar); B — to'liq (har bandda
  ≥ 48 qualifying, ≤ 16 epizod).
- Ma'lumot **ikki run'dan**. Xom fayllar **birlashtirilmaydi**: har run
  `datasets/<run_id>/` da alohida; tahlil ikkalasini yonma-yon yuklaydi va
  epizod kalitlarini `run_id:` bilan prefikslaydi. §0.2 dagi "shu run'dagi"
  so'zi endi **"`cal-01` va `cal-02` ning yaroqli epizodlari"** deb o'qiladi
  — bu yagona ma'noviy og'ish; §0.5 formulasi, `F`, `U`, grid **o'zgarmadi**.
- Controller'ga qo'shildi: har epizod boshida **va oxirida** `real − mono`
  siljishi tekshiriladi (> 1 s ⇒ `episode_end` yozilmaydi, run FAIL-CLOSED
  to'xtaydi). Host'ni idle-uyqudan orkestrator `request_keep_awake` bilan
  himoya qildi (faqat idle uyqu).

## 0B. OG'ISH — `cal-02` guard trip bilan to'xtadi (bu bo'lim `cal-03` dan OLDIN commit qilindi)

> Yozish paytida `cal-02` dan faqat epizod sonlari, guard yozuvi va soat
> sakrashi skani o'qildi; oraliq va `t_start` natijalariga **qaralmadi**.

- **FAKT:** `cal-02` A qismi to'liq bajarildi (`P0` 4, `P1` 3, `P2` 3
  epizod, hammasi `episode_end` bilan). B qismida `B-P2-05` epizodi
  ichida (mono `7638.741 s`) guard trip qildi: `user_full_rate2s_runaway`,
  `rate=0.9801941881552125`, `limit=0.98`, `window_us=2000019`,
  `action=kill_subtree`, `kill_ok=true`. Generator 13 s o'rniga mono
  `7638.895 s` da yo'qoldi. Controller keyingi epizod (`B-P1-05`) boshida
  trip faylini ko'rib FAIL-CLOSED to'xtadi. Post-flight: `oom_kill 0`,
  `lab memory.swap.current 0`, `leftover_state` PASS, `boot_id` va pid1
  (`653523`) o'zgarmadi, `psi.csv` da soat sakrashi **yo'q**.
- **Chiqarish:** §0.5(4) bo'yicha (oldindan yozilgan) `B-P2-05` **butunlay
  tashlanadi** — uning 4 ta start'i ham. Tahlil skripti trip vaqti
  epizod oralig'iga tushgan epizodni chiqaradi.
- **Hisob:** B da yaroqli qualifying start'lar: har bandda **16**
  (4 epizod × 4). Maqsad 48 ⇒ har bandda **32** yetishmaydi.
- **`cal-03`:** faqat B, `--b-min-starts 32`, `--b-max-episodes 11`
  (§0.8 ning har band uchun ≤ 16 epizod chegarasi: `P2` da 5 epizod
  sarflangan), seed `20261005`. Agar `cal-03` ham trip bilan to'xtasa,
  qo'shimcha run qilinmaydi va B uchun namuna yetishmasligi §0.5(3)
  bo'yicha hisobotda yoziladi.
- Bu trip — kalibrlangan dial'da (`base_mb=184`, nishon 0.60) **guard
  trip'ining o'lchangan birinchi holati**: `10` §8.2 *"`base_mb=184` da 29
  epizodda trip YO'Q"* deydi. Natija bo'limida pilot uchun oqibati bilan
  qayta yoziladi.

---

## 1. Provenance va yaroqlilik

**Mashina:** WSL2, kernel `6.6.87.2-microsoft-standard-WSL2`, `systemd 257 (257.7-1)`,
`boot_id=4ea15279-acba-44ff-a533-6d7cd11924e5` (to'rt run'ning hammasida bir xil).
**Dial (har run'da kernel'dan o'qilgan, `slice-props.txt`):** `memory.max=2147483648`,
`memory.high=201326592`, `memory.swap.max=0`, `pids.max=256`, `cpu.max=400000 100000`.
**Bajarilish joyi:** ext4 (`~/openparams-work`, worktree'dan `rsync`), chiqishlar
`~/revix-runs/<run_id>/`. **Qulf:** `~/.revix-exclusive` `2026-10-03T17:42:32Z` da
olindi va `2026-10-04T08:50:15Z` da bo'shatildi (uzilish davomida ham bizda qoldi).
Run'lardan oldin Windows'da `VBoxHeadless` / `VirtualBoxVM` / `qemu-system-x86_64`
**yo'q** (`Get-Process`; birinchi tekshiruvda faqat bo'sh turgan `VBoxSVC` bor edi),
guest'da `VBoxHeadless|mmdebstrap|mksquashfs` **yo'q**, `loadavg1` har run boshida
`< 0.3` (0.00 / 0.00 / 0.06).

| run_id | commit | nima | `episode_end` | yaroqli (§0A/§0B) | pid1 | yakun |
|---|---|---|---|---|---|---|
| `open-params-smoke-01` | `1d344b2` | protokol sinovi, har bandda A 1 + B 1 | 6 | **hisobga kirmaydi** | 156737 | ok |
| `open-params-cal-01` | `1d344b2` | A (24 raund) + B | 63 (A) | A: `P0` 20, `P1` 21, `P2` 21; B: **0** | 156737 | host uyqusi + guest init restart (§0A) |
| `open-params-cal-02` | `8c3607c` | A `P0:4,P1:3,P2:3` + B | 23 | A: 4 / 3 / 3; B: `P0` 4, `P1` 4, `P2` 4 epizod | 653523 | guard trip `B-P2-05` (§0B) |
| `open-params-cal-03` | `c45de9f` | faqat B | 6 | B: `P0` 2, `P1` 2, `P2` 1 epizod | 653523 | guard trip `B-P2-02` |

**Chiqarilgan epizodlar (va FAQAT shular):** `cal-01:A-P0-21` (soat sakrashini
kesadi), `cal-01:A-P2-22` (tugamagan, sakrash ichida), `cal-02:B-P2-05` va
`cal-03:B-P2-02` (guard trip, §0.5(4)).

**Run'lar orasida pid1 o'zgardi** (`156737 → 653523`, §0A.1), shuning uchun monotonic
qiymatlar run chegarasidan o'tib **taqqoslanmaydi**. Birlashtiriladigan narsa faqat
**namuna ichidagi** kattaliklar (oraliq, `t_start`), har biri o'z run'i ichida o'lchangan.

**Har yaroqli epizodda:** `vmstat oom_kill` o'zgarmagan (0), `lab memory.swap.current = 0`.
Har run oxirida `revix doctor --json` `leftover_state` **PASS** (`cal-01` uchun —
uzilishdan keyingi qo'lda tozalashdan so'ng, §0A.1). Quiescence: `WashoutMachine`
barcha 72 A va 31 B yaroqli epizodda `complete` (mashina `15.009–15.022 s` da, §8.4
ning 15 s polida yakunlandi), va har epizod generator yo'qolgandan keyin
**20.01–20.22 s** kutdi; `washout_timeout` **0**.

## 2. A — watchdog oraliqlari (`WatchdogSec=5s`, fault yo'q)

### 2.1 FAKT — rezolyutsiya (§0.5(2)) va G2

- Poller: 70 218 namuna; unit poll'lari orasidagi eng katta interval **0.0699 s**
  (`< 1.0 s` sharti bajarildi); poller xatosi **0**. Ping oraliqlarining eng kichigi
  2.376 s, ya'ni birorta ping o'tkazib yuborilishi mumkin emas.
- **G2 tasdiqlandi:** boshlang'ich `WatchdogTimestampMonotonic − ActiveEnterTimestampMonotonic`
  n=72, min **−0.000125 s**, p50 **−0.000036 s**, max **−0.000031 s** — systemd
  watchdog'ni `READY=1` qabul qilinishi bilan birga qurollaydi.
- Arm→birinchi ping: har bandda n=24, max **2.5006 s** (`P0`), 2.5005 (`P1`),
  2.5007 (`P2`).

### 2.2 FAKT — natijalar

Faqat yaroqli epizodlar. "ping" = arm→birinchi ping'dan keyingi ketma-ket oraliqlar;
"pressure ichida" = oralig'i generator oynasiga (`pressure_start..pressure_stop`)
tegadigan ping oraliqlari. `δ = g − 2.5 s`, barcha oraliqlar bo'yicha.

| band | epizod | ping oraliqlari | p50 | p90 | p99 | **max `g`** | pressure ichida n / p90 / max | **max `δ`** | `W / max g` | `(W/2) / max δ` | `Result=watchdog` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `P0` | **24** | 336 | 2.5002 | 2.5005 | 2.5007 | **2.5012** | 144 / 2.5005 / 2.5010 | **0.0012** | **2.00** | 2157.03 | **0** |
| `P1` | **24** | 336 | 2.5004 | 2.5006 | 2.5755 | **2.6061** | 144 / 2.5375 / 2.6061 | **0.1061** | **1.92** | 23.57 | **0** |
| `P2` | **24** | 336 | 2.5002 | 2.5025 | 2.5868 | **2.6170** | 144 / 2.5531 / 2.6170 | **0.1170** | **1.91** | 21.38 | **0** |

- `Result`: 72/72 epizod oxirida `success`, `NRestarts` 0; poller ham, `UnitWatcher`
  ham birorta `Result=watchdog` ko'rmadi.
- Lab `full total=` haqiqatan o'sgan oraliqlar: `P0` **0**/360, `P1` **117**/360,
  `P2` **116**/360.
- Pressure'dan keyingi oraliqlarda max `δ`: `P0` 0.0007, `P1` 0.0009, `P2` 0.0011 s.
- Erishilgan doza (A epizodlarining PI fazasida 20 Hz `total=` dan 2 s tezliklar
  medianasi, har bandda n=24): `P0` **0.0000** (24/24), `P1` **0.2412–0.3670**
  (p50 0.2651), `P2` **0.5452–0.8526** (p50 0.6714).

**TALQIN.** Ish tsikli kalibrlangan bosim ostida deyarli och qolmaydi: eng yomon
kechikish 0.117 s, ya'ni nominal 2.5 s davrning 4.7% i. Mexanizm bilan mos:
`memory.high` throttling'i **xotira ajratish / page fault** yo'lida ishlaydi, SUT
ish tsikli esa barqaror holatda *"IO yo'q, malloc yo'q"* (`sut.c` boshidagi
2-qoida). 2.5 s dan kichik oraliqlar (min 2.376 s) shuni ko'rsatadiki, `δ` ga
systemd'ning ping'ni **qabul qilish** kechikishi ham kiradi (bitta ping kech qabul
qilinsa, keyingisigacha oraliq qisqaradi). `δ` shuning uchun starvation'ning
**yuqori bahosi** — va aynan qabul vaqti watchdog qarorini belgilaydi.

## 3. B — `t_start` (bosim ostida start)

### 3.1 FAKT — natijalar

Faqat qualifying start'lar (`P1`/`P2`: start oralig'ida lab `full total=` o'sgan;
`P0`: generator tirik paytida boshlangan). Barcha start'lar `active/success`;
**start muvaffaqiyatsizligi 0**, **`Result=timeout` 0**.

| band | epizod | n | min | p50 | p90 | p99 | **max** | `≤ 0.8 s` | `10 s / max` | SUT `uptime_us` p50 / max |
|---|---|---|---|---|---|---|---|---|---|---|
| `P0` | 6 | **24** | 0.0079 | 0.0349 | 0.0417 | 0.0538 | **0.0559** | 24/24 | 179.03 | 0.0167 / 0.0281 |
| `P1` | 6 | **24** | 0.0585 | 0.4685 | 0.7224 | 0.9553 | **0.9614** | 22/24 | **10.40** | 0.0173 / 0.1196 |
| `P2` | 5 | **20** | 0.3845 | 0.5311 | 0.7045 | 0.7510 | **0.7615** | 20/20 | **13.13** | 0.0173 / 0.1361 |

A qismning bosimdan **oldingi** start'lari (har bandda n=24): max `P0` 0.0556,
`P1` 0.0545, `P2` 0.0562 s. **`M_start` = 0.9614 s** (`cal-03` ning `B-P1` start'i).

**FAKT — namuna maqsadga yetmadi:** 24 / 24 / 20 qualifying start; §0.5(3)
maqsadi **48**. Sabab: `cal-01` da B boshlanmadi (§0A), `cal-02` va `cal-03`
ikkalasi ham `P2` B epizodida guard trip bilan FAIL-CLOSED to'xtadi (§0B, §6.3),
va §0B oldindan *"`cal-03` ham trip bilan to'xtasa, qo'shimcha run qilinmaydi"*
deb yozgan.

**FAKT (hisobga kirmaydi, lekin yashirilmaydi):** `smoke-01` ning `P2` B
epizodida (n=4, xuddi shu dial) `t_start` max **1.7030 s** — hisobga kirgan
`M_start` dan 1.77× katta. `10` §6.2 ning `P1` max'i **1.4807 s** edi.

**TALQIN.** n≈20–24 da dum barqaror emas: uch mustaqil o'lchovda eng katta start
0.96 / 1.48 / 1.70 s. `P1` ning dumi yana `P2` nikidan yuqori (`10` §6.5 ning
3-bandi bilan bir xil). Kechikishning katta qismi SUT tashqarisida (`uptime_us`
p50 ≈ 0.017 s), `10` §6.4 bilan mos.

## 4. `memory_high` — yangi o'lchov KERAK EMAS

- **FAKT (o'qilgan, o'lchanmagan):** `10-pressure-dozalash.md` §2.2 `MemoryHigh=192M`
  ni **`MemoryMax=2G`** ostida (`dose-01-dial`) qayta o'lchagan: `step_mb=16 → base 160`
  nol doza (`memory.current` max 185.3 MiB, `08` §3.4 bilan aynan bir xil),
  `step_mb=4 → base 184` erishilgan p50 **0.3344**; §2.6 dial'ni 2G ostida qotirgan.
  `02` ning 1G ostidagi qiymati **ko'chirilmagan**, qayta o'lchangan.
- **NATIJA (§0.7):** §16.10(6) — *"`MemoryMax=2G` topologiyasida qayta o'lchanadi;
  1G ostida o'lchangan 192 M ko'chirilmaydi"* — **bajarilgan**. Shu kalibratsiyadagi
  qayta-ishlab-chiqarish tekshiruvi: `P0` **30/30** epizodda `high` delta va
  `full total=` delta **0**; `P1` **30/30** va `P2` **29/29** da ikkalasi `> 0`
  (talab ≥ 90%). `pressure_stop` 30 / 30 / 29 da yozildi, `overrun_s` max
  0.0954 / 0.1373 / 0.1210 s. ⇒ **taklif: `192M`.**
- **CHEKLOV:** bu `192M` ning **optimal** ekanini ko'rsatmaydi — boshqa `MemoryHigh`
  qiymatlari o'lchanmagan (`10` OQ-11). §16.10(6) optimallikni talab qilmaydi;
  `driver.py` dagi `calibration_required: True` izohi OQ-11 ga tayanadi — yechish
  orkestratorning qarori. `memory_high` ning kalibratsiya run'lari `10` niki
  (`dose-01-dial`, `dose-02-bands`, `dose-03-p2sweep`); ularning xom ma'lumoti
  `datasets/` da **yo'q** (guest'da `~/revix-runs/dose-*` sifatida bor).

## 5. `T_trial`

- **NATIJA (§0.7):** (a) `23.0 + 0.1 + M_start 0.9614 + 8.0 + 0.1 = 32.16 s ≤ 41.1`;
  (b) `23.0 + max(D_probe) 2.2 (10 §7.2, P2) + 8.0 + 0.1 = 33.3 s ≤ 41.1`. Ikkalasi
  bajarildi ⇒ **taklif: `41.1 s`** (formula `t_pressure_off + w_stab_s + P`,
  `driver-contract/v1.2`; raqam o'lchovdan chiqarilmagan). `smoke-01` ning 1.7030 s
  i bilan ham (a) `32.90 s`.
- (c) **FAKT:** 72 A epizodining hammasida `pressure_stop` dan keyin lab
  `full total=` **birorta marta ham o'smadi** (20 Hz, ≤ 0.05 s aniqlik), va
  pressure'dan keyingi watchdog oraliqlarida max `δ` ≤ **0.0011 s**. Bosim
  o'chgandan keyin stall darhol to'xtaydi; `[33.0, 41.1] s` oynasiga bosim qoldig'i
  sizib o'tmaydi.

## 6. NATIJA — qoidaning qo'llanishi

### 6.1 `watchdog_sec` — **taklif: `5 s` (o'zgarmaydi)**

```
M_wd   = 0.1170 s  (P2; cal-01 + cal-02; 72 epizod, 1008 ping + 72 arm oralig'i; Result=watchdog 0)
L_wd   = 2 * 3 * 0.1170 = 0.70 s  -> ceil = 1 s
U_wd   = 18.0 - M_start 0.9614 = 17.04 s       (1 <= 17.04, ziddiyat yo'q)
taklif = max(5, 1) = 5 s
zaxira : (W/2) / M_wd = 21.38x  (talab F = 3);   W / max g = 5 / 2.6170 = 1.91  (dizayn bo'yicha <= 2)
```

> **§16.10(5) bayonoti:** *"Mexanizm (iv) (watchdog miss) ning mavjudligi `WatchdogSec`
> ning muzlatilgan qiymati bilan belgilangan."* `WatchdogSec = 5 s` da miss uchun ish
> tsikli (qabul kechikishi bilan birga) **≥ 2.5 s** ushlanishi kerak — kalibrlangan
> `P0/P1/P2` da o'lchangan eng yomon holatning **21.4×** i. Kalibrlangan dozada
> bosimning o'zi (iv) ni **yaratmadi** (0/72 epizod). Qoidaning yo'nalishi bo'yicha
> pilotda (iv) ning **yo'qligi** bu mexanizm haqida ma'lumot bermaydi.

### 6.2 `timeout_start_sec` — **taklif BERILMAYDI (§0.5(3))**

Qualifying start'lar 24 / 24 / 20 < 48. Oldindan yozilgan qoida bu holda taklif
bermaslikni talab qiladi, va men taklif bermayman. Faqat **ma'lumot uchun** (qaror
emas): qoidaning arifmetikasi shu ma'lumotda `L = 3 × 0.9614 = 2.88 → 3 s ≤ U = 18.0 s`,
`max(10, 3) = 10 s`; `smoke-01` ning 1.7030 s i bilan `6 s → 10 s`; `10` §6.2 ning
1.4807 s i bilan `5 s → 10 s`. Ya'ni kuzatilgan uchala dum bilan ham qoida `10 s`
ni o'zgartirmagan bo'lardi — lekin bu namuna sharti bajarilmagan arifmetika, va
`calibration_required: true` **o'z kuchida qoladi**.

> **§16.10(5) bayonoti (muzlatiladigan qiymat qaysi bo'lishidan qat'i nazar):**
> *"Mexanizm (i) (`TimeoutStartSec` oshib ketdi) ning mavjudligi `TimeoutStartSec`
> ning muzlatilgan qiymati bilan belgilangan."* `10 s` da (i) uchun start shu
> kalibratsiyaning eng yomon `t_start` idan **10.40×** sekin bo'lishi kerak
> (`smoke-01` ga nisbatan 5.87×). Kalibratsiyada `Result=timeout` **0** (68 qualifying
> + 72 bosimsiz start).

**Kerakli o'lchov:** xuddi shu protokol bilan yana `P0` 24, `P1` 24, `P2` 28
qualifying start. Lekin `P2` B epizodlari guard'ni ikki marta urdi (§6.3), demak
bu o'lchovni yakunlashdan oldin guard/dial masalasini kim va qanday hal qilishi
orkestratorning qarori. Men hal qilmayman.

### 6.3 FAKT — kalibrlangan `P2` da bosim ostidagi SUT start'lari guard'ni uradi

| run | epizod | sabab | `rate` | `limit` | `window_us` | `kill_ok` |
|---|---|---|---|---|---|---|
| `cal-02` | `B-P2-05` | `user_full_rate2s_runaway` | **0.9801941881552125** | 0.98 | 2000019 | true |
| `cal-03` | `B-P2-02` | `user_full_rate2s_runaway` | **0.9888733810188433** | 0.98 | 2100009 | true |

Ikkalasi ham **B** (bosim ostida ketma-ket 4 SUT start'i) ning **`P2`** epizodida.
**B-`P2`: 7 epizoddan 2 tasida trip; A-`P2` (bosim ostida start yo'q): 24 yaroqli
epizodda 0; B-`P0`/`P1`: 12 epizodda 0.** `oom_kill` 0, swap 0 — guard o'ldirdi,
kernel emas. `10` §8.2 kalibrlangan `base_mb=184` da 29 epizodda trip **ko'rmagan**.

**TALQIN (sabab o'lchanmagan):** yangi jarayonning `execve` va birinchi page
fault'lari to'yinishga yaqin `P2` arra tishiga qo'shilib, `user@` ning 2 s tezligini
0.98 dan oshiradi. **Pilot uchun oqibat:** arm `A` ning restart'i aynan shu holat
(bosim ostida start); `P2` da `aborted_guard` dispozitsiyasi kutilganidan ko'proq
bo'lishi mumkin, va u §12 bo'yicha analiz to'plamidan chiqariladi — ya'ni arm `A`
ning `P2` yacheykasida **tanlab yo'qotish** xavfi. Bu n=7 dan; bu hujjat uni
o'lchamadi, faqat qayd etdi.

### 6.4 `memory_high` — **taklif: `192M`** (§4). `T_trial` — **taklif: `41.1 s`** (§5).

## 7. Amendment `open_parameters` ga yozishi kerak bo'lgan qatorlar (TAKLIF)

```json
"watchdog_sec": {
  "value": "5s",
  "calibration_required": false,
  "calibration": {
    "run_ids": ["open-params-cal-01", "open-params-cal-02"],
    "rule": "docs/architecture/13-ochiq-parametrlar-kalibratsiyasi.md §0.5 (commit 812c989, ma'lumotdan oldin)",
    "F": 3, "M_wd_delta_s": 0.1170, "max_gap_s": 2.6170,
    "halfW_over_M_wd": 21.38, "W_over_max_gap": 1.91,
    "episodes": {"P0": 24, "P1": 24, "P2": 24}, "result_watchdog": 0
  },
  "mechanism_statement": "§9.2 (iv) ning mavjudligi WatchdogSec ning muzlatilgan qiymati bilan belgilangan"
},
"timeout_start_sec": {
  "value": "10s",
  "calibration_required": true,
  "calibration": {
    "run_ids": ["open-params-cal-02", "open-params-cal-03"],
    "status": "namuna §0.5(3) ga yetmadi (24/24/20 < 48) -- qoida taklif bermadi",
    "M_start_s": 0.9614, "timeout_over_max": 10.40, "result_timeout": 0
  },
  "mechanism_statement": "§9.2 (i) ning mavjudligi TimeoutStartSec ning muzlatilgan qiymati bilan belgilangan"
},
"memory_high": {
  "value": "192M",
  "calibration_required": false,
  "calibration": {
    "run_ids": ["dose-01-dial", "dose-02-bands", "dose-03-p2sweep"],
    "measured_in": "docs/architecture/10-pressure-dozalash.md §2.2, §2.6 (MemoryMax=2G)",
    "reproduced_in": ["open-params-cal-01", "open-params-cal-02", "open-params-cal-03"],
    "open_question": "10 OQ-11 -- boshqa MemoryHigh qiymatlari o'lchanmagan"
  }
},
"t_trial_s": 41.1
```

Muzlatish orkestratorning qarori; `timeout_start_sec` uchun bu hujjat
`calibration_required` ni yechishga **asos bermaydi**.

## 8. Pilot uchun boshqa topilmalar (mening fayllarim emas — faqat qayd)

1. **FAKT — host uyqusi `boot_id` ga ko'rinmaydi** (§0A). `boot_id` + pid1 markeri
   uyqu paytidagi muzlashni tutmaydi: trial ichidagi 11.7 soatlik muzlash
   monotonic vaqtda **0 s** bo'lib ko'rinadi. Uyg'onishdan keyingi guest init
   restart'ini esa pid1 tutadi. Pilotda har trial boshi va oxirida `real − mono`
   siljishi tekshirilishi kerak.
2. **FAKT — kalibrlangan `P2` da bosim ostidagi start'lar guard'ni uradi** (§6.3).
3. **Kod o'qishdan (o'lchanmagan):** `driver._pressure_properties()` generator
   unit'iga `WorkingDirectory` bermaydi; user manager'ning default ishchi katalogi
   `$HOME`. Guest'da `cd / && python3 -c "import revix"` → `ModuleNotFoundError`,
   va `systemctl --user show-environment` da `PYTHON*` o'zgaruvchisi **0** ta.
   Ya'ni `python3 -m revix.pressure` pilotda ishga tushmasligi mumkin. Driver
   bilan sinalmadi (`revix run` taqiqlangan); controller'im bu og'ishni o'zi
   qildi (modul izohi).
4. **Kod o'qishdan:** pilotda generator `max_seconds = ramp_s + hold_s = 18 s`
   (`run_trial`), ya'ni ~2.6 s o'z ramp'idan keyin ~15.4 s PI fazasi; mening
   epizodlarim 13 s (PI ≈ 10.4 s). §9.4 invariant 2 rejadagi `hold_s` ga
   qo'llanadi; PI fazasining haqiqiy uzunligi bilan munosabati ochiq savol.
5. §16.10(1) qiymatlarni *"`experiment/pressure-cal` tomonidan"* belgilashni
   aytadi; bu o'lchov `experiment/open-params` da bajarildi. Nom farqi —
   orkestratorning qarori.

## 9. CHEKLOV

- **Bitta kernel (`6.6.87.2-microsoft-standard-WSL2`), bitta dial (`192M`/`2G`,
  `base_mb` 160/184/184, nishon 0/0.30/0.60), bitta mashina.** Boshqa host'ga
  ko'chirilmaydi.
- **Faqat VM'siz host o'lchovi yaroqli.** Run'lar VirtualBox VM ishlamagan paytda
  bajarildi; VM bilan bir vaqtda olingan qayta o'lchov bu raqamlar bilan
  birlashtirilmasligi kerak.
- **G1 tekshirilmadi:** `δ` faqat `W = 5 s` da o'lchandi.
- **Bosim ichida boshlangan SUT ning watchdog oraliqlari o'lchanmadi:** A da SUT
  bosimdan 6 s oldin boshlanadi; pilotdagi arm `A` restart'i esa bosim ichida.
  B start'lari `READY` dan keyin darhol to'xtatiladi (ping yo'q).
- **Bystander va prober lab'da yo'q edi** (`10` ning dial kalibratsiyasi bilan
  taqqoslanadigan bo'lishi uchun); pilotda ikkalasi ishlaydi.
- **Epizod 13 s, pilot generatori 18 s** (§8(4)).
- **B namunasi kichik** (24/24/20) va dum barqaror emas (§3.1).
- **Ma'lumot uch run'dan**, run'lar orasida guest init restart (pid1) bo'ldi.
- `δ` ga systemd'ning ping qabul kechikishi kiradi (§2.2); post-pressure stall
  aniqligi 20 Hz.
- `memory_high` uchun yangi kalibratsiya bajarilmadi (§4).

## 10. Fayllar va qayta ishlab chiqarish

- Skriptlar: `scripts/open-params-run.sh`, `scripts/open-params-measure.py`,
  `scripts/open-params-analyze.py`.
- Ma'lumot: `datasets/open-params-cal-01/`, `datasets/open-params-cal-02/`,
  `datasets/open-params-cal-03/`, `datasets/open-params-smoke-01/` (xom fayllar
  `*.zst`, har birida `run_meta.json`); birlashtirilgan tahlil
  `datasets/open-params-cal-01/summary-combined-cal01-02-03.json` va
  `report-combined-cal01-02-03.txt`.
- `python3 scripts/open-params-analyze.py datasets/open-params-cal-01 datasets/open-params-cal-02 datasets/open-params-cal-03`
  `.zst` larni o'zi o'qiydi; uning chiqishi guest'dagi xom run'lardan olingan
  hisobot bilan bayt-bayt bir xil (md5 `d6132f779dd23161f011e11ce762ef4c`).
