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
import json, io, os, re, html, shutil, sys, datetime, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
from make_visual import build as make_visual

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

SITE = json.load(io.open("content/site.json", encoding="utf-8"))
ARTICLES = json.load(io.open("content/articles.json", encoding="utf-8"))

NAME     = SITE["site_name"]
TAGLINE  = SITE["tagline"]
BASE_URL = SITE["base_url"].rstrip("/")
CATS     = SITE["categories"]
SUB_LABEL = {(c["key"], sc["key"]): sc["label"]
             for c in CATS for sc in c.get("sub", [])}
FEAT     = SITE.get("features", {})
GA       = SITE.get("analytics", {}).get("ga_measurement_id", "").strip()
GSC      = SITE.get("analytics", {}).get("gsc_verification", "").strip()
def _asset_version():
    """assets の CSS/JS の内容から作る短いハッシュ。
       中身が変わったときだけURLが変わるため、ブラウザに古い
       スタイル・スクリプトが残り続けるのを防ぐ。"""
    h = hashlib.sha1()
    for f in ("style.css", "main.js", "search.js", "contact.js",
              "admin.css", "admin.js"):
        try:
            h.update(io.open(os.path.join(ROOT, "assets", f), "rb").read())
        except FileNotFoundError:
            pass
    return h.hexdigest()[:8]

ASSET_V = _asset_version()

# アクセスランキング用のデータ。
# content/ranking.json に実データ（GA4等）があればそれを使い、
# 無ければ閲覧者自身の端末に記録した閲覧回数で並べる（assets/main.js）。
try:
    RANKING = json.load(io.open(os.path.join(ROOT, "content", "ranking.json"),
                                encoding="utf-8")).get("views") or {}
except (FileNotFoundError, ValueError):
    RANKING = {}

# セール告知に使う日程。JSON をそのまま埋め込み、表示の可否は
# 閲覧時点の日付でブラウザ側が判断する（再ビルド不要にするため）。
def rank_json(p):
    data = {
        "views": RANKING,
        "items": [{"slug": a["slug"],
                   "title": a.get("list_title") or a["title"],
                   "url": f'{p}articles/{a["slug"]}.html',
                   "cat": CAT_LABEL.get(a["category"], ""),
                   "catKey": a["category"],
                   "thumb": visual_path(a, p)[0],
                   "excerpt": a.get("excerpt", ""),
                   "date": a.get("date", "")}
                  for a in PUBLISHED],
    }
    return html.escape(json.dumps(data, ensure_ascii=False), quote=True)


SALES_JSON = html.escape(json.dumps(
    (SITE.get("sales") or {}).get("items", []), ensure_ascii=False), quote=True)

ASSOC_TAG = SITE.get("amazon", {}).get("associate_tag", "").strip()
CAT_LABEL = {c["key"]: c["label"] for c in CATS}
CAT_ICON  = {c["key"]: c["icon"]  for c in CATS}

PUBLISHED = sorted([a for a in ARTICLES if a.get("published")],
                   key=lambda a: a.get("date", ""), reverse=True)

def e(s):
    return html.escape(str(s), quote=True)


def amazon_link(a):
    """ASIN があればアソシエイトタグ付きリンクを組み立てる。
       無ければ手入力の amazon_url をそのまま使う。"""
    asin = (a.get("asin") or "").strip().upper()
    if asin:
        url = f"https://www.amazon.co.jp/dp/{asin}"
        if ASSOC_TAG:
            url += f"?tag={ASSOC_TAG}"
        return url
    return a.get("amazon_url") or "https://www.amazon.co.jp/"


def visual_path(a, p):
    """アイキャッチのパスを返す。実写真が最優先、無ければ自動生成SVG。"""
    if a.get("thumb"):
        return p + a["thumb"], False
    return p + f'assets/img/auto/{a["slug"]}.svg', True

def title_lines(t):
    """「主題｜補足」形式のタイトルを2段に分けて表示する。
       1行に詰めると読みにくいうえ、区切り記号が目立ちすぎるため。"""
    if "｜" in t:
        main, sub = t.split("｜", 1)
        return (f'<span class="t-main">{e(main.strip())}</span>'
                f'<span class="t-sub">{e(sub.strip())}</span>')
    return f'<span class="t-main">{e(t)}</span>'


def jp_date(iso):
    try:
        y, m, d = iso.split("-")
        return "%s年%s月%s日" % (y, int(m), int(d))
    except Exception:
        return iso

# ============================================================ 共通パーツ
def public_url(url):
    """検索エンジンに知らせるURL。ホスティング側の作法に合わせて整える。
       Cloudflare Pages は /foo.html を /foo へ307でリダイレクトするため、
       canonical と sitemap にも拡張子なしの形を載せる。
       （サイト内のリンクは .html のままで問題なく開ける）"""
    if not SITE.get("hosting", {}).get("clean_urls", True):
        return url
    if url.endswith("/index.html"):
        return url[: -len("index.html")]
    if url.endswith(".html"):
        return url[: -len(".html")]
    return url


def head(title, desc, current, p, canonical, extra="", body_class=""):
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
    bodycls = f' class="{e(body_class)}"' if body_class else ""
    rank_data = rank_json(p)
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(public_url(canonical))}">
{gsc}<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:site_name" content="{e(NAME)}">
<meta property="og:url" content="{e(public_url(canonical))}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DotGothic16&family=Noto+Sans+JP:wght@400;500;700;900&display=swap">
<link rel="stylesheet" href="{p}assets/style.css?v={ASSET_V}">
{extra}{ga}</head>
<body data-cat="{current}"{bodycls} data-rank='{rank_data}'>
'''

def cat_tree(p, current="", current_sub="", idp="nav"):
    """カテゴリーとサブカテゴリーの一覧（PCの左サイド／スマホのメニューで共用）。
       記事のあるサブカテゴリーだけリンクにし、0件のものは件数付きの
       ただの文字として出す。中身のないページを作らないため。"""
    out = []
    for c in CATS:
        n = len([a for a in PUBLISHED if a["category"] == c["key"]])
        open_ = " open" if c["key"] == current else ""
        subs = ""
        for sc in c.get("sub", []):
            m = len([a for a in PUBLISHED
                     if a["category"] == c["key"] and a.get("sub") == sc["key"]])
            cur = ' class="is-current"' if (c["key"] == current and sc["key"] == current_sub) else ""
            if m:
                subs += (f'            <li><a href="{p}category-{c["key"]}-{sc["key"]}.html"{cur}>'
                         f'{e(sc["label"])}<span class="tree-num">{m}</span></a></li>\n')
            else:
                subs += (f'            <li><span class="tree-empty">{e(sc["label"])}'
                         f'<span class="tree-num">0</span></span></li>\n')
        out.append(
            f'      <li class="tree-item">\n'
            f'        <details{open_}>\n'
            f'          <summary>\n'
            f'            {icon(c["key"], "tree-icon")}\n'
            f'            <span class="tree-cat">{e(c["label"])}</span>\n'
            f'            <span class="tree-num">{n}</span>\n'
            f'          </summary>\n'
            f'          <ul class="tree-subs">\n'
            f'            <li><a class="tree-all" href="{p}category-{c["key"]}.html">'
            f'{e(c["label"])}の記事をすべて見る</a></li>\n'
            f'{subs}          </ul>\n'
            f'        </details>\n'
            f'      </li>\n')
    return ('    <ul class="cat-tree" id="' + idp + 'CatTree">\n'
            + "".join(out) + '    </ul>\n')


def today_panel(cls=""):
    """日替わりで1本だけ出すミニウィジェット。
       よく見ているジャンルから、その日の分を選ぶ（中身は assets/main.js）。"""
    return (f'    <section class="today-box {cls}" hidden>\n'
            f'      <p class="today-heading">本日のお勧めのモノ</p>\n'
            f'      <a class="today-card" href="#">\n'
            f'        <span class="today-thumb"><img src="" alt="" width="1200" height="600"></span>\n'
            f'        <span class="today-body">\n'
            f'          <span class="today-cat"></span>\n'
            f'          <span class="today-title"></span>\n'
            f'        </span>\n'
            f'      </a>\n'
            f'    </section>\n')


def rank_panel(p, limit=10):
    """アクセスランキングの枠。中身は assets/main.js が入れる。
       サイト全体の実データ（content/ranking.json）があればそれを、
       無ければ閲覧者自身の端末に記録された閲覧回数で並べる。"""
    return (f'    <section class="rank-box" data-rank-limit="{limit}">\n'
            f'      <p class="rank-heading">ACCESS RANKING</p>\n'
            f'      <ol class="rank-list"></ol>\n'
            f'      <p class="rank-note"></p>\n'
            f'    </section>\n')


def tab_bar(p, current="", current_sub=""):
    """スマホ用の固定タブ。横スクロールさせず4つに絞る。
       CATEGORIES はページ遷移せず、その場でカテゴリー一覧を開く。"""
    def cur(flag):
        return ' class="is-current"' if flag else ""
    is_all = current == "all"
    return (
        '<nav class="tab-bar" aria-label="表示の切り替え">\n'
        '  <div class="container">\n'
        f'    <a href="{p}index.html"{cur(is_all)}>{icon("all", "tab-icon")}<span>ALL</span></a>\n'
        f'    <a href="{p}new.html"{cur(current == "new")}>{icon("new", "tab-icon")}<span>NEW</span></a>\n'
        f'    <a href="{p}ranking.html"{cur(current == "ranking")}>{icon("rank", "tab-icon")}<span>RANKING</span></a>\n'
        f'    <a href="{p}search.html"{cur(current == "search")}>{icon("search", "tab-icon")}<span>SEARCH</span></a>\n'
        '    <button type="button" id="tabCats" aria-expanded="false" aria-controls="catPanel">'
        f'{icon("cats", "tab-icon")}<span>CATEGORIES</span></button>\n'
        '  </div>\n'
        '</nav>\n'
        '<div class="cat-panel" id="catPanel" hidden>\n'
        '  <div class="container">\n'
        + cat_tree(p, current, current_sub, "panel") +
        '  </div>\n'
        '</div>\n')


def crumb_bar(items):
    """カテゴリーナビの下に置くパンくず。items = [(ラベル, URL or None), ...]
       トップページ以外では常に出す。現在地が分かるようにするため。"""
    if not items:
        return ""
    parts = []
    for i, (label, url) in enumerate(items):
        if i:
            parts.append('<span class="crumb-sep" aria-hidden="true">›</span>')
        if url:
            parts.append(f'<a href="{url}">{e(label)}</a>')
        else:
            parts.append(f'<span aria-current="page">{e(label)}</span>')
    return f'''<nav class="crumb-bar" aria-label="現在の位置">
  <div class="container">{"".join(parts)}</div>
