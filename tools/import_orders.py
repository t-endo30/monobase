#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Amazonの注文履歴CSVから、記事の下書きを作る。

  $ python3 tools/import_orders.py ~/Downloads/Retail.OrderHistory.1.csv
  $ python3 tools/import_orders.py orders.csv --write     # articles.json に追記

【重要】
・CSVには住所・支払い方法・金額などの個人情報が含まれる。
  このスクリプトは商品名・ASIN・注文日だけを読み、他の列は一切出力しない。
・CSV自体はリポジトリに置かないこと（.gitignore で除外済み）。
・作られるのはすべて published:false の下書き。
  実際に使った内容を書いてから公開すること。
"""
import csv, io, json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shorten_name import shorten
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# CSVの列名は出力形式により異なるため、候補を並べて拾う
COL_TITLE = ["Product Name", "Title", "商品名", "product_name", "item_name"]
COL_ASIN  = ["ASIN", "ASIN/ISBN", "asin", "ASIN_ISBN"]
COL_DATE  = ["Order Date", "order_date", "注文日", "Ship Date", "ship_date"]
COL_QTY   = ["Quantity", "数量", "quantity"]
COL_URL   = ["Product URL", "URL", "商品URL"]

# カテゴリー自動判定（キーワード→カテゴリー）
RULES = [
    ("gadget", ["イヤホン", "ヘッドホン", "キーボード", "マウス", "モニター", "ディスプレイ",
                "充電", "ケーブル", "USB", "SSD", "ハブ", "スピーカー", "webカメラ", "マイク",
                "タブレット", "スマホ", "バッテリー", "アダプタ", "PC", "パソコン"]),
    ("desk",   ["デスク", "チェア", "椅子", "クッション", "ライト", "照明", "アーム",
                "ラック", "棚", "収納", "マット", "スタンド", "リストレスト", "パームレスト"]),
    ("home",   ["加湿器", "除湿", "空気清浄", "掃除機", "扇風機", "サーキュレーター", "ヒーター",
                "洗剤", "詰め替え", "ティッシュ", "タオル", "枕", "寝具", "布団", "調理",
                "電気ケトル", "炊飯", "冷蔵", "食洗", "歯ブラシ", "シャンプー"]),
]


def pick(row, names):
    for n in names:
        if n in row and str(row[n]).strip():
            return str(row[n]).strip()
    # 大文字小文字・空白を無視して再探索
    norm = {re.sub(r"[\s_]", "", k).lower(): v for k, v in row.items() if k}
    for n in names:
        k = re.sub(r"[\s_]", "", n).lower()
        if k in norm and str(norm[k]).strip():
            return str(norm[k]).strip()
    return ""


def guess_category(title):
    t = unicodedata.normalize("NFKC", title).lower()
    for cat, words in RULES:
        for w in words:
            if w.lower() in t:
                return cat
    return "gadget"


def short_title(title):
    """SEO目的で長くなった商品名を、記事タイトル用に要約する。"""
    return shorten(title)


def slugify(title, asin, used):
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    base = "-".join([p for p in base.split("-") if p][:4])
    if not base:
        base = "item"
    slug = f"{base}-review" if not asin else f"{base or 'item'}-{asin[-4:].lower()}-review"
    slug = re.sub(r"-+", "-", slug)[:60]
    n, out = 2, slug
    while out in used:
        out = f"{slug}-{n}"; n += 1
    used.add(out)
    return out


def read_orders(path):
    with io.open(path, encoding="utf-8-sig", errors="replace") as f:
        sample = f.read(4096); f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        except csv.Error:
            dialect = csv.excel
        rows = list(csv.DictReader(f, dialect=dialect))
    if not rows:
        return []

    items = OrderedDict()   # ASIN or 商品名 で重複排除
    for r in rows:
        title = pick(r, COL_TITLE)
        if not title:
            continue
        asin = pick(r, COL_ASIN).upper()
        if not asin:
            m = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", pick(r, COL_URL), re.I)
            asin = m.group(1).upper() if m else ""
        if asin and not re.fullmatch(r"[A-Z0-9]{10}", asin):
            asin = ""
        key = asin or title
        if key in items:
            items[key]["count"] += 1
            continue
        items[key] = {
            "title": title, "asin": asin,
            "date": pick(r, COL_DATE)[:10].replace("/", "-"),
            "qty": pick(r, COL_QTY) or "1", "count": 1,
        }
    return list(items.values())


def to_article(it, used):
    title = short_title(it["title"])
    cat = guess_category(it["title"])
    return {
        "slug": slugify(title, it["asin"], used),
        "category": cat, "published": False, "featured": False,
        "title": f"{title} レビュー｜",
        "list_title": f"{title} レビュー",
        "description": "", "excerpt": "",
        "date": it["date"] or "", "updated": it["date"] or "",
        "tags": ["レビュー"], "icon": "📦", "thumb": "",
        "asin": it["asin"], "amazon_url": "",
        "cta_label": "Amazonで価格と詳細を確認する",
        "verdict_title": "結論：", "summary": [],
        "rating": {"score": 0, "breakdown": ""}, "lead": "",
        "not_for": {"intro": "", "items": []}, "scenes": [],
        "pros": [], "cons": [],
        "spec": {"intro": "", "headers": [], "rows": []},
        "voices_intro": "", "voices": [],
        "personal_note": "",
        "next_problem": {"intro": "", "items": []},
        "conclusion_title": "まとめ", "conclusion": "",
        "_source_title": it["title"],
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    write = "--write" in sys.argv
    if not args:
        print(__doc__); return 0

    path = os.path.expanduser(args[0])
    if not os.path.exists(path):
        print(f"❌ ファイルが見つかりません: {path}"); return 1

    items = read_orders(path)
    if not items:
        print("❌ 商品を読み取れませんでした。列名が想定と異なる可能性があります。")
        return 1

    ap = os.path.join(ROOT, "content", "articles.json")
    arts = json.load(io.open(ap, encoding="utf-8"))
    have_asin = {a.get("asin") for a in arts if a.get("asin")}
    used = {a["slug"] for a in arts}

    new = []
    for it in items:
        if it["asin"] and it["asin"] in have_asin:
            continue
        new.append(to_article(it, used))

    print(f"読み取り: {len(items)} 商品 / 新規: {len(new)} 件\n")
    by_cat = {}
    for a in new:
        by_cat.setdefault(a["category"], []).append(a)
    labels = {"gadget": "ガジェット・PC周辺", "desk": "デスク環境・家具",
              "home": "生活家電・日用品", "compare": "比較・まとめ"}
    for cat, lst in by_cat.items():
        print(f"■ {labels.get(cat, cat)}（{len(lst)}件）")
        for a in lst:
            print(f"   {a['asin'] or '(ASIN不明)':12} {a['_source_title'][:44]}")
        print()

    if not write:
        print("→ 追記するには --write を付けて再実行してください。")
        return 0

    for a in new:
        a.pop("_source_title", None)
    arts.extend(new)
    io.open(ap, "w", encoding="utf-8").write(
        json.dumps(arts, ensure_ascii=False, indent=2) + "\n")
    print(f"✅ articles.json に下書き {len(new)} 件を追記しました。")
    print("   管理画面の「記事」タブで内容を書いてから公開してください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
