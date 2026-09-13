#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""バリューコマースの「広告素材から探す」一覧を自動で巡回し、
バナー広告コードを一括で取ってくる。

いままでは tools/vc-collect.js を、提携している案件のページを1つずつ
開いてコンソールで実行する必要があった（案件の数だけ繰り返す）。
これは、その「広告作成」ボタンを押す作業そのものを自動化する。

しくみ
  一覧の1枠1枠に「広告作成」ボタンがあり（id="createAdBtn_<adOid>"）、
  押すとその枠の中に「取得済み広告コード」欄が増えてコードが出る
  （別ページ・別タブへは飛ばない）。なので、
    1. いまのページに出ている未処理の adOid を見つけて押す
    2. 出てきたコードを拾う
    3. そのページの分を全部押し終えたら、次のページへ進む
  を繰り返す。adOid は一覧の並び順が変わっても枠ごとに固定なので、
  「一番上のボタンを押し続ける」ような雑なやり方はしない
  （同じ枠を何度も押すと、そのたびに別のトラッキングコードが増える
  だけで、案件としては増えないため。実際に最初の版でこれをやって
  しまい、1つの広告を1885回押していたことがあった）。

準備（最初の1回だけ）
  1. 自動操作の専用に、バリューコマース用のChromeプロフィールを作る
     （ふだん使っているウィンドウには触れない）
       $ open -na "Google Chrome" --args \
           --remote-debugging-port=9222 \
           --user-data-dir="$HOME/.vc-collect-chrome-profile"
  2. 開いたChromeでバリューコマースに普通にログインする
     （このプロフィールにログイン状態が残るので、次回以降は不要）

使い方
  1. 上のChromeで「広告」→「プログラム検索」→「広告素材から探す」を開く
     （絞り込みたい条件があれば先にそこで検索しておく。何もしなければ
      全案件のバナーが対象になる）
  2. 同じChromeを --remote-debugging-port=9222 のまま開いた状態で：
       $ python3 tools/collect_vc_ads.py
     はじめは --limit 5 を付けて、少ない件数で試すとよい。
  3. できた tools/_vc/collected_codes.txt を、いつも通り
       $ python3 tools/import_vc.py --codes tools/_vc/collected_codes.txt
     に渡す（--csv や --apply は今まで通り）。

  押した adOid は tools/_vc/collected_seen.json に記録される。
  取りこぼしたり止まったりしても、そのままもう一度実行すれば
  続きから（押していない枠だけ）再開する。
