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
# 公式仕様も official_url も無い記事は、rating と spec をキーごと省くぶん短くなる。
# それは正しい振る舞いなので、下限を下げて水増しを促さない。
MIN_CHARS_UNBACKED = 5000
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
  "sub": "サブカテゴリーのkey（分からなければ空文字）",
  "data_gaps": ["確認できなかったこと。無ければ空配列"],
  "self_check": {"fact_accuracy": 0, "source_reliability": 0,
                 "original_analysis": 0, "editorial_quality": 0,
                 "template_avoidance": 0, "purchase_helpfulness": 0,
                 "legal_safety": 0, "amazon_compliance": 0,
                 "total": 0, "notes": "低い項目の理由を1〜2文"}
}'''


ARTICLES = "content/articles.json"


def load(path):
    return json.load(io.open(os.path.join(ROOT, path), encoding="utf-8"))


def save_article(a):
    """書き上げた1本だけを articles.json へ書き戻す。

       起動時に読んだ配列をそのまま書き戻すと、実行中に別の場所
       （管理画面・手作業・別のツール）が同じファイルへ入れた変更を
       消してしまう。実際、生成中に足した official_url と facts が
       生成の完了時に消えた。だから保存のたびに読み直し、
       対象の記事だけを差し替える。"""
    path = os.path.join(ROOT, ARTICLES)
    latest = json.load(io.open(path, encoding="utf-8"))
    slug = a.get("slug")
    for i, x in enumerate(latest):
        if x.get("slug") == slug:
            latest[i] = a
            break
    else:
        latest.append(a)
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(latest, f, ensure_ascii=False, indent=1)


# 記事タイプごとに「使ってよい枠」。docs/article-prompt.md の【1.】と同じ内容を、
# その記事ぶんだけ抜き出して渡す。全部の型を毎回読ませるより取り違えが減る。
KIND_FRAMES = {
    "review": ("単一商品レビュー",
               "summary / rating / good_for / not_for / highlights / pros / cons / "
               "spec / sections / voices / faq / conclusion",
               "scenes は「想定される利用場面」として書ける場合だけ。書けないなら出さない。"),
    "roundup": ("商品比較・ランキング特集",
                "summary / good_for / not_for / spec / sections / faq / conclusion",
                "highlights・scenes は使わない（単一商品レビュー用の枠のため）。"),
    "guide": ("商品の選び方・商品解説",
              "summary / good_for / not_for / spec / sections / faq / conclusion",
              "rating・highlights・scenes・voices は使わない。"),
    "sale": ("セール情報",
             "summary / sections / faq / conclusion",
             "rating・highlights・scenes・good_for・not_for・voices・pros/cons は使わない。"
             "中身は「開催時期／セールの特徴／狙い目のカテゴリー／値下げされやすい商品の傾向／"
             "買うタイミング／注意点／価格を見るときの見方」にする。"
             "商品レビュー用の見出しを持ち込まない。"),
    "howto": ("ハウツー",
              "summary / sections / faq / conclusion",
              "rating・highlights・scenes・voices は使わない。"),
}

# 美容・ヘルスケアは表現の risk が別格なので、そのカテゴリーのときだけ追加で渡す。
CARE_NOTE = {
    "beauty": (
        "・この記事は美容・コスメです。効果の断定を書かない"
        "（シミを改善する／ニキビを治す／肌を再生する／肌の内部まで浸透する／"
        "毛穴が消える／シワが改善する／老化を防ぐ／メイク崩れを防ぐ）。"
        "使用感・テクスチャ・香り・保湿感・べたつき・成分表示・使用方法を中心にする。"
        "メーカーの説明は「メーカーは〇〇を特徴として説明しています」と出どころを明示する。"),
    "health": (
        "・この記事はヘルスケアです。「病気を診断できる」「治療できる」「予防できる」"
        "と書かない。測定値は「健康管理の参考値」として扱い、"
        "医療行為・診断と誤認される書き方をしない。"),
}


def kind_of(a):
    """記事の種類。build.py の kind_of と同じ判定にそろえる。"""
    k = a.get("kind")
    if k in KIND_FRAMES:
        return k
    return "roundup" if a.get("category") == "feature" else "review"


def kind_block(a):
    kind = kind_of(a)
    label, frames, note = KIND_FRAMES[kind]
    out = ["\n【この記事の種類】" + f"{kind}（{label}）",
           "・使ってよい枠：" + frames,
           "・" + note,
           "・ここに挙がっていないキーは出力しない。空で出すと空の見出しができる。",
           "・挙がっている枠でも、書くことが無ければ出さない。枠を埋めるために"
           "内容を作らない（テンプレートの量産になる）。"]
    care = CARE_NOTE.get(a.get("category"))
    if care:
        out.append(care)
    return "\n".join(out)


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
        kind_block(a),
        facts_block(a),
        official_block(a, do_fetch=fetch_official),
        "",
        "---------------- 出力の決まり ----------------",
        "・JSONだけを返す。前置きも、コードフェンスも付けない。",
        "・次の形に従う。項目を増やさない、減らさない。",
        SHAPE,
        f"・本文の合計は {MIN_CHARS}〜{MAX_CHARS - 500} 文字。"
        f"ただし公式仕様が確認できず rating と spec を省いた記事は、"
        f"{MIN_CHARS_UNBACKED} 文字まで短くてよい。"
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
        "・比較対象は実在する商品にする。「一般的な商品」「同クラス製品」"
        "「平均的なモデル」のような実在しない相手と比べない。"
        "実在の比較対象を挙げられないなら spec を出さない。"
        "比較表が無い記事は、それで完成。埋めるために架空の比較対象を作らない。",
        "・rating は、商品ジャンルに合う評価軸で採点し、何を評価し何を減点したかを"
        "breakdown に書く。公式仕様を確認できていない商品では rating を出さない"
        "（0.1刻みの数字だけが独り歩きするため）。"
        "rating が無い記事は、それで完成。無理に点数をひねり出さない。",
        "・pros / cons は商品固有の内容にする。「高性能」「使いやすい」「高い」"
        "のような、どの商品にも書ける言葉を書かない。"
        "「仕様・事実 → 読者への影響」まで書く。",
        "・good_for / not_for は、どんな人・用途・環境・予算・重視点かまで書く。"
        "おすすめしない側は理由も書く。",
        "・scenes は「実際の生活シーン」として書かない。架空の人物・体験談を作らない。"
        "「想定される利用場面」「この環境でメリットが出やすい」として書く。",
        "・口コミは、何が評価されているかだけでなく、"
        "なぜ評価が分かれるのかを仕様と結びつけて書く。"
        "口コミを取得できていないなら voices ごと出さない。",
        "・各記事に最低1つ、このサイトだから書ける分析を入れる"
        "（口コミと公式仕様の食い違い／評価が分かれる理由／"
        "スペックから分かる用途上の制約／購入前に見落としやすい点）。"
        "ただし独自性を作るために事実を作らない。",
        "・Amazon公式・Amazonの推薦や提携だと誤認させる書き方をしない。"
        "アソシエイトの開示文はサイト側が全ページに出しているので本文に重ねて書かない。",
        "・確認できないことは data_gaps に列挙する。本文で推測で埋めない。"
        "書けない枠はキーごと省く。",
        "・書き終えたら self_check を自分で採点する。甘く付けない。",
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
        "",
        # 長いプロンプトでは、途中の禁止事項ほど守られなくなる。
        # 実際、統合後の試し書きで「必ず」「絶対」「使ってみた」が混入した。
        # いちばん後ろにもう一度置いて、書き終える直前に読ませる。
        "---------------- 書き出す前に、もう一度確認する ----------------",
        "次の3つは、ほかのどの指示よりも優先して守る。",
        "1. 「" + "」「".join(NG_WORDS) + "」を、どの項目にも1回も書かない。"
        "　「必ず確認してください」も不可。「事前に確認してください」と書く。",
        "2. 実機を使ったと読める書き方をしない。"
        "「使ってみた」「使ってみると」「実際に感じた」「実測した（自分が測った意味で）」"
        "「装着してみた」「開封した」は書かない。"
        "　読者への助言としての「購入前に実測してください」は書いてよい。",
        "3. 実在しない比較対象（「一般的な製品」「同クラス製品」「平均的なモデル」）"
        "と比べない。実在の商品名を挙げられないなら、比較そのものを書かない。",
        "書き終えたら、この3点で出力を読み返してから返すこと。",
    ])


def facts_block(a):
    """メーカー公式で裏を取った仕様を渡す。
       ここを渡さないと、無い機能を「ある」と書いてしまう。
       実際、温度調節のない電気ケトルに温度調節の節が付いた。

       公式仕様が無いこと自体は異常ではない。公式サイトを持たない商品もあるし、
       管理画面から手で入れる運用も取らない。だから「書けない」ではなく
       「rating と spec を省いて書く」を正しい動きとして指示する。"""
    facts = a.get("facts") or []
    if isinstance(facts, str):
        facts = [facts]
    if not facts:
        return ("\n【仕様について】メーカー公式で裏を取った仕様は渡されていません。"
                "これは異常ではなく、通常の状態です。次のとおりに書いてください。\n"
                "・rating を出さない（キーごと省く）\n"
                "・spec（比較表）を出さない（キーごと省く）\n"
                "・数値・機能の有無を断定しない\n"
                "・そのうえで、記事は書き上げる\n"
                "公式仕様が無くても書けることを書きます。購入者レビューから読み取れる傾向と"
                "評価が分かれる理由、購入前に確認しておくべきこと、向く用途と向かない用途、"
                "販売ページで自分の目で確かめるべき項目（サイズ・付属品・保証・対応機種など）。"
                "読者には「仕様は販売ページで確認してください」と促します。\n"
                "公式仕様が無いことを self_check の減点理由にしないでください。"
                "確認できないものを省き、data_gaps に挙げ、書けることを書けていれば、"
                "source_reliability は下げなくて構いません。"
                "逆に、確認できていないのに rating や spec を出したら大きく減点します。")
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


# 実機を使ったと読める言い回し。読者への助言（「購入前に実測してください」）とは
# 区別したいので、書き手が自分で確かめたと読める形だけを集める。
FAKE_EXPERIENCE = re.compile(
    r"実際に使って(?:み|感じ|分かっ|わかっ)|使ってみ(?:た|ると|たら)|"
    r"(?:私|筆者|編集部)(?:が|は)[^。]{0,8}?(?:使っ|試し|触っ|装着し|測っ)|"
    r"使用して(?:分かっ|わかっ|感じ)|実際に感じ(?:た|られ)|"
    r"実測(?:した|して[みま]|の結果)|撮影して確認|装着してみ|"
    r"手に?とってみ|試してみたところ|開封(?:した|してみ)|実機レビュー")

# 確認できない口コミの件数・割合・平均星
FAKE_REVIEW_NUM = re.compile(
    r"\d+\s*件(?:の|を)?(?:レビュー|口コミ|評価)|"
    r"(?:レビュー|口コミ|評価)(?:を)?\s*\d+\s*件|"
    r"\d+\s*人(?:の|が)(?:購入者|レビュー|口コミ)|"
    r"(?:平均|口コミ|レビュー)(?:評価|星)[^。]{0,6}?\d\.\d|星\s*\d\.\d")

# Amazon との関係を誤認させる書き方
AMAZON_MISLEAD = re.compile(
    r"Amazon(?:の)?公式(?:サイト|ストア|見解|推奨)|Amazonが(?:推薦|認定|保証|おすすめ)|"
    r"Amazon(?:から)?(?:認定|推薦|公認)|Amazonと(?:の)?(?:提携|パートナー)")

# 実在しない比較対象
VAGUE_RIVAL = re.compile(
    r"一般的な(?:商品|製品|モデル|美容液|クリーム|タイプ|もの)|"
    r"同クラス(?:の)?(?:製品|商品)|平均的な(?:商品|製品|モデル)|"
    r"標準的な(?:商品|製品|モデル)|"
    # 比較表の見出しに出る「〜タイプ（一般）」「〜（一般的なもの）」
    r"[（(]一般(?:的)?[）)]|一般タイプ|他社(?:の)?一般")

# 薬機法のリスクになる断定（美容・ヘルスケア）
CARE_CLAIM = re.compile(
    r"シミが(?:消え|なくな)|シワが(?:消え|なくな|改善)|毛穴が(?:消え|なくな)|"
    r"ニキビが治|肌が再生|老化を防|アンチエイジング効果|"
    r"肌の(?:内側|奥|内部)(?:まで|から)(?:浸透|届|作用)|"
    r"病気を(?:治|予防|発見)|診断でき|美白|痩せ(?:る|られ|ます)")

# AI が量産する定型のヘッジ表現。1〜2回は自然な範囲なので回数で見る。
AI_PHRASE = re.compile(
    r"と言えるでしょう|と言えます|と考えられます|が期待できます|"
    r"最大の魅力(?:です|は)|総合的に判断すると|非常に(?:優れ|魅力的|便利)|"
    r"大きな(?:ポイント|メリット)です|バランスの取れた|ということが分かります")
AI_PHRASE_LIMIT = 6      # 1万字の記事での上限。これを超えたら書き直させる

# 打ち消し・仮定・疑問の文脈は拾わない
NEGATION = re.compile(
    r"[^。]{0,30}?(?:ませ[んぬ]|ないでください|わけでは|とは限|ような|"
    r"か[？?]|かどうか|ものではあり|と(?:は)?書き)|"
    # 出どころを明示した数値は断定ではない（「〜とメーカーが公表」など）
    r"[^。]{0,40}?(?:と(?:メーカーが)?公表|(?:という|の)?公表値|と(?:メーカーは)?説明|"
    r"と表示され)")


def _find(pat, text):
    """打ち消し文脈をのぞいた一致だけを返す。"""
    out = []
    for m in pat.finditer(text):
        if NEGATION.match(text[m.end():m.end() + 40]):
            continue
        out.append(m.group(0))
    return out


def audit(a):
    """管理画面と同じ検査。書き上げてから公開できないと分かるのを防ぐ。"""
    warns = []
    blob = json.dumps(a, ensure_ascii=False)
    # 読者が読む文だけを、タグを外して1本につなぐ
    body = {k: v for k, v in a.items() if k in GEN_FIELDS}
    text = re.sub(r"<[^>]+>", "", json.dumps(body, ensure_ascii=False))

    for label, pat in (("実体験の捏造", FAKE_EXPERIENCE),
                       ("確認できない口コミ数値", FAKE_REVIEW_NUM),
                       ("Amazonとの関係の誤認", AMAZON_MISLEAD),
                       ("実在しない比較対象", VAGUE_RIVAL)):
        for w in dict.fromkeys(_find(pat, text)):
            warns.append(f"{label}「{w}」")

    if a.get("category") in ("beauty", "health"):
        for w in dict.fromkeys(_find(CARE_CLAIM, text)):
            warns.append(f"効果の断定（薬機法）「{w}」")

    n_ai = len(_find(AI_PHRASE, text))
    if n_ai > AI_PHRASE_LIMIT:
        warns.append(f"AIらしい定型表現が {n_ai} 回（上限 {AI_PHRASE_LIMIT}）")

    # 裏づけが無いのに rating / spec を出していないか。
    # 公式情報が無いこと自体は問題ではない。無いのに数字を出すのが問題。
    facts = a.get("facts") or []
    if isinstance(facts, str):
        facts = [facts]
    backed = bool(facts) or bool((a.get("official_url") or "").strip())
    if not backed:
        if (a.get("rating") or {}).get("score"):
            warns.append("公式仕様の裏づけが無いのに rating がある"
                         "（キーごと省くのが正しい）")
        if (a.get("spec") or {}).get("rows"):
            warns.append("公式仕様の裏づけが無いのに spec がある"
                         "（キーごと省くのが正しい）")

    # 記事タイプに合わない枠を使っていないか
    kind = kind_of(a)
    allowed = {x.strip() for x in KIND_FRAMES[kind][1].replace("/", " ").split()}
    for key in ("rating", "highlights", "scenes", "voices", "good_for", "not_for"):
        v = a.get(key)
        has = bool(v.get("items")) if isinstance(v, dict) else bool(v)
        if has and key not in allowed and not (kind == "review" and key == "scenes"):
            warns.append(f"{kind} 記事に {key} が入っている（この型では使わない枠）")

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
    # rating・spec を省いたぶん短くなるのは正しい振る舞い。
    # 水増しを促さないよう、裏づけの無い記事では下限を下げる。
    floor = MIN_CHARS if backed else MIN_CHARS_UNBACKED
    if n < floor:
        warns.append(f"本文が {n:,} 字（下限 {floor:,}）"
                     "。水増しで埋めない。書けることが尽きているなら短いままでよい")
    if n > MAX_CHARS:
        warns.append(f"本文が {n:,} 字（上限 {MAX_CHARS:,}）")
    # 同じ指摘は1回だけ
    return list(dict.fromkeys(warns))


def apply_generated(a, gen, keep_updated=False):
    before = a.get("updated")
    for k in GEN_FIELDS:
        v = gen.get(k)
        if v not in (None, "", [], {}):
            a[k] = v

    # 書き直しでは、上書きだけでは足りない。
    # 生成AIが rating と spec を「根拠が無いので出さない」と判断して省いても、
    # 上書きしかしないと前の版の値が残り、根拠のない点数と比較表が生き続ける。
    # 実際、書き直した記事に「（一般）」を比較対象にした古い表が残っていた。
    # 省かれた＝出さないという判断なので、こちらでも落とす。
    for k in ("rating", "spec"):
        if gen.get(k) in (None, "", [], {}) and k in a:
            a.pop(k)

    # 公式仕様の裏づけが無いなら、生成AIが出していても落とす。
    facts = a.get("facts") or []
    if isinstance(facts, str):
        facts = [facts]
    if not (facts or (a.get("official_url") or "").strip()):
        for k in ("rating", "spec"):
            a.pop(k, None)

    # 記事タイプで使わない枠も、前の版の値が残ることがある。
    # 選び方の記事に「この商品の強み」「生活シーン」が残っていた。
    # 生成AIが正しく省いても、上書きしかしないと消えないため落とす。
    allowed = {x.strip() for x in KIND_FRAMES[kind_of(a)][1].replace("/", " ").split()}
    for k in ("rating", "highlights", "scenes", "voices", "good_for", "not_for",
              "spec", "pros", "cons"):
        if k in allowed or (kind_of(a) == "review" and k == "scenes"):
            continue
        a.pop(k, None)
        # 枠に付く前後の地の文も、見出しごと消えるので一緒に落とす
        for extra in (f"{k}_intro", f"{k}_after", f"{k}_note"):
            a.pop(extra, None)

    # リンク切れ検査で止まるので、作り話のリンクは落とす
    for it in (a.get("next_problem") or {}).get("items", []):
        it.pop("link_url", None)
        it.pop("link_label", None)
    if keep_updated:
        # 既存記事の書き直しでは、更新日を動かさないことがある。
        # 日付が動くと sitemap と feed の並びが変わり、
        # 中身の刷新とは別の理由で全記事が「更新された」ように見えるため。
        if before is None:
            a.pop("updated", None)
        else:
            a["updated"] = before
    else:
        a["updated"] = time.strftime("%Y-%m-%d")
    return a


# 自己採点の8項目。docs/article-prompt.md の【自己申告】と同じ並び。
SELF_CHECK_KEYS = [
    ("fact_accuracy", "事実の正確性"),
    ("source_reliability", "情報源の信頼性"),
    ("original_analysis", "独自分析"),
    ("editorial_quality", "編集品質"),
    ("template_avoidance", "テンプレート量産感の少なさ"),
    ("purchase_helpfulness", "購入判断への有用性"),
    ("legal_safety", "法令・表現上の安全性"),
    ("amazon_compliance", "Amazon関連ルールへの配慮"),
]
PUBLISH_SCORE = 85      # 総合これ未満は公開しない（人が読んで直す）


def report_self_check(gen):
    """生成AIの自己申告を表示する。articles.json には保存しない
       （記事の中身ではなく、編集部が読むための申し送りのため）。"""
    gaps = gen.get("data_gaps") or []
    if isinstance(gaps, str):
        gaps = [gaps]
    for g in gaps:
        print(f"    ? 確認できていない：{g}")

    sc = gen.get("self_check") or {}
    if not sc:
        print("    △ self_check が返っていません（自己採点なし）")
        return
    low = [f"{ja} {sc.get(k)}" for k, ja in SELF_CHECK_KEYS
           if isinstance(sc.get(k), (int, float)) and sc[k] < PUBLISH_SCORE]
    total = sc.get("total")
    mark = "✓" if isinstance(total, (int, float)) and total >= PUBLISH_SCORE else "△"
    print(f"    {mark} 自己採点 総合 {total}"
          + (f"（{PUBLISH_SCORE}点未満は公開しない）" if mark == "△" else ""))
    if low:
        print("      低い項目：" + "、".join(low))
    if sc.get("notes"):
        print(f"      {sc['notes']}")


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
    ap.add_argument("--keep-updated", action="store_true",
                    help="更新日（updated）を元のまま動かさない。既存記事の書き直し用")
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
        # 直前に読み直す。前の1本を書いている間に足された
        # official_url や facts を、取りこぼさずプロンプトへ渡すため。
        fresh = next((x for x in load(ARTICLES) if x.get("slug") == slug), None)
        if fresh is not None:
            a.clear()
            a.update(fresh)
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
            apply_generated(tmp, gen, keep_updated=args.keep_updated)
            warns = audit(tmp)
        else:
            apply_generated(a, gen, keep_updated=args.keep_updated)
            warns = audit(a)

        done += 1
        print(f"完了（{time.time() - t0:.0f}秒 / {body_chars(gen):,}字）")
        report_self_check(gen)
        for w in warns:
            print(f"    △ {w}")

        # 1本ごとに保存する。長時間のまとめ書き換えが途中で止まっても
        # そこまでの成果を失わないため。
        if not args.dry_run:
            save_article(a)

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
