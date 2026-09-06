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

別の商品の写真を出すのが一番まずいので、探し方ごとに採否の線を変える。

  ・記事に rakuten_url / yahoo_url があるモールだけを対象にする
  ・商品が一つに定まる引き方（JAN・楽天の商品コード）で引けたときは、
    その結果を採る
  ・商品名などのあいまいな引き方で引いたときは、記事に入っている
    商品ページURLと同じ商品だけを採る
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
# Amazonは入れない。PA-APIライセンス契約 13(n) が
#   「画像で構成される商品関連コンテンツを保存またはキャッシュしてはいけません」
#   「画像で構成される商品関連コンテンツへのリンクについては最長24時間保存することができます」
# としており、ビルドしたHTMLを何日も配信するこのサイトでは条件を満たせない。
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


def pick_image(hits, article, shop, exact):
    """検索結果から、この記事の商品に当たるものの写真を選ぶ。

       記事に入っているURLと同じ商品が最優先。
       それが無くても、商品が一つに定まる引き方（exact=True）で引いたなら、
       返ってきたものはその商品なので先頭を採る。
       あいまいな引き方のときは、URLが一致しない限り採らない。"""
    want = item_key(article.get(dict(SHOPS)[shop]) or "")
    withimg = [it for it in hits if it.get("image")]
    for it in withimg:
        if want and item_key(it.get("url")) == want:
            return it["image"], "URLが一致"
    if exact and withimg:
        return withimg[0]["image"], "商品コードで特定"
    return "", ""


def attempts(shop, article, keys):
    """引き方を、確かな順に並べて返す。(呼び出す関数, 一つに定まる引き方か)。

       上から順に試し、写真が採れたところで止める。"""
    jan = str(article.get("jan") or "").strip()
    out = []
    if shop == "rakuten" and keys.get("rk_id"):
        rk = lambda **kw: rakuten_search(keys["rk_id"], keys.get("rk_key"),
                                         hits=30, **kw)
        if jan:
            out.append((lambda: rk(jan=jan), True))
        code = item_key(article.get("rakuten_url") or "")
        if code:
            # 「店舗コード/商品コード」で直接引く。その商品だけが返る。
            out.append((lambda: rk(item_code=code), True))
            # 刷新後のAPIが itemCode を受けない場合の逃げ道。
            # あいまいなのでURLが一致したものしか採らない。
            out.append((lambda: rk(keyword=code.split("/")[-1]), False))
        name = str(article.get("product") or article.get("title") or "").strip()
        if name:
            out.append((lambda: rk(keyword=name), False))
    if shop == "yahoo" and keys.get("yh_id"):
        yh = lambda **kw: yahoo_search(keys["yh_id"], hits=30, **kw)
        if jan:
            out.append((lambda: yh(jan=jan), True))
        code = item_key(article.get("yahoo_url") or "")
        if code:
            out.append((lambda: yh(query=code.split("/")[-1]), False))
        name = str(article.get("product") or article.get("title") or "").strip()
        if name:
            out.append((lambda: yh(query=name), False))
    return out


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
            if not a.get(key) or got:
                continue
            url, why = "", ""
            for call, exact in attempts(shop, a, keys):
                try:
                    hits = call()
                except Exception as err:                  # noqa: BLE001
                    print(f"  ! {slug} / {shop}：{err}")
                    hits = []
                time.sleep(PAUSE)
                url, why = pick_image(hits, a, shop, exact)
                if url:
                    break
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
