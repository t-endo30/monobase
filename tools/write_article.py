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
import urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 検査の基準は管理画面・CIと揃える。ここだけ緩いと、
# 書き上げてから公開できないと分かることになる。
NG_WORDS = ["絶対", "必ず", "確実に", "保証します", "間違いなく", "100%",
            "誰でも", "永久に", "完治", "業界No.1", "日本一"]
MIN_CHARS = 6000
MAX_CHARS = 12000   # FAQ・情報源明記・比較基準まで入れると1万字前後になる。余白を持たせる

# 生成に任せる項目。slug や published、販売先URLは触らせない。
GEN_FIELDS = ["lead", "verdict_title", "summary", "rating", "good_for",
              "highlights", "not_for", "scenes", "pros", "cons", "spec", "sections",
              "voices_intro", "voices", "voices_after", "personal_note",
              "next_problem", "faq", "conclusion_title", "conclusion",
              "description", "excerpt", "list_title", "title", "tags", "sub"]

SHAPE = '''{
  "lead": ["段落", "段落"],
  "verdict_title": "結論：…",
  "summary": [{"title":"見出し","text":"本文"}],
  "rating": {"score": 4.2, "breakdown": "評価の内訳を1文で"},
  "good_for": {"intro":"", "items":[{"title":"読者像・使い方","text":"なぜ合うか"}]},
  "highlights": {"intro":"", "items":[{"title":"","text":""}]},
  "not_for": {"intro":"", "items":[{"title":"","text":""}]},
  "scenes": [{"title":"場面","text":"説明"}],
  "pros": ["良い点"], "cons": ["注意点"],
  "spec": {"intro":"", "headers":["項目","本機","比較A","比較B"],
           "rows":[["行名","値","値","値"]], "read":"表の読み方"},
  "sections": [{"heading":"見出し","paras":["段落"],
                "point":"青いポイント枠に入れる1〜2文（任意）",
                "warn":"黄色い注意枠に入れる1〜2文（任意）",
                "aside":"補足","aside_label":"レビューを読み込んで見えたこと"}],
  "voices_intro": "",
  "voices": [{"heading":"","who":"","stars":4,"text":"","negative":false,
              "fix_title":"","fix":""}],
  "voices_after": "",
  "personal_note": "",
  "next_problem": {"intro":"", "items":[{"title":"","text":""}]},
  "faq": [{"q":"購入前に迷いやすい質問","a":"仕様と口コミから導いた回答（1〜3文）"}],
  "conclusion_title": "まとめ", "conclusion": ["段落"],
  "description": "メタディスクリプション（120字以内）",
  "excerpt": "カード用の抜粋（60字以内）",
  "list_title": "一覧用の短いタイトル（22字以内・メーカー名＋商品名を含める）",
  "title": "記事タイトル（全角30字前後・末尾に「 - モノベース」は付けない）",
  "tags": ["タグ"],
  "sub": "サブカテゴリーのkey（分からなければ空文字）"
}'''


def load(path):
    return json.load(io.open(os.path.join(ROOT, path), encoding="utf-8"))


