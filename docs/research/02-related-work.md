# 02 — Related Work

## Tekshirish darajalari — MAJBURIY o'qish

Bu hujjatdagi har bir manba **tekshirish darajasi** bilan belgilangan. Bu formalizm emas:
sitat qilinган lekin mavjud bo'lmagan manba — ilmiy noxushlik, va REVIX loyiha
spetsifikatsiyasi (§40, §41) buni aniq taqiqlaydi.

| Daraja | Ma'nosi | Sitat qilish mumkinmi |
|---|---|---|
| **T1** | Men to'g'ridan-to'g'ri sahifani ochib, sarlavha/muallif/venue'ni tasdiqladim | ✅ ha |
| **T2** | Subagent skanida topilgan, URL bor, abstrakt/rasmiy sahifa ko'rilgan, lekin **men o'zim ochmadim** | ⚠️ maqola yozishdan oldin T1 ga ko'tarilishi shart |
| **T3** | Faqat eslatib o'tilgan, tasdiqlanmagan | ❌ **SITAT QILINMAYDI** |

---

## T1 — O'zim tasdiqlagan

### Narya — eng qattiq prior art

> **Predictive and Adaptive Failure Mitigation to Avert Production Cloud VM Interruptions**
> Sebastien Levy, Randolph Yao, Youjiang Wu, Yingnong Dang, Peng Huang, Zheng Mu, Pu Zhao,
> Tarun Ramani, Naga Govindaraju, Xukun Li, Qingwei Lin, Gil Lapid Shafriri, Murali Chintalapati.
> **OSDI '20** (14th USENIX Symposium on Operating Systems Design and Implementation).
> <https://www.usenix.org/conference/osdi20/presentation/levy>

Tasdiqlangan mazmuni:
- "predicts imminent host failures based on **multi-layer system signals**"
- "Narya's decision engine takes a novel **online experimentation** approach to continually
  explore the best mitigation action"; "enhances the adaptive decision capability through
  **reinforcement learning**"
- 15 oylik production deployment'da VM interruption'larni **"previous static strategy"** ga
  nisbatan o'rtacha **26%** kamaytirgan

**REVIX uchun ahamiyati:** bu aynan "ko'p-signalli kontekstdan adaptiv action tanlash,
statik siyosat o'rniga" — ya'ni REVIX ning boshlang'ich novelty da'vosi.
**Narya bu da'voni 2020 yilda bajargan.**

REVIX ni farqlash mumkin bo'lgan o'qlar (halol, lekin cheklangan):

| O'q | REVIX | Narya |
|---|---|---|
| Granularlik | bitta host'dagi **xizmatlar** | cloud fleet'dagi **host/VM** lar |
| Populyatsiya | n=1 (bitta mashina) → online A/B **mumkin emas** | katta fleet → online A/B mumkin |
| Artifact | ochiq, reproducible injection harness | yopiq |
| Hissa | **o'lchov + metrika** | tizim + production natija |

> **Bu farqlar Narya'ni "yengish" emas.** Ular REVIX ning da'vosini boshqa joyga ko'chiradi:
> REVIX **adaptiv qaror ixtiro qilmaydi** — u bitta node'da o'lchanadigan bo'shliqni
> o'lchaydi. Buni maqolada ochiq yozish kerak, aks holda reviewer buni o'zi topadi.

### OSS prior art — deyarli bir xil ishlanmagan artifact

> **`prethivganeshm2023-del/adaptive-self-healing-runtime`** (GitHub)
> <https://github.com/prethivganeshm2023-del/adaptive-self-healing-runtime>

O'zim tasdiqlagan mazmuni:
- systemd + journald + **psutil** telemetriyasi
- `RESTART` / `STOP` / `ESCALATE` orasidan qaror
- **exponential backoff** (1s → 2s → 4s → 8s)
- **`VERIFYING` state** — "the service must remain healthy for the configured verification period"
- rule-based **va** ML diagnostika, post-recovery validation
- 0 star, o'zini "a research and engineering prototype" deb ataydi, sintetik training data

