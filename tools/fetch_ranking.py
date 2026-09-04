#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GA4 のページビューを取得して content/ranking.json を書き出す。

  $ python3 tools/fetch_ranking.py            # 直近28日
  $ python3 tools/fetch_ranking.py --days 7

必要なもの（GitHub Actions では Secrets で渡す）
  GA4_PROPERTY_ID … GA4 のプロパティID（数字のみ。測定IDの G-XXXX とは別物）
  GOOGLE_APPLICATION_CREDENTIALS … サービスアカウントのJSONへのパス
                                    （Actions では GA4_SA_KEY から書き出す）

サイト側は content/ranking.json に値が入っていればそれを使い、
空なら閲覧者自身の端末の閲覧回数で並べる（assets/main.js）。
つまりこの処理が失敗しても、サイトの表示は壊れない。
"""
import argparse, io, json, os, re, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "content", "ranking.json")


def slugs():
    """公開記事の slug 一覧。GA4 から来たパスを照合するために使う。"""
    arts = json.load(io.open(os.path.join(ROOT, "content", "articles.json"),
                             encoding="utf-8"))
    return {a["slug"] for a in arts if a.get("published")}


def fetch(prop_id, days):
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        DateRange, Dimension, Metric, RunReportRequest)

    client = BetaAnalyticsDataClient()
    req = RunReportRequest(
        property=f"properties/{prop_id}",
        dimensions=[Dimension(name="pagePath")],
        metrics=[Metric(name="screenPageViews")],
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
        limit=500,
    )
    res = client.run_report(req)
    out = {}
    for row in res.rows:
        path = row.dimension_values[0].value or ""
        views = int(row.metric_values[0].value or 0)
        # 配信は拡張子なしのURL（hosting.clean_urls）。GA4 には
        #   /articles/desk-side-rack-review
        # の形で入るが、GitHub Pages へ戻すと .html が付く。
        # 末尾のスラッシュとクエリも来るので、どの形でも slug を取り出す。
        m = re.search(r"/articles/([^/?#]+)", path)
        if m:
            slug = m.group(1)
            if slug.endswith(".html"):
                slug = slug[:-len(".html")]
            if slug:
                out[slug] = out.get(slug, 0) + views
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=28, help="集計する日数（既定28日）")
    args = ap.parse_args()

    prop = os.environ.get("GA4_PROPERTY_ID", "").strip()
    if not prop:
        print("::warning::GA4_PROPERTY_ID が未設定のため、ランキングは更新しません。")
        return 0

    try:
        views = fetch(prop, args.days)
    except Exception as ex:                      # noqa: BLE001 - 失敗しても止めない
        print(f"::warning::GA4 からの取得に失敗しました（{ex}）。既存の値を残します。")
        return 0

    live = slugs()
    views = {k: v for k, v in views.items() if k in live}

    data = {
        "_note": "tools/fetch_ranking.py が GA4 から自動生成します。手で編集しても、"
                 "次回の実行で上書きされます。",
        "updated": date.today().isoformat(),
        "range_days": args.days,
        "views": dict(sorted(views.items(), key=lambda x: -x[1])),
    }
    json.dump(data, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ {len(views)} 記事のアクセス数を書き出しました（直近{args.days}日）")
    for slug, n in list(data["views"].items())[:5]:
        print(f"   {n:>6}  {slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
