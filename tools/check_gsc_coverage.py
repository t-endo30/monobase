#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sitemap.xml に載っている全URLのうち、Search Consoleで一度も
表示（インプレッション）が付いていないものを洗い出す。

インデックスされていない、またはインデックスはされていても
どんな検索語でも一度も表示されていないページの手がかりになる
（インデックス状況を直接見る urlInspection API は1件ずつしか
調べられず件数が多いと重いので、まずは searchanalytics の
page ディメンションで「表示回数が記録されているURL集合」を
まとめて取り、無いものを容疑者として出す簡易版）。

  $ python3 tools/check_gsc_coverage.py            # 直近90日で集計
  $ python3 tools/check_gsc_coverage.py --days 180

必要なもの（tools/fetch_gsc_ranks.py と同じ）
  GSC_SITE_URL / GOOGLE_APPLICATION_CREDENTIALS
"""
import argparse, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_gsc_ranks import get_service, query, date_range, site_url  # noqa: E402


def sitemap_urls():
    text = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
    return re.findall(r"<loc>([^<]+)</loc>", text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90,
                    help="集計期間（既定90日）")
    args = ap.parse_args()

    prop = site_url()
    if not prop:
        print("::error::サイトURLが分かりません。")
        return 1

    urls = sitemap_urls()
    if not urls:
        print("sitemap.xml にURLがありません。")
        return 0

    service = get_service()

    try:
        sm = service.sitemaps().get(siteUrl=prop,
                                     feedpath=f"{prop.rstrip('/')}/sitemap.xml").execute()
        print("--- sitemap.xml の提出状況（Search Console）---")
        print(f"最終取得: {sm.get('lastSubmitted')} / 最終ダウンロード: {sm.get('lastDownloaded')}")
        for c in sm.get("contents", []):
            print(f"  種別:{c.get('type')} 送信済み:{c.get('submitted')} "
                  f"インデックス済み:{c.get('indexed')}")
        errs = sm.get("errors") or []
        warns = sm.get("warnings") or []
        if errs or warns:
            print(f"  エラー:{errs} 警告:{warns}")
        print()
    except Exception as ex:                                    # noqa: BLE001
        print(f"::warning::sitemap.xml の提出状況を取得できませんでした: {ex}\n")

    start, end = date_range(args.days)
    rows = query(service, prop, start, end, dimensions=["page"], row_limit=5000)
    seen = {}
    for r in rows:
        page = (r.get("keys") or [None])[0]
        if page:
            seen[page.rstrip("/")] = int(r.get("impressions", 0))

    zero, low = [], []
    for u in urls:
        key = u.rstrip("/")
        imp = seen.get(key)
        if imp is None:
            zero.append(u)
        elif imp <= 2:
            low.append((u, imp))

    print(f"サイトURL: {prop}")
    print(f"集計期間: {start} 〜 {end}（{args.days}日）")
    print(f"sitemap.xml のURL数: {len(urls)}")
    print(f"GSCに表示回数の記録があるURL数: {len(seen)}")
    print(f"\n一度も表示されていない（要確認・{len(zero)}件）:")
    for u in zero:
        print(f"  ::warning:: {u}")
    if low:
        print(f"\n表示はあるが2回以下（{len(low)}件・参考）:")
        for u, imp in low:
            print(f"  {u} … {imp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