> **Bu REVIX ning "aniq" arxitekturasi — allaqachon yozilgan.** Peer-reviewed emas, lekin
> **reviewer buni topadi.** Maqolada ochiq sitat qilinadi va farq (o'lchov qat'iyligi,
> pre-registration, PSI gating, FR metrikasi) aniq ko'rsatiladi.

### Mahalliy tekshirilgan texnik faktlar
`systemd.service(5)` man sahifasi, systemd 261 (261.2-1), bu mashinada:
- `RestartSteps=`, `RestartMaxDelaySec=` mavjud (misol: `RestartSec=10s`, `RestartSteps=4`, `RestartMaxDelaySec=160s`)
- `ExecCondition=`, `WatchdogSec=`, `StartLimitIntervalSec=`, `RestartMode=` mavjud
- Kubernetes uslubidagi health probe direktivi **yo'q**

`/usr/lib/systemd/system/user@.service.d/10-oomd-user-service-defaults.conf`:
`ManagedOOMMemoryPressure=kill`, `ManagedOOMMemoryPressureLimit=50%`;
`DefaultMemoryPressureDurationSec=20s`.

Batafsil: [`01-texnologiya-auditi.md`](01-texnologiya-auditi.md).

---

## T2 — Subagent skanida topilgan, T1 ga ko'tarilishi kerak

### Asos — autonomic va recovery-oriented computing

| Manba | Ahamiyati |
|---|---|
| Kephart & Chess, *The Vision of Autonomic Computing*, **IEEE Computer 36(1):41–50, 2003**, DOI 10.1109/MC.2003.1160055 | **MAPE-K** loop'ning kelib chiqishi — REVIX quvuri MAPE-K ning bir ko'rinishi |
| Patterson, Brown, Broadwell, Candea, Chen, Cutler, Enriquez, Fox, Kıcıman va boshq., *Recovery Oriented Computing (ROC)*, **UC Berkeley CSD-02-1175, 2002-03-15** | **ROC aynan "recovery benchmark" va tizimli xato kiritishni talab qilgan.** REVIX ning ikkilamchi hissasi shu an'anada |
| Candea, Kawamoto, Fujiki, Friedman, Fox, *Microreboot — A Technique for Cheap Recovery*, **OSDI '04, 31–44** | arzon restart granularligi |
| Candea & Fox, *Recursive Restartability: Turning the Reboot Sledgehammer into a Scalpel*, **HotOS-VIII, 2001** | restart granularligi va dependency |
| Candea & Fox, *Crash-Only Software*, **HotOS IX, 2003** | restart'ni birinchi darajali recovery sifatida |
| Psaier & Dustdar, *A survey on self-healing systems*, **Computing 91:43–73, 2011** | survey |
| Ghosh, Sharman, Rao, Upadhyaya, *Self-healing systems — survey and synthesis*, **Decision Support Systems 42(4):2164–2185, 2007** | survey |

### Adaptiv / o'rganiladigan recovery

| Manba | Ahamiyati |
|---|---|
| Li, Cheng, Hsieh, Dang, Huang, Singh, Yang, Lin, Wu, Levy, Chintalapati, *Gandalf*, **NSDI '20** | Narya shu paket ichida |
| Sanabria, Dusparic, Cardozo, *Learning Recovery Strategies for Dynamic Self-healing in Reactive Systems*, **SEAMS '24** (arXiv 2401.12405) | **Ikkinchi eng yaqin prior art** — Q-learning bilan corrective sequence tanlash, context-oriented programming variatsiyalari |
| Aribe Jr & Oracion, *When Web Apps Heal Themselves: A MAPE-K Based Approach…*, **Int. J. Informatics & Comm. Tech. 15(2):729–740, 2026** (arXiv 2605.19261) | MAPE-K + fault injection, 20 scenario; o'zi "relies on predefined recovery strategies" deb tan oladi. Past darajali venue, lekin framing deyarli bir xil |
| Du, Li, Zheng, Srikumar, *DeepLog*, **ACM CCS 2017** | log'dan anomaliya aniqlash |
| Verma, Pedrosa, Korupolu, Oppenheimer, Tune, Wilkes, *Large-scale cluster management at Google with Borg*, **EuroSys 2015** | task restart/reschedule |

