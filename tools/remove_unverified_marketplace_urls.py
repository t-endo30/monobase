#!/usr/bin/env python3
"""検索結果ページを商品リンクとして扱わないための限定移行。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "content", "articles.json")

with open(PATH, encoding="utf-8") as f:
    articles = json.load(f)

SEARCH_URL_ARTICLES = {"ylt-ag30e-yamazen"}
SEARCH_URL_ARTICLES.add("cellularline-iphone18pro-iphone18promax")

for article in articles:
    if article.get("slug") in SEARCH_URL_ARTICLES:
        url = article.get("amazon_url") or ""
        if "amazon.co.jp/s?" in url:
            article["amazon_url"] = ""
            article["updated"] = "2026-10-06"
            print(f"検索結果URLを除去しました: {article['slug']}")
    if article.get("slug") == "cellularline-iphone18pro-iphone18promax":
        if article.get("yahoo_url"):
            article["yahoo_url"] = ""
            article["updated"] = "2026-10-06"
            print("商品番号未照合のYahoo! URLを除去しました: cellularline-iphone18pro-iphone18promax")

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=1)
