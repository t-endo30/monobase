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
  ・記事の商品名の語が、商品側にどれだけ入っているかで測る
  ・含有率が --min-score 未満のものは採らない
  ・Pro・第2世代など、記事に無い枝番が付いた商品は採らない
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
from pick_products import rakuten_search, yahoo_search   # noqa: E402

# 楽天は毎秒1回まで。短くすると429で弾かれるので、少し余裕を持たせる。
PAUSE = 1.5

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 本体ではなく付属品を売っている商品名。これを掴むと読者が別物を買う。
ACCESSORY = re.compile(
    r"(ケース|カバー|フィルム|保護|スタンド|ホルダー|替え|交換用|互換|"
    r"用アダプタ|プロテクター|収納袋|ポーチ|スキンシール|"
    r"中古|美品|ジャンク|訳あり|アウトレット|リユース|再生品)")

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
    """比べる前の下ごしらえ。飾りを落として小文字へ。"""
    s = DECOR.sub(" ", str(s or ""))
    s = re.sub(r"[\s　・/／,、。\-—–_'\"()（）\[\]【】]+", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


# 型番の枝分かれを表す語。記事の商品名に無いのに商品側にあるときは、
# 別モデル（Pro・Plus・第2世代など）を掴んでいる。
# 前後が英数字だと別の語の一部になるもの（se が sensor に当たるなど）
VARIANT = re.compile(
    r"(?<![a-z0-9])(pro|plus|max|mini|lite|halo|ultra|se|neo|air|"
    r"ii|iii|advanced|active|上位)(?![a-z0-9])")
# くっついて書かれるもの（コアラピロー2ndGen のような形）
VARIANT_JOINED = re.compile(r"(2nd|3rd|第[2-9]世代|新型|gen\d)")


def variants(name):
    n = norm(name)
    return set(VARIANT.findall(n)) | set(VARIANT_JOINED.findall(n))


def tokens(name):
    """商品名を、照合に使う語に割る。
       英数字（型番）は1語ずつ、日本語はまとまりごとに見る。"""
    n = norm(name)
    out = [t for t in n.split(" ") if t]
    return out or [n]


# 英字か数字を含む語。ブランド名や型番にあたる。
MODEL = re.compile(r"[a-z0-9][a-z0-9\-]*")


def model_tokens(name):
    """商品名のうち、ブランド・型番にあたる語。
       これが1つも無い商品名は一般名詞だけで、商品を特定できない。
       「Watch 5」の 5 のような一桁の数字も、世代を分ける大事な語なので拾う
       （落とすと Watch 6 を掴む）。"""
    return [t for t in tokens(name)
            if MODEL.fullmatch(t) and (len(t) >= 2 or t.isdigit())]


def model_ok(name, cand):
    """記事の型番・ブランドが、商品側の名前に入っているか。
       数字だけの語（Watch の 5 など）は、単体で探すとクーポンの日時や
       寸法に当たってしまう。直前の語とつなげた形で探す
       （「watch5」を探せば Watch 6 を弾ける）。"""
    ts = tokens(name)
    flat = norm(cand).replace(" ", "")
    for i, t in enumerate(ts):
        if not (MODEL.fullmatch(t) and (len(t) >= 2 or t.isdigit())):
            continue
        if t.isdigit() and len(t) <= 2 and i > 0:
            if (ts[i - 1] + t) not in flat:
                return False
        elif t not in flat:
            return False
    return True


def coverage(name, cand):
    """記事の商品名の語が、商品側の名前にどれだけ含まれているか。
       楽天の商品名は装飾が長いので、全体の似かたではなく
       「記事の語が入っているか」で見ないと正しく測れない。"""
    ts = tokens(name)
    if not ts:
        return 0.0
    flat = norm(cand).replace(" ", "")
    hit = sum(1 for t in ts if t.replace(" ", "") in flat)
    return hit / len(ts)


def best_match(name, cands, min_score):
    """検索結果から、記事の商品といちばん近いものを選ぶ。
       含有率がいちばん高いもの。同じなら、余計な語が少ない＝短い方を採る
       （装飾やセット品を掴みにくい）。返すのは (商品, 含有率)。"""
    scored = []
    for c in cands:
        cname = c.get("name") or ""
        if not c.get("url"):
            continue
        # 付属品だけを売っている商品は、記事の商品ではない
        if ACCESSORY.search(cname) and not ACCESSORY.search(name):
            continue
        # 記事に無い枝番（Pro・第2世代など）が付いていたら別モデル
        extra = variants(cname) - variants(name)
        if extra:
            continue
        # ブランド・型番は、1語でも欠けたら別商品として扱う
        if not model_ok(name, cname):
            continue
        scored.append((coverage(name, cname), len(norm(cname)), c))
    if not scored:
        return None, 0.0
    scored.sort(key=lambda x: (-x[0], x[1]))
    top, _, hit = scored[0]
    return (hit, top) if top >= min_score else (None, top)


def clean_url(u):
    """楽天APIは商品URLに自前の追跡パラメータ（rafcid）を付けて返す。
       こちらは楽天アフィリエイトのIDでリンクを包むので、これを外す。"""
    u = str(u or "")
    base, _, q = u.partition("?")
    if not q:
        return u
    keep = [kv for kv in q.split("&")
            if kv and not kv.split("=")[0] in ("rafcid", "scid", "sc2id")]
    return base + ("?" + "&".join(keep) if keep else "")


def shorten(name):
    """検索で1件も返らないときに試す、短くした言い方。
       楽天の検索は語をすべて含む商品を探すため、語が多いと0件になる。"""
    ts = name.split()
    out = []
    for n in (3, 2):
        if len(ts) > n:
            out.append(" ".join(ts[:n]))
    return out


def search(shop, keys, jan=None, keyword=None, tries=3):
    """1回ぶんの検索。レート制限（429）は間を空けて数回まで待つ。"""
    for n in range(tries):
        try:
            if shop == "rakuten":
                return rakuten_search(keys["rakuten_id"], keys["rakuten_key"],
                                      jan=jan, keyword=keyword, hits=20)
            return yahoo_search(keys["yahoo_id"], jan=jan, query=keyword,
                                hits=20)
        except Exception as ex:                       # noqa: BLE001
            if "429" in str(ex) and n < tries - 1:
                time.sleep(PAUSE * (n + 2))
                continue
            raise


def lookup(shop, name, jan, keys, min_score):
    """1商品ぶんの検索。JANがあればJANで、無ければ商品名で引く。
       0件のときは、商品名を短くして引き直す（楽天は語をすべて含む
       商品を探すため、語が多いと0件になりやすい）。"""
    plans = ([("jan", jan)] if jan else [])
    plans += [("keyword", name)] + [("keyword", q) for q in shorten(name)]
    fallback_s = 0.0
    for how, q in plans:
        try:
            cands = search(shop, keys,
                           jan=q if how == "jan" else None,
                           keyword=q if how == "keyword" else None)
        except Exception as ex:                       # noqa: BLE001
            print(f"      検索できませんでした（{shop}/{q}）：{ex}")
            time.sleep(PAUSE)
            continue
        time.sleep(PAUSE)
        if not cands:
            continue
        # JANは型番そのものなので、名前の一致は緩めてよい
        hit, s = best_match(name, cands, 0.0 if how == "jan" else min_score)
        if hit:
            hit = dict(hit, url=clean_url(hit.get("url")))
            return hit, s, ("JAN" if how == "jan" else f"「{q}」")
        fallback_s = max(fallback_s, s)
    return None, fallback_s, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="記事に書き戻す（付けないと下見だけ）")
    ap.add_argument("--shops", default="rakuten,yahoo",
                    help="対象のモール。既定は rakuten,yahoo")
    ap.add_argument("--min-score", type=float, default=0.75,
                    help="商品名の含有率の下限（0〜1）。既定 0.75")
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
    vague = []
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
        # ブランドも型番も無い題名（「デスクサイドラック」など）は、
        # 検索しても記事とは別の商品が当たる。人が選ぶしかない。
        if not jan and not model_tokens(name):
            print(f"\n・{a.get('slug')}：題名に型番・ブランドが無いため"
                  f"飛ばします（{name}）")
            vague.append((a.get("slug"), name))
            continue
        print(f"\n・{a.get('slug')}")
        print(f"   記事の商品：{name}" + (f"（JAN {jan}）" if jan else ""))
        for shop in need:
            hit, s, how = lookup(shop, name, jan, keys, args.min_score)
            label = "楽天" if shop == "rakuten" else "Yahoo!"
            if not hit:
                print(f"   {label}：見つかりません（最も近い含有率 {s:.2f}）")
                missed.append((a.get("slug"), label))
                continue
            print(f"   {label}：{hit['name'][:56]}")
            print(f"        含有率 {s:.2f}（{how}で検索） / {hit['price']:,}円")
            print(f"        {hit['url']}")
            a[f"{shop}_url"] = hit["url"]
            filled[shop] += 1

    print("\n" + "-" * 56)
    for shop in shops:
        label = "楽天" if shop == "rakuten" else "Yahoo!"
        print(f"{label}：{filled[shop]} 本ぶんのURLが見つかりました")
    if missed:
        print(f"見つからなかった組み合わせ：{len(missed)} 件")
    if vague:
        print(f"\n題名で商品を特定できず、手で選ぶ必要があるもの：{len(vague)} 本")
        for slug, nm in vague:
            print(f"   ・{slug}（{nm}）")

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
