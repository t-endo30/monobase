#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPT記事経路を生成→レビューの順で実行する安全な入口。"""
import argparse
import csv
import json
import os
import subprocess
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER_PAGE_SIZE = 10


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


def all_slugs():
    with open(os.path.join(ROOT, "content", "articles.json"), encoding="utf-8") as f:
        return {a.get("slug") for a in json.load(f) if a.get("slug")}


def published_slugs():
    with open(os.path.join(ROOT, "content", "articles.json"), encoding="utf-8") as f:
        articles = json.load(f)
    return {a.get("slug") for a in articles if a.get("published") and a.get("slug")}


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


def order_history_rows():
    """購入履歴探索の上限を、固定値ではなく候補プールの行数から決める。

    候補経路は、先頭ページの商品が画像・個別URL・レビュー条件で落ちても
    別の商品へ進める必要がある。ここでは再分類済み候補だけを有限走査する。
    """
    path = os.path.join(ROOT, "AmazonExport", "candidates.csv")
    try:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            return sum(1 for row in csv.DictReader(handle)
                       if str(row.get("ASIN") or "").strip()
                       and str(row.get("Product Name") or "").strip()
                       and str(row.get("category") or "").strip())
    except (OSError, csv.Error):
        # 候補CSVを読めない場合でも、有限値で処理を止める。
        return 1200


def order_history_only():
    try:
        with open(os.path.join(ROOT, "content", "site.json"), encoding="utf-8") as f:
            return bool((json.load(f).get("automation") or {}).get(
                "order_history_only", False))
    except (OSError, ValueError, TypeError):
        return False


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
                         "asin": article.get("asin"),
                         "source_name": article.get("source_name"),
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
    ap.add_argument("--refresh-order-products", action="store_true",
                    help="購入履歴ASINを優先して候補を再収集する")
    ap.add_argument("--order-offset", type=int, default=0,
                    help="購入履歴候補の探索開始位置")
    ap.add_argument("--orders-first", action="store_true",
                    help="1日5本のうち先に購入履歴由来を3本確保し、残りを通常候補で作る")
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
    if args.refresh_order_products or args.orders_first:
        args.select = True
    if args.orders_first and not args.dry_run:
        # 当面は再分類済み購入履歴プールだけを母集団にする。設定が解除された
        # 場合だけ、従来どおり購入履歴3本→通常候補へ切り替える。
        pool_only = order_history_only()
        order_target = args.take if pool_only else min(3, args.take)
        order_cmd = [sys.executable, __file__, "--select", "--refresh-order-products",
                     "--take", str(order_target), "--batch-size", str(args.batch_size),
                     "--model", args.model, "--review-model", args.review_model,
                     "--timeout", str(args.timeout)]
        if args.order_offset:
            order_cmd += ["--order-offset", str(args.order_offset)]
        if args.publish:
            order_cmd.append("--publish")
        if args.jev:
            order_cmd.append("--jev")
        published_before = published_slugs()
        order_code = subprocess.run(order_cmd, cwd=ROOT, check=False).returncode
        order_published = len(published_slugs() - published_before)
        remaining = max(0, args.take - order_published)
        if remaining == 0:
            print(f"目標達成: {args.take} 本（購入履歴由来 {order_published} 本）")
            return 0
        if pool_only:
            print(f"購入履歴候補プールのみで {order_published}/{args.take} 本。"
                  "通常候補へは切り替えず、次回枠へ繰り越します。")
            return 1
        if order_code:
            print(f"購入履歴由来は {order_published}/3 本。残り {remaining} 本を通常候補へ切り替えます。")
        normal_cmd = [sys.executable, __file__, "--select", "--refresh-products",
                      "--take", str(remaining), "--batch-size", str(args.batch_size),
                      "--model", args.model, "--review-model", args.review_model,
                      "--timeout", str(args.timeout)]
        if args.publish:
            normal_cmd.append("--publish")
        if args.jev:
            normal_cmd.append("--jev")
        return subprocess.run(normal_cmd, cwd=ROOT, check=False).returncode
    if args.select:
        target_count = max(1, args.take)
        batch_size = max(1, min(args.batch_size, target_count))
        succeeded = set()
        tried = 0
        refresh = args.refresh_products
        order_refresh = args.refresh_order_products
        order_offset = max(0, args.order_offset)
        # 購入履歴は1ページで決め打ちせず、候補不成立なら別ページへ進む。
        # 1ページ30件を元CSVの行数ぶんだけ探索してから候補枯渇と判断する。
        # CSV全体を上限にする有限走査なので、無限再試行にはならない。
        if order_refresh:
            order_page_size = ORDER_PAGE_SIZE
            max_order_pages = max(1, (order_history_rows() + order_page_size - 1)
                                  // order_page_size)
            max_batches = max(5, max_order_pages)
        else:
            max_batches = max(5, (target_count * 10 + batch_size - 1) // batch_size)
        for batch_no in range(max_batches):
            remaining = target_count - len(succeeded)
            if remaining <= 0:
                break
            batch = min(batch_size, remaining)
            before = slugs_with_content()
            before_all = all_slugs()
            selection = [sys.executable, "tools/gpt_select_products.py", "--take", str(batch)]
            if order_refresh:
                selection.append("--refresh-orders")
                selection += ["--order-offset", str(order_offset)]
                # 1ページ分ずつ先へ進める。前ページがレビュー不合格でも、
                # 同じ候補を再取得せず、次の購入履歴商品を照合する。
                order_offset += order_page_size
            elif refresh:
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
            after_all = all_slugs()
            new_slugs = (after - before) if not args.dry_run else set()
            blank_new = ((after_all - before_all) - new_slugs
                         if not args.dry_run else set())
            if blank_new:
                remove_failed_new(blank_new)
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