</nav>
'''


ICON_SPRITE = ""
try:
    ICON_SPRITE = io.open(os.path.join(ROOT, "assets", "img", "cat-icons.svg"),
                          encoding="utf-8").read().strip()
except FileNotFoundError:
    pass


def icon(key, cls="cat-icon"):
    """カテゴリーのドット絵アイコン。スプライトの symbol を参照する。"""
    return (f'<svg class="{cls}" aria-hidden="true" focusable="false">'
            f'<use href="#i-{key}"></use></svg>')


def cat_nav_item(c, p, cls=""):
    """PCのカテゴリー一覧の1件。サブカテゴリーがあるものは、
       押すとその場で開くパネルを一緒に持たせる（画面は移動しない）。
       JavaScriptが動かない環境では、そのままカテゴリーページへ進む。"""
    a = f' class="{cls}"' if cls else ""
    subs = [sc for sc in c.get("sub", [])
            if any(x["category"] == c["key"] and x.get("sub") == sc["key"]
                   for x in PUBLISHED)]
    link = (f'<a href="{p}category-{c["key"]}.html"{a}>'
            f'{icon(c["key"])}<span class="cat-nav-label">{e(c["label"])}</span></a>')
    if not subs:
        return f'      <li>{link}</li>\n'

    items = (f'          <li><a href="{p}category-{c["key"]}.html">'
             f'{e(c["label"])}のすべて</a></li>\n')
    for sc in subs:
        n = len([x for x in PUBLISHED
                 if x["category"] == c["key"] and x.get("sub") == sc["key"]])
        items += (f'          <li><a href="{p}category-{c["key"]}-{sc["key"]}.html">'
                  f'{e(sc["label"])}<span class="sub-n">{n}</span></a></li>\n')
    return (f'      <li class="has-sub" data-cat="{c["key"]}">{link}\n'
            f'        <div class="sub-pop" hidden>\n'
            f'          <ul>\n{items}          </ul>\n'
            f'        </div>\n'
            f'      </li>\n')


def header(current, p, crumbs=None, current_sub="", band=""):
    # いま見ているカテゴリーは、ALL のすぐ右に持ってくる。
    # 一覧は横スクロールするので、右のほうにあると現在地が画面外に出てしまう。
    # 重複させず「移動」させるので、同じリンクが2つ並ぶことはない。
    here = next((c for c in CATS if c["key"] == current), None)

    allcur = ' class="is-current"' if current == "all" else ""
    nav = (f'      <li><a href="{p}index.html"{allcur}>{icon("all")}'
           f'<span class="cat-nav-label">ALL</span></a></li>\n')
    if here:
        nav += cat_nav_item(here, p, "is-current is-here")
    for c in CATS:
        if here and c["key"] == here["key"]:
            continue          # 先頭に出したので、ここでは出さない
        nav += cat_nav_item(c, p)

    # ハンバーガー内の検索は出さない。スマホには SEARCH タブがあり、
    # PCではヘッダーの右側に同じリンクが並ぶため。
    search_link = (f'<li class="pc-only-link"><a href="{p}search.html">検索</a></li>\n        '
                   if FEAT.get("search") else "")
    contact_nav = (f'<li><a href="{p}contact.html">お問い合わせ</a></li>'
                   if FEAT.get("contact_form") else
                   f'<li><a href="mailto:{e(SITE["email"])}">お問い合わせ</a></li>')

    return f'''{ICON_SPRITE}
<header class="site-header">
  <div class="container header-inner">
    <div class="header-side" aria-hidden="true"></div>
    <div class="site-brand">
      <a class="site-title" href="{p}index.html" aria-label="{e(NAME)}">
        <span class="brand-mark" aria-hidden="true"></span>
        <span class="brand-name">{e(NAME)}</span>
      </a>
      <div class="site-tagline">{e(TAGLINE)}</div>
    </div>
    <button class="nav-toggle" id="navToggle" aria-expanded="false" aria-controls="globalNav" aria-label="メニューを開く">
      <span></span><span></span><span></span>
    </button>
    <nav class="global-nav" id="globalNav" aria-label="メニュー">
      <ul class="nav-links">
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

{tab_bar(p, current, current_sub)}{crumb_bar(crumbs)}{band}<!-- セール告知：期間内だけ JS が表示する（assets/main.js） -->
<div class="site-notice" id="saleNotice" hidden data-sales='{SALES_JSON}'>
  <div class="container">
    <span class="notice-label">お知らせ</span>
    <div class="notice-marquee"><p id="saleText"></p></div>
  </div>
</div>
'''

def footer(p, sticky_url=None):
    if FEAT.get("contact_form"):
        contact_link = f'<a href="{p}contact.html">お問い合わせフォーム</a>'
    else:
        contact_link = f'<a href="mailto:{e(SITE["email"])}">{e(SITE["email"])}</a>'

    sticky = ""
    if sticky_url and FEAT.get("sticky_cta"):
        sticky = f'''<div class="sticky-cta" id="stickyCta">
  <a class="btn-amazon" href="{e(sticky_url)}" target="_blank" rel="nofollow sponsored noopener">
    <span class="cart">{icon("cart", "btn-icon")}</span>Amazonで商品の詳細を見る
  </a>
</div>

'''
    return f'''<footer class="site-footer" id="contact">
  <div class="container">
    <div class="footer-rows">
      <div class="footer-row">
        <span class="footer-row-label">サイト情報</span>
        <ul class="footer-inline">
          <li><a href="{p}privacy.html">プライバシーポリシー</a></li>
          <li><a href="{p}disclaimer.html">免責事項</a></li>
          <li><a href="{p}about.html">運営者情報</a></li>
          <li><a href="{p}search.html">サイト内検索</a></li>
        </ul>
      </div>
      <div class="footer-row">
        <span class="footer-row-label">お問い合わせ</span>
        <ul class="footer-inline">
          <li>{contact_link}</li>
        </ul>
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

