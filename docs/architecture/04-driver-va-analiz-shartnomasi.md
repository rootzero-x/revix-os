# 04 — Driver va analiz shartnomasi (MUZLATILGAN)

**Versiya:** `driver-contract/v1.1` | **Holat:** MUZLATILGAN

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
`run_mode` ni `validate.check_run_meta()` o'qiydi (`revix/validate.py:491`),
`t_trial_us` esa §5 dagi hisoblangan horizon. Ikkisi ham §4.3 jadvalida.

### 1.2 Trial hodisalari ketma-ketligi (har trial uchun)

```
trial_begin      arm, fault_class, pressure_band, position_in_block,
                 planned_timeline   (trial_id va block_index — ENVELOPE'da)
env_snapshot     (trial boshida)
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
| 1 | **Guard BIRINCHI start, OXIRGI stop** | qotib qolgan driver guard'ni o'chira olmasligi kerak |
| 2 | Guard ishga tushmasa — run **boshlanmaydi** | fail-closed |
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

---

## 2. Analiz moduli nima ishlab chiqaradi

`revix/analyze.py` **qat'iy offline**: `reduce.py` chiqishini + `stats.py` ni
oladi, pre-registration §10 dagi analizni bajaradi.

### 2.1 Kirish
`reduce.py` ning `trial_metrics` record'lari (JSONL) + `run_meta.json`.

### 2.2 Chiqish: `analysis.json` — qat'iy sxema

```jsonc
{
  "schema_version": 1,
  "analysis_version": "p1/v1",
  "preregistration_sha256": "...",     // kirish run_meta dan
  "generated_mono_us": 0,
  "n_trials": {"total": 0, "by_disposition": {}},
  "primary": {                          // §11 birlamchi endpoint
    "endpoint": "P(VR) trend across pressure levels",
    "test": "cochran_armitage_trend",
    "statistic": 0.0, "p_value": 0.0, "direction": "decreasing|increasing|none",
    "cells": [{"level": "P0", "k": 0, "n": 0, "p_hat": 0.0,
               "ci_lower": 0.0, "ci_upper": 0.0, "ci_method": "clopper_pearson"}],
    "risk_difference": {"estimate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0,
                        "ci_method": "newcombe"},
    "falsified": false,                 // §11 mezoni bo'yicha
    "falsification_rule": "trend p>0.05 AND newcombe_upper<0.15"
  },
  "survival": {                         // §10.2
    "km": {"by_arm": {"<arm>": {"times": [], "survival": [], "at_risk": [],
                                "greenwood_var": []}}},
    "logrank": {"chi2": 0.0, "p_value": 0.0, "observed": {}, "expected": {}},
    "rmst": {"tau": 0.0, "by_arm": {"<arm>": {"estimate": 0.0, "se": 0.0}},
             "difference": {"estimate": 0.0, "se": 0.0,
                            "ci_lower": 0.0, "ci_upper": 0.0}},
    "proportional_hazards_checked": false,   // tekshirilmasa HR BERILMAYDI
    "censoring": {"n_censored": 0, "recovered_within_horizon": "k/n"}
  },
  "false_recovery": {                   // §5
    "fr_a": {"per_action": 0.0, "per_episode": 0.0, "n_undetermined": 0},
    "fr_b": {"computed": false, "reason": "no calibration matrix (P1)"}
  },
  "downtime": {                         // §6.1 uchala o'lchov
    "d_sd": {}, "d_probe": {}, "d_eff": {}   // median, p90, p99 + BCa CI
  },
  "sensitivity": {                      // §4 sweep
    "w_stab": [8,10,30,60,120], "theta": [0.5,0.8,0.95],
    "grid": [{"w_stab": 8, "theta": 0.8, "p_vr_by_level": {}, "note": null}]
  },
  "multiplicity": {"method": "holm_bonferroni", "family": [], "adjusted": []},
  "exclusions": {"rate": 0.0, "by_reason": {}},   // NATIJA sifatida beriladi
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
| 3 | Har record uchun `stream = record_type` (ya'ni `Emitter` default'i) | `validate._stream_key()` oqimni `(emitter, record_type)` juftligi bilan taxmin qiladi (`revix/validate.py:302`); bitta emitter ikki `record_type` ni bitta oqimga yozsa **soxta `seq` bo'shligi** chiqadi (§14.6-3 buziladi) |
| 4 | `mono_us` envelope'dan keladi va **o'sha record'ning kuzatuv vaqti** bo'lishi kerak; kuzatuv vaqti boshqa bo'lsa `Emitter.record(..., mono=…)` bilan beriladi | `reduce.py` oyna a'zoligini `mono_us` bilan hisoblaydi (`revix/reduce.py:770`, `:882`) |

### 4.3 Normativ jadval

Ustunlar: **manba** (qiymat qaydan keladi) → **record maydoni** (xom
record'dagi AYNAN nom) → **consumer** (uni o'qiydigan kod, fayl:qator).

#### `run_meta`

| manba | record maydoni | consumer |
|---|---|---|
| `git status --porcelain` bo'sh emasligi | `git_dirty` | `validate.check_run_meta` (`validate.py:492`) |
| run rejimi (`pilot` \| `confirmatory`) | `run_mode` | `validate.check_run_meta` (`validate.py:491`; `mode` ga fallback qiladi) |
| `sha256sum PREREGISTRATION.md` | `preregistration_sha256` | `validate.check_run_meta` (`validate.py:510`), `analyze.py` |
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
| harness qarori, `schema.DISPOSITIONS` enum'idan | `disposition` | `reduce.derive_disposition` (`reduce.py:1418`), `validate.check_dispositions` (`validate.py:255`) |
| harness | `reason` | odam o'qishi uchun (`RAW_CONTRACT`) |
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
| `NRestarts` | `NRestarts` **va** `n_restarts` | `reduce.evaluate_vr` 4-band (`reduce.py:770`), `reduce.reduce_trial` loop_rate (`reduce.py:1523`), `validate._invocation_changed` (`validate.py:449`, `:453`) |
| `InvocationID` | `InvocationID` **va** `invocation_id` | `reduce.reduce_trial` (`reduce.py:1520`), `validate._invocation_changed` (`validate.py:442`) |
| `ActiveEnterTimestampMonotonic` | o'sha nom **va** `active_enter_ts_mono_us` | `reduce.compute_d_sd` (`reduce.py:1342`) |
| `ActiveExitTimestampMonotonic` | o'sha nom **va** `active_exit_ts_mono_us` | `reduce.compute_d_sd` (`reduce.py:1341`) |
| `Result` | `Result` **va** `result` | **hech kim** (§4.6); `RAW_CONTRACT` talab qiladi |
| `recv_mono_us` (`units.py:1098`) | `recv_mono_us` **saqlanadi**, va envelope `mono_us := recv_mono_us` | `reduce` oyna filtrlari (`reduce.py:770`, `:882`, `:1341`), `validate` (`validate.py:441`) |
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
| aktor | `action_id` | `reduce.split_trials` (`reduce.py:471`), `validate.check_actions` (`validate.py:406`) |
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
| 3 | `unit_state`: snake_case vs xom systemd nomlari | **HAQIQIY — lekin faqat 5 maydonda** | runtime'da o'qiladi: `active_state` (`reduce.py:886`), `n_restarts` (`reduce.py:770`, `:1523`, `validate.py:449`), `invocation_id` (`reduce.py:1520`, `validate.py:442`), `active_enter_ts_mono_us` / `active_exit_ts_mono_us` (`reduce.py:1341-1342`). `UnitWatcher` esa `ActiveState`, `NRestarts`, `InvocationID`, `ActiveEnterTimestampMonotonic`, `ActiveExitTimestampMonotonic` beradi (`units.py:1113`, `STATE_PROPS` = `units.py:122`). **`result`** gumon ro'yxatida bor, lekin **runtime'da o'qilmaydi** — u `RAW_CONTRACT` dagi hujjat qatori (§4.6). **Hal:** §4.3 — xom nom + snake_case, ikkisi ham |

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

**CHEKLOV (ochiq, tuzatilmadi):** `validate._stream_key()` izohi
*"`Emitter.envelope()` `stream` argumentini OLADI lekin record'ga YOZMAYDI"*
deydi (`validate.py:306`). Bu **eskirgan**: `schema.Emitter.envelope()`
`stream` ni yozadi (`schema.py:219`) va `ENVELOPE_FIELDS` uni sanaydi
(`schema.py:244`). Izoh `validate.py` egasiga tegishli; shu amendment unga
tegmaydi. Driver uchun amaliy natija — §4.2 qoida 3.

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
Tekshirildi: `T_trial` faqat §6.2 (357, 358, 365-qatorlar) va §6.4 (388,
389-qatorlar) da **ishlatiladi**, ta'riflanmaydi; §9.4 trial jadvalini
fazalar bilan beradi (`pre-flight → baseline 10 s → ramp 5 s → hold 12 s →
washout ≥20 s ≈ 52 s`), lekin recovery horizon'ini raqamlamaydi.

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
| `t_pressure_off` | 32.0 s |
| `w_stab_s` | 8.0 s |
| `P` | 0.1 s |
| **`T_trial`** | **40.1 s = 40 100 000 µs** |
| `total_s` (yuqori chegara) | 52.0 s |

### 5.3 NEGA aynan shu formula

| had | nega |
|---|---|
| `t_pressure_off` | VR oynasining **eng kech qonuniy boshlanishi**. §9.4 analiz **erishilgan** pressure'dan foydalanadi; pressure o'chgandan keyin kelgan `t_up` — treatment'dan tashqaridagi recovery, demak oyna boshlanishi uchun oxirgi ma'noli nuqta |
| `+ w_stab_s` | §4 oynaning **TO'LIQ** kuzatilishini talab qiladi. `evaluate_vr()` kesilgan oynada `vr=None`, `reason="window_truncated"` qaytaradi (`reduce.py:831`), va `None` hech qachon `False` ga aylantirilmaydi. Horizon qisqa bo'lsa — ma'lumot yetishmovchiligi **ommaviy** `vr=None` ga aylanadi va birlamchi endpoint hisoblanmaydi |
| `+ P` | `window_complete` sharti `last_probe_us >= win_end − window_slack_us`, va `window_slack_us == probe_period_us` (`reduce.py:158`, `:751`). §6.1 probe kvantlashini (±P) ochiq e'lon qilgan; bitta davr qo'shilmasa, oyna chegarasidagi probe tasodifan yetib kelmasligi mumkin |
| yuqori chegara `total_s` | `trial_end` rejalashtirilgan jadval ichida qolishi kerak, aks holda washout va keyingi trial bir-biriga kirib ketardi (§8.4 `T_w` poli) |
| pastki chegara `t_verify_end_earliest` | §4 ning eng yaxshi holatdagi oynasi horizon ichiga **sig'ishi shart**; sig'masa shartnoma o'z-o'ziga qarama-qarshi bo'lardi |

**Busiz nima buzilardi:** horizon jimgina `total_s` (52 s) yoki `t_pressure_off`
(32 s) qilib olinsa — birinchi holatda `loop_rate` maxraji `loop_detected`
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
| 5 | `trial_end` aynan `trial_begin.mono_us + T_trial` da emit qilinadi (yoki undan **oldin**, agar disposition `aborted_guard` / `harness_error` bo'lsa) | `reduce.Trial.end_us` (`reduce.py:406`) censoring nuqtasi sifatida shuni oladi |
| 6 | `analyze.py` `t_trial_us` ni `analysis.json` ga ko'chiradi (§2.3-9) | har jadval/figura qaysi horizon ostida censor qilinganini ko'rsatadi (§6.2 `recovered_within_horizon: k/n`) |

### 5.5 Qamrov: bu qaror SHU hujjatning qarori

`PREREGISTRATION.md` bu amendment bilan **tahrirlanmadi**. `T_trial`
pre-registration'ning bo'shlig'i va u yerda ham amendment qilinishi kerak —
bu **boshqa agentning** ishi (`CONTRIBUTING.md` §1.1 protsedurasi bo'yicha).
Shu bo'lim esa `driver-contract/v1.1` ning qarori: driver va analiz
modullari parallel yozilishi uchun raqam **hozir** kerak.

Agar `PREREGISTRATION.md` amendment'i boshqa ta'rif bersa — **u ustun**, va
bu bo'lim shunga moslashtiriladi (`CONTRIBUTING.md` §3: nomuvofiqlik jimgina
tuzatilmaydi).

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

---

## 7. Aloqador hujjatlar

| Hujjat | Mazmuni |
|---|---|
| [`PREREGISTRATION.md`](../../PREREGISTRATION.md) | muzlatilgan ta'riflar; §1 vaqt disiplinasi, §4 VR, §5 FR, §6 downtime/latency/loop, §12 disposition, §14 data schema |
| [`CONTRIBUTING.md`](../../CONTRIBUTING.md) | §1.1 amendment protsedurasi, §1.4 append-only, §3 nomuvofiqlik topilsa |
| [`DEVELOPMENT.md`](../../DEVELOPMENT.md) | §5 commit uslubi, §7 muzlatilgan hujjatlar tartibi |
| [`INSTALLATION.md`](../../INSTALLATION.md) | bog'liqliklar ro'yxati (§6 dagi bo'shliq) |
| [`03-sut-protokoli.md`](03-sut-protokoli.md) | muzlatilgan wire protokol (`sut-protocol/v1`), `probe_sample` qiymatlarining manbai |
| [`ARCHITECTURE.md`](../../ARCHITECTURE.md) | §6 ochiq nomuvofiqliklar ro'yxati |
