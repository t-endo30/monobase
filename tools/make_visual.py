#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事のサムネイル用SVGを生成する。

方針：
・商品名と分野を文字で入れる。一覧に出すのはモールの実物写真だけに
  したので、写真が無い記事にはこの絵が出る。図形だけでは何の記事か
  分からず、クリックの手がかりにならない。「準備中」の類は書かない。
  作りかけのサイトに見えるうえ、読む人には何の役にも立たない。
・キャンバスは正方形。枠が 1:1 なので、横長で作ると左右が切り取られて
  文字が読めなくなる。文字は中央の帯に置き、横長の枠で上下を
  切り取られても残るようにする。
・モチーフは中央に配置し、どの比率で切り取られても破綻しないようにする。
・外部素材を使わないため著作権・規約のリスクがない。
・地色はモノトーン。モチーフ（イラスト）だけにカテゴリー色を使う。
  一覧に並べても色が面で主張せず、それでいて category ごとの識別が付く。
"""
import os

# カテゴリー別の色（モチーフの描画色）
CAT_COLOR = {
    "gadget":  "#2F5FA8",
    "desk":    "#A0722B",
    "home":    "#1E7A5E",
    "compare": "#6350A8",
}
DEFAULT = "#5A5D63"

BASE_LIGHT = "#EDEDEF"   # 地色（モノトーン）
BASE_DARK  = "#DEDEE1"   # 地色のグラデーション下端
LINE       = "#25282D"   # 使わなくなった旧・線色（互換のため残す）

CX, CY = 600, 600     # キャンバス中心（1200x1200）


def motif(category, LINE):
    """カテゴリーごとの幾何モチーフ。中心 (600,330) から対称に描く。
       下に商品名を置くので、少し上寄りにしている。"""
    if category == "gadget":      # 同心円＝波形・信号
        return f'''
  <circle cx="600" cy="330" r="150" fill="none" stroke="{LINE}" stroke-opacity=".55" stroke-width="2"/>
  <circle cx="600" cy="330" r="72" fill="none" stroke="{LINE}" stroke-opacity=".70" stroke-width="2"/>
  <circle cx="600" cy="330" r="72" fill="none" stroke="{LINE}" stroke-opacity=".85" stroke-width="2"/>
  <circle cx="600" cy="330" r="34"  fill="{LINE}" fill-opacity=".45"/>'''
    if category == "desk":        # 水平線と支柱＝什器
        return f'''
  <line x1="330" y1="330" x2="870" y2="330" stroke="{LINE}" stroke-opacity=".85" stroke-width="4"/>
  <line x1="410" y1="330" x2="410" y2="430" stroke="{LINE}" stroke-opacity=".65" stroke-width="3"/>
  <line x1="790" y1="330" x2="790" y2="430" stroke="{LINE}" stroke-opacity=".65" stroke-width="3"/>
  <rect x="452" y="230" width="296" height="150" fill="none" stroke="{LINE}" stroke-opacity=".50" stroke-width="2"/>'''
    if category == "home":        # 同心の角丸＝住まいの層
        return f'''
  <rect x="418" y="228" width="364" height="304" rx="26" fill="none" stroke="{LINE}" stroke-opacity=".55" stroke-width="2"/>
  <rect x="478" y="266" width="244" height="208" rx="20" fill="none" stroke="{LINE}" stroke-opacity=".65" stroke-width="2"/>
  <rect x="538" y="304" width="124" height="112" rx="14" fill="{LINE}" fill-opacity=".40"/>'''
    # compare：左右対称の棒＝比較
    return f'''
  <rect x="446" y="312" width="46" height="96"  rx="6" fill="{LINE}" fill-opacity=".40"/>
  <rect x="514" y="282" width="46" height="176" rx="6" fill="{LINE}" fill-opacity=".55"/>
  <rect x="582" y="256" width="46" height="248" rx="6" fill="{LINE}" fill-opacity=".65"/>
  <rect x="650" y="282" width="46" height="176" rx="6" fill="{LINE}" fill-opacity=".55"/>
  <rect x="718" y="312" width="46" height="96"  rx="6" fill="{LINE}" fill-opacity=".40"/>'''


def esc(t):
    return (str(t or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def wrap(title, per=9, lines=3):
    """商品名を折り返す。日本語は語で切れないので、文字数で折る。
       入りきらないぶんは落として「…」を付ける。
       枠は一覧で180px程度にしか出ない。1行に詰め込むと縮んで読めないので、
       1行を短くして行数で見せる。"""
    t = " ".join(str(title or "").split())
    out = []
    while t and len(out) < lines:
        out.append(t[:per])
        t = t[per:]
    if t and out:
        out[-1] = out[-1][:per - 1] + "…"
    return out


def build(slug, title, category, cat_label, site_name, out_dir):
    accent = CAT_COLOR.get(category, DEFAULT)
    rows = wrap(title)
    # 文字は中央の帯（y=760〜900）に置く。横長の枠で上下を切り取られても
    # 残る位置。フォントは閲覧者の端末にあるものを使う（SVGを<img>で
    # 読むため、Webフォントは効かない）。
    fam = ("&quot;Hiragino Sans&quot;, &quot;Noto Sans JP&quot;, "
           "&quot;Yu Gothic&quot;, sans-serif")
    text = ""
    # 上から順に、モチーフ・商品名・分野。
    # 分野は商品名の下に置く。上に離して置くと図形と商品名の間に
    # 挟まって、どちらの見出しなのか分かりにくかった。
    top = 700 - (len(rows) - 1) * 55
    for i, line in enumerate(rows):
        text += (f'\n  <text x="600" y="{top + i * 110}" text-anchor="middle" '
                 f'font-family="{fam}" font-size="96" font-weight="700" '
                 f'fill="{LINE}" fill-opacity=".80">{esc(line)}</text>')
    if cat_label:
        text += (f'\n  <text x="600" y="{top + (len(rows) - 1) * 110 + 112}" '
                 f'text-anchor="middle" '
                 f'font-family="{fam}" font-size="64" letter-spacing="10" '
                 f'fill="{accent}" fill-opacity=".70">{esc(cat_label)}</text>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200" role="img" aria-label="{esc(title)}">
  <defs>
    <linearGradient id="shade" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0%" stop-color="{BASE_LIGHT}"/>
      <stop offset="100%" stop-color="{BASE_DARK}"/>
    </linearGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M40 0 L0 0 0 40" fill="none" stroke="{LINE}" stroke-opacity=".05" stroke-width="1"/>
    </pattern>
  </defs>

  <rect width="1200" height="1200" fill="url(#shade)"/>
  <rect width="1200" height="1200" fill="url(#grid)"/>
{motif(category, accent)}{text}
</svg>
'''
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, slug + ".svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path