<script src="{p}assets/vendor/motion-mini.min.js" defer></script>
<script src="{p}assets/main.js?v={ASSET_V}" defer></script>
</body>
</html>
'''

def main_block(body, p, current="", current_sub="", sidebar=False, hero_slot=""):
    """本文の器。一覧ページではPC幅のときだけ左にカテゴリー一覧を置く。
       スマホでは幅が足りないので出さず、ハンバーガーメニュー側に集約する。"""
    if not sidebar:
        return ('\n<main id="top" class="layout">\n  <div class="container">\n'
                + body + '  </div>\n</main>\n\n')
    tree = cat_tree(p, current, current_sub, "side")
    # 3カラムのときは「本日のお勧めのモノ」を左、検索を右に置く。
    # 2カラムに縮んだときは右列が消えるので、検索は左に残す。
    # 両方を書き出し、どちらを見せるかはCSSの幅で切り替える。
    search_l = (side_search(p, "only-2col") if FEAT.get("search") else "")
    search_r = (side_search(p, "only-3col") if FEAT.get("search") else "")
    return ('\n<main id="top" class="layout has-side">\n'
            '  <div class="container layout-grid">\n'
            + hero_slot +
            '    <div class="side-col">\n'
            + today_panel("is-side") + search_l +
            '    <aside class="side-nav side-tile" aria-label="カテゴリー">\n'
            '      <p class="side-heading">CATEGORIES</p>\n'
            + tree +
            '    </aside>\n'
            '    </div>\n'
            '    <div class="layout-main">\n'
            + body +
            '    </div>\n'
            '    <div class="side-rank">\n'
            + rank_panel(p, 10) + search_r + '    </div>\n'
            '  </div>\n</main>\n\n')


def page(title, desc, current, p, canonical, body, sticky_url=None, extra_head="", extra_js="", body_class="", crumbs=None, current_sub="", sidebar=False, band="", hero_slot=""):
    return (head(title, desc, current, p, canonical, extra_head, body_class)
            + header(current, p, crumbs, current_sub, band)
            + main_block(body, p, current, current_sub, sidebar, hero_slot)
            + footer(p, sticky_url).replace("</body>", extra_js + "</body>"))

# ============================================================ 部品
def thumb(a, p):
    src, _ = visual_path(a, p)
    return (f'<img src="{e(src)}" alt="{e(a.get("list_title") or a["title"])}" '
            f'loading="lazy" width="1200" height="430">')

KIND_LABEL = {"review": "レビュー", "roundup": "特集", "guide": "選び方"}


def kind_of(a):
    """記事の種類を返す。明示が無ければカテゴリーから推測する。
       review  : 1つの商品を掘り下げるレビュー
       roundup : 複数の商品を比べる特集"""
    k = a.get("kind")
    if k in KIND_LABEL:
        return k
    return "roundup" if a.get("category") == "feature" else "review"


def kind_badge(a):
    k = kind_of(a)
    return f'<span class="tag tag-kind is-{k}">{KIND_LABEL[k]}</span>'


def product_table(a, p):
    """特集用の商品比較表。行が1商品で、価格・特徴・リンクを並べる。
       個別レビューがある商品は、その記事へ送る導線も置く。"""
    items = a.get("products") or []
    if not items:
        return ""
    pub = {x["slug"]: x for x in PUBLISHED}
    rows = ""
    for it in items:
        pick = (f'<span class="pd-pick">{e(it["pick"])}</span>' if it.get("pick") else "")
        maker = (f'<span class="pd-maker">{e(it["maker"])}</span>' if it.get("maker") else "")
        buy = ""
        if it.get("asin") or it.get("url"):
            href = amazon_link({"asin": it.get("asin"), "amazon_url": it.get("url")})
            buy = (f'<a class="pd-buy" href="{e(href)}" target="_blank" '
                   f'rel="nofollow sponsored noopener">Amazonで見る</a>')
        rev = ""
        tgt = pub.get((it.get("slug") or "").strip())
        if tgt:
            rev = (f'<a class="pd-review" href="{p}articles/{e(tgt["slug"])}.html">'
                   f'詳しいレビュー <span aria-hidden="true">→</span></a>')
        rows += f'''                <tr>
                  <th scope="row">{pick}{maker}<span class="pd-name">{it.get("name","")}</span></th>
                  <td class="pd-price">{it.get("price","")}</td>
                  <td>{it.get("note","")}</td>
                  <td class="pd-links">{buy}{rev}</td>
                </tr>
'''
    return f'''          <h2 id="sec-products">比較した商品</h2>
{paras(a.get("products_intro"))}          <p class="scroll-hint">← 横にスクロールできます →</p>
          <div class="table-scroll pd-table" tabindex="0" role="region" aria-label="商品の比較表">
            <table>
              <thead>
                <tr><th scope="col">商品</th><th scope="col">価格の目安</th><th scope="col">特徴</th><th scope="col">リンク</th></tr>
              </thead>
              <tbody>
{rows}              </tbody>
            </table>
          </div>
'''


def featured_in(a, p):
    """この商品を扱っている特集を探して、記事の下に置く導線にする。
       特集側の products[].slug を見て、逆向きにたどる。"""
    me = a["slug"]
    hits = [x for x in PUBLISHED
            if x["slug"] != me
            and any((it.get("slug") or "") == me for it in (x.get("products") or []))]
    if not hits:
        return ""
    cards = ""
    for x in hits[:3]:
        cards += (f'''            <a class="fi-card" href="{p}articles/{e(x["slug"])}.html">
              <span class="fi-label">特集</span>
              <span class="fi-title">{title_lines(x.get("list_title") or x["title"])}</span>
              <span class="fi-desc">{e(x.get("excerpt",""))}</span>
            </a>
''')
    return f'''          <h2 id="sec-featured-in">この商品を比較した特集</h2>
          <p>ほかの選択肢と並べて見たい場合は、こちらもあわせてどうぞ。</p>
          <div class="fi-grid">
{cards}          </div>
'''


def card(a, p, lead=False):
    tags = f'<span class="tag tag-hot">{e(CAT_LABEL.get(a["category"], ""))}</span>'
    tags += "".join(f'<span class="tag">{e(t)}</span>' for t in a.get("tags", [])[:1])
    cls = "card is-lead" if lead else "card"
    return f'''        <article class="{cls} reveal" data-cat="{a["category"]}" data-slug="{e(a["slug"])}" data-date="{e(a.get("date",""))}">
          <div class="card-thumb is-auto"><span class="card-flags" aria-hidden="true"></span>{thumb(a, p)}</div>
          <div class="card-body">
            <div class="card-tags">{tags}{kind_badge(a)}</div>
            <h3 class="card-title"><a class="card-stretch" href="{p}articles/{e(a["slug"])}.html">{title_lines(a.get("list_title") or a["title"])}</a></h3>
            <p class="card-desc">{e(a.get("excerpt",""))}</p>
            <span class="card-link" aria-hidden="true">詳細を見る</span>
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
            <span class="cart">{icon("cart", "btn-icon")}</span>{e(label)}
          </a>{n}
        </div>
'''

def stars(n):
    n = int(round(float(n or 0)))
    return "★" * n + "☆" * (5 - n)

# ============================================================ 記事ページ
def paras(v, cls=""):
    """文字列でも配列でも受け取り、段落に組む。
       ライターの地の文はここを通す。改行だけの段落は捨てる。"""
    if not v:
        return ""
    items = v if isinstance(v, list) else [v]
    c = f' class="{cls}"' if cls else ""
    return "".join(f"          <p{c}>{t}</p>\n" for t in items if str(t).strip())


def render_article(a):
    p = "../"
    slug = a["slug"]
    cat = a["category"]
    url = f'{BASE_URL}/articles/{slug}.html'
    b = []
    add = b.append

    add('      <article class="card-surface" id="review">\n')
    add(f'''        <div class="article-meta">
          <span class="badge badge-cat">{e(CAT_LABEL.get(cat,""))}</span>
          {kind_badge(a)}
          <span class="article-date">{e(jp_date(a.get("updated") or a["date"]))} 更新</span>
        </div>

        <h1 class="article-title">{title_lines(a["title"])}</h1>
''')

    # アイキャッチは実写真があるときだけ置く。
    # 自動生成の模様を記事冒頭に大きく出しても情報がなく、結論ボックスを押し下げるだけなので出さない。
    if a.get("thumb"):
        # AIで作った画像は、実物の写真ではないことを画像の下に明記する。
        note = ('\n          <figcaption class="eyecatch-note">'
                'イメージ（AI生成）。実際の製品とは異なります。</figcaption>'
                if a.get("image_ai") else "")
        add(f'''        <figure class="eyecatch has-image">
          <img src="{p}{e(a["thumb"])}" alt="{e(a["title"])}" width="1200" height="600">{note}
        </figure>
