# REVIX — Pre-registration: PSI Pilot (P1)

| | |
|---|---|
| **Versiya** | `preregistration/v1.14` |
| **Holat** | MUZLATILGAN — kod yozishdan oldin commit qilindi |
| **Qamrov** | Faqat **pilot eksperiment P1**. Confirmatory eksperiment alohida pre-registration talab qiladi. |
| **Muzlatilgan sana** | 2026-09-29 (v1, v1.1, v1.2, v1.3) · 2026-10-02 (v1.4, v1.5, v1.6) · 2026-10-03 (v1.7, v1.8, v1.9, v1.10, v1.11) · 2026-10-04 (v1.12, v1.13, v1.14) |
| **Muhit** | Bu pre-registration **§15.1 va §16.11 da qayd etilgan o'lchangan fingerprint** uchun qo'llanadi. |
| **✅ Qaror 1 — QABUL QILINDI (v1.11)** | **§17.5 — dizayn nuqsoni** (stabilizatsiya oynasi pressure hold'ga sig'maydi) → **O3**: `hold_cap_s` **12 s → 13 s**. Orkestrator, egasining 2026-10-03 dagi ochiq delegatsiyasi bo'yicha. Asos, narx va cheklovlar: **Amendment log, v1.10 → v1.11** va §17.5. |
| **✅ Qaror 2 — QABUL QILINDI (v1.11)** | **§18.6 — §11 ning fail-slow limbi ishlamaydi** → **F2**: `thr = 0.20 × τ = 1.6 s`, **fiksa**. Orkestrator, o'sha delegatsiya bo'yicha. §18.2 ning `thr = 0.20 × RMST(P0)` o'qishi **bekor qilinadi**. Asos, **bias yo'nalishi** va narx: **Amendment log, v1.10 → v1.11**, §18.6, §18.7. |
| | Ikkala qaror **birinchi pilot trial'idan OLDIN** va **birgalikda** qabul qilindi (tuguni `τ = W_stab_pilot = 8 s`; §18.6, §19.3). **Juftlik izchil:** O3 `W_stab_pilot` ni ham, `τ` ni ham **tegmasdan qoldiradi**, demak §18.6 ning O1 haqidagi ogohligi **yuzaga kelmaydi**. |
| **🔴 Oshkora e'lon (v1.11)** | **Ikkala tanlov ham KALIBRATSIYA MA'LUMOTI KO'RILGANDAN KEYIN qabul qilindi.** P1 trial'i o'tkazilmagan, lekin `10-pressure-dozalash.md` ning o'lchovlari tanlov paytida **qo'lda edi**, va F2 holatida nomzod chegaralar **o'lchangan `P2 − P0` farqiga nisbatan** taqqoslandi. §17.6 va §18.7 ning *“ma'lumot mavjud emas”* kafolati **v1.11 ga O'TMAYDI** — Amendment log, v1.10 → v1.11, **0-band**. |
| **✅ Ochiq parametrlar — MUZLATILDI (v1.12)** | **§16.10:** `WatchdogSec = 5 s`, `MemoryHigh = 192M` (`MemoryMax=2G` bilan), `T_trial = 41.1 s` — oldindan yozilgan qoida / formula bo'yicha; **`TimeoutStartSec = 10 s` — ⚠️ OSHKORA OG'ISH:** o'z kalibratsiya qoidasi namuna yetmagani uchun (24/24/20 < 48) **taklif BERMAGAN**, qiymat ma'lumotdan oldingi default sifatida saqlandi. Kalibratsiya run'lari: `open-params-cal-01`, `-02`, `-03`. Orkestrator, egasining 2026-10-03 delegatsiyasi bo'yicha. **Amendment log, v1.11 → v1.12, 1-band.** |
| **✅ Generator vaqti — V2 (v1.12)** | Generator `t_h − R` da boshlanadi (`R = 2.57 s` — o'z o'lchangan ramp'i), `hold_s + R` ishlaydi, `pressure_off` (33.0 s) da chiqadi. **§9.4 ning hech bir muzlatilgan vaqti siljimadi** — *"ramp 5 s"* ning implementatsion aniqlashtirilishi. Sabab: avvalgi 18 s li generator bilan sustain taymeri hold'dan **1.4 s oldin** boshlanib `P2` 2/2 `aborted_guard` bo'lgan — **v1.11 (1.5) ning premisasi yolg'on chiqdi**. **2-band.** |
| **⚠️ `P2` da kutilgan yo'qotish (v1.12)** | Guard'ning **runaway** qoidasi (`0.98`) bo'yicha ba'zi `P2` trial'lari `aborted_guard` bo'ladi (1/6 … 2/7 tartibida — **o'lchangan stavka EMAS**). Ular §12 bo'yicha chiqariladi; **`(arm × pressure)` yacheyka jadvali MAJBURIY**; bias yo'nalishi (shartli: **H1 ga qarshi**) va arm'lararo **confound** xavfi oldindan e'lon qilindi. **3-band.** |
| **🔴 Oshkora e'lon (v1.12)** | **v1.12 ning qarorlari kalibratsiya VA smoke ma'lumoti ko'rilgandan KEYIN qabul qilindi.** `TimeoutStartSec` og'ishi, V2 va `P2` yo'qotishi kutilmasi uchun *"ko'r tanlangan"* kafolati **yo'q**; qoidaga tayangan qiymatlar uchun qamrovi 0-band jadvalida. **Amendment log, v1.11 → v1.12, 0-band.** |
| **✅ Gate — YOPILDI (v1.12), shart bilan** | **§21.7:** generator §9.4 ning ikki invariantini **o'lchov bo'yicha** majburlaydi — **faqat V2 generator vaqti bilan ishlaydigan driver uchun** (chiqish 33.075–33.245 s vs 33.0 s; eng uzun guard oralig'i ≤ 13.0 s; sustain trip 0/6; n = 6). `main` ning hozirgi (V0) driver'i bilan trial — **protokol buzilishi**. Orkestrator qarori. **5-band.** |
| **⛔ Pilot preshartlari (v1.12)** | Birinchi pilot trial'i o'tkazilmaydi, toki `main` da: **(1)** driver istisno yo'li nuqsonining tuzatishi (guard abort'i `harness_error` bo'lib, washout o'tkazib yuborilardi); **(2)** V2 kodi; **(3)** muzlatilgan qiymatlarni `run_id` bilan olib yuradigan `run_meta.open_parameters`; **(4)** V2 ning `P1`/`P0` regressiya smoke'i merge qilingan kod bilan; **(5)** v1.12 merge qilingan va tag qilingan. **9-band.** |
| **🔴 Pilot `p1-pilot-001` — YAROQSIZ (v1.13)** | 120/120 trial (v1.12, `main` `4cbd1c6`, seed 20261006), lekin `revix.validate` **4 xato, 3 trial** (hammasi `A/P2`) ⇒ §14.6 bo'yicha **analiz qilinmaydi**. Sabab — uchta **driver** nuqsoni (§17.4 oyna fakti yo'q; `probe_gap_exceeded` §4 ta'rifidan emas; eskirgan `ActiveExitTimestamp`), validator va muzlatilgan ta'rif emas (`15`). Run saqlanadi, **o'chirilmaydi**, hech qachon birlashtirilmaydi. **Amendment log, v1.12 → v1.13, 1- va 2-band.** |
| **✅ Qaror — V-A (v1.13)** | Driver uch nuqsonni tuzatadi (§4, §17.4(2), (5) ni **implementatsiya qiladi**; hech bir ta'rif yoki qiymat o'zgarmaydi), unit test + `p1-pilot-001` ustida oflayn replay + smoke bilan tekshiriladi; butun pilot **`p1-pilot-002`** sifatida **bir xil seed (20261006) va jadval digest'i (`69ae399e…cb2dc`)** bilan qayta o'tkaziladi. **`p1-pilot-002` — analiz qilinishi mumkin bo'lgan YAGONA pilot run'i.** Orkestrator, egasining 2026-10-03 delegatsiyasi bo'yicha. **3-band.** |
| **🔴 Oshkora e'lon (v1.13)** | **Qayta o'tkazish qarori `p1-pilot-001` ning DISPOSITION HISOBLARI KO'RILGANDAN KEYIN qabul qilindi** (orkestrator — yacheyka bo'yicha; tahlil agenti — run jami). *"Ko'r tanlangan"* kafolati **yo'q**; bias faqat **almashtirish** yo'nalishida — run'lar orasida **tanlov yo'q**; `p1-pilot-002` ham yiqilsa uchinchi run **yangi amendment'siz** o'tkazilmaydi. **0-band.** |
| **⛔ `p1-pilot-002` preshartlari (v1.13)** | **(1)** uch tuzatish `main` da; **(2)** replay faqat `b007t001`, `b013t004` (→ `censored`) va `b010t001` (action vaqtlari) ni o'zgartiradi, boshqa trial yo'q; **(3)** smoke oldindan commit qilingan mezondan o'tdi; **(4)** `git_commit` tuzatishlarni o'z ichiga oladi; **(5)** dry-run digest'i bir xil; **(6)** v1.13 merge va tag; **(7)** VirtualBox VM o'chirilgan, host uyg'oq; **(8)** `04` ning revizya yozuvi. **8-band.** |
| **🔴 Pilot `p1-pilot-002` — v1.13 darvozasi ostida O'TMADI (v1.14)** | 120/120 trial (v1.13, `main` `8deaaf0`), post-flight toza, `p1-pilot-001` ning uch xato klassi **takrorlanmadi**; lekin `revix.validate` **O'TMADI — 1 xato, 23 ogohlantirish**: `b010t005` (`no_action/P2`, `aborted_guard`) da probe uzilishi **678 119 µs**. Bu asl hukm **yozuvda qoladi**. Sabab — validator'ning `probe_gap` va `probe_coverage_gap` tekshiruvlari muzlatilgan ustuvorlik tartibiga **ko'r** (`17`). **Amendment log, v1.13 → v1.14, 1- va 2-band.** |
| **✅ Qaror — (a), SIMMETRIK; uchinchi run YO'Q (v1.14)** | Validator tuzatiladi: `probe_gap` / `probe_coverage_gap` — XATO **faqat `complete`** da, qolgan har disposition'da ogohlantirish; teskari tomonda `guard_event_not_reflected` — `aborted_guard` (yoki undan oldin turuvchi `harness_error`) dan boshqa **har** disposition'ni belgilaydi. Mavjud `p1-pilot-002` xom ma'lumoti qayta validatsiya qilinadi; **yangi run yo'q**. Hech bir metrika, disposition qiymati yoki muzlatilgan ta'rif o'zgarmaydi. `p1-pilot-002` — *"v1.14 ning tuzatilgan darvozasi ostida yaroqli"* (hech qachon *"yaroqli edi"* emas) va **yagona** analiz qilinishi mumkin bo'lgan pilot run'i; `p1-pilot-001` yaroqsiz qoladi. Orkestrator, egasining 2026-10-03 delegatsiyasi bo'yicha. **2-, 3-, 4-band.** |
| **🔴 Oshkora e'lon (v1.14)** | **Darvoza IKKINCHI muvaffaqiyatsizlikdan KEYIN va uning ta'siri (O'TMADI → O'TADI) OLDINDAN MA'LUM bo'lgan holda o'zgartirildi.** v1.13 (0.6) bu holatning oqibatini boshqacha yozgan edi; §14.6(4) so'zma-so'z o'qilsa eski xatti-harakatni qo'llaydi. *"Ko'r tanlangan"* kafolati **yo'q**. **0-band.** |
| **⚠️ Probe uzilishi tarqalishi (v1.14) — ALOHIDA yaroqlilik topilmasi** | `p1-pilot-002` da **24/120** trial'da (68 uzilish) probe uzilishi > 2P — bu tuzatishning qismi **emas**. fsync GIPOTEZA'si **o'lchanmagan**, sabab da'vo qilinmaydi; **birorta confirmatory run'dan OLDIN** o'lchanishi va instrument qarori qabul qilinishi SHART. **5-band.** |
| **⛔ `p1-pilot-002` ni analiz qilish preshartlari (v1.14)** | **(1)** validator tuzatishi testlari va oldin/keyin isboti bilan `main` da; **(2)** v1.14 merge va tag; **(3)** tuzatilgan validator arxivlangan `p1-pilot-002` ustida ishlatilgan va hukmi asl hukm **yonida** yozilgan. **10-band.** |

Bu fayl `run_meta.preregistration_sha256` orqali har bir eksperiment run'iga bog'lanadi.
Fayl o'zgarsa — hash o'zgaradi, ya'ni qaysi ta'riflar ostida o'lchangani har doim aniqlanadi.

---

## Amendment log

Pre-registration **jimgina tahrirlanmaydi.** Har bir o'zgarish shu yerda
qayd etiladi, versiya oshiriladi, va oldingi versiyaning hash'i saqlanadi.
Shunda qaysi ta'riflar ostida o'lchangani har doim tekshirilishi mumkin.

### v1.13 → v1.14 (2026-10-04)

| | |
|---|---|
| **v1.13 sha256** | `f0c45722b231687c5e73a4a41e52517a6bd0ae96669c1d244211d18d8ac7b117` |
| **v1.13 git tag** | `v0.1.13-preregistration` |
| **Sabab** | Ikkinchi pilot run'i **`p1-pilot-002`** 120/120 trial'ni toza post-flight bilan tugatdi va `p1-pilot-001` ning uch xato klassi takrorlanmadi, lekin `revix.validate` **O'TMADI — 1 xato, 23 ogohlantirish**. Yagona xato — `aborted_guard` trial'idagi probe uzilishi, va uni validator'ning **muzlatilgan ustuvorlik tartibiga ko'r** ikki tekshiruvidan biri beradi (`docs/architecture/17-pilot-002-validatsiya-xatosi.md`, quyida `17`). v1.13 (0.6) bo'yicha `p1-pilot-002` **hozir yaroqsiz**, va har qanday keyingi qadam **yangi amendment** talab qiladi (`17` §6.1). Qaror run va uning hisoblari **ko'rilgandan keyin** qabul qilindi — shuning uchun u shu yerda, oshkora e'lon bilan, `p1-pilot-002` ning **birorta natijasi hisoblanishidan OLDIN** yoziladi |
| **Qarorni kim qabul qildi** | **Orkestrator**, loyiha egasining **2026-10-03 dagi ochiq delegatsiyasi** bo'yicha (v1.11–v1.13 dagi o'sha delegatsiya). Asos fayl: `17` (§0–§8; §10). Matnni `agent/amend-v114` agenti yozdi. **`17` hali `main` da emas:** u `agent/pilot-ready` branch'ida. Matn yozilayotgan paytda o'qilgan holati: avval commit **`2849896`** (§0–§9); commit qilishdan oldin qayta tekshirilganda o'sha branch'da **`c3ad687`** paydo bo'lgan — u `17` ga **§10** ni qo'shadi (tuzatish spetsifikatsiyasi, isbot usuli, **kutilgan natija** va to'xtash qoidasi — kod o'zgarishidan **oldin** commit qilingan); u ham o'qildi va shu amendment bilan **mos**. Validator tuzatishining **kodi va isboti** o'sha paytda **commit qilinmagan edi** (worktree'da commit qilinmagan o'zgarishlar bor edi — bu amendment ularni **o'qimagan** va ularga tayanmaydi). **Har bir raqam `17` ga va u keltirgan fayllarga** (`PREREGISTRATION.md` v1.13; `main` `8deaaf0` dagi `revix/validate.py`, `revix/schedule.py`, `revix/reduce.py`, `revix/schema.py`, `revix/prober.py`; `04` §8.1; `15`) **qarshi tekshirildi**; guest'ga kirilmadi — fayl bilan tekshirib bo'lmagan bayonotlar 1-bandda belgilangan |
| **O'zgardi** | **Hech bir ta'rif emas — validator'ning yaroqlilik qoidasi.** **(1)** `p1-pilot-002` ning asl hukmi (**O'TMADI**, 1 xato) qayd etildi va **yozuvda qoladi** (1-band). **(2)** Qaror **(a)** (`17` §6.2), **simmetrik**: `probe_gap` va `probe_coverage_gap` XATOsi faqat `complete` ga; `guard_event_not_reflected` `aborted_guard` / `harness_error` dan boshqa **har** disposition'ga (2-band). **(3)** Mavjud `p1-pilot-002` xom ma'lumoti tuzatilgan validator bilan **qayta validatsiya** qilinadi; kutilgan ta'sir **oldindan** yozildi (3-band). **(4)** **Uchinchi run rad etildi** (4-band). **(5)** `p1-pilot-002` — analiz qilinishi mumkin bo'lgan **YAGONA** pilot run'i, *"v1.14 ning tuzatilgan darvozasi ostida yaroqli"* sifatida (0.5). **(6)** Probe uzilishi tarqalishi — tuzatishdan **alohida** yaroqlilik topilmasi (5-band). **(7)** §14.6(4) ga belgilangan `v1.14` ko'rsatkichi (7-band). **(8)** `p1-pilot-002` ni analiz qilish preshartlari (10-band) |
| **O'zgarMADI** | **hech bir metrika, statistik test, arm, fault klassi, probe parametri, VR/FR ta'rifi, `disposition` enum'i va uning ustuvorlik tartibi, falsifikatsiya mezoni**, `W_stab_pilot`, `τ`, `hold_cap_s`, `injection_offset`, `θ`, `k_f`, `P`, `T_conn`, `T_rt`, blok va trial soni, **seed**, **jadval digest'i**, **guard chegaralari**, **dial**, v1.12 ning **muzlatilgan ochiq parametrlari**, **V2 generator vaqti** va **v1.13 ning driver tuzatishlari**. To'liq ro'yxat — 6-bandda |
| **Yig'ilgan ma'lumot** | **Ikki pilot run'i mavjud.** `p1-pilot-001` — **yaroqsiz** (v1.13), o'zgarishsiz. `p1-pilot-002` — v1.13 darvozasi ostida **O'TMAGAN**; tuzatilgan darvoza ostida yaroqli bo'lishi **kutiladi** (3-band), haqiqiy hukm 10-band (3) da yoziladi; **analiz qilinmagan**. VR, FR, downtime, `t_up` taqsimoti, p-qiymat yoki effekt bahosi **hisoblanmagan**. **LEKIN** disposition hisoblari va 24 uzilishli trial'ning yacheykasi **ko'rilgan** — 0-band. Smoke va kalibratsiya ma'lumoti — pilot to'plamidan **chiqarilgan**. To'liq holat — 8-band |

**0. 🔴 OSHKORA E'LON — validatsiya darvozasi IKKINCHI muvaffaqiyatsizlikdan KEYIN, va uning ta'siri O'TMADI → O'TADI ekani MA'LUM bo'lgan holda o'zgartirildi.**

Bu jumla `17` §6.4(1) talab qilgan shaklda yoziladi: **darvoza ikkinchi
muvaffaqiyatsizlikdan keyin o'zgartirilmoqda — `p1-pilot-002` ning
O'ZI uchun.** Tuzatishning shu run'ga ta'siri qarordan oldin **to'liq
ma'lum edi**: `17` §4 da tuzatilgan og'irlik `p1-pilot-002` ga **xotirada**
qo'llangan va natija **0 xato, 24 ogohlantirish** chiqqan. Bias xavfi
shakl jihatidan **maksimal** (`17` §6.2(a)).

**(0.1) Kim nimani ko'rdi** (`17` §0):

| kim | nimani ko'rdi | nimani ko'rmadi |
|---|---|---|
| **orkestrator** | **ikkala** pilotning **har `(arm × pressure)` yacheykasi bo'yicha disposition sonlari** (o'zi chop etgan; `17` §0 — uning o'z bayonoti). Demak bu qaror **ikkala** run'ning yacheyka hisoblari ma'lum bo'lgandan **keyin** qabul qilindi | hech bir fayl orkestratorning bundan boshqa ko'rgan yoki ko'rmagan narsasini qayd etmaydi; bu amendment buni **da'vo qilmaydi** va **tasdiqlay olmaydi** |
| **tahlil agenti** (`17`) | `p1-pilot-002`: `validate.txt` to'liq, `launcher.log`, boshlang'ich/yakuniy marker'lar, `clock-watch` xulosasi, `run_meta` ning kalit maydonlari; `driver.json` dagi **run bo'yicha jami**: `aborted_guard` **9**, `censored` **70**, `complete` **41** (yacheyka bo'yicha **emas**); **faqat 24 uzilishli trial** uchun `trial_id`, blok, yacheyka, disposition, `reason`, `matched_rules`, uzilish vaqtlari va `probe_overrun` soni; `b010t005` ning probe'dan boshqa record'lari; ikkala run'da `guard_event` × disposition kesishmasi; `p1-pilot-001` — validator natijasi (xotirada qayta ishlatilgan) va uning ikki uzilishli trial'i (`15` dan ma'lum) | qolgan **96 trial** uchun yacheyka bo'yicha hisob; 120 trial bo'yicha yacheyka × disposition jadvali; `t_up`, downtime, VR, FR, recovery, p-qiymat, effekt — **hech biri hisoblanmagan**; uzilishsiz `censored` trial'larning sababi; `pressure.jsonl`, `psi.csv`; guest disk IO, `dmesg`, host holati vaqt bo'yicha; `fsync` davomiyligi |
| **shu amendment muallifi** | `17` ning matni (`2849896`, keyin `c3ad687` dagi §10; yuqoridagi sonlar faqat shu orqali); `15`; `04` §8.1; `8deaaf0` dagi `validate.py`, `schedule.py`, `reduce.py`, `schema.py`, `prober.py` kodi | run kataloglari, `validate.txt`, `driver.json`, `gate.json` va `p12_gate.py` chiqishi; tuzatilgan validator kodi va uning chiqishi (matn yozilayotganda commit qilinmagan edi) |

`17` ning tahlil agenti `p1-pilot-001` ning `aborted_guard` sonini
`p1-pilot-002` niki bilan **solishtirmagan** (v1.13 0.5); bu amendment
ham solishtirmaydi.

**(0.2) Qaysi oldindan yozilgan qoida chetlab o'tiladi.**

1. **v1.13 (0.6)** bu holatni **oldindan** belgilagan: *"Agar
   `p1-pilot-002` ham validatsiyadan o'tmasa. U §14.6 bo'yicha **analiz
   qilinmaydi**; xuddi `p1-pilot-001` kabi **saqlanadi, yaroqsiz deb
   belgilanadi**"*, va keyingi qadam sifatida faqat **uchinchi run**ni
   (yangi amendment bilan) ko'zda tutgan. v1.14 shu oldindan yozilgan
   oqibatni run ko'rilgandan **keyin** o'zgartiradi.
2. **v1.13 V-B ning rad etilish asosi** — *"Darvoza ma'lumotdan keyin
   yumshatiladi"*. (a) **protsedura jihatidan aynan shu shakldagi** qaror
   (`17` §6.2(a), §7). Farqi (TALQIN, `17` §6.2): V-B xom ma'lumotni
   qayta tasniflab disposition'larni o'zgartirardi; (a) **birorta
   disposition'ni o'zgartirmaydi**, bitta trial topilmasining
   **og'irligini** o'zgartiradi, va trial chiqarilgan holda qoladi. Bu
   farq protseduraviy e'tirozni **yo'qotmaydi**.
3. **§16.10(3) ning ruhi** — natijaga qarab o'zgartirmaslik — v1.13 (0.2)
   dagi kabi **o'xshatish bo'yicha** qo'llanadi.

**Shuning uchun "ko'r tanlangan" degan kafolat bu qarorga BERILMAYDI.**

**(0.3) Tuzatishni nima HIMOYALANADIGAN qiladi — qulay emas, balki
asosli.**

