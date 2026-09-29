#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GA4 の週次レポートを作る（.github/workflows/ga-report.yml が毎週回す）。

  $ python3 tools/ga_report.py                # 直近7日と、その前の7日を比べる
  $ python3 tools/ga_report.py --days 28

出すもの
  content/ga_report.json … 数字そのもの。Claude Code が次のセッションで
                           読んで判断できるよう、リポジトリに残す
  --md のパス            … 人が読む要約（Issue と実行サマリーに貼る）

GA4 の画面はログインが要るので Claude からは開けない。「アナリティクスを
見てどう思う？」に答える材料を、ここで毎週そろえておく（2026-09-29）。

必要なもの（ranking.yml と同じ）
  GA4_PROPERTY_ID / GOOGLE_APPLICATION_CREDENTIALS
"""
import argparse, io, json, os, sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "content", "ga_report.json")
HOST = "monobase.site"

CHANNEL_JA = {
    "Organic Search": "検索（自然）", "Direct": "直接", "Referral": "他サイト",
    "Organic Social": "SNS", "Paid Search": "検索広告", "Unassigned": "不明",
    "Email": "メール", "Display": "ディスプレイ広告",
}


def client():
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    return BetaAnalyticsDataClient()


def run(cl, prop, dims, mets, ranges, host=True, order=None, limit=50,
        extra_filter=None):
    """1回ぶんの問い合わせ。行を dict のリストで返す。
       期間が2つあると、GA4 は dateRange という列を足して返す。"""
    from google.analytics.data_v1beta.types import (
        DateRange, Dimension, Filter, FilterExpression, FilterExpressionList,
        Metric, OrderBy, RunReportRequest)
    filters = []
    if host:
        filters.append(FilterExpression(filter=Filter(
            field_name="hostName",
            string_filter=Filter.StringFilter(value=HOST))))
    if extra_filter:
        name, value = extra_filter
        filters.append(FilterExpression(filter=Filter(
            field_name=name, string_filter=Filter.StringFilter(value=value))))
    fexp = None
    if len(filters) == 1:
        fexp = filters[0]
    elif filters:
        fexp = FilterExpression(and_group=FilterExpressionList(expressions=filters))
    req = RunReportRequest(
        property=f"properties/{prop}",
        dimensions=[Dimension(name=d) for d in dims],
        metrics=[Metric(name=m) for m in mets],
        date_ranges=[DateRange(start_date=a, end_date=b, name=n)
                     for n, a, b in ranges],
        dimension_filter=fexp,
        order_bys=([OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order),
                            desc=True)] if order else None),
        limit=limit)
    res = cl.run_report(req)
    names = [h.name for h in res.dimension_headers]
    rows = []
    for r in res.rows:
        row = {n: v.value for n, v in zip(names, r.dimension_values)}
        for m, v in zip(mets, r.metric_values):
            x = float(v.value or 0)
            row[m] = int(x) if x.is_integer() else round(x, 2)
        rows.append(row)
    return rows


def pct(cur, prev):
    if not prev:
        return "—"
    return f"{(cur - prev) / prev * 100:+.0f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--md", default="")
    args = ap.parse_args()

    prop = os.environ.get("GA4_PROPERTY_ID", "").strip()
    if not prop:
        print("::error::GA4_PROPERTY_ID が未設定です。")
        return 1

    end = date.today() - timedelta(days=1)          # 今日はまだ途中なので含めない
    start = end - timedelta(days=args.days - 1)
    pend = start - timedelta(days=1)
    pstart = pend - timedelta(days=args.days - 1)
    cur = ("cur", start.isoformat(), end.isoformat())
    prev = ("prev", pstart.isoformat(), pend.isoformat())
    cl = client()

    tot_m = ["activeUsers", "newUsers", "sessions", "engagedSessions",
             "screenPageViews", "userEngagementDuration"]
    tot = {r["dateRange"]: r for r in run(cl, prop, [], tot_m, [cur, prev])}
    daily = run(cl, prop, ["date"], ["activeUsers", "screenPageViews"], [cur],
                limit=100)
    daily.sort(key=lambda r: r["date"])
    channels = run(cl, prop, ["sessionDefaultChannelGroup"],
                   ["sessions", "activeUsers"], [cur], order="sessions")
    sources = run(cl, prop, ["sessionSourceMedium"], ["sessions"], [cur],
                  order="sessions", limit=15)
    pages = run(cl, prop, ["pagePath", "pageTitle"],
                ["screenPageViews", "activeUsers", "userEngagementDuration"],
                [cur], order="screenPageViews", limit=30)
    organic = run(cl, prop, ["landingPage"], ["sessions"], [cur],
                  order="sessions", limit=15,
                  extra_filter=("sessionDefaultChannelGroup", "Organic Search"))
    devices = run(cl, prop, ["deviceCategory"], ["activeUsers"], [cur],
                  order="activeUsers")
    # 本番以外のホスト名（ローカル確認など）がどれだけ混ざっているか
    hosts = run(cl, prop, ["hostName"], ["screenPageViews"], [cur],
                host=False, order="screenPageViews", limit=10)

    for p in pages:
        v = p["screenPageViews"] or 1
        p["avgEngagementSec"] = round(p["userEngagementDuration"] / v, 1)

    c = tot.get("cur", {}) or {}
    pv = tot.get("prev", {}) or {}
    ses = c.get("sessions") or 0
    org = sum(r["sessions"] for r in channels
              if r["sessionDefaultChannelGroup"] == "Organic Search")
    other_hosts = [h for h in hosts if h["hostName"] != HOST]

    # 気づいたこと。数字を並べるだけだと、毎週読まれなくなるので、
    # 判断につながる点だけ機械的に書き出す。
    notes = []
    zero = [r["date"] for r in daily if not r["screenPageViews"]]
    missing = args.days - len(daily)
    if zero or missing > 0:
        notes.append(f"閲覧0の日が {len(zero) + max(missing, 0)} 日ありました。")
    if ses:
        notes.append(f"検索（自然）からの訪問は {org} 回で、全体の "
                     f"{org / ses * 100:.0f}% です。")
    short = [p for p in pages if p["screenPageViews"] >= 3
             and p["avgEngagementSec"] < 10]
    if short:
        notes.append("3回以上読まれたのに平均10秒未満で離れているページ："
                     + "、".join(p["pagePath"] for p in short[:5]))
    if other_hosts:
        n = sum(h["screenPageViews"] for h in other_hosts)
        notes.append(f"本番以外のホスト名からの閲覧が {n} 回混ざっています"
                     f"（{', '.join(h['hostName'] for h in other_hosts)}）。"
                     "このレポートの数字には含めていません。")

    data = {
        "_note": "tools/ga_report.py が GA4 から自動生成します（毎週月曜）。",
        "generated": date.today().isoformat(),
        "range": {"cur": [cur[1], cur[2]], "prev": [prev[1], prev[2]]},
        "totals": {"cur": c, "prev": pv},
        "daily": daily, "channels": channels, "sources": sources,
        "pages": pages, "organic_landing": organic, "devices": devices,
        "hosts": hosts, "notes": notes,
    }
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")

    def secs(r):
        u = r.get("activeUsers") or 0
        return f'{(r.get("userEngagementDuration") or 0) / u:.0f}秒' if u else "—"

    L = [f"## GA4 週次レポート（{cur[1]} 〜 {cur[2]}）", ""]
    L += ["| | 今週 | 前週 | 増減 |", "|---|---:|---:|---:|"]
    for k, lab in [("activeUsers", "ユーザー"), ("newUsers", "新規ユーザー"),
                   ("sessions", "訪問"), ("screenPageViews", "閲覧ページ数")]:
        a, b = c.get(k, 0), pv.get(k, 0)
        L.append(f"| {lab} | {a} | {b} | {pct(a, b)} |")
    L.append(f"| 1人あたりの滞在 | {secs(c)} | {secs(pv)} | |")
    L += ["", "### 気づいたこと", ""]
    L += [f"- {n}" for n in notes] or ["- 特になし"]
    L += ["", "### 流入元", "", "| 経路 | 訪問 | ユーザー |", "|---|---:|---:|"]
    for r in channels:
        g = r["sessionDefaultChannelGroup"]
        L.append(f'| {CHANNEL_JA.get(g, g)} | {r["sessions"]} | {r["activeUsers"]} |')
    L += ["", "### 参照元（上位）", "", "| 参照元 / メディア | 訪問 |", "|---|---:|"]
    L += [f'| {r["sessionSourceMedium"]} | {r["sessions"]} |' for r in sources]
    L += ["", "### よく読まれたページ", "",
          "| ページ | 閲覧 | ユーザー | 平均滞在 |", "|---|---:|---:|---:|"]
    for p in pages[:15]:
        L.append(f'| {p["pagePath"]} | {p["screenPageViews"]} | '
                 f'{p["activeUsers"]} | {p["avgEngagementSec"]}秒 |')
    if organic:
        L += ["", "### 検索から入ってきたページ", "", "| ページ | 訪問 |", "|---|---:|"]
        L += [f'| {r["landingPage"]} | {r["sessions"]} |' for r in organic]
    L += ["", "### 日ごと", "", "| 日付 | ユーザー | 閲覧 |", "|---|---:|---:|"]
    for r in daily:
        d = r["date"]
        L.append(f'| {d[4:6]}/{d[6:]} | {r["activeUsers"]} | {r["screenPageViews"]} |')
    L += ["", "### 端末", ""]
    L.append("、".join(f'{r["deviceCategory"]} {r["activeUsers"]}' for r in devices) or "—")
    md = "\n".join(L) + "\n"
    if args.md:
        with io.open(args.md, "w", encoding="utf-8") as f:
            f.write(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
