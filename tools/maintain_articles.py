#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公開中の記事を見回り、痛んだものを直す（または公開を止める）。

記事は書いて終わりではありません。モール型の楽天・Yahoo!は店舗が
出品をやめると商品ページごと消え、Amazonも出品が取り下げられれば同じです。
リンクの先が404の記事を公開したままにするのは、読者にとっても
検索エンジンにとっても最悪の状態です。

  $ python3 tools/maintain_articles.py                 # 見るだけ（既定）
  $ python3 tools/maintain_articles.py --apply         # 直して articles.json を更新
  $ python3 tools/maintain_articles.py --apply --push  # 直してビルド・コミット・push
  $ python3 tools/maintain_articles.py --budget 100    # 1回に見る本数を変える
  $ python3 tools/maintain_articles.py --slug xxx      # 1本だけ確かめる

【記事が増えても回るようにする】
  全記事を毎回見に行くと、記事が1000本になったころには
  1回の実行が何時間もかかり、相手のサーバーにも迷惑をかけます。
  そこで **予算制** にしています。

    ・1回に見るのは --budget 本（既定40本）だけ
    ・「最後に見てから長く経っている順」に選ぶ（health.checked を記録）
    ・毎日まわせば、記事1000本でも25日で一巡する
    ・一巡にかかる日数を毎回表示するので、増えたら budget を上げるだけ

【直し方の段階】
  1. 販売先が1つでも生きていれば     … 死んだリンクだけ外して公開を続ける
  2. 販売先が全部死んだら            … published:false にして公開を止める
  3. 更新から日が経ちすぎている      … 古い記事として報告する（止めはしない）

  「止める」は最後の手段です。リンクを1本外せば読める記事を、
  丸ごと引っ込めてしまうと、それまでの検索評価も失われます。
