#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPT記事経路を生成→レビューの順で実行する安全な入口。"""
import argparse
import os
import subprocess
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drafts", action="store_true", help="空の下書きを生成")
    ap.add_argument("--select", action="store_true", help="既存経路と同じ選定ロジックで商品を選ぶ")
    ap.add_argument("--refresh-products", action="store_true", help="候補をAPIから再収集してから選ぶ")
    ap.add_argument("--take", type=int, default=2)
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--model", default=None)
    ap.add_argument("--review-model", default=None)
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
        selection = [sys.executable, "tools/gpt_select_products.py", "--take", str(args.take)]
        if args.refresh_products:
            selection.append("--refresh")
        selected = subprocess.run(selection, cwd=ROOT, check=False)
        if selected.returncode != 0:
            return selected.returncode
        args.drafts = True
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
