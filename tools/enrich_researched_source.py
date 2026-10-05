#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""確認済みの一次ページ情報を記事へ追加する小さな編集用ツール。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE = {
    "ylt-ag30e-yamazen": {
        "official_url": "https://book.yamazen.co.jp/product/detail/I00004142",
        "facts": [
            "山善の商品情報サイトで型番YLT-AG30Eの掲載を確認",
            "楽天市場の個別商品ページで本体サイズは幅35.5×奥行35×高さ66-85cm、重量2.8kgと表示",
            "楽天市場の個別商品ページで電源はAC100V（50/60Hz）、消費電力は38/39W（50/60Hz）と表示",
            "楽天市場の個別商品ページで30cm羽根、風量3段階、左右首振り、切りタイマー、押しボタン式と商品名・説明に表示",
        ],
        "voices": [{
            "heading": "楽天市場のレビュー本文で確認できた声",
            "who": "楽天市場みんなのレビュー（2026-10-06確認）",
            "text": "2026年6月1日の投稿では、シンプルでタイマー付きの点、軽量で組み立てやすい点が評価されていました。一方、別の2026年9月11日の投稿では、台座の底面にフェルトを貼って使っているという指摘がありました。いずれも個別投稿で、全購入者の傾向を代表すると断定しません。",
            "negative": True,
            "fix_title": "組み立て後に底面を確認する",
            "fix": "組み立てやすさを評価する声がある一方、底面の状態を気にする投稿もあるため、設置前に台座の接地部を確認し、床を傷つけない置き方を検討してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://book.yamazen.co.jp/product/detail/I00004142",
            "title": "山善 商品情報サイト（YLT-AG30E掲載）",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/yamazenkaden/1467895/",
            "title": "山善 家電店 楽天市場 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/205937_10001743/1.1/",
            "title": "楽天市場 みんなのレビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "kitchen-20261005": {
        "official_url": "https://chimoto-coffee.co.jp/",
        "facts": [
            "販売ページの内容量：1セットは4種類・500g×4袋の合計2kg",
            "販売ページの杯数目安：200杯分",
            "販売ページの表示：豆・粉と挽き方を選べる形式",
            "販売ページの賞味期限：製造日より1年（袋の裏面に印字）",
            "販売ページの保存方法：直射日光・高温多湿を避け、密閉保存",
            "商品ページに記載された4種：ロイヤルミディアムブレンド、デリシャスミックス、ジャーマンシティブレンド、リッチブレンド",
        ],
        "voices": [{
            "heading": "商品ページで確認できたレビュー表示",
            "who": "楽天市場の商品ページ（2026-10-06確認）",
            "text": "商品ページのレビュー欄には、評価5.00の購入者投稿が表示されていました。ただし、これは表示された個別投稿の確認であり、4種類の味や商品の全体傾向を代表すると断定しません。",
            "negative": False,
            "fix_title": "レビューの数字だけで味を決めない",
            "fix": "味の好みは個人差が大きいため、レビューの平均点だけでなく、豆か粉か、挽き目、保存条件を自分の飲み方と照合してください。",
        }],
        "source_notes": [{
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/chimoto-coffee/10000204/",
            "title": "チモトコーヒー 大入り福袋 商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "official_company",
            "url": "https://chimoto-coffee.co.jp/",
            "title": "チモトコーヒー公式サイト",
            "checked_at": "2026-10-06",
        }],
    }
}


def main():
    path = os.path.join(ROOT, "content", "articles.json")
    with open(path, encoding="utf-8") as f:
        articles = json.load(f)
    for article in articles:
        data = SOURCE.get(article.get("slug"))
        if not data:
            continue
        article.update({k: v for k, v in data.items() if k != "source_notes"})
        article["source_notes"] = data["source_notes"]
        article["updated"] = "2026-10-06"
        print(f"根拠を追加しました: {article['slug']}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
