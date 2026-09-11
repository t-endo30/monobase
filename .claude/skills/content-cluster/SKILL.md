---
name: content-cluster
description: monobase.site に「悩み・比較・選び方」のコンテンツクラスター（ハブ記事＋関連記事＋既存レビューへの内部リンク）を追加する。商品名＋口コミ検索に依存せず、検索母数の大きいロングテール検索の入口を増やしたいときに使う。
---

# Content Cluster Playbook

MONOBASEで「商品単体の口コミ記事」だけに頼らず、悩み・比較・選び方の検索意図を
獲得するコンテンツクラスターを作るための手順。2026-09-11に冷蔵庫マットクラスター
（ハブ1本＋関連3本）を作った際の実際の手順と、そこで踏んだ地雷をまとめている。

## 0. 大原則

- **いきなり記事を書かない。** 必ず既存記事を先に調べ、同じ検索意図の記事が
  無いことを確認してから着手する（カニバリゼーション防止）。
- **架空の仕様・レビュー・体験談は書かない。** 確認できない数値は断定せず、
  「販売ページで確認してください」に逃がす。素材の一般的な性質（PVCは柔らかい、
  等）のような公知の知識と、特定商品の仕様（厚み・耐荷重など）は明確に分ける。
- **記事数を目的にしない。** 同じ検索意図なら1本に統合する（例：「いらない」
  「必要ない」「デメリット」「後悔」は1本にまとめる）。裏付け（実際にレビュー
  した商品）を超えて数だけ増やさない。

## 1. クラスターの見つけ方

```bash
python3 -c "
import json
arts = json.load(open('content/articles.json'))
pub = [a for a in arts if a.get('published')]
for a in sorted(pub, key=lambda x: (x['category'], x.get('sub',''), x['slug'])):
    print(f\"{a['category']:12} {a.get('sub','') or '-':12} {a['slug']:45} {a['title']}\")
"
```

同じ `category`/`sub` に**3本以上**の商品レビューが集まっていて、かつ
`category:"feature", sub:"guide"` のハブ記事が無い組み合わせが最有力候補。
既存記事のリード文・`pros`/`cons`/`sections` に書かれている事実（素材・サイズ
展開・用途）をそのまま使い回せるクラスターを優先する（新しい調査が要らない
ため、事実の断定リスクが下がる）。

`content/site.json` の `categories[].sub` で正式なsub一覧を確認できる。

## 2. 記事の型（`kind`）と使ってよいキー

`docs/review-rules.md` の「5-3 記事タイプに合わない枠」を必ず読む。ハブ・
関連記事は通常 `"kind": "guide"` にする（`build.py` の `kind_of()` が
`category=="feature"` なら自動で `"roundup"` 扱いにしてしまうため、
「選び方ガイド」として作るなら明示的に `"kind":"guide"` を入れて上書きする）。

| kind | 使ってよい主なキー |
|---|---|
| review | summary / rating / good_for / not_for / highlights / pros / cons / spec / sections / voices / faq / conclusion |
| roundup | summary / good_for / not_for / spec / sections / faq / conclusion / **products**（比較表） |
| guide | summary / good_for / not_for / spec / sections / faq / conclusion（+ next_problem / personal_note は使ってよい） |

`humidifier-buying-guide`（既存のハブ記事の実例）を必ずテンプレートとして
読むこと。フィールドの入れ方・トーンが分かる。

ハブ記事から個別レビューへ「比較表つき」でリンクしたい場合は `products[]`
に `{"name":..., "note":..., "slug": "<レビューのslug>"}` を入れる。これだけで
2つの効果が自動で出る：

1. ハブ側に比較表と「詳しいレビュー」リンクが出る（`product_table()`）
2. レビュー側に「この商品を比較した特集」という逆リンクが自動で出る（`featured_in()`）

## 3. 内部リンクの組み方（ここが今回のキモ）

MONOBASEには内部リンクの仕組みが最初から4つ実装されている。**手で`<a>`タグを
本文に書いてはいけない**（許可されたHTMLタグは `<strong>`/`<em>` のみ）。

