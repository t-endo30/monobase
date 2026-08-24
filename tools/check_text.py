#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事本文の禁止表現チェック。
   景品表示法・薬機法・Amazonアソシエイト規約のリスクになる
   断定／保証表現が混入していないか検査する。
   $ python3 tools/check_text.py
"""
import re, os, sys, glob, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 保証・断定表現（記事本文に出してはいけない）
# 単語として出た時点で問題になるもの
NG = ["絶対", "必ず", "確実に", "保証します", "間違いなく", "100%",
      "誰でも", "永久に", "完治", "業界No.1", "日本一"]

# 文脈によっては問題ない語。断定の主張として使われた場合だけ検出する
NG_CONTEXT = [
    r"最安値(?:です|でした|保証|を保証|！|。)",   # 「過去の最安値を確認」は対象外
    r"業界最安",
    r"日本最[安大高]",
]

# 本文にそのまま出てしまったHTMLタグ。テンプレート側で
# エスケープしすぎると <strong> が文字として表示される。
ESCAPED_TAG = re.compile(r"&lt;/?(?:strong|em|b|i|br|span|a|p|ul|li|code)\b[^&]{0,40}?&gt;")


def check_escaped_tags():
    hits = []
    for f in sorted(glob.glob("articles/*.html")) + sorted(glob.glob("*.html")):
        if os.path.basename(f) == "admin.html":
            continue          # 管理画面の説明文には例として書いてある
        raw = open(f, encoding="utf-8").read()
        for m in ESCAPED_TAG.finditer(raw):
            ctx = raw[max(0, m.start() - 30): m.start() + 40].replace("\n", " ").strip()
            hits.append((f, m.group(0), ctx))
    return hits


def main():
    os.chdir(ROOT)
    hits = []
    for f in sorted(glob.glob("articles/*.html")):
        raw = open(f, encoding="utf-8").read()
        # ヘッダー・フッター・ナビは対象外。記事本文だけを検査する
        m = re.search(r'<article class="card-surface".*?</article>', raw, re.S)
        if not m:
            continue
        s = html.unescape(re.sub(r"<[^>]+>", "", m.group(0)))
        for w in NG:
            for m in re.finditer(re.escape(w), s):
                ctx = s[max(0, m.start() - 25): m.start() + 25].replace("\n", " ").strip()
                hits.append((f, w, ctx))
        for pat in NG_CONTEXT:
            for m in re.finditer(pat, s):
                ctx = s[max(0, m.start() - 25): m.start() + 25].replace("\n", " ").strip()
                hits.append((f, m.group(0), ctx))

    tags = check_escaped_tags()
    if tags:
        print(f"::error::HTMLタグが本文にそのまま出ています（{len(tags)} 件）。"
              "build.py でエスケープしすぎている可能性があります。")
        for f, w, ctx in tags[:20]:
            print(f"  [{w}] {f}\n       …{ctx}…")

    if hits:
        print(f"::error::保証・断定表現が {len(hits)} 件見つかりました。")
        for f, w, ctx in hits:
            print(f"  [{w}] {f}\n       …{ctx}…")
    if hits or tags:
        return 1

    print(f"✅ 禁止表現・タグの露出なし（{len(glob.glob('articles/*.html'))} 記事を検査）")
    return 0

if __name__ == "__main__":
    sys.exit(main())
