# 01 — P1 pilot natijalari: `p1-pilot-002`

> **Bu tadqiqotchi (exploratory) pilot. U hech qanday tasdiqlovchi da'vo qilmaydi.**
> Frozen qoida (§20.3) bo'yicha pilot **GATE QILINGAN**: birlamchi endpoint hisoblangan, lekin
> **talqin qilinmaydi**. Pilotning asosiy qiymati — mashina ishlashini va muzlatilgan dizaynning
> aniq zaif joylarini ko'rsatganida (§6).

| | |
|---|---|
| run | `p1-pilot-002`, seed `20261006`, 120 trial (20 blok × 6 yacheyka), `schedule_digest` `69ae399e…b2dc` |
| kod / prereg | `git` `8deaaf0aab33…` (toza), `preregistration/v1.13` `f0c45722…b117` (run paytida); validatsiya **v1.14** darvozasi ostida |
| vaqt | `2026-10-04 13:50:38Z` → `15:43:53Z`, driver wall `6792 s` |
| yaroqlilik | asl `validate`: **O'TMADI** (1 xato); tuzatilgan (v1.14) darvoza: **O'TDI** (0 xato, 24 ogohlantirish). Ikkala hukm saqlangan (§1). |
| ma'lumot | `datasets/p1-pilot-002/` (xom `*.zst`, hukmlar, `derived/`), `analysis.json` sha256 `e980b3710c26e70308229a70e622405ad553a810cdc2834c67e9af8e6394d7b8` |

Hujjat FAKT / GIPOTEZA / NATIJA / TALQIN / CHEKLOV tartibida. **NATIJA** — muzlatilgan qoidaning
o'lchangan ma'lumotga qo'llanishi, tadqiqot gipotezasi haqidagi xulosa emas.

---

## 0. Oshkora e'lon — kim nimani ko'rdi

