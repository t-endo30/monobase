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

    Array.prototype.forEach.call(targets, function (el) { io.observe(el); });

    /* 画面内・画面より上にある要素は、その場で表示してしまう。
       目次リンクやアンカー付きURLで一気にスクロールすると、
       IntersectionObserver が反応しないまま通り過ぎた要素が
       透明のまま残るため、スクロールのたびに取りこぼしを拾う。 */
    var sweeping = false;
    function sweep() {
      sweeping = false;
      Array.prototype.forEach.call(targets, function (el) {
        if (el.classList.contains('is-in')) return;
        if (el.getBoundingClientRect().top < window.innerHeight) {
          el.classList.add('is-in');
          io.unobserve(el);
        }
      });
    }
    function queueSweep() {
      if (sweeping) return;
      sweeping = true;
      window.requestAnimationFrame(sweep);
    }
    window.addEventListener('scroll', queueSweep, { passive: true });
    window.addEventListener('hashchange', queueSweep);
    window.addEventListener('resize', queueSweep);
    sweep();
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
   スマホの操作性：カテゴリーの横スワイプ切り替え
   ------------------------------------------------------------
   一覧ページ（トップ／カテゴリー）でだけ有効。
   指の動きに画面が追従し、離した位置で「切り替える／戻す」を決める。
   カテゴリーナビの並び順をそのまま使うので、タブを増やしても
   このコードを直す必要はない。
   ============================================================ */
