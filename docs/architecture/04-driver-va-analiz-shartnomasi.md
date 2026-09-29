# 04 — Driver va analiz shartnomasi (MUZLATILGAN)

**Versiya:** `driver-contract/v1` | **Holat:** MUZLATILGAN

> **Nega bu birinchi yoziladi:** driver, analiz va figura modullari parallel
> ishlab chiqiladi. Shartnoma oldindan muzlatilmasa, ular bir-biriga mos
> kelmaydigan narsa yozadi. Bu `03-sut-protokoli.md` bilan bir xil usul.
>
> Implementatsiya bu faylni **o'zgartirmaydi**. Nomuvofiqlik topilsa — avval
> shu fayl amendment qilinadi.

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

### 1.2 Trial hodisalari ketma-ketligi (har trial uchun)

```
trial_begin      arm, fault_class, pressure_level, block_index,
                 position_in_block, planned_timeline
env_snapshot     (trial boshida)
baseline_window  R_ref o'lchangan oyna: mono_us_begin/end, throughput
fault_inject     mono_us_before_call, mono_us_after_call, fault_id, kind, params
fault_effective  t_fault_effective va uning manbasi (probe|oom_kill|...)
action           action_id, actor, action_class, t_issue/t_begin/t_exec,
                 policy_delay_us (L_dec dan ALOHIDA)
action_defer     action o'rniga kechiktirilganda
actor_signal     success (aktorning O'Z da'vosi) + actor_signal_source
unit_state       (units.UnitWatcher dan; recv_mono_us alohida)
cgroup_events    memory.events / memory.swap.events delta'lari
env_snapshot     (trial oxirida)
trial_end        disposition (§12 yopiq enum, AYNAN BITTA) + reason
```

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

---

## 3. Figura moduli

`revix/figures.py` **faqat `analysis.json` ni** o'qiydi — xom ma'lumotni emas.
Shunda figura analizdan uzoqlasha olmaydi.

Chiqish: `figures/<nom>.svg` (matplotlib), va har figura yonida
`figures/<nom>.json` — figurani hosil qilgan **aynan raqamlar**, shunda figura
tekshirilishi mumkin.

Majburiy figuralar (loyiha spetsifikatsiyasi §47 dan, P1 uchun tegishlilari):
`p_vr_vs_pressure` (dose-response + CI), `km_time_to_vr`, `downtime_ecdf`
(uchala o'lchov), `sensitivity_heatmap` (W_stab × θ), `exclusion_breakdown`,
`probe_cost`.

**Rang/uslub qoidasi:** figura oq-qora chop etishda ham o'qilishi kerak
(marker/chiziq turi bilan farqlanadi, faqat rang bilan emas).
