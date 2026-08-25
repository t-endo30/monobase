#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A8.net の広告コードを取り込み、案件名とカテゴリーを自動で割り当てる。

A8には広告コードを配るAPIがありません。コード自体は
`tools/a8-collect.js`（ブラウザのコンソールに貼る）で集めます。
このツールは、集めたコードに **名前とカテゴリーを付ける** 役です。

  なぜCSVが要るか
    集めたコードには `mid=s00000000040014012000` という番号が入っています。
    この先頭15桁が、提携中プログラムのCSVにある「プログラムID」と一致します。
    突き合わせれば、どの案件のバナーかが分かり、案件のカテゴリーから
    「サイトのどのカテゴリーの記事に出すか」まで決められます。

  CSVからリンクは作れません
    CSVには成果を紐づける `a8mat=` が入っていないためです。
    リンクの取得は、必ずA8の画面から行ってください（コードは書き換えない）。

使い方
  1. A8で「プログラム管理 → 参加中プログラム」→ CSVをダウンロード
  2. A8の「広告リンク」ページで tools/a8-collect.js を実行してコードをコピー
  3. コピーしたものをファイルに保存（例：codes.txt）
  4. $ python3 tools/import_a8.py --csv programs.csv --codes codes.txt
     （中身を確認するだけ。--apply を付けると content/site.json に書き込む）

  $ python3 tools/import_a8.py --csv programs.csv --codes codes.txt --apply
  $ python3 tools/import_a8.py --csv programs.csv --codes codes.txt --where side --apply
"""
import argparse, csv, io, json, os, re, sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A8のCSVは Shift-JIS で出てくる。取り違えると全部化けるので順に試す。
ENCODINGS = ["cp932", "utf-8-sig", "utf-16", "euc_jp"]

# 広告コードの区切り。まとめて貼ったものも1件ずつに分ける。
HEADS = re.compile(
    r'(?=<a[^>]+href="https?://(?:px\.a8\.net|rpx\.a8\.net))', re.I)

# 案件のジャンル・名前から、サイトのどのカテゴリーの記事に出すかを決める。
# 記事の内容と関係のない広告を並べないための対応表。
RULES = [
    (r"光回線|プロバイダ|インターネット接続|ドコモ|ホームルーター|WiMAX|wifi|Wi-?Fi",
     ["pc"], "回線・Wi-Fi"),
    (r"家電|レンタル|サブスク",           ["appliance", "kitchen"], "家電レンタル"),
    (r"買取|買い取り|リユース|中古",       ["pc", "av"],             "買取"),
    (r"寝具|マットレス|枕|布団",           ["furniture"],            "寝具"),
    (r"引越|引っ越し",                     ["furniture", "daily"],   "引越し"),
    (r"電気|ガス|電力",                    ["appliance"],            "電気・ガス"),
    (r"ウォーターサーバー|食材宅配|ミールキット", ["kitchen"],        "キッチン周り"),
]


def read_csv(path):
    """提携中プログラムのCSVを読む。ID → (案件名, ジャンル) を返す。"""
    last = None
    for enc in ENCODINGS:
        try:
            raw = io.open(path, encoding=enc).read()
        except (UnicodeDecodeError, LookupError) as ex:
            last = ex
            continue
        rows = list(csv.reader(io.StringIO(raw)))
        if rows and len(rows[0]) >= 4:
            out = {}
            for r in rows[1:]:
                if len(r) < 4 or not r[0].strip().startswith("s"):
                    continue
                out[r[0].strip()] = (r[1].strip(), r[3].strip())
            if out:
                print(f"CSVを {enc} として読みました（{len(out)} 件の提携）")
                return out
    raise SystemExit(f"CSVを読めませんでした：{last}")


def split_codes(text):
    parts = [t.strip() for t in re.split(r"(?m)^\s*-{3,}\s*$", text) if t.strip()]
    if len(parts) > 1:
        return parts
    return [t.strip() for t in HEADS.split(text) if t.strip()]


def program_id(code):
    """コードの mid= からプログラムIDを取り出す。先頭15桁がCSVのIDと一致する。"""
    m = re.search(r"[?&]mid=(s\d+)", code)
    if not m:
        return ""
    return m.group(1)[:15]


def classify(name, genre):
    """案件名とジャンルから、出す先のカテゴリーを決める。"""
    blob = f"{name} {genre}"
    for pat, cats, label in RULES:
        if re.search(pat, blob, re.I):
            return cats, label
    return [], "その他"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="提携中プログラムのCSV")
    ap.add_argument("--codes", required=True,
                    help="a8-collect.js で集めたコードを保存したファイル")
    ap.add_argument("--where", default="article_end",
                    choices=["article_end", "side", "none"],
                    help="出す場所（既定は記事の下）")
    ap.add_argument("--apply", action="store_true",
                    help="content/site.json に書き込む")
    ap.add_argument("--replace", action="store_true",
                    help="いまの広告設定を捨てて入れ替える（既定は追加）")
    args = ap.parse_args()

    programs = read_csv(args.csv)
    codes = split_codes(io.open(args.codes, encoding="utf-8").read())
    if not codes:
        raise SystemExit("広告コードが見つかりませんでした。")

    # 同じカテゴリーに出すものは1つの枠にまとめる。
    # 枠の中に複数入れておくと、表示のたびに1件が選ばれる。
    groups = OrderedDict()
    unknown = []
    for c in codes:
        pid = program_id(c)
        name, genre = programs.get(pid, ("", ""))
        cats, label = classify(name, genre)
        if not name:
            unknown.append(c[:70])
        key = (tuple(cats), label)
        groups.setdefault(key, {"label": label, "cats": cats,
                                "names": [], "codes": []})
        groups[key]["codes"].append(c)
        if name and name not in groups[key]["names"]:
            groups[key]["names"].append(name)

    print(f"\n広告コード {len(codes)} 件を {len(groups)} 枠にまとめました\n")
    items = []
    for (cats, label), g in groups.items():
        where = args.where if cats else "none"
        cat_txt = "、".join(cats) if cats else "（振り分け先が決まらず。出さないに設定）"
        print(f"■ {label}：{len(g['codes'])} 件 → {cat_txt}")
        for n in g["names"][:6]:
            print(f"    ・{n[:52]}")
        if len(g["names"]) > 6:
            print(f"    …ほか {len(g['names']) - 6} 件")
        items.append({
            "name": f"{label}（{len(g['codes'])}件）",
            "where": where,
            "cats": list(cats),
            "html": "\n---\n".join(g["codes"]),
        })

    if unknown:
        print(f"\n△ CSVに見つからないコードが {len(unknown)} 件ありました"
              "（提携日がCSVより新しい可能性があります）")
        for u in unknown[:3]:
            print(f"    {u}…")

    if not args.apply:
        print("\n（--apply を付けると content/site.json に書き込みます）")
        return 0

    p = os.path.join(ROOT, "content", "site.json")
    site = json.load(io.open(p, encoding="utf-8"))
    promos = site.setdefault("promos", {})
    promos.setdefault("label", "PR")
    old = [] if args.replace else (promos.get("items") or [])
    promos["items"] = old + items
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(site, f, ensure_ascii=False, indent=1)
    print(f"\ncontent/site.json に {len(items)} 枠を書き込みました。")
    print("次にやること：python3 build.py で反映し、記事を開いて表示を確かめる")
    return 0


if __name__ == "__main__":
    sys.exit(main())
