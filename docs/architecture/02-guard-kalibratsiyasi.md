# 02 — Guard kalibratsiyasi va pressure mexanizmi

Bu hujjatdagi har bir raqam **haqiqatan o'lchangan**. Hech bir chegara taxmin
bilan qo'yilmagan.

**Sana:** 2026-09-29 | **Mashina:** Kali 2026.3, kernel 7.1.5, systemd 261, 15Gi RAM, 12 CPU
**Topologiya:** `revixlab.slice` (MemoryMax=1G, MemoryHigh=192M, MemorySwapMax=0,
TasksMax=64, CPUQuota=200%), `revixmon.slice` (harness, sibling)
**Skript:** [`scripts/guard-test.sh`](../../scripts/guard-test.sh)

---

## 1. 🔴 Eng muhim topilma: `user@` PSI ≈ `lab` PSI

Bo'sh desktop'da ota scope child scope'ni **deyarli aynan** aks ettiradi.
O'lchangan (2 s oynali `full` stall tezligi):

| t (s) | `user@1000.service` | `revixlab.slice` |
|---|---|---|
| 4.4 | 0.268 | 0.271 |
| 5.2 | 0.597 | 0.613 |
| 6.0 | 0.882 | 0.898 |
| 7.6 | 0.968 | 0.970 |
| 9.2 | 0.925 | 0.925 |
| cho'qqi | **0.980** | **0.984** |