| 仕組み | 使い方 | 効果 |
|---|---|---|
| `next_problem.items[].link_url/link_label` | ハブ・詳細記事の各JSONに明示的に書く。**既存73記事はどれも未使用だった**ので、これが「ハブ⇄詳細記事」を意図通りに繋ぐ主役 | 「◯◯を見る」という自然文アンカーのカードリンクが記事末尾に出る |
| `products[]` ⇄ `featured_in()` | ハブに`products[].slug`でレビューを指定するだけ | レビュー側に自動で逆リンクが出る（手動で触らない） |
| `related_map()` | 何もしなくても`category`/`sub`/`tags`の近さで自動選出 | 記事末尾の「関連記事」カルーセル。タグを揃えておくと同クラスターの記事同士が選ばれやすくなる |
| `link_past_articles()` | 本文中に他記事の`list_title`（末尾の「選び方」「ガイド」等は自動で削られる）を書くだけ | 初出の該当語だけ自動でリンク化（1記事あたり最大5本） |

手順：

1. クラスター内の全記事に共通タグ（商品ジャンル名など）を入れる → `related_map`が自動で拾う
2. ハブの`next_problem`に、各詳細記事へのカードリンクを3本前後用意する
3. 各詳細記事の`next_problem`にも、ハブと他の詳細記事へのリンクを入れる（双方向にする）
4. ハブに`products[]`で代表レビューを1件指定する → レビュー側は自動でリンクが付く
5. 既存レビュー記事側にも、ハブ・詳細記事への`next_problem`を1〜2件手動で追加する

## 4. 禁止表現チェック（★ここで一度ビルドが落ちた。必ず先にやる）

`docs/review-rules.md`の「絶対／必ず／誰でも」等の禁止語一覧は**ガイドライン**
だが、実は `tools/check_text.py` が **CIで機械的に文字列一致で落とす**。
`必ず確認してください`のような読者への助言表現でも容赦なく引っかかる。

執筆後、公開前に必ず実行：

```bash
python3 tools/check_text.py     # 禁止表現・タグの露出をチェック（NGは即fail）
python3 tools/check_articles.py # 文字数・JAN・記事タイプの整合性チェック
```

ローカルで先に潰しておく簡易スクリプト：

```python
import json
NG = ["絶対","必ず","確実に","保証します","間違いなく","100%",
      "誰でも","永久に","完治","業界No.1","日本一"]
arts = json.load(open("content/articles.json"))
for slug in ["<新規slug1>", "<新規slug2>"]:
    a = next(x for x in arts if x["slug"] == slug)
    hits = [w for w in NG if w in json.dumps(a, ensure_ascii=False)]
    print(slug, hits or "clean")
```

文字数下限は `tools/check_articles.py` の `body_chars()` で確認する
（公式仕様なし＝`rating`/`spec`を省いた記事は5,000字、それ以外は6,000字が下限）。

```python
import sys; sys.path.insert(0, "tools")
from check_articles import body_chars, MIN_CHARS_UNBACKED
```

## 5. ビルド確認（サンドボックス制約への対処）

この開発環境では、**Gitで管理済みの既存ファイルへの上書きがBashからブロック
される**（新規ファイルの作成は通る）。`python3 build.py`はほぼ全ファイルを
上書きするため、リポジトリ内で直接実行すると失敗する。

対処：リポジトリ全体をスクラッチ領域にコピーしてそこでビルドする。

```bash
SCRATCH=/path/to/scratchpad/buildcheck
rm -rf "$SCRATCH" && mkdir -p "$SCRATCH"
git ls-files -z | rsync -a --files-from=- -0 . "$SCRATCH"/
cp content/articles.json "$SCRATCH/content/articles.json"   # 作業中の変更を反映
cd "$SCRATCH" && python3 build.py && python3 tools/check_text.py && python3 tools/check_articles.py
```

ここで以下を確認する：

