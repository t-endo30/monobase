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
     あわせて楽天のジャンル別ランキングAPIから「今売れている」商品も
     取り、レビュー件数の少ない新商品も拾えるようにする（--no-trending
     で止められる）。ランキング由来と通常の候補は交互に並べて出すので、
     1回の実行で作る本数が少なくても、話題のものと定番のものが
     両方混ざる（片方だけに偏らせない）。
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
import json, io, os, re, sys, time, argparse, collections, zlib, datetime
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


def fits_category(name, cat, extra=None):
    """商品名が、そのカテゴリーの品物を指しているか。

       extra には、そのとき引いたサブ区分の検索語を渡す。CATEGORY_WORDS は
       カテゴリー全体をざっくり見分けるための語しか持っていないので、
       サブ単位で引くようになると、そのサブの品物がここで落ちてしまう
       （「保存容器」「水槽」「園芸用品」「電動歯ブラシ」「液晶テレビ」は
       どれも CATEGORY_WORDS に無く、実際に候補が1件も通らなかった）。
       サブの検索語はそのサブの品物そのものを指しているので、
       見分け語として足して扱う。

       CATEGORY_EXCLUDE は extra に関係なく効かせる。こちらは
       「衣類アイロンとヘアアイロン」のような取り違えを止めるためのもので、
       サブを指定したからといって緩めてよい種類の判定ではない。"""
    low = str(name or "").lower()
    if any(x.lower() in low for x in CATEGORY_EXCLUDE.get(cat, [])):
        return False
    words = list(CATEGORY_WORDS.get(cat) or []) + list(extra or [])
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
# 総合順（今の売れ行きに近い枠）から来た商品の下限。伸びている新商品ほど
# レビューが少ないので MIN_REVIEWS は当てないが、0件まで通すと
# 「レビューが1件も無い無名品」がそのまま候補に入る（2026-09-27の実機
# 確認で、上位10件のうち4件がレビュー0件だった）。本文を書いてから
# 校閲で破棄するのが一番高くつくので、ここで薄く下限を引く。
# 2026-10-01：5 → 30。build.py の indexable() は口コミ30件未満の記事を
# noindex にするため、それ未満の商品で書いても AdSense の審査では
# 「有用性の低いページ」の側に数えられ、1日の本数にも入らない
# （schedule_gate.py は index される記事だけを数える）。
MIN_REVIEWS_TRENDING = 30
MIN_RATING = 3.6
# 価格帯。極端に安い物はレビューが機能せず、高すぎる物は読者層と合わない。
MIN_PRICE = 1500
MAX_PRICE = 120000

# 1カテゴリーが候補全体に占められる割合の上限。
# これを入れる前は、12カテゴリー分の候補をまとめてレビュー件数の降順に
# 並べて上から切っていたため、レビュー件数が桁違いに多いジャンル
# （PC周辺機器・美容家電）が候補を独占していた。2026-09-27時点で
# 公開144本のうちパソコンが30本（21%）、直近30本では13本（43%）まで
# 偏り、ホームの新着枠がPCアクセサリだけで埋まっていた。
CATEGORY_SHARE = 0.25

# クールダウンで見る「直近の公開記事」の本数。
# ここに多く出ているカテゴリーほど、次の候補では後ろに回す。
COOLDOWN_RECENT = 30

# サブ区分のクールダウンで見る本数。カテゴリー（12個）より対象が
# 広い（67個）ので、同じ30本だとほとんどのサブが0で横並びになる。
SUB_COOLDOWN_RECENT = 120

# 1回の実行で引くサブ区分の数と、1カテゴリーから取るサブの上限。
# 67個すべてを毎回引くと、楽天の1秒1回制限で候補集めに4〜6分かかる。
# 1回に書くのは最大2本なので、記事の少ないサブから順に少しずつ引いて、
# 日をまたいで一周させる。
SUBS_PER_RUN = 14
SUBS_PER_CATEGORY = 2

