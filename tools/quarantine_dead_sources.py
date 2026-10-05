#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""商品ページが404等で到達できない公開記事を公開停止する。"""
import json
import os
import datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    report = os.path.join(ROOT, "reports", "product-source-collection.json")
    articles_path = os.path.join(ROOT, "content", "articles.json")
    with open(report, encoding="utf-8") as f:
        rows = json.load(f)
    dead = {row["slug"] for row in rows if row.get("status") != 200}
    with open(articles_path, encoding="utf-8") as f:
        articles = json.load(f)
    changed = []
    for article in articles:
        if article.get("published") and article.get("slug") in dead:
            article["published"] = False
            article["unpublished_reason"] = (
                "商品ページが到達不能で、現在の販売・商品根拠を確認できないため"
                f"（{dt.date.today().isoformat()}）"
            )
            changed.append(article["slug"])
    with open(articles_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=1)
    print(f"到達不能な商品ページの記事を {len(changed)} 本停止しました")
    for slug in changed:
        print(f"  - {slug}")


if __name__ == "__main__":
    main()
