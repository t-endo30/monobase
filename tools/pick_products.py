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

  $ export RAKUTEN_APP_ID=...            # 楽天のアプリケーションID（UUID）
  $ export RAKUTEN_ACCESS_KEY=pk_...     # 楽天のアクセスキー
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

# 楽天は2026年2月にAPIを刷新した。旧 app.rakuten.co.jp は停止済みで、
# 認証は applicationId と accessKey の2点が要る。
RAKUTEN_API = ("https://openapi.rakuten.co.jp/ichibams/api/IchibaItem"
               "/Search/20260701")
# 楽天ウェブサービスに登録したアプリのURL。
# 2026年2月の刷新でブラウザからの呼び出しを前提とする作りになり、
# Origin と Referer の両方を見るようになった。どちらかが欠けると
# REQUEST_CONTEXT_BODY_HTTP_REFERRER_MISSING で弾かれる。
# ここに入れるURLは、アプリの「許可サイト」に登録しておくこと
# （登録が無いと HTTP_REFERRER_NOT_ALLOWED になる）。
RAKUTEN_ORIGIN = (os.environ.get("RAKUTEN_ORIGIN", "").strip()
                  or "https://monobase.site")

YAHOO_API = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"

TIMEOUT = 15
PAUSE = 1.0        # APIの呼び出し間隔。楽天は1秒1回までの制限がある

# カテゴリーの見分け語。楽天のジャンルIDだけに頼ると、別分野の商品が紛れ込む。
# 実際に kitchen と beauty が同じIDを指しており、フェイスマスクが
# キッチンの候補として上がってきた。商品名にこの語のどれかが
# 入っていることを確かめる。入っていない商品は候補にしない。
CATEGORY_WORDS = {
    "pc": ["マウス", "キーボード", "モニター", "ディスプレイ", "ハブ", "ドック",
           "SSD", "HDD", "ルーター", "webカメラ", "ウェブカメラ", "PC", "パソコン",
           "USB", "モニターアーム", "ノートPC", "タブレット"],
    "appliance": ["扇風機", "サーキュレーター", "空気清浄", "加湿", "除湿", "掃除機",
                  "照明", "シーリング", "ライト", "エアコン", "ヒーター", "ストーブ",
                  "洗濯", "冷蔵庫", "衣類スチーマー", "スチームアイロン",
                  "電池", "充電器", "スマートリモコン",
                  "投光器", "センサーライト"],
    "furniture": ["デスク", "チェア", "椅子", "テーブル", "棚", "ラック", "収納",
                  "ベッド", "マットレス", "枕", "ソファ", "スツール", "ベンチ"],
    "daily": ["ゴミ箱", "収納", "掃除", "洗剤", "タオル", "傘", "防災", "工具",
              "アウトドア", "レジャー", "シャワー", "水筒", "スタンド"],
    "av": ["イヤホン", "ヘッドホン", "スピーカー", "マイク", "アンプ", "オーディオ",
           "サウンドバー", "スピーカーフォン", "レコーダー"],
    "camera": ["カメラ", "レンズ", "三脚", "ジンバル", "ドローン", "SDカード",
               "ストロボ", "撮影"],
    "smartphone": ["スマホ", "iPhone", "Android", "ケース", "充電", "モバイルバッテリー",
                   "ケーブル", "スマートウォッチ", "フィルム", "MagSafe"],
    "kitchen": ["炊飯", "electric ケトル", "電気ケトル", "ケトル", "レンジ", "オーブン",
                "トースター", "ミキサー", "ブレンダー", "コーヒー", "圧力鍋", "鍋",
                "フライパン", "食洗", "ホットプレート", "包丁", "まな板", "保温"],
    "health": ["体重計", "体組成", "血圧", "体温", "歩数", "マッサージ", "サポーター",
               "フォームローラー", "healthcare", "ヘルスメーター"],
    "beauty": ["シェーバー", "髭剃り", "ひげ", "ドライヤー", "ヘアアイロン", "美顔",
               "脱毛", "化粧", "コスメ", "スキンケア", "美容液", "セラム", "日焼け",
               "マスカラ", "アイブロウ", "洗顔", "シャンプー", "パック", "フェイス"],
    "pet": ["犬", "猫", "ペット", "給餌", "給水", "トイレ", "ケージ", "爪切り"],
    "fashion": ["靴下", "ソックス", "シャツ", "パンツ", "ジャケット", "コート",
                "スニーカー", "ベルト", "財布", "バッグ", "リュック", "帽子",
                "インナー", "肌着"],
}

