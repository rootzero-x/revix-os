# CONTRIBUTING — ilmiy yaxlitlikni buzmasdan hissa qo'shish

REVIX ning ilmiy hissasi arxitektura emas, **o'lchov**
([`docs/research/04-novelty-statement.md`](docs/research/04-novelty-statement.md)).
Hissa o'lchov bo'lsa, **ta'riflar mahsulotning o'zi** — demak ta'rifni,
metrikani yoki raqamni ehtiyotsiz o'zgartirish "kichik refactor" emas, balki
mahsulotni buzish.

Shu sababli quyidagi qoidalar **muhokama qilinmaydi**. Ular
[`README.md`](README.md) "Ilmiy yaxlitlik" bo'limi va
[`PREREGISTRATION.md`](PREREGISTRATION.md) ning bevosita davomi.

**Holat:** hech qanday eksperiment ishga tushirilmadi, hech qanday natija
yo'q. Hissa qo'shayotganda hech qanday natijaga ishora qilmang.

---

## 1. Qattiq qoidalar

### 1.1 Muzlatilgan hujjat jimgina tahrirlanmaydi

Muzlatilgan hujjatlar: [`PREREGISTRATION.md`](PREREGISTRATION.md)
(`preregistration/v1.1`) va
[`docs/architecture/03-sut-protokoli.md`](docs/architecture/03-sut-protokoli.md)
(`sut-protocol/v1`).

Har o'zgarish uchun:

1. **Amendment log** ga yozing: sana, sabab, nima o'zgardi, **nima
   o'zgarMAdi**, va o'zgarish paytidagi yig'ilgan ma'lumot holati.
2. **Versiyani oshiring** (`v1` → `v1.1`).
3. **Oldingi versiyaning `sha256` ini va git tag'ini SAQLANG.**
4. Yangi tag qo'ying, tag xabarida yangi `sha256`.
5. Commit tanasida amendment **nega qonuniy** ekanini asoslang.

`PREREGISTRATION.md` har run'ga `run_meta.preregistration_sha256` orqali
bog'lanadi: fayl o'zgarsa hash o'zgaradi, ya'ni qaysi ta'riflar ostida
o'lchangani **har doim** aniqlanadi. Protsedura va hozirgi hash:
[`DEVELOPMENT.md`](DEVELOPMENT.md) §7.

> **Ma'lumot yig'ilgandan keyin o'zgarish kerak bo'lsa — eski ma'lumot eski
> ta'riflar ostida qayta hisoblanadi**, yangi ta'riflar ostida emas.

`03-sut-protokoli.md` uchun: nomuvofiqlik topilsa **avval protokol fayli**
yangilanadi va ikkala implementatsiya (`sut.c`, `prober.py`) moslashtiriladi —
implementatsiya protokolni o'zgartirmaydi.

### 1.2 Ishga tushirilmagan test "o'tdi" deb yozilmaydi

