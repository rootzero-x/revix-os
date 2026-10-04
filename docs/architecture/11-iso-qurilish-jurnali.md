# 11 — ISO qurilish jurnali: nima HAQIQATDA bajarildi

**Holat:** bu hujjat **bajarilgan ishning jurnali**, dizayn emas. Dizayn —
`09-iso-qurilishi.md` (685 satr, muzlatilgan). Bu yerda faqat **bajarilgan
buyruqlar, ularning haqiqiy chiqishi, o'lchangan davomiyligi va topilgan
xatolar** yoziladi.

Belgilar `09` bilan bir xil: **FAKT** (o'lchangan, buyrug'i keltirilgan),
**TALQIN** (xulosa), **CHEKLOV** (bu muhitda ta'minlanmaydigan narsa).

---

## 0. Bu image NIMA — va NIMA EMAS. Birinchi ekran, footnote emas

**REVIX'da adaptive recovery engine YO'Q.** Bu jumla shu hujjatning
birinchi ekranida turadi, chunki `09` §0 aynan shu sababni yozadi: ISO —
overclaiming eng oson bo'ladigan joy.

- `PREREGISTRATION.md` §13: **arm C (REVIX) siyosati va gate chegaralari
  muzlatilMAGAN**; ular o'z pre-registration'ini talab qiladi.
- `revix/` da arm C ni implement qiladigan **birorta modul yo'q**.
- `PREREGISTRATION.md` §0: P1 failure classifier, action selector yoki
  `Repairs()` matritsasi haqida **hech qanday da'vo qilmaydi**.

**Qurilgan narsaning yagona halol ta'rifi:**

> **Debian trixie + REVIX o'lchov harness'i.**
> Bu **reproducible research appliance** — benchmark'ni ko'chirib yurish
> uchun transport. Bu **operatsion tizim hissasi EMAS**, **adaptiv
> self-healing OS EMAS**, va uning nomi **"REVIX OS" EMAS**.

Image ichidagi `revix` nomi faqat **harness**ga tegishli.

Image **NIMA QILMAYDI** degan to'liq ro'yxat — §9.

---

## 1. Muhit — o'lchangan, taxmin qilinmagan

**FAKT.** Build WSL2 guest ichida bajarildi (Windows host emas):

```
$ uname -a
Linux Root-Zero 6.6.87.2-microsoft-standard-WSL2 #1 SMP PREEMPT_DYNAMIC
  Thu Jun  5 18:30:46 UTC 2025 x86_64 GNU/Linux
$ wsl.exe -l -v
  kali-linux       Stopped/Running   2
$ df -h /
/dev/sdd  1007G  5.4G  951G   1% /
$ free -m
Mem:  9945 total,  9389 available
```

**FAKT — toolchain, o'z ko'zim bilan tekshirildi** (brifing «o'rnatilgan va
tekshirilgan» deganini qayta o'lchadim, chunki tekshirilmagan da'vo FAKT
emas):

```
$ mmdebstrap --version        -> mmdebstrap 1.5.7
$ xorriso --version           -> xorriso version : 1.5.8.pl02
$ mksquashfs -version         -> mksquashfs version 4.7.5 (2026/03/01)
$ grub-mkstandalone --version -> grub-mkstandalone (GRUB) 2.14-2+kali1
$ command -v mkfs.vfat        -> /usr/sbin/mkfs.vfat
$ command -v mcopy            -> /usr/bin/mcopy
$ ls -l /usr/lib/ISOLINUX/isohdpfx.bin                  -> 432 bayt, bor
$ ls -l /usr/lib/syslinux/modules/bios/ldlinux.c32      -> 118884 bayt, bor
$ command -v qemu-system-x86_64                         -> YO'Q
```

**TALQIN:** toolchain haqiqatan mavjud. `qemu` esa **yo'q** — demak `09` §6
ning QEMU rejasi bu mashinada bajarilmaydi va boot testi **VirtualBox**
bilan o'tkazildi (§7).

**FAKT — pre-flight toza edi** (`iso/lib/common.sh:require_clean_env`,
`revix/units.py:require_clean()` mantig'i):

```
[revix-iso] pre-flight: toza (revix-* unit yo'q, revixlab/revixmon cgroup yo'q)
```

Ya'ni hech qanday REVIX o'lchovi buzilmadi.

**FAKT — `snapshot.debian.org` ISHLADI, almashtirish KERAK BO'LMADI.**
Brifing sekin bo'lsa oddiy mirror'ga o'tishga ruxsat bergan edi; o'tilmadi,
chunki arxiv javob berdi:

```
$ curl -sSI http://snapshot.debian.org/archive/debian/20261001T000000Z/dists/trixie/Release
HTTP/1.1 302 FOUND
location: /file/441fafd5eecf075d660c2495a16fa13252c80790/Release
```

va yuklab olish tezligi o'lchandi (kernel `.deb` ning o'sishi, namespace
ichidan):

```
t=0s   linux-image-6.12.107+deb13-amd64_6.12.107-1_amd64.deb  49 858 348 bayt
t=30s  linux-image-6.12.107+deb13-amd64_6.12.107-1_amd64.deb  74 307 107 bayt
=> ~815 KB/s
```

**TALQIN:** pinned snapshot (`R1`, `09` §3.1) **buzilmadi**. Reproducibility
da'vosi oddiy mirror'ga tushib **zaiflashmadi**. Bu muhim: `09` §3.1 R1
butun paket to'plamini VAQTGA qotiradi, va oddiy mirror bu kafolatni
yo'qotardi.

---

## 2. Topilgan va tuzatilgan xatolar

`09` §10 ochiq yozadi: skriptlar **yozildi va `bash -n` qilindi, lekin
bajarilmadi**. Bajarilganda **o'n yettita** haqiqiy xato chiqdi. Hammasi
`iso/` va `packaging/` ichida tuzatildi (fayl egaligi meniki), va har biri
uchun **xatoni ko'rsatgan haqiqiy xabar** keltiriladi.

Birinchi beshta xatoning **to'rttasi bitta ildizdan** o'sadi, va shu ildiz
`09` da **umuman yo'q**: `mmdebstrap --mode=unshare` ning uid map'i (§2.0).

**Xatolar xaritasi:**

| # | Qisqacha | Bo'lim |
|---|---|---|
| 1 | `$HOME` build yo'li sifatida yaroqsiz | §2.1 |
| 2 | build kataloglari ichkaridagi root uchun yozilmaydi | §2.2 |
| 3 | EFI FAT image binaridan kichik | §2.3 |
| 4 | rootfs tashqaridan to'liq o'qilmaydi | §2.4 |
| 5 | manba repo namespace ichidan o'qilmaydi | §2.5 |
| 6 | `dubious ownership`, ikki yuz bilan | §2.7 |
| 7 | build host'ining git konfiguratsiyasi oqib kiradi | §2.8 |
| 8 | guest build o'rtasida qayta ishga tushadi | §2.9 |
| 9 | normalizatsiya hook'i jonli procfs'ni aylanadi | §2.10 |
| 10 | `mksquashfs` env + CLI flaglarni rad etadi | §2.11 |
| 11 | `-sort` bo'shliqli yo'lni ifodalay olmaydi | §2.12 |
| 12 | `user@1000.service` ishga tushmaydi (**eng jiddiy**) | §2.13 |
| 13 | image ichida root bo'lish yo'li yo'q | §2.14 |
| 14 | `revix-swapfile.service` live rejimda o'ladi | §2.15 |
| 15 | fingerprint heredoc'ida command substitution | §2.16 |
| 16 | `python3-gi` yo'q → 12 ta test ERROR | §6.3 |
| 17 | `python3-matplotlib` yo'q → 2 ta test FAILED | §6.3 |

### 2.0 Ildiz sabab — o'lchangan

`mmdebstrap` manbasi (`/usr/bin/mmdebstrap:1469`):

```perl
push @result, ["u", 0, $subid, $num_subid];
```

ya'ni map **bitta** satrdan iborat. Tasdiq:

```
$ unshare --user --map-auto --setuid 0 -- cat /proc/self/uid_map
         0     100000      65536
```

**TALQIN — ikki oqibat, ikkisi ham `09` da hisobga olinmagan:**

1. Namespace ichida **uid 0 == tashqi uid 100000**.
2. Foydalanuvchining **o'z uid'i (1000) UMUMAN map qilinmaydi** — u ichkarida
   `nobody` bo'lib ko'rinadi.

Shundan: `$HOME` (`drwx------`) namespace ichidan **o'tib bo'lmaydi**, va
`mmdebstrap` yozgan rootfs tashqaridan **to'liq o'qilmaydi**.

### 2.1 Bug #1 — `$HOME` build yo'li sifatida prinsipial yaroqsiz

**Xato (haqiqiy chiqish, 1-urinish):**

```
E: cannot create /home/snowden/revix-iso: Permission denied;
   cannot create /home/snowden/revix-iso/work: Permission denied;
   cannot create /home/snowden/revix-iso/work/rootfs: Permission denied; ...
W: hooklistener errored out: E: received eof on socket
E: mmdebstrap failed to run
```

**Sabab:** `iso/config.sh` da `OUT_DIR="${OUT_DIR:-$HOME/revix-iso}"`.
Tasdiq:

```
$ ls -ld /home/snowden
drwx------ 19 snowden snowden /home/snowden
$ unshare --user --map-auto --setuid 0 -- ls -ld /home/snowden
drwx------ 19 nobody nogroup /home/snowden
$ unshare --user --map-auto --setuid 0 -- touch /home/snowden/revix-iso/probe
touch: cannot touch '...': Permission denied
```

**TALQIN:** bu konfiguratsiya emas, **struktura** muammosi. `09` §9.1
`OUT_DIR` ni «ext4 HOME» deb tanlaganda **to'g'ri** sababni (`/mnt/c` =
drvfs, 98% to'la) ko'rsatgan, lekin `--mode=unshare` bilan birga `$HOME`
ning 0700 rejimi **halokatli** ekani hisobga olinmagan.

**Tuzatish:** `OUT_DIR` default'i `/var/tmp/revix-iso` ga ko'chirildi.
`NEGA /var/tmp`: ota-katalog `drwxrwxrwt` (1777) — namespace ichidan
o'tiladi; fs ext4 (`stat -fc %T /var/tmp` → `ext2/ext3`) va 951 G bo'sh,
demak §7.2 ning **asl sababi** (ext4, drvfs emas) buzilmaydi.

`$HOME` ning o'zini `chmod o+x` qilish **qilinmadi**: u foydalanuvchining
shaxsiy katalogi va uning rejimini o'zgartirish build skriptining ishi emas.

### 2.2 Bug #2 — build kataloglari ichkaridagi root uchun yozilmaydi

**Xato (2-urinish, mening o'z fail-closed tekshiruvim ushladi):**

```
[revix-iso] XATO: build yo'li user namespace ICHIDAN yetib borilmaydi:
[revix-iso]   /var/tmp/revix-iso
```

**Sabab:** `mkdir -p` kataloglarni `snowden:snowden 0755` qilib yaratadi;
ichkaridagi root (tashqi 100000) ularga **yoza olmaydi**. Qo'shimcha: eski
kod `mkdir -p "$ROOTFS_DIR"` bilan rootfs katalogini **oshkora** yaratardi,
bu esa muammoni kuchaytirardi.

**Tuzatish:** `iso/lib/common.sh` ga `prepare_build_dirs()` qo'shildi —
`OUT_DIR`, `WORK_DIR`, `STAGE_DIR`, `STAGE_DIR/live` ni **bitta joyda**
0777 bilan yaratadi; `ROOTFS_DIR` esa **mmdebstrap'ning o'ziga** qoldiriladi
va eski rootfs namespace **ichida** o'chiriladi (`ns_run rm -rf`), chunki
tashqaridan `rm -rf` 0700 kataloglarda «Permission denied» beradi.

`NEGA bitta funksiya`: birinchi tuzatishda `OUT_DIR` 0777 qilindi, lekin
`STAGE_DIR/live` qilinmadi — va xato faqat 30-qadamda ko'rinardi. Kataloglar
ro'yxati bitta joyda bo'lsa bu sinf butunlay yopiladi.

### 2.3 Bug #3 — EFI FAT image EFI binarisidan KICHIK

Bu xato **bitishdan oldin** o'lchov bilan topildi (40-qadamga yetmasdan):

```
$ grub-mkstandalone --format=x86_64-efi --locales= --fonts= -o bootx64.efi ...
$ stat -c %s bootx64.efi
3817472          # = 3728 KiB
```

`iso/40-make-iso.sh` esa FAT image'ni **qo'lda** 2048 KiB deb yaratardi:

```bash
mkfs.vfat -C "$EFI_IMG" 2048 -n REVIXEFI -i ...
```

**TALQIN:** `mcopy` «disk full» bilan o'lardi. Qo'lda yozilgan hajm grub
versiyasi o'zgarishi bilan yana **jimgina** buziladi.

**Tuzatish:** hajm **binaridan hisoblanadi** —
`ceil((binary_KiB + 512) / 1024) * 1024`. Determinizm buzilmaydi: hajm
faqat binarining o'lchamiga bog'liq funksiya, vaqtga yoki tasodifga emas.
`+512 KiB`: FAT superblock, FAT jadvallari va root katalog yozuvlari joy
egallaydi.

### 2.4 Bug #4 — rootfs'ni ODDIY FOYDALANUVCHI sifatida o'qib bo'lmaydi

**Xato (o'lchangan, `du` bilan ko'rsatildi):**

```
$ du -sh /var/tmp/revix-iso/work/rootfs
du: cannot read directory '.../rootfs/root': Permission denied
du: cannot read directory '.../rootfs/var/cache/ldconfig': Permission denied
du: cannot read directory '.../rootfs/var/cache/apt/archives/partial': Permission denied
```

`09` §2 zanjiri `mksquashfs` ni **oddiy foydalanuvchi** sifatida bajarishni
nazarda tutgan. Bu ishlamaydi, chunki rootfs tashqi uid 100000 ga tegishli
va ichida o'qilmaydigan joylar bor: `/root` (0700), `/etc/ssh` kalitlari,
`/boot/initrd.img-*` (**0600**), `/etc/shadow`.

**TALQIN — ikkinchi oqibat birinchisidan YOMONROQ:**
agar xato yutilsa (`|| true`), squashfs **jimgina to'liqsiz** bo'ladi **va**
undagi egalik 100000 bo'lib qoladi — ya'ni boot qilgan tizimda `/root`
egasi `nobody` bo'lardi, va buni faqat guest ichida, ancha keyin sezardik.

**Tuzatish:** yangi fayl `iso/lib/ns-squashfs.sh` — sort fayli, `mksquashfs`,
kernel/initrd ko'chirish va bootloader binarlarini chiqarish **hammasi
namespace ichida**, `ns_run` orqali, mmdebstrap bilan **aynan bir xil** uid
map ostida bajariladi. Natijada:

- `find` 0700 kataloglarga kiradi → sort fayli to'liq → determinizm (R4)
  buzilmaydi;
- `mksquashfs` egalikni **0:0** deb yozadi — kerakli natija;
- `cp -a` o'rniga `cp` + oshkora `chmod 0644`, chunki namespace ichida
  yozilgan 0600 fayl keyingi qadamda (xorriso, oddiy foydalanuvchi)
  **o'qilmaydi**.

`09` §2.1 ning «root'siz build» sharti **buzilmaydi**: `sudo` ishlatilmadi,
biz hali ham privilegiyasiz user namespace ichidamiz.

30-qadamga **fail-closed** tekshiruv qo'shildi: namespace ichida yozilgan
uchta fayl (`filesystem.squashfs`, `vmlinuz`, `initrd.img`) tashqaridan
`-r` bilan tekshiriladi, aks holda qadam «bug #4 qaytdi» deb o'ladi.

### 2.5 Bug #5 — manba repo ham namespace ichidan o'qilishi kerak

**Sabab:** `iso/hooks/customize-10-revix.sh` → `packaging/install-revix.sh`
→ `git clone --no-hardlinks "$REPO_SRC" ...` **customize-hook fazasida**,
ya'ni **namespace ichida** ishlaydi. `REPO_SRC` `$HOME` ostida bo'lsa clone
«Permission denied» bilan o'ladi — va bu **butun paket o'rnatish
tugagandan KEYIN**, ya'ni ~20 daqiqa behuda ketadi.

**Tuzatish:** `iso/lib/common.sh` ga `require_userns_readable()` qo'shildi
va `10-build-rootfs.sh` da **build boshida** `REPO_SRC` uchun chaqiriladi.
Manba klon `/var/tmp/revix-src` ga ko'chirildi.

### 2.6 Qo'shimcha: worktree pointer tuzog'i — `09` §5.2(a) TASDIQLANDI

`09` §5.2(a) worktree'ning `.git` **pointer fayli** tuzog'ini oldindan
aytgan edi. U **tasdiqlandi, va kutilganidan yomonroq shaklda**: pointer
**Windows** yo'lini saqlaydi, demak WSL ichidan **umuman** yechilmaydi.

```
$ cat .claude/worktrees/isobuild/.git
gitdir: C:/Users/snowden/revix-os/.git/worktrees/isobuild
$ wsl: git -C /mnt/c/.../isobuild rev-parse HEAD
fatal: not a git repository:
  /mnt/c/.../isobuild/C:/Users/snowden/revix-os/.git/worktrees/isobuild
```

**TALQIN:** `09` ning «`git clone --no-hardlinks`, worktree pointer EMAS»
qarori **to'g'ri edi** va uni o'zgartirish kerak bo'lmadi. Lekin undan
tashqari **build'ning o'zi** worktree'dan bajarilmaydi: shuning uchun
`REPO_SRC` har doim **mustaqil ext4 klon** (`/var/tmp/revix-src`,
`git clone -b build/iso-run`).

### 2.7 Bug #6 — `dubious ownership`, IKKI yuz bilan

`09` §5.2(b) `dubious ownership` ni oldindan aytgan, lekin faqat **image
ichidagi** daraxt uchun (`chown` + `safe.directory`). Amalda xato **uch**
joyda chiqdi, va ikkitasi `09` da **yo'q**:

```
# (b1) MANBA repo, namespace ichida -- egasi map qilinmagan uid 1000 -> `nobody`
fatal: detected dubious ownership in repository at '/var/tmp/revix-src'
# (b2) va yana GITDIR yo'li uchun alohida:
fatal: detected dubious ownership in repository at '/var/tmp/revix-src/.git'
```

**TALQIN:** `git clone <mahalliy yo'l>` manba repoda `upload-pack` ni ishga
tushiradi va egalikni **gitdir yo'li uchun alohida** tekshiradi — ya'ni
bitta `safe.directory` yozuvi **yetarli emas**, ikkitasi kerak.

**Tuzatish:** `packaging/install-revix.sh` da `git_safe()` yordamchisi —
har yo'l uchun `-c safe.directory=$p -c safe.directory=$p/.git`, va barcha
`git` chaqiruvlari `git_src`/`git_img` orqali o'tadi. `iso/50-fingerprint.sh`
da ham image repo uchun oshkora `safe.directory` qo'shildi (u **namespace
tashqarisida** ishlaydi va daraxt egasi tashqi 101000).

`git config --global` **ishlatilmadi**: foydalanuvchining shaxsiy
konfiguratsiyasini o'zgartirish build skriptining ishi emas.
`safe.directory=*` ham ishlatilmadi: u barcha repozitoriylar uchun
tekshiruvni o'chiradi.

**NEGA bu xato 28 daqiqa yo'qotmadi:** soxta rootfs ustida, namespace
ichida `install-revix.sh` ni alohida **dry-run** qildim
(`/var/tmp/hooktest`) — xato **sekundlarda** chiqdi. To'liq build'ni
kutish shart emas edi.

### 2.8 Bug #7 — build host'ining git konfiguratsiyasi image'ga ta'sir qiladi

Dry-run ogohlik oqimini ko'rsatdi:

```
warning: unable to access '/home/snowden/.config/git/ignore': Permission denied
warning: unable to access '/home/snowden/.config/git/attributes': Permission denied
```

**TALQIN — bu faqat shovqin EMAS.** Bu yerda `$HOME` o'qilmagani uchun
ogohlik bilan tugadi; lekin `$HOME` **o'qilsa** (boshqa mashinada, yoki
skript tirik tizimda `sudo` bilan ishlatilsa), build host'ining shaxsiy
git konfiguratsiyasi clone'ga **ta'sir qiladi** — `core.autocrlf`,
`core.excludesFile`, filter'lar. Oqibati: image ichidagi daraxt **iflos**
chiqishi mumkin (→ doctor #18 `git_clean`), va image build host'iga
**bog'lanadi** (→ `09` §3 determinizmi).

Bu `customize-90-normalize.sh` ning `resolv.conf` uchun aytgan sababining
aynan o'zi: *«build host'ining sozlamalari image'ga TUSHADI — bu ham
nondeterminizm, ham provenance oqishi.»*

**Tuzatish:** `install-revix.sh` boshida `HOME`/`XDG_CONFIG_HOME` vaqtinchalik
izolyatsiya qilingan katalogga o'rnatiladi (`mktemp -d`, `trap` bilan
tozalanadi). `GIT_CONFIG_NOSYSTEM` **ishlatilmaydi**, chunki
`/etc/gitconfig` ga `safe.directory` **yozilishi kerak**.

### 2.9 Bug #8 — guest build o'rtasida qayta ishga tushadi (eng xavflisi)

Bu xato **xato bermaydi** — u **jimgina muvaffaqiyatga o'xshaydi**.

**O'LCHANGAN HODISA** (koordinator ikki marta, mustaqil ravishda ko'rdi):
`mmdebstrap` PID ~1900 bilan ishlayotgan va `~/revix-iso` 6.8 GB ga
o'sgan; bir necha daqiqadan keyin **aynan shu buyruq** PID ~400 bilan
**qaytadan** ishlayapti, `work/rootfs` **bo'sh**, `apt-get update`
**boshidan**, disk 5.4 GB ga tushgan. Tizimdagi eng katta PID **2901 →
557**. Bu progress emas, **yangi boot**.

