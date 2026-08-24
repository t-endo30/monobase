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
    """カテゴリーごとの幾何モチーフ。中心は (985, 215) に統一する。"""
    if category == "gadget":      # 同心円＝波形・信号
        return """
  <circle cx="985" cy="215" r="150" fill="none" stroke="#fff" stroke-opacity=".14" stroke-width="2"/>
  <circle cx="985" cy="215" r="108" fill="none" stroke="#fff" stroke-opacity=".20" stroke-width="2"/>
  <circle cx="985" cy="215" r="66"  fill="none" stroke="#fff" stroke-opacity=".26" stroke-width="2"/>
  <circle cx="985" cy="215" r="24"  fill="#fff" fill-opacity=".28"/>"""
    if category == "desk":        # 直線の組み合わせ＝机・什器
        return """
  <rect x="868" y="112" width="234" height="140" fill="none" stroke="#fff" stroke-opacity=".20" stroke-width="2"/>
  <line x1="868" y1="252" x2="868" y2="322" stroke="#fff" stroke-opacity=".20" stroke-width="2"/>
  <line x1="1102" y1="252" x2="1102" y2="322" stroke="#fff" stroke-opacity=".20" stroke-width="2"/>
  <line x1="840" y1="252" x2="1130" y2="252" stroke="#fff" stroke-opacity=".30" stroke-width="3"/>"""
    if category == "home":        # 家型＝住まい
        return """
  <path d="M985 92 L1104 190 L1104 322 L866 322 L866 190 Z"
        fill="none" stroke="#fff" stroke-opacity=".20" stroke-width="2"/>
  <path d="M949 322 L949 242 L1021 242 L1021 322"
        fill="none" stroke="#fff" stroke-opacity=".26" stroke-width="2"/>"""
    # compare：棒グラフ＝比較
    return """
  <rect x="878" y="236" width="42" height="86"  fill="#fff" fill-opacity=".18"/>
  <rect x="940" y="176" width="42" height="146" fill="#fff" fill-opacity=".28"/>
  <rect x="1002" y="212" width="42" height="110" fill="#fff" fill-opacity=".22"/>
  <rect x="1064" y="140" width="42" height="182" fill="#fff" fill-opacity=".14"/>
  <line x1="856" y1="322" x2="1128" y2="322" stroke="#fff" stroke-opacity=".32" stroke-width="2"/>"""


def build(slug, title, category, cat_label, site_name, out_dir):
    base = CAT_COLOR.get(category, DEFAULT)
    label = html.escape(cat_label)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="430" viewBox="0 0 1200 430" role="img" aria-label="{label}">
  <defs>
    <linearGradient id="shade" x1="0" y1="0" x2="0.4" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity=".10"/>
      <stop offset="100%" stop-color="#000000" stop-opacity=".16"/>
    </linearGradient>
    <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
      <path d="M48 0 L0 0 0 48" fill="none" stroke="#ffffff" stroke-opacity=".07" stroke-width="1"/>
    </pattern>
  </defs>

  <rect width="1200" height="430" fill="{base}"/>
  <rect width="1200" height="430" fill="url(#grid)"/>
  <rect width="1200" height="430" fill="url(#shade)"/>
{motif(category)}

  <line x1="80" y1="168" x2="164" y2="168" stroke="#FF9900" stroke-width="5"/>
  <text x="80" y="232" font-family="\'Noto Sans JP\',\'Hiragino Sans\',\'Yu Gothic\',sans-serif"
        font-size="44" font-weight="700" fill="#ffffff" letter-spacing="3">{label}</text>
  <text x="80" y="284" font-family="\'Noto Sans JP\',\'Hiragino Sans\',\'Yu Gothic\',sans-serif"
        font-size="24" font-weight="400" fill="#ffffff" fill-opacity=".60" letter-spacing="4">{html.escape(site_name)}</text>
</svg>
'''
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, slug + ".svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path
