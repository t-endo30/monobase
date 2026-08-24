#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事のサムネイル用SVGを生成する。

方針：
・文字を一切入れない。切り抜き（object-fit: cover）で端が削れるうえ、
  表示サイズによって文字の大きさが変わり、カード間で統一感が崩れるため。
  カテゴリー名はカード側のタグ・記事側のバッジで既に示している。
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

CX, CY = 600, 300     # キャンバス中心


def motif(category, LINE):
    """カテゴリーごとの幾何モチーフ。中心 (600,300) から対称に描く。"""
    if category == "gadget":      # 同心円＝波形・信号
        return f'''
  <circle cx="600" cy="300" r="230" fill="none" stroke="{LINE}" stroke-opacity=".55" stroke-width="2"/>
  <circle cx="600" cy="300" r="170" fill="none" stroke="{LINE}" stroke-opacity=".70" stroke-width="2"/>
  <circle cx="600" cy="300" r="110" fill="none" stroke="{LINE}" stroke-opacity=".85" stroke-width="2"/>
  <circle cx="600" cy="300" r="52"  fill="{LINE}" fill-opacity=".45"/>'''
    if category == "desk":        # 水平線と支柱＝什器
        return f'''
  <line x1="330" y1="300" x2="870" y2="300" stroke="{LINE}" stroke-opacity=".85" stroke-width="4"/>
  <line x1="410" y1="300" x2="410" y2="452" stroke="{LINE}" stroke-opacity=".65" stroke-width="3"/>
  <line x1="790" y1="300" x2="790" y2="452" stroke="{LINE}" stroke-opacity=".65" stroke-width="3"/>
  <rect x="452" y="150" width="296" height="150" fill="none" stroke="{LINE}" stroke-opacity=".50" stroke-width="2"/>'''
    if category == "home":        # 同心の角丸＝住まいの層
        return f'''
  <rect x="418" y="148" width="364" height="304" rx="26" fill="none" stroke="{LINE}" stroke-opacity=".55" stroke-width="2"/>
  <rect x="478" y="196" width="244" height="208" rx="20" fill="none" stroke="{LINE}" stroke-opacity=".65" stroke-width="2"/>
  <rect x="538" y="244" width="124" height="112" rx="14" fill="{LINE}" fill-opacity=".40"/>'''
    # compare：左右対称の棒＝比較
    return f'''
  <rect x="446" y="252" width="46" height="96"  rx="6" fill="{LINE}" fill-opacity=".40"/>
  <rect x="514" y="212" width="46" height="176" rx="6" fill="{LINE}" fill-opacity=".55"/>
  <rect x="582" y="176" width="46" height="248" rx="6" fill="{LINE}" fill-opacity=".65"/>
  <rect x="650" y="212" width="46" height="176" rx="6" fill="{LINE}" fill-opacity=".55"/>
  <rect x="718" y="252" width="46" height="96"  rx="6" fill="{LINE}" fill-opacity=".40"/>'''


def build(slug, title, category, cat_label, site_name, out_dir):
    accent = CAT_COLOR.get(category, DEFAULT)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="600" viewBox="0 0 1200 600" role="presentation" aria-hidden="true">
  <defs>
    <linearGradient id="shade" x1="0" y1="0" x2="0.35" y2="1">
      <stop offset="0%" stop-color="{BASE_LIGHT}"/>
      <stop offset="100%" stop-color="{BASE_DARK}"/>
    </linearGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M40 0 L0 0 0 40" fill="none" stroke="{LINE}" stroke-opacity=".05" stroke-width="1"/>
    </pattern>
  </defs>

  <rect width="1200" height="600" fill="url(#shade)"/>
  <rect width="1200" height="600" fill="url(#grid)"/>
{motif(category, accent)}
</svg>
'''
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, slug + ".svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path
