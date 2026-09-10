---
name: seo-rank-watch
description: monobase.site のGoogle検索順位を継続的に改善する。1位を取れそうなキーワードを1つ選び、検索ニーズに応じた改善を1つ行い、7日間観察する。1位になるまで繰り返す。
---

# SEO Rank Watch

対象サイト（monobase.site）のGoogle検索順位を継続的に改善するスキル。

目的：1位を取れそうなキーワードを見つけ、検索ニーズに答える改善を1つ行い、
7日間観察する。これを1位になるまで繰り返す。

## データ

- `content/seo/watchwords.json` — `{ keywords: [{keyword, targetPath, priority}] }`。空でもよい（3.で自動発見する）
- `content/seo/rank-history.json` — `{ entries: [...] }`。順位履歴。**追記専用**、過去のentryは書き換えない
- `content/seo/improvement-log.json` — `{ items: [...] }`。改善履歴・status・次回レビュー日

`status`：
- `active` — 改善候補
- `observing` — 改善後7日間の観察中
- `achieved` — 1位（average position ≦ 1.5）達成。監視のみ

## サイトの構造（このプロジェクト固有）

- 記事ページ `articles/<slug>.html` の中身は `content/articles.json` の該当
  `slug` エントリ（`title` / `description` / `lead` / `sections` / `faq` /
  `conclusion` など）から `build.py` が生成する。**HTMLファイルを直接編集し
  ない**。必ず `content/articles.json` を編集してから `python3 build.py` で
  再生成する。
- カテゴリーページ `category-*.html` の中身は `content/site.json` の
  `categories` から生成される。こちらも直接編集せず `site.json` を編集して
  `python3 build.py` で再生成する。
- `python3 build.py` は構造化データ（Product の offers/review/
  aggregateRating）を検算し、欠けているとビルドが落ちる。既存記事の
  レビュー件数・評価を消さないこと。
- 内部リンク先候補：記事 ↔ カテゴリーページ ↔ `ranking.html`（人気記事）。

## Workflow

### 1. 順位を測る

原則としてGoogle Search Consoleを使う。

```
python3 tools/fetch_gsc_ranks.py --append
```

前回からの順位変動を確認する。GSCが使えない場合や当日の順位を確認したい
場合のみWebSearchを使う（WebSearch順位は概算、GSCを正とする）。
`rank: null` かつ `impressions: 0` は未インデックスとは限らない。必要なら
WebSearchで確認する。

### 2. 7日経過した改善をレビューする

`content/seo/improvement-log.json` の `status: "observing"` かつ
`nextReviewDate <= 今日` の項目を確認する。改善効果を見るときは
28日平均ではなく直近7日のGSCを使う：

```
python3 tools/fetch_gsc_ranks.py --days 7
```

- 1位（average position ≦ 1.5）→ `achieved`
- 改善したが1位未達 → `active`
- 効果なし → `active`。次回は前回と違う改善方法を使う

判定結果を `improvement-log.json` に記録する。

### 3. 今日改善するキーワードを1つ選ぶ

`observing` と `achieved` は除外する。以下の順で1キーワードだけ選ぶ。

1. 2〜10位 + impressionsあり — 1位に近いものを優先
2. 11〜20位 + impressionsが多い
3. 改善したが1位未達 / 効果なし（2.で違う方法が決まっているもの）
4. 高優先度の `rank: null`
5. GSCで見つかった有望な未登録クエリ（`python3 tools/fetch_gsc_ranks.py --discover`）

5.で選んだ場合は、`watchwords.json` にも追加して以後の監視対象にする。

候補がなければ、順位チェックとレポートだけで終了する。**改善するために
無理やり対象を作らない。**

### 4. 検索ニーズを分析する

改善前に必ず、

1. 「誰が・何を知りたくて検索しているか」を1〜2文で定義する
2. WebSearchで現在の上位1〜3ページを確認する
3. 上位ページと対象ページ（`content/articles.json` の該当記事、または
   `content/site.json` のカテゴリー）を比較する
4. 検索ニーズに対して不足している情報をギャップとして特定する

SEOのために文章量を増やすのではなく、検索ユーザーが欲しい情報を追加する。

### 5. 1つのキーワードを改善する

ギャップに応じて必要なものだけ実装する。例：

- `content/articles.json` の `title` / `description` / `lead` / `faq` 改善
- 不足しているセクション（`sections`）の追加
- 記事 ↔ カテゴリーページ ↔ `ranking.html` の内部リンク追加
- 不足している実データ（レビュー件数・価格帯など）の追加
  （`tools/fetch_reviews.py` などで取得済みのものに限る。数字を捏造しない）

編集後は必ず `python3 build.py` を実行して静的HTMLを再生成する。

内部リンクはSEO目的だけでなく、検索ユーザーの「次に知りたい・やりたい
こと」へ誘導する。

**1回の実行で改善するキーワードは必ず1つだけ。**

`noindex` の変更や、テンプレート・レイアウトに関わる大きなページ構造変更は
勝手に適用しない。人が確認できるセッションでは提案して承認を得る。
GitHub Actionsなど無人実行のセッションでは、その変更は見送って
レポートに「要承認」として残す。

見た目に関わる変更（レイアウト・CSSなど）をした場合は、公開前にheadless
Chromeで実物をスクリーンショットして目視確認する。

### 6. 改善を記録して7日待つ

`content/seo/improvement-log.json` の `items` に追記する：

```json
{
  "keyword": "...",
  "targetPath": "...",
  "status": "observing",
  "nextReviewDate": "今日+7日",
  "actions": [{
    "date": "...",
    "rankAtAction": 4.2,
    "needs": "検索ニーズ",
    "done": "実際に行った改善"
  }]
}
```

`content/seo/*.json` の変更、`content/articles.json` / `content/site.json`
の変更、`build.py` が再生成したHTMLをコミットする。**`git add -A` は
使わない**（管理画面の未コミット変更を巻き込む事故があるため）。変更した
ファイルを個別に `git add` してからコミットし、mainへpushする（push起点で
サイトが公開される。ビルドだけでは公開されない）。

`observing` のキーワードは `nextReviewDate` まで絶対に再改善しない。

## Report

最後に簡潔に報告する。

- 前回から大きく上昇 / 下降したキーワード
- 今回行った効果判定（2.のレビュー結果）
- 今日選んだキーワードと選定理由
- 推測した検索ニーズ
- 実際に行った改善
- `observing` 中のキーワードと `nextReviewDate`

順位改善を予測で断定しない。何を変更したかを報告し、効果は次回の実測で
判断する。

## Guardrails

- Google SERPを独自スクリプトでスクレイピングしない。GSCまたはWebSearchを使う
- 1回につき改善は1キーワードだけ
- `observing` の7日間クールダウンを厳守
- `rank-history.json` の過去データを書き換えない（追記のみ）
- 認証キーや秘密情報を出力・コミットしない
- `noindex` や大きな構造変更は承認なしで適用しない
- 改善効果を断定しない
- 改善対象がなければ何もしない
- `git add -A` を使わない。変更したファイルを個別に指定する

「測定 → 1位に近いワードを1つ選ぶ → 検索意図を調べる → 改善 → 7日観察 →
実測で判定」。このループを、1位になるまで繰り返す。
