(function () {
  'use strict';

  /* ---- ハンバーガーメニュー ---- */
  var toggle = document.getElementById('navToggle');
  var nav = document.getElementById('globalNav');
  if (!toggle || !nav) return;

  /* 背面の覆い。押すと閉じる（メニューは画面に被せて出す） */
  var veil = document.createElement('div');
  veil.className = 'nav-veil';
  veil.hidden = true;
  document.body.appendChild(veil);

  function setOpen(open) {
    nav.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
    veil.hidden = !open;
  }
  veil.addEventListener('click', function () { setOpen(false); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && nav.classList.contains('is-open')) setOpen(false);
  });

  toggle.addEventListener('click', function () {
    setOpen(!nav.classList.contains('is-open'));
  });

  /* ナビ内リンクを押したら閉じる（スマホ時） */
  nav.addEventListener('click', function (e) {
    if (e.target.tagName === 'A' && window.innerWidth < 900) setOpen(false);
  });

  /* PC幅に戻したときは状態をリセット */
  window.addEventListener('resize', function () {
    if (window.innerWidth >= 900) setOpen(false);
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

  /* スワイプの移動順。並び替える前の「サイト本来の順序」を使う。
     見た目の順序で動かすと、切り替えるたびに隣が変わってしまう。
     スマホではカテゴリーの横並びを出していないので、
     ALL / NEW / RANKING を見ているときはその3つの間を移動し、
     カテゴリーのページを見ているときはカテゴリー間を移動する。 */
  var tabs = document.querySelector('.tab-bar');
  var onTabPage = ['all', 'new', 'ranking'].indexOf(bodyCat) >= 0;
  var narrow = window.matchMedia && window.matchMedia('(max-width:899px)').matches;
  var order = (narrow && tabs && onTabPage)
    ? Array.prototype.slice.call(tabs.querySelectorAll('a'))
    : Array.prototype.slice.call(list.querySelectorAll('a'));

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

  var here = location.pathname.split('/').pop() || 'index.html';
  var current = links.findIndex(function (a) {
    return (a.getAttribute('href') || '').split('/').pop() === here;
  });
  if (current < 0) {
    current = links.findIndex(function (a) { return a.classList.contains('is-current'); });
  }
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
    hint.textContent = (narrow && tabs && onTabPage)
      ? '← 左右にスワイプで ALL / NEW / RANKING を切り替え →'
      : '← 左右にスワイプでカテゴリーを切り替え →';
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

/* ============================================================
   閲覧回数の記録 / New・Hot バッジ / アクセスランキング
   ------------------------------------------------------------
   ランキングの元データは2通り。
     ① content/ranking.json に値が入っていれば、それ（サイト全体の実数）
     ② 空なら、その端末に記録した閲覧回数
   ②は閲覧者ごとの記録なので、初めての人には出せない。その場合は
   新着順で埋め、断り書きを添える。
   ============================================================ */
(function () {
  'use strict';

  var VIEW_KEY = 'mb.views';
  var data = {};
  try { data = JSON.parse(document.body.getAttribute('data-rank') || '{}'); }
  catch (e) { data = {}; }
  var items = data.items || [];
  var siteViews = data.views || {};
  var hasSiteViews = Object.keys(siteViews).length > 0;

  /* ---- この端末の閲覧回数を数える ---- */
  var mine = {};
  try { mine = JSON.parse(localStorage.getItem(VIEW_KEY) || '{}') || {}; }
  catch (e) { mine = {}; }

  var article = document.querySelector('article.card-surface');
  if (article) {
    var m = location.pathname.match(/articles\/([^/]+)\.html$/);
    if (m) {
      mine[m[1]] = (mine[m[1]] || 0) + 1;
      try { localStorage.setItem(VIEW_KEY, JSON.stringify(mine)); } catch (e) {}
    }
  }

  /* ---- 並び順を決める ---- */
  var counts = hasSiteViews ? siteViews : mine;
  var ranked = items.slice().sort(function (a, b) {
    var d = (counts[b.slug] || 0) - (counts[a.slug] || 0);
    if (d) return d;
    return (b.date || '').localeCompare(a.date || '');   /* 同数なら新しい順 */
  });
  var hot = {};
  ranked.slice(0, 10).forEach(function (it) {
    if ((counts[it.slug] || 0) > 0) hot[it.slug] = true;
  });

  /* ---- カードに New / Hot を付ける ---- */
  var DAY = 24 * 60 * 60 * 1000;
  function flags(root) {
    var cards = (root || document).querySelectorAll('.card[data-slug]');
    Array.prototype.forEach.call(cards, function (card) {
      var box = card.querySelector('.card-flags');
      if (!box || box.dataset.done) return;
      box.dataset.done = '1';
      var d = card.getAttribute('data-date');
      if (d) {
        var t = new Date(d + 'T00:00:00').getTime();
        if (!isNaN(t) && Date.now() - t < DAY) {
          box.insertAdjacentHTML('beforeend', '<span class="flag flag-new">New</span>');
        }
      }
      if (hot[card.getAttribute('data-slug')]) {
        box.insertAdjacentHTML('beforeend', '<span class="flag flag-hot">Hot</span>');
      }
    });
  }
  flags();
  /* 検索結果はあとから差し込まれるので、増えたぶんにも付ける */
  var results = document.getElementById('searchResults');
  if (results && 'MutationObserver' in window) {
    new MutationObserver(function () { flags(results); })
      .observe(results, { childList: true });
  }

  /* ---- ランキングを描く ---- */
  var lists = document.querySelectorAll('.rank-list');
  if (!lists.length) return;
  var top = ranked.slice(0, 10);
  var html = top.map(function (it, i) {
    var n = counts[it.slug] || 0;
    return '<li class="rank-item">' +
      '<a href="' + it.url + '">' +
        '<span class="rank-no rank-no-' + (i + 1) + '">' + (i + 1) + '</span>' +
        '<span class="rank-body">' +
          '<span class="rank-title">' + it.title + '</span>' +
          '<span class="rank-meta">' + it.cat + (n ? '　' + n + '回' : '') + '</span>' +
        '</span>' +
      '</a></li>';
  }).join('');
  Array.prototype.forEach.call(lists, function (el) { el.innerHTML = html; });

  /* 並び順の説明文は出さない（画面を説明で埋めない） */
})();

/* ============================================================
   スマホのタブ「CATEGORIES」：その場でカテゴリー一覧を開閉する
   ============================================================ */
(function () {
  'use strict';
  var btn = document.getElementById('tabCats');
  var panel = document.getElementById('catPanel');
  if (!btn || !panel) return;
  var bar = btn.closest('.tab-bar');

  /* 背面の覆いは実体のある要素にする。疑似要素だと押した場所を
     受け取れず、外側を押しても閉じられないため。 */
  var veil = document.createElement('div');
  veil.className = 'cat-veil';
  veil.hidden = true;
  document.body.appendChild(veil);
  veil.addEventListener('click', function () { setOpen(false); });

  function setOpen(open) {
    if (open) panel.removeAttribute('hidden'); else panel.setAttribute('hidden', '');
    btn.setAttribute('aria-expanded', String(open));
    btn.classList.toggle('is-current', open);
    /* 開いているあいだは現在ページのタブの色を消す。
       選択されている印が2か所に出ると、どちらが今の状態か分からなくなる。 */
    if (bar) bar.classList.toggle('is-panel-open', open);
    document.body.classList.toggle('is-cat-open', open);
    veil.hidden = !open;
  }

  btn.addEventListener('click', function () {
    setOpen(panel.hasAttribute('hidden'));
  });
  /* メニューの外を押したら閉じる */
  document.addEventListener('click', function (ev) {
    if (panel.hasAttribute('hidden')) return;
    if (panel.contains(ev.target) || btn.contains(ev.target)) return;
    setOpen(false);
  });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && !panel.hasAttribute('hidden')) setOpen(false);
  });
})();

