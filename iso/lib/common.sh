# REVIX image build -- umumiy fail-closed tekshiruvlar.
#
# Bu fayl `source` qilinadi, bajarilmaydi.
#
# Loyiha qoidasi: tekshiruvning O'ZI xato bersa natija PASS emas, FAIL
# bo'ladi. Bu `revix/cli.py:collect_checks()` dagi aynan shu prinsip:
# "FAIL-CLOSED: tekshiruvning O'ZI istisno tashlasa, natija PASS emas, FAIL
# bo'ladi. Aks holda doctor'dagi bug jimgina 'hammasi yaxshi' ga aylanardi."
#
# shellcheck shell=bash

set -euo pipefail

# --- log --------------------------------------------------------------------

log()  { printf '[revix-iso] %s\n' "$*"; }
warn() { printf '[revix-iso] OGOHLIK: %s\n' "$*" >&2; }
die()  { printf '[revix-iso] XATO: %s\n' "$*" >&2; exit 1; }

# --- 1. root sifatida ishga tushirishni rad etish ---------------------------

# NEGA: 00-pilot-topologiya.md §4 prinsipi -- "barcha privilegiyali
# operatsiyalar BITTA qisqa, ko'rib chiqiladigan setup skriptida, sessiyaga
# bir marta ishlaydi va har trial'da hech narsa qilmaydi". Build uchun ham
# shu disiplina: faqat 00-host-prepare.sh root bilan ishlaydi, qolgan
# hamma qadam mmdebstrap --mode=unshare orqali ROOT'SIZ bajariladi (09 §2.1).
require_not_root() {
  if [ "$(id -u)" -eq 0 ]; then
    die "bu skript root sifatida ishga tushirilmaydi (00 §4 prinsipi). Faqat iso/00-host-prepare.sh root talab qiladi."
  fi
}

# --- 2. eksperiment davom etayotgan bo'lsa ishga tushmaslik -----------------

# NEGA: `revix/units.py:1506 preflight()` / `require_clean()` mantig'ining
# shell'dagi qayta yozilishi. units.py docstring'i sababni aytadi:
#
#   "qoldiq unit yoki cgroup JIMGINA keyingi run'ga qo'shilib ketardi --
#    eski memory.current, eski NRestarts, eski failed holat. O'lchov
#    hissasi bo'lgan loyihada bu jimgina kontaminatsiya, demak run
#    boshlanmaydi."
#
# Build uchun sabab teskari tomondan bir xil: build guest'ning xotira, disk
# va CPU'sini to'yintiradi, demak jonli o'lchovni BUZADI. Qat'iy rad etish
# mezonlari units.py bilan BIR XIL (00-pilot-topologiya.md §2):
#   * `revix-*` ga mos YUKLANGAN unit;
#   * `revixlab.slice` / `revixmon.slice` -- unit YOKI cgroup katalogi.
#
# Qo'shimcha: scripts/guard-test.sh pre-flight'i `revix-press.service` ni
# alohida tekshiradi -- shu ham qo'shildi.
REVIX_UNIT_GLOB="revix-*"
REVIX_LAB_SLICE="revixlab.slice"
REVIX_MON_SLICE="revixmon.slice"

# user@UID.service cgroup yo'li. revix/cgroup.py:user_service_cgroup() ning
# shell ekvivalenti; modul mavjud bo'lsa modulning o'zidan olinadi, chunki
# yo'lni ikki joyda ikki xil hisoblash -- jimgina divergensiya manbai.
revix_user_cgroup() {
  local uid cg
  uid="$(id -u)"
  if [ -n "${REPO_SRC:-}" ] && [ -f "${REPO_SRC}/revix/cgroup.py" ]; then
    if cg="$(cd "$REPO_SRC" && python3 -c 'from revix import cgroup as c; print(c.user_service_cgroup())' 2>/dev/null)"; then
      printf '%s\n' "$cg"
      return 0
    fi
  fi
  printf '/sys/fs/cgroup/user.slice/user-%s.slice/user@%s.service\n' "$uid" "$uid"
}

