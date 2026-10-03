# 07 — WSL2 muhit tekshiruvlari (empirik)

Bu hujjatdagi har bir raqam **shu mashinada haqiqatan ishga tushirilgan**
buyruqdan olingan. Qayerda o'lchov bajarilmagan bo'lsa, shunday deb yozilgan.
Hujjat uchta belgi bilan ishlaydi:

- **FAKT** — o'lchandi, buyruq va chiqish keltirilgan;
- **TALQIN** — FAKTdan nima kelib chiqishi (o'lchov emas, xulosa);
- **CHEKLOV** — bu muhitda o'lchab bo'lmaydigan yoki kafolatlab bo'lmaydigan narsa.

Bu fayl [`01-muhit-tekshiruvlari.md`](01-muhit-tekshiruvlari.md) ning davomi:
o'sha hujjat avvalgi mashinani (native Kali) yozgan, bu esa REVIX endi ishlayotgan
mashinani (WSL2) yozadi. Natijalar qaysi mashinaga tegishli ekanini ko'rsatish —
shu hujjatning vazifasi.

**Sana:** 2026-10-02 (mahalliy vaqt UTC+05:00)
**Mashina:** hostname `Root-Zero`, Kali GNU/Linux Rolling `VERSION_ID="2025.3"`,
kernel `6.6.87.2-microsoft-standard-WSL2`, systemd `257 (257.7-1)`, foydalanuvchi
`snowden` (uid 1000), WSL `2.6.1.0`, Windows `10.0.26200.9550`.

### Kim nimani o'lchagan (provenance)

| Natija | Kim | Qayerda |
|---|---|---|
| `doctor` (4 ta ishga tushirish), baseline faktlar, `RestartSteps=` va boshqa property'lar, slice nomlash, dead-unit tuzog'i, distro idle testi, PSI trigger oynalari, fayl tizimi latency'si, xotira barqarorligi | **`agent/envcheck`** (men) | §1–§7 |
| `SOCK_SEQPACKET`, abstract `SOCK_SEQPACKET`, `NOTIFY_SOCKET` (fayl yo'li va `@abstract`), `Type=notify` + `WatchdogSec=2` real systemd 257.7 ostida | **`agent/sut-build`** | §7.1 — **men qayta o'lchamadim**, koordinator orqali olindi |
| `wsl.exe` `Wsl/Service/0x8007274c` va `E_UNEXPECTED`, guest `uptime` 9 daqiqadan 0 ga qaytishi, SIGABRT→exit ≈5 s anomaliyasi, dpkg yarim-configure | **`agent/sut-build`** va koordinator (mustaqil ravishda) | §6.3 — **men bu hodisalarni ko'rmadim**, faqat ko'chirdim |
| `doctor` 13 PASS / 3 WARN / 2 FAIL (git worktree sababli) | `agent/cli` va men (mustaqil, §1 da o'zimning raqamlarim) | §1 |

> **Nomlash haqida ochiq eslatma.** Topshiriq `revixselftest-` prefiksi va
> `revixselftest.slice` ni talab qildi. §3, §4, §5 dagi birinchi to'plam testlar
> shunday nomlar bilan o'tdi. Keyin aniqlandi: **boshqa agent o'z testlarini
> aynan shu `revixselftest.slice` da ishga tushirmoqda va har testdan keyin
> slice'ni teardown qilmoqda** (§4.5). Shuning uchun keyingi testlar (§3.2, §3.3,
> §4.4, §7) shaxsiy oila nomlari — `revixselftestec07.slice` va
> `revixselftestec07-*.service` — bilan o'tdi. Ular ham `revix-*`,
> `revixlab.slice`, `revixmon.slice` bilan to'qnashmaydi (`units.preflight()`
> default'i ularni ko'rmaydi — §3.3 da tasdiqlangan). Bu og'ish mening qarorim va
> sababi shu.

---

## 0. Qisqa xulosa

| | |
|---|---|
| `doctor` (yakuniy, 17:31:09Z) | **13 PASS, 3 WARN, 2 FAIL, exit code 1** |
| FAIL'lar | `git_present`, `git_clean` — **muhit buzuq emas**, git worktree tuzog'i (§4.3) |
| WARN'lar | `io_delegation`, `cpu_governor`, `kvm_access` |
| `GIT_DIR` berilgan diagnostik ishga tushirish | **15 PASS, 3 WARN, 0 FAIL, exit code 0** |
| **`RestartSteps=` systemd 257 da** | ✅ **qabul qilinadi VA ishlaydi** — lekin faqat `RestartMaxDelaySec=` bilan birga (§3, §4.2) |
| `cpufreq`, `thermal_zone*` | ❌ **yo'q** → PREREGISTRATION §8.5 tekshiruvi bu muhitda **mumkin emas** (§6.1) |
| `systemd-oomd` | ❌ **o'rnatilmagan** (binary ham, unit ham, config ham yo'q) |
| `sudo -n` | parol so'raydi |
| Distro idle'da to'xtaydi | ⚠️ transient unit'lar **o'ladi**, `boot_id` o'zgarmaydi (§4.4) |

---

## 1. `revix doctor`

```
$ python3 -m revix.cli doctor --json
```

Cheklov: bu worktree'da `cli.py` o'zgartirilmagan; hisobot shu holicha.

### 1.1 To'rt marta ishga tushirish

