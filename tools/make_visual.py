#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事タイトルとカテゴリーから、アイキャッチ用のSVGを生成する。

・外部素材を一切使わないため、著作権・規約のリスクがない
・カテゴリー色で自動的に配色されるので、一覧に並べたときの識別性が高い
・実写真が用意できたら thumb フィールドを設定すれば、そちらが優先される
"""
import os, re, html

CAT_COLOR = {
    "gadget":  ("#2E6BE6", "#1B47A8"),
    "desk":    ("#C77A16", "#8F5407"),
    "home":    ("#12916A", "#0A6349"),
    "compare": ("#7A4FD1", "#53309A"),
}
DEFAULT = ("#1B2436", "#2C3A55")


def wrap(text, per_line=13, max_lines=3):
    """日本語タイトルを指定文字数で折り返す。区切り記号を優先して分割する。"""
    text = re.sub(r"^【[^】]*】", "", text).strip()
    for sep in ("｜", "|", "／"):
        if sep in text:
            text = text.split(sep)[0].strip()
            break
    lines, cur = [], ""
    for ch in text:
        cur += ch
        if len(cur) >= per_line:
            lines.append(cur)
            cur = ""
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if not lines:
        lines = [text[:per_line]]
    if len(lines) == max_lines and len("".join(lines)) < len(text):
        lines[-1] = lines[-1][:per_line - 1] + "…"
    return lines


def build(slug, title, category, cat_label, site_name, out_dir):
    c1, c2 = CAT_COLOR.get(category, DEFAULT)
    lines = wrap(title)
    # 行数に応じて縦位置を調整し、常に中央に収める
    start_y = 300 - (len(lines) - 1) * 34
    tspans = "".join(
        f'<tspan x="72" y="{start_y + i * 68}">{html.escape(l)}</tspan>'
        for i, l in enumerate(lines)
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675" role="img" aria-label="{html.escape(title)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
    <radialGradient id="glow" cx="18%" cy="8%" r="70%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity=".28"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1.6" fill="#ffffff" fill-opacity=".14"/>
    </pattern>
  </defs>

  <rect width="1200" height="675" fill="url(#bg)"/>
  <rect width="1200" height="675" fill="url(#dots)"/>
  <rect width="1200" height="675" fill="url(#glow)"/>

  <circle cx="1075" cy="128" r="190" fill="#ffffff" fill-opacity=".07"/>
  <circle cx="1160" cy="560" r="240" fill="#000000" fill-opacity=".08"/>

  <rect x="72" y="86" width="{max(150, len(cat_label) * 30 + 52)}" height="48" rx="24" fill="#ffffff" fill-opacity=".18"/>
  <text x="{72 + 26}" y="117" font-family="'Noto Sans JP','Hiragino Sans','Yu Gothic',sans-serif"
        font-size="24" font-weight="700" fill="#ffffff" letter-spacing="1.5">{html.escape(cat_label)}</text>

  <text font-family="'Noto Sans JP','Hiragino Sans','Yu Gothic',sans-serif"
        font-size="58" font-weight="900" fill="#ffffff" letter-spacing="1">{tspans}</text>

  <rect x="72" y="576" width="96" height="6" rx="3" fill="#FF9900"/>
  <text x="72" y="622" font-family="'Noto Sans JP','Hiragino Sans','Yu Gothic',sans-serif"
        font-size="26" font-weight="700" fill="#ffffff" fill-opacity=".85" letter-spacing="2">{html.escape(site_name)}</text>
</svg>
'''
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, slug + ".svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path
