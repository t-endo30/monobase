#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事を公開するための最低限の一次情報・商品同定チェック。"""
import re
import datetime as dt
from urllib.parse import urlparse

def _url(value):
    return str(value or "").strip()

def is_individual_product_url(value):
    url = _url(value)
    if not re.match(r"^https?://", url):
        return False
    low = url.lower()
    if any(x in low for x in ("/s?", "/s/", "search", "keyword=", "query=")):
        return False
    host = urlparse(url).netloc.lower()
    if "amazon." in host:
        return bool(re.search(r"/(?:dp|gp/product)/[A-Z0-9]{8,}", url, re.I))
    if "rakuten.co.jp" in host:
        return bool(re.search(r"item\.rakuten\.co\.jp/[^/]+/[^/?#]+", url, re.I))
    if "yahoo.co.jp" in host:
        return bool(re.search(r"shopping\.yahoo\.co\.jp/[^/]+/[^/?#]+", url, re.I))
    return True

def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)

def review_text_present(article):
    """レビュー本文を保持しているか。件数・平均点だけでは真にしない。"""
    voices = article.get("voices")
    if isinstance(voices, list) and any(len("".join(_strings(v))) >= 30 for v in voices):
        return True
    text = "\n".join(_strings(article.get("review_texts")))
    return bool(len(text) >= 60 and not re.search(r"口コミ本文は(?:取得|未取得)していない", text))

def assessment(article):
    official = _url(article.get("official_url"))
    facts = article.get("facts") or []
    if isinstance(facts, str):
        facts = [facts]
    has_official = bool(official) and bool(re.match(r"^https?://", official))
    has_official_evidence = has_official or bool(facts)
    shop_urls = {key: _url(article.get(key)) for key in
                 ("amazon_url", "rakuten_url", "yahoo_url") if _url(article.get(key))}
    individual_urls = {key: value for key, value in shop_urls.items()
                       if is_individual_product_url(value)}
    has_identity = bool(_url(article.get("asin")) or _url(article.get("jan")))
    title = str(article.get("title") or "").split("｜", 1)[0]
    has_identity = has_identity or bool(re.search(r"[A-Za-z0-9][A-Za-z0-9._-]{2,}", title))
    has_reviews = review_text_present(article)
    missing = []
    if not has_official_evidence:
        missing.append("公式資料またはfacts")
    if not individual_urls:
        missing.append("個別商品URL")
    if not has_identity:
        missing.append("商品同定情報（型番・ASIN・JAN等）")
    if not has_reviews:
        missing.append("レビュー本文")
    if not has_identity or not individual_urls:
        category = "公開停止候補"
    elif not has_official_evidence or not has_reviews:
        category = "追加調査"
    else:
        category = "修正可能"
    return {"category": category, "has_official_evidence": has_official_evidence,
            "official_url": official, "has_individual_product_url": bool(individual_urls),
            "individual_product_urls": individual_urls, "has_product_identity": has_identity,
            "has_review_text": has_reviews, "review_stats_present": bool(article.get("review_stats")),
            "missing": missing}

def publish_blockers(article):
    result = assessment(article)
    blockers = []
    if not result["has_official_evidence"]:
        blockers.append("公式資料またはfactsがありません")
    if not result["has_individual_product_url"]:
        blockers.append("個別商品URLがありません（検索結果URLは不可）")
    if not result["has_product_identity"]:
        blockers.append("商品を一意に同定できません")
    # review_stats がある記事は、レビューを扱う記事として生成されている。
    # 件数・平均点だけを根拠に「利用者の声」を説明しないよう、本文が無ければ止める。
    if result["review_stats_present"] and not result["has_review_text"]:
        blockers.append("レビュー統計はありますが、レビュー本文がありません")
    return blockers

def stamp_evidence(article):
    """今回確認した証拠状態を記事JSONに残す。本文の正しさを保証する印ではない。"""
    result = assessment(article)
    blockers = publish_blockers(article)
    article["evidence_audit"] = {
        "checked_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "pass" if not blockers else "blocked",
        "official_url": result["official_url"],
        "has_official_evidence": result["has_official_evidence"],
        "individual_product_urls": result["individual_product_urls"],
        "has_product_identity": result["has_product_identity"],
        "has_review_text": result["has_review_text"],
        "review_stats_present": result["review_stats_present"],
        "missing": result["missing"],
        "blockers": blockers,
    }
    return blockers
