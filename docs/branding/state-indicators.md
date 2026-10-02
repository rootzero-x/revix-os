# State indicators — holatlar uchun vizual til

Vizual varaq: [`state-indicators.svg`](state-indicators.svg) (yetti holatning glyph'lari
`<symbol id="st-*">` sifatida shu faylda, GUI ularni to'g'ridan-to'g'ri nusxalaydi).
Palitra: [`00-design-system.md`](00-design-system.md) §2, §5.

---

## 1. Bitta qoida, qolgani undan kelib chiqadi

> **O'lchanmagan qiymat hech qachon o'lchangan qiymat kabi ko'rinmaydi. Hali bajarilmagan
> qadam hech qachon bajarilgan kabi ko'rinmaydi.**

Loyihada `None` = **o'lchanmadi**, `0` dan farqli (`CONTRIBUTING.md` §4). Instrumentatsiya
yo'qolishi **hech qachon jimgina natijaga aylanmaydi**: probe uzilishi >2×P bo'lsa trial
`censored`, **`failed` emas** (`PREREGISTRATION.md` §4; `censored` ning ikki ma'nosi — §16 (B)). Figura kalit yo'q bo'lganda "kamroq
chizadi va nima yo'qligini aytadi" (`docs/architecture/04-driver-va-analiz-shartnomasi.md` §3.1).
Bu hujjat o'sha intizomni **belgilarga** ko'chiradi.

**NEGA bu qoida alohida hujjat:** `healthy` yoki `failed` yetarli ko'rinadi, lekin ularning
*yo'qligini* ko'rsatishning o'z tili bo'lmasa, UI bo'sh joyni **nol** yoki **OK** deb o'qitadi.
Tadqiqot instrumenti uchun bu — eng og'ir xato: ishlamagan o'lchovdan "yaxshi" natija chiqadi.

---

## 2. Yetti holat

Holatlarning mashina qiymati (`state`) — yopiq enum, **tarjima qilinmaydi**:
`healthy | recovering | degraded | isolated | failed | not_measured | not_run`.

| Holat | Glyph (silhouet + to'ldirish) | CLI tegi | Rang token | Ma'nosi (loyiha atamalarida) |
|---|---|---|---|---|
| **healthy** | **to'ldirilgan doira** | `[ OK ]` | `--rx-ok` | Joriy probe oynasida contract'dan o'tmoqda **va**, agar action bo'lgan bo'lsa, epizod **VR** bajargan (`PREREGISTRATION.md` §4) |
| **recovering** | **yarim to'ldirilgan doira** (o'ng yarmi to'la) | `[ .. ]` | `--rx-fg-1` (neytral) | Action berilgan; `[t_up, t_up + W_stab]` oynasi **hali yopilmagan**; invalidator yo'q |
| **degraded** | **to'ldirilgan uchburchak** | `[ /\ ]` | `--rx-fg-1` (neytral) | Jarayon tirik (`F_sd` failure bermagan), lekin **contract yoki throughput bandi buzilgan** (`contract_fail`, `throughput_below_theta`) va epizod hali yakuniy failed emas |
| **isolated** | **kesilgan doira** (halqa + gorizontal chiziq) | `[ || ]` | `--rx-fg-1` (neytral) | Kuzatilayotgan element **qasddan ajratilgan** (host guard ishga tushgan, ekskluziya). **Hukm emas** |
| **failed** | **to'ldirilgan kvadrat, ichida kesilgan X** | `[FAIL]` | `--rx-fail` | Failure aniq aniqlangan (`F_sd` yoki `F_probe`) va VR bajarilmagan, yoki horizon down holatda tugagan (`VR = false` kuzatilgan, `PREREGISTRATION.md` §16 (B)). **Aniq** — taxminiy emas |
| **not measured** | **shtrixlangan kvadrat** (diagonal chiziqlar, ichi to'la ko'rinadi) | `[ n/m ]` | `--rx-fg-2` | Run **bo'lgan**, lekin asbob bu qiymat uchun **qiymat bermadi** (`None`). **Sabab MAJBURIY** |
| **not run** | **punktir kvadrat** (ichi bo'sh) | `[ n/r ]` | `--rx-fg-2` | Bu qadam **hali bajarilmagan**. Qiymatni hosil qiluvchi run mavjud emas |

**Qoida H-1.** Faqat **healthy** (yashil) va **failed** (qizil) signal rangiga ega. Qolgan beshtasi
neytral kulrang (`--rx-fg-1` yoki `--rx-fg-2`). **NEGA:** `00-design-system.md` §5.3, N3–N4 —
tasdiqlanmagan holat va yo'q ma'lumotga signal rangi berish ularni "yaxshi yo'l" yoki "yomon yo'l"
ga joylaydi. Va §12.7: sariq/amber **qo'shilmaydi**.

**Qoida H-2.** `healthy` tegining yonida predicate yoziladi (`VR`, `contract ok`, `15 PASS`).
**NEGA:** `00-design-system.md` §5.1 Y1.

**Qoida H-3.** `recovering` da `elapsed / W_stab` — oddiy raqam, o'lchangan bo'lsa. Animatsiyali
progress yo'q. **NEGA:** `00-design-system.md` §9, F3.

### 2.1 Bu ta'riflar nima asosida — va nima asosiz

`PREREGISTRATION.md` da **`healthy`, `recovering`, `degraded`, `isolated` nomli holatlar ta'riflanmagan**.
Ular shu hujjatda **dizayn taklifi** sifatida §3 (failure detektorlari), §4 (VR) va §12
(disposition enum'i) tushunchalaridan **olingan**. Ma'no o'zgartirilishi mumkin; **`not_measured`
va `not_run` esa loyihaning o'z qoidalaridan to'g'ridan-to'g'ri keladi** (`CONTRIBUTING.md` §4;
`README.md`: "Hech qanday eksperiment hali ishga tushirilmadi").

`isolated` ayniqsa ehtiyotkorlik talab qiladi: arm C siyosati va uning "izolyatsiya" amali
`PREREGISTRATION.md` §0 va §13 bo'yicha **hali belgilanmagan va muzlatilmagan**. Hozircha `isolated` faqat
quyidagilarga mos keladi:

| `isolated` bo'ladi | Manba |
|---|---|
| trial `aborted_guard` (host guard ishga tushdi) | `PREREGISTRATION.md` §12 |
| trial `contaminated` (biz yubormagan SIGKILL, bystander buzildi, cheklanmagan cgroup'da oom_kill) | `PREREGISTRATION.md` §12 |

**`aborted_guard`/`contaminated` ulushi natija sifatida beriladi, yashirilmaydi** (`PREREGISTRATION.md` §12).
Shuning uchun `isolated` — o'chirilgan qator emas, ko'rinadigan, neytral belgi. **NEGA neytral:**
bu xizmatning hukmi emas, asbob chegarasining belgisi (`00-design-system.md` §5.2, Q2).

---

## 3. Holatni aniqlash tartibi

Quyidagi tartib **majburiy**: yuqoridagi qoida birinchi mos kelganini beradi.

```
1. Qiymatni hosil qiluvchi qadam bajarilmaganmi?            -> not_run
2. Qadam bajarilgan, lekin qiymat None / kalit yo'q /
   probe_gap (probe uzilishi > 2xP)?                        -> not_measured   (+ reason)
3. Aks holda o'lchangan holatlardan biri:
   VR bajarilgan va oyna yopilgan                           -> healthy
   action berilgan, oyna yopilmagan                         -> recovering
   jarayon tirik, contract/band buzilgan                    -> degraded
   guard / contaminated                                     -> isolated
   failure aniqlangan, VR yo'q (jumladan down_at_horizon)   -> failed
```

**NEGA `not_run` va `not_measured` har doim birinchi:** o'lchangan holat faqat **o'lchov mavjud
bo'lganda** talqin qilinadi. 1–2-bandlar o'tkazib yuborilsa, `None` "healthy" ga yoki "0" ga
yashirinib ketadi — loyiha aynan shundan qochadi.

**`censored` ikkiga bo'linadi — va ikki holat ikki xil ko'rsatiladi** (`PREREGISTRATION.md` §16 (B)):

| `disposition_source` | Nima bo'ldi | Holat |
|---|---|---|
| `probe_gap` (probe uzilishi > 2×P) | instrumentatsiya yo'qoldi: natija **kuzatilmadi** | **`not_measured`** (`reason=probe_gap`), `failed` **emas** (§4) |
| `down_at_horizon` (horizon down holatda tugadi) | xizmat qaytmadi: **`VR = false` kuzatildi** | **`failed`**: bu to'liq aniqlangan natija, yetishmayotgan kuzatuv emas |

**NEGA shunday:** ikkalasini bitta "censored/unknown" belgisiga birlashtirish — yo `probe_gap` ni
`failed` qilib jimgina natija yaratadi, yo `down_at_horizon` ni `not_measured` qilib haqiqiy
qizil natijani yashiradi. §16 (B) aynan shu ikkisini ajratadi. Aniqlanmagan trial'lar ham hech
qachon "recovered emas" ga qo'shilmaydi (driver shartnomasi §3.1, `n_undetermined`).

### 3.1 Aggregatsiya (guruh, jadval sarlavhasi, KPI)

- **A-1.** Guruh yagona glyph bilan **faqat barcha a'zolari bir xil holatda** bo'lganda ko'rsatiladi.
  Aks holda — **sanoq**: `7 healthy · 2 failed · 1 n/m · 3 n/r`.
- **A-2.** Nisbat/o'rtacha **faqat o'lchanganlar** ustida hisoblanadi va maxraj yoziladi:
  `0.82 (41 of 50 measured)`. `n/m` va `n/r` **ham 0 sifatida, ham chiqarib tashlangan holda jim**
  hisobga olinmaydi.
- **A-3.** Guruhda bitta `n/m` bo'lsa — guruhning qiymati `n/m` bilan **izohlanadi**, aks holda bo'lmaydi.
- **A-4.** Saralash: `n/m` va `n/r` qatorlari **alohida blok** (oxirida), sonli saralashga **aralashmaydi**
  va `0` sifatida eng pastga tushmaydi.

**NEGA:** yo'q ma'lumotning jim chiqarilishi — eksklyuziya, eksklyuziya darajasi esa **natija**
(`README.md`, "Ilmiy yaxlitlik"; `PREREGISTRATION.md` §12).

---

## 4. "Not measured" va "not run": nega ular boshqacha va qanday ajratiladi

### 4.1 Ular nimadan farq qiladi

| Taqqoslash | Healthy | Zero (`0`, `0 ms`, `0%`) | Not measured | Not run |
|---|---|---|---|---|
| Qiymat bor | ha | **ha** (o'lchangan nol) | **yo'q** | **yo'q** |
| Run bo'lgan | ha | ha | **ha** | **yo'q** |
| Raqam ko'rsatiladi | yo'q (predicate bor) | **ha** | **hech qachon** | **hech qachon** |
| Glyph | to'la doira | (glyph yo'q, oddiy raqam) | shtrixlangan kvadrat | punktir kvadrat |
| Matn | `OK` + predicate | `0 ms` + birlik | `n/m` + `reason=…` | `n/r` |
| Rang | yashil | `--rx-fg-0` | `--rx-fg-2` | `--rx-fg-2` |

### 4.2 Not measured — vizual til (MAJBURIY elementlar)

1. **Naqsh:** diagonal shtrix (`--rx-hatch`, 45°, 1 px, davr 4 px, `--rx-fg-2`) **qiymat joyida**. Hech qachon ochiq/bo'sh emas.
2. **Chegara:** to'liq (punktirsiz) `1px solid --rx-fg-2` (`--rx-border-strong`).
3. **Matn:** `n/m` (zich) yoki `NOT MEASURED` (to'liq). Matn **qattiq fon plitasi** ustida
   (`--rx-bg-0`), shtrix ustida emas — shtrix chiziqlari matn o'qilishini pasaytiradi (bu sinovda
   `state-indicators.svg` da haqiqatan kuzatildi va plita bilan tuzatildi).
4. **Sabab (`reason`) majburiy.** Sababsiz `n/m` — taqiq. Sabab kodlari yopiq lug'at bo'lishi kerak;
   quyidagilar **illyustrativ takliflar** (amalga oshiruvchi to'g'rilaydi): `probe_gap`
   (probe uzilishi >2×P), `key_absent` (`analysis.json` da kalit yo'q), `sysfs_absent`
   (interfeys yo'q — masalan, bu mashinada `cpufreq`, `docs/architecture/07-wsl-muhit-tekshiruvlari.md` §6.1),
   `horizon_not_reported`, `time_unit_not_declared`.
5. **Hech qachon:** raqam, `0`, `—`, bo'sh katak, `N/A`.

**NEGA `N/A` ham taqiq:** "not applicable" — qiymat bu yerda **mavjud emas** degan **da'vo**. `n/m` esa
"mavjud, lekin o'lchanmadi" deydi. Ikkalasini aralashtirish — ikkinchi xato turi.

### 4.3 Not run — vizual til

1. **Ichi bo'sh** (to'ldirishsiz), **punktir** chegara `1.5px dashed --rx-fg-2` (dash/gap teng).
2. Matn `n/r` yoki `NOT RUN`, `--rx-fg-2`.
3. Sabab shart emas (hali bajarilmagan — sababning o'zi), lekin **nima kutilayotgani** yozilishi mumkin
   (`pilot kalibratsiyasi pilotni gate qiladi`, `README.md` "Holat" jadvali).
4. **Hech qachon:** to'ldirilgan, yashil, "0".

### 4.4 Ikkalasini bir-biridan ajratish

| Kanal | Not measured | Not run |
|---|---|---|
| To'ldirish | **shtrix bor** ("yozilgan, lekin o'qib bo'lmaydi") | **bo'sh** ("hali chizilmagan") |
| Chegara | **yaxlit** | **punktir** |
| Matn | `n/m` + sabab | `n/r` |
| Ma'no | run bo'ldi, qiymat yo'q | run yo'q |

### 4.5 Rangsiz kirish imkoniyati (rang yagona kanal emas)

Har holat **beshta mustaqil kanal** bilan aytiladi; rang ulardan faqat bittasi va **eng zaifi**:

1. **Silhouet** — doira / yarim doira / uchburchak / kesilgan doira / kvadrat (to'la, shtrix, punktir).
2. **To'ldirish turi** — to'la, yarim, outline, shtrix, bo'sh.
3. **Matn yorlig'i** — doim (`HEALTHY` … `NOT RUN`); zich jadvalda `[ n/m ]` tegi + legend.
4. **Dasturiy ma'no:** `data-state="not_measured"`, `role="img"`, `aria-label="not measured, reason: probe_gap"`.
   Ekran o'quvchi `n/m` ni "n slash m" deb o'qimaydi.
5. **Joylashuv:** `n/m` / `n/r` katagida **hech qachon raqam yo'q**; ular raqamli ustunga aralashib "0" bo'la olmaydi.

**Sinov (bajarildi):** `state-indicators.svg` ikkinchi bloki — har rang unga **teng relative luminance'li kulrangga**
almashtirilgan: yashil → `#ACACAC`, qizil → `#888888`, neytral o'zgarishsiz. Natijada failed (`#888888`),
not measured (`#888888`) va not run (`#888888`) **bir xil kulrang**, lekin silhouet va to'ldirish bilan ajraladi
(ko'zdan kechirildi). Bu **simulyatsiya**; haqiqiy printer yoki rang-ko'r foydalanuvchi bilan sinalmagan.

**Minimal o'lcham:** glyph ≥ 16 px; chiziq 1.5 birlik (16 birlik gridda). `--rx-fg-2` chiziqlar `bg-0` ga nisbatan
5.65:1 (3:1 dan yuqori).

### 4.6 Eksport va mashina qiymatlari

| Holat | JSON / CSV |
|---|---|
| not measured | `null` (+ `reason` maydoni). **`0`, `""`, `"NaN"` emas** |
| not run | qator/kalit **yo'q** yoki `"state": "not_run"`; **hech qachon `null` ning o'zi emas** (u `n/m` bilan aralashadi) |

**NEGA:** `None` — o'lchanmadi (`CONTRIBUTING.md` §4). CSV da bo'sh qiymat ko'pgina vositalarda `0` ga
aylanadi — shuning uchun `n/m` uchun aniq belgi (`reason`) talab qilinadi.

---

## 5. ASCII / CLI shakli

Joriy CLI inson chiqishi ASCII (`--`, `|`; `render_doctor_human` va `format_check_human` qatorlari, `revix/cli.py`; Unicode faqat izohlarda). Teglar 6 belgili:

```
[ OK ]   healthy        [FAIL]   failed
[ .. ]   recovering     [ n/m ]  not measured  (reason=<kod> MAJBURIY)
[ /\ ]   degraded       [ n/r ]  not run
[ || ]   isolated
```

`revix doctor` ning `PASS / WARN / FAIL` — **tekshiruv natijasi**, xizmat holati emas (boshqa o'q).
Moslik: `PASS` → healthy rangi (`--rx-ok`), `FAIL` → failed rangi (`--rx-fail`), `WARN` → neytral `[ /\ ]`;
bajarilmagan tekshiruv → `[ n/r ]`.

Terminalda naqsh yo'q; shuning uchun `n/m` ni **matn va `reason=`** ajratadi (`terminal-theme.md` T5).

---

## 6. Glyph geometriyasi (16 × 16 grid, `currentColor`)

| Glyph | Geometriya |
|---|---|
| `st-healthy` | doira `r=6`, to'la |
| `st-recovering` | halqa `r=5.25` chiziq 1.5 + o'ng yarim disk (`M8 2A6 6 0 0 1 8 14Z`) |
| `st-degraded` | uchburchak `(8,2) (14.5,13.5) (1.5,13.5)`, to'la |
| `st-isolated` | halqa `r=5.25` chiziq 1.5 + gorizontal chiziq `y=7.25..8.75`, `x=2..14` |
| `st-failed` | kvadrat `2..14`, ichidan `evenodd` bilan X kesilgan (12 uchli ko'pburchak) |
| `st-not-measured` | kvadrat kontur `2.75..13.25`, chiziq 1.5, ichida 45° chiziqlar (1.25), kontur bo'yicha kesilgan |
| `st-not-run` | kvadrat kontur `2.75..13.25`, chiziq 1.5, `stroke-dasharray="2.1 2.1"` |

HTML da ishlatish (qisqa namuna; **to'liq komponent `feature/gui` ga tegishli**):

```html
<span class="rx-state" data-state="not_measured" role="img"
      aria-label="not measured, reason: probe_gap">
  <svg width="16" height="16"><use href="#st-not-measured"/></svg>
  <span class="rx-state__tag">n/m</span>
</span>
```

```css
.rx-cell--not-measured { background: var(--rx-bg-1) var(--rx-hatch); border: var(--rx-border-strong); }
.rx-cell--not-measured .rx-cell__label { background: var(--rx-bg-0); color: var(--rx-fg-1); }
.rx-cell--not-run { background: transparent; border: 1.5px dashed var(--rx-fg-2); color: var(--rx-fg-2); }
```

---

## 7. Tekshirilgan va tekshirilmagan

**Tekshirildi:**
- Yetti glyph `state-indicators.svg` da Browser pane da ko'rildi (rangli va luminance-simulyatsiya bloklari);
  har juftlik silhouet bilan ajraldi.
- Shtrix ustidagi matn o'qilishi pastligi kuzatildi va qattiq plita bilan tuzatildi (§4.2, 3-band).
- `--rx-fg-2` (`#888888`) outline kontrastlari hisoblangan (5.65 / 5.15).

**Tekshirilmadi:**
- Haqiqiy ekran o'quvchi bilan `aria-label` o'qilishi.
- Haqiqiy printer; rang-ko'r foydalanuvchi.
- **16 px da** shtrix (to'rt chiziq) va punktir (besh bo'lak) glyph'lari DPR 1 da: ko'rilganda ajraldi
  (DPR 1.25, kichraytirilgan skrinshot), lekin fizik 16 px da sinalmagan.
- Holat ta'riflarining (§2.1) loyiha egasi tomonidan tasdiqlanishi: `healthy`, `recovering`, `degraded`, `isolated`
  nomlari `PREREGISTRATION.md` da yo'q.
- Sabab kodlari ro'yxati — taklif; yopiq lug'at hali yo'q.
