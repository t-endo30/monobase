#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""バリューコマースの広告コードを取り込み、案件名とカテゴリーを自動で割り当てる。

A8と同じ考え方だが、2点だけ違う。

  コードに大きさが書かれていない
    A8のバナーは <img width="300" height="250"> のように大きさが
    コードに直接入っているが、VCの広告コードは
      <script src=".../jsbanner?sid=..&pid=..">
      <noscript><a href="ck.jp.ap.valuecommerce.com/..."><img src="ad.jp.ap.valuecommerce.com/.../gifbanner?sid=..&pid=.."></a></noscript>
    という形で、大きさはサーバ側でpid（サイト×案件の組）ごとに決まっている。
    このツールは、img の指す先を実際に取得して大きさを調べる
    （gifbanner は 302 で本当の画像へ飛ぶので、そこを見る）。

  CSVにコードの手がかりが無い
    A8の mid= はCSVの「プログラムID」と直接一致するが、VCの pid は
    サイト×案件で決まる別の番号で、CSVのプログラムIDとは一致しない。
    そのため、tools/vc-collect.js がページの見出し（案件名）も
    一緒に拾っておき、それをCSVの「プログラム名」「広告主名」と
    文字列で突き合わせてカテゴリーを決める。

使い方
  1. VCで「提携中のプログラム」→ CSVダウンロード
  2. 各案件の「広告作成」ページで tools/vc-collect.js を実行し、
     出力をファイルに追記（案件の数だけ繰り返す）
  3. $ python3 tools/import_vc.py --csv programs.csv --codes codes.txt
     （中身を確認するだけ。--apply で content/site.json に書き込む）

  $ python3 tools/import_vc.py --csv programs.csv --codes codes.txt --apply
