/* ============================================================
   お問い合わせフォーム
   ------------------------------------------------------------
   ・送信先（data-endpoint）が設定されていれば、そこへ送る
     （Formspree など、JSON を受け取る窓口を想定）
   ・設定されていないあいだは、入力内容をメールの本文に組み立てて
     メールソフトを開く。どちらでも連絡が取れる状態にしておく。
   ・JSが動かない環境では、素の <form> の送信がそのまま働く
   ============================================================ */
(function () {
  'use strict';
  var form = document.getElementById('contactForm');
  if (!form) return;

  var $ = function (id) { return document.getElementById(id); };
  var status = $('cfStatus');
  var submit = $('cfSubmit');
  var endpoint = (form.getAttribute('data-endpoint') || '').trim();
  var mail = form.getAttribute('data-mailto') || '';

  /* 文字数の表示 */
  var body = $('cf-body'), count = $('cf-count');
  if (body && count) {
    var tick = function () { count.textContent = body.value.length; };
    body.addEventListener('input', tick);
    tick();
  }

  function setError(id, msg) {
    var el = $(id + '-err'), input = $(id);
    if (!el) return;
    el.textContent = msg || '';
    el.hidden = !msg;
    if (input) {
      input.setAttribute('aria-invalid', msg ? 'true' : 'false');
      input.classList.toggle('is-invalid', !!msg);
    }
  }

  /* 入力の確認。ブラウザ任せにせず、日本語で理由を出す。 */
  function validate() {
    var ok = true;
    var name = $('cf-name').value.trim();
    var email = $('cf-email').value.trim();
    var msg = body.value.trim();

    setError('cf-name', name ? '' : 'お名前をご記入ください。');
    if (!name) ok = false;

    if (!email) { setError('cf-email', 'メールアドレスをご記入ください。'); ok = false; }
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('cf-email', 'メールアドレスの形式をご確認ください。'); ok = false;
    } else setError('cf-email', '');

    if (!msg) { setError('cf-body', 'お問い合わせ内容をご記入ください。'); ok = false; }
    else if (msg.length < 10) {
      setError('cf-body', '内容を10文字以上でご記入ください。'); ok = false;
    } else setError('cf-body', '');

    if (!ok) {
      var bad = form.querySelector('.is-invalid');
      if (bad) { bad.focus(); bad.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
    }
    return ok;
  }

  function say(msg, kind) {
    if (!status) return;
    status.textContent = msg;
    status.className = 'form-status is-' + kind;
    status.hidden = false;
  }

  function values() {
    return {
      topic: $('cf-topic') ? $('cf-topic').value : '',
      name: $('cf-name').value.trim(),
      email: $('cf-email').value.trim(),
      page_url: $('cf-url') ? $('cf-url').value.trim() : '',
      message: body.value.trim()
    };
  }

  /* 送信先が無いあいだは、メールソフトを開いて代わりにする */
  function openMail(v) {
    var lines = [
      'ご用件：' + v.topic,
      'お名前：' + v.name,
      'メールアドレス：' + v.email,
      '該当ページ：' + (v.page_url || '（なし）'),
      '', '── お問い合わせ内容 ──', v.message, ''
    ].join('\n');
    var href = 'mailto:' + mail
      + '?subject=' + encodeURIComponent('【お問い合わせ】' + v.topic)
      + '&body=' + encodeURIComponent(lines);
    window.location.href = href;
    say('メールソフトを開きました。内容をご確認のうえ送信してください。開かない場合は ' + mail + ' へ直接お送りください。', 'info');
  }

  /* 一度出した指摘は、直したその場で消す */
  ['cf-name', 'cf-email', 'cf-body'].forEach(function (id) {
    var el = $(id);
    if (!el) return;
    el.addEventListener('input', function () {
      if (el.classList.contains('is-invalid')) setError(id, '');
    });
  });

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    /* 迷惑送信よけの欄が埋まっていたら、黙って終わる */
    var trap = $('cf-company');
    if (trap && trap.value) return;
    if (!validate()) return;

    var v = values();
    if (!endpoint) { openMail(v); return; }

    submit.disabled = true;
    say('送信しています…', 'info');

    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(v)
    }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      form.reset();
      if (count) count.textContent = '0';
      say('送信しました。3営業日以内にご返信します。', 'ok');
    }).catch(function () {
      say('送信できませんでした。お手数ですが ' + mail + ' へ直接お送りください。', 'ng');
    }).then(function () {
      submit.disabled = false;
    });
  });
})();
