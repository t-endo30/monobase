# -*- coding: utf-8 -*-
"""Order History.csv を、サイトのカテゴリー体系（content/site.json）に沿って仕分ける。

  $ python3 AmazonExport/classify.py

出力
  candidates.csv … まだ記事にしていない商品（カテゴリー／サブカテゴリー付き）
  used.csv       … すでに記事化した商品（articles.json から自動判定）
  unmatched.csv  … どのカテゴリーにも当てはまらなかった商品
  excluded.csv   … サイトで扱わないと決めた商品（アダルト等）

判定はすべて商品名のキーワード一致。上から順に評価し、最初に当たった
サブカテゴリーを採用する。取りこぼしは unmatched.csv を見て RULES に足す。
"""
import csv, json, os, re, collections

SRC  = "Order History.csv"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# サイトで扱わないもの（アフィリエイトの方針・媒体の性格として外す）
EXCLUDE = [
    "オナホ","オナニー","ディルド","アダルト","エネマ","コンドーム","TENGA","バイブ","ローター",
    "電動ガン","エアガン","ガスガン","BB弾","サバゲ","マルイ","LAYLAX","ホルスター","ダットサイト",
    "スコープ","ハンドガード","アウターバレル","サプレッサー","フラッシュハイダー","マガジンキャッチ",
    "処方","医薬品","第2類","第3類",
]

