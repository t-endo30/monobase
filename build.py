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
import json, io, os, re, html, shutil, sys, datetime, hashlib, urllib.parse
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
ADS      = SITE.get("ads", {}) or {}
PROMOS   = SITE.get("promos", {}) or {}
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
                   "score": a.get("rating", {}).get("score") or 0,
                   "date": a.get("date", "")}
                  for a in PUBLISHED],
    }
    return html.escape(json.dumps(data, ensure_ascii=False), quote=True)


ASSOC_TAG = SITE.get("amazon", {}).get("associate_tag", "").strip()
CAT_LABEL = {c["key"]: c["label"] for c in CATS}
CAT_ICON  = {c["key"]: c["icon"]  for c in CATS}

PUBLISHED = sorted([a for a in ARTICLES if a.get("published")],
                   key=lambda a: a.get("date", ""), reverse=True)

# ブランドマーク：ドット絵の「M」と、その下に沿う開いたダンボール箱。
# 16×16 のマス目を「1マス＝1色」で持つ（(x, y, 幅) のリスト）。
# ここ1か所を直すだけで、ヘッダーのSVG・favicon・OGP画像の見た目が揃う。
#   line … Mの字（白）
#   box  … 箱の面（オレンジ）
#   in   … 箱の開いた口（濃いオレンジ）
#   seam … 箱がダンボールだと分かるように入れた、テープの黒いライン
LOGO_CELLS = {
    "line": [(1,2,2),(13,2,2),(1,3,3),(12,3,3),(1,4,4),(11,4,4),(1,5,2),(4,5,3),
             (9,5,3),(13,5,2),(1,6,2),(5,6,6),(13,6,2),(1,7,2),(6,7,4),(13,7,2),
             (1,8,2),(7,8,2),(13,8,2),(1,9,2),(13,9,2),(1,10,2),(13,10,2),
             (1,11,2),(13,11,2),(1,12,2),(13,12,2),(1,13,2),(13,13,2),
             (1,14,2),(13,14,2)],
    "box":  [(4,9,1),(11,9,1),(4,10,2),(10,10,2),(5,11,1),(10,11,1),
             (5,12,6),(5,13,6),(5,14,6)],
    "in":   [(6,11,4)],
    "seam": [(5,12,6),(7,13,2),(7,14,2)],
}
LOGO_COLOR_VAR = {
    "line": "var(--mk-line,#fff)",
    "box":  "var(--mk-box,#FF9900)",
    "in":   "var(--mk-in,#C25E00)",
    "seam": "var(--mk-seam,#1A1006)",
}


def _logo_path_d(cells):
    return "".join(f"M{x} {y}h{w}v1h-{w}z" for x, y, w in cells)


def logo_svg(size="100%"):
    """ブランドマークのSVG（16×16グリッド）。header() と favicon/OGP 生成で共用する。"""
    paths = "".join(
        f'<path fill="{LOGO_COLOR_VAR[key]}" d="{_logo_path_d(LOGO_CELLS[key])}"/>'
        for key in ("line", "box", "in", "seam"))
    return (f'<svg viewBox="0 0 16 16" width="{size}" height="{size}" '
            f'shape-rendering="crispEdges" aria-hidden="true">{paths}</svg>')


LOGO_SVG_INNER = logo_svg()

def e(s):
    return html.escape(str(s), quote=True)


def amazon_tagged(url):
    """AmazonのURLにアソシエイトIDを付ける。
       商品ページだけでなく、トップやセール会場のURLでも成果は計上されるので、
       Amazonへ送るリンクは1本残らずここを通す。
       すでに tag= が入っているものは触らない（手で貼った別IDを壊さない）。"""
    u = (url or "").strip()
    if not u or not ASSOC_TAG:
        return u
    if "amazon.co.jp" not in u and "amzn.to" not in u:
        return u
    if re.search(r"[?&]tag=", u):
        return u
    sep = "&" if "?" in u else "?"
    frag = ""
    if "#" in u:                       # #以降の前に足す
        u, frag = u.split("#", 1)
        frag = "#" + frag
    return f"{u}{sep}tag={ASSOC_TAG}{frag}"


# セール告知のリンクもAmazonへ送るので、アソシエイトIDを付ける
SALES_JSON = html.escape(json.dumps(
    [dict(x, url=amazon_tagged(x.get("url", "")))
     for x in (SITE.get("sales") or {}).get("items", [])],
    ensure_ascii=False), quote=True)


def amazon_link(a):
    """ASIN があればアソシエイトタグ付きリンクを組み立てる。
       無ければ手入力の amazon_url を使う（こちらにもタグを付ける）。"""
    asin = (a.get("asin") or "").strip().upper()
    if asin:
        return amazon_tagged(f"https://www.amazon.co.jp/dp/{asin}")
    return amazon_tagged(a.get("amazon_url") or "https://www.amazon.co.jp/")


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


# ============================================================ 広告（AdSense）
# Googleが配るコードは書き換えない（規約）。こちらで決めるのは
#   ・読み込みタグを置く場所（<head>）
#   ・広告ユニットを差し込む位置
# の2つだけ。枠の周りに自前の器やラベルを付けるのは認められている。
def ads_on():
    return bool(ADS.get("enabled") and (ADS.get("client") or "").strip())


def ads_meta():
    """所有確認のメタタグ。審査中や広告を止めているあいだも出しておく。"""
    c = (ADS.get("client") or "").strip()
    return f'<meta name="google-adsense-account" content="{e(c)}">\n' if c else ""


def ads_head():
    """読み込みタグ。Googleが配る形のまま置く。"""
    if not ads_on():
        return ""
    return ('<script async src="https://pagead2.googlesyndication.com/pagead/js/'
            f'adsbygoogle.js?client={e(ADS["client"].strip())}"\n'
            '     crossorigin="anonymous"></script>\n')


# ASPの広告コードの先頭。ここが出てきたら、次の広告の始まりとみなす。
PROMO_HEADS = re.compile(
    r'(?=<a[^>]+href="https?://(?:px\.a8\.net|ck\.jp\.ap\.valuecommerce\.com'
    r'|af\.moshimo\.com|rpx\.a8\.net))', re.I)


def split_codes(text):
    """広告コードのかたまりを、1件ずつに分ける。

       「---」だけの行があればそこで切る。無ければ、ASPのリンクの
       始まりを見て自動で切る。まとめてコピーしてきたものを、そのまま
       貼れるようにするため（計測用の1×1画像は、直前のコードに付く）。"""
    text = (text or "").strip()
    if not text:
        return []
    parts = [t.strip() for t in re.split(r"(?m)^\s*-{3,}\s*$", text) if t.strip()]
    if len(parts) > 1:
        return parts
    auto = [t.strip() for t in PROMO_HEADS.split(text) if t.strip()]
    return auto or [text]


def promo_slot(where, cat="", cls=""):
    """ASP（A8.net・バリューコマースなど）で取得した広告リンクを置く枠。
       配られたコードは書き換えず、そのまま流し込む（規約）。
       決めるのは「どこに出すか」と「どのカテゴリーの記事に出すか」だけ。

       1つの枠に複数のコードを入れておくと、表示のたびに1つを選ぶ。
       選ばれなかったコードは <template> の中に置いたままなので、
       画像も計測用の画像も読み込まれない（表示回数が水増しされない）。

       cats が空の案件は全記事に出す。記事のカテゴリーが一致した案件だけを
       その記事に出すことで、内容と関係のない広告が並ぶのを避ける。"""
    items = [x for x in (PROMOS.get("items") or [])
             if str(x.get("where") or "") == where and (x.get("html") or "").strip()]
    if cat:
        items = [x for x in items
                 if not x.get("cats") or cat in (x.get("cats") or [])]
    if not items:
        return ""
    label = e(str(PROMOS.get("label") or "PR"))
    out = ""
    for x in items:
        c = f" {cls}" if cls else ""
        codes = split_codes(x["html"])
        if len(codes) == 1:
            body = f'          <div class="promo-body">{codes[0]}</div>\n'
        else:
            tpl = "".join(f'          <template class="promo-item">{t}</template>\n'
                          for t in codes)
            body = ('          <div class="promo-body"></div>\n'
                    + tpl
                    + f'          <noscript><div class="promo-body">{codes[0]}</div></noscript>\n')
        rot = ' data-rotate="1"' if len(codes) > 1 else ""
        out += (f'        <aside class="promo-slot{c}"{rot} aria-label="広告">\n'
                f'          <span class="ad-label">{label}</span>\n'
                + body +
                f'        </aside>\n')
    return out


def ad_slot(name, cls=""):
    """広告ユニット1枠。mode=auto のときは何も置かない
       （どこに出すかはGoogle側が決めるため）。
       枠の高さをあらかじめ空けておき、読み込みで文章が飛ばないようにする。"""
    if not ads_on() or str(ADS.get("mode", "manual")) != "manual":
        return ""
    slot = str((ADS.get("slots") or {}).get(name) or "").strip()
    if not slot:
        return ""
    label = e(str(ADS.get("label") or "スポンサーリンク"))
    c = f" {cls}" if cls else ""
    return (f'        <aside class="ad-slot{c}" aria-label="広告">\n'
            f'          <span class="ad-label">{label}</span>\n'
            f'          <ins class="adsbygoogle" style="display:block"\n'
            f'               data-ad-client="{e(ADS["client"].strip())}"\n'
            f'               data-ad-slot="{e(slot)}"\n'
            f'               data-ad-format="auto"\n'
            f'               data-full-width-responsive="true"></ins>\n'
            f'          <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>\n'
            f'        </aside>\n')


def og_image(img):
    """OGP画像の絶対URL。SNSと検索結果のカードに出る絵。
       相対パスのままだと読まれないので、必ず絶対URLにする。
       自動生成のSVGは多くのSNSが解釈しないため、実画像があるときだけ出す。"""
    u = (img or "").strip()
    if not u or u.endswith(".svg"):
        return ""
    if u.startswith("http"):
        return u
    return f'{BASE_URL}/{u.lstrip("./")}'