### Kernel infratuzilmasi
PSI: Johannes Weiner, commit `eb414681d5a0`, **Linux 4.20**, `CONFIG_PSI=y`,
`/proc/pressure/{cpu,memory,io}`, 10/60/300 s oynalar.
Iste'molchilar: oomd, systemd-oomd, Kubernetes metrikalari.

### Ishlab chiqarish tizimlari
Pacemaker/Corosync (`on-fail`, `migration-threshold`, `failure-timeout`, OCF `monitor`),
Kubernetes (CrashLoopBackOff 10→300 s, probe'lar, node-pressure eviction, KEP #5734 —
"not planned" deb yopilgan), monit, supervisord, runit/s6, greenboot, systemd Automatic
Boot Assessment, rpm-ostree, snapd, ChromeOS `update_engine`, Android AVB,
OpenStack Masakari, AWS ASG health checks, Event-Driven Ansible, Sensu remediation.

Batafsil taqqoslash: [`01-texnologiya-auditi.md`](01-texnologiya-auditi.md) §6.

### Chaos / fault injection
`stress-ng`, `chaosblade` (CNCF sandbox, Alibaba), Chaos Mesh, LitmusChaos, `pumba`.

Tekshirilmagan, metodologiya yozishdan oldin tasdiqlanishi kerak: Linux
`CONFIG_FAULT_INJECTION` (`failslab`, `fail_page_alloc`, `fail_make_request`), `tc netem`
tafsilotlari, `dm-flakey`, `dm-delay`.

### Boshqa OSS artifact
`advaithsarva/self-healing-system-agent` — gated capability jadvali + verification uchun
qayta o'lchash; 200 seeded trial'da 0 false positive da'vosi. **Men tekshirmadim.**

---

## T3 — SITAT QILINMAYDI

Faqat eslatib o'tilgan, tasdiqlanmagan:
Candea va boshq. *JAGR* (2003); Swift va boshq. *Nooks* (TOCS);
*CRRL: A Causality-Based RL Framework for Autonomous System Recovery* (arXiv 2607.03177);
*Adaptive Fault Injection Planning for Multi-Layer Self-Healing AI Infrastructure* (arXiv 2607.16161);
*Self-Healing Software Systems: Lessons from Nature, Powered by AI* (arXiv 2504.20093);
*Restart-Based Fault-Tolerance* (arXiv 1705.02412);
*Application and system-level software fault tolerance through full system restarts* (ICCPS 2017).

Netflix chaos vositalari — bu skanda tekshirilmadi.

**ResearchGate-da faqat topilgan "RL self-healing infrastructure" natijalari predatory /
peer-reviewed emasga o'xshaydi → butunlay chiqarib tashlanadi.**

---

## Manfiy topilma — REVIX uchun eng muhim

Subagent skani **PSI ni failure detection yoki recovery qaroriga kirish signali sifatida
ishlatgan peer-reviewed maqola TOPMADI.** PSI faqat OOM/eviction trigger sifatida
iste'mol qilinadi.

Shuningdek, **Linux service manager'lar uchun "false recovery" metrikasi yoki recovery
benchmark topilmadi.**

> ⚠️ **Bu manfiy da'vo va manfiy da'volarni tasdiqlash qiyin.** Hozirgi holati:
> **preliminary**. Maqola yozishdan oldin tizimli qidiruv (ACM DL, IEEE Xplore, USENIX,
> DBLP, Google Scholar; kalit so'zlar: PSI, pressure stall, recovery decision, restart
> admission, false recovery, recovery benchmark) bajarilishi va natijasi shu faylga
> yozilishi shart. Hozirgi asosda "birinchi marta" deb **yozilmaydi**.
