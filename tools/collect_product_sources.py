#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""既存の個別販売URLを読み取り、到達性とページ識別情報を調べる。

記事本文は変更しない。取得できた内容は、公式資料を確認するための調査キューにする。
"""
import concurrent.futures
import html
import json
import os
import re
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fetch(item):
    slug, url = item
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 monobase-source-audit"})
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            raw = response.read(400_000).decode("utf-8", errors="replace")
            status = response.status
            final_url = response.geturl()
        def meta(name):
            m = re.search(r'<meta[^>]+(?:property|name)=["\']' + re.escape(name) +
                          r'["\'][^>]+content=["\']([^"\']*)', raw, re.I)
            return html.unescape(m.group(1)).strip() if m else ""
        title = meta("og:title") or (re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S) or ["", ""])[1]
        desc = meta("description") or meta("og:description")
        return {"slug": slug, "url": url, "status": status, "final_url": final_url,
                "title": re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", title))).strip(),
                "description": re.sub(r"\s+", " ", desc).strip()[:500]}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        return {"slug": slug, "url": url, "status": None, "error": str(exc)[:200]}


def main():
    path = os.path.join(ROOT, "content", "articles.json")
    with open(path, encoding="utf-8") as f:
        articles = json.load(f)
    items = []
    for article in articles:
        if not article.get("published"):
            continue
        url = article.get("rakuten_url") or article.get("yahoo_url")
        if url:
            items.append((article.get("slug"), url))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(fetch, items))
    out = os.path.join(ROOT, "reports", "product-source-collection.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    ok = sum(1 for row in rows if row.get("status") == 200)
    print(f"調査対象 {len(rows)}本 / 到達200 {ok}本 / その他 {len(rows)-ok}本")
    print(f"調査キュー: {out}")


if __name__ == "__main__":
    main()
