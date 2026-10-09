#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPT経路で使うStrict Structured Outputsのスキーマ。"""


def s(nullable=False):
    return {"anyOf": [{"type": "string"}, {"type": "null"}]} if nullable else {"type": "string"}


def arr(item=None, nullable=False):
    value = {"type": "array", "items": item or {"type": "string"}}
    return {"anyOf": [value, {"type": "null"}]} if nullable else value


def obj(properties, nullable=False):
    value = {"type": "object", "properties": properties,
             "required": list(properties), "additionalProperties": False}
    return {"anyOf": [value, {"type": "null"}]} if nullable else value


PAIR = obj({"title": s(), "text": s()})
SECTION = obj({"heading": s(), "paras": arr(), "point": s(), "warn": s(),
               "aside": s(), "aside_label": s()})
VOICE = obj({"heading": s(), "who": s(), "text": s(), "negative": {"type": "boolean"},
             "fix_title": s(), "fix": s()})

ARTICLE_FIELDS = {
    "lead": arr(), "verdict_title": s(), "summary": arr(PAIR),
    "rating": obj({"score": {"type": "number"}, "breakdown": s()}, True),
    "good_for": obj({"intro": s(), "items": arr(PAIR)}, True),
    "highlights": obj({"intro": s(), "items": arr(PAIR)}, True),
    "not_for": obj({"intro": s(), "items": arr(PAIR)}, True),
    "scenes": arr(PAIR, True), "pros": arr(), "cons": arr(),
    "spec": obj({"intro": s(), "headers": arr(), "rows": arr(arr()), "read": s()}, True),
    "sections": arr(SECTION),
    "toc_items": arr(obj({"id": s(), "label": s()}), True),
    "voices_intro": s(), "voices": arr(VOICE, True),
    "voices_after": s(), "personal_note": s(),
    "next_problem": obj({"intro": s(), "items": arr(PAIR)}, True),
    "faq": arr(obj({"q": s(), "a": s()})), "conclusion_title": s(),
    "conclusion": arr(), "description": s(), "excerpt": s(), "list_title": s(),
    "title": s(), "tags": arr(), "sub": s(), "data_gaps": arr(),
    "self_check": obj({k: ({"type": "number"} if k != "notes" else s())
                         for k in ("fact_accuracy", "source_reliability", "original_analysis",
                                   "editorial_quality", "template_avoidance",
                                   "purchase_helpfulness", "legal_safety",
                                   "amazon_compliance", "total", "notes")})
}

ARTICLE_SCHEMA = {"name": "monobase_article", "schema": obj(ARTICLE_FIELDS)}

FIXED_FIELDS = {k: {"anyOf": [v, {"type": "null"}]} for k, v in ARTICLE_FIELDS.items()}
REVIEW_SCHEMA = {"name": "monobase_article_review", "schema": obj({
    "findings": arr(obj({"where": s(), "rule": s(), "problem": s()})),
    "fixed": obj(FIXED_FIELDS), "removed": arr(),
    "score": obj({k: {"type": "number"} for k in (
        "fact_accuracy", "source_reliability", "original_analysis", "editorial_quality",
        "template_avoidance", "purchase_helpfulness", "legal_safety", "amazon_compliance",
        "total") } | {"notes": s()}),
    "blockers": arr(), "discard": s(), "category": s(),
})}
