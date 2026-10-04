# Pilot skriptlari (orkestrator)

`p1-pilot-001` va `p1-pilot-002` shu skriptlar bilan o'tkazilgan. Ular **tadqiqot ma'lumotini
hosil qilmaydi**, faqat run'ni ishga tushiradi, kuzatadi va xom ma'lumotni reduksiya uchun
tayyorlaydi.

| fayl | vazifasi |
|---|---|
| `pilot-run.sh <HEAD>` | pre-flight (qulf, host'da VirtualBox yo'qligi, yuk, git HEAD, toza daraxt, qoldiq unit yo'q, **jadval hash'i**), keyin `revix run`, post-flight va `validate`. `pilot-001` da run papkasi `p1-pilot-001`, `pilot-002` da `p1-pilot-002`. |
| `pilot-watch.sh`, `pilot-status.py` | faqat o'qiydi: trial soni, yacheyka bo'yicha disposition, guard hodisalari, `real − mono` soat farqi. |
| `pilot-reduce.py <run> <out>` | **SUT-only ko'rinish** (`validate.reducer_view`) → `revix.reduce`. |

## `pilot-reduce.py` haqida (muhim)

Xom `probe.csv` ikkala target'ni (`sut`, `bystander`) saqlaydi; filtrlanmagan reduksiya bystander
probe'larini aralashtiradi. Shuning uchun reducerga SUT-only ko'rinish beriladi. Skriptning birinchi
versiyasi CSV'ni faqat `PROBE_FIELDS` bilan qayta yozib, `validate.load_run_dir` qo'shadigan
`progress` ustunini **jimgina tashlab yuborgan** va `R_ref` 120/120 trialda hisoblanmagan
(`docs/architecture/18-vr-implementatsiya-auditi.md` §2). Hozirgi versiya barcha kalitlarni yozadi.
`PYTHONPATH=<repo>` bilan ishga tushiriladi.
