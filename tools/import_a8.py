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
import argparse, csv, datetime, io, json, os, re, sys
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
    (r"イヤホン|ヘッドホン|オーディオ|スピーカー",
     ["av"], "オーディオ"),
    (r"光回線|プロバイダ|インターネット接続|ドコモ|ホームルーター|WiMAX|wifi|Wi-?Fi"
     r"|フレッツ|ひかり|光】|光\b|回線|ネット使い放題|キャッシュバック",
     ["pc"], "回線・Wi-Fi"),
    (r"家電|レンタル|サブスク",           ["appliance", "kitchen"], "家電レンタル"),
    (r"買取|買い取り|リユース|中古",       ["pc", "av"],             "買取"),
    (r"寝具|マットレス|枕|布団",           ["furniture"],            "寝具"),
    (r"引越|引っ越し",                     ["furniture", "daily"],   "引越し"),
    (r"電気|ガス|電力",                    ["appliance"],            "電気・ガス"),
    (r"ウォーターサーバー|食材宅配|ミールキット", ["kitchen"],        "キッチン周り"),
    (r"脱毛|エステ|美容医療|クリニック",   ["beauty"],               "脱毛・美容"),
    (r"化粧品|スキンケア|コスメ|美容液|シャンプー|ヘアケア",
     ["beauty"],                                                     "コスメ・ヘアケア"),
    (r"日用品|洗剤|防災|収納|クリーニング|家事代行",
     ["daily"],                                                      "日用品・暮らし"),
    (r"旅行|ホテル|宿|航空券|ツアー|レンタカー|スーツケース|海外Wi-?Fi",
     ["travel"],                                                     "旅行"),
    (r"健康食品|サプリ|プロテイン|青汁|検査キット|ダイエット",
     ["health"],                                                     "健康・サプリ"),
    (r"スマホ|格安SIM|MVNO|携帯|モバイル回線",
     ["smartphone"],                                                 "スマホ・回線"),
]


def read_csv(path):
    """提携中プログラムのCSVを読む。ID → (案件名, ジャンル, 開始日, 終了日) を返す。
       列は プログラムID／プログラム名／広告主名／カテゴリ／開始日／終了日／提携日"""
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
                start = r[4].strip().replace("/", "-") if len(r) > 4 else ""
                stop = r[5].strip().replace("/", "-") if len(r) > 5 else ""
                out[r[0].strip()] = (r[1].strip(), r[3].strip(), start, stop)
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


def mat_key(code):
    """a8mat の前半2つは、案件ごとに決まっている。
       テキストリンクには mid= が入らないので、同じ案件の画像バナーと
       突き合わせるための鍵として使う。"""
    m = re.search(r"a8mat=([0-9A-Z]+)\+([0-9A-Z]+)", code, re.I)
    return f"{m.group(1)}+{m.group(2)}" if m else ""


def name_from_code(code):
    """CSVが無いときの代わり。広告コードのリンク文言を案件名として使う。
       画像バナーだけのコードには文言が入っていないので、その場合は空。"""
    m = re.search(r"<a[^>]*>(.*?)</a>", code, re.I | re.S)
    if not m:
        return ""
    txt = re.sub(r"<[^>]+>", "", m.group(1))
    txt = re.sub(r"\s+", " ", txt).strip()
    if len(txt) < 2 or re.fullmatch(r"[詳細はこちらコチラ？!。、 ]+", txt):
        return ""
    return txt


def shape(code):
    """広告の形を見分ける。出せる場所が形で決まるため。

         tile … 四角いバナー（300x250 など）。記事下に、関連記事と同じ
                タイルの形で出す。写真の位置にちょうど収まる
         wide … 横長のバナー（468x60 など）。タイルの写真の位置に入れると
                スマホで文字が読めなくなるので、記事下には出さない
         text … 文字だけのリンク。写真の位置が空くので、記事下には出さない

       wide と text も捨てずに取り込む。出す場所が決まったら、
       content/site.json の where を書き換えるだけで使える。"""
    m = re.search(r'<img[^>]*\bwidth="(\d+)"[^>]*\bheight="(\d+)"', code, re.I)
    if "svt/bgt" not in code:
        return "text"
    if not m:
        return "tile"          # 大きさの指定が無いバナーは、そのまま扱う
    w, h = int(m.group(1)), int(m.group(2))
    if w <= 1 or h <= 1:
        return "text"          # 計測用の1x1しか無い＝文字だけのリンク
    return "wide" if w / h >= 1.6 else "tile"


SHAPE_LABEL = {"tile": "四角いバナー", "wide": "横長バナー", "text": "テキストリンク"}


