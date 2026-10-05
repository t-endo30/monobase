#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPT経路用の商品選定入口。

候補の取得・重複排除・製品特定はClaude経路と同じ機械ロジックを使い、
選定後の本文だけをGPTへ渡す。モデルに商品を自由選択させない。
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(args):
    return subprocess.run([sys.executable, *args], cwd=ROOT, check=False).returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--take", type=int, default=2)
    ap.add_argument("--refresh", action="store_true", help="楽天・Yahoo!から候補を再収集")
    ap.add_argument("--limit", type=int, default=30, help="候補収集件数")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.refresh:
        code = run(["tools/pick_products.py", "--limit", str(args.limit)])
        if code:
            return code
    draft = ["tools/make_drafts.py", "--take", str(args.take)]
    if args.dry_run:
        draft.append("--dry-run")
    return run(draft)


if __name__ == "__main__":
    raise SystemExit(main())