# サイトのカテゴリーと、楽天のジャンルID／Yahoo!の検索語の対応。
# 楽天のジャンルIDは https://webservice.rakuten.co.jp/documentation/ で調べられる。
#
# subs は content/site.json のサブ区分と同じキーで、そのサブを指す検索語。
# ジャンルIDはカテゴリーに1つのままで、サブは**検索語で絞る**
# （2026-09-27、ユーザー判断）。サブごとにジャンルIDを割り当てる案もあったが、
#   ・保守対象が12個から67個に増える。ジャンルIDは改編で消える
#     （2026年2月の刷新で楽天ランキングAPIが丸ごと消えた前例がある）
#   ・サブ単位のジャンルIDを調べる IchibaGenre/Search が刷新後も
#     生きているか確認できていない
# ため、まず検索語で回して効果を測ることにした。検索語は腐らない。
# 取りこぼしが実際に問題になったら、ジャンルIDに移す。
#
# **ここを直す前に content/site.json の sub と突き合わせること。**
# キーがずれると、そのサブは永久に候補が作られない（起動時に検算する）。
CATEGORY_MAP = {
    "pc": {
        "rakuten_genre": 100026, "words": ["PC周辺機器"],
        "subs": {
            "laptop":     ["ノートパソコン", "ノートPC"],
            "tablet":     ["タブレット", "電子書籍リーダー"],
            "monitor":    ["モニター", "ディスプレイ", "モニターアーム"],
            "input":      ["キーボード", "マウス", "トラックボール"],
            "peripheral": ["USBハブ", "ドッキングステーション", "webカメラ"],
            "storage":    ["外付けSSD", "外付けHDD", "SDカード"],
            "network":    ["無線LANルーター", "Wi-Fiルーター", "LANケーブル"],
            "parts":      ["CPUクーラー", "グラフィックボード", "PCケース", "電源ユニット"],
            "software":   ["セキュリティソフト", "Office ソフト"],
        },
    },
    "appliance": {
        "rakuten_genre": 562637, "words": ["生活家電"],
        "subs": {
            "aircon":  ["扇風機", "サーキュレーター", "加湿器", "除湿機", "ヒーター"],
            "clean":   ["掃除機", "ロボット掃除機", "スティック掃除機"],
            "laundry": ["洗濯機", "衣類乾燥機", "衣類スチーマー"],
            "light":   ["シーリングライト", "デスクライト", "センサーライト"],
            "smart":   ["スマートリモコン", "スマートプラグ", "スマートスピーカー"],
            "power":   ["ポータブル電源", "乾電池", "充電池"],
        },
    },
    "furniture": {
        "rakuten_genre": 100804, "words": ["インテリア 収納"],
        "subs": {
            "desk":  ["デスク", "昇降デスク", "パソコンデスク"],
            "chair": ["オフィスチェア", "ゲーミングチェア", "スツール"],
            "shelf": ["収納ラック", "本棚", "チェスト"],
            "bed":   ["マットレス", "敷布団", "枕"],
            "deco":  ["カーテン", "ラグ", "クッション"],
        },
    },
    "daily": {
        "rakuten_genre": 215783, "words": ["日用品"],
        "subs": {
            "storage":    ["収納ボックス", "収納ケース"],
            "clean":      ["洗剤", "掃除用品", "スポンジ"],
            "bath":       ["シャワーヘッド", "バスマット", "トイレブラシ"],
            "safety":     ["防災セット", "防犯カメラ", "非常用持ち出し袋"],
            "misc":       ["タオル", "傘", "水筒"],
            "fashion":    ["腕時計", "サングラス"],
            "tool":       ["電動ドライバー", "工具セット", "脚立"],
            "garden":     ["園芸用品", "プランター", "高圧洗浄機"],
            "hobby":      ["ゲーミング", "ボードゲーム", "プラモデル"],
            "car":        ["ドライブレコーダー", "カーチャージャー", "車載ホルダー"],
            "outdoor":    ["テント", "寝袋", "アウトドアチェア"],
            "stationery": ["シュレッダー", "ラミネーター", "文房具セット"],
        },
    },
    "av": {
        "rakuten_genre": 211742, "words": ["オーディオ"],
        "subs": {
            "headphone": ["ワイヤレスイヤホン", "ヘッドホン", "骨伝導イヤホン"],
            "speaker":   ["Bluetoothスピーカー", "サウンドバー"],
            "tv":        ["液晶テレビ", "プロジェクター"],
            "mic":       ["コンデンサーマイク", "USBマイク", "オーディオインターフェース"],
        },
    },
    "camera": {
        "rakuten_genre": 204040, "words": ["カメラ"],
        "subs": {
            "body":   ["ミラーレス一眼", "デジタルカメラ", "アクションカメラ"],
            "lens":   ["カメラ レンズ", "単焦点レンズ", "望遠レンズ"],
            "security": ["見守りカメラ", "防犯カメラ", "ベビーモニター"],
            "tripod": ["三脚", "ジンバル", "自撮り棒"],
            "acc":    ["カメラバッグ", "SDカード カメラ", "ストロボ"],
        },
    },
    "smartphone": {
        "rakuten_genre": 565004, "words": ["スマートフォン アクセサリ"],
        "subs": {
            "body":    ["SIMフリースマホ", "スマートフォン 本体"],
            "case":    ["スマホケース", "ガラスフィルム"],
            "charger": ["モバイルバッテリー", "USB充電器", "MagSafe 充電"],
            "acc":     ["スマホスタンド", "スマホリング", "車載ホルダー スマホ"],
        },
    },
    "kitchen": {
        "rakuten_genre": 100644, "words": ["キッチン家電"],
        "subs": {
            "appliance": ["電気ケトル", "炊飯器", "electric トースター", "コーヒーメーカー"],
            "tool":      ["フライパン", "包丁", "圧力鍋"],
            "ware":      ["保存容器", "食器セット", "タンブラー"],
            "storage":   ["キッチン収納", "water 調味料ラック", "水切りラック"],
        },
    },
    "health": {
        "rakuten_genre": 100938, "words": ["健康計測"],
        "subs": {
            "measure":    ["体組成計", "血圧計", "スマートウォッチ"],
            "care":       ["マッサージガン", "フォームローラー", "マッサージチェア"],
            "supplement": ["プロテイン", "サプリメント"],
            "hygiene":    ["電動歯ブラシ", "口腔洗浄器", "体温計"],
        },
    },
    "beauty": {
        "rakuten_genre": 100939, "words": ["美容家電"],
        "subs": {
            "skincare": ["化粧水", "美容液", "日焼け止め"],
            "haircare": ["シャンプー", "ヘアオイル", "トリートメント"],
            "makeup":   ["マスカラ", "アイブロウ", "ファンデーション"],
            "device":   ["ドライヤー", "ヘアアイロン", "美顔器", "脱毛器"],
            "shave":    ["電気シェーバー", "メンズシェーバー", "眉毛シェーバー"],
        },
    },
    "pet": {
        "rakuten_genre": 101213, "words": ["ペット用品"],
        "subs": {
            "dog":  ["犬 ハーネス", "犬 ベッド", "ペットカート"],
            "cat":  ["猫 トイレ", "キャットタワー", "猫 爪とぎ"],
            "food": ["ドッグフード", "キャットフード", "ペット おやつ"],
            "care": ["ペット 爪切り", "ペットブラシ", "ペットシーツ"],
            "aqua": ["水槽", "アクアリウム", "小動物 ケージ"],
        },
    },
    "fashion": {
        "rakuten_genre": 100371, "words": ["メンズファッション"],
        "subs": {
            "shoes": ["スニーカー", "ビジネスシューズ", "サンダル"],
            "bag":   ["リュック", "ビジネスバッグ", "財布"],
            "watch": ["腕時計 メンズ", "腕時計 レディース"],
            "acc":   ["ベルト", "帽子", "マフラー"],
            "wear":  ["シャツ", "ジャケット", "インナー"],
        },
    },
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


def rakuten_ranking(app_id, access_key=None, genre=None, hits=10):
    """楽天ジャンル別ランキングAPI。売れ筋の実際の順位を取る。

       商品検索API（IchibaItem/Search）と同じ楽天ウェブサービスの
       ファミリーなので、URLの形・認証（Origin/Referer・accessKey）は
       商品検索と同じにしてある。2026年2月の刷新でエンドポイントの
       ドメインが変わった経緯があるため、ここが弾かれるようになったら
       まずURLのバージョン・ドメインを商品検索API側の最新と見比べる
       こと（呼び出し側は失敗しても検索結果だけで動けるようにしてある）。

       「話題性」までは分からないが、レビュー件数（=これまでの累計）
       とは別の切り口で、直近の売れ行きを拾える。"""
    q = {
        "applicationId": app_id,
        "format": "json",
        "formatVersion": 2,
    }
    if genre:
        q["genreId"] = genre
    head = {"Origin": RAKUTEN_ORIGIN, "Referer": RAKUTEN_ORIGIN + "/"}
    if access_key:
        head["accessKey"] = access_key
    url = RAKUTEN_API.replace("IchibaItem/Search", "IchibaItem/Ranking")
    data = get_json(url + "?" + urllib.parse.urlencode(q), head)
    out = []
    for w in (data.get("Items") or data.get("items") or [])[:hits]:
        it = w.get("Item") or w.get("item") or w
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
            "image": _rakuten_image(it),
            "rank": int(w.get("rank") or it.get("rank") or 0),
        })
    return out