def head(title, desc, current, p, canonical, extra="", body_class="", image="",
         noindex=False):
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
    # 検索結果のページは検索エンジンに載せない。中身が毎回変わるうえ、
    # 「検索結果の検索結果」はGoogleが載せない方針のため、
    # クロールの予算を記事のほうへ回す。
    norobots = ('<meta name="robots" content="noindex,follow">\n'
                if noindex else "")
    oi = og_image(image) or f"{BASE_URL}/assets/img/og-default.jpg"
    ogimg = ""
    if oi:
        ogimg = (f'<meta property="og:image" content="{e(oi)}">\n'
                 f'<meta property="og:image:width" content="1200">\n'
                 f'<meta property="og:image:height" content="630">\n'
                 f'<meta name="twitter:image" content="{e(oi)}">\n')
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
<link rel="alternate" type="application/rss+xml" title="{e(NAME)}" href="{BASE_URL}/feed.xml">
<link rel="icon" href="{p}assets/img/favicon.svg" type="image/svg+xml">
<link rel="icon" href="{p}assets/img/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{p}assets/img/apple-touch-icon.png">
{gsc}{norobots}{ads_meta()}<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:site_name" content="{e(NAME)}">
<meta property="og:url" content="{e(public_url(canonical))}">
{ogimg}<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DotGothic16&family=Noto+Sans+JP:wght@400;500;700;900&display=swap">
<link rel="stylesheet" href="{p}assets/style.css?v={ASSET_V}">
{extra}{ga}{ads_head()}</head>
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
            f'          <span class="today-head">\n'
            f'            <span class="today-title"></span>\n'
            f'            <span class="today-cat cat-badge"></span>\n'
            f'          </span>\n'
            f'          <span class="today-rating" hidden></span>\n'
            f'          <span class="today-catch"></span>\n'
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


def breadcrumb_ld(items):
    """パンくずの構造化データ。items = [(ラベル, 絶対URL), ...]
       画面のパンくずと同じ並びを、検索エンジンにも読める形で渡す。"""
    items = [(t, u) for t, u in items if t]
    if len(items) < 2:
        return ""
    ld = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": t, "item": public_url(u)}
            for i, (t, u) in enumerate(items, start=1)
        ],
    }
    return ('<script type="application/ld+json">'
            + json.dumps(ld, ensure_ascii=False) + '</script>\n')


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


def _header_count_text():
    """ヘッダーに出す「◯◯など◯カテゴリーで◯記事公開中」。
       JSが無くても読めるよう、既定の文言をサーバー側で入れておく。"""
    names = [c["label"] for c in CATS
             if c["key"] != "feature"
             and any(a["category"] == c["key"] for a in PUBLISHED)]
    n_cat = len(names)
    n_pub = len(PUBLISHED)
    cats_json = html.escape(json.dumps(names, ensure_ascii=False), quote=True)
    head = "／".join(names[:2])
    default = (f"{head} など {n_cat} カテゴリー・{n_pub} 記事公開中"
               if head else f"{n_cat} カテゴリー・{n_pub} 記事公開中")
    return names, n_cat, n_pub, cats_json, default


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

    _cn_names, _cn_ncat, _cn_npub, _cn_json, _cn_default = _header_count_text()

    return f'''{ICON_SPRITE}
<header class="site-header">
  <div class="container header-inner">
    <div class="header-side" aria-hidden="true"></div>
    <div class="site-brand">
      <a class="site-title" href="{p}index.html" aria-label="{e(NAME)}">
        <span class="brand-mark" aria-hidden="true">{LOGO_SVG_INNER}</span>
        <span class="brand-name">{e(NAME)}</span>
      </a>
      <div class="site-tagline hero-count" data-cats='{_cn_json}' data-n-cat="{_cn_ncat}" data-n-pub="{_cn_npub}">{e(_cn_default)}</div>
    </div>
    <button class="nav-toggle" id="navToggle" aria-expanded="false" aria-controls="globalNav" aria-label="メニューを開く">
      <span></span><span></span><span></span>
    </button>
    <nav class="global-nav" id="globalNav" aria-label="メニュー">
      <ul class="nav-links">
        <li><a href="{p}index.html">ホーム</a></li>
        {search_link}<li class="sp-only-link"><a href="{p}sitemap.html">サイトマップ</a></li>
        <li><a href="{p}about.html">運営者情報</a></li>
        <li class="sp-only-link"><a href="{p}editorial-policy.html">記事作成方針</a></li>
        <li class="sp-only-link"><a href="{p}advertising.html">広告掲載について</a></li>
        {contact_nav}
      </ul>
    </nav>
  </div>
</header>

<!-- カテゴリーナビゲーション -->
<nav class="cat-nav" aria-label="カテゴリー">
  <div class="container">
    <button type="button" class="cat-nav-arrow is-prev" aria-label="カテゴリーを左へ" hidden><span aria-hidden="true"></span></button>
    <ul class="cat-nav-list">
{nav}    </ul>
    <button type="button" class="cat-nav-arrow is-next" aria-label="カテゴリーを右へ" hidden><span aria-hidden="true"></span></button>
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
    <div class="footer-cols">
      <div class="footer-col">
        <p class="footer-col-heading">サイト</p>
        <ul class="footer-col-list">
          <li><a href="{p}index.html">ホーム</a></li>
          <li><a href="{p}search.html">サイト内検索</a></li>
          <li><a href="{p}sitemap.html">サイトマップ</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <p class="footer-col-heading">サイトについて</p>
        <ul class="footer-col-list">
          <li><a href="{p}about.html">運営者情報</a></li>
          <li><a href="{p}editorial-policy.html">記事作成方針</a></li>
          <li><a href="{p}advertising.html">広告掲載について</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <p class="footer-col-heading">お問い合わせ</p>
        <ul class="footer-col-list">
          <li>{contact_link}</li>
          <li><a href="{p}privacy.html">プライバシーポリシー</a></li>
          <li><a href="{p}disclaimer.html">免責事項</a></li>
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

def main_block(body, p, current="", current_sub="", sidebar=False, hero_slot="",
               side_search_on=True):
    """本文の器。一覧ページではPC幅のときだけ左にカテゴリー一覧を置く。
       スマホでは幅が足りないので出さず、ハンバーガーメニュー側に集約する。"""
    if not sidebar:
        return ('\n<main id="top" class="layout">\n  <div class="container">\n'
                + body + '  </div>\n</main>\n\n')
    tree = cat_tree(p, current, current_sub, "side")
    # 3カラムのときは「本日のお勧めのモノ」を左、検索を右に置く。
    # 2カラムに縮んだときは右列が消えるので、検索は左に残す。
    # 両方を書き出し、どちらを見せるかはCSSの幅で切り替える。
    # 検索ページ自身には出さない。同じ画面に検索窓が2つ並んでも迷うだけ。
    want = FEAT.get("search") and side_search_on
    search_l = (side_search(p, "only-2col") if want else "")
    search_r = (side_search(p, "only-3col") if want else "")
    return ('\n<main id="top" class="layout has-side">\n'
            '  <div class="container layout-grid">\n'
            + hero_slot +
            '    <div class="side-col">\n'
            + search_l +
            '    <aside class="side-nav side-tile" aria-label="カテゴリー">\n'
            '      <p class="side-heading">CATEGORIES</p>\n'
            + tree +
            '    </aside>\n'
            '    </div>\n'
            '    <div class="layout-main">\n'
            + body +
            '    </div>\n'
            '    <div class="side-rank">\n'
            + rank_panel(p, 10) + search_r
            + promo_slot("side", current, "is-side") + ad_slot("side", "is-side")
            + '    </div>\n'
            '  </div>\n</main>\n\n')


def page(title, desc, current, p, canonical, body, sticky_url=None, extra_head="", extra_js="", body_class="", crumbs=None, current_sub="", sidebar=False, band="", hero_slot="", side_search_on=True, image="", noindex=False):
    return (head(title, desc, current, p, canonical, extra_head, body_class, image,
                 noindex)
            + header(current, p, crumbs, current_sub, band)
            + main_block(body, p, current, current_sub, sidebar, hero_slot,
                         side_search_on)
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
    """一覧の記事タイル。カテゴリー名はタグの行ではなく、見出しの右上に
       枠で囲んで置く（トップのタブの中の並びと同じ見え方にそろえる）。
       タグの行には、記事のタグと種類バッジだけが残る。"""
    tags = "".join(f'<span class="tag">{e(t)}</span>' for t in a.get("tags", [])[:1])
    cls = "card is-lead" if lead else "card"
    return f'''        <article class="{cls} reveal" data-cat="{a["category"]}" data-slug="{e(a["slug"])}" data-date="{e(a.get("date",""))}">
          <div class="card-thumb is-auto"><span class="card-flags" aria-hidden="true"></span>{thumb(a, p)}</div>
          <div class="card-body">
            <div class="card-tags">{tags}{kind_badge(a)}</div>
            <div class="card-head">
              <h3 class="card-title"><a class="card-stretch" href="{p}articles/{e(a["slug"])}.html">{title_lines(a.get("list_title") or a["title"])}</a></h3>
              <span class="cat-badge">{e(CAT_LABEL.get(a["category"], ""))}</span>
            </div>
            {card_rating(a)}
            <p class="card-desc">{e(a.get("excerpt",""))}</p>
            <span class="card-link" aria-hidden="true">詳細を見る</span>
          </div>
        </article>