1. **U allaqachon muzlatilgan ustuvorlik tartibiga ergashadi.** §4:
   invalidator'larning yopiq enum'ida `guard_fired` bor, va *"Probe
   uzilishi > 2×P → trial `censored`"* qoidasi **ulardan keyin** keladi.
   §12: `aborted_guard` = *"host guard ishga tushdi"*, *"aynan bitta"*
   disposition, va `aborted_guard` / `contaminated` *"birlamchi
   analizdan chiqariladi"*. v1.12 log 3.3(3) (va §12 ostidagi v1.12
   izohi): `aborted_guard` birlamchi to'plamga kirmaydi (§16.2(B)). v1.12 log 9.5-band
   istisno yo'li nuqsonini aynan *"§12 ning ustuvorligi
   (`aborted_guard`) o'rniga `harness_error`"* deb ta'riflagan. Kodda
   tartib oshkora: `schedule.DISPOSITION_RULES` — `harness_error` →
   `guard_fired` → uch `contaminated` fakti → `washout_timed_out` →
   **`probe_gap_exceeded`** → `window_outside_hold` →
   `horizon_ended_down` → `measured`; `reduce.derive_disposition` —
   `aborted_guard` → xom `contaminated` / `washout_timeout` /
   `harness_error` → **`probe_gap`** → …; `04` §8.1 driver'ni avtoritet
   qiladi. Har ikki tartibda `aborted_guard`, `contaminated`,
   `washout_timeout`, `harness_error` probe-uzilish qoidasidan **oldin**
   turadi; undan **keyin** turuvchi yagona disposition — `complete`.
   **CHEKLOV (`17` §2.5, §8):** tartib `PREREGISTRATION.md` da
   **tartiblangan ro'yxat sifatida yozilmagan** — u `schedule.py` va `04`
   §8.1 da; muzlatilgan matnda uning **oqibati** va v1.12 9.5-band mezoni
   bor.
2. **Simmetrik qo'llanadi** (2-band): xato yaratadigan tekshiruv
   yumshatiladi, lekin teskari yo'nalishda **yumshoq** bo'lgan
   `guard_event_not_reflected` **qat'iylashtiriladi** — tuzatish bir
   tomonlama emas.
