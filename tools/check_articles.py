#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公開設定の記事に、公開に足る中身があるかを検査する。

管理画面の「公開に」ボタンは中身を検査せず切り替わるため、
空の記事がそのまま本番に出る事故を、ここで止める。

  $ python3 tools/check_articles.py
"""
import json, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MIN_BLOCKS = 3      # summary/pros/cons/scenes/voices の合計要素数の下限
MIN_CHARS = 5000    # 本文の文字数の下限（docs/article-prompt.md と揃える）
MAX_CHARS = 7600    # 上限。長すぎる記事は読み切られない

# 文字数に数えないキー（識別子・URL・分類など、読者が読む文ではない）
SKIP_KEYS = {"slug", "thumb", "banner", "amazon_url", "asin", "date", "updated",
             "icon", "category", "sub", "tags", "cta_label", "image_prompt",
             "feature_of", "feature_covers"}


def body_chars(a):
    """記事本文の文字数。入れ子の配列・辞書をたどって文字列だけ数える。
       HTMLタグは読者が読む文字ではないので取り除く。"""
    buf = []

    def walk(v):
        if isinstance(v, str):
            buf.append(re.sub(r"<[^>]+>", "", v))
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, dict):
            for k, x in v.items():
                if k not in SKIP_KEYS:
                    walk(x)

    for k, v in a.items():
        if k not in SKIP_KEYS:
            walk(v)
    return len("".join(buf))


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

        n = body_chars(a)
        if n < MIN_CHARS:
            warns.append(f"{slug}: 本文が {n:,} 文字です（下限 {MIN_CHARS:,} 文字）。"
                         "表だけでなく、地の文を足してください")
        elif n > MAX_CHARS:
            warns.append(f"{slug}: 本文が {n:,} 文字あります（上限 {MAX_CHARS:,} 文字）")

    # 内部リンク切れの検査：公開記事から未公開記事へのリンクは404になる
    pubslugs = {a.get("slug") for a in arts if a.get("published")}
    allslugs = {a.get("slug") for a in arts}
    for a in arts:
        if not a.get("published"):
            continue
        for it in (a.get("next_problem") or {}).get("items", []):
            url = (it.get("link_url") or "").strip()
            # カテゴリーページへのリンク。site.json の分類を変えると
            # 古いURLが残り、そのまま404になるためここで止める。
            if url.startswith("category-"):
                if not os.path.exists(os.path.join(ROOT, url)):
                    errors.append(f"{a['slug']}: リンク先のカテゴリーページがありません（{url}）")
                continue
            if not url.startswith("articles/"):
                continue
            target = url[len("articles/"):].removesuffix(".html")
            if target not in allslugs:
                errors.append(f"{a['slug']}: リンク先の記事が存在しません（{url}）")
            elif target not in pubslugs:
                errors.append(f"{a['slug']}: リンク先が下書きのままです（{url}）")

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