/* ============================================================
   特集カルーセル：1枠に1件ずつ、5秒ごとに送る
   ------------------------------------------------------------
   ・自動送りは、指で操作している間・タブが裏にある間は止める
   ・前後ボタンと下の点、指のスワイプでも動かせる
   ・「動きを減らす」設定の人には自動送りをしない
   ============================================================ */
(function () {
  'use strict';
  var box = document.querySelector('.feat-carousel');
  if (!box) return;
  var track = box.querySelector('.feat-track');
  var slides = box.querySelectorAll('.feat-slide');
  if (!track || slides.length < 2) return;

  var dots = box.querySelectorAll('.feat-dot');
  var wait = parseInt(box.getAttribute('data-interval'), 10) || 5000;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var i = 0, timer = null;

  box.classList.add('is-ready');

  function show(n) {
    i = (n + slides.length) % slides.length;
    track.style.transform = 'translate3d(' + (-i * 100) + '%,0,0)';
    Array.prototype.forEach.call(dots, function (d, k) {
      d.classList.toggle('is-current', k === i);
    });
  }
  function next() { show(i + 1); }
  function start() {
    if (reduce || timer) return;
    timer = setInterval(next, wait);
  }
  function stop() { clearInterval(timer); timer = null; }
  function restart() { stop(); start(); }

  show(0);
  start();

  var prev = box.querySelector('.feat-prev');
  var nxt = box.querySelector('.feat-next');
  if (prev) prev.addEventListener('click', function () { show(i - 1); restart(); });
  if (nxt) nxt.addEventListener('click', function () { show(i + 1); restart(); });
  Array.prototype.forEach.call(dots, function (d) {
    d.addEventListener('click', function () {
      show(parseInt(d.getAttribute('data-go'), 10) || 0);
      restart();
    });
  });

  box.addEventListener('mouseenter', stop);
  box.addEventListener('mouseleave', start);
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) stop(); else start();
  });

  /* 指でも送れるようにする。カテゴリー切り替えのスワイプと
     取り合いにならないよう、この枠の中では横移動を打ち切る。 */
  var x0 = 0, y0 = 0, drag = false;
  box.addEventListener('touchstart', function (ev) {
    if (ev.touches.length !== 1) return;
    x0 = ev.touches[0].clientX; y0 = ev.touches[0].clientY; drag = true;
    stop();
  }, { passive: true });
  box.addEventListener('touchmove', function (ev) {
    if (!drag) return;
    var dx = ev.touches[0].clientX - x0;
    var dy = ev.touches[0].clientY - y0;
    if (Math.abs(dx) > 12 && Math.abs(dx) > Math.abs(dy) * 1.4) {
      ev.stopPropagation();
      if (ev.cancelable) ev.preventDefault();
    }
  }, { passive: false });
  box.addEventListener('touchend', function (ev) {
    if (!drag) return;
    drag = false;
    var dx = ev.changedTouches[0].clientX - x0;
    var dy = ev.changedTouches[0].clientY - y0;
    if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.4) {
      ev.stopPropagation();
      show(i + (dx < 0 ? 1 : -1));
    }
    start();
  }, { passive: true });
})();