| # | Vaqt (mahalliy) | Python | Natija | exit | Izoh |
|---|---|---|---|---|---|
| 1 | 22:18:28 | 3.13.7 | 12 PASS / 3 WARN / **3 FAIL** | 1 | `python_modules` FAIL: `hech biri -- YETMAYDI: psutil, dbus, numpy, scipy` (o'rnatish hali ketayotgan edi) |
| 2 | 22:21:45 | 3.14.7 | 13 PASS / 3 WARN / **2 FAIL** | 1 | `apt-get install` tugagach (`/var/log/apt/history.log`: 22:18:38 → 22:20:43). `python_modules` PASS |
| 3 | 22:30:34 | 3.14.7 | **15 PASS / 3 WARN / 0 FAIL** | 0 | **diagnostik**: `GIT_DIR=…/.git/worktrees/envcheck GIT_WORK_TREE=…` bilan (§4.3). Rasmiy natija **emas** |
| 4 | 22:31:09 (17:31:09Z) | 3.14.7 | 13 PASS / 3 WARN / **2 FAIL** | 1 | **yakuniy**, barcha test unit'lari tozalangandan keyin |

`python_modules` talabi "bir marta kutib, qayta urinib, yakuniy holatni yozing"
edi: 2-ishga tushirishda PASS. Yakuniy holat shu.

### 1.2 18 ta tekshiruv (yakuniy holat, 2- va 4-ishga tushirish bir xil)

Ustunlar: tekshiruv `observed` / `required` ni o'zi shunday chiqargan. "Oqibat" —
`consequence` maydonining qisqartirilgan mazmuni (JSON'da to'liq matn bor va
PASS holatda ham to'ldiriladi).

| # | key | holat | observed | required | oqibat (doctor matni, qisqa) |
|---|---|---|---|---|---|
| 1 | `systemd_version` | PASS | `systemd 257 (257.7-1)` | `>= 254` | < 254 da `RestartSteps=`/`RestartMaxDelaySec=` yo'q → Baseline B o'lchanmaydi |
| 2 | `cgroup_v2` | PASS | `cgroup2 (/sys/fs/cgroup)` | `cgroup2 (stat -fc %T = cgroup2fs)` | v1 da `memory.pressure`, `cgroup.kill`, delegatsiya yo'q → harness ishlamaydi |
| 3 | `delegated_controllers` | PASS | `cpu memory pids` | `cpu memory pids` | delegatsiya bo'lmasa transient unit'lar `MemoryMax=`/`CPUQuota=`/`TasksMax=` qabul qilmaydi |
| 4 | `io_delegation` | **WARN** | `io delegated EMAS; io.pressure o'qiladi (IO PSI o'lchanadi)` | `io (ixtiyoriy -- P1 ishlatmaydi)` | `io.max` yozilmaydi → IO injection root/guest talab qiladi; `io.pressure` baribir o'qiladi |
| 5 | `psi_host` | PASS | `cpu, io, memory` | `cpu, io, memory -- o'qiladi va parse bo'ladi` | host PSI bo'lmasa pressure o'lchanmaydi |
| 6 | `psi_cgroup` | PASS | `cpu.pressure, io.pressure, memory.pressure` | `user@UID.service da cpu/io/memory.pressure o'qiladi` | guard `user@UID.service` ni kuzata olmaydi |
| 7 | `oomd` | PASS | `oomd inactive (enabled=not-found); user@1000.service: ManagedOOMMemoryPressure=auto; limit=? [oomd.conf, raw=0]; duration=? [oomd.conf] -- kill authority YO'Q` | `kill authority bo'lsa: oomd duration > 15 s (guard sustain chegarasi), pressure oynasi <= 12 s` | oomd desktop'ni o'ldirishi mumkin; yumshatish 12 s oyna + guard |
| 8 | `leftover_state` | PASS | `qoldiq yo'q (unit ham, cgroup ham)` | `revix-* unit yo'q; revixlab.slice/revixmon.slice cgroup'lari yo'q` | qoldiq bo'lsa run boshlanmaydi (00 §2) |
| 9 | `cgroup_write` | PASS | `hammasi yozildi va probe cgroup tozalandi` | `memory.max, memory.high, memory.swap.max, cgroup.kill -- yoziladi` | yozilmasa dosing/swap himoyasi/guard teardown yo'q |
| 10 | `memory_headroom` | PASS | `MemAvailable=9.2 GiB (MemTotal=9.7 GiB)` (1-run: `9.1 GiB`) | `>= 3.4 GiB MemAvailable (2.0 GiB shift + 1.4 GiB guard poli)` | yetmasa guard darhol trip qiladi yoki global OOM |
| 11 | `swap_headroom` | PASS | `SwapTotal=4.0 GiB, ishlatilgan 0 kiB (0.0%)` (1-run: `120.8 MiB (2.9%)`) | `swap mavjud va tinch holatda deyarli ishlatilmagan (< 10%)` | swap band bo'lsa reclaim sekinlashadi |
| 12 | `cpu_governor` | **WARN** | `cpufreq interfeysi yo'q (VM yoki driver yo'q)` | `performance (aks holda chastota kovariata sifatida log'lanadi)` | DVFS timing confound; chastota arm bo'yicha farq qilsa taqqoslash haqiqiy emas (§8.5) |
| 13 | `toolchain_cc` | PASS | `/usr/bin/cc -- cc (Debian 14.3.0-5) 14.3.0` | `` `cc` PATH'da `` | kompilyator bo'lmasa `sut.c` qurilmaydi |
| 14 | `python_version` | PASS | `3.14.7 (/usr/bin/python3)` | `>= 3.11` | 3.11 dan pastda ishga tushmaydi |
| 15 | `python_modules` | PASS | `psutil=7.1.0, dbus=1.4.0, numpy=2.4.6, scipy=1.17.1` | `psutil, dbus, numpy, scipy` | statistik tahlil / jarayon o'lchovi / D-Bus yo'q |
| 16 | `kvm_access` | **WARN** | `mavjud, lekin ruxsat yo'q  [kvm guruhida: yo'q]` | `/dev/kvm o'qish+yozish mumkin (ACL yoki guruh orqali)` | root talab qiladigan fault klasslari guest'da ham ishlamaydi; P1 uchun shart emas |
| 17 | `git_present` | **FAIL** | `…/envcheck git repo emas: fatal: not a git repository: …/envcheck/C:/Users/snowden/revix-os/.git/worktrees/envcheck` | `git binari bor va REPO_ROOT git repozitoriysi` | `run_meta` da commit yozilmaydi |
| 18 | `git_clean` | **FAIL** | `aniqlanmadi: fatal: not a git repository: …` | `toza daraxt (confirmatory run uchun MAJBURIY)` | confirmatory run reproducible emas |

`host` bo'limi (yakuniy hisobotdan): `hostname=Root-Zero`, `kernel=6.6.87.2-microsoft-standard-WSL2`,
`uid=1000`, `cpu_count=12`, `own_cgroup=/init.scope`, `boot_id=f7038da5-5ef5-426e-a2c1-3463cf5e43f2`.

### 1.3 Har bir non-PASS nega shunday (bu muhit nuqtai nazaridan)

- **#4 `io_delegation` WARN** — FAKT: `/sys/fs/cgroup/cgroup.controllers` =
  `cpuset cpu io memory hugetlb pids rdma`, lekin `cgroup.subtree_control` =
  `cpu memory pids`. `io` rootdan pastga yoqilmagan, shuning uchun
  `user@1000.service/cgroup.controllers` = `cpu memory pids`. Avvalgi mashinadagi
  holat bilan bir xil (01 §1). `io.pressure` o'qiladi (§2).
- **#12 `cpu_governor` WARN** — `cpufreq` va `thermal_zone*` yo'q (§6.1).
- **#16 `kvm_access` WARN** — FAKT: `crw-rw---- 1 root kvm 10, 232 /dev/kvm`;
  `id` → `groups=…4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),100(users),1001(docker)` —
  `kvm` guruhida emas; `test -r`/`test -w` ikkalasi ham "not". `getfacl` o'rnatilmagan
  (`command -v getfacl` → yo'q), shuning uchun doctor ACL yozuvini ko'rsata olmaydi.
  Modul yuklangan: `lsmod` → `kvm_amd`, `kvm`. 01 §8 da avvalgi mashinada ACL orqali
  `rw-` bor edi; bu yerda yo'q.
- **#17, #18 `git_*` FAIL** — §4.3.

---

## 2. Baseline faktlar

Hammasi bitta skriptdan (`$ ` bilan boshlangan qator — buyruq), 22:19–22:21.

```
$ uname -srm
Linux 6.6.87.2-microsoft-standard-WSL2 x86_64
$ systemctl --version | head -1
systemd 257 (257.7-1)
$ cat /proc/1/comm
systemd
$ systemctl is-system-running
running
$ grep -E "^(PRETTY_NAME|VERSION|VERSION_ID|ID|ID_LIKE)=" /etc/os-release
PRETTY_NAME="Kali GNU/Linux Rolling"   VERSION_ID="2025.3"   VERSION="2025.3"   ID=kali   ID_LIKE=debian
$ nproc
12
$ lscpu | grep …
Model name: AMD Ryzen 5 5600H with Radeon Graphics   Thread(s) per core: 2   Core(s) per socket: 6
Hypervisor vendor: Microsoft   Virtualization type: full   Virtualization: AMD-V
$ cat /proc/cmdline
initrd=\initrd.img WSL_ROOT_INIT=1 panic=-1 nr_cpus=12 hv_utils.timesync_implicit=1 console=hvc0 debug pty.legacy_count=0 WSL_ENABLE_CRASH_DUMP=1
```

```
$ grep -E "^(MemTotal|MemAvailable|SwapTotal|SwapFree):" /proc/meminfo     (22:19)
MemTotal:       10183888 kB          MemAvailable:    9660800 kB
SwapTotal:       4194304 kB          SwapFree:        4194304 kB
$ df -h /
/dev/sdd       1007G  4.7G  951G   1% /            (ext4 rw,relatime,discard,errors=remount-ro,data=ordered)
$ df -h /mnt/c
C:\             368G  358G   10G  98% /mnt/c       (9p rw,noatime,aname=drvfs;path=C:\;uid=1000;gid=1000;…;cache=5,access=client,msize=65536,trans=fd)
$ swapon --show
/dev/sdc partition   4G   0B   -2
```

```
$ stat -fc %T /sys/fs/cgroup
cgroup2fs                                  (cgroup2 rw,nosuid,nodev,noexec,relatime,nsdelegate)
$ cat /sys/fs/cgroup/cgroup.controllers
cpuset cpu io memory hugetlb pids rdma
$ cat /sys/fs/cgroup/cgroup.subtree_control
cpu memory pids
$ systemctl show user@1000.service -p Delegate -p DelegateControllers
Delegate=yes
DelegateControllers=cpu memory pids
$ cat …/user@1000.service/cgroup.controllers        # delegated subtree
cpu memory pids
$ cat …/user@1000.service/cgroup.subtree_control
cpu memory pids
$ ls -ld /run/user/1000
drwx------ 4 snowden snowden 160 Oct  2 22:19 /run/user/1000        (tmpfs, size=1018388k, mode=700)
```

PSI (bo'sh holat, bitta lahza):

```
$ cat /proc/pressure/{cpu,io,memory}
cpu:    some avg10=0.72 avg60=0.13 avg300=0.02 total=194788 | full avg10=0.00 … total=0
io:     some avg10=0.72 … total=359679 | full avg10=0.72 … total=327018
memory: some avg10=0.00 … total=0      | full avg10=0.00 … total=0
$ cat …/user@1000.service/{cpu,io,memory}.pressure      # per-cgroup
cpu:    some … total=487   | full … total=487
io:     some … total=13087 | full … total=13087
memory: some … total=0     | full … total=0
$ cat …/user@1000.service/cgroup.pressure
1
$ grep oom_kill /proc/vmstat
oom_kill 0
```

`/sys/fs/cgroup/cgroup.pressure` (root'da) ham mavjud. `CONFIG_PSI=y`,
`CONFIG_MEMCG=y`, `CONFIG_CGROUPS=y` (`zcat /proc/config.gz`).

oomd:

```
$ systemctl is-active systemd-oomd     → inactive   (rc=4)
$ systemctl is-enabled systemd-oomd    → not-found  (rc=4)
$ ls /usr/lib/systemd/systemd-oomd /usr/lib/systemd/system/systemd-oomd.service
ls: cannot access … No such file or directory     (ikkalasi ham)
$ dpkg -l systemd-oomd
dpkg-query: no packages found matching systemd-oomd
$ systemd-analyze cat-config systemd/oomd.conf
# Main configuration file systemd/oomd.conf not found
$ ls /usr/lib/systemd/system/user@.service.d/
10-login-barrier.conf                      (01 §7 dagi 10-oomd-user-service-defaults.conf YO'Q)
$ systemctl show user@1000.service -p ManagedOOMMemoryPressure -p ManagedOOMMemoryPressureLimit -p ManagedOOMSwap -p ManagedOOMPreference
ManagedOOMSwap=auto   ManagedOOMMemoryPressure=auto   ManagedOOMMemoryPressureLimit=0   ManagedOOMPreference=none
```

`/dev/kvm`: §1.3.

---

## 3. ⚠️ `RestartSteps=` systemd 257 da — Baseline B shartining empirik tekshiruvi

**Muhit:** `systemd 257 (257.7-1)`; loyiha 261 ga qarshi ishlab chiqilgan.

### 3.1 Qabul qilinishi — 13 property, bitta TIRIK transient unit (22:23:38)

```
$ systemd-run --user --slice=revixselftest.slice --unit=revixselftest-props --collect \
    -p Type=notify -p Restart=on-failure -p RestartSec=1s -p RestartSteps=4 -p RestartMaxDelaySec=8s \
    -p StartLimitBurst=0 -p WatchdogSec=30s -p TimeoutStartSec=10s \
    -p MemoryMax=64M -p MemoryHigh=48M -p MemorySwapMax=0 -p CPUQuota=50% -p TasksMax=16 \
    /usr/bin/python3 /tmp/ec07-notifier.py ping 40
Running as unit: revixselftest-props.service; invocation ID: f15f6918…        (rc=0)
```

Jonlilik isboti **bir xil `systemctl --user show` chaqiruvlar to'plamida**:

```
$ systemctl --user show revixselftest-props.service -p LoadState -p ActiveState -p SubState -p MainPID -p NRestarts -p Slice -p NotifyAccess
NotifyAccess=main  MainPID=302  NRestarts=0  Slice=revixselftest.slice
LoadState=loaded   ActiveState=active   SubState=running
```

```
$ systemctl --user show revixselftest-props.service -p Type -p Restart -p RestartUSec -p RestartSteps -p RestartMaxDelayUSec -p StartLimitBurst -p WatchdogUSec -p TimeoutStartUSec -p MemoryMax -p MemoryHigh -p MemorySwapMax -p CPUQuotaPerSecUSec -p TasksMax
Type=notify
Restart=on-failure
RestartUSec=1s
RestartSteps=4
RestartMaxDelayUSec=8s
TimeoutStartUSec=10s
WatchdogUSec=30s
CPUQuotaPerSecUSec=500ms
MemoryHigh=50331648
MemoryMax=67108864
MemorySwapMax=0
TasksMax=16
StartLimitBurst=0
```

**Kernel tomonidan o'zaro tekshiruv** (`/sys/fs/cgroup<ControlGroup>/…`):

```
memory.max        67108864        memory.high   50331648       memory.swap.max 0
cpu.max           50000 100000    pids.max      16              cgroup.pressure 1
```

| property | qabul qilindi | jonli qiymat | kernel |
|---|---|---|---|
| `Type` | ✅ | `notify` | — |
| `Restart` | ✅ | `on-failure` | — |
| `RestartSec` | ✅ | `RestartUSec=1s` | — |
| **`RestartSteps`** | ✅ | `RestartSteps=4` | — |
| **`RestartMaxDelaySec`** | ✅ | `RestartMaxDelayUSec=8s` | — |
| `StartLimitBurst` | ✅ | `0` | — |
| `WatchdogSec` | ✅ | `WatchdogUSec=30s` | — |
| `TimeoutStartSec` | ✅ | `TimeoutStartUSec=10s` | — |
| `MemoryMax` | ✅ | `67108864` | `memory.max` = `67108864` |
| `MemoryHigh` | ✅ | `50331648` | `memory.high` = `50331648` |
| `MemorySwapMax` | ✅ | `0` | `memory.swap.max` = `0` |
| `CPUQuota` | ✅ | `CPUQuotaPerSecUSec=500ms` | `cpu.max` = `50000 100000` |
| `TasksMax` | ✅ | `16` | `pids.max` = `16` |

Qo'shimcha: jonli unit uchun `systemctl --user show | wc -l` = **287**;
`RestartUSecNext=1s`, `RestartMode=normal` ham mavjud (257 da `RestartUSecNext` bor).

### 3.2 ⚠️ Qabul qilish ≠ ishlash: xatti-harakat testi (22:29)

Faqat `systemctl show` da `RestartSteps=4` ko'rinishi yetarli emas. Uch unit,
bir vaqtda, har biri `/bin/false` (darhol `exit 1`), `Restart=on-failure`,
`RestartSec=1s`, `StartLimitBurst=0`; 16 s davomida har 50 ms da
`systemctl --user show -p NRestarts -p ExecMainStartTimestampMonotonic -p RestartUSecNext`.
`d_start` = ketma-ket `ExecMainStartTimestampMonotonic` farqi:

| unit | qo'shimcha property | NRestarts → d_start (s) | `RestartUSecNext` |
|---|---|---|---|
| **A** | `RestartSteps=3`, `RestartMaxDelaySec=4s` | 1→1.040, 2→1.631, 3→2.566, 4→4.058, 5→4.031 | `1s`, `1.587401s`, `2.519842s`, `4s`, `4s` |
| **B** | `RestartSteps=3` (**`RestartMaxDelaySec` yo'q**) | 15 restart, d_start 1.011…1.092 s | doim `1s` |
| **C** | (hech narsa — nazorat) | 15 restart, d_start 1.026…1.091 s | doim `1s` |

(B jadvalida bir qator `d_start=0.000` — so'rov artefakti: `NRestarts` yangilandi,
`ExecMainStartTimestampMonotonic` hali yangilanmagan edi; keyingi qatorda 1.037 s.)

**FAKT:** A da kechikish geometrik oshadi (1 → 1.587 → 2.520 → 4 s) va
`RestartMaxDelaySec` da to'xtaydi. B va C da kechikish doimiy ≈1.03–1.09 s.

### 3.3 Harness'ning o'z yo'li — `revix/units.py` (D-Bus `StartTransientUnit`)

```
$ python3 dbus1.py        # SystemdUser.start_transient + dump_unit_properties(require_alive=True)
start_transient: job_result='done'  bracket_us=2556
dump: dump_valid=True load_state=loaded alive_before=True alive_after=True property_count=287
  Type=notify  Restart=on-failure  RestartUSec=1s  RestartSteps=4  RestartMaxDelayUSec=8s
  StartLimitBurst=0  WatchdogUSec=30s  TimeoutStartUSec=10s
  MemoryMax=67108864  MemoryHigh=50331648  MemorySwapMax=0  CPUQuotaPerSecUSec=500ms  TasksMax=16
  ActiveState=active SubState=running
guard: UnitNotAliveError raised for a non-existent unit (good)
teardown: errors=[] stopped=['revixselftestec07-dbus.service', 'revixselftestec07.slice']
preflight(own family): clean=True problems=[]
preflight() DEFAULT (revix-*, revixlab.slice, revixmon.slice): clean=True problems=[]
```

`teardown` **aniq** `unit_patterns`/`slices` bilan chaqirildi (default'lari
`revix-*`/`revixlab`/`revixmon` ga qaratilgan).

### 3.4 `WatchdogSec=` haqiqatan majburlanadi (22:24:22)

```
$ systemd-run --user … --unit=revixselftest-wd -p Type=notify -p WatchdogSec=2s -p Restart=no -p LimitCORE=0 \
    /usr/bin/python3 /tmp/ec07-notifier.py silent 60        # READY=1 yuboradi, keyin jim
(t≈0.5 s)  LoadState=loaded ActiveState=active SubState=running Result=success WatchdogUSec=2s
(t≈4.5 s)  LoadState=loaded ActiveState=failed  SubState=failed  Result=watchdog ExecMainCode=2 ExecMainStatus=6
journal:   revixselftest-wd.service: Watchdog timeout (limit 2s)!
           … Killing process 427 (python3) with signal SIGABRT.
           … Failed with result 'watchdog'.
```

Bu `agent/sut-build` ning real `sut` bilan olgan natijasi (§7.1) bilan mos.
**Nazorat testi** (jim emas, har soniya `WATCHDOG=1` yuboruvchi unit 2 s dan
uzoq tirik qoladimi) **yaroqsiz**: unit 22:24:27 da boshlandi va 22:24:30 da
`status=9/KILL` bilan o'ldi — men yubormagan SIGKILL; aynan shu soniyada boshqa
agentning teardown'i `revixselftest.slice` ni olib tashladi (§4.5). Bu o'lchov
**bajarilmadi**, qayta ishga tushirilmadi (kerak emas: `agent/sut-build` real
`sut` bilan "watchdog ping bor → 7 s tirik" ni o'lchagan, §7.1).

### 3.5 VERDIKT

> ✅ **`RestartSteps=` va `RestartMaxDelaySec=` systemd 257.7 da transient
> user-unit property sifatida qabul qilinadi (`systemctl --user show` jonli
> unit'dan), D-Bus `StartTransientUnit` yo'li bilan ham, va kechikishni haqiqatan
> geometrik oshiradi. Baseline B uchun unit fayli kerak emas va 257 yetarli.**
>
> ⚠️ **Shart:** `RestartMaxDelaySec=` **albatta** berilishi kerak. U bo'lmasa
> `RestartSteps=` jimgina e'tiborsiz qoladi (§4.2) — va `systemctl show` baribir
> `RestartSteps=3` ni ko'rsatadi.

TALQIN: harness Baseline B ni sozlaganda `RestartSteps`, `RestartMaxDelaySec`
(va `RestartSec`) ni **juftlik sifatida** yozishi va `run_meta.units_show` da
`RestartMaxDelayUSec != infinity` ni validatsiya qilishi kerak. Bu men yozmaydigan
kodga tavsiya (`units.py`/`validate.py` meniki emas).

---

## 4. Tuzoqlar (empirik topilgan)

### 4.1 Dead-unit tuzog'i — 257 da qayta tasdiqlandi (01 §4)

```
$ systemd-run --user --slice=revixselftest.slice --unit=revixselftest-dead --collect \
    -p RestartSteps=4 -p MemoryMax=64M -p WatchdogSec=7s /bin/sleep 6
(t≈1 s, TIRIK)  RestartSteps=4  WatchdogUSec=7s  MemoryMax=67108864  LoadState=loaded  ActiveState=active   | wc -l = 286
(t≈9 s, o'lgan) RestartSteps=0  WatchdogUSec=infinity  MemoryMax=infinity  LoadState=not-found  ActiveState=inactive | wc -l = 263
$ systemctl --user show revixselftest-dead.service >/dev/null; echo $?     → 0
$ systemctl --user is-active revixselftest-dead.service                    → inactive (rc=4)
```

`rc=0` va 263 qator **default'lar**, haqiqiy qiymat emas. (Mening birinchi
urinishimda `sleep 1` + 1.5 s kutish unit'ni o'ldirib qo'ydi va "tirik" o'qish
aynan shu default'larni berdi — tuzoqning o'zi. Qayta o'tkazildi: yuqoridagi
natija.) `units.dump_unit_properties(require_alive=True)` bu holatda
`UnitNotAliveError` ko'taradi (§3.3 da tasdiqlandi).

### 4.2 ⚠️ `RestartSteps=` `RestartMaxDelaySec=`siz — qabul qilinadi, e'tiborsiz qoladi

journal (`revixselftest-dead` va `revixselftestec07-stepsB`):

```
revixselftest-dead.service: Service has RestartSteps= but no RestartMaxDelaySec= setting. Ignoring.
```

Bu mashinada `systemctl show` bu holatda **ham** `RestartSteps=` ni ko'rsatadi;
yagona belgi — journal ogohlantirishi va §3.2 dagi B unit'ning doimiy 1 s
kechikishi. Baseline B ni jimgina nazoratga aylantirib qo'yadigan tuzoq.

### 4.3 ⚠️ Git worktree `.git` fayli Windows yo'lini saqlaydi — doctor FAIL beradi, muhit buzuq emas

```
$ cat …/worktrees/envcheck/.git
gitdir: C:/Users/snowden/revix-os/.git/worktrees/envcheck
$ git -C …/worktrees/envcheck rev-parse HEAD                      (WSL ichida)
fatal: not a git repository: …/envcheck/C:/Users/snowden/revix-os/.git/worktrees/envcheck     rc=128
$ git -C /mnt/c/Users/snowden/revix-os rev-parse HEAD            (asosiy checkout)
2030ff8973d605a541a13f1bf6ba4e60e6a1e198                          rc=0
$ GIT_DIR=/mnt/c/Users/snowden/revix-os/.git/worktrees/envcheck GIT_WORK_TREE=…/envcheck git rev-parse HEAD
2030ff8973d605a541a13f1bf6ba4e60e6a1e198                          rc=0
$ … git branch --show-current
agent/envcheck
```

Windows git yaratgan worktree'ning `.git` **fayli** `C:/…` mutlaq yo'lini
saqlaydi; Linux git uni joriy katalogga nisbatan o'qiydi va topolmaydi. Natija
(§1.1, 3-ishga tushirish): `GIT_DIR`/`GIT_WORK_TREE` bilan doctor
`git_present PASS (HEAD=2030ff8)` va `git_clean PASS (toza, HEAD=2030ff8)`,
jami **15/3/0, exit 0**.

TALQIN: bu "muhit buzuq" ko'rinishi, lekin emas. Oqibati harness uchun:
`run_meta.git_commit` va `git_dirty` majburiy (04 §1.1), `validate.py` da
`git_dirty` yo'q bo'lsa `git_dirty_missing` **ERROR** (`validate.py:493–495`),
confirmatory run'da `true` ham ERROR (`:502`). Demak **bajarish nusxasida
(execution copy) `.git` Linux tomonidan yechiladigan bo'lishi shart**.
Koordinator buni ext4 workspace'da tuzatayotgani aytildi; men tuzatishni
o'lchamadim.

### 4.4 ⚠️ Distro idle'da to'xtaydi: transient unit'lar o'ladi, `boot_id` o'zgarmaydi, bo'sh cgroup'lar qoladi

**Idle vaqti** (PowerShell, `wsl.exe -l --running` har 2–3 s da so'raladi, T0 = oxirgi
`wsl.exe` klienti chiqqan lahza). Ikki urinish:

| urinish | oxirgi poll'da hali "running" | birinchi "NOT running" |
|---|---|---|
| 1 (22:26:38 dan) | +12 s (3 s qadam) | **+15.3 s** |
| 2 (22:27:52 dan) | +8.3 s (2 s qadam) | **+10.3 s** |

**Unit o'lishi** (22:27:45 da `systemd-run --user --unit=revixselftestec07-persist --collect /bin/sleep 600`,
keyin klient chiqdi; ≈26 s keyin tekshirildi):

| | A (boshlash) | B (≈26 s keyin) |
|---|---|---|
| `boot_id` | `f7038da5-5ef5-426e-a2c1-3463cf5e43f2` | **o'sha** `f7038da5-…` |
| `/proc/uptime` | 518.15 s | 551.47 s (uzluksiz) |
| PID 1 `etimes` | 1 s | **7 s** (yangi init) |
| user manager `systemd --user` PID | 241 | **238** |
| `revixselftestec07-persist.service` | `loaded active running`, MainPID=303 | **`LoadState=not-found`, `inactive`** (`sleep 600` ham yo'q) |

Shu bilan mos: 22:22:16 dan oldingi journal'da `systemd[241]`, 22:23:38 dan
keyin `systemd[238]` — bir xil `boot_id` ichida.

Bo'sh cgroup'lar: unit yo'qolgach `…/user@1000.service/revixselftestec07.slice/`
va uning `…-persist.service/` bolasi **qoldi** (`cgroup.events: populated 0`,
`cgroup.procs` bo'sh); `rmdir` avval "Device or resource busy" (bola bor), bolani
keyin otani `rmdir` qilish ishladi (rc=0, rc=0). Qo'lda tozalandi.

**TALQIN (xulosa, o'lchov emas):**
- Oxirgi `wsl.exe` klienti chiqqandan ≈10–15 s keyin distro (systemd, user
  manager, barcha transient unit'lar) to'xtaydi. Kechalik kampaniya
  **doimiy ulangan `wsl.exe` sessiyasi** (driver'ning o'zi shu sessiyada yoki
  keepalive) talab qiladi; aks holda trial o'rtasida hamma narsa o'ladi.
  Bu mexanizmni (`instanceIdleTimeout`/`vmIdleTimeout`) men **nomlab tasdiqlamadim**
  — faqat xatti-harakat o'lchandi.
- **`run_meta.boot_id` distro qayta ishga tushganini ko'rsatmaydi** (VM
  o'zgarmagan). Detektor sifatida taklif (tekshirilmagan): `ps -o etimes= -p 1`
  yoki user manager PID'ning o'zgarishi.
- Qayta ishga tushgan distro'dan keyin `revixlab.slice` bo'sh cgroup katalogi
  **qolishi mumkin**, va `leftover_state`/`units.preflight()` uni **bloklovchi**
  deb sanaydi (`revixlab.slice`/`revixmon.slice` cgroup katalogi). Men buni
  `revixlab.slice` bilan sinamadim (taqiqlangan), faqat o'z oilamda ko'rdim.
- VM darajasidagi boot'lar ham ko'p: `journalctl --list-boots` (oxirgi 8 tasi) —
  21:48:06, 21:52:28, 21:57:12, 22:03:40, 22:03:56, 22:06:05, 22:08:22 (22:18:50
  gacha), 22:19:10 (davom etmoqda). Sababi menga noma'lum.

### 4.5 `revixselftest.slice` nom maydoni bir nechta agent o'rtasida **umumiy**

FAKT (journal, `-b 0`): boshqa test to'plami `revixselftest-{life,steps,watch,sink,preflight,teardown,failed,sliceprop}`
unit'larini **xuddi shu** `revixselftest.slice` da yaratib, har biridan keyin
`Removed slice revixselftest.slice` qildi (22:22:15–16 va 22:24:30–31). Mening
`revixselftest-wdok` nazorat unit'im 22:24:27 da boshlanib 22:24:30 da
`status=9/KILL` bilan o'ldi (§3.4). Slice darajasidagi `cgroup.kill` butun
subtree'ni o'ldiradi; shuning uchun umumiy slice nomi parallel agentlar uchun
xavfli. TALQIN (sabab nomlanishi): u boshqa suite'ning teardown'i — journal
vaqtlari mos keladi, lekin men jarayonning kimligini isbotlamadim.

### 4.6 Python interpreter o'lchov o'rtasida o'zgardi: 3.13.7 → 3.14.7

```
$ dpkg -l | grep -E "^ii +python3(\.[0-9]+)? "
python3 3.14.7-3   python3.13 3.13.7-1   python3.14 3.14.7-3
$ ls -l /usr/bin/python3        →  python3 -> python3.14
/var/log/apt/history.log: Start-Date 2026-10-02 22:18:38 … apt-get install -y build-essential python3-pytest
  python3-psutil python3-dbus python3-systemd python3-yaml python3-numpy python3-scipy python3-matplotlib rsync zstd
  (End-Date 22:20:43)
```

`doctor` 1-ishga tushirish 3.13.7, 2-chi 3.14.7 ko'rsatdi. O'rnatilgan versiyalar
(men import qilib tekshirdim): pytest 9.1.1, matplotlib 3.10.9+dfsg1, numpy 2.4.6,
scipy 1.17.1, psutil 7.1.0, dbus 1.4.0; `cc` 14.3.0 (Debian 14.3.0-5), GNU Make 4.4.1.
Loyiha ≥3.11 talab qiladi — PASS. TALQIN: interpreter `run_meta.python_version`
ga yozilishi shart (04 §1.1 da bor) — avvalgi mashina natijalari boshqa
interpreter bilan olingan. (Koordinator ma'lumoti: 3.14 ostida tizim `anyio`
plugini `SyntaxWarning: 'return' in a 'finally' block` chiqaradi — men buni
o'lchamadim.)

### 4.7 Shell'dan tug'ilgan jarayonlar `user@1000.service` ichida **emas**

```
$ cat /proc/self/cgroup
0::/init.scope
```

(`doctor` `host.own_cgroup` = `/init.scope`.) 01 §6 da avvalgi mashinada jarayon
Claude scope'ida (`user@…/app.slice/…`) tug'ilgan edi. Bu yerda `wsl.exe -e`
jarayonlari distro ildizidagi `/init.scope` da — `user@1000.service` PSI'siga
kirmaydi. TALQIN: 01 §6 ning **qoidasi o'z kuchida** (harness faqat
`systemd-run --user --slice=…` orqali), lekin sababi boshqa; avvalgi
"oomd Claude'ni o'ldiradi" xavfi bu yerda oomd yo'qligi uchun mavjud emas (§6.4).

---

## 5. Slice nomlash — qayta tasdiq (01 §2)

```
$ systemd-run --user --slice=revixselftest-nest.slice --unit=revixselftest-nest-a --collect --property=MemoryMax=64M /bin/sleep 30
$ systemd-run --user --slice=revixselftest.slice      --unit=revixselftest-dash-svc-b --collect --property=MemoryMax=64M /bin/sleep 30
$ find …/user@1000.service -maxdepth 3 -name 'revixselftest*'
revixselftest.slice
revixselftest.slice/revixselftest-dash-svc-b.service
revixselftest.slice/revixselftest-nest.slice                       <-- NESTED
revixselftest.slice/revixselftest-nest.slice/revixselftest-nest-a.service
$ systemctl --user show revixselftest-nest.slice -p Slice -p ControlGroup
Slice=revixselftest.slice
ControlGroup=/user.slice/user-1000.slice/user@1000.service/revixselftest.slice/revixselftest-nest.slice
$ systemctl --user show revixselftest.slice -p Slice
Slice=-.slice
$ systemctl --user show revixselftest-dash-svc-b.service -p Slice
Slice=revixselftest.slice
$ ls -d …/user@1000.service/revixselftest-nest.slice
ls: cannot access … No such file or directory
$ systemctl --user list-units 'revixselftest*' --all
… revixselftest-nest.slice   loaded active active  Slice /revixselftest/nest
```

✅ **Slice nomidagi `-` — ierarxiya ajratuvchisi** (`revixselftest-nest.slice` →
`revixselftest.slice/revixselftest-nest.slice`, `systemd` ning o'z tavsifi
`Slice /revixselftest/nest`). Dashli **service** nomi
(`revixselftest-dash-svc-b.service`) `--slice=` ko'rsatgan joyga tushdi,
hosila ierarxiya yaratmadi. `revixlab.slice`/`revixmon.slice` nomlari
(amendment v1.1) bu mashinada ham to'g'ri.

---

## 6. Bu yerda o'lchab BO'LMAYDIGAN narsalar (CHEKLOV) va nega muhim

### 6.1 CHEKLOV — `cpufreq` va `thermal_zone*` yo'q: PREREGISTRATION §8.5 tekshiruvi **mumkin emas**

```
$ ls -d /sys/devices/system/cpu/cpu0/cpufreq
ls: cannot access '/sys/devices/system/cpu/cpu0/cpufreq': No such file or directory     (rc=2)
$ cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq     → No such file or directory
$ cat …/cpufreq/scaling_governor                                → No such file or directory
$ cat …/cpufreq/scaling_driver                                  → No such file or directory
$ ls -d /sys/devices/system/cpu/cpufreq ; ls -la /sys/devices/system/cpu/cpufreq/
/sys/devices/system/cpu/cpufreq          (mavjud, lekin BO'SH katalog)
$ ls /sys/devices/system/cpu/cpu0/
cache crash_notes crash_notes_size driver firmware_node hotplug node0 power subsystem topology uevent
$ ls /sys/class/thermal
cooling_device0 … cooling_device11                                (12 ta, thermal_zone* YO'Q)
$ ls -d /sys/class/thermal/thermal_zone*
ls: cannot access '/sys/class/thermal/thermal_zone*': No such file or directory         (rc=2)
$ cat /sys/class/thermal/thermal_zone0/temp                     → No such file or directory
$ find /sys -maxdepth 6 -name scaling_cur_freq                  → (bo'sh)
$ find /sys -maxdepth 6 -name 'thermal_zone*'                   → (bo'sh)
$ find /sys -maxdepth 6 -name 'temp*_input'                     → (bo'sh)
$ for h in /sys/class/hwmon/hwmon*; …                           hwmon0: BAT1 (in0_input), hwmon1: AC1   (harorat yo'q)
```

`/proc/cpuinfo` dagi `cpu MHz` — **jonli chastota emas**: bo'sh holatda ikki marta
(3 s oraliq) o'qildi, 12 ta CPU ham `3293.730`. (Yuk ostida o'lchamadim —
yuk generatsiya qilmaslik qoidasi.) Kernel config'da `CONFIG_CPU_FREQ=y`,
`CONFIG_THERMAL=y`, lekin guest'da driver yo'q.

**Nega muhim:** PREREGISTRATION §8.5 har trial chegarasida `scaling_cur_freq`
va `thermal_zone*/temp` ni log'lashni va "agar chastota arm bo'yicha tizimli farq
qilsa, timing taqqoslashlari haqiqiy emas — bu tekshiriladi va hisobotda
beriladi" ni talab qiladi. **Bu tekshiruv bu muhitda bajarib bo'lmaydi.**
Chastota kovariata sifatida ham, arm bo'yicha farq testi sifatida ham mavjud emas.

- `run_meta.governor` va `run_meta.scaling_driver` = **`None` ("o'lchanmadi")**,
  hech qachon `0` ("nol o'lchandi") emas. `doctor` ham shunday qiladi
  (`cpu_governor` → WARN, `detail.governors=[]`). `validate.py` da `governor`/
  `scaling` ga havola yo'q (`grep` natijasi bo'sh) — demak `None` uni
  to'xtatmaydi.
- Yagona qolgan yumshatish — §8.5 ning o'zi nomlagan: **blok ichida
  randomizatsiya** (§8.4: RCBD, blok = har `(arm × pressure)` yacheykadan bitta
  trial). U sekin drift'ni arm'lar bo'yicha tarqatadi — lekin chastotani
  **o'lchamaydi** va tizimli farq bor-yo'qligini **tekshirmaydi**.
- §8.5 ning bu muhitdagi holati `agent/research` tomonidan alohida
  tuzatilmoqda; men uni o'zgartirmayman.

### 6.2 CHEKLOV — `io` controller delegated emas; `io.pressure` o'qiladi

§1.3 #4 va §2: `DelegateControllers=cpu memory pids`; `io.pressure` har ikki
joyda (`/proc/pressure/io`, `user@1000.service/io.pressure`) o'qiladi va
parse bo'ladi (doctor `psi_host`, `psi_cgroup` PASS). `io.max` va IO injection
P1 doirasidan tashqari (00 §4), o'zgarishsiz.

### 6.3 CHEKLOV — host/hypervisor beqarorligi guest ichidan ko'rinmaydi (boshqa agentlar ma'lumoti)

> **Provenance:** bu bandning FAKTlari men tomondan **ko'rilmagan**; ular
> `agent/sut-build` va koordinator tomonidan o'lchangan/kuzatilgan va menga
> yetkazildi. Men faqat §4.4 dagi o'zim kuzatganimni (VM boot ro'yxati, distro
> qayta ishga tushishi) qo'shaman.

Kuzatilgan (boshqalar): `wsl.exe` → `Wsl/Service/0x8007274c`, keyin
`Wsl/Service/E_UNEXPECTED` (tiklash uchun `wsl --shutdown` kerak bo'ldi); guest
`uptime` 9 daqiqadan 0 ga qaytishi; bitta ishga tushirishda SIGABRT→jarayon
chiqishi orasidagi interval ≈**5 s**, xuddi shu stsenariyning ikki qayta
ishga tushirishida ≈**7 ms**. Qayta ishlab chiqarilmadi va servis beqarorligi
bilan bir vaqtga to'g'ri keldi. Koordinatorda dpkg yarim-configure holatida qoldi
(`dpkg --configure -a` kerak bo'ldi).

**CHEKLOV:** REVIX tiklanish kechikishini mikrosekundlarda o'lchaydi. Hypervisor
darajasidagi soniyalar davom etgan to'xtash ma'lumotga **soniyalarda tiklangan
trial** sifatida tushadi va guest ichida uni artefakt deb belgilovchi
hech narsa yo'q: guest buni aniqlay olmaydi; kuzatilgan yagona alomat —
`/proc/uptime` ning 0 ga qaytishi.

Mavjud himoyalar va ularning **ochiq tan olingan** chegarasi:
- PREREGISTRATION §8.4 blok ichida randomizatsiya bunday hodisalarni arm'lar
  bo'yicha tarqatadi, bitta arm'ni yuklamaydi;
- §12 `contaminated` disposition va bystander servis kollateral zararni
  tutish uchun mo'ljallangan — lekin **hypervisor to'xtashi uchun
  loyihalanmagan**: bystander ham, SUT ham bir vaqtda to'xtaydi va ular
  o'rtasidagi nisbatda hech narsa ko'rinmasligi mumkin.

Monitoring taklifi (**da'vo emas, tekshirilmagan**): run davomida
`/proc/uptime` monotonligini va ketma-ket namunalar orasidagi mono-vaqt
sakrashini arzon tripwire sifatida kuzatish. Men `/proc/uptime` monotonligini
faqat bo'sh 25 s oynada tekshirdim (1 Hz, barcha delta = 1.000 s, §7.3) —
bu tripwire ishlashini isbotlamaydi.

### 6.4 CHEKLOV — `systemd-oomd` yo'q: frozen hujjatlarning 1-RAQAMLI xavfi bu yerda mavjud emas, lekin nima o'rniga turishi noma'lum

§2 FAKTlari: binary, unit, config yo'q. Doctor `oomd` → PASS (`kill authority YO'Q`)
— **PASS shu daemon yo'qligidan, mitigatsiya o'lchangani uchun emas**.
00 §3.1 va PREREGISTRATION §4 dagi `W_stab_pilot = 8 s` / ≤12 s oyna / guard
15 s sustain oomd'ning 20 s sharti ustiga qurilgan. Bu muhitda oomd yo'q — **bu
cheklovlarning hali kerak yoki kerak emasligini men hal qilmayman** (§9 OQ-1).

### 6.5 CHEKLOV — `sudo -n` parol so'raydi

```
$ sudo -n true
sudo: a password is required            (rc=1)
```

`snowden` `sudo` guruhida, lekin nazoratsiz privilegiyali qadam mumkin emas —
00 §4 bilan mos. `/dev/kvm` ga kirish ham shu sababli (§1.3 #16) yopiq.

---

## 7. WSL2-xos topilmalar

### 7.1 Unix socket'lar va `sd_notify` — **`agent/sut-build` o'lchagan, men qayta o'lchamadim**

Yetkazilgan natijalar (men tasdiqlamadim): `SOCK_SEQPACKET` to'liq ishlaydi
(bind, listen, connect, accept, xabar chegaralari saqlanadi, peer yopilgandan
keyin `recv` → `b''`); `CONFIG_UNIX=y`; abstract `SOCK_SEQPACKET` ishlaydi;
`NOTIFY_SOCKET` ham fayl yo'li, ham `@abstract` shaklida ishlaydi; `/run/user/1000`
tmpfs, 0700, `snowden` egasi, yoziladigan; real systemd 257.7 bilan `Type=notify`
`READY=1` ni qabul qildi, `NotifyAccess=main`, `WatchdogSec=2` unit'ni tirik
ushladi, progress to'xtatilgach `Watchdog timeout (limit 2s)!` →
`Failed with result 'watchdog'`.

Men mustaqil ravishda faqat quyidagini ko'rdim: `NOTIFY_SOCKET` ning haqiqiy
qiymati bu mashinada `'/run/user/1000/systemd/notify'` (fayl yo'li shakli;
`notifier.py` chiqishi), `WATCHDOG_USEC='30000000'` / `'2000000'` env'ga
berilgan, va §3.4 da watchdog SIGABRT bilan o'ldirdi.

**O'lchanmagan (mening tomondan):** `/mnt/c` (9p) da unix socket yaratish.

### 7.2 `/mnt/c` — 9p/drvfs

FAKT (§2): fs turi `9p`, `aname=drvfs`, `cache=5`, `msize=65536`; **C: 98%
to'la, 10G bo'sh**. Repo shu yerda (`findmnt -T <worktree>` → `9p C:\ /mnt/c`).
Qisqa append-latency namunasi (300 × 201 bayt, ms; p50 / p99 / max; **bitta
qisqa o'lchov, umumlashtirilmaydi**):

| fs | fsync=False | fsync=True |
|---|---|---|
| ext4 `/tmp` | 0.001 / 0.010 / 0.061 | 1.267 / 2.163 / 3.178 |
| tmpfs `/run/user/1000` | 0.002 / 0.005 / 0.012 | 0.002 / 0.006 / 0.014 |
| 9p `/mnt/c` (scratch katalog, repo emas) | 0.122 / 0.249 / 0.328 | 0.669 / 1.159 / 1.696 |

TALQIN: 9p yozuvi `fsync`siz ext4 dan ~100× sekin (0.122 vs 0.001 ms). 9p da
`fsync` ext4 dagidan **tez** chiqdi — bu 9p `fsync` Windows tomonida haqiqiy
diskka tushganini **kafolatlamaydi** deb o'qilmasin (men buni tekshirmadim, faqat
vaqtni o'lchadim). Harness JSONL'ni (10 Hz prober) ext4/tmpfs ga yozishi
maqsadga muvofiq — bu tavsiya, o'lchangan ustunlik emas. Repo `/mnt/c` da bo'lgani
uchun `doctor`/git so'rovlari ham 9p orqali o'tadi.

### 7.3 Xotira barqarorligi va `.wslconfig`

`C:\Users\snowden\.wslconfig` (o'qildi):

```
[wsl2]            memory=10GB   processors=12   swap=4GB
[experimental]    autoMemoryReclaim=disabled
```

(`pageReporting` kaliti faylda **yo'q**; "bu WSL build uni noma'lum deb rad etdi"
degan gap topshiriq matnidan — men buni tekshirmadim.) `/etc/wsl.conf`: `[boot] systemd=true`.

Ichkaridan samarali qiymatlar:

| `.wslconfig` | ichkarida o'lchangan | holat |
|---|---|---|
| `memory=10GB` | `MemTotal: 10183888 kB` (≈ 9.71 GiB) | ✅ mos (kernel zaxirasi hisobiga biroz kam) |
| `processors=12` | `nproc` = 12, `nr_cpus=12` (cmdline) | ✅ |
| `swap=4GB` | `SwapTotal: 4194304 kB` (aniq 4 GiB), `/dev/sdc` | ✅ |
| `autoMemoryReclaim=disabled` | — | **bu o'lchov bajarilmadi, sabab:** guest ichida bu sozlamani ko'rsatuvchi interfeys topilmadi |

Qo'shimcha o'qishlar: `/sys/module/page_reporting/parameters/page_reporting_order=5`,
`hv_balloon` moduli yuklangan (`hot_add=Y`, `pressure_report_delay=0`),
`/proc/vmstat`: `balloon_inflate 0`, `balloon_deflate 0`, `balloon_migrate 0`.
`vm.swappiness=60`, `overcommit_memory=0`, `transparent_hugepage=[madvise]`.

25 ta namuna, 1 Hz, **bo'sh holat, hech qanday pressure yo'q:**

```
MemTotal kB      min=10183888 max=10183888
MemAvailable kB  min=9204428   max=9628340
SwapFree kB      min=4194304   max=4194304
/proc/uptime delta: min=1.000 max=1.000 (monotonic: True)
oom_kill 0
```

TALQIN: `MemTotal` va swap 25 s ichida o'zgarmadi — shu oynada ballooning
ko'rinmadi. `MemAvailable` esa ≈424 MB (9204428→9628340 kB) tebrandi —
parallel agentlar ishlayotgan umumiy muhitda shu kutilgan. Uzoq muddatli
barqarorlik **o'lchanmadi** (25 s).

### 7.4 PSI trigger oynasi — privilegiyasiz

`revixselftestec07-psi` unit'ining `memory.pressure` fayliga (`some 150000 <oyna_µs>`):

| oyna | natija |
|---|---|
| 500 ms | REJECTED (Invalid argument) |
| 1000 ms | REJECTED |
| 1500 ms | REJECTED |
| **2000 ms** | **ACCEPTED** |
| 3000 ms | REJECTED |
| **4000 ms** | **ACCEPTED** |

01 §5 bilan mos: privilegiyasiz trigger oynasi 2 s ning karrali bo'lishi shart
(kernel 6.6.87.2). PREREGISTRATION §7 qarori — `total` polling, trigger emas —
bu mashinada ham o'zgarishsiz.

### 7.5 Aniqlangan cgroup yozish huquqi

`doctor` `cgroup_write` PASS: `memory.max`, `memory.high`, `memory.swap.max`,
`cgroup.kill` throwaway child'da yoziladi va tozalanadi; `cgroup.kill` bilan
subtree o'ldirish §3.4/§4.5 da kuzatildi.

### 7.6 Guest o'z-o'zidan qayta ishga tushadi; `vmIdleTimeout` buni to'xtatmadi

Bu bo'limni orkestrator o'lchadi (2026-10-03, ISO qurilishi davomida), chunki
uzun ishlar — ISO qurilishi va **≈2.5 soatlik pilot kampaniyasi** — o'rtasida
uzilib qolardi.

#### O'lchov usuli

`systemd-logind` har bir boot'da sessiya uchun `/var/tmp/systemd-private-<boot_id>-systemd-logind.service-XXXXXX`
katalogini yaratadi va **o'chirmaydi**. Katalog nomidagi 32 belgili maydon —
`/proc/sys/kernel/random/boot_id`. Demak bu kataloglar qayta ishga tushishlarning
saqlanib qolgan yozuvi: nomdan `boot_id`, `stat`dan vaqt.

#### FAKT

```
jami katalog              = 199
jami uniq boot_id         = 89
2026-10-03 uniq boot_id   = 23
```

2026-10-03 dagi qayta ishga tushish vaqtlari (`boot_id` o'zgargan daqiqalar):

```
00:06  03:24  03:29  03:36  03:38  04:22  04:36  04:37
10:07  10:10  10:16  10:20  10:26  10:53  11:08  11:09
11:14  11:27  11:31  12:03  12:08  12:12  12:12
```

Bo'sh holatdagi oraliqlar **1–5 daqiqa**. 11:33–12:01 oralig'ida (28 daqiqa)
yangi `boot_id` yo'q — o'sha oynada `mmdebstrap` ishlayotgan va uni kuzatuvchi
`wsl.exe` mijozi har 60 s da ochilayotgan edi.

#### FAKT — `vmIdleTimeout` qo'yildi va YORDAM BERMADI

`C:\Users\snowden\.wslconfig` ga `[wsl2] vmIdleTimeout=14400000` (4 soat)
qo'shildi, `wsl --shutdown` bajarildi. Kalit **qabul qilindi** — ishga
tushirishda "Unknown key" ogohligi chiqmadi (`pageReporting` chiqargan edi).
Shundan **keyin** qayta ishga tushishlar davom etdi: `12:03`, `12:08`,
`12:12`, `12:12`.

Muhit: `WSL version 2.6.1.0`, `Kernel version 6.6.87.2-1`, guest
`6.6.87.2-microsoft-standard-WSL2`, `systemd 257 (257.7-1)`.

#### FAKT — uzoq yashovchi mijoz ushlab turdi

Guest ichida 3 soatlik jarayon (`wsl.exe -d kali-linux -e sh -c 'exec sleep 10800'`)
ochiq mijoz sifatida ushlab turildi. `boot_id=fac1548b-…` **12:12:28 dan
12:27:04 gacha (≈15 daqiqa) o'zgarmadi** (`uptime` monoton o'sdi: 215 → 371 → 548 → 782 → 876 s),
va bu oynada ikkita ISO build zanjiri ishga tushdi.

#### TALQIN

Guest'ni tirik tutadigan narsa — **ochiq `wsl.exe` mijozi**, `vmIdleTimeout`
emas. Kalit nega hurmat qilinmagani **o'lchanmadi** (WSL ichki holati guest
ichidan ko'rinmaydi, 6.3 ga qarang); ehtimolliklar: bu build kalitni tahlil
qiladi-yu qo'llamaydi, yoki `[wsl2]` ichidagi boshqa kalit bilan ziddiyat.
Bu **gipoteza, tasdiqlanmagan** — lekin yechim unga bog'liq emas.

#### OQIBAT — protokol qadami (bajarilishi SHART)

Har uzun ish (ISO qurilishi, `revix run` pilot kampaniyasi) **ochiq mijoz
ushlab turilgan holda** boshlanadi, va ish **`boot_id` ni boshida yozib,
har qadamdan oldin solishtiradi**. `boot_id` o'zgarsa — natija bekor, chunki
transient unit'lar va `CLOCK_MONOTONIC` asosi yo'qolgan.

Pilot uchun qo'shimcha talab: ushlab turuvchi jarayon `sleep` bo'lsin va
o'lchanadigan slice'lardan **tashqarida** turishi kerak (WSL sessiya scope'ida,
`revixlab.slice`/`revixmon.slice` da emas) — aks holda u o'lchovga kiradi.

#### CHEKLOV — sanoq pastki chegara

Usul faqat `systemd-logind` sessiya ochgan boot'larni ko'radi. Sessiyasiz
boot iz qoldirmaydi, demak **23 — pastki chegara, aniq son emas**. Shuningdek
katalog vaqti boot vaqti emas, balki birinchi sessiya vaqti; farq o'lchanmadi
(hozirgi boot'da `uptime` bo'yicha ≈45 s).

#### O'LCHOV ARTEFAKTI — userns build kataloglari tashqaridan o'qilmaydi

`mmdebstrap --mode=unshare` yaratgan `rootfs` katalogi tashqi uid `100000` ga
tegishli; ichidagi kataloglarning bir qismi `0700`. Tashqaridan `ls` **bo'sh
natija** qaytaradi va `du` ichiga tushmaydi. Shuning uchun "katalog bo'sh"
o'qishi **yo'qlik dalili emas** — bu xato orkestratorning dastlabki
diagnostikasida sodir bo'ldi. Progress `du -sh <OUT_DIR>` (ota-katalog) yoki
`df` delta bilan o'lchanadi.

---

## 8. Avvalgi mashina bilan taqqoslash

Avvalgi: [`02-guard-kalibratsiyasi.md`](02-guard-kalibratsiyasi.md) sarlavhasi va
[`01-muhit-tekshiruvlari.md`](01-muhit-tekshiruvlari.md). Hozirgi: §1–§7.

| | avvalgi | hozir (o'lchangan) | harness uchun ma'nosi (TALQIN) |
|---|---|---|---|
| OS | Kali 2026.3 | Kali Rolling `VERSION_ID="2025.3"` (WSL2) | sarlavhadagi versiya `os-release` ga qarab yoziladi |
| kernel | 7.1.5+kali-amd64 | **6.6.87.2-microsoft-standard-WSL2** | PSI/cgroup v2 bor; boshqa kernel → guard/dosing qayta o'lchanishi kerak |
| systemd | 261 (261.2-1) | **257 (257.7-1)** | `RestartSteps=` ≥254 — ✅ ishlaydi (§3); `RestartMaxDelaySec=` majburiy juft |
| RAM | 15 GiB (15.4 total, ~7.6 avail) | **9.71 GiB** total, ≈9.2–9.6 GB avail | 2 GiB shift nisbatan zaxira kattaroq, lekin total kichik; `.wslconfig` bilan cheklangan |
| swap | 5.5 GiB | **4 GiB** (aniq) | `MemorySwapMax=0` siyosati o'zgarmaydi |
| CPU | 12 | **12** (Ryzen 5 5600H, 6c/12t, hypervisor) | `CPUQuota=400%` hali 12 dan ≥8 erkin degan farazga mos, lekin VM vCPU |
| `/` | nvme 100G, 25G bo'sh | ext4 virtual disk 1007G, 951G bo'sh; **`/mnt/c` 9p, 10G bo'sh (98%)** | disk yetarli; repo 9p da (§7.2) |
| foydalanuvchi | `rootzero` | `snowden` (uid 1000) | `user@1000.service` yo'li bir xil |
| oomd | **faol**, `kill`, 50%, 20 s | **o'rnatilmagan** | 00 §3.1 / PREREG §4 asoslari o'zgaradi — OQ-1 |
| CPU chastota | `amd-pstate-epp`, `powersave` | **`cpufreq` yo'q** | §8.5 tekshiruvi mumkin emas (§6.1) |
| termal | `thermal_zone*` | **yo'q** | xuddi shu |
| `/dev/kvm` | ACL `user:rootzero:rw-` — ishlaydi | `root:kvm 0660`, kirish **yo'q** | QEMU lab hozir mumkin emas |
| jarayon tug'ilishi | Claude scope (`user@…/app.slice`) | **`/init.scope`** | PSI hisobiga kirmaydi; qoida o'sha (`systemd-run --user`) |
| yashash muddati | doimiy desktop | **distro ≈10–15 s idle'da to'xtaydi** | kampaniya doimiy `wsl.exe` sessiyasini talab qiladi (§4.4) |
| Python | (hujjatda yozilmagan) | 3.14.7 (apt orqali 3.13.7 dan o'zgardi) | `run_meta.python_version` yozilishi shart |

### Xulosa — build tartibi (00 §6) talab qiladi

Avvalgi mashinaning **guard testi** va **pressure dosing kalibratsiyasi** bu
mashinaga ko'chirilmaydi: kernel, systemd versiyasi, jami RAM, oomd mavjudligi va
`user@` ichidagi band/bo'sh jarayonlar to'plami — hammasi boshqa. 02 §1 ning o'zi
"bu topilma bo'sh desktop shartiga bog'liq va band tizimda qayta o'lchanishi kerak"
deydi. Shuning uchun:

> **Har qanday pressure eksperimentidan oldin guard testi (00 §6 qadam 3) va
> pressure dosing kalibratsiyasi (qadam 4) bu mashinada QAYTA bajarilishi shart.
> "Retrofit qilinmaydi."**

Men hech qanday pressure ishga tushirmadim; guard bu yerda qayta
kalibrlanmagan.

---

## 9. Ochiq savollar (frozen hujjatlar bilan ziddiyat — men hal qilmayman)

- **OQ-1.** 00 §3.1 oomd'ni "1-RAQAMLI XAVF" deb, ≤12 s oyna va guard 15 s
  sustain'ni oomd'ning 20 s sharti ustiga quradi; PREREGISTRATION §4
  `W_stab_pilot = 8 s` shunga bog'liq. Bu muhitda `systemd-oomd` yo'q
  (§2, §6.4). Bu cheklovlar hali kerakmi — qaror frozen hujjat egasiniki.
  Kernel global OOM va VM xotira chegarasi (10GB) xavfi qoladi, lekin ular
  bu yerda o'lchanmadi.
- **OQ-2.** 02 §1 dagi "`user@` PSI ≈ `lab` PSI" topilmasi band desktop
  jarayonlari yo'qligiga bog'liq edi; bu yerda `user@1000.service` ichida desktop
  ilovalari yo'q, shell jarayonlari esa `/init.scope` da (§4.7). Guard
  chegaralari (35% / 15 s va oniy chegaralar) bu sharoitda qayta o'lchanishi
  kerak (§8 xulosasi).
- **OQ-3.** PREREGISTRATION §8.5 `scaling_cur_freq`/`thermal_zone*/temp` ni
  talab qiladi; bu yerda ikkalasi ham yo'q (§6.1). Tuzatish `agent/research`da.
- **OQ-4.** 01 §8 `/dev/kvm` ni mavjud deb yozadi; bu yerda kirish yo'q (§1.3).
- **OQ-5.** `run_meta.boot_id` distro qayta ishga tushishini ushlamaydi (§4.4);
  04 §1.1 / `schema.py` shartnomasi boot_id'ni "monotonic qiymatlar faqat bir
  boot ichida" invarianti uchun ishlatadi — distro restart unit'larni o'ldiradi,
  lekin monotonlik buzilmaydi. Qo'shimcha detektor kerakmi — shartnoma egasiniki.

---

## 10. Tozalash tasdiqlandi (yakuniy, 17:31:09Z)

```
$ systemctl --user list-units 'revix*' --all --no-legend --plain
(bo'sh)
$ ls …/user@1000.service | grep revix       → (bo'sh, grep rc=1)
$ find …/user@1000.service -maxdepth 3 -name 'revix*'    → (bo'sh)
$ ls /run/user/1000 | grep -i revix          → (bo'sh)
$ ls ~/.config/systemd/user                  → No such file or directory
$ ls /run/user/1000/systemd/user.control     → No such file or directory
$ units.preflight()  # default: revix-*, revixlab.slice, revixmon.slice
clean=True problems=[]
```

Yaratilgan hamma narsa: `revixselftest-{props,dead,nest-a,dash-svc-b,wd,wdok}`,
`revixselftest-nest.slice`, `revixselftest.slice`;
`revixselftestec07-{stepsA,stepsB,stepsC,dbus,psi,persist}`,
`revixselftestec07.slice`. Hech biri `revix-*`, `revixlab.slice`, `revixmon.slice`
emas. Skriptlar `/tmp` ichida (WSL) va sessiya scratch katalogida; repoga
faqat shu hujjat qo'shildi. Eslatma: `revixselftest.slice` ni boshqa agent ham
yaratadi/o'chiradi (§4.5), shuning uchun "tozalangan" holat faqat men
tekshirgan lahza uchun to'g'ri.
