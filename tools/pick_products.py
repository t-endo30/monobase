#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事にする商品の候補を、楽天市場とYahoo!ショッピングから集める。

「何を書くか」を決めるための下ごしらえをする道具です。
価格とレビュー件数はAPIで取れますが、「その商品が読者の困りごとに
答えるか」はAPIには分かりません。ここは候補を並べるところまでを担当し、
どれを書くかは人が選びます。

やること。

  1. カテゴリーごとに、レビュー件数の多い順で商品を集める
     （当サイトの記事はレビューの読み込みが土台なので、まず件数で絞る）
  2. すでに書いた商品を、JANコードとASINで突き合わせて落とす
  3. 同じJANの商品を3モール横断で照合し、モールごとの最安店舗を選ぶ
     （送料込みで比べる。送料別の見かけ上の最安に引っかからないため）
  4. 候補を content/candidates.json に書き出す

Amazon は PA-API の利用にアソシエイト承認と直近の売上が要るため、
承認されるまでは楽天とYahoo!だけで探します。承認後は
AMAZON_ACCESS_KEY 等を渡せば、同じJANでAmazon側も照合します。

  $ export RAKUTEN_APP_ID=...            # 楽天ウェブサービスのアプリID
  $ export YAHOO_CLIENT_ID=...           # Yahoo!デベロッパーのClient ID
  $ python3 tools/pick_products.py                 # 全カテゴリーから探す
  $ python3 tools/pick_products.py --category pc   # カテゴリーを絞る
  $ python3 tools/pick_products.py --limit 5       # 上位5件だけ
