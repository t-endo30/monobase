#!/usr/bin/env python3
import json
import re

PATH = "content/articles.json"
TARGETS = {
    "samsung-galaxy-a57-128gb-awesome-navy",
    "tp-link-archer-ax3000-ax3000-wi-fi",
}

def clean(value):
    if isinstance(value, str):
        value = value.replace("口コミ", "利用者の声")
        value = value.replace("レビュー41件", "利用者評価")
        value = value.replace("レビュー100件", "利用者評価")
        value = re.sub(r"\d+件", "", value)
        value = value.replace("レビューを読み込んで見えたこと", "確認できた情報")
        value = value.replace("レビュー・利用者の声", "利用者評価")
        value = value.replace("レビュー分析", "利用者評価の整理")
        value = value.replace("Tetherアプリ", "公式設定ガイド")
        return value
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k not in {"count"}}
    return value

with open(PATH, encoding="utf-8") as f:
    articles = json.load(f)
for article in articles:
    if article.get("slug") in TARGETS:
        article.update(clean(article))
        if article.get("slug") == "tp-link-archer-ax3000-ax3000-wi-fi":
            article["thumb"] = "https://static.tp-link.com/upload/image-line/Archer_AX3000-JP-2_large_20230216020744e.jpg"
        article["updated"] = "2026-10-07"
with open(PATH, "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=1)
print("対象2記事を正規化しました")
