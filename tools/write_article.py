#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事作成プロンプトを Claude に渡して、下書きの本文を書かせる。

Anthropic の API キー（従量課金）ではなく、**Claude Code のログイン**を使う。
`claude` コマンドはサブスクの認証をそのまま持っているので、
このツールから呼べば、追加の課金なしで書かせられる。

管理画面（ブラウザ）からは同じことができない。ブラウザから使える認証は
APIキーだけで、サブスクの認証は取り出せないため。そのため本文を
Claude で書くときは、この手元のツールを使う。

  $ python3 tools/write_article.py --drafts          # 本文が空の下書きを全部
  $ python3 tools/write_article.py mx-master-3s-review
  $ python3 tools/write_article.py --drafts --model sonnet --dry-run

書き終えたら content/articles.json を更新し、build.py を回すところまでやる。
コミットはしない（内容を読んでから、いつもの手順で公開する）。
"""
import json, io, os, re, sys, time, argparse, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 検査の基準は管理画面・CIと揃える。ここだけ緩いと、
# 書き上げてから公開できないと分かることになる。
NG_WORDS = ["絶対", "必ず", "確実に", "保証します", "間違いなく", "100%",
            "誰でも", "永久に", "完治", "業界No.1", "日本一"]
MIN_CHARS = 6000
MAX_CHARS = 8300

# 生成に任せる項目。slug や published、販売先URLは触らせない。
GEN_FIELDS = ["lead", "verdict_title", "summary", "rating", "highlights",
              "not_for", "scenes", "pros", "cons", "spec", "sections",
              "voices_intro", "voices", "voices_after", "personal_note",
              "next_problem", "conclusion_title", "conclusion",
              "description", "excerpt", "list_title", "title", "tags", "sub"]

SHAPE = '''{
  "lead": ["段落", "段落"],
  "verdict_title": "結論：…",
  "summary": [{"title":"見出し","text":"本文"}],
  "rating": {"score": 4.2, "breakdown": "評価の内訳を1文で"},
  "highlights": {"intro":"", "items":[{"title":"","text":""}]},
  "not_for": {"intro":"", "items":[{"title":"","text":""}]},
  "scenes": [{"title":"場面","text":"説明"}],
  "pros": ["良い点"], "cons": ["注意点"],
  "spec": {"intro":"", "headers":["項目","本機","比較A","比較B"],
           "rows":[["行名","値","値","値"]], "read":"表の読み方"},
  "sections": [{"heading":"見出し","paras":["段落"],
                "aside":"補足","aside_label":"レビューを読み込んで見えたこと"}],
  "voices_intro": "",
  "voices": [{"heading":"","who":"","stars":4,"text":"","negative":false,
              "fix_title":"","fix":""}],
  "voices_after": "",
  "personal_note": "",
  "next_problem": {"intro":"", "items":[{"title":"","text":""}]},
  "conclusion_title": "まとめ", "conclusion": ["段落"],
  "description": "メタディスクリプション（120字以内）",
  "excerpt": "カード用の抜粋（60字以内）",
  "list_title": "一覧用の短いタイトル（30字以内）",
  "title": "記事タイトル",
  "tags": ["タグ"],
  "sub": "サブカテゴリーのkey（分からなければ空文字）"
}'''


def load(path):
    return json.load(io.open(os.path.join(ROOT, path), encoding="utf-8"))


def build_prompt(a, site, prompt_md):
    cat = next((c for c in site.get("categories", [])
                if c.get("key") == a.get("category")), {})
    subs = "、".join(f'{x["key"]}（{x["label"]}）'
                    for x in cat.get("sub", [])) or "なし"
    shops = []
    if a.get("asin") or a.get("amazon_url"):
        shops.append("Amazon")
    if a.get("rakuten_url"):
        shops.append("楽天市場")
    if a.get("yahoo_url"):
        shops.append("Yahoo!ショッピング")

    return "\n".join([
        prompt_md,
        "",
        "---------------- ここから今回の商品 ----------------",
        f'商品名：{a.get("title", "")}',
        f'カテゴリー：{cat.get("label") or a.get("category")}',
        f"選べるサブカテゴリーのkey：{subs}",
        f'JANコード：{a.get("jan") or "不明"}',
        f'買えるモール：{"、".join(shops) or "不明"}',
        facts_block(a),
        "",
        "---------------- 出力の決まり ----------------",
        "・JSONだけを返す。前置きも、コードフェンスも付けない。",
        "・次の形に従う。項目を増やさない、減らさない。",
        SHAPE,
        f"・本文の合計は {MIN_CHARS}〜{MAX_CHARS - 300} 文字。",
        "・HTMLは <strong> と <em> だけ。それ以外のタグは書かない。",
        "　ただしスペック表の丸印だけは "
        '<span class="mark-o">◎</span> / <span class="mark-x">×</span> を使ってよい。',
        "・「" + "」「".join(NG_WORDS) + "」は使わない。",
        "・実際に使った体験として書かない。レビューと仕様から読み取れることだけを書く。",
        "・next_problem の項目にリンクURLを入れない。",
        "・価格は書かない。変動するため。",
    ])


def facts_block(a):
    """メーカー公式で裏を取った仕様を渡す。
       ここを渡さないと、無い機能を「ある」と書いてしまう。
       実際、温度調節のない電気ケトルに温度調節の節が付いた。"""
    facts = a.get("facts") or []
    if isinstance(facts, str):
        facts = [facts]
    if not facts:
        return ("\n【仕様について】確かな仕様が渡されていません。"
                "数値や機能の有無を断定せず、レビューから読み取れる範囲で書いてください。")
    return ("\n【メーカー公式で確認済みの仕様】\n"
            + "\n".join(f"・{f}" for f in facts)
            + "\nここに無い機能を「ある」と書かないでください。"
            "スペック表もこの範囲で作ります。")


SYSTEM = ("あなたは日本語の商品レビュー記事を書くライターです。"
          "返事はJSONオブジェクトそのものだけにしてください。"
          "前置き・あとがき・説明・コードフェンスは一切付けません。"
          "最初の文字は { で、最後の文字は } です。")


def run_claude(prompt, model, timeout):
    """`claude -p` に渡して、返ってきたJSONを読む。
       プロンプトが長いので、引数ではなく標準入力から渡す。"""
    cmd = ["claude", "-p", "--output-format", "json", "--model", model,
           "--append-system-prompt", SYSTEM]
    try:
        p = subprocess.run(cmd, input=prompt, capture_output=True,
                           text=True, timeout=timeout)
    except FileNotFoundError:
        raise RuntimeError(
            "claude コマンドが見つかりません。Claude Code をインストールして、"
            "`claude` でログインしてください。")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"{timeout} 秒で応答がありませんでした")

    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "").strip()[:400])

    try:
        env = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise RuntimeError("claude の応答を読み取れませんでした：" + p.stdout[:200])

    if env.get("is_error"):
        raise RuntimeError(str(env.get("result"))[:400])
    return env.get("result", ""), env.get("total_cost_usd") or 0


def parse_json(out):
    """前置きやコードフェンスが付くことがあるので取り除いてから読む。"""
    out = re.sub(r"^\s*```(?:json)?\s*", "", out)
    out = re.sub(r"\s*```\s*$", "", out)
    i, k = out.find("{"), out.rfind("}")
    if i >= 0 and k > i:
        out = out[i:k + 1]
    try:
        return json.loads(out)
    except json.JSONDecodeError as ex:
        # 何が返ってきたのか分からないままだと直せない。中身を残す。
        path = os.path.join(ROOT, "content", "_last_generation.txt")
        try:
            io.open(path, "w", encoding="utf-8").write(out)
        except OSError:
            path = "(保存できず)"
        head = out[:160].replace("\n", " ")
        raise RuntimeError(
            f"JSONとして読めませんでした（{len(out):,}字）: {ex}\n"
            f"    応答の先頭：{head}\n"
            f"    全文：{path}")


def body_chars(v):
    if isinstance(v, str):
        return len(re.sub(r"<[^>]+>", "", v))
    if isinstance(v, list):
        return sum(body_chars(x) for x in v)
    if isinstance(v, dict):
        return sum(body_chars(x) for x in v.values())
    return 0


def audit(a):
    """管理画面と同じ検査。書き上げてから公開できないと分かるのを防ぐ。"""
    warns = []
    blob = json.dumps(a, ensure_ascii=False)
    for w in NG_WORDS:
        if w in blob:
            warns.append(f"禁止表現「{w}」")
    for t in re.findall(r"</?[a-z]+[^>]*>", blob, re.I):
        if re.match(r"</?(strong|em)\b", t, re.I):
            continue
        if re.match(r'<span class=\\?"mark-[ox]\\?">$|</span>$', t, re.I):
            continue
        warns.append(f"使えないタグ {t}")
    n = body_chars({k: a[k] for k in GEN_FIELDS if k in a})
    if n < MIN_CHARS:
        warns.append(f"本文が {n:,} 字（下限 {MIN_CHARS:,}）")
    if n > MAX_CHARS:
        warns.append(f"本文が {n:,} 字（上限 {MAX_CHARS:,}）")
    # 同じ指摘は1回だけ
    return list(dict.fromkeys(warns))


def apply_generated(a, gen):
    for k in GEN_FIELDS:
        v = gen.get(k)
        if v not in (None, "", [], {}):
            a[k] = v
    # リンク切れ検査で止まるので、作り話のリンクは落とす
    for it in (a.get("next_problem") or {}).get("items", []):
        it.pop("link_url", None)
        it.pop("link_label", None)
    a["updated"] = time.strftime("%Y-%m-%d")
    return a


def is_empty(a):
    """本文がまだ入っていない下書きか。"""
    n = sum(len(a.get(k) or []) for k in ("summary", "pros", "cons",
                                          "scenes", "sections", "voices"))
    return n == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*", help="対象の記事slug")
    ap.add_argument("--drafts", action="store_true",
                    help="本文が空の下書きをすべて対象にする")
    ap.add_argument("--model", default="opus",
                    help="opus / sonnet（既定は opus。今ある記事と同じ）")
    ap.add_argument("--timeout", type=int, default=900,
                    help="1本あたりの待ち時間（秒）")
    ap.add_argument("--dry-run", action="store_true",
                    help="書き込まず、結果だけ表示する")
    args = ap.parse_args()

    arts = load("content/articles.json")
    site = load("content/site.json")
    prompt_md = io.open(os.path.join(ROOT, "docs", "article-prompt.md"),
                        encoding="utf-8").read()

    if args.drafts:
        targets = [a for a in arts if not a.get("published") and is_empty(a)]
    else:
        want = set(args.slugs)
        targets = [a for a in arts if a.get("slug") in want]
        missing = want - {a.get("slug") for a in targets}
        for m in missing:
            print(f"::warning::{m} という記事がありません", file=sys.stderr)

    if not targets:
        print("対象の記事がありません。--drafts を付けるか、slugを指定してください。")
        return 0

    print(f"{len(targets)} 本を {args.model} で書きます"
          f"（Claude Code のログインを使用。1本あたり数分かかります）\n")

    cost = 0.0
    done, failed = 0, 0
    for i, a in enumerate(targets, 1):
        slug = a.get("slug", "?")
        print(f"[{i}/{len(targets)}] {slug} … ", end="", flush=True)
        t0 = time.time()
        prompt = build_prompt(a, site, prompt_md)
        gen = None
        for attempt in (1, 2):
            try:
                out, c = run_claude(prompt, args.model, args.timeout)
                cost += c
                gen = parse_json(out)
                break
            except RuntimeError as ex:
                # 文章で返してくることがある。1度だけ言い直して頼む。
                if attempt == 1 and "JSONとして読めません" in str(ex):
                    print("形が違ったのでやり直し … ", end="", flush=True)
                    prompt = (prompt + "\n\n【重要】前回はJSON以外が返ってきました。"
                              "説明や前置きを書かず、JSONオブジェクトだけを返してください。")
                    continue
                print(f"失敗\n    {ex}")
                failed += 1
                break
        if gen is None:
            continue

        if args.dry_run:
            tmp = dict(a)
            apply_generated(tmp, gen)
            warns = audit(tmp)
        else:
            apply_generated(a, gen)
            warns = audit(a)

        done += 1
        print(f"完了（{time.time() - t0:.0f}秒 / {body_chars(gen):,}字）")
        for w in warns:
            print(f"    △ {w}")

    if not args.dry_run and done:
        with io.open(os.path.join(ROOT, "content", "articles.json"),
                     "w", encoding="utf-8") as f:
            json.dump(arts, f, ensure_ascii=False, indent=1)
        print("\ncontent/articles.json を更新しました。")

    print(f"\n完了 {done} 本 / 失敗 {failed} 本 / 参考コスト ${cost:.2f}")
    if not args.dry_run and done:
        print("次にやること：")
        print("  1. 内容を読む（スペック表の数値はメーカー公式で裏を取る）")
        print("  2. python3 build.py && python3 tools/check_articles.py")
        print("  3. 問題なければコミットして push")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