/* ============================================================
   トップの見出しを1行に収める
   ------------------------------------------------------------
   文字数と枠の幅は端末で変わるので、実際に測って字を詰める。
   小さくしすぎないよう下限を決め、それでも入らない場合は
   折り返しを許して読めなくならないようにする。
   ============================================================ */
(function () {
  'use strict';
  var el = document.querySelector('.fit-line');
  if (!el) return;

  var MAX = 34, MIN = 12;      /* px。これ以上は小さくしない */
  var box = el.parentElement;
  if (!box) return;

  function overflows() {
    /* はみ出しているかは、要素自身の表示幅と中身の幅を比べて判定する。
       親の幅から余白を引く方法だと1px単位でずれ、いつまでも縮み続ける。 */
    return el.scrollWidth > el.clientWidth + 1;
  }

  function fit() {
    if (!el.clientWidth) return;           /* まだ表示されていないときは測らない */
    el.style.whiteSpace = 'nowrap';
    el.style.fontSize = MAX + 'px';
    if (!overflows()) return;

    /* はみ出し量から必要な大きさを見積もり、そこから微調整する */
    var size = Math.max(MIN, Math.floor(MAX * el.clientWidth / el.scrollWidth * 2) / 2);
    el.style.fontSize = size + 'px';
    var guard = 0;
    while (size > MIN && overflows() && guard++ < 60) {
      size -= 0.5;
      el.style.fontSize = size + 'px';
    }
    if (overflows()) el.style.whiteSpace = '';   /* 下限でも入らなければ折り返す */
  }

  /* 枠の幅が決まったタイミングで測る。読み込み直後やフォント適用前だと
     幅が確定しておらず、必要以上に小さくなることがあるため。 */
  if ('ResizeObserver' in window) {
    new ResizeObserver(fit).observe(box);
  } else {
    window.addEventListener('resize', fit);
  }
  requestAnimationFrame(fit);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
})();

