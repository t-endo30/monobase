#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""商品同定または個別商品URLが無い記事を公開停止する。記事自体は削除しない。"""
import argparse
import datetime as dt
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from article_evidence import assessment


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    path = os.path.join(ROOT, "content", "articles.json")
    with open(path, encoding="utf-8") as f:
        articles = json.load(f)
    changed = []
    for article in articles:
        result = assessment(article)
        if result["category"] != "公開停止候補" or not article.get("published"):
            continue
        changed.append(article.get("slug"))
        if args.apply:
            article["published"] = False
            article["unpublished_reason"] = (
                "商品同定情報または個別商品URLが不足し、公式根拠を確認できないため"
                f"（{dt.date.today().isoformat()}）"
            )
    print(f"公開停止対象: {len(changed)}本")
    for slug in changed:
        print(f"  - {slug}")
    if args.apply:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=1)
        print("articles.jsonへ反映しました。記事本文は削除していません。")


if __name__ == "__main__":
    main()
