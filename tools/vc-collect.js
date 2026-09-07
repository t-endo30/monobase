/* ============================================================
   バリューコマースの広告コードを、そのページからまとめて取り出す
   ------------------------------------------------------------
   VCも、広告コードは画面上の <textarea>（またはコード表示欄）に
   入っている。それを拾ってクリップボードへ入れる。

   コードには手を触れない。並べて「---」の行でつなぐだけ。
   ページの見出し（プログラム名）も先頭に添えて、あとで
   tools/import_vc.py がどの案件のコードか分かるようにする。

   使い方
     1. バリューコマースにログインし、提携中のプログラムから
        「広告作成」（バナー・テキスト広告の作成）ページを開く
     2. ブラウザの開発者ツールを開く（Chrome：⌥⌘I → Console）
     3. このファイルの中身を丸ごと貼って Enter
     4. 「◯件をコピーしました」と出たら、テキストファイルに
        追記で貼り付ける（1ページ実行するごとに追記していく）
     5. プログラムの数ぶん、1〜4を繰り返す
     6. できたファイルを import_vc.py --codes に渡す

   ※ 1ページぶんずつ拾う。複数のバナーサイズが並ぶページでは、
      見えている分だけ全部拾う（大きさはあとで実際の画像を取得して判別する）。
   ============================================================ */
(function () {
  'use strict';

  var HOST = /valuecommerce\.com/i;

  /* 広告コードが入っている場所を、textarea → input → コードらしい
     <pre>/<code> → ページ全体のHTML の順で探す。 */
  function fromFields() {
    var els = document.querySelectorAll('textarea, input[type="text"], input:not([type])');
    return Array.prototype.map.call(els, function (t) {
      return (t.value || '').trim();
    }).filter(function (v) { return v && HOST.test(v); });
  }

  function fromBlocks() {
    var els = document.querySelectorAll('pre, code, .code, .tag, .html, [class*="code"]');
    return Array.prototype.map.call(els, function (t) {
      return (t.textContent || '').trim();
    }).filter(function (v) { return v && HOST.test(v); });
  }

  /* 欄が見つからないページ用の最後の手段。href/src に
     valuecommerce.com を含む要素を、その親ごと拾う。
     jsbanner（<script>）は noscript の中の <a><img> を優先する
     （静的サイトでは document.write を使う script 版を貼れないため）。 */
  function fromAnchors() {
    var out = [];
    document.querySelectorAll('noscript').forEach(function (ns) {
      var html = ns.textContent || ns.innerHTML || '';
      if (HOST.test(html)) out.push(html.trim());
    });
    if (out.length) return out;
    document.querySelectorAll('a[href*="valuecommerce.com"]').forEach(function (a) {
      if (HOST.test(a.href)) out.push(a.outerHTML);
    });
    return out;
  }

  var codes = fromFields();
  if (!codes.length) codes = fromBlocks();
  if (!codes.length) codes = fromAnchors();

  var seen = {};
  codes = codes.filter(function (v) {
    if (seen[v]) return false;
    seen[v] = 1;
    return true;
  });

  if (!codes.length) {
    console.log('%c広告コードが見つかりませんでした。',
      'color:#c00;font-weight:bold');
    console.log('「広告作成」（バナー・テキスト広告）のページで実行してください。');
    return;
  }

  /* プログラム名らしい見出しを拾う。パンくずや h1 の文言をそのまま使う。
     見つからなければページの title をそのまま使う。 */
  function guessName() {
    var h1 = document.querySelector('h1');
    if (h1 && h1.textContent.trim()) return h1.textContent.trim();
    return (document.title || '').trim();
  }

  var label = '===' + guessName() + '===';
  var out = label + '\n' + codes.join('\n---\n');

  function done() {
    console.log('%c' + codes.length + ' 件をコピーしました（' + guessName() + '）',
      'color:#0a7;font-weight:bold;font-size:14px');
    console.log('テキストファイルに追記してください。次のプログラムのページでも同じ手順を。');
  }

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(out).then(done, function () {
      console.log('クリップボードに入れられませんでした。下の文字列を選んでコピーしてください。');
      console.log(out);
    });
  } else {
    console.log('下の文字列を選んでコピーしてください。');
    console.log(out);
  }
})();