"""
import argparse, io, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_links import fetch, LIVE, WORKERS      # 疎通の判定は1か所にまとめる

SHOPS = [("asin", "Amazon"), ("amazon_url", "Amazon"),
         ("rakuten_url", "楽天市場"), ("yahoo_url", "Yahoo!")]

STALE_DAYS = 365       # これ以上更新していない記事は「古い」として報告する
RETRY = 1


def load(path):
    return json.load(io.open(os.path.join(ROOT, path), encoding="utf-8"))


# 各店のトップページなど、特定の商品を指していないURL。
# 「選び方」「セールカレンダー」のような読み物記事は、商品ではなく
# ここへリンクしていることがある。これは販売先ではないので、
# 生き死にの判定には使わない（つないでも買う相手がいない＝当然）。
GENERIC_PATHS = ("", "/")


def is_generic_shop_url(url):
    """商品ページではなく、店のトップページ等を指していないか。"""
    try:
        from urllib.parse import urlsplit
        parts = urlsplit(url.strip())
        return parts.path in GENERIC_PATHS and not parts.query
    except Exception:                                # noqa: BLE001
        return False


def shop_urls(a):
    """記事が持っている販売先を (キー, 店名, URL) で返す。
       店のトップページのような汎用リンクは、販売先として数えない。"""
    out = []
    asin = (a.get("asin") or "").strip().upper()
    if asin:
        out.append(("asin", "Amazon", f"https://www.amazon.co.jp/dp/{asin}"))
    elif (a.get("amazon_url") or "").strip():
        out.append(("amazon_url", "Amazon", a["amazon_url"].strip()))
    for key, label in (("rakuten_url", "楽天市場"), ("yahoo_url", "Yahoo!")):
        u = (a.get(key) or "").strip()
        if u:
            out.append((key, label, u))
    return [(k, l, u) for k, l, u in out if not is_generic_shop_url(u)]


def days_since(iso):
    try:
        d = datetime.strptime(str(iso)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return 10 ** 4
    return (date.today() - d).days


def pick(arts, budget, slugs):
    """今回見る記事を選ぶ。指定が無ければ「久しく見ていない順」に budget 本。"""
    pub = [a for a in arts if a.get("published")]
    if slugs:
        return [a for a in pub if a.get("slug") in slugs]
    pub.sort(key=lambda a: (days_since((a.get("health") or {}).get("checked")),
                            days_since(a.get("updated") or a.get("date"))),
             reverse=True)
    return pub[:budget]


def check_one(job):
    """1本のリンクを確かめる。check_links と同じ判定を使う。"""
    slug, key, label, url = job
    for i in range(RETRY + 1):
        code, note = fetch(url)
        if code in LIVE:
            return (slug, key, label, url, code, True)
        if i < RETRY:
            time.sleep(1.5)
    return (slug, key, label, url, code, False)


def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=40,
                    help="1回に見る記事の本数（既定40）")
    ap.add_argument("--slug", action="append", default=[],
                    help="この記事だけ見る（何度でも指定できる）")
    ap.add_argument("--strikes", type=int, default=3,
                    help="販売先が全滅していても、続けてこの回数落ちるまでは"
                         "公開を止めない（既定3。通販サイトの一時的な"
                         "アクセス拒否で記事が消えるのを防ぐ）")
    ap.add_argument("--stale-days", type=int, default=STALE_DAYS,
                    help="これ以上更新していない記事を古いとみなす日数")
    ap.add_argument("--apply", action="store_true",
                    help="見つけた問題を articles.json に反映する")
    ap.add_argument("--push", action="store_true",
                    help="反映したうえでビルドし、コミットして push する")
    args = ap.parse_args()

    arts = load("content/articles.json")
    targets = pick(arts, args.budget, set(args.slug))
    published = [a for a in arts if a.get("published")]

    if not targets:
        print("見る記事がありません。")
        return 0

    jobs = []
    for a in targets:
        for key, label, url in shop_urls(a):
            jobs.append((a["slug"], key, label, url))

    print(f"公開 {len(published)} 本のうち {len(targets)} 本を確認します"
          f"（リンク {len(jobs)} 本 / 同時 {WORKERS} 本）")
    if not args.slug and len(published) > args.budget:
        laps = -(-len(published) // args.budget)     # 切り上げ
        print(f"  ※ この本数なら、毎日まわして {laps} 日で全記事を一巡します")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        results = list(ex.map(check_one, jobs))
    dt = time.time() - t0

    dead = {}
    for slug, key, label, url, code, ok in results:
        if not ok:
            dead.setdefault(slug, []).append((key, label, url, code))

    today = date.today().isoformat()
    dropped, stopped, stale, warned = [], [], [], []

    for a in targets:
        slug = a["slug"]
        bad = dead.get(slug, [])
        alive = len(shop_urls(a)) - len(bad)
        h = a.setdefault("health", {})
        h["checked"] = today

        if bad and alive <= 0:
            # 買える場所が1つも無い。ただし1回の失敗で止めてはいけない。
            # 通販サイトは自動アクセスを一時的にはじくことがあり、
            # 実際には生きているのに落ちたように見えることがある。
            # 続けて STRIKES 回落ちたときだけ、公開を止める。
            n = int(h.get("dead_strikes") or 0) + 1
            h["dead"] = [b[2] for b in bad]
            if args.apply:
                h["dead_strikes"] = n
            if n >= args.strikes:
                stopped.append((slug, [b[1] for b in bad]))
                h["stopped_reason"] = "販売先のリンクがすべて切れています"
                if args.apply:
                    a["published"] = False
            else:
                warned.append((slug, [b[1] for b in bad], n, args.strikes))
        elif bad:
            # 生きている販売先が残っている。切れたボタンだけ外す。
            dropped.append((slug, [b[1] for b in bad]))
            h["dead"] = [b[2] for b in bad]
            if args.apply:
                for key, label, url, code in bad:
                    if key == "asin":
                        a["asin"] = ""
                    else:
                        a[key] = ""
        else:
            h.pop("dead", None)
            h.pop("stopped_reason", None)
            h.pop("dead_strikes", None)

        old = days_since(a.get("updated") or a.get("date"))
        if old >= args.stale_days:
            stale.append((slug, old))
            h["stale_days"] = old
        else:
            h.pop("stale_days", None)

    for slug, shops in dropped:
        print(f"::warning::{slug}: {'・'.join(shops)} のリンクが切れています"
              "（そのボタンだけ外します。記事は公開のまま）")
    for slug, shops, n, need in warned:
        print(f"::warning::{slug}: 販売先がすべて落ちています"
              f"（{'・'.join(shops)}）。{n}/{need} 回目なので、"
              "様子を見て公開のままにします")
    for slug, shops in stopped:
        print(f"::warning::{slug}: 販売先がすべて切れています"
              f"（{'・'.join(shops)}）。公開を止めます")
    for slug, old in stale:
        print(f"::notice::{slug}: 最後の更新から {old} 日。内容の見直しどきです")

    print(f"\n所要 {dt:.1f} 秒 / 確認 {len(targets)} 本 / "
          f"リンクを外す {len(dropped)} 本 / 様子見 {len(warned)} 本 / "
          f"公開停止 {len(stopped)} 本 / "
          f"古い記事 {len(stale)} 本")

    if not args.apply:
        print("\n（--apply を付けると、上の内容を articles.json に反映します）")
        return 0

    with io.open(os.path.join(ROOT, "content", "articles.json"),
                 "w", encoding="utf-8") as f:
        json.dump(arts, f, ensure_ascii=False, indent=1)
    print("content/articles.json を更新しました。")

    if not args.push:
        return 0

    for cmd in (["python3", "build.py"],
                ["python3", "tools/check_articles.py"],
                ["python3", "tools/check_text.py"]):
        code, out = run(cmd)
        if code != 0:
            print(f"::error::{cmd[-1]} で止まりました\n{out}")
            return 1

    msg = (f"記事の見回り：リンク切れ {len(dropped)} 本・"
           f"公開停止 {len(stopped)} 本（自動）")
    for cmd in (["git", "add", "-A"], ["git", "commit", "-m", msg],
                ["git", "push"]):
        code, out = run(cmd)
        if code != 0 and "nothing to commit" not in out:
            print(f"::error::{' '.join(cmd)}\n{out}")
            return 1
    print("コミットして push しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
