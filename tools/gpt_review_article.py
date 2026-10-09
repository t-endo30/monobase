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
                            has_publishable_thumbnail, lacks_shop_photo, load,
                            looks_unidentifiable,
                            save_article, scan)


def review_instructions(jev):
    extra = ""
    if jev.get("status") == "ok":
        extra = ("\nJevの補助判定も受け取りました。Jevの指摘は事実そのものではなく、"
                 "要確認候補として扱い、公式情報や記事中の根拠が無い主張を残さないでください。\n"
                 + str(jev))
    return """あなたは厳格な編集レビュー担当です。レビュー基準、機械検査結果、記事JSONを照合し、直すべき項目だけを fixed に返してください。架空の事実を補わず、根拠が弱い rating/spec は removed にしてください。score は修正後の実物に対して採点します。
追加ルール：特集・選び方記事のタイトルと一覧名に個別商品名・型番を入れず、カテゴリ名・用途名に直してください。特集のサムネイルはカテゴリ画像を使う前提です。根拠ブロックの thumbnail_policy が category_image の場合はサムネイル不足として扱わないでください。個別商品記事でサムネイルが無い場合は公開不可にしてください。特集の商品紹介は商品ごとに画像付きリンクと説明を交互に配置し、画像カードの一覧だけにしないでください。特集は記事JSONへHTMLを直書きする設計ではなく、feature_coversの各掲載元に個別商品URLとthumbnail_urlまたはshop_imagesがある場合、ビルド時にその商品を最初に説明する段落の直前へ画像付きリンクを自動挿入します。この生成経路が成立している場合、JSON内にHTMLカードが見えないことだけを理由に不合格にしないでください。feature_sourcesの全商品について画像URL・個別商品URL・本文中の商品説明位置が揃っているかを確認してください。特集の目次は固定テンプレート扱いにせず、本文の比較軸・用途・確認項目に合わせた toc_items を記事ごとに作成してください。toc_items の id は実際の sections（sec-note1 など）・FAQ（sec-faq）・まとめ（sec-conclusion）に対応させ、label は記事固有の短い見出しにしてください。特集テーマと商品カテゴリ・用途が一致しない商品（例：カメラ特集のスマートフォン専用レンズカバー）は削除または別テーマへ差し替えてください。本文の商品名リンクはAmazon→楽天→Yahoo!の順で、Amazon導線が存在する場合はAmazonを優先してください。公式資料リンクは削除せず、公式OGP画像が根拠データにある場合は表示用フィールドを残してください。「このサイトでは判断できない」「正確に判断できない」「個別の例で評価全体の傾向を示さない」などの弱気なメタ表現は、確認できた事実と購入前の具体的な確認項目へ書き換えてください。「口コミ」は出典が曖昧な本文では「利用者の声」に統一してください。
個別商品記事のタイトルは「利用者の声」を機械的な共通接尾辞にせず、本文の中心である仕様・用途・比較軸・設置条件・選び方など商品固有の判断軸を前面に出してください。JSON Schemaに厳密に従うJSONだけを返してください。""" + extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--new", action="store_true", help="未公開記事を対象")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--model", default="gpt-5.6-luna")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--jev", action="store_true", help="Jevの補助判定を使う（ローカルブリッジを優先）")
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
        # GPT呼び出し・Jev判定より前に、公開済み記事との型番重複を除外する。
        # 重複記事は根拠や文章を直しても公開対象にならないため、候補を
        # 早く次へ回し、レビュー枠とAPI利用を消費しない。
        dup = duplicate_of(a, arts)
        if dup:
            ng += 1
            reason = (f"既存公開記事と型番が重複するため公開対象外（重複先: {dup}）")
            a["published"] = False
            a["unpublished_reason"] = reason
            print(f"  → GPTレビュー前に除外: {reason}")
            if not args.dry_run:
                save_article(a)
            continue
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
            thumbnail_blocker = False
            if a.get("category") != "feature" and not has_publishable_thumbnail(a):
                blockers.append("個別商品画像の取得・確認が済んでいないため公開不可")
                thumbnail_blocker = True
            passed = passed and not evidence_blockers and not thumbnail_blocker
        if passed:
            ok += 1
            a["reviewed"] = {"at": time.strftime("%Y-%m-%d"), "rev": content_rev(a), "score": score}
            if args.publish and not args.dry_run:
                a["published"] = True
                a.pop("unpublished_reason", None)
                print("  ✓ 合格・published: true")
            else:
                print("  ✓ 合格（公開は保留）")
        else:
            ng += 1
            print(f"  ✗ 要確認（レビュー実行={reviewed}, total={total}）")
            for b in blockers:
                print(f"    - {b}")
            if args.publish and not args.dry_run and reviewed:
                a["published"] = False
                a["unpublished_reason"] = "GPTレビュー不合格：根拠・独自性・安全性の再確認が必要"
                print("  → published: false（レビュー不合格）")
        if not args.dry_run:
            save_article(a)
    print(f"合格 {ok} 本 / 要確認 {ng} 本")
    return 1 if ng else 0


if __name__ == "__main__":
    raise SystemExit(main())
