# REVIX

**Linux service recovery'ni o'lchash bo'yicha tadqiqot loyihasi.**

---

## Loyiha nima

REVIX — Linux'da xizmat recovery'ining **tizim pressure'iga qanday bog'liqligini**
o'lchaydigan tadqiqot artifact'i. U quyidagilarni beradi:

1. **Operatsion ta'riflar** — "verified recovery" (process-liveness'dan ko'proq),
   "false recovery", uchta downtime o'lchovi
2. **`FR-A`** — oracle-free false-recovery metrikasi
3. **Reproducible recovery benchmark** — nazorat qilinadigan fault injection bilan
4. **Falsifikatsiya qilinadigan gipoteza** va uni sinash uchun harness

## Loyiha nima EMAS

REVIX **adaptiv recovery ixtiro qilmaydi.** Bu ochiq va qat'iy:

| Da'vo qilinmaydi | Chunki allaqachon mavjud |
|---|---|
| Exponential backoff | systemd **v254+**: `RestartSteps=` + `RestartMaxDelaySec=` |
| Adaptiv multi-action selection | **Narya**, OSDI '20 (Microsoft Azure) |
| Post-restart health verification | Kubernetes probe'lari, Pacemaker OCF `monitor`, greenboot |
| Failure-turiga qarab action tanlash | Pacemaker `on-fail`, OpenStack Masakari |
| Health-gated rollback | greenboot, systemd Automatic Boot Assessment, rpm-ostree |

Batafsil: [`docs/research/03-research-gap.md`](docs/research/03-research-gap.md)

Bu shuningdek **Linux distributivi emas**, **desktop theme emas**, **cybersecurity
toolkit emas** va **Kali Linux moslashtirmasi emas**.

---

## Gipotezalar

**H1** — Xizmatni restart qilishning verified recovery bilan tugash ehtimoli, tizim yoki
xizmat cgroup'i yuqori memory/IO pressure ostida bo'lganda sezilarli past:

```
P(verified recovery | high PSI)  <<  P(verified recovery | low PSI)
```

**H2** — PSI-gated restart admission control systemd'ning **native** exponential
backoff'iga nisbatan kam downtime va kam false-recovery beradi.

> H1 — **dunyo haqidagi da'vo**, REVIX haqida emas. Uni sinash uchun REVIX engine'i kerak
> emas: pilot arm'lari shunchaki systemd konfiguratsiyalari.

### Baseline'lar
| | Konfiguratsiya |
|---|---|
| **A** | `Restart=on-failure`, `RestartSec=100ms` |
| **B** | `Restart=on-failure`, `RestartSec=10s`, `RestartSteps=4`, `RestartMaxDelaySec=160s` — **systemd native backoff, kuchli baseline** |
| **C** | PSI-gated admission control + post-restart verification (REVIX) |
| **no_action** | `Restart=no` — majburiy nazorat |

---

## Holat

| Faza | Holat |
|---|---|
| Texnologiya auditi | ✅ bajarildi |
| Prior art skani | ✅ bajarildi (tekshirish darajalari bilan) |
| Research gap | ✅ aniqlandi |
| **Pre-registration (P1)** | ✅ **muzlatildi** |
| Pilot harness | ⏳ keyingi qadam |
| Pilot eksperiment | ⏳ |
| Kalibratsiya (`Repairs()`) | ⏳ |
| Confirmatory eksperiment | ⏳ |
| Arm C (REVIX engine) | ⏳ |

**Hech qanday eksperiment hali ishga tushirilmadi. Hech qanday natija hali yo'q.**

---

## Hujjatlar

