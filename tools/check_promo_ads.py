#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ホーム・記事下に出しているPRタイル（content/site.json の promos）の
バナー画像がまだ生きているかを確かめ、死んでいるものを取り除く。

広告主がキャンペーンを終えると、コードは残ったままバナー画像だけが
404になる（クリック先ではなく画像を見るのは、クリックリンクを踏むと
ASP側にクリックとして記録されてしまい、実際のクリック率の集計を
汚してしまうため）。1×1の計測用画像はどのASPでも常に生きているので、
判定には使わず、幅・高さが1でないバナー本体の画像だけを見る。

  $ python3 tools/check_promo_ads.py                 # 見るだけ（既定）
  $ python3 tools/check_promo_ads.py --apply         # 死んだものを site.json から外す
  $ python3 tools/check_promo_ads.py --apply --push  # 外してビルド・コミット・push

tools/maintain_articles.py と同じ考え方で、1回の失敗では外さない
（ASP側の一時的な詰まりで生きているものを消さないため）。
--strikes 回、続けて死んでいたときだけ外す。
"""
import argparse, hashlib, io, json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_links import fetch, LIVE, WORKERS      # 疎通の判定は1か所にまとめる

SITE_JSON = os.path.join(ROOT, "content", "site.json")

IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
SRC = re.compile(r'src="([^"]+)"', re.I)
PIXEL = re.compile(r'(?:width|height)="1"', re.I)


def ad_id(ad):
    """ads には固有IDが無いので、コードのハッシュを身代わりの鍵にする。"""
    return hashlib.sha1((ad.get("html") or "").encode("utf-8")).hexdigest()[:12]


def creative_urls(html_):
    """バナー本体の画像URLだけを拾う（1×1の計測用画像は除く）。
       全部が計測用画像しか無ければ、それしか無いので仕方なく使う。"""
    main, pixel = [], []
    for tag in IMG_TAG.findall(html_ or ""):
        m = SRC.search(tag)
        if not m:
            continue
        url = m.group(1)
        if url.startswith("//"):
            url = "https:" + url
        (pixel if PIXEL.search(tag) else main).append(url)
    return main or pixel


def check_one(job):
    key, url = job
    code, note = fetch(url)
    return (key, url, code, code in LIVE)


def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strikes", type=int, default=2,
                    help="続けてこの回数死んでいたときだけ外す（既定2）")
    ap.add_argument("--apply", action="store_true",
                    help="見つけた問題を site.json に反映する")
    ap.add_argument("--push", action="store_true",
                    help="反映したうえでビルドし、コミットして push する")
    args = ap.parse_args()

    site = json.load(io.open(SITE_JSON, encoding="utf-8"))
    items = site.get("promos", {}).get("items") or []

    jobs, by_key = [], {}
    for item in items:
        for ad in item.get("ads") or []:
            k = ad_id(ad)
            by_key[k] = ad
            urls = creative_urls(ad.get("html"))
            for u in urls:
                jobs.append((k, u))

    if not jobs:
        print("確認するPRタイルがありません。")
        return 0

    print(f"PRタイルのバナー画像 {len(jobs)} 本を確認します"
          f"（広告 {len(by_key)} 件・同時 {WORKERS} 本）")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        results = list(ex.map(check_one, jobs))
    dt = time.time() - t0

    # 広告1件が複数枚の画像を持つことは無いが、念のため
    # 「その広告の画像が1枚でも死んでいれば死んだ扱い」にする。
    dead_keys = {k for k, url, code, ok in results if not ok}

    today = date.today().isoformat()
    dropped_ads, dropped_items = [], []

    for item in items[:]:
        ads = item.get("ads") or []
        keep = []
        for ad in ads:
            k = ad_id(ad)
            h = ad.setdefault("health", {})
            h["checked"] = today
            if k in dead_keys:
                n = int(h.get("dead_strikes") or 0) + 1
                if args.apply:
                    h["dead_strikes"] = n
                if n >= args.strikes:
                    title = ad.get("title") or item.get("name") or k
                    dropped_ads.append(title)
                    continue    # 外す（keepに入れない）
            else:
                h.pop("dead_strikes", None)
                h.pop("dead", None)
            keep.append(ad)
        if args.apply:
            item["ads"] = keep
        if not keep:
            dropped_items.append(item.get("name") or "?")
            if args.apply:
                items.remove(item)

    for title in dropped_ads:
        print(f"::warning::PRタイルのバナー画像が開けません：{title}")
    for name in dropped_items:
        print(f"::notice::枠が空になったので削除します：{name}")

    print(f"\n所要 {dt:.1f} 秒 / 広告 {len(by_key)} 件 / "
          f"死亡候補 {len(dead_keys)} 件 / 実際に外す {len(dropped_ads)} 件 / "
          f"空になった枠 {len(dropped_items)} 件")

    if not args.apply:
        if dropped_ads:
            print("\n（--apply を付けると、上の内容を site.json から取り除きます）")
        else:
            print("✅ すべてのPRタイルのバナー画像が生きています。")
        return 0

    with io.open(SITE_JSON, "w", encoding="utf-8") as f:
        json.dump(site, f, ensure_ascii=False, indent=1)
    print("content/site.json を更新しました。")

    if not args.push:
        return 0

    if not dropped_ads and not dropped_items:
        print("変わったものが無いので push しません。")
        return 0

    for cmd in (["python3", "build.py"],):
        code, out = run(cmd)
        if code != 0:
            print(f"::error::{cmd[-1]} で止まりました\n{out}")
            return 1

    msg = f"リンク切れのPRタイルを削除（{len(dropped_ads)}件・自動）"
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
