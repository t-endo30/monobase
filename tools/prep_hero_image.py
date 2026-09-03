#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ヒーローの箱写真を、紙面に置ける形に整える。

    python3 tools/prep_hero_image.py [元画像] [出力先]
    （既定: tools/hero-box-src.jpg -> assets/img/hero-box.jpg）
    元画像は assets/ に置かない。配信に乗るうえ、画像の重さの検査に引っかかるため。

やっていること:

1. **地色を白(255)に正規化する**
   元画像の地色は 235 前後で、紙面の色（--bg:#f4f4f2）より暗い。そのまま置くと
   写真が「四角い板」として浮いて見える。CSS の brightness やマスクでごまかすと、
   フタの先端が切れたり、地の色を変えるたびに破綻する。
   照明のムラを面で推定して割り、地色を白に揃えておけば、CSS 側は
   mix-blend-mode:multiply で重ねるだけでよい。multiply は白を素通しするので、
   紙面の色を何色に変えても板は出ない。

2. **箱の輪郭を自動で見つけて正方形に切り出す**
   地色から離れた画素の外接矩形を取り、落ち影のぶんだけ余白を足して正方形にする。
   手で座標を決めないので、元画像を差し替えても同じ手順で作り直せる。
"""

import sys
import numpy as np
from PIL import Image, ImageFilter

SRC = sys.argv[1] if len(sys.argv) > 1 else "tools/hero-box-src.jpg"
DST = sys.argv[2] if len(sys.argv) > 2 else "assets/img/hero-box.jpg"

BORDER = 60      # 地色を測る縁の幅
TOL = 12         # 地色とみなす明るさの幅
BLUR = 90        # 照明のムラを取り出す暈しの半径
PAD_RATIO = 0.06 # 落ち影のために残す余白（箱の大きさに対する割合）


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

    norm.crop((L, T, L + side, T + side)).save(
        DST, quality=92, optimize=True, progressive=True)

    out = Image.open(DST)
    chk = np.asarray(out.convert("L"))
    corners = [int(chk[y, x]) for y, x in [(4, 4), (4, -5), (-5, 4), (-5, -5)]]
    print(f"{DST} <- 切り出し {out.size} / 四隅の明るさ {corners}")
    if min(corners) < 250:
        print("⚠ 四隅が白くありません。板に見える可能性があります。")


if __name__ == "__main__":
    main()
