#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公開設定の記事に、公開に足る中身があるかを検査する。

管理画面の「公開に」ボタンは中身を検査せず切り替わるため、
空の記事がそのまま本番に出る事故を、ここで止める。

  $ python3 tools/check_articles.py
"""
import json, io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MIN_BLOCKS = 3      # summary/pros/cons/scenes/voices の合計要素数の下限


def main():
    p = os.path.join(ROOT, "content", "articles.json")
    arts = json.load(io.open(p, encoding="utf-8"))
    errors, warns = [], []

    for a in arts:
        if not a.get("published"):
            continue
        slug = a.get("slug", "(slug未設定)")

        blocks = sum(len(a.get(k, [])) for k in
                     ("summary", "pros", "cons", "scenes", "voices"))
        nf = len((a.get("not_for") or {}).get("items", []))
        total = blocks + nf

        if total == 0:
            errors.append(f"{slug}: 本文が空のまま公開設定になっています")
        elif total < MIN_BLOCKS:
            warns.append(f"{slug}: 本文の要素が {total} 個しかありません")

        if not a.get("description"):
            errors.append(f"{slug}: メタディスクリプションが未設定です")
        if not a.get("excerpt"):
            errors.append(f"{slug}: カード用の抜粋が未設定です")
        if not a.get("asin") and not a.get("amazon_url"):
            warns.append(f"{slug}: ASIN・リンクのどちらも未設定です")
        if not a.get("conclusion"):
            warns.append(f"{slug}: まとめが未記入です")

    pub = sum(1 for a in arts if a.get("published"))
    print(f"公開記事 {pub} 本を検査")

    for w in warns:
        print(f"::warning::{w}")
    if errors:
        print(f"::error::公開できない記事が {len(errors)} 件あります。")
        for e in errors:
            print(f"  ❌ {e}")
        print("\n管理画面で内容を入力するか、下書きに戻してください。")
        return 1

    print("✅ すべての公開記事に必要な内容が揃っています。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
