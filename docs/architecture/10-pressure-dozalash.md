# 10 — Pressure dozalash kalibratsiyasi (o'lchangan WSL2 muhitida)

Bu hujjatdagi har bir raqam **shu mashinada haqiqatan ishga tushirilgan**
buyruqning chiqishidan olingan. O'lchov bajarilmagan joyda shunday deb
yozilgan. Uchta belgi ishlatiladi:

- **FAKT** — o'lchandi, buyruq va chiqish keltirilgan;
- **TALQIN** — FAKTdan nima kelib chiqishi (o'lchov emas, xulosa);
- **CHEKLOV** — bu muhitda o'lchab bo'lmaydigan yoki kafolatlab bo'lmaydigan narsa.

Bu fayl [`00-pilot-topologiya.md`](00-pilot-topologiya.md) §6 ning **4-qadami**
(`pressure dosing kalibratsiyasi`). U [`08-guard-rekalibratsiya.md`](08-guard-rekalibratsiya.md)
§14.2 ning uchta majburiy kirish shartini bajaradi va §14.3 ning salbiy
verdiktini qayta o'lchaydi.

**Sana:** 2026-10-03 (05:12Z – 05:54Z; mahalliy UTC+05:00)
**Mashina:** hostname `Root-Zero`, Kali Rolling `VERSION_ID="2025.3"` (WSL2),
kernel `6.6.87.2-microsoft-standard-WSL2`, systemd `257 (257.7-1)`,
`MemTotal: 10183876 kB` (≈9.71 GiB), `SwapTotal: 4194304 kB`, 12 CPU
(`AMD Ryzen 5 5600H with Radeon Graphics`), uid 1000 (`snowden`),
`systemd-oomd` **o'rnatilmagan** (`NOT-INSTALLED / inactive`),
delegated controllers: `cpu memory pids`.
**Topologiya:** `revixlab.slice` (**MemoryMax=2G** — `00` §1 ning muzlatilgan
qiymati, `08` ning 1G i **emas**; MemoryHigh=192M, MemorySwapMax=0,
TasksMax=256, CPUQuota=400%), `revixmon.slice` (harness, sibling).
**Kompilyator:** `cc (Debian 14.3.0-5) 14.3.0`.
**Repo:** `experiment/pressure-dose`, commit `f3c2d1e`, `git_dirty=no`,
`PREREGISTRATION.md` = `preregistration/v1.10`.
**Bajarilish joyi:** ext4 (`$HOME/revix-work`, `fs=ext2/ext3`), chiqishlar
`$HOME/revix-runs/` — `/mnt/c` (9p/drvfs) ustida **emas** (`07` §7.2).
**Hajm:** 9 run, **35 pressure epizodi**, 78 SUT start'i, 36 fault injeksiyasi.

---

## 0. Qisqa xulosa

| | |
|---|---|
| Doza yetkazildimi? | ✅ **HA — bu mashinada BIRINCHI MARTA.** Dial: `MemoryHigh=192M`, `base_mb=184`, `step_mb=4` (§2) |
| Mexanizm tasdiqlandimi (throttling, OOM emas)? | ✅ **HA** — `memory.events high` o'sdi (2191–5748/epizod), `max` **0**, `oom_kill` **0**, `memory.swap.current` **0** (§2.3) |
| `P0` yetkaziladimi? | ✅ **HA** — erishilgan stall **aynan 0.0000**, 9.8/9.8 s band ichida (§3.2) |
| `P1` (0.20–0.35) yetkaziladimi? | ✅ **HA** — nishon 0.30 → epizod medianalari **0.2234–0.3892**, 10/13 band ichida (§3.3) |
| `P2` (0.60–0.80) yetkaziladimi? | ⚠️ **MEDIANA bo'yicha HA** — nishon **0.60** → epizod medianalari **0.5726–0.9213**, 8/11 band ichida (§3.4) |
| `P2` **USHLAB TURILADIMI**? | ❌ **YO'Q** — band ichidagi eng uzun **uzluksiz** qolish **1.1 s**, ≈9.5 s hold'da (§3.4) |
| `P1` ushlab turiladimi? | ❌ **YO'Q** — eng uzun uzluksiz **1.9 s** (§3.3) |
| `ramp_above_threshold_s` | **0.000 s** — `base_mb=184` da **29 epizoddan 29 tasida**, haqiqiy doza bilan (§4.1) |
| §9.4 invariant 2 (`hold + ramp ≤ 15 s`) | ✅ **BAJARILADI**: `12 + 0.000 = 12.000 ≤ 15`, 3.000 s zaxira (§4.2) |
| §9.4 invariant 1 / epizod chegarasi | ✅ **BAJARILADI** — `overrun_s` n=34, p50 **0.0619 s**, max **0.2899 s** (§5) |
| **`p90(t_start)` — kalibrlangan `P2`** | **0.7863 s** (n=24, 22/24 budjet ichida) → §17.2 ning **0.8 s budjeti BAJARILDI**, 1.02× (§6.5) |
| `p90(t_start)` — kalibrlangan `P1` | **0.9543 s** (n=24, 19/24) → budjet **BAJARILMADI**, 0.84× (§6.5) |
| `p90(t_start)` — `P1 + P2` (n=48) | **0.9105 s** (41/48) → budjet **BAJARILMADI**, 0.88× (§6.5) |
| `p90(t_start)` — `P0` nazorat | **0.0481 s** (n=30, 30/30) → 16.65× zaxira (§6.2) |
| Start muvaffaqiyatsizligi | **0/78** — `08` ning 6/14 va 1/7 iga qarshi (§6.2) |
| Kechikish SUT ichidami? | ❌ **YO'Q** — SUT o'z `uptime_us` p50 **0.0151/0.0152 s**, `t_start` p50 **0.5041/0.5727 s** → **97.0–97.3% SUT tashqarisida** (§6.4) |
| **§17.5 ning qarori hali kerakmi?** | ⚠️ **`08` ning 6.8× halokati RAD ETILDI; nuqson budjet CHEGARASIDA qoldi — qaror hamon kerak** (§6.5, §12.4) |
| `D_probe` proxy p50 | `P0` **0.300 s** · `P1` **0.900 s** · `P2` **1.000 s** (har birida n=12) (§7) |
| §18.6 ning qarori kerakmi? | ✅ **HA, uchala bandda** — `thr = 0.60 / 1.70 / 2.05 × P`, hammasi **< 5P** (§7.5) |
| Brownout (restart'siz contract buzilishi) | `P0` **0**, `P1` **4**, `P2` **4** epizod — §9.2 (iii) ning o'lchangan izi (§7.4) |
| Probe narxi (§8.2) | `core_percent` **0.2663–0.2968%**, budjet 1.0%, `budget_exceeded: false` uchala bandda (§7.6) |
| Guard trip | **1 marta** (35 epizod): `user_full_rate2s_runaway` `rate=0.9801962`, `kill_ok: true` (§8.2) |
| Kollateral zarar | ✅ **YO'Q**; qoldiq **NOL** (§9) |
| Pilot ishga tushirilishi mumkinmi? | ❌ **YO'Q** — `driver.py` dozalash parametrlarini bermaydi (OQ-2) (§12.5) |

---

## 1. Metodologiya, harness va provenance

### 1.1 FAKT — `scripts/guard-test.sh` ISHLATILMADI va O'ZGARTIRILMADI

`08` §2 ikki blokerni o'lchagan: (1) `pgrep -f 'claude-desktop --type=renderer'`
`set -euo pipefail` ostida skriptni o'ldiradi (bu guest'da bunday jarayon yo'q —
Claude va Chrome Windows tomonida); (2) skript `revixlab.slice` ga **hech qanday
property qo'ymaydi**, demak `memory.high` qo'yilmaydi va pressure mexanizmi
**mavjud bo'lmaydi**.

Men skriptni **bir bayt ham o'zgartirmadim** (u mening faylim emas) va uni
ishlatmadim ham. Blokerlardan tashqari **uchinchi**, dozalash uchun hal
qiluvchi sabab bor: `guard-test.sh` bitta chaqiruvda **bitta** pressure
epizodi bajaradi, dozalash kalibratsiyasi esa bitta guard jarayoni ostida
**ketma-ket ko'p epizod** talab qiladi (nishon sweep'i, band taqqoslashi,
`t_start` va `D_probe` namunalari).

Shuning uchun **scratchpad'dagi** (repo'dan **tashqarida**, commit
qilinmaydigan) o'z runner'imni yozdim. U loyihaning aynan o'sha modullarini
**o'zgartirmasdan** chaqiradi:

```
python3 -m revix.guard        --watch-cgroup <user@> --lab-cgroup <lab> \
                              --log guard.jsonl --trip-file trip.json --max-seconds N
python3 -m revix.psi_sampler  --with-host --with-user \
                              --scope lab=<lab> --scope mon=<mon> --hz 10
python3 -m revix.pressure     --mode pi --cgroup <lab> --target-rate T \
                              --step-mb S --base-mb B --chunk-mb 32 \
                              --interval-ms 250 --max-seconds N
python3 -m revix.prober       --target sut=<socket> --hz 10 --report-cost
make -C revix all   &&   systemd-run … $HOME/revix-work/revix/sut
```

Hamma narsa `systemd-run --user --slice=revixlab.slice` (SUT, generator) yoki
`--slice=revixmon.slice` (guard, sampler, prober, kuzatuvchi) orqali — hech
narsa shell'dan tug'ilmaydi (`00` §2).

**Operator qadami** (skriptda emas, `08` §2.2 bilan bir xil yondashuv):

```
$ systemctl --user set-property --runtime revixlab.slice \
    MemoryMax=2G MemoryHigh=192M MemorySwapMax=0 TasksMax=256 CPUQuota=400%
set-property rc=0
$ systemctl --user show revixlab.slice -p MemoryMax -p MemoryHigh \
    -p MemorySwapMax -p TasksMax -p CPUQuotaPerSecUSec
CPUQuotaPerSecUSec=4s   MemoryHigh=201326592   MemoryMax=2147483648
MemorySwapMax=0         TasksMax=256
```

Kernel tomonidan o'zaro tekshiruv (slice cgroup'i yaratilgandan **keyin**,
har run'da):

```
kernel: memory.max=2147483648  memory.high=201326592  memory.swap.max=0
        pids.max=256           cpu.max=400000 100000
```

`201326592 B = 192 MiB`, `2147483648 B = 2 GiB` — ya'ni `00` §1 ning
muzlatilgan `MemoryMax=2G` i **haqiqatan qo'llanildi**.

**FAKT — `08` §2.2 ning tmpfs tuzog'i takrorlanmadi.** Barcha drop-in'lar
`/run/user/1000/systemd/user.control/revixlab.slice.d/` da paydo bo'ldi
(`50-MemoryMax.conf`, `50-MemoryHigh.conf`, `50-MemorySwapMax.conf`,
`50-TasksMax.conf`, `50-CPUQuota.conf`) va **setup har run bilan bir xil
`wsl.exe` chaqiruvida** bajarildi. `~/.config/systemd/user/` butun sessiya
davomida **umuman mavjud bo'lmadi**.

### 1.2 Har run'da qayd etilgan narsa

Har run'ning oldi va orqasida (`marker-pre.txt`, `marker-post.txt`):
`wall_utc`, `boot_id`, `/proc/uptime`, **`/proc/1/stat` 22-maydon**
(`pid1_starttime_ticks`), PID 1 yoshi, user manager PID, `MemAvailable`,
`SwapFree`, `/proc/vmstat oom_kill`, lab `memory.swap.current`, lab
`memory.events`, lab `memory.current`, `revix*` unit va cgroup'lari, failed
unit'lar, begona `pytest`/`verify` jarayonlari, journal'dagi oom/oomd hits.

Run **davomida**: `revix/psi_sampler.py` 10 Hz da (`host`/`user`/`lab`/`mon`,
har scope uchun alohida `read_mono_us` — `PREREGISTRATION.md` §7),
`revix-watch` 5 Hz da (read-only: lab `memory.current`, `memory.peak`,
`memory.swap.current`, `memory.events`, `/proc/vmstat oom_kill`).
Har **epizodning** oldi va orqasida lab `memory.events` to'g'ridan-to'g'ri
o'qildi — shuning uchun `high` delta'si **epizod bo'yicha** beriladi.

Tezlik **har joyda** `PREREGISTRATION.md` §7 ning qoidasi bilan hisoblanadi:
`total=` deltasi, **eng tor ≥2 s oyna** (`02` §2 va `guard.py` bilan aynan bir
xil qoida). `avgN` **hech qanday qarorda ishlatilmadi** — faqat
`t_start` jadvallarida kontekst uchun keltiriladi.

### 1.3 FAKT — run'lar va ularning yaroqliligi

9 run, 35 pressure epizodi. Har run'da `boot_id` **va**
`pid1_starttime_ticks` ikki chekkada solishtirildi:

| run | maqsad | epizod | `boot_id` | `pid1_starttime_ticks` | `vmstat oom_kill` | holat |
|---|---|---|---|---|---|---|
| `dose-01-dial` | dial qidiruvi | 3 | `ca924fea` → `ca924fea` | 75 → 75 | 0 → 0 | ✅ **YAROQLI** |
| `dose-02-bands` | band sweep | 6 | `7484ed3a` → `7484ed3a` | 80 → 80 | 0 → 0 | ✅ **YAROQLI** |
| `dose-03-p2sweep` | `P2` nishon sweep'i | 6 | `32301222` → `32301222` | 82 → 82 | 0 → 0 | ✅ **YAROQLI** |
| `tstart-P0` | `t_start` nazorat | 0 | `32301222` → `32301222` | 26992 → 26992 | 0 → 0 | ✅ **YAROQLI** |
| `tstart-P1` | `t_start` kalibrlangan `P1` | 6 | `32301222` → `32301222` | 32172 → 32172 | 0 → 0 | ✅ **YAROQLI** |
| `tstart-P2` | `t_start` kalibrlangan `P2` | 6 | `32301222` → `32301222` | 32172 → 32172 | 0 → 0 | ✅ **YAROQLI** |
| `dprobe-P0` | `D_probe` nazorat | 0 | `32301222` → `32301222` | 32172 → 32172 | 0 → 0 | ✅ **YAROQLI** |
| `dprobe-P1` | `D_probe` kalibrlangan `P1` | 4 | `32301222` → `32301222` | 32172 → 32172 | 0 → 0 | ✅ **YAROQLI** |
| `dprobe-P2` | `D_probe` kalibrlangan `P2` | 4 | `32301222` → `32301222` | 32172 → 32172 | 0 → 0 | ✅ **YAROQLI** |

**FAKT:** birorta run `boot_id` o'zgarishini yoki PID 1 restart'ini qamrab
olmadi, demak **birorta run yaroqsiz deb belgilanmadi** va hech bir raqam
tashlab yuborilmadi.

