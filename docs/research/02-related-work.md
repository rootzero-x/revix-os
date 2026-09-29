# 02 — Related Work

## Tekshirish darajalari — MAJBURIY o'qish

Bu hujjatdagi har bir manba **tekshirish darajasi** bilan belgilangan. Bu formalizm emas:
sitat qilingan lekin mavjud bo'lmagan manba — ilmiy noxushlik, va REVIX loyiha
spetsifikatsiyasi (§40, §41) buni aniq taqiqlaydi.

| Daraja | Ma'nosi | Sitat qilish mumkinmi |
|---|---|---|
| **T1** | Men to'g'ridan-to'g'ri avtoritativ sahifani ochib, sarlavha/muallif/venue'ni tasdiqladim | ✅ ha |
| **T2** | Skanda topilgan, URL bor, lekin **men o'zim avtoritativ sahifani ochmadim** | ⚠️ maqola yozishdan oldin T1 ga ko'tarilishi shart |
| **T3** | Faqat eslatib o'tilgan, tasdiqlanmagan | ❌ **SITAT QILINMAYDI** |

**Avtoritativ sahifa** deb quyidagilar qabul qilinadi: nashriyot sahifasi
(USENIX/ACM/IEEE), Crossref DOI registri (`api.crossref.org` — DOI metadata'sining
rasmiy manbasi), arXiv'ning o'z API'si, maqolaning **birlamchi PDF**'i, rasmiy git
repozitoriysi yoki mahalliy o'rnatilgan `man` sahifasi.

> **2026-09-29 sessiyasida bajarilgan ish:** 22 manba T2/T3 dan T1 ga ko'tarildi,
> 10 yangi T1 manba qo'shildi, 4 bibliografik xato tuzatildi, va §"Tizimli qidiruv"
> qo'shildi. **Manfiy da'vo qayta yozildi — u avvalgi shaklda yolg'on edi.**
> Batafsil: §"Verifikatsiya jurnali".

---

## T1 — O'zim tasdiqlagan

### ⚠️ systemd `ConditionMemoryPressure=` — ENG QATTIQ PRIOR ART

> **`ConditionMemoryPressure=`, `ConditionCPUPressure=`, `ConditionIOPressure=`**
> `systemd.unit(5)`, **systemd v250 da qo'shilgan** (bu mashinada systemd 261 (261.2-1)
> man sahifasidan tasdiqlangan)

Man sahifasidan aynan:

> "Verify that the overall system (memory, CPU or IO) pressure is below or equal to a
> threshold. … the pressure will be measured as an average over the last five minutes
> **before the attempt to start the unit is performed**. … The supported timespans match
> what the kernel provides, and are limited to `10sec`, `1min` and `5min`. The `full` PSI
> will be checked first, and if not found `some` will be checked."
>
> "Optionally, the threshold value can be prefixed with the slice unit under which the
> pressure will be checked, followed by a `:`."

Va `Conditions and Asserts` bo'limidan:

> "Before the unit is started, systemd will verify that the specified conditions and
> asserts are true. If not, the starting of the unit will be (mostly silently) **skipped**
> (in case of conditions) … Failing conditions or asserts will **not** result in the unit
> being moved into the `failed` state. The conditions and asserts are checked **at the time
> the queued start job is to be executed**."

**REVIX uchun ahamiyati — bu loyihaning eng muhim topilmasi:**

`Restart=` avtomatik qayta ishga tushirish **start job navbatga qo'yadi**, va shartlar
"at the time the queued start job is to be executed" tekshiriladi. Demak:

> **systemd 2021 yildan (v250) beri PSI-gated restart admission control'ga ega.**
> REVIX ning H2 mexanizmi — "pressure yuqori bo'lsa restart'ni bloklash" — **allaqachon
> shipped feature**, `RestartSteps=` kabi.

Ammo muhim **farq** (va REVIX ning haqiqiy joyi shu):

| O'q | `ConditionMemoryPressure=` | REVIX H2 |
|---|---|---|
| Harakat | pressure yuqori → start **skip qilinadi** | pressure yuqori → restart **kechiktiriladi va qayta urinadi** |
| Natija | shart bajarilmasa xizmat **o'chib qoladi** (skip failure emas, demak yangi restart ham rejalashtirilmaydi) | xizmat pressure tushgach tiklanadi |
| O'lchangan | ❌ **hech kim o'lchamagan** | ✅ o'lchash — hissa |

**Xulosa:** `ConditionMemoryPressure=` REVIX ning **to'rtinchi baseline arm'i** bo'lishi
kerak (A: `Restart=` fiksa, B: `RestartSteps=` backoff, C: REVIX PSI-gated defer,
**D: `ConditionMemoryPressure=` PSI-gated skip**). Bu `RestartSteps=` bilan bo'lgan
vaziyatning aynan takrori: mexanizm mavjud → hissa mexanizm emas, **o'lchov**.

> ⚠️ **Men o'zim tekshirmagan qism:** `Restart=` yo'li shartni qayta baholaydi degan
> xulosa man sahifasining "queued start job" iborasidan **mantiqiy chiqarilgan**, lekin
> men buni jonli tizimda **empirik sinamadim**. Pilot bu xatti-harakatni birinchi
> navbatda tekshirishi shart — agar shart avtomatik restart yo'lida baholanmasa, yuqoridagi
> tahlil o'zgaradi. Bu `PREREGISTRATION.md` uchun aniq, arzon, falsifikatsiya qilinadigan
> tekshiruv.

### Narya — fleet darajasidagi eng qattiq prior art

