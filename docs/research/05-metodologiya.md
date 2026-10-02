# 05 — Eksperimental metodologiya

> **Bu hujjat qisqa.** Barcha operatsion ta'riflar, statistik testlar, falsifikatsiya
> mezonlari va confound nazorati **[`PREREGISTRATION.md`](../../PREREGISTRATION.md)** da
> muzlatilgan. Ikki joyda takrorlash — ular bir-biridan uzoqlashishiga olib keladi,
> va o'sha paytda qaysi biri haqiqiy ekani noaniq bo'ladi.
>
> Bu fayl **yo'l xaritasi va asoslash**ni beradi; pre-registration **shartnomani**.

---

## 1. Eksperiment darajalari

| Daraja | Nima | Pre-registration | Holat |
|---|---|---|---|
| **P1 — pilot** | H1 ni bitta toza yacheykada sinash: `clean_crash × ekzogen pressure` | `preregistration/v1.4` ✅ | rejalashtirilgan |
| **CAL — kalibratsiya** | har `(fault × action)` uchun `P̂(VR)` → `Repairs()` matritsasi | kerak | P1 dan keyin |
| **P2 — confirmatory** | to'liq fault taksonomiyasi × arm A/B/C × pressure × pulse duration | kerak, P1 effect size'idan `n` hisoblanadi | CAL dan keyin |

**P1 ma'lumotlari P2 analiziga qo'shilmaydi** — bir xil ma'lumotda hipotezani generatsiya
qilib, keyin sinash — garden of forking paths.

---

## 2. Arm'lar va baseline mantiqi

| Arm | Konfiguratsiya | Roli |
|---|---|---|
| **A** | `Restart=on-failure`, `RestartSec=100ms` | systemd default'ga yaqin |
| **B** | `Restart=on-failure`, `RestartSec=10s`, `RestartSteps=4`, `RestartMaxDelaySec=160s` | **systemd NATIVE backoff — kuchli baseline** |
| **C** | PSI-gated admission control + post-restart verification | REVIX |
| **no_action** | `Restart=no` | **majburiy nazorat** (§4) |

> **B nima uchun kritik:** agar REVIX faqat A ga qarshi o'lchansa, natija ma'nosiz —
> chunki B systemd'da bir qator konfiguratsiya bilan mavjud. Reviewer darhol so'raydi:
> *"`RestartSteps=4` qo'ysangiz nima bo'ladi?"* Javob o'lchangan bo'lishi kerak.

**Barcha arm'larda `StartLimitBurst=0`.** Aks holda A ning raqamlari systemd rate
limiter'i bilan belgilanadi va taqqoslash backoff haqida emas, `StartLimit` haqida
bo'lib qoladi. Give-up mantiqi harness'da, hamma uchun bitta qoida.

---

## 3. Nega `clean_crash × ekzogen pressure` — P1 ning asosiy yacheykasi

H1 ni o'ldiradigan e'tiroz:

> *"`P(VR | high PSI)` past, chunki pressure sababi — restart'i baribir muvaffaqiyatsiz
> bo'ladigan memory leak'ning o'zi."*

Pressure va fault class **konstruksiya bo'yicha** confound. Yechim:

