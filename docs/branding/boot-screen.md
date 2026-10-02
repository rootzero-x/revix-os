# Boot screen — REVIX

Konsept: [`boot-screen.svg`](boot-screen.svg) (ikki kadr). Holat tegi va ranglar:
[`state-indicators.md`](state-indicators.md), [`00-design-system.md`](00-design-system.md).

> Bu **konsept**. Hech qanday kod yozilmagan; `revix/cli.py` ga tegilmagan (fayl egaligi: `feature/gui`
> va CLI egalari). SVG dagi raqamlar **jonli o'lchov emas** — kadr 2 dagi sonlar `README.md` ning
> "O'lchangan holat" blokidan (2026-10-02, shu mashina) ko'chirilgan va SVG da shunday belgilangan.

---

## 1. Printsip: boot screen — asbobning o'zini-o'zi tavsifi, shou emas

Boot screen foydalanuvchiga **bitta narsani** aytadi: *asbob nima, va hozir nimasi ma'lum.*
"Tayyor" demaydi, agar tayyor ekani o'lchanmagan bo'lsa.

**NEGA:** o'lchov asbobi ishga tushganda o'z holatini haqiqatan bilmaydi — `revix doctor` hali
ishga tushmagan bo'lishi mumkin. Shu paytda "System ready ✓" yozilsa, bu aynan loyiha rad etgan
narsa: o'lchanmagan holatni o'lchangan kabi ko'rsatish (`CONTRIBUTING.md` §4;
`README.md`: "Hech qanday eksperiment hali ishga tushirilmadi").

---

## 2. Nima ko'rsatiladi

Ikki kadr (`boot-screen.svg`):

**Kadr 1 — ishga tushgan zahoti.** Hech narsa tekshirilmagan, shuning uchun hamma qator `[ n/r ]`:

```
REVIX  0.1.0-dev
Linux service recovery o'lchov asbobi

muhit        [ n/r ]  `revix doctor` hali ishga tushirilmagan
guard        [ n/r ]  guard hali ishga tushirilmagan
eksperiment  [ n/r ]  hech qanday eksperiment ishga tushirilmagan
natija       [ n/r ]  hech qanday natija yo'q

keyingi qadam: revix doctor
```

**Kadr 2 — `revix doctor` dan keyin** (ILLUSTRATIV; raqamlar `README.md` dan, jonli emas):

```
muhit        [ OK ]   15 PASS, 0 FAIL
muhit        [ /\ ]   3 WARN
cpufreq      [ n/m ]  sysfs interfeysi yo'q (reason: sysfs_absent)
guard        [ n/r ]  guard hali ishga tushirilmagan
eksperiment  [ n/r ]  hech qanday eksperiment ishga tushirilmagan
natija       [ n/r ]  hech qanday natija yo'q
```

