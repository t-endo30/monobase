#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事のサムネイル用SVGを生成する。

方針：
・記事タイトルは載せない。カード本文と重複するうえ、
  表示サイズによって文字の大きさが変わり統一感が崩れるため。
・カテゴリーごとに落ち着いた単色＋細い罫線で構成し、
  どのサイズで切り取られても破綻しないようにする。
・外部素材を使わないため著作権・規約のリスクがない。
"""
import os, html

# カテゴリー別の地色（彩度を抑えた単色）
CAT_COLOR = {
    "gadget":  "#2F5FA8",
    "desk":    "#A0722B",
    "home":    "#1E7A5E",
    "compare": "#6350A8",
}
DEFAULT = "#3A4557"

# カテゴリーごとの幾何モチーフ（意味を持たせて描き分ける）
def motif(category):
    if category == "gadget":      # 同心円＝波形・信号
        return '''
  <circle cx="980" cy="338" r="150" fill="none" stroke="#fff" stroke-opacity=".16" stroke-width="2"/>
  <circle cx="980" cy="338" r="110" fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="2"/>
  <circle cx="980" cy="338" r="70"  fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="2"/>
  <circle cx="980" cy="338" r="26"  fill="#fff" fill-opacity=".30"/>'''
    if category == "desk":        # 直線の組み合わせ＝机・什器
        return '''
  <rect x="852" y="212" width="256" height="180" fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="2"/>
  <line x1="852" y1="392" x2="852" y2="470" stroke="#fff" stroke-opacity=".22" stroke-width="2"/>
  <line x1="1108" y1="392" x2="1108" y2="470" stroke="#fff" stroke-opacity=".22" stroke-width="2"/>
  <line x1="820" y1="392" x2="1140" y2="392" stroke="#fff" stroke-opacity=".30" stroke-width="3"/>'''
    if category == "home":        # 家型＝住まい
        return '''
  <path d="M980 208 L1112 318 L1112 462 L848 462 L848 318 Z"
        fill="none" stroke="#fff" stroke-opacity=".22" stroke-width="2"/>
  <path d="M940 462 L940 372 L1020 372 L1020 462"
        fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="2"/>'''
    # compare：棒グラフ＝比較
    return '''
  <rect x="866" y="366" width="46" height="104" fill="#fff" fill-opacity=".20"/>
  <rect x="934" y="296" width="46" height="174" fill="#fff" fill-opacity=".30"/>
  <rect x="1002" y="336" width="46" height="134" fill="#fff" fill-opacity=".24"/>
  <rect x="1070" y="252" width="46" height="218" fill="#fff" fill-opacity=".16"/>
  <line x1="840" y1="470" x2="1140" y2="470" stroke="#fff" stroke-opacity=".35" stroke-width="2"/>'''


def build(slug, title, category, cat_label, site_name, out_dir):
    base = CAT_COLOR.get(category, DEFAULT)
    label = html.escape(cat_label)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675" role="img" aria-label="{label}">
  <defs>
    <linearGradient id="shade" x1="0" y1="0" x2="0.4" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity=".10"/>
      <stop offset="100%" stop-color="#000000" stop-opacity=".16"/>
    </linearGradient>
    <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
      <path d="M48 0 L0 0 0 48" fill="none" stroke="#ffffff" stroke-opacity=".07" stroke-width="1"/>
    </pattern>
  </defs>

  <rect width="1200" height="675" fill="{base}"/>
  <rect width="1200" height="675" fill="url(#grid)"/>
  <rect width="1200" height="675" fill="url(#shade)"/>
{motif(category)}

  <line x1="80" y1="470" x2="176" y2="470" stroke="#FF9900" stroke-width="5"/>
  <text x="80" y="530" font-family="'Noto Sans JP','Hiragino Sans','Yu Gothic',sans-serif"
        font-size="40" font-weight="700" fill="#ffffff" letter-spacing="3">{label}</text>
  <text x="80" y="580" font-family="'Noto Sans JP','Hiragino Sans','Yu Gothic',sans-serif"
        font-size="23" font-weight="400" fill="#ffffff" fill-opacity=".62" letter-spacing="4">{html.escape(site_name)}</text>
</svg>
'''
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, slug + ".svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path
