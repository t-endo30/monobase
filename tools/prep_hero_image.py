#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ヒーローの箱写真を、紙面に置ける形に整える。

    python3 tools/prep_hero_image.py [元画像] [出力先]
    （既定: tools/hero-box-src.jpg -> assets/img/hero-box.webp）
    元画像は assets/ に置かない。配信に乗るうえ、画像の重さの検査に引っかかるため。

やっていること:

1. **地色を白(255)に正規化する**
   元画像の地色は 235 前後で、紙面の色（--bg:#f4f4f2）より暗い。そのまま置くと
   写真が「四角い板」として浮いて見える。CSS の brightness やマスクでごまかすと、
   フタの先端が切れたり、地の色を変えるたびに破綻する。
   照明のムラを面で推定して割り、地色を白に揃える。

2. **地を透明にする**
   以前は白い地のまま置いて、CSS の mix-blend-mode:multiply で紙面に溶かして
   いた。ただし multiply は、親に opacity や transform が掛かると効かなくなる
   （そこで合成が閉じるため）。ヒーローに出てくる動きを付けたとたん、白い
   四角が浮き出てしまう。
   そこで書き出しの時点で地を抜く。画像の縁から白いところをたどって
   「外側」を塗り分け、その部分だけ透明にする。箱の中の白（フタの表）は
   外とつながっていないので残る。境目は少しぼかして、輪郭のギザギザを消す。

3. **箱の輪郭を自動で見つけて正方形に切り出す**
   地色から離れた画素の外接矩形を取り、落ち影のぶんだけ余白を足して正方形にする。
   手で座標を決めないので、元画像を差し替えても同じ手順で作り直せる。
"""

import os
import sys

import numpy as np
from PIL import Image, ImageFilter

SRC = sys.argv[1] if len(sys.argv) > 1 else "tools/hero-box-src.jpg"
DST = sys.argv[2] if len(sys.argv) > 2 else "assets/img/hero-box.webp"

BORDER = 60      # 地色を測る縁の幅
TOL = 12         # 地色とみなす明るさの幅
BLUR = 90        # 照明のムラを取り出す暈しの半径
PAD_RATIO = 0.06 # 落ち影のために残す余白（箱の大きさに対する割合）
ALPHA_TOL = 10   # ここまで白ければ「地」とみなす
FEATHER = 1.2    # 輪郭のぼかし（画素）


def main():
    im = Image.open(SRC).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    h, w, _ = a.shape

    g = np.asarray(im.convert("L")).astype(np.float32)
    border = np.concatenate([g[:BORDER].ravel(), g[-BORDER:].ravel(),
                             g[:, :BORDER].ravel(), g[:, -BORDER:].ravel()])
    bg = float(np.median(border))

    # 箱の画素は明るさが大きく外れるので推定から除き、周囲の地色で埋めてから暈す
    mask = np.abs(g - bg) > TOL
    filled = g.copy()
    filled[mask] = bg
    flat = np.asarray(Image.fromarray(filled.astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(BLUR))).astype(np.float32)
    flat = np.clip(flat, 1, None)

    norm = Image.fromarray(np.clip(a / flat[:, :, None] * 255.0, 0, 255).astype(np.uint8))
    print(f"地色 {bg:.0f} -> 255 に正規化")

    gn = np.asarray(norm.convert("L")).astype(int)
    m = np.abs(gn - 255) > TOL
    ys, xs = np.where(m)
    if len(xs) == 0:
        raise SystemExit("箱が見つかりません。TOL を見直してください。")
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()

    pad = int(max(x1 - x0, y1 - y0) * PAD_RATIO)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    side = int(min(max(x1 - x0, y1 - y0) + pad * 2, h, w))
    L = max(0, min(int(round(cx - side / 2)), w - side))
    T = max(0, min(int(round(cy - side / 2)), h - side))

    cut = norm.crop((L, T, L + side, T + side))

    # ---- 地を透明にする ----
    # 縁から白いところをたどって「外側」を塗り分ける。箱の中の白（フタの表）は
    # 外とつながっていないので残り、落ち影も明るさに応じて薄く残る。
    gc = np.asarray(cut.convert("L")).astype(int)
    white = np.abs(gc - 255) <= ALPHA_TOL
    outside = _flood_from_edges(white)

    alpha = np.full(gc.shape, 255, dtype=np.float32)
    alpha[outside] = 0
    # 落ち影は白に近いほど薄く。輪郭の内側は触らない
    soft = np.clip((255 - gc) * 8, 0, 255).astype(np.float32)
    alpha = np.where(outside, 0, np.maximum(alpha, soft))
    am = Image.fromarray(alpha.astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(FEATHER))

    cut.putalpha(am)
    # PNG だと 330KB を超える。透過を保ったまま軽くしたいので WebP にする
    cut.save(DST, "WEBP", quality=86, method=6)

    out = Image.open(DST)
    aa = np.asarray(out.split()[-1])
    corners = [int(aa[y, x]) for y, x in [(4, 4), (4, -5), (-5, 4), (-5, -5)]]
    kb = os.path.getsize(DST) // 1024
    print(f"{DST} <- 切り出し {out.size} / {kb}KB / 四隅の不透明度 {corners}")
    if max(corners) > 4:
        print("⚠ 四隅が透明になっていません。板に見える可能性があります。")


def _flood_from_edges(white):
    """縁から白いところをたどって「外側」を塗り分ける。
       scipy を入れずに済ませたいので、上下左右の伝播を収束するまで繰り返す。"""
    h, w = white.shape
    out = np.zeros_like(white)
    out[0] |= white[0]; out[-1] |= white[-1]
    out[:, 0] |= white[:, 0]; out[:, -1] |= white[:, -1]
    while True:
        before = out.sum()
        for _ in range(2):
            out[1:] |= out[:-1] & white[1:]
            out[:, 1:] |= out[:, :-1] & white[:, 1:]
            out[:-1] |= out[1:] & white[:-1]
            out[:, :-1] |= out[:, 1:] & white[:, :-1]
        if out.sum() == before:
            return out


if __name__ == "__main__":
    main()
