#!/usr/bin/env bash
# REVIX: repozitoriyni NTFS'dan WSL ext4 workspace'iga ko'chiradi.
#
# NEGA: repo Windows NTFS'da turadi (manba va git), lekin o'lchov /mnt/c
# (drvfs) ustida bajarilMAYDI. Prober va psi_sampler 10 Hz'da yozadi; drvfs
# syscall latency'si o'lchovga jitter kiritadi, bu esa PREREGISTRATION.md
# 6.1-bo'limdagi +-P kvantlash da'vosini buzadi. Bajarish toza ext4'da ketadi.
#
# Run kataloglari ham ext4'da. datasets/ ga ko'chirish run TUGAGANDAN keyin,
# driver'dan TASHQARIDA bajariladi (04-shartnoma 1-bo'lim: driver mavjud run
# katalogiga yozmaydi).
#
# Ishlatilishi:
#   bash scripts/sync-to-ext4.sh
#   DEST=~/revix-work RUNS=~/revix-runs bash scripts/sync-to-ext4.sh
set -euo pipefail

SRC="${SRC:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
DEST="${DEST:-$HOME/revix-work}"
RUNS="${RUNS:-$HOME/revix-runs}"

# FAIL-CLOSED: drvfs ustida bajarishga yo'l qo'yilmaydi.
if [[ "$DEST" == /mnt/* || "$RUNS" == /mnt/* ]]; then
  echo "XATO: DEST yoki RUNS drvfs ustida. O'lchov ext4'da bo'lishi SHART." >&2
  exit 1
fi

mkdir -p "$DEST" "$RUNS"

# --delete: ext4 nusxasi manbaning aynan ko'zgusi, qoldiq fayl qolmaydi.
#
# .git NUSXALANADI. NEGA: run_meta.git_commit va git_dirty majburiy maydonlar
# (04-shartnoma 1.1) va validate.check_run_meta git_dirty ni confirmatory run
# uchun XATO deb hisoblaydi. revix doctor ning git_present/git_clean
# tekshiruvlari ham shu nusxada bajariladi. .git bo'lmasa o'lchov tekshirilishi
# mumkin bo'lgan commit'ga bog'lanmaydi -- PREREGISTRATION.md 7-bo'limdagi
# reproducibility sharti buziladi.
#
# QOIDA: ext4 nusxasidan HECH QACHON commit qilinmaydi. U faqat o'qish uchun
# provenance manbai; barcha git yozuvlari NTFS tomonida (bitta egalik, index
# aralashmaydi).
#
# datasets/ ham NUSXALANADI: tashlab ketilsa git uni o'chirilgan deb ko'radi va
# git_dirty buziladi. .claude/ (agent worktree'lari), __pycache__/ va
# .pytest_cache/ .gitignore'da, shuning uchun ularni tashlash daraxtni iflos
# qilmaydi.
rsync -a --delete \
  --exclude '.claude/' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  "$SRC"/ "$DEST"/

echo "sync: $SRC -> $DEST"
echo "runs: $RUNS"
printf 'fs(DEST)=%s\n' "$(stat -fc %T "$DEST")"
printf 'fs(RUNS)=%s\n' "$(stat -fc %T "$RUNS")"
printf 'git(DEST)=%s\n' "$(git -C "$DEST" rev-parse --short HEAD 2>&1)"
printf 'dirty(DEST)=%s\n' "$(test -z "$(git -C "$DEST" status --porcelain 2>/dev/null)" && echo no || echo YES)"