# 商品名が広告文になっている商品。楽天には、商品名の欄に売り文句を
# 詰め込んでいる出品者がいる。こういう商品は名前から型番も種類も
# 読み取れず、記事の題名にもURLにもできない。
#   例）発酵→これが、発酵酵素ダイエットの火付け役!→レビュー＼10万／超が証明→…
AD_COPY = re.compile(r"[→⇒]|[＼\\][0-9０-９]|超が証明|話題沸騰|第[0-9０-９]+位|"
                     r"ランキング[0-9０-９]+|[!！]{2,}|[0-9０-９]+冠")


# そのカテゴリーには入れない語。ジャンルIDの取り違えや、語の多義
# （衣類アイロン と ヘアアイロン）で、別分野の商品が混ざるのを止める。
CATEGORY_EXCLUDE = {
    "appliance": ["ヘアアイロン", "ストレートアイロン", "カールアイロン", "コテ",
                  "2wayアイロン", "ドライヤー", "美容液", "クレンジング",
                  "クレンズ", "シャンプー", "トリートメント", "フェイスパック"],
    "kitchen":   ["美容液", "クレンジング", "クレンズ", "シャンプー", "化粧水",
                  "マスカラ", "アイブロウ", "パック", "美顔", "ヘアアイロン"],
    "daily":     ["ヘアアイロン", "美容液", "クレンジング", "シャンプー"],
}


def fits_category(name, cat):
    """商品名が、そのカテゴリーの品物を指しているか。"""
    low = str(name or "").lower()
    if any(x.lower() in low for x in CATEGORY_EXCLUDE.get(cat, [])):
        return False
    words = CATEGORY_WORDS.get(cat)
    if not words:
        return True
    return any(w.lower() in low for w in words)


def looks_like_ad(name):
    """商品名ではなく売り文句になっているか。"""
    return bool(AD_COPY.search(str(name or "")))


# Bluetooth6.0 / Android16 / 64GB のような仕様の型番風の数字は、
# 商品を特定する手がかりにならない。SPEC_TOKEN に当たるトークンは
# looks_identifiable での判定から除く。
SPEC_TOKEN = re.compile(
    r"^(Bluetooth|BT|Wi-?Fi[0-9]*|USB(-?C)?|HDMI|Android|iOS|iPhone|iPad|"
    r"Widevine|IPX?|4K|8K|HD|LED|Type-?C)[0-9.\-]*$"
    r"|^[0-9]+(\.[0-9]+)?(GB|TB|MB|K|W|V|L|cm|mm|kg|mAh|インチ|型|畳|人|枚|点|冠|週|位)$",
    re.I)


# 商品名に型番らしき文字列（英字と数字が混ざる3文字以上のトークンで、
# 仕様の記載ではないもの）が無く、出品も公式ストアでない商品。記事に
# しても「メーカー名・型番を特定できない」としてレビュー
# （docs/review-rules.md 5-1）で必ず破棄される。ここで除外はせず
# 並び順を後ろに回すだけにする。判定の精度は目安どまり（「純」の
# ような製品固有名は拾えない）なので、除外すると書ける商品まで
# 取りこぼす。実際、2026-09-10 はレビュー件数の多い順に並んだ上位
# 5件がすべてこの型で、本文を書いてから5本とも破棄され、その日の
# 公開が0本になった。
def looks_identifiable(name, shops):
    """メーカー名・型番で読者・校閲が商品を特定できそうか（目安）。"""
    if any(is_official(v) for v in (shops or {}).values()):
        return True
    for t in re.split(r"[\s　/／・,、()（）\[\]【】.]+", str(name or "")):
        if len(t) < 3 or SPEC_TOKEN.match(t):
            continue
        if re.search(r"[A-Za-z]", t) and re.search(r"[0-9]", t):
            return True
    return False


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
    "kitchen":    {"rakuten_genre": 100644, "words": ["キッチン家電"]},
    "health":     {"rakuten_genre": 100938, "words": ["健康計測"]},
    "beauty":     {"rakuten_genre": 100939, "words": ["美容家電"]},
    "pet":        {"rakuten_genre": 101213, "words": ["ペット用品"]},
    "fashion":    {"rakuten_genre": 100371, "words": ["メンズファッション"]},
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
        # 楽天は理由を返してくれる。刷新の前後で入れ物が変わったので両方拾う。
        try:
            j = json.loads(body)
            body = ((j.get("errors") or {}).get("errorMessage")
                    or j.get("error_description") or j.get("error") or body)
        except Exception:                                 # noqa: BLE001
            pass
        raise RuntimeError(f"HTTP {ex.code}: {body}") from ex


