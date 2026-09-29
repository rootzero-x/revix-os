# INSTALLATION — talablar va sozlash

> ## ⚠️ Avval o'qing
> Bu repozitoriy **nazorat qilinadigan memory pressure** yaratadigan kod o'z
> ichiga oladi. Ko'plab Linux desktop tizimlarida `systemd-oomd`
> foydalanuvchi sessiyasiga qarshi **kill authority** bilan sozlangan, va PSI
> ierarxik — ya'ni ehtiyotsiz pressure eksperimenti brauzeringizni,
> editoringizni yoki butun desktop sessiyangizni o'ldirishi mumkin.
>
> **O'rnatishdan keyin birinchi qadam — guard testi**, pressure eksperimenti
> emas. [`SECURITY.md`](SECURITY.md) va [`TESTING.md`](TESTING.md) §3.

**Holat:** hech qanday eksperiment ishga tushirilmadi, hech qanday natija
yo'q. O'rnatish sizga harness komponentlarini va ularning testlarini beradi
([`ARCHITECTURE.md`](ARCHITECTURE.md) §1 komponent holatini ko'rsatadi).

---

## 1. Pilot privilegiyasiz ishlaydi

**P1 uchun root kerak emas.** Bu dizayn qarori, tasodif emas: benchmark har
kim o'z mashinasida root'siz ishga tushira olishi kerak
([`docs/research/04-novelty-statement.md`](docs/research/04-novelty-statement.md) C4).

---

## 2. Ahamiyatga ega versiyalar

Bu jadvaldagi har bir chegara **aniq bir imkoniyat** uchun kerak — "yangiroq
yaxshiroq" degan umumiy tavsiya emas.

| Talab | Minimal | Nega aynan shu |
|---|---|---|
| **systemd** | **≥ 254** | `RestartSteps=` va `RestartMaxDelaySec=` v254 (2023-avgust) dan mavjud. Baseline B **butunlay** shunga tayanadi: `RestartSteps=` bo'lmasa systemd native exponential backoff yo'q va kuchli baseline yo'qoladi ([`docs/research/01-texnologiya-auditi.md`](docs/research/01-texnologiya-auditi.md) §1) |
| **cgroup** | **v2** (`cgroup2fs`), `cpu memory pids` **delegated** | `MemoryMax=`/`MemoryHigh=`/`MemorySwapMax=`/`CPUQuota=`/`TasksMax=` va `cgroup.kill` privilegiyasiz ishlashi uchun. systemd v258 da cgroup v1 butunlay olib tashlangan (`01-texnologiya-auditi.md` §3) |
| **kernel PSI** | `CONFIG_PSI=y`, Linux **≥ 4.20** | butun o'lchov `total=` akkumulyatoriga tayanadi. PSI bo'lmasa loyihaning markaziy o'zgaruvchisi yo'q (`PREREGISTRATION.md` §7) |
| kernel (PSI trigger izohi) | — | Linux **6.5+** da privilegiyasiz PSI poll trigger oynasi 2 s **karrasi** bo'lishi shart. Bu cheklov emas: harness `total` polling ishlatadi, trigger emas (`01-muhit-tekshiruvlari.md` §5) |
| **Python** | **≥ 3.11** | `PREREGISTRATION.md` va `README.md` belgilagan minimal. Shu mashinada 3.13.15 bilan ishlayapti |
| Python paketlar | `psutil`, `python-systemd`, `dbus`, `pyyaml`, `numpy`, `scipy` | pastda batafsil |
| **C kompilyator** | `gcc` yoki `clang`, C11 | `revix/sut.c` ni qurish uchun (`-std=c11 -pthread`) |
| `make` | — | `revix/Makefile`; `tests/unit/test_sut.py` uni chaqiradi |
| `pytest` | — | unit suite (shu mashinada 9.1.1) |

### Python paketlari haqida halol izoh

**Hozirgi commit qilingan harness modullari faqat standart kutubxonadan
foydalanadi.** `revix/schema.py`, `cgroup.py`, `guard.py`, `pressure.py`,
`psi_sampler.py`, `prober.py` — hech biri uchinchi tomon paketini import
qilmaydi (tekshirilgan: `grep` bo'yicha faqat stdlib import'lari).

Yuqoridagi paketlar **rejadagi** komponentlar uchun:

| Paket | Kim uchun |
|---|---|
| `dbus` (yoki `python-systemd`) | `F_sd` detektori: `ActiveState`, `Result`, `*TimestampMonotonic` (`PREREGISTRATION.md` §3, §6.1) — **rejada** |
| `numpy`, `scipy` | statistika: Fisher, Mann–Whitney, Kruskal–Wallis, bootstrap, va qo'lda yoziladigan Cochran–Armitage / KM / log-rank / RMST (`PREREGISTRATION.md` §10.3) — **rejada** |
| `psutil` | jarayon/resurs kuzatuvi — **rejada** |
| `pyyaml` | konfiguratsiya — **rejada** |

> `statsmodels` va `lifelines` **ishlatilmaydi va qo'shilmaydi.**
> `PREREGISTRATION.md` §10.3: statistika bog'liqlik qo'shmasdan o'zimiz
> yoziladi va nashr etilgan ishlangan misolga qarshi unit-test qilinadi.

---

## 3. O'rnatish (privilegiyasiz)

```bash
git clone <repo> revix && cd revix

# unit testlar
python3 -m pytest tests/unit/ -q

# SUT build'i
make -C revix all            # -> revix/sut
```

`pip install`, `setup.py` yoki `pyproject.toml` **yo'q** — bu ataylab. Repo
`python3 -m revix.<modul>` sifatida repo root'dan ishlatiladi:

```bash
python3 -m revix.guard       --help
python3 -m revix.pressure    --help
python3 -m revix.psi_sampler --help
python3 -m revix.prober      --help
```

> ⚠️ **Bu buyruqlarni to'g'ridan-to'g'ri Bash'dan ishga tushirish faqat
> `--help` uchun xavfsiz.** Haqiqiy pressure yoki o'lchov jarayonlari
> **majburiy ravishda** `systemd-run --user --slice=…` orqali ishga
> tushiriladi — aks holda ular ishlab chiqish vositangizning cgroup'ida
> tug'iladi va oomd o'sha scope'ni o'ldirishi mumkin
> (`01-muhit-tekshiruvlari.md` §6, [`SECURITY.md`](SECURITY.md) §1).

### Paketlarni o'rnatish

Distro paketlari afzal (Debian/Kali/Ubuntu nomlari):

```bash
sudo apt install build-essential python3-pytest python3-psutil \
     python3-dbus python3-systemd python3-yaml python3-numpy python3-scipy
```

> Paket o'rnatish — **root talab qiladigan yagona sozlash qadami** va u
> o'lchovdan oldin, bir marta bajariladi. O'lchov davomida hech qanday root
> process tirik emas ([`SECURITY.md`](SECURITY.md) §5).

---

## 4. Root kerak bo'ladigan narsalar — va nega ular guest'ga tegishli

**P1 da quyidagilarning hech biri ishlatilMAYDI**
(`docs/architecture/00-pilot-topologiya.md` §4, `PREREGISTRATION.md` §0):

| Nima | Nima uchun kerak bo'lardi |
|---|---|
| `io` controller / `io.max` | nazorat qilinadigan IO stall (fault class 6). `io` **delegated emas** — `01-muhit-tekshiruvlari.md` §1 |
| `dm-delay` / `dm-flakey` | blok qurilma darajasidagi IO fault'lari |
| `tc netem` | tarmoq latency fault'lari |
| cgroup `cpuset` pinning | CPU izolyatsiyasi (harness `sched_setaffinity` bilan chetlab o'tadi) |
| `scaling_governor=performance` | DVFS ni o'chirish (`PREREGISTRATION.md` §8.5) |
| `drop_caches` | cold-start o'lchovi — **qilinmaydi**, butun ish stansiyasini buzadi (`§8.3`) |
| paket o'rnatish | yuqorida |
| harness'ni **system slice**ga ko'chirish | oomd kill scope'idan butunlay chiqish — guard'ning qoldiq riskini yopadigan **yagona to'liq yechim** ([`SECURITY.md`](SECURITY.md) §4.1) |

### 🔑 Prinsip: *"root kerak" = "guest'ga tegishli."*

`sudo -n` parol so'raydi, demak hech bir privilegiyali qadam nazorsiz
ishlamaydi. Shundan kelib chiqib: kechalik kampaniya **to'liq
privilegiyasiz** yoki **to'liq QEMU guest ichida** bo'lishi kerak — aralash
emas.

QEMU ichida siz izolyatsiyalangan kernel'da root'siz va host privilegiyasi
`/dev/kvm` dan boshqa kerak emas. Shu mashinada KVM tekshirilgan va 25 G bo'sh
joy bor (`01-muhit-tekshiruvlari.md` §8).

Guest talab qiladigan tadqiqot bloklari: IO injection, sustained pressure
>15 s, `W_stab = 60 s`, host `/proc/pressure` javobi
([`docs/architecture/02-guard-kalibratsiyasi.md`](docs/architecture/02-guard-kalibratsiyasi.md) §7).

---

## 5. Mashinangizni tekshirish

> **Ma'lumotnoma:**
> [`docs/architecture/01-muhit-tekshiruvlari.md`](docs/architecture/01-muhit-tekshiruvlari.md)
> — u shu mashinada **haqiqatan ishga tushirilgan** buyruqlar va ularning
> chiqishini qayd etadi. Quyidagi ro'yxat o'sha hujjatning bandlariga
> ishora qiladi: agar sizning chiqishingiz boshqacha bo'lsa, o'sha banddagi
> asoslash sizda **qo'llanilmaydi** va harness'ning tegishli qarori qayta
> ko'rilishi kerak.

Barcha buyruqlar **faqat o'qiydi** va xavfsiz.

### (1) Versiyalar

```bash
systemctl --version | head -1        # >= 254
python3 --version                    # >= 3.11
uname -r
cc --version | head -1
```

### (2) cgroup v2 va delegatsiya — `01` §1

```bash
stat -fc %T /sys/fs/cgroup/                                    # cgroup2fs
systemctl show user@$(id -u).service -p Delegate -p DelegateControllers
```

Kutilgan: `Delegate=yes`, `DelegateControllers=cpu memory pids`.
`io` ro'yxatda **bo'lmasligi normal** — IO injection guest'ga tegishli, lekin
`io.pressure` **o'qish** baribir ishlaydi (`01` §3).

### (3) PSI mavjud

```bash
cat /proc/pressure/memory
cat /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/memory.pressure
```

Ikkisi ham `some ... total=` va `full ... total=` satrlarini berishi kerak.
`total=` — **asosiy** o'lchov (`PREREGISTRATION.md` §7).

### (4) 🚨 oomd holati — eng muhim tekshiruv — `01` §7

```bash
systemctl show user@$(id -u).service -p ManagedOOMMemoryPressure
systemd-analyze cat-config systemd/oomd.conf | grep -i duration
cat /usr/lib/systemd/system/user@.service.d/*oomd*.conf 2>/dev/null
```

`ManagedOOMMemoryPressure=kill` chiqsa — **sizda ham xavf bor** va guard
majburiy. Chiqmasa ham guard'ni o'chirmang: kernel global OOM killer va swap
thrash baribir mavjud ([`SECURITY.md`](SECURITY.md) §4.3).

### (5) Resurs zaxirasi — `01` §8

```bash
free -h
df -h /
```

`01` §8 da o'lchangani: 15 GiB umumiy, ~7.6 GiB available, 5.5 GiB swap (0
ishlatilgan). 2 GiB eksperiment shifti xavfsiz zaxira qoldirgan. Sizda
available sezilarli kam bo'lsa — guard'ning `host_mem_available_min_kb`
chegarasini va slice `MemoryMax` ni qayta ko'rish kerak.

### (6) Sizning jarayonlaringiz qaysi scope'da tug'iladi — `01` §6

```bash
cat /proc/self/cgroup
```

Chiqish `…/app.slice/app-….scope` ko'rinishida bo'lsa — bu aynan `01` §6
dagi holat: ishlab chiqish vositangizdan ishga tushirilgan jarayon shu
scope'da tug'iladi. **Demak `systemd-run --slice=` majburiy.**

### (7) Qoldiq holat yo'qligi — `01` §9

```bash
systemctl --user list-units 'revix*' --all --no-legend
ls -d /sys/fs/cgroup/user.slice/user-$(id -u).slice/user@$(id -u).service/revix* 2>/dev/null
```

Ikkisi ham bo'sh bo'lishi kerak. Bo'sh bo'lmasa harness pre-flight'da
**ishga tushmaydi** — avval tozalash kerak:

```bash
systemctl --user stop 'revix-*' 2>/dev/null
systemctl --user reset-failed 2>/dev/null
```

### (8) `RestartSteps=` transient property sifatida qabul qilinadimi — `01` §4

Bu tekshiruv transient unit yaratadi (pressure yo'q, `sleep`):

```bash
systemd-run --user --unit=revix-check-rs \
  --property=Restart=on-failure --property=RestartSec=1s \
  --property=RestartSteps=4 --property=RestartMaxDelaySec=8s \
  --property=StartLimitBurst=0 --collect sleep 5
systemctl --user show revix-check-rs.service -p RestartSteps -p StartLimitBurst
```

`RestartSteps=4` chiqsa Baseline B uchun `~/.config/systemd/user/` ga fayl
yozish **kerak emas**.

`--collect` sababli unit 5 s dan keyin o'chadi va qoldiq qolmaydi. Baribir bu
tekshiruvni harness ishga tushirishdan **oldin** bajaring: pre-flight
`revix-*` naqshini tekshiradi, demak tirik `revix-check-rs.service`
harness'ning ishga tushishini rad etadi.

> ⚠️ `01` §4 ning ogohligi: `--collect` bilan unit tugagandan keyin o'chadi, va
> `systemctl show` mavjud bo'lmagan unit uchun **default**larni chiqaradi.
> Shuning uchun **har unit'ning property'lari u TIRIK paytida dump qilinishi
> shart** — `run_meta` ga source fayldan emas, `systemctl show` dan yoziladi
> (`docs/research/05-metodologiya.md` §7).

---

## 6. O'rnatishdan keyingi tartib

1. `python3 -m pytest tests/unit/ -q` — o'tishi kerak
   ([`TESTING.md`](TESTING.md) §1).
2. `make -C revix all` — `-Werror` bilan ogohlantirishsiz qurilishi kerak.
3. Yuqoridagi (1)–(8) mashina tekshiruvlari.
4. **Guard integratsiya testi** — [`TESTING.md`](TESTING.md) §3.
   **Bu qadamdan oldin hech qanday pressure eksperimenti ishga
   tushirilmaydi** (`docs/architecture/00-pilot-topologiya.md` §6).
5. Keyingi qadamlar (pressure kalibratsiyasi, smoke trial, pilot) driver
   moduliga tayanadi — u hali **yozilmagan**
   ([`ARCHITECTURE.md`](ARCHITECTURE.md) §1).

---

## 7. Aloqador hujjatlar

- [`docs/architecture/01-muhit-tekshiruvlari.md`](docs/architecture/01-muhit-tekshiruvlari.md) — empirik muhit faktlari (bu hujjatning manbasi)
- [`docs/architecture/00-pilot-topologiya.md`](docs/architecture/00-pilot-topologiya.md) §4 — privilegiya yuzasi
- [`SECURITY.md`](SECURITY.md) — xavfsizlik va threat model
- [`TESTING.md`](TESTING.md) — testlar va guard testi
- [`DEVELOPMENT.md`](DEVELOPMENT.md) — build, branch, commit uslubi
- [`README.md`](README.md) — loyihaning umumiy tavsifi va talablar jadvali