'''

def dot_date(iso):
    """掲載日を「2026.08.31」の形で返す。タイルの右下に小さく置く用。"""
    t = str(iso or "").strip()
    return t[:10].replace("-", ".") if len(t) >= 10 else ""


def article_row(a, p, no=None, badge_on_thumb=False):
    """一覧の1行。トップのタブ（読まれている記事／本日のお勧めのモノ）と
       同じ形にそろえてある。

         ┌────────┐ 見出し
         │[カテゴリ│ ★★★★☆ 4.2
         │  ]写真  │ 一言の説明
         └────────┘                    2026.08.31

       写真は行の高さいっぱいに伸ばす（＝一言の下の線とそろう）。
       カテゴリーは見出しの右上（badge_on_thumb のときは写真の右上）、
       日付は右下。どちらもそれまで空いていた場所なので、行の高さは
       増えない。中身が同じ形なので、assets/main.js が組み立てる
       ランキングの行とも見た目が一致する。
       badge_on_thumb … True なら新着一覧ページと同じく、カテゴリーの札を
       常に写真の上に乗せる。"mobile" ならスマホ幅のときだけ写真の上、
       PC幅では今までどおり見出しの横（両方をマークアップに入れておき、
       CSSの画面幅で出し分ける）。"""
    sc = 0
    try:
        sc = float(a.get("rating", {}).get("score") or 0)
    except (TypeError, ValueError):
        sc = 0
    rating = ("" if sc <= 0 else
              f'<span class="arow-rating" aria-label="評価 {sc:g} / 5">'
              f'<span aria-hidden="true">{stars(sc)}</span>'
              f'<b>{sc:g}</b></span>')
    catch = (f'<span class="arow-catch">{e(a.get("excerpt",""))}</span>'
             if a.get("excerpt") else "")
    d = dot_date(a.get("date"))
    date = f'<span class="arow-date">{e(d)}</span>' if d else ""
    rank = (f'<span class="arow-no arow-no-{no}">{no}</span>' if no else "")
    src, _ = visual_path(a, p)
    title = a.get("list_title") or a["title"]
    cat_label = e(CAT_LABEL.get(a["category"], ""))
    if badge_on_thumb == "mobile":
        thumb_badge = f'<span class="cat-badge is-thumb-badge">{cat_label}</span>'
        head_badge = f'<span class="cat-badge is-head-badge">{cat_label}</span>'
    elif badge_on_thumb:
        thumb_badge = f'<span class="cat-badge">{cat_label}</span>'
        head_badge = ""
    else:
        thumb_badge = ""
        head_badge = f'<span class="cat-badge">{cat_label}</span>'
    return (
        f'          <li class="arow" data-cat="{a["category"]}" '
        f'data-slug="{e(a["slug"])}" data-date="{e(a.get("date",""))}">\n'
        f'            <a class="arow-link" href="{p}articles/{e(a["slug"])}.html">\n'
        f'              <span class="arow-thumb">'
        f'<img src="{e(src)}" alt="" loading="lazy" decoding="async" '
        f'width="1200" height="430">'
        f'<span class="card-flags" aria-hidden="true"></span>{rank}{thumb_badge}</span>\n'
        f'              <span class="arow-body">\n'
        f'                <span class="arow-head">'
        f'<span class="arow-title">{e(title)}</span>'
        f'{head_badge}</span>\n'
        f'                {rating}{catch}{date}\n'
        f'              </span>\n'
        f'            </a>\n'
        f'          </li>\n')


def article_rows(items, p, numbered=False, badge_on_thumb=False):
    """記事の縦並び。トップの新着と、新着一覧ページで使う。"""
    if not items:
        return ('      <p class="empty-state">記事は準備中です。'
                '<a href="' + p + 'index.html">トップページ</a>から他の記事をご覧ください。</p>\n')
    rows = "".join(article_row(a, p, (i + 1) if numbered else None, badge_on_thumb)
                   for i, a in enumerate(items))
    return '        <ol class="arow-list">\n' + rows + '        </ol>\n'


def grid(items, p):
    if not items:
        return ('      <p class="empty-state">このカテゴリーの記事は準備中です。'
                '<a href="' + p + 'index.html">トップページ</a>から他の記事をご覧ください。</p>\n')
    return '      <div class="card-grid">\n' + "\n".join(card(a, p) for a in items) + '      </div>\n'

MSM = SITE.get("moshimo") or {}

SHOPS = [
    ("amazon",  "Amazon",            "amazon_url"),
    ("rakuten", "楽天市場",           "rakuten_url"),
    ("yahoo",   "Yahoo!ショッピング",  "yahoo_url"),
]


def moshimo_url(shop, target):
    """もしもアフィリエイト経由のリンクを組み立てる。
       IDが登録されていないショップは、そのまま商品ページへ送る。
       もしもの形式：af.moshimo.com/af/c/click?a_id=…&url=<商品URL>"""
    if shop == "amazon":
        # Amazon だけは Amazon アソシエイトの直リンクを使う。
        # もしも経由にすると、こちらのタグでの成果にならない。
        return target
    ids = MSM.get(shop) or {}
    if not all(ids.get(k) for k in ("a_id", "p_id", "pc_id", "pl_id")):
        return target
    return ("https://af.moshimo.com/af/c/click"
            f'?a_id={ids["a_id"]}&p_id={ids["p_id"]}'
            f'&pc_id={ids["pc_id"]}&pl_id={ids["pl_id"]}'
            f'&url={urllib.parse.quote(target, safe="")}')


def shop_links(a):
    """記事に入っている販売先を、ショップごとに返す。
       URLが入っていないショップは返さない（ボタンを出さない）。"""
    out = []
    for shop, label, key in SHOPS:
        target = (a.get(key) or "").strip()
        if shop == "amazon":
            # ASINからURLを作る／手入力のURLにもタグを付ける
            target = amazon_link(a) if (not target or a.get("asin")) else amazon_tagged(target)
        if not target:
            continue
        out.append((shop, label, moshimo_url(shop, target)))
    return out


# 1記事に置くボタン列は3か所まで。
#   上部（目次の下）と下部（まとめ）は位置を固定。
#   中間の1か所だけ、記事ごとに置き場所を選べる（cta_position）。
# 商品画像つきのリンクカードはこの3か所には数えない。
_cta_mid_used = [False]   # 中間を出したか。render_article() で戻す


def cta_mid_at(a):
    """中間ボタンの置き場所。記事の cta_position で指定する。
         "spec"      … スペック表の下（既定）
         "section:N" … N番目の見出しの直後
         "voices"    … 「気になる点と、その対策」の直後
         "none"      … 中間は置かない
       指定が読めないときは既定に倒す。"""
    v = str(a.get("cta_position") or "spec").strip()
    if v.startswith("section:"):
        n = v.split(":", 1)[1].strip()
        return ("section", int(n)) if n.isdigit() else ("spec", 0)
    if v in ("spec", "voices", "none"):
        return (v, 0)
    return ("spec", 0)


def shop_buttons_mid(a, where, idx=0, note=""):
    """中間の置き場所に来たときだけボタンを出す。1記事につき1回まで。"""
    if _cta_mid_used[0]:
        return ""
    want, wi = cta_mid_at(a)
    if want != where or (where == "section" and wi != idx):
        return ""
    out = shop_buttons(a, note)
    if out:
        _cta_mid_used[0] = True
    return out


def shop_buttons(a, note=""):
    """販売先のボタンを並べる。1つしか無ければ1つだけ出す。"""
    links = shop_links(a)
    if not links:
        return ""
    btns = ""
    for shop, label, href in links:
        btns += (f'          <a class="btn-shop is-{shop}" href="{e(href)}" '
                 f'target="_blank" rel="nofollow sponsored noopener">'
                 f'{icon("cart", "btn-icon")}<span>{e(label)}で見る</span></a>\n')
    n = f" is-n{min(len(links), 3)}"
    return (f'        <div class="shop-cta{n}">\n{btns}        </div>\n'
            + (f'        <p class="cta-note">{e(note)}</p>\n' if note else ""))


def product_card(a, p, eager=False, with_img=True):
    """商品画像つきのリンクカード。写真・商品名・販売先ボタンをまとめる。
       本文中のボタン3か所とは別枠なので、数には数えない。

       with_img=False のときは写真を出さない。すぐ上のアイキャッチと
       同じ写真が並ぶと、スマホでは同じ画像が2枚重なって見えるため。"""
    links = shop_links(a)
    if not links:
        return ""
    # 実写真が最優先。無ければカード一覧と同じ自動生成SVGを使う。
    # 画像が無いという理由だけで購入導線を落とさない。
    img = a.get("thumb") or a.get("eyecatch") or ""
    src = (p + e(img)) if img else visual_path(a, p)[0]
    # 商品名。無ければ記事タイトルの「｜」より前を使う（後半は補足なので落とす）
    name = a.get("product_name") or a.get("title", "").split("｜")[0].strip()
    first = links[0][2]
    btns = ""
    for shop, label, href in links:
        btns += (f'            <a class="btn-shop is-{shop}" href="{e(href)}" '
                 f'target="_blank" rel="nofollow sponsored noopener">'
                 f'{icon("cart", "btn-icon")}<span>{e(label)}</span></a>\n')
    lazy = "" if eager else 'loading="lazy" '
    note = a.get("image_ai") and '<span class="pc-ai">イメージ（AI生成）</span>' or ""
    thumb = f'''
          <a class="prod-thumb" href="{e(first)}" target="_blank" rel="nofollow sponsored noopener">
            <img src="{src}" alt="{e(name)}" {lazy}decoding="async" width="800" height="450">
          </a>''' if with_img else ""
    cls = "prod-card" if with_img else "prod-card is-noimg"
    return f'''        <div class="{cls}">{thumb}
          <div class="prod-body">
            <p class="prod-name">{e(name)}</p>{note}
            <div class="prod-links is-n{min(len(links), 3)}">
{btns}            </div>
            <p class="prod-note">価格・在庫は変動します。最新情報はリンク先でご確認ください。</p>
          </div>
        </div>
