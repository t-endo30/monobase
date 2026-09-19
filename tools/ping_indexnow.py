#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新したページを IndexNow で知らせる。

  $ python3 tools/ping_indexnow.py             # 直前のコミットで変わった記事
  $ python3 tools/ping_indexnow.py --all       # 公開中の全ページ
  $ python3 tools/ping_indexnow.py --dry-run   # 送らずに、送る先だけ出す

IndexNow は Bing・Yandex・Naver・Seznam が受け取る共通の窓口で、
1回の通知が参加している全検索エンジンに配られる。
**Google は参加していない。** Google はサイトマップとリンクから拾う。

相手は content/site.json の indexnow.key に入れた鍵で持ち主を確かめる。
build.py がその鍵を <鍵>.txt としてサイトの直下に置いているので、
鍵を変えたら build.py を流し直すこと（先に古い鍵のファイルが消えると、
通知が拒否される）。

送りすぎても罰則はないが、変わっていないURLを毎回送るのは相手の負担に
なるため、既定では直前のコミットで変わった記事だけを送る。
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT = 20


def site():
    return json.load(io.open(os.path.join(ROOT, "content", "site.json"),
                             encoding="utf-8"))


def public_url(base, path, clean):
    """配信しているURLの形にそろえる。clean_urls なら .html を落とす。"""
    u = f"{base}/{path}"
    return u[:-len(".html")] if clean and u.endswith(".html") else u


# 中身が変わっていなくても、ビルドのたびに書き換わる部分。
# ここだけの違いは「更新」として通知しない。
#   data-rank … GA4のアクセス数を全記事の <body> に焼き込んでいるため、
#               ランキングを取り直すたびに全記事のHTMLが変わる。
#   ?v=       … 静的ファイルのキャッシュ避けスタンプ。
VOLATILE = (
    (re.compile(r"data-rank='[^']*'"), "data-rank=''"),
    (re.compile(r"\?v=[0-9a-zA-Z]+"), "?v="),
)


def _stable(text):
    """毎回変わる部分を取り除いた中身。"""
    for pat, rep in VOLATILE:
        text = pat.sub(rep, text)
    return text


def _at(rev, path):
    """あるコミット時点のファイルの中身（無ければ None）。"""
    r = subprocess.run(["git", "show", f"{rev}:{path}"],
                       cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def changed_paths(rev):
    """直前のコミットで中身が変わったHTMLを拾う。
       最初のコミットなど、比較先が無いときは空を返す。

       git の差分そのままでは使えない。全記事の <body> にアクセス数
       （data-rank）を焼き込んでいるため、ランキングを取り直すだけで
       126本ぜんぶが「変わった」ことになり、記事を1本出しただけで
       全URLを IndexNow に送り直していた（2026-09-19に判明）。
       毎回変わる部分を取り除いて突き合わせ、本当に中身が変わった
       ものだけを返す。"""
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", rev, "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return []
    paths = [ln.strip() for ln in out.splitlines()
             if ln.strip().endswith(".html")]

    real, cosmetic = [], 0
    for path in paths:
        before, after = _at(rev, path), _at("HEAD", path)
        # 新しく増えたページ（比較先が無い）は、そのまま通知する。
        if before is None or after is None:
            real.append(path)
            continue
        if _stable(before) == _stable(after):
            cosmetic += 1
            continue
        real.append(path)
    if cosmetic:
        print(f"（アクセス数・キャッシュ避けの書き換えだけの {cosmetic} 件は"
              "通知しません）")
    return real


def submit(endpoint, host, key, key_url, urls, dry):
    body = json.dumps({"host": host, "key": key, "keyLocation": key_url,
                       "urlList": urls}, ensure_ascii=False).encode("utf-8")
    if dry:
        print(f"（--dry-run のため送っていません）")
        return 0
    req = urllib.request.Request(endpoint, data=body, method="POST")
    req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            code = r.status
    except urllib.error.HTTPError as ex:
        code = ex.code
        detail = ex.read().decode("utf-8", "replace")[:200]
        # 422 は「鍵が読めない」など、こちら側の設定の問題
        print(f"::warning::IndexNow に断られました（HTTP {code}）{detail}")
        return 1
    except Exception as ex:                           # noqa: BLE001
        print(f"::warning::IndexNow へ送れませんでした（{ex}）")
        return 1
    # 200=受理、202=受理したが鍵の確認は後回し。どちらも成功。
    print(f"✅ {len(urls)} 件のURLを IndexNow に送りました（HTTP {code}）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="公開中の全ページを送る")
    ap.add_argument("--since", default="HEAD~1",
                    help="どのコミットからの変更を見るか（既定 HEAD~1）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    s = site()
    conf = s.get("indexnow") or {}
    key = str(conf.get("key") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9\-]{8,128}", key or ""):
        print("::warning::indexnow.key が未設定のため、通知しません。")
        return 0
    base = s["base_url"].rstrip("/")
    host = base.split("//")[-1]
    clean = bool((s.get("hosting") or {}).get("clean_urls"))
    endpoint = conf.get("endpoint") or "https://api.indexnow.org/indexnow"
    key_url = f"{base}/{key}.txt"

    arts = json.load(io.open(os.path.join(ROOT, "content", "articles.json"),
                             encoding="utf-8"))
    live = {f'articles/{a["slug"]}.html' for a in arts if a.get("published")}

    if args.all:
        paths = sorted(live) + ["index.html", "new.html", "ranking.html"]
    else:
        # 変わったHTMLのうち、公開記事とトップまわりだけを送る。
        # カテゴリー一覧まで送ると、記事1本の更新で何十件も通知が飛ぶ。
        paths = [p for p in changed_paths(args.since)
                 if p in live or p in ("index.html", "new.html", "ranking.html")]
        if not paths:
            print("変わったページはありません。通知しません。")
            return 0

    urls = [public_url(base, p, clean) for p in dict.fromkeys(paths)]
    print(f"送る先：{endpoint}")
    print(f"鍵の置き場所：{key_url}")
    for u in urls[:12]:
        print(f"   {u}")
    if len(urls) > 12:
        print(f"   ほか {len(urls) - 12} 件")
    return submit(endpoint, host, key, key_url, urls, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
