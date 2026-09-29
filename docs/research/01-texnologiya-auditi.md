# 01 — Texnologiya auditi: Linux'da mavjud recovery mexanizmlari

**Maqsad:** REVIX nimani qayta ixtiro qilmasligi kerakligini aniqlash.
Bu hujjatdagi "✅ tasdiqlangan" belgisi — **shu mashinada o'zim tekshirganim** degani,
hujjatdan o'qiganim emas.

**Tekshirish muhiti:**
```
Kali GNU/Linux Rolling 2026.3 | kernel 7.1.5+kali-amd64 | x86_64
systemd 261 (261.2-1) | cgroup v2 (cgroup2fs) | 12 CPU | 15Gi RAM | 5.5Gi swap
```

---

## 1. systemd restart siyosati

| Direktiv | Nima qiladi | Versiya | Holat |
|---|---|---|---|
| `Restart=` | `no`/`on-success`/`on-failure`/`on-abnormal`/`on-watchdog`/`on-abort`/`always` — **exit sabab klasslarini allaqachon farqlaydi** | v201 davri | ✅ |
| `RestartSec=` | kechikish, default **100 ms** | — | ✅ |
| **`RestartSteps=`** | `RestartSec=` dan `RestartMaxDelaySec=` ga qadam-baqadam o'sish | **v254** | ✅ **man sahifasida o'zim ko'rdim** |
| **`RestartMaxDelaySec=`** | shift; default `infinity`; faqat `RestartSteps=` bilan ishlaydi | **v254** | ✅ |
| `RestartMode=` | `normal`/`direct`/`debug` | v254 | ✅ |
| `StartLimitIntervalSec=` / `StartLimitBurst=` / `StartLimitAction=` | tezlik chegarasi + eskalatsiya (`reboot*`, `soft-reboot*`, `kexec*`, `exit*`) | v229 | ✅ |
| `FailureAction=` / `SuccessAction=` | bir xil qiymat to'plami | v236 | ✅ |
| `OnFailure=` / `OnSuccess=` | boshqa unit'larni faollashtirish; `OnFailureJobMode=isolate` | v201 / v249 | ✅ |
| `WatchdogSec=` | `sd_notify(WATCHDOG=1)` heartbeat; o'tkazib yuborilsa `failed` + `SIGABRT` | — | ✅ |
| `Upholds=` | unit inactive/failed bo'lsa uzluksiz restart | v249 | ✅ |
| `ExecCondition=` | start'dan oldingi shart; exit 1–254 → unit **skip**, `failed` emas | v243 | ✅ |
| `MemoryPressureWatch=` | unit'ga `$MEMORY_PRESSURE_WATCH` eksport qiladi | v254 | ✅ |
| `CPUPressureWatch=` / `IOPressureWatch=` | mos env eksporti | v261 | (man'da bor) |

### 🔴 Eng muhim xulosa
**Exponential backoff systemd'da v254 (2023-avgust) dan boshlab native mavjud.**
Bu mashinaning `systemd.service(5)` man sahifasida aynan shu misol bor:

```
RestartSec=10s
RestartSteps=4
RestartMaxDelaySec=160s
```

→ **REVIX ning "exponential backoff" da'vosi novelty EMAS. U baseline.**

### systemd'da YO'Q narsalar (tekshirilgan)
1. **Restart'dan keyin health verification, process-liveness'dan tashqari.** Mavjud
   signal'lar: `Type=notify` `READY=1`, exit status, `WatchdogSec=` heartbeat. Kubernetes
   uslubidagi probe (exec/HTTP/gRPC/TCP) **yo'q**. Local man sahifasida `ExecMonitor=`
   yoki shunga o'xshash direktiv yo'q.
2. **Tizim holatiga qarab har xil recovery action tanlash.** Siyosat unit bo'yicha statik.
3. **Backoff'ning muvaffaqiyatli start'dan keyin reset bo'lishi** — `systemctl reset-failed`
   qo'lda kerak (subagent skanida systemd issue #43813 sifatida ko'rsatilgan, men issue'ni
   o'zim ochmadim).

---

## 2. PSI — Pressure Stall Information

✅ **Tasdiqlangan, global:**
```
/proc/pressure/cpu, /proc/pressure/io, /proc/pressure/memory
cpu: some avg10=0.00 avg60=0.00 avg300=0.00 total=31596002
     full avg10=0.00 avg60=0.00 avg300=0.00 total=0
```

✅ **Tasdiqlangan, per-cgroup:**
```
/sys/fs/cgroup/cgroup.pressure
/sys/fs/cgroup/cpu.pressure
/sys/fs/cgroup/io.pressure
/sys/fs/cgroup/memory.pressure
```

| Xususiyat | Qiymati REVIX uchun | Cheklov |
|---|---|---|
| `avgN` (10/60/300 s) | deployed gate arzon o'qiy oladi | **eksponensial silliqlangan, 2 s kadensda yangilanadi** → <2 s oldin boshlangan fault'ni ko'rmasligi mumkin |
| `total=` (µs akkumulyator) | **aniq interval stall fraction'i** → atributsiya uchun qat'iy yaxshiroq | 2 s kadensda partiyalarda kreditlanadi → 100 ms delta oniy tezlik **emas** |
| ierarxiklik | ota cgroup avlodlarning stall'ini o'z ichiga oladi | **xavf:** `revixlab.slice` stall'i `user@1000.service` ga tarqaladi (§4) |
| per-cgroup atributsiya | per-service gate qila oladigan scope | `io` controller delegated bo'lmasa ham `io.pressure` **o'qiladi** |
| poll trigger | event-driven reaksiya | **unprivileged oyna 2 s karrasi bo'lishi shart** (Linux 6.5+) → sub-2 s event-driven yo'q |

### Kim PSI ni iste'mol qiladi
- `systemd-oomd` — PSI + cgroup v2 o'qiydi, **yagona action: `SIGKILL`**
- Facebook `oomd` — xuddi shunday
- Kubernetes — PSI metrikalarini eksport qiladi
- systemd — `*PressureWatch=` orqali unit'ga **eksport qiladi**, o'zi qaror qilmaydi

### 🟢 Aniqlangan bo'shliq
**PSI hech qayerda recovery QARORIGA kirish signali sifatida ishlatilmagan** — faqat
OOM/eviction trigger sifatida. Bu REVIX ning asosiy gipotezasi (H1) turgan joy.

---

## 3. cgroup v2 va resurs nazorati

✅ **Tasdiqlangan:** `stat -fc %T /sys/fs/cgroup/` → `cgroup2fs` (faqat v2; systemd v258 da
cgroup v1 butunlay olib tashlangan).

✅ **Delegatsiya holati** — REVIX harness dizayni uchun kritik:
```
systemctl show user@1000.service -p Delegate -p DelegateControllers
  Delegate=yes
  DelegateControllers=cpu memory pids
```

| Controller | Delegated? | REVIX uchun natija |
|---|---|---|
| `memory` | ✅ | `memory.max`, `memory.high`, `memory.swap.max`, `memory.reclaim` unprivileged yoziladi |
| `cpu` | ✅ | `CPUQuota=`, `CPUWeight=` unprivileged |
| `pids` | ✅ | `TasksMax=` unprivileged |
| **`io`** | ❌ **YO'Q** | **`io.max` user cgroup'da mavjud emas → IO injection root/guest talab qiladi.** Lekin `io.pressure` **o'qish** ishlaydi |
| `cpuset` | ❌ | CPU pinning `sched_setaffinity` orqali qilinadi, cgroup orqali emas |

✅ `cgroup.kill` — bitta yozish bilan atomik subtree kill, unprivileged.
Bu washout va guard teardown uchun asosiy mexanizm.

Statik shift'lar: `CPUQuota=` (v213), `IOWeight=` (v230), `MemoryHigh=`/`MemoryMax=` (v231),
`MemorySwapMax=` (v232), `MemoryMin=`/`MemoryLow=` (v240), `TasksMax=` (v227).
**Hammasi statik — hech biri tizim holatiga qarab o'zini sozlamaydi.**

---

## 4. systemd-oomd — ✅ tasdiqlangan XAVF

```
$ cat /usr/lib/systemd/system/user@.service.d/10-oomd-user-service-defaults.conf
[Service]
ManagedOOMMemoryPressure=kill
ManagedOOMMemoryPressureLimit=50%

$ systemd-analyze cat-config systemd/oomd.conf | grep Duration
DefaultMemoryPressureDurationSec=20s

$ systemctl show user@1000.service -p ManagedOOMMemoryPressure
ManagedOOMMemoryPressure=kill
```

| Fakt | Qiymat |
|---|---|
| `user@1000.service` oomd holati | `kill` authority, 50% chegara |
| Sustained shart | **20 s** |
| `app.slice` xotira | 1.9 G |
| Claude desktop scope | 594 MB (`MemoryCurrent=594866176`) |

### Natija REVIX uchun
PSI ierarxik bo'lgani uchun `revixlab.slice` ichidagi stall `user@1000.service` ga tarqaladi.
20 s davomida 50% dan oshsa, oomd avlod cgroup'ni o'ldiradi — va `app.slice` ostidagi eng
yirik iste'molchi Claude desktop app.

→ **Ehtiyotsiz pressure eksperimenti ishlab chiqish sessiyasini o'ldiradi.**

Muzlatilgan yumshatish (`PREREGISTRATION.md` §9.4 va rejada):
1. Har pressure epizodi **≤12 s**, keyin ≥20 s quiescence
2. **Mustaqil guard process** — driver'dan alohida

systemd-oomd o'zi REVIX uchun ham **prior art**, ham **xavf**: u PSI ni o'qiydi lekin
yagona action'i `SIGKILL` — strategiya tanlash yo'q.

---

## 5. journald

✅ `systemd-journald` active. Default `RateLimitIntervalSec=30s`, `RateLimitBurst=10000`.

**Natija:** 10 Hz prober journald'ga yozsa, rate-limit'ga tushib **jimgina yo'qoladi** va
foydalanuvchi journal'ini ifloslaydi.

→ Muzlatilgan qaror: **harness o'z fayllariga yozadi; hech qanday o'lchov ma'lumoti
journald'dan o'tmaydi.** journald faqat systemd'ning o'z hodisalarini cross-check qilish uchun.

---

## 6. Mavjud vositalar — qoplanish tahlili

Quyidagilar subagent prior-art skanida topilgan; men `systemd`, `PSI`, `cgroup`, `oomd`
qismlarini mahalliy tekshirdim, tashqi tizimlarni **tekshirmadim** (URL'lar `02` da).

| Tizim | Nima qiladi | Context-aware strategiya tanlashi? |
|---|---|---|
| **Pacemaker/Corosync** | per-operation `on-fail ∈ {ignore, block, stop, demote, restart, fence, standby}`; `migration-threshold=N`; `failure-timeout`; OCF `monitor` = haqiqiy app-level verification | **Eng yaqin mavjud "adaptiv eskalatsiya."** Fault-turiga bog'liq action + hisobga asoslangan eskalatsiya + verification. **Lekin PSI/cgroup/config-change fusion'i yo'q**; siyosat deklarativ |
| **Kubernetes** | CrashLoopBackOff 10→20→40→80→160→300 s, 5 min shift, 10 min sog'lomdan keyin reset; liveness/readiness/startup probe = haqiqiy verification; node-pressure eviction | Yo'q. Fiksa eskalatsiya narvoni + probe'lar |
| **monit** | `IF <n> RESTART <n> CYCLE(S) THEN <action>`; content/protocol/checksum/resource testlari | Chegaraga asoslangan action tanlash — REVIX qaror jadvalining klassik statik analogi |
| **supervisord** | `autorestart`, `startretries`, **chiziqli** +1s backoff | Yo'q |
| **runit / s6** | restart-always 1s pol; `s6-rc` dependency tartibi | Yo'q |
| **systemd-oomd / fb oomd** | PSI + cgroup v2 → `SIGKILL`; `Senpai` proaktiv xotira o'lchamlash | Signal-driven, yagona action |
| **greenboot** (Fedora IoT, RHEL Edge) | per-boot health-check skriptlari; fail → reboot; takroriy fail → `rpm-ostree rollback` | **Health-gated rollback allaqachon mahsulot** — fiksa eskalatsiya, image granularligi |
| **systemd Automatic Boot Assessment** | sd-boot boot counting + `boot-complete.target` + `systemd-bless-boot` → eski entry'ga avtomatik qaytish | Health-gated rollback, **boot/image darajasida** |
| **snapd / ChromeOS / Android** | `check-health` hook, revision revert; A/B `update_engine`; AVB slot SUCCESSFUL belgilanmasa fallback | Image/versiya rollback, health'ga bog'langan — hal qilingan pattern |
| **OpenStack Masakari** | host/instance/process monitor → TaskFlow recovery workflow, failure turiga qarab sozlanadi | Failure-turi dispatch, operator yozgan |
| **Nagios/Sensu/EDA/Salt reactor** | "shart → playbook" quvuri | Siyosatni operator yozadi; fusion yo'q, verification loop yo'q |

---

## 7. Xulosa — REVIX nimani qayta ixtiro QILMASLIGI kerak

Bu ro'yxat novelty da'vosidan **olib tashlanadi**:

1. Exponential backoff — systemd v254 native ✅ tasdiqlangan
2. Kechiktirilgan restart — `RestartSec=`
3. Takroriy failure'da eskalatsiya — `StartLimitBurst=` + `StartLimitAction=`; Pacemaker `migration-threshold`; monit; k8s CrashLoopBackOff
4. Failure-turi → action xaritalash — Pacemaker `on-fail`; `Restart=on-abnormal|on-abort|on-watchdog`; Masakari
5. Dependency-first recovery — `Requires=`/`BindsTo=`/`After=`; `s6-rc`; Pacemaker ordering
6. Resurs mitigatsiyasi — cgroup v2 shift'lar, systemd-oomd, Senpai, kubelet eviction
7. Health-gated config/versiya rollback — greenboot, Automatic Boot Assessment, rpm-ostree, snapd, A/B
8. Izolyatsiya — `OnFailureJobMode=isolate`, Pacemaker `standby`/`fence`, k8s cordon
9. Post-recovery health verification — k8s probe, Pacemaker OCF `monitor`, monit, greenboot. **Faqat systemd'da yo'q**
10. Adaptiv, o'rganilgan, ko'p-signalli action tanlash — **Narya (OSDI '20)**, Sanabria va boshq. (SEAMS '24)

**Qolgan haqiqiy bo'shliq → `03-research-gap.md`.**
