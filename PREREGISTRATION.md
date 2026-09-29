# REVIX — Pre-registration: PSI Pilot (P1)

| | |
|---|---|
| **Versiya** | `preregistration/v1.1` |
| **Holat** | MUZLATILGAN — kod yozishdan oldin commit qilindi |
| **Qamrov** | Faqat **pilot eksperiment P1**. Confirmatory eksperiment alohida pre-registration talab qiladi. |
| **Muzlatilgan sana** | 2026-09-29 (v1), 2026-09-29 (v1.1 amendment) |

Bu fayl `run_meta.preregistration_sha256` orqali har bir eksperiment run'iga bog'lanadi.
Fayl o'zgarsa — hash o'zgaradi, ya'ni qaysi ta'riflar ostida o'lchangani har doim aniqlanadi.

---

## Amendment log

Pre-registration **jimgina tahrirlanmaydi.** Har bir o'zgarish shu yerda
qayd etiladi, versiya oshiriladi, va oldingi versiyaning hash'i saqlanadi.
Shunda qaysi ta'riflar ostida o'lchangani har doim tekshirilishi mumkin.

### v1 → v1.1 (2026-09-29)

| | |
|---|---|
| **v1 sha256** | `0b1fdd18783bd27b22d0d64291eea657a83857f22af14a772d037dfd33075130` |
| **v1 git tag** | `v0.1.0-preregistration` |
| **Sabab** | systemd slice nomlash tuzog'i empirik aniqlandi |
| **O'zgardi** | faqat cgroup/slice **nomlari** |
| **O'zgarMADI** | hech bir ta'rif, chegara, metrika, statistik test yoki falsifikatsiya mezoni |
| **Yig'ilgan ma'lumot** | **yo'q** — hech qanday eksperiment ishga tushirilmagan edi |

**Nima aniqlandi:** systemd slice nomlarida `-` ierarxiya ajratuvchisi, demak
`a-b.slice` avtomatik `a.slice/a-b.slice` bo'lib joylashadi. Bu mashinada
empirik tasdiqlangan (`systemd-run --user --slice=revix-envcheck.slice` →
`.../revix.slice/revix-envcheck.slice`).

Natijada boshlang'ich `revix-harness.slice` nomi **sibling bo'lmaydi**, u
`revix.slice` ning childi bo'lib qolar edi — va harness'ning PSI'si
eksperiment slice'ining PSI'siga qo'shilib, §8.2 oldini olmoqchi bo'lgan
feedback artefaktini yaratardi. Ya'ni bu kosmetik emas, **validlik xatosi**.

| eski | yangi | roli |
|---|---|---|
| `revix.slice` | **`revixlab.slice`** | eksperiment (SUT, bystander, generator) |
| `revix-harness.slice` | **`revixmon.slice`** | harness (driver, prober, sampler, guard) |

Ikkisi ham `user@1000.service` ning to'g'ridan-to'g'ri childi, ya'ni haqiqiy
sibling. Service nomlaridagi dash muammo emas (faqat *slice* nomlari
ierarxiya hosil qiladi).

**Bu amendment qonuniy, chunki:** hali hech qanday ma'lumot yig'ilmagan, hech
qanday natija ko'rilmagan, va o'zgarish hech bir endpoint, chegara yoki testga
tegmaydi. Agar ma'lumot yig'ilgandan keyin o'zgarish kerak bo'lsa — bu yerga
yoziladi va **eski ma'lumot eski ta'riflar ostida qayta hisoblanadi**, yangi
ta'riflar ostida emas.

---

> **Nega bu fayl birinchi yoziladi?** REVIX ning ilmiy hissasi arxitektura emas, **o'lchov**.
> Agar hissa o'lchov bo'lsa, ta'riflar mahsulotning o'zi. Ta'riflarni natijani ko'rgandan keyin
> tanlash imkoniyati — bu ishni ilmiy jihatdan qiymatsiz qiladi.

---

## 0. Nima o'lchanmaydi (qamrovdan tashqari)

P1 quyidagilar haqida **hech qanday** da'vo qilmaydi:

- H2 (PSI-gating vs systemd native backoff) — A-vs-B taqqoslash P1 da **yo'q** (§6.3).
- REVIX arm C, failure classifier, action selector, `Repairs()` matritsasi.
- Host-wide (global `/proc/pressure`) pressure.
- 12 sekunddan uzoq sustained pressure.
- Nazorat qilinadigan IO stall (`io` controller delegated emas).
- Haqiqiy xizmatlar (SUT sintetik).

---

## 1. Vaqt disiplinasi

Barcha davomiylik **`CLOCK_MONOTONIC`, mikrosekund**da hisoblanadi.

Sabab: systemd'ning `*TimestampMonotonic` D-Bus property'lari va journald'ning
`__MONOTONIC_TIMESTAMP` aynan shu domenda. Bitta clock — konversiya yo'q, konversiya xatosi yo'q.