require_clean_env() {
  local problems=() cg

  # (a) YUKLANGAN unit'lar. `--all` yuklangan, lekin faol bo'lmaganini ham
  # ko'rsatadi -- units.py list_units() bilan bir xil qamrov.
  if command -v systemctl >/dev/null 2>&1; then
    local units
    units="$(systemctl --user list-units "$REVIX_UNIT_GLOB" "$REVIX_LAB_SLICE" "$REVIX_MON_SLICE" \
               --all --no-legend 2>/dev/null || true)"
    if [ -n "$units" ]; then
      while IFS= read -r line; do
        [ -n "$line" ] || continue
        problems+=("qoldiq unit: $line")
      done <<< "$units"
    fi
    # guard-test.sh pre-flight'ining aynan tekshiruvi.
    if systemctl --user --quiet is-active revix-press.service 2>/dev/null; then
      problems+=("revix-press.service ISHLAYAPTI")
    fi
  else
    # FAIL-CLOSED: systemctl bo'lmasa tekshiruv bajarilmadi, demak "toza" deb
    # ayta olmaymiz.
    die "systemctl topilmadi -- eksperiment holatini tekshirib bo'lmaydi, build rad etiladi (fail-closed)"
  fi

  # (b) cgroup kataloglari. 07 §4.4 o'lchagan holat: distro qayta ishga
  # tushgandan keyin BO'SH cgroup katalogi QOLADI va preflight() uni
  # bloklovchi deb sanaydi. Biz ham xuddi shunday sanaymiz.
  cg="$(revix_user_cgroup)"
  local sl
  for sl in "$REVIX_LAB_SLICE" "$REVIX_MON_SLICE"; do
    if [ -d "$cg/$sl" ]; then
      problems+=("qoldiq cgroup: $cg/$sl")
    fi
  done

  if [ "${#problems[@]}" -gt 0 ]; then
    printf '[revix-iso] XATO: REVIX eksperimenti davom etmoqda yoki qoldiq holat bor.\n' >&2
    printf '[revix-iso]   %s\n' "${problems[@]}" >&2
    printf '[revix-iso] Build RAD ETILDI: image qurilishi guest xotira/disk/CPU sini to\xe2\x80\x99yintiradi\n' >&2
    printf '[revix-iso] va jonli o\xe2\x80\x99lchovni buzadi (revix/units.py require_clean(), 00-pilot-topologiya.md \xc2\xa72).\n' >&2
    exit 1
  fi
  log "pre-flight: toza (revix-* unit yo'q, revixlab/revixmon cgroup yo'q)"
}

# --- 3. chiqish yo'li ext4'da bo'lishi ---------------------------------------

