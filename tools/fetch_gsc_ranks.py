#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Google Search Console から順位・表示回数・クリック数を取得する。

  $ python3 tools/fetch_gsc_ranks.py --append          # 監視中キーワードを測って記録
  $ python3 tools/fetch_gsc_ranks.py --days 7           # 改善レビュー用（直近7日）
  $ python3 tools/fetch_gsc_ranks.py --discover         # 未登録の有望クエリを一覧

content/seo/watchwords.json の keyword ごとに、Search Console の
searchAnalytics.query（query + page ディメンション）で平均順位・表示回数・
クリック数を取る。--append を付けると content/seo/rank-history.json の
entries に今回ぶんを追記する（追記専用。過去の記録は書き換えない）。

必要なもの（GitHub Actions では Secrets で渡す）
  GSC_SITE_URL                    … Search Console に登録したプロパティURL
                                     （未設定なら content/site.json の domain から組み立てる）
  GOOGLE_APPLICATION_CREDENTIALS  … サービスアカウントのJSONへのパス
                                     （Search Console でそのアカウントを
                                     「制限付き」ユーザーとして追加しておく）

GSCが使えない・失敗したときは exit 1 で止め、既存の記録には触らない
（tools/fetch_ranking.py と違い、順位はGA4のように黙って埋め合わせが
できないため）。GSCが使えない日はスキル側がWebSearchで代替する。
"""
import argparse, io, json, os, sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCHWORDS = os.path.join(ROOT, "content", "seo", "watchwords.json")
HISTORY = os.path.join(ROOT, "content", "seo", "rank-history.json")
SITE = os.path.join(ROOT, "content", "site.json")


def load_json(path, default):
    try:
        return json.load(io.open(path, encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return default


def site_url():
    env = os.environ.get("GSC_SITE_URL", "").strip()
    if env:
        return env
    domain = (load_json(SITE, {}).get("domain") or "").strip()
    return f"https://{domain}/" if domain else ""


def get_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if not key_path:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS が未設定です。")
    creds = service_account.Credentials.from_service_account_file(
        key_path, scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    return build("searchconsole", "v1", credentials=creds)


def query(service, prop, start, end, dimensions, row_limit=1000, dim_filter=None):
    body = {"startDate": start, "endDate": end, "dimensions": dimensions,
            "rowLimit": row_limit}
    if dim_filter:
        body["dimensionFilterGroups"] = [{"filters": [dim_filter]}]
    res = service.searchanalytics().query(siteUrl=prop, body=body).execute()
    return res.get("rows", [])


def date_range(days):
    # 直近2〜3日はGSCのデータがまだ確定していないため、昨日までを対象にする
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def fetch_keyword(service, prop, keyword, days):
    start, end = date_range(days)
    rows = query(service, prop, start, end, dimensions=["query", "page"],
                 dim_filter={"dimension": "query", "operator": "equals",
                             "expression": keyword})
    if not rows:
        return {"rank": None, "impressions": 0, "clicks": 0, "page": None}
    best = max(rows, key=lambda r: r.get("impressions", 0))
    return {
        "rank": round(best.get("position", 0), 1),
        "impressions": int(best.get("impressions", 0)),
        "clicks": int(best.get("clicks", 0)),
        "page": (best.get("keys") or [None, None])[1],
    }


def discover_candidates(service, prop, days, known, limit=20):
    start, end = date_range(days)
    rows = query(service, prop, start, end, dimensions=["query"], row_limit=1000)
    rows = [r for r in rows if (r.get("keys") or [""])[0] not in known]
    rows.sort(key=lambda r: -r.get("impressions", 0))
    return [
        {"query": r["keys"][0], "rank": round(r.get("position", 0), 1),
         "impressions": int(r.get("impressions", 0)),
         "clicks": int(r.get("clicks", 0))}
        for r in rows[:limit]
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=ROOT, help="（互換のため受け付けるが未使用。常にこのファイルの2階層上を使う）")
    ap.add_argument("--days", type=int, default=28,
                     help="集計期間（既定28日。改善レビューには7を指定する）")
    ap.add_argument("--append", action="store_true",
                     help="content/seo/rank-history.json に今回ぶんを追記する")
    ap.add_argument("--discover", action="store_true",
                     help="watchwords.json に無い、表示回数の多いクエリを一覧する")
    args = ap.parse_args()

    prop = site_url()
    if not prop:
        print("::error::サイトURLが分かりません。GSC_SITE_URL か content/site.json の domain を設定してください。")
        return 1

    watchwords = load_json(WATCHWORDS, {"keywords": []})
    watch = watchwords.get("keywords", [])

    try:
        service = get_service()
    except Exception as ex:  # noqa: BLE001
        print(f"::error::Search Console への接続に失敗しました（{ex}）。")
        return 1

    today = date.today().isoformat()
    results = []
    for w in watch:
        kw = (w.get("keyword") or "").strip()
        if not kw:
            continue
        try:
            r = fetch_keyword(service, prop, kw, args.days)
        except Exception as ex:  # noqa: BLE001
            print(f"::warning::「{kw}」の取得に失敗しました（{ex}）。")
            continue
        entry = {"date": today, "keyword": kw, "targetPath": w.get("targetPath", ""),
                  "days": args.days, **r}
        results.append(entry)
        rank_disp = f"{r['rank']:.1f}" if r["rank"] is not None else "圏外/未計測"
        print(f"  {rank_disp:>10}位  imp {r['impressions']:>5}  clicks {r['clicks']:>3}  {kw}")

    if args.discover:
        known = {(w.get("keyword") or "") for w in watch}
        candidates = discover_candidates(service, prop, args.days, known)
        print("\n未登録の有望クエリ（表示回数順・上位10件）:")
        for c in candidates[:10]:
            print(f"  {c['rank']:>6.1f}位  imp {c['impressions']:>5}  clicks {c['clicks']:>3}  {c['query']}")

    if args.append:
        history = load_json(HISTORY, {"entries": []})
        history.setdefault("entries", []).extend(results)
        json.dump(history, io.open(HISTORY, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"\n✅ {len(results)} 件を content/seo/rank-history.json に追記しました。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