**FAKT — kontaminatsiya YO'Q.** Har ikki chekkada `interference=` maydoni
**bo'sh** (begona `pytest`/`verify` jarayoni yo'q) va `journal_oom_hits=0`.
`08` §1.3 ning holati takrorlanmadi, demak bu hujjatda CLEAN/DIRTY ajratishi
**kerak emas**: barcha run'lar toza.

**CHEKLOV — run'lar ORASIDA PID 1 restart bo'ldi, run'lar ICHIDA emas.**
`boot_id` uch marta o'zgardi (`ca924fea` → `7484ed3a` → `32301222`, va
yakuniy tekshiruv paytida `b7a7f0b5`) va `pid1_starttime_ticks` run'lar
orasida sakradi (82 → 26992 → 32172). Bu `07` §4.4 / `08` §8 ning distro
idle-stop xatti-harakati. **Oqibati:** monotonik qiymatlar **run'lar
bo'ylab taqqoslanmaydi**, va bu hujjatda hech qanday taqqoslash run
chegarasini kesib o'tmaydi. Har bir statistik yig'ma (masalan `t_start`
p90) bitta run ichidagi namunalardan, yoki bandni belgilaydigan bitta
run'dan olinadi.

**CHEKLOV — `$HOME/revix-runs/guard-recal-*` 08 NING ma'lumoti.**
O'sha katalog bu guest'da `08` dan qolgan va unda 13 run bor. Mening
yig'malarim **faqat** yuqoridagi 9 run'dan hisoblanadi; `guard-recal-*`
**chiqarib tashlangan** va uning birorta raqami bu hujjatda ishlatilmagan.

### 1.4 CHEKLOV — epizod uzunligi pilotning epizodidan QISQA

Topshiriqning xavfsizlik qoidasi: **har pressure epizodi ≤ 12 s**. Men
`--max-seconds 12` + `RuntimeMaxSec=14s` ishlatdim, hamma joyda, 35 epizodda.

`revix/driver.py` esa generatorga `max_seconds = ramp_s + hold_s` beradi
(`_start_pressure`: `(pressure_off - ramp_start)/1e6`), ya'ni
`PREREGISTRATION.md` §9.4 ning jadvali bilan **5 + 12 = 17 s**. Demak
pilotning haqiqiy epizodi 17 s, mening o'lchovim 12 s.

**Oqibati:** o'lchangan ramp **2.553–2.614 s** (`base_mb=184`, §4.1), demak
hold uchun **≈9.5 s** qoldi, pilotda esa 12 s bo'lardi. Band ichida qolish
vaqtlari (§3) **≈9.5 s hold uchun** berilgan va 12 s ga
**ko'chirilmaydi**. `ramp_above_threshold_s` esa ramp fazasining
xususiyati va hold uzunligiga bog'liq emas, demak u **ko'chiriladi**
(§4.2). Bu **OQ-5**.

---

## 2. 🔴 Dial — doza bu mashinada BIRINCHI MARTA yetkazildi

### 2.1 Arifmetika — nega `08` ning dozasi nol bo'lgan

`02` §3 mexanizmni shunday belgilaydi:

> «**Baza `memory.high` dan bir oz PAST bo'lishi kerak** (avtomatik:
> `high - 2*blok`). Shunda ramp **bepul** bo'ladi va pressure faqat churn
> impulslaridan keladi. O'lchangan: `baza=184MB` (high=192MB), ramp tezligi
> median **0.000**, max **0.000**.»

`revix/pressure.py:run_pi` shu formulani bajaradi:

```python
base = max(16, (high // (1 << 20)) - 2 * step_mb)
```

`high = 192 MiB` da:

| `step_mb` | `base = 192 − 2·step_mb` | manba |
|---|---|---|
| **16** (modul default'i) | **160 MiB** | `08` §3.4 ning **NOL-doza** juftligi |
| 8 | 176 MiB | — |
| **4** | **184 MiB** | **`02` §3 ning O'LCHANGAN juftligi** |
| 2 | 188 MiB | — |

> **Ya'ni `02` §3 ning `base = 184` i FAQAT `step_mb = 4` da chiqadi.**
> `08` skript default'i `STEP_MB=16` bilan ishlagan, bazasi 160 MiB
> bo'lgan va doza **0.000** chiqqan. Bu `MemoryMax` ning (1G yoki 2G)
> masalasi **emas** — §2.2 buni o'lchov bilan ko'rsatadi.

### 2.2 FAKT — o'lchangan dial sweep'i (`dose-01-dial`, nishon 0.30, `MemoryMax=2G`)

```
$ python3 -m revix.pressure --mode pi --cgroup <lab> --target-rate 0.30 \
    --step-mb <S> --chunk-mb 32 --interval-ms 250 --max-seconds 12 \
    --log pressure.jsonl
```

| epizod | `step_mb` | `base_mb` (auto) | **erishilgan stall p50** | p95 | `memory.current` max | `ramp_above_threshold_s` | `overrun_s` |
|---|---|---|---|---|---|---|---|
| **D1** | 16 | **160** | **0.0000** | 0.0000 | **185.3 MiB** | 0.000 s | 0.0563 |
| **D2** | **4** | **184** | **0.3344** | 0.9346 | **197.2 MiB** | 0.000 s | 0.0614 |
| **D3** | 8 | 176 | 0.0138 | 0.0193 | 193.7 MiB | 0.000 s | 0.0579 |

**FAKT — D1 `08` §3.4 ni AYNAN takrorladi.** `memory.current` max
**185.3 MiB** — `08` §3.4 ning o'lchovi ham **185.3 MiB**. `touched_mb`
160 da barqaror, churn `p50=7 max=12 sum=315`, erishilgan tezlik
**114 namunada ham aynan 0.0000**, `memory.events high` delta **0**.

> **TALQIN:** nol doza **`MemoryMax=1G` ning artefakti EMAS** — u `2G` da
> aynan shunday takrorlanadi, bitta kasrgacha. Sababi `MemoryMax` emas,
> **`base_mb`**. Bu `08` §12 OQ-4 ni (*«dial 2G da qaytadan chiqarilishi
> kerak»*) **yopadi**: `MemoryHigh = 192M` **ko'chiriladi**, o'zgarishi
> kerak bo'lgan narsa `step_mb`.

**FAKT — D2 doza berdi.** Nishon 0.30, erishilgan p50 **0.3344**
(xato +0.0344). `02` §4 ning avvalgi mashinadagi o'lchovi: nishon 0.30 →
erishilgan **0.311** (xato +0.011). Ya'ni **`02` §4 ning natijasi bu
mashinada qayta ishlab chiqarildi** — lekin faqat to'g'ri `step_mb` bilan.

**TALQIN — arifmetikaning o'zi.** `memory.current` = `touched_mb` +
generator overhead'i. O'lchangan overhead: D1 da `185.3 − 160 = 25.3 MiB`.
Demak:

```
base=160: 160 + 25.3 = 185.3 MiB  <  192 MiB (high)  -> breach YO'Q   -> stall 0.0000
base=176: 176 + 25.3 = 201.3 MiB  >  192 MiB         -> kichik overage -> stall 0.0138
base=184: 184 + 25.3 = 209.3 MiB  >  192 MiB         -> katta overage  -> stall 0.33
```

`base=184` da kernel `memory.current` ni **197.2 MiB** da ushlab turdi
(209.3 emas) — ya'ni reclaim faol ishladi, va **aynan shu ish stall**dir.

### 2.3 FAKT — mexanizm tasdiqlandi: throttling, OOM emas

`02` §3 fault class 4 uchun shart qo'yadi: `high` o'sishi kerak, `max` va
`oom_kill` **0** qolishi kerak. Epizod chekkalarida to'g'ridan-to'g'ri
o'qilgan `lab/memory.events` (`dose-02-bands`):

| epizod | `base_mb` | nishon | `high` delta | `max` | `oom` | `oom_kill` | `memory.swap.current` |
|---|---|---|---|---|---|---|---|
| `P0` | 160 | 0.0 | **0** | 0 | 0 | 0 | **0** |
| `P1a` | 184 | 0.30 | **2191** | 0 | 0 | 0 | **0** |
| `P1b` | 182 | 0.30 | **2476** | 0 | 0 | 0 | **0** |
| `P2a` | 184 | 0.70 | **5748** | 0 | 0 | 0 | **0** |
| `P2b` | 188 | 0.70 | **1357** | 0 | 0 | 0 | **0** |
| `P2c` | 196 | 0.70 | **1452** | 0 | 0 | 0 | **0** |

`dose-03-p2sweep` (hammasi `base=184`, `step=4`):

| nishon | 0.40 | 0.45 | 0.50 | 0.55 | 0.60 | 0.30 |
|---|---|---|---|---|---|---|
| `high` delta | 3355 | 3381 | 3739 | 4395 | **4842** | 2215 |

**FAKT:** `memory.events max` butun sessiyada, **35 epizodning hammasida**,
barcha namunada **0**. `oom` va `oom_kill` ham **0**.
`/proc/vmstat oom_kill` har run'ning ikki chekkasida **0**.

**FAKT:** `memory.swap.current` **hamma run'da, hamma namunada 0** — ikki
mustaqil kuzatuvchi (10 Hz sampler va 5 Hz watcher) bo'yicha. `SwapFree`
`4194304 kB` da **o'zgarmadi**. `00` §3.3 ning abort sharti **birorta
marta ham yuzaga kelmadi**.

**FAKT:** `memory.current` cho'qqisi dozalangan epizodlarda
**197.2–199.2 MiB**, over-doza epizodlarida `memory.peak` 211.1 va
215.1 MiB — ya'ni `memory.high` (192 MiB) dan **bir oz yuqori** va
`memory.max` (2048 MiB) dan **ancha past** (eng yomon holatda 9.5×
zaxira).

→ **`02` §3 ning fault class 4 sharti bajarildi: throttling bor, kill yo'q.**

### 2.4 🔴 TALQIN — `02` §3 ning dizayn bayonoti bu mashinada YARIM to'g'ri

`02` §3 aytadi: *baza `memory.high` dan **PAST** bo'lishi kerak, shunda ramp
bepul bo'ladi va pressure faqat **churn impulslaridan** keladi.*

O'lchov buni **ikki qismga ajratadi**:

1. **«Ramp bepul bo'ladi» — TASDIQLANDI.** `base=184` da
   `ramp_above_threshold_s` **29 epizoddan 29 tasida 0.000 s**, ramp
   tezligi `min = p50 = max = 0.0000` (§4.1).
2. **«Pressure churn impulslaridan keladi» — RAD ETILDI.** O'lchangan churn
   hajmi dozalangan epizodlarda **hayratlanarli kichik**:

| run / epizod | `base_mb` | nishon | erishilgan p50 | `churn/tik` p50 | max | **sum** |
|---|---|---|---|---|---|---|
| `D1` | 160 | 0.30 | **0.0000** | 7.0 | 12 | **315** |
| `D3` | 176 | 0.30 | 0.0138 | 7.0 | 11 | **297** |
| `P1a` | 184 | 0.30 | 0.2834 | **0.0** | 3 | **6** |
| `T60` | 184 | 0.60 | 0.7174 | **0.0** | 7 | **13** |
| `P2a` | 184 | 0.70 | 0.8868 | **0.0** | 8 | **12** |

**TALQIN:** nol-doza konfiguratsiyasida controller **to'yingan** holda
315 blok churn qildi va **hech narsa chiqarmadi**; doza beradigan
konfiguratsiyada esa controller **deyarli hech narsa qilmaydi** (6–13 blok),
chunki stall allaqachon bazadan keladi va controller `n = 0` ga tushadi.

Qolaversa `base_mb=184` da `memory.current` **197.2 MiB > 192 MiB**, ya'ni
`02` §3 ning «baza high dan past» bayonoti `touched_mb` haqida to'g'ri
(184 < 192), lekin **`memory.current` haqida noto'g'ri** — generator
overhead'i (25.3 MiB, o'lchangan) bazani high'dan yuqoriga chiqaradi, va
**doza aynan shu overage'dan keladi**.

> **Demak dozaning haqiqiy knob'i `base_mb` (ya'ni `memory.current` ning
> `memory.high` dan oshishi), `02` §3 aytganidek blok hajmi va churn soni
> EMAS.** Bu frozen hujjat bilan ziddiyat va **OQ-1** da qayd etilgan.
> Men `02` ni o'zgartirmayman.

### 2.5 🔴 FAKT — pilot KODI hozir nol-doza konfiguratsiyasida ishlaydi

`revix/driver.py:_pressure_argv` generatorga **`--step-mb` ham,
`--base-mb` ham, `--interval-ms` ham BERMAYDI**:

```python
def _pressure_argv(self, level: str, max_seconds: float) -> list[str]:
    return [
        self.cfg.python, "-m", "revix.pressure",
        "--mode", "pi",
        "--cgroup", str(self.lab_cgroup),
        "--target-rate", f"{pressure_target_rate(level)}",
        "--max-seconds", f"{max_seconds:.3f}",
        "--log", self.pressure_path,
        "--run-id", self.run_id,
        "--session-id", self.cfg.session_id,
    ]
```

Demak pilot `revix/pressure.py` ning default'larini meros qiladi:
`step_mb = 16`, `interval_ms = 250`. `driver.py` ning
`DEFAULT_MEMORY_HIGH = "192M"` i bilan birga bu
**`base = 192 − 2·16 = 160 MiB`** beradi — ya'ni **aynan D1/`P0` ning
o'lchangan nol-doza konfiguratsiyasi** (§2.2).

**TALQIN:** bugun pilot ishga tushirilsa, `P1` va `P2` arm'lari
**0.0000 stall** bilan ishlardi va `PREREGISTRATION.md` §9.3 ning uch
darajali dizayni **jimgina bitta darajaga — `P0` ga — qulardi**. Natija
null bo'lardi va u **H1 ga qarshi dalil emas, asbob nuqsoni** bo'lardi.
Bu `PREREGISTRATION.md` §9.2 ning *«liveness-only VR ta'rifi ehtimol
null pilot beradi, va bu null — ta'rif artefakti»* ogohligining
**asbob tomonidagi analogi**.

**Bu kod o'zgarishini talab qiladi, lekin men hech qanday kodni
o'zgartirmadim** (topshiriqning fayl egaligi qoidasi). Topilma **OQ-2**
sifatida qayd etilgan; hal qilish `driver.py` egasining qarori.

### 2.6 FAKT — kalibrlangan dial

```
MemoryMax   = 2G      (00 §1, muzlatilgan — TASDIQLANDI)
MemoryHigh  = 192M    (driver.py DEFAULT_MEMORY_HIGH — 2G ostida TASDIQLANDI)
step_mb     = 4       (KRITIK: modul default'i 16 NOL doza beradi)
base_mb     = 184     ( = 192 - 2*4;  02 §3 ning O'LCHANGAN qiymati)
chunk_mb    = 32
interval_ms = 250     (modul default'i)

P0:  base_mb = 160,  target_rate = 0.0
P1:  base_mb = 184,  target_rate = 0.30
P2:  base_mb = 184,  target_rate = 0.60    (driver.py ning 0.70 i EMAS — §3.1)
```

