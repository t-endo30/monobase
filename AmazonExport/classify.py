# -*- coding: utf-8 -*-
"""Order History.csv からサイトのカテゴリ(gadget/desk/home)に使える商品だけを抽出する。
使い方: python3 classify.py
出力: candidates.csv (未使用の候補), used.csv (記事化済み), excluded.csv (除外分)
記事化済みASINは content/articles.json から自動で読み、candidates.csv から外れる。
"""
import csv, json, os, re, collections

SRC  = "Order History.csv"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def used_asins():
    """すでに記事化したASIN。content/articles.json を唯一の正とする。"""
    p = os.path.join(ROOT, "content", "articles.json")
    try:
        arts = json.load(open(p, encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return {(a.get("asin") or "").upper(): a["slug"] for a in arts if a.get("asin")}

# --- 明確に除外するもの（サイトの趣旨に合わない/紹介できない） ---
EXCLUDE = [
    # アダルト
    "オナホ","オナニー","ディルド","アダルト","エネマ","コンドーム","TENGA","バイブ","ローター","電マ",
    # サバゲー・銃器・ミリタリー
    "電動ガン","エアガン","ガスガン","マガジン","マルイ","BB弾","スコープ","サバゲ","タクティカル","MOLLE",
    "ホルスター","ダットサイト","ハンドガード","アウターバレル","ピストル","ライフル","LAYLAX","M4","AK",
    "サプレッサー","チャンバー","ホップ","レイル","レール","ストック","グリップ","スリング","フラッシュハイダー",
    # 医薬・健康食品・サプリ
    "サプリ","プエラリア","漢方","錠","粒","mg)","栄養","プロテイン","医薬部外","絆創膏","マスク","目薬",
    # 化粧品・ヘアケア・衛生
    "シャンプー","コンディショナー","トリートメント","化粧水","乳液","美容液","BBクリーム","クッション","日焼け",
    "香水","コロン","歯ブラシ","歯磨","カミソリ","替刃","柔軟剤","洗剤","石鹸","ボディ","スキン","クリオ","ミシャ",
    "コスメ","ネイル","まつ毛","リップ","ファンデ",
    # 衣類・靴・アクセ・時計バンド
    "Tシャツ","シャツ","パンツ","靴下","スニーカー","下駄","ジャケット","帽子","手袋","ベルト","財布","時計ベルト",
    "ストラップ 20mm","バンド","サンダル","インナー",
    # 食品・飲料・ペット・園芸・車バイク・玩具・書籍
    "食品","お菓子","コーヒー","紅茶","ドリンク","レトルト","米","調味","ペット","猫","犬","園芸","肥料","培養土",
    "鉢","バイク","自動車","車用","タイヤ","フィギュア","超合金","プラモ","トレカ","ポケカ","カード","漫画","本 ",
    "コンタクト","1day","ワンデー","メガネ","眼鏡","収納袋","カーテン","ストロー","テーブルクロス","DVD","Blu-ray","ゲームソフト","おもちゃ","玩具","提灯","カレンダー",
]

# --- カテゴリ判定（上から順に評価） ---
RULES = [
 ("gadget", ["イヤホン","ヘッドホン","ヘッドフォン","キーボード","マウス","モニター","ディスプレイ","充電器","充電ケーブル",
   "モバイルバッテリー","USB","Type-C","HDMI","LANケーブル","ハブ","SSD","HDD","SDカード","microSD","マイク",
   "スピーカー","Bluetooth","Wi-Fi","WiFi","ルーター","スマートウォッチ","スマートリモコン","スマートプラグ",
   "webカメラ","Webカメラ","カメラ","カメラレンズ","交換レンズ","三脚","ジンバル","AirTag","Apple","iPhone","iPad","Anker","エレコム",
   "サンワサプライ","バッファロー","変換アダプタ","ドッキング","液晶保護","ガラスフィルム","タブレット","PC","パソコン",
   "ノートパソコン","電源タップ","タップ","プリンタ","スキャナ","NAS","キャプチャ","ゲーミング","コントローラー",
   "SDカードリーダー","バッテリーチャージャー","ドライブレコーダー","プロジェクター","電子書籍","Kindle","Echo","Fire TV"]),
 ("desk", ["デスク","机","チェア","椅子","デスクチェア","モニターアーム","モニタースタンド","ノートPCスタンド","リストレスト",
   "パームレスト","デスクマット","マウスパッド","フットレスト","昇降","ケーブルトレー","ケーブルボックス","配線",
   "収納ラック","本棚","書棚","引き出し","ワゴン","デスクライト","照明 デスク","クッション 座","座布団","ゲーミングチェア",
   "オフィス","ファイルボックス","ペンスタンド","穴あけパンチ","ホッチキス","付箋","ブックスタンド"]),
 ("home", ["加湿器","除湿","空気清浄","掃除機","扇風機","サーキュレーター","ヒーター","こたつ","電気毛布","炊飯",
   "電子レンジ","トースター","ケトル","コーヒーメーカー","ミキサー","フライパン","鍋","包丁","まな板","食器",
   "洗濯","物干し","ハンガー","ゴミ箱","ダストボックス","収納ボックス","突っ張り","山崎実業",
   "バスルーム","浴室","キッチン","洗面","トイレ","歯間","シーリングライト","LED電球","間接照明","電球","シーリング","掛け時計","目覚まし",
   "スリッパ","カーテン","ラグ","掛け布団","枕","マットレス","シャワーヘッド","ミラブル","体重計","温湿度計","隙間収納",
   "キャビネット","サニタリー","フック","ワイヤレス給電"]),
]

def excluded(name):
    return next((w for w in EXCLUDE if w in name), None)

def categorize(name):
    for cat, kws in RULES:
        for kw in kws:
            if kw in name:
                return cat, kw
    return None, None

rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))

USED = used_asins()
keep, drop, used_rows = [], [], []
seen = set()
for r in rows:
    name = r["Product Name"]
    asin = r["ASIN"]
    ex = excluded(name)
    if ex:
        drop.append({**r, "reason": f"NG:{ex}"}); continue
    cat, kw = categorize(name)
    if not cat:
        drop.append({**r, "reason": "該当カテゴリなし"}); continue
    if asin in seen:
        drop.append({**r, "reason": "重複ASIN"}); continue
    seen.add(asin)
    if asin in USED:
        used_rows.append({"ASIN": asin, "category": cat, "slug": USED[asin],
                          "Product Name": name})
        continue
    keep.append({"ASIN": asin, "category": cat, "matched": kw,
                 "Product Name": name, "Order Date": r["Order Date"][:10],
                 "Unit Price": r["Unit Price"]})

with open("candidates.csv","w",newline="",encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["ASIN","category","matched","Product Name","Order Date","Unit Price"])
    w.writeheader(); w.writerows(sorted(keep, key=lambda x:(x["category"], x["Product Name"])))

with open("excluded.csv","w",newline="",encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())+["reason"])
    w.writeheader(); w.writerows(drop)

with open("used.csv","w",newline="",encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["ASIN","category","slug","Product Name"])
    w.writeheader(); w.writerows(sorted(used_rows, key=lambda x: x["slug"]))

c = collections.Counter(x["category"] for x in keep)
print(f"元データ: {len(rows)}件")
print(f"採用: {len(keep)}件 / 除外: {len(drop)}件 / 記事化済み: {len(used_rows)}件")
for cat, label in [("gadget","ガジェット・PC周辺"),("desk","デスク環境・家具"),("home","生活家電・日用品")]:
    print(f"  {cat:7s} {label:12s} {c[cat]:4d}件")
