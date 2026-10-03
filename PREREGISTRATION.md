# REVIX — Pre-registration: PSI Pilot (P1)

| | |
|---|---|
| **Versiya** | `preregistration/v1.11` |
| **Holat** | MUZLATILGAN — kod yozishdan oldin commit qilindi |
| **Qamrov** | Faqat **pilot eksperiment P1**. Confirmatory eksperiment alohida pre-registration talab qiladi. |
| **Muzlatilgan sana** | 2026-09-29 (v1, v1.1, v1.2, v1.3) · 2026-10-02 (v1.4, v1.5, v1.6) · 2026-10-03 (v1.7, v1.8, v1.9, v1.10, v1.11) |
| **Muhit** | Bu pre-registration **§15.1 va §16.11 da qayd etilgan o'lchangan fingerprint** uchun qo'llanadi. |
| **✅ Qaror 1 — QABUL QILINDI (v1.11)** | **§17.5 — dizayn nuqsoni** (stabilizatsiya oynasi pressure hold'ga sig'maydi) → **O3**: `hold_cap_s` **12 s → 13 s**. Orkestrator, egasining 2026-10-03 dagi ochiq delegatsiyasi bo'yicha. Asos, narx va cheklovlar: **Amendment log, v1.10 → v1.11** va §17.5. |
| **✅ Qaror 2 — QABUL QILINDI (v1.11)** | **§18.6 — §11 ning fail-slow limbi ishlamaydi** → **F2**: `thr = 0.20 × τ = 1.6 s`, **fiksa**. Orkestrator, o'sha delegatsiya bo'yicha. §18.2 ning `thr = 0.20 × RMST(P0)` o'qishi **bekor qilinadi**. Asos, **bias yo'nalishi** va narx: **Amendment log, v1.10 → v1.11**, §18.6, §18.7. |
| | Ikkala qaror **birinchi pilot trial'idan OLDIN** va **birgalikda** qabul qilindi (tuguni `τ = W_stab_pilot = 8 s`; §18.6, §19.3). **Juftlik izchil:** O3 `W_stab_pilot` ni ham, `τ` ni ham **tegmasdan qoldiradi**, demak §18.6 ning O1 haqidagi ogohligi **yuzaga kelmaydi**. |
| **🔴 Oshkora e'lon (v1.11)** | **Ikkala tanlov ham KALIBRATSIYA MA'LUMOTI KO'RILGANDAN KEYIN qabul qilindi.** P1 trial'i o'tkazilmagan, lekin `10-pressure-dozalash.md` ning o'lchovlari tanlov paytida **qo'lda edi**, va F2 holatida nomzod chegaralar **o'lchangan `P2 − P0` farqiga nisbatan** taqqoslandi. §17.6 va §18.7 ning *“ma'lumot mavjud emas”* kafolati **v1.11 ga O'TMAYDI** — Amendment log, v1.10 → v1.11, **0-band**. |
| **⛔ Gate** | **§21.7 — generator §9.4 ning ikki invariantini majburlamaguncha hech qanday pilot trial o'tkazilmaydi** (o'lchangan: 5 s so'rov → 16.3 s epizod). |

Bu fayl `run_meta.preregistration_sha256` orqali har bir eksperiment run'iga bog'lanadi.
Fayl o'zgarsa — hash o'zgaradi, ya'ni qaysi ta'riflar ostida o'lchangani har doim aniqlanadi.

---

## Amendment log

Pre-registration **jimgina tahrirlanmaydi.** Har bir o'zgarish shu yerda
qayd etiladi, versiya oshiriladi, va oldingi versiyaning hash'i saqlanadi.
Shunda qaysi ta'riflar ostida o'lchangani har doim tekshirilishi mumkin.

### v1.10 → v1.11 (2026-10-03)

| | |
|---|---|
| **v1.10 sha256** | `5c5d0dd9c3a0661cd658e678cb44c34214a7497ba6b65d78b7830284177436d8` |
| **v1.10 git tag** | `v0.1.10-preregistration` |
| **Sabab** | Sarlavhadagi **ikki ochiq qaror** — §17.5 (O1–O4) va §18.6 (F1–F4) — qabul qilindi. Ikkisi ham **birinchi pilot trial'idan OLDIN** talab qilingan edi, va `docs/architecture/10-pressure-dozalash.md` ning **kalibrlangan dozadagi** o'lchovlari ikkisining ham **zarurligini** tasdiqladi |
| **Qarorni kim qabul qildi** | **Orkestrator**, loyiha egasining **2026-10-03 dagi ochiq delegatsiyasi** bo'yicha. §17.5 va §18.6 tanlovni *"loyiha egasiga"* qoldirgan edi; delegatsiya shu huquqni orkestratorga o'tkazdi va bu shu yerda qayd etiladi |
| **O'zgardi** | **(1) `hold_cap_s`: 12 s → 13 s** — §9.4 invariant 1, §4 ning `W_stab_pilot` izohi, §9.4 ning kampaniya arifmetikasi (52 → 53 s). **(2) §11 ning fail-slow limbining CHEGARASI** — referens `RMST(P0)` dan **`τ`** ga o'tdi ⇒ `thr = 0.20 × τ = 1.6 s`, **fiksa**; §18.2 ning o'qishi **bekor qilinadi**. **(3) `ramp_above_threshold_s`: eskirgan TAXMIN `3.0 s` → **o'lchangan** `0.000 s`** (3-band — bu **qaror emas**, §9.4 ning o'z talabining bajarilishi). **(4) §0 ning *“12 sekunddan uzoq sustained pressure”*** bandi **cap'ni kuzatadigan** shaklga keltirildi (1.11-band) — aks holda hujjat **o'zining birinchi sahifasida o'ziga zid** bo'lardi. §17.5 va §18.6 qaror qayd etilgan holda qayta yozildi — **O1–O4 va F1–F4 jadvallari SAQLANDI** |
| **O'zgarMADI** | **hech bir metrika ta'rifi, statistik test, arm, fault klassi, probe parametri, VR ta'rifi, FR ta'rifi, `disposition` enum'i, va fail-slow limbining chegarasidan BOSHQA hech bir falsifikatsiya mezoni.** To'liq ro'yxat 5-bandda |
| **Yig'ilgan ma'lumot** | **P1 trial'i ma'lumoti — YO'Q:** hech qanday trial o'tkazilmagan, demak **eski ta'riflar ostida qayta hisoblanadigan endpoint yo'q** (`DEVELOPMENT.md` §7 ning *"ma'lumot yig'ilgandan keyin"* qoidasi qo'llanmaydi). **LEKIN kalibratsiya o'lchovlari MAVJUD edi** — 0-bandni ko'ring |

**0. 🔴 OSHKORA E'LON — BU IKKI QAROR MA'LUMOT KO'RILGANDAN KEYIN QABUL QILINDI.**

§17.6 va §18.7 — o'z qarorlarini (v1.6 va v1.7 da) himoya qilib — shunday
yozgan edi: *"Qaror hech qanday ma'lumot mavjud bo'lmaganda qabul qilinadi,
demak natijani ko'rib tanlash imkoniyati yo'q."* **O'sha kafolat v1.11 ga
O'TMAYDI, va buni footnote emas, OSHKORA E'LON sifatida yozaman.**

- **O1–O4 va F1–F4 tanlovi `10-pressure-dozalash.md` ning o'lchovlari
  QO'LDA bo'lgan holda qilindi.** Qaysi variant qaysi o'lchov bilan
  o'tadi — tanlovchiga **ma'lum** edi: `hold_cap_s` ning har bir
  nomzod qiymati `t_start` taqsimotiga nisbatan tekshirildi (1-band), va
  **F1 ning hamda F2 ning chegaralari o'lchangan `P2 − P0` farqiga
  nisbatan taqqoslandi** (2.5-band).
- **Bu aynan shu hujjat oldini olishga qaratilgan xavf sinfi:**
  chegarani o'lchovga qarab tanlash. O'quvchi buni **ko'rishi shart**,
  va shuning uchun u sarlavhada ham turadi.
- **Nima bu xavfni CHEKLAYDI** (bekor qilmaydi, faqat chegaralaydi):
  **(i)** hech qanday **P1 trial'i** o'tkazilmagan, demak **birlamchi
  endpoint** (`P(VR)`), `Δ`, CI va p-qiymat **ko'rilmagan** — ko'rilgan
  narsa kalibratsiya proxy'lari (`t_start`, `D_probe` proxy),
  gipotezaning natijasi **emas**; **(ii)** ikkala qarorning **bias
  yo'nalishi** ochiq e'lon qilinadi (1.7, 2.10-bandlar), va F2 ning
  bias'i **loyihaning o'z tezisiga QARSHI**; **(iii)** qaror
  hujjatning **o'zi** majburiy qilgan va **o'zi sanab bergan** to'rt
  variantdan tanlangan — yangi variant **ixtiro qilinmagan**;
  **(iv)** rad etilgan variantlarning jadvallari **saqlandi**, demak
  tanlov **tekshirilishi** mumkin.
- **Nima bu xavfni CHEKLAMAYDI:** F2 ning tanlovi `thr` ni o'lchangan
  farqning **qaysi tomoniga** tushirishini bilib turib qilindi
  (2.5-band: farq F1 ning chegarasidan **katta**, F2 ning chegarasidan
  **kichik**). **Ya'ni ikki konvensiya o'lchangan farqning qarama-qarshi
  tomonlarida turadi, va tanlovchi buni KO'RGAN.** Shuning uchun F2 ni
  *"matn shunday deydi"* deb emas, **"F1 ning inkor shoxi asbobning
  kvantlash polidan past"** deb asoslayman — 2-band — va bias'ni
  2.9 da ochiq e'lon qilaman.

> **Maqolada shunday yoziladi:** *"§9.4 ning `hold_cap_s` i va §11 ning
> fail-slow chegarasi pilotning birinchi trial'idan oldin, lekin
> **dozalash kalibratsiyasining natijalari ko'rilgandan keyin**
> muzlatilgan; ikkala tanlovning bias yo'nalishi pre-registration'da
> oldindan e'lon qilingan."*

**1. QAROR 1 — §17.5 O3 bo'yicha hal qilindi: `hold_cap_s` 12 s → 13 s.**

**(1.1) §17.2 ning arifmetikasi, 12 s da.** Oyna hold ichida bo'lishi
sharti `t_up + W_stab_pilot ≤ t_h + hold_cap_s`, injeksiya `t_h + 3` da
⇒ `t_up − t_inject ≤ hold_cap_s − 11`. Budjet taqsimoti:
`RestartSec (0.1) + t_start + probe kvantlashi (0.1)`, demak
**`t_start ≤ hold_cap_s − 11 − 0.2`**. `hold_cap_s = 12 s` da bu
**`t_start ≤ 0.8 s`** — §17.2 ning o'z raqami.

**(1.2) §17.5 ning qochish bandi QO'LLANMAYDI.** §17.5 shunday yozgan:
*"`p90(t_start) ≤ 0.8 s` bo'lsa — nuqson amalda bezarar va O1–O4 kerak
emas."* O'lchangan (`10` §6.2, §6.5; **kalibrlangan** doza, `base_mb=184`):

| band | n | **p90** | p99 | max | `≤ 0.8 s` | qochish bandi |
|---|---|---|---|---|---|---|
| `P0` (generator yo'q) | 30 | **0.0481** | 0.0555 | 0.0576 | **30/30** | qo'llanadi |
| **`P1`** (kalibrlangan) | 24 | **0.9543** | **1.3948** | **1.4807** | **19/24** | **QO'LLANMAYDI** |
| `P2` (kalibrlangan) | 24 | **0.7863** | 1.1211 | 1.1883 | 22/24 | harfan qo'llanadi, **1.7% zaxira** |
| **`P1 + P2`** | 48 | **0.9105** | 1.3433 | 1.4807 | **41/48** | **QO'LLANMAYDI** |

`P1` budjetni **19.3%** ga, birlashtirilgan 48 namuna **13.8%** ga
oshiradi. `P2` ning 1.7% zaxirasi esa `10` §12.4 ning o'z hukmi bilan
**o'lchov shovqinidan kichik** (`n = 24`, va `P1` ning p90 i `P2` dan
**yuqori** chiqqan — monotonlikning buzilishi). §9.3 `P1` ni
**to'laqonli yacheyka** qiladi (`3 × 2 × 20` dizaynining uchdan biri),
demak `P1` da buzilgan invariant **butun dizaynni** qamrab oladi.

> **Demak qaror MAJBURIY, va §17.5 ning o'z shartiga ko'ra u birinchi
> pilot trial'idan OLDIN qabul qilinishi kerak edi.** Shu bajarildi:
> hech qanday trial o'tkazilmagan.

**(1.3) 13 s da arifmetika, va QAYSI budjet `P1` ni boshqaradi.**
`hold_cap_s = 13 s` da `t_up − t_inject ≤ 2 s` ⇒ **`t_start ≤ 1.8 s`**.

§17.2 ning **gate qilingan** varianti (`+D_f = 300 ms` ⇒ `t_start ≤ 1.5 s`)
**shartli**: u *"agar action `F_probe` ga gate qilinsa"* deb yozilgan.
§9.3 P1 ning arm'larini muzlatadi: **`A`** (`Restart=on-failure`,
`RestartSec=100ms` — restart'ni **systemd o'zi** qiladi, yo'lda harness
qarori yo'q) va **`no_action`** (`Restart=no`). **Ikkisi ham `F_probe` ga
gate qilinmagan.** Probe'ga gate qilingan aktor — **arm C**, va §13 uni
**muzlatmaydi** va bu pilotdan **tashqarida** qoldiradi.

> **Demak `P1` ni boshqaradigan budjet — GATE QILINMAGAN budjet: 1.8 s.**

| band | p99 | budjetgacha (1.8 s) | max | budjetgacha |
|---|---|---|---|---|
| `P1` (hal qiluvchi band) | **1.3948 s** | **22% pastda** | **1.4807 s** | **18% pastda** |
| `P2` | 1.1211 s | 38% pastda | 1.1883 s | 34% pastda |
| `P0` | 0.0555 s | 97% pastda | 0.0576 s | 97% pastda |

**78 urinishning 78 tasi** `1.8 s` budjeti ichida (eng katta o'lchangan
`t_start = 1.4807 s`, `10` §6.2 / §10.1).

**Va §17.2 ning asosiy e'tirozi son bilan toraytiriladi.** §17.2:
*"`0.8 s < t_start < 10 s` bo'lgan har qanday 'muvaffaqiyatli' restart,
verifikatsiya oynasi pressure'dan **chiqib ketgan** restart'dir."*
O'lchangan (`10` §10.1): o'sha oraliqqa `P1` da **5/24**, `P2` da
**2/24** urinish tushadi — ya'ni `12 s` da **7/48**. `13 s` da oraliq
`1.8 s < t_start < 10 s` ga aylanadi va unga **0/48** urinish tushadi.

**(1.4) Nega aynan 13 s.** **Minimal o'zgarish — printsipial sabab, va u
har qanday zaxira argumentidan kuchliroq:** muzlatilgan qiymat
**kerak bo'lgan eng kichik qadamga** siljitiladi.

- **12.5 s ishlamaydi:** budjet `12.5 − 11 − 0.2 = 1.3 s`, `P1` ning
  o'lchangan max'i **1.4807 s** undan **oshadi**.
- **13 s ishlaydi:** budjet **1.8 s**, 78/78 ichida (yuqoriga qarang).
- **15 s tanlanMAYDI**, garchi `10` §6.5 uni ruxsat etilgan deb
  ko'rsatgan bo'lsa ham: `15 + 0.000 = 15 ≤ 15` — invariant 2
  **tenglik bilan** qanoatlanadi, ya'ni **nol zaxira**. 13 s esa
  **2.000 s** zaxira qoldiradi.

**(1.5) §9.4 invariant 2 buzilMAYDI — O'LCHANGAN.** `10` §4.1:
`ramp_above_threshold_s` = **0.000 s**, **29 epizoddan 29 tasida**,
**haqiqiy** dozada (`base_mb = 184`, `step_mb = 4`, `MemoryHigh = 192M`;
erishilgan doza p50 `0.223 .. 0.921`; ramp tezligi `min = p50 = max =
0.0000`).

```
hold_s + ramp_above_threshold_s <= guard_sustain_s
13 + 0.000 = 13.000  <=  15     ✓   zaxira 2.000 s
```

§17.5 O3 uchun **ikki shart** qo'ygan edi: invariant 2 **qayta
tekshirilsin** va guard **qayta kalibratsiya qilinsin**. Birinchisi
bajarildi (yuqoridagi o'lchov). Ikkinchisi — `10` §4.2 va §6.5 ga
ko'ra **kerak emas**: guard'ning `sustain_max_seconds = 15.0` va
`sustain_rate_threshold = 0.35` **o'zgarmaydi**, chunki
`ramp_above_threshold_s = 0` bo'lgani uchun sustain taymeri faqat hold
ichida boshlanishi mumkin, va `base_mb=184` ning **29 epizodida
`sustained_pressure` trip'i YO'Q**.

**(1.6) §15.3 ning IKKI sababi ham javob oladi.** §15.3 `hold_cap_s = 12 s`
ni **ikki mustaqil yetarli** sabab bilan saqlagan edi:

1. *"Ular muzlatilgan qiymatlar. Pre-registration qulaylik uchun
   bo'shashtirilmaydi."* — **rad etilmaydi, QO'LLANMAYDI.** Bu
   bo'shashtirish **qulaylik uchun emas**: §17.5 ning o'zi to'rt
   muzlatilgan qiymatning **birgalikda qanoatlantirilmasligini** e'lon
   qilgan va qarorni **majburiy** qilgan; o'lchov esa nuqsonning
   `P1` da **haqiqatan** yuzaga kelishini ko'rsatdi. (Bu **ma'lumotga
   tayangan** amendment — 0-bandning oshkora e'loni shu yerga ham
   tegishli.)
2. *"12 s — endi shartnomaviy arifmetika: `injection_offset (3 s) +
   W_stab_pilot (8 s) = 11 s ≤ 12 s`."* — **o'z kuchida va
   BUZILMADI**: `11 ≤ 13`, zaxira `1 s → 2 s` ga **oshdi**. Demak
   **v1.3 bekor qilinmaydi**; uning ziddiyat yechimi (cheklov faqat
   HOLD ga tegishli, ramp+hold ga emas) **kengroq zaxira bilan**
   saqlanadi: `13 − 5 = 8 < 11`, ya'ni cheklovni ramp+hold ga
   qo'llash hamon ziddiyat beradi.

**(1.7) Asl 12 s ni YARATGAN cheklov bu muhitda endi bog'lamaydi.**
12 s `systemd-oomd` ning 20 s sustained oynasi ostidagi vaqt zaxirasi
sifatida tanlangan (§9.4 invariant 1 ning asl izohi;
`00-pilot-topologiya.md` §3.1 ning *"1-RAQAMLI XAVF"* i). O'lchangan:
`systemd-oomd` **bu mashinada yo'q** (§15.2; binar, unit, config, drop-in
yo'q; `docs/architecture/07-wsl-muhit-tekshiruvlari.md` §6.4, doctor
`oomd` → PASS, *"kill authority YO'Q"*), va u tadqiqot appliance
image'ida ham **ATAYLAB yo'q**: `iso/config.sh` da
`OOMD_INSTALLED="no"`, `iso/20-record-manifest.sh` manifest'da
`systemd-oomd` paydo bo'lsa **build'ni to'xtatadi**, va qurilish
jurnali shuni qayd etgan (`docs/architecture/11-iso-qurilish-jurnali.md`:
*"systemd-oomd: yo'q (ATAYLAB, 09 §4.4)"*).

> **⚠️ CHEKLOV — bu zaxirani OLIB TASHLAYDI, va buni ochiq yozaman.**
> oomd bor muhitda pilotning xavfsizlik argumenti **ikki qatlamli**
> edi: guard **va** oomd. oomd yo'q, va hold 12 s dan 13 s ga chiqdi,
> demak argument endi **faqat guard'ga** tayanadi (§15.3 ning
> *"guard majburiy va fail-closed"* bandi, `02-guard-kalibratsiyasi.md`
> ning oniy chegaralari, §8.4(3) ning fail-closed qoidasi). Qolgan
> xavflar o'z joyida: **kernel global OOM killer** va **runaway
> generator**. Qolaversa image *"oomd armed desktop"* muhitini
> **qayta ishlab chiqarmaydi** (`04-novelty-statement.md` C4), demak
> natijalar oomd ostidagi muhitga **ko'chirilmaydi**.

**(1.8) ⚠️ CHEKLOV — arm C `hold_cap_s = 13 s` ni MEROS QILIB OLMAYDI.**
13 s da **gate qilingan** budjet 1.5 s, va `P1` ning o'lchangan max'i
1.4807 s ⇒ zaxira **0.0193 s = 1.3%**. `10` §12.4 allaqachon **1.7%**
zaxirani *"o'lchov shovqinidan kichik"* deb hukm qilgan, demak 1.3% ham
shunday. Probe'ga gate qilingan arm'ni (arm C, §13) pre-register
qiladigan kishi **§17.2 ning arifmetikasini o'zi uchun qaytadan
bajarishi SHART**. Bu **P1 dagi nuqson emas** — bu **oldinga qaragan
cheklov**.

**(1.9) ⚠️ CHEKLOV — O3 `window_past_pressure` ni KAMAYTIRADI, YO'Q
QILMAYDI.** `t_up − t_inject` uchun ruxsat 12 s da `1.0 s`, 13 s da
`2.0 s`. O'lchangan `D_probe` proxy epizodlari (`10` §7.2, arm `A`,
har bandda n=12) — agar failure injeksiya bilan **bir vaqtda** deb
olinsa, `D_probe ≈ t_up − t_inject`:

| ruxsat | oshgan epizod (`P1 + P2`, n=24) |
|---|---|
| `1.0 s` (12 s) | **5/24** (`P1`: 1.7, 1.1 · `P2`: 1.1, 2.2, 1.6) |
| **`2.0 s` (13 s)** | **1/24** (`P2` ning **2.200 s** li epizodi) |

`P1` ning max'i **1.700 s** (ruxsat ichida), `P2` ning max'i
**2.200 s** — **ruxsatdan oshadi**. Demak:

> **O3 nuqsonni 5/24 dan 1/24 ga tushiradi, lekin YO'Q QILMAYDI.**
> §17.4(4) ning talabi **o'z kuchida va majburiy**:
> `window_past_pressure` darajasi **har `(arm × pressure)` yacheykasi
> bo'yicha ALOHIDA beriladi**, va §12 ning *"yuqori eksklyuziya
> darajasi o'zi natija — yashirilmaydi"* qoidasi qo'llanadi.

**Bu hisob ikki taqribga tayanadi, va ikkisi ham `1/24` ni PAST
baho qiladi:** (i) failure injeksiya bilan bir vaqtda deb olinadi —
toza restart bo'lmagan uzilishlar `t_start` ustiga vaqt **qo'shadi**;
(ii) epizodlar `0.1 s` li probe panjarasida va `±P` kvantlash bilan
(§6.1), demak *"aynan 1.0"* va *"1.0 dan katta"* farqi polning
**ichida**.

**(1.10) Nega O1, O2, O4 emas — har birining narxi §17.5 ning o'z
so'zlari bilan.**

| variant | nega tanlanmadi |
|---|---|
| **O1** (`W_stab_pilot` kichraytiriladi) | §17.5: *"VR da'vosini **kuchsizlashtiradi** — §4 ning 5-bandi (throughput) qisqa oynada kamroq ma'noga ega."* Qolaversa u `τ` ni ham siljitadi (§10.2/§11 da `τ = 8 s` — `W_stab_pilot` bilan **bir xil raqam**), demak **Qaror 2 bilan to'qnashadi** — §18.6 ning o'z ogohligi |
| **O2** (`injection_offset` kichraytiriladi) | §17.5: 3 s *"hold boshidan keyin pressure'ning **barqarorlashuvi** uchun bor; kichraytirish 'o'rnatilgan pressure ostida injeksiya' binosini kuchsizlashtiradi"* — ya'ni **mustaqil o'zgaruvchini confound qiladi** |
| **O4** (oyna pressure'dan chiqishiga ruxsat) | §17.5: §4 ning o'z cheklov izohiga (*"pressure davom etayotganda tasdiqlangan recovery"*) **qarshi** — *"bu raqam emas, **metrikaning ma'nosini** o'zgartiradi, demak eng og'ir variant"* |

> **§17.5 O3 ni o'zi *"yagona variant hech bir ilmiy da'voni
> kuchsizlashtirmaydigan"* deb belgilagan.** O3 shu sababdan tanlandi,
> va uning o'zi qo'ygan ikki sharti (invariant 2 + guard) o'lchov bilan
> **bajarildi** (1.5-band). O3 ning narxi — ta'rif o'zgarishi **va**
> yuqoridagi to'rt CHEKLOV, **ilmiy da'vo emas**.

**(1.11) §0 NING QAMROV BANDI TUZATILDI — aks holda hujjat o'ziga zid
bo'lardi.** §0 (*"Nima o'lchanmaydi"*) P1 hech qanday da'vo qilmaydigan
narsalar orasida **`12 sekunddan uzoq sustained pressure`** ni sanagan edi.
`hold_cap_s = 13 s` da **har bir trial 13 s ishlaydi**, ya'ni §0 ning o'zi
qamrovdan tashqari deb e'lon qilgan rejimda — **birinchi sahifadagi
ziddiyat**.

Band **raqamni almashtirish bilan emas**, **cap'ni kuzatadigan** shaklga
keltirildi, va uning **asl maqsadi saqlandi**: u *uzoq davomiylik rejimini*
chiqarib tashlash uchun bor, ya'ni `W_stab = 60 s` ning to'liq dizayni va
daqiqalar tartibidagi sustained pressure — bular P1 ning qamrovida
**emas** va **bo'lmaydi** (§4 ning *"P1 dagi ochiq cheklov"* i,
§15.5). **Qamrov sinfi o'zgarmadi; chegara 1 s siljidi.**

**2. QAROR 2 — §18.6 F2 bo'yicha hal qilindi: `thr = 0.20 × τ = 1.6 s`, fiksa.**

**(2.1) §18.6 ning qochish bandi QO'LLANMAYDI.** §18.6:
*"Agar `thr ≥ ~5 × P` bo'lsa, 18.4 ning cheklovi amalda bezarar va F1
yetarli."* `P = 100 ms` ⇒ qochish chegarasi **0.5 s**. F1 ostidagi
`thr = 0.20 × RMST(P0)` **ikki mustaqil yo'l** bilan hisoblanadi, va
ikkisi ham bir xil javob beradi:

**(a) O'LCHANGAN** (`10` §7.2, §7.5 — loyihaning o'z prober'i, 10 Hz,
arm `A`, har bandda 12 injeksiya, epizod `invocation_id` o'zgarishi
bo'yicha tasniflangan):

```
D_probe proxy (P0):  n = 12,  hammasi AYNAN 0.300 s  =>  mean 0.3000 s
thr = 0.20 x 0.3000  =  0.0600 s  =  0.60 x P        =>  5P dan 8.3x PAST
```

**(b) CHIQARILGAN** (§18.4 ning muzlatilgan-overhead yo'li:
`D_probe(P0) = t_start + (0.2 … 0.4) s`), o'lchangan
`p50(t_start | P0) = 0.0386 s` (`10` §6.2) bilan:

```
D_probe(P0) ~ 0.2386 .. 0.4386 s   =>   thr ~ 0.048 .. 0.088 s
                                        o'rtasi ~ 0.068 s  =  0.68 x P
```

**(c) Va xulosa `P0` bandining artefakti EMAS** (`10` §7.5, o'lchangan):

| band | referens (`D_probe` proxy `mean`) | `thr = 0.20 × referens` | `P` birligida | `≥ 5P`? |
|---|---|---|---|---|
| `P0` | 0.3000 s | **0.0600 s** | 0.60 × P | ❌ |
| `P1` | 0.8500 s | **0.1700 s** | 1.70 × P | ❌ |
| `P2` | 1.0250 s | **0.2050 s** | 2.05 × P | ❌ |

Eng katta qiymat — `p90(P2)` da **3.10 × P** — ham `5P` dan past.

> **Har uch yo'lda bir xil xulosa: F1 ning INKOR shoxi asbobning o'z
> kvantlash polining OSTIDA qoladi.** §6.1 `D_probe` ning o'zini
> *"±P kvantlash, har chekkada +P/2 bias"* bilan beradi, §7 esa
> *"100 ms delta oniy tezlik deb talqin qilinmaydi"* deb ogohlantiradi.
> **Demak F1 YETARLI EMAS.**

**(2.2) F1 ga qarshi hal qiluvchi dalil.** **Inkor shoxiga erishib
bo'lmaydigan pre-registered falsifikatsiya mezoni — test emas.** U
faqat *"qo'llab-quvvatlanadi"* ni chiqaradigan shtamp bo'ladi, ya'ni
§11 ning fail-slow limbi o'zi e'lon qilgan ishni **qilmaydi**. Bu
§17 ning argumentining aynan o'zi, fail-slow limbiga qo'llangan.

**(2.3) F3 DOMINATSIYA QILINGAN.** (i) U §18.4 ning kvantlash
muammosini **hal qilmaydi** — o'lchangan `P0` taqsimoti **degenerat**:
12 epizodning hammasi aynan `0.300 s`, demak `median = mean = 0.300 s`
va `thr` **o'zgarmaydi** (umumiy holda mediana o'rtachadan **kichik**,
ya'ni chegara yana **kichrayadi**); (ii) §18.6 ning o'zi qo'shimcha
nuqsonni sanaydi: KM medianasi **`nan`** bo'lishi mumkin
(`04-driver-va-analiz-shartnomasi.md` §2.3, 8-band).

**(2.4) F4 emas, lekin F2 — PRINTSIPIAL `k` bilan F4.** §18.6 F4 ni
*"`k` ni tanlash **o'lchov talab qiladi**"* deb hozirga qoldirgan edi.
O'lchov endi bor, lekin **`k` uchun hali ham ankor yo'q**: har qanday
`k × P` tanlovi o'zboshimcha bo'ladi. **F2 — aynan F4, lekin
asoslangan `k` bilan:** u matnning **o'z `0.20` koeffitsientini**
saqlaydi va uni **muzlatilgan qiymat** `τ = 8 s` ga ankorlaydi.

```
thr = 0.20 x tau = 0.20 x 8 s = 1.6 s = 16 x P      =>  kvantlashdan 16x YUQORI
```

**(2.5) F2 ostida IKKALA shox ham erishiladigan — va aynan shu yerda
0-bandning oshkora e'loni eng muhim.** `10` §7.2 ning o'lchangan
`D_probe` proxy **o'rtachalari**: `P0` **0.3000 s**, `P2` **1.0250 s**
⇒ farq **0.7250 s**. Bu:

```
0.7250 / 0.0600 (F1 ning thr i)  ~  12 x      =>  F1: "qo'llab-quvvatlanadi" deyarli avtomatik
0.7250 / 1.6    (F2 ning thr i)  ~  0.45 x    =>  F2: IKKALA shox ham erishiladigan
```

> **⚠️ Bu raqam FAQAT ILLYUSTRATIV, va uch sababdan da'vo emas:**
> **(i)** u `D_probe` **proxy'i**, §10.2 ning Kaplan–Meier egrisidan
> hisoblangan **`RMST` EMAS** (`10` §7.5 ning o'z CHEKLOV'i);
> **(ii)** `n = 12` har bandda; **(iii)** **hech qanday ishonch
> intervali hisoblanmagan**, falsifikatsiya mezoni esa `CI95_upper` ga
> tayanadi. U faqat bitta narsani ko'rsatadi: **ikki konvensiya
> o'lchangan farqning QARAMA-QARSHI tomonlarida turadi** — va
> **shuning uchun 0-bandning post-data e'loni zarur**, chunki
> tanlovchi buni **ko'rgan**.

**(2.6) F2 §18.5 NING QOPLAMA (coverage) E'TIROZINI BUTUNLAY YO'Q QILADI
— bu kvantlash dalilidan MUSTAQIL, va oldin aytilmagan argument.**

§18.5 ikki mustaqil statistik e'tiroz qo'ygan edi, va **F2 ikkisini ham
yo'q qiladi**:

1. **Qoplama.** F1 da `thr = 0.20 × RMST(P0)` — **baholangan**
   kattalik, konstanta emas, demak `CI95[Δ]` ni **xuddi shu
   ma'lumotdan** baholangan chegaraga qarshi taqqoslash **95%
   qoplamaga ega emas** (`RMST(P0)` ning noaniqligi `Δ` da ham,
   `thr` da ham, **korrelyatsiyalangan** holda ishtirok etadi). **F2 da
   `thr = 0.20 × τ = 1.6 s` — MUZLATILGAN qiymatdan olingan
   KONSTANTA**, demak **ikkinchi baholangan kattalik YO'Q** va
   birgalikdagi noaniqlik muammosi **umuman tug'ilmaydi**.
2. **Nisbiy chegara vs muzlatilgan effect measure.** §18.5: nisbiy
   chegara (`20%`) va §10.2 ning muzlatilgan *"RMST **difference**"*
   effect measure'i **bir-biriga mos kelmaydi**. **F2 da chegara
   sekundda ifodalangan ABSOLUT kattalik (`1.6 s`)**, demak u
   `RMST` **farqining** `CI95_upper` i bilan **bir xil birlikda** va
   **to'g'ridan-to'g'ri** taqqoslanadi.

**Va bu amaliy oqibat beradi.** §18.5 ning yumshatish yo'li **bootstrap**
edi: har resample'da `Δ*` va `thr* = 0.20 × RMST*(P0)` qayta hisoblanadi.
Lekin loyihaning o'z `revix/stats.py` idagi `bootstrap_ci` **ochiq
bayon qiladi**: *"**CENSORED ma'lumot uchun YARAMAYDI.** Censoring bor
joyda KM/RMST"* — va §6.2 censored trial'larni **tashlashni taqiqlaydi**
(*"censored trial'lar Kaplan–Meier / log-rank analiziga **kiradi**"*).

> **Demak F1 ostida BUYURILGAN usul (birgalikdagi noaniqlik bootstrap'i)
> va MAVJUD usul (censoring bilan ishlay olmaydigan bootstrap)
> ZIDDIYATDA edi. F2 ostida ziddiyat YO'Q:** chegara konstanta, demak
> taqqoslash **analitik** `RMST` farq intervali bilan bajariladi —
> Greenwood variansi + normal interval, `revix/stats.py` ning
> `rmst_difference` i (`SE = sqrt(var_a + var_b)`,
> `CI = diff ± z · SE`), u **censoring'ni KM orqali to'g'ri
> ishlaydi**.
>
> **§10.2 ning o'z bootstrap talabi o'zgarmaydi** — `rmst_difference`
> ning izohi normal yaqinlashishni kichik `n` da *"taxminiy"* deb
> belgilaydi va §10.2 bootstrap variantini **ham** talab qiladi. F2 yo'q
> qilgan narsa — **chegaraga qarshi taqqoslash uchun** birgalikdagi
> noaniqlik bootstrap'ining **zaruriyati**, umuman bootstrap emas.

**(2.7) Qo'shimcha foyda — §18.8 ning ta'siri TORAYADI.** §18.8
*"time-to-VR"* ning §6.1 ning uch o'lchovidan (`D_sd` / `D_probe` /
`D_eff`) qaysi biriga bog'lanishini **ochiq qoldirgan**, va §21.4
uchala nomzod ham F1 ostida `thr ≈ 0.1 s` berishini ko'rsatgan. F2 da
`thr = 0.20 × τ` — **endpoint tanlovidan MUSTAQIL**, demak chegara
§18.8 ga **bog'liq bo'lmay qoladi**. §18.8 **o'z sabablari bilan ochiq
qoladi** (`Δ` hamon endpoint'ga bog'liq), lekin F2 uning
**chegaraga** ta'sirini yo'qotadi.

**(2.8) F2 NING NARXI — ochiq yoziladi.** F2 *"20% oshish"* ning
**bazasini** `P0` ning downtime'idan **horizonga** ko'chiradi, va
§18.6 buni o'z so'zi bilan *"**boshqa bayonot**"* deb atagan: u
§11 ning *"×P0"* grammatikasiga (davom etish mezoni (b):
*"`D_eff` `P2` da ≥1.5× `P0`"*) **qarshi** boradi. §18.2 ning
uchta matn asosi (§11 ning o'z grammatikasi, §10.2 ning downtime
o'qishi, `P0` ning solishtirma daraja bo'lishi) **rad etilmaydi** —
ular **matnga sodiqlik** uchun hamon kuchli, va F2 ularga **qarshi**
tanlandi.

**(2.9) §18.7(2) ning ogohligi tan olinadi.** §18.7 ochiq yozgan edi:
*"menga qulay bo'lgan variant **F2** bo'lardi (u limbni ishlaydigan
qiladi va H1 ga qarshi bias beradi, ya'ni 'qattiqqo'l' ko'rinardi) —
lekin F2 matn bilan **qo'llab-quvvatlanmaydi**."* **Bu ogohlik bekor
qilinmaydi, balki javob oladi:** F2 **matnga sodiqlik** uchun emas,
**sinaluvchanlik (testability)** uchun tanlandi — F1 ning inkor shoxi
**o'lchov bilan** erishib bo'lmaydigan ekani ko'rsatilgandan keyin.
Matniy narx 2.8 da, bias 2.10 da, va **tanlovning ma'lumot ko'rilgandan
keyin qilingani 0-bandda** qayd etilgan. **§18.7 ning *"ma'lumot
mavjud emas"* kafolati bu tanlovga QO'LLANMAYDI** — u §18.2 ning
v1.7 dagi qaroriga tegishli.

**(2.10) 🔴 BIAS — F2 ANTI-KONSERVATIV, va bu yumshatilmaydi.**
F2 `thr` ni **kattalashtiradi** (`0.0600 s → 1.6 s`, ≈27×), demak
`CI95_upper[Δ] < thr` shartini **osonlashtiradi**:

```
fail-slow shakli QO'LLAB-QUVVATLANMAYDI  <=>  CI95_upper[ Delta(P2,P0) ] < thr
```

> **Ya'ni F2 *"fail-slow qo'llab-quvvatlanmaydi"* degan xulosani F1 ga
> nisbatan OSON qiladi — u fail-slow gipotezasiga nisbatan
> ANTI-KONSERVATIV.** §18.6 ning jadvali buni allaqachon shunday
> belgilagan: F1 — *"fail-slow / H1 FOYDASIGA"*, F2 —
> *"H1 GA QARSHI"*. **Ikki variant QARAMA-QARSHI yo'nalishda og'adi va
> o'quvchi bu tanlov QAYSI tomonga og'ganini bilishi SHART.** Bu
> **yumshatilmaydi**.

**3. `ramp_above_threshold_s`: eskirgan TAXMIN `3.0 s` → o'lchangan `0.000 s`.**

**Bu uchinchi qaror EMAS** — bu §9.4 ning **o'z talabining** bajarilishi:
*"`ramp_above_threshold_s` … **pressure dosing kalibratsiyasidan
olinadi**, taxmin qilinmaydi."*

- **`3.0 s` hech qachon o'lchanmagan**, va kod buni o'zi aytadi:
  `revix/schedule.py:70` da `RAMP_ABOVE_THRESHOLD_S = 3.0`, izohi —
  *"guard.py kalibratsiyasi bu qismni ≤3 s deb hisoblagan. **Bu
  TAXMIN**, va dosing kalibratsiyasidan … haqiqiy qiymat olinishi
  kerak."*
- **O'lchangan qiymat — `0.000 s`, 29 epizoddan 29 tasida**, kalibrlangan
  `base_mb = 184` da (`10` §4.1).
- **Hujjat allaqachon o'lchangan qiymatni ishlatgan, faqat KOD orqada
  qolgan:** `10` §4.2 kalibratsiyadan beri invariant 2 ni
  `12 + 0.000 = 12.000 ≤ 15` deb yozadi.

**Nega bu amendment'da qayd etiladi:** `TrialTimeline.__post_init__`
(`revix/schedule.py:844`) invariant 2 ni shu konstanta bo'yicha
**majburlaydi**, demak `hold_cap_s = 13.0` eski juftlik bilan default
timeline'ni **ishga tushmaydigan** qiladi:

```
eski juftlik:  12 + 3 = 15 <= 15      o'tadi, lekin AYNAN chegarada (nol zaxira)
yangi 13 va 3: 13 + 3 = 16  > 15      PressureCapExceeded
yangi juftlik: 13 + 0.000   = 13 <= 15   zaxira 2.000 s
```

> **Demak juftlik `13.0 / 0.0` invariant 2 ga zaxira QO'SHADI** (nol →
> 2.000 s), ya'ni bu amendment zaxirani **sarflamaydi**, balki
> **yaratadi**. **Kod o'zgarishi bu amendment'ning qismi emas** — u
> `revix/schedule.py` da bajariladi; bu yerda **qayd etilishi** shart,
> chunki invariant 2 ning arifmetikasi shu konstantaga tayanadi.

**⚠️ CHEKLOV 1 — jarayon nuqsoni.** Eski juftlik invariant 2 ni
**aynan chegarada** qanoatlantirgan (`12 + 3 = 15`), ya'ni **nol
zaxira** bilan, va **birorta test default `TrialTimeline()`
konstruksiyasini sinamagan**. Demak ikki konstanta faqat
**tasodifan** izchil edi, va muammo taxmin yozilgan paytda emas,
**boshqa, aloqasiz o'zgarish paytida** yuzaga chiqdi. Bu
**pre-registration nuqsoni emas, jarayon nuqsoni**, lekin u
`hold_cap_s` ning har qanday o'zgarishi kod invariantini
**jimgina** buzishi mumkinligini ko'rsatadi.

**⚠️ CHEKLOV 2 — invariant REJA ustida, REALLIK ustida emas.**
Validator (`revix/validate.py:1602`, `check_planned_timeline`)
`trial_begin.planned_timeline` ga yozilgan **rejalashtirilgan**
`ramp_above_threshold_s` ni tekshiradi, **trial bo'yicha o'lchangan
qiymatni emas**. Reja `0.0` bo'lsa, u **hech qanday zaxira ko'tarmaydi**:
haqiqiy ramp noldan oshgan run **rejani buzadi**, va reja uni
**yutmaydi**. Yumshatish — har trial'ning **o'lchangan** ramp'ini
yozish va invariantni **unga** nisbatan tekshirish; **bu ish
BAJARILMAGAN**, demak *"invariant 2 reallikka nisbatan majburlanadi"*
deb **o'qilmaydi**. (`10` §4.1 ning 29/29 o'lchovi bu xavfni
**kichik** qiladi, lekin **yo'q qilmaydi**.)

**4. IKKI QARORNING IZCHILLIGI — nega ular BIRGA tanlandi.**

§18.6 ochiq ogohlantirgan edi:

> *"§17.5 ning O1 varianti (`W_stab_pilot` ni kichraytirish) `τ` ni ham
> o'zgartirishi mumkin … va `τ` o'zgarsa F2 ning chegarasi ham
> o'zgaradi. §17.5 va §18.6 ni alohida hal qilish ziddiyat yaratishi
> mumkin."*

**O3 bu ziddiyatni yuzaga kelmaydigan qiladi:** u faqat `hold_cap_s` ga
tegadi va **`W_stab_pilot = 8 s` ni ham, `τ = 8 s` ni ham tegmasdan
qoldiradi**, demak F2 ning `thr = 0.20 × τ = 1.6 s` chegarasi
**barqaror**. Teskarisi ham to'g'ri: F2 `τ` ga tayanadi, demak u O1 ni
**qimmatlashtiradi** — va O1 allaqachon VR da'vosini kuchsizlashtirgani
uchun rad etilgan.

> **(O3, F2) — ichki izchil juftlik, va bu ularni BIRGALIKDA tanlashning
> sabablaridan biri.** §17.5/§18.6 ning *"birgalikda hal qilinishi
> tabiiy"* talabi shu bilan bajarildi.

**5. NIMA O'ZGARMADI — to'liq ro'yxat.**

**§0 ning qolgan bandlari** (H2/A-vs-B, arm C, host-wide pressure,
`io` stall, sintetik SUT) — **o'zgarmadi**; faqat sustained-pressure
bandining chegarasi cap bilan birga siljidi (1.11-band).

**Hech bir metrika ta'rifi** (§4 VR, §5 FR-A/FR-B, §6.1 ning uch
downtime o'lchovi `D_sd`/`D_probe`/`D_eff`, §6.3 latency, §6.4 recovery
loop, §7 pressure o'lchovi); **hech bir statistik test**
(§10.1 Cochran–Armitage, Newcombe/Wilson, Clopper–Pearson,
§10.2 Kaplan–Meier / log-rank / **RMST difference** / Cox-HR taqiqi,
§10.4 Holm oilasi); **hech bir arm** (`A`, `no_action` — §9.3);
**hech bir fault klassi** (faqat `clean_crash`); **hech bir probe
parametri** (`P = 100 ms`, `T_conn = 50 ms`, `T_rt = 50 ms`, `k_f = 3`
⇒ `D_f = 300 ms`); **`disposition` ning yopiq enum'i** va *"aynan bitta
disposition"* qoidasi (§12); **§14 data schema**; va **fail-slow
limbining chegarasidan BOSHQA hech bir falsifikatsiya mezoni** —
§11 ning **kuchli shakli** (`trend p > 0.05` **VA** Newcombe yuqori
chegarasi `< 0.15`), **halol power bayonoti**, **davom etish mezonlari
(a)(b)(c)**, va **null bo'lsa burilish** — **hammasi o'zgarmadi.**
§17.4 ning ikki `disposition_source` qiymati va besh bandi —
**o'zgarmadi** (1.9-band ularni **majburiy** deb qaytaradi).

**Raqamlar, ochiq:**

| qiymat | holat |
|---|---|
| `W_stab_pilot = 8 s` | **O'ZGARMADI** |
| `τ = 8 s` (§10.2, §11) | **O'ZGARMADI** |
| `injection_offset = 3 s` | **O'ZGARMADI** |
| `θ = 0.8` | **O'ZGARMADI** |
| `k_f = 3` | **O'ZGARMADI** |
| `P = 100 ms` | **O'ZGARMADI** |
| `T_conn = 50 ms`, `T_rt = 50 ms` | **O'ZGARMADI** |
| **20 blok / 120 trial** (`3 × 2 × 20`) | **O'ZGARMADI** |
| `W_stab = 60 s`, `guard_sustain_s = 15 s`, `ε = 32 MiB`, quiescence `0.05`, `T_q = 5 s`, `T_w = 15 s`, `T_w_max = 120 s`, `ramp_s = 5 s`, `baseline = 10 s`, washout `≥ 20 s` | **O'ZGARMADI** (kod tomonda ham mexanik tekshirildi: `GUARD_SUSTAIN_WINDOW_S`, `INJECTION_OFFSET_S`, `W_STAB_PILOT_S`, washout va quiescence konstantalari — **tegilmagan**) |
| `hold_cap_s` | **12 s → 13 s** |
| fail-slow limbining `thr` i | **`0.20 × RMST(P0)` → `0.20 × τ = 1.6 s`** |
| `ramp_above_threshold_s` (**muzlatilgan qiymat emas** — §9.4 uni kalibratsiyadan oladi) | taxmin `3.0 s` → **o'lchangan `0.000 s`** |

§0 (qamrovdan tashqari) va §13 (nima muzlatilmaydi) ga **tegilmadi**.
§16, §19, §20, §21, §22 ning qarorlari **o'z kuchida**.

**6. TARIXIY BO'LIMLAR QAYTA YOZILMADI.** §17.9, §18.10, §19.4,
§21.10 va §22 ning *"NIMA O'ZGARMAYDI"* ro'yxatlari, §15.6 ning jadvali
va §16 ning ro'yxatlari `hold_cap_s = 12 s` deb yozadi. **Bular
o'z versiyasidagi holat haqidagi bayonotlar va ular TO'G'RI — shuning
uchun ular o'zgartirilmaydi.** Ularni qayta yozish tarixni
soxtalashtirish bo'lardi. Buning o'rniga **normativ** joylar yangilandi
(§4, §9.4, §11) va §15.3, §17.2, §17.6, §18.2, §18.7 ga
**belgilangan `v1.11` ko'rsatkichi** qo'yildi, demak o'sha bandlarni
o'qiyotgan kishi eski qiymatga yoki eski kafolatga **ishonib qolmaydi**.

**7. NEGA BU AMENDMENT QONUNIY — va u NIMANI KAFOLATLAMAYDI.**

1. **Hech qanday P1 trial'i o'tkazilmagan**, demak **birlamchi endpoint
   ko'rilmagan** va `DEVELOPMENT.md` §7 ning *"ma'lumot yig'ilgandan
   keyin"* qoidasi **qo'llanmaydi**. **Lekin kalibratsiya ma'lumoti
   ko'rilgan** — 0-bandning oshkora e'loni, va bu **kafolat emas,
   e'lon**;
2. **ikkala o'zgarish ham hujjatning O'ZI talab qilgan**: §17.5 va
   §18.6 qarorni *"birinchi pilot trial'idan oldin"* **shart** qilgan,
   va §9.4 `ramp_above_threshold_s` ni kalibratsiyadan olishni **shart**
   qilgan;
3. **ikkalasi ham o'lchov bilan asoslangan, taxmin bilan emas** — v1.3
   ning *"ma'lumot bilan asoslangan amendment, taxmin bilan emas"*
   qoidasi ostida (`10-pressure-dozalash.md` §4, §6, §7);
4. **protsedura bajarildi** (`DEVELOPMENT.md` §7): sana, sabab, nima
   o'zgardi, **nima o'zgarMAdi**, ma'lumot holati, va **v1.10 ning
   `sha256` i bilan git tag'i saqlandi**. Hash hujjatdan ko'chirilmadi —
   `sha256sum` ishga tushirildi va `v0.1.10-preregistration` tag xabari
   bilan solishtirildi (ikkisi **mos**).

**8. BU AMENDMENT NIMANI YOPMAYDI.**

1. **§21.7 ning GATE'i yopilmaydi.** `10` §12.2 gate shartini
   *"o'lchov bo'yicha BAJARILDI"* deb beradi (`overrun_s` n=34, p50
   0.0619 s, max 0.2899 s), lekin *"gate'ni rasman yopish frozen matn
   egasining qarori"* deb ham yozadi. **Bu amendment gate'ga tegmaydi.**
   Sarlavhadagi ⛔ Gate qatori **o'z joyida qoladi** (matni endi
   `hold_s ≤ 13 s` ni bildiradi).
2. **§18.8 ochiq qoladi** — survival endpoint hamon `D_sd`/`D_probe`/
   `D_eff` dan biriga bog'lanmagan (2.6-band ta'sirni toraytiradi,
   masalani hal qilmaydi).
3. **§17.7 ochiq qoladi** — §8.2 ning (ii) nazorati (*"injeksiya yo'q,
   pressure bor"*) §9.3 ning panjarasida hamon yo'q.
4. **§14.4 ning havolasi ATAYLAB yopilmaydi, va bu qarz ko'rinadigan
   qoladi.** §17.8 va §18.9 shunday shart qo'ygan edi: *"§17.5 ning
   O1–O4 qarori muzlatilgan matnga baribir tegadi … shu amendment bu
   havolani tuzatish uchun to'g'ri joy."* **v1.11 — o'sha amendment, va
   shart bajarildi.** Lekin havola tuzatishi **delegatsiya qilingan
   qarorning qismi emas**, shuning uchun u bu yerda **qilinmaydi**.
   **Talab to'liq kuchda:** `units_show` unit **TIRIK** paytida olinadi
   (to'g'ri havola: `docs/architecture/01-muhit-tekshiruvlari.md` §4;
   `04-driver-va-analiz-shartnomasi.md` §1.1 unga to'g'ri havola qiladi).
   Bu **beshinchi** amendment bo'ylab ochiq.
5. **`window_past_pressure` yo'q qilinmadi** — 1.9-band: `1/24` epizod
   hamon ruxsatdan oshadi, va §17.4(4) ning yacheyka bo'yicha hisobot
   talabi **majburiy** bo'lib qoladi.
6. **Pilot hali ishga tushirilishi mumkin emas** — `10` §12.5 ning
   qolgan blokerlari **kod** tomonda (OQ-2: `driver.py` generatorga
   dozalash parametrlarini bermaydi ⇒ o'lchangan **nol doza**;
   `PRESSURE_TARGET_RATE["P2"] = 0.70` over-doza beradi, o'lchangan
   to'g'ri qiymat **0.60**), ustiga 3-bandning `schedule.py` dagi ikki
   konstantasi. **Bular pre-registration masalasi emas.**
7. **Ikki kod nuqsoni — ular bu amendment'ning ma'lumot holati
   bayonotiga TEGADI, lekin bu yerda tuzatilmaydi** (boshqa agentga
   topshirilgan): `revix/driver.py` `ramp_above_threshold_s` ni hamon
   **`"calibration_required": true`** bilan beradi, holbuki
   kalibratsiya **bajarilgan** (3-band), va bir test shu nosaholiq
   qiymatni **tasdiqlaydi**; shuningdek `tests/unit/test_driver.py`
   hamon `13.0 s` li hold **rad etilishini** tasdiqlaydi. **Ya'ni
   harness hozir kalibratsiyani ham, yangi cap'ni ham to'g'ri
   ifodalamaydi**, va bu holat bu hujjatning 0-bandidagi ma'lumot
   holati bilan **birga o'qilishi** kerak: o'lchov bor, lekin kod uni
   hali aks ettirmagan.

### v1.9 → v1.10 (2026-10-03)

| | |
|---|---|
| **v1.9 sha256** | `0cc14a006ccdf78b6f6f085284f16c1555b0dd73f304e7e3259f4fb8461939f6` |
| **v1.9 git tag** | `v0.1.9-preregistration` |
| **Sabab** | §8.2 ning probe narxi bandi: avval xabar qilingan budjet buzilishi **artefakt** bo'lib chiqdi, lekin bandning **ikkinchi** talabi — *"arm'lar bo'yicha bir xil ushlanadi"* — **o'lchangan holda buzilgan**, va u **confound** |
| **O'zgardi** | **§22 qo'shildi** (yangi bo'lim). Mavjud bo'limlar raqamlari va matni O'ZGARMADI |
| **O'zgarMADI** | **hech bir operatsion ta'rif, metrika, chegara, statistik test yoki falsifikatsiya mezoni.** §8.2 ning **to'rtala bandi ham**, §2 ning `P = 100 ms` i — **o'zgarmadi**. **F1–F4, O1–O4, C1–C2 tanlovlari QILINMADI** |
| **Yig'ilgan ma'lumot** | **yo'q** — hech qanday P1 trial'i o'tkazilmagan |

**1. Artefakt qayd etiladi (§22.1).** Avval xabar qilingan `1.238%`
(§8.2 ning `>1%` budjetidan yuqori) **noto'g'ri edi**:
`prober.cost_report()` `time.process_time()` va
`getrusage(RUSAGE_SELF)` ni o'qiydi — ikkisi ham **process bo'yicha**,
barcha thread'lar yig'indisi — va test rig'i soxta SUT'ni
**prober'ning o'z processi ichida thread** sifatida ishlatgan.
Alohida process bilan: `0.608 / 0.601 / 0.605 %`; eski rig'da
prober'ning **o'z thread'i**: `0.574 / 0.586 / 0.563 %` — ikkisi
**mos**, demak xabar qilingan raqamning ≈55% i testning o'z soxta
xizmati edi. Produksiyada prober `revixmon.slice` da alohida
process, demak process-CPU **o'sha yerda to'g'ri**; faqat rig
noto'g'ri edi.

> **Saqlanishga arzigulik metodologik qayd:** **o'z-o'zini
> perturbatsiyani o'lchaydigan asbobning o'zi o'zining test
> harness'i tomonidan perturbatsiya qilingan edi** — §8.2 ning
> butun mavzusi, o'lchov zanjirining eng kutilmagan joyida.

Hech bir oldingi bo'lim bu raqamga tayanmagan (§21 probe narxini
muhokama qilmaydi), demak **retraktsiya qilinadigan qaror yo'q**.

**2. CHEKLOV — kollizya yo'q bo'lmadi, TORAYDI (§22.2).**
**Produksiya konfiguratsiyasida** (2 target — SUT **va** bystander):
`0.77–0.88 %`, va **14 ta 8-sekundlik run'dan 1 tasi `1.007 %`**.
Pol ≈ `0.49 %` (§2 ning talab qilgan kernel ishi ≈53%, muzlatilgan
`P` pacing ≈9%). Demak §8.2 ning budjeti va §2 ning `P` si
**birgalikda qanoatlantiriladi, lekin ≈0.15 pp zaxira bilan**.
**Nega hali ham kollizya:** §8.2 budjet oshsa yagona remedy beradi
— *"sekinlashtiriladi"* — lekin `P = 100 ms` **§2 da muzlatilgan**,
demak **ruxsat etilgan remedy yo'q**; qolgan yo'llar probe ishini
kamaytirish (kod — §22.8) yoki amendment. **Gate qilinmaydi**
(`1/14`, va `0.49%` poli budjetning printsipial erishiladigan
ekanini ko'rsatadi), lekin zaxira **produksiya
konfiguratsiyasida** ingichka ⇒ **har qanday kelgusi o'lchov
2 target bilan berilishi kerak**; 1-target raqamlari bu xavfni
**ko'rsatmaydi**.

**3. FAKT — narx arm'lar bo'yicha bir xil emas (§22.3).**
8 takror × 6 s, 1 target, aralashtirilgan tartib:
`ok` median **0.601 %** (sd 0.032); `silent` 0.480 % (sd 0.038);
`down` median **0.433 %** (sd 0.055). Sog'lom target `down` dan
**1.39×** qimmat, har bir holatning `sd` sidan ancha tashqarida.
Mexanizm: buzilgan probe round-trip'ni, parse'ni va qator
qurishning ko'p qismini o'tkazib yuboradi. **Nega bookkeeping
emas:** `no_action` (`Restart=no`) trial oxirigacha down, ya'ni
**eng ko'p downtime**, demak **eng kam instrumentatsiya yuki** —
va u aynan §8.2 ning **majburiy** nazorati, vazifasi PSI
atributsiyasi.

**4. QAROR — bandning o'qilishi (§22.4).** Butun band **o'lchangan**
registrda (*o'lchanadi / beriladi / sekinlashtiriladi*), demak
*"bir xil ushlanadi"* matniy jihatdan **amalga oshgan yukka**
tegishli. **Lekin amalga oshgan yuk konstruksiya bo'yicha
qanoatlantirilmaydi** — probe'ning narxi u kuzatayotgan natijaga
bog'liq, va tenglashtirishning yagona yo'li **padding**, u esa
umumiy harness CPU'sini **oshirib** §8.2 ning **o'z maqsadini
buzadi**. Ruling, uch bandli:

1. **Konfiguratsiya bir xil SHART** (`hz`, `T_conn`, `T_rt`,
   `k_f`, bo'sh `frozen_deviation()`, bir xil target to'plami) —
   **qanoatlantirilgan**;
2. **amalga oshgan yuk `(arm × pressure)` bo'yicha O'LCHANADI va
   HISOBOTGA KIRITILADI** (`prober_stop` allaqachon `cost` **va**
   `outcome_counts` ni olib yuradi) — **berilmasa band bajarilmagan
   hisoblanadi**;
3. **har qanday PSI-atributsiya da'vosi** (§8.2 ning maqsadi;
   `05-metodologiya.md` §4 ning DiD i; `harm_indicator` / FR-B)
   **harness differentsialini hisobga olishi yoki chegaralashi
   SHART** — asbob qo'shgan narsa action'ga **yozilmaydi**.

> **Ochiq yoziladi: bandning so'zma-so'z talabi BAJARILMAGAN va
> konstruksiya bo'yicha BAJARILMAYDI.** Ruling uni **toraytiradi**,
> demak u matnni zaiflashtiradi va **egasi rad etishi mumkin**
> (§22.7, C1–C2).

**5. QAROR — qayerda tishlaydi (§22.5).** **Birlamchi endpoint
strukturaviy himoyalangan, ikki sabab bilan:** (i) §8.2 ning
1-bandi harness'ni `revixmon.slice` ga qo'yadi va
*"kovariata sifatida ishlatiladigan hech bir scope ichida emas"*
deydi, §7 ning asosiy scope'i esa `revixlab.slice` — demak
prober CPU'si **birlamchi kovariataga umuman kirmaydi**;
(ii) §16.2(A) bo'yicha trend testi **arm `A` ichida**, demak
`A ↔ no_action` farqi birlamchi endpoint'ga **kirmaydi**.

**Arm `A` ichida** (derivatsiya, o'lchov emas): narx uptime ulushi
bilan o'sadi, uptime ulushi pressure bilan kamayadi (H1 ning o'z
prognozi) ⇒ `cost(A,P2) < cost(A,P0)`, ya'ni harness **eng kam**
perturbatsiya qiladi **recovery eng qiyin** yacheykada. H1 yolg'on
bo'lsa — bias **yo'q**; H1 to'g'ri bo'lsa — trend **susayadi** ⇒
**H1 ga qarshi**. **Ikkala holatda ham differentsial prognoz
qilingan effektni YARATA OLMAYDI.**

**Atributsiya — mana shu yerda haqiqiy confound:** arm `A` da
prober qimmatroq, demak `A − no_action` ayirmasi action'ga
**ortiqcha yozadi** ⇒ **action'ning PSI narxi oshirib
ko'rsatiladi**, ya'ni action haqiqatdan **zararliroq** ko'rinadi —
va bu **loyihaning o'z tezisiga mos keladigan** yo'nalish.
**Noqulay yo'nalish, ochiq yoziladi.**

**Magnitudasi chegaralangan:** differentsial `0.168` pp **bitta
yadroda**, 12 CPU li muhitda (§15.1) ≈ `0.014%` umumiy sig'im, va
**kovariata scope'idan tashqarida**. 2 target'da bystander
**hech qachon fault qilinmaydi** ⇒ uning komponenti **konstanta**.
Demak **magnitudasi kichik, yo'nalishi tizimli** — remedy
**analitik**, operatsion emas.

**6. Bias (§22.6).** Ruling bandni **toraytiradi**, ya'ni §8.2 ni
zaiflashtiradi. Birlamchi endpoint uchun differentsialning o'zi
**H1 ga qarshi**, demak ruling bu yerda **H1 ga qarshi**.
Atributsiya uchun differentsial **loyiha tezisi foydasiga**, va
ruling uni tenglashtirmaydi, faqat hisobga olishni talab qiladi ⇒
**agar hisobga olish bajarilmasa, bias loyiha foydasiga qoladi, va
aynan shuning uchun §22.4(3) "SHART" deb yozilgan, "iloji bo'lsa"
deb emas.**

**7. GATE QILINMAYDI (§22.7).** §17.5 va §18.6 dan farqli, birlamchi
endpoint xavf ostida emas, differentsial konservativ yo'nalishda va
magnitudasi chegaralangan ⇒ **CHEKLOV va hisobot talabi**, pilotni
bloklaydigan qaror emas. Egasi **C1** (so'zma-so'z o'qish ⇒ padding,
§8.2 ning maqsadini buzadi — **tavsiya qilinmaydi**) yoki **C2**
(differentsialni gate deb hisoblash ⇒ `P` §2 da muzlatilgan) ni
tanlashi mumkin; **men tanlamadim**.

**8. OCHIQ MASALA (§22.8).** `revix/schema.py` ning `csv.write` i
har probe narxining **≈10%** i, **ataylab tegilmagan** (boshqa
agentning fayli) — §22.2 ning ≈0.15 pp zaxirasini kengaytirish
kerak bo'lsa **eng katta qolgan element**. Bu
**pre-registration masalasi emas** (`P`, budjet va §2 ning
contract bandlari o'zgarmaydi), demak kollizyani **ta'rifga
tegmasdan** yopish yo'li. **Interpretator sabab emas** — o'sha
agent Python 3.14 ≈18% yomonroq degan bir-takrorli taxminini
**o'zi rad etdi** (run-to-run shovqin).

### v1.8 → v1.9 (2026-10-03)

| | |
|---|---|
| **v1.8 sha256** | `30b5036ab8cb538d17fbe73ab429f5817e7661b78ecb0e46ac649995ff7a9b07` |
| **v1.8 git tag** | **hali yo'q** (integratsiyadan keyin) |
| **Sabab** | `experiment/guard-recal` ikki hal qiluvchi raqamni o'lchadi va **OQ-12** ni ko'tardi; §16.11 ning GIPOTEZA'si **FAKT** bo'ldi; va `InvocationID` ning kod bo'ylab qamrovi aniqlandi |
| **O'zgardi** | **§21 qo'shildi** (yangi bo'lim). Mavjud bo'limlar raqamlari va matni O'ZGARMADI |
| **O'zgarMADI** | **hech bir operatsion ta'rif, metrika, chegara, statistik test yoki falsifikatsiya mezoni.** §4 ning matni va uning 3–4 bandlari, §9.4 ning ikki invarianti, §9.3 ning `P2` bandi — **o'zgarmadi**. **F1–F4 va O1–O4 tanlovlari QILINMADI** |
| **Yig'ilgan ma'lumot** | **yo'q** — hech qanday P1 trial'i o'tkazilmagan; `guard-recal` ning o'lchovlari **guard va generator kalibratsiyasi** (`08` §14.3: *"Pilot ishga tushirilishi mumkinmi? ❌ HOZIR MUMKIN EMAS"*) |

**Bu bo'lim qaysi savollarga javob beradi:**

| savol | javob | qayerda |
|---|---|---|
| **OQ-12** — §11 ning `RMST(P0)` i `D_probe` mi yoki `W_stab` ni o'z ichiga olgan to'liq time-to-VR mi? | **`D_probe`** — OQ-12 **rad etiladi**, §18.3 o'z kuchida | §21.1 |
| §18.6 ning qarori kerakmi? | **HA** — va **OQ-12 ning javobidan qat'i nazar** | §21.2 |
| §18.8 (bog'lanmagan endpoint) javobni o'zgartiradimi? | **YO'Q** | §21.4 |
| §17.5 ning qarori kerakmi? | **HA** | §21.5 |
| Band 4 aldanishi mumkinmi? | **O'LCHANDI — ha, soxta VR ko'rsatildi** | §21.6 |
| Bo'sh `InvocationID` ni qanday o'qish kerak? | **ANIQLANMAGAN** (na "o'zgarmadi", na "mos kelmadi") | §21.6.1 |

---

**1. OQ-12 RAD ETILADI (§21.1).** `08` §16.2 ning CHEKLOV'i: *agar
time-to-VR `W_stab` ni o'z ichiga olsa, `RMST(P0) ≈ 8.5 s`,
`thr ≈ 1.7 s ≥ 5P`, demak §18.6 ning qarori kerak emas.*

Uchta mustaqil asos bilan rad etiladi:

- **(a) matn:** §6.1 `D_probe` ni oynaning **birinchi** probe'ida
  tugatadi; §6.3 verification latency'ni *"ta'rifan `W_stab`ga teng"*
  deb metrikadan **ataylab chiqaradi** — ya'ni §18.3 allaqachon hal
  qilgan;
- **(b) arifmetika:** `RMST(τ) = E[min(T, τ)] ≤ τ` **har doim**. Oyna
  kiritilsa `T ≥ 8 s` har bir trial uchun, demak
  `RMST(P0) = 8.000 s` **AYNAN** (8.5 s **emas** — `8.5` bu `E[T]`,
  chegaralanmagan o'rtacha, ya'ni §10.2 `RMST` ni tanlab **qochgan**
  kattalik). Natijada `Δ = 8 − 8 = 0` **ayni, dispersiyasi nol**,
  `CI = [0,0]`, `0 < 1.6` **har doim** ⇒ *"fail-slow
  qo'llab-quvvatlanmaydi"* **har qanday ma'lumot uchun avtomatik**.
  **Ya'ni bu o'qish qarorni keraksiz qilmaydi — limbni SHARTSIZ
  INKOR qiladigan qilib qo'yadi, bu esa hozirgi holatdan qat'iy
  yomonroq;**
- **(c) §19.3:** `R = 8 s > τ/1.20 = 6.67 s`, ya'ni §19.3 ning
  **yuqori degeneratsiyasi**ning chegaraviy holati.

**2. TUZATISH — mening §18.6 qabul qoidam BIR TOMONLAMA edi (§21.2).**
§18.6 *"`thr ≥ ~5P` ⇒ F1 yetarli"* deb faqat **pastki** chegarani
tekshirgan. §19.3 yuqori chegarani (`thr ≤ τ − R`) chiqardi, lekin
men uni **qabul qoidasiga qaytarib qo'ymadim**. **OQ-12 aynan shu
bo'shliqdan o'tdi** — `R` ni oshirib mening **yozilgan qoidamni
bajaradi** va shu bilan yuqori degeneratsiyaga tushadi. **Qoidam
noto'g'ri edi, OQ-12 emas.** Tuzatilgan ikki tomonlama qoida:

```
5P <= thr <= 1/2 (tau - R)        <=>        2.5 s <= R <= 5.7 s
```

| o'qish | `R` | `≥ 5P` | `≤ ½(τ−R)` | natija |
|---|---|---|---|---|
| `t_up` anchor (o'lchangan) | **0.483 s** | ❌ | ✓ | **qaror KERAK** |
| oyna-ichida (OQ-12) | **8.000 s** | ✓ | ❌ | **qaror KERAK** |

→ **§18.6 ning qarori OQ-12 ning javobidan QAT'I NAZAR zarur.**

**3. O'lchangan chegara (§21.3).** `D_probe` proxy, `P0`, n=12,
`boot_id` va `pid1_starttime` ikki chekkada ham o'zgarmagan:
`mean = 0.4833 s` ⇒ `thr = 0.0967 s = 0.97 × P` ⇒ **5P dan past**.
Bu §18.4 ning `80–220 ms` derivatsiyasini **o'lchov bilan**
tasdiqlaydi. Va `guard-recal` ning proxy'i o'zi da'vo qilganidan
**tighter**: §18.3 bo'yicha oyna **davomiyligini** chiqarish
to'g'ri, demak u o'sha sababdan pastki chegara **emas**; 12
epizodda qayta buzilish bo'lmagani uchun **proxy = `D_probe`
aynan**. Pressure ostidagi toza `t_start` (p50 2.83 s) bilan
`Δ̂ ≈ 3 s ≈ 31 × thr` ⇒ limb *"fail-slow qo'llab-quvvatlanadi"* ni
**avtomatik** beradi va 3 s kechikishni 0.2 s dan **ajrata
olmaydi**. §19.3 ning **pastki degeneratsiyasi** o'lchov bilan
tasdiqlandi.

**4. §18.8 javobni o'zgartirMAYDI (§21.4).** `D_probe` 0.483 s,
`D_eff` ≈ `P·(3–4 probe)` + integral ≈ 0.3–0.4 s+, `D_sd` §6.1
bo'yicha *"ortiqcha kredit"* ⇒ undan **kichik**. **Uchalasi ham
`P0` da sub-sekundli**, demak `thr ≈ 0.1 s` hammasida. `D_eff` ning
past kvantlash poli CI ni **toraytiradi**, lekin to'siq
`Δ̂ ≈ 31 × thr` bo'lgani uchun u *"qo'llab-quvvatlash"* ni **yanada
aniqroq** qiladi. §18.8 **o'z sabablari bilan ochiq qoladi.**

**5. §17.5 ning qarori ham ZARUR (§21.5).** Toza o'lchov:
`p90(t_start)` `P0` da **0.0497 s** (`30/30` budjet ichida,
`16×` zaxira), pressure ostida **5.4042 s** — §17.2 ning `0.8 s`
budjetidan **6.8× katta**, va **ikki mustaqil o'lchovda** budjet
ichida **bitta ham** urinish yo'q (`0/6`, `0/8`). **Va bir yo'l
yopiladi:** kechikish SUT ning **ichida emas** (uning `uptime_us`
0.06–0.96 s, `t_start` 1.67–7.20 s) — `execve`, dinamik yuklash va
reclaim ostidagi page fault'lar, `main()` dan **oldin**. Demak
**SUT ni tezlashtirish nuqsonni tuzatmaydi**, va bu O1–O4 dan
qochish yo'lini **olib tashlaydi**.

**6. §16.11 ning GIPOTEZA'si endi FAKT (§21.6): band 4 ALDANDI.**
`08` §8: `-virgin` unit'ida `NRestarts` ikki chekkada ham **0** —
"o'zgarmadi" — holbuki oyna ichida PID 1 qayta ishga tushdi, unit
yo'q qilindi va jarayoni o'ldirildi ⇒ **§4 ning 4-bandi
qanoatlanadi va bo'lmagan recovery VR deb hisoblanadi: SOXTA VR.**

**QAROR — bandlar yamalmaydi, marker PRESHART qilinadi:**
(1) §4 ning 3–4 bandlari **shartli haqiqiy** — faqat PID 1 oyna
ichida qayta ishga tushmagan bo'lsa (matn o'zgarmaydi; bu
bandlarning **amal qilish sharti**); ularni mustahkamlash
**befoyda**, chunki `systemctl show` o'lgan unit uchun default'larni
`rc=0` bilan qaytaradi. (2) §16.11 ning marker'i — trial
**presharti**: `pid1_starttime` trial ichida o'zgarsa, §20.2
bo'yicha **`vr = None`**. (3) **KM/log-rank'dan ham tashqarida** —
`no_episode` dan keyin ikkinchi shunday kategoriya, sababi boshqa:
§1 bo'yicha monotonic taqqoslanuvchanlik yo'qoladi, demak
davomiylik **kuzatuv sifatida ham** yaroqsiz.

**7. Bo'sh `InvocationID` — ANIQLANMAGAN (§21.6.1).** Orkestrator
tasdiqladi (main `0a83824`): uchala iste'molchi ham bo'sh id ni
**jimgina tashlaydi** (`reduce.py:1006`, `reduce.py:2071`,
`validate.py:671` → `check_actions:657`), demak **"o'zgarmadi" va
"yo'q" hozir ayni bir kuzatuv**. Va `guard-recal` o'lchadi: yo'q
qilingan unit yangi id **olmaydi, BO'SH bo'ladi** — eng xavfli
variant. **Ikkinchi ko'rinishi:** restart qilgan action
**ta'sirsiz action** kabi ko'rinadi ⇒ soxta
`action_without_invocation_change`, ya'ni §14.6(6) **buzilgan** deb
xabar beriladi, holbuki u **baholanmagan**.

**Bu RULING, deduksiya emas** — §8.4(3) washout quiescence haqida
yozilgan, §4 ning bandlari haqida emas. Shuning uchun u faqat o'sha
analogiyaga tayanmaydi: (i) **§4 ning o'z talabi** — oyna davomida
unit tirik bo'lishi kerak, bo'sh id esa *"o'qilgan paytda tirik
emas"* degani (`01-muhit-tekshiruvlari.md` §4 dead-unit tuzog'i),
ya'ni probe'lar o'tgan-u unit tirik emas — **ichki ziddiyat**;
(ii) **§20.2** ning muzlatilgan printsipi.

**Shakl:** `reduce.py` bo'sh/`None` id ni to'plamdan **tashlamaydi**,
balki `vr = None`, `vr_reason = "invocation_id_unreadable"` qiladi;
`validate.py` `action_without_invocation_change` **bermaydi**, balki
alohida topilma beradi va §14.6(6) ni o'sha action uchun
**baholanmagan** deb belgilaydi — ***buzilgan* va *baholanmagan* bir
xil xabar bilan berilmaydi**. Daraja
**instrumentatsiya yo'qolishi** sinfida. Bu marker preshart'iga
**ikkinchi himoya chizig'i**, ortiqcha emas.

**8. CHEKLOV — §9.4 ning invariantlari majburlanmaydi: GATE, amendment
EMAS (§21.7).** `08` §5: 5 s so'rov → **16.3 s** epizod. §9.4 ning
invariantlari **haqiqiy trial'ning preshartlari**, demak ularni
buzgan epizod trial **emas** — invariantlar **to'g'ri qoladi**,
bajarilmaydigan narsa **asbob**. Qoida: **generator ikki
invariantni majburlamaguncha hech qanday pilot trial
o'tkazilmaydi.** Noqulay oqibati: bugun trial o'tkazilsa
`aborted_guard` **qoida** bo'lardi va §12 ning eksklyuziya darajasi
— **hisobotga kiradigan NATIJA** — asbob nuqsonidan belgilanardi;
va `08` §17 ga ko'ra guard **birinchi trip'dan keyin boshqa
o'ldirmaydi**, demak qolgan 119 trial himoyasiz va
`aborted_guard` **kam** hisoblanadi — **jimgina**, ya'ni ko'p
hisoblashdan yomonroq. `ramp_above_threshold_s = 0.000 s`
**nol dozada** o'lchangan (`08` §3.4), demak §9.4 ning
*"kalibratsiyadan olinadi, taxmin qilinmaydi"* talabini
**qanoatlantirmaydi** — pilotga ko'chirilmaydi.

**9. FAKT — `P2` erishiladigan, lekin USHLAB TURILMAGAN (§21.8).**
`0.604–0.785` har bir toza run'da ko'rindi, lekin faqat `0.999` ga
to'yinish yo'lidagi **0.6–0.9 s traversi** sifatida. v1.5 §16.10
ning CHEKLOV'i **aniqlashtiriladi**: endi *erishiladigan* deb
ko'rsatildi, *ushlab turilgani* **ko'rsatilmadi**. §9.3 ning bandi
**rad etilmadi va isbotlanmadi**.

**10. FAKT — §15.3 ning guard asosi mustaqil tasdiqlandi (§21.9).**
`user/lab` `p50 = 0.9963`, **642 toza juftlashtirilgan namuna**
(`02` §1 ning `0.996` iga qarshi), va `user@ some == user@ full`
**har bir qatorda** — `02` §1 ning mexanizmi **xulosa emas,
bevosita o'lchov** bilan tasdiqlandi. Demak davomiylik kriteriyasi
**to'g'ri qoladi**.

### v1.7 → v1.8 (2026-10-03)

| | |
|---|---|
| **v1.7 sha256** | `314deecfd9e4343a22f936556415c0248f606e33960af145ca1d70a865215fe4` |
| **v1.7 git tag** | `v0.1.7-preregistration` |
| **Sabab** | uchta mustaqil narsa: §16.11 ning ochiq o'lchovi **yopildi**; `analyze` §18.4 ning rejim tahlili **chala** ekanini ko'rsatdi; va `reduce-fix` §12 jim qolgan **uchinchi** nuqtani topdi (`vr = None` maxrajda) |
| **O'zgardi** | **§19 va §20 qo'shildi** (ikki yangi bo'lim). Mavjud bo'limlar raqamlari va matni O'ZGARMADI |
| **O'zgarMADI** | **hech bir operatsion ta'rif, metrika, chegara, statistik test yoki falsifikatsiya mezoni.** §18.2 ning referens qarori, §16.11 ning marker talabi, §16.2(B) va §17.4 — **o'zgarmadi**; §19 va §20 ularni **asoslaydi va umumlashtiradi** |
| **Yig'ilgan ma'lumot** | **yo'q** — hech qanday eksperiment ishga tushirilmagan |

> **Nega bitta amendment'da ikki bo'lim:** §19 va §20 bir-biridan
> mustaqil, lekin ikkalasi ham **hech qanday muzlatilgan qiymatga
> tegmaydi** va ikkalasi ham oxiriga qo'shiladi, demak ularni ajratish
> faqat versiya sonini oshirardi, hech qanday kafolat qo'shmasdan.
>
> **Bitta versiyada ikki qaror — bu hujjat uchun BIRINCHI marta**,
> shuning uchun qaysi bo'lim qaysi savolga javob berishi ochiq
> yoziladi, chalkashmasligi uchun:
>
> | bo'lim | qaysi savolga javob beradi | tashabbus |
> |---|---|---|
> | **§19** | (a) §16.11 ning ochiq o'lchovi: to'liq VM restart'da `boot_id` o'zgaradimi — **ha**, va yetarlilik chegarasi chizildi; (b) **§18.4 ning rejim tahlili chala edi** — `RMST` ning `τ` bilan chegaralanganligi ikkinchi degeneratsiyani yaratadi | orkestratorning o'lchovi + `agent/analyze` ning nuqtasi |
> | **§20** | **sof brownout / `vr = None`**: contract buzilmagani uchun epizod yo'q (`vr_reason = "no_episode"`), lekin trial `complete`/`derived` bo'lib **binar maxrajda** qoladi; va qo'shni holat `r_ref_unavailable` | `reduce-fix` ning fixture'i |
>
> `no_episode` va `r_ref_unavailable` **turli da'volar** (*"o'lchash
> uchun narsa yo'q"* va *"o'lchov muvaffaqiyatsiz bo'ldi"*) va §20.3
> bilan §20.4 da **turlicha** ishlanadi.

---

**1. §19.1 — `boot_id` yetarlilik chegarasi chizildi.** §16.11 da
*"to'liq WSL VM restart'ida `boot_id` o'zgaradimi — bu o'lchov
bajarilmadi"* deb yozilgan edi. Endi o'lchandi: `boot_id`
**O'ZGARADI**. Ikki restart rejimi ajratildi, har biriga bitta
detektor:

| rejim | `boot_id` | `pid1_starttime` | kim tutadi |
|---|---|---|---|
| to'liq VM restart | **o'zgaradi** | yana kichik | **§14.6(5)** |
| init-only | o'zgarmaydi | **sakraydi** | **§16.11** marker'i |

§16.11 ning xulosasi **aniqlashtiriladi, bekor qilinmaydi:** §1 ning
da'vosi **umuman** yolg'on emas — **faqat init-only** holatda yolg'on;
§14.6(5) **zarur va to'liq VM restart uchun yetarli**; §16.11 ning
marker'i **init-only teshigini** yopadi, demak **ortiqcha emas**.
Ikkalasi **to'ldiruvchi**. §16.11 **kuchsizlanmadi — kuchaydi.**

**Provenans ochiq ajratilgan:** o'qishlar **orkestrator** tomonidan,
bu agent tomonidan **emas** va **mustaqil tasdiqlanmagan** (WSL ishi
to'xtatilgan). *"Yangi kernel boot"* orkestratorning **o'z**
o'qishlari bilan yetarli (uptime `2024.34 → 544.35 s` **orqaga**;
PID 1 yoshi boot bilan teng). *"`boot_id` o'zgardi"* esa **ikki
agentning** o'qishiga tayanadi — eski qiymat bu agentning §16.11
yozuvidan, yangisi orkestratordan; **bitta agent ikkalasini ham
ko'rmagan.** Shu sababli **muzlatilgan talab:** `/proc/uptime`,
`boot_id` va `/proc/1/stat` 22-maydoni **bitta atomik o'qish guruhi**
sifatida, bitta record'ga yoziladi.

**2. §19.2 — feasibility kuchaydi.** To'liq VM restart init-only'dan
**qat'iy yomonroq**. §9.4 ning **≈2.5 soatlik** kampaniyasi shu
guest'da uzilish ehtimoli **e'tiborsiz emas**, demak driver'ning
hard-abort'i **ishga tushishi kutiladi**. **Yangi ochiq bo'shliq:**
uzilish §8.4 ning blok strukturasini buzadi va **tugallanmagan
bloklarning taqdiri §8.4 da aytilmagan.**

**3. §19.3 — TUZATISH: §18.4 ning rejim tahlili chala edi.** §18.4
`RMST(P0) → 8 s` rejimini *"inkor erishiladigan, qo'llab-quvvatlash
qat'iy"* deb **sog'lom** ko'rsatgan. **Chala va chalg'ituvchi:**
`RMST ∈ [0, τ]`, demak `Δ ≤ τ − R`, va:

```
thr <= tau - R   <=>   0.20*R <= tau - R   <=>   R <= tau/1.20 = 6.67 s
thr >= P         <=>   R >= 0.5 s     ;    thr >= 5P  <=>  R >= 2.5 s
```

→ `R > 6.67 s` bo'lsa `thr` **erishilishi mumkin bo'lgan eng katta
effektdan katta**: kriteriy **sodir bo'lishi mumkin bo'lmagan**
holatni qidiradi va xulosa **ma'lumotdan emas, arifmetikadan**
chiqadi. To'g'rilangan rejimlar: **pastki degeneratsiya**
(`R < 0.5 s`) — inkor **aniqlanmaydi**; **tishli band**
(`R ≈ 2.5 … 5.7 s`); **yuqori degeneratsiya** (`R > 6.67 s`) — inkor
**avtomatik**. **Ikki degeneratsiya TESKARI xulosaga olib keladi.**
§18.4 ning chiqarmasi `R ≈ 0.4 … 1.1 s` — **pastki degeneratsiya
chegarasida**. `analyze` ning nuqtasi §18.2 ni kuchsizlashtirmaydi,
**o'tkirlashtiradi**: referens chegarani masshtablamaydi — u
kriteriyning **tishi bor-yo'qligini** belgilaydi. **Ceiling muammosi
hech bir F variantida yo'qolmaydi** (hatto F2 ham `R > 6.4 s` da
erishib bo'lmaydigan bo'ladi), demak **§17.5, §18.6 va §18.8 —
bitta qarorning uch bo'lagi**, tuguni `τ = W_stab_pilot = 8 s`.
**F1–F4 tanlovi QILINMADI.**

---

**4. §20 — `vr = None` maxrajda: umumlashtirilgan qoida.**
`reduce-fix` **sof brownout** fixture'i qurdi (throughput `R_ref`
ning 30% i, **har bir probe contract'dan o'tadi**) ⇒ epizod yo'q ⇒
`vr = None`, `vr_reason = "no_episode"` ⇒ trial `complete`/`derived`
bo'lib **binar maxrajda** qoladi, aniqlanmagan VR bilan.

**QAROR (§20.2):** maxrajning to'g'ri ta'rifi disposition ro'yxati
emas, **predikatning aniqlanganligi**:

> **Binar `P(VR)` maxraji — §4 ning predikati ANIQLANGAN qiymat
> (`true`/`false`) olgan trial'lar to'plami. `vr = None` — sababi
> nima bo'lishidan qat'i nazar — maxrajdan TASHQARIDA, va sabab
> nomlanib beriladi.**

Bu **yangi qoida emas, umumlashtirish**: §16.2(B) va §17.4 undan
kelib chiqadi. **Hech qanday yangi `disposition` qiymati kerak emas;
§12 ning yopiq enum'iga tegilmadi.**

**`no_episode` va `r_ref_unavailable` FARQLI ishlanadi** — ular
boshqa da'volar:

| | `no_episode` | `r_ref_unavailable`, `throughput_unmeasurable` |
|---|---|---|
| VR savoli | **tug'ilmagan** | **tug'ildi**, javob kuzatilmadi |
| binar maxraj | **yo'q** | **yo'q** |
| KM/log-rank | **yo'q** — §6.2 ning qoidasi *"recovery bo'lmagan"* trial'lar haqida, bu esa recovery **kutilmagan** trial | **ha**, horizon'da censored |
| hisobot sinfi | **injektor samaradorligi** | **instrumentatsiya yo'qolishi** (`probe_gap` bilan birga) |

`no_episode` — v1.5 dan beri **ikkala** to'plamdan ham chiqadigan
birinchi kategoriya; §6.2 ga zid emas, chunki §6.2 ning qoidasi bu
holatga **yetib bormaydi**. Va §9.3 bo'yicha har trial'da bitta
injeksiya bo'lgani uchun `no_episode` **injeksiya ishlamaganini**
bildiradi — **trial nuqsoni**, natija emas, va noldan farqli daraja
**pilotni gate qiladi**.

`r_ref_unavailable` uchun **qat'iy taqiq:** 1–4 bandlar ustida VR
hisoblash **TAQIQLANADI**, chunki §4 5-bandni *"VR ni
process-liveness'dan ajratadigan narsa"* deb ataydi va §9.2
*"liveness-only VR ta'rifi ehtimol null pilot beradi, va bu null —
ta'rif artefakti"* deb oldindan yozgan.

**CHEKLOV (§20.5):** sof brownout **§9.2 ning (iii) mexanizmi emas**
((iii) *"start bo'ldi"* deydi, ya'ni epizodni nazarda tutadi).
Natijada binar endpoint contract'ni buzmagan degradatsiyaga
**ko'r** — 30% throughput'da na `VR = false`, na invalidator, na
epizod. **Lekin pilot ko'r emas:** §6.1 ning `D_eff` i brownout'ni
**hisoblaydi**, va §11(b) aynan `D_eff` ni ishlatadi, demak §11(b)
qo'shimcha emas, **mustaqil zarur** mezon. Maqolada shunday yoziladi,
**yumshatilmaydi**. Bog'liqlik: contract'ni buzmagan pressure
degradatsiyasi — aynan §8.2 ning (ii) nazorati o'lchashi kerak
bo'lgan narsa, va u §9.3 panjarasida yo'q (§17.7).

**Bias (§20.6):** birlamchi asos — **aniqlanganlik**, yo'nalish emas:
qaror `P(VR)` ni har qanday `None`-siyosatidan **mustaqil** qiladi.
Yo'nalish, **shartli**: `vr = None` maxrajda qolsa `P(VR)` pasayadi,
va brownout `P2` da ko'proq uchrashi ehtimol, demak hozirgi holat
trend'ni **kuchaytirardi** (H1 foydasiga) — **qaror H1 GA QARSHI
ishlaydi**. `no_episode` ning `P2` da to'planishi **o'lchanmagan**
taxmin, shuning uchun yo'nalish shartli e'lon qilinadi. **Bu qaror
§16.2(B) va §18.2 bilan teskari yo'nalishga ishlaydi** — qarorlar
bir tomonga tizmalanmayotgani ularning **yo'naltirilmayotganining**
dalili.

**TASDIQ (§20.7):** `reduce-fix` ning ikki hukmi §17 ga **zid emas**.
(a) §17.4 ni `P0` da ham bir xil qo'llash **majburiy** — §9.4 jadvali
barcha darajalarda amal qiladi, `P0` da generator idle (§9.3) lekin
fazalar jadval sifatida saqlanadi; yumshatilsa trend strataları
bo'ylab **turli kattaliklar** taqqoslanardi, aynan §17 olib tashlagan
bias. (b) **allow-list** §8.4(3) ning fail-closed qoidasining
to'g'ridan-to'g'ri qo'llanishi; §20.2 shu printsipni `vr` ga ham
yoyadi — `vr` **tasdiqlab aniqlangan** bo'lishi shart.

**OCHIQ BO'SHLIQ (§20.8):** §12 ning yopiq enum'ida *"injeksiya
ishlamadi"* uchun qiymat yo'q; hozirgi kodda bunday trial
`complete`/`derived` bo'lib qoladi, bu esa §12 ning *"to'liq
o'lchandi"* ma'nosiga mos kelmaydi. **Hal qilinmaydi** — yopiq
enum'ga tegadi. §20.2 bo'shliqni analiz tomondan yopgani uchun
**P1 ni bloklamaydi**. Egasining qarori; §17.5 amendment'i tabiiy joy.

**O'LCHANMADI:** `R = RMST_A(P0, τ)` va `D_probe(P0)` taqsimoti
(§18.6/§19.3 so'rovi, endi aniq qabul mezoni bilan); `no_episode`
ning `(arm × pressure)` bo'yicha taqsimoti.

### v1.6 → v1.7 (2026-10-03)

| | |
|---|---|
| **v1.6 sha256** | `69a6948c977bdbb54ceec39b73c6db6c73ea1344d010c20d7b05911333f8f5f9` |
| **v1.6 git tag** | `v0.1.6-preregistration` |
| **Sabab** | §11 ning **fail-slow limbi hisoblanmaydi**: *"20% oshish"* ning referens kattaligi aytilmagan, ayirish tartibi va yo'nalish ham aytilmagan |
| **O'zgardi** | **§18 qo'shildi** (yangi bo'lim). Mavjud bo'limlar raqamlari va matni O'ZGARMADI |
| **O'zgarMADI** | **hech bir operatsion ta'rif, metrika, chegara, statistik test yoki falsifikatsiya mezoni.** §11 ning ikkala limbi ham **matn sifatida o'zgarmadi**; `τ = 8 s` va `20%` **o'zgartirilmadi** |
| **Yig'ilgan ma'lumot** | **yo'q** — hech qanday eksperiment ishga tushirilmagan, demak eski ta'riflar ostida qayta hisoblanishi kerak bo'lgan hech narsa yo'q |

> **Sana haqida:** bu amendment ustidagi ish 2026-10-02 da boshlangan va
> kalendar kuni ish davomida almashdi; muzlatilgan sana **2026-10-03**,
> ya'ni haqiqiy commit kuni. §18 da **hech qanday yangi o'lchov yo'q** —
> 18.4 ning butun arifmetikasi muzlatilgan qiymatlardan chiqarilgan.
> §15.1 va §16.11 dagi o'lchovlar **2026-10-02** da olingan va shu sana
> ostida qoladi.

**Muammo:** §11 ning kuchli shakl limbi to'liq aniqlangan
(*"Newcombe CI ning **yuqori chegarasi < 0.15**"*), fail-slow limbi esa
*"95% CI **20% oshishni** chiqarib tashlasa"* deydi va **nimaning 20% i**
ekanini aytmaydi. Ayirish tartibi (`P2 − P0` yoki teskarisi) va
*"chiqarib tashlash"* ning yo'nalishi ham aytilmagan. Ya'ni
**§11 ning ikki limbidan biri hisoblanmaydi** — va §17 ning argumenti
bu yerga ham qo'llanadi: hisoblab bo'lmaydigan pre-registered qoida
hech narsani falsifikatsiya qilmaydi.

**QAROR (§18.2) — referens `RMST(P0)`, matnning O'Z konvensiyasidan:**

1. §11 ning davom etish mezoni **(b)** pressure effektini
   *"`D_eff` `P2` da **≥1.5× `P0`**, bootstrap CI **1.0 ni** chiqarib
   tashlaydi"* shaklida ifodalaydi — ya'ni §11 ning o'z grammatikasi
   **`P0` ga nisbatan karrali**, va fail-slow limbi xuddi shu
   grammatikada yozilgan;
2. §10.2 RMST farqini *"**τ sekund ichida tejalgan kutilgan downtime**"*
   deb o'qiydi, demak bazasi solishtirma darajaning downtime'i;
3. `P0` — dizaynning solishtirma darajasi (§9.3).

Qolgan nomzodlar rad etiladi: `τ` ning 20% i boshqa bayonot; `P0` ning
**o'rtachasi** §10.2 da taqiqlangan; farqning 20% i sirkulyar.

Formalizatsiya (arm `A` ichida, §16.5):
```
Δ(P2,P0) := RMST_A(P2, τ=8 s) − RMST_A(P0, τ=8 s)
thr      := 0.20 × RMST_A(P0, τ=8 s)
fail-slow QO'LLAB-QUVVATLANMAYDI  ⟺  CI95_upper[ Δ(P2,P0) ] < thr
```
Sxema `survival.rmst.pressure_difference` da ayirish tartibini **ochiq**
ko'rsatishi shart (`orientation: "P2_minus_P0"`) — aytilmagan ishora
qoidani hisoblanmaydigan qiladigan yana bir yo'l.

**§18.3:** RMST bu yerda `∫₀^τ S(t)dt` = **τ horizonidagi kutilgan
downtime**, va `time-to-VR` hodisa vaqti **`t_up`** da, oyna oxirida
emas — aks holda `time-to-VR ≥ 8 s` bo'lib `RMST ≡ τ` va limb **ayni
degenerat** bo'lardi. §6.1 ning `D_probe` ta'rifi (*"VR shartini
qanoatlantiruvchi oynaning **birinchi probe'i**"*) va §6.3 ning
verification-latency taqiqi bu anchor'ni qo'llab-quvvatlaydi.

**CHEKLOV (§18.4) — chegara kvantlash polida.** Muzlatilgan
qiymatlardan chiqarilgan (`P = 100 ms`, `RestartSec = 100 ms`, §6.1,
§9.2); yagona noma'lum `t_start` **o'lchanmagan**:
```
D_probe(P0) = t_start + (0.2 … 0.4) s      ⇒  RMST(P0) ≈ E[D_probe(P0)]
t_start = 0.1 s ⇒ thr ≈ 80 ms  ;  t_start = 0.8 s ⇒ thr ≈ 220 ms
          ⇒  thr ≈ 0.8 … 2.2 probe davri      (0.20 × τ = 1.6 s = 16 davr)
```
§6.1 `D_probe` ni *"±P kvantlash, har chekkada +P/2 bias"* bilan beradi.
**Demak: §9.2 ning o'zi aytgan rejimda (`P(VR|P0) ≈ 1.0`, tez tuzalish)
inkor shoxi ERISHIB BO'LMAYDI va qo'llab-quvvatlash shoxi deyarli
avtomatik. Bitta muzlatilgan jumla — dizayn AYTGAN rejimda shtamp, va
faqat dizayn BO'LMAYDI deb aytgan rejimda haqiqiy test.**

**CHEKLOV (§18.5) — uchinchi mustaqil sabab:** `thr` baholangan
kattalik, demak `CI95[Δ]` ni xuddi shu ma'lumotdan baholangan
chegaraga qarshi taqqoslash **95% qoplamaga ega emas**. Statistik
to'g'ri shakl nisbat ustida (`CI95_upper[ρ] < 1.20`), lekin §10.2
effect measure sifatida ayni **"RMST difference"** ni muzlatadi. Ya'ni
**nisbiy chegara va muzlatilgan absolut effect measure mos kelmaydi.**
Bootstrap (`Δ*` va `thr*` ni har resample'da qayta hisoblash) —
hisoblash yo'li, qaror emas, va 18.4 ning polini hal qilmaydi.

**HAL QILINMAGANI, ATAYLAB (§18.6):** 18.2 limbni hisoblanadigan
qildi, lekin 18.4 uni **ishlamaydigan** ko'rsatadi. Tuzatish referensni
o'zgartirishni, ya'ni §11 ning **ma'nosini** o'zgartirishni talab
qiladi — **shuning uchun bu tanlovni qilmayman.** F1–F4 variantlari,
narxlari va **bias yo'nalishlari** §18.6 da; **tanlov qilinmagan.**
F1 (matnga sodiq) **H1 foydasiga**, F2 (`referens = τ`) **H1 ga
qarshi** bias beradi — teskari yo'nalishlar, ya'ni tanlov texnik emas,
ilmiy. §17.5 ning O1 varianti `W_stab_pilot` ni, demak ehtimol `τ` ni
ham o'zgartirgani uchun **§17.5 va §18.6 birga hal qilinishi kerak.**

**Bias yo'nalishi ochiq e'lon qilinadi (§18.7):** 18.2 ning qarori
fail-slow / H1 **FOYDASIGA** ishlaydi, chunki inkor shoxini erishib
bo'lmaydigan qiladi. Bilib turib qabul qilinadi, chunki referens
**tanlanmagan — o'qilgan**; menga qulay variant aslida **F2** bo'lardi
(u limbni ishlaydigan va meni qattiqqo'l ko'rsatardi), lekin F2 matn
bilan qo'llab-quvvatlanmaydi; hech qanday ma'lumot mavjud emas; va
cheklovning o'zi ochiq yozilgan, demak maqolada *"fail-slow limbi bu
pilotda fail-slow'ni inkor qila olmaydi"* deb yoziladi.

**OCHIQ BO'SHLIQ (§18.8):** §10.2/§11 ning *"time-to-VR"* i §6.1 ning
uch o'lchovidan (`D_sd`, `D_probe`, `D_eff`) **birortasiga ham
bog'lanmagan**. 18.3 `D_probe` deb o'qidi (§6.1 uni ta'rifan
time-to-VR qiladi), lekin tanlov ahamiyatli: `D_eff` uzluksiz va
kvantlash poli past, va §11(b) aynan `D_eff` ni ishlatadi. **Qayd
etiladi, hal qilinmaydi — F1–F4 bilan birga hal qilinishi kerak.**

**O'LCHANMADI:** `P0` ostidagi `D_probe` taqsimoti (`p50/p90/p99`) va
`t_start`. Bu agent guest ichida **hech narsa o'lchamadi**. So'rov:
`guard-recal` `t_start` bilan birga shuni ham bersin;
`thr ≥ ~5 × P` bo'lsa 18.4 ning cheklovi amalda bezarar va F1 yetarli.

**§14.4 havolasi (§18.9) ATAYLAB yopilmadi:** §17.8 da *"muzlatilgan
matnni ochadigan amendment"* shartini o'zim qo'ygan edim; v1.7 matnni
ochmaydi, demak shart bajarilmadi. Nagging element'ni yopish uchun o'z
mezonimni jimgina yumshatish — aynan bu hujjat oldini olishi kerak
bo'lgan narsa.

### v1.5 → v1.6 (2026-10-02)

| | |
|---|---|
| **v1.5 sha256** | `5c0038976c861b334b5d721ae747db3aca54a0171ea8ef2c142af2667605f53b` |
| **v1.5 git tag** | `v0.1.5-preregistration` |
| **Sabab** | §16.8 ning ochiq savoli hal qilindi, va **§16.8 dagi ikki xato tuzatildi**; jarayonda **dizayn nuqsoni** aniqlandi |
| **O'zgardi** | **§17 qo'shildi** (yangi bo'lim). Mavjud bo'limlar raqamlari va matni O'ZGARMADI |
| **O'zgarMADI** | **hech bir operatsion ta'rif, metrika, chegara, statistik test yoki falsifikatsiya mezoni** — to'liq ro'yxat §17.9 da. **`W_stab_pilot`, `injection_offset`, `hold_cap_s` ATAYLAB o'zgartirilmadi** |
| **Yig'ilgan ma'lumot** | **yo'q** — hech qanday eksperiment ishga tushirilmagan, demak eski ta'riflar ostida qayta hisoblanishi kerak bo'lgan hech narsa yo'q |

**O'z xatomni tuzatish (§17.1).** v1.5 §16.8 ikki narsani xato yozgan:

1. *"Oyna pressure hold ichida bo'lishi SHARTmi — §4 buni aytmaydi."*
   **Xato.** §4 ning parametr jadvali ochiq aytadi: `W_stab_pilot` —
   *"sustained HOLD (≤12 s) **ichida sig'ishi kerak**"*, va §4 ning cheklov
   izohi metrikaning ma'nosini belgilaydi: *"pressure davom etayotganda
   tasdiqlangan recovery"*. Matn **jim emas** — men to'liq o'qimaganman.
2. *"bias teskari yo'nalishda (yana H1 foydasiga)"*. **Ustun had
   aksincha — H1 GA QARSHI.** §16.8 ikkita holatdan faqat kam
   ehtimollisini ko'rgan.

**NUQSON (§17.2) — muzlatilgan qiymatlardan olingan arifmetika:**

§4 ning 1-bandi oynani **`t_up`** dan boshlaydi (*"oxirgi action'dan keyingi
birinchi contract'dan o'tgan probe"*), v1.3 ning yarashtiruvchi arifmetikasi
`3 + 8 = 11 ≤ 12` esa uni **`t_inject`** dan boshlanadi deb hisoblaydi —
ya'ni jimgina **nol recovery vaqtini** nazarda tutadi. Haqiqiy shart:

```
t_up + W_stab_pilot <= t_h + hold_cap_s     =>  t_up - t_inject <= 1 s
arm A:  RestartSec(0.1) + t_start + probe kvantlashi(<=0.1) <= 1 s
                                            =>  t_start <= 0.8 s
```

→ **Muzlatilgan dizayn SUT'dan `P2` ostida ~0.8 s ichida ishga tushishni
TALAB qiladi**, §9.2 esa mexanizm (i) *"`TimeoutStartSec` oshib ketdi"* va
(iv) *"watchdog miss"* ni oldindan aytadi, ya'ni **sekin start'ni kutadi**;
`driver.py` `TimeoutStartSec = 10 s` ni default qilgan — **oyna budjetidan
12× katta**. Dizayn o'zi oldindan aytgan hodisa o'zining o'lchov oynasini
buzadi.

**Uch holat, ikki bias TESKARI yo'nalishda (§17.3):** (a) oyna
pressure'dan chiqadi, horizon ichida — VR osonlashadi ⇒ `P(VR|P2)` oshadi ⇒
**H1 ga qarshi**, va §11 ning qoidasi ostida **soxta FALSIFIKATSIYA**
yaratishi mumkin; (b) oyna horizon'dan chiqadi — haqiqiy censoring
`VR = false` deb yoziladi ⇒ **H1 foydasiga**. (a) `t_start > 0.8 s` da,
(b) `t_start > ~14 s` da yuzaga keladi (`T_trial = 40.1 s` default'i
bilan), demak **(a) ustun**.

**HAL QILINGANI (§17.4):** oynasi hold ichida bo'lmagan trial §4 ning
kattaligini **o'lchamagan**, demak `complete` + `VR = false` deb
yozilmaydi va binar `P(VR)` maxrajiga muvaffaqiyatsizlik sifatida
kiritilmaydi. Ikki yangi **`disposition_source`** qiymati —
`window_past_pressure` va `window_past_horizon`; `disposition` ikkalasida
`censored`. **§12 ning yopiq enum'iga tegilmadi** — bular `disposition`
qiymatlari emas, va §16.2 ning `(disposition, disposition_source)`
qoidasi ularni o'zgarmagan holda qamrab oladi. Ikkalasi §6.2 bo'yicha
KM/log-rank ga kiradi; darajasi `(arm × pressure)` bo'yicha alohida
beriladi, chunki **`P2` da to'plangan yuqori daraja o'zi NATIJA**.
Validator sharti: har `complete` trial uchun
`t_up + W_stab_pilot ≤ T_h` bajarilgan bo'lishi shart.

**HAL QILINMAGANI, ATAYLAB (§17.5):** 17.4 bias'ning oldini oladi,
**nuqsonni tuzatmaydi.** To'rt muzlatilgan qiymat birgalikda
qanoatlantirilmaydi: `W_stab_pilot = 8 s` (§4), `injection_offset = 3 s`
(§9.4), `hold_cap_s = 12 s` (§9.4 inv. 1), va oyna hold ichida bo'lishi
sharti (§4). **Bu savolga javob berish muzlatilgan ta'rifga tegadi,
shuning uchun men uni hal qilmayman** — qaror loyiha egasiga tegishli.
O1–O4 variantlari va har birining narxi §17.5 da, **tanlov qilinmagan**.
O3 (`hold_cap_s` ni oshirish) yagona variant hech bir ilmiy da'voni
kuchsizlashtirmaydigan, lekin §15.3 uni shartnomaviy asosda saqlagan —
ya'ni shartnomaviy va ilmiy asos **qarama-qarshi** ko'rsatadi.

**Qaror uchun zarur, lekin MAVJUD BO'LMAGAN o'lchov:** har pressure
bandida SUT start davomiyligi (`t_start`, `p50/p90/p99`). **Bu o'lchov
bajarilmadi** — bu agent guest ichida hech narsa o'lchamadi. Agar
`p90(t_start) ≤ 0.8 s` bo'lsa, nuqson amalda bezarar; aks holda O1–O4
dan biri **birinchi pilot trial'idan oldin** tanlanishi shart.

**Bias yo'nalishi ochiq e'lon qilinadi (§17.6):** 17.4 (a) va (b) ni
ikkalasini chiqaradi, (a) ustun bo'lgani uchun **sof natija ehtimol H1
foydasiga**. Buni bilib turib qabul qilaman, chunki alternativa —
kuzatilmagan natijani kuzatilgan deb yozish — ikki yo'nalishda ham
noto'g'ri, va qaror hech qanday ma'lumot mavjud bo'lmaganda ta'rif
asosida qabul qilinadi. `t_start` o'lchangandan keyin (b) ustun bo'lsa
ham **bu qaror o'zgarmaydi**.

**§8.2 ning (ii) nazorati — endi DIZAYN NUQSONI deb ataladi (§17.7).**
v1.5 §16.9 uni "ochiq savol" deb yozgan edi; aniqrog'i: §8.2 (ii)
*"injeksiya yo'q, pressure bor"* nazoratini **majburiy** deb ataydi,
§9.3 ning `3 × 2 × 20 = 120` panjarasi esa uni **o'z ichiga olmaydi**,
demak dizayn o'zining e'lon qilingan talabini bajarmaydi. Oqibati §8.2
ning so'zlari bilan: *"pressure'ning o'zi baseline"* i yo'q, demak PSI
atributsiyasi **to'liq identifikatsiya qilinmaydi**. P1 ni **bloklamaydi**
(FR-B P1 da hisoblanmaydi — §14.7), lekin atributsiya da'vosi chala
bo'ladi va maqolada shunday yozilishi kerak. Yechim §9.3 ning trial
soniga va §8.4 ning blok strukturasiga tegadi (uchinchi arm ⇒
`3 × 3 × 20 = 180`), demak **loyiha egasining qarori.**

**§14.4 ning "§7 tirik unit sharti" havolasi (§17.8)** v1.4 §15.6(2) dan
beri ochiq. Tavsiya: 17.5 ning qarori muzlatilgan matnga baribir tegadi,
shuning uchun shu amendment bu havolani tuzatish uchun to'g'ri joy.

### v1.4 → v1.5 (2026-10-02)

| | |
|---|---|
| **v1.4 sha256** | `0e1547aa9e13b6f9727ad4da9476617ad4de699653f740ad2c95b5c0688c11de` |
| **v1.4 git tag** | `v0.1.4-preregistration` |
| **Sabab** | **ikki mustaqil implementator bir xil bo'shliqni ko'rsatdi**: §12 `censored` ning analiz holatini aytmaydi, va shu jimlik barcha 60 `no_action` trial'ini birlamchi to'plamdan chiqarib tashlaydi |
| **O'zgardi** | **§16 qo'shildi** (yangi bo'lim): analiz to'plamiga kirish qoidasi, `censored` ning ikki ma'nosi, §10.1/§11 ning arm qamrovi, muzlatilmagan parametrlar qoidasi, va `boot_id` kafolatining buzilishi. Mavjud bo'limlar raqamlari va matni O'ZGARMADI |
| **O'zgarMADI** | **hech bir operatsion ta'rif, metrika, chegara, statistik test yoki falsifikatsiya mezoni** — to'liq ro'yxat §16.6 da |
| **Yig'ilgan ma'lumot** | **yo'q** — hech qanday eksperiment ishga tushirilmagan, demak eski ta'riflar ostida qayta hisoblanishi kerak bo'lgan hech narsa yo'q |

**Qaror, qisqa shaklda:**

1. **§10.1 ning birlamchi Cochran–Armitage trend testi arm `A` ichida
   hisoblanadi.** `no_action` — §8.2 ning **nazorat** arm'i (PSI
   atributsiyasi va `harm_indicator` uchun); u trend testiga yacheyka
   bermaydi, lekin §6.2 bo'yicha KM/log-rank, loop-rate va
   `recovered within T_trial: k/n` jadvallariga **kiradi**. Asos: §9.1 ning
   savoli ta'rifan arm `A` haqida, §9.2 ning to'rtala mexanizmi restart'ni
   nazarda tutadi, va pooling `P(VR) = 0` ni uchala strataga qo'shib
   trend'ni **susaytirardi**.
2. **"Horizon down holatda tugadi" — kuzatilgan no'l-hodisa, censoring
   emas.** U binar `P(VR)` maxrajiga **`VR = false`** sifatida kiradi.
   `censored` yorlig'i ikki holatni birlashtiradi va §4 ularni allaqachon
   boshqacha ishlaydi: §4 `censored` ni *"probe uzilishi → `failed` emas"*
   ma'nosida (**kuzatilmagan natija**) ishlatadi, §6.2 esa **downtime
   davomiyligini** censor qiladi, binar natijani emas. §4 ning VR ta'rifi
   horizon bilan chegaralangan, demak `t_up` bo'lmagan trial uchun
   `VR = false` **to'liq aniqlangan**.
3. **Yangi enum qiymati kerak emas**: farq allaqachon `reduce.py` ning
   **`disposition_source`** maydonida (`"probe_gap"` / `"down_at_horizon"`).
   Qoida: birlamchi to'plam **`(disposition, disposition_source)`** jufti
   bilan aniqlanadi. §12 ning yopiq enum'iga **tegilmadi**.
4. **§11 ning `P0` vs `P2` RMST kontrasti ham arm `A` ichida** — §10.1
   bilan bir xil qamrov, aks holda ikki bo'lim turli arm'da bo'lib
   qolardi. §10.2 ning "har arm uchun KM" i — taqdimot birligi; `A` vs
   `no_action` log-rank §8.2 ning atributsiya savoliga javob beradi, H1 ga
   emas. §10.4 bo'yicha birlamchi test **bitta**.

**Zarar `no_action` da emas, arm `A` da kattaroq** (§16.3): `P2` ostida
qaytmagan arm `A` trial'lari — **aynan H1 kutgan natija** — chiqarib
tashlansa, `P(VR|P2)` 1 ga siljiydi, trend susayadi, va §11 ning
falsifikatsiya qoidasi siljigan baho ustida qo'llanadi. Ya'ni **"null"
dunyodan emas, eksklyuziyadan tug'ilishi mumkin.** §6.2 aynan shuni
*"klassik yashirin bias"* deb nomlaydi. **Bu qaror H1 foydasiga ishlaydi
va shu holda ochiq e'lon qilinadi** — u faqat hech qanday ma'lumot mavjud
emasligi uchun qonuniy.

**Kod o'zgartirilMADI.** `reduce.PRIMARY_DISPOSITIONS == ("complete",)` —
muzlatilgan qiymat emas, §12 ning jimligini implementator hal qilgan joy;
uni tuzatish **muzlatilgan matnga moslashtirish**, amendment emas. Ikkala
modul ham test bilan qoplangan, demak o'zgarish ataylab qilingan qaror
bo'lishi kerak. §16.4 ikki konstantaning qaysi savolga javob berishini
qayd etadi va eksklyuziya darajasi **qaysi to'plam ustida hisoblanganini
nomlashi shart** degan qoidani muzlatadi.

**Yangi o'lchangan fakt (v1.5 ning eng og'ir topilmasi):** §1 va §14.6(5)
ning `boot_id` kafolati **shu host'da yolg'on**. 49 s oraliqda, `boot_id`
**aynan bir xil** bo'lgan holda PID 1 ning yoshi `62.46 s → 9.68 s` ga
**orqaga ketdi** (to'liq o'lchov §16.11 da). §14.6(5) **zarur, lekin
yetarli emas**; PID 1 ning `starttime` i ham yozilishi va tekshirilishi
shart. §4 ning 3- va 4-bandlarining PID 1 restart ostidagi xatti-harakati
**o'lchanmadi** va birinchi trial'dan oldin o'lchanishi shart.

**Hal qilinMAGAN, ataylab (har biri o'z qarorini talab qiladi):**
§16.8 `W_stab` oynasi horizon'dan oshib ketsa (`W_stab` ta'rifiga tegadi);
§16.9 §8.2(ii) varianti §9.3 ning 120-trial panjarasida yo'q (trial soniga
tegadi); §16.10 oltita muzlatilmagan parametr — **qiymat emas, qoida
muzlatildi**, chunki men ularning hech birini o'lchamadim.

### v1.3 → v1.4 (2026-10-02)

| | |
|---|---|
| **v1.3 sha256** | `c9d7148138b0c9e15e8d53d4fe7914aaafd7c01e3c7dca06fdacf65ba5cc835a` |
| **v1.3 git tag** | **yo'q** — qarang §15.6(1) |
| **Sabab** | **o'lchov muhiti o'zgardi.** Pre-registration o'zi qaysi muhitga tegishli ekanini qayd etishi shart |
| **O'zgardi** | **§15 qo'shildi** (yangi bo'lim): muhit fingerprint'i, `systemd-oomd` yo'qligi, va §8.5 ni bu mashinada bajarib bo'lmasligi. Mavjud bo'limlar raqamlari va matni O'ZGARMADI |
| **O'zgarMADI** | **hech bir operatsion ta'rif, metrika, chegara, statistik test yoki falsifikatsiya mezoni** — to'liq ro'yxat pastda |
| **Yig'ilgan ma'lumot** | **yo'q** — hech qanday eksperiment ishga tushirilmagan, demak eski ta'riflar ostida qayta hisoblanishi kerak bo'lgan hech narsa yo'q |

**Nima o'zgardi (muhitda, hujjatda emas):** `docs/architecture/02-guard-kalibratsiyasi.md`
dagi har bir chegara bitta aniq mashinada o'lchangan — o'sha hujjat sarlavhasi:
*"Kali 2026.3, kernel 7.1.5, systemd 261, 15Gi RAM, 12 CPU"*, `systemd-oomd`
qurollangan. Loyiha endi boshqa muhitda ishlaydi: kernel
`6.6.87.2-microsoft-standard-WSL2`, systemd `257`, `MemTotal = 10183888 kB`
(9.71 GiB), `systemd-oomd` **binari ham, uniti ham yo'q**, `cpufreq` va
`thermal_zone*` sysfs interfeyslari **yo'q**. To'liq o'lchangan fingerprint va
har bir qiymat ortidagi buyruq — **§15.1**.

Pre-registration `run_meta.preregistration_sha256` orqali har bir run'ga
bog'lanadi. Agar u o'zi qaysi muhitga tegishli ekanini aytmasa, *"qaysi
ta'riflar ostida o'lchangan"* savoliga javob chala bo'ladi — chegaralar
muhitdan o'lchangan, demak muhit ta'rifning bir qismi.

**O'zgarMAGAN qiymatlar — to'liq ro'yxat.** Hammasi muzlatilgan holida qoladi:

| qiymat | bo'lim |
|---|---|
| `θ = 0.8` | §4 |
| `W_stab = 60 s`, `W_stab_pilot = 8 s` | §4 |
| sensitivity sweep `W_stab ∈ {8,10,30,60,120}` × `θ ∈ {0.5,0.8,0.95}` | §4 |
| invalidator'lar yopiq enum'i | §4 |
| `T_conn = 50 ms`, `T_rt = 50 ms`, `P = 100 ms` | §2 |
| `k_f = 3` (⇒ `D_f = 300 ms`) | §3 |
| `ε = 32 MiB`, quiescence chegarasi `0.05`, `T_q = 5 s`, `T_w = 15 s`, `T_w_max = 120 s` | §8.4 |
| `hold_cap_s = 12 s`, `guard_sustain_s = 15 s` (ikki xavfsizlik invarianti) | §9.4 |
| arm'lar `A` va `no_action`; `P0`/`P1`/`P2`; **20 blok / 120 trial** | §9.3 |
| birlamchi test: **Cochran–Armitage** trend testi | §10.1 |
| Newcombe/Wilson risk difference CI, Clopper–Pearson yacheyka CI | §10.1 |
| Kaplan–Meier + log-rank; **RMST**, `τ = 8 s`; Cox/HR ishlatilmaydi | §10.2, §11 |
| Holm–Bonferroni multiplicity | §10.4 |
| **falsifikatsiya qoidasi** (trend p > 0.05 **va** 95% CI yuqori chegarasi < 0.15) | §11 |
| halol power bayonoti va davom etish mezonlari | §11 |
| disposition yopiq enum'i | §12 |
| data schema, envelope, majburiy maydonlar, validator invariantlari | §14 |

**Agar bu qiymatlardan birortasini o'zgartirish kerak bo'lsa — bu BOSHQA va
ancha og'ir amendment turi**, va u alohida yoziladi, o'z sababi va o'z
asoslanishi bilan. v1.4 bunday o'zgarish **qilmaydi**.

**Nega bu amendment qonuniy:** hech qanday ma'lumot yig'ilmagan, hech qanday
natija ko'rilmagan, va o'zgarish hech bir endpoint, chegara yoki testga
tegmaydi. Qo'shilgan narsa — **muhit fakti va undan kelib chiqadigan cheklov**,
ya'ni ilgari yozilmagan, lekin natijani o'qish uchun zarur kontekst.

**Eng muhim bir fakt, chalkashtirilmasligi uchun ochiq yozilgan:**
`systemd-oomd` yo'qolgani §9.4 ning `hold_cap_s = 12 s` cheklovini
**bo'shashtirMAYDI.** Cheklovning *sababi* qisman muhitdan shartnomaga
siljidi; cheklovning *qiymati* o'zgarmadi. Batafsil: **§15.3**.

**Eng noqulay bir fakt, yashirilmagani uchun ochiq yozilgan:** §8.5 ning
chastota/termal tekshiruvi bu mashinada **bajarilishi mumkin emas**, chunki
ikkala sysfs interfeysi ham mavjud emas. Bu timing taqqoslashlari validligiga
haqiqiy tahdid va maqolaning Limitations bo'limiga **yumshatilmasdan** kiradi.
Batafsil: **§15.4**.

### v1.2 → v1.3 (2026-09-29)

| | |
|---|---|
| **v1.2 sha256** | `9a663f73dd5699f595cf6f5fb69307f88810853174dbbfea63b9be64a195f59f` |
| **Sabab** | §9.4 va §4 orasida **ichki ziddiyat**; ikki parametr umuman raqamlanmagan |
| **O'zgardi** | §4, §8.4, §9.4 ning **aniqlashtirilishi** va ikki parametrning raqamlanishi |
| **O'zgarMADI** | hech bir metrika, statistik test yoki falsifikatsiya mezoni |
| **Yig'ilgan ma'lumot** | **yo'q** |

**Ziddiyat (implementator aniqladi, men tasdiqladim):**

§9.4 "ramp 5 s → hold, injeksiya hold'ga 3 s kirgach → **umumiy pressure-on
≤ 12 s**" deydi. §4 esa `W_stab_pilot = 8 s` ni talab qiladi va u pressure
oynasi ichida bo'lishi kerak.

```
Agar 12 s cheklovi ramp+hold bo'lsa:  hold ≤ 12 − 5 = 7 s
Lekin kerak:                          injeksiya(3) + W_stab(8) = 11 s
7 < 11  →  ZIDDIYAT
```

**Hal qilindi:** `12 s` cheklovi **faqat sustained hold** ga tegishli, ramp'ga
emas. Ramp ham pressure beradi, shuning uchun **ikkinchi invariant** qo'shildi:

```
hold_s + ramp_above_threshold_s ≤ 15 s
```

15 s — guard'ning `sustain_max_seconds` i. Bu aynan guard o'lchaydigan
kattalik (2 s oynadagi tezlik ≥ 0.35) ustidan qo'yilgan cheklov, demak
"to'g'ri ishlayotgan trial guard'ni ishga tushirmaydi" kafolati matematik
jihatdan yopiladi.

**Raqamlanмаган parametrlar (endi muzlatildi):**

§8.4 "baseline ±ε" va "quiescence chegarasi" deb yozgan, lekin raqam bermagan.
Ikkalasi ham endi belgilandi (pastga qarang). Ular kalibratsiya bilan
tasdiqlanishi kerak; agar kalibratsiya ularni erishib bo'lmas ko'rsatsa, bu
**ma'lumot bilan asoslangan amendment** bo'ladi, taxmin bilan emas.

**Kampaniya vaqti:** §9.4 dagi "≈75 s/trial" fazalar yig'indisidan (52 s)
23 s katta. Bu farq unit yaratish/yo'q qilish, D-Bus round-trip va ma'lumot
flush'idan iborat. U **taxmin qilinmaydi, o'lchanadi** — kampaniya bahosi
o'lchangan qiymatni ishlatishi shart.

### v1.1 → v1.2 (2026-09-29)

| | |
|---|---|
| **v1.1 sha256** | `ff4233e1a5e60fcf4cdc75d07bf7871a6dbec688b6b5e5f38fc98b5acab1c966` |
| **v1.1 git tag** | `v0.1.1-preregistration` |
| **Sabab** | data schema bo'limi umuman yo'q edi, lekin unga havola qilinardi |
| **O'zgardi** | **§14 qo'shildi** (yangi bo'lim). Mavjud bo'limlar raqamlari O'ZGARMADI |
| **O'zgarMADI** | hech bir ta'rif, chegara, metrika, statistik test yoki falsifikatsiya mezoni |
| **Yig'ilgan ma'lumot** | **yo'q** — hech qanday eksperiment ishga tushirilmagan |

**Qanday topildi:** ikki mustaqil implementator (prober va reducer) bir-biridan
xabarsiz bir xil nuqsonni ko'rsatdi — `revix/schema.py` va
`docs/architecture/03-sut-protokoli.md` "§8 (data schema)" ga havola qiladi,
lekin §8 aslida *Confound nazorati*. Data schema faqat rejalashtirish hujjatida
bor edi va muzlatilgan shartnomaga ko'chirilmagan.

Natijasi: ikkalasi ham record kontraktini **mahalliy** e'lon qilishga majbur
bo'ldi. Bu aynan pre-registration oldini olishi kerak bo'lgan holat.

**Nega §14, §8 emas:** mavjud bo'limlarni qayta raqamlash `schema.py`,
`reduce.py`, `prober.py` va barcha hujjatlardagi havolalarni buzardi. Yangi
bo'lim oxiriga qo'shildi, noto'g'ri havolalar §14 ga tuzatildi.

**Bu amendment qonuniy:** hech qanday ma'lumot yig'ilmagan, hech bir endpoint,
chegara yoki test o'zgarmagan. Qo'shilgan narsa — nima YOZILISHI kerakligi,
ya'ni allaqachon nazarda tutilgan, lekin yozib qo'yilmagan shartnoma.

### v1 → v1.1 (2026-09-29)

| | |
|---|---|
| **v1 sha256** | `0b1fdd18783bd27b22d0d64291eea657a83857f22af14a772d037dfd33075130` |
| **v1 git tag** | `v0.1.0-preregistration` |
| **Sabab** | systemd slice nomlash tuzog'i empirik aniqlandi |
| **O'zgardi** | faqat cgroup/slice **nomlari** |
| **O'zgarMADI** | hech bir ta'rif, chegara, metrika, statistik test yoki falsifikatsiya mezoni |
| **Yig'ilgan ma'lumot** | **yo'q** — hech qanday eksperiment ishga tushirilmagan edi |

**Nima aniqlandi:** systemd slice nomlarida `-` ierarxiya ajratuvchisi, demak
`a-b.slice` avtomatik `a.slice/a-b.slice` bo'lib joylashadi. Bu mashinada
empirik tasdiqlangan (`systemd-run --user --slice=revix-envcheck.slice` →
`.../revix.slice/revix-envcheck.slice`).

Natijada boshlang'ich `revix-harness.slice` nomi **sibling bo'lmaydi**, u
`revix.slice` ning childi bo'lib qolar edi — va harness'ning PSI'si
eksperiment slice'ining PSI'siga qo'shilib, §8.2 oldini olmoqchi bo'lgan
feedback artefaktini yaratardi. Ya'ni bu kosmetik emas, **validlik xatosi**.

| eski | yangi | roli |
|---|---|---|
| `revix.slice` | **`revixlab.slice`** | eksperiment (SUT, bystander, generator) |
| `revix-harness.slice` | **`revixmon.slice`** | harness (driver, prober, sampler, guard) |

Ikkisi ham `user@1000.service` ning to'g'ridan-to'g'ri childi, ya'ni haqiqiy
sibling. Service nomlaridagi dash muammo emas (faqat *slice* nomlari
ierarxiya hosil qiladi).

**Bu amendment qonuniy, chunki:** hali hech qanday ma'lumot yig'ilmagan, hech
qanday natija ko'rilmagan, va o'zgarish hech bir endpoint, chegara yoki testga
tegmaydi. Agar ma'lumot yig'ilgandan keyin o'zgarish kerak bo'lsa — bu yerga
yoziladi va **eski ma'lumot eski ta'riflar ostida qayta hisoblanadi**, yangi
ta'riflar ostida emas.

---

> **Nega bu fayl birinchi yoziladi?** REVIX ning ilmiy hissasi arxitektura emas, **o'lchov**.
> Agar hissa o'lchov bo'lsa, ta'riflar mahsulotning o'zi. Ta'riflarni natijani ko'rgandan keyin
> tanlash imkoniyati — bu ishni ilmiy jihatdan qiymatsiz qiladi.

---

## 0. Nima o'lchanmaydi (qamrovdan tashqari)

P1 quyidagilar haqida **hech qanday** da'vo qilmaydi:

- H2 (PSI-gating vs systemd native backoff) — A-vs-B taqqoslash P1 da **yo'q** (§6.3).
- REVIX arm C, failure classifier, action selector, `Repairs()` matritsasi.
- Host-wide (global `/proc/pressure`) pressure.
- `hold_cap_s` dan uzoq sustained pressure — **v1.11** dan beri **13 s**
  (§9.4 invariant 1; avval 12 s, §17.5 O3 bilan siljidi). **Bu band cap'ni
  KUZATADI, literal raqamni emas:** har bir P1 trial'i aynan bitta sustained
  hold ichida o'lchanadi, demak **uzoq davomiylik rejimi** — `W_stab = 60 s`
  ning to'liq dizayni va daqiqalar tartibidagi sustained pressure — P1 ning
  qamrovidan **tashqarida qoladi** (§4 ning *“P1 dagi ochiq cheklov”* i,
  §15.5). **Qamrov sinfi o'zgarmadi; faqat chegara 1 s siljidi.**
- Nazorat qilinadigan IO stall (`io` controller delegated emas).
- Haqiqiy xizmatlar (SUT sintetik).

---

## 1. Vaqt disiplinasi

Barcha davomiylik **`CLOCK_MONOTONIC`, mikrosekund**da hisoblanadi.

Sabab: systemd'ning `*TimestampMonotonic` D-Bus property'lari va journald'ning
`__MONOTONIC_TIMESTAMP` aynan shu domenda. Bitta clock — konversiya yo'q, konversiya xatosi yo'q.

- Har bir record'da **`boot_id`**. Monotonic qiymatlar faqat bitta boot ichida taqqoslanadi;
  `boot_id` bu shartni tekshirib bo'ladigan qiladi.
- `CLOCK_REALTIME` (`real_us`) faqat inson o'qishi va tashqi log'lar bilan bog'lash uchun
  yoziladi. **Hech qanday davomiylik hisobida ishlatilmaydi.**
- `clock_getres` 1 ns beradi; yuk ostida amaliy aniqlik o'nlab µs. Bu barcha
  taqqoslashlar uchun yetarli, chunki eng kichik qiziqarli interval 100 ms (probe davri).

---

## 2. Service contract — VR ta'rifining asosi

SUT `sleep infinity` bo'lsa, quyidagi barcha ta'riflar process-liveness'ga qulaydi va
hissa yo'qoladi. Shuning uchun SUT maxsus yozilgan xizmat:

- `Type=notify`, `sd_notify` bilan `READY=1` va `WATCHDOG=1`
- `SOCK_SEQPACKET` unix control/probe socket
- deterministik ish tsikli, **monotonic progress counter** bilan
- har bir probe javobida `INVOCATION_ID` va pid echo qiladi

**Contract — uchta shart, hammasi bajarilishi kerak:**

| # | shart | parametr |
|---|---|---|
| a | socket `T_conn` ichida accept qiladi | `T_conn = 50 ms` |
| b | to'g'ri formatdagi javob `T_rt` ichida keladi | `T_rt = 50 ms` |
| c | `progress_counter` oldingi probe'dan **qat'iy katta** | — |

Probe davri **`P = 100 ms`** (10 Hz), absolut `CLOCK_MONOTONIC` deadline'larda.

---

## 3. Failure — ikki mustaqil detektor

Ikki detektor **alohida log'lanadi va hech qachon bitta raqamga birlashtirilmaydi.**

| detektor | manba | timestamp | nimani ko'rmaydi |
|---|---|---|---|
| `F_sd` | D-Bus: `ActiveState` ≠ `active`, yoki `Result` ≠ `success` | `ActiveExitTimestampMonotonic` / `InactiveEnterTimestampMonotonic` | hang (agar `WatchdogSec=` qo'yilmagan bo'lsa) |
| `F_probe` | prober: contract `k_f` marta ketma-ket buzildi | birinchi buzilgan probe'ning `mono_us_send` | hech narsa, lekin probe davriga kvantlangan |

**`k_f = 3`** → `D_f = 300 ms`. Sabab: bitta probe'dagi shovqinni (scheduling jitter,
socket backlog) failure deb hisoblamaslik.

### Injeksiya vaqti
`t_inject` = triggerlovchi chaqiruv qaytgandan keyingi monotonic vaqt, **ikki tomondan
bracket qilingan**: harness'ning `mono_us_before_call` / `mono_us_after_call`, **va**
SUT'ning o'z ichki "fault armed/fired" record'i.

Ramp fault'lar (leak, pressure) uchun qo'shimcha `t_fault_effective` = birinchi contract
buzilishi yoki `memory.events.oom_kill` ning birinchi o'sishi.

> **Ochiq cheklov:** `t_fault_effective` — **kuzatuv**, xizmat qachon nosog'lom bo'lgani
> haqidagi ground truth emas. Ramp fault'lar uchun service-level onset tabiatan noaniq;
> probe davri (100 ms) — e'lon qilingan noaniqlik chegarasi.

### Detection latency
`L_det = t_detect − t_fault_effective`, **har detektor uchun alohida** beriladi.

Clean crash uchun `L_det_sd` **manfiy** bo'lishi mumkin — systemd `SIGCHLD` orqali keyingi
probe'dan oldin biladi. Bu xato emas, ma'lumot: crash uchun systemd tezroq, hang uchun
prober yagona imkoniyat.

---

## 4. Verified Recovery (VR)

Epizod `E` verified-recovered, agar `[t_up, t_up + W_stab]` oynasi mavjud bo'lsa va unda:

1. `t_up` = `E` ning oxirgi action'idan keyingi birinchi contract'dan o'tgan probe;
2. oynadagi **har bir** probe contract'dan o'tadi;
3. `InvocationID` butun oyna davomida o'zgarmaydi (yashirin restart yo'q);
4. `NRestarts` butun oyna davomida o'zgarmaydi;
5. **oyna throughput'i ≥ `θ · R_ref`**, `R_ref` = shu trial'ning fault'dan oldingi throughput'i;
6. SUT cgroup'da yangi `memory.events.oom_kill` yo'q;
7. host guard ishlamagan.

**5-band VR ni process-liveness'dan ajratadigan narsa.** Qaytgan lekin 5% throughput'da
ishlayotgan xizmat recovered emas. Busiz butun hissa "process tirikmi?" ga qulaydi.

### Parametrlar
| parametr | qiymat | izoh |
|---|---|---|
| `θ` | **0.8** | pre-fault throughput'ning ulushi |
| `W_stab` | **60 s** (to'liq dizayn) | mexanik asos: λ tezlikdagi leak va M shift uchun refail vaqti ≈ M/λ; λ shunday tanlanadi-ki bu 15–25 s bo'ladi, demak 60 s ≥2 refail tsiklini qoplaydi |
| `W_stab_pilot` | **8 s** | sustained HOLD (≤13 s) ichida sig'ishi kerak: injeksiya hold'ga 3 s kirgach boshlanadi, demak 3 + 8 = 11 ≤ 13 ✓ (v1.3 aniqlashtirishi; `hold_cap_s` **v1.11** da 12 s → 13 s — §17.5 O3, zaxira 1 s → 2 s) |

> **P1 dagi ochiq cheklov:** `W_stab_pilot = 8 s` bilan o'lchanadigan narsa —
> **"pressure davom etayotganda tasdiqlangan recovery"**, 60 s sustained recovery **emas**.
> To'liq `W_stab` root (system slice) yoki QEMU guest talab qiladi. Bu maqolada shunday
> yoziladi, yumshatilmaydi.

### Invalidator'lar (yopiq enum)
`contract_fail`, `invocation_changed`, `nrestarts_changed`, `oom_kill`,
`throughput_below_theta`, `guard_fired`.

**Probe uzilishi > 2×P** → trial `censored`, **`failed` emas**.
Instrumentatsiya yo'qolishi hech qachon jimgina natijaga aylanmaydi.

### Sensitivity sweep (oldindan e'lon qilingan)
`W_stab ∈ {8, 10, 30, 60, 120} s` × `θ ∈ {0.5, 0.8, 0.95}` — **raw probe trace'lardan
post-hoc hisoblanadi**, eksperiment qayta ishga tushirilmaydi.

Sabab: "siz `W` ni natija chiqishi uchun tanlagansiz" — har qanday shu turdagi metrikaga
birinchi hujum. Javob — bitta raqam emas, **butun egri chiziq**. Shuning uchun §8 raw
trace'larni saqlashni talab qiladi.

---

## 5. False Recovery — yangi metrika

**Ikki operatsion jihatdan farqli sub-metrika. Hech qachon bitta raqamga aralashtirilmaydi.**

### FR-A — muddatidan oldin muvaffaqiyat (oracle-free, BIRLAMCHI)

```
FR_A = 1   ⟺   actor_success_signal == true   AND   VR == false
```

`actor_success_signal` — **aktorning o'z da'vosi**:
- systemd uchun: unit `active` holatiga yetdi (`Type=notify` da `READY=1` qabul qilindi);
- REVIX uchun: engine `state=RECOVERED` chiqardi.

Ikkala operand ham **log'langan fakt**. **Oracle yo'q. Fault-class label yo'q. Matritsa yo'q.**

Har action uchun va har epizod uchun hisoblanadi (epizod darajasida = ≥1 FR-A action).

> **Loyihaning qoidasi:** dizayn shunday bo'lishi kerak-ki, agar reviewer FR-B ni butunlay
> chiqarib tashlasa ham, **FR-A yolg'on maqolani ko'tara oladi.**

### FR-B — action/fault mos kelmasligi (matritsaga nisbatan, IKKILAMCHI)

```
FR_B = 1   ⟺   action_class ∉ Repairs(injected_fault_class)   OR   harm_indicator == true
```

`harm_indicator` **o'lchanadi, da'vo qilinmaydi**. `[t_action_begin, t_action_begin + 5 s]`
ichida quyidagilardan biri:
- slice yoki host `memory.pressure` stall **tezligi** (`total=` delta'laridan) action'dan
  oldingi 5 s tezligidan **≥ 1.5×** oshdi; **yoki**
- o'rab turgan slice'da `oom_kill` oshdi; **yoki**
- bystander xizmat contract'ini yo'qotdi.

`Repairs()` **empirik kalibrlanadi, farmon bilan belgilanmaydi**: alohida kalibratsiya
eksperimenti har `(fault_class × action_class)` uchun `P̂(VR | f, a)` o'lchaydi, so'ng

```
Repairs(f) = { a : ClopperPearson_lower95( P̂(VR|f,a) ) ≥ p_min }
```

**`p_min = 0.7`** (oldindan muzlatilgan).

Kalibratsiya `VR` dan foydalanadi — u contract asosida va oracle-free — demak
sirkulyarlik yo'q.

> **FR-B nimani isbotlamaydi:**
> 1. Field'da fault **klassifikatsiya** haqida hech narsa. Injected label'lar ustidagi FR-B —
>    **mukammal klassifikatsiya sharti ostidagi yuqori chegara.**
> 2. Tashqi validlik: laboratoriya fault'lari toza va yolg'iz; real incident'lar murakkab va kaskadli.
> 3. `Repairs()` **bizning** action to'plamiga nisbatan. Action qo'shilsa matritsa o'zgaradi,
>    demak FR-B faqat bitta muzlatilgan matritsani baham ko'rgan arm'lar orasida taqqoslanadi.
>
> P1 da `Repairs()` **hisoblanmaydi** (kalibratsiya eksperimenti hali yo'q), demak
> **P1 da FR-B berilmaydi**. Faqat FR-A.

### 🚨 Sirkulyarlik — muzlatilgan kafolatlar

**PSI hech qanday ta'rifga kirmaydi. PSI faqat prediktor / kovariata.**

Boshlang'ich loyiha spetsifikatsiyasidagi FR ta'rifi — *"host memory exhaustion sababli
ishdan chiqqan xizmatni restart qilish"* — aynan tuzoq. FR ni shunday ta'riflab, keyin
"PSI gating FR ni kamaytiradi" deb "isbotlash" **tavtologiya**, natija emas.

To'rt kafolat, maqolada ochiq yoziladi:

1. **PSI failure, VR yoki FR ta'rifiga kirmaydi** — faqat prediktor sifatida.
2. **O'lchov prober'i hech bir arm'ning qaror yo'liga ulanmaydi**, uchala arm'da bir xil
   ishlaydi, va probe narxi arm'lar bo'yicha bir xil. (Agar arm C prober ishlatsa — u
   **alohida** process bo'ladi.)
3. `W_stab`, `θ`, `p_min` shu faylda oldindan muzlatilgan; sensitivity sweep e'lon qilingan.
4. **FR-A birlamchi va oracle-free; FR-B ikkilamchi va "matrix-relative" deb belgilanadi.**

---

## 6. Downtime va latency

### 6.1 Downtime — uchta ichma-ich o'lchov, hammasi beriladi

| o'lchov | qayerdan → qayerga | manba | nimani ko'rmaydi |
|---|---|---|---|
| `D_sd` | `ActiveExitTimestampMonotonic` → keyingi `ActiveEnterTimestampMonotonic` | D-Bus, µs | **ortiqcha kredit**: `active` ≠ to'g'ri xizmat qilayapti |
| **`D_probe`** (asosiy) | failure'dan oldingi oxirgi o'tgan probe → VR shartini qanoatlantiruvchi oynaning birinchi probe'i | prober | ±P kvantlash, har chekkada +P/2 bias — **e'lon qilinadi, jimgina "tuzatilmaydi"** |
| `D_eff` | `P·n_failing_probes + ∫ max(0, 1 − r(t)/R_ref) dt` | prober throughput | yo'q — **brownout'ni ham hisoblaydi** |

`D_eff` — C ning B dan halol ustun kelishi eng ehtimoliy joyi, va `D_sd` eng chalg'ituvchi
joyi: `active` lekin 20% throughput'dagi xizmat `D_sd` bo'yicha **nol** downtime ko'rsatadi.

### 6.2 Right censoring — tashlanmaydi, ishlanadi

`trial_downtime` = horizon `T_trial` ichidagi epizod downtime'larining yig'indisi.
Horizon tugasa va xizmat hali down bo'lsa → downtime **`T_trial` da censored**.

**Recovery bo'lmagan trial'larni tashlash — klassik yashirin bias**, va u tez ishdan
chiqadigan arm'ni chiroyli ko'rsatadi. Muzlatilgan qoida:

- censored trial'lar Kaplan–Meier / log-rank analiziga **kiradi**;
- censored trial'lar loop-rate metrikasiga **kiradi**;
- har bir jadvalda **"`T_trial` ichida recovered: k/n"** shartli vaqt taqsimoti bilan
  **birga** beriladi.

### 6.3 Latency — ikki soxta taqqoslashning oldini olish

**`L_dec = t_action_issue − t_detect`**, lekin **`policy_delay_us` (sozlangan kutish
vaqti) ALOHIDA field**.

> Sabab: B ning 10 s `RestartSec`ini "decision latency" deb hisoblab, keyin "C tezroq
> qaror qiladi" deyish — **soxta taqqoslash**. Arm'lar **downtime** bo'yicha taqqoslanadi,
> va downtime siyosat kechikishini haqli ravishda o'z ichiga oladi.

**`StartLimitBurst=0` (o'chirilgan) barcha arm'larda.** Give-up mantiqi harness'da,
hamma uchun bitta qoida.

> Sabab: aks holda arm A ning raqamlari systemd'ning start rate limiter'i bilan
> belgilanadi, va reviewer to'g'ri aytadi: "bu taqqoslash backoff haqida emas,
> `StartLimit` haqida."

**"Verification latency" achievement metrikasi sifatida BERILMAYDI** — muvaffaqiyatli VR
uchun u ta'rifan `W_stab`ga teng. O'rniga `time_to_first_up = t_up − t_detect`.

### 6.4 Recovery loop
`loop_rate = Δ NRestarts / T_trial`.
`loop_detected = 1` ⟺ `T_trial` ichida ≥5 invocation va **barchasi** VR dan o'tmagan.

---

## 7. Pressure o'lchovi — `total=` asosiy, `avgN` ikkilamchi

`avgN` (avg10/avg60/avg300) — eksponensial silliqlangan, **2 s kadensda yangilanadi**.
Fault boshlanishi failure'dan <2 s oldin bo'lsa, `avg10` umuman siljimasligi mumkin.

**`total=` (monotonik µs akkumulyator) atributsiya uchun qat'iy yaxshiroq va ASOSIY o'lchov:**

```
stall_fraction(t1, t2) = ( total(t2) − total(t1) ) / ( t2 − t1 )
```

Silliqlash yo'q, oyna mos kelmasligi yo'q.

**Muzlatilgan qarorlar:**

- Namuna olish: **4 scope** (host, `revixlab.slice`, SUT, bystander) × 3 resurs × {some, full},
  **10 Hz**, **har scope uchun alohida o'qish timestamp'i** (o'qishlar bir vaqtda emas —
  ularni bir vaqtda deb ko'rsatish xato bo'ladi).
- Pressure kovariatalari **hodisaga bog'langan interval'lar**, wall-clock'ga emas:
  `P_pre[Δ]` = `[t_fault_effective − Δ, t_fault_effective)`,
  `P_act[Δ]` = `[t_action_begin, t_action_begin + Δ)`,
  **Δ ∈ {0.5, 1, 2, 5, 10} s**.
- **Asosiy: `Δ = 2 s` pre-fault.** Qolgan Δ lar — sensitivity.
- **Asosiy scope: `revixlab.slice`** (per-service gate haqiqatan atributsiya qila oladigan scope).
  Host va SUT scope'lari — exploratory. Uchala scope × 3 resurs berilsa **Holm korreksiyasi**.
  **Ahamiyatlilik uchun scope bo'ylab "shopping" qilinmaydi** — reviewer taqqoslashlarni sanaydi.
- `avgN` ham yoziladi: (a) arzon deployed gate aynan shuni o'qiydi; (b) "laggy `avg10` gate
  vs aniq `total` gate" — bepul, o'z-o'zicha kichik natija.

> **Kvantlash ogohligi (muzlatilgan):** PSI ichki yangilanish kadensi 2 s va `total`
> partiyalarda kreditlanadi. Bitta 100 ms delta 0 o'qib, keyin sakrashi mumkin.
> **100 ms delta oniy tezlik deb talqin qilinmaydi.** Tezlik uchun ≥2 s oyna.

**Unprivileged PSI poll trigger ishlatilmaydi** — Linux 6.5+ da unprivileged trigger
oynasi 2 s karrasi bo'lishi shart. `total` polling ishlatiladi; trigger keyingi
optimizatsiya, dependency emas.

---

## 8. Confound nazorati (muzlatilgan)

### 8.1 Yashirin o'zgaruvchi — H1 ni o'ldiradigan e'tiroz

> *"`P(VR | high PSI)` past, chunki pressure sababi — restart'i baribir muvaffaqiyatsiz
> bo'ladigan memory leak'ning o'zi."*

Pressure va fault class **konstruksiya bo'yicha** confound. Ikki majburiy yechim:

1. **H1 fault class ICHIDA sinaladi.** Pooled analiz ta'rifan confounded.
2. **Pressure ekzogen va ortogonal injeksiya qilinadi** — fault class'dan **mustaqil**
   randomizatsiya qilingan, SUT'ning fault'iga aloqasi yo'q generatordan.

→ **`clean_crash × exogenous pressure` — H1 ning eng toza testi va P1 ning asosiy
yacheykasi.** `clean_crash` tinch holatda p≈1 bilan restart'dan tuzaladi va o'zi pressure
yaratmaydi; demak pressure'ni o'zgartirish **pressure'ning sababiy ta'sirini izolyatsiya
qiladi.** Manipulyatsiyasiz PSI-vs-natija faqat korrelyatsion bo'ladi.

### 8.2 O'z perturbatsiyasi
Restart CPU/xotira/IO iste'mol qiladi → PSI ni **oshiradi**. Gate PSI o'qisa va action PSI ni
oshirsa — feedback loop va artefakt.

- Harness (**driver, prober, psi_sampler, guard**) **sibling slice**da: `revixmon.slice` (dash'siz nom — Amendment log'ni ko'ring).
  Kovariata sifatida ishlatiladigan hech bir scope ichida emas.
- Harness'ning o'z `CPUUsageNSec` / `MemoryPeak` log'lanadi va hisobotda beriladi.
- **Probe narxi budjeti:** prober CPU'si trial bo'yicha o'lchanadi, yadro foizida beriladi.
  >1% bo'lsa sekinlashtiriladi. **Arm'lar bo'yicha bir xil ushlanadi.**
- **No-action arm MAJBURIY**, opsional emas: (i) injeksiya + `Restart=no`, (ii) injeksiya yo'q —
  har pressure darajasida. Busiz "restart PSI ni oshirdi" ni "fault PSI ni oshirdi" dan
  ajratib bo'lmaydi va `harm_indicator` talqin qilinmaydi.

### 8.3 Page cache / warm-cold
P1 da cache **iliq va barqaror ushlanadi** (har trial'dan oldin SUT fayllariga fiksa teginish).
**Cold start P1 qamrovidan tashqarida.** `drop_caches` root talab qiladi va butun ish
stansiyasini buzadi — **qilinmaydi**.

Kovariata sifatida log'lanadi: `memory.stat` (`pgmajfault`, `pgscan_*`, `pgsteal_*`,
`workingset_*`), host `MemAvailable`, trial boshidagi page cache hajmi, **trial indeksi**
(monoton drift testi uchun).

### 8.4 Randomizatsiya va washout

**Randomized complete block design.** Blok = har `(arm × pressure)` yacheykadan **aynan
bitta** trial, blok ichida **seeded RNG** bilan aralashtirilgan (seed `run_meta` da).
`n` blok ⇒ yacheykaga `n` replika, va blok sekin drift'ni (kun vaqti, cache holati, termal)
o'ziga singdiradi.

**Washout ketma-ketligi (muzlatilgan):**
1. `revixlab.slice/cgroup.kill` ga `1` yozish — atomik subtree kill;
2. slice `memory.current` baseline ±ε ga qaytishini kutish, **ε = 32 MiB**;
3. slice **va** host stall tezliklari quiescence chegarasidan past bo'lishi, `T_q = 5 s` davomida.
   **Quiescence chegarasi = 0.05** (2 s oynadagi stall ulushi). Kuzatuv
   o'qilmasa (None) u **jim deb hisoblanMAYDI** — guard'ning fail-closed
   qoidasi bilan bir xil;
4. qattiq pol **`T_w = 15 s`**, cap **`T_w_max = 120 s`** → `washout_timeout`, trial chiqariladi.

> **`T_w = 15 s` va §9.4 dagi "washout ≥20 s" ziddiyat emas:** 15 s — holat
> mashinasi majburlaydigan **minimum**; 20 s — rejalashtirilgan qiymat, va u
> minimumni qanoatlantiradi. Reja minimumdan past bo'lsa — xato.

> Agar analiz `avg300` ishlatganda washout ≈300 s bo'lishi kerak edi.
> `total`-asosli interval o'lchovlari washout'ni **15 s** qiladi — umumiy kampaniya
> vaqtidan bir daraja. Bu o'lchov qaroridan kelib chiqqan dizayn foydasi.

### 8.5 DVFS / termal
CPU: `amd-pstate-epp`, governor `powersave`. Sustained yuk chastotani pasaytiradi, demak
yuk ostidagi response-time o'lchovlari kontentsiya bilan DVFS ni aralashtiradi.

- Yumshatish: blok ichida randomizatsiya.
- Har trial chegarasida `scaling_cur_freq` (har CPU) va `thermal_zone*/temp` log'lanadi;
  o'rtacha chastota kovariata.
- **Agar chastota arm bo'yicha tizimli farq qilsa, timing taqqoslashlari haqiqiy emas** —
  bu tekshiriladi va hisobotda beriladi.

---

## 9. P1 dizayni

### 9.1 Yagona savol

> **Ekzogen** injeksiya qilingan memory pressure, systemd'ning o'z `Restart=on-failure` i
> bilan restart qilinadigan **oson tuzatiladigan** fault (clean crash) uchun `P(VR)` ni
> kamaytiradimi va time-to-VR ni oshiradimi?

Bu yacheyka **REVIX engine'ini umuman talab qilmaydi** — arm'lar shunchaki systemd
config'lari. **H1 dunyo haqidagi da'vo, REVIX haqida emas.**

### 9.2 Mexanizm — oldindan aytilgan
Tinch holatda `P(VR | clean_crash, restart) ≈ 1.0`. Pressure ostida pasayishi mumkin
bo'lgan sanab o'tiladigan yo'llar:

| # | mexanizm | log'da izi |
|---|---|---|
| i | `TimeoutStartSec` oshib ketdi | `Result=timeout` |
| ii | start paytida OOM-kill | `memory.events.oom_kill` +1, `Result=oom-kill` |
| iii | start bo'ldi lekin throughput < `θ·R_ref` — **brownout** | `throughput_below_theta` invalidator |
| iv | scheduling delay'dan watchdog miss | `Result=watchdog` |

> **(iii) eng ehtimoliy signal manbasi, va u FAQAT VR ta'rifida throughput bandi (§4.5)
> borligi uchun mavjud.** Xulosa, oldindan yozilgan: **liveness-only VR ta'rifi ehtimol
> null pilot beradi, va bu null — ta'rif artefakti, H1 ga qarshi dalil EMAS.**

### 9.3 Faktorlar va arm'lar

| | |
|---|---|
| **Arm'lar** | `A` (`Restart=on-failure`, `RestartSec=100ms`) va `no_action` (`Restart=no`) |
| **Fault** | faqat `clean_crash`, trial'ga bitta injeksiya |
| **Pressure** | `P0` (generator idle), `P1` (~20–35% slice stall), `P2` (~60–80%) |
| **Bloklar** | 20 |
| **Trial'lar** | 3 × 2 × 20 = **120** |

**Baseline B (`RestartSteps=`) P1 da YO'Q.** Sabab: B ning `RestartSec=10s` xavfsiz
pressure oynasidan (12 s) oshadi — B ning restart'i hold oxirida tushar va stabilizatsiya
oynasi pressure'dan **tashqarida** qolar edi. A va B restart paytida taqqoslanadigan
pressure'ga tushmaydi. **A-vs-B — bu H2 va confirmatory eksperimentga tegishli.**

### 9.4 Pressure dosing
Generator **closed-loop PI controller** bilan slice'ning `total`-asosli 2 s stall tezligini
nishon bandida ushlaydi.

**Analiz ERISHILGAN (uzluksiz) pressure'dan foydalanadi, mo'ljallangan darajadan emas.**
Natija: ta'sir qilmagan treatment trial'ni buzmaydi — u kovariataga aylanadi; va kategorik
dizayn bir xil `n` da kuchliroq regressiyaga aylanadi.

**Trial jadvali:** pre-flight → `R_ref` baseline 10 s → ramp 5 s → hold, injeksiya
hold'ga 3 s kirgach → pressure off → washout ≥20 s.

**Ikki xavfsizlik invarianti (v1.3):**

| # | invariant | qiymat | nega |
|---|---|---|---|
| 1 | `hold_s ≤ hold_cap_s` | **13 s** (**v1.11**: 12 s → 13 s) | **Asl asos (v1.3):** *“oomd 20 s sustained talab qiladi; bu asosiy vaqt zaxirasi”* — bu muhitda kuchini yo'qotgan: `systemd-oomd` **yo'q** (§15.2). **v1.11 asosi (§17.5 O3):** o'lchangan `t_start` 12 s li cheklovni `P1` da buzadi; 13 s da budjet `t_start ≤ 1.8 s` va 78/78 urinish ichida. Shartnomaviy arifmetika saqlanadi: `3 + 8 = 11 ≤ 13` |
| 2 | `hold_s + ramp_above_threshold_s ≤ guard_sustain_s` | **15 s** | ramp ham pressure beradi; bu guard'ning `sustain_max_seconds` i, demak to'g'ri trial guard'ni ISHGA TUSHIRMASLIGI matematik kafolatlanadi |

> **`hold_cap_s` cheklovi faqat HOLD ga tegishli, ramp+hold ga emas.** Aks
> holda `hold ≤ 13 − 5 = 8 s` bo'lardi, lekin injeksiya(3 s) +
> `W_stab_pilot`(8 s) = 11 s talab qilinadi — ya'ni ziddiyat (v1.3 ning
> arifmetikasi 12 s da `hold ≤ 7 s` bergan edi; **v1.11** dan keyin 8 s,
> va 8 < 11 bo'lgani uchun yechim o'zgarmaydi). Ikkinchi invariant uzun ramp orqali
> qo'shimcha pressure "olib o'tilishini" to'xtatadi.

`ramp_above_threshold_s` (ramp'ning quiescence chegarasidan yuqori qismi)
**pressure dosing kalibratsiyasidan olinadi**, taxmin qilinmaydi.

> **✅ v1.11 — bu talab BAJARILDI:** o'lchangan qiymat **`0.000 s`**,
> kalibrlangan `base_mb = 184` da **29 epizoddan 29 tasida**
> (`docs/architecture/10-pressure-dozalash.md` §4.1). Demak invariant 2:
> `13 + 0.000 = 13.000 ≤ 15`, **zaxira 2.000 s**. Eski kod qiymati
> `3.0 s` **TAXMIN** edi (`revix/schedule.py` izohining o'z so'zi) va u
> invariant 2 ni **aynan chegarada** (`12 + 3 = 15`) o'tkazardi —
> Amendment log, v1.10 → v1.11, **3-band**, va o'sha banddagi ikki
> CHEKLOV (validator **rejalashtirilgan**, o'lchangan emas, qiymatni
> tekshiradi).

**Kampaniya vaqti:** fazalar yig'indisi = pre-flight + 10 + 5 + 13 + 20 ≈ 53 s
(**v1.11**: `hold_cap_s` 12 → 13 s, demak 52 → 53 s — bu **chiqarilgan baho**,
muzlatilgan parametr emas).
Haqiqiy trial vaqti bundan katta (unit yaratish/yo'q qilish, D-Bus
round-trip, ma'lumot flush). Bu qo'shimcha **o'lchanadi, taxmin qilinmaydi**,
va kampaniya bahosiga o'lchangan qiymat kiritiladi. Boshlang'ich baho
≈75 s/trial ⇒ ≈2.5 soat, 120 trial uchun.

---

## 10. Statistik tahlil (muzlatilgan)

### 10.1 H1 birlamchi endpoint — `P(VR)` pressure stratalari orasida, fault class ichida

- **Birlamchi test: Cochran–Armitage trend testi** `P0 < P1 < P2` bo'ylab.
  Sabab: tartibni ishlatadi (pairwise'dan ancha kuchli), va *"`P(VR)` pressure bilan
  monoton kamayadi"* — *"yuqori < past"* dan kuchliroq, ko'proq falsifiable da'vo.
- 2×2 uchun **Fisher exact** (yoki ko'proq power uchun Barnard).
- **Effect size: risk difference + Newcombe/Wilson-score CI** (birlamchi, downtime
  argumenti uchun eng talqin qilinadigan). Risk ratio va OR ikkilamchi.
  Har yacheyka proporsiyasi uchun **Clopper–Pearson exact CI**.
- Uzluksiz versiya: `logit P(VR) ~ P_pre[2s] + block` — **qo'llab-quvvatlovchi, birlamchi
  emas**. Kichik `n` da ortiqcha modellashtirish qilinmaydi.

### 10.2 Downtime / recovery-time taqsimotlari

Bu taqsimotlar og'ir dumli, ehtimol bimodal ("birinchi urinishda" vs "k loop'dan keyin"),
va o'ngdan censored.

- **`t-test` ISHLATILMAYDI. `mean ± SD` BERILMAYDI.**
- **Birlamchi: Kaplan–Meier time-to-VR har arm uchun, log-rank bilan taqqoslash** —
  censoring'ni to'g'ri ishlaydigan yagona oila.
- **Cox / hazard ratio ISHLATILMAYDI** — hazard'lar proporsional bo'lmasligi deyarli aniq
  (fiksa kechikishlar step hazard yaratadi). Schoenfeld residual'lari tekshirilmasa,
  HR berilmaydi.
- **Effect measure: RMST difference** τ horizon'ga qadar — non-proportional hazard ostida
  haqiqiy, va to'g'ridan-to'g'ri *"τ sekund ichida tejalgan kutilgan downtime"* sifatida
  o'qiladi. **Bu mavjud eng yaxshi statistik tanlov va H2 ga to'g'ridan-to'g'ri javob beradi.**
- Ikkilamchi (censored bo'lmagan qism ustida): Mann–Whitney U, Kruskal–Wallis + Dunn;
  effect size **Cliff's δ** / A₁₂ bootstrap CI bilan.
- **median, p90, p99 + BCa bootstrap CI** — dum xatti-harakati muhim; p99 downtime
  operatorlar uchun ahamiyatli.
- Blokdan foyda: per-blok farqlarda **Wilcoxon signed-rank**, yoki blok-stratifikatsiyalangan
  log-rank.
- Restart/loop soni: **negative binomial** (Poisson overdispersion sababli xato bo'ladi),
  yoki tezlik farqining nonparametrik bootstrap'i.
- ECDF'lar to'liq chizilib beriladi — har qanday bitta testdan ishonchliroq.

### 10.3 Implementatsiya
`statsmodels` va `lifelines` mavjud emas. `scipy` Fisher, Mann–Whitney, Kruskal–Wallis va
bootstrap'ni qoplaydi. Cochran–Armitage ~10 qator; KM + log-rank + RMST ~100 qator numpy.

**Dependency qo'shmasdan o'zimiz yozamiz**, va **nashr etilgan ishlangan misolga qarshi
unit-test** qilamiz. Self-contained artifact reviewer uchun tejalgan mehnatdan qimmatroq.

### 10.4 Multiplicity
Pre-registered per-class birlamchi testlar bo'ylab **Holm–Bonferroni**. P1 da bitta fault
class bor (`clean_crash`), demak bitta birlamchi test; scope/Δ sweep'lari **exploratory**
deb belgilanadi.

---

## 11. Falsifikatsiya va davom etish mezonlari

**Ishga tushirishdan OLDIN muzlatilgan.**

### H1 ning kuchli shakli bu yacheykada YOLG'ON, agar:
- Cochran–Armitage trend testi `P0 < P1 < P2` bo'ylab **ahamiyatsiz** (p > 0.05); **VA**
- `P(VR|P0) − P(VR|P2)` uchun 95% Newcombe CI ning **yuqori chegarasi < 0.15**
  (ya'ni 15 punktdan katta effekt inkor qilinadi).

Bir vaqtda, fail-slow shakli qo'llab-quvvatlanmaydi, agar `P0` va `P2` orasidagi
time-to-VR RMST farqi (τ = 8 s) uchun 95% CI 20% oshishni chiqarib tashlasa.

> **✅ v1.11 — bu limbning aytilmagan referensi HAL QILINDI (§18.6 → F2).**
> Chegara `τ` ga ankorlanadi va **fiksa**:
>
> ```
> Delta(P2,P0) := RMST_A(P2, tau=8 s) - RMST_A(P0, tau=8 s)
> thr          := 0.20 x tau = 0.20 x 8 s = 1.6 s      (fiksa, 16 x P)
>
> fail-slow shakli QO'LLAB-QUVVATLANMAYDI  <=>  CI95_upper[ Delta(P2,P0) ] < 1.6 s
> ```
>
> `_A` — §16.5 bo'yicha **arm `A` ichida**; ayirish tartibi va yo'nalish
> §18.2 dan **o'zgarmagan holda** saqlanadi. **§18.2 ning
> `thr = 0.20 × RMST(P0)` o'qishi (F1) BEKOR QILINADI.** Sabab (F1 ning
> inkor shoxi asbobning kvantlash polidan past), **bias yo'nalishi
> (F2 ANTI-KONSERVATIV)**, narxi, va **qaror kalibratsiya ma'lumoti
> ko'rilgandan keyin qabul qilingani**: **Amendment log, v1.10 → v1.11**
> (0-band va 2-band), §18.6, §18.7. §11 ning qolgan hamma bandi —
> kuchli shakl, power bayonoti, davom etish mezonlari, burilish —
> **o'zgarmadi**.

### Halol power bayonoti (oldindan majburiyat)
`n = 20`/daraja Fisher exact bilan `1.00 → ~0.65` ni ≈80% power bilan aniqlaydi.
**`1.00 → 0.90` ni aniqlamaydi.**

> **Null pilot faqat KATTA effektni inkor qiladi va H1 ning kuchsiz shaklini
> yolg'onga chiqarmaydi.** Bu o'qish oldindan qabul qilinadi — natijadan keyin
> qayta talqin qilinmaydi.

### Davom etish mezoni (biri yetarli)
- **(a)** trend p < 0.05 **va** risk difference ≥ 0.15;
- **(b)** `D_eff` `P2` da ≥1.5× `P0`, bootstrap CI 1.0 ni chiqarib tashlaydi;
- **(c)** mexanizm log'larida faqat `P2` da paydo bo'ladigan takrorlanuvchi yo'l
  (masalan `Result=timeout`), agregat tezliklar deyarli siljimasa ham.

> **(c) sifatiy va ehtimol eng qimmatli pilot natijasi, chunki u mexanizmni NOMLAYDI.**
> Nomlangan mexanizm H1 ni korrelyatsiyadan nazariyaga aylantiradi.

### Null bo'lsa — oldindan belgilangan burilish
Binar endpoint null bo'lsa: **restart pressure ostida sekinroq va degradatsiyalangan
bo'ladimi** — `D_eff` orqali. Kuchsizroq, lekin hali nashr qilinadigan da'vo, va
**xuddi shu ma'lumotdan** tekshiriladi. Binar null — o'lik yo'l emas.

---

## 12. Trial disposition — yopiq enum

Har trial'ga **aynan bitta** disposition. Bu jimgina eksklyuziyaning oldini oladi.

| disposition | ma'nosi |
|---|---|
| `complete` | to'liq o'lchandi, birlamchi analizga kiradi |
| `censored` | probe uzilishi >2×P, yoki horizon down holatda tugadi |
| `contaminated` | biz yubormagan `SIGKILL`, biz cheklamagan cgroup'da `oom_kill`, yoki bystander buzildi |
| `aborted_guard` | host guard ishga tushdi |
| `washout_timeout` | washout `T_w_max` ichida yakunlanmadi |
| `harness_error` | harness istisnosi |

**`contaminated` va `aborted_guard` trial'lar birlamchi analizdan chiqariladi, LEKIN
ularning ulushi natija sifatida beriladi.** Yuqori eksklyuziya darajasi o'zi natija —
yashirilmaydi.

---

## 13. Bu pre-registration NIMANI muzlatmaydi

Quyidagilar **keyinchalik** aniqlanadi va **o'z pre-registration'ini** talab qiladi:
- Confirmatory eksperiment `n` (P1 effect size'ini baholagandan keyin hisoblanadi)
- `Repairs()` matritsasi (kalibratsiya eksperimentidan)
- Arm C (REVIX) siyosati va gate chegaralari
- `pressure_pulse_duration` faktor darajalari (H2 uchun kritik)
- Fault taxonomiyasining qolgan 8 klassi

**P1 ma'lumotlari confirmatory analizga QO'SHILMAYDI.** P1 — effect size baholash va
mexanizm aniqlash uchun; u hipotezani sinash uchun ishlatilsa, keyin yana bir xil
hipotezani sinash — garden of forking paths.

---

## 14. Data schema (muzlatilgan)

> Bu bo'lim **v1.2 amendment** bilan qo'shildi. Oldingi versiyalarda data schema
> faqat rejalashtirish hujjatida bor edi va bu ikki implementatorni record
> kontraktini mustaqil ixtiro qilishga majbur qildi.

### 14.1 Fayl formatlari

| oqim | format | sabab |
|---|---|---|
| hodisalar (kam tezlikli, heterogen) | **JSON Lines** | turli record turlari bitta CSV'ga sig'maydi; append-only + line-delimited crash-safe |
| `probe_sample`, `psi_sample` (10 Hz) | **CSV** | ~1–2M qator; JSONL ~5–10× bayt, ~3–5× parse. Serializatsiyaga ketgan CPU — eksperimentdan o'g'irlangan CPU |

JSONL: bitta `write()` oldindan serializatsiya qilingan bytes, `O_APPEND`.
**`fsync` davriy, hech qachon har qatorda** — har qatorda fsync o'lchanayotgan
tizimga IO kiritadi.

### 14.2 Envelope — har JSONL record'da

```
schema_version  record_type  stream  run_id  session_id  boot_id
trial_id  block_index  seq  mono_us  real_us  emitter
```

- **`stream`** — `seq` shu oqim bo'yicha monotonik. Validator bo'shliqni
  topish uchun qaysi oqim ekanini bilishi SHART. Busiz u `record_type` ni
  proksi sifatida ishlatadi va bitta oqimga ikki record turi yozilsa **soxta
  bo'shliq** ko'rsatadi.
- **`boot_id`** — monotonic qiymatlar faqat bitta boot ichida taqqoslanadi.
- CSV oqimlarida envelope yo'q (hajm sababli); ular `<stream>_start` record'i
  orqali run'ga bog'lanadi va validator ularni `schema_version` tekshiruvidan
  ochiq ravishda ozod qiladi.

### 14.3 Record turlari

**Harness (driver):** `run_meta`, `trial_begin`, `trial_end`, `env_snapshot`,
`fault_inject`, `fault_effective`, `baseline_window`, `action`, `action_defer`,
`actor_signal`, `unit_state`, `cgroup_events`, `harness_error`

**Prober:** `prober_start`, `prober_stop`, `probe_sample` (CSV), `probe_overrun`,
`detection`, `contract_restored`

**PSI sampler:** `sampler_start`, `sampler_stop`, `psi_sample` (CSV),
`psi_scope_unavailable`

**Guard:** `guard_start`, `guard_event`, `guard_stop`

**Pressure generatori:** `pressure_start`, `pressure_ramp`, `pressure_sample`,
`pressure_stop`

**Derived (reducer chiqaradi, alohida faylga):** `trial_metrics`, `episode`

### 14.4 Majburiy maydonlar (ta'riflar shularga tayanadi)

| record | maydon | nega majburiy |
|---|---|---|
| `run_meta` | `preregistration_sha256`, `git_commit`, `git_dirty`, `rng_seed`, `boot_id`, har unit'ning **tirik** `systemctl show` dump'i | reproducibility; §7 tirik unit shartini ko'ring |
| `trial_end` | **`disposition`** (§12 yopiq enum, aynan bitta) | jimgina eksklyuziyani oldini oladi |
| `probe_sample` | `mono_us_send`, `outcome`, `progress_counter`, **`invocation_id_seen`** | invocation echo yangi invocation race'ini yopadi |
| `unit_state` | systemd'ning **o'z** monotonic timestamp'lari **va** harness'ning qabul `mono_us`i **alohida** | D-Bus delivery latency ko'rinadi, o'lchov ichida yashirinmaydi |
| `action` | `policy_delay_us` **`L_dec` dan alohida** | §6.3 soxta taqqoslashning oldini oladi |
| `actor_signal` | `success` (aktorning O'Z da'vosi) | **FR-A ning birlamchi operandi** (§5). Aniq record afzal; `unit_state` dan chiqarish mumkin, lekin manba (`actor_signal_source`) yozilishi SHART |

### 14.5 Ikki yuk ko'taruvchi talab

1. **Stabilizatsiya oynasining raw per-probe trace'lari saqlanadi.** Metrika
   alternativ `W_stab`/`θ`/`p_min` ostida **qayta hisoblanishi** shart,
   eksperimentni qayta ishga tushirmasdan. Bu §4 dagi sensitivity sweep'ning
   yagona asosi va *"siz W ni natija uchun tanlagansiz"* hujumiga javob.
2. **Derived record'lar alohida fayllarda va raw'dan qayta yaratiladi.
   Raw fayllar derived maydon qo'shish uchun HECH QACHON tahrirlanmaydi.**

### 14.6 Validator invariantlari (analizdan oldin o'tishi SHART)

1. har `trial_begin` uchun mos `trial_end`
2. trial'ga **aynan bitta** `disposition`, §12 enum'idan
3. `(stream)` bo'yicha `seq` bo'shlig'i yo'q
4. trial ichida probe uzilishi > 2×P yo'q (aks holda trial `censored`)
5. `boot_id` sessiya ichida o'zgarmas
6. har `action` uchun mos invocation o'zgarishi yoki ochiq `action_defer`
7. har record'ning `schema_version` i tanilgan
8. confirmatory run uchun `run_meta.git_dirty == false` (pilot uchun ogohlantirish)

**Validatsiyadan o'tmagan run analiz qilinmaydi.**

### 14.7 Ochiq bo'shliqlar (implementatorlar aniqlagan, kelajakdagi amendment uchun)

- **`harm_indicator`** (FR-B uchun, §5) hech bir record turida yo'q. P1 da
  FR-B hisoblanmaydi, demak bu P1 ni bloklamaydi, lekin kalibratsiya
  eksperimentidan oldin ta'riflanishi kerak.
- **`guard_event` da `trial_id` yo'q** — bu TO'G'RI, guard mustaqil jarayon
  (§8.2). Atributsiya monotonic vaqt bo'yicha, demak faqat bitta boot ichida
  haqiqiy — `boot_id` invariantining ahamiyati aynan shu.

---

## 15. Muhit fingerprint va undan kelib chiqadigan cheklovlar (muzlatilgan)

> Bu bo'lim **v1.4 amendment** bilan qo'shildi. U **hech bir ta'rifni, metrikani,
> chegarani, statistik testni yoki falsifikatsiya mezonini o'zgartirmaydi.** U faqat
> ikki narsani qiladi: (1) pre-registration endi qaysi muhitga tegishli ekanini qayd
> etadi, (2) o'sha muhitdan kelib chiqadigan cheklovlarni ochiq yozadi.
>
> **Nega yangi bo'lim, mavjudlarini tahrirlash emas:** mavjud bo'limlarni qayta
> raqamlash `revix/schema.py`, `revix/reduce.py`, `revix/prober.py` va hujjatlardagi
> havolalarni buzardi — v1.2 ham aynan shu sababdan §14 ni **oxiriga** qo'shgan.

### 15.1 FAKT — o'lchangan muhit (2026-10-02)

Quyidagi har bir qiymat **shu sanada, shu mashinada, ko'rsatilgan buyruq bilan
o'lchangan.** Hech biri taxmin yoki ko'chirma emas.

| o'lchov | buyruq | qiymat |
|---|---|---|
| kernel | `uname -srm` | `Linux 6.6.87.2-microsoft-standard-WSL2 x86_64` |
| distro | `/etc/os-release` | `NAME="Kali GNU/Linux"`, `VERSION_ID="2025.3"`, `PRETTY_NAME="Kali GNU/Linux Rolling"` |
| systemd | `systemctl --version \| head -1` | `systemd 257 (257.7-1)` |
| CPU soni | `nproc` | `12` |
| CPU modeli | `/proc/cpuinfo` `model name` | `AMD Ryzen 5 5600H with Radeon Graphics` |
| RAM | `/proc/meminfo` `MemTotal` | `10183888 kB` = **9.71 GiB** |
| swap | `/proc/meminfo` `SwapTotal` | `4194304 kB` = **4.00 GiB** (`/proc/swaps`: `/dev/sdc`, partition) |
| cgroup | `stat -fc %T /sys/fs/cgroup` | `cgroup2fs` |
| root controller'lar | `/sys/fs/cgroup/cgroup.controllers` | `cpuset cpu io memory hugetlb pids rdma` |
| delegatsiya | `.../user-1000.slice/user@1000.service/cgroup.controllers` | **`cpu memory pids`** |
| `user@1000.service` | `systemctl is-active user@1000.service` | `active` |
| host PSI | `/proc/pressure/{memory,io,cpu}` | uchalasi ham o'qiladi |
| per-cgroup PSI | `.../user@1000.service/{memory,io}.pressure` | ikkalasi ham o'qiladi |
| `systemd-oomd` unit | `systemctl show systemd-oomd -p LoadState -p ActiveState` | **`LoadState=not-found`**, `ActiveState=inactive` |
| `systemd-oomd` binar | `/usr/lib/`, `/lib/`, `/usr/libexec/systemd/systemd-oomd` | **uchalasi ham YO'Q** |
| `oomctl` | `command -v oomctl` | yo'q (exit 1) |
| oomd drop-in | `ls /usr/lib/systemd/system/user@.service.d/` | faqat `10-login-barrier.conf`; **`10-oomd-user-service-defaults.conf` YO'Q** |
| `oomd.conf` | `systemd-analyze cat-config systemd/oomd.conf` | `# Main configuration file systemd/oomd.conf not found` |
| ManagedOOM | `systemctl show user@1000.service -p ManagedOOM*` | `ManagedOOMMemoryPressure=auto`, `ManagedOOMMemoryPressureLimit=0`, `ManagedOOMSwap=auto` |
| `cpufreq` sysfs | `ls /sys/devices/system/cpu/cpu0/cpufreq` | **`No such file or directory`** |
| `scaling_cur_freq` | `find /sys/devices/system/cpu -maxdepth 3 -name scaling_cur_freq` | **count = 0** |
| `thermal_zone*` | `ls /sys/class/thermal/` | faqat `cooling_device0`…`cooling_device11`; `thermal_zone*/temp` **count = 0** |
| `/dev/kvm` | `ls -l /dev/kvm` | `crw-rw---- 1 root kvm 10, 232` (mavjud) |
| global OOM | `grep ^oom_kill /proc/vmstat` | `oom_kill 0` |
| `systemd-run` | `command -v systemd-run` | `/usr/bin/systemd-run` |

**O'lchanMAGANlar (ochiq yoziladi):** guard chegaralarining shu mashinadagi
qiymatlari, pressure dosing bandlari, va transient unit'da `RestartSteps=`
qabul qilinishi — **bu o'lchovlar bu yerda bajarilmadi.** Sabab: pressure
eksperimenti `00-pilot-topologiya.md` §6 ning 3-qadami o'tmaguncha taqiqlangan,
va amendment uchun pressure ishga tushirilmadi.

#### Kalibratsiya hujjati boshqa mashinani e'lon qiladi

`docs/architecture/02-guard-kalibratsiyasi.md` sarlavhasi o'z o'lchov muhitini
shunday yozadi: *"Kali 2026.3, kernel 7.1.5, systemd 261, 15Gi RAM, 12 CPU"*,
`systemd-oomd` qurollangan (`ManagedOOMMemoryPressure=kill`, limit `50%`,
`DefaultMemoryPressureDurationSec=20s` — `01-muhit-tekshiruvlari.md` §7).
**Yuqoridagi fingerprint u emas.** Mos keladigan yagona qiymat — CPU soni (12).

#### Qamrov cheklovi (ochiq majburiyat)

Bu muhitda olingan har qanday natija **shu fingerprint uchun haqiqiy** va undan
tashqariga avtomatik ko'chirilMAYDI. Bog'lanish mexanizmi allaqachon mavjud:
`run_meta` da `uname` va `systemd_version` majburiy maydonlar
(`04-driver-va-analiz-shartnomasi.md` §1.1), `preregistration_sha256` bilan
birga — demak har bir run **qaysi ta'riflar ostida** va **qaysi muhitda**
o'lchangani ikki tomondan aniqlanadi. `oomd_effective` maydoni shu muhitda
oomd yo'qligini qayd etadi.

Boshqa mashinada guard chegaralari **qayta o'lchanishi shart.** Bu talab
yangi emas: `02-guard-kalibratsiyasi.md` §7 (1-masala) `user@ ≈ lab` topilmasi
**bo'sh desktop** sharti uchun ekanini va band tizimda qayta o'lchanishi
kerakligini allaqachon aytadi. Boshqa kernel va boshqa xotira budjeti — bundan
kuchliroq o'zgarish, demak xuddi shu talab ostida.

### 15.2 FAKT — `systemd-oomd` bu mashinada mavjud emas

Unit `not-found`, binar uchala standart yo'lda ham yo'q, `oomctl` yo'q,
`oomd.conf` yo'q, va `user@.service.d/` da oomd drop-in'i yo'q (15.1).
`ManagedOOMMemoryPressure=auto` — bu **default** qiymat va oomd'siz
hech qanday ta'sir qilmaydi.

Demak `00-pilot-topologiya.md` §3.1 da *"1-RAQAMLI XAVF"* deb nomlangan
xavf — oomd 20 s sustained pressure'dan keyin avlod cgroup'ni o'ldirishi —
**bu muhitda yo'q.**

### 15.3 TALQIN — sabab o'zgardi, cheklov o'zgarMADI

Bu v1.4 ning eng muhim ajratishi.

§9.4 ning 1-invarianti `hold_s ≤ hold_cap_s = 12 s` **aynan muzlatilgan holida
qoladi.** `W_stab_pilot = 8 s` (§4) ham. Ikki sabab, ikkisi ham mustaqil
yetarli:

1. **Ular muzlatilgan qiymatlar.** Pre-registration qulaylik uchun
   bo'shashtirilmaydi. "Endi xavf yo'q, demak oynani uzaytiraylik" — aynan
   natijani ko'rishdan oldin ta'rifni tanlash, ya'ni bu hujjatning oldini
   olish uchun yozilgan narsa.
2. **12 s — endi shartnomaviy arifmetika.** `injection_offset (3 s) +
   W_stab_pilot (8 s) = 11 s ≤ 12 s` — aynan shu hisob v1.3 amendment'ining
   yaratilish sababi edi (§4 va §9.4 orasidagi ziddiyat). 12 s ni o'zgartirish
   v1.3 ni bekor qilish bo'ladi.

**Shuning uchun:** `hold_cap_s = 12 s` ning **asoslanishi endi qisman
muhitga, qisman shartnomaga tayanadi.** v1.3 gacha u sof muhit cheklovi edi
(oomd'ning 20 s sharti ostida vaqt zaxirasi); v1.4 dan keyin oomd zaxirasi
**bu muhitda ma'nosiz**, lekin shartnomaviy arifmetika **o'z kuchida qoladi va
yagona hukmron asos bo'lib qoladi.** §9.4 jadvalidagi *"oomd 20 s sustained
talab qiladi"* izohi — **o'sha muhitdagi** asos, va u matn **o'zgartirilmaydi**;
bu bo'lim uni to'ldiradi.

> **⚠️ v1.11 — bu banddagi `hold_cap_s = 12 s` BEKOR QILINDI.** §17.5 ning
> qarori **O3** bo'yicha `hold_cap_s` = **13 s** (§9.4 invariant 1).
> 15.3 ning ikki sababi **rad etilmaydi**, javob oladi: **1-sabab**
> (muzlatilgan qiymat qulaylik uchun bo'shashtirilmaydi) **qo'llanmaydi**,
> chunki §17.5 to'rt muzlatilgan qiymatning **birgalikda
> qanoatlantirilmasligini** e'lon qilgan va qarorni **birinchi trial'dan
> oldin majburiy** qilgan — demak bu qulaylik emas, **e'lon qilingan
> dizayn nuqsoni**, va u `10-pressure-dozalash.md` §6.5 da **o'lchandi**;
> **2-sabab** (shartnomaviy arifmetika) **o'z kuchida va buzilmadi** —
> `injection_offset(3) + W_stab_pilot(8) = 11 ≤ 13`, zaxira 1 s dan
> **2 s** ga oshdi, demak **v1.3 bekor qilinmaydi**. Pastdagi *"guard
> majburiy va fail-closed"* bandi **kuchayadi**, chunki oomd yo'q va hold
> uzaygan holda xavfsizlik argumenti **faqat guard'ga** tayanadi —
> Amendment log, v1.10 → v1.11, (1.7).

#### Guard majburiy va fail-closed bo'lib qoladi

`00-pilot-topologiya.md` §3.1 ning (b) yumshatishi — mustaqil guard process,
`✅ majburiy`, driver'dan **alohida** process, birinchi start / oxirgi stop —
**o'z kuchida.** oomd yo'qolgani guard'ni opsional qilmaydi, chunki qolgan
xavflar o'z joyida:

- **kernel global OOM killer** (`00-pilot-topologiya.md` §3.2) — oomd'ga
  bog'liq emas; bu mashinada xotira budjeti kalibratsiya mashinasidan
  **kichikroq** (9.71 GiB vs e'lon qilingan 15 GiB), demak bu xavf
  **kamaymadi**, balki zaxira torayadi. O'lchangan: `/proc/vmstat oom_kill = 0`
  — ya'ni hozircha ishlamagan, bu **himoya emas**;
- **runaway generator** — `02-guard-kalibratsiyasi.md` §1 ning oniy chegaralari
  (`user_full_avg10_max=85`, `user_some_avg10_max=90`,
  `user_full_rate2s_max=0.98`) aynan buni tutish uchun;
- **fail-closed qoidasi** — §8.4(3): kuzatuv o'qilmasa (`None`) u **jim deb
  hisoblanMAYDI.** Bu qoida muhitga bog'liq emas.

Guard chegaralari **bu mashinada qayta kalibratsiya qilinishi shart**
(`02-guard-kalibratsiyasi.md` §7, 1-masala), va `00-pilot-topologiya.md` §6
ning 3-qadami keyingi **har bir** qadamni gate qiladi. v1.4 bu gate'ni
ochmaydi va bu amendment uchun hech qanday pressure ishga tushirilmadi.

### 15.4 CHEKLOV — §8.5 bu muhitda BAJARILISHI MUMKIN EMAS

§8.5 uchta narsani talab qiladi:

1. har trial chegarasida `scaling_cur_freq` (har CPU uchun) log'lansin;
2. har trial chegarasida `thermal_zone*/temp` log'lansin; o'rtacha chastota
   kovariata bo'lsin;
3. **"agar chastota arm bo'yicha tizimli farq qilsa, timing taqqoslashlari
   haqiqiy emas — bu tekshiriladi va hisobotda beriladi."**

O'lchangan (15.1): `/sys/devices/system/cpu/cpu0/cpufreq` **mavjud emas**,
butun `/sys/devices/system/cpu` ostida `scaling_cur_freq` **nol dona**, va
`/sys/class/thermal/` da `thermal_zone*` **nol dona** (faqat
`cooling_device0..11`). WSL2 kernel'i bu ikki sysfs interfeysini **umuman
eksport qilmaydi.**

**Natija: (1) va (2) bajarilmaydi, demak (3) dagi TEKSHIRUV BAJARILMAYDI.**

Operatsion oqibatlari, aniq:

- `run_meta.governor` va `run_meta.scaling_driver`
  (`04-driver-va-analiz-shartnomasi.md` §1.1) **`None`** bo'ladi, ma'nosi
  **"o'lchanmadi"**. **Hech qachon `0` emas** — `0` "o'lchandi va nolga teng"
  degan ma'noni berardi, bu esa yolg'on bo'lardi. Bu §8.4(3) ning
  None-mantiqi bilan bir xil: o'lchanmagan narsa qulay qiymat bilan
  to'ldirilmaydi.
- per-trial `scaling_cur_freq` va `thermal_zone*/temp` yozuvlari ham `None`.
  §8.5 ko'zda tutgan **"o'rtacha chastota kovariata"** bu muhitda
  **mavjud emas** — regressiyaga qo'shiladigan hech narsa yo'q.
- **Yumshatish — faqat §8.5 ning o'zi nomlagani:** blok ichida randomizatsiya
  (§8.4 randomized complete block design). U chastota farqini arm'lar bo'ylab
  **balanslaydi**, lekin uni **o'lchamaydi**. Balanslash — tizimli siljishning
  oldini oladigan dizayn himoyasi; o'lchash — uning bo'lmaganini **ko'rsatib
  beradigan** dalil. Bu yerda ikkinchisi yo'q.
- **Qo'shimcha og'irlashtiruvchi fakt:** mehmon (WSL2) host (Windows)
  chastota boshqaruvini **ko'rmaydi.** Demak DVFS **mavjud bo'lishi mumkin va
  butunlay o'lchanmaydi** — "yo'q" emas, "ko'rinmas". Bu eng yomon
  kombinatsiya, va shunday yoziladi.

**Bu `D_probe`, `D_eff`, `D_sd`, `time_to_first_up`, time-to-VR va RMST
(§6, §10.2) validligiga HAQIQIY tahdid.** U maqolaning Limitations bo'limiga
**aynan shu shaklda** kiradi va **yumshatilmaydi:**

> *Biz DVFS ni nazorat qildik demaymiz. Biz uni **o'lchay olmadik**, va faqat
> blok ichidagi randomizatsiyaga tayandik. §8.5 ning "tizimli farq bo'lsa
> timing taqqoslashlari haqiqiy emas" tekshiruvini bu muhitda bajarish
> imkonsiz, demak timing natijalari shu shart ostida o'qilishi kerak.*

**TALQIN (torlashtirilgan, yumshatish EMAS):** §4(5) dagi throughput bandi
`θ · R_ref` ni ishlatadi, `R_ref` esa **shu trial'ning o'zining** fault'dan
oldingi throughput'i — ya'ni nisbat trial ichida normalizatsiya qilingan.
Demak §10.1 ning **binar** birlamchi endpoint'i (`P(VR)`, Cochran–Armitage)
sekin chastota drift'iga absolut timing o'lchovlaridan **kamroq ta'sirchan**.
**Bu timing tahdidini kamaytirMAYDI** va §11 ning fail-slow shakli (RMST,
`τ = 8 s`) yuqoridagi cheklov ostida qoladi. Trial ichidagi tez chastota
o'zgarishi `R_ref` ni ham buzadi, va buni ham **o'lchab bo'lmaydi**.

> **Nega bu yerda yozilgan:** `CONTRIBUTING.md` va `README.md` manfiy natija va
> noqulay faktni yashirishni taqiqlaydi. §8.5 — aynan shu qoidaning sinovi.
> Agar bu cheklov amendment'ga yozilmasa, u maqolaga ham yetib bormaydi.

### 15.5 CHEKLOV — `W_stab = 60 s` hali ham erishib bo'lmaydi, lekin sabab siljidi

§4 ning ochiq cheklovi **o'zgarmaydi:**

> *P1 o'lchaydigan narsa — "pressure davom etayotganda tasdiqlangan recovery",
> 60 s sustained recovery EMAS. Bu maqolada shunday yoziladi, yumshatilmaydi.*

**O'zgargan narsa — sabab.** v1.3 gacha asosiy to'siq privilegiya **va** oomd
edi (`00-pilot-topologiya.md` §3.1(a): *"ILMIY CHEKLOV yaratadi"*). Endi oomd
to'sig'i bu muhitda yo'q, lekin cheklov **o'z joyida**, chunki qolgan sabablar
yetarli:

| # | sabab | holat |
|---|---|---|
| 1 | `W_stab_pilot = 8 s` **muzlatilgan** (§4) | v1.4 uni o'zgartirmaydi |
| 2 | `hold_cap_s = 12 s`, `guard_sustain_s = 15 s` **muzlatilgan** (§9.4) | 15.3 ga qarang |
| 3 | `io` controller delegated emas — o'lchangan: `cpu memory pids` (15.1) | §0 da allaqachon qamrovdan tashqarida |
| 4 | `drop_caches` root talab qiladi (§8.3) | qilinmaydi |
| 5 | guard o'zini oomd'dan himoya qila olmaydi (`oom_score_adj` pasaytirish privilegiya talab qiladi) — `02-guard-kalibratsiyasi.md` §7, 3-masala | bu muhitda oomd yo'q, lekin privilegiya cheklovi o'zgarmadi |

Demak: **cheklov endi asosan muzlatilgan shartnomadan va privilegiyasiz
muhitdan kelib chiqadi, oomd'dan emas.** Bu farq maqolada ham shunday
yoziladi — "oomd bizni cheklaydi" deb yozish bu muhitda **noto'g'ri** bo'lardi.

`/dev/kvm` mavjud (o'lchangan, 15.1), demak `02-guard-kalibratsiyasi.md` §7
(4- va 6-masalalar) ko'rsatgan "VM kerak" yo'li texnik jihatdan **ochiq**.
Lekin sustained pressure >12 s **§0 bo'yicha P1 qamrovidan tashqarida** va
**o'z pre-registration'ini talab qiladi.** v1.4 bu yo'lni ochmaydi va §13 ga
tegmaydi.

### 15.6 Ochiq masalalar — v1.4 ularni HAL QILMAYDI, faqat qayd etadi

1. **`v0.1.1-preregistration` tag mavjud emas.** `git tag --list` faqat
   `v0.1.0-preregistration` ni beradi. v1.1 → v1.2 yozuvi
   `v0.1.1-preregistration` ga havola qiladi, lekin u **push qilinmagan.**
   v1.2, v1.3 va v1.4 ham tag'siz. Tag'lash integratsiyadan keyin bajariladi;
   bu amendment hech qanday tag yaratmaydi.
2. **§14.4 ning `run_meta` qatori "§7 tirik unit shartini ko'ring" deydi, lekin
   §7 — *Pressure o'lchovi* va unda tirik unit haqida hech qanday shart yo'q.**
   Haqiqiy talab `docs/architecture/01-muhit-tekshiruvlari.md` §4 da:
   *"Har unit'ning property'lari u TIRIK paytida dump qilinishi shart"*; shu
   havolani `04-driver-va-analiz-shartnomasi.md` §1.1 **to'g'ri** ishlatadi.
   Bu yerda **jimgina qayta ko'rsatilMADI**, chunki havola muzlatilgan hujjat
   ichida va v1.2 aynan shunday noto'g'ri havolani tuzatish uchun yaratilgan —
   demak u o'z amendment'ini talab qiladi. **Talabning o'zi to'liq kuchda:
   `units_show` unit tirik paytida olinadi.**
3. **systemd 257 ≥ 254**, demak `RestartSteps=` mavjud. Lekin
   `01-muhit-tekshiruvlari.md` §4 dagi transient-unit qabul qilinishi
   **eski mashinada** o'lchangan; bu mashinada **qayta tasdiqlanishi kerak**.
   P1 ni bloklamaydi, chunki Baseline B §9.3 bo'yicha P1 da **yo'q**.
4. **Guard va pressure dosing kalibratsiyasi bu mashinada bajarilmagan.**
   `00-pilot-topologiya.md` §6: 3-qadam (guard testi) keyingi har bir qadamni
   gate qiladi, 4-qadam (pressure dosing) undan keyin. Bu amendment uchun
   **hech qanday pressure eksperimenti ishga tushirilmadi.**

### 15.7 NATIJA — yo'q

**Hech qanday eksperiment ishga tushirilmadi. Hech qanday natija yo'q.**
Shuning uchun v1.4 ostida eski ta'riflar bilan qayta hisoblanishi kerak
bo'lgan hech qanday ma'lumot yo'q. Bu bo'lim faqat **o'lchangan muhitni** va
**undan kelib chiqadigan cheklovlarni** qayd etadi.

---

## 16. Analiz to'plami, `censored` ning ikki ma'nosi, va muzlatilmagan parametrlar (muzlatilgan)

> Bu bo'lim **v1.5 amendment** bilan qo'shildi. U **hech bir operatsion
> ta'rifni, metrikani, chegarani, statistik testni yoki falsifikatsiya
> mezonini o'zgartirmaydi.** U §6.2, §4, §10.1, §10.2, §11 va §12 ning
> allaqachon muzlatilgan matnini **bir-biriga nisbatan o'qiydi** va §12 jim
> qolgan nuqtalarni hal qiladi.
>
> **Nega kerak bo'ldi:** ikki mustaqil implementator (`driver.py`,
> `analyze.py`) bir xil oqibatni ko'rsatdi — barcha 60 `no_action` trial
> birlamchi analiz to'plamidan chiqib ketadi. v1.2 ham aynan shunday
> hodisadan tug'ilgan: ikki implementator bir vaqtda bir xil bo'shliqni
> ko'rsatsa, bu **pre-registration bo'shlig'i**, implementatsiya xatosi emas.
>
> **Nega yangi bo'lim:** mavjud bo'limlarni tahrirlash yoki qayta raqamlash
> `revix/schema.py`, `revix/reduce.py`, `revix/prober.py` va hujjatlardagi
> havolalarni buzardi — v1.2 (§14) va v1.4 (§15) ham oxiriga qo'shgan.

### 16.1 FAKT — nima aniqlandi

Ikki **committed va test bilan qoplangan** modul "birlamchi analizga qaysi
disposition kiradi" savoliga **turli javob** beradi, va nomlari faqat bitta
so'z bilan farq qiladi (fayllar o'qildi, **o'zgartirilmadi** — ular bu
agentga tegishli emas):

```
reduce.PRIMARY_DISPOSITIONS            == ("complete",)              # reduce.py:117
schedule.PRIMARY_ANALYSIS_DISPOSITIONS == ("complete", "censored")
```

`schedule.py` yana `enters_primary_analysis(disposition)` ni va o'z
kengaytirilgan to'plamining to'ldiruvchisi bo'lgan
`schedule.EXCLUDED_DISPOSITIONS` ni ham beradi. Endpoint'ni **amalda
hisoblaydigan** narsa — `reduce.select_primary`, ya'ni **tor** to'plam.

Oqibati: `derive_disposition` "horizon down holatda tugadi" ni **`censored`**
ga map qiladi; `no_action` arm `Restart=no` bo'lgani uchun `clean_crash` dan
keyin **hech qachon** qaytmaydi, demak **har doim** horizon down holatda
tugaydi, demak **har doim** `censored`, demak **60 trial ham birlamchi
to'plamdan chiqadi** — §8.2 esa shu arm'ni **majburiy** deb e'lon qiladi.

### 16.2 QAROR — savol bitta emas, ikkita

Ularni bitta savol deb ko'rish — chalkashlikning manbai.

| # | savol | javob |
|---|---|---|
| **A** | §10.1 ning trend testi qaysi arm ustida hisoblanadi? | **faqat arm `A` ustida** |
| **B** | "horizon down holatda tugadi" trial'lari binar endpoint'ning maxrajiga kiradimi? | **KIRADI, `VR = false` sifatida** |

#### (A) Trend testi arm `A` ichida — matn buni qo'llab-quvvatlaydi

§9.1 yagona savolni shunday qo'yadi: pressure *"systemd'ning o'z
`Restart=on-failure` i bilan restart qilinadigan oson tuzatiladigan fault"*
uchun `P(VR)` ni kamaytiradimi. Bu **ta'rifan arm `A`**.

§9.2 ning to'rtta oldindan aytilgan mexanizmi — `TimeoutStartSec` oshib
ketishi, start paytida OOM-kill, start'dan keyingi brownout, watchdog miss —
**to'rtalasi ham restart'ni nazarda tutadi.** `Restart=no` arm'da ularning
hech biri sodir bo'lishi mumkin emas.

§8.2 `no_action` ga **o'z vazifasini** beradi: *"Busiz 'restart PSI ni
oshirdi' ni 'fault PSI ni oshirdi' dan ajratib bo'lmaydi va `harm_indicator`
talqin qilinmaydi."* Bu **PSI atributsiyasi** vazifasi — trend testiga
yacheyka qo'shish vazifasi emas. `docs/research/05-metodologiya.md` §4 ham
shunday: `no_action` → *"fault'ning o'zi PSI ni qancha oshirdi"*.

**Hal qiluvchi arifmetika:** `no_action` da `P(VR) = 0` **har uchala
pressure darajasida, konstruksiya bo'yicha**. Ikki arm'ni pool qilish uchala
strataga bir xil nolni qo'shadi, ya'ni trend'ni **susaytiradi**, va §11 ning
`P(VR|P0) − P(VR|P2)` farqini `0 − 0 = 0` ga intiltiradi — falsifikatsiya
mezoni **trivial ravishda** qanoatlanadi. Pooling nafaqat keraksiz, balki
**testni buzadi.**

→ **`no_action` trial'lari trend testiga yacheyka bermaydi.** Ular §6.2
bo'yicha KM/log-rank ga, loop-rate ga va har bir jadvalning
`recovered within T_trial: k/n` qatoriga **kiradi**, va §8.2 bo'yicha PSI
atributsiyasi va `harm_indicator` uchun ishlatiladi. Hech narsa
yashirilmaydi.

**Lekin §10.1 bu arm qamrovini AYTMAYDI**, va `analysis.json` ning
`primary.cells` sxemasi (`04-driver-va-analiz-shartnomasi.md` §2.2) faqat
`level` kaliti bilan, **`arm` kaliti bo'lmagan** holda yozilgan — ikki
implementator'ning xavotiri aynan shundan. Shu sababli ochiq yoziladi:
**§10.1 ning birlamchi Cochran–Armitage trend testi arm `A` ichida
hisoblanadi**, va `analysis.json` da arm ochiq ko'rsatiladi.

#### (B) "Horizon down" — kuzatilgan NO'L-HODISA, censoring EMAS

§12 ning `censored` yorlig'i **ikki epistemologik jihatdan boshqa** holatni
bitta nom ostida birlashtiradi:

| sabab | nima bo'ldi | binar `VR` natijasi |
|---|---|---|
| **probe uzilishi > 2×P** | instrumentatsiya yo'qoldi | **kuzatilMADI** |
| **horizon down holatda tugadi** | xizmat qaytmadi | **kuzatildi: `false`** |

Matn bu ikkisini allaqachon boshqacha ishlaydi:

- **§4** (invalidator'lardan keyin): *"**Probe uzilishi > 2×P** → trial
  `censored`, **`failed` emas**. Instrumentatsiya yo'qolishi hech qachon
  jimgina natijaga aylanmaydi."* Bu yerda `censored` ning qarshi qo'yilgani —
  `failed`. Ya'ni §4 `censored` ni **"kuzatmagan narsani natija deb
  yozmaymiz"** ma'nosida ishlatadi.
- **§6.2**: *"Horizon tugasa va xizmat hali down bo'lsa → **downtime**
  `T_trial` da censored."* Censored bo'lgan narsa — **davomiylik**, binar
  natija emas. Downtime'ning haqiqiy qiymati `≥ T_trial`, aniq qiymati
  noma'lum — bu haqiqiy right censoring va shuning uchun bu trial'lar
  KM/log-rank ga kiradi.
- **§4** ning VR ta'rifi **horizon bilan chegaralangan**: *"Epizod `E`
  verified-recovered, agar `[t_up, t_up + W_stab]` oynasi **mavjud bo'lsa**…"*
  `t_up` umuman paydo bo'lmagan trial uchun oyna **mavjud emas**, demak
  `VR = false` — **to'liq aniqlangan**, yetishmayotgan kuzatuv emas.

→ **`disposition_source == "down_at_horizon"`** → binar birlamchi to'plamga
`VR = false` sifatida **kiradi**.
→ **`disposition_source == "probe_gap"`** → binar birlamchi to'plamdan
**chiqariladi** (natija kuzatilmagan), **lekin ulushi §12 qoidasi bo'yicha
natija sifatida beriladi.**
→ Ikkalasi ham §6.2 bo'yicha KM/log-rank va loop-rate ga **censored
davomiylik** sifatida kiradi.

**Yangi enum qiymati KERAK EMAS, va §12 ning yopiq enum'iga tegilMAYDI.**
Farq allaqachon ma'lumotda: `reduce.py` har trial uchun
**`disposition_source`** ni yozadi (`"probe_gap"` / `"down_at_horizon"` /
`"guard_event"` / `"trial_end"` / `"derived"`). Qoida:

> **Birlamchi analiz to'plami `disposition` bilan EMAS, `(disposition,
> disposition_source)` jufti bilan aniqlanadi.**

### 16.3 CHEKLOV — arm `A` uchun bu xato ANCHA og'ir

Savol `no_action` ustida qo'yilgan, lekin zarar **arm `A`** da kattaroq.

Arm `A` trial'i `P2` ostida restart qilishga urinib, horizon tugaguncha
qaytmasligi mumkin — **aynan H1 oldindan aytgan natija** (§9.2 mexanizmlari
i, ii, iv). Agar bu trial'lar birlamchi to'plamdan chiqsa:

1. `P(VR|P2)` faqat **qaytgan** trial'lar ustida hisoblanadi → **1 ga qarab
   siljiydi**;
2. demak `P0 → P2` trendi **susayadi**;
3. demak §11 ning qoidasi — *"trend p > 0.05 **VA** Newcombe CI yuqori
   chegarasi < 0.15"* — **siljigan baho** ustida qo'llanadi;
4. demak **"null" natija dunyodan emas, eksklyuziyadan tug'ilishi mumkin.**

§6.2 aynan shuni ogohlantiradi: *"**Recovery bo'lmagan trial'larni tashlash —
klassik yashirin bias**, va u tez ishdan chiqadigan arm'ni chiroyli
ko'rsatadi."* Shuning uchun §6.2 har jadvalda **`T_trial` ichida recovered:
k/n`** ni talab qiladi — `n` maxraji qaytmagan trial'larni **o'z ichiga
oladi**.

> **Yo'nalishni ochiq e'lon qilaman:** bu qaror H1 ning **foydasiga**
> ishlaydi — u `P2` dagi qaytmagan trial'larni tiklaydi, demak trend'ni
> **kuchaytiradi**. Buni bilib turib qabul qilaman, chunki (i) §6.2 bu
> qoidani hech qanday ma'lumot mavjud bo'lishidan **oldin** muzlatgan,
> (ii) alternativa ko'rsatib bo'ladigan darajada siljigan, (iii) hech qanday
> ma'lumot yo'q, demak bu qarorni natijani ko'rib tanlash imkoniyati mavjud
> emas. Agar bu qaror ma'lumot ko'rilgandan **keyin** qabul qilinsa — u
> **qonuniy bo'lmas edi.**

### 16.4 Ikki konstanta — qaysi biri qaysi savolga javob beradi

16.2 dagi qarordan keyin **ikkala konstanta ham o'z savoliga to'g'ri
javob beradi, lekin biri noto'g'ri nomlangan va biri noto'g'ri
qo'llanilgan:**

| konstanta | qaysi savolga javob beradi | holati |
|---|---|---|
| `schedule.PRIMARY_ANALYSIS_DISPOSITIONS == ("complete", "censored")` | **analiz to'plami butun holda** — survival, loop-rate va `k/n` jadvallariga kiradigan trial'lar (§6.2) | **to'g'ri**, lekin nomi `ANALYSIS_SET` bo'lishi kerak edi; `PRIMARY` so'zi uni §10.1 ning birlamchi testi bilan chalkashtiradi |
| `reduce.PRIMARY_DISPOSITIONS == ("complete",)` | **binar `P(VR)` ning maxraji** (§10.1) | **to'g'ri savol, NOTO'G'RI javob** — 16.2(B) bo'yicha maxraj `complete` **va** `down_at_horizon` ni o'z ichiga olishi kerak |

Ya'ni javob "biri to'g'ri, biri noto'g'ri nomlangan" **emas**: tor to'plam
noto'g'ri nomlanmagan, u **noto'g'ri qiymatga ega**. `schedule.py` esa
§6.2 ga mos, lekin nomi bilan chalg'itadi.

**Majburiy hisobot qoidasi.** §12 eksklyuziya darajasini **natija** deb
e'lon qiladi (*"Yuqori eksklyuziya darajasi o'zi natija — yashirilmaydi"*).
Ikki xil to'plam ikki xil eksklyuziya darajasi beradi, demak:

> **Har qanday maqolada, jadvalda yoki `analysis.json` da berilgan
> eksklyuziya darajasi QAYSI to'plam ustida hisoblanganini NOMLASHI
> SHART** — binar `P(VR)` maxraji, yoki survival/`k/n` analiz to'plami.
> Nomlanmagan eksklyuziya darajasi **takrorlanuvchi emas** va natija
> sifatida berilmaydi.

`analysis.json` ning `exclusions` obyekti (`04-…` §2.2) shu sababli ikkala
to'plam uchun **alohida** berilishi kerak.

### 16.5 QAROR — §11 ning pressure kontrasti va §10.2 ning arm KM'i

§10.2: *"**Birlamchi: Kaplan–Meier time-to-VR har arm uchun**, log-rank
bilan taqqoslash."* §11: *"fail-slow shakli qo'llab-quvvatlanmaydi, agar
`P0` va `P2` orasidagi time-to-VR RMST farqi (`τ = 8 s`) uchun 95% CI 20%
oshishni chiqarib tashlasa."* Biri **arm** bo'yicha, ikkinchisi **pressure**
bo'yicha — va §11 arm'ni aytmaydi, xuddi §10.1 aytmaganidek.

**Xuddi shu asos bilan xuddi shunday hal qilinadi** (aks holda §10.1 va §11
turli qamrovda bo'lib qolardi):

- §10.2 ning **har arm uchun KM** — taqdimot va stratifikatsiya birligi;
  `A` vs `no_action` log-rank §8.2 ning atributsiya savoliga javob beradi,
  **H1 ga emas**.
- §11 ning **`P0` vs `P2` RMST kontrasti arm `A` ICHIDA** hisoblanadi.
  `no_action` da time-to-VR har uchala darajada ta'rifan mavjud emas, demak
  u yerda `P0` vs `P2` kontrasti **bo'sh** — 16.2(A) dagi pooling
  argumentining aynan o'zi.
- §10.4 *"P1 da bitta fault class bor, demak **bitta birlamchi test**"*
  deydi, demak §10.1 ning Cochran–Armitage testi **yagona birlamchi test**;
  §10.2 ning KM oilasi — taqsimotlar uchun birlamchi **usul**, va §11 ning
  RMST bandi **fail-slow ikkilamchi shakli**. Holm oilasi (§10.4)
  o'zgarmaydi.

### 16.6 NIMA O'ZGARMAYDI

- `VR` ta'rifi (§4) — **o'zgarmadi.** `P(VR)` har doim "§4 shartini
  qanoatlantirgan trial'lar ulushi" bo'lgan; o'zgargan narsa — maxrajga
  qaysi trial'lar kirishi, va **u hech qachon pre-registration'da
  yozilmagan edi.**
- §10.1 ning birlamchi testi (Cochran–Armitage), §11 ning falsifikatsiya
  qoidasi va halol power bayonoti, §10.2 ning KM/log-rank/RMST
  (`τ = 8 s`, Cox/HR taqiqi), §10.4 ning Holm oilasi, §12 ning yopiq
  enum'i va "aynan bitta disposition" qoidasi, `θ = 0.8`,
  `W_stab_pilot = 8 s`, `W_stab = 60 s`, `T_conn`/`T_rt` = 50 ms,
  `P` = 100 ms, `k_f` = 3, `ε` = 32 MiB, quiescence 0.05, `T_q` = 5 s,
  `T_w` = 15 s, `T_w_max` = 120 s, `hold_cap_s` = 12 s,
  `guard_sustain_s` = 15 s, arm'lar `A`/`no_action`, 20 blok / 120 trial,
  §14 data schema — **hammasi o'zgarmadi.** §13 ga tegilmadi.
- `PRIMARY_DISPOSITIONS == ("complete",)` **muzlatilgan qiymat emas** —
  u §12 ning jimligini implementator hal qilgan joy. Bu bo'lim o'sha
  jimlikni §6.2 foydasiga hal qiladi. Shuning uchun **`reduce.py` ni
  tuzatish — muzlatilgan matnga MOSLASHTIRISH**, pre-registration'ni
  o'zgartirish emas. Kod bu agentga tegishli emas va **o'zgartirilmadi**;
  ikkala modul ham test bilan qoplangan, demak o'zgarish **ataylab
  qilingan qaror** bo'lishi kerak, jimgina tuzatish emas.

### 16.7 CHEKLOV — §12 va §6.2 matn sifatida ziddiyatda

1. **§12 enum'i `censored` ni sanaydi, lekin uning analiz holatini
   AYTMAYDI.** §12 faqat `contaminated` va `aborted_guard` ni ochiq
   chiqaradi; `censored`, `washout_timeout`, `harness_error` haqida hech
   narsa demaydi. `complete` qatori *"birlamchi analizga kiradi"* deydi —
   bu `complete` **yetarli** shart ekanini bildiradi, **zarur** ekanini
   bildirmaydi; kod uni zarur deb o'qidi.
2. **§6.2 ning "tashlanmaydi, ishlanadi" qoidasi va
   `reduce.PRIMARY_DISPOSITIONS == ("complete",)` matn sifatida
   ziddiyatda.** Ikkisi bir vaqtda to'g'ri bo'lishi mumkin emas. Bu bo'lim
   §6.2 ni ustun deb hal qiladi, chunki §6.2 **muzlatilgan matn**, kod
   konstantasi esa **emas**.

### 16.8 OCHIQ SAVOL — `W_stab` oynasi horizon'dan oshib ketsa

16.2(B) ikki holatni hal qildi. **Uchinchi holat bor:** xizmat qaytdi,
lekin horizon `t_up + W_stab_pilot` dan **oldin** yopildi. Bunda `VR`
**haqiqatan ham administrativ censored** — oyna o'tarmidi yoki yo'qmi,
biz bilmaymiz.

§9.4 jadvali bu holatni to'g'ri trial'da oldini oladi (`injeksiya 3 s +
W_stab_pilot 8 s = 11 s ≤ hold_cap_s 12 s`), lekin `P2` ostida kechikkan
restart — **aynan H1 kutgan narsa** — `t_up` ni keyinga suradi.
**Oyna pressure hold ichida bo'lishi SHARTmi** — §4 buni aytmaydi.

**Bu savolga javob berish `W_stab` ning ta'rifiga tegadi, demak bu bo'lim
unga javob BERMAYDI.** U birinchi trial'dan **oldin** hal qilinishi shart.

**Nega birinchi darajali:** hozirgi kodda bu holat `down_at_horizon` emas,
`complete` sifatida tushib, `VR = false` berishi mumkin — ya'ni haqiqiy
censoring'ni **kuzatilgan muvaffaqiyatsizlik** deb yozishi mumkin. Bu
16.3 dagiga **teskari yo'nalishdagi** bias (yana H1 foydasiga), demak u
ham tekshirilishi shart.

### 16.9 OCHIQ SAVOL — §8.2 ning (ii) varianti §9.3 jadvalida yo'q

§8.2: *"**No-action arm MAJBURIY**, opsional emas: (i) injeksiya +
`Restart=no`, (ii) injeksiya yo'q — har pressure darajasida."*
§9.3 esa ikkita arm beradi (`A`, `no_action`) va `3 × 2 × 20 = 120`.
Ya'ni **(ii) "injeksiya yo'q" varianti 120-trial jadvalida yo'q.**
`docs/research/05-metodologiya.md` §4 uni alohida nazorat qatori sifatida
sanaydi (*"injeksiya yo'q, pressure bor"*).

**Hal qilinMADI**, chunki har qanday yechim §9.3 ning muzlatilgan trial
soniga (120) tegadi. Qayd etiladi.

### 16.10 CHEKLOV — muzlatilmagan parametrlar natijani YARATA oladi

`revix/driver.py` parametrlarni **standart qiymat bilan** to'ldirishga
majbur bo'ldi, chunki ular **hech qayerda muzlatilmagan**. Ikkitasi §9.2
ning oldindan aytilgan mexanizmlarini **boshqaradi**, demak ular
**kutilgan natijani yarata oladi** — bu §11 ning davom etish mezoni (c)
(*"mexanizm log'larida faqat `P2` da paydo bo'ladigan takrorlanuvchi yo'l,
masalan `Result=timeout`"*) uchun to'g'ridan-to'g'ri xavf.

| # | parametr | driver tanlagani | nega xavfli |
|---|---|---|---|
| 1 | `TimeoutStartSec` | 10 s | §9.2 mexanizm **(i)** *"`TimeoutStartSec` oshib ketdi"* **shu qiymat bilan belgilanadi**. Kichik qiymat `Result=timeout` ni yaratadi, katta qiymat uni yo'q qiladi |
| 2 | `WatchdogSec` | 5 s | §9.2 mexanizm **(iv)** *"watchdog miss"* **shu qiymat bilan belgilanadi**. `00-pilot-topologiya.md` §1 da `WatchdogSec=` — **qiymatsiz dial** |
| 3 | slice `MemoryHigh` dial | 192 M | kalibratsiya **`MemoryMax=1G`** ostida o'lchangan (`02-guard-kalibratsiyasi.md` sarlavhasi), lekin `00-pilot-topologiya.md` §1 va §2 **`MemoryMax=2G`** ni muzlatadi — **qiymat ko'chirilmaydi** |
| 4 | `P2` nishon stall tezligi | 0.70 | §9.3 ning `~60–80%` bandi **ichida**, demak buzilish emas; lekin kalibratsiya faqat 0.60 ni nishonga olgan va **0.558** ga erishgan — band'ning pastki chekkasidan **past** |
| 5 | **`T_trial`** (horizon) | shartnoma formulasi: `t_pressure_off + w_stab_s + P` = **40.1 s** | §6.2, §6.4 unga tayanadi, lekin **hech qayerda raqamlanmagan**. 16.2(B) dan keyin u binar endpoint'ning **maxrajini to'g'ridan-to'g'ri belgilaydi**: qisqa horizon qaytmaslikni yaratadi, uzun horizon qaytishni |
| 6 | `τ` va horizon munosabati | `τ = 8 s` muzlatilgan (§10.2) | `T_trial` muzlatilmagani uchun `τ ≤ T_trial` invarianti **tekshirilmaydi** |

**`T_trial` haqida aniq:** 40.1 s — `driver-contract/v1.2` ning formulasi,
ya'ni **qaror bilan emas, default bilan** o'rnatilgan. U quyidagi
muzlatilgan qiymatlardan kelib chiqadigan chegaralarni **qanoatlantiradi**,
demak u *noto'g'ri* emas — u **hal qilinmagan**.

#### QAROR — raqam muzlatilMAYDI, QOIDA muzlatiladi

Men bu qiymatlarning **hech birini o'lchamadim.** O'lchamagan qiymatni
muzlatish §9.4 ning *"`ramp_above_threshold_s` pressure dosing
kalibratsiyasidan olinadi, **taxmin qilinmaydi**"* qoidasini va v1.3 ning
*"ma'lumot bilan asoslangan amendment, taxmin bilan emas"* majburiyatini
buzardi. Shuning uchun **qiymat emas, qoida muzlatiladi:**

1. Hammasi **birinchi pilot trial'idan OLDIN** `experiment/pressure-cal`
   tomonidan belgilanadi va `run_meta.open_parameters` ga kalibratsiya
   run'ining `run_id` si bilan yoziladi.
2. Ular **barcha arm'lar bo'ylab va barcha pressure darajalari bo'ylab
   AYNAN bir xil** bo'ladi. Aks holda ular arm/daraja bilan confound
   bo'ladi — §8.2 probe narxi uchun aynan shu qoidani qo'yadi
   (*"Arm'lar bo'yicha bir xil ushlanadi"*).
3. **Hech qanday P1 natijasi ko'rilgandan keyin o'zgartirilMAYDI.**
   Post-hoc o'zgarish **run'ni bekor qiladi**, parametrni emas.
4. `T_trial` uchun muzlatilgan qiymatlardan kelib chiqadigan **pastki
   chegara** (arifmetika, o'lchov emas): §9.4 jadvali `baseline 10 s +
   ramp 5 s + injeksiya hold'ga 3 s` ⇒ injeksiya trial boshidan ≥ 18 s da;
   §4 `W_stab_pilot = 8 s` oynasini talab qiladi ⇒ **`T_trial` ≥ 26 s**;
   va §10.2 uchun **`τ ≤ T_trial`** (`τ = 8 s`). Shartnomaning 40.1 s
   default'i ikkalasini ham qanoatlantiradi (`40.1 ≥ 26`, `8 ≤ 40.1`),
   lekin **aniq qiymat kalibratsiyadan olinadi va ochiq qaror bilan
   muzlatiladi.**
5. §11 ning (c) mezoni mexanizm **(i)** yoki **(iv)** ga tayansa,
   hisobotda `TimeoutStartSec` / `WatchdogSec` ning muzlatilgan qiymati va
   *"bu mexanizmning mavjudligi shu qiymat bilan belgilangan"* bayonoti
   **berilishi SHART.** Busiz (c) ni da'vo qilish — o'z tanlagan
   parametrini natija deb ko'rsatish.
6. `MemoryHigh` dial `MemoryMax=2G` topologiyasida **qayta o'lchanadi**;
   1G ostida o'lchangan 192 M ko'chirilmaydi.

#### CHEKLOV — `P2` bandi hali erishiladigan deb ko'rsatilMAGAN

§9.3 `P2` ni `~60–80%` deb muzlatadi. Kalibratsiya faqat 0.60 nishonini
sinagan va **0.558** ga erishgan — band'ning pastki chekkasidan past.
`02-guard-kalibratsiyasi.md` §8 *"P1/P2 bandlari **erishiladigan**
(0.30 → 0.311 ko'rsatildi)"* deydi, lekin keltirilgan o'lchov (0.311)
**`P1` bandida** (20–35%), `P2` da emas — **ya'ni bu da'vo `P2` uchun
o'lchov bilan qo'llab-quvvatlanmaydi.** Bu o'sha hujjatdagi overclaim,
shu yerda qayd etiladi (fayl bu agentga tegishli emas).

§9.4 ning *"analiz ERISHILGAN (uzluksiz) pressure'dan foydalanadi"*
qarori uzluksiz analizni himoya qiladi. Lekin **kategorik** trend
testining uchinchi stratasi erishilmasa, §10.1 ning Cochran–Armitage
testi uch daraja o'rniga amalda **ikki darajaga qulaydi**. Bu oldindan
e'lon qilingan xavf va kalibratsiya natijasi bilan hal qilinadi.

### 16.11 FAKT + CHEKLOV — `boot_id` kafolati bu host'da BUZILGAN

§1: *"Monotonic qiymatlar faqat bitta boot ichida taqqoslanadi; **`boot_id`
bu shartni tekshirib bo'ladigan qiladi**."* §14.6 invariant 5: *"`boot_id`
sessiya ichida o'zgarmas."*

**Shu mashinada o'zim o'lchadim** (faqat o'qish; hech qanday pressure,
hech qanday unit yaratilmadi), 49 s oraliq bilan ikki marta:

| o'lchov | 1-o'qish `18:18:56Z` | 2-o'qish `18:19:45Z` |
|---|---|---|
| `/proc/sys/kernel/random/boot_id` | `ca4e5bab-2cd8-43aa-8455-2a22ca6746f3` | `ca4e5bab-2cd8-43aa-8455-2a22ca6746f3` — **AYNAN BIR XIL** |
| `/proc/uptime` (1-maydon) | `1975.34` s | `2024.34` s (+49.0 s, normal) |
| `/proc/1/stat` 22-maydon | `191289` tick | **`201467`** tick (+10178 tick = **+101.78 s**) |
| PID 1 yoshi = `uptime − starttime/HZ` | `62.46` s | **`9.68` s — ORQAGA KETDI** |
| `getconf CLK_TCK` | `100` | `100` |

Qo'shimcha o'lchovlar (1-o'qish): `systemctl show -p
UserspaceTimestampMonotonic` = `1913200622` µs (= 1913.2 s), ya'ni
systemd'ning **o'zi** userspace 1913 s da boshlanganini aytadi, kernel
uptime esa 1975 s; `FinishTimestampMonotonic` = `1913973576` µs;
`CLOCK_MONOTONIC` = `CLOCK_BOOTTIME` (delta ≈ `-0.000`), demak monotonic
soatning o'zi uzluksiz ko'rinadi.

**FAKT:** `boot_id` o'zgarmagan holda PID 1 ning yoshi 62.46 s dan 9.68 s
ga **kamaydi**, va uning `starttime` i uptime 49 s o'tganda 101.78 s
oldinga sakradi. Bu faqat bitta narsa bilan izohlanadi: **PID 1 (systemd)
`boot_id` o'zgarmagan holda qayta ishga tushdi** (hisob: yangi PID 1
uptime ≈ `2014.67` s da boshlangan, bu ikki o'qish orasidagi oraliqda).

**TALQIN:** `boot_id` ning o'zgarmasligi **endi bitta uzluksiz systemd
instansiyasini KAFOLATLAMAYDI.** §1 ning *"`boot_id` bu shartni tekshirib
bo'ladigan qiladi"* da'vosi shu host'da **yolg'on**: §14.6(5) invarianti
**zarur, lekin YETARLI EMAS.**

**GIPOTEZA (o'lchanMAGAN, lekin birinchi trial'dan oldin o'lchanishi
SHART):** systemd qayta ishga tushsa, u kuzatayotgan unit'larning
`NRestarts` hisoblagichi nolga qaytishi va `InvocationID` yangilanishi
mumkin. Agar `NRestarts` oyna boshida ham, oxirida ham `0` bo'lsa, §4 ning
**4-bandi** (*"`NRestarts` butun oyna davomida o'zgarmaydi"*) **restart
sodir bo'lgan holda ham qanoatlanadi** — ya'ni **soxta VR**. §4 ning
3-bandi (`InvocationID` o'zgarmasligi) teskari yo'nalishda ishlaydi va
VR ni `false` qiladi, ya'ni konservativ. **Ikkala bandning PID 1 restart
ostidagi xatti-harakati o'lchanishi shart** — bu o'lchov **bajarilmadi.**

**O'LCHANMADI:** to'liq WSL VM restart'ida `boot_id` o'zgaradimi —
**bu o'lchov bajarilmadi**, chunki avvalgi VM restart'idan oldin
`boot_id` yozib olinmagan edi. (Wall-clock va uptime farqi o'sha
restart'ni ko'rsatadi: `17:21Z` da uptime ≈ 2 daqiqa, `18:18Z` da
1975 s ≈ 32.9 daqiqa, ya'ni ~60 daqiqa wall-clock ichida uptime ~31
daqiqa o'sgan.)

**Majburiy qo'shimcha shart (yangi invariant EMAS — §14.6 qayta
raqamlanMAYDI):** `boot_id` ga qo'shimcha ravishda **PID 1 ning
`starttime` i (`/proc/1/stat` 22-maydon)** `run_meta` va har
`env_snapshot` da yozilishi, va validator **uni ham** sessiya ichida
o'zgarmas deb tekshirishi shart. O'zgargan bo'lsa — run **bekor**, chunki
monotonic taqqoslanuvchanlik va `NRestarts`/`InvocationID` bookkeeping'i
bir vaqtda shubhali bo'ladi. Bu §14.6(5) ni **almashtirmaydi**, uni
**to'ldiradi**.

> Bu fakt §15.1 ning muhit fingerprint'ini **kengaytiradi.** §15 muzlatilgan
> bo'lgani uchun u yerga yozilmaydi — **§15.1 va 16.11 birga o'qiladi.**
> Bu shu muhitda ishlashning **feasibility gate**'i hamdir: trial davomida
> systemd qayta ishga tushsa, transient unit'lar va `--collect` unit'lari
> yo'qoladi. `00-pilot-topologiya.md` §6 ning qadam tartibi shu sababdan
> ham majburiy.

### 16.12 NATIJA — yo'q

**Hech qanday eksperiment ishga tushirilmadi. Hech qanday natija yo'q.**
Shuning uchun bu bo'limdagi hech bir qaror hech qanday kuzatilgan
natijani ko'rgandan keyin qabul qilinmagan, va eski ta'riflar ostida
qayta hisoblanishi kerak bo'lgan ma'lumot yo'q.

---

## 17. Stabilizatsiya oynasi va pressure hold — dizayn nuqsoni (muzlatilgan)

> Bu bo'lim **v1.6 amendment** bilan qo'shildi va §16.8 ning ochiq savoliga
> javob beradi. U **hech bir operatsion ta'rifni, metrikani, chegarani,
> statistik testni yoki falsifikatsiya mezonini o'zgartirmaydi.** U ikki
> narsani qiladi: (1) §16.8 dagi **o'z xatomni tuzatadi**, (2) nuqsonni
> aniq ko'rsatadi va **uni hal qilish uchun loyiha egasiga qaror
> qoldiradi** — chunki hal qilish muzlatilgan ta'rifga tegadi.

### 17.1 TUZATISH — §16.8 dagi ikki da'vom XATO edi

v1.5 §16.8 shunday dedi: *"**Oyna pressure hold ichida bo'lishi SHARTmi** —
§4 buni aytmaydi."* **Bu xato.** §4 ning parametr jadvali buni ochiq
aytadi:

> | `W_stab_pilot` | **8 s** | sustained HOLD (≤12 s) **ichida sig'ishi
> kerak**: injeksiya hold'ga 3 s kirgach boshlanadi, demak 3 + 8 = 11 ≤ 12
> ✓ (v1.3 aniqlashtirishi) |

va §4 ning cheklov izohi metrikaning **ma'nosini** ham belgilaydi:

> *"`W_stab_pilot = 8 s` bilan o'lchanadigan narsa — **"pressure davom
> etayotganda tasdiqlangan recovery"**, 60 s sustained recovery **emas**."*

Demak **matn jim emas:** oyna hold ichida bo'lishi **shart**, va agar
bo'lmasa, o'lchangan narsa §4 ning o'zi e'lon qilgan kattalik **emas**.
§16.8 ni "§4 jim" deb yozganim — matnni to'liq o'qimaganim.

**Ikkinchi xato, va u og'irroq:** §16.8 bu bo'shliqning bias'i
*"teskari yo'nalishda (yana H1 foydasiga)"* deb yozdi. **Ustun had
aksincha** — 17.3 ni ko'ring. §16.8 faqat ikkita holatdan **kam
ehtimollisini** hisobga olgan.

### 17.2 FAKT — arifmetika: oyna hold'ga faqat `t_start ≤ 0.8 s` bo'lsa sig'adi

Hamma qiymat muzlatilgan matndan. `t_h` = hold boshlanishi.

| qadam | manba | qiymat |
|---|---|---|
| injeksiya | §9.4 (*"injeksiya hold'ga 3 s kirgach"*) | `t_h + 3 s` |
| hold tugashi | §9.4 invariant 1 (`hold_s ≤ hold_cap_s`) | `t_h + 12 s` |
| oyna uzunligi | §4 (`W_stab_pilot`) | `8 s` |
| oyna **boshi** | §4, 1-band: `t_up` = *"oxirgi action'dan keyingi **birinchi contract'dan o'tgan probe**"* | `t_up`, **`t_inject` emas** |

Oyna hold ichida bo'lishi sharti:

```
t_up + 8 ≤ t_h + 12      ⇒   t_up ≤ t_h + 4
injeksiya t_h + 3 da      ⇒   t_up − t_inject ≤ 1 s
```

Arm `A` da restart'ni **systemd o'zi** qiladi (`Restart=on-failure`), demak
harness qaror kechikishi yo'q. `t_up − t_inject` budjeti:

```
RestartSec                 = 100 ms   (§9.3, arm A)
SUT start davomiyligi      = t_start  (MUZLATILMAGAN — §16.10)
probe kvantlashi           ≤ 100 ms   (§2: P = 100 ms; t_up — probe)
                           ────────────
0.1 + t_start + 0.1 ≤ 1    ⇒   t_start ≤ 0.8 s
```

Agar action `F_probe` ga gate qilinsa, `D_f = 300 ms` (§3: `k_f = 3`) ham
qo'shiladi ⇒ **`t_start ≤ 0.5 s`**.

> **FAKT: muzlatilgan dizayn SUT'dan `P2` pressure ostida ~0.8 s ichida
> ishga tushib contract'dan o'tishni TALAB qiladi.**

> **⚠️ v1.11 — bu arifmetika `hold_cap_s = 12 s` uchun.** §17.5 ning
> qarori **O3** bo'yicha `hold_cap_s` = **13 s**, demak umumiy shakl
> `t_start ≤ hold_cap_s − 11 − 0.2` ga ko'ra budjet **`t_start ≤ 1.8 s`**
> (gate qilingan variant: **`≤ 1.5 s`**, lekin u §9.3 ning ikki arm'iga
> **qo'llanmaydi** — Amendment log (1.3)). O'lchangan `max(t_start) =
> 1.4807 s` (78 urinish; `10-pressure-dozalash.md` §6.2, §10.1) ⇒
> **78/78 budjet ichida**, va pastdagi `0.8 s < t_start < 10 s` oralig'i
> `1.8 s < t_start < 10 s` ga aylanib unga **0/48** urinish tushadi
> (12 s da 7/48 edi). **Lekin nuqson YO'Q QILINMADI** — Amendment log
> (1.9): `D_probe` proxy bo'yicha `1/24` epizod hamon ruxsatdan oshadi.
> 17.5 ning qaroriga qarang.

**Va bu §9.2 ga to'g'ridan-to'g'ri qarshi.** §9.2 oldindan aytilgan
mexanizm **(i)** — *"`TimeoutStartSec` oshib ketdi"* — va **(iv)** —
*"scheduling delay'dan watchdog miss"* — ya'ni dizayn **sekin start'ni
kutadi**. `driver.py` esa `TimeoutStartSec = 10 s` ni default qilgan
(§16.10), ya'ni **12× oyna budjetidan katta** start'ga ruxsat beradi.

> **Dizayn o'zi oldindan aytgan hodisa — pressure ostida sekinlashgan
> start — o'zining o'lchov oynasini buzadi.** `0.8 s < t_start < 10 s`
> bo'lgan har qanday "muvaffaqiyatli" restart, verifikatsiya oynasi
> pressure'dan **chiqib ketgan** restart'dir.

**v1.3 ning yarashtiruvchi arifmetikasi `3 + 8 = 11 ≤ 12` oynani
`t_inject` dan boshlanadi deb hisoblaydi**, §4 ning 1-bandi esa uni
`t_up` dan boshlaydi. Ya'ni o'sha arifmetika **jimgina `t_up = t_inject`,
ya'ni nol recovery vaqtini** nazarda tutadi — aynan H1 **effekt kutmagan**
holat. v1.3 ziddiyatni to'g'ri hal qilgan, lekin `t_up ≠ t_inject` ekani
hisobga olinmagan.

### 17.3 TALQIN — uch holat, va ikki bias TESKARI yo'nalishda

| holat | shart (`T_h` = hold tugashi, `T_trial` = horizon) | hozirgi kodda | binar ta'siri |
|---|---|---|---|
| **(c)** oyna hold ichida | `t_up + 8 ≤ T_h` | `complete`, VR o'lchandi | **to'g'ri** |
| **(a)** oyna pressure'dan chiqadi, horizon ichida | `T_h < t_up + 8 ≤ T_trial` | `complete`, VR **hisoblanadi** | 2- va 5-bandlar **qisman pressure'siz** baholanadi ⇒ VR o'tishi **osonlashadi** ⇒ `P(VR|P2)` **oshadi** ⇒ trend **susayadi** ⇒ **H1 ga QARSHI** |
| **(b)** oyna horizon'dan chiqadi | `t_up + 8 > T_trial` | `complete`, **`VR = false`** | haqiqiy censoring kuzatilgan muvaffaqiyatsizlik deb yoziladi ⇒ `P(VR|P2)` **kamayadi** ⇒ trend **kuchayadi** ⇒ **H1 FOYDASIGA** |

**Ular bir-birini yo'qotmaydi** — bu turli trial'lar, va nisbiy
chastotasi `T_trial` ga (muzlatilmagan, §16.10(5)) va `t_start`
taqsimotiga (o'lchanmagan) bog'liq.

**Qaysi biri ustun — hisoblab ko'rsatiladi.** Shartnomaning default
`T_trial = 40.1 s` i va §9.4 jadvali bilan (baseline 10 s, ramp 5 s ⇒
`t_h = 15 s`, injeksiya 18 s, hold tugashi 27 s):

```
(a) uchun kerak:  t_start > 0.8 s
(b) uchun kerak:  t_up + 8 > 40.1  ⇒  t_up > 32.1  ⇒  t_start > ~14 s
```

> **Demak ustun had — (a), ya'ni bias ASOSAN H1 GA QARSHI.** (b) faqat
> ~14 s dan uzun start'larda yuzaga keladi; (a) esa ~0.8 s dan uzun har
> qanday start'da. §16.8 ning *"yana H1 foydasiga"* bahosi **xato edi**:
> u faqat (b) ni ko'rgan.

**Nega bu (a) ni "konservativ, demak xavfsiz" qilmaydi:** §11 ning
falsifikatsiya qoidasi — *"trend p > 0.05 **VA** Newcombe CI yuqori
chegarasi < 0.15"* — susaytirilgan trend ustida qo'llanadi, demak (a)
**soxta FALSIFIKATSIYA** yaratishi mumkin: H1 ning kuchli shakli
dunyodan emas, **o'lchov oynasining pressure'dan chiqib ketganidan**
yolg'onga chiqarilishi mumkin. Pre-registered falsifikatsiya mezoni
uchun bu soxta pozitiv bilan bir xil darajada og'ir.

### 17.4 QAROR — nimani hal qilaman (hech bir muzlatilgan qiymat siljimaydi)

1. **Oynasi hold ichida bo'lmagan trial §4 ning kattaligini
   O'LCHAMAGAN.** U `complete` + `VR = false` deb yozilMAYDI va binar
   `P(VR)` maxrajiga **muvaffaqiyatsizlik sifatida kiritilMAYDI.**
   Sabab: §4 oynaning hold ichida bo'lishini **talab qiladi**, demak
   oyna chiqib ketgan trial ta'rif shartini qanoatlantirmaydi —
   natija **kuzatilmagan**, `false` emas.
2. **Ikki yangi `disposition_source` qiymati** (§12 ning **yopiq
   enum'iga tegilMAYDI** — bular `disposition` qiymatlari emas):

   | `disposition_source` | ma'nosi |
   |---|---|
   | `window_past_pressure` | holat (a): `T_h < t_up + W_stab_pilot ≤ T_trial` |
   | `window_past_horizon` | holat (b): `t_up + W_stab_pilot > T_trial` |

   `disposition` ikkalasida ham **`censored`**, chunki §4 `censored` ni
   aynan *"kuzatmagan narsani natija deb yozmaymiz"* ma'nosida ishlatadi
   (§16.2(B) dagi asos). §16.2 ning qoidasi — birlamchi to'plam
   **`(disposition, disposition_source)`** jufti bilan aniqlanadi —
   o'zgarmagan holda shu ikki qiymatni ham qamrab oladi.
3. **Ikkalasi ham binar `P(VR)` maxrajidan chiqariladi** (natija
   kuzatilmagan) va §6.2 bo'yicha KM/log-rank va loop-rate ga
   **censored davomiylik** sifatida **kiradi**.
4. **Ularning darajasi `(arm × pressure)` yacheykasi bo'yicha ALOHIDA
   beriladi**, va §16.4 ning nomlash qoidasi qo'llanadi. **`P2`
   yacheykasida to'plangan yuqori daraja — o'zi NATIJA:** u
   *"dizayn qiziqtirgan yacheykani o'lchay olmadi"* degan ma'noni
   beradi, va §12 ning *"Yuqori eksklyuziya darajasi o'zi natija —
   yashirilmaydi"* qoidasi ostida **yashirilmaydi.**
5. **Oyna bo'sh-joy invarianti analizdan oldin tekshiriladi:** har
   `complete` trial uchun `t_up + W_stab_pilot ≤ T_h` **bajarilgan
   bo'lishi shart**. Bajarilmagan bo'lsa va trial `complete` deb
   yozilgan bo'lsa — bu **validator xatosi**, jimgina o'tkazilmaydi.

### 17.5 CHEKLOV — nimani HAL QILMAYMAN: bu dizayn nuqsoni, disposition bilan yopilmaydi

17.4 **bias'ning oldini oladi, nuqsonni tuzatmaydi.** Agar `P2` ostida
`t_start > 0.8 s` tipik bo'lsa, `P2` yacheykasining katta qismi
`censored` bo'ladi va **birlamchi endpoint aynan qiziqtirgan yacheykada
hisoblab bo'lmaydi.** Buni hech qanday disposition qoidasi tuzatmaydi.

**To'rt muzlatilgan qiymat birgalikda qanoatlantirilmaydi** (realistik
`t_start` da):

| # | qiymat | manba |
|---|---|---|
| 1 | `W_stab_pilot = 8 s` | §4 |
| 2 | `injection_offset = 3 s` | §9.4 |
| 3 | `hold_cap_s = 12 s` | §9.4 invariant 1 |
| 4 | oyna hold **ichida** bo'lishi sharti | §4 (*"ichida sig'ishi kerak"*) + §4 cheklov izohi (*"pressure davom etayotganda"*) |

> **✅ QABUL QILINDI (v1.11) — O3: `hold_cap_s` 12 s → 13 s.** Qarorni
> **orkestrator** qabul qildi, loyiha egasining **2026-10-03 dagi ochiq
> delegatsiyasi** bo'yicha. Asos, o'lchangan raqamlar, to'rt CHEKLOV va
> O1/O2/O4 ning rad etilish sabablari: **Amendment log, v1.10 → v1.11**,
> 1-band; qisqa shakli pastdagi *“QAROR (v1.11)”* bandida. **Qaror
> kalibratsiya ma'lumoti ko'rilgandan keyin qabul qilindi** — o'sha
> log'ning **0-bandi**.
>
> **Pastdagi jadval ATAYLAB saqlanadi** — o'quvchi nima rad etilganini va
> **nega** rad etilganini ko'rishi kerak.

| variant | nima o'zgaradi | narxi |
|---|---|---|
| **O1** | `W_stab_pilot` kichraytiriladi | VR da'vosini **kuchsizlashtiradi** — §4 ning 5-bandi (throughput) qisqa oynada kamroq ma'noga ega. Ma'lumot tomondan arzon: §4 ning sensitivity sweep'i (`W_stab ∈ {8,10,30,60,120}`) **xom trace'lardan post-hoc** hisoblanadi (§14.5(1)), demak tanlov "qaysi biri BIRLAMCHI" haqida, hisoblanish haqida emas |
| **O2** | `injection_offset` kichraytiriladi | 3 s hold boshidan keyin pressure'ning **barqarorlashuvi** uchun bor; kichraytirish *"o'rnatilgan pressure ostida injeksiya"* binosini kuchsizlashtiradi |
| **O3** | `hold_cap_s` 12 s dan oshiriladi | **yagona variant hech bir ilmiy da'voni kuchsizlashtirmaydigan.** 12 s ni yaratgan oomd xavfi bu host'da **yo'q** (§15.2). LEKIN: §15.3 uni **shartnomaviy** asosda saqlagan, va §9.4 invariant 2 (`hold + ramp_above_threshold ≤ guard_sustain_s = 15 s`) **qayta tekshirilishi** va guard **qayta kalibratsiya qilinishi** shart |
| **O4** | oyna pressure'dan chiqishiga ruxsat beriladi | §4 ning o'z cheklov izohiga (*"pressure davom etayotganda tasdiqlangan recovery"*) **qarshi** — bu raqam emas, **metrikaning ma'nosini** o'zgartiradi, demak eng og'ir variant |

**O1, O2, O4 — sof ta'rif o'zgarishi. O3 — ta'rif o'zgarishi + yangi
o'lchov (guard rekalibratsiyasi).** §15.3 ning shartnomaviy asosi va bu
yerdagi ilmiy asos **qarama-qarshi yo'nalishga** ko'rsatadi, demak bu
haqiqiy qaror nuqtasi, texnik tanlov emas.

#### Qaror uchun zarur, lekin MAVJUD BO'LMAGAN o'lchov

Nuqsonning kattaligi **`t_start` ga** bog'liq: `P0`, `P1`, `P2` ostida
SUT'ning start davomiyligi. **Bu o'lchov bajarilmadi** — bu agent
guest ichida hech narsa o'lchamadi (WSL ishi to'xtatilgan) va
pressure eksperimenti `00-pilot-topologiya.md` §6 ning 3-qadami
o'tmaguncha taqiqlangan.

> **So'rov:** `experiment/pressure-cal` yoki `experiment/guard-recal`
> har pressure bandida **SUT start davomiyligi taqsimotini** (`t_start`,
> `READY=1` ga qadar, `p50/p90/p99`) o'lchashi kerak. `p90(t_start) ≤ 0.8 s`
> bo'lsa — nuqson amalda bezarar va O1–O4 kerak emas. Aks holda loyiha
> egasi O1–O4 dan birini tanlashi **shart**, va bu tanlov **birinchi
> pilot trial'idan oldin** qilinishi kerak.

#### ✅ QAROR (v1.11) — O3 tanlandi: `hold_cap_s` 12 s → 13 s

**So'ralgan o'lchov BAJARILDI.** Yuqoridagi so'rov
(`experiment/pressure-cal` yoki `guard-recal` har pressure bandida
`t_start` taqsimotini bersin) `docs/architecture/10-pressure-dozalash.md`
§6 da bajarildi, **kalibrlangan** dozada (`base_mb = 184`; `08` ning
nazoratsiz to'yinish dozasi emas).

| band | n | **p90** | p99 | max | `≤ 0.8 s` (12 s) | `≤ 1.8 s` (13 s) |
|---|---|---|---|---|---|---|
| `P0` | 30 | **0.0481** | 0.0555 | 0.0576 | **30/30** | 30/30 |
| **`P1`** | 24 | **0.9543** | **1.3948** | **1.4807** | **19/24** | **24/24** |
| `P2` | 24 | **0.7863** | 1.1211 | 1.1883 | 22/24 | 24/24 |
| `P1 + P2` | 48 | **0.9105** | 1.3433 | 1.4807 | **41/48** | **48/48** |

- **Qochish bandi (`p90 ≤ 0.8 s`) QO'LLANMAYDI:** `P1` budjetni
  **19.3%** ga oshiradi (`P1` — §9.3 bo'yicha to'laqonli yacheyka),
  birlashtirilgan 48 namuna **13.8%** ga; `P2` ning 1.7% zaxirasi
  `10` §12.4 ga ko'ra **o'lchov shovqinidan kichik**. Demak qaror
  **majburiy** edi.
- **13 s da budjet `t_start ≤ 1.8 s`** (gate qilingan `≤ 1.5 s`
  **qo'llanmaydi**: §9.3 ning `A` va `no_action` arm'lari `F_probe` ga
  gate qilinmagan; probe'ga gate qilingan aktor — **arm C**, §13 uni
  muzlatmaydi). `P1` p99 **22%**, max **18%** zaxira bilan o'tadi,
  va **78/78** urinish ichida.
- **Nega 13, nega 12.5 emas:** 12.5 s da budjet 1.3 s va `P1` ning max'i
  **1.4807 s** undan oshadi ⇒ **13 s — ishlaydigan eng kichik yarim
  sekundli qadam**. Muzlatilgan qiymatga **minimal o'zgarish** —
  printsipial sabab.
- **Nega 15 emas** (`10` §6.5 uni ruxsat etilgan deb ko'rsatgan):
  `15 + 0.000 = 15 ≤ 15` — invariant 2 **tenglik bilan**
  qanoatlanadi, nol zaxira. 13 s **2.000 s** qoldiradi.
- **Invariant 2 buzilmaydi, O'LCHANGAN:** `ramp_above_threshold_s =
  0.000 s`, **29/29 epizod**, haqiqiy dozada (`10` §4.1) ⇒
  `13 + 0.000 = 13 ≤ 15`. **Guard qayta kalibratsiya qilinMAYDI** —
  `sustain_max_seconds = 15.0` o'zgarmaydi (`10` §4.2, §6.5), demak
  yuqoridagi O3 qatorining ikki sharti **bajarildi**.

**To'rt CHEKLOV, ochiq:** **(1)** 12 s ni yaratgan `systemd-oomd`
zaxirasi bu muhitda yo'q (§15.2), demak pilotning xavfsizlik argumenti
endi **faqat guard'ga** tayanadi, guard + oomd ga emas; **(2) arm C
`hold_cap_s = 13 s` ni meros qilib olmaydi** — gate qilingan budjetda
zaxira `P1` ning max'iga nisbatan **1.3%**, demak probe'ga gate qilingan
arm'ni pre-register qiladigan kishi §17.2 ning arifmetikasini **o'zi
uchun qaytadan bajarishi shart**; **(3) `hold_s = 13 s` li epizod hech
qachon ishga tushirilmagan** — `10` §4.2 ga ko'ra hatto 12 s li hold ham
sinalmagan (epizodlar ≤12 s ramp+hold bilan cheklangan), demak 13 s da
invariant 2 **arifmetika + o'lchangan ramp** ga tayanadi; **(4) nuqson
KAMAYDI, YO'Q BO'LMADI** — `D_probe` proxy bo'yicha ruxsatdan oshgan
epizod `5/24` dan `1/24` ga tushdi, demak **17.4(4) ning yacheyka
bo'yicha `window_past_pressure` hisoboti MAJBURIY bo'lib qoladi**.

Batafsil: **Amendment log, v1.10 → v1.11**, 0-band (post-data e'lon) va
1-band (1.1–1.11; 1.11 — §0 ning qamrov bandi).

### 17.6 Bias yo'nalishini ochiq e'lon qilish

17.4 ning qarori holat (a) ni va holat (b) ni **ikkalasini** binar
maxrajdan chiqaradi. Ularning bias'lari teskari bo'lgani uchun, bu
qarorning sof yo'nalishi **oldindan aniq emas** — u `t_start`
taqsimotiga bog'liq, va u o'lchanmagan.

Aniq aytilishi mumkin bo'lgan narsa:

- Hozirgi kodga nisbatan, 17.4 **(a) ni olib tashlaydi**, ya'ni
  H1 ga qarshi ustun bias'ni olib tashlaydi ⇒ **sof ta'sir H1
  foydasiga**;
- va u **(b) ni ham** olib tashlaydi, ya'ni H1 foydasiga bo'lgan
  kichikroq bias'ni ham olib tashlaydi ⇒ bu qism **H1 ga qarshi**.
- Ustun had (a) bo'lgani uchun (17.3 hisobi), **17.4 ning sof natijasi
  ehtimol H1 FOYDASIGA.**

**Buni bilib turib qabul qilaman**, chunki alternativa — kuzatilmagan
natijani kuzatilgan deb yozish, va u **ikki yo'nalishda ham** noto'g'ri.
Qaror hech qanday ma'lumot mavjud bo'lmaganda qabul qilinadi, demak
natijani ko'rib tanlash imkoniyati yo'q. **Agar `t_start` o'lchangandan
keyin ma'lum bo'lsa-ki (b) ustun, bu qaror O'ZGARMAYDI** — u
o'lchangan natija emas, ta'rif asosida qabul qilingan.

> **⚠️ v1.11 — bu banddagi *“hech qanday ma'lumot mavjud bo'lmaganda”*
> kafolati FAQAT 17.4 NING QARORIGA tegishli.** U **17.5 ning O3
> tanloviga QO'LLANMAYDI**: O3 `10-pressure-dozalash.md` ning
> kalibratsiya o'lchovlari **ko'rilgandan keyin** tanlandi — Amendment
> log, v1.10 → v1.11, **0-band**. 17.4 ning qarori (holat (a) va (b) ni
> binar maxrajdan chiqarish) va uning yuqoridagi bias bahosi
> **o'zgarmadi**, va u hamon `t_start` o'lchanmagan paytda qabul
> qilingan qaror bo'lib qoladi.

### 17.7 DIZAYN NUQSONI — §8.2 ning (ii) nazorati §9.3 panjarasida yo'q

v1.5 §16.9 buni "ochiq savol" deb qayd etgan edi. **Aniqroq aytilishi
kerak: bu dizayn nuqsoni.**

§8.2: *"**No-action arm MAJBURIY**, opsional emas: (i) injeksiya +
`Restart=no`, (ii) injeksiya yo'q — har pressure darajasida. Busiz
'restart PSI ni oshirdi' ni 'fault PSI ni oshirdi' dan ajratib
bo'lmaydi va `harm_indicator` talqin qilinmaydi."*

§9.3: arm'lar `A` va `no_action`; `3 × 2 × 20 = 120`.

→ **(ii) "injeksiya yo'q, pressure bor" §9.3 ning panjarasida YO'Q.**
`docs/research/05-metodologiya.md` §4 uni alohida nazorat qatori
sifatida sanaydi.

**Oqibati, §8.2 ning o'z so'zlari bilan:** (ii) bo'lmasa
*"pressure'ning o'zi baseline"* i yo'q, demak fault'ning PSI hissasini
pressure'ning PSI hissasidan ajratish **to'liq identifikatsiya
qilinmaydi**. §8.2 bu nazoratni **majburiy** deb ataydi, demak uning
yo'qligi **dizaynning e'lon qilingan talabini bajarmasligi.**

**Hal qilinMAYDI:** har qanday yechim §9.3 ning muzlatilgan trial
soniga (120) va blok strukturasiga tegadi (§8.4: blok = har
`(arm × pressure)` yacheykadan **aynan bitta** trial). Uchinchi arm
qo'shilsa `3 × 3 × 20 = 180` bo'ladi. **Bu loyiha egasining qarori.**
P1 ni bloklaydimi — §8.2 ning *"`harm_indicator` talqin
qilinmaydi"* bandi FR-B ga tegishli, va FR-B P1 da hisoblanmaydi
(§14.7), demak **P1 ni bloklamaydi**; lekin PSI atributsiya da'vosi
(ii) siz **chala** bo'ladi va maqolada shunday yozilishi kerak.

### 17.8 OCHIQ MASALA — §14.4 ning "§7 tirik unit sharti" havolasi

v1.4 §15.6(2) dan beri ochiq, uchinchi amendment bo'ylab hal
qilinmagan. §14.4 ning `run_meta` qatori *"§7 tirik unit shartini
ko'ring"* deydi; §7 — *Pressure o'lchovi* va unda bunday shart yo'q.
Haqiqiy talab `docs/architecture/01-muhit-tekshiruvlari.md` §4 da, va
`04-driver-va-analiz-shartnomasi.md` §1.1 unga **to'g'ri** havola
qiladi.

> **Tavsiya:** 17.5 ning O1–O4 qarori muzlatilgan matnga **baribir
> tegadi.** Shu amendment — bu havolani tuzatish uchun **to'g'ri joy**,
> chunki u mustaqil holda muzlatilgan hujjatni ochishga arzimaydi.
> Talabning o'zi to'liq kuchda: `units_show` unit **tirik** paytida
> olinadi.

### 17.9 NIMA O'ZGARMAYDI

`W_stab_pilot = 8 s`, `W_stab = 60 s`, `injection_offset = 3 s`,
`hold_cap_s = 12 s`, `guard_sustain_s = 15 s`, `θ = 0.8`,
`T_conn`/`T_rt` = 50 ms, `P` = 100 ms, `k_f` = 3, `ε` = 32 MiB,
quiescence 0.05, `T_q` = 5 s, `T_w` = 15 s, `T_w_max` = 120 s,
arm'lar `A`/`no_action`, `P0`/`P1`/`P2`, 20 blok / 120 trial,
§10.1 ning Cochran–Armitage testi, §10.2 ning KM/log-rank/RMST
(`τ = 8 s`, Cox/HR taqiqi), §10.4 ning Holm oilasi, §11 ning
falsifikatsiya qoidasi va power bayonoti, §12 ning **yopiq enum'i** va
*"aynan bitta disposition"* qoidasi, §14 data schema, §16 ning
qarorlari — **hammasi o'zgarmadi.** §13 ga tegilmadi.

Qo'shilgan narsa: ikki `disposition_source` qiymati (bular
`disposition` qiymatlari **emas**), bir validator sharti, bir hisobot
qoidasi, va **hal qilinmagan qaror'ning ochiq bayonoti.**

### 17.10 NATIJA — yo'q

**Hech qanday eksperiment ishga tushirilmadi. Hech qanday natija yo'q.**
Bu bo'limdagi hech bir qaror kuzatilgan natijani ko'rgandan keyin qabul
qilinmagan. 17.2 ning arifmetikasi **muzlatilgan qiymatlardan**
olingan, o'lchovdan emas; `t_start` **o'lchanmadi** va uni o'lchash
17.5 da so'ralgan.

---

## 18. §11 ning fail-slow limbi — referens aniqlangan, limb ishlamaydi (muzlatilgan)

> Bu bo'lim **v1.7 amendment** bilan qo'shildi. U **hech bir operatsion
> ta'rifni, metrikani, chegarani, statistik testni yoki falsifikatsiya
> mezonini o'zgartirmaydi.** U ikki narsani qiladi: (1) §11 ning
> fail-slow limbidagi aytilmagan referens kattalikni **muzlatilgan
> matnning o'z konvensiyasidan** aniqlaydi, (2) o'sha referens bilan
> limb **hisoblanadigan, lekin ishlamaydigan** bo'lib qolishini
> ko'rsatadi — va buni hal qilish uchun **loyiha egasiga qaror
> qoldiradi.**

### 18.1 FAKT — matn nimani aytadi va nimani aytmaydi

§11, so'zma-so'z:

> *"Bir vaqtda, fail-slow shakli qo'llab-quvvatlanmaydi, agar `P0` va `P2`
> orasidagi time-to-VR RMST farqi (τ = 8 s) uchun 95% CI **20% oshishni**
> chiqarib tashlasa."*

Aytilmagan uch narsa, va uchalasi ham limbni hisoblanmaydigan qiladi:

| # | aytilmagan | nega kerak |
|---|---|---|
| 1 | **20% — NIMANING 20% i** | nisbiy chegara baza talab qiladi |
| 2 | **ayirish tartibi** | `RMST(P2) − RMST(P0)` yoki teskarisi; "oshish" musbat kattalik |
| 3 | **"chiqarib tashlasa" qaysi yo'nalishda** | CI chegaradan pastda bo'lsa — effekt inkor qilinadi; yuqorida bo'lsa — tasdiqlanadi |

Taqqoslash uchun: **kuchli shakl limbi to'liq aniqlangan** —
*"`P(VR|P0) − P(VR|P2)` uchun 95% Newcombe CI ning **yuqori chegarasi
< 0.15**"*. Ya'ni §11 ning ikki limbidan faqat fail-slow limbi
hisoblanmaydi.

> **§17 ning argumenti shu yerga ham qo'llanadi: hisoblab bo'lmaydigan
> pre-registered qoida hech narsani falsifikatsiya qilmaydi.**

### 18.2 QAROR — referens muzlatilgan matnning O'Z konvensiyasidan aniqlanadi

Referens **`RMST(P0)`**. Bu ixtiro emas, uchta mustaqil matn asosi bor:

1. **§11 ning o'zi, davom etish mezoni (b):** *"`D_eff` `P2` da **≥1.5×
   `P0`**, bootstrap CI **1.0 ni** chiqarib tashlaydi."* Ya'ni §11
   pressure effektini **`P0` ga nisbatan karrali** shaklda ifodalaydi va
   CI ni **null nisbatga** qarshi tekshiradi. Bu §11 ning o'z grammatikasi,
   va fail-slow limbi xuddi shu grammatikada yozilgan ("20% oshish").
2. **§10.2:** *"**Effect measure: RMST difference** τ horizon'ga qadar —
   … to'g'ridan-to'g'ri **"τ sekund ichida tejalgan kutilgan downtime"**
   sifatida o'qiladi."* Demak RMST farqi — **downtime farqi**, va
   downtime'dagi "20% oshish" ning bazasi solishtirma darajaning
   downtime'i, ya'ni `RMST(P0)`.
3. **`P0` — dizaynning solishtirma darajasi** (§9.3: `P0` = generator
   idle). Boshqa hech bir daraja baza bo'lishga da'vo qilmaydi.

Qolgan nomzodlar matn bilan qo'llab-quvvatlanmaydi: `τ` ning 20% i —
"oshish" ni **horizon ulushiga** aylantiradi, bu boshqa bayonot;
`P0` ning **o'rtacha** time-to-VR si — §10.2 *"`mean ± SD` BERILMAYDI"*
deb taqiqlaydi; RMST **farqining** 20% i — sirkulyar.

**Ayirish tartibi va yo'nalish**, §11 ning kuchli shakl limbini oynadek
aks ettirib (*"yuqori chegarasi < 0.15"*):

```
Δ(P2,P0) := RMST_A(P2, τ=8 s) − RMST_A(P0, τ=8 s)    # pressure ostida downtime OSHISHI
thr      := 0.20 × RMST_A(P0, τ=8 s)

fail-slow shakli QO'LLAB-QUVVATLANMAYDI  ⟺  CI95_upper[ Δ(P2,P0) ] < thr
```

`_A` — §16.5 bo'yicha **arm `A` ichida**. Fail-slow ostida pressure
recovery'ni sekinlashtiradi, demak `RMST(P2) > RMST(P0)` va `Δ > 0`;
shuning uchun **baholanadigan kattalik `P2 − P0`**, teskarisi emas.

> **Sxema talabi:** `survival.rmst.pressure_difference` ning
> `contrast: "P0-P2"` yorlig'i **ayirish tartibini aytmaydi** — u faqat
> juftlikni nomlaydi. Falsifikatsiya mezonidagi aytilmagan ishora —
> qoidani hisoblanmaydigan qiladigan yana bir yo'l. Sxema ayirish
> tartibini **ochiq** ko'rsatishi shart (masalan
> `orientation: "P2_minus_P0"`).

> **⚠️ v1.11 — 18.2 ning REFERENSI BEKOR QILINDI.** §18.6 ning qarori
> **F2** bo'yicha referens `RMST(P0)` **emas**, balki **`τ`**:
> `thr = 0.20 × τ = 1.6 s`, **fiksa** (§11 ning yangilangan bandi).
> 18.2 ning **uch matn asosi rad etilmaydi** — ular matnga sodiqlik
> uchun hamon kuchli, va F2 ularga **qarshi** tanlandi, chunki
> 18.4/18.6 ning kvantlash cheklovi **o'lchov bilan tasdiqlandi**:
> F1 ning **inkor shoxi** asbobning kvantlash polidan **past**.
> **Ayirish tartibi, yo'nalish talabi va `orientation` sxema talabi
> O'ZGARMADI.** Sabab, bias yo'nalishi, narx, va **qaror ma'lumot
> ko'rilgandan keyin qabul qilingani**: **Amendment log,
> v1.10 → v1.11**, 0- va 2-bandlar; §18.6, §18.7.

### 18.3 FAKT — bu yerda RMST nima, va nega `τ = 8 s` degenerat emas

`time-to-VR` ning survival endpoint'i uchun RMST:

```
RMST(τ) = ∫₀^τ S(t) dt ,   S(t) = P(hali VR ga erishilmagan, t da)
        = τ gacha VR ga erishilmagan holatda o'tkazilgan kutilgan vaqt
        = τ horizonidagi KUTILGAN DOWNTIME
```

Bu §10.2 ning o'z o'qishi bilan **aynan bir xil**: *"τ sekund ichida
tejalgan kutilgan downtime"*. Demak `RMST ∈ [0, τ] = [0, 8 s]` va u
**downtime kattaligi**, recovery tezligi emas.

**Muhim: `time-to-VR` hodisa vaqti `t_up` da, oyna oxirida EMAS.**
Aks holda VR `W_stab_pilot = 8 s` oynasini talab qilgani uchun
`time-to-VR ≥ 8 s` bo'lardi, demak `τ = 8 s` da `RMST ≡ 8 s` **har bir
guruhda**, farq **ayni nolga teng** va limb **ayni degenerat** bo'lardi.

Matn `t_up` anchor'ini qo'llab-quvvatlaydi: **§6.1** `D_probe` (asosiy
downtime o'lchovi) ni *"failure'dan oldingi oxirgi o'tgan probe → VR
shartini qanoatlantiruvchi oynaning **birinchi probe'i**"* deb ta'riflaydi
— ya'ni oyna **boshida** tugaydi, oxirida emas. Va **§6.3**
*"'Verification latency' achievement metrikasi sifatida BERILMAYDI —
muvaffaqiyatli VR uchun u ta'rifan `W_stab`ga teng"* deb aynan oyna
uzunligini metrikadan chiqaradi.

### 18.4 CHEKLOV — chegaraning kattaligi kvantlash polida

`thr = 0.20 × RMST(P0)` ning qiymati `RMST(P0)` ga bog'liq. Uni
**muzlatilgan qiymatlardan** chiqaraman (o'lchov emas; yagona
noma'lum — `t_start`, u **o'lchanmagan**).

`P0` ostida (`clean_crash`, `Restart=on-failure`, arm `A`),
`D_probe` ning tarkibi:

| had | manba | qiymat |
|---|---|---|
| oxirgi o'tgan probe → haqiqiy failure | §2 (`P = 100 ms`) | ≤ 100 ms |
| systemd crash'ni ko'rishi (`SIGCHLD`) | §3 (`L_det_sd` manfiy ham bo'lishi mumkin) | ≈ 0 |
| `RestartSec` | §9.3, arm `A` | 100 ms |
| SUT start davomiyligi | **MUZLATILMAGAN** (§16.10(1–2)) | `t_start` — **o'lchanmagan** |
| `READY=1` → `t_up` (birinchi o'tgan probe) | §2, §4 1-band | ≤ 100 ms |

```
D_probe(P0) = t_start + (0.2 … 0.4) s        # qavs ichi — sof muzlatilgan overhead
§9.2: P(VR | P0, restart) ≈ 1.0  va  D_probe(P0) << 8 s
  ⇒  RMST(P0) ≈ E[D_probe(P0)]

t_start = 0.1 s  ⇒  RMST(P0) ≈ 0.4 s  ⇒  thr ≈ 80 ms
t_start = 0.8 s  ⇒  RMST(P0) ≈ 1.1 s  ⇒  thr ≈ 220 ms      (0.8 s — §17.2 ning dizayn shifti)
```

> **thr ≈ 0.8 … 2.2 probe davri.** Va §6.1 `D_probe` ning o'zi
> *"±P kvantlash, har chekkada +P/2 bias"* bilan keladi, §7 esa
> *"100 ms delta oniy tezlik deb talqin qilinmaydi"* deb ogohlantiradi.
> Ya'ni **chegara o'lchov asbobining kvantlash polida.**

Taqqoslash: `0.20 × τ = 1.6 s` = **16 probe davri.**

#### Qaysi rejim qat'iy, qaysi rejim ahamiyatsiz

| rejim | `RMST(P0)` | `thr` | fail-slow'ni INKOR qilish | fail-slow'ni QO'LLAB-QUVVATLASH |
|---|---|---|---|---|
| **`P0` tez tuzaladi** (§9.2 bu rejimni **aytadi**) | ≈ 0.4–1.1 s | ≈ 80–220 ms | `CI_upper[Δ] <` kvantlash poli kerak ⇒ **ERISHIB BO'LMAYDI** | har qanday kichik effekt chegaradan oshadi ⇒ **DEYARLI AVTOMATIK** |
| `P0` ham 8 s ichida tuzalmaydi | → 8 s | → 1.6 s | erishiladigan | qat'iy |

> **Bitta muzlatilgan jumla — dizayn o'zi AYTGAN rejimda shtamp, va faqat
> dizayn o'zi BO'LMAYDI deb aytgan rejimda haqiqiy test.** Ikkinchi
> rejim §9.2 ning *"Tinch holatda `P(VR | clean_crash, restart) ≈ 1.0`"*
> bayonotiga qarshi, va u yuzaga kelsa `P0` yacheykasining o'zi
> degenerat bo'ladi (pasayish uchun joy yo'q — §8.1 ning ceiling
> argumenti teskari tomonga).

### 18.5 CHEKLOV — nisbiy chegara muzlatilgan effect measure bilan statistik jihatdan mos kelmaydi

`thr = 0.20 × RMST(P0)` — **baholangan** kattalik, konstanta emas.
`CI95[Δ]` ni **xuddi shu ma'lumotdan** baholangan chegaraga qarshi
taqqoslash **95% qoplamaga ega emas**: `RMST(P0)` ning noaniqligi
ikki marta — `Δ` da va `thr` da — ishtirok etadi va korrelyatsiyalangan.

Statistik jihatdan to'g'ri shakl — **nisbat** ustida:

```
ρ := RMST_A(P2, τ) / RMST_A(P0, τ)
fail-slow QO'LLAB-QUVVATLANMAYDI  ⟺  CI95_upper[ ρ ] < 1.20
```

Lekin **§10.2 effect measure sifatida ayni "RMST difference" ni
muzlatadi** (*"Effect measure: RMST difference"*), nisbatni emas. Demak:

> **Nisbiy chegara (`20%`) va muzlatilgan absolut effect measure
> (`difference`) bir-biriga mos kelmaydi.** Nisbat CI si §10.2 ning
> muzlatilgan effect measure'i **emas**; difference CI si esa nisbiy
> chegara bilan to'g'ri taqqoslanmaydi. Bu **uchinchi** mustaqil sabab,
> nega limb hozirgi holatda hisoblanmaydi.

Yumshatish (ta'rif o'zgarishi EMAS): `Δ` va `thr` ning birgalikdagi
noaniqligini **bootstrap** bilan ushlash mumkin — har resample'da
`Δ*` va `thr* = 0.20 × RMST*(P0)` qayta hisoblanadi va
`Pr[Δ* ≥ thr*]` baholanadi. §10.2 bootstrap'ni allaqachon ruxsat
etadi (*"median, p90, p99 + BCa bootstrap CI"*, §10.3 *"`scipy`
… bootstrap'ni qoplaydi"*). **Bu hisoblash yo'li, qaror emas** —
u 18.4 ning kvantlash polini **hal qilmaydi**.

> **✅ v1.11 — 18.5 NING IKKI E'TIROZI HAM YO'Q BO'LDI.** §18.6 ning
> qarori **F2** bo'yicha `thr = 0.20 × τ = 1.6 s` — **muzlatilgan
> qiymatdan olingan KONSTANTA**. Demak: **(a)** `thr` **baholanmaydi**,
> ya'ni `Δ` va `thr` ning **birgalikdagi noaniqligi** muammosi
> **umuman tug'ilmaydi** va yuqoridagi qoplama e'tirozi **kuchini
> yo'qotadi**; **(b)** chegara **sekundda absolut**, demak §10.2 ning
> muzlatilgan *"RMST **difference**"* effect measure'i bilan **mos
> keladi** — nisbat (`ρ`) ga o'tish **kerak emas**.
>
> **Oqibati amaliy va muhim:** yuqoridagi bootstrap yumshatishi
> **shart emas** — taqqoslash **analitik** interval bilan bajariladi
> (Greenwood variansi + normal interval,
> `revix/stats.py:rmst_difference`). Bu muhim, chunki
> `revix/stats.py:bootstrap_ci` o'zi *"**CENSORED ma'lumot uchun
> YARAMAYDI.** Censoring bor joyda KM/RMST"* deb yozadi, §6.2 esa
> censored trial'larni **tashlashni taqiqlaydi** — ya'ni **F1 ostida
> buyurilgan usul va mavjud usul ZIDDIYATDA edi**. **§10.2 ning o'z
> bootstrap talabi (kichik `n` da robustlik) o'zgarmaydi.**
> Amendment log, v1.10 → v1.11, **(2.6)**.

### 18.6 HAL QILMAYDIGAN QAROR — limb ishlamaydi, bu egasining tanlovi

18.2 referensni aniqladi, demak limb **hisoblanadigan** bo'ldi. Lekin
18.4 ko'rsatadi: **§9.2 ning o'zi aytgan rejimda limb fail-slow'ni
INKOR QILA OLMAYDI**, chunki inkor shoxi o'lchov kvantlashidan
mayda farqni ko'rsatishni talab qiladi.

> **Buni 18.2 ning referensini o'zgartirmasdan tuzatib bo'lmaydi, va
> referensni o'zgartirish §11 ning MA'NOSINI o'zgartiradi.**
>
> **✅ QABUL QILINDI (v1.11) — F2: `thr = 0.20 × τ = 1.6 s`, fiksa.**
> Qarorni **orkestrator** qabul qildi, loyiha egasining **2026-10-03 dagi
> ochiq delegatsiyasi** bo'yicha, va **§17.5 ning O3 qarori bilan
> BIRGALIKDA**. Asos, o'lchangan raqamlar, **bias yo'nalishi** va narxi:
> **Amendment log, v1.10 → v1.11**, 2-band; qisqa shakli pastdagi
> *“QAROR (v1.11)”* bandida, bias esa §18.7 da. **Qaror kalibratsiya
> ma'lumoti ko'rilgandan keyin qabul qilindi** — o'sha log'ning
> **0-bandi**.
>
> **Pastdagi jadval ATAYLAB saqlanadi** — o'quvchi nima rad etilganini va
> **nega** rad etilganini ko'rishi kerak.

| variant | nima bo'ladi | narxi | bias yo'nalishi |
|---|---|---|---|
| **F1** | 18.2 ni o'z holida qoldirish (`thr = 0.20 × RMST(P0)`) | matnning o'z konvensiyasiga **eng sodiq**; lekin inkor shoxi erishib bo'lmaydigan ⇒ limb amalda **bir tomonlama** | **fail-slow / H1 FOYDASIGA** — limb uni deyarli hech qachon inkor qilmaydi |
| **F2** | referens `τ` (`thr = 0.20 × 8 s = 1.6 s`, fiksa) | o'lchanadigan, rejimdan mustaqil, kvantlashdan 16× yuqori; lekin §11 ning *"×P0"* konvensiyasiga **qarshi**, va "20% oshish" **"horizonning 20% i"** ga aylanadi — boshqa bayonot | **H1 GA QARSHI** — sub-sekundli bazada 1.6 s qo'llab-quvvatlash shoxini qat'iy, inkor shoxini oson qiladi |
| **F3** | referens `P0` ning **medianasi** (§10.2 medianani ruxsat etadi) | 18.4 ning kvantlash muammosi **o'zgarmaydi**; qo'shimcha: KM medianasi `nan` bo'lishi mumkin (`04-driver-va-analiz-shartnomasi.md` §2.3, 8-band) | F1 bilan bir xil |
| **F4** | nisbiy chegarani **absolut** chegara bilan almashtirish (sekundda, masalan `k × P`) | `k` ni tanlash **o'lchov talab qiladi** (`t_start` va `D_probe` taqsimoti) ⇒ v1.3 ning *"ma'lumot bilan asoslangan amendment, taxmin bilan emas"* qoidasi ostida — **hozir qilib bo'lmaydi** | o'lchovdan oldin aniq emas |

**F1 va F2 teskari yo'nalishga bias beradi.** Bu — tanlov texnik emas,
**ilmiy** ekanining belgisi, va §17.5 dagi O1–O4 bilan bir xil turdagi
qaror. Ikkalasini **bir vaqtda** hal qilish tabiiy, chunki ikkalasi ham
`τ = 8 s` / `W_stab_pilot = 8 s` ga bog'langan.

> **Bog'liqlik, ochiq yoziladi:** §17.5 ning O1 varianti
> (`W_stab_pilot` ni kichraytirish) `τ` ni ham o'zgartirishi mumkin
> (§10.2/§11 da `τ = 8 s` — `W_stab_pilot` bilan bir xil raqam), va
> `τ` o'zgarsa F2 ning chegarasi ham o'zgaradi. **§17.5 va §18.6 ni
> alohida hal qilish ziddiyat yaratishi mumkin.**

#### Qaror uchun zarur, lekin MAVJUD BO'LMAGAN o'lchov

`thr` ning haqiqiy kattaligi `RMST(P0)` ga, u esa `t_start` ga
bog'liq. **Bu o'lchov bajarilmadi** — bu agent guest ichida hech
narsa o'lchamadi (WSL ishi to'xtatilgan).

> **So'rov:** `experiment/guard-recal` `t_start` ni o'lchaganda
> (§17.5 so'rovi), **`P0` ostidagi `D_probe` taqsimotini ham**
> (`p50/p90/p99`) bersin. `RMST(P0)` shundan baholanadi, va
> `thr = 0.20 × RMST(P0)` ning `P = 100 ms` ga nisbati 18.4 ning
> xulosasini **tasdiqlaydi yoki rad etadi**. Agar
> `thr ≥ ~5 × P` bo'lsa, 18.4 ning cheklovi amalda bezarar va F1
> yetarli; aks holda egasi F1–F4 dan birini tanlashi **shart**.

#### ✅ QAROR (v1.11) — F2 tanlandi: `thr = 0.20 × τ = 1.6 s`, fiksa

**So'ralgan o'lchov BAJARILDI** (`docs/architecture/10-pressure-dozalash.md`
§7, kalibrlangan dozada), va **qochish bandi (`thr ≥ ~5 × P = 0.5 s`)
QO'LLANMAYDI** — uch mustaqil yo'lda:

| yo'l | manba | `thr` | `P` birligida | `≥ 5P`? |
|---|---|---|---|---|
| **O'LCHANGAN** | `10` §7.2/§7.5: `D_probe(P0)` proxy, n=12, **hammasi aynan 0.300 s** ⇒ `0.20 × 0.3000` | **0.0600 s** | **0.60 × P** | ❌ (5P dan **8.3×** past) |
| **CHIQARILGAN** | §18.4 ning muzlatilgan-overhead yo'li; o'lchangan `p50(t_start\|P0) = 0.0386 s` ⇒ `0.20 × (0.2386 .. 0.4386)` | **0.048 .. 0.088 s**, o'rtasi ≈ **0.068 s** | ≈ 0.68 × P | ❌ |
| **O'LCHANGAN, boshqa bandlar** | `10` §7.5: `P1` mean 0.8500 s / `P2` mean 1.0250 s | **0.170 s** / **0.205 s** | 1.70 / 2.05 × P | ❌ (eng katta — `p90(P2)` da **3.10 × P**) |

Ya'ni xulosa **bandga bog'liq emas** va **`P0` bandining artefakti emas**.
**Har bir raqam o'lchangan yoki chiqarilgan deb belgilangan.**

- **F1 yetarli emas:** uning **inkor** shoxi §6.1 ning `±P` kvantlashi va
  §7 ning *“100 ms delta oniy tezlik deb talqin qilinmaydi”*
  ogohligining **ostida** qoladi. **Inkor shoxiga erishib bo'lmaydigan
  pre-registered falsifikatsiya mezoni — test emas.** Bu F1 ga qarshi
  **hal qiluvchi** dalil.
- **F3 dominatsiya qilingan:** o'lchangan `P0` taqsimoti **degenerat**
  (12/12 epizod aynan `0.300 s` ⇒ `median = mean`), demak kvantlash
  muammosi **o'zgarmaydi** (umuman mediana o'rtachadan kichik ⇒ chegara
  yana **kichrayadi**), ustiga §18.6 ning sanagan **`nan`** nuqsoni.
- **F4 uchun `k` ga ankor yo'q; F2 — aynan F4, lekin printsipial `k`
  bilan:** matnning **o'z `0.20`** koeffitsienti saqlanadi va
  **muzlatilgan** `τ = 8 s` ga ankorlanadi ⇒ `thr = 1.6 s = 16 × P`,
  kvantlashdan **16× yuqori**.
- **F2 da ikkala shox ham erishiladigan:** `10` §7.2 ning `D_probe`
  proxy **o'rtachalari** farqi `P2 − P0 = 1.0250 − 0.3000 =` **0.7250 s**
  — F1 ning chegarasidan ≈**12× katta**, F2 ning chegarasidan esa
  ≈**0.45×**, ya'ni kichik. **⚠️ Bu raqam ILLYUSTRATIV, da'vo emas:**
  u `RMST` **emas** (`D_probe` proxy'i; `10` §7.5 ning CHEKLOV'i),
  `n = 12`, va **hech qanday CI hisoblanmagan** — mezon esa
  `CI95_upper` ga tayanadi.
- **§18.5 NING IKKI E'TIROZI YO'Q BO'LADI** (kvantlash dalilidan
  **mustaqil**): F2 da `thr` — **muzlatilgan qiymatdan olingan
  konstanta**, demak **(a)** `Δ` va `thr` ning **birgalikdagi
  noaniqligi** muammosi **tug'ilmaydi** (18.5 ning qoplama e'tirozi), va
  **(b)** chegara **sekundda absolut** bo'lgani uchun §10.2 ning
  muzlatilgan *"RMST **difference**"* effect measure'i bilan
  **mos keladi**. Oqibati amaliy: taqqoslash **analitik** interval bilan
  bajariladi (Greenwood variansi + normal interval,
  `revix/stats.py:rmst_difference`), 18.5 ning bootstrap yo'li bilan
  **emas** — va bu muhim, chunki `revix/stats.py:bootstrap_ci` o'zi
  *"CENSORED ma'lumot uchun YARAMAYDI"* deb yozadi, §6.2 esa censored
  trial'larni tashlashni **taqiqlaydi**. §10.2 ning o'z bootstrap
  talabi (kichik `n` da robustlik uchun) **o'zgarmaydi**.
- **Qo'shimcha foyda:** `thr = 0.20 × τ` **endpoint tanlovidan
  mustaqil**, demak §18.8 ning ochiq masalasi **chegaraga** ta'sir
  qilmaydi (§21.4 F1 ostida uchala nomzod ham `thr ≈ 0.1 s` berishini
  ko'rsatgan edi). §18.8 **o'z sabablari bilan ochiq qoladi**.
- **§17.5 bilan izchil:** O3 `W_stab_pilot` ni ham, `τ` ni ham
  **tegmasdan** qoldiradi, demak yuqoridagi *“Bog'liqlik”* ogohligi
  (O1 ⇒ `τ` siljiydi ⇒ F2 ning chegarasi siljiydi) **yuzaga
  kelmaydi**. Juftlik `(O3, F2)` **ichki izchil**, va bu ularni
  **birgalikda** tanlashning sabablaridan biri.
- **NARXI:** F2 *“20% oshish”* ning **bazasini** `P0` ning
  downtime'idan **horizonga** ko'chiradi — yuqoridagi jadvalning o'z
  so'zi bilan *“boshqa bayonot”*, va §11 ning *“×P0”*
  grammatikasiga qarshi.
- **🔴 BIAS: F2 ANTI-KONSERVATIV** — 18.7 ning v1.11 bandiga qarang,
  u **yumshatilmaydi**.
- **🔴 POST-DATA:** bu tanlov **kalibratsiya o'lchovlari ko'rilgandan
  keyin** qilindi, va yuqoridagi `0.7250 s` ko'rsatadi-ki ikki
  konvensiya o'sha farqning **qarama-qarshi tomonlarida** turadi —
  Amendment log, v1.10 → v1.11, **0-band**.

Batafsil: **Amendment log, v1.10 → v1.11**, 0-band va 2-band (2.1–2.10).

### 18.7 Bias yo'nalishini ochiq e'lon qilish

**18.2 ning qarori (referens = `RMST(P0)`) fail-slow / H1 FOYDASIGA
ishlaydi**, chunki u limbning inkor shoxini erishib bo'lmaydigan
qiladi (18.4). Ya'ni bu qaror H1 ning fail-slow shaklini
falsifikatsiyadan **amalda himoya qiladi**.

**Buni bilib turib qabul qilaman**, chunki:

1. referens **matnning o'z konvensiyasidan** kelib chiqadi (§11(b) ning
   *"×P0"* grammatikasi, §10.2 ning downtime o'qishi), demak u
   **tanlanmagan** — **o'qilgan**;
2. menga qulay bo'lgan variant **F2** bo'lardi (u limbni ishlaydigan
   qiladi va H1 ga qarshi bias beradi, ya'ni "qattiqqo'l" ko'rinardi) —
   lekin F2 matn bilan **qo'llab-quvvatlanmaydi**, va natijani
   yaxshi ko'rsatish uchun matnni qayta o'qish aynan bu hujjat oldini
   olish uchun yozilgan narsa;
3. hech qanday ma'lumot mavjud emas, demak bu qarorni natijani ko'rib
   tanlash imkoniyati yo'q;
4. va **cheklovning o'zi 18.4/18.6 da ochiq yozilgan**, demak qaror
   H1 ni himoya qilsa ham, **himoya ko'rinmas emas** — maqolada
   *"fail-slow limbi bu pilotda fail-slow'ni inkor qila olmaydi"*
   deb yozilishi shart.

> **Agar `D_probe(P0)` o'lchangandan keyin `thr` kvantlashdan ancha
> yuqori chiqsa, 18.2 ning qarori O'ZGARMAYDI** — u o'lchangan natijaga
> emas, matnga asoslangan. O'zgaradigan narsa — 18.4 ning cheklovi
> kuchini yo'qotadi, va bu **yaxshi xabar**, qayta talqin emas.

#### 🔴 v1.11 — F2 NING BIAS'I: ANTI-KONSERVATIV, va yuqoridagi kafolat O'TMAYDI

Yuqoridagi hamma narsa **18.2 ning referensi (F1)** haqida edi. v1.11 da
referens **F2** ga o'tdi, demak **bias yo'nalishi ham TESKARIGA aylandi**,
va buni ochiq yozish shart.

```
fail-slow shakli QO'LLAB-QUVVATLANMAYDI  <=>  CI95_upper[ Delta(P2,P0) ] < thr
thr:  F1 => 0.0600 s (o'lchangan)        F2 => 1.6 s (fiksa)      ~27x KATTA
```

> **`thr` kattalashgani uchun shart OSONLASHADI, demak F2
> *“fail-slow qo'llab-quvvatlanmaydi”* degan xulosani F1 ga nisbatan
> OSON qiladi — ya'ni F2 fail-slow gipotezasiga nisbatan
> ANTI-KONSERVATIV.** 18.6 ning jadvali buni allaqachon shunday
> belgilagan: F1 — *“fail-slow / H1 FOYDASIGA”*, F2 —
> *“H1 GA QARSHI”*.

**🔴 Va yuqoridagi 3-band — *“hech qanday ma'lumot mavjud emas, demak bu
qarorni natijani ko'rib tanlash imkoniyati yo'q”* — F2 GA
QO'LLANMAYDI.** U **18.2 ning v1.7 dagi qaroriga** tegishli va o'sha
yerda o'z kuchida. **F2 esa kalibratsiya o'lchovlari ko'rilgandan keyin
tanlandi**, va 18.6 ning QAROR bandidagi `0.7250 s` ko'rsatadi-ki F1 va
F2 o'sha o'lchangan farqning **qarama-qarshi tomonlarida** turadi —
ya'ni tanlovchi **qaysi konvensiya qaysi javobni beradigan** ekanini
ko'rgan. Oshkora e'lon: **Amendment log, v1.10 → v1.11, 0-band.**

**Shunga qaramay F2 qabul qilinadi, chunki:**

1. F1 ning **inkor** shoxi o'lchov bilan **erishib bo'lmaydigan**
   (18.6 ning QAROR bandi: `thr = 0.60 × P`, uchala bandda `< 5P`),
   ya'ni F1 limbni **bir tomonlama** qoldiradi — va bir tomonlama
   falsifikatsiya mezoni **mezon emas**;
2. **hech qanday P1 trial'i o'tkazilmagan**, demak **birlamchi endpoint,
   `Δ`, CI va p-qiymat KO'RILMAGAN** — ko'rilgan narsa kalibratsiya
   proxy'lari, gipotezaning natijasi emas;
3. **matniy narx ochiq qayd etilgan** (18.6 ning QAROR bandi): F2
   §11 ning *“×P0”* grammatikasiga qarshi boradi va *“20% oshish”*
   ning bazasini horizonga ko'chiradi;
4. va **yuqoridagi 2-band tan olinadi**: o'sha band F2 ni *“menga
   qulay bo'lgan variant”* deb belgilagan va *“matn bilan
   qo'llab-quvvatlanmaydi”* deb rad etgan edi. **Bu ogohlik bekor
   qilinmaydi.** F2 **matnga sodiqlik** uchun emas,
   **sinaluvchanlik** uchun tanlandi — va bias'i, narxi hamda
   post-data holati **hammasi oldindan, ma'lumot yig'ilishidan oldin**
   e'lon qilinadi.

> **F1 va F2 QARAMA-QARSHI yo'nalishda og'adi, va o'quvchi bu tanlov
> QAYSI tomonga og'ganini bilishi SHART.** Maqolada shunday yoziladi:
> *“fail-slow limbining chegarasi birinchi trial'dan OLDIN, lekin
> dozalash kalibratsiyasi KO'RILGANDAN KEYIN `thr = 0.20 × τ = 1.6 s`
> ga fiksa qilingan; bu F1 (`0.20 × RMST(P0)`) ga nisbatan
> fail-slow'ni INKOR qilishni osonlashtiradi.”* Bu **yumshatilmaydi**.

### 18.8 OCHIQ BO'SHLIQ — "time-to-VR" §6.1 ning uch o'lchovidan birortasiga bog'lanmagan

§10.2 va §11 **"time-to-VR"** deb yozadi. §6.1 esa uchta downtime
o'lchovini beradi: `D_sd`, **`D_probe` (asosiy)**, `D_eff`. **Qaysi
biri survival endpoint'i ekani hech qayerda aytilmagan.**

18.3 da `D_probe` deb o'qidim, chunki §6.1 uni aynan *"VR shartini
qanoatlantiruvchi oynaning birinchi probe'i"* gacha ta'riflaydi, ya'ni
u **ta'rifan** time-to-VR. Bu eng kuchli o'qish, lekin **matn buni
ochiq aytmaydi**, va tanlov ahamiyatli:

- `D_probe` — probe davriga kvantlangan (±P), 18.4 ning poli shundan;
- `D_eff` — brownout'ni ham hisoblaydi, uzluksiz, kvantlash poli
  **past**; §11(b) davom etish mezoni **aynan `D_eff`** ni ishlatadi;
- `D_sd` — §6.1 ning o'zi uni *"eng chalg'ituvchi"* deb ataydi.

> **Qayd etiladi, hal qilinMAYDI:** survival endpoint'ini `D_eff` deb
> o'qish 18.4 ning kvantlash polini **yumshatishi mumkin** va §11(b)
> bilan izchil bo'lardi — lekin bu `time-to-VR` ning ta'rifini
> tanlashdir, va §11/§10.2 matni `D_probe` ni ham, `D_eff` ni ham
> nomlamaydi. **F1–F4 bilan birga hal qilinishi kerak**, chunki u
> `thr` ning o'lchov poliga nisbatini o'zgartiradi.

### 18.9 OCHIQ MASALA — §14.4 ning havolasi: ATAYLAB yopilmadi

v1.4 §15.6(2) dan beri ochiq, endi to'rtta amendment bo'ylab. §17.8 da
shunday tavsiya berganman: *"§17.5 ning qarori muzlatilgan matnga
baribir tegadi, shuning uchun shu amendment bu havolani tuzatish uchun
to'g'ri joy."*

**v1.7 muzlatilgan matnni ochmaydi** — u, v1.4/v1.5/v1.6 kabi, faqat
oxiriga bo'lim qo'shadi. Demak **o'zim qo'ygan shart bajarilmadi**, va
men uni yopmayman. Nagging element'ni yopish uchun o'z mezonimni
jimgina yumshatish — aynan bu hujjat oldini olishi kerak bo'lgan narsa.

Havola xatosi **ikki marta** qayd etilgan (§15.6(2), §17.8) va to'g'ri
havola `04-driver-va-analiz-shartnomasi.md` §1.1 da mavjud, demak
amaliy xavf past va hujjatlashtirilgan. **Talab to'liq kuchda:
`units_show` unit TIRIK paytida olinadi.** Tuzatish vositasi — §17.5
qarorini amalga oshiradigan amendment.

### 18.10 NIMA O'ZGARMAYDI

§11 ning **ikkala limbi ham matn sifatida o'zgarmadi** — kuchli shakl
(`trend p > 0.05` **VA** Newcombe yuqori chegarasi `< 0.15`) va
fail-slow (`τ = 8 s`, `20%`). `τ = 8 s`, `W_stab_pilot = 8 s`,
`W_stab = 60 s`, `θ = 0.8`, `injection_offset = 3 s`,
`hold_cap_s = 12 s`, `guard_sustain_s = 15 s`, `T_conn`/`T_rt` = 50 ms,
`P` = 100 ms, `k_f` = 3, `ε` = 32 MiB, quiescence 0.05, `T_q` = 5 s,
`T_w` = 15 s, `T_w_max` = 120 s, arm'lar `A`/`no_action`,
`P0`/`P1`/`P2`, 20 blok / 120 trial, §10.1 Cochran–Armitage,
§10.2 KM/log-rank/**RMST difference**/Cox-HR taqiqi, §10.4 Holm,
§12 yopiq enum'i, §14 data schema, §16 va §17 ning qarorlari —
**hammasi muzlatilgan holida.** §13 ga tegilmadi.

Qo'shilgan narsa: aytilmagan referensning **o'qilishi**, ayirish
tartibi va yo'nalish talabi, bir sxema maydoni talabi
(`orientation`), va **hal qilinmagan qarorning ochiq bayonoti**.

### 18.11 NATIJA — yo'q

**Hech qanday eksperiment ishga tushirilmadi. Hech qanday natija yo'q.**
18.4 ning barcha raqamlari **muzlatilgan qiymatlardan** chiqarilgan
(`P = 100 ms`, `RestartSec = 100 ms`, §6.1 ning `D_probe` ta'rifi,
§9.2 ning `P(VR|P0) ≈ 1.0` bayonoti); yagona noma'lum — `t_start`, va
u **o'lchanmadi**. Uni o'lchash 18.6 da so'ralgan.

---

## 19. `boot_id` ning yetarlilik chegarasi, va §18.4 ning aniqlashtirilishi (muzlatilgan)

> Bu bo'lim **v1.8 amendment** bilan qo'shildi. U **hech bir operatsion
> ta'rifni, metrikani, chegarani, statistik testni yoki falsifikatsiya
> mezonini o'zgartirmaydi.** U uch narsani qiladi: (1) §16.11 ning
> ochiq qolgan o'lchovini **yopadi** (boshqa agent o'lchovi, provenans
> bilan), (2) §18.4 ning rejim tahlilini **tuzatadi va aniqlashtiradi**,
> (3) feasibility cheklovini kuchaytiradi.

### 19.1 FAKT — `boot_id` to'liq VM restart'ida O'ZGARADI; yetarlilik chegarasi chizildi

§16.11 da shunday yozilgan edi: *"**O'LCHANMADI:** to'liq WSL VM
restart'ida `boot_id` o'zgaradimi — **bu o'lchov bajarilmadi**."*
**Endi o'lchandi.**

**Provenans (aniq aytiladi):** quyidagi o'qishlar **orkestrator
tomonidan** olingan, **bu agent tomonidan emas**. Bu agent o'lchov
paytida guest ichida hech narsa o'qimadi (WSL ishi `guard-recal`
uchun to'xtatilgan) va bu qiymatlarni **mustaqil tasdiqlamadi.**

| o'lchov | qiymat |
|---|---|
| `/proc/uptime` | **544.35 s** (shu sessiyada avval: 2024.34 s) |
| `/proc/1/stat` 22-maydon | **74** tick ⇒ PID 1 yoshi 543.6 s = boot bilan teng |
| `boot_id` | **`580d1c88-a68b-4134-92ba-9712b5a6dd56`** |
| `UserspaceTimestampMonotonic` | **1248170** µs (1.25 s — yangi boot) |
| `FinishTimestampMonotonic` | **2326211** µs |

**Xulosaning qaysi qismi kimning o'lchoviga tayanadi — ajratib
yoziladi:**

- *"Yangi kernel boot bo'ldi"* — **orkestratorning o'z o'lchovi bilan
  yetarlicha asoslangan**: uptime `2024.34 s → 544.35 s` ga **orqaga
  ketdi**, va PID 1 yoshi boot bilan teng bo'lib qoldi. Bitta agentning
  o'qishlari buni o'zi ko'rsatadi.
- *"`boot_id` o'zgardi"* — **ikki agentning o'qishiga tayanadi**:
  avvalgi qiymat `ca4e5bab-2cd8-43aa-8455-2a22ca6746f3` **bu agentning
  §16.11 dagi yozuvidan** (uptime 1975 s da), yangi qiymat
  orkestratordan. **Bitta agent ikki qiymatni ham ko'rmagan.**

#### Natija — ikki restart rejimi ajratildi, har biriga bitta detektor

| restart rejimi | `boot_id` | `pid1_starttime_ticks` | kim tutadi |
|---|---|---|---|
| **to'liq VM restart** (yangi kernel boot) | **o'zgaradi** | yana kichik | **§14.6(5)** — allaqachon muzlatilgan |
| **init-only** (PID 1 restart, kernel ishlashda davom etadi) | **o'zgarmaydi** | **sakraydi** | **§16.11** ning marker'i |

**Shuning uchun §16.11 ning xulosasi aniqlashtiriladi, lekin
bekor qilinMAYDI:**

- §1 ning *"`boot_id` bu shartni tekshirib bo'ladigan qiladi"* da'vosi
  **umuman yolg'on emas** — u **faqat init-only holatda** yolg'on.
  §16.11 bu da'voni *"shu host'da yolg'on"* deb yozgan; aniqrog'i —
  *"init-only restart uchun yolg'on, to'liq VM restart uchun
  to'g'ri"*.
- §14.6(5) **zarur**, va **to'liq VM restart uchun yetarli**.
- §16.11 ning PID 1 `starttime` marker'i **init-only teshigini
  yopadi**, demak u **ortiqcha emas** — va endi buning sababi
  **o'lchov bilan** ko'rsatilgan.

> **§16.11 kuchsizlanmadi, kuchaydi:** ilgari marker *"`boot_id` ga
> ishonib bo'lmaydi"* degan umumiy asos bilan talab qilinardi; endi u
> **aniq nomlangan, o'lchangan teshikni** yopadi, va `boot_id` ning
> o'z roli ham saqlanadi. Ikki detektor **ortiqcha emas,
> to'ldiruvchi** — ikkalasi ham talab qilinadi.

#### Muzlatilgan talab — o'z-o'zini guvohlantiradigan o'qish

Yuqoridagi provenans bo'linishi takrorlanmasligi uchun:

> **Har bir `/proc/uptime` o'qishi bilan BIR VAQTDA `boot_id` va
> `/proc/1/stat` 22-maydoni ham o'qiladi va bir record'ga yoziladi**
> (`run_meta` va har `env_snapshot`, §16.11 talabini to'ldirib).
> Shunda keyingi restart **bitta agentning o'qishlaridan** o'zi
> guvohlanadi va ikki manbaga tayanmaydi.

Bu uch maydon **bitta atomik o'qish guruhi** — alohida vaqtlarda
olingan `uptime` va `boot_id` juftligi aynan hozirgi provenans
bo'linishini qaytaradi.

### 19.2 CHEKLOV — feasibility: to'liq VM restart init-only'dan QATTIQROQ

§16.11 PID 1 restart'ini **feasibility gate** deb atagan (transient va
`--collect` unit'lar yo'qoladi). **To'liq VM restart qat'iy yomonroq:**
kernel ham, cgroup ierarxiyasi ham, barcha monotonic anchor'lar ham
yangi.

**Orkestrator xabari (bu agent tasdiqlamagan):** yuqoridagi restart
`experiment/guard-recal` kalibratsiya ishlatayotganda sodir bo'lgan;
uning unit'lari yo'qolgan va run kataloglari `guard-recal-C5` gacha
mavjud, demak ishining bir qismi restart'dan **oshib ketgan** bo'lishi
mumkin.

**Pilot uchun amaliy oqibati:** §9.4 ning kampaniya bahosi
**≈2.5 soat** (120 trial × ≈75 s). Shu guest'da bu davomiylikda
uzilish ehtimoli **e'tiborsiz emas**. Demak:

- driver'ning marker o'zgarishida **hard-abort** xatti-harakati
  nazariy himoya emas — u **ishga tushishi kutiladi**;
- uzilgan kampaniya **`harness_error`** yoki `censored` trial'lar
  ko'rinishida chiqadi va §12 ning eksklyuziya darajasi hisobotiga
  kiradi — **yashirilmaydi**;
- uzilish **blok strukturasini** buzadi (§8.4: blok = har
  `(arm × pressure)` yacheykadan **aynan bitta** trial). To'liq
  bo'lmagan blok — **blokning o'zi** tugallanmagan, demak
  *"blok sekin drift'ni o'ziga singdiradi"* xossasi o'sha blok uchun
  yo'qoladi. **Tugallanmagan bloklarning taqdiri §8.4 da aytilmagan**
  — bu **ochiq bo'shliq**, va u kampaniya uzilsa yuzaga keladi.

> **TALQIN:** bu `feature/iso` ning izolyatsiyalangan QEMU guest'i
> uchun **ilmiy** asos, qulaylik emas: o'zimiz boshqaradigan guest
> o'zini qayta ishga tushirmaydi, demak `boot_id` va marker
> invariantlari kampaniya davomida **ushlanadi**. §15.1 da `/dev/kvm`
> mavjudligi o'lchangan, demak yo'l texnik jihatdan ochiq. Lekin bu
> **§0 bo'yicha P1 qamrovidan tashqarida** va o'z pre-registration'ini
> talab qiladi — v1.8 bu yo'lni **ochmaydi**.

### 19.3 TUZATISH — §18.4 ning rejim tahlili chala edi: IKKALA chet ham degenerat

§18.4 ikki rejimni shunday bergan:

| rejim | §18.4 nima dedi |
|---|---|
| `RMST(P0)` kichik | inkor **erishib bo'lmaydi**, qo'llab-quvvatlash **deyarli avtomatik** |
| `RMST(P0) → 8 s` | inkor **erishiladigan**, qo'llab-quvvatlash **qat'iy** |

**Ikkinchi qator chala va chalg'ituvchi.** U o'sha rejimni *sog'lom*
ko'rsatadi. Aslida u ham **degenerat**, va sababi — `RMST` ning
**yuqoridan `τ` bilan chegaralanganligi**, ya'ni aynan `analyze`
ko'rsatgan nuqta.

#### Aniq arifmetika (hammasi muzlatilgan qiymatlardan)

`R := RMST_A(P0, τ)`, `τ = 8 s`, `thr = 0.20 · R`, va
`Δ = RMST_A(P2, τ) − R`. `RMST ∈ [0, τ]` bo'lgani uchun:

```
Δ ≤ τ − R                                  (yuqori chegara — ceiling)
```

Demak *"20% oshish"* **erishiladigan** bo'lishi uchun:

```
thr ≤ τ − R   ⟺   0.20·R ≤ τ − R   ⟺   1.20·R ≤ τ   ⟺   R ≤ τ/1.20 = 6.67 s
```

> **FAKT: agar `R > 6.67 s` bo'lsa, `thr` **erishilishi mumkin bo'lgan
> eng katta effektdan katta** bo'ladi. Ya'ni kriteriy **sodir bo'lishi
> MUMKIN BO'LMAGAN** holatni qidiradi, va *"fail-slow
> qo'llab-quvvatlanmaydi"* degan xulosa ma'lumotdan emas,
> **arifmetikadan** kelib chiqadi.**

Pastki chetda, §6.1 ning kvantlashi (`±P`, har chekkada `+P/2` bias):

```
thr ≥ P   ⟺   0.20·R ≥ 0.1 s   ⟺   R ≥ 0.5 s
thr ≥ 5P  ⟺   R ≥ 2.5 s
```

#### To'g'rilangan rejim jadvali

| rejim | `R` | `thr` | kriteriy holati |
|---|---|---|---|
| **pastki degeneratsiya** | `< 0.5 s` | `< P` | chegara **kvantlash polidan past** ⇒ inkor **aniqlanmaydi** ⇒ fail-slow deyarli hech qachon inkor qilinmaydi |
| **tishli band** | `≈ 2.5 … 5.7 s` | `0.5 … 1.14 s` | `thr ≥ 5P` **va** `thr ≤ ½(τ−R)` ⇒ kriteriy **haqiqiy test** |
| **yuqori degeneratsiya** | `> 6.67 s` | `> τ − R` | *"20% oshish"* **erishib bo'lmaydigan** ⇒ inkor **arifmetik jihatdan avtomatik** |

**Va §9.2 aytgan rejim qayerda:** §18.4 ning chiqarmasi
`R ≈ 0.4 … 1.1 s` — ya'ni **pastki degeneratsiya chegarasida yoki
undan sal yuqorida**, va **tishli banddan ancha past**.

> **Shuning uchun `analyze` ning nuqtasi to'g'ri va §18.2 ni
> kuchsizlashtirmaydi, balki uni o'tkirlashtiradi: referens kattalik
> chegarani shunchaki masshtablamaydi — u kriteriyning TISHI bor-yo'qligini
> belgilaydi.** Ikkala chetda ham kriteriy *"fail-slow
> qo'llab-quvvatlanmaydi"* yoki *"qo'llab-quvvatlanadi"* degan javobni
> **ma'lumotdan emas, rejimdan** oladi.

**Diqqat — bir nozik farq:** yuqori degeneratsiyada kriteriy
fail-slow'ni **avtomatik INKOR qiladi** (ma'lumot nimani ko'rsatsa
ham), pastki degeneratsiyada esa **avtomatik QO'LLAB-QUVVATLAYDI**.
Ya'ni ikki degeneratsiya **teskari xulosaga** olib keladi, va qaysi
biriga tushishni `R` belgilaydi — u esa **o'lchanmagan**. §18.7 da
e'lon qilingan bias yo'nalishi (H1 foydasiga) **pastki
degeneratsiyaga, ya'ni §9.2 aytgan rejimga** tegishli va **o'zinicha
qoladi**.

#### §18.6 ning variantlariga ta'siri

19.3 **F1–F4 tanlovini qilmaydi** va §18.2 ning referensini
o'zgartirmaydi (u matndan o'qilgan, rejimdan emas). Lekin u
variantlarni **aniqroq baholaydi**:

- **F1** (`thr = 0.20·R`): §9.2 aytgan rejimda **pastki
  degeneratsiya**. 19.3 buni endi **aniq chegara bilan** ko'rsatadi
  (`R < 0.5 s ⇒ thr < P`).
- **F2** (`thr = 0.20·τ = 1.6 s`): rejimdan **mustaqil** va
  kvantlashdan `16×` yuqori — lekin `Δ ≤ τ − R` chegarasi bilan
  taqqoslansa, `R > 6.4 s` bo'lsa F2 ham **erishib bo'lmaydigan**
  chegaraga aylanadi (`1.6 > 8 − R ⟺ R > 6.4 s`). Ya'ni **F2 ham
  yuqori degeneratsiyadan himoyalanmagan**, faqat chegarasi boshqa.
- **ceiling muammosi hech bir F variantida yo'qolmaydi**, chunki u
  `RMST ∈ [0, τ]` dan kelib chiqadi, referensdan emas. **Uni faqat
  `τ` ni oshirish yoki endpoint'ni o'zgartirish (§18.8) hal qiladi** —
  ikkalasi ham §17.5 ning qaroriga bog'langan.

> **Demak §17.5, §18.6 va §18.8 — uchalasi bitta qarorning
> bo'laklari**, va ularni alohida hal qilish ziddiyat yaratadi.
> `τ = W_stab_pilot = 8 s` — uchalasining ham tuguni.

#### Qaror uchun zarur, lekin MAVJUD BO'LMAGAN o'lchov

`R = RMST_A(P0, τ)`. **Bu o'lchov bajarilmadi** — bu agent guest
ichida hech narsa o'lchamadi. §18.6 ning so'rovi kuchda qoladi va
endi **aniq qabul mezoni** bilan:

| o'lchangan `R` | xulosa |
|---|---|
| `R < 0.5 s` | **pastki degeneratsiya** — F1 yaramaydi, egasi F2–F4 dan tanlashi shart |
| `0.5 … 2.5 s` | chegara kvantlashdan `1–5×` — **chegara zonasi**, ehtiyotkorlik bilan |
| `2.5 … 5.7 s` | **tishli band** — F1 yetarli |
| `> 6.67 s` | **yuqori degeneratsiya** — hech bir nisbiy chegara ishlamaydi |

### 19.4 NIMA O'ZGARMAYDI

§18.2 ning qarori (referens = `RMST(P0)`, ayirish tartibi `P2 − P0`,
yuqori chegara shakli) — **o'zgarmadi**; u matndan o'qilgan va 19.3
uni **qo'llab-quvvatlaydi**. §16.11 ning PID 1 marker talabi —
**o'zgarmadi**, 19.1 uni **asoslaydi**. §14.6(5) — o'zgarmadi.
§11 ning ikkala limbi, `τ = 8 s`, `20%`, `W_stab_pilot = 8 s`,
`W_stab = 60 s`, `θ = 0.8`, `injection_offset = 3 s`,
`hold_cap_s = 12 s`, `guard_sustain_s = 15 s`, `T_conn`/`T_rt` = 50 ms,
`P` = 100 ms, `k_f` = 3, `ε` = 32 MiB, quiescence 0.05, `T_q` = 5 s,
`T_w` = 15 s, `T_w_max` = 120 s, arm'lar `A`/`no_action`,
`P0`/`P1`/`P2`, 20 blok / 120 trial, §10.1, §10.2, §10.4, §12 ning
yopiq enum'i, §14, §16, §17, §18 — **hammasi muzlatilgan holida.**
§13 ga tegilmadi.

Qo'shilgan narsa: bir FAKT (provenans bilan), bir atomik o'qish
talabi, §18.4 ning **tuzatilgan** rejim tahlili, va bir ochiq
bo'shliq (19.2: tugallanmagan bloklar).

### 19.5 NATIJA — yo'q

**Hech qanday eksperiment ishga tushirilmadi. Hech qanday natija yo'q.**
19.1 ning o'lchovlari **boshqa agent tomonidan** olingan va shu
sifatida belgilangan; bu agent ularni mustaqil tasdiqlamadi. 19.3 ning
butun arifmetikasi **muzlatilgan qiymatlardan** chiqarilgan
(`τ = 8 s`, `P = 100 ms`, `RMST ∈ [0, τ]`, §6.1 ning kvantlash
bayonoti); `R` **o'lchanmadi**.

---

## 20. `vr = None` — maxrajga kirish aniqlanganlik bilan belgilanadi (muzlatilgan)

> Bu bo'lim **v1.8 amendment** bilan qo'shildi. U **hech bir operatsion
> ta'rifni, metrikani, chegarani, statistik testni yoki falsifikatsiya
> mezonini o'zgartirmaydi.** U §12 jim qolgan uchinchi nuqtani hal
> qiladi, va §16.2(B) bilan §17.4 ni **bitta umumiy printsipning**
> xususiy hollari qilib ko'rsatadi.

### 20.1 FAKT — nima aniqlandi

`reduce-fix` **sof brownout** fixture'i qurdi: throughput `R_ref` ning
30% iga tushadi, lekin **har bir probe contract'dan o'tadi**. Kodda:

```
contract buzilishi yo'q  ⇒  find_failure_onsets hech narsa topmaydi
                         ⇒  build_episodes hech narsa qurmaydi
                         ⇒  evaluate_vr → vr = None, vr_reason = "no_episode"
trial `complete` / `derived`  ⇒  §16.2(B) ning kiruvchi juftlari bo'yicha
                                 BINAR MAXRAJDA — aniqlanmagan VR bilan
```

`vr = None` ning uchta sababi kodda nomlangan: **`no_episode`**,
**`r_ref_unavailable`**, **`throughput_unmeasurable`** (§17 ga
tegishli `window_truncated` esa nol bo'lishi shart).

**Muammo:** maxrajga kirish *natija kuzatilgan* degan da'vo. `vr = None`
bilan maxrajda bo'lish — kuzatilmagan narsani kuzatilgan deb ko'rsatish,
va `P(VR)` ning qiymati `None` ni implementatsiya qanday ishlashiga
bog'liq bo'lib qoladi — aynan §16 va §17 boshqa joylarda **olib
tashlagan** noaniqlik turi.

### 20.2 QAROR — umumiy printsip, uchta holatni bir joyga yig'adi

§4 VR ni **epizod `E` uchun** ta'riflaydi: *"Epizod `E`
verified-recovered, agar …"*. Demak maxrajning to'g'ri ta'rifi
disposition'lar ro'yxati emas, balki **predikatning aniqlanganligi**:

> **Binar `P(VR)` maxraji — §4 ning predikati ANIQLANGAN qiymat
> (`true` yoki `false`) olgan trial'lar to'plami. `vr = None` —
> sababi nima bo'lishidan qat'i nazar — maxrajdan TASHQARIDA, va
> sabab §12 ning *"eksklyuziya darajasi natija sifatida beriladi"*
> qoidasi va §16.4 ning nomlash qoidasi bo'yicha **nomlanib**
> beriladi.**

Bu **yangi qoida emas, umumlashtirish** — §16.2(B) va §17.4 undan
kelib chiqadi:

| holat | `vr` | maxrajda? | manba |
|---|---|---|---|
| oyna o'tdi | `true` | **ha** (numerator) | §4 |
| `t_up` yo'q, horizon down tugadi | **`false`** (aniqlangan) | **ha** | §16.2(B) |
| probe uzilishi > 2×P | `None` | **yo'q** | §16.2(B) |
| oyna hold'dan/horizon'dan chiqdi | `None` | **yo'q** | §17.4 |
| **`no_episode`** | `None` | **yo'q** | **20.3** |
| **`r_ref_unavailable`**, **`throughput_unmeasurable`** | `None` | **yo'q** | **20.4** |

**Hech qanday yangi `disposition` qiymati kerak emas va §12 ning yopiq
enum'iga tegilMAYDI.** Qoida `vr` maydonining o'ziga tayanadi, u
allaqachon mavjud.

### 20.3 QAROR — `no_episode`: savol UMUMAN tug'ilmagan

Bu uchinchi epistemologik kategoriya, va u avvalgi ikkisidan **farq
qiladi**:

| kategoriya | VR savoli | javob |
|---|---|---|
| `down_at_horizon` | **tug'ildi** | kuzatilgan `false` |
| `probe_gap`, §17.4 | **tug'ildi** | **kuzatilmagan** |
| **`no_episode`** | **TUG'ILMAGAN** | — |

Epizod bo'lmasa §4 ning predikati **instansiyalanmaydi**: `t_up`
("`E` ning oxirgi action'idan keyingi birinchi contract'dan o'tgan
probe") ta'rifi `E` ga bog'liq, `E` esa yo'q. **`None` — halol
qiymat**, va shu sababli maxrajdan tashqarida.

#### Survival'ga ham KIRMAYDI — bu birinchi shunday kategoriya

§6.2 censored trial'larni KM/log-rank'ga kiritishni talab qiladi.
**Lekin §6.2 ning qoidasi `recovery bo'lmagan` trial'lar haqida:**
*"**Recovery bo'lmagan trial'larni tashlash** — klassik yashirin
bias, va u tez ishdan chiqadigan arm'ni chiroyli ko'rsatadi."*

`no_episode` trial — **recovery bo'lmagan trial emas.** Unda
recovery **kutilmagan**: xizmat ishdan chiqmagan, demak hech qanday
hodisa **kutilayotgan** emas edi. Censored kuzatuv *"hodisa `t`
gacha sodir bo'lmadi"* degan da'vo, va u hodisaning **kutilayotgan**
bo'lishini talab qiladi. Bu yerda u kutilayotgan emas.

> **Shuning uchun `no_episode` **ikkala** to'plamdan ham chiqariladi —
> binar maxrajdan **va** KM/log-rank'dan. Bu §6.2 ga zid emas, chunki
> §6.2 ning qoidasi bu holatga **yetib bormaydi**.** Bu v1.5 dan beri
> birinchi kategoriya bo'lib ikkala to'plamdan ham chiqadi, shuning
> uchun ochiq yoziladi.

#### Lekin bu trial SIFAT metrikasi — yashirilmaydi

§9.3 bo'yicha **har trial'ga aynan bitta injeksiya** beriladi, va P1
ning yagona fault'i `clean_crash` (probe → `exit(1)`, `SIGKILL`,
`SIGSEGV`). SUT o'ldirilsa contract **buzilishi shart** (socket
accept qilmaydi). Demak muzlatilgan P1 dizaynida `no_episode`
**injeksiya ishlamaganini** bildiradi — natija emas, **trial
nuqsoni**.

> **Muzlatilgan hisobot qoidasi:** `no_episode` darajasi
> `(arm × pressure)` bo'yicha **alohida** beriladi va
> **injektor samaradorligi metrikasi** deb nomlanadi, boshqa
> eksklyuziyalar bilan **birlashtirilmaydi**. Nolga teng bo'lmagan
> daraja — fault injektori o'z ishini bajarmayotganini bildiradi va
> **pilotni gate qiladi**: §9.2 ning to'rtala mexanizmi ham
> injeksiyaning ishlashini nazarda tutadi.

### 20.4 QAROR — `r_ref_unavailable` / `throughput_unmeasurable`: savol tug'ildi, 5-band baholanmaydi

Bu **boshqa da'vo** va `no_episode` dan **farqli** ishlanadi.

Epizod **bor**, demak VR savoli **tug'ildi**. Lekin §4 ning
**5-bandi** (*"oyna throughput'i ≥ `θ · R_ref`"*) baholanishi uchun
`R_ref` kerak, va u yo'q. §4 bu bandning rolini ochiq aytadi:

> *"**5-band VR ni process-liveness'dan ajratadigan narsa.** Qaytgan
> lekin 5% throughput'da ishlayotgan xizmat recovered emas. **Busiz
> butun hissa "process tirikmi?" ga qulaydi.**"*

Demak:

1. **`vr = None`, maxrajdan tashqarida** — bu `probe_gap` bilan bir
   xil sinf: savol tug'ildi, javob **kuzatilmadi**.
2. **1–4 bandlar ustida VR hisoblash QAT'IYAN TAQIQLANADI.**
   5-bandni tashlab 1–4 ni baholash — VR ni **liveness-only**
   ta'rifga tushirish, va §9.2 buning natijasini oldindan yozgan:
   *"**liveness-only VR ta'rifi ehtimol null pilot beradi, va bu
   null — ta'rif artefakti, H1 ga qarshi dalil EMAS.**"*
   Ya'ni bunday trial'ni "VR = true" deb yozish §9.2 ning
   ogohlantirgan artefaktini **yaratadi**.
3. **KM/log-rank'ga KIRADI** — `no_episode` dan farqli, bu yerda
   hodisa **kutilayotgan** edi (xizmat ishdan chiqdi). `D_probe`
   ning oxiri (*"VR shartini qanoatlantiruvchi oynaning birinchi
   probe'i"*, §6.1) aniqlanmaydi, demak trial **horizon'da
   censored** sifatida kiradi — §6.2 ning qoidasi aynan shu
   holatga **yetib boradi**.
4. Darajasi **instrumentatsiya yo'qolishi** sinfida, `probe_gap`
   bilan **birga** beriladi va `no_episode` bilan
   **birlashtirilMAYDI**.

### 20.5 CHEKLOV — §4 contract'ni buzmagan brownout'ga KO'R

Fixture'ning ochgan narsasi bookkeeping'dan kattaroq.

**Avval bir aniqlik:** sof brownout **§9.2 ning (iii) mexanizmi
EMAS.** (iii) *"**start bo'ldi** lekin throughput < `θ·R_ref`"* —
ya'ni u **restart'dan keyingi** brownout va epizodni **nazarda
tutadi**. Contract umuman buzilmagan brownout — boshqa hodisa.

**Natija:** `θ = 0.8` va 30% throughput bilan xizmat **jiddiy
degradatsiyalangan**, lekin §4 ning predikati **instansiyalanmaydi**,
demak binar endpoint buni **umuman ko'rmaydi** — na `VR = false`, na
invalidator, na epizod.

**Lekin pilot ko'r emas:** §6.1 ning `D_eff` i
(`P·n_failing_probes + ∫ max(0, 1 − r(t)/R_ref) dt`) aynan shu
degradatsiyani o'lchaydi — §6.1 uning haqida *"yo'q —
**brownout'ni ham hisoblaydi**"* deydi. Va §11 ning davom etish
mezoni **(b)** aynan `D_eff` ni ishlatadi
(*"`D_eff` `P2` da ≥1.5× `P0`"*).

> **Shuning uchun maqolada shunday yoziladi:** binar endpoint
> (`P(VR)`, §10.1) contract'ni buzmagan degradatsiyaga **ko'r**;
> uzluksiz downtime o'lchovi (`D_eff`, §6.1) uni **ko'radi**; va
> §11(b) shu sababli faqat qo'shimcha emas, **mustaqil zarur**
> mezon. Bu **yumshatilmaydi**.

**Bog'liqlik (§17.7):** contract'ni buzmagan, pressure sabab
degradatsiya — aynan §8.2 ning (ii) nazorati
(*"injeksiya yo'q, pressure bor"*) o'lchashi kerak bo'lgan narsa, va
o'sha nazorat §9.3 ning panjarasida **yo'q**. Fixture shu bo'shliqni
boshqa tomondan ko'rsatdi.

### 20.6 Bias yo'nalishini ochiq e'lon qilish

**Birlamchi asos — aniqlanganlik, yo'nalish emas.** Hozirgi holatda
`P(VR)` ning qiymati `None` ni implementatsiya qanday ishlashiga
bog'liq; qaror shu bog'liqlikni **olib tashlaydi**. Bu qaror
`None` ni raqamga aylantirmaydi, balki uni **maxrajdan chiqaradi**,
demak `P(VR)` har qanday `None`-siyosatidan **mustaqil** bo'ladi.

**Yo'nalish, shartli ravishda va halol:** `vr = None` trial maxrajda
qolsa, u numeratorga **kirmaydi**, demak `P(VR) = k/n` ni
**pasaytiradi**. Pressure sabab brownout `P2` da ko'proq uchrashi
**ehtimol**, demak hozirgi holat `P(VR|P2)` ni pasaytirib trend'ni
**kuchaytirardi** — ya'ni **H1 foydasiga** bias. Qaror uni olib
tashlaydi, demak **bu qaror H1 GA QARSHI ishlaydi.**

> **Diqqat:** `no_episode` ning `P2` da to'planishi **o'lchanmagan**
> taxmin. Clean_crash injeksiyasi pressure'dan qat'i nazar epizod
> berishi kerak, demak to'planish faqat pressure injeksiya yo'lining
> o'zini buzgan holda yuzaga keladi. Shuning uchun yo'nalish
> **shartli** deb e'lon qilinadi, va qarorning asosi **aniqlanganlik**.

**Shuni ham ochiq aytaman:** bu qaror §16.2(B) va §18.2 bilan
**teskari yo'nalishga** ishlaydi (ular H1 foydasiga edi). Qarorlar
bir tomonga qarab tizmalanmayotgani — ular **yo'naltirilmayotganining**
o'zi dalili. Har biri alohida matndan chiqarilgan.

### 20.7 TASDIQ — `reduce-fix` ning ikki hukmi §17 ga ZID EMAS

**(a) §17.4 ni `P0` da ham bir xil qo'llash — TO'G'RI**, va asos
`reduce-fix` aytganidan kuchliroq. §9.4 ning trial jadvali
(*"baseline 10 s → ramp 5 s → hold, injeksiya hold'ga 3 s kirgach"*)
**barcha pressure darajalarida** amal qiladi; `P0` da generator
**idle** (§9.3), lekin fazalar **jadval sifatida** saqlanadi.
Agar oyna sharti `P0` da yumshatilsa, trend testi `P2` da
*"fazaning ichiga to'liq sig'gan oyna"* ni `P0` da *"fazadan chiqib
ketgan oyna"* bilan taqqoslardi — ya'ni **trend strataları bo'ylab
turli kattaliklar**, aynan §17 olib tashlagan bias. **Bir xil
qo'llash — majburiy.**

**(b) deny-list o'rniga allow-list — TO'G'RI**, va u §8.4(3) ning
muzlatilgan fail-closed qoidasining to'g'ridan-to'g'ri qo'llanishi:
*"Kuzatuv o'qilmasa (None) u **jim deb hisoblanMAYDI**."*
Kelgusi `disposition_source` avtomatik **chiqariladi va nomlanadi**,
maxrajga **sudralib kirmaydi**.

> **20.2 ning qoidasi shu printsipni `vr` ga ham yoyadi:** `vr`
> **tasdiqlab aniqlangan** bo'lishi shart (`true` yoki `false`),
> *"aniqlanmaganligi ma'lum emas"* yetarli **emas**.

### 20.8 OCHIQ BO'SHLIQ — §12 enum'ida "injeksiya ishlamadi" qiymati yo'q

20.3 `no_episode` ni **trial nuqsoni** deb atadi, lekin §12 ning
**yopiq** enum'ida unga mos qiymat yo'q: `contaminated` (biz
yubormagan `SIGKILL` / cheklamagan `oom_kill` / bystander),
`harness_error` (harness istisnosi), `censored` (probe uzilishi yoki
horizon down) — **birortasi ham emas**. Hozirgi kodda u
`complete` / `derived` bo'lib qoladi.

**Hal qilinMAYDI:** yangi qiymat qo'shish §12 ning **yopiq
enum'ini** o'zgartiradi, va *"Har trial'ga **aynan bitta**
disposition"* qoidasi bilan birga bu muzlatilgan shartnomaga
tegish bo'ladi. **20.2 ning qoidasi bu bo'shliqni analiz tomondan
yopadi** (`vr = None` ⇒ maxrajdan tashqarida, sabab nomlanadi),
demak u **P1 ni bloklamaydi**; lekin `no_episode` trial `complete`
deb **nomlanishi** — §12 ning *"to'liq o'lchandi"* ma'nosiga mos
kelmaydi. Egasining qarori; §17.5 amendment'i uchun tabiiy joy.

### 20.9 NIMA O'ZGARMAYDI

§4 ning VR ta'rifi va **5-bandi**, §6.1 ning uch downtime o'lchovi,
§6.2 ning *"tashlanmaydi, ishlanadi"* qoidasi, §9.2 ning to'rtta
mexanizmi va liveness-only ogohligi, §10.1, §10.2, §10.4, §11 ning
ikkala limbi va davom etish mezonlari, §12 ning **yopiq enum'i** va
*"aynan bitta disposition"* qoidasi, §14, §16, §17, §18, §19 —
**hammasi muzlatilgan holida.** `θ = 0.8`, `τ = 8 s`,
`W_stab_pilot = 8 s`, `W_stab = 60 s`, `injection_offset = 3 s`,
`hold_cap_s = 12 s`, `guard_sustain_s = 15 s`, `T_conn`/`T_rt` =
50 ms, `P` = 100 ms, `k_f` = 3, `ε` = 32 MiB, quiescence 0.05,
`T_q` = 5 s, `T_w` = 15 s, `T_w_max` = 120 s, arm'lar
`A`/`no_action`, `P0`/`P1`/`P2`, 20 blok / 120 trial —
**o'zgarmadi.** §13 ga tegilmadi.

Qo'shilgan narsa: bitta umumlashtirilgan maxraj qoidasi (20.2), ikki
holat uchun **farqli** ishlov (20.3, 20.4), ikki hisobot sinfi, bir
cheklov (20.5), ikki tasdiq (20.7) va bir ochiq bo'shliq (20.8).

### 20.10 NATIJA — yo'q

**Hech qanday eksperiment ishga tushirilmadi. Hech qanday natija yo'q.**
Bu bo'limdagi hech bir qaror kuzatilgan natijadan keyin qabul
qilinmagan; barcha asoslar §4, §6.1, §6.2, §9.2, §9.3, §8.4 va §12
ning muzlatilgan matnidan. `no_episode` ning taqsimoti
**o'lchanmagan** va 20.6 da shunday belgilangan.

---

## 21. `guard-recal` ning o'lchovlari: OQ-12, va band 4 ning FAKT bo'lishi (muzlatilgan)

> Bu bo'lim **v1.9 amendment** bilan qo'shildi. U **hech bir operatsion
> ta'rifni, metrikani, chegarani, statistik testni yoki falsifikatsiya
> mezonini o'zgartirmaydi.** U: (1) **OQ-12 ni rad etadi** va §18.3 ni
> tasdiqlaydi, (2) **o'z qabul qoidamdagi nuqsonni tuzatadi**,
> (3) §17.5 va §18.6 qarorlarining **ikkisi ham zarur** ekanini
> o'lchov bilan belgilaydi, (4) §16.11 ning GIPOTEZA'sini **FAKT**
> sifatida qayd etadi va undan kelib chiqadigan qoidani beradi.

**Manba:** `docs/architecture/08-guard-rekalibratsiya.md` (1662 qator),
`experiment/guard-recal` tomonidan o'lchangan. **Bu agent guest ichida
hech narsa o'lchamadi** (WSL ishi guard o'lchovi uchun to'xtatilgan);
quyidagi raqamlar **o'sha hujjatdan o'qilgan** va mustaqil
tasdiqlanmagan. Hujjatning o'z kontaminatsiya yozuvi (§1.3) hisobga
olinadi: pressure ostidagi `t_start` ning **toza** o'lchovi ishlatiladi.

### 21.1 QAROR — OQ-12 RAD ETILADI; §18.3 o'z kuchida

OQ-12 (`08` §12, §16.2 CHEKLOV): *agar §11 ning `RMST(P0)` i
`W_stab_pilot = 8 s` ni o'z ichiga olgan to'liq time-to-VR bo'lsa,
`RMST(P0) ≈ 8.5 s`, `thr ≈ 1.7 s ≥ 5P`, demak §18.6 ning qarori
kerak emas.*

**Rad etiladi, uchta mustaqil asos bilan.**

#### (a) Matn — §18.3 allaqachon hal qilgan

§6.1 `D_probe` ni *"failure'dan oldingi oxirgi o'tgan probe → VR
shartini qanoatlantiruvchi oynaning **birinchi probe'i**"* deb
ta'riflaydi — oyna **boshida** tugaydi. §6.3 esa
*"'Verification latency' achievement metrikasi sifatida BERILMAYDI —
muvaffaqiyatli VR uchun u ta'rifan `W_stab`ga teng"*. Ya'ni oyna
uzunligi metrikadan **ataylab chiqarilgan**.

#### (b) Arifmetika — `RMST(τ)` `τ` BILAN CHEGARALANGAN

Bu OQ-12 ning aniq xatosi:

```
RMST(τ) = ∫₀^τ S(t) dt = E[ min(T, τ) ]        ⇒   RMST(τ) ≤ τ  HAR DOIM
```

Agar `time-to-VR` oynani o'z ichiga olsa, `T = t_up + 8 ≥ 8 s` **har bir
trial uchun**, demak `min(T, 8) = 8` **har bir trial uchun**, demak:

```
RMST(P0) = 8.000 s  AYNAN     (8.5 s EMAS)
RMST(P2) = 8.000 s  AYNAN
Δ = 8 − 8 = 0       AYNIQSA, dispersiyasi NOL, har qanday ma'lumot uchun
```

`≈8.5 s` raqami — `E[T]`, ya'ni **chegaralanmagan o'rtacha**, va u
aynan §10.2 `RMST` ni tanlab **qochgan** kattalik (censoring ostida
beqaror). `RMST` emas.

**Natija teskari:** `thr = 0.20 × 8 = 1.6 s`, lekin `CI = [0, 0]`,
demak `CI_upper = 0 < 1.6` **har doim** ⇒ *"fail-slow
qo'llab-quvvatlanmaydi"* **har qanday ma'lumot uchun avtomatik** e'lon
qilinadi.

> **Ya'ni oyna-ichidagi o'qish qarorni keraksiz qilmaydi — u limbni
> SHARTSIZ INKOR qiladigan qilib qo'yadi.** Bu hozirgi holatdan
> **qat'iy yomonroq.**

#### (c) §19.3 ning chegarasi buni allaqachon aytgan

§19.3: `thr ≤ τ − R` ⟺ `R ≤ τ/1.20 = 6.67 s`. Oyna-ichidagi o'qishda
`R = 8 s > 6.67 s`, demak u §19.3 ning **yuqori degeneratsiyasi**ning
chegaraviy holati: `thr > τ − R = 0`.

#### Natija

> **§18.3 o'z kuchida: `time-to-VR` hodisa vaqti `t_up` da.**
> `guard-recal` ning proxy'i — **to'g'ri kattalik**.

### 21.2 TUZATISH — mening §18.6 qabul qoidam BIR TOMONLAMA edi

§18.6 da shunday yozganman: *"`thr ≥ ~5 × P` bo'lsa §18.4 ning
cheklovi amalda bezarar va F1 yetarli"*. **Bu faqat pastki chegarani
tekshiradi.** §19.3 keyinchalik yuqori chegarani (`thr ≤ τ − R`)
chiqardi, lekin **men uni qabul qoidasiga qaytarib qo'ymadim.**

**OQ-12 aynan shu bo'shliqdan o'tdi:** u `R` ni oshirib
*"`thr ≥ 5P`"* ni qanoatlantiradi — ya'ni **mening yozilgan qoidamni
bajaradi** — va shu bilan birga yuqori degeneratsiyaga tushadi.
Qoidam noto'g'ri edi, OQ-12 emas.

**Tuzatilgan, IKKI TOMONLAMA qabul qoidasi** (barchasi muzlatilgan
qiymatlardan):

```
5P ≤ thr ≤ ½(τ − R)        ⟺        2.5 s ≤ R ≤ 5.7 s
```

| o'qish | `R` | pastki test (`≥ 5P`) | yuqori test (`≤ ½(τ−R)`) | natija |
|---|---|---|---|---|
| `t_up` anchor (§18.3, o'lchangan) | **0.483 s** | ❌ yiqiladi | ✓ o'tadi | **qaror KERAK** |
| oyna-ichida (OQ-12) | **8.000 s** | ✓ o'tadi | ❌ yiqiladi | **qaror KERAK** |

> **Ikkala o'qish ham tuzatilgan qoidadan yiqiladi, demak §18.6 ning
> qarori OQ-12 ning javobidan QAT'I NAZAR zarur.** Javob (21.1)
> baribir muhim — u qaysi degeneratsiyada turganimizni aytadi — lekin
> *"qaror kerakmi"* savoli unga **bog'liq emas**.

### 21.3 FAKT — o'lchangan chegara, va limb nima qiladi

`08` §16.1–16.2, `revix/prober.py` 10 Hz, arm `A`, 12 epizod,
`boot_id` va `pid1_starttime` ikki chekkada ham **o'zgarmagan**
(ya'ni o'lchov §16.11 ning marker shartini qanoatlantiradi):

```
D_probe proxy (P0):  n=12  min 0.400  p50 0.500  p90 0.500  p99 0.500  mean 0.4833 s
thr = 0.20 × mean  =  0.0967 s  =  0.97 × P        ⇒  5P DAN PAST
```

Bu §18.4 ning `80–220 ms` derivatsiyasini **o'lchov bilan** tasdiqlaydi.

**`guard-recal` ning proxy'i o'zi da'vo qilganidan TIGHTER.** Hujjat
uni *"`D_probe` ning pastki chegarasi"* deb ataydi, chunki `W_stab`
tasdiqlash sharti kiritilmagan. **§18.3 bo'yicha oyna
DAVOMIYLIGINI chiqarish to'g'ri**, demak bu sababdan pastki chegara
**emas**. U pastki chegara faqat boshqa, ancha kuchsiz sababdan:
§4 ning 1-bandi `t_up` ni **kvalifikatsiya qiladigan** oynaning
birinchi probe'i deb talab qiladi, demak birinchi o'tgan probe'dan
keyin qayta buzilish bo'lsa haqiqiy `t_up` keyinroq bo'ladi.
O'lchangan 12 epizodda **har bir buzilish faqat `conn_refused` /
`a_conn`** edi va `b_response` / `c_progress` **nol marta** buzildi,
ya'ni qayta buzilish yo'q ⇒ **o'sha epizodlarda proxy = `D_probe`
aynan.**

#### Limb nima qiladi — o'lchangan raqamlar bilan

Pressure ostidagi **toza** `t_start` (`08` §15.3; n kichik — hujjat
§15.3 da `n = 7`, orkestrator jadvalida `n = 6`, **farq hal
qilinmadi**): `p50 = 2.83 s`, `p90 = 5.40 s`, `p99 = 7.20 s`.

```
D_probe(P2) ≈ RestartSec(0.1) + t_start + job overhead + kvantlash ≈ t_start + 0.2…0.3 s
            ⇒ p50 ≈ 3.1 s      ⇒  RMST(P2) ≈ 3…4 s   (τ = 8 s bilan chegaralangan)
Δ̂ ≈ RMST(P2) − RMST(P0) ≈ 3 s      vs      thr = 0.0967 s
                                   ⇒  Δ̂ ≈ 31 × thr
```

> **Demak limb *"fail-slow qo'llab-quvvatlanadi"* ni avtomatik beradi
> va 3 s kechikishni 0.2 s kechikishdan AJRATA OLMAYDI.** §19.3 ning
> **pastki degeneratsiyasi** o'lchov bilan tasdiqlandi: inkor shoxi
> erishib bo'lmaydigan, qo'llab-quvvatlash shoxi deyarli avtomatik.
> §11 ning fail-slow limbi — falsifikatsiya mezoni bo'lishi kerak
> edi — **hech narsani falsifikatsiya qilmaydi.**

**CHEKLOV — bu baho `P2` dan YUQORI dozada olingan.** `08` §3.7 ga
ko'ra nazoratsiz ramp **0.999 ga to'yinadi**, ya'ni `P2` ning
0.60–0.80 bandidan ancha yuqori. Demak `Δ̂ ≈ 3 s` — `P2` effektining
**yuqori** bahosi. Lekin hatto `10×` kichik bo'lsa ham (`0.3 s`) u
`thr` dan `3×` katta bo'lib qoladi, demak **xulosa bardoshli.**

### 21.4 QAROR — §18.8 (bog'lanmagan endpoint) javobni O'ZGARTIRMAYDI

Koordinator aniq so'radi: `D_eff` ning kvantlash poli pastroq, bu
javobni o'zgartiradimi? **Yo'q.**

| endpoint | `P0` dagi kattaligi | `thr = 0.20 × R` |
|---|---|---|
| `D_probe` | o'lchangan **0.483 s** | 0.097 s |
| `D_eff` | `P · n_failing` (o'lchangan 3–4 probe ⇒ **0.3–0.4 s**) + throughput integrali | ≈ 0.08–0.10 s |
| `D_sd` | §6.1: *"**ortiqcha kredit**"* ⇒ `D_probe` dan **kichik** | **< 0.097 s** |

**Uchala nomzod ham `P0` da sub-sekundli `R` beradi, demak
`thr ≈ 0.1 s` — hammasida.** `D_eff` ning afzalligi — **CI ni
toraytirishi**, lekin to'siq `Δ̂ ≈ 31 × thr` bo'lgani uchun torroq CI
*"qo'llab-quvvatlash"* ni **yanada aniqroq** qiladi, inkorni
erishiladigan qilmaydi. `D_sd` esa **yomonroq**.

> §18.8 **o'z sabablari bilan ochiq qoladi** (endpoint hali ham
> bog'lanmagan), lekin u §18.6 ning qarorini **keraksiz qilmaydi**.

### 21.5 QAROR — §17.5 ning qarori ham ZARUR

`08` §15.1 va §15.3 (toza o'lchov):

| band | n | p50 | **p90** | p99 | `≤ 0.8 s` (§17.2 shifti) |
|---|---|---|---|---|---|
| `P0` | 30 | 0.0394 | **0.0497** | 0.0643 | **30/30** — `16×` zaxira |
| pressure, toza | 6–7 | 2.8308 | **5.4042** | 7.1958 | **0/6** |
| pressure, kontaminatsiyalangan | 8 | 3.6492 | **4.8133** | 9.8586 | **0/8** |

`p90(t_start) = 5.40 s` — §17.2 ning `0.8 s` budjetidan **6.8×
katta**, va **ikki mustaqil o'lchovda** budjet ichida **bitta ham**
urinish yo'q.

> **§17.5 ning dizayn nuqsoni amalda bezarar EMAS. Qaror zarur.**

**Va bir yo'l yopiladi:** kechikish SUT ning **ichida emas** — uning
o'z `uptime_us` i `0.06–0.96 s`, `t_start` esa `1.67–7.20 s`, demak
vaqt `execve`, dinamik yuklash va reclaim throttling ostidagi
birinchi page fault'larga ketadi, `main()` ishga tushishidan **oldin**.
Ya'ni **SUT ni tezlashtirish nuqsonni tuzatmaydi**, va bu O1–O4 dan
qochish yo'lini **olib tashlaydi**. Bu §9.2 ning (i) va (iv)
mexanizmlarini **to'g'ridan-to'g'ri qo'llab-quvvatlaydi**.

### 21.6 FAKT — §16.11 ning GIPOTEZA'si endi FAKT: band 4 aldandi

§16.11 da shunday yozilgan edi: *"**GIPOTEZA (o'lchanMAGAN…)**:
systemd qayta ishga tushsa … `NRestarts` nolga qaytishi mumkin …
soxta VR."* `08` §8 buni **o'lchadi**:

| | oldin | keyin |
|---|---|---|
| `…-restarted` `NRestarts` | **2** | **0** |
| `…-virgin` `NRestarts` | **0** | **0** |
| `InvocationID` (ikkisi) | qo'yilgan | **BO'SH** |
| `LoadState` | loaded | `not-found`, `systemctl show` rc **0** |
| `pid1_starttime_ticks` | 282684 | **293478** |
| PID 1 yoshi | 9.75 s | **1.85 s — orqaga** |
| `boot_id` | — | **o'zgarmagan** |

`-virgin` unit'i namoyish: **`NRestarts` ikki chekkada ham `0` —
"o'zgarmadi" — holbuki oyna ichida PID 1 qayta ishga tushdi, unit
yo'q qilindi va jarayoni o'ldirildi. §4 ning 4-bandi qanoatlanadi va
bo'lmagan recovery VR deb hisoblanadi — SOXTA VR.**

#### QAROR — bandlarni yamamaymiz; marker PRESHART qilinadi

1. **§4 ning 3- va 4-bandlari — SHARTLI HAQIQIY:** ular faqat
   **PID 1 oyna ichida qayta ishga tushmagan** bo'lsa haqiqiy. Bu
   §4 ning matnini o'zgartirmaydi — u bandlarning **amal qilish
   shartini** qayd etadi. Bandlarni mustahkamlashga urinish
   **befoyda**: ular unit'ning o'z bookkeeping'ini o'qiydi, va
   `systemctl show` o'lgan unit uchun **default'larni `rc=0` bilan**
   qaytaradi (`08` §8; `01-muhit-tekshiruvlari.md` §4 ning dead-unit
   tuzog'i). O'lchov substrati yo'q qilinganda uni o'qib bo'lmaydi.
2. **§16.11 ning PID 1 marker'i — trial PRESHARTI**, invalidator emas:
   agar `pid1_starttime` trial ichida o'zgargan bo'lsa, §4 ning
   predikati **aniqlanmagan** ⇒ §20.2 bo'yicha **`vr = None`**,
   binar maxrajdan tashqarida, sabab nomlanadi.
3. **Va KM/log-rank'dan ham tashqarida** — `no_episode` dan keyin
   **ikkinchi** shunday kategoriya. Sabab boshqa: §1 bo'yicha
   monotonic qiymatlar **faqat bitta boot ichida** taqqoslanadi, va
   PID 1 restart'i bilan vaqt bazasining o'zi **haqiqiyligini
   yo'qotadi**, demak davomiylik **kuzatuv sifatida ham** yaroqsiz.
4. **Bo'sh `InvocationID` — ANIQLANMAGAN kuzatuv**, na
   *"o'zgarmadi"*, na *"o'qilmadi, o'tkazib yuboraman"*, na
   *"mos kelmadi"*. U 3-bandni **aniqlanmagan** qiladi ⇒ §20.2
   bo'yicha **`vr = None`**. Batafsil asos va qamrov — 21.6.1.

> **Nega "mos kelmadi" ham EMAS:** `08` §8 band 3 ni *"konservativ,
> agar implementatsiya bo'sh qiymatni «mos kelmadi» deb qabul
> qilsa"* deb bergan. **Men uni "mos kelmadi" deb qabul
> qilmayman** — bu kuzatilmagan narsaga `VR = false` yozish
> bo'lardi, ya'ni §16.2(B) olib tashlagan aynan o'sha xato,
> faqat teskari yo'nalishda. §20.2 ning **aniqlanganlik**
> printsipi **ikkala** noto'g'ri javobdan ham qochadi.

#### 21.6.1 Bo'sh `InvocationID` — qamrov, asos va shakl

**FAKT (orkestrator tasdiqlagan, main `0a83824` da; bu agent kodni
o'zgartirmaydi va o'qimadi — qator raqamlari xabardan):** uchala
iste'molchi ham bo'sh `InvocationID` ni **jimgina tashlaydi**:

| joy | kod | ta'siri |
|---|---|---|
| `revix/reduce.py:1006` | `{p.invocation_id for p in win if p.invocation_id is not None}` | VR oynasining invocation to'plami |
| `revix/reduce.py:2071` | `{p.invocation_id for p in trial.probes if p.invocation_id}` | bo'sh satrni **ham** tashlaydi |
| `revix/validate.py:671` | `_invocation_changed(...)`, `if p.invocation_id` filtri; `check_actions` (:657) ga boradi | §14.6(6) ning *"action → invocation o'zgarishi"* tekshiruvi |

> **Demak hozir "o'zgarmadi" va "yo'q" — har bir iste'molchi uchun
> AYNI BIR kuzatuv**, va §4 ning 3-bandi 4-bandning ko'r nuqtasini
> yopishi faqat implementatsiya qaysi birini ko'rayotganiga qarab
> hal bo'ladi. `guard-recal` o'lchadi: PID 1 restart'idan keyin
> yo'q qilingan unit'ning `InvocationID` i **yangi qiymat olmaydi,
> BO'SH bo'ladi** (`08` §8) — ya'ni amalda **eng xavfli** variant.

**IKKINCHI KO'RINISHI, VR dan tashqarida.** Bo'sh id bilan qayta
ishga tushgan unit **invocation o'zgarishini ko'rsatmaydi**, demak
xizmatni haqiqatan restart qilgan action **ta'sirsiz action** kabi
ko'rinadi. `validate.py` da bu **soxta
`action_without_invocation_change`** sifatida chiqadi — ya'ni
§14.6(6) invarianti **buzilgan deb** xabar beriladi, holbuki u
**baholanmagan**.

**ASOS — bu RULING, deduksiya emas.** §8.4(3) ning
*"Kuzatuv o'qilmasa (`None`) u jim deb hisoblanMAYDI"* qoidasi
**washout quiescence tekshiruvi** haqida yozilgan, §4 ning bandlari
haqida emas, demak uni bu yerga yoyish — **qaror**. Shuning uchun
u faqat o'sha analogiyaga **tayanmaydi**; ikki mustaqil asos:

1. **§4 ning o'z talabi.** Oyna davomida unit **tirik** bo'lishi va
   contract'dan o'tishi kerak (1–2 bandlar). Bo'sh `InvocationID`
   *"o'qilgan paytda unit tirik emas edi"* degani —
   `01-muhit-tekshiruvlari.md` §4 ning dead-unit tuzog'i
   (`systemctl show` o'lgan unit uchun default'larni `rc=0` bilan
   beradi). Probe'lar o'tgan, lekin unit tirik emas deb o'qilgan —
   bu **ichki ziddiyat**, demak kuzatuv **aniqlanmagan**, iхtiyoriy
   tomonga hal qilinadigan emas.
2. **§20.2 ning printsipi**, u allaqachon muzlatilgan: predikat
   aniqlanmasa `vr = None`.

**SHAKL (so'ralgan aniqlik):**

- **`reduce.py`** — bo'sh yoki `None` `InvocationID` o'lchanayotgan
  trial oynasi **ichida** uchrasa: uni invocation to'plamidan
  **tashlamaydi**, balki `vr = None` qiladi,
  `vr_reason = "invocation_id_unreadable"` bilan. §20.2 bo'yicha
  binar maxrajdan tashqarida, sabab nomlanadi.
- **`validate.py`** — xuddi shu holatda
  `action_without_invocation_change` **BERMAYDI**; o'rniga alohida
  topilma (`invocation_id_unreadable`) beradi va §14.6(6) ni
  o'sha action uchun **baholanmagan** deb belgilaydi.
  *Buzilgan* va *baholanmagan* bir xil xabar bilan berilmaydi.
- **Daraja** `(arm × pressure)` bo'yicha alohida beriladi,
  **instrumentatsiya yo'qolishi** sinfida (`probe_gap` bilan birga,
  §20.4), `no_episode` bilan **birlashtirilmaydi**.

**Munosabat 21.6(2) bilan:** bo'sh `InvocationID` ning o'lchangan
sababi — PID 1 restart'i, va uni **birinchi navbatda** marker
preshart'i tutadi. Bu qoida — **ikkinchi himoya chizig'i**:
marker biror sababdan o'tkazib yuborsa ham, soxta VR
yaratilmaydi. Ikkalasi **to'ldiruvchi**, ortiqcha emas — xuddi
§19.1 ning `boot_id` / marker juftligi kabi.

**CHEKLOV (`08` §8 dan ko'chirilgan):** bu **bitta** o'lchov, bitta
restart hodisasi; restart provokatsiya qilinmagan va sababi
nomlanib tasdiqlanmagan.

### 21.7 CHEKLOV — §9.4 ning invariantlari hozir majburlanmaydi: bu GATE, amendment emas

`08` §5 va §11: `--max-seconds 5` + `RuntimeMaxSec=7s` so'ralgan
epizod 0.35 chegarasidan yuqorida **16.3 s** turdi; faqat guard'ning
`cgroup.kill` i to'xtatdi. Demak §9.4 ning ikki invarianti —
`hold_s ≤ 12 s` va `hold_s + ramp_above_threshold_s ≤ 15 s` —
**bu asbob bilan bajarilmaydi**.

**Bu amendment talab qilMAYDI.** §9.4 ning invariantlari **haqiqiy
trial'ning preshartlari**: ularni buzgan epizod — trial **emas**,
balki protokol buzilishi. Demak invariantlar **to'g'ri qoladi**, va
bajarilmaydigan narsa — **asbob**. Qoida:

> **Generator §9.4 ning ikki invariantini majburlamaguncha hech
> qanday pilot trial o'tkazilmaydi.** Bu `00-pilot-topologiya.md` §6
> ning qadam tartibining davomi, yangi shart emas.

**Noqulay oqibati, ochiq yoziladi:** agar trial'lar bugun
o'tkazilsa, `aborted_guard` **qoida** bo'lib qolardi, va §12 ning
eksklyuziya darajasi — **hisobotga kiradigan NATIJA** — hodisadan
emas, **asbob nuqsonidan** belgilanardi. Va `08` §17 ga ko'ra guard
**birinchi trip'dan keyin boshqa o'ldirmaydi**, demak qolgan 119
trial **himoyasiz** — ya'ni `aborted_guard` birinchi trial'dan keyin
**kam hisoblanadi**, bu esa ko'p hisoblashdan **yomonroq**, chunki
**jimgina**.

**`ramp_above_threshold_s`:** `08` §11 uni `0.000 s` deb o'lchagan,
lekin **doza nol bo'lgan** konfiguratsiyada (`08` §3.4). Hujjatning
o'zi aytadi: bu raqam **pilotga ko'chirilmaydi**. **Tasdiqlanadi** —
§9.4 *"`ramp_above_threshold_s` kalibratsiyadan olinadi, taxmin
qilinmaydi"* deydi, va nol dozadagi qiymat kalibratsiya **emas**.

### 21.8 FAKT — `P2` fizik jihatdan erishiladigan, lekin USHLAB TURILMAGAN

`08` §3.6: `0.60–0.80` bandi **har bir toza pressured run'da**
ko'rindi (masalan `0.604–0.785`), lekin faqat nazoratsiz ramp
`0.999` ga to'yinish yo'lida o'tayotgandagi **0.6–0.9 s traversi**
sifatida.

Bu v1.5 §16.10 ning CHEKLOV'ini **aniqlashtiradi** (u *"`P2` hali
erishiladigan deb ko'rsatilMAGAN"* degan edi): endi **erishiladigan
deb ko'rsatildi**, lekin **ushlab turilgani ko'rsatilMADI**. §9.3
ning bandi **rad etilmadi va isbotlanmadi**.

Oqibati §10.1 uchun: `P2` hold qilinmasa, §9.4 ning *"analiz
ERISHILGAN pressure'dan foydalanadi"* qarori uzluksiz analizni
himoya qiladi, lekin **kategorik** uchinchi strata
**o'rnatilmagan** bo'lib qoladi — va 21.3 ning `Δ̂` bahosi aynan
shuning uchun `P2` dan yuqori dozada olingan.

### 21.9 FAKT — §15.3 ning guard asosi mustaqil tasdiqlandi

`08` §4.2: `user/lab` nisbati `p50 = 0.9963`, **642 toza
juftlashtirilgan namuna** bo'yicha, `02` §1 ning `0.996` iga
qarshi. Va `user@ some == user@ full` **har bir qatorda** — ya'ni
`02` §1 ning mexanizmi (PSI `full` faqat non-idle task'larni
hisoblaydi) **xulosa emas, bevosita o'lchov** bilan tasdiqlandi.

Demak oniy chegarali guard har bir `P2` trial'ini o'ldirardi va
**davomiylik kriteriyasi to'g'ri qoladi** — bu §15.3 ning guard'ni
majburiy saqlagan asosini **mustaqil ravishda** qo'llab-quvvatlaydi.

### 21.10 NIMA O'ZGARMAYDI

§18.2 ning referens qarori va §18.3 ning `t_up` anchor'i —
**o'zgarmadi**, 21.1 ularni **tasdiqlaydi**. §16.2(B), §17.4,
§20.2 — o'zgarmadi; 21.6 ularning **qo'llanishi**. §4 ning matni,
uning **3- va 4-bandlari**, §9.4 ning **ikki invarianti**, §9.3 ning
`P2` bandi, §11 ning ikkala limbi, `τ = 8 s`, `20%`,
`W_stab_pilot = 8 s`, `W_stab = 60 s`, `θ = 0.8`,
`injection_offset = 3 s`, `hold_cap_s = 12 s`,
`guard_sustain_s = 15 s`, `T_conn`/`T_rt` = 50 ms, `P` = 100 ms,
`k_f` = 3, `ε` = 32 MiB, quiescence 0.05, `T_q` = 5 s,
`T_w` = 15 s, `T_w_max` = 120 s, arm'lar `A`/`no_action`,
20 blok / 120 trial, §10.1, §10.2, §10.4, §12 ning **yopiq enum'i**,
§14, §15, §16, §17, §18, §19, §20 — **hammasi muzlatilgan holida.**
§13 ga tegilmadi.

**F1–F4 va O1–O4 tanlovlari QILINMADI.** 21.2 faqat *"qaror
kerakmi"* savoliga javob beradi — **ha, ikkalasi ham** — va
*"qaysi variant"* savolini **loyiha egasiga** qoldiradi.

Qo'shilgan narsa: OQ-12 ning rad etilishi, **o'z qabul qoidamning
tuzatilishi** (bir tomonlama → ikki tomonlama), ikki qarorning
zaruriyati o'lchov bilan, band 4 uchun **preshart qoidasi**, bir
gate (21.7) va uch FAKT (21.6, 21.8, 21.9).

### 21.11 NATIJA — yo'q

**Hech qanday eksperiment ishga tushirilmadi. Hech qanday natija yo'q.**
`guard-recal` ning o'lchovlari **guard va generator kalibratsiyasi**,
P1 trial'lari **emas** — `08` §14.3 ning o'z verdikti:
*"Pilot (120 trial) ishga tushirilishi mumkinmi? ❌ **HOZIR MUMKIN
EMAS**"*. Hech bir VR, `P(VR)`, downtime taqsimoti yoki
falsifikatsiya natijasi hisoblanmadi. 21.1(b) va 21.2 ning butun
arifmetikasi **muzlatilgan qiymatlardan**; 21.3 va 21.5 ning
raqamlari **boshqa agentning o'lchovidan** va shu sifatida
belgilangan.

---

## 22. §8.2 ning probe narxi: budjet va "arm'lar bo'yicha bir xil" (muzlatilgan)

> Bu bo'lim **v1.10 amendment** bilan qo'shildi. U **hech bir operatsion
> ta'rifni, metrikani, chegarani, statistik testni yoki falsifikatsiya
> mezonini o'zgartirmaydi.** U: (1) avval xabar qilingan budjet
> buzilishining **artefakt** ekanini qayd etadi, (2) kollizyaning
> **yo'q bo'lmaganini, torayganini** ko'rsatadi, (3) §8.2 ning
> *"arm'lar bo'yicha bir xil ushlanadi"* bandi **bajarilmaganini**
> qayd etadi va uni qanday o'qish kerakligini hal qiladi.

**Manba va provenans:** raqamlar `agent/prober` (yoki unga teng agent)
tomonidan o'lchangan va orkestrator xabari orqali keldi. **Bu agent
guest ichida hech narsa o'lchamadi va kodni o'qimadi.** 2-target
raqamlari **repo testidan emas, agentning scratchpad harness'idan** —
o'sha agent 2-target budjet assertion'ini **ataylab qo'shmagan**
(0.77–0.88% da flaky bo'lardi va flakiness signal emas, shovqin
bo'lardi). Mustaqil tasdiqlanmagan.

### 22.1 FAKT — avvalgi budjet buzilishi ARTEFAKT edi, va sababi qayd etiladi

Avval `1.238%` xabar qilingan edi (§8.2 ning `>1%` budjetidan yuqori).
**Bu noto'g'ri.** Sabab: `prober.cost_report()` `time.process_time()`
va `getrusage(RUSAGE_SELF)` ni o'qiydi — ikkisi ham **process bo'yicha**,
ya'ni barcha thread'lar yig'indisi. Test rig'i soxta SUT'ni
**prober'ning o'z processi ichida thread** sifatida ishlatgan, demak
SUT ning CPU'si prober'ga **yozilgan**.

| konfiguratsiya | 3 takror |
|---|---|
| SUT thread sifatida (eski rig) | 1.240 / 1.265 / 1.236 % |
| SUT alohida process (tuzatilgan) | 0.608 / 0.601 / 0.605 % |
| eski rig'da prober'ning **o'z thread'i** | 0.574 / 0.586 / 0.563 % |

Oxirgi ikki qator bir-biriga **mos**, demak izoh to'liq: xabar
qilingan raqamning ≈55% i testning o'z soxta xizmati edi.
Produksiyada prober `revixmon.slice` da **alohida process**, SUT esa
`revixlab.slice` da `sut.c` — demak process-CPU **o'sha yerda
to'g'ri o'lchov**; faqat rig noto'g'ri edi.

> **Metodologik qayd, saqlanishga arzigulik:** **o'z-o'zini
> perturbatsiyani o'lchaydigan asbobning o'zi o'zining test harness'i
> tomonidan perturbatsiya qilingan edi.** Bu §8.2 ning butun mavzusi
> — kuzatuvchining kuzatilayotganga qo'shilishi — va u o'lchov
> zanjirining **eng kutilmagan joyida** yuzaga chiqdi. Shuning uchun
> bu yerda yozilади, nafaqat tuzatiladi.

**Bu pre-registration'da hech narsani o'zgartirmaydi** va hech qanday
oldingi bo'lim bu raqamga tayanmagan (§21 probe narxini umuman
muhokama qilmaydi), demak **retraktsiya qilinadigan qaror yo'q**.

### 22.2 CHEKLOV — kollizya YO'Q BO'LMADI, TORAYDI

Budjet **sistematik** buzilmaydi. Lekin **produksiya
konfiguratsiyasida** — 2 target, SUT **va** bystander (§8.3,
`05-metodologiya.md` §5: bystander *"hech qachon fault
qilinmaydi"*) — o'lchangan:

```
2 target:  0.77 – 0.88 %     va  14 ta 8-sekundlik run'dan 1 tasi  1.007 %
pol (agar prober tomonidagi har bir Python qatori bepul bo'lsa): ≈ 0.49 %
  — §2 ning talab qilgan kernel ishi (har probe'ga yangi socket — (a) bandi,
    connect/send/recv/close) ≈ 53 %, muzlatilgan `P` pacing ≈ 9 %
```

> **Demak §8.2 ning `>1%` budjeti va §2 ning muzlatilgan
> `P = 100 ms` i birgalikda qanoatlantiriladi — lekin ≈0.15 pp
> zaxira bilan, va produksiya konfiguratsiyasida 14 run'dan 1 tasi
> chegaradan **o'tib ketdi**.**

**Nega bu hali ham kollizya:** §8.2 budjet buzilsa yagona remedy
beradi — *"**sekinlashtiriladi**"* — ya'ni probe davrini uzaytirish.
Lekin `P = 100 ms` **§2 da muzlatilgan**. Demak budjet produksiyada
oshsa, **§8.2 ning ruxsat etilgan remedy'si yo'q**: qolgan yo'llar
(a) probe'dagi ishni kamaytirish (kod, ta'rif emas — 22.8 ga qarang),
yoki (b) amendment.

**Qayd etiladi, gate QILINMAYDI:** buzilish `1/14` va u **margin**
masalasi, ta'rif masalasi emas; `0.49%` poli esa budjetning
**printsipial** erishiladigan ekanini ko'rsatadi. Lekin zaxira
**ingichka** va u **produksiya konfiguratsiyasida** ingichka —
ya'ni 1-target o'lchovlari bu xavfni **ko'rsatmaydi**. Har qanday
kelgusi o'lchov **2 target bilan** berilishi kerak.

### 22.3 FAKT — probe narxi arm'lar bo'yicha BIR XIL EMAS

8 takror × 6 s, 1 target, aralashtirilgan tartib:

| SUT holati | median | mean | sd |
|---|---|---|---|
| `ok` (sog'lom) | **0.601 %** | 0.606 | 0.032 |
| `silent` (`rt_timeout` / `conn_timeout`) | 0.480 % | 0.488 | 0.038 |
| `down` (`conn_refused`) | **0.433 %** | 0.450 | 0.055 |

Sog'lom target `down` dan **1.39×** qimmat, va farq har bir holatning
`sd` sidan **ancha tashqarida**. Mexanizm sodda: buzilgan probe
round-trip'ni, parse'ni va qator qurishning ko'p qismini **o'tkazib
yuboradi**.

**Nega bu bookkeeping emas:** arm'lar **konstruksiya bo'yicha**
downtime ulushi bilan farq qiladi. `no_action` — `Restart=no`,
clean crash'dan keyin trial oxirigacha down (§9.3), ya'ni **eng
ko'p downtime'li arm**, demak **eng kam instrumentatsiya yuki
ko'taradigan** arm. Va u aynan §8.2 ning **majburiy** nazorati,
vazifasi PSI atributsiyasi. Demak harness ikki arm'ni **turli
miqdorda** perturbatsiya qiladi, va **o'lchanayotgan narsa bilan
korrelyatsiyalangan yo'nalishda**.

### 22.4 QAROR — bandning o'qilishi: konfiguratsiya + O'LCHANGAN va HISOBOTGA KIRITILGAN yuk

§8.2 ning bandi, so'zma-so'z:

> *"**Probe narxi budjeti:** prober CPU'si trial bo'yicha
> **o'lchanadi**, yadro foizida **beriladi**. >1% bo'lsa
> **sekinlashtiriladi**. **Arm'lar bo'yicha bir xil ushlanadi**."*

**Matniy jihatdan** butun band **o'lchangan** registrda
(*o'lchanadi / beriladi / sekinlashtiriladi*), demak *"bir xil
ushlanadi"* ham eng tabiiy holda **o'sha o'lchangan kattalikka**
tegishli — ya'ni **amalga oshgan yuk**, konfiguratsiya emas.

**Lekin amalga oshgan yuk konstruksiya bo'yicha
QANOATLANTIRILMAYDI:** probe'ning narxi u **kuzatayotgan natijaga**
bog'liq (22.3). O'lik socket'ga qilingan probe'ni tirik socket'ga
qilingan probe bilan teng qilishning yagona yo'li — **ataylab CPU
yoqish**, ya'ni padding. Va padding §8.2 ning **o'z maqsadini
buzadi**: u differentsialni yo'qotish uchun **umumiy** harness
CPU'sini **oshiradi**, ya'ni o'z-o'zini perturbatsiyani kuchaytiradi.

**Shuning uchun ruling, uch bandli:**

1. **Konfiguratsiya bir xil bo'lishi SHART** — `hz`, `T_conn`,
   `T_rt`, `k_f`, bo'sh `frozen_deviation()`, bir xil target
   to'plami. **Bu qanoatlantirilgan** (o'lchangan va tasdiqlangan).
2. **Amalga oshgan yuk `(arm × pressure)` yacheykasi bo'yicha
   O'LCHANADI va HISOBOTGA KIRITILADI** — `prober_stop` allaqachon
   `cost` **va** `outcome_counts` ni olib yuradi, demak mexanizm
   ham qayta qurilади. **Hisobotda berilmasa, band bajarilmagan
   hisoblanadi.**
3. **Har qanday PSI-atributsiya da'vosi** (§8.2 ning o'z maqsadi;
   `05-metodologiya.md` §4 ning difference-in-differences i;
   `harm_indicator` / FR-B) **harness narxi differentsialini
   hisobga olishi yoki chegaralashi SHART.** Asbob qo'shgan narsa
   action'ga **yozilmaydi**.

> **Va ochiq yoziladi: bandning so'zma-so'z talabi — "amalga oshgan
> yuk bir xil" — BAJARILMAGAN va konstruksiya bo'yicha
> BAJARILMAYDI.** Yuqoridagi ruling uni **toraytiradi**: men
> *"bir xil"* ni *"bir xil konfiguratsiya + o'lchangan + hisobga
> olingan"* deb o'qiyapman. **Bu matnni toraytirish, demak loyiha
> egasi uni rad etishi mumkin** (22.7).

### 22.5 QAROR — differentsial QAYERDA tishlaydi va qayerda tishlamaydi

#### Birlamchi endpoint — strukturaviy himoyalangan, ikki sabab bilan

1. **§8.2 ning 1-bandi** harness'ni `revixmon.slice` ga qo'yadi va
   aytadi: *"**Kovariata sifatida ishlatiladigan hech bir scope
   ichida emas**"*. §7 ning **asosiy scope**'i —
   `revixlab.slice`. Demak prober'ning CPU'si — teng yoki teng
   emas — **birlamchi kovariataga umuman kirmaydi**. Qoldiq kanal:
   host darajasidagi CPU kontentsiyasi va host PSI (§7 bo'yicha
   **exploratory**).
2. **§16.2(A)**: §10.1 ning trend testi **arm `A` ichida**
   hisoblanadi. Demak `A` ↔ `no_action` farqi **birlamchi
   endpoint'ga kirmaydi**.

#### Arm `A` ICHIDA differentsial pressure bo'yicha qanday boradi

Bu muhim, va u **derivatsiya** (o'lchov emas): narx uptime ulushi
bilan o'sadi (22.3), uptime ulushi esa pressure bilan
**kamayadi** — bu aynan H1 ning o'z prognozi (§9.2). Demak arm `A`
ichida:

```
cost(A, P2)  <  cost(A, P1)  <  cost(A, P0)
```

ya'ni harness **eng kam** perturbatsiya qiladi **aynan recovery
eng qiyin bo'lgan** yacheykada.

| H1 holati | arm `A` ichida narx | ta'siri trend'ga |
|---|---|---|
| H1 **yolg'on** | pressure bo'ylab ~bir xil | **bias yo'q** |
| H1 **to'g'ri** | `P2` da **pastroq** ⇒ `P2` da kontentsiya **kamroq** | trend'ni **susaytiradi** ⇒ **H1 GA QARSHI** |

> **Ikkala holatda ham differentsial prognoz qilingan effektni
> YARATA OLMAYDI.** Birlamchi endpoint uchun mexanizm
> **konservativ**.

#### Atributsiya — mana shu yerda haqiqiy confound

§8.2 ning 4-bandi `no_action` ga vazifa beradi:
*"restart PSI ni oshirdi"* ni *"fault PSI ni oshirdi"* dan ajratish.
`05-metodologiya.md` §4: *"Action'ning PSI hissasi — mos keladigan
pressure'da **difference-in-differences**"*.

Arm `A` da prober **qimmatroq** (ko'proq uptime), demak `A` ning
o'lchangan yukida prober'ning **ortiqcha** CPU'si bor. Demak
`A − no_action` ayirmasi action'ga **ORTIQCHA YOZADI**:

> **Action'ning PSI narxi OSHIRIB ko'rsatiladi.** Ya'ni action
> haqiqatda bo'lgandan **zararliroq** ko'rinadi — va bu loyihaning
> o'z tezisiga (*pressure ostida action qimmat, shuning uchun
> PSI-gating foydali*) **MOS KELADIGAN** yo'nalish. **Bu noqulay
> yo'nalish va shuning uchun ochiq yoziladi.**

#### Magnitudasi — chegaralangan

Differentsial `0.601 − 0.433 = 0.168` pp, **bitta yadroning**
foizida, 1 target uchun. 2 target konfiguratsiyasida bystander
**hech qachon fault qilinmaydi**, demak uning komponenti
**konstanta** — swing faqat SUT target'idan keladi. O'lchangan
muhitda **12 CPU** (§15.1), demak `0.168` pp bitta yadroda
≈ `0.014%` umumiy CPU sig'imi. Va u **kovariata scope'idan
tashqarida** (§8.2 bandi 1).

> **Demak: magnitudasi KICHIK, lekin yo'nalishi TIZIMLI.**
> Xavf — kattalikda emas, **atributsiyaning sistematik
> siljishida**. Shuning uchun remedy **analitik** (o'lchash +
> hisobga olish), **operatsion emas** (tenglashtirish).

### 22.6 Bias yo'nalishini ochiq e'lon qilish

22.4 ning ruling'i bandni **toraytiradi**, demak u §8.2 ni
**zaiflashtiradi** — qat'iy talab (*"bir xil"*) hisobot talabiga
aylanadi. Yo'nalish:

- **Birlamchi endpoint uchun:** differentsialning o'zi
  **H1 ga qarshi** (22.5), demak uni tenglashtirmaslik H1 ga
  qarshi konservativ qolishni **saqlaydi** ⇒ ruling bu yerda
  **H1 ga qarshi**.
- **Atributsiya uchun:** differentsial action'ning PSI narxini
  **oshirib** ko'rsatadi, ya'ni **loyiha tezisi foydasiga**. Ruling
  uni **tenglashtirmaydi**, faqat **hisobga olishni talab qiladi**
  ⇒ agar hisobga olish bajarilmasa, **loyiha foydasiga** bias
  qoladi. **Shuning uchun 22.4(3) majburiy, tavsiya emas.**

**Buni bilib turib qabul qilaman**, chunki (i) so'zma-so'z talab
**fizik jihatdan bajarilmaydi** va padding §8.2 ning maqsadini
buzardi; (ii) differentsial **o'lchangan va qayta qurilishi
mumkin** (`cost` + `outcome_counts`), demak u **yashirin emas**;
(iii) hech qanday ma'lumot mavjud emas, demak qarorni natijani
ko'rib tanlash imkoniyati yo'q. **Agar hisobga olish bajarilmasa,
bu bias loyiha foydasiga qoladi — va aynan shuning uchun 22.4(3)
"SHART" deb yozilgan, "iloji bo'lsa" deb emas.**

### 22.7 Nima GATE qilinmaydi, va loyiha egasi nimani rad etishi mumkin

**Gate qilinMAYDI.** §17.5 va §18.6 dan farqli, bu yerda
**birlamchi endpoint xavf ostida emas** (22.5), differentsial
**konservativ** yo'nalishda, va magnitudasi **chegaralangan**.
Shuning uchun u **CHEKLOV va hisobot talabi**, pilotni
bloklaydigan qaror emas.

**Lekin egasi ikki narsani rad etishi mumkin, va ularni ochiq
qoldiraman:**

| # | mening o'qishim | alternativa va narxi |
|---|---|---|
| **C1** | *"bir xil"* = konfiguratsiya + o'lchangan + hisobga olingan (22.4) | *"bir xil"* ni **so'zma-so'z** o'qish ⇒ band **bajarilmaydi**, va yagona yo'l probe'ni **padding** qilish ⇒ umumiy harness CPU oshadi, §8.2 ning maqsadi **buziladi**. Men bu yo'lni **tavsiya qilmayman**, lekin tanlov egasining |
| **C2** | differentsial hisobotga kiritiladi, pilot bloklanmaydi | differentsialni **gate** deb hisoblash ⇒ pilot `P` yoki probe ishi o'zgarmaguncha kutadi ⇒ `P` **§2 da muzlatilgan** (22.2) |

### 22.8 OCHIQ MASALA — `csv.write` va zaxirani kengaytirish

`revix/schema.py` ning `csv.write` i **har probe narxining ≈10%**
i va u **ataylab tegilmagan** (fayl egasi boshqa agent). 22.2 ning
≈0.15 pp zaxirasi kengaytirilishi kerak bo'lsa, **bu eng katta
qolgan kamaytirilishi mumkin bo'lgan element**.

**Bu pre-registration masalasi emas** — `P` ham, budjet ham, §2
ning contract bandlari ham o'zgarmaydi; faqat probe'ning ichidagi
ish kamayadi. Shuning uchun u **amendment talab qilmaydi** va
22.2 ning kollizyasini **ta'rifga tegmasdan** yopishning yo'li.

**Ruled out sabab (qayd etiladi):** interpretator **emas** —
o'sha agent o'zining Python 3.14 ≈18% yomonroq degan bir-takrorli
taxminini **o'zi rad etdi** (run-to-run shovqin; ikkala
interpretator eski rig'da **aynan bir xil** yiqiladi va 3.13 bu
yerda **bir oz qimmatroq**).

### 22.9 NIMA O'ZGARMAYDI

§8.2 ning **matni** — o'zgarmadi, **to'rtala bandi ham**, shu
jumladan *"arm'lar bo'yicha bir xil ushlanadi"* va `>1%` budjeti.
§2 ning `P = 100 ms`, `T_conn`/`T_rt` = 50 ms va contract bandlari
(a)(b)(c) — o'zgarmadi. §7 ning asosiy scope'i, §16.2(A) ning arm
qamrovi, §9.3 ning arm'lari — o'zgarmadi. `θ = 0.8`, `τ = 8 s`,
`W_stab_pilot = 8 s`, `W_stab = 60 s`, `k_f` = 3,
`injection_offset = 3 s`, `hold_cap_s = 12 s`,
`guard_sustain_s = 15 s`, `ε` = 32 MiB, quiescence 0.05,
`T_q` = 5 s, `T_w` = 15 s, `T_w_max` = 120 s, 20 blok / 120 trial,
§10.1, §10.2, §10.4, §11 ning ikkala limbi, §12 ning yopiq enum'i,
§14, §15–§21 — **hammasi muzlatilgan holida.** §13 ga tegilmadi.

**F1–F4, O1–O4 va C1–C2 tanlovlari QILINMADI.**

Qo'shilgan narsa: bir artefaktning qaydi (22.1), bir torayган
kollizya (22.2), bir o'lchangan buzilish (22.3), bandning
o'qilishi va **uch majburiy talab** (22.4), qayerda tishlashining
tahlili (22.5), bias e'loni (22.6), va bir ochiq masala (22.8).

### 22.10 NATIJA — yo'q

**Hech qanday eksperiment ishga tushirilmadi. Hech qanday natija yo'q.**
22.1–22.3 ning raqamlari **boshqa agentning o'lchovidan** va shu
sifatida belgilangan; 2-target raqamlari **repo testidan emas**,
scratchpad harness'idan. 22.5 ning arm `A` ichidagi pressure
bo'yicha tartibi — **derivatsiya**, o'lchov emas, va u H1 ning o'z
prognoziga tayanadi. Bu agent guest ichida hech narsa o'lchamadi.