"""
import json, io, os, re, sys, time, argparse
import urllib.request
import urllib.error
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAKUTEN_API = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"
YAHOO_API = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"

TIMEOUT = 15
PAUSE = 1.0        # APIの呼び出し間隔。楽天は1秒1回までの制限がある

# 候補として扱う下限。ここを下回る商品は、記事の土台になるレビューが足りない。
MIN_REVIEWS = 30
MIN_RATING = 3.6
# 価格帯。極端に安い物はレビューが機能せず、高すぎる物は読者層と合わない。
MIN_PRICE = 1500
MAX_PRICE = 120000

# サイトのカテゴリーと、楽天のジャンルID／Yahoo!の検索語の対応。
# 楽天のジャンルIDは https://webservice.rakuten.co.jp/documentation/ で調べられる。
CATEGORY_MAP = {
    "pc":         {"rakuten_genre": 100026, "words": ["PC周辺機器"]},
    "appliance":  {"rakuten_genre": 562637, "words": ["生活家電"]},
    "furniture":  {"rakuten_genre": 100804, "words": ["インテリア 収納"]},
    "daily":      {"rakuten_genre": 215783, "words": ["日用品"]},
    "av":         {"rakuten_genre": 211742, "words": ["オーディオ"]},
    "camera":     {"rakuten_genre": 204040, "words": ["カメラ"]},
    "smartphone": {"rakuten_genre": 565004, "words": ["スマートフォン アクセサリ"]},
    "kitchen":    {"rakuten_genre": 100939, "words": ["キッチン家電"]},
    "health":     {"rakuten_genre": 100938, "words": ["健康計測"]},
    "beauty":     {"rakuten_genre": 100939, "words": ["美容家電"]},
    "pet":        {"rakuten_genre": 101213, "words": ["ペット用品"]},
}


def get_json(url, headers=None):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "monobase-pick-products/1.0")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.load(r)
    except urllib.error.HTTPError as ex:
        body = ex.read().decode("utf-8", "replace")[:300]
        # 楽天は理由を error_description で返す。そのまま見せないと直せない。
        try:
            j = json.loads(body)
            body = j.get("error_description") or j.get("error") or body
        except Exception:                                 # noqa: BLE001
            pass
        raise RuntimeError(f"HTTP {ex.code}: {body}") from ex


# ----------------------------------------------------------- 楽天市場

def rakuten_search(app_id, genre=None, keyword=None, jan=None, hits=30,
                   sort="-reviewCount"):
    """楽天商品検索API。JANを渡すときは keyword に入れる（専用の欄がない）。"""
    q = {
        "applicationId": app_id,
        "format": "json",
        "hits": hits,
        "sort": sort,
        "imageFlag": 1,          # 画像のある商品だけ
        "availability": 1,       # 在庫のある商品だけ
    }
    if genre:
        q["genreId"] = genre
    kw = jan or keyword
    if kw:
        q["keyword"] = kw
    data = get_json(RAKUTEN_API + "?" + urllib.parse.urlencode(q))
    out = []
    for w in data.get("Items", []):
        it = w.get("Item", w)
        # 送料込みで比べる。postageFlag は 0=送料込み 1=送料別。
        price = int(it.get("itemPrice") or 0)
        out.append({
            "shop": "rakuten",
            "name": it.get("itemName", ""),
            "url": it.get("itemUrl", ""),
            "price": price,
            "postage_included": int(it.get("postageFlag") or 0) == 0,
            "reviews": int(it.get("reviewCount") or 0),
            "rating": float(it.get("reviewAverage") or 0),
            "shop_name": it.get("shopName", ""),
            "image": ((it.get("mediumImageUrls") or [{}])[0] or {}).get("imageUrl", ""),
        })
    return out


# ------------------------------------------------------ Yahoo!ショッピング

def yahoo_search(client_id, query=None, jan=None, hits=30, sort="-review_count"):
    """Yahoo!ショッピング商品検索API v3。JANは jan_code で直接引ける。"""
    q = {"appid": client_id, "results": hits, "sort": sort, "in_stock": "true"}
    if jan:
        q["jan_code"] = jan
    elif query:
        q["query"] = query
    data = get_json(YAHOO_API + "?" + urllib.parse.urlencode(q))
    out = []
    for it in data.get("hits", []):
        rv = it.get("review") or {}
        ship = it.get("shipping") or {}
        out.append({
            "shop": "yahoo",
            "name": it.get("name", ""),
            "url": it.get("url", ""),
            "price": int(it.get("price") or 0),
            # 2 = 条件付き送料無料、1 = 送料無料
            "postage_included": str(ship.get("code", "")) in ("1", "2"),
            "reviews": int(rv.get("count") or 0),
            "rating": float(rv.get("rate") or 0),
            "shop_name": ((it.get("seller") or {}).get("name") or ""),
            "jan": (it.get("janCode") or "").strip(),
            "image": ((it.get("image") or {}).get("medium") or ""),
        })
    return out


# ------------------------------------------------------------- 選別

def is_official(entry):
    """メーカー公式ストアらしいか。出品終了が起きにくく、保証も付く。"""
    name = (entry.get("shop_name") or "") + " " + (entry.get("url") or "")
    return bool(re.search(r"公式|オフィシャル|official|direct|-shop|store\.", name, re.I))


def pick_cheapest(entries):
    """同じ商品の中から1つ選ぶ。公式ストアを優先し、次に送料込みの安さ。
       価格だけで選ばないのは、最安店舗は入れ替わりが激しく、
       数週間で出品が消えてリンク切れになりやすいため。"""
    ok = [e for e in entries if e.get("price")]
    if not ok:
        return None
    officials = [e for e in ok if is_official(e)]
    pool = officials or ok
    # 送料別は実質の支払額が読めないので後ろへ回す
    pool.sort(key=lambda e: (not e["postage_included"], e["price"]))
    return pool[0]


def clean_name(s):
    """検索用に商品名から飾りを落とす。【送料無料】【ポイント10倍】など。"""
    s = re.sub(r"[【\[（(][^】\]）)]{0,20}(送料無料|ポイント|クーポン|セール|限定|正規品)[^】\]）)]{0,20}[】\]）)]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def known_products(arts):
    """すでに記事にした商品。JANとASINで見分ける。"""
    jans, asins = set(), set()
    for a in arts:
        j = str(a.get("jan") or "").strip()
        if j:
            jans.add(j)
        s = (a.get("asin") or "").strip().upper()
        if s:
            asins.add(s)
    return jans, asins


def build_candidates(rakuten_id, yahoo_id, categories, limit, per_category):
    arts = json.load(io.open(os.path.join(ROOT, "content", "articles.json"),
                             encoding="utf-8"))
    seen_jan, _ = known_products(arts)
    seen_names = {clean_name(a.get("title", ""))[:20] for a in arts}

    out = []
    for cat in categories:
        conf = CATEGORY_MAP.get(cat)
        if not conf:
            print(f"::warning::カテゴリー {cat} の対応表がありません", file=sys.stderr)
            continue

        found = []
        if rakuten_id:
            try:
                found = rakuten_search(rakuten_id, genre=conf["rakuten_genre"],
                                       hits=per_category)
            except Exception as ex:                       # noqa: BLE001
                # ジャンルは改編される。弾かれたらキーワードで探し直す。
                if "genre" in str(ex).lower():
                    time.sleep(PAUSE)
                    try:
                        found = rakuten_search(rakuten_id,
                                               keyword=conf["words"][0],
                                               hits=per_category)
                    except Exception as ex2:              # noqa: BLE001
                        print(f"::warning::楽天の検索に失敗（{cat}）: {ex2}",
                              file=sys.stderr)
                else:
                    print(f"::warning::楽天の検索に失敗（{cat}）: {ex}",
                          file=sys.stderr)
            time.sleep(PAUSE)
        if not found and yahoo_id:
            try:
                found = yahoo_search(yahoo_id, query=conf["words"][0],
                                     hits=per_category)
            except Exception as ex:                       # noqa: BLE001
                print(f"::warning::Yahoo!の検索に失敗（{cat}）: {ex}", file=sys.stderr)
            time.sleep(PAUSE)

        for e in found:
            if e["reviews"] < MIN_REVIEWS or e["rating"] < MIN_RATING:
                continue
            if not (MIN_PRICE <= e["price"] <= MAX_PRICE):
                continue
            name = clean_name(e["name"])
            if name[:20] in seen_names:
                continue

            jan = (e.get("jan") or "").strip()
            shops = {e["shop"]: e}

            # JANが分かる場合だけ、もう一方のモールを照合する。
            # 商品名での照合は別商品を掴むので行わない。
            if jan:
                if jan in seen_jan:
                    continue
                if e["shop"] != "yahoo" and yahoo_id:
                    try:
                        alt = yahoo_search(yahoo_id, jan=jan, hits=20)
                        best = pick_cheapest(alt)
                        if best:
                            shops["yahoo"] = best
                    except Exception:                     # noqa: BLE001
                        pass
                    time.sleep(PAUSE)
                if e["shop"] != "rakuten" and rakuten_id:
                    try:
                        alt = rakuten_search(rakuten_id, jan=jan, hits=20,
                                             sort="+itemPrice")
                        best = pick_cheapest(alt)
                        if best:
                            shops["rakuten"] = best
                    except Exception:                     # noqa: BLE001
                        pass
                    time.sleep(PAUSE)
                seen_jan.add(jan)

            seen_names.add(name[:20])
            out.append({
                "name": name,
                "jan": jan,
                "category": cat,
                "reviews": max(v["reviews"] for v in shops.values()),
                "rating": max(v["rating"] for v in shops.values()),
                "price": min(v["price"] for v in shops.values()),
                "image": e.get("image", ""),
                "rakuten_url": (shops.get("rakuten") or {}).get("url", ""),
                "yahoo_url": (shops.get("yahoo") or {}).get("url", ""),
                "amazon_url": "",       # PA-API承認後にここを埋める
                "shops": {k: {"price": v["price"], "shop_name": v["shop_name"],
                              "postage_included": v["postage_included"]}
                          for k, v in shops.items()},
            })

    # レビュー件数の多い順。記事の土台になる材料が多い商品から並べる。
    out.sort(key=lambda c: (-c["reviews"], -c["rating"]))
    return out[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", action="append",
                    help="対象カテゴリー（省略すると全部）")
    ap.add_argument("--limit", type=int, default=20, help="出力する候補の数")
    ap.add_argument("--per-category", type=int, default=30,
                    help="カテゴリーごとに取得する件数")
    ap.add_argument("--out", default="content/candidates.json")
    args = ap.parse_args()

    rakuten_id = os.environ.get("RAKUTEN_APP_ID", "").strip()
    yahoo_id = os.environ.get("YAHOO_CLIENT_ID", "").strip()
    if not rakuten_id and not yahoo_id:
        print("RAKUTEN_APP_ID か YAHOO_CLIENT_ID のどちらかを設定してください。",
              file=sys.stderr)
        print("  楽天  https://webservice.rakuten.co.jp/", file=sys.stderr)
        print("  Yahoo! https://e.developer.yahoo.co.jp/register", file=sys.stderr)
        return 1

    cats = args.category or list(CATEGORY_MAP)
    print(f"カテゴリー {len(cats)} 件から候補を探します"
          f"（楽天={'あり' if rakuten_id else 'なし'} / "
          f"Yahoo!={'あり' if yahoo_id else 'なし'}）")

    cands = build_candidates(rakuten_id, yahoo_id, cats,
                             args.limit, args.per_category)

    path = os.path.join(ROOT, args.out)
    payload = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S+09:00",
                                   time.localtime(time.time())),
        "count": len(cands),
        "items": cands,
    }
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    print(f"\n候補 {len(cands)} 件を {args.out} に書き出しました。")
    for c in cands[:10]:
        shops = "/".join(k for k in ("amazon", "rakuten", "yahoo")
                         if c.get(k + "_url"))
        print(f"  ・{c['name'][:44]}")
        print(f"     {c['category']} / ￥{c['price']:,} / "
              f"レビュー{c['reviews']:,}件 ★{c['rating']:.1f} / {shops or '—'}")
    if len(cands) > 10:
        print(f"  … ほか {len(cands) - 10} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
