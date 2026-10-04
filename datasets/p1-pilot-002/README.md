# `p1-pilot-002` — yagona tahlil qilinadigan pilot run

**Holat:** tuzatilgan (`preregistration/v1.14`) validatsiya darvozasi ostida **yaroqli**; asl darvoza ostida **yaroqsiz** edi.
**Ikkala hukm saqlangan** va bir-biridan ajratilmaydi:

| fayl | hukm |
|---|---|
| `meta/validate.txt` | **ASL**: `NATIJA: O'TMADI` (1 xato: `b010t005`, `aborted_guard` + probe uzilishi) |
| `meta/validate-v114-CORRECTED.txt` | tuzatilgan validator: `NATIJA: O'TDI` (0 xato, 24 ogohlantirish) |

Pilot **tadqiqotchi** (exploratory). Frozen §20.3 bo'yicha **gate qilingan**: birlamchi endpoint hisoblangan, lekin talqin qilinmaydi.
To'liq natijalar: `docs/experiments/01-p1-pilot-natijalari.md`.

## Tarkib

| katalog | mazmuni |
|---|---|
| `raw/` | xom oqimlar `*.zst` (`events.jsonl`, `probe.csv`, `psi.csv`, `guard.jsonl`, `pressure.jsonl`), `run_meta.json`, `guard.trip`; `RAW.SHA256SUMS` — **siqilmagan** xom fayllarning yaxlitlik yig'indisi |
| `meta/` | `launcher.log`, `marker-pre/post.json`, `clock-watch.log`, ikkala `validate` hukmi, post-flight qoldiq tekshiruvi |
| `derived/` | `analysis.json`, `reduce-summary.json`, `trials/episodes/sweep` (`*.zst`), `figures/` (6 SVG + raqam sidecar'i JSON) |

## Qoidalar

- **Append-only.** Bu katalog qayta yozilmaydi. Yangi tahlil — yangi `derived-<sana>/` katalogi.
- **Faqat bu run tahlil qilinadi.** `p1-pilot-001` yaroqsiz va `-002` bilan hech qachon aralashtirilmaydi yoki tanlab keltirilmaydi.
- **Smoke va kalibratsiya** ma'lumoti (`datasets/smoke-*`, `datasets/open-params-*`) bu run'ga **kirmaydi**.
- Tekshirish: `zstd -dc raw/events.jsonl.zst | sha256sum` ni `raw/RAW.SHA256SUMS` dagi `events.jsonl` bilan solishtiring.
- `derived/` **SUT-only ko'rinish** orqali hosil qilingan (`scripts/pilot/pilot-reduce.py`); filtrsiz reduksiya bystander probe'larini aralashtiradi.
