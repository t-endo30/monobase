# GPT記事経路

既存のClaude経路は変更せず、次の2段階でGPT経路を使う。

```sh
python3 tools/gpt_write_article.py --drafts
python3 tools/gpt_review_article.py --new
```

一連で実行する場合は次の入口を使う。

```sh
python3 tools/run_gpt_article_pipeline.py --drafts
```

`--publish` はレビュー合格時だけ `published: true` にする。定期実行へ接続するまでは付けず、生成・レビュー結果を確認する。

初回は書き込みをせず確認する。

```sh
python3 tools/gpt_write_article.py <slug> --dry-run
python3 tools/gpt_review_article.py <slug> --dry-run
```

既定はChatGPTにログイン済みのCodex CLIを使うため、`OPENAI_API_KEY`は不要。モデルはCLIの設定または各コマンドの`--model`で変更できる。APIキー方式を明示的に使う場合だけ`GPT_BACKEND=api`と`OPENAI_API_KEY`を設定する（この場合はAPI課金の対象）。

生成はCodex CLIのJSON Schema出力を使う。記事のトップレベル項目とレビュー結果の項目をスキーマで固定し、JSONの前置き・未知のキーを受け付けない。

生成後は既存の `apply_generated` と `audit`、レビュー後は既存の `scan` と85点ゲートを通す。GPTの応答が失敗した場合、レビュー未実施として扱い、公開しない。

## Jevの位置づけ

`--jev` を付けると、既定の `https://jev.moonplace.link/mcp` に接続し、`jev_system_one`で記事の主張リスクを補助判定する。接続先を変える場合だけ `JEV_MCP_URL` を設定する。互換用に `JEV_COMMAND` を設定した場合はコマンド方式を優先する。

Jevは、主張の不確実性・要確認箇所・根拠不足の候補を増やす二次判定としては有効。ただしJevの判定だけで事実を確定してはいけないため、GPTレビューには「要確認候補」として渡し、公式情報・facts・口コミなどの根拠が無い記述は残さない。Jev未接続でも通常の機械検査とGPTレビューは継続する。

この環境ではJevブリッジのヘルスチェックと実呼び出しを確認済み。接続後は同じ入力記事で、Jevなし／ありの指摘数と公式根拠の残存率を比較してから定期実行に入れる。
