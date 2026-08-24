#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事のサムネイル用SVGを生成する。

方針：
・文字を一切入れない。切り抜き（object-fit: cover）で端が削れるうえ、
  表示サイズによって文字の大きさが変わり、カード間で統一感が崩れるため。
  カテゴリー名はカード側のタグ・記事側のバッジで既に示している。
・モチーフは中央に配置し、どの比率で切り取られても破綻しないようにする。
・外部素材を使わないため著作権・規約のリスクがない。
"""
import os

# カテゴリー別の地色（彩度を抑えた単色）
CAT_COLOR = {
    "gadget":  "#2F5FA8",
    "desk":    "#A0722B",
    "home":    "#1E7A5E",
    "compare": "#6350A8",
}
DEFAULT = "#3A4557"

CX, CY = 600, 300     # キャンバス中心


def motif(category):
    """カテゴリーごとの幾何モチーフ。中心 (600,300) から対称に描く。"""
    if category == "gadget":      # 同心円＝波形・信号
        return '''
  <circle cx="600" cy="300" r="230" fill="none" stroke="#fff" stroke-opacity=".10" stroke-width="2"/>
  <circle cx="600" cy="300" r="170" fill="none" stroke="#fff" stroke-opacity=".14" stroke-width="2"/>
  <circle cx="600" cy="300" r="110" fill="none" stroke="#fff" stroke-opacity=".18" stroke-width="2"/>
  <circle cx="600" cy="300" r="52"  fill="#fff" fill-opacity=".16"/>'''
    if category == "desk":        # 水平線と支柱＝什器
        return '''
  <line x1="330" y1="300" x2="870" y2="300" stroke="#fff" stroke-opacity=".22" stroke-width="4"/>
  <line x1="410" y1="300" x2="410" y2="452" stroke="#fff" stroke-opacity=".16" stroke-width="3"/>
  <line x1="790" y1="300" x2="790" y2="452" stroke="#fff" stroke-opacity=".16" stroke-width="3"/>
  <rect x="452" y="150" width="296" height="150" fill="none" stroke="#fff" stroke-opacity=".13" stroke-width="2"/>'''
    if category == "home":        # 同心の角丸＝住まいの層
        return '''
  <rect x="418" y="148" width="364" height="304" rx="26" fill="none" stroke="#fff" stroke-opacity=".11" stroke-width="2"/>
  <rect x="478" y="196" width="244" height="208" rx="20" fill="none" stroke="#fff" stroke-opacity=".15" stroke-width="2"/>
  <rect x="538" y="244" width="124" height="112" rx="14" fill="#fff" fill-opacity=".13"/>'''
    # compare：左右対称の棒＝比較
    return '''
  <rect x="446" y="252" width="46" height="96"  rx="6" fill="#fff" fill-opacity=".13"/>
  <rect x="514" y="212" width="46" height="176" rx="6" fill="#fff" fill-opacity=".18"/>
  <rect x="582" y="176" width="46" height="248" rx="6" fill="#fff" fill-opacity=".22"/>
  <rect x="650" y="212" width="46" height="176" rx="6" fill="#fff" fill-opacity=".18"/>
  <rect x="718" y="252" width="46" height="96"  rx="6" fill="#fff" fill-opacity=".13"/>'''


def build(slug, title, category, cat_label, site_name, out_dir):
    base = CAT_COLOR.get(category, DEFAULT)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="600" viewBox="0 0 1200 600" role="presentation" aria-hidden="true">
  <defs>
    <linearGradient id="shade" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity=".09"/>
      <stop offset="100%" stop-color="#000000" stop-opacity=".15"/>
    </linearGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M40 0 L0 0 0 40" fill="none" stroke="#ffffff" stroke-opacity=".055" stroke-width="1"/>
    </pattern>
  </defs>

  <rect width="1200" height="600" fill="{base}"/>
  <rect width="1200" height="600" fill="url(#grid)"/>
  <rect width="1200" height="600" fill="url(#shade)"/>
{motif(category)}
</svg>
'''
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, slug + ".svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path
