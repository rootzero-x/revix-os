#!/usr/bin/env bash
# REVIX image build, qadam 50: build fingerprint + checksum'lar.
#
# BU SKRIPT BAJARILMADI, sabab: guard kalibratsiyasi davom etmoqda.
#
# NEGA fingerprint:
# PREREGISTRATION.md §15 "Muhit fingerprint va undan kelib chiqadigan
# cheklovlar" muzlatilgan bo'lim: natija qaysi muhitda olinganini aytib
# bo'lmasa, natijaning o'zi tekshirilmaydi. §14.4 esa `run_meta` ning
# majburiy maydonlarini aynan "reproducibility" bilan asoslaydi.
#
# Image uchun shu talab IMAGE DARAJASIDA takrorlanadi: run `run_meta` orqali
# kodga bog'lanadi, image esa `build-fingerprint.json` orqali PAKET
# TO'PLAMIGA, SNAPSHOT'ga va FROZEN HUJJAT HASH'iga bog'lanadi.
#
# Bu fayl ISO'ning checksum'i YONIDA commit qilinadi.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./config.sh
. "$HERE/config.sh"
# shellcheck source=./lib/common.sh
. "$HERE/lib/common.sh"

require_not_root
require_sde

ISO_PATH="$OUT_DIR/$ISO_NAME"
MANIFEST="$OUT_DIR/manifest.txt"
FP="$OUT_DIR/build-fingerprint.json"

[ -f "$ISO_PATH" ]  || die "ISO yo'q: $ISO_PATH -- avval 40-make-iso.sh"
[ -f "$MANIFEST" ]  || die "manifest yo'q -- avval 20-record-manifest.sh"

