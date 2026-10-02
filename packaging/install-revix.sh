#!/usr/bin/env bash
# REVIX harness'ini tizimga (yoki image rootfs'iga) o'rnatadi.
#
# BU SKRIPT BAJARILMADI, sabab: guard kalibratsiyasi davom etmoqda.
#
# ==========================================================================
# QAROR: ODDIY DARAXT + systemd unit to'plami. `.deb` EMAS.
# ==========================================================================
# NEGA (1) -- loyiha qoidasi:
#   INSTALLATION.md §3: "`pip install`, `setup.py` yoki `pyproject.toml`
#   YO'Q -- bu ataylab. Repo `python3 -m revix.<modul>` sifatida repo
#   root'dan ishlatiladi."
#   Packaging sxemasi o'ylab topilmaydi; mavjudi hurmat qilinadi.
#
# NEGA (2) -- hal qiluvchi TEXNIK sabab, git:
#   * PREREGISTRATION.md §14.4 va 04-driver-va-analiz-shartnomasi.md §1.1:
#     `git_commit` va `git_dirty` -- MAJBURIY `run_meta` maydonlari.
#   * revix/cli.py:git_info() `git -C REPO_ROOT rev-parse HEAD` ni
#     chaqiradi, va `REPO_ROOT = os.path.dirname(PKG_DIR)`. `rev-parse`
#     nolga teng bo'lmagan kod qaytarsa `is_repo=False`, va
#     `check_git_present()` ham, `check_git_clean()` ham FAIL beradi
#     (kodda tekshirildi).
#   * `.deb` faqat CHECKOUT QILINGAN fayllarni ko'chiradi; `.deb` ichida
#     `.git` bo'lmaydi (va uni solish paket siyosatini buzadi).
#   => `.deb` -> git_present FAIL -> 0-FAIL qabul mezoni BUZILADI.
#
# Shuning uchun: HAQIQIY, MUSTAQIL git repozitoriysi o'rnatiladi.
# ==========================================================================
#
# Ishlatilishi:
#   # image build ichidan (mmdebstrap customize-hook):
#   REVIX_ROOTFS=/path/to/rootfs REVIX_FROM_IMAGE_BUILD=yes bash packaging/install-revix.sh
#   # tirik tizimda (root):
#   sudo bash packaging/install-revix.sh

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_SRC="${REVIX_REPO_SRC:-$(cd "$HERE/.." && pwd)}"

# Image build rejimida hamma yo'l rootfs ostida; tirik tizimda -- "/".
ROOTFS="${REVIX_ROOTFS:-/}"
PREFIX="${REVIX_INSTALL_PREFIX:-/opt/revix}"
MEASURE_USER="${REVIX_MEASURE_USER:-revix}"
MEASURE_UID="${REVIX_MEASURE_UID:-1000}"
DEST="${ROOTFS%/}$PREFIX"

log()  { printf '[install-revix] %s\n' "$*"; }
die()  { printf '[install-revix] XATO: %s\n' "$*" >&2; exit 1; }

[ -d "$REPO_SRC/.git" ] || [ -f "$REPO_SRC/.git" ] \
  || die "manba '$REPO_SRC' git repozitoriysi emas -> git_present/git_clean FAIL bo'lardi"
command -v git >/dev/null 2>&1 || die "git topilmadi"

SRC_COMMIT="$(git -C "$REPO_SRC" rev-parse HEAD)"
log "manba: $REPO_SRC @ $SRC_COMMIT"
log "maqsad: $DEST"

# --- (1) clone ---------------------------------------------------------------
#
# NEGA `git clone`, rsync/cp EMAS:
#   07-wsl-muhit-tekshiruvlari.md §4.3 o'lchagan FAIL aynan shu edi --
#   worktree'ning `.git` POINTER FAYLI boshqa mashinadagi absolute yo'lga
#   ishora qiladi, demak `git rev-parse` "not a git repository" beradi va
#   doctor #17/#18 FAIL bo'ladi (07 §1.2).
#   `git clone --no-hardlinks` TO'LIQ, MUSTAQIL `.git` KATALOGI yaratadi --
#   pointer emas. Bu xato sinfini butunlay yopadi.
#
# NEGA --no-hardlinks: hardlink'lar faqat BIR fayl tizimi ichida ishlaydi
#   va rootfs keyinroq squashfs'ga ko'chiriladi; hardlink'lar jimgina
#   nusxalarga aylanadi yoki clone buziladi.
#
# NEGA --no-local YO'Q va --shared YO'Q: `--shared` alternates orqali
#   MANBA repozitoriyga bog'lanadi -> image ichida obyektlar YO'Q bo'ladi
#   va `rev-parse` ishlamaydi.
rm -rf "$DEST"
mkdir -p "$(dirname "$DEST")"
git clone --no-hardlinks "$REPO_SRC" "$DEST"
git -C "$DEST" checkout --detach "$SRC_COMMIT"