def build_prompt(a, site, prompt_md, fetch_official=True):
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
        official_block(a, do_fetch=fetch_official),
        "",
        "---------------- 出力の決まり ----------------",
        "・JSONだけを返す。前置きも、コードフェンスも付けない。",
        "・次の形に従う。項目を増やさない、減らさない。",
        SHAPE,
        f"・本文の合計は {MIN_CHARS}〜{MAX_CHARS - 500} 文字。"
        "書くことが十分にある商品では上限側（1万字前後）に寄せてよい。"
        "薄い内容を水増しして字数を稼がない。うち4割以上は"
        "表や箇条書きではなく地の文（段落）にする。",
        "・HTMLは <strong> と <em> だけ。それ以外のタグは書かない。",
        "　ただしスペック表の丸印だけは "
        '<span class="mark-o">◎</span> / <span class="mark-x">×</span> を使ってよい。',
        "・「" + "」「".join(NG_WORDS) + "」は使わない。",
        "・「〜と考えられます」「〜と言えるでしょう」「〜が期待できます」"
        "「非常に魅力的です」「バランスの取れた商品です」のような"
        "AIらしい定型のヘッジ表現を連発しない。原則「事実 → 判断」の順で簡潔に書く。",
        "・実際に使った体験として書かない（「実際に使ってみると」「手にとってみると」"
        "「〇日間使用した」は禁止）。「メーカー仕様から見ると」「購入者レビューでは」"
        "「公開情報から判断すると」「モノベースでは〜と評価します」に置き換える。",
        "・実機を確認していないので、タイトルや本文で「実機レビュー」と書かない。"
        "「口コミ・評判」「仕様・口コミレビュー」「メーカー仕様と口コミから分析」と表記する。",
        "・耐久性・防水/防塵性・内部構造・冷却性能・バッテリー性能など、メーカーが"
        "明示していない事項を事実として断定しない。触れる場合は"
        "「公開情報から判断すると〜と考えられます」と、推測であることを明記する。",
        "・口コミの件数や割合（「100件を分析した」など）を、確認できていないのに書かない。"
        "数字がなければ「購入者レビューでは」「一部の口コミでは」とする。"
        "口コミは並べるだけでなく、評価が分かれる背景・理由まで説明する。",
        "・情報の優先順位は ①メーカー公式サイト・仕様表・マニュアル（一次情報）"
        "→ ②Amazon等の販売ページ（価格・在庫の確認）→ ③購入者レビュー"
        "→ ④メディア記事・比較ブログ・SNS。一次情報と第三者情報が食い違うときは"
        "一次情報を優先し、食い違い自体も本文に明記する。",
        "・「メーカー公表の事実」「購入者の評価」「モノベースの独自判断」を"
        "読者が区別できる書き方にする。",
        "・spec（比較表）と、その read には、何を基準に比較したのか"
        "（用途・価格帯・同クラスなど）を必ず書く。",
        "・conclusion の最後の段落に、使った主要な情報源"
        "（メーカー公式サイト・販売ページなど）と「最終確認日：YYYY年MM月DD日」を書く。"
        "「価格・在庫は変動するため最新情報はリンク先でご確認ください。」も入れる。",
        "・faq は3〜6問。購入前に実際に迷う点を、仕様と口コミから答える。"
        "各回答は1〜3文。答えられない質問は載せない。",
        "・next_problem の項目にリンクURLを入れない。",
        "・価格は書かない。変動するため。",
        "",
        "---------------- タイトルの付け方（title）----------------",
        "・全角30字前後。検索結果で末尾が切れるため35字を超えない。",
        "・メーカー名（分かれば）＋商品名・型番を必ず含める。",
        "・前半に、読者が実際に検索する語を置く。"
        "「レビュー」「比較」「電気代」「静音」「口コミ」など、"
        "その商品で調べられている具体語を商品名の直後に。",
        "・「〜は買う価値があるか」「〜で何が変わるか」のような"
        "問いかけ・あおり型にしない。何の記事か一目で分かる名詞句にする。",
        "・良い例：「MX Master 3s レビュー｜静音化で変わった点と合う人」",
        "・良い例：「DCモーター扇風機の電気代と静音性｜買い替えの目安」",
        "・悪い例：「ロジクール MX MASTER 3s は静音化で何が変わったか」",
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


def fetch_text(url, limit=6000):
    """メーカー公式ページの本文テキストをざっくり抜く。
       自動取得なので、数値は「参考」。断定の根拠にはしない。"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/126.0 Safari/537.36")})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read(2_000_000)
            enc = r.headers.get_content_charset() or "utf-8"
        htmltext = raw.decode(enc, "replace")
    except (urllib.error.URLError, ValueError, TimeoutError, OSError) as ex:
        print(f"（公式ページを取得できませんでした: {ex}）", end="", flush=True)
        return ""
    htmltext = re.sub(r"(?is)<(script|style|noscript|svg|header|footer|nav)[^>]*>.*?</\1>",
                      " ", htmltext)
    text = re.sub(r"(?s)<[^>]+>", " ", htmltext)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text).strip()
    return text[:limit]


def official_block(a, do_fetch=True):
    """メーカー公式ページのURLと、（任意で）自動取得した本文。"""
    url = (a.get("official_url") or "").strip()
    if not re.match(r"https?://", url):
        return ""
    out = [f"\n【メーカー公式ページ】{url}",
           "・この製品の一次情報。仕様・スペック表は公式の公表値を優先する。",
           "・記事にはこのURLを本文へ書かない（サイト側が参照リンクとして表示する）。"]
    if do_fetch:
        body = fetch_text(url)
        if body:
            out.append("\n― 公式ページから自動抽出（参考。文字化け・古い情報を含むことがある。"
                       "数値はここだけを根拠に断定せず、facts と突き合わせる）―\n"
                       + body + "\n― 抽出ここまで ―")
    return "\n".join(out)


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
    """前置きやコードフェンスが付くことがあるので取り除いてから読む。
       生成AIは末尾カンマ（ ,} や ,] ）を付けがちなので、それも落とす。"""
    out = re.sub(r"^\s*```(?:json)?\s*", "", out)
    out = re.sub(r"\s*```\s*$", "", out)
    i, k = out.find("{"), out.rfind("}")
    if i >= 0 and k > i:
        out = out[i:k + 1]
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        # 末尾カンマだけが原因のことが多い。文字列の外側の ,}/,] を除いて再挑戦。
        fixed = re.sub(r",(\s*[}\]])", r"\1", out)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
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
    ap.add_argument("--no-fetch", action="store_true",
                    help="official_url のページを自動取得しない")
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
        prompt = build_prompt(a, site, prompt_md, fetch_official=not args.no_fetch)
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

        # 1本ごとに保存する。長時間のまとめ書き換えが途中で止まっても
        # そこまでの成果を失わないため。
        if not args.dry_run:
            with io.open(os.path.join(ROOT, "content", "articles.json"),
                         "w", encoding="utf-8") as f:
                json.dump(arts, f, ensure_ascii=False, indent=1)

    if not args.dry_run and done:
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
