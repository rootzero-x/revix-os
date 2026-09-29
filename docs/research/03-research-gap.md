# 03 — Research Gap

## Metod
`01-texnologiya-auditi.md` mavjud mexanizmlarni sanadi, `02-related-work.md` adabiyotni.
Bu hujjat ikkisini kesib, **nima qoplangan va nima qolgan**ini aytadi.

Qoida: agar funksiya allaqachon mavjud bo'lsa — u **baseline**, hissa emas.

---

## 1. Qoplangan — novelty da'vosidan OLIB TASHLANADI

| # | Mexanizm | Kim allaqachon qilgan |
|---|---|---|
| 1 | **Exponential backoff** | systemd v254 `RestartSteps=` + `RestartMaxDelaySec=` — ✅ bu mashinada tasdiqlangan |
| 2 | Kechiktirilgan restart | `RestartSec=` |
| 3 | Takroriy failure'da eskalatsiya | `StartLimitBurst=`+`StartLimitAction=`; Pacemaker `migration-threshold`; monit restart-cycles; k8s CrashLoopBackOff |
| 4 | Failure-turi → action xaritalash | Pacemaker per-operation `on-fail`; `Restart=on-abnormal\|on-abort\|on-watchdog`; Masakari |
| 5 | Dependency-first recovery | `Requires=`/`Requisite=`/`BindsTo=`/`PartOf=`/`After=`; `s6-rc`; Pacemaker ordering/colocation |
| 6 | Resurs mitigatsiyasi | cgroup v2 shift'lar; systemd-oomd; fb oomd + Senpai; kubelet node-pressure eviction |
| 7 | Health-gated config/versiya rollback | greenboot; systemd Automatic Boot Assessment; rpm-ostree; snapd; ChromeOS/Android A/B |
| 8 | Izolyatsiya | `OnFailureJobMode=isolate`; Pacemaker `standby`/`fence`; k8s cordon |
| 9 | Post-recovery health verification | k8s probe'lar; Pacemaker OCF `monitor`; monit content testlari; greenboot. **Faqat systemd'da yo'q** |
| 10 | **Adaptiv, ko'p-signalli action tanlash** | **Narya (OSDI '20)**; Sanabria va boshq. (SEAMS '24) |
| 11 | systemd+psutil+`VERIFYING` prototipi | `adaptive-self-healing-runtime` (GitHub, peer-reviewed emas) |

→ **REVIX ning boshlang'ich "Adaptive Recovery Decision Engine" novelty da'vosi
qoplanган.** Buni tan olmaslik — maqolani reviewer qo'lida yo'q qilish.

---

## 2. Haqiqatan qoplanmagan

### G1 — PSI recovery qaroriga kirish signali sifatida
Hech bir tizim — systemd, Pacemaker, Kubernetes, monit, oomd — **pressure'ni restart
qilish/qilmaslik qarorining kiritmasi** sifatida ishlatmaydi.

- systemd pressure'ni unit'ga **eksport qiladi** (`MemoryPressureWatch=`), qaror qilmaydi
- systemd-oomd pressure'ni **o'qiydi**, lekin yagona action'i `SIGKILL`
- Kubernetes PSI'ni **metrika** sifatida eksport qiladi
- Adabiyotda PSI-asosli recovery qarori haqida peer-reviewed ish **topilmadi** (preliminary)

**Bu REVIX ning H1/H2 turgan joyi.**

### G2 — Signal fusion bitta node'da action tanlash uchun
Hech bir single-node Linux service manager PSI + cgroup metrikalari + restart tarixi +
dependency holati + config-change provenance'ni **bitta action qaroriga** birlashtirmaydi.

Har bir signal alohida mavjud; bitta host uchun fusion hech qayerda yo'q.

⚠️ **Lekin:** Narya buni fleet darajasida qilgan, va `adaptive-self-healing-runtime`
buni prototip darajasida qilgan. Demak G2 **yolg'iz o'zi yetarli hissa emas** —
reviewer "integration engineering" deb aytadi va haq bo'ladi.

### G3 — "False recovery" metrikasi va recovery benchmark
Linux service manager'lar uchun:
- **restart noto'g'ri action bo'lganini o'lchaydigan metrika yo'q**
- reproducible recovery benchmark yo'q

ROC (Patterson va boshq., 2002) aynan recovery benchmark'larni talab qilgan.
**24 yil o'tib, bu qatlamda hali yo'q.**

**Bu eng himoya qilinadigan hissa** — chunki u tizim emas, o'lchov, va o'lchov
"integration engineering" tanqidiga tushmaydi.

### G4 — Service-granular config-change provenance rollback
greenboot / rpm-ostree / snapd / ChromeOS A-B **butun image yoki deployment**ni rollback
qiladi. Hech narsa *"unit X `/etc/X.conf` o'zgarishidan 40 s keyin ishdan chiqdi"* ni
**shu unit uchun** targeted revert bilan bog'lamaydi.

**Eng toza whitespace, lekin implementatsiya qiymati yuqori** → REVIX v1 qamrovidan
tashqarida qoldirildi (kelajak ishi).

---

## 3. Tanlangan yo'nalish va nega

Loyiha egasi **G1 + G3** ni tanladi.

| Variant | Kuchi | Zaifligi | Qaror |
|---|---|---|---|
| G1+G3 — PSI-gated + benchmark | falsifiable, o'lchanadigan, `RestartSteps=` ni **baseline** ga aylantiradi (hissa emas), metrika hissasi tizim tanqidiga tushmaydi | tor | ✅ **tanlandi** |
| G4 — config provenance | eng toza bo'shliq | implementatsiya qiyin, verification murakkab | keyinga |
| G2 — keng adaptive engine | ko'p komponent | Narya'ni yengish qiyin, "integration engineering" riski yuqori | ❌ |

### Nima uchun bu yo'nalish ishlaydi
`RestartSteps=` mavjudligi — **muammo emas, imkoniyat**: u REVIX ni kuchli baseline'ga
qarshi o'lchashga majbur qiladi. Zaif baseline'ga qarshi g'alaba qiymatsiz; kuchli
baseline'ga qarshi **halol natija** — hatto "backoff foydaning ko'pini oladi" bo'lsa ham —
nashr qilinadigan o'lchov.

---

## 4. Halol zaifliklar

Bu bo'lim maqolaning Limitations bo'limiga aynan ko'chadi.

### H2 H1 dan ancha qiyin
1. Pressure muhim bo'lgan fault class'larda **"defer" ≈ B ning backoff'i tasodifan
   erishayotgan narsa.** Halol natija: *"native `RestartSteps` mavjud foydaning ko'pini
   allaqachon oladi."* Bunga tayyor bo'lish kerak.
2. **Restart'ni kechiktirish ta'rifan downtime'ni oshiradi** — agar kechiktirilgan restart
   muvaffaqiyatsiz bo'lmaganida. Demak C faqat tor rejimda ustun: **pressure B ning
   backoff'idan qisqa, A ning restart interval'idan uzoq** vaqt shkalasida o'tkinchi bo'lishi kerak.

→ **`pressure_pulse_duration` faktorial dizaynga HOZIR qo'shiladi**, keyin aralash
natijaning post-hoc izohi bo'lib qolmasligi uchun. Reviewer farqni sezadi.

### Manfiy da'vo tasdiqlanmagan
"PSI recovery qarorida ishlatilmagan" — **preliminary**. Tizimli adabiyot qidiruvi
bajarilmaguncha "birinchi marta" deb yozilmaydi. `02-related-work.md` oxiridagi ogohlikni ko'ring.

### SUT sintetik
Confirmatory eksperiment bitta haqiqiy xizmat (nginx yoki postgresql, guest'da) bilan
takrorlanishi **shart**, aks holda maqola to'g'ri ravishda "faqat o'yinchoq o'lchagan"
deb tanqid qilinadi.

### Sirkulyarlik — eng katta xato riski
PSI ni FR ta'rifiga qo'shish tavtologiya yaratadi.
Muzlatilgan kafolatlar: [`PREREGISTRATION.md`](../../PREREGISTRATION.md) §5.

---

## 5. Bepul, engine'ga bog'liq bo'lmagan oldindan aytish

**Fiksa `TimeoutStartSec` o'zgaruvchan pressure ostida yashirin failure amplifikatori.**

Mexanizm: pressure start'ni sekinlashtiradi; `TimeoutStartSec` fiksa; demak pressure
sog'lom xizmatni start-timeout failure'iga **aylantiradi**.

Agar bu chiqsa — H1 mexanizmini **REVIX mavjudligiga bog'liq bo'lmagan holda**
qo'llab-quvvatlaydi, va bu o'z-o'zicha toza natija. Shuning uchun oldindan e'lon qilinadi
(hech narsa turmaydi).
