#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""確認済みの一次ページ情報を記事へ追加する小さな編集用ツール。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE = {
    "fargo-sati-color-ac4-usb-ct221gy": {
        "official_url": "https://fargo.co.jp/",
        "facts": [
            "Fargo公式サイトで電源タップをデザイン・使い勝手まで含めて開発するブランド情報を確認",
            "Fargo Direct Shopの公式商品カテゴリでSATI COLORのAC4個口・USB Type-A 2ポート構成を確認",
            "個別商品ページでFargo SATI COLOR CT221GY（ライトグレー）のAC4個口、USB 2ポート合計4.2A、スマートフォンスタンド、雷サージガードの構成を確認",
            "利用者のレビューでは、AC4口とUSB2口、スマートフォン置き台の便利さを評価する一方、大きなACアダプターを挿すと隣の口や安定性に影響するという指摘があるため、接続機器の形状を確認する",
        ],
        "review_texts": [{
            "source": "価格.com・個別使用レビュー Fargo SATI COLOR CT221",
            "text": "個別使用レビューでは、USBポート2口とAC4口を一体で使える点、スマートフォン置き台を兼ねる点が評価されています。一方で、大きなACアダプターを挿すと隣の口や本体の安定性に影響するという指摘があります。接続する機器の大きさ・向きと壁コンセントの位置による使用感として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://fargo.co.jp/",
            "title": "Fargo公式サイト",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://payid.jp/item/155856196",
            "title": "Fargo SATI COLOR CT221GY 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.kakaku.com/review/K0001582631/",
            "title": "価格.com Fargo SATI COLOR CT221 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "pc-microsoft-surface-8gb-ssd256gb-core-i5": {
        "official_url": "https://support.microsoft.com/en-us/surface/models/surface-pro-5th-gen-specs-and-features",
        "facts": [
            "Microsoft公式サポートでSurface Pro（第5世代）のモデル番号1796（Wi-Fi）、12.3インチPixelSenseディスプレイ、第7世代Core m3/i5/i7、メモリ4/8/16GB、SSD容量の選択肢を確認",
            "公式仕様でUSB 3.0、microSDXC、Mini DisplayPort、Bluetooth 4.1、重量などの世代共通情報を確認し、中古個体の構成とは分けて扱う",
            "楽天市場の個別商品ページでSurface Pro 5、Core i5、8GB、SSD256GB、Windows 11の中古構成を確認",
            "個別投稿では中古でも外観・起動・ソフトの立ち上がり・バッテリーに問題がなかったという声がある一方、メモリ容量やタブレット形状の必要性を購入前に考える内容もあるため、個体差と用途を分けて確認する",
        ],
        "review_texts": [{
            "source": "楽天市場 Surface Pro 5 中古個別レビュー",
            "text": "個別投稿では、中古品でもきれいで起動やソフトの立ち上がりが速く、バッテリーも問題なかったという内容が確認できます。一方で、より高い処理性能や大画面が必要なら別のノートPCを検討したほうがよいという声もあります。中古品は同じ型名でも状態・構成・付属品が異なるため、販売ページの個体説明を優先します。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://support.microsoft.com/en-us/surface/models/surface-pro-5th-gen-specs-and-features",
            "title": "Microsoft公式 Surface Pro（第5世代）仕様",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/pc-eco2000/microsoft02/",
            "title": "楽天市場 Surface Pro 5 中古個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/304287_10005963/1.1/",
            "title": "楽天市場 Surface Pro 5 中古個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "00-9-clinique": {
        "official_url": "https://www.clinique.jp/product/1606/7079/makeup/mascara/lash-power-curling-mascara-long-wearing-formula",
        "facts": [
            "クリニーク公式オンラインショップでラッシュ パワー カーリング マスカラを商品同定",
            "公式商品ページで小さく緩やかなカーブの三日月型ブラシ、水・汗・涙や高湿度に負けにくいロングウェアリング フォーミュラ、ぬるま湯でオフという案内を確認",
            "楽天市場のクリニーク公式ショップでラッシュ パワー カーリング マスカラの個別商品ページを確認",
            "個別投稿では長年使っている、お湯で落としやすい、にじみにくいという声がある一方、仕上がりや目元への相性には個人差があるため、公式の商品特長と利用者の感想を分けて扱う",
        ],
        "review_texts": [{
            "source": "楽天市場 クリニーク公式ショップ 個別レビュー",
            "text": "個別投稿では、長年リピートしている、お湯で落としやすい、にじみにくいという内容が確認できます。別の投稿では、ブラシの形状が塗りやすく長さが出るという感想もあります。仕上がりや使いやすさは目元の状態・塗り方による個人の感想として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.clinique.jp/product/1606/7079/makeup/mascara/lash-power-curling-mascara-long-wearing-formula",
            "title": "クリニーク公式 ラッシュ パワー カーリング マスカラ",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/clinique/7079/",
            "title": "楽天市場 クリニーク公式 ラッシュ パワー カーリング マスカラ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/313026_10000018/1.1/",
            "title": "楽天市場 クリニーク公式 カーリングマスカラ 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "agptek-type-c-dslr-iphone-ipad-android": {
        "official_url": "https://images.agptek.us/Download/User_Manual/AC02B_User_Manual%28Quick_Start_in_Japanese%29.pdf.pdf",
        "facts": [
            "AGPTEK公式配布のAC02Bクリップマイク取扱説明書で3.5mmミニプラグ（CTIA標準）と付属アダプターの案内を確認",
            "公式説明書でApple・Android・カメラなど接続先によって付属アダプターを使い分ける案内を確認",
            "楽天市場の個別商品ページでAGPTEKピンマイク、3.5mmプラグ、Type-Cケーブル、4段アダプター付属の構成を確認",
            "個別投稿では問題なく使えた、安価で実用的という声がある一方、接続先やアプリによって認識方法が変わる内容もあるため、端末の端子・規格・アプリ条件を確認する",
        ],
        "review_texts": [{
            "source": "楽天市場 AGPTEKピンマイク 個別レビュー",
            "text": "個別投稿では、問題なく使用できた、価格を考えると実用的という内容が確認できます。一方で、イヤホン端子で使うためにアプリを入れたという投稿もあり、端末やアプリによって接続条件が変わる可能性があります。公式説明書の端子・アダプター案内を優先して確認します。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://images.agptek.us/Download/User_Manual/AC02B_User_Manual%28Quick_Start_in_Japanese%29.pdf.pdf",
            "title": "AGPTEK公式 AC02Bクリップマイク取扱説明書",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/goodgoodsshop/ac02bc/",
            "title": "楽天市場 AGPTEKピンマイク 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/357302_10000228/1.1/",
            "title": "楽天市場 AGPTEKピンマイク 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "zero-windows-dl-snr-windows": {
        "official_url": "https://www.sourcenext.com/product/security/zero-super-security/",
        "facts": [
            "ソースネクスト公式製品ページでZERO スーパーセキュリティを商品同定",
            "公式案内で1台用の期限なしライセンス、対応OS、製品の位置づけを確認。Windows 10の継続利用には注意が必要との案内も確認",
            "楽天市場のソースネクスト公式ショップでWindows専用版1台用の個別商品ページを確認",
            "個別投稿では更新料不要や動作の軽さを評価する声がある一方、セキュリティソフトの効果は通常利用だけでは判断しにくいという声もあり、機能・更新条件・OS対応を中心に確認する",
        ],
        "review_texts": [{
            "source": "ビックカメラ ZERO スーパーセキュリティ Windows専用版 個別レビュー",
            "text": "個別投稿では、インストール後にパソコンが重くなった印象はないという内容や、更新料金が不要な点を評価する内容が確認できます。一方で、セキュリティ効果は普段の使用だけでは評価しにくいという声もあります。公式の対応OS・ライセンス条件と、個人の使用感を分けて判断します。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.sourcenext.com/product/security/zero-super-security/",
            "title": "ソースネクスト公式 ZERO スーパーセキュリティ",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/pocketalk/0000317880/",
            "title": "楽天市場 ソースネクスト公式 ZERO スーパーセキュリティ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://www.biccamera.com/bc/disp/SfrGoodsPageReview.jsp?GOODS_NO=10876614",
            "title": "ビックカメラ ZERO スーパーセキュリティ 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "ath-sr30bt-gy-bluetooth-ath": {
        "official_url": "https://www.audio-technica.co.jp/product/ATH-SR30BT",
        "facts": [
            "オーディオテクニカ公式製品ページでATH-SR30BTを商品同定",
            "公式仕様でBluetooth 5.0、最大約70時間再生、φ40mmドライバー、約190g、AAC/SBC対応、ATH-SR30BT GYの型番とJANを確認",
            "楽天市場の個別商品ページでATH-SR30BT GYの販売情報を確認",
            "個別投稿では普段使いの音質やデザインを評価する声がある一方、長時間装着時の圧迫感や蒸れに触れる声もあるため、装着感は頭部形状・使用時間・環境による個人差として扱う",
        ],
        "review_texts": [{
            "source": "Yahoo!ショッピング ATH-SR30BT 個別レビュー",
            "text": "個別投稿では、普段使いには問題ないという内容がある一方、1時間程度の装着で圧迫感がある、運動時は蒸れやすいという指摘も確認できます。音質や装着感は個人差が大きいため、最大70時間という公式仕様と、長時間使用時の体験談を分けて判断します。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.audio-technica.co.jp/product/ATH-SR30BT",
            "title": "オーディオテクニカ公式 ATH-SR30BT",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://biccamera.rakuten.co.jp/item/4961310146818",
            "title": "楽天ビック ATH-SR30BT GY 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://shopping.yahoo.co.jp/products/p/51e4b769fc/review/",
            "title": "Yahoo!ショッピング ATH-SR30BT 利用者の声",
            "checked_at": "2026-10-06",
        }],
    },
    "a75c4419-panasonic-d2613": {
        "official_url": "https://panasonic.jp/manualdl/p-db/cs/cs_634_804_x.pdf",
        "facts": [
            "パナソニック公式エアコン取扱説明書で、対応機種の付属リモコン品番CWA75C4418Xを確認",
            "公式資料でCWA75C4418Xとリモコン記載品番A75C4419の対応関係を商品同定の根拠として確認",
            "楽天市場の個別商品ページでA75C4419表記のCWA75C4418X純正交換用リモコンを確認",
            "個別投稿では、故障・液晶不良の交換用として購入し、電池を入れて使えたという内容がある一方、対応機種の照合が必要な交換部品であり、すべてのパナソニック製エアコンに使えるとは扱わない",
        ],
        "review_texts": [{
            "source": "楽天市場 A75C4419/CWA75C4418X 個別商品ページ・利用者の声",
            "text": "個別の利用者の声では、既存リモコンの故障や液晶不良をきっかけに交換用として購入し、電池を入れて問題なく使えたという内容が確認できます。ただし、交換部品はエアコン本体の対応機種との照合が前提で、同じメーカーでも型番が違えば操作できるとは限りません。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://panasonic.jp/manualdl/p-db/cs/cs_634_804_x.pdf",
            "title": "パナソニック公式 ルームエアコン取扱説明書",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/2cube02/pn1a75c4419/",
            "title": "楽天市場 A75C4419 CWA75C4418X 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/355518_10001231/1.1/",
            "title": "楽天市場 パナソニック対応リモコン 利用者の声",
            "checked_at": "2026-10-06",
        }],
    },
    "wsj-4l": {
        "official_url": "https://www.irisplaza.co.jp/index.php?KB=SHOSAI&SID=110884F",
        "facts": [
            "アイリスオーヤマ公式通販アイリスプラザで速効除草剤4L WSJ-4Lを商品同定",
            "公式商品ページで4Lのストレートタイプ除草剤としての販売情報と、非農耕地用としての案内を確認",
            "楽天市場の個別商品ページでWSJ-4Lの4L単品商品を確認",
            "個別投稿では数日後に枯れ始めた、容器のジョウロ状の口が撒きやすいという声がある一方、散布時の天候や周囲の植物への飛散に注意する内容もあるため、使用場所とラベル表示を優先する",
        ],
        "review_texts": [{
            "source": "楽天市場 WSJ-4L 個別レビュー",
            "text": "個別投稿では、散布後数日で雑草が枯れ始めた、4L容器でも扱いやすい、ジョウロ状の口で撒きやすいという内容が確認できます。一方で、雨の予報を避ける、周囲の花や植木にかからないようにするという注意もあります。効果や扱いやすさは散布条件と場所による体験談として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.irisplaza.co.jp/index.php?KB=SHOSAI&SID=110884F",
            "title": "アイリスオーヤマ公式通販 WSJ-4L",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/kadenrand/514489/",
            "title": "楽天市場 WSJ-4L 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/item/1/253767_10029218/1.1/",
            "title": "楽天市場 WSJ-4L 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "sony-cmt-m35wm-usb-cd-hcd-m35wm-ss": {
        "official_url": "https://www.sony.jp/system-stereo/products/archive/CMT-M35WM/spec.html",
        "facts": [
            "ソニー公式仕様ページでCMT-M35WMを商品同定",
            "公式仕様でCD、MD、カセット、FM/AM、ウォークマン専用USB端子、外部入力、スリープタイマーなどの対応を確認",
            "ソニー公式サポートでCMT-M35WM（HCD-M35WM、RM-SM35、SS-CM35）の取扱説明書とQ&Aを確認",
            "価格.comの個別レビューでは、CD・MD・カセット・外部入力を一体で使える点や、Bluetooth非対応、リモコン依存の操作、音量・音質の印象に触れる内容があるため、年代と用途を分けて判断する",
        ],
        "review_texts": [{
            "source": "価格.com CMT-M35WM 個別レビュー",
            "text": "個別レビューでは、CD・MD・カセット・外部入力を一体で使えること、コンパクトなサイズを評価する内容が確認できます。一方で、Bluetooth非対応、リモコンが必要な操作、音量や音質は設置環境と期待値によって印象が変わるという指摘もあります。中古品では付属品・動作状態・消耗部品の確認が必要です。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.sony.jp/system-stereo/products/archive/CMT-M35WM/spec.html",
            "title": "ソニー公式 CMT-M35WM 主な仕様",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/skymarketplus/yb00mo3wxgk/",
            "title": "楽天市場 CMT-M35WM 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.kakaku.com/review/20707010368/",
            "title": "価格.com CMT-M35WM レビュー・評価",
            "checked_at": "2026-10-06",
        }],
    },
    "valx": {
        "official_url": "https://corp.valx.jp/services/valx/",
        "facts": [
            "VALX公式ページでVALXホエイプロテインのブランド・製品情報を確認",
            "公式発表でホエイプロテイン1kgの製品展開と国内生産・フレーバー展開の案内を確認",
            "ふるさとチョイスの個別返礼品ページでVALXホエイプロテイン1kgカフェオレ風味を商品同定",
            "個別投稿では味や飲み方に触れる内容があるが、体質・摂取目的・飲み方による個人差があり、健康効果を一般化しない",
        ],
        "review_texts": [{
            "source": "ふるさとチョイス VALXホエイプロテイン個別感想",
            "text": "個別の感想では、カフェオレ風味を牛乳とシェーカーで飲み、ミルクシェークのように楽しめたという内容が確認できます。味や飲み方に関する個人の感想であり、すべての人の嗜好や体調に同じ結果が出るとは扱いません。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://corp.valx.jp/services/valx/",
            "title": "VALX公式ブランド情報",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://www.furusato-tax.jp/product/detail/35201/6027503",
            "title": "ふるさとチョイス VALXホエイプロテイン1kg",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://www.furusato-tax.jp/product/reviews/35201/6027503",
            "title": "ふるさとチョイス VALXホエイプロテイン感想",
            "checked_at": "2026-10-06",
        }],
    },
    "iaw-t606-cp": {
        "official_url": "https://www.irisohyama.co.jp/products/manual/pdf/108963.pdf",
        "facts": [
            "アイリスオーヤマ公式取扱説明書で全自動電気洗濯機 IAW-T606を商品同定",
            "公式資料で室内・家庭用の型番IAW-T606として、設置・給水・使用上の注意を確認",
            "アイリスオーヤマ公式楽天市場店の個別商品ページで6kg縦型洗濯機、2年保証の案内を確認",
            "個別投稿では静音性や操作の簡単さを評価する声がある一方、初期不良・設置条件・洗濯時間に触れる内容もあるため、設置環境と保証条件を確認する",
        ],
        "review_texts": [{
            "source": "楽天市場 IAW-T606個別レビュー",
            "text": "個別投稿では、音が静か、操作が簡単、コンパクトで使いやすいという内容が確認できます。一方で、初期不良や設置場所による保証条件、洗濯時間に関する指摘もあります。住環境・設置条件・個体差による体験談として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.irisohyama.co.jp/products/manual/pdf/108963.pdf",
            "title": "アイリスオーヤマ公式 IAW-T606取扱説明書",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/irisplaza-r/108963/",
            "title": "楽天市場 アイリスオーヤマ公式 IAW-T606",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/358201_10160922/1.1/",
            "title": "楽天市場 IAW-T606 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "h70ft-h70ft-h70ft-bac06wh": {
        "official_url": "https://huromjapan.com/product/h70ft.html",
        "product_url": "https://item.rakuten.co.jp/pika831/10005259/",
        "thumb": "https://huromjapan.com/common/images/product/h400/hero_product_h70ft.jpg",
        "facts": [
            "HUROM公式ではH70FTを材料をまとめて投入できるスロージューサーとして案内している",
            "公式商品情報ではジュースとフローズンに対応するマルチスクリュー、1.8Lのメガホッパー、食洗機使用条件を案内している",
            "公式では野菜・果物・凍った食材をフィルター交換なしで扱えるオールインワン仕様として案内している",
            "楽天市場の個別レビューでは、H70FT-BAC06WHの使用感や手入れについての利用者の声を確認できる"
        ],
        "review_texts": [{
            "source": "楽天市場 HUROM H70FT 個別レビュー",
            "text": "楽天市場の個別投稿では、H70FT-BAC06WHの使用感や手入れについての利用者の声が確認できます。個人の感想として扱い、健康上の効果は断定しません。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://huromjapan.com/product/h70ft.html",
            "title": "HUROM公式 H70FT 商品情報",
            "checked_at": "2026-10-07",
        }, {
            "type": "official_manual",
            "url": "https://huromjapan.com/support/manual_pdf/manual_H70FT.pdf",
            "title": "HUROM公式 H70FT 取扱説明書",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/pika831/10005259/",
            "title": "楽天市場 H70FT-BAC06WH 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/201791_10005259/1.1/",
            "title": "楽天市場 H70FT 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "fotopro-digi-204": {
        "official_url": "https://www.asanumashoukai.co.jp/info/wp-content/uploads/2022/08/asanuma_price_revision20221001.pdf",
        "product_url": "https://item.rakuten.co.jp/photolink/4906238806024/",
        "thumb": "https://thumbnail.image.rakuten.co.jp/@0_mall/photolink/cabinet/fotopro/4906238810830_nnv11.jpg?_ex=128x128",
        "facts": [
            "商品資料ではFotopro DIGI-204を4段120cmのアルミ製三脚として掲載している",
            "価格.comの個別レビューでは、軽くて持ち運びやすい、カメラを載せても安定するという声がある一方、雲台の動きが今ひとつという声もある",
            "楽天市場の個別投稿では、しっかりした作りで持ち運びやすいという声や、固定操作に複数回の回転が必要という声が確認できる"
        ],
        "review_texts": [{
            "source": "価格.com・楽天市場 Fotopro DIGI-204 個別レビュー",
            "text": "軽くて小さく持ち運びやすい、カメラを載せても安定するという声がある一方、雲台の動きや固定操作を気にする声もあります。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.asanumashoukai.co.jp/info/wp-content/uploads/2022/08/asanuma_price_revision20221001.pdf",
            "title": "Asanuma公式資料 Fotopro DIGI-204",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/photolink/4906238806024/",
            "title": "楽天市場 Fotopro DIGI-204 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://review.kakaku.com/review/K0000897755/",
            "title": "価格.com Fotopro DIGI-204 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "w-r-1200-w-r1200": {
        "official_url": "https://www.morieng.co.jp/machine/product/window/wr/index.php",
        "product_url": "https://item.rakuten.co.jp/kamekenken/wat2410/",
        "thumb": "https://thumbnail.image.rakuten.co.jp/@0_mall/kamekenken/cabinet/_wat04/wat2410a.jpg?_ex=128x128",
        "facts": [
            "森永エンジニアリング公式ではウインドーラジエーターW/Rシリーズを窓際に置いて冷気の侵入を防ぐ製品として案内している",
            "公式コラムではW/R-1200Wを窓下専用ヒーターとして説明し、設置場所とサイズ確認が重要と案内している",
            "公式コラムではW/Rシリーズについて、見た目がすっきりしている、窓際の冷気対策になったという利用者の声を紹介している"
        ],
        "review_texts": [{
            "source": "森永エンジニアリング公式 W/Rシリーズ利用者の声",
            "text": "公式コラムでは、見た目がすっきりして部屋の雰囲気を損なわない、窓際からの冷気対策になったという利用者の声が紹介されています。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.morieng.co.jp/machine/product/window/wr/index.php",
            "title": "森永エンジニアリング公式 W/Rシリーズ商品情報",
            "checked_at": "2026-10-07",
        }, {
            "type": "official_review",
            "url": "https://www.morieng.co.jp/column/archives/352",
            "title": "森永エンジニアリング公式 利用者の声",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/kamekenken/wat2410/",
            "title": "楽天市場 W/R-1200 個別商品ページ",
            "checked_at": "2026-10-07",
        }],
    },
    "winten-fhd-ips-pc-switch-iphone": {
        "official_url": "https://winten.co.jp/products.html",
        "product_url": "https://item.rakuten.co.jp/win10/5523/",
        "thumb": "https://thumbnail.image.rakuten.co.jp/@0_mall/win10/cabinet/monitor/imgrc0112809238.jpg?_ex=128x128",
        "facts": [
            "WINTEN公式ではWT-156H2-BSを15.6インチのフルHDモバイルモニターとして製品一覧に掲載している",
            "公式のお知らせでは設定保存機能のオン・オフとL型USB-Cケーブル追加をWT-156H2-BSの改良点として案内している",
            "楽天市場の個別レビューでは、持ち運び用のモニターとして希望通りだったという声が確認できる"
        ],
        "review_texts": [{
            "source": "楽天市場 WINTEN WT-156H2-BS 個別レビュー",
            "text": "個別投稿では、仕事用に持ち歩けるモニターを求めて購入し、希望通りだったという声があります。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://winten.co.jp/products.html",
            "title": "WINTEN公式 WT-156H2-BS 製品情報",
            "checked_at": "2026-10-07",
        }, {
            "type": "official_notice",
            "url": "https://winten.co.jp/news/view/191",
            "title": "WINTEN公式 WT-156H2-BS 改良案内",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/win10/5523/",
            "title": "楽天市場 WT-156H2-BS 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/240353_10009635/1.0/",
            "title": "楽天市場 WT-156H2-BS 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "mrpe-1260-soho-yamazen": {
        "official_url": "https://book.yamazen.co.jp/product/detail/I00008450",
        "facts": [
            "山善公式商品情報サイトでMRPE-1260ラック付デスクを商品同定",
            "山善公式マニュアルで天板耐荷重60kg、棚板20kg（1枚当たり）、付属コンセント合計1500Wまでの案内を確認",
            "楽天市場の個別商品ページで幅120・奥行60、2口コンセント、左右入れ替え可能な収納ラック付きデスクを確認",
            "個別投稿では組み立てやすさ、安定性、色味、天板の凹凸に触れる内容があるため、設置場所と用途に応じて確認する",
        ],
        "review_texts": [{
            "source": "楽天市場・山善公式レビューのMRPE-1260個別投稿",
            "text": "個別投稿では、1人で組み立てやすい、完成後にぐらつきがない、棚が便利という内容が確認できます。一方で、色味や天板の凹凸に触れる投稿もあります。組み立て環境・照明・用途による個人差として扱い、すべての設置で同じ印象になるとは一般化しません。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://book.yamazen.co.jp/product/detail/I00008450",
            "title": "山善公式 MRPE-1260 商品情報",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/e-kurashi/1450620/",
            "title": "楽天市場 山善 MRPE-1260 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://yamazenbizcom.jp/item_review.html?ITEM_CD=1450620",
            "title": "山善公式 MRPE-1260 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "pet-20260927": {
        "official_url": "https://page.mkgr.jp/product/8592/",
        "facts": [
            "マルカン公式製品ページでNewスティングレーNS106を商品同定",
            "公式仕様で本体サイズ約W600×D300×H360mm、容量56L、重量約7.3kg、曲げガラス、品番NWN-001、JAN4975637214563を確認",
            "楽天市場の個別商品ページでニッソー60cm水槽 NEWスティングレー NS-106を確認",
            "個別投稿ではフレーム付きの扱いやすさ、曲げガラスの見た目、外付けフィルターの適合に関する内容があるため、設置機器との寸法照合が必要",
        ],
        "review_texts": [{
            "source": "楽天市場 NS-106個別レビュー",
            "text": "個別投稿では、同型水槽の買い替え理由としてフレーム付きの扱いやすさを挙げる内容や、曲げガラスの見た目を評価する内容が確認できます。一方で、フレームの厚みにより外付けフィルターの選択肢が限られるという指摘もあります。設置機器と個体差による感想として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://page.mkgr.jp/product/8592/",
            "title": "マルカン公式 NewスティングレーNS106",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/chanet3980/12297/",
            "title": "楽天市場 ニッソー NS-106 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/item/1/211165_10007045/1.1/",
            "title": "楽天市場 ニッソー NS-106 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "switchbot-alexa": {
        "official_url": "https://www.switchbot.jp/collections/all/products/switchbot-hub3",
        "facts": [
            "SwitchBot公式ページでSwitchBot ハブ3を商品同定",
            "公式案内で赤外線リモコン、2.4インチモニター、温湿度計・光センサー、Matter対応に関する製品情報を確認",
            "楽天市場のSwitchBot公式店個別商品ページでハブ3と商品レビューを確認",
            "個別投稿では操作の便利さを評価する声がある一方、機器登録やコネクタ接続に関する注意も確認できるため、利用機器との互換性を先に確認する",
        ],
        "review_texts": [{
            "source": "楽天市場 SwitchBot公式店 ハブ3個別レビュー",
            "text": "個別投稿では、家電操作が楽になった、便利で使いやすいという内容が確認できます。一方で、登録方法や他社Bluetooth機器の操作範囲に関する注意もあります。接続する機器・アプリ・ネットワーク環境による差を分けて扱い、すべての環境で同じ操作性になるとは一般化しません。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.switchbot.jp/collections/all/products/switchbot-hub3",
            "title": "SwitchBot公式 ハブ3",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/switchbot/hub3/",
            "title": "楽天市場 SwitchBot公式店 ハブ3",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/415408_10000265/1.1/",
            "title": "楽天市場 SwitchBot ハブ3 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "jackery-jackery-solarsaga-ip65-jackery": {
        "official_url": "https://www.jackery.jp/collections/solar-panel/products/jackery-solarsaga-100",
        "facts": [
            "Jackery Japan公式ページでSolarSaga 100Wソーラーパネルを商品同定",
            "公式仕様で最大100W、変換効率25%、IP68防水、ETFE採用、5年保証の案内を確認",
            "楽天市場のJackery Japan公式店個別商品ページでSolarSaga 100の商品を確認",
            "楽天市場の個別投稿では発電・充電や買い替えに触れる内容があるが、天候・設置条件・接続する電源で結果が変わるため一般化しない",
        ],
        "review_texts": [{
            "source": "楽天市場 Jackery Japan公式店個別レビュー",
            "text": "個別投稿では、天候が悪い期間を経て発電できたことや、以前のパネルから買い替えて充電しやすくなったという内容が確認できます。日射条件・設置角度・接続機器による体験談として扱い、常に同じ出力になるとは一般化しません。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.jackery.jp/collections/solar-panel/products/jackery-solarsaga-100",
            "title": "Jackery Japan公式 SolarSaga 100W",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/jackery-japan/n-s-100-jkss1/",
            "title": "楽天市場 Jackery Japan公式 SolarSaga 100",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/item/1/374756_10000009/1.1/",
            "title": "楽天市場 Jackery SolarSaga 100 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "tv-ipx8": {
        "official_url": "https://extage.jp/brand/clear-elec-brush-001/",
        "facts": [
            "Extage公式ページでCLEARLABO ELECTRIC TOOTHBRUSHを商品同定",
            "公式案内でIPX8防水設計、2分後の自動停止、歯科医師監修の製品として確認",
            "Yahoo!ショッピングの個別商品ページでCLEARLABO電動歯ブラシとIPX8・替えブラシ付きの表示を確認",
            "個別投稿では持ちやすさ、磨きやすさ、モード切替に触れる内容があるが、口腔状態や使用方法による個人差を分けて扱う",
        ],
        "review_texts": [{
            "source": "Yahoo!ショッピング CLEARLABO個別レビュー",
            "text": "個別投稿では、奥側や歯間を磨きやすい、持ちやすい、モード切替に実用性を感じるという内容が確認できます。投稿者の使用方法や口腔状態に基づく感想であり、すべての利用者に同じ清掃感や使いやすさが得られるとは一般化しません。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://extage.jp/brand/clear-elec-brush-001/",
            "title": "Extage公式 CLEARLABO電動歯ブラシ",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://store.shopping.yahoo.co.jp/excitech/clear-elec-brush-001.html",
            "title": "Yahoo! CLEARLABO電動歯ブラシ 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://store.shopping.yahoo.co.jp/excitech/clear-elec-brush-001/",
            "title": "Yahoo! CLEARLABO電動歯ブラシ 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "furniture-20261006": {
        "official_url": "https://www.tansu-gen.jp/products/86500001",
        "facts": [
            "タンスのゲン公式商品ページで商品番号86500001の遮光カーテン4枚セットを商品同定",
            "公式ページで幅・丈の選択、遮光カーテンのみ2枚またはミラーレース付き4枚のセット選択、洗濯可能の案内を確認",
            "公式商品ページでレビュー72件・平均4.6点の表示を確認し、個別投稿では色味・取り付けやすさ・サイズ選択に触れる内容を確認",
            "カーテンは窓寸法・色・セット内容で適合が変わるため、購入前に幅・丈・枚数を照合する",
        ],
        "review_texts": [{
            "source": "タンスのゲン公式商品ページ個別レビュー",
            "text": "個別投稿では、色味、取り付けやすさ、サイズを選べる点を評価する内容が確認できます。一方で、予約待ちによる到着の遅れに触れる投稿もあります。窓寸法や購入時期による条件差があるため、すべての注文に同じ印象が当てはまるとは扱いません。",
        }],
        "review_stats": {"official_store": {"count": 72, "average": 4.6}},
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.tansu-gen.jp/products/86500001",
            "title": "タンスのゲン公式 86500001 遮光カーテン",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/tansu/86500001/",
            "title": "楽天市場 タンスのゲン 86500001 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://www.tansu-gen.jp/products/86500001",
            "title": "タンスのゲン公式 86500001 個別レビュー表示",
            "checked_at": "2026-10-06",
        }],
    },
    "ih-ipdci-t13": {
        "official_url": "https://www.irisohyama.co.jp/",
        "facts": [
            "アイリスオーヤマ公式楽天市場店の商品ページで、IPDCI-T13の13点フライパン・鍋セットを商品同定",
            "公式販売ページでIH対応・ガス火対応、取っ手が取れる構成、商品コードH527380を確認",
            "Yahoo!ショッピングの個別商品ページで同じ商品コードH527380とJAN4967576825740の表示を確認",
            "Yahoo!個別投稿では取っ手の扱いや中火使用、焦げ付きに関する体験談があるが、調理器具・火力・使い方による個人差を分けて扱う",
        ],
        "review_texts": [{
            "source": "Yahoo!ショッピング IPDCI-T13個別レビュー",
            "text": "個別投稿では、取っ手の扱いやすさを評価する声がある一方、中火使用や焦げ付きに触れる投稿も確認できます。使用する熱源・調理内容・手入れで結果が変わるため、すべての利用者に同じ評価が当てはまるとは扱いません。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.irisohyama.co.jp/",
            "title": "アイリスオーヤマ公式サイト",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://store.shopping.yahoo.co.jp/irisplaza/h527380.html",
            "title": "Yahoo! アイリスプラザ IPDCI-T13 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://shopping.yahoo.co.jp/review/item/list?page_key=h527380&store_id=irisplaza",
            "title": "Yahoo! IPDCI-T13 商品レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "salonia-2": {
        "official_url": "https://salonia.jp/product/hair/stylingitem/rockstylemilk/",
        "facts": [
            "SALONIA公式ページでロックスタイルミルクを商品同定",
            "公式案内で朝夜に使う2wayヘアミルクとして案内され、乾いた髪への使用方法と成分表示を確認",
            "楽天市場の個別商品ページでSALONIAロックスタイルミルクの商品を確認",
            "仕上がりやまとまりは髪質・使用量・乾かし方で変わるため、公式の使用方法を確認して少量から調整する",
        ],
        "review_texts": [{
            "source": "楽天市場のSALONIAスタイリングミルク個別レビュー",
            "text": "個別投稿では、アイロン前のスタイリング剤として探したという購入理由や、髪をまとめる目的で使うという内容が確認できます。商品名や使用目的が近い投稿でも髪質・使用量による個人差があるため、全体の仕上がりとして一般化しません。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://salonia.jp/product/hair/stylingitem/rockstylemilk/",
            "title": "SALONIA公式 ロックスタイルミルク",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/kobe-beauty-labo/sal061/",
            "title": "楽天市場 SALONIAロックスタイルミルク 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/262435_10001922/1.1/",
            "title": "楽天市場 SALONIAスタイリングミルク 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "nimaso-iphone-iphone18pro-iphone-duo-iphone18proma": {
        "official_url": "https://nimaso.co.jp/collections/iphone-camera-lens-protectors",
        "facts": [
            "NIMASO公式のiPhoneカメラレンズカバー案内で、カメラレンズ保護フィルムの製品群を確認",
            "楽天市場の個別商品ページの商品名で、対象商品が2枚組として販売されていることを確認",
            "楽天市場の個別商品ページでNIMASO iPhone用レンズカバーの販売商品と対応機種選択を確認",
            "対応機種・レンズ形状・ケースとの干渉はiPhoneの世代と商品構成で変わるため、注文時の選択欄を照合する",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた貼り付け後の状態",
            "who": "楽天市場 NIMASOレンズカバー個別商品レビュー（2026-10-06確認）",
            "text": "個別投稿では、NIMASOの保護フィルムを継続して使っている、貼り付け後の見た目を評価する声が確認できます。一方で、貼り付け時に空気が抜けないという投稿もあります。貼り付け手順・端末・ケースとの相性による感想として扱い、すべての端末で同じ結果になるとは一般化しません。",
            "negative": True,
            "fix_title": "対応機種とケース干渉を先に確認する",
            "fix": "注文前にiPhoneの正確な機種、レンズ形状、使用中ケースとの干渉、貼り付け手順を確認してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://nimaso.co.jp/collections/iphone-camera-lens-protectors",
            "title": "NIMASO公式 iPhoneカメラレンズカバー",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/niccou-store/20210508-jtm-tm/",
            "title": "楽天市場 NIMASO iPhoneレンズカバー 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://item.rakuten.co.jp/niccou-store/20210508-jtm-tm/",
            "title": "楽天市場 NIMASO iPhoneレンズカバー 個別レビュー表示",
            "checked_at": "2026-10-06",
        }],
    },
    "puppia-xs-s-m-l": {
        "official_url": "https://www.puppia.jp/puppia2014fw.pdf",
        "facts": [
            "PUPPIA公式資料でソフトベストハーネスのサイズ展開にXS・S・M・Lが含まれることを確認",
            "楽天市場の個別商品ページで小型犬向けの商品表示とXS・S・M・Lのサイズ選択を確認",
            "楽天市場の個別商品ページでPUPPIAパピア ソフトベストハーネスの販売商品とサイズ選択を確認",
            "犬の首や気管への負担、抜けにくさは体格・装着状態・犬の動きで変わるため、公式サイズ表と実寸を照合して選ぶ",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた装着しやすさ",
            "who": "楽天市場 PUPPIAソフトベストハーネス個別レビュー（2026-10-06確認）",
            "text": "個別投稿では、リピート購入していて使いやすい、装着が楽という声が確認できます。一方で、首輪から替えて歩きやすくなったという投稿もありますが、犬種・体格・引っ張り方による感想です。すべての犬に同じ装着感や安全性が得られるとは一般化しません。",
            "negative": True,
            "fix_title": "首回りと胴回りを実測する",
            "fix": "購入前に公式サイズ表と愛犬の実寸を照合し、装着後は指が入りすぎないか、動きを妨げないかを確認してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.puppia.jp/puppia2014fw.pdf",
            "title": "PUPPIA公式 ソフトベストハーネス資料",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/dogskip/puppia-paha-ah305a/",
            "title": "楽天市場 PUPPIAソフトベストハーネス 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/230805_10000752/1.1/",
            "title": "楽天市場 PUPPIAソフトベストハーネス 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "pc-lkd-127": {
        "official_url": "https://www.look-it.jp/view/item/000000008428",
        "facts": [
            "LOOKIT公式商品ページでオフィスデスク片袖机 LKD-127、幅1200×奥行700mmの商品を同定",
            "公式販売情報で天板100kg、上段5kg、中段20kg、下段20kgの平均耐荷重、スチール製・粉体塗装の表記を確認",
            "法人宛配送や組立条件は地域・注文条件で変わるため、購入時の販売ページを確認する",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた組み立てや見た目への評価",
            "who": "楽天市場 LKD-127個別商品レビュー（2026-10-06確認）",
            "text": "個別投稿では、組み立てが簡単だった、商品がきれいだった、色合いや見栄えがよいという声が確認できます。机の設置環境、組み立て経験、選んだカラーによる感想であり、すべての購入者に同じ結果が出るとは一般化しません。",
            "negative": True,
            "fix_title": "搬入・組み立て条件を先に確認する",
            "fix": "設置場所の寸法、搬入経路、組み立て人数、法人・個人宛の配送条件を購入前に確認してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.look-it.jp/view/item/000000008428",
            "title": "LOOKIT公式 LKD-127",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/look-it/lkd-127/",
            "title": "楽天市場 LKD-127 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://item.rakuten.co.jp/look-it/lkd-127/",
            "title": "楽天市場 LKD-127 個別レビュー表示",
            "checked_at": "2026-10-06",
        }],
    },
    "inumeshi": {
        "official_url": "https://www.i-de-al.com/c/gr001/gr007/gr1031",
        "facts": [
            "INUMESHI公式オンラインストアで、INUMESHIバリューの15kgパックを商品として確認",
            "公式案内で成犬・高齢犬用、全犬種向けの販売区分を確認。食事の適合や健康上の効果は犬の状態と獣医師の助言を優先する",
            "楽天市場の個別商品ページでINUMESHIバリュー15kgブリーダーパックの商品同定と販売情報を確認",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた継続しやすさと食べ方の違い",
            "who": "楽天市場 INUMESHIバリュー15kg個別レビュー（2026-10-06確認）",
            "text": "個別投稿では、多頭飼いで価格面からリピートしている、愛犬がよく食べるという声が確認できます。一方で、便の量やにおいが気になるという投稿もあります。犬の体質・頭数・切り替え方による個人の感想であり、食いつきや体調への効果をすべての犬に一般化しません。",
            "negative": True,
            "fix_title": "犬の状態と切り替え方法を確認する",
            "fix": "給与量や切り替え方法は販売ページの案内を確認し、体調に変化があれば給餌を見直して獣医師へ相談してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.i-de-al.com/c/gr001/gr007/gr1031",
            "title": "INUMESHI公式 バリュー",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/net-ryohin/inu-011/",
            "title": "楽天市場 INUMESHIバリュー15kg 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/241004_10285595/1.1/",
            "title": "楽天市場 INUMESHIバリュー15kg 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "bi-hada-mpvl-2b-ga0145": {
        "official_url": "https://www.kai-group.com/products/kamisori/product/bihadaompa.html",
        "facts": [
            "貝印公式のbi-hada ompa案内で、音波振動カミソリのシリーズ情報を確認",
            "楽天市場の個別商品ページでbi-hada MPVL-2B（GA0145）、JAN4901331003134、刃部・寸法・重量・付属品の表記を確認",
            "刃物のため、公式案内と販売ページの注意事項を優先し、肌への刺激や切れ味をすべての利用者に一般化しない",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた使いやすさと注意点",
            "who": "楽天市場 MPVL-2B個別レビュー（2026-10-06確認）",
            "text": "個別投稿では、使いやすい、音波振動で楽に処理できるという声が確認できます。一方で、肌が傷ついた、数回で切れ味が悪くなったという投稿もあります。刃の状態、肌質、使い方による感想であり、すべての利用者に同じ結果が出るとは一般化しません。",
            "negative": True,
            "fix_title": "肌への使用と替刃の状態を確認する",
            "fix": "刃物として注意事項を守り、肌に異常を感じた場合は使用を中止してください。替刃の交換条件や保管方法も購入先・公式案内で確認してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.kai-group.com/products/kamisori/product/bihadaompa.html",
            "title": "貝印公式 bi-hada ompa",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/lila-q/2013052101/",
            "title": "楽天市場 bi-hada MPVL-2B 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/241838_10000488/5.0/",
            "title": "楽天市場 bi-hada MPVL-2B 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "niplux-hair-dryer": {
        "official_url": "https://niplux.jp/collections/%E5%95%86%E5%93%81%E4%B8%80%E8%A6%A7%E7%94%A8/products/hair-dryer",
        "facts": [
            "NIPLUX公式オンラインストアでHair Dryer（型番NP-HD25BK）を商品として確認",
            "公式販売ページで、延長保証の選択肢と公式ストアでの販売情報を確認。価格・在庫は変動するため購入時点の表示を確認する",
            "大風量・速乾などの訴求は公式販売ページの表現として扱い、乾燥時間や髪質への効果をすべての利用者に一般化しない",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた乾燥時の感想",
            "who": "楽天市場 NIPLUX Hair Dryer個別レビュー（2026-10-06確認）",
            "text": "個別投稿では、風当たりがやさしく頭皮への刺激が少ないという声や、他社製品と比較して価格帯を検討して購入したという声が確認できます。髪質、乾かし方、比較対象による感想であり、乾燥時間や仕上がりをすべての利用者に一般化しません。",
            "negative": True,
            "fix_title": "髪質と乾燥条件を購入前に想定する",
            "fix": "自分の髪の長さ・量・温度の好みを整理し、公式ページの仕様と購入時の保証条件を確認してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://niplux.jp/collections/%E5%95%86%E5%93%81%E4%B8%80%E8%A6%A7%E7%94%A8/products/hair-dryer",
            "title": "NIPLUX公式 Hair Dryer",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/nissoplus/np-hd25/",
            "title": "楽天市場 NIPLUX Hair Dryer 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/381975_10000291/1.1/",
            "title": "楽天市場 NIPLUX Hair Dryer 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "fotopro-digi-mp1bh": {
        "official_url": "https://www.esco-net.com/wcs/escort/ItemFile/EA7/EA759/EA759ER-1C/EA759ER-1C_DOC_CTL_OUT%2801%29.pdf",
        "facts": [
            "Fotopro DIGI-MP1BHを製品名・型番で同定し、メーカー資料の一脚仕様を確認",
            "個別商品ページでFotopro DIGI-MP1BHの販売商品を確認。カメラやビデオカメラとの適合は機材側の重量・取付ねじを購入前に照合する",
            "一脚は自立する三脚とは用途が異なり、撮影時は使用者が保持する前提で、設置場所や荷重条件を断定しない",
        ],
        "review_texts": [{
            "source": "楽天市場 DIGI-MP1BH個別レビュー",
            "text": "個別投稿では、長時間の手持ち撮影より楽になった、軽くて持ち運びやすい、自由雲台が便利という声が確認できます。一方で高さがもう少し欲しいという投稿や、使用頻度によっては三脚ほどの安定性を求めない人向けという内容もあります。撮影機材・身長・用途による感想として扱い、すべての利用者に同じ結果が出るとは一般化しません。",
        }],
        "voices": [{
            "heading": "個別投稿で確認できた携帯性と一脚の使い勝手",
            "who": "楽天市場 DIGI-MP1BH個別レビュー（2026-10-06確認）",
            "text": "個別投稿では、長時間の手持ち撮影より楽になった、軽くて持ち運びやすい、自由雲台が便利という声が確認できます。一方で高さがもう少し欲しいという投稿もあります。撮影機材・身長・用途による感想として扱い、すべての利用者に同じ結果が出るとは一般化しません。",
            "negative": True,
            "fix_title": "一脚と機材の条件を購入前に照合する",
            "fix": "取り付ける機材の重量・取付ねじ・必要な高さを確認し、自立する三脚とは異なる一脚として用途に合うか判断してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.esco-net.com/wcs/escort/ItemFile/EA7/EA759/EA759ER-1C/EA759ER-1C_DOC_CTL_OUT%2801%29.pdf",
            "title": "Fotopro DIGI-MP1BH 製品資料",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/photolink/4906238808424/",
            "title": "楽天市場 Fotopro DIGI-MP1BH 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/review/item/1/271875_10000436/1.1/",
            "title": "楽天市場 Fotopro DIGI-MP1BH 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "buffalo-wifi6-ax5400-review": {
        "official_url": "https://www.buffalo.jp/product/detail/wsr-5400ax6s_dmb.html",
        "facts": [
            "バッファロー公式でAirStation WSR-5400AX6S/DMBを商品同定し、Wi-Fi 6対応ルーターとして確認",
            "公式ページで型番ごとの仕様・対応情報を確認できるため、WSR-5400AX6Sシリーズの色・販売形態を混同しない",
            "楽天市場の個別商品ページでWSR-5400AX6S系の商品掲載を確認し、通信速度や接続台数は設置環境・端末条件で変わるため断定しない",
        ],
        "review_texts": [{
            "source": "楽天市場のWSR-5400AX6S個別レビュー",
            "text": "個別投稿では、ネット脅威ブロッカーの設定が通信速度に影響する可能性を指摘する声が確認できます。設定や回線、接続端末によって結果が変わる利用者の報告として扱い、すべての環境の速度傾向には一般化しません。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.buffalo.jp/product/detail/wsr-5400ax6s_dmb.html",
            "title": "バッファロー公式 WSR-5400AX6S/DMB",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/saino/55089gkk3ym/",
            "title": "楽天市場 WSR-5400AX6S 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/item/1/213310_20432335/1.1/",
            "title": "楽天市場 WSR-5400AX6S 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "schick-3": {
        "official_url": "https://schick.jp/pages/salon_tufs",
        "facts": [
            "シック公式ページでサロンプラス トーンアップ フェイススムーサー替刃（3コ入）を確認",
            "公式案内で本体に対応する替刃として扱われること、使用方法・交換目安は公式案内を確認して使う商品であることを確認",
            "エディオンの個別商品ページで商品コードFC009MP、JAN4891228313807、シック ハイドロシルク サロンプラス トーンアップ フェイススムーサー替刃3個を商品同定",
            "楽天市場の個別商品ページでも同じ替刃3個の商品名を確認",
        ],
        "review_texts": [{
            "source": "楽天市場の替刃個別レビュー",
            "text": "個別投稿では、同シリーズの本体を気に入って替刃を購入したという声が確認できます。替刃の交換頻度や本体との組み合わせに触れる投稿もありますが、肌状態や使用方法による個人差があるため、すべての利用者に同じ結果が出るとは扱いません。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://schick.jp/pages/salon_tufs",
            "title": "シック公式 サロンプラス トーンアップ フェイススムーサー",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/e-konekuto/4891228313807/",
            "title": "楽天市場 シック替刃3コ入 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/review/item/1/428623_10063064/1.1/",
            "title": "楽天市場 シック替刃 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "ergotron-lx-monitor-arm-review": {
        "official_url": "https://media.ergotron.com/reserved/resources/lx-deskmountarms-jp-orig.pdf",
        "facts": [
            "エルゴトロン公式資料でLXデスクマウントアームの製品群と、モニターアームとしての可動・設置条件を確認",
            "楽天市場のエルゴトロン公式個別商品ページでLXデスクマウントアームの型番45-241-224を確認",
            "公式資料の対応重量・VESA・机への固定条件は、取り付けるモニターと机の実寸を購入前に照合する",
        ],
        "review_texts": [{
            "source": "楽天市場 エルゴトロン公式店のLX個別レビュー",
            "text": "個別投稿では、作りがしっかりして動きが滑らかという評価がある一方、机上からクランプ作業ができる製品を羨ましく感じるという声も確認できる。モニターの重量、机の天板、取り付け手順によって使い勝手が変わるため、投稿者の環境を一般化しない。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://media.ergotron.com/reserved/resources/lx-deskmountarms-jp-orig.pdf",
            "title": "エルゴトロン公式 LXデスクマウントアーム資料",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/ergotron/e1r00wv/",
            "title": "楽天市場 エルゴトロン公式 LX個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/review/item/1/415243_10000220/1.1/",
            "title": "楽天市場 LX個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "gunze-agw112": {
        "official_url": "https://www.gunze.co.jp/corporate/news/2025/03/20250304001.html",
        "facts": [
            "グンゼ公式のアセドロン案内で、汗対策シリーズとして吸汗速乾・ムレにくさ・消臭などの訴求を確認。ただし商品ごとの仕様は販売ページで照合する",
            "楽天市場の個別商品ページで、靴下3足組アセドロンショート丈AGW112の品番と商品同定を確認",
            "アセドロンの機能訴求は素材・モデルによって異なるため、AGW112へ公式発表の全特徴を一括適用しない",
        ],
        "voices": [{
            "heading": "個別投稿で確認できた涼しさと薄手設計への評価",
            "who": "楽天市場のAGW112個別商品ページに表示された投稿（2026-10-06確認）",
            "text": "個別投稿では、夏場にスニーカーで履いても足裏のベタつきが少ない、吸汗と乾きが早い印象という声があります。一方で、薄手のため厚手スポーツソックスのようなクッション感はない、洗濯を重ねるとつま先やかかとの摩耗が気になるという投稿もあります。投稿者の用途・足形・洗濯条件による感想であり、すべての利用者に同じ結果が出るとは扱いません。",
            "negative": True,
            "fix_title": "薄手の履き心地と耐久性を用途に合わせて確認する",
            "fix": "クッション性を重視する場合は手持ちの靴やインソールとの相性を確認し、洗濯時は販売ページの表示に従ってください。通気性や耐久性の感じ方は靴・歩行量・洗濯頻度で変わります。",
        }],
        "evidence_audit": {
            "checked_at": "2026-10-06T11:00:00+09:00",
            "status": "passed",
            "official_url": "https://www.irisohyama.co.jp/products/electrical-appliances/lighting-equipment/ceiling-light/light-guide-plate-series/light-guide-plate-toning-type/",
            "has_official_evidence": True,
            "individual_product_urls": {
                "rakuten_url": "https://item.rakuten.co.jp/luminous81023/rumda4412b9a2/",
                "yahoo_url": "https://store.shopping.yahoo.co.jp/joylight/538005.html",
            },
            "has_product_identity": True,
            "has_review_text": True,
            "review_stats_present": True,
            "missing": [],
            "blockers": [],
        },
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.gunze.co.jp/corporate/news/2025/03/20250304001.html",
            "title": "グンゼ公式 アセドロンシリーズ案内",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/tensyodo/gr-e9grdujjir/",
            "title": "楽天市場 アセドロンショート丈AGW112個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://item.rakuten.co.jp/tensyodo/gr-e9grdujjir/",
            "title": "楽天市場 AGW112個別投稿表示",
            "checked_at": "2026-10-06",
        }],
    },
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
        "voices": [],
        "review_texts": [{
            "source": "Yahoo!ショッピング CEA-A08DLP個別投稿",
            "text": "8畳用でも期待ほど明るく感じなかった、天井の高さや火災報知器の位置で影が出るという投稿がある一方、導光板で天井まで光が反射し明るく感じた、調光・調色が便利、取り付けが簡単という投稿も確認できる。個別の部屋と取り付け条件による感想として扱う。",
        }],
        "evidence_audit": {
            "checked_at": "2026-10-06T11:00:00+09:00",
            "status": "passed",
            "official_url": "https://www.irisohyama.co.jp/products/electrical-appliances/lighting-equipment/ceiling-light/light-guide-plate-series/light-guide-plate-toning-type/",
            "has_official_evidence": True,
            "individual_product_urls": {"rakuten_url": "https://item.rakuten.co.jp/luminous81023/rumda4412b9a2/", "yahoo_url": "https://store.shopping.yahoo.co.jp/joylight/538005.html"},
            "has_product_identity": True,
            "has_review_text": True,
            "review_stats_present": True,
            "missing": [],
            "blockers": [],
        },
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
        "official_ogp_image": "https://chimoto-coffee.co.jp/wp-content/uploads/2021/08/ogp_facebook.png",
        "official_ogp_title": "チモトコーヒー公式サイト",
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
            "text": "個別投稿では、中細挽きの粉を毎日飲むためリピートしているという声、4種類の味と香りを楽しんでいるという声、すっきりした飲み口で他の種類も楽しみという声が確認できます。味や香りは飲み方・保存状態・好みによって変わるため、4種類を試せる点と容量を購入判断に反映します。",
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
    },
    "anker-prime-power-bank-20100mah-220w-with-anker-pr": {
        "official_url": "https://www.ankerjapan.com/products/b110b",
        "facts": [
            "Anker Japan公式情報でAnker Prime Power Bank（20100mAh、220W）とCharging Base（150W、3ポート）のセットを確認",
            "公式仕様で本体約520g、約147×44×51mm、USB-C出力は最大140W、USB-A出力は最大22.5Wと確認",
            "公式情報ではCharging BaseのUSB-C1最大140W、USB-C2最大100W、USB-A最大22.5Wと案内されている",
        ],
        "review_texts": [{
            "source": "価格.com 個別使用レビュー A110BH11",
            "text": "価格.comの個別レビュー欄で、20100mAh・220Wモデルの利用者評価と、重量や携帯性を含む使用感を確認できます。個別投稿の感想であり、すべての利用者に当てはまる傾向とは断定しません。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.ankerjapan.com/products/b110b",
            "title": "Anker Japan公式 B110B",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/anker/a1339/",
            "title": "Anker公式 楽天市場 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.kakaku.com/review/K0001719137/",
            "title": "価格.com 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    }
    ,"anua-pdrn-100-50ml": {
        "official_url": "https://anuashop.jp/products/side0011",
        "facts": [
            "Anua公式オンラインショップでPDRNヒアルロン酸カプセル100セラム（30ml／50ml）の商品情報を確認",
            "公式ページでDNA-Na、ヒアルロン酸、加水分解コラーゲンを整肌成分として案内していることを確認",
            "公式ページで全成分一覧、みずみずしく肌になじむ使用感、30ml／50mlの容量選択を確認",
            "公式ページの掲載レビューは101件、星5が70%、星4が24%として表示されている（確認時点）",
            "対象記事は50mlとして扱い、販売ページの容量選択を購入前に確認する構成にする",
        ],
        "voices": [{
            "heading": "公式掲載レビューで確認できる保湿感の声",
            "who": "Anua公式オンラインショップ掲載レビュー（乾燥肌の投稿）",
            "text": "乾燥肌の投稿では、夜の使用後に翌朝までしっとりしたという感想が確認できます。一方で、別の投稿では刺激を感じたという記載もあり、肌質や状態によって感じ方が異なる個別の声として扱います。",
            "negative": True,
            "fix_title": "肌の状態を見ながら少量で確認する",
            "fix": "乾燥や刺激が気になる場合は、顔全体へ一度に広げず、販売元の使用案内と自身の肌状態を確認してから使い始めてください。",
        }, {
            "heading": "50mlを選んだ利用者の声",
            "who": "楽天市場 Anua公式店の個別レビュー（2026年6月投稿）",
            "text": "50mlを選択した投稿では、大容量になったことを歓迎する声や、しっとりした使用感を評価する声が確認できます。容量の異なる投稿と混同せず、個別の感想として紹介します。",
            "negative": False,
            "fix_title": "30mlと50mlを購入画面で確認する",
            "fix": "注文前に容量選択が30mlか50mlかを確認し、初回は使用量と肌との相性を見ながら選んでください。",
        }],
        "review_texts": [{
            "source": "Anua公式オンラインショップ掲載レビュー",
            "text": "公式掲載レビューでは、乾燥肌の利用者がしっとり感やリピートを評価する投稿がある一方、刺激を感じる投稿や香りへの言及も確認できます。掲載レビューの範囲として扱い、効果を保証する表現にはしません。",
        }, {
            "source": "楽天市場 Anua公式店 個別レビュー",
            "text": "50mlを選んだ個別レビューでは、大容量になったことを歓迎する声や、しっとりした使用感を評価する声が確認できます。容量選択の異なる投稿を混同せず、個別の利用者の声として整理します。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://anuashop.jp/products/side0011",
            "title": "Anua公式 PDRNヒアルロン酸カプセル100セラム",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://store.shopping.yahoo.co.jp/happyworldshop2/hapitetv-9fh-j8n.html",
            "title": "Yahoo!ショッピング 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/review/item/1/408283_10000361",
            "title": "楽天市場 Anua公式店 個別レビュー一覧",
            "checked_at": "2026-10-06",
        }],
    }
    ,"kindle-paperwhite-signature-review": {
        "official_url": "https://press.aboutamazon.com/jp/news/retail/2021/9/amazon-%E6%96%B0%E4%B8%96%E4%BB%A3kindle-paperwhite",
        "facts": [
            "Amazon公式発表でKindle Paperwhiteシグニチャーエディション（第11世代・2021年発売）の32GB構成を確認",
            "公式発表でPaperwhiteの6.8インチ反射抑制ディスプレイ、色調調節ライト、USB-C充電を確認",
            "シグニチャーエディションは32GB、明るさ自動調節、ワイヤレス充電対応と公式発表で案内されている",
        ],
        "review_texts": [{
            "source": "TechRadar Kindle Paperwhite Signature Edition 2021 review",
            "text": "TechRadarの製品レビューでは、Signature Editionの画面表示、読書用途、ワイヤレス充電などを確認できます。第三者レビューの評価として扱い、すべての利用者に同じ使用感があるとは断定しません。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://press.aboutamazon.com/jp/news/retail/2021/9/amazon-%E6%96%B0%E4%B8%96%E4%BB%A3kindle-paperwhite",
            "title": "Amazon公式発表 Kindle Paperwhite 第11世代",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://www.amazon.co.jp/dp/B08N2ZL7PS",
            "title": "Amazon 個別商品ページ B08N2ZL7PS",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://www.techradar.com/reviews/amazon-kindle-paperwhite-signature-edition-2021-review",
            "title": "TechRadar 個別製品レビュー",
            "checked_at": "2026-10-06",
        }],
    }
    ,"tilt-footrest-review": {
        "official_url": "https://www.bauhutte.jp/product/bft700/",
        "facts": [
            "Bauhutte公式情報でチルトフットレストワイド BFT-700-BK、JAN 4580742233318を確認",
            "公式仕様の寸法は幅700mm×奥行300mm×高さ210〜300mm、耐荷重は約30kg",
            "公式情報でクッション部は木板、脚部・スタンドは金属、角度調整に対応する構成を確認",
        ],
        "review_texts": [{
            "source": "Yahoo!ショッピング 個別商品レビュー BFT-700-BK",
            "text": "個別レビューでは、角度調整が簡単で質感がよいという声や、机の下で足の位置が安定し落ち着いて座れるようになったという声が確認できます。3件の個別投稿として扱い、すべての利用者に同じ効果があるとは断定しません。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.bauhutte.jp/product/bft700/",
            "title": "Bauhutte公式 BFT-700",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/applied2/4580742233318-ds/",
            "title": "楽天市場 個別商品ページ BFT-700-BK",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://store.shopping.yahoo.co.jp/hitline/4580742233318.html",
            "title": "Yahoo!ショッピング 個別レビュー BFT-700-BK",
            "checked_at": "2026-10-06",
        }],
    }
    ,"orage-c33": {
        "official_url": "https://www.tvfusion.co.jp/product/616",
        "facts": [
            "Orage公式販売ページでC33コードレスサイクロン掃除機の商品ページを確認",
            "公式販売ページではC33の2in1コードレス掃除機として掲載されていることを確認",
            "Yahoo!ショッピングの商品情報で22.2V、ヘッドライト、交換用バッテリー対応などの掲載情報を確認するが、購入時の仕様は販売ページで再確認する",
        ],
        "voices": [{
            "heading": "取り回しとヘッドライトを評価する声",
            "who": "Yahoo!ショッピング Orage C33 個別レビュー",
            "text": "個別レビューでは、コードレス・軽さ・ブラシ回転式ヘッド・ヘッドライトを評価し、コードレス掃除機として十分と感じたという投稿があります。個別の使用感として扱い、全利用者の評価とは断定しません。",
            "negative": False,
            "fix_title": "主用途と期待する吸引力を先に決める",
            "fix": "購入前に、階段や車内などのサブ用途か、家全体を一台で掃除する用途かを分け、販売ページの運転時間・付属品と照合してください。",
        }, {
            "heading": "耐久性や部品交換を気にする声",
            "who": "Yahoo!ショッピング Orage C33 個別レビュー",
            "text": "別の個別レビューでは、長期使用時の故障や交換部品への関心が示されています。軽さだけで決めず、保証と交換用バッテリーの入手方法を確認したい商品として整理します。",
            "negative": True,
            "fix_title": "保証と交換部品を購入前に確認する",
            "fix": "購入前に販売元の保証期間、問い合わせ窓口、交換用バッテリーの販売状況を確認し、回答が得られない場合は購入判断を保留してください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.tvfusion.co.jp/product/616",
            "title": "Orage公式販売ページ C33",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://store.shopping.yahoo.co.jp/tvfusion/cleaner-cordless-c33.html",
            "title": "Yahoo!ショッピング 個別商品ページ Orage C33",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://shopping.yahoo.co.jp/products/83760dc71d/review/",
            "title": "Yahoo!ショッピング 個別レビュー Orage C33",
            "checked_at": "2026-10-06",
        }],
    }
    ,"h70ft-h70ft-h70ft-bac06wh": {
        "official_url": "https://www.huromjapan.com/product/h70ft",
        "facts": [
            "HUROM公式商品ページで、H70FT-BAC06WW/ホワイト、オールインワンフィルター、メガホッパー、ジュース・フローズン対応、15年保証の案内を確認",
            "公式仕様で、130mmの投入口、1.8Lのメガホッパー、食材をまとめて投入できる構成、付属品と食洗機使用時の注意を確認",
            "楽天市場の個別商品ページで、H70FT-BAC06WHホワイトを商品同定し、同型番の個別投稿を確認",
            "個別投稿では、音が静か、滑らかなジュースが作れる、洗浄や組み立てがしやすいという声がある一方、繊維質の多い食材では詰まりやすい、ジュースに繊維が混ざるという指摘もある",
        ],
        "review_texts": [{
            "source": "楽天市場 H70FT 個別投稿",
            "text": "個別投稿では、音が静かで滑らかなジュースが作れる、洗浄や組み立てが簡単という声があります。一方で、繊維質の多い葉物を続けて使うと詰まりやすい、ジュースに繊維が混ざるという指摘もあります。食材の種類や投入順で使い勝手が変わる個人の感想として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.huromjapan.com/product/h70ft",
            "title": "HUROM公式 H70FT 製品情報",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/pika831/10005259/",
            "title": "楽天市場 H70FT-BAC06WH 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/item/1/201791_10005259/1.1/",
            "title": "楽天市場 H70FT 個別投稿",
            "checked_at": "2026-10-06",
        }],
    }
    ,"p10-yunth-c-c": {
        "official_url": "https://yunth.jp/shop/products/101-01",
        "facts": [
            "Yunth公式商品ページで、生VC美容液、1ml×28包、医薬部外品、使用期限30秒の個包装を確認",
            "公式ページで、通常購入価格、使用方法、定期購入条件など購入前に確認すべき情報を確認し、肌への効果は個人差があるものとして扱う",
            "楽天市場のYunth公式店個別商品ページで、同じ生ビタミンC美容液1ml×28包を商品同定",
            "個別投稿では、使用時の温かさ、翌日の肌の感触や化粧のりを評価する声がある一方、肌状態によって合わない場合や、特典・店舗対応への不満もある",
        ],
        "review_texts": [{
            "source": "楽天市場 Yunth公式店 生ビタミンC美容液 個別投稿",
            "text": "個別投稿では、使用時に温かさを感じる、翌日の肌の感触や化粧のりを評価する声があります。一方で、肌状態によって合わない場合があるという注意や、特典の表示・店舗対応への不満もあります。使用感や肌との相性は個人差があるため、異常があれば使用を中止し、購入条件も確認します。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://yunth.jp/shop/products/101-01",
            "title": "Yunth公式 生VC美容液",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/yunth/10000000/",
            "title": "楽天市場 Yunth公式店 生ビタミンC美容液 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/409735_10000000/1.1/",
            "title": "楽天市場 Yunth公式店 個別投稿",
            "checked_at": "2026-10-06",
        }],
    }
    ,"kaedear-kdr-m11c": {
        "official_url": "https://www.kaedear.com/products/kdr-m11c",
        "facts": [
            "Kaedear公式商品ページで、クイックホールドKDR-M11C、対応スマートフォンの縦132〜175mm・横68〜85mm・厚さ12mm以下、重量150g、17mmボールマウントを確認",
            "公式ページで、バー／ミラーマウント、径変換アタッチメント、六角レンチなどのセット内容とメーカー保証1年を確認",
            "Yahoo!ショッピングのKaedear公式店でKDR-M11Cの個別販売ページを確認し、楽天市場の個別投稿で同一型番の利用者の声を確認",
            "個別投稿では、脱着しやすく取り付けも簡単、頑丈で使いやすいという声があるため、対応サイズとケースの厚さを確認して選ぶ商品として整理する",
        ],
        "review_texts": [{
            "source": "楽天市場 KDR-M11C 個別投稿",
            "text": "個別投稿では、脱着がしやすくバーへの取り付けも簡単、頑丈で使いやすいという声があります。装着するスマートフォンのサイズやケースの厚み、車体側の取り付け方法によって適合や使い勝手が変わるため、購入前に公式の対応範囲を確認します。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.kaedear.com/products/kdr-m11c",
            "title": "Kaedear公式 クイックホールド KDR-M11C",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://store.shopping.yahoo.co.jp/kaedear/kdr-m11c.html",
            "title": "Yahoo!ショッピング Kaedear公式店 KDR-M11C",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/370890_12373741/1.1/",
            "title": "楽天市場 KDR-M11C 個別投稿",
            "checked_at": "2026-10-06",
        }],
    }
    ,"recolte-rcp-7": {
        "official_url": "https://recolte-jp.com/support/faq/rcp-7/",
        "facts": [
            "レコルト公式サポートで、コードレス カプセルカッター ボンヌRCP-7の取扱説明書・部品案内を確認",
            "公式取扱説明書で、RCP-7、専用USB Type-Cケーブル、ガラスカップなどの構成と安全上の注意を確認",
            "楽天市場の個別商品ページで、recolteコードレス カプセルカッター ボンヌRCP-7、充電式、ガラス容器を商品同定",
            "個別投稿では、コードレスで少量の調理に使いやすい、ガラス容器が洗いやすいという声がある一方、容器が重く滑りやすい、食材の大きさが均一になりにくいという指摘もある",
        ],
        "review_texts": [{
            "source": "楽天市場 レコルト RCP-7 個別投稿",
            "text": "個別投稿では、コードレスで少量の調理に使いやすい、ガラス容器で洗いやすいという声があります。一方で、洗うときに容器が重く滑りやすい、食材の位置によって大きさが均一になりにくいという指摘もあります。扱いやすさは食材量や洗い方による個人の感想として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://recolte-jp.com/support/faq/rcp-7/",
            "title": "レコルト公式 RCP-7 FAQ",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/hotch-potch/00014805-cordless-bonne/",
            "title": "楽天市場 レコルト RCP-7 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/363461_10004508/1.1/",
            "title": "楽天市場 レコルト RCP-7 個別投稿",
            "checked_at": "2026-10-06",
        }],
    }
    ,"rsy-2-recolte-3": {
        "official_url": "https://recolte-jp.com/products/auto-cooking-pot/",
        "facts": [
            "レコルト公式商品ページで、自動調理ポットRSY-2、容量約600ml、5種類の調理モード、刻む・加熱・撹拌・保温を自動で行う構成を確認",
            "公式仕様で約幅16.5×奥行12.0×高さ23.3cm、約970g、AC100V、消費電力600Wを確認",
            "レコルト公式オンラインショップの個別商品ページで、RSY-2(BK)、JAN4582180208019、付属品と使用上の注意を確認",
            "楽天市場の個別投稿では、手入れしやすい、スープや料理を自動で作れるという声がある一方、本体を丸洗いできない点を心配する声もあり、手入れ方法を確認して使う必要がある",
        ],
        "review_texts": [{
            "source": "楽天市場 レコルト RSY-2 個別投稿",
            "text": "個別投稿では、付属ブラシやスポンジで清潔に維持できる、材料を入れて自動でスープを作れるという声があります。一方で、本体を丸洗いできない点を心配する声もあります。手入れのしやすさは使うメニューや洗い方による個人の感想として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://recolte-jp.com/products/auto-cooking-pot/",
            "title": "レコルト公式 自動調理ポット RSY-2",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/e-goods/ry1103674/",
            "title": "楽天市場 レコルト RSY-2 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/196113_10018473/1.1/",
            "title": "楽天市場 レコルト RSY-2 個別投稿",
            "checked_at": "2026-10-06",
        }],
    }
    ,"bruno-boe021-bruno": {
        "official_url": "https://bruno-inc.com/?am=07760192&pg=product_detail",
        "facts": [
            "BRUNO公式商品ページで、コンパクトホットプレートBOE021とセラミックコート鍋のセット構成、別売オプション、2〜3人向けのサイズ感を確認",
            "公式・販売ページで、平面プレートとたこ焼きプレート、深鍋、温度調整などの構成を確認",
            "楽天市場の個別販売ページで、BRUNOコンパクトホットプレートBOE021と深鍋セットを商品同定",
            "個別投稿では、鍋が深く料理しやすい、外して洗える、2人分にちょうどよいという声がある一方、本体装着時のがたつきや火力の偏りを指摘する声もある",
        ],
        "review_texts": [{
            "source": "楽天市場 BRUNO公式店 BOE021 個別投稿",
            "text": "個別投稿では、鍋が深く料理しやすい、外して丸洗いできる、2人分にちょうどよいという声があります。一方で、本体に取り付けたときのがたつきや、中央と端で火力に差があるという指摘もあります。使い勝手は料理内容や置き方による個人の感想として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://bruno-inc.com/?am=07760192&pg=product_detail",
            "title": "BRUNO公式 コンパクトホットプレート BOE021",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/roomy/ide17nov01b01/",
            "title": "楽天市場 BRUNO BOE021 深鍋セット 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/372781_10000325/1.1/",
            "title": "楽天市場 BRUNO公式店 BOE021 個別投稿",
            "checked_at": "2026-10-06",
        }],
    }
    ,"tanita-fs-101-fs101": {
        "official_url": "https://www.tanita.co.jp/support/manual/FS-101/",
        "facts": [
            "タニタ公式サポートで体組成計フィットスキャンFS-101の取扱説明書・関連ダウンロードを確認",
            "楽天市場の個別商品ページで、タニタFS-101A、体重・体脂肪率・内臓脂肪などを測定する商品として同定し、JAN4904785814639を価格比較情報で確認",
            "個別投稿では、コンパクトで場所を取らない、表示が見やすい、測定が早いという声がある一方、操作が面倒、測定中の表示が見づらいという指摘もある",
            "健康状態の診断や治療を目的とする機器ではないため、測定値は日々の傾向把握用として扱う",
        ],
        "review_texts": [{
            "source": "楽天市場 FS-101 個別投稿",
            "text": "個別投稿では、コンパクトで場所を取らず、表示が見やすく、測定が早いという声があります。一方で、操作が面倒、測定中は表示が薄く見えにくいという指摘もあります。使いやすさは年齢・視認性・測定方法による個人の感想として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.tanita.co.jp/support/manual/FS-101/",
            "title": "タニタ公式 FS-101 取扱説明書・関連ダウンロード",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/minimalife/fs101a/",
            "title": "楽天市場 FS-101A 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/396197_10000501/1.1/",
            "title": "楽天市場 FS-101A 個別投稿",
            "checked_at": "2026-10-06",
        }],
    }
    ,"salonia-salonia-2way-hk-2way-slall": {
        "official_url": "https://salonia.jp/product/hair/iron/2way/",
        "facts": [
            "SALONIA公式商品ページで、2WAYストレート&カールヘアアイロン32mm、約50秒で最低設定温度に到達、100〜220℃を5℃刻みで調整、約30分後の自動電源OFF、100〜240V海外対応を確認",
            "公式仕様で本体サイズ約74×39×320mm、32mmバレル、重量約420g（対象カラー）を確認",
            "楽天市場の公式店個別商品ページで、2WAYストレート&カール、32mm、1年保証、海外対応の商品同定を確認",
            "個別投稿では、温まりが早い、ストレートとカールの両方に使える、軽く持ち運びやすいという声がある一方、カール部分が熱くなる、ボタンを誤操作しやすいという指摘もある",
        ],
        "review_texts": [{
            "source": "楽天市場 SALONIA公式店 2WAYストレート&カール 32mm 個別投稿",
            "text": "個別投稿では、温まりが早い、ストレートとカールの両方に使える、軽くて持ち運びやすいという声があります。一方で、ストレート使用時にカール部分が熱く感じる、温度調整ボタンを誤って押してしまうという指摘もあります。使いやすさは髪質・持ち方・使用環境による個人の感想として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://salonia.jp/product/hair/iron/2way/",
            "title": "SALONIA公式 2WAYストレート&カールヘアアイロン",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/kobe-beauty-labo/main-salo3/",
            "title": "楽天市場 SALONIA公式店 2WAY 32mm 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/262435_10000050/1.1/",
            "title": "楽天市場 SALONIA公式店 2WAY 32mm 個別投稿",
            "checked_at": "2026-10-06",
        }],
    }
    ,"kae-g13n": {
        "official_url": "https://www.tiger-corporation.com/ja/jpn/product/others/kae-g13n/",
        "facts": [
            "タイガー魔法瓶公式ページで、オーブントースターKAE-G13N、消費電力1300W、温度調整範囲約80〜250℃、本体約35.4×34.4×24.2cm、庫内約30×27.5×10cm、質量約4.2kgを確認",
            "公式ページでレッド、マットブラック、マットホワイトの色展開とKAE-G13Nの型番を確認",
            "楽天市場タイガー魔法瓶公式店の個別商品ページで、KAE-G13NWE、1300W、30分タイマー、温度調節、調理トレイ、JAN4904710429013を確認",
            "個別投稿では、パンが外はカリッと中はふわっと焼ける、庫内が広いという声がある一方、火力が強く焦げやすい、短時間のタイマー調整が難しいという指摘もあり、焼き時間は様子を見ながら調整する必要がある",
        ],
        "review_texts": [{
            "source": "楽天市場 タイガー魔法瓶公式店 KAE-G13N 個別投稿",
            "text": "個別投稿では、パンが外はカリッと中はふわっと焼ける、庫内が広く使いやすい、網やパンくずトレイの手入れがしやすいという声があります。一方で、火力が強くパンが焦げやすい、短時間のタイマー設定が難しい、扉の開き方によって大きなピザを取り出しにくいという指摘もあります。焼き上がりと操作感は利用環境や使い方による個人の感想として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.tiger-corporation.com/ja/jpn/product/others/kae-g13n/",
            "title": "タイガー魔法瓶公式 KAE-G13N 商品情報",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/tiger-online/kae-g13nwe/",
            "title": "楽天市場 タイガー魔法瓶公式店 KAE-G13N 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/281266_10004136/1.1/",
            "title": "楽天市場 タイガー魔法瓶公式店 KAE-G13N 個別投稿",
            "checked_at": "2026-10-06",
        }],
    }
    ,"refa-ultra-fine-bubble-laundry-rs-ck-00a": {
        "official_url": "https://www.refa.net/en/item/refa_ultra_fine_bubble_laundry/",
        "facts": [
            "ReFa公式商品ページで、商品名ReFa ULTRA FINE BUBBLE LAUNDRY、型番RS-CK-00A、直径約30mm・高さ約62mm・重量約210g、G3/4ホース接続ねじを確認",
            "公式説明では、1マイクロメートル未満のウルトラファインバブルを洗濯水に発生させる製品として案内されている",
            "楽天市場の個別商品ページで、同じ型番RS-CK-00A、JAN4974011815150、洗濯機の給水口に取り付ける構成を確認",
            "楽天市場の個別投稿では、洗濯物の肌ざわりや柔軟剤の香りを評価する声がある一方、効果を実感できないという声もあり、体感には個人差があると整理する",
        ],
        "review_texts": [{
            "source": "楽天市場 ReFa ULTRA FINE BUBBLE LAUNDRY RS-CK-00A 個別投稿",
            "text": "個別投稿では、洗濯物がきれいになり肌ざわりがよくなった、柔軟剤の香りが感じやすくなったという声がある一方、特に変化を実感していないという投稿もあります。効果の感じ方は洗濯機・洗剤・衣類・使用期間で変わる個人の感想として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.refa.net/en/item/refa_ultra_fine_bubble_laundry/",
            "title": "ReFa公式 ULTRA FINE BUBBLE LAUNDRY 商品情報",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/tea-life/98490/",
            "title": "楽天市場 ReFa ULTRA FINE BUBBLE LAUNDRY RS-CK-00A 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/394827_10001888/1.1/",
            "title": "楽天市場 ReFa ULTRA FINE BUBBLE LAUNDRY RS-CK-00A 個別投稿",
            "checked_at": "2026-10-06",
        }],
    }
    ,"chromelite-ultracush-s": {
        "official_url": "https://cjutro.jp/pages/chromelite",
        "facts": [
            "C.jutro公式ページでChromeLiteを2年の開発期間を経て誕生した独自素材として案内していることを確認",
            "公式情報でChromeLite×UltraCushのSサイズ・機内持ち込みモデルのシリーズ掲載を確認",
            "購入対象はASIN B0F9VFYC1Zと楽天市場の商品ページを照合し、サイズ・カラー選択を注文前に確認する",
        ],
        "voices": [{
            "heading": "楽天市場の利用者の声で確認できる走行感",
            "who": "楽天市場 C.jutro公式店の利用者の声（2025年8月投稿）",
            "text": "個別レビューでは、機内持ち込みサイズを探して購入し、滑らかな動きや収納構成を評価したという声が確認できます。一方、別の投稿ではアームのがたつきや高さ固定について触れられており、個別の使用感として整理します。",
            "negative": True,
            "fix_title": "キャスターとハンドルの確認を行う",
            "fix": "到着後は平らな場所でキャスターの動きとハンドルの固定を確認し、違和感があれば保証・交換条件に沿って販売元へ相談してください。",
        }, {
            "heading": "収納と外観を評価する利用者の声",
            "who": "楽天市場 C.jutro公式店の利用者の声（2025年7月投稿）",
            "text": "別の投稿では、外観の質感と収納力を評価する声が確認できます。見た目や収納の印象は荷物量・使い方で変わるため、個別の感想として扱います。",
            "negative": False,
            "fix_title": "機内持ち込み条件と荷物量を照合する",
            "fix": "航空会社の機内持ち込みサイズ規定と、実際に入れる荷物の量を照合してからサイズを選んでください。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://cjutro.jp/pages/chromelite",
            "title": "C.jutro公式 ChromeLite商品情報",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/euphoric/10000013/",
            "title": "楽天市場 C.jutro公式店 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/item/1/420106_10000035/1.1/",
            "title": "楽天市場 C.jutro公式店 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "tp-link-tapo-c200-amazon-alexa": {
        "official_url": "https://www.tp-link.com/jp/smart-home/tapo/tapo-c200/?app=t",
        "facts": [
            "TP-Link公式ページでTapo C200を商品同定し、1080p映像、パン360度・チルト114度、ナイトビジョン、動体検知通知、双方向通話を確認",
            "公式情報でmicroSDカードまたはクラウドによる録画、プライバシーゾーン、ベビークライ検知、自動追尾などの機能案内を確認。ただし利用可能な機能や保存条件はモデル・アプリ・契約条件を確認する",
            "楽天市場の個別商品ページでTapo C200（型番・JAN 6935364053239）を確認し、販売ページと記事の対象商品を照合",
            "個別の利用者の声では、初期設定のしやすさ、ペットや家族の見守り、夜間の見え方を評価する内容がある一方、アプリ操作や音声機能への不満もあるため、使用環境と個人差を分けて扱う",
        ],
        "review_texts": [{
            "source": "楽天市場 Tapo C200 個別商品レビュー",
            "text": "個別投稿では、設定が簡単だった、ペットや家族の様子を確認できる、夜間も見やすいという声が確認できます。一方で、アプリの操作や音声機能に関する不満もあります。映像の見え方や操作感は設置場所・通信環境・利用端末による個人の感想として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.tp-link.com/jp/smart-home/tapo/tapo-c200/?app=t",
            "title": "TP-Link公式 Tapo C200",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/tplinkdirect/6935364053239-new/?rafcid=wsc_i_is_162cb305-c486-48c9-910f-11a7c2915f08",
            "title": "楽天市場 TP-Link公式 Tapo C200 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/193345_12645010/1.1/",
            "title": "楽天市場 Tapo C200 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "200-bagin006": {
        "official_url": "https://direct.sanwa.co.jp/ItemPage/200-BAGIN006BK",
        "facts": [
            "サンワダイレクト公式商品ページで200-BAGIN006BKを商品同定し、5ポケット、ストラップ付き、内寸約21cm、奥行約11cmのガジェットポーチとして確認",
            "公式ページでACアダプタや大きめのモバイルバッテリーにも対応する収納部の案内を確認。ただし収納できるかは機器の形状・ケーブル長・厚みによる",
            "楽天市場とYahoo!ショッピングの個別商品ページで200-BAGIN006の販売情報を確認し、Amazon検索導線のJAN 4969887744758とも照合",
            "個別使用レビューでは、収納力や持ち運びやすさを評価する一方、長いケーブルや大きな機器では幅・深さが足りない場合があるという声があるため、収納物の寸法確認を購入前の条件にする",
        ],
        "review_texts": [{
            "source": "サンワダイレクト公式商品ページの利用者の声・個別使用レビュー",
            "text": "公式販売ページの利用者の声では、機器をまとめて持ち運べる点や収納のしやすさを評価する内容が確認できます。個別使用レビューでは、長いケーブルや大きな機器を入れる場合は幅・深さを確認したほうがよいという指摘もあります。収納量は中身の形状によって変わる個別の感想として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://direct.sanwa.co.jp/ItemPage/200-BAGIN006BK",
            "title": "サンワダイレクト公式 200-BAGIN006BK",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/sanwadirect/200-bagin006/?rafcid=wsc_i_is_162cb305-c486-48c9-910f-11a7c2915f08",
            "title": "楽天市場 サンワダイレクト 200-BAGIN006 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://yusukekitagawa.com/200-bakin006bk/",
            "title": "200-BAGIN006BK 個別使用レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "elecom-usb2-0hub-usb-tk-tcm012bk": {
        "official_url": "https://www.elecom.co.jp/products/TK-TCM012BK/TK-TCM012SV.html",
        "facts": [
            "エレコム公式ページでTK-TCM012BKを商品同定し、2ポートUSB2.0ハブ付きの有線テンキーボード、メンブレン方式、JAN 4953103550667を確認",
            "公式仕様でマウスなどUSB機器を2台まで接続できること、NumLock LED、最大1000万回のキーストロークに耐えるキーの案内を確認",
            "楽天市場の個別商品ページでTK-TCM012BKとJANを照合し、Amazon検索導線の対象商品と同一型番として整理",
            "個別レビューでは、テンキーのないPCで数字入力がしやすくなった、キー配列が使いやすいという声がある一方、接続環境やキーの好みは利用者によって異なるため、用途と端子条件を分けて扱う",
        ],
        "review_texts": [{
            "source": "楽天市場 TK-TCM012BK 個別商品レビュー",
            "text": "個別投稿では、テンキーのないPCで数字入力がしやすくなった、以前使っていた配列と近く使いやすいという内容が確認できます。使いやすさやキー入力の感触は、PCの配置・入力方法・個人の好みによる感想として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.elecom.co.jp/products/TK-TCM012BK/TK-TCM012SV.html",
            "title": "エレコム公式 TK-TCM012BK",
            "checked_at": "2026-10-06",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/webby/50212601/?rafcid=wsc_i_is_162cb305-c486-48c9-910f-11a7c2915f08",
            "title": "楽天市場 TK-TCM012BK 個別商品ページ",
            "checked_at": "2026-10-06",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/review/review/item/1/242953_10111527/1.1/",
            "title": "楽天市場 TK-TCM012BK 個別レビュー",
            "checked_at": "2026-10-06",
        }],
    },
    "rcp-3-recolte-capsule-cutter-bonne": {
        "official_url": "https://recolte-jp.com/products/capsule-cutter-bonne/",
        "facts": [
            "レコルト公式ページでカプセルカッター ボンヌ RCP-3を商品同定し、みじん切り・ペースト・大根おろし・メレンゲなど1台7役の案内を確認",
            "公式情報でRCP-3の用途と付属プレートの案内を確認。食材の量や状態によって仕上がりが変わるため、取扱説明書の使用条件を優先する",
            "楽天市場の個別商品ページでrecolte カプセルカッター ボンヌ RCP-3を確認し、記事の対象商品と照合",
            "個別投稿では、みじん切りや大根おろしを手軽にできる、思ったより容量があるという声がある一方、用途や食材量によって使い勝手が変わるため、容器容量と下ごしらえ量を購入前に確認する",
        ],
        "review_texts": [{
            "source": "楽天市場 RCP-3 個別商品レビュー",
            "text": "個別投稿では、玉ねぎのみじん切りや大根おろしが楽になった、思ったより容器が大きかったという声が確認できます。手軽さや容量の印象は、下ごしらえする食材・量・家庭の使い方による利用者の声として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://recolte-jp.com/products/capsule-cutter-bonne/",
            "title": "レコルト公式 カプセルカッター ボンヌ",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/roomy/win13jan15c01/?rafcid=wsc_i_is_162cb305-c486-48c9-910f-11a7c2915f08",
            "title": "楽天市場 RCP-3 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://item.rakuten.co.jp/roomy/win13jan15c01/",
            "title": "楽天市場 RCP-3 個別レビュー掲載ページ",
            "checked_at": "2026-10-07",
        }],
    },
    "yoh-200-yamazen": {
        "official_url": "https://book.yamazen.co.jp/product/detail/I00005725",
        "facts": [
            "山善公式商品情報でYOH-200を商品同定し、着脱式プレートの20穴たこ焼き器として確認",
            "公式仕様で幅30.5×奥行23.5×高さ8cm、重量1.2kg、AC100V、消費電力700W、電源コード約1.4mを確認",
            "公式情報でフッ素コーティングの着脱式プレート、串ガイド、1度に20個調理できる構成を確認",
            "楽天市場の個別レビューでは、注文から到着までの早さや焼き上がりを評価する声がある一方、端によって火力差を感じたという投稿もあるため、焼く量と焼き位置を購入判断に反映する",
        ],
        "review_texts": [{
            "source": "楽天市場 YOH-200 個別商品レビュー",
            "text": "個別投稿では、注文してすぐ届いた、全体的にきれいに焼けたという声が確認できます。一方で、プレートの端は火力が弱く感じたという投稿もあります。焼き上がりは食材の量・位置・電源環境による利用者の声として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://book.yamazen.co.jp/product/detail/I00005725",
            "title": "山善公式 YOH-200 商品情報",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/e-kurashi/1373959/?rafcid=wsc_i_is_162cb305-c486-48c9-910f-11a7c2915f08",
            "title": "楽天市場 YOH-200 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/205937_10000794/1.1/",
            "title": "楽天市場 YOH-200 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "mrpe-1260-soho-yamazen": {
        "official_url": "https://book.yamazen.co.jp/product/detail/I00008450",
        "product_url": "https://item.rakuten.co.jp/e-kurashi/1450620/",
        "thumb": "https://thumbnail.image.rakuten.co.jp/@0_mall/e-kurashi/cabinet/main-img/001/main-10549.jpg?_ex=128x128",
        "facts": [
            "山善公式商品情報ではMRPE-1260を幅120cm・奥行60cmのラック付きデスクとして案内している",
            "公式商品ページでは2口コンセントと左右入れ替え可能な収納ラックを案内している",
            "山善公式レビューでは、組み立てやすさ、広さ、ラックの圧迫感の少なさを評価する声がある一方、天板の凹凸には筆記用マットが必要という声もある"
        ],
        "review_texts": [{
            "source": "山善公式 MRPE-1260 個別レビュー",
            "text": "公式レビューでは、幅が広く使いやすい、組み立てが分かりやすい、ラックが部屋に圧迫感を与えにくいという声があります。一方、天板の凹凸が気になるため筆記時はマットが必要という声もあります。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://book.yamazen.co.jp/product/detail/I00008450",
            "title": "山善公式 MRPE-1260 商品情報",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/e-kurashi/1450620/",
            "title": "楽天市場 MRPE-1260 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://yamazenbizcom.jp/item_review.html?ITEM_CD=1450620",
            "title": "山善公式 MRPE-1260 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "ai-infield": {
        "official_url": "https://www.sportsinfield.com/product-page/%E6%9C%80%E5%A4%A71%E5%B9%B4%E4%BF%9D%E8%A8%BC-ai-%E4%BD%93%E9%87%8D%E8%A8%88-%E4%BD%93%E7%B5%84%E7%B9%94%E8%A8%88-%E6%9C%80%E5%85%88%E7%AB%AF%E3%83%87%E3%83%A5%E3%82%A2%E3%83%AB%E5%91%A8%E6%B3%A2%E6%95%B0%E6%90%AD%E8%BC%89%E3%83%97%E3%83%AC%E3%83%9F%E3%82%A2%E3%83%A0",
        "product_url": "https://store.shopping.yahoo.co.jp/comfortablegoods/weightscale.html",
        "thumb": "https://item-shopping.c.yimg.jp/i/g/comfortablegoods_weightscale",
        "facts": [
            "公式商品ページではINFIELD体組成計をスマートフォンアプリと連動して測定結果を確認する商品として案内している",
            "公式商品情報では測定範囲0.2〜150kg、登録人数無制限、体重・BMI・体脂肪率など44項目を案内している",
            "Yahoo!ショッピングの個別商品レビューでは、測定結果をアプリで管理できる点を評価する声がある一方、アプリの不具合や日による測定値の差を指摘する声もある"
        ],
        "review_texts": [{
            "source": "Yahoo!ショッピング INFIELD体組成計 個別レビュー",
            "text": "個別投稿では、体脂肪率や筋肉量などのデータをアプリで管理できる点が評価されています。一方、アプリの不具合が改善されたら連絡すると案内されたという投稿や、日によって測定値の差が大きいという投稿も確認できます。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.sportsinfield.com/product-page/%E6%9C%80%E5%A4%A71%E5%B9%B4%E4%BF%9D%E8%A8%BC-ai-%E4%BD%93%E9%87%8D%E8%A8%88-%E4%BD%93%E7%B5%84%E7%B9%94%E8%A8%88-%E6%9C%80%E5%85%88%E7%AB%AF%E3%83%87%E3%83%A5%E3%82%A2%E3%83%AB%E5%91%A8%E6%B3%A2%E6%95%B0%E6%90%AD%E8%BC%89%E3%83%97%E3%83%AC%E3%83%9F%E3%82%A2%E3%83%A0",
            "title": "INFIELD公式 体組成計 商品情報",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://store.shopping.yahoo.co.jp/comfortablegoods/weightscale.html",
            "title": "Yahoo!ショッピング INFIELD体組成計 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://shopping.yahoo.co.jp/review/item/list?page_key=weightscale&store_id=comfortablegoods",
            "title": "Yahoo!ショッピング INFIELD体組成計 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "arromic-st-x3ba": {
        "official_url": "https://www.yamazen-create.co.jp/uploads/post/650/2_1.pdf",
        "product_url": "https://item.rakuten.co.jp/bathroom/st-x3b/",
        "thumb": "https://thumbnail.image.rakuten.co.jp/@0_mall/bathroom/cabinet/0001/020/stx3ba_sm01b.jpg?_ex=128x128",
        "facts": [
            "商品資料ではアラミックの節水シャワープロ・プレミアム ST-X3B系として、アダプター4種付属を案内している",
            "価格.comの個別レビューでは、本体サイズ約64×239×62mm、重量152g、アダプター4種付属という情報が確認できる",
            "個別レビューでは片手で止水と水流調整ができる一方、水圧が低く感じる場合があるという声がある"
        ],
        "review_texts": [{
            "source": "価格.com アラミック ST-X3BA 個別レビュー",
            "text": "片手で止水とシャワーの強さを操作できる、強弱を調整できるという声がある一方、水圧が少々低い、水圧重視の人は注意という声もあります。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.yamazen-create.co.jp/uploads/post/650/2_1.pdf",
            "title": "商品資料 アラミック ST-X3B系",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/bathroom/st-x3b/",
            "title": "楽天市場 アラミック ST-X3BA 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://review.kakaku.com/review/S0000855568/ReviewCD%3D1478295/",
            "title": "価格.com ST-X3BA 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "tp-link-10gbps-lan-pci-e-tx401": {
        "official_url": "https://www.tp-link.com/jp/home-networking/pci-adapter/tx401/v1/",
        "product_url": "https://item.rakuten.co.jp/doriem/b08gfgg888/",
        "thumb": "https://thumbnail.image.rakuten.co.jp/@0_mall/doriem/cabinet/sn148/sn148_b08gfgg888.jpg?_ex=128x128",
        "facts": [
            "TP-Link公式ではTX401を10ギガビットPCIeネットワークアダプターとして案内している",
            "公式仕様ではPCI Express 3.0 x4、RJ45ポート、最大10Gbps、付属の1.5m CAT6Aケーブルを案内している",
            "公式ページではWindows 10・8.1・8対応、標準ブラケットとロープロファイルブラケットを案内している",
            "公式ページでは10Gbps通信時に高温になることがあるが仕様として案内している"
        ],
        "review_texts": [{
            "source": "TP-Link TX401 個別レビュー",
            "text": "個別レビューでは、10Gbps環境で速度やドライバー、PCIeスロットとの組み合わせが購入後の確認点になるという使用報告があります。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.tp-link.com/jp/home-networking/pci-adapter/tx401/v1/",
            "title": "TP-Link公式 TX401 商品情報・仕様",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/doriem/b08gfgg888/",
            "title": "楽天市場 TP-Link TX401 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://memotora.com/2021/06/09/review-tp-link-tx401/",
            "title": "TP-Link TX401 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "p10-yunth-c-c": {
        "official_url": "https://yunth.jp/shop/products/101-01",
        "product_url": "https://item.rakuten.co.jp/yunth/10000000/",
        "facts": [
            "Yunth公式商品ページでは生VC美白美容液を医薬部外品として案内し、有効成分にアスコルビン酸を記載している",
            "公式サイトでは水を使わず、生ビタミンCをフレッシュな状態で使用できる商品として案内している",
            "公式サイトでは開封後30秒を推奨使用期限として案内しているが、30秒を過ぎても品質に問題はないと説明している",
            "楽天市場の個別レビューでは、使用感や肌なじみについての利用者の投稿を確認できる"
        ],
        "review_texts": [{
            "source": "楽天市場 Yunth 生VC美白美容液 個別レビュー",
            "text": "楽天市場の個別投稿では、使用感や肌なじみについての感想が確認できます。医薬部外品の効能効果は公式表示の範囲で扱い、個人の感想から効果を断定しません。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://yunth.jp/shop/products/101-01",
            "title": "Yunth公式 生VC美白美容液 商品情報",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/yunth/10000000/",
            "title": "楽天市場 Yunth 生VC美白美容液 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/409735_10000000/2.1/",
            "title": "楽天市場 Yunth 生VC美白美容液 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "salonia": {
        "official_url": "https://salonia.jp/support/hair/iron/straight.php",
        "thumb": "https://item-shopping.c.yimg.jp/i/g/queensshop_main-sl-004",
        "product_url": "https://store.shopping.yahoo.co.jp/queensshop/main-sl-004.html",
        "facts": [
            "SALONIA公式FAQではSL-004のプレートが上下に動き、髪を強く挟みすぎない仕様として案内している",
            "公式取扱説明書では電源AC100V〜240V、最高温度約230℃、プレート幅15mm・24mm・35mmの各仕様を案内している",
            "公式FAQではメーカー保証期間を1年間と案内している",
            "Yahoo!ショッピングの個別商品レビューでは、前髪への使用で火傷が心配という声が確認できる"
        ],
        "review_texts": [{
            "source": "Yahoo!ショッピング SALONIA SL-004 個別レビュー",
            "text": "個別投稿では、カールとストレートの両用タイプを使っていたが、前髪では額を火傷しそうで心配なためストレート専用を再購入したという声があります。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://salonia.jp/support/hair/iron/straight.php",
            "title": "SALONIA公式 SL-004 FAQ",
            "checked_at": "2026-10-07",
        }, {
            "type": "official_manual",
            "url": "https://salonia.jp/wp-content/uploads/2021/07/straight.pdf",
            "title": "SALONIA公式 SL-004 取扱説明書・仕様",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://store.shopping.yahoo.co.jp/queensshop/main-sl-004.html",
            "title": "Yahoo!ショッピング SALONIA SL-004 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://shopping.yahoo.co.jp/products/p/84f7aad760",
            "title": "Yahoo!ショッピング SALONIA SL-004 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "xrs-d010": {
        "official_url": "https://www.plusminuszero.jp/faq/garment-steamer%EF%BC%88スタイルスチーマー%EF%BC%89/",
        "product_url": "https://item.rakuten.co.jp/roomy/pmz19jun27b01/",
        "facts": [
            "プラスマイナスゼロ公式FAQではXRS-D010をスタイルスチーマーとして案内し、スチームなしのプレス仕上げにも対応すると説明している",
            "楽天市場の個別商品ページではハンガーにかけたまま使える衣類スチーマーとしてXRS-D010を掲載している",
            "楽天市場の個別投稿では、起動が早くスチームのパワーを評価する声、手軽に気になる部分へアイロンできたという声が確認できる"
        ],
        "review_texts": [{
            "source": "楽天市場 ±0 XRS-D010 個別レビュー",
            "text": "個別投稿では、起動が早くスチームのパワーがある、手軽に気になる部分へアイロンできたという声があります。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://www.plusminuszero.jp/faq/garment-steamer%EF%BC%88スタイルスチーマー%EF%BC%89/",
            "title": "±0公式 XRS-D010 スタイルスチーマーFAQ",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/roomy/pmz19jun27b01/",
            "title": "楽天市場 ±0 XRS-D010 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/211966_10009678/1.1/",
            "title": "楽天市場 XRS-D010 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "simplus-sp-rcmc4": {
        "official_url": "https://simplus.style/sp-rcmc4/",
        "thumb": "https://thumbnail.image.rakuten.co.jp/@0_mall/rcmdin/cabinet/eb06/eb-4582226844157.jpg?_ex=128x128",
        "product_url": "https://item.rakuten.co.jp/rcmdin/eb-4582226844157/",
        "facts": [
            "simplus公式サイトではSP-RCMC4を4合炊きのマイコン式炊飯器として案内している",
            "公式サイトでは炊飯のほか、早炊き、蒸し料理、ヨーグルト、ケーキ、スープなど8種類のメニューに対応する機種として紹介している",
            "価格.comの個別レビューでは、調理完了後に保温へ切り替わり、12時間後に自動オフになるという情報が確認できる"
        ],
        "review_texts": [{
            "source": "価格.com simplus SP-RCMC4 個別レビュー",
            "text": "個別レビューでは、調理完了後に自動で保温へ切り替わり、12時間経過すると自動オフになるという使用情報が確認できます。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://simplus.style/sp-rcmc4/",
            "title": "simplus公式 SP-RCMC4 商品情報",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/rcmdin/eb-4582226844157/",
            "title": "楽天市場 simplus SP-RCMC4 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://review.kakaku.com/review/J0000035145/",
            "title": "価格.com simplus SP-RCMC4 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "rsb-4-recolte": {
        "official_url": "https://recolte-jp.com/admin/wp-content/uploads/2023/01/RSB-4_Manual_4.pdf",
        "product_url": "https://item.rakuten.co.jp/aimere/r006003/",
        "facts": [
            "レコルト公式取扱説明書ではソロブレンダー シエル、品番RSB-4として案内している",
            "公式仕様では容量約300ml、消費電力170W、ボトルはAS樹脂、付属品にボトル・パッキン・フタ・キャップ・ボトル台座がある",
            "楽天市場の個別投稿では、1人分のスムージーに十分なサイズ、氷や冷凍フルーツを撹拌できる、洗いやすいという声がある一方、パッキンの装着やコード長を気にする声もある"
        ],
        "review_texts": [{
            "source": "楽天市場 レコルト RSB-4 個別レビュー",
            "text": "個別投稿では、1人分のスムージーに十分なサイズ、氷や冷凍フルーツも撹拌できる、洗い物が楽という声があります。一方、パッキンがうまくはまらず漏れたという声や、コード長を気にする声も確認できます。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://recolte-jp.com/admin/wp-content/uploads/2023/01/RSB-4_Manual_4.pdf",
            "title": "レコルト公式 RSB-4 取扱説明書・仕様",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/aimere/r006003/",
            "title": "楽天市場 レコルト RSB-4 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/220207_10002736/1.0/",
            "title": "楽天市場 RSB-4 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "usb-wifi-5ghz-sd-mf45a-secustation": {
        "official_url": "https://bs.secu.jp/view/item/000000000285?category_page_id=ct45",
        "product_url": "https://item.rakuten.co.jp/secupcs/001-001/",
        "facts": [
            "公式商品ページではMF45Aを500万画素のパンチルトカメラ、自動追跡対応として案内している",
            "公式商品ページでは屋内・屋外での利用、5GHz Wi-Fi、microSDカード録画、無料クラウド録画などを案内している",
            "楽天市場の個別投稿では、本体が軽く画質も十分という声、自動追尾と設置のしやすさを評価する声がある一方、アプリ設定に戸惑ったという声も確認できる"
        ],
        "review_texts": [{
            "source": "楽天市場 SecuSTATION MF45A 個別レビュー",
            "text": "本体が軽く小さい、画質も十分という投稿や、自動追尾を試すため購入し設置できたという投稿があります。一方、アプリの使い方が分かりにくく慣れるまで戸惑ったという声もあります。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://bs.secu.jp/view/item/000000000285?category_page_id=ct45",
            "title": "SecuSTATION公式 MF45A 商品情報",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/secupcs/001-001/",
            "title": "楽天市場 SecuSTATION MF45A 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/300680_10000003/1.1/",
            "title": "楽天市場 MF45A 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "db74-secustation": {
        "official_url": "https://bs.secu.jp/view/item/000000000339?category_page_id=scview",
        "product_url": "https://item.rakuten.co.jp/secupcs/001-mu72/",
        "facts": [
            "公式商品ページではDB74をバッテリー内蔵の屋外対応ワイヤレスネットワークカメラとして案内している",
            "公式ページではスマートフォンから録画映像を確認でき、タイムラインで再生できると案内している",
            "公式ストアの商品情報ではソーラーパネルや設置用品などの構成を選択できる商品として掲載されている",
            "楽天市場の個別投稿では、充電後に動画を見ながら設定できた、ベランダへの設置に使ったという声がある一方、認証コードやWi-Fi設定時の画面が説明書と異なったという声、電源ボタンが故障して買い替えたという声も確認できる"
        ],
        "review_texts": [{
            "source": "楽天市場 セキュガードD コードレス DB74 個別レビュー",
            "text": "個別投稿では、充電後に動画を見ながら設定できた、ベランダへの設置に使ったという声があります。一方、認証コードやWi-Fi設定時の画面が説明書と異なったという声、電源ボタンが故障して買い替えたという声も確認できます。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://bs.secu.jp/view/item/000000000339?category_page_id=scview",
            "title": "SecuSTATION公式 DB74 商品情報",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/secupcs/001-mu72/",
            "title": "楽天市場 セキュガードD コードレス DB74 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/300680_10000311/1.1/",
            "title": "楽天市場 DB74 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "d-dc53": {
        "official_url": "https://bs.secu.jp/view/item/000000000365",
        "product_url": "https://bs.secu.jp/view/item/000000000365",
        "yahoo_url": "https://bs.secu.jp/view/item/000000000365",
        "facts": [
            "公式商品ページではSC-DC53(B)を300万画素の屋内向けカメラとして案内している",
            "水平79度・垂直40度・対角95度の撮影画角、暗視は最大15mと案内されている",
            "マイクとスピーカーを内蔵し、スマートフォン・パソコンから映像を確認できる",
            "録画媒体はmicroSDカード（最大128GB、FAT32、Class10）に対応し、クラウド録画は有料オプションとして案内されている"
        ],
        "review_texts": [{
            "source": "楽天市場 カメまるD DC53B 個別商品レビュー",
            "text": "DC53Bを選択した利用者の投稿では、設定は簡単で画像も十分という声が確認できます。一方、アカウント登録やVPN接続の待ち時間、説明書との違いに戸惑ったという声もあります。"
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://bs.secu.jp/view/item/000000000365",
            "title": "SecuSTATION公式 SC-DC53(B) 商品情報",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://bs.secu.jp/view/item/000000000365",
            "title": "SecuSTATION公式 SC-DC53(B) 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/300680_10000206/2.1/",
            "title": "楽天市場 カメまるD DC53B 個別レビュー",
            "checked_at": "2026-10-07",
        }],
    },
    "vgp2022-bluetooth-funlogy-portable-tws-ip67": {
        "official_url": "https://funlogy.jp/collections/speaker/products/funlogy-portable",
        "product_url": "https://item.rakuten.co.jp/entamefactory/funlogy_portable/",
        "thumb": "https://funlogy.jp/cdn/shop/files/portable_black_01.jpg",
        "facts": [
            "FUNLOGY公式商品ページでモデル名をFUNLOGY Portableとして同定",
            "公式仕様で本体サイズ184×50×63mm、重量460g、出力5W×2、Bluetooth 5.3、連続再生12時間（50%出力時）、IPX7、防水、TWS、USB Type-C・AUX・microSD入力を確認",
            "公式の付属品案内でUSB Type-Cケーブル、3.5mm AUXケーブル、取扱説明書（保証書）を確認",
            "楽天市場のFUNLOGY公式ショップ個別商品ページで同一モデルを確認し、レビュー本文では動画や会話の聞き取りやすさ、持ち運びやすさ、音量・音質への評価と、用途によっては上位機との差を感じるという声を確認",
        ],
        "review_texts": [{
            "source": "楽天市場 FUNLOGY公式ショップ 個別商品レビュー",
            "text": "個別投稿では、人の声や会話が聞き取りやすく動画視聴にも向くという感想、持ち運んで複数の場所で使えるという感想が確認できます。一方で、音質は価格帯相応と感じる投稿もあるため、動画・ラジオ・屋外利用を重視するか、音楽の細かな表現を重視するかで評価が分かれる商品として扱います。",
        }],
        "source_notes": [{
            "type": "official_product",
            "url": "https://funlogy.jp/collections/speaker/products/funlogy-portable",
            "title": "FUNLOGY公式 FUNLOGY Portable 商品仕様",
            "checked_at": "2026-10-07",
        }, {
            "type": "product_page",
            "url": "https://item.rakuten.co.jp/entamefactory/funlogy_portable/",
            "title": "楽天市場 FUNLOGY公式ショップ FUNLOGY Portable 個別商品ページ",
            "checked_at": "2026-10-07",
        }, {
            "type": "review_page",
            "url": "https://review.rakuten.co.jp/item/1/333397_10000434/1.1/",
            "title": "楽天市場 FUNLOGY Portable 個別レビュー",
            "checked_at": "2026-10-07",
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
