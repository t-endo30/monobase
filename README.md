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
