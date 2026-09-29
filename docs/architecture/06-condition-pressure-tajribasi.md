# 06 — `ConditionMemoryPressure=` tajribasi

**Sana:** 2026-09-29 | **Mashina:** systemd 261 (261.2-1), Kali 2026.3

> Bu hujjat loyihaning **asosiy manfiy da'vosini rad etadi va uni aniqroq
> shaklda tiklaydi**. Har bir natija shu mashinada haqiqatan ishga tushirilgan.

---

## 1. Nima topildi

Adabiyot verifikatsiyasi loyihaning markaziy da'vosini buzdi:

> ~~"PSI hech qayerda recovery qaroriga kirish signali sifatida ishlatilmagan"~~

**Bu YOLG'ON.** `man systemd.unit` (shu mashinada tekshirildi):

```
ConditionMemoryPressure=, ConditionCPUPressure=, ConditionIOPressure=
    Verify that the overall system (memory, CPU or IO) pressure is below
    or equal to a threshold. ... the pressure will be measured as an average
    over the last five minutes before the attempt to start the unit is
    performed. ... "10%/1min" ... The "full" PSI will be checked first, and
    if not found "some" will be checked.
    Optionally, the threshold value can be prefixed with the slice unit
    under which the pressure will be checked, followed by a ":".

    Added in version 250.
```

Ya'ni **PSI-gated start admission control systemd'da 2021 yildan (v250) beri
mavjud** — slice scope bilan, kerakli oyna bilan, `full` keyin `some` tartibi
bilan. Bu REVIX taklif qilgan gate'ning deyarli aynan shakli.

---

## 2. Hal qiluvchi savol

Adabiyot agenti muhim ogohlantirish qoldirdi: `Restart=` yo'lida shart
**qayta baholanadimi?** U buni man sahifasidagi "queued start job" iborasidan
**xulosa qilgan**, lekin **sinamagan**.

Bu farq hal qiluvchi:

| Agar shart restart'da qayta baholansa | Agar baholanmasa |
|---|---|
| `ConditionMemoryPressure=` = **restart admission control** | faqat **birinchi start** uchun gate |
| REVIX ning H2 si qoplangan | H2 ochiq qoladi |

---

## 3. Tajriba

**Usul:** `ConditionPathExists=` proksi sifatida ishlatildi. Sabab:
systemd barcha `Condition*=` larni bitta kod yo'lida baholaydi, va
`ConditionPathExists` ni **deterministik** boshqarish mumkin, memory
pressure'ni esa yo'q (pressure'ni "har doim rad etadigan" chegara mavjud emas,
chunki shart `pressure ≤ threshold`).

```
unit:  Restart=on-failure, RestartSec=1s, StartLimitBurst=0
       ConditionPathExists=/tmp/revix-cond-flag
exec:  log yozadi, 0.3s uxlaydi, exit 1
```

**Ketma-ketlik:** bayroq bor → 3.5 s kutish → bayroqni o'chirish → 4 s kutish.

### Natija

```
Bayroq BOR (3.5 s):     ishga tushishlar = 3,  NRestarts = 2,  ConditionResult = yes
Bayroq O'CHIRILDI (4s): ishga tushishlar = 6,  NRestarts = 5,  ConditionResult = yes
                        ^^^ bayroq yo'q bo'lsa ham YANA 3 marta ishga tushdi

journal:
  Scheduled restart job, restart counter is at 1..5
  (hech qanday "Condition ... not met" xabari yo'q)
```

### Tasdiqlovchi teskari testlar

| test | natija |
|---|---|
| A: `ConditionPathExists=` yo'q faylga, **birinchi** start | `ConditionResult=no`, `ActiveState=inactive` → shart **birinchi start'ni GATE QILADI** ✅ |
| B: `ConditionMemoryPressure=90%` | qabul qilindi, `ConditionResult=yes`, unit ishga tushdi → **haqiqatan baholanadi** ✅ |
| C: `ConditionMemoryPressure=revixcond.slice:50%/1min` | qabul qilindi, baholandi → **slice-scoped shakl ishlaydi** ✅ |

---

## 4. Xulosa

```
ConditionMemoryPressure=  =  PSI-gated START admission control      ✅ shipped
                          ≠  PSI-gated RESTART admission control    ❌ yo'q
```

Avtomatik `Restart=` yo'li shartni qayta baholamaydi. Xizmat pressure
chegarasidan oshgan holatda ham cheksiz restart bo'laveradi.

**Adabiyot agentining xulosasi noto'g'ri edi** — u buni tekshirilmagan deb
ochiq belgilagan va sinashni tavsiya qilgan; sinov uni rad etdi. Bu aynan
agent hisobotlarini tekshirmasdan qabul qilmaslik sababi.

---

## 5. Loyihaga ta'siri

### Rad etilgan (hujjatlardan olib tashlandi)
- ~~"PSI hech qayerda recovery qaroriga kirish sifatida ishlatilmagan"~~
- ~~"systemd pressure'ni eksport qiladi, qaror qilmaydi"~~ — u qaror qiladi,
  lekin faqat birinchi start uchun

### Tiklangan, aniqroq shaklda
**H2 ochiq qoladi:** PSI-gated **restart** admission control systemd'da yo'q.
Va endi bu **taqqoslanadigan** da'vo — chunki yaqin qarindoshi shipped.

### Yangi imkoniyat: Baseline D
`ConditionMemoryPressure=` ni **baseline arm** sifatida qo'shish mumkin:

| arm | xatti-harakat |
|---|---|
| **D** | `ConditionMemoryPressure=X%` — pressure yuqori bo'lsa start **SKIP** qilinadi |
| **C** (REVIX) | pressure yuqori bo'lsa restart **KECHIKTIRILADI va qayta uriniladi** |

Farq real va sinaladigan: skip qilingan start **failure emas**, demak keyingi
restart rejalashtirilmaydi va **xizmat down qoladi**. Defer esa qayta uriniladi.

> **Lekin D arm P1 ga QO'SHILMAYDI.** P1 ning savoli dunyo haqida (pressure
> restart muvaffaqiyatiga ta'sir qiladimi), mexanizmlarni taqqoslash haqida
> emas. D arm — H2 savoli, demak **confirmatory eksperimentga (P2)** tegishli,
> va u o'z pre-registration'ini talab qiladi.

### Yangi mikro-natija
"systemd PSI start gating'ni beradi, restart gating'ni bermaydi" — bu o'z-o'zicha
qayd etishga arziydigan topilma, va u H2 ni motivatsiya qiladi.

---

## 6. Cheklov

Tajriba `ConditionPathExists` proksisidan foydalandi, `ConditionMemoryPressure`
dan emas. Asos: systemd barcha `Condition*=` larni bir xil mexanizm bilan
baholaydi. Bu **oqilona, lekin bilvosita**. To'g'ridan-to'g'ri tasdiq uchun
pressure'ni chegaradan oshirib ushlab turish kerak — bu guard ostida va
≤12 s oynada bajariladi, ya'ni **pilot harness'ining ishi**.

Shu sababli bu tekshiruv pilotning birinchi tasdiqlovchi qadamiga kiritiladi.
