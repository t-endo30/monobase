# モノベース

暮らしと作業を快適にするおすすめアイテム紹介ブログ（Amazonアソシエイト対応）。
GitHub Pages + 独自ドメインで運用する静的サイトです。

## 構成

```
content/site.json        サイト設定（サイト名・ドメイン・GA/GSC・機能ON/OFF）
content/articles.json    記事データ（これが唯一の原稿。HTMLは手で触らない）
build.py                 ジェネレーター。JSON → 全HTML を生成
admin.html               管理画面（記事の追加・編集・削除、画像圧縮、設定）
assets/style.css         サイト共通CSS
assets/main.js           サイト共通JS（ナビ・追従CTA）
assets/search.js         サイト内検索
assets/admin.css / .js   管理画面
assets/img/              画像（常に圧縮して置く）
tools/optimize-images.sh 画像一括圧縮（macOS）
tools/check_images.py    画像サイズ検査（CIで実行）
tools/review_article.py  記事レビュー（禁止表現・ダークパターン）
tools/maintain_articles.py 公開中の記事の見回り（リンク切れ・鮮度）
tools/schedule_gate.py   自動作成の実行日と本数を決める
docs/review-rules.md     レビューの判定基準
.github/workflows/       push すると自動でビルド＆デプロイ
```

生成されるファイル（**直接編集しない**。build.py が上書きします）:
`index.html` / `articles/*.html` / `category-*.html` / `search.html` /
`about.html` / `privacy.html` / `disclaimer.html` / `404.html` /
`search.json` / `sitemap.xml` / `robots.txt` / `CNAME`

## 記事を書く

### 方法A：管理画面（推奨）

1. `https://<ドメイン>/admin.html` を開く
2. 「接続」タブで GitHub のユーザー名・リポジトリ名・アクセストークンを入力
3. 「記事」タブ →「＋ 新規記事を作成」→ 入力 →「この記事を保存」
4. 「記事」タブ →「GitHubに保存して公開」
5. 1〜2分で GitHub Actions がビルドし、サイトに反映される

トークンは **Fine-grained personal access token**（Contents = Read and write、対象リポジトリのみ）を使ってください。
`robots.txt` で `admin.html` はクロール除外済みですが、URL自体は公開されます。第三者に知られてもトークンがなければ書き込みはできません。

### 方法B：ローカル

```bash
# content/articles.json を編集してから
python3 build.py
git add -A && git commit -m "記事を追加" && git push
```

### 方法C：Claude に書かせて、レビューまで通す

```bash
python3 tools/write_article.py --drafts          # 本文を書かせる
python3 tools/review_article.py --new            # レビューして直す
python3 tools/review_article.py --new --publish --push   # 公開して push まで
```

`tools/review_article.py` は、記事ができたあとの最終検査です。

1. **機械検査** … 禁止表現・ダークパターン（煽り／閲覧者数の演出／割引表示など）・
   使えないHTMLタグ・項目の形の崩れ・分量を、正規表現で拾う
2. **Claude によるレビュー** … `docs/review-rules.md` を基準として渡し、
   指摘と修正後の値を返させる。返ってきた値を `content/articles.json` に書き戻す
3. **やり直し** … 直したあと、もう一度①をかける（`--rounds` 回まで）
4. **仕上げ** … `build.py` と `tools/check_*.py` を回し、
   `--publish` なら `published: true`、`--push` ならコミットして push

`--check-only` を付けると機械検査だけを行い、Claude を呼びません（書き換えもしません）。
判定の基準は `docs/review-rules.md` にまとまっています。ルールを足すときはそこに書きます。

週次の `.github/workflows/write.yml` でも、本文を書いた直後にこのレビューが走ります。

### ASPの広告（A8.net・バリューコマースなど）

`content/site.json` の `promos` に、ASPで取得した広告リンクを**そのまま**持ちます
（管理画面の「サイト設定 → ASPの広告」から追加・削除できます）。

```
label   広告の上に出す表示（既定 "PR"）
items   [{name, where, cats, html}]
          where … article_end（記事の下）／side（PCサイド）／none（出さない）
          cats  … 対象カテゴリーのkey。空なら全記事
          html  … ASPからコピーしたコードをそのまま
```

コードは書き換えません。こちらで決めるのは置き場所と対象カテゴリーだけです。
「PR」の表示は自動で付きます（ステマ規制の対応）。

`html` に複数のコードを入れると、**表示のたびに1つを選びます**。
区切りは `---` だけの行でも、単に続けて貼るだけでも構いません
（ASPのリンクの始まりを見て、1件ずつに自動で分けます）。

