# monobase.site 運用メモ

このファイルは、Claude Code のセッション・キャッシュ・メモリ（`~/.claude/...`）が
消えても失われないよう、このリポジトリで繰り返し必要になる運用知識をまとめたもの。
`~/.claude` 配下の自動メモリは端末・アカウントのローカル状態でしかないが、
このファイルは git リポジトリの一部なので `git clone` すれば必ず一緒に付いてくる。

新しい教訓を得たら、ここに追記する（このファイルも通常のコミット対象）。

---

## 1. 公開の仕組み（絶対に外さないこと）

- 配信は **Cloudflare が GitHub リポジトリの `main` を直接見ている**方式。
  公開手順は必ず `python3 build.py` → コミット → **`origin/main` へ push** まで。
  手元から `npx wrangler deploy` するだけでは、次にリポジトリ発のデプロイが走った
  瞬間に上書きされて消える（2026-09-02 に実際に発生）。
- push 前に `git fetch` して `origin/main` から離れていないか確認する。
  管理画面（`/admin`）からの記事追加や、GitHub Actions の自動再生成コミット
  （「サイトを再生成（自動）」）が向こうに積まれていることが多い。
- コミット時は **`git add -A` / `git add .` を使わない**。変更したファイルを
  パス指定で add する。管理画面がバックグラウンドで `content/articles.json` を
  書き換えるため、作業ツリーに「自分が触っていない変更」が同居しうる。
  2026-09-05 に `git add -A` で記事本文の書きかけ状態を巻き込んでコミット・push し、
  本文3節を消したことがある。commit 前は必ず `git status --short` を読み、
  身に覚えのない差分は取り込まずユーザーに報告する。
- 別プロセス（管理画面など）が自動で `git stash` → リベース → `stash pop` を
  裏で回すことがある。編集中のファイルが一瞬 HEAD の内容に戻って見えても、
  壊れたのではなく退避されているだけ。慌てて書き直さず `git stash list` /
  `git reflog` を見て pop を待つ。push が弾かれたときの衝突は、ほぼ全てが
  生成物 HTML の `?v=` スタンプ行だけなので、片側を採って `build.py` を
  流し直せば整合する。
- 見た目（CSS）を変えたら、公開前に必ずヘッドレス Chrome でスクリーンショットを
  撮って目視確認する。読んだだけの推測で直さない（2回デグレさせた実績あり）。
  幅は 390px（スマホ）と 500px を見る。**このMacのヘッドレスChromeは
  `--window-size` の幅が約500px未満だと効かず、`clientWidth` が485〜500に
  頭打ちになる**ので、390px指定のスクショは右側が切れて写る。実際の幅で
  判定したいときは `getBoundingClientRect()` の実測値を数値で取る。
  ```
  (python3 -m http.server 8765 &)
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new \
    --disable-gpu --hide-scrollbars --virtual-time-budget=4000 \
    --window-size=390,3000 --screenshot=<出力先>.png http://127.0.0.1:8765/index.html
  ```
- `build.py` は JSON-LD を検算し、`offers`/`review`/`aggregateRating` のどれも
  持たない `Product`（入れ子含む）があるとビルドを失敗させる。レビューの
  構造化データは Product を頂点にして中に review を置く形にすること。

## 2. 自動記事作成（`.github/workflows/write.yml`）

- 毎日5時間おき×5回 cron で走る。頻度・本数（`runs_per_week` /
  `articles_per_run`）と自動公開の有無（`auto_publish`）は
  `content/site.json` の `automation` で管理画面から変更できる。
  `enabled:false` の間は何も作らない。
- 流れ：`pick_products.py`（候補集め）→ `make_drafts.py`（下書き化）→
  `write_article.py`（本文生成、Claude Code サブスク使用）→
  `backfill_shop_urls.py` / `fetch_shop_images.py`（楽天・Yahoo!のURL/写真埋め）→
  `review_article.py --publish --push`（校閲・公開・push を1回にまとめる）。
- **Claude Code のサブスクは5時間ごとに利用上限がリセット**される。
  1回のジョブが欲張ると「上限に当たって0本のまま90分粘って失敗」を
  起こしやすい（2026-09-11〜09-14に実際に繰り返し発生）ため、1回の実行の
  目標は最大2本までに絞ってある。
- `write_article.py` のメイン書き込みループ・`review_article.py` の校閲ループには
  「TRANSIENT な失敗が続けて2回で諦める（dead）」early-exit の仕組みが必須。
  無いと session limit に当たったまま候補を替えて呼び直し続け、
  タイムアウトまで1本も書けずに空回りする（2026-09-11に実際に発生、
  write_article.py 側に無くて起きた）。
- `CLAUDE_CODE_OAUTH_TOKEN` と `CLAUDE_CODE_OAUTH_TOKEN_2`（GitHub Secrets）は
  **本来は別アカウントの予備として用意する想定だったが、2026-09-12の調査で
  実は同一アカウント（同一orgId）と判明した**。session limit はアカウント単位
  なので、切り替えても回避にならない。恒久対応は本当に別アカウントの
  Pro サブスクを TOKEN_2 に差し替えること。当面は既定モデルを opus ではなく
  sonnet にして同じ枠でより多く書けるようにしている
  （`write.yml` / `write_article.py` / `review_article.py` の `--model` 既定値）。
  「毎日動いているのに記事が0本」に見えたら、まず session limit を疑う。
