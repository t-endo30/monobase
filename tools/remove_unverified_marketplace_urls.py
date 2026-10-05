#!/usr/bin/env python3
"""検索結果ページを商品リンクとして扱わないための限定移行。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "content", "articles.json")

with open(PATH, encoding="utf-8") as f:
    articles = json.load(f)

for article in articles:
    if article.get("slug") == "ylt-ag30e-yamazen":
        url = article.get("amazon_url") or ""
        if "amazon.co.jp/s?" in url:
            article["amazon_url"] = ""
            article["updated"] = "2026-10-06"
            print("検索結果URLを除去しました: ylt-ag30e-yamazen")

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=1)