- Test o'tganini faqat **o'zingiz ishga tushirgandan keyin** yozing.
- Test sonini boshqa hujjatdan yoki commit xabaridan **ko'chirmang**.
  (Masala: commit `12b478b` "full unit suite 85 pass" deydi — o'sha son
  merge'dan oldingi holat; hozir 102. [`TESTING.md`](TESTING.md) §1.)
- Ishga tushirilmagan test uchun aniq shakl:
  ***"bu test ishga tushirilmadi, sabab: …"***
- Skip qilingan test "o'tgan" emas. `tests/unit/test_sut.py` C toolchain
  bo'lmasa butun modul bilan skip qiladi — bu holat ko'rinadi va shunday
  yozilishi kerak.
- **Guard tasdiqlanmasa hech qanday pressure eksperimenti ishga
  tushirilmaydi** (`docs/architecture/00-pilot-topologiya.md` §6).

### 1.3 Sitat, natija va benchmark raqami to'qib chiqarilmaydi

- **Sitat faqat tekshirilgan manbalarga.**
  [`docs/research/02-related-work.md`](docs/research/02-related-work.md)
  tekshirish darajalarini belgilaydi: **T1** — sahifani o'zim ochdim
  (sitat mumkin); **T2** — URL bor, lekin o'zim ochmadim (maqoladan oldin T1
  ga ko'tarilishi shart); **T3** — tasdiqlanmagan, **sitat qilinmaydi**.
- **Mavjud bo'lmagan manbani sitat qilish — ilmiy noxushlik.** Bu formalizm
  emas, taqiq.
- **Benchmark raqami yoki o'lchov natijasi o'ylab topilmaydi.** Har raqam
  qayerda o'lchanganini ko'rsatuvchi havola bilan keladi (masalan
  `docs/architecture/02-guard-kalibratsiyasi.md` §4).
- **Manfiy natijalar yashirilmaydi**, va manfiy da'volar `PRELIMINARY` deb
  belgilanadi. "PSI recovery qarorida ishlatilmagan" — hozircha
  **preliminary**; tizimli adabiyot qidiruvi bajarilmaguncha "birinchi marta"
  deb **yozilmaydi** (`02-related-work.md` oxiri).
- Da'vo kuchi darajalanadi: **FAKT / GIPOTEZA / NATIJA / TALQIN / CHEKLOV**
  ochiq ajratiladi (`04-novelty-statement.md` oxiridagi jadval namuna).

### 1.4 Raw ma'lumot append-only

- `datasets/` **append-only**: raw eksperiment ma'lumoti hech qachon ustiga
  yozilmaydi yoki tahrirlanmaydi. Hech qachon, hech qanday sababga ko'ra.
- Yozuvchilar shuni ta'minlaydi: `JsonlWriter` `O_APPEND` bilan ochadi,
  oldindan serializatsiya qilingan **bitta** `write()` qiladi va `fsync` ni
  **davriy** bajaradi (har qatorda fsync o'lchanayotgan tizimga IO kiritardi)
  — [`revix/schema.py`](revix/schema.py).
- Xato topsangiz — raw'ni **tahrirlamang**. Xatoni derived qatlamda yoki
  validator/reducer'da hisobga oling va nima qilganingizni yozib qoldiring.
- **Derived ma'lumot regenerable**: reducer uni raw'dan qayta yaratadi va
  alohida fayllarda saqlaydi. Derived faylni o'chirish xavfsiz; raw faylni
  tahrirlash — yaxlitlik buzilishi.
- Sensitivity sweep (`W_stab × θ`) **raw trace'lardan post-hoc** hisoblanadi,
  eksperiment qayta ishga tushirilmaydi (`PREREGISTRATION.md` §4). Shu sabab
  raw trace'lar saqlanishi majburiy.
- **Trial jimgina chiqarib tashlanmaydi.** Har trial'ga yopiq enum'dan aynan
  bitta disposition (`complete`, `censored`, `contaminated`, `aborted_guard`,
  `washout_timeout`, `harness_error`), va **eksklyuziya darajasi natija
  sifatida beriladi** (`PREREGISTRATION.md` §12).

### 1.5 🚨 PSI failure, VR yoki FR ta'rifiga KIRMAYDI

**Bu loyihadagi eng muhim bitta qoida.** PSI faqat **prediktor / kovariata**.

Boshlang'ich loyiha spetsifikatsiyasidagi FR ta'rifi — *"host memory
exhaustion sababli ishdan chiqqan xizmatni restart qilish"* — aynan tuzoq.

#### Nega: markaziy gipoteza tavtologiyaga aylanadi

H1 shunday deydi:

```
P(verified recovery | high PSI)  <<  P(verified recovery | low PSI)
```

Agar PSI failure, verified recovery yoki false recovery **ta'rifiga** kirsa,
u holda tenglikning ikki tomonida bir xil o'zgaruvchi turadi. "PSI gating FR
ni kamaytiradi" degan xulosa **ta'rifdan** kelib chiqadi, ma'lumotdan emas —
ya'ni **tavtologiya**, natija emas. Butun hissa shu bilan yo'qoladi, va
reviewer buni birinchi topadi.

Shuning uchun to'rt kafolat muzlatilgan (`PREREGISTRATION.md` §5) va maqolada
ochiq yoziladi:

1. **PSI failure, VR yoki FR ta'rifiga kirmaydi** — faqat prediktor sifatida.
2. **O'lchov prober'i hech bir arm'ning qaror yo'liga ulanmaydi**, uchala
   arm'da bir xil ishlaydi, probe narxi arm'lar bo'yicha bir xil. (Arm C
   probe'ga muhtoj bo'lsa — u **alohida** process bo'ladi.)
3. `W_stab`, `θ`, `p_min` oldindan muzlatilgan; sensitivity sweep e'lon
   qilingan.
4. **FR-A birlamchi va oracle-free; FR-B ikkilamchi va "matrix-relative"** deb
   belgilanadi.

#### Amalda bu nimani taqiqlaydi

| ❌ Qilinmaydi | Nega |
|---|---|
| VR shartlariga PSI chegarasi qo'shish | tavtologiya (yuqoriga qarang) |
| `F_probe` yoki `F_sd` detektoriga PSI ni kiritish | failure ta'rifi PSI'ga bog'lanib qoladi |
| FR-A ni "pressure ostidagi restart" deb ta'riflash | aynan boshlang'ich tuzoq |
| `psi_sampler` chiqishini prober yoki VR hisobiga ulash | shuning uchun ular alohida jarayon |
| Prober'ni arm'ning qaror yo'liga ulash | kafolat 2 |

VR faqat **contract** asosida ta'riflanadi (socket accept, javob formati va
deadline'i, `progress` qat'iy o'sishi, `InvocationID`/`NRestarts`
o'zgarmasligi, throughput ≥ θ·R_ref, `oom_kill` yo'qligi, guard
ishlamaganligi) — `PREREGISTRATION.md` §2 va §4. PSI bu ro'yxatda **yo'q** va
qo'shilmaydi.

`Repairs()` kalibratsiyasi ham VR dan foydalanadi (contract asosida,
oracle-free), demak u yerda ham sirkulyarlik yo'q
(`PREREGISTRATION.md` §5).

---

## 2. Ilmiy yaxlitlikning qolgan qoidalari

Bular [`README.md`](README.md) dan, to'liq kuchda:

- **FAKT / GIPOTEZA / NATIJA / TALQIN / CHEKLOV** ochiq ajratiladi.
- Ta'riflar natijani ko'rgandan **oldin** muzlatiladi va hash bilan run'ga
  bog'lanadi.
- Eksklyuziya darajasi **natija sifatida** beriladi.
- Manfiy natijalar yashirilmaydi.

Qo'shimcha, `PREREGISTRATION.md` dan:

- **`t-test` ishlatilmaydi, `mean ± SD` berilmaydi** downtime taqsimotlari
  uchun (§10.2). Ular og'ir dumli, ehtimol bimodal va o'ngdan censored.
- **Cox / hazard ratio Schoenfeld residual'lari tekshirilmasa berilmaydi**
  (§10.2).
- **Recovery bo'lmagan trial'lar tashlanmaydi** — censored trial'lar
  Kaplan–Meier / log-rank va loop-rate metrikasiga **kiradi** (§6.2).
- **Ahamiyatlilik uchun scope bo'ylab "shopping" qilinmaydi** — reviewer
  taqqoslashlarni sanaydi; Holm korreksiyasi qo'llanadi (§7, §10.4).
- **P1 ma'lumotlari confirmatory analizga qo'shilmaydi** (§13) — garden of
  forking paths.

---

## 3. Nomuvofiqlik topsangiz

**O'zingiz tuzatmang.** Muzlatilgan hujjat bilan kod o'rtasida yoki ikki
hujjat o'rtasida qarama-qarshilik bo'lsa:

1. **Xabar bering** (hisobot, issue yoki PR tavsifi).
2. **O'z hujjatingizda ochiq savol sifatida qayd eting** — namuna:
   [`ARCHITECTURE.md`](ARCHITECTURE.md) §6 dagi jadval.
3. **Hujjatni jimgina "to'g'rilab" qo'ymang.** Muzlatilgan hujjatga tegish
   amendment protsedurasini talab qiladi (§1.1), va tegishli qaror
   kalibratsiya bilan o'lchangan bo'lishi mumkin — ya'ni hujjat emas, sizning
   taxminingiz xato bo'lishi ehtimoli bor.

Hozirda ochiq nomuvofiqliklar ro'yxati:
[`ARCHITECTURE.md`](ARCHITECTURE.md) §6.

---

## 4. Kod hissasi uchun kontrol ro'yxati

O'zgarish yuborishdan oldin:

- [ ] `python3 -m pytest tests/unit/ -q` ishga tushirildi va o'tdi; son
      hisobotda **haqiqiy**.
- [ ] `make -C revix all` `-Werror` bilan ogohlantirishsiz o'tdi (agar
      `sut.c` ga tegilgan bo'lsa).
- [ ] O'lchov validligini himoya qiluvchi har bir qoida uchun **regressiya
      qulfi** (test) bor.
- [ ] Izohlar va docstring'lar **o'zbekcha**, identifikatorlar **inglizcha**
      ([`DEVELOPMENT.md`](DEVELOPMENT.md) §6).
- [ ] O'lchov validligiga tegishli har bir qaror uchun **nega** yozilgan, va
      tercihan **busiz nima buzilardi**.
- [ ] Muzlatilgan hujjatga havola **aniq bandga** qiladi.
- [ ] Yangi bog'liqlik **qo'shilmadi** (`PREREGISTRATION.md` §10.3).
- [ ] Yopiq enum'lar yopiq qoldi; qo'shilgan bo'lsa `SCHEMA_VERSION` va
      amendment masalasi ko'rib chiqildi.
- [ ] `None` va `0` aralashtirilmadi (`None` = o'lchanmadi).
- [ ] Muzlatilgan hujjat o'zgargan bo'lsa — amendment log, versiya, eski hash,
      yangi tag (§1.1).
- [ ] Commit sarlavhasi inglizcha imperativ + `type:` prefiksi; tanasi
      o'zbekcha; pre-registration ta'siri alohida qator; trailer
      `Co-Authored-By:` ([`DEVELOPMENT.md`](DEVELOPMENT.md) §5).
- [ ] Hech qanday natija yoki eksperiment da'vo qilinmadi — hozircha
      **hech biri yo'q**.

---

## 5. Aloqador hujjatlar

- [`PREREGISTRATION.md`](PREREGISTRATION.md) — muzlatilgan shartnoma (§5 sirkulyarlik kafolatlari, §12 disposition)
- [`README.md`](README.md) — loyiha framing'i va ilmiy yaxlitlik qoidalari
- [`docs/research/02-related-work.md`](docs/research/02-related-work.md) — T1/T2/T3 tekshirish darajalari
- [`docs/research/03-research-gap.md`](docs/research/03-research-gap.md) — nima qoplangan, nima qolgan, halol zaifliklar
- [`docs/research/04-novelty-statement.md`](docs/research/04-novelty-statement.md) — hissa nima va nima emas
- [`DEVELOPMENT.md`](DEVELOPMENT.md) — kod uslubi, branch, commit, amendment protsedurasi
- [`TESTING.md`](TESTING.md) — test strategiyasi va "tasdiqlangan" so'zining ma'nosi
- [`SECURITY.md`](SECURITY.md) — xavfsizlik chegaralari
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — komponentlar va ochiq nomuvofiqliklar
