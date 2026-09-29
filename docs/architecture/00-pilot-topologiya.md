# 00 — Pilot topologiyasi va xavfsizlik chegarasi

## 1. cgroup topologiyasi

```
user@1000.service                    [oomd: ManagedOOMMemoryPressure=kill, 50%, 20s]
│
├── revix.slice                       MemoryMax=2G        <- kernel darajasidagi shift
│   │                                 MemoryHigh=<dial>   <- PI controller nishoni
│   │                                 CPUQuota=400%       <- 1200% dan; desktop uchun >=8 yadro
│   │                                 TasksMax=256
│   │
│   ├── revix-sut.service             MemoryMax=256M
│   │                                 MemorySwapMax=0
│   │                                 TasksMax=64
│   │                                 Type=notify, WatchdogSec=
│   │                                 StartLimitBurst=0   <- barcha arm'larda
│   │
│   ├── revix-bystander.service       MemoryMax=128M
│   │                                 (hech qachon fault qilinmaydi -> spillover detektori)
│   │
│   └── revix-press.service           MemoryMax=1.5G
│                                     MemorySwapMax=0
│                                     RuntimeMaxSec=      <- trial'dan uzoq yashamaydi
│
└── revix-harness.slice               driver, prober, psi_sampler, guard
                                      ^^^^^^^ SIBLING — kovariata sifatida ishlatiladigan
                                      hech bir scope ichida EMAS
```

### Nega harness sibling slice'da
Restart CPU/xotira/IO iste'mol qiladi → PSI ni **oshiradi**. Agar harness o'lchanayotgan
slice ichida bo'lsa, uning resurs sarfi kovariata sifatida ishlatiladigan PSI ga kiradi →
feedback loop va artefakt.

Harness'ning o'z `CPUUsageNSec` / `MemoryPeak` log'lanadi va hisobotda beriladi.
Prober CPU'si yadro foizida o'lchanadi; >1% bo'lsa sekinlashtiriladi.
**Probe narxi arm'lar bo'yicha bir xil ushlanadi** — aks holda arm'lar instrumentatsiya
yuki bo'yicha farq qiladi.

---

## 2. Cheklash mexanizmlari

| Mexanizm | Nimani to'xtatadi |
|---|---|
| slice `MemoryMax=2G` | kernel darajasidagi umumiy anonim xotira shifti |
| `MemorySwapMax=0` (generator + SUT) | 5.5 GiB swap to'lib host-wide IO va SSD wear yaratishi |
| `TasksMax` | fork bomb |
| `CPUQuota=400%` | desktop CPU starvation (12 yadrodan ≥8 erkin) |
| hog `sched_setaffinity` | CPU fault'lari SUT bilan bir xil yadro to'plamida qoladi (`cpuset` delegated emas) |
| **`cgroup.kill`** | bitta yozish → atomik subtree teardown (unprivileged ✅) |
| `RuntimeMaxSec` (generator) | generator trial'dan uzoq yashamasligi |
| pre-flight tekshiruv | `revix-*` unit yoki `revix.slice` allaqachon bor bo'lsa **ishga tushmaydi** |
| `--collect` transient unit'lar | qoldiq failed unit'lar |

---

## 3. ⚠️ Nima hali ham host'ga o'tishi mumkin

### 3.1 systemd-oomd foydalanuvchi ilovalarini o'ldirishi — 1-RAQAMLI XAVF

Bu **tekshirilgan**, gipoteza emas:

```
/usr/lib/systemd/system/user@.service.d/10-oomd-user-service-defaults.conf
    ManagedOOMMemoryPressure=kill
    ManagedOOMMemoryPressureLimit=50%
oomd.conf:  DefaultMemoryPressureDurationSec=20s
```

PSI ierarxik → `revix.slice` stall'i `user@1000.service` ga tarqaladi. 20 s davomida
chegaradan oshsa, oomd **avlod cgroup'ni** o'ldiradi (o'z evristikasi bo'yicha: eng
yuqori pressure/reclaim). Nishon bo'lishi mumkin: brauzer, editor, IDE, GNOME sessiyasi,
**yoki ishlab chiqish vositangiz.**

**Yumshatishlar, ustuvorlik tartibida:**

| | Yechim | Holat |
|---|---|---|
| **(a)** | **Har pressure epizodi ≤12 s** (<20 s) + ≥20 s quiescence → oomd ning sustained sharti **bajarilmaydi**, chunki o'rtacha 20 s uzluksiz oshish yig'ilishidan oldin pasayadi | ✅ **birlamchi, privilegiyasiz** |
| **(b)** | **Mustaqil guard process**: `user@1000.service/memory.pressure` ni 10 Hz (`total`) va 1 Hz (`avg10`) kuzatadi; `full avg10 > 15%` yoki 2 s stall tezligi chegaradan oshsa → `revix.slice/cgroup.kill` ga `1` yozadi, trial `aborted_guard`. **Driver'dan ALOHIDA process** — qotib qolgan driver guard'ni o'chira olmasligi kerak. Birinchi start, oxirgi stop, o'z `OOMScoreAdjust` i bilan | ✅ **majburiy** |
| **(c)** | Foydalanuvchining mavjud app scope'lariga `ManagedOOMPreference=avoid/omit` qo'yish | ❌ **qilinmaydi** — jonli muhitni o'zgartiradi va mavjud scope'larda ishonchli qo'yilmaydi |
| **(d)** | Harness'ni **system slice**ga ko'chirish (`/etc/systemd/system/revix.slice`, `ManagedOOMMemoryPressure=auto`, `-.slice` ostida) → oomd kill scope'idan **butunlay chiqadi** | 🟡 **sudo mumkin bo'lganda uzoq muddatli to'g'ri uy** |
| **(e)** | `systemd-oomd` ni to'xtatish | ❌ **qilinmaydi** — haqiqiy mashina himoyasini o'chiradi, (d) dan yomonroq |

