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
                           run_claude, parse_json, body_chars, load,
                           kind_of, KIND_FRAMES, PUBLISH_SCORE,
                           MIN_CHARS_UNBACKED,
                           FAKE_EXPERIENCE, FAKE_REVIEW_NUM, AMAZON_MISLEAD,
                           VAGUE_RIVAL, CARE_CLAIM, AI_PHRASE, AI_PHRASE_LIMIT,
                           NEGATION, save_article)

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

    # ---- 2026-09-03 に統合した品質ルール --------------------------------
    # 打ち消し・疑問の文脈は拾わない（「実測したわけではありません」
    # 「購入前に実測してください」「治りますか？」は問題ない）。
    def find(pat, plain_text):
        for m in pat.finditer(plain_text):
            if NEGATION.match(plain_text[m.end():m.end() + 40]):
                continue
            yield m.group(0)

    ai_hits = 0
    for path, s_ in texts({k: v for k, v in a.items() if k not in SKIP}):
        pl = ANY_TAG.sub("", s_)
        for label, pat in (("実体験の捏造", FAKE_EXPERIENCE),
                           ("確認できない口コミ数値", FAKE_REVIEW_NUM),
                           ("Amazonとの関係の誤認", AMAZON_MISLEAD),
                           ("実在しない比較対象", VAGUE_RIVAL)):
            for w in find(pat, pl):
                hits.append((label, path, f"「{w}」"))
        if a.get("category") in ("beauty", "health"):
            for w in find(CARE_CLAIM, pl):
                hits.append(("効果の断定（薬機法）", path, f"「{w}」"))
        ai_hits += len(list(find(AI_PHRASE, pl)))

    if ai_hits > AI_PHRASE_LIMIT:
        hits.append(("AIらしい定型表現", "本文全体",
                     f"{ai_hits}回（上限 {AI_PHRASE_LIMIT}）"))

    # 記事タイプに合わない枠。セール記事にレビュー用の見出しを入れない等。
    kind = kind_of(a)
    allowed = {x.strip() for x in KIND_FRAMES[kind][1].replace("/", " ").split()}
    for key in ("rating", "highlights", "scenes", "voices", "good_for", "not_for"):
        v = a.get(key)
        has = bool(v.get("items")) if isinstance(v, dict) else bool(v)
        if has and key not in allowed and not (kind == "review" and key == "scenes"):
            hits.append(("記事タイプに合わない枠", key,
                         f"{kind} 記事では使わない枠"))

    # 評価の根拠。数字だけが独り歩きしないよう、内訳を必ず書かせる。
    rating = a.get("rating") or {}
    if rating.get("score"):
        bd = ANY_TAG.sub("", str(rating.get("breakdown") or ""))
        if len(bd) < 20:
            hits.append(("評価の根拠不足", "rating.breakdown",
                         f"内訳が {len(bd)}字。何を評価し何を減点したかを書く"))

    # 裏づけが無いのに rating / spec を出していないか。
    # 公式情報が無いこと自体は問題ではない。無いのに数字を出すのが問題。
    facts = a.get("facts") or []
    if isinstance(facts, str):
        facts = [facts]
    backed = bool(facts) or bool((a.get("official_url") or "").strip())
    if not backed:
        if rating.get("score"):
            hits.append(("裏づけのない rating", "rating",
                         "公式仕様も official_url も無い。キーごと省く"))
        if (a.get("spec") or {}).get("rows"):
            hits.append(("裏づけのない spec", "spec",
                         "公式仕様も official_url も無い。キーごと省く"))

    # まとめの情報源と最終確認日
    concl = a.get("conclusion")
    concl = "".join(concl) if isinstance(concl, list) else (concl or "")
    if concl and "最終確認日" not in ANY_TAG.sub("", concl):
        hits.append(("情報源の明示不足", "conclusion",
                     "最終確認日（YYYY年MM月DD日）が無い"))

    # 分量。tools/check_articles.py と同じ数え方にそろえる。
    n = body_chars({k: v for k, v in a.items() if k not in SKIP})
    # rating・spec を省いたぶん短くなるのは正しい。裏づけの無い記事は下限を下げる。
    floor = MIN_CHARS if backed else MIN_CHARS_UNBACKED
    if n < floor:
        hits.append(("分量", "本文", f"{n:,}字（下限 {floor:,}）"))
    if n > MAX_CHARS:
        hits.append(("分量", "本文", f"{n:,}字（上限 {MAX_CHARS:,}）"))

    # 同じ指摘は1回だけ
    return list(dict.fromkeys(hits))


# 採点の項目。docs/review-rules.md の「6. 採点と公開基準」と同じ並び。
SCORE_KEYS = [
    ("fact_accuracy", "事実の正確性"),
    ("source_reliability", "情報源の信頼性"),
    ("original_analysis", "独自分析"),
    ("editorial_quality", "編集品質"),
    ("template_avoidance", "テンプレート量産感の少なさ"),
    ("purchase_helpfulness", "購入判断への有用性"),
    ("legal_safety", "法令・表現上の安全性"),
    ("amazon_compliance", "Amazon関連ルールへの配慮"),
]


# ---------------------------------------------------------------- Claude
SYSTEM = ("あなたは日本語の商品記事の校閲者です。"
          "返事はJSONオブジェクトそのものだけにしてください。"
          "前置き・あとがき・説明・コードフェンスは一切付けません。"
          "最初の文字は { で、最後の文字は } です。")

