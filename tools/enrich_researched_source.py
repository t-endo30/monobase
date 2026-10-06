#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""確認済みの一次ページ情報を記事へ追加する小さな編集用ツール。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE = {
    "sspp-3s": {
        "official_url": "https://www.suisaku.com/product/air_pomp/122/",
        "facts": [
            "水作公式の水心シリーズで、水心SSPP-3S、JAN4974105006082、45〜60cm水槽用、最大吐出量3.0L/min、吐出量調節機能を確認",
            "公式説明で振動吸収脚ゴムによる静音化と、SSPP-3Sのエア量を調整するダイヤル機構を確認",
            "楽天市場の個別商品ページで水作 水心 SSPP-3Sの型番・商品同定を確認。エアチューブ等の付属条件は購入時の商品ページを確認する",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた静音性と設置条件",
            "who": "楽天市場のSSPP-3S個別投稿（2026-10-06確認）",
            "text": "個別投稿では、従来使っていたエアーポンプより音が気になりにくい、エア量を調整できる点が便利という声を確認できます。一方で、夜間の室内では作動音が聞こえる、吊り下げると静かになった、エアチューブが別売りだったという記述もあります。水槽台や設置方法によって感じ方は変わるため、投稿者の感想をすべての環境に一般化しません。",
            "negative": True,
            "fix_title": "付属品と設置方法を購入前に確認する",
            "fix": "購入ページでエアチューブなどの付属条件を確認し、設置時は脚ゴムが安定して接地する場所を選んでください。音が気になる場合も、取扱説明書に反する吊り下げ方は避け、メーカー案内を優先しましょう。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.suisaku.com/product/air_pomp/122/",
            "title": "水作公式 水心シリーズ SSPP-3S",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/chanet/12666/",
            "title": "楽天市場 水作 水心 SSPP-3S個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/211165_10280753/1.1/",
            "title": "楽天市場 SSPP-3S個別投稿",
            "checked_at": "2026-10-06",
        }],
    },
    "hbf-214-w": {
        "official_url": "https://store.healthcare.omron.co.jp/support/download/catalog/pdf/hbf_series01.pdf",
        "facts": [
            "オムロン公式カタログで体重体組成計カラダスキャン HBF-214-W（ホワイト）を確認",
            "オムロン公式取扱説明書で販売名HBF-214 カラダスキャンと、体重・体脂肪率・BMI等の測定に関する案内を確認",
            "楽天市場の個別商品ページでHBF-214-Wの型番と商品同定を確認。医療上の診断や治療を目的とする機器として扱わない",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた表示項目と薄型設計への評価",
            "who": "楽天市場・価格.comのHBF-214-W個別投稿（2026-10-06確認）",
            "text": "個別投稿では、体重だけでなく体脂肪率やBMIなどを確認できる点、薄型でコンパクトな点を評価する声があります。一方で、測定値は使用条件や個人差の影響を受けるため、投稿者の評価をすべての利用者に一般化しません。健康状態の判断は医療専門家への相談を優先してください。",
            "negative": True,
            "fix_title": "設置場所と測定条件をそろえる",
            "fix": "硬く平らな床に設置し、取扱説明書の測定手順を確認してください。数値だけで健康状態を自己判断せず、気になる変化がある場合は医療機関へ相談しましょう。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://store.healthcare.omron.co.jp/support/download/catalog/pdf/hbf_series01.pdf",
            "title": "オムロン公式 HBFシリーズカタログ",
            "checked_at": "2026-10-06",
        }, {
            "type": "official_manual",
            "url": "https://store.healthcare.omron.co.jp/support/download/manual/pdf/5333221-2F_HBF-214.pdf",
            "title": "オムロン公式 HBF-214取扱説明書",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/rakuten24/e224959h/",
            "title": "楽天市場 HBF-214-W個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/item/1/261122_10759459/1.1/",
            "title": "楽天市場 HBF-214-W個別投稿",
            "checked_at": "2026-10-06",
        }],
    },
    "health-20261005": {
        "official_url": "https://brushmo.co.jp/collections/brush-head-refills",
        "facts": [
            "ブラシモ公式オンラインストアのソニッケアー向け替えブラシ商品群を確認",
            "ブラシモ公式Yahoo!商品ページで商品名『ダイヤモンドクリーン スタンダード 8本入 ブラシモ互換品』と商品コードSM6068-JPを確認",
            "販売ページでソニッケアー対応のスタンダードサイズ8本入として表示されることを確認。互換品であり、フィリップス純正品とは別商品として扱う",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた装着感と純正品との違い",
            "who": "ブラシモ公式Yahoo!ショッピング商品ページに表示された利用者の声（2026-10-06確認）",
            "text": "個別投稿では、ソニッケアー本体で問題なく使えた、消耗品として交換しやすいという声を確認できます。一方で、純正品との使い心地の違いを感じた、互換品によってはブラシ毛が抜けた経験があるという記述もあります。投稿者の本体・使用条件に基づく感想であり、すべての本体で同じ装着感や耐久性になるとは扱いません。",
            "negative": True,
            "fix_title": "本体型番と互換品であることを確認する",
            "fix": "使用中のソニッケアー本体のシリーズ名・型番を販売ページの対応表示と照合し、純正品ではなく互換品であることを理解したうえで購入してください。装着後はぐらつきや毛の抜けがないか確認しましょう。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://brushmo.co.jp/collections/brush-head-refills",
            "title": "BRUSHMO公式オンラインストア 替えブラシ一覧",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://store.shopping.yahoo.co.jp/sonimart/sm6068-jp.html",
            "title": "ブラシモ公式 Yahoo!ショッピング SM6068-JP個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://store.shopping.yahoo.co.jp/sonimart/sm6068-jp.html",
            "title": "ブラシモ公式Yahoo!商品ページの個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "web-200-cam021n": {
        "official_url": "https://direct.sanwa.co.jp/ItemPage/200-CAM021N",
        "facts": [
            "サンワダイレクト公式でカメラ三脚200-CAM021N、4段伸縮、耐荷重1.5kg、ミラーレス一眼・ビデオカメラ対応を確認",
            "公式商品ページと取扱説明書で、クイックシュー、一般的なUNC1/4インチねじ、専用収納ケースの説明を確認",
            "商品ページで伸縮範囲41〜125cmの表示を確認。機材重量と使用時の安定性は機材・設置面に依存するため保証しない",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた高さ調整と携帯性",
            "who": "サンワダイレクト公式商品ページとYahoo!商品ページに表示された利用者の声（2026-10-06確認）",
            "text": "個別投稿では、雲台の微調整や伸縮部の固定がしやすい、収納ケース付きで持ち運びやすいという声を確認できます。一方で、高さを変える部分が硬いという指摘や、雲台の取っ手の質感に不満を感じたという声もあります。個別の機材・設置環境での感想であり、すべての利用者に同じ操作感が出るとは扱いません。",
            "negative": True,
            "fix_title": "機材重量と設置面を確認してから使う",
            "fix": "カメラとレンズの合計重量が耐荷重内かを確認し、脚を伸ばした状態では平らで安定した場所に設置してください。固定部に緩みがないかを撮影前に確認しましょう。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://direct.sanwa.co.jp/ItemPage/200-CAM021N",
            "title": "サンワダイレクト公式 200-CAM021N 商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/sanwadirect/200-cam021n/",
            "title": "楽天市場 サンワダイレクト 200-CAM021N 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://direct.sanwa.co.jp/ItemReview/200-CAM021N",
            "title": "サンワダイレクト公式 200-CAM021N 利用者の声",
            "checked_at": "2026-10-06",
        }],
    },
    "200-dgbg008bk": {
        "official_url": "https://direct.sanwa.co.jp/ItemPage/200-DGBG008BK",
        "facts": [
            "サンワダイレクト公式でカメラバッグ200-DGBG008BK、品番200-DGBG008BKを確認",
            "公式商品ページで一眼カメラ本体と交換用レンズを収納でき、ショルダーベルトとベルトループに対応する商品説明を確認",
            "公式説明で間仕切りを使って収納レイアウトを調整できることを確認",
        ],
        "voices": [{
            "heading": "個別投稿で確認できたサイズ感と収納範囲",
            "who": "サンワダイレクト公式商品ページとYahoo!商品ページに表示された利用者の声（2026-10-06確認）",
            "text": "個別投稿では、散歩などの気軽な撮影に使いやすい大きさ、カメラとレンズの収納にちょうどよいサイズ感という声を確認できます。一方で、カメラ機材以外の収納はメッシュポケット程度に限られるという記述もあります。機材の大きさや持ち物によって使い勝手は変わるため、投稿者の感想をすべての組み合わせに一般化しません。",
            "negative": True,
            "fix_title": "機材と周辺品の寸法を先に照合する",
            "fix": "カメラ本体・レンズ・予備バッテリーなどの寸法を測り、公式商品ページの収納説明と照合してください。機材以外の荷物を多く入れる場合は別のバッグも用意しましょう。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://direct.sanwa.co.jp/ItemPage/200-DGBG008BK",
            "title": "サンワダイレクト公式 200-DGBG008BK 商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/sanwadirect/200-dgbg008bk/",
            "title": "楽天市場 サンワダイレクト 200-DGBG008BK 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://direct.sanwa.co.jp/ItemReview/200-DGBG008BK",
            "title": "サンワダイレクト公式 200-DGBG008BK 利用者の声",
            "checked_at": "2026-10-06",
        }],
    },
    "200-bg019": {
        "official_url": "https://direct.sanwa.co.jp/ItemPage/200-BG019LBK",
        "facts": [
            "サンワダイレクト公式で200-BG019シリーズのカメラインナーボックス（ソフトクッション・Lサイズ）を確認",
            "公式商品ページでカメラに合わせて仕切りを配置できる構造と、クッション材で機材を保護する商品説明を確認",
            "商品ページの型番表記はカラー・サイズで異なるため、購入時は200-BG019L／200-BG019LBKなど選択した型番を照合する",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた収納性と仕切りの使い勝手",
            "who": "サンワダイレクト公式商品ページに表示された利用者の声（2026-10-06確認）",
            "text": "個別投稿では、手持ちのバッグをカメラバッグとして使える、仕切りとクッション性で機材を守りやすい、仕切りの間隔をマジックテープで調整できるという声を確認できます。一方で、マジックテープの強度を心配する声や、機材の大きさによって収納感が変わるという注意もあります。投稿者の機材とバッグに基づく感想であり、すべての組み合わせに同じ結果が出るとは扱いません。",
            "negative": True,
            "fix_title": "内寸と機材の組み合わせを先に確認する",
            "fix": "カメラ本体・レンズ・付属品を実測し、公式ページの内寸と仕切り配置に収まるか確認してください。仕切りを固定した後は、持ち運び前に機材が動かないかを確かめましょう。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://direct.sanwa.co.jp/ItemPage/200-BG019LBK",
            "title": "サンワダイレクト公式 200-BG019LBK 商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/sanwadirect/200-bg019/",
            "title": "楽天市場 サンワダイレクト 200-BG019 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://direct.sanwa.co.jp/ItemReview/200-BG019L",
            "title": "サンワダイレクト公式 200-BG019L 利用者の声",
            "checked_at": "2026-10-06",
        }],
    },
    "anker-568-usbc-dock-review": {
        "official_url": "https://www.ankerjapan.com/products/a8399",
        "facts": [
            "Anker Japan公式でAnker 568 USB-Cドッキングステーション（11-in-1、USB4）、製品型番A83995A1を確認",
            "公式仕様でUSB4上流40Gbps、映像出力は1画面8K/30Hzまたは4K/60Hz、2画面最大4K/60Hz、3画面最大4K/30Hzを確認",
            "公式仕様でPC給電最大100W、USB-Cポート2つ使用時は最大65W、USB-A 3.2 Gen1×2とUSB-A 2.0×2を確認",
            "公式ページで180W ACアダプタ、USB4ケーブル、18か月保証（会員登録で6か月延長）、Dock Manager対応を確認",
        ],
        "voices": [{
            "heading": "実使用レビューで確認できたポート構成と互換条件",
            "who": "PCWorldおよびFramework Communityに掲載されたAnker 568実使用レビュー（2026-10-06確認）",
            "text": "実使用レビューでは、前面にUSB-C給電ポートと電源ボタンがあること、USB4ドックとして複数機器をまとめられることを確認できます。一方で、PC側のUSB4・Thunderbolt対応や映像出力条件によって結果が変わり、機器によっては画面出力やUSBハブの挙動を個別に確認する必要があります。レビューは特定のPC構成での結果であり、すべての環境で同じ動作を保証するものではありません。",
            "negative": True,
            "fix_title": "PC・モニター・ケーブルの規格を先に確認する",
            "fix": "購入前にPC側のUSB4／Thunderbolt対応、DisplayPort Alt Mode、モニターの解像度とリフレッシュレート、使用するケーブルの規格を照合してください。複数画面や高出力給電では公式の条件を優先しましょう。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.ankerjapan.com/products/a8399",
            "title": "Anker Japan公式 Anker 568 USB-Cドッキングステーション",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://www.pcworld.com/article/1922334/anker-568-usb-c-docking-station-review.html",
            "title": "PCWorld Anker 568実使用レビュー",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://community.frame.work/t/user-review-anker-568-framework-13-amd-intel-12th-gen/54256",
            "title": "Framework Community Anker 568利用者レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "iris-panel-light-ceiling-review": {
        "official_url": "https://www.irisohyama.co.jp/products/electrical-appliances/lighting-equipment/ceiling-light/light-guide-plate-series/light-guide-plate-toning-type/",
        "facts": [
            "アイリスオーヤマ公式のパネルライト（導光板）シリーズ 調光・調色タイプを確認",
            "公式説明で導光板の側面から入れたLED光を拡散反射させ、点光源のまぶしさを抑えやすい構造を確認",
            "公式説明で導光パネルにより天井面まで光が届き、薄型デザインで天井をすっきり見せる特徴を確認",
            "販売ページで確認対象のCEA-A08DLPは8畳用として表示される一方、型番ごとに適用畳数・全光束・消費電力・サイズが異なるため購入時に照合する",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた明るさと取り付け時の注意",
            "who": "Yahoo!ショッピングの商品ページに表示されたCEA-A08DLP個別投稿（2026-10-06確認）",
            "text": "個別投稿では、導光板で天井まで光が反射し、従来のLEDシーリングライトより明るく感じたという声、調光できてリビングでも使えたという声を確認できます。一方で、取り付け時にうまくはまらず手こずったという記述もあります。個別の部屋と取り付け条件での感想であり、すべての部屋で同じ明るさになるとは扱いません。",
            "negative": True,
            "fix_title": "畳数・天井器具・取り付け条件を照合する",
            "fix": "購入する型番の適用畳数と全光束を確認し、天井の引掛シーリングに対応するか、取り付けスペースを確保できるかを先に確認してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.irisohyama.co.jp/products/electrical-appliances/lighting-equipment/ceiling-light/light-guide-plate-series/light-guide-plate-toning-type/",
            "title": "アイリスオーヤマ公式 パネルライト導光板シリーズ",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://store.shopping.yahoo.co.jp/joylight/538005.html",
            "title": "Yahoo!ショッピング CEA-A08DLP 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://shopping.yahoo.co.jp/review/item/list?page_key=538005&store_id=insair-y",
            "title": "Yahoo!ショッピング CEA-A08DLP 個別投稿",
            "checked_at": "2026-10-06",
        }],
    },
    "benq-screenbar-review": {
        "official_url": "https://www.benq.com/ja-jp/lighting/monitor-light/screenbar/spec.html",
        "facts": [
            "BenQ公式仕様ページでScreenBar（無印）の製品名と仕様を確認",
            "公式仕様で中央照度930ルクス（照射面から45cm）、演色性Ra以上95、USB 5V／最大1A、最大消費電力5Wを確認",
            "公式仕様で本体サイズ45×9×9.2cm、重量約0.53kg、対応モニター厚1〜3cmを確認",
            "ScreenBar Proは別製品のため、Proの自動調光や仕様を無印の説明に混在させない",
        ],
        "voices": [{
            "heading": "実使用レビューで確認できた設置と照明範囲",
            "who": "Real Sound Techおよび個人使用レビューに掲載された実使用記録（2026-10-06確認）",
            "text": "実使用レビューでは、モニター上に置くだけで手元を照らせること、画面への反射を抑えやすいこと、デスク作業の照明として使いやすいという記録を確認できます。一方で、モニターの形状や設置環境によって使い勝手は変わり、レビューは特定の使用環境での結果です。",
            "negative": True,
            "fix_title": "モニターの厚みと上部スペースを先に測る",
            "fix": "購入前にモニター上部の厚みが1〜3cmの範囲か、背面側のクリップが干渉しないかを確認してください。USB給電できるポートの位置とケーブルの取り回しも見ておきましょう。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.benq.com/ja-jp/lighting/monitor-light/screenbar/spec.html",
            "title": "BenQ公式 ScreenBar 仕様",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/murauchi-dvd/4544438000455/",
            "title": "楽天市場 BenQ ScreenBar 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://realsound.jp/tech/2023/12/post-1503556.html",
            "title": "Real Sound Tech BenQ ScreenBar実使用レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "iris-kpc-ma4-pressure-cooker-review": {
        "official_url": "https://www.irisohyama.co.jp/e-pressure-cooker/4l/",
        "facts": [
            "アイリスプラザの商品ページで電気圧力鍋4.0L KPC-MA4、型番KPC-MA4、JAN 4967576470674を確認",
            "商品情報で満水容量4.0L、調理容量2.6L、最高圧力70kPa、自動メニュー80種類、消費電力1000Wを確認",
            "商品情報で圧力・温度・なべ・無水・蒸し・低温／発酵の手動調理、蒸しプレートとレシピブックの付属を確認",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた容量と手入れの注意",
            "who": "価格.comのKPC-MA4個別投稿およびアイリスプラザ商品ページに表示された利用者の声（2026-10-06確認）",
            "text": "個別投稿では、肉料理が柔らかく仕上がる、家族向けの容量を選んだという声を確認できます。一方で、4人家族では料理によって容量が足りないという指摘、ふたの掃除や電源が落ちたときのやり直しを負担に感じたという声、エラーや仕上がりへの不満もあります。投稿者の調理量・使い方に基づく感想であり、すべての家庭で同じ結果になるとは扱いません。",
            "negative": True,
            "fix_title": "調理量と手入れの手間を購入前に確認する",
            "fix": "家族人数だけでなく、作りたい料理の一度の分量が調理容量に収まるかを確認し、使用後にふたやパーツを洗う手間も考慮してください。圧力調理は取扱説明書の手順と安全表示に従いましょう。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.irisohyama.co.jp/e-pressure-cooker/4l/",
            "title": "アイリスオーヤマ公式 電気圧力鍋4Lシリーズ",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://www.irisplaza.co.jp/index.php?KB=SHOSAI&SID=H516394F",
            "title": "アイリスプラザ KPC-MA4 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.kakaku.com/review/K0001275735/",
            "title": "価格.com KPC-MA4 利用者レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "beauty-20260830": {
        "official_url": "https://creerina.co.jp/items/powderyliquideyebrow/",
        "facts": [
            "クレーリナ公式商品ページで、パウダリーリキッドアイブロウ ウルトラキープ、全4色、メーカー希望小売価格1,870円（税込）を確認",
            "公式説明でウォータープルーフ・スマッジプルーフ処方と、斜めカット平筆で太さを調整できる仕様を確認",
            "公式の使用方法として、容器を振り、筆の両面をしごいてから眉中央から眉尻へ描く手順を確認",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた仕上がりと描きやすさ",
            "who": "アットコスメの商品ページに表示された個別投稿（2026-10-06確認）",
            "text": "個別投稿では、リキッドなのにパウダーのようにふんわり仕上がる、斜めカットの平筆で眉尻まで描きやすいという声を確認できます。一方で、色の濃さや描きやすさは肌質・筆圧・使用色によって変わるという前提で扱います。投稿者の感想であり、すべての人に同じ仕上がりや持続性が出るとは限りません。",
            "negative": True,
            "fix_title": "色と筆圧を少量から確認する",
            "fix": "初回は手の甲などで色の濃さと液量を確認し、眉頭は薄く、眉尻は筆の角度を変えながら少量ずつ描いてください。肌に異常が出た場合は使用を中止しましょう。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://creerina.co.jp/items/powderyliquideyebrow/",
            "title": "クレーリナ公式 パウダリーリキッドアイブロウ ウルトラキープ",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/boundless/4901477090029/",
            "title": "楽天市場 クレーリナ個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://www.cosme.net/variations/1242045/",
            "title": "アットコスメ クレーリナ個別投稿",
            "checked_at": "2026-10-06",
        }],
    },
    "health-20261005-2": {
        "official_url": "https://brushmo.co.jp/collections/brush-head-refills",
        "facts": [
            "ブラシモ公式 Yahoo!ショッピング店の商品ページで、商品名『フィリップス ソニッケアー 替えブラシ 電動歯ブラシ 対応 ダイヤモンドクリーン ミニ8本入 ブラシモ 互換替えブラシ』と商品コードSM6078-JPを確認",
            "商品ページでダイヤモンドクリーン、ダイヤモンドクリーンスマート、イージークリーン、フレックスケアー、ヘルシーホワイト、ガムヘルス、アダプティブクリーン、プラチナシリーズ、プロテクトクリーン等への対応表示を確認",
            "商品ページでミニサイズの替えブラシ8本入、DuPont素材の表示を確認。仕様・パッケージは変更される場合があるため購入時の表示を優先する",
            "ブラシモ公式オンラインストアの替えブラシ一覧で、ソニッケアー向けブラシヘッドの商品群を確認。SM6078-JPの個別仕様は公式Yahoo!商品ページで照合する",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた装着感とサイズの違い",
            "who": "ブラシモ公式Yahoo!商品ページに表示された利用者の声（2026-10-06確認）",
            "text": "個別投稿では、ソニッケアー本体に装着して問題なく使えた、ミニサイズが本人や子どもに合ったという声を確認できます。一方で、純正品よりやや柔らかい・幅広く感じたという個人の感想、旧購入品で接続部が外れたことがあるという指摘、耐久性はまだ判断できないという声もあります。投稿者の使用条件に基づく感想であり、すべての本体や口腔状態に同じ結果が出るとは扱いません。",
            "negative": True,
            "fix_title": "本体型番とブラシサイズを購入前に照合する",
            "fix": "使用中のソニッケアー本体のシリーズ名・型番を対応表と照合し、ミニサイズの大きさが自分や子どもの口に合うかを確認してください。装着後は接続部にぐらつきがないかを確かめ、違和感があれば使用を中止しましょう。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://brushmo.co.jp/collections/brush-head-refills",
            "title": "BRUSHMO公式オンラインストア 替えブラシ一覧",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://store.shopping.yahoo.co.jp/sonimart/sm6078-jp.html",
            "title": "ブラシモ公式 Yahoo!ショッピング店 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://store.shopping.yahoo.co.jp/sonimart/sm6078-jp.html",
            "title": "ブラシモ公式 Yahoo!商品ページに表示された個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "petkit-pura-max2": {
        "official_url": "https://www.petkit.com/products/puramax-2-ultimate-bundles",
        "facts": [
            "PETKIT公式商品ページでPuraMax 2の自動清掃、Xsecure安全センサー、アプリでの利用状況管理、消臭機能を確認",
            "PETKIT公式の製品情報でPuraMax 2に2種類のリッターシフターが付属することを確認",
            "楽天市場のPETKIT公式ストア個別商品ページで商品コードP9902、Pura Max2本体、個別販売条件を確認",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた猫の慣れと設置条件",
            "who": "楽天市場PETKIT公式ストアの商品ページに表示された利用者の声（2026-10-06確認）",
            "text": "個別投稿では、2匹の猫のうち警戒心の強い猫も数日後に使えたという声、消臭や掃除の負担が軽くなったという声を確認できます。一方で、予想より本体が大きいという指摘や、猫が慣れるまで時間がかかる可能性も確認できます。個別投稿の内容であり、すべての猫・住環境に同じ結果が出るとは扱いません。",
            "negative": True,
            "fix_title": "本体寸法と猫の慣らし期間を先に考える",
            "fix": "設置場所の寸法を測り、現在のトイレをすぐ撤去せず、猫が新しいトイレに慣れるまで併設できるスペースを確保してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.petkit.com/products/puramax-2-ultimate-bundles",
            "title": "PETKIT公式 PuraMax 2 商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/neikonu/pkt-p9902/",
            "title": "楽天市場 PETKIT公式ストア Pura Max2 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/435566_10000015/1.1/",
            "title": "楽天市場 利用者の声 Pura Max2",
            "checked_at": "2026-10-06",
        }],
    },
    "camera-20260830": {
        "amazon_url": "https://www.amazon.co.jp/dp/B0FM76RYRP",
        "source_notes": [{
            "type": "product_page",
            "url": "https://www.amazon.co.jp/dp/B0FM76RYRP",
            "title": "Amazon 個別商品ページ クレーリナ エアリーカールマスカラ",
            "checked_at": "2026-10-06",
        }],
    },
    "redmi-watch-5-review": {
        "amazon_url": "https://www.amazon.co.jp/dp/B0DPX91VHZ",
        "source_notes": [{
            "type": "product_page",
            "url": "https://www.amazon.co.jp/dp/B0DPX91VHZ",
            "title": "Amazon 個別商品ページ Xiaomi REDMI Watch 5",
            "checked_at": "2026-10-06",
        }],
    },
    "speakerphone-conference-review": {
        "official_url": "https://www.ankerjapan.com/products/a3307",
        "amazon_url": "https://www.amazon.co.jp/dp/B09N6F7TPG",
        "facts": [
            "Anker公式商品ページでPowerConf S360、型番A3307041を確認",
            "公式仕様でUSB-C有線接続、Bluetooth非対応、内蔵バッテリーなしを確認",
            "公式仕様で本体サイズ約120×120×35mm、重量約250g、スピーカー出力3Wを確認",
            "公式説明でエコーキャンセリング、残響抑制、ノイズリダクション、製品から3m以内の使用推奨を確認",
        ],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.ankerjapan.com/products/a3307",
            "title": "Anker Japan PowerConf S360 公式商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://www.amazon.co.jp/dp/B09N6F7TPG",
            "title": "Amazon 個別商品ページ ASIN B09N6F7TPG",
            "checked_at": "2026-10-06",
        }],
    },
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
            "fix": "初回は電源音を聞かせて反応を確認し、アタッチメントがしっかりはまっているかを試運転で確認してから使用してください。",
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