# ----------------------------------------------------------- 楽天市場

def _rakuten_image(it):
    first = (it.get("mediumImageUrls") or it.get("smallImageUrls") or [None])[0]
    if not first:
        return ""
    return first if isinstance(first, str) else (first.get("imageUrl") or "")


def rakuten_search(app_id, access_key=None, genre=None, keyword=None, jan=None,
                   hits=30, sort="-reviewCount", item_code=None):
    """楽天商品検索API。JANを渡すときは keyword に入れる（専用の欄がない）。
       アクセスキーはURLに載せず、accessKey ヘッダで送る。

       item_code は「店舗コード/商品コード」。これを渡すと、その商品だけが
       返る（検索語での取り違えが起きない）。刷新後のAPIが受け付けない
       場合は結果が空になるので、呼ぶ側で次の手に進むこと。"""
    q = {
        "applicationId": app_id,
        "format": "json",
        "formatVersion": 2,
        "hits": hits,
        "sort": sort,
        "imageFlag": 1,          # 画像のある商品だけ
        "availability": 1,       # 在庫のある商品だけ
    }
    if genre:
        q["genreId"] = genre
    if item_code:
        q["itemCode"] = item_code
    else:
        kw = jan or keyword
        if kw:
            q["keyword"] = kw
    # 楽天は、アプリ登録時に届け出たURLと同じ Referer を要求する
    # （無いと REQUEST_CONTEXT_BODY_HTTP_REFERRER_MISSING で弾かれる）。
    head = {"Origin": RAKUTEN_ORIGIN, "Referer": RAKUTEN_ORIGIN + "/"}
    if access_key:
        head["accessKey"] = access_key
    data = get_json(RAKUTEN_API + "?" + urllib.parse.urlencode(q), head)
    out = []
    # 刷新で items（小文字・平たい配列）になったが、古い形も受けておく。
    for w in (data.get("items") or data.get("Items") or []):
        it = w.get("Item") or w.get("item") or w
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
            # formatVersion=2 は文字列の配列、旧形式は {imageUrl} の配列
            "image": _rakuten_image(it),
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


def item_key(url):
    """商品ページURLから、店舗と商品コードの部分だけを取り出す。
       クエリやアフィリエイトの飾りが付いても、同じ商品だと分かる。

       楽天  https://item.rakuten.co.jp/<店舗>/<商品コード>/
       Yahoo https://store.shopping.yahoo.co.jp/<店舗>/<商品コード>.html"""
    u = urllib.parse.urlsplit(str(url or ""))
    if not u.netloc:
        return ""
    path = re.sub(r"\.html?$", "", u.path.strip("/"))
    parts = [x for x in path.split("/") if x]
    if len(parts) < 2:
        return ""
    return u.netloc.lower() + "/" + "/".join(parts[:2]).lower()


def known_items(arts):
    """すでに記事にした商品ページ。JANの無い商品は、これでしか見分けが
       つかない。実際、JANの無い商品で同じ記事が2本できた。
       題名どうしの比較では防げない（記事の題名とモールの商品名は別物で、
       先頭20文字が一致しない）。"""
    keys = set()
    for a in arts:
        for k in ("rakuten_url", "yahoo_url", "amazon_url"):
            key = item_key(a.get(k))
            if key:
                keys.add(key)
    return keys


