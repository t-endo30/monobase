/* ============================================================
   A8.net：一覧のページから、その先の広告リンクをまとめて集める
   ------------------------------------------------------------
   1件ずつ「広告リンク」を開いてコピーするのは、案件が増えると
   現実的ではありません。これは **いま開いているページ内のリンクを
   たどって**、その先にある広告コードをまとめて拾う道具です。

   使い方
     1. A8にログインし、「プログラム管理 → 参加中プログラム」を開く
     2. 開発者ツールのコンソール（⌥⌘I → Console）で `allow pasting` と
        打って Enter（Chromeの決まり。1回だけ）
     3. このファイルの中身を貼って Enter
     4. 進み具合がコンソールに出る。終わると件数が出て、
        クリップボードに入る

   決まりごと
     ・A8のコードには手を触れません（並べて --- でつなぐだけ）
     ・自分のアカウントのページを、ログイン中のまま読むだけです
     ・相手のサーバーに負荷をかけないよう、1件ずつ 0.4 秒あけて読みます
     ・既定では **1案件につき1つ** だけ拾います（全部欲しいときは
       下の ONE_PER_PAGE を false に）

   うまく拾えないとき
     A8の画面構成が変わっている可能性があります。コンソールに出る
     「確認したページ」を見て、拾えていないページのURLを教えてください。
   ============================================================ */
(async function () {
  'use strict';

  var ONE_PER_PAGE = true;   /* 1ページにつき1件だけ拾う（推奨） */
  var MAX_PAGES = 300;       /* 読みに行くページ数の上限 */
  var WAIT_MS = 400;         /* 1件ごとに空ける時間 */

  var origin = location.origin;
  var isCode = function (v) { return /px\.a8\.net|a8mat=/.test(v); };
  var codes = [];
  var seenCode = {};
  var seenUrl = {};
  var checked = 0;

  function add(v) {
    v = (v || '').trim();
    if (!v || !isCode(v) || seenCode[v]) return false;
    seenCode[v] = 1;
    codes.push(v);
    return true;
  }

  /* 文書の中の広告コードを拾う。取得した文書では textarea.value が
     入らないので、textContent も見る。 */
  function collect(doc) {
    var list = doc.querySelectorAll('textarea');
    var got = 0;
    for (var i = 0; i < list.length; i++) {
      var v = list[i].value || list[i].textContent || '';
      if (add(v)) {
        got++;
        if (ONE_PER_PAGE) break;
      }
    }
    return got;
  }

  /* たどる先を集める。同じサイトの中のリンクだけ。
     ログアウトや問い合わせなど、関係のないものは避ける。 */
  function links(doc, base) {
    var out = [];
    var as = doc.querySelectorAll('a[href]');
    for (var i = 0; i < as.length; i++) {
      var href = as[i].getAttribute('href');
      if (!href || href.charAt(0) === '#') continue;
      var u;
      try { u = new URL(href, base); } catch (e) { continue; }
      if (u.origin !== origin) continue;
      if (/logout|inquiry|help|faq|password|profile|payment/i.test(u.href)) continue;
      out.push(u.href.split('#')[0]);
    }
    return out;
  }

  /* いま開いているページから始める */
  collect(document);
  var queue = [];
  links(document, location.href).forEach(function (u) {
    if (!seenUrl[u]) { seenUrl[u] = 1; queue.push(u); }
  });

  console.log('%cA8：' + queue.length + ' 件のリンクをたどります',
    'color:#0a7;font-weight:bold');

  for (var qi = 0; qi < queue.length && checked < MAX_PAGES; qi++) {
    var url = queue[qi];
    try {
      var r = await fetch(url, { credentials: 'same-origin' });
      var html = await r.text();
      var doc = new DOMParser().parseFromString(html, 'text/html');
      var got = collect(doc);

      /* 広告コードがあったページは、ページ送りも追いかける
         （同じ道筋で、番号だけ違うリンク） */
      if (got) {
        var here = new URL(url);
        links(doc, url).forEach(function (u) {
          var v = new URL(u);
          if (v.pathname === here.pathname && v.search !== here.search
              && !seenUrl[u] && queue.length < MAX_PAGES) {
            seenUrl[u] = 1;
            queue.push(u);
          }
        });
      }
    } catch (e) { /* 読めないページは飛ばす */ }

    checked++;
    if (checked % 10 === 0) {
      console.log('  ' + checked + ' / ' + queue.length
        + ' ページ確認、コード ' + codes.length + ' 件');
    }
    await new Promise(function (res) { setTimeout(res, WAIT_MS); });
  }

  if (!codes.length) {
    console.log('%c広告コードが見つかりませんでした。',
      'color:#c00;font-weight:bold');
    console.log('「参加中プログラム」の一覧ページで実行してください。');
    return;
  }

  var out = codes.join('\n---\n');
  function done() {
    console.log('%c' + codes.length + ' 件をコピーしました（'
      + checked + ' ページ確認）',
      'color:#0a7;font-weight:bold;font-size:14px');
    console.log('codes.txt に貼り付けて、'
      + 'python3 tools/import_a8.py --csv <CSV> --codes codes.txt に渡してください。');
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(out).then(done, function () {
      console.log('クリップボードに入れられませんでした。下を選んでコピーしてください。');
      console.log(out);
    });
  } else {
    console.log(out);
  }
})();