/* ============================================================
   トップの記事数の一文（カテゴリー名は毎回3つ選ぶ）
   ============================================================ */
(function () {
  'use strict';
  var el = document.querySelector('.hero-count');
  if (!el) return;
  var names = [];
  try { names = JSON.parse(el.getAttribute('data-cats') || '[]'); } catch (e) { names = []; }
  var nCat = el.getAttribute('data-n-cat') || '0';
  var nPub = el.getAttribute('data-n-pub') || '0';

  /* 並びを混ぜて先頭3つを使う */
  for (var i = names.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var t = names[i]; names[i] = names[j]; names[j] = t;
  }
  /* カテゴリー名自体に「・」が入るものがあるため、区切りは「／」にする */
  var pick = names.slice(0, 3).join('／');
  el.textContent = pick
    ? '現在（' + pick + '）など ' + nCat + ' カテゴリーで ' + nPub + ' 記事公開中'
    : '現在 ' + nCat + ' カテゴリーで ' + nPub + ' 記事公開中';

  /* 右に余白があるなら1行で見せる。入らないときだけ折り返す。 */
  function fitCount() {
    if (!el.clientWidth) return;
    el.style.whiteSpace = 'nowrap';
    el.style.fontSize = '';
    var base = parseFloat(getComputedStyle(el).fontSize) || 13;
    var size = base;
    /* 少し詰めれば1行に入る場合だけ縮める。読めない大きさにはしない。 */
    while (size > base - 2 && size > 11.5 && el.scrollWidth > el.clientWidth + 1) {
      size -= 0.25;
      el.style.fontSize = size + 'px';
    }
    if (el.scrollWidth > el.clientWidth + 1) {
      el.style.fontSize = '';        /* 入らないときは元の大きさで折り返す */
      el.style.whiteSpace = '';
    }
  }
  if ('ResizeObserver' in window) new ResizeObserver(fitCount).observe(el);
  else window.addEventListener('resize', fitCount);
  requestAnimationFrame(fitCount);
})();

/* ============================================================
   「今日のモノ」：日替わりで1本だけ出すミニウィジェット
   ------------------------------------------------------------
   よく見ているジャンルの記事から選ぶ。読み込むたびに変わると
   「今日の」ではなくなるため、日付をもとに選び、同じ日は同じ記事を出す。
   ============================================================ */
(function () {
  'use strict';
  var boxes = document.querySelectorAll('.today-box');
  if (!boxes.length) return;

  var data = {};
  try { data = JSON.parse(document.body.getAttribute('data-rank') || '{}'); }
  catch (e) { return; }
  var items = data.items || [];
  if (!items.length) return;

  var counts = {};
  try { counts = JSON.parse(localStorage.getItem('mb.catCounts') || '{}') || {}; }
  catch (e) { counts = {}; }

  /* よく見ているジャンルを候補にする。まだ履歴がなければ全記事から選ぶ。 */
  var liked = Object.keys(counts).filter(function (k) { return counts[k] > 0; });
  var pool = items.filter(function (it) { return liked.indexOf(it.catKey) >= 0; });
  if (pool.length < 2) pool = items;

  /* 日付から決める。同じ日は同じ記事、日が変われば別の記事になる。 */
  var today = new Date();
  var seed = today.getFullYear() * 10000 + (today.getMonth() + 1) * 100 + today.getDate();
  var h = seed;
  for (var i = 0; i < liked.length; i++) h += liked[i].charCodeAt(0) * (i + 7);
  var pick = pool[h % pool.length];
  if (!pick) return;

  Array.prototype.forEach.call(boxes, function (box) {
    var a = box.querySelector('.today-card');
    var img = box.querySelector('.today-thumb img');
    a.href = pick.url;
    img.src = pick.thumb;
    img.alt = pick.title;
    box.querySelector('.today-cat').textContent = pick.cat;
    box.querySelector('.today-title').textContent = pick.title;
    box.hidden = false;
  });
})();

