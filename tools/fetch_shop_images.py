#!/usr/bin/env python3
"""既存記事に、本文の商品カードへ出す「実物の商品写真」のURLを埋める。

アイキャッチ（記事の顔・一覧のカード・SNSの絵）はこれまでどおり自前の画像を使う。
ここで入れるのは、記事の中ほどに出る商品カードの写真だけ。

  $ export RAKUTEN_APP_ID=...            # 楽天のアプリケーションID
  $ export RAKUTEN_ACCESS_KEY=pk_...     # 楽天のアクセスキー
  $ export YAHOO_CLIENT_ID=...           # Yahoo!のクライアントID（任意）
  $ python3 tools/fetch_shop_images.py            # 下見（書き込まない）
  $ python3 tools/fetch_shop_images.py --apply    # 書き込む

**画像は当サイトへ保存しない。** 各モールの規約では、APIで取得した画像を
自分のサーバへ保存して配り直すことはできない。参照してよいのは、返ってきた
URLをそのまま表示する形（ホットリンク）だけ。そのため記事にはURLだけを持たせ、
build.py が <img src> にそのまま入れる。

**写真はその写真を出したモールへリンクする。** 規約が求めるのは
「取得元へのリンクとともに表示すること」なので、写真だけ楽天・リンク先はAmazon
という組み合わせは作らない。そのショップのURLが記事に無ければ、写真も入れない。

別の商品の写真を出すのが一番まずいので、次の条件を満たしたものだけ採る。
  ・記事に rakuten_url / yahoo_url があるモールだけを対象にする
  ・JANが記事にあるときは、JAN検索の結果だけを使う（型番が一致するため）
  ・JANが無いときは、記事に入っている商品ページURLと同じ商品だけを採る
  ・どちらでも決まらない記事は飛ばす（商品名の一致だけでは採らない）
"""

import argparse
import io
import json
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pick_products import rakuten_search, yahoo_search   # noqa: E402

# 楽天は毎秒1回まで。短くすると429で弾かれるので、少し余裕を持たせる。
PAUSE = 1.5

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 記事が持つショップURLの項目名と、写真を入れる鍵。
SHOPS = [("rakuten", "rakuten_url"), ("yahoo", "yahoo_url")]


def item_key(url):
    """商品ページURLから、店舗と商品コードの部分だけを取り出して比べる鍵にする。
       クエリやアフィリエイトの飾りが付いても同じ商品だと分かるようにする。

       楽天  https://item.rakuten.co.jp/<店舗>/<商品コード>/
       Yahoo https://store.shopping.yahoo.co.jp/<店舗>/<商品コード>.html
    """
    u = urllib.parse.urlsplit(str(url or ""))
    path = re.sub(r"\.html?$", "", u.path.strip("/"))
    parts = [x for x in path.split("/") if x]
    return "/".join(parts[:2]).lower() if len(parts) >= 2 else ""


def pick_image(hits, article, shop):
    """検索結果から、この記事の商品に当たるものの写真を選ぶ。
       記事に入っているURLと同じ商品を最優先。無ければ諦める。"""
    want = item_key(article.get(dict(SHOPS)[shop]) or "")
    for it in hits:
        if not it.get("image"):
            continue
        if want and item_key(it.get("url")) == want:
            return it["image"], "URLが一致"
    return "", ""


def search(shop, article, keys):
    """JANがあればJANで、無ければ記事のURLの商品コードを手掛かりに探す。"""
    jan = str(article.get("jan") or "").strip()
    if shop == "rakuten":
        if not keys.get("rk_id"):
            return []
        # JANが無いときは、商品ページURLをそのまま検索語にすると
        # 同じ商品が返ってくることが多い（楽天は商品コードで引ける）。
        kw = None if jan else (article.get("rakuten_url") or "")
        return rakuten_search(keys["rk_id"], keys.get("rk_key"),
                              keyword=kw, jan=jan or None, hits=30)
    if shop == "yahoo":
        if not keys.get("yh_id"):
            return []
        kw = None if jan else (article.get("yahoo_url") or "")
        return yahoo_search(keys["yh_id"], query=kw, jan=jan or None, hits=30)
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="記事に書き込む（付けないと下見だけ）")
    ap.add_argument("--slug", help="この記事だけを対象にする")
    ap.add_argument("--force", action="store_true",
                    help="すでに写真が入っている記事も調べ直す")
    ap.add_argument("--limit", type=int, default=0,
                    help="調べる記事数の上限（0で全部）")
    args = ap.parse_args()

    keys = {
        "rk_id": os.environ.get("RAKUTEN_APP_ID", "").strip(),
        "rk_key": os.environ.get("RAKUTEN_ACCESS_KEY", "").strip(),
        "yh_id": os.environ.get("YAHOO_CLIENT_ID", "").strip(),
    }
    if not keys["rk_id"] and not keys["yh_id"]:
        print("RAKUTEN_APP_ID か YAHOO_CLIENT_ID を環境変数に入れてください。")
        return 1

    path = os.path.join(ROOT, "content", "articles.json")
    with io.open(path, encoding="utf-8") as f:
        arts = json.load(f)

    targets = []
    for a in arts:
        if args.slug and a.get("slug") != args.slug:
            continue
        if a.get("shop_images") and not args.force:
            continue
        # 写真を出せるのは、そのモールのボタンが出ている記事だけ
        if not any(a.get(key) for _shop, key in SHOPS):
            continue
        targets.append(a)
    if args.limit:
        targets = targets[:args.limit]

    if not targets:
        print("対象の記事がありません。")
        return 0

    print(f"{len(targets)} 本を調べます。\n")
    found, missed = 0, []
    for a in targets:
        slug = a.get("slug", "")
        got = False
        for shop, key in SHOPS:
            if not a.get(key):
                continue
            try:
                hits = search(shop, a, keys)
            except Exception as err:                      # noqa: BLE001
                print(f"  ! {slug} / {shop}：{err}")
                hits = []
            time.sleep(PAUSE)
            url, why = pick_image(hits, a, shop)
            if not url:
                continue
            label = "楽天" if shop == "rakuten" else "Yahoo!"
            print(f"  ○ {slug}（{label}・{why}）\n     {url}")
            # 1記事につき1枚だけ持つ。出るのは1枚なので、
            # 別のモールの写真が残っていると迷う。
            a["shop_images"] = {shop: url}
            found += 1
            got = True
            break
        if not got:
            missed.append(slug)

    print("\n" + "-" * 56)
    print(f"見つかった：{found} 本")
    if missed:
        print(f"見つからなかった：{len(missed)} 本")
        for slug in missed:
            print(f"   ・{slug}")

    if not args.apply:
        print("\n（下見のため書き込んでいません。"
              "内容を確かめて --apply を付けて実行してください）")
        return 0
    if not found:
        print("\n書き込むものがありません。")
        return 0

    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(arts, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("\ncontent/articles.json に書き込みました。"
          "python3 build.py でページに反映されます。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
