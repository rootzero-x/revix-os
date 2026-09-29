# 01 — Muhit tekshiruvlari (empirik)

Bu hujjatdagi har bir natija **shu mashinada haqiqatan ishga tushirilgan**
buyruqdan olingan. Hujjatdan o'qilgan yoki taxmin qilingan narsa yo'q.

**Sana:** 2026-09-29
**Mashina:** Kali GNU/Linux Rolling 2026.3, kernel 7.1.5+kali-amd64, systemd 261 (261.2-1)

---

## 1. cgroup delegatsiyasi

```
$ systemctl show user@1000.service -p Delegate -p DelegateControllers
Delegate=yes
DelegateControllers=cpu memory pids
```

| Controller | Delegated | Natija |
|---|---|---|
| `cpu`, `memory`, `pids` | ✅ | privilegiyasiz sozlanadi |
| **`io`** | ❌ | `io.max` **yo'q** → IO injection root/guest talab qiladi |

Lekin `io.pressure` **o'qiladi** (io controller o'chiq bo'lsa ham) — pastga qarang.

---

## 2. ⚠️ Slice nomlashdagi tuzoq — validlik xatosi bo'lardi

```
$ systemd-run --user --slice=revix-envcheck.slice --unit=revix-envcheck-a \
    --property=MemoryMax=64M --property=MemorySwapMax=0 --property=TasksMax=16 \
    --collect sleep 60
Running as unit: revix-envcheck-a.service

$ find .../user@1000.service -maxdepth 2 -name "revix*" -type d
.../user@1000.service/revix.slice
.../user@1000.service/revix.slice/revix-envcheck.slice          <-- NESTED
.../revix.slice/revix-envcheck.slice/revix-envcheck-a.service
```

**systemd slice nomlarida `-` ierarxiya ajratuvchisi.** `a-b.slice` →
`a.slice/a-b.slice`. systemd oraliq `a.slice` ni avtomatik yaratadi.

→ Rejaning `revix-harness.slice` nomi **sibling bo'lmas edi**, `revix.slice`
ning childi bo'lib qolardi, va harness PSI'si eksperiment PSI'siga
qo'shilardi. Bu kosmetik emas — `PREREGISTRATION.md` §8.2 aynan shu
feedback artefaktini oldini olmoqchi.

**Tuzatildi** (pre-registration amendment v1 → v1.1):

| eski | yangi |
|---|---|
| `revix.slice` | **`revixlab.slice`** |
| `revix-harness.slice` | **`revixmon.slice`** |