Men ham shu rejimni mustaqil ravishda o'lchadim: build 12:11:17 da jimgina
to'xtadi, `pgrep -x mmdebstrap` → **yo'q**, rootfs 159 M da muzlab qoldi,
hech qanday xato xabari **yozilmadi**.

**SABAB (FAKT, `07` §4.4 da o'lchangan):** WSL2 oxirgi `wsl.exe` klienti
chiqqandan **10.3–15.3 s** keyin distro'ni to'xtatadi. Har bir tool-call
orasidagi bo'shliq — guest'ni yo'q qilish imkoniyati.

**TALQIN — nega bu eng xavfli xato:** agar 10-qadam yarmida o'lsa va
20-qadam **davom etsa**, ISO **yarim to'ldirilgan** rootfs'dan qurilardi.
Manifest yozilardi, checksum hisoblanardi, `SHA256SUMS` chiqardi —
**build muvaffaqiyatli ko'rinardi**, va buzilgan image faqat guest ichida,
ancha keyin fosh bo'lardi.

**Tuzatish — IKKI qism:**

1. **Sabab** (koordinator tomonidan): `C:\Users\snowden\.wslconfig` ga
   `vmIdleTimeout=14400000` (4 soat) qo'shildi va WSL qayta ishga tushirildi.
   Kalit **qabul qilindi** («Unknown key» ogohligi yo'q).
2. **Fail-closed detektor** (`iso/lib/common.sh`): `record_generation()` /
   `require_same_generation()`. 10-qadam generatsiyani qayd etadi; 20, 30,
   40, 50 qadamlari har biri **boshida** uni tekshiradi va o'zgargan bo'lsa
   **RAD ETADI**.

**NEGA IKKI marker, bittasi YETARLI EMAS** — `09` §1.1 jadvali va
`PREREGISTRATION.md` §16.11 aynan shuni talab qiladi:

| Marker | Nimani ushlaydi | Ko'r nuqtasi |
|---|---|---|
| `boot_id` | to'liq VM restart | init-only restart'da **o'zgarmaydi** |
| `/proc/1/stat` 22-maydon | init-only restart (PID 1 starttime) | yangi boot'ni eski boot'dan ajratmaydi |

`09` §1.1 ni takrorlaymiz: *«§14.6(5) invarianti **zarur, lekin YETARLI
EMAS**»*, va qo'shimcha marker uni *«**almashtirmaydi**, uni
**to'ldiradi**»*. Build detektori ham aynan **ikkisini** yozadi.

**TALQIN:** bu `09` §8 **G8** gipotezasining build darajasidagi
ekvivalenti. G8 kampaniya davomida markerlar o'zgarmasligini **gipoteza**
deb qo'ygan edi; build paytida u **buzildi** — ya'ni G8 bu muhitda
**jiddiy** risk, «ehtimol» emas.

### 2.10 Bug #9 — normalizatsiya hook'i JONLI procfs'ni aylanib chiqadi

**Xato (haqiqiy chiqish):**

```
[hook-90] normalizatsiya (SOURCE_DATE_EPOCH=1790812800)
touch: setting times of '.../rootfs/proc/13981/net/netfilter': Operation not permitted
touch: setting times of '.../rootfs/proc/13981/net/nf_conntrack': Operation not permitted
touch: setting times of '.../rootfs/proc/14017': No such file or directory
E: setup failed: E: command failed: .../customize-90-normalize.sh "$1"
E: mmdebstrap failed to run
```

**SABAB:** `mmdebstrap` customize-hook fazasida rootfs **ichiga** `/proc`,
`/sys`, `/dev` ni **mount qiladi** — chroot'da `useradd`,
`systemctl enable` va `update-initramfs` ishlashi uchun, ya'ni hook-20
aynan shunga **tayanadi**. Natijada `find "$ROOTFS"` butun **jonli**
procfs'ni aylanib chiqadi:

- (a) procfs faylining mtime'ini o'zgartirish **prinsipial ravishda**
  mumkin emas → `Operation not permitted`;
- (b) PID kataloglari yurish davomida **paydo bo'ladi va yo'qoladi** →
  `No such file or directory`, ya'ni xato **nondeterministik** — build har
  safar boshqa joyda o'lardi.

**Tuzatish:** `find` dan `/proc`, `/sys`, `/dev`, `/run` **prune**
qilinadi (`/opt/revix/.git` allaqachon prune qilingan edi).

**NEGA determinizm buzilmaydi:** `/proc`, `/sys`, `/run` image ichida
**bo'sh** mount point'lar (mmdebstrap build oxirida unmount qiladi), demak
ularning mtime'i squashfs'ga **tushmaydi**.
**CHEKLOV:** `/dev` ichidagi statik node'lar mtime normalizatsiyasidan
chetda qoladi — lekin squashfs bosqichi baribir barcha mtime'ni
SOURCE_DATE_EPOCH ga **clamp** qiladi (§2.11), demak **image darajasida
ta'siri yo'q**.

### 2.11 Bug #10 — `mksquashfs` 4.7.5 `SOURCE_DATE_EPOCH` + CLI flaglarni RAD ETADI

**Xato (haqiqiy chiqish):**

```
[ns-30] sortfile yo'llar soni: 32758
FATAL ERROR: SOURCE_DATE_EPOCH and command line options can't be used
             at the same time to set timestamp(s)
```

`09` §3.1 R3 `SOURCE_DATE_EPOCH` ni **ham** env orqali, **ham**
`-all-time`/`-mkfs-time` orqali berishni yozgan. `squashfs-tools` 4.7.5 esa
env o'zgaruvchisini **o'zi** qo'llab-quvvatlaydi va takroriy CLI
bayroqlarini **ziddiyat** deb sanaydi. `09` yozilganda bu tekshiruv hali
yo'q edi.

**Tuzatish:** faqat env o'zgaruvchisi ishlatiladi (u `iso/config.sh` da
export qilinadi, demak §3.3 ning «yagona haqiqat manbai» sharti
**buzilmaydi**).

**O'LCHANGAN TASDIQ** (soxta daraxt, `/var/tmp/sqtest`):

```
# faqat env bilan ikki build, 2 s oraliq bilan:
env1=7c07400cea16aa036f697a0fdee750815a4761c297978dbd351829131815b89f
env2=7c07400cea16aa036f697a0fdee750815a4761c297978dbd351829131815b89f
=> BIT-IDENTIK
# superblock:
Creation or last append time Thu Oct  1 05:00:00 2026   (= SOURCE_DATE_EPOCH)
```

**CHEKLOV — SEMANTIKA FARQI, oshkora:** `-all-time` barcha mtime'ni
**majburan** o'rnatadi; `SOURCE_DATE_EPOCH` esa ularni **clamp** qiladi.
O'lchangan:

```
a.txt  mtime 2020-09-13 (< epoch) -> 2020-09-13 SAQLANDI
b.txt  mtime 2033       (> epoch) -> 2026-10-01 CLAMP bo'ldi
```

**NEGA bu yerda ekvivalent:** `customize-90-normalize.sh` barcha faylni
(pseudo-fs'lardan tashqari) aynan SOURCE_DATE_EPOCH ga qotiradi, va
normalizatsiyadan chetda qolgan yagona narsa — build paytida yaratilgan
`/dev` node'lari, ularning vaqti epoch'dan **keyin**, demak **clamp**
bo'ladi. Natijada image ichidagi har bir mtime SOURCE_DATE_EPOCH ga teng.

### 2.12 Bug #11 — `-sort` fayl formati bo'shliqli yo'lni IFODALAB BO'LMAYDI

**Xato (haqiqiy chiqish):**

```
Sort file ".../sortfile.txt", can't find priority in entry
"usr/lib/python3/dist-packages/scipy/io/tests/data/Transparent Busy.ani 0",
EOL or match failure
FATAL ERROR: Failed to read sort file
```

**SABAB:** `mksquashfs -sort` formati `<yo'l> <priority>` bo'lib, oxirgi
bo'shliqdan keyingi qismni priority deb o'qiydi. Formatda **quoting yoki
escaping mexanizmi YO'Q**, demak ichida bo'shliq bo'lgan yo'lni
**ifodalab bo'lmaydi**. Bu formatning qattiq cheklovi.

**O'LCHANGAN:** butun rootfs'da (32758 yo'l) bo'shliqli yo'l **aynan
bitta** — `scipy` ning test fixture'i `Transparent Busy.ani`.

**Tuzatish:** bo'shliqli yo'llar sort faylidan chiqariladi, lekin **har
biri log'ga oshkora yoziladi** (jimgina tashlab ketilmaydi). To'liq ro'yxat
`$WORK_DIR/filelist.txt` da saqlanadi.

**NEGA determinizm deyarli buzilmaydi:** sort faylida bo'lmagan fayl
mksquashfs'da default priority **0** oladi — ro'yxatdagilar bilan aynan
bir xil. Demak farq faqat shu bitta faylning bir xil prioritetli guruh
**ichidagi** o'rnida.
**NEGA fayl image'dan chiqarilmaydi:** u `python3-scipy` paketining qismi;
uni o'chirish dpkg integrity'sini va manifest'ning to'g'riligini buzardi.
**CHEKLOV:** `09` §3.1 R4 ning «to'liq oshkora tartib» da'vosi 32758
yo'ldan **32757** tasi uchun amal qiladi, hammasi uchun **emas**.

### 2.13 Bug #12 — `user@1000.service` ishga tushmaydi (eng JIDDIY xato)

Bu xato image'ni **boot bo'ladigan, lekin FOYDASIZ** holatga keltiradi.

**O'LCHANGAN, birinchi boot'da, guest ICHIDA:**

```
$ systemctl status user@1000.service
   Active: failed (Result: exit-code)
  Process: 610 ExecStart=/usr/lib/systemd/systemd --user
           (code=exited, status=1/FAILURE)
    Error: code: 49 (Protocol driver not attached)
$ dpkg -l libpam-systemd
  un  libpam-systemd <none>        <- UMUMAN O'RNATILMAGAN
$ echo $XDG_RUNTIME_DIR
  (bo'sh)
```

va `revix doctor` da shundan **beshta** FAIL kelib chiqdi — hammasi
**bitta** ildizdan:

```
delegated_controllers :: RuntimeError('user@1000.service cgroup topilmadi:
                         /sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service')
io_delegation         :: (ayni xato)
psi_cgroup            :: (ayni xato)
cgroup_write          :: (ayni xato)
leftover_state        :: "Failed to connect to user scope bus via local transport:
                          $DBUS_SESSION_BUS_ADDRESS and $XDG_RUNTIME_DIR not defined"
```

**NEGA bu eng jiddiy:** loyihaning **butun o'lchov qamrovi**
`user@UID.service` ierarxiyasi ichida yashaydi —
`00-pilot-topologiya.md` §1 `revixlab.slice`/`revixmon.slice` ni
`user@UID.service` ostiga qo'yadi, `revix/cgroup.py:user_service_cgroup()`
aynan shu yo'lni hisoblaydi, va `revix/units.py` transient unit'larni
`systemd-run --user` orqali yaratadi. U ishga tushmasa image **boot
bo'ladi**, lekin **birorta trial o'tkaza olmaydi** — ya'ni «ISO boot
bo'ldi» rost bo'lib qolib, image baribir **foydasiz** bo'lardi.

**MUHIM — nima ayb EMAS edi** (o'lchangan, taxmin emas):

```
$ cat /sys/fs/cgroup/cgroup.subtree_control
cpu io memory pids                       <- `io` BOR, revix-io-delegate ISHLADI
$ systemctl is-active revix-io-delegate.service
active
$ systemctl show user@1000.service -p Delegate -p DelegateControllers
Delegate=yes
DelegateControllers=cpu io memory pids   <- mening drop-in'im QO'LLANDI
```

Ya'ni `09` §1 ning **asosiy ilmiy maqsadi** — `io` ni cgroup root'ning
`subtree_control` iga yozib **fault class 6** ni ochish — **ISHLADI**.
Nosozlik delegatsiyada emas, **sessiya** qatlamida edi.

**Tuzatish:** `libpam-systemd` va `dbus-user-session` paket to'plamiga
qo'shildi.
`NEGA libpam-systemd`: `pam_systemd.so` login paytida logind sessiyasini
yaratadi va `XDG_RUNTIME_DIR` (`/run/user/1000`) ni o'rnatadi; usiz
`systemd --user` o'z runtime katalogini topa olmaydi.
`NEGA dbus-user-session`: `systemd-run --user` session bus'ni talab qiladi.
`NEGA --variant=important ularni o'zi tortib kelmadi`: ikkisi ham
"important" to'plamiga kirmaydi.

### 2.14 Bug #13 — image ichida ROOT bo'lishning YO'LI YO'Q edi

**O'LCHANGAN:** `sudo` o'rnatilmagan; root paroli Debian default'i bo'yicha
**qulflangan**; `customize-20-systemd.sh` faqat **o'lchov**
foydalanuvchisining parolini bo'shatadi (`passwd -d revix`).

**TALQIN — bu image'ning butun asosiga zid.** `09` §1 image'ni aynan
«privilegiyali tier'larni ochish» uchun asoslaydi, va
`00-pilot-topologiya.md` §4 ro'yxati — `io.max`, `dm-delay`/`dm-flakey`,
`tc netem`, `cpuset` pinning, `drop_caches`, harness'ni system slice'ga
ko'chirish — **hammasi root talab qiladi**. Root'siz image *«root kerak =
guest'ga tegishli»* prinsipini **bajarmaydi**, ya'ni o'zining **yagona
ilmiy sababini** bajarmaydi.

Qo'shimcha, amaliy oqibat: root'siz `journalctl -u user@1000.service`
*«No journal files were opened due to insufficient permissions»* beradi —
ya'ni bug #12 ni image **ichida** diagnostika qilib bo'lmadi.

**Tuzatish:** `sudo` qo'shildi, `/etc/sudoers.d/90-revix` da NOPASSWD, va
o'lchov foydalanuvchisi `adm`,`systemd-journal` guruhlariga qo'shildi.

**CHEKLOV (oshkora):** NOPASSWD sudo + parolsiz autologin image'ni
**ishonchsiz tarmoqqa chiqarish uchun mutlaqo yaroqsiz** qiladi. U
tadqiqot appliance'i, **deployment artifact'i EMAS** (`09` §0).

### 2.15 Bug #14 — `revix-swapfile.service` live rejimda o'ladi

**O'LCHANGAN (serial console'da, boot paytida):**

```
[FAILED] Failed to start revix-swapfile.service
```

**SABAB:** `ConditionPathIsReadWrite=/var` live image'da **rost** bo'ladi —
`live-boot` squashfs ustiga RAM'da yoziladigan qatlam qo'yadi, demak
`/var` haqiqatan yoziladi. Lekin u **RAM**, ya'ni 4 GiB swapfile 3 GiB li
VM'ga **sig'maydi**, va sig'gan taqdirda ham bu **RAM'ni RAM'ga swap
qilish** bo'lardi.

Unit'ning o'z izohi bu holatni **oldindan aytgan** edi (*«live rootfs
overlay RAM'da bo'lsa swapfile FOYDASIZ … unit o'sha holatda O'ZINI
O'CHIRADI»*), lekin `ConditionPathIsReadWrite=` uni **aniqlay olmaydi** —
u faqat **yozilishni** tekshiradi, **ortdagi qurilmani** emas.

**Tuzatish:** `ExecStartPre`/`ExecStart` `findmnt -no FSTYPE --target /var`
bilan `tmpfs|overlay|ramfs` ni aniqlab, unit'ni **muvaffaqiyat bilan,
lekin ish qilmasdan** tugatadi.
`NEGA exit 0, xato EMAS`: swap yo'qligi doctor #11 da **WARN**, FAIL emas
(`revix/cli.py:check_swap_headroom` → `if total == 0: ... WARN`). Soxta
`FAILED` holat esa `systemctl is-system-running` ni `degraded` qiladi va
**haqiqiy** nosozliklarni ko'mib yuboradi.

### 2.16 Bug #15 — `50-fingerprint.sh` heredoc ichida COMMAND SUBSTITUTION

`iso/50-fingerprint.sh:125` da markdown backtick'lari **quote qilinmagan**
heredoc (`<<EOF`) ichida turardi, demak bash ularni **buyruq** sifatida
bajardi:

```
revix: command not found
```

va natijada `build-fingerprint.json` ga backtick'li matn **jimgina
o'chirilgan** holda yozildi:

```json
"measurement_equivalent": "... ikkisida ham  checks[].status bir xil"
```

**TALQIN:** bu provenance faylining **mazmunini** o'zgartiradi, va xato
**jimgina** — hech qanday ogohlik yo'q. Heredoc `<<EOF` bo'lib qolishi
**kerak** (u `$SUITE`, `$ARCH` va boshqalarni interpolyatsiya qiladi),
shuning uchun backtick'lar escape qilindi (`\``).

### 2.17 Qo'shimcha: `wsl.exe` orqali quoting — xatolar manbai

**CHEKLOV (metodologik, kodda emas):** `wsl.exe -- bash -lc '<ko'p satrli
skript>'` chaqiruvlari Git Bash → `wsl.exe` argument konversiyasi sababli
**jimgina buziladi** (o'zgaruvchi bo'sh qoladi, `awk '{print $22}'`
«runaway string constant» beradi, `/mnt/...` yo'li
`C:/Program Files/Git/mnt/...` ga aylanadi). Shuning uchun **barcha**
build qadamlari **fayl sifatida** yozilib, `bash <fayl>` bilan chaqirildi.
Bu `iso/` kodiga tegishli emas, lekin jurnalga yozildi, chunki keyingi
o'quvchi aynan shu tuzoqqa tushadi.

---

## 3. Build — o'lchangan wall-clock vaqt

**FAKT.** Yakuniy build, toza daraxtdan (`f495fcd`), bitta uzluksiz
`wsl.exe` chaqiruvi ichida. Vaqtlar `date +%s` bilan o'lchangan, taxmin
EMAS.

| Qadam | Vosita | RC | Wall-clock |
|---|---|---|---|
| `10-build-rootfs.sh` | `mmdebstrap --mode=unshare` | 0 | **14 m 37 s** |
| `20-record-manifest.sh` | `dpkg-query --admindir` | 0 | **0 m 00 s** |
| `30-make-squashfs.sh` | `mksquashfs` (xz, `-processors 1`) | 0 | **3 m 42 s** |
| `40-make-iso.sh` | `grub-mkstandalone` + `xorriso` | 0 | **0 m 07 s** |
| `50-fingerprint.sh` | `sha256sum` | 0 | **0 m 02 s** |
| **JAMI** | | | **18 m 28 s** |

**TALQIN:** vaqtning **~79%** i bitta qadamda — `mmdebstrap` da, va uning
ichida ham asosiy qism `snapshot.debian.org` dan yuklab olish. Shu qadam
to'rt marta o'lchandi: **28 m 34 s**, **20 m 37 s**, **16 m 21 s**,
**14 m 37 s** — ya'ni u **tarmoqqa bog'liq** va takrorlanganda ikki
baravargacha tebranadi. Qolgan to'rt qadam birgalikda **4 daqiqadan kam**.

**Javob «bu qancha vaqt oladi?» savoliga:** toza mashinada, tarmoq yaxshi
bo'lsa — **~15–20 daqiqa**; tarmoq sekin bo'lsa — **~30 daqiqagacha**.

Guest generation build boshida va oxirida **bir xil** edi:

```
boshida: boot_id=fac1548b-572a-439b-9c69-f993abc673aa pid1_starttime_ticks=15609
oxirida: boot_id=fac1548b-572a-439b-9c69-f993abc673aa pid1_starttime_ticks=15609
```

ya'ni bug #8 bu build davomida **takrorlanmadi**.

---

## 4. Natija — ISO

**FAKT:**

```
fayl      : revix-appliance-trixie-20261001T000000Z.iso
hajm      : 564 133 888 bayt  (538 MiB)
sha256    : ccb08016908e82b0509cd0263555e5713dea4513abeb575c61b73d46da3b2e8d
manifest  : 05c92b0c2605f498d8850ac71a5b2fa5a28ff422735a754a3b5a6826d86f2ae5
fingerprint: d4a47386b261c64f2fe2155691ab35364a83722045631bc03e4dbcbbacc93b52
git_commit: f495fcdea284298d8c2eb90fc63cdc2a943ddfe1
git_dirty_at_build: false
paket soni: 352
```

Oldingi, oraliq image (`67d54d5`, 281 paket, 481 296 384 bayt,
sha256 `56bed692...`) ham qurildi va boot qilindi; u `pytest` dagi ikki
paket kamchiligini (§6.3) fosh qilgani uchun saqlanmadi.

**Versiya chegaralari — `20-record-manifest.sh` ularni HAQIQATAN tekshiradi**
(brifing «verify it does» deb so'ragan edi; `dpkg --compare-versions`
ishlatilishi tasdiqlandi va u o'tdi):

```
systemd = 257.13-1~deb13u1 (kerak >= 254)   <- Baseline B o'lchanadi
python3 = 3.13.5-1         (kerak >= 3.11)
python3-{psutil,dbus,numpy,scipy}: bor
git: bor ; build-essential: bor
systemd-oomd: yo'q (ATAYLAB, 09 §4.4)
kernel: linux-image-6.12.107+deb13-amd64 6.12.107-1
```

**El Torito — hybrid boot tasdiqlandi** (`xorriso -report_el_torito`):

```
Volume id    : 'REVIX_APPLIANCE'
El Torito boot img : 1  BIOS  /isolinux/isolinux.bin  (boot-info-table, isohybrid-suitable)
El Torito boot img : 2  UEFI  /EFI/boot/efiboot.img
Boot record  : El Torito , MBR isohybrid cyl-align-on GPT
```

---

## 5. Boot — VirtualBox, HAQIQIY DALIL

### 5.1 Aynan bajarilgan `VBoxManage` buyruqlari

Foydalanuvchining `snowden` VM'iga **tegilmadi** (u `poweroff`, 4000 MB,
4 vCPU holatida qoldi). Alohida `revix-os` VM ishlatildi.

```powershell
$VB  = 'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'
$ISO = 'C:\Users\snowden\revix-iso\revix-appliance-trixie-20261001T000000Z.iso'
$SER = 'C:\Users\snowden\revix-iso\revix-os-serial.log'

# (bir marta) VM yaratish -- agar hali bo'lmasa:
& $VB createvm --name revix-os --ostype Debian_64 --register
& $VB storagectl revix-os --name IDE --add ide --controller PIIX4

# sozlash + ISO ulash
& $VB storageattach revix-os --storagectl IDE --port 0 --device 0 --type dvddrive --medium none
& $VB storageattach revix-os --storagectl IDE --port 0 --device 0 --type dvddrive --medium $ISO
& $VB modifyvm revix-os --memory 4096 --cpus 2 --firmware bios `
      --nic1 nat --audio-driver none --graphicscontroller vmsvga --vram 16 `
      --uart1 0x3F8 4 --uartmode1 file $SER --boot1 dvd --boot2 disk

# headless boot + dalil
& $VB startvm revix-os --type headless
& $VB controlvm revix-os screenshotpng 'C:\Users\snowden\revix-iso\revix-os-boot.png'

# interaktiv serial console uchun (doctor/make/pytest shu orqali bajarildi):
& $VB controlvm revix-os poweroff
& $VB modifyvm revix-os --uartmode1 tcpserver 2323
& $VB startvm revix-os --type headless
#   -> 127.0.0.1:2323 ga TCP bilan ulanib, serial console'da ishlanadi
```

### 5.2 Dalil

**FAKT — serial console** (`revix-os-boot-serial.log`):

```
ISOLINUX 6.04 20250413  Copyright (C) 1994-2015 H. Peter Anvin et al
  REVIX research appliance (live)
  Automatic boot in 5... 4... 3... 2... 1 second
[    5.176378] vmwgfx 0000:00:02.0: ... (kernel ishga tushdi)

Debian GNU/Linux 13 revix-appliance ttyS0
revix-appliance login: revix (automatic login)
Linux revix-appliance 6.12.107+deb13-amd64 #1 SMP PREEMPT_DYNAMIC
  Debian 6.12.107-1 (2026-08-29) x86_64
revix@revix-appliance:~$
```

**FAKT — screenshot** (`revix-os-boot.png`, `controlvm screenshotpng`):

```
Debian GNU/Linux 13 revix-appliance tty1
revix-appliance login: _
```

**FAKT — ulangan ISO'ning provenance'i.** Koordinator ham ISO'ni o'z
nusxasidan ulagani uchun men ulangan faylning hash'ini **o'zim**
tekshirdim (boshqa birovning so'ziga tayanmaslik uchun):

```
PS> (Get-FileHash 'C:\Users\snowden\revix-iso\revix-appliance-...iso').Hash
ccb08016908e82b0509cd0263555e5713dea4513abeb575c61b73d46da3b2e8d
PS> VBoxManage showvminfo revix-os
Location: "C:\Users\snowden\revix-iso\revix-appliance-trixie-20261001T000000Z.iso"
```

ya'ni boot qilingan narsa **aynan shu jurnalda qayd etilgan ISO**.

**TALQIN:** `09` §8 ning **G1** (build xatosiz tugaydi) va **G2** (ISO boot
bo'ladi) gipotezalari — **TASDIQLANDI**.

---

## 6. Qabul mezoni — `09` §4.1

### 6.1 `revix doctor --json` → **0 FAIL** ✅

**FAKT**, guest ichida, 4096 MB VM'da:

```
$ revix doctor --json > /tmp/doctor.json; echo $?
0
$ jq -r '.checks[].status' /tmp/doctor.json | sort | uniq -c
     14 PASS
      4 WARN
      0 FAIL
$ systemctl is-system-running
running
```

`09` §4 ning qabul mezoni — **birinchi boot'da 0 FAIL** — **BAJARILDI**.

**To'rtta WARN, har biri `09` §4.2/§4.3 da OLDINDAN aytilgan:**

```
WARN memory_headroom :: MemAvailable=3.5 GiB (MemTotal=3.8 GiB) -- zaxira yupqa
WARN swap_headroom   :: swap yo'q (SwapTotal=0)       <- live image, 09 §4.2
WARN cpu_governor    :: cpufreq interfeysi yo'q       <- 09 §4.3, HAL BO'LMAYDI
WARN kvm_access      :: /dev/kvm yo'q                 <- 09 §4.2, nested KVM kerak emas
```

`memory_headroom` **3072 MB li VM'da FAIL** edi (MemAvailable 2.7 GiB <
3.4 GiB kerak). **4096 MB** ga ko'tarilgach u WARN'ga tushdi va 0 FAIL
mezoni bajarildi. `09` §6.2 `-m 6144` ni tavsiya qiladi; **bu host'da
6144 MB MUMKIN EMAS** (jami 15.7 GiB, WSL2 10 GiB ushlab turadi, bo'sh
~2.6-3.4 GiB). Bu **host cheklovi**, image nuqsoni emas.

**Eng muhim PASS'lar — ular image'ning ILMIY sababini tasdiqlaydi:**

| `key` | Natija | Nimani tasdiqlaydi |
|---|---|---|
| `io_delegation` | **PASS** | `09` §8 **G5** — **fault class 6 (`io_stall`) OCHILDI**. Bu image'ning asosiy ilmiy sababi (§1) |
| `psi_cgroup`, `psi_host` | **PASS** | `09` §8 **G4** — arxiv kernel'ida `CONFIG_PSI=y` (bu §2.3 da GIPOTEZA edi) |
| `delegated_controllers` | **PASS** | `cpu memory pids` + `io` delegatsiyasi ishlaydi |
| `cgroup_write` | **PASS** | delegated subtree'ga yozish mumkin |
| `git_present`, `git_clean` | **PASS** | `09` §3.1 **R7** — `git clone --no-hardlinks` qarori ishladi; `run_meta.git_commit`/`git_dirty` to'ldiriladi |
| `leftover_state` | **PASS** | toza boot |
| `oomd` | **PASS** | `systemd-oomd` ataylab yo'q (§4.4) |

**O'lchangan cgroup holati:**

```
$ cat /sys/fs/cgroup/cgroup.subtree_control
cpu io memory pids                 <- `io` ROOTDAN PASTGA OCHILDI
$ systemctl is-active revix-io-delegate.service
active
$ systemctl show user@1000.service -p Delegate -p DelegateControllers
Delegate=yes
DelegateControllers=cpu io memory pids
$ systemctl is-system-running
running                            <- degraded EMAS
```

### 6.2 `make -C /opt/revix/revix all` → **rc=0, `-Werror` toza** ✅

**FAKT:**

```
$ cd /opt/revix && make -C revix all; echo $?
make: Entering directory '/opt/revix/revix'
cc -O2 -Wall -Wextra -Werror -std=c11 -pthread  -o sut sut.c
make: Leaving directory '/opt/revix/revix'
0
```

`-Werror` bilan qurildi va **birorta ogohlik chiqmadi** (chiqsa `-Werror`
build'ni to'xtatardi).

### 6.3 `python3 -m pytest tests/ -q` — 1045/1046 ✅ (bitta TIMING nosozligi ❌)

**FAKT — yakuniy image (`f495fcd`), guest ichida:**

```
$ cd /opt/revix && python3 -m pytest tests/ -q
1 failed, 1045 passed, 1 skipped in 88.09s (0:01:28)
FAILED tests/unit/test_prober.py::test_pacing_10hz_va_drift_yigmaydi
```

Yagona nosozlik — **pacing/timing** testi. Uning docstring'i o'zi aytadi:

> *"~2 s da probe soni 10 Hz ga yaqin, xato YIG'ILMAYDI va narx §8.2
> budjetida. … Absolut deadline'da chetlashish faqat **scheduler
> jitter**'i bo'lib qoladi."*

**TALQIN:** bu paket yoki kod kamchiligi **emas** — bu §7 dagi CHEKLOV'ning
bevosita natijasi: VirtualBox bu host'da **NEM** ustida ishlaydi (AMD-V
yo'q, chunki WSL2 ning Hyper-V'i uni egallagan), demak scheduler jitter
haqiqiy mashinadagidan katta. Aynan shu sababli §7 **bu VM'da birorta
timing o'lchovi haqiqiy emas** deydi — va test buni **mustaqil ravishda
tasdiqlaydi**.

**Bu test haqiqiy KVM yoki bare-metal host'da QAYTA o'tkazilishi kerak;
bu muhitda uning natijasi hal qiluvchi emas.**

#### Qanday qilib bu yerga yetildi — ikki bosqich

Birinchi o'lchov (oraliq image `67d54d5`) ikkita **paket kamchiligini**
fosh qildi:

```
$ cd /opt/revix && python3 -m pytest tests/ -q
3 failed, 938 passed, 2 skipped, 12 errors in 59.87s
```

Sabablar **uchta**, va ikkitasi **paket to'plamidagi kamchilik**:

| Soni | Sabab | Tuzatildi? |
|---|---|---|
| **12 error** | `ModuleNotFoundError: No module named 'gi'` (`revix/units.py:231`) — GLib main loop, D-Bus signal'lari uchun. BUTUN `tests/unit/test_units.py` yiqiladi | ✅ `python3-gi` qo'shildi (`f495fcd`) |
| **2 failed** | `test_zanjir_figura` — *"analysis.json -> `revix.figures` (matplotlib kerak)"* | ✅ `python3-matplotlib` qo'shildi (`f495fcd`) |
| **1 failed** | `test_pacing_10hz_va_drift_yigmaydi` — **TIMING** testi | ❌ **tuzatilmaydi**, §7 CHEKLOV'ga qarang |

**TALQIN:** 12 ta error eng jiddiysi edi — `python3-dbus` o'rnatilgani
`doctor` #15 ni qoniqtiradi, lekin `units.py` **PyGObject** ni alohida
talab qiladi, va usiz harness'ning **yadrosi** (transient unit yaratish,
`RestartSteps=` round-trip, `preflight()`/`teardown()`) umuman sinalmaydi.
`doctor` buni **ko'rmaydi**, chunki `gi` uning `REQUIRED_MODULES`
ro'yxatida yo'q. Ya'ni **0 FAIL doctor** va **ishlaydigan harness** —
ikki alohida narsa, va buni faqat `pytest` ko'rsatdi.

---

## 7. CHEKLOV — bu VM'da O'LCHOV O'TKAZIB BO'LMAYDI

Bu bo'lim **alohida** turadi, chunki uni e'tibordan chetda qoldirish
butun loyihani buzadigan xato bo'lardi.

**FAKT, `VBox.log` dan:**

```
HM: HMR3Init: Attempting fall back to NEM: AMD-V is not available
```

VirtualBox bu host'da **NEM (Windows Hypervisor Platform)** ustida
ishlaydi, **AMD-V** ustida emas — chunki **WSL2 ning Hyper-V'i**
virtualizatsiya kengaytmalarini **egallab olgan**. Guest ichida ham:

```
WARN kvm_access :: /dev/kvm yo'q (KVM modul yuklanmagan?)
```

**TALQIN — va bu QAT'IY QOIDA:**

> **Bu VM ichida olingan HECH QANDAY timing o'lchovi tadqiqot uchun
> HAQIQIY EMAS.**

`09` §6.1 aynan shu qoidani QEMU/TCG uchun yozgan edi: *«`revix doctor`
ning `kvm_access` tekshiruvi PASS bermaguncha guest'da birorta timing
o'lchovi o'tkazilmaydi. TCG'da faqat FUNKSIONAL smoke mumkin, va natija
TIMING sifatida YOZILMAYDI.»* **Shu qoida NEM'ga ham, so'zma-so'z,
qo'llanadi.**

Buning **o'lchangan** oqibati allaqachon ko'rindi: `pytest` dagi yagona
tuzatilmagan nosozlik —
`test_pacing_10hz_va_drift_yigmaydi` — bu **10 Hz prober'ning pacing
aniqligi** testi. U paket kamchiligi emas; u aynan emulyatsiya qilingan
vaqtning mahsuli.

`PREREGISTRATION.md` §6 (downtime va latency) va §1 (vaqt disiplinasi)
o'lchovlari shu VM'da **o'tkazilmaydi**. Ular uchun **bare-metal** yoki
hech bo'lmasa **haqiqiy KVM/AMD-V** host kerak, va u bu mashinada
WSL2 bilan **bir vaqtda** mavjud emas.

---

## 8. Image NIMA QILMAYDI — oshkora ro'yxat

Bu ro'yxat `09` §0 ning talabi: ISO — overclaiming eng oson bo'ladigan joy.

1. **Adaptive recovery engine YO'Q.** Arm C muzlatilmagan
   (`PREREGISTRATION.md` §13) va uni implement qiladigan **birorta kod
   yo'q**. Image «self-healing OS» **emas**.
2. **Bu Linux distributivi EMAS.** `README.md`: REVIX *«Linux distributivi
   emas, desktop theme emas, cybersecurity toolkit emas va Kali Linux
   moslashtirmasi emas»*. Uning nomi **«REVIX OS» EMAS**.
3. **Timing o'lchovi o'tkazmaydi** — §7. NEM/emulyatsiya ostida
   `PREREGISTRATION.md` §6 va §1 o'lchovlari haqiqiy emas.
4. **DVFS confound nazoratini ochmaydi.** `cpu_governor` WARN:
   *«cpufreq interfeysi yo'q (VM yoki driver yo'q)»*. `09` §4.3 buni
   oldindan aytgan: virtualizatsiya qilingan CPU'da `cpufreq` sysfs
   interfeysi **yo'q**, va bu **bare-metal** host'da hal bo'ladi.
   `PREREGISTRATION.md` §8.5 DVFS nazorati shu image bilan
   **yopilmaydi**.
5. **`systemd-oomd` armed desktop muhitini qayta ishlab chiqarmaydi.**
   oomd **ataylab** o'rnatilmagan (`09` §4.4), demak
   `04-novelty-statement.md` **C4** ning *«oomd armed jonli ish
   stansiyasida hech narsani buzmasdan»* da'vosini sinash **host'da**
   qoladi.
6. **ISO bit-reproducible EMAS** va bu **da'vo qilinmaydi** (`09` §3.2
   N1–N6). Qo'shimcha, shu build'da aniqlangan ikki yangi nuans:
   `mksquashfs` ning `SOURCE_DATE_EPOCH` semantikasi **clamp** (force
   emas, §2.11), va `-sort` 32758 yo'ldan **bittasini** qamrab olmaydi
   (§2.12).
7. **Ikki marta qurib taqqoslanmadi.** `09` §8 **G6** (kompozitsiya
   takrorlanadi) va **G7** (`diffoscope`) — **bu qadam bajarilmadi,
   sabab: har build ~20 daqiqa va vaqt boot dalilini olishga sarflandi.**
8. **Guard testi va dosing kalibratsiyasi guest ichida bajarilMADI.**
   `09` §6.2 ularni talab qiladi (`scripts/guard-test.sh`, keyin dosing),
   va `00-pilot-topologiya.md` §6 *«Retrofit qilinmaydi»* deydi.
   **Bu qadamlar bajarilmadi, sabab: §7 bo'yicha bu VM'da timing
   o'lchovi haqiqiy emas, demak kalibratsiya o'tkazish NOTO'G'RI
   natija berardi.** Ular haqiqiy KVM yoki bare-metal host'da
   **noldan** bajarilishi kerak.
9. **Birorta trial, birorta kampaniya o'tkazilmadi.** `revix driver`
   umuman ishga tushirilmadi.
10. **Installer yo'q, GUI yo'q, branding ulanmagan** (`09` §7 bo'yicha
    ataylab kechiktirilgan). Image **live** va **headless**.
11. **Ishonchsiz tarmoq uchun YAROQSIZ.** Parolsiz autologin **va**
    NOPASSWD `sudo` (§2.14). U tadqiqot appliance'i, **deployment
    artifact'i EMAS**.
12. **`build-fingerprint.json` ning `not_measured` ro'yxati BUILD
    PAYTIDAGI holatni aks ettiradi** (u yerda hali *«ISO boot
    qilinmadi»* deb turadi). Bu **to'g'ri**: fayl build momentida
    yoziladi. Boot va `doctor` natijalari **shu jurnalda** (§5, §6).

---
## 9. Xulosa — nima BAJARILDI, nima BAJARILMADI

### 9.1 BAJARILDI (har biri o'lchangan, buyrug'i va chiqishi yuqorida)

| `09` §8 | Gipoteza | Natija |
|---|---|---|
| **G1** | Build qadamlari xatosiz tugaydi | ✅ **TASDIQLANDI** — 10→50 hammasi RC=0, 18 m 28 s |
| **G2** | ISO boot bo'ladi | ✅ **TASDIQLANDI** — VirtualBox 7.2.2, serial log + screenshot |
| **G3** | `revix doctor` 0 FAIL | ✅ **TASDIQLANDI** — 14 PASS, 4 WARN, **0 FAIL** |
| **G4** | Arxiv kernel'ida `CONFIG_PSI=y` | ✅ **TASDIQLANDI** — `psi_host`, `psi_cgroup` PASS |
| **G5** | `io` delegatsiyasi → fault class 6 ochiladi | ✅ **TASDIQLANDI** — `io_delegation` PASS, `subtree_control` = `cpu io memory pids` |

Qo'shimcha: `09` §3.1 **R7** (image ichida haqiqiy `.git`) — `git_present`
va `git_clean` **ikkisi ham PASS**; `make -C revix all` **rc=0, `-Werror`
toza**; `pytest` **1045 passed**.

### 9.2 BAJARILMADI — va NEGA

| `09` §8 | Nima | Nega bajarilmadi |
|---|---|---|
| **G6** | Ikki marta qurib `manifest.txt` ni `diff` | **bajarilmadi, sabab: har build ~18–20 daqiqa, va vaqt boot dalilini olishga hamda topilgan 17 ta xatoni tuzatishga sarflandi** |
| **G7** | `diffoscope` bilan ikki ISO taqqoslash | **bajarilmadi, sabab: G6 bajarilmadi** (u G6 ning davomi) |
| **G8** | Kampaniya davomida markerlar o'zgarmasligi | **bajarilmadi, sabab: kampaniya umuman o'tkazilmadi** (§8.9). Lekin BUILD davomida ikkala marker ham o'lchandi va o'zgarmadi |
| **G9** | `scripts/guard-test.sh` guest ichida | **bajarilmadi, sabab: §7 — bu VM'da timing haqiqiy emas, demak guard kalibratsiyasi NOTO'G'RI natija berardi** |
| **G10** | `kvm_access` host'da PASS | **bajarilmadi, sabab: WSL2 ning Hyper-V'i AMD-V ni egallagan; VirtualBox NEM'ga tushdi (§7)** |

Shuningdek **bajarilmadi**: birorta trial, birorta kampaniya, dosing
kalibratsiyasi, `revix driver` ning ishga tushirilishi, `revix validate`.

### 9.3 Yakuniy, bir jumlalik halol bayon

> **Debian trixie + REVIX o'lchov harness'idan iborat reproducible
> research appliance qurildi (538 MiB, sha256 `ccb08016…`), VirtualBox'da
> boot bo'ldi, va uning ichida `revix doctor` 0 FAIL berdi, `make`
> `-Werror` bilan toza o'tdi, test suite'ining 1046 testidan 1045 tasi
> o'tdi. Bu image o'lchov o'tkazish uchun TAYYOR EMAS: unda timing
> haqiqiy emas (NEM emulyatsiyasi), guard kalibratsiyasi qilinmagan, va
> adaptive recovery engine umuman mavjud emas.**

---

## 10. Dashboard o'z-o'zidan ishga tushadi va `curl` image'da (agent/iso-dash)

Bu bo'lim §1–§9 dagi image'ga **ikkita amaliy kamchilikni** yopadi.
Orchestrator ularni ishlayotgan VM'da o'lchagan edi: (1) image'da `curl`
yo'q, demak dashboard guest ichidan sinalmaydi; (2) `revix/gui.py`
`/opt/revix/` da bor, lekin uni foydalanuvchi qo'lda
`--host 0.0.0.0 --allow-remote` bilan ishga tushirishi kerak. §0 va §8 dagi
barcha cheklovlar **o'zgarmaydi**.

### 10.1 Nima o'zgardi (uch fayl, boshqasiga tegilmadi)

| Fayl | O'zgarish |
|---|---|
| `iso/config.sh` | `PKGS_TOOLS` ga `curl` |
| `packaging/systemd/revix-dashboard.service` | **yangi** system unit |
| `iso/hooks/customize-20-systemd.sh` | unit'ni o'rnatadi va yoqadi; `MEASURE_USER`/`MEASURE_UID` unit'dagi qattiq `revix`/`1000` ga mos kelmasa build'ni **fail-closed** to'xtatadi |

**Qarorlar** (asoslari unit faylining o'z izohida, (1)–(6) bo'limlar):

- **System manager, `user@1000.service` ichida EMAS.** O'lchov qamrovi
  `user@1000.service` ostida; dashboard u yerda tug'ilsa uning RSS/CPU'si
  guard kuzatadigan scope'ga tushardi, va `revix-*` nomi
  `iso/lib/common.sh: REVIX_UNIT_GLOB` (`systemctl --user list-units
  "revix-*"`) ga mos kelib `require_clean_env`/doctor `leftover_state`
  uni **bloklovchi qoldiq** deb sanardi. System manager'da unit
  `system.slice` ostida, `systemctl --user` uni ko'rmaydi (xuddi
  `revix-io-delegate.service` va `revix-swapfile.service` kabi).
