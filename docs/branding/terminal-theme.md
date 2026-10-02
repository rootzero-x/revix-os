# Terminal theme — REVIX

Palitra: [`00-design-system.md`](00-design-system.md) §2. Bu hujjat o'sha palitradan
16 ANSI rangini, asosiy ranglarni va CLI chiqishi qoidalarini chiqaradi.

Fayllar (bir xil qiymatlar):

| Fayl | Terminal |
|---|---|
| [`terminal-theme.windows-terminal.json`](terminal-theme.windows-terminal.json) | Windows Terminal (`schemes` ro'yxatiga qo'shiladi) |
| [`terminal-theme.alacritty.toml`](terminal-theme.alacritty.toml) | Alacritty (`[colors.*]` sxemasi) |

Qiymatlarning yagona manbai — shu hujjatdagi §1–§2 jadvallari.

---

## 1. Asosiy ranglar

| Rol | Hex | Token | `#080808` ga nisbatan kontrast |
|---|---|---|---|
| background | `#080808` | `--rx-bg-0` | — |
| foreground | `#D4D4D4` | `--rx-fg-1` | 13.51:1 |
| cursor | `#FFFFFF` (matn `#080808`) | `--rx-fg-0` | 20.03:1 |
| selection background | `#444444` | `--rx-line` | — |

Tanlangan matn (`selection`): `#D4D4D4` / `#444444` = **6.57:1**; `#FFFFFF` / `#444444` = 9.74:1;
**`#888888` / `#444444` = 2.75:1** (tanlangan ikkilamchi matn o'qilishi yomonlashadi).

**NEGA foreground `#D4D4D4`, `#FFFFFF` emas:** 20:1 kontrast uzoq o'qishda charchatadi; `#FFFFFF`
`--rx-fg-0` ni **urg'u** uchun saqlaydi (bright white). Oddiy matn va urg'u orasidagi farq
shu tarzda ko'rinadigan bo'lib qoladi.

---

## 2. 16 ANSI rangi

Kontrast — fon `#080808` (asosiy) va `#151515` (status qator, panel) ga nisbatan; hammasi hisoblangan.

| ANSI | Nom | Hex | Kontrast `#080808` | Kontrast `#151515` | Izoh |
|---|---|---|---|---|---|
| 0 | black | `#444444` | **2.06** | **1.87** | pastroq 3:1; **faqat bezak/xira matn, ma'lumot tashimaydi** |
| 1 | red | `#E53935` | 4.74 | **4.32** | `#151515` da 4.5 dan past |
| 2 | green | `#22C55E` | 8.79 | 8.01 | |
| 3 | yellow | `#888888` | 5.65 | 5.15 | neytral (§2.1) |
| 4 | blue | `#888888` | 5.65 | 5.15 | neytral (§2.1) |
| 5 | magenta | `#888888` | 5.65 | 5.15 | neytral (§2.1) |
| 6 | cyan | `#888888` | 5.65 | 5.15 | neytral (§2.1) |
| 7 | white | `#D4D4D4` | 13.51 | 12.32 | default foreground bilan bir xil |
| 8 | bright black | `#888888` | 5.65 | 5.15 | "xira matn" (izoh, placeholder) |
| 9 | bright red | `#FF3B30` | 5.65 | 5.15 | |
| 10 | bright green | `#00C853` | 8.95 | 8.16 | |
| 11 | bright yellow | `#D4D4D4` | 13.51 | 12.32 | neytral |
| 12 | bright blue | `#D4D4D4` | 13.51 | 12.32 | neytral |
| 13 | bright magenta | `#D4D4D4` | 13.51 | 12.32 | neytral |
| 14 | bright cyan | `#D4D4D4` | 13.51 | 12.32 | neytral |
| 15 | bright white | `#FFFFFF` | 20.03 | 18.26 | |

### 2.1 Nega sariq, ko'k, magenta, cyan neytral

Palitra — qora + qizil + yashil + neytral. ANSI esa to'rtta qo'shimcha hue talab qiladi.
Ularni **toza hue** bilan to'ldirish identitetni buzadi (neon/kiberpank — `00-design-system.md` §9, F5;
ko'k esa Kali'ning asosiy rangi — F7). Shuning uchun ular **neytral pog'onaga** tushirildi:
normal 3–6 = `#888888`, bright 11–14 = `#D4D4D4`.

**NEGA bu qabul qilinadigan narx:** REVIX o'z chiqishida rangga tayanmaydi (§4); uchinchi tomon
dasturlari (`ls`, `git`, `vim`) esa rangni **dekorativ** ishlatadi, va dekorativ rang bizning
identitetda yo'q. Dekorativ rangning neytralga aylanishi — ataylab natija.

