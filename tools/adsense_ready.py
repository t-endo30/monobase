#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AdSense を再申請してよい頃合いかを判定する（2026-09-29 導入）。

「有用性の低いコンテンツ」で落ちたあと、弱い記事を noindex にした
（build.py の indexable()）。その効果が出るのは、Google がそれらを
クロールし直して索引から外したあと。外れきる前に再申請すると、
同じ理由でまた落ちる。

判定：
  1. noindex にした日（NOINDEX_SINCE）から MIN_DAYS 日たっている
  2. noindex の記事のうち、Google にまだ「登録済み」（verdict PASS）で
     残っているものが MAX_STILL_INDEXED 本以下

noindex の記事は、生成済みの articles/*.html の robots メタで拾う
（build.py の判定と必ず一致させるため）。URL検査APIを1件ずつ引くので、
150本で15分ほどかかる。

  $ python3 tools/adsense_ready.py            # 判定して結果を出す
  $ python3 tools/adsense_ready.py --limit 20 # 試しに20件だけ

終了コード：0＝まだ / 10＝再申請してよい / 1＝エラー
GITHUB_STEP_SUMMARY があれば、そこにも結果を書く。
必要なもの（tools/fetch_gsc_ranks.py と同じ）
  GSC_SITE_URL / GOOGLE_APPLICATION_CREDENTIALS
"""
import argparse, datetime, glob, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_gsc_ranks import get_service, site_url  # noqa: E402
from gsc_inspect import inspect  # noqa: E402

NOINDEX_SINCE = datetime.date(2026, 9, 29)
MIN_DAYS = 14
MAX_STILL_INDEXED = 3
BASE = "https://monobase.site"
READY = 10


def noindex_urls():
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "articles", "*.html"))):
        head = open(path, encoding="utf-8").read(20000)
        if 'name="robots" content="noindex' in head:
            slug = os.path.basename(path)[:-len(".html")]
            out.append(f"{BASE}/articles/{slug}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sleep", type=float, default=0.2)
    args = ap.parse_args()

    today = datetime.date.today()
    days = (today - NOINDEX_SINCE).days
    urls = noindex_urls()
    if args.limit:
        urls = urls[:args.limit]
    prop = site_url()
    if not prop:
        print("::error::サイトURLが分かりません。")
        return 1

    service = get_service()
    still, blocked, unknown, failed = [], 0, 0, 0
    for i, u in enumerate(urls, 1):
        try:
            r = inspect(service, prop, u)
        except Exception as ex:                                # noqa: BLE001
            failed += 1
            print(f"  検査できず {u} … {str(ex)[:120]}")
            continue
        if r.get("verdict") == "PASS":
            still.append((u, (r.get("lastCrawlTime") or "")[:10]))
        elif r.get("indexingState") == "BLOCKED_BY_META_TAG":
            blocked += 1
        else:
            unknown += 1          # まだ知られていない等。索引に無いので問題なし
        if i % 25 == 0:
            print(f"  …{i}/{len(urls)}件")
        time.sleep(args.sleep)

    ready = (days >= MIN_DAYS and len(still) <= MAX_STILL_INDEXED
             and failed <= len(urls) // 10)
    lines = [
        f"## AdSense 再申請の判定（{today}）",
        "",
        f"- noindex にしてから：{days}日（目安 {MIN_DAYS}日以上）",
        f"- noindex の記事：{len(urls)}本を検査",
        f"  - まだ登録済みで残っている：**{len(still)}本**（目安 {MAX_STILL_INDEXED}本以下）",
        f"  - noindex を読んで外れた：{blocked}本",
        f"  - 索引に無い（未認識など）：{unknown}本",
        f"  - 検査できず：{failed}本",
        "",
        "**判定：再申請してよい**" if ready else "判定：まだ",
    ]
    if still:
        lines += ["", "### まだ登録済みの記事", ""]
        lines += [f"- {u}（最終クロール {c or '不明'}）" for u, c in still[:30]]
    text = "\n".join(lines) + "\n"
    print(text)
    summ = os.environ.get("GITHUB_STEP_SUMMARY")
    if summ:
        open(summ, "a", encoding="utf-8").write(text)
    # 通知（Issue）の本文に使う。リポジトリには置かない
    tmp = os.environ.get("RUNNER_TEMP")
    if tmp:
        open(os.path.join(tmp, "adsense-ready.md"), "w", encoding="utf-8").write(text)
    return READY if ready else 0


if __name__ == "__main__":
    sys.exit(main())