def rakuten_search(app_id, access_key=None, genre=None, keyword=None, jan=None,
                   hits=30, sort="-reviewCount", item_code=None):
    """楽天商品検索API。JANを渡すときは keyword に入れる（専用の欄がない）。
       アクセスキーはURLに載せず、accessKey ヘッダで送る。

       item_code は「店舗コード:商品コード」（コロン区切り）。これを渡すと
       その商品だけが返るので、検索語での取り違えが起きない。

       **itemCode を渡すときは、絞り込みの欄を一緒に送らない。**
       hits・sort・imageFlag・availability を添えると楽天は
       `HTTP 400: itemCode is not valid` を返す（2026-09-27、
       177本中130本がこれで取れなかった）。itemCode は1件を名指しする
       指定なので、並べ替えも在庫の絞り込みも意味を持たない。
       取れなかった場合は結果が空になるので、呼ぶ側で次の手に進むこと。"""
    if item_code:
        q = {
            "applicationId": app_id,
            "format": "json",
            "formatVersion": 2,
            "itemCode": item_code,
        }
    else:
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


# 型番らしいトークン（英字+ハイフン+英数字、数字を含む）を拾う。
# 「レコルト RSY-2」のように、店舗ごとに商品名の言い回しが違っても
# 型番の表記だけはほぼ共通して残ることを利用して、同一商品の判定に使う。
# USB-C・Wi-Fi のような規格名は数字を含まないため拾わない。
_MODEL_CODE_RE = re.compile(r"[A-Za-z]{1,8}-[A-Za-z0-9]{1,8}")


