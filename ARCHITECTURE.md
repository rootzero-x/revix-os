# ARCHITECTURE — REVIX harness arxitekturasi

> **Bu hujjat spetsifikatsiya EMAS.** Muzlatilgan ta'riflar, metrikalar,
> chegaralar va statistik reja [`PREREGISTRATION.md`](PREREGISTRATION.md) da;
> wire protokol [`docs/architecture/03-sut-protokoli.md`](docs/architecture/03-sut-protokoli.md) da;
> o'lchangan kalibratsiya natijalari
> [`docs/architecture/02-guard-kalibratsiyasi.md`](docs/architecture/02-guard-kalibratsiyasi.md) da.
> Bu fayl komponentlar **qanday birlashtirilgani** va **nega aynan shunday**
> ekanini tushuntiradi. Raqamlar va ta'riflar shu yerda **takrorlanmaydi** —
> takrorlangan spetsifikatsiya bir-biridan uzoqlashadi, keyin qaysi biri
> haqiqiy ekani noaniq bo'ladi.

**Holat (halol):** hech qanday eksperiment ishga tushirilmadi, hech qanday
natija yo'q. Quyida tasvirlangan narsa — commit qilingan va unit test bilan
qoplangan kod, plus muzlatilgan hujjatlar. Kalibratsiya va muhit tekshiruvlari
ishga tushirilgan (`docs/architecture/01`, `02`); **pilot eksperiment yo'q.**

---

## 1. Komponent xaritasi

| Komponent | Fayl | Roli | Holat |
|---|---|---|---|
| **SUT** | [`revix/sut.c`](revix/sut.c) | o'lchanadigan sintetik xizmat: `SOCK_SEQPACKET` socket, monoton `progress` hisoblagichi, 8 fault endpoint'i, `sd_notify` + watchdog | ✅ bor, test bilan |
| SUT build | [`revix/Makefile`](revix/Makefile) | bog'liqliksiz build, `-Werror` | ✅ bor |
| **Prober** | [`revix/prober.py`](revix/prober.py) | 10 Hz contract o'lchovi, `F_probe` failure detektori, `probe_sample` oqimi | ✅ bor, test bilan |
| **PSI sampler** | [`revix/psi_sampler.py`](revix/psi_sampler.py) | bir necha scope × 3 resurs × {some, full}, 10 Hz, scope bo'yicha alohida o'qish timestamp'i | ✅ bor |
| **Pressure generator** | [`revix/pressure.py`](revix/pressure.py) | ekzogen memory pressure: churn impulsi + PI controller; `ramp` rejimi guard testi uchun | ✅ bor, test bilan |
| **Guard** | [`revix/guard.py`](revix/guard.py) | MUSTAQIL xavfsizlik jarayoni, fail-closed, `cgroup.kill` bilan teardown | ✅ bor, test bilan |
| cgroup/PSI qatlami | [`revix/cgroup.py`](revix/cgroup.py) | cgroup v2 o'qish/yozish, PSI parse, `total=` dan stall tezligi | ✅ bor, test bilan |
| Schema + yozuvchilar | [`revix/schema.py`](revix/schema.py) | record envelope, oqim bo'yicha `seq`, JSONL (`O_APPEND`) va CSV yozuvchilar, disposition enum'i | ✅ bor, test bilan |
| Guard integratsiya testi | [`scripts/guard-test.sh`](scripts/guard-test.sh) | uchdan-uchiga: guard + sampler + haqiqiy pressure, keyin kollateral zarar tekshiruvi | ✅ bor |
| **Driver** | — | trial jadvalini yurituvchi, unit'larni `systemd-run` bilan yaratuvchi, disposition qaror qiluvchi | ⏳ **REJADA** |
| Validator | — | analizdan oldin majburiy tekshiruv (`seq` bo'shliqlari, `boot_id`, envelope) | ⏳ **REJADA** |
| Reducer | — | raw → derived record'lar (`D_probe`, `D_eff`, VR, FR-A) | ⏳ **REJADA** |
| Statistika | — | Cochran–Armitage, Fisher, KM + log-rank + RMST, bootstrap | ⏳ **REJADA** |

> **Rejadagi komponentlar hali mavjud emas** va bu hujjat ularning
> xatti-harakatini tasvirlamaydi. `PREREGISTRATION.md` §10.3 statistikani
> bog'liqlik qo'shmasdan o'zimiz yozishni va nashr etilgan ishlangan misolga
> qarshi unit-test qilishni talab qiladi.

### Jarayon chegaralari

Har bir komponent **alohida jarayon**, va bu ataylab:

```
revixmon.slice                          revixlab.slice
├── guard        (mustaqil, birinchi)    ├── revix-sut.service
├── prober       (o'lchov)               ├── revix-bystander.service
├── psi_sampler  (o'lchov)               └── revix-press.service
└── driver       (rejada)
```

- **Guard driver'dan mustaqil**, chunki qotib qolgan driver guard'ni o'chira
  olmasligi kerak ([`revix/guard.py`](revix/guard.py) dizayn qoidasi 1).
- **Prober hech bir arm'ning qaror yo'liga ulanmaydi** — `PREREGISTRATION.md`
  §5 sirkulyarlik kafolati 2. Arm C keyinchalik probe'ga muhtoj bo'lsa, u
  **alohida** process bo'ladi.
- Prober va sampler o'lchaydi, **qaror qilmaydi**. Qaror (disposition, VR,
  FR-A) driver va reducer'da, ya'ni o'lchovdan keyin va o'lchovdan tashqarida.

