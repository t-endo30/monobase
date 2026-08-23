#!/bin/bash
# ============================================================
# assets/img/ の画像を一括圧縮する（macOS 標準の sips を使用）
#   使い方:  bash tools/optimize-images.sh [最大幅]
#   例    :  bash tools/optimize-images.sh 1200
#
# cwebp がインストールされていれば WebP にも変換します。
#   brew install webp
# ============================================================
set -euo pipefail

MAXW="${1:-1200}"
DIR="$(cd "$(dirname "$0")/.." && pwd)/assets/img"
mkdir -p "$DIR"

shopt -s nullglob nocaseglob
files=("$DIR"/*.jpg "$DIR"/*.jpeg "$DIR"/*.png)
if [ ${#files[@]} -eq 0 ]; then
  echo "圧縮対象の画像がありません: $DIR"
  exit 0
fi

echo "最大幅 ${MAXW}px にリサイズします（対象 ${#files[@]} 件）"
total_before=0
total_after=0

for f in "${files[@]}"; do
  before=$(stat -f%z "$f")
  total_before=$((total_before + before))

  # 横幅がMAXWを超える場合のみ縮小
  w=$(sips -g pixelWidth "$f" | awk '/pixelWidth/{print $2}')
  if [ "$w" -gt "$MAXW" ]; then
    sips --resampleWidth "$MAXW" "$f" >/dev/null
  fi
  # JPEG は再エンコードで軽量化
  case "$f" in
    *.jpg|*.jpeg|*.JPG|*.JPEG)
      sips -s format jpeg -s formatOptions 78 "$f" --out "$f" >/dev/null ;;
  esac

  # WebP 版を生成（cwebp があるときだけ）
  if command -v cwebp >/dev/null 2>&1; then
    out="${f%.*}.webp"
    cwebp -quiet -q 82 "$f" -o "$out"
    echo "  WebP生成: $(basename "$out") ($(($(stat -f%z "$out")/1024))KB)"
  fi

  after=$(stat -f%z "$f")
  total_after=$((total_after + after))
  printf "  %-40s %5dKB → %5dKB\n" "$(basename "$f")" $((before/1024)) $((after/1024))
done

echo
echo "合計: $((total_before/1024))KB → $((total_after/1024))KB （$(( (total_before-total_after)*100/total_before ))% 削減）"
echo "仕上げに: python3 tools/check_images.py"