- 「メーカー公式情報が取れない」はこのサイトでは異常ではなく通常運用。
  `official_url` や `facts` を人力入力する運用は取らない。公式仕様が
  確認できないときは `rating` と `spec`（比較表）をキーごと省いて書き上げる
  （2026-09-03 に検査の向きを反転させた：「公式情報が無いこと」ではなく
  「裏づけの無い rating/spec を出していること」を指摘する）。

## 3. 校閲・公開基準（`tools/review_article.py` / `docs/review-rules.md`）

- 基準の全文は `docs/review-rules.md`。特に「5. 事実の扱い」節が最優先。
- **製品を特定できない記事は、下書きにも残さず丸ごと破棄する。**
  題名・本文のどこにもメーカー名・型番が出てこず、リンク先の商品を
  読者が特定できない記事は、校閲で製品名を補うと捏造になるため直しようがない。
  「要確認」として残すと、自動生成のたびにレビューへ掛かってコストを食うだけで
  いつまでも公開されない。2026-09-08 に `ss-p2-hifi-bluetooth6-iphone-android`
  （一般名詞の説明に終始）で発生し、破棄する運用に決めた。
  `review_article.py` の応答 JSON の `discard` フィールドがこれを担う
  （理由があれば `delete_article()` で削除）。
- **この discard 判定は校閲LLM任せで、見落とすことがある。** 2026-09-16、
  「Bluetooth5.4イヤホン」の記事が題名・本文で自ら「型番不明」
  「メーカー名や型番が確認できない」と書いていたのに `discard` が空のまま
  校閲を通過し、実際に公開されてしまった（サムネイルも汎用アイコンのまま）。
  再発防止として `review_article.py` に **機械的な安全網**（`ADMIT_UNIDENTIFIABLE`
  正規表現 / `looks_unidentifiable()`）を追加済み：本文が自分で
  「型番不明」「メーカー名や型番が確認できない」等と書いているのに
  discard が空なら、LLMの判定を待たずに強制的に破棄する。レビュー結果を
  使い回す（`already_reviewed`）経路でも毎回この保険をかける。
  同種の問題を見つけたら、まずこの安全網の正規表現が拾えているか確認し、
  拾えない言い回しなら `ADMIT_UNIDENTIFIABLE` を拡張する。
- ダークパターン・煽り表現・架空レビューなどの機械検査は `tools/check_text.py`
  と `review_article.py` の `scan()` 側の正規表現が共通の基準。

## 4. 外部連携・アフィリエイト経路

- 楽天市場 … 楽天アフィリエイト**直参加**（`content/site.json` の
  `affiliate.rakuten.affiliate_id`）。
- Yahoo!ショッピング … **バリューコマース**経由。単独の「Yahoo!アフィリエイト」
  サービスは終了済み。sid/pid が未取得の間はタグなしの通常リンクで出る。
- もしもアフィリエイト … 2026-09-04 に登録審査落ちのため**不使用**。
- Amazon … アソシエイト直リンク（`associate_tag`）。PA-API 5.0 の利用資格
  （180日以内に3件以上の適格販売）を得たら、セール商品のオリジナル
  ウィジェットを自作する方針（2026-09-05 決定、手本は gori.me の
  「ゴリセール」）。Amazon公式のバナー／画像リンクは2023年末に廃止済み。
  リンク組み立ては `build.py` の `affiliate_url()` 一箇所、IDは
  `content/site.json` の `affiliate` に入れる。
- Google AdSense … `ca-pub-4017242913861863` で広告ユニット3種を作成済みだが、
  2026-09-14時点で審査「準備中」が続いていたため一時的にスロットIDを空にして
  無効化中。スロットIDは記録済み（ディスプレイ `7363458968` →
  `ads.slots.top`、インフィード `5580438157` → `ads.slots.article_end`、
  記事内 `8070870122` → `ads.slots.article_mid`）。審査通過後は
  `content/site.json` の該当 `ads.slots.*.id` に書き戻して `build.py` を
  流すだけで再開できる（コード側の変更は不要）。

## 5. 進行中・予定されている変更

- monobase.site のドメインを **お名前.com から Cloudflare Registrar へ移管予定**
  （ユーザー決定、2026-09-08）。移管可能になるのは登録60日後＝
  **2026-10-23以降**。移管後、お名前.com のレンタルサーバー ベーシック
  （契約番号 2445508）を解約する。サーバーの唯一の用途は「契約中は
  monobase.site の更新料が無料」という無料ドメインのひも付けだけで、
  web/mysql/mail は未使用。MXも無く連絡先は monobase.site@gmail.com なので
  メールへの影響もない。

## 6. 作業の進め方（Claude Code 自身への注意）

- 数百行未満のファイル確認・特定シンボルの検索・単発の調査は、Explore/
  general-purpose サブエージェントに丸投げせず自分で直接 Read/Bash(grep) を
  使う。Claude Code サブスクの使用量（週次リミット）は同一アカウントの
  全セッションでプールされており、1回のサブエージェント呼び出しで
  数万トークン消費することがある。新規セッションで簡単な指示をしただけなのに
  使用量が70%消費されていた事故が、同時に動いていた別セッションの
  安易な委譲で起きている。サブエージェントは、複数箇所にまたがる広範な
  調査で委譲のオーバーヘッドに見合う場合だけに限定する。
