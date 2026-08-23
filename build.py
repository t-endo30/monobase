#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kurashi Pick - 静的サイトジェネレーター

  content/site.json     … サイト全体の設定（GA・GSC・カテゴリ・機能ON/OFF）
  content/articles.json … 記事データ

  $ python3 build.py

生成物: index.html / articles/*.html / category-*.html /
        search.html / about.html / privacy.html / disclaimer.html /
        404.html / search.json / sitemap.xml / robots.txt
"""
import json, io, os, html, shutil, sys, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

SITE = json.load(io.open("content/site.json", encoding="utf-8"))
ARTICLES = json.load(io.open("content/articles.json", encoding="utf-8"))

NAME     = SITE["site_name"]
TAGLINE  = SITE["tagline"]
BASE_URL = SITE["base_url"].rstrip("/")
CATS     = SITE["categories"]
FEAT     = SITE.get("features", {})
GA       = SITE.get("analytics", {}).get("ga_measurement_id", "").strip()
GSC      = SITE.get("analytics", {}).get("gsc_verification", "").strip()
CAT_LABEL = {c["key"]: c["label"] for c in CATS}
CAT_ICON  = {c["key"]: c["icon"]  for c in CATS}

PUBLISHED = sorted([a for a in ARTICLES if a.get("published")],
                   key=lambda a: a.get("date", ""), reverse=True)

def e(s):
    return html.escape(str(s), quote=True)

def jp_date(iso):
    try:
        y, m, d = iso.split("-")
        return "%s年%s月%s日" % (y, int(m), int(d))
    except Exception:
        return iso

# ============================================================ 共通パーツ
def head(title, desc, current, p, canonical, extra=""):
    """p = ルートへの相対プレフィックス（"./" または "../"）"""
    ga = ""
    if GA:
        ga = f'''<script async src="https://www.googletagmanager.com/gtag/js?id={e(GA)}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{e(GA)}');
</script>
'''
    gsc = f'<meta name="google-site-verification" content="{e(GSC)}">\n' if GSC else ""
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(canonical)}">
{gsc}<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:site_name" content="{e(NAME)}">
<meta property="og:url" content="{e(canonical)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{p}assets/style.css">
{extra}{ga}</head>
<body>
'''

def header(current, p):
    allcur = ' class="is-current"' if current == "all" else ""
    nav = f'      <li><a href="{p}index.html"{allcur}>ALL</a></li>\n'
    for c in CATS:
        cur = ' class="is-current"' if c["key"] == current else ""
        nav += (f'      <li><a href="{p}category-{c["key"]}.html"{cur}>'
                f'<span class="cat-icon" aria-hidden="true">{c["icon"]}</span>{e(c["label"])}</a></li>\n')

    search_link = (f'<li><a href="{p}search.html">検索</a></li>\n        '
                   if FEAT.get("search") else "")
    contact_nav = (f'<li><a href="{p}contact.html">お問い合わせ</a></li>'
                   if FEAT.get("contact_form") else
                   f'<li><a href="mailto:{e(SITE["email"])}">お問い合わせ</a></li>')

    return f'''<header class="site-header">
  <div class="container header-inner">
    <div class="site-brand">
      <div class="site-title"><a href="{p}index.html">{e(NAME)}</a></div>
      <div class="site-tagline">{e(TAGLINE)}</div>
    </div>
    <button class="nav-toggle" id="navToggle" aria-expanded="false" aria-controls="globalNav" aria-label="メニューを開く">
      <span></span><span></span><span></span>
    </button>
    <nav class="global-nav" id="globalNav">
      <ul>
        <li><a href="{p}index.html">ホーム</a></li>
        {search_link}<li><a href="{p}about.html">運営者情報</a></li>
        {contact_nav}
      </ul>
    </nav>
  </div>
</header>

<!-- カテゴリーナビゲーション -->
<nav class="cat-nav" aria-label="カテゴリー">
  <div class="container">
    <ul class="cat-nav-list">
{nav}    </ul>
  </div>
</nav>

<!-- 広告表記 -->
<div class="site-notice">
  <div class="container">
    <p>
      <span class="notice-label">お知らせ</span>
      当サイトの記事には広告（Amazonアソシエイト等）を含みます。掲載価格・在庫は執筆時点のもので、最新情報は販売ページをご確認ください。
    </p>
  </div>
</div>
'''

def footer(p, sticky_url=None):
    catlinks = "".join(
        f'          <li><a href="{p}category-{c["key"]}.html">{e(c["label"])}</a></li>\n' for c in CATS)
    if FEAT.get("contact_form"):
        contact = (f'<p>下記のフォームからお気軽にご連絡ください。通常3営業日以内に返信いたします。</p>\n'
                   f'        <a class="footer-contact-btn" href="{p}contact.html">お問い合わせフォーム</a>')
    else:
        contact = (f'<p>記事内容の誤り・掲載依頼などはメールでご連絡ください。通常3営業日以内に返信いたします。</p>\n'
                   f'        <a class="footer-contact-btn" href="mailto:{e(SITE["email"])}">メールで問い合わせる</a>')

    sticky = ""
    if sticky_url and FEAT.get("sticky_cta"):
        sticky = f'''<div class="sticky-cta" id="stickyCta">
  <a class="btn-amazon" href="{e(sticky_url)}" target="_blank" rel="nofollow sponsored noopener">
    <span class="cart">🛒</span>Amazonで価格を見る
  </a>
</div>

'''
    return f'''<footer class="site-footer" id="contact">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-col">
        <h3>{e(NAME)}</h3>
        <p>{e(TAGLINE)}をコンセプトに、実際に使ったアイテムを紹介するメディアです。良い点も悪い点も正直にお伝えし、あなたの「買って後悔した」を減らすことを目指しています。</p>
      </div>
      <div class="footer-col">
        <h3>カテゴリー</h3>
        <ul>
{catlinks}        </ul>
      </div>
      <div class="footer-col">
        <h3>サイト情報</h3>
        <ul>
          <li><a href="{p}privacy.html">プライバシーポリシー</a></li>
          <li><a href="{p}disclaimer.html">免責事項</a></li>
          <li><a href="{p}about.html">運営者情報</a></li>
          <li><a href="{p}search.html">サイト内検索</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h3>お問い合わせ</h3>
        {contact}
      </div>
    </div>

    <p class="assoc-note">
      当サイトは、Amazon.co.jpを宣伝しリンクすることによってサイトが紹介料を獲得できる手段を提供することを目的に設定されたアフィリエイトプログラムである、Amazonアソシエイト・プログラムの参加者です。<br>
      Amazon、Amazon.co.jp およびそれらのロゴは Amazon.com, Inc. またはその関連会社の商標です。
    </p>

    <p class="copyright">&copy; {e(SITE["founded"])} {e(NAME)}. All rights reserved.</p>
  </div>
</footer>

{sticky}<button class="to-top" id="toTop" aria-label="ページ上部へ戻る">▲</button>

<script src="{p}assets/main.js"></script>
</body>
</html>
'''

def page(title, desc, current, p, canonical, body, sticky_url=None, extra_head="", extra_js=""):
    return (head(title, desc, current, p, canonical, extra_head)
            + header(current, p)
            + f'\n<main id="top" class="layout">\n  <div class="container">\n{body}  </div>\n</main>\n\n'
            + footer(p, sticky_url).replace("</body>", extra_js + "</body>"))

# ============================================================ 部品
def thumb(a, p):
    if a.get("thumb"):
        return (f'<img src="{p}{e(a["thumb"])}" alt="{e(a.get("list_title") or a["title"])}" '
                f'loading="lazy" width="640" height="360">')
    return (f'<span aria-hidden="true" style="font-size:26px;margin-right:8px;">'
            f'{a.get("icon","📦")}</span>IMAGE 16:9')

def card(a, p):
    tags = "".join(f'<span class="tag">{e(t)}</span>' for t in a.get("tags", [])[:2])
    tags += f'<span class="tag tag-hot">{e(CAT_LABEL.get(a["category"], ""))}</span>'
    return f'''        <article class="card">
          <a class="card-thumb" href="{p}articles/{e(a["slug"])}.html">{thumb(a, p)}</a>
          <div class="card-body">
            <div class="card-tags">{tags}</div>
            <h3 class="card-title"><a href="{p}articles/{e(a["slug"])}.html">{e(a.get("list_title") or a["title"])}</a></h3>
            <p class="card-desc">{e(a.get("excerpt",""))}</p>
            <a class="card-link" href="{p}articles/{e(a["slug"])}.html">詳細を見る</a>
          </div>
        </article>
'''

def grid(items, p):
    if not items:
        return ('      <p class="empty-state">このカテゴリーの記事は準備中です。'
                '<a href="' + p + 'index.html">トップページ</a>から他の記事をご覧ください。</p>\n')
    return '      <div class="card-grid">\n' + "\n".join(card(a, p) for a in items) + '      </div>\n'

def cta(url, label, note=""):
    n = f'\n          <p class="cta-note">{e(note)}</p>' if note else ""
    return f'''        <div class="cta-wrap">
          <a class="btn-amazon" href="{e(url)}" target="_blank" rel="nofollow sponsored noopener">
            <span class="cart">🛒</span>{e(label)}
          </a>{n}
        </div>
'''

def stars(n):
    n = int(round(float(n or 0)))
    return "★" * n + "☆" * (5 - n)

# ============================================================ 記事ページ
def render_article(a):
    p = "../"
    slug = a["slug"]
    cat = a["category"]
    url = f'{BASE_URL}/articles/{slug}.html'
    b = []
    add = b.append

    add(f'''      <div class="breadcrumb">
        <a href="{p}index.html">ホーム</a><span>›</span>
        <a href="{p}category-{cat}.html">{e(CAT_LABEL.get(cat,""))}</a><span>›</span>{e(a.get("list_title") or a["title"])}
      </div>
''')
    add('      <article class="card-surface" id="review">\n')
    add(f'''        <div class="article-meta">
          <span class="badge badge-cat">{e(CAT_LABEL.get(cat,""))}</span>
          <span class="badge badge-pr">PR・広告を含みます</span>
          <span class="article-date">{e(jp_date(a.get("updated") or a["date"]))} 更新</span>
        </div>

        <h1 class="article-title">{e(a["title"])}</h1>
''')

    # アイキャッチ
    if a.get("thumb"):
        add(f'''        <figure class="eyecatch has-image">
          <img src="{p}{e(a["thumb"])}" alt="{e(a["title"])}" width="1200" height="675">
        </figure>
''')
    else:
        add(f'''        <figure class="eyecatch">
          <div class="eyecatch-placeholder">
            <span class="icon">{a.get("icon","📦")}</span>
            アイキャッチ画像を配置<br>（推奨サイズ 1200 × 675px）
          </div>
        </figure>
''')

    # 結論ボックス
    if a.get("summary"):
        items = "".join(f'              <li>{e(s)}</li>\n' for s in a["summary"])
        rating = ""
        sc = a.get("rating", {}).get("score") or 0
        if sc:
            rating = f'''          <div class="rating-row">
            <span class="stars">{stars(sc)}</span>
            <span class="rating-score">{sc}</span>
            <span class="rating-label">/ 5.0（{e(a["rating"].get("breakdown",""))}）</span>
          </div>
'''
        add(f'''        <section class="summary-box">
          <div class="summary-head">{e(a.get("verdict_title","結論"))}</div>
          <div class="summary-body">
            <ul class="summary-list">
{items}            </ul>
          </div>
{rating}        </section>
''')

    add(cta(a.get("amazon_url","#"), a.get("cta_label","Amazonで価格を見る"),
            "※ 価格・在庫は変動します。最新情報はリンク先でご確認ください。"))

    # 目次
    toc = []
    if a.get("not_for", {}).get("items"): toc.append(("sec-notfor", "買わないほうがいい人"))
    if a.get("scenes"):                   toc.append(("sec-scenes", "この商品で変わる生活シーン"))
    if a.get("pros") or a.get("cons"):    toc.append(("sec-proscons", "メリットとデメリット"))
    if a.get("spec", {}).get("rows"):     toc.append(("spec", "スペック比較表"))
    if a.get("voices"):                   toc.append(("sec-voice", "共通の不満点と対処法"))
    if a.get("next_problem", {}).get("items"): toc.append(("sec-next", "次に困りそうなこと"))
    if a.get("conclusion"):               toc.append(("sec-conclusion", "まとめ"))
    if toc:
        li = "".join(f'            <li><a href="#{i}">{e(t)}</a></li>\n' for i, t in toc)
        add(f'''        <nav class="toc" aria-label="目次">
          <div class="toc-title">目次</div>
          <ol>
{li}          </ol>
        </nav>
''')

    add('        <div class="article-body">\n')
    if a.get("lead"):
        add(f'          <p>{a["lead"]}</p>\n')

    # 1. 買わないほうがいい人（最優先のネガティブ訴求）
    nf = a.get("not_for", {})
    if nf.get("items"):
        items = "".join(f'              <li>{x}</li>\n' for x in nf["items"])
        add(f'''          <h2 id="sec-notfor">この商品を買わないほうがいい人</h2>
          <div class="notfor-box">
            <div class="notfor-head">⚠ 先に読んでください</div>
            <div class="notfor-body">
              <p>{e(nf.get("intro",""))}</p>
              <ul class="notfor-list">
{items}              </ul>
              <p class="notfor-foot">上のどれかに当てはまる場合、この商品は期待に応えられない可能性が高いです。別の選択肢を検討したほうが満足度は高くなります。</p>
            </div>
          </div>
''')

    # 2. この商品で変わる「実際の生活シーン」
    if a.get("scenes"):
        add('          <h2 id="sec-scenes">この商品で変わる「実際の生活シーン」</h2>\n')
        add('          <div class="scenes">\n')
        for i, sc in enumerate(a["scenes"], start=1):
            add(f'''            <div class="scene">
              <span class="scene-num">{i}</span>
              <div class="scene-body">
                <h3 class="scene-title">{e(sc.get("title",""))}</h3>
                <p>{sc.get("text","")}</p>
              </div>
            </div>
''')
        add('          </div>\n')

    # メリット / デメリット
    if a.get("pros") or a.get("cons"):
        pros = "".join(f'                <li>{p_}</li>\n' for p_ in a.get("pros", []))
        cons = "".join(f'                <li>{c_}</li>\n' for c_ in a.get("cons", []))
        add(f'''          <h2 id="sec-proscons">メリット・デメリット</h2>
          <div class="proscons">
            <div class="pc-box pc-good">
              <div class="pc-head">👍 良かった点（メリット）</div>
              <ul>
{pros}              </ul>
            </div>
            <div class="pc-box pc-bad">
              <div class="pc-head">👎 気になった点（デメリット）</div>
              <ul>
{cons}              </ul>
            </div>
          </div>
''')

    # スペック比較表
    sp = a.get("spec", {})
    if sp.get("rows"):
        HL = ' class="col-highlight"'
        th = "".join('<th scope="col"%s>%s</th>' % (HL if i == 1 else "", h)
                     for i, h in enumerate(sp["headers"]))
        rows = ""
        for r in sp["rows"]:
            tds = "".join("<td%s>%s</td>" % (HL if i == 1 else "", v)
                          for i, v in enumerate(r[1:], start=1))
            rows += f'                <tr><th scope="row">{r[0]}</th>{tds}</tr>\n'
        add(f'''          <h2 id="spec">スペック比較表</h2>
          <p>{e(sp.get("intro",""))}</p>
          <p class="scroll-hint">← 横にスクロールできます →</p>
          <div class="table-scroll" tabindex="0" role="region" aria-label="スペック比較表">
            <table>
              <thead>
                <tr>{th}</tr>
              </thead>
              <tbody>
{rows}              </tbody>
            </table>
          </div>
''')
        add(cta(a.get("amazon_url","#"), a.get("cta_label","Amazonでチェックする"),
                "タイムセール対象になっている場合があります"))

    # 口コミ・対策
    if a.get("voices"):
        add(f'          <h2 id="sec-voice">気になる点と、その対策</h2>\n')
        if a.get("voices_intro"):
            add(f'          <p>{e(a["voices_intro"])}</p>\n')
        for v in a["voices"]:
            st = (f'<span class="voice-stars">{stars(v["stars"])}</span>'
                  if v.get("stars") else "")
            neg = " is-negative" if v.get("negative") else ""
            add(f'''          <h3>{e(v.get("heading",""))}</h3>
          <div class="voice{neg}">
            <span class="voice-name">{e(v.get("who",""))}{st}</span>
            {e(v.get("text",""))}
          </div>
          <div class="fix-box">
            <span class="fix-title">✔ {e(v.get("fix_title",""))}</span>
            {e(v.get("fix",""))}
          </div>
''')

    # 6. 運営者の実体験コラム
    if a.get("personal_note"):
        add(f'''          <div class="personal-note">
            <span class="pn-label">運営者の実体験メモ</span>
            <p>{a["personal_note"]}</p>
          </div>
''')

    # 7. Amazonボタン
    add(cta(a.get("amazon_url","#"), "Amazonで価格と詳細を確認する",
            "※ 価格・在庫は変動します。最新情報はリンク先でご確認ください。"))

    # 8. 次に困りそうなこと・併売の提案（回遊導線）
    np_ = a.get("next_problem", {})
    if np_.get("items"):
        add('          <h2 id="sec-next">次に困りそうなこと</h2>\n')
        if np_.get("intro"):
            add(f'          <p>{e(np_["intro"])}</p>\n')
        add('          <div class="next-grid">\n')
        for it in np_["items"]:
            link = ""
            if it.get("link_url") and it.get("link_label"):
                link = (f'\n                <a class="next-link" href="{p}{e(it["link_url"])}">'
                        f'{e(it["link_label"])} <span aria-hidden="true">→</span></a>')
            add(f'''            <div class="next-card">
              <h3 class="next-title">{e(it.get("title",""))}</h3>
              <p>{it.get("text","")}</p>{link}
            </div>
''')
        add('          </div>\n')

    # まとめ
    if a.get("conclusion"):
        add(f'''          <h2 id="sec-conclusion">{e(a.get("conclusion_title","まとめ"))}</h2>
          <p>{a["conclusion"]}</p>
''')
        add(cta(a.get("amazon_url","#"), "Amazonで購入する",
                "※ 当リンクからの購入で当サイトに紹介料が発生する場合があります"))
        add(f'''        <div class="cta-wrap" style="margin-top:-10px;">
          <a class="btn-sub" href="{p}category-{cat}.html">同じカテゴリーの記事を見る</a>
        </div>
''')

    add('        </div>\n      </article>\n')

    # 関連記事
    rel = [x for x in PUBLISHED if x["slug"] != slug and x["category"] == cat]
    rel += [x for x in PUBLISHED if x["slug"] != slug and x["category"] != cat]
    rel = rel[:3]
    if rel:
        add(f'''
      <section class="section-block">
        <h2 class="section-heading">あわせて読みたい</h2>
        <p class="section-sub">同じ悩みを扱った記事です</p>
{grid(rel, p)}      </section>
''')

    # 構造化データ
    ld = {
      "@context": "https://schema.org", "@type": "Article",
      "headline": a["title"], "description": a.get("description",""),
      "datePublished": a["date"], "dateModified": a.get("updated") or a["date"],
      "author": {"@type": "Person", "name": SITE["author"]},
      "publisher": {"@type": "Organization", "name": NAME},
      "mainEntityOfPage": url,
    }
    extra_js = ('<script type="application/ld+json">'
                + json.dumps(ld, ensure_ascii=False) + '</script>\n')

    return page(f'{a["title"]} - {NAME}', a.get("description") or a.get("excerpt",""),
                cat, p, url, "".join(b),
                sticky_url=a.get("amazon_url"), extra_js=extra_js)

# ============================================================ 一覧・固定ページ
def hero(icon, h1, lead, count=None):
    ic = f'<span class="page-hero-icon" aria-hidden="true">{icon}</span>\n        ' if icon else ""
    c = f'\n        <span class="hero-count">全 {count} 記事</span>' if count is not None else ""
    return f'''      <div class="page-hero">
        {ic}<h1>{e(h1)}</h1>
        <p>{e(lead)}</p>{c}
      </div>
'''

SEARCH_BOX = '''      <form class="searchbox" action="./search.html" method="get" role="search">
        <input type="search" name="q" placeholder="キーワードで記事を探す（例：加湿器、腰痛）" aria-label="サイト内検索">
        <button type="submit">検索</button>
      </form>
'''

def build_index():
    p = "./"
    feat = [a for a in PUBLISHED if a.get("featured")][:3]
    latest = PUBLISHED[:6]
    body = hero("", f"{NAME}へようこそ", SITE["description"])
    if FEAT.get("search"):
        body += SEARCH_BOX
    if feat:
        body += f'''      <section class="section-block" style="margin-top:28px;">
        <h2 class="section-heading">注目の記事</h2>
        <p class="section-sub">まず読んでほしい、実際に使い込んだレビューです</p>
{grid(feat, p)}      </section>
'''
    body += f'''      <section class="section-block">
        <h2 class="section-heading">新着記事</h2>
        <p class="section-sub">ガジェットからデスク環境、生活家電・日用品まで</p>
{grid(latest, p)}      </section>

      <section class="section-block">
        <h2 class="section-heading">カテゴリーから探す</h2>
        <p class="section-sub">目的に近いカテゴリーからどうぞ</p>
        <div class="cat-tiles">
'''
    for c in CATS:
        n = len([a for a in PUBLISHED if a["category"] == c["key"]])
        body += f'''          <a class="cat-tile" href="{p}category-{c["key"]}.html">
            <span class="cat-tile-icon" aria-hidden="true">{c["icon"]}</span>
            <span class="cat-tile-label">{e(c["label"])}</span>
            <span class="cat-tile-count">{n} 記事</span>
          </a>
'''
    body += '''        </div>
      </section>

      <section class="disclosure">
        <h2>当サイトについて</h2>
        <p>当サイトでは、実際に購入・使用したアイテムを中心に、暮らしと作業を快適にするおすすめ商品を紹介しています。掲載しているスペック・価格は執筆時点のものであり、最新の情報は必ず販売ページにてご確認ください。</p>
        <p>Amazonのアソシエイトとして、当サイトは適格販売により収入を得ています。</p>
      </section>
'''
    return page(f"{NAME}｜{TAGLINE}", SITE["description"], "all", p, BASE_URL + "/", body)

def build_category(c):
    p = "./"
    items = [a for a in PUBLISHED if a["category"] == c["key"]]
    body = f'      <div class="breadcrumb"><a href="{p}index.html">ホーム</a><span>›</span>{e(c["label"])}</div>\n'
    body += hero(c["icon"], c["label"] + "の記事", c["lead"], len(items))
    if FEAT.get("search"):
        body += SEARCH_BOX
    body += f'''      <section class="section-block" style="margin-top:24px;">
{grid(items, p)}      </section>
'''
    return page(f'{c["label"]}の記事一覧 - {NAME}',
                c["lead"][:110], c["key"], p,
                f'{BASE_URL}/category-{c["key"]}.html', body)

def build_search():
    p = "./"
    tags = sorted({t for a in PUBLISHED for t in a.get("tags", [])})
    chips = "".join(f'          <button type="button" class="chip" data-tag="{e(t)}">{e(t)}</button>\n'
                    for t in tags)
    catchips = "".join(f'          <button type="button" class="chip" data-cat="{c["key"]}">{c["icon"]} {e(c["label"])}</button>\n'
                       for c in CATS)
    body = f'''      <div class="breadcrumb"><a href="{p}index.html">ホーム</a><span>›</span>サイト内検索</div>
{hero("🔍", "サイト内検索", "キーワードやタグから記事を探せます。すべてブラウザ内で動作するため、入力内容が送信されることはありません。")}
      <div class="search-panel">
        <form class="searchbox" role="search" onsubmit="return false;">
          <input type="search" id="searchInput" placeholder="キーワードを入力（例：加湿器、腰痛、イヤホン）" aria-label="サイト内検索" autocomplete="off">
          <button type="button" id="searchClear">クリア</button>
        </form>

        <div class="chip-group">
          <span class="chip-label">カテゴリー</span>
          <div class="chips" id="catChips">
{catchips}          </div>
        </div>

        <div class="chip-group">
          <span class="chip-label">タグ</span>
          <div class="chips" id="tagChips">
{chips}          </div>
        </div>

        <p class="search-status" id="searchStatus" aria-live="polite"></p>
      </div>

      <section class="section-block" style="margin-top:20px;">
        <div class="card-grid" id="searchResults"></div>
        <p class="empty-state" id="searchEmpty" hidden>該当する記事が見つかりませんでした。キーワードを短くするか、タグの選択を解除してみてください。</p>
      </section>
'''
    return page(f"サイト内検索 - {NAME}", f"{NAME}のサイト内検索。キーワードとタグで記事を絞り込めます。",
                "", p, BASE_URL + "/search.html", body,
                extra_js='<script src="./assets/search.js"></script>\n')

# ============================================================ 固定ページ
def static_pages():
    p = "./"
    today = jp_date(datetime.date.today().isoformat())
    out = []

    privacy = f'''      <h2>個人情報の利用目的</h2>
      <p>当サイトでは、お問い合わせをいただく際に、氏名・メールアドレス等の個人情報をご入力いただく場合があります。取得した個人情報は、お問い合わせに対する回答や必要な情報を電子メールでご連絡する場合にのみ利用し、それ以外の目的では利用いたしません。</p>

      <h2>個人情報の第三者への開示</h2>
      <p>取得した個人情報は適切に管理し、次のいずれかに該当する場合を除き、第三者に開示することはありません。</p>
      <ul>
        <li>本人のご同意がある場合</li>
        <li>法令に基づき開示が必要となる場合</li>
        <li>人の生命・身体または財産の保護のために必要があり、本人の同意を得ることが困難な場合</li>
      </ul>

      <h2>アクセス解析ツールについて</h2>
      <p>当サイトでは、サイトの利用状況を把握するために Google Analytics を利用しています。このツールはトラフィックデータの収集のために Cookie を使用しますが、このデータは匿名で収集されており、個人を特定するものではありません。この機能はブラウザの設定で Cookie を無効にすることで収集を拒否できます。</p>

      <h2>広告の配信について</h2>
      <p>当サイトは、Amazon.co.jpを宣伝しリンクすることによってサイトが紹介料を獲得できる手段を提供することを目的に設定されたアフィリエイトプログラムである、Amazonアソシエイト・プログラムの参加者です。</p>
      <p>第三者配信の広告サービスを利用する場合、広告配信事業者がユーザーの興味に応じた広告を表示するために Cookie を使用することがあります。Cookie を無効にする設定およびパーソナライズ広告の詳細については、各配信事業者のサイトをご確認ください。</p>

      <h2>著作権について</h2>
      <p>当サイトに掲載されている文章・画像等の著作権は、当サイトまたはそれぞれの権利者に帰属します。引用の範囲を超えた無断転載を禁止します。掲載内容に問題がある場合はお問い合わせよりご連絡ください。速やかに対応いたします。</p>

      <h2>免責事項</h2>
      <p>当サイトの掲載内容については、<a href="{p}disclaimer.html">免責事項</a>のページをご確認ください。</p>

      <h2>プライバシーポリシーの変更</h2>
      <p>当サイトは、法令の変更等に応じて本ポリシーの内容を予告なく変更することがあります。変更後のプライバシーポリシーは、当ページに掲載した時点から効力を生じるものとします。</p>

      <p class="updated">最終更新：{today}</p>'''

    disclaimer = f'''      <h2>掲載情報の正確性について</h2>
      <p>当サイトのコンテンツや情報は、可能な限り正確な情報を掲載するよう努めていますが、誤情報が含まれたり、情報が古くなっている場合があります。当サイトに掲載された内容によって生じた損害等について、一切の責任を負いかねますので、あらかじめご了承ください。</p>

      <h2>商品の価格・仕様について</h2>
      <p>記事内に掲載している価格・スペック・在庫状況は、執筆または更新時点のものです。これらは予告なく変更される場合がありますので、購入前に必ず販売ページにて最新の情報をご確認ください。</p>

      <h2>レビュー内容について</h2>
      <p>当サイトのレビューは、運営者が実際に使用した範囲での個人的な感想および評価です。使用環境・体格・好みによって感じ方は異なります。効果や満足度を保証するものではありません。</p>

      <h2>リンク先のコンテンツについて</h2>
      <p>当サイトからリンクやバナーによって他のサイトに移動した場合、移動先サイトで提供される情報・サービス等について一切の責任を負いません。</p>

      <h2>アフィリエイトプログラムについて</h2>
      <p>当サイトは、Amazonアソシエイト・プログラムをはじめとする各種アフィリエイトプログラムに参加しており、商品を紹介することで紹介料を得ています。ただし、紹介料の有無が記事の評価内容に影響を与えることはありません。</p>

      <p class="updated">最終更新：{today}</p>'''

    about = f'''      <h2>サイトの方針</h2>
      <p>{e(NAME)} は、「{e(TAGLINE)}」をコンセプトに、実際に購入・使用したアイテムを紹介するメディアです。ガジェットやPC周辺機器から、デスク環境を整える家具、毎日使う生活家電・日用品まで、ジャンルを限定せずに扱っています。</p>
      <p>読んだ人が「買って後悔した」を減らせることを目的にしているため、良い点だけでなく、気になった点や向いていない人についても必ず記載しています。</p>

      <h2>レビューの基準</h2>
      <dl>
        <dt>実際に使う</dt>
        <dd>原則として自費で購入し、最低2週間以上使用してから記事にしています。</dd>
        <dt>デメリットを書く</dt>
        <dd>気になった点は必ず記載し、可能な限り対処法もあわせて提示します。</dd>
        <dt>比較する</dt>
        <dd>同価格帯の代替候補と並べ、どんな人にどちらが向くかを明示します。</dd>
        <dt>更新する</dt>
        <dd>後継製品の発売や仕様変更があった場合は、記事を更新または追記します。</dd>
      </dl>

      <h2>運営者について</h2>
      <ul>
        <li>サイト名：{e(NAME)}</li>
        <li>運営者：{e(SITE["author"])}</li>
        <li>開設：{e(SITE["founded"])}年</li>
        <li>連絡先：<a href="mailto:{e(SITE["email"])}">{e(SITE["email"])}</a></li>
      </ul>

      <h2>関連ページ</h2>
      <ul>
        <li><a href="{p}privacy.html">プライバシーポリシー</a></li>
        <li><a href="{p}disclaimer.html">免責事項</a></li>
      </ul>

      <p class="updated">最終更新：{today}</p>'''

    for fname, title, desc, content in [
        ("privacy.html", "プライバシーポリシー",
         f"{NAME}のプライバシーポリシー。アクセス解析・広告配信・個人情報の取り扱いについて記載しています。", privacy),
        ("disclaimer.html", "免責事項",
         f"{NAME}の免責事項。掲載情報の正確性、商品情報、リンク先の内容についての責任範囲を記載しています。", disclaimer),
        ("about.html", "運営者情報",
         f"{NAME}の運営者情報。サイトの方針、レビューの基準、お問い合わせ先を記載しています。", about),
    ]:
        body = (f'      <div class="breadcrumb"><a href="{p}index.html">ホーム</a><span>›</span>{e(title)}</div>\n'
                f'      <div class="page-hero"><h1>{e(title)}</h1></div>\n'
                f'      <div class="prose">\n{content}\n      </div>\n')
        out.append((fname, page(f"{title} - {NAME}", desc, "", p,
                                f"{BASE_URL}/{fname}", body)))

    # 404
    body404 = f'''      <div class="page-hero" style="text-align:center;">
        <span class="page-hero-icon" aria-hidden="true">🔍</span>
        <h1>ページが見つかりませんでした</h1>
        <p>お探しのページは移動または削除された可能性があります。<br>下記から目的の記事をお探しください。</p>
      </div>
{SEARCH_BOX}      <div class="cta-wrap"><a class="btn-sub" href="{p}index.html">トップページへ戻る</a></div>
'''
    out.append(("404.html", page(f"ページが見つかりません - {NAME}",
                                 "お探しのページは見つかりませんでした。", "", p,
                                 f"{BASE_URL}/404.html", body404)))

    # お問い合わせフォーム（features.contact_form が true のときだけ生成）
    if FEAT.get("contact_form"):
        endpoint = FEAT.get("contact_form_endpoint", "")
        body = f'''      <div class="breadcrumb"><a href="{p}index.html">ホーム</a><span>›</span>お問い合わせ</div>
      <div class="page-hero"><h1>お問い合わせ</h1>
        <p>記事内容の誤りのご指摘、掲載・レビュー依頼などはこちらからご連絡ください。通常3営業日以内に返信いたします。</p>
      </div>
      <div class="prose">
        <form class="contact-form" action="{e(endpoint)}" method="POST">
          <label for="cf-name">お名前 <span class="req">必須</span></label>
          <input type="text" id="cf-name" name="name" required>

          <label for="cf-email">メールアドレス <span class="req">必須</span></label>
          <input type="email" id="cf-email" name="email" required>

          <label for="cf-subject">件名</label>
          <input type="text" id="cf-subject" name="subject">

          <label for="cf-body">お問い合わせ内容 <span class="req">必須</span></label>
          <textarea id="cf-body" name="message" rows="8" required></textarea>

          <p class="form-note">送信をもって<a href="{p}privacy.html">プライバシーポリシー</a>に同意したものとみなします。</p>
          <button type="submit" class="btn-submit">送信する</button>
        </form>
      </div>
'''
        out.append(("contact.html", page(f"お問い合わせ - {NAME}",
                                         f"{NAME}へのお問い合わせフォームです。", "", p,
                                         f"{BASE_URL}/contact.html", body)))
    return out

# ============================================================ 出力
def write(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    io.open(path, "w", encoding="utf-8").write(content)

def main():
    written = []

    # 記事ページ（下書きは出力しない＆既存ファイルは削除）
    os.makedirs("articles", exist_ok=True)
    keep = set()
    for a in PUBLISHED:
        f = f'articles/{a["slug"]}.html'
        write(f, render_article(a)); written.append(f); keep.add(os.path.basename(f))
    for f in os.listdir("articles"):
        if f.endswith(".html") and f not in keep:
            os.remove("articles/" + f)
            print("  removed (非公開):", f)

    write("index.html", build_index()); written.append("index.html")
    for c in CATS:
        f = f'category-{c["key"]}.html'
        write(f, build_category(c)); written.append(f)
    if FEAT.get("search"):
        write("search.html", build_search()); written.append("search.html")
    for f, c in static_pages():
        write(f, c); written.append(f)

    # contact_form を切ったときに残骸を消す
    if not FEAT.get("contact_form") and os.path.exists("contact.html"):
        os.remove("contact.html"); print("  removed: contact.html")

    # 検索インデックス
    idx = [{"slug": a["slug"], "title": a.get("list_title") or a["title"],
            "excerpt": a.get("excerpt", ""), "desc": a.get("description", ""),
            "cat": a["category"], "catLabel": CAT_LABEL.get(a["category"], ""),
            "icon": a.get("icon", "📦"), "thumb": a.get("thumb", ""),
            "tags": a.get("tags", []), "date": a["date"],
            "url": f'articles/{a["slug"]}.html'} for a in PUBLISHED]
    write("search.json", json.dumps(idx, ensure_ascii=False, separators=(",", ":")))
    written.append("search.json")

    # sitemap / robots / CNAME / .nojekyll
    urls = [(BASE_URL + "/", "1.0")]
    urls += [(f'{BASE_URL}/category-{c["key"]}.html', "0.8") for c in CATS]
    urls += [(f'{BASE_URL}/articles/{a["slug"]}.html', "0.9") for a in PUBLISHED]
    urls += [(f"{BASE_URL}/{f}", "0.3") for f in ("about.html", "privacy.html", "disclaimer.html")]
    today = datetime.date.today().isoformat()
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u, pr in urls:
        sm += f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{today}</lastmod>\n    <priority>{pr}</priority>\n  </url>\n"
    sm += "</urlset>\n"
    write("sitemap.xml", sm); written.append("sitemap.xml")
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /admin.html\n\nSitemap: {BASE_URL}/sitemap.xml\n")
    written.append("robots.txt")
    write("CNAME", SITE["domain"] + "\n"); written.append("CNAME")
    write(".nojekyll", "")

    print(f"\n✅ ビルド完了：{len(written)} ファイル")
    print(f"   公開記事 {len(PUBLISHED)} 本 / 下書き {len(ARTICLES)-len(PUBLISHED)} 本")
    print(f"   ドメイン {SITE['domain']} / GA {'設定済' if GA else '未設定'} / GSC {'設定済' if GSC else '未設定'}")
    print(f"   お問い合わせフォーム: {'ON' if FEAT.get('contact_form') else 'OFF（メールリンクのみ）'}")

if __name__ == "__main__":
    main()
