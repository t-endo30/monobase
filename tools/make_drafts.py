#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/pick_products.py が集めた候補から、記事の下書きを作る。

管理画面の「選んだ商品で下書きを作る」と同じことを、手元とCIでもできるようにする。
埋めるのは機械的に決まる項目だけ。本文は tools/write_article.py が書く。

  $ python3 tools/pick_products.py --limit 20      # 候補を集める
  $ python3 tools/make_drafts.py --take 5          # 上位5件を下書きに
  $ python3 tools/write_article.py --drafts        # 本文を書かせる

下書きは published=false で作る。公開は管理画面から手で行う。
"""
import json, io, os, re, sys, time, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    return json.load(io.open(os.path.join(ROOT, path), encoding="utf-8"))


def clean_name(s):
    """商品名から飾りを落とす。【送料無料】【ポイント10倍】など。"""
    s = re.sub(r"[【\[（(][^】\]）)]{0,20}"
               r"(送料無料|ポイント|クーポン|セール|限定|正規品|あす楽)"
               r"[^】\]）)]{0,20}[】\]）)]", "", str(s or ""))
    return re.sub(r"\s+", " ", s).strip()


def draft_slug(name, cat, taken):
    """商品名からURLを作る。日本語だけの名前だと英数字が拾えないので、
       その場合はカテゴリー＋日付にして、あとで直せる形にする。"""
    latin = re.findall(r"[a-z0-9][a-z0-9\-]*", str(name).lower())
    base = re.sub(r"-+", "-", "-".join(latin)).strip("-")[:50]
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
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--take", type=int, default=5, help="下書きにする件数")
    ap.add_argument("--from", dest="src", default="content/candidates.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

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