# (カテゴリー, サブカテゴリー, キーワード) を上から評価する
RULES = [
 # --- パソコン ---
 ("pc","monitor",["モニター","ディスプレイ","液晶ディスプレイ","モニターアーム","モニタースタンド","ウルトラワイド"]),
 ("pc","input",["キーボード","マウス","トラックボール","ペンタブ","マウスパッド","リストレスト","パームレスト"]),
 ("pc","storage",["SSD","HDD","外付けドライブ","microSD","SDカード","USBメモリ","NAS","カードリーダー"]),
 ("pc","network",["ルーター","Wi-Fi","WiFi","無線LAN","LANケーブル","スイッチングハブ","中継機","PLC"]),
 ("pc","peripheral",["ドッキングステーション","USBハブ","USB Type-C","変換アダプタ","HDMI","DisplayPort","KVM","ケーブル","机上台","ドッキング"]),
 ("pc","laptop",["ノートパソコン","ノートPC","gram","MacBook","Chromebook","ノートブック"]),
 ("pc","tablet",["タブレット","iPad","Kindle","電子書籍","MediaPad"]),
 ("pc","parts",["PCケース","電源ユニット","グラフィックボード","GPU","CPUクーラー","メモリ DDR","マザーボード","ケースファン"]),
 ("pc","software",["Office","Excel","Word","ライセンス","ソフトウェア","ウイルス対策"]),
 # --- AV機器 ---
 ("av","headphone",["イヤホン","ヘッドホン","ヘッドフォン","ヘッドセット","イヤーピース"]),
 ("av","mic",["マイク","ピンマイク","オーディオインターフェース","会議用スピーカー","スピーカーフォン","配信"]),
 ("av","tv",["テレビ","プロジェクター","Fire TV","Chromecast","レコーダー","アンテナ"]),
 ("av","speaker",["スピーカー","サウンドバー","ウーファー"]),
 # --- カメラ ---
 ("camera","lens",["交換レンズ","単焦点","広角レンズ","望遠","レンズフィルター","レンズフード","Eマウント"]),
 ("camera","tripod",["三脚","ジンバル","雲台","一脚","スタビライザー"]),
 ("camera","body",["一眼","ミラーレス","デジカメ","アクションカメラ","OSMO","GoPro","カメラ本体"]),
 ("camera","acc",["カメラバッグ","防湿庫","SDカードケース","レリーズ","カメラストラップ","バッテリーチャージャー","NP-"]),
 # --- スマートフォン ---
 ("smartphone","case",["スマホケース","iPhoneケース","スマホカバー","液晶保護フィルム","保護ガラス","ガラスフィルム","手帳型ケース"]),
 ("smartphone","charger",["モバイルバッテリー","充電器","急速充電","MagSafe","ワイヤレス充電","充電スタンド","シガーチャージャー"]),
 ("smartphone","acc",["スマホリング","スマホホルダー","車載ホルダー","自撮り棒","スマホスタンド","MagSafe","マグセーフ"]),
 ("smartphone","body",["SIMフリー","スマートフォン本体","Pixel","Galaxy","Xperia"]),
 # --- 家電 ---
 ("appliance","aircon",["加湿器","除湿","空気清浄","扇風機","サーキュレーター","ヒーター","こたつ","電気毛布","冷風","エアコン","ストーブ"]),
 ("appliance","clean",["掃除機","ロボット掃除機","スチームクリーナー","布団乾燥","高圧洗浄"]),
 ("appliance","laundry",["洗濯機","乾燥機","アイロン","衣類スチーマー"]),
 ("appliance","light",["シーリングライト","LED電球","投光器","デスクライト","モニターライト","間接照明","電球","照明器具","ダウンライト","スタンドライト","LEDライト","ナイトライト","ランタン","スクリーンバー"]),
 ("appliance","smart",["スマートリモコン","スマートプラグ","スマートスピーカー","Alexa","Echo","Google Home","SwitchBot","Nature Remo","スマートロック"]),
 ("appliance","power",["電源タップ","延長コード","乾電池","充電池","蓄電池","ポータブル電源","UPS"]),
 # --- キッチン ---
 ("kitchen","appliance",["電子レンジ","炊飯","トースター","電気ケトル","コーヒーメーカー","ミキサー","ホットプレート","食洗機","電気圧力鍋","ノンフライヤー"]),
 ("kitchen","tool",["フライパン","鍋","包丁","まな板","ピーラー","計量","菜箸","キッチンばさみ","おろし金"]),
 ("kitchen","ware",["食器","マグカップ","タンブラー","水筒","保存容器","弁当箱","カトラリー","グラス"]),
 ("kitchen","storage",["水切り","キッチン収納","スパイスラック","冷蔵庫収納","シンク"]),
 # --- 美容・コスメ ---
 ("beauty","haircare",["シャンプー","コンディショナー","トリートメント","ヘアオイル","ドライヤー","ヘアアイロン","育毛"]),
 ("beauty","skincare",["化粧水","乳液","美容液","日焼け止め","クレンジング","洗顔","保湿","パック","フェイスマスク"]),
 ("beauty","makeup",["ファンデーション","BBクリーム","クッション","口紅","リップ","アイライナー","マスカラ","コンシーラー","ネイル","コスメ"]),
 ("beauty","device",["美顔器","脱毛器","光美容","毛穴","EMS"]),
 ("beauty","shave",["カミソリ","シェーバー","替刃","髭剃り","除毛"]),
 # --- ヘルスケア ---
 ("health","measure",["スマートウォッチ","活動量計","体重計","体組成計","血圧計","体温計","パルスオキシ","歩数計"]),
 ("health","care",["マッサージ","ストレッチ","フォームローラー","骨盤","サポーター","温熱","湿布","枕 首"]),
 ("health","supplement",["サプリ","プロテイン","ビタミン","乳酸菌","青汁","プエラリア","漢方"]),
 ("health","hygiene",["マスク","絆創膏","消毒","うがい","歯ブラシ","歯磨","デンタル","マウスウォッシュ","綿棒","体温"]),

 # --- 日用品・雑貨（他カテゴリーに収まらない領域） ---
 ("daily","fashion",["腕時計","時計ベルト","NATOストラップ","財布","スニーカー","サンダル","ジャケット",
   "Tシャツ","パンツ","帽子","キャップ","手袋","マフラー","サングラス","メガネ","眼鏡","下駄","ネクタイ",
   "リュック","バックパック","ショルダーバッグ","トートバッグ"]),
 ("daily","tool",["ドライバー","ドライバーセット","レンチ","ペンチ","ニッパー","ドリル","六角","ハンダ",
   "はんだ","工具","ビス","ネジ","取付金具","接着剤","ヤスリ","ノギス","メジャー","作業手袋","脚立",
   "電動ドライバー","トルク","WERA","TRUSCO"]),
 ("daily","garden",["園芸","培養土","肥料","鉢","プランター","種子","植物育成","ハイドロ","じょうろ",
   "剪定","支柱","防草"]),
 ("daily","hobby",["Nintendo","Switch","PlayStation","PS5","PS4","ゲームソフト","コントローラー",
   "プラモ","ガンプラ","フィギュア","トレカ","ポケカ","カードローダー","スリーブ","ジグソー","ボードゲーム",
   "楽器","ギター","超合金"]),
 ("daily","car",["バイク用","カー用品","車載","タイヤ","エンジンオイル","ドライブレコーダー","ヘルメット",
   "デイトナ","ハンドルバー","チェーンロック","洗車"]),
 ("daily","outdoor",["キャンプ","テント","寝袋","シュラフ","ランタン","登山","トレッキング","釣り",
   "自転車","サイクル","ヨガ","ダンベル","トレーニング","縄跳び","水筒 保冷"]),
 ("daily","stationery",["ノート","付箋","クリップ","封筒","印鑑","ラベル","カッター","はさみ","定規",
   "穴あけパンチ","ホッチキス","ファイル","ペンケース","マーカー","消しゴム","電卓"]),
 # --- ペット ---
 ("pet","food",["ドッグフード","キャットフード","ペットフード","ささみ","おやつ 犬","おやつ 猫"]),
 ("pet","care",["ペットシーツ","猫砂","トイレ 猫","ブラッシング","爪切り ペット","消臭 ペット"]),
 ("pet","aqua",["水槽","アクアリウム","金魚","メダカ","エアポンプ","ハムスター","ケージ"]),
 ("pet","dog",["犬用","ドッグ","首輪","リード 犬","ハーネス 犬"]),
 ("pet","cat",["猫用","キャット","爪とぎ","キャットタワー"]),
 # --- 家具・インテリア ---
 ("furniture","desk",["デスク","昇降","フットレスト","足置き","デスクマット","チェアマット","天板"]),
 ("furniture","chair",["デスクチェア","オフィスチェア","ゲーミングチェア","スツール","座椅子","チェアカバー","腰痛 クッション"]),
 ("furniture","shelf",["ウォールラック","スチールラック","オープンラック","シェルフ","本棚","書棚","収納ラック","デスクラック","デスクワゴン","サイドワゴン","キャビネット","収納家具","玄関ベンチ","チェスト","サイドテーブル","ダイニングテーブル","突っ張りラック","壁面収納"]),
 ("furniture","bed",["マットレス","枕","まくら","布団","ベッド","シーツ","毛布","寝具","ピロー"]),
 ("furniture","deco",["カーテン","ラグマット","カーペット","掛け時計","目覚まし時計","ポスター","観葉植物","フォトフレーム"]),
 # --- 日用品・雑貨 ---
 ("daily","clean",["ゴミ箱","ダストボックス","洗剤","柔軟剤","スポンジ","雑巾","クリーナー","コロコロ","ブラシ","ゴミ袋"]),
 ("daily","bath",["バスルーム","浴室","シャワーヘッド","風呂","洗面","トイレ","タオル","バスマット"]),
 ("daily","safety",["防犯カメラ","防災","非常用","消火","ホームセキュリティ","センサーライト","鍵","南京錠"]),
 ("daily","storage",["収納ボックス","突っ張り棒","壁掛けフック","マグネット収納","隙間収納","衣類収納","ハンガー","小物収納","収納ケース","収納袋"]),
 ("daily","misc",["文房具","ファイルボックス","ボールペン","万年筆","ハサミ","養生テープ","マスキングテープ","折りたたみ傘","スリッパ","玄関マット","穴あけパンチ","ホッチキス"]),
]