# NEGA: 07 §7.2 FAKT -- /mnt/c = 9p/drvfs, 98% to'la, 10 G bo'sh; append
# latency ext4 dan ~100x sekin. scripts/sync-to-ext4.sh ayni shu fail-closed
# tekshiruvini qiladi: "DEST yoki RUNS drvfs ustida. O'lchov ext4'da bo'lishi
# SHART." Build uchun qo'shimcha sabab: 10 G build'ga YETMAYDI va /mnt/c ni
# to'ldirish Windows tomonini buzadi.
require_ext4_out() {
  local path="$1" fstype
  case "$path" in
    /mnt/*|/media/*)
      die "chiqish yo'li drvfs/9p ustida ($path). Image ext4 HOME'da qurilishi SHART (07 §7.2)." ;;
  esac
  mkdir -p "$path"
  fstype="$(stat -fc %T "$path")"
  case "$fstype" in
    ext2/ext3|ext4|xfs|btrfs|tmpfs) log "chiqish fs: $fstype ($path)" ;;
    9p|fuseblk|msdos|vfat|ntfs)
      die "chiqish fs '$fstype' ($path) -- determinizm va performance uchun yaroqsiz (07 §7.2)." ;;
    *)
      # FAIL-CLOSED: tanimagan fs -> ruxsat berilmaydi.
      die "chiqish fs '$fstype' ($path) tanilmadi -- fail-closed, build rad etiladi." ;;
  esac
}

# --- 3b. user namespace ichidan YETIB BORILADIGANLIK ------------------------
#
# TUZATISH (11-iso-qurilish-jurnali.md, bug #1 va bug #2).
#
# `mmdebstrap --mode=unshare` uid map'i (o'lchangan, /usr/bin/mmdebstrap:1469
# va `unshare --map-auto` bilan tasdiqlangan):
#       0 -> 100000, range 65536
# Foydalanuvchining O'Z uid'i map QILINMAYDI. Shundan ikki oqibat chiqadi va
# ikkisi ham build'ni o'ldiradi:
#
#   (1) Build yo'lining HAR BIR ota-katalogi namespace ichidan o'tiladigan
#       bo'lishi SHART (o+x). $HOME 0700 -> yaroqsiz (config.sh ga qarang).
#   (2) mmdebstrap yozgan rootfs tashqi tomondan uid 100000 ga tegishli
#       bo'ladi, va uning ichida 0700 rejimli kataloglar bor (`/root`,
#       `/etc/ssh`, `initrd.img` 0600). Demak rootfs'ni OQIYDIGAN qadamlar
#       (squashfs, kernel/initrd ko'chirish) oddiy foydalanuvchi sifatida
#       ISHLAMAYDI -- va ishlagandek ko'rinsa, squashfs ichidagi EGALIK
#       100000 bo'lib qolardi, ya'ni boot qilgan tizimda `/root` egasi
#       `nobody` bo'lardi.
#
# NEGA fail-closed tekshiruv: bu xato BIRINCHI marta mmdebstrap'ning
# tushunarsiz "cannot create ...: Permission denied" xabari bilan chiqdi --
# sababi ko'rinmaydi. Tekshiruv sababni BUILD BOSHIDA, aniq matn bilan
# aytadi.
require_userns_path() {
  local path="$1"
  command -v unshare >/dev/null 2>&1 \
    || die "unshare topilmadi -- mmdebstrap --mode=unshare ishlamaydi"
  mkdir -p "$path"
  if ! unshare --user --map-auto --setuid 0 --setgid 0 \
         test -w "$path" 2>/dev/null; then
    printf '[revix-iso] XATO: build yo\xe2\x80\x99li user namespace ICHIDAN yetib borilmaydi:\n' >&2
    printf '[revix-iso]   %s\n' "$path" >&2
    printf '[revix-iso] SABAB: mmdebstrap --mode=unshare uid map'"'"'i = (0 -> 100000, 65536);\n' >&2
    printf '[revix-iso] foydalanuvchining o\xe2\x80\x99z uid\xe2\x80\x99i map QILINMAYDI, demak yo\xe2\x80\x99ldagi\n' >&2
    printf '[revix-iso] har bir ota-katalog o+x bo\xe2\x80\x99lishi va build katalogi yozilishi\n' >&2
    printf '[revix-iso] mumkin bo\xe2\x80\x99lishi SHART. $HOME (0700) bu rejim uchun yaroqsiz.\n' >&2
    printf '[revix-iso] YECHIM: OUT_DIR ni o+x ota-katalog ostiga qo\xe2\x80\x99ying (default /var/tmp).\n' >&2
    exit 1
  fi
  log "userns: '$path' namespace ichidan yoziladi"
}

# MANBA repo uchun: namespace ichidan O'QILISHI (va o'tilishi) kerak, lekin
# yozilishi kerak EMAS.
#
# NEGA alohida tekshiruv kerak -- TUZATISH (bug #5):
# `iso/hooks/customize-10-revix.sh` -> `packaging/install-revix.sh` ->
# `git clone --no-hardlinks "$REPO_SRC" ...` mmdebstrap'ning customize-hook
# fazasida, ya'ni NAMESPACE ICHIDA ishlaydi. Agar REPO_SRC `$HOME` ostida
# bo'lsa (0700, map qilinmagan uid 1000), clone "Permission denied" bilan
# o'ladi -- va bu BUTUN paket o'rnatish tugagandan KEYIN sodir bo'ladi,
# ya'ni ~20 daqiqa behuda ketadi. Shuning uchun tekshiruv BUILD BOSHIDA.
require_userns_readable() {
  local path="$1"
  command -v unshare >/dev/null 2>&1 \
    || die "unshare topilmadi -- mmdebstrap --mode=unshare ishlamaydi"
  [ -e "$path" ] || die "yo'l mavjud emas: $path"
  if ! unshare --user --map-auto --setuid 0 --setgid 0 \
         test -r "$path" 2>/dev/null; then
    printf '[revix-iso] XATO: manba yo\xe2\x80\x99li user namespace ICHIDAN o\xe2\x80\x99qilmaydi:\n' >&2
    printf '[revix-iso]   %s\n' "$path" >&2
    printf '[revix-iso] SABAB: customize-hook (install-revix.sh -> git clone) namespace\n' >&2
    printf '[revix-iso] ICHIDA ishlaydi, u yerda foydalanuvchining uid\xe2\x80\x99i map QILINMAGAN.\n' >&2
    printf '[revix-iso] $HOME (0700) ostidagi manba repo clone qilinmaydi.\n' >&2
    printf '[revix-iso] YECHIM: REPO_SRC ni o+rx yo\xe2\x80\x99lga ko\xe2\x80\x99chiring, masalan /var/tmp/revix-src.\n' >&2
    exit 1
  fi
  log "userns: manba '$path' namespace ichidan o'qiladi"
}

# Namespace ichida mmdebstrap BILAN AYNAN BIR XIL identitet ostida buyruq
# bajaradi: ichki uid 0 == tashqi uid 100000 == rootfs egasi.
#
# NEGA `--map-auto`: u /etc/subuid ni mmdebstrap bilan bir xil o'qiydi
# (tasdiq: ikkisi ham `0 100000 65536` beradi). Boshqa map ishlatilsa
# rootfs egaligi ichkarida yana mos kelmaydi.
# NEGA `--setuid 0 --setgid 0`: busiz namespace ichida uid 65534 (nobody)
# bo'lib qolinadi va hech narsa o'qilmaydi.
ns_run() {
  unshare --user --map-auto --setuid 0 --setgid 0 -- "$@"
}

# Build kataloglari: namespace ICHIDAGI root (tashqi 100000) ularga YOZISHI
# kerak, tashqi foydalanuvchi (xorriso, sha256sum) esa O'QISHI kerak.
# Ikkisi ham kerak bo'lgani uchun rejim 0777.
# NEGA bu xavfsizlik muammosi emas: /var/tmp allaqachon 1777, va bu
# vaqtinchalik build katalogi -- image'ga KIRMAYDI (image ichidagi egalik
# va rejimlar mmdebstrap/squashfs tomonidan alohida belgilanadi).
make_shared_dir() {
  local d
  for d in "$@"; do
    mkdir -p "$d"
    chmod 0777 "$d"
  done
}

# Build daraxtining HAMMA kataloglari bir joyda tayyorlanadi.
#
# NEGA bitta funksiya: birinchi urinishda OUT_DIR 0777 qilindi, lekin
# STAGE_DIR/live qilinmadi -- va xato faqat 30-qadamda, mksquashfs
# "Permission denied" bergandan keyin ko'rindi. Kataloglar ro'yxati BITTA
# joyda bo'lsa bu sinf butunlay yopiladi.
#
# NEGA OUT_DIR ham 0777: mmdebstrap namespace ICHIDAN butun yo'l zanjirini
# (OUT_DIR -> work -> rootfs -> rootfs/etc/...) o'zi yaratadi, demak OUT_DIR
# ichkaridagi root uchun yozilishi mumkin bo'lishi SHART. Birinchi urinishda
# OUT_DIR snowden:snowden 0755 edi va mmdebstrap aynan shu yerda to'xtadi.
prepare_build_dirs() {
  make_shared_dir "$OUT_DIR" "$WORK_DIR" "$STAGE_DIR" "$STAGE_DIR/live"
}

# --- 3c. GUEST GENERATION -- build o'rtasida host qayta ishga tushdimi? -----
#
# TUZATISH (11-iso-qurilish-jurnali.md, bug #8). Bu eng xavfli xato edi,
# chunki u XATO BERMAYDI -- u JIMGINA muvaffaqiyatga o'xshaydi.
#
# O'LCHANGAN HODISA (ikki marta, mustaqil ravishda ko'rildi): `mmdebstrap`
# PID ~1900 bilan ishlayotgan va rootfs 6.8 GB ga o'sgan; bir necha daqiqa
# keyin AYNAN SHU buyruq PID ~400 bilan QAYTA ishlayapti, `work/rootfs`
# BO'SH, `apt-get update` boshidan. Tizimdagi eng katta PID 2901 dan 557 ga
# tushgan. Bu progress emas, YANGI BOOT.
#
# SABAB: WSL2 oxirgi `wsl.exe` klienti chiqqandan keyin distro'ni to'xtatadi
# (`07-wsl-muhit-tekshiruvlari.md` §4.4: 10.3-15.3 s o'lchangan). Har bir
# tool-call orasidagi bo'shliq -- guest'ni yo'q qilish imkoniyati.
#
# NEGA bu FAIL-CLOSED tekshiruvni talab qiladi: agar 10-qadam yarmida
# o'lsa va 20-qadam davom etsa, ISO YARIM TO'LDIRILGAN rootfs'dan qurilardi
# -- va build MUVAFFAQIYATLI ko'rinardi. Natija: buzilgan image, soxta
# checksum, soxta manifest. Shuning uchun har qadam oldidan generatsiya
# tekshiriladi.
#
# NEGA IKKI marker (bittasi YETARLI EMAS) -- `09` §1.1 jadvali aynan shuni
# aytadi va `PREREGISTRATION.md` §16.11 ni takrorlaydi:
#   * `boot_id`                -> to'liq VM restart'ni ushlaydi;
#     ko'r nuqtasi: init-only restart'da O'ZGARMAYDI.
#   * `/proc/1/stat` 22-maydon  -> init-only restart'ni ushlaydi
#     (PID 1 ning starttime tick'i).
# `09` §1.1: "§14.6(5) invarianti ZARUR, lekin YETARLI EMAS" va qo'shimcha
# marker uni "almashtirmaydi, uni TO'LDIRADI".
generation_now() {
  local bid ticks
  bid="$(cat /proc/sys/kernel/random/boot_id 2>/dev/null || echo UNKNOWN)"
  ticks="$(awk '{print $22}' /proc/1/stat 2>/dev/null || echo UNKNOWN)"
  printf 'boot_id=%s pid1_starttime_ticks=%s\n' "$bid" "$ticks"
}

generation_stamp_path() { printf '%s\n' "$WORK_DIR/build-generation.txt"; }

record_generation() {
  local f
  f="$(generation_stamp_path)"
  generation_now > "$f"
  chmod 0666 "$f" 2>/dev/null || true
  log "guest generation qayd etildi: $(cat "$f")"
}

require_same_generation() {
  local f now recorded
  f="$(generation_stamp_path)"
  if [ ! -f "$f" ]; then
    die "guest generation stamp yo'q ($f) -- avval iso/10-build-rootfs.sh (fail-closed)"
  fi
  recorded="$(cat "$f")"
  now="$(generation_now)"
  if [ "$recorded" != "$now" ]; then
    printf '[revix-iso] XATO: GUEST BUILD O\xe2\x80\x99RTASIDA QAYTA ISHGA TUSHGAN.\n' >&2
    printf '[revix-iso]   qayd etilgan: %s\n' "$recorded" >&2
    printf '[revix-iso]   hozirgi:      %s\n' "$now" >&2
    printf '[revix-iso] Oldingi qadamlarning natijasi YO\xe2\x80\x99Q yoki YARIM -- davom etish\n' >&2
    printf '[revix-iso] YARIM TO\xe2\x80\x99LDIRILGAN rootfs\xe2\x80\x99dan ISO qurardi va build MUVAFFAQIYATLI\n' >&2
    printf '[revix-iso] ko\xe2\x80\x99rinardi (07 \xc2\xa74.4; PREREGISTRATION.md \xc2\xa716.11).\n' >&2
    printf '[revix-iso] Build RAD ETILDI. Noldan boshlang: iso/10-build-rootfs.sh\n' >&2
    exit 1
  fi
  log "guest generation o'zgarmagan: $now"
}

# --- 4. disk zaxirasi -------------------------------------------------------

require_disk() {
  local path="$1" need_gb="$2" avail_kb avail_gb
  avail_kb="$(df -Pk "$path" | awk 'NR==2 {print $4}')"
  [ -n "$avail_kb" ] || die "df '$path' uchun bo'sh joyni aniqlay olmadi (fail-closed)"
  avail_gb=$(( avail_kb / 1024 / 1024 ))
  if [ "$avail_gb" -lt "$need_gb" ]; then
    die "yetarli disk yo'q: $path da ${avail_gb} GiB bo'sh, kerak >= ${need_gb} GiB (rootfs + apt cache + squashfs + ISO)"
  fi
  log "disk: ${avail_gb} GiB bo'sh ($path), kerak >= ${need_gb} GiB"
}

# --- 5. SOURCE_DATE_EPOCH majburiy ------------------------------------------

require_sde() {
  [ -n "${SOURCE_DATE_EPOCH:-}" ] \
    || die "SOURCE_DATE_EPOCH o'rnatilmagan -- determinizm yo'q (09 §3.3)"
  case "$SOURCE_DATE_EPOCH" in
    ''|*[!0-9]*) die "SOURCE_DATE_EPOCH butun son bo'lishi kerak: '$SOURCE_DATE_EPOCH'" ;;
  esac
  log "SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH ($(date -u -d "@$SOURCE_DATE_EPOCH" +%Y-%m-%dT%H:%M:%SZ))"
}

# --- 6. kerakli vositalar ---------------------------------------------------

require_tools() {
  local missing=() t
  for t in "$@"; do
    command -v "$t" >/dev/null 2>&1 || missing+=("$t")
  done
  if [ "${#missing[@]}" -gt 0 ]; then
    printf '[revix-iso] XATO: vositalar topilmadi: %s\n' "${missing[*]}" >&2
    printf '[revix-iso] Avval `bash iso/00-host-prepare.sh` ni bajaring (u YAGONA privilegiyali qadam).\n' >&2
    exit 1
  fi
}

# --- 7. yordamchi -----------------------------------------------------------

sha256_of() {
  sha256sum "$1" | awk '{print $1}'
}

# Deterministik tartiblash: LC_ALL=C MAJBURIY.
# NEGA: locale'ga bog'liq `sort` boshqa mashinada boshqa tartib beradi, demak
# squashfs ichidagi fayl tartibi o'zgaradi va determinizm (09 §3.1 R4) yo'q.
sorted_find() {
  ( cd "$1" && find . -print | LC_ALL=C sort )
}
