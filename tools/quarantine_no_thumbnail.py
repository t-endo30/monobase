#!/usr/bin/env python3
"""実物サムネイルを取得できない個別商品記事を公開対象から外す。"""
import json

PATH = "content/articles.json"
data = json.load(open(PATH, encoding="utf-8"))
changed = []
for a in data:
    if not a.get("published") or a.get("category") == "feature" or a.get("thumb"):
        continue
    imgs = a.get("shop_images") or {}
    if any(str(imgs.get(s) or "").strip().startswith("http") for s in ("rakuten", "yahoo")):
        continue
    a["published"] = False
    a["unpublished_reason"] = "実物サムネイルを取得できないため公開対象外（特集記事を除く）"
    changed.append(a.get("slug"))
json.dump(data, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"公開対象外に変更: {len(changed)}件")
for slug in changed:
    print(slug)