def build_candidates(rakuten_id, rakuten_key, yahoo_id, categories,
                     limit, per_category):
    arts = json.load(io.open(os.path.join(ROOT, "content", "articles.json"),
                             encoding="utf-8"))
    seen_jan, _ = known_products(arts)
    seen_names = {clean_name(a.get("title", ""))[:20] for a in arts}
    seen_items = known_items(arts)

    out = []
    for cat in categories:
        conf = CATEGORY_MAP.get(cat)
        if not conf:
            print(f"::warning::カテゴリー {cat} の対応表がありません", file=sys.stderr)
            continue

        # 登録されているモールを両方とも検索して結果を合わせる。
        # 片方だけを見ると、そのモールにしか無い商品を取りこぼす。
        found = []
        if rakuten_id:
            try:
                found += rakuten_search(rakuten_id, rakuten_key,
                                        genre=conf["rakuten_genre"],
                                        hits=per_category)
            except Exception as ex:                       # noqa: BLE001
                # ジャンルは改編される。弾かれたらキーワードで探し直す。
                if "genre" in str(ex).lower():
                    time.sleep(PAUSE)
                    try:
                        found += rakuten_search(rakuten_id, rakuten_key,
                                                keyword=conf["words"][0],
                                                hits=per_category)
                    except Exception as ex2:              # noqa: BLE001
                        print(f"::warning::楽天の検索に失敗（{cat}）: {ex2}",
                              file=sys.stderr)
                else:
                    print(f"::warning::楽天の検索に失敗（{cat}）: {ex}",
                          file=sys.stderr)
            time.sleep(PAUSE)
        if yahoo_id:
            try:
                found += yahoo_search(yahoo_id, query=conf["words"][0],
                                      hits=per_category)
            except Exception as ex:                       # noqa: BLE001
                print(f"::warning::Yahoo!の検索に失敗（{cat}）: {ex}", file=sys.stderr)
            time.sleep(PAUSE)

        # レビューの多い順に混ぜる。モールごとに固まらないようにする。
        found.sort(key=lambda e: -e["reviews"])

        for e in found:
            if e["reviews"] < MIN_REVIEWS or e["rating"] < MIN_RATING:
                continue
            if not (MIN_PRICE <= e["price"] <= MAX_PRICE):
                continue
            # 同じ商品ページを指す商品は採らない。JANの無い商品では、
            # これが唯一の確かな手がかりになる。
            ikey = item_key(e.get("url"))
            if ikey and ikey in seen_items:
                continue
            name = clean_name(e["name"])
            if name[:20] in seen_names:
                continue
            # 名前が売り文句になっている商品と、分野が合わない商品は採らない。
            # ここで落としておかないと、題名もURLも作れない記事になる。
            if looks_like_ad(name) or not fits_category(name, cat):
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
                        alt = rakuten_search(rakuten_id, rakuten_key,
                                             jan=jan, hits=20,
                                             sort="+itemPrice")
                        best = pick_cheapest(alt)
                        if best:
                            shops["rakuten"] = best
                    except Exception:                     # noqa: BLE001
                        pass
                    time.sleep(PAUSE)
                seen_jan.add(jan)

            seen_names.add(name[:20])
            if ikey:
                seen_items.add(ikey)
            for v in shops.values():
                k2 = item_key(v.get("url"))
                if k2:
                    seen_items.add(k2)
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

    # まず型番・メーカー名を特定できそうな商品を前に、そのうえで
    # レビュー件数の多い順（記事の土台になる材料が多い商品から並べる）。
    # 特定できなそうな商品を除外はしない。判定の目安が外れることも
    # あるため、後ろに回すだけにして候補からは消さない。
    out.sort(key=lambda c: (not looks_identifiable(c["name"], c["shops"]),
                            -c["reviews"], -c["rating"]))
    return out[:limit]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", action="append",
                    help="対象カテゴリー（省略すると全部）")
    ap.add_argument("--limit", type=int, default=20, help="出力する候補の数")
    ap.add_argument("--per-category", type=int, default=30,
                    help="カテゴリーごとに取得する件数")
    ap.add_argument("--out", default="content/candidates.json")
    ap.add_argument("--require-rakuten", action="store_true",
                    help="楽天の商品ページが取れた商品だけを候補にする")
    args = ap.parse_args()

    rakuten_id = os.environ.get("RAKUTEN_APP_ID", "").strip()
    rakuten_key = os.environ.get("RAKUTEN_ACCESS_KEY", "").strip()
    if rakuten_id and not rakuten_key:
        print("::warning::RAKUTEN_ACCESS_KEY が未設定です。"
              "2026年2月の刷新後、楽天はアクセスキーが無いと認証を通りません。",
              file=sys.stderr)
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

    cands = build_candidates(rakuten_id, rakuten_key, yahoo_id, cats,
                             args.limit, args.per_category)

    if args.require_rakuten:
        # 楽天の商品ページが取れた商品だけに絞る。
        # 一覧に出す実物写真は、そのページから引いてくるため。
        # 取れない商品は記事にしても、写真が自動生成の絵のままになる。
        before = len(cands)
        cands = [c for c in cands if (c.get("rakuten_url") or "").strip()]
        print(f"楽天の商品ページがあるものだけに絞りました："
              f"{before} → {len(cands)} 件")

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
