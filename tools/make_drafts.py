#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/pick_products.py が集めた候補から、記事の下書きを作る。

管理画面の「選んだ商品で下書きを作る」と同じことを、手元とCIでもできるようにする。
埋めるのは機械的に決まる項目だけ。本文は tools/write_article.py が書く。

  $ python3 tools/pick_products.py --limit 20      # 候補を集める
  $ python3 tools/make_drafts.py --take 5          # 上位5件を下書きに
  $ python3 tools/write_article.py --drafts        # 本文を書かせる

下書きは published=false で作る。公開は管理画面から手で行う。

Amazonへの導線は、どの下書きにも必ず1本入れる。候補は楽天とYahoo!の
商品検索から集めるので、Amazonの商品ページ（ASIN）は分からない。その
場合はAmazonの検索結果へのリンクを入れておく。ASINが分かったら記事の
asin を埋めれば、商品ページへの直リンクに切り替わる。
"""
import json, io, os, re, sys, time, argparse, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    return json.load(io.open(os.path.join(ROOT, path), encoding="utf-8"))


# 商品名に混ざる売り文句。楽天・Yahoo!の商品名は、検索に当てるため
# 飾りが長く付く。題名とURLに使う前に、ここを落とす。
PROMO = (r"送料無料|ポイント\s*[0-9０-９]+\s*倍|最大[0-9０-９]+[%％]\s*(OFF|オフ)?|"
         r"[0-9０-９]+[%％]\s*(OFF|オフ)|半額|クーポン|セール|SALE|あす楽|即納|"
         r"限定|正規品|国内正規|新品|未使用|公式|メーカー保証|[0-9０-９]+年保証|"
         r"ランキング[0-9０-９]*[位週]?|[0-9０-９]+冠|レビュー特典|"
         r"楽天スーパー(SALE|セール)?|[0-9０-９]+週?[0-9０-９]*位|"
         r"期間限定|実施中|[0-9０-９]+/[0-9０-９]+まで|"
         r"タイムセール|買い回り|お買い物マラソン|"
         r"最新(バージョン|モデル)?|大容量|翌日配送|当日出荷|プレゼント|"
         r"母の日|父の日|敬老の日|お歳暮|お中元|ギフト|ラッピング")


def clean_name(s):
    """商品名から売り文句を落として、題名に使える形にする。

       楽天の商品名は検索に当てるための飾りが長い。
         【ケノン 公式 楽天スーパーSALE！3年保証】（最新バージョン）脱毛器 ランキング58週1位
       この形のまま題名にすると読めないので、括弧の中身と売り文句を落とす。
       ただし括弧を丸ごと消すと、ブランド名や型番まで消えることがあるため、
       括弧の中は「売り文句だけで出来ているとき」に限って落とす。"""
    s = str(s or "")

    def drop(m):
        inner = m.group(1)
        # 中身から売り文句を抜いても何か残るなら、それは商品の情報なので残す。
        rest = re.sub(PROMO, "", inner)
        rest = re.sub(r"[\s　!！・/／、,]+", "", rest)
        return "" if len(rest) <= 2 else " " + inner + " "

    for _ in range(3):          # 入れ子の括弧を順にほどく
        s2 = re.sub(r"[【\[]([^】\]]*)[】\]]", drop, s)
        s2 = re.sub(r"[（(]([^）)]*)[）)]", drop, s2)
        if s2 == s:
            break
        s = s2
    s = re.sub(PROMO, " ", s)
    # 売り文句を抜いたあとに残る記号と、区切りだけの並び
    s = re.sub(r"[／|｜/]{1,}", " ", s)
    s = re.sub(r"[!！]{1,}", " ", s)
    return re.sub(r"[\s　]+", " ", s).strip(" 　-・,、")


def amazon_search_url(name, jan=""):
    """Amazonの検索結果へのリンクを作る。

       候補は楽天とYahoo!の商品検索から集めているため、Amazonの商品ページ
       （ASIN）は分からない。PA-APIの承認が下りるまで、これは埋まらない。
       それでも記事にはAmazonへの導線を必ず1本置く。読者の多くはAmazonで
       買うため、経路が無い記事は取りこぼしになる。

       JANがあれば型番で絞れるので、それを検索語にする。無ければ商品名。
       アソシエイトIDは build.py の amazon_tagged が付ける（Amazonは
       検索結果へのリンクでも成果を計上する）。

       ASINが分かったら記事の asin を埋めればよい。build.py は asin を
       優先するので、商品ページへの直リンクに自動で切り替わる。"""
    q = str(jan or "").strip() or str(name or "").strip()
    if not q:
        return ""
    return ("https://www.amazon.co.jp/s?k="
            + urllib.parse.quote(q, safe="") + "&i=aps")


# URLに使わない語。数字だけ・単位つき・売り文句は、商品を指さない。
SLUG_DROP = re.compile(
    r"^(?:[0-9]+(?:ml|l|g|kg|cm|mm|m|w|v|a|ah|mah|inch|型|枚|本|個|台|点|"
    r"set|pcs|p)?|off|sale|new|pro?|plus|set|no|vol|ver)$")


def draft_slug(name, cat, taken):
    """商品名からURLを作る。

       ブランドと型番にあたる語だけを拾う。値段・枚数・割引率まで拾うと
       「sale-3-587-1-vio-ipl-9」のような、何の記事か分からないURLになる。
       拾える語が無いときはカテゴリー＋日付にして、あとで直せる形にする。"""
    latin = re.findall(r"[a-z0-9][a-z0-9\-]*", str(name).lower())
    keep = [w for w in latin if not SLUG_DROP.match(w)]
    # 数字だけの語は、前の語につながっているときだけ意味がある（watch 5 など）
    keep = [w for w in keep if not w.isdigit() or len(w) >= 3]
    base = re.sub(r"-+", "-", "-".join(keep[:6])).strip("-")[:50]
    if len(base) < 3:
        base = f"{cat}-{time.strftime('%Y%m%d')}"
    slug, n = base, 2
    while slug in taken:
        slug = f"{base}-{n}"
        n += 1
    taken.add(slug)
    return slug


def draft_tags(name, cat_label):
    words = [w.strip("【】[]（）()「」")
             for w in re.split(r"[\s　・／/,、]+", str(name))]
    tags = [w for w in words
            if 2 <= len(w) <= 14 and not re.fullmatch(r"[0-9,.]+", w)][:3]
    if cat_label and cat_label not in tags:
        tags.append(cat_label)
    return tags


def make_draft(c, site, taken):
    cat_key = c.get("category", "")
    cat = next((x for x in site.get("categories", [])
                if x.get("key") == cat_key), {})
    label = cat.get("label", "")
    name = clean_name(c.get("name", ""))
    today = time.strftime("%Y-%m-%d")

    a = {
        "slug": draft_slug(name, cat_key, taken),
        "category": cat_key, "sub": "",
        "published": False, "featured": False,
        "title": name, "list_title": name[:30],
        # 仮の文章。本文を書くときに書き換わる。
        "description": f"{name}は買う価値があるのか。"
                       "レビューを読み込んで、良い点と注意点、向いている人を整理します。",
        "excerpt": f"レビューから見えた、{name[:24]}の実力と向き不向き。",
        "date": today, "updated": today,
        "tags": draft_tags(name, label),
        "icon": cat.get("icon") or "📦",
        "thumb": "",
        "asin": "", "amazon_url": "",
        "cta_label": "Amazonで価格と詳細を確認する",
        "verdict_title": "結論：", "summary": [],
        "rating": {"score": 0, "breakdown": ""},
        "lead": "",
        "not_for": {"intro": "", "items": []},
        "scenes": [], "personal_note": "",
        "next_problem": {"intro": "", "items": []},
        "pros": [], "cons": [],
        "spec": {"intro": "", "headers": [], "rows": []},
        "voices_intro": "", "voices": [],
        "conclusion_title": "まとめ", "conclusion": "",
    }
    if c.get("jan"):
        a["jan"] = c["jan"]
    for key in ("rakuten_url", "yahoo_url", "amazon_url"):
        if c.get(key):
            a[key] = c[key]
    if c.get("asin"):
        a["asin"] = c["asin"]
    # Amazonへの導線は必ず1本入れる。商品ページが分からないときは検索結果へ。
    if not (a.get("asin") or a.get("amazon_url")):
        a["amazon_url"] = amazon_search_url(name, c.get("jan"))
    return a


def fill_existing(dry_run):
    """すでにある記事で、Amazonへの導線が無いものに検索リンクを入れる。

       対象は商品を1つ扱っている記事だけ。特集や選び方の記事は、扱う商品が
       1つに決まらないため、商品名で検索させても読者の役に立たない。
       楽天かYahoo!の商品URL、またはJANを持っていることを目印にする。"""
    path = os.path.join(ROOT, "content", "articles.json")
    arts = json.load(io.open(path, encoding="utf-8"))
    done, skipped = [], []
    for a in arts:
        if (a.get("asin") or "").strip() or (a.get("amazon_url") or "").strip():
            continue
        product = bool(a.get("jan") or a.get("rakuten_url") or a.get("yahoo_url"))
        # 「｜」以降の説明と、末尾の「レビュー」「口コミ」を落として商品名にする
        name = re.sub(r"[｜|].*$", "", str(a.get("title") or ""))
        name = clean_name(re.sub(
            r"[\s　]*(徹底|正直)?(レビュー|口コミ(分析)?|評価|選び方|比較)$",
            "", name).strip())
        if not product or not name:
            skipped.append(a.get("slug", ""))
            continue
        a["amazon_url"] = amazon_search_url(name, a.get("jan"))
        done.append((a.get("slug", ""), name))

    print(f"Amazonへの導線が無い記事：{len(done) + len(skipped)} 本")
    for slug, name in done:
        print(f"  埋める  {slug}  ← 「{name[:34]}」で検索")
    for slug in skipped:
        print(f"  見送り  {slug}（商品を1つに絞れない記事）")
    if not done:
        return 0
    if dry_run:
        print("\n（--dry-run のため書き込んでいません）")
        return 0
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(arts, f, ensure_ascii=False, indent=1)
    print(f"\n{len(done)} 本に書き込みました。python3 build.py で反映します。")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--take", type=int, default=5, help="下書きにする件数")
    ap.add_argument("--from", dest="src", default="content/candidates.json")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fill-existing", action="store_true",
                    help="すでにある記事のうち、Amazonへの導線が無いものを埋める")
    args = ap.parse_args()

    if args.fill_existing:
        return fill_existing(args.dry_run)

    src = os.path.join(ROOT, args.src)
    if not os.path.exists(src):
        print(f"{args.src} がありません。先に tools/pick_products.py を実行してください。",
              file=sys.stderr)
        return 1

    cands = json.load(io.open(src, encoding="utf-8")).get("items", [])
    arts = load("content/articles.json")

    taken = {a.get("slug") for a in arts if a.get("slug")}
    seen_jan = {str(a.get("jan")) for a in arts if a.get("jan")}
    seen_name = {clean_name(a.get("title", ""))[:20] for a in arts}

    made = []
    for c in cands:
        if len(made) >= args.take:
            break
        name = clean_name(c.get("name", ""))
        if not name:
            continue
        # すでに書いた商品は飛ばす。JANが無い場合は名前の頭で見る。
        if c.get("jan") and str(c["jan"]) in seen_jan:
            continue
        if name[:20] in seen_name:
            continue
        seen_name.add(name[:20])
        if c.get("jan"):
            seen_jan.add(str(c["jan"]))
        made.append(make_draft(c, load("content/site.json"), taken))

    if not made:
        print("下書きにできる候補がありませんでした（すべて既出です）。")
        return 0

    for a in made:
        shops = "/".join(k.replace("_url", "") for k in
                         ("amazon_url", "rakuten_url", "yahoo_url") if a.get(k))
        if a.get("amazon_url", "").startswith("https://www.amazon.co.jp/s?"):
            shops = shops.replace("amazon", "amazon(検索)")
        print(f"  ・{a['title'][:44]}")
        print(f"     {a['slug']} / {a['category']} / {shops or '—'}")

    if args.dry_run:
        print(f"\n（--dry-run のため書き込んでいません）")
        return 0

    arts = made + arts          # 新しい記事を先頭に置く
    with io.open(os.path.join(ROOT, "content", "articles.json"),
                 "w", encoding="utf-8") as f:
        json.dump(arts, f, ensure_ascii=False, indent=1)
    print(f"\n下書きを {len(made)} 本作りました（published=false）。")
    print("次にやること：python3 tools/write_article.py --drafts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
