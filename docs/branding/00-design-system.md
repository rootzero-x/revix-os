# 00 — REVIX Design System (v1.0)

> **Bu hujjat spetsifikatsiya**, kayfiyat tavsifi emas. `feature/gui` va kelajakdagi
> har qanday sirt (CLI, hujjat, figura, README) shuni amalga oshiradi. Mashina o'qiydigan
> nusxa: [`tokens.css`](tokens.css). Ikkisi ziddiyatda bo'lsa — **shu hujjat ustun**.
>
> Har qoida `NEGA:` bilan keladi. Sababi yo'q qoida keyingi odam tomonidan buziladi.
> Har raqam ham hisoblangan: §13 da nima tekshirilgani, nima **tekshirilmagani** yozilgan.

---

## 1. Asos: identitet nimaga to'g'ri bo'lishi kerak

REVIX — **o'lchov asbobi**: Linux xizmatini restart qilish uni haqiqatan tiklaydimi va bu
tizim pressure'iga qanday bog'liq, shuni o'lchaydi (`README.md`, "Loyiha nima").

Identitet quyidagilarga **to'g'ri bo'lishi shart**, aks holda yolg'on gapiradi:

| Loyiha aytadi | Manba | Identitet uchun oqibati |
|---|---|---|
| REVIX **adaptiv recovery ixtiro qilmaydi** | `README.md` "Loyiha nima EMAS"; `docs/research/04-novelty-statement.md` "Hissa NIMA EMAS" | "aqlli", "o'z-o'zini davolovchi", "AI" ohangi taqiqlanadi (§11) |
| "REVIX AI-powered" — **da'vo qilinmaydi** | `04-novelty-statement.md` jadvali | Logo/UI da miya, uchqun, neyron, "AI" belgisi yo'q |
| REVIX **Linux distributivi, desktop theme, cybersecurity toolkit va Kali moslashtirmasi emas** | `README.md` | Kali, "hacker", xavfsizlik estetikasi taqiqlanadi (§9) |
| `None` = **o'lchanmadi**, `0` dan farqli | `CONTRIBUTING.md` §4 | "not measured" alohida vizual til (`state-indicators.md`) |
| Hech qanday eksperiment ishga tushirilmagan, natija yo'q | `README.md` "O'lchangan holat" | UI boshlang'ich holati "n/r", hech qachon "0" yoki "OK" emas |
| P1 H2, arm C, host-wide pressure va boshqalar haqida **hech qanday da'vo qilmaydi** | `PREREGISTRATION.md` §0, §13 | UI bu narsalarni "tayyor" ko'rsatmaydi |
| Figura **oq-qora chop etishda ham o'qilishi kerak**; yo'q ma'lumot jim qolmaydi | `docs/architecture/04-driver-va-analiz-shartnomasi.md` §3, §3.1 | UI figuradan **zaifroq bo'lmasligi** kerak: rang yagona kanal emas (§4, §5) |

**Konsepsiya, bir gapda.** *Identitet — oscilloskop yoki laboratoriya stendi: qora yuza,
neytral kulrang matn, va faqat ikki signal rangi (qizil, yashil), ikkalasi ham hodisaning
ma'nosini bildirganda ishlatiladi, bezak sifatida emas.*

**NEGA oscilloskop, "terminal" emas:** terminal estetikasi (yashil-qora, prompt) — aynan
"hacker vositasi" belgisi; loyiha esa buni rad etadi. O'lchov asbobi esa ko'rinish bilan
emas, **ko'rsatishi mumkin bo'lgan narsaning chegarasi** bilan ishonch qozonadi: shuning
uchun "ko'rsatilmagan" holati (n/m, n/r) identitetning markaziy elementi.

---

## 2. Palitra

Berilgan qiymatlar o'zgartirilmagan. Tokenlar **ma'no bo'yicha** nomlanadi.
(§12 da berilgan qiymatlar bo'yicha topilmalar — ikkita qizil va ikkita yashil
orasidagi tanlov ham shu yerda asoslanadi.)

### 2.1 Yuzalar (dark — asosiy sirt)

| Token | Hex | Vazifasi |
|---|---|---|
| `--rx-bg-0` | `#080808` | canvas: sahifa, terminal foni |
| `--rx-bg-1` | `#0F0F0F` | panel, karta |
| `--rx-bg-2` | `#151515` | ko'tarilgan: input, jadval qatori, hover |

**NEGA uch pog'ona:** panel va canvas ajralishi kerak. **Lekin** pog'onalar orasidagi
kontrast 1.045 (`bg-0`/`bg-1`), 1.050 (`bg-1`/`bg-2`), 1.097 (`bg-0`/`bg-2`) — ya'ni
ko'zga deyarli ko'rinmaydi. **Qoida:** yuza chegarasi faqat ohang farqiga tayanmaydi;
ajratuvchi `--rx-border` (1 px) majburiy (§7).

### 2.2 Neytrallar

| Token | Hex | Vazifasi | Faqat shu vazifa |
|---|---|---|---|
| `--rx-fg-0` | `#FFFFFF` | urg'u: bosh qiymat, sarlavha, **focus ring** | matn + focus |
| `--rx-fg-1` | `#D4D4D4` | asosiy matn | matn |
| `--rx-fg-2` | `#888888` | ikkilamchi matn (birlik, label), **ma'noli outline** | matn + outline |
| `--rx-line` | `#444444` | hairline, bezak | **MATN EMAS, ma'noli outline EMAS** |

