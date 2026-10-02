# 08 — Guard rekalibratsiyasi (o'lchangan WSL2 muhitida)

Bu hujjatdagi har bir raqam **shu mashinada haqiqatan ishga tushirilgan**
buyruqning chiqishidan olingan. O'lchov bajarilmagan joyda shunday deb
yozilgan. Uchta belgi ishlatiladi:

- **FAKT** — o'lchandi, buyruq va chiqish keltirilgan;
- **TALQIN** — FAKTdan nima kelib chiqishi (o'lchov emas, xulosa);
- **CHEKLOV** — bu muhitda o'lchab bo'lmaydigan yoki kafolatlab bo'lmaydigan narsa.

Bu fayl [`02-guard-kalibratsiyasi.md`](02-guard-kalibratsiyasi.md) ning qayta
o'lchovi: o'sha hujjat avvalgi mashinani (native Kali, kernel 7.1.5, systemd 261,
15 GiB RAM, `systemd-oomd` **qurollangan**) yozgan. REVIX endi boshqa mashinada
ishlaydi va [`07-wsl-muhit-tekshiruvlari.md`](07-wsl-muhit-tekshiruvlari.md) §8
ning o'z xulosasi shuni talab qiladi:

> «Har qanday pressure eksperimentidan oldin guard testi (00 §6 qadam 3) va
> pressure dosing kalibratsiyasi (qadam 4) bu mashinada QAYTA bajarilishi shart.
> "Retrofit qilinmaydi."»

**Sana:** 2026-10-02 (18:08Z – 18:40Z; mahalliy UTC+05:00)
**Mashina:** hostname `Root-Zero`, Kali Rolling `VERSION_ID="2025.3"` (WSL2),
kernel `6.6.87.2-microsoft-standard-WSL2`, systemd `257 (257.7-1)`,
`MemTotal: 10183876 kB` (≈9.71 GiB), swap 4.0 GiB, 12 CPU (AMD Ryzen 5 5600H),
uid 1000 (`snowden`), `boot_id=ca4e5bab-2cd8-43aa-8455-2a22ca6746f3`,
`systemd-oomd` **o'rnatilmagan**.
**Topologiya:** `revixlab.slice` (**MemoryMax=1G**, MemoryHigh=192M,
MemorySwapMax=0, TasksMax=64, CPUQuota=200%) — ya'ni 02 ning sarlavhasidagi
aynan o'sha qiymatlar, `00-pilot-topologiya.md` §1 dagi `MemoryMax=2G` **emas**
(§12 OQ-4); `revixmon.slice` (harness, sibling).
**Skript:** [`scripts/guard-test.sh`](../../scripts/guard-test.sh) — **bir bayt
ham o'zgartirilmagan**; sozlash faqat uning o'z env o'zgaruvchilari orqali.
**Bajarilish joyi:** ext4 (`$HOME/revix-guardcal`), chiqishlar `$HOME/revix-runs/`
— `/mnt/c` (9p/drvfs) ustida **emas** (07 §7.2).

---

## 0. Qisqa xulosa

| | |
|---|---|
| Guard trip qiladimi, o'ldiradimi? | ✅ **HA** — 8 ta trip (5 tasi toza scope'da), har birida `kill_ok: true`, `SIGKILL`, `oom_kill: 0` |
| Davomiylik kriteriyasi aniqmi? | ✅ **HA** — `sustained_s` = 5.000018 / 5.000022 (limit 5.0); 15.000039 / 15.099918 / 15.100025 (limit 15.0) |
| `user@ ≈ lab` topilmasi saqlanadimi? | ✅ **HA** — toza run'larda `user/lab` nisbati p50 = **0.9963** (§4) |
| Kollateral zarar | ✅ **YO'Q** (§7); qoldiq **YO'Q** (§7.3) |
| `scripts/guard-test.sh` bu mashinada ishlaydimi? | ❌ **YO'Q** — ikki bloker (§2) |
| Mo'ljallangan doza (0.30 / 12 s) guard'ni trip qiladimi? | ❌ **trip QILMAYDI** — lekin skript default'lari bilan **doza 0.000** (§3.4) |
| Pressure epizodi o'z vaqt chegaralarida to'xtaydimi? | ❌ **YO'Q** — 5 s so'ralgan epizod 16.3 s davom etdi (§5) |
| `t_start` p90 — band `P0` | **0.0497 s** (n=30, toza) → §17 budjeti (0.8 s) **bajarildi**, 16× zaxira (§15.1) |
| `t_start` p90 — pressure ostida | **4.8133 s** (n=8; 14 urinishdan **6 tasi umuman start bo'lmadi**) → budjetdan **6×** katta (§15.2) |
| `D_probe` proxy p50 — band `P0` | **0.500 s** (n=12) → `0.20 × mean` = **0.0967 s** = **0.97 × P** < 5P → §18 qarori **KERAK** (§16) |
| Guard birinchi trip'dan keyin ham o'ldiradimi? | ❌ **YO'Q** — 350 s da 1 kill + 3256 `already_tripped` (§17) |
| **Pressure gate** | ⚠️ **guard qismi O'TDI; pilot hozir ishga tushirilishi MUMKIN EMAS** (§14) |

---

## 1. Metodologiya, provenance va kontaminatsiya yozuvi

### 1.1 Kim nimani o'lchadi

| Natija | Kim | Qayerda |
|---|---|---|
| Barcha guard run'lari, PSI jadvallari, containment, kollateral zarar, qoldiq, PID 1 probe | **`experiment/guard-recal`** (men) | §2–§8, §10 |
| Muhit faktlari (kernel, systemd, oomd yo'qligi, `MemTotal`, delegatsiya, distro idle-stop, `/mnt/c` latency) | **`agent/envcheck`** | 07 — **men qayta o'lchamadim**, havola qilaman |
| PID 1 restart hodisasining mustaqil o'lchovlari (`/proc/1/stat` 22-maydon, PID 1 yoshi orqaga ketishi) | **`agent/envcheck`**, **`agent/contract`**, **`agent/research`** | koordinator orqali; men §8 da **mustaqil** o'z o'lchovimni qildim |
| Kontaminatsiya manbasining kimligi (`agent/contract`, `agent/driver` pytest run'lari) | **koordinator** | §1.3 — men faqat jarayon command-line'larini ko'rdim |

### 1.2 Har bir run'da qayd etilgan narsa

Har run'ning oldi va orqasida (`collateral-before.txt`, `collateral-after.txt`):
`/proc/uptime`, `/proc/1/stat` 22-maydon (`starttime`, tick), PID 1 yoshi,
user manager PID'i, `boot_id`, `/proc/meminfo`, `/proc/vmstat oom_kill`,
begona `pytest`/`verify` jarayonlari, failed unit'lar, `revix*` unit va cgroup'lari,
runtime va persistent drop-in'lar.

Run **davomida** 5 Hz da (`revixguardcalsent-watch.service`, read-only):
lab `memory.events`, `memory.swap.current`, `memory.current`, `memory.peak`,
`/proc/vmstat oom_kill`, `MemAvailable`, `/proc/uptime`.
Run davomida 10 Hz da: `revix/psi_sampler.py` (`host`/`user`/`lab`/`mon`).

### 1.3 🔴 FAKT — kontaminatsiya: begona agentlar `user@1000.service` ichida ishladi

Men o'z snapshot'larimda begona yukni ko'rdim va qayd etdim. Birinchi
ko'rinishi 18:08:14Z da:

```
$ pgrep -a python3
334 python3 -m pytest tests/ -q
$ cat /proc/334/cgroup   -> 0::/init.scope
$ tr "\0" " " < /proc/300/cmdline
/bin/bash /mnt/c/Users/snowden/revix-os/.claude/tmp/verify2.sh
$ ps -o pcpu=,rss= -p 334   -> 90.9  183132
```

journal esa (`systemd[238]` — user manager) begona **jonli transient
unit**larni ko'rsatdi:

```
Oct 02 23:13:13 ... Created slice revixselftest.slice - Slice /revixselftest.
Oct 02 23:13:13 ... Started revixselftest-sink.service - revix selftest...
Oct 02 23:13:13 ... revixselftest-sink.service: Main process exited, code=killed, status=9/KILL
Oct 02 23:13:13 ... Removed slice revixselftest.slice
   (shuningdek -watch, -preflight, -teardown, -failed, -sliceprop)
```

Koordinator ma'lumoti (men agentlarning kimligini isbotlamadim):
`agent/contract` to'liq suite'ni bir marta (~87 s), `agent/driver` to'liq
suite'ni ikki marta + `tests/unit/` ni yana bir marta ishga tushirgan.
`tests/unit/test_units.py` D-Bus orqali **jonli transient user unit** yaratadi
va ular `user@1000.service` ichiga tushadi — aynan §4 o'qiydigan ota scope.

**Natijasi.** Men har bir run'ni o'z snapshot'imga qarab **CLEAN** yoki **DIRTY**
deb belgiladim va **DIRTY** bo'lganlarini koordinator guest'ni tozalaganidan
keyin **qaytadan o'lchadim**. Ikki o'qish ham §3 va §4 da beriladi — o'chirilgan
o'lchov ma'lumot emas, tan olingan kontaminatsiyalangan o'lchov esa ma'lumot.

### 1.4 FAKT — PID 1 restart detektori har run'da tekshirildi

`07-wsl-muhit-tekshiruvlari.md` §4.4 va koordinator yetkazgan uchta mustaqil
o'lchov: bu guest'da PID 1 **`boot_id` o'zgarmasdan** qayta ishga tushadi va
shunda **barcha transient unit'lar yo'qoladi** — guard, generator va sampler
ham transient unit. Shuning uchun har run'da `/proc/1/stat` 22-maydoni
o'lchandi:

| run | `pid1_starttime_ticks` (oldi / orqa) | holat |
|---|---|---|
| C1 | 252900 / 252900 | ✅ o'zgarmadi |
| C2 | 252900 / 252900 | ✅ o'zgarmadi |
| C2b | 297003 / 297003 | ✅ o'zgarmadi |
| C3 | 252900 / 252900 | ✅ o'zgarmadi |
| C4 | 252900 / 252900 | ✅ o'zgarmadi |
| C5 | 252900 / 252900 | ✅ o'zgarmadi |

Run 1–7 da bu maydon **yozilmagan** (detektorni koordinator talabidan keyin
qo'shdim); ular uchun o'rniga PID 1 yoshi ishlatildi va u har safar run
davomiyligicha o'sgan (masalan run 3: 32 s → 56 s, run davomiyligi 24 s), ya'ni
o'sha run'lar davomida ham restart bo'lmagan. Lekin run 2 va run 5 **restartdan
keyin 1 s** ichida boshlangan (`pid1_etimes: 13` va `1`), va run 2 aynan shu
sababdan **yaroqsiz** (§2.2).

**CHEKLOV:** hisobotdagi hech bir run PID 1 restart'i ichida qolmagan, lekin
bu kafolat emas — bu faqat ikki chegara o'lchovidan chiqqan xulosa. Restart
run'ning **o'rtasida** bo'lsa, oxirgi o'qish uni ko'rsatadi (maydon o'zgaradi),
demak detektor yetarli.

---

## 2. 🔴 Ikki bloker: `scripts/guard-test.sh` bu mashinada ishga tushmaydi

Topshiriq aytganidek, skript **avval aynan belgilangan ko'rinishda** ishga
tushirildi:

```
$ OUT=$HOME/revix-runs/guard-recal-1 SUSTAIN_MAX=15.0 bash scripts/guard-test.sh
OUT=/home/snowden/revix-runs/guard-recal-1
kuzatiladi: user (/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service)
runaway chegaralari: full_avg10=85.0 some_avg10=90.0 rate2s=0.98
davomiylik: >=0.35 tezlik, 15.0s dan uzoq -> trip
pressure: mode=ramp 8s, cap 768M, RuntimeMaxSec=12s

--- pre-flight ---
  MemAvailable kB: 9645844
  vmstat oom_kill: 0
                                                        <-- va shu yerda TUGADI
######## guard-test.sh rc=1 ########
```

**FAKT:** skript 0.18 s ichida `rc=1` bilan chiqdi. `guard.jsonl`, `psi.csv`,
`pressure.jsonl` yaratilmadi; guard hatto ishga tushmadi.

Yon tomondan tasdiq: `SUSTAIN_MAX` **haqiqatan** 15.0 — skriptning o'z
chiqishi `davomiylik: >=0.35 tezlik, 15.0s dan uzoq -> trip` deb yozdi, ya'ni
commit `251f45f` ning tuzatishi joyida (`TESTING.md` §3 dagi «default `13.0`»
ogohligi **eskirgan** — §12 OQ-1).

### 2.1 🔴 Bloker 1 — `pgrep` + `set -euo pipefail`: Claude/Chrome guest ichida yo'q

Skript pre-flight'dan keyin:

```bash
CLAUDE_PIDS="$(pgrep -f 'claude-desktop --type=renderer' | tr '\n' ' ')"
CHROME_PIDS="$(pgrep -f 'chrome --type=renderer' | head -3 | tr '\n' ' ')"
```

**FAKT:** bu guest'da bunday jarayon yo'q — Claude va Chrome **Windows
tomonida** ishlaydi va bu guest'ning cgroup daraxtiga umuman kirmaydi
(07 §4.7: shell'dan tug'ilgan jarayonlar `/init.scope` da; desktop ilovalari
esa guest'da mavjud emas). `pgrep` moslik topmasa `1` qaytaradi, `pipefail`
butun pipeline'ni muvaffaqiyatsiz qiladi, `set -e` esa skriptni o'ldiradi.
Shuning uchun `kuzatiladigan Claude renderer PID'lar:` qatori **hech qachon
chiqmadi**.

**TALQIN:** bu `02-guard-kalibratsiyasi.md` §6 ning kollateral-zarar
tekshiruvi avvalgi mashinada *bir xil Linux desktop'da* Claude va Chrome
ishlayotganiga bog'lab qo'yilganining natijasi. Bu mashinada u tekshiruv
mavjud emas va skript **fail-closed emas, fail-blind**: u xavfsizlik tekshiruvi
yo'qligidan emas, `pgrep` ning exit kodidan yiqiladi.

### 2.2 🔴 Bloker 2 — `memory.high` hech qachon qo'yilmaydi, demak pressure mexanizmi mavjud emas

`02-guard-kalibratsiyasi.md` sarlavhasi topologiyani `revixlab.slice`
(MemoryMax=1G, **MemoryHigh=192M**, …) deb yozadi va §3 butun mexanizmni
`memory.high` dan oshishga qurgan. Lekin:

**FAKT:** `scripts/guard-test.sh` `revixlab.slice` ga **hech qanday property
qo'ymaydi**. U faqat `systemd-run --user --slice=revixlab.slice …` qiladi, ya'ni
slice default'lar bilan tug'iladi (`memory.high = max`). Repo'da bu bo'shliqni
to'ldiradigan joy yo'q:

```
$ grep -rn "set-property\|MemoryHigh" scripts/ revix/guard.py
(scripts/ da hech narsa; guard.py da hech narsa)
```

Natijasi o'lchangan (run 2, `memory.high` qo'yilmagan holat):

```
touched_mb min=32 max=768 last=768
lab memory.current max=817700864 (779.8 MiB)
lab memory.events high: min=0 max=0 (delta=0)        <-- throttling YO'Q
PEAK user@=0.000  lab=0.000
```

768 MiB anonim xotira ajratildi, bitta ham reclaim throttling hodisasi
bo'lmadi, PSI **aynan nol** qoldi. Guard 22 s kuzatdi va `tripped: false`
bilan tugadi — chunki **kuzatadigan narsa yo'q edi**.

**TALQIN:** `02` ning o'z o'lchovlari operator `revixlab.slice` ga property'ni
**skriptdan tashqarida** qo'ygan holatda olingan (`02` §6: «`set-property
--runtime` ishlatilgani uchun» — bu qadam hech qayerda hujjatlashtirilmagan:
na `TESTING.md` §3 protsedurasida, na skriptda). Ya'ni `02` §5 ning to'rt
run'i **qayta ishlab chiqarilishi mumkin emas** faqat `TESTING.md` ni o'qib.

**Men nima qildim (va nega bu tuzatish emas, operator qadami):**

```
$ systemctl --user set-property --runtime revixlab.slice \
    MemoryMax=1G MemoryHigh=192M MemorySwapMax=0 TasksMax=64 CPUQuota=200%
rc=0
$ systemctl --user show revixlab.slice -p MemoryMax -p MemoryHigh -p MemorySwapMax -p TasksMax -p CPUQuotaPerSecUSec
CPUQuotaPerSecUSec=2s   MemoryHigh=201326592   MemoryMax=1073741824
MemorySwapMax=0         TasksMax=64
$ find /run/user/1000/systemd/user.control -maxdepth 3
/run/user/1000/systemd/user.control/revixlab.slice.d/50-{CPUQuota,TasksMax,MemorySwapMax,MemoryHigh,MemoryMax}.conf
```

Kernel tomonidan o'zaro tekshiruv (slice'da unit paydo bo'lgandan keyin):

```
memory.max 1073741824   memory.high 201326592   memory.swap.max 0
pids.max 64             cpu.max 200000 100000
```

**FAKT (kutilmagan, lekin muhim):** `set-property --runtime` **hali faol
bo'lmagan**, fragment fayli yo'q implicit slice uchun ham ishlaydi
(`LoadState=loaded ActiveState=inactive FragmentPath=` holatida `rc=0`), va
drop-in faqat `/run/user/1000/systemd/user.control/` da paydo bo'ladi —
`~/.config/systemd/user/` da **hech narsa** (§7.3).

**FAKT (run 2 ni yaroqsiz qilgan narsa):** bu drop-in'lar `/run/user/1000`
tmpfs'ida yashaydi. Distro oxirgi `wsl.exe` klienti chiqqandan ~10–15 s keyin
to'xtaydi (07 §4.4) va qayta ishga tushganda `/run/user/1000` **yangi tmpfs**
bo'ladi — drop-in'lar yo'qoladi. Run 2 da aynan shu bo'ldi: setup bir
`wsl.exe` chaqiruvida, run esa keyingisida bajarilgan; run 2 ning
`collateral-before.txt` da `pid1_etimes: 13` va
`runtime dropins: find: '…user.control': No such file or directory`.
**Run 2 shu sababdan yaroqsiz deb belgilandi** va keyingi barcha run'larda
setup **run bilan bir xil `wsl.exe` chaqiruvida** bajarildi.

### 2.3 Sentinel'lar — §6 ning kollateral tekshiruvining o'rnini bosuvchi (va nimani isbotlamaydi)

`02` §6 kollateral zararni «Claude renderer PID'lari tirik, Chrome renderer
PID'lari tirik» bilan o'lchagan. Bu mashinada bunday jarayon yo'q (§2.1),
shuning uchun ikkita **sentinel** unit yaratdim:

```
$ cat /tmp/gc-sentinel/gc-sentinel-claude-desktop
#!/bin/bash
sleep "${SENT_SECONDS:-150}" &
wait

$ systemd-run --user --slice=revixguardcalsent.slice --unit=revixguardcalsent-claude \
    --collect --property=MemoryMax=32M --property=MemorySwapMax=0 \
    --property=TasksMax=16 --property=RuntimeMaxSec=55s --setenv=SENT_SECONDS=55 \
    /bin/bash /tmp/gc-sentinel/gc-sentinel-claude-desktop --type=renderer
```

(`exec` **ishlatilmaydi**: `exec sleep` argv'ni almashtirib yuboradi va
`pgrep -f` moslikni yo'qotadi — bu birinchi urinishda o'lchandi.)

**Nimani ta'minlaydi (FAKT):**
- ularning command-line'i skriptning `pgrep` qatorlariga mos keladi, demak
  `guard-test.sh` **o'zgartirilmasdan** oxirigacha ishlaydi va o'zining
  post-flight tekshiruvini bajaradi (`Claude PID 362 TIRIK`);
- ular `user@1000.service` **ichida**, lekin `revixlab.slice` **tashqarisida**
  (`revixguardcalsent.slice` — dash'siz nom, demak `user@` ning bevosita
  childi, 07 §5), ya'ni ular `cgroup.kill` subtree'siga kirmaydi va
  ularni o'ldiradigan har qanday narsa **haqiqiy kollateral zarar**dir;
- `MemoryMax=32M`, `MemorySwapMax=0`, `TasksMax=16`, `RuntimeMaxSec=` —
  00 §2 ning cheklash qoidalari ularga ham qo'llanadi.

**Nimani isbotlamaydi (CHEKLOV):**
- ular **idle `sleep`**, ya'ni haqiqiy brauzer yoki editor emas: ularning
  xotira izi 32 MiB bilan chegaralangan, reclaim bosimiga javob bermaydi,
  va `oom_score` bo'yicha jozibador nishon emas. `02` §6 «Claude renderer
  tirik» deganda *haqiqiy, yirik, faol* iste'molchi haqida gapirgan;
- demak sentinel'lar **kill-authority yo'qligi**ni (oomd yo'q, kernel OOM
  bo'lmadi) tasdiqlaydi, lekin *«haqiqiy desktop ilovasi bu yukni omon
  qoladi»*ni **tasdiqlamaydi**;
- bu mashinada bu savolni o'lchash **umuman mumkin emas**: guest ichida
  desktop ilovasi yo'q, Windows tomonidagi Claude/Chrome esa guest'ning PSI
  va cgroup ierarxiyasiga kirmaydi.

---

## 3. Guard uchdan-uchiga — 13 run

`WATCH=user` (default) — guard `user@1000.service/memory.pressure` ni kuzatadi,
`revixlab.slice` ni o'ldiradi. Hamma joyda `SUSTAIN_RATE=0.35`.

| run | konfiguratsiya (env) | toza? | `reason` | o'lchangan qiymat | `kill_ok` | guard exit |
|---|---|---|---|---|---|---|
| **1** | `SUSTAIN_MAX=15.0` (aynan topshiriqdagi) | CLEAN | — | **skript `rc=1`, guard ishga tushmadi** (§2.1) | — | — |
| **2** | `=1` bilan bir xil, `memory.high` qo'yilgan deb o'ylab | DIRTY | — | **YAROQSIZ**: drop-in'lar distro restart'ida yo'qolgan, stall = 0.000 (§2.2) | — | 0 |
| **3** | `MODE=ramp PRESS=8 RUNTIME=12 OBS=22`, **shipped chegaralar** | **CLEAN** | `user_full_rate2s_runaway` | `rate=0.983641139050318` `limit=0.98` `window_us=2000017` | **true** | 1 |
| 4 | `MODE=pi TARGET=0.30 PRESS=12 RUNTIME=15 OBS=28` | DIRTY | **trip YO'Q** | doza **0.000** | — | 0 |
| 5 | `MODE=ramp RATE2S=0.999 SUSTAIN_MAX=5.0 PRESS=12` | DIRTY | `sustained_pressure` | `sustained_s=5.000018` `limit_s=5.0` `rate=0.9716345992789025` | true | 1 |
| 6 | `MODE=ramp RATE2S=0.999 SUSTAIN_MAX=15.0 PRESS=12` | DIRTY | `user_full_rate2s_runaway` | `rate=0.9990905131875588` `limit=0.999` `window_us=2000029` | true | 1 |
| 7 | `MODE=ramp RATE2S=1.5 AVG10=99.9 SUSTAIN_MAX=15.0 PRESS=12` | DIRTY | `sustained_pressure` | `sustained_s=15.099994` `limit_s=15.0` `rate=0.995337` | true | 1 |
| **C1** | `=3` bilan **aynan bir xil**, toza scope'da | **CLEAN** | `sustained_pressure` | `sustained_s=15.000039` `limit_s=15.0` `rate=0.9631396843015785` | **true** | 1 |
| C2 | `=4` bilan bir xil | DIRTY | **trip YO'Q** | doza **0.000** | — | 0 |
| **C2b** | `=4` bilan bir xil, toza scope'da — **calib v4** | **CLEAN** | **trip YO'Q** ✅ | doza **0.000** ⚠️ | — | **0** |
| **C3** | `=5` bilan bir xil, toza scope'da — **Run D ekvivalenti** | **CLEAN** | `sustained_pressure` | `sustained_s=5.000022` `limit_s=5.0` `rate=0.983999` | **true** | 1 |
| **C4** | `=7` bilan bir xil, toza scope'da | **CLEAN** | `sustained_pressure` | `sustained_s=15.100025` `limit_s=15.0` `rate=0.995028` | **true** | 1 |
| **C5** | `PRESS=5 RUNTIME=7`, qolgani `=C4` | **CLEAN** | `sustained_pressure` | `sustained_s=15.099918` `limit_s=15.0` `rate=0.9972714077821545` | **true** | 1 |

`RATE2S=0.999` va `RATE2S=1.5 / AVG10=99.9` — oniy runaway tutuvchilarni
ko'tarib, **davomiylik yo'lini izolyatsiya qilish** uchun (skriptning o'z env
interfeysi orqali). `02` Run D ham xuddi shu maqsadda PI nishonini 0.60 ga
qo'ygan. Davomiylik chegarasi bu run'larda **har doim qurollangan**.

### 3.1 FAKT — guard o'ldirdi, kernel emas

Har bir trip'da `guard_event` `"action": "kill_subtree"`, `"kill_ok": true`, va
journal generatorning qanday o'lganini mustaqil tasdiqlaydi:

```
Oct 02 23:20:14 ... revix-press.service: Main process exited, code=killed, status=9/KILL
Oct 02 23:20:14 ... revix-press.service: Failed with result 'signal'
Oct 02 23:20:14 ... revix-press.service: Consumed 410ms CPU time, 200.8M memory peak.
Oct 02 23:20:30 ... revix-guard.service: Main process exited, code=exited, status=1/FAILURE
```

`status=1/FAILURE` — bu `guard.py` ning shartnomasi: exit 1 = trip bo'ldi
(exit 0 = hech qachon trip qilmadi, exit 2 = `watch_open_failed`). C2b da bu
qator **yo'q**, ya'ni guard 0 bilan chiqdi, va `trip.json` yaratilmadi:

```
$ ls $HOME/revix-runs/guard-recal-C2b/trip.json
ls: cannot access '…/trip.json': No such file or directory
$ grep guard_stop …/guard-recal-C2b/guard.jsonl
{… "tripped":false,"iterations":280,"elapsed_s":28.000422573999913}
```

Har bir run'da `memory.events` `oom_kill: 0` va `max: 0`, `/proc/vmstat
oom_kill` = 0 (§6). Ya'ni **o'ldirgan narsa `cgroup.kill`, OOM emas** —
`02` §5 ning asosiy shartining qayta tasdig'i.

### 3.2 FAKT — tezlik oynasi tor, 2 s

`02` §2 tuzatgan xato (oyna 2–8 s orasida suzishi) **qaytmagan**:
`window_us = 2000017` (run 3) va `2000029` (run 6) — ya'ni eng **tor**
`≥2 s` oyna tanlanadi. `psi.csv` dan hisoblangan oynalar ham `2.000000`–
`2.100030` s oralig'ida (10 Hz namuna qadami hisobiga).

### 3.3 FAKT — davomiylik kriteriyasi bir poll tik aniqligida ishlaydi

| limit | o'lchangan `sustained_s` | farq |
|---|---|---|
| 5.0 | **5.000018** (run 5), **5.000022** (C3) | +18 µs, +22 µs |
| 15.0 | **15.000039** (C1) | +39 µs |
| 15.0 | **15.099918** (C5), **15.099994** (run 7), **15.100025** (C4) | +0.0999 s ≈ bitta 100 ms poll tik |

**TALQIN:** chegaradan oshish lahzasi 10 Hz poll gridiga tushadi, shuning uchun
trip 15.000–15.100 s oralig'ida bo'ladi. Bu **bir poll periodidan katta
bo'lmagan** xato va `sustain_max_seconds` ni o'zgartirishni talab qilmaydi.

### 3.4 🔴 calib v4 — mo'ljallangan doza guard'ni trip QILMAYDI, lekin doza 0.000

Bu eksperiment umuman mumkinmi yoki yo'qmi degan savolni hal qiladigan run.
Toza scope'da (C2b), skriptning hech qanday chegarasi o'zgartirilmagan holda:

```
pressure_start: mode=pi target_rate=0.3 base_mb=160 step_mb=16 cap_mb=768
                max_seconds=12.0 oom_score_adj=1000
pressure_stop : touched_mb_at_stop=160 elapsed_s=12.13612743800013
samples=65 (shundan pressure_ramp=10)
rate2s non-None=47   max=0.0
churn: n=55 p50=7 max=12 sum=365
touched_mb min=16 max=160
guard_stop: tripped=false iterations=280 elapsed_s=28.000422573999913
lab memory.current max=185.3 MiB      (memory.high = 192 MiB)
lab memory.events high delta = 0      (throttling hodisasi YO'Q)
PEAK user@=0.0000  lab=0.0000
```

**FAKT:** guard **trip qilmadi** (`tripped: false`, `trip.json` yo'q, exit 0).
**FAKT:** erishilgan pressure ham **0.0000** — birorta namunada ham
`slice_full_rate2s > 0` bo'lmadi, `memory.events high` birorta marta ham
oshmadi. PI controller tik'da median 7, maksimum 12 blok churn qildi
(jami 365 blok × 16 MiB), ya'ni **boshqaruvchi to'liq to'yingan** holda
ishladi va hech narsa chiqarmadi.

**TALQIN:** `base = memory.high/MiB − 2·step_mb = 192 − 32 = 160` (kod
`pressure.py:run_pi`). 160 MiB `touched` + generator overhead'i bilan
`memory.current` **185.3 MiB** bo'ldi — `memory.high` = 192 MiB dan **past**.
Churn impulsi (ajrat → bo'shat) `memory.high` chegarasini kesib o'tmadi,
demak `02` §3 ning «impuls + duty cycle» mexanizmi **ishga tushmadi**.
`02` §3 da baza `184 MB` (`high=192MB` da) bo'lgan, ya'ni `step_mb=4`; skript
default'i `STEP_MB=16` esa bazani 24 MiB pastga tushiradi.

**Shuning uchun C2b «calib v4 o'tdi» DEGANI EMAS.** U faqat shuni
ko'rsatadi: *doza nol bo'lsa, guard trip qilmaydi* — bu kutilgan va
ma'lumotsiz natija. Mo'ljallangan 0.30 darajadagi doza bilan guard nima
qilishi §3.5 da bilvosita, §5 da esa to'g'ridan-to'g'ri o'lchanadi.

**CHEKLOV:** mo'ljallangan dozani **haqiqatan yetkazadigan** konfiguratsiya
bu hujjatda topilmadi va topilishi kerak ham emas — bu 00 §6 ning **4-qadami**
(`experiment/pressure-cal`) vazifasi. Men dozani sozlamadim.

### 3.5 FAKT — P1 bandi matematik jihatdan trip qila olmaydi; xavf P2 da

| band (PREREG §9.3) | tezlik | `sustain_rate_threshold = 0.35` | natija |
|---|---|---|---|
| `P0` | ~0 | past | sustain taymer **boshlanmaydi** |
| `P1` | 0.20–0.35 | chegara aynan yuqori chetida | taymer deyarli boshlanmaydi |
| `P2` | 0.60–0.80 | **yuqori** | taymer **ishlaydi**, 15 s da trip |

**TALQIN:** P1 trial'i guard'ni trip qila olmaydi (0.35 dan past → taymer
qayta tiklanadi; 0.98 runaway chegarasidan ham ancha past). Butun xavf
**P2** da: u 0.35 dan yuqori, demak sustain taymeri har P2 hold'ida ishlaydi
va faqat `hold_s + ramp_above_threshold_s < 15 s` bo'lsa trip qilmaydi. Bu
aynan `PREREGISTRATION.md` §9.4 ning 2-invarianti. §5 bu invariantning
hozirda **majburlab bo'lmasligi**ni ko'rsatadi.

### 3.6 FAKT — P2 bandi (0.60–0.80) birinchi marta ko'rindi, lekin ushlab turilmadi

Koordinator so'raganidek. `lab` scope'ning 2 s oynali `full` tezligi
0.60–0.80 oralig'iga tushgan namunalar soni (10 Hz, ya'ni namuna = 100 ms):

| run | toza? | namunalar | o'lchangan oraliq |
|---|---|---|---|
| 3 | CLEAN | 7 | 0.627 – 0.790 |
| C1 | CLEAN | 6 | 0.647 – 0.760 |
| C3 | CLEAN | 7 | 0.638 – 0.780 |
| C4 | CLEAN | 9 | 0.613 – 0.793 |
| C5 | CLEAN | 9 | 0.604 – 0.785 |

**TALQIN:** P2 bandi bu mashinada **fizik jihatdan erishiladi** — nazoratsiz
ramp unda 0.6–0.9 s davomida o'tadi. Lekin bu **ushlab turish** emas: ramp
bandni kesib o'tib ~0.99 ga to'yinadi (§3.7). Ya'ni bu P2 ning *mumkinligi*
haqidagi birinchi o'lchov, uning *boshqarilishi* haqida emas. `02` §8 ning
«P1/P2 bandlari erishiladigan» da'vosi 0.311 ga (P1 bandi) asoslangan edi;
bu hujjat P2 bandiga tegadigan birinchi raqamlarni beradi, lekin **P2 ni
nishon sifatida ushlash hali ko'rsatilmagan**. Bu `experiment/pressure-cal`
masalasi.

### 3.7 FAKT — nazoratsiz ramp 0.999 ga to'yinadi, ya'ni 0.98 dan YUQORI

| scope | eng katta o'lchangan 2 s tezlik |
|---|---|
| `user@1000.service` | **0.9992** (C5), 0.9991 (run 6, run 7), 0.9987 (C4) |
| `revixlab.slice` | **0.9993** (run 7), 0.9992 (C5), 0.9990 (C4, run 6) |

`02` §1 ning izohi `user_full_rate2s_max = 0.98` ni shunday asoslaydi:
«*`0.98` raqami o'lchovdan: qonuniy ramp burst'i **0.93–0.98** ga chiqadi*».
Bu mashinada u to'yinish darajasi **0.999** — ya'ni 0.98 dan yuqori.
Natijasi §9.1 da.

---

## 4. §1 ning qayta o'lchovi — `user@` PSI va `lab` PSI munosabati

Bu hujjat javob beradigan eng muhim ilmiy savol. `02` §1 bo'sh desktop'da
ota scope child scope'ni deyarli aynan aks ettirishini o'lchagan (cho'qqi
0.980 / 0.984) va aynan shu topilma guard'ni oniy chegaradan **davomiylik**
kriteriyasiga o'tkazgan. `02` §7 masala 1 va 07 §9 OQ-2 bu topilmani
**bo'sh scope shartiga bog'liq** deb belgilagan.

### 4.1 FAKT — toza scope, C1 (eng uzun toza platoli run)

2 s oynali `full` stall tezligi (har 5-namuna, `psi.csv`, 10 Hz):

| t (s) | `user@1000.service` | `revixlab.slice` | `user@` *some* | `revixmon.slice` | host | oyna (s) |
|---|---|---|---|---|---|---|
| 3.3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2.099925 |
| 3.8 | 0.201 | 0.219 | 0.201 | 0.000 | 0.208 | 2.099738 |
| 4.3 | 0.428 | 0.443 | 0.428 | 0.000 | 0.440 | 2.096038 |
| 4.8 | 0.655 | 0.677 | 0.655 | 0.000 | 0.674 | 2.100010 |
| 5.3 | 0.929 | 0.913 | 0.929 | 0.000 | 0.954 | 2.000004 |
| 5.8 | 0.958 | 0.988 | 0.958 | 0.000 | 0.984 | 2.099989 |
| 7.3 | 0.964 | 0.995 | 0.964 | 0.000 | 0.990 | 2.099984 |
| 9.3 | 0.966 | 0.996 | 0.966 | 0.000 | 0.988 | 2.000171 |
| 11.3 | 0.966 | 0.997 | 0.966 | 0.000 | 0.991 | 2.099893 |
| 13.3 | 0.827 | 0.860 | 0.827 | 0.000 | 0.871 | 2.000009 |
| 15.3 | 0.962 | 0.997 | 0.962 | 0.000 | 0.967 | 2.000020 |
| 17.3 | 0.960 | 0.997 | 0.960 | 0.000 | 0.945 | 2.099991 |
| 19.3 | 0.917 | 0.947 | 0.917 | 0.000 | 0.937 | 2.000094 |
| 20.8 | 0.230 | 0.236 | 0.230 | 0.000 | 0.236 | 2.099954 |
| 21.3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 2.100008 |
| **cho'qqi** | **0.9664** | **0.9985** | — | **0.0000** | — | — |

C3 (qisqaroq epizod, toza):

| t (s) | `user@` | `lab` | `user@` some | host |
|---|---|---|---|---|
| 3.5 | 0.220 | 0.223 | 0.220 | 0.222 |
| 4.5 | 0.676 | 0.685 | 0.676 | 0.669 |
| 5.5 | 0.978 | 0.991 | 0.978 | 0.972 |
| 7.0 | 0.984 | 0.997 | 0.984 | 0.990 |
| 8.5 | 0.984 | 0.997 | 0.984 | 0.992 |
| 9.5 | 0.640 | 0.649 | 0.640 | 0.647 |
| **cho'qqi** | **0.9840** | **0.9975** | — | — |

### 4.2 FAKT — barcha toza run'lar bo'yicha juftlashtirilgan statistika

`lab ≥ 0.05` (PREREG §8.4 quiescence chegarasi) bo'lgan namunalar ustida,
scope'lar juft-juft solishtirilgan (har scope o'z `read_mono_us` i bilan):

| to'plam | n | `user − lab` min / p05 / p50 / p95 / max | `user / lab` min / p05 / p50 / p95 / max |
|---|---|---|---|---|
| **CLEAN** (3, C1, C3, C4, C5) | **642** | −0.0626 / −0.0349 / **−0.0036** / +0.0003 / +0.0374 | 0.6881 / 0.9649 / **0.9963** / 1.0004 / 1.2489 |
| DIRTY (5, 6, 7) | 370 | −0.0937 / −0.0635 / **−0.0000** / +0.0115 / +0.0470 | 0.9062 / 0.9334 / **1.0000** / 1.0140 / 1.5176 |

Har run bo'yicha cho'qqilar:

(«cho'qqilar farqi» = `max(user) − max(lab)`, ya'ni ikki alohida cho'qqining
ayirmasi; «nisbat p50» esa **juftlashtirilgan** namunalar ustidagi mediana.)

| run | toza? | cho'qqi `user@` | cho'qqi `lab` | cho'qqilar farqi | nisbat p50 | n (aktiv) |
|---|---|---|---|---|---|---|
| 3 | CLEAN | 0.9487 | 0.9556 | −0.0069 | 1.0001 | 38 |
| C1 | CLEAN | 0.9664 | 0.9985 | −0.0321 | 0.9686 | 177 |
| C3 | CLEAN | 0.9840 | 0.9975 | −0.0135 | 0.9864 | 76 |
| C4 | CLEAN | 0.9987 | 0.9990 | −0.0003 | 1.0000 | 174 |
| C5 | CLEAN | 0.9992 | 0.9992 | −0.0000 | 0.9981 | 177 |
| 5 | DIRTY | 0.9937 | 0.9936 | +0.0001 | 1.0001 | 76 |
| 6 | DIRTY | 0.9991 | 0.9990 | +0.0001 | 0.9999 | 117 |
| 7 | DIRTY | 0.9991 | 0.9993 | −0.0002 | 0.9983 | 177 |

### 4.3 FAKT — kontaminatsiyalangan va toza o'qish, aynan bir xil konfiguratsiyada

Koordinator so'raganidek, ikkala raqam ham beriladi. Faqat **konfiguratsiyasi
aynan bir xil** juftliklar solishtiriladi (aks holda taqqoslash nazorat
qilinmagan bo'ladi):

| juftlik | `sustained_s` | cho'qqi `user@` | cho'qqi `lab` | nisbat p50 |
|---|---|---|---|---|
| run 5 (**DIRTY**) | 5.000018 | 0.9937 | 0.9936 | 1.0001 |
| C3 (**CLEAN**) | 5.000022 | 0.9840 | 0.9975 | 0.9864 |
| | Δ = **+4 µs** | Δ = −0.0097 | Δ = +0.0039 | Δ = −0.0137 |
| run 7 (**DIRTY**) | 15.099994 | 0.9991 | 0.9993 | 0.9983 |
| C4 (**CLEAN**) | 15.100025 | 0.9987 | 0.9990 | 1.0000 |
| | Δ = **+31 µs** | Δ = −0.0004 | Δ = −0.0003 | Δ = +0.0017 |
| run 4 (**DIRTY**) | trip yo'q | 0.0000 | 0.0000 | — |
| C2, C2b (**DIRTY**, **CLEAN**) | trip yo'q | 0.0000 | 0.0000 | — |

**TALQIN:** kontaminatsiya **o'lchangan natijalarni sezilarli o'zgartirmadi**.
Trip vaqtlari 4 µs va 31 µs ichida mos keldi; `user/lab` nisbati p50 ikki
holatda ham 0.986–1.000 oralig'ida. Sababi — 07 §4.7: begona `pytest`
jarayonlari `/init.scope` da tug'iladi, ya'ni `user@1000.service` ning PSI
ierarxiyasiga **kirmaydi**; `test_units.py` yaratgan transient unit'lar esa
`user@` ichida bo'lsa ham qisqa yashaydigan `sleep` tipidagi **idle** unit'lar,
va PSI `full` idle task'ni hisoblamaydi.

**Bu kutilgan samarani KO'RSATMAYDI.** Koordinator to'g'ri aytganidek,
`user@` ichidagi qo'shimcha **non-idle** task `full` ni pasaytirishi kerak edi.
Men bu samarani ko'rmadim, chunki begona CPU yuki `user@` ning **tashqarisida**
edi. Demak `02` §7 masala 1 («band desktop'da qayta o'lchanishi kerak»)
**hali ham ochiq**: bu kontaminatsiya *band desktop* emas, *band distro ildizi*
edi (§12 OQ-3).

### 4.4 TALQIN — munosabat saqlandi, lekin sababi o'zgardi va ishorasi doimiy

1. **Munosabat saqlanadi.** Toza run'larda `user/lab` nisbati p50 = 0.9963,
   p05 = 0.9649. `02` §1 ning cho'qqi juftligi 0.980 / 0.984 (nisbat 0.996);
   bu mashinada C4 da 0.9987 / 0.9990 (nisbat 0.9997), C1 da 0.9664 / 0.9985
   (nisbat 0.968). Ya'ni **ota scope child scope'ni hamon deyarli aynan aks
   ettiradi**, va shuning uchun **oniy chegarada trip qiluvchi guard hamon
   har bir P2 trial'ini o'ldirardi.** `02` §1 ning dizayn qarori — davomiylik
   kriteriyasi — **bu mashinada ham to'g'ri**.

2. **Lekin ishora doimiy va bir tomonli:** `user@` deyarli har doim `lab` dan
   **bir oz PAST** (p50 farq −0.0036; namunalarning 25.1% ida `user@` `lab` dan
   0.02 dan ko'proq past). Buning eng ehtimoliy sababi o'lchovda ko'rinadi:
   `revixmon.slice` (guard 10 Hz + sampler 10 Hz) **`user@1000.service` ning
   ichida**, va uning `full` tezligi hamma joyda **0.000** — ya'ni harness
   task'lari *non-idle, lekin stall qilmayotgan* task'lar. PSI `full` butun
   cgroup'dagi **barcha** non-idle task stall bo'lishini talab qiladi, demak
   harness'ning o'zi ota scope'ning `full` qiymatini pasaytiradi.
   **Bu TALQIN, atributsiya o'lchovi emas:** men harness'ni o'chirib qo'yib
   farqni o'lchamadim (guard'siz pressure ishga tushirish xavfsizlik qoidasini
   buzadi).

3. **`some == full` aynan.** Jadvallarda `user@ some` va `user@ full`
   ustunlari barcha qatorlarda bir xil (masalan C1 da 0.964 / 0.964). Bu
   `02` §1 ning mexanizm izohini to'g'ridan-to'g'ri tasdiqlaydi: pressure
   davomida `user@` ichidagi yagona haqiqiy ishchi — generator.

4. **Davomiylik kriteriyasining SABABI o'zgardi.** `02` §1 15 s ni oomd ning
   20 s sustained shartidan kelib chiqib tanlagan. Bu mashinada `systemd-oomd`
   **yo'q** (07 §2, §6.4), demak:
   - `02` §1 ning «*oomd ~28–30 s da ishlardi; guard 15 s da to'xtatadi*»
     zaxira hisobi bu yerda **bo'sh** — himoya qilinadigan daemon mavjud emas;
   - lekin 15 s ning **ikkinchi** asoslanishi — «*pilot hold ≤12 s + ramp
     ≤3 s = eng yomon holatda 15 s, demak to'g'ri ishlayotgan trial hech
     qachon trip qilmaydi*» — **oomd'ga umuman bog'liq emas** va o'z kuchida
     qoladi. Endi 15 s oomd'dan himoya emas, **epizod uzunligi
     invariantining majburlovchisi**: u `PREREGISTRATION.md` §9.4
     2-invariantini kodda amalga oshiradi.
   - Guard **majburiy va fail-closed bo'lib qoladi**, chunki yo'qolgan
     yagona xavf oomd edi; **kernel global OOM xavfi esa kichraymadi,
     o'sdi**: xotira zaxirasi 15 GiB dan **9.71 GiB** ga tushdi (07 §8).

---

## 5. 🔴 Pressure epizodi o'zining ikki vaqt chegarasini ham buzadi

Bu hujjatning eng jiddiy topilmasi va u guard chegarasi haqida emas.

`TESTING.md` §3 shunday da'vo qiladi:

> «**Ikki vaqt chegarasi chegaradan mustaqil**, demak PSI qanday bo'lishidan
> qat'i nazar pressure to'xtaydi. Bu skriptning eng muhim xavfsizlik
> xususiyati: u guard'ning to'g'ri ishlashiga **tayanmaydi**.»

**FAKT — bu da'vo bu mashinada rad etildi.** `lab` scope'ning 2 s tezligi
`sustain_rate_threshold = 0.35` dan yuqorida **uzluksiz** turgan vaqt,
`psi.csv` dan hisoblangan:

| run | `--max-seconds` | `RuntimeMaxSec=` | 0.35 dan yuqorida (lab) | `pressure_stop` yozuvi |
|---|---|---|---|---|
| **C5** | **5** | **7 s** | **16.3 s** | **YO'Q** (SIGKILL) |
| C1 | 8 | 12 s | 16.2 s | YO'Q (SIGKILL) |
| C3 | 12 | 15 s | 6.2 s | YO'Q (SIGKILL) |
| C4 | 12 | 14 s | 16.2 s | YO'Q (SIGKILL) |
| run 3 | 8 | 12 s | 2.5 s | YO'Q (SIGKILL) |
| C2b (doza 0) | 12 | 15 s | 0.0 s | **BOR**, `elapsed_s=12.136` |

Generatorning oxirgi `pressure_sample` yozuvi C5 da `t = 2.824 s` da, C4 da
`t = 2.815 s` da — ya'ni jarayon o'z log tsiklini bajarishni **to'xtatdi** va
shundan keyin ham pressure 13 s davom etdi.

journal `RuntimeMaxSec=` ning ishga tushganini va keyin nima bo'lganini
ko'rsatadi (C5):

```
Oct 02 23:31:49 ... revix-press.service: Service reached runtime time limit. Stopping.
Oct 02 23:31:59 ... revix-press.service: Main process exited, code=killed, status=9/KILL
Oct 02 23:31:59 ... revix-press.service: Failed with result 'timeout'
```

`RuntimeMaxSec=` SIGTERM yubordi, lekin jarayon **10 s** keyin, `SIGKILL`
bilan o'ldi.

**TALQIN (sabab, kod o'qishidan — mexanizm o'lchanmadi):**
`pressure.py:run_ramp` tsiklining ichida `self.alloc.add(chunk_mb << 20)`
turadi va `--max-seconds` faqat **tsikl boshida** tekshiriladi. Slice
`memory.high` dan oshganda kernel ajratuvchi task'ni reclaim throttling
bilan **uxlatadi**; `MemorySwapMax=0` va to'liq anonim xotira bilan reclaim
hech narsa bo'shatolmaydi, demak bitta `add()` chaqiruvi soniyalarga cho'zilishi
mumkin. Throttling uyqusi SIGTERM bilan uzilmaydi. Shuning uchun:
- generatorning **o'z** `--max-seconds` i — **cheklov emas**;
- systemd `RuntimeMaxSec=` ning SIGTERM'i — **kechikadi**;
- epizodni haqiqatan to'xtatgan narsa — **guard'ning `cgroup.kill`i** (SIGKILL,
  throttling uyqusini uzadi).

**CHEKLOV:** C2b da `pressure_stop` o'z vaqtida (`elapsed_s = 12.136`, so'rov
12.0 s) keldi, ya'ni PI rejimida va `memory.high` dan **past** bazada overrun
bo'lmaydi. Lekin aynan o'sha konfiguratsiya **doza ham bermaydi** (§3.4). Ya'ni
*dozani ham beradigan, ham o'z vaqtida to'xtaydigan konfiguratsiya bu hujjatda
o'lchanmadi — chunki bunday konfiguratsiya hozir mavjud emas.*

**Oqibati pilot uchun (TALQIN):** `PREREGISTRATION.md` §9.4 ning ikkinchi
invarianti `hold_s + ramp_above_threshold_s ≤ 15 s` **hozirda majburlab
bo'lmaydi**, chunki `hold_s` ni belgilaydigan mexanizm (generator
`--max-seconds` + `RuntimeMaxSec=`) haqiqiy `hold_s` ni belgilamaydi. O'lchov:
5 s so'ralgan, 16.3 s olindi. Demak P2 trial'i guard tomonidan o'ldiriladi
(`aborted_guard`) va bu **guard xatosi emas — guard aynan loyihalanganidek
ishlaydi**.

---

## 6. Containment tasdig'i

Har bir run bo'yicha, 5 Hz kuzatuvchidan (`collateral.csv`) va 10 Hz
sampler'dan (`psi.csv`), **run jonli bo'lgan paytda** o'qilgan:

| run | `memory.swap.current` max | lab `memory.events` `oom_kill` | lab `events.max` | lab `events.high` delta | `/proc/vmstat oom_kill` | lab `memory.current` max | `/proc/uptime` monoton |
|---|---|---|---|---|---|---|---|
| 2 | **0** | **0** | 0 | 0 | **0** | 779.8 MiB | ✅ |
| 3 | **0** | **0** | 0 | 631 | **0** | 200.6 MiB | ✅ |
| 4 | **0** | **0** | 0 | 0 | **0** | 185.4 MiB | ✅ |
| 5 | **0** | **0** | 0 | 991 | **0** | 204.7 MiB | ✅ |
| 6 | **0** | **0** | 0 | 981 | **0** | 206.6 MiB | ✅ |
| 7 | **0** | **0** | 0 | 1372 | **0** | 207.3 MiB | ✅ |
| C1 | **0** | **0** | 0 | 1460 | **0** | 209.0 MiB | ✅ |
| C2 | **0** | **0** | 0 | 0 | **0** | 185.2 MiB | ✅ |
| C2b | **0** | **0** | 0 | 0 | **0** | 185.3 MiB | ✅ |
| C3 | **0** | **0** | 0 | 794 | **0** | 205.0 MiB | ✅ |
| C4 | **0** | **0** | 0 | 1202 | **0** | 210.3 MiB | ✅ |
| C5 | **0** | **0** | 0 | 1185 | **0** | 209.0 MiB | ✅ |

**FAKT:** `memory.swap.current` **hamma run'da, hamma namunada 0** — ikki
mustaqil kuzatuvchi bo'yicha. 00 §3.3 ning abort sharti **birorta marta ham
yuzaga kelmadi**.

**FAKT:** `/proc/vmstat oom_kill` butun sessiya boshidan oxirigacha **0**
(18:08:14Z da 0, 18:39:26Z da 0).

**FAKT:** `memory.events` da `high` o'sdi (631–1460), `max` esa **0** qoldi —
ya'ni throttling ishladi, `MemoryMax` ga yetilmadi. Bu `02` §3 ning fault
class 4 sharti: `host_mem_pressure` kill'siz bo'lishi kerak.

**FAKT:** `memory.current` cho'qqisi 200.6–210.3 MiB, ya'ni `memory.high`
(192 MiB) dan bir oz yuqori va `memory.max` (1024 MiB) dan ancha past —
`02` §3 ning «binar» mexanizmini tasdiqlaydi: `high` dan oshish ~0.99 stall
beradi, o'rta band yo'q.

**FAKT:** `/proc/uptime` har run'da monoton (orqaga qadam soni = 0, masalan
C4: birinchi 2288.40 → oxirgi 2318.40, span 30.00 s). VM to'xtamadi.

**CHEKLOV:** `/proc/uptime` monotonligi **distro restart'ini aniqlamaydi**
(07 §4.4: VM o'zgarmaydi) — buning uchun `/proc/1/stat` 22-maydoni ishlatildi
(§1.4).

### 6.1 FAKT — host PSI `user@` dan pasaytirilgan

C1 da `host` (`/proc/pressure/memory`) `full` tezligi 0.987–0.991 bo'lib
`user@` (0.962–0.966) dan **yuqori** chiqdi; run 5 da esa aks holat —
`host` 0.484–0.495, `user@` 0.971–0.992, ya'ni taxminan **yarmi**.

**TALQIN:** run 5 da `/init.scope` da 100% CPU iste'mol qilayotgan begona
`pytest` bor edi (§1.3). Tizim darajasidagi `full` **barcha** non-idle task
stall bo'lishini talab qiladi; stall qilmayotgan bitta qo'shimcha ishchi host
`full` ni ikki baravar pasaytiradi. `user@` esa o'sha yukni o'z ichiga
olmaydi (07 §4.7).

**Oqibati (TALQIN):** guard `user@1000.service` ni kuzatishi — host
`/proc/pressure` ni emas — bu muhitda **aniq to'g'ri qaror**. Host PSI begona
yuk bilan suyultiriladi va guard'ni jimgina kar qilib qo'yardi.

---

## 7. Kollateral zarar — `02` §6 bilan bir xil ro'yxat

### 7.1 Nima tekshirildi va nima topildi

```
Sentinel unit'lar (user@ ichida, revixlab.slice tashqarisida):
  revixguardcalsent-claude.service  -> 12 run'dan 12 tasida TIRIK
  revixguardcalsent-chrome.service  -> 12 run'dan 12 tasida TIRIK
  (skriptning o'z post-flight'i: "Claude PID 362 TIRIK", "Chrome PID 364 TIRIK")

systemd-oomd journal xabarlari            -> HECH QANDAY
  $ journalctl --since "2 min ago" -u systemd-oomd   -> har run'da bo'sh
  $ journalctl -b 0 | grep -Eic "oomd|out of memory|invoked oom"   -> 0

/proc/vmstat oom_kill                     -> 0 (sessiya boshi va oxiri)
revixlab.slice memory.events oom_kill     -> 0 (har run, har namuna)
revixlab.slice memory.events max          -> 0 (har run, har namuna)
memory.swap.current (lab)                 -> 0 (har run, har namuna)
SwapFree                                  -> 4194304 kB (o'zgarmadi)
Qoldiq failed unit'lar                    -> YO'Q (har run'dan keyin)
revixlab.slice tashqarisida o'lgan narsa  -> HECH NARSA
/proc/uptime monotonligi                  -> har run'da monoton
```

### 7.2 FAKT — `revixlab.slice` tashqarisida men o'ldirgan narsalar (ataylab)

Tozalik uchun: journal'da `status=9/KILL` bilan o'lgan
`revixguardcalsent-*` qatorlari bor. Ular **mening o'z teardown'im** —
run tugagandan keyin `cgroup.kill` ni o'z sentinel slice'imga yozganim.
Har run'ning *ichida* ular tirik qoldi va skriptning post-flight tekshiruvi
shuni qayd etdi.

### 7.3 FAKT — qoldiq: NOL (loyihaning o'z tekshiruvchisi bilan)

Yakuniy holat, 2026-10-02T18:39:26Z:

```
$ systemctl --user list-units 'revix*' --all --no-legend --plain
(bo'sh)
$ systemctl --user list-units --state=failed --no-legend --plain
(bo'sh)
$ find …/user@1000.service -maxdepth 3 -name 'revix*'
(bo'sh)
$ ls -d …/user@1000.service/*/
…/app.slice/   …/init.scope/                     <-- faqat tizimning o'zi
$ find /run/user/1000/systemd/user.control -maxdepth 3
find: '…/user.control': No such file or directory      <-- runtime drop-in YO'Q
$ ls -R $HOME/.config/systemd/user
ls: cannot access '…': No such file or directory       <-- PERSISTENT drop-in YO'Q
$ ls /run/user/1000/systemd/transient
ls: cannot access '…': No such file or directory
$ pgrep -af "revix|gc-sentinel|gc-watch"
(none)
$ python3 -c "import json; from revix import units; print(json.dumps(units.preflight()))"
{"clean": true, "problems": [], "units": [], "cgroups": [], "stale_drop_ins": [],
 "unit_patterns": ["revix-*"], "slices": ["revixlab.slice", "revixmon.slice"],
 "mono_us": 78775514}
```

`~/.config/systemd/user/` katalogi **umuman mavjud emas** — aynan
`set-property --runtime` ishlatilgani uchun (`02` §6 bilan bir xil natija).

### 7.4 🔴 FAKT — `guard-test.sh` ning o'z teardown'i `revixlab.slice` va `revixmon.slice` ni QOLDIRADI

Skript teardown'idan **keyingi** holat (run 3 ning `collateral-after.txt`,
mening qo'shimcha tozalashimdan oldin):

```
revix units: revixlab.slice loaded active active Slice /revixlab;
             revixmon.slice loaded active active Slice /revixmon;
revix cgroups: …/user@1000.service/revixmon.slice;
               …/user@1000.service/revixlab.slice;
```

Skript `systemctl --user stop revix-press.service revix-guard.service
revix-sampler.service` qiladi, lekin **slice'larning o'zini to'xtatmaydi**.
Bo'sh slice'lar `active` holatda qoladi.

**TALQIN:** `00-pilot-topologiya.md` §2 ning pre-flight qoidasi
(«`revix-*` unit yoki `revixlab.slice`/`revixmon.slice` cgroup'lari allaqachon
bor bo'lsa **ishga tushmaydi**») va `units.preflight()` ning default'lari
aynan shu cgroup'larni **bloklovchi** deb sanaydi. Demak `guard-test.sh` ni
ketma-ket ikki marta ishga tushirish ikkinchisini `units.preflight()` orqali
bloklaydi. Men har run'dan oldin va keyin
`systemctl --user stop revixlab.slice revixmon.slice` + `rmdir` qildim — bu
**mening operator qadamim**, skriptning qismi emas.

### 7.5 FAKT — begona agent mening qoldig'imni o'ziga tegishli deb o'qidi

Koordinator ma'lumoti: `agent/driver` ning bitta run'i
`test_units.py::test_zzz_hech_qanday_selftest_qoldigi_qolmadi` ni
`revixselftest.slice` qoldig'i sababli yiqitgan, va mening `revixlab.slice` imni
o'z qoldig'i deb hisobot qilgan. Men buni o'z tomonimdan ko'rmadim
(mening snapshot'larim faqat `revix*` nomlarini sanaydi); bu
`07` §4.5 ning («umumiy slice nom maydoni parallel agentlar uchun xavfli»)
yana bir ko'rinishi va §12 OQ-6 da qayd etilgan.

---

## 8. PID 1 restart: `NRestarts` va `InvocationID` — band 4 aldanishi mumkin

Koordinator so'ragan, hali hech kim o'lchamagan savol. **Restart
provokatsiya qilinmadi**: distro'ning o'z idle-stop mexanizmi (07 §4.4)
ishlatildi — barcha `wsl.exe` klientlari chiqarildi va 70 s kutildi, guest
yuklanmadi.

**ARM fazasi** (2026-10-02T18:33:17.301Z, `uptime 2836.59`,
`pid1_starttime_ticks = 282684`, PID 1 yoshi 9.75 s, user manager PID 238,
`CLK_TCK = 100`). Ikki unit o'z slice oilamda (`revixguardcalpid1.slice`):

```
$ systemd-run --user --slice=revixguardcalpid1.slice --unit=revixguardcalpid1-restarted \
    --collect -p Restart=on-failure -p RestartSec=1s -p RestartMaxDelaySec=4s \
    -p RestartSteps=2 -p StartLimitBurst=0 -p MemoryMax=32M -p MemorySwapMax=0 \
    -p TasksMax=16 /bin/sleep 600
$ systemctl --user kill -s SIGKILL revixguardcalpid1-restarted.service   # x2

--- revixguardcalpid1-restarted.service
Restart=on-failure  MainPID=303  NRestarts=2
InvocationID=3837d4bb1e784182972aae69c877b9fe
LoadState=loaded  ActiveState=active  SubState=running
--- revixguardcalpid1-virgin.service
Restart=no  MainPID=288  NRestarts=0
InvocationID=6bd09d60292446d98d1ecdabdcfbe01b
LoadState=loaded  ActiveState=active  SubState=running
```

Keyin barcha klientlar chiqdi:

```
PS> wsl.exe -l --running
kali-linux (Default)
PS> Start-Sleep -Seconds 70 ; wsl.exe -l --running
There are no running distributions.
```

**DISARM fazasi** (2026-10-02T18:34:57.339Z, yangi `wsl.exe` klienti):

```
uptime: 2936.63
pid1_starttime_ticks: 293478          <-- O'ZGARDI (282684 -> 293478)
pid1_etimes: 1                        <-- PID 1 yoshi 9.75 s -> 1.85 s, ORQAGA
boot_id: ca4e5bab-2cd8-43aa-8455-2a22ca6746f3     <-- O'ZGARMADI
user_mgr_pid: 241                     <-- 238 -> 241

--- revixguardcalpid1-restarted.service
Restart=no  MainPID=0  NRestarts=0        <-- 2 -> 0
InvocationID=                             <-- BO'SH
LoadState=not-found  ActiveState=inactive  SubState=dead
is-active: inactive rc=4
systemctl show rc: 0                      <-- rc=0, ya'ni "xato yo'q"
--- revixguardcalpid1-virgin.service
Restart=no  MainPID=0  NRestarts=0        <-- 0 -> 0  (O'ZGARMADI!)
InvocationID=                             <-- BO'SH
LoadState=not-found  ActiveState=inactive  SubState=dead
systemctl show rc: 0

$ pgrep -af "sleep 600"      -> (hech narsa; ikki jarayon ham YO'Q)
$ ls …/user@1000.service | grep -i revix
revixguardcalpid1.slice                   <-- bo'sh cgroup QOLDI
```

PID 1 restart lahzasi: `293478 / 100 = 2934.78 s` uptime, ya'ni ARM
o'qishidan **≈98.2 s keyin** — klient chiqishi va distro idle-stop bilan mos.

### FAKT — javoblar

| savol | javob |
|---|---|
| `NRestarts` PID 1 restart'idan keyin tiklanadimi? | **HA — 2 dan 0 ga**. Unit yo'qoladi, `systemctl show` default'larni `rc=0` bilan qaytaradi (07 §4.1 dead-unit tuzog'i) |
| `InvocationID` yangilanadimi? | **YO'Q — u BO'SH bo'ladi.** Yangi qiymatga almashmaydi, umuman yo'qoladi |
| `boot_id` buni ko'rsatadimi? | **YO'Q** — o'zgarmadi (07 OQ-5 ning tasdig'i) |
| Ishlaydigan detektor bormi? | **HA** — `/proc/1/stat` 22-maydoni (282684 → 293478); yon tasdiq: PID 1 yoshi orqaga ketadi, user manager PID o'zgaradi (238 → 241) |

### TALQIN — `PREREGISTRATION.md` §4 band 4 **aldanishi mumkin**

> §4 band 4: «`NRestarts` butun oyna davomida o'zgarmaydi»

`-virgin` unit'i aynan shu stsenariyni ko'rsatadi: `NRestarts` oynaning
**boshida 0**, **oxirida 0** — o'zgarmadi — holbuki oyna ichida PID 1 qayta
ishga tushdi, unit butunlay yo'q qilindi va uning jarayoni o'ldirildi.
**Band 4 qanoatlantiriladi va bo'lmagan recovery verified recovery deb
hisoblanadi — soxta VR.**

Band 3 (`InvocationID` o'zgarmasligi) teskari tomonga ishlaydi va
**konservativ**: yozilgan `3837d4bb…` ga qarshi bo'sh qiymat mos kelmaydi,
demak band 3 yiqiladi va trial VR deb hisoblanmaydi. **Lekin bu faqat
implementatsiya bo'sh qiymatni «mos kelmadi» deb qabul qilsa to'g'ri** —
agar u bo'sh qiymatni «o'qilmadi, o'tkazib yuboraman» deb talqin qilsa,
himoya yo'qoladi. `PREREGISTRATION.md` §8.4 ning
«`None` **jim deb hisoblanMAYDI**» qoidasi aynan shu holatga tegishli va
`InvocationID` uchun ham shunday majburlanishi kerak.

**CHEKLOV:** bu bitta o'lchov, bitta restart hodisasi. Men restart'ni
provokatsiya qilmadim va uning sababini (`instanceIdleTimeout` /
`vmIdleTimeout` yoki boshqa) **nomlab tasdiqlamadim** — faqat xatti-harakat
o'lchandi, 07 §4.4 bilan bir xil.

**CHEKLOV:** bu band 4 uchun **tuzatish taklif qilmaydi**. Qaror
`PREREGISTRATION.md` egasiniki (§12 OQ-5).

---

## 9. `revix/guard.py` chegaralari bo'yicha tavsiyalar — **implementatsiya QILINMAGAN**

Loyiha qoidasi: chegarani o'zgartiradigan kalibratsiya natijasi — ataylab
qabul qilinadigan, ma'lumotga asoslangan qaror; qolaversa `guard.py` 21 unit
test bilan qoplangan. Shuning uchun quyidagilar **tavsiya**, va men hech
qanday faylni o'zgartirmadim.

### 9.1 `user_full_rate2s_max = 0.98` — qiymatni saqlang, **asoslanishini tuzating**

**O'lchov:** `02` §1 bu raqamni «*qonuniy ramp burst'i 0.93–0.98 ga chiqadi*»
deb asoslaydi. Bu mashinada nazoratsiz ramp `user@` da **0.9992** ga,
`lab` da **0.9993** ga to'yinadi (§3.7). Ya'ni 0.98 endi «har qanday qonuniy
qiymatdan yuqori» emas — u to'yinish oralig'ining **ichida**.

Buning bevosita kuzatilgan oqibati: **aynan bir xil konfiguratsiyali ikki run
ikki xil sabab bilan trip qildi** —

| run | konfiguratsiya | trip sababi | `user@` plato |
|---|---|---|---|
| 3 | `MODE=ramp PRESS=8 RUNTIME=12 OBS=22` | `user_full_rate2s_runaway` (0.9836) | 0.9487 cho'qqi |
| C1 | **aynan o'sha** | `sustained_pressure` (15.000039 s) | 0.962–0.966 plato |

**Tavsiya:** `0.98` ni **o'zgartirmaslik**. Sabab: pilot dozasi (P2 ≤ 0.80)
bu chegaradan ancha past, demak to'g'ri dozalangan trial uchun 0.98 hamon
xavfsiz runaway tutuvchi. Lekin `02` §1 dagi asoslovchi jumla bu mashina
uchun **noto'g'ri** va tuzatilishi kerak. Chuqurroq xulosa:
**`rate2s` runaway tutuvchisi bu kernelda to'yinishni runaway'dan ajrata
olmaydi** (ikkisi ham ≈0.999), demak himoyani haqiqatan bajaradigan narsa —
**davomiylik kriteriyasi**. Bu `02` §1 ning dizayn qarorini yana bir marta
tasdiqlaydi.

### 9.2 `sustain_max_seconds = 15.0` va `sustain_rate_threshold = 0.35` — o'zgartirish KERAK EMAS

**O'lchov:** taymer bir poll tik (100 ms) aniqligida ishlaydi (§3.3), 5 ta
mustaqil trip'da. P1 bandi (0.20–0.35) chegarani ishga tushirmaydi, P2 bandi
(0.60–0.80) ishga tushiradi — bu loyihalangan xatti-harakat (§3.5).

**Tavsiya:** o'zgartirmaslik. Lekin `guard.py` ning izohi 15 s ni oomd ning
20 s sharti bilan asoslaydi (`"sustain_design": "oomd: avg10>=50%/20s ->
guard: rate2s>=35%/15s"` — bu `guard_start` yozuviga ham chiqadi). Bu
mashinada oomd yo'q, demak izoh **yangi asoslanishni** aytishi kerak:
15 s — `PREREGISTRATION.md` §9.4 2-invariantining majburlovchisi (§4.4).

### 9.3 `host_mem_available_min_kb = 1_500_000` — qiymat yetarli, asoslanish eskirgan

**O'lchov:** `MemAvailable` barcha run'larda 9 519 016 – 9 668 512 kB
oralig'ida qoldi; 1 GiB slice bilan chegaraga **yaqinlashilmadi**. Lekin
`00` §3.2 va `SECURITY.md` §4.3 zaxirani «15.4 GiB umumiy, ~7.6 GiB
available» deb hisoblaydi — bu mashinada `MemTotal` **9.71 GiB**.

**Tavsiya:** qiymatni o'zgartirmaslik (o'lchov asos bermaydi), lekin
`00` §3.2 va `SECURITY.md` §4.3 ning raqamlarini 07 §8 ga moslashtirish.
`MemoryMax=2G` ga o'tilganda (00 §1) zaxira 9.71 − 2 = 7.7 GiB bo'ladi, bu
1.5 GiB polidan ancha yuqori.

### 9.4 🔴 Eng muhim tavsiya — chegarada emas, generatorda

§5 ko'rsatgan topilma: epizod uzunligi majburlanmaydi. Bu `guard.py` ning
chegarasi bilan hal qilinmaydi va `experiment/pressure-cal` uchun kirish
shartidir. Mumkin yo'nalishlar (**men sinamadim, tavsiya ham emas, ro'yxat**):
`add()` chaqiruvlarini kichikroq bo'laklarga bo'lish; alohida thread'dan
qattiq deadline bilan `cgroup.kill` yozish; `TimeoutStopSec=` ni qisqartirib
`RuntimeMaxSec=` ning SIGKILL'ga o'tishini tezlashtirish; `memory.high` dan
oshishni ajratish tezligi bilan emas, `memory.high` ning o'zini burish bilan
boshqarish. Qaysi biri to'g'ri — o'lchov masalasi, bu hujjatda o'lchanmadi.

---

## 10. Avvalgi mashina bilan taqqoslash

| | `02-guard-kalibratsiyasi.md` (2026-09-29) | bu hujjat (2026-10-02) |
|---|---|---|
| kernel | 7.1.5 | **6.6.87.2-microsoft-standard-WSL2** |
| systemd | 261 | **257 (257.7-1)** |
| RAM | 15 GiB (≈7.6 GiB available) | **9.71 GiB** (≈9.5 GiB available) |
| swap | 5.5 GiB | **4.0 GiB** (ishlatilmadi: 0) |
| `systemd-oomd` | **faol**, `kill`, 50%, 20 s | **o'rnatilmagan** (07 §2) |
| `revixlab.slice` `MemoryMax` | 1G | **1G** (bir xil; 00 §1 esa 2G talab qiladi — §12 OQ-4) |
| `revixlab.slice` `MemoryHigh` | 192M | **192M** (bir xil) |
| cho'qqi `user@` / `lab` | 0.980 / 0.984 (nisbat 0.996) | **0.9664 / 0.9985** (C1), **0.9987 / 0.9990** (C4) |
| `user/lab` nisbat p50 | o'lchanmagan (faqat cho'qqilar berilgan) | **0.9963** (642 namuna, toza) |
| `some == full`? | ha (§1) | **ha**, barcha qatorlarda |
| qonuniy ramp to'yinishi | 0.93–0.98 | **0.9992** |
| `window_us` | 2000009, 2000000 | **2000017**, **2000029** |
| davomiylik trip aniqligi | `sustained_s=5.1` vs `limit 5.0` (Run D) | **5.000018 / 5.000022** (limit 5.0); **15.000039 … 15.100025** (limit 15.0) |
| calib v4 (0.30, 12 s) | trip yo'q, **erishilgan 0.311** | trip yo'q, **erishilgan 0.000** ⚠️ (§3.4) |
| PI nishonga chiqdimi? | ha (0.30 → 0.311) | **yo'q** — skript default'lari bilan doza 0 |
| epizod o'z vaqtida to'xtadimi? | hujjatda qayd etilmagan | **YO'Q** — 5 s so'rov → 16.3 s (§5) |
| `oom_kill` (global va lab) | 0 | **0** |
| `memory.swap.current` | 0 | **0** |
| kollateral zarar | yo'q | **yo'q** (sentinel'lar bilan — §2.3 CHEKLOV) |
| qoldiq | 0 unit, 0 cgroup, 0 persistent drop-in | **0 / 0 / 0** (`units.preflight()` clean=true) |
| `guard-test.sh` o'zgartirilmasdan ishladimi? | (shart qo'yilmagan) | **YO'Q** — ikki bloker (§2) |
| guest barqarorligi | doimiy desktop | **PID 1 restart, `boot_id` o'zgarmaydi** (§8) |

---

## 11. `PREREGISTRATION.md` §9.4 invariantlari

| # | invariant | qiymat | holat bu mashinada |
|---|---|---|---|
| 1 | `hold_s ≤ hold_cap_s` | 12 s | ⚠️ **majburlanmaydi** — generator o'z `--max-seconds` ini buzadi (§5). O'lchov: 5 s so'rov → 16.3 s |
| 2 | `hold_s + ramp_above_threshold_s ≤ guard_sustain_s` | 15 s | ⚠️ **majburlanmaydi**, 1-invariant buzilganidan kelib chiqib |

**`ramp_above_threshold_s` ning o'lchovi.** PREREG §9.4: «*`ramp_above_threshold_s`
pressure dosing kalibratsiyasidan olinadi, taxmin qilinmaydi*». Men uni
pilotning haqiqiy rejimida (`MODE=pi`) o'lchadim:

```
C2b:  RAMP above quiescence(0.05): 0 of 10 samples -> ramp_above_threshold_s = 0.000 s
```

**FAKT:** PI rejimining ramp fazasi quiescence chegarasidan (0.05) **hech
qachon oshmadi**, ya'ni `ramp_above_threshold_s = 0.000 s`. Bu `02` §3 ning
dizayn qarorini («baza `memory.high` dan bir oz PAST bo'lishi kerak, shunda
ramp **bepul** bo'ladi») tasdiqlaydi.

**CHEKLOV — bu raqamni invariantga qo'yib bo'lmaydi.** U doza **nol** bo'lgan
konfiguratsiyada o'lchandi (§3.4). Doza haqiqatan yetkazilganda baza
`memory.high` ga yaqinroq bo'lishi kerak va ramp o'sha paytda stall berishi
**ehtimoli bor**. Demak invariant 2 uchun ishlatiladigan
`ramp_above_threshold_s` **hali o'lchanmagan** va u `experiment/pressure-cal`
ning birinchi natijalaridan biri bo'lishi kerak.

Topshiriq so'ragan savolga javob: ramp hozircha quiescence chegarasidan
yuqorida **0 s** turadi, demak invariant 2 **qattiqlashmaydi** — lekin bu
faqat doza nol bo'lgani uchun, va shuning uchun bu raqam pilotga
**ko'chirilmaydi**.

---

## 12. Ochiq masalalar (frozen hujjatlar bilan ziddiyat — men hal qilmayman)

- **OQ-1.** `TESTING.md` §3 `scripts/guard-test.sh` ning `SUSTAIN_MAX`
  default'ini `13.0` deb yozadi va aniq `SUSTAIN_MAX=15.0` bilan ishga
  tushirishni tavsiya qiladi. Skript **endi 15.0** ni ishlatadi (commit
  `251f45f`; skriptning o'z chiqishi bilan tasdiqlangan). `TESTING.md` ning
  ogohligi va `ARCHITECTURE.md` §6 ning 2-ochiq masalasi **eskirgan**.
- **OQ-2.** `TESTING.md` §3 ning «Ikki vaqt chegarasi … guard'ning to'g'ri
  ishlashiga **tayanmaydi**» da'vosi bu mashinada **rad etildi** (§5).
  Bu xavfsizlik da'vosi, shuning uchun qayta yozilishi kerak.
- **OQ-3.** `02` §7 masala 1 (band desktop'da qayta o'lchash) **hali ochiq**.
  Bu hujjatdagi kontaminatsiya `user@` tashqarisida (`/init.scope`) bo'lgani
  uchun kutilgan samarani ko'rsatmadi (§4.3). `user@` ichida haqiqiy
  non-idle yuk bilan o'lchash **bajarilmadi, sabab: bu mashinada
  `user@1000.service` ichida desktop ilovasi yo'q va sun'iy non-idle yuk
  qo'shish guard testini o'zini buzardi.**
- **OQ-4.** `MemoryHigh=192M` `MemoryMax=1G` ostida kalibrlangan (`02`
  sarlavhasi) va men ham shu juftlikni ishlatdim; `00-pilot-topologiya.md`
  §1 va §2 esa `MemoryMax=2G` ni muzlatadi. Dial **ko'chirilmaydi** va 2G da
  qaytadan chiqarilishi kerak. Mening barcha raqamlarim `MemoryMax=1G`
  uchun.
- **OQ-5.** `PREREGISTRATION.md` §4 band 4 (`NRestarts` o'zgarmaydi) PID 1
  restart'ida **aldanishi mumkin** (§8). Band 3 konservativ, lekin faqat bo'sh
  `InvocationID` «mos kelmadi» deb qabul qilinsa. Qaror §4 egasiniki.
- **OQ-6.** `guard-test.sh` ning teardown'i `revixlab.slice` va
  `revixmon.slice` ni `active` holatda qoldiradi (§7.4), bu esa
  `units.preflight()` va 00 §2 bo'yicha keyingi run'ni **bloklaydi**.
- **OQ-7.** `02` §5 ning to'rt run'i `TESTING.md` §3 protsedurasidan
  **qayta ishlab chiqarilmaydi**, chunki `revixlab.slice` ga property
  qo'yish qadami hech qayerda yozilmagan (§2.2).
- **OQ-8.** `02` §8 ning «P1/P2 bandlari erishiladigan» da'vosi 0.311 ga
  (P1 bandi) asoslangan; P2 (0.60–0.80) **nishon sifatida hali hech qachon
  ko'rsatilmagan**. Bu hujjat bandga tegadigan birinchi raqamlarni beradi
  (§3.6), lekin ushlab turishni emas. Agar P2 erishilmasa, §10.1 ning uch
  darajali Cochran–Armitage testi ikki darajaga qisqaradi.
- **OQ-10.** `guard.py` birinchi trip'dan keyin boshqa `cgroup.kill`
  qilmaydi (§17), lekin `00` §3.1(b) va `SECURITY.md` §2(b) bitta guard
  jarayonini butun kampaniyaga mo'ljallaydi. Bu xavfsizlik xususiyatining
  buzilishi; tuzatish `guard.py` egasining qarori.
- **OQ-11.** `PREREGISTRATION.md` §9.2 ning (i) «`TimeoutStartSec` oshib
  ketdi» mexanizmi bu mashinada pressure ostida **44% chastotada** yuz
  beradi (§15.2) va `driver.py` ning `TimeoutStartSec = 10 s` default'i
  `t_start` ning o'lchangan p99 (9.86 s) ga **juda yaqin**. Demak arm A ning
  o'zi pressure ostida `Result=timeout` beradi va bu VR ta'rifiga
  to'g'ridan-to'g'ri ta'sir qiladi.
- **OQ-12.** §11 ning fail-slow chegarasi `0.20 × RMST(P0)` da `RMST(P0)`
  **aynan qaysi kattalik**: `D_probe` ning o'zimi (men o'lchagan, §16 →
  chegara 0.097 s ≈ 1 × P, qaror kerak) yoki `W_stab` ni o'z ichiga olgan
  to'liq time-to-VR (→ chegara ≈1.7 s ≥ 5P, qaror kerak emas)? Javob §18 ning
  xulosasini **teskariga o'zgartiradi**. Men hal qilmayman.
- **OQ-9.** `guard.py` va `SECURITY.md` ning butun motivatsiyasi
  `systemd-oomd` ustiga qurilgan, u esa bu mashinada **yo'q**. Guard majburiy
  bo'lib qoladi (§4.4), lekin modul docstring'i va `SECURITY.md` §1 «bu xavf
  gipoteza emas, tasdiqlangan» deb yozadi — bu **bu mashinada noto'g'ri**.
  07 §9 OQ-1 bilan bir xil masala.

---

## 13. `PREREGISTRATION.md` ga ta'siri

**Hech bir ta'rif, endpoint, metrika yoki statistik test o'zgarmadi.** Men
pre-registration'ni o'zgartirmadim va o'zgartirishni tavsiya ham qilmayman.

**Tasdiqlandi:** §7 ning «`total` asosiy o'lchov, avgN ikkilamchi» qarori —
davomiylik taymeri `total` deltasidan hisoblanadi va bir poll tik aniqligida
ishlaydi (§3.3); `avgN` esa bu run'larda 47.5–58.0 gacha **o'z-o'zidan
sudralib** keldi (C2 ning idle pre-read'i) va chegara qarori uchun yaroqsiz
bo'lishini yana ko'rsatdi.

**Tasdiqlandi:** §7 ning PSI trigger ishlatmaslik qarori — 07 §7.4 bu
mashinada ham oyna 2 s karrasi bo'lishi shartini o'lchagan.

**Ogohlantirish (yangi, §9.4 ga):** ikki v1.3 xavfsizlik invarianti
**hozirda majburlanmaydi** (§11). Bu ta'rif o'zgarishi emas, **amalga
oshirish bo'shlig'i**, lekin u pilotni to'xtatadi.

**Ogohlantirish (yangi, §4 ga):** band 4 soxta VR berishi mumkin (§8, OQ-5).

**Ogohlantirish (yangi, §9.3 ga):** P2 bandi nishon sifatida hali
ko'rsatilmagan (OQ-8).

**Yangi o'lchovlar, §17/§18 qarorlari uchun kirish ma'lumoti:** `t_start`
(§15) va `D_probe` proxy (§16). Ular ta'rifni o'zgartirmaydi, lekin ikki
muzlatilgan-qiymat qarorining **zarurligini** aniqlaydi (§14.5).

**Ogohlantirish (yangi, §4 bandi 1 ga):** `t_start` pressure ostida
p90 = 4.81 s, ya'ni `t_up − t_inject ≤ 1 s` cheklovi **bajarilmaydi**, va
14 urinishdan 6 tasi `TimeoutStartSec=10s` ichida umuman start bo'lmadi
(§15.2, OQ-11).

---

## 14. VERDIKT — pressure gate o'tdimi?

`00-pilot-topologiya.md` §6 ning 3-qadami aynan shuni talab qiladi:

> «**GUARD TESTI** — SUT'siz, injeksiyasiz, sintetik pressure manbasiga qarshi.
> Guard slice'ni belgilangan vaqt ichida o'ldirishi TASDIQLANADI.»

### 14.1 Guard'ning o'zi: ✅ **O'TDI**

Men guard'ning trip qilishini **ko'rdim** va o'ldirishini **tasdiqladim** —
**8 marta**, shundan **5 tasi toza scope'da**, ikki xil trip yo'li bo'yicha:

- `sustained_pressure` (asosiy, davomiylik) — **6 marta** (run 5, run 7, C1,
  C3, C4, C5), `sustained_s` limitdan bir poll tik ichida (5.000018,
  5.000022, 15.000039, 15.099918, 15.099994, 15.100025);
- `user_full_rate2s_runaway` (oniy tutuvchi) — **2 marta** (run 3, run 6),
  oyna aynan 2000017 va 2000029 µs;
- har holatda `kill_ok: true`, generator `status=9/KILL`
  (`Failed with result 'signal'`), `memory.events oom_kill = 0`,
  `/proc/vmstat oom_kill = 0` → **guard o'ldirdi, kernel emas**;
- guard exit kodi shartnomaga mos (trip = 1, trip yo'q = 0);
- fail-closed xatti-harakati buzilmadi;
- containment to'liq: `memory.swap.current` hamma joyda 0, `events.max` = 0;
- kollateral zarar **yo'q**, qoldiq **nol** (`units.preflight()` clean=true).

`user@ ≈ lab` topilmasi ham saqlandi (`user/lab` p50 = 0.9963), demak
guard'ning davomiylik dizayni **bu mashinada ham to'g'ri** — garchi uning
*sababi* o'zgargan bo'lsa ham (oomd yo'q; 15 s endi §9.4 invariantining
majburlovchisi, §4.4).

### 14.2 `experiment/pressure-cal` boshlanishi mumkinmi? ✅ **HA — uchta majburiy kirish sharti bilan**

4-qadam 3-qadam o'tgani uchun boshlanishi mumkin. Lekin u quyidagilarni
**o'z ishining birinchi qismi** sifatida hal qilishi shart, chunki ularsiz
dosing kalibratsiyasi ham bajarilmaydi:

1. **`scripts/guard-test.sh` bu mashinada o'zgartirilmasdan ishga
   tushmaydi** (§2.1 `pgrep`+`pipefail`; §2.2 `memory.high` qo'yilmaydi).
   Mening run'larim bu ikkisini **tashqi operator qadami** bilan aylanib
   o'tdi; bu vaqtinchalik yechim, tuzatish emas.
2. **Doza skript default'lari bilan yetkazilmaydi** — `STEP_MB=16` da
   `base = 160 MiB` va `memory.current` 185.3 MiB `memory.high` = 192 MiB dan
   past qoladi, erishilgan tezlik **0.000** (§3.4).
3. **`MemoryHigh=192M` `MemoryMax=1G` uchun kalibrlangan**, `00` §1 esa 2G ni
   muzlatadi (OQ-4). Dial 2G da qaytadan chiqarilishi kerak.

### 14.3 Pilot (120 trial) ishga tushirilishi mumkinmi? ❌ **HOZIR MUMKIN EMAS**

Bu **salbiy natija** va u yashirilmaydi. Sababi bitta va u guard chegarasi
emas:

> **Pressure epizodining uzunligi majburlanmaydi.** O'lchov: `--max-seconds 5`
> va `RuntimeMaxSec=7s` berilgan epizod `lab` scope'da 0.35 chegarasidan
> yuqorida **16.3 s** turdi va uni to'xtatgan narsa guard'ning `cgroup.kill`i
> bo'ldi (§5, C5).

Shundan kelib chiqib `PREREGISTRATION.md` §9.4 ning ikki v1.3 xavfsizlik
invarianti ham **hozirda majburlanmaydi** (§11), va P2 trial'i guard
tomonidan o'ldiriladi — ya'ni `aborted_guard` dispozitsiyasi istisno
emas, **qoida** bo'lib qoladi.

Diqqat: bu **guard'ning nosozligi emas**. Guard aynan loyihalanganidek
ishlaydi va aynan shu holatni tutish uchun bor. Nosozlik generator
tomonida, va `TESTING.md` §3 ning «ikki vaqt chegarasi guard'ga tayanmaydi»
da'vosi bu mashinada rad etilgan (OQ-2) — ya'ni hozir **butun epizod
chegarasi guard'ning to'g'ri ishlashiga tayanadi**, bu esa qatlamli
himoyaning (`SECURITY.md` §2) buzilishi.

### 14.4 Qisqa qilib

| savol | javob |
|---|---|
| Guard testi (00 §6 qadam 3) o'tdimi? | ✅ **HA** |
| Guard majburiy va fail-closed bo'lib qoladimi? | ✅ **HA** — oomd yo'qolgani xavfni kamaytirmadi; xotira zaxirasi 15 GiB dan 9.71 GiB ga tushdi |
| `experiment/pressure-cal` boshlanishi mumkinmi? | ✅ **HA**, §14.2 ning uch sharti bilan |
| Pilot ishga tushirilishi mumkinmi? | ❌ **YO'Q** — §5 ning epizod chegarasi muammosi yopilmaguncha |
| Gate'ni kim yopadi? | `experiment/pressure-cal` — §14.2 (1)–(3) va §5; keyin bu hujjatga qo'shimcha |

### 14.5 Loyiha egasiga yo'naltirilgan ikki qaror (mening o'lchovlarim bilan)

| qaror | hal qiluvchi o'lchov | natija |
|---|---|---|
| `preregistration/v1.6` §17.5 (`t_up` oynasi) | `t_start` p90 | `P0` da **0.0497 s** → qaror kerak emas; **pressure ostida 4.8133 s va 43% start muvaffaqiyatsizligi** → **qaror KERAK** (§15) |
| `preregistration/v1.7` §18.6 (fail-slow chegarasi) | `D_probe` `P0` | `0.20 × mean` = **0.0967 s** = **0.97 × P** < 5P → **qaror KERAK**, lekin OQ-12 ga bog'liq (§16) |

Ikkinchi qaror uchun diqqat: men bergan raqam `D_probe` ning o'zidan
chiqadi. Agar §11 ning `RMST(P0)` i `W_stab` ni o'z ichiga olsa, chegara
≈1.7 s bo'lib `5P` dan oshadi va qaror kerak bo'lmaydi — shuning uchun
§18 ni hal qilishdan oldin OQ-12 javob talab qiladi.

---

## 15. `t_start` — SUT ning `READY=1` ga chiqish vaqti, band bo'yicha

Koordinator so'ragan va `preregistration/v1.6` §17 ning qarorini hal qiladigan
o'lchov. Ta'rif: `t_start` = SUT unit'ining
`ActiveEnterTimestampMonotonic − InactiveExitTimestampMonotonic`, ya'ni start
job boshlanishidan `READY=1` systemd tomonidan qabul qilinishigacha. Mustaqil
o'zaro tekshiruv: SUT ning o'z `INFO` javobidagi
`uptime_us = mono_us() − g_start_us`.

SUT ext4 nusxada qurildi (`make -C revix all`, `cc (Debian 14.3.0-5) 14.3.0`,
`-O2 -Wall -Wextra -Werror -std=c11 -pthread`, 28328 bayt). Har start
`systemd-run --user --slice=revixlab.slice` orqali, `Type=notify`,
`NotifyAccess=main`, `MemoryMax=256M`, `MemorySwapMax=0`, `TasksMax=64`,
`TimeoutStartSec=10s`, `StartLimitBurst=0`, `Restart=no`. Guard **birinchi**
ishga tushdi va **oxirgi** to'xtadi (`--max-seconds 900`).

### 15.1 FAKT — band `P0` (pressure YO'Q), toza scope, n = 30

```
boot_id (ikki chekkada ham) : ad70d5bb-67c7-4a01-b293-5105aed9c855
pid1_starttime_ticks        : 89 -> 89            (o'zgarmadi)
uptime                      : 3.07 -> 47.51 s
interference                : [] -> []            (yo'q)
vmstat oom_kill             : 0 -> 0
guard                       : tripped=false, iterations=442, elapsed 44.2 s
```

| o'lchov | n | min | **p50** | **p90** | **p99** | max |
|---|---|---|---|---|---|---|
| **`t_start`** (systemd timestamp'lari) | **30** | 0.0240 | **0.0394** | **0.0497** | **0.0643** | 0.0643 |
| SUT `INFO uptime_us` (o'zaro tekshiruv) | 30 | 0.0311 | 0.0331 | 0.0374 | 0.0498 | 0.0498 |
| `systemd-run` wall clock | 30 | 0.0380 | 0.0525 | 0.0666 | 0.0764 | 0.0764 |

Barcha 30 urinish `rc=0`, `ActiveState=active`, `SubState=running`,
`Result=success`, har birida boshqa `InvocationID`.

**§17 budjetlari:**

| budjet | shart | natija |
|---|---|---|
| `t_start ≤ 0.8 s` (harakat systemd signaliga ulangan) | **30/30 = 100%** | ✅ p90 = **0.0497 s**, 16× zaxira |
| `t_start ≤ 0.5 s` (harakat `F_probe` ga ulangan, `+D_f = 300 ms`) | **30/30 = 100%** | ✅ 10× zaxira |

> **TALQIN — `P0` da §17 ning nuqsoni amalda zararsiz.** `p90(t_start)` =
> 0.0497 s, budjetdan 16 marta kichik. Agar pilot faqat `P0` da ishlaganda,
> `agent/research` topgan `t_up − t_inject ≤ 1 s` cheklovi qiyinchiliksiz
> bajarilardi.

### 15.2 🔴 FAKT — pressure ostida, n = 14 urinish (⚠️ KONTAMINATSIYALANGAN)

```
boot_id (ikki chekkada ham) : ad70d5bb-67c7-4a01-b293-5105aed9c855
pid1_starttime_ticks        : 15876 -> 15876      (o'zgarmadi)
uptime                      : 165.28 -> 515.39 s
interference (boshida)      : pytest tests/unit/test_validate.py + tests/integration
interference (oxirida)      : []
vmstat oom_kill             : 0 -> 0
lab memory.swap.current     : 0 (har o'qishda)
```

4 epizod × 4 start. Tasniflash qoidasi: namuna **PRESSURED** deb sanaladi
faqat `lab` slice'ning `full total=` hisoblagichi shu namunaning pre-o'qishi
va keyingi namunaning pre-o'qishi orasida **haqiqatan oshgan** bo'lsa. Oshmagan
bo'lsa, `avg10` qancha baland ko'rsatsa ham stall yig'ilmagan — bu
`PREREGISTRATION.md` §7 ning `total` ni birlamchi qilish sababining aynan
o'zi (`avg10` sekin pasayadi va bu yerda yolg'on gapiradi).

| tag | rc | holat | `t_start` (s) | wall (s) | pre `full total=` | pre `full avg10` | pressured? |
|---|---|---|---|---|---|---|---|
| PRESS1\|1 | 0 | active | **1.8672** | 1.880 | 2163081 | 21.29 | ha |
| PRESS1\|2 | 1 | **inactive/dead** | **START BO'LMADI** | 2.441 | 4663380 | 33.56 | ha |
| PRESS1\|3 | 0 | active | 0.0425 | 0.055 | 7043019 | 43.60 | **yo'q** |
| PRESS1\|4 | 0 | active | 0.0385 | 0.052 | 7043019 | 43.60 | **yo'q** |
| PRESS2\|1 | 0 | active | **4.3175** | 4.334 | 9390134 | 27.87 | ha |
| PRESS2\|2 | 0 | active | **9.8586** | 9.872 | 13524581 | 54.96 | ha |
| PRESS2\|3 | 1 | **inactive/dead** | **START BO'LMADI** | 10.231 | 24170454 | 82.24 | ha |
| PRESS2\|4 | 1 | **inactive/dead** | **START BO'LMADI** | 58.628 | 33946333 | 89.08 | ha |
| PRESS3\|1 | 0 | active | **2.8207** | 2.833 | 107173323 | 42.76 | ha |
| PRESS3\|2 | 0 | active | **2.8515** | 2.864 | 110466697 | 60.96 | ha |
| PRESS3\|3 | 1 | **inactive/dead** | **START BO'LMADI** | 14.350 | 113876253 | 71.45 | ha |
| PRESS3\|4 | 1 | **inactive/dead** | **START BO'LMADI** | 78.591 | 127673955 | 90.67 | ha |
| PRESS4\|1 | 0 | active | **1.9283** | 1.941 | 206135605 | 44.54 | ha |
| PRESS4\|2 | 1 | **inactive/dead** | **START BO'LMADI** | 13.241 | 208897538 | 57.81 | ha |
| PRESS4\|3 | 0 | active | **4.8133** | 4.825 | 221721248 | 83.35 | ha |
| PRESS4\|4 | 0 | active | **3.6492** | 3.661 | 226779409 | 90.01 | ha |

| to'plam | urinish | start bo'ldi | **start BO'LMADI** | min | **p50** | **p90** | **p99** | max | `≤0.8 s` |
|---|---|---|---|---|---|---|---|---|---|
| **PRESSURED** | **14** | 8 | **6 (43%)** | 1.8672 | **3.6492** | **4.8133** | **9.8586** | 9.8586 | **0/8** |
| UNPRESSURED (epizod ichida, bosim to'xtagach) | 2 | 2 | 0 | 0.0385 | 0.0385 | 0.0425 | 0.0425 | 0.0425 | 2/2 |

Pressured, start bo'lgan namunalar uchun SUT ning **o'z** `INFO uptime_us`:
min 0.3174, p50 0.5306, max 0.9266 s.

**TALQIN — ikki xulosa:**

1. **§17 ning nuqsoni pressure ostida amalda ZARARLI.** `p90(t_start)` =
   **4.8133 s**, budjetdan (`0.8 s`) **6 baravar** katta; 8 ta start'dan
   **birortasi ham** 0.8 s ga sig'madi. Qolaversa 14 urinishdan **6 tasi
   (43%) umuman start bo'lmadi** — `ActiveState=inactive`, `SubState=dead`,
   `InvocationID` bo'sh. Ya'ni `agent/research` ning §17 topilmasi
   **gipotetik emas**: §9.2 ning oldindan aytilgan «`TimeoutStartSec` oshib
   ketdi» mexanizmi bu mashinada haqiqatan ishga tushadi.
2. **Kechikish SUT ning ichida EMAS.** SUT ning o'z `uptime_us` i 0.32–0.93 s,
   `t_start` esa 1.87–9.86 s — ya'ni vaqtning katta qismi SUT `main()` da
   `g_start_us` ni olishidan **oldin** ketadi: `execve`, dinamik yuklash va
   birinchi sahifa fault'lari reclaim throttling ostida. Bu
   `PREREGISTRATION.md` §9.2 ning (i) va (iv) mexanizmlarini qo'llab-quvvatlaydi.

**CHEKLOV — bu o'lchov kontaminatsiyalangan.** Boshida begona agentning
`pytest tests/unit/test_validate.py` va `pytest tests/integration` run'lari
ishlayotgan edi (oxirida yo'q). Begona CPU yuki `t_start` ni **oshiradi**,
demak raqamlar **yuqori chegara** sifatida o'qilishi kerak. Lekin:
- 43% start muvaffaqiyatsizligi CPU yuki bilan tushuntirilmaydi — u
  `TimeoutStartSec=10s` ning oshib ketishi va reclaim throttling natijasi;
- o'sha **bir xil sessiyada** `P0` o'lchovi **toza** edi va 0.04 s berdi,
  ya'ni ikki band orasidagi ~100× farq kontaminatsiyadan kelib chiqmaydi.

**Toza qayta o'lchov tavsiya etiladi** va u bajarilmadi, sabab: koordinator
guest'ni faqat keyinchalik tozaladi va men ustuvorlikni hujjatni commit
qilishga berdim.

**CHEKLOV — epizod 1 dagi bitta muvaffaqiyatsizlik guard'ga tegishli.**
Guard shu run'da **bir marta** `kill_subtree` qildi (mono 174649189,
`user_full_rate2s_runaway`, `rate=0.9805152380952381`, `limit=0.98`,
`window_us=2100000`, `kill_ok=True`). PRESS1\|2 ning
muvaffaqiyatsizligi shu kill oynasiga to'g'ri keladi, demak u **guard
tomonidan o'ldirilgan** bo'lishi ehtimoli bor va pressure sababli deb
sanalmasligi kerak. Qolgan **5 ta** muvaffaqiyatsizlik (PRESS2\|3,
PRESS2\|4, PRESS3\|3, PRESS3\|4, PRESS4\|2) guard'ning hech qanday kill'i
bo'lmagan paytda yuz berdi (§17 — guard birinchi trip'dan keyin boshqa
o'ldirmaydi), demak ular **sof pressure natijasi**.

### 15.3 Qisqa javob

| band | n | p50 | **p90** | p99 | `p90 ≤ 0.8 s`? | §17 qarori kerakmi? |
|---|---|---|---|---|---|---|
| `P0` (toza) | 30 | 0.0394 | **0.0497** | 0.0643 | ✅ **HA** | **yo'q** |
| pressured (kontaminatsiyalangan) | 8 (+6 start bo'lmadi) | 3.6492 | **4.8133** | 9.8586 | ❌ **YO'Q** | **HA, KERAK** |

---

## 16. `D_probe` — band `P0`, proxy o'lchov

`preregistration/v1.7` §18 ning qarorini hal qiladigan o'lchov.

**Men nimani o'lchadim (va nimani o'lchamadim).** `PREREGISTRATION.md` §6.1
ning `D_probe` i «*oxirgi contract-passing probe'dan to VR shartini
qanoatlantiruvchi oynaning birinchi probe'igacha*». Men to'liq trial
o'tkazmadim (SUT + fault + arm + `W_stab` oynasi + VR qarori), demak bu
**`D_probe` ning o'zi emas**. Men o'lchagan narsa — koordinator taklif qilgan
eng halol o'rnini bosuvchi:

> **oxirgi contract-passing probe'dan restartdan keyingi birinchi
> contract-passing probe'gacha**, 10 Hz probe kadensida.

Ya'ni `W_stab` oynasining tasdiqlash sharti **kiritilmagan**. Shuning uchun
quyidagi raqam `D_probe` ning **pastki chegarasi**: haqiqiy `D_probe`
(VR shartini talab qiladigan) bundan kichik bo'lishi mumkin emas.

**Asbob.** Loyihaning o'z prober'i (`revix/prober.py`), 10 Hz,
`revixmon.slice` da, `--target sut=<socket>`. SUT **arm A** sifatida
sozlangan: `Type=notify`, `Restart=on-failure`, `RestartSec=100ms`,
`StartLimitBurst=0`, `TimeoutStartSec=10s` (jonli unit'dan tasdiqlangan:
`RestartUSec=100ms`). Fault — protokolning o'zi orqali:
`FAULT exit code=1`, 12 marta, har 3 s da. Har injeksiya `OK armed=exit`
javobini oldi va `NRestarts` 1 → 12 gacha ketma-ket o'sdi.

### 16.1 FAKT

```
boot_id (ikki chekkada ham) : ad70d5bb-67c7-4a01-b293-5105aed9c855
pid1_starttime_ticks        : 89 -> 89            (o'zgarmadi)
interference                : [] -> []
guard                       : tripped=false (bu fazada hech qanday trip yo'q)
probe namunalari            : 385
outcome taqsimoti           : {'ok': 339, 'conn_refused': 46}
clause_failed taqsimoti     : {'a_conn': 46}
ko'rilgan alohida invocation_id : 13   (= 1 boshlang'ich + 12 restart)
aniqlangan uzilish epizodlari   : 12   (= injeksiyalar soni)
```

| o'lchov | n | min | **p50** | **p90** | **p99** | max |
|---|---|---|---|---|---|---|
| `D_probe` proxy (s) | **12** | 0.400 | **0.500** | **0.500** | **0.500** | 0.500 |
| probe periodlarida (`P` = 100 ms) | 12 | 4.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| epizoddagi contract-buzgan probe soni | 12 | 3 | 4 | — | — | 4 |

Barcha 12 epizod: `0.500, 0.500, 0.500, 0.500, 0.400, 0.500, 0.500, 0.400,
0.500, 0.500, 0.500, 0.500` s. Har bir buzilish `conn_refused` / band `a_conn`
— ya'ni socket yo'q bo'lgan vaqt, va boshqa hech qanday contract bandi
buzilmadi (`b_response`, `c_progress` — **nol marta**).

**TALQIN — qiymat o'z komponentlaridan tushuntiriladi:**
`RestartSec` (0.100) + `t_start` (p50 0.039, §15.1) + systemd job overhead
≈ 0.15–0.20 s, ustiga probe gridining ±`P` kvantlashi va har chekkada `+P/2`
bias (§6.1 ning o'z ogohligi) → 0.4–0.5 s. Ya'ni **o'lchangan qiymatning
yarmidan ko'pi asbobning kvantlashi**, xizmatning haqiqiy uzilishi emas.

### 16.2 🔴 §18 ning qarori KERAK

`agent/research` ning qoidasi: agar `thr = 0.20 × RMST(P0)` taxminan `5 × P`
(≈ 500 ms) yoki undan katta bo'lsa, cheklov amalda zararsiz.

| referens | qiymat | `thr = 0.20 × referens` | `P` birligida | `≥ 5P` ? |
|---|---|---|---|---|
| `mean(D_probe proxy)` | 0.4833 s | **0.0967 s** | **0.97 × P** | ❌ **YO'Q** |
| `p50(D_probe proxy)` | 0.500 s | **0.1000 s** | **1.00 × P** | ❌ **YO'Q** |
| `p90(D_probe proxy)` | 0.500 s | **0.1000 s** | **1.00 × P** | ❌ **YO'Q** |

**Chegara aynan bitta probe periodiga tushadi.** Bu `agent/research` ning
80–220 ms oralig'idagi bahosini o'lchov bilan tasdiqlaydi (mening
o'lchovim 97–100 ms). Demak §11 ning fail-slow limbi `P0` da aynan
«asbobning kvantlash poli» da turadi: `>0.0967 s` kechikish «fail-slow» deb
belgilanishi uchun **bitta probe periodi** yetarli, ya'ni test
`PREREGISTRATION.md` §6.1 ning o'z `±P` xatosidan farqlanmaydi.

> **Xulosa: §18.6 ning qarori ZARUR** va u pilotdan oldin qabul qilinishi
> kerak. Men to'rt variantdan birini tanlamayman — har biri muzlatilgan
> ta'rifga tegadi.

**CHEKLOV — `RMST(P0)` mening proxy'im EMAS.** §10.2 ning `RMST` i
time-to-VR ning Kaplan–Meier egri chizig'idan `τ` gorizontigacha
hisoblanadi, va time-to-VR ta'rifi `W_stab` tasdiqlash oynasini o'z ichiga
olsa (`W_stab_pilot = 8 s`), haqiqiy `RMST(P0)` ≈ 8.5 s bo'lardi va
`thr ≈ 1.7 s ≥ 5P` — ya'ni **xulosa teskari bo'lardi**. Demak §18 ning
javobi **§11 ning `RMST(P0)` da aynan qaysi kattalikni nazarda tutishiga
bog'liq**, va bu hujjat buni hal qilmaydi: u frozen matn egasining savoli
(§12 OQ-12). Men bergan raqam — `D_probe` ning o'zi, ya'ni
`agent/research` ning derivatsiyasida ishlatilgan kattalik.

---

## 17. 🔴 Guard birinchi trip'dan keyin boshqa O'LDIRMAYDI

Bu §15.2 ning uzun run'i (350 s, 4 pressure epizodi, bitta guard jarayoni)
ustida kuzatilgan va `guard-test.sh` ning qisqa run'larida **ko'rinmaydi**,
chunki u har run'da yangi guard jarayonini yaratadi.

**FAKT** (`presspass/guard.jsonl`, 350 s, guard `--max-seconds 900`):

```
$ grep -c guard_event guard.jsonl                 -> 3257
$ grep -c '"action": "kill_subtree"'  (hisoblangan) -> 1
$ grep -c '"action": "already_tripped"'             -> 3256
$ ls -l guard.jsonl                               -> 1751702 bayt (1.67 MiB)
guard_stop: tripped=true iterations=3499 elapsed_s=349.900166559
```

Yagona haqiqiy kill: mono 174649189, `user_full_rate2s_runaway`,
`rate=0.9805152380952381`, `kill_ok=True`. Shundan keyin 2, 3 va 4-epizodlarda
pressure `full avg10` 95.73 ga chiqdi (`user_full_avg10_runaway` va
`user_some_avg10_runaway` ham qayd etildi), lekin **birorta kill bo'lmadi**.

**TALQIN — sabab kodda ochiq:** `Guard.trip()` da

```python
first = not self.tripped
self.tripped = True
if first:
    killed = cg.kill_subtree(self.lab_cgroup)
```

`self.tripped` hech qachon tiklanmaydi, demak `first` bir martadan keyin
doimo `False` va `cg.kill_subtree` **boshqa hech qachon chaqirilmaydi**.
Modul izohi buni qisman tan oladi («Guard TO'XTAMAYDI: keyingi buzilishlarni
ham kuzatishda davom etadi»), lekin *kuzatish* bilan *o'ldirish* orasidagi
farq hujjatlashtirilmagan.

**Nega bu muhim:** `00-pilot-topologiya.md` §3.1(b) va `SECURITY.md` §2(b)
guard'ni «**birinchi start, oxirgi stop**» deb belgilaydi — ya'ni **bitta**
guard jarayoni butun 120-trial kampaniyasini (≈2.5 soat) qoplaydi. Shu
dizaynda **birinchi `aborted_guard` trial'idan keyin guard qolgan 119
trial uchun himoyani to'xtatadi.** `guard-test.sh` da bu ko'rinmaydi, chunki
u har run'da yangi guard yaratadi.

**Ikkinchi oqibat — log o'sishi chegaralanmagan:** 350 s da 1.67 MiB va
3256 ortiqcha yozuv. 2.5 soatlik kampaniyada bu ≈43 MiB va ≈84 000 yozuv
bo'lardi, va `04-driver-va-analiz-shartnomasi.md` ning stream'lariga
qo'shilardi.

**Tavsiya (implementatsiya QILINMAGAN):** `trip()` kill'ni har trip'da
takrorlasin (`cgroup.kill` idempotent va arzon), yoki trial chegarasida
`tripped` tiklansin; va takroriy `already_tripped` yozuvlari throttle
qilinsin. Qaysi biri to'g'ri — `guard.py` egasining qarori; bu 21 unit test
bilan qoplangan fayl.

---

## 18. Aloqador hujjatlar

- [`02-guard-kalibratsiyasi.md`](02-guard-kalibratsiyasi.md) — avvalgi mashinaning kalibratsiyasi; §1, §2, §3, §5, §6, §7 bu hujjatning shabloni
- [`00-pilot-topologiya.md`](00-pilot-topologiya.md) — §1 topologiya, §2 cheklash, §3 xavf tahlili, §4 privilegiya, §6 qurilish tartibi
- [`07-wsl-muhit-tekshiruvlari.md`](07-wsl-muhit-tekshiruvlari.md) — shu mashinaning o'lchangan muhiti; §2 oomd yo'qligi, §4.4 distro restart, §4.7 `/init.scope`, §7.3 `.wslconfig`, §8 taqqoslash, §9 ochiq savollar
- [`PREREGISTRATION.md`](../../PREREGISTRATION.md) — §4 VR ta'rifi va bandlar, §7 PSI o'lchov qarorlari, §8.4 washout va quiescence, §9.3 arm/pressure bandlari, §9.4 dosing va ikki invariant, §12 disposition
- [`SECURITY.md`](../../SECURITY.md) — §1 oomd xavfi, §2 qatlamli yumshatishlar, §3 fail-closed, §4 qoldiq risk, §6 operator tartibi
- [`TESTING.md`](../../TESTING.md) — §3 guard testi protsedurasi (OQ-1, OQ-2)
- [`revix/guard.py`](../../revix/guard.py) — `DEFAULTS`, `Guard.trip`, `check_psi`, `_check_sustain`, `check_host`, `run`
- [`revix/pressure.py`](../../revix/pressure.py) — `Allocator.churn`, `run_ramp`, `run_pi` (§5 ning sababi)
- [`scripts/guard-test.sh`](../../scripts/guard-test.sh) — harness (§2 ning ikki blokeri)
