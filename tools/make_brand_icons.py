#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""favicon・apple-touch-icon・OGP画像を、ブランドマークから作り直す。

    python3 tools/make_icons.py

作るもの（すべて assets/img/ へ）:
    favicon.svg           ブラウザのタブ（拡大しても粗くならないSVG）
    favicon-32.png        SVGを読まないブラウザ向けの控え
    apple-touch-icon.png  iOSのホーム画面（角丸はiOS側が付けるので四角のまま）
    og-default.jpg        SNSに貼られたときの既定の画像

マークは build.py の logo_svg() と同じ形。色だけ、暗い地の上に置くため
フッターと同じ組み合わせ（白い箱・黒いフタ）に入れ替えている。

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


def mark(body, flap, line, letter, inner="#ffffff", inner2="#1b1b1b", flaps=True):
    """写真（開いた箱に MB）に寄せたブランドマーク。
       立方体を角から見た形。上面は菱形の開口で、そこから4枚のフタが開く。
       奥の2枚は立ち上がり、手前の2枚は上面と同じ平面のまま外へ倒れる。"""
    T, L, R, F = (24, 13), (9, 22), (39, 22), (24, 31)
    L2, F2, R2 = (9, 35.5), (24, 44.5), (39, 35.5)
    def d(*pts): return "M" + " L".join(f"{x} {y}" for x, y in pts) + " Z"

    # 手前のフタは上面と同じ平面のまま外へ。奥へ向かう対角の逆向きに倒す
    fl_front = f'''<path d="{d(L, F, (15.6,32.8), (0.6,23.8))}"/>
    <path d="{d(F, R, (47.4,23.8), (32.4,32.8))}"/>'''
    # 奥のフタは立ち上がる
    fl_back = f'''<path d="{d(L, T, (21.5,2.5), (6.5,10.5))}"/>
    <path d="{d(T, R, (41.5,10.5), (26.5,2.5))}"/>'''
    g_front = (f'<g fill="{flap}" stroke="{line}" stroke-width="0.9" '
               f'stroke-linejoin="round">{fl_front}</g>' if flaps else "")
    g_back = (f'<g fill="{flap}" stroke="{line}" stroke-width="0.9" '
              f'stroke-linejoin="round">{fl_back}</g>' if flaps else "")
    return f'''<g>
  {g_front}
  <path d="{d(T, R, F, L)}" fill="{inner}" stroke="{line}" stroke-width="0.9" stroke-linejoin="round"/>
  <path d="{d((24,22.5),(31,26.5),(24,30.5),(17,26.5))}" fill="{inner2}"/>
  {g_back}
  <path d="{d(L, F, F2, L2)}" fill="{body}"/>
  <path d="{d(F, R, R2, F2)}" fill="{body}"/>
  <g fill="{letter}" font-family="Helvetica Neue,Arial,sans-serif"
     font-size="11" font-weight="700" text-anchor="middle" dominant-baseline="central">
    <text x="16.5" y="23.6" transform="matrix(1,0.6,0,1,0,0)">M</text>
    <text x="31.5" y="52.4" transform="matrix(1,-0.6,0,1,0,0)">B</text>
  </g>
</g>'''


# マークの図形が実際に占める範囲（48×44 の枠のうち、フタの先から箱の底まで）。
# タイルいっぱいに収めるための計算に使う。
MARK_BOX = (0.6, 2.5, 47.4, 44.5)       # フタまで入れたとき
MARK_BOX_NOFLAP = (9.0, 13.0, 39.0, 44.5)   # 箱だけのとき


def tile_svg(round_corners=True, pad=3.0, flaps=True):
    """暗いタイルにマークを載せたもの。favicon と apple-touch-icon で共用。
       16pxまで小さくなるので、余白を詰めてタイルいっぱいに置く。
       余らせると箱が小さくなり、中の MB が読めなくなる。"""
    x1, y1, x2, y2 = MARK_BOX if flaps else MARK_BOX_NOFLAP
    w, h = x2 - x1, y2 - y1
    s = min((64 - pad * 2) / w, (64 - pad * 2) / h)
    tx = (64 - w * s) / 2 - x1 * s
    ty = (64 - h * s) / 2 - y1 * s
    r = ' rx="14"' if round_corners else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64"{r} fill="{INK}"/>
  <g transform="translate({tx:.2f},{ty:.2f}) scale({s:.3f})">
{mark("#ffffff", INK, "#ffffff", INK, inner=INK, inner2="#ffffff", flaps=flaps)}
  </g>
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
  <g transform="translate(504,176) scale(4)">
{mark(INK, "#ffffff", INK, "#ffffff")}
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

    # 1) favicon.svg。タブは小さいので角丸を付けた暗いタイルに載せる
    fav = os.path.join(OUT, "favicon.svg")
    io.open(fav, "w", encoding="utf-8").write(tile_svg(flaps=False) + "\n")
    print(f"  {os.path.relpath(fav, ROOT)}")

    # 2) SVGを読まないブラウザ向けの控え
    p32 = os.path.join(OUT, "favicon-32.png")
    shot(tile_svg(flaps=False), 32, 32, p32, ch, transparent=True)
    print(f"  {os.path.relpath(p32, ROOT)}  32×32")

    # 3) iOSのホーム画面。角丸はiOSが付けるので、こちらは四角のまま
    apple = os.path.join(OUT, "apple-touch-icon.png")
    shot(tile_svg(round_corners=False), 180, 180, apple, ch)
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