- Orkestrator pilot **paytida** yacheyka bo'yicha disposition sonlarini chop etdi (kuzatuvchi orqali).
- Validatsiya darvozasi **ikkinchi yiqilishdan keyin** va effekti (yiqilish → o'tish) oldindan
  ma'lum holda o'zgartirildi (v1.14). Himoya va qarshi dalillar `PREREGISTRATION.md` v1.14 da.
- Tahlil zanjirining birinchi ishga tushishida **orkestratorning o'z skripti** `progress` ustunini
  tashlab yuborgan va `R_ref` 120/120 trialda hisoblanmagan (§7). Bu natija e'lon qilinishidan oldin
  mustaqil audit (`18`) bilan topildi va tuzatildi; hisobot **tuzatilgan** reduksiyaga asoslangan.
- Audit agenti tasodifan arm A yacheykalarining k/n sonlarini ko'rdi; ular uning hisobotida yo'q.

## 1. Yaroqlilik tarixi — `FAKT`

| run | asl `validate` | tuzatilgan (v1.14) | holat |
|---|---|---|---|
| `p1-pilot-001` | O'TMADI: 4 xato, 3 ogohlantirish (3 driver nuqsoni) | **O'TMADI**: xuddi shu 4 xato | **yaroqsiz**, qutqarilmagan, tahlil qilinmaydi, hech qachon `-002` bilan aralashtirilmaydi (`datasets/p1-pilot-001-INVALID/`) |
| `p1-pilot-002` | O'TMADI: 1 xato (`b010t005`, `aborted_guard` + probe uzilishi) | **O'TDI**: 0 xato, 24 ogohlantirish | yagona tahlil qilinadigan run, **tuzatilgan darvoza ostida** |

Validator tuzatishi (`348eacd`): probe-gap xatosi faqat `complete` uchun; `guard_event_not_reflected`
simmetrik qat'iylashtirildi. `pilot-001` ga ta'siri 0 (har bir xato joyida). `b010t005` ikki mustaqil
asosda chiqariladi (`aborted_guard`, `bystander_lost_contract`).

## 2. Mashina — `FAKT`

- 120/120 `trial_end` (har trialga aynan bitta), `harness_error` **0**, `contaminated` 0, `washout_timeout` 0.
- Post-flight: `boot_id` va PID 1 o'zgarmagan, `oom_kill` 0 → 0, `revix` unit 0, cgroup 0, `real − mono` farqi +2 µs;
  jonli soat kuzatuvi har 20 s da ≤ 3 µs, **host uyqusi yo'q**.
- **Sustain guard trip: 0** (pilot-001 da ham 0). V2 (generator `hold_start − 2.57 s` da boshlanadi) vazifasini bajardi.
- `run_meta`: `disposition_facts = post_window_reducer_facts` (v1.13 tuzatishlari), `open_parameters` muzlatilgan qiymatlar bilan.

## 3. Yacheyka bo'yicha jadval — `FAKT` (majburiy arm × yacheyka eksklyuziya jadvali, v1.12/v1.14)

| arm | pressure | n | complete | censored | aborted_guard | `no_episode` | `probe_gap` | `window_past_pressure` | `down_at_horizon` |
|---|---|---|---|---|---|---|---|---|---|
| A | P0 | 20 | 17 | 3 | 0 | **10** | 3 | 0 | 0 |
| A | P1 | 20 | 13 | 6 | 1 | 0 | 5 | 1 | 0 |
| A | P2 | 20 | 11 | 7 | 2 | 0 | 6 | 1 | 0 |
| no_action | P0 | 20 | 0 | 20 | 0 | 0 | 5 | 0 | 15 |
| no_action | P1 | 20 | 0 | 17 | 3 | 0 | 2 | 0 | 15 |
| no_action | P2 | 20 | 0 | 17 | 3 | 0 | 2 | 0 | 15 |

Birlamchi binar maxrajga kirganlar: A/P0 **7**, A/P1 **13**, A/P2 **11**; `no_action` har yacheykada 15 (`down_at_horizon`
kuzatilgan `VR = false`, §16.2(B)). Jami chiqarilgan: 44/120 (36.7%): `probe_gap` 23, `aborted_guard` 9, `no_episode` 10, `window_past_pressure` 2.

- `aborted_guard`: arm A **3** (P1 1, P2 2), `no_action` **6** (P1 3, P2 3), P0 da **0**. Sabab **hammasida** `user_full_rate2s_runaway`
  (stall tezligi 0.98 dan oshdi). v1.12 da P2 uchun e'lon qilingan kutilma P1 da ham kuzatildi. n kichik; arm'lar orasidagi farq haqida xulosa chiqarilmaydi.
- `window_past_pressure`: **2** trial (A/P1 1, A/P2 1); eng yuqori daraja `A:P2` da **0.050** (§17.4(4): bu o'zi natija, yashirilmaydi).

## 4. Frozen qoida bo'yicha pilot holati — `NATIJA`: **GATE QILINGAN**

§20.3 *muzlatilgan hisobot qoidasi*: `no_episode` darajasi `(arm × pressure)` bo'yicha alohida beriladi va **injektor samaradorligi
metrikasi** deb nomlanadi; nolga teng bo'lmagan daraja pilotni gate qiladi va **birlamchi endpoint talqin qilinmaydi**.

| yacheyka | `no_episode` |
|---|---|
| A / P0 | **10 / 20** |
| A / P1, A / P2 | 0 / 20, 0 / 20 |
| `no_action` (hammasi) | 0 (restart yo'q, uzilish gorizontgacha davom etadi) |

Daraja nolga teng emas ⇒ analiz kodi `pilot_gated_by_injector_effectiveness` beradi (n = 10, 8.3%). **Bu qoida so'zma-so'z qo'llanadi.**

### 4.1 Lekin qoidaning faraz-sababi bu implementatsiyada yolg'on — `FAKT` (`18` §1)

§20.3: *"SUT o'ldirilsa contract buzilishi shart; demak `no_episode` injeksiya ishlamaganini bildiradi."* Audit o'lchagani:

- Injektor **20/20** `A/P0` trialda ishladi (`armed=exit`, `Result=exit-code`, `NRestarts 0→1`, prober yangi invocation ko'rdi).
- `no_episode` bo'lgan 10 trialda crash **aynan 2 ta ketma-ket `conn_refused`** probe berdi, epizodli 10 trialda 3–4 ta. Detektor chegarasi `k_f = 3` (§3).
- Uzilishni asosan `systemd` restart taymeri belgilaydi (+162, +212, +300 ms), `start → active` esa 20–35 ms.

**Ya'ni injeksiya ishladi; epizod tug'ilmadi, chunki uzilish detektorning o'lchamidan qisqa.** P0 (reference daraja) da pre-registratsiya qilingan VR
**konstruksiya bo'yicha aniqlanmagan** — bu dizayn xususiyati, nuqson emas. Frozen §20.3 bunga tayyor emas.

**Qaror (shu hujjatning):** gate qoidasi so'zma-so'z qo'llanadi (birlamchi endpoint talqin qilinmaydi) **va** sabab uning farazidan boshqacha ekani ochiq yoziladi.
Qoidani o'zgartirish yoki "gate shart emas" deyish ma'lumotdan keyingi ikkinchi darvoza o'zgarishi bo'lardi.

## 5. Hisoblangan, lekin TALQIN QILINMAYDI — `FAKT`

To'liq shaffoflik uchun (yashirish tanlab hisobot bo'lardi), tuzatilgan reduksiyaning birlamchi chiqishi:

| arm A | P0 | P1 | P2 |
|---|---|---|---|
| `VR = true` / maxraj | 7 / 7 | 5 / 13 | 1 / 11 |

Cochran–Armitage trend (arm ichida): statistika −3.72, `p = 0.000198`, yo'nalish *kamayuvchi*; xavf farqi `P0 − P2` = 0.909, Newcombe 95% CI [0.453, 0.984];
falsifikatsiya qoidasi bajarilmadi (`falsified: false`). **Bularni tadqiqot natijasi deb o'qimang**, sababi:

1. **Gate (§4).** Qoida o'zi talqinni taqiqlaydi.
2. **P0 maxraji tanlangan.** P0 da maxrajga faqat uzilishi ≥ 3 probe bo'lgan trial'lar kirgan (7/20); tez qayta ko'tarilganlar `no_episode` sifatida chiqarilgan. P0 ning 7/7 si **sekinroq restart'larga shartli**.
3. **P1/P2 maxraji boshqacha tarkibli.** `18` §1: arm A da birinchi epizodlarning 16 tasi injeksiyadan **oldin** boshlanadi — bosimning o'zi sabab bo'lgan `rt_timeout` portlashlari. Maxrajga kirish qoidasi darajalar bo'yicha mexanik farq qiladi.
4. **VR ni bekor qiladigan narsa asosan `contract_fail`** (§6.3), va u dizaynning ichki tarangligiga tayanadi.

Boshqa chiqishlar degeneratlangan va ogohlantirishlar bilan keladi (`analysis.json`, 62 ogohlantirish): RMST (`τ = 8 s`) hamma arm/darajada 8 s (SE 0), fail-slow limbi *baholanmaydi*
(`Δ` ning SE'si nol, §21.1(b)), FR-A 26/77 epizodda aniqlanmagan, `FR-B` hisoblanmaydi (kalibratsiya matritsasi yo'q). `no_action` bilan log-rank `A − no_action` mazmunsiz:
`no_action` da hech qachon restart yo'q.

## 6. Pilot topgan narsalar — muzlatilgan dizaynning zaif joylari — `NATIJA` / `TALQIN`

Bular pilotning haqiqiy qiymati. Har biri **tasdiqlovchi runga qadar** yangi pre-registratsiyada hal qilinishi kerak.

1. **Reference daraja (P0) kuzatilmaydi** (§4.1). `k_f = 3`, `P = 100 ms`, `RestartSec = 100 ms` birgalikda 300 ms dan qisqa uzilishni ko'rmaydi. §20.3 ning farazi va gate qoidasi shunga
   moslanmagan. Hal qilish dizaynni o'zgartirishni talab qiladi (masalan detektor yoki restart parametrlari) — buni **bu pilot hal qilmaydi**.
2. **Probe uzilishi 24/120 trialda** (pilot-001 da 2). 68 uzilishning 55 tasi prober `CsvWriter` ning har 5 s dagi `fsync` ga mos vaqtda boshlanadi (`17`). **Sabab gipoteza, o'lchanmagan**; 13 uzilish bu naqshga to'g'ri kelmaydi. Natija: bunday trial §4 bo'yicha `censored`, ya'ni beshdan biri instrument yo'qotilishi tufayli natijasiz.
3. **`contract_fail` va §3/§4.2 taranglik** (`18` §3). VR-ni bekor qilgan 29 oynada 284 muvaffaqiyatsiz probe, hammasi `rt_timeout` (`T_rt = 50 ms`); restart probe, bystander yoki boshqa invocation **yo'q** — bular haqiqiy §2(b) buzilishlari va reducer §4 ni so'zma-so'z qo'llaydi. Lekin 29 oynadan **8 tasida** hukm 1–2 ta muvaffaqiyatsiz probe'ga tayanadi: §3 shunday qisqa seriyani shovqin (`k_f = 3`) deydi, §4.2 esa bitta probe'ni yetarli deydi. Prober shovqini bunga sabab emas (29 oynadan 3 tasida uzilish yaqinida).
4. **Guard runaway qoidasi P1 va P2 da** 9/120 trialni to'xtatdi (P0 da 0). Bu o'lchangan stavka emas, bitta run.
5. **Frozen matnning ichki ziddiyatlari**, pilot jarayonida topilgan va hujjatlangan: §14.6(4) ↔ §12 ustuvorligi (v1.14), §20.3 farazi (shu hujjat), validator `disposition` ni o'qiydi, `reason` ni emas (v1.14 9.10).

## 7. Jarayon yozuvi — pilot nima uchun ikki marta o'tkazildi — `FAKT`

| topilma | joyi | holat |
|---|---|---|
| generator `WorkingDirectory` yo'q | driver | tuzatildi (smoke), `14` |
| teardown tartibi: guard SIGKILL | driver | tuzatildi, `14` |
| guard trip + istisno yo'li: washout o'tkazib yuborilardi | driver | tuzatildi, `14` §12 |
| host uyqusi VM'ni 11.7 soatga muzlatdi, guest sezmadi | muhit | `07` §7.7, validator tekshiruvi |
| oyna hold ichidami fakti yo'q; probe-gap noto'g'ri manbadan; `t_issue` eskirgan | driver | tuzatildi (v1.13), `15`/`16` |
| validator ustuvorlikni bilmaydi | validator | tuzatildi, simmetrik (v1.14), `17` |
| `progress` ustuni tashlandi, `R_ref` 120/120 yo'q | **orkestrator skripti** | tuzatildi, `18` §2 |
| ikki frozen qiymat qarori (§17.5 O3, §18.6 F2) | PREREG | v1.11 |

## 8. CHEKLOV

- **Bitta mashina, bitta kernel** (`6.6.87.2-microsoft-standard-WSL2`), VM'siz; hech qanday kalibratsiya boshqa kernelda yo'q.
- **n = 20 / yacheyka**, maxrajlar 7–15; CI'lar keng. Pilot ma'lumoti tasdiqlovchi analizga kirmaydi (frozen).
- Birlamchi endpoint **talqin qilinmaydi** (§4). Ikkinchi darajali va sezgirlik chiqishlari degeneratlangan yoki tadqiqotchi.
- Darvoza ikkinchi yiqilishdan keyin o'zgargan (v1.14); asl FAIL hukmi yozuvda.
- Probe uzilishi sababi o'lchanmagan; `fsync` gipotezasi tasdiqlanmagan.
- `aborted_guard` darajasi o'lchangan stavka emas; arm'lar orasidagi farq haqida xulosa yo'q.
- Reduksiya SUT-only ko'rinish orqali (`scripts/pilot/pilot-reduce.py`), `validate.reducer_view` bilan bir xil filtr.
- Host uyqusi runtime'da aniqlanmaydi, faqat post-hoc; 1 s dan qisqa muzlash ushlanmaydi.

## 9. Keyingi qadamlar (tavsiya, qaror egasiga)

1. **Tasdiqlovchi run oldidan** yangi pre-registratsiya: P0 kuzatuvchanligi (§4.1), `T_rt`/single-probe qoidasi (§6.3), `fsync` gipotezasini o'lchash va instrument qarori, guard runaway stavkasi.
2. §20.3 ning farazini va gate qoidasini qayta ko'rib chiqish (injeksiya ishlaganini tekshirish mexanizmi `no_episode` dan alohida bo'lishi kerak).
3. Validator `reason` ni ham o'qishi (v1.14 9.10) — alohida amendment.

## 10. Fayllar va qayta ishlab chiqarish

```
datasets/p1-pilot-002/raw/        xom *.zst, run_meta.json, RAW.SHA256SUMS (yaxlitlik)
datasets/p1-pilot-002/meta/       launcher.log, markerlar, validate.txt (ASL), validate-v114-CORRECTED.txt, clock-watch.log
datasets/p1-pilot-002/derived/    analysis.json, reduce-summary.json, trials/episodes/sweep (*.zst), figures/ (6 SVG + JSON)
datasets/p1-pilot-001-INVALID/    yaroqsiz run, saqlangan, tahlil qilinmaydi
scripts/pilot/                    launcher, kuzatuvchi, pilot-reduce.py
docs/architecture/15,16,17,18     tahlil yozuvlari (validatsiya xatolari, tuzatishlar, VR auditi)
```

Qayta hisoblash: `PYTHONPATH=<repo> python3 scripts/pilot/pilot-reduce.py <run_dir> <out>` → `revix analyze` → `revix figures`
(`scripts/pilot/README.md`). `analysis.json` sha256 yuqorida.
