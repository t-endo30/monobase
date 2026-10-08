#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPT記事経路を生成→レビューの順で実行する安全な入口。"""
import argparse
import json
import os
import subprocess
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def slugs_with_content():
    with open(os.path.join(ROOT, "content", "articles.json"), encoding="utf-8") as f:
        articles = json.load(f)
    # 候補選定直後にも title/summary の空キーが存在するため、
    # 「キーがある」ではなく本文として実体のあるフィールドだけを判定する。
    body_fields = ("sections", "lead", "summary", "conclusion", "personal_note")
    return {
        a.get("slug") for a in articles
        if any(a.get(field) for field in body_fields)
    }


def reviewed_successes(slugs):
    with open(os.path.join(ROOT, "content", "articles.json"), encoding="utf-8") as f:
        articles = json.load(f)
    result = set()
    for article in articles:
        if article.get("slug") not in slugs:
            continue
        score = (article.get("reviewed") or {}).get("score") or {}
        if (article.get("published") and
                isinstance(score.get("total"), (int, float)) and
                score["total"] >= 85):
            result.add(article.get("slug"))
    return result


def remove_failed_new(slugs):
    """今回作ったが本文生成・レビューに失敗した下書きを次候補の邪魔にしない。"""
    if not slugs:
        return
    path = os.path.join(ROOT, "content", "articles.json")
    with open(path, encoding="utf-8") as f:
        articles = json.load(f)
    failed = [a for a in articles if a.get("slug") in slugs]
    if not failed:
        return
    remaining = [a for a in articles if a.get("slug") not in slugs]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(remaining, f, ensure_ascii=False, indent=1)
    rejected_path = os.path.join(ROOT, "content", "candidates.rejected.json")
    try:
        with open(rejected_path, encoding="utf-8") as f:
            rejected = json.load(f)
    except (OSError, ValueError):
        rejected = []
    for article in failed:
        rejected.append({"title": article.get("title"), "jan": article.get("jan"),
                         "urls": [article.get(k) for k in ("rakuten_url", "yahoo_url")
                                  if article.get(k)],
                         "reason": "GPT経路で目標品質に達しなかったため次候補へ切替"})
    with open(rejected_path, "w", encoding="utf-8") as f:
        json.dump(rejected[-500:], f, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drafts", action="store_true", help="空の下書きを生成")
    ap.add_argument("--select", action="store_true", help="商品候補を選定して新規記事を作る")
    ap.add_argument("--refresh-products", action="store_true", help="候補をAPIから再収集してから選ぶ")
    ap.add_argument("--take", type=int, default=5, help="その日の目標記事数")
    ap.add_argument("--batch-size", type=int, default=2, help="1回に処理する候補数")
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--model", default="gpt-5.6-luna",
                    help="記事生成モデル（既定: gpt-5.6-luna）")
    ap.add_argument("--review-model", default="gpt-5.6-luna",
                    help="レビュー用モデル（既定: gpt-5.6-luna）")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--publish", action="store_true", help="レビュー合格記事だけ公開")
    ap.add_argument("--jev", action="store_true")
    args = ap.parse_args()
    if args.drafts and args.slugs:
        ap.error("--drafts と slug は同時に指定しません")
    if args.refresh_products:
        args.select = True
    if args.select:
        target_count = max(1, args.take)
        batch_size = max(1, min(args.batch_size, target_count))
        succeeded = set()
        tried = 0
        refresh = args.refresh_products
        max_batches = max(1, (target_count * 3 + batch_size - 1) // batch_size)
        for batch_no in range(max_batches):
            remaining = target_count - len(succeeded)
            if remaining <= 0:
                break
            batch = min(batch_size, remaining)
            before = slugs_with_content()
            selection = [sys.executable, "tools/gpt_select_products.py", "--take", str(batch)]
            if refresh:
                selection.append("--refresh")
            selected = subprocess.run(selection, cwd=ROOT, check=False)
            refresh = False
            if selected.returncode != 0:
                print("候補選定に失敗したため、次回の実行枠へ繰り越します。")
                break
            args.drafts = True
            target = [sys.executable, "tools/gpt_write_article.py", "--drafts",
                      "--timeout", str(args.timeout)]
            if args.model:
                target += ["--model", args.model]
            if args.dry_run:
                target.append("--dry-run")
            generated = subprocess.run(target, cwd=ROOT, check=False)
            after = slugs_with_content()
            new_slugs = (after - before) if not args.dry_run else set()
            tried += len(new_slugs)
            if args.dry_run:
                continue
            if not new_slugs:
                print("本文を作成できる候補がありません。次候補を探します。")
                continue
            review = [sys.executable, "tools/gpt_review_article.py", *sorted(new_slugs),
                      "--timeout", str(args.timeout)]
            if args.review_model:
                review += ["--model", args.review_model]
            if args.publish:
                review.append("--publish")
            if args.jev:
                review.append("--jev")
            subprocess.run(review, cwd=ROOT, check=False)
            passed = reviewed_successes(new_slugs)
            succeeded |= passed
            remove_failed_new(new_slugs - passed)
            print(f"GPT経路: {len(succeeded)}/{target_count} 本を確保、"
                  f"今回試行 {tried} 本")
        if len(succeeded) < target_count:
            print(f"目標未達: {len(succeeded)}/{target_count} 本。"
                  "候補・認証・利用上限を確認し、次回枠で続行します。")
            return 1
        print(f"目標達成: {target_count} 本")
        return 0
    target = [sys.executable, "tools/gpt_write_article.py"]
    target += ["--drafts"] if args.drafts or not args.slugs else args.slugs
    if args.model:
        target += ["--model", args.model]
    target += ["--timeout", str(args.timeout)]
    if args.dry_run:
        target += ["--dry-run"]
    generated = subprocess.run(target, cwd=ROOT, check=False)
    if generated.returncode != 0:
        return generated.returncode

    review = [sys.executable, "tools/gpt_review_article.py"]
    review += ["--new"] if args.drafts or not args.slugs else args.slugs
    if args.review_model:
        review += ["--model", args.review_model]
    review += ["--timeout", str(args.timeout)]
    if args.dry_run:
        review += ["--dry-run"]
    if args.publish:
        review += ["--publish"]
    if args.jev:
        review += ["--jev"]
    return subprocess.run(review, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
