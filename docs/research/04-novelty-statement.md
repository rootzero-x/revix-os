# 04 — Novelty Statement

## Bir jumlada

> REVIX **adaptiv recovery ixtiro qilmaydi.** U Linux service recovery'da o'lchanmagan
> narsani o'lchaydi: **restart muvaffaqiyati tizim pressure'ига qanday bog'liq**, va buni
> o'lchash uchun zarur bo'lgan **ta'riflar, metrikalar va reproducible benchmark**ni beradi.

---

## Hissa NIMA EMAS — ochiq inkor

Bu bo'lim maqolada **Introduction'da** turadi, Limitations'da emas. Reviewer buni o'zi
topishidan oldin biz aytamiz.

| Da'vo qilinMAYDI | Chunki |
|---|---|
| "Biz adaptive recovery engine ixtiro qildik" | **Narya (OSDI '20)** ko'p-signalli kontekstdan RL bilan action tanlashni production'da qilgan; Sanabria va boshq. (SEAMS '24) recovery strategiyalarini o'rgangan |
| "Biz exponential backoff qo'shdik" | **systemd v254** dan native (`RestartSteps=`, `RestartMaxDelaySec=`) — bu mashinada tasdiqlangan |
| "Biz post-restart verification ixtiro qildik" | Kubernetes probe'lari, Pacemaker OCF `monitor`, monit content testlari, greenboot. Faqat **systemd**da yo'q |
| "Biz failure-turiga qarab action tanlashni ixtiro qildik" | Pacemaker `on-fail`, Masakari per-failure workflow |
| "Biz health-gated rollback ixtiro qildik" | greenboot, systemd Automatic Boot Assessment, rpm-ostree, snapd, A/B |
| "REVIX AI-powered" | v1 — **rule-based, context-aware**. Rule ishlatgani uchun "AI" deb atash noto'g'ri (loyiha spetsifikatsiyasi §28) |
| "Bu arxitektura yangi" | `adaptive-self-healing-runtime` (GitHub) systemd+journald+psutil+`VERIFYING`+backoff'ni allaqachon qilgan |

---

## Hissa NIMA

### C1 — Falsifikatsiya qilinadigan empirik da'vo (birlamchi)

**H1:** Xizmatni restart qilishning **verified recovery** bilan tugash ehtimoli, tizim
yoki xizmat cgroup'i yuqori memory/IO pressure ostida bo'lganda sezilarli past.

```
P(VR | high PSI)  <<  P(VR | low PSI)
```

**H2:** PSI-gated restart admission control systemd'ning **native** exponential backoff'iga
nisbatan kam downtime va kam false-recovery beradi.

Nega bu hissa: **hozirgacha o'lchanmagan.** PSI 2018 yildan (Linux 4.20) mavjud, lekin
hech kim *"pressure restart muvaffaqiyatiga ta'sir qiladimi?"* degan savolni o'lchamagan.
Bu tizim haqidagi da'vo emas — **dunyo haqidagi da'vo**, va uni sinash uchun REVIX
engine'i kerak emas (pilot arm'lari shunchaki systemd config'lari).

### C2 — `FR-A`: oracle-free false-recovery metrikasi

```
FR_A = 1  ⟺  actor_success_signal == true  AND  VR == false
```

Ikki xususiyat uni yangi qiladi:
1. **Oracle kerak emas** — fault-class label, "to'g'ri action" matritsasi, hakam yo'q.
   Ikkala operand ham log'langan fakt: aktorning o'z muvaffaqiyat da'vosi, va
   contract-asosli verification natijasi.
2. **Aktorga agnostik** — systemd, REVIX yoki boshqa har qanday recovery aktori uchun
   bir xil hisoblanadi. Demak taqqoslash mumkin.

Mavjud vositalar recovery *muvaffaqiyatini* o'lchaydi (k8s probe → Ready).