'''


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


def card_rating(a):
    """一覧カード用の小さな星評価。score が無い記事では何も出さない。"""
    sc = 0
    try:
        sc = float(a.get("rating", {}).get("score") or 0)
    except (TypeError, ValueError):
        sc = 0
    if sc <= 0:
        return ""
    return (f'<span class="card-rating" aria-label="評価 {sc} / 5">'
            f'<span class="cr-stars" aria-hidden="true">{stars(sc)}</span>'
            f'<span class="cr-score">{sc:g}</span></span>')

# ============================================================ 記事ページ
def li_html(x):
    """箇条書きの1項目を組む。ライターは文字列でも
       {"title": ..., "text": ...} でも返してくるので、両方受ける。
       辞書のまま文字列に混ぜると、Pythonの辞書表記が
       そのまま記事に出てしまうため、ここで必ず通す。"""
    if isinstance(x, dict):
        t = str(x.get("title") or "").strip()
        b = str(x.get("text") or x.get("body") or "").strip()
        if t and b:
            return f'<b class="li-t">{mark(t)}</b><span class="li-b">{mark(b)}</span>'
        return mark(t or b)
    return mark(str(x))


_MARK_RE = __import__("re").compile(r"==([^=]+)==")


def mark(s):
    """本文中の ==重要語== を蛍光ペン風マーカーに変える。
       ライターは <strong>/<em> と ==…== だけで強調を指定する。"""
    if not s:
        return s
    return _MARK_RE.sub(r'<mark class="hl">\1</mark>', str(s))


def paras(v, cls=""):
    """文字列でも配列でも受け取り、段落に組む。
       ライターの地の文はここを通す。改行だけの段落は捨てる。"""
    if not v:
        return ""
    items = v if isinstance(v, list) else [v]
    c = f' class="{cls}"' if cls else ""
    return "".join(f"          <p{c}>{mark(t)}</p>\n" for t in items if str(t).strip())


def official_link(a):
    """メーカー公式の製品ページへの参照リンク。
       販売リンク（アフィリエイト）ではないので sponsored は付けず、
       nofollow の通常リンクとして出す。仕様の一次情報の出どころを示す。"""
    url = (a.get("official_url") or "").strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return ""
    label = e(a.get("official_label") or "メーカー公式サイトで仕様を確認する")
    return (f'          <p class="official-ref">'
            f'<a href="{e(url)}" target="_blank" rel="nofollow noopener">'
            f'{label} <span aria-hidden="true">↗</span></a>'
            f'<span class="official-ref-note">'
            f'（この記事の仕様は公式の公表値を基にしています）</span></p>\n')


# ---- 過去に書いた記事への差し込みリンク ----------------------
# 本文に、すでに書いてある商品の名前が出てきたら、その記事へ送る。
# 手で貼り直す運用にすると必ず貼り漏れるので、組み立てのときに入れる。

_NAME_TAIL = re.compile(
    r"[\s\u3000]*(徹底|正直)?(レビュー|口コミ(分析)?|評価|選び方|比較|"
    r"買い時カレンダー|ガイド)$")
# 「加湿器の選び方」→「加湿器の」のように助詞が残ると、文の途中で
# 切れたリンクになる。末尾の助詞は落とす。
_NAME_JOSHI = re.compile(r"[のなにをはがでとへも]+$")


# 一般名として使ってはいけない語。「口コミ」「上位機」のような
# どの記事にも出てくる言葉をリンクにすると、本文が青くなるだけで
# 押す理由が伝わらない。
_TAIL_STOP = {"口コミ", "上位機", "評判", "本音", "違い", "使い方", "選び方",
              "電気代", "静音性", "実力", "実際", "感想", "比較", "まとめ",
              "おすすめ", "分析", "評価", "レビュー", "ガイド"}


def product_key(a):
    """記事が扱っている物の名前。タイトルの「｜」より前から、
       末尾の「レビュー」「口コミ」などと助詞を落として取り出す。
       「口コミ評価」のように重なっているときは、無くなるまで落とす。"""
    t = (a.get("list_title") or a.get("title", "")).split("｜")[0].strip()
    while True:
        t2 = _NAME_JOSHI.sub("", _NAME_TAIL.sub("", t).strip()).strip()
        if t2 == t:
            return t
        t = t2


def product_keys(a):
    """その記事に当てる語。商品名そのものと、その末尾の一般名。

       本文は「象印 CK-AX08 蒸気レスケトル」と型番まで書くより、
       「蒸気レスケトル」と書くほうが多い。商品名だけで待っていると
       ほとんど当たらないので、末尾の一般名も拾う。
       英数字を含む語（型番・ブランド）は一般名として使わない。"""
    k = product_key(a)
    keys = [k] if k else []
    tail = k.split()[-1] if k else ""
    if (tail and tail != k and len(tail) >= 3
            and tail not in _TAIL_STOP
            and not re.search(r"[A-Za-z0-9]", tail)):
        keys.append(tail)
    return keys


def _link_targets(cur_slug, p):
    """差し込み先の一覧。長い名前から先に当てる（短い名前が
       長い名前の一部を食ってしまわないようにするため）。"""
    out = []
    for x in PUBLISHED:
        if x["slug"] == cur_slug:
            continue
        for k in product_keys(x):
            # 短すぎる語は、関係のない文にまで当たるので使わない。
            # 漢字・かなは1文字あたりの情報量が多いので3文字から、
            # 英字まじりは4文字から拾う。
            least = 3 if not re.search(r"[A-Za-z0-9]", k) else 4
            if len(k) < least:
                continue
            out.append((k, f'{p}articles/{e(x["slug"])}.html',
                        x.get("list_title") or x["title"]))
    out.sort(key=lambda t: -len(t[0]))
    return out


# 差し込むのは、地の文（段落と箇条書き）の中だけ。
#   ・見出し・表・ボタン・図の説明には入れない
#   ・すでにリンクの中には入れない（押し先が二重になる）
#   ・関連記事のタイルや商品名の札など、それ自体が別のリンクに
#     なっている部品にも入れない（class で見分ける）
_SKIP_TAGS = ("a", "h1", "h2", "h3", "h4", "h5", "script", "style",
              "table", "button", "figcaption", "summary")
_SKIP_CLASS = ("card-", "prod-", "spec", "cta", "next-", "fi-", "tag",
               "btn", "flag", "badge", "arow", "rank-", "today-", "deal")
# 地の文が入っているのはここだけ。商品カードや関連記事のタイルは
# この外にあるか、上の class で弾かれる。
_BODY_CLASS = "article-body"
_OK_TEXT_TAGS = ("p", "li")
_TAG_RE = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*)>")
_CLASS_RE = re.compile(r'class="([^"]*)"')
_VOID = {"br", "img", "hr", "input", "meta", "link", "source", "wbr"}


def link_past_articles(html_body, cur_slug, p, limit=5):
    """本文のHTMLを流し見して、まだリンクになっていない地の文に
       過去記事の商品名が出てきたら、そこを1回だけリンクにする。
       同じ記事へは1回まで、1本の記事で {limit} 本まで。"""
    targets = _link_targets(cur_slug, p)
    if not targets:
        return html_body
    used, made = set(), [0]
    stack = []          # [(タグ名, 入れてよい場所か, 本文の器か)]

    def linkable():
        """いま見ている場所が、本文の地の文の中かどうか。
           ・article-body の中にいる（商品カードや関連記事の外）
           ・段落か箇条書きの中にいる
           ・避けたいタグ／部品の中にはいない
           の3つがそろったときだけ差し込む。"""
        inside_body = False
        in_text = False
        for name, ok, is_body in stack:
            if not ok:
                return False
            if is_body:
                inside_body = True
            if name in _OK_TEXT_TAGS:
                in_text = True
        return inside_body and in_text

    def link_text(text):
        for key, url, title in targets:
            if made[0] >= limit or key in used:
                continue
            i = text.find(key)
            if i < 0:
                continue
            used.add(key)
            made[0] += 1
            a = (f'<a class="past-link" href="{url}" '
                 f'title="{e(title)}">{e(key)}</a>')
            return text[:i] + a + link_text(text[i + len(key):])
        return text

    out, pos = [], 0
    for m in _TAG_RE.finditer(html_body):
        if m.start() > pos:
            chunk = html_body[pos:m.start()]
            out.append(link_text(chunk) if linkable() else chunk)
        name, attrs = m.group(2).lower(), m.group(3)
        if not m.group(1) and name not in _VOID and not attrs.rstrip().endswith("/"):
            cm = _CLASS_RE.search(attrs)
            cls = cm.group(1) if cm else ""
            # class で弾くのは、本文の器（article-body）に入ってから。
            # 本文を包んでいる外側の器（card-surface など）まで
            # 名前で弾くと、中身がまるごと対象外になってしまう。
            in_body = any(is_body for _, _, is_body in stack)
            ok = name not in _SKIP_TAGS
            if ok and in_body and any(w in cls for w in _SKIP_CLASS):
                ok = False
            stack.append((name, ok, _BODY_CLASS in cls))
        elif m.group(1):
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][0] == name:
                    del stack[i:]
                    break
        out.append(m.group(0))
        pos = m.end()
    tail = html_body[pos:]
    out.append(link_text(tail) if linkable() else tail)
    return "".join(out)


def render_article(a):
    _cta_mid_used[0] = False
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

    # 商品カード（写真つきの購入リンク）は結論の上に置く。
    # 読者が最初に見る位置に、商品そのものと買える場所を出す。
    # 特集（複数商品の比較）は商品を1つに絞れないので、上には置かない。
    top_card = (product_card(a, p, eager=True, with_img=not a.get("thumb"))
                if kind_of(a) == "review" else "")

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
    elif not top_card:
        # 写真も商品カードも無いときだけ、色帯で見出しと本文を分ける
        add('        <div class="article-accent" aria-hidden="true"></div>\n')

    add(top_card)

    # 結論ボックス（結論ファースト：評価・3行まとめ・GOOD/BAD・購入ボタンを冒頭に凝縮）
    if a.get("summary"):
        items = "".join(f'              <li>{li_html(s)}</li>\n' for s in a["summary"])
        rating = ""
        sc = a.get("rating", {}).get("score") or 0
        if sc:
            rating = f'''          <div class="rating-row">
            <span class="stars">{stars(sc)}</span>
            <span class="rating-score">{sc}</span>
            <span class="rating-label">/ 5.0（{e(a["rating"].get("breakdown",""))}）</span>
          </div>
