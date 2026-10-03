# 12 — Ikki muzlatilgan qiymat qarori: `hold_cap_s` (§17.5 → O3) va fail-slow chegarasi (§18.6 → F2)

Bu hujjat **qaror yozuvi** (decision record). U `PREREGISTRATION.md` ni
o'zgartirmaydi — rasmiy amendment boshqa agent tomonidan, boshqa faylda yoziladi.
Bu yerda yozilgan narsa: qaror **nimaga** asoslangan, **qaysi dalil** bilan,
**qaysi variantlar rad etildi** va **nimasi cheklangan** — hujjatni hech qachon
ko'rmagan sharhlovchi tanlovni shu fayldan audit qila olishi uchun.

Besh belgi ishlatiladi:

- **FAKT** — fayldan olingan raqam yoki matn; manba (fayl + bo'lim) har joyda keltirilgan;
- **GIPOTEZA** — hali sinalmagan taxmin; o'lchov emas, va shunday deb belgilangan;
- **NATIJA** — bu hujjatda **faqat** bir ma'noda: *oldindan muzlatilgan qoida*
  o'lchangan FAKTga qo'llanganda chiqqan **hukm**. Bu **pilot natijasi EMAS**.
  **Pilot natijasi hozircha YO'Q** — birorta pilot trial'i o'tkazilmagan (§6);
- **TALQIN** — FAKTdan chiqarilgan xulosa yoki arifmetika (o'lchov emas);
- **CHEKLOV** — kafolatlab bo'lmaydigan yoki o'lchanmagan narsa.

**Qoida:** bu hujjatdagi har bir raqam quyidagi fayllarning birida **o'qilgan**
va manbasi ko'rsatilgan (§9 — audit jadvali). Hisoblangan raqam (`TALQIN`)
formulasi bilan beriladi. «doc 10» — `10-pressure-dozalash.md`.

**Sana:** 2026-10-03.
**Qaror qabul qiluvchi:** orkestrator — loyiha egasi shu sanada ikki ochiq
muzlatilgan qiymat qarorini unga **delegatsiya qilgan**.
**Asos holat:** `main` @ `76fa33c`; `PREREGISTRATION.md` = `preregistration/v1.10`
(sarlavha jadvali).
**O'qilgan manbalar:** `PREREGISTRATION.md` §0, §9.3, §9.4, §13, §17, §18, §19.3, §21.2, §21.3;
`docs/architecture/10-pressure-dozalash.md` §0, §1.4, §4, §6, §7, §8, §10, §11, §12;
`docs/architecture/08-guard-rekalibratsiya.md` (sarlavha, §14.5);
`docs/architecture/07-wsl-muhit-tekshiruvlari.md` §6.4.

---

## 0. Qisqa jadval

| qaror | tanlangan variant | qarorni hal qilgan **bitta** raqam | endi amendment qilinadigan bo'lim |
|---|---|---|---|
| **Ochiq qaror 1** — stabilizatsiya oynasi hold'ga sig'maydi | **O3**: `hold_cap_s` **12 s → 13 s** | `P1` bandida `p90(t_start) = 0.9543 s > 0.8 s` (19/24): §17.5 ning o'z qoidasi bo'yicha qaror **majburiy** edi. 13 s da boshqaruvchi (gate'siz) budjet `t_start ≤ 1.8 s`; `P1` ning o'lchangan `max = 1.4807 s` undan **17.7% past** | `PREREGISTRATION.md` **§17.5** (variantlar jadvali) va **§9.4** invariant 1 ning qiymati (`12 s`) |
| **Ochiq qaror 2** — fail-slow limbi ishlamaydi | **F2**: `thr = 0.20 × τ = 1.6 s`, **qat'iy** (fiksa) | o'lchangan `P0` da `thr = 0.0600 s = 0.60 × P` — `5P = 0.5 s` dan **8.3×** past va kvantlash poli `P = 0.1 s` dan ham past (doc 10 §7.5) | `PREREGISTRATION.md` **§18.6** (variantlar jadvali) va fail-slow limbi ishlatadigan `thr` ta'rifi (§18.2) |

**Yo'nalish (batafsil §5):** O3 hech bir ilmiy da'voni kuchsizlashtirmaydi.
**F2 esa kuchsizlashtiradi** — u `thr` ni kattalashtiradi va shu bilan
*«fail-slow qo'llab-quvvatlanmaydi»* xulosasiga **osonroq** yetkazadi.
F1 va F2 **teskari tomonga** og'adi; bu tanlov **F2 tomoniga** og'adi.

---

## 1. Nima uchun ikki qaror, va nima uchun birga

`PREREGISTRATION.md` sarlavhasi ikkala qarorni **birinchi pilot trial'idan oldin**
va **birgalikda** qabul qilinishi shart deb belgilaydi («Ochiq qaror 1/2» qatorlari).
§18.6 sababini aytadi: ikkalasi ham `τ = W_stab_pilot = 8 s` ga bog'langan, va §17.5
ning O1 varianti (`W_stab_pilot` ni kichraytirish) `τ` ni ham o'zgartirishi mumkin —
shunda F2 ning `0.20 × τ` chegarasi siljiydi. §19.3 buni kuchaytiradi: *«§17.5, §18.6
va §18.8 — uchalasi bitta qarorning bo'laklari»*.

**TALQIN:** O3 `τ` ga tegmaydi, shuning uchun O3 ni tanlash F2 ni **mumkin** qiladi:
`τ = 8 s` o'zgarmaydi va F2 ning `1.6 s` i barqaror referensga ega bo'ladi. O1 tanlansa
ikki qaror to'qnashardi (§2.8).

---

## 2. Ochiq qaror 1 — `hold_cap_s` (§17.5)

### 2.1 FAKT — §17.5 o'zi uchun qo'ygan qaror qoidasi

`PREREGISTRATION.md` §17.5, «Qaror uchun zarur, lekin MAVJUD BO'LMAGAN o'lchov»:

> *«`p90(t_start) ≤ 0.8 s` bo'lsa — nuqson amalda bezarar va O1–O4 kerak emas.
> Aks holda loyiha egasi O1–O4 dan birini tanlashi **shart**, va bu tanlov
> **birinchi pilot trial'idan oldin** qilinishi kerak.»*

Bu qoidaning `0.8 s` raqami §17.2 arifmetikasidan keladi (2.3 da to'liq).

### 2.2 FAKT — o'lchov (to'liq jadval)

Manba: doc 10 §6.2 (natijalar jadvali) va §6.5 (qaror qoidasi). Kalibrlangan dial:
`MemoryHigh=192M`, `base_mb=184`, `step_mb=4` (doc 10 §0, §2.6). Barcha 78 urinishda
start muvaffaqiyatsizligi **0/78** (doc 10 §6.2).

| band | n | min | p50 | **p90** | **p99** | **max** | `≤ 0.8 s` | `p90 / 0.8 s` |
|---|---|---|---|---|---|---|---|---|
| `P0` (generator yo'q) | 30 | 0.0237 | 0.0386 | **0.0481** | 0.0555 | 0.0576 | 30/30 | 0.06× (16.65× zaxira) |
| **`P1`** (kalibrlangan) | 24 | 0.0555 | 0.5041 | **0.9543** | **1.3948** | **1.4807** | **19/24** | **1.19×** |
| `P2` (kalibrlangan) | 24 | 0.3154 | 0.5727 | **0.7863** | 1.1211 | 1.1883 | 22/24 | 0.98× |
| `P1 + P2` | 48 | 0.0555 | 0.5611 | **0.9105** | 1.3433 | 1.4807 | 41/48 | 1.14× |

`p99` ustunida **`P1` (1.3948 s) `P2` dan (1.1211 s) yomon** — qarorni hal qilgan band `P1`,
`P2` emas. Qo'shimcha FAKTlar (doc 10 §6.5, §10.1):

- `≤ 0.5 s` (2.3 dagi gate'li budjet, 12 s da): `P0` 30/30, `P1` 11/24, `P2` 9/24.
- `0.8 s < t_start < 10 s` oralig'iga `P1` da **5/24**, `P2` da **2/24** urinish tushgan.
- Nazoratsiz to'yinishdagi (≈0.999 doza) avvalgi o'lchov: `p90 = 5.4042 s`, `p99 = 7.1958 s`,
  `≤ 0.8 s` — **0/6** (doc 10 §6.3; manba `08` §15.3).

**Kontrast (TALQIN):** `P2` bo'yicha `p99` `7.1958 s` dan `1.1211 s` ga tushdi (doc 10 §6.3,
6.42×; `p90` 6.87×). Buning deyarli **hammasini dozalash kalibratsiyasi** qildi. O3 esa faqat
**qolgan bo'shliqni** yopadi: kalibratsiyadan keyin ham `P1` `0.8 s` budjetidan o'tmaydi
(1.19×). Ya'ni O3 «halokatni davolash» emas, **chegara bo'shlig'ini yopish**. Doc 10 §6.5 ning
o'z hukmi: *«`08` ning HALOKATI rad etildi, lekin nuqson YOPILMADI»*.

### 2.3 TALQIN — arifmetika (§17.2 ning to'liq qayta hisobi)

`t_h` — hold boshlanishi, `h = hold_cap_s`. Muzlatilgan qiymatlar: injeksiya `t_h + 3 s`
(§9.4), hold tugashi `t_h + h` (§9.4 invariant 1), oyna `W_stab_pilot = 8 s` (§4),
`RestartSec = 100 ms` (§9.3, arm `A`), probe davri `P = 100 ms` (§2). Oyna hold ichida
bo'lishi sharti (§17.2):

```
t_up + 8 <= t_h + h        =>   t_up <= t_h + (h - 8)
t_inject = t_h + 3         =>   t_up - t_inject <= h - 11
t_up - t_inject = RestartSec + t_start + P_kvant = 0.1 + t_start + 0.1
=> t_start <= (h - 11) - 0.2 = h - 11.2             (GATE'SIZ budjet)
   action F_probe ga gate qilinsa D_f = 300 ms (k_f = 3, §3) qo'shiladi:
=> t_start <= h - 11.5                               (GATE'LI budjet)
```

`h = 12` da bu aynan §17.2 ning `0.8 s` / `0.5 s` i. Boshqa `h` lar uchun (invariant 2
zaxirasi = `15 − h − ramp_above_threshold_s`, bunda `ramp_above_threshold_s = 0.000 s`, 2.4):

| `hold_cap_s` | gate'siz budjet | gate'li budjet | invariant 2 zaxirasi | `P1` max (1.4807 s) gate'siz budjetga nisbatan |
|---|---|---|---|---|
| 12 s (hozirgi muzlatilgan) | 0.8 s | 0.5 s | 3.0 s | 85% **ustida** |
| 12.5 s | 1.3 s | 1.0 s | 2.5 s | 14% **ustida** |
| **13 s (tanlangan)** | **1.8 s** | 1.5 s | **2.0 s** | **17.7% past** |
| 15 s | 3.8 s | 3.5 s | **0.0 s** | 61% past |

13 s da: `P1` `p99` (1.3948 s) gate'siz budjetdan **22.5% past**; `P2` `max` (1.1883 s) — 34% past.

### 2.4 FAKT — invariant 2 va `ramp_above_threshold_s`

`PREREGISTRATION.md` §9.4 invariant 2: `hold_s + ramp_above_threshold_s ≤ guard_sustain_s = 15 s`.
Doc 10 §4.1: `ramp_above_threshold_s = 0.000 s` — `base_mb = 184` da **29 epizoddan 29 tasida**,
haqiqiy doza bilan; ramp tezligi `min = p50 = max = 0.0000`. Demak 13 s da `13 + 0.000 = 13 ≤ 15`,
**2.0 s zaxira** (doc 10 §4.2 da 12 s uchun 3.000 s).

**CHEKLOV (doc 10 §4.2):** `hold_s = 12 s` ham, `13 s` ham **sinalmadi**: o'lchangan epizodlar
`ramp + hold = 12 s` (haqiqiy hold ≈ 9.5 s). `ramp_above_threshold_s` ramp fazasining xususiyati
va hold uzunligiga bog'liq emas (arifmetika shu sababli ko'chadi). Uzunroq hold'da `sustained_pressure`
xavfi **oshmaydi** deyish doc 10 da **TALQIN**, o'lchov emas. Bu §8 C2 da qayta yoziladi.

### 2.5 NATIJA — qoidaning hukmi

§17.5 ning o'z qoidasi `P1` da **buziladi**: `p90 = 0.9543 s`, budjetdan `0.1543 s` (**19.3%**) katta;
birlashtirilgan 48 namunada ham buziladi (`0.9105 s`, 13.8%). `PREREGISTRATION.md` §9.3 `P1` ni
**to'laqonli yacheyka** qiladi (3 × 2 × 20 ning uchdan biri), shuning uchun `P1` dagi buzilish
butun dizaynni qamrab oladi (doc 10 §6.5, §12.4). Qoidaning **harfi** `P2` da bajarilgan (`0.7863 s`,
1.7% zaxira), lekin doc 10 §12.4 buni «o'lchov shovqinidan kichik» deb baholagan. **Qaror majburiy edi.**

### 2.6 Qaysi budjet `P1` ni boshqaradi — gate'sizmi, gate'limi

§17.2: gate'li budjet (`t_start ≤ h − 11.5`) **faqat** *«agar action `F_probe` ga gate qilinsa»*.
Pilotda bu shart **yolg'on**:

- `PREREGISTRATION.md` §9.3 pilot arm'larini muzlatadi: `A` (`Restart=on-failure`, `RestartSec=100ms`)
  va `no_action` (`Restart=no`). `A` da restartni **systemd o'zi** bajaradi, harness qarori yo'lda
  **yo'q** (§17.2: *«harness qaror kechikishi yo'q»*). `F_probe` hech bir pilot arm'ining
  harakatini gate qilmaydi.
- `F_probe` ga gate qilingan aktor — arm C (REVIX). §13 arm C siyosati va gate chegaralarini
  **muzlatmaydi** va ularni *«o'z pre-registration'ini»* talab qiladigan narsa deb belgilaydi;
  §0 («Nima o'lchanmaydi») arm C ni pilot qamrovidan chiqaradi.

**TALQIN:** pilotdagi `P1` (va `P0`, `P2`) uchun boshqaruvchi budjet — **gate'siz**,
`t_start ≤ h − 11.2`. Gate'li arifmetika bu pilotga **qo'llanmaydi**; lekin kelajak arm C uchun
**majburiy cheklov** (§8, C7).

### 2.7 TALQIN — nima uchun O3, va nima uchun aynan 13 s

**(a) O3 — hech bir ilmiy da'voni kuchsizlashtirmaydigan yagona variant.** Bu §17.5 ning **o'z**
bayonoti (*«yagona variant hech bir ilmiy da'voni kuchsizlashtirmaydigan»*). O1, O2, O4 — sof
ta'rif o'zgarishi; O3 — ta'rif o'zgarishi **va** yangi o'lchov (guard rekalibratsiyasi). §17.5 O3
narxini ikki shart bilan qo'ygan: (i) invariant 2 **qayta tekshirilsin**, (ii) guard **qayta
kalibratsiya qilinsin**. Birinchisi doc 10 §4 da **bajarilgan** (2.4). Ikkinchisi bo'yicha doc 10
§12.4: `ramp_above_threshold_s = 0` bo'lgani uchun guard'ning `sustain_max_seconds = 15.0` i
**o'zgartirilishi kerak emas** (arifmetika; sinalmagan — §8 C2). 12 s ni yaratgan oomd xavfi bu
host'da yo'q (§17.5; doc 07 §6.4) — bu O3 narxini pasaytiradi, lekin pilotning xavfsizlik
dalilini **faqat guard'ga** qoldiradi (§8 C1).

**(b) 13 s — gate'siz budjetni boshqaruvchi bandning o'lchangan `max` ida qoplaydigan eng kichik
yarim-soniyali qadam.**

```
gate'siz budjet(h) = h - 11.2  >=  max(t_start | P1) = 1.4807 s   =>   h >= 12.6807 s
```

- `h = 12.5` → budjet `1.3 s`; `P1` `max = 1.4807 s` uni **oshadi** (`p99 = 1.3948 s` ham).
  12.5 da kamida bitta o'lchangan start (eng sekini) oynasi pressure'dan chiqib ketgan bo'lardi.
- `h = 13` → budjet `1.8 s`; `P1` `max` undan **17.7%**, `p99` **22.5%** past.

Tamoyil — **«muzlatilgan qiymatning eng kichik o'zgarishi, u ishlasa»**; margin bahsi emas.
(Aniq nazariy minimum `12.6807 s` — nol zaxira; yarim soniyali granulyarlik — **tanlov**, §8 C4.)

**(c) Nega 15 s emas.** 15 s da gate'siz budjet `3.8 s`, lekin invariant 2 zaxirasi **0.0 s**:
`15 + 0.000 = 15 ≤ 15` (doc 10 §12.4 ning o'z hisobi) — guard'ning `sustain_max_seconds = 15.0` i
bilan **to'liq tenglik**; sustain taymeri yoki `ramp_above_threshold_s` ning har qanday kichik
musbat qiymati invariantni buzadi. 13 s kerakli budjetni beradi va **2.0 s** zaxira qoldiradi.

**(d) Nega 12.5 emas** — (b): `P1` `max` uni oshadi.

### 2.8 Nega O1, O2, O4 emas

Narxlar — §17.5 ning o'z jadvalidan:

| variant | §17.5 narxi | bu qarorda nega rad etildi |
|---|---|---|
| **O1** — `W_stab_pilot` kichraytiriladi | VR da'vosini **kuchsizlashtiradi**: §4 ning 5-bandi (throughput) qisqa oynada kamroq ma'noga ega | Qo'shimcha: **`τ` ni siljitadi** — §10.2/§11 da `τ = 8 s` `W_stab_pilot` bilan bir xil raqam; `τ` o'zgarsa F2 ning `0.20 × τ` chegarasi ham o'zgaradi (§18.6 «Bog'liqlik»). O1 **Ochiq qaror 2 bilan to'qnashadi** va ikkalasini birga hal qilish sharti buziladi |
| **O2** — `injection_offset` kichraytiriladi | 3 s hold boshidan keyin pressure **barqarorlashuvi** uchun; kichraytirish *«o'rnatilgan pressure ostida injeksiya»* binosini kuchsizlashtiradi | Dizaynning identifikatsiya binosiga tegadi; O3 tegmaydi |
| **O4** — oyna pressure'dan chiqishiga ruxsat | §4 ning o'z izohiga (*«pressure davom etayotganda tasdiqlangan recovery»*) **qarshi**: raqam emas, **metrikaning ma'nosini** o'zgartiradi — eng og'ir variant | Bo'shliqni yopish o'rniga ma'noni o'zgartirish |

---

## 3. Ochiq qaror 2 — fail-slow chegarasi (§18.6)

### 3.1 FAKT — §18.6 o'zi uchun qo'ygan qaror qoidasi va §11 ning matni

§11 (so'zma-so'z, §18.1 orqali): *«fail-slow shakli qo'llab-quvvatlanmaydi, agar `P0` va `P2`
orasidagi time-to-VR RMST farqi (τ = 8 s) uchun 95% CI **20% oshishni** chiqarib tashlasa.»*
§18.2 referensni `RMST(P0)` deb o'qiydi:

```
Delta(P2,P0) := RMST_A(P2, tau=8 s) - RMST_A(P0, tau=8 s)
thr          := 0.20 * RMST_A(P0, tau=8 s)                     (F1 — hozirgi matn)
fail-slow QO'LLAB-QUVVATLANMAYDI  <=>  CI95_upper[ Delta(P2,P0) ] < thr
```

§18.6 yopiq qoidasi: *«Agar `thr ≥ ~5 × P` bo'lsa, 18.4 ning cheklovi amalda bezarar va F1
yetarli; aks holda egasi F1–F4 dan birini tanlashi **shart**.»* (`P = 100 ms`, `5P = 0.5 s`.)

### 3.2 `thr` ning hisobi — ikki yo'l, ikkalasi ko'rsatilgan

**(A) O'LCHANGAN yo'l** — doc 10 §7.5 (har bandda n = 12 restart epizodi; `D_probe` proxy, `mean`):

| band | `RMST(P0)` proxy (`mean D_probe`) | `thr = 0.20 × mean` | `P` birligida | `5P = 0.5 s` ga nisbati |
|---|---|---|---|---|
| **`P0`** | 0.3000 s | **0.0600 s** | **0.60 × P** | **8.3× past** |
| `P1` | 0.8500 s | 0.1700 s | 1.70 × P | 2.9× past |
| `P2` | 1.0250 s | 0.2050 s | 2.05 × P | 2.4× past |

Doc 10 §7.5: chegara **uchala bandda ham** `5P` dan kichik (eng kattasi `p90(P2)` da `3.10 × P`).
`P1` va `P2` qatorlari natija **`P0` bandining artefakti emasligini** ko'rsatadi. Mustaqil
takror: `PREREGISTRATION.md` §21.3 — `08` §16 dan `D_probe` proxy (`P0`, n = 12, mean 0.4833 s)
→ `thr = 0.0967 s = 0.97 × P`. Ikki mustaqil o'lchov (0.3000 va 0.4833) `thr` ni `P` dan **past** beradi.

**(B) HISOBLANGAN (derived) yo'l** — §18.4 ning muzlatilgan-overhead formulasi:

```
D_probe(P0) = t_start + (0.2 ... 0.4) s              (§18.4: sof muzlatilgan overhead)
RMST(P0) ~= E[D_probe(P0)]                           (§9.2: P(VR|P0,restart) ~ 1.0)
o'lchangan P0 t_start p50 = 0.0386 s                 (doc 10 §6.2)
=> RMST(P0) ~= 0.2386 ... 0.4386 s
=> thr = 0.20 * RMST(P0) ~= 0.048 ... 0.088 s        (0.48 ... 0.88 x P)
```

Bu **o'lchov emas**: o'rtacha o'rniga `p50` ishlatilgan, overhead oralig'i §18.4 dan. `5P = 0.5 s`
ga nisbatan **5.7–10.5×** past. (Oraliq o'rtasi ≈ 0.068 s; «≈ 0.07 s» shu hisoblangan
o'rta — o'lchangan raqam sifatida berilmaydi.)

### 3.3 NATIJA — F1 ning hukmi

Ikkala yo'lda **bir xil hukm**: `thr` `5P` dan ham, kvantlash poli `P = 0.1 s` dan ham past
(§19.3: `thr < P ⟺ RMST(P0) < 0.5 s`; bu yerda `RMST(P0) ≈ 0.24–0.44 s`). §18.6 qoidasi
**bajarilmadi** — qaror **majburiy**. F1 ning inkor shoxi (`CI_upper[Δ] < thr`) o'lchov
kvantlashidan mayda farqni ko'rsatishni talab qiladi, ya'ni kvantlash polining **tagida** —
§19.3 ning «pastki degeneratsiya» rejimi.

**TALQIN — F1 amalda tekshirib bo'lmaydi.** Kalibratsiya proxy'laridan (3.5 dagi ogohlantirishlar
bilan): `Δ̂_proxy(P2−P0) = 1.0250 − 0.3000 = 0.7250 s`. F1 da `thr = 0.0600 s`, nisbat `12.1×`:
limb *«qo'llab-quvvatlanadi»* ni **avtomatik** beradi va `0.7 s` kechikishni `0.07 s` kechikishdan
ajrata olmaydi (xuddi shu xulosa `PREREGISTRATION.md` §21.3 da, uning o'z raqamlari bilan).
§18.1 ning o'z printsipi: *«hisoblab bo'lmaydigan pre-registered qoida hech narsani falsifikatsiya
qilmaydi»*; F1 da qoida hisoblanadi, lekin inkor shoxi **erishib bo'lmaydi**.

### 3.4 Variantlar — nega F2

Narxlar va bias yo'nalishi — §18.6 jadvalidan:

| variant | §18.6 narxi | bias (§18.6) | qaror |
|---|---|---|---|
| **F1** — `thr = 0.20 × RMST(P0)` | matnga eng sodiq; **inkor shoxi erishib bo'lmaydigan** ⇒ limb bir tomonlama | **fail-slow / H1 FOYDASIGA** | **rad** (3.3) |
| **F2** — `thr = 0.20 × τ = 1.6 s` | o'lchanadigan, rejimdan **mustaqil**, kvantlashdan **16×** yuqori; lekin §11 ning *«×P0»* konvensiyasiga qarshi va «20% oshish» → «horizonning 20%i» | **H1 GA QARSHI** | **TANLANDI** |
| **F3** — `thr = 0.20 × median(P0)` | kvantlash muammosi **o'zgarmaydi**; qo'shimcha: KM medianasi `nan` bo'lishi mumkin (`04` §2.3, 8-band) | F1 bilan bir xil | **rad** — dominatsiyalangan (quyida) |
| **F4** — absolut chegara (`k × P`) | `k` ni tanlash o'lchov talab qiladi | oldindan aniq emas | `k` ni «anchor»siz tanlash o'zboshimcha; **F2 — F4 ning asoslangan `k` li shakli** (quyida) |

**F3 nega dominatsiyalangan.** `P0` da 12 epizodning **hammasi aynan 0.300 s** (doc 10 §7.2):
mean = median = 0.3000 s, demak F3 ning `thr` i F1 niki bilan **bir xil** (`0.0600 s`). F3 F1 ning
barcha kamchiligini saqlaydi va ustiga `nan` xavfini qo'shadi.

**F4 nega anchor'siz o'zboshimcha, F2 nega F4 ning asoslangan shakli.** `k = 5`, `10` yoki `20` ni
tanlash uchun muzlatilgan asos yo'q (§18.6: `k` o'lchov talab qiladi). F2 da `k` **ikki
muzlatilgan qiymatdan** chiqadi:

```
thr_F2 = 0.20 * tau = 0.20 * 8 s = 1.6 s = 16 * P      (P = 0.1 s)
```

`0.20` — §11 ning o'z «20% oshish» raqami; `τ = 8 s` — §10.2/§11 ning muzlatilgan horizonti.
**F2 = F4 da `k = 16`**, va `16` hech kim tomonidan tanlanmagan: u muzlatilgan `20%` va
muzlatilgan `τ/P` ning ko'paytmasi. Bu qarorda **yangi raqam kiritilmaydi**.

### 3.5 TALQIN — F2 ning qo'shimcha foydalari va chegaralari

- **§18.5 ning uchinchi sababi yo'qoladi.** §18.5: `0.20 × RMST(P0)` — *baholangan* kattalik;
  `CI95[Δ]` ni xuddi shu ma'lumotdan baholangan chegaraga solishtirish 95% qoplamaga ega emas.
  F2 da `thr = 1.6 s` — **konstanta**; bu muammo yo'q.
- **Ceiling muammosi saqlanadi.** §19.3: `RMST ∈ [0, τ]`, `Δ ≤ τ − R`; F2 chegarasi
  `1.6 > 8 − R ⟺ R > 6.4 s` bo'lganda erishib bo'lmaydi — **F2 yuqori degeneratsiyadan
  himoyalanmagan** (§19.3 «§18.6 ning variantlariga ta'siri»). Buni faqat `τ` ni oshirish yoki
  endpoint'ni o'zgartirish (§18.8) hal qiladi — **bu qaror ularni hal qilmaydi**.
- **§18.8 ochiq qoladi:** F2 qaysi downtime o'lchovi (`D_probe`, `D_eff`, `D_sd`) survival
  endpoint ekanini hal qilmaydi.

---

## 4. `P1` `t_start` bo'yicha `P2` dan yomonroq — TUSHUNTIRILMAGAN

**FAKT** (doc 10 §6.2, §6.5): `p90` `P1` da `0.9543 s`, `P2` da `0.7863 s`; `p99` `1.3948` vs `1.1211`;
`max` `1.4807` vs `1.1883`; `≤ 0.8 s` `19/24` vs `22/24`. `p50` esa teskari: `0.5041` (`P1`) vs
`0.5727` (`P2`). Doza tartibi (`P1` < `P2`) bo'yicha monotonlik yuqori kvantillarda **buzilgan**:
kuchsizroq doza dumda yomonroq.

**Bu hujjat uchun nima muhim:** O3 ning 13 s i aynan **`P1` ning o'lchangan maksimumiga**
asoslangan (2.7b). Agar `P1` dumi tasodifiy bo'lsa, 13 s ning bir qismi keraksiz; agar tizimli
bo'lsa, `P1` ning haqiqiy dumi shu. Qaysi ekani **noma'lum**.

**Mexanizm — TUSHUNTIRILMAGAN. Bu hujjat hech qanday mexanizm taklif qilmaydi.** Doc 10 §6.5
(3-band) va §11 OQ-6 faqat sinalmagan taxminni keltiradi: **GIPOTEZA (doc 10 ning, bu hujjatniki
emas, sinalmagan):** start lahzasidagi oniy stall dozaga emas, **arra tishi fazasiga** bog'liq
(tezlik `0.03–0.95` oralig'ida tebranadi, doc 10 §11 OQ-3). Doc 10 o'zi aytadi: start lahzasidagi
**oniy** stall yozilmadi, shuning uchun bu taxmin o'lchov bilan **tasdiqlanmagan** (OQ-6). Ochiq
savol: **nima uchun `P1` `t_start` bo'yicha `P2` dan yomonroq?** Kerakli o'lchov doc 10 §6.5 da
ta'riflangan (start'larni arra tishi fazasiga qasddan sinxronlash) va bajarilmagan.

---

## 5. Bias yo'nalishi — yumshatilmagan e'lon

### 5.1 F2 ning bias'i

> **F2 `thr` ni kattalashtiradi** — o'lchangan `0.0600 s` (F1) dan `1.6 s` ga, ya'ni **26.7×**
> (`1.6 / 0.0600`). Shu bilan *«fail-slow qo'llab-quvvatlanmaydi»* (`CI_upper[Δ] < thr`)
> xulosasiga yetish **osonlashadi**, *«qo'llab-quvvatlanadi»* xulosasi esa **qiyinlashadi**.

**F1 va F2 teskari tomonga og'adi** (§18.6 jadvali: F1 → H1 foydasiga, F2 → H1 ga qarshi).
O'quvchi skeptitsizmini shunga qarab sozlashi kerak: **bu tanlov H1 ning fail-slow shakliga
qarshi tomonga og'adi.** Agar fail-slow limbi «qo'llab-quvvatlanmaydi» desa, bu qisman ma'lumot,
qisman `thr = 1.6 s` ning kattaligi.

**Raqamli ko'rsatma (TALQIN, ogohlantirishlar bilan).** Doc 10 §7.2/§7.5 kalibratsiya proxy'lari
bo'yicha: `Δ̂_proxy(P2−P0) = 1.0250 − 0.3000 = 0.7250 s`; `Δ̂_proxy(P1−P0) = 0.8500 − 0.3000 = 0.5500 s`.

| | `thr` | `Δ̂_proxy(P2−P0) / thr` | `Δ̂_proxy(P1−P0) / thr` |
|---|---|---|---|
| F1 (o'lchangan) | 0.0600 s | **12.1×** — «qo'llab-quvvatlanadi» avtomatik | 9.2× |
| **F2** | 1.6 s | **0.45×** — nuqtaviy baho `thr` **ostida** | 0.34× |

Ya'ni **bir xil kalibratsiya ma'lumotida F1 va F2 teskari hukm tomon suradi.** Bu **pilot natijasi
EMAS**: (i) proxy `D_probe` — `RMST` emas (doc 10 §7.5 CHEKLOV); (ii) n = 12 va **CI
hisoblanmagan** — F2 da «qo'llab-quvvatlanmaydi» uchun `CI_upper < 1.6 s` kerak, nuqtaviy bahoning
0.45× da bo'lishi bunga **kafolat emas**; (iii) bu kalibratsiya dozasi, pilot emas. Ammo u
**yo'nalishni** ko'rsatadi.

**Qaror qanday qabul qilingan (shaffoflik).** F2 §11 ning muzlatilgan *«×P0»* konvensiyasiga
**qarshi** (§18.6 F2 narxi). F1 ni saqlash limbni falsifikatsiya qilmaydigan holda qoldirardi (3.3).
Qaror kalibratsiya raqamlarini **ko'rgandan keyin** qabul qilingan, shuning uchun §17.6/§18.7 dagi
*«qaror ma'lumot bo'lmaganda qabul qilindi»* kafolati bu qarorga **ko'chmaydi**: bu yerda ma'lumot
**bor edi**. Qarorning asosi — `thr = 1.6 s` ning muzlatilgan qiymatlardan chiqishi (3.4), o'lchangan
raqamdan tanlanishi emas; lekin tanlovning *yo'nalishini* o'quvchi o'zi baholashi kerak.

### 5.2 O3 ning bias'i

**TALQIN (§17.3, §17.6 ga tayanib).** §17.3 ning ustun bias'i holat (a): oyna pressure'dan chiqadi
→ `P(VR|P2)` **oshadi** → trend **susayadi** → **H1 ga qarshi**. O3 `h` ni oshirib (a) chastotasini
**kamaytiradi**, ya'ni H1 ga qarshi o'lchov artefaktini **kamaytiradi**; o'lchangan trend
**kuchayishi mumkin**. Bu **GIPOTEZA**: haqiqiy ta'sir `t_start` taqsimotiga va `P1` dumiga
bog'liq (§4) va o'lchanmagan. O3 hech bir ilmiy da'voni kuchsizlashtirmaydi (2.7a): u o'lchov
oynasini ta'rif talab qilgan joyga qaytaradi.

### 5.3 Yig'ma jadval

| qaror | og'ish yo'nalishi | manba |
|---|---|---|
| O3 (`hold_cap_s = 13`) | H1 ga qarshi artefaktni kamaytiradi (GIPOTEZA) | §17.3, 5.2 |
| **F2 (`thr = 1.6 s`)** | **fail-slow'ni inkor qilishga osonroq — H1 ning fail-slow shakliga qarshi** | §18.6, 5.1 |
| F1 (rad etilgan) | fail-slow'ni inkor qilish deyarli mumkin emas — H1 foydasiga | §18.6, §18.7 |

---

## 6. NATIJA — yo'q

**Hech qanday pilot eksperimenti ishga tushirilmagan. Hech qanday pilot natijasi yo'q.** Bu
hujjatdagi har bir raqam **kalibratsiyadan** (doc 10: 9 run, 35 pressure epizodi, 78 SUT start'i)
va **muzlatilgan matnning arifmetikasidan** olingan. Birorta `P1` trial'i o'tkazilmagan.
Qarorlar pilot natijasini ko'rib emas, kalibratsiya o'lchovini ko'rib qabul qilingan (5.1).

---

## 7. Nima o'zgarmaydi

Bu qarorlar quyidagilarga **tegmaydi**: `W_stab_pilot = 8 s`, `W_stab = 60 s`, `injection_offset = 3 s`,
`guard_sustain_s = 15 s` (va guard'ning `sustain_max_seconds`), `τ = 8 s`, `θ = 0.8`, `P = 100 ms`,
`k_f = 3`, arm'lar `A`/`no_action`, `P0`/`P1`/`P2`, 20 blok / 120 trial, §10.1 Cochran–Armitage,
§10.2 KM/log-rank/**RMST difference**, §10.4 Holm, §12 yopiq enum'i, §11 ning kuchli shakl limbi
(Newcombe yuqori chegarasi `< 0.15`). **Yagona ikki o'zgarish: `hold_cap_s` 12 → 13 s va
fail-slow `thr` ta'rifi `0.20 × RMST(P0)` → `0.20 × τ`.**

---

## 8. CHEKLOV

**C1. 12 s cheklovning asl asosi — oomd — bu host'da yo'q; pilotning xavfsizlik dalili endi
FAQAT guard'ga tayanadi.** `PREREGISTRATION.md` §9.4 invariant 1 asosi: *«oomd 20 s sustained talab
qiladi»*; §17.5 O3: *«12 s ni yaratgan oomd xavfi bu host'da yo'q»*. Doc 07 §6.4: `systemd-oomd` ning
binary'si, unit'i va config'i **yo'q**; `00` §3.1 va `PREREGISTRATION.md` §4 dagi 12 s oyna va 15 s
sustain *«oomd'ning 20 s sharti ustiga qurilgan»*, va doc 07 ularning hali kerak-kerak emasligini
**hal qilmaydi** (OQ-1). Shuning uchun: (i) 12 → 13 ga ko'tarish yo'qolgan xavfsizlik qatlamini
qaytarmaydi — u bu host'da **umuman mavjud emas**; (ii) pilot containment dalili **faqat guard**
(`sustain 15 s`, `user_full_rate2s_max 0.98`) va `revixlab.slice` chegaralariga (doc 10 sarlavhasi:
`MemoryMax=2G`, `MemorySwapMax=0`) **tayanadi**. Agar pilot oomd mavjud host'ga ko'chsa, 13 s ni
qayta tekshirish shart: oomd 20 s oynasidan zaxira `20 − h` — 12 da `8 s`, 13 da `7 s` (TALQIN).

**C2. 13 s hold sinalmadi.** Doc 10 §1.4, §4.2, OQ-5: o'lchangan epizodlar `ramp + hold = 12 s`
(haqiqiy hold ≈ 9.5 s); pilotning haqiqiy epizodi `5 + 12 = 17 s` (13 da `5 + 13 = 18 s`). Band
ichida qolish vaqtlari ≈ 9.5 s hold uchun va ko'chirilmaydi. Guard 35 epizodda **1 marta** trip qildi
(`user_full_rate2s_runaway`, `rate = 0.9801962`, `limit = 0.98`, `kill_ok: true`; doc 10 §8.2) —
`dose-02-bands` run'ida. 13 s hold'da `sustained_pressure` trip'i xavfi **oshmaydi** deyish —
arifmetika (invariant 2: `13 + 0 ≤ 15`), o'lchov emas.

**C3. `t_start` faqat shu mashinada o'lchangan; budjet zaxirasi ko'chmaydi.** Mashina `Root-Zero`,
WSL2, kernel `6.6.87.2-microsoft-standard-WSL2`, systemd 257, 9.71 GiB RAM, `MemoryHigh=192M`,
`base_mb=184` (doc 10 sarlavhasi, §2.6). `t_start` ning 97.0–97.3% i SUT `main()` idan **oldin**
ketadi (`execve`, dinamik yuklash, reclaim throttling ostidagi page fault'lar; doc 10 §6.4) — u
**kernel/reclaim** xossasi. 13 s ning 17.7% zaxirasi boshqa kernel, host, RAM yoki dial'ga
**ko'chmaydi**. Ishchi `base_mb` oynasi tor (faqat 184; doc 10 §3.6, OQ-11).

**C4. n kichik, `p99 ≈ max`.** Har bandda n = 24 (6 epizod × 4 start); `p99` bu n da `max` ga yaqin —
**taqsimot bahosi emas** (doc 10 §6.5). 17.7% zaxira — n = 24 dagi **maksimumga** nisbatan.
Yarim soniyali granulyarlik — **tanlov**, o'lchov emas.

**C5. `P1` `P2` dan yomonroq — TUSHUNTIRILMAGAN** (§4). 13 s aynan `P1` maksimumiga asoslangan.

**C6. Birorta `P1` pilot trial'i o'tkazilmagan** — hamma raqam kalibratsiyadan (§6). Doc 10 §12.5:
pilot hozir ishga tushirilishi **mumkin emas** (`driver.py` dozalash parametrlarini bermaydi, OQ-2;
`PRESSURE_TARGET_RATE["P2"] = 0.70` over-doza beradi; `WatchdogSec` kalibrlanmagan, OQ-8).

**C7. Gate'li arifmetika — kelajak arm C uchun MAJBURIY cheklov.** Gate'li budjet 13 s da
`t_start ≤ 1.5 s` (2.3). `P1` ning o'lchangan `max = 1.4807 s` da zaxira **`0.0193 s` = 1.3%**
(`1.5 − 1.4807`; `p99 = 1.3948 s` da `0.1052 s` = 7.0%). Doc 10 §12.4 ning o'z standarti bo'yicha
(1.7% zaxira «o'lchov shovqinidan kichik» edi) **1.3% shovqin ichida**. Shuning uchun:

> **Arm C (yoki `F_probe` ga gate qilingan har qanday aktor) 13 s cheklovni MEROS QILIB OLA
> OLMAYDI.** Arm C ni pre-registratsiya qiladigan kishi bu arifmetikani (`t_start ≤ h − 11.5`,
> yangi o'lchangan `t_start` taqsimoti bilan) **qaytadan bajarishi shart.** 13 s faqat
> **gate'siz** pilot arm'lari (`A`, `no_action`) uchun asoslangan.

**C8. `t_start` budjeti butun uzilishni qoplamaydi (brownout).** 2.3 dagi arifmetika uzilishni
`RestartSec + t_start + P` deb oladi. Doc 10 §7.2 `D_probe` proxy'si (n = 12 epizod / band):
`P1` da `max = 1.700 s`, `P2` da **`max = 2.200 s`**. 13 s da `t_up − t_inject` budjeti `h − 11 = 2.0 s`;
injeksiyadan oldingi oxirgi o'tgan probe ≤ `P` oldin bo'lgani uchun `t_up − t_inject ∈
[D_probe − P, D_probe]` (TALQIN; failure ≈ injeksiya deb olingan). Demak `P2` ning bitta epizodi
(`2.2 s` ⇒ `≥ 2.1 s`) **2.0 s dan oshadi**, `P1` ning eng uzuni (`1.7 s`) o'tadi. Doc 10 §7.4/OQ-9:
`P1` va `P2` da har birida 4 ta brownout epizodi (restartsiz contract buzilishi) — bu uzilishni
`t_start` dan **tashqari** uzaytiradi. **O3 oyna-chiqish holatini (a) YO'Q qilmaydi, KAMAYTIRADI:**
`window_past_pressure` darajasi (`PREREGISTRATION.md` §17.4(4)) yacheyka bo'yicha **hamon hisobotga
kiritilishi shart**. `D_probe` proxy — `t_up` emas, n = 12.

**C9. `thr` va OQ-12.** Doc 10 §7.5 CHEKLOV: agar time-to-VR ta'rifi `W_stab` oynasini ichiga olsa,
`RMST(P0) ≈ 8.3 s` va `thr ≈ 1.66 s ≥ 5P`; `PREREGISTRATION.md` §21.2 OQ-12 ni **rad etgan** va
§18.3 ni (anchor `t_up`) kuchda qoldirgan — bu qaror §18.3 ga tayanadi. §21.2 ning ikki tomonlama
qoidasi (`5P ≤ thr ≤ ½(τ − R)`) bo'yicha **ikkala o'qish ham** yiqiladi, ya'ni §18.6 qarori OQ-12
javobidan **qat'i nazar** zarur. `D_probe` proxy `RMST` emas. `P0` proxy ikki o'lchovda turlicha:
`0.3000 s` (doc 10) va `0.4833 s` (§21.3) — farq asbobning kvantlash poli ichida (doc 10 §7.3);
ikkalasida ham `thr < P`.

**C10. Kod izohi eskiradi.** `revix/schedule.py:50` (`main` @ `76fa33c`):
`HOLD_CAP_S = 12.0  # §9.4 -- oomd xavfsiz oynasi (oomd 20 s talab qiladi)`. Bu hujjat kodni
**o'zgartirmaydi** (boshqa agent egalik qiladi); qiymat 13 ga o'tganda izohning oomd asosi C1 ga
ko'ra eskiradi — kod egasi uni yangilashi kerak.

**C11. Amendment bo'limi raqami noma'lum.** Rasmiy amendment boshqa agent tomonidan yoziladi;
bu hujjatdagi `§17.5` / `§18.6` / `§9.4` havolalari **v1.10 ning mavjud bo'limlari**.

---

## 9. Audit uchun manba jadvali

| raqam | qiymat | manba |
|---|---|---|
| `p90(t_start)`: `P0`/`P1`/`P2`/`P1+P2` | 0.0481 / 0.9543 / 0.7863 / 0.9105 s | doc 10 §6.2, §6.5 |
| `p99`: `P1`/`P2`/`P1+P2` | 1.3948 / 1.1211 / 1.3433 s | doc 10 §6.2 |
| `max`: `P1`/`P2` | 1.4807 / 1.1883 s | doc 10 §6.2, §10.1 |
| `≤ 0.8 s` | 30/30, 19/24, 22/24, 41/48 | doc 10 §6.2, §6.5 |
| `≤ 0.5 s` | `P0` 30/30, `P1` 11/24, `P2` 9/24 | doc 10 §6.5 |
| `0.8 < t_start < 10 s` | `P1` 5/24, `P2` 2/24 | doc 10 §10.1 |
| nazoratsiz `p99` / `p90` / budjet ichida | 7.1958 s / 5.4042 s / 0/6 | doc 10 §6.3; `08` §15.3 |
| `ramp_above_threshold_s` | 0.000 s, 29/29 (`base_mb = 184`) | doc 10 §4.1 |
| invariant 2 (12 s) | `12 + 0 = 12 ≤ 15`, 3.000 s zaxira | doc 10 §4.2 |
| 15 s da invariant 2 | `15 + 0 = 15 ≤ 15` | doc 10 §12.4 |
| budjet arifmetikasi | `0.1 + t_start + 0.1 ≤ 1`; gate'li `+ 0.3` | `PREREGISTRATION.md` §17.2 |
| `thr` (o'lchangan) `P0`/`P1`/`P2` | 0.0600 / 0.1700 / 0.2050 s | doc 10 §7.5 |
| `D_probe` proxy mean `P0`/`P1`/`P2`; max | 0.3000 / 0.8500 / 1.0250 s; 0.300 / 1.700 / 2.200 s | doc 10 §7.2 |
| `thr` mustaqil o'lchov | 0.0967 s = 0.97 × P (mean 0.4833 s) | `PREREGISTRATION.md` §21.3 |
| `thr` derived | 0.048–0.088 s | §18.4 formulasi + doc 10 §6.2 `P0` p50 0.0386 s |
| O1–O4 va narxlari; `p90 ≤ 0.8 s` qoidasi | — | `PREREGISTRATION.md` §17.5 |
| F1–F4 va narxlari; `thr ≥ ~5P` qoidasi; τ bog'liqligi | — | `PREREGISTRATION.md` §18.6 |
| `thr < P ⟺ R < 0.5 s`; F2 yuqori degeneratsiya `R > 6.4 s` | — | `PREREGISTRATION.md` §19.3 |
| arm'lar `A`, `no_action`; arm C muzlatilmagan | — | `PREREGISTRATION.md` §9.3, §13, §0 |
| `systemd-oomd` yo'q | binary/unit/config yo'q | doc 07 §6.4 |
| guard: 1 trip / 35 epizod | `rate = 0.9801962`, `kill_ok: true` | doc 10 §8.2 |
| `HOLD_CAP_S = 12.0` | `revix/schedule.py:50` @ `76fa33c` | kod |

---

## 10. Aloqador hujjatlar

- [`10-pressure-dozalash.md`](10-pressure-dozalash.md) — barcha o'lchovlar (§4, §6, §7, §10, §12).
- [`08-guard-rekalibratsiya.md`](08-guard-rekalibratsiya.md) — nazoratsiz to'yinish o'lchovi, §14.5 ning ikki qaror jadvali.
- [`07-wsl-muhit-tekshiruvlari.md`](07-wsl-muhit-tekshiruvlari.md) — `systemd-oomd` yo'qligi (§6.4).
- `PREREGISTRATION.md` — §9.3/§9.4, §17, §18, §19.3, §21.