> ⚠️ **2026-09-29 da yumshatildi.** Oldingi shakli ("hech biri buni metrika
> sifatida bermaydi") **juda kuchli edi**. Dai va boshq. (arXiv 2607.20005)
> **false remediation rate (FRR)** ni ta'riflaydi, R2Act (arXiv 2607.04623)
> "recovery-validity metrics" beradi. Farq shundaki, FRR **label asosida**
> ishlaydi — natijalar izolyatsiyalangan replikada qayta ishga tushirilib
> belgilanadi.
>
> **FR-A ning qolgan ustunligi tor va aniq:** u *oracle-free* (label, hakam
> yoki qayta ishga tushirish kerak emas — ikkala operand ham log'langan fakt)
> va *aktorga agnostik* (systemd, REVIX yoki boshqa aktor uchun bir xil
> hisoblanadi, demak taqqoslanadi). "Birinchi marta" DEYILMAYDI.

### C3 — Recovery benchmark, ROC an'anasida

Patterson va boshq. (2002) recovery benchmark va tizimli xato kiritishni talab qilgan.
Linux service manager qatlamida bu hali yo'q.

REVIX beradi:
- **Ta'riflar:** verified recovery (throughput bandi bilan, liveness emas), uchta ichma-ich
  downtime o'lchovi, censoring qoidalari, disposition enum'i
- **Reproducible fault taksonomiyasi** + har biri uchun deterministik injeksiya mexanizmi
- **Confound nazorati** ekzogen pressure manipulyatsiyasi bilan (korrelyatsiya emas, sababiy)
- **Ochiq artifact** — Narya'ning harness'i yopiq
- **Pre-registration** + sensitivity sweep'lar

### C4 — Portativ, privilegiyasiz o'lchov dizayni
Pressure eksperimentlarini `systemd-oomd` armed bo'lgan jonli ish stansiyasida
**hech narsani buzmasdan** o'tkazish: delegated cgroup'lar, ≤12 s pressure oynalari,
mustaqil guard, `cgroup.kill` teardown.

Kichik, lekin amaliy hissa: bu benchmark'ni **har kim o'z mashinasida root'siz**
ishga tushira olishini ta'minlaydi.

---

## Nomzod maqola sarlavhasi

Yo'nalish o'zgargani uchun boshlang'ich sarlavhalar mos emas
("Adaptive Self-Healing Mechanism…" — bu adaptiv engine'ni hissa deb ko'rsatadi).

Nomzodlar:
1. **"Does Pressure Make Restarts Fail? Measuring Verified Recovery in Linux Service Managers"**
2. **"False Recovery: An Oracle-Free Metric for Automated Service Recovery"**
3. **"A Recovery Benchmark for Linux Service Managers: Definitions, Metrics, and a Pressure Dose–Response Study"**

Yakuniy sarlavha **pilot natijasidan keyin** tanlanadi. Agar H1 null bo'lsa, (1) mos
kelmaydi, (2) va (3) hali ham to'g'ri.

---

## Da'vo kuchining halol darajalanishi

| Da'vo | Ishonch | Asos |
|---|---|---|
| `RestartSteps=` mavjud, backoff novelty emas | **FAKT** | man sahifasi, systemd 261, o'zim ko'rdim |
| Narya adaptiv action tanlashni qilgan | **FAKT** | USENIX sahifasi, o'zim ochdim |
| systemd'da post-restart health verification yo'q | **FAKT** | man sahifasi tekshirildi |
| PSI **start** qarorida ishlatilgan (`ConditionMemoryPressure=`, v250) | **FAKT** | man sahifasi, shu mashinada tekshirildi |
| PSI **restart** qarorida ishlatilmagan | **FAKT** | tajriba: `Restart=` yo'li shartni qayta baholamaydi ([06](../architecture/06-condition-pressure-tajribasi.md)) |
| H1 to'g'ri | **GIPOTEZA** | sinalmagan — pilot buni hal qiladi |
| H2 to'g'ri | **GIPOTEZA, zaifroq** | strukturaviy sabablar `03` §4 da |
| FR-A yangi metrika | **DA'VO** | mavjud vositalarda analogi topilmadi (preliminary) |
