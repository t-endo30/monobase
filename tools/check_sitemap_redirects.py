#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サイトマップに301転送元や重複URLを混ぜないための生成物検査。"""
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / "sitemap.xml"
WORKER = ROOT / "tools" / "worker.template.js"


def normalize(path: str) -> str:
    path = path.split("?", 1)[0].rstrip("/") or "/"
    return path[:-5] if path.endswith(".html") else path


def main() -> int:
    sitemap = SITEMAP.read_text(encoding="utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    normalized = [normalize(urlparse(url).path) for url in locs]
    errors = []
    if len(normalized) != len(set(normalized)):
        errors.append("sitemap.xml に重複URLがあります")

    worker = WORKER.read_text(encoding="utf-8")
    block = re.search(r"const ARTICLE_REDIRECTS = \{(.*?)\n\};", worker, re.S)
    redirect_sources = set()
    if block:
        for source in re.findall(r'"([^"\n]+)"\s*:', block.group(1)):
            redirect_sources.add(normalize(source))
    leaked = sorted(redirect_sources.intersection(normalized))
    if leaked:
        errors.append("301転送元がsitemap.xmlに含まれています: " + ", ".join(leaked))

    if errors:
        for error in errors:
            print(f"::error::{error}")
        return 1
    print(f"✅ sitemap redirect guard: {len(locs)} URLを検査、転送元・重複なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
