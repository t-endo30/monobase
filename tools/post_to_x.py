#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新しく公開した記事を X（旧Twitter）に投稿する。

  $ python3 tools/post_to_x.py            # 本日公開の未投稿記事を投稿
  $ python3 tools/post_to_x.py --dry-run   # 投稿せず、内容だけ表示

対象
  content/articles.json の中で、
    ・published: true
    ・date が「今日」
    ・x_posted がまだ立っていない
  の記事だけを投稿する。過去の記事を一度に大量投稿しないための条件。
  投稿できたら、その記事に x_posted: true を立てて articles.json に書き戻す
  （.github/workflows/deploy.yml の「Commit regenerated site」でコミットされる）。

認証（OAuth 1.0a・User Context）
  以下4つを GitHub の Settings → Secrets and variables → Actions に登録し、
  ワークフロー側で環境変数として渡す。どれか欠けていれば何もせず終了する
  （フォークや手元での実行でエラーにしないため）。
    X_API_KEY            … API Key（Consumer Key）
    X_API_SECRET         … API Key Secret（Consumer Secret）
    X_ACCESS_TOKEN        … Access Token
    X_ACCESS_TOKEN_SECRET … Access Token Secret

  Developer Portal 側で「Read and Write」権限にしたうえで発行した
  Access Token でないと、投稿（POST /2/tweets）は 403 になる。
  外部ライブラリは使わず、標準ライブラリだけで OAuth 1.0a 署名を組み立てる
  （CI環境に pip install の手間を増やさないため）。
"""
import argparse, base64, datetime, hashlib, hmac, io, json, os, random
import string, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A_PATH = os.path.join(ROOT, "content", "articles.json")
S_PATH = os.path.join(ROOT, "content", "site.json")
ENDPOINT = "https://api.twitter.com/2/tweets"

ENV_KEYS = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")


def _nonce(n=32):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(n))


def _sign(method, url, params, consumer_secret, token_secret):
    """OAuth 1.0a HMAC-SHA1 署名を作る。"""
    base = "&".join(
        urllib.parse.quote(x, safe="")
        for x in (method, url, "&".join(
            f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
            for k, v in sorted(params.items())))
    )
    key = f"{urllib.parse.quote(consumer_secret, safe='')}&{urllib.parse.quote(token_secret, safe='')}"
    sig = hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()
    return base64.b64encode(sig).decode()


def post_tweet(text, api_key, api_secret, access_token, access_secret):
    """POST /2/tweets を OAuth 1.0a で叩く。標準ライブラリのみで完結させる。"""
    oauth = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": _nonce(),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }
    oauth["oauth_signature"] = _sign("POST", ENDPOINT, oauth, api_secret, access_secret)
    header = "OAuth " + ", ".join(
        f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
        for k, v in sorted(oauth.items()))

    body = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
        "Authorization": header,
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


DISCLOSURE = "#PR"  # アフィリエイトリンクを含む記事への投稿だと分かるようにする


def build_text(a, base_url):
    """280字（Xの上限）に収まるよう、タイトル・一言・URL・開示表記を組み立てる。
       日本語も1文字=1カウントなので、単純に文字数で切ればよい。
       #PR は、リンク先の記事にアフィリエイトリンクを含むことを示す開示。
       投稿そのものにはAmazonの商品リンクを直接貼らない（自サイトの記事
       ページだけを貼る）方針とあわせて、規約・ステマ規制の両方に配慮する。"""
    title = a.get("list_title") or a["title"]
    url = f"{base_url}/articles/{a['slug']}.html"
    excerpt = a.get("excerpt", "")
    # URL・開示表記・改行ぶんを引いた残りに、タイトル→一言の順で詰める
    tail = f"\n{url}\n{DISCLOSURE}"
    budget = 280 - len(tail)
    body = title
    if excerpt:
        candidate = f"{title}\n{excerpt}"
        if len(candidate) <= budget:
            body = candidate
        else:
            keep = max(0, budget - len(title) - 2)
            if keep > 4:
                body = f"{title}\n{excerpt[:keep - 1]}…"
    if len(body) > budget:
        body = body[:max(0, budget - 1)] + "…"
    return f"{body}{tail}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="投稿せず、内容だけ表示する")
    ap.add_argument("--test", action="store_true",
                    help="articles.json を見ず、接続確認用の投稿を1件だけ行う")
    args = ap.parse_args()

    creds = {k: os.environ.get(k, "").strip() for k in ENV_KEYS}
    if not args.dry_run and not all(creds.values()):
        missing = [k for k, v in creds.items() if not v]
        print(f"::warning::X投稿用の環境変数が未設定のため、投稿をスキップします: {', '.join(missing)}")
        return 0

    if args.test:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        text = f"【接続確認】モノベースの自動投稿テストです（{now}）。この投稿は削除して構いません。"
        print(text)
        if args.dry_run:
            return 0
        try:
            res = post_tweet(text, creds["X_API_KEY"], creds["X_API_SECRET"],
                             creds["X_ACCESS_TOKEN"], creds["X_ACCESS_TOKEN_SECRET"])
            print(f"→ 投稿に成功しました: {res}")
        except Exception as e:
            print(f"::error::テスト投稿に失敗しました: {e}")
            return 1
        return 0

    site = json.load(io.open(S_PATH, encoding="utf-8"))
    base_url = site["base_url"].rstrip("/")
    arts = json.load(io.open(A_PATH, encoding="utf-8"))

    today = datetime.date.today().isoformat()
    targets = [a for a in arts
               if a.get("published") and a.get("date") == today and not a.get("x_posted")]

    if not targets:
        print("本日公開・未投稿の記事はありません。")
        return 0

    changed = False
    for a in targets:
        text = build_text(a, base_url)
        print(f"── {a['slug']} ──\n{text}\n")
        if args.dry_run:
            continue
        try:
            post_tweet(text, creds["X_API_KEY"], creds["X_API_SECRET"],
                      creds["X_ACCESS_TOKEN"], creds["X_ACCESS_TOKEN_SECRET"])
            a["x_posted"] = True
            changed = True
            print(f"  → 投稿しました")
        except Exception as e:
            # 1本の失敗でCI全体を止めない。次回の実行でまた対象になる。
            print(f"::warning::{a['slug']} のX投稿に失敗しました: {e}")

    if changed:
        io.open(A_PATH, "w", encoding="utf-8").write(
            json.dumps(arts, ensure_ascii=False, indent=2) + "\n")
        print(f"articles.json を更新しました（x_posted）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