- Har bir record'da **`boot_id`**. Monotonic qiymatlar faqat bitta boot ichida taqqoslanadi;
  `boot_id` bu shartni tekshirib bo'ladigan qiladi.
- `CLOCK_REALTIME` (`real_us`) faqat inson o'qishi va tashqi log'lar bilan bog'lash uchun
  yoziladi. **Hech qanday davomiylik hisobida ishlatilmaydi.**
- `clock_getres` 1 ns beradi; yuk ostida amaliy aniqlik o'nlab µs. Bu barcha
  taqqoslashlar uchun yetarli, chunki eng kichik qiziqarli interval 100 ms (probe davri).

---

## 2. Service contract — VR ta'rifining asosi

SUT `sleep infinity` bo'lsa, quyidagi barcha ta'riflar process-liveness'ga qulaydi va
hissa yo'qoladi. Shuning uchun SUT maxsus yozilgan xizmat:

- `Type=notify`, `sd_notify` bilan `READY=1` va `WATCHDOG=1`
- `SOCK_SEQPACKET` unix control/probe socket
- deterministik ish tsikli, **monotonic progress counter** bilan
- har bir probe javobida `INVOCATION_ID` va pid echo qiladi

**Contract — uchta shart, hammasi bajarilishi kerak:**

| # | shart | parametr |
|---|---|---|
| a | socket `T_conn` ichida accept qiladi | `T_conn = 50 ms` |
| b | to'g'ri formatdagi javob `T_rt` ichida keladi | `T_rt = 50 ms` |
| c | `progress_counter` oldingi probe'dan **qat'iy katta** | — |

Probe davri **`P = 100 ms`** (10 Hz), absolut `CLOCK_MONOTONIC` deadline'larda.

---

## 3. Failure — ikki mustaqil detektor

Ikki detektor **alohida log'lanadi va hech qachon bitta raqamga birlashtirilmaydi.**

| detektor | manba | timestamp | nimani ko'rmaydi |
|---|---|---|---|
| `F_sd` | D-Bus: `ActiveState` ≠ `active`, yoki `Result` ≠ `success` | `ActiveExitTimestampMonotonic` / `InactiveEnterTimestampMonotonic` | hang (agar `WatchdogSec=` qo'yilmagan bo'lsa) |
| `F_probe` | prober: contract `k_f` marta ketma-ket buzildi | birinchi buzilgan probe'ning `mono_us_send` | hech narsa, lekin probe davriga kvantlangan |

**`k_f = 3`** → `D_f = 300 ms`. Sabab: bitta probe'dagi shovqinni (scheduling jitter,
socket backlog) failure deb hisoblamaslik.

### Injeksiya vaqti
`t_inject` = triggerlovchi chaqiruv qaytgandan keyingi monotonic vaqt, **ikki tomondan
bracket qilingan**: harness'ning `mono_us_before_call` / `mono_us_after_call`, **va**
SUT'ning o'z ichki "fault armed/fired" record'i.

Ramp fault'lar (leak, pressure) uchun qo'shimcha `t_fault_effective` = birinchi contract
buzilishi yoki `memory.events.oom_kill` ning birinchi o'sishi.

> **Ochiq cheklov:** `t_fault_effective` — **kuzatuv**, xizmat qachon nosog'lom bo'lgani
> haqidagi ground truth emas. Ramp fault'lar uchun service-level onset tabiatan noaniq;
> probe davri (100 ms) — e'lon qilingan noaniqlik chegarasi.

### Detection latency
`L_det = t_detect − t_fault_effective`, **har detektor uchun alohida** beriladi.

Clean crash uchun `L_det_sd` **manfiy** bo'lishi mumkin — systemd `SIGCHLD` orqali keyingi
probe'dan oldin biladi. Bu xato emas, ma'lumot: crash uchun systemd tezroq, hang uchun
prober yagona imkoniyat.

---

## 4. Verified Recovery (VR)

Epizod `E` verified-recovered, agar `[t_up, t_up + W_stab]` oynasi mavjud bo'lsa va unda:

1. `t_up` = `E` ning oxirgi action'idan keyingi birinchi contract'dan o'tgan probe;
2. oynadagi **har bir** probe contract'dan o'tadi;
3. `InvocationID` butun oyna davomida o'zgarmaydi (yashirin restart yo'q);
4. `NRestarts` butun oyna davomida o'zgarmaydi;
5. **oyna throughput'i ≥ `θ · R_ref`**, `R_ref` = shu trial'ning fault'dan oldingi throughput'i;
6. SUT cgroup'da yangi `memory.events.oom_kill` yo'q;
7. host guard ishlamagan.