---

## 3. Uch band — erishilgan doza va USHLAB TURISH

Tezlik: `lab` scope, `total=` deltasi, eng tor ≥2 s oyna, 10 Hz namuna
(bitta namuna = 0.1 s). Hold fazasi = oxirgi `pressure_ramp` yozuvidan
`pressure_stop` gacha (≈9.5 s).

### 3.1 FAKT — nishon → erishilgan xaritasi (`base_mb=184`, `step_mb=4`)

| nishon | erishilgan p50 | xato | o'rnashgan p50 (oxirgi 6 s) | p05 | p95 | manba |
|---|---|---|---|---|---|---|
| 0.00 (`base=160`) | **0.0000** | +0.0000 | 0.0000 | 0.0000 | 0.0000 | `dose-02` `P0` |
| **0.30** | 0.2834 | −0.0166 | 0.2699 | 0.0411 | 0.8332 | `dose-02` `P1a` |
| 0.40 | 0.5253 | +0.1253 | 0.4261 | 0.0529 | 0.9480 | `dose-03` `T40` |
| 0.45 | 0.4833 | +0.0333 | 0.4156 | 0.0438 | 0.9076 | `dose-03` `T45` |
| 0.50 | 0.5841 | +0.0841 | 0.5364 | 0.0731 | 0.9239 | `dose-03` `T50` |
| 0.55 | 0.5395 | −0.0105 | 0.5138 | 0.1901 | 0.9390 | `dose-03` `T55` |
| **0.60** | **0.7174** | +0.1174 | 0.6896 | 0.0760 | 0.9361 | `dose-03` `T60` |
| 0.70 | **0.8868** | +0.1868 | 0.8901 | 0.1751 | 0.9428 | `dose-02` `P2a` |

**FAKT:** xarita **chiziqli emas va monoton ham emas** (0.40 → 0.5253
lekin 0.45 → 0.4833; 0.50 → 0.5841 lekin 0.55 → 0.5395). Nishon 0.70
band `P2` ning **ustidan** o'tib ketadi (0.8868).

> **TALQIN:** `P2` (0.60–0.80) uchun o'lchangan to'g'ri nishon **0.60**,
> `driver.py` ning `PRESSURE_TARGET_RATE["P2"] = 0.70` i **emas**
> (u over-doza beradi). `P1` uchun **0.30** to'g'ri va u `driver.py`
> dagi qiymat bilan **mos keladi**.

### 3.2 FAKT — band `P0`: yetkaziladi va USHLAB TURILADI

`dose-02-bands` `P0` (nishon 0.0, `base_mb=160`, `step_mb=4`):

```
erishilgan stall: p05=0.0000 p50=0.0000 p95=0.0000 min=0.0000 max=0.0000  (n=98)
band P0 [0.0,0.05]: 98 namuna = 9.8 s ichida, eng uzun uzluksiz = 9.8 s
memory.events high delta = 0      memory.current max = 169.2 MiB
churn/tik: n=40 p50=0.0 max=0 sum=0
```

**FAKT:** `P0` **to'liq hold davomida** (9.8/9.8 s) band ichida.
`PREREGISTRATION.md` §9.3 ning «generator idle» sharti bajarildi:
generator tirik, 160 MiB rezident, lekin **birorta stall mikrosekundi
yig'ilmadi** va birorta `high` hodisasi bo'lmadi.

### 3.3 FAKT — band `P1` (0.20–0.35): yetkaziladi, lekin USHLAB TURILMAYDI

**13 epizod**, nishon 0.30, `base_mb=184`, `step_mb=4`
(`dose-01` D2, `dose-02` P1a, `dose-03` T30b, `tstart-P1` ×6,
`dprobe-P1` ×4):

```
epizod medianalari (n=13), o'sish tartibida:
  0.2234  0.2303  0.2495  0.2566  0.2670  0.2726  0.2810
  0.2834  0.3344  0.3379  0.3518  0.3658  0.3892

min = 0.2234   p50 = 0.2810   max = 0.3892   mean = 0.2956
band [0.20, 0.35] ICHIDA bo'lgan epizod medianalari: 10/13
```

| o'lchov | qiymat |
|---|---|
| epizod medianalarining medianasi | **0.2810** (nishon 0.30, xato **−0.0190**) |
| band ichida bo'lgan epizodlar | **10/13** (chetda: 0.3518, 0.3658, 0.3892 — hammasi band **ustida**) |
| band ichida **eng uzun uzluksiz** qolish | 0.3 / 0.4 / 0.4 / 0.5 / 1.3 / 1.4 / 1.6 / 1.6 / 1.7 / 1.7 / 1.8 / 1.8 / **1.9 s** |
| band ichida **jami** qolish | 1.2–2.9 s, ya'ni hold'ning **13–31%** i |
| `p05` oralig'i | 0.0343 – 0.1901 |
| `p95` oralig'i | 0.5666 – 0.9480 |

**FAKT:** medianalar bandni **yaxshi topadi** (10/13, xato −0.019), **lekin
band ichida eng uzun uzluksiz qolish 1.9 s**, ≈9.5 s hold'da — ya'ni
hold'ning **20%** i. `p95 − p05` = **0.51–0.90**, demak treatment
`[0.03, 0.95]` oralig'ida tebranadi.

### 3.4 🔴 FAKT — band `P2` (0.60–0.80): mediana erishiladi, USHLAB TURILMAYDI

Bu topshiriqning asosiy savollaridan biri. **11 epizod**, nishon 0.60,
`base_mb=184`, `step_mb=4` (`dose-03` T60, `tstart-P2` ×6, `dprobe-P2` ×4):

```
epizod medianalari (n=11), o'sish tartibida:
  0.5726  0.5988  0.6120  0.6164  0.6753  0.7023
  0.7094  0.7174  0.7288  0.7412  0.9213

min = 0.5726   p50 = 0.7023   max = 0.9213   mean = 0.6905
band [0.60, 0.80] ICHIDA bo'lgan epizod medianalari: 8/11
```

| o'lchov | qiymat |
|---|---|
| epizod medianalarining medianasi | **0.7023** (nishon 0.60, xato **+0.1023**) |
| band ichida bo'lgan epizodlar | **8/11** (chetda: 0.5726 va 0.5988 — band **ostida**; 0.9213 — band **ustida**) |
| band ichida **eng uzun uzluksiz** qolish | 0.4 / 0.4 / 0.4 / 0.5 / 0.5 / 0.5 / 0.5 / 0.5 / 0.6 / 0.8 / **1.1 s** |
| band ichida **jami** qolish | 1.3–1.9 s, ya'ni hold'ning **14–20%** i |
| `p05` oralig'i | 0.0750 – 0.1989 |
| `p95` oralig'i | 0.9276 – 0.9545 |

Taqqoslash uchun, nishon **0.70** da (`dose-02` `P2a`): erishilgan p50
**0.8868** (band **ustida**), lekin band ichida eng uzun uzluksiz
**2.2 s** — ya'ni banddan yuqorida ishlagan epizod bandni **uzoqroq**
kesib o'tdi, chunki u bandni pasayish yo'lida bosib o'tdi.

> **TALQIN — javob ochiq va aniq:**
>
> **`P2` nishon sifatida ERISHILADI** (epizod medianalarining 8/11 i
> `[0.60, 0.80]` ichida, `PI` controller bilan, guard trip'siz, 12 s
> epizod ichida) — **lekin USHLAB TURILMAYDI**: band ichida eng uzun
> uzluksiz qolish **1.1 s**, hold'ning 12% i. `p05 = 0.075` va
> `p95 = 0.95` — ya'ni oniy tezlik butun oraliqni bosib o'tadi.
>
> Bu `08` §3.6 va `PREREGISTRATION.md` §21.8 ning holatini **bir qadam**
> oldinga olib boradi: `08` `P2` ni faqat nazoratsiz ramp'ning
> **0.6–0.9 s traversi** sifatida ko'rgan; bu hujjat uni **nishon
> sifatida** ko'rsatadi. **Lekin uzluksiz 2 s ham turmaydi**, demak
> §21.8 ning hukmi — *«erishiladigan deb ko'rsatildi, ushlab turilgani
> ko'rsatilMADI»* — **o'z kuchida qoladi**. §9.3 ning `P2` bandi
> **isbotlanmadi va rad etilmadi**; endi sabab o'lchangan (§3.5).

### 3.5 TALQIN — nega ushlab turilmaydi: mexanizm HAMON BINAR

`02` §3 ning eng muhim bayonoti: *anonim + `swap=0` bilan mexanizm
**binar**, o'rta band **YO'Q***:

```
memory.high dan past   -> stall ~= 0.000
memory.high dan yuqori -> stall ~= 0.93 .. 0.98
o'rta band             -> YO'Q
```

O'lchangan vaqt qatori buni **to'g'ridan-to'g'ri ko'rsatadi**
(`dose-03` `T60`, nishon 0.60, hold boshidan, har 0.5 s):

```
2.7s=0.015  3.2s=0.233  3.7s=0.473  4.2s=0.688  4.7s=0.917  5.2s=0.928
5.7s=0.920  6.2s=0.932  6.7s=0.938  7.2s=0.721  7.7s=0.476  8.2s=0.235
8.7s=0.043  9.2s=0.209  9.7s=0.439  10.2s=0.629 10.7s=0.891 11.2s=0.921
11.7s=0.898
```

Va `dose-02` `P1a` (nishon 0.30):

```
2.6s=0.001  3.1s=0.185  3.6s=0.400  4.1s=0.613  4.6s=0.891  5.1s=0.786
5.6s=0.581  6.1s=0.337  6.6s=0.089  7.1s=0.145  7.6s=0.283  8.1s=0.283
8.6s=0.270  9.1s=0.132  9.6s=0.090  10.1s=0.330 10.6s=0.412 11.1s=0.392
11.6s=0.352
```

**FAKT:** har ikki holatda tezlik **arra tishi** shaklida, davri ≈3–4 s,
amplitudasi **0.04 → 0.94**. Oraliq qiymatlar faqat **o'tish yo'lida**
uchraydi, plato sifatida emas.