# --- frozen hujjatning hash'i -----------------------------------------------
#
# NEGA MAJBURIY: 04-driver-va-analiz-shartnomasi.md §1.1 va
# PREREGISTRATION.md §14.4 `preregistration_sha256` ni `run_meta` ning
# majburiy maydoni qiladi, va `validate.check_run_meta` uni o'qiydi
# (revix/validate.py:735). Image ichidagi nusxa manbadagisi bilan MOS
# bo'lishi kerak, aks holda guest'da olingan run boshqa shartnomaga
# bog'langan bo'ladi.
#
# .gitattributes (`* text=auto eol=lf`) nega muhim: u faylning o'zida
# yozilgan -- CRLF "matn fayllarining sha256'ini o'zgartiradi, va
# run_meta.preregistration_sha256 esa muzlatilgan hujjatning hash'i bo'lishi
# SHART". Linux'dagi clone LF bilan checkout qiladi, demak hash barqaror.
PREREG_SHA="$(sha256_of "$REPO_SRC/PREREGISTRATION.md")"
PREREG_IMG_SHA="$(sha256_of "$ROOTFS_DIR/${INSTALL_PREFIX#/}/PREREGISTRATION.md")"
if [ "$PREREG_SHA" != "$PREREG_IMG_SHA" ]; then
  die "PREREGISTRATION.md hash'i mos emas: manba=$PREREG_SHA image=$PREREG_IMG_SHA (CRLF yoki noto'g'ri commit?)"
fi
log "preregistration_sha256: $PREREG_SHA (manba va image MOS)"

SRC_COMMIT="$(git -C "$REPO_SRC" rev-parse HEAD)"
SRC_DIRTY="$(test -z "$(git -C "$REPO_SRC" status --porcelain)" && echo false || echo true)"
IMG_COMMIT="$(git -C "$ROOTFS_DIR/${INSTALL_PREFIX#/}" rev-parse HEAD)"
if [ "$SRC_COMMIT" != "$IMG_COMMIT" ]; then
  die "image ichidagi commit manbadan farq qiladi: $IMG_COMMIT != $SRC_COMMIT"
fi

# --- vosita versiyalari -----------------------------------------------------
#
# NEGA qayd etiladi: vosita versiyasi chiqishni o'zgartiradi (masalan
# mksquashfs'ning default siqish parametrlari minor versiyalar orasida
# o'zgargan). Versiya yozilmasa, ikki build farq qilganda sababini
# aniqlashning yo'li yo'q.
tool_ver() { command -v "$1" >/dev/null 2>&1 && { "$1" "${2:---version}" 2>&1 | head -1; } || echo "yo'q"; }

json_str() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

cat > "$FP" <<EOF
{
  "schema": "revix-image-fingerprint/v1",
  "_izoh": "Bu fayl FAQAT haqiqiy build natijasida to'ldiriladi. 09-iso-qurilishi.md §3.1 R6.",

  "scope_statement": "Debian + REVIX measurement harness. Research appliance, EMAS 'REVIX OS'. Adaptive recovery engine YO'Q (PREREGISTRATION.md §0, §13; README.md 'Loyiha nima EMAS').",

  "suite": "$(json_str "$SUITE")",
  "arch": "$(json_str "$ARCH")",
  "snapshot_ts": "$(json_str "$SNAPSHOT_TS")",
  "mirror": "$(json_str "$MIRROR")",
  "source_date_epoch": $SOURCE_DATE_EPOCH,

  "git_commit": "$(json_str "$SRC_COMMIT")",
  "git_dirty_at_build": $SRC_DIRTY,
  "preregistration_sha256": "$(json_str "$PREREG_SHA")",

  "manifest_sha256": "$(json_str "$(sha256_of "$MANIFEST")")",
  "package_count": $(grep -cv '^#' "$MANIFEST"),
  "iso_name": "$(json_str "$ISO_NAME")",
  "iso_sha256": "$(json_str "$(sha256_of "$ISO_PATH")")",
  "iso_bytes": $(stat -c %s "$ISO_PATH"),
  "squashfs_sha256": "$(json_str "$(sha256_of "$STAGE_DIR/live/filesystem.squashfs")")",

  "oomd_installed": "$(json_str "$OOMD_INSTALLED")",
  "oomd_decision_why": "09-iso-qurilishi.md §4.4: image'da desktop sessiyasi yo'q; oomd o'rnatilsa o'lchovning O'ZIGA aralashadi. CHEKLOV: image 01/00 tasvirlagan 'oomd armed desktop' muhitini QAYTA ISHLAB CHIQARMAYDI.",

  "build_tools": {
    "mmdebstrap": "$(json_str "$(tool_ver mmdebstrap)")",
    "mksquashfs": "$(json_str "$(tool_ver mksquashfs -version)")",
    "xorriso": "$(json_str "$(tool_ver xorriso)")",
    "grub_mkstandalone": "$(json_str "$(tool_ver grub-mkstandalone)")",
    "dpkg": "$(json_str "$(tool_ver dpkg)")",
    "git": "$(json_str "$(tool_ver git)")"
  },

  "reproducibility_claims": {
    "package_set_recorded": "DA'VO QILINADI -- manifest.txt + sha256 (R2)",
    "composition_repeatable": "DA'VO QILINADI, SHARTLI -- snapshot.debian.org ga bog'liq (R1, N7)",
    "bit_identical_iso": "DA'VO QILINMAYDI -- 09 §3.2 N1-N6 (initramfs, dpkg tartibi, maintainer script keshlari, machine-id, GRUB memdisk, Debian .deb larining o'zi)",
    "measurement_equivalent": "GIPOTEZA -- o'lchovi: ikki ISO + diffoscope + ikkisida ham `revix doctor --json` checks[].status bir xil"
  },

  "not_measured": [
    "ISO boot qilinmadi",
    "revix doctor image ichida ishga tushirilmadi",
    "ikki marta qurib taqqoslanmadi (diffoscope)",
    "guard testi guest ichida bajarilmadi"
  ]
}
EOF

log "fingerprint: $FP"

# --- checksum'lar -----------------------------------------------------------
( cd "$OUT_DIR" && sha256sum "$ISO_NAME" manifest.txt build-fingerprint.json > SHA256SUMS )
log "SHA256SUMS: $OUT_DIR/SHA256SUMS"

cat <<'MSG'

[revix-iso] ESLATMA -- INTEGRITY:
  Bu skript faqat FAYL hash'larini yozadi. U quyidagilarni DA'VO QILMAYDI:
    * image boot bo'ladi            -> GIPOTEZA (09 §8 G2)
    * revix doctor 0 FAIL beradi    -> GIPOTEZA (09 §8 G3)
    * ISO bit-identik takrorlanadi  -> DA'VO QILINMAYDI (09 §3.2)
  Ularning har biri uchun o'lchov 09 §8 jadvalida yozilgan.
MSG
