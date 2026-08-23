#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AmazonのURL（短縮リンク含む）から ASIN を取り出す。

  $ python3 tools/resolve_asin.py "https://amzn.to/xxxxxx" "https://www.amazon.co.jp/dp/B0XXXXXXXX"
  $ python3 tools/resolve_asin.py --check     # articles.json のASINを検証

短縮リンクはリダイレクト先のURLを見るだけで、
商品ページの中身は取得しない（スクレイピングにあたらない）。
"""
import re, sys, json, io, os, urllib.request, urllib.error

PATTERNS = [
    r"/dp/([A-Z0-9]{10})",
    r"/gp/product/([A-Z0-9]{10})",
    r"/gp/aw/d/([A-Z0-9]{10})",
    r"/product/([A-Z0-9]{10})",
    r"[?&]asin=([A-Z0-9]{10})",
]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def from_url(url):
    """URL文字列からASINを抽出する。"""
    if re.fullmatch(r"[A-Z0-9]{10}", url.strip(), re.I):
        return url.strip().upper()
    for pat in PATTERNS:
        m = re.search(pat, url, re.I)
        if m:
            return m.group(1).upper()
    return None


def resolve(url, timeout=10):
    """短縮リンクならリダイレクトを追って最終URLからASINを取り出す。"""
    asin = from_url(url)
    if asin:
        return asin, url

    req = urllib.request.Request(url, method="HEAD", headers={
        "User-Agent": "Mozilla/5.0 (compatible; monobase-linkcheck/1.0)"
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            final = res.geturl()
    except urllib.error.HTTPError as ex:
        final = ex.url or url
    except Exception as ex:
        return None, f"取得失敗: {ex}"
    return from_url(final), final


def check_articles():
    """articles.json の asin を検証する。"""
    p = os.path.join(ROOT, "content", "articles.json")
    arts = json.load(io.open(p, encoding="utf-8"))
    ng = 0
    for a in arts:
        asin = (a.get("asin") or "").strip()
        if not asin:
            state = "未設定" if a.get("published") else "未設定（下書き）"
            mark = "⚠" if a.get("published") else "・"
            if a.get("published") and not a.get("amazon_url"):
                ng += 1
        elif re.fullmatch(r"[A-Z0-9]{10}", asin):
            state, mark = asin, "✅"
        else:
            state, mark = f"形式エラー: {asin}", "❌"
            ng += 1
        print(f"  {mark} {a['slug']:34} {state}")
    print(f"\n{'❌ 要修正 ' + str(ng) + ' 件' if ng else '✅ 問題なし'}")
    return 1 if ng else 0


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0
    if args[0] == "--check":
        return check_articles()

    for url in args:
        asin, final = resolve(url)
        if asin:
            print(f"✅ {asin}")
            if final != url:
                print(f"   展開先: {final}")
        else:
            print(f"❌ ASINを取り出せませんでした: {final}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
