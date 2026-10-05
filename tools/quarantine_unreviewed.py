#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPTレビュー合格を確認できない公開記事を公開停止する。"""
import datetime as dt
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    path = os.path.join(ROOT, "content", "articles.json")
    with open(path, encoding="utf-8") as f:
        articles = json.load(f)
    changed = []
    for article in articles:
        if not article.get("published"):
            continue
        score = (article.get("reviewed") or {}).get("score") or {}
        total = score.get("total")
        if isinstance(total, (int, float)) and total >= 90:
            continue
        article["published"] = False
        article["unpublished_reason"] = (
            "GPTレビュー合格（90点以上）を確認できないため、再レビュー待ち"
            f"（{dt.date.today().isoformat()}）"
        )
        changed.append(article.get("slug"))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=1)
    print(f"未合格記事を {len(changed)} 本停止しました")
    for slug in changed:
        print(f"  - {slug}")


if __name__ == "__main__":
    main()
