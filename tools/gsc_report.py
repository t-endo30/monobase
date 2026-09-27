#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search Console の「検索パフォーマンス」画面と同じ集計をログに出す。

  $ python3 tools/gsc_report.py                 # 直近28日（前28日と比較）
  $ python3 tools/gsc_report.py --days 90

管理画面（search.google.com/search-console/performance/search-analytics）は
ログインが要るため人にしか開けない。同じ数字を searchanalytics API から
取って、合計・推移・クエリ・ページ・デバイス・検索面ごとに出す。
何もコミットしない、見るだけの診断（tools/check_gsc_coverage.py と同じ扱い）。

必要なもの（tools/fetch_gsc_ranks.py と同じ）
  GSC_SITE_URL / GOOGLE_APPLICATION_CREDENTIALS
"""
import argparse, os, sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_gsc_ranks import get_service, query, site_url  # noqa: E402


def span(days, back=0):
    """直近 days 日（GSCが確定していない当日・前日を避けて昨日まで）。
    back=1 でその1つ前の同じ長さの期間。"""
    end = date.today() - timedelta(days=1 + back * days)
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def totals(service, prop, start, end):
    rows = query(service, prop, start, end, dimensions=[], row_limit=1)
    if not rows:
        return {"clicks": 0, "impressions": 0, "ctr": 0.0, "position": 0.0}
    r = rows[0]
    return {"clicks": int(r.get("clicks", 0)),
            "impressions": int(r.get("impressions", 0)),
            "ctr": float(r.get("ctr", 0.0)),
            "position": float(r.get("position", 0.0))}


def diff(now, before, key, lower_is_better=False):
    a, b = now[key], before[key]
    if not b:
        return "（前期間は0）"
    pct = (a - b) / b * 100
    good = (pct < 0) if lower_is_better else (pct > 0)
    mark = "↑" if pct > 0 else ("↓" if pct < 0 else "→")
    return f"{mark}{abs(pct):.0f}%（前期間 {b:.1f}）{'' if good or pct == 0 else ' ※悪化'}"


def table(rows, label, limit=20):
    print(f"\n--- {label}（上位{limit}）---")
    if not rows:
        print("  （データなし）")
        return
    print(f"  {'クリック':>6} {'表示':>7} {'CTR':>6} {'順位':>6}  キー")
    for r in rows[:limit]:
        key = " / ".join(r.get("keys") or [])
        print(f"  {int(r.get('clicks',0)):>6} {int(r.get('impressions',0)):>7} "
              f"{float(r.get('ctr',0))*100:>5.1f}% {float(r.get('position',0)):>6.1f}  {key}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=28, help="集計期間（既定28日）")
    ap.add_argument("--limit", type=int, default=20, help="各表の行数（既定20）")
    args = ap.parse_args()

    prop = site_url()
    if not prop:
        print("::error::サイトURLが分かりません。")
        return 1
    service = get_service()

    start, end = span(args.days)
    pstart, pend = span(args.days, back=1)
    now = totals(service, prop, start, end)
    before = totals(service, prop, pstart, pend)

    print(f"サイト: {prop}")
    print(f"集計期間: {start} 〜 {end}（{args.days}日）")
    print(f"比較対象: {pstart} 〜 {pend}\n")
    print("=== 合計 ===")
    print(f"  クリック数 : {now['clicks']:>8}   {diff(now, before, 'clicks')}")
    print(f"  表示回数   : {now['impressions']:>8}   {diff(now, before, 'impressions')}")
    print(f"  CTR        : {now['ctr']*100:>7.2f}%   "
          f"（前期間 {before['ctr']*100:.2f}%）")
    print(f"  平均掲載順位: {now['position']:>7.1f}   "
          f"{diff(now, before, 'position', lower_is_better=True)}")

    days = query(service, prop, start, end, dimensions=["date"], row_limit=1000)
    print(f"\n--- 日ごとの推移（{args.days}日）---")
    for r in sorted(days, key=lambda x: x["keys"][0]):
        print(f"  {r['keys'][0]}  クリック {int(r.get('clicks',0)):>3}  "
              f"表示 {int(r.get('impressions',0)):>5}  "
              f"順位 {float(r.get('position',0)):>5.1f}")

    for dims, label in (
        (["query"], "検索クエリ"),
        (["page"], "ページ"),
        (["device"], "デバイス"),
        (["country"], "国"),
        (["searchAppearance"], "検索結果の見え方"),
    ):
        try:
            rows = query(service, prop, start, end, dimensions=dims, row_limit=500)
        except Exception as ex:                                # noqa: BLE001
            print(f"\n--- {label} --- 取得できませんでした: {ex}")
            continue
        rows.sort(key=lambda r: (-int(r.get("impressions", 0)),
                                 -int(r.get("clicks", 0))))
        n = len(rows)
        table(rows, f"{label}（全{n}件）",
              args.limit if dims[0] in ("query", "page") else 10)

    clicked = [r for r in query(service, prop, start, end,
                                dimensions=["query"], row_limit=500)
               if int(r.get("clicks", 0)) > 0]
    clicked.sort(key=lambda r: -int(r.get("clicks", 0)))
    table(clicked, "クリックが付いた検索クエリ", args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
