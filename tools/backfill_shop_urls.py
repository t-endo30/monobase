#!/usr/bin/env python3
"""既存記事に、抜けている楽天市場・Yahoo!ショッピングの商品URLを埋める。

記事を書いた経路によっては rakuten_url / yahoo_url が空のまま公開されている。
その記事では販売ボタンが出ないため、そのモールからの収益経路が無い。
この道具は商品検索APIで同じ商品を探し、URLだけを記事に書き戻す。

  $ export RAKUTEN_APP_ID=...            # 楽天のアプリケーションID
  $ export RAKUTEN_ACCESS_KEY=pk_...     # 楽天のアクセスキー
  $ export YAHOO_CLIENT_ID=...           # Yahoo!のクライアントID
  $ python3 tools/backfill_shop_urls.py              # 下見（書き込まない）
  $ python3 tools/backfill_shop_urls.py --apply      # 書き込む

別の商品を掴むのが一番まずいので、次の条件を満たしたものだけ採る。
  ・JANが記事にあるときは、JAN検索の結果を優先する（型番が一致するため）
  ・名前の一致度が --min-score 未満のものは採らない
  ・「ケース」「フィルム」など、付属品だけを売る商品名は落とす
下見では採った商品名を並べて出すので、目で見てから --apply する。
"""

import argparse
import difflib
import io
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pick_products import rakuten_search, yahoo_search, PAUSE   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 本体ではなく付属品を売っている商品名。これを掴むと読者が別物を買う。
ACCESSORY = re.compile(
    r"(ケース|カバー|フィルム|保護|スタンド|ホルダー|替え|交換用|互換|"
    r"用アダプタ|プロテクター|収納袋|ポーチ|スキンシール|中古|ジャンク)")

# 商品名から落とす飾り。モール側の商品名は装飾語が多い。
DECOR = re.compile(
    r"[【\[（(][^】\]）)]{0,30}[】\]）)]|"
    r"(送料無料|ポイント\d*倍|あす楽|正規品|国内正規|新品|即納|限定|"
    r"最大\d+%OFF|クーポン|訳あり|ラッピング|沖縄|離島)")


def product_name(article):
    """記事タイトルから商品名を取り出す。
       タイトルは「商品名 口コミ｜○○と△△」の形で作られている。"""
    t = str(article.get("title") or "")
    t = t.split("｜")[0].split("|")[0]
    t = re.sub(r"(の(口コミ|レビュー|選び方|比較)|口コミ|レビュー|"
               r"仕様分析|徹底比較|比較)\s*$", "", t).strip()
    return t


def norm(s):
    """一致度を測る前の下ごしらえ。記号と空白を落として小文字へ。"""
    s = DECOR.sub(" ", str(s or ""))
    s = re.sub(r"[\s　・/／,、。\-—–_'\"()（）\[\]【】]+", "", s)
    return s.lower()