**NEGA `--rx-line` matn emas:** `#444444` `bg-0` da **2.06:1**, `bg-2` da **1.87:1** —
matn uchun 4.5:1 va grafik element uchun 3:1 chegaralarining ikkalasidan past (§3).
U faqat "olib tashlasangiz ham ma'no yo'qolmaydigan" hairline uchun. Ma'no tashiydigan
chiziq (masalan, "not run" ning punktir ramkasi) **`--rx-fg-2`** bilan chiziladi.

### 2.3 Signal ranglari — faqat ma'no (qoidalar: §5)

| Token | Hex | Vazifasi |
|---|---|---|
| `--rx-fail` | `#FF3B30` | failure: **matn, glyph, outline** |
| `--rx-fail-solid` | `#E53935` | failure: to'ldirilgan yuza (ustiga `--rx-on-signal`) |
| `--rx-ok` | `#22C55E` | verified: **matn, glyph, outline** |
| `--rx-ok-solid` | `#00C853` | verified: to'ldirilgan yuza (ustiga `--rx-on-signal`) |
| `--rx-on-signal` | `#080808` | signal "solid" yuzasi ustidagi matn |

Berilgan to'rtta hex (`#E53935 / #FF3B30`, `#00C853 / #22C55E`) ikkitadan ikki rolga
bo'lindi. Asoslash: §12.1 (qizil), §12.2 (yashil).

**NEGA `--rx-on-signal` qora, oq emas:** oq matn `#E53935` ustida **4.23:1** (4.5 dan past),
`#00C853` ustida **2.24:1**. Qora (`#080808`) `#E53935` ustida 4.74:1, `#00C853` ustida 8.95:1.

### 2.4 Yorug' sirt / chop etish (berilgan palitraga QO'SHIMCHA)

Berilgan palitra faqat dark uchun. Lekin loyihaning figuralari va hujjatlari **oq qog'ozda**
chop etiladi (`04-driver-va-analiz-shartnomasi.md` §3), shuning uchun minimal qo'shimcha kerak:

| Token | Hex | Qog'ozda kontrast | Vazifasi |
|---|---|---|---|
| `--rx-paper` | `#FFFFFF` | — | qog'oz |
| `--rx-ink` | `#080808` | 20.03:1 | asosiy matn |
| `--rx-ink-2` | `#444444` | 9.74:1 | ikkilamchi matn |
| `--rx-fail-ink` | `#A62926` | 7.08:1 | failure matni |
| `--rx-ok-ink` | `#00672B` | 7.06:1 | verified matni |

**NEGA qo'shildi:** berilgan qiymatlar oq qog'ozda matn bo'la olmaydi — `#00C853` **2.24:1**,
`#22C55E` 2.28:1, `#FF3B30` 3.55:1, `#E53935` 4.23:1, `#888888` 3.54:1. `-ink` qiymatlari
berilgan ranglarni qoramaytirish (har kanalni bir xil ko'paytirish) bilan olingan,
7:1 ga yetguncha; yangi hue kiritilmagan. `--rx-ink-2` (`#444444`) — berilgan neytral:
qog'ozda `#888888` o'rniga ishlatiladi.

---

## 3. Kontrast — hisoblangan qiymatlar

Formula: WCAG 2.x relative luminance, `(L1 + 0.05) / (L2 + 0.05)`. Hammasi Python bilan
hisoblangan (sRGB → linear → `0.2126 R + 0.7152 G + 0.0722 B`).
Chegaralar: oddiy matn **4.5:1** (WCAG 1.4.3), grafik/UI element **3:1** (WCAG 1.4.11).

### 3.1 Matn va glyph, dark yuzalarda

| Token | Hex | `bg-0` `#080808` | `bg-1` `#0F0F0F` | `bg-2` `#151515` | matn (4.5) |
|---|---|---|---|---|---|
| `--rx-fg-0` | `#FFFFFF` | 20.03 | 19.17 | 18.26 | o'tadi |
| `--rx-fg-1` | `#D4D4D4` | 13.51 | 12.93 | 12.32 | o'tadi |
| `--rx-fg-2` | `#888888` | 5.65 | 5.41 | 5.15 | o'tadi |
| `--rx-line` | `#444444` | **2.06** | **1.97** | **1.87** | **o'tmaydi** (3:1 ham yo'q) |
| `--rx-fail` | `#FF3B30` | 5.65 | 5.40 | 5.15 | o'tadi |
| `--rx-fail-solid` | `#E53935` | 4.74 | 4.53 | **4.32** | `bg-2` da **o'tmaydi** |
| `--rx-ok` | `#22C55E` | 8.79 | 8.41 | 8.01 | o'tadi |
| `--rx-ok-solid` | `#00C853` | 8.95 | 8.57 | 8.16 | o'tadi |

### 3.2 Solid yuza va ustidagi matn