"""
import argparse, csv, datetime, io, json, os, re, sys, time
import urllib.request, urllib.error
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_a8 import RULES, classify  # 分類の対応表はA8と共通で使う

ENCODINGS = ["cp932", "utf-8-sig", "utf-16", "euc_jp"]

HOST = re.compile(r"valuecommerce\.com", re.I)
SID_PID = re.compile(r"[?&]sid=(\d+)[^\"'&]*&pid=(\d+)", re.I)
IMG_SRC = re.compile(r'<img[^>]*\bsrc="([^"]+gifbanner[^"]*)"', re.I)


def read_csv(path):
    """提携中プログラムのCSV。列は
       広告主ID/広告主名/広告主サイトURL/会社名/プログラムID/プログラム名/…/
       提携ステータス/期間開始/期間終了/…/カテゴリー1..4
       プログラム名・広告主名・カテゴリーを、あとで案件名と突き合わせるために使う。"""
    last = None
    for enc in ENCODINGS:
        try:
            raw = io.open(path, encoding=enc).read()
        except (UnicodeDecodeError, LookupError) as ex:
            last = ex
            continue
        rows = list(csv.reader(io.StringIO(raw)))
        if rows and len(rows[0]) >= 10:
            header = rows[0]
            idx = {h: i for i, h in enumerate(header)}
            need = ["広告主名", "プログラム名", "期間終了", "カテゴリー1"]
            if not all(k in idx for k in need):
                continue
            out = []
            for r in rows[1:]:
                if len(r) <= idx["プログラム名"]:
                    continue
                out.append({
                    "advertiser": r[idx["広告主名"]].strip(),
                    "program": r[idx["プログラム名"]].strip(),
                    "stop": r[idx["期間終了"]].strip().replace("/", "-"),
                    "cats": [r[idx[k]].strip() for k in
                            ("カテゴリー1", "カテゴリー2", "カテゴリー3", "カテゴリー4")
                            if idx.get(k) is not None and len(r) > idx[k]
                            and r[idx[k]].strip()],
                })
            if out:
                print(f"CSVを {enc} として読みました（{len(out)} 件の提携）")
                return out
    raise SystemExit(f"CSVを読めませんでした：{last}")


def find_program(name, programs):
    """案件名（ページの見出し）から、CSVの行をゆるく突き合わせる。
       双方の文字列が、互いの先頭部分を含み合っていれば同じ案件とみなす
       （VCは「Yahoo!ショッピング(ヤフー ショッピング)」のように、
       広告作成ページの見出しとCSVの表記が完全一致しないことがある）。"""
    name = re.sub(r"[\s　]+", "", name or "")
    if not name:
        return None
    best = None
    for p in programs:
        for key in ("program", "advertiser"):
            cand = re.sub(r"[\s　]+", "", p[key])
            if not cand:
                continue
            if cand in name or name in cand or cand[:8] == name[:8]:
                if best is None:
                    best = p
    return best


def split_blocks(text):
    """tools/vc-collect.js の出力を、===案件名=== ごとのかたまりに分ける。"""
    parts = re.split(r"(?m)^===(.*)===\s*$", text)
    # parts[0] は最初の見出しより前の余り（空のはず）
    blocks = []
    for i in range(1, len(parts), 2):
        name = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        codes = [c.strip() for c in re.split(r"(?m)^\s*-{3,}\s*$", body) if c.strip()]
        for c in codes:
            blocks.append((name, c))
    if blocks:
        return blocks
    # 見出しが無い（手で貼っただけ）ときは、案件名なしの1本として扱う
    codes = [c.strip() for c in re.split(r"(?m)^\s*-{3,}\s*$", text) if c.strip()]
    return [("", c) for c in codes]


def to_static(code):
    """<script src=".../jsbanner?...">形式を、静的サイトでも動く
       <a><img></a> の形に直す。noscript の中身がすでにあればそれを使う。"""
    m = re.search(r"<noscript>(.*?)</noscript>", code, re.I | re.S)
    if m and HOST.search(m.group(1)):
        return m.group(1).strip()
    if "<a" in code.lower() and HOST.search(code):
        return code.strip()
    # script だけのとき（noscriptが無い旧型）は sid/pid から組み立てる
    m = SID_PID.search(code)
    if not m:
        return code.strip()
    sid, pid = m.group(1), m.group(2)
    return (f'<a href="https://ck.jp.ap.valuecommerce.com/servlet/referral'
            f'?sid={sid}&pid={pid}" rel="nofollow">'
            f'<img src="https://ad.jp.ap.valuecommerce.com/servlet/gifbanner'
            f'?sid={sid}&pid={pid}" border="0"></a>')


_size_cache = {}


def fetch_size(img_url, timeout=10):
    """gifbanner のURLを実際に取りに行き、リダイレクト先の画像から
       縦横を読む。取れなければ None（テキストリンク扱いにする）。"""
    if img_url.startswith("//"):
        img_url = "https:" + img_url
    if img_url in _size_cache:
        return _size_cache[img_url]
    size = None
    try:
        req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read(2_000_000)
        size = _read_image_size(data)
    except Exception:                                     # noqa: BLE001
        size = None
    _size_cache[img_url] = size
    return size


def _read_image_size(data):
    """PILを使わず、GIF/PNG/JPEGのヘッダーから縦横だけ読む
       （このツール以外に依存を増やしたくないため）。"""
    if data[:6] in (b"GIF87a", b"GIF89a"):
        w = data[6] | (data[7] << 8)
        h = data[8] | (data[9] << 8)
        return (w, h)
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        w = int.from_bytes(data[16:20], "big")
        h = int.from_bytes(data[20:24], "big")
        return (w, h)
    if data[:2] == b"\xff\xd8":  # JPEG
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3):
                h = int.from_bytes(data[i + 5:i + 7], "big")
                w = int.from_bytes(data[i + 7:i + 9], "big")
                return (w, h)
            seglen = int.from_bytes(data[i + 2:i + 4], "big")
            i += 2 + seglen
        return None
    return None


def shape_of(code):
    """コードの形を見分ける。img が無ければテキストリンク。
       画像が取れれば縦横比で tile/wide を決める（A8のshape()と同じ基準）。"""
    m = IMG_SRC.search(code)
    if not m:
        return "text", None
    size = fetch_size(m.group(1))
    if not size:
        return "text", None
    w, h = size
    if w <= 1 or h <= 1:
        return "text", size
    return ("wide" if w / h >= 1.6 else "tile"), size


SHAPE_LABEL = {"tile": "四角いバナー", "wide": "横長バナー", "text": "テキストリンク"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", help="提携中プログラムのCSV（省略可）")
    ap.add_argument("--codes", required=True,
                    help="tools/vc-collect.js で集めたコードを保存したファイル")
    ap.add_argument("--where", default="article_end",
                    choices=["article_end", "side", "none"])
    ap.add_argument("--keep-unknown", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--replace", action="store_true",
                    help="いまの広告設定を捨てて入れ替える（既定は追加）")
    args = ap.parse_args()

    programs = read_csv(args.csv) if args.csv else []
    text = io.open(args.codes, encoding="utf-8").read()
    blocks = split_blocks(text)
    if not blocks:
        raise SystemExit("広告コードが見つかりませんでした。")

    today = datetime.date.today().isoformat()
    groups = OrderedDict()
    unknown = []
    ended = []
    seen_pid = set()

    print(f"取り込むコード {len(blocks)} 件。大きさを実際に取得して調べます…")
    for name, raw in blocks:
        code = to_static(raw)
        m = SID_PID.search(code)
        pid = m.group(2) if m else code[:40]
        if pid in seen_pid:
            continue
        seen_pid.add(pid)

        prog = find_program(name, programs) if programs else None
        if programs and not prog:
            unknown.append(name or code[:50])
        if prog and prog["stop"] and prog["stop"] < today:
            ended.append((prog["program"], prog["stop"]))
            continue

        blob = f"{name} {(prog or {}).get('program','')} {' '.join((prog or {}).get('cats', []))}"
        cats, label = classify(blob, "")
        if not label or label == "その他":
            label = name or (prog or {}).get("advertiser") or "バリューコマース"

        kind, size = shape_of(code)
        where = (args.where if cats else "none") if kind == "tile" else "none"
        cat_txt = ("、".join(cats) if cats else
                   ("（振り分け先が決まらず。出さないに設定）" if kind == "tile"
                    else "（在庫として保管。いまは出さない）"))
        sizetxt = f"{size[0]}x{size[1]}" if size else "?"
        print(f"■ [{SHAPE_LABEL[kind]} {sizetxt}] {label}：{name or '(名称不明)'} → {cat_txt}")

        key = (kind, tuple(cats), label)
        groups.setdefault(key, {"label": label, "cats": cats, "kind": kind, "ads": []})
        groups[key]["ads"].append({
            "html": code, "title": name or label, "date": today,
            "size": (f"{size[0]}x{size[1]}" if size else ""),
        })

    if ended:
        print(f"\n提携が終了した案件を外しました（{len(ended)} 件）")
        for nm, d in ended[:6]:
            print(f"    ・{d} 終了：{nm[:44]}")
    if unknown:
        print(f"\n△ CSVで見つからない案件名が {len(unknown)} 件あります"
              "（カテゴリーは付けられません。案件名の表記ゆれの可能性があります）")
        for u in unknown[:6]:
            print(f"    {u[:60]}")

    items = []
    for (kind, cats, label), g in groups.items():
        items.append({
            "name": f"{SHAPE_LABEL[kind]}／{label}（{len(g['ads'])}件）",
            "kind": kind, "where": (args.where if (cats and kind == 'tile') else 'none'),
            "cats": list(cats), "ads": g["ads"],
        })

    total = sum(len(g["ads"]) for g in groups.values())
    print(f"\n広告コード {total} 件を {len(items)} 枠にまとめました")

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
        f.write("\n")
    print(f"\ncontent/site.json に {len(items)} 枠を書き込みました。")
    print("次にやること：python3 build.py で反映し、記事を開いて表示を確かめる")
    return 0


if __name__ == "__main__":
    sys.exit(main())