- ビルドがエラーなく完了し、`公開記事`本数が期待どおり増えているか
- `sitemap.xml`に新規記事のURLが入っているか（`grep <slug> sitemap.xml`）
- 内部リンクのリンク切れが無いか（`articles/*.html`と`index.html`のhrefを
  全部拾って、対象ファイルが存在するか突き合わせる）
- `category-<cat>-<sub>.html`に新規記事が一覧表示されているか

確認できたらスクラッチ領域は削除し、本物のリポジトリの
`content/articles.json`はEditツールで直接編集する（大きなJSONファイルでも
Editツールなら上書きできる。末尾に新記事を追記する場合は、ファイル末尾の
一意な文字列（例：`  }\n]`の直前の1記事分）をold_stringにして差し込む）。

**実際のHTML生成はローカルでは不要。** `main`にpushすると
`.github/workflows/deploy.yml`（表示名`Build & Check`）が`build.py`を実行し、
禁止表現チェックも走り、通れば生成したHTMLを`サイトを再生成（自動）`という
コミットで**push し返す**。ローカルのビルド確認はあくまで「pushする前に
致命的な間違いを潰す」ための保険。

## 6. push後の確認とサムネイルの注意

```bash
git push origin main
gh run list --limit 3       # Build & Check が success になるまで数十秒待つ
git fetch origin main && git log --oneline -3 origin/main   # 「サイトを再生成（自動）」コミットが乗る
git reset --hard origin/main  # ローカルをそれに追従させる（無関係な未コミット変更は事前にstash）
curl -s -o /dev/null -w "%{http_code}\n" -L https://monobase.site/articles/<slug>.html
```

**⚠️サムネイル未検証の既知の落とし穴**：`thumb`を空にすると
`assets/img/auto/<slug>.svg`が自動生成され、SVGファイル自体は正しく配信される
（`curl`で200・正しい中身を確認済み）。しかし2026-09-11時点で、
`category:"feature"`のハブ記事を含むこのクラスターでは**一覧タイルの
サムネイルが表示されない**という報告があり、原因を特定できないまま該当
クラスターを`published:false`に戻した。既存の`feature`カテゴリー記事
（`humidifier-buying-guide`）は自動SVGではなく`tools/make_images.py`で
生成した実写真調のJPGを`thumb`に設定しており、**自動SVGフォールバックの
描画パスが`feature`カテゴリーの記事で実際に目視検証されたことが無かった**
可能性が高い。

そのため、次にクラスターを作るときは：

1. 公開前に、ビルドしたHTMLをブラウザ（または `tools/check_layout.py` の
   ようなヘッドレスChrome検査）で**実際に開いてサムネイルが表示されるか
   目視確認する**（本メモリ：ヘッドレスChromeは幅500px未満のスマホ幅検証が
   効かないので、必要なら数値で裏を取る）
2. 可能なら `tools/make_images.py` で実写真調のアイキャッチを1枚用意し、
   `thumb`に設定してから公開する（自動SVGに頼らない）
3. 目視確認できない場合は `published:false`（下書き）のままpushし、
   確認が取れてから`published:true`にする2段階公開にする

## 7. 完了チェックリスト

- [ ] 既存記事を検索し、同じ検索意図のクラスターが無いことを確認した
- [ ] 各記事の`kind`が正しく、そのkindで許可されたキーだけを使っている
- [ ] `next_problem`でハブ⇄詳細記事の双方向リンクを張った
- [ ] タグをクラスター内で揃え、`related_map`にも拾われるようにした
- [ ] `tools/check_text.py` / `tools/check_articles.py` を通した
- [ ] スクラッチ領域でビルドし、リンク切れ・sitemap反映を確認した
- [ ] push後、`Build & Check`がsuccessになったことを`gh run list`で確認した
- [ ] 本番URLでタイトル・サムネイルを目視確認してから`published:true`にした
- [ ] `SEO_IMPROVEMENT_REPORT.md`（または同等のログ）に変更内容を記録した
