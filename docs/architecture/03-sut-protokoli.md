# 03 — SUT wire protokoli (MUZLATILGAN)

**Versiya:** `sut-protocol/v1`
**Holat:** MUZLATILGAN — `sut.c` va `prober.py` mustaqil yozilishi uchun.

> **Nega bu birinchi yoziladi:** SUT va prober parallel ishlab chiqiladi.
> Protokol oldindan muzlatilmasa, ikki komponent bir-biriga to'g'ri kelmaydi.
> Bu faylni **hech bir implementatsiya o'zgartirmaydi** — nomuvofiqlik topilsa,
> avval shu fayl yangilanadi va ikkala tomon moslashtiriladi.

---

## 1. Transport

| | |
|---|---|
| Socket turi | `AF_UNIX`, **`SOCK_SEQPACKET`** |
| Yo'l | `$REVIX_SUT_SOCKET` env, default `/run/user/<uid>/revix-sut.sock` |
| Rejim | `0600` |
| Kодировка | ASCII, satr oxiri **yo'q** (datagram chegarasi xabar chegarasi) |
| Maks xabar | 4096 bayt |

`SOCK_SEQPACKET` tanlangan: xabar chegaralarini saqlaydi (framing kerak emas)
va `SOCK_STREAM` dagi qisman o'qish muammosi yo'q.

**Har ulanish bitta so'rov-javob.** Prober har probe'da yangi ulanish ochadi —
shunda `T_conn` (accept vaqti) haqiqatan o'lchanadi (`PREREGISTRATION.md` §2a).

---

## 2. So'rovlar

```
PROBE
INFO
FAULT <kind> [key=value ...]
```

Buyruq nomi katta harfda. Argumentlar bo'sh joy bilan ajratiladi.

---

## 3. Javoblar

### Muvaffaqiyat
```
OK progress=<u64> pid=<i32> invocation=<hex32> rss_kb=<u64> mono_us=<u64>
```

| maydon | ma'nosi |
|---|---|
| `progress` | **monoton o'suvchi** ish hisoblagichi (pastga qarang) |
| `pid` | SUT jarayonining pid'i |
| `invocation` | `$INVOCATION_ID` (systemd bergan), yo'q bo'lsa `0` x32 |
| `rss_kb` | joriy RSS |
| `mono_us` | SUT ning `CLOCK_MONOTONIC` vaqti javob yozilishidan oldin |

> **`invocation` KRITIK:** prober javobdagi invocation'ni yozadi. Busiz probe
> *yangi* invocation'ga muvaffaqiyatli tegib, siz uni eskisiga yozib qo'yadigan
> race yopilmaydi (`PREREGISTRATION.md` §14, `probe_sample.invocation_id_seen`).

### Xato
```
ERR <reason>
```
`reason` — bo'sh joysiz qisqa token: `unknown_command`, `bad_args`,
`not_ready`, `internal`.

### `INFO`
```
OK proto=1 impl=<matn> progress=<u64> pid=<i32> invocation=<hex32> uptime_us=<u64>
```

---

## 4. Progress hisoblagichi — VR ta'rifining asosi

**Semantika (buzilmaydi):**

1. `u64`, **qat'iy monoton o'suvchi** xizmat sog'lom bo'lganda.
2. Har ish tsikli iteratsiyasida **aynan 1 ga** oshadi.
3. Bitta iteratsiya **deterministik doimiy ish** bajaradi (CPU-bound, IO yo'q,
   ajratish yo'q) — shunda `Δprogress/Δt` haqiqiy throughput o'lchovi bo'ladi.
4. Restart'da **0 dan boshlanadi** (yangi invocation).
5. Probe'ga javob berish progress'ni **oshirmaydi** — aks holda o'lchov o'zini
   o'lchagan bo'lardi.

**Nega muhim:** `PREREGISTRATION.md` §4.5 throughput bandi VR ni process-liveness
dan ajratadigan yagona narsa. Progress hisoblagichi noto'g'ri bo'lsa, butun
hissa qulaydi.

Ish tsikli target tezligi: **`$REVIX_SUT_RATE_HZ`**, default `2000` iter/s.
Tsikl absolut `CLOCK_MONOTONIC` deadline'larda ishlaydi (drift yig'masligi uchun).

---

## 5. Fault endpoint'lari