---

## 2. cgroup topologiyasi va nega harness sibling slice'da

To'liq topologiya, `MemoryMax`/`CPUQuota`/`TasksMax` qiymatlari bilan:
[`docs/architecture/00-pilot-topologiya.md`](docs/architecture/00-pilot-topologiya.md) §1.

Qisqasi: `user@1000.service` ning ikki **sibling** childi bor —
`revixlab.slice` (o'lchanadigan narsa) va `revixmon.slice` (o'lchovchi narsa).

### Nega harness o'lchanayotgan scope ICHIDA emas

Restart CPU, xotira va IO iste'mol qiladi → PSI ni **oshiradi**. Agar harness
`revixlab.slice` ichida bo'lsa, prober va sampler'ning o'z resurs sarfi
kovariata sifatida ishlatiladigan PSI ga **qo'shilib ketadi**. Natija —
feedback loop: gate PSI ni o'qiydi, action PSI ni oshiradi, va o'lchov o'z
perturbatsiyasini o'lchaydi. `PREREGISTRATION.md` §8.2 aynan shuni taqiqlaydi.

Shuning uchun:
- harness `revixmon.slice` da, kovariata bo'lgan hech bir scope ichida emas;
- harness'ning o'z `CPUUsageNSec`/`MemoryPeak` log'lanadi va hisobotda beriladi;
- prober o'z CPU narxini **o'zi o'lchaydi** va `prober_stop` record'iga yozadi
  (`Prober.cost_report()`), budjet — bir yadroning 1% i (`PREREGISTRATION.md` §8.2);
- probe narxi arm'lar bo'yicha **bir xil** ushlanadi, aks holda arm'lar
  instrumentatsiya yuki bo'yicha farq qiladi.

### ⚠️ Slice nomlash tuzog'i — qayta kiritilmasligi kerak

**systemd slice nomlarida `-` ierarxiya ajratuvchisi.** `a-b.slice`
avtomatik `a.slice/a-b.slice` bo'lib joylashadi, va systemd oraliq `a.slice`
ni **o'zi yaratadi**.

Bu shu mashinada empirik aniqlangan
([`docs/architecture/01-muhit-tekshiruvlari.md`](docs/architecture/01-muhit-tekshiruvlari.md) §2):
`--slice=revix-envcheck.slice` → `.../user@1000.service/revix.slice/revix-envcheck.slice`.

