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
