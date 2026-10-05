#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""既存の機械検査・公開判定を保ったGPTレビュー経路。"""
import argparse
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from article_evidence import stamp_evidence
from gpt_llm import GPTError, jev_judge, request_json
from gpt_schemas import REVIEW_SCHEMA
from review_article import (CATEGORY_MAP, PUBLISH_SCORE, apply_fixed,
                            build_prompt, content_rev, duplicate_of,
                            lacks_shop_photo, load, looks_unidentifiable,
                            save_article, scan)


def review_instructions(jev):
    extra = ""
    if jev.get("status") == "ok":
        extra = ("\nJevの補助判定も受け取りました。Jevの指摘は事実そのものではなく、"
                 "要確認候補として扱い、公式情報や記事中の根拠が無い主張を残さないでください。\n"
                 + str(jev))
    return """あなたは厳格な編集レビュー担当です。レビュー基準、機械検査結果、記事JSONを照合し、直すべき項目だけを fixed に返してください。架空の事実を補わず、根拠が弱い rating/spec は removed にしてください。score は修正後の実物に対して採点します。JSON Schemaに厳密に従うJSONだけを返してください。""" + extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--new", action="store_true", help="未公開記事を対象")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--model", default=None)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--jev", action="store_true", help="JEV_COMMANDがある場合だけ補助判定を使う")
    args = ap.parse_args()
    arts = load("content/articles.json")
    rules = io.open(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "docs", "review-rules.md"), encoding="utf-8").read()
    if args.all:
        targets = list(arts)
    elif args.new:
        targets = [a for a in arts if not a.get("published") and not a.get("unpublished_reason")]
    else:
        wanted = set(args.slugs)
        targets = [a for a in arts if a.get("slug") in wanted]
    if not targets:
        print("対象の記事がありません。--new、--all、または slug を指定してください。")
        return 0

    ok = ng = 0
    for i, a in enumerate(targets, 1):
        slug = a.get("slug", "?")
        print(f"[{i}/{len(targets)}] {slug}")
        hits = scan(a)
        for kind, path, detail in hits:
            print(f"  △ [{kind}] {path}: {detail}")
        jev = {"status": "not_requested"}
        if args.jev:
            jev = jev_judge({"task": "article_claim_risk", "slug": slug,
                             "article": {k: a.get(k) for k in ("title", "facts", "sections", "spec", "faq")}})
            print(f"  Jev: {jev.get('status')}" + (f" ({jev.get('reason')})" if jev.get('reason') else ""))
        score = {}
        blockers = []
        reviewed = False
        for round_no in range(1, args.rounds + 1):
            prompt = build_prompt(a, rules, hits, arts)
            if jev.get("status") == "ok":
                prompt += "\n\n================ Jev補助判定 ================\n" + str(jev)
            try:
                result = request_json(review_instructions(jev), prompt, REVIEW_SCHEMA,
                                      model=args.model, timeout=args.timeout,
                                      cwd=os.path.dirname(os.path.dirname(__file__)))
            except GPTError as exc:
                print(f"  ✗ レビュー失敗: {exc}")
                break
            reviewed = True
            for finding in result.get("findings") or []:
                print(f"  ● {finding.get('where')}: {finding.get('problem')} ({finding.get('rule')})")
            score = result.get("score") or {}
            blockers = result.get("blockers") or []
            if result.get("discard") or looks_unidentifiable(a) or lacks_shop_photo(a):
                blockers.append(result.get("discard") or "機械検査で製品を一意に確認できません")
                break
            newcat = (result.get("category") or "").strip()
            if newcat in CATEGORY_MAP and newcat != a.get("category"):
                a["category"] = newcat
            fixed = {k: v for k, v in (result.get("fixed") or {}).items() if v is not None}
            changed = apply_fixed(a, fixed, removed=result.get("removed"))
            if not changed:
                break
            hits = scan(a)
        hits = scan(a)
        total = score.get("total")
        passed = reviewed and not hits and not blockers and isinstance(total, (int, float)) and total >= PUBLISH_SCORE
        if args.publish:
            evidence_blockers = stamp_evidence(a)
            blockers.extend(evidence_blockers)
            passed = passed and not evidence_blockers
        if passed:
            ok += 1
            a["reviewed"] = {"at": time.strftime("%Y-%m-%d"), "rev": content_rev(a), "score": score}
            if args.publish and not args.dry_run:
                a["published"] = True
                print("  ✓ 合格・published: true")
            else:
                print("  ✓ 合格（公開は保留）")
        else:
            ng += 1
            print(f"  ✗ 要確認（レビュー実行={reviewed}, total={total}）")
            for b in blockers:
                print(f"    - {b}")
            if args.publish and not args.dry_run:
                a["published"] = False
                a["unpublished_reason"] = "GPTレビュー不合格：根拠・独自性・安全性の再確認が必要"
                print("  → published: false（レビュー不合格）")
        if not args.dry_run:
            save_article(a)
    print(f"合格 {ok} 本 / 要確認 {ng} 本")
    return 1 if ng else 0


if __name__ == "__main__":
    raise SystemExit(main())