Natijasi: rejadagi `revix-harness.slice` nomi **sibling bo'lmaydi**, u
`revix.slice` ning childi bo'lib qoladi → harness PSI'si eksperiment
slice'ining PSI'siga qo'shiladi → §8.2 oldini olmoqchi bo'lgan feedback
artefakti aynan yuzaga keladi.

**Bu kosmetik xato emas, validlik xatosi.** Shuning uchun pre-registration
v1 → v1.1 amendment qilindi va nomlar dash'siz:

| eski (xato) | yangi (to'g'ri) |
|---|---|
| `revix.slice` | `revixlab.slice` |
| `revix-harness.slice` | `revixmon.slice` |

Service nomlaridagi dash muammo emas (`revix-sut.service` `--slice=` ko'rsatgan
joyga tushadi) — faqat **slice** nomlari ierarxiya hosil qiladi.

Kodda bu tuzoq [`revix/cgroup.py`](revix/cgroup.py) `user_child()`
docstring'ida qulflangan va `tests/unit/test_cgroup.py::test_user_child_dash_siz_nom`
bilan test qilingan. **Yangi slice nomi qo'shsangiz — dash ishlatmang.**

---

## 3. Ma'lumot oqimi: raw → derived

```
  SUT (sut.c)                     cgroup v2 / PSI fayllari
      │ PROBE/javob                        │ pread(fd, 0)
      ▼                                    ▼
  prober.py                          psi_sampler.py            guard.py
      │                                    │                      │
      ├─ probe_sample  (CSV, 10 Hz/target) ├─ psi_sample (CSV)    ├─ guard_event
      └─ detection / harness_error /        └─ sampler_start/stop  ├─ guard_start/stop
         contract_restored / prober_*         psi_scope_unavailable └─ trip.json
         (JSONL)                              (JSONL)
                          │
                          ▼
                 datasets/  ← APPEND-ONLY, hech qachon ustiga yozilmaydi
                          │
                          ▼
                 validator (rejada)  — o'tmasa analiz qilinmaydi
                          │
                          ▼
                 reducer (rejada)  → derived record'lar:
                          VR, FR-A, D_sd / D_probe / D_eff, L_det,
                          time_to_first_up, loop_rate, disposition
                          │
                          ▼
                 statistika (rejada)
```

### Nega ikki format

- **CSV** — fiksa sxemali yuqori tezlikli oqimlar uchun (`probe_sample`,
  `psi_sample`). `revix/schema.py` `CsvWriter` docstring'i bu ikki oqim uchun
  ~1–2M qatorni mo'ljallaydi; JSONL bunda
  ~5–10× bayt va ~3–5× parse vaqti talab qilardi, va serializatsiyaga ketgan
  CPU — **eksperimentdan o'g'irlangan CPU**
  ([`revix/schema.py`](revix/schema.py) `CsvWriter` docstring).
- **JSONL** — hodisa record'lari uchun (`detection`, `guard_event`,
  `harness_error`, `*_start`/`*_stop`): sxemasi bir xil emas va hajmi kichik.

CSV da `run_id`/`boot_id` **yo'q** — fayl `prober_start` / `sampler_start`
record'i orqali run'ga bog'lanadi (u envelope'da `run_id`, `boot_id` va
`csv_path` ni beradi).

### Yo'q qiymat va nol qiymat aralashtirilmaydi

`CsvWriter` `None` ni **bo'sh maydon** sifatida yozadi, 0 yoki NaN sifatida
emas. `cgroup.read_text()` o'qilmagan faylga `None` qaytaradi. Sabab bitta:
**0 — haqiqiy o'lchov qiymati**, demak "o'lchanmadi" ni "nol o'lchandi" ga
aylantirish ma'lumotni jimgina buzadi.

---

## 4. O'lchov validligini himoya qiluvchi dizayn qarorlari