/* ============================================================
   スマホ：画面下に浮かぶ検索
   ------------------------------------------------------------
   記事の詳細ページ以外で出す。スクロール中は隠し、
   指が止まったらふわっと戻す。
   ============================================================ */
(function () {
  'use strict';
  if (document.querySelector('article.card-surface')) return;   /* 記事ページには出さない */
  if (document.getElementById('searchResults')) return;         /* 検索ページにも出さない */
  var form = document.querySelector('.search-tile .searchbox, .side-search .searchbox');
  if (!form) return;

  var bar = document.createElement('div');
  bar.className = 'float-search';
  bar.innerHTML = form.outerHTML;
  document.body.appendChild(bar);

  var timer = null;
  function show() { bar.classList.add('is-visible'); }
  function hide() { bar.classList.remove('is-visible'); }

  show();
  window.addEventListener('scroll', function () {
    hide();
    clearTimeout(timer);
    timer = setTimeout(show, 220);      /* 指が止まってから戻す */
  }, { passive: true });

  /* 入力中は隠さない */
  var input = bar.querySelector('input');
  if (input) {
    input.addEventListener('focus', function () { clearTimeout(timer); show(); });
  }
})();

/* ============================================================
   スマホ：下へスクロールしているあいだはタブを隠す
   ------------------------------------------------------------
   本文の表示領域を稼ぐため。ヘッダーとパンくずは残したままにして、
   今どこを見ているかは常に分かるようにする。
   上へスクロールするか、ページの先頭に戻ると再び出す。
   ============================================================ */
