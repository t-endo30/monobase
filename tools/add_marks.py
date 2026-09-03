#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事の本文はそのままに、蛍光ペン（==…==）だけを足す。

`==この語==` はサイトの記法で、テンプレートが黄色いマーカーに変換する。
流し読みでも要点が拾えるようにするための仕掛けなので、
0〜2か所しか無い記事は、読者が目を留める場所を失う。

書き直すと本文ごと変わってしまうので、この道具は
**マーカーの位置だけ** を決めさせる。文章は1文字も変えない。

  $ python3 tools/add_marks.py --check          # 足りない記事を数えるだけ
  $ python3 tools/add_marks.py <slug> ...       # 指定した記事に足す
  $ python3 tools/add_marks.py --all            # 足りない記事すべてに足す

更新日は動かさない。マーカーは表示上の強調であって、内容の更新ではない。
"""
import argparse, io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from write_article import GEN_FIELDS, run_claude, parse_json, load, save_article

MIN_MARKS = 4
MAX_MARKS = 10

# マーカーを置いてよい場所。読者が判断を持ち帰るところに限る。
# 表の中（spec）や FAQ の質問文には置かない。
TARGET_FIELDS = ["summary", "highlights", "good_for", "not_for",
                 "scenes", "sections", "conclusion", "personal_note",
                 "voices_after", "proscons_note"]

SYSTEM = ("あなたは日本語の商品記事の編集者です。"
          "返事はJSONオブジェクトそのものだけにしてください。"
          "前置き・あとがき・説明・コードフェンスは一切付けません。"
          "最初の文字は { で、最後の文字は } です。")


def count_marks(v):
    return len(re.findall(r"==[^=]+==", json.dumps(v, ensure_ascii=False)))


def build_prompt(a, have):
    body = {k: a[k] for k in TARGET_FIELDS if k in a}
    return "\n".join([
        "次の記事に、蛍光ペンの指定（==この語==）を足してください。",
        "",
        "【この作業の趣旨】",
        "・==この語== はこのサイトの記法で、テンプレートが黄色いマーカーに変換します。",
        "・流し読みでも要点が拾えるようにするための仕掛けです。",
        f"・いまこの記事には {have} か所しかありません。"
        f"記事全体で {MIN_MARKS}〜{MAX_MARKS} か所になるようにしてください。",
        "",
        "【守ること（最重要）】",
        "・<strong>文章を書き換えないでください。</strong>"
        "語順・語尾・句読点・漢字かなの使い分けまで、1文字も変えません。",
        "・やることは、既存の文のどこかを == と == で挟むことだけです。",
        "・すでに == で挟まれている箇所は、そのまま残します。",
        "・1段落（1つの文字列）につき1か所までです。",
        "・挟むのは、その段落でいちばん重要な結論・判断・条件のひとことです。"
        "10〜30文字くらいの、意味のまとまった範囲にします。",
        "・単なる商品名や数値だけを挟まないでください。"
        "読者の判断に効く言い回しを選びます。",
        "・見出し（sections の heading、summary の title など）には付けません。"
        "本文（text / paras / 段落の文字列）に付けます。",
        "",
        "================ 記事（JSON） ================",
        json.dumps(body, ensure_ascii=False, indent=1),
        "",
        "================ 出力の決まり ================",
        "・JSONだけを返す。前置きも、コードフェンスも付けない。",
        "・上と同じキー・同じ形で、<strong>マーカーを足した項目だけ</strong>を返す。",
        "・触っていない項目は返さない。",
        "・文字列は、== を足したこと以外はまったく同じであること。",
    ])


def strip_marks(s):
    return re.sub(r"==([^=]+)==", r"\1", s)


def same_text(before, after):
    """== を外したら元と同じか。文章が書き換えられていないことの確認。"""
    return strip_marks(before) == strip_marks(after)


def verify(orig, new, path=""):
    """返ってきた値を、文章が変わっていないものだけ受け入れる。"""
    if isinstance(orig, str) and isinstance(new, str):
        return new if same_text(orig, new) else orig
    if isinstance(orig, list) and isinstance(new, list) and len(orig) == len(new):
        return [verify(o, n) for o, n in zip(orig, new)]
    if isinstance(orig, dict) and isinstance(new, dict):
        return {k: (verify(v, new[k]) if k in new else v) for k, v in orig.items()}
    return orig


def trim(a, keep):
    """多すぎるマーカーを機械的に減らす。

       生成に任せると、記事によっては全段落に付けてくる（実際に31か所に
       なった）。全体が黄色くなると、強調しているつもりで何も強調できない。
       文章は変えずに == を外すだけなので、機械的に落として構わない。
       残すのは前のほうの項目（結論・強み）で、後ろから外していく。"""
    removed = 0
    have = count_marks({k: a.get(k) for k in GEN_FIELDS})
    over = have - keep
    if over <= 0:
        return 0

    def walk(v):
        nonlocal over, removed
        if isinstance(v, str):
            while over > 0 and re.search(r"==[^=]+==", v):
                v = re.sub(r"==([^=]+)==", r"\1", v, count=1)
                over -= 1
                removed += 1
            return v
        if isinstance(v, list):
            return [walk(x) for x in reversed(v)][::-1]
        if isinstance(v, dict):
            return {k: walk(x) for k, x in reversed(list(v.items()))}
        return v

    # 後ろの項目から外す。まとめ→本文→強み→結論の順で残りやすくする。
    for k in reversed(TARGET_FIELDS):
        if over <= 0:
            break
        if k in a:
            a[k] = walk(a[k])
    return removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--all", action="store_true", help="足りない記事すべて")
    ap.add_argument("--check", action="store_true", help="数えるだけ")
    ap.add_argument("--trim", action="store_true",
                    help="多すぎる記事を、上限まで機械的に減らす（生成AIを呼ばない）")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    arts = load("content/articles.json")
    lack = [a for a in arts
            if count_marks({k: a.get(k) for k in GEN_FIELDS}) < MIN_MARKS]
    over = [a for a in arts
            if count_marks({k: a.get(k) for k in GEN_FIELDS}) > MAX_MARKS]

    if args.trim:
        for a in over:
            before = count_marks({k: a.get(k) for k in GEN_FIELDS})
            n = trim(a, MAX_MARKS)
            after = count_marks({k: a.get(k) for k in GEN_FIELDS})
            save_article(a)
            print(f"  {a['slug']}: {before} → {after} か所（{n} 個を外した）")
        print(f"\n{len(over)} 本を上限 {MAX_MARKS} か所まで減らしました。")
        return 0

    if args.check:
        print(f"蛍光ペンが {MIN_MARKS} か所未満の記事：{len(lack)} 本")
        for a in lack:
            print(f"  {count_marks({k: a.get(k) for k in GEN_FIELDS}):>2} か所  {a['slug']}")
        print(f"\n{MAX_MARKS} か所を超える記事：{len(over)} 本"
              "（--trim で減らせます）")
        for a in over:
            print(f"  {count_marks({k: a.get(k) for k in GEN_FIELDS}):>2} か所  {a['slug']}")
        return 0

    if args.all:
        targets = lack
    else:
        want = set(args.slugs)
        targets = [a for a in arts if a.get("slug") in want]
    if not targets:
        print("対象がありません。--all か slug を指定してください。")
        return 0

    print(f"{len(targets)} 本に蛍光ペンを足します（文章は変えません）\n")
    for i, a in enumerate(targets, 1):
        slug = a["slug"]
        have = count_marks({k: a.get(k) for k in GEN_FIELDS})
        print(f"[{i}/{len(targets)}] {slug}（いま {have} か所）… ", end="", flush=True)
        try:
            out, _ = run_claude(build_prompt(a, have), args.model, args.timeout)
            res = parse_json(out)
        except RuntimeError as ex:
            print(f"失敗\n    {ex}")
            continue

        changed = 0
        for k, v in res.items():
            if k not in TARGET_FIELDS or k not in a:
                continue
            fixed = verify(a[k], v)
            if fixed != a[k]:
                a[k] = fixed
                changed += 1
        now = count_marks({k: a.get(k) for k in GEN_FIELDS})
        # 更新日は動かさない。マーカーは表示上の強調で、内容の更新ではない。
        save_article(a)
        mark = "✓" if now >= MIN_MARKS else "△"
        print(f"{mark} {have} → {now} か所（{changed} 項目）")

    print("\ncontent/articles.json を更新しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
