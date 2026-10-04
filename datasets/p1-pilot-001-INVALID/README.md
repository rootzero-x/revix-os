# `p1-pilot-001` — YAROQSIZ run (saqlangan, tahlil QILINMAYDI)

> **Bu run tahlil qilinmaydi, `p1-pilot-002` bilan aralashtirilmaydi va tanlab keltirilmaydi** (`preregistration/v1.13`, v1.14).

**Nega yaroqsiz.** 120/120 trialga yetdi va post-flight toza edi, lekin `revix.validate` **O'TMADI** (4 xato, 3 trial) va §14.6 bo'yicha
bunday run analiz qilinmaydi. Sabab — uchta **driver implementatsiya nuqsoni** (validator va frozen ta'riflar to'g'ri edi):

1. `schedule.TrialFacts` da "oyna hold ichidami" fakti yo'q edi → kech oyna `censored` bo'lmadi (`b007t001`, `b013t004`);
2. `probe_gap_exceeded` §4 ta'rifidan emas, "prober tirikmi" dan olinardi (`b007t001`);
3. `t_issue` eskirgan `ActiveExitTimestamp` dan olinardi → ikki action bir xil vaqt oldi (`b010t001`).

Tahlil: `docs/architecture/15-pilot-001-validatsiya-xatolari.md`, tuzatishlar: `16`.

| fayl | hukm |
|---|---|
| `meta/validate.txt` | ASL: `NATIJA: O'TMADI`, 4 xato |
| `meta/validate-v114-CORRECTED-on-pilot001.txt` | **tuzatilgan** (v1.14) validator: **O'TMADI**, xuddi shu 4 xato — tuzatish bu run'ni **qutqarmaydi** |

Ma'lumot **o'chirilmaydi**: yaroqsiz run tarixi tadqiqotning bir qismi. Tarkib `p1-pilot-002/` bilan bir xil (`raw/`, `meta/`).
