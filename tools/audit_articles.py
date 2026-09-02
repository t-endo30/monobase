#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""既存記事の品質を点検する（読むだけ。書き換えない）。

`tools/review_article.py` は「これから公開する記事」を直すための道具で、
Claude を呼んで本文を書き換える。こちらは **すでに公開している記事** を
まとめて見渡し、どこに危ないところが残っているかを一覧にするだけの道具。

  $ python3 tools/audit_articles.py                # 公開中の記事すべて
  $ python3 tools/audit_articles.py --all          # 下書きも含める
  $ python3 tools/audit_articles.py --slug mx-master-3s-review
  $ python3 tools/audit_articles.py --min high     # HIGH 以上だけ表示
  $ python3 tools/audit_articles.py --json out.json

**この道具は articles.json を一切書き換えない。**
記事の削除・URL変更・リンク削除も行わない。直すかどうかは人が決める。

深刻度は4段階。

  CRITICAL … 誤情報・架空情報・架空レビュー・架空体験・重大な表現リスク
  HIGH     … 公式仕様不足・AIテンプレート感・独自性不足・Amazon開示不足・美容/健康表現
  MEDIUM   … 内部リンク・比較・FAQ・SEO
  LOW      … 軽微な文章表現・重複・文体
"""
import argparse, io, json, os, re, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LEVELS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

# 読者が読む文ではないキー。検査の対象から外す。
SKIP_KEYS = {"slug", "thumb", "banner", "amazon_url", "asin", "jan", "date",
             "updated", "rakuten_url", "yahoo_url", "cta_position", "official_url",
             "icon", "category", "sub", "tags", "cta_label", "image_prompt",
             "feature_of", "feature_covers", "health", "facts", "kind",
             "published", "featured"}


# ---------------------------------------------------------------- 検出ルール
# (深刻度, 分類, 正規表現, 説明, 対象カテゴリー)
# 対象カテゴリーが None なら全記事。集合を書くとそのカテゴリーだけを見る。
#
# 「見つけたら必ず直す」ものを CRITICAL に置く。
# 文脈しだいのものは HIGH 以下にして、人が読んで判断できるようにする。

RULES = [
    # ---- CRITICAL：架空の体験 -------------------------------------------
    ("CRITICAL", "架空体験",
     # 「実測」「実際に使う」だけでは拾わない。読者への助言として正しく使う語なので、
     # **書き手が自分で確かめた** と読める形だけを集める。
     r"実際に使って(?:み|感じ|分かっ|わかっ)|使ってみ(?:た|ると|たら)|"
     r"(?:私|筆者|編集部)(?:が|は)[^。]{0,8}?(?:使っ|試し|触っ|装着し|測っ)|"
     r"使用して(?:分かっ|わかっ|感じ)|実際に感じ(?:た|られ)|"
     r"実際に\d+\s*[日週か月ヶヵ][^。]{0,6}?使(?:っ|用)|"
     r"実測(?:した|して[みま]|の結果|してみ)|計測してみ|撮影して確認|"
     r"装着してみ|手に?とってみ|手に取ってみ|触ってみたところ|"
     r"試してみたところ|開封(?:した|してみ)",
     "実機を使っていないのに、使用体験として書いている", None),

    # ---- CRITICAL：架空の口コミ・評価数値 --------------------------------
    ("CRITICAL", "架空口コミ数値",
     r"\d+\s*件(?:の|を)?(?:レビュー|口コミ|評価)|"
     r"(?:レビュー|口コミ|評価)(?:を)?\s*\d+\s*件|"
     r"\d+\s*人(?:の|が)(?:購入者|レビュー|口コミ|使って|評価)|"
     r"レビューの\s*\d+\s*[%％割]|口コミの\s*\d+\s*[%％割]",
     "確認できない口コミ件数・割合を数字で書いている", None),

    ("CRITICAL", "架空の星評価",
     r"(?:平均|口コミ|レビュー|Amazon(?:の)?)(?:評価|星)[^。]{0,6}?\d\.\d|"
     r"星\s*\d\.\d|\d\.\d\s*/\s*5(?:\.0)?\s*(?:の評価|の星|でした)",
     "販売ページの平均評価を、確認できないまま数値で書いている", None),

    # ---- CRITICAL：Amazon との関係の誤認 ---------------------------------
    ("CRITICAL", "Amazon誤認",
     r"Amazon(?:の)?公式(?:サイト|ストア|見解|推奨)|Amazonが(?:推薦|認定|保証|おすすめ)|"
     r"Amazon(?:から)?(?:認定|推薦|公認)|Amazonと(?:の)?(?:提携|パートナー)",
     "Amazon公式・Amazonの推薦であるかのように読める", None),

    # ---- CRITICAL：医薬品的な効能の断定（美容・ヘルスケア） --------------
    ("CRITICAL", "医療的断定",
     r"完治|治ります|treatment|治療でき|病気を(?:治|防|予防)|"
     r"シミが(?:消え|なくな)|シワが(?:消え|なくな)|毛穴が(?:消え|なくな)|"
     r"ニキビが治|肌が再生|老化を防|アンチエイジング効果|"
     r"肌の(?:内側|奥|内部)(?:まで|から)(?:浸透|届|作用)|"
     r"診断でき|病気を発見",
     "医薬品的な効能を断定している（薬機法のリスク）", None),

    ("CRITICAL", "断定・保証",
     r"絶対|必ず|確実に|保証します|間違いなく|100\s*[%％]|誰でも|永久に|"
     r"業界No\.?1|日本一|最安値(?:です|でした|保証|を保証)|業界最安|日本最[安大高]",
     "景表法・アソシエイト規約のリスクになる断定表現", None),

    # ---- HIGH：美容・健康のやわらかい効果表現 ----------------------------
    ("HIGH", "美容・健康表現",
     # 「この場面では効きます」のような日常語の「効く」は拾わない。
     r"美白|痩せ(?:る|られ|ます)|(?:効果|効能)が(?:あり|得られ)ます|"
     r"肌荒れが(?:治|改善)|くすみが(?:取れ|消え)|ハリが戻|"
     r"メイク崩れを防(?:ぎ|げ)|皮脂を抑え(?:ます|られ)|"
     r"血圧を(?:下げ|改善)|睡眠の質が(?:上が|改善)|健康を改善",
     "効果を断定的に読ませる表現。使用感・成分表示・メーカーの説明に置き換える",
     {"beauty", "health"}),

    # ---- HIGH：未公表の技術情報を断定 ------------------------------------
    ("HIGH", "未確認スペック断定",
     r"耐久性が(?:高|あり|優れ)|頑丈です|壊れにくいです|"
     r"防水(?:です|なので)|放熱性が(?:高|優れ)|冷却性能が(?:高|優れ)|"
     r"バッテリーは\s*\d+\s*年|寿命は\s*\d+",
     "メーカーが明示していない事項を事実として断定している", None),

    # ---- HIGH：AI らしい定型表現 -----------------------------------------
    ("HIGH", "AI定型表現",
     r"と言えるでしょう|と言えます|と考えられます|が期待できます|"
     r"最大の魅力(?:です|は)|総合的に判断すると|"
     r"非常に(?:優れ|魅力的|便利)|大きな(?:ポイント|メリット)です|"
     r"という(?:選択肢も|価値が)|バランスの取れた|ということが分かります",
     "AI が量産する定型のヘッジ表現。事実→判断の順に書き換える", None),

    # ---- HIGH：架空の生活シーンを実体験として書く ------------------------
    ("HIGH", "架空の生活シーン",
     r"(?:深夜|夜中|朝)\s*\d+\s*時[^。]{0,20}(?:帰宅|起き|目が覚め)|"
     r"ある日|そんなとき私|筆者(?:は|が)",
     "架空の人物・場面を作っている。「想定される利用場面」として書く", None),

    # ---- MEDIUM：比較対象があいまい ---------------------------------------
    ("MEDIUM", "曖昧な比較対象",
     r"一般的な(?:商品|製品|モデル|美容液|クリーム)|同クラス(?:の)?(?:製品|商品)|"
     r"平均的な(?:商品|製品|モデル)|標準的な(?:商品|製品|モデル)|"
     r"他社製品では|一般的な他社",
     "実在しない比較対象。実在の型番に置き換えるか、比較そのものをやめる", None),

    # ---- MEDIUM：煽り・ダークパターン -------------------------------------
    ("MEDIUM", "煽り表現",
     r"在庫僅少|残りわずか|売り切れ間近|お早めに|今すぐ買|買い逃|"
     r"今だけ|本日限り|期間限定|まもなく終了|間もなく終了|"
     r"知らないと損|買わない理由がな|話題沸騰|爆売れ",
     "読者を急かす・貶す表現", None),

    # ---- LOW：冗長な言い回し ---------------------------------------------
    ("LOW", "冗長表現",
     r"することができます|というのが(?:実情|実態)です|"
     r"言うまでもありませんが|改めて言うまでもなく|"
     r"〜という点においては",
     "短く言い切れる", None),
]

# AI定型表現は1〜2回なら許容する。これを超えたら指摘に上げる。
AI_PHRASE_LIMIT = 3

# 実体験の禁止語のうち、打ち消し文脈（「〜とは書けません」等）で出ることがある
# 直後にこれらが来る一致は拾わない。
# 「シワが消えるような変化を期待する人には向きません」「実測したわけではありません」
# のように、**否定・仮定・読者への助言**として使われている形。
NEGATION = re.compile(
    r"[^。]{0,30}?(?:ませ[んぬ]|ないでください|わけでは|とは限|ような|"
    r"か[？?]|かどうか|"
    r"ようなこと|と(?:は)?思わ|期待(?:する|しては)|保証はあり|"
    r"ものではあり|とうたう|と(?:は)?書き|と称する)")


def texts(v, path=""):
    """記事の中の文字列を、どこにあるかと一緒に取り出す。"""
    if isinstance(v, str):
        yield path, v
    elif isinstance(v, list):
        for i, x in enumerate(v):
            yield from texts(x, f"{path}[{i}]")
    elif isinstance(v, dict):
        for k, x in v.items():
            if k in SKIP_KEYS:
                continue
            yield from texts(x, f"{path}.{k}" if path else k)


def plain(s):
    return re.sub(r"<[^>]+>", "", s)


def body_text(a):
    return "".join(plain(s) for _, s in texts(a))


def kind_of(a):
    """記事の種類。build.py の kind_of と同じ判定にそろえる。"""
    k = a.get("kind")
    if k in ("review", "roundup", "guide", "sale", "howto"):
        return k
    return "roundup" if a.get("category") == "feature" else "review"


def find_patterns(a):
    """正規表現にかかった箇所を拾う。"""
    hits = []
    ai_phrases = []
    cat = a.get("category")
    for path, s in texts(a):
        p = plain(s)
        for level, label, pat, why, cats in RULES:
            if cats and cat not in cats:
                continue
            for m in re.finditer(pat, p):
                # 「〜と書きません」のような打ち消し文は拾わない
                if NEGATION.match(p[m.end():m.end() + 40]):
                    continue
                if label == "AI定型表現":
                    ai_phrases.append((path, m.group(0)))
                    continue
                hits.append((level, label, path, m.group(0), why))

    # AI定型表現は回数で判定する（1〜2回は文章の自然な範囲）
    if len(ai_phrases) >= AI_PHRASE_LIMIT:
        c = Counter(w for _, w in ai_phrases)
        top = "、".join(f"「{w}」×{n}" for w, n in c.most_common(4))
        hits.append(("HIGH", "AI定型表現", "本文全体",
                     f"{len(ai_phrases)}回（{top}）",
                     "AI が量産する定型のヘッジ表現。事実→判断の順に書き換える"))
    return hits


def find_structure(a):
    """正規表現では見えない、記事の作りの問題を見る。"""
    hits = []
    kind = kind_of(a)
    text = body_text(a)

    def add(level, label, where, what, why):
        hits.append((level, label, where, what, why))

    # ---- 公式情報の裏づけ ------------------------------------------------
    facts = a.get("facts") or []
    if isinstance(facts, str):
        facts = [facts]
    if kind == "review":
        if not (a.get("official_url") or "").strip():
            add("HIGH", "公式情報不足", "official_url", "未設定",
                "メーカー公式の製品ページが無い。仕様の一次情報を確認できない")
        if not facts:
            add("HIGH", "公式情報不足", "facts", "未設定",
                "公式で裏を取った仕様が記事データに無い。生成時に推測が混ざる")

    # ---- 情報源と最終確認日 ----------------------------------------------
    concl = a.get("conclusion")
    concl = "".join(concl) if isinstance(concl, list) else (concl or "")
    if a.get("published"):
        if "最終確認日" not in plain(concl):
            add("HIGH", "情報源の明示不足", "conclusion", "最終確認日なし",
                "まとめの最終段落に「最終確認日：YYYY年MM月DD日」を書く")
        if not re.search(r"公式|情報源|メーカーサイト|販売ページ", plain(concl)):
            add("HIGH", "情報源の明示不足", "conclusion", "情報源の記載なし",
                "まとめの最終段落に、使った主要な情報源を書く")

    # ---- 事実・口コミ・分析の区別 ----------------------------------------
    marks = {
        "メーカー公表": bool(re.search(r"メーカー(?:公式|仕様|の公表|は)|公式(?:仕様|サイト|の公表)|公表値", text)),
        "購入者評価": bool(re.search(r"購入者レビュー|口コミでは|レビューでは|一部の口コミ", text)),
        "編集部の判断": bool(re.search(r"モノベース(?:は|では)|当サイト(?:は|では)|公開情報から判断", text)),
    }
    missing = [k for k, v in marks.items() if not v]
    if missing and kind in ("review", "roundup"):
        add("HIGH", "事実と推測の分離不足", "本文全体",
            "／".join(missing) + " の帰属表現なし",
            "「メーカー公表の事実」「購入者の評価」「モノベースの判断」を読者が区別できる書き方にする")

    # ---- 独自性 ----------------------------------------------------------
    original = re.search(
        r"食い違|一致しません|一方で|評価が分かれ|分かれる理由|見落と|"
        r"公式仕様では[^。]{0,40}(?:が|けれど|ものの)|"
        r"レビューを読み込|突き合わせ", text)
    if not original and kind in ("review", "roundup"):
        add("HIGH", "独自性不足", "本文全体", "独自分析の手がかりなし",
            "口コミと公式仕様の食い違い・評価が分かれる理由・見落としやすい点のいずれかを入れる")

    # ---- 評価の根拠 -------------------------------------------------------
    rating = a.get("rating") or {}
    score = rating.get("score")
    if score:
        bd = plain(str(rating.get("breakdown") or ""))
        if len(bd) < 20:
            add("HIGH", "評価根拠不足", "rating.breakdown",
                f"score {score} / 内訳 {len(bd)}字",
                "何を評価し何を減点したのかを1文で書く。書けないなら数値を出さない")
        if not facts and kind == "review":
            add("HIGH", "評価根拠不足", "rating.score", f"{score}",
                "公式で裏を取った仕様が無いまま 0.1 刻みの点数を出している")

    # ---- 記事タイプに合わない見出し --------------------------------------
    if kind in ("roundup", "guide", "sale", "howto"):
        for key, label in (("scenes", "この商品で変わる生活シーン"),
                           ("highlights", "この商品の強み")):
            v = a.get(key)
            has = bool(v.get("items")) if isinstance(v, dict) else bool(v)
            if has:
                add("HIGH", "テンプレート流用", key, label,
                    f"{kind} 記事に単一商品レビュー用の枠を入れている")

    # ---- 生活シーンの見出し ----------------------------------------------
    if a.get("scenes"):
        add("MEDIUM", "生活シーンの表現", "scenes",
            f"{len(a['scenes'])}項目",
            "「実際の生活シーン」ではなく「想定される利用場面」として読める内容か確認する")

    # ---- FAQ --------------------------------------------------------------
    faq = [q for q in (a.get("faq") or []) if q.get("q") and q.get("a")]
    if a.get("published") and len(faq) < 3:
        add("MEDIUM", "FAQ不足", "faq", f"{len(faq)}問",
            "購入前に実際に迷う点を3〜6問。ただし埋めるためだけの質問は入れない")
    for i, q in enumerate(faq):
        ans = q["a"] if isinstance(q["a"], str) else "".join(q["a"])
        if re.fullmatch(r"\s*(?:はい|いいえ)[、。]?\s*おすすめ.{0,12}", plain(ans)):
            add("MEDIUM", "FAQ不足", f"faq[{i}]", plain(ans)[:24],
                "「おすすめですか？→はい」の類は載せない")

    # ---- 比較表 -----------------------------------------------------------
    sp = a.get("spec") or {}
    if sp.get("rows"):
        basis = plain(str(sp.get("intro", "")) + str(sp.get("read", "")))
        if not re.search(r"同(?:じ|価格帯|クラス|用途)|価格帯|基準|比較(?:した|の軸)", basis):
            add("MEDIUM", "比較基準の欠落", "spec",
                "比較の基準が書かれていない",
                "何を基準に並べたのか（用途・価格帯・同クラス）を intro か read に書く")
    elif kind in ("review", "roundup"):
        add("MEDIUM", "比較なし", "spec", "比較表なし",
            "比較できる実在商品が無いなら無理に作らなくてよい。判断の記録として")

    # ---- 内部リンク -------------------------------------------------------
    links = [it for it in (a.get("next_problem") or {}).get("items", [])
             if (it.get("link_url") or "").strip()]
    if a.get("published") and not links:
        add("MEDIUM", "内部リンク不足", "next_problem", "リンクなし",
            "読者が次に知りたい情報につながる既存記事があれば1〜2本つなぐ")

    # ---- SEO --------------------------------------------------------------
    desc = plain(a.get("description") or "")
    if a.get("published"):
        if not desc:
            add("MEDIUM", "SEO", "description", "未設定", "メタディスクリプションが無い")
        elif len(desc) > 130:
            add("LOW", "SEO", "description", f"{len(desc)}字",
                "検索結果で切れる。120字以内に収める")
        t = plain(a.get("title") or "")
        if len(t) > 35:
            add("LOW", "SEO", "title", f"{len(t)}字", "35字を超えると検索結果で切れる")

    # ---- 分量 -------------------------------------------------------------
    n = len(text)
    if a.get("published"):
        if n < 6000:
            add("MEDIUM", "分量", "本文", f"{n:,}字", "下限 6,000字")
        elif n > 12000:
            add("LOW", "分量", "本文", f"{n:,}字", "上限 12,000字")

    return hits


def audit(a):
    return find_patterns(a) + find_structure(a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", action="append", default=[], help="この記事だけ見る")
    ap.add_argument("--all", action="store_true", help="下書きも含めて全部")
    ap.add_argument("--min", default="low",
                    choices=[x.lower() for x in LEVELS],
                    help="この深刻度以上だけ表示する（既定 low）")
    ap.add_argument("--json", help="結果をJSONで書き出す先")
    ap.add_argument("--quiet", action="store_true", help="集計だけ出す")
    args = ap.parse_args()

    arts = json.load(io.open(os.path.join(ROOT, "content", "articles.json"),
                             encoding="utf-8"))
    if args.slug:
        want = set(args.slug)
        targets = [a for a in arts if a.get("slug") in want]
    elif args.all:
        targets = list(arts)
    else:
        targets = [a for a in arts if a.get("published")]

    if not targets:
        print("対象の記事がありません。")
        return 0

    floor = LEVELS.index(args.min.upper())
    total = Counter()
    report = []

    for a in targets:
        hits = [h for h in audit(a) if LEVELS.index(h[0]) <= floor]
        c = Counter(h[0] for h in hits)
        total.update(c)
        report.append({
            "slug": a.get("slug"),
            "kind": kind_of(a),
            "category": a.get("category"),
            "counts": {k: c.get(k, 0) for k in LEVELS},
            "findings": [{"level": l, "label": lb, "where": w,
                          "what": s, "why": y} for l, lb, w, s, y in hits],
        })

    report.sort(key=lambda r: [-r["counts"][k] for k in LEVELS])

    if not args.quiet:
        for r in report:
            head = "  ".join(f"{k[0]}{r['counts'][k]}" for k in LEVELS)
            print(f"\n■ {r['slug']}  [{r['kind']}/{r['category']}]  {head}")
            for f in r["findings"]:
                print(f"   {f['level']:<8} [{f['label']}] {f['where']}"
                      f"：{f['what']}\n            → {f['why']}")

    print(f"\n{'=' * 60}")
    print(f"記事 {len(targets)} 本 / 指摘 {sum(total.values())} 件")
    for k in LEVELS:
        print(f"  {k:<9} {total.get(k, 0):>4} 件")
    worst = [r["slug"] for r in report if r["counts"]["CRITICAL"]]
    if worst:
        print("\nCRITICAL がある記事（先に直す）：" + "、".join(worst))

    if args.json:
        with io.open(args.json, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        print(f"\n{args.json} に書き出しました。")

    print("\n※ この道具は記事を書き換えません。直すかどうかは人が決めます。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
