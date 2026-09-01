#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ブランドマーク（ヘッダーの16×16ドット絵ロゴ）から、favicon と OGP のデフォルト画像を作る。

  build.py の LOGO_CELLS がロゴの唯一の原稿。ここを直したら、
  このスクリプトを再実行すれば favicon・OGP にも同じ見た目が反映される。

  $ python3 tools/make_logo_assets.py

生成物:
  assets/img/favicon.svg          … ブラウザタブ用（ベクター、常に鮮明）
  assets/img/favicon-32.png       … 32×32（favicon.svgに未対応の環境向け）
  assets/img/apple-touch-icon.png … 180×180（iOSのホーム画面用）
  assets/img/og-default.jpg       … 1200×630（記事に画像が無いページのOGP既定値）
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from PIL import Image, ImageDraw, ImageFont

import build as B  # LOGO_CELLS / NAME / TAGLINE を再利用する

# CSS変数のフォールバック値をそのまま使う（実際にヘッダーに出ている色と揃える）
COLORS = {
    "line": (255, 255, 255, 240),
    "box":  (255, 153, 0, 255),
    "in":   (194, 94, 0, 255),
    "seam": (26, 16, 6, 230),
    "outline": (255, 255, 255, 240),
}
NAVY = (37, 40, 45, 255)

IMG_DIR = os.path.join(ROOT, "assets", "img")


def draw_logo(draw, ox, oy, scale):
    """16×16のセル定義を、原点(ox,oy)・1マス=scale px で描く。"""
    for key in ("line", "box", "in", "seam", "outline"):
        for x, y, w in B.LOGO_CELLS[key]:
            draw.rectangle(
                [ox + x * scale, oy + y * scale,
                 ox + (x + w) * scale - 1, oy + (y + 1) * scale - 1],
                fill=COLORS[key])


def rounded_navy(size, radius):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=NAVY)
    return im, d


def make_icon(size, path, radius_ratio=0.22):
    im, d = rounded_navy(size, int(size * radius_ratio))
    # ロゴは16マス角。周囲に少し余白を持たせて中央に置く。
    scale = size / 20
    ox = oy = scale
    draw_logo(d, ox, oy, scale)
    im.save(path)
    print(f"  wrote {path} ({size}x{size})")


def make_favicon_svg(path):
    paths = "".join(
        f'<path fill="rgba({COLORS[k][0]},{COLORS[k][1]},{COLORS[k][2]},{COLORS[k][3]/255:.2f})" '
        f'd="{B._logo_path_d(B.LOGO_CELLS[k])}"/>'
        for k in ("line", "box", "in", "seam", "outline"))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">'
           f'<rect x="0" y="0" width="20" height="20" rx="4.4" '
           f'fill="rgb({NAVY[0]},{NAVY[1]},{NAVY[2]})"/>'
           f'<g transform="translate(1,1)">{paths}</g></svg>')
    io.open(path, "w", encoding="utf-8").write(svg)
    print(f"  wrote {path}")


def make_og_default(path):
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), NAVY[:3])
    d = ImageDraw.Draw(im, "RGBA")

    def font(paths, size):
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return ImageFont.load_default()

    jp_bold = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    name_font = font(jp_bold, 46)
    tag_font = font(jp_bold, 21)

    scale = 16
    logo_w = 16 * scale
    name = B.NAME
    tag = B.TAGLINE
    name_bbox = d.textbbox((0, 0), name, font=name_font)
    name_h = name_bbox[3] - name_bbox[1]
    tag_bbox = d.textbbox((0, 0), tag, font=tag_font)
    tag_h = tag_bbox[3] - tag_bbox[1]

    gap_logo_name, gap_name_tag = 26, 12
    block_h = logo_w + gap_logo_name + name_h + gap_name_tag + tag_h
    oy = (H - block_h) // 2
    ox = (W - logo_w) // 2
    draw_logo(d, ox, oy, scale)

    ny = oy + logo_w + gap_logo_name
    d.text(((W - (name_bbox[2] - name_bbox[0])) / 2 - name_bbox[0], ny - name_bbox[1]),
           name, font=name_font, fill=(255, 255, 255, 255))
    ty = ny + name_h + gap_name_tag
    d.text(((W - (tag_bbox[2] - tag_bbox[0])) / 2 - tag_bbox[0], ty - tag_bbox[1]),
           tag, font=tag_font, fill=(255, 153, 0, 255))
    im.save(path, "JPEG", quality=88)
    print(f"  wrote {path}")


def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    make_favicon_svg(os.path.join(IMG_DIR, "favicon.svg"))
    make_icon(32, os.path.join(IMG_DIR, "favicon-32.png"))
    make_icon(180, os.path.join(IMG_DIR, "apple-touch-icon.png"), radius_ratio=0.18)
    make_og_default(os.path.join(IMG_DIR, "og-default.jpg"))
    print("done.")


if __name__ == "__main__":
    main()
