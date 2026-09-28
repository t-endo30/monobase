#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事のサムネイル用SVGを生成する。

方針：
・一覧に出すのはモールの実物写真だけにしたので、写真が無い記事
  （特集・選び方・Amazonのみのレビュー）にはこの絵が出る。題名を
  大きく入れて、絵だけで何の記事か分かるようにする。「準備中」の類は
  書かない。作りかけのサイトに見えるうえ、読む人の役に立たない。
・以前の版は灰色の地に灰色の棒で、文字は字数で機械的に折っていた。
  一覧では仮の画像にしか見えず、「エアリ／ーカール」「KP／C-MA4」の
  ように語の途中で切れていた（2026-09-29に作り直し）。
・地色はカテゴリーごとの濃い色、文字は白。並んだときに分野の見分けが
  付き、商品写真（白地が多い）の中でも埋もれない。
・キャンバスは正方形。一覧のカードは 1:1 だが、特集のスライダーと
  記事の見出し画像は 16:9 に切り取られる（object-fit:cover）。
  1200四方を16:9で切ると上下が 262px ずつ落ちるので、読ませる文字は
  すべて y=290〜910 の帯に置く。帯の外は飾りだけにする。
・SVG は <img> で読むので Webフォントは効かず、文字の幅も測れない。
  全角1文字＝1em、半角＝約0.6em で見積もって、改行位置と文字の大きさを
  決める。
