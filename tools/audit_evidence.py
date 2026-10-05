#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""既存記事の根拠状態を分類し、修正対象レポートを生成する。"""
import argparse
import datetime as dt
import json
import os
from collections import Counter
from article_evidence import assessment

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="下書きも含める")
    parser.add_argument("--json", default="reports/article-evidence-audit.json")
    parser.add_argument("--markdown", default="reports/article-evidence-audit.md")
    args = parser.parse_args()
    with open(os.path.join(ROOT, "content", "articles.json"), encoding="utf-8") as f:
        articles = json.load(f)
    targets = articles if args.all else [a for a in articles if a.get("published")]
    rows = []
    for article in targets:
        result = assessment(article)
        rows.append({"slug": article.get("slug"), "title": article.get("title"),
                     "published": bool(article.get("published")),
                     "updated": article.get("updated") or article.get("date"), **result})
    counts = Counter(row["category"] for row in rows)
    missing_counts = Counter(item for row in rows for item in row["missing"])
    summary = {"generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
               "scope": "all" if args.all else "published", "total": len(rows),
               "counts": dict(counts), "missing_counts": dict(missing_counts), "articles": rows}
    for path in (args.json, args.markdown):
        os.makedirs(os.path.dirname(os.path.join(ROOT, path)), exist_ok=True)
    with open(os.path.join(ROOT, args.json), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2); f.write("\n")
    lines = ["# 記事証拠監査レポート", "", f"生成日時: {summary['generated_at']}",
             f"対象: {'全記事' if args.all else '公開記事'}（{len(rows)}本）", "",
             "## 分類", "", "| 分類 | 本数 |", "|---|---:|"]
    for category in ("修正可能", "追加調査", "公開停止候補"):
        lines.append(f"| {category} | {counts.get(category, 0)} |")
    lines += ["", "## 不足項目", "", "| 項目 | 本数 |", "|---|---:|"]
    for key, count in missing_counts.most_common():
        lines.append(f"| {key} | {count} |")
    lines += ["", "## 記事一覧", "", "| 分類 | slug | 公開 | 不足項目 |", "|---|---|---:|---|"]
    for row in sorted(rows, key=lambda x: (x["category"], x.get("slug") or "")):
        missing = "、".join(row["missing"]) or "なし"
        lines.append(f"| {row['category']} | `{row.get('slug','')}` | "
                     f"{'はい' if row['published'] else 'いいえ'} | {missing} |")
    with open(os.path.join(ROOT, args.markdown), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"監査対象 {len(rows)}本")
    for category in ("修正可能", "追加調査", "公開停止候補"):
        print(f"  {category}: {counts.get(category, 0)}本")
    print(f"不足項目: {dict(missing_counts)}")
    print(f"レポート: {args.json}, {args.markdown}")

if __name__ == "__main__":
    main()