OUT_SHAPE = '''{
  "findings": [{"where": "どの項目か", "rule": "違反したルール", "problem": "何が問題か"}],
  "fixed": { "直した項目だけを、記事JSONと同じキー・同じ形で入れる" },
  "removed": ["削除すべき項目のキー名。裏づけの無い spec や rating など。無ければ空配列"],
  "score": {"fact_accuracy": 0, "source_reliability": 0, "original_analysis": 0,
            "editorial_quality": 0, "template_avoidance": 0,
            "purchase_helpfulness": 0, "legal_safety": 0,
            "amazon_compliance": 0, "total": 0, "notes": "低い項目の理由を1〜2文"},
  "blockers": ["85点以上でも公開できない理由があれば書く。無ければ空配列"]
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
        "・項目をまるごと削るべきときは、fixed に空の値を入れるのではなく "
        "removed にキー名を並べる（fixed で空にしても消えない）。"
        "裏づけの無い spec や rating を落とすときはこちらを使う。",
        "・項目の形（配列か辞書か、キー名）は元の記事と同じにする。",
        "・直すところが無ければ findings も fixed も空にする。",
        "・score は**直したあとの記事**に対する採点。甘く付けない。",
        f"・blockers には、総合 {PUBLISH_SCORE} 点以上でも公開できない理由"
        "（架空情報・架空レビュー・架空体験・未確認スペック・誤った商品情報・"
        "医療的効果の断定・Amazonとの関係を誤認させる表現・根拠のない評価・"
        "商品名を入れ替えれば他の記事にも使える文章）があれば書く。",
        f"・本文の合計は {MIN_CHARS}〜{MAX_CHARS - 500} 文字の範囲を保つ。"
        f"ただし公式仕様が確認できず rating と spec を省いている記事は、"
        f"{MIN_CHARS_UNBACKED} 文字まで短くてよい。水増しで伸ばさない。",
        "・公式仕様（facts）も official_url も無いことは、それ自体では問題ではない。"
        "公式サイトを持たない商品もある。減点せず、rating と spec が"
        "キーごと省かれているかだけを確かめる。省かれていなければ、その2つを削る。",
        "・==この語== はこのサイトの記法で、テンプレートが蛍光ペンに変換する。"
        "装飾タグではないので消さない。1段落に1か所を超えているときだけ減らす。",
        "・HTMLは <strong> と <em> だけ。表の丸印は "
        '<span class="mark-o">◎</span> / <span class="mark-x">×</span> のみ可。',
        "・価格は書かない。変動するため。",
    ])


def apply_fixed(a, fixed, keep_updated=False, removed=None):
    """返ってきた修正を書き戻す。触らせない項目は弾く。

       fixed は上書きしかできない。「この項目はまるごと消すべき」という
       判断（裏づけの無い比較表など）は removed で受け取る。
       空の値を fixed に入れても消えないので、指摘だけが残ってしまう。"""
    changed = []
    for k in (removed or []):
        if k in GEN_FIELDS and k in a:
            a.pop(k)
            changed.append(f"{k}（削除）")
    for k, v in (fixed or {}).items():
        if k not in GEN_FIELDS:
            continue
        if v in (None, "", [], {}) or a.get(k) == v:
            continue
        a[k] = v
        changed.append(k)
    # 既存記事の手直しでは、更新日を動かさないことがある。
    # 日付が動くと sitemap と feed の並びが、中身の刷新とは別の理由で変わる。
    if changed and not keep_updated:
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
    ap.add_argument("--keep-updated", action="store_true",
                    help="更新日（updated）を元のまま動かさない。既存記事の手直し用")
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
        score, blockers = {}, []
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
            score, blockers = res.get("score") or {}, res.get("blockers") or []
            if args.dry_run:
                break

            changed = apply_fixed(a, res.get("fixed"), args.keep_updated,
                                  res.get("removed"))
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
        # 機械検査が通っても、採点と公開不可の理由が残っていれば公開しない。
        total = score.get("total") if isinstance(score, dict) else None
        if isinstance(total, (int, float)):
            low = [f"{k} {score[k]}" for k, _ in SCORE_KEYS
                   if isinstance(score.get(k), (int, float))
                   and score[k] < PUBLISH_SCORE]
            print(f"    ◇ 採点 総合 {total}"
                  + ("（低い項目：" + "、".join(low) + "）" if low else ""))
            if score.get("notes"):
                print(f"      {score['notes']}")
        for b in blockers:
            print(f"    ✗ 公開できない理由：{b}")

        under = isinstance(total, (int, float)) and total < PUBLISH_SCORE

        if hits or blockers or under:
            ng.append(slug)
            for k, p, d in hits:
                print(f"    ✗ 残った指摘 [{k}] {p}：{d}")
            if under:
                print(f"    ✗ 総合 {total} 点。{PUBLISH_SCORE} 点未満は公開しません")
        else:
            ok.append(slug)
            print("    ✓ 基準を満たしました")
            if args.publish and not args.dry_run:
                a["published"] = True
                print("    → published: true")

    if not args.dry_run and not args.check_only:
        # 丸ごと書き戻すと、実行中に別の場所が入れた変更を消す。
        # write_article.py と同じく、対象の記事だけを差し替える。
        for a in targets:
            save_article(a)
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