Bu bo'lim hujjatning asosiy qismi: har bir qaror **nima buzilishining oldini
olgani** bilan birga yozilgan. Sababsiz qoida keyinchalik "soddalashtirib"
yo'q qilinadi.

### 4.1 `total=` asosiy, `avgN` ikkilamchi

PSI `avgN` (avg10/avg60/avg300) eksponensial silliqlangan va **2 s kadensda**
yangilanadi. Fault failure'dan <2 s oldin boshlansa, `avg10` umuman
siljimasligi mumkin — ya'ni atributsiya qilib bo'lmaydi.

`total=` — monotonik mikrosekund akkumulyator, demak aniq interval o'lchovi
beradi:

```
stall_fraction(t1, t2) = ( total(t2) − total(t1) ) / ( t2 − t1 )
```

Silliqlash yo'q, oyna mos kelmasligi yo'q. To'liq asoslash:
`PREREGISTRATION.md` §7.

Kodda: [`revix/cgroup.py`](revix/cgroup.py) `stall_fraction()`.

**Kvantlash qoidasi qattiq kodlangan:** oyna 2 s dan qisqa bo'lsa funksiya
`None` qaytaradi. PSI `total` ni partiyalarda kreditlaydi, demak bitta 100 ms
delta 0 o'qib keyin sakrashi mumkin — **100 ms delta oniy tezlik emas.**
Guard ham (`guard.py`), PI controller ham (`pressure.py`) shu bir xil
funksiyadan foydalanadi, ya'ni qoida bitta joyda.

