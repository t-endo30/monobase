#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公開記事から、下書き・停止記事への内部リンクだけを外す。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    path = os.path.join(ROOT, "content", "articles.json")
    with open(path, encoding="utf-8") as f:
        articles = json.load(f)
    published = {a.get("slug") for a in articles if a.get("published")}
    changed = 0
    for article in articles:
        for item in (article.get("next_problem") or {}).get("items", []):
            url = str(item.get("link_url") or "")
            if not url.startswith("articles/"):
                continue
            slug = url[len("articles/"):].removesuffix(".html")
            if slug not in published and item.get("link_url"):
                item.pop("link_url", None)
                item.pop("link_label", None)
                changed += 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=1)
    print(f"下書き・停止記事への内部リンクを {changed} 件整理しました")


if __name__ == "__main__":
    main()
