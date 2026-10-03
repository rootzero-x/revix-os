# 04 — Driver va analiz shartnomasi (MUZLATILGAN)

**Versiya:** `driver-contract/v1.2` | **Holat:** MUZLATILGAN

> **Nega bu birinchi yoziladi:** driver, analiz va figura modullari parallel
> ishlab chiqiladi. Shartnoma oldindan muzlatilmasa, ular bir-biriga mos
> kelmaydigan narsa yozadi. Bu `03-sut-protokoli.md` bilan bir xil usul.
>
> Implementatsiya bu faylni **o'zgartirmaydi**. Nomuvofiqlik topilsa — avval
> shu fayl amendment qilinadi.

---

## Amendment log

Bu fayl **jimgina tahrirlanmaydi** (`CONTRIBUTING.md` §1.1, `DEVELOPMENT.md`
§7). Har o'zgarish shu yerda qayd etiladi, versiya oshiriladi, va oldingi
versiyaning `sha256` i saqlanadi.

### v1.1 → v1.2 (2026-10-02)

| | |
|---|---|
| **v1.1 sha256** | `4a13baed81129416077d446d3e94e5b35bbd8f03d806b77bfbaafab2fc2392cf` |
| **v1.1 git tag** | **`v0.1.1-driver-contract`** — v1.2 integratsiyasidan keyin qo'yildi (v1.1 ni integratsiya qilgan merge `b6dbad2`). Uchala versiya ham taglangan: `v0.1.0-driver-contract`, `v0.1.1-driver-contract`, `v0.1.2-driver-contract` |
| **Sabab** | **uchta mustaqil defekt, barchasi implementatsiya tomonidan topilgan:** (1) §3 ikkita majburiy figura talab qiladi (`downtime_ecdf`, `probe_cost`), lekin §2.2 ularga **ma'lumot bermaydi** — ya'ni shartnomaga mos `analysis.json` §3 ni bajara olmaydi (`agent/figures`, `92eca55`); (2) **`PREREGISTRATION.md` §11 ning fail-slow falsifikatsiya mezoni `analysis.json` dan HISOBLANMAYDI** — u `P0`–`P2` **pressure** kontrastini nomlaydi, §2.2 esa faqat arm kontrastini beradi (`agent/analyze`, `2518e26`); (3) **`boot_id` bu host'da yetarli emasligi O'LCHANDI** — guest PID 1 restart bo'lganda `boot_id` o'zgarmaydi, demak §14.6 invarianti 5 soxta "o'tdi" beradi (`agent/envcheck`, `fe914d6`; shu amendment paytida **mustaqil takrorlandi** — §1.4) |
| **O'zgardi** | §1.1, §1.2 — **`guest_generation`** majburiy maydon; **yangi §1.4** (marker, o'lchov, identifikator va abort qoidasi); §1.3 — yangi majburiyatlar 13–16 va ikki tuzatilgan havola; §2.1 — kirish flaglari jadvali, yangi ixtiyoriy **`--events`** va **`--episodes`**, `probe_cost` provenance zanjiri; §2.2 — `time_unit`, `t_trial_us`, `t_trial_formula`, provenans kalitlari, `downtime` ning ichki shakli + ixtiyoriy `ecdf`, yangi `probe_cost`, `survival.censoring.n_undetermined`, **`survival.rmst.pressure_difference` va `*.by_pressure_band`**, `contrast` / `ci_level` / `basis` / `uncorrected` / `exclusions.n_*`; §2.3 — yangi majburiyatlar 10–19; **yangi §2.4–§2.10**; §3.1 — figura **degradatsiya** qoidalari; §4.2-3 va §4.6 — `stream` CHEKLOVI yopildi; §4.3 — `overhead_us` qatori; **yangi §4.7** (reducer kirishi bitta target/unit); §5.1 — bo'lim havolasi (v1.4 da qatorlar siljidi); §5.4 — horizon toleransi `P` deb raqamlandi; **yangi §7** (o'lchangan tuzoqlar); **yangi §8** (kod-vs-kod ochiq nomuvofiqliklari) |
| **O'zgarMADI** | hech bir ta'rif, chegara, metrika, statistik test yoki **falsifikatsiya mezoni**. **§11 ning fail-slow mezoni va uning 20% chegarasi tegilmadi** — faqat uni hisoblash uchun transport qo'shildi (§2.10); `τ = 8 s` o'zgarmadi; `survival.rmst.by_arm` **saqlandi**. **§4.1–§4.6 ning maydon nomlari jadvali o'zgarmadi**; **§5.2 ning `T_trial` formulasi va 40.1 s o'zgarmadi** *[2026-10-03 tuzatma: bu bayonot faqat **v1.1 → v1.2** oralig'iga tegishli edi. 40.1 s hozirgi qiymat **emas** — `preregistration/v1.11` (`hold_cap_s` 12 s → 13 s) dan keyin default `T_trial` = **41.1 s**; formula o'zgarmadi. Qarang: "v1.2 ikkinchi revizyasi (2026-10-03)" pastda]*; **§6 (`matplotlib`) o'zgarmadi**; §1.1 ning mavjud maydonlari, §1.3 ning 1–12 majburiyatlari, §2.2 ning `primary.cells` / `falsification_rule` / `fr_b` / `sensitivity` grid'i va §3 ning figura ro'yxati o'z holida. **`SCHEMA_VERSION` SILJIMAYDI** — qo'shilgani faqat **payload va chiqish maydonlari**, yangi record turi ham, yangi enum qiymati ham yo'q (§2.2: `schema_version: 1`). §8 dagi ikki nomuvofiqlik **HAL QILINMADI**, faqat qayd etildi. `PREREGISTRATION.md` va `INSTALLATION.md` **tahrirlanmadi**; `revix/*.py` **tahrirlanmadi** |
| **Yig'ilgan ma'lumot** | **yo'q** — hech qanday eksperiment ishga tushirilmagan va hech qanday ma'lumot mavjud emas, demak **eski ta'riflar ostida qayta hisoblanadigan narsa yo'q** |

**Bu amendment nega qonuniy:** uchala o'zgarish ham **transport** qatlamiga
tegadi — qaysi qiymat qaysi maydonda yetkazilishiga — **ta'riflarga emas**.

1. `probe_cost` va ECDF `PREREGISTRATION.md` §8.2 va §10.2 da **allaqachon
   talab qilingan**; v1.2 ularga faqat yo'l ochadi.
2. §11 ning mezoni **o'zgarmadi** — na kontrast (`P0`–`P2` ni §11 **o'zi**
   nomlagan), na `τ = 8 s`, na 20% chegarasi. Qo'shilgani faqat uni
   **hisoblash uchun joy**. Mezonni hisoblab bo'lmasligi — bo'shliq;
   mezonni o'zgartirish bo'lardi, **buzilish**. v1.2 birinchisini yopadi.
3. Guest generatsiya markeri §1 ning `boot_id` kafolatini
   **almashtirmaydi**, uni **to'ldiradi** — `boot_id` saqlanadi va majburiy
   qoladi.

Hali ma'lumot yig'ilmagan, demak "ta'riflarni natijani ko'rgandan keyin
tanlash" xavfi yo'q. `CONTRIBUTING.md` §3 bajarildi: defektlarni
`agent/figures`, `agent/analyze` va `agent/envcheck` **xabar qildi**, hujjat
jimgina "to'g'rilanmadi", va §8 dagi ikki **kod-vs-kod** ziddiyati
**hal qilinmasdan** ochiq savol sifatida qayd etildi.

#### v1.2 revizyasi (2026-10-02) — FAKTIK tuzatish, TALAB o'zgarmadi

**Versiya OSHIRILMADI va oshirilmasligi kerak.** Bu revizya shartnomaning
birorta **talabini** o'zgartirmaydi: na maydon nomi, na kalit, na majburiyat,
na degradatsiya qoidasi. U faqat **boshqa fayllar haqidagi bayonotni**
haqiqatga moslashtiradi — v1.2 yozilayotgan paytda ikki narsa yo'q edi,
yozib bo'lingach paydo bo'ldi.

| nima | v1.2 asl matnida | hozir |
|---|---|---|
| `analyze.py --events` / `--episodes` (§2.1) | *"hali yo'q — shartnomaning talabi"* | **bor** (`agent/analyze`, commit `5641a75`); to'liq flag ro'yxati va `revix analyze` uzatishi §2.1 da |
| budjet konstantasining regressiya qulfi (§2.7) | *"bunday test hozir YO'Q"* | **bor**: `test_probe_cost_budjet_konstantasi_proberdagi_bilan_bir_xil` (`tests/unit/test_analyze.py:1186`) |
| `probe_cost` bo'shlig'ining dalili (§2.7) | `test_zanjir_figura` **ishdan chiqadi** | **o'tadi**, to'ldirilgan `probe_cost` figurasi bilan — zanjir ulandi |
| `driver-contract` git tag'i (yuqoridagi jadval) | *"hali birorta tag qo'yilmagan"* | **uchalasi ham taglangan** (`v0.1.{0,1,2}-driver-contract`) |

**Hujjat `sha256` i o'zgaradi, versiya esa o'zgarmaydi** — shuning uchun bu
yerda ochiq qayd etiladi, aks holda provenans zanjirida hisobga olinmagan
o'zgarish qolardi:

| | |
|---|---|
| v1.2 (merge qilingan asl matn, taglangan) | `fa6e1725ea6f0d818c2d029ad2bcbb8ffcef9e6e17da48ca1a1db080642d14f4` |
| v1.2 (shu revizyadan keyin) | commit xabarida beriladi |

> **NEGA versiya oshirilmaydi:** `CONTRIBUTING.md` §1.1 ning amendment
> protsedurasi **ta'rif, metrika yoki talab** o'zgarganda versiya oshirishni
> talab qiladi. Bu yerda o'zgargan narsa — hujjatning **boshqa modullar
> holati haqidagi kuzatuvi**. Versiyani oshirish *"shartnoma o'zgardi"*
> degan **yolg'on signal** berardi va `agent/driver` /
> `agent/analyze` / `agent/figures` ni mavjud bo'lmagan farqni izlashga
> majburlardi. Lekin o'zgarishni **yozmaslik** ham mumkin emas: hujjat
> yolg'on bayonotni olib yurardi, va *"ishga tushirilmagan test o'tdi deb
> yozilmaydi"* qoidasining teskari tomoni ham shu — **o'tgan test
> yo'q deb yozilmaydi**.

#### v1.2 ikkinchi revizyasi (2026-10-03) — HISOBLANGAN qiymat siljidi, QOIDA o'zgarmadi

**Versiya OSHIRILMADI.** Bu revizya shartnomaning birorta **qoidasini**
o'zgartirmaydi: §5.2 ning formulasi, §5.4 ning hosilasi (derivation) va
invarianti, `PROBE_PERIOD_US`, `SCHEMA_VERSION`, har bir record turi va har
bir enum aynan o'sha. O'zgargan narsa — formulaning **default timeline'da
beradigan qiymati**, va u o'zgargan sababi shu fayldan **tashqarida**.

