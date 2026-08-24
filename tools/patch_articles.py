#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事に地の文を追記するための小道具。
   バッチ用スクリプトから import して使う。

     from patch_articles import apply
     apply({"slug": { "lead": [...], "sections": [...] }})

   既存の値は上書きする。spec.read / not_for.after のように
   入れ子の中へ入れたいものは "spec.read" のようにドットで書く。
"""
import io, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "content", "articles.json")


def apply(patch):
    arts = json.load(io.open(PATH, encoding="utf-8"))
    index = {a.get("slug"): a for a in arts}
    missing = [s for s in patch if s not in index]
    if missing:
        raise SystemExit("該当する記事がありません: " + ", ".join(missing))

    for slug, fields in patch.items():
        a = index[slug]
        for key, val in fields.items():
            if "." in key:
                head, tail = key.split(".", 1)
                a.setdefault(head, {})[tail] = val
            else:
                a[key] = val

    io.open(PATH, "w", encoding="utf-8").write(
        json.dumps(arts, ensure_ascii=False, indent=1) + "\n")
    print(f"更新: {len(patch)} 本")