> **Predictive and Adaptive Failure Mitigation to Avert Production Cloud VM Interruptions**
> Sebastien Levy, Randolph Yao, Youjiang Wu, Yingnong Dang (Microsoft Azure);
> Peng Huang (Johns Hopkins University); Zheng Mu (Microsoft Azure); Pu Zhao (Microsoft
> Research); Tarun Ramani, Naga Govindaraju, Xukun Li (Microsoft Azure); Qingwei Lin
> (Microsoft Research); Gil Lapid Shafriri, Murali Chintalapati (Microsoft Azure).
> **14th USENIX Symposium on Operating Systems Design and Implementation (OSDI '20)**,
> November 4–6, 2020, pp. **1155–1170**, ISBN 978-1-939133-19-9.
> <https://www.usenix.org/conference/osdi20/presentation/levy>

Men PDF'ni to'liq o'qib chiqdim (`osdi20-levy.pdf`). Tasdiqlangan mazmuni:

- "predicts imminent host failures based on **multi-layer system signals**"
- "Narya's decision engine takes a novel **online experimentation** approach to continually
  explore the best mitigation action"; "further enhances the adaptive decision capability
  through **reinforcement learning**" — muayyan model: **multi-armed Bandit**
- 15 oylik production deployment'da VM interruption'larni "previous static strategy" ga
  nisbatan o'rtacha **26%** kamaytirgan

**Action space (Table 2, PDF'dan aynan) — primitiv:**
Live Migration (LM, "Migrate VMs to other nodes on the fly"); Service Healing (SH,
"Discon. VMs, move them to healthy nodes"); Soft Reboot (SR, "Reload host OS kernel, VM
states preserved"); Mark Unallocatable (UA, default T = 7 kun); Avoid.
**Kompozit:** UA-LM-HI, UA-LM-RH, UA-SR, Avoid-RH. Plus **NoOp** — "This is the baseline
to measure the benefits of prediction and taking actions."

#### Narya nimani qoplaydi va nimani QOPLAMAYDI — halol paragraf

Narya failure **prediction**dan mitigation **action tanlash**gacha bo'lgan to'liq yopiq
halqani quradi va uni Azure compute platformasida 15 oy production'da yuritadi. Uning
qaror mexanizmi haqiqatan ham adaptiv: A/B online eksperiment bilan action'larni fleet
miqyosida sinaydi, keyin multi-armed bandit va RL bilan tanlovni optimallashtiradi,
va optimallashtirish maqsadi bitta aniq obyektiv metrika — **VM interruption soni**.
Muhim nozik jihat: Narya'da `NoOp` **ataylab** action space ichida turadi, ya'ni
"hech narsa qilmaslik" ham tanlanadigan variant va prediction'ning foydasini o'lchash
uchun baseline. Bu REVIX ning "defer" g'oyasiga **kontseptual jihatdan yaqin**, va
buni maqolada yashirmaslik kerak.

Narya **qoplamaydigan** narsalar, va nima uchun bu REVIX ni yo'q qilmaydi:

1. **Granularlik boshqa.** Narya host va VM darajasida ishlaydi; uning action'lari
   migratsiya, host OS kernel soft reboot, allokatsiyani bloklash. Bitta host ichidagi
   **alohida xizmatni** qayta ishga tushirish uning action space'ida **yo'q**.
2. **Resurs pressure signal emas.** PDF'da "pressure" so'zi faqat ikki joyda uchraydi va
   ikkalasi ham metaforik/sig'im ma'nosida ("intense pressure to mitigate", "capacity
   pressure"). **PSI, `/proc/pressure`, cgroup pressure — PDF'da yo'q.** Narya'ning
   signallari apparat/telemetriya darajasida (masalan CPU chastotasi pasayishi, IERR).
3. **n=1 da uning metodi ishlamaydi.** Narya'ning butun qaror mexanizmi *katta
   populyatsiya* talab qiladi: A/B testing "each unit is one failure prediction" va
   statistik kuch fleet hajmidan keladi. Bitta mashinada bu metod **printsipial ravishda**
   qo'llanilmaydi — bu REVIX ning cheklovi emas, **boshqa muammo sinfi**.
4. **"False recovery" metrikasi yo'q.** Narya action'larning foydasini VM interruption
   kamayishi bilan o'lchaydi. "Action muvaffaqiyat deb hisoblandi, lekin aslida emas edi"
   degan alohida metrika PDF'da yo'q — eng yaqin narsa cost modeliga kiritilgan
   "cases where the action was skipped or later overridden".
5. **Artifact yopiq.** Azure production servisi; reproducible harness yo'q.

> **Halol yakun:** REVIX **adaptiv qaror ixtiro qilmaydi** — Narya buni 2020 yilda,
> production'da, bizdan ancha qattiq sharoitda qilgan. REVIX ning da'vosi boshqa joyda:
> **bitta node'da pressure va restart muvaffaqiyati orasidagi bog'liqlikni o'lchash**, va
> buning uchun ta'rif/metrika/benchmark berish. Buni maqolada Introduction'da ochiq
> yozish kerak, Limitations'da emas.

### Sanabria va boshq. — ikkinchi eng yaqin prior art

> **Learning Recovery Strategies for Dynamic Self-healing in Reactive Systems**
> Mateo Sanabria, Ivana Dusparic, Nicolás Cardozo.
> **Proceedings of the 19th International Symposium on Software Engineering for Adaptive
> and Self-Managing Systems (SEAMS '24)**, pp. **133–142**, 2024-04-15.
> DOI **10.1145/3643915.3644097**
> Preprint: arXiv **2401.12405** (2024-01-22), CC BY 4.0
> <https://arxiv.org/abs/2401.12405>

Tasdiqlangan mazmuni (arXiv API + Crossref DOI registri):

- Monitor'lar runtime **predikat** sifatida — "monitors as predicates specifying
  satisfiability conditions of system properties"
- **Reinforcement learning** foydalanuvchining korrektiv harakatlaridan recovery
  strategiyasini o'rganadi
- Strategiyalar **Context-Oriented Programming variatsiyalari** sifatida chiqarilib,
  normal xatti-harakatni dinamik ravishda ustiga yoziladi
- Ikki ilova: mouse-tracking reactive system va **DeltaIoT** exemplar
- Natija: birinchi ilovada failure'larni **55%–92%** holatda aniqlash va tiklash;
  ikkinchisida "at par with the predefined strategies"

#### Sanabria va boshq. — halol taqqoslash

Bu ish REVIX bilan bitta muhim g'oyani baham ko'radi: **recovery strategiyasi oldindan
belgilangan bo'lmasligi kerak**, u kontekstga qarab tanlanishi kerak. Ular buni
Q-learning bilan qiladi va — REVIX uchun qiziq tomoni — monitor'larni *predikat*
sifatida ta'riflaydilar, ya'ni "failure holati" ni domen-maxsus metrikaga emas, mantiqiy
shartga bog'laydilar. Bu REVIX ning contract-asosli verification g'oyasiga metodologik
jihatdan yaqin.

Farqlar, halol:

1. **Qatlam butunlay boshqa.** Ular reactive/COP tilida ishlaydilar (ilova ichidagi
   variatsiyalar), REVIX OS service manager qatlamida (systemd unit'lari). Ularning
   "recovery action" — kod variatsiyasini aktivlashtirish; REVIX'da — process restart.
2. **Resurs pressure yo'q.** PSI, memory pressure, cgroup metrikalari ularning
   signal to'plamida yo'q. Ular funksional predikat buzilishiga reaksiya qiladilar.
3. **Oracle talab qiladi.** Ularning o'rganish signali **foydalanuvchining korrektiv
   harakati** — ya'ni inson oracle'i. REVIX ning `FR-A` metrikasi aniq bunga qarshi
   dizayn qilingan (oracle-free).
4. **Baseline'ga nisbatan natija kamtarin.** Ikkinchi ilovada (DeltaIoT) natija
   "at par with the predefined strategies" — ya'ni o'rganilgan strategiya oldindan
   belgilangandan **ustun chiqmagan.** Bu REVIX ning H2 bo'yicha kutilgan xavfiga
   to'g'ridan-to'g'ri mos keladi (`03-research-gap.md` §4): mavjud statik mexanizm
   foydaning ko'pini olib qo'yishi mumkin. **Bu bizning gipotezamizga qarshi mustaqil
   dalil va uni Limitations'da sitat qilish kerak.**
5. **n va o'lchov qat'iyligi.** Pre-registration, faktorial dizayn, censoring qoidalari
   yo'q. REVIX ning hissasi shu joyda.

> **Bibliografik nozik jihat:** ACM'ning Crossref'ga yuborgan metadata'sida ikkinchi
> muallif **"Ivana Dusaric"** deb yozilgan — bu ACM tomonidagi **imlo xatosi**. To'g'ri
> shakl **Ivana Dusparic** (arXiv yozuvi va shu mualliflarning boshqa Crossref
> yozuvlari bilan tasdiqlangan). Maqolada to'g'ri shakl ishlatiladi.
> Shuningdek arXiv comment venue'ni "Conference" deb ataydi, ACM proceedings sarlavhasi
> esa "Symposium" — nashr etilgan shakl (Symposium) ishlatiladi.

### Bindschaedler — "qayerda restart xavfsiz" degan savol

> **Rebooting Microreboot: Architectural Support for Safe, Parallel Recovery in
> Microservice Systems**
> Laurent Bindschaedler.
> **Proc. 39th GI/ITG International Conference on Architecture of Computing Systems
> (ARCS), 2026** (arXiv journal-ref'da tasdiqlangan). arXiv **2604.09963** (2026-04-11).
> <https://arxiv.org/abs/2604.09963>

Abstraktdan aynan: "in modern microservices **naive restarts are unsafe**"; "Autonomous
remediation agents compound this by actuating raw infrastructure commands without safety
guarantees"; planning va actuation ajratilgan — uch agent (diagnosis, planning,
verification) + **yetti action'li ISA** aniq side-effect semantikasi bilan, va
"a small microkernel **validates and executes each plan transactionally**"; "To determine
**where restart is safe**, we infer recovery boundaries online from distributed traces,
computing minimal restart groups and ordering constraints."

**REVIX uchun:** bu chop etilgan adabiyotda **restart admission control** g'oyasiga eng
yaqin ish — restart bajarilishidan oldin uni tasdiqlaydigan darvoza. Farq: uning darvozasi
**dependency/trace-driven** (topologiya bo'yicha qaysi restart guruhi xavfsiz), REVIX'ning
darvozasi **pressure-driven** (tizim holati restart'ning muvaffaqiyatiga ta'sir qiladimi).
Bundan tashqari u distributed microservice muhitida, REVIX bitta node'da.
⚠️ Uning yakuniy jumlasi REVIX uchun ogohlantirish: "The primary value is safety, not
speed" — ya'ni gating **TTR ni oshiradi**. REVIX ning H2 si aynan shu savdoni yutishi
kerak va bu oson emas.

### Dai va boshq. — `false remediation rate` (FRR)

> **Safe Remediation as Risk-Constrained Intervention Decision in Microservice Systems**
> Chengxiao Dai, Zhaokun Yan, Chenjun Lei, Qiao Li, Luyan Zhang.
> arXiv **2607.20005** (2026-07-22), cs.AI. Peer-reviewed venue **hali yo'q** (preprint).
> <https://arxiv.org/abs/2607.20005>

Men PDF'ni yuklab, FRR ta'rifini o'zim o'qidim. Aynan:

> "The cost `c(s, a)` indicates **false remediation**: executing an action that fails or
> further escalates the incident."

Eksperimentda yorliqlash: "Each action runs in an isolated replica with full state reset,
**labeled** resolved (metrics recover within 60 s), partial, or false remediation (fails
or worsens downstream)." Dataset: 8 320 qaror yozuvi, 1 664 hodisadan; offline training
to'plami **simulyatsiya qilingan** suboptimal operator siyosati bilan generatsiya
qilingan. `ϵsafe = 0.10`.

**REVIX ning `FR-A` ga ta'siri — bu eng muhim tahdid:**

FRR REVIX ning `FR-A` metrikasi bilan **bir xil hodisani** nomlaydi — foyda keltirmagan
yoki zarar qilgan remediation. Demak `04-novelty-statement.md` dagi "mavjud vositalar
… hech biri 'aktor muvaffaqiyat deb e'lon qildi, lekin aslida emas edi' ni metrika
sifatida bermaydi" degan da'vo **juda kuchli** va toraytirilishi kerak.

`FR-A` ning omon qolgan farqi (va u haqiqiy, lekin **tor**):

| | FRR (Dai va boshq.) | `FR-A` (REVIX) |
|---|---|---|
| Nimani o'lchaydi | action **ishlamadi yoki zarar qildi** | aktor **muvaffaqiyat deb e'lon qildi, lekin VR false** |
| Hisoblash uchun kerak | 3 sinfli **yorliqlash** + izolyatsiyalangan replica'da qayta yurgizish + 60 s metrika mezoni | ikki **log'langan fakt** — aktorning o'z signali va contract verification natijasi |
| Oracle | ha (yorliqlar, o'rganilgan risk modeli) | yo'q |
| Aktorga agnostik | yo'q (CMDP agent ichida ta'riflangan) | ha |

> **Halol yakun:** `FR-A` ning novelty'si **"bu hodisani birinchi bo'lib o'lchash" emas** —
> bu 2026-07 dan beri da'vo qilingan. `FR-A` ning novelty'si **oracle'siz va aktorga
> agnostik hisoblanishi**. Bu haqiqiy, lekin ancha tor da'vo, va maqolada aynan shu
> tor shaklda yozilishi kerak. Reviewer FRR ni topadi.

### Qi va boshq. — R2Act, recovery-action evaluation

> **Can LLMs Really Recover Microservice Failures? A Recovery-Aware Evaluation of
> Diagnosis-to-Action Reasoning**
> Jiaxing Qi, Zhongzhi Luan, Hongyu Zhang, Shaohan Huang, Carol Fung, Yongxin Tong,
> Hailong Yang, Depei Qian.
> arXiv **2607.04623** (2026-07-06), cs.SE. Peer-reviewed venue **hali yo'q** (preprint).
> <https://arxiv.org/abs/2607.04623>

Abstraktdan aynan: operator "must translate the diagnosis into a concrete recovery action,
apply it to an **admissible target**, and **verify that service health has been
restored**." R2Act "defines an incident schema, quality gate, action-space representation,
**recovery-validity metrics**, offline evaluator, and live-replay protocol".

**REVIX uchun:** "recovery-validity metrics" + harakatdan keyingi sog'liq verifikatsiyasi
`FR-A` va `C3` ning ikkalasiga ham yaqin. Farq: microservice/LLM-agent domeni, OS service
manager emas; va REVIX'ning verification'i **contract-asosli throughput bandi**, LLM baho
emas. Bu ham FRR bilan bir qatorda "post-recovery verification metrikasi yo'q" degan
da'voni **yopadi**.

### Nogueira & Coelho — reproducible recovery benchmark (actor runtimes)

> **Benchmarking Fault-Tolerance Characteristics of Actor-Based Runtimes**
> Luís Nogueira, Jorge Coelho.
> **Computers** (MDPI), **15(7):439**, 2026-07-10. DOI **10.3390/computers15070439**
> <https://doi.org/10.3390/computers15070439>

Crossref DOI registri orqali tasdiqlangan metadata va abstrakt. Til-mustaqil benchmark
framework; Elixir/BEAM, Scala/Akka, Go/Proto.Actor. O'lchaydi: throughput, reconnection
latency, failure-detection latency — takrorlanuvchi o'tkinchi failure'lar ostida.
Fault modeli abstraktdan aynan: "the **supervised crash recovery** of in-memory,
effectively stateless actor services, in which chat actors are abruptly terminated and
**restarted by their supervisors** while clients rediscover and reconnect to them."
Stateful recovery va multi-node effektlari qamrovdan tashqarida. Xulosasi: "a
**reproducible** benchmarking framework".

**REVIX uchun — bu `C3` ga eng qattiq tahdid.** Bu *reproducible, bitta node'da,
supervisor tomonidan restart qilinadigan* recovery benchmark, 2026-07 da chop etilgan.
Strukturasi REVIX'ning benchmarkiga juda o'xshash, "service manager" o'rniga "actor
supervisor" qo'yilgan. REVIX ning omon qolgan farqlari: (a) OS service manager qatlami
(systemd/supervisord/monit/Pacemaker) emas, **til runtime**'lari; (b) **latency va
throughput** o'lchaydi, recovery **to'g'riligini** emas — false-recovery metrikasi yo'q;
(c) pressure manipulyatsiyasi yo'q; (d) pre-registration yo'q.

### PSI-ni actuator sifatida ishlatgan ishlar — manfiy da'voni buzadigan dalil

> **TMO: Transparent Memory Offloading in Datacenters**
> Johannes Weiner, Niket Agarwal, Dan Schatzberg, Leon Yang, Hao Wang, Blaise Sanouillet,
> Bikash Sharma, Tejun Heo, Mayank Jain, Chunqiang Tang, Dimitrios Skarlatos.
> **ASPLOS '22** (Proc. 27th ACM Int. Conf. on Architectural Support for Programming
> Languages and Operating Systems), pp. **609–621**. DOI **10.1145/3503222.3507731**
> Keyingi jurnal versiyasi: **Communications of the ACM 68(9):102–110**, 2025.
> DOI **10.1145/3746651**

**Bu peer-reviewed ish PSI ni OOM trigger emas, balki graduallashgan control action
(proaktiv memory offloading, Senpai kontrolleri) uchun kirish signali sifatida
ishlatadi.** Shu sababli "PSI faqat OOM/eviction trigger" degan avvalgi da'vo **yolg'on**.

> **A Bounded Reclaim Actuator for PSI-Guided Compressed Memory: A Controlled Ablation**
> Abhiyan Dhakal, Sanjog Sigdel. arXiv **2608.13689** (2026-08-13), cs.OS, 5 bet.
> Peer-reviewed venue yo'q. <https://arxiv.org/abs/2608.13689>

Men PDF'ni o'qidim. Uch konfiguratsiya: (1) zram boshidan yoqilgan; (2) zram **faqat PSI
memory pressure ko'rsatgandan keyin** yoqiladi; (3) zram boshidan + bir martalik 96 MiB
cgroup reclaim so'rovi. Kontroller background cgroup'ning PSI hisoblagichlarini
**1 sekundlik** intervalda o'qiydi. 16 case'li pilot → **180 confirmatory case**
(har arm uchun 60), to'qqiz 1-vCPU Linux VM'da, compute va SQLite workload'lari.
Natija: bounded reclaim compute p99 ni static zram'ga nisbatan **6%** yaxshilagan, SQLite
uchun "statistically indistinguishable"; delayed activation **eng yomon** median p99.
Xulosadan aynan: "so the **predefined decision rule** did not establish a general
responsiveness benefit."

**REVIX uchun ikki jihatdan muhim:**
1. **Mazmun:** PSI bitta Linux node'da **korrektiv actuator'ni** gate qiladi. Restart
   emas, lekin "PSI faqat kuzatuv signali" degan da'voni buzadi.
2. **Metodologiya:** pilot → confirmatory, oldindan belgilangan qaror qoidasi, p99
   natijalar, "statistically indistinguishable" deb halol xabar berish — **REVIX ning
   metodologik shakli bilan deyarli bir xil.** Va natijasi *aralash* chiqdi. Bu REVIX
   uchun ogohlantirish: shu dizayn shu sinf savolda null/aralash natija berishi mumkin.
   ⚠️ Shuningdek "delayed activation eng yomon" natijasi REVIX ning "defer" strategiyasiga
   qarshi mustaqil dalil — Limitations'da sitat qilinishi shart.

> **SchedBlame: Who Ran While You Waited? Culprit-Attributed CPU Contention for
> Containers on Stock Kernels**
> Hao Li, Tonghao Zhang, Honglei Wang. arXiv **2609.02052** (2026-09-02), cs.OS, 12 bet.
> Comment: "Preliminary evaluation". Peer-reviewed venue yo'q.
> <https://arxiv.org/abs/2609.02052>

Abstraktdan aynan: "Pressure stall information, per-cgroup wait counters, and run-queue
latency histograms are all **victim-side**: they report that a container waited, **never
who it waited for**."

**REVIX uchun:** novelty tahdidi emas, lekin **reviewer e'tirozi**. REVIX PSI dan
"restart yordam beradimi" degan xulosa chiqarsa, bu ish PSI ning victim-side ekanini
eslatadi — yuqori pressure *sababini* ko'rsatmaydi. H1 ning kauzal talqini shu e'tirozni
oldindan qarshi olishi kerak.

### Brown & Patterson — availability benchmark'ning kanonik namunasi

> **Towards Availability Benchmarks: A Case Study of Software RAID Systems**
> Aaron Brown, David A. Patterson (Computer Science Division, UC Berkeley).
> **2000 USENIX Annual Technical Conference**, June 18–23, 2000, San Diego, California.
> <https://www.usenix.org/legacy/event/usenix2000/general/full_papers/brown/brown_html/>

Tasdiqlangan metodologiya: nazorat ostidagi **fault injection** (emulyatsiya qilingan disk
— correctable/uncorrectable media error, hardware error, parity error, power failure, disk
hang); mavjud performance benchmark (**SPECWeb99**) uzluksiz workload generatori sifatida;
**QoS metrikasi vaqt bo'yicha**, availability'ni binary up/down deb emas; single-fault
microbenchmark va multi-fault macrobenchmark ajratilgan; natijalar grafik + confidence
interval bilan.

**REVIX uchun — bu `C3` ni jiddiy toraytiradi.** REVIX ning "verified recovery
throughput bandi bilan, liveness emas" g'oyasi **shakl jihatidan 2000 yilda Brown &
Patterson tomonidan qilingan**, va Linux'da. ROC hisoboti buni `[Brown00]` deb sitat
qiladi va benchmark mavzusini "we do not cover the topic in this paper" deb unga
yo'llaydi. Demak REVIX **metodologiyani ixtiro qilmaydi** — u uni yangi qatlamga
(service manager) va yangi stressorga (pressure) ko'chiradi. Buni ochiq yozish kerak.

### Asos — autonomic va recovery-oriented computing (hammasi tasdiqlangan)

> **The vision of autonomic computing**
> J. O. Kephart, D. M. Chess. **Computer 36(1):41–50**, 2003-01.
> DOI **10.1109/MC.2003.1160055** (Crossref registri orqali tasdiqlangan)

**MAPE-K** loop'ning kelib chiqishi. REVIX quvuri MAPE-K ning bir ko'rinishi.

> **Recovery Oriented Computing (ROC): Motivation, Definition, Techniques, and Case
> Studies**
> David Patterson, Aaron Brown, Pete Broadwell, George Candea, Mike Chen, James Cutler,
> Patricia Enriquez, Armando Fox, Emre Kıcıman, Matthew Merzbacher, David Oppenheimer,
> Naveen Sastry, William Tetzlaff, Jonathan Traupman, Noah Treuhaft.
> **Computer Science Technical Report UCB//CSD-02-1175, U.C. Berkeley**, **March 15, 2002**.
> <http://roc.cs.berkeley.edu/papers/ROC_TR02-1175.pdf>

Men birlamchi PDF'ni o'qidim. To'liq muallif ro'yxati yuqorida (avvalgi versiyada
"va boshq." bilan qisqartirilgan edi).

⚠️ **Avvalgi da'vo tuzatildi.** Hujjatda "ROC aynan 'recovery benchmark' va tizimli xato
kiritishni talab qilgan" deb yozilgan edi. Aniqroq shakl — PDF'dan aynan:

> "Progress on performance was so quick in part because we had a common yardstick–
> benchmarks–to measure success. To make such rapid progress on recovery, we need similar
> incentives. Prior work has **successfully benchmarked availability** [Brown00][Brown02],
> and so **we do not cover the topic in this paper**."

va

> "We need to continue the quest for real failure data and to develop useful
> **availability and maintainability benchmarks**."

va

> "We note the importance of **recovery experiments** in evaluating virtually all our
> proposals."

Demak ROC **availability va maintainability benchmark**larini va **recovery
experiment**larini talab qiladi, va benchmark qurishni Brown & Patterson ishiga
havola qiladi. "Recovery benchmark" — REVIX ning atamasi, ROC ning emas. Bu farq
kichik, lekin maqolada ROC ni noto'g'ri sitat qilmaslik uchun muhim.

| Manba | Tasdiqlangan metadata | Ahamiyati |
|---|---|---|
| **Microreboot—A Technique for Cheap Recovery**. George Candea, Shinichi Kawamoto, Yuichi Fujiki, Greg Friedman, Armando Fox (Stanford University). **OSDI '04**, pp. **31–44**. <https://www.usenix.org/legacy/event/osdi04/tech/candea.html> | USENIX sahifasi | arzon restart granularligi |
| **Recursive Restartability: Turning the Reboot Sledgehammer into a Scalpel**. George Candea, Armando Fox (Stanford University). **Proceedings of the 8th Workshop on Hot Topics in Operating Systems (HotOS-VIII), May 2001**. <http://roc.cs.berkeley.edu/papers/recursive_restartability.pdf> | birlamchi PDF sarlavha sahifasi | restart granularligi va dependency |
| **Crash-Only Software**. George Candea, Armando Fox (Stanford University). **Proceedings of the 9th Workshop on Hot Topics in Operating Systems (HotOS-IX), May 2003**. <https://dslab.epfl.ch/pubs/crashonly.pdf> | birlamchi PDF sarlavha sahifasi | restart'ni birinchi darajali recovery sifatida |
| **JAGR: an autonomous self-recovering application server**. G. Candea, E. Kiciman, S. Zhang, P. Keyani, A. Fox. **2003 Autonomic Computing Workshop**, pp. **168–177**. DOI **10.1109/ACW.2003.1210217** | Crossref | avtonom recovery, microreboot amaliyoti |
| **A survey on self-healing systems: approaches and systems**. Harald Psaier, Schahram Dustdar. **Computing 91(1):43–73**. DOI **10.1007/s00607-010-0107-y** | Crossref | survey |
| **Self-healing systems — survey and synthesis**. Debanjan Ghosh, Raj Sharman, H. Raghav Rao, Shambhu Upadhyaya. **Decision Support Systems 42(4):2164–2185**, 2007. DOI **10.1016/j.dss.2006.06.011** | Crossref | survey |

> ⚠️ **Psaier & Dustdar yil nozikligi:** Crossref'da `issued` = **2010-08-05** (online
> first), jild/son esa **91(1)** va bu **2011** yilning bosma soni. Avvalgi hujjatda
> "2011" deb yozilgan — bu bosma yil bo'yicha to'g'ri. Maqolada chalkashlikni oldini
> olish uchun DOI berilishi kerak.

### Restart'ni birinchi darajali dizayn primitivi sifatida (embedded / CPS)

| Manba | Tasdiqlangan metadata |
|---|---|
| **Restart-Based Fault-Tolerance: System Design and Schedulability Analysis**. Fardin Abdi, Renato Mancuso, Rohan Tabish, Marco Caccamo. **2017 IEEE 23rd International Conference on Embedded and Real-Time Computing Systems and Applications (RTCSA)**, pp. **1–10**. DOI **10.1109/RTCSA.2017.8046320**. Preprint: arXiv **1705.02412** (2017-05-05) | arXiv API + Crossref |
| **Application and system-level software fault tolerance through full system restarts**. Fardin Abdi, Rohan Tabish, Matthias Rungger, Majid Zamani, Marco Caccamo. **Proceedings of the 8th International Conference on Cyber-Physical Systems (ICCPS 2017)**, pp. **197–206**. DOI **10.1145/3055004.3055012** | Crossref |

⚠️ **Tuzatish:** avvalgi hujjat `arXiv 1705.02412` ni "*Restart-Based Fault-Tolerance*"
deb qisqa nom bilan T3 ga qo'ygan edi. To'liq sarlavha va **peer-reviewed venue (RTCSA
2017)** topildi. Bu ish REVIX uchun ahamiyatli: restart *rejalashtirilgan* recovery
primitivi sifatida, timing kafolatlari bilan — ya'ni "restart qachon xavfsiz" savolining
real-time varianti.

### Adaptiv / o'rganiladigan recovery — qolgan tasdiqlangan manbalar

| Manba | Tasdiqlangan metadata | Ahamiyati |
|---|---|---|
| **CRRL: A Causality-Based Reinforcement Learning Framework for Autonomous System Recovery**. Safia Fatima, Kai Olav Ellefsen, Leon Moonen. arXiv **2607.03177** (2026-07-03), cs.SE, 30 bet. Peer-reviewed venue **yo'q** | arXiv API | RL recovery; "RL policies often **stall in failure states**"; heuristic recovery'ni pretrained PPO ga qo'shish reward'ni **yomonlashtiradi** — REVIX uchun ogohlantirish |
| **Adaptive Fault Injection Planning for Multi-Layer Self-Healing AI Infrastructure**. Saurabh Kulkarni, Yuxin Yang, Rohan Kulkarni, Gautam Nayak. arXiv **2607.16161** (2026-07-17), cs.ET. Peer-reviewed venue **yo'q** | arXiv API | ADA-ST; fault-propagation graph; 72 550 repair ticket. **`C3` ning fault-injection qamrovi argumentiga yaqin** |
| **When web apps heal themselves: a MAPE-K based approach to fault tolerance and adaptive recovery**. **Sales G. Aribe Jr.**, Rov Japheth G. Oracion. **International Journal of Informatics and Communication Technology (IJ-ICT) 15(2):729–740**, 2026-06-01. DOI **10.11591/ijict.v15i2.pp729-740** (nashriyot: Institute of Advanced Engineering and Science). Preprint: arXiv **2605.19261** | Crossref + arXiv API | MAPE-K + fault injection, **20 scenario**; recovery success rate 93.2%, TTR 56.2% → 3.92 s. Past darajali venue, lekin framing yaqin va **recovery success rate** metrikasi bor |
| **Self-Healing Software Systems: Lessons from Nature, Powered by AI**. Mohammad Baqar, Rajat Khanda, Saba Naqvi. arXiv **2504.20093** (2025-04-25), cs.SE. **Peer-reviewed emas, venue yo'q** | arXiv API | vision/framework maqolasi; peer-reviewed adabiyot haqidagi da'voni qo'llab-quvvatlash uchun **ishlatilmaydi** |
| **Gandalf: An Intelligent, End-To-End Analytics Service for Safe Deployment in Large-Scale Cloud Infrastructure**. Ze Li, Qian Cheng, Ken Hsieh, Yingnong Dang, Peng Huang, Pankaj Singh, Xinsheng Yang, Qingwei Lin, Youjiang Wu, Sebastien Levy, Murali Chintalapati. **NSDI '20** (17th USENIX Symposium on Networked Systems Design and Implementation), pp. **389–402**, ISBN 978-1-939133-13-7 | USENIX sahifasi | ⚠️ **izoh tuzatildi** — pastga qarang |
| **DeepLog: Anomaly Detection and Diagnosis from System Logs through Deep Learning**. Min Du, Feifei Li, Guineng Zheng, Vivek Srikumar. **Proceedings of the 2017 ACM SIGSAC Conference on Computer and Communications Security (CCS '17)**, pp. **1285–1298**. DOI **10.1145/3133956.3134015** | Crossref (mualliflar, venue, betlar) + Semantic Scholar (to'liq sarlavha) | log'dan anomaliya aniqlash |
| **Large-scale cluster management at Google with Borg**. Abhishek Verma, Luis Pedrosa, Madhukar Korupolu, David Oppenheimer, Eric Tune, John Wilkes. **Proceedings of the Tenth European Conference on Computer Systems (EuroSys '15)**, pp. **1–17**. DOI **10.1145/2741948.2741964** | Crossref | task restart/reschedule |
| **Improving the reliability of commodity operating systems** (tizim nomi: **Nooks**). Michael M. Swift, Brian N. Bershad, Henry M. Levy. **ACM Transactions on Computer Systems 23(1):77–110**, 2005. DOI **10.1145/1047915.1047919**. Konferentsiya versiyasi: **SOSP '03**, pp. 207–222, DOI **10.1145/945445.945466** | Crossref | driver izolyatsiyasi va tiklash |

⚠️ **Gandalf izohi tuzatildi.** Avvalgi hujjatda Gandalf "Narya shu paket ichida" deb
izohlangan edi. **Bu noto'g'ri.** Gandalf — **safe deployment** tizimi: fault
signal'larni davom etayotgan rollout'lar bilan spatial/temporal korrelyatsiya qiladi,
ensemble ranking bilan qaysi rollout sababchi ekanini aniqlaydi va binary classifier
bilan ta'sirni baholaydi (data-plane: 92.4% precision / 100% recall; control-plane:
94.9% / 99.8%). U Narya bilan **mualliflarni** baham ko'radi (Dang, Huang, Lin, Wu, Levy,
Chintalapati) va bir xil Azure kontekstida, lekin **boshqa muammoni** hal qiladi.
Gandalf'ning REVIX uchun to'g'ri ahamiyati: u **`G4` (config/deployment-change
provenance)** ga eng yaqin prior art — "qaysi o'zgarish bu failure'ni keltirib chiqardi"
savolini fleet miqyosida hal qiladi. `G4` kelajakda qaytilsa, Gandalf asosiy prior art
bo'ladi.

⚠️ **Nooks tuzatildi.** Avvalgi hujjat "Swift va boshq. *Nooks* (TOCS)" deb yozgan edi.
**Nooks — tizim nomi, maqola sarlavhasi emas.** Maqola sarlavhasi "Improving the
Reliability of Commodity Operating Systems", TOCS 23(1), 2005.

⚠️ **DeepLog bibliografik nozikligi:** ACM'ning Crossref'ga yuborgan metadata'sida
sarlavha faqat "DeepLog" deb qisqartirilgan; to'liq sarlavha Semantic Scholar'dan
olindi. Semantic Scholar esa ikkinchi muallifni "**Fei-Fei Li**" deb ko'rsatadi — bu
S2 ning **muallif disambiguation xatosi** (Stanford'dagi Fei-Fei Li bilan chalkashtirgan).
To'g'ri shakl **Feifei Li** (Crossref bo'yicha). Maqolada Crossref muallif ro'yxati
ishlatiladi.

### Kernel infratuzilmasi — PSI (to'liq tasdiqlangan)

> **`psi: pressure stall information for CPU, memory, and IO`**
> Johannes Weiner `<hannes@cmpxchg.org>`, commit **`eb414681d5a0`**
> (to'liq SHA `eb414681d5a07d28d2ff90dc05f69ec6b232ebd2`), **2018-10-26**.
> Tekshirilgan: `torvalds/linux` rasmiy mirror, GitHub API.

Tasdiqlangan faktlar:
- **Linux 4.20** birinchi release: `kernel/sched/psi.c` **v4.19'da yo'q** (HTTP 404),
  **v4.20'da bor** (blob `fe24de3fbc93805f0c1e913a85657a15d141ad2f`). Demak "4.20" to'g'ri.
- `Documentation/accounting/psi.txt` (v4.20) dan: "Pressure information for each resource
  is exported through the respective file in **`/proc/pressure/`** — cpu, memory, and io",
  format `some avg10= avg60= avg300= total=` va memory/IO uchun qo'shimcha `full` qatori.
  Demak **10/60/300 s oynalar** to'g'ri.
- `CONFIG_PSI` `init/Kconfig` da; commit `kernel/sched/psi.c`, `mm/vmscan.c`,
  `mm/page_alloc.c`, `mm/compaction.c`, `mm/filemap.c` ni o'zgartiradi.

> ⚠️ **Kernel hujjatining o'z niyati — manfiy da'vo uchun muhim.** `psi.txt` dan aynan:
> "As psi aggregates this information in realtime, systems can be managed dynamically
> using techniques such as load shedding, migrating jobs to other systems or data centers,
> or **strategically pausing or killing low priority or restartable batch jobs**."
>
> Ya'ni **pressure-driven lifecycle harakati PSI ning birinchi kunidan e'lon qilingan
> niyati**. Bu "hech kim PSI ni lifecycle qaroriga ishlatishni o'ylamagan" degan
> talqinni bekor qiladi. Aniq farq: bu jumla *restartable* ishlarni **o'ldirish** haqida,
> **qachon restart qilishni hal qilish** haqida emas. REVIX ning da'vosi shu ingichka
> farqda turadi va u shu darajada aniq yozilishi kerak.

### Kubernetes KEP — tasdiqlangan

> **KEP #5734 — "Automated Pod Hard Reset Policy for Persistent CrashLoopBackOff"**
> `kubernetes/enhancements` issue #5734. Ochilgan **2025-12-12**, yopilgan
> **2026-06-18**, `state_reason` = **`not_planned`**.
> Label'lar: `sig/apps`, `sig/node`, **`lifecycle/rotten`**.

Avvalgi hujjatning "'not planned' deb yopilgan" da'vosi **to'g'ri**. Nozik jihat:
`lifecycle/rotten` label'i shuni ko'rsatadi — u **texnik asosda rad etilmagan, balki
e'tiborsizlikdan eskirib avtomatik yopilgan**. Maqolada "Kubernetes buni rad etdi"
deb yozish **noto'g'ri** bo'ladi.

### OSS prior art — tasdiqlangan artifact'lar

> **`prethivganeshm2023-del/adaptive-self-healing-runtime`** (GitHub)
> <https://github.com/prethivganeshm2023-del/adaptive-self-healing-runtime>
> GitHub API: yaratilgan **2026-09-17**, oxirgi push **2026-09-27**, **0 star**,
> **litsenziya YO'Q**, arxivlanmagan.
> Rasmiy tavsifi: "An ML-assisted Linux runtime that detects service failures, diagnoses
> incidents, and performs controlled automated recovery using systemd, journald, and
> process telemetry."

O'zim tasdiqlagan mazmuni: systemd + journald + **psutil** telemetriyasi;
`RESTART`/`STOP`/`ESCALATE` orasidan qaror; **exponential backoff** (1s→2s→4s→8s);
**`VERIFYING` state** — "the service must remain healthy for the configured verification
period"; rule-based **va** ML diagnostika; post-recovery validation; sintetik training
data; o'zini "a research and engineering prototype" deb ataydi.

> **Bu REVIX ning "aniq" arxitekturasi — allaqachon yozilgan.** Peer-reviewed emas, lekin
> reviewer buni topadi. **Litsenziya yo'qligi muhim:** kodni qayta ishlatish mumkin emas,
> faqat sitat qilinadi. Yana bir nozik jihat: repozitoriy REVIX bilan **bir vaqtda**
> yozilayotgan (2026-09), ya'ni bu "ilgari qilingan ish" emas, **parallel ish** — buni
> maqolada to'g'ri ifodalash kerak.

> **`advaithsarva/self-healing-system-agent`** (GitHub)
> <https://github.com/advaithsarva/self-healing-system-agent>
> GitHub API: yaratilgan **2026-08-27**, oxirgi push **2026-09-17**, **1 star**,
> **litsenziya YO'Q**.
> Rasmiy tavsifi (aynan): "Autonomous agent that diagnoses machine faults from learned
> baselines and remediates them through a gated capability table, then re-measures to
> verify. **200 seeded trials: 0 false positives, 0 missed faults, 120/120 fixes
> verified.**"

Avvalgi hujjat bu manbani "Men tekshirmadim" deb T2 ga qo'ygan edi. Endi
**mavjudligi va da'vosi tasdiqlandi** (repozitoriy tavsifidan). Lekin:

> ⚠️ **"0 false positives" da'vosi — auditdan o'tmagan o'z-o'zini hisoboti.** Men
> `eval/` natijalarini qayta yurgizmadim. Muhimi: bu artifact **remediation'da false
> positive'ni metrika sifatida da'vo qiladi**, ya'ni `FR-A` ga kontseptual jihatdan
> yaqin. Reviewer buni topsa, "FR-A birinchi" degan da'vo yana zaiflashadi.
> `FR-A` ning farqi baribir kuchli: bu yerda "false positive" **fault aniqlash** bo'yicha,
> aktorning **muvaffaqiyat da'vosi** bo'yicha emas.

### Mahalliy tekshirilgan texnik faktlar

`systemd.service(5)` / `systemd.unit(5)` man sahifalari, **systemd 261 (261.2-1)**, bu
mashinada:
- `RestartSteps=`, `RestartMaxDelaySec=` mavjud (misol: `RestartSec=10s`, `RestartSteps=4`,
  `RestartMaxDelaySec=160s`)
- `ExecCondition=`, `WatchdogSec=`, `StartLimitIntervalSec=`, `RestartMode=` mavjud
- **`ConditionMemoryPressure=` / `ConditionCPUPressure=` / `ConditionIOPressure=` mavjud
  (v250 dan)** — yuqoridagi birinchi bo'limga qarang
- Kubernetes uslubidagi health probe direktivi **yo'q**

`/usr/lib/systemd/system/user@.service.d/10-oomd-user-service-defaults.conf`:
`ManagedOOMMemoryPressure=kill`, `ManagedOOMMemoryPressureLimit=50%`;
`DefaultMemoryPressureDurationSec=20s`.

Batafsil: [`01-texnologiya-auditi.md`](01-texnologiya-auditi.md).

### Amaliyotchi dalili — H1 uchun mustaqil qo'llab-quvvatlash

> **systemd issue #13922 — "systemd gives up on restarting journald under memory
> pressure"**
> <https://github.com/systemd/systemd/issues/13922>
> Ochilgan **2019-11-02**, holati **OPEN** (7 yildan ortiq), 3 comment.
> Label'lar: `needs-discussion 🤔`, `journal`, `needs-reporter-feedback ❓`

Issue matnidan aynan: "When the system is under memory pressure, `systemd-journald` often
fails because is `malloc()`s fail, and shuts down… Then I observe on my system that it
dies and is **never restarted** by systemd… `Restart = always` by default… but contrary to
the name that is not enough to make a systemd service restart forever; **it will give up
after a couple of tries.** It needs `StartLimitIntervalSec = 0`… otherwise the restart
counter will prevent the service from retrying."

**REVIX uchun — bu juda qimmatli topilma.** Bu aynan H1 mexanizmining amaliyotdagi
hisoboti: memory pressure → restart urinishi muvaffaqiyatsiz → `StartLimitBurst`
tugaydi → xizmat **butunlay o'chib qoladi**. Ya'ni REVIX o'lchamoqchi bo'lgan hodisa
haqiqiy, xabar qilingan, va **7 yildan ortiq hal qilinmagan**.

> ⚠️ **Ehtiyot:** issue'da "memory pressure" **so'zlashuv ma'nosida** ishlatilgan —
> PSI yoki `/proc/pressure` haqida gap yo'q. Bu PSI prior art emas; bu **fenomen
> dalili**. Maqolada aynan shu tarzda ishlatilishi kerak: motivatsiya, PSI sitat emas.

---

## T2 — Tasdiqlanishi kerak (men avtoritativ sahifani ochmadim)

### systemd PSI shartining kelib chiqishi
`systemd/systemd` issue **#20139** ("RFE: skip job activation if not enough system
resources (CPU/memory) are available") va PR **#21437** ("core: add
Condition[Memory/CPU]Pressure", merged 2021-12-01). Subagent skanida topilgan;
**men bu sahifalarni o'zim ochmadim.** Feature'ning **o'zi** man sahifasi orqali T1
(yuqoriga qarang) — bu yerdagi T2 faqat **provenance/dizayn muhokamasi** haqida.
Maqolada dizayn mulohazasini (masalan "skip vs defer" bahsi) sitat qilish kerak bo'lsa,
bu avval T1 ga ko'tarilishi shart.

### Cloud / microservice remediation benchmark'lari
Subagent skanida topilgan, **men ochmadim** — `C3` ni scope qilish uchun muhim, chunki
ular birgalikda "remediation benchmark yo'q" degan da'voni cloud kontekstida yopadi:

| Manba (skandan, tasdiqlanmagan) | Nima uchun muhim |
|---|---|
| *SRE-Marathon: A Continuous, Change-Driven Benchmark for Autonomous Site Reliability Agents*, arXiv 2609.33023 | Kubernetes, seeded fault schedule |
| *SREGym: A Live Benchmark for AI SRE Agents with High-Fidelity Failure Scenarios*, arXiv 2605.07161 | live cloud-native stack |
| *Cloud-OpsBench: A Reproducible Benchmark for Agentic Root Cause Analysis in Cloud Systems*, arXiv 2603.00468 | 754 case, 57 fault turi |
| *AIOpsLab*, arXiv 2501.06706 (Microsoft) | diagnosis + mitigation |
| *ITBench*, arXiv 2502.05352 (IBM) | 94 scenario |
| *MicroRemed: Benchmarking LLMs in Microservices Remediation*, arXiv 2511.01166 | "**first benchmark**" da'vosi |

⚠️ **Bu ro'yxat `C3` ning formulasiga bevosita ta'sir qiladi.** REVIX ning benchmark
da'vosi **hech qanday holatda** "remediation benchmark yo'q" deb yozilmaydi.

### Boshqa yaqin ishlar (skandan, tasdiqlanmagan)
- *Evaluation of IoT Self-healing Mechanisms using Fault-Injection in Message Brokers*,
  arXiv 2203.12960 — fault-injection bilan self-healing baholashning metodologik namunasi
- *Self-Healing Harness for Runtime Oversight of Agent Self-Modification*, arXiv 2609.24130
  — "admission control for self-modification" iborasi ishlatilgan
- *A reinforcement learning framework for self-healing fault recovery in intent-based SDNs*,
  *Discover Networks* 2:14 (2026), DOI 10.1007/s44354-026-00028-z — o'rganilgan action
  space'da **no-op va switch restart** bor. ⚠️ Springer auth orqasida, muallif ro'yxati
  **tasdiqlanmagan** — snippet'ga tayanib sitat qilinmaydi
- *SARA: A Stall-Aware Memory Allocation Strategy for Mixed-Criticality Systems*,
  arXiv 2511.19991 — PSI-asosli metrika, "proactively drop affected jobs"
- *AppFlow: Memory Scheduling for Cold Launch of Large Apps on Mobile and Vehicle Systems*,
  arXiv 2603.17259 — "restart cost" kill/relaunch qaroriga kirish sifatida
- `Apexyunhnao/self-healing-agent` (GitHub) — "**Verification Escape Rate**" metrikasi,
  35 scenario. ⚠️ **`FR-A` nomlanishiga eng yaqin prior art**, lekin Windows-only va
  peer-reviewed emas. Men ochmadim — **ko'tarilishi shart**

### Ishlab chiqarish tizimlari
Pacemaker/Corosync (`on-fail`, `migration-threshold`, `failure-timeout`, OCF `monitor`),
Kubernetes (CrashLoopBackOff 10→300 s, probe'lar, node-pressure eviction),
monit, supervisord, runit/s6, greenboot, systemd Automatic Boot Assessment, rpm-ostree,
snapd, ChromeOS `update_engine`, Android AVB, OpenStack Masakari, AWS ASG health checks,
Event-Driven Ansible, Sensu remediation.

Batafsil taqqoslash: [`01-texnologiya-auditi.md`](01-texnologiya-auditi.md) §6.

### Chaos / fault injection
`stress-ng`, `chaosblade` (CNCF sandbox, Alibaba), Chaos Mesh, LitmusChaos, `pumba`.
Shuningdek *FaultSee: Reproducible Fault Injection in Distributed Systems*,
**EDCC 2020**, DOI 10.1109/EDCC51268.2020.00014 (Crossref qidiruvida ko'rindi, sahifasini
ochmadim).

Tekshirilmagan, metodologiya yozishdan oldin tasdiqlanishi kerak: Linux
`CONFIG_FAULT_INJECTION` (`failslab`, `fail_page_alloc`, `fail_make_request`), `tc netem`
tafsilotlari, `dm-flakey`, `dm-delay`. Shuningdek **DBench** oilasi (DBench-OS,
DBench-OLTP, DBench-FI) va Kanoun & Spainhower, *Dependability Benchmarking for Computer
Systems* — ROC an'anasidagi benchmark prior art, `C3` uchun muhim.

---

## T3 — SITAT QILINMAYDI

Faqat eslatib o'tilgan yoki snippet darajasida ko'rilgan:

- Netflix chaos vositalari — bu skanda ham tekshirilmadi
- PandaStack blog posti ("PSI Explained: Safe Memory Oversubscription", 2026-09-04) —
  PSI ni admission gate sifatida tavsiflaydi, lekin **peer-reviewed emas, sanoat blogi**;
  men ochmadim. Novelty muhokamasida ishlatilmaydi
- SD Times, "The False-Heal Problem in AI Test Automation" (2026-09-02) — "**false heal**"
  atamasining nomlanish presedenti, lekin UI test avtomatizatsiyasi domeni; men ochmadim
- Zenodo 19408576; arXiv 2601.09393, 2507.13757, 2512.23499, 2506.22185, 2608.15016,
  2606.01416, 2609.34701, 2605.06737, 2609.29015, 2601.00339, 2601.22352, 2511.20663,
  2609.13672, 2609.11264, 2602.09345, 2404.03079, 2608.11836, 2605.18755 — barchasi
  subagent skanida snippet/abstrakt darajasida; men hech birini ochmadim
- `github.com/8ven0m8/FaultBench-Industrial`; `claudegoogl-sudo/paperclip` PR #370;
  `bot-forgeai/forgeai-build` PR #87; `kenmclennan/lightcycle` PR #638;
  `openclaw/openclaw` issue #138348 — shovqin darajasida, sifat tekshirilmagan
- *Reboot-based Recovery of Performance Anomalies* — manba tasdiqlanmagan

**ResearchGate-da topilgan "RL self-healing infrastructure" natijalari predatory /
peer-reviewed emasga o'xshaydi → butunlay chiqarib tashlanadi.**

---

## Tizimli qidiruv — manfiy da'voning reproducible asosi

**Bajarilgan sana:** 2026-09-29. **Bajaruvchi:** literature verification sessiyasi.
Maqsad: `01`–`04` hujjatlarida **preliminary** deb belgilangan manfiy da'voni
tasdiqlash yoki rad etish.

### Qamrab olingan bazalar va metod

| Baza | Kirish usuli | Holat |
|---|---|---|
| **arXiv** | `http://export.arxiv.org/api/query` (rasmiy API) | ✅ 12 so'rov bajarildi |
| **Crossref** | `https://api.crossref.org/works` (DOI registri) | ✅ 12 so'rov bajarildi |
| **USENIX** (OSDI/NSDI/ATC/HotOS) | `usenix.org` sahifalari + domen-cheklangan qidiruv | ✅ qismli |
| **Linux kernel git** | `torvalds/linux` rasmiy mirror, GitHub API | ✅ |
| **systemd issue tracker** | `gh search issues/prs --repo systemd/systemd` | ✅ |
| **Kubernetes enhancements** | GitHub API | ✅ |
| **mahalliy `man`** | systemd 261 (261.2-1) | ✅ |
| **Semantic Scholar** | `api.semanticscholar.org/graph/v1` | ❌ **11 so'rovdan 10 tasi HTTP 429** — amalda qidirilmagan |
| **lore.kernel.org** (LKML arxivi) | `?q=` qidiruv | ❌ **Anubis bot-himoyasi**; bypass qilinmadi (taqiqlangan) |
| **DBLP** | `dblp.org`, `dblp.uni-trier.de` | ❌ **Anubis bot-himoyasi** |
| **IEEE Xplore** | to'g'ridan-to'g'ri | ❌ bloklangan; faqat **Crossref DOI metadata** orqali |
| **ACM DL** | to'g'ridan-to'g'ri | ❌ HTTP 403; faqat **Crossref DOI metadata** orqali |
| **Google Scholar** | — | ❌ programmatik kirish yo'q |

### Bajarilgan so'rovlar (arXiv API, `search_query`)

```
all:"pressure stall information"                          → totalResults = 2
all:"pressure stall information" AND all:recovery         → 0
all:"pressure stall information" AND all:restart          → 0
all:"memory pressure" AND all:"restart decision"          → 0
all:"restart admission control"                           → 0
all:"false recovery"                                      → 3  (hech biri CS recovery emas)
all:"recovery benchmark"                                  → 16 (hech biri OS/service emas)
all:"self-healing benchmark"                              → 0
all:"restart success rate"                                → 0
all:"MAPE-K" AND all:systemd                              → 0
all:systemd AND all:recovery AND all:evaluation           → 0
all:"pressure-aware" AND all:recovery                     → 0
```

`all:"pressure stall information"` **butun arXiv'da faqat 2 ta maqola** qaytardi:
**2608.13689** (PSI-guided reclaim) va **2609.02052** (SchedBlame). Ikkalasi ham yuqorida
T1 da tahlil qilingan; **ikkalasi ham restart/recovery qarori emas.**

### Bajarilgan so'rovlar (Crossref, `query.bibliographic`)

```
pressure stall information                    | pressure stall information recovery
pressure stall information restart            | memory pressure restart decision service
restart admission control                     | false recovery metric self-healing
recovery benchmark service manager Linux      | self-healing benchmark fault injection reproducible
service restart success rate measurement      | MAPE-K Linux systemd service recovery
systemd recovery evaluation experiment        | pressure aware failure recovery Linux cgroup
```

**Natija:** Crossref relevance-ranked, shuning uchun `total-results` ma'nosiz (millionlar).
Muhimi — **top natijalarda birortasi ham tegishli emas**: "pressure stall" so'rovlari
**aerodinamik stall** (qanot, kompressor), **qon bosimi**, va **turbomashina** maqolalarini
qaytardi. Bu Crossref indeksida PSI (Linux) adabiyoti bu atamalar bilan **yo'q** ekanini
ko'rsatadi. Tegishli chiqqan yagona narsalar: **FaultSee (EDCC 2020)** va
**ClosRCA-Bench** (Authorea preprint, tekshirilmagan).

### Bajarilgan so'rovlar (systemd / Kubernetes tracker)

```
gh search issues --repo systemd/systemd "pressure"              → #13922 topildi (T1 ga)
gh search issues --repo systemd/systemd "MemoryPressureWatch"   → tegishli emas
gh search issues --repo systemd/systemd "restart under memory pressure" → 0
gh search issues --repo systemd/systemd "PSI pressure stall"    → 0
gh search issues --repo systemd/systemd "TimeoutStartSec memory pressure" → 0
gh api repos/kubernetes/enhancements/issues/5734                → tasdiqlandi
```

### Qidiruvning ochiq zaifliklari — halol ro'yxat

Bu ro'yxat manfiy da'voning **chegarasini** belgilaydi. Uni maqolada yashirish
mumkin emas.

1. **arXiv API faqat sarlavha + abstrakt + comment'ni indekslaydi, to'liq matnni EMAS.**
   PSI ni *metodida* ishlatgan lekin abstraktda eslatmagan maqola bu qidiruvda
   **ko'rinmaydi**. Bu eng katta teshik.
2. **Semantic Scholar amalda qidirilmadi** (11 so'rovdan 10 tasi HTTP 429).
3. **lore.kernel.org va DBLP Anubis bot-himoyasi orqasida.** Bot-detection'ni chetlab
   o'tish taqiqlangan, shuning uchun bu ikki manba **qidirilmagan** deb hisoblanadi.
   LKML — tegishli thread yashirinishi ehtimoli eng yuqori joy.
4. **IEEE Xplore va ACM DL ning o'z qidiruv interfeyslariga kirilmagan** — faqat
   Crossref DOI metadata orqali. DSN, ISSRE, SEAMS, ICSE, EuroSys, Middleware
   proceedings'i **to'g'ridan-to'g'ri sanab chiqilmagan**.
5. **"PSI" akronim kolliziyasi.** Umumiy akademik qidiruvda "PSI" deyarli butunlay
   **Private Set Intersection** kriptografiyasini qaytaradi. Shu sababli faqat
   `"pressure stall information"` to'liq iborasi ishonchli; bu esa qisqartma ishlatgan
   maqolalarni o'tkazib yuborishi mumkin.
6. **Google Scholar ishlatilmagan** (programmatik kirish yo'q).

### Takrorlash uchun

Yuqoridagi so'rovlar `arxiv-log.txt`, `crossref-log.txt`, `s2-log.txt` fayllarida
to'liq chiqish bilan saqlangan (sessiya scratchpad'i). Qidiruv skriptlari deterministik:
bir xil `search_query` va bir xil API endpoint'lar. Har kim `export.arxiv.org` va
`api.crossref.org` ga bir xil so'rovlarni yuborib natijani qayta hosil qila oladi.

---

## Manfiy topilma — QAYTA YOZILGAN

> ⚠️ **Bu bo'lim to'liq qayta yozildi. Avvalgi shakli YOLG'ON edi.**

### Avvalgi da'vo va nima uchun u yolg'on

Avvalgi matn shunday edi:

> ~~"PSI ni failure detection yoki recovery qaroriga kirish signali sifatida ishlatgan
> peer-reviewed maqola TOPILMADI. PSI faqat OOM/eviction trigger sifatida iste'mol
> qilinadi. Shuningdek, Linux service manager'lar uchun 'false recovery' metrikasi yoki
> recovery benchmark topilmadi."~~

Bu da'vo **uch joyda rad etildi**:

1. **`ConditionMemoryPressure=` (systemd v250, 2021).** PSI chegarasi unit start job'ining
   bajarilishini gate qiladi, va start job'lar — `Restart=` navbatga qo'yadigan narsa.
   Ya'ni **PSI-gated restart admission control shipped software'da mavjud**, 5 yildan
   beri. Bu adabiyot emas, lekin `03-research-gap.md` §G1 dagi "hech bir tizim …
   ishlatmaydi" degan shakl **noto'g'ri**.
2. **TMO (ASPLOS '22, peer-reviewed).** PSI Senpai kontrolleri orqali **proaktiv memory
   offloading**ni boshqaradi — bu OOM kill ham, eviction ham emas, balki graduallashgan
   control action. Demak "PSI faqat OOM/eviction trigger" **yolg'on**.
3. **"False recovery" kontseptsiyasi da'vo qilingan.** Dai va boshq. (arXiv 2607.20005,
   2026-07) **false remediation rate (FRR)** ni formal CMDP cheklovi sifatida
   ta'riflaydi. Qi va boshq. (arXiv 2607.04623) "recovery-validity metrics" beradi.
   Va **recovery benchmark** ham mavjud: Brown & Patterson (USENIX ATC 2000) fault
   injection bilan availability benchmarking'ni **Linux'da** qilgan; Nogueira & Coelho
   (*Computers* 15(7):439, 2026-07) reproducible, bitta node'li, supervisor-restart
   recovery benchmark'ini chop etgan.

### Omon qolgan da'vo — kalibrlangan shakl

2026-09-29 da arXiv, Crossref, USENIX, Linux kernel git, systemd va Kubernetes
tracker'lari ustida yuqorida sanab o'tilgan so'rovlar bilan bajarilgan tizimli qidiruv
quyidagilarni **topmadi**:

> **N1.** **Tizim pressure'i xizmat restart'ining muvaffaqiyat ehtimoliga ta'sir qiladimi**
> degan savolni **o'lchagan** hech qanday ish — peer-reviewed ham, preprint ham.
> PSI ni actuator gate sifatida ishlatgan ishlar bor (TMO, 2608.13689), lekin ularning
> actuator'i **reclaim/offload**, restart emas.
>
> **N2.** `ConditionMemoryPressure=` ni (yoki umuman PSI-gated restart admission'ni)
> baseline'ga qarshi **baholagan** hech qanday ish. Mexanizm 5 yil shipped, va
> **o'lchanmagan.**
>
> **N3.** **OS-darajasidagi service manager'lar** (systemd, supervisord, monit, Pacemaker)
> uchun **bitta Linux node'da**, recovery **to'g'riligini** (latency emas) o'lchaydigan
> reproducible recovery benchmark.
>
> **N4.** Recovery muvaffaqiyatini **aktorning o'z muvaffaqiyat signali** bilan mustaqil
> verification natijasining **konjunksiyasi** sifatida — yorliqlash yoki oracle
> bosqichisiz — ta'riflaydigan metrika. (FRR va R2Act hodisani o'lchaydi, lekin
> yorliqlangan natijalar orqali.)

### Nima bu da'voni rad etadi (falsifikatsiya shartlari)

Halol manfiy da'vo o'zini qanday buzishni aytishi kerak. `N1`–`N4` quyidagilar bilan
rad etiladi:

- **`N1`/`N2`:** PSI (yoki boshqa pressure metrikasi) bilan restart/recovery muvaffaqiyati
  orasidagi bog'liqlikni o'lchagan **har qanday** ish — shu jumladan sanoat blog posti,
  SREcon/LISA ma'ruzasi, kernel/systemd mailing list thread'i, yoki abstraktda PSI ni
  eslatmagan lekin metodida ishlatgan maqola. **LKML va Semantic Scholar qidirilmagani
  uchun bu eng ehtimolli topilish joyi.**
- **`N3`:** systemd/supervisord/monit/Pacemaker uchun fault injection + recovery
  to'g'riligi metrikasi bilan e'lon qilingan benchmark. Nogueira & Coelho'ning actor
  runtime benchmark'i OS service manager'ga **ko'chirilsa**, `N3` yo'qoladi.
- **`N4`:** oracle'siz recovery-muvaffaqiyat metrikasi — FRR yoki "Verification Escape
  Rate" ning yorliqsiz varianti.

### Yozish qoidalari — majburiy

1. **"Birinchi marta", "hech kim qilmagan", "hech qachon" IBORALARI TAQIQLANADI.**
   Ruxsat etilgan shakl: *"a systematic search over arXiv, Crossref, USENIX, the Linux
   kernel git history and the systemd/Kubernetes issue trackers on 2026-09-29, using the
   queries listed in §Tizimli qidiruv, found no work that …"* — va **darhol keyin**
   qidiruvning chegaralari (§"Qidiruvning ochiq zaifliklari") keltiriladi.
2. **`ConditionMemoryPressure=` baseline arm sifatida kiritiladi**, aks holda maqola
   mavjud shipped mexanizmni bilmagandek ko'rinadi. Bu `RestartSteps=` bilan bo'lgan
   vaziyatning takrori.
3. **FRR, R2Act, Brown & Patterson, Nogueira & Coelho va Bindschaedler
   Introduction'da sitat qilinadi**, Related Work'ning oxirida emas. Reviewer bularni
   topadi; biz birinchi topishimiz kerak.
4. `FR-A` ning da'vosi **faqat "oracle-free + aktorga agnostik"** deb yoziladi, "yangi
   hodisa" deb emas.

> **Holat: `preliminary` EMAS, balki `documented systematic search, with stated gaps`.**
> Da'vo endi 2026-09-29 dagi hujjatlashtirilgan qidiruvga tayanadi. Uning chegaralari
> aniq: **LKML, DBLP, Semantic Scholar, Google Scholar va ACM/IEEE ning o'z qidiruv
> interfeyslari qamrab olinmagan, va arXiv qidiruvi to'liq matnni indekslamaydi.**
> Bu chegaralar maqolada aytilishi shart.

---

## Boshqa hujjatlarga ta'sir — MUVOFIQLASHTIRISH KERAK

Bu sessiya faqat shu faylni o'zgartirdi. Quyidagi qarama-qarshiliklar **boshqa
hujjatlarda** qoldi va markazlashgan tarzda hal qilinishi kerak:

| Hujjat | Qarama-qarshi da'vo | Topilma |
|---|---|---|
| `03-research-gap.md` §G1 | "Hech bir tizim — systemd, Pacemaker, Kubernetes, monit, oomd — pressure'ni restart qilish/qilmaslik qarorining kiritmasi sifatida ishlatmaydi" | **Rad etildi.** systemd `ConditionMemoryPressure=` (v250) aynan shuni qiladi |
| `03-research-gap.md` §G1 | "systemd pressure'ni unit'ga **eksport qiladi** (`MemoryPressureWatch=`), qaror qilmaydi" | **Rad etildi.** `ConditionMemoryPressure=` gating qarori qabul qiladi |
| `03-research-gap.md` §G3 | "ROC (Patterson va boshq., 2002) aynan recovery benchmark'larni talab qilgan. **24 yil o'tib, bu qatlamda hali yo'q.**" | Qismli. ROC *availability/maintainability* benchmark'larini talab qilgan va Brown & Patterson (2000) ni sitat qilgan; oxirgisi Linux'da bajarilgan |
| `04-novelty-statement.md` | "PSI recovery qarorida ishlatilmagan — **PRELIMINARY**" | **Rad etildi** (systemd v250, TMO) |
| `04-novelty-statement.md` C2 | "**Hech biri** 'aktor muvaffaqiyat deb e'lon qildi, lekin aslida emas edi' ni metrika sifatida bermaydi" | **Juda kuchli.** FRR va R2Act hodisani o'lchaydi; `FR-A` ning farqi faqat *oracle-free* + *aktorga agnostik* |
| `04-novelty-statement.md` C3 | "Narya'ning harness'i yopiq" (ochiq artifact hissa sifatida) | To'g'ri, lekin Nogueira & Coelho ochiq reproducible recovery benchmark chop etgan |
| `PREREGISTRATION.md` | pilot arm'lari (A: fiksa, B: `RestartSteps=`, C: REVIX) | **D arm qo'shilishi kerak:** `ConditionMemoryPressure=` |

---

## Verifikatsiya jurnali

Barcha tekshiruvlar **2026-09-29** sanasida bajarilgan.

| # | Manba | Daraja | Ochilgan URL / usul |
|---|---|---|---|
| 1 | Narya, OSDI '20 | T1 → **T1** (chuqurlashtirildi: to'liq PDF o'qildi, Table 2 action space) | `https://www.usenix.org/conference/osdi20/presentation/levy` + `https://www.usenix.org/system/files/osdi20-levy.pdf` |
| 2 | Sanabria va boshq., SEAMS '24 | **T2 → T1** | `https://arxiv.org/abs/2401.12405` (arXiv API) + Crossref `10.1145/3643915.3644097` |
| 3 | Kephart & Chess, IEEE Computer 2003 | **T2 → T1** | Crossref `10.1109/MC.2003.1160055` |
| 4 | ROC, UCB//CSD-02-1175 | **T2 → T1** (+ da'vo aniqlashtirildi) | `http://roc.cs.berkeley.edu/papers/ROC_TR02-1175.pdf` (birlamchi PDF) |
| 5 | Microreboot, OSDI '04 | **T2 → T1** | `https://www.usenix.org/legacy/event/osdi04/tech/candea.html` |
| 6 | Recursive Restartability, HotOS-VIII | **T2 → T1** | `http://roc.cs.berkeley.edu/papers/recursive_restartability.pdf` |
| 7 | Crash-Only Software, HotOS-IX | **T2 → T1** | `https://dslab.epfl.ch/pubs/crashonly.pdf` |
| 8 | Psaier & Dustdar, Computing 91(1) | **T2 → T1** | Crossref `10.1007/s00607-010-0107-y` |
| 9 | Ghosh va boshq., DSS 42(4) | **T2 → T1** | Crossref `10.1016/j.dss.2006.06.011` |
| 10 | Gandalf, NSDI '20 | **T2 → T1** (+ **izoh tuzatildi**) | `https://www.usenix.org/conference/nsdi20/presentation/li` |
| 11 | Aribe Jr & Oracion, IJ-ICT 15(2) | **T2 → T1** | Crossref `10.11591/ijict.v15i2.pp729-740` + arXiv API `2605.19261` |
| 12 | DeepLog, CCS '17 | **T2 → T1** (+ sarlavha to'ldirildi) | Crossref `10.1145/3133956.3134015` + S2 `DOI:10.1145/3133956.3134015` |
| 13 | Borg, EuroSys '15 | **T2 → T1** | Crossref `10.1145/2741948.2741964` |
| 14 | PSI kernel commit `eb414681d5a0` | **T2 → T1** | GitHub API `repos/torvalds/linux/commits/eb414681d5a0`; `contents/kernel/sched/psi.c?ref=v4.19` (404) va `?ref=v4.20` (topildi); `Documentation/accounting/psi.txt?ref=v4.20` |
| 15 | Kubernetes KEP #5734 | **T2 → T1** | GitHub API `repos/kubernetes/enhancements/issues/5734` |
| 16 | `advaithsarva/self-healing-system-agent` | **T2 → T1** (mavjudlik; da'volar audit qilinmagan) | GitHub API `repos/advaithsarva/self-healing-system-agent` |
| 17 | `prethivganeshm2023-del/adaptive-self-healing-runtime` | T1 → **T1** (metadata to'ldirildi: 0 star, litsenziya yo'q, 2026-09) | GitHub API |
| 18 | JAGR, Autonomic Computing Workshop 2003 | **T3 → T1** | Crossref `10.1109/ACW.2003.1210217` |
| 19 | Nooks → "Improving the Reliability of Commodity Operating Systems", TOCS 23(1) | **T3 → T1** (+ **sarlavha tuzatildi**) | Crossref `10.1145/1047915.1047919` |
| 20 | CRRL, arXiv 2607.03177 | **T3 → T1** (+ **sarlavha tuzatildi**) | arXiv API `2607.03177` |
| 21 | Adaptive Fault Injection Planning, arXiv 2607.16161 | **T3 → T1** | arXiv API `2607.16161` |
| 22 | Self-Healing Software Systems, arXiv 2504.20093 | **T3 → T1** (peer-reviewed emas deb belgilandi) | arXiv API `2504.20093` |
| 23 | Restart-Based Fault-Tolerance → **RTCSA 2017** | **T3 → T1** (+ **sarlavha va venue topildi**) | arXiv API `1705.02412` + Crossref `10.1109/RTCSA.2017.8046320` |
| 24 | Full system restarts, ICCPS 2017 | **T3 → T1** | Crossref `10.1145/3055004.3055012` |
| 25 | **systemd `Condition{Memory,CPU,IO}Pressure=`** | **yangi → T1** | mahalliy `man systemd.unit` (systemd 261 (261.2-1)) |
| 26 | TMO, ASPLOS '22 + CACM 2025 | **yangi → T1** | Crossref `10.1145/3503222.3507731`, `10.1145/3746651` |
| 27 | Brown & Patterson, USENIX ATC 2000 | **yangi → T1** | `https://www.usenix.org/legacy/event/usenix2000/general/full_papers/brown/brown_html/` |
| 28 | Bindschaedler, Rebooting Microreboot, ARCS 2026 | **yangi → T1** | arXiv API `2604.09963` (journal-ref ARCS 2026) |
| 29 | Dai va boshq., FRR, arXiv 2607.20005 | **yangi → T1** | arXiv API + to'liq PDF (`arxiv.org/pdf/2607.20005v1`), FRR ta'rifi o'qildi |
| 30 | Qi va boshq., R2Act, arXiv 2607.04623 | **yangi → T1** | arXiv API `2607.04623` |
| 31 | Nogueira & Coelho, Computers 15(7):439 | **yangi → T1** | Crossref `10.3390/computers15070439` |
| 32 | Dhakal & Sigdel, arXiv 2608.13689 | **yangi → T1** | arXiv API + to'liq PDF (`arxiv.org/pdf/2608.13689v1`) |
| 33 | Li va boshq., SchedBlame, arXiv 2609.02052 | **yangi → T1** | arXiv API `2609.02052` |
| 34 | systemd issue #13922 | **yangi → T1** | GitHub API `repos/systemd/systemd/issues/13922` |
| 35 | systemd #20139 / PR #21437 | **yangi → T2** | subagent skani; **men ochmadim** |
| 36 | Cloud/microservice benchmark oilasi (6 manba) | **yangi → T2** | subagent skani; **men ochmadim** |
| 37 | `Apexyunhnao/self-healing-agent` | **yangi → T2** | subagent skani; **men ochmadim** |
| 38 | FaultSee, EDCC 2020 | **yangi → T2** | Crossref qidiruv natijasida ko'rindi; sahifasi ochilmadi |
| 39 | SDN RL, Discover Networks 2:14 | **yangi → T3** | Springer auth orqasida; muallif ro'yxati tasdiqlanmagan |
| 40 | PandaStack blog, SD Times | **yangi → T3** | peer-reviewed emas; ochilmadi |

### Ko'tarilMAGAN manbalar va nima uchun

| Manba | Nima uchun qoldi |
|---|---|
| Pacemaker / Kubernetes / monit / supervisord / greenboot ro'yxati | mexanizm ro'yxati, bibliografik manba emas; `01-texnologiya-auditi.md` ga tegishli |
| `CONFIG_FAULT_INJECTION`, `tc netem`, `dm-flakey`, `dm-delay` | metodologiya hujjatiga tegishli; bu sessiyada tekshirilmadi |
| DBench oilasi, Kanoun & Spainhower | `C3` uchun muhim, lekin bu sessiyada vaqt yetmadi — **keyingi sessiyada birinchi navbatda** |
| Netflix chaos vositalari | bu skanda ham tekshirilmadi |
| ClosRCA-Bench (Authorea preprint) | Crossref'da ko'rindi, lekin Authorea preprint'i; ochilmadi |
| snippet-darajasidagi 18 arXiv ID (T3 ro'yxati) | subagent skani; men hech birini ochmadim — **ko'tarilishi uchun har biri alohida ochilishi kerak** |