''')
    else:
        add('        <div class="article-accent" aria-hidden="true"></div>\n')

    # 結論ボックス
    if a.get("summary"):
        items = "".join(f'              <li>{s}</li>\n' for s in a["summary"])
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
          <div class="summary-head">{a.get("verdict_title","結論")}</div>
          <div class="summary-body">
            <ul class="summary-list">
{items}            </ul>
          </div>
{rating}        </section>
''')

    # 目次
    toc = []
    if a.get("highlights", {}).get("items"): toc.append(("sec-highlights", "ここが効く"))
    if a.get("not_for", {}).get("items"): toc.append(("sec-notfor", "買わないほうがいい人"))
    if a.get("scenes"):                   toc.append(("sec-scenes", "この商品で変わる生活シーン"))
    if a.get("pros") or a.get("cons"):    toc.append(("sec-proscons", "メリットとデメリット"))
    if a.get("products"):                 toc.append(("sec-products", "比較した商品"))
    if a.get("spec", {}).get("rows"):     toc.append(("spec", "スペック比較表"))
    for i, sec in enumerate(a.get("sections", []), start=1):
        toc.append((f"sec-note{i}", sec.get("heading", "")))
    if a.get("voices"):                   toc.append(("sec-voice", "共通の不満点と対処法"))
    if a.get("next_problem", {}).get("items"): toc.append(("sec-next", "次に困りそうなこと"))
    if featured_in(a, p):                 toc.append(("sec-featured-in", "この商品を比較した特集"))
    if a.get("conclusion"):               toc.append(("sec-conclusion", "まとめ"))
    if toc:
        li = "".join(f'            <li><a href="#{i}">{e(t)}</a></li>\n' for i, t in toc)
        add(f'''        <nav class="toc" aria-label="目次">
          <div class="toc-title">目次</div>
          <ol>
{li}          </ol>
        </nav>
''')

    # 購入リンクは目次の下に置く。結論を読んですぐ動ける位置。
    add(cta(amazon_link(a), a.get("cta_label", "Amazonで価格を見る"),
            "※ 価格・在庫は変動します。最新情報はリンク先でご確認ください。"))

    add('        <div class="article-body">\n')
    add(paras(a.get("lead")))

    # 良い点を先に、はっきり見せる枠。
    hl = a.get("highlights", {})
    if hl.get("items"):
        add(f'''          <h2 id="sec-highlights">{hl.get("heading", "ここが効く")}</h2>
''')
        add(paras(hl.get("intro")))
        add('          <div class="hl-grid">\n')
        for i, it in enumerate(hl["items"], start=1):
            add(f'''            <div class="hl-card">
              <span class="hl-num">{i}</span>
              <div class="hl-body">
                <h3 class="hl-title">{it.get("title","")}</h3>
                <p>{it.get("text","")}</p>
              </div>
            </div>
''')
        add('          </div>\n')
        add(paras(hl.get("after")))

    # 1. 買わないほうがいい人（最優先のネガティブ訴求）
    nf = a.get("not_for", {})
    if nf.get("items"):
        items = "".join(f'              <li>{x}</li>\n' for x in nf["items"])
        add(f'''          <h2 id="sec-notfor">この商品を買わないほうがいい人</h2>
          <div class="notfor-box">
            <div class="notfor-head">{icon("warn", "hd-icon")} 先に読んでください</div>
            <div class="notfor-body">
              <p>{nf.get("intro","")}</p>
              <ul class="notfor-list">
{items}              </ul>
              <p class="notfor-foot">上のどれかに当てはまる場合、この商品は期待に応えられない可能性が高いです。別の選択肢を検討したほうが満足度は高くなります。</p>
            </div>
          </div>
''')
        add(paras(nf.get("after")))

    # 2. この商品で変わる「実際の生活シーン」
    if a.get("scenes"):
        add('          <h2 id="sec-scenes">この商品で変わる「実際の生活シーン」</h2>\n')
        add(paras(a.get("scenes_intro")))
        add('          <div class="scenes">\n')
        for i, sc in enumerate(a["scenes"], start=1):
            add(f'''            <div class="scene">
              <span class="scene-num">{i}</span>
              <div class="scene-body">
                <h3 class="scene-title">{sc.get("title","")}</h3>
                <p>{sc.get("text","")}</p>
              </div>
            </div>
''')
        add('          </div>\n')
        add(paras(a.get("scenes_after")))

    # メリット / デメリット
    if a.get("pros") or a.get("cons"):
        pros = "".join(f'                <li>{p_}</li>\n' for p_ in a.get("pros", []))
        cons = "".join(f'                <li>{c_}</li>\n' for c_ in a.get("cons", []))
        add(f'''          <h2 id="sec-proscons">メリット・デメリット</h2>
          <div class="proscons">
            <div class="pc-box pc-good">
              <div class="pc-head">{icon("good", "hd-icon")} 良かった点（メリット）</div>
              <ul>
{pros}              </ul>
            </div>
            <div class="pc-box pc-bad">
              <div class="pc-head">{icon("bad", "hd-icon")} 気になった点（デメリット）</div>
              <ul>
{cons}              </ul>
            </div>
          </div>
''')
        add(paras(a.get("proscons_note")))

    # 比較した商品（特集用）
    add(product_table(a, p))

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
          <p>{sp.get("intro","")}</p>
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
        add(paras(sp.get("read")))
        add(cta(amazon_link(a), a.get("cta_label","Amazonでチェックする"),
                "タイムセール対象になっている場合があります"))

    # ライターの地の文。見出し＋段落の自由記述で、表では伝わらない
    # 判断の根拠や使いどころを書く。
    for i, sec in enumerate(a.get("sections", []), start=1):
        add(f'          <h2 id="sec-note{i}">{e(sec.get("heading",""))}</h2>\n')
        add(paras(sec.get("paras")))
        if sec.get("aside"):
            add(f'''          <div class="personal-note">
            <span class="pn-label">{e(sec.get("aside_label","レビューを読み込んで見えたこと"))}</span>
            <p>{sec["aside"]}</p>
          </div>
''')

    # 口コミ・対策
    if a.get("voices"):
        add(f'          <h2 id="sec-voice">気になる点と、その対策</h2>\n')
        if a.get("voices_intro"):
            add(f'          <p>{a["voices_intro"]}</p>\n')
        for v in a["voices"]:
            st = (f'<span class="voice-stars">{stars(v["stars"])}</span>'
                  if v.get("stars") else "")
            neg = " is-negative" if v.get("negative") else ""
            add(f'''          <h3>{v.get("heading","")}</h3>
          <div class="voice{neg}">
            <span class="voice-name">{v.get("who","")}{st}</span>
            {v.get("text","")}
          </div>
          <div class="fix-box">
            <span class="fix-title">{icon("check", "hd-icon")} {v.get("fix_title","")}</span>
            {v.get("fix","")}
          </div>
''')
        add(paras(a.get("voices_after")))

    # 6. 運営者の実体験コラム
    if a.get("personal_note"):
        add(f'''          <div class="personal-note">
            <span class="pn-label">レビューから見えたこと</span>
            <p>{a["personal_note"]}</p>
          </div>
''')

    # 7. Amazonボタン
    add(cta(amazon_link(a), "Amazonで価格と詳細を確認する",
            "※ 価格・在庫は変動します。最新情報はリンク先でご確認ください。"))

    # 8. 次に困りそうなこと・併売の提案（回遊導線）
    np_ = a.get("next_problem", {})
    if np_.get("items"):
        add('          <h2 id="sec-next">次に困りそうなこと</h2>\n')
        if np_.get("intro"):
            add(f'          <p>{np_["intro"]}</p>\n')
        add('          <div class="next-grid">\n')
        for it in np_["items"]:
            link = ""
            if it.get("link_url") and it.get("link_label"):
                link = (f'\n                <a class="next-link" href="{p}{e(it["link_url"])}">'
                        f'{e(it["link_label"])} <span aria-hidden="true">→</span></a>')
            add(f'''            <div class="next-card">
              <h3 class="next-title">{it.get("title","")}</h3>
              <p>{it.get("text","")}</p>{link}
            </div>
''')
        add('          </div>\n')

    # この商品を扱っている特集への導線
    add(featured_in(a, p))

    # まとめ
    if a.get("conclusion"):
        add(f'''          <h2 id="sec-conclusion">{a.get("conclusion_title","まとめ")}</h2>
''')
        add(paras(a["conclusion"]))
        add(cta(amazon_link(a), "Amazonで購入する"))
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
        <h2 class="section-heading">関連記事</h2>
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
                sticky_url=(amazon_link(a) if (a.get("asin") or a.get("amazon_url")) else None),
                extra_js=extra_js,
                # 記事ページはサイドを出さず、本文だけを広く使う
                sidebar=False, body_class="is-article", current_sub=a.get("sub", ""),
                crumbs=[("ホーム", f"{p}index.html"),
                        (CAT_LABEL.get(cat, ""), f"{p}category-{cat}.html"),
                        (a.get("list_title") or a["title"], None)])

# ============================================================ 一覧・固定ページ
def hero(mark, h1, lead, count=None):
    """ページ見出しの枠。アイコンと見出しは横に並べて1行に収める。
       mark には icon() が返すドット絵のSVGを渡す。"""
    ic = f'<span class="page-hero-icon" aria-hidden="true">{mark}</span>' if mark else ""
    c = f'\n        <span class="hero-count">全 {count} 記事</span>' if count is not None else ""
    lead_html = f'\n        <p>{e(lead)}</p>' if lead else ""
    return f'''      <div class="page-hero">
        <div class="page-hero-head">{ic}<h1>{e(h1)}</h1></div>{lead_html}{c}
      </div>
'''

SEARCH_HINT = "例：加湿器、モニターアーム、腰痛"


def side_search(p, cls=""):
    """PCのサイドに置く検索。カテゴリーとは別のタイルにする。"""
    return (f'    <div class="side-tile side-search {cls}">\n'
            f'      <form class="searchbox" action="{p}search.html" method="get" role="search">\n'
            f'        <input type="search" name="q" placeholder="{e(SEARCH_HINT)}" aria-label="サイト内検索">\n'
            f'        <button type="submit">検索</button>\n'
            f'      </form>\n'
            f'    </div>\n')


SEARCH_TILE = '''        <div class="search-tile">
          <form class="searchbox" action="./search.html" method="get" role="search">
            <input type="search" name="q" placeholder="例：加湿器、モニターアーム、腰痛" aria-label="サイト内検索">
            <button type="submit">検索</button>
          </form>
        </div>
'''

SEARCH_BOX = '''      <form class="searchbox" action="./search.html" method="get" role="search">
        <input type="search" name="q" placeholder="キーワードで記事を探す（例：加湿器、腰痛）" aria-label="サイト内検索">
        <button type="submit">検索</button>
      </form>
'''

