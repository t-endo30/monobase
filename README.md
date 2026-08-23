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