3. **`p1-pilot-001` ning har xatosi joyida qoladi** (`17` §4):
   `b007t001` (`complete` + uzilish, `complete` + oyna), `b013t004`
   (`complete` + oyna), `b010t001` (`action_without_invocation_change` —
   §14.6(6), disposition'dan mustaqil). Tuzatish uni **qutqarmaydi**.
4. **`b010t005` ikki mustaqil asos bilan chiqarilgan:** `guard_fired`
   (`aborted_guard`) **va** `bystander_lost_contract` (`contaminated`);
   ikkalasi ham `matched_rules` da `probe_gap_exceeded` dan **oldin**
   turadi (`17` §2.3). Uzilish **jimgina emas** — `matched_rules` da
   yozilgan.
5. So'zma-so'z o'qishda guard + uzilish trial'i uchun **muvofiq
   disposition yo'q** (`17` §2.4): `aborted_guard` §14.6(4) ni buzadi;
   `censored` §12 ning ta'rifini buzadi va §6.2 bo'yicha guard o'ldirgan
   trial'ni KM ga **kiritadi** — §12 ning *"birlamchi analizdan
   chiqariladi"* jumlasiga teskari. Ya'ni muzlatilgan matnning o'zi bu
   holatda **ziddiyatda**, va qaysi o'qish tanlansa ham u talqin.

**(0.4) Skeptik nimani ishlatishi mumkin — va to'g'ri ishlatadi.**

1. **Ta'sir oldindan ma'lum edi** (yuqorida; `17` §4).
2. **§14.6(4) so'zma-so'z eski xatti-harakatni qo'llaydi:** *"trial ichida
   probe uzilishi > 2×P yo'q (aks holda trial `censored`)"*. Validator
   aynan shuni bajardi (`17` §2.5: *"validator §14.6(4) ni so'zma-so'z
   amalga oshiradi"*). Tuzatish — §14.6(4) ning **ma'lumotdan keyingi
   talqini**.
3. **Qaror ma'lumotdan keyin**, orkestrator **ikkala** run'ning yacheyka
   hisoblarini ko'rgandan keyin qabul qilindi.
4. **`17` ning o'z TALQINI** (§7): validator tuzatilib **uchinchi run**
   o'tkazilsa, darvoza o'zgarishi u baholaydigan ma'lumotdan **oldin**
   bo'ladi — *"bu (a) dan tozaroq, narxi bir run"*. Orkestrator (a) ni
   tanladi; nega — 4-band. Bu e'tiroz 4-band bilan **yo'qolmaydi**.
5. v1.13 bu holatning oqibatini **boshqacha** yozgan edi (0.2(1)).

**(0.5) "Yagona run" qoidasi — o'zgarmaydi, faqat qayta tasdiqlanadi.**

- **`p1-pilot-002` — analiz qilinishi mumkin bo'lgan YAGONA pilot
  run'i** (v1.13 0.5). U **"v1.14 ning tuzatilgan darvozasi ostida
  yaroqli"** deb tasvirlanadi — **hech qachon** *"yaroqli edi"* yoki
  *"validatsiyadan o'tdi"* deb emas. Asl hukm (1-band) har hisobotda
  **iqtibos qilinadi**.
- **`p1-pilot-001` yaroqsiz qoladi:** analiz qilinmaydi,
  birlashtirilmaydi, sezgirlik/takrorlash sifatida ishlatilmaydi, tanlab
  iqtibos keltirilmaydi, disposition sonlari solishtirilmaydi (v1.13 0.5
  so'zma-so'z o'z kuchida).
- Run'lar orasida **tanlov yo'q**: v1.14 yangi run qo'shmaydi.

**(0.6) Pilot ma'lumoti EKSPLORATIV.** Muzlatilgan dizayn P1 ma'lumotini
confirmatory analizga **kiritmaydi** (sarlavha jadvali: *"Confirmatory
eksperiment alohida pre-registration talab qiladi"*). Bu qaror noto'g'ri
bo'lsa yetkazadigan zararni **chegaralaydi**. Bu fakt qarorni
**oqlamaydi** va yuqoridagi e'lonni **yumshatmaydi** — u faqat qayd
etiladi.

**(0.7) Agar tuzatilgan validator kutilgandan boshqa natija bersa** (3-band):
`p1-pilot-002` **analiz qilinmaydi**, farq **to'xtash va xabar** sifatida
yoziladi; tuzatishni natijaga **moslashtirish taqiqlanadi**; har qanday
keyingi qadam **yangi amendment** (v1.15 yoki keyingi) talab qiladi.

> **Maqolada shunday yoziladi:** *"Ikkinchi pilot run'i 120/120 trial'ni
> tugatdi va oldindan belgilangan yaroqlilik darvozasidan (validator)
> bitta xato bilan O'TMADI: guard tomonidan to'xtatilgan va shu sababli
> analizdan chiqarilgan trial'dagi probe uzilishi. Ikkinchi
> muvaffaqiyatsizlikdan keyin va ta'siri ma'lum bo'lgan holda validator
> muzlatilgan disposition ustuvorligiga mos qilib (simmetrik) tuzatildi;
> run qayta o'tkazilmadi, mavjud ma'lumot qayta validatsiya qilindi.
> Asl hukm, kim nimani ko'rgani va muqobil yo'llar hisobotda saqlanadi.
> Pilot ma'lumoti eksplorativ."*

**1. FAKT — `p1-pilot-002` va uning ASL hukmi (`17` §1).**

| | |
|---|---|
| run katalogi | `~/revix-runs/p1-pilot-002` (guest; `dr-xr-xr-x` — faqat o'qish; `17` sarlavhasi) |
| `git_commit` / `git_dirty` | `8deaaf0` / `False` |
| `run_meta.disposition_facts.method` | `post_window_reducer_facts` |
| trial'lar | **120/120** `trial_end`; driver rc 0 |
| wall | `wall_s 6792` |
| post-flight | `boot_id` va pid1 **o'zgarmagan**; `real_minus_mono` +2 µs; `oom_kill` 0 → 0; `clock-watch` `\|Δreal − Δmono\| ≤ 9 µs` |
| `p1-pilot-001` ning uch xato klassi | **takrorlanmadi**: `window_outside_hold_complete` 0, `action_without_invocation_change` 0, `complete` + `probe_gap` 0 (yagona xato `aborted_guard` trial'ida; 23 ogohlantirish hammasi `censored`) |
| `revix.validate` | **O'TMADI — 1 xato, 23 ogohlantirish** |

**Asl hukm — o'chirilmaydi, iqtibos qilinadi.** `validate.txt` va
xotirada qayta ishlatilgan `validate_run_dir` (o'zgartirilmagan kod,
`8deaaf0`) bir xil natija beradi (`17` §1). `revix/validate.py` (`8deaaf0`)
bunday run uchun yakuniy satrni *"O'TMADI -- bu run ANALIZ QILINMAYDI
(§14.6)"* deb chiqaradi (`:2763`; satrning `validate.txt` dagi aynan
ko'rinishini bu amendment muallifi ko'rmagan).

| daraja | soni | topilma |
|---|---|---|
| ERROR | **1** | `probe_gap` — `b010t005` (`no_action/P2`, blok 10, o'rni 5), disposition **`aborted_guard`**, 1 uzilish, **678 119 µs** |
| WARNING | **23** | hammasi `probe_gap`, hammasi `censored`, `reason probe_gap_exceeded`; `probe_coverage_gap` — 0 |

**`b010t005` vaqt chizig'i** (`trial_begin` dan, s; `17` §2.3): `prober_start`
0.066; **uzilish 5.066 → 5.744** (baseline ichida); `probe_overrun` ×2
(5.414, 5.744); `baseline_window` 15.000; `fault_inject` 23.646;
`guard_event` (`kill_subtree`, `user_full_rate2s_runaway`) 27.275;
`trial_end` 41.100 — `reason guard_fired`, `aborted_guard`,
`matched_rules = [guard_fired, bystander_lost_contract,
probe_gap_exceeded, horizon_ended_down, measured]`. Uzilish injeksiyadan
**18 s**, guard'dan **22 s** oldin.

**Orkestrator guest'da o'lchagan faktlar** (`17`, `15`, `16` ularni qayd
etmaydi; amendment muallifi guest'ga kirmagan, shuning uchun ularni
orkestrator o'zi o'lchab bergan, 2026-10-04, `p1-pilot-002.pilot/launcher.log`
va `run_meta.json` dan):

| fakt | o'lchangan qiymat |
|---|---|
| boshlanish | `2026-10-04 13:50:38Z` (`launcher.log`: `PILOT BOSHLANDI seed=20261006`) |
| `rng_seed` | `20261006` |
| `git_commit` / `git_dirty` | `8deaaf0aab33c51074ea69365a7b368830eaa332` / `False` |
| `preregistration_sha256` | `f0c45722b231687c5e73a4a41e52517a6bd0ae96669c1d244211d18d8ac7b117` (v1.13) |
| `schedule_digest` | `69ae399edbb20b5a0271d4b6657a3b5c1ec45b61b19a04a2bf9e0b6e8decb2dc` — v1.13 8-band va 5-preshart bilan **mos** |
| `run_mode` / `disposition_facts` | `pilot` / `post_window_reducer_facts` (pilot-001 da bu maydon yo'q) |
| arxiv | `~/revix-runs/_backup/p1-pilot-002.SHA256SUMS` (7 fayl) va `p1-pilot-002.tar.zst` (5 460 313 bayt) |
| katalog | `dr-xr-xr-x` (faqat-o'qish); `events.jsonl` sha256 `686014f93e8e437c69a7356903cdf2256f41ec7473cef504e53de4f1d17022b7` |

Bular bu qarorga asos emas, lekin run'ning kimligini qayd etadi.

**2. QAROR — validator tuzatishi, SIMMETRIK (`17` §6.2 (a)).**

**(2.1) FAKT — nuqson (`17` §2.1, §3; `revix/validate.py`, `8deaaf0`).**

| tekshiruv | hozirgi shart | `aborted_guard` / `contaminated` / `washout_timeout` / `harness_error` da | ustuvorlikka mos? |
|---|---|---|---|
| `check_probe_gaps` (`:615`, `:632`) | uzilish va disp ≠ `censored` ⇒ XATO | **XATO** | **YO'Q** — ko'r |
| `check_probe_coverage` → `probe_coverage_gap` (`:2316`, `:2356`) | chegaradagi uzilish va disp ≠ `censored` ⇒ XATO | **XATO** | **YO'Q** — ko'r (ikkala pilotda 0 marta ishlagan) |
| `check_guard_stream` → `guard_event_not_reflected` (`:2402`, `:2470`) | oynada `guard_event` va disp ∈ `MEASURED_DISPOSITIONS` = {`complete`, `censored`} ⇒ XATO | jim | **teskari yo'nalishda yumshoq** — `guard_fired` dan past turgan `contaminated` / `washout_timeout` ni ushlamaydi |

`17` §3 validator'ning **har** disposition'ga bog'liq tekshiruvini
ko'rib chiqdi (`trial_without_probes`, `check_window_containment`,
`check_harness_errors`, `check_disposition_cross_check`,
`check_trial_events`, `check_trial_overhead`, `sut_unit_state_missing`,
`check_trial_horizon`, `check_actions` ham): ustuvorlikka ko'r **faqat
ikkitasi** — `probe_gap` va `probe_coverage_gap`; bittasi teskari
yo'nalishda yumshoq — `guard_event_not_reflected`.

**(2.2) Tuzatish — faqat shu uchtasi** (validator agenti; bu amendment
kod yozmaydi):

1. **`probe_gap` va `probe_coverage_gap`:** XATO **faqat disposition
   `complete` bo'lsa**; boshqa har disposition'da (`censored`,
   `aborted_guard`, `contaminated`, `washout_timeout`, `harness_error`)
   **OGOHLANTIRISH**. Asos: uzilish **o'lchangan natija da'vosini**
   bekor qiladi; u trial'ni allaqachon natija analizidan chiqargan va
   uzilish qoidasidan **oldin** turuvchi disposition'ga **zid kela
   olmaydi**. Topilma **o'chirilmaydi** — u ogohlantirish sifatida
   hisobotda qoladi.
2. **`guard_event_not_reflected` — teskari tomonga:** trial oynasida
   `guard_event` bo'lsa, disposition **`aborted_guard`** (yoki
   `schedule.DISPOSITION_RULES` da undan oldin turuvchi
   **`harness_error`**) bo'lishi SHART; **boshqa har** disposition
   (`complete`, `censored`, `contaminated`, `washout_timeout`) — XATO.
3. Ikkalasi ham **faqat yaroqlilik qoidasi**: hech bir metrika, hech bir
   disposition qiymati, ustuvorlik tartibi, `schedule.py`, `reduce.py`
   yoki driver, va hech bir muzlatilgan ta'rif o'zgarmaydi. **Bu ta'rif
   o'zgarishi EMAS.** Lekin bu **yaroqlilik darvozasining** o'zgarishi —
   §14.6(4) ning qavsi endi ustuvorlik tartibi bilan birga o'qiladi
   (7-band).

**Tanlanmagan variant** (`17` §4, qayd uchun): og'irlikni **faktga**
bog'lash — *"uzilish bor ⇒ `probe_gap_exceeded` `matched_rules` da
bo'lishi shart, va disposition `complete` emas"*. U `p1-pilot-002` da
ham 0 xato beradi (24 uzilishli trial'ning hammasida fakt bor), va
`p1-pilot-001` da xatolarni **4 dan 5 ga** oshiradi (`b009t000`).
Tanlangan variant og'irlikni **disposition'ga** bog'laydi; bu amendment
fakt variantining tanlanmaganlik sababini qayd etmaydi (orkestrator
qarori). **Narxi (CHEKLOV):** tanlangan variantda chiqarilgan
trial'dagi uzilish `matched_rules` ga yozilmay qolsa ham faqat
ogohlantirish beradi.

**3. QAYTA VALIDATSIYA — mavjud `p1-pilot-002`, yangi run YO'Q.
Kutilgan ta'sir — tuzatilgan validator ishga tushirilishidan OLDIN, shu
yerda yozilgan.**

Tuzatilgan validator **arxivlangan** `p1-pilot-002` xom ma'lumoti ustida
ishlatiladi (katalog faqat o'qiladi; chiqish run katalogidan
**tashqarida**). Xuddi shu tuzatilgan validator `p1-pilot-001` ustida
ham — **faqat** uning qutqarilmasligini tasdiqlash uchun — ishlatiladi.

| run | asl (`8deaaf0`) | **kutilgan** (tuzatilgan validator) | o'zgaradigan trial |
|---|---|---|---|
| `p1-pilot-001` | O'TMADI — **4 xato, 3 ogohl.** | O'TMADI — **4 xato, 3 ogohl.** (o'zgarishsiz, **qutqarilmaydi**) | **yo'q** |
| `p1-pilot-002` | O'TMADI — **1 xato, 23 ogohl.** | **0 xato, 24 ogohl.** | **faqat `b010t005`** (XATO → ogohl.) |

**Kutilmaning manbai — halol:** probe qismi uchun bu `17` §4 ning
**xotiradagi** simulyatsiyasining natijasi (`p12_gate.py`; `validate.py`
fayli tahrirlanmagan) — ya'ni bu "bashorat" emas, **allaqachon
ko'rilgan** natija (0.4(1)). `guard_event_not_reflected` qismi
simulyatsiyada **yo'q edi**; uning ta'siri **0** deb kutiladi, chunki
`17` §0(d) va §3 ga ko'ra ikkala run'da guard_event'li **har** trial
`aborted_guard`. Haqiqiy tuzatilgan validator kodi boshqacha bo'lishi
mumkin (`17` §8) — shuning uchun kutilma bu yerda **qat'iy** yoziladi:
kutilgandan **har qanday** farq — 0.7-band.

**Xuddi shu kutilma `17` §10 da** (`c3ad687`, validator kodi
o'zgarishidan **oldin** commit qilingan) kod va trial darajasida
yozilgan: `p1-pilot-001` — 4 xato (`action_without_invocation_change` 1,
`probe_gap` 1 — `b007t001`, `window_outside_hold_complete` 2) va 3 ogohl.
(`disposition_cross_check` 2, `probe_gap` 1 — `b009t000`), oldin ham keyin
ham; `p1-pilot-002` — 1 xato / 23 ogohl. → **0 xato / 24 ogohl.**;
`guard_event_not_reflected` va `probe_coverage_gap` ikkala run'da oldin ham
keyin ham **0**; o'zgaradigan **yagona** topilma — `b010t005` ning
`probe_gap` i, XATO → OGOHLANTIRISH. Isbot usuli: "oldin" — `2849896`
validator'i, "keyin" — tuzatish commit'i, ikkalasi `python3 -m
revix.validate` bilan, chiqish run kataloglaridan tashqarida.

**4. QAROR — uchinchi run RAD ETILDI.**

1. **O'zgarmagan validator bilan uchinchi run faqat chiqarilgan trial'dagi
   uzilishdan yiqila oladi** (`probe_gap` tekshiruvi bo'yicha; `17` §6.3).
   Tuzatilgan driver `probe_gap_exceeded` ni `reduce.probe_gaps` dan oladi
   (`8deaaf0`), demak `complete` + uzilish **konstruksiya bo'yicha**
   bo'lmaydi; qolgan yo'l — aynan `p1-pilot-002` ni yiqitgan,
   natija analiziga kirmaydigan trial'lar klassi.
2. **Takrorlanish ehtimoli haqida hech narsa aytib bo'lmaydi** (`17`
   §6.3; arifmetika, **o'lchangan stavka emas**): uzilishli
   `aborted_guard` — **1 / 9** ⇒ `p̂ = 0.111`, Clopper–Pearson 95%
   **`[0.0028, 0.4825]`**; uchinchi run'da ham 9 ta `aborted_guard`
   bo'lsa, kamida bittasida uzilish ehtimoli `1 − (1 − p)^9`: nuqta
   **0.65**, interval chegaralari bilan **0.025 … 0.997** — deyarli
   butun `[0, 1]`. Bundan tashqari `aborted_guard` soni noma'lum, va
   uzilishlar **statsionar emas** (24 dan 23 tasi 10–19 bloklarda —
   5-band).
3. **Tuzatish baribir darvoza o'zgarishi bo'lardi.** Validator uchinchi
   run'dan oldin tuzatilsa ham darvoza o'zgaradi; farqi faqat u
   baholaydigan ma'lumotdan **oldin** bo'lishi (0.4(4)). Narxi: ~6800 s
   wall + VM + lock (`17` §6.2(b)), uchinchi run qarorining **o'zi** ham
   hisoblar ko'rilgandan keyin bo'lardi, va 5-banddagi instrument
   yo'qotishi takrorlanishi mumkin (GIPOTEZA, `17` §7).

**Variantlar** (`17` §6.2):

| # | variant | holat |
|---|---|---|
| **(a)** | validator tuzatishi + mavjud `p1-pilot-002` ni qayta validatsiya | **TANLANDI** (simmetrik shaklda — 2-band) |
| (b) | v1.14 + uchinchi run; `p1-pilot-002` yaroqsiz qoladi | **rad etildi** — yuqoridagi 1–3 |
| (c1) | `p1-pilot-002` yaroqsiz, uchinchi run yo'q; P1 yaroqli run'siz yakunlanadi | **tanlanmadi** (orkestrator qarori); narxi — analiz qilinadigan pilot yo'q |
| (c2) | validator + prober yozuvini o'zgartirish (masalan `fsync` ni o'lchov tsiklidan chiqarish), smoke, uchinchi run | **tanlanmadi**: 5-banddagi gipoteza avval **o'lchanishi** kerak; instrument pilotlar orasida o'zgarardi. Instrument qarori — 5-band, confirmatory run'dan oldin |
| (c3) | (a) faqat "sezgirlik" sifatida, asosiy hukm "yaroqsiz" | **ruxsat yo'q** — v1.13 (0.6) yaroqsiz run'ning har qanday analizini taqiqlaydi; V-C ham rad etilgan |

**5. ALOHIDA YAROQLILIK TOPILMASI — probe uzilishi tarqalishi. Bu tuzatishning QISMI EMAS.**

**(5.1) FAKT** (`17` §5):

- `p1-pilot-002` da **24/120** trial'da (20%, ya'ni **beshdan bir**) probe
  uzilishi > 2P; jami **68** uzilish; shu trial'larda **101** ta
  `probe_overrun` record'i; eng katta uzilish **4 689 678 µs**
  (`b016t003`). `p1-pilot-001` da uzilishli trial **2** ta edi (`15`) —
  bu instrument fakti, natijalar solishtiruvi **emas**.
- **Blok bo'yicha:** 3:1, 10:1, 11:2, 12:2, 13:1, 14:5, 16:3, 17:3,
  18:5, 19:1 ⇒ 0–9 bloklarda **1**, 10–19 bloklarda **23**.
- **Yacheyka bo'yicha** (`b010t005` bilan): `A/P0` 3, `A/P1` 5, `A/P2` 6,
  `no_action/P0` 5, `no_action/P1` 2, `no_action/P2` 3 — **har olti
  yacheykada**.
- **Faza:** 68 uzilishdan **55 tasi** shu trial'ning `prober_start` idan
  `k × 5 s` dan keyin **0.0–0.3 s** ichida boshlanadi (`k` = 1…8); bir
  trial ichidagi ketma-ket juftlarning **31/44** tasi orasidagi masofa
  5 s karralisidan ≤ 0.25 s farq qiladi.
- **Kod:** prober har trial uchun qayta ishga tushadi
  (`driver._start_prober`); `probe_sample` ni `schema.CsvWriter` orqali
  yozadi (`prober.py:886`), va `CsvWriter.write` har
  `flush_interval_s = 5.0` s da **o'lchov tsikli ichida sinxron**
  `flush()` + `os.fsync()` qiladi (`schema.py:118`, `:147–150`).
  `revix/schema.py` va `revix/prober.py` `4cbd1c6` (`p1-pilot-001`) va
  `8deaaf0` (`p1-pilot-002`) orasida **bayt bo'yicha bir xil**
  (`git diff --stat` bo'sh; oxirgi o'zgarish `b712f6d`, ikkalasining
  ajdodi).

**(5.2) GIPOTEZA — O'LCHANMAGAN.** Uzilishlarning asosiy qismi prober'ning
o'z CSV fayliga 5 s lik sinxron `fsync` ning **muhit sababli**
cho'zilishi (guest disk / host IO yoki fayl hajmi). `fsync`
davomiyligi, disk IO va host holati vaqt bo'yicha **o'lchanmagan**;
`fsync` hech qayerga yozilmaydi. **68 dan 13 uzilish bu fazaga
tushmaydi — sababi noma'lum.** **Sabab da'vo qilinmaydi.**

**(5.3) Tadqiqot uchun oqibati.** Bunday trial §4 bo'yicha `censored`
(`disposition_source = probe_gap`): §16.2(B) bo'yicha binar birlamchi
`P(VR)` to'plamidan **chiqariladi** (natija kuzatilmagan), §6.2 bo'yicha
KM / log-rank ga **censored davomiylik** sifatida kiradi. Demak
`p1-pilot-002` trial'larining **beshdan biri** binar natijasini
**instrument yo'qotishiga** boy beradi.

1. **Yacheyka va arm bo'yicha chiqarilish jadvali MAJBURIY** (v1.12 3.3(4),
   §17.4(4), v1.13 7.2) va u **buni ko'rsatishi shart**: `probe_gap`
   chiqarilishi **har `(arm × pressure)` yacheykasi bo'yicha alohida**,
   `aborted_guard`, `window_past_*` va boshqa chiqarilishlardan
   **ajratilgan holda**, blok bo'yicha taqsimot bilan.
2. Uning natijaga ta'siri **baholanmagan** (`17` §5.4); bu amendment uni
   baholamaydi.
3. **Birorta confirmatory run'dan OLDIN:** `fsync` gipotezasi **o'lchanishi**
   (masalan `fsync` davomiyligi, prober tsikli bilan bir vaqtda) va
   **instrument qarori** (prober yozuvini o'zgartirish yoki o'zgartirmaslik,
   asoslangan holda) **qabul qilinishi SHART**. Bu P1 pilotining analizini
   to'xtatmaydi, lekin confirmatory dizaynni to'xtatadi.

**6. NIMA O'ZGARMADI — to'liq ro'yxat.**

**Validator tuzatishi ta'rif o'zgarishi EMAS** — u validator'ning ikki
tekshiruvini muzlatilgan ustuvorlik tartibi bilan **mos qiladi**, va
uchinchisini shu tartib bo'yicha **qat'iylashtiradi**; **hech bir
ta'rif, chegara yoki qiymat yangidan tanlanmadi.**

**Hech bir metrika ta'rifi** (§4 VR va uning invalidator'lari, §5 FR-A /
FR-B, §6.1 `D_sd` / `D_probe` / `D_eff`, §6.2 censoring, §6.3 latency,
§6.4 recovery loop, §7 pressure o'lchovi); **hech bir statistik test**
(§10.1 Cochran–Armitage, Fisher/Barnard, Newcombe/Wilson,
Clopper–Pearson; §10.2 Kaplan–Meier / log-rank / RMST difference /
Cox-HR taqiqi / BCa; §10.4 Holm); **hech bir arm** (`A`:
`Restart=on-failure`, `RestartSec=100ms`; `no_action`: `Restart=no`);
**hech bir fault klassi** (faqat `clean_crash`, trial'ga bitta injeksiya);
**probe parametrlari**; **`P0`/`P1`/`P2` bandlari** (§9.3); **`disposition`
ning yopiq enum'i**, *"aynan bitta"* qoidasi (§12) va **ustuvorlik
tartibi** (`schedule.DISPOSITION_RULES`, `reduce.derive_disposition`,
`04` §8.1 — kod va shartnoma **tegilmaydi**); §16.2 (A)/(B) va
`(disposition, disposition_source)` qoidasi; §17.4 ning ikki
`disposition_source` qiymati va besh bandi; **§11 butunlay** (kuchli
shakl, fail-slow limbi `thr = 0.20 × τ = 1.6 s`, halol power bayonoti,
davom etish mezonlari, null bo'lsa burilish); **§14 data schema**;
§14.6 invariantlari (**matni tahrirlanmadi, qayta raqamlanmadi**; faqat
7-banddagi belgilangan ko'rsatkich); v1.12 ning `host_clock_discontinuity`
qoidasi va smoke/kalibratsiya chiqarilishi; **v1.13 ning uch driver
tuzatishi** (3.1) va `04` ning v1.2 uchinchi revizyasi; §0, §13 —
**tegilmadi**; §15–§22 ning qarorlari **o'z kuchida**.

| qiymat | holat |
|---|---|
| `W_stab_pilot = 8 s`, `W_stab = 60 s` | **O'ZGARMADI** |
| `τ = 8 s` (§10.2, §11) | **O'ZGARMADI** |
| `hold_cap_s = 13 s`, `ramp_s = 5 s`, baseline 10 s, pre-flight 5 s, washout `≥ 20 s` | **O'ZGARMADI** |
| `injection_offset = 3 s` | **O'ZGARMADI** |
| `θ = 0.8` | **O'ZGARMADI** |
| `k_f = 3` (`D_f = 300 ms`) | **O'ZGARMADI** |
| `P = 100 ms`, `T_conn = 50 ms`, `T_rt = 50 ms` | **O'ZGARMADI** |
| **20 blok / 120 trial** (`3 × 2 × 20`) | **O'ZGARMADI** |
| seed `20261006`, `schedule_digest` `69ae399e…cb2dc` | **O'ZGARMADI** |
| `ε = 32 MiB`, quiescence `0.05`, `T_q = 5 s`, `T_w = 15 s`, `T_w_max = 120 s` | **O'ZGARMADI** |
| guard: `sustain_rate_threshold = 0.35`, `sustain_max_seconds = 15.0`, `user_full_rate2s_max = 0.98`, `user_full_avg10_max = 85.0`, `user_some_avg10_max = 90.0`, `host_mem_available_min_kb = 1 500 000` (`revix/guard.py` `DEFAULTS`); `guard_sustain_s = 15 s` (§9.4) | **O'ZGARMADI** |
| dial: slice `MemoryMax = 2G`, `MemoryHigh = 192M`, `CPUQuota = 400%`, `TasksMax = 256`; generator `step_mb = 4`, `base_mb` 160 / 184 / 184, `target_rate` 0.0 / 0.30 / 0.60, `interval_ms = 250`, generator unit `MemoryMax = 1536M` | **O'ZGARMADI** |
| v1.12 muzlatilgan ochiq parametrlari: `WatchdogSec = 5 s`, `MemoryHigh = 192M`, `TimeoutStartSec = 10 s` (og'ish bilan), `T_trial = 41.1 s` | **O'ZGARMADI** (v1.12 1-band, og'ish e'loni ham) |
| V2 generator vaqti: start `t_h − R = 17.43 s`, `R = 2.57 s`, `hold_s + R = 15.57 s`, `pressure_off = 33.0 s` | **O'ZGARMADI** (v1.12 2-band) |
| v1.13 driver tuzatishlari: §17.4 oyna fakti, §4 probe fakti (`reduce.probe_gaps`), `t_issue` vaqt manbai | **O'ZGARMADI** (v1.13 3.1) |
| `P2` dagi runaway yo'qotishi kutilmasi va uning bias mulohazasi | **O'ZGARMADI** (v1.12 3-band; 9-band) |

**7. §14.6 KO'RSATKICHI va TARIXIY BO'LIMLAR.**

**Tarixiy bo'limlar qayta yozilmadi** (v1.11–v1.13 siyosati). **v1.13
log yozuvi** — jumladan uning (0.6) bandi, V-B ning rad etilishi va
8-band preshartlari — **o'zgartirilmadi**: u `v0.1.13-preregistration`
tag'i bilan e'lon qilingan versiyaning bayonoti; `p1-pilot-002` **o'sha**
versiya ostida o'tkazilgan va **o'sha** versiyaning darvozasidan
o'tmagan. Sarlavha jadvalining v1.11–v1.13 qatorlari ham tegilmadi.
Buning o'rniga **normativ** joylarga **belgilangan `v1.14`
ko'rsatkichi** qo'yildi: sarlavha jadvali va §14.6.

**§14.6(4) ko'rsatkichi nimani aytadi:** (4) ning qavsi (*"aks holda
trial `censored`"*) **ustuvorlik tartibi bilan birga** o'qiladi — uzilish
probe-uzilish qoidasiga yetib kelgan trial'ni `censored` qiladi; undan
**oldin** turuvchi disposition olgan trial uchun uzilish topilma
(ogohlantirish) sifatida qayd etiladi. **Bu o'qish ma'lumotdan keyin
yozilgan talqin** — dalili `17` §2 (muzlatilgan jumlalar, `b010t005`,
so'zma-so'z o'qishda muvofiq disposition yo'qligi) va §3 (tekshiruvlar
auditi). §14.6 matni **o'zgartirilmadi**.

**8. MA'LUMOT HOLATI.**

| to'plam | holat | pilot to'plamiga |
|---|---|---|
| **`p1-pilot-001`** (120 trial, v1.12, `4cbd1c6`) | guest'da, faqat o'qish; **YAROQSIZ** (§14.6; v1.13); v1.14 tuzatishi uni **qutqarmaydi** (3-band) | **HECH QACHON** — analiz qilinmaydi, birlashtirilmaydi, **o'chirilmaydi** (v1.13 0.5) |
| **`p1-pilot-002`** (120 trial, v1.13, `8deaaf0`) | guest'da, faqat o'qish; v1.13 darvozasi ostida **O'TMADI** (1 xato — asl hukm saqlanadi); v1.14 ning tuzatilgan darvozasi ostida yaroqli bo'lishi **kutiladi** — hukm 10-band (3) bajarilganda yoziladi; **analiz qilinmagan** | **YAGONA** analiz qilinishi mumkin bo'lgan pilot run'i — **faqat** 10-banddagi preshartlardan keyin |
| `17` ning xotiradagi qayta validatsiyasi (`gate.json`) | guest scratch'da | **HECH QACHON** — yaroqlilik tekshiruvi |
| tuzatilgan validator'ning `p1-pilot-001` / `p1-pilot-002` ustidagi chiqishi | hali yo'q | **HECH QACHON** natija sifatida — yaroqlilik hukmi |
| v1.13 tuzatishlarining smoke partiyasi, `open-params-*`, `dose-*`, `tstart-*`, `dprobe-*`, `smoke-*` | v1.12 8-band va v1.13 6-band jadvalidagidek | **HECH QACHON** (v1.12 4.5) |

**Hech qanday tadqiqot ma'lumoti analiz qilinmagan.** `p1-pilot-002`
dan ko'rilgan narsa — 0.1-banddagi ro'yxat.

**9. BU AMENDMENT NIMANI YOPMAYDI.**

1. **Probe uzilishi tarqalishi va o'lchanmagan `fsync` gipotezasi**
   (5-band) — 13 uzilishning sababi noma'lum; confirmatory run'dan oldin
   o'lchov va instrument qarori **shart**.
2. **Yacheyka va arm bo'yicha chiqarilish jadvali** — MAJBURIY (5.3(1);
   v1.12 3.3(4); §17.4(4); v1.13 7.2); u hali **tuzilmagan**.
3. **`P2` dagi runaway guard kutilmasi** e'lon qilinganicha qoladi (v1.12
   3.3–3.5) — bias mulohazasi va confound ogohligi bilan. `p1-pilot-002`
   ning `aborted_guard` soni (0.1-band) bu kutilmani **yangilash yoki
   stavkani baholash uchun ishlatilmaydi**.
4. **OQ-11** — boshqa `MemoryHigh` qiymatlari o'lchanmagan (v1.12 1.2, 9.2).
5. **v1.13 dan qolgan jonli sinalmagan yo'llar** (`8deaaf0` merge xabari:
   probe gap, oyna hold'dan tashqarida, eskirgan `ActiveExit`, runaway
   trip'dan keyingi istisno yo'li). `17` ga ko'ra `p1-pilot-002` da
   ulardan ba'zilari **ishlagan** — `probe_gap_exceeded` 24 trial'ning
   hammasida `matched_rules` da, `window_outside_hold` `b017t001` va
   `b019t000` da, 9 `aborted_guard` bilan `harness_error` 0 — lekin
   ularning to'g'riligi validator'dan tashqari **alohida tekshirilmagan**;
   eskirgan `ActiveExit` yo'li haqida `17` da ma'lumot **yo'q**. Ochiq
   qoladi.
6. **Bitta kernel** (v1.12 9.4) — boshqa kernel'da kalibratsiya yo'q.
7. **Host uyqusi runtime'da aniqlanmaydi** — faqat post-hoc
   (`host_clock_discontinuity`, `clock-watch`; v1.12 4.4); 1 s dan
   qisqa muzlashni ushlamaydi.
8. **Ustuvorlik tartibi `PREREGISTRATION.md` da tartiblangan ro'yxat
   sifatida yozilmagan** (0.3(1) CHEKLOV) — u `schedule.py` va `04` §8.1
   da; v1.14 uni muzlatilgan matnga **ko'chirmaydi**.
9. `p1-pilot-002` ham ko'rilmagan klassni ochgani kabi, **keyingi run**
   ham yangi klass ochishi mumkin; uning ehtimolini baholab bo'lmaydi.

**10. `p1-pilot-002` NI ANALIZ QILISH PRESHARTLARI.** `p1-pilot-002`
ustida birorta natija (VR, FR, downtime, `t_up` taqsimoti, yacheyka
bo'yicha hisob, test) hisoblanmaydi, toki:

1. **Validator tuzatishi** (2.2) — **unit testlari** va **oldin/keyin
   isboti** bilan (ikkala run ustida asl va tuzatilgan validator
   natijasi yonma-yon) — **`main` ga merge qilingan** (`17` bilan birga).
2. **v1.14 `main` ga merge qilingan va tag qilingan**
   (`v0.1.14-preregistration`).
3. **Tuzatilgan validator arxivlangan `p1-pilot-002` ma'lumoti ustida
   ishlatilgan**, va uning hukmi **asl hukm (1-band) yonida** yozilgan;
   natija 3-banddagi kutilmaga **aynan** mos (`p1-pilot-002`: 0 xato,
   24 ogohl., faqat `b010t005` o'zgargan; `p1-pilot-001`: 4 xato,
   3 ogohl., o'zgarishsiz). Har qanday farq — 0.7-band.

**To'xtatmaydigan narsalar:** 9-banddagi ochiq cheklovlar — e'lon
qilingan; ular `p1-pilot-002` analizini to'xtatmaydi, lekin 5.3(3)
confirmatory run'ni to'xtatadi.

### v1.12 → v1.13 (2026-10-04)

| | |
|---|---|
| **v1.12 sha256** | `ccb6186e55d94935cedd4a4e49562675fa5a2b1e276ae799e4605e239d004ad2` |
| **v1.12 git tag** | `v0.1.12-preregistration` |
| **Sabab** | Birinchi pilot run'i **`p1-pilot-001`** 120/120 trial'ni tugatdi, lekin `revix.validate` dan **O'TMADI** (4 xato, 3 trial) — §14.6 bo'yicha run **analiz qilinmaydi**. Sabab — uchta **driver implementatsiya nuqsoni**; validator va muzlatilgan ta'riflar to'g'ri ishladi (`docs/architecture/15-pilot-001-validatsiya-xatolari.md`, `main` `7b41ca7`). Pilotni **qayta o'tkazish** qarori disposition hisoblari **ko'rilgandan keyin** qabul qilindi — shuning uchun u shu yerda, oshkora e'lon bilan, **ikkinchi run boshlanishidan OLDIN** yoziladi |
| **Qarorni kim qabul qildi** | **Orkestrator**, loyiha egasining **2026-10-03 dagi ochiq delegatsiyasi** bo'yicha (v1.11 va v1.12 dagi o'sha delegatsiya). Asos fayl: `15` (§0–§7). Matnni `agent/amend-v113` agenti yozdi; **har bir raqam `15` ga va u keltirgan fayllarga (`PREREGISTRATION.md`, `04`, `14` §13, `revix/schedule.py`, `revix/driver.py`, `datasets/smoke-tools/p1_validity.py`) qarshi tekshirildi**; guest'ga kirilmadi — tekshirilmagan ikki bayonot 1-bandda belgilangan |
| **O'zgardi** | **Hech bir ta'rif emas.** **(1)** `p1-pilot-001` **yaroqsiz** deb qayd etildi: saqlanadi, hech qachon analiz qilinmaydi, o'chirilmaydi (1-, 6-band). **(2)** Qaror **V-A** (`15` §5.2): driver'ning uch nuqsoni tuzatiladi — §4 va §17.4(2), (5) ni **implementatsiya qiladi** — va butun pilot **`p1-pilot-002`** sifatida **bir xil seed va bir xil jadval** bilan qayta o'tkaziladi (3-band). **(3)** `p1-pilot-002` — **analiz qilinishi mumkin bo'lgan YAGONA pilot run'i**; birlashtirish va tanlab iqtibos keltirish taqiqi; u ham yiqilsa nima bo'lishi (0-band). **(4)** `p1-pilot-002` preshartlari (8-band) |
| **O'zgarMADI** | **hech bir metrika, statistik test, arm, fault klassi, probe parametri, VR/FR ta'rifi, `disposition` enum'i, falsifikatsiya mezoni**, `W_stab_pilot`, `τ`, `hold_cap_s`, `injection_offset`, `θ`, `k_f`, `P`, `T_conn`, `T_rt`, blok va trial soni, **seed**, **jadval digest'i**, **guard chegaralari**, **dial**, v1.12 ning **muzlatilgan ochiq parametrlari** va **V2 generator vaqti**. To'liq ro'yxat — 4-bandda |
| **Yig'ilgan ma'lumot** | **Bitta pilot run'i mavjud va u YAROQSIZ** (`p1-pilot-001`). **Hech qanday tadqiqot ma'lumoti analiz qilinmagan** — VR, FR, downtime, `t_up` taqsimoti, p-qiymat yoki effekt bahosi **hisoblanmagan**. **LEKIN disposition hisoblari ko'rilgan** — 0-band. Smoke va kalibratsiya ma'lumoti — pilot to'plamidan **chiqarilgan** (v1.12 4.5). To'liq holat — 6-band |

**0. 🔴 OSHKORA E'LON — qayta o'tkazish qarori DISPOSITION HISOBLARI KO'RILGANDAN KEYIN qabul qilindi.**

**(0.1) Kim nimani ko'rdi** (`15` §0, va `7b41ca7` merge xabaridagi
orkestrator bayonoti):

| kim | nimani ko'rdi | nimani ko'rmadi |
|---|---|---|
| **orkestrator** | pilot ishlayotgan paytda **har `(arm × pressure)` yacheykasi bo'yicha disposition sonlari** (o'zi chop etgan) | — (bu amendment uning boshqa ko'rganlarini da'vo qilmaydi) |
| **tahlil agenti** (`15`) | `validate.txt` to'liq; `driver.json` dagi **run bo'yicha jami**: `aborted_guard` **10**, `censored` **57**, `complete` **53**; 10 ta `guard_event` (hammasi `user_full_rate2s_runaway`); uch nomlangan trial'ning xom record'lari; 120 trial bo'yicha **faqat yaroqlilik** klassifikatsiyasi | yacheyka bo'yicha `complete` maxrajlari; VR, FR, downtime, `t_up` taqsimoti, p-qiymat, effekt bahosi — **hisoblanmagan** (`15` §0) |
| **shu amendment muallifi** | `15` ning matni (yuqoridagi jami sonlar shu orqali); `p1_validity.py` ning **kodi** | uning chiqishi (`validity.json` commit qilinmagan, `15` §7); guest'dagi run katalogi |

**(0.2) Qaysi qoida, va nega u QO'LLANADI.** §16.10(3): *"Hech qanday P1
natijasi ko'rilgandan keyin o'zgartirilMAYDI. Post-hoc o'zgarish run'ni
bekor qiladi, parametrni emas."* Harfan bu qoida **ochiq parametrlar**
haqida (`15` §5.1), harness kodi haqida emas. Lekin uning **maqsadi** —
natijaga qarab o'zgartirmaslik — **o'xshatish bo'yicha qo'llanadi**:
disposition hisoblari P1 natijasining bir qismi (§12: *"Yuqori
eksklyuziya darajasi o'zi natija"*), va qayta o'tkazish qarori ular
ma'lum bo'lgandan keyin qabul qilindi. **Shuning uchun "ko'r tanlangan"
degan kafolat bu qarorga BERILMAYDI.**

**(0.3) Nega qayta o'tkazish baribir asosli.**

1. **Run muzlatilgan yaroqlilik darvozasidan o'tmadi** (§14.6) — natija
   sababli emas, **implementatsiya sababli**, va bu sababni **muzlatilgan
   matnning o'zi** aniqlaydi: §4 (*"Probe uzilishi > 2×P → trial
   `censored`"*), §14.6(4), §17.4(2) va §17.4(5) (*"`complete` deb
   yozilgan bo'lsa — bu validator xatosi"*). Rad etish mezoni run
   boshlanishidan **oldin** yozilgan edi; uni hech kim ma'lumotdan keyin
   qo'ymadi.
2. **Tuzatishlar muzlatilgan ta'riflarni implementatsiya qiladi** — hech
   bir chegara, ta'rif yoki qiymat o'zgarmaydi (4-band). Har uch
   tuzatishning **to'g'ri chiqishi** muzlatilgan matn bilan oldindan
   belgilangan (`b007t001` → `censored`, `b013t004` → `censored`,
   `b010t001` ning ikki action'i — ikki turli `t_issue`; `15` §5.2 V-B):
   tuzatuvchi uchun **tanlov erkinligi yo'q**.
3. **Alternativalar yomonroq** (3.3-band): darvozani ma'lumotdan keyin
   yumshatish (V-B) yoki trial'larni tanlab olib tashlash (V-D) — aynan
   §16.10(3) ning ruhi taqiqlagan narsa.

**(0.4) Qayta o'tkazishni nima E'TIROZLI qiladi.** `p1-pilot-001` va
`p1-pilot-002` orasidagi har qanday o'zgarish **muzlatilgan ta'rifning
implementatsiyasi bo'lmasa** — masalan guard chegarasi, dial, `T_trial`,
generator vaqti, ochiq parametr, seed, jadval, blok soni, arm yoki band
tartibi, prober yoki SUT sozlamasi, yoki driver'ning disposition
qoidalarining 3.1-banddagi uch nuqsondan **tashqaridagi** har qanday
o'zgarishi — u **post-hoc o'zgarish**, va `p1-pilot-002` ni ham
**yaroqsiz** qiladi (§16.10(3) ruhi). Buning mexanik tekshiruvi —
8-band, 2-preshart (oflayn replay **boshqa hech bir** trial'ning
disposition'ini o'zgartirmasligi) va 5-preshart (jadval digest'i bir
xil). Tuzatish agenti vazifasidan tashqari biror narsa kerak deb
topsa — **to'xtaydi va xabar beradi**, yangi amendment'siz
o'zgartirmaydi.

**(0.5) BIAS YO'NALISHI — qayta o'tkazish faqat ALMASHTIRADI, hech qachon
TANLAMAYDI.**

- **`p1-pilot-002` — analiz qilinishi mumkin bo'lgan YAGONA pilot run'i.**
  Bu **hozir**, `p1-pilot-002` ning birorta trial'idan oldin
  belgilanadi, va uning natijasi qanday bo'lishidan **qat'i nazar**
  o'zgarmaydi.
- **`p1-pilot-001` hech qachon:** analiz qilinmaydi; `p1-pilot-002` bilan
  **birlashtirilmaydi** (pooling); sezgirlik, izchillik yoki "takrorlash"
  tekshiruvi sifatida **ishlatilmaydi** (V-C rad etildi — 3.3-band);
  natija sifatida **tanlab iqtibos keltirilmaydi**; uning disposition
  sonlari `p1-pilot-002` ning sonlari bilan **solishtirilmaydi**. Unga
  havola faqat **yaroqsiz run va uning sababi** sifatida (`15`, shu band)
  va 3.2(2) ning **yaroqlilik replay'ida** (faqat o'zgargan trial'lar
  ro'yxati) mumkin.
- Shuning uchun "ikki run'dan yoqqanini olish" yo'li **yo'q**: tanlov
  bitta (qayta o'tkazish), u natija ko'rilishidan **oldin** yopiladi, va
  qolgan yagona run'ning natijasi qanday chiqsa — shunday hisobot qilinadi.
- **Qolgan xavf, ochiq:** qayta o'tkazish qarorining **o'zi** hisoblar
  ma'lum bo'lgandan keyin qabul qilindi. Agar `p1-pilot-001` ning
  hisoblari "yoqqan" bo'lganida, darvozani yumshatish (V-B) jozibali
  bo'lardi — bu xavf **V-B ning rad etilishi** va yuqoridagi "yagona run"
  qoidasi bilan **cheklanadi**, lekin **nolga tushmaydi**. O'quvchi buni
  ko'rishi shart.
- **Tuzatishning o'z yo'nalishi yangi emas.** Kech oynali `complete`
  trial'larni `censored` qilish — §17.4 ning qarori; uning bias
  yo'nalishi **§17.6 da birorta P1 ma'lumotidan oldin** e'lon qilingan,
  va v1.13 uni **o'zgartirmaydi**. `probe_gap` → `censored` — §4 ning
  matni. Ikkalasi ham `A/P2` yacheykasida to'planishi mumkin —
  shuning uchun yacheyka jadvali majburiy (7-band).

**(0.6) Agar `p1-pilot-002` ham validatsiyadan o'tmasa.** U §14.6 bo'yicha
**analiz qilinmaydi**; xuddi `p1-pilot-001` kabi **saqlanadi, yaroqsiz
deb belgilanadi, o'chirilmaydi**; sababi `15` uslubidagi **faqat
yaroqlilik** tahlili bilan va **shu banddagi oshkora e'lon bilan** (kim
nimani ko'rdi) yoziladi. **Uchinchi run yangi amendment'siz (v1.14 yoki
keyingi) O'TKAZILMAYDI** — u amendment uchinchi run'dan **oldin** merge
qilinadi va tag qilinadi. `p1-pilot-001` va `p1-pilot-002` hech qachon
birlashtirilmaydi; "yagona analiz qilinadigan run" qoidasi ham shu
amendment orqali qayta belgilanadi.

> **Maqolada shunday yoziladi:** *"Birinchi pilot run'i 120/120 trial'ni
> tugatdi, lekin oldindan belgilangan yaroqlilik darvozasidan
> (validator) driver implementatsiyasidagi uch nuqson tufayli o'tmadi va
> analiz qilinmadi. Nuqsonlar muzlatilgan ta'riflarni o'zgartirmasdan
> tuzatildi va pilot bir xil seed va jadval bilan qayta o'tkazildi;
> qayta o'tkazish qarori birinchi run'ning disposition hisoblari
> ko'rilgandan keyin, lekin ikkinchi run'dan OLDIN qabul qilingan va
> faqat ikkinchi run analiz qilingan."*

**1. FAKT — `p1-pilot-001` (`15` §1).**

| | |
|---|---|
| run katalogi | `~/revix-runs/p1-pilot-001` (guest; `dr-xr-xr-x` — faqat o'qish) |
| zaxira | `~/revix-runs/_backup/p1-pilot-001.tar.zst` (`15` sarlavhasi) |
| `git_commit` / `git_dirty` | `4cbd1c6` / `false` |
| pre-registration | `preregistration/v1.12`, `ccb6186e…` |
| seed / `schedule_digest` | `20261006` / `69ae399edbb20b5a0271d4b6657a3b5c1ec45b61b19a04a2bf9e0b6e8decb2dc` (`14` §13.2 dagi bilan bir xil) |
| `generator_window.lead_s` | `2.57` (V2) |
| trial'lar | **120/120** `trial_end` |
| post-flight | `boot_id`, pid1 `653523`, `real − mono` siljishi (oldin ham, keyin ham bir xil), `oom_kill 0` — **o'zgarmagan**; `clock-watch.log` da `\|Δreal − Δmono\| ≤ 3 µs` |
| wall | 6754 s (`15` §5.2) |
| `revix.validate` | **4 xato, 3 ogohlantirish** — *"O'TMADI — bu run ANALIZ QILINMAYDI (§14.6)"* |

**Orkestrator o'lchagan ikki fakt** (`15` ularni qayd etmaydi; amendment
muallifi guest'ga kirmagan, shuning uchun ularni orkestrator o'zi guest'da
o'lchab bergan, 2026-10-04):

- **Qoldiq holat:** launcher post-flight'da `revix doctor`ni **ISHGA
  TUSHIRMAGAN**, shuning uchun `leftover_state` tekshiruvining o'zi bu run
  uchun mavjud emas. O'lchangani: `systemctl --user list-units 'revix*'
  --all` — **0** ta unit; `user@1000.service` ostidagi `revix*` cgroup —
  **0** ta; `oom_kill` oldin ham, keyin ham 0.
- **Yaxlitlik:** run papkasi yaxlitlik yig'indisi bilan arxivlangan
  (`~/revix-runs/_backup/p1-pilot-001.SHA256SUMS`, yaxlit 7 fayl) va siqilgan
  nusxasi `p1-pilot-001.tar.zst` (5 395 648 bayt); papka **faqat-o'qish**
  qilindi. `events.jsonl` sha256:
  `f8fa7001fbbbe8e970f8e67f2e1e0c30c1f266253605ec26904923c46e8ceee2`.

Ikkalasi ham hech bir qarorga asos emas.

**Xatolar** (`15` §1):

| trial | yacheyka | topilma | daraja |
|---|---|---|---|
| `b007t001` | A, P2 | `probe_gap` (492 256 µs > 2P) + driver `complete` | ERROR |
| `b007t001` | A, P2 | `window_outside_hold_complete` (`t_up + W_stab` `T_h` dan 0.391 s keyin) | ERROR |
| `b013t004` | A, P2 | `window_outside_hold_complete` (1.550 s keyin) | ERROR |
| `b010t001` | A, P2 | `action_without_invocation_change` | ERROR |

**Faqat yaroqlilik tekshiruvi** (`15` §4; `p1_validity.py` —
validator'ning o'z funksiyalari): driver `complete` deb yozgan har
trial'da ikki shart — buzilish **faqat `A/P2` da** (probe uzilishi 1,
oyna hold'dan tashqarida 2); **qolgan besh yacheykada 0**. Oyna holati
`not_evaluated` bo'lgan `complete` trial yo'q. Validator'ning qolgan
tekshiruvlari (`probe_coverage`, `host_clock_discontinuity`,
`guest_generation`, `trial_timing` va boshqalar) — **xato yo'q**.

**2. FAKT — uchta DRIVER nuqsoni (validator ham, muzlatilgan ta'rif ham EMAS).**

| # | muzlatilgan matn | driver nima qildi | trial |
|---|---|---|---|
| 1 | §17.4(1), (2): oynasi hold ichida bo'lmagan trial `censored` (`window_past_pressure` / `window_past_horizon`); §17.4(5): `t_up + W_stab_pilot > T_h` bo'lgan `complete` — **validator xatosi** | `schedule.TrialFacts` ning **sakkiz** faktida §17 oynasi haqida fakt **yo'q**; driver `t_up` ni **hisoblamaydi** ⇒ kech oyna hech qachon `censored` bo'lmaydi | `b007t001` (`25.391 + 8.0 = 33.391 > 33.0`), `b013t004` (`26.550 + 8.0 = 34.550 > 33.0`) — ikkalasi `complete` deb yozilgan |
| 2 | §4: *"Probe uzilishi > 2×P → trial `censored`"*; §14.6(4) | `driver._collect_facts`: `probe_gap_exceeded = prober_state not in ("active",)` — prober jarayonining horizon'da **tirikligi**, probe qatorlari orasidagi uzilish emas | `b007t001`: uzilish 8.391 → 8.884 s = **492 256 µs** (baseline ichida, bosimdan oldin); prober tirik ⇒ fakt `false` |
| 3 | §14.6(6): har `action` uchun mos invocation o'zgarishi | `driver._note_unit_state` chiqayotgan invocation'ning exit vaqtini **avval `ActiveExitTimestamp`** dan oladi; systemd uni faqat unit **`active` dan chiqqanda** yangilaydi | `b010t001` (`aborted_guard`): guard restart qilingan SUT'ni hali `activating` paytida o'ldirdi; ikkinchi action'ning `t_issue` i birinchisiniki bilan **teng** (23.023 s) ⇒ `check_actions` oynasi bo'sh ⇒ xato |

**Hukm (`15` §2.4, §3.3):** validator §14.6(4), §14.6(6) va §17.4(5) ni
**so'zma-so'z** bajardi; reducer `b007t001` va `b013t004` ni **mustaqil
ravishda** `censored` (`probe_gap`, `window_past_pressure`) deb
chiqardi. Pre-registration matnida **noaniqlik yo'q** — §4, §12,
§14.6(4), §17.4(2), (5) bir xil narsani aytadi. Bo'shliq
**implementatsiya shartnomasida** (`04` §8.1) — 7-band, 3-qator.
`b010t001` da §14.6(6) **mazmunan** bajarilgan (ikki action, ikki
invocation o'zgarishi); xato buzilgan record vaqtining natijasi, trial
disposition'i (`aborted_guard`) unga bog'liq emas.

**3. QAROR — V-A (`15` §5.2): driver tuzatiladi, butun pilot `p1-pilot-002` sifatida qayta o'tkaziladi.**

**(3.1) Tuzatish — faqat shu uchtasi** (driver agenti; bu amendment kod
yozmaydi):

1. **§17.4(2), (5) — oyna fakti.** Driver §17 oynasining joylashuvini
   **reducer'ning o'z funksiyalari** bilan hisoblaydi (`15` §5.2:
   `build_episodes` → `classify_window_containment`; validator ham
   shularga tayanadi) va `window_past_pressure` / `window_past_horizon`
   holatini `censored` qiladi. **Ikkinchi, mustaqil `t_up` ta'rifi
   yozilmaydi** — aks holda driver va reducer yana ajralishi mumkin.
2. **§4 — probe fakti.** `probe_gap_exceeded` **probe qatorlari orasidagi
   haqiqiy `> 2×P` uzilish**dan olinadi — reducer/validator ishlatadigan
   shartning o'zi bilan; prober jarayonining holati bu faktning
   ta'rifi emas.
3. **`t_issue` ning vaqt manbai.** Chiqayotgan invocation hech qachon
   `active` bo'lmagan bo'lsa, eskirgan `ActiveExitTimestamp` emas — shu
   invocation'ning **haqiqiy** chiqish vaqti olinadi (`15` §5.2:
   `exec_main_exit_ts` / `inactive_exit_ts`; aniq tanlov driver
   agentiniki, u testda asoslanadi). Bu **vaqt manbaining tuzatilishi**,
   §14.6(6) ning ta'rifi o'zgarmaydi.

`disposition` ning qiymati ikki yo'lda ham `censored`; driver va
reducer'ning `disposition_source` i **bir xil** bo'lishi kerak (§16.2(B)
— birlamchi to'plam `(disposition, disposition_source)` jufti bilan
aniqlanadi; `04` §8.1 qoida 3 — kelishmovchilik validator topilmasi).

**(3.2) Tekshiruv — uch qatlam.**

1. **Unit testlar** — har nuqson uchun regressiya testi (nomlangan uch
   trial'ning holati sintetik record'da).
2. **Oflayn replay** `p1-pilot-001` ning **xom record'lari** ustida
   (katalog faqat o'qiladi; chiqish run katalogidan **tashqarida**).
   **Kutilgan natija — oldindan, shu yerda yozilgan:** `b007t001`
   `complete` → `censored`; `b013t004` `complete` → `censored`;
   `b010t001` — ikki action **ikki turli** `t_issue` oladi,
   disposition `aborted_guard` **o'zgarmaydi**; **boshqa birorta ham
   trial'ning disposition'i o'zgarmaydi.** Replay hisoboti **faqat
   o'zgargan trial'lar ro'yxatini** beradi — yacheyka bo'yicha
   hisoblar, VR, downtime yoki boshqa natija **hisobot qilinmaydi**
   (0.1-band ko'rilgan narsalarni kengaytirmaslik uchun). Kutilgandan
   har qanday farq — **to'xtash va xabar**, tuzatishni moslashtirish
   emas.
3. **Smoke partiyasi** — mezoni smoke trial'laridan **OLDIN** commit
   qilinadi (`14` §10 va §12.1 dagi uslubda); smoke ma'lumoti pilot
   to'plamiga **hech qachon** kirmaydi (v1.12 4.5).

**(3.3) Qayta o'tkazish.** **`p1-pilot-002`**: seed **`20261006`**,
`schedule_digest` **`69ae399edbb20b5a0271d4b6657a3b5c1ec45b61b19a04a2bf9e0b6e8decb2dc`**
(ya'ni **aynan bir xil** 120 trial'lik jadval va tartib — tartibni
tanlash imkoni yo'q), **yangi run katalogi**; `p1-pilot-001` ning
katalogi va zaxirasi **tegilmaydi**. `run_meta.preregistration_sha256` —
**v1.13** niki.

**Rad etilgan variantlar** (`15` §5.2):

| # | variant | nega rad etildi |
|---|---|---|
| V-B | `p1-pilot-001` ni oflayn qayta tasniflash (reducer'ning derived disposition'i) | run hamon §14.6 dan o'tmaydi: o'tishi uchun validator'ni yoki `04` ning avtoritet qoidasini **ma'lumot ko'rilgandan keyin** o'zgartirish kerak (raw'ni tahrirlash §14.5(2) bo'yicha taqiqlangan); `b010t001` uchun **qo'shimcha erkinlik darajasi**. Darvoza ma'lumotdan keyin yumshatiladi |
| V-C | V-A + `p1-pilot-001` ning oflayn qayta tasnifi sezgirlik tekshiruvi sifatida | yaroqsiz run'ni **natija yonida** saqlaydi va 0.5-band taqiqlagan solishtirish yo'lini ochadi; yaroqlilik haqida qo'shadigani 3.2(2) ning replay'ida allaqachon bor |
| V-D | `p1-pilot-001` dan uch trial'ni chiqarib analiz | §14.6 — **run** darajasidagi darvoza; trial'ni tanlab olib tashlashga **hech bir muzlatilgan qoida ruxsat bermaydi** |

**4. NIMA O'ZGARMADI — to'liq ro'yxat.**

**Tuzatishlar driver'ning disposition'larini ALLAQACHON muzlatilgan
ta'riflar bilan MOS qiladi** — §4, §12, §14.6(4), (6), §17.4(1), (2), (5);
**hech bir ta'rif, chegara yoki qiymat yangidan tanlanmadi.**

**Hech bir metrika ta'rifi** (§4 VR va uning invalidator'lari, §5 FR-A /
FR-B, §6.1 `D_sd` / `D_probe` / `D_eff`, §6.2 censoring, §6.3 latency,
§6.4 recovery loop, §7 pressure o'lchovi); **hech bir statistik test**
(§10.1 Cochran–Armitage, Fisher/Barnard, Newcombe/Wilson,
Clopper–Pearson; §10.2 Kaplan–Meier / log-rank / RMST difference /
Cox-HR taqiqi / BCa; §10.4 Holm); **hech bir arm** (`A`:
`Restart=on-failure`, `RestartSec=100ms`; `no_action`: `Restart=no`);
**hech bir fault klassi** (faqat `clean_crash`, trial'ga bitta injeksiya);
**`P0`/`P1`/`P2` bandlari** (§9.3); **`disposition` ning yopiq enum'i**
va *"aynan bitta"* qoidasi (§12); §16.2 (A)/(B) va `(disposition,
disposition_source)` qoidasi; §17.4 ning ikki `disposition_source`
qiymati va besh bandi; **§11 butunlay** (kuchli shakl, fail-slow limbi
`thr = 0.20 × τ = 1.6 s`, halol power bayonoti, davom etish mezonlari,
null bo'lsa burilish); **§14 data schema** va §14.6 invariantlari
(**qayta raqamlanmadi**, darvoza **yumshatilmadi**); v1.12 ning
`host_clock_discontinuity` qoidasi va smoke/kalibratsiya chiqarilishi;
§0, §13 — **tegilmadi**; §15–§22 ning qarorlari **o'z kuchida**.

| qiymat | holat |
|---|---|
| `W_stab_pilot = 8 s`, `W_stab = 60 s` | **O'ZGARMADI** |
| `τ = 8 s` (§10.2, §11) | **O'ZGARMADI** |
| `hold_cap_s = 13 s`, `ramp_s = 5 s`, baseline 10 s, pre-flight 5 s, washout `≥ 20 s` | **O'ZGARMADI** |
| `injection_offset = 3 s` | **O'ZGARMADI** |
| `θ = 0.8` | **O'ZGARMADI** |
| `k_f = 3` (`D_f = 300 ms`) | **O'ZGARMADI** |
| `P = 100 ms`, `T_conn = 50 ms`, `T_rt = 50 ms` | **O'ZGARMADI** |
| **20 blok / 120 trial** (`3 × 2 × 20`) | **O'ZGARMADI** |
| seed `20261006`, `schedule_digest` `69ae399e…cb2dc` | **O'ZGARMADI** (5-preshart uni tekshiradi) |
| `ε = 32 MiB`, quiescence `0.05`, `T_q = 5 s`, `T_w = 15 s`, `T_w_max = 120 s` | **O'ZGARMADI** |
| guard: `sustain_rate_threshold = 0.35`, `sustain_max_seconds = 15.0`, `user_full_rate2s_max = 0.98`, `user_full_avg10_max = 85.0`, `user_some_avg10_max = 90.0`, `host_mem_available_min_kb = 1 500 000` (`revix/guard.py` `DEFAULTS`); `guard_sustain_s = 15 s` (§9.4) | **O'ZGARMADI** |
| dial: slice `MemoryMax = 2G`, `MemoryHigh = 192M`, `CPUQuota = 400%`, `TasksMax = 256`; generator `step_mb = 4`, `base_mb` 160 / 184 / 184, `target_rate` 0.0 / 0.30 / 0.60, `interval_ms = 250`, generator unit `MemoryMax = 1536M` | **O'ZGARMADI** |
| v1.12 muzlatilgan ochiq parametrlari: `WatchdogSec = 5 s`, `MemoryHigh = 192M`, `TimeoutStartSec = 10 s` (og'ish bilan), `T_trial = 41.1 s` | **O'ZGARMADI** (v1.12 1-band, og'ish e'loni ham) |
| V2 generator vaqti: start `t_h − R = 17.43 s`, `R = 2.57 s`, `hold_s + R = 15.57 s`, `pressure_off = 33.0 s` | **O'ZGARMADI** (v1.12 2-band) |
| `P2` dagi runaway yo'qotishi kutilmasi va uning bias mulohazasi | **O'ZGARMADI** (v1.12 3-band; 7-band) |

**5. TARIXIY BO'LIMLAR QAYTA YOZILMADI** (v1.11 va v1.12 ning 7-band
siyosati). **v1.12 log yozuvi** — jumladan uning 9-bandi va *"PILOTNI
HOZIR NIMA TO'XTATADI"* ro'yxati — **o'zgartirilmadi**: u
`v0.1.12-preregistration` tag'i bilan e'lon qilingan versiyaning
bayonoti; `p1-pilot-001` **o'sha** versiya ostida o'tkazilgan. Sarlavha
jadvalining v1.12 qatorlari ham tegilmadi. Buning o'rniga **normativ**
joylarga **belgilangan `v1.13` ko'rsatkichi** qo'yildi: sarlavha jadvali
va §14.6.

**6. MA'LUMOT HOLATI.**

| to'plam | holat | pilot to'plamiga |
|---|---|---|
| **`p1-pilot-001`** (120 trial, v1.12, `4cbd1c6`) | guest'da, faqat o'qish; zaxira `~/revix-runs/_backup/p1-pilot-001.tar.zst`; **YAROQSIZ** (§14.6) | **HECH QACHON** — analiz qilinmaydi, birlashtirilmaydi, **o'chirilmaydi** (0.5) |
| **`p1-pilot-002`** | **mavjud emas** | **YAGONA** analiz qilinishi mumkin bo'lgan pilot run'i (0.5) |
| 3.2(2) ning oflayn replay chiqishi | hali yo'q | **HECH QACHON** — yaroqlilik tekshiruvi |
| v1.13 tuzatishlarining smoke partiyasi | hali yo'q | **HECH QACHON** (v1.12 4.5) |
| `open-params-*`, `dose-*`, `tstart-*`, `dprobe-*`, `smoke-01`…`smoke-25` | v1.12 8-band jadvalidagidek | **HECH QACHON** (v1.12 4.5) |

**Hech qanday tadqiqot ma'lumoti analiz qilinmagan.** `p1-pilot-001`
dan ko'rilgan narsa — 0.1-banddagi ro'yxat (disposition hisoblari,
guard hodisalari, uch trial'ning xom record'lari, yaroqlilik
klassifikatsiyasi); `15` ning yaroqlilik skripti ichkarida `t_up` ni
hisoblaydi, lekin uni nomlangan uch trial'dan boshqasi uchun **hisobot
qilmaydi** va uning chiqishi commit qilinmagan (`15` §0, §7).

**7. BU AMENDMENT NIMANI YOPMAYDI.**

1. **v1.12 ning 9-bandi o'z kuchida**, bitta istisno bilan: 9.5-band
   (driver istisno yo'li) kodi `main` da — `9c98e7f` va `1a40263` `4cbd1c6`
   ning ajdodi (`ebf0e7e` merge'i; `git merge-base --is-ancestor` bilan
   tekshirildi). Qolgan bandlar (reja va o'lchangan ramp, OQ-11, `P2`
   abort stavkasi va arm'lararo farqi, bitta kernel, `timeout_start_sec`
   namunasi, watchdog cheklovi, V2 cheklovlari, smoke chiqarilishining
   mexanik majburlanmasligi, host uyqusini runtime'da aniqlash yo'qligi,
   v1.11 dan meros §18.8 / §17.7 / `window_past_pressure`) —
   **ochiq qoladi**; bu amendment ularni **qayta tekshirmadi**.
2. **Yacheyka bo'yicha chiqarilish jadvali MAJBURIY qoladi** —
   `aborted_guard` uchun (v1.12 3.3(4): har `(arm × pressure)`
   yacheykasi, guard qoidasi, injeksiyaga nisbatan vaqt) va
   `window_past_pressure` / `window_past_horizon` / `probe_gap` uchun
   (§17.4(4)). **Ahamiyati oshdi:** 3.1 ning tuzatishi bilan `A/P2`
   yacheykasida chiqarilishning **ikki manbai** (runaway abort va kech
   oyna) bir joyga to'planishi mumkin; §17.4(4): *"`P2` yacheykasida
   to'plangan yuqori daraja — o'zi NATIJA"*.
3. **`P2` dagi runaway guard kutilmasi e'lon qilinganicha qoladi**
   (v1.12 3.3, 3.4, 3.5) — bias mulohazasi va confound ogohligi bilan.
   `p1-pilot-001` ning guard hodisalari (0.1-band) bu kutilmani
   **yangilash yoki stavkani baholash uchun ishlatilmaydi**.
4. **Implementatsiya shartnomasidagi bo'shliq — QAYD ETILDI, bu yerda
   hal qilinmaydi.** `04` §8.1 (interim qoida, `driver-contract/v1.2`)
   disposition avtoritetini **driver'ga** beradi, lekin driver'dan §4 ning
   probe faktini va §17.4 ning oyna faktini **hisoblashni talab
   qilmaydi**; `_collect_facts` ning docstring'i ikkalasini reducer'ga
   qoldiradi (*"ikki yo'l bir-birini qoplaydi"*) — bu taxmin §17.4(5)
   bilan **birga yashay olmaydi**: qoplash reducer'da, rad etish esa run
   darajasida (`15` §2.4). `04` §8.2 ning mitigatsiyasi (*"bu holat amalda
   yuzaga kelmasligi lozim"*) ham bu klassni to'smadi. **`04` o'z revizya
   yozuvini talab qiladi:** uning sarlavhasi *"Implementatsiya bu faylni
   o'zgartirmaydi. Nomuvofiqlik topilsa — avval shu fayl amendment
   qilinadi"* deydi, demak driver'ning ikki fakt majburiyati `04` da
   (o'z amendment log'i bilan, oldingi hash saqlanib) driver tuzatishi
   merge qilinishidan **oldin yoki u bilan birga** yozilishi kerak. **Kim:**
   orkestrator tayinlagan agent (driver tuzatish agenti yoki alohida
   shartnoma agenti); **bu amendment `04` ni tahrirlamaydi** — u
   `agent/amend-v113` ga tegishli emas. Bu talab 8-bandda 8-preshart.
5. **`b007t001` dagi baseline uzilishining sababi o'lchanmagan** (8.19–8.88 s,
   generator hali ishlamagan; `15` §6). GIPOTEZA: host/VM darajasidagi
   qisqa to'xtash — `host_clock_discontinuity` 1 s dan qisqasini
   ko'rmaydi (v1.12 4.4). Tuzatishdan keyin bunday trial **to'g'ri**
   `censored` bo'ladi, lekin sababi ochiq.
6. **`p1-pilot-002` hali ko'rilmagan klassni ochishi mumkin** (`15` §5.2
   CHEKLOV): 120 trial'lik birinchi run smoke ko'rsatmagan uch klassni
   ochdi; ehtimolini baholab bo'lmaydi. Bunday holat — 0.6-band.

**8. `p1-pilot-002` PRESHARTLARI.** Birorta `p1-pilot-002` trial'i
o'tkazilmaydi, toki:

1. **Uch tuzatish** (3.1) unit testlari bilan **`main` ga merge
   qilingan**.
2. **Oflayn replay** (3.2(2)) oldindan yozilgan natijani berdi: faqat
   `b007t001` va `b013t004` ning disposition'i o'zgardi (`censored`),
   `b010t001` ning ikki action'i ikki turli `t_issue` oldi va
   disposition'i `aborted_guard` qoldi, **boshqa hech bir trial
   o'zgarmadi** — ya'ni **yon ta'sir yo'q**.
3. **Smoke partiyasi** o'z **oldindan commit qilingan** mezonidan
   o'tdi, merge qilingan kod bilan.
4. `p1-pilot-002` ning `run_meta.git_commit` i tuzatishlarni **ajdod
   sifatida** o'z ichiga oladi, `git_dirty: false`.
5. Tuzatilgan kod bilan `--dry-run` (seed `20261006`) **aynan**
   `69ae399edbb20b5a0271d4b6657a3b5c1ec45b61b19a04a2bf9e0b6e8decb2dc`
   ni beradi.
6. **v1.13 `main` ga merge qilingan va tag qilingan**
   (`v0.1.13-preregistration`); `run_meta.preregistration_sha256` —
   v1.13 niki.
7. **Muhit:** VirtualBox VM'i **o'chirilgan** (`VBoxHeadless` yo'q —
   `14` §3 dagi tekshiruv), va host pilot davomida **uyg'oq ushlanadi**
   (v1.12 4.4: bu faqat idle uyquni to'sadi).
8. `04` ning ikki fakt majburiyati uchun revizya yozuvi (7.4-band)
   **merge qilingan** — `04` ning o'z sarlavha qoidasidan kelib chiqadi.

**To'xtatmaydigan narsalar:** 7-banddagi ochiq cheklovlar (1, 5, 6) —
e'lon qilingan, pilotni to'xtatmaydi.

### v1.11 → v1.12 (2026-10-04)

| | |
|---|---|
| **v1.11 sha256** | `bf6a02d9de7d6383e985ae7ebdca9f7003a625300af8e4581648f202f9b66d1e` |
| **v1.11 git tag** | `v0.1.11-preregistration` |
| **Sabab** | §16.10 ning QAROR bandi **birinchi pilot trial'idan OLDIN** ikki narsani talab qiladi: muzlatilmagan parametrlar **kalibratsiya run'ining `run_id` si bilan** belgilanadi (1-qoida), va `T_trial` ning aniq qiymati **ochiq qaror bilan** muzlatiladi (4-qoida). Bu amendment o'sha talabni bajaradi. Qo'shimcha ravishda real driver bilan **birinchi smoke trial'lar** v1.11 (1.5) ning premisasini **o'lchov bilan rad etdi**, `P2` da guard yo'qotishining **ikkinchi yo'lini** ko'rsatdi, va kalibratsiya host uyqusi bilan bog'liq **yaroqlilik bo'shlig'ini** ochdi — bularning hammasi birinchi trial'dan oldin yozilishi shart |
| **Qarorni kim qabul qildi** | **Orkestrator**, loyiha egasining **2026-10-03 dagi ochiq delegatsiyasi** bo'yicha (*"choose whichever is better and continue"*). Asos fayllar: `docs/architecture/13-ochiq-parametrlar-kalibratsiyasi.md` (`main`); `docs/architecture/14-smoke-trial-natijalari.md` — **amaldagi versiyasi faqat `agent/pilot-ready` branch'ida (bu yozuv tahrir qilingan paytda `9c98e7f`), `main` ga merge qilinMAGAN**; `main` da faqat §9 gacha eski nusxa bor, va bu yerda shu branch'dagi **barqaror FAKT'lar** keltiriladi (§5, §6, §10, §11, §12); `10-pressure-dozalash.md` §2.2, §4, §5.1, §6, §7.2, §10, §12; `07-wsl-muhit-tekshiruvlari.md` §7.7. Matnni `agent/amend-v112` agenti yozdi; **har bir raqam keltirilgan faylga qarshi qayta tekshirildi** |
| **O'zgardi** | **(1)** §16.10 ning ochiq parametrlari **muzlatildi**: `watchdog_sec = 5 s`, `memory_high = 192M` (`MemoryMax=2G` bilan), `timeout_start_sec = 10 s` (**⚠️ oshkora og'ish bilan** — o'z oldindan yozilgan qoidasi taklif BERMAGAN; 1.3-band), `T_trial = 41.1 s` (ochiq qaror; formula o'zgarmadi). **(2)** Generatorning ramp oynasi **ichidagi** boshlanish nuqtasi (V2) — §9.4 ning *"ramp 5 s"* iborasining **implementatsion aniqlashtirilishi**; §9.4 ning hech bir muzlatilgan vaqti siljimadi (2-band). **(3)** `P2` da `aborted_guard` yo'qotishi **oldindan e'lon qilingan kutilma** sifatida yozildi, uning bias yo'nalishi tahlil qilindi, va `aborted_guard` ning **`(arm × pressure)` yacheyka jadvali MAJBURIY** qilindi — bu **hisobot talabi, ta'rif emas** (3-band). **(4)** Bitta yangi **yaroqlilik** qoidasi `host_clock_discontinuity` (faqat run'ni **rad etadi**) va smoke/kalibratsiya ma'lumotining pilot to'plamidan **chiqarilish** qoidasi (4-band). **(5)** §21.7 ning ⛔ gate'i **YOPILDI — faqat V2 generator vaqti bilan ishlaydigan driver uchun** (5-band) |
| **O'zgarMADI** | **hech bir metrika ta'rifi, statistik test, arm, fault klassi, probe parametri, VR/FR ta'rifi, `disposition` enum'i, falsifikatsiya mezoni**, `W_stab_pilot`, `τ`, `injection_offset`, `θ`, `k_f`, `P`, `T_conn`, `T_rt`, blok va trial soni, **guard chegaralari** va **dial**. To'liq ro'yxat — 6-bandda |
| **Yig'ilgan ma'lumot** | **P1 trial'i ma'lumoti — YO'Q:** birorta pilot trial'i o'tkazilmagan, birlamchi endpoint ko'rilmagan. **LEKIN** kalibratsiya (`open-params-*`) va smoke (`smoke-*`) ma'lumotlari **MAVJUD va KO'RILGAN** — 0-band; ular pilot ma'lumot to'plamiga **hech qachon kirmaydi** — 4.5-band; to'liq holat — 8-band |

**0. 🔴 OSHKORA E'LON — bu qarorlar kalibratsiya VA smoke ma'lumoti ko'rilgandan KEYIN qabul qilindi.**

§17.6 va §18.7 o'z qarorlarini *"hech qanday ma'lumot mavjud bo'lmaganda"*
qabul qilingan deb himoya qilgan; v1.11 ning 0-bandi bu kafolat v1.11 ga
**o'tmasligini** e'lon qilgan. **Xuddi shu e'lon v1.12 uchun ham — va
ayniqsa 1.3-band (`timeout_start_sec`), 2-band (V2) va 3-band (`P2`
yo'qotishi) uchun.** *"Ko'r tanlangan"* degan har qanday da'vo faqat
quyidagi jadvalda ko'rsatilgan qamrovda o'qiladi:

| qaror | qoida ma'lumotdan OLDIN yozilganmi? | qiymat qoidadan mexanik chiqdimi? | *"ko'r"* da'vosining qamrovi |
|---|---|---|---|
| `watchdog_sec = 5 s` (1.1) | **HA** — `13` §0, commit `812c989` (2026-10-03 22:34:48 +0500); o'lchov runner'i `1d344b2` (22:42:16 +0500) uning avlodi, qulf `17:42:32Z` (= 22:42:32 +0500) da olindi | **HA** — `max(5, ceil(0.70)) = 5 s` | faqat **qoida va uning chiqishi** ko'r; qoidani **muzlatish** qarori ma'lumot ko'rilgandan keyin |
| `memory_high = 192M` (1.2) | **HA** — `13` §0.7 ning qayta-ishlab-chiqarish mezoni, o'sha commit | **HA** — mezon bajarildi; qiymat ma'lumotdan oldingi default | xuddi shunday |
| `T_trial = 41.1 s` (1.4) | formula `driver-contract/v1.2` — ma'lumotdan oldin; tekshiruvlar `13` §0.7 da | **HA** — formula, o'lchov emas | raqam ma'lumotdan **tanlanmagan** |
| `timeout_start_sec = 10 s` (1.3) | qoida bor edi — **u taklif BERMADI** | **YO'Q — og'ish** | **YO'Q** |
| V2 (2) | V2 ning **muvaffaqiyat mezoni** V2 trial'laridan oldin yozildi (`14` §10, commit `8ebf130`), lekin **V2 ning o'zi** V0 ning 2/2 trip'i ko'rilgandan keyin tanlandi, va mezonning **(a) qismi BAJARILMADI** | — | **YO'Q** |
| `P2` yo'qotishi kutilmasi (3) | 1/6 va 2/7 ko'rilgandan keyin | — | **YO'Q** — lekin **har qanday P1 ma'lumotidan OLDIN** |
| `host_clock_discontinuity` chegarasi `1.0 s` (4) | 72 402 juft ko'rilgandan keyin | — | YO'Q; qoida faqat **rad etadi** (4.3) |
| §21.7 gate'ining yopilishi (5) | o'lchovdan keyin | — | YO'Q |

- **Nima bu xavfni CHEKLAYDI:** **(i)** hech qanday P1 trial'i
  o'tkazilmagan — `P(VR)`, `Δ`, CI va p-qiymat **ko'rilmagan**; ko'rilgan
  narsa mashina va kalibratsiya kattaliklari (watchdog oraliqlari,
  `t_start`, guard tezligi, generator vaqtlari); **(ii)** bu amendment
  **hech bir ta'rifga, testga yoki falsifikatsiya mezoniga** tegmaydi — u
  vaqt implementatsiyasi, ikki driver default'ining muzlatilishi,
  yaroqlilik qoidasi va hisobot talabini o'zgartiradi; **(iii)** 3-band
  `P2` yo'qotishining **bias yo'nalishini** P1 ma'lumotidan oldin yozadi.
- **Nima bu xavfni CHEKLAMAYDI:** V2 va 1.3-band **ularning oqibati
  bilinib turib** tanlandi. V2 aynan **`P2` yacheykalarini bo'sh qoldiradigan**
  sustain trip'larini (2/2) yo'q qilgani uchun saqlandi — ya'ni
  **o'tkaziluvchanlik (feasibility) ma'lumotiga qarab tanlov**. 1.3-band
  esa o'z qoidasi taklif bermagan joyda default'ni ushlab qoladi. O'quvchi
  buni **ko'rishi shart**.

> **Maqolada shunday yoziladi:** *"`WatchdogSec`, `MemoryHigh` va
> `T_trial` oldindan yozilgan qoida bo'yicha muzlatilgan; `TimeoutStartSec`
> qoida taklif bermagani uchun ma'lumotdan oldingi default'da **og'ish
> sifatida** saqlangan; generatorning boshlanish nuqtasi va `P2` dagi
> kutilgan guard yo'qotishi **kalibratsiya va smoke ma'lumoti ko'rilgandan
> keyin, lekin birinchi pilot trial'idan OLDIN** belgilangan."*

**1. §16.10 NING OCHIQ PARAMETRLARI MUZLATILDI.**

**(1.0) Qaysi run'lar, qaysi qoida.** O'lchov `experiment/open-params`
branch'ida bajarildi (§16.10(1) `experiment/pressure-cal` ni nomlaydi —
**nom farqi** `13` §8(5) da qayd etilgan; qoidaning mazmuni —
kalibratsiya run'ining `run_id` si — shu yerda bajariladi). Qoida — `13`
§0 (commit `812c989`, ma'lumotdan oldin); og'ishlar `13` §0A va §0B —
har biri **keyingi run'dan oldin** commit qilingan (`8c3607c`, `c45de9f`).
`13` §1 bo'yicha:

| `run_id` | commit | nima | nimaga ishlatildi |
|---|---|---|---|
| `open-params-cal-01` | `1d344b2` | A (watchdog) + B (boshlanmadi — host uyqusi, `13` §0A) | watchdog: yaroqli A epizodlari `P0` 20, `P1` 21, `P2` 21 |
| `open-params-cal-02` | `8c3607c` | A `P0:4,P1:3,P2:3` + B | watchdog: A 4 / 3 / 3; `t_start`: B (guard trip `B-P2-05`, §0B) |
| `open-params-cal-03` | `c45de9f` | faqat B | `t_start`: B (guard trip `B-P2-02`); `M_start = 0.9614 s` shu run'dan |
| `open-params-smoke-01` | `1d344b2` | protokol sinovi | **hisobga KIRMAYDI**; uning `1.7030 s` i 1.3-band jadvalida **oshkoralik uchun** keltiriladi |

Chiqarilgan epizodlar (va **faqat shular**, `13` §1): `cal-01:A-P0-21`,
`cal-01:A-P2-22` (soat sakrashi), `cal-02:B-P2-05`, `cal-03:B-P2-02`
(guard trip, `13` §0.5(4)).

**(1.1) `watchdog_sec = 5 s` — qoida bo'yicha (`13` §2.2, §6.1).**

```
g     = WatchdogTimestampMonotonic ning ketma-ket ikki turli qiymati orasidagi oraliq
delta = g - W/2 = g - 2.5 s           (miss sharti: delta > W/2)
72 yaroqli epizod (P0 24, P1 24, P2 24; cal-01 + cal-02 ning A qismi)
1008 ping oralig'i (336 x 3) + 72 arm -> birinchi ping oralig'i
max g = 2.6170 s (P2);   M_wd = max delta = 0.1170 s (P2)
Result=watchdog: 0/72;   NRestarts: 0;   poller interval max 0.0699 s (< 1.0 s)
L_wd  = 2 x F x M_wd = 2 x 3 x 0.1170 = 0.70 s  ->  ceil = 1 s
U_wd  = 18.0 - M_start = 18.0 - 0.9614 = 17.04 s       (1 <= 17.04, ziddiyat yo'q)
qiymat = max(5, 1) = 5 s
zaxira: (W/2) / M_wd = 2.5 / 0.1170 = 21.4x   (oldindan qo'yilgan talab F = 3)
```

`cal-03` A qismini o'z ichiga olmaydi; u `U_wd` dagi `M_start` ni beradi.
`F = 3` `10` §10.2 (OQ-8) ning *"kamida 2–3 karrasi"* talabining yuqori
cheti (`13` §0.3). G2 (watchdog `READY=1` bilan birga qurollanadi)
tasdiqlandi (`13` §2.1).

> **§16.10(5) bayonoti:** *"§9.2 mexanizm **(iv)** (watchdog miss) ning
> mavjudligi `WatchdogSec` ning muzlatilgan qiymati — **5 s** — bilan
> belgilangan."* Kalibrlangan dozada miss uchun SUT ish tsikli (ping
> qabul kechikishi bilan birga) **≥ 2.5 s** ushlanishi kerak — o'lchangan
> eng yomon holatning **21.4×** i. **Kalibrlangan dozada bosimning o'zi
> (iv) ni YARATMADI (0/72).** Shuning uchun pilotda (iv) ning **yo'qligi**
> bu mexanizm haqida **ma'lumot bermaydi**, uning **paydo bo'lishi** esa
> pilot sharoiti kalibratsiyadan `F×` dan ortiq chetga chiqqanini bildiradi.

**CHEKLOV (`13` §9):** watchdog oraliqlari **bosimdan oldin** ishga
tushgan SUT da o'lchandi — pilotdagi arm `A` restart'i esa **bosim
ichida**; bystander va prober kalibratsiyada lab'da **yo'q** edi; G1
(`δ` davrga bog'liq emas) tekshirilmadi; bitta kernel.

**(1.2) `memory_high = 192M` (`MemoryMax=2G` bilan) — §16.10(6) bajarildi.**
§16.10(6): *"`MemoryHigh` dial `MemoryMax=2G` topologiyasida **qayta
o'lchanadi**; 1G ostida o'lchangan 192 M ko'chirilmaydi."* `10` §2.2
(`dose-01-dial`, `MemoryMax=2G` ostida): `step_mb=16 → base 160` nol doza
(`memory.current` max 185.3 MiB — `08` §3.4 bilan aynan bir xil),
`step_mb=4 → base 184` erishilgan p50 **0.3344**; `10` §2.6 dial'ni 2G
ostida qotirgan. **Ya'ni 192M 2G ostida qayta o'lchangan, ko'chirilmagan.**
Qayta-ishlab-chiqarish tekshiruvi (`13` §4, mezon `13` §0.7, `≥ 90%`):
`P0` **30/30** epizodda `memory.events high` va lab `full total=` deltasi
**0**; `P1` **30/30**, `P2` **29/29** da ikkalasi `> 0`. Kalibratsiya
run'lari: `dose-01-dial`, `dose-02-bands`, `dose-03-p2sweep` (xom
ma'lumoti `datasets/` da **yo'q**, guest'da `~/revix-runs/dose-*`);
qayta-ishlab-chiqarish: `open-params-cal-01/-02/-03`.

> **⚠️ CHEKLOV — OQ-11 ochiq qoladi:** bu `192M` ning **optimal** ekanini
> ko'rsatmaydi — **boshqa hech bir `MemoryHigh` qiymati o'lchanmagan**
> (`10` §11 OQ-11), va ishchi `base_mb` oynasi **tor** (faqat 184,
> `10` §3.6). §16.10(6) optimallikni talab qilmaydi; muzlatilgan narsa —
> **o'lchangan dial**, eng yaxshi dial emas.

**(1.3) `timeout_start_sec = 10 s` — ⚠️ OSHKORA OG'ISH: o'z qoidasi taklif BERMAGAN.**

**Birinchi navbatda:** `13` §0.5(3) har bandda **≥ 48** bosim ostidagi
(PRESSURED) start'ni talab qiladi. Olingani **24 / 24 / 20** (`13` §3.1).
**Qoida o'z shartiga ko'ra TAKLIF BERMADI** (`13` §6.2: *"taklif
BERILMAYDI"*), va bu band buni **yashirmaydi**.

**Nega namuna to'lmadi:** `cal-01` ning B qismi host uyqusi va guest init
restart'i tufayli **umuman boshlanmadi** (`13` §0A); `cal-02` va `cal-03`
ikkalasi ham kalibrlangan `P2` da **bosim ostidagi SUT start'i paytida**
guard'ning runaway chegarasini urdi (`B-P2-05`: `rate 0.9802`; `B-P2-02`:
`rate 0.9889`; `limit 0.98`) va controller **oldindan yozilgandek**
FAIL-CLOSED to'xtadi; `13` §0B oldindan yozgan: *"`cal-03` ham trip bilan
to'xtasa, qo'shimcha run qilinmaydi"*.

**Orkestratorning qarori:** ma'lumotdan **oldingi** driver default'i —
**10 s** — saqlanadi va muzlatiladi. U tayangan o'lchovlar:

| manba | run | band | eng katta o'lchangan `t_start` | `10 s / max` |
|---|---|---|---|---|
| `13` §3.1 (hisobga kirgan, `M_start`) | `open-params-cal-03` (B) | `P1` | **0.9614 s** | **10.40×** |
| `13` §3.1 (hisobga **kirmaydi**) | `open-params-smoke-01` (B) | `P2` | **1.7030 s** | **5.87×** |
| `10` §6.2 / §10.1 | `10` ning `tstart-*` run'lari | `P1` | **1.4807 s** | **6.75×** |

`Result=timeout`: kalibratsiyada **0** (68 qualifying + 72 bosimsiz start,
`13` §6.2), `10` da **0/78**.

> **Bu QOIDANING bajarilishi EMAS — bu hujjatlashtirilgan OG'ISH.** U
> ikki sababga tayanadi: **(a)** o'lchangan **har bir** dum 10 s dan
> uzoq pastda (eng yomoni `5.87×`); **(b)** qiymat birinchi trial'dan
> oldin muzlatilishi **shart** (§16.10(1), (4)) va P1 ma'lumotidan keyin
> uni o'zgartirish **taqiqlangan** (§16.10(3)) — namunani to'ldirish esa
> aynan guard'ni urgan `P2` B epizodlarini (2/7) qaytadan talab qilardi,
> `13` §0B esa buni oldindan taqiqlagan. `13` §6.2 ning *"ma'lumot
> uchun"* arifmetikasi (har uch dum bilan qoida `max(10, 3 | 6 | 5) = 10 s`
> berardi) **dalil sifatida ishlatilmaydi**: u namuna sharti bajarilmagan
> arifmetika.

> **§16.10(5) bayonoti:** *"§9.2 mexanizm **(i)** (`TimeoutStartSec`
> oshib ketdi) ning mavjudligi `TimeoutStartSec` ning muzlatilgan
> qiymati — **10 s** — bilan belgilangan."* (i) uchun start o'lchangan
> eng sekin start'dan kamida **5.87×** (hisobga kirgan kalibratsiyaga
> nisbatan **10.40×**) sekin bo'lishi kerak.

> **O'quvchi nima xulosa qilishi kerak:** `Result=timeout` pilotda
> **bosimning o'zidan kutilmaydi.** Uning **yo'qligi** mexanizm (i)
> haqida ham, arm `A` (systemd restart) haqida ham **topilma sifatida
> hisobot qilinMAYDI** — u parametr tanlovi bilan belgilangan. §11(c)
> mexanizm (i) ga tayansa, yuqoridagi bayonot, muzlatilgan qiymat **va
> shu og'ish** hisobotda **majburiy**.

(v1.11 (4.5) ning kuzatuvi — §17.3 (b) chegarasi `t_start > ~9.9 s` 10 s
dan **biroz pastda** — o'z kuchida qoladi; xulosa chiqarilmaydi.)

**(1.4) `T_trial = 41.1 s` — §16.10(4) talab qilgan OCHIQ QAROR.**
Formula **o'zgarmadi**: `T_trial = t_pressure_off + w_stab_s + P =
33.0 + 8.0 + 0.1 = 41.1 s` (`driver-contract/v1.2`; qiymat `hold_cap_s =
13 s` dan chiqadi, v1.11 4-band). `13` §5 ning tekshiruvlari (oldindan
`13` §0.7 da yozilgan):

```
(a) eng sekin start + verifikatsiya oynasi:
    t_inject + RestartSec + M_start + W_stab_pilot + P = 23.0 + 0.1 + 0.9614 + 8.0 + 0.1 = 32.16 s <= 41.1
    (open-params-smoke-01 ning 1.7030 s i bilan: 32.90 s <= 41.1)
(b) eng uzun o'lchangan tiklanish (10 §7.2, P2, D_probe proxy max 2.2 s):
    23.0 + 2.2 + 8.0 + 0.1 = 33.3 s <= 41.1
(c) 72 A epizodida pressure_stop dan keyin lab full total= BIRORTA marta ham o'smagan;
    pressure'dan keyingi max delta <= 0.0011 s  ->  [33.0, 41.1] s ga bosim qoldig'i sizmaydi
```

Chegaralar: `41.1 ≥ t_verify_end_earliest = 31` ✓ (v1.11 4.2), `41.1 ≤
total_s = 53` ✓, va §16.10 ning 6-qatori (`τ ≤ T_trial`) **endi
tekshiriladi**: `8 ≤ 41.1` ✓. V2 (2-band) `T_trial` ga **tegmaydi** —
`t_pressure_off` o'zgarmadi. **Raqam ma'lumotdan tanlanmagan**; uni
**muzlatish qarori** ma'lumot ko'rilgandan keyin (0-band).

**(1.5) §16.10 jadvalining qolgan qatorlari.** 4-qator (`P2` nishoni
0.70) — v1.11 dan **oldin** kodda 0.60 ga tuzatilgan (v1.11 log,
9.6-band), bu amendment'ning qarori emas. §16.10(2) — **bir qiymat barcha
arm va daraja uchun** — bajariladi: yuqoridagi to'rt qiymatning hammasi
arm/band'ga bog'liq emas. §16.10(1) ning ikkinchi yarmi — qiymatlarni
`run_id` lari bilan **`run_meta.open_parameters` ga yozish** — **kod
ishi, va u hali bajarilmagan**: `main` da ham, `agent/pilot-ready` da ham
uchala yozuv hamon `calibration_required: true` (9-band, pilot preshart 3).
`run_meta` olib yurishi kerak bo'lgan mazmun: har parametr uchun qiymat,
kalibratsiya `run_id` lari (yuqoridagi jadval), §16.10(5) bayonoti, va
`timeout_start_sec` uchun **shu og'ishga havola**.

**2. GENERATOR VAQTI (V2) — §9.4 ning "ramp 5 s" iborasining IMPLEMENTATSION aniqlashtirilishi.**

**(2.1) FAKT — V0 (`14` §4, §5; `P2` n = 2).** Driver generatorni
rejadagi ramp boshidan (15.0 s) **`ramp_s + hold_s = 18 s`** ishlatgan.
Generatorning **o'z** ramp'i 17.646 s da tugagan (2.57 s), PI fazasi esa
hold'dan (20.0 s) **oldin** boshlangan. Guard kuzatadigan `user` 2 s
tezligi `≥ 0.35` ga **18.544 / 18.647 s** da chiqqan — hold'dan
**1.35–1.46 s OLDIN** — va guard'ning sustain taymeri
(`sustain_rate_threshold = 0.35`, `sustain_max_seconds = 15.0`,
`revix/guard.py` `DEFAULTS`) **15 s dan keyin** tugagan: **2/2 `P2`
trial `aborted_guard`**, `sustained_s` **15.10 / 15.00**, trip
33.634 / 33.553 s da (generator 33.127 / 33.120 s da to'xtagandan keyin,
2 s oynaning qoldig'ida). Eng uzun uzluksiz `≥ 0.35` oraliq **15.4 /
14.9 s**. `P1` da 2/2 trip yo'q (oraliq 2.7 / 2.3 s).

**(2.2) Bu v1.11 (1.5) NING PREMISASIGA ZID.** v1.11 (1.5) guard
qayta kalibratsiyasini shunday rad etgan edi: *"`ramp_above_threshold_s
= 0` bo'lgani uchun sustain taymeri faqat hold ichida boshlanishi
mumkin"*. **Pilot timeline'ida bu yolg'on bo'lib chiqdi.** Sabab:
`ramp_above_threshold_s = 0.000` (`10` §4.1, 29/29) **generatorning o'z
ramp oynasida** (`pressure_start` → oxirgi `pressure_ramp`, 2.55–2.61 s)
o'lchangan; §9.4 ning invarianti esa **timeline ramp'iga** (5 s)
tegishli. Rejadagi 5 s ramp oynasida `[15.0, 20.0] s` o'lchangan qiymat
**2.0–2.1 s** (`14` §4.3) ⇒ `13 + 2.1 = 15.1 > 15`. v1.11 log yozuvi
**qayta yozilmaydi** (7-band); tuzatish — shu band.

**(2.3) QAROR — V2.** Generator **`t_h − R = 20.0 − 2.57 = 17.43 s`** da
boshlanadi, **`hold_s + R = 15.57 s`** ishlaydi, va **`t_pressure_off =
33.0 s`** da — avvalgidek — chiqadi. `R = 2.57 s` — generatorning **o'z
o'lchangan ramp'i** (`14` §5.1: `17.646 − 15.076 = 2.570 s`,
`17.646 − 15.078 = 2.568 s`), **nomli konstanta, sozlanmaydi**, barcha arm
va band uchun **bir xil** (§16.10(2) ruhida). Kod: `11fca44`
(`agent/pilot-ready`, **merge qilinMAGAN**); `run_meta.generator_window`
rejani (`planned_pressure_on_s = 18`) ham, amaldagi oynani (`15.57 s`)
ham yozadi.

**(2.4) Nega bu implementatsion aniqlashtirish, ta'rif o'zgarishi emas.**
§9.4 ning **muzlatilgan vaqtlari — hammasi o'zgarmadi**:

| kattalik | qiymat (`trial_begin` dan) | V2 dan keyin |
|---|---|---|
| pre-flight | 5 s | o'zgarmadi |
| `R_ref` baseline | 10 s (5.0–15.0) | o'zgarmadi |
| ramp | 5 s (15.0–20.0) | o'zgarmadi |
| hold (`hold_cap_s`) | 13 s (20.0–33.0) | o'zgarmadi |
| injeksiya | `t_h + 3 = 23.0 s` | o'zgarmadi |
| pressure off | `t_h + 13 = 33.0 s` | o'zgarmadi |
| `T_trial` | 41.1 s | o'zgarmadi |
| washout | `≥ 20 s` | o'zgarmadi |
| **generatorning ramp oynasi ichidagi boshlanishi** | 15.0 s | **17.43 s** |

O'qish: *"ramp 5 s"* — bosim **ko'tariladigan** 5 s li oyna; generatorning
o'z ramp'i uning **oxirgi 2.57 s** ini egallaydi, birinchi ~2.43 s da
generator ishlamaydi (bu `R_ref` baseline'iga kirmaydi — u 15.0 s da
tugaydi). **Oqibati:** `run_meta.timeline.pressure_on_s = 18` (reja)
endi generatorning amaldagi ishlash vaqtining (**≈ 15.57 s**; o'lchangan
`elapsed` 15.568–15.697 s) **yuqori chegarasi**, uning o'zi emas.

**Narxi, ochiq:** injeksiya paytida PI fazasining "yoshi" o'zgaradi.
V0 da `≥ 0.35` injeksiyadan ~4.4 s oldin boshlangan; V2 da 20.95–21.05 s
da, ya'ni injeksiyadan ~2 s oldin, generatorning o'z ramp'i tugaganidan
~2.9 s keyin. (TALQIN: bu kalibratsiyaning B protokoli bilan bir xil
ofset — `13` §0.8 da start'lar generator ramp'idan **3 s keyin**
boshlanadi.) Injeksiya lahzasidagi **erishilgan** doza §9.4 bo'yicha
**o'lchanadi** (*"analiz ERISHILGAN pressure'dan foydalanadi"*), taxmin
qilinmaydi.

**(2.5) FAKT — V2 natijasi (`14` §11; `P2`, n = 6: 3 × `A`, 3 × `no_action`).**

| kattalik | 6 trial (min–max) | reja |
|---|---|---|
| generator `pressure_start` | 17.494–17.547 s | 17.43 s |
| generatorning o'z ramp'i tugadi | 20.056–20.115 s | 20.0 s |
| `user` `≥ 0.35` birinchi marta | 20.946–21.051 s | hold ichida |
| `ramp_above_threshold_s`, **rejadagi** ramp oynasi `[15, 20] s` | **0.0 (6/6)** | 0.0 |
| eng uzun uzluksiz `≥ 0.35` oraliq | **5.0–13.0 s** (`smoke-13` kill bilan 2.1 s da kesilgan) | `< 15 s` |
| `sustained_pressure` trip'i | **0/6** (V0 da 2/2) | 0 |
| generator chiqishi (5 tugagan trial) | **33.075–33.245 s** (`overrun` 0.000–0.127 s) | 33.0 s |
| `user_full_rate2s_runaway` trip'i | **1/6** (`smoke-13`) | — (3-band) |

**V2 ning OLDINDAN yozilgan mezoni** (`14` §10, `8ebf130`, V2 kodi va
trial'laridan oldin): (a) *"birorta ham `P2` trial'i `aborted_guard`
bilan tugamaydi"* — **BAJARILMADI** (`smoke-13`, runaway); (b) eng uzun
oraliq `≤ 14 s` — **6/6 bajarildi**. To'xtash qoidasi qo'llandi: `P1`/`P0`
regressiya trial'lari (`smoke-14`…`smoke-17`) **bajarilmadi** (`14` §11.3).
**Orkestrator qarori** (`14` §11.7): V2 **saqlanadi**, dial va guard'ga
**tegilmaydi**; (a) ning muvaffaqiyatsizligi **boshqa mexanizm**
(runaway) — u V2 dan oldin kalibratsiyada ham ishlagan. **Ya'ni V2 o'z
mezonining so'zma-so'z matni bajarilmagan holda saqlandi** — 0-band.

Zaxira tor: `smoke-11` ning **13.0 s** i 15 s dan atigi **2.0 s** past
(`14` §11.5). **n = 6.**

**(2.6) Rad etilgan variantlar (`14` §6).**

| # | variant | nega rad etildi |
|---|---|---|
| V0 | hech narsa o'zgarmaydi | `P2` 2/2 `aborted_guard`; `P2` yacheykalari bo'sh, `3 × 2` dizayn amalda `P0/P1` ga qisqaradi; §9.4 invariant 2 o'lchov bilan buzilgan holda qoladi |
| V1 | generator umri `= hold_s` (13 s), ramp boshidan | generator ~28.1 s da to'xtaydi — `W_stab_pilot` oynasining (23–31 s) bir qismi **bosimsiz** (§17.4); `pressure_off` ni 28 s ga surish aynan §9.4 rad etgan `hold ≤ 8 s` o'qishi (`3 + 8 = 11 > 8`) — **frozen matnga zid** |
| V3 | `P2` dozasini pasaytirish | §9.3 ning `P2` bandi (60–80%) 0.35 dan yuqori; dial muzlatilgan (1.2-band, `10` §2.6), ishchi oyna tor; qayta kalibratsiya kerak va 15 s chegarasi baribir PI tebranishiga bog'liq qoladi |
| **V4** | guard chegaralarini (`0.35 / 15 s`) o'zgartirish | **CHIQARIB TASHLANDI** — guard pilotning **yagona** containment mexanizmi (§15.3; v1.11 1.7: oomd yo'q); xavfsizlik mexanizmi natijaga moslab sozlanmaydi |

**(2.7) CHEKLOV.** n = 6, faqat `P2`; `R` ikki trial'dan va `P2` dial'ida
o'lchangan (`P0` da generatorning o'z ramp'i 2.245–2.264 s — u hold'dan
~0.3 s oldin tugaydi, `P0` da stall yo'q); **V2 real driver bilan `P1`/`P0`
da hech qachon ishlamagan**; guard tezligi `psi.csv` dan qayta qurilgan;
`P2` PI nazoratining yo'qolishi (`14` §5.2(b)) hal qilinmadi; validator
invariantni hamon **reja** ustida tekshiradi (v1.11 3-band CHEKLOV 2 —
9.1-band).

**3. `P2` DA KUTILGAN YO'QOTISH — BOSHQA GUARD QOIDASI BO'YICHA. OLDINDAN E'LON, P1 MA'LUMOTIDAN OLDIN.**

**(3.1) FAKT.** Guard'ning **runaway** qoidasi
(`user_full_rate2s_max = 0.98`) uch marta ishladi:

| run | epizod / trial | `rate` | qachon | kontekst |
|---|---|---|---|---|
| `open-params-cal-02` | `B-P2-05` | **0.9802** | bosim ostidagi SUT start'lari paytida | kalibratsiya, driver yo'q, V2 yo'q |
| `open-params-cal-03` | `B-P2-02` | **0.9889** | bosim ostidagi SUT start'lari paytida | xuddi shunday |
| `smoke-13-noaction-P2` | V2 trial | **0.9817** | `trial_begin` dan 22.526 s — **injeksiyadan OLDIN**, restart'siz | real driver, V2 |

Kalibratsiyada: B-`P2` (bosim ostida ketma-ket start) **2/7** epizodda
trip; A-`P2` (bosim ostida start yo'q) **0/24**; B-`P0`/`P1` **0/12**
(`13` §6.3). V2 smoke'da **1/6**. V0 smoke'da (`P2`, n = 2) max tezlik
0.96 / 0.93 — runaway yo'q.

**(3.2) V2 bilan bog'liqligi — ANIQ ifoda.** Runaway mexanizmi V2 dan
**mustaqil mavjud**: u kalibratsiyada, driver ham, V2 ham bo'lmagan
holda, ikki marta ishlagan. Lekin **V2 uning chastotasini o'zgartirdimi —
o'lchanmagan** (`14` §11.5: V2 dan oldin faqat 2 trial). Shuning uchun
*"V2 sabab emas"* deb emas, **"V2 bu mexanizmni yaratmagan; uning
chastotasiga ta'siri noma'lum"** deb yoziladi.

**(3.3) MUZLATILGAN KUTILMA (birorta pilot ma'lumotidan OLDIN).**

1. **Ba'zi `P2` trial'lari `aborted_guard` bilan tugaydi.**
2. Stavka **1/6 dan 2/7 gacha tartibda** — **bu O'LCHANGAN STAVKA EMAS:**
   n = 6–7, ikki xil protokol (real driver trial'i vs epizodda 4 ta
   ketma-ket bosim ostidagi start), va Clopper–Pearson 95% intervallari `1/6 → [0.004, 0.641]`,
   `2/7 → [0.037, 0.710]` — ya'ni amalda **har qanday** stavka bilan mos.
   Bu raqam hech qanday chegara yoki qaror uchun **ishlatilmaydi**.
3. `aborted_guard` — §12 ning **yopiq enum** qiymati; u birlamchi
   analizdan **chiqariladi** (§12; §16.2(B) — birlamchi to'plam
   `(disposition, disposition_source)` bilan aniqlanadi va `aborted_guard`
   unga kirmaydi). **Yangi qoida kerak emas, hech bir qoida o'zgarmadi.**
4. Chiqarilish darajasi **natija sifatida** beriladi (§12: *"Yuqori
   eksklyuziya darajasi o'zi natija — yashirilmaydi"*;
   `04-driver-va-analiz-shartnomasi.md` §2.3, 5-majburiyat).
   **v1.12 qo'shadi (hisobot talabi, ta'rif EMAS):** `aborted_guard`
   soni va ulushi **har `(arm × pressure)` yacheykasi bo'yicha ALOHIDA**,
   **guard qoidasi** bo'yicha (`sustained_pressure` / runaway / boshqa)
   va **injeksiyaga nisbatan vaqti** bo'yicha (injeksiyadan oldin /
   keyin) — **MAJBURIY jadval** (§17.4(4) ning `window_past_pressure`
   uchun qo'ygan yacheyka qoidasining aynan shu shakli).

**(3.4) BIAS YO'NALISHI — mulohaza, va uning chegarasi.**

- **Mexanizm.** Runaway qoidasi **eng yuqori oniy** 2 s stall'da
  (`≥ 0.98`) ishlaydi. Demak u qo'zg'atgan trial'lar — konstruksiya
  bo'yicha — `P2` yacheykasining **eng og'ir stall epizodli** trial'lari;
  ularning chiqarilishi `P2` ning **erishilgan pressure taqsimotining
  yuqori dumini kesadi**.
- **H1 to'g'ri bo'lsa.** §9.2 ning to'rt mexanizmi ham og'irlikka bog'liq
  (start kechikishi, OOM, brownout, watchdog), va `10` §6.5 ning
  CHEKLOV'i *"`t_start` faqat to'yinishga yaqin dozada portlaydi"* degan
  (TALQIN, o'lchanmagan) chiziqsiz javobni ko'rsatadi. Agar effekt
  og'irlik bilan monoton o'ssa, chiqarilgan trial'lar — **VR
  muvaffaqiyatsizligi eng ehtimoliy** va tiklanishi **eng uzun** bo'lgan
  trial'lar. Ularni olib tashlash `P(VR|P2)` ni **oshiradi** va
  `RMST(P2)` ni **kamaytiradi** ⇒ `P0`–`P2` kontrastini **null tomonga
  susaytiradi** ⇒ **H1 GA QARSHI** (§11 ning kuchli shaklining *"yolg'on"*
  hukmi va *"fail-slow qo'llab-quvvatlanmaydi"* hukmi tomon). Agar effekt
  faqat to'yinish yaqinida bo'lsa, kesilgan dum **aynan effekt
  yashaydigan** soha bo'lishi mumkin — susayish **kuchli** bo'ladi.
- **H1 yolg'on bo'lsa** (effekt yo'q), og'irlik bo'yicha chiqarish nuqta
  bahosiga **bias kiritmaydi**.
- **Qarama-qarshi ta'sir — aniqlik.** Kamroq `P2` trial'i ⇒ kengroq CI.
  §11 ning kuchli shakli *"yolg'on"* uchun Newcombe yuqori chegarasi
  `< 0.15`, fail-slow limbi uchun `CI95_upper[Δ] < 1.6 s` talab qiladi;
  kengroq CI **ikkala "yolg'on/qo'llab-quvvatlanmaydi" hukmini ham
  QIYINLASHTIRADI**. Ya'ni nuqta bahosi H1 ga qarshi og'adi, aniqlik esa
  noto'g'ri inkordan himoya qiladi; **hukmga sof ta'sir oldindan
  aniqlanmaydi.**
- **Bu mulohazaning tayanchi:** og'irlik–effekt monotonligi — **H1 ning
  o'z premisasi, o'lchanmagan.** Shuning uchun yo'nalish **shartli
  mulohaza**, o'rnatilgan fakt emas.
- **Injeksiyagacha va keyingi abort'lar farq qiladi.** `smoke-13` kabi
  **injeksiyadan oldingi** abort natija paydo bo'lishidan oldin trial'ni
  olib tashlaydi — tanlov **faqat pressure og'irligi** (davolanishdan
  oldingi kovariata) bo'yicha. Arm `A` da **restart paytidagi** abort
  (kalibratsiyaning 2/7 i shu turdagi) esa H1 aynan o'lchamoqchi bo'lgan
  jarayon — **bosim ostidagi restart** — eng og'ir bo'lgan trial'larni
  olib tashlaydi: bu **mexanizm bo'yicha tanlov**, va u ham H1 ga qarshi
  og'adi. Shu sababli injeksiyaga nisbatan vaqt jadvalda **majburiy**.

**(3.5) NOMA'LUM — arm'lar orasidagi farq, va u confound.** Abort
ehtimoli arm `A` va `no_action` orasida farq qiladimi — **o'lchanmagan;
namuna buni ayta olmaydi.** **GIPOTEZA (o'lchanmagan):** kalibratsiya
bosim ostidagi start'ning o'zi runaway'ni qo'zg'atishi mumkinligini
ko'rsatadi (B-`P2` 2/7 vs A-`P2` 0/24), arm `A` esa injeksiyadan keyin
bosim ostida restart qiladi, `no_action` qilmaydi — ya'ni arm `A` da
**ikkinchi qo'zg'atuvchi** bo'lishi mumkin; `smoke-13` esa `no_action`
da injeksiyadan oldin ham abort bo'lishini ko'rsatdi. **Oqibat:**
§10.1 ning trend testi arm `A` ichida (§16.2(A)), shuning uchun
arm'lararo farq unga **to'g'ridan-to'g'ri kirmaydi** — lekin §10.2 ning
arm'lararo KM/log-rank taqqoslashi va §8.2 ning PSI atributsiyasi
(`no_action` taqqoslovchi) uchun **arm'lar orasida differentsial
chiqarilish CONFOUND** bo'ladi. **Shuning uchun `(arm × pressure)`
jadvali majburiy**, va yuqoridagi yo'nalish mulohazasi **o'rnatilgan
deb taqdim etilmaydi.**

**4. YAROQLILIK QOIDASI `host_clock_discontinuity` (ta'rif EMAS), va smoke/kalibratsiya ma'lumotining CHIQARILISHI.**

**(4.1) FAKT** (`07` §7.7, `13` §0A.1). Windows host uyqusi WSL VM ni
kalibratsiya epizodi (`cal-01:A-P2-22`) **o'rtasida** muzlatdi: ikki
ketma-ket yozuv orasida `Δmono = 6.0 s`, `Δreal = 42 094.8 s` = **11.7
soat**. Guest'ning `boot_id` i **o'zgarmadi** — ya'ni muzlashning o'zini
**ichkaridan hech narsa ko'rmadi** (uyg'ongandan keyingi guest PID 1
restart'ini pid1 markeri ushladi, `13` §0A.1, lekin muzlashni emas).

**(4.2) QOIDA.** Validator (`revix/validate.py`,
`HOST_CLOCK_DISCONTINUITY_US = 1_000_000`; `main` da — commit `cb8d16d`, merge `5f5c873`):
**yozish lahzasida** o'qilgan `(mono, real)` juftlari mono bo'yicha
tartiblanadi, va **ketma-ket juftda `|Δreal − Δmono| > 1.0 s` bo'lsa —
ERROR, run rad etiladi** (`14` §2.3). Chegara **haqiqiy ma'lumotdan**
tanlangan: `~/revix-runs` dagi barcha soat oqimlari bo'yicha **72 402**
ketma-ket juft; qonuniy maksimum **0.000386 s** (`cal-01`, birinchi
sakrashdan oldin; `cal-01` siz 0.000206 s), p99.9 0.000099 s (`14`
§2.2). `1.0 s` — qonuniy maksimumdan **2590×** yuqori, 11.7 soatlik
hodisadan **42 088×** past. 28 tarixiy run katalogidan **faqat
`open-params-cal-01`** belgilandi.

**(4.3) MAQOMI — yaroqlilik qoidasi, TA'RIF EMAS.** U **faqat run'ni
rad eta oladi**; hech qachon metrikani, disposition'ni yoki ta'rifni
**o'zgartirmaydi** (test: uyquli va uyqusiz sintetik run'ning
`reduce_run(...).trials` i aynan teng, `14` §2.3). U §14.6 ga
**yangi invariant raqami sifatida emas**, §16.11 ning pid1 qoidasi kabi
**qo'shimcha shart** sifatida yoziladi (§14.6 qayta raqamlanmaydi).
§14.6: *"Validatsiyadan o'tmagan run analiz qilinmaydi"* — demak bitta
uyqu **butun run'ni** yo'qotadi, bitta trial'ni emas.

**(4.4) NIMANI USHLAY OLMAYDI.** **1 s dan qisqa muzlash** ushlanmaydi;
driver uyquni **runtime'da sezmaydi** — qoida faqat validatsiyada
ishlaydi (`14` §2.4 CHEKLOV), ya'ni uxlagan kampaniya davom etadi va
keyin butunlay rad etiladi; host realtime'ni `> 1 s` qadam bilan
tuzatsa, run **soxta** rad etiladi (o'lchangan ma'lumotda bunday hodisa
yo'q; guest'da NTP daemon yo'q, `14` §2.2). Yumshatish — host'ni uyg'oq
ushlash — faqat **idle** uyquni to'sadi (`07` §7.7).

**(4.5) QOIDA — smoke va kalibratsiya ma'lumoti pilot to'plamiga HECH
QACHON kirmaydi.** `datasets/smoke-*`, `datasets/open-params-*` va `10`
ning kalibratsiya run'lari (`dose-*`, `tstart-*`, `dprobe-*`, guest'da)
**pilot ma'lumot to'plamining qismi emas**: ular pilot bilan
**birlashtirilmaydi**, hech qanday P1 endpoint'ini hisoblashda
ishlatilmaydi va pilot natijasi sifatida **hisobot qilinmaydi**.
**Nega yozilishi shart:** smoke run'lar `run_meta` da **`run_mode =
"pilot"`** bilan yozilgan (validator `"smoke"` ni qabul qilmaydi, `14`
§7.2) va pilot bilan bir xil pre-registration hash'ini olib yuradi —
ya'ni **`run_meta` ularni pilotdan ajrata olmaydi**; ajratuvchi faqat
`run_id` / katalog nomi. **Mexanik majburlash (masalan validator yoki
analiz tekshiruvi) mavjud emas** — 9.9-band.

**5. §21.7 NING GATE'I — YOPILDI, faqat V2 generator vaqti bilan ishlaydigan driver uchun.**

**(5.1) Gate sharti.** §21.7: *"Generator §9.4 ning ikki invariantini
majburlamaguncha hech qanday pilot trial o'tkazilmaydi."* Invariantlar:
(1) `hold_s ≤ hold_cap_s = 13 s`; (2) `hold_s + ramp_above_threshold_s ≤
guard_sustain_s = 15 s`. Gate `08` §5 ning topilmasidan tug'ilgan: 5 s
so'ralgan epizod 0.35 dan yuqorida **16.3 s** turgan va uni **faqat
guard** to'xtatgan.

**(5.2) Invariant 1 — generator bosimni O'ZI tugatadi (o'lchangan).**

| manba | n | o'lchov |
|---|---|---|
| `10` §5.1 | 34 epizod | `overrun_s` p50 0.0619, max **0.2899 s** (kalibrlangan dial'da max 0.1766 s) |
| `13` §4 | 30 / 30 / 29 `pressure_stop` | `overrun_s` max 0.0954 / 0.1373 / 0.1210 s |
| `14` §11.2 (V2, real driver) | 5 tugagan `P2` trial | chiqish **33.075–33.245 s** (`pressure_off` 33.0); `overrun` 0.000–0.127 s, qolgani start kechikishi (start 17.494–17.547 vs 17.43 s) |

Tugagan V2 trial'larining **birortasida ham** bosimni guard
tugatmagan. **Harfan:** jismoniy hold (20.0 s dan generator chiqishigacha)
**13.075–13.245 s**, ya'ni 13 s dan **≤ 0.245 s** ortiq. **Nega bu gate'ni
ochiq qoldirmaydi:** (i) ortiqcha **chegaralangan** — start kechikishi +
bitta uzilmas page fault (`10` §5.1 ning `pressure.py` izohi), va har
trial'da `pressure_stop` record'i bilan **o'lchanadi**, yashirilmaydi;
(ii) 13 s ning v1.11 dagi asosi (`3 + 8 = 11 ≤ 13`) **tegilmaydi** —
`W_stab_pilot` oynasi 31.0 s da, `pressure_off` dan oldin tugaydi;
(iii) invariant 2 jismoniy eng yomon holat bilan ham bajariladi:
`13.245 + 0.0 = 13.245 ≤ 15`.

**(5.3) Invariant 2 — reja va o'lchov.** Reja: `13 + 0.0 = 13 ≤ 15`
(v1.11). O'lchov (V2, n = 6): rejadagi ramp oynasida
`ramp_above_threshold_s = 0.0` (**6/6**), guard'ga tegishli eng uzun
`≥ 0.35` oraliq **≤ 13.0 s**, `sustained_pressure` trip'i **0/6**.

**(5.4) QAROR (orkestrator, egasining 2026-10-03 delegatsiyasi bo'yicha):
gate YOPILDI — LEKIN faqat V2 ni o'z ichiga olgan driver uchun.** `main`
dagi **hozirgi** driver (V0, 18 s generator) uchun invariant 2 o'lchov
bilan **buzilgan** (`13 + 2.1 = 15.1 > 15`; `P2` 2/2 sustain trip) —
shuning uchun **u bilan pilot trial'i protokol buzilishi.** Shart: pilot
run'ining `run_meta.git_commit` i `11fca44` ni (yoki uning `main` ga
merge'ini) ajdod sifatida o'z ichiga oladi va `run_meta.generator_window`
`lead_s = 2.57` ni ko'rsatadi.

**(5.5) Gate'ning yopilishi NIMANI QAMRAMAYDI.** (i) **runaway qoidasi** —
u §9.4 ning invarianti emas, 3-band uni kutilma sifatida e'lon qiladi;
(ii) **`P1`/`P0` da V2 real driver bilan ishlamagan** — `P1` uchun dalil
V0 smoke'dan (18 s generator bilan oraliq 2.7 / 2.3 s, n = 2) va
kalibratsiyadan (`P1` oraliqlari ≤ 2.9 s, n = 24, `14` §5.2); V2 ning
qisqaroq oynasi ularni uzaytirmasligi — **TALQIN**, o'lchov emas;
(iii) n = 6, zaxira 2.0 s; (iv) validator invariantni **reja** ustida
tekshiradi (9.1-band).

**6. NIMA O'ZGARMADI — to'liq ro'yxat.**

**Hech bir metrika ta'rifi** (§4 VR va uning invalidator'lari, §5 FR-A /
FR-B, §6.1 ning uch downtime o'lchovi `D_sd` / `D_probe` / `D_eff`, §6.2
censoring, §6.3 latency, §6.4 recovery loop, §7 pressure o'lchovi);
**hech bir statistik test** (§10.1 Cochran–Armitage, Fisher/Barnard,
Newcombe/Wilson, Clopper–Pearson; §10.2 Kaplan–Meier / log-rank / **RMST
difference** / Cox-HR taqiqi / BCa; §10.4 Holm); **hech bir arm** (`A`:
`Restart=on-failure`, `RestartSec=100ms`; `no_action`: `Restart=no`);
**hech bir fault klassi** (faqat `clean_crash`, trial'ga bitta injeksiya);
**`P0`/`P1`/`P2` bandlari** (§9.3); **`disposition` ning yopiq enum'i**
va *"aynan bitta"* qoidasi (§12); §16.2 (A)/(B) va `(disposition,
disposition_source)` qoidasi; §17.4 ning ikki `disposition_source` qiymati
va besh bandi; **§11 butunlay** — kuchli shakl (`trend p > 0.05` VA
Newcombe yuqori chegarasi `< 0.15`), fail-slow limbi (`thr = 0.20 × τ =
1.6 s`, v1.11), halol power bayonoti, davom etish mezonlari (a)(b)(c),
null bo'lsa burilish; **§14 data schema** (record turlari, majburiy
maydonlar; §14.6 invariantlari **qayta raqamlanmadi**); §0 va §13 —
**tegilmadi**; §15–§22 ning qarorlari **o'z kuchida**.

| qiymat | holat |
|---|---|
| `W_stab_pilot = 8 s`, `W_stab = 60 s` | **O'ZGARMADI** |
| `τ = 8 s` (§10.2, §11) | **O'ZGARMADI** |
| `injection_offset = 3 s` | **O'ZGARMADI** |
| `θ = 0.8` | **O'ZGARMADI** |
| `k_f = 3` (`D_f = 300 ms`) | **O'ZGARMADI** |
| `P = 100 ms`, `T_conn = 50 ms`, `T_rt = 50 ms` | **O'ZGARMADI** |
| **20 blok / 120 trial** (`3 × 2 × 20`) | **O'ZGARMADI** |
| `hold_cap_s = 13 s`, `ramp_s = 5 s`, baseline 10 s, pre-flight 5 s, washout `≥ 20 s` | **O'ZGARMADI** |
| `ε = 32 MiB`, quiescence `0.05`, `T_q = 5 s`, `T_w = 15 s`, `T_w_max = 120 s` | **O'ZGARMADI** |
| `ramp_above_threshold_s = 0.0` (reja; v1.11) | **O'ZGARMADI** (2-band uning **o'lchov** bilan mosligini tiklaydi) |
| guard: `sustain_rate_threshold = 0.35`, `sustain_max_seconds = 15.0`, `user_full_rate2s_max = 0.98`, `user_full_avg10_max = 85.0`, `user_some_avg10_max = 90.0`, `host_mem_available_min_kb = 1 500 000` (`revix/guard.py` `DEFAULTS`); `guard_sustain_s = 15 s` (§9.4) | **O'ZGARMADI** (V4 rad etildi) |
| dial: slice `MemoryMax = 2G`, `MemoryHigh = 192M`, `CPUQuota = 400%`, `TasksMax = 256`; generator `step_mb = 4`, `base_mb` 160 / 184 / 184, `target_rate` 0.0 / 0.30 / 0.60, `interval_ms = 250`, generator unit `MemoryMax = 1536M` (`10` §2.6; `driver.py` `PRESSURE_*`) | **O'ZGARMADI** — 1.2-band uni **muzlatadi**, siljitmaydi |
| `WatchdogSec = 5 s`, `TimeoutStartSec = 10 s` | **qiymat o'zgarmadi** (driver default'lari) — endi **muzlatilgan** (1.1, 1.3) |
| `T_trial` formulasi `t_pressure_off + w_stab_s + P` | **O'ZGARMADI** — raqam (41.1 s) endi **muzlatilgan** (1.4) |
| generatorning ramp oynasi ichidagi boshlanishi | **15.0 s → 17.43 s** (V2, 2-band); `pressure_off` 33.0 s **o'zgarmadi** |

**7. TARIXIY BO'LIMLAR QAYTA YOZILMADI** (v1.11 ning 7-band siyosati).
**v1.11 log yozuvi** — jumladan uning (1.5) bandi (*"sustain taymeri faqat
hold ichida boshlanishi mumkin"*), 9.1 va 9.8 bandlari — **o'zgartirilmadi**:
u `v0.1.11-preregistration` tag'i bilan **e'lon qilingan** versiyaning
bayonoti. (v1.11 o'z yozuvini joyida tuzatgan edi, chunki u paytda tag
**yo'q** edi — v1.11 log, 8.5-band; bu yerda tag **bor**, shuning uchun
tuzatish yangi versiyada.) §16.10 ning jadvali va QAROR ro'yxati, §21.7
ning matni, §21.10 ning ro'yxati ham **tegilmadi**. Buning o'rniga
**normativ** joylarga **belgilangan `v1.12` ko'rsatkichi** qo'yildi:
sarlavha jadvali, §9.4 (V2), §12 (yacheyka jadvali), §14.6 (yaroqlilik
qoidasi), §16.10 (muzlatilgan qiymatlar), §21.7 (gate).

**8. NEGA BU AMENDMENT QONUNIY — va MA'LUMOT HOLATI.**

1. **Hech qanday P1 trial'i o'tkazilmagan** — birlamchi endpoint
   ko'rilmagan, `DEVELOPMENT.md` §7 ning *"ma'lumot yig'ilgandan keyin"*
   qoidasi **qo'llanmaydi**. **Lekin kalibratsiya va smoke ma'lumoti
   ko'rilgan** — 0-bandning e'loni, va bu **kafolat emas, e'lon**.
2. **Hujjatning O'ZI talab qilgan:** §16.10 ning 1-, 4-, 5- va
   6-qoidalari; §21.7 ning gate'i; §9.4 ning invariantlari.
3. **O'lchov bilan asoslangan, taxmin bilan emas** (v1.3 qoidasi) —
   1.3-banddan tashqari, va u **og'ish** sifatida belgilangan.
4. **Protsedura** (`DEVELOPMENT.md` §7): sana, sabab, nima o'zgardi,
   **nima o'zgarMAdi**, ma'lumot holati, **v1.11 ning `sha256` i va git
   tag'i saqlandi**. Hash hujjatdan ko'chirilmadi: tahrirdan oldin
   `sha256sum PREREGISTRATION.md` ishga tushirildi va
   `v0.1.11-preregistration` tag xabari bilan solishtirildi (**mos**).
   v1.12 ning o'z hash'i bu yerda yozilmaydi — u merge'dan keyin
   `v0.1.12-preregistration` tag xabarida qayd etiladi.

**MA'LUMOT HOLATI:**

| to'plam | holat | pilot to'plamiga |
|---|---|---|
| **P1 pilot trial'lari** | **YO'Q (0)** | — |
| `open-params-cal-01/-02/-03`, `open-params-smoke-01` | `datasets/` da (`main`) | **HECH QACHON** (4.5) |
| `10` ning `dose-*`, `tstart-*`, `dprobe-*` | guest `~/revix-runs` da | **HECH QACHON** |
| `smoke-01`…`smoke-07` (V0) | `datasets/` da (`main`) | **HECH QACHON** |
| `smoke-08`…`smoke-13` (V2) | `agent/pilot-ready` da, merge qilinMAGAN | **HECH QACHON** |

Smoke run'larida analiz moduli **mashina zanjirini tekshirish** uchun
ishga tushirilgan va bitta trial'lik `analysis.json` fayllari mavjud
(`14` §9). Bu amendment'ning hech bir qarori ularga **tayanmaydi**, va
ular gipoteza haqida **o'qilmaydi**.

**9. BU AMENDMENT NIMANI YOPMAYDI — va pilotni hozir nima to'xtatadi.**

1. **Reja va o'lchangan ramp.** `validate.check_planned_timeline` hamon
   **rejalashtirilgan** `ramp_above_threshold_s` ni tekshiradi, trial
   bo'yicha **o'lchanganini emas** (v1.11 3-band, CHEKLOV 2 — o'z
   kuchida). V2 ning o'lchangan mosligi faqat smoke'da (n = 6). Har trial
   uchun rejadagi ramp oynasida o'lchangan qiymatni yozish va tekshirish
   — **bajarilmagan**.
2. **OQ-11** — boshqa `MemoryHigh` qiymatlari o'lchanmagan (1.2).
3. **`P2` abort stavkasi o'lchanmagan**, arm'lar orasidagi farqi ham
   (3-band). U pilotning **natijasi** sifatida hisobot qilinadi.
4. **Bitta kernel.** Barcha kalibratsiya va smoke
   `6.6.87.2-microsoft-standard-WSL2`, systemd 257, bitta mashina, VM'siz
   host'da (`13` §9, `14` §8). **Boshqa kernel'da hech qanday kalibratsiya
   o'tkazilmagan**; `R = 2.57 s`, dial va to'rt muzlatilgan qiymatning
   asoslari boshqa muhitga **ko'chmaydi**.
5. **🔴 Driver istisno yo'lining nuqsoni — OCHIQ, merge qilinmaguncha.**
   V2 smoke partiyasi (`smoke-13`) topdi: guard abort'i injeksiyadan oldin
   SUT ni o'ldirganda `run_trial` ning istisno yo'li `guard_fired` ni
   tekshirmaydi, trial'ga §12 ning ustuvorligi (`aborted_guard`) o'rniga
   **`harness_error`** yoziladi va **washout o'tkazib yuboriladi** (`14`
   §11.4). Tuzatish `agent/pilot-ready` branch'ida (bu yozuv tahrir
   qilingan paytda `9c98e7f`; `14` §12, uning empirik tekshiruvi §12.1 da
   oldindan rejalashtirilgan) — **merge qilinMAGAN**. **Pilot u `main` ga
   merge qilinmaguncha BOSHLANMAYDI.**
6. **`timeout_start_sec` ning namunasi to'lmagan** — og'ish o'z kuchida
   (1.3); uni yopish faqat **yangi pre-registration**'da mumkin, P1
   ma'lumotidan keyin emas.
7. **Watchdog** bosim ichida ishga tushgan SUT da o'lchanmagan;
   kalibratsiyada bystander va prober yo'q edi (1.1).
8. **V2 cheklovlari** — `P1`/`P0` real driver bilan ishlamagan, zaxira
   2.0 s, `P2` PI nazoratining yo'qolishi (2.7, 5.5).
9. **Smoke/kalibratsiya chiqarilishi mexanik majburlanmaydi** (4.5).
10. **Host uyqusini runtime'da aniqlash yo'q** (4.4).
11. v1.11 dan meros: §18.8, §17.7 va `window_past_pressure` (v1.11 9.2,
    9.3, 9.5) — **ochiq qoladi**. Kampaniya bahosi o'lchangan trial
    wall'idan ~3.3 s/trial past (`14` §4.4) — ochiq, pilotni
    to'xtatmaydi.

**PILOTNI HOZIR NIMA TO'XTATADI** (v1.12 dan keyin, `main` bo'yicha):

1. **Driver istisno yo'li tuzatishi `main` da emas** (9.5-band).
2. **V2 kodi (`11fca44`) `main` da emas** — 5.4-band: `main` ning
   hozirgi driver'i bilan trial — protokol buzilishi.
3. **`run_meta.open_parameters`** muzlatilgan qiymatlarni kalibratsiya
   `run_id` lari bilan **olib yurmaydi** (1.5-band; §16.10(1)) — kod ishi.
4. **V2 hech qachon `P1`/`P0` da real driver bilan ishlamagan**, va
   (1)–(3) driver'ni o'zgartiradi: `14` §10 ning bajarilmagan regressiya
   trial'lari (`P1`, `P0`, ikkala arm) **merge qilingan kod bilan**
   birinchi pilot trial'idan oldin o'tkaziladi. Bu shart **shu
   amendment'da qo'yiladi** (5.5-band ning (ii) bandi sababli) — u
   mashina tekshiruvi, tadqiqot ma'lumoti emas, va 4.5 bo'yicha pilot
   to'plamiga kirmaydi.
5. **Bu amendment `main` ga merge qilinmagan va tag qilinmagan** — pilot
   run'larining `run_meta.preregistration_sha256` i v1.12 niki bo'lishi
   shart.

**To'xtatmaydigan narsalar:** OQ-11 (e'lon qilingan cheklov), `P2` abort
stavkasining noma'lumligi (oldindan e'lon qilingan kutilma), bitta
kernel (qamrov cheklovi), kampaniya bahosi.

### v1.10 → v1.11 (2026-10-03)

| | |
|---|---|
| **v1.10 sha256** | `5c5d0dd9c3a0661cd658e678cb44c34214a7497ba6b65d78b7830284177436d8` |
| **v1.10 git tag** | `v0.1.10-preregistration` |
| **Sabab** | Sarlavhadagi **ikki ochiq qaror** — §17.5 (O1–O4) va §18.6 (F1–F4) — qabul qilindi. Ikkisi ham **birinchi pilot trial'idan OLDIN** talab qilingan edi, va `docs/architecture/10-pressure-dozalash.md` ning **kalibrlangan dozadagi** o'lchovlari ikkisining ham **zarurligini** tasdiqladi |
| **Qarorni kim qabul qildi** | **Orkestrator**, loyiha egasining **2026-10-03 dagi ochiq delegatsiyasi** bo'yicha. §17.5 va §18.6 tanlovni *"loyiha egasiga"* qoldirgan edi; delegatsiya shu huquqni orkestratorga o'tkazdi va bu shu yerda qayd etiladi |
| **O'zgardi** | **(1) `hold_cap_s`: 12 s → 13 s** — §9.4 invariant 1, §4 ning `W_stab_pilot` izohi, §9.4 ning kampaniya arifmetikasi (52 → 53 s). **(2) §11 ning fail-slow limbining CHEGARASI** — referens `RMST(P0)` dan **`τ`** ga o'tdi ⇒ `thr = 0.20 × τ = 1.6 s`, **fiksa**; §18.2 ning o'qishi **bekor qilinadi**. **(3) `ramp_above_threshold_s`: eskirgan TAXMIN `3.0 s` → **o'lchangan** `0.000 s`** (3-band — bu **qaror emas**, §9.4 ning o'z talabining bajarilishi). **(4) §0 ning *“12 sekunddan uzoq sustained pressure”*** bandi **cap'ni kuzatadigan** shaklga keltirildi (1.11-band) — aks holda hujjat **o'zining birinchi sahifasida o'ziga zid** bo'lardi. §17.5 va §18.6 qaror qayd etilgan holda qayta yozildi — **O1–O4 va F1–F4 jadvallari SAQLANDI**. **(5) `T_trial` ning chiqarilgan default'i: 40.1 s → 41.1 s** — (1) ning **mexanik oqibati**, formula o'zgarmadi, raqam hech qachon muzlatilmagan (4-band — **qaror emas**); shu bandda §17.3 ning (b) chegarasi va §16.10 ning pastki chegarasi **bir xil vaqt boshida qayta chiqarildi** — ikkalasi pre-flight'ni tashlab ketgan edi, **hech bir xulosa o'zgarmaydi**. **(6) §14.4 ning ichki havolasi tuzatildi** (§7 → `01-muhit-tekshiruvlari.md` §4; 9.4-band — **ilmiy o'zgarish emas**) |
| **O'zgarMADI** | **hech bir metrika ta'rifi, statistik test, arm, fault klassi, probe parametri, VR ta'rifi, FR ta'rifi, `disposition` enum'i, va fail-slow limbining chegarasidan BOSHQA hech bir falsifikatsiya mezoni.** To'liq ro'yxat 6-bandda |
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

**4. `T_trial` (horizon): chiqarilgan default 40.1 s → 41.1 s — O3 ning OQIBATI, qaror EMAS.**

**Bu uchinchi qaror ham EMAS.** `T_trial` ni `revix/driver.py` ning
`t_trial_us()` i **o'zgarmagan** formula bo'yicha hisoblaydi
(`04-driver-va-analiz-shartnomasi.md` §5.2):

```
T_trial = t_pressure_off + w_stab_s + P
```

**Vaqt boshi — `trial_begin`** (`TrialTimeline` ning `t = 0` nuqtasi;
`04` §5.2: *"`T_trial` `trial_begin` dan … o'lchanadi"*). Bu boshdan
§9.4 jadvali **pre-flight bilan** boshlanadi: pre-flight 5 s → baseline
10 s → ramp 5 s → hold. Quyidagi hamma raqam **shu bitta boshdan**:

| kattalik | `hold_cap_s = 12 s` (v1.10; `04` §5.2 jadvali) | **`hold_cap_s = 13 s` (v1.11; o'lchangan)** |
|---|---|---|
| `t_hold_start` (`t_h`) | 20.0 s | 20.0 s |
| `t_inject` (`t_h + 3`) | 23.0 s | 23.0 s |
| `t_verify_end_earliest` (`t_inject + W_stab_pilot`) | 31.0 s | 31.0 s |
| `t_pressure_off` (`t_h + hold_s`) | 32.0 s | **33.0 s** |
| **`T_trial`** | **40.1 s** | **41.1 s = 41 100 000 µs** |
| `total_s` (yuqori chegara) | 52.0 s | 53.0 s |

13 s ustuni **ishga tushirib** olindi: `TrialTimeline()` default'i va
`driver.t_trial_us(TrialTimeline())` = `41100000`. Validator ham shuni
majburlaydi: 40.1 s ni ko'targan `run_meta` `t_trial_formula_mismatch`
bilan rad etiladi (`run_meta.t_trial_us` formuladan hisoblangan qiymatga
teng bo'lishi shart) — bu **kod/test** tomonining ishi, bu amendment'ning
emas.

**(4.1) Nega bu ilmiy o'zgarish EMAS.** §16.10 ning 5-qatori `T_trial`
ni **muzlatilmagan** deb sanaydi, va §16.10 ning qarori ochiq yozadi:
*"raqam muzlatilMAYDI, QOIDA muzlatiladi"*. Qoida — formula — o'zgarmadi;
faqat uning kirishi `t_pressure_off` (1) ning `hold_cap_s` 12 → 13 s
qadami bilan **1 s** siljidi. **Demak 41.1 s yangi tanlov emas, eski
qoidaning yangi muzlatilgan qiymatdagi natijasi.** §16.10(1) va (4) ning
talabi — aniq qiymat birinchi pilot trial'idan **oldin** ochiq qaror
bilan muzlatiladi — **o'z kuchida**, va bu band u qarorni **qilmaydi**
(9.8-band).

**(4.2) TUZATISH — §16.10 ning 4-QAROR bandidagi pastki chegara XATO
chiqarilgan edi.** U shunday yozgan: *"injeksiya trial boshidan ≥ 18 s
da … ⇒ `T_trial` ≥ 26 s"*. **18 s pre-flight'ni (5 s) tashlab ketadi**,
`T_trial` esa (40.1 s) `trial_begin` dan, ya'ni pre-flight **bilan**
o'lchanadi — **ikki xil vaqt boshi aralashgan**. Bir xil boshda
injeksiya **23 s** da, eng erta oyna oxiri **31 s** da, demak:

```
to'g'ri pastki chegara:  T_trial >= t_verify_end_earliest = 23 + 8 = 31 s
```

Kod aynan shu chegarani majburlaydi: `t_trial_us()`
`t_verify_end_earliest ≤ T_trial ≤ total_s` buzilsa **istisno** beradi.
**Matn tayangan ikkala tengsizlik ham o'z kuchida:** `41.1 ≥ 31` ✓ (va
eski yozilgan `41.1 ≥ 26` ham ✓), `τ = 8 ≤ 41.1` ✓; yuqoridan
`41.1 ≤ 53` ✓.

**(4.3) TUZATISH — §17.3 ning (b) holati chegarasi XATO chiqarilgan edi;
bir xil boshda qayta hisoblanadi.** §17.3 `t_h = 15 s`, injeksiya
`18 s`, hold oxiri `27 s` (pre-flight'siz bosh) ni `T_trial = 40.1 s`
(pre-flight bilan bosh) ga qarshi qo'ygan va `t_start > ~14 s` ni
olgan — **o'sha aralashish, 5 s xato bilan.** To'g'ri hisob, faqat
`trial_begin` boshida:

```
(b):          t_up + W_stab_pilot > T_trial
              T_trial = t_pressure_off + W_stab_pilot + P
         =>   t_up > t_pressure_off + P
              t_pressure_off = t_inject + (hold_cap_s - injection_offset)
         =>   t_up - t_inject > hold_cap_s - 3 + 0.1
budjet (§17.2):  t_up - t_inject = RestartSec (0.1) + t_start + probe kvantlashi (<= 0.1)
         =>   t_start > hold_cap_s - 3.1   (taxminan; kvantlash 0 .. 0.1 s)

12 s:  t_up > 32.0 + 0.1 = 32.1   =>  t_up - t_inject > 9.1    =>  t_start > ~8.9 s
13 s:  t_up > 33.0 + 0.1 = 33.1   =>  t_up - t_inject > 10.1   =>  t_start > ~9.9 s
```

Ya'ni (b) — **oyna pressure o'chgandan keyin boshlansa**; u faqat
`hold_cap_s` ga bog'liq, `T_trial` ning o'z raqamiga emas.

**(4.4) HECH BIR XULOSA O'ZGARMAYDI.** §17.3 ning hukmi — **(a) ustun,
ya'ni bias asosan H1 GA QARSHI** — o'z kuchida: (a) `t_start > 1.8 s`
da (v1.11; v1.10 da `0.8 s`), (b) `t_start > ~9.9 s` da (v1.10 da
`~8.9 s`, `~14 s` emas). Tuzatish (b) ni **yaqinlashtiradi**, lekin
(a) va (b) orasidagi tartibni **o'zgartirmaydi**. O'lchangan
`max(t_start) = 1.4807 s` (78 urinish, 1.3-band) ikkalasidan ham past.

**(4.5) KUZATUV, xulosa chiqarilmaydi:** `~9.9 s` driver'ning
`TimeoutStartSec = 10 s` default'idan (§16.10 ning 1-qatori) **biroz
pastda** turadi.

**(4.6) Tarix qayta yozilMADI** (7-band). v1.5 → v1.6 log yozuvi
`~14 s` va `40.1 s` ni o'z versiyasining bayonoti sifatida saqlaydi;
§16.10 ning 5-qatoriga va §17.3 ning hisobiga **belgilangan `v1.11`
ko'rsatkichi** qo'yildi.

**5. IKKI QARORNING IZCHILLIGI — nega ular BIRGA tanlandi.**

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

**6. NIMA O'ZGARMADI — to'liq ro'yxat.**

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
| `T_trial` (**muzlatilgan qiymat emas** — §16.10 ning 5-qatori; formula `t_pressure_off + w_stab_s + P` **o'zgarmadi**) | chiqarilgan default **40.1 s → 41.1 s** (4-band) |

§0 (qamrovdan tashqari) va §13 (nima muzlatilmaydi) ga **tegilmadi**.
§16, §19, §20, §21, §22 ning qarorlari **o'z kuchida**.

**7. TARIXIY BO'LIMLAR QAYTA YOZILMADI.** §17.9, §18.10, §19.4,
§21.10 va §22 ning *"NIMA O'ZGARMAYDI"* ro'yxatlari, §15.6 ning jadvali
va §16 ning ro'yxatlari `hold_cap_s = 12 s` deb yozadi. **Bular
o'z versiyasidagi holat haqidagi bayonotlar va ular TO'G'RI — shuning
uchun ular o'zgartirilmaydi.** Ularni qayta yozish tarixni
soxtalashtirish bo'lardi. Buning o'rniga **normativ** joylar yangilandi
(§4, §9.4, §11) va §15.3, §17.2, §17.6, §18.2, §18.7 ga
**belgilangan `v1.11` ko'rsatkichi** qo'yildi, demak o'sha bandlarni
o'qiyotgan kishi eski qiymatga yoki eski kafolatga **ishonib qolmaydi**.
Xuddi shu qoida bo'yicha §16.10 ning 5-qatori va §17.3 ning (b) hisobi
(4-band), hamda §15.6(2), §17.8 va §18.9 ning *"§14.4 havolasi ochiq"*
bayonotlari (9.4-band) ham **belgilangan `v1.11` ko'rsatkichi** oldi;
v1.5 → v1.6 log yozuvining `~14 s` i va eski log yozuvlarining
*"ATAYLAB yopilmadi"* bayonotlari **qayta yozilmadi**. Yagona **normativ
matn tuzatishi** — §14.4 ning havolasi (9.4-band).

**8. NEGA BU AMENDMENT QONUNIY — va u NIMANI KAFOLATLAMAYDI.**

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
   bilan solishtirildi (ikkisi **mos**). v1.11 ning o'z `sha256` i bu
   yerda yozilmaydi — har bir yozuv faqat **oldingi** versiyaning hash'ini
   saqlaydi; v1.11 niki merge'dan keyin `v0.1.11-preregistration` tag
   xabarida qayd etiladi;
5. **bu yozuv tag va push'dan OLDIN joyida tuzatildi** (2026-10-03).
   Birinchi tahririda (`744ef93`, merge `7e7a837`) uchta kamchilik
   bor edi: `T_trial` ning siljishi qayd etilmagan (endi 4-band); 9.6
   band yozilgan paytdayoq **eskirgan**, 9.7 band esa keyinroq kod
   tuzatilgach eskirgan (ikkalasi endi tarixi bilan qayta yozildi); va
   §14.4 havolasi ochiq qoldirilgan (endi 9.4-band). Tuzatish paytida
   `origin/main` hamon `76fa33c` da va `v0.1.11-preregistration` tag'i
   **yo'q** edi — ya'ni v1.11 hech qachon **e'lon qilinmagan**, va
   tuzatish yangi versiya (v1.12) talab qilmaydi.

**9. BU AMENDMENT NIMANI YOPMAYDI** (va 9.4 da — nimani **yopdi**).

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
4. **✅ §14.4 ning havolasi SHU AMENDMENT'DA YOPILDI (v1.11,
   2026-10-03) — ilmiy o'zgarish EMAS.** §14.4 ning `run_meta` qatori
   *"§7 tirik unit shartini ko'ring"* der edi; §7 — *Pressure o'lchovi*,
   unda bunday shart yo'q (§15.6(2), v1.4 dan beri ochiq). Havola endi
   **`docs/architecture/01-muhit-tekshiruvlari.md` §4** ga ko'rsatadi —
   talab o'sha yerda so'zma-so'z turadi (*"Har unit'ning property'lari u
   TIRIK paytida dump qilinishi shart"*), va
   `04-driver-va-analiz-shartnomasi.md` §1.1 ham aynan unga havola qiladi
   (ikkalasi tekshirildi).
   **Qaysi shart ostida:** §17.8 — *"17.5 ning O1–O4 qarori muzlatilgan
   matnga baribir tegadi … shu amendment bu havolani tuzatish uchun
   to'g'ri joy"*; §18.9 — *"Tuzatish vositasi — §17.5 qarorini amalga
   oshiradigan amendment."* v1.11 — **aynan o'sha amendment**: u §17.5
   qarorini amalga oshiradi va muzlatilgan matnni (§0, §4, §9.4, §11)
   **ochadi**. Demak o'sha ikki bo'lim qo'ygan shart **bajarildi**, va
   §18.9 ning *"o'z mezonimni jimgina yumshatmayman"* qoidasi buzilmaydi:
   mezon yumshatilmadi, u **qanoatlantirildi**.
   **Tarix, ochiq:** bu yozuvning birinchi tahriri havolani *"ATAYLAB
   yopilmaydi"* deb qoldirgan edi, sabab sifatida *"havola tuzatishi
   delegatsiya qilingan qarorning qismi emas"* ni keltirib. **Bu sabab
   qaytarib olinadi:** ichki ko'rsatkichning to'g'riligini tiklash hech
   bir delegatsiya qilingan qarorga (O1–O4, F1–F4) **tegmaydi**, demak u
   delegatsiyani talab qilmaydi — yagona shart §17.8/§18.9 niki edi.
   Havola v1.4 dan v1.10 gacha, **besh** amendment bo'ylab ochiq qoldi.
   **Talabning o'zi o'zgarmadi:** `units_show` unit **TIRIK** paytida
   olinadi.
5. **`window_past_pressure` yo'q qilinmadi** — 1.9-band: `1/24` epizod
   hamon ruxsatdan oshadi, va §17.4(4) ning yacheyka bo'yicha hisobot
   talabi **majburiy** bo'lib qoladi.
6. **✅ YOPILGAN — va bu band YOZILGAN PAYTDAYOQ ESKIRGAN edi.**
   Birinchi tahrir `10` §12.5 dan ikki kod blokerini ko'chirgan edi:
   OQ-2 (`driver.py` generatorga dozalash parametrlarini bermaydi ⇒
   o'lchangan **nol doza**) va `PRESSURE_TARGET_RATE["P2"] = 0.70`
   (over-doza; o'lchangan to'g'ri qiymat **0.60**). **Ikkalasi ham bu
   yozuv tahrir qilinishidan OLDIN tuzatilgan edi** — uchala commit
   v1.11 tahriri `744ef93` ning **ajdodi**
   (`git merge-base --is-ancestor`): `821a6a0` (merge,
   `experiment/pressure-dose` — kalibratsiyaning o'zi), `042631b`
   (merge, `fix/driver-dose` — `a02cea9`: kalibrlangan dial generatorga
   beriladi, `P2` nishoni 0.60) va `31ebd4a` (merge, `fix/driver-dose`
   — `663ff8d`: nol doza bilan start rad etiladi). Ya'ni band
   `10` §12.5 ning holatini ko'chirgan, `main` niki emas. `main` da
   hozir: `PRESSURE_TARGET_RATE = {"P0": 0.0, "P1": 0.30, "P2": 0.60}`,
   `PRESSURE_STEP_MB = 4`, `PRESSURE_BASE_MB = {"P0": 160, "P1": 184,
   "P2": 184}`, dial `_pressure_argv()` da **oshkora** argv sifatida
   beriladi, va `setup_run()` ning `_require_nonzero_dose()`
   pre-flight'i nol doza bilan run'ni **boshlatmaydi**.
   Band qo'shimcha ravishda 3-bandning `schedule.py` dagi ikki
   konstantasini ham sanagan edi — u esa tahrir paytida **haqiqatan
   ochiq** edi va keyin `437c699` bilan (merge `fe0cd1d`,
   `agent/holdcap`) yopildi: `HOLD_CAP_S = 13.0`,
   `RAMP_ABOVE_THRESHOLD_S = 0.0`. **Bular pre-registration masalasi
   emas edi** — va endi kod masalasi ham emas.
7. **✅ YOPILGAN — bu band yozilgan paytda TO'G'RI edi.** Birinchi
   tahrir shunday yozgan: `revix/driver.py` `ramp_above_threshold_s` ni
   hamon **`"calibration_required": true`** bilan beradi, holbuki
   kalibratsiya bajarilgan (3-band), va bir test shuni tasdiqlaydi;
   `tests/unit/test_driver.py` esa `13.0 s` li hold **rad etilishini**
   tasdiqlaydi. Tahrir paytida bu **haqiqat** edi (tuzatuvchi commit
   `744ef93` ning ajdodi emas). **Yopildi:** `ccaa53b` (merge `2a80443`,
   `agent/driver-cap`). `main` da hozir `open_parameters` ning
   `ramp_above_threshold_s` yozuvi `calibration_required: false` va
   o'lchov, manba, reja va invariant 2 zaxirasini olib yuradigan
   `calibration` bloki bilan keladi; test `HOLD_CAP_S == 13.0` va
   `hold_s == hold_cap_s` ning **qonuniyligini** tasdiqlaydi. **Ya'ni
   harness endi kalibratsiyani ham, yangi cap'ni ham to'g'ri
   ifodalaydi.** 3-bandning CHEKLOV 2 si (invariant **reja** ustida,
   o'lchov ustida emas) **o'z kuchida** — u tuzatilgan nuqson emas,
   e'lon qilingan cheklov.
8. **PILOTNI HOZIR NIMA TO'XTATADI — `main` va muzlatilgan matn
   bo'yicha.** Javob *"hech narsa"* **EMAS**: muzlatilgan hujjatning
   **o'zi** ikki preshart qo'yadi va ular bajarilmagan.
   1. **§21.7 ning ⛔ GATE'i rasman ochiq** (9.1-band; sarlavhaning
      Gate qatori): *"Generator §9.4 ning ikki invariantini
      majburlamaguncha hech qanday pilot trial o'tkazilmaydi."* `10`
      §12.2 shart **o'lchov bo'yicha bajarilgan**, deydi, lekin rasman
      yopish — frozen matn egasining qarori, va bu amendment uni
      **qilmaydi**.
   2. **§16.10 QAROR 1 va 4:** muzlatilmagan parametrlarning hammasi
      *"birinchi pilot trial'idan OLDIN"* kalibratsiya bilan belgilanadi
      va `run_meta.open_parameters` ga **kalibratsiya run'ining `run_id`
      si bilan** yoziladi; `T_trial` ning aniq qiymati *"ochiq qaror
      bilan muzlatiladi"*. `main` da: `WatchdogSec` **o'lchanmagan**
      (`10` §10.2, OQ-8); `driver.py` ning `open_parameters` ida
      `watchdog_sec`, `timeout_start_sec` va `memory_high` hamon
      `calibration_required: true` (`TimeoutStartSec = 10 s` uchun
      o'lchangan asos `10` §10.1 da bor, lekin belgi va qaror yo'q);
      `open_parameters` da kalibratsiya run'ining `run_id` siga havola
      **yo'q**; `T_trial = 41.1 s` — **default**, ochiq qaror bilan
      muzlatilmagan (4.1-band).
   **To'xtatmaydigan narsalar:** 3-bandning CHEKLOV 2 si (e'lon qilingan
   cheklov); validator 40.1 s ni rad etadigan ikki `T_trial` test
   fixture'i (kod/test ishi, pre-registration emas); `P2` ning ushlab
   turilmasligi (`10` §12.5(4) — §9.4 ning uzluksiz analizi qoplaydi);
   9.2, 9.3, 9.5 bandlar — ochiq qoladi, lekin matn ularni trial
   preshartiga **aylantirmaydi** (§17.7 o'zi *"P1 ni bloklamaydi"*
   deydi).

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

> **⚠️ v1.12 — yuqoridagi `0.000 s` GENERATORNING O'Z ramp oynasida
> o'lchangan; rejadagi 5 s ramp oynasida esa avvalgi driver bilan 2.0–2.1 s
> chiqdi.** Real driver bilan smoke trial'lar generatorning **ramp boshidan
> (15.0 s) `ramp_s + hold_s = 18 s`** ishlaganini, guard'ning sustain
> taymeri hold'dan **1.35–1.46 s OLDIN** boshlanganini va `P2` ning 2/2
> trial'i `aborted_guard` bo'lganini ko'rsatdi (`13 + 2.1 = 15.1 > 15`).
> **Implementatsion aniqlashtirish (V2):** generator **`t_h − R`** da
> boshlanadi (`R = 2.57 s` — generatorning o'z o'lchangan ramp'i, nomli
> konstanta, barcha arm va band uchun bir xil), **`hold_s + R`** ishlaydi
> va **`t_pressure_off`** da chiqadi. Yuqoridagi jadvalning **hech bir
> vaqti o'zgarmadi** (pre-flight 5, baseline 10, ramp 5, hold 13,
> injeksiya `t_h + 3`, pressure off `t_h + 13`); *"ramp 5 s"* — bosim
> ko'tariladigan oyna, generatorning o'z ramp'i uning oxirgi 2.57 s ini
> egallaydi. Shuning uchun rejadagi `pressure_on_s = 18 s` amaldagi
> generator vaqtining (≈ 15.57 s) **yuqori chegarasi**. V2 bilan (`P2`,
> **n = 6**): rejadagi ramp oynasida o'lchangan qiymat **0.0 (6/6)**,
> guard'ga tegishli eng uzun `≥ 0.35` oraliq **≤ 13.0 s**, sustain trip
> **0/6**. Amendment log, v1.11 → v1.12, **2-band**.

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

> **v1.12 — hisobot talabi (ta'rif EMAS, enum'ga tegilmadi):** `aborted_guard`
> soni va ulushi **har `(arm × pressure)` yacheykasi bo'yicha ALOHIDA**, guard
> qoidasi (`sustained_pressure` / runaway / boshqa) va **injeksiyaga nisbatan
> vaqti** (oldin / keyin) bilan **majburiy jadvalda** beriladi. `P2` da guard'ning
> runaway qoidasi bo'yicha bunday trial'lar **kutiladi** (oldindan e'lon
> qilingan; stavka **o'lchanmagan**); ularning chiqarilishi shartli ravishda
> **H1 ga qarshi** og'adi, arm'lar orasidagi farqi esa **confound** bo'ladi.
> Amendment log, v1.11 → v1.12, **3-band**.

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
| `run_meta` | `preregistration_sha256`, `git_commit`, `git_dirty`, `rng_seed`, `boot_id`, har unit'ning **tirik** `systemctl show` dump'i | reproducibility; `docs/architecture/01-muhit-tekshiruvlari.md` §4 ning tirik unit shartini ko'ring (**v1.11**: havola tuzatildi — avval xato ravishda §7 ga ko'rsatardi; Amendment log, v1.10 → v1.11, 9.4-band) |
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

> **v1.12 — qo'shimcha yaroqlilik qoidasi (yangi invariant EMAS; §14.6 qayta
> raqamlanmaydi — §16.11 ning pid1 qoidasi kabi): `host_clock_discontinuity`.**
> Yozish lahzasida o'qilgan `(mono_us, real_us)` juftlarining ketma-ket ikkitasi
> orasida `|Δreal − Δmono| > 1.0 s` bo'lsa run **rad etiladi** — host uyqusi VM ni
> muzlatadi va `boot_id` buni ko'rmaydi (`docs/architecture/07-wsl-muhit-tekshiruvlari.md`
> §7.7). Bu qoida **faqat rad etadi**: hech bir metrika, disposition yoki ta'rifni
> o'zgartirmaydi; 1 s dan qisqa muzlashni **ushlamaydi**. Smoke va kalibratsiya
> run'lari (`smoke-*`, `open-params-*`) — `run_mode` dan qat'i nazar — pilot
> ma'lumot to'plamiga **hech qachon** kirmaydi. Amendment log, v1.11 → v1.12,
> **4-band**.

> **v1.13 — bu darvoza birinchi pilot run'ini RAD ETDI (darvoza o'zgarmadi).**
> `p1-pilot-001` (v1.12, 120/120 trial) 4 xato bilan o'tmadi — (4) va (6)
> invariantlari va §17.4(5) bo'yicha; sabab — driver implementatsiyasining uch
> nuqsoni (`docs/architecture/15-pilot-001-validatsiya-xatolari.md`). Run
> **analiz qilinmaydi**, saqlanadi, **o'chirilmaydi**; analiz qilinishi mumkin
> bo'lgan **yagona** pilot run'i — `p1-pilot-002`. Amendment log, v1.12 → v1.13,
> **0- va 3-band**.

> **v1.14 — (4) ning qavsi USTUVORLIK TARTIBI bilan birga o'qiladi (matn o'zgarmadi).**
> *"(aks holda trial `censored`)"* — probe-uzilish qoidasiga yetib kelgan trial
> uchun; undan **oldin** turuvchi disposition (`aborted_guard`, `contaminated`,
> `washout_timeout`, `harness_error`; §4 invalidator'lari, §12,
> `schedule.DISPOSITION_RULES`, `reduce.derive_disposition`, `04` §8.1) olgan
> trial'dagi uzilish **ogohlantirish** sifatida qayd etiladi; validator XATOsi —
> faqat `complete` da. **Bu talqin ma'lumotdan KEYIN yozilgan:** `p1-pilot-002`
> shu qavs bo'yicha **O'TMADI** (1 xato — `b010t005`, `aborted_guard`), va asl
> hukm yozuvda qoladi. Dalil: `docs/architecture/17-pilot-002-validatsiya-xatosi.md`
> §2–§4. Amendment log, v1.13 → v1.14, **0-, 2- va 7-band**.

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
   > **✅ v1.11 — havola tuzatildi** (§14.4 endi `01-muhit-tekshiruvlari.md`
   > §4 ga ko'rsatadi). Amendment log, v1.10 → v1.11, 9.4-band.
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
| 5 | **`T_trial`** (horizon) | shartnoma formulasi: `t_pressure_off + w_stab_s + P` = **40.1 s** (**⚠️ v1.11**: `hold_cap_s` 12 → 13 s bilan formula o'zgarmagan holda **41.1 s**; pastdagi 4-QAROR bandining `≥ 26 s` chegarasi pre-flight'ni tashlab ketgan — to'g'risi **`≥ 31 s`** (`t_verify_end_earliest`), xulosa o'zgarmaydi. Amendment log, v1.10 → v1.11, **4-band**) | §6.2, §6.4 unga tayanadi, lekin **hech qayerda raqamlanmagan**. 16.2(B) dan keyin u binar endpoint'ning **maxrajini to'g'ridan-to'g'ri belgilaydi**: qisqa horizon qaytmaslikni yaratadi, uzun horizon qaytishni |
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

> **✅ v1.12 — 1-, 2-, 3- va 5-qatorlar MUZLATILDI** (1- va 4-qoida bajarildi;
> kalibratsiya run'lari `open-params-cal-01`, `-02`, `-03` —
> `docs/architecture/13-ochiq-parametrlar-kalibratsiyasi.md`):
> `WatchdogSec = 5 s` (qoida bo'yicha, zaxira **21.4×**, `Result=watchdog` 0/72);
> `MemoryHigh = 192M` (`MemoryMax=2G` ostida **qayta o'lchangan** —
> `10-pressure-dozalash.md` §2.2, `dose-01-dial` — demak 6-qoida bajarildi; OQ-11
> ochiq); `T_trial = 41.1 s` (ochiq qaror, formula o'zgarmadi; 6-qator endi
> tekshiriladi: `τ = 8 ≤ 41.1`); **`TimeoutStartSec = 10 s` — ⚠️ OG'ISH:** o'z
> kalibratsiya qoidasi namuna yetmagani uchun **taklif bermagan**, qiymat
> ma'lumotdan oldingi default sifatida saqlandi. 5-qoidaning (i) va (iv) uchun
> bayonotlari: Amendment log, v1.11 → v1.12, **1.1 va 1.3-band**. 4-qator (`P2`
> nishoni) v1.11 dan oldin kodda 0.60 ga tuzatilgan. **1-qoidaning ikkinchi
> yarmi — qiymatlarni `run_id` lari bilan `run_meta.open_parameters` ga yozish —
> kod ishi, va u hali bajarilmagan** (1.5 va 9-band). Yuqoridagi jadval va QAROR
> matni **tarix sifatida** o'zgartirilmadi.

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

> **⚠️ v1.11 — yuqoridagi (b) hisobi IKKI VAQT BOSHINI aralashtirgan.**
> `t_h = 15 s` / injeksiya `18 s` pre-flight'siz boshdan, `T_trial =
> 40.1 s` esa `trial_begin` dan (pre-flight 5 s **bilan**) o'lchanadi.
> Bir xil boshda (`trial_begin`; injeksiya **23 s**): (b) ⇔ `t_up >
> t_pressure_off + P` ⇒ `t_start > hold_cap_s − 3.1`, ya'ni 12 s da
> **`t_start > ~8.9 s`** (`~14 s` emas), v1.11 ning 13 s cap'i va
> `T_trial = 41.1 s` da **`t_start > ~9.9 s`**. **Xulosa o'zgarmaydi:**
> (a) `t_start > 1.8 s` da (v1.11), (b) `~9.9 s` da — (a) ustun.
> Amendment log, v1.10 → v1.11, **4-band** (4.3, 4.4).

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

> **✅ v1.11 — YOPILDI.** Tavsiyaning sharti bajarildi: v1.11 §17.5
> qarorini amalga oshiradi va muzlatilgan matnni ochadi; §14.4 endi
> `01-muhit-tekshiruvlari.md` §4 ga ko'rsatadi. Amendment log,
> v1.10 → v1.11, **9.4-band**.

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

> **✅ v1.11 — YOPILDI, aynan shu shart ostida.** v1.11 — §17.5 qarorini
> amalga oshiradigan amendment, va u muzlatilgan matnni ochadi; mezon
> yumshatilmadi, **qanoatlantirildi**. §14.4 endi
> `01-muhit-tekshiruvlari.md` §4 ga ko'rsatadi. Amendment log,
> v1.10 → v1.11, **9.4-band**.

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

> **✅ v1.12 — GATE YOPILDI, faqat V2 generator vaqti bilan ishlaydigan driver
> uchun** (orkestrator qarori, egasining 2026-10-03 delegatsiyasi bo'yicha).
> Invariant 1: generator bosimni **o'zi** tugatadi — `overrun_s` max 0.2899 s
> (`10` §5.1, n = 34), V2 real driver'da chiqish **33.075–33.245 s**
> (`pressure_off` 33.0 s; n = 5), ya'ni jismoniy hold 13 s dan **≤ 0.245 s**
> ortiq — chegaralangan, har trial'da o'lchanadi, va `3 + 8 = 11 ≤ 13` hamda
> `13.245 + 0.0 ≤ 15` ni buzmaydi. Invariant 2: rejadagi ramp oynasida
> o'lchangan qiymat **0.0 (6/6)**, guard'ga tegishli eng uzun oraliq **≤ 13.0 s**,
> sustain trip **0/6**. `main` ning hozirgi (V0, 18 s generator) driver'i bilan
> invariant 2 o'lchov bo'yicha **buzilgan** — u bilan trial **protokol
> buzilishi**. Runaway qoidasi (`0.98`) gate'ga **kirmaydi**. Amendment log,
> v1.11 → v1.12, **5-band**.

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
