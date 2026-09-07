#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""favicon・apple-touch-icon・OGP画像を、ブランドマークから作り直す。

    python3 tools/make_icons.py

作るもの（すべて assets/img/ へ）:
    favicon.svg           ブラウザのタブ（拡大しても粗くならないSVG）
    favicon-32.png        SVGを読まないブラウザ向けの控え
    apple-touch-icon.png  iOSのホーム画面（角丸はiOS側が付けるので四角のまま）
    og-default.jpg        SNSに貼られたときの既定の画像

マークは build.py の logo_svg() と同じ形・同じ色。ヘッダーに出ている
ものと、タブ・ホーム画面・ブックマーク・SNSの絵が揃う。

PNG/JPG は Chrome を画面なしで動かして書き出す。SVGを直接ラスタライズする
道具（cairosvg など）を新たに入れずに済ませるため。
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "img")

INK = "#111111"      # 地の色（暗いタイル）
PAPER = "#f4f4f2"    # 紙面の地の色

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
]


def chrome():
    for c in CHROME_CANDIDATES:
        if c and os.path.exists(c):
            return c
    sys.exit("Chrome が見つかりません。")


def mark(body="#3d3d3d", body2="#2a2a2a", flap="#f2f2f2", flap2="#f7f7f7",
         line="#9a9a9a", inner="#c9c9c9", letter="#ffffff"):
    """ブランドマーク。build.py の logo_svg() と同じ座標。
       立方体を角から見た形で、上面の菱形の開口から4枚のフタが外へ開く。
       色だけ引数で入れ替える（暗い地に置くときは白黒を反転させる）。"""
    return f'''<g stroke="{line}" stroke-width="0.9" stroke-linejoin="round">
  <path d="M32 11 L10 23 L3 14 L30 1 Z" fill="{flap}"/>
  <path d="M32 11 L54 23 L61 14 L34 1 Z" fill="{flap}"/>
  <path d="M10 23 L32 11 L54 23 L32 35 Z" fill="{inner}"/>
  <path d="M10 23 L10 49 L32 61 L32 35 Z" fill="{body}"/>
  <path d="M54 23 L54 49 L32 61 L32 35 Z" fill="{body2}"/>
  <path d="M10 23 L32 35 L26 40 L4 28 Z" fill="{flap2}"/>
  <path d="M54 23 L32 35 L38 40 L60 28 Z" fill="{flap2}"/>
</g>
<g fill="{letter}" font-family="Helvetica Neue,Helvetica,Arial,sans-serif"
   font-size="13" font-weight="700" text-anchor="middle" dominant-baseline="central">
  <text x="21" y="34.9" transform="matrix(1,0.6,0,1,0,0)">M</text>
  <text x="43" y="73.3" transform="matrix(1,-0.6,0,1,0,0)">B</text>
</g>'''


# マークの図形が実際に占める範囲（フタの先から箱の底まで）。
# 紙面に載せるとき、位置と大きさを決める計算に使う。
MARK_BOX = (3.0, 1.0, 61.0, 61.0)


def tile_svg(round_corners=False):
    """紙の地にマークを載せたもの。favicon と apple-touch-icon で共用。
       ヘッダーに出ているものと同じ配色・同じ座標なので、
       タブ・ホーム画面・ブックマークでヘッダーと同じ絵になる。"""
    r = ' rx="14"' if round_corners else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
<rect width="64" height="64"{r} fill="#ffffff"/>
{mark()}
</svg>'''


def shot(svg, w, h, path, chrome_bin, transparent=False):
    """SVGをその大きさちょうどで描いて画像に落とす。"""
    with tempfile.TemporaryDirectory() as d:
        html = os.path.join(d, "i.html")
        io.open(html, "w", encoding="utf-8").write(
            "<!doctype html><meta charset='utf-8'>"
            "<style>html,body{margin:0;padding:0;"
            + ("background:transparent" if transparent else "background:#fff")
            + f"}}svg{{display:block;width:{w}px;height:{h}px}}</style>" + svg)
        cmd = [chrome_bin, "--headless", "--disable-gpu", "--hide-scrollbars",
               f"--window-size={w},{h}", f"--screenshot={path}"]
        if transparent:
            cmd.append("--default-background-color=00000000")
        cmd.append("file://" + html)
        subprocess.run(cmd, capture_output=True)


def og_svg(name, tagline):
    """SNSに貼られたときの画像。紙面と同じ地の色に、マークと名前を置く。"""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="{PAPER}"/>
  <g stroke="#dcdcd8" stroke-width="1.4" fill="none">
    <path d="M0 108 H1200"/><path d="M0 522 H1200"/>
  </g>
  <g stroke="#d3d3ce" stroke-width="1.4" fill="none" opacity=".8">
    <circle cx="600" cy="248" r="142"/>
    <circle cx="600" cy="248" r="90" stroke-dasharray="4 7"/>
  </g>
  <g transform="translate(472,120) scale(4)">
{mark()}
  </g>
  <g font-family="Helvetica Neue,Arial,Hiragino Sans,Meiryo,sans-serif" text-anchor="middle">
    <text x="600" y="452" font-size="62" font-weight="800" fill="{INK}">{name}</text>
    <text x="600" y="506" font-size="26" font-weight="500" fill="#6e6e6e">{tagline}</text>
    <text x="600" y="574" font-size="17" font-weight="700" fill="#9a9a9a"
          letter-spacing="6">MONOBASE</text>
  </g>
</svg>'''


def main():
    import json
    site = json.load(io.open(os.path.join(ROOT, "content/site.json"), encoding="utf-8"))
    ch = chrome()

    # 1) favicon.svg。ブラウザのタブとブックマークで使われる
    fav = os.path.join(OUT, "favicon.svg")
    io.open(fav, "w", encoding="utf-8").write(tile_svg() + "\n")
    print(f"  {os.path.relpath(fav, ROOT)}")

    # 2) SVGを読まないブラウザ向けの控え
    p32 = os.path.join(OUT, "favicon-32.png")
    shot(tile_svg(), 32, 32, p32, ch)
    print(f"  {os.path.relpath(p32, ROOT)}  32×32")

    # 3) iOSのホーム画面。角丸はiOSが付けるので、こちらは四角のまま
    apple = os.path.join(OUT, "apple-touch-icon.png")
    shot(tile_svg(), 180, 180, apple, ch)
    print(f"  {os.path.relpath(apple, ROOT)}  180×180")

    # 4) OGP。JPEGにしたいので、一度PNGで撮ってから変換する
    og = os.path.join(OUT, "og-default.jpg")
    with tempfile.TemporaryDirectory() as d:
        tmp = os.path.join(d, "og.png")
        shot(og_svg(site["site_name"], site.get("tagline", "")), 1200, 630, tmp, ch)
        from PIL import Image
        Image.open(tmp).convert("RGB").save(og, "JPEG", quality=88, optimize=True)
    print(f"  {os.path.relpath(og, ROOT)}  1200×630  "
          f"{os.path.getsize(og) // 1024}KB")


if __name__ == "__main__":
    main()