Tasdiq: `--slice=revixlab.slice` → `.../user@1000.service/revixlab.slice`
(to'g'ridan-to'g'ri child, nesting yo'q).

**Service nomlaridagi dash muammo emas** — `revix-envcheck-a.service`
`--slice=` ko'rsatgan joyga tushdi, hosila ierarxiya yaratmadi.

---

## 3. cgroup fayllari — yozish huquqi

`revixlab.slice` da (privilegiyasiz, `rootzero` sifatida):

| fayl | mavjud | yoziladi | o'qiladi |
|---|---|---|---|
| `cgroup.kill` | ✅ | ✅ | — |
| `memory.max` | ✅ | ✅ | ✅ |
| `memory.high` | ✅ | ✅ | ✅ |
| `memory.swap.max` | ✅ | ✅ | ✅ |
| `memory.pressure` | ✅ | ✅ | ✅ |
| `cpu.pressure` | ✅ | ✅ | ✅ |
| **`io.pressure`** | ✅ | ✅ | ✅ |
| `memory.current` | ✅ | — | ✅ |
| `memory.events` | ✅ | — | ✅ |

**`io.pressure` io controller delegated bo'lmasa ham o'qiladi** — ya'ni
**IO PSI o'lchash privilegiyasiz, IO injection esa emas.**

### `cgroup.kill` haqiqatan ishlaydi
```
$ echo 1 > .../revixlab.slice/cgroup.kill
$ systemctl --user is-active revix-envcheck-a.service
inactive
```
Atomik subtree kill bitta yozish bilan tasdiqlandi. Bu washout va guard
teardown uchun asosiy mexanizm.

---

## 4. Transient unit property'lari

```
$ systemd-run --user --slice=revixlab.slice --unit=revix-ec-restart \
    --property=Restart=on-failure --property=RestartSec=1s \
    --property=RestartSteps=4 --property=RestartMaxDelaySec=8s \
    --property=StartLimitBurst=0 --property=MemoryMax=64M --collect sleep 5
$ systemctl --user show revix-ec-restart.service -p RestartSteps -p StartLimitBurst
StartLimitBurst=0
RestartSteps=4
```

✅ **`RestartSteps=` transient property sifatida qabul qilinadi** → Baseline B
uchun `~/.config/systemd/user/` ga fayl yozish **kerak emas**.

```
$ systemd-run --user ... --property=WatchdogSec=5s --property=TimeoutStartSec=3s ...
$ systemctl --user show revix-ec-wd.service -p WatchdogUSec -p TimeoutStartUSec
TimeoutStartUSec=3s
WatchdogUSec=5s
```

✅ `WatchdogSec` va `TimeoutStartSec` user unit'da ishlaydi.

### `systemctl show` uchun to'g'ri property nomlari
Vaqt property'lari `USec` suffiksi bilan chiqadi — `run_meta` ga dump qilishda
shu nomlar ishlatiladi:

```
RestartUSec=100ms
RestartMaxDelayUSec=infinity
RestartSteps=0
RestartMode=normal
```

> Diqqat: `--collect` bilan unit tugagandan keyin o'chadi, va `systemctl show`
> mavjud bo'lmagan unit uchun **default**larni chiqaradi. Yuqoridagi `0` /
> `infinity` — o'chgan unit'ning default'lari, ishlagan qiymat emas.
> **Har unit'ning property'lari u TIRIK paytida dump qilinishi shart.**

---

## 5. PSI poll trigger — privilegiyasiz cheklov

```
$ # memory.pressure ga trigger yozish, turli oyna kattaliklari bilan
  oyna   500 ms -> RAD ETILDI (Invalid argument)
  oyna  1000 ms -> RAD ETILDI (Invalid argument)
  oyna  2000 ms -> QABUL QILINDI
  oyna  4000 ms -> QABUL QILINDI
```

✅ **Privilegiyasiz trigger oynasi 2 s karrasi bo'lishi shart** (Linux 6.5+).
Sub-2s event-driven PSI reaksiyasi `CAP_SYS_RESOURCE` talab qiladi.

→ `PREREGISTRATION.md` §7 ning qarori tasdiqlandi: **`total` polling
ishlatiladi, trigger emas.** Trigger keyingi optimizatsiya, dependency emas.

---

## 6. ⚠️ Harness jarayonlari Claude scope ichida tug'iladi

```
$ cat /proc/self/cgroup
0::/user.slice/user-1000.slice/user@1000.service/app.slice/app-com.anthropic.Claude-76218.scope
```

Ishlab chiqish vositasidan ishga tushirilgan har qanday jarayon **Claude
desktop scope ichida** tug'iladi. Agar pressure generatori shu yerda
ishlatilsa — uning xotirasi Claude scope'iga hisoblanadi va **oomd Claude'ni
o'ldirishi mumkin.**

→ **Majburiy:** eksperiment jarayonlari **faqat** `systemd-run --user
--slice=revixlab.slice` orqali ishga tushiriladi, shunda ular alohida
cgroup'ga tushadi. Harness jarayonlari — `--slice=revixmon.slice`.

**Hech qachon** pressure generatorini to'g'ridan-to'g'ri Bash'dan
(`python3 pressure.py &`) ishga tushirmaslik.

---

## 7. oomd holati (takror tasdiq)

```
$ cat /usr/lib/systemd/system/user@.service.d/10-oomd-user-service-defaults.conf
[Service]
ManagedOOMMemoryPressure=kill
ManagedOOMMemoryPressureLimit=50%

$ systemd-analyze cat-config systemd/oomd.conf | grep Duration
DefaultMemoryPressureDurationSec=20s

$ systemctl show user@1000.service -p ManagedOOMMemoryPressure
ManagedOOMMemoryPressure=kill
```

→ Guard va ≤12 s pressure oynasi **majburiy**.
Batafsil: [`00-pilot-topologiya.md`](00-pilot-topologiya.md) §3.1

---

## 8. Resurs zaxirasi

```
$ free -h
               total        used        free      shared  buff/cache   available
Mem:            15Gi       7.4Gi       3.2Gi        92Mi       4.8Gi       7.6Gi
Swap:          5.5Gi          0B       5.5Gi

$ getfacl /dev/kvm | grep rootzero
user:rootzero:rw-                      # KVM ishlaydi (kvm guruhida bo'lmasa ham)

$ df -h / | tail -1
/dev/nvme0n1p6  100G   70G   25G  74% /
```

2 GiB eksperiment shifti 7.6 GiB available'ga nisbatan xavfsiz zaxira qoldiradi.
QEMU guest uchun 25 G bo'sh joy va ishlaydigan KVM mavjud.

---

## 9. Tozalash tasdiqlandi

```
$ systemctl --user list-units 'revix*' --all --no-legend
(bo'sh)
$ find .../user@1000.service -maxdepth 1 -name "revix*" -type d
(bo'sh)
```

Barcha test unit'lari va cgroup'lari tozalandi. `--collect` + `cgroup.kill` +
`systemctl --user reset-failed` kombinatsiyasi qoldiq qoldirmadi.
