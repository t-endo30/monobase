#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次情報・レビュー根拠を確認できない追加調査記事を公開停止する。"""
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
        facts = article.get("facts") or []
        if isinstance(facts, str):
            facts = [facts]
        has_official = bool((article.get("official_url") or "").strip()) or bool(facts)
        has_reviews = bool(article.get("voices") or article.get("review_texts"))
        if has_official and (has_reviews or not article.get("review_stats")):
            continue
        article["published"] = False
        article["unpublished_reason"] = (
            "公式資料または確認可能なレビュー本文が不足し、追加調査なしでは"
            f"Google向けの根拠を満たせないため（{dt.date.today().isoformat()}）"
        )
        changed.append(article.get("slug"))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=1)
    print(f"追加調査未解決の記事を {len(changed)} 本停止しました")
    for slug in changed:
        print(f"  - {slug}")


if __name__ == "__main__":
    main()
