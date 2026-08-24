#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サブカテゴリー単位で記事の蓄積を見て、特集を作るべきかを判定し、
   載せる記事を選び、特集記事の下書きまで組み立てる。

  $ python3 tools/feature_plan.py            # 判定と選出結果を表示するだけ
  $ python3 tools/feature_plan.py --write    # 下書き（published:false）を追加

【1本増えるたびに作り直さないための考え方】
  しきい値（site.json の features.feature_threshold、5/10/15）を「段」として扱う。
  記事数 ÷ しきい値 の整数部分を「段」と呼び、段が上がったときだけ作り直す。
  例）しきい値5 → 5本で1段目の特集。6〜9本では作らない。10本で2段目。
  すでに同じ段の特集がある場合は何もしない。

【どの記事を載せるかの選び方】
  ただ新しい順に並べるのではなく、比較記事として成立する組み合わせを選ぶ。
    ・比較軸が揃っているか（スペック表の見出しが他と重なるほど加点）
    ・記事としての厚み（結論・良い点・気になる点・表の行数）
    ・情報の新しさ（更新日が古いものは減点）
    ・似すぎる記事を避ける（タグとタイトル語の重複が多いものは減点）
  上位から既定5本を選び、なぜ選んだかを併せて出力する。
"""
import argparse, io, json, os, re, sys
from collections import Counter
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A_PATH = os.path.join(ROOT, "content", "articles.json")
S_PATH = os.path.join(ROOT, "content", "site.json")

PICK = 5          # 1本の特集に載せる記事数の上限


def load():
    arts = json.load(io.open(A_PATH, encoding="utf-8"))
    site = json.load(io.open(S_PATH, encoding="utf-8"))
    return arts, site


def words(t):
    return set(re.findall(r"[ぁ-んァ-ヶ一-龠A-Za-z0-9]{2,}", t or ""))


def score(a, peers):
    """比較記事として載せる価値を点数にする。peers は同じジャンルの他の記事。"""
    s, why = 0.0, []

    # 比較軸の揃い方：スペック表の見出しが他の記事と重なるほど、並べて比べやすい
    heads = set(a.get("spec", {}).get("headers", []))
    if heads:
        shared = sum(len(heads & set(b.get("spec", {}).get("headers", []))) for b in peers)
        v = min(shared * 0.6, 6)
        s += v
        if v >= 2:
            why.append("比較軸が他の記事と揃っている")

    # 記事の厚み
    depth = (len(a.get("summary", [])) + len(a.get("pros", [])) + len(a.get("cons", []))
             + len(a.get("voices", [])) * 2 + len(a.get("spec", {}).get("rows", [])))
    s += min(depth * 0.25, 8)
    if depth >= 20:
        why.append("内容量が十分")

    # 新しさ（今年なら満点、古いほど減る）
    try:
        y = int((a.get("updated") or a.get("date") or "2000")[:4])
        s += max(0, 4 - (date.today().year - y) * 1.5)
    except ValueError:
        pass

    # 似すぎている記事は避ける（同じような製品ばかりの特集にしない）
    mine = words(a.get("list_title") or a.get("title")) | set(a.get("tags", []))
    dup = sum(len(mine & (words(b.get("list_title") or b.get("title")) | set(b.get("tags", []))))
              for b in peers)
    s -= min(dup * 0.25, 4)

    # ASIN があるもの（実在の商品レビュー）を優先する
    if a.get("asin"):
        s += 2
        why.append("商品が特定できている")
    return s, why


def plan(arts, site):
    th = int((site.get("features") or {}).get("feature_threshold") or 5)
    pub = [a for a in arts if a.get("published")]
    labels = {c["key"]: c["label"] for c in site["categories"]}
    slabels = {(c["key"], sc["key"]): sc["label"]
               for c in site["categories"] for sc in c.get("sub", [])}

    # すでにある特集が、どのジャンルの何段目をカバーしているか
    done = {}
    for a in arts:
        if a.get("category") == "feature" and a.get("feature_of"):
            done[a["feature_of"]] = max(done.get(a["feature_of"], 0),
                                        int(a.get("feature_stage") or 1))

    out = []
    for c in site["categories"]:
        if c["key"] == "feature":
            continue
        for sc in c.get("sub", []):
            key = f'{c["key"]}/{sc["key"]}'
            items = [a for a in pub if a["category"] == c["key"] and a.get("sub") == sc["key"]]
            stage = len(items) // th                    # 何段目まで到達したか
            if stage < 1 or stage <= done.get(key, 0):  # 未到達、または作成済み
                continue
            ranked = []
            for a in items:
                peers = [b for b in items if b is not a]
                sc_, why = score(a, peers)
                ranked.append((sc_, why, a))
            ranked.sort(key=lambda x: -x[0])
            out.append({
                "key": key,
                "label": f'{labels[c["key"]]}／{slabels[(c["key"], sc["key"])]}',
                "cat": c["key"], "sub": sc["key"],
                "total": len(items), "stage": stage, "threshold": th,
                "picked": ranked[:PICK],
                "rest": ranked[PICK:],
            })
    return th, out


def draft(pl, site):
    """特集記事の下書き。構成・比較表・各記事への導線までは機械的に作れる。
       本文の評価コメントは、公開前に人が確認して書き足す前提。"""
    picked = [a for _, _, a in pl["picked"]]
    name = pl["label"].split("／")[-1]
    slug = f'feature-{pl["cat"]}-{pl["sub"]}-{pl["stage"]}'
    heads = ["記事", "結論", "向いている人"]
    rows = []
    for a in picked:
        rows.append([
            f'<a href="{a["slug"]}.html">{a.get("list_title") or a["title"]}</a>',
            (a.get("verdict_title") or "").replace("結論：", "") or "—",
            (a.get("not_for", {}).get("items") or ["—"])[0][:40] + "…",
        ])
    today = date.today().isoformat()
    return {
        "slug": slug, "category": "feature", "sub": "compare",
        "published": False, "featured": False,
        "feature_of": pl["key"], "feature_stage": pl["stage"],
        "feature_covers": [a["slug"] for a in picked],
        "asin": "", "amazon_url": "", "banner": "",
        "title": f"{name}のおすすめ{len(picked)}選｜どんな場合にどれを選ぶか",
        "list_title": f"{name}のおすすめ{len(picked)}選",
        "description": f"{name}のレビュー記事{pl['total']}本から{len(picked)}製品を選び、"
                       f"どんな条件のときにどれが向くかを整理しました。",
        "excerpt": f"{name}の{len(picked)}製品を、選ぶ条件ごとに整理しました。",
        "date": today, "updated": today,
        "tags": ["比較", name], "icon": "📊", "thumb": "",
        "cta_label": "Amazonで価格と詳細を確認する",
        "verdict_title": "結論：条件で選ぶものが変わる",
        "summary": [f"{name}のレビュー{pl['total']}本のうち、比較軸が揃う{len(picked)}製品を選定",
                    "（公開前に記入）どれを選ぶかの分かれ目",
                    "（公開前に記入）価格差が意味を持つ条件"],
        "rating": {"score": 0, "breakdown": ""},
        "lead": f"{name}について公開しているレビューが{pl['total']}本になりました。"
                f"ここでは比較しやすい{len(picked)}製品を並べ、"
                f"<strong>どんな条件のときにどれを選ぶか</strong>を整理します。",
        "not_for": {"intro": "（公開前に記入）この記事が役に立たない人", "items": []},
        "scenes": [], "pros": [], "cons": [],
        "spec": {"intro": "選定した記事の要点です。表は横にスクロールできます。",
                 "headers": heads, "rows": rows},
        "voices_intro": "", "voices": [], "personal_note": "",
        "next_problem": {"intro": "", "items": []},
        "conclusion_title": "まとめ", "conclusion": "（公開前に記入）",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="下書きを articles.json に追加する")
    args = ap.parse_args()

    arts, site = load()
    th, plans = plan(arts, site)
    print(f"特集のしきい値：{th}本ごと（1段）\n")
    if not plans:
        print("いま作るべき特集はありません。")
        print("（しきい値に届いていないか、その段の特集がすでにあります）")
        return 0

    added = []
    for pl in plans:
        print(f"■ {pl['label']}  {pl['total']}本 → {pl['stage']}段目の特集を作る")
        for i, (sc_, why, a) in enumerate(pl["picked"], 1):
            print(f"   {i}. [{sc_:5.1f}] {a.get('list_title') or a['title']}")
            if why:
                print(f"        理由: {' / '.join(why)}")
        for sc_, _, a in pl["rest"]:
            print(f"   -  [{sc_:5.1f}] {a.get('list_title') or a['title']}（今回は見送り）")
        if args.write:
            d = draft(pl, site)
            if any(x["slug"] == d["slug"] for x in arts):
                print(f"   ※ {d['slug']} はすでにあります")
            else:
                arts.append(d); added.append(d["slug"])
        print()

    if args.write and added:
        json.dump(arts, io.open(A_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"下書きを追加しました：{', '.join(added)}")
        print("本文の評価コメントを書き足してから published:true にしてください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
