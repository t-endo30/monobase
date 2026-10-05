#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""確認済みの一次ページ情報を記事へ追加する小さな編集用ツール。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE = {
    "switchbot-hub-remote-review": {
        "official_url": "https://www.switchbot.jp/collections/all/products/switchbot-hub2",
        "facts": [
            "SwitchBot公式商品ページでハブ2を確認",
            "楽天市場の個別商品ページで本体サイズ80×70×23mm、重量63gと表示",
            "楽天市場の個別商品ページでWi-Fiは2.4GHz帯のみ対応と表示",
            "楽天市場の個別商品ページで温度・湿度測定機能、Matter対応、赤外線家電操作を案内",
            "楽天市場の個別商品ページで保証期間は購入日から1年間と表示",
            "公式販売ページの利用者投稿では、古い家電で一部操作だけになるという指摘と、アプリで複数家電を管理できたという投稿を確認",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた対応可否の注意",
            "who": "SwitchBot公式店 楽天市場の利用者投稿（2026年9月10日投稿）",
            "text": "個別投稿では、古い家電ではリモコン登録後も電源のオン・オフだけになり、温度調整や照明の明暗調整ができなかったという指摘がありました。対応状況は家電とリモコンの組み合わせで確認が必要です。",
            "negative": True,
            "fix_title": "古い家電は操作範囲を先に確認する",
            "fix": "購入前に、使いたい家電のメーカー・型番と、必要な操作が対応表やアプリで確認できるかを照合してください。",
        }, {
            "heading": "複数家電をまとめたという投稿",
            "who": "SwitchBot公式店 楽天市場の利用者投稿（2026年9月7日投稿）",
            "text": "別の投稿では、エアコンとテレビを設定し、説明書だけでは詳しい設定が分かりにくかったため、案内を見ながら設定したという内容が確認できます。個別の環境での感想として扱います。",
            "negative": False,
            "fix_title": "設定に必要な時間を見込む",
            "fix": "使う家電を先に列挙し、各リモコンの登録と動作確認を一台ずつ行える時間を確保してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.switchbot.jp/collections/all/products/switchbot-hub2",
            "title": "SwitchBot公式 ハブ2",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/switchbot/10000076/",
            "title": "SwitchBot公式店 楽天市場 個別商品ページ",
            "checked_at": "2026-10-06",
        }],
    },
    "fujiboeki-folding-stool-review": {
        "official_url": "https://www.fujiboeki.jp/products/86078/",
        "facts": [
            "不二貿易公式情報でフォールディングステップスツール H39cm、品番86078を確認",
            "公式情報のサイズ：幅39×奥行33×高さ39cm、座面290×220mm",
            "公式情報の折りたたみ時サイズ：幅390×奥行45×高さ530mm",
            "公式情報の重量：1.45kg、座面耐荷重：150kg",
            "公式情報の材質：本体ポリプロピレン、滑り止めTPR",
            "公式情報のカラー：ホワイト／カーキ／ブラック",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた使い勝手",
            "who": "楽天市場みんなのレビュー（2022年3月31日投稿）",
            "text": "個別投稿では、開閉が簡単で使いやすく、高さもちょうどよいという感想が確認できます。これは1件の投稿の内容であり、全購入者の傾向とは扱いません。",
            "negative": False,
            "fix_title": "開閉と高さを設置場所で確認する",
            "fix": "開いた状態の幅・奥行きと高さ39cmが置き場所に合うかを先に測り、折りたたんだ状態で収納できる場所も確認してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.fujiboeki.jp/products/86078/",
            "title": "不二貿易公式商品情報 86078",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/kankapro/20240602080328_138/",
            "title": "楽天市場 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/item/1/227725_10001649/1.1/",
            "title": "楽天市場 みんなのレビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "ylt-ag30e-yamazen": {
        "official_url": "https://book.yamazen.co.jp/product/detail/I00004142",
        "facts": [
            "山善の商品情報サイトで型番YLT-AG30Eの掲載を確認",
            "楽天市場の個別商品ページで本体サイズは幅35.5×奥行35×高さ66-85cm、重量2.8kgと表示",
            "楽天市場の個別商品ページで電源はAC100V（50/60Hz）、消費電力は38/39W（50/60Hz）と表示",
            "楽天市場の個別商品ページで30cm羽根、風量3段階、左右首振り、切りタイマー、押しボタン式と商品名・説明に表示",
            "楽天市場の個別商品ページでコード長さ約1.6m、切タイマー最高3時間、メーカー保証1年と表示",
        ],
        "voices": [{
            "heading": "楽天市場のレビュー本文で確認できた声",
            "who": "楽天市場みんなのレビュー（2026-10-06確認）",
            "text": "個別投稿では、組み立てが簡単で和室にグレージュが合うという感想、ボタン式を選んで満足しているという感想、台座部分の付着物が気になったという指摘を確認できます。いずれも個別投稿で、全購入者の傾向とは扱いません。",
            "negative": True,
            "fix_title": "組み立てと台座を確認する",
            "fix": "組み立て後は台座や首のねじ部分を確認し、設置場所の色やコード長さが合うかを購入前に照合してください。",
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
            "heading": "個別投稿で確認できた飲み方",
            "who": "利用者の声（楽天市場の個別商品ページ、2026-10-06確認）",
            "text": "個別投稿では、中細挽きの粉を毎日飲むためリピートしているという声、4種類の味と香りを楽しんでいるという声、すっきりした飲み口で他の種類も楽しみという声が確認できます。個別投稿の内容であり、全購入者の傾向とは扱いません。",
            "negative": False,
            "fix_title": "飲む量と挽き方を先に決める",
            "fix": "毎日飲む量、豆のままか粉か、挽き方を先に決めてから、2kgを保存できる密閉容器と消費ペースを確認してください。",
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
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/262969_10000204/1.1/",
            "title": "楽天市場 みんなのレビュー",
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
