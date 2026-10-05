#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""確認済みの一次ページ情報を記事へ追加する小さな編集用ツール。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE = {
    "rs-60e3-lcd-pdf": {
        "official_url": "https://www.rowa.co.jp/products/tc-2001",
        "facts": [
            "ロワジャパン公式商品ページで商品型番TC-2001、RS-60E3互換を確認",
            "公式商品ページで対応カメラ機種と、端子形状・リモートスイッチ型番の確認が必要と案内",
            "公式商品ページでフォーカス・シャッター・バルブ制御ロック、インターバルタイマー、露光時間設定の説明を確認",
            "Yahoo!ショッピングの個別商品ページで商品コードTC-2001、RS-60E3互換、レビュー本文を確認",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた操作性と注意点",
            "who": "Yahoo!ショッピング ロワジャパン個別商品ページの利用者の声（2026-10-06確認）",
            "text": "個別投稿では、Canon機で問題なく動作し、インターバル撮影やディレイ設定を直感的に使えたという声が確認できます。一方で、電源スイッチがなく表示が点いたままになること、液晶の見え方や電池管理が気になるという指摘もあります。個別投稿の内容であり、すべてのカメラとの互換性を保証するものではありません。",
            "negative": True,
            "fix_title": "端子と電池管理を購入前に確認する",
            "fix": "カメラ側の端子形状と対応型番を公式一覧で照合し、使用しないときに電池を外す運用ができるかを確認してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.rowa.co.jp/products/tc-2001",
            "title": "ロワジャパン公式 TC-2001 商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://store.shopping.yahoo.co.jp/rowa/tc-2001.html",
            "title": "Yahoo!ショッピング ロワジャパン TC-2001 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://shopping.yahoo.co.jp/review/item/list?page_key=tc-2001&store_id=rowa",
            "title": "Yahoo!ショッピング 利用者の声 TC-2001",
            "checked_at": "2026-10-06",
        }],
    },
    "mvp3-3in1": {
        "facts": [
            "楽天市場の個別商品ページで商品番号pet-trimerb、商品名ペットトリマーβを確認",
            "個別商品ページで本体重量180g、爪やすり用・肉球周り用の3アタッチメント、USB充電、充電時間約3〜4時間を確認",
            "個別商品ページで刃の長さ2mm、交換時は試運転を行う注意、初回は音に慣らす注意を確認",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた使用感",
            "who": "楽天市場の商品ページに表示された利用者の声（2026-10-06確認）",
            "text": "個別投稿では、爪を切った後のバリ取りが楽で、モーター音がうるさくないという感想、まだ使用前だが刃先を見て使えそうという声、使いやすいという感想を確認できます。投稿時点や個体差を含む利用者の声であり、すべてのペットに同じ結果が出るとは扱いません。",
            "negative": False,
            "fix_title": "音への慣らしとアタッチメント固定を確認する",
            "fix": "初回は電源音を聞かせて反応を確認し、アタッチメントが確実にはまっているかを試運転で確認してから使用してください。",
        }],
        "source_notes": [{
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/next-online/pet-trimerb/",
            "title": "楽天市場 Nextオンライン ペットトリマーβ 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/item/1/372877_10000162/1.1/",
            "title": "楽天市場 利用者の声（商品ページから確認）",
            "checked_at": "2026-10-06",
        }],
    },
    "kaedear-kdr-m11c": {
        "official_url": "https://www.kaedear.com/products/kdr-m11c",
        "facts": [
            "Kaedear KDR-M11C（クイックホールド）の商品番号を確認",
            "商品情報でホルダーサイズは縦132〜175mm、横68〜85mm、厚さ12mm、重量150gと表示",
            "商品情報で17mmボールマウント、縦横の向き調整、バー・ミラーマウント等の同梱品を確認",
            "楽天の商品情報でJAN 4580675590427、メーカー型番KDR-M11Cを確認",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた脱着と固定の感想",
            "who": "Webike利用者レビューおよび楽天市場の個別投稿（2026-10-06確認）",
            "text": "個別投稿では、スマートフォンを置いてロックする操作とレバーで外す操作が簡単という感想、多様なハンドル径に対応できる点を評価する声を確認できます。一方で、荒れた路面では補助ラバーを使うという記述や、端末サイズごとの確認が必要という注意もあります。個別投稿の内容であり、すべての車種・端末に当てはまるとは扱いません。",
            "negative": True,
            "fix_title": "端末寸法と取付場所を先に照合する",
            "fix": "ケースを含めた端末の幅・高さ・厚さを測り、ハンドル径またはミラー取付部が同梱マウントに合うかを購入前に確認してください。荒れた路面で使う場合は補助ラバーや防振対策も確認しましょう。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.kaedear.com/products/kdr-m11c",
            "title": "Kaedear公式 KDR-M11C 商品情報",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/kaedear/kdr-m11c/",
            "title": "楽天市場 Kaedear公式 KDR-M11C 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://thai.webike.net/en/review/article/755500",
            "title": "Webike 利用者レビュー KDR-M11C",
            "checked_at": "2026-10-06",
        }],
    },
    "cellularline-iphone18pro-iphone18promax": {
        "official_url": "https://www.lauda.co.jp/c/brand/cl/handypadk",
        "rakuten_url": "https://item.rakuten.co.jp/lauda/cl-grip/",
        "facts": [
            "Cellularline日本代理店ページでGRIPの案内を確認",
            "Cellularline公式の車載ホルダー案内で、製品群に固定方式の異なる車載ホルダーがあることを確認",
            "楽天市場の個別商品ページで商品番号XL-GRIP、対応機種欄にiPhone 18 Pro／18 Pro Maxなどの表示を確認",
            "楽天市場の個別商品ページでダッシュボード等への粘着固定を特徴として表示",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた固定力と設置条件",
            "who": "楽天市場みんなのレビュー（ZEROA楽天市場店の個別商品ページ、2026-10-06確認）",
            "text": "個別投稿では、平らな面積が少ない車内でも安定したという声、長期間使っても剥がれや劣化が少ないという声、粘着力が強い一方でほこりが付きやすいという指摘を確認できます。個別投稿の内容であり、すべての車種や使用環境に当てはまるとは扱いません。",
            "negative": True,
            "fix_title": "貼り付け面と取り外し条件を確認する",
            "fix": "レンタカーで使う場合は、ダッシュボードの素材・曲面・貼り付け可否を事前に確認し、返却時に跡を残さず取り外せるかも販売ページの案内で確かめてください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.lauda.co.jp/c/brand/cl/handypadk",
            "title": "Cellularline日本代理店 ブランド商品案内",
            "checked_at": "2026-10-06",
        }, {
            "type": "official_catalog",
            "url": "https://www.cellularline.com/en-fr/Power-and-Holders/Car-and-Bike-Holders/c-0009",
            "title": "Cellularline公式 車載・自転車ホルダー一覧",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/lauda/cl-grip/",
            "title": "楽天市場 Cellularline GRIP 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/212271_10001703/1.1/",
            "title": "楽天市場 みんなのレビュー Cellularline GRIP",
            "checked_at": "2026-10-06",
        }],
    },
    "led-pv-bl2h-n": {
        "official_url": "https://kadenfan.hitachi.co.jp/clean/lineup/pv-bl2h/",
        "facts": [
            "日立公式商品ページでコードレス式スティッククリーナーPV-BL2H（N色）を確認",
            "日立公式の仕様表示で標準質量1.1kg、自走式のパワフル スマートヘッド light、ヘッドライトを確認",
            "日立公式の取扱説明書でPV-BL2Hの使用方法・お手入れ方法を確認",
            "楽天市場の個別商品ページで型番PV-BL2H-N、シャンパンゴールド、回転ブラシ水洗い可の表示を確認",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた軽さと注意点",
            "who": "楽天市場みんなのレビュー（楽天スーパーDEALSHOPの個別商品ページ、2026-10-06確認）",
            "text": "個別投稿では、軽さやヘッドの滑り、前方ライトの見やすさを評価する声が確認できます。一方で、従来のスタンドが使えず充電方法を工夫したという指摘や、回転ブラシが軽い布類を巻き込むことがあるという注意も確認できます。個別投稿の内容であり、全購入者の傾向とは扱いません。",
            "negative": True,
            "fix_title": "収納方法と床面の巻き込みを先に確認する",
            "fix": "購入前に、現在使っているスタンドや充電場所がPV-BL2H-Nの収納・充電方法に合うかを確認してください。軽いラグや布類を掃除する場合は、回転ブラシの巻き込みに注意できるかも確認しましょう.",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://kadenfan.hitachi.co.jp/clean/lineup/pv-bl2h/",
            "title": "日立公式 PV-BL2H 商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "official_manual",
            "url": "https://kadenfan.hitachi.co.jp/support/clean/item/docs/pv-bl2h_a.pdf",
            "title": "日立公式 PV-BL2H 取扱説明書",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/superdeal/11776pvbl2hn20220523/",
            "title": "楽天市場 個別商品ページ PV-BL2H-N",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/363461_10002065/1.1/",
            "title": "楽天市場 みんなのレビュー PV-BL2H-N",
            "checked_at": "2026-10-06",
        }],
    },
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