def feature_banner(a, p):
    """特集のバナー。記事に banner が設定されていればそれを使い、
       無ければ文字入りのSVGを自動生成して当てる。"""
    if a.get("banner"):
        return (f'<img src="{p}{e(a["banner"])}" alt="{e(a.get("list_title") or a["title"])}" '
                f'loading="lazy" width="1200" height="300">')
    src, _ = visual_path(a, p)
    return (f'<img src="{e(src)}" alt="{e(a.get("list_title") or a["title"])}" '
            f'loading="lazy" width="1200" height="300">')


def feature_cards(p):
    """特集をカルーセルで1本ずつ見せる。
       枠は常に1つぶんの幅にし、自動送りと前後ボタンで切り替える。
       中身の切り替えは assets/main.js（JSが動かない環境では
       横スクロールできる並びとして機能する）。"""
    feats = [a for a in PUBLISHED if a["category"] == "feature"][:8]
    if not feats:
        return ""
    slides = ""
    for i, a in enumerate(feats):
        slides += (
            f'            <li class="feat-slide">\n'
            f'              <a class="feat-card" href="{p}articles/{e(a["slug"])}.html">\n'
            f'                <span class="feat-banner">\n'
            f'                  <span class="feat-label">特集</span>\n'
            f'                  {feature_banner(a, p)}\n'
            f'                </span>\n'
            f'                <span class="feat-body">\n'
            f'                  <span class="feat-title">{title_lines(a.get("list_title") or a["title"])}</span>\n'
            f'                  <span class="feat-desc">{e(a.get("excerpt",""))}</span>\n'
            f'                </span>\n'
            f'              </a>\n'
            f'            </li>\n')
    dots = "".join(
        f'            <button type="button" class="feat-dot" data-go="{i}" '
        f'aria-label="{i + 1}件目を表示"></button>\n' for i in range(len(feats)))
    multi = len(feats) > 1
    ctrl = ""
    if multi:
        ctrl = ('        <button type="button" class="feat-arrow feat-prev" aria-label="前の特集">'
                '<span aria-hidden="true">◀</span></button>\n'
                '        <button type="button" class="feat-arrow feat-next" aria-label="次の特集">'
                '<span aria-hidden="true">▶</span></button>\n')
    return ('      <section class="section-block is-flush">\n'
            f'        <div class="feat-carousel" data-interval="5000" data-count="{len(feats)}">\n'
            '          <ul class="feat-track">\n' + slides +
            '          </ul>\n' + ctrl +
            ('          <div class="feat-dots">\n' + dots + '          </div>\n' if multi else '') +
            '        </div>\n'
            '      </section>\n')


def feature_ready():
    """特集を作る段に達したジャンルを返す。
       しきい値ごとの「段」で数え、1本増えるたびに作り直さないようにする。
       判定の詳細と記事の選出は tools/feature_plan.py と同じ考え方。"""
    th = int(FEAT.get("feature_threshold") or 5)
    done = {}
    for a in ARTICLES:
        if a.get("category") == "feature" and a.get("feature_of"):
            done[a["feature_of"]] = max(done.get(a["feature_of"], 0),
                                        int(a.get("feature_stage") or 1))
    ready = []
    for c in CATS:
        if c["key"] == "feature":
            continue
        for sc in c.get("sub", []):
            n = len([a for a in PUBLISHED
                     if a["category"] == c["key"] and a.get("sub") == sc["key"]])
            stage = n // th
            if stage >= 1 and stage > done.get(f'{c["key"]}/{sc["key"]}', 0):
                ready.append((f'{c["label"]}／{sc["label"]}', n, stage))
    return th, ready


DEFAULT_TOP = [
    {"key": "hero",       "on": True},
    {"key": "today",      "on": True},
    {"key": "new",        "on": True},
    {"key": "feature",    "on": True},
    {"key": "ranking",    "on": True},
    {"key": "categories", "on": True},
    {"key": "policy",     "on": True},
]

# 管理画面に出す名前。ここに無いものは並べ替えの対象にしない。
TOP_LABEL = {
    "hero":       "見出しバナー",
    "today":      "本日のお勧めのモノ",
    "new":        "新着記事",
    "feature":    "特集",
    "ranking":    "よく読まれている記事（スマホのみ）",
    "categories": "カテゴリーから探す",
    "policy":     "このサイトの読み方",
}


def top_layout():
    """トップの区画の並び順。設定に無いものは既定の位置に補う。"""
    saved = (SITE.get("layout") or {}).get("top") or []
    out, seen = [], set()
    for it in saved:
        k = it.get("key")
        if k in TOP_LABEL and k not in seen:
            out.append({"key": k, "on": bool(it.get("on", True))})
            seen.add(k)
    for it in DEFAULT_TOP:
        if it["key"] not in seen:
            out.append(dict(it))
    return out


def news_rail(items, p):
    """新着。スマホでは横に流す小さめのカード、PCではこれまでどおりの並び。
       中身は同じHTMLで、見せ方だけCSSで切り替える。"""
    return ('      <section class="section-block">\n'
            '        <div class="rail">\n' + grid(items, p) +
            '        </div>\n'
            '        <div class="cta-wrap rail-more">\n'
            f'          <a class="btn-sub" href="{p}new.html">新着記事をもっと見る</a>\n'
            '        </div>\n'
            '      </section>\n')


def mobile_ranking(p):
    """スマホにはPCのようなサイドが無く、ランキングへ行く手立てがタブだけに
       なる。トップにも上位を出して、読まれている記事から入れるようにする。"""
    return ('      <section class="section-block is-mobile-only">\n'
            '        <h2 class="section-heading">よく読まれている記事</h2>\n'
            + rank_panel(p, 5) +
            '        <div class="cta-wrap">\n'
            f'          <a class="btn-sub" href="{p}ranking.html">ランキングをすべて見る</a>\n'
            '        </div>\n'
            '      </section>\n')


def cat_finder(p):
    """カテゴリーから探すタイル。記事のあるカテゴリーを、代表記事の
       画像つきで並べる。画像は、そのカテゴリーで最も新しい記事のものを
       借りる（無ければ自動生成のものになる）。"""
    rows = ""
    for c in CATS:
        items = [a for a in PUBLISHED if a["category"] == c["key"]]
        if not items:
            continue
        newest = max(items, key=lambda a: a.get("updated") or a.get("date") or "")
        src, _ = visual_path(newest, p)
        rows += (f'          <a class="cf-tile" href="{p}category-{c["key"]}.html">\n'
                 f'            <span class="cf-thumb"><img src="{e(src)}" alt="" '
                 f'loading="lazy" width="1200" height="430"></span>\n'
                 f'            <span class="cf-body">\n'
                 f'              <span class="cf-label">{icon(c["key"])}{e(c["label"])}</span>\n'
                 f'              <span class="cf-count">{len(items)} 記事</span>\n'
                 f'            </span>\n'
                 f'          </a>\n')
    if not rows:
        return ""
    return ('      <section class="section-block">\n'
            '        <h2 class="section-heading">カテゴリーから探す</h2>\n'
            '        <div class="cf-grid">\n' + rows +
            '        </div>\n'
            '      </section>\n')

POLICY = [
    ("01", "購入者レビューと公表仕様を突き合わせています",
     "良い評価だけでなく、低い評価に繰り返し出てくる内容まで読み込み、仕様と照らして整理しています。"),
    ("02", "「合わない場面」を先に書きます",
     "どんな製品にも向かない環境があります。買ってから気づく条件を、記事の前半ではっきり書くようにしています。"),
    ("03", "広告収益の有無で内容は変えません",
     "Amazonアソシエイトによる収益がありますが、掲載の可否や評価は独立して判断しています。"),
]


def policy_details(p):
    """見出しバナーの中に畳んでおく「このサイトの読み方」。
       押したときだけ開く。JavaScriptなしでも動く details を使う。"""
    items = ""
    for num, head, text in POLICY:
        items += ('            <div class="policy-item">\n'
                  f'              <span class="policy-num">{num}</span>\n'
                  '              <div class="policy-body">\n'
                  f'                <h3>{e(head)}</h3>\n'
                  f'                <p>{e(text)}</p>\n'
                  '              </div>\n'
                  '            </div>\n')
    return ('        <details class="hero-policy">\n'
            '          <summary>このサイトの読み方'
            f'{icon("check", "hd-icon")}</summary>\n'
            '          <p class="policy-lead">購入者レビューと製品仕様を突き合わせ、'
            '良い点だけでなく「合わない場面」まで整理しています。</p>\n'
            '          <div class="policy">\n' + items +
            '          </div>\n'
            f'          <div class="cta-wrap"><a class="btn-sub" href="{p}about.html">'
            '運営者情報を見る</a></div>\n'
            '        </details>\n')


