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
