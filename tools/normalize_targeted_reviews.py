#!/usr/bin/env python3
import json
import re

PATH = "content/articles.json"
TARGETS = {
    "samsung-galaxy-a57-128gb-awesome-navy",
    "tp-link-archer-ax3000-ax3000-wi-fi",
    "200-dgcam016",
    "pc-20260914",
    "ol-90185",
}

def clean(value):
    if isinstance(value, str):
        value = value.replace("口コミ", "利用者の声")
        value = value.replace("レビュー41件", "利用者評価")
        value = value.replace("レビュー100件", "利用者評価")
        value = re.sub(r"\d+件", "", value)
        value = value.replace("レビューを読み込んで見えたこと", "確認できた情報")
        value = value.replace("レビュー・利用者の声", "利用者評価")
        value = value.replace("レビュー分析", "利用者評価の整理")
        value = value.replace("Tetherアプリ", "公式設定ガイド")
        value = value.replace("軽量", "携帯しやすい")
        value = value.replace("携帯しやすいな", "携帯しやすい")
        value = value.replace("購入者の評価", "利用者の声")
        value = value.replace("レビュー本文", "利用者の声")
        value = value.replace("レビュー情報", "利用者の声")
        value = value.replace("レビューを読む際", "利用者の声を読む際")
        value = value.replace("レビュー", "利用者の声")
        value = value.replace("利用者評価はで平均", "利用者の声では平均")
        value = value.replace("Yahoo!ショッピングはで", "Yahoo!ショッピングで")
        value = value.replace("機材重量や撮影環境による扱いやすさの違いは、根拠データ上では利用者の声そのものではなく、利用者の声と仕様を照合した編集部の整理です。", "機材重量や撮影環境による扱いやすさの違いは、利用者の声と仕様を照合した編集部の整理です。")
        value = value.replace("口コミ", "利用者の声")
        return value
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k not in {"count"}}
    return value

with open(PATH, encoding="utf-8") as f:
    articles = json.load(f)
for article in articles:
    if article.get("slug") in TARGETS:
        article.update(clean(article))
        if article.get("slug") == "200-dgcam016":
            article["cons"] = [
                "一脚のため、手を離して自立させる用途には使えない",
                "機材重量や撮影環境によって安定感・操作感が変わる",
                "カメラ側の取り付け条件が合わないとクイックシューを活用できない",
                "収納時の具体的な寸法や重量は今回の確認範囲に含めていない",
                "長時間同じ構図を固定する目的では三脚が適している",
            ]
        if article.get("slug") == "pc-20260914":
            article["cons"] = [
                "利用するOSによって対応機能が異なる",
                "契約終了後の更新条件は購入時の条件と分けて確認が必要",
                "一部の利用者の声では更新やインストール時にサポートが必要だった",
                "1台だけを短期間使う人には3台・3年の構成が合わない可能性がある",
            ]
            if isinstance(article.get("voices"), list):
                article["voices"] = [v for v in article["voices"] if "編集部分析" not in str(v.get("who", ""))]
            for section in article.get("sections", []):
                section["paras"] = [p.replace("ネット詐欺対策、プライバシー保護、保護者による使用制限、ファイアウォール強化、パソコン・スマホ最適化", "OSごとに対応状況が異なる機能") for p in section.get("paras", [])]
            article["good_for"]["items"][2] = {"title": "対応OSと必要な機能を確認したい人", "text": "公式の対応OS・機能一覧を見て、自分の端末で必要な機能が案内されているか確認したい人に向きます。"}
        if article.get("slug") == "ol-90185":
            article["voices_intro"] = "確認できた利用者の声では、収納量や組み立て後の使いやすさに関する内容が見られます。"
            article["pros"] = [p for p in article.get("pros", []) if "公式ブランド・商品情報を確認できる" not in p]
            article["title"] = article.get("title", "").replace("口コミ", "利用者の声")
            article.pop("personal_note", None)
            article.pop("voices_after", None)
            if isinstance(article.get("conclusion"), list):
                article["conclusion"] = [p.replace("価格・在庫は変動するため", "在庫状況は変動するため") for p in article["conclusion"]]
        if article.get("slug") == "tp-link-archer-ax3000-ax3000-wi-fi":
            article["thumb"] = "https://static.tp-link.com/upload/image-line/Archer_AX3000-JP-2_large_20230216020744e.jpg"
        article["updated"] = "2026-10-07"
with open(PATH, "w", encoding="utf-8") as f:
    json.dump(articles, f, ensure_ascii=False, indent=1)
print("対象記事を正規化しました")
