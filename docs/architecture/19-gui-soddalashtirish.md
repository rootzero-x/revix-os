# 19 — GUI'ni soddalashtirish: oddiy foydalanuvchi uchun dashboard

**Holat:** `agent/gui-clarity` branch'i (main `9a3530d` dan). Fayllar:
`revix/gui.py`, `revix/gui_assets/style.css`, `revix/gui_assets/app.js`,
`tests/unit/test_gui.py`, shu jurnal va `docs/architecture/img/19-gui-*.png`.

**Muammo (foydalanuvchi so'zi):** "ui umuman tushunarsizku". Birinchi ekran
tadqiqotchi uchun yozilgan zich matn edi: 11 tabli menyu, `SYSTEM HEALTH`,
`host cpu some stall 0.6421`, `SwapTotal 0 kiB [O'LCHANGAN NOL]`, `manba yo'q`
va ichida `cgroup.snapshot_cgroup()` bo'lgan uzun punktir qutilar. Oddiy odam
10 soniyada "tizimim yaxshimi? REVIX nima? nima qilay?" degan savollarga javob
topa olmasdi.

**Maqsad:** birinchi qarashda tushunarli bo'lish, lekin loyihaning ilmiy
halollik qoidalarini (`gui.py` docstring qoidalari 1–10) BUZMASDAN.

---

## §1. Yangi "Bosh sahifa" (`/`)

Ildiz endi `page_home`. Birinchi ekran (1280x800) aylantirmasdan ko'rsatadi:

1. **Holat jumlasi (hero):** belgi + rang + so'z. Manba FAQAT
   `cli.health_report()["status"]` va uning `problems`/`warnings` ro'yxatlari:
   - `ok` -> "✓ Tizim yaxshi holatda" + nima tekshirilgani;
   - `warn` -> "! Diqqat: N ta ogohlik bor" + ogohliklar oddiy tilda;
   - `fail` -> "✗ Muammo bor: N ta muammo topildi" + FAQAT muammolar
     (ogohliklar soni alohida qatorda — aks holda sarlavhadagi son ro'yxat
     bilan mos kelmasdi, bu skrinshotda ko'rildi va tuzatildi);
   - boshqa / o'qilmadi -> "? Tizim holatini o'qib bo'lmadi" + sabab.
   Stall talqini va boshqa GUI hisoblari bu jumlaga **ta'sir qilmaydi**
   (test: `test_holat_jumlasiga_STALL_TALQINI_TASIR_QILMAYDI`).
   Doctor (18 tekshiruv) bosh sahifada ATAYLAB chaqirilmaydi: u subprocess'lar
   ishlatadi va bitta vaqtinchalik cgroup yaratadi; u "Tizim holati"
   sahifasida qoladi.
2. **To'rt karta:** Protsessor (yadro soni + kutish talqini), Xotira (band /
   jami GiB + `<progress>` chiziq + "tajriba uchun yetadimi"), Disk, Tarmoq.
   Disk va Tarmoq uchun REVIX'da o'lchov manbasi YO'Q (`MISSING_SOURCES`) —
   kartada "—" va "REVIX disk hajmini / tarmoqni o'lchamaydi" deb yoziladi.
   Disk kartasida faqat mavjud PSI `io` kutish talqini bor.
3. **Xizmatlar mini-ro'yxati:** `revix*` unit'lar — belgi + oddiy so'z
   (● ishlayapti / ✗ xato bilan to'xtagan / ○ to'xtagan / ◐ ishga tushmoqda).
   Bo'sh ro'yxat: "Hozir hech qanday REVIX xizmati ishlamayapti … bu NORMAL".
4. **"REVIX nima?"** — ikki jumla (tadqiqot stendi; ekran faqat o'qiydi).
5. **"Nima qilsam bo'ladi?"** — Xizmatlar, Tizim holati, Yordam havolalari.

4 va 5 bitta keng kartada: ikki tor karta matnni 8+ qatorga sindirib, pastki
qatorni 800 px dan chiqarib yuborgan edi (1-iteratsiya skrinshoti).

## §2. Menyu: guruhlangan, hech narsa o'chirilmagan

Chap ustun (tor ekranda tepada):

- **Oddiy:** Bosh sahifa, Xizmatlar, Tizim holati, Resurslar, Yordam.
- **"Tadqiqotchi uchun"** (`<details>`, default yopiq, joriy sahifa shu
  guruhda bo'lsa ochiq): Texnik umumiy ko'rinish (eski "Boshqaruv paneli",
  endi `/overview`), Recovery hodisalari, Failure tahlili, Recovery
  siyosatlari, Xavfsizlik, Tadqiqot metrikalari, Log'lar, Sozlamalar,
  Loyiha haqida.

Barcha avvalgi 11 slug o'zgarmagan; jami 14 sahifa (`+help`, `+overview`).
Manbasi yo'q sahifa menyuda punktir chiziq va "hali bo'sh: tajriba natijasi
yo'q" yozuvi bilan belgilanadi (`class="empty-page"` saqlangan).

Har sahifa (bosh sahifadan tashqari) boshida "**Bu sahifa nima
ko'rsatadi:** … / **Kim uchun:** …" bloki va yig'iladigan "Texnik tafsilot"
(eski texnik intro matni) bor.

**Yordam** (`/help`): ekranni o'qish qadamlari, belgilar jadvali (✓ / ! / ✗ /
— / 0 / hali ishga tushirilmadi / taxminiy talqin), 23 atamali lug'at (PSI /
stall, some/full, cgroup, slice, recovery, failure, pressure, p99, SUT, guard,
systemd-oomd, disposition, censored, horizon, CI, arm, FR-A, MemAvailable,
swap, GiB, synthetic …), live image eslatmalari (`revix` foydalanuvchisi,
parolsiz avtomatik kirish, NOPASSWD sudo -> ishonchsiz tarmoqqa ulanmaydi,
Ctrl+Alt+F2 matnli konsol, GUI faqat ko'rish, **VM vaqtlari tadqiqot natijasi
sifatida yaroqsiz**, grafik rejim ~0.4 GiB oladi — 6 GiB tavsiya, jurnal 11
o'lchovi), talqin chegaralari va `reason=` kodlarining oddiy izohi.

## §3. Yorliqlar va "qiymat yo'q" ko'rinishi

**Yorliqlar:** xom maydon nomi asosiy yorliq emas. `kv()` endi
`(odam yorlig'i, qiymat, xom nom)` oladi: "Jami xotira" + kichik `MemTotal`,
"Kutish: kimdir kutdi" + `host cpu some` va h.k. Inglizcha sarlavhalar
(`SYSTEM HEALTH`, `MEMORY`, `CPU`, `SERVICES` …) o'zbekchaga o'girildi
(Tizim holati va resurslar, Xotira (RAM), Protsessor (CPU), REVIX xizmatlari).
Holat nishonlari: belgi + o'zbekcha so'z + kichik xom qiymat
(`✓ o'tdi PASS`, `✗ xato failed`). Doctor jadvali: oddiy savol
("Bo'sh xotira yetarlimi?") + kichik kalit (`memory_headroom`), FAIL/WARN
qatorlari yuqorida (faqat tartib, hech bir qator tushirilmaydi). Health
muammo/ogohlik matnlari prefiks bo'yicha oddiy jumlaga o'giriladi, xom matn
yonida qoladi; tanilmagan matn xom holda (o'ylab topilgan tarjima yo'q).

**Qiymat holatlari — semantika O'ZGARMADI, faqat balandligi:**

| Holat | Oldin (har joyda) | Endi: oddiy sahifa (`grp-main`) | Endi: tadqiqotchi sahifasi (`grp-research`) |
|---|---|---|---|
| `None` | shtrixli plita `o'lchanmadi n/m reason=…` | `—` + kichik `i`; `title` = "O'lchanmadi: <oddiy sabab> (reason=<kod>)" | oldingidek shtrix + matn (branding §4.2) |
| `0` | `0 [O'LCHANGAN NOL]` | oddiy `0`; `title` = "O'lchangan qiymat: aniq nol" | `0` + kichik "o'lchangan nol" |
| manba yo'q | to'lqinli `manba yo'q` | `—` + `i`; `title` = "REVIX bu qiymatni umuman o'lchamaydi" | to'lqinli `manba yo'q` |
| artifact yo'q | punktir `hali ishga tushirilmadi n/r` | o'sha (sokinroq shrift) | o'sha |

DOM da hamma narsa qoladi: `class="val v-missing|v-zero|v-nosource|v-norun"`,
`data-state`, yangi `data-reason`, `role="img"`, `aria-label`, matnli
tafsilot (`.detail` / `.zmark` — oddiy sahifada CSS bilan vizual yashirin,
ekran o'quvchida bor). Ko'rinadigan "—" raqam emas, demak "o'lchanmagan
qiymatda raqam yo'q" qoidasi piksel darajasida ham bajariladi.
Uzun izohlar (`honesty`) `<details>` ga yig'ildi (sarlavha ko'rinadi);
`critical` izohlar HECH QACHON yig'ilmaydi.

## §4. Hisob-kitob va TAXMINIY TALQIN (qoida 4 bilan munosabat)

GUI analiz qilmaydi (qoida 4). Ikkita ataylab, ekranda asosi yozilgan
istisno:

1. **RAM band = MemTotal − MemAvailable** (bitta manba, `/proc/meminfo`, ikki
   maydon). Kartada pastda "band = jami − bo'sh (MemTotal − MemAvailable)"
   yozilgan; `<progress max=MemTotal value=band>` XOM kB bilan. Ikkala maydon
   ham butun son va `0 <= avail <= total` bo'lmasa — "—", son yo'q.
   "Yetadimi?" hukmi O'ZIMIZ solishtirmaymiz: u `health_report()` ning
   `MemAvailable…` muammosi / `xotira zaxirasi yupqa` ogohligidan olinadi;
   ro'yxatlar yo'q bo'lsa hukm ham yo'q.
2. **PSI `some` kutish ulushi -> so'z** (faqat ekran uchun, har doim
   "(taxminiy talqin)" yorlig'i va xom son yonida):

   | `some` ulushi | so'z | ma'nosi |
   |---|---|---|
   | `< 0.05` | past | dasturlar navbatni deyarli kutmayapti |
   | `0.05 … < 0.25` | o'rta | ba'zan kutyapti |
   | `>= 0.25` | yuqori | ko'p vaqt kutyapti |
   | `None` | "—" | talqin YO'Q (hech qachon "past" emas) |

   Nega konservativ: bo'sh desktopda `some` odatda 0.01 dan past; oynaning
   5 % kutish allaqachon sezilarli, shuning uchun "o'rta" erta boshlanadi;
   chorak vaqt kutish — "yuqori". Shubhali holatda so'z yuqoriroq darajani
   beradi. Bu chegaralar `PREREGISTRATION.md` da YO'Q, hech qaysi qaror, guard,
   analiz yoki holat jumlasi ularni ishlatmaydi (konstantalar
   `STALL_LEVEL_MID`, `STALL_LEVEL_HIGH`; Yordam sahifasida ham jadval).

**CPU foizi ixtiro qilinmadi:** CPU kartasi yadro soni (`os.cpu_count()`)
va kutish talqinini beradi; "band foizi (CPU %) o'lchanmaydi" deb yoziladi
(test: `test_bosh_sahifa_CPU_foizini_IXTIRO_QILMAYDI`). Disk sig'imi
(`os.statvfs`) ham QO'SHILMADI — bu gateway semantikasini o'zgartirgan
bo'lardi (vazifa shartiga ko'ra taqiqlangan); qarorni keyinroq alohida
qilish mumkin (pastda, zaifliklar).

## §5. Vizual dizayn

- Body 16 px, h1 26 px, karta sarlavhasi 18 px, katta qiymat 26–30 px;
  branding tokenlari (`--rx-*`) O'ZGARMADI, ikkinchi `:root` da faqat o'lcham
  tokenlari (`--gui-*`) qo'shildi (`style.css` qoida 9).
- Ranglar faqat `:root` da; qizil/yashil faqat xato/yaxshi; "Diqqat" —
  neytral oq + punktir chegara + "!" (branding H-1: sariq yo'q). Har holatda
  belgi + so'z + shakl bor; rang yagona kanal emas.
- Tashqi font/CDN/JS kutubxonasi yo'q; inline `style=""` yo'q (CSP
  `style-src 'self'`; chiziq `<progress>` bilan) — test qulflaydi.
- Grid: 1280 da 4 ustun, 900–1180 da 2 ustun, < 900 da menyu tepaga
  o'tadi; jadvallar faqat ICHKI aylantiriladi, sahifa gorizontal
  aylanmaydi. Jadval kataklari `overflow-wrap: break-word` (anywhere emas —
  800 px skrinshotda "ishlaya pti" kabi so'z o'rtasidan bo'linish ko'rildi).

## §6. Avto-yangilanish va yig'ilgan holat

Avvalgi holat: `app.js` da avto-yangilanish **YO'Q** edi (qoida 2: sahifa
o'zini jimgina yangilamaydi) — bu SAQLANDI. Yangilash — F5 yoki yangi
"↻ Yangilash" tugmasi (to'liq qayta yuklash). Shuning uchun miltillash
muammosi yo'q. Qayta yuklashda `<details>` holati yo'qolmasligi uchun
`app.js` uni `localStorage` da `data-key` bo'yicha saqlaydi (try/catch;
ishlamasa server default holati; menyu guruhi uchun `data-force-open`
ustun). Skript hech qanday qiymat yozmaydi va serverga hech narsa
yubormaydi.

Topilgan va tuzatilgan xato: manba yoshi "?" ko'rinardi. Sabab:
`data-server-now-real-us` so'rov BOSHIDAGI vaqt edi, tirik o'qish esa
undan >= 2 s keyin (PSI oynasi), ya'ni yosh manfiy -> `fmtAge` "?".
Endi `layout()` sahifa chiqarilgan paytni (`max(ctx.now, cli.real_us())`)
beradi.

## §7. Testlar

`tests/unit/test_gui.py`: 74 -> 93 test (19 yangi). **Faqat ko'rinish
o'zgargan joylarda** o'zgartirildi:

- `_cell_for()` yordamchisi `<dt>` ichidagi `<span class="rawkey">` ni qabul
  qiladi va qatorni odam yorlig'i YOKI xom nom bilan topadi.
- Yorliq nomlari: `"eksperiment uchun kerak"` -> `"Tajriba uchun kerak"`,
  `"sig'im / band"` -> `"Sig'im / band joy"`, `"foydalanish %"` ->
  `"Band foizi (%)"`, `"interfeyslar"`/`"bayt / paket"` bosh harf bilan.
  Raqam yo'qligi tekshiruvlari O'ZGARMAGAN.
- Sahifalar soni 12 -> 14 (+ eski 11 slug saqlanganini tekshiradi).
- `test_bosh_manba_bilan_renderlangan_sahifa_SON_IXTIRO_QILMAYDI`: ildiz
  endi bosh sahifa — kartalar `data-field` bilan tekshiriladi, eski kv
  yorliqlari `/overview` da.
- `visible_text()` docstring'i aniqlashtirildi: bu "DOM matni" (vizual
  yashirin `.detail` ham kiradi); piksel ko'rinishi (faqat "—") alohida test
  bilan qulflandi.

To'rt holat, `n/m reason=` formati, `aria-label`, sintetik belgi, escape,
loopback, CSP, gradient/animatsiya taqiqi testlari O'ZGARMASDAN o'tadi.
Yangi testlar: tire + sabab `title`, har sabab kodining oddiy izohi, nol
ko'rinishi, holat jumlasi (4 holat), talqin jumlaga ta'sir qilmasligi,
health matn tarjimasi + escape, RAM band/jami/`<progress>`, hukm faqat
health'dan, talqin chegaralari va `None`, unit so'zlari, xizmat nomi
escape, `<details>` yig'ish qoidasi, Yordam lug'ati, inline style yo'qligi,
guruhlangan menyu, har sahifa intro + body guruh klassi, CPU % yo'qligi.

**To'liq to'plam (ext4 nusxa `~/gui-clarity-work`, WSL kali):**
`1175 passed, 1 skipped` (main'da 1156 passed, 1 skipped; +19 yangi).

## §8. Vizual tekshiruv (headless Edge, ko'z bilan o'qildi)

Server WSL'da `127.0.0.1:8797` (loopback, `--allow-remote` siz), Windows'dan
localhost forward orqali; sintetik holatlar `--mark-synthetic` bilan statik
render qilindi (har birida qizil "SINTETIK MA'LUMOT" banneri bor). Doctor
chaqiradigan sahifalar (Tizim holati, Xavfsizlik) tirik serverda OCHILMADI —
faqat fixture bilan (vaqtinchalik cgroup yaratmaslik uchun).

Iteratsiyalar (har birida skrinshot o'qildi):
1. v1: bosh sahifa — pastki qator 800 px dan chiqdi; RAM "573.6 MiB / 9.7
   GiB" ikki qatorga sindi; yosh "?" -> uchala muammo tuzatildi.
2. v2: FAIL holatida sarlavha "2 ta muammo", ro'yxatda 3 qator (ogohlik
   aralashgan); Tizim holati sahifasida hero ro'yxati pastdagi ro'yxatni
   takrorladi -> tuzatildi.
3. v3/v4: Xizmatlar bo'sh matnida backtick ko'rindi; hujjat manbasi
   "o'qilmadi" deb ko'rindi; menyudagi "hali bo'sh" yorlig'i sinib turdi ->
   tuzatildi.
4. v5: 800 px da jadval kataklari so'z o'rtasidan bo'lindi -> `break-word`;
   oddiy sahifada qiymatlar sans shriftga o'tdi.

Yakuniy skrinshotlar (`docs/architecture/img/`, har biri < 100 KB):
`19-gui-1-home-1280x800.png`, `19-gui-2-home-800x900.png`,
`19-gui-3-fail-home-SYNTHETIC-1280x800.png`,
`19-gui-4-warn-home-SYNTHETIC-1280x800.png`,
`19-gui-5-fail-services-SYNTHETIC-800x900.png`,
`19-gui-6-services-1280x800.png`, `19-gui-7-help-1280x800.png`,
`19-gui-8-resources-1280x800.png`,
`19-gui-9-research-recovery-events-1280x800.png`,
`19-gui-10-fail-system-health-SYNTHETIC-1280x800.png`.

## §9. Skeptik oddiy foydalanuvchi ko'zi bilan

**(a) Birinchi 10 soniyada nima ko'rinadi (1280x800, WSL, tirik):** chapda
REVIX va 5 ta tushunarli menyu bandi; tepada katta yashil ✓ "Tizim yaxshi
holatda" va bir jumla nima tekshirilgani; ostida to'rt karta: "12 yadro,
Kutish: past", "578.8 MiB / 9.7 GiB" chiziq bilan va "✓ yetadi", Disk va
Tarmoq "—" va "REVIX … o'lchamaydi"; pastda "Hozir hech qanday REVIX xizmati
ishlamayapti … NORMAL", "REVIX nima?" ikki jumla va uchta "nima qilsam
bo'ladi" havolasi. Aylantirish shart emas. FAIL holatida qizil ✗ "Muammo
bor: 2 ta muammo topildi" va oddiy tildagi sabablar (xom matn kichik).

**(b) Qolgan zaifliklar (halol):**
- Disk va Tarmoq kartalari asosan bo'sh ("—"). Bu halol, lekin oddiy
  foydalanuvchi "nega disk ko'rsatilmaydi?" deb so'rashi mumkin. Disk
  sig'imini `os.statvfs` bilan o'qish — alohida qaror (gateway semantikasi
  va `MISSING_SOURCES` matni o'zgaradi), bu ishda qilinmadi.
- "Tizim yaxshi holatda" — bu `revix health` ning TAJRIBAGA tayyorlik
  hukmi (xotira zaxirasi, qoldiq, oomd, bosim), umumiy kompyuter sog'lig'i
  emas. Jumla ostida nima tekshirilgani yozilgan, lekin noto'g'ri
  umumlashtirish xavfi qoladi.
- "—" ning sababi faqat sichqoncha `title` da; kiosk'da sichqoncha
  harakati VM'da sinalmagan (jurnal 11), klaviatura bilan `title` ochilmaydi.
  Sabablar Yordam sahifasida ro'yxat sifatida bor.
- Tadqiqotchi sahifalari hali ham zich (texnik matn, uzun yo'llar, bo'sh
  holat izohlari); ular faqat intro, sarlavha va yig'ilgan izohlar bilan
  yengillashtirildi.
- Talqin chegaralari (0.05 / 0.25) empirik kalibrlanmagan — faqat ekran
  so'zi; "taxminiy talqin" yorlig'i bilan.
- Ba'zi texnik so'zlar (PSI, slice, systemd) oddiy sahifalarda qoldi —
  lug'atga havola bilan; to'liq yo'qotib bo'lmaydi.
- Avto-yangilanish yo'q (ataylab, qoida 2): ochiq qoldirilgan sahifa 30 s
  dan keyin qizil "eskirgan" bo'ladi, lekin o'zi yangilanmaydi.

**Tekshirilmagan:** VM ichidagi kiosk Firefox'da yangi dizayn ko'rilmadi
(VM ishga tushirish va ISO qurish bu vazifada taqiqlangan) — skrinshotlar
Windows headless Edge'dan. Firefox ESR'da `<progress>` va `details`
uslublari kutilganidek ishlashi taxmin qilinadi (`::-moz-progress-bar`
yozilgan), lekin ko'z bilan tekshirilmagan. Tirik `/system-health` va
`/security` sahifalari (doctor) faqat sintetik fixture bilan ko'rildi.