def model_codes(text):
    """商品名・記事題名から型番コードを抜き出す（大文字に揃えて返す）。
       2026-09-18、同じ「レコルトRSY-2」が別ショップのURL違いで
       6本も記事化される事故があり、item_key（URL単位）だけでは
       同一商品を見分けられないと分かったため追加した。"""
    return {m.upper() for m in _MODEL_CODE_RE.findall(str(text or ""))
            if any(ch.isdigit() for ch in m)}


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


def recent_category_load(arts, n=COOLDOWN_RECENT):
    """直近に公開した n 本のカテゴリー分布を数える。

       候補を選ぶ順番をここで決める（多く書いたカテゴリーほど後ろに回す）。
       下書きのままの記事は数えない。公開まで至らなかったものを
       「もう十分書いた」と見なすと、書けないカテゴリーばかりが
       いつまでも先頭に来てしまうため。"""
    pub = [a for a in arts if a.get("published")]
    pub.sort(key=lambda a: (str(a.get("date") or ""), str(a.get("slug") or "")))
    return collections.Counter(a.get("category", "") for a in pub[-n:])


def recent_sub_load(arts, n=SUB_COOLDOWN_RECENT):
    """直近に公開した n 本の「カテゴリー/サブ」分布を数える。

       カテゴリー単位のクールダウンだけでは、同じカテゴリーの中の偏りは
       直らない。実際 pc は9個あるサブのうち「周辺機器・USBハブ」に24本、
       サイト全体では75個あるサブの26個（35%）が記事0本だった
       （2026-09-27）。ここは記事0本のサブが先頭に来るように数える。

       カテゴリーと違って範囲が広い（75個）ので、見る本数も広く取る。
       直近30本では、ほとんどのサブが0のまま横並びになってしまう。"""
    pub = [a for a in arts if a.get("published")]
    pub.sort(key=lambda a: (str(a.get("date") or ""), str(a.get("slug") or "")))
    return collections.Counter(
        (a.get("category", ""), a.get("sub", "")) for a in pub[-n:])


