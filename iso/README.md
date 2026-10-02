# `iso/` — research appliance image build

**Dizayn va asoslash:**
[`docs/architecture/09-iso-qurilishi.md`](../docs/architecture/09-iso-qurilishi.md).
Bu fayl faqat yo'l ko'rsatkich — qarorlar va `NEGA:` lar o'sha hujjatda.

## Qamrov — avval shuni o'qing

Bu yerdagi skriptlar **Debian + REVIX o'lchov harness'i**dan iborat
**reproducible research appliance** quradi. Bu **operatsion tizim emas**,
**"REVIX OS" emas** va **adaptiv self-healing tizim emas**: REVIX'da
adaptive recovery engine **yo'q**, arm C `PREREGISTRATION.md` §13 bo'yicha
**muzlatilmagan**, va uni implement qiladigan kod `revix/` da mavjud emas.
To'liq bayon: `09-iso-qurilishi.md` §0.

## Holat

**Hech qanday image qurilmadi. Hech qanday ISO boot qilinmadi.**
Barcha skriptlar yozildi va `bash -n` bilan tekshirildi, lekin
**bajarilmadi, sabab: guard kalibratsiyasi davom etmoqda.**
Bajarilmagan qadamlarning to'liq ro'yxati: `09-iso-qurilishi.md` §10.

## Tartib

```bash
# (1) YAGONA privilegiyali qadam -- build'ga bir marta, nazorat ostida.
REVIX_ISO_CONFIRM=yes bash iso/00-host-prepare.sh

# (2) build (root'siz: mmdebstrap --mode=unshare)
REVIX_ISO_CONFIRM=yes bash iso/build-all.sh

# (3) QEMU smoke
bash iso/99-qemu-smoke.sh
```

`REVIX_ISO_CONFIRM=yes` bo'lmasa skriptlar **ishga tushmaydi**. `NEGA:`
build guest'ning xotira, disk va CPU'sini to'yintiradi; bu mashinada
REVIX o'lchovi davom etayotgan bo'lsa, build **o'sha o'lchovni buzadi** va
o'lchov qayta takrorlanmaydi.

## Fail-closed shartlar (`lib/common.sh`)

| Shart | Manba |
|---|---|
| `revix-*` unit yoki `revixlab.slice`/`revixmon.slice` (unit yoki cgroup) bo'lsa — **rad etadi** | `revix/units.py:1506 preflight()` / `require_clean()`; `00-pilot-topologiya.md` §2 |
| chiqish yo'li ext4'da; `/mnt/*` **rad etiladi** | `07-wsl-muhit-tekshiruvlari.md` §7.2; `scripts/sync-to-ext4.sh` |
| `< 25 GiB` bo'sh disk — **rad etadi** | `07` §7.2 (`/mnt/c` da 10 G) |
| `SOURCE_DATE_EPOCH` majburiy | `09` §3.3 |
| `00-host-prepare.sh` dan boshqa skript root bilan — **rad etadi** | `00-pilot-topologiya.md` §4 |

## Fayllar

| Fayl | Qadam |
|---|---|
| `config.sh` | yagona pinning manbai (`SNAPSHOT_TS`, `SOURCE_DATE_EPOCH`, suite, paketlar) |
| `lib/common.sh` | fail-closed tekshiruvlar |
| `00-host-prepare.sh` | **yagona privilegiyali skript** |
| `10-build-rootfs.sh` | `mmdebstrap --mode=unshare` |
| `20-record-manifest.sh` | paket manifest'i + versiya chegaralari |
| `30-make-squashfs.sh` | deterministik squashfs + kernel/initrd |
| `40-make-iso.sh` | GRUB (EFI) + isolinux (BIOS) + `xorriso` |
| `50-fingerprint.sh` | `build-fingerprint.json` + `SHA256SUMS` |
| `99-qemu-smoke.sh` | QEMU test rejasi |
| `build-all.sh` | 10 → 50 orkestratsiyasi |
| `hooks/` | `mmdebstrap` customize hook'lari |

Harness image ichiga qanday o'rnatilishi: [`packaging/`](../packaging).
