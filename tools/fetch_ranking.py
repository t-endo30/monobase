#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GA4 のページビューを取得して content/ranking.json を書き出す。

  $ python3 tools/fetch_ranking.py            # 前回の続きから昨日まで足す
  $ python3 tools/fetch_ranking.py --days 7   # 「よく読まれている」の集計期間

閲覧数は積み上げる。GA4 に毎回「直近28日」を聞くと、29日前の閲覧が
落ちるぶん数字が減っていき、記事タイルに出す VIEW が日ごとに小さく
なってしまう。そこで
  views        … 開設からの累計（前回の続きから昨日ぶんを足していく）
  views_recent … 直近28日（「よく読まれている記事」の並び順に使う）
の2つを持つ。累計はこのファイル自身が記録で、GA4 のデータ保持期間を
過ぎても減らない。

必要なもの（GitHub Actions では Secrets で渡す）
  GA4_PROPERTY_ID … GA4 のプロパティID（数字のみ。測定IDの G-XXXX とは別物）
  GOOGLE_APPLICATION_CREDENTIALS … サービスアカウントのJSONへのパス
                                    （Actions では GA4_SA_KEY から書き出す）

サイト側は content/ranking.json に値が入っていればそれを使い、
空なら閲覧者自身の端末の閲覧回数で並べる（assets/main.js）。
つまりこの処理が失敗しても、サイトの表示は壊れない。
"""
import argparse, io, json, os, re, sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "content", "ranking.json")


def slugs():
    """公開記事の slug 一覧。GA4 から来たパスを照合するために使う。"""
    arts = json.load(io.open(os.path.join(ROOT, "content", "articles.json"),
                             encoding="utf-8"))
    return {a["slug"] for a in arts if a.get("published")}


def load_prev():
    """前回の書き出しを読む。壊れていても止めない。"""
    try:
        return json.load(io.open(OUT, encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def fetch(prop_id, start, end):
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        DateRange, Dimension, Metric, RunReportRequest)

    client = BetaAnalyticsDataClient()
    req = RunReportRequest(
        property=f"properties/{prop_id}",
        dimensions=[Dimension(name="pagePath")],
        metrics=[Metric(name="screenPageViews")],
        date_ranges=[DateRange(start_date=start, end_date=end)],
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
    ap.add_argument("--days", type=int, default=28,
                    help="「よく読まれている記事」の集計期間（既定28日）")
    ap.add_argument("--since", default="",
                    help="累計の起点（YYYY-MM-DD）。初回だけ使う")
    args = ap.parse_args()

    prop = os.environ.get("GA4_PROPERTY_ID", "").strip()
    if not prop:
        print("::warning::GA4_PROPERTY_ID が未設定のため、ランキングは更新しません。")
        return 0

    prev = load_prev()
    totals = dict(prev.get("views") or {})
    through = (prev.get("counted_through") or "").strip()

    today = date.today()
    yesterday = today - timedelta(days=1)

    # 足しはじめる日を決める。
    #   ・前回どこまで数えたかが分かっていれば、その翌日から
    #   ・分からなければ --since、それも無ければ「直近28日」を起点にする
    #     （以前の書き出しは直近28日の値だったので、それを初期の累計とみなす）
    if through:
        start = date.fromisoformat(through) + timedelta(days=1)
    elif args.since:
        start = date.fromisoformat(args.since)
        totals = {}
    else:
        start = today - timedelta(days=args.days - 1)
        if prev.get("updated"):
            # 前回の数字が覆っている期間は数え直さない
            start = date.fromisoformat(prev["updated"]) + timedelta(days=1)

    added = {}
    if start <= yesterday:
        try:
            added = fetch(prop, start.isoformat(), yesterday.isoformat())
        except Exception as ex:                  # noqa: BLE001 - 失敗しても止めない
            print(f"::warning::GA4 からの取得に失敗しました（{ex}）。既存の値を残します。")
            return 0
        for slug, n in added.items():
            totals[slug] = totals.get(slug, 0) + n
        through = yesterday.isoformat()
    else:
        # 足すぶんが無くても、どこまで数えたかは必ず記録する。
        # これを書かないと、次回もまた同じ起点を計算し直すことになり、
        # いつまでも累計が増えない。
        through = through or (start - timedelta(days=1)).isoformat()
        print("今日はまだ足すぶんがありません（昨日までは取り込み済み）。")

    # 並び順に使う直近ぶん。こちらは毎回取り直す
    try:
        recent = fetch(prop, f"{args.days}daysAgo", "today")
    except Exception as ex:                      # noqa: BLE001
        print(f"::warning::直近{args.days}日の取得に失敗しました（{ex}）。")
        recent = dict(prev.get("views_recent") or {})

    live = slugs()
    recent = {k: v for k, v in recent.items() if k in live}
    # 累計は下書きに戻した記事のぶんも消さずに持っておく。公開し直した
    # ときに 0 から数え直しにならないようにするため。
    data = {
        "_note": "tools/fetch_ranking.py が GA4 から自動生成します。手で編集しても、"
                 "次回の実行で上書きされます。views は開設からの累計、"
                 "views_recent は直近の集計期間ぶん。",
        "updated": today.isoformat(),
        "counted_through": through or "",
        "range_days": args.days,
        "views": dict(sorted(totals.items(), key=lambda x: -x[1])),
        "views_recent": dict(sorted(recent.items(), key=lambda x: -x[1])),
    }
    json.dump(data, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ 累計 {len(totals)} 記事 / 直近{args.days}日 {len(recent)} 記事を書き出しました"
          f"（{len(added)} 記事ぶんを加算、{through} まで）")
    for slug, n in list(data["views"].items())[:5]:
        print(f"   {n:>6}  {slug}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
