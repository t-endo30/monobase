#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Amazonの長い商品名から、記事タイトル用の短い名前を作る。

  $ python3 tools/shorten_name.py "LED投光器 LED作業灯 屋外 コンセント式 2Mコード ..."

Amazonの商品名はSEO目的でキーワードが詰め込まれているため、
そのまま見出しにすると読めない。中核の商品種別と、
購入判断に効く特徴だけを残す。
"""
import re, sys, unicodedata

# 商品の中核となる種別（先頭付近に出ることが多い）
CORE = [
    "投光器", "作業灯", "デスクライト", "シーリングライト", "電球", "照明",
    "イヤホン", "ヘッドホン", "スピーカー", "マイク", "webカメラ",
    "メカニカルキーボード", "キーボード", "マウス", "モニター", "ディスプレイ", "モニターアーム",
    "充電器", "モバイルバッテリー", "ケーブル", "USBハブ", "SSD", "HDD",
    "加湿器", "除湿機", "空気清浄機", "掃除機", "扇風機", "サーキュレーター",
    "ヒーター", "電気ケトル", "炊飯器", "電子レンジ", "冷蔵庫",
    "チェア", "椅子", "デスク", "クッション", "枕", "マットレス", "ラック", "収納",
]

# 購入判断に効く特徴（拾って括弧内に入れる）
FEATURE = [
    r"コンセント式", r"充電式", r"電池式", r"USB給電", r"ソーラー",
    r"IP6[0-9]", r"IPX[0-9]", r"防水", r"防塵", r"防犯",
    r"人感センサー", r"センサー付", r"リモコン付", r"調光", r"調色",
    r"昼光色", r"昼白色", r"電球色",
    r"\d+W", r"\d+V", r"\d+lm", r"\d+畳", r"\d+インチ", r"\d+mm", r"\d+kg",
    r"ワイヤレス", r"Bluetooth", r"有線", r"折りたたみ", r"超薄型", r"薄型",
    r"ノイズキャンセリング", r"静音", r"高反発", r"低反発",
]

DROP = [
    r"送料無料", r"日本語説明書", r"PSE認証", r"技適", r"1年保証", r"２年保証",
    r"新登場", r"最新", r"改良版", r"進化版", r"正規品", r"日本企業", r"国内発送",
    r"多用途", r"多機能", r"高輝度", r"超高輝度", r"省エネ", r"長寿命",
    r"[0-9]+個セット", r"セット", r"プレゼント", r"ギフト",
]


def shorten(name, max_features=2):
    t = unicodedata.normalize("NFKC", name)
    t = re.sub(r"[【\[（(].*?[】\]）)]", " ", t)      # 括弧内の宣伝文句を除去
    for d in DROP:
        t = re.sub(d, " ", t, flags=re.I)
    t = re.sub(r"[／/、,]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    # 中核の種別を探す（最初に見つかったもの）
    core = ""
    for c in sorted(CORE, key=len, reverse=True):   # 最長一致を優先
        if c in t:
            core = c
            break
    if core:
        # 直前の LED / ワイヤレス などの接頭辞を残す
        m = re.search(r"(LED|LEDライト|ワイヤレス|電動|折りたたみ)\s*" + re.escape(core), t, re.I)
        if m:
            core = m.group(0).replace(" ", "")
    if not core:
        # 見つからなければ先頭の語をそのまま使う
        core = t.split(" ")[0][:16]

    # 特徴を拾う（重複を避けつつ最大 max_features 個）
    feats, seen = [], set()
    for pat in FEATURE:
        m = re.search(pat, t, re.I)
        if not m:
            continue
        v = m.group(0)
        key = v.lower()
        if key in seen:
            continue
        if key in core.lower():        # 中核語に含まれる語は繰り返さない
            continue
        seen.add(key)
        if re.match(r"IP", v, re.I):
            seen.update({"防水", "防塵"})       # IP等級があれば重複表記を避ける
        feats.append(v)
        if len(feats) >= max_features:
            break

    return f"{core}（{'・'.join(feats)}）" if feats else core


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 0
    for name in sys.argv[1:]:
        print(f"元 : {name}")
        print(f"短 : {shorten(name)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