def plan_targets(categories, arts, subs_per_run, per_cat_subs=SUBS_PER_CATEGORY):
    """今回どの「カテゴリー/サブ」を引くかを決める。

       サブを全部（67個）毎回引くと、楽天の1秒1回制限で候補集めだけに
       4〜6分かかる。1回の実行で書くのは最大2本なので、そこまで引く
       必要がない。**記事の少ないサブから順に、今回ぶんだけ引く**。
       書いたサブは次の実行で後ろへ回るので、日をまたいで一周する。

       同じ本数のサブが並んだときは、日付で決まる順に回す。こうしないと
       候補が集まらないサブ（母数が小さく MIN_REVIEWS を超える商品が
       無いサブ）が毎回先頭に居座り、他のサブがいつまでも引かれない。
       日替わりにしておけば、1日1回ずつ順に試されて全体が回る。

       1カテゴリーから取るサブは per_cat_subs 個まで。日用品・雑貨は
       サブが12個あるので、上限が無いと1カテゴリーで枠を使い切る。"""
    recent = recent_sub_load(arts)
    day = int(datetime.date.today().strftime("%j"))
    pairs = []
    for cat in categories:
        conf = CATEGORY_MAP.get(cat) or {}
        for sub, words in (conf.get("subs") or {}).items():
            if not words:
                continue
            # 同数のときの並び。crc32 を使うのは、Python の hash() が
            # 実行ごとに変わる（文字列はソルト付き）ため。日を足して
            # 剰余を取ることで、同数のサブが日替わりで前後する。
            spin = (zlib.crc32(f"{cat}/{sub}".encode("utf-8")) + day) % 997
            pairs.append((recent.get((cat, sub), 0), spin, cat, sub, words))
    pairs.sort()

    taken, per_cat = [], collections.Counter()
    for _n, _spin, cat, sub, words in pairs:
        if per_cat[cat] >= per_cat_subs:
            continue
        per_cat[cat] += 1
        taken.append((cat, sub, words))
        if len(taken) >= subs_per_run:
            break
    return taken, recent


def check_subs():
    """CATEGORY_MAP の subs が content/site.json のサブ区分と合っているか。

       合っていないキーを説明つきで返す（空なら問題なし）。
       サイト側のサブを増やしたとき、ここへ検索語を足し忘れると、
       そのサブは候補が永久に作られないまま「記事0本」としてクールダウンの
       先頭に居座り、他のサブの番を毎回奪ってしまう。"""
    site = json.load(io.open(os.path.join(ROOT, "content", "site.json"),
                             encoding="utf-8"))
    known = {c["key"]: {s["key"] for s in c.get("sub", [])}
             for c in site.get("categories", [])}
    bad = []
    for cat, conf in CATEGORY_MAP.items():
        want = known.get(cat)
        if want is None:
            bad.append(f"CATEGORY_MAP の {cat} が content/site.json にありません")
            continue
        have = set((conf.get("subs") or {}))
        for x in sorted(have - want):
            bad.append(f"{cat}/{x} は content/site.json に無いサブ区分です"
                       "（CATEGORY_MAP の subs から消すか、綴りを直してください）")
        for x in sorted(want - have):
            bad.append(f"{cat}/{x} に検索語がありません"
                       "（CATEGORY_MAP の subs に足してください）")
    return bad


