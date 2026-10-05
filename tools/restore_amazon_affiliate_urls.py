#!/usr/bin/env python3
"""商品同定用URLとは分離して、既存のAmazonアフィリエイト導線を復元する。"""
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "content", "articles.json")
HISTORICAL = {
    "rs-60e3-lcd-pdf": "003ffeea3b970d48bf234283c393a4414e015c69",
    "mvp3-3in1": "7b022d56a74515c5519a213080eca5210bdba1f1",
    "led-pv-bl2h-n": "28349f889",
    "cellularline-iphone18pro-iphone18promax": "71b2c725de5697c54ceeaf8ce462f9a663976f54",
}

with open(PATH, encoding="utf-8") as f:
    articles = json.load(f)

for slug, commit in HISTORICAL.items():
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{commit}:content/articles.json"], cwd=ROOT
        )
        old = next(a for a in json.loads(raw) if a.get("slug") == slug)
    except (subprocess.CalledProcessError, StopIteration, json.JSONDecodeError):
        continue
    for article in articles:
        if article.get("slug") == slug and old.get("amazon_url"):
            article["amazon_url"] = old["amazon_url"]
            article["updated"] = "2026-10-06"
            print(f"Amazon導線を復元しました: {slug}")

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=1)