(function () {
  'use strict';

  var list = document.querySelector('.cat-nav-list');
  if (!list) return;

  /* ---- よく見るカテゴリーを ALL の右隣へ寄せる ----
     直近に見たものを動かすと、2つのカテゴリーを行き来しただけで
     並びが入れ替わり続けてしまうため、閲覧回数の多い順にする。
     並び替えるのは先頭の1つだけで、残りは元の順序のままにしておく。 */
  var COUNT_KEY = 'mb.catCounts';
  var bodyCat = document.body.getAttribute('data-cat') || '';
  var counts = {};
  try { counts = JSON.parse(localStorage.getItem(COUNT_KEY) || '{}') || {}; }
  catch (e) { counts = {}; }
  if (bodyCat && bodyCat !== 'all') {
    counts[bodyCat] = (counts[bodyCat] || 0) + 1;
    try { localStorage.setItem(COUNT_KEY, JSON.stringify(counts)); } catch (e) {}
  }

  /* スワイプの移動順は、並び替える前の「サイト本来の順序」を使う。
     見た目の順序で動かすと、切り替えるたびに隣が変わってしまう。 */
  var order = Array.prototype.slice.call(list.querySelectorAll('a'));

  var top = Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; })[0];
  if (top && counts[top] >= 2) {
    var li = list.querySelector('a[href*="category-' + top + '.html"]');
    li = li && li.parentNode;
    var first = list.querySelector('li');          /* ALL */
    if (li && first && li !== first) first.insertAdjacentElement('afterend', li);
  }

  if (!document.body.classList.contains('is-listing')) return;

  var links = order;
  if (links.length < 2) return;

  var current = links.findIndex(function (a) { return a.classList.contains('is-current'); });
  if (current < 0) current = 0;

  /* ---- 現在のタブを画面内に見せる ---- */
  var cur = links[current];
  if (cur && list.scrollWidth > list.clientWidth) {
    list.scrollLeft = cur.offsetLeft - (list.clientWidth - cur.offsetWidth) / 2;
  }

  /* ---- 隣のページを先読みしておく（切り替えを待たせない） ---- */
  [current - 1, current + 1].forEach(function (i) {
    if (i < 0 || i >= links.length) return;
    var l = document.createElement('link');
    l.rel = 'prefetch';
    l.href = links[i].getAttribute('href');
    document.head.appendChild(l);
  });

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var stage = document.querySelector('main.layout') || document.querySelector('main');
  if (!stage) return;

  var KEY = 'mb.swipeHintSeen';
  var seen = false;
  try { seen = localStorage.getItem(KEY) === '1'; } catch (e) { seen = false; }
  if (!seen) {
    var hint = document.createElement('p');
    hint.className = 'swipe-hint';
    hint.textContent = '← 左右にスワイプでカテゴリーを切り替え →';
    var box = document.querySelector('main .container');
    if (box && box.firstElementChild) box.insertBefore(hint, box.firstElementChild);
  }

  function go(dir) {
    var next = current + dir;
    if (next < 0 || next >= links.length) return;
    try { localStorage.setItem(KEY, '1'); } catch (e) {}
    var href = links[next].getAttribute('href');
    if (!href) return;
    if (reduce) { window.location.href = href; return; }
    /* 画面を最後まで送り出してから遷移する */
    stage.style.transition = 'transform .22s var(--ease, ease), opacity .22s ease';
    stage.style.transform = 'translate3d(' + (dir > 0 ? '-16%' : '16%') + ',0,0)';
    stage.style.opacity = '0';
    setTimeout(function () { window.location.href = href; }, 190);
  }

  /* ---- 指の動きに追従させる ----
     縦横どちらの操作か決まるまでは何もしない。
     横だと判定した後だけ、既定のスクロールを止めて画面を動かす。 */
  var x0 = 0, y0 = 0, t0 = 0;
  var state = 'idle';        /* idle → maybe → drag */
  var IGNORE = '.table-scroll,.cat-nav,.chips,input,textarea,select,button';
  var LOCK = 12;             /* この距離で縦か横かを決める */
  var DECIDE = 0.28;         /* 画面幅のこの割合を超えたら切り替える */
  var FLICK = 0.45;          /* px/ms：速く払ったら距離が短くても切り替える */

  function width() { return window.innerWidth || 360; }

  function reset(animate) {
    stage.style.transition = animate ? 'transform .22s var(--ease, ease)' : '';
    stage.style.transform = '';
    stage.style.opacity = '';
  }

  function edge(dir) {
    /* 端では動かせないので、引っ張っても戻る量を小さくする */
    var next = current + dir;
    return next < 0 || next >= links.length;
  }

  document.addEventListener('touchstart', function (ev) {
    if (ev.touches.length !== 1) { state = 'idle'; return; }
    if (ev.target.closest && ev.target.closest(IGNORE)) { state = 'idle'; return; }
    var t = ev.touches[0];
    x0 = t.clientX; y0 = t.clientY; t0 = Date.now();
    state = 'maybe';
    stage.style.transition = '';
  }, { passive: true });

  document.addEventListener('touchmove', function (ev) {
    if (state === 'idle') return;
    var t = ev.touches[0];
    var dx = t.clientX - x0;
    var dy = t.clientY - y0;

    if (state === 'maybe') {
      if (Math.abs(dy) > LOCK && Math.abs(dy) > Math.abs(dx)) { state = 'idle'; return; }
      if (Math.abs(dx) > LOCK && Math.abs(dx) > Math.abs(dy) * 1.4) { state = 'drag'; }
      else return;
    }

    /* 横スワイプと決まったら、縦スクロールは起こさせない */
    if (ev.cancelable) ev.preventDefault();
    var move = dx * (edge(dx < 0 ? 1 : -1) ? 0.22 : 0.72);   /* 端は重くする */
    stage.style.transform = 'translate3d(' + move.toFixed(1) + 'px,0,0)';
    stage.style.opacity = String(Math.max(0.55, 1 - Math.abs(move) / width()));
  }, { passive: false });

  function release(ev) {
    if (state !== 'drag') { state = 'idle'; return; }
    state = 'idle';
    var t = ev.changedTouches[0];
    var dx = t.clientX - x0;
    var speed = Math.abs(dx) / Math.max(1, Date.now() - t0);
    var dir = dx < 0 ? 1 : -1;
    /* 速く払った場合でも、ある程度の距離がなければ誤操作とみなす */
    var flick = speed > FLICK && Math.abs(dx) > 48;
    if (!edge(dir) && (Math.abs(dx) > width() * DECIDE || flick)) {
      go(dir);
    } else {
      reset(true);
    }
  }
  document.addEventListener('touchend', release, { passive: true });
  document.addEventListener('touchcancel', function () {
    if (state === 'drag') reset(true);
    state = 'idle';
  }, { passive: true });

  /* ---- PCではキーボードの左右でも移動できるようにする ---- */
  document.addEventListener('keydown', function (ev) {
    if (ev.altKey || ev.ctrlKey || ev.metaKey || ev.shiftKey) return;
    var tag = (ev.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
    if (ev.key === 'ArrowRight') go(1);
    if (ev.key === 'ArrowLeft') go(-1);
  });

  /* 戻るボタンで戻ってきたときに、送り出した状態が残らないようにする */
  window.addEventListener('pageshow', function () { reset(false); });
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

/* ============================================================
   セール告知：期間内だけ、右から左へ流して表示する
   ------------------------------------------------------------
   Amazonはセール日程を機械的に配信していないため、日程は
   content/site.json に登録しておき、表示するかどうかは
   閲覧時点の日付でここが判断する（再ビルドしなくても切り替わる）。
   ============================================================ */
(function () {
  'use strict';
  var box = document.getElementById('saleNotice');
  var text = document.getElementById('saleText');
  if (!box || !text) return;

  var items;
  try { items = JSON.parse(box.getAttribute('data-sales') || '[]'); }
  catch (e) { return; }
  if (!items.length) return;

  function ymd(d) {
    return d.getFullYear() + '/' +
      ('0' + (d.getMonth() + 1)).slice(-2) + '/' + ('0' + d.getDate()).slice(-2);
  }

  var now = new Date();
  var live = items.filter(function (s) {
    var st = new Date(s.start + 'T00:00:00');
    var en = new Date(s.end + 'T23:59:59');
    return !isNaN(st) && !isNaN(en) && now >= st && now <= en;
  });
  if (!live.length) return;          /* セール期間外は何も出さない */

  var s = live[0];
  var span = ymd(new Date(s.start + 'T00:00:00')) + '〜' + ymd(new Date(s.end + 'T00:00:00'));
  var label = '現在' + s.name + '開催中！　期間：' + span +
              (s.note ? '　' + s.note : '');
  if (s.url) {
    var a = document.createElement('a');
    a.href = s.url;
    a.target = '_blank';
    a.rel = 'nofollow sponsored noopener';
    a.textContent = label;
    text.appendChild(a);
  } else {
    text.textContent = label;
  }
  box.hidden = false;

  /* 文字数に応じて流す時間を変える。短い文が速く流れると読みにくいため */
  var len = label.length;
  text.style.animationDuration = Math.max(14, Math.round(len / 3)) + 's';
})();