- **`User=revix`**: `cli.status_report()`/`collect_checks()` o'lchov
  foydalanuvchisining `systemctl --user` va `user@1000.service` cgroup'ini
  o'qiydi. `XDG_RUNTIME_DIR`/`DBUS_SESSION_BUS_ADDRESS` qo'lda beriladi.
- **Default bind = `127.0.0.1`** (`--allow-remote` **siz**). `gui.py`
  himoyasi chetlab o'tilmadi va `gui.py` o'zgartirilmadi.
- **Remote faqat kernel buyruq satri bilan**: `revix.dashboard=remote` ->
  `--host 0.0.0.0 --port 8787 --allow-remote`. Fayl emas, chunki image
  live (`/etc` RAM'da, qayta boot'da yo'qoladi).
- **Yengil sandbox**: `NoNewPrivileges`, `ProtectSystem=strict`,
  `PYTHONDONTWRITEBYTECODE=1`, `GIT_OPTIONAL_LOCKS=0`. `PrivateDevices`,
  `ProtectHome`, `ProtectControlGroups`, `PrivateTmp` **ataylab yo'q**:
  ular dashboard ko'rsatadigan doctor natijasini o'zgartirardi
  (soxta `kvm_access`/`cgroup_write`). `io` controller'iga tegilmadi.
- **O'lchovga yon ta'siri minimal**: `Nice=10`, `CPUWeight=20`,
  `OOMScoreAdjust=500`, `MemoryMax=384M`, `TasksMax=64`.

### 10.2 Build — o'lchangan

**FAKT.** Manba: `main` `ea79af9` + shu uch fayl = build commit
`e409858f5b7d1e2ff4a04896ac8f124e195ca3f5` (klon `/var/tmp/revix-src-dash`,
`core.fileMode=false`, `git status --porcelain` bo'sh). Barcha qadamlar
bitta `boot_id` (`4ea15279-acba-44ff-a533-6d7cd11924e5`) ichida; WSL guest
oldingi sessiya va shu sessiya orasida qayta ishga tushgan edi
(`fac1548b...` -> `4ea15279...`), shuning uchun holat qayta tekshirildi.

```
10-build-rootfs.sh    RC=0  2m33s   (apt kesh issiq; §3 da 14m37s edi)
20-record-manifest.sh RC=0  0m00s
30-make-squashfs.sh   RC=0  4m19s
40-make-iso.sh        RC=0  0m02s
50-fingerprint.sh     RC=0  0m02s
JAMI                        6m56s
```

```
iso        : revix-appliance-trixie-20261001T000000Z.iso
hajm       : 566 231 040 bayt (540 MiB)
sha256     : cc49ca27574132a27c79e835b00b674be154cc636fa6e334b33d2526db239763
manifest   : 61a8db3ac174a2a686c7898004c3d04875c97420abdac9200279c2dc5692933d
fingerprint: c0b769b94ee2ae1ae23e92fa0f9c16c3307ba1efd4ba6573f66fec21ae683ac1
git_commit : e409858f5b7d1e2ff4a04896ac8f124e195ca3f5   git_dirty_at_build: false
paket soni : 354
```

Oldingi image'ning manifest'i bilan farq (`diff`, tashlab yuborilgan
birinchi build'da o'lchangan; yakuniy build'ning manifest sha256'i u bilan
bir xil): **aniq ikki satr** — `curl 8.14.1-2+deb13u5` va
`libcurl4t64 8.14.1-2+deb13u5`. Paket soni 352 -> 354. Manifest sha256
o'zgardi (`05c92b0c...` -> `61a8db3a...`), ISO sha256 ham (`ccb08016...` ->
`cc49ca27...`) — bu kutilgan.

**TALQIN.** Image `git_commit` maydoniga `e409858` ni yozadi. Yakuniy
commit shu uch fayl bilan **bir xil** va shu jurnal bo'limini qo'shadi
(parent esa `main` ning keyingi uchi `9bdb6ae`; `e409858` dan keyin `main`
ga boshqa o'zgarishlar kirgan): `git diff e409858 <yakuniy> -- iso packaging`
**bo'sh** bo'lishi kerak (tekshirildi: 0 farq). Image va yakuniy commit
hash'i shu sababli **farq qiladi**, va image `main` ning `9bdb6ae` dagi
keyingi o'zgarishlarini (masalan `PREREGISTRATION.md` tuzatishlari) o'z ichiga
**olmaydi**.

**CHEKLOV.** Bundan oldingi, tashlab yuborilgan build (`8b80d50`, `main`
yangilanishidan oldin; sha256 `30651641...`) ham xuddi shu uch fayl bilan
boot bo'ldi va dashboard birinchi urinishda javob berdi; u hisobotga
**kirmaydi**, quyidagi barcha raqamlar **yakuniy** image'dan.

### 10.3 Boot va dashboard — o'lchangan (VirtualBox, 4096 MB, 2 vCPU, NEM)

**FAKT.** O'z VM'im `revix-os-dash` (`revix-os` va `snowden` ga tegilmadi;
`revix-os-dash` keyin o'chirildi). Birinchi urinish 4096 MB da Windows
`commit limit` (xato 1455) bilan yiqildi, chunki o'sha paytda `revix-os`
4 GiB ushlab turgan edi; `revix-os` to'xtagach 4096 MB boshlandi.

```
$ systemctl is-system-running            -> running   (ikkala boot'da)
$ systemctl --failed                     -> (bo'sh)
$ systemctl is-active revix-dashboard    -> active   ; is-enabled -> enabled
ControlGroup=/system.slice/revix-dashboard.service
User=revix  Nice=10  CPUWeight=20  OOMScoreAdjust=500  MemoryMax=402653184
TasksMax=64  NoNewPrivileges=yes  ProtectSystem=strict  NRestarts=0
$ ss -ltnH | grep 8787  -> LISTEN 127.0.0.1:8787          (default)
RSS ~30.9 MB; MemoryPeak 41 275 392 B (barcha sahifalar ochilgandan keyin)
```

`curl` guest **ichidan** (yangi paket):

```
$ curl --version | head -1   -> curl 8.14.1 (x86_64-pc-linux-gnu) libcurl/8.14.1 OpenSSL/3.5.7 ...
$ curl -sS -o /tmp/d.html -w "HTTP %{http_code} %{size_download} bytes\n" http://127.0.0.1:8787/
HTTP 200 8457 bytes
<title>REVIX &mdash; Boshqaruv paneli</title>
/system-health 200 14393B  /services 200  /resources 200  /logs 200
/settings 200  /about 200  /nonexistent 404   POST / -> 501 (faqat o'qish)
birinchi so'rov 4.3 s (PSI >= 2 s + doctor), keyingilari ~2 ms (kesh)
```

**FAKT — loopback default HOST'dan ko'rinmaydi** (kutilgan):

```
PS> Invoke-WebRequest http://127.0.0.1:8788/      (NAT forward 8788 -> guest 8787)
... The underlying connection was closed
```

**FAKT — remote rejim, ikki yo'l bilan:** (a) `/proc/cmdline` ustiga
`mount --bind` (unit'ning HAQIQIY `ExecStart`'i, qayta boot'siz);
(b) **haqiqiy boot**: `controlvm reset`, serial'da ISOLINUX menyusida
`Tab` va ` revix.dashboard=remote`. Ikkinchisida:

```
$ cat /proc/cmdline  -> BOOT_IMAGE=/live/vmlinuz boot=live components quiet
     console=ttyS0,115200n8 systemd.unified_cgroup_hierarchy=1 psi=1
     initrd=/live/initrd.img revix.dashboard=remote
$ ss -ltnH | grep 8787 -> LISTEN 0.0.0.0:8787
journal: revix-dashboard: REMOTE rejim (kernel cmdline revix.dashboard=remote):
         0.0.0.0:8787 -- autentifikatsiyasiz, ishonchsiz tarmoqda ISHLATMANG
         OGOHLIK: loopback BO'LMAGAN manzil -- tirik tizim holati tashqariga ochilgan
PS> Invoke-WebRequest http://127.0.0.1:8788/  -> HTTP 200, 8410 bayt,
    <title>REVIX &mdash; Boshqaruv paneli</title>      (Windows -> NAT -> guest)
$ systemctl is-system-running -> running
```

### 10.4 Qabul mezoni — `revix doctor` va `pytest`

**FAKT** (`revix doctor --json`, dashboard ISHLAYOTGANDA, ikki alohida boot):

```
boot 1: rc=0   14 PASS   4 WARN   0 FAIL
boot 2: rc=0   14 PASS   4 WARN   0 FAIL   (remote rejimda)
WARN: memory_headroom, swap_headroom, cpu_governor, kvm_access   (§6.1 dagi to'rtta bilan bir xil)
leftover_state: PASS -- qoldiq yo'q (unit ham, cgroup ham)
```

`09` §4.1 mezoni (**0 FAIL**) dashboard bilan **bajarildi**.

**FAKT — `require_clean_env` buzilmadi:** dashboard ishlayotganda o'lchov
foydalanuvchisining user manager'i unit'ni ko'rmaydi:

```
$ systemctl --user list-units "revix*" --all --no-legend ; echo rc=$?
(bo'sh)  rc=0                         # serial'dagi revix sessiyasi
$ sudo -u revix XDG_RUNTIME_DIR=/run/user/1000 systemctl --user list-units 'revix*' --all
(bo'sh)  rc=0
$ systemctl list-units 'revix*' --all   # SYSTEM manager
revix-dashboard.service  loaded active running
revix-io-delegate.service / revix-swapfile.service   loaded active exited
$ ls /sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/  -> revixlab/revixmon YO'Q
```

**FAKT — dashboard o'z doctor'i CLI bilan bir xil** (`/system-health`
sahifasi, sandbox'ga qaramay): `cgroup_write PASS`, `kvm_access WARN`,
`git_clean PASS (HEAD=e409858, toza)`, `leftover_state PASS`,
`io_delegation PASS`. Sahifalar yuklangandan keyin `git -C /opt/revix
status --porcelain` **bo'sh**.

**FAKT — `python3 -m pytest tests/ -q`** (image ichida, 4096 MB):

```
1 failed, 1089 passed, 1 skipped in 107.38s (0:01:47)
FAILED tests/unit/test_prober.py::test_pacing_10hz_va_drift_yigmaydi
  assert 87734 < 50000
```

Yagona nosozlik — §6.3/§7 da ma'lum bo'lgan timing testi (NEM). **Yangi
nosozlik yo'q.** (§6.3 da 1046 test edi; `main` testlar qo'shgani uchun
endi 1091.)

### 10.5 Dashboard xotira zaxirasini yeydi — o'lchangan, yupqa chegara

**FAKT.** `memory_headroom` doctor'da `MemAvailable >= 3 597 152 kB`
(3.43 GiB) talab qiladi, bundan kam bo'lsa FAIL. 4096 MB VM'da (MemTotal
4 016 012 kB):

```
doctor paytida MemAvailable: boot 1 = 3 657 304 kB (chegaradan +60 MB)
                             boot 2 = 3 668 688 kB (chegaradan +71 MB)
dashboard TO'XTATILGAN:  3 610 732 kB
dashboard ISHLAYOTGAN:   3 595 064 kB      -> farq ~ 15.7 MB
pytest'dan keyin (dashboard ishlayotgan): 3 591 252 kB
```

**TALQIN.** 4096 MB da zaxira **bir necha o'n MB**, dashboard esa shundan
~16 MB (RSS ~31 MB) oladi. `pytest`dan keyingi o'qish (3 591 252 kB)
chegaradan **past**: shu paytda doctor chaqirilmagani uchun uning FAIL
bergani **tasdiqlanmagan**, lekin raqam shuni ko'rsatadi. Ya'ni
**0 FAIL natijasi 4096 MB da dashboard va page-cache holatiga sezgir**;
`09` §6.2 tavsiyasi (6144 MB) shu sababli jiddiy. Bu image nuqsoni emas,
host cheklovi (§6.1).

### 10.6 CHEKLOV — oshkora

1. **Image ishonchsiz tarmoq uchun YAROQSIZ** (parolsiz autologin +
   NOPASSWD sudo, §8.11). Dashboard buni **o'zgartirmaydi**.
   **Default loopback**: image headless, brauzer yo'q, VirtualBox NAT
   forward guest loopback'iga emas NIC manziliga ulanadi — demak default'da
   dashboard **faqat guest ichidan** (`curl`) ko'rinadi, host brauzeridan
   emas. Bu ataylab olingan xarajat.
2. **Remote rejim** (`revix.dashboard=remote`): `0.0.0.0` (barcha IPv4
   interfeyslar), **autentifikatsiya yo'q, TLS yo'q**. NAT ortida faqat
   o'zingiz yaratgan port-forward ochiq; bridged/host-only tarmoqda shu
   tarmoqdagi **har kim** tirik tizim holatini (cgroup, PSI, unit, journal)
   o'qiydi. `gui.py` o'zi ham stderr'ga ogohlik yozadi, unit ham alohida
   satr yozadi.
3. Remote rejimni yoqish uchun foydalanuvchi ISOLINUX/GRUB'da buyruq
   satrini **qo'lda** tahrirlashi kerak: `iso/40-make-iso.sh` da alohida
   menyu yo'li **yo'q** (bu fayl shu ishning qamrovida emas). Sinalgan:
   ISOLINUX (BIOS) `Tab`. **GRUB (UEFI) yo'li sinalmadi.**
4. Trial davomida dashboard sahifasini ochish o'lchovga bosim qo'shadi
   (PSI >= 2 s, doctor 18 tekshiruv, throwaway cgroup) — `gui.py`
   dizayni; unit buni yo'q qila olmaydi. Qoida: trial paytida ochmang yoki
   `systemctl stop revix-dashboard`. Unit buni **avtomatik qilmaydi**.
5. Timing o'lchovi bu VM'da haqiqiy emas (§7): dashboard va `curl` bilan
   ham o'zgarmaydi.
6. Buyruqlar serial konsol orqali yuborildi; uzun satrlarning *aks-sadosi*
   buzilib ko'rinardi (kiritish emas, natija to'g'ri chiqdi). Skriptlar
   heredoc bilan guest'ga yozildi va bajarildi.

### 10.7 Yakuniy image — `main` `8400c3c` dan qayta qurildi (FAKT / TALQIN / CHEKLOV)

§10.2–§10.5 dagi image `main` `ea79af9` + shu uch fayldan edi. Undan keyin
`main` ga 13 s cap, V2, `host_clock_discontinuity`, `open_parameters`,
`preregistration/v1.12`, docs 13/14 va **boot menyusidagi ikkinchi band**
(`iso/40-make-iso.sh`, ISOLINUX va GRUB uchun, commit `a847de9`) kirdi.
Shu sababli image **qayta qurildi**; quyidagi raqamlar §10.2–§10.5 ning
o'rnini egallaydi (eskilari tarixiy yozuv sifatida qoladi).

**FAKT — build.** `/var/tmp/revix-src` (`origin` = Windows repo, `git fetch
origin main`, `checkout --detach`, `git clean -fdx`), `git rev-parse HEAD` =
`8400c3c660c6c9dcd08bb51656e445ad02e081ea`, `git status --porcelain` bo'sh.
Ekskluziv lock (`~/.revix-exclusive`) butun build davomida ushlab turildi va
chiqishda bo'shatildi. Har qadam oldidan `boot_id` + `/proc/1/stat` 22-maydon
solishtirildi; boshida va oxirida bir xil:
`boot_id=4ea15279-acba-44ff-a533-6d7cd11924e5 pid1_ticks=653523`.

```
10-build-rootfs.sh    RC=0  2m48s
20-record-manifest.sh RC=0  0m00s
30-make-squashfs.sh   RC=0  3m37s
40-make-iso.sh        RC=0  0m02s
50-fingerprint.sh     RC=0  0m02s
JAMI                        6m30s

iso        : revix-appliance-trixie-20261001T000000Z.iso
hajm       : 573 571 072 bayt (547 MiB)
sha256     : f086378f2b24728b3db02070738c245eed349be92aebdee06eedf5e6fcb59ee9
manifest   : 61a8db3ac174a2a686c7898004c3d04875c97420abdac9200279c2dc5692933d
fingerprint: a5bfbab4f086ac7416cbfe67d7d2d5335ed9823788eacaa07d6ccef4a175750a
git_commit : 8400c3c660c6c9dcd08bb51656e445ad02e081ea   git_dirty_at_build: false
paket soni : 354
```

`diff` oldingi image (`cc49ca27...`) manifest'i bilan: **IDENTICAL** (paket
to'plami o'zgarmadi; faqat repo mazmuni va menyu o'zgardi).
Nusxa `C:\Users\snowden\revix-iso-final\`; Windows tomonida
`Get-FileHash` shu sha256 ni berdi.

**FAKT — menyu** (ISOLINUX, serial capture, VirtualBox BIOS): ikki band bor:

```
REVIX research appliance (live)
REVIX research appliance (live) - dashboard reachable fr      <- kesilgan
Press [Tab] to edit options   Automatic boot in 5 seconds...
```

`Down` yuborilgach ikkinchi band teskari rangda (highlight) ko'rinadi
(escape-sequence capture), `Enter` undan boot qiladi.

**TALQIN / muammo (CHEKLOV).** ISOLINUX menyusi 80 ustunli serial'da bandni
~54 belgida **kesadi**: ekranda `[NO AUTH]` ogohlantirishi **ko'rinmaydi**
(`...reachable fr`). Ya'ni xavfsizlik ogohlantirishi aynan kerak joyda
yo'qoladi. Yechim `iso/40-make-iso.sh` da (shu ishning qamrovida emas):
yorliqni qisqartirish (masalan `REVIX live - dashboard on network [NO AUTH]`)
yoki `MENU WIDTH` ni oshirish. GRUB bandi sinalmadi (pastga qarang).

**FAKT — default band, 4096 MB** (o'z VM'im, `revix-os`/`snowden` ga
tegilmadi):

```
cmdline: ... psi=1 initrd=/live/initrd.img            (revix.dashboard YO'Q)
is-system-running: running ; systemctl --failed: bo'sh
revix-dashboard: active / enabled ; LISTEN 127.0.0.1:8787
curl -sS .../ : HTTP 200 8482 bytes ; <title>REVIX &mdash; Boshqaruv paneli</title>
systemctl --user list-units "revix*" --all : bo'sh
git -C /opt/revix log -1 -> 8400c3c660c6c9dcd08bb51656e445ad02e081ea ; status --porcelain: bo'sh
cd /opt/revix && python3 -c "import revix"  -> OK
revix doctor --json : rc=0  14 PASS  4 WARN  0 FAIL
  WARN: memory_headroom, swap_headroom, cpu_governor, kvm_access
  memory_headroom: MemAvailable 3 637 588 kB, talab 3 597 152 kB (+40 MB)
```

**FAKT — yangi band** ("dashboard reachable from host [NO AUTH]"):

```
cmdline: ... psi=1 revix.dashboard=remote initrd=/live/initrd.img
is-system-running: running ; --failed: bo'sh ; LISTEN 0.0.0.0:8787
journal: revix-dashboard: REMOTE rejim (kernel cmdline revix.dashboard=remote):
         0.0.0.0:8787 -- autentifikatsiyasiz, ishonchsiz tarmoqda ISHLATMANG
         OGOHLIK: loopback BO'LMAGAN manzil -- tirik tizim holati tashqariga ochilgan
revix doctor --json : rc=0  14 PASS  4 WARN  0 FAIL   (MemAvailable 3 648 344 kB, +51 MB)
PS> Invoke-WebRequest http://127.0.0.1:8788/    (NAT forward 8788 -> guest 8787)
Windows -> NAT -> guest : HTTP 200, 8482 bytes, <title>REVIX &mdash; Boshqaruv paneli</title>
```

Bu foydalanuvchiga haqiqatan kerak bo'lgan yo'l: ISO ni boot qiladi, ikkinchi
bandni tanlaydi, brauzerda ochadi.

**FAKT — 6144 MB** (`modifyvm --memory 6144`; Windows commit limit bu safar
yetarli bo'ldi, `revix-os` ishlamayotgan edi), default band:

```
MemTotal 6 074 252 kB ; MemAvailable 5 706 988 kB
revix doctor --json : rc=0  15 PASS  3 WARN  0 FAIL
  WARN: swap_headroom, cpu_governor, kvm_access        (memory_headroom endi PASS)
  memory_headroom: avail_kb=5 695 240, talab 3 597 152
is-system-running: running ; --failed: bo'sh ; dashboard active, HTTP 200 (8619 bytes)
```

**TALQIN.** 4096 MB da zaxira (+40...+51 MB) §10.5 dagidan (+60...+71 MB) ham
**yupqaroq** chiqdi (repo va main kodi kattaroq). 0 FAIL saqlandi, lekin
page-cache'ga sezgir; 6144 MB da `memory_headroom` PASS va WARN soni
4 -> 3. Pilot/o'lchov uchun 6144 MB ni ishlating (host ruxsat bersa).

**CHEKLOV — sinalmadi:**
1. **GRUB/UEFI** (ikkala band) — faqat BIOS/ISOLINUX sinaldi; GRUB menyusi
   kodda bor, lekin boot qilinmadi.
2. 6144 MB da faqat **default** band boot qilindi (yangi band emas).
3. `pytest` bu yakuniy image'da **qayta ishga tushirilmadi** (§10.4 natijasi
   `ea79af9` image'iga tegishli).
4. Trial yoki yuk ostida dashboard ta'siri o'lchanmadi (§10.6.4 o'zgarmaydi).
5. Timing o'lchovi NEM ostida haqiqiy emas (§7).
6. Image ishonchsiz tarmoq uchun YAROQSIZ (parolsiz autologin, NOPASSWD sudo),
   yangi band esa autentifikatsiyasiz va TLS'siz tinglaydi.

**FAKT — tozalash.** VM `revix-os-dash` o'chirildi; lock bo'shatildi
(VM fazasi 10:45:12Z-10:50:57Z; `boot_id` fazaning boshida va oxirida
`4ea15279...`). Eski nusxalar o'chirildi: `C:\Users\snowden\revix-iso-dash\`
(butunlay) va `C:\Users\snowden\revix-iso\*.iso` (eski `ccb08016...` image).
DIQQAT: `revix-os` VM (holati `aborted`) aynan shu o'chirilgan ISO'ni DVD
sifatida ulagan edi — uni qayta ulash kerak
(`C:\Users\snowden\revix-iso-final\...iso`).