**Nima yo'qoladi (ochiq):**
- Dasturlar sariq/ko'k/magenta/cyan orqali ajratgan farq endi faqat `#888888` va `#D4D4D4` pog'onasi
  (ya'ni normal / bright) bilan ajraladi. `ls --color` kataloglari (ko'k) `#888888` bo'ladi.
- ANSI 3, 4, 5, 6, 8 — **bir xil `#888888`**. ANSI 7, 11, 12, 13, 14 — **bir xil `#D4D4D4`**.
- Normal va bright juftliklar orasida: qizil — relative luminance kontrasti 1.19:1, yashil — **1.02:1**.
  "Bold = bright" ga tayanuvchi dasturda bu farq deyarli ko'rinmaydi.
- Fon rangi sifatida ANSI 0 (`#444444`) ustida oq matn 9.74:1 — yaxshi; foreground sifatida
  `#080808` ustida 2.06:1 — **yomon**. ANSI "qora matn"ni dastur qora fonda ishlatsa o'qilmay qoladi.

### 2.2 Nega ANSI 0 = `#444444`, `#151515` emas

`#151515` fonga nisbatan 1.10:1 — **ko'rinmaydi**. `#444444` 2.06:1 — xira, lekin ko'rinadi.
Ko'rinmas matnni tanlagandan ko'ra xira matn afzal.

---

## 3. REVIX CLI chiqishi uchun qoidalar

Joriy `revix/cli.py` **ANSI chiqarmaydi** (`\033`, `NO_COLOR`, `isatty` — kodda yo'q; tekshirildi,
`grep`). Quyidagilar kelajakdagi rang qo'shuvchi uchun talablar.

- **T1. Rang yagona kanal emas.** Har holat `[ OK ]`, `[FAIL]`, `[ n/m ]` kabi matn tegi bilan
  chiqadi (`state-indicators.md` §5). Rang — qo'shimcha. **NEGA:** CLI chiqishi log fayliga,
  CI ga, `less` ga, nusxalab maqolaga tushadi; rang u yerda yo'qoladi (`00-design-system.md` §4).
- **T2. `NO_COLOR` va non-TTY.** `NO_COLOR` o'rnatilgan yoki `stdout` terminal emas bo'lsa — ANSI chiqarilmaydi.
  **NEGA:** `NO_COLOR` — keng tarqalgan konventsiya; fayl/pipe ga tushgan ANSI kodlari logni
  o'qib bo'lmaydigan qiladi va grep/diff ni buzadi.
- **T3. Faqat ikki SGR rang:** `31` (red) — `FAIL` va `failed` uchun, `32` (green) — `PASS` va `healthy` uchun.
  Boshqa rang kodlari (`33–36`, `90–97` rangli) ishlatilmaydi. **NEGA:** qizil/yashil qoidasi (`00-design-system.md` §5)
  terminalda ham amal qiladi; boshqa kodlar neytralga tushadigan bo'lsa ham, boshqa terminalda
  boshqa rang bo'lib chiqishi mumkin.
- **T4. `WARN` rangsiz.** `[ /\ ] WARN` neytral. **NEGA:** WARN — tasdiqlanmagan, failed ham emas
  (`00-design-system.md` §5.3, N3).
- **T5. `n/m` va `n/r` rangsiz va hech qachon `0`.** `[ n/m ]` + `reason=<kod>` MAJBURIY; `[ n/r ]`.
  Terminalda naqsh yo'q, shuning uchun **matn va sabab** — yagona tashuvchi (`state-indicators.md` §4).
- **T6. Prompt tayinlanmaydi.** REVIX `PS1` yetkazmaydi. Ayniqsa Kali'ning ikki qatorli
  "`┌──(…)-[…]` / `└─$`" prompt uslubi takrorlanmaydi. **NEGA:** `00-design-system.md` §9, F7.
- **T7. Soxta terminal effektlari yo'q:** harf-harf yozuv, "boot" animatsiyasi, soxta progress.
  **NEGA:** `00-design-system.md` §9, F3, F4; `boot-screen.md`.

---

## 4. Tekshirilgan va tekshirilmagan

**Tekshirildi:** barcha kontrast nisbatlari hisoblangan (§1–§2); JSON va TOML fayllar sintaksis
jihatidan parse qilindi va ularning 16 ANSI + asosiy qiymatlari §2 jadvali bilan skript orqali
solishtirildi.

**Tekshirilmadi:**
- Temalar **Windows Terminal'da ham, Alacritty'da ham yuklab ko'rilmadi**; faqat fayl sintaksisi.
  Alacritty `text = "CellForeground"` (selection) qiymatining hujjatdagi sxemaga mosligi — xotiradan.
- WSL2 Kali ichidagi haqiqiy dasturlar (`ls`, `git diff`, `vim`) bu temada qanday ko'rinishi.
- Bright = bold xatti-harakati terminalga qarab farq qiladi; sinalmagan.
