#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPT経路用の商品選定入口。

候補の取得・重複排除・製品特定はClaude経路と同じ機械ロジックを使い、
選定後の本文だけをGPTへ渡す。モデルに商品を自由選択させない。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(args):
    return subprocess.run([sys.executable, *args], cwd=ROOT, check=False).returncode


def refresh_candidates(limit):
    """GitHub Actionsの暗号化Secretsで候補を集め、artifactだけを取得する。"""
    if not shutil.which("gh"):
        print("gh CLIが見つかりません", file=sys.stderr)
        return 1
    repo = "t-endo30/monobase"
    started = time.time()
    code = subprocess.run(["gh", "workflow", "run", "candidates.yml", "--repo", repo,
                           "-f", f"limit={limit}"], cwd=ROOT, check=False).returncode
    if code:
        return code
    run_id = None
    for _ in range(30):
        proc = subprocess.run(["gh", "run", "list", "--repo", repo,
                               "--workflow", "candidates.yml", "--limit", "5",
                               "--json", "databaseId,createdAt,status",
                               "--jq", ".[] | select(.createdAt != null) | [.databaseId,.createdAt,.status] | @tsv"],
                              cwd=ROOT, text=True, capture_output=True, check=False)
        for line in proc.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                try:
                    if time.time() - started < 5 or parts[2] in ("queued", "in_progress"):
                        run_id = parts[0]
                        break
                except ValueError:
                    pass
        if run_id:
            break
        time.sleep(2)
    if not run_id:
        print("候補収集workflowの実行IDを取得できませんでした", file=sys.stderr)
        return 1
    watch = subprocess.run(["gh", "run", "watch", run_id, "--repo", repo, "--exit-status"],
                           cwd=ROOT, check=False)
    if watch.returncode:
        return watch.returncode
    with tempfile.TemporaryDirectory(prefix="monobase-candidates-") as tmp:
        code = subprocess.run(["gh", "run", "download", run_id, "--repo", repo,
                               "-n", "product-candidates", "-D", tmp],
                              cwd=ROOT, check=False).returncode
        if code:
            return code
        source = os.path.join(tmp, "candidates.json")
        if not os.path.exists(source):
            print("候補artifactにcandidates.jsonがありません", file=sys.stderr)
            return 1
        with open(source, encoding="utf-8") as handle:
            json.load(handle)
        shutil.copy2(source, os.path.join(ROOT, "content", "candidates.json"))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--take", type=int, default=2)
    ap.add_argument("--refresh", action="store_true", help="楽天・Yahoo!から候補を再収集")
    ap.add_argument("--limit", type=int, default=30, help="候補収集件数")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.refresh:
        code = refresh_candidates(args.limit)
        if code:
            return code
    draft = ["tools/make_drafts.py", "--take", str(args.take)]
    if args.dry_run:
        draft.append("--dry-run")
    return run(draft)


if __name__ == "__main__":
    raise SystemExit(main())