| Fayl | Mazmuni |
|---|---|
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | **Muzlatilgan ta'riflar, metrikalar, statistik testlar, falsifikatsiya mezonlari.** Shartnoma. |
| [`docs/research/01-texnologiya-auditi.md`](docs/research/01-texnologiya-auditi.md) | systemd / PSI / cgroup / oomd imkoniyat va cheklovlari — mahalliy tekshirilgan |
| [`docs/research/02-related-work.md`](docs/research/02-related-work.md) | Adabiyot, **T1/T2/T3 tekshirish darajalari** bilan |
| [`docs/research/03-research-gap.md`](docs/research/03-research-gap.md) | Nima qoplangan, nima qolgan |
| [`docs/research/04-novelty-statement.md`](docs/research/04-novelty-statement.md) | Hissa nima va nima emas |
| [`docs/research/05-metodologiya.md`](docs/research/05-metodologiya.md) | Eksperiment darajalari, fault taksonomiyasi, asoslash |
| [`docs/architecture/00-pilot-topologiya.md`](docs/architecture/00-pilot-topologiya.md) | Pilot cgroup topologiyasi va xavfsizlik chegarasi |

---

## ⚠️ Xavfsizlik ogohligi

Bu repozitoriy **nazorat qilinadigan memory pressure** yaratadigan kod o'z ichiga oladi.

Ko'plab Linux desktop tizimlarida `systemd-oomd` foydalanuvchi sessiyasiga qarshi
**kill authority** bilan sozlangan:

```
ManagedOOMMemoryPressure=kill
ManagedOOMMemoryPressureLimit=50%
DefaultMemoryPressureDurationSec=20s
```

PSI **ierarxik** — test slice'i ichidagi stall yuqoriga `user@1000.service` ga tarqaladi.
**Ehtiyotsiz pressure eksperimenti brauzeringizni, editoringizni yoki butun desktop
sessiyangizni o'ldirishi mumkin.**

Majburiy yumshatishlar, harness'da qattiq kodlangan:
1. Har pressure epizodi **≤12 s** (oomd ning 20 s sustained shartidan kam), keyin ≥20 s quiescence
2. **Mustaqil guard process** — driver'dan alohida, birinchi ishga tushadi, oxirida to'xtaydi
3. Slice `MemoryMax` shift + `MemorySwapMax=0` + `TasksMax` + `CPUQuota`
4. Pre-flight: `revix-*` unit yoki `revixlab.slice`/`revixmon.slice` allaqachon mavjud bo'lsa **ishga tushmaydi**

**Guard'ni sinamasdan hech qanday pressure eksperimenti ishga tushirilmaydi.**
Batafsil: [`docs/architecture/00-pilot-topologiya.md`](docs/architecture/00-pilot-topologiya.md)

---

## Talablar

Pilot **privilegiyasiz** ishlaydi (root kerak emas):

| | Minimal |
|---|---|
| systemd | ≥ 254 (`RestartSteps=` uchun) |
| cgroup | **v2**, `cpu memory pids` delegated |
| kernel | PSI yoqilgan (`CONFIG_PSI=y`, ≥ 4.20) |
| Python | ≥ 3.11 + `psutil`, `python-systemd`, `dbus`, `pyyaml`, `numpy`, `scipy` |
| C kompilyator | SUT uchun (`gcc` yoki `clang`) |

Root **faqat** quyidagilar uchun: `io` controller / `io.max`, `dm-delay`/`dm-flakey`,
`tc netem`, cgroup `cpuset` pinning, `scaling_governor`, paket o'rnatish.

> **Loyiha prinsipi:** *"root kerak" = "guest'ga tegishli."* QEMU ichida siz
> izolyatsiyalangan kernel'da root'siz va host privilegiyasi `/dev/kvm` dan boshqa kerak
> emas. Bu benchmark'ni portativ qiladi — ya'ni haqiqiy tadqiqot deliverable'i.

---

## Ilmiy yaxlitlik

Bu loyiha quyidagi qoidalarga bo'ysunadi:

- **FAKT / GIPOTEZA / NATIJA / TALQIN / CHEKLOV** ochiq ajratiladi
- Test ishga tushirilmasa — *"bu test ishga tushirilmadi, sabab: …"* deb yoziladi
- **Manfiy natijalar yashirilmaydi**
- Ta'riflar natijani ko'rgandan **oldin** muzlatiladi va hash bilan run'ga bog'lanadi
- `datasets/` **append-only**; raw ma'lumot hech qachon ustiga yozilmaydi
- Eksklyuziya darajasi **natija sifatida** beriladi
- Sitat faqat tekshirilgan manbalarga (`02-related-work.md` T1/T2/T3)