A8の広告リンクを1件ずつコピーするのは骨が折れるので、
`tools/a8-collect.js` を用意しています。A8の「広告リンク」ページで
開発者ツールのコンソールに貼ると、そのページのコードが全部
クリップボードに入ります（コードには手を触れません）。
選ばれなかったコードは `<template>` の中に残るので、画像も計測用の画像も読み込まれません
（1回の表示につき1件だけが数えられます）。

### 自動で記事を作る頻度

`content/site.json` の `automation` で決めます（管理画面の「サイト設定」から変更可）。

```
enabled           自動作成のON/OFF
runs_per_week     週に何回まわすか（1〜7）
articles_per_run  1回に何本作るか（1〜10）
auto_publish      true なら、レビューを通った記事をそのまま公開する
```

`.github/workflows/write.yml` は**毎日**動き、`tools/schedule_gate.py` が
この設定を読んで実行日を間引きます（週2回なら月・金、週3回なら月・水・土）。
`auto_publish` を切ると、下書きはプルリクエストで止まります。

### 公開後の見回り

`.github/workflows/maintain.yml` が毎日 `tools/maintain_articles.py` を回します。

- 販売先が1つでも生きていれば、**切れたリンクだけ外して**公開を続ける
- 販売先が全部切れたら、**公開を止める**（`published:false`）
- 最後の更新から1年以上たった記事は、古い記事として報告する

記事が増えても実行時間が伸びないよう、1回に見るのは `--budget` 本（既定40本）だけです。
「最後に見てから長く経っている順」に選ぶので、毎日まわせば順に一巡します
（記事1000本・1日40本なら25日で一周）。各記事の `health.checked` に最後に見た日が入ります。

### 広告（Google AdSense）

`content/site.json` の `ads` で決めます（管理画面の「サイト設定」から変更可）。

```
enabled   広告を出すか
client    パブリッシャーID（ca-pub-…）
mode      manual＝下の位置にだけ出す ／ auto＝自動広告
slots     article_mid / article_end / side に広告ユニットID
```

`client` を入れておけば、所有確認のメタタグと `ads.txt` は
build.py が自動で書き出します（`ads.txt` はドメイン直下に必要）。

**Googleが配るコードは書き換えません。** 置き場所だけこちらで決めています。

| 位置 | 場所 |
|---|---|
| `article_mid` | 記事の「メリット・デメリット」の直後 |
| `article_end` | 関連記事の下（ページ最下部） |
| `side` | PCサイドのランキング・検索の下 |

購入ボタンの近くには置きません。広告とアフィリエイトリンクが隣り合うと、
読者がどちらを押しているのか分からなくなり、規約上もリスクになるためです。

## 画像

**常に圧縮してから置く**（GitHubの容量制限対策）。

- 管理画面の「画像」タブに投げ込めば、自動でリサイズ＋WebP変換されてからアップロードされます
- 手元で処理する場合：`bash tools/optimize-images.sh 1200`
- CI で1枚300KBを超える画像があるとビルドが失敗します（`tools/check_images.py`）

## ローカルプレビュー

```bash
python3 build.py
python3 -m http.server 8000
# → http://localhost:8000
```

`file://` で直接開くと検索機能（fetch）が動かないため、必ずサーバー経由で確認してください。

## お問い合わせフォーム

初期状態は **OFF**（フッターのメールリンクのみ）です。必要になったら管理画面の
「サイト設定」→「お問い合わせフォームを設置する」をON にし、送信先URLを入れるだけで
`contact.html` が生成され、ヘッダー・フッターのリンクも自動で切り替わります。

GitHub Pages はサーバー処理ができないため、外部サービスの受信URLが必要です:
Formspree（月50件無料）／ Googleフォーム ／ Cloudflare Workers など。

## デプロイ

`main` に push すると `.github/workflows/deploy.yml` が
`build.py` を実行して GitHub Pages に公開します。
リポジトリの Settings → Pages → Source は **GitHub Actions** を選択してください。

## Amazonリンクの運用（第1段階：ASIN方式）

記事には **ASIN**（商品ページURLの `/dp/` 直後の10桁）だけを入れる。
アソシエイトIDは `content/site.json` の `amazon.associate_tag` で一元管理し、
`build.py` が以下の形でリンクを組み立てる。

```
https://www.amazon.co.jp/dp/{ASIN}?tag={associate_tag}
```

IDを変更しても全記事へ自動反映されるため、記事ごとに貼り直す必要がない。
ASIN が空の記事は `amazon_url` の値がそのまま使われる。

### 規約上の注意

- **価格は記事に直書きしない。** PA-API 未取得のあいだは「価格を見る」ボタンのみにする。
  比較表に価格を載せる場合は取得日を明記するか、「1万円台」のような価格帯表記にとどめる