def build_candidates(rakuten_id, rakuten_key, yahoo_id, categories,
                     limit, per_category, trending=True,
                     subs_per_run=SUBS_PER_RUN):
    arts = json.load(io.open(os.path.join(ROOT, "content", "articles.json"),
                             encoding="utf-8"))
    seen_jan, _ = known_products(arts)
    seen_names = {clean_name(a.get("title", ""))[:20] for a in arts}
    seen_items = known_items(arts)
    # 記事の題名から拾った型番の集合。seen_names は自分たちが書いた
    # 題名の先頭20文字と、モールの生の商品名を比べているだけなので、
    # 言い回しが違うとすり抜ける（実際にすり抜けて同一商品が6本
    # できた）。型番はどちらの文字列にも残りやすいので、もう1段
    # 別の切り口で見る。
    seen_models = set()
    for a in arts:
        seen_models |= model_codes(a.get("title", ""))

    # 今回引く「カテゴリー/サブ」を決める。サブを全部引くと時間が
    # かかりすぎるので、記事の少ないサブから順に少しずつ引く。
    targets, recent_sub = plan_targets(categories, arts, subs_per_run)
    if not targets:
        print("::warning::引けるサブ区分がありません"
              "（CATEGORY_MAP の subs を確認してください）", file=sys.stderr)
    print(f"今回引くサブ区分 {len(targets)} 件"
          f"（直近{SUB_COOLDOWN_RECENT}本での本数が少ない順）：")
    for cat, sub, words in targets:
        print(f"  {cat}/{sub:11s} 直近{recent_sub.get((cat, sub), 0):2d}本  "
              f"検索語「{words[0]}」")
    print()

    out = []
    ranking_failed = []
    # 「今売れている枠」はカテゴリー単位で1回だけ引く。サブごとに引くと
    # 呼び出し回数が倍近くになるわりに、同じジャンルの総合順が返るだけで
    # 中身がほとんど重なる。
    # 2026年2月の刷新後、ランキングAPI（IchibaItem/Ranking）は新しい
    # ドメインに存在せず、全カテゴリーが404を返す状態が続いている
    # （2026-09-19に確認。版・パスを変えても404）。生きているかだけは
    # 1回だけ確かめて、駄目なら以降は呼ばない。カテゴリーやサブごとに
    # 呼ぶと、返ってこないと分かっている404を毎回叩くことになる。
    ranking_alive = bool(trending and rakuten_id)
    if ranking_alive:
        try:
            rakuten_ranking(rakuten_id, rakuten_key,
                            genre=next(iter(CATEGORY_MAP.values()))["rakuten_genre"],
                            hits=1)
            print("楽天ランキングAPIが復活しています（この行が出たら、"
                  "サブ区分ごとのランキング取得を入れ直す価値があります）")
        except Exception:                                    # noqa: BLE001
            ranking_alive = False
            ranking_failed.append("ranking")
        time.sleep(PAUSE)

    for cat, sub, sub_words in targets:
        conf = CATEGORY_MAP.get(cat)
        if not conf:
            print(f"::warning::カテゴリー {cat} の対応表がありません", file=sys.stderr)
            continue

        # 登録されているモールを両方とも検索して結果を合わせる。
        # 片方だけを見ると、そのモールにしか無い商品を取りこぼす。
        found = []
        if trending and rakuten_id:
            # 「今の売れ行き」に近い枠。レビュー件数順（＝累計の人気）
            # だけで埋めると、レビュー件数を売り文句にした無名品ばかりが
            # 上位に来る（2026-09-18〜19に、候補6件すべてが型番不明で
            # 破棄され公開0本になった）。
            #
            # ランキングAPIが死んでいるので、楽天の既定の並び
            # （standard＝総合順）で代用する。**サブの検索語を付けて引く**
            # ——カテゴリー単位で引くと、返ってきた商品にそのとき処理中の
            # サブの札が付いてしまう（実際「appliance/smart」に
            # エアコンの配管化粧カバーが入った）。
            rank = []
            try:
                rank = rakuten_search(rakuten_id, rakuten_key,
                                      genre=conf["rakuten_genre"],
                                      keyword=sub_words[0],
                                      hits=10, sort="standard")
            except Exception as ex2:                     # noqa: BLE001
                print(f"::warning::楽天の総合順の取得に失敗（{cat}/{sub}）: {ex2}",
                      file=sys.stderr)
            for e in rank:
                e["trending"] = True
            found += rank
            time.sleep(PAUSE)
        # ジャンルはカテゴリー単位のまま、サブは検索語で絞る。
        # ジャンルだけで引くと、そのジャンルでレビュー件数の多い商品
        # （＝安価なアクセサリ）ばかりが返り、ノートPC・モニターの
        # ような単価の高い商品にたどり着けない。
        kw = sub_words[0]
        if rakuten_id:
            try:
                found += rakuten_search(rakuten_id, rakuten_key,
                                        genre=conf["rakuten_genre"],
                                        keyword=kw, hits=per_category)
            except Exception as ex:                       # noqa: BLE001
                # ジャンルは改編される。弾かれたら検索語だけで探し直す。
                if "genre" in str(ex).lower():
                    time.sleep(PAUSE)
                    try:
                        found += rakuten_search(rakuten_id, rakuten_key,
                                                keyword=kw, hits=per_category)
                    except Exception as ex2:              # noqa: BLE001
                        print(f"::warning::楽天の検索に失敗（{cat}/{sub}）: {ex2}",
                              file=sys.stderr)
                else:
                    print(f"::warning::楽天の検索に失敗（{cat}/{sub}）: {ex}",
                          file=sys.stderr)
            time.sleep(PAUSE)
        if yahoo_id:
            try:
                found += yahoo_search(yahoo_id, query=kw, hits=per_category)
            except Exception as ex:                       # noqa: BLE001
                print(f"::warning::Yahoo!の検索に失敗（{cat}/{sub}）: {ex}",
                      file=sys.stderr)
            time.sleep(PAUSE)

        # レビューの多い順に混ぜる。モールごとに固まらないようにする。
        found.sort(key=lambda e: -e["reviews"])

        for e in found:
            # 総合順（今売れている枠）の商品は、レビュー件数の下限を
            # 緩める。伸びている新商品ほどレビューが少ないため、
            # MIN_REVIEWS をそのまま当てると「話題のものを優先する」
            # 意味が無くなる。ただし0件まで通すと無名品がそのまま入る。
            # 評価（星）の下限は、粗悪品を混ぜないために外さない。
            floor = MIN_REVIEWS_TRENDING if e.get("trending") else MIN_REVIEWS
            if e["reviews"] < floor:
                continue
            if e["rating"] and e["rating"] < MIN_RATING:
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
            if model_codes(name) & seen_models:
                continue
            # 名前が売り文句になっている商品と、分野が合わない商品は採らない。
            # ここで落としておかないと、題名もURLも作れない記事になる。
            if looks_like_ad(name) or not fits_category(name, cat, sub_words):
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
            seen_models |= model_codes(name)
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
                # どのサブ区分を狙って引いた候補か。make_drafts.py が
                # 下書きの sub にそのまま入れる（これが無いと、本文を
                # 書いたあとに推測で埋めることになる）。
                "sub": sub,
                "reviews": max(v["reviews"] for v in shops.values()),
                "rating": max(v["rating"] for v in shops.values()),
                "price": min(v["price"] for v in shops.values()),
                "image": e.get("image", ""),
                # モールごとの商品写真。ここに入るのは「その _url が
                # 指している商品そのもの」の写真で、検索し直して名前で
                # 突き合わせたものではないため、別商品を掴む心配が無い。
                # これを下書きに引き継げば、fetch_shop_images.py が
                # 商品コード・JANで一意に特定できず写真を諦める記事でも、
                # 一覧に実物写真を出せる（2026-09-19、型番のある商品が
                # 「写真を特定できない」だけで破棄されていたため追加）。
                "images": {k: v.get("image", "") for k, v in shops.items()
                           if v.get("image")},
                "rakuten_url": (shops.get("rakuten") or {}).get("url", ""),
                "yahoo_url": (shops.get("yahoo") or {}).get("url", ""),
                "amazon_url": "",       # PA-API承認後にここを埋める
                "trending": bool(e.get("trending")),
                # 価格・レビュー件数・平均評価は、ここで各モールのAPIが
                # 正規に返した値。make_drafts.py がこれを下書きの
                # review_stats に引き継ぎ、記事に数字として出す。
                # （fetch_reviews.py は JAN のある記事しか埋められず、
                #   JANを持つ記事は144本中10本しかない）
                "shops": {k: {"price": v["price"], "shop_name": v["shop_name"],
                              "postage_included": v["postage_included"],
                              "reviews": v["reviews"], "rating": v["rating"]}
                          for k, v in shops.items()},
            })

    if ranking_failed:
        print("楽天ランキングAPIは使えないままなので、総合順で代用しました"
              "（2026年2月の刷新で消えたまま。警告にはしない——"
              "通常運用であって故障ではない）")

    # まず型番・メーカー名を特定できそうな商品を前に、そのうえで
    # レビュー件数の多い順（記事の土台になる材料が多い商品から並べる）。
    # 特定できなそうな商品を除外はしない。判定の目安が外れることも
    # あるため、後ろに回すだけにして候補からは消さない。
    def rank_key(c):
        return (not looks_identifiable(c["name"], c["shops"]),
                -c["reviews"], -c["rating"])

    def interleave(items):
        """ランキング由来（今売れている）と、レビュー件数由来（定番）を
           それぞれ並べてから交互に混ぜる。ランキング由来だけを先頭に
           固めると、1回のバッチが少ない本数（今は1回2本）のとき、
           話題の商品ばかりに偏ってしまうため（実際にそう指摘があった）。
           交互にすることで、上から順に take しても両方が混ざって出てくる。"""
        trend = sorted((c for c in items if c["trending"]), key=rank_key)
        normal = sorted((c for c in items if not c["trending"]), key=rank_key)
        mixed = []
        for a, b in zip(trend, normal):
            mixed.append(a)
            mixed.append(b)
        mixed += trend[len(normal):]
        mixed += normal[len(trend):]
        return mixed

    # カテゴリーごとに上限を設けて、カテゴリーをまたいで1件ずつ拾う。
    # カテゴリーの中では、さらにサブ区分をまたいで1件ずつ拾う。
    #
    # 以前はここで全カテゴリーの候補を1本の列にまとめ、レビュー件数の
    # 降順に並べて上から limit 件を切っていた。カテゴリーを一切見て
    # いなかったので、レビュー件数が桁違いに多いジャンルが候補を
    # 独占する（「マウスパッド10枚セット」が「ノートPC」より上に来る）。
    per_cat = max(2, int(limit * CATEGORY_SHARE))
    by_cat = {}
    for c in out:
        by_cat.setdefault(c["category"], {}).setdefault(c.get("sub", ""), []).append(c)

    # サブの中で並べ、サブをまたいで1件ずつ拾ってカテゴリーの列を作る。
    # ここを飛ばしてカテゴリー単位で件数順に並べると、同じカテゴリーの
    # 中でレビュー件数の多いサブ（周辺機器など）が枠を独占してしまい、
    # サブ単位で引いた意味が無くなる。
    for cat, subs in by_cat.items():
        for sub in subs:
            subs[sub] = interleave(subs[sub])
        sub_order = sorted(subs, key=lambda k: (recent_sub.get((cat, k), 0), k))
        merged = []
        while any(subs[k] for k in sub_order):
            for k in sub_order:
                if subs[k]:
                    merged.append(subs[k].pop(0))
        by_cat[cat] = merged[:per_cat]

    # 直近に書いた本数が少ないカテゴリーから先に拾う（クールダウン）。
    # 書いたカテゴリーは次の実行で自然に後ろへ回るので、日をまたいで
    # 均される。同数のときはキー名で決める（実行ごとに並びが変わると、
    # ログを見比べたときに何が効いたのか分からなくなるため）。
    recent = recent_category_load(arts)
    order = sorted(by_cat, key=lambda k: (recent.get(k, 0), k))

    picked = []
    while len(picked) < limit and any(by_cat[k] for k in order):
        for k in order:
            if not by_cat[k]:
                continue
            picked.append(by_cat[k].pop(0))
            if len(picked) >= limit:
                break

    got = collections.Counter(c["category"] for c in picked)
    print("カテゴリーごとの候補数（直近{}本の公開実績→今回の候補）："
          .format(COOLDOWN_RECENT))
    for k in order:
        if got.get(k):
            subs = collections.Counter(c.get("sub", "") for c in picked
                                       if c["category"] == k)
            inner = "・".join(f"{x}{n}" for x, n in subs.most_common())
            print(f"  {k:12s} 直近{recent.get(k, 0):2d}本 → 候補{got[k]:2d}件"
                  f"（{inner}）")
    empty = [f"{c}/{s}" for c, s, _w in targets
             if not any(x["category"] == c and x.get("sub") == s for x in out)]
    if empty:
        # 候補が1件も取れなかったサブ。母数が小さくて MIN_REVIEWS を
        # 超える商品が無いサブは、ここに毎回出る。出続けるようなら
        # そのサブの検索語を見直すか、対象から外す。
        print(f"候補が取れなかったサブ区分 {len(empty)} 件："
              + "、".join(empty))
    return picked


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
    ap.add_argument("--no-trending", action="store_true",
                    help="楽天ランキングAPIを使わない（レビュー件数だけで選ぶ、従来どおりの動き）")
    ap.add_argument("--subs-per-run", type=int, default=SUBS_PER_RUN,
                    help="1回の実行で引くサブ区分の数（記事の少ないサブから順に引く）")
    ap.add_argument("--check-subs", action="store_true",
                    help="CATEGORY_MAP の subs と content/site.json を突き合わせるだけ")
    args = ap.parse_args()

    # サブ区分のキーがサイト側とずれていないか、毎回必ず確かめる。
    # ずれたサブは候補が永久に作られないうえ、記事が0本のまま
    # クールダウンの先頭に居座り続けて他のサブの番を奪う。
    # 気づける経路が無いので、警告ではなくエラーで止める。
    bad = check_subs()
    if bad:
        for line in bad:
            print(f"::error::{line}", file=sys.stderr)
        return 1
    if args.check_subs:
        n = sum(len(c.get("subs") or {}) for c in CATEGORY_MAP.values())
        print(f"✅ CATEGORY_MAP の subs {n} 件は content/site.json と一致しています")
        return 0

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
          f"Yahoo!={'あり' if yahoo_id else 'なし'} / "
          f"ランキング={'なし' if args.no_trending else 'あり'}）")

    cands = build_candidates(rakuten_id, rakuten_key, yahoo_id, cats,
                             args.limit, args.per_category,
                             trending=not args.no_trending,
                             subs_per_run=args.subs_per_run)

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
        mark = "🔥話題 " if c.get("trending") else ""
        print(f"  ・{mark}{c['name'][:44]}")
        print(f"     {c['category']} / ￥{c['price']:,} / "
              f"レビュー{c['reviews']:,}件 ★{c['rating']:.1f} / {shops or '—'}")
    if len(cands) > 10:
        print(f"  … ほか {len(cands) - 10} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