def policy_box(p):
    """このサイトの読み方。何を根拠に書いているかを短く示す。
       広告収益のあるサイトでは、書き方の基準を明示しておくことが
       読者の判断材料になる（検索エンジンの評価でも見られる部分）。"""
    items = ""
    for num, head, text in POLICY:
        items += ('          <div class="policy-item">\n'
                  f'            <span class="policy-num">{num}</span>\n'
                  '            <div class="policy-body">\n'
                  f'              <h3>{e(head)}</h3>\n'
                  f'              <p>{e(text)}</p>\n'
                  '            </div>\n'
                  '          </div>\n')
    return ('      <section class="section-block">\n'
            '        <h2 class="section-heading">このサイトの読み方</h2>\n'
            '        <p class="policy-lead">購入者レビューと製品仕様を突き合わせ、'
            '良い点だけでなく「合わない場面」まで整理しています。</p>\n'
            '        <div class="policy">\n' + items +
            '        </div>\n'
            f'        <div class="cta-wrap"><a class="btn-sub" href="{p}about.html">'
            '運営者情報を見る</a></div>\n'
            '      </section>\n')


def build_index():
    p = "./"
    feat = [a for a in PUBLISHED if a.get("featured")][:3]
    latest = PUBLISHED[:6]
    n_pub = len(PUBLISHED)
    n_cat = len([c for c in CATS if any(a["category"] == c["key"] for a in PUBLISHED)])
    # 記事のあるカテゴリー名。表示する3つはページを開くたびにJSが選ぶ。
    cat_names = html.escape(json.dumps(
        [c["label"] for c in CATS
         if c["key"] != "feature" and any(a["category"] == c["key"] for a in PUBLISHED)],
        ensure_ascii=False), quote=True)
    # ヒーローバナー。ヘッダー直下の帯ではなく、本文の先頭に置く
    # 独立したタイルにする（サイトの主張はヘッダーにも出ているため、
    # ここでは見出しと記事数だけに絞って高さを抑える）。
    band = ""
    # 見出しバナー。「このサイトの読み方」は畳んでおき、押すと開く。
    # 常に出しておくと縦を取りすぎるが、隠しておくと信頼の材料が伝わらない。
    hero_tile = (
        '      <section class="hero-tile">\n'
        '        <h1 class="fit-line">レビューを読み込んで、'
        '<span class="accent">不満点まで</span>まとめる。</h1>\n'
        f'        <p class="hero-count" data-cats=\'{cat_names}\' '
        f'data-n-cat="{n_cat}" data-n-pub="{n_pub}"></p>\n'
        + policy_details(p) +
        (SEARCH_TILE if FEAT.get("search") else "") +
        '      </section>\n')
    # トップに置く区画。並び順と表示・非表示は content/site.json の
    # layout.top で決める（管理画面からドラッグして入れ替えられる）。
    blocks = {
        "today":      lambda: today_panel("is-mobile"),
        "new":        lambda: news_rail(latest, p),
        "feature":    lambda: feature_cards(p),
        "ranking":    lambda: mobile_ranking(p),
        "categories": lambda: cat_finder(p),
        "policy":     lambda: policy_box(p),
    }
    body = ""
    hero_on = True
    for item in top_layout():
        if item["key"] == "hero":
            hero_on = item.get("on", True)
            continue
        make = blocks.get(item["key"])
        if make and item.get("on", True):
            # PCで並び替えられるよう、区画ごとに印を付けておく
            body += f'<div class="tb" data-tb="{item["key"]}">\n' + make() + '</div>\n'
    hero_slot = ('    <div class="hero-slot">\n' + hero_tile + '    </div>\n'
                 if hero_on else "")
    return page(f"{NAME}｜{TAGLINE}", SITE["description"], "all", p, BASE_URL + "/", body,
                body_class="is-listing is-home", sidebar=True, band=band,
                hero_slot=hero_slot)

def build_category(c):
    p = "./"
    items = [a for a in PUBLISHED if a["category"] == c["key"]]
    body = ""
    body += hero(icon(c["key"], "page-icon"), c["label"] + "の記事", c["lead"], len(items))
    if FEAT.get("search"):
        body += SEARCH_BOX
    body += f'''      <section class="section-block" style="margin-top:24px;">
{grid(items, p)}      </section>
'''
    return page(f'{c["label"]}の記事一覧 - {NAME}',
                c["lead"][:110], c["key"], p,
                f'{BASE_URL}/category-{c["key"]}.html', body,
                body_class="is-listing", sidebar=True,
                crumbs=[("ホーム", f"{p}index.html"), (c["label"], None)])

def build_subcategory(c, sc):
    """サブカテゴリーの一覧ページ。記事が1本以上あるときだけ作る。"""
    p = "./"
    items = [a for a in PUBLISHED
             if a["category"] == c["key"] and a.get("sub") == sc["key"]]
    body = hero(icon(c["key"], "page-icon"), sc["label"],
                f'{c["label"]}のうち、{sc["label"]}に分類した記事です。', len(items))
    body += f'''      <section class="section-block" style="margin-top:24px;">
{grid(items, p)}      </section>
'''
    return page(f'{sc["label"]}の記事一覧 - {NAME}',
                f'{NAME}の{sc["label"]}に関する記事一覧です。購入者レビューと仕様をもとに整理しています。',
                c["key"], p,
                f'{BASE_URL}/category-{c["key"]}-{sc["key"]}.html', body,
                body_class="is-listing", sidebar=True, current_sub=sc["key"],
                crumbs=[("ホーム", f"{p}index.html"),
                        (c["label"], f'{p}category-{c["key"]}.html'),
                        (sc["label"], None)])


def build_new():
    """新着一覧。スマホのタブ「NEW」の行き先。"""
    p = "./"
    items = sorted(PUBLISHED, key=lambda a: a.get("date", ""), reverse=True)[:24]
    body = hero(icon("new", "page-icon"), "新着記事", "24時間以内に公開した記事には New が付きます。")
    body += f'''      <section class="section-block" style="margin-top:24px;">
{grid(items, p)}      </section>
'''
    return page(f"新着記事 - {NAME}", f"{NAME}の新着記事一覧です。", "new", p,
                f"{BASE_URL}/new.html", body, body_class="is-listing", sidebar=True,
                crumbs=[("ホーム", f"{p}index.html"), ("新着記事", None)])


def build_ranking():
    """アクセスランキングのページ。スマホのタブ「RANKING」の行き先。"""
    p = "./"
    body = hero(icon("rank", "page-icon"), "アクセスランキング",
                "よく読まれている記事を上位から並べています。", None)
    body += ('      <section class="section-block" style="margin-top:24px;">\n'
             '        <div class="rank-page">\n'
             + rank_panel(p, 10) +
             '        </div>\n      </section>\n')
    return page(f"アクセスランキング - {NAME}",
                f"{NAME}でよく読まれている記事のランキングです。", "ranking", p,
                f"{BASE_URL}/ranking.html", body, body_class="is-listing", sidebar=True,
                crumbs=[("ホーム", f"{p}index.html"), ("アクセスランキング", None)])


