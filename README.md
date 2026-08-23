# Kurashi Pick

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
