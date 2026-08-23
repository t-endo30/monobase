#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assets/img/ の画像サイズを検査する。
   1枚が上限を超えていたらビルドを失敗させ、圧縮忘れを防ぐ。
   $ python3 tools/check_images.py
"""
import os, sys

MAX_KB = 300          # 1枚あたりの上限
WARN_TOTAL_MB = 50    # 合計がこれを超えたら警告

IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "img")

def main():
    if not os.path.isdir(IMG_DIR):
        print("assets/img がありません。スキップします。")
        return 0
    over, total = [], 0
    for name in sorted(os.listdir(IMG_DIR)):
        if not name.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")):
            continue
        size = os.path.getsize(os.path.join(IMG_DIR, name))
        total += size
        if size > MAX_KB * 1024:
            over.append((name, size))

    print(f"画像 {len(os.listdir(IMG_DIR))} 件 / 合計 {total/1024/1024:.1f}MB")
    if total > WARN_TOTAL_MB * 1024 * 1024:
        print(f"::warning::画像の合計が {WARN_TOTAL_MB}MB を超えています。不要な画像を整理してください。")

    if over:
        print(f"::error::{MAX_KB}KB を超える画像があります。tools/optimize-images.sh で圧縮してください。")
        for n, s in over:
            print(f"  - {n}: {s/1024:.0f}KB")
        return 1
    print("✅ すべての画像が上限内です。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