def load_used():
    p = os.path.join(ROOT, "content", "articles.json")
    try:
        arts = json.load(open(p, encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return {(a.get("asin") or "").upper(): a["slug"] for a in arts if a.get("asin")}

def excluded(name):
    return next((w for w in EXCLUDE if w in name), None)

def classify(name):
    for cat, sub, kws in RULES:
        for kw in kws:
            if kw in name:
                return cat, sub, kw
    return None, None, None

def main():
    os.chdir(HERE)
    rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
    used = load_used()
    keep, drop, unmatched, used_rows = [], [], [], []
    seen = set()

    for r in rows:
        name, asin = r["Product Name"], r["ASIN"]
        ng = excluded(name)
        if ng:
            drop.append({**r, "reason": f"対象外:{ng}"}); continue
        cat, sub, kw = classify(name)
        if not cat:
            unmatched.append({"ASIN": asin, "Product Name": name}); continue
        if asin in seen:
            drop.append({**r, "reason": "重複ASIN"}); continue
        seen.add(asin)
        if asin in used:
            used_rows.append({"ASIN": asin, "category": cat, "sub": sub,
                              "slug": used[asin], "Product Name": name}); continue
        keep.append({"ASIN": asin, "category": cat, "sub": sub, "matched": kw,
                     "Product Name": name, "Order Date": r["Order Date"][:10],
                     "Unit Price": r["Unit Price"]})

    def dump(path, rows_, fields):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader(); w.writerows(rows_)

    dump("candidates.csv", sorted(keep, key=lambda x: (x["category"], x["sub"], x["Product Name"])),
         ["ASIN","category","sub","matched","Product Name","Order Date","Unit Price"])
    dump("used.csv", sorted(used_rows, key=lambda x: x["slug"]),
         ["ASIN","category","sub","slug","Product Name"])
    dump("unmatched.csv", unmatched, ["ASIN","Product Name"])
    dump("excluded.csv", drop, list(rows[0].keys()) + ["reason"])

    site = json.load(open(os.path.join(ROOT, "content", "site.json"), encoding="utf-8"))
    label = {c["key"]: c["label"] for c in site["categories"]}
    slabel = {(c["key"], sc["key"]): sc["label"]
              for c in site["categories"] for sc in c.get("sub", [])}
    cnt = collections.Counter((x["category"], x["sub"]) for x in keep)

    print(f"元データ {len(rows)} 行")
    print(f"  候補 {len(keep)} / 記事化済み {len(used_rows)} / "
          f"未分類 {len(unmatched)} / 対象外・重複 {len(drop)}\n")
    for c in site["categories"]:
        total = sum(v for (k, _), v in cnt.items() if k == c["key"])
        if not total:
            continue
        print(f"■ {label[c['key']]}  {total}件")
        for sc in c.get("sub", []):
            n = cnt.get((c["key"], sc["key"]), 0)
            if n:
                print(f"    {slabel[(c['key'], sc['key'])]:<22} {n:>4}")

if __name__ == "__main__":
    main()