"""
import argparse, html, json, os, re, sys, time
from urllib.parse import urljoin

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DEFAULT = os.path.join(ROOT, "tools", "_vc", "collected_codes.txt")
SEEN_DEFAULT = os.path.join(ROOT, "tools", "_vc", "collected_seen.json")

CODE_BLOCK = re.compile(
    r'<script[^>]*jsbanner[^>]*>.*?</script>\s*<noscript>.*?</noscript>',
    re.I | re.S)
SID_PID = re.compile(r"[?&]sid=(\d+)[^\"'&]*&pid=(\d+)", re.I)
BTN_ID = re.compile(r'id="createAdBtn_(\d+)"')
NEXT_PAGE = re.compile(r'data-ga-label="next"[^>]*>|aria-label="Next"[^>]*>')
PAGE_HREF = re.compile(r'href="([^"]*?/ad/selectAdLink/page\?page=\d+)"[^>]*data-ga-label="next"')
LAST_PAGE = re.compile(r'href="[^"]*?page=(\d+)"[^>]*aria-label="Last"')
TOTAL_COUNT = re.compile(r'/\s*([\d,]+)\s*件中')
LIMIT_DATA = re.compile(r'[?&]limitData=(\d+)')


def load_seen(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(path, seen):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f)


def extract_codes(html_text):
    """いま画面に出ている広告コードを全部拾う（すでに前回までに
       作成済みで、押さなくても表示されているものも含む）。
       広告スペース名は id="adproName_<pid>" から拾う。"""
    text = html.unescape(html_text)
    names = dict(re.findall(r'id="adproName_(\d+)"[^>]*>([^<]+)<', text))
    out = []
    for m in CODE_BLOCK.finditer(text):
        code = m.group(0).strip()
        pm = SID_PID.search(code)
        pid = pm.group(2) if pm else None
        out.append({"pid": pid, "name": names.get(pid, "").strip(), "code": code})
    return out


def find_next_page_url(html_text, current_url):
    m = PAGE_HREF.search(html_text)
    if not m:
        return None
    return urljoin(current_url, m.group(1))


def load_existing(out_path):
    """前回までに書き出した tools/_vc/collected_codes.txt を読み込む。
       再ログインなどで中断・再実行しても、前回分を上書きで
       消してしまわないようにするため。"""
    collected = {}
    if not os.path.exists(out_path):
        return collected
    text = open(out_path, encoding="utf-8").read()
    parts = re.split(r"(?m)^===(.*)===\s*$", text)
    for i in range(1, len(parts), 2):
        name = parts[i].strip()
        body = parts[i + 1] if i + 1 < len(parts) else ""
        code = body.split("---", 1)[0].strip()
        if not code:
            continue
        pm = SID_PID.search(code)
        pid = pm.group(2) if pm else None
        base = re.sub(r"_\d+$", "", name) if name else (pid or code[:40])
        collected[base] = {"pid": pid, "name": name, "code": code}
    return collected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cdp", default="http://localhost:9222",
                    help="接続先Chromeのリモートデバッグアドレス")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--seen", default=SEEN_DEFAULT,
                    help="押した adOid の記録先（再実行時に続きから）")
    ap.add_argument("--limit", type=int, default=0,
                    help="試しに最初のN件だけ押して止める（0で無制限）")
    ap.add_argument("--max-pages", type=int, default=200, help="暴走よけの上限")
    ap.add_argument("--pause", type=float, default=1.0,
                    help="1回押すごとの待ち時間（秒）。VCへの負荷を抑える")
    ap.add_argument("--fresh", action="store_true",
                    help="押した記録を無視して、いま見えている分をもう一度拾い直す")
    ap.add_argument("--no-reset-page", action="store_true",
                    help="開始前に1ページ目へ戻るのをやめる（いま見えている"
                    "ページからそのまま始める）")
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit(
            "playwright が入っていません。\n"
            "  $ pip3 install --user --break-system-packages playwright\n"
            "を先に実行してください（既に開いているChromeにつなぐだけなので\n"
            "playwright install は不要）")

    seen = set() if args.fresh else load_seen(args.seen)
    collected = {} if args.fresh else load_existing(args.out)  # base名 -> {...}
    if collected:
        print(f"前回までの収集分 {len(collected)} 件を引き継ぎます。")

    def connect():
        """VCのタブに繋ぎ直す。一度確立したCDP接続は、ナビゲーション中に
           コマ落ちすると Page オブジェクトごと無効になることがあるので、
           そのたびに繋ぎ直せるようにしておく。"""
        browser = pw.chromium.connect_over_cdp(args.cdp)
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        for p in ctx.pages:
            if "valuecommerce" in p.url:
                return p
        raise SystemExit(
            "バリューコマースのタブが見つかりませんでした。\n"
            "案内のChromeで「広告素材から探す」の一覧ページを開いてから"
            "実行してください。")

    with sync_playwright() as pw:
        try:
            page = connect()
        except Exception as ex:                                # noqa: BLE001
            raise SystemExit(
                f"{args.cdp} に接続できませんでした：{ex}\n"
                "先に案内の通り、--remote-debugging-port=9222 を付けて\n"
                "Chromeを開いているか確かめてください。")

        print(f"接続しました：{page.url}")

        # ページ番号を正しく数えるため、必ず1ページ目から始める
        # （繋ぎ直した先が途中のページだと、内部の数え方と実際のページ番号が
        # ずれてしまうため）。検索条件はセッション側に残っているはずなので、
        # ?page=1 に行くだけで1ページ目に戻れる。
        if not args.no_reset_page:
            m = re.search(r"(.*/ad/selectAdLink)(?:/page)?", page.url)
            base = m.group(1) if m else "https://aff.valuecommerce.ne.jp/ad/selectAdLink"
            page.goto(f"{base}/page?page=1", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)

        def remember(c):
            """同じ枠を昔の不具合や再実行で何度も押してしまっていても、
               広告スペース名（末尾の連番を除く）が同じなら1件に
               まとめる。連番はVC側が自動でつけるトラッキングコード
               ごとの番号で、案件が増えたわけではないため。"""
            base = re.sub(r"_\d+$", "", c["name"]) if c["name"] else (c["pid"] or "")
            if base and base not in collected:
                collected[base] = c

        def with_retry(fn, what, retries=5):
            """Playwrightの接続が一瞬切れて Target...Closed になっても、
               繋ぎ直して同じ操作をやり直す。何度もダメなら諦めて投げる。"""
            nonlocal page
            for attempt in range(retries):
                try:
                    return fn()
                except Exception as ex:                        # noqa: BLE001
                    print(f"  ! {what}に失敗（{attempt + 1}回目）：{ex}")
                    if attempt == retries - 1:
                        raise
                    time.sleep(5)
                    try:
                        page = connect()
                    except Exception:                           # noqa: BLE001
                        pass
            return None

        def check_logged_in(text):
            if "ログインしてください" in text or "<title>ログイン</title>" in text:
                raise SystemExit(
                    "バリューコマースからログアウトさせられていました"
                    "（無操作が続くと自動ログアウトする仕様のようです）。\n"
                    "案内のChromeでもう一度ログインし、「広告素材から探す」の"
                    "一覧を開き直してから、もう一度実行してください。\n"
                    "（押した分の記録は残っているので、続きから再開します）")

        clicks = 0
        stop = False
        last_page = None
        for page_no in range(1, args.max_pages + 1):
            text = html.unescape(with_retry(page.content, "ページ読み取り"))
            check_logged_in(text)

            if last_page is None:
                mt = TOTAL_COUNT.search(text)
                ml = LIMIT_DATA.search(page.url)
                if mt:
                    total = int(mt.group(1).replace(",", ""))
                    per_page = int(ml.group(1)) if ml else 20
                    last_page = -(-total // per_page)  # 切り上げ
                    print(f"（全 {total} 件、1ページ {per_page} 件 → "
                          f"全 {last_page} ページあるようです）")
            if last_page and page_no > last_page:
                print(f"最後のページ（{last_page}）を超えたので、ここで終わりです"
                      "（ページ送りのリンク自体は残っていることがあるため、"
                      "件数から判断しました）。")
                break

            adoids = list(dict.fromkeys(BTN_ID.findall(text)))  # 出現順・重複なし

            # 繋ぎ直した直後などは、まだ描画が終わっていないだけで
            # 本当は0件ではないことがある。念のため読み直してから決める。
            for _ in range(2):
                if adoids:
                    break
                time.sleep(2)

                def reload_it():
                    page.reload(timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=15000)

                with_retry(reload_it, "再読み込み")
                text = html.unescape(with_retry(page.content, "ページ読み取り"))
                check_logged_in(text)
                adoids = list(dict.fromkeys(BTN_ID.findall(text)))

            for c in extract_codes(text):
                if c["pid"]:
                    remember(c)

            todo = [a for a in adoids if a not in seen]
            print(f"[ページ{page_no}] 枠 {len(adoids)} 件中、未処理 {len(todo)} 件")

            for adoid in todo:
                if args.limit and clicks >= args.limit:
                    stop = True
                    break

                def click_it(adoid=adoid):
                    page.locator(f"#createAdBtn_{adoid}").click()
                    page.wait_for_load_state("networkidle", timeout=15000)

                try:
                    with_retry(click_it, f"adOid {adoid} のクリック")
                except Exception:                               # noqa: BLE001
                    # ここでは既読にしない。次回の実行でもう一度試せるように
                    # しておく（既読にすると、失敗した分を二度と拾えなくなる）。
                    print(f"  ! adOid {adoid} は失敗のため今回は諦めます"
                          "（次回の実行で再挑戦します）")
                    continue
                seen.add(adoid)
                clicks += 1
                time.sleep(args.pause)
                for c in extract_codes(with_retry(page.content, "ページ読み取り")):
                    if c["pid"]:
                        remember(c)
                print(f"  ✓ adOid {adoid} を押しました（累計クリック {clicks} 件、"
                      f"収集 {len(collected)} 件）")

            save_seen(args.seen, seen)
            write_out(args.out, collected)

            if stop:
                print(f"--limit {args.limit} 件に達したので止めます。")
                break

            next_url = find_next_page_url(text, page.url)
            if not next_url:
                print("次のページが無いので、ここで終わりです。")
                break

            def goto_it(next_url=next_url):
                page.goto(next_url, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)

            with_retry(goto_it, "ページ送り")
            time.sleep(args.pause)

    print(f"\n{clicks} 回押して、コード {len(collected)} 件を書き出しました：{args.out}")
    print("次は：\n"
          f"  $ python3 tools/import_vc.py --codes {os.path.relpath(args.out, ROOT)}")


def write_out(out_path, collected):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for c in collected.values():
            f.write(f"==={c['name']}===\n{c['code']}\n---\n")


if __name__ == "__main__":
    sys.exit(main())
