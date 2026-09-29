# SECURITY — xavfsizlik va threat model

> Bu loyihaning eng muhim xavfsizlik xususiyati bitta jumlada:
>
> ## 🚨 Pressure eksperimenti `systemd-oomd` ni qo'zg'atib foydalanuvchining ilovalarini o'ldirishiga YO'L QO'YILMAYDI.
>
> Bu "yaxshi bo'lardi" emas, **majburiy chegara**. Buzilsa, natija — o'chgan
> brauzer, o'chgan editor yoki o'chgan desktop sessiyasi, ya'ni yo'qolgan ish.

Bu hujjat **klassik dasturiy xavfsizlik** (CVE, autentifikatsiya, tashqi
hujumchi) haqida emas. REVIX — lokal tadqiqot harness'i; uning threat modeli
**o'z eksperimentining kollateral zarari**.

---

## 1. Tasdiqlangan xavf: `systemd-oomd`

Bu gipoteza emas. Shu mashinada o'qilgan
([`docs/architecture/01-muhit-tekshiruvlari.md`](docs/architecture/01-muhit-tekshiruvlari.md) §7,
[`docs/research/01-texnologiya-auditi.md`](docs/research/01-texnologiya-auditi.md) §4):

```
/usr/lib/systemd/system/user@.service.d/10-oomd-user-service-defaults.conf
    ManagedOOMMemoryPressure=kill
    ManagedOOMMemoryPressureLimit=50%

oomd.conf:  DefaultMemoryPressureDurationSec=20s

systemctl show user@1000.service -p ManagedOOMMemoryPressure
    ManagedOOMMemoryPressure=kill
```

Ya'ni `user@1000.service` ustida oomd ning **kill authority** si bor: 50%
memory pressure 20 s davomida saqlansa, oomd **avlod cgroup'ni** o'z
evristikasi bo'yicha (eng yuqori pressure/reclaim) o'ldiradi.

### Nega PSI ning ierarxikligi bu xavfni real qiladi

PSI **ierarxik**: ota cgroup avlodlarining stall'ini o'z ichiga oladi. Demak
`revixlab.slice` ichida ataylab yaratilgan stall **avtomatik ravishda**
`user@1000.service` ga tarqaladi. Eksperiment "o'z qutisida" qolmaydi — u
oomd ning kuzatuv scope'ini to'g'ridan-to'g'ri ko'taradi.

Kalibratsiya bu tarqalishni **o'lchadi**, va natija kutilganidan yomon:

> Bo'sh desktop'da `user@1000.service` PSI'si `revixlab.slice` PSI'siga
> **deyarli aynan teng** (o'lchangan 2 s oynali `full` tezliklar, masalan
> t=7.6 s da 0.968 vs 0.970; cho'qqi 0.980 vs 0.984) —
> [`docs/architecture/02-guard-kalibratsiyasi.md`](docs/architecture/02-guard-kalibratsiyasi.md) §1.

Sabab: PSI `full` faqat **non-idle** task'larni hisoblaydi. Claude/Chrome
idle bo'lganda yagona non-idle task — pressure generatori, demak ota scope
child scope'ni aks ettiradi. (Band tizimda `full` ancha past bo'lardi — bu
topilma **bo'sh desktop shartiga** bog'liq va band desktop'da qayta
o'lchanishi kerak: `02` §7 masala 1.)

**Natijasi:** pilotning P2 bandi (60–80% *slice* stall) `user@` ni ham shu
darajaga ko'taradi. Ya'ni "slice'ni cheklash orqali izolyatsiya" **ishlamaydi**
— cheklash xotirani ushlaydi, PSI tarqalishini esa ushlamaydi.

### Nima nishon bo'lishi mumkin

`app.slice` ostidagi eng yirik iste'molchi: brauzer, editor, IDE, GNOME
sessiyasi — **yoki ishlab chiqish vositangizning o'zi**. Muhit tekshiruvi
buni ko'rsatdi: ishlab chiqish vositasidan ishga tushirilgan har qanday
jarayon shu vositaning scope'ida tug'iladi
(`01-muhit-tekshiruvlari.md` §6):

```
$ cat /proc/self/cgroup
0::/user.slice/user-1000.slice/user@1000.service/app.slice/app-com.anthropic.Claude-….scope
```

→ **Pressure generatorini hech qachon to'g'ridan-to'g'ri Bash'dan ishga
tushirmang.** Faqat `systemd-run --user --slice=revixlab.slice` orqali,
shunda u alohida cgroup'ga tushadi.

---

## 2. Qatlamli yumshatishlar

Hech bir qatlam yolg'iz yetarli emas. Ustuvorlik tartibida
([`docs/architecture/00-pilot-topologiya.md`](docs/architecture/00-pilot-topologiya.md) §3.1):

### (a) Har pressure epizodi ≤12 s — birlamchi, privilegiyasiz

oomd ning sharti **20 s sustained**. Epizod ≤12 s, keyin ≥20 s quiescence
bo'lsa, o'rtacha 20 s uzluksiz oshish yig'ilishidan **oldin** pasayadi, demak
oomd ning sharti **umuman bajarilmaydi**.

Bu chegara harness'da qattiq kodlangan va trial jadvalining o'zida
(`00-pilot-topologiya.md` §5, `PREREGISTRATION.md` §9.4):
`R_ref` baseline 10 s → ramp 5 s → hold, injeksiya hold'ga 3 s kirgach →
**umumiy pressure-on ≤12 s** → washout ≥20 s.

> ⚠️ **Bu qatlam ILMIY CHEKLOV yaratadi**, xavfsizlik bonusi emas: sustained
> pressure eksperimentlari VM yoki root talab qiladi. Shuning uchun
> `PREREGISTRATION.md` §4 da `W_stab_pilot = 8 s` ochiq yozilgan va
> maqolada shunday beriladi, yumshatilmaydi. P1 da o'lchanadigan narsa —
> *"pressure davom etayotganda tasdiqlangan recovery"*, 60 s sustained
> recovery **emas**.

### (b) Mustaqil guard jarayoni — majburiy

[`revix/guard.py`](revix/guard.py). Buzilmaydigan dizayn qoidalari:

1. **MUSTAQIL jarayon.** Driver'dan alohida ishga tushadi, driver'ga hech
   qanday bog'liqligi yo'q. **Qotib qolgan driver guard'ni o'chira
   olmasligi kerak** — shuning uchun guard driver'ning thread'i yoki childi
   emas.
2. **Birinchi start, oxirgi stop.**
3. **FAIL-CLOSED** (pastda alohida bo'lim).
4. **Repo'dagi eng sodda fayl.** Bu yerda ayyorlik qilinmaydi.
5. **Hech qachon istisnodan yiqilmaydi:** yozish xatolari yutiladi, asosiy
   tsiklning har qanday istisnosi **trip**'ga aylanadi.

Guard `user@UID.service/memory.pressure` ni kuzatadi (10 Hz `total`, 1 Hz
`avgN`) va chegaradan oshsa `revixlab.slice/cgroup.kill` ga `1` yozadi; trial
`aborted_guard` disposition'ini oladi (`PREREGISTRATION.md` §12).

Guard trip'dan keyin **to'xtamaydi** — kill'dan keyin ham qoldiq pressure
bo'lishi mumkin, shuning uchun kuzatish davom etadi (kill esa idempotent,
faqat bir marta bajariladi).

#### Guard chegaralari — kalibratsiya bilan aniqlangan, taxmin bilan emas

Boshlang'ich dizayn **oniy** chegarada trip qilardi. Kalibratsiya
ko'rsatdi-ki `user@` PSI ≈ `lab` PSI, demak oniy chegara **har bir P2
trial'ini o'ldirardi** va eksperimentni imkonsiz qilardi. Guard qayta
loyihalandi: asosiy himoya oniy chegara emas, balki oomd ning **o'z
kriteriyasini aks ettiruvchi davomiylik** —

| | chegara | davomiylik |
|---|---|---|
| **oomd** | `avg10 ≥ 50%` | 20 s |
| **guard** | 2 s tezlik ≥ 35% | 15 s |

Zaxira katta, chunki soatlar boshqacha yuradi: oomd ning hisoblagichi `avg10`
50% dan oshgandan **keyin** boshlanadi, `avg10` esa haqiqiy tezlikka yetishi
uchun ~10 s kerak. 0.6 tezlikda qotgan generator uchun oomd ~28–30 s da
ishlardi; guard 15 s da to'xtatadi. 15 s ning tanlanishi: pilot hold ≤12 s +
ramp ≤3 s = eng yomon holatda 15 s → **to'g'ri ishlayotgan trial hech qachon
trip qilmaydi.**

To'liq asoslash va o'lchangan raqamlar:
[`docs/architecture/02-guard-kalibratsiyasi.md`](docs/architecture/02-guard-kalibratsiyasi.md) §1.

Oniy chegaralar **runaway tutuvchi** sifatida qoldi (to'liq qotish holati):
`user_full_avg10_max`, `user_some_avg10_max`, `user_full_rate2s_max`. Oxirgisining
qiymati (`0.98`) ham o'lchovdan: qonuniy ramp burst'i 0.93–0.98 ga chiqadi,
va boshlang'ich `0.90` qiymati qonuniy pressure'ni o'ldirgan (`02` §1, §5 Run B).

Davomiylik tezligi **`total=` dan** olinadi, `avgN` dan emas: `avgN` pressure
to'xtagandan keyin ham sekin pasayadi va **soxta davomiylik** yig'ardi.

> ⚠️ Chegara qiymatlari bo'yicha uch joy bir-biriga mos kelmaydi (15 s / 13 s)
> va `00-pilot-topologiya.md` §3.1(b) hali kalibratsiyadan oldingi 15%
> chegarasini yozadi. To'liq ro'yxat:
> [`ARCHITECTURE.md`](ARCHITECTURE.md) §6, masala 1 va 2.

### (c) Kernel darajasidagi cheklashlar

| Mexanizm | Nimani to'xtatadi |
|---|---|
| slice `MemoryMax` | kernel darajasidagi umumiy anonim xotira shifti |
| **`MemorySwapMax=0`** (generator + SUT) | 5.5 GiB swap to'lib host-wide IO va SSD wear yaratishi |
| `TasksMax` | fork bomb |
| `CPUQuota` | desktop CPU starvation (12 yadrodan ≥8 erkin qoladi) |
| hog `sched_setaffinity` | CPU fault'lari SUT bilan bir xil yadro to'plamida qoladi (`cpuset` delegated emas) |
| `RuntimeMaxSec=` (generator) | generator trial'dan uzoq yashamasligi |
| generator'ning o'z `--max-seconds` | **ikkinchi**, systemd'dan mustaqil vaqt chegarasi |
| `oom_score_adj = 1000` (generator) | kernel global OOM killer boshqa hech narsani emas, **avval generatorni** tanlaydi |

Aniq qiymatlar: `00-pilot-topologiya.md` §1 va §2. Ikki mustaqil vaqt
chegarasi ataylab: ular PSI chegarasiga bog'liq emas, demak pressure PSI
qanday bo'lishidan qat'i nazar to'xtaydi.

### (d) `cgroup.kill` bilan teardown

Bitta yozish → **atomik subtree kill**, privilegiyasiz. Bu mashinada
tasdiqlangan (`01-muhit-tekshiruvlari.md` §3): `echo 1 >
revixlab.slice/cgroup.kill` → unit `inactive`. Kalibratsiyada har holatda
ishladi: `SIGKILL` (status 9/KILL), `oom_kill: 0` — ya'ni **guard o'ldirdi,
OOM emas** (`02` §5).

Bu mexanizm ikki joyda ishlatiladi: guard trip'ida va har trial'dan keyingi
washout'da (`PREREGISTRATION.md` §8.4).

### (e) Pre-flight: qoldiq holatda ishga tushmaydi

`revix-*` unit yoki `revixlab.slice`/`revixmon.slice` allaqachon mavjud
bo'lsa harness **ishga tushmaydi**. Sabab: qoldiq unit avvalgi run'ning
holatini olib kiradi va bir run'ning pressure'i boshqasining o'lchoviga
qo'shilib ketadi — bu ham xavfsizlik, ham validlik masalasi.

`scripts/guard-test.sh` bu tekshiruvning **qisman** shaklini bajaradi:
`revix-press.service` faol bo'lsa xato bilan chiqadi. `--collect` transient
unit'lari qoldiq failed unit qoldirmaydi.

> **Bo'shliq:** `00-pilot-topologiya.md` §2 va `README.md` talab qilgan to'liq
> pre-flight (barcha `revix-*` unit'lari **va** `revixlab.slice`/`revixmon.slice`
> cgroup'larining yo'qligi) **driver** moduliga tegishli — u hali yozilmagan
> ([`ARCHITECTURE.md`](ARCHITECTURE.md) §1). Hozircha qoldiq holatni qo'lda
> tekshirish kerak ([`INSTALLATION.md`](INSTALLATION.md) §5, 7-tekshiruv).

### Qilinmaydigan narsalar — va nega

| | Yechim | Nega qilinmaydi |
|---|---|---|
| (c) | Foydalanuvchining app scope'lariga `ManagedOOMPreference=avoid/omit` qo'yish | jonli muhitni o'zgartiradi va mavjud scope'larda ishonchli qo'yilmaydi |
| (e) | `systemd-oomd` ni to'xtatish | **haqiqiy mashina himoyasini o'chiradi** — eksperiment uchun xavfsizlik mexanizmini o'chirish qabul qilinmaydi |

(`00-pilot-topologiya.md` §3.1 dagi to'liq jadval.)

Uzoq muddatli to'g'ri yechim (d): harness'ni **system slice**ga ko'chirish
(`ManagedOOMMemoryPressure=auto`, `-.slice` ostida) → oomd kill scope'idan
**butunlay** chiqadi. Bu `sudo` talab qiladi, demak loyiha prinsipi bo'yicha
"guest'ga tegishli" (§5).

---

## 3. Guard'ning fail-closed dizayni

Guard **xato holatda xavfsiz deb taxmin qilmaydi.** Quyidagi holatlarning
har biri **trip** qiladi:

| Holat | `reason` |
|---|---|
| PSI faylini o'qish istisno bilan tugadi | `psi_read_failed` |
| PSI da `some` yoki `full` satri yo'q | `psi_incomplete` |
| kuzatiladigan `memory.pressure` ochilmadi | `watch_open_failed` (+ exit kodi 2) |
| asosiy tsiklda kutilmagan istisno | `guard_exception` |
| `/proc/meminfo` o'qilmadi | `meminfo_unreadable` |
| host `MemAvailable` chegaradan past | `host_mem_available` |
| lab tashqarisida kernel OOM kill | `kernel_oom_kill_outside_lab` |
| lab slice'da swap ishlatildi | `lab_swap_used` |
| 2 s tezlik runaway chegarasidan oshdi | `user_full_rate2s_runaway` |
| `avg10` runaway chegarasidan oshdi | `user_full_avg10_runaway` / `user_some_avg10_runaway` |
| chegaradan yuqori pressure juda uzoq davom etdi | `sustained_pressure` |

Asimmetriya ataylab va u kodda izohlangan: **noto'g'ri trip bitta trial
yo'qotadi; noto'g'ri o'tkazib yuborish foydalanuvchi ilovasini yo'qotadi.**
Ikkinchisi ancha qimmat, demak guard xatoga qarab **to'xtatish** tomonga
og'adi.

### OOM atributsiyasi — nozik joy

Cheklangan cgroup'dagi OOM ham global `/proc/vmstat oom_kill` ni oshiradi.
Shuning uchun guard global o'sishdan lab'ning **o'z** o'sishini **ayiradi**
va faqat qolgan qism ("outside") host xavfini bildiradi. Busiz kutilgan,
cheklangan OOM (fault class 3 — `leak_oom_noswap`) host OOM deb xato talqin
qilinib, har leak trial'i abort bo'lardi. Testlar:
`test_guard.py::test_cheklangan_cgroup_oom_host_oom_deb_hisoblanmaydi` va
`::test_lab_tashqarisidagi_oom_trip_qiladi`.

---

## 4. Qoldiq risk — halol bayon

### 4.1 Guard o'zini himoya qila olmaydi

**Bu eng muhim qoldiq risk.**

Guard'ning o'zini oomd va kernel OOM killer'dan himoya qilish uchun uning
`oom_score_adj` ini **pasaytirish** kerak. Privilegiyasiz faqat **oshirish**
mumkin. Demak:

- guard **kichik xotira izi** bilan ishlaydi (guard testida
  `MemoryMax=128M`), chunki oomd eng yirik iste'molchini tanlaydi;
- lekin bu **kafolat emas**.

Bu [`revix/guard.py`](revix/guard.py) modul docstring'ida ochiq yozilgan va
`02-guard-kalibratsiyasi.md` §7 da 3-masala sifatida qayd etilgan. To'liq
yechim — harness'ni system slice'ga ko'chirish (`sudo`).

> Qarama-qarshi tomoni: pressure generatori **ataylab** o'z `oom_score_adj`
> ini `1000` ga ko'taradi ([`revix/pressure.py`](revix/pressure.py)
> `set_oom_score_adj()`), ya'ni kernel global OOM killer boshqa hech narsani
> emas, avval generatorni tanlaydi. Oshirish privilegiyasiz mumkin, demak bu
> qism **ishlaydi**.

### 4.2 Guard `oom_score_adj` haqidagi hujjat nomuvofiqligi

`00-pilot-topologiya.md` §3.1(b) guard "o'z `OOMScoreAdjust` i bilan"
ishlaydi deb yozadi. **Kodda bunday narsa yo'q** va privilegiyasiz bo'lishi
ham mumkin emas. Bu [`ARCHITECTURE.md`](ARCHITECTURE.md) §6 dagi 8-ochiq
masala.

### 4.3 Kernel global OOM killer

Faqat eksperiment shifti + host sarfi jismoniy xotiradan oshsa yetiladi.
O'lchangan zaxira (`01-muhit-tekshiruvlari.md` §8): 15 GiB umumiy, ~7.6 GiB
available; 2 GiB eksperiment shifti xavfsiz zaxira qoldiradi. Guard qo'shimcha
`/proc/vmstat oom_kill` va host `MemAvailable` ni kuzatadi.

### 4.4 journald flooding

Default `RateLimitIntervalSec=30s`, `RateLimitBurst=10000`. 10 Hz prober
journald'ga yozsa rate-limit'ga tushib **jimgina yo'qoladi** va foydalanuvchi
journal'ini ifloslaydi.

→ Muzlatilgan qaror: **harness o'z fayllariga yozadi; hech qanday o'lchov
ma'lumoti journald'dan o'tmaydi.** journald faqat systemd'ning o'z
hodisalarini cross-check qilish uchun (`00` §3.4, `01-texnologiya-auditi.md` §5).

Bu xavfsizlikdan ko'ra ma'lumot yaxlitligi masalasi, lekin natijasi bir xil:
jimgina yo'qolgan o'lchov.

### 4.5 Band desktop'da qayta o'lchanmagan

`user@ ≈ lab` topilmasi **bo'sh desktop** shartida olingan. Band tizimda
`full` ancha past bo'ladi va guard sezgirligi o'zgaradi — ya'ni guard
chegaralari band mashinada **qayta kalibrlanishi kerak** (`02` §7 masala 1).
Hozircha guard testi bo'sh desktop'da o'tkazilishi kerak.

### 4.6 Sustained pressure va to'liq `W_stab` imkonsiz

>15 s sustained pressure va `W_stab = 60 s` privilegiyasiz **imkonsiz**
(`02` §7 masala 4). Bu xavfsizlik chegarasining bevosita natijasi va
`PREREGISTRATION.md` §4 da cheklov sifatida yozilgan.

### 4.7 Nima bilan umuman cheklanmaydi

PSI ning 2 s yangilanish granularligi va DVFS/termal ta'siri. **Bular
validlik masalasi, xavfsizlik emas** — `PREREGISTRATION.md` §7 va §8.5.

---

## 5. Privilegiya yuzasi

### Privilegiyasiz ishlaydi (tekshirilgan)

`user@1000.service` da `Delegate=yes`, `DelegateControllers=cpu memory pids`
(`01-muhit-tekshiruvlari.md` §1), demak privilegiyasiz:

- transient user unit'lar `MemoryMax=`, `MemoryHigh=`, `MemorySwapMax=`,
  `CPUQuota=`, `TasksMax=`, `Restart*`, `WatchdogSec=`, `TimeoutStartSec=`,
  `RestartSteps=` qabul qiladi;
- delegated subtree'da `memory.max`, `memory.high`, `memory.swap.max`,
  `cgroup.kill`, `memory.reclaim` **yoziladi**;
- per-cgroup PSI **o'qiladi** — `io.pressure` ham, `io` controller delegated
  bo'lmasa ham.

Ya'ni **IO PSI o'lchash privilegiyasiz, IO injection esa emas.**

### Root kerak (P1 da ishlatilMAYDI)

`io` controller / `io.max`; `dm-delay`/`dm-flakey`; `tc netem`; cgroup
`cpuset` pinning; `scaling_governor=performance`; `drop_caches`; paket
o'rnatish; harness'ni system slice'ga ko'chirish.

### 🔑 Loyiha prinsipi: "root kerak" = "guest'ga tegishli"

`sudo -n` parol so'raydi, demak **hech bir privilegiyali qadam nazorsiz
ishlamaydi.** Shundan ikki majburiyat kelib chiqadi:

1. Kechalik kampaniya **to'liq privilegiyasiz** yoki **to'liq guest ichida**
   bo'lishi kerak — aralash emas.
2. Barcha privilegiyali operatsiyalar **bitta** qisqa, ko'rib chiqiladigan
   setup skriptida, sessiyaga bir marta ishlaydi va har trial'da hech narsa
   qilmaydi → **o'lchov davomida hech qanday root process tirik emas.**

QEMU ichida siz izolyatsiyalangan kernel'da root'siz va host privilegiyasi
`/dev/kvm` dan boshqa kerak emas. Bu benchmark'ni **portativ** qiladi — ya'ni
haqiqiy tadqiqot deliverable'i ([`README.md`](README.md) "Talablar",
[`docs/research/04-novelty-statement.md`](docs/research/04-novelty-statement.md) C4).

`drop_caches` **qilinmaydi**: u root talab qiladi va butun ish stansiyasini
buzadi, shuning uchun cold start P1 qamrovidan tashqarida
(`PREREGISTRATION.md` §8.3).

---

## 6. Operatorning majburiy tartibi

1. **Guard testini ishga tushiring va o'tganini tekshiring** —
   [`TESTING.md`](TESTING.md) §3. Guard tasdiqlanmasa hech qanday pressure
   eksperimenti ishga tushirilmaydi.
2. Bo'sh desktop'da ishlang (guard chegaralari shu shartda kalibrlangan) va
   yo'qotib qo'yish mumkin bo'lgan ishni oldin saqlab qo'ying.
3. Eksperiment jarayonlarini **faqat** `systemd-run --user --slice=…` orqali
   ishga tushiring.
4. Guard **birinchi**, keyin sampler, keyin pressure. Teardown teskari
   tartibda.
5. Har run'dan keyin post-flight tekshiruvni o'qing: `vmstat oom_kill`,
   oomd journal, slice `memory.swap.current`, qoldiq unit'lar.
6. Kollateral zarar belgisi bo'lsa — trial `contaminated` yoki
   `aborted_guard`, va **eksklyuziya darajasi natija sifatida beriladi**
   (`PREREGISTRATION.md` §12), yashirilmaydi.

---

## 7. Aloqador hujjatlar

- [`docs/architecture/00-pilot-topologiya.md`](docs/architecture/00-pilot-topologiya.md) — topologiya, §3 xavf tahlili, §4 privilegiya yuzasi
- [`docs/architecture/01-muhit-tekshiruvlari.md`](docs/architecture/01-muhit-tekshiruvlari.md) — empirik muhit faktlari
- [`docs/architecture/02-guard-kalibratsiyasi.md`](docs/architecture/02-guard-kalibratsiyasi.md) — o'lchangan chegaralar, §6 kollateral zarar, §7 ochiq masalalar
- [`docs/research/01-texnologiya-auditi.md`](docs/research/01-texnologiya-auditi.md) §4 — oomd auditi
- [`PREREGISTRATION.md`](PREREGISTRATION.md) §4, §8, §12 — cheklovlar, washout, disposition
- [`TESTING.md`](TESTING.md) — guard testi protsedurasi
- [`ARCHITECTURE.md`](ARCHITECTURE.md) §6 — hujjatlar orasidagi ochiq nomuvofiqliklar