| Yuza | `--rx-on-signal` `#080808` | oq `#FFFFFF` |
|---|---|---|
| `--rx-fail-solid` `#E53935` | 4.74 (o'tadi) | 4.23 (**o'tmaydi**) |
| `--rx-fail` `#FF3B30` | 5.65 | 3.55 (**o'tmaydi**) |
| `--rx-ok-solid` `#00C853` | 8.95 | 2.24 (**o'tmaydi**) |
| `--rx-ok` `#22C55E` | 8.79 | — (2.28 oqda) |

### 3.3 Boshqa o'lchanganlar

| Nima | Qiymat |
|---|---|
| Focus ring `#FFFFFF` / `bg-0` | 20.03:1 |
| "not run" punktir ramkasi `#888888` / `bg-0`, `bg-2` | 5.65, 5.15 (3:1 chegarasidan yuqori) |
| "not measured" shtrix chiziqlari `#888888` / `bg-1` | 5.41 |
| Selection: `#FFFFFF` / `#444444`; `#D4D4D4` / `#444444`; `#888888` / `#444444` | 9.74; 6.57; **2.75** |

---

## 4. Monoxrom chop etish va rang ko'rligi

### 4.1 Faqat yorqinlik (monoxrom) — o'lchangan

CIE L\* (0–100) berilgan ranglar uchun:

| Rang | Hex | L\* |
|---|---|---|
| oq | `#FFFFFF` | 100.0 |
| neytral 300 | `#D4D4D4` | 84.9 |
| yashil | `#00C853` / `#22C55E` | 70.8 / 70.2 |
| neytral 500 | `#888888` | 56.7 |
| **qizil** | **`#FF3B30`** | **56.7** |
| qizil | `#E53935` | 51.7 |
| neytral 700 | `#444444` | 28.9 |

**Topilma:** `#FF3B30` va `#888888` bir xil L\* ga ega (56.7; relative luminance 0.2460 va
0.2462, ya'ni kontrast **1.00:1**). Monoxrom chop etishda qizil failure matni va kulrang
ikkilamchi matn **bir xil kulrang** bo'ladi. `#E53935` bilan farq 5 L\* birlik (kontrast
1.19:1) — ham yetarli emas. Qizil va yashil orasi: relative-luminance kontrasti
**1.56–1.89:1** (to'rt juftlikda).

**Xulosa (qoida):** **rang hech qachon yagona kanal emas.** Har holat glyph shakli +
matn yorlig'i bilan ham aytiladi. `state-indicators.svg` ning ikkinchi bloki aynan shu
sinov: har rang unga **teng luminance'li kulrangga** almashtirilgan (yashil → `#ACACAC`,
qizil → `#888888`), va yetti holat baribir shakl bilan ajraladi. Bu **simulyatsiya**;
haqiqiy printerda chop etilmagan.

**NEGA:** loyihaning o'z figuralari marker/chiziq turi bilan farqlanadi, "faqat rang bilan emas"
(`04-driver-va-analiz-shartnomasi.md` §3). Interfeys shu intizomdan past tushsa, ekran
skrinshoti maqolaga qo'yilganda ma'no yo'qoladi.

### 4.2 Rang ko'rligi simulyatsiyasi

Machado va boshq. (2009) matritsalari (severity 1.0), linear RGB da. **Ehtiyot:** matritsalarni
men **xotiradan** kiritdim va ma'lumotnoma implementatsiyasi bilan solishtirmadim;
natijalar sifat jihatidan ma'lum xatti-harakatga (qizil/yashil zaytun-sariqqa yaqinlashadi)
mos keladi, lekin aniq raqamlar **tasdiqlanmagan**. ΔE — CIE76 (oddiy Lab masofasi).

| Juftlik | oddiy ko'rish ΔE | protanopia ΔE / lum. kontrast | deuteranopia ΔE / lum. kontrast | tritanopia ΔE / lum. kontrast |
|---|---|---|---|---|
| `--rx-fail` `#FF3B30` vs `--rx-ok` `#22C55E` | 134.5 | 29.7 / 2.47 | **23.4 / 1.22** | 134.7 / 1.74 |
| `--rx-fail-solid` `#E53935` vs `--rx-ok-solid` `#00C853` | 132.4 | 42.1 / 2.92 | **14.4 / 1.48** | 134.7 / 1.83 |

Deuteranopia simulyatsiyasida qizil va yashil ΔE ≈ 132–135 dan **14–23 ga** tushadi,
yorqinlik kontrasti **1.22–1.48:1**. Ya'ni qizil/yashil juftligi ko'plab foydalanuvchi uchun
rang bilan ajralmaydi. Palitrada sariq/ko'k yo'q (restraint), shuning uchun yechim —
rang almashtirish emas, **qo'shimcha kanal**: glyph shakli, matn, naqsh (`state-indicators.md`).

---

## 5. Qizil va yashil qachon ishlatiladi

Asosiy g'oya: **qizil va yashil — hodisaning (observation event) ma'nosi, natijaning
baholashi emas.** Loyiha FAKT / NATIJA / TALQINni ochiq ajratadi (`README.md`, "Ilmiy
yaxlitlik"); rang ham shu chegaradan o'tmaydi.

### 5.1 Yashil (`--rx-ok`, `--rx-ok-solid`) — **faqat** quyidagilar

| # | Yashil bo'lishi mumkin | Manba |
|---|---|---|
| G1 | **verified recovery** (VR) bajarilgan epizod holati | `PREREGISTRATION.md` §4 |
| G2 | **`healthy`** holati, `state-indicators.md` ta'rifi bo'yicha | — |
| G3 | `revix doctor` / validator tekshiruvi **PASS** | `revix/cli.py` (`PASS/WARN/FAIL`) |

**Y1 — Predicate nomi yoniga yoziladi.** Yashil element yonida *nima tasdiqlangani*
yozilgan bo'lishi shart (`VR`, `contract ok`, `15 PASS`). Predicate'siz yashil nuqta — taqiq.
**NEGA:** loyihaning butun hissasi — "process tirik" va "tiklandi" bir narsa emas
(`PREREGISTRATION.md` §4, 5-band: *"5% throughput'da ishlayotgan xizmat recovered emas"*).
Predicate'siz yashil nuqta aynan shu xatoni takrorlaydi: "ishlayapti" ni "tiklandi" deb ko'rsatadi.

**Y2 — Liveness yolg'iz o'zi yashil emas.** `ActiveState=active`, "running", "connected",
"online" — neytral (`--rx-fg-1`). **NEGA:** Y1 bilan bir sabab; aks holda yashil
`F_sd` detektorining "hamma narsa yaxshi" holatini VR sifatida ko'rsatadi.

**Y3 — Yashil matn bloki emas.** Yashil: bitta token (glyph, tag, bitta so'z) darajasida.
Abzats, jadval qatori to'liq, yoki terminal default foreground yashil bo'lmaydi.
**NEGA:** yashil-qora to'liq matn — "hacker terminal" ning eng ravshan belgisi (§9, F4).
Kam ishlatilgan yashil esa "diqqat qil" signali bo'lib qoladi.

### 5.2 Qizil (`--rx-fail`, `--rx-fail-solid`) — **faqat** quyidagilar

| # | Qizil bo'lishi mumkin | Manba |
|---|---|---|
| R1 | **`failed`** holati: contract buzilgan va tiklanmagan (aniq aniqlangan) | `PREREGISTRATION.md` §3, §4 |
| R2 | `revix doctor` / validator **FAIL** | `revix/cli.py` |
| R3 | **Guard ishga tushdi / xavfsizlik to'xtatish** — jonli ogohlantirish banneri | `README.md` "Xavfsizlik ogohligi"; `PREREGISTRATION.md` §12 (`aborted_guard`) |
| R4 | **Xavfli amal tasdig'i**: pressure eksperimentini ishga tushirish (desktop sessiyani o'ldirishi mumkin) | `README.md` "Xavfsizlik ogohligi" |
| R5 | **Host xavfsizlik ogohligi**: `systemd-oomd` kill authority bilan qurollangan | `README.md` "Xavfsizlik ogohligi" |

**Q1 — R4 tugmasi yagona qizil solid.** Xavfli amal tugmasi `--rx-fail-solid` + `--rx-on-signal`,
matni **aniq oqibatni** aytadi, va u **default focus emas**.
**NEGA:** qizil rang kam ishlatilsagina "to'xta" ma'nosini saqlaydi; oqibat matnda yozilmasa,
rang "xavfli" demaydi, faqat "diqqat" deydi.

**Q2 — Guard ishga tushishi (R3) va natija holati farqlanadi.** Jonli banner — qizil
(**kritik ogohlantirish**). Lekin o'sha trial'ning *natija holati* `isolated` (neytral), chunki
`aborted_guard` — xizmatning hukmi emas, eksklyuziya sababi; uning ulushi **natija sifatida**
beriladi, yashirilmaydi (`PREREGISTRATION.md` §12). **NEGA:** qizil bilan ko'rsatilgan
eksklyuziya jadvaldagi "yomon xizmat" kabi o'qiladi, holbuki bu asbob chegarasining ko'rsatkichi.

### 5.3 Qizil ham, yashil ham **bo'lmaydigan** narsalar

| # | Neytral qoladi | NEGA |
|---|---|---|
| N1 | **Statistik natija**: `P(VR \| PSI)`, effect size, `p`, CI, **FR-A nisbati**, eksklyuziya ulushi | Natija — o'lchangan raqam; "yaxshi/yomon" — talqin (`PREREGISTRATION.md` §0). Rang talqinni natijaga jimgina yopishtiradi |
| N2 | **Gipoteza hukmi** (H1/H2 "tasdiqlandi", "rad etildi", "null") | **Manfiy natija yashirilmaydi** (`README.md`). H1 null bo'lsa, u qizil "muvaffaqiyatsizlik" emas — natija. H1 tasdiqlansa, yashil "g'alaba" emas |
| N3 | `recovering`, `degraded`, `isolated` | Bular tasdiqlanmagan va failed ham emas; ularga signal rangi berish ularni "yaxshi" yoki "yomon" toifaga joylaydi (`state-indicators.md`) |
| N4 | **`not measured`, `not run`** | Yo'qlik ma'lumot emas. Qizil — "o'lchandi va yomon" ni, yashil — "o'lchandi va yaxshi" ni bildirar edi. Ikkalasi ham yolg'on |
| N5 | Diff, log darajalari, sintaksis ranglari (loyiha UI ichida) | Ular failure/verified emas; terminal ANSI esa qoida bilan cheklangan (`terminal-theme.md` §2) |
| N6 | Dekor: logo, sarlavha, hover, border, fon, illyustratsiya | Dekorativ qizil/yashil ma'noni **suyultiradi**: hamma joyda ko'rinadigan qizil "failure" demaydi |

### 5.4 Rang yagona kanal bo'lmaydi

**C1.** Qizil/yashil bilan bo'yalgan har element **glyph shakli + matn yorlig'i** bilan ham
aytiladi (`state-indicators.md`). Rangni olib tashlasangiz ma'no qolishi shart.
**NEGA:** §4: monoxrom chop etishda `#FF3B30` = `#888888` (1.00:1) va deuteranopiyada qizil/yashil
ΔE 14–23 ga tushadi. Rang yagona tashuvchi bo'lsa, ma'no yo'qoladi.

**C2.** Signal rangining **to'ldirilgan yuzasi** ustida faqat `--rx-on-signal`.
**NEGA:** §3.2: oq matn `#E53935` da 4.23:1, `#00C853` da 2.24:1.

**C3.** Qog'ozda / yorug' sirtda `-ink` qiymatlari (§2.4), hech qachon dark tokenlar.
**NEGA:** `#00C853` oqda 2.24:1.

---

## 6. Tipografiya

Tashqi font **yo'q** (`@font-face`, CDN, Google Fonts — hech biri).
**NEGA:** loyiha privilegiyasiz, portativ, oflayn o'lchov benchmark'i (`README.md`, "Talablar");
tashqi resursga bog'liq interfeys bu prinsipni buzadi va izolyatsiyalangan guest'da ishlamaydi.

| Token | Qiymat |
|---|---|
| `--rx-font-mono` | `ui-monospace, "Cascadia Mono", "DejaVu Sans Mono", Consolas, Menlo, monospace` |
| `--rx-font-sans` | `system-ui, -apple-system, "Segoe UI", "DejaVu Sans", Arial, sans-serif` |

**Qoida F-1:** raqamlar, holat teglari, vaqtlar, identifikatorlar, CLI, jadval qiymatlari —
`--rx-font-mono`. Abzats va navigatsiya — `--rx-font-sans`.
**NEGA:** o'lchov qiymatlari ustunlarda tekislanishi va `0` bilan `O`, `1` bilan `l` aralashmasligi kerak.

**Qoida F-2:** har raqamli yuzada `font-variant-numeric: tabular-nums` (`--rx-numeric`).
`font-feature-settings: "zero"` (o'tkazilgan nol) **so'raladi**; shrift uni qo'llab-quvvatlashi
**tekshirilmagan**, shuning uchun unga tayanilmaydi.
**NEGA:** "0" va "o'lchanmadi" hech qachon aralashmasligi kerak (`CONTRIBUTING.md` §4).

### Shkala (qadamlar qat'iy, modulyar nisbat emas)

| Token | px | Vazifasi |
|---|---|---|
| `--rx-text-label` | 12 | UPPERCASE label, birlik, caption (`--rx-tracking-label: 0.08em`) |
| `--rx-text-body` | 14 | asosiy matn, jadval ma'lumoti |
| `--rx-text-lead` | 16 | bo'lim sarlavhasi |
| `--rx-text-title` | 20 | sahifa sarlavhasi |
| `--rx-text-figure` | 28 | asosiy raqam |
| `--rx-text-display` | 40 | faqat boot screen / bo'sh holat |

Yo'nalish: `--rx-leading-body: 1.5`, `--rx-leading-tight: 1.2`. Og'irlik: `400` va `600`.
**12 px dan kichik matn yo'q. 700+ og'irlik yo'q.**
**NEGA:** kichik, ingichka matn qorong'i yuzada yorug'lik tarqalishi sababli o'qilishi qiyin;
ikki og'irlik — restraint: tartib sarlavha emas, o'lcham va joylashuvdan keladi.

---

## 7. Spacing, shakl, chegara

| Token | Qiymat |
|---|---|
| `--rx-space-1 … -8` | 4, 8, 12, 16, 24, 32, 48, 64 px |
| `--rx-radius` | **2 px maksimum** (0 afzal) |
| `--rx-border` | `1px solid var(--rx-line)` (hairline, bezak) |
| `--rx-border-strong` | `1px solid var(--rx-fg-2)` (ma'noli chegara) |
| `--rx-focus` | `2px solid var(--rx-fg-0)`, offset 2 px |
| `--rx-row-height` | 32 px |

- **Qoida S-1:** spacing 4 px asosiga ko'paytma. **NEGA:** ritm — asbob paneli kabi tartib hissi.
- **Qoida S-2:** `border-radius > 2px`, pill, dumaloq tugma — taqiq. **NEGA:** yumaloq shakl iste'molchi
  / bolalarcha UI belgisi (§9, F1).
- **Qoida S-3:** soya yo'q (`box-shadow`, `text-shadow`, `filter: drop-shadow` — hech biri). Ko'tarilish
  `--rx-bg-2` + `--rx-border`. **NEGA:** soya glow'ga aylanadi (§9, F5) va qorong'i yuzada ko'rinmaydi.
- **Qoida S-4:** focus ring faqat oq (`--rx-fg-0`), rangli emas va glow emas.
  **NEGA:** qizil/yashil ma'no uchun band (§5); oq `bg-0` da 20.03:1.

---

## 8. Komponent qoidalari (GUI uchun minimal)

- **K-1. Jadval — asosiy shakl.** Qator balandligi `--rx-row-height`; raqamlar o'ngga, matn chapga;
  birlik ustun sarlavhasida yoki qiymat yonida. **NEGA:** o'lchov asbobi — ko'rsatkichlar paneli,
  kartochkalar galereyasi emas.
- **K-2. Birliksiz raqam yo'q.** Vaqt qiymati birligini ko'rsatadi; birlik e'lon qilinmagan bo'lsa
  *"time unit not declared"* deb yoziladi va **taxmin qilinmaydi**.
  **NEGA:** `04-driver-va-analiz-shartnomasi.md` §3.1 (`time_unit` yo'q → o'q birliksiz, taxmin yo'q).
- **K-3. Noaniqlik raqam bilan birga.** CI bor bo'lsa — yoniga; CI darajasi e'lon qilinmagan
  bo'lsa *"CI level not declared"*; hisoblanmagan bo'lsa *"CI not computed"*, **error bar chizilmaydi**.
  **NEGA:** §3.1 shartnomasi: jim qisqartirilgan figura to'liq figura kabi ko'rinadi.
- **K-4. Yo'q ma'lumot jim qolmaydi.** Ko'rsatilmagan qiymat — "not measured" yoki "not run"
  (`state-indicators.md`), sabab bilan. Bo'sh katak, `0`, `-`, `N/A`, yashirin qator — taqiq.
  **NEGA:** `None` = o'lchanmadi (`CONTRIBUTING.md` §4); jim yo'qotish natijaga aylanadi
  (`PREREGISTRATION.md` §4: "instrumentatsiya yo'qolishi hech qachon jimgina natijaga aylanmaydi").
- **K-5. Egri chiziq yo'q ma'lumot orqali o'tmaydi.** Chiziq grafikda yo'q nuqtalar orasi
  **birlashtirilmaydi** (§3.1: "birlashtiruvchi chiziq yo'q").
  **NEGA:** interpolyatsiya o'lchanmagan oraliqni o'lchangan kabi ko'rsatadi.
- **K-6. Yuklanmoqda holati — matn.** Spinner, skeleton shimmer, progress animatsiyasi yo'q;
  "recovering" uchun `elapsed / W_stab` — oddiy raqam. **NEGA:** §9, F3.

---

## 9. Taqiqlanganlar

Har biri **aniq** taqiq, "iloji boricha" emas.

| # | Taqiq | NEGA |
|---|---|---|
| **F1** | **Bolalarcha UI**: pill/dumaloq shakl (`radius > 2px`), emoji interfeysda, mascot, o'yinchoq illyustratsiya, ovozli undov ("Hooray!", "Oops!"), kamalak ranglar | Tadqiqot instrumenti iste'molchi ilovasi emas; ohang xato bo'lsa, natijaga ishonch kamayadi |
| **F2** | **Ortiqcha gradient**: bu spetsifikatsiyada gradient **yo'q**. *Yagona istisno:* `--rx-hatch` — qattiq to'xtash nuqtalari bilan takrorlanuvchi diagonal chiziq naqshi (CSS gradient sintaksisi, lekin vizual silliq o'tish emas) | Gradient — iste'molchi va "futuristik" belgi; shuningdek ma'lumotsiz hajm tuyg'usi beradi |
| **F3** | **Keraksiz animatsiya**: `transition`, `animation`, spinner, pulse, blink, typewriter yozuv, skeleton shimmer, parallaks. **Animatsiyaga ruxsat berilgan holat yo'q** | Qiymat o'zgarishi o'zi ma'lumot; unga effekt qo'shish "tirik tizim" taassurotini beradi, bu esa o'lchov asbobi uchun yolg'on gap (tizim hech narsa "qilmayapti", o'lchayapti). Shuningdek `n/m` va `n/r` holatlari harakatsiz bo'lishi shart |
| **F4** | **Soxta-hacker estetikasi**: matritsa yomg'iri, aylanuvchi hex, soxta progress ("Hacking…"), "ACCESS GRANTED", bosh suyagi, kapyushonli figura, yashil-qora **to'liq** terminal fon, soxta raqamlar oqimi | README: REVIX cybersecurity toolkit emas. Soxta-hacker belgilari aynan shu da'voni yaratadi. Soxta raqamlar oqimi esa to'g'ridan-to'g'ri **"o'lchanmagan qiymatni o'lchangan kabi ko'rsatma"** qoidasini buzadi |
| **F5** | **Neon / kiberpank**: to'yingan siyan, magenta, binafsha, har qanday palitradan tashqari hue | Palitra — qora + qizil + yashil + neytral. Boshqa hue ma'noni suyultiradi (§5). Neon — kiberpank estetikasi |
| **F6** | **Glow**: `box-shadow` blur, `text-shadow`, `filter: drop-shadow/blur`, "neon chiziq", yorug'lik nuri | F5 bilan bir sabab; qorong'i yuzada glow matn o'qilishini ham buzadi |
| **F7** | **Kali Linux brendiga o'xshash narsa**: ajdaho (yoki boshqa hayvon) belgisi, qora-ko'k ranglar juftligi, "K" shaklidagi glif, qurol-yarog' toifasi ikonlari to'ri, Kali wallpaper uslubi | README ataylab "Kali moslashtirmasi emas" deydi, **va muhit WSL2 Kali** (`README.md` "O'lchangan holat"): shu sharoitda bitta logo butun ogohlantirishni bekor qilishi mumkin. Identitet **ko'k hue ishlatmaydi** |
| **F8** | **Xavfsizlik ikonografiyasi**: qalqon, qulf, kalit, bosh suyagi, "shield" belgisi | REVIX xavfsizlik vositasi emas. Qalqon "himoya qiladi" demoqchi bo'ladi; REVIX hech narsani himoya qilmaydi, o'lchaydi |
| **F9** | **Terminal-prompt belgisi** (`>_`, `$`, `❯`) logo yoki ikon sifatida | Eng ko'p ishlatilgan "dasturchi" klishesi; belgi o'lchov mavzusidan olinishi kerak (§10) |
| **F10** | **"AI / aqlli / o'z-o'zini davolovchi" ikonografiyasi**: miya, uchqun, neyron to'ri, robot | `04-novelty-statement.md`: "REVIX AI-powered" — da'vo qilinmaydi (v1 rule-based) |
| **F11** | **Yolg'on to'liqlik**: n/m / n/r ni yashirish, bo'sh `0` bilan to'ldirish, "—" bilan almashtirish | §8 K-4 |

---

## 10. Logo va icon

Fayllar: [`logo.svg`](logo.svg) (belgi + so'z belgisi), [`icon.svg`](icon.svg) (faqat belgi),
[`logo-test-sheet.svg`](logo-test-sheet.svg) (tekshiruv varag'i, brend aktivi emas).

**G'oya (batafsil `logo.svg` yuqoridagi izohda):** throughput izi tushadi va qaytadi;
qaytishdan boshlangan alohida planka — verification oynasi. **Qaytish alohida, tasdiq alohida.**

**NEGA aynan shu belgi:** loyihaning markaziy ta'rifi — qaytish yetarli emas, `[t_up, t_up + W_stab]`
oynasi talab qilinadi (`PREREGISTRATION.md` §4). Belgi shu farqni chizadi, va u qalqon, qulf,
prompt, ajdaho emas — o'lchov mavzusidan olingan. Bu o'lchangan natija **emas**:
chuqurlik va uzunlik bezak.

**Qoidalar**
- **L-1. Bitta rang.** Belgi `currentColor`. Qora fonda `--rx-fg-0` (yoki `--rx-fg-1`), oq fonda `--rx-ink`.
  **Belgi hech qachon qizil yoki yashil bo'lmaydi.** **NEGA:** §5, N6 (dekorativ signal rangi ma'noni suyultiradi).
- **L-2. Minimal o'lcham.** `icon.svg` — **16 px** (eng kichik e'lon qilingan). So'z belgili `logo.svg` — balandligi
  **16 px** gacha ko'rib chiqildi; interfeys sarlavhasida **≥ 24 px** tavsiya. **NEGA:** pastroqda
  harf teshiklari (R, E) yopiladi — tekshirilmagan.
- **L-3. Clear space** — barcha tomondan logo balandligining 0.5 qismi (so'z belgili logo uchun
  19.5 birlikning yarmi ≈ 10 birlik). **NEGA:** belgi to'g'ri burchakli chiziqlardan iborat;
  tutash element uni "jadval chizig'i" kabi o'qitadi.
- **L-4. Buzilmaydi:** cho'zish, soya, kontur, gradient, aylantirish, boshqa harf bilan almashtirish,
  to'ldirilgan konteyner ichiga solish. **NEGA:** konteyner ichiga solingan belgi sinovda "yuz" (ko'z-burun-og'iz)
  kabi o'qildi (`icon.svg` izohiga qarang).
- **L-5. So'z belgisi:** doim `REVIX` bosh harflarda. Matnda ham `REVIX` (README shunday yozadi).

---

## 11. Matn ovozi (copy)

- **Aniq va quruq.** Gaplar fakt aytadi: "hech qanday eksperiment ishga tushirilmagan" (`README.md`),
  "yaxshi", "ajoyib", undov belgisi yo'q.
- **"Restart" va "recovery" ikki so'z.** `restarted` — action; `verified` — VR. "Recovered" so'zi faqat VR
  bajarilgandan keyin. **NEGA:** `PREREGISTRATION.md` §4.
- **Taqiq so'zlar** (REVIX tavsifida): `AI-powered`, `self-healing`, `smart`, `intelligent`,
  `adaptive` (REVIX haqida; adaptiv recovery `Narya` kabi boshqa tizimlarniki), `secure`,
  `hardened`, `pentest`, `exploit`. **NEGA:** `04-novelty-statement.md` jadvali — bu da'volar
  qilinmaydi.
- **UI tili:** CLI hozir o'zbekcha jumlalar (`revix/cli.py`). Holat tokenlari (`healthy`, `failed`,
  `not_measured`, ...) **tarjima qilinmaydi** — ular mashina enum'i. **NEGA:** tarjima bitta
  holat uchun ikki yozuv hosil qiladi va qidirish/filtrni buzadi.

---

## 12. Berilgan palitra bo'yicha topilmalar

Quyidagi qiymatlar **o'zgartirilmadi**; faqat roli belgilandi va muammolar raqam bilan ko'rsatildi.

### 12.1 Ikki qizil — bir xil rol emas

`#E53935` va `#FF3B30` relative luminance 0.1984 va 0.2460 (kontrast farqi 1.19:1).
`#E53935` `bg-2` (`#151515`) da **4.32:1** — oddiy matn uchun 4.5 dan past; `#FF3B30` hamma uchta yuzada
5.15+. Shuning uchun **`#FF3B30` — matn/glyph/outline**, **`#E53935` — to'ldirilgan yuza** (ustiga qora matn: 4.74:1).
`#E53935` matn sifatida faqat `bg-0` da (4.74) va `bg-1` da (4.53, chegarada) o'tadi; `bg-2` da — yo'q.

### 12.2 Ikki yashil — deyarli bir xil

`#00C853` va `#22C55E`: relative luminance 0.4193 va 0.4108 (kontrast **1.02:1**). Ular bir-biridan
ko'zga ajralmaydi. Ikkita token **rol aniqligi uchun** saqlandi (qizil bilan simmetriya:
matn va solid), lekin amalda GUI bittasini (`--rx-ok`) ishlatsa ham hech narsa yo'qolmaydi.

### 12.3 `#FF3B30` va `#888888` monoxromda bir xil

L\* = 56.7 ikkalasida; kontrast 1.00:1 (§4.1). Bu palitraning haqiqiy cheklovi va shuning uchun
**qoida C1** (rang yagona kanal emas) majburiy.

### 12.4 `#444444` — matn ham, ma'noli chegara ham emas

`bg-0` da 2.06:1, `bg-2` da 1.87:1. Faqat hairline (§2.2).

### 12.5 Uch bazaviy qora — ohang bilan ajralmaydi

1.045 / 1.050 / 1.097:1. Border majburiy (§2.1).

### 12.6 Yorug' yuzada berilgan ranglar yetarli emas

`#00C853` oqda 2.24:1, `#888888` 3.54:1 (§2.4). `-ink` tokenlari qo'shildi.

### 12.7 Berilgan palitrada amber/sariq yo'q — bu **xato emas**

Uchta holat (`recovering`, `degraded`, `isolated`) signal rangiga ega emas, ular shakl va neytral
rang bilan ajraladi. Amber **qo'shilmadi**. **NEGA:** (a) "svetofor" (qizil-sariq-yashil) — iste'molchi UI
belgisi; (b) qizil/yashil allaqachon rang ko'rligi uchun xavfli juftlik (§4.2), uchinchi signal
rangi muammoni kamaytirmaydi, (c) bu holatlar **tasdiqlanmagan va failed emas** (§5.3, N3) — ularga
"yo'l-yo'riq" ma'nosi bermaslik kerak.

---

## 13. Tekshirilgan va tekshirilmagan

**Tekshirildi (haqiqatan bajarildi):**
- Barcha kontrast nisbatlari §3 va §2.4 da Python bilan **hisoblangan** (WCAG 2.x formulasi).
- CIE L\* qiymatlari (§4.1) va qizil/yashil/kulrang luminance juftliklari hisoblangan.
- `logo.svg`, `icon.svg`, `logo-test-sheet.svg`, `state-indicators.svg`, `boot-screen.svg`
  — XML sifatida parse qilindi; Browser pane da ochilib ko'rildi: qora va oq fonda,
  icon 16 / 24 / 32 / 48 / 64 / 512 px, so'z belgisi balandligi 16 / 24 / 48 px. Qo'shimcha: icon
  dastlab to'ldirilgan kvadrat ichida sinaldi va "yuz" kabi o'qilgani uchun rad etildi.
- `tokens.css` dagi har hex shu hujjatdagi jadvallar bilan skript orqali solishtirildi.
- Terminal tema JSON va TOML — sintaksis jihatidan parse qilindi.

**Tekshirilmadi:**
- Skrinshotlar Browser pane da **DPR 1.25** va ~0.78 masshtabda olindi; **DPR 1 da haqiqiy 16 px** va
  haqiqiy favicon/tab ko'rinishi tekshirilmagan.
- **Haqiqiy printerda** oq-qora chop etish — faqat luminance simulyatsiyasi (§4.1).
- Rang ko'rligi matritsalari xotiradan kiritilgan va ma'lumotnoma bilan solishtirilmagan (§4.2).
- Terminal temalari Windows Terminal / Alacritty'da **yuklab ko'rilmadi** (faqat sintaksis).
- `font-feature-settings: "zero"` ni shriftlar qo'llab-quvvatlashi.
- Foydalanuvchi sinovi (haqiqiy odamlar) o'tkazilmagan.
- `feature/gui` bu hujjatni hali amalga oshirmagan; GUI da qo'llanilganda kutilmagan holatlar chiqishi mumkin.
