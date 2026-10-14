#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GPT経路用の商品選定入口。

候補の取得・重複排除・製品特定は既存の商品選定ロジックを使い、
新規候補を下書き化したあと、本文生成とレビューをGPT経路へ渡す。
モデルに商品を自由選択させない。
"""
import argparse
import base64
import csv
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# GitHub Actions の workflow_dispatch 入力にはサイズ上限があるため、
# 購入履歴候補を一度に送りすぎない。30件なら商品名が長いページでも
# 圧縮後の入力が上限を越えにくく、ページを進めてCSV全体を探索できる。
ORDER_PAGE_SIZE = 30


def _order_classifier():
    path = os.path.join(ROOT, "AmazonExport", "classify.py")
    spec = importlib.util.spec_from_file_location("monobase_order_classifier", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def order_items(limit=80, offset=0):
    """購入履歴の全ASINを再分類し、既出商品を除いてworkflowへ渡す。

    AmazonExport/candidates.csv は過去の分類結果なので信用せず、元の
    Order History.csv を再分類する。ここでは商品名・ASIN・日付・価格だけを
    渡し、注文番号や配送情報などは外へ出さない。
    """
    src = os.path.join(ROOT, "AmazonExport", "Order History.csv")
    if not os.path.exists(src):
        raise RuntimeError("AmazonExport/Order History.csv が見つかりません")
    classifier = _order_classifier()
    with open(src, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    with open(os.path.join(ROOT, "content", "articles.json"), encoding="utf-8") as f:
        articles = json.load(f)
    used = {str(a.get("asin") or "").upper() for a in articles if a.get("asin")}
    seen = set()
    groups = {}
    for row in rows:
        asin = str(row.get("ASIN") or "").strip().upper()
        name = str(row.get("Product Name") or "").strip()
        if len(asin) != 10 or asin in used or asin in seen or not name:
            continue
        seen.add(asin)
        if classifier.excluded(name):
            continue
        category, sub, _matched = classifier.classify(name)
        if not category or not sub:
            continue
        # adult を含む分類漏れと、カテゴリ内の明白な取り違えを二重に除外。
        if any(x.lower() in name.lower() for x in classifier.EXCLUDE):
            continue
        groups.setdefault(category, []).append({
            "asin": asin, "name": name, "category": category, "sub": sub,
            "order_date": str(row.get("Order Date") or "")[:10],
            "order_price": str(row.get("Unit Price") or ""),
        })
    for values in groups.values():
        values.sort(key=lambda x: (x["order_date"], x["asin"]), reverse=True)
    selected = []
    target = max(0, int(offset)) + max(0, int(limit))
    while len(selected) < target and any(groups.values()):
        for category in sorted(groups):
            if groups[category]:
                selected.append(groups[category].pop(0))
                if len(selected) >= target:
                    break
    return selected[max(0, int(offset)):max(0, int(offset)) + max(0, int(limit))]


def refresh_order_candidates(limit, offset=0):
    """購入履歴由来候補を、Secretsを持つGitHub Actionsで照合する。"""
    if not shutil.which("gh"):
        print("gh CLIが見つかりません", file=sys.stderr)
        return 1
    try:
        # 1ページを広めに取り、前ページが条件不足でも購入履歴CSVの
        # 次の商品へ進める。旧設定は20件だけで止まり、検索語の400が
        # 起きたときに「履歴に候補がない」と誤判定していた。
        page_size = max(ORDER_PAGE_SIZE, limit * 10)
        items = order_items(page_size, offset=offset)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"購入履歴候補を準備できません: {exc}", file=sys.stderr)
        return 1
    if not items:
        print("未記事化でカテゴリ一致するASIN候補がありません", file=sys.stderr)
        return 1
    # workflow_dispatchの入力上限を超えないよう、商品名を含む候補は
    # zlib+base64で圧縮して渡す。注文履歴CSVそのものは渡さない。
    payload = base64.b64encode(zlib.compress(
        json.dumps(items, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), 9
    )).decode("ascii")
    started = time.time()
    code = subprocess.run(["gh", "workflow", "run", "order-candidates.yml", "--repo",
                           "t-endo30/monobase", "-f", f"items_blob={payload}",
                           "-f", f"limit={limit}"], cwd=ROOT, check=False).returncode
    if code:
        return code
    run_id = None
    for _ in range(30):
        proc = subprocess.run(["gh", "run", "list", "--repo", "t-endo30/monobase",
                               "--workflow", "order-candidates.yml", "--limit", "5",
                               "--json", "databaseId,createdAt,status",
                               "--jq", ".[] | select(.createdAt != null) | [.databaseId,.createdAt,.status] | @tsv"],
                              cwd=ROOT, text=True, capture_output=True, check=False)
        for line in proc.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) == 3 and (time.time() - started < 5 or parts[2] in ("queued", "in_progress")):
                run_id = parts[0]
                break
        if run_id:
            break
        time.sleep(2)
    if not run_id:
        print("購入履歴候補workflowの実行IDを取得できませんでした", file=sys.stderr)
        return 1
    watch = subprocess.run(["gh", "run", "watch", run_id, "--repo", "t-endo30/monobase", "--exit-status"], cwd=ROOT, check=False)
    if watch.returncode:
        return watch.returncode
    with tempfile.TemporaryDirectory(prefix="monobase-order-candidates-") as tmp:
        code = subprocess.run(["gh", "run", "download", run_id, "--repo", "t-endo30/monobase",
                               "-n", "order-product-candidates", "-D", tmp], cwd=ROOT, check=False).returncode
        if code:
            return code
        source = os.path.join(tmp, "candidates.json")
        if not os.path.exists(source):
            print("購入履歴候補artifactにcandidates.jsonがありません", file=sys.stderr)
            return 1
        with open(source, encoding="utf-8") as handle:
            data = json.load(handle)
        items = data.get("items") or []
        if not all(x.get("source") == "amazon_order_history" for x in items):
            print("購入履歴由来でない候補が混入したため採用しません", file=sys.stderr)
            return 1
        shutil.copy2(source, os.path.join(ROOT, "content", "candidates.json"))
        print(f"購入履歴由来の照合済み候補 {len(items)} 件を取得しました")
    return 0


def run(args):
    return subprocess.run([sys.executable, *args], cwd=ROOT, check=False).returncode


def refresh_candidates(limit):
    """GitHub Actionsの暗号化Secretsで候補を集め、artifactだけを取得する。"""
    if not shutil.which("gh"):
        print("gh CLIが見つかりません", file=sys.stderr)
        return 1
    repo = "t-endo30/monobase"
    # ファイル名で run list を絞ると、同じ candidates ジョブを持つ購入履歴
    # ワークフローを拾うことがある。通常候補の表示名を固定して、通常候補と
    # 購入履歴候補の切替後に別ワークフローを確実に監視する。
    workflow = "Check candidates"
    started = time.time()
    code = subprocess.run(["gh", "workflow", "run", workflow, "--repo", repo,
                           "-f", f"limit={limit}"], cwd=ROOT, check=False).returncode
    if code:
        return code
    run_id = None
    for _ in range(30):
        proc = subprocess.run(["gh", "run", "list", "--repo", repo,
                               "--workflow", workflow, "--limit", "5",
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
    ap.add_argument("--refresh-orders", action="store_true",
                    help="Amazon購入履歴のASINを楽天・Yahoo!と照合して候補化")
    ap.add_argument("--limit", type=int, default=30, help="候補収集件数")
    ap.add_argument("--order-offset", type=int, default=0,
                    help="購入履歴候補の探索開始位置（カテゴリ巡回後）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.refresh_orders:
        code = refresh_order_candidates(args.limit, offset=args.order_offset)
        if code:
            return code
    elif args.refresh:
        code = refresh_candidates(args.limit)
        if code:
            return code
    draft = ["tools/make_drafts.py", "--take", str(args.take)]
    if args.dry_run:
        draft.append("--dry-run")
    return run(draft)


if __name__ == "__main__":
    raise SystemExit(main())