**Sabab:** PSI `full` faqat **non-idle** task'larni hisoblaydi. Claude/Chrome
idle bo'lganda yagona non-idle task — generator. Shuning uchun `some == full`
va ota `≈` child. (Band desktop'da `full` ancha past bo'lardi — bu topilma
**bo'sh desktop sharti**ga bog'liq va band tizimda qayta o'lchanishi kerak.)

### Natijasi guard dizayni uchun — dizayn o'zgardi

Pilotning P2 bandi (60–80% *slice* stall) `user@` ni ham 60–80% ga ko'taradi.
Demak **oniy chegarada trip qiluvchi guard har bir P2 trial'ini o'ldirardi** va
eksperimentni imkonsiz qilardi.

Guard qayta loyihalandi: asosiy himoya oniy chegara **emas**, balki oomd ning
o'z kriteriyasini aks ettiruvchi **davomiylik**:

| | chegara | davomiylik |
|---|---|---|
| **oomd** | `avg10 ≥ 50%` | 20 s |
| **guard** | `2s tezlik ≥ 35%` | **15 s** |

Zaxira katta, chunki soatlar boshqacha yuradi: oomd ning hisoblagichi `avg10`
50% dan oshgandan **keyin** boshlanadi, `avg10` esa haqiqiy tezlikka yetishi
uchun ~10 s kerak. 0.6 tezlikda qotgan generator uchun oomd ~28–30 s da
ishlardi; guard 15 s da to'xtatadi.

15 s tanlanishi: pilot hold ≤12 s + ramp ≤3 s = eng yomon holatda 15 s → to'g'ri
ishlayotgan trial hech qachon trip qilmaydi.

Oniy chegaralar **runaway tutuvchi** sifatida qoldi (to'liq qotish):
`user_full_avg10_max=85`, `user_some_avg10_max=90`, `user_full_rate2s_max=0.98`.

> `0.98` raqami o'lchovdan: qonuniy ramp burst'i **0.93–0.98** ga chiqadi.
> Boshlang'ich `0.90` qiymati qonuniy pressure'ni o'ldirar edi — va aynan
> shunday bo'ldi (Run B, calib v2/v3).

---

## 2. Tuzatilgan xato: tezlik oynasi suzib ketishi

Boshlang'ich kod `≥2 s` bo'lgan **eng eski** namunani tanlardi, demak oyna
2–8 s orasida suzardi. O'lchovda `window_us = 4900157` (4.9 s) bo'lib ko'rindi.

Natijasi: tezlik silliqlanib, guard **sekinlashardi** — ya'ni aynan `avgN` dan
qochish maqsadi buzilardi.

**Tuzatildi:** eng **tor** `≥2 s` oyna tanlanadi (eng yangidan eskiga qarab).
Tasdiq: keyingi ishga tushirishlarda `window_us = 2000009` va `2000000`.

Xuddi shu xato `pressure.py` ning PI controller'ida ham bor edi va tuzatildi.
Regressiya unit test bilan qulflandi (`test_tezlik_oynasi_eng_tor_2s_ni_tanlaydi`).

---

## 3. Pressure mexanizmi: anonim + `swap=0` **binar**, o'rta band yo'q

O'lchangan: `memory.high` dan oshish **~0.98 stall** beradi. `MemorySwapMax=0`
va to'liq anonim xotira bilan reclaim **hech narsa bo'shata olmaydi**, demak
throttling deyarli to'liq.

```
memory.high dan past   -> stall ~= 0.000
memory.high dan yuqori -> stall ~= 0.93 .. 0.98
o'rta band             -> YO'Q
```

`memory.events`: `high: 419 -> 923` (throttling), `oom_kill: 0`, `max: 0` —
ya'ni throttling ishladi, OOM bo'lmadi. Bu fault class 4 uchun shart
(`host_mem_pressure` kill'siz bo'lishi kerak, aks holda fault class 3 ga
aylanib qoladi).

### Yechim: impuls + duty cycle

**Churn tartibi hal qiluvchi:**

| tartib | natija |
|---|---|
| bo'shat → ajrat | `current` `memory.high` dan **hech qachon oshmaydi** → pressure **YO'Q** |
| **ajrat → bo'shat** | har churn high dan blok hajmicha **vaqtincha oshadi** → boshqariladigan impuls |

Ya'ni: **blok hajmi** = bitta impulsning stall kattaligi; **churn soni** =
tik'dagi duty cycle. Ikkisi 2 s oynadagi o'rtacha stall ulushini boshqaradi.

Bu regressiya unit test bilan qulflandi (`test_churn_avval_ajratadi_keyin_boshatadi`).

**Baza `memory.high` dan bir oz PAST bo'lishi kerak** (avtomatik:
`high - 2*blok`). Shunda ramp **bepul** bo'ladi va pressure faqat churn
impulslaridan keladi. O'lchangan: `baza=184MB` (high=192MB), ramp tezligi
median **0.000**, max **0.000**.

> Boshlang'ich `baza=256MB` (high dan yuqori) ramp'ning o'zini ~0.66–0.98 stall
> qilardi va guard runaway'ni urardi — control tsikliga hech qachon yetmasdi.

---

## 4. PI controller — nishonni ushlaydi

| nishon | erishilgan median | xato | churn/tik median | toza tugadi | guard trip |
|---|---|---|---|---|---|
| **0.30** | **0.311** | **+0.011** | 0.0 (max 4) | ✅ ha | yo'q ✅ |
| 0.60 | 0.558 | −0.042 | — | (sustain testi) | sustain ✅ |

`touched` butun davomida **184 MB da barqaror** — churn o'sishsiz, ya'ni
`MemoryMax` ga yetib OOM bo'lmaydi.

**Boshqarish qo'pol:** tezlik 0.246–0.411 orasida tebranadi. Bu qabul qilinadi,
chunki `PREREGISTRATION.md` §9.4 analizda **erishilgan (uzluksiz)** tezlikni
ishlatishni belgilaydi, mo'ljallangan darajani emas. Treatment silliq emas,
**bursty** — va bu har namunada log'lanadi.

---

## 5. Guard uchdan-uchiga tasdiqlandi

| test | shart | natija |
|---|---|---|
| Run A | boshlang'ich chegaralar | trip `user_full_rate2s` rate=0.250, `kill_ok: True`, unit `inactive` |
| Run B | runaway chegarasi 0.90 | trip rate=0.931, oyna **aynan 2.000000 s** ✅ |
| calib v4 | mo'ljallangan pressure (0.30, 12 s) | **trip YO'Q** ✅ — eksperiment mumkin |
| **Run D** | `sustain_max=5 s`, nishon 0.60 | trip `sustained_pressure`, `sustained_s=5.1` vs `limit_s=5.0`, `kill_ok: True` ✅ |

`cgroup.kill` har holatda ishladi: `SIGKILL` (status=9/KILL), `oom_kill: 0` —
ya'ni guard o'ldirdi, OOM emas.

---

## 6. Kollateral zarar: YO'Q

Barcha ishga tushirishlar bo'yicha:

```
Claude renderer PID'lar (76391, 76578, 172844, 174048)  -> hammasi TIRIK
Chrome renderer PID'lar (71038, 71102, 71176)           -> hammasi TIRIK
systemd-oomd journal xabarlari                          -> HECH QANDAY
/proc/vmstat oom_kill                                   -> 0 (o'zgarmadi)
revixlab.slice memory.events oom_kill                   -> 0
memory.swap.current                                     -> 0 (swap ishlatilmadi)
```

Tozalash qoldiq qoldirmadi: 0 unit, 0 cgroup, `~/.config/systemd/user/` da
**0 doimiy drop-in** (`set-property --runtime` ishlatilgani uchun).

---

## 7. Ochiq masalalar va cheklovlar

| # | masala | holat |
|---|---|---|
| 1 | `user@ ≈ lab` topilmasi **bo'sh desktop** sharti uchun. Band tizimda `full` ancha past bo'ladi va guard sezgirligi o'zgaradi | **qayta o'lchanishi kerak** band desktop'da |
| 2 | PI boshqarishi qo'pol (±0.08). Nozikroq blok (1–2 MB) yaxshilashi mumkin | sinalmagan |
| 3 | Guard'ning o'zini oomd'dan himoya qilish mumkin emas (`oom_score_adj` pasaytirish privilegiya talab qiladi). Guard kichik xotira izi bilan ishlaydi, lekin bu **kafolat emas** | to'liq yechim: system slice (sudo) |
| 4 | Sustained pressure >15 s va `W_stab`=60 s hali ham **imkonsiz** privilegiyasiz | VM yoki system slice kerak |
| 5 | `io.pressure` o'qiladi, lekin IO **injection** qilinmaydi (`io` delegated emas) | guest'ga tegishli |
| 6 | Host `/proc/pressure` javobi zaif (15 GiB host'da 1 GiB slice) | VM kerak — `PREREGISTRATION.md` §9.6 da allaqachon yozilgan |

## 8. Pre-registration'ga ta'siri

**Hech bir ta'rif, endpoint, metrika yoki statistik test o'zgarmadi.**

Tasdiqlangan: §9.4 ning "analiz erishilgan uzluksiz pressure'dan foydalanadi"
qarori **to'g'ri va zarur** — chunki treatment bursty va qo'pol, mo'ljallangan
daraja haqiqiy dozani aks ettirmaydi.

Tasdiqlangan: P1/P2 bandlari **erishiladigan** (0.30 → 0.311 ko'rsatildi),
demak §9.3 ning uch darajali dizayni amalga oshirilishi mumkin.
