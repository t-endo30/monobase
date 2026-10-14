#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Amazon購入履歴のASINを、非Amazonモールの商品ページと照合する。

購入履歴そのものはリポジトリへ持ち込まず、workflowから渡された最小限の
商品情報だけを受け取る。候補にするには、カテゴリ一致、成人向け除外、
ASIN、楽天またはYahoo!の個別URL、同一商品の非Amazon画像、レビュー15件以上、
評価3.0以上をすべて満たす必要がある。
"""
import argparse
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pick_products import (CATEGORY_EXCLUDE, CATEGORY_WORDS, fits_category,
                           model_codes, rakuten_search, yahoo_search,
                           looks_identifiable, MIN_REVIEWS, MIN_RATING)

ADULT = ("オナホ", "オナニー", "ディルド", "アダルト", "エネマ", "コンドーム",
         "TENGA", "バイブ", "ローター", "ラブドール", "セクシー")
ASIN_RE = re.compile(r"^[A-Z0-9]{10}$", re.I)


def norm(value):
    value = str(value or "").lower()
    return re.sub(r"[^0-9a-zぁ-んァ-ヶ一-龥]+", "", value)


def rejected(name, category):
    low = str(name or "").lower()
    if any(word.lower() in low for word in ADULT):
        return "adult"
    if any(word.lower() in low for word in CATEGORY_EXCLUDE.get(category, [])):
        return "category_exclude"
    if not fits_category(name, category):
        return "category_mismatch"
    return ""


def same_product(order_name, shop_name):
    """型番一致を最優先し、型番のない商品は保守的な語の重なりで照合する。"""
    order_codes = model_codes(order_name)
    shop_codes = model_codes(shop_name)
    if order_codes:
        return bool(order_codes & shop_codes)
    a = norm(order_name)
    b = norm(shop_name)
    if len(a) < 6 or len(b) < 6:
        return False
    # ブランド・固有語を含む連続部分が残る商品だけ採用する。
    chunks = [x for x in re.split(r"[\s　/／・,、()（）\[\]【】]+", str(order_name))
              if len(norm(x)) >= 3]
    hits = sum(1 for x in chunks if norm(x) in b)
    return hits >= 2 or (hits >= 1 and len(chunks) == 1 and norm(chunks[0]) == b)


def marketplace_query(name):
    """購入履歴の商品名を楽天/Yahoo検索用の短い語へ整える。

    購入履歴には、商品名に説明文やキャンペーン文言まで連結された行が
    あり、楽天APIの keyword 上限（128文字）を超えることがある。長い文字列
    をそのまま渡すと楽天が400を返し、その候補だけでなくページ全体の照合が
    空振りになる。型番が見つかる場合は型番を優先し、見つからない場合は
    商品名の先頭から検索に使える語だけを残す。
    """
    text = re.sub(r"[\r\n\t]+", " ", str(name or ""))
    codes = sorted(model_codes(text))
    if codes:
        query = " ".join(codes)
    else:
        words = re.findall(
            r"[A-Za-z0-9][A-Za-z0-9._/-]{1,}|[ぁ-んァ-ヶ一-龥]{2,}",
            text,
        )
        query = " ".join(words[:10])
    # 楽天APIは記号の組み合わせを「keyword is not valid」として拒否する
    # ことがある。商品同定に不要な記号を空白へ置き換え、語数も絞る。
    query = re.sub(r"[^0-9A-Za-zぁ-んァ-ヶ一-龥 ]+", " ", query)
    query = re.sub(r"\s+", " ", query).strip()
    query = " ".join(query.split()[:8])
    # 楽天の上限より十分短くして、全角文字を含む商品名でも400を避ける。
    query = query[:80] or "商品"
    while len(query.encode("utf-8")) > 96 and query:
        query = query[:-1].rstrip()
    return query or "商品"


def eligible_shop(entry, order_name, category):
    if not entry.get("url", "").startswith(("http://", "https://")):
        return False
    if not entry.get("image", "").startswith(("http://", "https://")):
        return False
    if int(entry.get("reviews") or 0) < MIN_REVIEWS:
        return False
    if float(entry.get("rating") or 0) < MIN_RATING:
        return False
    if not fits_category(entry.get("name"), category):
        return False
    return same_product(order_name, entry.get("name"))


def best(entries, order_name, category):
    ok = [x for x in entries if eligible_shop(x, order_name, category)]
    ok.sort(key=lambda x: (-int(x.get("reviews") or 0), -float(x.get("rating") or 0)))
    return ok[0] if ok else None


def make_candidate(item, shops):
    asin = str(item.get("asin") or "").strip().upper()
    name = str(item.get("name") or "").strip()
    category = str(item.get("category") or "").strip()
    sub = str(item.get("sub") or "").strip()
    chosen = {k: v for k, v in shops.items() if v}
    if not asin or not ASIN_RE.fullmatch(asin) or not name or not category or not chosen:
        return None
    return {
        "source": "amazon_order_history",
        "asin": asin,
        "amazon_url": f"https://www.amazon.co.jp/dp/{asin}",
        "name": name,
        "category": category,
        "sub": sub,
        "order_date": item.get("order_date", ""),
        "order_price": item.get("order_price", ""),
        "rakuten_url": (chosen.get("rakuten") or {}).get("url", ""),
        "yahoo_url": (chosen.get("yahoo") or {}).get("url", ""),
        "images": {k: v.get("image", "") for k, v in chosen.items() if v.get("image")},
        "shops": {k: {"price": int(v.get("price") or 0),
                       "shop_name": v.get("shop_name", ""),
                       "postage_included": bool(v.get("postage_included")),
                       "reviews": int(v.get("reviews") or 0),
                       "rating": float(v.get("rating") or 0)}
                  for k, v in chosen.items()},
        "reviews": max(int(v.get("reviews") or 0) for v in chosen.values()),
        "rating": max(float(v.get("rating") or 0) for v in chosen.values()),
        "price": min(int(v.get("price") or 0) for v in chosen.values() if v.get("price")),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-json", required=True)
    ap.add_argument("--out", default="/tmp/candidates.json")
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args()
    items = json.load(open(args.input_json, encoding="utf-8"))
    rk_id = os.environ.get("RAKUTEN_APP_ID", "").strip()
    rk_key = os.environ.get("RAKUTEN_ACCESS_KEY", "").strip()
    yh_id = os.environ.get("YAHOO_CLIENT_ID", "").strip()
    if not (rk_id or yh_id):
        print("楽天またはYahoo!の認証情報がありません", file=sys.stderr)
        return 1
    out = []
    for i, item in enumerate(items, 1):
        name = str(item.get("name") or "")
        category = str(item.get("category") or "")
        reason = rejected(name, category)
        if reason:
            continue
        shops = {}
        query = marketplace_query(name)
        rk_match = None
        try:
            if rk_id:
                rk_match = best(rakuten_search(rk_id, rk_key, keyword=query), name, category)
                if rk_match:
                    shops["rakuten"] = rk_match
        except Exception as exc:  # noqa: BLE001
            print(f"楽天照合失敗: {exc}", file=sys.stderr)
        # 片方の個別商品ページで条件を満たせば十分。楽天で一致した
        # 商品はYahoo!を呼ばず、API待ちを半分にする。
        if not rk_match:
            time.sleep(1)
            try:
                if yh_id:
                    yh_match = best(yahoo_search(yh_id, query=query), name, category)
                    if yh_match:
                        shops["yahoo"] = yh_match
            except Exception as exc:  # noqa: BLE001
                print(f"Yahoo照合失敗: {exc}", file=sys.stderr)
        candidate = make_candidate(item, shops)
        if candidate:
            out.append(candidate)
        if len(out) >= args.limit:
            break
        time.sleep(1)
    payload = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
               "count": len(out), "items": out}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f"購入履歴由来の照合済み候補: {len(out)}件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
