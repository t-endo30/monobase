/* ============================================================
   A8.net：参加中プログラムの広告コードを、一度に全部集める
   ------------------------------------------------------------
   「参加中プログラム」の一覧から、各案件の「広告リンク作成」を
   順にたどって、広告コードをまとめて拾います。72件でも1回で済みます。

   使い方
     1. A8にログインし、「プログラム管理 → 参加中プログラム」を開く
        （表示件数を 20件 → いちばん大きい数 に変えておくと速い）
     2. 開発者ツールのコンソール（⌥⌘I → Console）で `allow pasting`
        と打って Enter（Chromeの決まり。1回だけ）
     3. このファイルの中身を丸ごと貼って Enter
     4. 進み具合が出る。終わるとクリップボードに入る
     5. codes.txt に貼り付けて
        python3 tools/import_a8.py --csv programs.csv --codes codes.txt

   決まりごと
     ・A8のコードには手を触れません（並べて --- でつなぐだけ）
     ・自分のアカウントのページを、ログイン中のまま読むだけです
     ・相手に負荷をかけないよう、1ページごとに間をあけて読みます

   拾う数
     1案件からバナーを何種類も取ると、表示のたびにサイズが変わって
     記事の見た目が崩れます。既定では **1案件につき2件まで**、
     画像バナーを優先して拾います。全部欲しいときは MAX_PER_PROGRAM
     を 0（無制限）にしてください。
   ============================================================ */
(async function () {
  'use strict';

  var MAX_PER_PROGRAM = 2;   /* 1案件から拾う上限。0 で無制限 */
  var WAIT_MS = 400;         /* 1ページごとに空ける時間 */
  var MAX_PAGES = 400;       /* 読みに行くページ数の上限（安全弁） */

  var origin = location.origin;
  var here = new URL(location.href);
  var codes = [];
  var seenCode = {};
  var checked = 0;

  var isCode = function (v) { return /px\.a8\.net|rpx\.a8\.net|a8mat=/.test(v); };

  function get(url) {
    return fetch(url, { credentials: 'same-origin' })
      .then(function (r) { return r.text(); })
      .then(function (h) {
        return new DOMParser().parseFromString(h, 'text/html');
      });
  }

  function wait() {
    return new Promise(function (res) { setTimeout(res, WAIT_MS); });
  }

  /* --- 1. 一覧のページをすべて集める（ページ送りをたどる） --- */
  function pagerLinks(doc, base) {
    var out = [];
    var as = doc.querySelectorAll('a[href]');
    for (var i = 0; i < as.length; i++) {
      var u;
      try { u = new URL(as[i].getAttribute('href'), base); } catch (e) { continue; }
      if (u.origin !== origin) continue;
      if (u.pathname !== here.pathname) continue;
      if (u.search === new URL(base).search) continue;
      out.push(u.href.split('#')[0]);
    }
    return out;
  }

  /* --- 2. 「広告リンク作成」の行き先を集める --- */
  function linkPages(doc, base) {
    var out = [];
    var as = doc.querySelectorAll('a[href]');
    for (var i = 0; i < as.length; i++) {
      var a = as[i];
      var txt = (a.textContent || '').replace(/\s+/g, '');
      var href = a.getAttribute('href') || '';
      /* 文字で見分ける。画面が変わっても、URLの形でも拾えるようにする */
      var byText = /広告リンク(作成)?$/.test(txt);
      var byUrl  = /link|banner|material|creative/i.test(href)
                   && /mid=|program/i.test(href);
      if (!byText && !byUrl) continue;
      var u;
      try { u = new URL(href, base); } catch (e) { continue; }
      if (u.origin !== origin) continue;
      out.push(u.href.split('#')[0]);
    }
    return out;
  }

  /* --- 3. 1ページから広告コードを拾う --- */
  function collect(doc) {
    var found = [];
    var list = doc.querySelectorAll('textarea');
    for (var i = 0; i < list.length; i++) {
      var v = (list[i].value || list[i].textContent || '').trim();
      if (v && isCode(v) && found.indexOf(v) < 0) found.push(v);
    }
    /* 画像バナーを先に。テキストリンクだけの案件はそのまま残る */
    found.sort(function (a, b) {
      return (/<img/i.test(b) ? 1 : 0) - (/<img/i.test(a) ? 1 : 0);
    });
    if (MAX_PER_PROGRAM > 0) found = found.slice(0, MAX_PER_PROGRAM);
    var got = 0;
    found.forEach(function (v) {
      if (seenCode[v]) return;
      seenCode[v] = 1;
      codes.push(v);
      got++;
    });
    return got;
  }

  /* ===== 実行 ===== */
  var listPages = [location.href];
  var seenList = {}; seenList[location.href] = 1;
  pagerLinks(document, location.href).forEach(function (u) {
    if (!seenList[u]) { seenList[u] = 1; listPages.push(u); }
  });

  console.log('%cA8：一覧 ' + listPages.length + ' ページから案件を集めます',
    'color:#0a7;font-weight:bold');

  var targets = [];
  var seenTarget = {};
  for (var li = 0; li < listPages.length && li < 60; li++) {
    var doc = li === 0 ? document : await get(listPages[li]);
    if (li > 0) {
      /* あとから見つかったページ送りも足す */
      pagerLinks(doc, listPages[li]).forEach(function (u) {
        if (!seenList[u] && listPages.length < 60) {
          seenList[u] = 1; listPages.push(u);
        }
      });
      await wait();
    }
    linkPages(doc, listPages[li]).forEach(function (u) {
      if (!seenTarget[u]) { seenTarget[u] = 1; targets.push(u); }
    });
  }

  if (!targets.length) {
    console.log('%c「広告リンク作成」の行き先が見つかりませんでした。',
      'color:#c00;font-weight:bold');
    console.log('「プログラム管理 → 参加中プログラム」で実行してください。');
    console.log('それでも出ないときは、案件の「広告リンク作成」を手で開いて、'
      + 'そのURLを Claude に伝えてください（形を合わせます）。');
    return;
  }

  console.log('  案件 ' + targets.length + ' 件。広告コードを取りに行きます');

  for (var ti = 0; ti < targets.length && checked < MAX_PAGES; ti++) {
    try {
      var d = await get(targets[ti]);
      collect(d);
    } catch (e) { /* 読めないページは飛ばす */ }
    checked++;
    if (checked % 10 === 0) {
      console.log('  ' + checked + ' / ' + targets.length
        + ' 件、コード ' + codes.length + ' 件');
    }
    await wait();
  }

  if (!codes.length) {
    console.log('%c広告コードが見つかりませんでした。',
      'color:#c00;font-weight:bold');
    console.log('広告リンクのページが JavaScript で作られている可能性があります。'
      + '1件だけ手で開いて tools/a8-collect.js を試してください。');
    return;
  }

  var out = codes.join('\n---\n');
  function done() {
    console.log('%c' + codes.length + ' 件をコピーしました（案件 '
      + checked + ' 件を確認）',
      'color:#0a7;font-weight:bold;font-size:14px');
    console.log('codes.txt に貼り付けて、次を実行してください：');
    console.log('  python3 tools/import_a8.py --csv programs.csv --codes codes.txt');
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