def build_search():
    p = "./"
    tags = sorted({t for a in PUBLISHED for t in a.get("tags", [])})
    chips = "".join(f'          <button type="button" class="chip" data-tag="{e(t)}">{e(t)}</button>\n'
                    for t in tags)
    catchips = "".join(f'          <button type="button" class="chip" data-cat="{c["key"]}">'
                       f'{icon(c["key"], "chip-icon")}{e(c["label"])}</button>\n'
                       for c in CATS)
    body = f'''{hero(icon("search", "page-icon"), "サイト内検索", "キーワードやタグから記事を探せます。すべてブラウザ内で動作するため、入力内容が送信されることはありません。")}
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
                "search", p, BASE_URL + "/search.html", body,
                extra_js=f'<script src="./assets/search.js?v={ASSET_V}"></script>\n',
                body_class="is-listing", sidebar=True,
                crumbs=[("ホーム", f"{p}index.html"), ("サイト内検索", None)])

# ============================================================ Worker
def worker_js(maintenance):
    """Cloudflare Workers の入口。中身は tools/worker.template.js。
       やっていることは2つ。

       1. 管理画面の入口をそろえる
          /admin.html を /admin に寄せる。保護は Cloudflare Access が
          /admin を見張って行うので、入口を1つにしておかないと
          片方だけ素通りしてしまう。
       2. メンテナンス表示
          有効なあいだ、全ページを 503 の「準備中」に差し替える。"""
    tpl = io.open(os.path.join(ROOT, "tools", "worker.template.js"),
                  encoding="utf-8").read()
    return tpl.replace("__MAINTENANCE__", "true" if maintenance else "false")


# ============================================================ 固定ページ
def static_pages():
    p = "./"
    # 「最終更新」はビルド日ではなく、規約の文面を変えた日を出す。
    # ビルドのたびに日付が動くと、生成物が毎日変わってしまう。
    today = jp_date(SITE.get("legal_updated")
                    or datetime.date.today().isoformat())
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
      <p>当サイトの記事は、購入者レビューと公開されている製品仕様をもとに整理したものです。運営者が全商品を実際に使用したうえで執筆しているわけではありません。使用環境・体格・好みによって感じ方は異なり、効果や満足度を保証するものではありません。</p>
      <p>引用・参照している購入者レビューは、販売ページに掲載されている一般利用者の意見であり、その正確性を当サイトが保証するものではありません。</p>

      <h2>リンク先のコンテンツについて</h2>
      <p>当サイトからリンクやバナーによって他のサイトに移動した場合、移動先サイトで提供される情報・サービス等について一切の責任を負いません。</p>

      <h2>アフィリエイトプログラムについて</h2>
      <p>当サイトは、Amazonアソシエイト・プログラムをはじめとする各種アフィリエイトプログラムに参加しており、商品を紹介することで紹介料を得ています。ただし、紹介料の有無が記事の評価内容に影響を与えることはありません。</p>

      <p class="updated">最終更新：{today}</p>'''

    about = f'''      <h2>サイトの方針</h2>
      <p>{e(NAME)} は、「{e(TAGLINE)}」をコンセプトに、<strong>購入者レビューと製品仕様をもとに商品を整理して紹介する</strong>メディアです。ガジェットやPC周辺機器から、デスク環境を整える家具、毎日使う生活家電・日用品まで、ジャンルを限定せずに扱っています。</p>
      <p>読んだ人が「買って後悔した」を減らせることを目的にしているため、良い点だけでなく、気になった点や向いていない人についても必ず記載しています。</p>
      <p>購入者レビューと製品仕様をもとに、商品を整理して紹介しています。良い点だけでなく、合わない場面や不満点も省かずに記載しています。</p>

      <h2>記事の作り方</h2>
      <dl>
        <dt>レビューを読み込む</dt>
        <dd>販売ページの購入者レビューを、高評価・低評価の両方から読み取り、繰り返し挙がっている内容を整理しています。</dd>
        <dt>仕様と突き合わせる</dt>
        <dd>レビューの内容がメーカー公表の仕様と整合するかを確認したうえで記載します。</dd>
        <dt>デメリットを必ず書く</dt>
        <dd>不満点は省かずに記載し、可能な限り対処法もあわせて提示します。</dd>
        <dt>比較する</dt>
        <dd>同価格帯の代替候補と並べ、どんな人にどちらが向くかを明示します。</dd>
        <dt>更新する</dt>
        <dd>後継製品の発売や仕様変更があった場合は、記事を更新または追記します。</dd>
      </dl>

      <h2>記事の性質について</h2>
      <p>当サイトの記事は、<strong>運営者が全商品を実際に使用したうえで書いたものではありません</strong>。購入者レビューと公開されている製品仕様を整理・分析した内容が中心です。実機を使用した記事については、その旨を記事内に明記します。</p>
      <p>掲載している内容は購入判断の参考としてご利用いただき、最終的な仕様・価格は必ず販売ページでご確認ください。</p>

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
        body = (                f'      <div class="page-hero"><h1>{e(title)}</h1></div>\n'
                f'      <div class="prose">\n{content}\n      </div>\n')
        out.append((fname, page(f"{title} - {NAME}", desc, "", p,
                                f"{BASE_URL}/{fname}", body,
                                crumbs=[("ホーム", f"{p}index.html"), (title, None)])))

    # メンテナンス画面（features.maintenance が true のときだけ表示される）
    mnote = SITE.get("maintenance_message") or "ただいまサイトの準備・調整を行っています。"
    bodym = f'''      <div class="page-hero" style="text-align:center;">
        <div class="page-hero-head" style="justify-content:center;">
          <span class="page-hero-icon" aria-hidden="true">{icon("tool", "page-icon")}</span><h1>ただいま準備中です</h1>
        </div>
        <p>{e(mnote)}</p>
      </div>
      <div class="prose" style="text-align:center;">
        <p>もうしばらくお待ちください。準備が整いしだい公開します。</p>
        <p class="field-hint">お急ぎのご用件は <a href="mailto:{e(SITE["email"])}">{e(SITE["email"])}</a> までお願いします。</p>
      </div>
'''
    out.append(("maintenance.html",
                page(f"準備中 - {NAME}", "ただいま準備中です。", "", p,
                     f"{BASE_URL}/maintenance.html", bodym,
                     extra_head='<meta name="robots" content="noindex,nofollow">\n')))

    # 404
    body404 = f'''      <div class="page-hero" style="text-align:center;">
        <span class="page-hero-icon" aria-hidden="true">{icon("search", "page-icon")}</span>
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
        endpoint = FEAT.get("contact_form_endpoint", "").strip()
        body = f'''      <div class="page-hero"><h1>お問い合わせ</h1>
        <p>記事内容の誤りのご指摘、掲載・レビューのご依頼、その他のご連絡はこちらからお願いします。内容を確認のうえ、通常3営業日以内にご返信します。</p>
      </div>

      <div class="contact-wrap">
        <form class="contact-form" id="contactForm"
              data-endpoint="{e(endpoint)}" data-mailto="{e(SITE["email"])}"
              action="{e(endpoint) or "mailto:" + e(SITE["email"])}" method="POST" novalidate>

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
            <input type="text" id="cf-name" name="name" autocomplete="name"
                   required maxlength="80" placeholder="山田 太郎">
            <p class="field-error" id="cf-name-err" hidden></p>
          </div>

          <div class="field">
            <label for="cf-email">メールアドレス <span class="req">必須</span></label>
            <input type="email" id="cf-email" name="email" autocomplete="email"
                   required maxlength="120" placeholder="you@example.com">
            <p class="field-hint">ご返信先です。お間違いのないようご確認ください。</p>
            <p class="field-error" id="cf-email-err" hidden></p>
          </div>

          <div class="field">
            <label for="cf-url">該当ページのURL</label>
            <input type="url" id="cf-url" name="page_url" maxlength="300"
                   placeholder="https://{e(SITE["domain"])}/articles/…">
            <p class="field-hint">記事へのご指摘の場合にご記入ください。</p>
          </div>

          <div class="field">
            <label for="cf-body">お問い合わせ内容 <span class="req">必須</span></label>
            <textarea id="cf-body" name="message" rows="9" required maxlength="2000"
                      placeholder="お問い合わせの内容をご記入ください。"></textarea>
            <p class="field-count"><span id="cf-count">0</span> / 2000 文字</p>
            <p class="field-error" id="cf-body-err" hidden></p>
          </div>

          <!-- 迷惑送信よけ。人には見えない欄で、埋まっていたら送らない -->
          <div class="cf-trap" aria-hidden="true">
            <label for="cf-company">会社名（入力しないでください）</label>
            <input type="text" id="cf-company" name="_gotcha" tabindex="-1" autocomplete="off">
          </div>

          <p class="form-note">送信をもって<a href="{p}privacy.html">プライバシーポリシー</a>に同意いただいたものとみなします。
          いただいた個人情報は、ご返信の目的以外には利用しません。</p>

          <button type="submit" class="btn-submit" id="cfSubmit">送信する</button>
          <p class="form-status" id="cfStatus" role="status" aria-live="polite" hidden></p>
        </form>

        <aside class="contact-side">
          <div class="side-tile">
            <p class="side-heading">レビューのご依頼も受け付けています</p>
            <p class="field-hint">メーカー・販売店の方からの掲載・レビューのご依頼を歓迎します。
            上のフォームで「掲載・レビューのご依頼」を選び、次の内容をお知らせください。</p>
            <ul class="contact-list">
              <li>製品名と、公式の製品ページのURL</li>
              <li>訴求したい点と、想定している読者</li>
              <li>サンプル提供の可否と、貸出の場合は期間</li>
              <li>希望する公開時期（あれば）</li>
            </ul>
            <p class="field-hint">当サイトは<strong>購入者レビューと公表仕様をもとに、合わない場面まで書く方針</strong>です。
            提供の有無にかかわらず内容は編集しません。良い点だけを書くご依頼はお受けできません。
            記事化する場合は、提供を受けた旨を明記します。</p>
            <p class="contact-mail"><a href="mailto:{e(SITE["email"])}">{e(SITE["email"])}</a></p>
            <p class="field-hint">フォームがうまく送れない場合は、こちらへ直接お送りください。</p>
          </div>
          <div class="side-tile">
            <p class="side-heading">お答えできないこと</p>
            <ul class="contact-list">
              <li>個別の商品購入・返品に関するお問い合わせ（Amazonカスタマーサービスへご連絡ください）</li>
              <li>製品の故障・修理に関するご相談（メーカーの窓口をご利用ください）</li>
              <li>掲載を確約するご依頼</li>
            </ul>
          </div>
        </aside>
      </div>
'''
        out.append(("contact.html", page(f"お問い合わせ - {NAME}",
                                         f"{NAME}へのお問い合わせフォームです。記事内容のご指摘、掲載のご依頼などを受け付けています。", "", p,
                                         f"{BASE_URL}/contact.html", body,
                                         extra_js=f'<script src="{p}assets/contact.js?v={ASSET_V}" defer></script>\n',
                                         crumbs=[("ホーム", f"{p}index.html"),
                                                 ("お問い合わせ", None)])))
    return out

# ============================================================ 出力
def write(path, content):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    io.open(path, "w", encoding="utf-8").write(content)

