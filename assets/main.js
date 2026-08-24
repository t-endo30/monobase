(function () {
  'use strict';

  /* ---- ハンバーガーメニュー ---- */
  var toggle = document.getElementById('navToggle');
  var nav = document.getElementById('globalNav');
  if (!toggle || !nav) return;

  toggle.addEventListener('click', function () {
    var open = nav.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
  });

  /* ナビ内リンクを押したら閉じる（スマホ時） */
  nav.addEventListener('click', function (e) {
    if (e.target.tagName === 'A' && window.innerWidth < 900) {
      nav.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });

  /* PC幅に戻したときは状態をリセット */
  window.addEventListener('resize', function () {
    if (window.innerWidth >= 900) {
      nav.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });

})();

(function () {
  'use strict';

  /* ---- スクロール連動：追従CTA / トップへ戻る ---- */
  var sticky = document.getElementById('stickyCta');
  var toTop = document.getElementById('toTop');
  var footer = document.querySelector('.site-footer');
  if (!toTop || !footer) return;
  var ticking = false;

  function onScroll() {
    var y = window.pageYOffset || document.documentElement.scrollTop;
    var showAfter = 500;

    /* フッターに到達したら追従CTAは隠す */
    var footerTop = footer.getBoundingClientRect().top;
    var nearFooter = footerTop < window.innerHeight;

    if (sticky) {
      if (y > showAfter && !nearFooter) {
        sticky.classList.add('is-visible');
      } else {
        sticky.classList.remove('is-visible');
      }
    }

    if (y > showAfter) {
      toTop.classList.add('is-visible');
    } else {
      toTop.classList.remove('is-visible');
    }
    ticking = false;
  }

  window.addEventListener('scroll', function () {
    if (!ticking) {
      window.requestAnimationFrame(onScroll);
      ticking = true;
    }
  }, { passive: true });

  onScroll();

  toTop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();

/* ============================================================
   スクロール表示アニメーション + ヘッダーの引き締め
   ============================================================ */
(function () {
  'use strict';

  /* ---- 動きを減らす設定の人には適用しない ---- */
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var targets = document.querySelectorAll('.reveal');

  if (reduce || !('IntersectionObserver' in window)) {
    Array.prototype.forEach.call(targets, function (el) { el.classList.add('is-in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target;
        /* 同じ行のカードを少しずつ遅らせて、順に現れるようにする */
        var i = Array.prototype.indexOf.call(el.parentNode.children, el);
        el.style.transitionDelay = Math.min(i % 3, 2) * 70 + 'ms';
        el.classList.add('is-in');
        io.unobserve(el);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });

    Array.prototype.forEach.call(targets, function (el) {
      /* 読み込み時点で既に画面の上側にある要素は、アニメーションを待たせない。
         #アンカー付きURLで開いたときに本文が消えたままになるのを防ぐ。 */
      if (el.getBoundingClientRect().top < window.innerHeight) {
        el.classList.add('is-in');
        return;
      }
      io.observe(el);
    });
  }

  /* ---- ヘッダーの引き締め ---- */
  var header = document.querySelector('.site-header');
  if (!header) return;
  var ticking = false;
  function onScroll() {
    header.classList.toggle('is-shrunk', (window.pageYOffset || 0) > 80);
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { window.requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });
  onScroll();
})();

/* ============================================================
   スマホの操作性：カテゴリータブの左右スワイプ切り替え
   ------------------------------------------------------------
   一覧ページ（トップ／カテゴリー）でだけ有効。
   カテゴリーナビの並び順（ALL → 各カテゴリー）をそのまま使うので、
   タブを増やしても JS 側の変更は要らない。
   ============================================================ */
(function () {
  'use strict';

  if (!document.body.classList.contains('is-listing')) return;

  var list = document.querySelector('.cat-nav-list');
  if (!list) return;

  var links = Array.prototype.slice.call(list.querySelectorAll('a'));
  if (links.length < 2) return;

  var current = links.findIndex(function (a) { return a.classList.contains('is-current'); });
  if (current < 0) current = 0;

  /* ---- 現在のタブを常に画面内に見せる（横スクロールするため） ---- */
  var cur = links[current];
  if (cur && list.scrollWidth > list.clientWidth) {
    list.scrollLeft = cur.offsetLeft - (list.clientWidth - cur.offsetWidth) / 2;
  }

  /* ---- スワイプできることを伝える一文（タッチ端末のみCSSで表示） ---- */
  var KEY = 'mb.swipeHintSeen';
  var seen = false;
  try { seen = localStorage.getItem(KEY) === '1'; } catch (e) { seen = false; }
  if (!seen) {
    var hint = document.createElement('p');
    hint.className = 'swipe-hint';
    hint.textContent = '← 左右にスワイプでカテゴリーを切り替え →';
    var main = document.querySelector('main .container');
    if (main && main.firstElementChild) {
      main.insertBefore(hint, main.firstElementChild);
    }
  }

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function go(dir) {
    try { localStorage.setItem(KEY, '1'); } catch (e) { /* 保存できなくても動作に影響しない */ }
    var next = current + dir;
    if (next < 0 || next >= links.length) return;      /* 端では何もしない */
    var href = links[next].getAttribute('href');
    if (!href) return;
    if (reduce) { window.location.href = href; return; }
    document.body.classList.add('is-swiping-out', dir > 0 ? 'to-left' : 'to-right');
    setTimeout(function () { window.location.href = href; }, 150);
  }

  /* ---- スワイプ判定 ----
     ・横移動が縦移動より明確に大きいときだけ切り替える（縦スクロールを邪魔しない）
     ・横スクロールする部品（表・タブ・カルーセル）の上から始まった操作は無視する */
  var x0 = 0, y0 = 0, t0 = 0, tracking = false;
  var IGNORE = '.table-scroll,.cat-nav,.chips,input,textarea,select,button';
  var MIN_X = 60;        /* この距離を超えたら切り替え */
  var MAX_Y = 45;        /* 縦にこれ以上動いたらスクロール操作とみなす */
  var MAX_MS = 700;      /* ゆっくりした操作は対象外 */

  document.addEventListener('touchstart', function (ev) {
    if (ev.touches.length !== 1) { tracking = false; return; }
    if (ev.target.closest && ev.target.closest(IGNORE)) { tracking = false; return; }
    var t = ev.touches[0];
    x0 = t.clientX; y0 = t.clientY; t0 = Date.now(); tracking = true;
  }, { passive: true });

  document.addEventListener('touchend', function (ev) {
    if (!tracking) return;
    tracking = false;
    var t = ev.changedTouches[0];
    var dx = t.clientX - x0;
    var dy = t.clientY - y0;
    if (Date.now() - t0 > MAX_MS) return;
    if (Math.abs(dy) > MAX_Y) return;
    if (Math.abs(dx) < MIN_X) return;
    if (Math.abs(dx) < Math.abs(dy) * 1.6) return;
    go(dx < 0 ? 1 : -1);          /* 左へスワイプ＝次のカテゴリー */
  }, { passive: true });

  /* ---- PCではキーボードの左右でも移動できるようにする ---- */
  document.addEventListener('keydown', function (ev) {
    if (ev.altKey || ev.ctrlKey || ev.metaKey || ev.shiftKey) return;
    var tag = (ev.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
    if (ev.key === 'ArrowRight') go(1);
    if (ev.key === 'ArrowLeft') go(-1);
  });
})();

/* ============================================================
   横スクロールする表：右端まで見たらグラデーションを消す
   ============================================================ */
(function () {
  'use strict';
  var tables = document.querySelectorAll('.table-scroll');
  if (!tables.length) return;
  Array.prototype.forEach.call(tables, function (el) {
    function update() {
      var end = el.scrollLeft + el.clientWidth >= el.scrollWidth - 4;
      el.classList.toggle('is-end', end || el.scrollWidth <= el.clientWidth);
    }
    el.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    update();
  });
})();