Kadr 2 da `[ n/m ]` qatori **ataylab** kiritilgan: bu mashinada `cpufreq` interfeysi yo'q va
shu sababli `PREREGISTRATION.md` §8.5 tekshiruvi mumkin emas
(`docs/architecture/07-wsl-muhit-tekshiruvlari.md` §6.1; `README.md`: "`cpufreq` va `thermal_zone` sysfs
interfeyslari **yo'q**"). Bu — "not measured" ning haqiqiy misoli, va u **nol** ham, **OK** ham
ko'rsatilmaydi. `sysfs_absent` — illyustrativ sabab kodi (`state-indicators.md` §4.2, 4-band).

### 2.1 Qatorlar manbasi

| Qator | Qaerdan | Boot paytida |
|---|---|---|
| sarlavha `REVIX <versiya>` | `VERSION` fayli (joriy: `0.1.0-dev`) | doim |
| `muhit` | `revix doctor` natijasi (`PASS/WARN/FAIL`, `revix/cli.py`) | ishga tushmagan bo'lsa `n/r` |
| `guard` | mustaqil guard jarayoni (`revix/guard.py`) | ishlamayotgan bo'lsa `n/r` |
| `eksperiment` | `datasets/` dagi run'lar (append-only) | bo'sh bo'lsa `n/r` |
| `natija` | `analysis.json` mavjudligi | yo'q bo'lsa `n/r` |

**Boot paytida hech narsa bajarilmaydi** (doctor ham, guard ham, probe ham). Boot screen faqat
**allaqachon ma'lum** narsani ko'rsatadi.
**NEGA:** (a) boot — o'lchov emas; unda hosil bo'lgan "natija" hech qaysi pre-registration qoidasiga
tegishli emas; (b) pressure bilan bog'liq hech narsa kutilmagan paytda boshlanmasligi kerak
(`README.md` "Xavfsizlik ogohligi": pressure eksperimenti desktop sessiyani o'ldirishi mumkin).

---

## 3. Qoidalar

| # | Qoida | NEGA |
|---|---|---|
| **B1** | Bitta ekran: **≤ 24 qator, ≤ 80 ustun** | terminal ichida skroll qilinmaydigan, log'ga bir xil tushadigan chiqish |
| **B2** | **Animatsiya yo'q**: harf-harf yozuv, spinner, progress bar, "yuklanmoqda" nuqtalari yo'q. Chiqish bir marta, to'liq | `00-design-system.md` §9, F3; "tirik tizim" taassuroti o'lchov asbobi uchun yolg'on |
| **B3** | **ASCII-art banner yo'q** (figlet, ajdaho, katta harf yozuv). Birinchi qator — `REVIX <versiya>` | soxta-hacker estetikasi (F4) va Kali bilan o'xshashlik (F7) |
| **B4** | Har qator: `nom`, holat tegi (`[ OK ]`…`[ n/r ]`), **bitta fakt** | qator o'z-o'zidan tushunarli bo'lishi va `grep` qilinishi kerak |
| **B5** | **"Ready", "OK", "Secure", "Online" kabi umumiy xulosa yo'q.** Faqat qatorlar | umumiy xulosa o'lchanmagan qismlarni yashiradi (`state-indicators.md` §3.1, A-1) |
| **B6** | `n/m` qatorida **sabab** (`reason: …`) MAJBURIY | `state-indicators.md` §4.2 |
| **B7** | Rang faqat `[ OK ]` (yashil) va `[FAIL]` (qizil) tegida; qolgani neytral. `NO_COLOR` / non-TTY da — rangsiz | `terminal-theme.md` T1–T3; teg matn bo'lgani uchun ma'no yo'qolmaydi |
| **B8** | Taglavha — **tavsif**: "Linux service recovery o'lchov asbobi". Shior, va'da, sifat so'zi ("aqlli", "ishonchli") yo'q | `00-design-system.md` §11; `04-novelty-statement.md` |
| **B9** | Qatorlar tartibi qat'iy: `muhit → guard → eksperiment → natija` | qat'iy tartib: ikki boot chiqishi (skrinshot, log) qator-ma-qator taqqoslanadi (`diff`) |
| **B10** | Jim rejim (`--quiet`) mavjud bo'lishi kerak; boot screen skript chiqishiga qo'shilmaydi | CLI chiqishi boshqa vositalarga ulanadi |

### 3.1 Hech qachon ko'rsatilmaydi

- Soxta yuklanish ketma-ketligi, tasodifiy hex/raqamlar oqimi, "ACCESS GRANTED".
- Mashina nomi, IP, foydalanuvchi nomi (kerak emas va maqolaga skrinshot qilinganda tarqaladi).
- `0` yoki `OK` — tekshirilmagan narsa uchun.
- Hech qanday xavfsizlik da'vosi (`secure`, `hardened`) — REVIX xavfsizlik vositasi emas.

---

## 4. GUI varianti

GUI da (`feature/gui`) boot screen — bosh sahifaning sarlavha polosasi: chapda `logo.svg` (`--rx-fg-1`),
o'ngda versiya; pastida shu to'rt qator **jadval qatori** sifatida (`--rx-row-height`), glyph + tag + fakt.
Qoidalar B2–B8 o'zgarishsiz. **NEGA:** CLI va GUI bir xil faktni, bir xil tilda aytishi kerak; aks holda
ikki sirt bir-biriga zid ko'rinadi.

---

## 5. Ochiq masalalar

- **Pre-registration versiyasi va hash.** `README.md` "ta'riflar hash bilan run'ga bog'lanadi" deydi;
  boot screen unga bir qator (`ta'riflar  v… · sha256:…`) qo'shishi mumkin. Joriy versiyani men
  bilmayman (README `v1.4`, so'nggi commit `v1.6` deydi — nomuvofiqlik, men tuzatmadim), shuning uchun
  konseptga qo'shilmadi.
- **Kadr 2 dagi `muhit` qatori ikkiga bo'lingan** (`15 PASS, 0 FAIL` va `3 WARN`) — `0 FAIL` ni
  predicate sifatida yashil teg bilan yonma-yon ko'rsatish uchun. Bitta qatorda ham mumkin; qaror GUI egasiga.
- Boot screen `revix doctor` natijasini **saqlangan** holda ko'rsatishi mumkinmi (`n/r` o'rniga oxirgi
  natija + vaqt belgisi)? Bu saqlash joyini talab qiladi — branding doirasidan tashqarida.

## 6. Tekshirilgan va tekshirilmagan

**Tekshirildi:** `boot-screen.svg` XML sifatida parse qilindi va Browser pane da ochilib ko'rildi
(ikki kadr, ustunlar tekislangan, matn o'qiladi). Versiya `VERSION` faylidan (`0.1.0-dev`) olingan.

**Tekshirilmadi:** haqiqiy terminalda (80 ustun) ko'rinishi — SVG tizim monospace shriftida,
ustunlar x koordinata bilan tekislangan; haqiqiy CLI chiqishi probel bilan tekislanadi va farq qilishi mumkin.
CLI da amalga oshirilmagan.
