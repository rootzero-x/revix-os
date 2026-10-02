# 09 — Reproducible research appliance image: build dizayni

**Holat:** bu hujjat **dizayn**. Hech qanday image qurilmadi, hech qanday ISO
yozilmadi, hech qanday guest boot qilinmadi. `iso/` va `packaging/` dagi
skriptlar **yozildi va syntax-check qilindi**, lekin **bajarilmadi, sabab:
guard kalibratsiyasi davom etmoqda** (`experiment/guard-recal` shu WSL guest
ichida jonli o'lchov o'tkazmoqda; `debootstrap`/`mmdebstrap` darajasidagi
build guest'ning xotira, disk va CPU'sini to'yintirib o'sha o'lchovni buzadi).

Hujjat loyihaning belgilari bilan ishlaydi: **FAKT** (o'lchangan, buyrug'i
keltirilgan), **GIPOTEZA** (hali o'lchanmagan), **TALQIN** (xulosa),
**CHEKLOV** (bu muhitda ta'minlanmaydigan narsa).

---

## 0. Qamrov — bu birinchi ekranda turadi, footnote'da emas

**REVIX'da adaptive recovery engine YO'Q.**

- `README.md` → *"Loyiha nima EMAS"*: *"REVIX adaptiv recovery ixtiro
  qilmaydi"* va *"Bu shuningdek **Linux distributivi emas**, desktop theme
  emas, cybersecurity toolkit emas va Kali Linux moslashtirmasi emas."*
- `PREREGISTRATION.md` §0: P1 **REVIX arm C, failure classifier, action
  selector, `Repairs()` matritsasi** haqida hech qanday da'vo qilmaydi.
- `PREREGISTRATION.md` §13: **Arm C (REVIX) siyosati va gate chegaralari
  muzlatilMAGAN** — ular keyinchalik aniqlanadi va **o'z pre-registration'ini**
  talab qiladi.
- `docs/research/04-novelty-statement.md`: *"Biz adaptive recovery engine
  ixtiro qildik"* — **da'vo qilinMAYDI**.
- `revix/` da arm C ni implement qiladigan modul **yo'q** (`README.md`
  komponent jadvali: `Arm C (REVIX engine) — ⏳`).

**Shundan kelib chiqadigan yagona halol ta'rif:**

> Bugun qurilishi mumkin bo'lgan image = **Debian** (asos) **+ REVIX o'lchov
> harness'i**. Bu **reproducible research appliance** — benchmark'ni ko'chirib
> yurish uchun transport. Bu **operatsion tizim hissasi EMAS**, **adaptiv
> self-healing OS EMAS**, va uning nomi **"REVIX OS" EMAS**.

Image ichida `revix` nomi faqat harness'ga tegishli. Agar bir kun arm C
yozilsa, u ham shu harness'ning moduli bo'ladi — image'ning o'zi hech qachon
"recovery engine" bo'lmaydi.

**NEGA bu birinchi ekranda:** ISO — aynan overclaiming eng oson bo'ladigan
joy. Bootable image'ga nom berilishi bilan u "distributiv" deb o'qiladi, va
`04-novelty-statement.md` ning "Hissa NIMA EMAS" bo'limi (maqolada
Introduction'da turadi, Limitations'da emas) bir zumda buziladi. Loyihaning
butun ishonchliligi da'vo qilmaslikka tayanadi.

---

## 1. Unda image NEGA kerak — haqiqiy motivatsiya

Motivatsiya "distributiv chiqarish" emas. U `00-pilot-topologiya.md` §4 —
**privilegiya yuzasi** — dan to'g'ridan-to'g'ri kelib chiqadi.

§4 ro'yxatlaydi: root **faqat** quyidagilar uchun kerak — `io` controller /
`io.max`; `dm-delay`/`dm-flakey`; `tc netem`; cgroup `cpuset` pinning;
`scaling_governor=performance`; `drop_caches`; paket o'rnatish; harness'ni
**system slice**ga ko'chirish. Va §4 ning prinsipi:

> **"root kerak" = "guest'ga tegishli."**

`PREREGISTRATION.md` §0 shu sababli quyidagilarni P1 qamrovidan **chiqarib
tashlaydi**:

| P1 da yo'q | Nega yo'q | Guest nimani ochadi |
|---|---|---|
| Nazorat qilinadigan IO stall = **fault class 6 (`io_stall`)** | `io` controller delegated emas (`07` §1.3 #4: `cgroup.subtree_control` = `cpu memory pids`) | guest'da root → `io` ni `subtree_control` ga yozish → `io.max` ishlaydi |
| **12 s dan uzoq sustained pressure** | `systemd-oomd` ning 20 s sharti (`00` §3.1) oynani ≤12 s ga qisadi | guest'da oomd siyosati **bizning qo'limizda**; desktop sessiyasi yo'q → yo'qotiladigan narsa yo'q |
| **`W_stab = 60 s`** to'liq stabilizatsiya oynasi | pilot `W_stab_pilot = 8 s` bilan cheklangan — ≤12 s pressure oynasi ichiga sig'ishi kerak (`02-guard-kalibratsiyasi.md` §7) | uzun oyna uzun pressure'ni talab qiladi, u esa guest'ni talab qiladi |
| host-wide `/proc/pressure` javobi | host = ish stansiyasi; uni pressure ostiga qo'yish mumkin emas | guest'ning host'i = guest'ning o'zi |
| `scaling_governor=performance` | root (`07` §1.3 #12: bu muhitda `cpufreq` umuman yo'q) | **ochilMAYDI** — §4.3 ga qarang, bu CHEKLOV |

### 1.1 Ikkinchi, mustaqil motivatsiya: **bu host o'zini qayta ishga tushiradi**

Bu "qulaylik" emas. Bu **feasibility gate**, va u ikki xil nosozlik
rejimida, bir-biridan mustaqil ravishda **o'lchangan**.

**Rejim A — init-only restart (`boot_id` O'ZGARMAYDI).**
**FAKT**, `PREREGISTRATION.md` §16.11 (49 s oraliq bilan ikki o'qish; uchta
agent mustaqil ravishda shu rejimni ko'rdi):

| o'lchov | 1-o'qish | 2-o'qish |
|---|---|---|
| `boot_id` | `ca4e5bab-…` | **AYNAN BIR XIL** |
| `/proc/uptime` | `1975.34` s | `2024.34` s (+49.0 s, normal) |
| `/proc/1/stat` 22-maydon | `191289` tick | **`201467`** tick (+101.78 s) |
| PID 1 yoshi | `62.46` s | **`9.68` s — ORQAGA KETDI** |

**FAKT**, `07-wsl-muhit-tekshiruvlari.md` §4.4 (alohida o'lchov): oxirgi
`wsl.exe` klienti chiqqandan ≈10–15 s keyin distro to'xtaydi; PID 1 qayta
ishga tushadi (`etimes` 1 s → 7 s, user manager PID 241 → 238), barcha
transient unit'lar **o'ladi** (`revixselftestec07-persist.service` →
`LoadState=not-found`), `boot_id` esa **o'zgarmaydi**. Bo'sh cgroup
kataloglari qoladi.

**Rejim B — to'liq VM restart (`boot_id` O'ZGARADI).**
**FAKT, koordinator o'lchagan** (men bu o'lchovni bajarmadim va qayta
tekshirmadim — provenance aniq bo'lishi uchun shunday yozildi): uptime
`2024` s dan `544` s ga tushdi, va **o'sha paytda `boot_id` o'zgardi**.
Bu `PREREGISTRATION.md` §16.11 ning *"O'LCHANMADI: to'liq WSL VM
restart'ida `boot_id` o'zgaradimi"* bandini **yopadi**.

**TALQIN:** ikkala rejim ham `--collect` va transient unit'larni **trial
o'rtasida o'ldiradi**. 120 trial'lik kampaniya (`00` §5: ~75 s/trial →
**~2.5 soat**) WSL'da to'g'ridan-to'g'ri o'tkazilsa, uning **o'z host'i
tomonidan buzilishi haqiqiy ehtimol** — va buzilgan kampaniya qayta
takrorlanmaydi, chunki P1 ma'lumotlari confirmatory analizga qo'shilmaydi
(`PREREGISTRATION.md` §13). QEMU guest **bizning nazoratimizda** va o'zini
qayta ishga tushirmaydi.

Shuning uchun image **imkoniyat** emas, **risk kamaytirish**: u
privilegiyali tier'lardan (§1 jadvali) **mustaqil** ravishda asoslanadi.

#### Ikki detektor, ikkita ko'r nuqta — IKKISI HAM yoziladi

| Detektor | Nimani ushlaydi | Ko'r nuqtasi | Holati |
|---|---|---|---|
| `boot_id` | **Rejim B** (to'liq VM restart) | Rejim A'da **o'zgarmaydi** → init restart'ni ko'rmaydi | `PREREGISTRATION.md` §14.6(5) — **muzlatilgan** |
| `pid1_starttime_ticks` (`/proc/1/stat` 22-maydon) | **Rejim A** (init-only restart) | VM restart'da ham o'zgaradi, lekin yangi boot'ni eski boot'dan ajratmaydi | `PREREGISTRATION.md` §16.11 ning "majburiy qo'shimcha shart"i; `04-driver-va-analiz-shartnomasi.md` §1.4 `guest_generation` |

`PREREGISTRATION.md` §16.11 xulosasini aynan takrorlaymiz: *"§14.6(5)
invarianti **zarur, lekin YETARLI EMAS**"*, va qo'shimcha marker uni
*"**almashtirmaydi**, uni **to'ldiradi**"*.

**Shundan image uchun kelib chiqadigan talab:** guest ichida ishlaydigan
harness **ikkala** markerni ham `run_meta` da va **har** `env_snapshot` da
yozishi shart (`04` §1.1 v1.2 allaqachon shunday talab qiladi). Image bu
talabni **yengillashtirmaydi** — guest restart qilmaydi degan **GIPOTEZA**
markerlarni olib tashlash uchun asos emas. Teskarisi: markerlar aynan shu
gipotezani **o'lchaydigan** vosita (§8 G8).

> Bu `revix/` kodiga o'zgartirish **emas** va men `revix/` ga tegmadim —
> bu `09` ning image'dan kutadigan xatti-harakati, va u shartnomada
> allaqachon mavjud.

### 1.2 Uchinchi sabab: fayl tizimi

`07` §7.2 (**FAKT**): repo `/mnt/c` da, u `9p`/drvfs, **98% to'la,
10 G bo'sh**; append latency ext4 dan ~100× sekin. 10 Hz prober va
psi_sampler aynan shu yo'lga yozadi. Guest'ning o'z ext4 root'i bu
muammoni ham olib tashlaydi.

### 1.3 Xulosa

Reproducible guest image — `docs/research/04-novelty-statement.md`
**C4** ("Portativ, privilegiyasiz o'lchov dizayni") ning amaliy davomi:
benchmark'ni **ko'chirma** qiladi va **privilegiyali tier'larni erishiladigan**
qiladi. Bu haqiqiy tadqiqot deliverable'i. Lekin u **engine emas**.

---

## 2. Build chain

Spetsifikatsiya talab qilgan zanjir: **source → build → rootfs → kernel →
init/systemd → bootloader → ISO**. Har qadam uchun aniq vosita va `NEGA:`.

| # | Qadam | Vosita | Natija |
|---|---|---|---|
| 0 | privilegiyali tayyorgarlik (bir marta) | `apt-get`, `usermod`/`setfacl` | `iso/00-host-prepare.sh` |
| 1 | source | `git clone --no-hardlinks <repo> --branch <commit>` | `/opt/revix` ichiga mustaqil repo |
| 2 | rootfs | **`mmdebstrap --mode=unshare`** | `rootfs/` (root'siz) |
| 3 | kernel | Debian arxivdan `linux-image-amd64` (**o'z kernel qurilMAYDI**) | `vmlinuz` + `initrd.img` |
| 4 | initramfs | `initramfs-tools` + `live-boot` | live rootfs'ni squashfs ustidan ko'taradi |
| 5 | init/systemd | Debian **trixie** systemd (257) | `systemd_version ≥ 254` PASS |
| 6 | rootfs → tasvir | `mksquashfs` (determinizm bayroqlari bilan) | `live/filesystem.squashfs` |
| 7 | bootloader | `grub-mkstandalone` (EFI) + `isolinux` (BIOS) | hybrid boot |
| 8 | ISO | **`xorriso -as mkisofs`** | `revix-appliance-<ts>.iso` |
| 9 | manifest + fingerprint | `dpkg-query`, `sha256sum` | `manifest.txt`, `build-fingerprint.json`, `SHA256SUMS` |

### 2.1 Qadam 2 — NEGA `mmdebstrap`, NEGA `live-build` emas

Bu uchta haqiqiy qarorning **birinchisi**.

`NEGA:` `live-build` (`lb config && lb build`) Debian live image'ning
an'anaviy yo'li va ko'proq yurilgan, lekin u **root talab qiladi**: `lb build`
chroot'ni egalik, `mknod` va mount bilan quradi. `mmdebstrap --mode=unshare`
esa **user namespace** ichida ishlaydi va **umuman root talab qilmaydi**
(`uidmap` paketi va `/proc/sys/kernel/unprivileged_userns_clone` yoqilgan
bo'lishi kifoya).

Bu `00-pilot-topologiya.md` §4 prinsipining to'g'ridan-to'g'ri qo'llanilishi:
*"barcha privilegiyali operatsiyalar **bitta** qisqa, ko'rib chiqiladigan setup
skriptida, sessiyaga bir marta ishlaydi va **har trial'da hech narsa
qilmaydi**"*. `mmdebstrap` bilan build vaqtidagi privilegiyali operatsiyalar
soni **nolga** tushadi — `00-host-prepare.sh` faqat **paket o'rnatish** va
**`/dev/kvm` ruxsati** uchun qoladi, va ikkisi ham `00` §4 / `INSTALLATION.md`
§4 ning ro'yxatida allaqachon "root kerak, bir marta" deb yozilgan.

Qo'shimcha sabablar:
- `mmdebstrap` `SOURCE_DATE_EPOCH` ni **tushunadi** va apt'ni shunga mos
  sozlaydi (`--variant`, `--hook-dir`, `--setup-hook`/`--customize-hook`).
- U `snapshot.debian.org` manzilini oddiy `deb` satri sifatida qabul qiladi,
  ya'ni pinning hech qanday wrapper talab qilmaydi.
- Hook'lar **ko'rinadigan shell fayllar** — `live-build` ning `config/hooks/`
  daraxtiga qaraganda ko'rib chiqish yuzasi kichik.

`CHEKLOV (qabul qilingan narx):` `mmdebstrap` **live image qurmaydi**. U
faqat rootfs beradi. Demak **biz** `live-boot`, `mksquashfs`, bootloader va
`xorriso` ni o'zimiz yig'amiz (qadam 4, 6, 7, 8) — `live-build` buni avtomatik
qiladi. Bu ko'proq kod va ko'proq xato ehtimoli; buning o'rniga olinadigan
narsa — **root'siz build** va **ko'rinadigan determinizm bayroqlari**. Qaror
loyiha prinsipi foydasiga qabul qilindi.

### 2.2 Qadam 5 — NEGA Debian trixie, NEGA Kali emas, NEGA bookworm emas

Bu ikkinchi haqiqiy qaror.

`NEGA:` `INSTALLATION.md` §2 systemd uchun **≥ 254** chegarasini qo'yadi va
sababini aniq aytadi: *"`RestartSteps=` va `RestartMaxDelaySec=` v254
(2023-avgust) dan mavjud. **Baseline B butunlay shunga tayanadi**: `RestartSteps=`
bo'lmasa systemd native exponential backoff yo'q va kuchli baseline
yo'qoladi."*

| Nomzod | systemd | Qaror |
|---|---|---|
| Debian **bookworm** (12) | **252** | ❌ **< 254** → `RestartSteps=` yo'q → Baseline B o'lchanmaydi → image ilmiy jihatdan foydasiz |
| Debian **trixie** (13) | **257** | ✅ **tanlandi** |
| Kali Rolling | 257 (`07` §8: `257 (257.7-1)`) | ❌ reproducibility sababidan — pastga qarang |
| Debian sid | ≥257, lekin harakatlanadi | ❌ snapshot bo'lmasa muzlatilmaydi; trixie ham snapshot bilan muzlatiladi |

Kali rad etilishining **ikki** sababi, ikkisi ham texnik:

1. Kali'da `snapshot.debian.org` ekvivalenti **yo'q** — vaqt bo'yicha
   indekslangan, o'zgarmas arxiv yo'q. Rolling mirror ustidan qurilgan image
   ikki hafta ichida boshqa paket to'plamini beradi. Bu §3 ning butun
   reproducibility shartini buzadi.
2. `README.md` ochiq aytadi: REVIX **"Kali Linux moslashtirmasi emas"**. Kali
   asos qilib olinsa, bu inkor hujjatda qoladi, lekin artifact'da buziladi.

`FAKT (provenance):` shu mashinada o'lchangan muhit — Kali Rolling WSL2,
systemd 257 (`07` §8). `CHEKLOV:` demak image Debian trixie'da qurilsa,
**o'lchov muhiti o'zgaradi**: boshqa kernel, boshqa paket to'plami. `07`
§"Xulosa — build tartibi" allaqachon aytadi: *"Har qanday pressure
eksperimentidan oldin guard testi (00 §6 qadam 3) va pressure dosing
kalibratsiyasi (qadam 4) bu mashinada QAYTA bajarilishi shart. 'Retrofit
qilinmaydi.'"* **Shu qoida image'ga ham qo'llanadi: guest ichida guard testi
va dosing kalibratsiyasi NOLDAN qayta bajariladi.** Image host'ning
kalibratsiyasini meros qilib olmaydi.

### 2.3 Qadam 3 — NEGA o'z kernel qurilmaydi

`NEGA:` harness kernel'dan faqat **ikki** narsani talab qiladi:
`CONFIG_PSI=y` (Linux ≥ 4.20) va cgroup v2 (`INSTALLATION.md` §2). Debian'ning
`linux-image-amd64` paketi ikkisini ham beradi. O'z kernel qurish:
(a) build vaqtini soatlarga cho'zadi; (b) **yangi o'lchanmagan o'zgaruvchi**
kiritadi (scheduler, mm, PSI accounting yo'llari); (c) `PREREGISTRATION.md`
§15 "muhit fingerprint" ni arxivdan tekshirilmaydigan qiymatga bog'laydi.
Arxiv kernel'i `manifest.txt` da versiyasi va `sha256`i bilan qayd etiladi —
bu yetarli provenance.

`CHEKLOV:` `CONFIG_PSI=y` ni **biz tasdiqlamadik**. Debian kernel'lari uni
yoqadi deb **ishoniladi**, lekin bu **GIPOTEZA** bo'lib qoladi: o'lchovi —
guest ichida `revix doctor` ning `psi_host` va `psi_cgroup` tekshiruvlari
(`revix/cli.py`, `EXPECTED_CHECK_KEYS` #5, #6). Ular PASS bersa gipoteza
tasdiqlanadi; bermasa image yaroqsiz.

### 2.4 Qadam 7–8 — bootloader va ISO

`NEGA (hybrid boot):` QEMU'ni ham BIOS (`-bios` default SeaBIOS), ham UEFI
(`-bios OVMF.fd`) rejimida ishlatish mumkin, va benchmark **portativ** bo'lishi
kerak (C4). `grub-mkstandalone` EFI yo'lini (`EFI/boot/bootx64.efi`),
`isolinux`/`syslinux` BIOS yo'lini beradi; `xorriso -as mkisofs
-isohybrid-mbr` ikkisini bitta image'ga yig'adi.

`NEGA (xorriso, genisoimage emas):` `xorriso` `--modification-date=` ni
qabul qiladi (ISO9660 Primary Volume Descriptor'dagi timestamp'larni
`SOURCE_DATE_EPOCH` ga qotirish uchun **majburiy**), deterministik
tartiblashni qo'llab-quvvatlaydi, va `live-build` ning o'zi ham aynan uni
chaqiradi. `genisoimage` eskirgan va `--modification-date` ekvivalenti yo'q.

---

## 3. Reproducibility — eng muhim bo'lim

`PREREGISTRATION.md` §14.4 `run_meta` ning majburiy maydonlarini
(`preregistration_sha256`, `git_commit`, `git_dirty`, `rng_seed`, `boot_id`,
har unit'ning **tirik** `systemctl show` dump'i) bitta sabab bilan asoslaydi:
**reproducibility**. `scripts/sync-to-ext4.sh` ham shu sababni yozadi:
*".git bo'lmasa o'lchov tekshirilishi mumkin bo'lgan commit'ga bog'lanmaydi."*

Image uchun bu shartni **kengaytiramiz**: run faqat kodga emas, **butun
muhitga** bog'lanishi kerak.

### 3.1 Ta'minlanadigan narsalar (dizayn xususiyati — har biri hali GIPOTEZA)

| # | Xususiyat | Mexanizm | Tekshirish |
|---|---|---|---|
| R1 | **Pinned arxiv** | `deb http://snapshot.debian.org/archive/debian/<SNAPSHOT_TS>/ trixie main` + `Acquire::Check-Valid-Until=false` | `manifest.txt` sarlavhasida `SNAPSHOT_TS` |
| R2 | **Aniq paket manifest'i** | `dpkg-query -W -f='${Package}\t${Version}\t${Architecture}\n'` rootfs ustida, `LC_ALL=C sort` | `manifest.txt` + uning `sha256` |
| R3 | **`SOURCE_DATE_EPOCH`** | bitta joydan (`iso/config.sh`), `mmdebstrap`, `mksquashfs -all-time -mkfs-time`, `xorriso --modification-date` ga beriladi | `build-fingerprint.json` |
| R4 | **Deterministik tartib** | `find … \| LC_ALL=C sort` → `mksquashfs -sort` fayli; `tar --sort=name --numeric-owner --owner=0 --group=0` | `sortfile.txt` commit qilinadi? **yo'q** — fingerprint'da sha256 bilan qayd etiladi |
| R5 | **Nondeterminizm normalizatsiyasi** | `customize-90-normalize.sh`: `/var/log/*`, `/var/cache/apt/*`, `/var/lib/apt/lists/*` o'chiriladi; `/etc/machine-id` **bo'shatiladi**; SSH host kalitlari o'chiriladi; `/etc/resolv.conf` tiklanadi | hook'ning o'zi |
| R6 | **Build fingerprint** | `build-fingerprint.json`: `SNAPSHOT_TS`, `SOURCE_DATE_EPOCH`, suite, `git_commit`, `preregistration_sha256`, vosita versiyalari (`mmdebstrap`, `mksquashfs`, `xorriso`, `dpkg`), `manifest_sha256`, `iso_sha256` | `SHA256SUMS` yonida commit qilinadi |
| R7 | **Kodning commit'ga bog'lanishi** | image ichida **haqiqiy `.git`** (§5) → `doctor` ning `git_present`/`git_clean` PASS → `run_meta.git_commit`/`git_dirty` to'ldiriladi | `revix doctor --json` |
| R8 | **Frozen hujjatga bog'lanish** | `sha256sum PREREGISTRATION.md` fingerprint'ga yoziladi va image ichidagi nusxa bilan taqqoslanadi | `build-fingerprint.json` |

### 3.2 Bit-darajada ta'minlanMAYDIGAN narsalar — va nega

Bu bo'lim ataylab batafsil. **Debian live image bugun bit-reproducible EMAS**,
va buni yashirish §3.1 ni ham ishonchsiz qiladi.

| # | Nima | Nega bit-identik bo'lmaydi |
|---|---|---|
| N1 | **initramfs** | `update-initramfs` cpio'ni ishga tushgan tizimdagi modul to'plami va `/etc/initramfs-tools/conf.d` holatidan yig'adi. Modul tartibi `find` natijasiga, `resume=` UUID'i esa build host'ining swap'iga bog'liq bo'lishi mumkin. `SOURCE_DATE_EPOCH` gzip header'ini tuzatadi, cpio **tartibini** tuzatmaydi. Bu Debian'ning **ochiq** reproducible-builds muammosi; biz hal qilmaymiz |
| N2 | **`/var/lib/dpkg/*`** | `status`, `available`, `*.list` fayllari o'rnatish **tartibiga** bog'liq, va apt bog'liqlik yechimi versiya o'zgarsa tartibni o'zgartiradi. Pinned snapshot bu riskni kamaytiradi, **yo'q qilmaydi** |
| N3 | **maintainer script yon ta'siri** | `ldconfig` cache (`/etc/ld.so.cache`), `systemd` journal catalog (`/var/lib/systemd/catalog/database`), `fontconfig`/`mandb` cache'lari — hammasi build paytida generatsiya qilinadi va ichki tartibi yoki timestamp'i barqaror emas. Ba'zilarini o'chiramiz (R5), lekin **hammasini emas** — ba'zilari boot'da kerak |
| N4 | **`machine-id`** | Image'da **bo'sh** qoldiriladi (bu to'g'ri xatti-harakat: `systemd` birinchi boot'da generatsiya qiladi). Demak **image** bir xil bo'lsa ham **booted tizim** bir xil emas. Image reproducibility'si va runtime identity'si ikki alohida narsa |
| N5 | **GRUB EFI binari** | `grub-mkstandalone` ichiga memdisk cpio joylaydi; `SOURCE_DATE_EPOCH` bilan deterministik bo'lishi **kutiladi**, lekin biz tekshirmadik |
| N6 | **Kernel va har bir `.deb` ning o'zi** | Ular Debian tomonidan qurilgan. Ularning reproducible'ligi **Debian'ning da'vosi**, bizning emas. Biz faqat **aynan o'sha binarlarni** olganimizni (R2 + sha256) ko'rsatamiz |
| N7 | **`snapshot.debian.org`** | Uchinchi tomon xizmati. Uning mavjudligi va retention'i bizning nazoratimizda emas. Pinned URL o'zgarmas **bo'lishi kerak**, lekin bu **kafolat emas** |

**Shuning uchun da'vo quyidagicha darajalanadi:**

| Da'vo | Daraja | Tekshirish usuli |
|---|---|---|
| "Paket to'plami qayd etilgan va tekshiriladi" | **da'vo qilinadi** (R2 + R6 bilan machine-checkable) | `manifest.txt` ni qayta qurilgan rootfs bilan `diff` |
| "Image kompozitsiyasi takrorlanadi" | **da'vo qilinadi, shartli** (R1 + R3 + R4; N7 ga bog'liq) | ikki marta qurib `manifest.txt` ni `diff` |
| "ISO **bit-identik** qayta qurilади" | ❌ **DA'VO QILINMAYDI** | N1–N6 |
| "Qayta qurilgan image **o'lchov uchun ekvivalent**" | **GIPOTEZA** | ikki ISO'ni qurib `diffoscope` bilan solishtirish + ikkisida ham `revix doctor --json` ning `checks[].status` bir xil chiqishi |

**Bu qadamlar bajarilmadi, sabab: guard kalibratsiyasi davom etmoqda.**
Birorta ISO qurilmagani uchun `manifest.txt` ham, `diffoscope` natijasi ham
mavjud emas.

### 3.3 `SOURCE_DATE_EPOCH` va `SNAPSHOT_TS` bitta joyda

`iso/config.sh` — **yagona haqiqat manbai**. `NEGA:` ikki skript ikki xil
epoch ishlatsa, determinizm jimgina buziladi va buni faqat `diffoscope`
ko'rsatadi. Bitta sourced fayl bu sinfni butunlay yopadi.

`SOURCE_DATE_EPOCH` **`SNAPSHOT_TS` dan hosil qilinadi** (`date -u -d`), qo'lda
yozilmaydi. `NEGA:` epoch snapshot'dan keyin bo'lsa, arxivdagi `Release`
fayllarining `Valid-Until` mantiqi va fayl mtime'lari bir-biriga mos kelmaydi.

---

## 4. Image nima qoniqtirishi kerak

Manba: `INSTALLATION.md` §2 (versiya chegaralari) va `revix/cli.py` ning
`EXPECTED_CHECK_KEYS` — **18 ta tekshiruv**, barqaror kalitlar.

**Qabul mezoni:** `revix doctor` guest'ning **birinchi boot'ida 0 FAIL** berishi
kerak. Bu mezon ataylab shunday tanlandi: u **mashina tomonidan
tekshiriladi** va allaqachon mavjud kod bilan o'lchanadi.

### 4.1 Qamrab olinishi SHART (FAIL bo'lsa image yaroqsiz)

| # | `key` | Image nima qiladi |
|---|---|---|
| 1 | `systemd_version` | trixie → systemd 257 ≥ 254 (§2.2) |
| 2 | `cgroup_v2` | Debian trixie default: unified hierarchy |
| 3 | `delegated_controllers` | `user@.service` uchun drop-in: `Delegate=cpu memory pids io` |
| 5 | `psi_host` | arxiv kernel'i `CONFIG_PSI=y` (§2.3 — GIPOTEZA) |
| 6 | `psi_cgroup` | shu kernel + cgroup v2 |
| 7 | `oomd` | `systemd-oomd` **o'rnatilMAYDI** → `kill authority yo'q` → PASS (§4.4) |
| 8 | `leftover_state` | toza boot'da `revix-*` unit ham, `revixlab.slice` cgroup ham yo'q |
| 9 | `cgroup_write` | delegatsiya (#3) bo'lsa ishlaydi |
| 10 | `memory_headroom` | **≥ 3.4 GiB `MemAvailable`** kerak (2.0 GiB shift + 1.4 GiB guard poli) → QEMU `-m 6144` (§6) |
| 13 | `toolchain_cc` | `build-essential` → `/usr/bin/cc` |
| 14 | `python_version` | trixie → Python 3.13 ≥ 3.11 |
| 15 | `python_modules` | `python3-psutil python3-dbus python3-numpy python3-scipy` (apt, **`pip` emas**) |
| 17 | `git_present` | image ichida **haqiqiy `.git`** + `safe.directory` (§5) |
| 18 | `git_clean` | clone aynan bir commit'da → toza daraxt |

### 4.2 WARN bo'lib qoladigan, lekin FAIL qilMAYDIGAN tekshiruvlar

Bu farq muhim: `revix/cli.py` ni o'qib tasdiqlandi — quyidagilar **hech qachon
FAIL bermaydi**, demak "0 FAIL" mezoni ularga bog'liq emas.

| # | `key` | Guest'dagi holat |
|---|---|---|
| 4 | `io_delegation` | **guest'da PASS bo'lishi mumkin** — root bo'lgani uchun `io` ni `cgroup.subtree_control` ga yozamiz. **Bu aynan fault class 6 ni ochadigan narsa** (§1). **GIPOTEZA** |
| 11 | `swap_headroom` | `SwapTotal=0` → `check_swap_headroom()` **WARN** qaytaradi (kod o'qildi: `if total == 0: return … WARN`). Live ISO'da swap yo'q → WARN. `revix-swapfile.service` (§5) bu WARN'ni yopadi |
| 16 | `kvm_access` | `check_kvm_access()` docstring'i: *"Hech qachon FAIL emas"*. Guest ichida ikkinchi daraja nested KVM kerak emas → WARN |

### 4.3 CHEKLOV — image **hal qilmaydigan** narsa

| `key` | Nega guest ham yordam bermaydi |
|---|---|
| **12 `cpu_governor`** | `PREREGISTRATION.md` §8.5 `scaling_cur_freq` va `thermal_zone*/temp` ni talab qiladi. Virtualizatsiya qilingan CPU'da `cpufreq` sysfs interfeysi **yo'q** — `acpi-cpufreq` yoki `amd-pstate` guest'da bind qilmaydi. `07` §1.3 #12 ni ham, §6.1 ni ham ko'ring: bu muhitda ham yo'q. **Demak §8.5 DVFS confound nazorati QEMU guest'da ham o'lchanmaydi**, va u faqat **bare-metal** host'da hal bo'ladi. Bu `07` §9 OQ-3 ning ochiq savoli; men hal qilmayman |

Bu yagona, lekin jiddiy cheklov: image "barcha privilegiyali tier'larni
ochadi" deb **da'vo qilinmaydi**. U `io`, `dm-*`, `tc netem`, `cpuset`, uzun
pressure oynasi va system-slice ko'chirishni ochadi; **DVFS nazoratini
ochmaydi**.

### 4.4 `systemd-oomd` — qarshilik va u KIMNING qarori

`07` §9 **OQ-1** ochiq savol qo'yadi: `00` §3.1 oomd'ni "1-RAQAMLI XAVF" deb
belgilaydi va ≤12 s pressure oynasi, guard 15 s sustain, `W_stab_pilot = 8 s`
— hammasi oomd'ning 20 s shartidan kelib chiqadi. Lekin shu mashinada
`systemd-oomd` **o'rnatilmagan** (`07` §0, §2).

**Image qarori:** `systemd-oomd` **o'rnatilmaydi**, va bu
`build-fingerprint.json` da **oshkora qayd etiladi**.

`NEGA:` (a) image'da desktop sessiyasi yo'q — oomd himoya qiladigan narsa yo'q;
(b) oomd o'rnatilsa, u o'lchovning o'ziga **aralashadi** (slice'larni o'ldiradi)
va bu arm'lar bo'ylab tizimli bo'lmagan kill'lar kiritadi; (c) guard
(`revix/guard.py`) mustaqil va `00` §6 qadam 3 bo'yicha **baribir** sinaladi.

`CHEKLOV:` demak image `01`/`00` da tavsiflangan "oomd armed desktop"
muhitini **qayta ishlab chiqarMAYDI**. `04-novelty-statement.md` C4 aynan
*"`systemd-oomd` armed bo'lgan jonli ish stansiyasida hech narsani
buzmasdan"* deydi — **o'sha** da'voni sinash **host'da**, image'da emas,
qoladi. Image **privilegiyali tier** uchun, C4 ni almashtirish uchun emas.
Pressure oynasini guest'da ≤12 s dan uzaytirish **frozen hujjat egasining
qarori** (OQ-1); men `PREREGISTRATION.md` ni o'zgartirmadim.

---

## 5. `packaging/` — `revix` image ichiga qanday o'rnatiladi

### 5.1 Qaror: **oddiy daraxt + systemd unit to'plami**, `.deb` emas

`NEGA:` `INSTALLATION.md` §3 aniq: *"`pip install`, `setup.py` yoki
`pyproject.toml` **yo'q** — bu ataylab. Repo `python3 -m revix.<modul>`
sifatida repo root'dan ishlatiladi."* Packaging sxemasi o'ylab topilmaydi,
mavjudi hurmat qilinadi.

Hal qiluvchi texnik sabab esa **git**:

- `PREREGISTRATION.md` §14.4 va `04-driver-va-analiz-shartnomasi.md` §1.1:
  `git_commit` va `git_dirty` — **majburiy** `run_meta` maydonlari.
- `revix/cli.py` ni o'qib tasdiqlandi: `git_info()` `git -C REPO_ROOT
  rev-parse HEAD` ni chaqiradi, va `REPO_ROOT = os.path.dirname(PKG_DIR)`.
  `rev-parse` nolga teng bo'lmagan kod qaytarsa `is_repo=False`, va
  **`git_present` ham, `git_clean` ham FAIL** bo'ladi.
- `.deb` paket faqat **checkout qilingan fayllarni** ko'chiradi; `.deb` ichida
  `.git` bo'lmaydi (va uni `.deb` ga solish — paket siyosati buzilishi).
  Demak **`.deb` → `git_present` FAIL → qabul mezoni (0 FAIL) buziladi.**

Shuning uchun: `/opt/revix` ga **mustaqil git repozitoriysi** o'rnatiladi.

### 5.2 Uchta nozik joy, uchtasi ham oldindan yopildi

**(a) Worktree pointer tuzog'i.** `07` §4.3 o'lchagan FAIL aynan shu edi:
worktree'ning `.git` **fayl** (gitdir pointer) bo'lib, boshqa mashinadagi
absolute yo'lga ishora qiladi → `rev-parse` *"not a git repository"* beradi →
`git_present`/`git_clean` **FAIL** (`07` §1.2 #17, #18). Yechim:
`git clone --no-hardlinks` — bu **to'liq, mustaqil `.git` katalogi** yaratadi,
pointer emas.

**(b) `dubious ownership`.** `/opt/revix` root egaligida bo'lsa va harness
uid 1000 bo'lsa, zamonaviy git *"detected dubious ownership"* bilan rc≠0
qaytaradi → yana ikki FAIL. Yechim: `git config --system --add
safe.directory /opt/revix` **va** daraxtni o'lchov foydalanuvchisiga `chown`
qilish. Ikkisi ham `packaging/install-revix.sh` da, `NEGA:` izohi bilan.

**(c) Daraxt toza bo'lishi.** `.gitattributes` (`* text=auto eol=lf`) CRLF
tuzog'ini allaqachon yopadi — va u faylning o'zi nega kerakligini yozadi:
*"noto'g'ri qator oxiri run'ni tekshirilishi mumkin bo'lmagan hujjat
versiyasiga bog'lab qo'yadi."* Clone Linux'da LF bilan checkout qiladi, demak
`git status --porcelain` bo'sh → `git_clean` PASS. `sut` binari
`.gitignore` da, ya'ni `make -C revix all` daraxtni **iflos qilmaydi**.

### 5.3 Fayl to'plami

| Fayl | Vazifasi | `NEGA:` |
|---|---|---|
| `packaging/install-revix.sh` | `/opt/revix` ga clone, egalik, `safe.directory`, unit'larni joylash | bitta joyda, ko'rib chiqiladigan |
| `packaging/bin/revix` | `/usr/local/bin/revix` wrapper → `cd /opt/revix && exec python3 -m revix.cli "$@"` | qabul mezoni `revix doctor` deb yozilgan; `python3 -m revix.cli` `sys.path` da repo root'ni talab qiladi |
| `packaging/systemd/user@.service.d/10-revix-delegate.conf` | `Delegate=cpu memory pids io` | `io` delegatsiyasi = **fault class 6** (§1); `doctor` #3 va #4 |
| `packaging/systemd/revix-swapfile.service` | 4 GiB swapfile, boot'da | `swap_headroom` WARN'ni yopadi; `check_swap_headroom` consequence: *"Swap butunlay yo'q bo'lsa reclaim yo'li qisqa: kernel OOM killer'ga tezroq yetiladi"* |
| `packaging/systemd/revix-io-delegate.service` | `io` ni cgroup root `subtree_control` ga yozadi | systemd `io` ni rootdan pastga avtomatik yoqmaydi (`07` §1.3 #4 o'lchagan holat) |
| `packaging/systemd/revix-harness.slice` | **o'rnatiladi, yoqilMAYDI** — system-slice ko'chirish uchun shablon | `00` §4 / `SECURITY.md` §4.1: system slice'ga ko'chirish — oomd qoldiq riskini yopadigan yagona to'liq yechim. Lekin bu **o'lchov topologiyasining o'zgarishi**, demak u `PREREGISTRATION.md` §15 ga ta'sir qiladi → **kechiktirilgan**, default'da yoqilmaydi |

`revix doctor` `/opt/revix` dan `python3 -m revix.cli doctor` sifatida
ishlaydi; `VERSION` fayli ham o'sha daraxtda (`cli.py:263` uni
`REPO_ROOT/VERSION` dan o'qiydi).

---

## 6. QEMU test rejasi

**Bu reja bajarilmadi, sabab: guard kalibratsiyasi davom etmoqda.** Hech qanday
guest boot qilinmadi.

### 6.1 Akseleratsiya — brifingdagi taxminni tuzatish

`INSTALLATION.md` §4 *"Shu mashinada KVM tekshirilgan"* deydi, lekin u
**avvalgi** mashinaga ishora qiladi (`01` §8: ACL `user:rootzero:rw-`).

**FAKT, shu mashinada o'lchangan** (`07` §1.2 #16 va §1.3 #16):

```
crw-rw---- 1 root kvm 10, 232 /dev/kvm          # device node BOR
lsmod -> kvm_amd, kvm                            # modullar yuklangan (nested)
id   -> ... 27(sudo) ... 1001(docker)            # `kvm` guruhida EMAS
test -r /dev/kvm ; test -w /dev/kvm  -> ikkisi ham "not"
doctor #16 kvm_access -> WARN "mavjud, lekin ruxsat yo'q"
```

`07` §8 jadvali xulosani ochiq yozadi: **"QEMU lab hozir mumkin emas."** Va
`07` §4.5: `sudo -n true` → *"a password is required"*.

**TALQIN:** `/dev/kvm` **mavjud**, lekin **bugun ishlatilmaydi**. Uni ochish
— bir martalik **privilegiyali** qadam (`usermod -aG kvm $USER` yoki
`setfacl -m u:$USER:rw /dev/kvm`), u `iso/00-host-prepare.sh` da yozilgan va
**bajarilmadi**.

**CHEKLOV (jiddiy):** KVM'siz QEMU TCG emulyatsiyasiga tushadi. TCG'da
timing 10–30× sekin va **nolinear**. `PREREGISTRATION.md` §6 downtime/latency
o'lchovlari va §1 vaqt disiplinasi TCG ostida **haqiqiy emas**. Shuning uchun:

> **Qoida: `revix doctor` ning `kvm_access` tekshiruvi PASS bermaguncha
> guest'da birorta timing o'lchovi o'tkazilmaydi.** TCG'da faqat *funksional*
> smoke (boot bo'ladimi, `doctor` ishlaydimi) qilish mumkin, va natija
> **timing sifatida yozilmaydi**.

### 6.2 Boot va qabul ketma-ketligi

```bash
# Host (KVM ochilgandan KEYIN):
qemu-system-x86_64 \
  -machine q35,accel=kvm -cpu host -smp 4 -m 6144 \
  -cdrom "$OUT_DIR/revix-appliance-$SNAPSHOT_TS.iso" \
  -drive file="$OUT_DIR/scratch.qcow2",if=virtio \
  -nographic -serial mon:stdio
```

`NEGA -m 6144:` `doctor` #10 `memory_headroom` **≥ 3.4 GiB `MemAvailable`**
talab qiladi (`cli.py`: `PLANNED_CEILING_KB` 2 GiB shift + `GUARD_MEM_FLOOR_KB`
guard poli), va `cli.py` yana +1 GiB "qulay zaxira" hisoblaydi. 4 GiB bilan
tekshiruv chegarada turadi; 6 GiB zaxira qoldiradi.

`NEGA -smp 4:` `CPUQuota=400%` siyosati (`00` §2) kamida 4 vCPU'ni nazarda
tutadi. `07` §8: host'da 12 vCPU bor, lekin guest'ga hammasini berish
host'dagi `experiment/guard-recal` ni buzadi.

`NEGA alohida virtio disk:` IO fault injection (`dm-delay`/`dm-flakey`, fault
class 6) **yozish mumkin bo'lgan blok qurilma**ni talab qiladi; live ISO
read-only.

Guest ichida, shu tartibda:

```bash
revix doctor --json  > /srv/accept/doctor.json     # MEZON: 0 FAIL
make -C /opt/revix/revix all                        # MEZON: rc=0, -Werror toza
cd /opt/revix && python3 -m pytest tests/ -q        # MEZON: suite o'tadi
cd /opt/revix && bash scripts/guard-test.sh         # MEZON: 00 §6 qadam 3 — GATE
cd /opt/revix && python3 -m revix.driver --dry-run …   # smoke, keyin 1 trial P0
cd /opt/revix && python3 -m revix.validate …        # smoke run validatsiyasi
```

`00-pilot-topologiya.md` §6 tartibi **image ichida ham majburiy**: qadam 3
(guard testi) qadam 4 (dosing kalibratsiyasi) dan oldin. *"Retrofit
qilinmaydi."* Guest — yangi mashina, demak guard testi va dosing
kalibratsiyasi **noldan** qayta bajariladi (§2.2 oxiri).

### 6.3 NEGA kampaniya WSL'da emas, guest ichida

To'liq asos §1.1 da. Qisqasi: host **ikki xil** usulda o'zini qayta ishga
tushiradi — init-only (`boot_id` o'zgarmaydi, `PREREGISTRATION.md` §16.11) va
to'liq VM restart (`boot_id` o'zgaradi, koordinator o'lchagan) — va ikkisi ham
transient hamda `--collect` unit'larini **trial o'rtasida** o'ldiradi. QEMU
guest bizning nazoratimizda.

**Kampaniya davomida IKKALA marker ham yoziladi** (`04` §1.1 / §1.4 allaqachon
shunday talab qiladi): `boot_id` Rejim B ni, `pid1_starttime_ticks` Rejim A ni
ushlaydi; har biri alohida **ko'r nuqtaga** ega (§1.1 jadvali).

**GIPOTEZA (§8 G8):** guest ichida **ikkala** marker ham butun ~2.5 soatlik
kampaniya davomida o'zgarmaydi. **O'lchovi:** har `env_snapshot` dagi
`boot_id` va `guest_generation.pid1_starttime_ticks` ni yig'ib, **har
ikkisi** uchun unikal qiymat sonini sanash — ikkisi ham 1 bo'lishi kerak.
Agar `pid1_starttime_ticks` o'zgarsa-yu `boot_id` o'zgarmasa — bu Rejim A
guest'da ham mavjud degani va image bu muammoni **hal qilmagan** bo'ladi.

---

## 7. Kechiktirilgan — oshkora

| Nima | Nega kechiktirildi |
|---|---|
| **Installer** (`d-i`, Calamares, `live-installer`) | Loyiha spetsifikatsiyasi: recovery engine ishlamaguncha installer murakkabligi ustuvor qilinmaydi. Qamrov (§0) bo'yicha engine **yo'q**, demak installer **bugun** foydasiz murakkablik. Live boot + alohida virtio disk tadqiqot uchun yetarli |
| **GUI** | `feature/gui` boshqa branch va boshqa fayl egaligi. Bundan tashqari GUI guest'da fon yuk kiritadi → `PREREGISTRATION.md` §8 confound nazorati buziladi. Image **headless** (`-nographic`, serial console) |
| **Branding integratsiyasi** (boot screen, logo, terminal theme) | Dizayn `docs/branding/` da **allaqachon mavjud** (`boot-screen.md`, `boot-screen.svg`, `00-design-system.md`, `tokens.css`, `terminal-theme.md`); u shu hujjatda **takrorlanmaydi** — bootloader matni uchun `docs/branding/boot-screen.md` o'qiladi. Image'ga **ulanmaydi**, chunki: (a) `feature/branding` boshqa branch va boshqa fayl egaligi; (b) §0 bo'yicha brending "distributiv" taassurotini kuchaytiradi, bu esa aynan oldini olmoqchi bo'lgan overclaiming; (c) image **headless** — `40-make-iso.sh` dagi bootloader konfiguratsiyasi serial console uchun, grafik splash uchun emas |
| **`revix-harness.slice` ni yoqish** | system slice'ga ko'chirish o'lchov topologiyasini o'zgartiradi → `PREREGISTRATION.md` §15 muhit fingerprint'iga ta'sir qiladi. Shablon o'rnatiladi, yoqilmaydi (§5.3) |
| **Pressure oynasini >12 s ga uzaytirish** | Bu `PREREGISTRATION.md` §0 ning qamrov chegarasi va `07` §9 OQ-1. Image **imkoniyatni** beradi; **qaror frozen hujjat egasiniki** |
| **Arm C** | `PREREGISTRATION.md` §13: muzlatilmagan, o'z pre-registration'ini talab qiladi |

---

## 8. GIPOTEZA ro'yxati — har biri uchun tasdiqlovchi o'lchov

Quyidagilarning **hech biri** o'lchanmadi.

| # | GIPOTEZA | Uni tasdiqlaydigan o'lchov |
|---|---|---|
| G1 | Build qadamlari xatosiz tugaydi | `bash iso/build-all.sh` → rc=0 va `OUT_DIR/*.iso` mavjud |
| G2 | ISO QEMU'da boot bo'ladi | serial console'da `systemd` target'iga yetish; `systemctl is-system-running` |
| G3 | `revix doctor` **0 FAIL** beradi | `revix doctor --json` → `jq '[.checks[]\|select(.status=="FAIL")]\|length' == 0` |
| G4 | Arxiv kernel'ida `CONFIG_PSI=y` | `doctor` #5 `psi_host` va #6 `psi_cgroup` PASS |
| G5 | `io` delegatsiyasi guest'da ishlaydi → fault class 6 ochiladi | `doctor` #4 `io_delegation` PASS **va** `revixlab.slice/io.max` ga yozish rc=0 |
| G6 | Kompozitsiya takrorlanadi | ikki marta qurib `manifest.txt` ni `diff` → bo'sh |
| G7 | ISO bit-identik | ❌ **da'vo qilinmaydi** (§3.2 N1–N6). `diffoscope` farqni **ko'rsatishi kutiladi** |
| G8 | Guest'da na PID 1, na VM qayta ishga tushmaydi | kampaniya davomida **ikkala** marker: `boot_id` **va** `guest_generation.pid1_starttime_ticks` — har biri uchun unikal qiymat soni = 1 (§1.1, §6.3) |
| G9 | Guard guest'da ishlaydi | `scripts/guard-test.sh` guest ichida o'tadi (`00` §6 qadam 3) |
| G10 | KVM akseleratsiyasi mavjud | `doctor` #16 `kvm_access` **host'da** PASS → keyin guest'da `accel=kvm` |

---

## 9. Fayl ro'yxati

```
iso/
  README.md                       qisqa yo'l ko'rsatkich
  config.sh                       YAGONA pinning manbai (SNAPSHOT_TS, SOURCE_DATE_EPOCH, suite, paketlar)
  lib/common.sh                   log, fail-closed tekshiruvlar (disk, ext4, experiment-in-progress)
  00-host-prepare.sh              *** YAGONA PRIVILEGIYALI SKRIPT *** -- build'da bir marta
  10-build-rootfs.sh              mmdebstrap --mode=unshare (root'siz)
  20-record-manifest.sh           dpkg-query -> manifest.txt + sha256
  30-make-squashfs.sh             mksquashfs, determinizm bayroqlari
  40-make-iso.sh                  grub EFI + isolinux BIOS + xorriso
  50-fingerprint.sh               build-fingerprint.json + SHA256SUMS
  99-qemu-smoke.sh                QEMU test rejasi (§6)
  build-all.sh                    10 -> 50 orkestratsiyasi
  hooks/customize-10-revix.sh     packaging/ ni chaqiradi
  hooks/customize-20-systemd.sh   delegatsiya, swapfile, unit'lar
  hooks/customize-90-normalize.sh nondeterminizmni tozalaydi (R5)
packaging/
  install-revix.sh                /opt/revix ga clone + egalik + safe.directory
  bin/revix                       /usr/local/bin/revix wrapper
  systemd/user@.service.d/10-revix-delegate.conf
  systemd/revix-io-delegate.service
  systemd/revix-swapfile.service
  systemd/revix-harness.slice     o'rnatiladi, YOQILMAYDI
```

`iso/README.md` — qisqa yo'l ko'rsatkich (qarorlar shu hujjatda, u yerda
takrorlanmaydi).

Har bir skript: `set -euo pipefail`, fail-closed, izohlar o'zbekcha,
identifikatorlar inglizcha.

### 9.1 Umumiy fail-closed shartlar (`iso/lib/common.sh`)

| Shart | `NEGA:` |
|---|---|
| **Eksperiment davom etayotgan bo'lsa ishga tushmaydi** | `revix/units.py:1506 preflight()` / `require_clean()` mantig'i shell'da qayta yozildi: `revix-*` ga mos **yuklangan** unit, yoki `revixlab.slice`/`revixmon.slice` (unit **yoki cgroup katalogi**) topilsa — **rad etadi**. `units.py` docstring'i sababni aytadi: *"qoldiq unit yoki cgroup JIMGINA keyingi run'ga qo'shilib ketardi"*. `00-pilot-topologiya.md` §2 va `scripts/guard-test.sh` pre-flight'i ham shunday |
| **Chiqish yo'li ext4'da, `/mnt/*` da emas** | `07` §7.2 **FAKT**: `/mnt/c` = 9p/drvfs, **98% to'la, 10 G bo'sh**; ext4 root'da 951 G. `scripts/sync-to-ext4.sh` allaqachon shu fail-closed tekshiruvini qiladi — bir xil qoida |
| **Yetarli disk bo'lmasa ishga tushmaydi** | rootfs + squashfs + ISO + apt cache ≈ 25 G. `/mnt/c` da 10 G — yetmaydi va **to'lib ketish Windows tomonini buzadi** |
| **`SOURCE_DATE_EPOCH` majburiy** | o'rnatilmagan bo'lsa determinizm yo'q (§3.3) |
| **`root` sifatida ishga tushirilsa rad etadi** (`00-host-prepare.sh` dan boshqa) | `00` §4: *"o'lchov davomida hech qanday root process tirik emas"* — build'da ham shu disiplina |

---

## 10. Bajarilmagan qadamlar — to'liq ro'yxat

| Qadam | Holat |
|---|---|
| `iso/00-host-prepare.sh` (apt install, KVM ruxsati) | **bajarilmadi, sabab: guard kalibratsiyasi davom etmoqda** |
| `iso/10-build-rootfs.sh` (`mmdebstrap`) | **bajarilmadi, sabab: guard kalibratsiyasi davom etmoqda** |
| `iso/20-record-manifest.sh` | bajarilmadi — rootfs yo'q |
| `iso/30-make-squashfs.sh` | bajarilmadi — rootfs yo'q |
| `iso/40-make-iso.sh` | bajarilmadi — squashfs yo'q |
| `iso/50-fingerprint.sh` | bajarilmadi — ISO yo'q |
| `iso/99-qemu-smoke.sh` (boot, `doctor`, testlar, guard testi, smoke trial) | bajarilmadi — ISO yo'q; qo'shimcha: `/dev/kvm` ruxsati ham yo'q (§6.1) |
| `packaging/install-revix.sh` | bajarilmadi — rootfs yo'q |
| `diffoscope` bilan ikki marta qurish taqqoslashi | bajarilmadi |
| `shellcheck` | **mavjud emas** bu muhitda (`command -v shellcheck` → topilmadi) |

**Bajarilgan yagona tekshiruv:** har bir skript uchun `bash -n` (syntax).

**Hech qanday image qurilmadi. Hech qanday ISO boot qilinmadi. Hech qanday
checksum taqqoslanmadi. Hech qanday natija yo'q.**

---

## 11. Aloqador hujjatlar

- `README.md` — *"Loyiha nima EMAS"*
- `PREREGISTRATION.md` §0 (qamrov), §7 (`total=` asosiy), §8.5 (DVFS), §13 (muzlatilmagan), §14.4 (majburiy maydonlar), §14.6(5) (`boot_id` invarianti), §15 (muhit fingerprint), **§16.11** (`boot_id` kafolati buzilgan — PID 1 restart)
- `docs/branding/boot-screen.md` — boot screen dizayni (bu hujjatda **takrorlanmaydi**; §7 ga qarang)
- `INSTALLATION.md` §2 (versiya chegaralari), §3 (`pip` yo'q), §4 (root kerak = guest'ga tegishli)
- `docs/architecture/00-pilot-topologiya.md` §2, §4, §5, §6
- `docs/architecture/02-guard-kalibratsiyasi.md` §7 (guest talab qiladigan bloklar)
- `docs/architecture/04-driver-va-analiz-shartnomasi.md` §1.1, §1.4 (`guest_generation`)
- `docs/architecture/07-wsl-muhit-tekshiruvlari.md` §1.2, §1.3, §4.3, §4.4, §7.2, §8, §9
- `docs/research/04-novelty-statement.md` C4
- `revix/cli.py` (`EXPECTED_CHECK_KEYS`, `git_info`, `check_*`), `revix/units.py` (`preflight`, `require_clean`)
- `scripts/sync-to-ext4.sh`, `scripts/guard-test.sh` — fail-closed naqshning manbai
