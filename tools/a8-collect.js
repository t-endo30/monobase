/* ============================================================
   A8.net の広告リンクを、そのページからまとめて取り出す
   ------------------------------------------------------------
   A8には広告コードを配るAPIがありません。1件ずつコピーするしかない
   ように見えますが、コードは画面上の <textarea> に入っているので、
   それを全部拾ってクリップボードへ入れれば一度で済みます。

   コードには手を触れません。並べて「---」の行でつなぐだけです。

   使い方
     1. A8にログインし、「プログラム管理 → 参加中プログラム」から
        取りたい案件の「広告リンク」を開く
     2. ブラウザの開発者ツールを開く（Chrome：⌥⌘I → Console）
     3. このファイルの中身を丸ごと貼って Enter
     4. 「◯件をコピーしました」と出たら、管理画面の
        「サイト設定 → ASPの広告 → 広告リンクのコード」に貼り付ける

   ※ 1ページぶんずつ拾います。ページを送って、そのつど実行してください。
   ※ 画像バナーだけ欲しい／テキストリンクだけ欲しいときは、
      A8側の絞り込み（サイズ・種類）をかけてから実行してください。
   ============================================================ */
(function () {
  'use strict';

  /* 広告コードが入っているのは textarea。中身で見分ける。 */
  var codes = Array.prototype.map
    .call(document.querySelectorAll('textarea'), function (t) {
      return (t.value || '').trim();
    })
    .filter(function (v) {
      return v && /px\.a8\.net|a8mat=/.test(v);
    });

  /* 同じコードが複数の欄に出ていることがあるので、重複を落とす */
  var seen = {};
  codes = codes.filter(function (v) {
    if (seen[v]) return false;
    seen[v] = 1;
    return true;
  });

  if (!codes.length) {
    console.log('%c広告コードが見つかりませんでした。',
      'color:#c00;font-weight:bold');
    console.log('「広告リンク」のページで実行してください'
      + '（プログラム管理 → 参加中プログラム → 広告リンク）。');
    return;
  }

  var out = codes.join('\n---\n');

  function done() {
    console.log('%c' + codes.length + ' 件をコピーしました',
      'color:#0a7;font-weight:bold;font-size:14px');
    console.log('管理画面の「サイト設定 → ASPの広告」に貼り付けてください。');
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
