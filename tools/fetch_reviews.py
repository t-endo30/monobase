#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""口コミの件数と平均評価を、販売APIから取ってきて記事に持たせる。

これまで記事は「利用者の声では〜という傾向があります」としか書けず、
件数も平均も「確認できていない」として扱っていた。レビュー本文を
モールから機械で集めるのは各社の規約に触れるが、**件数と平均評価は
楽天・Yahoo!の公式APIが正規に返す**ので、そこだけを取り込む。

  $ export RAKUTEN_APP_ID=... RAKUTEN_ACCESS_KEY=pk_... YAHOO_CLIENT_ID=...
  $ python3 tools/fetch_reviews.py                # JANのある公開記事すべて
  $ python3 tools/fetch_reviews.py <slug> ...
  $ python3 tools/fetch_reviews.py --dry-run

取れた値は `review_stats` に入れる。`facts`（メーカー公式で裏を取った仕様）
とは別のキーにする。口コミの件数は「販売情報」であって「公式情報」ではなく、
混ぜると rating や spec の裏づけがあるかの判定まで狂うため。

記事生成時は、この値が「確認済みの販売情報」としてプロンプトに渡る。
"""
import argparse, io, json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from write_article import load, save_article
from pick_products import rakuten_search, yahoo_search


def stats_for(jan, rk_id, rk_key, yh_id):
    """JANで各モールを引き、件数と平均評価を集める。
       同じJANでも店舗ごとに別レビューなので、件数は合計、
       平均は件数で重みを付けた平均にする。"""
    out = {}
    if rk_id:
        try:
            items = [x for x in rakuten_search(rk_id, rk_key, jan=jan) if x["reviews"]]
        except Exception as ex:                       # noqa: BLE001
            print(f"    （楽天を引けませんでした: {ex}）")
            items = []
        if items:
            n = sum(x["reviews"] for x in items)
            avg = sum(x["reviews"] * x["rating"] for x in items) / n
            out["rakuten"] = {"count": n, "average": round(avg, 2),
                              "shops": len(items)}
    if yh_id:
        try:
            items = [x for x in yahoo_search(yh_id, jan=jan) if x["reviews"]]
        except Exception as ex:                       # noqa: BLE001
            print(f"    （Yahoo!を引けませんでした: {ex}）")
            items = []
        if items:
            n = sum(x["reviews"] for x in items)
            avg = sum(x["reviews"] * x["rating"] for x in items) / n
            out["yahoo"] = {"count": n, "average": round(avg, 2),
                            "shops": len(items)}
    return out


def describe(st):
    """プロンプトと記事で使える日本語にする。数字はここで文にしておく。"""
    lines = []
    for shop, ja in (("rakuten", "楽天市場"), ("yahoo", "Yahoo!ショッピング")):
        v = st.get(shop)
        if v:
            lines.append(f"{ja}：レビュー {v['count']:,}件、"
                         f"平均 {v['average']}／5.0（{v['shops']}店舗の合計）")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--dry-run", action="store_true", help="書き込まない")
    args = ap.parse_args()

    rk_id = os.environ.get("RAKUTEN_APP_ID")
    rk_key = os.environ.get("RAKUTEN_ACCESS_KEY")
    yh_id = os.environ.get("YAHOO_CLIENT_ID")
    if not (rk_id or yh_id):
        print("::error::RAKUTEN_APP_ID か YAHOO_CLIENT_ID を設定してください。")
        print("週次の GitHub Actions では Secrets から渡されます。")
        return 1

    arts = load("content/articles.json")
    if args.slugs:
        want = set(args.slugs)
        targets = [a for a in arts if a.get("slug") in want]
    else:
        targets = [a for a in arts if a.get("published")]

    # JANが無いと同一商品を照合できない。推測で引くと別商品の口コミを
    # 記事に載せることになるので、その場合は何もしない。
    todo = [a for a in targets if str(a.get("jan") or "").strip()]
    skipped = [a["slug"] for a in targets if a not in todo]

    print(f"{len(todo)} 本を調べます"
          f"（JANが無い {len(skipped)} 本は、商品を照合できないので飛ばします）\n")

    got = 0
    for i, a in enumerate(todo, 1):
        slug = a["slug"]
        print(f"[{i}/{len(todo)}] {slug} … ", end="", flush=True)
        st = stats_for(str(a["jan"]).strip(), rk_id, rk_key, yh_id)
        if not st:
            print("レビューのある商品ページが見つかりませんでした")
            continue
        st["checked"] = time.strftime("%Y-%m-%d")
        print("／".join(describe(st)))
        if not args.dry_run:
            a["review_stats"] = st
            save_article(a)
        got += 1

    if not args.dry_run and got:
        print("\ncontent/articles.json を更新しました。")
    print(f"\n取得できた記事 {got} 本 / 対象 {len(todo)} 本")
    if skipped:
        print("JANが無くて飛ばした記事：" + "、".join(skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