> **(a) ILMIY CHEKLOV yaratadi:** sustained pressure eksperimentlari VM/root-only bo'ladi.
> Bu `PREREGISTRATION.md` §4 da `W_stab_pilot = 8 s` sifatida ochiq yozilgan.

### 3.2 Kernel global OOM killer
Faqat eksperiment shifti + host sarfi jismoniy xotiradan oshsa yetiladi.
15.4 GiB umumiy, ~7.6 GiB available, 2 GiB shift → zaxira yetarli.
Guard qo'shimcha `/proc/vmstat oom_kill` va host `MemAvailable` ni kuzatadi.

### 3.3 Swap thrash / SSD wear
`MemorySwapMax=0` bilan oldini olinadi.
Slice'da nolga teng bo'lmagan `memory.swap.current` — **konfiguratsiya xatosi ⇒ abort.**

### 3.4 journald flooding
Default `RateLimitIntervalSec=30s`, `RateLimitBurst=10000`. 10 Hz prober journald'ga
yozsa, rate-limit'ga tushib **jimgina yo'qoladi**.
→ **Harness o'z fayllariga yozadi; hech qanday o'lchov ma'lumoti journald'dan o'tmaydi.**
journald faqat systemd'ning o'z hodisalarini cross-check qilish uchun.

### 3.5 Hech narsa bilan cheklanmaydi
PSI ning 2 s yangilanish granularligi; DVFS/termal ta'siri.
**Bular validlik masalasi, xavfsizlik emas** — `PREREGISTRATION.md` §7, §8.5.

---

## 4. Privilegiya yuzasi

### Privilegiyasiz ishlaydi (tekshirilgan)
`cpu`, `memory`, `pids` delegated (`DelegateControllers=cpu memory pids`), demak:
- transient user unit'lar `MemoryMax=`, `MemoryHigh=`, `MemorySwapMax=`, `CPUQuota=`,
  `TasksMax=`, `Restart*`, `WatchdogSec=`, `TimeoutStartSec=` qabul qiladi
- delegated subtree'da `memory.max`, `memory.high`, `memory.swap.max`, `cgroup.kill`,
  `memory.reclaim` **yozilishi mumkin**
- per-cgroup PSI **o'qiladi**, `io.pressure` ham (io controller o'chiq bo'lsa ham)

### Root kerak (P1 da ishlatilMAYDI)
`io` controller / `io.max`; `dm-delay`/`dm-flakey`; `tc netem`; cgroup `cpuset` pinning;
`scaling_governor=performance`; `drop_caches`; paket o'rnatish; harness'ni system slice'ga
ko'chirish.

> `sudo -n` parol so'raydi → **hech bir privilegiyali qadam nazorsiz ishlamaydi.**
> Demak kechalik kampaniya **to'liq privilegiyasiz** yoki **to'liq guest ichida** bo'lishi kerak.

**Prinsip:** barcha privilegiyali operatsiyalar **bitta** qisqa, ko'rib chiqiladigan setup
skriptida, sessiyaga bir marta ishlaydi va **har trial'da hech narsa qilmaydi** →
**o'lchov davomida hech qanday root process tirik emas.**

---

## 5. Trial jadvali

```
pre-flight tekshiruv
   |
   v
R_ref baseline (fault yo'q, pressure yo'q)          10 s
   |
   v
pressure ramp (PI controller nishonga chiqadi)       5 s
   |
   v
hold  ----[ injeksiya, hold'ga 3 s kirgach ]----    <= 12 s   <-- oomd xavfsiz oyna
   |          |
   |          +-- detection -> action -> W_stab_pilot = 8 s verification
   v
pressure off
   |
   v
washout:  cgroup.kill -> memory.current baseline -> stall tezligi quiescence T_q=5s
          qattiq pol T_w = 15 s,  cap 120 s -> washout_timeout
   |
   v                                                   ~75 s / trial
keyingi trial (blok ichida randomizatsiya)             120 trial ~ 2.5 soat
```

---

## 6. Qurilish tartibi — guard birinchi

```
1. PREREGISTRATION.md + docs           <- kod yo'q          [BAJARILDI]
2. sut.c, prober.py, psi_sampler.py, guard.py
3. >>> GUARD TESTI <<<  SUT'siz, injeksiyasiz, sintetik pressure manbasiga qarshi
        Guard slice'ni belgilangan vaqt ichida o'ldirishi TASDIQLANADI
        Guard to'g'riligi keyingi HAR BIR qadamni gate qiladi
4. pressure dosing kalibratsiyasi (fault yo'q)
        - <=12 s oyna ichida erishiladigan PSI bandlari
        - user@1000.service PSI oomd chegarasidan uzoq pastda qolishi
        - memory.swap.current == 0
5. muhit tekshiruvlari (transient RestartSteps=, PSI trigger oynasi)
6. smoke trial (1 trial, P0) -> validate.py o'tadi
7. pilot (120 trial)
```

**3-qadam 4-qadamdan oldin bajarilishi shart. Retrofit qilinmaydi.**
