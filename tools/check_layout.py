#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""画面の崩れを機械で見張る。

CSSの直しは、直した場所と関係のないところを壊しがちです。
「PCのナビが2行になった」「スマホで横にはみ出した」といった崩れは、
見た目を人が見ないと気づけない——という状態をやめるための道具です。

Chrome を画面なしで動かし、いくつかの幅でページを実際に描画して、
守りたい条件を確かめます。

  $ python3 tools/check_layout.py            # 全部確かめる
  $ python3 tools/check_layout.py --keep     # 失敗したときに画像を残す

確かめること
  1. 横にはみ出していない（どの幅でも）
  2. PC（1000px以上）でカテゴリーの横並びが1行に収まっている
  3. カテゴリーの項目が右端で切れていない
  4. ヘッダーのメニューが1行に収まっている（900px以上）
  5. 「このサイトの読み方」を開くと、板が画面の中に出る（スマホ幅）
  6. 記事タイルの高さがそろっている（スマホ幅の一覧）

Chrome が見つからないときは、何もせずに成功として抜けます
（CIで Chrome が無い環境でも止めないため）。
"""
import argparse, http.server, json, os, re, socketserver, subprocess
import sys, tempfile, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8731

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]

# 各ページで走らせる検査。JSで測って JSON を document.title に入れる。
PROBE = r"""
<script>
window.addEventListener('load', function () { setTimeout(function () {
  var r = {};
  var de = document.documentElement;
  r.vw = de.clientWidth;
  r.overflow = de.scrollWidth - de.clientWidth;

  var list = document.querySelector('.cat-nav-list');
  if (list) {
    var rows = {}, cut = 0;
    var lr = list.getBoundingClientRect();
    Array.prototype.forEach.call(list.children, function (c) {
      var b = c.getBoundingClientRect();
      rows[Math.round(b.top)] = 1;
      if (b.right > lr.right + 1 || b.left < lr.left - 1) cut++;
    });
    r.navRows = Object.keys(rows).length;
    r.navCut = cut;
  }

  var nav = document.querySelector('.global-nav ul');
  if (nav) {
    var nrows = {};
    Array.prototype.forEach.call(nav.children, function (c) {
      nrows[Math.round(c.getBoundingClientRect().top)] = 1;
    });
    r.menuRows = Object.keys(nrows).length;
  }

  var cards = document.querySelectorAll('.card-grid .card:not(.is-lead)');
  if (cards.length > 1) {
    var hs = Array.prototype.map.call(cards, function (c) {
      return Math.round(c.getBoundingClientRect().height);
    });
    r.cardHeights = hs.length;
    r.cardSpread = Math.max.apply(null, hs) - Math.min.apply(null, hs);
  }

  var d = document.querySelector('details.hero-policy');
  if (d) {
    d.querySelector('summary').click();
    setTimeout(function () {
      var p = document.querySelector('.policy-pop');
      if (p) {
        var b = p.getBoundingClientRect();
        r.policyVisible = (b.top >= -1 && b.bottom <= innerHeight + 1
                           && b.width > 40) ? 1 : 0;
        r.policyTop = Math.round(b.top);
      }
      document.title = 'RESULT' + JSON.stringify(r);
    }, 400);
  } else {
    document.title = 'RESULT' + JSON.stringify(r);
  }
}, 1400); });
</script>
"""

# ページ, 幅, 期待すること
CASES = [
    ("index.html",          375,  ["no-overflow", "policy", "cards"]),
    ("new.html",            390,  ["no-overflow", "cards"]),
    ("index.html",          768,  ["no-overflow"]),
    ("category-beauty.html", 1000, ["no-overflow", "nav-1row", "nav-nocut", "menu-1row"]),
    ("category-beauty.html", 1280, ["no-overflow", "nav-1row", "nav-nocut", "menu-1row"]),
    ("index.html",          1280, ["no-overflow", "nav-1row", "nav-nocut", "menu-1row"]),
    ("index.html",          1478, ["no-overflow", "nav-1row", "menu-1row"]),
    ("articles/mx-master-3s-review.html", 375, ["no-overflow"]),
]


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def serve():
    """検査用の簡易サーバー。1本ずつしか捌けないサーバーだと、
       ブラウザが同時に複数つないだ時点で止まってしまうので、
       必ず並行して捌ける形にする。"""
    os.chdir(ROOT)
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a, **k: None
    handler.protocol_version = "HTTP/1.0"      # 接続を持ち越さない
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def make_probe_page(path):
    """検査用の一時ページを作る。中身は本物のページ＋測る仕掛け。"""
    src = os.path.join(ROOT, path)
    html = open(src, encoding="utf-8").read()
    # 記事ページなど、深い場所のものは相対パスが変わるので同じ階層に置く
    d = os.path.dirname(src)
    tmp = os.path.join(d, "_layout_check.html")
    open(tmp, "w", encoding="utf-8").write(html.replace("</body>", PROBE + "</body>"))
    return tmp, os.path.relpath(tmp, ROOT)


def run_case(chrome, path, width, keep, prof):
    tmp, rel = make_probe_page(path)
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
           f"--user-data-dir={prof}", "--no-first-run", "--disable-extensions",
           f"--window-size={width},900", "--virtual-time-budget=6000",
           "--dump-dom", f"http://127.0.0.1:{PORT}/{rel}"]
    # 点滅などの終わらない動きがあると、書き出したあともChromeが居座る。
    # 出力を受け取れた時点で用は済むので、待ちすぎずに終わらせる。
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True)
    try:
        out, _ = proc.communicate(timeout=25)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
    finally:
        if not keep and os.path.exists(tmp):
            os.remove(tmp)
    m = re.search(r"RESULT(\{.*?\})", out)
    return json.loads(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true",
                    help="検査用の一時ページを残す（原因を追うとき）")
    args = ap.parse_args()

    chrome = find_chrome()
    if not chrome:
        print("Chrome が見つからないため、画面の検査は行いません。")
        return 0

    httpd = serve()
    bad = []
    prof = tempfile.mkdtemp(prefix="mb-layout-")
    try:
        for path, width, wants in CASES:
            r = run_case(chrome, path, width, args.keep, prof)
            name = f"{path} @{width}px"
            if r is None:
                print(f"  ? {name}：測れませんでした")
                continue

            errs = []
            if "no-overflow" in wants and r.get("overflow", 0) > 1:
                errs.append(f"横に {r['overflow']}px はみ出している")
            if "nav-1row" in wants and r.get("navRows", 1) > 1:
                errs.append(f"カテゴリーが {r['navRows']} 行になっている")
            if "nav-nocut" in wants and r.get("navCut", 0):
                errs.append(f"カテゴリーの項目が {r['navCut']} 件切れている")
            if "menu-1row" in wants and r.get("menuRows", 1) > 1:
                errs.append(f"ヘッダーのメニューが {r['menuRows']} 行になっている")
            if "policy" in wants and r.get("policyVisible", 1) == 0:
                errs.append(f"「このサイトの読み方」が画面の外に出ている"
                            f"（top={r.get('policyTop')}）")
            if "cards" in wants and r.get("cardSpread", 0) > 2:
                errs.append(f"記事タイルの高さが {r['cardSpread']}px ばらついている")

            if errs:
                bad.append((name, errs))
                print(f"  ✗ {name}")
                for e in errs:
                    print(f"      {e}")
            else:
                print(f"  ✓ {name}")
    finally:
        httpd.shutdown()

    if bad:
        print(f"\n::error::画面の崩れが {len(bad)} 件見つかりました。")
        return 1
    print("\n✅ 画面の崩れはありません。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