'''
        gb = ""
        pros3 = [x for x in (a.get("pros") or []) if x][:3]
        cons3 = [x for x in (a.get("cons") or []) if x][:3]
        if pros3 and cons3:
            pl = "".join(f'                <li>{li_html(x)}</li>\n' for x in pros3)
            cl = "".join(f'                <li>{li_html(x)}</li>\n' for x in cons3)
            gb = f'''          <div class="summary-gb">
            <div class="sgb-box sgb-good">
              <div class="sgb-head">{icon("good", "hd-icon")} GOOD</div>
              <ul>
{pl}              </ul>
            </div>
            <div class="sgb-box sgb-bad">
              <div class="sgb-head">{icon("bad", "hd-icon")} BAD</div>
              <ul>
{cl}              </ul>
            </div>
          </div>
'''
        cta = shop_buttons(a, "※ 価格・在庫は変動します。最新情報はリンク先でご確認ください。")
        add(f'''        <section class="summary-box">
          <div class="summary-head">{a.get("verdict_title","結論")}</div>
{rating}          <div class="summary-body">
            <div class="summary-3lines">3行でわかる結論</div>
            <ul class="summary-list">
{items}            </ul>
          </div>
{gb}{cta}        </section>
''')

    # 目次
    toc = []
    if a.get("good_for", {}).get("items"): toc.append(("sec-goodfor", "こんな人におすすめ"))
    if a.get("not_for", {}).get("items"): toc.append(("sec-notfor", "こんな人にはおすすめしない"))
    if a.get("highlights", {}).get("items"): toc.append(("sec-highlights", "この商品の強み"))
    if a.get("scenes"):                   toc.append(("sec-scenes", "この商品で変わる生活シーン"))
    if a.get("pros") or a.get("cons"):    toc.append(("sec-proscons", "メリットとデメリット"))
    if a.get("products"):                 toc.append(("sec-products", "比較した商品"))
    if a.get("spec", {}).get("rows"):     toc.append(("spec", "スペック比較表"))
    elif official_link(a):                toc.append(("spec", "メーカー公式情報"))
    for i, sec in enumerate(a.get("sections", []), start=1):
        toc.append((f"sec-note{i}", sec.get("heading", "")))
    if a.get("voices"):                   toc.append(("sec-voice", "共通の不満点と対処法"))
    if a.get("next_problem", {}).get("items"): toc.append(("sec-next", "次に困りそうなこと"))
    if a.get("faq"):                      toc.append(("sec-faq", "よくある質問"))
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

    # 購入リンクは結論ボックス内（冒頭）に移動済み。
    # 結論ボックスに summary が無い記事のときだけ、ここで補う。
    if not a.get("summary"):
        add(shop_buttons(a, "※ 価格・在庫は変動します。最新情報はリンク先でご確認ください。"))

    add('        <div class="article-body">\n')
    add(paras(a.get("lead")))

    # 結論の直後に「誰に向くか」を対で置く（結論ファースト）。
    gf = a.get("good_for", {})
    if gf.get("items"):
        gitems = "".join(
            f'''              <li>
                <span class="goodfor-t">{mark(e(x.get("title",""))) if isinstance(x, dict) else li_html(x)}</span>
                {f'<span class="goodfor-d">{mark(x.get("text",""))}</span>' if isinstance(x, dict) and x.get("text") else ""}
              </li>\n'''
            for x in gf["items"])
        add(f'''          <h2 id="sec-goodfor">こんな人におすすめ</h2>
          <div class="goodfor-box">
            <div class="goodfor-head">{icon("good", "hd-icon")} この使い方なら、買って後悔しにくい</div>
            <div class="goodfor-body">
              <p>{e(gf.get("intro",""))}</p>
              <ul class="goodfor-list">
{gitems}              </ul>
            </div>
          </div>
''')
        add(paras(gf.get("after")))

    # 「誰に向かないか」。good_for と対にして読ませる。
    nf = a.get("not_for", {})
    if nf.get("items"):
        items = "".join(f'              <li>{li_html(x)}</li>\n' for x in nf["items"])
        add(f'''          <h2 id="sec-notfor">こんな人にはおすすめしない</h2>
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

    # 良い点を、はっきり見せる枠。
    hl = a.get("highlights", {})
    if hl.get("items"):
        add(f'''          <h2 id="sec-highlights">{hl.get("heading", "この商品の強み")}</h2>
''')
        add(paras(hl.get("intro")))
        add('          <div class="hl-grid">\n')
        for i, it in enumerate(hl["items"], start=1):
            add(f'''            <div class="hl-card">
              <span class="hl-num">{i}</span>
              <h3 class="hl-title">{mark(it.get("title",""))}</h3>
              <p class="hl-text">{mark(it.get("text",""))}</p>
            </div>
''')
        add('          </div>\n')
        add(paras(hl.get("after")))

    # 2. この商品で変わる「実際の生活シーン」
    if a.get("scenes"):
        add('          <h2 id="sec-scenes">この商品で変わる「実際の生活シーン」</h2>\n')
        add(paras(a.get("scenes_intro")))
        add('          <div class="scenes">\n')
        for i, sc in enumerate(a["scenes"], start=1):
            add(f'''            <div class="scene">
              <span class="scene-num">{i}</span>
              <div class="scene-body">
                <h3 class="scene-title">{mark(sc.get("title",""))}</h3>
                <p>{mark(sc.get("text",""))}</p>
              </div>
            </div>
''')
        add('          </div>\n')
        add(paras(a.get("scenes_after")))

    # メリット / デメリット
    if a.get("pros") or a.get("cons"):
        pros = "".join(f'                <li>{li_html(p_)}</li>\n' for p_ in a.get("pros", []))
        cons = "".join(f'                <li>{li_html(c_)}</li>\n' for c_ in a.get("cons", []))
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

    # 広告は本文の中ほどに1枠だけ。購入ボタンの近くには置かない
    # （どちらを押しているか分からなくなるため。規約上もリスクになる）。
    add(ad_slot("article_mid", "is-inline"))

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
        add(official_link(a))
        add(shop_buttons_mid(a, "spec", note="セール対象になっている場合があります"))
    elif official_link(a):
        # 比較表が無い記事でも、公式リンクは出す
        add('          <h2 id="spec">メーカー公式情報</h2>\n')
        add(official_link(a))

    # ライターの地の文。見出し＋段落の自由記述で、表では伝わらない
    # 判断の根拠や使いどころを書く。
    for i, sec in enumerate(a.get("sections", []), start=1):
        add(f'          <h2 id="sec-note{i}">{mark(e(sec.get("heading","")))}</h2>\n')
        add(paras(sec.get("paras")))
        if sec.get("point"):
            add(f'''          <div class="callout callout-point">
            <span class="callout-label">{icon("check", "callout-icon")} ここがポイント</span>
            <p>{mark(sec["point"])}</p>
          </div>
''')
        if sec.get("warn"):
            add(f'''          <div class="callout callout-warn">
            <span class="callout-label">{icon("warn", "callout-icon")} 購入前の注意点</span>
            <p>{mark(sec["warn"])}</p>
          </div>
''')
        if sec.get("aside"):
            add(f'''          <div class="personal-note">
            <span class="pn-label">{e(sec.get("aside_label","レビューを読み込んで見えたこと"))}</span>
            <p>{mark(sec["aside"])}</p>
          </div>
''')
        add(shop_buttons_mid(a, "section", i,
                             "※ 価格・在庫は変動します。最新情報はリンク先でご確認ください。"))

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
        add(shop_buttons_mid(a, "voices",
                             "※ 価格・在庫は変動します。最新情報はリンク先でご確認ください。"))

    # 6. 運営者の実体験コラム
    if a.get("personal_note"):
        add(f'''          <div class="personal-note">
            <span class="pn-label">レビューから見えたこと</span>
            <p>{a["personal_note"]}</p>
          </div>
''')


    # 特集記事の商品カードは、比較表を読んだあとの本文中に置く
    if not top_card:
        add(product_card(a, p))

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

    # よくある質問（FAQ）。読者が購入前に迷う点を、仕様と口コミから答える。
    faq = [q for q in (a.get("faq") or [])
           if q.get("q") and q.get("a")]
    if faq:
        add('          <h2 id="sec-faq">よくある質問</h2>\n')
        for q in faq:
            add(f'''          <h3>{mark(e(q["q"]))}</h3>
{paras(q["a"])}''')

    # この商品を扱っている特集への導線
    add(featured_in(a, p))

    # まとめ
    if a.get("conclusion"):
        add(f'''          <h2 id="sec-conclusion">{a.get("conclusion_title","まとめ")}</h2>
''')
        add(paras(a["conclusion"]))
        add(shop_buttons(a, "※ 価格・在庫は変動します。最新情報はリンク先でご確認ください。"))
        add(f'''        <div class="cta-wrap" style="margin-top:-10px;">
          <a class="btn-sub" href="{p}category-{cat}.html">同じカテゴリーの記事を見る</a>
        </div>
''')

    add('        </div>\n      </article>\n')

    # シェアボタン。外部からの流入（SNS経由の訪問・被リンク）を増やすため、
    # 読み終えた人がそのまま共有できる導線を記事の直後に置く。
    # クエリの値は urllib.parse.quote でURLエンコードしてから、
    # HTML属性として安全な形に e() で escape する（&の連結はここで足す）。
    _share_text = urllib.parse.quote(a.get("list_title") or a["title"], safe="")
    _share_url_q = urllib.parse.quote(public_url(url), safe="")
    share_url_plain = e(public_url(url))
    add(f'''      <div class="share-row" aria-label="この記事をシェアする">
        <span class="share-label">この記事をシェア</span>
        <a class="share-btn is-x" href="{e(f"https://twitter.com/intent/tweet?text={_share_text}&url={_share_url_q}")}" target="_blank" rel="noopener" aria-label="Xでシェア">X</a>
        <a class="share-btn is-line" href="{e(f"https://social-plugins.line.me/lineit/share?url={_share_url_q}")}" target="_blank" rel="noopener" aria-label="LINEでシェア">LINE</a>
        <a class="share-btn is-hatena" href="{e(f"https://b.hatena.ne.jp/entry/panel/?url={_share_url_q}")}" target="_blank" rel="noopener" aria-label="はてなブックマークに追加">B!</a>
        <button type="button" class="share-btn is-copy" data-copy-url="{share_url_plain}">リンクをコピー</button>
      </div>
''')

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

    # 広告はページのいちばん下にもう1枠。関連記事より下に置いて、
    # 記事を読み終えた人の目に入る位置にする。
    add(promo_slot("article_end", cat))
    add(ad_slot("article_end"))

    # 構造化データ。検索結果に日付・書き手・画像を出すための材料。
    ld = {
      "@context": "https://schema.org", "@type": "Article",
      "headline": a["title"][:110],       # Googleは110字までしか読まない
      "description": a.get("description", ""),
      "datePublished": a["date"], "dateModified": a.get("updated") or a["date"],
      "author": {"@type": "Person", "name": SITE["author"],
                 "url": f"{BASE_URL}/about"},
      "publisher": {"@type": "Organization", "name": NAME,
                    "url": BASE_URL},
      "mainEntityOfPage": {"@type": "WebPage", "@id": public_url(url)},
      "inLanguage": "ja",
    }
    oi = og_image(a.get("thumb"))
    if oi:
        ld["image"] = [oi]
    if a.get("tags"):
        ld["keywords"] = "、".join(a["tags"])

    # レビュー記事の評価点。検索結果に★の評点を出すための材料。
    # 実際に自分たちで採点した1件ぶんの評価なので Review（AggregateRating
    # ではない）で出す。他社のレビューを寄せ集めたように見せないため。
    review_ld = None
    score = 0
    try:
        score = float((a.get("rating") or {}).get("score") or 0)
    except (TypeError, ValueError):
        score = 0
    if kind_of(a) == "review" and score > 0:
        product_name = a.get("product_name") or a.get("title", "").split("｜")[0]
        # 記事タイトル末尾の「レビュー」「口コミ」等は、商品名ではないので落とす
        product_name = re.sub(
            r"[\s　]*(徹底|正直)?(レビュー|口コミ(分析)?|評価|選び方|比較)$",
            "", product_name).strip()
        review_ld = {
            "@context": "https://schema.org", "@type": "Review",
            "itemReviewed": {"@type": "Product", "name": product_name},
            "reviewRating": {"@type": "Rating", "ratingValue": score,
                             "bestRating": "5", "worstRating": "1"},
            "author": {"@type": "Person", "name": SITE["author"]},
            "publisher": {"@type": "Organization", "name": NAME},
            "datePublished": a["date"],
        }
        if oi:
            review_ld["itemReviewed"]["image"] = oi

    # パンくずの構造化データ。検索結果に「ホーム › 家電 › 記事名」と出る。
    crumb_ld = breadcrumb_ld([
        ("ホーム", f"{BASE_URL}/"),
        (CAT_LABEL.get(cat, ""), f"{BASE_URL}/category-{cat}.html"),
        (a.get("list_title") or a["title"], public_url(url)),
    ])
    extra_js = ('<script type="application/ld+json">'
                + json.dumps(ld, ensure_ascii=False) + '</script>\n'
                + crumb_ld)
    if review_ld:
        extra_js += ('<script type="application/ld+json">'
                     + json.dumps(review_ld, ensure_ascii=False) + '</script>\n')

    # FAQ の構造化データ。検索結果に質問と回答が出ることがある。
    faq_items = [q for q in (a.get("faq") or []) if q.get("q") and q.get("a")]
    if faq_items:
        def _txt(v):
            v = " ".join(v) if isinstance(v, list) else str(v)
            return re.sub(r"<[^>]+>", "", v).strip()
        faq_ld = {
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{
                "@type": "Question", "name": _txt(q["q"]),
                "acceptedAnswer": {"@type": "Answer", "text": _txt(q["a"])},
            } for q in faq_items],
        }
        extra_js += ('<script type="application/ld+json">'
                     + json.dumps(faq_ld, ensure_ascii=False) + '</script>\n')

    # 本文が出来上がってから、過去に書いた記事への導線を差し込む。
    # 組み立ての最後にまとめてやるので、貼り漏れが起きない。
    body_html = link_past_articles("".join(b), slug, p)

    return page(f'{a["title"]} - {NAME}', a.get("description") or a.get("excerpt",""),
                cat, p, url, body_html,
                sticky_url=(shop_links(a)[0][2] if shop_links(a) else None),
                extra_js=extra_js,
                # 記事ページはサイドを出さず、本文だけを広く使う
                sidebar=False, body_class="is-article", current_sub=a.get("sub", ""),
                image=a.get("thumb", ""),
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

SEARCH_HINT = "例：加湿器、腰痛"


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
            <input type="search" name="q" placeholder="例：加湿器、腰痛" aria-label="サイト内検索">
            <button type="submit">検索</button>
          </form>
        </div>
'''

SEARCH_BOX = '''      <form class="searchbox" action="./search.html" method="get" role="search">
        <input type="search" name="q" placeholder="キーワードで記事を探す" aria-label="サイト内検索">
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
    {"key": "feature",    "on": True},
    {"key": "new",        "on": True},
    {"key": "ranking",    "on": True},
    {"key": "categories", "on": True},
]