1. H1 **fault class ichida** sinaladi (pooled analiz ta'rifan confounded)
2. Pressure **ekzogen** — SUT'ning fault'iga aloqasi yo'q generatordan, fault class'dan
   **mustaqil** randomizatsiya qilingan

`clean_crash` ideal, chunki:
- tinch holatda `P(VR) ≈ 1.0` → pasayish uchun joy bor (ceiling effect yo'q)
- restart uni **ishonchli** tuzatadi → "restart noto'g'ri action" confound'i yo'q
- **o'zi pressure yaratmaydi** → pressure butunlay ekzogen

→ Pressure'ni o'zgartirish **pressure'ning sababiy ta'sirini izolyatsiya qiladi.**
Manipulyatsiyasiz natija faqat korrelyatsion bo'lar edi va reviewer haqli ravishda
uni chegirib tashlar edi.

---

## 4. Nazorat arm'lari — nima uchun ikkita

| Nazorat | Nimani ajratadi |
|---|---|
| `no_action` (injeksiya + `Restart=no`) | fault'ning o'zi PSI ni qancha oshirdi |
| injeksiya yo'q, pressure bor | pressure'ning o'zi baseline |
| restart-cost microbenchmark (fault yo'q, `systemctl restart` × n) | **action**ning PSI narxi, pressure funksiyasi sifatida |

Busiz `harm_indicator` (FR-B) talqin qilinmaydi va "restart PSI ni oshirdi" ni
"fault PSI ni oshirdi" dan ajratib bo'lmaydi.

Action'ning PSI hissasi — mos keladigan pressure'da **difference-in-differences**.

---

## 5. Fault taksonomiyasi (P2 uchun; P1 da faqat #1)

Uch o'q: **locus** (in-service / cgroup / host / dependency / config),
**manifestation** (fail-stop / fail-slow / fail-silent),
**repair-relevant class** (`Repairs()` nimaga kalitlangan).

| # | class | mexanizm | restart tuzatadimi | izoh |
|---|---|---|---|---|
| 1 | `clean_crash` | probe → `exit(1)`, `SIGKILL`, `SIGSEGV` | ✅ ~1.0 | **P1 yacheykasi** |
| 2a | `hang_deadlock` | teskari tartibda ikki lock | ✅ | detection masalasi |
| 2b | `hang_livelock` | lock ushlab tor spin | ✅ | |
| 2c | `hang_blocked_io` | hech kim yozmaydigan FIFO'dan blocking read | ✅ | |
| 3a | `leak_oom_noswap` | `MemoryMax=256M`, `MemorySwapMax=0`, λ tezlikda leak | ✅, keyin M/λ da qayta ishdan chiqadi | **kanonik FR-A generatori** |
| 3b | `leak_oom_swap` | xuddi shunday, swap ruxsat | qisqa vaqt | kam deterministik |
| 4 | `host_mem_pressure` | slice'dagi alohida generator, `MemoryHigh=H` → reclaim, kill'siz | ❌ | **H2 ni ko'taradi** |
| 5 | `cpu_starvation` | hog thread'lar + `CPUWeight` skew + `CPUQuota`; `sched_setaffinity` bilan pin | ❌ | `cpuset` delegated emas |
| 6 | `io_stall` | **root/guest**: `dm-delay`, `dm-flakey` | ❌ | `io` delegated emas |
| 7 | `dep_unavailable` | ikkinchi unit unix socket orqali; dep handler'ida latency | ❌ | **kanonik FR-B klassi**; in-process latency aniq takrorlanadi, root/netem kerak emas |
| 8 | `misconfiguration` | config fayli sintaktik/semantik/valid-lekin-noto'g'ri | ❌ hech qachon | fayl **o'zi** fault → mukammal deterministik |
| 9 | `slow_start` | `READY=1` ni `d` ms kechiktirish, `TimeoutStartSec=T` ga qarshi | ❌ | `d` ni `T` atrofida sweep |

### Uchta muhim eslatma

**(a) Class 2 (hang) — detection haqida, action haqida emas.**
`Restart=on-failure` + watchdog yo'q → systemd hang'ni **umuman** ko'rmaydi. "C hang'ni
ko'radi, B ko'rmaydi" — bu systemd **konfiguratsiyasi** haqidagi bayonot, va reviewer'ning
bir qatorli javobi: *"`WatchdogSec=` qo'ying."*
→ **Baseline'larga C ning detection budjetiga moslangan `WatchdogSec` beriladi**, shunda
taqqoslash detection'dan **keyin** nima qilish haqida bo'ladi — ya'ni haqiqiy savol.

**(b) Class 8 (misconfiguration) pressure yaratmaydi**, demak PSI gate yordam bermaydi.
C bu yerda B dan ustun kelmaydi, va B (backoff qiladi) yaxshi ko'rinadi.
→ **Per-fault-class analiz birlamchi, agregat faqat deskriptiv.** Agregat "C yaxshiroq"
class aralashmasi bilan belgilanadi, va reviewer birinchi so'raydigan narsa — breakdown.

**(c) Class 9 × class 4 — REVIX'ga bog'liq bo'lmagan ehtimoliy natija.**
`TimeoutStartSec` fiksa, pressure start'ni sekinlashtiradi → pressure sog'lom xizmatni
start-timeout failure'iga aylantiradi. H1 mexanizmi uchun toza hikoya, engine kerak emas.

### Injeksiyani kollateral zarardan ajratish
1. **Ikki tomonli bracket** — harness before/after + SUT'ning ichki "armed/fired" record'i
2. **Terminal sabab systemd'dan O'QILADI**, taxmin qilinmaydi: `Result`, `ExecMainCode`,
   `ExecMainStatus`, `memory.events.oom_kill` delta'lari. Biz yubormagan `SIGKILL` yoki
   biz cheklamagan cgroup'dagi `oom_kill` → trial `contaminated`, **va eksklyuziya
   darajasi natija sifatida beriladi**
3. **Bystander xizmat** — bir xil slice, bir xil yuk, hech qachon fault qilinmaydi.
   Buzilsa — trial'da spillover bor. Bu kollateral zararni *nazorat qilish* va
   *nazorat qildim deb aytish* orasidagi farq
4. **Host guard** — host PSI, oomd journal kill'lari, `/proc/vmstat oom_kill`, har trial
   atrofida failed system unit to'plami

---

## 6. Nima o'lchanadi — qisqa ro'yxat

Har trial uchun: VR (throughput bandi bilan), `D_probe`, `D_eff`, `D_sd`,
`time_to_first_up`, restart soni, **4 scope**da erishilgan pressure kovariatalari
(Δ ∈ {0.5,1,2,5,10} s pre-fault va post-action), `Result`/`ExecMainStatus`,
`oom_kill` delta'lari, bystander contract trace'i, guard trace'i, per-CPU chastota +
termallar, host `MemAvailable`, blok indeksi, RNG seed, disposition.

To'liq schema: `PREREGISTRATION.md` **§14** va `revix/schema.py`.

> **Havola tuzatildi (2026-10-02).** Bu qator ilgari "§7–8" ga ko'rsatardi;
> §7 — *Pressure o'lchovi*, §8 — *Confound nazorati*. Data schema **§14** da,
> va u aynan shunday noto'g'ri havolani tuzatish uchun **v1.2 amendment**
> bilan qo'shilgan. Bu fayl non-normativ, shuning uchun bu tuzatish
> amendment emas — **hujjat tuzatishi**.

---

## 7. Reproducibility

- **Pre-registration hash** har `run_meta` ga kiradi
- **`git_dirty` flag** — confirmatory run uchun `false` bo'lishi shart
- Har unit'ning barcha property'lari **`systemctl show` dan** olinadi, source fayldan emas
  → **haqiqatan ishlagani** yoziladi
- `boot_id` — monotonic taqqoslanuvchanligini tekshirib bo'ladigan qiladi
- RNG seed log'lanadi → randomizatsiya qayta tiklanadi
- **Validator analizdan oldin o'tishi shart**; o'tmagan run analiz qilinmaydi
- `datasets/` append-only; raw hech qachon ustiga yozilmaydi; derived record'lar alohida
  fayllarda va raw'dan qayta yaratiladi