- **Amazonの商品画像は使えない。** PA-API 経由で取得したものだけが利用可。
  それまでは自動生成ビジュアル（下記）か自分で撮影した写真を使う
- スクレイピングは禁止。アカウント停止のリスクがある

### 第2段階（PA-API 取得後）

適格販売3件を達成して PA-API のキーが発行されたら、
Actions の定期実行で価格・在庫・公式画像を毎日更新する構成に移行できる。
24時間ごとに更新されるため、「価格は24時間以内のもの」という規約要件を満たせる。

## アイキャッチ画像

`thumb` が空の記事は、**ビルド時にSVGのアイキャッチが自動生成される**
（`assets/img/auto/{slug}.svg`）。カテゴリー色で配色され、タイトルと
サイト名が入る。外部素材を使わないため著作権・規約のリスクがない。

実写真を用意したら、管理画面の「画像」タブからアップロードして
`thumb` にパスを入れる。そちらが優先され、自動生成SVGは削除される。

> **注意：** SNSのOGP画像はSVG非対応のため、シェア時のサムネイルを出したい記事には
> PNG/JPEG の実画像が必要。

## アクセスランキング

トップ右（PC）とランキングページに表示します。元データは2系統です。

1. `content/ranking.json` に値があれば、それ（サイト全体の実数）
2. 空なら、閲覧者自身の端末に記録された閲覧回数

2 のままでも動きますが、閲覧者ごとの数字なので「サイトでよく読まれている記事」には
なりません。実数に切り替えるには GA4 と接続します。

### GA4 と接続する手順

1. **GA4 の測定IDを設定する**
   管理画面「サイト設定」→ GA測定ID（`G-XXXXXXXXXX`）を入力して保存。
   これを入れないとアクセスが計測されません。

2. **サービスアカウントを作る**
   Google Cloud コンソール → IAMとサービスアカウント → サービスアカウントを作成 →
   鍵（JSON）を作成してダウンロード。

3. **GA4 に閲覧権限を与える**
   GA4 の管理 → プロパティのアクセス管理 → 2 で作ったサービスアカウントの
   メールアドレスを「閲覧者」で追加。

4. **GitHub に登録する**
   リポジトリの Settings → Secrets and variables → Actions で2つ登録します。

   | Secret 名 | 中身 |
   |---|---|
   | `GA4_PROPERTY_ID` | GA4 のプロパティID（数字のみ。測定IDとは別） |
   | `GA4_SA_KEY` | 2 でダウンロードしたJSONの中身をそのまま貼り付け |

5. あとは毎日 5:00（JST）に `.github/workflows/ranking.yml` が動き、
   `content/ranking.json` を更新してコミットします。手動で動かす場合は
   Actions タブから「Update access ranking」を実行してください。

Secret が未設定でも、ワークフローは警告を出して終了するだけで失敗しません。
ローカルで試す場合は次のとおりです。

```bash
pip install google-analytics-data
export GA4_PROPERTY_ID=123456789
export GOOGLE_APPLICATION_CREDENTIALS=~/ga4-sa.json
python3 tools/fetch_ranking.py --days 28
```

## 記事の画像をAIで作る

`tools/make_images.py` が記事ごとに英文プロンプトを組み立て、Gemini に写真風の
画像を作らせます。作った画像は `assets/img/gen/<slug>.jpg` に保存され、
`articles.json` の `thumb` が差し替わります。

```bash
python3 tools/make_images.py --dry-run                 # プロンプトの確認だけ
export GEMINI_API_KEY=xxxxxxxx
python3 tools/make_images.py --slug mx-master-3s-review
python3 tools/make_images.py --all --limit 5
```

GitHub 上で動かす場合は、Settings → Secrets and variables → Actions に
**`GEMINI_API_KEY`** を登録し、Actions タブの「Generate article images」を
手動実行してください（課金されるため自動実行にはしていません）。

**APIキーを管理画面に入力しないでください。** 管理画面の内容はGitHubへ
コミットされるため、公開リポジトリにキーが残ります。管理画面ではモデルの
選択だけを行い、キーは必ず Secrets か環境変数で渡します。

### 画像の扱いについて

- 生成画像には `image_ai: true` が付き、記事のアイキャッチの下に
  「イメージ（AI生成）。実際の製品とは異なります。」と表示されます
- プロンプトはブランド名・ロゴ・文字を出さない指定にしています。実在する製品の
  外観を模した画像は、商標や意匠の問題に加えて読者の誤認を招くためです
- Amazonの商品画像は保存・加工が規約で禁止されているため、生成画像とは
  別物として扱ってください（記事内の公式リンクで表示する用途に限られます）