def score(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def best_match(name, cands, min_score):
    """検索結果から、記事の商品といちばん近いものを選ぶ。
       付属品らしき商品名は先に落とす。返すのは (商品, 一致度)。"""
    best, best_s = None, 0.0
    for c in cands:
        cname = c.get("name") or ""
        if not c.get("url"):
            continue
        # 記事の商品名側に無い語で、付属品を示す語が入っていたら落とす
        if ACCESSORY.search(cname) and not ACCESSORY.search(name):
            continue
        s = score(name, cname)
        if s > best_s:
            best, best_s = c, s
    if best and best_s >= min_score:
        return best, best_s
    return None, best_s


def lookup(shop, name, jan, keys, min_score):
    """1商品ぶんの検索。JANがあればJANで、無ければ商品名で引く。
       JANで見つからなかったときは商品名で引き直す。"""
    tries = ([("jan", jan)] if jan else []) + [("keyword", name)]
    fallback_s = 0.0
    for how, q in tries:
        try:
            if shop == "rakuten":
                cands = rakuten_search(keys["rakuten_id"], keys["rakuten_key"],
                                       jan=q if how == "jan" else None,
                                       keyword=q if how == "keyword" else None,
                                       hits=20)
            else:
                cands = yahoo_search(keys["yahoo_id"],
                                     jan=q if how == "jan" else None,
                                     query=q if how == "keyword" else None,
                                     hits=20)
        except Exception as ex:                       # noqa: BLE001
            print(f"      検索できませんでした（{shop}/{how}）：{ex}")
            time.sleep(PAUSE)
            continue
        time.sleep(PAUSE)
        # JAN検索で1件でも返れば、それは型番一致なので一致度を緩める
        hit, s = best_match(name, cands,
                            0.0 if how == "jan" and cands else min_score)
        if hit:
            return hit, s, how
        fallback_s = max(fallback_s, s)
    return None, fallback_s, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="記事に書き戻す（付けないと下見だけ）")
    ap.add_argument("--shops", default="rakuten,yahoo",
                    help="対象のモール。既定は rakuten,yahoo")
    ap.add_argument("--min-score", type=float, default=0.62,
                    help="商品名の一致度の下限（0〜1）。既定 0.62")
    ap.add_argument("--limit", type=int, default=0,
                    help="処理する記事数の上限。0で全部")
    ap.add_argument("--slug", default="",
                    help="この slug の記事だけ処理する")
    ap.add_argument("--include-drafts", action="store_true",
                    help="下書き（published:false）も対象にする")
    ap.add_argument("--include-no-asin", action="store_true",
                    help="ASINの無い記事も対象にする（既定は飛ばす）")
    args = ap.parse_args()

    keys = {
        "rakuten_id": os.environ.get("RAKUTEN_APP_ID", "").strip(),
        "rakuten_key": os.environ.get("RAKUTEN_ACCESS_KEY", "").strip(),
        "yahoo_id": os.environ.get("YAHOO_CLIENT_ID", "").strip(),
    }
    shops = [s for s in args.shops.split(",") if s.strip()]
    if "rakuten" in shops and not keys["rakuten_id"]:
        print("RAKUTEN_APP_ID が未設定のため、楽天は飛ばします。")
        shops.remove("rakuten")
    if "yahoo" in shops and not keys["yahoo_id"]:
        print("YAHOO_CLIENT_ID が未設定のため、Yahoo!は飛ばします。")
        shops.remove("yahoo")
    if not shops:
        print("引ける先がありません。APIの鍵を設定してください。", file=sys.stderr)
        return 1

    path = os.path.join(ROOT, "content", "articles.json")
    arts = json.load(io.open(path, encoding="utf-8"))

    targets = [a for a in arts if a.get("published") or args.include_drafts]
    if args.slug:
        targets = [a for a in targets if a.get("slug") == args.slug]

    filled = {s: 0 for s in shops}
    missed = []
    done = 0
    for a in targets:
        need = [s for s in shops if not (a.get(f"{s}_url") or "").strip()]
        if not need:
            continue
        # ASINが無い記事は、特定の1商品を指していない（選び方・セール情報など）。
        # そこへ単品のURLを付けると、記事と違う物へ読者を送ることになる。
        if not (a.get("asin") or "").strip() and not args.include_no_asin:
            print(f"\n・{a.get('slug')}：ASINが無いため飛ばします"
                  f"（{a.get('kind') or '—'}）")
            continue
        if args.limit and done >= args.limit:
            break
        done += 1
        name = product_name(a)
        jan = str(a.get("jan") or "").strip()
        print(f"\n・{a.get('slug')}")
        print(f"   記事の商品：{name}" + (f"（JAN {jan}）" if jan else ""))
        for shop in need:
            hit, s, how = lookup(shop, name, jan, keys, args.min_score)
            label = "楽天" if shop == "rakuten" else "Yahoo!"
            if not hit:
                print(f"   {label}：見つかりません（最も近い一致度 {s:.2f}）")
                missed.append((a.get("slug"), label))
                continue
            print(f"   {label}：{hit['name'][:56]}")
            print(f"        一致度 {s:.2f}（{how}検索） / {hit['price']:,}円")
            print(f"        {hit['url']}")
            a[f"{shop}_url"] = hit["url"]
            filled[shop] += 1

    print("\n" + "-" * 56)
    for shop in shops:
        label = "楽天" if shop == "rakuten" else "Yahoo!"
        print(f"{label}：{filled[shop]} 本ぶんのURLが見つかりました")
    if missed:
        print(f"見つからなかった組み合わせ：{len(missed)} 件")

    if not args.apply:
        print("\n（下見のため書き込んでいません。"
              "内容を確かめて --apply を付けて実行してください）")
        return 0

    if not any(filled.values()):
        print("\n書き込むものがありません。")
        return 0

    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(arts, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\ncontent/articles.json に書き込みました。"
          f"python3 build.py でページに反映されます。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
