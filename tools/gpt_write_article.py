#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPT経路で記事本文を生成する。Claude Codeには依存しない。"""
import argparse
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gpt_llm import GPTError, jev_judge, request_json
from gpt_schemas import ARTICLE_SCHEMA
from write_article import (ARTICLES, INDEX_MIN_REVIEWS, MIN_CHARS, ROOT,
                           apply_generated, audit, body_chars, build_prompt,
                           delete_article, is_empty, kind_of, load,
                           report_self_check, review_count, save_article,
                           section_chars)


INSTRUCTIONS = """あなたはモノベースの編集部員です。与えられた事実・公式情報・口コミだけで、購入判断に役立つ日本語記事を作成してください。
事実にない仕様、体験、口コミ、価格、効果を補わないでください。曖昧な情報は data_gaps に記録し、rating と spec は根拠がある場合だけ値を入れてください。
記事全体の表現ルール：本文に出る商品名・型番には、Amazon→楽天→Yahoo!の優先順でテキストリンクを設定できるようにしてください。特集・選び方記事は個別商品名をタイトルに入れず、カテゴリ名・用途名で表現してください。特集では紹介する全商品を掲載元記事と対応づけ、各商品に実物画像付きの購入リンクを表示する前提です。特集のサムネイルはカテゴリ画像を使う前提です。
公式資料リンクは記事内に必ず残し、公式OGP画像が提供されている場合はリンクカードで表示できるよう official_ogp_image と official_ogp_title を保持してください。読者に責任を押し付けるような「このサイトでは判断できない」「正確に判断できない」「個別の例で評価全体の傾向を示さない」といった編集部の弱気な定型句は使わず、確認できた事実と購入前に確認する具体的な項目へ書き換えてください。利用者の声は出典を示して「利用者の声」と表現します。
サムネイルは、(1)商品を特定できるメーカー公式画像、(2)取得時にHTTP応答とContent-Typeを確認した楽天・Yahoo!画像、の順で選びます。公式OGPやロゴを商品画像として扱わないでください。両方とも用意できない個別商品記事は公開候補にせず、特集記事だけカテゴリ画像を許可します。出力は指定されたJSON Schemaに厳密に従うJSONオブジェクトだけにしてください。"""


def jev_context(article):
    """生成前にJevで主張リスクを確認し、結果を本文生成へ渡す。"""
    result = jev_judge({
        "task": "article_claim_risk_before_generation",
        "slug": article.get("slug"),
        "article": {k: article.get(k) for k in
                     ("title", "official_url", "rakuten_url", "yahoo_url",
                      "facts", "voices", "review_stats", "source_notes")},
    })
    if result.get("status") != "ok":
        return "Jevは利用できなかったため、提供された根拠だけで生成してください。"
    return ("生成前Jev補助判定（事実そのものではなく、要確認候補として扱う）:\n"
            + str(result))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--drafts", action="store_true", help="本文が空の未公開下書き")
    ap.add_argument("--model", default="gpt-5.6-luna")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--keep-updated", action="store_true")
    args = ap.parse_args()

    arts = load(ARTICLES)
    site = load("content/site.json")
    prompt_md = io.open(os.path.join(ROOT, "docs", "article-prompt.md"), encoding="utf-8").read()
    if args.drafts:
        targets = [a for a in arts if not a.get("published") and is_empty(a)]
    else:
        wanted = set(args.slugs)
        targets = [a for a in arts if a.get("slug") in wanted]
    if not targets:
        print("対象の記事がありません。--drafts または slug を指定してください。")
        return 0

    print(f"{len(targets)} 本をGPT経路で生成します")
    failed = 0
    for i, original in enumerate(targets, 1):
        slug = original.get("slug", "?")
        print(f"[{i}/{len(targets)}] {slug}")
        fresh = next((x for x in load(ARTICLES) if x.get("slug") == slug), None)
        a = fresh or original
        count = review_count(a)
        if kind_of(a) == "review" and not a.get("spec") and count is not None and count < INDEX_MIN_REVIEWS and not (a.get("source_notes") and a.get("review_texts")):
            print(f"  - 口コミ {count} 件のため対象外")
            continue
        prompt = build_prompt(a, site, prompt_md, fetch_official=not args.no_fetch)
        prompt += "\n\n================ 生成前Jev確認 ================\n" + jev_context(a)
        try:
            gen = request_json(INSTRUCTIONS, prompt, ARTICLE_SCHEMA,
                               model=args.model, timeout=args.timeout, cwd=ROOT)
        except GPTError as exc:
            print(f"  ✗ 生成失敗: {exc}")
            failed += 1
            continue
        if kind_of(a) == "review" and section_chars(gen) < 1300:
            print(f"  ✗ sections が {section_chars(gen)} 字。公開候補にしません")
            failed += 1
            continue
        candidate = dict(a)
        apply_generated(candidate, gen, keep_updated=args.keep_updated)
        warns = audit(candidate)
        for warning in warns:
            print(f"  △ {warning}")
        report_self_check(gen)
        print(f"  ✓ JSON受領（本文 {body_chars(gen):,} 字）。レビュー待ち")
        if not args.dry_run:
            save_article(candidate)
    print(f"完了：失敗 {failed} 本。生成後は tools/gpt_review_article.py を必ず実行してください。")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