**5-band VR ni process-liveness'dan ajratadigan narsa.** Qaytgan lekin 5% throughput'da
ishlayotgan xizmat recovered emas. Busiz butun hissa "process tirikmi?" ga qulaydi.

### Parametrlar
| parametr | qiymat | izoh |
|---|---|---|
| `θ` | **0.8** | pre-fault throughput'ning ulushi |
| `W_stab` | **60 s** (to'liq dizayn) | mexanik asos: λ tezlikdagi leak va M shift uchun refail vaqti ≈ M/λ; λ shunday tanlanadi-ki bu 15–25 s bo'ladi, demak 60 s ≥2 refail tsiklini qoplaydi |
| `W_stab_pilot` | **8 s** | oomd xavfsizlik oynasi (≤12 s) ichida sig'ishi kerak — §6.4 |

> **P1 dagi ochiq cheklov:** `W_stab_pilot = 8 s` bilan o'lchanadigan narsa —
> **"pressure davom etayotganda tasdiqlangan recovery"**, 60 s sustained recovery **emas**.
> To'liq `W_stab` root (system slice) yoki QEMU guest talab qiladi. Bu maqolada shunday
> yoziladi, yumshatilmaydi.

### Invalidator'lar (yopiq enum)
`contract_fail`, `invocation_changed`, `nrestarts_changed`, `oom_kill`,
`throughput_below_theta`, `guard_fired`.

**Probe uzilishi > 2×P** → trial `censored`, **`failed` emas**.
Instrumentatsiya yo'qolishi hech qachon jimgina natijaga aylanmaydi.

### Sensitivity sweep (oldindan e'lon qilingan)
`W_stab ∈ {8, 10, 30, 60, 120} s` × `θ ∈ {0.5, 0.8, 0.95}` — **raw probe trace'lardan
post-hoc hisoblanadi**, eksperiment qayta ishga tushirilmaydi.

Sabab: "siz `W` ni natija chiqishi uchun tanlagansiz" — har qanday shu turdagi metrikaga
birinchi hujum. Javob — bitta raqam emas, **butun egri chiziq**. Shuning uchun §8 raw
trace'larni saqlashni talab qiladi.

---

## 5. False Recovery — yangi metrika

**Ikki operatsion jihatdan farqli sub-metrika. Hech qachon bitta raqamga aralashtirilmaydi.**

### FR-A — muddatidan oldin muvaffaqiyat (oracle-free, BIRLAMCHI)

```
FR_A = 1   ⟺   actor_success_signal == true   AND   VR == false
```

`actor_success_signal` — **aktorning o'z da'vosi**:
- systemd uchun: unit `active` holatiga yetdi (`Type=notify` da `READY=1` qabul qilindi);
- REVIX uchun: engine `state=RECOVERED` chiqardi.

Ikkala operand ham **log'langan fakt**. **Oracle yo'q. Fault-class label yo'q. Matritsa yo'q.**

Har action uchun va har epizod uchun hisoblanadi (epizod darajasida = ≥1 FR-A action).

> **Loyihaning qoidasi:** dizayn shunday bo'lishi kerak-ki, agar reviewer FR-B ni butunlay
> chiqarib tashlasa ham, **FR-A yolg'on maqolani ko'tara oladi.**

### FR-B — action/fault mos kelmasligi (matritsaga nisbatan, IKKILAMCHI)

```
FR_B = 1   ⟺   action_class ∉ Repairs(injected_fault_class)   OR   harm_indicator == true
```

`harm_indicator` **o'lchanadi, da'vo qilinmaydi**. `[t_action_begin, t_action_begin + 5 s]`
ichida quyidagilardan biri:
- slice yoki host `memory.pressure` stall **tezligi** (`total=` delta'laridan) action'dan
  oldingi 5 s tezligidan **≥ 1.5×** oshdi; **yoki**
- o'rab turgan slice'da `oom_kill` oshdi; **yoki**
- bystander xizmat contract'ini yo'qotdi.

`Repairs()` **empirik kalibrlanadi, farmon bilan belgilanmaydi**: alohida kalibratsiya
eksperimenti har `(fault_class × action_class)` uchun `P̂(VR | f, a)` o'lchaydi, so'ng

```
Repairs(f) = { a : ClopperPearson_lower95( P̂(VR|f,a) ) ≥ p_min }
```

**`p_min = 0.7`** (oldindan muzlatilgan).

Kalibratsiya `VR` dan foydalanadi — u contract asosida va oracle-free — demak
sirkulyarlik yo'q.

> **FR-B nimani isbotlamaydi:**
> 1. Field'da fault **klassifikatsiya** haqida hech narsa. Injected label'lar ustidagi FR-B —
>    **mukammal klassifikatsiya sharti ostidagi yuqori chegara.**
> 2. Tashqi validlik: laboratoriya fault'lari toza va yolg'iz; real incident'lar murakkab va kaskadli.
> 3. `Repairs()` **bizning** action to'plamiga nisbatan. Action qo'shilsa matritsa o'zgaradi,
>    demak FR-B faqat bitta muzlatilgan matritsani baham ko'rgan arm'lar orasida taqqoslanadi.
>
> P1 da `Repairs()` **hisoblanmaydi** (kalibratsiya eksperimenti hali yo'q), demak
> **P1 da FR-B berilmaydi**. Faqat FR-A.

### 🚨 Sirkulyarlik — muzlatilgan kafolatlar

**PSI hech qanday ta'rifga kirmaydi. PSI faqat prediktor / kovariata.**

Boshlang'ich loyiha spetsifikatsiyasidagi FR ta'rifi — *"host memory exhaustion sababli
ishdan chiqqan xizmatni restart qilish"* — aynan tuzoq. FR ni shunday ta'riflab, keyin
"PSI gating FR ni kamaytiradi" deb "isbotlash" **tavtologiya**, natija emas.

To'rt kafolat, maqolada ochiq yoziladi:

1. **PSI failure, VR yoki FR ta'rifiga kirmaydi** — faqat prediktor sifatida.
2. **O'lchov prober'i hech bir arm'ning qaror yo'liga ulanmaydi**, uchala arm'da bir xil
   ishlaydi, va probe narxi arm'lar bo'yicha bir xil. (Agar arm C prober ishlatsa — u
   **alohida** process bo'ladi.)
3. `W_stab`, `θ`, `p_min` shu faylda oldindan muzlatilgan; sensitivity sweep e'lon qilingan.
4. **FR-A birlamchi va oracle-free; FR-B ikkilamchi va "matrix-relative" deb belgilanadi.**

---

## 6. Downtime va latency

### 6.1 Downtime — uchta ichma-ich o'lchov, hammasi beriladi

| o'lchov | qayerdan → qayerga | manba | nimani ko'rmaydi |
|---|---|---|---|
| `D_sd` | `ActiveExitTimestampMonotonic` → keyingi `ActiveEnterTimestampMonotonic` | D-Bus, µs | **ortiqcha kredit**: `active` ≠ to'g'ri xizmat qilayapti |
| **`D_probe`** (asosiy) | failure'dan oldingi oxirgi o'tgan probe → VR shartini qanoatlantiruvchi oynaning birinchi probe'i | prober | ±P kvantlash, har chekkada +P/2 bias — **e'lon qilinadi, jimgina "tuzatilmaydi"** |
| `D_eff` | `P·n_failing_probes + ∫ max(0, 1 − r(t)/R_ref) dt` | prober throughput | yo'q — **brownout'ni ham hisoblaydi** |

`D_eff` — C ning B dan halol ustun kelishi eng ehtimoliy joyi, va `D_sd` eng chalg'ituvchi
joyi: `active` lekin 20% throughput'dagi xizmat `D_sd` bo'yicha **nol** downtime ko'rsatadi.

### 6.2 Right censoring — tashlanmaydi, ishlanadi

`trial_downtime` = horizon `T_trial` ichidagi epizod downtime'larining yig'indisi.
Horizon tugasa va xizmat hali down bo'lsa → downtime **`T_trial` da censored**.

**Recovery bo'lmagan trial'larni tashlash — klassik yashirin bias**, va u tez ishdan
chiqadigan arm'ni chiroyli ko'rsatadi. Muzlatilgan qoida:

- censored trial'lar Kaplan–Meier / log-rank analiziga **kiradi**;
- censored trial'lar loop-rate metrikasiga **kiradi**;
- har bir jadvalda **"`T_trial` ichida recovered: k/n"** shartli vaqt taqsimoti bilan
  **birga** beriladi.

### 6.3 Latency — ikki soxta taqqoslashning oldini olish

**`L_dec = t_action_issue − t_detect`**, lekin **`policy_delay_us` (sozlangan kutish
vaqti) ALOHIDA field**.

> Sabab: B ning 10 s `RestartSec`ini "decision latency" deb hisoblab, keyin "C tezroq
> qaror qiladi" deyish — **soxta taqqoslash**. Arm'lar **downtime** bo'yicha taqqoslanadi,
> va downtime siyosat kechikishini haqli ravishda o'z ichiga oladi.

**`StartLimitBurst=0` (o'chirilgan) barcha arm'larda.** Give-up mantiqi harness'da,
hamma uchun bitta qoida.

> Sabab: aks holda arm A ning raqamlari systemd'ning start rate limiter'i bilan
> belgilanadi, va reviewer to'g'ri aytadi: "bu taqqoslash backoff haqida emas,
> `StartLimit` haqida."

**"Verification latency" achievement metrikasi sifatida BERILMAYDI** — muvaffaqiyatli VR
uchun u ta'rifan `W_stab`ga teng. O'rniga `time_to_first_up = t_up − t_detect`.

### 6.4 Recovery loop
`loop_rate = Δ NRestarts / T_trial`.
`loop_detected = 1` ⟺ `T_trial` ichida ≥5 invocation va **barchasi** VR dan o'tmagan.

---

## 7. Pressure o'lchovi — `total=` asosiy, `avgN` ikkilamchi

`avgN` (avg10/avg60/avg300) — eksponensial silliqlangan, **2 s kadensda yangilanadi**.
Fault boshlanishi failure'dan <2 s oldin bo'lsa, `avg10` umuman siljimasligi mumkin.

**`total=` (monotonik µs akkumulyator) atributsiya uchun qat'iy yaxshiroq va ASOSIY o'lchov:**

```
stall_fraction(t1, t2) = ( total(t2) − total(t1) ) / ( t2 − t1 )
```

Silliqlash yo'q, oyna mos kelmasligi yo'q.

**Muzlatilgan qarorlar:**

- Namuna olish: **4 scope** (host, `revixlab.slice`, SUT, bystander) × 3 resurs × {some, full},
  **10 Hz**, **har scope uchun alohida o'qish timestamp'i** (o'qishlar bir vaqtda emas —
  ularni bir vaqtda deb ko'rsatish xato bo'ladi).
- Pressure kovariatalari **hodisaga bog'langan interval'lar**, wall-clock'ga emas:
  `P_pre[Δ]` = `[t_fault_effective − Δ, t_fault_effective)`,
  `P_act[Δ]` = `[t_action_begin, t_action_begin + Δ)`,
  **Δ ∈ {0.5, 1, 2, 5, 10} s**.
- **Asosiy: `Δ = 2 s` pre-fault.** Qolgan Δ lar — sensitivity.
- **Asosiy scope: `revixlab.slice`** (per-service gate haqiqatan atributsiya qila oladigan scope).
  Host va SUT scope'lari — exploratory. Uchala scope × 3 resurs berilsa **Holm korreksiyasi**.
  **Ahamiyatlilik uchun scope bo'ylab "shopping" qilinmaydi** — reviewer taqqoslashlarni sanaydi.
- `avgN` ham yoziladi: (a) arzon deployed gate aynan shuni o'qiydi; (b) "laggy `avg10` gate
  vs aniq `total` gate" — bepul, o'z-o'zicha kichik natija.

> **Kvantlash ogohligi (muzlatilgan):** PSI ichki yangilanish kadensi 2 s va `total`
> partiyalarda kreditlanadi. Bitta 100 ms delta 0 o'qib, keyin sakrashi mumkin.
> **100 ms delta oniy tezlik deb talqin qilinmaydi.** Tezlik uchun ≥2 s oyna.

**Unprivileged PSI poll trigger ishlatilmaydi** — Linux 6.5+ da unprivileged trigger
oynasi 2 s karrasi bo'lishi shart. `total` polling ishlatiladi; trigger keyingi
optimizatsiya, dependency emas.

---

## 8. Confound nazorati (muzlatilgan)

### 8.1 Yashirin o'zgaruvchi — H1 ni o'ldiradigan e'tiroz

> *"`P(VR | high PSI)` past, chunki pressure sababi — restart'i baribir muvaffaqiyatsiz
> bo'ladigan memory leak'ning o'zi."*

Pressure va fault class **konstruksiya bo'yicha** confound. Ikki majburiy yechim:

1. **H1 fault class ICHIDA sinaladi.** Pooled analiz ta'rifan confounded.
2. **Pressure ekzogen va ortogonal injeksiya qilinadi** — fault class'dan **mustaqil**
   randomizatsiya qilingan, SUT'ning fault'iga aloqasi yo'q generatordan.

→ **`clean_crash × exogenous pressure` — H1 ning eng toza testi va P1 ning asosiy
yacheykasi.** `clean_crash` tinch holatda p≈1 bilan restart'dan tuzaladi va o'zi pressure
yaratmaydi; demak pressure'ni o'zgartirish **pressure'ning sababiy ta'sirini izolyatsiya
qiladi.** Manipulyatsiyasiz PSI-vs-natija faqat korrelyatsion bo'ladi.

### 8.2 O'z perturbatsiyasi
Restart CPU/xotira/IO iste'mol qiladi → PSI ni **oshiradi**. Gate PSI o'qisa va action PSI ni
oshirsa — feedback loop va artefakt.

- Harness (**driver, prober, psi_sampler, guard**) **sibling slice**da: `revixmon.slice` (dash'siz nom — Amendment log'ni ko'ring).
  Kovariata sifatida ishlatiladigan hech bir scope ichida emas.
- Harness'ning o'z `CPUUsageNSec` / `MemoryPeak` log'lanadi va hisobotda beriladi.
- **Probe narxi budjeti:** prober CPU'si trial bo'yicha o'lchanadi, yadro foizida beriladi.
  >1% bo'lsa sekinlashtiriladi. **Arm'lar bo'yicha bir xil ushlanadi.**
- **No-action arm MAJBURIY**, opsional emas: (i) injeksiya + `Restart=no`, (ii) injeksiya yo'q —
  har pressure darajasida. Busiz "restart PSI ni oshirdi" ni "fault PSI ni oshirdi" dan
  ajratib bo'lmaydi va `harm_indicator` talqin qilinmaydi.

### 8.3 Page cache / warm-cold
P1 da cache **iliq va barqaror ushlanadi** (har trial'dan oldin SUT fayllariga fiksa teginish).
**Cold start P1 qamrovidan tashqarida.** `drop_caches` root talab qiladi va butun ish
stansiyasini buzadi — **qilinmaydi**.

Kovariata sifatida log'lanadi: `memory.stat` (`pgmajfault`, `pgscan_*`, `pgsteal_*`,
`workingset_*`), host `MemAvailable`, trial boshidagi page cache hajmi, **trial indeksi**
(monoton drift testi uchun).

### 8.4 Randomizatsiya va washout

**Randomized complete block design.** Blok = har `(arm × pressure)` yacheykadan **aynan
bitta** trial, blok ichida **seeded RNG** bilan aralashtirilgan (seed `run_meta` da).
`n` blok ⇒ yacheykaga `n` replika, va blok sekin drift'ni (kun vaqti, cache holati, termal)
o'ziga singdiradi.

**Washout ketma-ketligi (muzlatilgan):**
1. `revixlab.slice/cgroup.kill` ga `1` yozish — atomik subtree kill;
2. slice `memory.current` baseline ±ε ga qaytishini kutish;
3. slice **va** host stall tezliklari quiescence chegarasidan past bo'lishi, `T_q = 5 s` davomida;
4. qattiq pol **`T_w = 15 s`**, cap **`T_w_max = 120 s`** → `washout_timeout`, trial chiqariladi.

> Agar analiz `avg300` ishlatganda washout ≈300 s bo'lishi kerak edi.
> `total`-asosli interval o'lchovlari washout'ni **15 s** qiladi — umumiy kampaniya
> vaqtidan bir daraja. Bu o'lchov qaroridan kelib chiqqan dizayn foydasi.

### 8.5 DVFS / termal
CPU: `amd-pstate-epp`, governor `powersave`. Sustained yuk chastotani pasaytiradi, demak
yuk ostidagi response-time o'lchovlari kontentsiya bilan DVFS ni aralashtiradi.

- Yumshatish: blok ichida randomizatsiya.
- Har trial chegarasida `scaling_cur_freq` (har CPU) va `thermal_zone*/temp` log'lanadi;
  o'rtacha chastota kovariata.
- **Agar chastota arm bo'yicha tizimli farq qilsa, timing taqqoslashlari haqiqiy emas** —
  bu tekshiriladi va hisobotda beriladi.

---

## 9. P1 dizayni

### 9.1 Yagona savol

> **Ekzogen** injeksiya qilingan memory pressure, systemd'ning o'z `Restart=on-failure` i
> bilan restart qilinadigan **oson tuzatiladigan** fault (clean crash) uchun `P(VR)` ni
> kamaytiradimi va time-to-VR ni oshiradimi?

Bu yacheyka **REVIX engine'ini umuman talab qilmaydi** — arm'lar shunchaki systemd
config'lari. **H1 dunyo haqidagi da'vo, REVIX haqida emas.**

### 9.2 Mexanizm — oldindan aytilgan
Tinch holatda `P(VR | clean_crash, restart) ≈ 1.0`. Pressure ostida pasayishi mumkin
bo'lgan sanab o'tiladigan yo'llar:

| # | mexanizm | log'da izi |
|---|---|---|
| i | `TimeoutStartSec` oshib ketdi | `Result=timeout` |
| ii | start paytida OOM-kill | `memory.events.oom_kill` +1, `Result=oom-kill` |
| iii | start bo'ldi lekin throughput < `θ·R_ref` — **brownout** | `throughput_below_theta` invalidator |
| iv | scheduling delay'dan watchdog miss | `Result=watchdog` |

> **(iii) eng ehtimoliy signal manbasi, va u FAQAT VR ta'rifida throughput bandi (§4.5)
> borligi uchun mavjud.** Xulosa, oldindan yozilgan: **liveness-only VR ta'rifi ehtimol
> null pilot beradi, va bu null — ta'rif artefakti, H1 ga qarshi dalil EMAS.**

### 9.3 Faktorlar va arm'lar

| | |
|---|---|
| **Arm'lar** | `A` (`Restart=on-failure`, `RestartSec=100ms`) va `no_action` (`Restart=no`) |
| **Fault** | faqat `clean_crash`, trial'ga bitta injeksiya |
| **Pressure** | `P0` (generator idle), `P1` (~20–35% slice stall), `P2` (~60–80%) |
| **Bloklar** | 20 |
| **Trial'lar** | 3 × 2 × 20 = **120** |

**Baseline B (`RestartSteps=`) P1 da YO'Q.** Sabab: B ning `RestartSec=10s` xavfsiz
pressure oynasidan (12 s) oshadi — B ning restart'i hold oxirida tushar va stabilizatsiya
oynasi pressure'dan **tashqarida** qolar edi. A va B restart paytida taqqoslanadigan
pressure'ga tushmaydi. **A-vs-B — bu H2 va confirmatory eksperimentga tegishli.**

### 9.4 Pressure dosing
Generator **closed-loop PI controller** bilan slice'ning `total`-asosli 2 s stall tezligini
nishon bandida ushlaydi.

**Analiz ERISHILGAN (uzluksiz) pressure'dan foydalanadi, mo'ljallangan darajadan emas.**
Natija: ta'sir qilmagan treatment trial'ni buzmaydi — u kovariataga aylanadi; va kategorik
dizayn bir xil `n` da kuchliroq regressiyaga aylanadi.

**Trial jadvali:** pre-flight → `R_ref` baseline 10 s → ramp 5 s → hold, injeksiya hold'ga
3 s kirgach → **umumiy pressure-on ≤ 12 s** → washout ≥20 s.
≈75 s/trial ⇒ **≈2.5 soat**.

---

## 10. Statistik tahlil (muzlatilgan)

### 10.1 H1 birlamchi endpoint — `P(VR)` pressure stratalari orasida, fault class ichida

- **Birlamchi test: Cochran–Armitage trend testi** `P0 < P1 < P2` bo'ylab.
  Sabab: tartibni ishlatadi (pairwise'dan ancha kuchli), va *"`P(VR)` pressure bilan
  monoton kamayadi"* — *"yuqori < past"* dan kuchliroq, ko'proq falsifiable da'vo.
- 2×2 uchun **Fisher exact** (yoki ko'proq power uchun Barnard).
- **Effect size: risk difference + Newcombe/Wilson-score CI** (birlamchi, downtime
  argumenti uchun eng talqin qilinadigan). Risk ratio va OR ikkilamchi.
  Har yacheyka proporsiyasi uchun **Clopper–Pearson exact CI**.
- Uzluksiz versiya: `logit P(VR) ~ P_pre[2s] + block` — **qo'llab-quvvatlovchi, birlamchi
  emas**. Kichik `n` da ortiqcha modellashtirish qilinmaydi.

### 10.2 Downtime / recovery-time taqsimotlari

Bu taqsimotlar og'ir dumli, ehtimol bimodal ("birinchi urinishda" vs "k loop'dan keyin"),
va o'ngdan censored.

- **`t-test` ISHLATILMAYDI. `mean ± SD` BERILMAYDI.**
- **Birlamchi: Kaplan–Meier time-to-VR har arm uchun, log-rank bilan taqqoslash** —
  censoring'ni to'g'ri ishlaydigan yagona oila.
- **Cox / hazard ratio ISHLATILMAYDI** — hazard'lar proporsional bo'lmasligi deyarli aniq
  (fiksa kechikishlar step hazard yaratadi). Schoenfeld residual'lari tekshirilmasa,
  HR berilmaydi.
- **Effect measure: RMST difference** τ horizon'ga qadar — non-proportional hazard ostida
  haqiqiy, va to'g'ridan-to'g'ri *"τ sekund ichida tejalgan kutilgan downtime"* sifatida
  o'qiladi. **Bu mavjud eng yaxshi statistik tanlov va H2 ga to'g'ridan-to'g'ri javob beradi.**
- Ikkilamchi (censored bo'lmagan qism ustida): Mann–Whitney U, Kruskal–Wallis + Dunn;
  effect size **Cliff's δ** / A₁₂ bootstrap CI bilan.
- **median, p90, p99 + BCa bootstrap CI** — dum xatti-harakati muhim; p99 downtime
  operatorlar uchun ahamiyatli.
- Blokdan foyda: per-blok farqlarda **Wilcoxon signed-rank**, yoki blok-stratifikatsiyalangan
  log-rank.
- Restart/loop soni: **negative binomial** (Poisson overdispersion sababli xato bo'ladi),
  yoki tezlik farqining nonparametrik bootstrap'i.
- ECDF'lar to'liq chizilib beriladi — har qanday bitta testdan ishonchliroq.

### 10.3 Implementatsiya
`statsmodels` va `lifelines` mavjud emas. `scipy` Fisher, Mann–Whitney, Kruskal–Wallis va
bootstrap'ni qoplaydi. Cochran–Armitage ~10 qator; KM + log-rank + RMST ~100 qator numpy.

**Dependency qo'shmasdan o'zimiz yozamiz**, va **nashr etilgan ishlangan misolga qarshi
unit-test** qilamiz. Self-contained artifact reviewer uchun tejalgan mehnatdan qimmatroq.

### 10.4 Multiplicity
Pre-registered per-class birlamchi testlar bo'ylab **Holm–Bonferroni**. P1 da bitta fault
class bor (`clean_crash`), demak bitta birlamchi test; scope/Δ sweep'lari **exploratory**
deb belgilanadi.

---

## 11. Falsifikatsiya va davom etish mezonlari

**Ishga tushirishdan OLDIN muzlatilgan.**

### H1 ning kuchli shakli bu yacheykada YOLG'ON, agar:
- Cochran–Armitage trend testi `P0 < P1 < P2` bo'ylab **ahamiyatsiz** (p > 0.05); **VA**
- `P(VR|P0) − P(VR|P2)` uchun 95% Newcombe CI ning **yuqori chegarasi < 0.15**
  (ya'ni 15 punktdan katta effekt inkor qilinadi).

Bir vaqtda, fail-slow shakli qo'llab-quvvatlanmaydi, agar `P0` va `P2` orasidagi
time-to-VR RMST farqi (τ = 8 s) uchun 95% CI 20% oshishni chiqarib tashlasa.

### Halol power bayonoti (oldindan majburiyat)
`n = 20`/daraja Fisher exact bilan `1.00 → ~0.65` ni ≈80% power bilan aniqlaydi.
**`1.00 → 0.90` ni aniqlamaydi.**

> **Null pilot faqat KATTA effektni inkor qiladi va H1 ning kuchsiz shaklini
> yolg'onga chiqarmaydi.** Bu o'qish oldindan qabul qilinadi — natijadan keyin
> qayta talqin qilinmaydi.

### Davom etish mezoni (biri yetarli)
- **(a)** trend p < 0.05 **va** risk difference ≥ 0.15;
- **(b)** `D_eff` `P2` da ≥1.5× `P0`, bootstrap CI 1.0 ni chiqarib tashlaydi;
- **(c)** mexanizm log'larida faqat `P2` da paydo bo'ladigan takrorlanuvchi yo'l
  (masalan `Result=timeout`), agregat tezliklar deyarli siljimasa ham.

> **(c) sifatiy va ehtimol eng qimmatli pilot natijasi, chunki u mexanizmni NOMLAYDI.**
> Nomlangan mexanizm H1 ni korrelyatsiyadan nazariyaga aylantiradi.

### Null bo'lsa — oldindan belgilangan burilish
Binar endpoint null bo'lsa: **restart pressure ostida sekinroq va degradatsiyalangan
bo'ladimi** — `D_eff` orqali. Kuchsizroq, lekin hali nashr qilinadigan da'vo, va
**xuddi shu ma'lumotdan** tekshiriladi. Binar null — o'lik yo'l emas.

---

## 12. Trial disposition — yopiq enum

Har trial'ga **aynan bitta** disposition. Bu jimgina eksklyuziyaning oldini oladi.

| disposition | ma'nosi |
|---|---|
| `complete` | to'liq o'lchandi, birlamchi analizga kiradi |
| `censored` | probe uzilishi >2×P, yoki horizon down holatda tugadi |
| `contaminated` | biz yubormagan `SIGKILL`, biz cheklamagan cgroup'da `oom_kill`, yoki bystander buzildi |
| `aborted_guard` | host guard ishga tushdi |
| `washout_timeout` | washout `T_w_max` ichida yakunlanmadi |
| `harness_error` | harness istisnosi |

**`contaminated` va `aborted_guard` trial'lar birlamchi analizdan chiqariladi, LEKIN
ularning ulushi natija sifatida beriladi.** Yuqori eksklyuziya darajasi o'zi natija —
yashirilmaydi.

---

## 13. Bu pre-registration NIMANI muzlatmaydi

Quyidagilar **keyinchalik** aniqlanadi va **o'z pre-registration'ini** talab qiladi:
- Confirmatory eksperiment `n` (P1 effect size'ini baholagandan keyin hisoblanadi)
- `Repairs()` matritsasi (kalibratsiya eksperimentidan)
- Arm C (REVIX) siyosati va gate chegaralari
- `pressure_pulse_duration` faktor darajalari (H2 uchun kritik)
- Fault taxonomiyasining qolgan 8 klassi

**P1 ma'lumotlari confirmatory analizga QO'SHILMAYDI.** P1 — effect size baholash va
mexanizm aniqlash uchun; u hipotezani sinash uchun ishlatilsa, keyin yana bir xil
hipotezani sinash — garden of forking paths.
