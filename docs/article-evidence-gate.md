# 記事証拠ゲート

## 目的

新規記事を自動公開する前に、商品と根拠を読者が追跡できる状態かを確認する。
このゲートは記事の内容が正しいことを保証するものではなく、根拠が無い記事を公開しないための最低条件である。

## 公開前に確認する項目

- 公式資料または `facts` がある
- 検索結果ではなく、個別商品の販売URLがある
- 型番・ASIN・JANなどで商品を一意に同定できる
- `review_stats` を持つ記事は、レビュー本文も保持している

不足がある記事は `published: true` にしない。レビューを実行した場合は、記事JSONの `evidence_audit` に確認日時、根拠URL、欠落項目、保留理由を保存する。

## 一度限りの既存記事監査

全件監査は毎回の記事作成では実行しない。必要なときだけ次を実行する。

```text
python3 tools/audit_evidence.py --all
```

監査結果はローカルの `reports/article-evidence-audit.json` と
`reports/article-evidence-audit.md` に出力する。レポートはサイトへ公開しない。

## 次回以降の記事作成

新規記事では `tools/review_article.py --publish` と
`tools/gpt_review_article.py --publish` が証拠ゲートを通る。
GPT経路は目標本数に達するまで小さなバッチで候補を処理し、生成・レビューに失敗した候補を除外して次候補へ切り替える。認証失敗や利用上限の場合は、無限に再試行せず不足本数を報告して次の実行枠へ繰り越す。