# 管理画面に出す名前。ここに無いものは並べ替えの対象にしない。
TOP_LABEL = {
    "hero":       "見出しバナー",
    "feature":    "特集",
    "new":        "新着記事",
    "ranking":    "よく読まれている記事（スマホのみ）",
    "categories": "カテゴリーから探す",
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


def news_rail(items, p, limit=4):
    """トップの新着。横送りのカルーセルをやめて縦に並べる。

       横送りは、画面に1枚しか映らないぶん「何本あるのか」が
       見えない。縦に並べれば、指を下ろすだけで次が出る。
       出すのは4件。5件目は下半分を薄く透過させ、続きがあることを
       枠のかたちだけで示す（CSS）。続きは「もっと見る」で新着一覧へ送る。
       1行の形は article_row()＝トップのタブやランキングと同じ。"""
    return ('      <section class="section-block news-list-block">\n'
            '        <div class="tile-card">\n'
            '          <p class="tile-card-head">新着記事</p>\n'
            + article_rows(items[:limit + 1], p, badge_on_thumb="mobile") +
            '        </div>\n'
            '        <a class="arow-more" href="' + p + 'new.html">'
            + icon("new", "btn-icon") + 'もっと見る'
            '<span class="arow-more-arrow" aria-hidden="true"></span></a>\n'
            '      </section>\n')


def mobile_ranking(p, today_limit=5):
    """スマホにはPCのようなサイドが無く、ランキングへ行く手立てがタブだけに
       なる。トップにも上位を出して、読まれている記事から入れるようにする。

       ここは2枚を切り替えて見せる。左が実際に読まれている順、右がその日の
       お勧め。どちらも「次に何を読むか」を出す枠なので、縦に2つ並べるより
       切り替えたほうがスマホの縦を食わない。中身はどちらも assets/main.js。

       表示は4件、5件目は下半分を薄く透過させ（CSS）、続きがあることを
       枠のかたちだけで示す。「すべて見る」のボタンは、注目アイテム枠と
       同じボタンデザイン（.deals-btn 相当のCSS）にそろえる。"""
    return ('      <section class="section-block is-mobile-only pick-tabs">\n'
            '        <div class="pt-tabs" role="tablist" aria-label="トップの記事の出し分け">\n'
            '          <button type="button" class="pt-tab is-on" role="tab"'
            ' id="ptTabRank" aria-controls="ptPanelRank" aria-selected="true">読まれている記事</button>\n'
            '          <button type="button" class="pt-tab" role="tab"'
            ' id="ptTabToday" aria-controls="ptPanelToday" aria-selected="false" tabindex="-1">本日のお勧めのモノ</button>\n'
            '        </div>\n'
            '        <div class="pt-stage">\n'
            '        <div class="pt-panel" id="ptPanelRank" role="tabpanel" aria-labelledby="ptTabRank">\n'
            + rank_panel(p, today_limit) +
            f'          <a class="pt-more" href="{p}ranking.html">ランキングをすべて見る'
            '<span class="pt-more-arrow" aria-hidden="true"></span></a>\n'
            '        </div>\n'
            '        <div class="pt-panel" id="ptPanelToday" role="tabpanel" aria-labelledby="ptTabToday" hidden>\n'
            f'          <ol class="today-list" data-today-limit="{today_limit}"></ol>\n'
            f'          <a class="pt-more" href="{p}new.html">お勧め記事をもっと見る'
            '<span class="pt-more-arrow" aria-hidden="true"></span></a>\n'
            '        </div>\n'
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
    return ('      <section class="section-block cf-block">\n'
            '        <div class="tile-card">\n'
            '          <p class="tile-card-head">カテゴリーから探す</p>\n'
            '          <div class="rail-wrap">\n'
            '            <button type="button" class="rail-arrow is-prev" aria-label="前のカテゴリーへ" hidden><span aria-hidden="true"></span></button>\n'
            '            <div class="rail cf-rail">\n'
            '              <div class="cf-row">\n' + rows +
            '              </div>\n'
            '            </div>\n'
            '            <button type="button" class="rail-arrow is-next" aria-label="次のカテゴリーへ" hidden><span aria-hidden="true"></span></button>\n'
            '          </div>\n'
            '        </div>\n'
            '      </section>\n')

POLICY = [
    ("01", "購入者レビューと公表仕様を突き合わせています",
     "良い評価だけでなく、低い評価に繰り返し出てくる内容まで読み込み、仕様と照らして整理しています。"),
    ("02", "「合わない場面」を先に書きます",
     "どんな製品にも向かない環境があります。買ってから気づく条件を、記事の前半ではっきり書くようにしています。"),
    ("03", "広告収益の有無で内容は変えません",
     "アソシエイトによる収益を獲得する可能性がありますが、掲載の可否や評価は独立して判断しています。"),
]


# POLICY の中身（このサイトの読み方）は editorial-policy.html に出す。
# 組み立ては static_pages() 側で行う（policy_items）。


def build_index():
    p = "./"
    feat = [a for a in PUBLISHED if a.get("featured")][:3]
    latest = PUBLISHED[:10]
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
    # 見出しの文言は content/site.json（管理画面のサイト設定）で決める。
    # accent に入れた語だけ、マーカーを引いた見た目にする。
    # 文字送りの演出はやめ、最初から全文を出す（枠はオレンジの線で囲み、
    # 背景は下の記事が薄く透けるくらいの不透明度にする＝CSS側の .hero-tile）。
    hero_tile = (
        '      <section class="hero-tile">\n'
        '        <h1 class="fit-line hero-strong">良い点も、不満点も。</h1>\n'
        '        <p class="hero-strong">買う前に「リアル」が見える商品紹介サイト</p>\n'
        '        <p class="hero-desc">ネット上の膨大な口コミから独自に分析。<br>'
        '人それぞれに合う・合わないの基準を整理し記事を作成しています。</p>\n'
        '        <div class="hero-cta-row">\n'
        f'          <a class="btn-hero" href="{p}editorial-policy.html">このサイトの活用法'
        '<span class="btn-hero-arrow" aria-hidden="true">›</span></a>\n'
        f'          <a class="btn-hero" href="{p}ranking.html">人気の記事を見る'
        '<span class="btn-hero-arrow" aria-hidden="true">›</span></a>\n'
        '        </div>\n'
        + (SEARCH_TILE if FEAT.get("search") else "") +
        '      </section>\n')
    # トップに置く区画。並び順と表示・非表示は content/site.json の
    # layout.top で決める（管理画面からドラッグして入れ替えられる）。
    blocks = {
        "new":        lambda: news_rail(latest, p),
        "feature":    lambda: feature_cards(p),
        "ranking":    lambda: mobile_ranking(p),
        "categories": lambda: cat_finder(p),
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
    # サイトそのものの構造化データ。検索結果にサイト名と検索窓を出す材料。
    site_ld = [
        {"@context": "https://schema.org", "@type": "WebSite",
         "name": NAME, "url": BASE_URL + "/",
         "inLanguage": "ja",
         "description": SITE["description"],
         "potentialAction": {
             "@type": "SearchAction",
             "target": {"@type": "EntryPoint",
                        "urlTemplate": f"{BASE_URL}/search?q={{search_term_string}}"},
             "query-input": "required name=search_term_string"}},
        {"@context": "https://schema.org", "@type": "Organization",
         "name": NAME, "url": BASE_URL + "/",
         "description": SITE["description"],
         "email": SITE.get("email", "")},
    ]
    ld_js = "".join('<script type="application/ld+json">'
                    + json.dumps(x, ensure_ascii=False) + "</script>\n"
                    for x in site_ld)
    return page(f"{NAME}｜{TAGLINE}", SITE["description"], "all", p, BASE_URL + "/", body,
                body_class="is-listing is-home", sidebar=True, band=band,
                hero_slot=hero_slot, extra_js=ld_js,
                image=(PUBLISHED[0].get("thumb") if PUBLISHED else ""))

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
                image=(items[0].get("thumb") if items else ""),
                extra_js=breadcrumb_ld([
                    ("ホーム", f"{BASE_URL}/"),
                    (c["label"], f'{BASE_URL}/category-{c["key"]}.html')]),
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
                image=(items[0].get("thumb") if items else ""),
                extra_js=breadcrumb_ld([
                    ("ホーム", f"{BASE_URL}/"),
                    (c["label"], f'{BASE_URL}/category-{c["key"]}.html'),
                    (sc["label"], f'{BASE_URL}/category-{c["key"]}-{sc["key"]}.html')]),
                crumbs=[("ホーム", f"{p}index.html"),
                        (c["label"], f'{p}category-{c["key"]}.html'),
                        (sc["label"], None)])


def build_new():
    """新着一覧。スマホのタブ「NEW」の行き先。"""
    p = "./"
    items = sorted(PUBLISHED, key=lambda a: a.get("date", ""), reverse=True)[:24]
    body = hero(icon("new", "page-icon"), "新着記事", "24時間以内に公開した記事には New が付きます。")
    body += ('      <section class="section-block" style="margin-top:24px;">\n'
             '        <div class="rank-box">\n'
             '          <p class="rank-heading">LATEST ARTICLES</p>\n'
             + article_rows(items, p, badge_on_thumb=True) +
             '        </div>\n'
             '      </section>\n')
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


def build_sitemap():
    """人が読むサイトマップ。ハンバーガーメニューからの行き先。
       検索エンジン向けの sitemap.xml とは別物で、こちらは
       「どこに何があるか」を一枚で見渡すための一覧。"""
    p = "./"
    body = hero(icon("cats", "page-icon"), "サイトマップ",
                "サイト内のページを一覧にまとめています。", None)

    # ---- 主要ページ ----
    main_links = [("ホーム", f"{p}index.html"), ("新着記事", f"{p}new.html"),
                  ("アクセスランキング", f"{p}ranking.html")]
    if FEAT.get("search"):
        main_links.append(("サイト内検索", f"{p}search.html"))
    main_links += [("運営者情報", f"{p}about.html"),
                   ("記事作成方針", f"{p}editorial-policy.html"),
                   ("広告掲載について", f"{p}advertising.html"),
                   ("プライバシーポリシー", f"{p}privacy.html"),
                   ("免責事項", f"{p}disclaimer.html")]
    if FEAT.get("contact_form"):
        main_links.append(("お問い合わせ", f"{p}contact.html"))
    items = "".join(f'          <li><a href="{e(u)}">{e(t)}</a></li>\n'
                    for t, u in main_links)
    body += ('      <section class="section-block sm-block">\n'
             '        <h2 class="section-heading">主要なページ</h2>\n'
             f'        <ul class="sm-links">\n{items}        </ul>\n'
             '      </section>\n')

    # ---- カテゴリーと、その中の記事 ----
    for c in CATS:
        arts = [a for a in PUBLISHED if a["category"] == c["key"]]
        if not arts:
            continue
        subs = ""
        for sc in c.get("sub", []):
            n = len([a for a in arts if a.get("sub") == sc["key"]])
            if not n:
                continue
            subs += (f'          <li><a href="{p}category-{c["key"]}-{sc["key"]}.html">'
                     f'{e(sc["label"])}<span class="sm-num">{n}</span></a></li>\n')
        rows = "".join(
            f'          <li><a href="{p}articles/{e(a["slug"])}.html">'
            f'{e(a.get("list_title") or a["title"])}</a></li>\n' for a in arts)
        body += ('      <section class="section-block sm-block">\n'
                 '        <h2 class="section-heading">'
                 f'{icon(c["key"])}{e(c["label"])}</h2>\n'
                 f'        <p class="sm-all"><a href="{p}category-{c["key"]}.html">'
                 f'{e(c["label"])}の記事をすべて見る（{len(arts)}）</a></p>\n'
                 + (f'        <ul class="sm-links sm-subs">\n{subs}        </ul>\n' if subs else "")
                 + f'        <ul class="sm-links sm-arts">\n{rows}        </ul>\n'
                 '      </section>\n')

    return page(f"サイトマップ - {NAME}",
                f"{NAME}のサイトマップ。カテゴリーと記事の一覧です。", "", p,
                f"{BASE_URL}/sitemap.html", body, body_class="is-listing",
                sidebar=True,
                crumbs=[("ホーム", f"{p}index.html"), ("サイトマップ", None)])


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
          <input type="search" id="searchInput" placeholder="キーワードを入力" aria-label="サイト内検索" autocomplete="off">
          <button type="button" id="searchClear">クリア</button>
        </form>

        <div class="chip-group is-open" id="catGroup">
          <button type="button" class="chip-toggle" aria-expanded="true" aria-controls="catChips">
            <span class="chip-label">カテゴリー</span>
            <span class="chip-picked" hidden></span>
            <span class="chip-caret" aria-hidden="true"></span>
          </button>
          <div class="chips" id="catChips">
{catchips}          </div>
        </div>

        <div class="chip-group is-open" id="tagGroup">
          <button type="button" class="chip-toggle" aria-expanded="true" aria-controls="tagChips">
            <span class="chip-label">タグ</span>
            <span class="chip-picked" hidden></span>
            <span class="chip-caret" aria-hidden="true"></span>
          </button>
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
                body_class="is-listing", sidebar=True, side_search_on=False,
                noindex=True,
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
      <p>当サイトの記事は、購入者レビューと公開されている製品仕様を突き合わせて整理・分析したものです。実機で確認した記事については、その旨を記事内に明記します。使用環境・体格・好みによって感じ方は異なり、効果や満足度を保証するものではありません。</p>
      <p>引用・参照している購入者レビューは、販売ページに掲載されている一般利用者の意見であり、その正確性を当サイトが保証するものではありません。</p>

      <h2>リンク先のコンテンツについて</h2>
      <p>当サイトからリンクやバナーによって他のサイトに移動した場合、移動先サイトで提供される情報・サービス等について一切の責任を負いません。</p>

      <h2>アフィリエイトプログラムについて</h2>
      <p>当サイトは、Amazonアソシエイト・プログラムをはじめとする各種アフィリエイトプログラムに参加しており、商品を紹介することで紹介料を得ています。ただし、紹介料の有無が記事の評価内容に影響を与えることはありません。</p>

      <p class="updated">最終更新：{today}</p>'''

    about = f'''      <p>{e(NAME)} は、「{e(TAGLINE)}」をコンセプトに、暮らしと作業を快適にするアイテムを紹介するメディアです。何を基準に記事を作っているかは<a href="{p}editorial-policy.html">記事作成方針</a>のページにまとめています。</p>

      <h2>運営者について</h2>
      <ul>
        <li>サイト名：{e(NAME)}</li>
        <li>運営者：{e(SITE["author"])}</li>
        <li>開設：{e(SITE["founded"])}年</li>
        <li>扱うジャンル：PC・スマホ周辺機器、生活家電、デスク環境の家具、日用品など</li>
        <li>連絡先：<a href="mailto:{e(SITE["email"])}">{e(SITE["email"])}</a>（記事の誤り・仕様の指摘も歓迎します）</li>
      </ul>

      <h2>関連ページ</h2>
      <ul>
        <li><a href="{p}editorial-policy.html">記事作成方針</a></li>
        <li><a href="{p}advertising.html">広告掲載について</a></li>
        <li><a href="{p}privacy.html">プライバシーポリシー</a></li>
        <li><a href="{p}disclaimer.html">免責事項</a></li>
      </ul>

      <p class="updated">最終更新：{today}</p>'''

    policy_items = ""
    for num, head, text in POLICY:
        policy_items += ('        <div class="policy-item">\n'
                          f'          <span class="policy-num">{num}</span>\n'
                          '          <div class="policy-body">\n'
                          f'            <h3>{e(head)}</h3>\n'
                          f'            <p>{e(text)}</p>\n'
                          '          </div>\n'
                          '        </div>\n')

    editorial_policy = f'''      <h2>このサイトの読み方</h2>
      <p>購入者レビューと製品仕様を突き合わせ、良い点だけでなく「合わない場面」まで整理しています。</p>
      <div class="policy">
{policy_items}      </div>

      <h2>サイトの方針</h2>
      <p>{e(NAME)} は、「{e(TAGLINE)}」をコンセプトに、暮らしと作業を快適にするアイテムを紹介するメディアです。ガジェットやPC周辺機器から、デスク環境を整える家具、毎日使う生活家電・日用品まで、ジャンルを限定せずに扱っています。</p>
      <p>読んだ人が「買って後悔した」を減らせることを目的にしているため、良い点だけでなく、気になった点や向いていない人についても必ず記載しています。</p>

      <h2>記事の作り方</h2>
      <dl>
        <dt>仕様を確認する</dt>
        <dd>メーカー公表の仕様を確認し、数値や機能の有無を裏取りしたうえで記載します。</dd>
        <dt>使われ方を調べる</dt>
        <dd>実際の使用場面や、どんな環境で満足・不満につながりやすいかを調べ、繰り返し挙がる内容を整理します。</dd>
        <dt>デメリットを必ず書く</dt>
        <dd>不満点は省かずに記載し、可能な限り対処法もあわせて提示します。</dd>
        <dt>比較する</dt>
        <dd>同価格帯の代替候補と並べ、どんな人にどちらが向くかを明示します。</dd>
        <dt>更新する</dt>
        <dd>後継製品の発売や仕様変更があった場合は、記事を更新または追記します。</dd>
      </dl>

      <p>掲載している内容は購入判断の参考としてご利用いただき、最終的な仕様・価格は必ず販売ページでご確認ください。</p>

      <h2>評価の基準</h2>
      <dl>
        <dt>複数の情報源を突き合わせる</dt>
        <dd>ひとつの情報だけを根拠にしません。良い評価と悪い評価の両面を突き合わせ、メーカー公表の仕様と整合するかを確認します。</dd>
        <dt>スコアの内訳を示す</dt>
        <dd>総合評価だけでなく、どの観点で加点・減点したのかを記事内に明示します。</dd>
        <dt>向かない人を必ず書く</dt>
        <dd>すべての人に勧められる商品はありません。期待や設置環境が合わない場合は、その条件をはっきり書きます。</dd>
        <dt>代替候補と比較する</dt>
        <dd>同価格帯の他の選択肢と並べ、どんな人にどちらが向くかを示します。</dd>
        <dt>金銭的な関係を評価に持ち込まない</dt>
        <dd>アフィリエイト報酬の有無や料率は、掲載可否や評価内容に影響させません。</dd>
        <dt>公開後も更新する</dt>
        <dd>仕様変更・後継機の登場・価格傾向の変化があれば、記事を追記・修正します。</dd>
      </dl>

      <h2>なぜこのサイトを作ったか</h2>
      <p>ネット上の商品紹介は、良い点だけを並べたものか、逆に欠点をあげつらうだけのものに偏りがちです。どちらも、実際に買うかどうかを決めるときには役に立ちません。</p>
      <p>{e(NAME)} は、<strong>「この環境の自分なら効くか」を読者が自分で判断できる材料</strong>をそろえることを目的にしています。だからこそ、良い点は生活の場面まで踏み込んで具体的に書き、注意点は「誰に・どんな環境で当てはまるか」を絞って書きます。</p>

      <h2>関連ページ</h2>
      <ul>
        <li><a href="{p}about.html">運営者情報</a></li>
        <li><a href="{p}advertising.html">広告掲載について</a></li>
      </ul>

      <p class="updated">最終更新：{today}</p>'''

    advertising = f'''      <h2>広告について</h2>
      <p>{e(NAME)} は、Amazon.co.jpを宣伝しリンクすることによってサイトが紹介料を獲得できる手段を提供することを目的に設定されたアフィリエイトプログラムである、Amazonアソシエイト・プログラムをはじめとする各種アフィリエイトプログラムに参加しています。記事内の商品リンクを経由して購入いただいた場合、当サイトに紹介料が入ることがあります。</p>
      <p>広告収益の有無や多寡によって、記事の評価内容・掲載可否を変えることはありません。詳しい評価の考え方は<a href="{p}editorial-policy.html">記事作成方針</a>をご覧ください。</p>

      <h2>レビューのご依頼も受け付けています</h2>
      <p>メーカー・販売店の方からの掲載・レビューのご依頼を歓迎します。<a href="{p}contact.html">お問い合わせフォーム</a>で「掲載・レビューのご依頼」を選び、次の内容をお知らせください。</p>
      <ul>
        <li>製品名と、公式の製品ページのURL</li>
        <li>訴求したい点と、想定している読者</li>
        <li>サンプル提供の可否と、貸出の場合は期間</li>
        <li>希望する公開時期（あれば）</li>
      </ul>
      <p>当サイトは<strong>購入者レビューと公表仕様をもとに、合わない場面まで書く方針</strong>です。提供の有無にかかわらず内容は編集しません。良い点だけを書くご依頼はお受けできません。記事化する場合は、提供を受けた旨を明記します。</p>
      <p>フォームがうまく送れない場合は、<a href="mailto:{e(SITE["email"])}">{e(SITE["email"])}</a> へ直接お送りください。</p>

      <p class="updated">最終更新：{today}</p>'''

    for fname, title, desc, content in [
        ("privacy.html", "プライバシーポリシー",
         f"{NAME}のプライバシーポリシー。アクセス解析・広告配信・個人情報の取り扱いについて記載しています。", privacy),
        ("disclaimer.html", "免責事項",
         f"{NAME}の免責事項。掲載情報の正確性、商品情報、リンク先の内容についての責任範囲を記載しています。", disclaimer),
        ("about.html", "運営者情報",
         f"{NAME}の運営者情報。運営者・お問い合わせ先を記載しています。", about),
        ("editorial-policy.html", "記事作成方針",
         f"{NAME}がどんな基準で記事を作り、商品を評価しているかをまとめています。", editorial_policy),
        ("advertising.html", "広告掲載について",
         f"{NAME}の広告・アフィリエイトプログラムについて、およびレビュー・掲載のご依頼について記載しています。", advertising),
    ]:
        body = (                f'      <div class="page-hero"><h1>{e(title)}</h1></div>\n'
                f'      <div class="prose">\n{content}\n      </div>\n')
        bcls = "is-editorial-policy" if fname == "editorial-policy.html" else ""
        out.append((fname, page(f"{title} - {NAME}", desc, "", p,
                                f"{BASE_URL}/{fname}", body, body_class=bcls,
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
            <p class="side-heading">広告の掲載について</p>
            <p class="field-hint">メーカー・販売店の方からの掲載・レビューのご依頼を歓迎します。
            受け付けている内容や当サイトの方針は、下記のページにまとめています。</p>
            <p class="cta-wrap"><a class="btn-sub" href="{p}advertising.html">広告掲載について見る</a></p>
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
    write("sitemap.html", build_sitemap()); written.append("sitemap.html")
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
    static = ["about.html", "editorial-policy.html", "advertising.html",
              "privacy.html", "disclaimer.html", "sitemap.html"]
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

    # feed.xml：更新を知らせるフィード。
    # 読者の購読だけでなく、検索エンジンやニュース系のクローラが
    # 新着を見つける手がかりにもなる（sitemap より更新に敏感）。
    def rfc822(iso):
        try:
            y, m, d = str(iso)[:10].split("-")
            wd = datetime.date(int(y), int(m), int(d)).strftime("%a")
            mo = datetime.date(int(y), int(m), int(d)).strftime("%b")
            return f"{wd}, {int(d):02d} {mo} {y} 00:00:00 +0900"
        except (ValueError, TypeError):
            return ""

    items = ""
    for a in PUBLISHED[:20]:
        link = public_url(f'{BASE_URL}/articles/{a["slug"]}.html')
        items += (f"  <item>\n"
                  f"    <title>{e(a.get('list_title') or a['title'])}</title>\n"
                  f"    <link>{e(link)}</link>\n"
                  f"    <guid isPermaLink=\"true\">{e(link)}</guid>\n"
                  f"    <description>{e(a.get('excerpt') or a.get('description',''))}</description>\n"
                  f"    <category>{e(CAT_LABEL.get(a['category'],''))}</category>\n"
                  f"    <pubDate>{rfc822(a.get('updated') or a['date'])}</pubDate>\n"
                  f"  </item>\n")
    write("feed.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
          '<channel>\n'
          f"  <title>{e(NAME)}</title>\n"
          f"  <link>{BASE_URL}/</link>\n"
          f"  <description>{e(SITE['description'])}</description>\n"
          "  <language>ja</language>\n"
          f'  <atom:link href="{BASE_URL}/feed.xml" rel="self" type="application/rss+xml"/>\n'
          + items +
          "</channel>\n</rss>\n")
    written.append("feed.xml")

    # ads.txt：この広告枠を売ってよいのは誰か、をドメインの持ち主が宣言する。
    # 置いていないと AdSense 側で「要注意」と警告が出て、収益にも響く。
    # 中身は AdSense が配る1行をそのまま書く（pub-… はアカウント固有）。
    client = (ADS.get("client") or "").strip()
    if client:
        pub = client[3:] if client.startswith("ca-") else client
        write("ads.txt", f"google.com, {pub}, DIRECT, f08c47fec0942fa0\n")
        written.append("ads.txt")

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
