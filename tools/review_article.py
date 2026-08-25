#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""書き上がった記事をレビューし、問題があれば直してから公開する。

`tools/write_article.py` が本文を書いた **あと** に走らせる。
検査の基準は `docs/review-rules.md`（既存の禁止表現＋ダークパターン）。

  $ python3 tools/review_article.py --new              # 未公開の記事を全部
  $ python3 tools/review_article.py zojirushi-ck-ax08-kettle-review
  $ python3 tools/review_article.py --new --publish    # 直して公開まで
  $ python3 tools/review_article.py --new --check-only # 機械検査だけ（Claude を呼ばない）

やること
  ① 機械検査   禁止語・煽り表現・形の崩れを正規表現で拾う（tools/check_*.py と同じ基準）
  ② Claude     docs/review-rules.md と記事JSONを渡し、指摘と修正後の値を返させる
  ③ 適用       返ってきた値を articles.json に書き戻し、①をやり直す
  ④ 仕上げ     build.py と check_*.py を回す。--publish なら published を立てる

認証は write_article.py と同じ。Claude Code のログイン（サブスク）を使うので、
APIの従量課金は発生しない。--check-only なら `claude` コマンド自体が要らない。
"""
import json, io, os, re, sys, time, argparse, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 本文の生成・修正に任せる項目。slug・published・販売先URLは触らせない。
from write_article import (GEN_FIELDS, NG_WORDS, MIN_CHARS, MAX_CHARS,
                           run_claude, parse_json, body_chars, load)

# ---------------------------------------------------------------- 機械検査
# 断定・保証の表現。tools/check_text.py と同じ基準。
NG_CONTEXT = [
    r"最安値(?:です|でした|保証|を保証|！|。)",
    r"業界最安", r"日本最[安大高]",
]

# ダークパターン。docs/review-rules.md の分類に対応させる。
# 「見つけたら必ず直す」ものだけを入れる。判断が要るものは Claude に回す。
DARK = [
    # 「在庫が少ない・急げ」と読者を追い立てるもの
    ("緊急性",     r"在庫僅少|残りわずか|売り切れ間近|お早めに|今すぐ買|買い逃"),
    ("緊急性",     r"今だけ|本日限り|期間限定|まもなく終了|間もなく終了|タイムセール中"),
    # 閲覧者数・売れ行きの演出
    ("社会的証明", r"\d+\s*人が(?:見て|検討して|購入して)いま|話題沸騰|爆売れ|バカ売れ"),
    # 読者を貶して買わせるもの
    ("恥の植え付け", r"知らないと損|まだ.{0,6}使っていないん|情弱|買わない理由がな"),
    # 参考価格からの割引に見せる表示（価格そのものを書かない方針とも重なる）
    ("誤解を招く価格表示", r"\d+\s*%\s*OFF|割引価格|最安値(?:です|保証|！)"),
    ("隠れたコスト", r"送料無料(?:です|！)"),
    ("偽造広告",   r"広告では(?:あり)?ません"),
]

# 使ってよいHTMLタグ以外が混ざっていないか
OK_TAG = re.compile(r'</?(?:strong|em)>|<span class="mark-[ox]">|</span>')
ANY_TAG = re.compile(r"</?[a-zA-Z][^>]*>")

# {title, text} の形でなければならない項目
DICT_ITEMS = [("summary", None), ("not_for", "items"),
              ("highlights", "items"), ("next_problem", "items")]


def texts(v, path=""):
    """記事の中の文字列を、どこにあるかと一緒に取り出す。"""
    if isinstance(v, str):
        yield path, v
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from texts(x, f"{path}[{i}]")
    elif isinstance(v, dict):
        for k, x in v.items():
            yield from texts(x, f"{path}.{k}" if path else k)


SKIP = ("slug", "thumb", "amazon_url", "rakuten_url", "yahoo_url", "asin",
        "jan", "date", "updated", "category", "sub", "image_prompt", "facts")


def scan(a):
    """記事1本を機械検査する。返すのは指摘の一覧。"""
    hits = []
    for path, s in texts({k: v for k, v in a.items() if k not in SKIP}):
        plain = ANY_TAG.sub("", s)
        for w in NG_WORDS:
            if w in plain:
                hits.append(("禁止表現", path, f"「{w}」"))
        for pat in NG_CONTEXT:
            for m in re.finditer(pat, plain):
                hits.append(("断定・保証", path, f"「{m.group(0)}」"))
        for label, pat in DARK:
            for m in re.finditer(pat, plain):
                hits.append((f"ダークパターン／{label}", path, f"「{m.group(0)}」"))
        for t in ANY_TAG.finditer(s):
            if not OK_TAG.fullmatch(t.group(0)) and not t.group(0).startswith("<br"):
                hits.append(("使えないタグ", path, t.group(0)))

    # 形の崩れ。辞書なのに title も text も無いと、記事の側で
    # 空の行になったり、辞書の表記がそのまま出たりする。
    # （文字列だけの項目は昔からある書き方なので、そのままでよい）
    for key, sub in DICT_ITEMS:
        items = a.get(key) or []
        if sub:
            items = (items or {}).get(sub, []) if isinstance(items, dict) else []
        for i, x in enumerate(items):
            if isinstance(x, str):
                continue
            if not isinstance(x, dict) or not (x.get("title") or x.get("text")):
                hits.append(("形の崩れ", f"{key}[{i}]",
                             '文字列か {"title":…, "text":…} にする'))

    # 分量。tools/check_articles.py と同じ数え方にそろえる。
    n = body_chars({k: v for k, v in a.items() if k not in SKIP})
    if n < MIN_CHARS:
        hits.append(("分量", "本文", f"{n:,}字（下限 {MIN_CHARS:,}）"))
    if n > MAX_CHARS:
        hits.append(("分量", "本文", f"{n:,}字（上限 {MAX_CHARS:,}）"))

    # 同じ指摘は1回だけ
    return list(dict.fromkeys(hits))


# ---------------------------------------------------------------- Claude
SYSTEM = ("あなたは日本語の商品記事の校閲者です。"
          "返事はJSONオブジェクトそのものだけにしてください。"
          "前置き・あとがき・説明・コードフェンスは一切付けません。"
          "最初の文字は { で、最後の文字は } です。")

OUT_SHAPE = '''{
  "findings": [{"where": "どの項目か", "rule": "違反したルール", "problem": "何が問題か"}],
  "fixed": { "直した項目だけを、記事JSONと同じキー・同じ形で入れる" }
}'''


def build_prompt(a, rules, hits):
    """レビュー用のプロンプト。記事の全文と、機械検査の結果を渡す。"""
    found = "\n".join(f"・[{k}] {p}：{d}" for k, p, d in hits) or "（機械検査での指摘はありません）"
    body = {k: a[k] for k in GEN_FIELDS if k in a}
    return "\n".join([
        "次の記事を、下のレビュー基準に照らして点検し、問題があれば直してください。",
        "",
        "================ レビュー基準 ================",
        rules,
        "",
        "================ 機械検査で先に見つかった問題 ================",
        found,
        "上の指摘はすべて直してください。ほかにも基準に反する箇所があれば、あわせて直します。",
        "",
        "================ 記事（JSON） ================",
        json.dumps(body, ensure_ascii=False, indent=1),
        "",
        "================ 出力の決まり ================",
        "・JSONだけを返す。前置きも、コードフェンスも付けない。",
        "・次の形に従う。",
        OUT_SHAPE,
        "・fixed には**直した項目だけ**を入れる。直していない項目は入れない。",
        "・項目の形（配列か辞書か、キー名）は元の記事と同じにする。",
        "・直すところが無ければ findings も fixed も空にする。",
        f"・本文の合計は {MIN_CHARS}〜{MAX_CHARS - 300} 文字の範囲を保つ。",
        "・HTMLは <strong> と <em> だけ。表の丸印は "
        '<span class="mark-o">◎</span> / <span class="mark-x">×</span> のみ可。',
        "・価格は書かない。変動するため。",
    ])


def apply_fixed(a, fixed):
    """返ってきた修正を書き戻す。触らせない項目は弾く。"""
    changed = []
    for k, v in (fixed or {}).items():
        if k not in GEN_FIELDS:
            continue
        if v in (None, "", [], {}) or a.get(k) == v:
            continue
        a[k] = v
        changed.append(k)
    if changed:
        a["updated"] = time.strftime("%Y-%m-%d")
    return changed


# ---------------------------------------------------------------- 仕上げ
def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()


def finish(publish_slugs, do_push):
    """サイトを生成し、CIと同じ検査を通す。通ったら公開・push まで。"""
    print("\nサイトを生成して検査します …")
    for cmd in (["python3", "build.py"],
                ["python3", "tools/check_articles.py"],
                ["python3", "tools/check_text.py"],
                ["python3", "tools/check_images.py"]):
        code, out = run(cmd)
        name = cmd[-1]
        if code != 0:
            print(f"  ✗ {name}\n{out}")
            return 1
        print(f"  ✓ {name}")

    if not do_push:
        return 0

    msg = "記事をレビューして公開（" + "、".join(publish_slugs) + "）"
    for cmd in (["git", "add", "-A"],
                ["git", "commit", "-m", msg],
                ["git", "push"]):
        code, out = run(cmd)
        if code != 0 and "nothing to commit" not in out:
            print(f"  ✗ {' '.join(cmd)}\n{out}")
            return 1
    print("  ✓ コミットして push しました")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*", help="対象の記事slug")
    ap.add_argument("--new", action="store_true",
                    help="未公開（published:false）の記事をすべて対象にする")
    ap.add_argument("--all", action="store_true", help="公開中の記事も含めて全部")
    ap.add_argument("--model", default="opus", help="opus / sonnet")
    ap.add_argument("--rounds", type=int, default=2,
                    help="直してから見直す回数の上限")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--check-only", action="store_true",
                    help="機械検査だけ。Claude を呼ばず、書き換えもしない")
    ap.add_argument("--publish", action="store_true",
                    help="指摘が残らなければ published:true にする")
    ap.add_argument("--push", action="store_true",
                    help="コミットして push まで行う（--publish と併用）")
    ap.add_argument("--dry-run", action="store_true", help="書き込まない")
    args = ap.parse_args()

    arts = load("content/articles.json")
    rules = io.open(os.path.join(ROOT, "docs", "review-rules.md"),
                    encoding="utf-8").read()

    if args.all:
        targets = list(arts)
    elif args.new:
        targets = [a for a in arts if not a.get("published")]
    else:
        want = set(args.slugs)
        targets = [a for a in arts if a.get("slug") in want]
        for m in want - {a.get("slug") for a in targets}:
            print(f"::warning::{m} という記事がありません", file=sys.stderr)

    if not targets:
        print("対象の記事がありません。--new か --all、または slug を指定してください。")
        return 0

    print(f"{len(targets)} 本をレビューします\n")
    cost = 0.0
    ok, ng = [], []

    for i, a in enumerate(targets, 1):
        slug = a.get("slug", "?")
        print(f"[{i}/{len(targets)}] {slug}")
        hits = scan(a)
        for k, p, d in hits:
            print(f"    △ [{k}] {p}：{d}")

        if args.check_only:
            (ng if hits else ok).append(slug)
            if not hits:
                print("    ✓ 指摘なし")
            continue

        for r in range(1, args.rounds + 1):
            try:
                out, c = run_claude(build_prompt(a, rules, hits),
                                    args.model, args.timeout)
                cost += c
                res = parse_json(out)
            except RuntimeError as ex:
                print(f"    ✗ レビューできませんでした：{ex}")
                break

            for f in res.get("findings") or []:
                print(f"    ● {f.get('where','')}：{f.get('problem','')}"
                      f"（{f.get('rule','')}）")
            if args.dry_run:
                break

            changed = apply_fixed(a, res.get("fixed"))
            if not changed:
                print("    ✓ 直すところはありませんでした" if r == 1
                      else "    ✓ これ以上の修正はありません")
                break
            print(f"    ✎ 直した項目：{'、'.join(changed)}")

            hits = scan(a)
            if not hits:
                break
            if r == args.rounds:
                print("    △ 指摘が残ったまま上限に達しました")

        hits = scan(a)
        if hits:
            ng.append(slug)
            for k, p, d in hits:
                print(f"    ✗ 残った指摘 [{k}] {p}：{d}")
        else:
            ok.append(slug)
            print("    ✓ 基準を満たしました")
            if args.publish and not args.dry_run:
                a["published"] = True
                print("    → published: true")

    if not args.dry_run and not args.check_only:
        with io.open(os.path.join(ROOT, "content", "articles.json"),
                     "w", encoding="utf-8") as f:
            json.dump(arts, f, ensure_ascii=False, indent=1)
        print("\ncontent/articles.json を更新しました。")

    print(f"\n合格 {len(ok)} 本 / 要確認 {len(ng)} 本"
          + (f" / 参考コスト ${cost:.2f}" if cost else ""))
    if ng:
        print("要確認：" + "、".join(ng))

    code = 0
    if args.publish and ok and not args.dry_run:
        code = finish(ok, args.push)
    return 1 if (ng or code) else 0


if __name__ == "__main__":
    sys.exit(main())