def classify(name, genre):
    """案件名とジャンルから、出す先のカテゴリーを決める。"""
    blob = f"{name} {genre}"
    for pat, cats, label in RULES:
        if re.search(pat, blob, re.I):
            return cats, label
    return [], "その他"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="提携中プログラムのCSV（省略可。省くとリンクの文言を案件名として使う）")
    ap.add_argument("--codes", required=True,
                    help="a8-collect.js で集めたコードを保存したファイル")
    ap.add_argument("--where", default="article_end",
                    choices=["article_end", "side", "none"],
                    help="出す場所（既定は記事の下）")
    ap.add_argument("--keep-unknown", action="store_true",
                    help="CSVに無い広告も残す（既定は外す）")
    ap.add_argument("--size", default="",
                    help="使うバナーの大きさを絞る（例 300x250,336x280）。"
                         "テキストリンクは常に残す。空なら絞らない")
    ap.add_argument("--apply", action="store_true",
                    help="content/site.json に書き込む")
    ap.add_argument("--replace", action="store_true",
                    help="いまの広告設定を捨てて入れ替える（既定は追加）")
    args = ap.parse_args()

    programs = read_csv(args.csv) if args.csv else {}
    codes = split_codes(io.open(args.codes, encoding="utf-8").read())
    if not codes:
        raise SystemExit("広告コードが見つかりませんでした。")

    # a8mat の前半（案件ごとに決まっている）で、画像バナーとテキストリンクを
    # 突き合わせる。テキストリンクには mid= が入らず、画像バナーには
    # リンクの文言が入らないため、両方から1件ぶんの手がかりをまとめる。
    pid_by_mat, name_by_mat = {}, {}
    for c in codes:
        k = mat_key(c)
        if not k:
            continue
        pid, nm = program_id(c), name_from_code(c)
        if pid and k not in pid_by_mat:
            pid_by_mat[k] = pid
        if nm and k not in name_by_mat:
            name_by_mat[k] = nm

    # 掲載が終わった広告は使わない。CSVの「終了日」が今日より前のものと、
    # CSVに載っていないもの（提携が解除された／案件が消えた）を外す。
    # ただしCSVに無いものは「CSVより新しい提携」の可能性もあるので、
    # --drop-unknown を付けたときだけ外す。付けなければ数だけ知らせる。
    if programs:
        today = datetime.date.today().isoformat()
        ended, unknown_pid = [], []
        keep = []
        for c in codes:
            pid = program_id(c) or pid_by_mat.get(mat_key(c), "")
            if pid not in programs:
                # CSVに載っていない＝提携が切れているか、身元が分からない。
                # どちらにせよ案件名も終了日も引けないので、既定では外す。
                unknown_pid.append(c)
                if args.keep_unknown:
                    keep.append(c)
                continue
            stop = programs[pid][3]
            if stop and stop < today:
                ended.append((programs[pid][0], stop))
                continue
            keep.append(c)
        if ended:
            print(f"掲載が終わった案件を外しました（{len(ended)} 件）")
            for nm, d in ended[:6]:
                print(f"    ・{d} 終了：{nm[:44]}")
        if unknown_pid:
            state = "残しています" if args.keep_unknown else "外しました"
            print(f"CSVに見つからない広告が {len(unknown_pid)} 件（{state}）。"
                  "提携が解除されたか、CSVより新しい提携です")
        codes = keep

    # 形ごとに分ける。記事下に出せるのは四角いバナーだけだが、
    # 横長とテキストも取り込んでおく（出す場所が決まったら where を変える）。
    by_shape = {"tile": [], "wide": [], "text": []}
    for c in codes:
        by_shape[shape(c)].append(c)
    print("形の内訳：" + "、".join(
        f"{SHAPE_LABEL[k]} {len(v)}件" for k, v in by_shape.items() if v))

    # 大きさをさらに絞りたいとき（例：300x250だけにする）。
    # 表示のたびに1件が選ばれるので、縦横がばらばらだと記事の
    # レイアウトが動いてしまう。
    if args.size:
        want = {t.strip().lower() for t in args.size.split(",") if t.strip()}
        kept = []
        for c in by_shape["tile"]:
            m = re.search(r'<img[^>]*\bwidth="(\d+)"[^>]*\bheight="(\d+)"',
                          c, re.I)
            if m and f"{m.group(1)}x{m.group(2)}" in want:
                kept.append(c)
        print(f"四角いバナーを大きさで絞りました："
              f"{len(by_shape['tile'])} → {len(kept)} 件")
        by_shape["tile"] = kept

    # 同じカテゴリーに出すものは1つの枠にまとめる。
    # 枠の中に複数入れておくと、表示のたびに1件が選ばれる。
    # プログラムIDごとに、リンク文言から取れた名前を1つ覚えておく。
    # 画像バナーだけのコードは、同じ案件のテキストリンクから名前を借りる。
    groups = OrderedDict()
    unknown = []
    for kind in ("tile", "wide", "text"):
      for c in by_shape[kind]:
        k = mat_key(c)
        pid = program_id(c) or pid_by_mat.get(k, "")
        name, genre, start, stop = programs.get(pid, ("", "", "", ""))
        if not name:
            # CSVに無い（または --csv を省いた）ときは、リンクの文言を名前にする
            name = name_by_mat.get(k, "")
        cats, label = classify(name, genre)
        if not name:
            unknown.append(c[:70])
        key = (kind, tuple(cats), label)
        groups.setdefault(key, {"label": label, "cats": cats, "kind": kind,
                                "names": [], "ads": []})
        groups[key]["ads"].append({"html": c, "title": name, "date": start})
        if name and name not in groups[key]["names"]:
            groups[key]["names"].append(name)

    total = sum(len(v) for v in by_shape.values())
    print(f"\n広告コード {total} 件を {len(groups)} 枠にまとめました\n")
    items = []
    for (kind, cats, label), g in groups.items():
        # 記事下に出せるのは四角いバナーだけ。横長とテキストは、出す場所が
        # 決まるまで none にしておく（消さずに取っておく）
        where = args.where if (cats and kind == "tile") else "none"
        if not cats:
            cat_txt = "（振り分け先が決まらず。出さないに設定）"
        elif kind != "tile":
            cat_txt = f"{'、'.join(cats)}（形が合わないので、いまは出さない）"
        else:
            cat_txt = "、".join(cats)
        print(f"■ [{SHAPE_LABEL[kind]}] {label}：{len(g['ads'])} 件 → {cat_txt}")
        for n in g["names"][:6]:
            print(f"    ・{n[:52]}")
        if len(g["names"]) > 6:
            print(f"    …ほか {len(g['names']) - 6} 件")
        items.append({
            "name": f"{SHAPE_LABEL[kind]}／{label}（{len(g['ads'])}件）",
            "kind": kind,
            "where": where,
            "cats": list(cats),
            "ads": g["ads"],
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
