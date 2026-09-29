# DEVELOPMENT — loyihada ishlash tartibi

> O'rnatish va talablar: [`INSTALLATION.md`](INSTALLATION.md).
> Arxitektura va dizayn qarorlari: [`ARCHITECTURE.md`](ARCHITECTURE.md).
> Ilmiy yaxlitlik qoidalari: [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## 1. Tez boshlash

```bash
git clone <repo> revix && cd revix

# unit testlar (repo root'dan)
python3 -m pytest tests/unit/ -q

# SUT build'i
make -C revix all            # -> revix/sut
make -C revix clean
```

Kutilgan natija va hozirgi test soni: [`TESTING.md`](TESTING.md) §1.

### Talablar — qisqasi

| | Minimal |
|---|---|
| systemd | ≥ 254 (`RestartSteps=` uchun) |
| cgroup | **v2**, `cpu memory pids` delegated |
| kernel | PSI yoqilgan (`CONFIG_PSI=y`, ≥ 4.20) |
| Python | ≥ 3.11 + `psutil`, `python-systemd`, `dbus`, `pyyaml`, `numpy`, `scipy` |
| C kompilyator | `gcc` yoki `clang` (+ `make`) |

Batafsil, va privilegiyasiz/root bo'linishi bilan:
[`INSTALLATION.md`](INSTALLATION.md).

---

## 2. `sut.c` ni qurish

```bash
make -C revix all
```

[`revix/Makefile`](revix/Makefile) qarorlari:

- **`libsystemd`ga link qilinmaydi.** `sd_notify` `sut.c` ichida ~40 qatorda
  yozilgan (abstract socket shaklini ham ishlaydi). Repo ataylab yangi
  bog'liqlik qo'shmaydi — bu reproducibility narxi.
- **`-Werror` ataylab.** SUT — o'lchov asbobi. Format yoki imzo taqqoslash
  ogohlantirishlari bu yerda jim o'tkazilsa, ular **o'lchov xatosiga**
  aylanadi.
- `CFLAGS := -O2 -Wall -Wextra -Werror -std=c11 -pthread`, `CC ?= cc`.
- `EXTRA_CFLAGS` sanitizer yoki qo'shimcha ogohlantirish bayroqlari uchun:

```bash
make -C revix clean
make -C revix EXTRA_CFLAGS="-fsanitize=address,undefined -g" all
make -C revix EXTRA_CFLAGS="-fsanitize=thread -g" all
make -C revix EXTRA_CFLAGS="-Wshadow -Wformat=2 -Wcast-qual" all
```

`revix/sut` binari `.gitignore` da — **commit qilinmaydi**.

`tests/unit/test_sut.py` binarni **o'zi** `make` bilan quradi
(session-scoped fixture), demak testdan oldin qo'lda qurish shart emas.
`cc` yoki `make` bo'lmasa modul sababi bilan skip qiladi.

---

## 3. Testlar

To'liq strategiya, test soni, guard integratsiya testi protsedurasi va
sanitizer build'lari: **[`TESTING.md`](TESTING.md)**.

Bu yerda faqat ishlab chiquvchi uchun majburiy qoida:

> **Test o'tganini faqat uni ishga tushirgandan keyin yozing.** Test
> ishga tushirilmasa — *"bu test ishga tushirilmadi, sabab: …"* deb yoziladi.
> Test sonini boshqa hujjatdan yoki commit xabaridan **ko'chirmang**: o'zingiz
> `python3 -m pytest tests/unit/ -q` ishga tushirib sanang.

> 🚨 **Guard tasdiqlanmasa hech qanday pressure eksperimenti ishga
> tushirilmaydi** (`docs/architecture/00-pilot-topologiya.md` §6, 3-qadam).

---

## 4. Branch modeli

| Branch | Roli |
|---|---|
| `main` | **barqaror.** Faqat o'tgan testlar bilan, muzlatilgan hujjatlar bilan mos holat |
| `develop` | integratsiya |
| `feature/*` | kod ishi (mavjud misol: `feature/psi-pilot`) |
| `research/*` | hujjat va tadqiqot ishi (mavjud misol: `research/preregistration`) |
| `experiment/*` | eksperiment kampaniyalari va ularning konfiguratsiyasi |
| `agent/*` | parallel ishlayotgan agentlarning izolyatsiyalangan ishi (mavjud misollar: `agent/sut`, `agent/prober`, `agent/stats`, `agent/reduce`) |

### Parallel ish qoidasi

Bir vaqtda bir necha branch ishlaganda **fayl egaligi kesishmasligi kerak.**
Commit `26cf4cf` (merge) shu naqshning misoli: `agent/sut` faqat
`revix/sut.c`, `revix/Makefile`, `tests/unit/test_sut.py` ga tegdi,
`agent/prober` faqat `revix/prober.py`, `tests/unit/test_prober.py` ga —
natijada merge konfliktsiz o'tdi.

Ikki komponent bir-biriga bog'liq bo'lsa (SUT ↔ prober), **avval
spetsifikatsiya muzlatiladi**, keyin ikki tomon **mustaqil** yoziladi. Bu
`docs/architecture/03-sut-protokoli.md` ning mavjudlik sababi: protokol
oldindan muzlatilmasa ikki komponent bir-biriga to'g'ri kelmaydi — va
bir-birining xatosini tasdiqlab qo'yadi.

### Tag'lar

Muzlatilgan hujjatlar tag oladi va tag xabarida `sha256` bo'ladi:

```
v0.1.0-preregistration   P1 pre-registration v1
v0.1.1-preregistration   P1 pre-registration v1.1 (slice naming amendment)
```

`VERSION` faylida loyiha versiyasi (hozir `0.1.0-dev`).

---

## 5. Commit uslubi

`git log` dan o'qilgan haqiqiy naqsh:

```
<type>: <imperative English subject>

<o'zbekcha tana: NIMA o'zgardi va NEGA>

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

**Sarlavha inglizcha va imperativ**, `type:` prefiksi bilan. Ishlatilgan
type'lar: `chore`, `research`, `docs`, `feat`, `merge`.

**Tana o'zbekcha** va quyidagilarni beradi:

1. **O'lchov validligiga tegishli har bir qaror alohida yoziladi.** Commit
   `4b421bb` va `12b478b` shu uslubning misoli: har bir qaror uchun "nega" va
   "busiz nima buzilardi" bor.
2. **Kalibratsiya bilan topilgan xatolar raqami bilan sanaladi** (commit
   `80812b8`: uch xato, har biri o'lchangan sabab va test qulfi bilan).
3. **Tasdiqlangan natijalar "TASDIQLANGAN" / "Verified:" ostida**, faqat
   haqiqatan ishga tushirilgan buyruqdan. Commit `80812b8` "45 unit test
   o'tdi (haqiqatan ishga tushirildi)" deb yozadi — qavs ichidagi izoh
   ataylab.
4. **Pre-registration'ga ta'siri ochiq yoziladi**, hatto "hech narsa
   o'zgarmadi" bo'lsa ham. Bu eng muhim qator, chunki uni yozish
   majburiyati o'zgarishni sezdirmasdan o'tkazishni imkonsiz qiladi.
5. **Eksperiment holati:** "Hech qanday eksperiment ishga tushirilmadi. Hech
   qanday natija yo'q." — natija paydo bo'lmaguncha shunday qoladi.

> ⚠️ Commit xabaridagi raqamlar o'sha branch'dagi holatni aks ettiradi.
> `12b478b` "full unit suite 85 pass" deydi — bu merge'dan **oldingi** son.
> Merge'dan keyin 102. Shu sababli hujjatlarda test soni **commit
> xabaridan ko'chirilmaydi** ([`TESTING.md`](TESTING.md) §1).

---

## 6. Kod uslubi (uy qoidalari)

### Til

| Nima | Til |
|---|---|
| Izohlar, docstring'lar | **o'zbekcha (lotin)** |
| Identifikatorlar (funksiya, o'zgaruvchi, class, field) | **inglizcha** |
| Test funksiyalari nomlari | **o'zbekcha va tavsifiy** (`test_yangi_invocation_bilan_progress_reset_no_progress_EMAS`) |
| Record `record_type`, enum qiymatlari, CSV ustunlari | **inglizcha** (ular ma'lumot sxemasi, tarjima qilinmaydi) |
| Commit sarlavhasi | inglizcha; tanasi o'zbekcha |
| Standart texnik atamalar | inglizcha holatda qoldiriladi: cgroup, systemd, PSI, watchdog, commit, branch, socket, throughput, timeout, disposition |

### Eng muhim qoida: *nega* yoziladi

O'lchov validligini himoya qiluvchi har qanday kod **nega** bilan birga
yoziladi, va tercihan **busiz nima buzilardi** bilan. Sababsiz qoida
keyinchalik "soddalashtirib" yo'q qilinadi — va u yo'q qilinganda hech kim
nima yo'qolganini bilmaydi.

Repo'dagi namuna — [`revix/prober.py`](revix/prober.py) modul
docstring'idagi 1-qoida (parcha):

```
  1. **Absolut `CLOCK_MONOTONIC` deadline'lar.** `sleep(P)` ISHLATILMAYDI:
     u har tsiklda probe'ning o'z vaqtini (connect + round-trip + serializatsiya)
     davrga qo'shadi, ya'ni haqiqiy davr P dan katta bo'ladi va xato YIG'ILADI.
     `D_probe` ±P kvantlash bilan beriladi (§6.1) -- agar davr sekin-asta
     siljisa, kvantlash chegarasi yolg'on bo'lardi.
```

Naqsh: **qoida → mexanizm → busiz qanday buzilardi → qaysi bandga tegishli.**

### Amaliy konvensiyalar

- **Modul docstring'i "DIZAYN QOIDALARI (buzilmaydi)" ro'yxatini beradi.**
  `guard.py`, `prober.py`, `sut.c` shunday yozilgan. Yangi o'lchov moduli ham
  shunday yoziladi.
- **Muzlatilgan hujjatga havola aniq bandga qiladi**: `PREREGISTRATION.md §4`,
  `docs/architecture/03-sut-protokoli.md §8`. "Hujjatda yozilgan" degan
  havola yaroqsiz.
- **Kalibratsiya bilan aniqlangan har bir raqam manba bilan**: qayerda
  o'lchanganini ko'rsatuvchi izoh (`# Ko'ring:
  docs/architecture/02-guard-kalibratsiyasi.md`). Chegarani taxmin bilan
  qo'ymang; taxmin bo'lsa uni "taxmin" deb yozing.
- **Yopiq enum yopiq qoladi.** Yangi holat qo'shish — sxema o'zgarishi, ya'ni
  `SCHEMA_VERSION` va (agar u ta'rifga tegsa) pre-registration amendment
  masalasi.
- **`None` va `0` aralashtirilmaydi.** `None` = o'lchanmadi; `0` = nol
  o'lchandi. `CsvWriter` `None` ni bo'sh maydon qiladi.
- **Istisno o'lchov tsiklini to'xtatmaydi**, lekin **jim ham qolmaydi**:
  `harness_error` record'i yoziladi va hisoblagichga tushadi.
- **`from __future__ import annotations`** har Python modulida (mavjud
  uslubga mos).
- **Yangi bog'liqlik qo'shilmaydi.** `PREREGISTRATION.md` §10.3 statistikani
  o'zimiz yozishni belgilaydi: "Self-contained artifact reviewer uchun
  tejalgan mehnatdan qimmatroq." `statsmodels`/`lifelines` **ishlatilmaydi**.
- **Type hint'lar** Python modullarida ishlatiladi (mavjud kodga mos), lekin
  type checker majburiy emas.

### `.gitignore` bo'ysunadigan narsalar

`__pycache__/`, `.pytest_cache/`, C build artefaktlari (`revix/sut`, `*.o`),
ish fayllari (`*.pid`, `/run/`, `/tmp/`), `.env`.

> **`datasets/` raw ma'lumoti QO'LDA commit qilinadi** (`.gitignore` izohi).
> `*.zst` ignore qilinadi, demak raw arxivni qo'shish ataylab ongli qadam.

---

## 7. Muzlatilgan hujjatlar — amendment tartibi

**Muzlatilgan hujjat jimgina tahrirlanmaydi. Hech qachon.**

Muzlatilgan hujjatlar:

| Hujjat | Versiya nomi |
|---|---|
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | `preregistration/v1.1` |
| [`docs/architecture/03-sut-protokoli.md`](docs/architecture/03-sut-protokoli.md) | `sut-protocol/v1` |

`PREREGISTRATION.md` har eksperiment run'iga `run_meta.preregistration_sha256`
orqali bog'lanadi. Fayl o'zgarsa hash o'zgaradi, ya'ni **qaysi ta'riflar
ostida o'lchangani har doim aniqlanadi.**

Tekshirish (hozir mos keladi):

```bash
$ sha256sum PREREGISTRATION.md
ff4233e1a5e60fcf4cdc75d07bf7871a6dbec688b6b5e5f38fc98b5acab1c966  PREREGISTRATION.md
```

Bu qiymat faylning o'z Amendment log'idagi v1.1 hash'i va
`v0.1.1-preregistration` tag xabaridagi hash bilan bir xil.

### Amendment protsedurasi

1. O'zgarishni fayl boshidagi **Amendment log** ga yozing: sana, sabab, nima
   o'zgardi, **nima o'zgarMAdi**, va o'sha paytdagi yig'ilgan ma'lumot holati.
2. **Versiyani oshiring** (`v1` → `v1.1`).
3. **Oldingi versiyaning `sha256` ini va git tag'ini saqlang.**
4. Yangi tag qo'ying, tag xabarida yangi `sha256`.
5. Commit tanasida amendment **nega qonuniy** ekanini asoslang.

`v1 → v1.1` amendment'i namuna: u faqat slice **nomlarini** o'zgartirdi, hech
bir ta'rif/chegara/metrika/statistik test/falsifikatsiya mezoniga tegmadi, va
o'sha paytda **hech qanday ma'lumot yig'ilmagan edi.**

### Ma'lumot yig'ilgandan keyin

> Agar ma'lumot yig'ilgandan keyin o'zgarish kerak bo'lsa —
> **eski ma'lumot eski ta'riflar ostida qayta hisoblanadi**, yangi ta'riflar
> ostida emas (`PREREGISTRATION.md` Amendment log).

`03-sut-protokoli.md` uchun ham xuddi shunday: *"Bu faylni hech bir
implementatsiya o'zgartirmaydi — nomuvofiqlik topilsa, avval shu fayl
yangilanadi va ikkala tomon moslashtiriladi."*

---

## 8. Ish tartibi — yangi o'lchov moduli qo'shish

1. **O'qing:** [`PREREGISTRATION.md`](PREREGISTRATION.md) ning tegishli
   bandi, [`ARCHITECTURE.md`](ARCHITECTURE.md), va o'xshash mavjud modul
   (`prober.py` yoki `guard.py`).
2. **Modul docstring'ida** qaysi bandni amalga oshirayotganingizni va
   "DIZAYN QOIDALARI (buzilmaydi)" ro'yxatini yozing.
3. **Yopiq enum'larni** boshidan belgilang.
4. **Testni kod bilan birga** yozing, va o'lchov validligini himoya qiluvchi
   har bir qoida uchun alohida **regressiya qulfi** qo'ying.
5. **Ishga tushiring:** `python3 -m pytest tests/unit/ -q`.
6. **Commit:** o'lchov validligiga tegishli har qaror tanada, pre-registration
   ta'siri alohida qator, test soni haqiqiy.
7. **Nomuvofiqlik topsangiz — o'zingiz tuzatmang.** Muzlatilgan hujjat bilan
   kod o'rtasida yoki ikki hujjat o'rtasida qarama-qarshilik bo'lsa, uni
   hisobotga chiqaring va hujjatingizda ochiq savol sifatida qayd eting
   ([`ARCHITECTURE.md`](ARCHITECTURE.md) §6 shunday ro'yxat).

---

## 9. Aloqador hujjatlar

- [`INSTALLATION.md`](INSTALLATION.md) — talablar, o'rnatish, mashinani tekshirish
- [`TESTING.md`](TESTING.md) — test strategiyasi, guard testi
- [`SECURITY.md`](SECURITY.md) — xavfsizlik chegaralari va privilegiya yuzasi
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — komponentlar, ma'lumot oqimi, ochiq masalalar
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — ilmiy yaxlitlik qoidalari
- [`docs/research/05-metodologiya.md`](docs/research/05-metodologiya.md) — eksperiment darajalari va yo'l xaritasi