# NEGA remote olib tashlanadi: image ichida `origin` build host'ining
# mahalliy yo'liga ishora qiladi -- u guest'da mavjud emas va chalg'ituvchi.
# `git fetch` ni ham imkonsiz qilish ataylab: image o'z commit'iga
# QOTIRILGAN.
git -C "$DEST" remote remove origin 2>/dev/null || true

# --- (2) toza daraxt tekshiruvi ---------------------------------------------
#
# NEGA tekshiriladi: doctor #18 `git_clean` -- confirmatory run uchun
# MAJBURIY (revix/cli.py:check_git_clean required matni). Clone Linux'da LF
# bilan checkout qiladi (.gitattributes: `* text=auto eol=lf`), demak toza
# bo'lishi KERAK. Bo'lmasa -- CRLF yoki `.gitignore` muammosi, va buni
# IMAGE QURILGANDAN KEYIN emas, HOZIR bilish kerak.
if [ -n "$(git -C "$DEST" status --porcelain)" ]; then
  git -C "$DEST" status --porcelain >&2
  die "clone IFLOS chiqdi -> doctor #18 git_clean WARN bo'lardi. CRLF (.gitattributes) yoki .gitignore muammosi."
fi
log "clone toza: $(git -C "$DEST" rev-parse --short HEAD)"

# --- (3) `dubious ownership` ni oldini olish ---------------------------------
#
# NEGA MAJBURIY: `$PREFIX` root egaligida bo'lsa va harness uid
# $MEASURE_UID bilan ishlasa, zamonaviy git "detected dubious ownership in
# repository" bilan rc != 0 qaytaradi. revix/cli.py:git_info() buni
# `is_repo=False` deb o'qiydi -> doctor #17 VA #18 IKKISI HAM FAIL ->
# 0-FAIL qabul mezoni buziladi, va `run_meta.git_commit` BO'SH qoladi
# (04-shartnoma §1.1: majburiy maydon).
#
# IKKI chora qo'llanadi, chunki bittasi yetarli emas:
#   (a) egalikni o'lchov foydalanuvchisiga berish -- asosiy yechim;
#   (b) `safe.directory` -- egalik baribir mos kelmasa (masalan boshqa uid
#       bilan ishga tushirilsa) qulf.
chown -R "$MEASURE_UID:$MEASURE_UID" "$DEST"

mkdir -p "${ROOTFS%/}/etc"
GITCONFIG="${ROOTFS%/}/etc/gitconfig"
if ! grep -q "directory = $PREFIX" "$GITCONFIG" 2>/dev/null; then
  cat >> "$GITCONFIG" <<EOF
[safe]
	directory = $PREFIX
EOF
fi
log "safe.directory + chown($MEASURE_UID) qo'llandi"

# --- (4) `revix` wrapper -----------------------------------------------------
#
# NEGA wrapper: qabul mezoni `revix doctor` deb yozilgan
# (09-iso-qurilishi.md §4), va `python3 -m revix.cli` `sys.path` da repo
# root'ni talab qiladi. Wrapper `cd` qilib `exec` qiladi -- hech qanday
# `pip`, hech qanday `setup.py`, INSTALLATION.md §3 buzilmaydi.
install -D -m 0755 "$HERE/bin/revix" "${ROOTFS%/}/usr/local/bin/revix"
log "wrapper: /usr/local/bin/revix -> python3 -m revix.cli"

# --- (5) systemd unit'lari ---------------------------------------------------
#
# NEGA bu yerda EMAS: unit'lar iso/hooks/customize-20-systemd.sh da
# o'rnatiladi va yoqiladi, chunki qaysi unit YOQILADI degan qaror
# IMAGE SIYOSATI -- u harness o'rnatishning bir qismi emas.
# Tirik tizimda qo'lda o'rnatish uchun yo'llar:
#   packaging/systemd/user@.service.d/10-revix-delegate.conf
#   packaging/systemd/revix-io-delegate.service
#   packaging/systemd/revix-swapfile.service
#   packaging/systemd/revix-harness.slice      (O'RNATILADI, YOQILMAYDI)
if [ "${REVIX_FROM_IMAGE_BUILD:-}" != "yes" ]; then
  cat <<'MSG'
[install-revix] ESLATMA: systemd unit'lari O'RNATILMADI.
  Tirik tizimda ularni qo'lda joylashtiring (packaging/systemd/), va
  `revix-harness.slice` ni YOQMANG -- u o'lchov topologiyasini
  o'zgartiradi va PREREGISTRATION.md §15 muhit fingerprint'iga ta'sir
  qiladi (09-iso-qurilishi.md §5.3, §7).
MSG
fi

# --- (6) tekshiruv -----------------------------------------------------------
log "o'rnatildi: $DEST @ $(git -C "$DEST" rev-parse --short HEAD)"
cat <<'MSG'
[install-revix] INTEGRITY: `revix doctor` BU SKRIPT TOMONIDAN ISHGA
  TUSHIRILMADI. Uning 0 FAIL berishi -- GIPOTEZA
  (09-iso-qurilishi.md §8 G3). O'lchovi:
      revix doctor --json | jq '[.checks[]|select(.status=="FAIL")]|length'
MSG
