# TESTING — test strategiyasi va uni ishga tushirish

> **Bu loyihada "tasdiqlangan" so'zining ma'nosi qat'iy:** test **haqiqatan
> ishga tushirilgan** va uning chiqishi mavjud. Ishga tushirilmagan test
> haqida *"bu test ishga tushirilmadi, sabab: …"* deb yoziladi. Boshqa variant
> yo'q. Qoida [`README.md`](README.md) "Ilmiy yaxlitlik" bo'limida va
> [`CONTRIBUTING.md`](CONTRIBUTING.md) da.

---

## 1. Hozirgi holat — o'lchangan

```
$ python3 -m pytest tests/ -q
1062 passed, 1 skipped, 1 warning in 87.95s (0:01:27)
```

**1062 test o'tdi, 1 skip, 0 yiqilish.** Bu raqam shu hujjat yozilganda
haqiqatan ishga tushirilgan buyruqdan olingan: 2026-10-03, commit
`9482a1c`, Python 3.14.7 (GCC 16.2.0), pytest 9.1.1, WSL2 Kali,
kernel `6.6.87.2-microsoft-standard-WSL2`, ext4 ish joyi.

Skip qilingan 1 test — `systemd-oomd` mavjud bo'lgan holat uchun; bu
mashinada oomd o'rnatilmagan ([`07-wsl-muhit-tekshiruvlari.md`](docs/architecture/07-wsl-muhit-tekshiruvlari.md)
§6.4). **Skip — o'tish emas.**

`make -C revix all` → `rc=0`, `cc -O2 -Wall -Wextra -Werror -std=c11 -pthread`.

Fayl bo'yicha taqsimlanishi (`pytest --collect-only -q` bilan sanalgan,
har bir fayl alohida):

