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
NG = ["絶対", "必ず", "確実に", "保証します", "間違いなく", "100%",
      "誰でも", "永久に", "完治", "最安値", "業界No.1", "日本一"]

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

    if hits:
        print(f"::error::保証・断定表現が {len(hits)} 件見つかりました。")
        for f, w, ctx in hits:
            print(f"  [{w}] {f}\n       …{ctx}…")
        return 1

    print(f"✅ 禁止表現なし（{len(glob.glob('articles/*.html'))} 記事を検査）")
    return 0

if __name__ == "__main__":
    sys.exit(main())
