#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""デザイン更改案（v2）の確認用ページを作る。

本番の build.py には一切触れない。content/ の実データを読んで、
preview/pages/ に新デザインのHTMLを書き出すだけの道具。
preview/ は .gitignore に入れてあるので、デプロイには乗らない。

    python3 tools/build_preview.py

出力：
    preview/index.html        確認用の画面（PC/スマホの枠で並べて見る）
    preview/pages/top.html    トップ
    preview/pages/category.html   カテゴリー一覧
    preview/pages/category-sub.html   カテゴリーの絞り込み（サブ区分）
    preview/pages/article.html    記事
    preview/pages/search.html     サイト内検索
    preview/pages/contact.html    お問い合わせ
    preview/pages/404.html        ページが見つかりません
    preview/pages/about.html      運営者情報
"""

import html
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "preview")
PAGES = os.path.join(OUT, "pages")

SITE = json.load(open(os.path.join(ROOT, "content/site.json"), encoding="utf-8"))
ARTICLES = json.load(open(os.path.join(ROOT, "content/articles.json"), encoding="utf-8"))
PUBLISHED = [a for a in ARTICLES if a.get("published")]
PUBLISHED.sort(key=lambda a: a.get("date", ""), reverse=True)
CATS = SITE["categories"]
NAME = SITE["site_name"]
FOUNDED = SITE.get("founded", "2026")

# ページからサイトルートまでの相対パス（preview/pages/ に置くため2つ上）
R = "../../"


def e(s):
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------------------
# ブランドマーク
# ---------------------------------------------------------------------------
# assets/img/hero-box.webp（開いた箱に MB）の等角図をそのまま図形に起こしたもの。
# 箱の2面・開口部・4枚のフタという写真の構成を保つので、ヒーローの写真と
# 並べても同じものに見える。色は CSS 変数で外から差し替えられるようにして、
# 暗いフッターでは白黒を入れ替える（--mk-body / --mk-flap / --mk-line / --mk-letter）。
LOGO_MARK = '''<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
<g fill="var(--mk-flap,#ffffff)" stroke="var(--mk-line,#111111)" stroke-width="0.9" stroke-linejoin="round"><path d="M9 22 L24 31 L15.6 32.8 L0.6 23.8 Z"/>
    <path d="M24 31 L39 22 L47.4 23.8 L32.4 32.8 Z"/></g>
  <path d="M24 13 L39 22 L24 31 L9 22 Z" fill="var(--mk-inner,#ffffff)" stroke="var(--mk-line,#111111)" stroke-width="0.9" stroke-linejoin="round"/>
  <path d="M24 22.5 L31 26.5 L24 30.5 L17 26.5 Z" fill="var(--mk-inner2,#1b1b1b)"/>
  <g fill="var(--mk-flap,#ffffff)" stroke="var(--mk-line,#111111)" stroke-width="0.9" stroke-linejoin="round"><path d="M9 22 L24 13 L21.5 2.5 L6.5 10.5 Z"/>
    <path d="M24 13 L39 22 L41.5 10.5 L26.5 2.5 Z"/></g>
  <path d="M9 22 L24 31 L24 44.5 L9 35.5 Z" fill="var(--mk-body,#111111)"/>
  <path d="M24 31 L39 22 L39 35.5 L24 44.5 Z" fill="var(--mk-body,#111111)"/>
  <g fill="var(--mk-letter,#ffffff)" font-family="Helvetica Neue,Arial,sans-serif"
     font-size="11" font-weight="700" text-anchor="middle" dominant-baseline="central">
    <text x="16.5" y="23.6" transform="matrix(1,0.6,0,1,0,0)">M</text>
    <text x="31.5" y="52.4" transform="matrix(1,-0.6,0,1,0,0)">B</text>
  </g>
</svg>'''

IC_SEARCH = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
             'stroke-linecap="round"><circle cx="10.8" cy="10.8" r="7.2"/>'
             '<path d="M16.2 16.2 L21 21"/></svg>')

# ヒーローの3つの特長に置くアイコン。線の太さをそろえて図面の記号に見せる
IC_VOICE = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
            'stroke-linejoin="round" stroke-linecap="round">'
            '<path d="M3.5 5.5h17v11h-9.5L6.5 20.5V16.5h-3z"/>'
            '<path d="M8 9.5h8M8 12.6h5.5"/></svg>')
IC_ZOOM = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
           'stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.8"/>'
           '<path d="M15.4 15.4 L21 21M7.6 10.5h5.8M10.5 7.6v5.8"/></svg>')
IC_CHECK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.4 L10 17.2 L19.4 6.8"/></svg>')

# ヒーローの背景に敷く設計図の線。写真の周りに置くので、線は極細にする
HERO_DECO = '''<svg class="hero-deco" viewBox="0 0 1440 760" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
  <defs>
    <pattern id="dots" width="9" height="9" patternUnits="userSpaceOnUse">
      <circle cx="1.1" cy="1.1" r="1.1" fill="#c9c9c4"/>
    </pattern>
  </defs>
  <g stroke="#dcdcd8" stroke-width="1" fill="none">
    <path d="M470 0 V760"/>
    <path d="M1150 60 V700"/>
    <path d="M0 118 H1440"/>
    <path d="M0 645 H1440"/>
  </g>
  <g stroke="#d3d3ce" stroke-width="1" fill="none" opacity=".85">
    <circle cx="612" cy="300" r="118"/>
    <circle cx="612" cy="300" r="72" stroke-dasharray="3 5"/>
  </g>
  <g stroke="#b9b9b3" stroke-width="1.1" stroke-linecap="round">
    <path d="M525 148 h18 M534 139 v18"/>
    <path d="M690 132 h18 M699 123 v18"/>
    <path d="M1112 470 h16 M1120 462 v16"/>
    <path d="M905 690 h16 M913 682 v16"/>
  </g>
  <rect x="1195" y="196" width="82" height="46" fill="url(#dots)" opacity=".9"/>
  <rect x="382" y="556" width="58" height="34" fill="url(#dots)" opacity=".7"/>
  <g stroke="#d8d8d3" stroke-width="1" stroke-dasharray="2 6" fill="none">
    <path d="M700 0 V760"/>
    <path d="M0 392 H1440"/>
  </g>
</svg>'''

NAV = [
    ("HOME", "ホーム", "top.html"),
    ("CATEGORY", "カテゴリー", "category.html"),
    ("ABOUT", "モノベースについて", "about.html"),
    ("POLICY", "運営方針", "editorial-policy.html"),
    ("CONTACT", "お問い合わせ", "contact.html"),
]

# スマホの引き出しは現行サイトの項目をそのまま残す（ご指定）
DRAWER = [
    ("ホーム", "HOME", "top.html"),
    ("サイトマップ", "SITEMAP", "sitemap.html"),
    ("運営者情報", "ABOUT", "about.html"),
    ("記事作成方針", "POLICY", "editorial-policy.html"),
    ("広告掲載について", "ADVERTISING", "advertising.html"),
    ("お問い合わせ", "CONTACT", "contact.html"),
]


def nav_item(en, ja, href, current):
    cur = ' aria-current="page"' if current == en else ""
    menu = ""
    if en == "CATEGORY":
        cells = "".join(
            f'<a href="category.html"><span class="nav-en" style="font-size:12px;letter-spacing:.02em">'
            f'{e(c["label"])}</span></a>' for c in CATS)
        menu = f'<div class="nav-menu">{cells}</div>'
    cls = ' class="nav-has-menu"' if menu else ""
    return (f'<li{cls}><a href="{href}"{cur}>'
            f'<span class="nav-en">{en}</span><span class="nav-ja">{e(ja)}</span></a>{menu}</li>')


def header(current="HOME"):
    nav = "".join(nav_item(en, ja, href, current) for en, ja, href in NAV)
    drawer = "".join(
        f'<li><a href="{href}"><span>{e(ja)}</span><span>{en}</span></a></li>'
        for ja, en, href in DRAWER)
    cats = "".join(
        f'<li><a href="category.html"><span>{e(c["label"])}</span></a></li>' for c in CATS)
    return f'''<header class="v2-header">
  <div class="container header-inner">
    <a class="brand" href="top.html" aria-label="{e(NAME)}">
      <span class="brand-mark">{LOGO_MARK}</span>
      <span class="brand-text">
        <span class="brand-ja">{e(NAME)}</span>
        <span class="brand-en">MONOBASE</span>
      </span>
    </a>
    <nav class="v2-nav" aria-label="メニュー"><ul>{nav}</ul></nav>
    <span class="header-rule" aria-hidden="true"></span>
    <a class="header-search" href="search.html" aria-label="サイト内を検索">{IC_SEARCH}</a>
    <button class="nav-toggle" id="navToggle" aria-expanded="false" aria-controls="drawer" aria-label="メニューを開く">
      <span></span><span></span><span></span>
    </button>
  </div>
  <div class="drawer" id="drawer" data-open="false">
    <div class="container" style="padding:0">
      <ul class="drawer-main">{drawer}</ul>
      <p class="drawer-head">CATEGORY</p>
      <ul class="drawer-cats">{cats}</ul>
    </div>
  </div>
</header>'''


def footer():
    return f'''<footer class="v2-footer">
  <div class="container">
    <div class="footer-top">
      <div>
        <div class="brand" style="gap:11px">
          <span class="brand-mark">{LOGO_MARK}</span>
          <span class="brand-text">
            <span class="brand-ja">{e(NAME)}</span>
            <span class="brand-en">MONOBASE</span>
          </span>
        </div>
        <p class="footer-desc">{e(SITE["description"])}</p>
      </div>
      <div class="footer-cols">
        <div class="footer-col">
          <h3>ABOUT</h3>
          <ul>
            <li><a href="about.html">運営者情報</a></li>
            <li><a href="editorial-policy.html">記事作成方針</a></li>
            <li><a href="advertising.html">広告掲載について</a></li>
            <li><a href="sitemap.html">サイトマップ</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h3>SUPPORT</h3>
          <ul>
            <li><a href="contact.html">お問い合わせ</a></li>
            <li><a href="privacy.html">プライバシーポリシー</a></li>
            <li><a href="disclaimer.html">免責事項</a></li>
          </ul>
        </div>
      </div>
    </div>
    <div class="footer-bottom">
      <p>当サイトは Amazon アソシエイト・プログラムの参加者です。適格販売により収入を得ています。</p>
      <p>&copy; {FOUNDED} {e(NAME)}</p>
    </div>
  </div>
</footer>'''


DRAWER_JS = '''<script>
(function(){
  var b=document.getElementById('navToggle'), d=document.getElementById('drawer');
  if(!b||!d) return;
  b.addEventListener('click',function(){
    var open = b.getAttribute('aria-expanded')==='true';
    b.setAttribute('aria-expanded', String(!open));
    d.setAttribute('data-open', String(!open));
    document.body.style.overflow = !open ? 'hidden' : '';
  });
})();
</script>'''


def page(title, body, current="HOME"):
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{e(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;800;900&display=swap">
<link rel="stylesheet" href="{R}assets/style-v2.css">
</head>
<body>
{header(current)}
{body}
{footer()}
{DRAWER_JS}
</body>
</html>'''


# ---------------------------------------------------------------------------
# 部品
# ---------------------------------------------------------------------------
def sec_head(en, ja):
    return (f'<div class="sec-head"><span class="rule"></span>'
            f'<span class="titles"><span class="en">{en}</span><br>'
            f'<span class="ja">{e(ja)}</span></span><span class="rule"></span></div>')


def sec_more(href, label="VIEW ALL"):
    """一覧へ送る導線は、見出しの横ではなくタイルの下の中央に置く。
       スマホでは6件目をわざと切って、その続きがここにあることを示す。"""
    return f'<div class="sec-more"><a href="{href}">{label}</a></div>'


def cat_label(key):
    for c in CATS:
        if c["key"] == key:
            return c["label"]
    return key


def cat_image(c):
    """カテゴリー枠の写真。site.json の image に入れた1枚を固定で出す。
       まだ決めていないカテゴリーは、そのカテゴリーの最新記事の写真で代用する
       （枠だけ空くと、写真のあるカテゴリーだけが強く見えてしまうため）。"""
    src = (c.get("image") or "").strip()
    fixed = bool(src)
    if not src:
        src = next((a.get("thumb") for a in PUBLISHED
                    if a.get("category") == c["key"] and a.get("thumb")), "")
    if not src:
        return ""
    note = "" if fixed else ' data-fallback="1"'
    return f'<img src="{R}{e(src)}" alt="" loading="lazy"{note}>'


def card(a):
    thumb = a.get("thumb") or ""
    img = (f'<img src="{R}{e(thumb)}" alt="" loading="lazy">' if thumb else "")
    return (f'<a class="card" href="{article_href(a)}">'
            f'<span class="card-thumb">{img}</span>'
            f'<span class="card-date">{e(a.get("date",""))}</span>'
            f'<span class="card-title">{e(a.get("list_title") or a.get("title",""))}</span>'
            f'<span class="card-cat">{e(cat_label(a.get("category","")))}</span></a>')


def row(a):
    thumb = a.get("thumb") or ""
    img = (f'<img src="{R}{e(thumb)}" alt="" loading="lazy">' if thumb else "")
    return (f'<a class="row-item" href="{article_href(a)}">'
            f'<span class="thumb">{img}</span>'
            f'<span><h3>{e(a.get("title",""))}</h3>'
            f'<p>{e(a.get("excerpt",""))}</p>'
            f'<span class="meta">{e(a.get("date",""))}　/　{e(cat_label(a.get("category","")))}</span>'
            f'</span></a>')


def marker(text):
    """本文の ==語== を蛍光ペンに変える。"""
    return re.sub(r"==(.+?)==", r"<mark>\1</mark>", e(text))


def paras(value):
    """lead / summary / conclusion は、記事によって文字列だったり配列だったりする。
       どちらで来ても <p> の並びに開く（配列を str() すると
       ['…', '…'] がそのまま画面に出てしまうため）。"""
    if not value:
        return ""
    items = value if isinstance(value, list) else [value]
    return "".join(f"<p>{marker(x)}</p>" for x in items if x)


# ---------------------------------------------------------------------------
# トップ
# ---------------------------------------------------------------------------
def build_top():
    # 新着を先に出すので、ピックアップは新着と重ならないものから選ぶ。
    # featured が4本に満たないときは、残りの記事で埋めて枠を欠けさせない
    # スマホは6件目をわざと切って「続きがある」ことを示すので、6本ずつ渡す。
    # PCは4列なので、5本目から先は CSS で隠している
    latest = PUBLISHED[:6]
    picks = [a for a in PUBLISHED if a.get("featured") and a not in latest]
    for a in PUBLISHED:
        if len(picks) >= 6:
            break
        if a not in picks and a not in latest:
            picks.append(a)
    picks = picks[:6]

    # 3つ目の「購入判断をサポート」はスマホの3列だと2行に割れて崩れるので、
    # 横に詰めたとき用の短い言い方を別に持たせる
    points = [
        (IC_VOICE, "口コミを分析", "口コミを分析", "良い点も悪い点も<br>包み隠さず紹介"),
        (IC_ZOOM, "徹底調査", "徹底調査", "仕様・価格・競合まで<br>多角的に比較"),
        (IC_CHECK, "購入判断をサポート", "購入を判断", "向いている人・向いていない人を<br>明確に整理"),
    ]
    pt = "".join(
        f'<div class="hero-point"><span class="ic">{ic}</span>'
        f'<div><h3><span class="wide">{t}</span><span class="narrow">{sh}</span></h3>'
        f'<p>{d}</p></div></div>' for ic, t, sh, d in points)

    counts = {c["key"]: len([a for a in PUBLISHED if a.get("category") == c["key"]]) for c in CATS}
    cells = "".join(
        f'<a class="cat-cell" href="category.html">'
        f'<span class="cat-thumb">{cat_image(c)}</span>'
        f'<span class="cat-body">'
        f'<span class="n">{i+1:02d}</span>'
        f'<span class="l">{e(c["label"])}</span>'
        f'<span class="c">{counts[c["key"]]} 記事</span></span></a>'
        for i, c in enumerate(CATS))

    body = f'''<section class="hero">
  {HERO_DECO}
  <div class="container">
    <div class="hero-mark">
      <div class="num">01</div>
      <div class="txt">MONOBASE</div>
      <div class="txt">SINCE {FOUNDED}</div>
      <div class="bar"></div>
    </div>
    <div class="hero-inner">
      <div class="hero-copy">
        <h1 class="hero-title"><span class="tw">良い点も、不満点も。</span></h1>
        <p class="hero-sub">買う前に「リアル」が見える<br>商品紹介サイト</p>
        <div class="hero-rule"></div>
        <p class="hero-desc">口コミ・仕様・価格を徹底的に調査し、<br>購入判断に必要な情報を整理してお届けします。</p>
      </div>
      <figure class="hero-figure">
        <img src="{R}assets/img/hero-box.webp" alt="モノベースの箱" width="314" height="314">
      </figure>
      <div class="hero-points">{pt}</div>
    </div>
  </div>
</section>

<section class="v2-section is-tinted">
  <div class="container">
    {sec_head("NEW", "新着記事")}
    <div class="card-grid">{"".join(card(a) for a in latest)}</div>
    {sec_more("category.html")}
  </div>
</section>

<section class="v2-section">
  <div class="container">
    {sec_head("PICK UP", "ピックアップ記事")}
    <div class="card-grid">{"".join(card(a) for a in picks)}</div>
    {sec_more("category.html")}
  </div>
</section>

<section class="v2-section">
  <div class="container">
    {sec_head("CATEGORY", "カテゴリーから探す")}
    <div class="cat-grid">{cells}</div>
    {sec_more("category.html")}
  </div>
</section>

<section class="v2-section">
  <div class="container">
    {sec_head("RANKING", "よく読まれている記事")}
    <div class="row-list is-narrow">{"".join(row(a) for a in PUBLISHED[:5])}</div>
    {sec_more("category.html")}
  </div>
</section>
'''
    return page(f'{NAME}｜{SITE["tagline"]}', body, "HOME")


# ---------------------------------------------------------------------------
# カテゴリー一覧
# ---------------------------------------------------------------------------
def _cat_of(key):
    return next((c for c in CATS if c["key"] == key), None)


def _sub_counts(c):
    """カテゴリー内のサブ区分を、記事のあるものだけ件数つきで返す。"""
    out = []
    for sc in c.get("sub", []):
        n = len([a for a in PUBLISHED
                 if a.get("category") == c["key"] and a.get("sub") == sc["key"]])
        if n:
            out.append((sc, n))
    return out


def sub_nav(c, current_sub=""):
    """カテゴリー一覧の絞り込み。件数0のサブ区分は出さない（押しても空になるため）。
       色は使わず、選択中だけ地を反転させて示す。"""
    subs = _sub_counts(c)
    if not subs:
        return ""
    all_cls = " is-on" if not current_sub else ""
    items = [f'<a class="sub-chip{all_cls}" href="category.html">すべて'
             f'<span class="n">{len([a for a in PUBLISHED if a.get("category") == c["key"]])}</span></a>']
    for sc, n in subs:
        on = " is-on" if current_sub == sc["key"] else ""
        items.append(f'<a class="sub-chip{on}" href="category-sub.html">{e(sc["label"])}'
                     f'<span class="n">{n}</span></a>')
    return ('<div class="sub-nav"><span class="sub-nav-label">絞り込み</span>'
            f'<div class="sub-chips">{"".join(items)}</div></div>')


def build_category():
    # 記事が一番多いカテゴリーを見本にする
    c = max(CATS, key=lambda x: len([a for a in PUBLISHED if a.get("category") == x["key"]]))
    items = [a for a in PUBLISHED if a.get("category") == c["key"]]
    body = f'''<div class="page-head">
  <div class="container">
    <p class="crumbs"><a href="top.html">ホーム</a><span>/</span>{e(c["label"])}</p>
    <h1>{e(c["label"])}の記事</h1>
    <p class="lead">{e(c["lead"])}</p>
    <p class="count">{len(items)} ARTICLES</p>
    {sub_nav(c)}
  </div>
</div>
<div class="container">
  <div class="v2-section" style="padding:40px 0 80px">
    <div class="row-list">{"".join(row(a) for a in items)}</div>
  </div>
</div>'''
    return page(f'{c["label"]}の記事一覧 - {NAME}', body, "CATEGORY")


# ---------------------------------------------------------------------------
# カテゴリーの絞り込み（サブ区分）
# ---------------------------------------------------------------------------
def build_subcategory():
    """サブ区分で絞った一覧。見本として、記事のあるサブ区分のうち一番多いものを出す。"""
    best = None
    for c in CATS:
        for sc, n in _sub_counts(c):
            if best is None or n > best[2]:
                best = (c, sc, n)
    if best is None:                      # サブ区分に記事が1本もない場合の逃げ道
        return build_category()
    c, sc, _ = best
    items = [a for a in PUBLISHED
             if a.get("category") == c["key"] and a.get("sub") == sc["key"]]
    body = f'''<div class="page-head">
  <div class="container">
    <p class="crumbs"><a href="top.html">ホーム</a><span>/</span>
      <a href="category.html">{e(c["label"])}</a><span>/</span>{e(sc["label"])}</p>
    <h1>{e(sc["label"])}</h1>
    <p class="lead">{e(c["label"])}のうち、{e(sc["label"])}に分類した記事です。</p>
    <p class="count">{len(items)} ARTICLES</p>
    {sub_nav(c, sc["key"])}
  </div>
</div>
<div class="container">
  <div class="v2-section" style="padding:40px 0 80px">
    <div class="row-list">{"".join(row(a) for a in items)}</div>
  </div>
</div>'''
    return page(f'{sc["label"]}の記事一覧 - {NAME}', body, "CATEGORY")


# ---------------------------------------------------------------------------
# 記事
# ---------------------------------------------------------------------------
def article_href(a):
    """プレビューでも記事ごとに別のページへ飛ばす。
       1枚の見本に全部つないでいると、押しても同じ記事しか出ず、
       並びや導線を確かめられないため。"""
    return f'article-{e(a.get("slug") or "sample")}.html'


def build_article(a=None):
    if a is None:
        a = next((x for x in PUBLISHED if x.get("sections") and x.get("faq")), PUBLISHED[0])
    secs = a.get("sections") or []

    toc = "".join(f'<li><a href="#s{i}">{e(s["heading"])}</a></li>' for i, s in enumerate(secs))

    prose = paras(a.get("lead") or a.get("summary"))
    for i, s in enumerate(secs):
        prose += f'<h2 id="s{i}">{e(s["heading"])}</h2>'
        for p in s.get("paras", []):
            prose += f'<p>{marker(p)}</p>'
        if s.get("point"):
            prose += ('<div class="point-box"><p class="lb">POINT</p>'
                      f'<p>{marker(s["point"])}</p></div>')

    pros = "".join(f"<li>{marker(x)}</li>" for x in a.get("pros", []))
    cons = "".join(f"<li>{marker(x)}</li>" for x in a.get("cons", []))
    pc = ""
    if pros or cons:
        pc = (f'<div class="pc-grid">'
              f'<div class="pc-col"><h3>GOOD POINTS</h3><ul>{pros}</ul></div>'
              f'<div class="pc-col is-con"><h3>WEAK POINTS</h3><ul>{cons}</ul></div></div>')

    faq = ""
    if a.get("faq"):
        rows = "".join(
            f'<div class="faq-item"><div class="q">{e(f["q"])}</div>'
            f'<div class="a">{marker(f["a"])}</div></div>' for f in a["faq"])
        faq = f'<h2>よくある質問</h2><div class="faq-list">{rows}</div>'

    side_items = "".join(
        f'<li><a href="{article_href(x)}"><span class="th">'
        + (f'<img src="{R}{e(x.get("thumb",""))}" alt="" loading="lazy">' if x.get("thumb") else "")
        + f'</span><span class="tt">{e(x.get("list_title") or x.get("title",""))}</span></a></li>'
        for x in PUBLISHED[:5])

    conclusion = ""
    if a.get("conclusion"):
        conclusion = (f'<h2>{e(a.get("conclusion_title") or "まとめ")}</h2>'
                      + paras(a["conclusion"]))

    thumb = a.get("thumb") or ""
    hero_img = (f'<div class="article-hero"><img src="{R}{e(thumb)}" alt=""></div>' if thumb else "")

    body = f'''<div class="container">
  <div class="article-wrap">
    <article>
      <div class="article-head">
        <p class="crumbs"><a href="top.html">ホーム</a><span>/</span>'''\
        f'''<a href="category.html">{e(cat_label(a.get("category","")))}</a></p>
        <h1>{e(a.get("title",""))}</h1>
        <div class="meta"><span>PUBLISHED {e(a.get("date",""))}</span>'''\
        f'''<span>UPDATED {e(a.get("updated") or a.get("date",""))}</span></div>
      </div>
      {hero_img}
      <nav class="toc"><h2>CONTENTS</h2><ol>{toc}</ol></nav>
      <div class="prose">
        {prose}
        <h2>良い点と、気になる点</h2>
        {pc}
        {conclusion}
        {faq}
      </div>
      <div class="cta">
        <p class="lb">SPONSORED LINK</p>
        <h3>{e(a.get("cta_label") or "この商品をAmazonで見る")}</h3>
        <a class="btn-amazon" href="#" rel="nofollow sponsored noopener">Amazonで商品の詳細を見る</a>
        <p class="note">当サイトはAmazonアソシエイト・プログラムの参加者です。<br>
          リンクから購入があった場合、当サイトに収益が発生することがあります。</p>
      </div>
    </article>
    <aside class="side">
      <div class="side-block">
        <h2>SEARCH</h2>
        <form class="side-search" onsubmit="return false">
          <input type="search" placeholder="キーワードで探す" aria-label="サイト内を検索">
          <button type="submit" aria-label="検索">{IC_SEARCH}</button>
        </form>
      </div>
      <div class="side-block">
        <h2>LATEST</h2>
        <ul class="side-list">{side_items}</ul>
      </div>
    </aside>
  </div>
</div>'''
    return page(f'{a.get("title","")} - {NAME}', body, "CATEGORY")


# ---------------------------------------------------------------------------
# 運営者情報
# ---------------------------------------------------------------------------
def build_about():
    body = f'''<div class="page-head">
  <div class="container">
    <p class="crumbs"><a href="top.html">ホーム</a><span>/</span>運営者情報</p>
    <h1>モノベースについて</h1>
    <p class="lead">{e(SITE["description"])}</p>
  </div>
</div>
<div class="container">
  <div class="static-wrap">
    <h2>このサイトの立ち位置</h2>
    <p>モノベースは、利用者の声とメーカー公式仕様を突き合わせて、<mark>良い点だけでなく「向かない人」まで書く</mark>ことを方針にした商品紹介サイトです。売れている順に並べるのではなく、どんな条件のときに困るのかを先に示します。</p>
    <p>記事は、公式が公開している仕様（型番・寸法・消費電力など）と、販売サイトの利用者の声から読み取れる傾向を、別のものとして扱います。裏の取れていない数値は載せません。</p>

    <h2>運営情報</h2>
    <dl>
      <div><dt>サイト名</dt><dd>{e(NAME)}</dd></div>
      <div><dt>運営者</dt><dd>{e(SITE.get("author",""))}</dd></div>
      <div><dt>開設</dt><dd>{e(FOUNDED)}年</dd></div>
      <div><dt>連絡先</dt><dd>{e(SITE.get("email",""))}</dd></div>
      <div><dt>ドメイン</dt><dd>{e(SITE.get("domain",""))}</dd></div>
    </dl>

    <h2>広告について</h2>
    <p>当サイトは Amazon アソシエイト・プログラムをはじめとする各種アフィリエイトプログラムに参加しています。リンク経由で購入があった場合、当サイトに紹介料が発生することがあります。紹介料の有無で評価の書き方は変えません。</p>
  </div>
</div>'''
    return page(f"モノベースについて - {NAME}", body, "ABOUT")


# ---------------------------------------------------------------------------
# サイト内検索
# ---------------------------------------------------------------------------
# 本番と同じく、検索はすべてブラウザの中で完結させる（入力は外に送らない）。
# プレビューでも実際に絞り込めるよう、記事の索引をページに埋め込んでおく。
def build_search():
    tags = sorted({t for a in PUBLISHED for t in a.get("tags", [])})
    index = [{
        "t": a.get("title", ""),
        "x": a.get("excerpt", ""),
        "c": a.get("category", ""),
        "cl": cat_label(a.get("category", "")),
        "d": a.get("date", ""),
        "th": a.get("thumb", ""),
        "tg": a.get("tags", []),
        "u": article_href(a),
    } for a in PUBLISHED]

    catchips = "".join(
        f'<button type="button" class="chip" data-cat="{e(c["key"])}">{e(c["label"])}</button>'
        for c in CATS)
    tagchips = "".join(
        f'<button type="button" class="chip" data-tag="{e(t)}">{e(t)}</button>' for t in tags)

    body = f'''<div class="page-head">
  <div class="container">
    <p class="crumbs"><a href="top.html">ホーム</a><span>/</span>サイト内検索</p>
    <h1>サイト内検索</h1>
    <p class="lead">キーワード・カテゴリー・タグから記事を探せます。検索はすべてブラウザの中で動くので、入力した内容が送信されることはありません。</p>
  </div>
</div>
<div class="container">
  <div class="search-panel">
    <form class="search-field" role="search" onsubmit="return false;">
      <span class="ic" aria-hidden="true">{IC_SEARCH}</span>
      <input type="search" id="q" placeholder="キーワードを入力（例：モニター、静音、充電器）" aria-label="サイト内検索" autocomplete="off">
      <button type="button" id="clear">クリア</button>
    </form>

    <div class="chip-group">
      <p class="chip-label en-label">CATEGORY</p>
      <div class="chips" id="catChips">{catchips}</div>
    </div>

    <div class="chip-group">
      <p class="chip-label en-label">TAG</p>
      <div class="chips is-scroll" id="tagChips">{tagchips}</div>
    </div>
  </div>

  <div class="v2-section" style="padding:36px 0 80px">
    <p class="result-count" id="count"></p>
    <div class="row-list" id="results"></div>
    <p class="empty-state" id="empty" hidden>該当する記事が見つかりませんでした。<br>
      キーワードを短くするか、カテゴリー・タグの選択を外してみてください。</p>
  </div>
</div>

<script>
const IDX = {json.dumps(index, ensure_ascii=False)};
const RT = "{R}";
const q = document.getElementById('q');
let cat = "", tag = "";

function esc(s){{ return String(s).replace(/[&<>"]/g, function(c){{
  return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]; }}); }}

function render(){{
  const k = q.value.trim().toLowerCase();
  const hit = IDX.filter(function(a){{
    return (!cat || a.c === cat)
        && (!tag || a.tg.indexOf(tag) >= 0)
        && (!k || (a.t + ' ' + a.x + ' ' + a.cl + ' ' + a.tg.join(' ')).toLowerCase().indexOf(k) >= 0);
  }});

  document.getElementById('count').textContent = hit.length + ' ARTICLES';
  document.getElementById('empty').hidden = hit.length > 0;
  document.getElementById('results').innerHTML = hit.map(function(a){{
    return '<a class="row-item" href="' + esc(a.u) + '">'
      + '<span class="thumb">' + (a.th ? '<img src="' + RT + esc(a.th) + '" alt="" loading="lazy">' : '') + '</span>'
      + '<span><h3>' + esc(a.t) + '</h3><p>' + esc(a.x) + '</p>'
      + '<span class="meta">' + esc(a.d) + '　/　' + esc(a.cl) + '</span></span>'
      + '</a>';
  }}).join('');
}}

// カテゴリーとタグは1つずつ。同じものをもう一度押すと解除する
function pick(box, attr, set){{
  box.addEventListener('click', function(ev){{
    const b = ev.target.closest('.chip');
    if (!b) return;
    const v = b.dataset[attr];
    const on = b.classList.contains('is-on');
    box.querySelectorAll('.chip').forEach(function(x){{ x.classList.remove('is-on'); }});
    if (!on) b.classList.add('is-on');
    set(on ? "" : v);
    render();
  }});
}}
pick(document.getElementById('catChips'), 'cat', function(v){{ cat = v; }});
pick(document.getElementById('tagChips'), 'tag', function(v){{ tag = v; }});

q.addEventListener('input', render);
document.getElementById('clear').addEventListener('click', function(){{
  q.value = ""; cat = ""; tag = "";
  document.querySelectorAll('.chip').forEach(function(x){{ x.classList.remove('is-on'); }});
  render(); q.focus();
}});
render();
</script>'''
    return page(f"サイト内検索 - {NAME}", body, "")


# ---------------------------------------------------------------------------
# お問い合わせ
# ---------------------------------------------------------------------------
def build_contact():
    body = f'''<div class="page-head">
  <div class="container">
    <p class="crumbs"><a href="top.html">ホーム</a><span>/</span>お問い合わせ</p>
    <h1>お問い合わせ</h1>
    <p class="lead">記事内容の誤りのご指摘、掲載・レビューのご依頼、その他のご連絡はこちらからお願いします。内容を確認のうえ、通常3営業日以内にご返信します。</p>
  </div>
</div>
<div class="container">
  <div class="contact-wrap">
    <form class="v2-form" onsubmit="return false;" novalidate>
      <div class="field">
        <label for="cf-topic">ご用件</label>
        <select id="cf-topic" name="topic">
          <option>記事内容についてのご指摘・ご質問</option>
          <option>掲載・レビューのご依頼</option>
          <option>取材・執筆のご依頼</option>
          <option>広告・提携について</option>
          <option>その他</option>
        </select>
      </div>
      <div class="field">
        <label for="cf-name">お名前 <span class="req">必須</span></label>
        <input type="text" id="cf-name" name="name" maxlength="80" placeholder="山田 太郎" required>
      </div>
      <div class="field">
        <label for="cf-email">メールアドレス <span class="req">必須</span></label>
        <input type="email" id="cf-email" name="email" maxlength="120" placeholder="you@example.com" required>
        <p class="hint">ご返信先です。お間違いのないようご確認ください。</p>
      </div>
      <div class="field">
        <label for="cf-url">該当ページのURL</label>
        <input type="url" id="cf-url" name="page_url" maxlength="300"
               placeholder="https://{e(SITE.get("domain",""))}/articles/…">
        <p class="hint">記事へのご指摘の場合にご記入ください。</p>
      </div>
      <div class="field">
        <label for="cf-body">お問い合わせ内容 <span class="req">必須</span></label>
        <textarea id="cf-body" rows="9" maxlength="2000"
                  placeholder="お問い合わせの内容をご記入ください。" required></textarea>
        <p class="hint is-count"><span id="cf-count">0</span> / 2000 文字</p>
      </div>
      <p class="form-note">送信をもって<a href="privacy.html">プライバシーポリシー</a>に同意いただいたものとみなします。いただいた個人情報は、ご返信の目的以外には利用しません。</p>
      <button type="submit" class="btn-solid">送信する</button>
    </form>

    <aside class="contact-side">
      <div class="side-tile">
        <p class="side-heading">広告の掲載について</p>
        <p>メーカー・販売店の方からの掲載・レビューのご依頼を歓迎します。受け付けている内容や当サイトの方針は、下記のページにまとめています。</p>
        <p class="tile-cta"><a class="btn-line" href="advertising.html">広告掲載について見る</a></p>
      </div>
      <div class="side-tile">
        <p class="side-heading">お答えできないこと</p>
        <ul class="tile-list">
          <li>個別の商品購入・返品に関するお問い合わせ（Amazonカスタマーサービスへご連絡ください）</li>
          <li>製品の故障・修理に関するご相談（メーカーの窓口をご利用ください）</li>
          <li>掲載を確約するご依頼</li>
        </ul>
      </div>
    </aside>
  </div>
</div>

<script>
(function(){{
  var t = document.getElementById('cf-body'), n = document.getElementById('cf-count');
  if (t && n) t.addEventListener('input', function(){{ n.textContent = t.value.length; }});
}})();
</script>'''
    return page(f"お問い合わせ - {NAME}", body, "CONTACT")


# ---------------------------------------------------------------------------
# 404
# ---------------------------------------------------------------------------
def build_404():
    # 記事のないカテゴリーは出さない。行き止まりから空の一覧へ送っても仕方がない
    counted = [(c, len([a for a in PUBLISHED if a.get("category") == c["key"]])) for c in CATS]
    cats = "".join(
        f'<a class="nf-cat" href="category.html"><span class="l">{e(c["label"])}</span>'
        f'<span class="n">{n}</span></a>' for c, n in counted if n)
    latest = "".join(card(a) for a in PUBLISHED[:4])
    body = f'''<div class="notfound">
  <div class="container">
    <p class="nf-code en-label">404 / NOT FOUND</p>
    <h1>ページが見つかりませんでした</h1>
    <p class="nf-lead">お探しのページは移動または削除された可能性があります。<br>
      キーワードで探すか、下のカテゴリーからお進みください。</p>
    <form class="search-field is-center" role="search" onsubmit="return false;">
      <span class="ic" aria-hidden="true">{IC_SEARCH}</span>
      <input type="search" placeholder="キーワードを入力" aria-label="サイト内検索">
      <button type="button" onclick="location.href='search.html'">検索</button>
    </form>
    <p class="nf-back"><a class="btn-line" href="top.html">トップページへ戻る</a></p>
  </div>
</div>
<div class="container">
  <div class="v2-section" style="padding:56px 0 0">
    {sec_head("CATEGORY", "カテゴリーから探す")}
    <div class="nf-cats">{cats}</div>
  </div>
  <div class="v2-section" style="padding:56px 0 88px">
    {sec_head("NEW", "新着記事")}
    <div class="card-grid">{latest}</div>
    {sec_more("category.html")}
  </div>
</div>'''
    return page(f"ページが見つかりません - {NAME}", body, "")


# ---------------------------------------------------------------------------
# 固定ページ（プライバシー・免責・広告掲載・記事作成方針）
# ---------------------------------------------------------------------------
# 本番の HTML から見出しと本文だけを取り出して、新デザインの器に入れ直す。
# 文面を書き写すと本番と食い違うので、置き場所は1つに保つ。
STATIC_PAGES = [
    ("privacy.html", "プライバシーポリシー"),
    ("disclaimer.html", "免責事項"),
    ("advertising.html", "広告掲載について"),
    ("editorial-policy.html", "記事作成方針"),
]

# 本文の中のリンクを、プレビューの中で開けるものに向け直す
LINK_MAP = {
    "./index.html": "top.html",
    "./search.html": "search.html",
    "./contact.html": "contact.html",
    "./about.html": "about.html",
    "./sitemap.html": "sitemap.html",
    "./ranking.html": "category.html",
    "./new.html": "category.html",
}
for _f, _t in STATIC_PAGES:
    LINK_MAP["./" + _f] = _f


def _fix_links(html_src):
    """本番のリンクをプレビューの中の行き先に置き換える。
       置き換え先の無いもの（カテゴリー・記事・外部）は、それぞれの受け皿へ送る。"""
    def repl(m):
        href = m.group(1)
        if href in LINK_MAP:
            return f'href="{LINK_MAP[href]}"'
        if href.startswith("./articles/"):
            slug = href[len("./articles/"):-len(".html")]
            return f'href="article-{slug}.html"'
        if href.startswith("./category-"):
            return 'href="category.html"'
        if href.startswith("http") or href.startswith("mailto:"):
            return m.group(0)
        return 'href="top.html"'
    return re.sub(r'href="([^"]+)"', repl, html_src)


def build_static(fname):
    src = open(os.path.join(ROOT, fname), encoding="utf-8").read()
    h1 = re.search(r"<h1>(.*?)</h1>", src, re.S).group(1)
    # 本番の器は v2 に切り替わり、本文は .static-wrap の中に入った
    key = '<div class="static-wrap">' if '<div class="static-wrap">' in src \
        else '<div class="prose">'
    i = src.index(key) + len(key)
    j = src.rindex("</div>", i, src.index("</main>", i))
    prose = _fix_links(src[i:j].strip())
    body = f'''<div class="page-head">
  <div class="container">
    <p class="crumbs"><a href="top.html">ホーム</a><span>/</span>{h1}</p>
    <h1>{h1}</h1>
  </div>
</div>
<div class="container">
  <div class="static-wrap">{prose}</div>
</div>'''
    cur = "POLICY" if fname == "editorial-policy.html" else ""
    return page(f"{h1} - {NAME}", body, cur)


def build_sitemap():
    """サイトマップだけは本番の組み方が違うので、データから作り直す。"""
    def links(items):
        return "".join(f'<li><a href="{h}">{e(t)}</a></li>' for t, h in items)

    cats = "".join(
        f'<li><a href="category.html">{e(c["label"])}'
        f'<span class="n">{len([a for a in PUBLISHED if a.get("category") == c["key"]])}</span>'
        f'</a></li>' for c in CATS)
    arts = "".join(
        f'<li><a href="{article_href(a)}">{e(a.get("list_title") or a.get("title",""))}'
        f'<span class="n">{e(a.get("date",""))}</span></a></li>' for a in PUBLISHED)
    body = f'''<div class="page-head">
  <div class="container">
    <p class="crumbs"><a href="top.html">ホーム</a><span>/</span>サイトマップ</p>
    <h1>サイトマップ</h1>
    <p class="lead">このサイトにあるページの一覧です。</p>
  </div>
</div>
<div class="container">
  <div class="v2-section" style="padding:40px 0 80px">
    <div class="sitemap-cols">
      <div class="sitemap-block">
        <h2 class="en-label">MAIN</h2>
        <ul class="sitemap-list">{links([
            ("ホーム", "top.html"),
            ("サイト内検索", "search.html"),
            ("お問い合わせ", "contact.html"),
        ])}</ul>
      </div>
      <div class="sitemap-block">
        <h2 class="en-label">ABOUT</h2>
        <ul class="sitemap-list">{links([
            ("運営者情報", "about.html"),
            ("記事作成方針", "editorial-policy.html"),
            ("広告掲載について", "advertising.html"),
            ("プライバシーポリシー", "privacy.html"),
            ("免責事項", "disclaimer.html"),
        ])}</ul>
      </div>
    </div>

    <div class="sitemap-block is-wide">
      <h2 class="en-label">CATEGORY</h2>
      <ul class="sitemap-list is-cols">{cats}</ul>
    </div>

    <div class="sitemap-block is-wide">
      <h2 class="en-label">ARTICLES</h2>
      <ul class="sitemap-list is-cols">{arts}</ul>
    </div>
  </div>
</div>'''
    return page(f"サイトマップ - {NAME}", body, "")


# ---------------------------------------------------------------------------
# 確認用の画面
# ---------------------------------------------------------------------------
REVIEW_PAGES = [
    ("top", "トップ", "top.html"),
    ("category", "カテゴリー一覧", "category.html"),
    ("category-sub", "絞り込み", "category-sub.html"),
    ("article", "記事ページ", "article.html"),
    ("search", "検索", "search.html"),
    ("contact", "お問い合わせ", "contact.html"),
    ("notfound", "404", "404.html"),
    ("about", "運営者情報", "about.html"),
    ("editorial-policy", "記事作成方針", "editorial-policy.html"),
    ("advertising", "広告掲載", "advertising.html"),
    ("privacy", "プライバシー", "privacy.html"),
    ("disclaimer", "免責事項", "disclaimer.html"),
    ("sitemap", "サイトマップ", "sitemap.html"),
]
# 「現行と比較」で並べる、いまのサイトの対応ファイル。無いものは None
LIVE_PAGES = {
    "top": "../index.html",
    "category": "../category-pc.html",
    "category-sub": "../category-pc-monitor.html",
    "article": None,
    "search": "../search.html",
    "contact": "../contact.html",
    "notfound": "../404.html",
    "about": "../about.html",
    "editorial-policy": "../editorial-policy.html",
    "advertising": "../advertising.html",
    "privacy": "../privacy.html",
    "disclaimer": "../disclaimer.html",
    "sitemap": "../sitemap.html",
}


# スマホ幅を実寸で見るための補助ページ。Chrome はヘッドレスでも最小幅 485px 程度で
# 組んでしまうため、390px の iframe に閉じ込めて描かせる。
#   preview/_sp.html?p=top
SP_SHELL = """<!doctype html><meta charset="utf-8">
<title>SP preview</title>
<style>html,body{margin:0;background:#111}iframe{border:0;display:block;width:390px;height:2600px;background:#fff}</style>
<iframe id="f"></iframe>
<script>
  const f = document.getElementById('f');
  const p = new URLSearchParams(location.search).get('p') || 'top';
  f.src = 'pages/' + p + '.html';
  // 中身の高さに合わせて伸ばす。決め打ちだと長いページの下が切れて、
  // ヘッドレスで撮ったときにフッターが写らない
  f.addEventListener('load', function () {
    try { f.style.height = f.contentDocument.documentElement.scrollHeight + 'px'; }
    catch (e) {}
  });
</script>
"""


def build_shell():
    tabs = "".join(
        f'<button class="pg" data-page="{k}" data-file="{f}"'
        f'{" data-live=" + chr(34) + LIVE_PAGES[k] + chr(34) if LIVE_PAGES.get(k) else ""}>'
        f'{ja}</button>' for k, ja, f in REVIEW_PAGES)
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>デザイン更改案の確認 - {e(NAME)}</title>
<style>
  :root{{--ink:#111;--line:#333;--bg:#16171a;--panel:#1e2024;--muted:#9aa0a6;}}
  *{{box-sizing:border-box;}}
  body{{margin:0;background:var(--bg);color:#e8e8e6;
    font:14px/1.7 "Noto Sans JP","Helvetica Neue",Arial,"Hiragino Sans",Meiryo,sans-serif;}}
  a{{color:inherit;}}
  .bar{{position:sticky;top:0;z-index:10;display:flex;align-items:center;gap:20px;flex-wrap:wrap;
    padding:14px 22px;background:var(--panel);border-bottom:1px solid #2c2f34;}}
  .bar h1{{font-size:14px;font-weight:800;margin:0;letter-spacing:.04em;white-space:nowrap;}}
  .bar h1 small{{display:block;font-size:10.5px;font-weight:400;color:var(--muted);letter-spacing:.14em;}}
  .grp{{display:flex;align-items:center;gap:8px;}}
  .grp > .lb{{font-size:10.5px;letter-spacing:.16em;color:var(--muted);margin-right:2px;}}
  button{{font:inherit;background:#26292e;color:#d7d7d5;border:1px solid #34383e;
    padding:7px 14px;border-radius:3px;cursor:pointer;font-size:12.5px;transition:.15s;}}
  button:hover{{background:#2f333a;}}
  button.on{{background:#f0f0ee;color:#111;border-color:#f0f0ee;font-weight:700;}}
  .note{{margin-left:auto;font-size:11px;color:var(--muted);}}
  .stage{{display:flex;gap:28px;justify-content:center;align-items:flex-start;
    padding:28px 22px 64px;overflow-x:auto;}}
  .frame{{flex:0 0 auto;}}
  .frame > .cap{{display:flex;justify-content:space-between;align-items:baseline;
    margin-bottom:9px;font-size:11px;letter-spacing:.12em;color:var(--muted);}}
  .frame > .cap b{{color:#fff;font-size:11.5px;letter-spacing:.1em;}}
  .screen{{background:#fff;border:1px solid #34383e;overflow:hidden;
    box-shadow:0 18px 50px rgba(0,0,0,.45);}}
  .screen.sp{{border-radius:22px;}}
  iframe{{border:0;display:block;background:#fff;transform-origin:0 0;}}
  .empty{{display:flex;align-items:center;justify-content:center;height:100%;color:#888;
    font-size:12px;text-align:center;padding:24px;background:#f4f4f2;}}
</style>
</head>
<body>
<div class="bar">
  <h1>デザイン更改案 v2<small>PREVIEW / NOT DEPLOYED</small></h1>
  <div class="grp"><span class="lb">PAGE</span>{tabs}</div>
  <div class="grp"><span class="lb">VIEW</span>
    <button class="vw on" data-view="both">PC＋スマホ</button>
    <button class="vw" data-view="pc">PCのみ</button>
    <button class="vw" data-view="sp">スマホのみ</button>
    <button class="vw" data-view="compare">現行と比較</button>
  </div>
  <div class="grp"><span class="lb">ZOOM</span>
    <button class="zm" data-zoom="0.5">50%</button>
    <button class="zm on" data-zoom="0.7">70%</button>
    <button class="zm" data-zoom="0.85">85%</button>
    <button class="zm" data-zoom="1">100%</button>
  </div>
  <span class="note">枠の中はそのまま操作できます（スクロール・リンク・メニュー）</span>
</div>
<div class="stage" id="stage"></div>

<script>
const PAGES = {json.dumps({k: {"file": f, "ja": ja, "live": LIVE_PAGES.get(k)} for k, ja, f in REVIEW_PAGES}, ensure_ascii=False)};
let state = {{page:'top', view:'both', zoom:0.7}};

// 端末の枠。実機の論理解像度に合わせる（PCは1440、スマホはiPhone 14相当の390）
const DEVICES = {{
  pc:      {{w:1440, h:900,  label:'DESKTOP', note:'1440 × 900'}},
  sp:      {{w:390,  h:844,  label:'MOBILE',  note:'390 × 844'}},
}};

function frame(dev, src, title){{
  const d = DEVICES[dev], z = state.zoom;
  // スマホは常に等倍に近いほうが読めるので、拡大率を少し持ち上げる
  const zz = dev === 'sp' ? Math.min(1, z + 0.25) : z;
  const el = document.createElement('div');
  el.className = 'frame';
  el.innerHTML =
    '<div class="cap"><b>' + title + '</b><span>' + d.note + '</span></div>' +
    '<div class="screen ' + dev + '" style="width:' + Math.round(d.w*zz) + 'px;height:' + Math.round(d.h*zz) + 'px"></div>';
  const box = el.querySelector('.screen');
  if (src) {{
    const f = document.createElement('iframe');
    f.src = src; f.width = d.w; f.height = d.h;
    f.style.transform = 'scale(' + zz + ')';
    box.appendChild(f);
  }} else {{
    box.innerHTML = '<div class="empty">このページは現行サイトに<br>対応するファイルがないため<br>比較できません</div>';
  }}
  return el;
}}

function render(){{
  const stage = document.getElementById('stage');
  stage.innerHTML = '';
  const p = PAGES[state.page];
  const src = 'pages/' + p.file;
  if (state.view === 'both'){{
    stage.appendChild(frame('pc', src, '新デザイン / PC'));
    stage.appendChild(frame('sp', src, '新デザイン / スマホ'));
  }} else if (state.view === 'pc'){{
    stage.appendChild(frame('pc', src, '新デザイン / PC'));
  }} else if (state.view === 'sp'){{
    stage.appendChild(frame('sp', src, '新デザイン / スマホ'));
  }} else {{
    stage.appendChild(frame('pc', p.live, '現行 / PC'));
    stage.appendChild(frame('pc', src, '新デザイン / PC'));
  }}
}}

document.querySelectorAll('.pg').forEach(b => b.addEventListener('click', () => {{
  state.page = b.dataset.page;
  document.querySelectorAll('.pg').forEach(x => x.classList.toggle('on', x === b));
  render();
}}));
document.querySelectorAll('.vw').forEach(b => b.addEventListener('click', () => {{
  state.view = b.dataset.view;
  document.querySelectorAll('.vw').forEach(x => x.classList.toggle('on', x === b));
  render();
}}));
document.querySelectorAll('.zm').forEach(b => b.addEventListener('click', () => {{
  state.zoom = parseFloat(b.dataset.zoom);
  document.querySelectorAll('.zm').forEach(x => x.classList.toggle('on', x === b));
  render();
}}));

document.querySelector('.pg').classList.add('on');
render();
</script>
</body>
</html>'''


def main():
    os.makedirs(PAGES, exist_ok=True)
    files = {
        "top.html": build_top(),
        "category.html": build_category(),
        "category-sub.html": build_subcategory(),
        "article.html": build_article(),
        "search.html": build_search(),
        "contact.html": build_contact(),
        "404.html": build_404(),
        "about.html": build_about(),
    }
    for name, _t in STATIC_PAGES:
        files[name] = build_static(name)
    files["sitemap.html"] = build_sitemap()

    # 一覧から押した記事がそれぞれ開くように、記事は全部書き出す
    for a in PUBLISHED:
        files[article_href(a)] = build_article(a)

    for name, src in files.items():
        with open(os.path.join(PAGES, name), "w", encoding="utf-8") as f:
            f.write(src)
    for name in ("top.html", "category.html", "category-sub.html", "article.html",
                 "search.html", "contact.html", "404.html", "about.html",
                 "sitemap.html") + tuple(n for n, _t in STATIC_PAGES):
        print(f"  preview/pages/{name}")
    print(f"  preview/pages/article-*.html （記事 {len(PUBLISHED)} 本）")
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(build_shell())
    print("  preview/index.html")
    with open(os.path.join(OUT, "_sp.html"), "w", encoding="utf-8") as f:
        f.write(SP_SHELL)
    print("  preview/_sp.html")
    print(f"\n記事 {len(PUBLISHED)} 本 / カテゴリー {len(CATS)} 件を読み込みました。")
    print(f"確認する: open {os.path.join(OUT, 'index.html')}")


if __name__ == "__main__":
    main()