| kind | argumentlar | xatti-harakat | pilot'da kerakmi |
|---|---|---|---|
| `exit` | `code=<int>` (default 1) | javob yuboradi, keyin `_exit(code)` | ✅ **P1** |
| `sigkill_self` | — | javob yuboradi, keyin `kill(getpid(), SIGKILL)` | ✅ P1 variant |
| `sigsegv` | — | javob yuboradi, keyin ataylab segfault | P2 |
| `deadlock` | — | ikki mutex'ni teskari tartibda oladi → deadlock | P2 |
| `spin` | — | ish lock'ini ushlab tor spin → livelock | P2 |
| `block_fifo` | `path=<yo'l>` | FIFO'dan bloklanuvchi o'qish | P2 |
| `leak` | `rate_mb_s=<f>` | fon oqimi shu tezlikda xotira ajratadi va tegadi | P2 |
| `stop_progress` | — | ish tsikli to'xtaydi, socket javob beradi (fail-silent) | P2 |

**Barcha fault'lar:**
- **AVVAL** `OK armed=<kind>` javobini yuboradi, **KEYIN** bajaradi.
  Busiz harness fault'ning qabul qilinganini bilmaydi.
- `stderr` ga bitta satr yozadi: `FAULT ARMED <kind> mono_us=<u64>` —
  bu `inject_ack` ning ikki tomonli bracket'ining SUT tomoni
  (`PREREGISTRATION.md` §3).

### Start vaqtidagi fault'lar (env orqali, socket emas)

| env | ta'siri |
|---|---|
| `REVIX_SUT_DELAY_READY_MS` | `READY=1` ni shuncha ms kechiktiradi (`slow_start`) |
| `REVIX_SUT_CONFIG` | config faylini o'qiydi; yaroqsiz bo'lsa nolga teng bo'lmagan kod bilan chiqadi (`misconfiguration`) |

---

## 6. systemd integratsiyasi

- **`Type=notify`**. Socket tinglashga tayyor bo'lgandan **keyin**
  `sd_notify(0, "READY=1")`.
- `WATCHDOG_USEC` env bo'lsa, `sd_notify(0, "WATCHDOG=1")` ni har
  `WATCHDOG_USEC/2` mikrosekundda yuboradi. Ish tsikli to'xtasa watchdog ham
  to'xtaydi — shunda `stop_progress` va `deadlock` systemd'ga ham ko'rinadi.
- `STATUS=` ixtiyoriy.
- `SIGTERM` da toza chiqish (0 kod), socket o'chiriladi.

---

## 7. Misol almashuvi

```
-> PROBE
<- OK progress=18452 pid=4711 invocation=6b1f49fa2c3d4e5f6a7b8c9d0e1f2a3b rss_kb=5120 mono_us=884213771

-> FAULT exit code=1
<- OK armed=exit
   (stderr: FAULT ARMED exit mono_us=884215002)
   (jarayon 1 kod bilan chiqadi)

-> PROBE
<- (ulanish rad etiladi -- ECONNREFUSED)
```

---

## 8. Prober tomoni uchun shartlar

`PREREGISTRATION.md` §2 va §3 dan:

| parametr | qiymat |
|---|---|
| Probe davri `P` | **100 ms** (10 Hz), absolut `CLOCK_MONOTONIC` deadline'larda |
| `T_conn` | 50 ms |
| `T_rt` | 50 ms |
| `k_f` (failure uchun ketma-ket buzilish) | **3** |

**Contract buzilishi turlari** (`probe_sample.outcome` yopiq enum):
`ok`, `conn_refused`, `conn_timeout`, `rt_timeout`, `bad_response`, `no_progress`

`no_progress` = ulanish va javob muvaffaqiyatli, lekin `progress` oldingi
probe'dan **oshmagan** (va `invocation` o'zgarmagan).

> **Diqqat:** `invocation` o'zgargan bo'lsa `progress` kamayishi NORMAL
> (restart → 0 dan boshlanadi). Bu holat `no_progress` DEYILMAYDI —
> u yangi invocation'ning birinchi probe'i.

> **KRITIK cheklov (`PREREGISTRATION.md` §5 sirkulyarlik kafolati):**
> o'lchov prober'i **hech bir arm'ning qaror yo'liga ulanmaydi** va uchala
> arm'da bir xil ishlaydi. Arm C (REVIX) probe'ga muhtoj bo'lsa, u **alohida**
> process bo'ladi.