| | |
|---|---|
| **Sana** | 2026-10-03 |
| **Sabab** | `PREREGISTRATION.md` §17.5 **O3** bo'yicha hal qilindi: `hold_cap_s` **12 s → 13 s** (amendment `preregistration/v1.11`, `main` ga merge qilingan, hali taglanmagan). §5.2 ning `T_trial = t_pressure_off + w_stab_s + P` formulasi `TrialTimeline` dan **hisoblanadi**; `hold_s` default'i `HOLD_CAP_S` (`revix/schedule.py:96`, `13.0`) bo'lgani uchun `t_pressure_off` 1 s ga surildi. **Hosila qiymat siljidi, hech qanday qoida o'zgarmadi.** |
| **Hisob (kod'dan o'qildi va ishga tushirildi)** | `t_hold_start = preflight 5 + baseline 10 + ramp 5 = 20.0 s`; `t_pressure_off = 20.0 + hold 13.0 = 33.0 s`; `T_trial = 33.0 + w_stab 8.0 + P 0.1 = 41.1 s = 41 100 000 µs`; `total_s = 33.0 + washout 20.0 = 53.0 s`. `driver.t_trial_us(TrialTimeline())` = `41100000` |
| **O'zgardi** | §5.2 "Pilot qiymatlari" jadvali: `t_pressure_off` **32.0 → 33.0 s**; **`T_trial` 40.1 s = 40 100 000 µs → 41.1 s = 41 100 000 µs**; `total_s` **52.0 → 53.0 s**. §5.3 ning "Busiz nima buzilardi" misolidagi `total_s` (52 s → 53 s) va `t_pressure_off` (32 s → 33 s). Shuningdek §5.1 va §5.5 dagi o'tgan zamon bayonotlari yonida **sanalangan tuzatma** qo'shildi (qarang pastda) |
| **O'zgarMADI** | §5.2 ning **formulasi** va majburlanadigan invarianti `t_verify_end_earliest ≤ T_trial ≤ total_s` (`31.0 ≤ 41.1 ≤ 53.0` bajariladi); `t_inject` **23.0 s** va `t_verify_end_earliest` **31.0 s** (hold boshlanishi 20.0 s da qoladi); `w_stab_s` 8.0 s; `P` = `PROBE_PERIOD_US` = 100 000 µs; §5.4 ning barcha 6 majburiyati va `trial_end` toleransi `P`; `W_stab` sweep grid'i `{8,10,30,60,120}` va §2.3-7 (`60` va `120` hamon horizon'dan katta, `30` kichik); `τ = 8 s`; `SCHEMA_VERSION`; **har bir record turi va har bir enum qiymati**; §1–§4, §6–§8. `PREREGISTRATION.md`, `revix/*.py` va testlar bu revizya bilan **tahrirlanmadi** |
| **Yig'ilgan ma'lumot** | **yo'q** — hech qanday eksperiment ishga tushirilmagan, **birorta P1 trial ham o'tkazilmagan**. Demak **eski qiymat (40.1 s) ostida qayta hisoblanadigan narsa yo'q**: horizon hech bir run'da `run_meta.t_trial_us` ga yozilmagan va hech bir trial u bo'yicha censor qilinmagan |

**Hujjat `sha256` i o'zgaradi, versiya esa o'zgarmaydi** — shuning uchun bu
yerda ochiq qayd etiladi:

| | |
|---|---|
| v1.2 (birinchi revizyadan keyin, **shu revizyadan oldingi** matn; commit `7cc8178`) | `5ceae8076fa9f69e4b9bed4f1f5a13247dabcf63e1af72584030c29aefd1ea59` |
| v1.2 (shu revizyadan keyin) | commit xabarida beriladi |

`v0.1.2-driver-contract` tegi (`fa6e1725…`, v1.2 ning asl matni) **ko'chirilmaydi**
va yangi teg qo'yilmaydi: teg versiyani belgilaydi, versiya esa o'zgarmadi.

**Tarixiy matn nega o'z holida qoldi.** Quyidagi o'rinlar o'z davri uchun
**to'g'ri** bayonot edi va amendment log'ning o'tgan yozuvlarini qayta yozish
muzlatilgan hujjat intizomiga zid. Ular **o'chirilmadi** — ularning yoniga
sanalangan tuzatma qo'shildi, shunda o'quvchi ikkala qatlamni ham ko'radi:

| o'rin | asl matn | nega o'z holida | tuzatma |
|---|---|---|---|
| v1.1 → v1.2 yozuvi, **O'zgarMADI** qatori | *"§5.2 ning `T_trial` formulasi va 40.1 s o'zgarmadi"* | **v1.1 → v1.2** oralig'ida rost edi (v1.2 `hold_cap_s` ga tegmagan); lekin u **hozirgi** qiymat haqida emas | qator oxirida `[2026-10-03 tuzatma: …]` |
| §5.1, *"Lekin `PREREGISTRATION.md` …"* xatboshisi | *"hold 12 s … ≈ 52 s"* — `PREREGISTRATION.md` §9.4 ning o'sha paytdagi matnidan **iqtibos** | `preregistration/v1.4` ni tekshirish paytida §9.4 shunday yozgan; iqtibos o'z davrining dalili | jumla oxirida qavsli izoh: §9.4 endi 13 s va ≈ 53 s |
| §5.5 oxiridagi **"v1.2 tekshiruvi"** bloki | *"`hold_cap_s = 12 s` … o'zgarmadi — demak `T_trial = 40.1 s` ham o'zgarmaydi"* | `preregistration/v1.4` uchun **to'g'ri** xulosa edi | blokdan keyin yangi **"2026-10-03 tuzatma"** bloki |

> **NEGA versiya oshirilmaydi:** shu fayl o'zining yuqoridagi qoidasiga
> ko'ra (*"ta'rif, metrika yoki talab o'zgarganda"* oshiriladi) — bu yerda
> **talab o'zgarmadi**. §5.4-1 *"`T_trial` hisoblanadi, kodga yozilgan
> konstanta sifatida berilmaydi"* deb **raqamni emas, formulani** muzlatadi;
> §5.2 jadvali esa formulaning **default'dagi natijasi** (*"`TrialTimeline()`
> default'laridan ishga tushirilib hisoblangan"*), ya'ni kuzatuv, talab emas.
> Haqiqiy versiya oshishi `PREREGISTRATION.md` da bo'ldi
> (`preregistration/v1.11`) — shartnoma uni **kuzatadi**. Versiyani
> oshirish `agent/driver` / `agent/analyze` / `agent/figures` ga mavjud
> bo'lmagan **shartnoma farqini** izlashga majbur qiluvchi yolg'on signal
> bo'lardi. Lekin qiymatni **yozmaslik** ham mumkin emas: validator
> (`t_trial_formula_mismatch … != 41100000 us (kontrakt v1.1 §5.2)`) allaqachon
> 41.1 s ni talab qiladi, hujjat esa 40.1 s ni aytib turardi — ya'ni hujjat
> kod bilan **ziddiyatda** qolardi.

### v1 → v1.1 (2026-10-02)

| | |
|---|---|
| **v1 sha256** | `f47f36b7fa23b4de42ba25e49bcf91cb9f9c96ddd1909b82203e098dc1c9d637` |
| **v1 git tag** | **yo'q** — `driver-contract/v1` uchun tag qo'yilmagan; muzlatish commit'i `7244849` ("docs: freeze driver and analysis contract v1") |
| **Sabab** | §1.2 dagi record maydon nomlari `revix/reduce.py` ning haqiqatan o'qiydigan nomlari bilan **mos kelmaydi**, va `T_trial` (recovery horizon) hech qayerda raqamlanmagan |
| **O'zgardi** | §1.2 dagi `trial_begin` maydon nomi (`pressure_level` → `pressure_band`) va `unit_state` izohi; **yangi §4** (normativ maydon nomlari jadvali); **yangi §5** (`T_trial` ta'rifi); **yangi §6** (`matplotlib` bog'liqligi qayd etildi) |
| **O'zgarMADI** | hech bir ta'rif, chegara, metrika, statistik test, falsifikatsiya mezoni yoki disposition enum'i. §1.1, §1.3, §2 (butun `analysis.json` sxemasi va analiz majburiyatlari), §3 ning figura ro'yxati va rang qoidasi **o'zgarmadi**. `PREREGISTRATION.md` **tahrirlanmadi** (§5 ga qarang). `revix/reduce.py` **tahrirlanmadi** (§4.1 ga qarang) |
| **Yig'ilgan ma'lumot** | **yo'q** — hech qanday eksperiment ishga tushirilmagan va hech qanday ma'lumot mavjud emas. Shuning uchun **eski ta'riflar ostida qayta hisoblash talab qilinmaydi**: qayta hisoblanadigan narsa yo'q |

**Bu amendment nega qonuniy:** o'zgarish faqat **maydon nomlarining
yozilishiga** va oldin umuman raqamlanmagan bitta parametrga tegadi. Birorta
ham o'lchov ta'rifi (VR bandlari, FR-A/FR-B, uchala downtime, disposition
enum'i) o'zgarmadi, va hali ma'lumot yig'ilmagan — demak "ta'riflarni natijani
ko'rgandan keyin tanlash" xavfi mavjud emas. `CONTRIBUTING.md` §3 "o'zingiz
tuzatmang" qoidasi bajarildi: nomuvofiqlik jimgina to'g'rilanmadi, balki shu
amendment orqali hal qilindi.

---

## 1. Driver nima ishlab chiqaradi

Bitta run = bitta katalog. Fayl nomlari qat'iy:

```
<run_dir>/
├── events.jsonl        barcha hodisa record'lari (envelope bilan)
├── probe.csv           probe_sample oqimi (prober yozadi)
├── psi.csv             psi_sample oqimi (psi_sampler yozadi)
├── guard.jsonl         guard'ning O'Z oqimi (mustaqil jarayon)
├── pressure.jsonl      pressure generatorining oqimi
└── run_meta.json       bitta obyekt, run boshida yoziladi
```

**`datasets/` append-only.** Driver mavjud run katalogiga yozmaydi; katalog
allaqachon bo'lsa — xato.

### 1.1 `run_meta.json` — majburiy maydonlar

```
run_id, session_id, boot_id, started_real_us, started_mono_us,
preregistration_sha256, preregistration_version,
git_commit, git_dirty, rng_seed, schedule_digest,
uname, systemd_version, cpu_model, cpu_count, mem_total_kb,
cgroup_delegated_controllers, oomd_effective (user@ va -.slice uchun),
governor, scaling_driver, python_version, module_versions,
units_show (har unit uchun TIRIK paytida olingan systemctl show dump'i),
schedule (to'liq, schedule.to_json() dan)
```

`units_show` **unit tirik paytida** olinishi shart —
`01-muhit-tekshiruvlari.md` §4 dagi tuzoq: o'chgan unit uchun `systemctl show`
rc=0 va 268 qator **default** qaytaradi.

**v1.1 da qo'shildi:** `run_mode` va `t_trial_us` ham majburiy —
`run_mode` ni `validate.check_run_meta()` o'qiydi (`revix/validate.py:716`),
`t_trial_us` esa §5 dagi hisoblangan horizon. Ikkisi ham §4.3 jadvalida.

**v1.2 da qo'shildi — `guest_generation` (majburiy):**

```
boot_id              (saqlanadi -- §1 talabi, O'ZGARMADI)
guest_generation     dict:
   pid1_starttime_ticks   /proc/1/stat 22-maydon -- IDENTIFIKATOR KALITI
   clk_tck                getconf CLK_TCK -- tick -> sekund
   uptime_s               /proc/uptime 1-maydon  } faqat ODAM O'QISHI uchun,
   pid1_etimes_s          ps -p 1 -o etimes=     } IDENTIFIKATORGA KIRMAYDI
```

`guest_generation` **`run_meta` da va har `env_snapshot` da** majburiy
(§1.2), va butun run davomida **identifikatori o'zgarmasligi** shart. To'liq
sabab, o'lchov va abort qoidasi: **§1.4**.

> **`boot_id` OLIB TASHLANMAYDI va majburiy qoladi.** U to'g'ri va hali ham
> zarur (`PREREGISTRATION.md` §1, §14.6-5) — bu host'da shunchaki **yetarli
> emas**. Keyingi o'quvchi markerni "ortiqcha" deb o'chirmasligi uchun shu
> gap ochiq yozildi.

### 1.2 Trial hodisalari ketma-ketligi (har trial uchun)

```
trial_begin      arm, fault_class, pressure_band, position_in_block,
                 planned_timeline   (trial_id va block_index — ENVELOPE'da)
env_snapshot     (trial boshida) + guest_generation (§1.4) -- har trial
                 uchun MAJBURIY, identifikator kaliti
                 guest_generation.pid1_starttime_ticks
baseline_window  R_ref o'lchangan oyna: mono_us_begin/end, throughput
fault_inject     mono_us_before_call, mono_us_after_call, fault_id, kind, params
fault_effective  t_fault_effective va uning manbasi (probe|oom_kill|...)
action           action_id, actor, action_class, t_issue/t_begin/t_exec,
                 policy_delay_us (L_dec dan ALOHIDA)
action_defer     action o'rniga kechiktirilganda
actor_signal     success (aktorning O'Z da'vosi) + actor_signal_source
unit_state       (units.UnitWatcher dan; XOM systemd nomlari SAQLANADI va
                 snake_case nomlar QO'SHILADI — §4.3; recv_mono_us alohida)
cgroup_events    memory.events / memory.swap.events delta'lari
env_snapshot     (trial oxirida)
trial_end        disposition (§12 yopiq enum, AYNAN BITTA) + reason
                 + overhead_us (o'lchangan qo'shimcha vaqt, majburiyat 9)
```

> **v1.1:** `trial_begin` dagi maydon nomi `pressure_level` emas,
> **`pressure_band`** — `revix/reduce.py:389` aynan shuni o'qiydi. Sabab va
> to'liq moslik jadvali: **§4**. Bu yerdagi ro'yxat qisqa xulosa; ziddiyat
> bo'lsa **§4 jadvali ustun**.

`detection`, `contract_restored`, `probe_overrun` — prober yozadi.
`guard_event` — guard yozadi (`trial_id` YO'Q, u mustaqil jarayon; atributsiya
monotonic vaqt bo'yicha, shuning uchun `boot_id` invarianti muhim).

### 1.3 Driver majburiyatlari

| # | majburiyat | nega |
|---|---|---|
| 1 | **Guard BIRINCHI start, OXIRGI stop** | qotib qolgan driver guard'ni o'chira olmasligi kerak — `00-pilot-topologiya.md` **§3.1 mitigation (b)** (*"Driver'dan ALOHIDA process … Birinchi start, oxirgi stop"*, `✅ majburiy`) |
| 2 | Guard ishga tushmasa — run **boshlanmaydi** | fail-closed; o'sha §3.1 mitigation (b) ni guard'ni **majburiy** deb belgilaydi |
| 3 | Har run boshida `units.clear_runtime_drop_ins()` | oldingi run'ning `MemoryHigh=` sini meros olmaslik (§8 kontaminatsiya) |
| 4 | `units.require_clean()` pre-flight | qoldiq holat jimgina kontaminatsiya qilmasligi |
| 5 | Har trial uchun **aynan bitta** `trial_end` + disposition | §12; jimgina eksklyuziyani oldini oladi |
| 6 | `schedule.TrialTimeline` invariantlari **majburlanadi** | pressure cap = oomd himoyasi, afzallik emas |
| 7 | Prober va psi_sampler `revixmon.slice` da | §8.2 feedback artefakti |
| 8 | SUT/bystander/generator `revixlab.slice` da | o'lchanadigan scope |
| 9 | Trial qo'shimcha vaqti **o'lchanadi va yoziladi** | §9.4 v1.3: taxmin qilinmaydi |
| 10 | `--dry-run` hech narsa ishga tushirmaydi, jadvalni chiqaradi | randomizatsiya ko'zdan kechiriladi |
| 11 | **v1.1:** har record'ning maydon nomi §4.3 jadvaliga **aynan** mos keladi | nomi boshqa bo'lgan maydon `None` bo'lib o'qiladi, va `None` jimgina "o'lchanmadi" ga aylanadi |
| 12 | **v1.1:** `T_trial` **hisoblanadi va `run_meta` ga yoziladi** (§5) | jimgina konstanta yo'q; horizon qayd etilgan run parametri |
| 13 | **v1.2:** guest generatsiya markeri `run_meta` da **va** har `env_snapshot` da; marker o'zgarsa run **darhol abort**, trial `harness_error` | §1.4: `boot_id` bu host'da yetarli emas, va soxta "o'tdi" validatorsizlikdan yomonroq |
| 14 | **v1.2:** prober `--report-cost` bilan ishga tushiriladi | §8.2 probe narxini talab qiladi; §2.2 `probe_cost` ning manbai (§2.1) |
| 15 | **v1.2:** xom fayllar **barcha target va unit** ni saqlaydi; reducer'ga berilayotgan narsa **SUT ga filtrlanadi** (§4.7) | `reduce.split_trials` faqat `trial_id` bo'yicha guruhlaydi; bystander probe'lari filtrlanmasa `R_ref`, `D_probe`, `D_eff` va VR 3/4-bandlari buziladi |
| 16 | **v1.2:** `trial_end` o'lchangan qo'shimcha vaqtni `overhead_us` da olib yuradi | majburiyat 9 ning aniq maydoni; §9.4 v1.3 "o'lchanadi, taxmin qilinmaydi" |

### 1.4 Guest generatsiya markeri (v1.2) — `boot_id` yetarli emas

#### Defekt

`PREREGISTRATION.md` §1 `boot_id` ni **kafolat** qilib qo'yadi: *"Monotonic
qiymatlar faqat bitta boot ichida taqqoslanadi; `boot_id` bu shartni
tekshirib bo'ladigan qiladi."* §14.6 invarianti 5 esa uni majburlaydi:
*"`boot_id` sessiya ichida o'zgarmas."*

**Bu host'da kafolat ishlamaydi.** Guest PID 1 (systemd) qayta ishga
tushadi, systemd holati (unit'lar, `InvocationID`, `NRestarts`) nolga
qaytadi — va ba'zi hollarda `CLOCK_MONOTONIC` ning o'zi ham nolga qaytadi —
lekin **`boot_id` o'zgarmaydi**. Natijada run ichida **ikki taqqoslanmaydigan
vaqt boshlanishi** bo'ladi va **mavjud barcha invariant o'tadi**.

> **NEGA bu validatorsizlikdan yomonroq:** §14.6 ning butun mantiqi
> *"validatsiyadan o'tmagan run analiz qilinmaydi"* ga tayanadi. Soxta "o'tdi"
> buzilgan davomiylikni to'g'ridan-to'g'ri birlamchi endpoint'ga yuboradi, va
> buzilish **ko'rinmaydi**. Yo'q validator hech bo'lmasa ishonch bermaydi.

#### O'lchov

**(1) `agent/envcheck` o'lchovi** (branch `agent/envcheck`, commit `fe914d6`):
oxirgi `wsl.exe` klient jarayoni chiqqandan keyin distro 10.3–15.3 s ichida
"running" ro'yxatidan tushadi; ~26 s keyin transient `sleep 600` uniti
yo'qolgan (`LoadState=not-found`), PID 1 `etimes` = 7 s bo'lgan holda VM
uptime 551 s, user manager PID 241 → 238. **Shu restart bo'ylab `boot_id`
aynan bir xil qoldi.**

**(2) Shu amendment paytida mustaqil takrorlandi** (2026-10-02, shu Kali
distro'si, `wsl.exe -d kali-linux`; buyruqlar: `cat /proc/uptime`,
`cat /proc/1/stat` 22-maydon, `getconf CLK_TCK`, `ps -p 1 -o etimes=`,
`cat /proc/sys/kernel/random/boot_id`):

| o'qish | `uptime_s` | `pid1_starttime_ticks` | `pid1_etimes_s` | `boot_id` |
|---|---|---|---|---|
| A | `24.32` | **`83`** (= 0.83 s) | `23` | `a42ad70a-f548-4b37-b6fb-5ee8584eef9d` |
| B (≈1 daqiqa keyin) | — | **`6388`** (= 63.88 s) | **`18`** | `a42ad70a-f548-4b37-b6fb-5ee8584eef9d` — **AYNAN BIR XIL** |
| C (≈30 s keyin) | — | `6388` | `50` | — |

`clk_tck = 100` uchala o'qishda.

**A → B oralig'ida PID 1 qayta ishga tushdi:** start markeri `83` dan `6388`
ga o'zgardi va PID 1 ning yoshi **orqaga ketdi** (`23` → `18` s), **`boot_id`
esa o'zgarmadi.** B → C esa normal qarish (`18` → `50` s, marker o'zgarmagan),
ya'ni marker bitta generatsiya ichida barqaror. Bu `agent/envcheck` dan
**mustaqil** tasdiq.

**Qo'shimcha kuzatuv (juftlik olinmagan, shuning uchun o'lchov emas):**
A o'qishidagi `uptime_s = 24.32` shu sessiyada bir necha daqiqa oldin
muvaffaqiyatli bajarilgan WSL buyruqlaridan **keyin** olingan — demak oraliqda
uptime hisoblagichining O'ZI ham nolga qaytgan. Ya'ni ikki xil buzilish
mavjud:

| rejim | nima bo'ladi | nima buziladi | marker qaysi maydoni tutadi |
|---|---|---|---|
| **A** — butun guest/VM restart | `/proc/uptime` va `CLOCK_MONOTONIC` nolga qaytadi | **barcha davomiylik** — run ichida ikki vaqt boshlanishi | `uptime_s` **kamayadi** |
| **B** — faqat PID 1 restart (VM tirik) | uptime o'sishda davom etadi, lekin systemd holati nolga qaytadi | `NRestarts` / `InvocationID` baseline'lari va `units_show` dump'i | `pid1_starttime_ticks` **o'zgaradi**, `pid1_etimes_s` **orqaga ketadi** |

> **NEGA ikkita maydon kerak, bittasi emas:** `pid1_starttime_ticks` **boot'dan
> beri** tick'da o'lchanadi, demak A rejimida yangi boot'da yana kichik qiymat
> bo'lishi mumkin — ya'ni u yolg'iz holda A ni ishonchli ajratmaydi.
> `uptime_s` esa B rejimida uzluksiz o'sadi, demak u yolg'iz holda B ni
> ko'rmaydi. **Juftlik ikkala rejimni ham qoplaydi.** `pid1_etimes_s`
> hisobga kirmaydi — u `ps -p 1 -o etimes=` dan olingan **odam o'qiydigan
> kross-tekshiruv**, va aynan u restart'ni birinchi ko'rsatgan.

#### Abort qoidasi (normativ)

**Maydon nomi:** `guest_generation` (`validate.GUEST_MARKER_FIELD`,
`revix/validate.py:166`). **Identifikator kaliti:**
`pid1_starttime_ticks`; qabul qilinadigan aliaslar —
`starttime_ticks`, `pid1_starttime`, `starttime`
(`validate.GUEST_STARTTIME_KEYS`, `revix/validate.py:169`), yoki
`guest_generation` ning o'zi **yalang'och skalyar** bo'lsa, o'sha qiymat.

> **NORMATIV: `uptime_s` va `pid1_etimes_s` identifikatorga KIRMAYDI.** Ular
> **faqat odam o'qishi** uchun olib yuriladi.
>
> **NEGA:** ikkisi ham **uzluksiz o'zgaradi** — har o'qishda boshqa qiymat.
> Agar ular identifikatorning bir qismi bo'lsa, taqqoslash **har trial'da**
> ishdan chiqardi, ya'ni tekshiruv doimo "guest restart" deb qichqirardi.
> Har doim ishlaydigan tekshiruv — **tekshiruvsizlikdan yomonroq**: u
> o'chirib qo'yilardi, va u bilan birga haqiqiy restart'ni tutadigan yagona
> mexanizm ham ketardi. Shuning uchun identifikator **faqat** generatsiya
> ichida **qotib turadigan** qiymat: PID 1 ning `starttime` i.
>
> `uptime_s` va `pid1_etimes_s` baribir yoziladi, chunki ular §1.4 ning
> o'lchov jadvalini odam uchun o'qiladigan qiladi (`etimes` aynan restart'ni
> birinchi ko'rsatgan qiymat) va A/B rejimini **post-hoc** ajratishga imkon
> beradi.

Identifikator butun run davomida **o'zgarmas** bo'lishi SHART:

| # | shart | natija |
|---|---|---|
| 1 | `guest_generation` identifikatori o'zgardi | `guest_restarted`, **`error`** (`revix/validate.py:1395`) — run **darhol abort**, joriy trial `harness_error` |
| 2 | identifikator **o'qilmaydi** (kutilgan kalitlardan birortasi yo'q) | `guest_generation_unreadable`, `error` — restart aniqlanmaydi, demak run ishonchsiz |
| 3 | `boot_id` o'zgardi | mavjud `check_boot_id` (§14.6-5) — klassik reboot |

> **Implementatsiya holati:** `agent/validate` invariantni **yetkazdi**
> (`check_guest_generation`, `revix/validate.py:1329`; `validate_run` ro'yxatida
> ro'yxatdan o'tgan) va `agent/driver` shu shaklda emit qiladi. Bu bo'lim
> ularni **formallashtiradi**, yo'naltirmaydi.
>
> **NEGA abort, ogohlantirish emas:** reset'ning ikki tomonidagi ma'lumotni
> **birlashtirib bo'lmaydi**. Davom etish buzilgan davomiyliklarni jimgina
> analizga qo'shardi; `None` emas, **noto'g'ri raqam** chiqardi — bu loyihada
> mavjud eng yomon natija turi.
>
> **NEGA `env_snapshot` da ham, nafaqat `run_meta` da:** `run_meta` faqat run
> boshida yoziladi, demak u yolg'iz holda uzilishni faqat **run oxirida** va
> faqat *"qaerdadir bo'ldi"* darajasida ko'rsatardi. `env_snapshot` har trial
> boshida va oxirida yozilganda uzilish **aniq trial'ga lokalizatsiya
> qilinadi** — ya'ni kampaniyaning qancha qismi omon qolgani aniqlanadi.
> Lokalizatsiyasiz butun run tashlanardi.

#### Qamrov — nima o'zgarmaydi

- **`boot_id` saqlanadi va majburiy qoladi** (§1.1). Marker uni
  **almashtirmaydi**, **to'ldiradi**.
- Bu **payload maydoni**, ya'ni **yangi record turi ham, yangi enum qiymati
  ham emas**. `PREREGISTRATION.md` §14.3 record turlari ro'yxati va §12
  disposition enum'i **tegilmaydi**, demak **`SCHEMA_VERSION` siljimaydi**
  (`revix/schema.py:25`: `SCHEMA_VERSION = 1`).
- `harness_error` **mavjud** disposition (`schema.DISPOSITIONS`,
  `revix/schema.py:258`), yangi qiymat qo'shilmadi.
- `PREREGISTRATION.md` **tahrirlanmadi.** §1 va §14.6-5 ning `boot_id`
  kafolati bu host'da yetarli emasligi pre-registration'ning o'z
  bo'shlig'i va u yerda ham amendment talab qiladi — bu **boshqa agentning**
  ishi. Ziddiyat bo'lsa `PREREGISTRATION.md` **ustun** (§5.5 bilan bir xil
  qoida).

---

## 2. Analiz moduli nima ishlab chiqaradi

`revix/analyze.py` **qat'iy offline**: `reduce.py` chiqishini + `stats.py` ni
oladi, pre-registration §10 dagi analizni bajaradi.

### 2.1 Kirish

| flag | holat | nima |
|---|---|---|
| `--trials PATH` | **majburiy** | `reduce.py` ning `trial_metrics` record'lari (JSONL) |
| `--run-meta PATH` | **majburiy** | `run_meta.json` |
| `--sweep PATH` | ixtiyoriy | `sweep_cell` record'lari (§4 sensitivity) |
| **`--events PATH`** | **v1.2, ixtiyoriy** | xom `events.jsonl` — **faqat** `prober_stop.cost` uchun (§2.7) |
| **`--episodes PATH`** | **v1.2, ixtiyoriy** | `reduce.py` ning `episodes.jsonl` i — per-action / per-episode FR-A uchun (§2.9) |

> **NEGA ikki yangi flag "qat'iy offline" ni buzmaydi:** §2 ning talabi —
> o'lchanayotgan tizimga **tegmaslik**. Fayldan o'qish unga tegmaydi, va
> `reduce.py` ning o'zi ham aynan shunday o'qiydi (`RawRun.load`). Ikkisi ham
> **ixtiyoriy**: ular bo'lmasa `analyze.py` tegishli bo'limni **chiqaradi**
> va sababni `warnings` ga yozadi — hech narsa taxmin qilinmaydi.
>
> **IMPLEMENTATSIYA HOLATI (2026-10-02, v1.2 revizyasi):** ikkala flag ham
> **yetkazildi** (`agent/analyze`, commit `5641a75`). `revix/analyze.py`
> ning to'liq ro'yxati: `--trials` (`:1794`), `--run-meta` (`:1796`),
> `--out` (`:1797`), `--sweep` (`:1798`), **`--episodes`** (`:1800`),
> **`--events`** (`:1803`), `--json` (`:1806`). `revix analyze` ikkisini
> ham uzatadi (`revix/cli.py:2262`–`:2265`; flaglar `:2365` va `:2370` da
> e'lon qilingan).

#### v1.2 — `probe_cost` provenance zanjiri (revizya: zanjir ULANDI)

Zanjir to'rt bo'g'inda tekshirildi:

| bo'g'in | holat | dalil |
|---|---|---|
| prober raqamni **hisoblaydi** | ✅ bor | `Prober.cost_report()` `core_percent`, `core_fraction`, `budget_percent`, `cpu_us_per_probe`, `budget_exceeded` beradi (`revix/prober.py:757`, `:775`, `:778`); budjet konstantasi `PROBE_COST_BUDGET_PERCENT = 1.0` (`revix/prober.py:114`) |
| prober raqamni **yozadi** | ✅ bor | `prober_stop` payload'ida `"cost"` kaliti ostida (`revix/prober.py:712`, `:722`); CLI flag'i `--report-cost` (`revix/prober.py:840`) |
| granularlik **per-trial** | ✅ **v1.1 TUZATDI** | `cost_report()` prober jarayonining butun hayoti bo'yicha kumulyativ (`revix/prober.py:764`-`:768`), va §4.5(a) **har trial uchun alohida prober jarayonini** normativ qilgan — demak `prober_stop` endi **run'da bir marta emas, har trial'da** ishlaydi va `core_percent` ni o'z envelope'idagi `trial_id` bilan olib yuradi. §8.2 talab qilgan per-trial o'lchov **manbada mavjud** |
| `reduce.py` uni `trial_metrics` ga **chiqaradi** | ❌ **YO'Q — va ATAYLAB shunday qoladi** | `reduce.py` da `prober_stop` record turi **umuman yo'q** (`RT_*` ro'yxati: `revix/reduce.py:96-108`), va butun faylda `cost` so'zi **bitta marta ham** uchramaydi (revizyada qayta tekshirildi) |
| **transport** — `analyze.py` uni bevosita o'qiydi | ✅ **BOR** (revizya) | `--events` (`revix/analyze.py:1803`) → `prober_stop.cost.core_percent`, envelope'dagi `trial_id` bo'yicha `trials.jsonl` dagi `arm` ga bog'lanadi |

**Yechim reducer'ni O'ZGARTIRMAYDI, uni CHETLAB O'TADI.** O'lchov manbada
per-trial mavjud; `analyze.py` uni `--events` orqali to'g'ridan-to'g'ri
oladi.

> **NEGA `reduce.py` tuzatilmaydi:** §4.1 ning "KOD USTUN" printsipi uni
> tahrirlamaslikni talab qiladi, **va** probe narxi **o'lchov emas**,
> metodologiya hisoboti — reducer'ning VR / FR / downtime yo'liga umuman
> tegishli emas. Uni reducer'ga kiritish shu yo'lni kengaytirardi.
>
> **`--events` yo'q bo'lsa:** `probe_cost` bo'limi **chiqariladi** va sabab
> `warnings` ga yoziladi (§2.3-13) — hujjatlashtirilgan placeholder, to'qib
> chiqarilgan figura emas.

### 2.2 Chiqish: `analysis.json` — qat'iy sxema

```jsonc
{
  "schema_version": 1,
  "analysis_version": "p1/v1",
  "preregistration_sha256": "...",     // kirish run_meta dan
  "preregistration_version": "...",    // v1.2 (§2.8) provenans
  "run_id": "...", "session_id": "...",       // v1.2 (§2.8) provenans
  "time_unit": "us",                   // v1.2 MAJBURIY: §2.4 ni ko'ring
  "t_trial_us": 0,                     // v1.2 MAJBURIY, TOP-LEVEL:
                                       //   run_meta dan KO'CHIRILADI (§5),
                                       //   analyze.py QAYTA HISOBLAMAYDI
  "t_trial_formula": "...",            // v1.2 (§5.4-3) matn sifatida
  "generated_mono_us": 0,
  "n_trials": {"total": 0, "by_disposition": {}},
  "primary": {                          // §11 birlamchi endpoint
    "endpoint": "P(VR) trend across pressure levels",
    "test": "cochran_armitage_trend",
    "statistic": 0.0, "p_value": 0.0, "direction": "decreasing|increasing|none",
    "cells": [{"level": "P0", "k": 0, "n": 0, "p_hat": 0.0,
               "ci_lower": 0.0, "ci_upper": 0.0, "ci_method": "clopper_pearson"}],
    "risk_difference": {"contrast": "P0-P2",   // v1.2 (§2.8): nomsiz farq
                        "estimate": 0.0,       //   TALQIN QILINMAYDI
                        "ci_lower": 0.0, "ci_upper": 0.0,
                        "ci_method": "newcombe"},
    "ci_level": 0.95,                   // v1.2 (§2.8): yozilmasa figura
                                        //   "95%" deb DA'VO QILA OLMAYDI
    "recovered_within_horizon": "k/n",  // v1.2 (§2.3-4): HAR jadval bilan
    "falsified": false,                 // §11 mezoni bo'yicha
    "falsification_rule": "trend p>0.05 AND newcombe_upper<0.15"
  },
  "survival": {                         // §10.2
    "km": {"by_arm": {"<arm>": {"times": [], "survival": [], "at_risk": [],
                                "greenwood_var": [],
                                // v1.2 qo'shimchalari (§2.8):
                                "n_total": 0, "n_censored": 0, "n_events": 0,
                                "quantiles": {}}},   // §2.3-8: p90/p99 nan
           // v1.2 (§2.10): §11 pressure kontrasti KM'ni ham pressure
           // band bo'yicha talab qiladi -- RMST farqi aynan shu ikki
           // egri chiziqdan olinadi.
           "by_pressure_band": {"<band>": {"times": [], "survival": [],
                                           "at_risk": [], "greenwood_var": [],
                                           "n_total": 0, "n_censored": 0,
                                           "n_events": 0, "quantiles": {}}}},
    "logrank": {"chi2": 0.0, "p_value": 0.0, "observed": {}, "expected": {},
                "by_pressure_band": {}},   // v1.2 (§2.10)
    "rmst": {"tau": 0.0,              // MIKROSEKUND (§10.2/§11: tau = 8 s
                                      //   => 8000000)
             "by_arm": {"<arm>": {"estimate": 0.0, "se": 0.0}},
             "difference": {"contrast": "A-no_action",   // v1.2: nomsiz
                            "estimate": 0.0, "se": 0.0,  //   farq TALQIN
                            "ci_lower": 0.0,             //   QILINMAYDI
                            "ci_upper": 0.0},
             // v1.2 (§2.10) -- §11 ning fail-slow mezoni AYNAN shu
             // kontrastni nomlaydi: P0 va P2 orasidagi time-to-VR RMST
             // farqi, tau = 8 s. Busiz §11 HISOBLANMAYDI.
             "by_pressure_band": {"<band>": {"estimate": 0.0, "se": 0.0}},
             "pressure_difference": {"contrast": "P0-P2", "tau": 0.0,
                                     "estimate": 0.0, "se": 0.0,
                                     "ci_lower": 0.0, "ci_upper": 0.0}},
    "proportional_hazards_checked": false,   // tekshirilmasa HR BERILMAYDI
    "censoring": {"n_censored": 0, "recovered_within_horizon": "k/n",
                  "n_undetermined": 0}       // v1.2 IXTIYORIY: VR=None,
                                             //   "recovered EMAS" bilan
                                             //   QO'SHILMAYDI (§2.5)
  },
  "false_recovery": {                   // §5
    "fr_a": {"per_action": 0.0, "per_episode": 0.0, "n_undetermined": 0,
             "basis": "..."},           // v1.2 MAJBURIY (§2.9): qaysi
                                        //   denominator ishlatilgani
    "fr_b": {"computed": false, "reason": "no calibration matrix (P1)"}
  },
  "downtime": {                         // §6.1 uchala o'lchov
    // v1.2: ICHKI SHAKL endi belgilangan. Har o'lchov uchun `median`,
    // `p90`, `p99` MAJBURIY; har biri YO plain son, YO obyekt.
    // §10.2 BCa bootstrap CI ni talab qiladi => obyekt shakli NORMAL
    // holat, yalang'och son esa DEGENERAT holat (CI hisoblanmagan).
    "d_sd": {
      "median": {"estimate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0,
                 "ci_method": "bca_bootstrap"},
      "p90": {"estimate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0,
              "ci_method": "bca_bootstrap"},
      "p99": 0.0,                     // degenerat shakl: CI yo'q
      "ecdf": {"x": [], "y": []},     // v1.2 IXTIYORIY (§2.6)
      // v1.2 (§2.8) -- har jadval k/n bilan (§2.3-4) va `None` != 0:
      "recovered_within_horizon": "k/n", "unit": "us",
      "n": 0, "n_censored": 0, "n_missing": 0,
      "censoring_flag": "d_sd_censored",   // d_eff uchun null (§2.9)
      "note": null
    },
    "d_probe": {"median": {}, "p90": {}, "p99": {}},   // bir xil shakl
    "d_eff":   {"median": {}, "p90": {}, "p99": {},
                "censoring_flag": null}   // §2.9: ATAYLAB null
  },
  "probe_cost": {                       // v1.2 YANGI, IXTIYORIY (§2.7)
    "budget_percent": 1.0,              // yo'q bo'lsa §8.2 ning 1% i
    "by_arm": {
      "<arm>": {"core_percent": [0.0, null, 0.0]}   // TRIAL bo'yicha
    }                                   // null = o'lchanmadi (0 EMAS)
  },
  "sensitivity": {                      // §4 sweep
    // DIQQAT (§2.4 istisnosi): `w_stab` SEKUNDDA, mikrosekundda EMAS --
    // §4 grid'i aynan shu raqamlar bilan oldindan e'lon qilingan.
    "w_stab": [8,10,30,60,120], "theta": [0.5,0.8,0.95],
    "grid": [{"w_stab": 8, "theta": 0.8, "p_vr_by_level": {}, "note": null}],
    "recovered_within_horizon": "k/n"   // v1.2 (§2.3-4)
  },
  "multiplicity": {"method": "holm_bonferroni", "family": [], "adjusted": [],
                   "uncorrected": []},  // v1.2 (§2.8): §10.4 "exploratory
                                        //   deb belgilanadi"
  "exclusions": {"rate": 0.0, "by_reason": {},    // NATIJA sifatida beriladi
                 "n_total": 0, "n_excluded": 0, "n_primary": 0},  // v1.2:
                                        //   `rate` ning auditi (§2.8)
  "warnings": []                        // hisoblab bo'lmagan narsalar
}
```

### 2.3 Analiz majburiyatlari

| # | majburiyat | nega |
|---|---|---|
| 1 | `t-test` va `mean ± SD` **CHIQARMAYDI** | §10.2 taqiqi |
| 2 | Cox / hazard ratio **faqat** `proportional_hazards_checked=true` bo'lsa | §10.2 |
| 3 | Censored trial'lar KM/log-rank ga **kiradi**, tashlanmaydi | §6.2 |
| 4 | Har jadval `recovered_within_horizon: k/n` bilan birga | §6.2 |
| 5 | Eksklyuziya darajasi **natija sifatida** beriladi | §12 |
| 6 | Hisoblab bo'lmagan narsa `warnings` ga, **taxmin qilinmaydi** | soxta aniqlik yo'q |
| 7 | `W_stab > horizon` bo'lgan sweep yacheykasi `note` bilan belgilanadi | `reduce.py` uni `None` qaytaradi |
| 8 | p90/p99 KM'dan `nan` bo'lsa — **censored bo'lmagan qism** ustida BCa bootstrap | `stats.km_quantile` cheklovi |
| 9 | **v1.1:** `analysis.json` ga `t_trial_us` **kirish `run_meta` dan** ko'chiriladi | §5: qaysi horizon ostida censor qilingani figura va jadvaldan ko'rinadi |
| 10 | **v1.2:** `t_trial_us` **TOP-LEVEL** kalit; `analyze.py` uni **qayta hisoblamaydi** | §6.2 har jadval bilan `recovered_within_horizon: k/n` ni talab qiladi, va k/n horizon'siz **talqin qilinmaydi**. Qayta hisoblash ikkinchi haqiqat manbai yaratardi |
| 11 | **v1.2:** `time_unit: "us"` **har doim** yoziladi | §2.4 |
| 12 | **v1.2:** `downtime.<o'lchov>.{median,p90,p99}` **majburiy**; CI hisoblangan bo'lsa obyekt shaklida | §10.2: *"median, p90, p99 + BCa bootstrap CI"* |
| 13 | **v1.2:** `probe_cost` ni to'ldirish imkoni bo'lmasa — bo'lim **CHIQARILADI** va sabab `warnings` ga yoziladi | §2.1: provenance zanjiri uzilgan. Bu majburiyat 6 ning (*"hisoblab bo'lmagan narsa `warnings` ga"*) aynan qo'llanishi |
| 14 | **v1.2:** `survival.censoring.n_undetermined` hisoblansa yoziladi; VR=`None` hech qachon `n_censored` yoki "recovered emas" ga **qo'shilmaydi** | §2.5 |
| 15 | **v1.2:** §2.2 ning kalitlari **MAJBURIY MINIMUM**, yopiq ro'yxat emas | §2.8: §2.3 ning 4 va 8 majburiyatlari §2.2 da ko'rinmagan kalitlarni talab qiladi, demak ikkisi bir vaqtda bajarilishi uchun sxema ochiq bo'lishi SHART |
| 16 | **v1.2:** `survival.rmst.pressure_difference` (`contrast`, `tau`, `estimate`, `se`, `ci_lower`, `ci_upper`) va `survival.{km,logrank}...by_pressure_band` | §2.10: **§11 ning fail-slow mezoni** busiz **hisoblanmaydi** |
| 17 | **v1.2:** har farq (`difference`, `risk_difference`, `pressure_difference`) `contrast` maydoni bilan | nomsiz/belgisiz farq **talqin qilinmaydi** — qaysi tomon ayirilgani ko'rinmasa ishora ham noma'lum |
| 18 | **v1.2:** `false_recovery.fr_a.basis` **har doim** yoziladi | §2.9: qaysi denominator ishlatilgani auditga ochiq bo'lishi SHART |
| 19 | **v1.2:** `stats.TrendResult.direction` ning `"flat"` i `"none"` ga map qilinadi; `d_eff` uchun `censoring_flag` **`null`** | §2.9 — ikkisi ham **ataylab**, va ikkisi ham kod tuzatilmasdan hal qilingan |

### 2.4 `time_unit` — mikrosekund, taxmin qilinmaydi (v1.2)

**Qaror:** `analysis.json` dagi **barcha o'lchangan davomiylik mikrosekundda**,
va `analyze.py` top-level `time_unit: "us"` ni **har doim** yozadi.

**NEGA:** `PREREGISTRATION.md` §1 har davomiylikni `CLOCK_MONOTONIC`
**mikrosekund**da muzlatgan (*"Bitta clock — konversiya yo'q, konversiya
xatosi yo'q"*). Boshqa birlik shartnoma **ruxsat bermagan konversiya** bo'lardi.
v1.1 gacha sxemada birlik **hech qayerda yozilmagan edi** — vaqt disiplinasi
absolyut bo'lgan loyihada bu haqiqiy xavf.

**Ikki OCHIQ istisno** (ular o'lchov emas, **oldindan e'lon qilingan parametr
yorliqlari**):

| kalit | birlik | nega |
|---|---|---|
| `sensitivity.w_stab` va `sensitivity.grid[].w_stab` | **sekund** | §4 sweep grid'i `{8,10,30,60,120}` **sekundda** oldindan e'lon qilingan (`reduce.W_STAB_SWEEP_S`, `revix/reduce.py:72`), va aynan shu e'lon *"siz W ni natija uchun tanlagansiz"* hujumiga javob. Ularni µs ga aylantirish pre-registration'dagi grid'ni **ko'rinmas** qilardi |
| `sensitivity.theta`, `grid[].theta`, `p_min` | **birliksiz** | nisbat |

`survival.rmst.tau` — **mikrosekund** (davomiylik, istisno emas;
`PREREGISTRATION.md` §10.2 uni `τ = 8 s` deb muzlatgan ⇒ `8000000`).

**Figura qoidasi (normativ):** `time_unit` kaliti **yo'q** bo'lsa, figura
birlikni **TAXMIN QILMAYDI**. U o'qni birliksiz belgilaydi va figuraning
o'zida *"time unit not declared"* deb yozadi. Taxmin qilingan birlik —
jimgina konversiya xatosi, va u grafikda **to'g'ri ko'rinadi**.

### 2.5 `survival.censoring.n_undetermined` — VR=`None` alohida kategoriya (v1.2)

`reduce.py` VR ni **uch qiymatli** qiladi va `None` ni ochiq sabab bilan
qaytaradi: `r_ref_unavailable` (`revix/reduce.py:823`) va `window_truncated`
(`revix/reduce.py:831`). **`None` hech qachon `False` ga aylantirilmaydi** —
aniqlanmagan VR **ishdan chiqqan VR emas**.

v1.1 gacha sxemada `n_undetermined` faqat `false_recovery.fr_a` ostida bor
edi — lekin u **FR-A**, VR emas. Ya'ni aniqlanmagan VR'ni ko'rsatadigan joy
yo'q edi.

`analyze.py` uni `trial_metrics` dan hisoblaydi:

```
n_undetermined = |{ r : r["included_in_survival"] and r["vr"] is None }|
```

(`included_in_survival` — `revix/reduce.py:1570`; `vr` — `revix/reduce.py:1599`.)
Sabab taqsimoti `trial_metrics.vr_reason` da (`revix/reduce.py:1601`) —
**yangi kalit qo'shilmaydi**, figura o'sha maydondan yorliq oladi.

> **NEGA bu eng muhim qo'shimchalardan biri:** aniqlanmagan VR'ni
> "recovered emas" ga qo'shish **o'lchov yetishmovchiligini natijaga
> aylantiradi** — bu loyihada mavjud eng yomon buzilish turi, va u
> `reduce.py` ning 6-qoidasi (*"throughput bandi o'lchanmasa, VR
> TASDIQLANMAYDI"*) bilan ataylab oldini olingan. `analyze.py` da uni
> qaytib tiklash butun kafolatni bekor qilardi.
>
> `reduce.py` ning reduksiya xulosasida bu son allaqachon bor:
> `vr_undetermined` (`revix/reduce.py:1769`), `recovered_within_horizon`
> (`:1768`) va `recovered_k_of_n` (`:1771`) bilan birga. Ya'ni manba mavjud,
> faqat `analysis.json` da joy yo'q edi.

### 2.6 `downtime.<o'lchov>.ecdf` — ixtiyoriy, lekin interpolatsiya YO'Q (v1.2)

**Shakl:** `{"x": [...], "y": [...]}`, teng uzunlikdagi ikki massiv; `x` —
mikrosekundda downtime qiymatlari (§2.4), `y` — `[0, 1]` dagi kumulyativ
ulush.

**NEGA mavjud bo'lishi kerak:** `PREREGISTRATION.md` §10.2 ochiq yozadi:
*"ECDF'lar to'liq chizilib beriladi — har qanday bitta testdan
ishonchliroq."* §3 esa `figures.py` ni **faqat `analysis.json`** ni o'qishga
va **hech qanday statistika hisoblamaslikka** majbur qiladi. Ikkisi birga
olinganda: ECDF nuqtalari `analysis.json` da **bo'lishi SHART**, aks holda
§3 bajarilmaydi. Aynan shu yetishmovchilik v1.2 ning sababi.

**NEGA ixtiyoriy:** ECDF per-trial downtime qiymatlarining to'liq to'plamini
talab qiladi, va `d_sd` / `d_probe` / `d_eff` ning birortasi `None`
bo'lishi mumkin (o'lchanmadi). Majburiy qilinsa, `analyze.py` yo'q
ma'lumotni to'ldirishga majbur bo'lardi.

**Degradatsiya qoidasi (normativ):** `ecdf` **yo'q** bo'lsa,
`downtime_ecdf` figurasi faqat `median` / `p90` / `p99` **markerlarini**
chizadi, ularni **chiziq bilan birlashtirmaydi**, va figurada
*"no ECDF available — markers only"* deb **yozadi**. Uch nuqta orasida
egri chiziq chizish — **interpolatsiya**, ya'ni o'lchanmagan shaklni
o'lchangan deb ko'rsatish. Bu §2.3-6 (*"hisoblab bo'lmagan narsa
`warnings` ga, taxmin qilinmaydi"*) ning figuraga qo'llanishi.

### 2.7 `probe_cost` — §8.2 ning transporti, yangi talab emas (v1.2)

**Shakl:** `budget_percent` (son; **yo'q bo'lsa** §8.2 ning **1%** i
ishlatiladi) va `by_arm.<arm>.core_percent` — **trial bo'yicha ro'yxat**,
o'lchanmagan trial uchun `null`.

**NEGA bu yangi talab EMAS:** `PREREGISTRATION.md` §8.2 to'rt narsani
**allaqachon** majburlagan: prober CPU'si *"trial bo'yicha o'lchanadi"*,
*"yadro foizida beriladi"*, *">1% bo'lsa sekinlashtiriladi"*, va
*"arm'lar bo'yicha bir xil ushlanadi"*. v1.2 hech narsa qo'shmaydi — faqat
o'sha to'rt talabning **yetkazish yo'lini** ochadi. `budget_percent`
default'i ham o'ylab topilmagan: u §8.2 dagi 1% va
`prober.PROBE_COST_BUDGET_PERCENT = 1.0` (`revix/prober.py:114`).

**NEGA `by_arm` va trial bo'yicha ro'yxat:** §8.2 ning oxirgi bandi —
*"arm'lar bo'yicha bir xil ushlanadi"* — **arm'lar orasidagi taqqoslashni**
talab qiladi, demak narx arm bo'yicha guruhlanishi kerak; *"trial bo'yicha
o'lchanadi"* esa granularlikni belgilaydi. Arm qiymati
`trial_metrics.arm` dan (`revix/reduce.py:1561`).

**NEGA granularlik aynan trial darajasida chiqadi:** `cost_report()`
prober **jarayonining butun hayoti** bo'yicha kumulyativ
(`revix/prober.py:764`-`:768`), va §4.5(a) driver'ni **har trial uchun
alohida prober jarayoni** ishga tushirishga majburlaydi — demak
`prober_stop.cost` **tabiatan per-trial**. Granularlik qasddan emas, v1.1
qarorining natijasi.

**`null` nega `0` emas:** `0.0` haqiqiy o'lchov qiymati (*"CPU ishlatilmadi"*),
`null` esa *"o'lchanmadi"*. Ularni aralashtirish `CONTRIBUTING.md` §4 ning
ochiq taqig'i.

**Holat (v1.2 revizyasi): ZANJIR TO'LIQ ULANDI.**

| bo'g'in | holat |
|---|---|
| o'lchov **per-trial** | ✅ §4.5(a) ning per-trial prober qarori tufayli `prober_stop` har trial'da ishlaydi va `core_percent` ni envelope'idagi `trial_id` bilan beradi |
| **transport** | ✅ `analyze.py` uni `--events` orqali bevosita o'qiydi (`revix/analyze.py:1803`), `prober_stop.cost.core_percent` dan, `trial_id` bo'yicha `trials.jsonl` dagi `arm` ga bog'lab |

`analyze.py` holatlarni **ajratib** nomlaydi — jim qolmaydi va taxmin
qilmaydi (§2.3-6):

| kod | holat |
|---|---|
| `probe_cost_absent` | `--events` **berilmadi** (`revix/analyze.py:1410`) |
| `probe_cost_events_empty` | flag berilgan, lekin faylda `prober_stop` **yo'q** (`:1341`) |
| `probe_cost_no_trial_id` | `prober_stop` da `trial_id` yo'q (`:1368`) |
| `probe_cost_duplicate_trial_id` | bitta `trial_id` takrorlandi — **§4.5(a) ning bitta-prober qoidasiga** havola qiladi (`:1375`) |
| `probe_cost_orphan` | narx bor, lekin mos trial yo'q (`:1438`) |
| `probe_cost_partial` | trial'larning bir qismida narx yo'q (`:1433`) |

> **NEGA `absent` va `events_empty` ajratilgan:** birinchisi *"so'ralmadi"*,
> ikkinchisi *"so'raldi, lekin manba bo'sh"* — ikkinchisi **nosozlik
> belgisi**, birinchisi esa oddiy tanlov. Ularni bir kodga qo'shish
> yo'qolgan o'lchovni konfiguratsiya qarori kabi ko'rsatardi.

**Bo'shliq yopildi va buni dalil tasdiqlaydi.** v1.2 ning asl matni
`tests/integration/test_chain.py::test_zanjir_figura` ning **ishdan
chiqishini** `probe_cost` bo'shligi uchun dalil deb keltirgan edi.
`agent/validate` sintetik fixture'ga per-trial `prober_start`/`prober_stop`
(narx bilan) qo'shgandan keyin **o'sha test o'tadi**, va u **to'ldirilgan
`probe_cost` figurasini** ham qamrab oladi.

> **TASDIQLANGAN (o'zim ishga tushirdim, 2026-10-02):**
> `python3 -m pytest tests/integration/test_chain.py::test_zanjir_figura
> tests/unit/test_analyze.py::test_probe_cost_budjet_konstantasi_proberdagi_bilan_bir_xil -v`
> → **`2 passed`** (pytest 9.1.1, Python 3.14.7).

**Budjet konstantasining ATAYLAB TAKRORLANISHI.** `analyze.py` da
`PROBE_COST_BUDGET_PERCENT = 1.0` **mustaqil** ta'riflangan
(`revix/analyze.py:1303`), `prober.py` dan import qilinmaydi
(`revix/prober.py:114`).

> **NEGA takrorlanadi:** §2 ning 1-qoidasi `analyze.py` ni **qat'iy offline**
> qiladi; `prober` esa socket ochadi va o'lchanayotgan tizimga tegadi, demak
> uni import qilish offline kafolatini buzardi.
>
> **TALAB (regressiya qulfi, `CONTRIBUTING.md` §4):** ikki qiymat tengligini
> qotiradigan test **bo'lishi SHART** — aks holda bittasi o'zgarsa
> `budget_exceeded` va `probe_cost.budget_percent` jimgina ikki xil
> chegaradan gapirardi. Izoh **yetarli emas**: izoh buzilganda hech narsa
> ishdan chiqmaydi.
>
> **HOLAT (v1.2 revizyasi): QULF BOR.**
> `test_probe_cost_budjet_konstantasi_proberdagi_bilan_bir_xil`
> (`tests/unit/test_analyze.py:1186`). U `prober.py` ni **matn sifatida**
> o'qiydi va literal'ni regex bilan topadi — **import qilmaydi**, demak
> `analyze.py` ning offline kafolati (§2 qoida 1) buzilmaydi — so'ng
> `analyze.PROBE_COST_BUDGET_PERCENT` ga tengligini **va** ikkisining
> `1.0` ekanini tasdiqlaydi.
>
> **TASDIQLANGAN:** bu test o'zim ishga tushirgan `pytest` da **o'tdi**
> (yuqoridagi `2 passed`).

### 2.8 §2.2 — MAJBURIY MINIMUM, yopiq ro'yxat emas (v1.2)

#### Defekt

§2.3 ning majburiyatlari §2.2 **ko'rsatmagan** kalitlarni talab qiladi,
demak v1.1 holatida **ikki bo'lim bir vaqtda bajarilishi mumkin emas**:

- **majburiyat 4** — *"Har jadval `recovered_within_horizon: k/n` bilan
  birga"* — lekin §2.2 bu kalitni **faqat** `survival.censoring` da
  ko'rsatadi;
- **majburiyat 8** — KM p90/p99 `nan` bo'lsa BCa fallback — lekin §2.2 da
  **kvantil uchun joy yo'q**.

#### Qoida

**§2.2 ning kalitlari MAJBURIY MINIMUM.** Qo'shimcha kalit §2.2 ni buzmaydi;
§2.2 da ko'rsatilgan kalitni **tashlab ketish** buzadi.

Quyidagi kalitlar v1.2 bilan **oshkora** qo'shildi (`agent/analyze` ularni
o'z modul docstring'ida `SXEMA QO'SHIMCHALARI` ostida sanab bergan va
*"o'zboshimchalik bilan hal qilinmaydi"* deb shu amendment'ga qoldirgan):

| kalit | nega |
|---|---|
| `primary.recovered_within_horizon`, `downtime.<m>.recovered_within_horizon`, `sensitivity.recovered_within_horizon` | majburiyat 4 (§6.2) |
| `primary.ci_level` | yozilmasa figura *"95%"* deb **da'vo qila olmaydi** |
| `primary.risk_difference.contrast`, `survival.rmst.difference.contrast` | nomsiz farqning **ishorasi** noma'lum |
| `downtime.<m>.{unit, n, n_censored, n_missing, censoring_flag, note}` | `None` ≠ `0` (`CONTRIBUTING.md` §4); `n` siz kvantil hisobot qilinmaydi |
| `downtime.<m>.ecdf` | §10.2 (§2.6) |
| `survival.km.by_arm.<arm>.quantiles` | majburiyat 8 |
| `survival.km.by_arm.<arm>.{n_total, n_censored, n_events}` | `n` siz KM egri chizig'i va at-risk jadvali hisobot qilinmaydi |
| `survival.censoring.n_undetermined` | §2.5 |
| `false_recovery.fr_a.basis` | §2.9 |
| `multiplicity.uncorrected` | §10.4 *"exploratory deb belgilanadi"* — belgilash uchun joy kerak |
| `time_unit`, `t_trial_us`, `t_trial_formula` | §2.4, §5.4 |
| `run_id`, `session_id`, `preregistration_version` | provenans |
| `exclusions.{n_total, n_excluded, n_primary}` | `exclusions.rate` **natija** sifatida beriladi (§12), demak uning **auditi** ham kerak |

> **NEGA sxema ochiq, lekin kalit nomlari qat'iy:** `figures.py`,
> `analyze.py` va `validate.py` **bir xil nomlarga** bog'lanadi (§4.1 bilan
> bir mantiq). Ochiqlik *"yangi kalit qo'shish mumkin"* degani, *"nomni
> o'zgartirish mumkin"* degani **emas**.

### 2.9 FR-A asosi, `--episodes`, va ikki ataylab qaror (v1.2)

#### (a) `fr_a.basis` — majburiy

`PREREGISTRATION.md` §5 FR-A ni **har action** va **har epizod** uchun talab
qiladi, va §2.2 ikkisini ham (`per_action`, `per_episode`) so'raydi. Lekin
per-action / per-episode tafsiloti `reduce.py` ning **`episodes.jsonl`** ida
yashaydi, v1.1 §2.1 esa kirish sifatida faqat `trial_metrics` ni bergan.

**Hal:** ixtiyoriy `--episodes PATH` (§2.1). U **berilmasa**, `analyze.py`
faqat **aynan yechiladigan** quyi to'plamdan hisoblaydi: `n_episodes == 1`
bo'lgan trial'da trial darajasidagi FR-A epizod darajasiga **aynan teng**
(`_kleene_any` bitta element ustida), va `n_actions == 1` ham bo'lsa action
darajasiga teng. Yechilmagan trial'lar `warnings` da **sanab beriladi** va
denominatorga **kirmaydi**.

**`fr_a.basis` har ikki holatda ham MAJBURIY** — u *"qaysi denominator
ishlatilgan"* degan savolning yozma javobi.

> **NEGA majburiy:** `per_action = 0.07` raqami to'liq to'plamdan yoki
> yechiladigan quyi to'plamdan olinganiga qarab **boshqa ma'no** beradi.
> Asos yozilmasa, ikkisi bir xil ko'rinadi — ya'ni jimgina noto'g'ri
> talqin.

#### (b) `stats.TrendResult.direction` — `"flat"` → `"none"`

`stats.py` trend yo'nalishi uchun `"flat"` qaytaradi, §2.2 ning yopiq enumi
esa `decreasing|increasing|none`. **Qaror: §2.2 normativ**, `analyze.py`
`flat → none` map qiladi (`revix/analyze.py:601`, `:606`), **`stats.py`
tahrirlanmaydi** — §4.1 ning "KOD USTUN" printsipi bilan bir xil usul:
chiqish sxemasi shartnomada muzlatilgan, ichki nom modulning ishi.

#### (c) `d_eff` uchun `censoring_flag` ATAYLAB `null`

`reduce.py` `d_sd_censored` va `d_probe_censored` ni beradi, lekin
**`d_eff_censored` ni bermaydi** (`Downtime` dataclass: `revix/reduce.py:1309`,
`:1312`, `:1314`).

**Bu kamchilik emas, ta'rifning natijasi:** §6.1 ga ko'ra `D_eff` ning
integral domeni `[t_fault_effective, horizon]`, ya'ni u **qurilishi bo'yicha**
horizon bilan chegaralangan — kesilmagan "to'liq" qiymati mavjud emas.
Shuning uchun `analyze.py` har kuzatilgan qiymatni **event** deb oladi,
`censoring_flag: null` yozadi va `note` da sababini beradi.

> **NORMATIV TAQIQ:** `d_eff` uchun censoring'ni `down_at_horizon` dan
> (`revix/reduce.py:1487`) **chiqarib olish mumkin emas** — bu amendment'siz
> **qilinmaydi**. Aks holda bitta o'lchov ikki xil ta'rif ostida
> hisoblanardi: `D_eff` integrali horizon'ni **o'z ichiga oladi**, KM esa
> horizon'ni **censoring nuqtasi** deb oladi. Bu gap aynan shu uchun
> yozilgan: keyingi o'quvchi buni "tuzatilmagan joy" deb o'ylab
> **tuzatmasligi** kerak.

### 2.10 🚨 §11 ning fail-slow mezoni HISOBLANMAYDI — pressure kontrasti (v1.2)

#### Defekt — eng og'iri

`PREREGISTRATION.md` §11 muzlatilgan falsifikatsiya qoidasini beradi, va
uning ikkinchi bandi aynan shunday:

> *"fail-slow shakli qo'llab-quvvatlanmaydi, agar `P0` va `P2` orasidagi
> time-to-VR RMST farqi (τ = 8 s) uchun 95% CI 20% oshishni chiqarib
> tashlasa."*

Bu **pressure** kontrasti. Lekin §10.2 KM va log-rank'ni **arm bo'yicha**
belgilaydi, va v1.1 §2.2 faqat `survival.rmst.by_arm` va **bitta**
`difference` ni bergan. Ya'ni §11 nomlagan kontrast uchun sxemada
**joy yo'q**.

**O'lchangan oqibat:** `agent/analyze` (commit `2518e26`) hozir arm
kontrastini (`"A - no_action"`) chiqaradi va
`schema_gap_rmst_pressure_contrast` ogohlantirishini beradi
(`revix/analyze.py:923`) — ya'ni **§11 ning bandi BAHOLANMAYDI**.

> **NEGA bu kosmetik bo'shliq emas:** §11 — **muzlatilgan falsifikatsiya
> qoidasi**, loyihaning ilmiy qiymatining asosi (`README.md` "Ilmiy
> yaxlitlik": ta'riflar natijani ko'rishdan **oldin** muzlatiladi).
> **Chiqishdan hisoblab bo'lmaydigan qoida hech narsani falsifikatsiya
> qilmaydi.** Ya'ni bo'shliq §11 ni bezak qoldirardi.

#### Qoida (normativ, ADDITIV)

| kalit | mazmuni |
|---|---|
| `survival.rmst.by_pressure_band.<band>` | `{estimate, se}` — har pressure band uchun RMST |
| `survival.rmst.pressure_difference` | `{contrast: "P0-P2", tau, estimate, se, ci_lower, ci_upper}` |
| `survival.km.by_pressure_band.<band>` | arm bo'yicha KM bilan **bir xil** shakl |
| `survival.logrank.by_pressure_band` | pressure bo'yicha log-rank |

**Mavjud `by_arm` strukturasi SAQLANADI.** Ikkisi ham kerak:
§10.2 ning **arm** taqqoslashi va §11 ning **pressure** taqqoslashi
**boshqa savollarga** javob beradi.

> **NEGA KM ham pressure bo'yicha kerak:** RMST farqi **hosila** qiymat —
> u o'zi ikki survival egri chizig'idan hisoblanadi. Egri chiziqlar
> berilmasa, `pressure_difference` ni **tekshirib bo'lmaydi**, va §3
> `figures.py` ni faqat `analysis.json` ga bog'lagan — demak figura ham
> chizilmaydi. Shu sabab KM/log-rank ning pressure bo'yicha guruhlanishi
> **xuddi shu mantiqdan** kelib chiqadi.
>
> **NEGA bu ADDITIV va hech qanday ta'rifni o'zgartirmaydi:** §11 ning
> mezoni va uning **20% chegarasi tegilmaydi**; `τ = 8 s` tegilmaydi;
> `by_arm` tegilmaydi. Qo'shilgani faqat **hisoblash uchun transport**.
> Kontrast `P0`–`P2` ni §11 **o'zi** nomlagan, demak tanlov ham bu
> hujjatning emas.
>
> **CHEKLOV:** `τ` **mikrosekundda** (§2.4) ⇒ `8 s = 8000000`. §11 ning
> *"20% oshish"* i **nisbat**, demak birliksiz va konversiyadan xoli.

---

## 3. Figura moduli

`revix/figures.py` **faqat `analysis.json` ni** o'qiydi — xom ma'lumotni emas.
Shunda figura analizdan uzoqlasha olmaydi.

Chiqish: `figures/<nom>.svg` (matplotlib — bog'liqlik holati: **§6**), va har
figura yonida `figures/<nom>.json` — figurani hosil qilgan **aynan raqamlar**,
shunda figura tekshirilishi mumkin.

Majburiy figuralar (loyiha spetsifikatsiyasi §47 dan, P1 uchun tegishlilari):
`p_vr_vs_pressure` (dose-response + CI), `km_time_to_vr`, `downtime_ecdf`
(uchala o'lchov), `sensitivity_heatmap` (W_stab × θ), `exclusion_breakdown`,
`probe_cost`.

**Rang/uslub qoidasi:** figura oq-qora chop etishda ham o'qilishi kerak
(marker/chiziq turi bilan farqlanadi, faqat rang bilan emas).

### 3.1 Degradatsiya qoidalari (v1.2) — figura JIM QOLMAYDI va TAXMIN QILMAYDI

`figures.py` faqat `analysis.json` ni o'qiydi va hech qanday statistika
hisoblamaydi (§3). Demak kalit yo'q bo'lganda uning yagona to'g'ri xatti-
harakati — **kamroq chizish va nima yo'qligini aytish**. Bu §2.3-6 ning
figuraga qo'llanishi.

| yo'q kalit | figura | majburiy xatti-harakat |
|---|---|---|
| `downtime.<o'lchov>.ecdf` | `downtime_ecdf` | faqat `median`/`p90`/`p99` markerlari, **birlashtiruvchi chiziq yo'q**, figurada *"no ECDF available — markers only"* (§2.6) |
| `time_unit` | **hammasi** | o'q **birliksiz** belgilanadi + *"time unit not declared"*; birlik **taxmin qilinmaydi** (§2.4) |
| `probe_cost` | `probe_cost` | *"probe cost not available — reason: <`warnings` dagi sabab>"*; bo'sh o'q chizilmaydi (§2.7) |
| `survival.censoring.n_undetermined` | `km_time_to_vr` | aniqlanmagan trial'lar **alohida** ko'rsatiladi; mavjud bo'lmasa *"n_undetermined not reported"*. Ular **hech qachon** "recovered emas" ga qo'shilmaydi (§2.5) |
| `t_trial_us` | `km_time_to_vr`, `downtime_ecdf` | horizon chizig'i chizilmaydi + *"horizon not reported"*; `recovered_within_horizon` nisbati **horizon'siz talqin qilinmaydi** (§2.3-10) |
| `*.ci_lower` / `*.ci_upper` (degenerat shakl) | `p_vr_vs_pressure`, `downtime_ecdf` | nuqta chiziladi, **error bar chizilmaydi**; *"CI not computed"* (§2.2 degenerat shakl) |
| `survival.rmst.pressure_difference` yoki `survival.km.by_pressure_band` | `km_time_to_vr` | pressure kontrasti **chizilmaydi** + *"§11 fail-slow criterion not evaluable — reason: &lt;`warnings`&gt;"*; arm kontrasti pressure kontrasti **o'rniga ko'rsatilmaydi** (§2.10) |
| `primary.ci_level` | `p_vr_vs_pressure` | legend/o'qda *"95%"* **yozilmaydi**, *"CI level not declared"* (§2.8) |
| `false_recovery.fr_a.basis` | — | FR-A raqami **ko'rsatilmaydi**: asossiz nisbat talqin qilinmaydi (§2.9a) |

> **NEGA har holatda matn yoziladi:** jimgina kamroq chizilgan figura
> **to'liq figura kabi ko'rinadi**. Reviewer uchun *"ECDF yo'q"* va
> *"ECDF tekis"* — ikki butunlay boshqa xulosa, va ularni ajratishning
> yagona yo'li figuraning o'zida yozilgan gap. `figures/<nom>.json`
> (§3) ham o'sha holatni aks ettiradi, shunda figura tekshirilishi
> mumkin bo'lib qoladi.

---

## 4. Record maydon nomlari — normativ moslik jadvali (v1.1)

Bu bo'lim `driver.py`, `analyze.py` va `validate.py` **uchalasi** bog'lanadigan
yagona haqiqat manbai. `revix/reduce.py` ichidagi `RAW_CONTRACT`
(`revix/reduce.py:1898`) o'z izohida *"markazda yarashtirilishi kerak"* deydi —
mana shu markaz.

### 4.1 Hal qilish printsipi: KOD USTUN

`reduce.py` 75 KB, yozilgan va test bilan qoplangan; `driver.py` hali
yozilmagan. Shuning uchun:

- **`reduce.py` TAHRIRLANMAYDI.** Hujjat kodga moslashtiriladi, teskarisi emas.
- **Driver map/normalise qiladi.** Qiymat manbasidagi nom (`schedule.py`,
  `units.py`, `prober.py`) o'z modulida qoladi; record'ga yozilayotganda
  `reduce.py` o'qiydigan nomga aylantiriladi.
- **Xom ma'lumot ustiga yozilmaydi** (`CONTRIBUTING.md` §1.4). Normalizatsiya
  yozish paytida (driver) yoki reduksiya kirishida (adapter, §4.5) bo'ladi —
  mavjud xom faylni tahrirlash orqali EMAS.

**NEGA kod ustun:** hujjatni o'zgartirish narxi bitta amendment; 75 KB
test-qoplangan reducer'ni qayta nomlash narxi — regressiya xavfi, test
yangilanishi va `RAW_CONTRACT` bilan haqiqiy kod orasida yangi drift. Ikkinchisi
o'lchov validligiga **xavf**, birinchisi esa shunchaki protsedura.

**NEGA nom o'zgarishi jim ketmaydi:** `reduce.py` yo'q maydonni `None` deb
o'qiydi (`_as_int` / `_as_str`, `revix/reduce.py:215`, `:230`), va `None`
loyihada "o'lchanmadi" degani (`CONTRIBUTING.md` §4). Masalan `progress`
o'qilmasa `window_throughput()` `None` qaytaradi
(`revix/reduce.py:533`) → `R_ref` yo'q → `evaluate_vr()` `vr=None`
(`revix/reduce.py:823`, `reason="r_ref_unavailable"`) → **birlamchi endpoint
butunlay hisoblanmaydi**. Ya'ni bitta noto'g'ri ustun nomi butun eksperimentni
jimgina qiymatsiz qiladi.

### 4.2 Envelope va payload — chegara

`schema.Emitter.record()` payload envelope maydonini **bosib o'tsa
`ValueError` tashlaydi** (`revix/schema.py:236`). `ENVELOPE_FIELDS`
(`revix/schema.py:241`): `schema_version`, `record_type`, `stream`, `run_id`,
`session_id`, `boot_id`, `trial_id`, `block_index`, `seq`, `mono_us`,
`real_us`, `emitter`.

Normativ natijalar:

| # | qoida | nega |
|---|---|---|
| 1 | `trial_id` va `block_index` **envelope orqali** beriladi (`Emitter.record(..., trial_id=…, block_index=…)`), payload'da EMAS | `reduce.split_trials()` tekis record'dan o'qiydi (`revix/reduce.py:422`), demak natija bir xil; lekin payload'ga qo'yilsa `ValueError` |
| 2 | `schedule.Trial.as_dict()` **payload sifatida berilmaydi** | u `trial_id` va `block_index` ni o'z ichiga oladi (`revix/schedule.py:179`) → envelope bilan to'qnashadi → `ValueError`. Driver `levels_dict` dan maydonlarni ALOHIDA oladi |
| 3 | Har record uchun `stream = record_type` (ya'ni `Emitter` default'i) | `seq` oqim bo'yicha monotonik; bitta emitter ikki `record_type` ni bitta oqimga yozsa **soxta `seq` bo'shligi** chiqadi (§14.6-3 buziladi). **v1.2:** bu endi majburlanadi — `validate._stream_key()` kalitni `(emitter, stream)` dan oladi va `check_envelope` `stream_not_record_type` xatosini beradi (`revix/validate.py:483`) |
| 4 | `mono_us` envelope'dan keladi va **o'sha record'ning kuzatuv vaqti** bo'lishi kerak; kuzatuv vaqti boshqa bo'lsa `Emitter.record(..., mono=…)` bilan beriladi | `reduce.py` oyna a'zoligini `mono_us` bilan hisoblaydi (`revix/reduce.py:770`, `:882`) |

### 4.3 Normativ jadval

Ustunlar: **manba** (qiymat qaydan keladi) → **record maydoni** (xom
record'dagi AYNAN nom) → **consumer** (uni o'qiydigan kod, fayl:qator).

#### `run_meta`

| manba | record maydoni | consumer |
|---|---|---|
| `git status --porcelain` bo'sh emasligi | `git_dirty` | `validate.check_run_meta` (`validate.py:717`) |
| run rejimi (`pilot` \| `confirmatory`) | `run_mode` | `validate.check_run_meta` (`validate.py:716`; `mode` ga fallback qiladi) |
| `sha256sum PREREGISTRATION.md` | `preregistration_sha256` | `validate.check_run_meta` (`validate.py:735`), `analyze.py` |
| `Schedule.seed` | `rng_seed` | reproducibility (`RAW_CONTRACT`; runtime'da o'qilmaydi) |
| §5 formulasi | `t_trial_us` | `analyze.py`, `figures.py` (§2.3-9) |
| §1.1 ro'yxati | o'sha nomlar bilan | reproducibility |

#### `trial_begin`

| manba | record maydoni | consumer |
|---|---|---|
| `Trial.levels_dict["arm"]` | `arm` | `reduce.Trial.arm` (`reduce.py:385`) |
| **`Trial.levels_dict["pressure_level"]`** | **`pressure_band`** | `reduce.Trial.pressure_band` (`reduce.py:389`), `trial_metrics.pressure_band` (`reduce.py:1562`) |
| konstanta `"clean_crash"` (§9.3: P1 da faktor EMAS) | `fault_class` | `reduce.reduce_trial` → `evaluate_fr_b` (`reduce.py:1550`) |
| `Trial.trial_id` | envelope `trial_id` | `reduce.split_trials` (`reduce.py:422`) |
| `Trial.block_index` | envelope `block_index` | `reduce.Trial.block_index` (`reduce.py:380`) |
| `mono_us()` trial boshida | envelope `mono_us` | `reduce.Trial.start_us` (`reduce.py:398`) |
| `Trial.position_in_block` | `position_in_block` | reproducibility |
| `TrialTimeline.as_dict()` | `planned_timeline` | §5 tekshiruvi, `analyze.py` |
| P1 da **berilmaydi** (§14.7 ochiq bo'shlig'i) | `harm_indicator` | `reduce.reduce_trial` (`reduce.py:1552`); yo'q bo'lsa FR-B `computed=false` |

> **NEGA faktor nomi `pressure_level` qoladi:** `schedule.P1_FACTORS`
> (`revix/schedule.py:146`) `Factor("pressure_level", ("P0","P1","P2"))` deb
> ta'riflangan va `tests/unit/test_schedule.py` shunga bog'langan. Faktor
> nomi — **dizayn modulining ichki nomi**: u randomizatsiya, blok va digest
> hisobida ishlatiladi. Record maydoni esa **`pressure_band`**, chunki
> reducer aynan shuni o'qiydi. Ikkisi atayin ajratilgan: dizayn moduli va
> ma'lumot sxemasi mustaqil evolyutsiya qiladi, va bitta nom ikki joyda
> ikki xil ma'no olmaydi. Driver bu yagona map'ni amalga oshiradi.

#### `trial_end`

| manba | record maydoni | consumer |
|---|---|---|
| harness qarori, `schema.DISPOSITIONS` enum'idan | `disposition` | `reduce.derive_disposition` (`reduce.py:1418`), `validate.check_dispositions` (`validate.py:436`) |
| harness | `reason` | odam o'qishi uchun (`RAW_CONTRACT`) |
| **v1.2:** trial atrofidagi o'lchangan qo'shimcha (unit yaratish/yo'q qilish, D-Bus round-trip, flush) | **`overhead_us`** — qabul qilinadigan aliaslar `trial_overhead_us`, `overhead_s`, `trial_overhead_s` | `validate.TRIAL_OVERHEAD_FIELDS` (`revix/validate.py:155`); §1.3-9 va §9.4 v1.3: *"o'lchanadi, taxmin qilinmaydi"*. Birlik **nomda**: `_us` mikrosekund, `_s` sekund |
| `trial_begin.mono_us + T_trial` (§5) | envelope `mono_us` | `reduce.Trial.end_us` (`reduce.py:406`) — **horizon aynan shu nuqta**, right censoring shu yerda bo'ladi (§6.2) |

#### `probe_sample` — prober yozadi, driver YOZMAYDI

`probe.csv` ustunlari `prober.PROBE_FIELDS` (`revix/prober.py:142`) bilan
qat'iy belgilangan va `PREREGISTRATION.md` §14.4 majburiy maydonlarni
`mono_us_send`, `outcome`, **`progress_counter`**, `invocation_id_seen` deb
**muzlatgan**.

| manba (SUT javobi) | record maydoni (`probe.csv`) | consumer |
|---|---|---|
| probe boshlanishi | `mono_us_send` | `reduce.probe_from_record` (`reduce.py:289`) |
| `OUTCOMES` enum'i | `outcome` | `reduce.probe_from_record` (`reduce.py:294`), `Probe.passed` (`reduce.py:212`) |
| javobdagi `progress` | **`progress_counter`** → normalizatsiya → **`progress`** | `reduce.probe_from_record` (`reduce.py:298`) |
| javobdagi `invocation` | `invocation_id_seen` | `reduce.probe_from_record` (`reduce.py:299`) — **moslik bor, map kerak emas** |
| `Prober.trial_id` (`--trial-id`) | `trial_id` | `reduce.split_trials` (`reduce.py:453`) |
| target bo'yicha hisoblagich | `seq` | `reduce.probe_from_record` (`reduce.py:301`) |
| javobdagi `pid` | `sut_pid_seen` | **hech kim** (§4.6) |

#### `unit_state` — XOM systemd nomlari + snake_case nomlar, IKKISI HAM

`units.UnitWatcher` → `_state_record()` (`revix/units.py:1075`) **xom systemd
property nomlarini** chiqaradi. Driver ularni **o'chirmaydi** —
`reduce.py` o'qiydigan snake_case nomlarni **qo'shadi**.

| manba (`units.STATE_PROPS`) | record maydoni | consumer |
|---|---|---|
| `ActiveState` | `ActiveState` **va** `active_state` | `reduce.actor_success_signal` (`reduce.py:886`) |
| `NRestarts` | `NRestarts` **va** `n_restarts` | `reduce.evaluate_vr` 4-band (`reduce.py:770`), `reduce.reduce_trial` loop_rate (`reduce.py:1523`), `validate._invocation_changed` (`validate.py:674`, `:678`) |
| `InvocationID` | `InvocationID` **va** `invocation_id` | `reduce.reduce_trial` (`reduce.py:1520`), `validate._invocation_changed` (`validate.py:667`) |
| `ActiveEnterTimestampMonotonic` | o'sha nom **va** `active_enter_ts_mono_us` | `reduce.compute_d_sd` (`reduce.py:1342`) |
| `ActiveExitTimestampMonotonic` | o'sha nom **va** `active_exit_ts_mono_us` | `reduce.compute_d_sd` (`reduce.py:1341`) |
| `Result` | `Result` **va** `result` | **hech kim** (§4.6); `RAW_CONTRACT` talab qiladi |
| `recv_mono_us` (`units.py:1098`) | `recv_mono_us` **saqlanadi**, va envelope `mono_us := recv_mono_us` | `reduce` oyna filtrlari (`reduce.py:770`, `:882`, `:1341`), `validate` (`validate.py:666`) |
| arm C engine (P1 da YO'Q) | `engine_state` | `reduce.actor_success_signal` (`reduce.py:889`) |
| qolgan `STATE_PROPS` (`SubState`, `ExecMain*`, `*TimestampMonotonic`) | xom nomi bilan | `analyze.py` kovariatalari, diagnostika |

> **NEGA IKKALASI HAM:** `PREREGISTRATION.md` §1 systemd'ning **o'z**
> `*TimestampMonotonic` qiymatlarini avtoritet deb belgilaydi va barcha
> davomiylik shulardan hisoblanadi; §14.4 esa `unit_state` uchun
> *"systemd'ning o'z monotonic timestamp'lari va harness'ning qabul
> `mono_us`i alohida"* ni **majburiy** qiladi — shunda D-Bus yetkazish
> kechikishi ko'rinadi, o'lchov ichida yashirinmaydi. Xom nomlarni
> snake_case bilan **almashtirish** avtoritet qiymatni va `changed_props` /
> `missing_props` bilan bog'liqlikni yo'qotardi
> (`units.py:1105`, `:1118`); snake_case'ni **qo'shmaslik** esa `reduce.py`
> ni `D_sd` ni umuman hisoblay olmaydigan holatga qo'yardi. Shuning uchun
> ikkalasi ham yoziladi va `recv_mono_us` **alohida maydon sifatida
> qoladi**.
>
> `mono_us := recv_mono_us` qarori: `reduce.py` `unit_state.mono_us` ni
> FAQAT oyna a'zoligi uchun ishlatadi, ya'ni "bu kuzatuv qachon bo'ldi"
> degan ma'noda. Emit vaqti (yozish navbati) bu ma'noga mos kelmaydi.
> `Emitter.record(..., mono=recv_mono_us)` (`schema.py:226`) aynan shu
> uchun bor. §14.4 buzilmaydi: `recv_mono_us` o'z nomi bilan turadi va
> systemd timestamp'lari o'z maydonlarida.

#### `cgroup_events`

| manba | record maydoni | consumer |
|---|---|---|
| `cgroup.read_keyed(".../memory.events")["oom_kill"]` (`cgroup.py:263`) | `oom_kill` (kumulyativ, delta EMAS) | `reduce._oom_series` (`reduce.py:590`) |
| cgroup scope nomi (SUT scope'i) | `scope` | `reduce._oom_series` (`reduce.py:587`) |
| namuna vaqti | envelope `mono_us` | `reduce._oom_series` (`reduce.py:589`) |

> **NEGA kumulyativ:** `reduce._first_oom_increase_us()` (`reduce.py:597`)
> ketma-ket namunalar O'SISHINI izlaydi. Delta yozilsa, oyna chegarasidagi
> `base` qiymati yo'qolib, 6-band (`oom_kill`) yolg'on `unverified` bo'lardi.

#### `action` / `action_defer` / `actor_signal`

| manba | record maydoni | consumer |
|---|---|---|
| aktor | `action_id` | `reduce.split_trials` (`reduce.py:471`), `validate.check_actions` (`validate.py:631`) |
| aktor | `action_class` | `reduce.split_trials` (`reduce.py:472`), `evaluate_fr_b` (`reduce.py:1548`) |
| sozlangan kutish (masalan `RestartSec`) | `policy_delay_us` | `reduce.split_trials` (`reduce.py:473`) — §6.3: `L_dec` dan **ALOHIDA** |
| aktor | `deferred` (bool) | `reduce.split_trials` (`reduce.py:474`; `defer` va `action_class=="defer"` ham qabul qilinadi) |
| `action_defer` uchun | `reason` | `RAW_CONTRACT` |
| aktorning O'Z da'vosi | `success` (bool) | `reduce.actor_success_signal` (`reduce.py:877`) — §5 FR-A ning **birlamchi operandi** |
| da'vo manbasi | `source` | §14.4 talab qiladi; `reduce.py` runtime'da o'qimaydi (u `actor_signal_source` ni O'ZI chiqaradi, `reduce.py:1227`) |

#### `fault_inject` / `fault_effective` / `baseline_window` / `guard_event`

| manba | record maydoni | consumer |
|---|---|---|
| injeksiya chaqirig'i atrofi | `mono_us_before_call`, `mono_us_after_call` | `reduce.fault_effective_us` (`reduce.py:567`) |
| fault turi | `kind` | `reduce.reduce_trial` → `evaluate_fr_b` (`reduce.py:1551`) |
| driver qarori | `fault_effective.mono_us` + `source` | `reduce.fault_effective_us` (`reduce.py:558`) |
| `R_ref` oynasi | `mono_us_begin`, `mono_us_end` | `reduce.reference_throughput` (`reduce.py:617`, `:618`) |
| guard (mustaqil jarayon) | `guard_event`: `reason`, `action`, envelope `mono_us`, **`trial_id` YO'Q** | `reduce.split_trials` monotonic atributsiyasi (`reduce.py:510`), `derive_disposition` → `aborted_guard` (`reduce.py:1437`) |

### 4.4 Uchala gumon qilingan nomuvofiqlikning hukmi

| # | gumon | hukm | dalil |
|---|---|---|---|
| 1 | `trial_begin`: `pressure_band` vs `pressure_level` | **HAQIQIY** | `reduce.Trial.pressure_band` runtime'da `begin["pressure_band"]` ni o'qiydi (`reduce.py:389`) va `trial_metrics` ga `pressure_band` deb yozadi (`reduce.py:1562`); manba esa `schedule.P1_FACTORS` da `pressure_level` (`schedule.py:146`) va `Trial.as_dict()` uni shu nom bilan chiqaradi (`schedule.py:183`). **Hal:** §4.3 map'i |
| 2a | `probe_sample`: `progress` vs `progress_counter` | **HAQIQIY va eng xavfli** | `reduce.probe_from_record` `rec.get("progress")` ni o'qiydi (`reduce.py:298`); `prober.PROBE_FIELDS` da ustun `progress_counter` (`prober.py:153`) va `PREREGISTRATION.md` §14.4 aynan `progress_counter` ni majburiy qilgan. `progress=None` bo'lsa §4.5 throughput bandi o'lchanmaydi → `vr=None` → birlamchi endpoint yo'qoladi. **Hal:** §4.5 adapteri |
| 2b | `probe_sample`: `pid_seen` vs `sut_pid_seen` | **HAQIQIY EMAS (zararsiz)** | `pid_seen` faqat `RAW_CONTRACT` (`reduce.py:1904`) va `PROBE_CSV_FIELDS` (`reduce.py:270`) ichida bor; `reduce.py` uni **runtime'da hech qayerda o'qimaydi**. Map **ixtiro qilinmaydi**; ustun `sut_pid_seen` bo'lib qoladi va `RAW_CONTRACT`/`PROBE_CSV_FIELDS` dagi `pid_seen` — eskirgan hujjat qatori (§4.6) |
| 2c | `probe_sample`: `invocation_id_seen` | **NOMUVOFIQLIK YO'Q** | ikki tomon ham `invocation_id_seen` deydi (`prober.py:155`, `reduce.py:299`) |
| 3 | `unit_state`: snake_case vs xom systemd nomlari | **HAQIQIY — lekin faqat 5 maydonda** | runtime'da o'qiladi: `active_state` (`reduce.py:886`), `n_restarts` (`reduce.py:770`, `:1523`, `validate.py:674`), `invocation_id` (`reduce.py:1520`, `validate.py:667`), `active_enter_ts_mono_us` / `active_exit_ts_mono_us` (`reduce.py:1341-1342`). `UnitWatcher` esa `ActiveState`, `NRestarts`, `InvocationID`, `ActiveEnterTimestampMonotonic`, `ActiveExitTimestampMonotonic` beradi (`units.py:1113`, `STATE_PROPS` = `units.py:122`). **`result`** gumon ro'yxatida bor, lekin **runtime'da o'qilmaydi** — u `RAW_CONTRACT` dagi hujjat qatori (§4.6). **Hal:** §4.3 — xom nom + snake_case, ikkisi ham |

### 4.5 `probe_sample` normalizatsiya adapteri

**Muammo:** `progress_counter` → `progress` map'ini driver **yozish paytida
qila olmaydi**, chunki `probe.csv` ni prober mustaqil jarayon sifatida yozadi
(§1.3 majburiyat 7) va ustun nomlari `prober.PROBE_FIELDS` da qat'iy
(`prober.py:857`: `CsvWriter(args.csv, PROBE_FIELDS)`). Ustunni qayta nomlash
`PREREGISTRATION.md` §14.4 ni buzardi.

**Hal (normativ):** xom `probe.csv` **o'zgarmaydi** (`CONTRIBUTING.md` §1.4
append-only), normalizatsiya **reduksiya kirishida** bo'ladi:

```
rows   = reduce.load_probe_csv(path)          # xom, tahrirlanmagan
probes = [driver.normalise_probe_row(r) for r in rows]
run    = reduce.RawRun(records=…, probes=probes, sources=[…])
```

`reduce.RawRun` oddiy dataclass (`reduce.py:307`), `probes` ro'yxati
to'g'ridan-to'g'ri beriladi — demak `reduce.RawRun.load()` majburiy emas va
`reduce.py` ga tegilmaydi.

`driver.normalise_probe_row()` majburiyatlari:

| # | majburiyat | nega |
|---|---|---|
| 1 | `progress_counter` bo'lsa, `progress` **qo'shiladi** (xom kalit **o'chirilmaydi**) | `reduce.probe_from_record` `progress` ni o'qiydi (`reduce.py:298`); xom kalit §14.4 uchun qoladi |
| 2 | Mavjud `progress` **ustiga yozilmaydi** | JSONL yo'lidan kelgan record allaqachon to'g'ri nomda bo'lishi mumkin |
| 3 | `record_type = "probe_sample"` | `reduce.RawRun` turni shu bilan ajratadi |
| 4 | `trial_id` bo'sh bo'lsa, monotonic vaqt bo'yicha atributsiya qilinadi (`guard_event` bilan bir usul) va buni `warnings` ga yozadi | §4.5-a ga qarang |
| 5 | **Hech qanday qiymat o'zgartirilmaydi** — faqat kalit qo'shiladi | normalizatsiya o'lchov emas |

Natija **derived va regenerable** (`CONTRIBUTING.md` §1.4): xom CSV'dan har
doim qayta hosil qilinadi va alohida faylga ham yozilishi mumkin.

**(a) `probe_sample.trial_id` ni kim qo'yadi — ochiq qaror, v1.1 da hal
qilindi.** `Prober.trial_id` jarayon boshida `--trial-id` bilan o'rnatiladi
(`prober.py:839`, `:866`) va **ishlash davomida o'zgartirish mexanizmi yo'q**
(signal ham, control socket ham). Shuning uchun:

> **Normativ:** driver **har trial uchun alohida prober jarayoni** ishga
> tushiradi, `--trial-id <Trial.trial_id>` bilan, va uni trial oxirida
> to'xtatadi.
>
> **NEGA:** aks holda butun run bitta `trial_id` ostida yoziladi va
> `reduce.split_trials()` (`reduce.py:453`) barcha probe'ni bitta trial'ga
> biriktiradi — ya'ni 119 trial probe'siz qoladi va `vr=None` bo'ladi.
> Jarayon ishga tushishi washout ichida bo'ladi, ya'ni o'lchanadigan oynaga
> tushmaydi; narx uchala arm'da bir xil, demak §8.2 kafolati buzilmaydi; va
> `seq` trial ichida monotonik bo'lib §14.6-3 tekshiruvi aniqroq ishlaydi.
>
> **CHEKLOV:** bu qo'shimcha vaqt §1.3 majburiyat 9 bo'yicha **o'lchanadi va
> yoziladi**, taxmin qilinmaydi.

### 4.6 `reduce.py` o'qiydi, lekin `RAW_CONTRACT` e'lon qilmaydi

`RAW_CONTRACT` **majburlanmaydi** — u `reduce.py` dan tashqarida hech qayerda
ishlatilmaydi (butun repo bo'ylab tekshirildi: faqat `reduce.py:1898` dagi
ta'rif). Ya'ni u **hujjat**, validator emas. Shuning uchun u haqiqiy kod bilan
ikki tomonga drift qilgan:

| maydon | holat | qaror |
|---|---|---|
| `engine_state` (`unit_state`) | runtime'da o'qiladi (`reduce.py:889`), `RAW_CONTRACT` da **yo'q** | arm C uchun; P1 da (`arm ∈ {A, no_action}`) **yozilmaydi**. §4.3 jadvaliga qo'shildi |
| `harm_indicator` (`trial_begin`) | runtime'da o'qiladi (`reduce.py:1552`), `RAW_CONTRACT` da **yo'q** | §14.7 ochiq bo'shlig'i: P1 da FR-B hisoblanmaydi, demak **yozilmaydi** |
| `result` (`unit_state`) | `RAW_CONTRACT` da bor, runtime'da **o'qilmaydi** | `Result` + `result` ikkisi ham yoziladi (arzon, diagnostik) |
| `pid_seen`, `rt_us`, `mono_us_recv` (`probe_sample`) | `RAW_CONTRACT`/`PROBE_CSV_FIELDS` da bor, runtime'da **o'qilmaydi** | prober nomlari (`sut_pid_seen`, `rt_us`, `mono_us_recv`) o'z holida qoladi; `pid_seen` uchun map **ixtiro qilinmaydi** |
| `source` (`actor_signal`), `reason`/`action` (`guard_event`), `rng_seed`/`git_dirty`/`run_mode` (`run_meta`) | `RAW_CONTRACT` da bor, `reduce.py` o'qimaydi | `validate.py` va reproducibility uchun **majburiy qoladi** |
| `PROBE_CSV_FIELDS` (`reduce.py:268`) `mono_us` va `real_us` ni sanaydi | `probe.csv` da bunday ustun **yo'q** (`mono_us_send`, `real_us_send` bor) | `load_probe_csv` `PROBE_CSV_FIELDS` ni **ishlatmaydi** (u `csv.DictReader` natijasini to'g'ridan-to'g'ri oladi, `reduce.py:278`), demak zararsiz. `probe_from_record` `mono_us_send` ni afzal ko'radi (`reduce.py:290`) |

**v1.1 da qayd etilgan CHEKLOV — v1.2 da YOPILDI.** v1.1
`validate._stream_key()` izohining eskirganini qayd etgan edi (u
*"`Emitter.envelope()` `stream` ni record'ga YOZMAYDI"* deydi, holbuki
`schema.py:219` uni yozadi va `ENVELOPE_FIELDS` sanaydi — `schema.py:244`).
`agent/validate` buni **tuzatdi**: `_stream_key()` endi oqim kalitini
`(emitter, stream)` dan oladi va o'z docstring'ida §4.2-3 ga havola qilib
`stream == record_type` ni `check_envelope` da `stream_not_record_type`
sifatida **majburlaydi** (`revix/validate.py:483`). Ya'ni §4.2 qoida 3 endi
hujjat emas, **tekshiriladigan invariant**.

### 4.7 Reducer kirishi BITTA target va BITTA unit bo'lishi SHART (v1.2)

#### Defekt

`reduce.split_trials()` probe'larni **faqat `trial_id`** bo'yicha guruhlaydi
(`revix/reduce.py:453`) va `unit_state` ni **faqat trial** bo'yicha
(`revix/reduce.py:422` ichidagi `pick()`). `target` ham, `unit` ham
**umuman ko'rilmaydi**.

Lekin `PREREGISTRATION.md` §8.2 har trial'da **bystander** xizmatini ham probe
qilishni talab qiladi (spillover detektori; `prober.py` ikki target bilan
ishlaydi va bystander contract'ni yo'qotsa trial `contaminated` bo'ladi, §12).
Demak `probe.csv` da **ikki target**, hodisa oqimida esa **ikki unit**
qonuniy ravishda mavjud.

Filtrlanmasa:

| nima aralashadi | nima buziladi |
|---|---|
| bystander probe'lari SUT ning progress seriyasiga | `R_ref` (§4.5), `D_probe`, `D_eff` — `window_throughput()` `progress` ni bitta invocation ichida farqlaydi (`revix/reduce.py:533`), ikki xizmatning hisoblagichi aralashsa natija **ma'nosiz** |
| bystander probe'lari uzilish hisobiga | `probe_gaps()` (§4 censoring) — ikki target navbatma-navbat yozsa uzilish **yo'qoladi** |
| bystander `NRestarts` / `InvocationID` SUT ning holatiga | VR **3-band** (`invocation_changed`) va **4-band** (`nrestarts_changed`) — `revix/reduce.py:770`, `:1520` |

#### Qoida (normativ)

| # | qoida | nega |
|---|---|---|
| 1 | **Xom fayllar barcha target va unit ni saqlaydi** | bystander trace'i §12 ning `contaminated` disposition'i uchun **dalil**, va `datasets/` append-only (`CONTRIBUTING.md` §1.4) |
| 2 | **Reducer'ga berilayotgan hamma narsa SUT ga filtrlanadi** — §4.5 dagi **aynan o'sha adapter chegarasida**, `progress_counter` → `progress` normalizatsiyasi bilan birga | bitta joyda, bitta marta: ikki xil chegarada filtrlash ikki xil xatoga olib kelardi |
| 3 | Filtrlangan record'larda `target` (probe) va `unit` (`unit_state`) **saqlanib qoladi** | filtr **tekshirilishi** mumkin bo'lishi uchun: nimaning qolgani record'ning o'zida ko'rinadi |

> **NEGA filtr xom faylda emas:** xom faylni kesish `CONTRIBUTING.md` §1.4
> ning to'g'ridan-to'g'ri buzilishi bo'lardi, **va** spillover dalilini
> yo'q qilardi — ya'ni `contaminated` ni aniqlab bo'lmasdi. Filtr **derived**
> qatlamda, regenerable.

**Validator qoplashi:** `agent/validate` `probe_targets_mixed` ni **`error`**
sifatida beradi (`revix/validate.py:1897`) va `unit_state` uchun mos
tekshiruvni qo'shmoqda. Ya'ni filtrlanmagan kirish **jim o'tmaydi**.

---

## 5. `T_trial` — recovery horizon (v1.1 da ta'riflandi)

### 5.1 Nega bu bo'lim bor

`PREREGISTRATION.md` `T_trial` ga **uch joyda tayanadi**:

- §6.2 — `trial_downtime` = horizon `T_trial` ichidagi epizod downtime'lari
  yig'indisi; horizon down holatda tugasa → **`T_trial` da censored**;
- §6.4 — `loop_rate = Δ NRestarts / T_trial`, va `loop_detected = 1` ⟺
  `T_trial` ichida ≥5 invocation;
- §12 — `censored` disposition (*"horizon down holatda tugadi"*).

Lekin `PREREGISTRATION.md` **hech qayerda `T_trial` ga raqam bermaydi**.
Tekshirildi (`preregistration/v1.4` da **qayta** tekshirildi): `T_trial` faqat
§6.2 va §6.4 da **ishlatiladi** — beshta o'rinda, barchasi foydalanish —
ta'riflanmaydi; §9.4 trial jadvalini
fazalar bilan beradi (`pre-flight → baseline 10 s → ramp 5 s → hold 12 s →
washout ≥20 s ≈ 52 s`), lekin recovery horizon'ini raqamlamaydi.
*(2026-10-03: bu `preregistration/v1.4` dagi §9.4 dan iqtibos; `preregistration/v1.11`
dan beri §9.4 `hold 13 s` va `≈ 53 s` deydi — qarang "v1.2 ikkinchi revizyasi".)*

`reduce.py` esa uni **mavjud deb hisoblaydi**: `Trial.t_trial_us` =
`trial_end.mono_us − trial_begin.mono_us` (`reduce.py:415`). Ya'ni horizon
**driver nimani yozsa — o'sha**. Raqamsiz qoldirilsa, u jimgina
implementatsiya tasodifiga aylanadi.

### 5.2 Ta'rif

`T_trial` **jimgina konstanta EMAS.** U `schedule.TrialTimeline` ning
muzlatilgan invariantlaridan **hisoblanadi** va `run_meta` ga **oshkora
yoziladi**.

```
T_trial = TrialTimeline.t_pressure_off + TrialTimeline.w_stab_s + P
```

bu yerda `P` — probe davri (`reduce.P_US` = 100 ms), va `T_trial`
`trial_begin` dan (ya'ni `TrialTimeline` ning `t = 0` nuqtasidan) o'lchanadi.

**Majburlanadigan invariant:**

```
TrialTimeline.t_verify_end_earliest  ≤  T_trial  ≤  TrialTimeline.total_s
```

Invariant buzilsa — **istisno, ogohlantirish emas** (`TrialTimeline`
ning o'z uslubi, `schedule.py:806`).

**Pilot qiymatlari** (`TrialTimeline()` default'laridan **ishga tushirilib**
hisoblangan):

| kattalik | qiymat |
|---|---|
| `t_inject` | 23.0 s |
| `t_verify_end_earliest` | 31.0 s |
| `t_pressure_off` | 33.0 s |
| `w_stab_s` | 8.0 s |
| `P` | 0.1 s |
| **`T_trial`** | **41.1 s = 41 100 000 µs** |
| `total_s` (yuqori chegara) | 53.0 s |

Hisob: `t_hold_start = 5.0 + 10.0 + 5.0 = 20.0 s`; `t_pressure_off = 20.0 +
13.0 (hold_s = HOLD_CAP_S) = 33.0 s`; **`T_trial = 33.0 + 8.0 + 0.1 =
41.1 s`**; `total_s = 33.0 + 20.0 (washout) = 53.0 s`. Invariant:
`31.0 ≤ 41.1 ≤ 53.0`.

> **v1.2 ikkinchi revizyasi (2026-10-03):** bu jadvalda `t_pressure_off`
> 32.0 → 33.0 s, `T_trial` 40.1 → 41.1 s va `total_s` 52.0 → 53.0 s ga
> o'zgardi, chunki `PREREGISTRATION.md` §17.5 **O3** (`preregistration/v1.11`)
> `hold_cap_s` ni 12 s dan 13 s ga ko'tardi. **Formula o'zgarmadi** — faqat
> uning default'dagi qiymati. Amendment log'ga qarang.

### 5.3 NEGA aynan shu formula

| had | nega |
|---|---|
| `t_pressure_off` | VR oynasining **eng kech qonuniy boshlanishi**. §9.4 analiz **erishilgan** pressure'dan foydalanadi; pressure o'chgandan keyin kelgan `t_up` — treatment'dan tashqaridagi recovery, demak oyna boshlanishi uchun oxirgi ma'noli nuqta |
| `+ w_stab_s` | §4 oynaning **TO'LIQ** kuzatilishini talab qiladi. `evaluate_vr()` kesilgan oynada `vr=None`, `reason="window_truncated"` qaytaradi (`reduce.py:831`), va `None` hech qachon `False` ga aylantirilmaydi. Horizon qisqa bo'lsa — ma'lumot yetishmovchiligi **ommaviy** `vr=None` ga aylanadi va birlamchi endpoint hisoblanmaydi |
| `+ P` | `window_complete` sharti `last_probe_us >= win_end − window_slack_us`, va `window_slack_us == probe_period_us` (`reduce.py:158`, `:751`). §6.1 probe kvantlashini (±P) ochiq e'lon qilgan; bitta davr qo'shilmasa, oyna chegarasidagi probe tasodifan yetib kelmasligi mumkin |
| yuqori chegara `total_s` | `trial_end` rejalashtirilgan jadval ichida qolishi kerak, aks holda washout va keyingi trial bir-biriga kirib ketardi (§8.4 `T_w` poli) |
| pastki chegara `t_verify_end_earliest` | §4 ning eng yaxshi holatdagi oynasi horizon ichiga **sig'ishi shart**; sig'masa shartnoma o'z-o'ziga qarama-qarshi bo'lardi |

**Busiz nima buzilardi:** horizon jimgina `total_s` (53 s) yoki `t_pressure_off`
(33 s) qilib olinsa — birinchi holatda `loop_rate` maxraji `loop_detected`
ta'rifidan ajralib ketardi, ikkinchi holatda deyarli har trial
`window_truncated` bo'lib `vr=None` chiqardi. Ikkala holatda ham sabab
hujjatda **yozilmagan** bo'lardi, ya'ni reviewer "horizon qanday tanlandi?"
degan savolga javob olmasdi — bu aynan `W_stab` ga qilingan *"siz uni natija
uchun tanlagansiz"* hujumining ikkinchi shakli.

### 5.4 Driver va analiz majburiyatlari

| # | majburiyat | nega |
|---|---|---|
| 1 | `T_trial` **hisoblanadi**, kodga yozilgan konstanta sifatida berilmaydi | `W_stab` yoki timeline o'zgarsa, horizon o'zi kuzatib boradi |
| 2 | Hisoblangan qiymat `run_meta.t_trial_us` ga **yoziladi** (§1.1, §4.3) | *"jimgina konstanta yo'q"*: horizon har doim **qayd etilgan, hisoblangan run parametri** |
| 3 | Formula va hadlar `run_meta.t_trial_formula` ga matn sifatida yoziladi | qayta hisoblash uchun hujjat kerak bo'lmasligi |
| 4 | §5.2 invarianti **majburlanadi**; buzilsa run **boshlanmaydi** | fail-closed, §1.3-2 bilan bir uslub |
| 5 | `trial_end` `trial_begin.mono_us + T_trial` da emit qilinadi — **tolerans: bitta probe davri `P`** (yoki undan **oldin**, agar disposition `aborted_guard` / `harness_error` bo'lsa) | `reduce.Trial.end_us` (`reduce.py:406`) censoring nuqtasi sifatida shuni oladi |
| 6 | `analyze.py` `t_trial_us` ni `analysis.json` ga ko'chiradi (§2.3-9) | har jadval/figura qaysi horizon ostida censor qilinganini ko'rsatadi (§6.2 `recovered_within_horizon: k/n`) |

> **v1.2 — majburiyat 5 ning toleransi raqamlandi: `P` (bitta probe davri,
> 100 ms).** v1.1 "aynan" deb yozgan edi; **haqiqiy soat bilan "aynan"
> erishib bo'lmaydi** (yozish navbati, emit kechikishi).
>
> **NEGA aynan `P`:** `PREREGISTRATION.md` §6.1 probe kvantlashini (`±P`)
> **ochiq e'lon qilgan** va uni **tuzatmaydi** — ya'ni loyihada bitta probe
> davri allaqachon qabul qilingan noaniqlik birligi. Horizon toleransini
> boshqa raqam qilish yangi, asoslanmagan birlik kiritardi; kichikroq
> qilish esa to'g'ri ishlagan run'ni rad etardi.
>
> `agent/validate` buni shunday amalga oshirgan:
> `T_TRIAL_TOLERANCE_US = P_US` (`revix/validate.py:179`), tekshiruv
> `check_trial_horizon` (`revix/validate.py:1769`), `error` kodi
> `trial_horizon_mismatch`; `aborted_guard` va `harness_error` uchun
> **qisqa** trial kutilgan holat.

### 5.5 Qamrov: bu qaror SHU hujjatning qarori

`PREREGISTRATION.md` bu amendment bilan **tahrirlanmadi**. `T_trial`
pre-registration'ning bo'shlig'i va u yerda ham amendment qilinishi kerak —
bu **boshqa agentning** ishi (`CONTRIBUTING.md` §1.1 protsedurasi bo'yicha).
Shu bo'lim esa `driver-contract/v1.1` ning qarori: driver va analiz
modullari parallel yozilishi uchun raqam **hozir** kerak.

Agar `PREREGISTRATION.md` amendment'i boshqa ta'rif bersa — **u ustun**, va
bu bo'lim shunga moslashtiriladi (`CONTRIBUTING.md` §3: nomuvofiqlik jimgina
tuzatilmaydi).

> **v1.2 tekshiruvi:** `PREREGISTRATION.md` oradan `v1.4` ga ko'tarildi
> (2026-10-02, **§15 muhit fingerprint'i** qo'shildi). v1.4 ning
> *"O'zgarMAGAN qiymatlar — to'liq ro'yxat"* jadvali `T_trial` ni **sanamaydi**
> va §6.2/§6.4 matni o'zgarmadi — ya'ni `T_trial` **hali ham ta'riflanmagan**
> va §5 ning formulasi kuchda qoladi. Shuningdek v1.4 ning `W_stab_pilot = 8 s`,
> `hold_cap_s = 12 s` va `guard_sustain_s = 15 s` muzlatilgan qiymatlari
> §5.2 ning hisobiga **kiradigan** qiymatlar bo'lib, ular **o'zgarmadi** —
> demak `T_trial = 40.1 s` ham o'zgarmaydi.

> **2026-10-03 tuzatma (v1.2 ikkinchi revizyasi):** yuqoridagi xulosa
> `preregistration/v1.4` uchun **to'g'ri edi**, lekin **hozir amal qilmaydi**.
> `preregistration/v1.11` (§17.5 **O3**) `hold_cap_s` ni **12 s → 13 s** ga
> o'zgartirdi, shu sababli §5.2 ning hisobiga kiradigan `hold_s` o'zgardi va
> default `T_trial` = `33.0 + 8.0 + 0.1` = **41.1 s** (`41 100 000 µs`).
> `W_stab_pilot = 8 s` va `guard_sustain_s = 15 s` o'zgarmadi; **§5.2 ning
> formulasi va §5.5 ning "`PREREGISTRATION.md` ustun" qoidasi o'zgarmadi** —
> bu hujjatning formulasi kuchda, faqat uning default'dagi qiymati siljidi.

---

## 6. `figures.py` bog'liqligi: `matplotlib` (v1.1 da qayd etildi)

**Holat:** §3 `figures/<nom>.svg` chiqishini **matplotlib** bilan talab
qiladi, va bu talab `driver-contract/v1` dan beri turadi (v1 §3, o'zgarmagan).
Lekin `INSTALLATION.md` ning Python paketlar ro'yxati —
`psutil`, `python-systemd`, `dbus`, `pyyaml`, `numpy`, `scipy`
(`INSTALLATION.md` 39-qator) — **matplotlib ni sanamaydi**. Repo bo'ylab
tekshirildi: `matplotlib` so'zi faqat shu hujjatning §3 ida uchraydi, birorta
`.py` faylda yo'q.

**Bu bo'shliq, yangi bog'liqlik emas.** `CONTRIBUTING.md` §4 ning *"Yangi
bog'liqlik qo'shilmadi (`PREREGISTRATION.md` §10.3)"* qoidasi bajarilgan:

- §10.3 taqiqi **statistika** paketlariga tegishli (`statsmodels`,
  `lifelines` mavjud emas; Cochran–Armitage / KM / log-rank / RMST
  **o'zimiz yozamiz**). `matplotlib` statistik hisob qilmaydi — u faqat
  `analysis.json` dagi **tayyor raqamlarni** SVG ga chizadi (§3: figura
  modulida hisob yo'q).
- `matplotlib` shartnomada **v1 dan beri** talab qilingan, ya'ni v1.1 hech
  narsa qo'shmaydi — faqat allaqachon mavjud talabni **ko'rinadigan**
  qiladi.

**NEGA qayd etish kerak:** `run_meta.module_versions` (§1.1) qaysi kod
versiyasi bilan o'lchangani va chizilganini bog'laydi. Bog'liqlik
`INSTALLATION.md` da sanalmasa, u `module_versions` ga ham tushmasligi
mumkin — ya'ni figura qaysi matplotlib bilan hosil qilingani yo'qoladi.
Figura esa `figures/<nom>.json` orqali tekshirilishi kerak (§3).

**Majburiyatlar:**

| # | majburiyat | nega |
|---|---|---|
| 1 | `figures.py` `matplotlib` dan **faqat** `Agg` backend va SVG chiqishini ishlatadi | headless, GUI bog'liqligi yo'q |
| 2 | `matplotlib` **FAQAT** `figures.py` da import qilinadi | `reduce.py` / `analyze.py` offline va pur qoladi |
| 3 | `matplotlib.__version__` `run_meta.module_versions` ga yoziladi | yuqoridagi NEGA |
| 4 | `matplotlib` yo'q bo'lsa — `figures.py` **aniq xato** bilan to'xtaydi, bo'sh yoki qisman SVG yozmaydi | jimgina buzilgan figura — soxta natija |

**Egalik:** `INSTALLATION.md` **bu amendment bilan tahrirlanmaydi** — u
boshqa agentning fayli. Bu yerda bo'shliq qayd etiladi va shunday
**xabar beriladi** (`CONTRIBUTING.md` §3-1, §3-2: nomuvofiqlikni o'z
hujjatingizda ochiq savol sifatida qayd eting, jimgina tuzatmang).
`INSTALLATION.md` ga qo'shilishi kerak bo'lgan qator:

```
| matplotlib | figures.py: SVG figuralar (Agg backend) — rejada |
```

**v1.2 tekshiruvi:** `INSTALLATION.md` 39-qatori hali ham o'sha ro'yxat, va
`matplotlib` butun faylda **0 marta** uchraydi — bo'shliq ochiq qolgan.

---

## 7. Driver'ga tegishli o'lchangan tuzoqlar (v1.2)

Bu bo'lim `01-muhit-tekshiruvlari.md` §4 bilan bir sinfdagi defektlarni
yig'adi: **`systemctl show` qaytargan qiymat yolg'on bo'lishi mumkin.** Ikkisi
ham `agent/envcheck` tomonidan **shu mashinada o'lchangan** (systemd 257);
men ularni **o'zim ishga tushirmadim**, shuning uchun manba ochiq ko'rsatilgan.

### 7.1 `RestartSteps=` `RestartMaxDelaySec=` bo'lmasa JIMGINA e'tiborsiz qoldiriladi

**O'lchov (`agent/envcheck`, systemd 257):** `RestartSteps=` qabul qilinadi,
`systemctl show` uni **ko'rsatadi**, lekin journal
*"Service has RestartSteps= but no RestartMaxDelaySec= setting. Ignoring."*
deydi va interval ~**1.03 s** da qotib qoladi — ya'ni backoff **yo'q**.

**Ishlayotgan juftlik (o'lchangan qiymatlar, yozib qoldirish uchun):**
`RestartSec=1s` + `RestartSteps=3` + `RestartMaxDelaySec=4s` →
intervallar **1.040, 1.631, 2.566, 4.058, 4.031 s** (eksponensial, keyin
cap'da tekis).

**Normativ qoida:** arm konfiguratsiyasini yozadigan har qanday yordamchi
`RestartSteps=` va `RestartMaxDelaySec=` **juftligini kodda majburlaydi** va
`systemctl show` ning qaytargan qiymatiga **ishonmaydi**.

> **NEGA (va busiz nima buzilardi):** P1 da Baseline B **yo'q** (§9.3: faqat
> `A` va `no_action`), demak bu P1 ni bloklamaydi. Lekin H2 ning butun kuchi
> *"systemd'ning O'Z eksponensial backoff'i"* ga qarshi taqqoslashda —
> `01-texnologiya-auditi.md` §1 ga ko'ra `RestartSteps=` aynan shu sababli
> systemd ≥254 ni talab qiladi (`INSTALLATION.md` 34-qator). Juftlik
> majburlanmasa, "kuchli baseline B" **jimgina Baseline A ga aylanadi** va
> taqqoslash o'z ma'nosini yo'qotadi — `systemctl show` esa buni
> **ko'rsatmaydi**.

### 7.2 O'chgan unit tuzog'i — systemd 257 da QAYTA tasdiqlandi

**O'lchov (`agent/envcheck`, systemd 257):** tirik unit `systemctl show` da
**286** property qatori berdi; `--collect` bilan chiqib ketgandan keyin
**aynan o'sha** `show` **rc=0** va **263** qator **default** qaytardi —
`LoadState=not-found`, `RestartSteps=0`, `MemoryMax=infinity`.

**Natija:** §1.1 ning *"`units_show` unit TIRIK paytida olinishi shart"*
talabi shu systemd versiyasida **tasdiqlangan**, nafaqat eski mashinadan
**meros**. `01-muhit-tekshiruvlari.md` §4 o'z o'lchovini eski mashinada
qilgan (u yerda 268 qator), va `PREREGISTRATION.md` §15.6(3) aynan shu qayta
tasdiqni **talab qilgan** edi.

> **NEGA raqamlar farq qiladi:** 268 (eski mashina) va 263 (systemd 257) —
> **default qator soni versiyaga bog'liq**. Shuning uchun tekshiruv
> *"qator soni N mi?"* emas, **`LoadState`** bo'lishi kerak: `not-found` —
> unit o'chgan, demak dump **ishonchsiz**.

### 7.3 Guard kalibratsiyasining ochiq sharti

`02-guard-kalibratsiyasi.md` **§7 masala 1** guard chegaralarining
`user@ ≈ lab` topilmasi **bo'sh desktop** sharti uchun o'lchanganini va
**band desktop'da QAYTA O'LCHANISHI kerakligini** yozadi (*"Band tizimda
`full` ancha past bo'ladi va guard sezgirligi o'zgaradi"*). Shart —
**aynan band desktop**, "boshqa mashina" emas.

**Driver uchun natijasi:** §1.3-2 ning fail-closed qoidasi bu bilan
**yumshamaydi**; `00-pilot-topologiya.md` §6 ga ko'ra guard testi keyingi har
bir qadamni gate qiladi, va `CONTRIBUTING.md` §1.2 *"guard tasdiqlanmasa
hech qanday pressure eksperimenti ishga tushirilmaydi"* deydi.

---

## 8. Ochiq nomuvofiqliklar — KOD vs KOD (v1.2 qayd etadi, HAL QILMAYDI)

`CONTRIBUTING.md` §3 aniq: nomuvofiqlik topilsa **o'zingiz tuzatmang** —
xabar bering va o'z hujjatingizda **ochiq savol** sifatida qayd eting.
Quyidagilar muzlatilgan hujjat bilan kod orasidagi ziddiyat **emas**, balki
**ikki commit qilingan va test bilan qoplangan modul** orasidagi ziddiyat.
Shuning uchun ularning har biri **o'z o'zgarishini va o'z asoslanishini**
talab qiladi; v1.2 ularni **hal qilmaydi**.

### 8.1 Disposition ustuvorligi — `schedule.py` vs `reduce.py`

| manba | tartib | dalil |
|---|---|---|
| `schedule.DISPOSITION_RULES` | **1.** `harness_error` → **2.** `guard_fired` ⇒ `aborted_guard` → … | `revix/schedule.py:676`, `:677`, `:678` |
| `reduce.derive_disposition` | **1.** `guard_events` ⇒ `aborted_guard` → **2.** xom `contaminated`/`washout_timeout`/`harness_error` | `revix/reduce.py:1418`, `:1436`, `:1437`, `:1438` |

Ikki fakt **bir vaqtda** to'g'ri bo'lgan trial'da (harness ham xato berdi,
guard ham ishladi) ikki yo'l **boshqa disposition** beradi:
`schedule` → `harness_error`, `reduce` → `aborted_guard`.

**NEGA bu ahamiyatli:** §12 har trial'ga **aynan bitta** disposition talab
qiladi, va `aborted_guard` bilan `contaminated` birlamchi analizdan
**chiqariladi**, lekin ularning **ulushi natija sifatida beriladi**. Demak
kelishmovchilik **numerator'ni ham**, **hisobot qilinadigan eksklyuziya
darajasini ham** o'zgartiradi — ikkisi ham `analysis.json` ning
`exclusions` bo'limiga chiqadi (§2.2, §2.3-5).

**Interim qoida (orkestrator bergan, v1.2 qayd etadi):**

| # | qoida |
|---|---|
| 1 | **Avtoritet — driver'ning `trial_end.disposition` i**, u `schedule.explain_disposition()` dan olinadi (`revix/schedule.py:728`) |
| 2 | `reduce.derive_disposition()` — **kross-tekshiruv**, avtoritet emas |
| 3 | Kelishmovchilik **validator topilmasi** sifatida chiqadi, jimgina yarashtirilmaydi (`reduce_trial` allaqachon `disposition_conflict` ni beradi) |

> **NEGA driver avtoritet:** `schedule.DISPOSITION_RULES` ustuvorligini
> **oshkora, tartiblangan va total** jadval sifatida beradi va import
> paytida uning yopiq enum bilan mos kelishini tekshiradi
> (`revix/schedule.py:691`, `:697` — `assert` emas, chunki `python -O` uni
> o'chirardi). Uning izohi tartibning **sabab zanjirini** ham yozadi:
> *"harness o'zi ishlamagan bo'lsa, boshqa hech bir kuzatuvga ishonib
> bo'lmaydi"*. `reduce.py` ning tartibi esa kuzatuv **log faktlaridan**
> chiqariladi. Haqiqiy tuzatish `schedule.py` yoki `reduce.py` ga tegadi —
> **ikkisi ham commit qilingan va test bilan qoplangan** — demak u alohida
> o'zgarish, o'z asoslanishi bilan.

**Qo'shimcha kuzatuv (shu bilan bog'liq, ham HAL QILINMAGAN):** birlamchi
to'plamning nomi ikki modulda ikki xil:
`reduce.PRIMARY_DISPOSITIONS = ("complete",)` (`revix/reduce.py:117`),
`schedule.PRIMARY_ANALYSIS_DISPOSITIONS = ("complete", "censored")`
(`revix/schedule.py:740`). `reduce` ning `("complete", "censored")` to'plami
`SURVIVAL_DISPOSITIONS` deb nomlangan (`revix/reduce.py:121`). Ya'ni
ehtimol **nom** farqi (birlamchi endpoint = P(VR) trendi ⇒ `complete`;
survival analizi ⇒ `complete` + `censored`, §6.2), lekin
`schedule.enters_primary_analysis()` (`revix/schedule.py:746`) nomi bilan
boshqa narsani aytadi. **Eksklyuziya darajasi natija sifatida beriladi**
(§12), shuning uchun bu nom chalkashligi hisobot raqamiga tegishi mumkin —
qayd etildi, tuzatilmadi.

### 8.2 Trial boshi/oxiridagi probe uzilishlari — `reduce.py` vs validator

| manba | xatti-harakat | dalil |
|---|---|---|
| `reduce.probe_gaps()` | **faqat ketma-ket ikki probe orasini** ko'radi (`zip(probes, probes[1:])`), demak trial **boshidagi** va **oxiridagi** uzilishni **o'tkazib yuboradi** | `revix/reduce.py:1455`, `:1459` |
| `validate.check_probe_coverage()` | ularni **rad etadi** — `leading` va `trailing` uzilishlar aniq nomlanadi | `revix/validate.py:2030`, `:2034` |

Ya'ni **bitta run** reducer uchun `complete`, gate uchun esa **rad etilgan**
bo'lishi mumkin.

**Qaysi o'qish pre-registration'ga mos:** `PREREGISTRATION.md` §4 aniq —
probe uzilishi `> 2×P` trial'ni `censored` qiladi, va
*"instrumentatsiya yo'qolishi hech qachon jimgina natijaga aylanmaydi"*.
Demak **validator'ning qattiqroq o'qishi** pre-registration'ga mos.
**Lekin metrikani hisoblaydigan narsa — `reduce.py`.**

**Mitigatsiya (orkestrator bergan, v1.2 qayd etadi):** driver per-trial
prober'ni **washout ichida** ishga tushiradi va uni **horizon'dan keyin**
to'xtatadi (§4.5(a)), demak trial chegaralarida probe **bo'lishi kerak** va
bu holat **amalda yuzaga kelmasligi** lozim.

> **MITIGATSIYA — YECHIM EMAS.** U holatni **kamaytiradi**, lekin
> `reduce.py` va validator o'rtasidagi ziddiyatni **yo'qotmaydi**: prober
> trial o'rtasida o'lsa yoki birinchi probe kechiksa, ikki modul baribir
> boshqa javob beradi. Haqiqiy tuzatish `reduce.probe_gaps()` ga tegadi —
> u commit qilingan va test bilan qoplangan — demak alohida o'zgarish va
> alohida asoslanish talab qiladi. Shu holatda **validator ustun**: §14.6
> bo'yicha validatsiyadan o'tmagan run **analiz qilinmaydi**, demak gate
> qattiqroq bo'lsa natija chiqmaydi — bu xavfsiz tomon (fail-closed).

---

## 9. Aloqador hujjatlar

| Hujjat | Mazmuni |
|---|---|
| [`PREREGISTRATION.md`](../../PREREGISTRATION.md) | muzlatilgan ta'riflar (`preregistration/v1.4`); §1 vaqt disiplinasi va `boot_id`, §4 VR, §5 FR, §6 downtime/latency/loop, §8.2 probe narxi, §10.2 ECDF va BCa CI, §12 disposition, §14 data schema, §14.6 validator invariantlari, §15 muhit fingerprint'i |
| [`CONTRIBUTING.md`](../../CONTRIBUTING.md) | §1.1 amendment protsedurasi, §1.2 guard tasdiqlanmasa, §1.4 append-only, §3 nomuvofiqlik topilsa, §4 `None` ≠ `0` |
| [`DEVELOPMENT.md`](../../DEVELOPMENT.md) | §5 commit uslubi, §7 muzlatilgan hujjatlar tartibi |
| [`INSTALLATION.md`](../../INSTALLATION.md) | bog'liqliklar ro'yxati (§6 dagi bo'shliq), systemd ≥ 254 sharti (§7.1) |
| [`00-pilot-topologiya.md`](00-pilot-topologiya.md) | §3.1 mitigation (b) — guard majburiy, birinchi start/oxirgi stop (§1.3-1, §1.3-2); §6 qurilish tartibi — guard birinchi (§7.3) |
| [`01-muhit-tekshiruvlari.md`](01-muhit-tekshiruvlari.md) | §4 — `systemctl show` o'chgan unit uchun default qaytaradi (§1.1, §7.2) |
| [`02-guard-kalibratsiyasi.md`](02-guard-kalibratsiyasi.md) | §7 masala 1 — chegaralar **band desktop'da** qayta o'lchanishi kerak (§7.3) |
| [`03-sut-protokoli.md`](03-sut-protokoli.md) | muzlatilgan wire protokol (`sut-protocol/v1`), `probe_sample` qiymatlarining manbai |
| [`ARCHITECTURE.md`](../../ARCHITECTURE.md) | §6 ochiq nomuvofiqliklar ro'yxati |