| Fayl | Testlar | Nimani sinaydi |
|---|---|---|
| [`tests/unit/test_schema.py`](tests/unit/test_schema.py) | 12 | envelope, oqim bo'yicha `seq`, yozuvchilar, disposition enum'i |
| [`tests/unit/test_cgroup.py`](tests/unit/test_cgroup.py) | 9 | PSI parse, `stall_fraction` kvantlash qoidasi, dash'siz slice nomi |
| [`tests/unit/test_guard.py`](tests/unit/test_guard.py) | 30 | guard chegara mantiqi, FAIL-CLOSED, davomiylik himoyasi, tezlik oynasi |
| [`tests/unit/test_pressure.py`](tests/unit/test_pressure.py) | 9 | churn tartibi (ajrat→bo'shat), hisob tiklanishi, epizod chegarasi |
| [`tests/unit/test_prober.py`](tests/unit/test_prober.py) | 40 | tasnif qarorlari, detection vaqti, pacing, invocation race |
| [`tests/unit/test_sut.py`](tests/unit/test_sut.py) | 23 | haqiqiy `sut.c` jarayoni ustidan wire protokol va `progress` semantikasi |
| [`tests/unit/test_units.py`](tests/unit/test_units.py) | 19 | transient unit yaratish, property bracket'i, `require_alive` |
| [`tests/unit/test_schedule.py`](tests/unit/test_schedule.py) | 75 | jadval determinizmi, `TrialTimeline` invariantlari, washout mashinasi |
| [`tests/unit/test_stats.py`](tests/unit/test_stats.py) | 69 | Cochran–Armitage, KM, log-rank, RMST, Newcombe, Clopper–Pearson, BCa |
| [`tests/unit/test_reduce.py`](tests/unit/test_reduce.py) | 69 | onset topish, birlamchi denominator a'zoligi (§16.2/§17.4/§20.2) |
| [`tests/unit/test_driver.py`](tests/unit/test_driver.py) | 131 | trial orkestratsiyasi, 10 majburiyat, `--dry-run`, nol-doza rad etilishi |
| [`tests/unit/test_analyze.py`](tests/unit/test_analyze.py) | 104 | `analysis.json` sxemasi, 8 majburiyat, taqiqlangan statistika yo'qligi |
| [`tests/unit/test_figures.py`](tests/unit/test_figures.py) | 93 | 6 majburiy figura + raqam sidecar'i, oq-qora o'qiladigan |
| [`tests/unit/test_cli.py`](tests/unit/test_cli.py) | 83 | subcommand'lar, `--json` uslubi, nolga teng bo'lmagan exit |
| [`tests/unit/test_gui.py`](tests/unit/test_gui.py) | 74 | dashboard render'i, to'rt qiymat holati, `n/m reason=` |
| [`tests/unit/test_validate.py`](tests/unit/test_validate.py) | 183 | driver chiqishi uchun invariantlar |
| [`tests/integration/test_chain.py`](tests/integration/test_chain.py) | 40 | driver → reduce → validate → analyze → figures zanjiri, fixture ma'lumot bilan |
| **Jami** | **1063** | |

1063 collected = 1062 passed + 1 skipped. Yig'indi suite natijasiga mos.

> ⚠️ **Diqqat — test sonini hech qaerdan ko'chirmang.** Bu hujjat uch marta
> eskirgan: commit `12b478b` (prober) xabarida "full unit suite 85 pass"
> yozilgan edi, u merge'dan oldingi holat; keyin bu bo'lim **102** da
> qoldi (commit `26cf4cf`, faqat `tests/unit/`); `README.md` esa bir
> muddat **866 passed, 1 failed** deb turdi. Uchalasi ham o'z vaqtida
> to'g'ri bo'lgan va keyin jimgina noto'g'riga aylangan.
>
> Yana ikki tuzoq: `tests/unit/` ni `tests/` deb o'ylash
> `tests/integration/` ning 40 testini yashiradi (bu xato
> `test_zanjir_figura` ning yiqilishini bir muddat ko'rinmas qilgan);
> va image ichidagi raqam host raqamidan farq qiladi — appliance'da
> **1045 passed, 1 failed, 1 skipped** o'lchangan, yiqilgani
> `test_pacing_10hz_va_drift_yigmaydi`, sababi VM emulatsiyasida timing
> valid emas ([`11-iso-qurilish-jurnali.md`](docs/architecture/11-iso-qurilish-jurnali.md)).

**Hech qanday eksperiment ishga tushirilmadi.** Quyidagi testlar harness
komponentlarini sinaydi, gipotezani emas.

---

## 2. Unit testlarni ishga tushirish

```bash
# hammasi
python3 -m pytest tests/unit/ -q

# bitta fayl
python3 -m pytest tests/unit/test_prober.py -q

# bitta test
python3 -m pytest tests/unit/test_prober.py::test_pacing_10hz_va_drift_yigmaydi -v
```

Repo root'dan ishga tushiriladi (`revix` paketi `sys.path` ga shu tarzda
tushadi; `conftest.py` yoki `pyproject.toml` yo'q — bu ataylab, bog'liqlik
qo'shilmaydi).

O'rnatish va talablar: [`INSTALLATION.md`](INSTALLATION.md).

### Testlarning uslubi

| Qoida | Nega |
|---|---|
| **`test_sut.py` mock ishlatmaydi** — `sut.c` ni `make` bilan kompilyatsiya qiladi va haqiqiy jarayon + haqiqiy `SOCK_SEQPACKET` socket ustidan sinaydi | tekshirilayotgan narsa — **wire protokol**. Mock aynan protokoldan chetga chiqishni yashirardi, prober esa shu protokolga qarab mustaqil yozilgan |
| **`test_prober.py` `sut.c` ni talab qilmaydi** — test ichida yozilgan threadli `SOCK_SEQPACKET` server protokolning prober ko'radigan tomonini o'ynaydi | prober **spetsifikatsiyaga** qarshi sinaladi, parallel yozilgan implementatsiyaga qarshi emas. Ikki komponent bir-birining xatosini tasdiqlab qo'ymaydi |
| **`test_guard.py` haqiqiy pressure yaratmaydi** — `FakePsi` boshqarilgan PSI qiymatlarini beradi | guard **qarorlari** integratsiya testidan oldin to'g'ri bo'lishi kerak; pressure ostida noto'g'ri chegarani tuzatish qimmat |
| **`test_pressure.py` faqat mexanizmni sinaydi** — bir necha MB ajratadi, cgroup chegarasi yo'q | churn **tartibi** (ajrat→bo'shat) va hisob to'g'riligi pressure yaratmasdan tekshiriladi |
| Test nomlari **o'zbekcha va tavsifiy** | nima buzilganini `pytest -v` chiqishidan o'qib bo'ladi |

### Eng muhim uchta test

Bu testlar **regressiya qulfi**: ular buzilsa loyihaning ilmiy hissasi
buziladi, oddiy bug emas.

1. `test_sut.py::test_probe_progressni_shishirmaydi`
   — probe javobi `progress` ni oshirmaydi. Oshirsa, throughput probe tezligini
   o'lchagan bo'lardi, ya'ni o'lchov o'zini o'lchardi va
   `PREREGISTRATION.md` §4 ning 5-bandi ma'nosini yo'qotardi.
2. `test_prober.py::test_yangi_invocation_bilan_progress_reset_no_progress_EMAS`
   — restart'dan keyin `progress` 0 dan boshlanishi failure DEB
   hisoblanmaydi. Aks holda har restart soxta failure bo'lib, downtime
   o'lchovi jimgina buzilardi.
3. `test_guard.py::test_tezlik_oynasi_eng_tor_2s_ni_tanlaydi`
   — tezlik oynasi suzib ketmaydi. Kalibratsiyada bu xato 4.9 s oyna sifatida
   o'lchangan va guard'ni sekinlashtirgan
   ([`docs/architecture/02-guard-kalibratsiyasi.md`](docs/architecture/02-guard-kalibratsiyasi.md) §2).

Yaqin qatorda: `test_guard.py::test_mojallangan_eksperiment_bandi_trip_QILMAYDI`
(guard mo'ljallangan pilot pressure'ini o'ldirmaydi) va
`test_pressure.py::test_churn_avval_ajratadi_keyin_boshatadi` (churn tartibi;
teskari tartibda pressure **umuman** bo'lmaydi).

### C toolchain bo'lmasa

`tests/unit/test_sut.py` `cc` yoki `make` topilmasa **butun modul** bilan
skip qiladi va sababini yozadi:

```
C toolchain yo'q (cc topilmadi) -- sut.c kompilyatsiya qilinmaydi
```

Bu holatda umumiy son 102 dan 85 ga tushadi. Skip **jim emas** — skip
sababi ko'rinadi, va skip qilingan test "o'tgan" deb hisoblanmaydi.

### Sanitizer build'lari

[`revix/Makefile`](revix/Makefile) `EXTRA_CFLAGS` ni qabul qiladi, demak
`sut.c` ni sanitizer bilan qurib test suite'ini shu binar ustida ishga
tushirish mumkin:

```bash
make -C revix clean
make -C revix EXTRA_CFLAGS="-fsanitize=address,undefined -g" all
python3 -m pytest tests/unit/test_sut.py -q

make -C revix clean
make -C revix EXTRA_CFLAGS="-fsanitize=thread -g" all
python3 -m pytest tests/unit/test_sut.py -q

make -C revix clean        # oddiy binarni tiklash
```

> **Holat:** commit `4b421bb` ASan/UBSan va TSan build'lari suite'ni toza
> o'tganini qayd etadi, va TSan'ning qolgan "thread leak" xabari — ataylab
> join qilinmagan worker thread (join `SIGTERM` da qotib qolgan fault'lar
> uchun abadiy kutardi). **Men bu sanitizer build'larini bu hujjat uchun
> qayta ishga tushirmadim** — yuqoridagi 102 raqami oddiy build bilan
> olingan.

---

## 3. Guard integratsiya testi — `scripts/guard-test.sh`

### Nega bu test alohida turadi

`docs/architecture/00-pilot-topologiya.md` §6 ning qurilish tartibida guard
testi **3-qadam**, pressure kalibratsiyasi esa 4-qadam, va o'sha yerda
yozilgan: *"3-qadam 4-qadamdan oldin bajarilishi shart. Retrofit
qilinmaydi."*

> ### 🚨 QOIDA
> **Guard tasdiqlanmasa hech qanday pressure eksperimenti ishga
> tushirilmaydi.** Bu [`README.md`](README.md) xavfsizlik ogohligida va
> `00-pilot-topologiya.md` §6 da yozilgan majburiyat. Guard'ning to'g'riligi
> keyingi **har bir** qadamni gate qiladi, chunki noto'g'ri guard
> foydalanuvchining brauzerini, editorini yoki butun desktop sessiyasini
> yo'qotish demakdir ([`SECURITY.md`](SECURITY.md)).

Unit testlar guard'ning **qarorini** sinaydi (`FakePsi` bilan). Integratsiya
testi guard'ning **haqiqiy PSI ostida, haqiqiy cgroup'da, belgilangan vaqt
ichida** chegarani aniqlab, `revixlab.slice` subtree'sini o'ldirishini
sinaydi. Ikkisi bir-birini almashtirmaydi.

### Protsedura

Skript bir necha bosqichni ketma-ket bajaradi
([`scripts/guard-test.sh`](scripts/guard-test.sh)):

1. **Pre-flight** — `revix-press.service` allaqachon ishlayotgan bo'lsa
   **to'xtaydi**. Baseline yoziladi: `MemAvailable`, `MemFree`,
   `/proc/vmstat oom_kill`, lab `memory.events`, `user@` `memory.pressure`.
   Kuzatiladigan Claude va Chrome renderer PID'lari ro'yxatga olinadi.
2. **Guard ishga tushadi — BIRINCHI**, `systemd-run --user
   --slice=revixmon.slice` bilan, `MemoryMax=128M`, `MemorySwapMax=0`.
   Faol bo'lmasa skript xato bilan chiqadi.
3. **PSI sampler** ham `revixmon.slice` da, 10 Hz, `host`/`user`/`lab`/`mon`
   scope'lari bilan. 2 s baza namunasi yig'iladi.
4. **Pressure generatori** `systemd-run --user --slice=revixlab.slice` bilan,
   `MemorySwapMax=0` va `RuntimeMaxSec=` bilan.
5. **Kutish**, keyin **teardown**: `cgroup.kill`, `systemctl --user stop`,
   `reset-failed`.
6. **Post-flight tekshiruv** — ro'yxatga olingan Claude/Chrome PID'lari tirikmi,
   `systemd-oomd` journal'ida xabar bormi.

Natijalar `$OUT` katalogiga yoziladi: `baseline.json`, `guard.jsonl`,
`trip.json`, `psi.csv`, `sampler.jsonl`, `pressure.jsonl`.

### Xavfsizlik chegaralari

| Chegara | Qiymat (default) | Nega |
|---|---|---|
| pressure davomiyligi | `PRESS_SECONDS=8` s | oomd ning 20 s sustained shartidan ancha qisqa |
| generator'ning o'z chegarasi | `--max-seconds` | **birinchi** mustaqil vaqt chegarasi |
| systemd chegarasi | `RUNTIME_MAX=12` s → `RuntimeMaxSec=` | **ikkinchi**, birinchisidan mustaqil chegara |
| swap | `MemorySwapMax=0` | 5.5 GiB swap to'lib host-wide IO yaratishining oldini oladi |
| kuzatish oynasi | `OBS_SECONDS=22` s | guard pressure tugagandan keyin ham kuzatishda davom etadi |
| teardown | `cgroup.kill` | atomik subtree kill, privilegiyasiz — `docs/architecture/01-muhit-tekshiruvlari.md` §3 da tasdiqlangan |

**Ikki vaqt chegarasi chegaradan mustaqil**, demak PSI qanday bo'lishidan
qat'i nazar pressure to'xtaydi. Bu skriptning eng muhim xavfsizlik
xususiyati: u guard'ning to'g'ri ishlashiga **tayanmaydi**.

### Ishga tushirish

```bash
# default: user@ kuzatiladi, ramp rejimi, 8 s pressure
OUT=/tmp/guard-test-1 bash scripts/guard-test.sh

# PI rejimi, mo'ljallangan pilot bandiga yaqin nishon
OUT=/tmp/guard-test-2 MODE=pi TARGET_RATE=0.30 PRESS_SECONDS=12 \
  bash scripts/guard-test.sh
```

Sozlanadigan env o'zgaruvchilari skript boshida sanalgan (`WATCH`,
`PRESS_SECONDS`, `RUNTIME_MAX`, `CAP_MB`, `CHUNK_MB`, `MODE`, `TARGET_RATE`,
`BASE_MB`, `STEP_MB`, `OBS_SECONDS`, `FULL_AVG10`, `SOME_AVG10`, `RATE2S`,
`SUSTAIN_RATE`, `SUSTAIN_MAX`).

> ⚠️ **Skriptning `SUSTAIN_MAX` default'i (`13.0`) `revix/guard.py` ning
> `DEFAULTS["sustain_max_seconds"]` (`15.0`) va
> `docs/architecture/02-guard-kalibratsiyasi.md` §1 dagi kalibrlangan 15 s
> bilan mos EMAS.** Kalibratsiya hujjati 15 s ni "pilot hold ≤12 s + ramp
> ≤3 s = eng yomon holatda 15 s, demak to'g'ri ishlayotgan trial hech qachon
> trip qilmaydi" deb asoslaydi — 13 s bu asosni buzadi. Bu
> [`ARCHITECTURE.md`](ARCHITECTURE.md) §6 dagi **2-ochiq masala**; hal
> qilinmaguncha skriptni aniq `SUSTAIN_MAX=15.0` bilan ishga tushirish
> tavsiya etiladi.

### Nimasi tasdiqlangan (kimning o'lchoviga ko'ra)

[`docs/architecture/02-guard-kalibratsiyasi.md`](docs/architecture/02-guard-kalibratsiyasi.md)
§5 to'rt ishga tushirishning natijasini qayd etadi — trip sabablari, o'lchangan
tezliklar, `kill_ok`, va §6 da **kollateral zarar yo'q** (Claude/Chrome
renderer'lari tirik, oomd journal'ida hech narsa, `vmstat oom_kill`
o'zgarmagan, swap ishlatilmagan, qoldiq yo'q).

> **Men `scripts/guard-test.sh` ni bu hujjat uchun ishga tushirmadim.**
> Yuqoridagi natijalar `02-guard-kalibratsiyasi.md` da qayd etilgan
> o'lchovlar, shu hujjatning o'lchovi emas. Yangi mashinada guard testi
> **qaytadan** ishga tushirilishi shart, chunki `02` §7 ning 1-masalasi:
> `user@ ≈ lab` topilmasi **bo'sh desktop** shartiga bog'liq va band tizimda
> guard sezgirligi o'zgaradi.

---

## 4. Test qamrovidagi bo'shliqlar (halol ro'yxat)

| Bo'shliq | Sabab |
|---|---|
| Driver, validator, reducer, statistika testlari | bu modullar hali **yozilmagan** ([`ARCHITECTURE.md`](ARCHITECTURE.md) §1) |
| `sut.c` fault'larining hammasi integratsiya darajasida | `test_sut.py` `exit`, `sigkill_self`, `stop_progress`, `slow_start`, `misconfiguration` ni sinaydi; `sigsegv`, `spin`, `deadlock`, `block_fifo`, `leak` P2 fault'lari — ular `PREREGISTRATION.md` §9.3 bo'yicha P1 da ishlatilmaydi |
| Prober va `sut.c` ning uchdan-uchiga integratsiyasi | ikkisi protokolga qarshi **alohida** sinaladi; birgalikdagi smoke test driver bilan keladi (`00-pilot-topologiya.md` §6, 6-qadam) |
| Guard testi band desktop'da | `02` §7 masala 1 — qayta o'lchanishi kerak |
| Statistik funksiyalarni nashr etilgan ishlangan misolga qarshi test | `PREREGISTRATION.md` §10.3 talab qiladi; modul hali yo'q |

---

## 5. Aloqador hujjatlar

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — komponentlar va dizayn qarorlari
- [`SECURITY.md`](SECURITY.md) — nega guard mavjud va u nimani kafolatlamaydi
- [`INSTALLATION.md`](INSTALLATION.md) — talablar, `sut.c` build'i
- [`DEVELOPMENT.md`](DEVELOPMENT.md) — kod uslubi, branch va commit tartibi
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — test o'tganini da'vo qilish qoidalari