**Eng tor ≥2 s oyna tanlanadi, eng eskisi emas.** Kalibratsiyada eng eski
namuna tanlanardi va oyna 2–8 s orasida suzardi (o'lchangan: 4.9 s) — tezlik
silliqlanib, guard sekinlashardi, ya'ni `avgN` dan qochish maqsadi buzilardi.
Tuzatish [`docs/architecture/02-guard-kalibratsiyasi.md`](docs/architecture/02-guard-kalibratsiyasi.md) §2
da qayd etilgan va `tests/unit/test_guard.py::test_tezlik_oynasi_eng_tor_2s_ni_tanlaydi`
bilan qulflangan.

### 4.2 Absolut deadline'da pacing — `sleep(P)` ishlatilmaydi

`sleep(P)` har tsiklda ishning o'z narxini davrga qo'shadi, ya'ni haqiqiy
davr P dan katta bo'ladi va **xato yig'iladi**. Buning ikki alohida oqibati
bor:

1. **Prober:** `D_probe` ±P kvantlash bilan e'lon qilinadi
   (`PREREGISTRATION.md` §6.1). Davr sekin-asta siljisa, kvantlash bayonoti
   yolg'on bo'lardi. Shuning uchun keyingi deadline hisoblanadi va faqat
   **qolgan** vaqt uxlanadi. Butun slot yo'qolsa faza **saqlanib** butun P
   karralari bilan oldinga siljiydi — grid P ga tekis qoladi, demak yo'qolgan
   tsikllar butun P sifatida sanaladi (`Prober.run()`, `probe_overrun`
   record'i). `<P` kechikish uchun butun namuna tashlanmaydi.
2. **SUT ish tsikli:** kechikilsa deadline **qayta tiklanadi**, yo'qolgan
   iteratsiyalar quvib yetilmaydi. Quvib yetish stall'ni burst bilan
   yashirib, aynan `PREREGISTRATION.md` §4 ning 5-bandi o'lchaydigan
   throughput pasayishini ko'rinmas qilardi (`sut.c` `work_loop()`).

Xuddi shu qoida `guard.py` va `psi_sampler.py` asosiy tsikllarida ham.

### 4.3 Oqim bo'yicha `seq` — jimgina yo'qotish imkonsiz

[`revix/schema.py`](revix/schema.py) `Emitter` har **oqim** uchun alohida
monoton `seq` yuritadi. Prober'da oqim `probe_sample:<target>`, ya'ni har
target'ning trace'i alohida sanaladi.

Nega muhim: `PREREGISTRATION.md` §4 "probe uzilishi > 2×P → trial
`censored`, **`failed` emas**" deydi. Bu qaror aynan shu trace'dagi
bo'shliqqa qaraydi. `seq` bo'shligi bo'lmasa, yo'qolgan probe "failure" deb
o'qilardi va instrumentatsiya yo'qolishi jimgina **natijaga** aylanardi.

Shu sababli prober instrumentatsiya xatosida CSV qatorini **yozmaydi** va
`seq` bo'shligi **ataylab** qoldiriladi: yo'qolgan probe ko'rinadigan bo'lishi
kerak.

### 4.4 Instrumentatsiya xatosi ≠ xizmat failure'i

Prober'dagi errno tasnifi — qaror jadvali, tasodif emas:

| guruh | misol | natija |
|---|---|---|
| xizmat ulanishni bermadi | `ECONNREFUSED`, `ENOENT` | `conn_refused` (contract bandi a) |
| xizmat accept qilib yetishmadi | `ETIMEDOUT`, `EAGAIN` | `conn_timeout` (bandi a) |
| **prober'ning o'z muammosi** | `ENOMEM`, `ENOBUFS`, `EMFILE`, `EACCES` | **`harness_error`** |
| tanilmagan errno | — | **`harness_error`**, jimgina `conn_refused` emas |

Sabab: pressure ostida prober'ning o'zi socket ajratolmasligi **real xavf**.
Uni `conn_refused` deb yozish natijani aynan H1 foydasiga siljitardi —
`PREREGISTRATION.md` §8.1 dagi yashirin o'zgaruvchi e'tirozining eng arzon
shakli. `harness_error` ketma-ket buzilish hisoblagichiga **tegmaydi**.

### 4.5 `progress` hisoblagichi — hissaning tayanchi

`PREREGISTRATION.md` §4 ning 5-bandi (throughput ≥ θ·R_ref) — VR ni oddiy
process-liveness'dan ajratadigan **yagona** narsa. U `progress` ga tayanadi,
demak `sut.c` da uchta qoida buzilmaydi:

1. `progress` **faqat** ish tsiklida oshadi, iteratsiyaga aynan +1. Probe
   javobi hech qachon oshirmaydi — aks holda o'lchov o'zini o'lchagan bo'lardi.
   Test: `tests/unit/test_sut.py::test_probe_progressni_shishirmaydi`.
2. Bitta iteratsiya = **deterministik doimiy CPU ishi** (fiksa sonli
   arifmetik rounds `volatile` akkumulyator ustida; IO yo'q, ajratish yo'q),
   shunda `Δprogress/Δt` haqiqiy throughput.
3. `progress` atomik va probe uni **lock olmasdan** o'qiydi. Aks holda
   `spin`/`deadlock` fault'lari socket javobini ham bloklab, `stop_progress`
   ning fail-silent semantikasi yo'qolardi.

Shuning uchun SUT **ikki thread**: main accept qiladi, worker ish tsiklini
yurgizadi. Bitta thread bilan "ish tsikli o'lgan, socket tirik" holati
ifodalanmaydi, ya'ni fail-silent fault klassi umuman testlanmaydi.

Watchdog ping'i **ish tsiklidan** yuboriladi (protokol §6): tsikl qotsa
watchdog ham qotadi, demak `stop_progress` va `deadlock` systemd'ga ham
ko'rinadi.

### 4.6 Har probe'da yangi ulanish

Contract bandi (a) — "socket `T_conn` ichida accept qiladi". Ulanish qayta
ishlatilsa bu band **umuman o'lchanmagan** bo'lardi. Shuning uchun prober har
probe'da yangi `AF_UNIX/SOCK_SEQPACKET` socket ochadi
(protokol §1, [`revix/prober.py`](revix/prober.py) `probe_once()`).

`T_rt` ham **absolut deadline**: send va recv uchun alohida timeout qo'yilsa
eng yomon holatda 2×`T_rt` kutilardi va bandi (b) amalda ikki barobar
bo'lib qolardi.

### 4.7 `invocation` echo — restart race'ini yopadi

Protokol har javobda `INVOCATION_ID` va pid ni echo qilishni talab qiladi.
Prober uni yozadi va **invocation o'zgarganda `progress` kamayishini
`no_progress` deb hisoblamaydi** (restart hisoblagichni 0 dan boshlaydi,
protokol §4.4).

Bu — prober'dagi **eng kritik shart**: busiz restart'dan keyingi birinchi
probe soxta failure bo'lib, downtime o'lchovi jimgina buzilardi. Test:
`tests/unit/test_prober.py::test_yangi_invocation_bilan_progress_reset_no_progress_EMAS`.

`INVOCATION_ID` yo'q bo'lganda (systemd'siz ishga tushirish) SUT 32 nol
yuboradi; bunday qiymat restart'ni ajratib bera olmaydi, shuning uchun pid
o'zgarishi zaxira guvoh bo'ladi.

### 4.8 Har scope uchun alohida o'qish timestamp'i

`psi_sampler` bir tsiklda bir necha scope'ni o'qiydi, lekin o'qishlar **bir
vaqtda emas**. Ularni bir vaqtda deb ko'rsatish xato bo'lardi, shuning uchun
har scope o'z `__read_mono_us` maydonini oladi (`PREREGISTRATION.md` §7).

`PsiFile` fd'ni bir marta ochadi va har namunada `pread(fd, 0)` qiladi:
10 Hz × 4 scope × 3 resurs = 120 o'qish/sekund, demak har namunada
open/close sezilarli syscall va dentry yuki bo'lardi.

Yo'q scope jimgina tashlanmaydi — `psi_scope_unavailable` hodisasi yoziladi.

### 4.9 Guard fail-closed

Xavfsizlik mantiqi [`SECURITY.md`](SECURITY.md) da batafsil. Arxitektura
uchun muhimi: guard **hech qachon "hammasi yaxshi" deb taxmin qilmaydi.**
PSI o'qilmasa, PSI to'liq bo'lmasa, kuzatiladigan fayl ochilmasa yoki
kutilmagan istisno bo'lsa — **trip qiladi**. Noto'g'ri trip bitta trial
yo'qotadi; noto'g'ri o'tkazib yuborish foydalanuvchi ilovasini yo'qotadi.

Guard trip'dan keyin **to'xtamaydi**: kill'dan keyin ham qoldiq pressure
bo'lishi mumkin, shuning uchun kuzatish davom etadi (kill esa idempotent,
bir marta).

### 4.10 Raw append-only, derived qayta yaratiladi

- `datasets/` **append-only**: raw eksperiment ma'lumoti hech qachon ustiga
  yozilmaydi yoki tahrirlanmaydi. `JsonlWriter` `O_APPEND` bilan ochadi va
  oldindan serializatsiya qilingan **bitta** `write()` qiladi (qism-qism
  yozish qatorni bo'lib yuborishi mumkin). `fsync` **davriy**, har qatorda
  emas — har qatorda fsync o'lchanayotgan tizimga IO kiritardi.
- **Derived ma'lumot regenerable**: reducer uni raw'dan qayta yaratadi va
  alohida fayllarda saqlaydi. Shuning uchun derived faylni o'chirish xavfsiz,
  raw faylni tahrirlash esa — ilmiy yaxlitlik buzilishi.
- Sensitivity sweep (`W_stab × θ`, `PREREGISTRATION.md` §4) **raw probe
  trace'lardan post-hoc** hisoblanadi, eksperiment qayta ishga tushirilmaydi.
  Shu sabab raw trace'lar saqlanishi majburiy: bitta raqam emas, butun egri
  chiziq beriladi.

### 4.11 Yopiq enum'lar

`probe_sample.outcome`, contract bandlari (`a_conn`/`b_response`/`c_progress`),
VR invalidator'lari va trial disposition'lari — **yopiq** enum'lar
(`PREREGISTRATION.md` §4, §12; `revix/schema.py` `DISPOSITIONS`;
`revix/prober.py` `OUTCOMES`). Prober enum'dan tashqari outcome'ni istisno
bilan rad etadi.

Sabab: yopiq enum jimgina eksklyuziyani imkonsiz qiladi. Har trial'ga aynan
bitta disposition, va yuqori eksklyuziya darajasi **natija sifatida**
beriladi, yashirilmaydi.

### 4.12 PSI ta'riflarga kirmaydi

Arxitektura darajasidagi majburiyat: **PSI faqat prediktor/kovariata.** U
failure, VR yoki FR ta'rifiga kirmaydi (`PREREGISTRATION.md` §5). Shuning
uchun `psi_sampler` va `prober` **alohida** jarayonlar va sampler'ning
chiqishi VR hisobiga umuman kirmaydi.

Aks holda "PSI gating FR ni kamaytiradi" tavtologiya bo'lardi. Batafsil:
[`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## 5. Ishga tushirish tartibi va xavfsizlik chegarasi

To'liq qurilish tartibi: `docs/architecture/00-pilot-topologiya.md` §6.
Muhim invariant:

1. **Guard birinchi ishga tushadi, oxirgi to'xtaydi.**
2. **Guard tasdiqlanmasa hech qanday pressure eksperimenti ishlamaydi**
   ([`TESTING.md`](TESTING.md)).
3. Eksperiment jarayonlari **faqat** `systemd-run --user --slice=...` orqali
   tug'iladi. To'g'ridan-to'g'ri Bash'dan ishga tushirilgan jarayon
   ishlab chiqish vositasining scope'ida tug'iladi va oomd o'sha scope'ni
   o'ldirishi mumkin (`docs/architecture/01-muhit-tekshiruvlari.md` §6).
4. Pre-flight: `revix-*` unit yoki `revixlab.slice`/`revixmon.slice`
   qoldiq holatda bo'lsa — **ishga tushmaydi**. Bu tekshiruvning to'liq
   shakli **driver**ga tegishli va u hali yozilmagan;
   `scripts/guard-test.sh` faqat `revix-press.service` ni tekshiradi
   ([`SECURITY.md`](SECURITY.md) §2(e)).

---

## 6. Ochiq savollar — hujjatlar orasidagi nomuvofiqliklar

Bu ro'yxat **tuzatilmadi** (frozen hujjatlar va kod bu hujjatning egaligida
emas). Har biri hal qilinishi kerak:

| # | Nomuvofiqlik | Joy |
|---|---|---|
| 1 | Guard chegarasi: `00-pilot-topologiya.md` §3.1(b) guard'ni "`full avg10 > 15%`" da trip qiladi deb yozadi; `02-guard-kalibratsiyasi.md` §1 guard'ni **qayta loyihalagan** (oniy `full avg10` chegarasi 85%, asosiy himoya — 2 s tezlik ≥35% va 15 s davomiylik), va `revix/guard.py` `DEFAULTS` shu ikkinchisini amalga oshiradi. §3.1(b) amendment qilinmagan. | `00` §3.1(b) vs `02` §1 vs `guard.py` |
| 2 | Davomiylik chegarasi uch xil: `guard.py` `DEFAULTS["sustain_max_seconds"] = 15.0` va `02` §1 **15 s** deydi; `guard.py` `_check_sustain` docstring'i **13 s** deydi; `scripts/guard-test.sh` default'i `SUSTAIN_MAX=13.0`. 13 s eng yomon holatdagi qonuniy trial'ni (hold 12 s + ramp 3 s) trip qilishi mumkin. | `guard.py`, `guard-test.sh`, `02` §1 |
| 3 | `guard.py` izohida `user@` ≈ `lab` topilmasi uchun "o'lchangan: 11.05 vs 11.41" raqamlari keltirilgan; `02-guard-kalibratsiyasi.md` §1 jadvalida bu juftlik yo'q (u yerda 2 s oynali `full` tezliklar, masalan 0.968 vs 0.970). Raqamlarning birligi va manbasi noaniq. | `guard.py` izohi vs `02` §1 |
| 4 | `02-guard-kalibratsiyasi.md` §7 (6-qator) `PREREGISTRATION.md` **§9.6** ga havola qiladi; §9 da faqat 9.1–9.4 bor. | `02` §7 |
| 5 | `README.md` holat jadvali "Pilot harness ⏳ keyingi qadam" deydi, lekin schema/cgroup/guard/pressure/psi_sampler/sut.c/prober.py commit qilingan va test bilan qoplangan. | `README.md` |
| 6 | `docs/research/05-metodologiya.md` §1 `preregistration/v1` ga ishora qiladi; muzlatilgan fayl endi `v1.1`. | `05` §1 |
| 7 | `PREREGISTRATION.md` §7 `avgN` ni ham yozishni belgilaydi; `psi_sampler.build_fields()` faqat `avg10` ni ustun sifatida yozadi (`avg60`/`avg300` parse qilinadi, lekin saqlanmaydi). | `PREREGISTRATION.md` §7 vs `psi_sampler.py` |
| 8 | `00-pilot-topologiya.md` §3.1(b) guard "o'z `OOMScoreAdjust` i bilan" ishlaydi deydi; `guard.py` `oom_score_adj` ni o'zgartirmaydi (pasaytirish privilegiya talab qiladi — `guard.py` docstring'i buni halol yozadi) va `guard-test.sh` ham `OOMScoreAdjust=` bermaydi. | `00` §3.1(b) vs `guard.py` |
| 9 | `PREREGISTRATION.md` §7 to'rt scope'ni sanaydi (host, `revixlab.slice`, SUT, bystander); `psi_sampler` scope'larni CLI'dan oladi, ya'ni to'g'ri to'plamni **driver** ta'minlashi kerak. Guard testida boshqa to'plam ishlatilgan (host, user, lab, mon) — u pilot trial emas, lekin driver yozilganda §7 ning to'plami qattiq qo'yilishi kerak. | `PREREGISTRATION.md` §7 vs `psi_sampler.py` |

---

## 7. Aloqador hujjatlar

| Hujjat | Mazmuni |
|---|---|
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | muzlatilgan ta'riflar, metrikalar, statistik reja — **shartnoma** |
| [`docs/architecture/00-pilot-topologiya.md`](docs/architecture/00-pilot-topologiya.md) | cgroup topologiyasi, oomd xavfsizlik chegarasi, qurilish tartibi |
| [`docs/architecture/01-muhit-tekshiruvlari.md`](docs/architecture/01-muhit-tekshiruvlari.md) | empirik tekshirilgan muhit faktlari |
| [`docs/architecture/02-guard-kalibratsiyasi.md`](docs/architecture/02-guard-kalibratsiyasi.md) | o'lchangan guard chegaralari va pressure mexanizmi |
| [`docs/architecture/03-sut-protokoli.md`](docs/architecture/03-sut-protokoli.md) | muzlatilgan wire protokol (`sut-protocol/v1`) |
| [`docs/research/05-metodologiya.md`](docs/research/05-metodologiya.md) | eksperiment darajalari, fault taksonomiyasi |
| [`SECURITY.md`](SECURITY.md) | xavfsizlik va threat model |
| [`TESTING.md`](TESTING.md) | test strategiyasi va guard testi protsedurasi |
| [`INSTALLATION.md`](INSTALLATION.md) | talablar va sozlash |
| [`DEVELOPMENT.md`](DEVELOPMENT.md) | ishlash tartibi, branch va commit uslubi |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | ilmiy yaxlitlikni buzmasdan hissa qo'shish |