**TALQIN:** `02` §3 ning «binar» topilmasi **o'z kuchida**. PI controller
`n > 0` qilganda `memory.current` `memory.high` dan oshadi va stall
**darhol to'yinish darajasiga (≈0.93) chiqadi**; controller `n = 0`
qilganda stall **nolga tushadi**. 2 s oynadagi **o'rtacha** istalgan
qiymatni bera oladi — va beradi (medianalar 0.000 / 0.281 / 0.702) —
lekin **oniy** tezlik amalda faqat ikki qiymat oladi. `02` §3 ning
«impuls + duty cycle o'rta bandni qaytaradi» yechimi **o'rtacha ma'noda
ishlaydi, oniy ma'noda ishlamaydi**, va duty cycle granularligi
(250 ms control tik'i, 2 s PSI oynasi, 4 MiB blok) bandni **uzluksiz**
ushlash uchun juda qo'pol.

**TALQIN — `02` §4 bilan taqqoslash: boshqarish ANCHA qo'polroq.**
`02` §4: *«Boshqarish qo'pol: tezlik 0.246–0.411 orasida tebranadi»*
(±0.08). Bu mashinada: **0.03–0.95** (±0.46), ya'ni **≈5.7× kengroq**.
`02` §4 ning «qabul qilinadi» bahosi bu mashinaga **ko'chirilmaydi**.
Bu **OQ-3**.

**CHEKLOV — nozikroq boshqarishni sinay olmadim.** `run_pi` ning
`kp = 12.0` va `ki = 3.0` koeffitsiyentlari `pressure.py` ning `main()`
da **CLI orqali ochilmagan**, demak ularni o'zgartirmasdan sinab
bo'lmaydi va kod o'zgartirish mening fayl egaligimdan tashqarida.
`step_mb = 2` (`base = 188`) sinaldi va u **over-doza** berdi (§3.6).
Shuning uchun: *«nozikroq blok yoki yumshoqroq PI koeffitsiyenti bandni
uzluksiz ushlay oladimi» — bu o'lchov bajarilmadi, sabab: kerakli
parametrlar CLI da yo'q va kod o'zgartirilmaydi.* Bu **OQ-4**.

### 3.6 FAKT — `base_mb > 184` over-doza beradi va guard'ni uradi

| epizod | `base_mb` | natija |
|---|---|---|
| `P2b` | **188** | **guard trip** `user_full_rate2s_runaway` `rate=0.9801961999065715` `limit=0.98` `window_us=2100001`, `kill_ok=True`; generator `status=9/KILL` (`Failed with result 'signal'`); `pressure_stop` **yozilmadi**; `memory.peak` 211.1 MiB |
| `P2c` | **196** | ramp **12.217 s** davom etdi (butun epizod), ramp tezligi `p50=0.9594 max=0.9907`, `ramp_above_threshold_s = 9.500 s`, HOLD fazasi **umuman bo'lmadi**; `memory.peak` 215.1 MiB |

**FAKT:** ikkisida ham `events max = 0` va `oom_kill = 0` — ya'ni
over-doza ham **OOM emas**, faqat to'yinish.

**TALQIN:** `base_mb` ning ishchi oynasi **tor**:

```
160 -> 0.0000        (breach yo'q)
176 -> 0.0138        (kichik overage)
182 -> 0.3871        (bitta epizod)
184 -> 0.223 .. 0.921  <-- ISHCHI QIYMAT (29 epizod)
188 -> to'yinish, guard trip
196 -> ramp hech qachon tugamaydi
```

Ya'ni **184 yagona o'lchangan ishlaydigan qiymat**, va u `02` §3 ning
qiymatiga **aynan teng**.

**FAKT — guard aynan loyihalanganidek ishladi.** `P2b` da `user@` ning
2 s tezligi 0.98 chegarasini kesdi va guard `cgroup.kill` ni yozdi;
generator SIGKILL bilan o'ldi; `memory.events oom_kill = 0` va
`/proc/vmstat oom_kill = 0`, ya'ni **guard o'ldirdi, kernel emas**.

---

## 4. 🔴 `ramp_above_threshold_s` va §9.4 invariant 2

`PREREGISTRATION.md` §9.4: *«`ramp_above_threshold_s` (ramp'ning quiescence
chegarasidan yuqori qismi) **pressure dosing kalibratsiyasidan olinadi**,
taxmin qilinmaydi.»* §21.7 esa `08` ning qiymatini rad etadi: *«`08` §11 uni
`0.000 s` deb o'lchagan, lekin **doza nol bo'lgan** konfiguratsiyada… nol
dozadagi qiymat kalibratsiya **emas**.»*

**O'lchov usuli.** Ramp fazasi `pressure.jsonl` dagi `pressure_start` dan
oxirgi `pressure_ramp` yozuvigacha (`mono_us` bo'yicha). Shu oyna ichida
`psi.csv` ning 10 Hz namunalaridan 2 s oynali `lab` `full` tezligi
hisoblanadi va `PREREGISTRATION.md` §8.4 ning **quiescence chegarasi 0.05**
dan yuqori namunalar sanaladi (bitta namuna = 0.1 s).

### 4.1 FAKT — HAQIQIY doza bilan o'lchandi

| `base_mb` | epizod | ramp davomiyligi | `>0.05` namunalar | **`ramp_above_threshold_s`** | erishilgan doza p50 |
|---|---|---|---|---|---|
| 160 (`P0`) | 2 | 0.683 s / 2.219 s | 0/6, 0/22 | **0.000 s** | 0.0000 |
| 176 | 1 | 1.332 s | 0/14 | **0.000 s** | 0.0138 |
| 182 | 1 | 2.565 s | 0/26 | **0.000 s** | 0.3871 |
| **184** | **29** | **2.553 – 2.614 s** | hammasi **0** | **0.000 s** (**29/29**) | **0.223 – 0.921** |
| 188 | 1 | 3.301 s | 6/33 | **0.600 s** | to'yinish |
| 196 | 1 | 12.217 s | 95/123 | **9.500 s** | to'yinish |

**FAKT:** `base_mb = 184` da — ya'ni **doza haqiqatan yetkazilgan**
konfiguratsiyada — `ramp_above_threshold_s` **29 epizoddan 29 tasida
aynan 0.000 s**. Ramp tezligi `min = p50 = max = 0.0000`, ya'ni ramp
quiescence chegarasiga **yaqinlashmadi ham**. Bu 4 xil nishonda
(0.30, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70) va 4 xil run'da takrorlandi.

> **Bu `08` §11 ning CHEKLOV'ini va `PREREGISTRATION.md` §21.7 ning
> e'tirozini YOPADI.** `08` 0.000 s ni nol dozada o'lchagan va
> «pilotga ko'chirilmaydi» deb belgilagan. Endi **aynan o'sha qiymat
> haqiqiy dozada o'lchandi**:
>
> ```
> ramp_above_threshold_s = 0.000 s
>   @ base_mb = 184, step_mb = 4, MemoryHigh = 192M, MemoryMax = 2G
>   29 epizod, 29/29, erishilgan doza p50 = 0.223 .. 0.921
> ```

**TALQIN — nega nol.** `02` §3 ning dizayni aynan shuni mo'ljallagan.
Ramp 46 ta 4 MiB blokni 0.05 s pauza bilan ajratadi (`run_pi` ning
`ramp_pause = 0.05`), demak `touched_mb` 184 ga **2.56 s** da yetadi va
`memory.current` `memory.high` ni faqat **oxirgi bloklarda** kesadi.
2 s oynadagi o'rtacha stall shuning uchun 0.05 dan past qoladi.
Generator overhead'i `memory.current` ni high'dan yuqoriga chiqarsa ham,
bu **ramp tugagandan keyin** sodir bo'ladi — va aynan shu hold
fazasining dozasi (§2.4).

### 4.2 FAKT — invariant 2 son bilan

`PREREGISTRATION.md` §9.4 invariant 2:

```
hold_s + ramp_above_threshold_s <= guard_sustain_s = 15 s
```

`hold_s = 12 s` (§9.4 invariant 1 ning `hold_cap_s`) da:

| band | `base_mb` | `ramp_above_threshold_s` | `hold_s + ramp` | `≤ 15 s`? | zaxira |
|---|---|---|---|---|---|
| **`P0`** | 160 | **0.000 s** | **12.000 s** | ✅ **HA** | **3.000 s** |
| **`P1`** | 184 | **0.000 s** | **12.000 s** | ✅ **HA** | **3.000 s** |
| **`P2`** | 184 | **0.000 s** | **12.000 s** | ✅ **HA** | **3.000 s** |
| (over-doza) | 188 | 0.600 s | 12.600 s | ✅ ha | 2.400 s |
| (over-doza) | 196 | 9.500 s | **21.500 s** | ❌ **YO'Q** | **−6.500 s** |

> **Invariant 2 kalibrlangan dial'da (`base_mb = 184`) UCHALA BAND uchun
> ham BAJARILADI, 3.000 s zaxira bilan.**

**TALQIN — nega bu zaxira katta.** Guard'ning `sustain_rate_threshold`
i 0.35 va `sustain_max_seconds` i 15.0 s. `ramp_above_threshold_s = 0`
bo'lgani uchun sustain taymeri **faqat hold ichida** boshlanishi mumkin,
va hold 12 s. Qolaversa arra tishi tezlikni 0.35 dan pastga muntazam
tushiradi (§3.5), demak taymer **qayta tiklanadi**. O'lchov buni
tasdiqlaydi: `base_mb=184` ning **29 epizodida `sustained_pressure`
trip'i YO'Q** (§8.2). Ya'ni `08` §3.5 ning *«butun xavf `P2` da»*
TALQIN'i to'g'ri, lekin **kalibrlangan** `P2` ham trip qilmaydi.

**CHEKLOV — `hold_s = 12 s` sinalmadi.** Mening epizodlarim
`max_seconds = 12 s` bo'lgan **ramp + hold** yig'indisi, demak haqiqiy
hold ≈9.5 s (§1.4). `ramp_above_threshold_s = 0.000 s` ramp fazasining
xususiyati va u hold uzunligiga bog'liq **emas**, shuning uchun
invariant 2 ning arifmetikasi `hold_s = 12 s` uchun ham o'z kuchida.
Lekin **`ramp_s = 5 s` + `hold_s = 12 s` = 17 s li epizod bu hujjatda
o'lchanmadi, sabab: topshiriqning xavfsizlik qoidasi epizodni ≤12 s
bilan cheklaydi** (OQ-5). Uzunroq hold'da arra tishi ko'proq davr
beradi, demak `sustained_pressure` xavfi **oshmaydi** — lekin bu
TALQIN, o'lchov emas.

---

## 5. 🔴 Epizod chegarasi — `08` §5 ning nuqsoni TUZATILGAN

`08` §5 ning o'lchovi: `--max-seconds 5` + `RuntimeMaxSec=7s` berilgan
epizod `lab` scope'da 0.35 chegarasidan yuqorida **16.3 s** turdi, ya'ni
**11.3 s oshib ketish**, va uni to'xtatgan narsa faqat guard'ning
`cgroup.kill` i bo'ldi. `PREREGISTRATION.md` §21.7 shuning uchun **GATE**
qo'ygan: *«Generator §9.4 ning ikki invariantini majburlamaguncha hech
qanday pilot trial o'tkazilmaydi.»*

`revix/pressure.py` **`08` yozilganidan keyin o'zgargan**: `Deadline`
sinfi qo'shilgan va u **har sahifaga tegishdan OLDIN** tekshiriladi
(`Allocator._touch`, `retouch`, `churn`), **`run_ramp` va `run_pi`
ikkisida ham**; `_finish` endi `max_seconds` va `overrun_s` ni **yozadi**.

### 5.1 FAKT — o'lchangan `overrun_s`

Hamma joyda `--max-seconds 12.0`, `RuntimeMaxSec=14s`.

| run | epizod | `pressure_stop` yozdi | `overrun_s` min | p50 | max |
|---|---|---|---|---|---|
| `dose-01-dial` | 3 | 3 | 0.0563 | 0.0579 | 0.0614 |
| `dose-02-bands` | 6 | **5** | 0.0517 | 0.0617 | **0.2899** |
| `dose-03-p2sweep` | 6 | 6 | 0.0606 | 0.0654 | 0.0967 |
| `tstart-P1` | 6 | 6 | 0.0588 | 0.0617 | **0.1766** |
| `tstart-P2` | 6 | 6 | 0.0606 | 0.0619 | 0.0946 |
| `dprobe-P1` | 4 | 4 | 0.0615 | 0.0711 | 0.0839 |
| `dprobe-P2` | 4 | 4 | 0.0597 | 0.0617 | 0.0631 |
| **JAMI** | **35** | **34** | **0.0517** | **0.0619** | **0.2899** |

```
overrun_s: n=34  min=0.0517  p50=0.0619  p90=0.0960  p99=0.2525
                 max=0.2899  mean=0.0764
HAMMASI <= 0.3 s ?  HA
```

**FAKT — bitta epizod `pressure_stop` yozmadi:** `dose-02-bands` ning
`P2b` si (`base_mb=188`), chunki **guard uni SIGKILL bilan o'ldirdi**
(§3.6). Bu overrun **emas** — bu guard'ning to'g'ri ishlashi.

**FAKT:** eng katta overrun (**0.2899 s**) `base_mb=196` epizodida —
ya'ni ramp butun 12 s ni egallagan, to'yingan, maksimal throttling
holatda. Kalibrlangan `base_mb=184` da max **0.1766 s**, p50 **0.0617 s**.

> **TALQIN — `08` §5 ning topilmasi RAD ETILDI va `TESTING.md` §3 ning
> xavfsizlik da'vosi TIKLANDI.** 11.3 s oshib ketish **0.052–0.290 s**
> ga tushdi, ya'ni eng yomon holat bo'yicha **39.0× kichraydi**
> (`11.3 / 0.2899`). Epizodni to'xtatgan narsa **generatorning o'z
> `--max-seconds` i**, guard emas: 35 epizoddan 34 tasi `pressure_stop`
> yozdi va `Result=success` bilan tugadi. `SECURITY.md` §2 ning
> qatlamli himoyasi **tiklandi** — endi epizod chegarasi guard'ning
> to'g'ri ishlashiga **tayanmaydi**.

**TALQIN — qoldiq oyna aynan modul izohi aytganidek.** `pressure.py` ning
izohi halol bayon qiladi: *«bitta sahifaga tegish (bitta page fault)
boshlangandan keyin uni foydalanuvchi fazosidan uzish MUMKIN EMAS…
epizod chegarasi `max_seconds + bitta uzilmas page fault` bo'ladi…
Haqiqiy oshib ketish har epizodda `pressure_stop.overrun_s` da QAYD
ETILADI, demak u endi taxmin emas, o'lchov bo'ladi.»* O'lchangan qoldiq
oyna **0.0517–0.2899 s**. Bu **kafolat emas, chegara** — lekin u endi
**taxmin emas, 34 namunali o'lchov**.

**TALQIN — §21.7 ning GATE sharti bajarildi.** Gate ikki invariantni
talab qiladi: invariant 1 (`hold_s ≤ 12 s`) — o'lchangan oshib ketish
≤ **0.2899 s** (kalibrlangan dial'da ≤ **0.1766 s**); invariant 2
(`hold + ramp_above_threshold_s ≤ 15 s`) — o'lchangan
**12.000 ≤ 15 s** (§4.2). **Ikkisi ham bajarildi.** Gate'ni rasman
yopish frozen matn egasining qarori; men faqat o'lchovni beraman.

---

## 6. ⭐ `t_start` — kalibrlangan dozada

### 6.1 Ta'rif va metod (`08` §15 bilan AYNAN bir xil)

```
t_start = ActiveEnterTimestampMonotonic − InactiveExitTimestampMonotonic
```

ya'ni start job boshlanishidan `READY=1` systemd tomonidan qabul
qilinishigacha. Mustaqil o'zaro tekshiruv: SUT ning o'z `INFO` javobidagi
`uptime_us = mono_us() − g_start_us` (`revix/sut.c:612`, `812`), ya'ni
`main()` **ichida** o'lchangan vaqt.

SUT ext4 nusxada qurildi (`make -C revix all`, `cc (Debian 14.3.0-5)
14.3.0`, `-O2 -Wall -Wextra -Werror -std=c11 -pthread`). Har start:

```
$ systemd-run --user --slice=revixlab.slice --unit=revix-sut --collect \
    --working-directory=$HOME/revix-work \
    --property=Type=notify --property=NotifyAccess=main \
    --property=MemoryMax=256M --property=MemorySwapMax=0 --property=TasksMax=64 \
    --property=TimeoutStartSec=10s --property=StartLimitBurst=0 \
    --property=Restart=no \
    --setenv=REVIX_SUT_SOCKET=<sock> --setenv=REVIX_SUT_RATE_HZ=2000 \
    $HOME/revix-work/revix/sut
```

Guard **birinchi** ishga tushdi va **oxirgi** to'xtadi. `P0` da generator
**umuman ishga tushirilmadi** (`PREREGISTRATION.md` §9.3 ning «generator
idle» sharti, `08` §15.1 bilan taqqoslanadigan qilish uchun).

**Tasniflash (`08` §15.2 bilan bir xil):** namuna **PRESSURED** deb
sanaladi faqat `lab` slice'ning `full total=` hisoblagichi shu start'ning
oldi va orqa o'qishi orasida **haqiqatan oshgan** bo'lsa. `avgN`
ishlatilmaydi. `P1` va `P2` ning **48 namunasidan 48 tasi** shu mezon
bo'yicha PRESSURED (eng kichik `total_delta` = 30 208 µs).

### 6.2 FAKT — natijalar, band bo'yicha

| band | erishilgan doza (epizod medianalari) | n | start **BO'LMADI** | min | **p50** | **p90** | **p99** | max | `≤0.8 s` |
|---|---|---|---|---|---|---|---|---|---|
| **`P0`** (generator yo'q) | 0.0000 | **30** | **0** | 0.0237 | **0.0386** | **0.0481** | 0.0555 | 0.0576 | **30/30** |
| **`P1`** (kalibrlangan) | 0.2303 – 0.3892 | **24** | **0** | 0.0555 | **0.5041** | **0.9543** | 1.3948 | 1.4807 | **19/24** |
| **`P2`** (kalibrlangan) | 0.5726 – 0.7094 | **24** | **0** | 0.3154 | **0.5727** | **0.7863** | 1.1211 | 1.1883 | **22/24** |
| **`P1 + P2`** (birlashtirilgan) | — | **48** | **0** | 0.0555 | **0.5611** | **0.9105** | 1.3433 | 1.4807 | **41/48** |

Barcha **78 urinish**: `rc=0`, `ActiveState=active`, `SubState=running`,
`Result=success`, har birida **boshqa `InvocationID`** (30 / 24 / 24
alohida invocation). `natijalar: Counter({('active', 'running',
'success'): 30})` / `({… : 24})` / `({… : 24})`.

`P0` da `pre_full_avg10` oralig'i `0.0 .. 0.0`; `P1` da `0.0 .. 18.41`;
`P2` da `0.0 .. 19.37`.

**FAKT — start muvaffaqiyatsizligi 0/78.** `08` §15.2 da 6/14 (43%)
va §15.3 da 1/7 (14%, guard'ga tegishli) edi. Kalibrlangan dozada
**birorta start muvaffaqiyatsiz bo'lmadi** va `TimeoutStartSec=10s`
**birorta marta ham oshib ketmadi** (eng katta `t_start` **1.4807 s**,
chegaradan **6.8× kichik**).

### 6.3 🔴 FAKT — `08` bilan yonma-yon: nuqsonning kattaligi 6.76× dan 0.98× ga tushdi

| o'lchov | `08` §15.3 (nazoratsiz ramp, to'yinish) | **bu hujjat (kalibrlangan `P2`)** |
|---|---|---|
| doza | **nazoratsiz**, `lab full avg10` 33.98–70.02, to'yinish ≈0.999 | **kalibrlangan**, epizod medianalari 0.5726–0.7094 |
| n (pressured) | 6 (+1 guard kill) | **24** |
| start bo'lmadi | 1/7 (14%, guard'ga tegishli) | **0/24** |
| `t_start` p50 | 2.8308 s | **0.5727 s** |
| **`t_start` p90** | **5.4042 s** | **0.7863 s** |
| `t_start` p99 | 7.1958 s | **1.1211 s** |
| `≤ 0.8 s` | **0/6** | **22/24** |
| budjetga nisbati (`p90 / 0.8`) | **6.76×** | **0.98×** |

**FAKT:** p90 **5.4042 s → 0.7863 s**, ya'ni **6.87× kichraydi**.
p99 **7.1958 s → 1.1211 s** (6.42× kichraydi). max **7.1958 s →
1.1883 s**.

**TALQIN:** `08` §15.5 ning CHEKLOV'i (*«pressured bandda n kichik va bu
nazoratlangan doza emas — `MODE=ramp` to'yinishga chiqadi»*) va
`PREREGISTRATION.md` §21 ning «yuqori baho» belgisi **ikkisi ham
to'g'ri edi**. O'lchov buni **miqdoriy** qiladi: nazoratsiz to'yinish
`t_start` ni kalibrlangan `P2` dozasiga nisbatan **≈6.9×** cho'zadi.
`08` ning 5.4042 s i **noto'g'ri emas — u boshqa dozaning qiymati**.

### 6.4 FAKT — kechikish SUT ning ICHIDA emas: TASDIQLANDI

| band | SUT `uptime_us` p50 | p90 | max | `t_start` p50 | **SUT TASHQARISIDA** | ulush |
|---|---|---|---|---|---|---|
| `P1` | **0.0151 s** | 0.0968 | 0.1416 | 0.5041 s | **0.4890 s** | **97.0%** |
| `P2` | **0.0152 s** | 0.1367 | 0.1495 | 0.5727 s | **0.5575 s** | **97.3%** |

`P1`: `uptime_us` n=24, min 0.0123. `P2`: n=24, min 0.0134.

> **TALQIN — `08` §15.2 ning xulosasi va `PREREGISTRATION.md` §21.5 ning
> «bir yo'l yopiladi» bandi KALIBRLANGAN DOZADA TASDIQLANDI.**
> `t_start` ning **97.0–97.3%** i SUT `g_start_us` ni olishidan
> **oldin** ketadi: `execve`, dinamik yuklash va reclaim throttling
> ostidagi birinchi page fault'lar. Ya'ni **SUT ni tezlashtirish
> nuqsonni tuzatmaydi** — §21.5 ning bayonoti bu dozada ham o'z
> kuchida, va u O1–O4 dan qochish yo'lini **olib tashlaydi**.
> Bu `PREREGISTRATION.md` §9.2 ning (i) va (iv) mexanizmlarini
> qo'llab-quvvatlaydi.

**CHEKLOV — `P0` da SUT uptime o'lchanmadi.** `tstart-P0` run'ida `INFO`
so'rovi `SOCK_STREAM` bilan yuborildi, SUT esa `SOCK_SEQPACKET`
eshitadi (`sut.c:775`), demak javob olinmadi. Xato keyingi run'lardan
oldin tuzatildi. **`P0` uchun SUT uptime o'lchovi bajarilmadi, sabab:
asbobning socket turi xato edi.** `t_start` ning o'zi bunga bog'liq
emas (u systemd timestamp'laridan olinadi) va `P0` ning 30 namunasi
yaroqli.

### 6.5 🔴 §17.2 / §17.5 ning qaror qoidasi — raqam bilan

Muzlatilgan qoida (`PREREGISTRATION.md` §17.5, *«Qaror uchun zarur, lekin
MAVJUD BO'LMAGAN o'lchov»*):

> *«`p90(t_start) ≤ 0.8 s` bo'lsa — nuqson amalda bezarar va O1–O4 kerak
> emas. Aks holda loyiha egasi O1–O4 dan birini tanlashi **shart**, va bu
> tanlov **birinchi pilot trial'idan oldin** qilinishi kerak.»*

`08` §15.1 ning arifmetikasi (§17.2): `RestartSec` 0.1 + `t_start` +
probe kvantlashi 0.1 ≤ 1 s ⇒ `t_start ≤ 0.8 s`.

| band | **`p90(t_start)`** | budjet | zaxira | `≤0.8 s` | qoidaning javobi |
|---|---|---|---|---|---|
| `P0` | **0.0481 s** | 0.8 s | **16.65×** | 30/30 | ✅ qaror **kerak emas** |
| `P1` | **0.9543 s** | 0.8 s | **0.84×** | 19/24 | ❌ qaror **KERAK** |
| **`P2`** | **0.7863 s** | 0.8 s | **1.02×** | 22/24 | ✅ qaror **kerak emas** |
| **`P1 + P2`** | **0.9105 s** | 0.8 s | **0.88×** | 41/48 | ❌ qaror **KERAK** |

**FAKT:** `P2` da `p90 = 0.7863 s`, budjetdan **0.0137 s** (1.7%)
kichik. `P1` da `p90 = 0.9543 s`, budjetdan **0.1543 s** (19.3%) katta.
Birlashtirilgan 48 namunada `p90 = 0.9105 s`, budjetdan **13.8%** katta.

**FAKT:** `≤ 0.5 s` budjeti (agar harakat `F_probe` ga gate qilinsa,
`+D_f = 300 ms` ⇒ `t_start ≤ 0.5 s`): `P0` **30/30**, `P1` **11/24**,
`P2` **9/24**.

> **TALQIN — halol javob: `08` ning HALOKATI rad etildi, lekin nuqson
> YOPILMADI.**
>
> 1. **Rad etilgan narsa.** `PREREGISTRATION.md` §21.5 ning
>    *«budjetdan 6.8× katta… ikki mustaqil o'lchovda budjet ichida
>    **bitta ham** urinish yo'q»* bayonoti kalibrlangan dozada
>    **noto'g'ri**. Kalibrlangan `P2` da 24 urinishdan **22 tasi**
>    budjet ichida, `P1` da 24 dan **19 tasi**. Pilot «har bir `P2`
>    trial'ida oyna pressure'dan chiqib ketadi» degan holatda **emas**.
> 2. **Yopilmagan narsa.** Muzlatilgan qoida `P2` da «qaror kerak emas»
>    deydi, lekin **1.7% zaxira bilan**; `P1` da qoida **buziladi**
>    (0.84×); birlashtirilganda ham **buziladi** (0.88×).
>    `PREREGISTRATION.md` §9.3 `P1` ni **to'laqonli yacheyka** qiladi
>    (3 × 2 × 20 dizaynining uchdan biri), demak `P1` da buzilgan
>    invariant butun dizaynni qamrab oladi.
> 3. **`P1` ning p90 i `P2` dan YUQORI** (0.9543 > 0.7863) — ya'ni
>    monotonlik buzilgan. Bu `n = 24` da bu farqning **o'lchov
>    shovqini ichida** bo'lishini ko'rsatadi: §3.5 ga ko'ra ikki band
>    ham bir xil arra tishida 0.03–0.95 oralig'ida tebranadi, demak
>    start lahzasining oniy stall'i bandga emas, **arra tishining
>    fazasiga** bog'liq. `P2` ning 1.7% zaxirasi shu shovqindan
>    **kichik**.
>
> **Shuning uchun men qoidani «bajarildi» deb yopmayman.** Qoidaning
> **harfi** `P2` da bajarildi; qoidaning **maqsadi** —
> *«nuqson amalda bezarar»* — **bajarilmadi**, chunki `P1` yacheykasi
> budjetdan chiqadi va `P2` ning zaxirasi shovqindan kichik.
> **Qaror loyiha egasiniki.** Men O1–O4 dan birini tanlamayman:
> har biri muzlatilgan ta'rifga tegadi.
>
> **Qo'shimcha, qarorni ARZONLASHTIRADIGAN o'lchangan fakt:**
> `PREREGISTRATION.md` §17.5 O3 ni (`hold_cap_s` ni 12 s dan oshirish)
> *«yagona variant hech bir ilmiy da'voni kuchsizlashtirmaydigan»* deb
> belgilagan, lekin u §9.4 invariant 2 ning **qayta tekshirilishini**
> va guard'ning **qayta kalibratsiya qilinishini** shart qilgan. Bu
> hujjat o'sha tekshiruvni **bajardi**: `ramp_above_threshold_s =
> 0.000 s` (§4.1), demak `hold_cap_s` ni **15 s gacha** oshirish
> invariant 2 ni buzmaydi (`15 + 0.000 = 15 ≤ 15`) va guard'ning
> `sustain_max_seconds = 15.0` i **o'zgartirilishi kerak emas**.
> Bu O3 ning **narxini pasaytiradi** — lekin tanlovni **men
> qilmayman**.

**CHEKLOV — n kichik.** Har bandda n=24 (6 epizod × 4 start), `P0` da
n=30. `p99` n=24 da amalda `max` ga yaqin, demak u **taqsimot bahosi
emas**.

**CHEKLOV — start lahzasidagi ONIY stall yozilmadi.** Faqat start
oynasidagi `total=` deltasi yozildi (tasniflash uchun). Shuning uchun
`t_start` ning oniy dozaga **regressiyasi o'lchanmadi, sabab: buning
uchun start'larni arra tishining fazasiga qasddan sinxronlash kerak va
bu dozalash kalibratsiyasining qamrovidan tashqarida.** Bu **OQ-6** va
u §6.5 ning 3-bandidagi TALQIN'ni **o'lchov bilan tasdiqlanmagan**
qoldiradi.

**CHEKLOV — oraliq dozalar o'lchanmadi.** `t_start` faqat 0.0000,
≈0.28 va ≈0.70 dozalarida o'lchandi. `08` ning ≈0.999 dozasidagi
5.4042 s i bilan birga bu uch nuqta **chiziqli bo'lmagan** javobni
ko'rsatadi (`t_start` faqat to'yinishga yaqin dozada portlaydi), lekin
**0.80–0.95 oralig'ida `t_start` o'lchanmadi**, demak egri chiziqning
shakli **TALQIN**, o'lchov emas.

---

## 7. `D_probe` — uchala kalibrlangan bandda

### 7.1 Metod (`08` §16 bilan bir xil, bitta tuzatish bilan)

O'lchanadigan kattalik (`08` §16 ning o'z ta'rifi): *oxirgi
contract-passing probe'dan **restartdan keyingi** birinchi contract-passing
probe'gacha*, 10 Hz probe kadensida. `W_stab` tasdiqlash sharti
**kiritilmagan**, demak bu `D_probe` ning **pastki chegarasi** — haqiqiy
`D_probe` bundan kichik bo'lishi mumkin emas.

Asbob: loyihaning **o'z** prober'i (`revix/prober.py`), 10 Hz,
`revixmon.slice` da, `--target sut=<socket>`. SUT **arm A** sifatida
(`PREREGISTRATION.md` §9.3): `Type=notify`, `Restart=on-failure`,
`RestartSec=100ms`, `StartLimitBurst=0`, `TimeoutStartSec=10s`
(jonli unit'dan tasdiqlangan). Fault protokolning **o'zi** orqali:
`FAULT exit code=1`, har bandda **12 injeksiya**, har 3 s da. Har
injeksiya `OK armed=exit` javobini oldi.

**Tuzatish (`08` §16 da yo'q va u YERDA kerak emas edi).** `08` har
`ok → non-ok → ok` o'tishini bitta epizod deb sanagan va `P0` da bu
to'g'ri. Pressure ostida bu **xato**: pressure SUT'ni o'ldirmasdan ham
contract'ni buzadi (`rt_timeout`, band `b_response`), va bunday epizod
`D_probe` **emas** — u `PREREGISTRATION.md` §9.2 ning **(iii) brownout**
yo'li. Shuning uchun epizodni **`invocation_id` o'zgarishi** bo'yicha
tasnifladim: o'zgargan → restart (haqiqiy `D_probe`), o'zgarmagan →
brownout.

### 7.2 FAKT — natijalar, band bo'yicha

| band | probe namunasi | `outcome` taqsimoti | alohida `invocation_id` | `NRestarts` | uzilish epizodi | **restart** | brownout |
|---|---|---|---|---|---|---|---|
| **`P0`** | 410 | `ok` 386, `conn_refused` 24 | **13** | **12** | 12 | **12** | **0** |
| **`P1`** | 1351 | `ok` 1252, `conn_refused` 86, `rt_timeout` 12, `bad_response` 1 | **13** | **12** | 16 | **12** | **4** |
| **`P2`** | 1345 | `ok` 1230, `conn_refused` 95, `rt_timeout` 20 | **13** | **12** | 16 | **12** | **4** |

`13 alohida invocation_id = 1 boshlang'ich + 12 restart` — uchala bandda
ham **injeksiya soni bilan aynan mos**.

**`D_probe` proxy (faqat restart epizodlari, har bandda n=12):**

| band | min | **p50** | **p90** | **p99** | max | **mean** | `P` birligida (p50) | buzilgan probe (p50) |
|---|---|---|---|---|---|---|---|---|
| **`P0`** | 0.300 | **0.300** | 0.300 | 0.300 | 0.300 | **0.3000** | 3.0 × P | 2 |
| **`P1`** | 0.300 | **0.900** | 1.090 | 1.634 | 1.700 | **0.8500** | 9.0 × P | 8 |
| **`P2`** | 0.500 | **1.000** | 1.550 | 2.134 | 2.200 | **1.0250** | 10.0 × P | 9 |

Barcha epizodlar:

```
P0: [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3]
P1: [1.0, 1.7, 0.3, 1.0, 0.5, 1.0, 0.9, 0.4, 0.9, 0.9, 1.1, 0.5]
P2: [1.0, 1.0, 1.1, 2.2, 1.6, 0.7, 1.0, 0.7, 0.7, 0.8, 0.5, 1.0]
```

**FAKT — `P0` da taqsimot degenerat:** 12 epizodning **hammasi aynan
0.300 s** (3 probe periodi, 2 buzilgan probe). Barcha buzilishlar
`conn_refused` / band `a_conn` — socket yo'q bo'lgan vaqt;
`c_progress` **nol marta**.

**TALQIN — doza `D_probe` ni ≈3.4× cho'zadi.** `P0` 0.300 s →
`P1` 0.900 s → `P2` 1.000 s (p50 bo'yicha), ya'ni restartdan keyin
xizmatning qaytishi pressure ostida **sezilarli sekinlashadi**. Bu
§6 ning `t_start` o'lchovi bilan **mustaqil ravishda mos**:
`t_start` p50 0.0386 → 0.5041 → 0.5727, va `D_probe` ning ortishi
(0.600 va 0.700 s) `t_start` ning ortishi (0.466 va 0.534 s) bilan
bir xil tartibda. Ya'ni `D_probe` ning o'sishi asosan **`t_start` ning
o'sishi**, `RestartSec` yoki probe kvantlashi emas.

### 7.3 TALQIN — `08` §16 bilan taqqoslash

`08` §16 `P0` da p50 = **0.500 s** (5 × P, 3–4 buzilgan probe)
o'lchagan; men **0.300 s** (3 × P, 2 buzilgan probe) o'lchadim.

**TALQIN:** bu mashinada uzilish `08` dan **qisqaroq**. Komponentlar
bo'yicha: `RestartSec` 0.100 + `t_start` p50 **0.0386** (§6.2; `08` da
0.0394) + systemd job overhead ≈ 0.15 s, ustiga probe gridining
`±P` kvantlashi → 0.3 s. `08` ning 0.500 s i bilan farq **bitta-ikkita
probe periodi**, ya'ni asbobning kvantlash poli ichida. Ikki o'lchov
**bir-biriga zid emas**; `08` §16.1 ning *«o'lchangan qiymatning
yarmidan ko'pi asbobning kvantlashi»* TALQIN'i **tasdiqlanadi** va
mening qiymatim unga **yaqinroq pol** beradi.

### 7.4 FAKT — brownout: §9.2 (iii) ning O'LCHANGAN izi

| band | brownout epizodi | davomiyligi (s) | buzilgan band |
|---|---|---|---|
| `P0` | **0** | — | — |
| `P1` | **4** | 0.5, 0.2, 0.4, 0.2 | **`b_response`** |
| `P2` | **4** | 0.2, 0.2, 0.2, 0.2 | **`b_response`** |

**FAKT:** `P0` da **birorta** brownout epizodi yo'q; `P1` va `P2` da
**har birida 4 ta**. Buzilgan band hamma joyda **`b_response`**
(`rt_timeout`: javob vaqti `T_rt` dan oshdi), **`a_conn` emas** — ya'ni
SUT **tirik va socket ochiq**, lekin javob kechikdi. `invocation_id`
**o'zgarmadi**, demak restart bo'lmadi.

> **TALQIN:** bu `PREREGISTRATION.md` §9.2 ning **(iii) mexanizmi**
> (*«start bo'ldi lekin throughput < θ·R_ref — brownout»*) ning
> **bevosita o'lchangan izi**, va §9.2 uni *«eng ehtimoliy signal
> manbasi»* deb belgilagan. §4 ning `contract_fail` invalidator'iga
> bevosita tegadi: `W_stab` oynasi ichida tushgan bunday 0.2 s li
> brownout **butun VR ni invalidatsiya qiladi**, holbuki SUT
> o'lmagan ham, restart ham bo'lmagan.
>
> **Bu hujjat brownout'ni TAHLIL QILMAYDI** — u fault injeksiyasining
> yon mahsuli sifatida kuzatildi, maqsadli o'lchanmadi. Bu **OQ-9**.

### 7.5 FAKT — §11 / §18.6 ning fail-slow chegarasi

`agent/research` ning qoidasi (`08` §16.2): agar
`thr = 0.20 × RMST(P0)` taxminan `5 × P` (≈500 ms) yoki undan katta
bo'lsa, cheklov amalda zararsiz.

| band | referens | qiymat | `thr = 0.20 × referens` | `P` birligida | `≥ 5P`? |
|---|---|---|---|---|---|
| **`P0`** | `mean` | 0.3000 s | **0.0600 s** | **0.60 × P** | ❌ **YO'Q** |
| `P0` | `p50` | 0.3000 s | 0.0600 s | 0.60 × P | ❌ YO'Q |
| `P0` | `p90` | 0.3000 s | 0.0600 s | 0.60 × P | ❌ YO'Q |
| **`P1`** | `mean` | 0.8500 s | **0.1700 s** | **1.70 × P** | ❌ **YO'Q** |
| `P1` | `p90` | 1.0900 s | 0.2180 s | 2.18 × P | ❌ YO'Q |
| **`P2`** | `mean` | 1.0250 s | **0.2050 s** | **2.05 × P** | ❌ **YO'Q** |
| `P2` | `p90` | 1.5501 s | 0.3100 s | 3.10 × P | ❌ YO'Q |

> **FAKT: chegara UCHALA bandda ham `5P` dan kichik**, eng katta
> qiymat `p90(P2)` da **3.10 × P**. Demak `PREREGISTRATION.md` §18.6
> ning qarori **KERAK**, va bu xulosa **bandga bog'liq emas** —
> ya'ni `08` §16.2 va §21.3 ning hukmi **kalibrlangan dozalarda ham
> o'z kuchida**, qolaversa **kuchayadi** (`P0` da chegara `08` ning
> 0.0967 s idan ham kichik: **0.0600 s**).

**CHEKLOV — `RMST(P0)` mening proxy'im EMAS.** `08` §16.2 ning
CHEKLOV'i o'z kuchida: `PREREGISTRATION.md` §10.2 ning `RMST` i
time-to-VR ning Kaplan–Meier egri chizig'idan `τ` gorizontigacha
hisoblanadi, va time-to-VR ta'rifi `W_stab` tasdiqlash oynasini o'z
ichiga olsa (`W_stab_pilot = 8 s`), haqiqiy `RMST(P0)` ≈ **8.3 s**
bo'lardi va `thr ≈ 1.66 s ≥ 5P` — ya'ni **xulosa teskari bo'lardi**.
Bu `08` §12 **OQ-12** ning javobiga bog'liq;
`PREREGISTRATION.md` §21.2 OQ-12 ni **rad etgan** va §18.3 ni o'z
kuchida qoldirgan. **Men bu masalani hal qilmayman** — men bergan
raqam `D_probe` ning o'zi, ya'ni `08` §16 va `agent/research` ning
derivatsiyasida ishlatilgan kattalik.

### 7.6 FAKT — probe narxi (`PREREGISTRATION.md` §8.2 / §22)

`prober_stop` yozuvining `cost` bloki (`--report-cost`):

| band | `probes` | `cpu_total_s` | **`core_percent`** | budjet | `budget_exceeded` | `cpu_us_per_probe` | `max_rss_kb` | `overruns` | `skipped_cycles` |
|---|---|---|---|---|---|---|---|---|---|
| `P0` | 410 | 0.121671 | **0.2968%** | 1.0% | **false** | 296.76 | 17024 | 0 | 0 |
| `P1` | 1351 | 0.359790 | **0.2663%** | 1.0% | **false** | 266.31 | 16980 | 0 | 0 |
| `P2` | 1345 | 0.391987 | **0.2901%** | 1.0% | **false** | 291.44 | 16988 | **1** | **6** |

**FAKT:** `budget_exceeded: false` uchala bandda; `core_percent`
**0.2663–0.2968%**, ya'ni 1.0% budjetdan **3.4–3.8× kichik**.
`00` §1 ning *«Prober CPU'si yadro foizida o'lchanadi; >1% bo'lsa
sekinlashtiriladi»* sharti bajarildi.

**FAKT — `P2` da prober o'zi kechikdi:** `overruns = 1`,
`skipped_cycles = 6`. `P0` va `P1` da ikkisi ham **0**.

> **TALQIN:** prober `revixmon.slice` da (`MemoryMax=128M`, sibling)
> ishlasa ham, `P2` dozasi uni **6 tsiklda o'tkazib yuborishga**
> majbur qildi. Bu `PREREGISTRATION.md` §22.3 ning *«probe narxi
> arm'lar bo'yicha BIR XIL EMAS»* topilmasining **pressure bandlari
> bo'yicha analogi**: `skipped_cycles` `P0`/`P1` da 0, `P2` da 6.
> O'tkazib yuborilgan tsikl `probe_sample` qatorining **yo'qolishi**,
> va §14.6 ning `seq` bo'shliq invariantі aynan shuni tutadi.
> **Bu hujjat uning statistik ta'sirini tahlil qilmaydi** — bu
> §22 ning masalasi.

---

## 8. Guard — birinchi, oxirgi, fail-closed

### 8.1 FAKT — guard har run'da birinchi ishga tushdi va tiriklik tasdiqlandi

Har run'da tartib: `teardown` → `marker-pre` → `units.preflight()` →
`set-property` → `verify_kernel_props` → **guard** → tiriklik tekshiruvi →
`sampler` → watcher → baza → epizodlar → `sampler`/`guard` to'xtashi →
`marker-post` → `teardown` → `clear_runtime_drop_ins()`.

Runner'ning fail-closed sharti:

```bash
systemctl --user --quiet is-active revix-guard.service || {
  echo "ABORT (FAIL-CLOSED): guard ishga tushmadi -> hech narsa boshlanmaydi"
  teardown_slices; exit 1; }
```

**FAKT:** 9 run'dan 9 tasida guard ishga tushdi va tasdiqlandi
(`guard FAOL`). ABORT **birorta marta ham yuzaga kelmadi**, demak
**hech qanday epizod, hech qanday SUT start'i va hech qanday injeksiya
guard'siz ishlamadi**.

**FAKT — pre-flight har run'da toza** (loyihaning o'z tekshiruvchisi):

```
{"clean": true, "problems": [], "units": [], "cgroups": [],
 "stale_drop_ins": [], "unit_patterns": ["revix-*"],
 "slices": ["revixlab.slice", "revixmon.slice"]}
```

### 8.2 FAKT — bitta trip, 35 epizod bo'yicha

| run | `guard_event` | sabab | o'lchangan qiymat | `kill_ok` | `guard_stop` |
|---|---|---|---|---|---|
| `dose-01-dial` | 0 | — | — | — | `tripped=false iterations=1200 elapsed_s=120.000237` |
| **`dose-02-bands`** | **1** | `user_full_rate2s_runaway` | `rate=0.9801961999065715` `limit=0.98` `window_us=2100001` | **true** | `tripped=true iterations=2160 elapsed_s=216.000166` |
| `dose-03-p2sweep` | 0 | — | — | — | `tripped=false iterations=2160 elapsed_s=216.000157` |
| `tstart-P0` | 0 | — | — | — | `tripped=false iterations=72 elapsed_s=7.200152` |
| `tstart-P1` | 0 | — | — | — | `tripped=false iterations=1995 elapsed_s=199.500187` |
| `tstart-P2` | 0 | — | — | — | `tripped=false iterations=1989 elapsed_s=198.900249` |
| `dprobe-P0` | 0 | — | — | — | `tripped=false iterations=429 elapsed_s=42.900122` |

Chegaralar har run'da `guard_start` ga yozilgan va **o'zgartirilmagan**:

```
{'sustain_rate_threshold': 0.35, 'sustain_max_seconds': 15.0,
 'user_full_avg10_max': 85.0, 'user_some_avg10_max': 90.0,
 'user_full_rate2s_max': 0.98, 'host_mem_available_min_kb': 1500000}
```

`trip_summary` (`08` §17 ning tuzatishi bilan qo'shilgan maydon):

```
trip_summary=[{"reason": "user_full_rate2s_runaway", "kill_ok": true,
               "trips": 1, "suppressed_records": 0}]
```

**FAKT:** yagona trip **over-doza** epizodida (`base_mb=188`) bo'ldi
(§3.6). `window_us=2100001` — ya'ni `02` §2 ning tuzatgan xatosi
(oyna 2–8 s orasida suzishi) **qaytmagan**: oyna eng tor ≥2 s
(2.100001 s, 10 Hz namuna qadami hisobiga).

**FAKT — kalibrlangan dial'da (`base_mb=184`) 29 epizod bo'yicha trip
YO'Q.** `sustained_pressure` (0.35 dan yuqorida 15 s) birorta marta ham
ishga tushmadi — chunki epizod 12 s va arra tishi tezlikni 0.35 dan
pastga muntazam tushiradi (§3.5, §4.2).

> **TALQIN:** bu `08` §3.5 ning TALQIN'ini **ikki tomondan**
> tasdiqlaydi: `P1` trial'i guard'ni trip qila olmaydi, **va**
> kalibrlangan `P2` ham trip qilmaydi. `08` §14.3 ning
> *«`aborted_guard` dispozitsiyasi istisno emas, QOIDA bo'lib
> qoladi»* bahosi kalibrlangan dozada **rad etiladi**: 29 epizodda
> 0 trip.

**CHEKLOV — `08` §17 ning takroriy-kill tuzatishi SINALMADI.**
`guard.py` endi har trip'da `cgroup.kill` yozadi (`trip()` dagi `first`
faqat `trip_file` uchun ishlatiladi) va yozuv `(reason, kill_ok)`
bo'yicha 10 s da throttle qilinadi (`TRIP_RECORD_INTERVAL_S = 10.0`).
Mening o'lchovimda **bitta** trip bo'ldi va `suppressed_records = 0`.
Demak **ikkinchi trip'ning ham o'ldirishi va yozuv throttle'i
o'lchanmadi, sabab: kalibrlangan dozada guard trip qilmaydi, va
qasddan ikki marta trip qilish uchun over-doza epizodini takrorlash
kerak edi — bu dozalash kalibratsiyasining qamrovidan tashqarida va
guard gate'i `08` da allaqachon o'tgan.** Bu **OQ-7**.

---

## 9. Kollateral zarar va qoldiq

### 9.1 FAKT — nima tekshirildi

```
/proc/vmstat oom_kill                 -> 0 (har run'ning IKKI chekkasida, 9 run)
revixlab.slice memory.events oom_kill -> 0 (35 epizod, har namuna)
revixlab.slice memory.events max      -> 0 (35 epizod, har namuna)
revixlab.slice memory.events oom      -> 0 (35 epizod)
memory.swap.current (lab)             -> 0 (10 Hz sampler + 5 Hz watcher)
SwapFree                              -> 4194304 kB (O'ZGARMADI)
MemAvailable                          -> 9 660 068 .. 9 676 436 kB
journal oom/oomd hits                 -> 0 (har run'da)
systemd-oomd                          -> NOT-INSTALLED / inactive
revixlab.slice tashqarisida o'lgan narsa -> HECH NARSA
```

**FAKT:** `MemAvailable` hech qachon `host_mem_available_min_kb`
(1 500 000 kB) chegarasiga **yaqinlashmadi** — eng kichik o'lchangan
qiymat **9 660 068 kB**, chegaradan **6.4×** yuqori. `MemoryMax=2G`
bilan zaxira `9.71 − 2 = 7.7 GiB` (`08` §9.3 ning hisobi bilan mos).

**FAKT — ataylab o'ldirilgan narsalar.** Har run teardown'ida
`revixlab.slice/cgroup.kill` ga `1` yozildi va `revix-press`,
`revix-guard`, `revix-sampler`, `revix-watch`, `revix-sut`,
`revix-prober` unit'lari to'xtatildi. Bularning **hammasi mening o'z
unit'larim** va hammasi `revixlab.slice` yoki `revixmon.slice` ichida.
`revixlab.slice` tashqarisida men **hech narsa o'ldirmadim**.
Yagona kutilmagan o'lim — guard'ning `P2b` dagi `cgroup.kill` i, va u
**guard'ning to'g'ri ishlashi** (§3.6).

**CHEKLOV — sentinel unit'lar ISHLATILMADI.** `08` §2.3
`guard-test.sh` ning `pgrep` qatorlarini qanoatlantirish uchun sentinel
unit yaratgan. Men `guard-test.sh` ni ishlatmaganim uchun bu kerak
bo'lmadi. Demak *«`revixlab.slice` tashqarisidagi haqiqiy, yirik, faol
iste'molchi bu yukni omon qoladi»* — bu **o'lchov bajarilmadi, sabab:
bu guest ichida desktop ilovasi yo'q (Claude va Chrome Windows
tomonida va guest'ning cgroup ierarxiyasiga kirmaydi).** Men `08` ning
sentinel yondashuvini **ataylab takrorlamadim**, chunki `08` §2.3 ning
o'z CHEKLOV'i sentinel'lar bu savolga javob **bermasligini** yozgan
(ular idle `sleep`, 32 MiB bilan cheklangan, reclaim bosimiga javob
bermaydi). Qo'shimcha asos: bu mashinada `systemd-oomd` **yo'q** va
`/proc/vmstat oom_kill` 35 epizodda **0**, ya'ni kill-authority
umuman ishga tushmadi.

### 9.2 FAKT — qoldiq: NOL

Yakuniy holat, **2026-10-03T05:54:10Z**,
`boot_id=b7a7f0b5-cbad-4df0-86a2-6b1ed40a5df6` (barcha run'lardan
keyin, distro'ning o'z restart'idan keyin):

```
$ systemctl --user list-units 'revix*' --all --no-legend --plain      -> []
$ systemctl --user list-units --state=failed --no-legend --plain      -> []
$ find <user@1000.service> -maxdepth 3 -name 'revix*'                 -> []
$ ls -d <user@1000.service>/*/
    .../app.slice/   .../init.scope/            <-- faqat tizimning o'zi
$ find /run/user/1000/systemd/user.control -maxdepth 3
    No such file or directory                   <-- runtime drop-in YO'Q
$ ls -R $HOME/.config/systemd/user
    No such file or directory                   <-- PERSISTENT drop-in YO'Q
$ ls /run/user/1000/systemd/transient
    No such file or directory
$ ls /run/user/1000 | grep -i revix                                   -> []
$ pgrep -af 'revix/sut|revix.(pressure|guard|prober|psi_sampler)'     -> []
$ grep -w oom_kill /proc/vmstat                   -> oom_kill 0
$ awk '/^SwapFree:/{print $2}' /proc/meminfo      -> 4194304 kB
$ journalctl -b 0 | grep -Eic 'oomd|out of memory|invoked oom'  -> 0
$ systemctl is-active systemd-oomd                -> inactive
$ python3 -c "...units.preflight()"
{"clean": true, "problems": [], "units": [], "cgroups": [],
 "stale_drop_ins": [], "unit_patterns": ["revix-*"],
 "slices": ["revixlab.slice", "revixmon.slice"]}
```

**FAKT — `08` §7.4 / OQ-6 ning muammosi aylanib o'tildi.**
`guard-test.sh` ning teardown'i `revixlab.slice` va `revixmon.slice` ni
`active` holatda qoldiradi va keyingi pre-flight'ni bloklaydi. Mening
runner'im slice'larni **o'zi to'xtatadi** (`systemctl --user stop
revixlab.slice revixmon.slice` + `rmdir`) va runtime drop-in'larni
loyihaning **o'z** tozalovchisi bilan o'chiradi
(`revix/units.py:clear_runtime_drop_ins`):

```
removed: ["/run/user/1000//systemd/user.control/revixlab.slice.d"]
```

Shuning uchun **ketma-ket 9 run** bir-birini bloklamadi.

**FAKT:** `dose-01-dial` dan keyin (tozalovchi qo'shilishidan **oldin**)
`units.preflight()` `stale_drop_ins:
["/run/user/1000//systemd/user.control/revixlab.slice.d"]` qaytardi,
lekin `clean: true` bilan. Tozalovchi qo'shilgandan keyin
`stale_drop_ins` ham **bo'sh**.

**CHEKLOV — `$HOME/revix-runs/guard-recal-*` o'chirilmadi.** Bu `08`
ning 13 run'ining chiqishi va u mening ma'lumotim emas. Men unga
tegmadim (boshqa agentning o'lchov ma'lumotini o'chirish mening
vazifam emas), lekin uning birorta raqami bu hujjatda
**ishlatilmadi** (§1.3 CHEKLOV).

---

## 10. Muzlatilmagan parametrlar: `TimeoutStartSec` va `WatchdogSec`

`PREREGISTRATION.md` §16.10 va `revix/driver.py` (satr 248–254) ikkisini
ham `run_meta.open_parameters` da `calibration_required: true` bilan
qayd etadi, chunki §9.2 ning **(i)** (`TimeoutStartSec` oshib ketdi) va
**(iv)** (watchdog miss) **oldindan aytilgan mexanizmlar** — ya'ni bu
ikki raqam **natijani yaratishi mumkin**.

### 10.1 FAKT + TALQIN — `TimeoutStartSec = 10 s`

**O'lchangan** (§6.2):

| band | `t_start` max | p99 | `10 s` dan oshgan urinish |
|---|---|---|---|
| `P0` | 0.0576 s | 0.0555 s | **0/30** |
| `P1` | **1.4807 s** | 1.3948 s | **0/24** |
| `P2` | 1.1883 s | 1.1211 s | **0/24** |

**FAKT:** 78 urinishdan **birortasi ham** `TimeoutStartSec=10s` ga
yetmadi. Eng katta o'lchangan `t_start` **1.4807 s**, chegaradan
**6.75× kichik**.

**TALQIN — `08` §12 OQ-11 ning ogohligi kalibrlangan dozada
yumshaydi.** OQ-11: *«`TimeoutStartSec = 10 s` default'i `t_start` ning
pressure ostidagi o'lchangan p99 ga juda yaqin (toza o'lchov 7.20 s)»*.
Kalibrlangan dozada p99 **1.1211 s (`P2`) / 1.3948 s (`P1`)**, demak
chegara p99 dan **7.2–8.9×** yuqori. `08` ning *«arm A ning o'zi
pressure ostida `Result=timeout` beradi»* xavfi kalibrlangan dozada
**o'lchov bilan ko'rinmadi** (0/48).

**TALQIN — nima tavsiya qilaman (va nima qilmayman).** `10 s` qiymati
**xavfsiz** va men uni o'zgartirishni **tavsiya qilmayman**: u
mexanizm (i) ni maskalamaydi, chunki o'lchangan `t_start` unga
yaqinlashmaydi ham. **Lekin u `PREREGISTRATION.md` §17.2 ning
oyna budjetidan (0.8 s) 12.5× katta**, va §17.2 ning e'tirozi aynan
shu: *«`0.8 s < t_start < 10 s` bo'lgan har qanday "muvaffaqiyatli"
restart, verifikatsiya oynasi pressure'dan chiqib ketgan restartdir»*.
Mening o'lchovim bu oraliqqa **`P1` da 5/24, `P2` da 2/24** urinish
tushganini ko'rsatadi. Ya'ni **`TimeoutStartSec` ni o'zgartirish bu
muammoni hal qilmaydi** — u §17.5 ning qarori (O1–O4) bilan hal
qilinadi, chegarani siljitish bilan emas. **Shuning uchun:
`TimeoutStartSec = 10 s` saqlanadi, va §16.10 ning
`calibration_required: true` belgisi uchun o'lchangan asos endi bor:
`max(t_start) = 1.4807 s` da 10 s **6.75× zaxira** beradi.**

### 10.2 CHEKLOV — `WatchdogSec = 5 s`: bu o'lchov BAJARILMADI

**`WatchdogSec` bu hujjatda o'lchanmadi.** Barcha 78 SUT start'i
`WatchdogSec` **qo'yilmasdan** bajarildi (`revix/sut.c:837` ning
`WATCHDOG_USEC` env'i o'rnatilmagan, demak `sut.c:293` ning
`sd_notify(0, "WATCHDOG=1")` yo'li **ishga tushmadi**).

**Sabab:** `t_start` va `D_probe` o'lchovlari uchun `Restart=no` /
`Restart=on-failure` kerak edi, watchdog esa uchinchi, mustaqil
o'lim yo'lini kiritardi va `t_start` taqsimotini ifloslantirardi.
Watchdog'ni alohida o'lchash kerak, va u bu kalibratsiyaning
qamrovida emas edi.

**Shuning uchun `WatchdogSec` uchun tavsiya bermayman.** Kerakli
o'lchov — aniq va bajarilishi oson:

> **So'ralgan o'lchov.** SUT'ni kalibrlangan `P2` dozasi ostida
> (`base_mb=184`, `target_rate=0.60`) `WatchdogSec=` **juda katta**
> qiymat bilan (masalan 60 s, ya'ni amalda trip qilmaydigan) ishga
> tushirib, ketma-ket `WATCHDOG=1` keepalive'lari **orasidagi eng
> katta oraliqni** o'lchash kerak. `WatchdogSec` o'sha maksimumning
> kamida 2–3 karrasi bo'lishi kerak, aks holda §9.2 ning (iv)
> mexanizmi **asbob artefakti** sifatida ishga tushadi va
> `Result=watchdog` haqiqiy scheduling delay'ni emas, keepalive
> jadvalining qisqa uzilishini bildiradi.
>
> Mening o'lchovim bu uchun **bilvosita yuqori baho** beradi:
> `t_start` ning SUT tashqarisidagi qismi `P2` da p50 **0.5575 s**
> (= 0.5727 − 0.0152), va eng yomon holatda **≈1.175 s**
> (= `max(t_start)` 1.1883 − `min(uptime_us)` 0.0134), ya'ni reclaim
> throttling bitta jarayonni **1 s dan ko'proq** ushlab turishi
> o'lchandi. Agar keepalive sikli ham shunday ushlanса, `5 s`
> chegarasi **≈5× zaxira** beradi — lekin bu **TALQIN, o'lchov emas**,
> chunki keepalive sikli `main()` dan **keyin** ishlaydi va men uni
> o'lchamadim.

Bu **OQ-8**.

---

## 11. Ochiq masalalar (frozen hujjatlar bilan ziddiyat — men hal qilmayman)

- **OQ-1.** `02` §3 ning dizayn bayonoti bu mashinada **yarim to'g'ri**:
  ramp haqiqatan bepul (§4.1), lekin doza **bazaning `memory.current`
  overage'idan** keladi, churn impulslaridan **emas** (§2.4: dozalangan
  epizodlarda churn `sum = 6…13`, nol-doza epizodida `sum = 315`).
  `02` §3 ning knob'lari (*«blok HAJMI → impulsning stall kattaligi;
  churn SONI → duty cycle»*) o'lchov bilan **qo'llab-quvvatlanmaydi**.
  Qaror `02` egasiniki.
- **OQ-2.** 🔴 `revix/driver.py:_pressure_argv` generatorga `--step-mb`
  va `--base-mb` **bermaydi**, demak pilot `step_mb=16` →
  `base = 160 MiB` → **o'lchangan NOL doza** bilan ishlaydi (§2.5).
  Tuzatish kodda kerak (`--step-mb 4` yoki `--base-mb 184`, yoki
  `run_pi` ning avtomatik formulasini o'zgartirish) va `step_mb` /
  `base_mb` `run_meta.open_parameters` ga kiritilishi kerak.
  **Men kodni o'zgartirmadim.** Bu **pilotning eng yaqin blokeri**.
- **OQ-3.** `02` §4 ning *«Boshqarish qo'pol: tezlik 0.246–0.411
  orasida tebranadi»* bahosi bu mashinada **0.03–0.95** (§3.5), ya'ni
  ≈5.7× kengroq. `02` §4 ning «qabul qilinadi» hukmi bu muhitga
  **ko'chirilmaydi**; `PREREGISTRATION.md` §9.4 ning «analiz erishilgan
  pressure'dan foydalanadi» qarori shuning uchun **yanada zarurroq**.
- **OQ-4.** `run_pi` ning `kp = 12.0` va `ki = 3.0` koeffitsiyentlari
  `pressure.py` ning CLI'sida **ochilmagan**, shuning uchun nozikroq
  boshqarish bandni **uzluksiz** ushlay oladimi — **o'lchanmadi**
  (§3.5 CHEKLOV). Agar §9.3 ning uchinchi stratasi **kategorik**
  ko'rinishda kerak bo'lsa, bu o'lchov bajarilishi shart.
- **OQ-5.** Mening epizodlarim **12 s** (topshiriqning xavfsizlik
  qoidasi), pilotning epizodi esa `ramp_s + hold_s = 17 s`
  (`driver.py:_start_pressure`). Band ichida qolish vaqtlari (§3)
  ≈9.5 s hold uchun va **12 s hold'ga ko'chirilmaydi**.
  `ramp_above_threshold_s` ko'chiriladi (§4.2).
- **OQ-6.** Start lahzasidagi **oniy** stall yozilmadi, demak
  `t_start` ning dozaga regressiyasi **o'lchanmadi** (§6.5 CHEKLOV).
  `P1` ning `p90` i `P2` dan **yuqori** chiqishi shu sababdan
  tushuntirilmaydi — faqat arra tishining fazasi deb **taxmin**
  qilinadi.
- **OQ-7.** `guard.py` ning yangi takroriy-kill xatti-harakati va
  yozuv throttle'i (`08` §17 ning tuzatishi) **sinalmadi**:
  kalibrlangan dozada guard trip qilmaydi, o'lchovda esa bitta trip
  bo'ldi va `suppressed_records = 0` (§8.2 CHEKLOV).
- **OQ-8.** `WatchdogSec = 5 s` uchun **hech qanday o'lchov
  bajarilmadi** (§10.2). Kerakli o'lchov §10.2 da aniq
  ta'riflangan. `calibration_required: true` belgisi **o'z kuchida
  qoladi**.
- **OQ-9.** `D_probe` run'larida prober `P1` va `P2` da **har birida
  4 ta brownout** epizodini ko'rdi (`b_response` / `rt_timeout`,
  `invocation_id` o'zgarmagan), `P0` da **0** (§7.4). Bu §9.2 ning
  **(iii)** mexanizmining o'lchangan izi va §4 ning `contract_fail`
  invalidator'iga bevosita tegadi: `W_stab` ichidagi 0.2 s li
  brownout butun VR ni invalidatsiya qiladi, SUT o'lmagan va restart
  bo'lmagan holda. **Bu hujjat brownout'ni tahlil qilmaydi.**
- **OQ-10.** `P2` dozasida prober `skipped_cycles = 6`,
  `overruns = 1` qayd etdi (`P0`/`P1` da 0) — §22.3 ning
  *«probe narxi arm'lar bo'yicha bir xil emas»* topilmasining
  pressure bandlari bo'yicha analogi (§7.6). Statistik ta'siri
  tahlil qilinmadi.
- **OQ-11** (`08` §12 OQ-4 ning yopilishi). `MemoryHigh = 192M`
  `MemoryMax = 2G` ostida **ishlaydi** va `02` §3 ning `base = 184`
  juftligi qayta ishlab chiqarildi (§2.2). Lekin **`MemoryHigh` ning
  o'zi optimallashtirilmadi** — men faqat `00` §1 / `driver.py` ning
  `192M` ini sinadim; boshqa `MemoryHigh` qiymatlari **o'lchanmadi**.
  Ishchi `base_mb` oynasi **tor** (faqat 184, §3.6), demak boshqa
  `MemoryHigh` da `base_mb` **qaytadan** topilishi kerak bo'ladi.

---

## 12. VERDIKT

`00-pilot-topologiya.md` §6 ning **4-qadami** aynan shuni talab qiladi:

> «**pressure dosing kalibratsiyasi** (fault YO'Q) — `<=12 s` oyna
> ichida erishiladigan PSI bandlari; `user@1000.service` PSI oomd
> chegarasidan uzoq pastda qolishi; `memory.swap.current == 0`»

### 12.1 Qaysi bandlar DELIVERABLE

| band | nishon | erishilgan p50 (epizod medianalari) | band ichida (epizod) | **eng uzun uzluksiz** | hukm |
|---|---|---|---|---|---|
| **`P0`** | 0.00 | **0.0000** | 1/1 | **9.8 s** (9.8/9.8) | ✅ **YETKAZILADI va USHLAB TURILADI** |
| **`P1`** | **0.30** | **0.2810** (0.2234–0.3892) | **10/13** | **1.9 s** | ⚠️ **YETKAZILADI, USHLAB TURILMAYDI** |
| **`P2`** | **0.60** | **0.7023** (0.5726–0.9213) | **8/11** | **1.1 s** | ⚠️ **MEDIANA bo'yicha YETKAZILADI, USHLAB TURILMAYDI** |

**Dial** (§2.6): `MemoryMax=2G`, `MemoryHigh=192M`, `step_mb=4`,
`base_mb=184` (`P0`: 160), `chunk_mb=32`, `interval_ms=250`;
`target_rate` = 0.0 / 0.30 / **0.60**.

**`P2` ning ushlab turilmasligi birinchi darajali natija va u
yashirilmaydi.** Sababi o'lchangan: mexanizm hamon **binar** (`02` §3),
oniy tezlik 0.04 ↔ 0.94 orasida ≈3–4 s davr bilan arra tishi qiladi,
va 0.20 kenglikdagi bandni uzluksiz ushlash uchun duty cycle
granularligi juda qo'pol (§3.5). `PREREGISTRATION.md` §9.4 ning
*«analiz ERISHILGAN (uzluksiz) pressure'dan foydalanadi»* qarori bu
holatni **qoplaydi** — lekin §10.1 ning **kategorik** uch darajali
Cochran–Armitage testi uchun `P1` va `P2` ning **oniy** taqsimotlari
ustma-ust tushadi (ikkisi ham `[0.03, 0.95]`), garchi medianalari
yaxshi ajralsa ham (0.000 / 0.281 / 0.702).

### 12.2 §9.4 invariant 2 — BAJARILADI

```
ramp_above_threshold_s = 0.000 s   (base_mb=184, 29 epizodda 29/29, HAQIQIY doza bilan)
hold_s                 = 12 s      (§9.4 invariant 1 ning hold_cap_s)
-----------------------------------------------------------------------
12 + 0.000 = 12.000  <=  guard_sustain_s = 15     ✅  zaxira 3.000 s
```

Uchala band uchun ham. Qo'shimcha: **invariant 1 ham bajariladi** —
`overrun_s` n=34, p50 **0.0619 s**, max **0.2899 s** (kalibrlangan
dial'da max **0.1766 s**), ya'ni `08` §5 ning 11.3 s oshib ketishi
**39.0× kichraydi** va epizodni to'xtatgan narsa **generatorning o'zi**,
guard emas (§5.1).

> **`PREREGISTRATION.md` §21.7 ning GATE sharti o'lchov bo'yicha
> BAJARILDI.** Gate'ni rasman yopish frozen matn egasining qarori.

### 12.3 ⭐ Sarlavha — `p90(t_start)` kalibrlangan `P2` dozasida

```
p90(t_start)   =  0.7863 s        n = 24,  start muvaffaqiyatsizligi 0/24
budjet (§17.2) =  0.8 s
zaxira         =  1.02x           (0.0137 s, ya'ni 1.7%)
22/24 urinish budjet ichida
erishilgan doza: epizod medianalari 0.5726 .. 0.7094  (band P2 = 0.60..0.80)
```

Aynan bir xil metod bilan, taqqoslash uchun:

| | `08` §15.3 / §21.5 | **bu hujjat** |
|---|---|---|
| doza | nazoratsiz to'yinish ≈0.999 | **kalibrlangan `P2`** |
| `p90(t_start)` | **5.4042 s** | **0.7863 s** |
| budjetga nisbati | **6.76×** | **0.98×** |
| budjet ichida | **0/6** | **22/24** |
| start bo'lmadi | 1/7 | **0/24** |

### 12.4 §17.5 ning qarori hali kerakmi?

**Muzlatilgan qoidaning HARFI bo'yicha: kalibrlangan `P2` da
`p90(t_start) = 0.7863 s ≤ 0.8 s`, demak §17.5 ning O1–O4 qarori
KERAK EMAS.**

**Men bu hukmni yopilgan deb BERMAYMAN, va sababi uchta o'lchangan
fakt:**

1. **`P1` da qoida BUZILADI:** `p90 = 0.9543 s > 0.8 s` (19/24).
   §9.3 `P1` ni to'laqonli yacheyka qiladi, demak `P1` da buzilgan
   invariant butun dizaynni qamrab oladi.
2. **Birlashtirilgan 48 namunada ham BUZILADI:** `p90 = 0.9105 s`
   (41/48).
3. **`P2` ning zaxirasi o'lchov shovqinidan kichik:** 0.0137 s
   (1.7%), `n = 24` da; qolaversa `P1` ning p90 i `P2` dan **yuqori**
   chiqdi — monotonlikning buzilishi, ya'ni bu farq dozaning emas,
   arra tishi fazasining funksiyasi (§3.5, OQ-6).

> **Halol hukm:** `08` va `PREREGISTRATION.md` §21.5 ning **halokat
> bahosi (6.76×, 0/6) RAD ETILDI** — u kalibrlangan dozaning qiymati
> emas, to'yinish dozasining qiymati edi. **Nuqson esa YOPILMADI**:
> u endi halokat emas, **budjet chegarasidagi muvozanat**. `P2`
> o'tadi, `P1` o'tmaydi, zaxira shovqin ichida.
>
> **Qaror loyiha egasiniki**, va men O1–O4 dan birini tanlamayman.
> Bitta o'lchangan fakt qarorni **arzonlashtiradi**: §17.5 O3 ni
> *«yagona variant hech bir ilmiy da'voni kuchsizlashtirmaydigan»*
> deb belgilagan, lekin §9.4 invariant 2 ning qayta tekshirilishini
> shart qilgan — **bu hujjat o'sha tekshiruvni bajardi**
> (`ramp_above_threshold_s = 0.000 s`), demak `hold_cap_s` ni
> **15 s gacha** oshirish invariant 2 ni buzmaydi
> (`15 + 0.000 = 15 ≤ 15`) va guard'ning `sustain_max_seconds = 15.0`
> i **o'zgartirilishi kerak emas**.

### 12.5 Pilot (120 trial) ishga tushirilishi mumkinmi?

❌ **HOZIR MUMKIN EMAS** — lekin sabab `08` §14.3 ning sababi **EMAS**.

`08` ning blokeri (epizod uzunligi majburlanmaydi) **YOPILDI** (§5).
Qolgan blokerlar, ustuvorlik tartibida:

1. 🔴 **`driver.py` generatorga dozalash parametrlarini bermaydi**
   (OQ-2): pilot `step_mb=16` → `base=160 MiB` → **o'lchangan nol doza**
   bilan ishlardi, va `P1`/`P2` arm'lari jimgina `P0` ga aylanardi.
   **Kod tuzatishi; men kodni o'zgartirmadim.**
2. 🔴 **`driver.py` ning `PRESSURE_TARGET_RATE["P2"] = 0.70` i
   over-doza beradi** (erishilgan 0.8868, band **ustida**).
   O'lchangan to'g'ri qiymat **0.60**.
3. ⚠️ **§17.5 va §18.6 ning ikki qarori hali qabul qilinmagan**
   (`PREREGISTRATION.md` sarlavhasining «Ochiq qaror 1 va 2»). Bu
   hujjat ikkisi uchun ham **o'lchovni** beradi (§6.5, §7.5), lekin
   qarorni **bermaydi**.
4. ⚠️ **`P2` nishon sifatida ushlab turilmaydi** (§3.4). Bu pilotni
   to'xtatmaydi (§9.4 uzluksiz analizni belgilaydi), lekin §10.1 ning
   kategorik uchinchi stratasini **o'rnatilmagan** qoldiradi (OQ-4).
5. ⚠️ **`WatchdogSec` kalibrlanmagan** (OQ-8, §10.2).

### 12.6 Qisqa qilib

| savol | javob |
|---|---|
| Dosing kalibratsiyasi (`00` §6 qadam 4) bajarildimi? | ✅ **HA** |
| Doza bu mashinada yetkaziladimi? | ✅ **HA — birinchi marta** (§2) |
| `P0` / `P1` / `P2` yetkaziladimi? | ✅ / ✅ / ⚠️ **mediana bo'yicha ha** |
| `P2` **ushlab turiladimi**? | ❌ **YO'Q** — eng uzun uzluksiz 1.1 s (§3.4) |
| §9.4 invariant 1 va 2 bajariladimi? | ✅ **HA** (§4.2, §5.1) |
| §21.7 ning GATE sharti bajarildimi? | ✅ **HA** — o'lchov bo'yicha |
| `user@` PSI oomd chegarasidan pastda qoldimi? | ✅ **HA** — `systemd-oomd` bu mashinada yo'q; `user@` cho'qqisi 0.9434, guard 0.98 chegarasini bir marta (over-dozada) urdi |
| `memory.swap.current == 0`? | ✅ **HA** — 35 epizod, ikki kuzatuvchi, hamma namuna |
| **`p90(t_start)` kalibrlangan `P2` da** | **0.7863 s** (budjet 0.8 s, zaxira 1.02×) |
| **§17.5 ning qarori kerakmi?** | ⚠️ **`P2` da harfan YO'Q; `P1` da (0.9543) va birlashtirilganda (0.9105) HA** |
| §18.6 ning qarori kerakmi? | ✅ **HA, uchala bandda** — `thr` = 0.60 / 1.70 / 2.05 × P, hammasi < 5P |
| `TimeoutStartSec` | **10 s saqlanadi** — o'lchangan `max(t_start)` 1.4807 s, 6.75× zaxira (§10.1) |
| `WatchdogSec` | ❌ **o'lchanmadi** — kerakli o'lchov §10.2 da ta'riflangan (OQ-8) |
| Kollateral zarar / qoldiq | ✅ **YO'Q / NOL** (§9) |
| Pilot ishga tushirilishi mumkinmi? | ❌ **YO'Q** — OQ-2 (nol doza), `P2` nishoni, ikki ochiq qaror |

---

## 13. Aloqador hujjatlar

- [`08-guard-rekalibratsiya.md`](08-guard-rekalibratsiya.md) — bevosita
  salafi; §2 (harness blokerlari), §3.4 (nol doza), §3.5 (`P1` trip
  qilmaydi), §3.6 (`P2` traversi), §5 (epizod chegarasi), §11
  (`ramp_above_threshold_s`), §12 (OQ-4, OQ-6, OQ-11, OQ-12), §14
  (verdikt), §15 (`t_start`), §16 (`D_probe`), §17 (takroriy kill)
- [`02-guard-kalibratsiyasi.md`](02-guard-kalibratsiyasi.md) — §1
  (`user@ ≈ lab`), §2 (tezlik oynasi), **§3 (pressure mexanizmi, churn
  tartibi, baza qoidasi — OQ-1)**, §4 (PI controller — OQ-3), §6
  (kollateral zarar ro'yxati), §8
- [`00-pilot-topologiya.md`](00-pilot-topologiya.md) — §1
  (`MemoryMax=2G`, `MemoryHigh=<dial>`), §2 (cheklash mexanizmlari),
  §3 (xavf tahlili), §5 (trial jadvali), §6 (qurilish tartibi,
  **qadam 4**)
- [`07-wsl-muhit-tekshiruvlari.md`](07-wsl-muhit-tekshiruvlari.md) —
  §4.4 (distro idle-stop), §4.7 (`/init.scope`), §7.2 (drvfs), §8
- [`PREREGISTRATION.md`](../../PREREGISTRATION.md) — §4 (VR bandlari,
  `W_stab_pilot`), §7 (`total=` birlamchi), §8.2 (probe narxi),
  §8.4 (quiescence 0.05), §9.2 (oldindan aytilgan mexanizmlar),
  §9.3 (bandlar), **§9.4 (dosing va ikki invariant)**, §10.1/§10.2,
  §16.10 (muzlatilmagan parametrlar), §17.2/§17.5 (`t_start` budjeti
  va qaror), §18.6 (fail-slow limbi), §21.2/§21.3/§21.5/§21.7/§21.8,
  §22.3 (probe narxi arm'lar bo'yicha)
- [`revix/pressure.py`](../../revix/pressure.py) — `Deadline`,
  `Allocator._touch`/`retouch`/`churn`, `run_pi` (baza formulasi),
  `_finish` (`overrun_s`)
- [`revix/guard.py`](../../revix/guard.py) — `DEFAULTS`, `Guard.trip`,
  `_check_sustain`, `TRIP_RECORD_INTERVAL_S`
- [`revix/driver.py`](../../revix/driver.py) — **`_pressure_argv`
  (OQ-2)**, `PRESSURE_TARGET_RATE`, `LAB_SLICE_PROPERTIES`,
  `DEFAULT_MEMORY_HIGH`, `DEFAULT_TIMEOUT_START_SEC`,
  `DEFAULT_WATCHDOG_SEC`
- [`revix/prober.py`](../../revix/prober.py) — `PROBE_FIELDS`,
  `cost_report` (§7.6)
- [`revix/sut.c`](../../revix/sut.c) — `sd_notify` (satr 155),
  `INFO uptime_us` (satr 612), `WATCHDOG=1` (satr 293),
  `SOCK_SEQPACKET` (satr 775)
- [`scripts/guard-test.sh`](../../scripts/guard-test.sh) —
  **ishlatilmadi va o'zgartirilmadi** (§1.1)