(function () {
  'use strict';
  var bar = document.querySelector('.tab-bar');
  if (!bar) return;
  if (!window.matchMedia || !window.matchMedia('(max-width:899px)').matches) return;

  var last = window.pageYOffset || 0;
  var ticking = false;
  var SHOW_FROM_TOP = 120;   /* この位置より上では常に出す */
  var STEP = 6;              /* 小さな揺れで切り替わらないようにする */

  function onScroll() {
    ticking = false;
    var y = window.pageYOffset || 0;
    if (Math.abs(y - last) < STEP) return;
    var down = y > last;
    last = y;
    if (y < SHOW_FROM_TOP) {
      document.body.classList.remove('is-tab-hidden');
      return;
    }
    document.body.classList.toggle('is-tab-hidden', down);
  }

  window.addEventListener('scroll', function () {
    if (!ticking) { window.requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });

  /* カテゴリーメニューを開いているあいだはタブを隠さない */
  var btn = document.getElementById('tabCats');
  if (btn) btn.addEventListener('click', function () {
    document.body.classList.remove('is-tab-hidden');
  });
})();

/* ============================================================
   固定バーの高さを実測して、下に続く帯の位置をそこに合わせる
   ------------------------------------------------------------
   これまではヘッダー64px・タブ52pxという固定値で位置を決めていたが、
   実際の高さは文字サイズや端末で変わる。ずれるとタブがヘッダーの
   裏に潜って一部しか見えなくなるため、実測した高さを CSS 変数に入れる。
   ============================================================ */
(function () {
  'use strict';
  var header = document.querySelector('.site-header');
  if (!header) return;
  var tab = document.querySelector('.tab-bar');
  var catNav = document.querySelector('.cat-nav');
  var root = document.documentElement;

  function visibleHeight(el) {
    if (!el) return 0;
    if (getComputedStyle(el).display === 'none') return 0;
    return Math.round(el.getBoundingClientRect().height);
  }

  function sync() {
    root.style.setProperty('--header-h',
      Math.round(header.getBoundingClientRect().height) + 'px');
    /* ヘッダーの下に並ぶ帯は、スマホはタブ、PCはカテゴリーナビ。
       表示されているほうの高さを使う。 */
    var t = visibleHeight(tab) || visibleHeight(catNav);
    if (t > 0) root.style.setProperty('--tab-h', t + 'px');
  }

  sync();
  if ('ResizeObserver' in window) {
    var ro = new ResizeObserver(sync);
    ro.observe(header);
    if (tab) ro.observe(tab);
    if (catNav) ro.observe(catNav);
  }
  window.addEventListener('resize', sync);
  window.addEventListener('orientationchange', sync);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(sync);
})();

/* ============================================================
   Motion（motion.dev）による、押した感触・ホバーの動き
   ------------------------------------------------------------
   CSSのtransitionだけだと、押したときの「戻り」が機械的になる。
   ばね（spring）を使うと、指を離したあとの戻り方が自然になる。
   ・ライブラリは assets/vendor に置いた必要最小限の版（約11KB）
   ・読み込めていない場合や「動きを減らす」設定のときは、
     何もしない（CSS側の見た目のまま動く）
   ============================================================ */
(function () {
  'use strict';
  var M = window.Motion;
  if (!M || !M.press) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var spring = { type: 'spring', stiffness: 520, damping: 26, mass: .7 };
  var quick = { duration: .18, ease: [.2, .7, .3, 1] };

  function pressable(selector, downScale) {
    var els = document.querySelectorAll(selector);
    if (!els.length) return;
    Array.prototype.forEach.call(els, function (el) {
      M.press(el, function () {
        M.animate(el, { scale: downScale }, quick);
        return function () { M.animate(el, { scale: 1 }, spring); };
      });
    });
  }

  /* 押せるもの：面積が大きいほど縮み方は控えめにする */
  pressable('.btn-amazon', .97);
  pressable('.card', .985);
  pressable('.feat-card, .today-card, .cat-tile', .985);
  pressable('.card-link, .btn-sub, .searchbox button, .chip', .94);
  pressable('.tab-bar a, .tab-bar button', .93);
  pressable('.feat-arrow, .to-top, .nav-toggle', .88);
  pressable('.rank-item a, .cat-tree .tree-subs a', .985);

  /* ホバー：アイコンだけ少し持ち上げる（指の端末では起きない） */
  Array.prototype.forEach.call(
    document.querySelectorAll('.cat-nav-list a, .tree-item > details > summary'),
    function (el) {
      var icon = el.querySelector('.cat-icon, .tree-icon');
      if (!icon) return;
      M.hover(el, function () {
        M.animate(icon, { y: -2, scale: 1.12 }, spring);
        return function () { M.animate(icon, { y: 0, scale: 1 }, spring); };
      });
    }
  );

  /* 「＋」の開閉に合わせて、サブカテゴリーを滑り出させる */
  Array.prototype.forEach.call(document.querySelectorAll('.cat-tree details'), function (d) {
    d.addEventListener('toggle', function () {
      if (!d.open) return;
      var ul = d.querySelector('.tree-subs');
      if (!ul) return;
      M.animate(ul, { opacity: [0, 1], y: [-6, 0] }, { duration: .22, ease: 'easeOut' });
    });
  });

  /* カートの絵文字だけ、ボタンを押したときに少し先へ動かす */
  Array.prototype.forEach.call(document.querySelectorAll('.btn-amazon .cart'), function (cart) {
    var btn = cart.closest('.btn-amazon');
    if (!btn) return;
    M.press(btn, function () {
      M.animate(cart, { x: 3 }, quick);
      return function () { M.animate(cart, { x: 0 }, spring); };
    });
  });

  /* 画面に入ってきたランキングの行を、順に浮かび上がらせる */
  if (M.inView) {
    var rank = document.querySelector('.rank-list');
    if (rank) {
      M.inView(rank, function () {
        var rows = rank.querySelectorAll('.rank-item');
        Array.prototype.forEach.call(rows, function (row, i) {
          M.animate(row, { opacity: [0, 1], y: [8, 0] },
                    { duration: .3, delay: Math.min(i, 6) * .04, ease: 'easeOut' });
        });
      }, { amount: .2 });
    }
  }
})();
