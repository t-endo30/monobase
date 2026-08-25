#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事に張った販売先リンクが、まだ生きているかを確かめる。

楽天市場とYahoo!ショッピングはモール型で、店舗が出品をやめると
商品ページごと消える。Amazonの商品ページは在庫切れでも残るが、
出品が取り下げられれば同じことが起きる。
放置すると読者を404へ送り、その記事の収益はゼロになる。

  $ python3 tools/check_links.py           # 販売先リンクを確認
  $ python3 tools/check_links.py --all     # 記事内の外部リンクも含める

毎回のデプロイでは走らせない。外部サイトへの通信は速度が読めず、
先方の都合で失敗もするため、ビルドを止める理由にすると運用が壊れる。
週に1度、GitHub Actions（links.yml）から実行して報告だけさせる。
"""
import json, io, os, re, sys, time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TIMEOUT = 12           # 1本あたりの待ち時間（秒）
WORKERS = 6            # 同時に投げる本数。相手先に負荷をかけない範囲
RETRY = 1              # 失敗時の再試行回数
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# 生きていると見なす応答。
#   403 … Botよけ。ページ自体は存在する
#   405 … HEADを受け付けないだけ
LIVE = {200, 203, 206, 301, 302, 303, 307, 308, 403, 405, 429}


def fetch(url):
    """HEADで叩き、拒まれたらGETで確かめる。本文は読まない。"""
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method)
        req.add_header("User-Agent", UA)
        req.add_header("Accept-Language", "ja,en;q=0.8")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status, ""
        except urllib.error.HTTPError as ex:
            if method == "HEAD" and ex.code in (403, 405, 400):
                continue          # GETで確かめ直す
            return ex.code, ""
        except urllib.error.URLError as ex:
            return 0, str(ex.reason)
        except Exception as ex:                      # noqa: BLE001
            return 0, type(ex).__name__
    return 0, "unreachable"


def check(item):
    slug, shop, url = item
    for i in range(RETRY + 1):
        code, note = fetch(url)
        if code in LIVE:
            return (slug, shop, url, code, note, True)
        if i < RETRY:
            time.sleep(1.5)       # 一時的な失敗を再試行で拾う
    return (slug, shop, url, code, note, False)


def collect(arts, include_body=False):
    """確かめる対象を集める。公開記事だけを見る。"""
    out = []
    for a in arts:
        if not a.get("published"):
            continue
        slug = a.get("slug", "?")
        asin = (a.get("asin") or "").strip().upper()
        if asin:
            out.append((slug, "Amazon", f"https://www.amazon.co.jp/dp/{asin}"))
        elif (a.get("amazon_url") or "").strip():
            out.append((slug, "Amazon", a["amazon_url"].strip()))
        for key, label in (("rakuten_url", "楽天市場"),
                           ("yahoo_url", "Yahoo!")):
            u = (a.get(key) or "").strip()
            if u:
                out.append((slug, label, u))
        if include_body:
            blob = json.dumps(a, ensure_ascii=False)
            for u in set(re.findall(r'https?://[^\s"\'<>）]+', blob)):
                if "amazon.co.jp" in u or "rakuten.co.jp" in u \
                        or "yahoo.co.jp" in u or "monobase.site" in u:
                    continue
                out.append((slug, "本文", u))
    return out


def main():
    include_body = "--all" in sys.argv
    p = os.path.join(ROOT, "content", "articles.json")
    arts = json.load(io.open(p, encoding="utf-8"))
    targets = collect(arts, include_body)

    if not targets:
        print("確認するリンクがありません。")
        return 0

    print(f"販売先リンク {len(targets)} 本を確認します"
          f"（同時 {WORKERS} 本・1本あたり最長 {TIMEOUT} 秒）")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        results = list(ex.map(check, targets))
    dt = time.time() - t0

    dead = [r for r in results if not r[5]]
    for slug, shop, url, code, note, _ in dead:
        why = f"HTTP {code}" if code else (note or "接続できません")
        print(f"::warning::{slug}: {shop} のリンクが開けません（{why}）\n    {url}")

    print(f"\n所要 {dt:.1f} 秒 / 生存 {len(results) - len(dead)} 本 / 要確認 {len(dead)} 本")
    if dead:
        print("\n出品が終了している可能性があります。"
              "管理画面で該当ショップのURLを貼り直すか、空欄にしてボタンを消してください。")
        # 外部サイトの都合で落ちるため、ここでは失敗にしない。報告だけ。
    else:
        print("✅ すべての販売先リンクが生きています。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