・外部素材を使わないため著作権・規約のリスクがない。
"""
import os
import re

# カテゴリーごとの地色（濃い側, 明るい側）。白い文字が十分読める濃さにする。
CAT_BG = {
    "feature":    ("#1B2640", "#2E4470"),
    "appliance":  ("#164B63", "#23708F"),
    "smartphone": ("#23336B", "#3A51A0"),
    "pc":         ("#1F2F48", "#34507A"),
    "av":         ("#3A2458", "#5A3A86"),
    "camera":     ("#26292F", "#454B55"),
    "beauty":     ("#7A2E4A", "#A8476A"),
    "health":     ("#1E5E52", "#2F8A78"),
    "kitchen":    ("#7E3B1C", "#AE5A2E"),
    "daily":      ("#3E4F2A", "#5E7640"),
    "fashion":    ("#512B3A", "#7A4458"),
    "furniture":  ("#5A4128", "#84613E"),
    "pet":        ("#7A4E17", "#A87026"),
    "travel":     ("#164F66", "#237796"),
}
DEFAULT_BG = ("#2A2D33", "#474C55")
ACCENT = "#FFD36B"        # 数字（9製品・5選）を目立たせる色
WHITE = "#FFFFFF"

W = 1200
TEXT_W = 1000             # 題名に使える横幅
TOP, BOTTOM = 290, 910    # 16:9 に切り取られても残る帯

FAM = ("&quot;Hiragino Sans&quot;, &quot;Hiragino Kaku Gothic ProN&quot;, "
       "&quot;Noto Sans JP&quot;, &quot;Yu Gothic&quot;, &quot;Meiryo&quot;, sans-serif")


def esc(t):
    return (str(t or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# ---------------------------------------------------------------- 文字の幅
def cw(ch):
    """1文字の幅（em）。ヒラギノ角ゴの実測に近い値。"""
    if ch == " ":
        return 0.3
    if ord(ch) < 0x80:
        if ch in "il.,:;'|!":
            return 0.3
        if ch in "MWmw":
            return 0.92
        if ch.isupper():
            return 0.74
        if ch.isdigit():
            return 0.66
        return 0.62
    return 1.0


def width(s):
    return sum(cw(c) for c in s)


# ---------------------------------------------------------------- 改行位置
def ctype(ch):
    if re.match(r"[A-Za-z0-9]", ch):
        return "a"
    if re.match(r"[ァ-ヶー]", ch):
        return "k"
    if re.match(r"[ぁ-ん]", ch):
        return "h"
    if re.match(r"[一-龠々〆]", ch):
        return "j"
    return "p"


NO_HEAD = set("、。・ー）」』】〕,.:!?！？％%ぁぃぅぇぉゃゅょっゎァィゥェォャュョッヮ〜～")
NO_TAIL = set("（「『【〔")
GLUE = set("-+/._&'#")        # 型番の中の記号。前後で切らない
PARTICLE = set("のをとでにがはもへや")
COUNTER = set("選製機本点種台つ個枚型")


def break_cost(s, i):
    """s[i-1] と s[i] の間で改行するときの減点。None は改行しない。"""
    a, b = s[i - 1], s[i]
    if b in NO_HEAD or a in NO_TAIL or a in GLUE or b in GLUE:
        return None
    ta, tb = ctype(a), ctype(b)
    if a.isdigit() and b in COUNTER:      # 「5選」「9製品」の中
        return None
    if ta == tb == "a":                   # 英数字の語（型番）の中
        return None
    if ta == tb == "k":                   # 長いカタカナ語の中。他に切れ目が無いときだけ
        return 6.0
    if a == " " or b == " ":
        return 0.0
    if a in "・、":
        return 0.3
    if ta == "h" and tb != "h":
        return 0.6 if a in PARTICLE else 3.0   # 「の／選び方」は良い、「選び／方」は悪い
    if {ta, tb} == {"j", "k"}:
        return 2.5                        # 「防犯カメラ」のような複合語の中であることが多い
    if ta != tb:
        return 1.2                        # 文字の種類の変わり目（カメラ／9製品）
    if ta == "j":
        return 4.0                        # 漢字の熟語の中
    return 3.0


def layout(text, max_lines, fs_max, fs_min, line_h, max_h):
    """題名を max_lines 行までに折り、行の並びと文字サイズを返す。
       行ごとの幅がそろい、かつ語の切れ目で折れる並びを選ぶ。"""
    s = " ".join(str(text or "").split())
    if not s:
        return [], fs_max
    cuts = [(i, c) for i in range(1, len(s)) for c in [break_cost(s, i)] if c is not None]

    best = None

    def consider(breaks, pen):
        nonlocal best
        lines, last = [], 0
        for i in breaks:
            lines.append(s[last:i].strip())
            last = i
        lines.append(s[last:].strip())
        if any(not l for l in lines):
            return
        maxw = max(width(l) for l in lines)
        fs = min(fs_max, TEXT_W / maxw, max_h / (len(lines) * line_h))
        # 大きく読めることを最優先に、変な位置での改行と行数の多さを減点する
        score = fs - pen * 15 - (len(lines) - 1) * 6
        if best is None or score > best[0]:
            best = (score, lines, fs)

    consider([], 0)
    if max_lines >= 2:
        for i, c in cuts:
            consider([i], c)
    if max_lines >= 3:
        for x, (i, c1) in enumerate(cuts):
            for j, c2 in cuts[x + 1:]:
                consider([i, j], c1 + c2)

    _, lines, fs = best
    if fs < fs_min:
        # 入りきらない。最小の大きさで収まるところまで削って「…」を付ける
        fs = fs_min
        cap = TEXT_W / fs
        out = []
        for l in lines:
            if width(l) > cap:
                while l and width(l + "…") > cap:
                    l = l[:-1]
                l += "…"
            out.append(l)
        lines = out
    return lines, fs


# ---------------------------------------------------------------- 描画
EMPH = re.compile(r"(\d+(?:製品|選|機種|本|点|種類?|台|つ))")


def rich(line):
    """「9製品」「5選」のような数を差し色にする。"""
    out = []
    for part in EMPH.split(line):
        if not part:
            continue
        if EMPH.fullmatch(part):
            out.append(f'<tspan fill="{ACCENT}">{esc(part)}</tspan>')
        else:
            out.append(esc(part))
    return "".join(out)


def build(slug, title, category, cat_label, site_name, out_dir, kind_label=""):
    """kind_label は「特集」「レビュー」などの札。cat_label は札の横に出す
       分野名（サブ区分があればそちら）。"""
    dark, light = CAT_BG.get(category, DEFAULT_BG)
    raw = " ".join(str(title or "").split())
    main, _, sub = raw.partition("｜")
    main, sub = main.strip(), sub.strip()

    # 縦の配置：札 → 題名 → 補足 を、帯の中（下端の区切り線とサイト名の
    # 上まで）で上下中央にそろえる。題名の大きさは、残りの高さで決める。
    avail = BOTTOM - TOP - 20 - 90
    tag_h, gap1 = 76, 40
    sub_lines, sub_fs = layout(sub, 1, 60, 42, 1.3, 80) if sub else ([], 0)
    gap2 = 30 if sub_lines else 0
    sub_h = sub_fs * 1.3 if sub_lines else 0
    lines, fs = layout(main, 3, 132, 64, 1.22, avail - tag_h - gap1 - gap2 - sub_h)
    title_h = len(lines) * fs * 1.22
    block = tag_h + gap1 + title_h + gap2 + sub_h
    y0 = TOP + 20 + max(0, (avail - block) / 2)

    parts = []
    # 札（種類）と分野名
    x = 100
    if kind_label:
        tw = width(kind_label) * 50 + 60
        parts.append(f'<rect x="{x}" y="{y0:.0f}" width="{tw:.0f}" height="{tag_h}" rx="38" fill="{WHITE}"/>')
        parts.append(f'<text x="{x + tw / 2:.0f}" y="{y0 + 55:.0f}" text-anchor="middle" '
                     f'font-family="{FAM}" font-size="50" font-weight="800" fill="{dark}">{esc(kind_label)}</text>')
        x += tw + 26
    if cat_label:
        parts.append(f'<text x="{x}" y="{y0 + 55:.0f}" font-family="{FAM}" font-size="48" '
                     f'font-weight="600" fill="{WHITE}" fill-opacity=".82">{esc(cat_label)}</text>')

    # 題名（左そろえ。雑誌の表紙のように、行頭の線がそろうと読みやすい）
    y = y0 + tag_h + gap1 + fs * 0.92
    for l in lines:
        parts.append(f'<text x="100" y="{y:.0f}" font-family="{FAM}" font-size="{fs:.0f}" '
                     f'font-weight="800" fill="{WHITE}" letter-spacing="{-fs * 0.02:.1f}">{rich(l)}</text>')
        y += fs * 1.22
    if sub_lines:
        y += gap2 - fs * 0.92 + sub_fs * 0.9     # y は次の行の基線にいるので、最終行の下端まで戻す
        parts.append(f'<text x="100" y="{y:.0f}" font-family="{FAM}" font-size="{sub_fs:.0f}" '
                     f'font-weight="600" fill="{WHITE}" fill-opacity=".78">{rich(sub_lines[0])}</text>')

    # 帯の下端：区切り線とサイト名
    parts.append(f'<rect x="100" y="{BOTTOM - 62}" width="120" height="8" rx="4" fill="{ACCENT}"/>')
    parts.append(f'<text x="1100" y="{BOTTOM - 44}" text-anchor="end" font-family="{FAM}" '
                 f'font-size="34" font-weight="700" letter-spacing="8" fill="{WHITE}" '
                 f'fill-opacity=".6">{esc(site_name or "MONOBASE")}</text>')

    body = "\n  ".join(parts)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}" role="img" aria-label="{esc(raw)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{light}"/>
      <stop offset="100%" stop-color="{dark}"/>
    </linearGradient>
    <pattern id="dots" width="36" height="36" patternUnits="userSpaceOnUse">
      <circle cx="18" cy="18" r="2.2" fill="{WHITE}" fill-opacity=".07"/>
    </pattern>
  </defs>
  <rect width="{W}" height="{W}" fill="url(#bg)"/>
  <rect width="{W}" height="{W}" fill="url(#dots)"/>
  <circle cx="1080" cy="140" r="330" fill="{WHITE}" fill-opacity=".06"/>
  <circle cx="1080" cy="140" r="200" fill="{WHITE}" fill-opacity=".05"/>
  <circle cx="90" cy="1130" r="260" fill="{WHITE}" fill-opacity=".05"/>
  {body}
</svg>
'''
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, slug + ".svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return path
