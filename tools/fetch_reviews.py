#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""価格・口コミの件数・平均評価を、販売APIから取ってきて記事に持たせる。

これまで記事は「利用者の声では〜という傾向があります」としか書けず、
件数も平均も「確認できていない」として扱っていた。レビュー本文を
モールから機械で集めるのは各社の規約に触れるが、**件数と平均評価は
楽天・Yahoo!の公式APIが正規に返す**ので、そこだけを取り込む。

  $ export RAKUTEN_APP_ID=... RAKUTEN_ACCESS_KEY=pk_... YAHOO_CLIENT_ID=...
  $ python3 tools/fetch_reviews.py                # 照合できる公開記事すべて
  $ python3 tools/fetch_reviews.py <slug> ...
  $ python3 tools/fetch_reviews.py --dry-run

取れた値は `review_stats` に入れる。`facts`（メーカー公式で裏を取った仕様）
とは別のキーにする。口コミの件数は「販売情報」であって「公式情報」ではなく、
混ぜると rating や spec の裏づけがあるかの判定まで狂うため。

記事生成時は、この値が「確認済みの販売情報」としてプロンプトに渡る。
"""
import argparse, io, json, os, sys, time, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from write_article import load, save_article
from pick_products import rakuten_search, yahoo_search, PAUSE


def rakuten_item_code(url):
    """楽天の商品URLから itemCode を取り出す。

       JANを持たない記事でも、記事が抱えている商品URLそのものから
       「その商品だけ」を引き直せる。名前で検索し直すのとは違って
       別商品を掴む心配が無いので、JANと同じ確かさで使える。

         https://item.rakuten.co.jp/<店舗>/<商品コード>/ → <店舗>:<商品コード>

       **区切りはコロン**。URLと同じスラッシュで渡すと、楽天は
       `HTTP 400: itemCode is not valid` を返す（2026-09-27、177本中
       167本がこれで取れずに気づいた）。大文字小文字も変えない——
       商品コードはそのままの表記で登録されている。"""
    u = urllib.parse.urlsplit(str(url or ""))
    if "item.rakuten.co.jp" not in u.netloc:
        return ""
    parts = [x for x in u.path.strip("/").split("/") if x]
    return ":".join(parts[:2]) if len(parts) >= 2 else ""


def summarize(items):
    """同じ商品を売っている店舗の一覧から、価格と口コミをまとめる。

       口コミは店舗ごとに別に付くので件数は合計、平均は件数で重みを
       付けた平均にする。価格は最安値（読者が実際に払う額に一番近い）。
       口コミが1件も無くても価格だけは出す（数字が1つも無いページを
       減らすのが目的なので、片方だけでも載せる価値がある）。"""
    out = {}
    priced = [x for x in items if x.get("price")]
    if priced:
        best = min(priced, key=lambda x: x["price"])
        out["price"] = int(best["price"])
        out["postage_included"] = bool(best.get("postage_included"))
    rated = [x for x in items if x.get("reviews")]
    if rated:
        n = sum(x["reviews"] for x in rated)
        out["count"] = n
        out["average"] = round(sum(x["reviews"] * x["rating"] for x in rated) / n, 2)
        out["shops"] = len(rated)
    return out


def stats_for(jan, rk_id, rk_key, yh_id, rakuten_item=""):
    """各モールを引き、価格・口コミ件数・平均評価を集める。

       楽天は JAN が無くても itemCode で引けるので、記事が持っている
       楽天の商品URLを手がかりにする。Yahoo!の商品検索APIには
       商品コードで1件だけ引く口が無いため、JANがあるときだけ引く。"""
    out = {}
    if rk_id and (jan or rakuten_item):
        try:
            if jan:
                items = rakuten_search(rk_id, rk_key, jan=jan)
            else:
                items = rakuten_search(rk_id, rk_key, item_code=rakuten_item)
        except Exception as ex:                       # noqa: BLE001
            print(f"    （楽天を引けませんでした: {ex}）")
            items = []
        got = summarize(items)
        if got:
            out["rakuten"] = got
    if yh_id and jan:
        try:
            items = yahoo_search(yh_id, jan=jan)
        except Exception as ex:                       # noqa: BLE001
            print(f"    （Yahoo!を引けませんでした: {ex}）")
            items = []
        got = summarize(items)
        if got:
            out["yahoo"] = got
    return out


def describe(st):
    """プロンプトと記事で使える日本語にする。数字はここで文にしておく。"""
    lines = []
    for shop, ja in (("rakuten", "楽天市場"), ("yahoo", "Yahoo!ショッピング")):
        v = st.get(shop)
        if not v:
            continue
        bits = []
        if v.get("price"):
            ship = "送料込" if v.get("postage_included") else "送料別"
            bits.append(f"{v['price']:,}円（{ship}）")
        if v.get("count"):
            bits.append(f"レビュー {v['count']:,}件、"
                        f"平均 {v['average']}／5.0（{v['shops']}店舗の合計）")
        if bits:
            lines.append(f"{ja}：" + "、".join(bits))
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

    # 同一商品を照合できる手がかりが要る。推測で引くと別商品の価格・
    # 口コミを記事に載せることになるので、その場合は何もしない。
    # 手がかりは2つ：JAN と、記事が持っている楽天の商品URL（itemCode）。
    # JANを持つ記事は144本中10本しかなく、JANだけを見ていたころは
    # 残り134本が永久に数字の無いページのままだった。
    todo = [a for a in targets
            if str(a.get("jan") or "").strip()
            or rakuten_item_code(a.get("rakuten_url"))]
    skipped = [a["slug"] for a in targets if a not in todo]

    print(f"{len(todo)} 本を調べます"
          f"（JANも楽天の商品URLも無い {len(skipped)} 本は、"
          "商品を照合できないので飛ばします）\n")

    got = 0
    for i, a in enumerate(todo, 1):
        slug = a["slug"]
        # 楽天は1秒1回までしか受け付けない。JANのある10本を回すだけの
        # ころは気にせずに済んだが、楽天の商品URLからも引くようになって
        # 対象が100本を超えたので、1件ごとに間を空ける。
        if i > 1:
            time.sleep(PAUSE)
        print(f"[{i}/{len(todo)}] {slug} … ", end="", flush=True)
        st = stats_for(str(a.get("jan") or "").strip(), rk_id, rk_key, yh_id,
                       rakuten_item=rakuten_item_code(a.get("rakuten_url")))
        if not st:
            print("価格・レビューの取れる商品ページが見つかりませんでした")
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
        print("照合する手がかりが無くて飛ばした記事：" + "、".join(skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
