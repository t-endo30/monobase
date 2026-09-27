#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sitemap.xml の各URLを Search Console の URL検査API に掛けて、
インデックス状況（登録済み / 検出-未登録 / クロール済み-未登録 /
リダイレクトあり…）を種類ごとに数えて一覧にする。

  $ python3 tools/gsc_inspect.py              # sitemap の全URL
  $ python3 tools/gsc_inspect.py --limit 50   # 先頭50件だけ

管理画面の「ページがインデックスに登録されなかった理由」と同じ内訳を、
どのURLがどの理由かまで出す（画面の方は理由ごとの件数しか分からず、
URLの一覧はエクスポートしないと読めない）。
何もコミットしない、見るだけの診断。

URL検査APIの割り当ては1プロパティあたり 2,000件/日・600件/分。
1件ずつしか調べられないので、件数が多いときは --limit で刻む。

必要なもの（tools/fetch_gsc_ranks.py と同じ）
  GSC_SITE_URL / GOOGLE_APPLICATION_CREDENTIALS
"""
import argparse, os, re, sys, time
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_gsc_ranks import get_service, site_url  # noqa: E402


def sitemap_urls():
    text = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
    return re.findall(r"<loc>([^<]+)</loc>", text)


def inspect(service, prop, url):
    res = service.urlInspection().index().inspect(
        body={"inspectionUrl": url, "siteUrl": prop,
              "languageCode": "ja"}).execute()
    return (res.get("inspectionResult") or {}).get("indexStatusResult") or {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="調べる件数（0=全部）")
    ap.add_argument("--offset", type=int, default=0, help="何件目から調べるか")
    ap.add_argument("--sleep", type=float, default=0.2, help="1件ごとの間隔（秒）")
    args = ap.parse_args()

    prop = site_url()
    if not prop:
        print("::error::サイトURLが分かりません。")
        return 1

    urls = sitemap_urls()[args.offset:]
    if args.limit:
        urls = urls[:args.limit]
    if not urls:
        print("調べるURLがありません。")
        return 0

    service = get_service()
    groups = defaultdict(list)
    failed = []

    print(f"サイト: {prop}")
    print(f"調べるURL: {len(urls)}件\n")
    for i, u in enumerate(urls, 1):
        try:
            r = inspect(service, prop, u)
        except Exception as ex:                                # noqa: BLE001
            failed.append((u, str(ex).split("\n")[0][:160]))
            continue
        state = r.get("coverageState") or "（不明）"
        groups[state].append((u, r))
        if i % 25 == 0:
            print(f"  …{i}/{len(urls)}件")
        time.sleep(args.sleep)

    print("\n=== インデックス状況の内訳 ===")
    for state, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(items):>4} 件  {state}")
    if failed:
        print(f"  {len(failed):>4} 件  ※検査できず")

    for state, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"\n--- {state}（{len(items)}件）---")
        for u, r in items:
            bits = []
            if r.get("lastCrawlTime"):
                bits.append(f"最終クロール {r['lastCrawlTime'][:10]}")
            if r.get("googleCanonical") and r.get("userCanonical") and \
               r["googleCanonical"].rstrip("/") != r["userCanonical"].rstrip("/"):
                bits.append(f"Google側の正規URL {r['googleCanonical']}")
            if r.get("robotsTxtState") not in (None, "ALLOWED"):
                bits.append(f"robots {r['robotsTxtState']}")
            if r.get("pageFetchState") not in (None, "SUCCESSFUL"):
                bits.append(f"取得 {r['pageFetchState']}")
            if r.get("indexingState") not in (None, "INDEXING_ALLOWED"):
                bits.append(f"{r['indexingState']}")
            tail = ("  … " + " / ".join(bits)) if bits else ""
            print(f"  {u}{tail}")

    if failed:
        print(f"\n--- 検査できなかったURL（{len(failed)}件）---")
        for u, msg in failed:
            print(f"  {u} … {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