def main():
    written = []

    # アイキャッチ自動生成（実写真が無い記事のぶんだけ作る）
    auto_dir = "assets/img/auto"
    os.makedirs(auto_dir, exist_ok=True)
    made = 0
    for a in PUBLISHED:
        if not a.get("thumb"):
            make_visual(a["slug"], a.get("list_title") or a["title"], a["category"],
                        CAT_LABEL.get(a["category"], ""), NAME, auto_dir)
            made += 1
    keep_svg = {a["slug"] + ".svg" for a in PUBLISHED if not a.get("thumb")}
    for f in os.listdir(auto_dir):
        if f.endswith(".svg") and f not in keep_svg:
            os.remove(os.path.join(auto_dir, f))

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
    write("new.html", build_new()); written.append("new.html")
    write("ranking.html", build_ranking()); written.append("ranking.html")
    for c in CATS:
        f = f'category-{c["key"]}.html'
        write(f, build_category(c)); written.append(f)
        # サブカテゴリーは記事があるものだけページを作る
        for sc in c.get("sub", []):
            if not any(a["category"] == c["key"] and a.get("sub") == sc["key"]
                       for a in PUBLISHED):
                continue
            f = f'category-{c["key"]}-{sc["key"]}.html'
            write(f, build_subcategory(c, sc)); written.append(f)

    # カテゴリーを組み替えたときに、古いカテゴリーページが残らないようにする
    live = {os.path.basename(f) for f in written if f.startswith("category-")}
    import glob as _glob
    for old in _glob.glob("category-*.html"):
        if os.path.basename(old) not in live:
            os.remove(old)
            print(f"   🗑  {old}（古いカテゴリー）")
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
            "icon": a.get("icon", "📦"),
            "thumb": a.get("thumb") or f'assets/img/auto/{a["slug"]}.svg',
            "tags": a.get("tags", []), "date": a["date"],
            "url": f'articles/{a["slug"]}.html'} for a in PUBLISHED]
    write("search.json", json.dumps(idx, ensure_ascii=False, separators=(",", ":")))
    written.append("search.json")

    # sitemap / robots / Cloudflare 用の設定ファイル
    def mod(a):
        return a.get("updated") or a.get("date") or ""

    # 一覧ページの更新日は、そこに載っている記事の最新日にする。
    # ビルドした日を入れると「毎日全ページが更新された」という嘘になり、
    # 生成物も日替わりで変わってしまう。
    newest = max((mod(a) for a in PUBLISHED), default=datetime.date.today().isoformat())

    def cat_mod(key, sub=None):
        ds = [mod(a) for a in PUBLISHED
              if a["category"] == key and (sub is None or a.get("sub") == sub)]
        return max(ds, default=newest)

    urls = [(BASE_URL + "/", "1.0", newest)]
    urls += [(f'{BASE_URL}/new.html', "0.7", newest),
             (f'{BASE_URL}/ranking.html', "0.7", newest)]
    urls += [(f'{BASE_URL}/category-{c["key"]}.html', "0.8", cat_mod(c["key"])) for c in CATS]
    urls += [(f'{BASE_URL}/category-{c["key"]}-{sc["key"]}.html', "0.6",
              cat_mod(c["key"], sc["key"]))
             for c in CATS for sc in c.get("sub", [])
             if any(a["category"] == c["key"] and a.get("sub") == sc["key"]
                    for a in PUBLISHED)]
    urls += [(f'{BASE_URL}/articles/{a["slug"]}.html', "0.9", mod(a)) for a in PUBLISHED]
    static = ["about.html", "privacy.html", "disclaimer.html"]
    if FEAT.get("contact_form"):
        static.append("contact.html")
    urls += [(f"{BASE_URL}/{f}", "0.3", newest) for f in static]
    urls = [(public_url(u), pr, d) for u, pr, d in urls]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u, pr, d in urls:
        sm += f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{d}</lastmod>\n    <priority>{pr}</priority>\n  </url>\n"
    sm += "</urlset>\n"
    write("sitemap.xml", sm); written.append("sitemap.xml")
    # 管理画面は拡張子ありでも無しでも開けるので、両方を止める
    # 管理画面は build.py が生成しないので、資産のURLだけ版を打ち直す。
    # これをしないと、直したCSSがブラウザのキャッシュに阻まれて反映されない。
    apath = os.path.join(ROOT, "admin.html")
    if os.path.exists(apath):
        a = io.open(apath, encoding="utf-8").read()
        a2 = re.sub(r'(\./assets/admin\.(?:css|js))(\?v=[a-f0-9]+)?',
                    lambda m: f"{m.group(1)}?v={ASSET_V}", a)
        if a2 != a:
            io.open(apath, "w", encoding="utf-8").write(a2)
            print("   admin.html の資産URLを更新しました")

    write("robots.txt",
          "User-agent: *\n"
          "Allow: /\n"
          "Disallow: /admin.html\n"
          "Disallow: /admin\n"
          f"\nSitemap: {BASE_URL}/sitemap.xml\n")
    written.append("robots.txt")

    # ---- Cloudflare Pages 用の設定ファイル -------------------------------

    # wrangler.jsonc：Cloudflare Workers（静的アセット配信）の設定。
    #   デプロイは `npx wrangler deploy` が読む。これが無いと
    #   「デプロイするものが分からない」としてビルドが失敗する。
    hs = SITE.get("hosting", {})
    maint = bool(FEAT.get("maintenance"))
    assets = {
        # リポジトリ直下がそのまま公開ディレクトリ。
        # 配信したくないファイルは .assetsignore で除く。
        "directory": "./",
        # 見つからないURLでは 404.html を返す（真っ白なページを出さない）
        "not_found_handling": "404-page",
        # /foo.html を /foo に寄せる既定の挙動。canonical と sitemap も
        # これに合わせて拡張子なしで出している（public_url を参照）。
        "html_handling": "auto-trailing-slash",
    }
    # Worker は常に置く。管理画面のログイン判定をサーバー側で行うため。
    assets["binding"] = "ASSETS"
    # すべてのリクエストを Worker に通す。
    # 経路ごとの指定（配列）は Cloudflare 側のバージョンによって
    # 解釈が変わることがあるため、単純な true にしておく。
    assets["run_worker_first"] = True
    wrangler = {
        "name": hs.get("worker_name") or SITE["domain"].split(".")[0],
        "compatibility_date": hs.get("compatibility_date", "2026-08-24"),
        "main": "worker.js",
        "assets": assets,
    }
    write("worker.js", worker_js(maint))
    written.append("worker.js")
    write("wrangler.jsonc",
          "// このファイルは build.py が生成します。直接編集しないでください。\n"
          "// 設定を変えるときは content/site.json の hosting を編集します。\n"
          + json.dumps(wrangler, ensure_ascii=False, indent=2) + "\n")
    written.append("wrangler.jsonc")

    # .assetsignore：配信しないもの。ソースや作業用ファイルを公開しない。
    #   content/ は管理画面が読むので残す（公開リポジトリなので秘密は無い）。
    write(".assetsignore", "\n".join([
        "# ここに書いたものは配信されない（build.py が生成）",
        ".git",
        ".github",
        ".gitignore",
        ".DS_Store",
        ".assetsignore",
        "wrangler.jsonc",
        "build.py",
        "README.md",
        "package.json",
        "package-lock.json",
        "AmazonExport",
        "docs",
        "tools",
        "node_modules",
        ".npm-cache",
        "__pycache__",
        ".wrangler",
        "",
    ]))
    written.append(".assetsignore")

    # _headers：ハッシュ付きの資産は長期キャッシュ、HTMLは毎回確認。
    #   あわせて最低限の防御ヘッダーを付ける。
    write("_headers", "\n".join([
        "/*",
        "  X-Content-Type-Options: nosniff",
        "  Referrer-Policy: strict-origin-when-cross-origin",
        "  X-Frame-Options: SAMEORIGIN",
        "  Permissions-Policy: geolocation=(), microphone=(), camera=()",
        "",
        "# URLに ?v= が付くので、中身が変われば別のURLになる。",
        "# 管理画面の admin.css / admin.js にも build.py が版を打つ。",
        "/assets/*",
        "  Cache-Control: public, max-age=31536000, immutable",

        "",
        "/*.html",
        "  Cache-Control: public, max-age=0, must-revalidate",
        "",
        "# 管理画面は Worker 側でも止めているが、念のため二重に掛ける",
        "/admin.html",
        "  X-Robots-Tag: noindex, nofollow",
        "",
        "/admin",
        "  X-Robots-Tag: noindex, nofollow",
        "",
    ]))
    written.append("_headers")

    print(f"\n✅ ビルド完了：{len(written)} ファイル（アイキャッチ自動生成 {made} 枚）")
    print(f"   公開記事 {len(PUBLISHED)} 本 / 下書き {len(ARTICLES)-len(PUBLISHED)} 本")
    th, ready = feature_ready()
    if ready:
        print(f"   📌 特集を作る段（{th}本ごと）に達したジャンル:")
        for label, n, stage in ready:
            print(f"      ・{label}（{n}本 → {stage}段目）")
        print("      $ python3 tools/feature_plan.py --write で下書きを作れます")
    print(f"   ドメイン {SITE['domain']} / GA {'設定済' if GA else '未設定'} / GSC {'設定済' if GSC else '未設定'}")
    print(f"   お問い合わせフォーム: {'ON' if FEAT.get('contact_form') else 'OFF（メールリンクのみ）'}")

if __name__ == "__main__":
    main()
