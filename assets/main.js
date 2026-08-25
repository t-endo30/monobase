/* ============================================================
   重ねて出すものを開いているあいだ、背面のスクロールを止める
   ------------------------------------------------------------
   overflow:hidden にすると、PCではスクロールバーが消えたぶん
   ページ全体が横に広がって見える（画面サイズが変わったように見える）。
   消える幅と同じだけ余白を足して、位置が動かないようにする。
   ============================================================ */
window.mbLockScroll = function (on, cls) {
  var b = document.body;
  if (on) {
    var gap = window.innerWidth - document.documentElement.clientWidth;
    if (gap > 0) b.style.paddingRight = gap + 'px';
    b.classList.add(cls);
  } else {
    b.classList.remove(cls);
    if (!b.classList.contains('is-cat-open')
        && !b.classList.contains('is-policy-open')) {
      b.style.paddingRight = '';
    }
  }
};

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
  var onTabPage = ['all', 'new', 'ranking', 'search'].indexOf(bodyCat) >= 0;
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

  /* ---- 現在のタブが隠れているときだけ、見える位置まで送る ----
     links はスマホだとタブバー側の要素になることがあるので、
     この横並びの中にあるものだけを対象にする。ほかの入れ物の
     offsetLeft で位置を決めると、関係のない量だけ横にずれる。
     また、既に見えているときは動かさない。動かすと先頭の項目が
     中途半端に切れた状態で表示されてしまう。 */
  var cur = links[current];
  if (cur && list.contains(cur) && list.scrollWidth > list.clientWidth + 1) {
    var cl = cur.offsetLeft, cr = cl + cur.offsetWidth;
    var vs = list.scrollLeft, ve = vs + list.clientWidth;
    var max = list.scrollWidth - list.clientWidth;
    if (cl < vs) list.scrollLeft = Math.max(0, cl - 12);
    else if (cr > ve) list.scrollLeft = Math.min(max, cr - list.clientWidth + 12);
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
      ? '← 左右にスワイプでタブを切り替え →'
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
  /* この中で指を動かしたときは、カテゴリー切り替えのスワイプを起こさない。
     それぞれが自前の横スクロールを持っているため。 */
  var IGNORE = '.table-scroll,.cat-nav,.chips,.rail,.feat-carousel,'
             + 'input,textarea,select,button';
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

  function rows(limit) {
    return ranked.slice(0, limit).map(function (it, i) {
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
  }

  /* 枠ごとに出す件数を変えられるようにする（トップは5件、専用ページは10件） */
  Array.prototype.forEach.call(lists, function (el) {
    var box = el.closest('.rank-box');
    var limit = Number(box && box.getAttribute('data-rank-limit')) || 10;
    el.innerHTML = rows(limit);
  });

  /* 並び順の説明文は出さない（画面を説明で埋めない） */
})();

/* ============================================================
   PC：カテゴリーを押すと、その場でサブカテゴリーを開く
   ------------------------------------------------------------
   横並びのカテゴリーを押したとき、いきなり画面を移すのではなく
   下にサブカテゴリーを出す。もう一度押すか、外を押すと閉じる。
   サブカテゴリーが無いカテゴリーは、これまでどおり画面が移る。
   JavaScript が動かない環境でも、リンクとしてそのまま機能する。
   ============================================================ */
(function () {
  'use strict';
  var list = document.querySelector('.cat-nav-list');
  var nav = document.querySelector('.cat-nav');
  if (!list || !nav) return;
  var wide = window.matchMedia && window.matchMedia('(min-width:900px)');
  var open = null;

  /* 横並びは overflow で切り取られるので、パネルは一段外に出して置く。
     位置は押した項目に合わせて、そのつど計算する。 */
  Array.prototype.forEach.call(list.querySelectorAll('.sub-pop'), function (pop) {
    nav.appendChild(pop);
  });

  function place(li) {
    var pop = li._pop;
    var a = li.querySelector('a');
    var ar = a.getBoundingClientRect();
    var nr = nav.getBoundingClientRect();
    pop.hidden = false;
    var w = pop.offsetWidth;
    var left = ar.left - nr.left;
    /* 画面からはみ出すときは、右端に合わせて内側へ寄せる */
    var maxLeft = nr.width - w - 8;
    pop.style.left = Math.max(8, Math.min(left, maxLeft)) + 'px';
    pop.style.top = (ar.bottom - nr.top + 2) + 'px';
  }

  function close() {
    if (!open) return;
    open._pop.hidden = true;
    open.classList.remove('is-open');
    var a = open.querySelector('a');
    if (a) a.setAttribute('aria-expanded', 'false');
    open = null;
  }

  function show(li) {
    if (open === li) { close(); return; }
    close();
    place(li);
    li.classList.add('is-open');
    var a = li.querySelector('a');
    if (a) a.setAttribute('aria-expanded', 'true');
    open = li;
  }

  /* 開くのはPC幅のときだけ。スマホはタブのパネルが同じ役割を持つ。 */
  Array.prototype.forEach.call(list.querySelectorAll('.has-sub'), function (li, i) {
    li._pop = nav.querySelectorAll('.sub-pop')[i];
    var a = li.querySelector('a');
    a.setAttribute('aria-expanded', 'false');
    a.addEventListener('click', function (ev) {
      if (!wide || !wide.matches) return;      /* 狭い画面ではそのまま移動 */
      ev.preventDefault();
      show(li);
    });
  });

  /* 右端まで送りきったら、端のぼかしを外す */
  function edgeMask() {
    var end = list.scrollLeft + list.clientWidth >= list.scrollWidth - 2;
    list.classList.toggle('is-end', end);
  }
  list.addEventListener('scroll', edgeMask, { passive: true });
  window.addEventListener('resize', edgeMask);
  edgeMask();

  document.addEventListener('click', function (ev) {
    if (!open) return;
    if (!ev.target.closest) { close(); return; }
    if (!ev.target.closest('.has-sub') && !ev.target.closest('.sub-pop')) close();
  });
  /* スクロールで位置がずれるので、開いたまま動かさない */
  window.addEventListener('scroll', close, { passive: true });
  list.addEventListener('scroll', close, { passive: true });
  window.addEventListener('resize', close);
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') close();
  });
  if (wide && wide.addEventListener) {
    wide.addEventListener('change', function () { close(); });
  }
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
    window.mbLockScroll(open, 'is-cat-open');
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
  /* 端末の「動きを減らす」設定にかかわらず、PCと同じ間隔・同じ滑らかさで送る。
     （サイトの見え方を端末設定で変えたくない、という運営方針による） */
  var i = 0, timer = null, onScreen = true;

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
    if (timer || !onScreen) return;
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

  /* 指の端末で mouseenter だけが起きて mouseleave が来ないと、
     自動送りが止まったまま戻らない。マウスのある端末に限って結ぶ。 */
  var hoverable = window.matchMedia && window.matchMedia('(hover:hover)').matches;
  if (hoverable) {
    box.addEventListener('mouseenter', stop);
    box.addEventListener('mouseleave', start);
  }
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) stop(); else if (onScreen) start();
  });

  /* 画面の外にあるあいだは送らない。戻ってきたら送り直す。 */
  if (window.IntersectionObserver) {
    onScreen = false;
    stop();
    new IntersectionObserver(function (es) {
      onScreen = es[0].isIntersecting;
      if (onScreen && !document.hidden) start(); else stop();
    }, { threshold: .25 }).observe(box);
  }

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

  /* px。上限は控えめにして枠を大きくしすぎない。
     下限は、スマホの幅でもこの見出し（20字前後）が1行に収まる大きさ。
     ここを下回るときだけ折り返す（文字が切れることはない）。 */
  var MAX = 24, MIN = 11;
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
    if (overflows()) {
      /* 下限まで縮めても入らないときは、小さいまま折り返さない。
         読める大きさ（CSS側の指定）に戻したうえで折り返す。 */
      el.style.whiteSpace = '';
      el.style.fontSize = '';
    }
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
  /* トップの一文だけが対象。一覧ページの「全 N 記事」は
     同じクラスを使っているので、データ属性の有無で見分ける。 */
  var el = document.querySelector('.hero-count[data-n-pub]');
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
  var full = pick
    ? '現在（' + pick + '）など ' + nCat + ' カテゴリーで ' + nPub + ' 記事公開中'
    : '現在 ' + nCat + ' カテゴリーで ' + nPub + ' 記事公開中';
  /* 幅が足りないときの短い言い方。2行に折り返すより、
     短くして1行に収めたほうが見出しの下が締まる。 */
  var brief = nCat + ' カテゴリー・' + nPub + ' 記事を公開中';

  /* 長い言い方と短い言い方を、置ける幅で選ぶ。
     以前は文字を実測して縮めていたが、書き換えるたびに
     ResizeObserver が反応して測り直し、文言と大きさが行き来していた。
     幅の判定だけにして、決まったら二度と動かさない。 */
  var WIDE = 560;                  /* この幅より広ければ長いほうを出す */
  var shown = null;

  function fitCount() {
    var box = el.parentElement || el;
    var w = box.clientWidth;
    if (!w) return;
    var want = w >= WIDE ? 'full' : 'brief';
    if (want === shown) return;    /* 変わらないときは触らない（暴れの元） */
    shown = want;
    el.textContent = want === 'full' ? full : brief;
  }

  /* 監視するのは入れ物のほう。文字を書き換える本人を見張ると、
     自分の変化に自分で反応して止まらなくなる。 */
  var box = el.parentElement || el;
  if ('ResizeObserver' in window) new ResizeObserver(fitCount).observe(box);
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
  pressable('.feat-card, .today-card', .985);
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

  /* ホバー：カードをわずかに持ち上げる（指の端末では起きない） */
  var hoverable = window.matchMedia && window.matchMedia('(hover:hover)').matches;
  if (hoverable) {
    Array.prototype.forEach.call(
      document.querySelectorAll('.card, .feat-card, .today-card'),
      function (el) {
        M.hover(el, function () {
          M.animate(el, { y: -3 }, spring);
          return function () { M.animate(el, { y: 0 }, spring); };
        });
      }
    );
    /* Amazonボタンは、指す先が分かるようカートを先に進める */
    Array.prototype.forEach.call(document.querySelectorAll('.btn-amazon'), function (btn) {
      var cart = btn.querySelector('.cart');
      M.hover(btn, function () {
        if (cart) M.animate(cart, { x: 4 }, spring);
        return function () { if (cart) M.animate(cart, { x: 0 }, spring); };
      });
    });
    /* 「詳細を見る」の矢印を右へ送る */
    Array.prototype.forEach.call(document.querySelectorAll('.card'), function (card) {
      var link = card.querySelector('.card-link');
      if (!link) return;
      M.hover(card, function () {
        M.animate(link, { x: 3 }, spring);
        return function () { M.animate(link, { x: 0 }, spring); };
      });
    });
  }

  /* 画面下から浮き出るもの（検索・購入ボタン・先頭へ戻る）
     ------------------------------------------------------------
     出す／隠すの合図は各機能が is-visible の付け外しで送ってくる。
     その切り替わりを見て、ばねで下から持ち上げる。 */
  (function () {
    if (!window.MutationObserver) return;
    var floats = document.querySelectorAll('.float-search, .sticky-cta, .to-top');
    if (!floats.length) return;

    var rise = { type: 'spring', stiffness: 240, damping: 24, mass: .9 };
    var sink = { duration: .2, ease: [.4, 0, 1, 1] };

    Array.prototype.forEach.call(floats, function (el) {
      var shown = el.classList.contains('is-visible');
      /* CSS側の出し入れと二重にならないよう、動きはこちらに任せる */
      el.classList.add('has-motion');
      M.animate(el, shown ? { y: 0, opacity: 1 } : { y: 28, opacity: 0 }, { duration: 0 });

      new MutationObserver(function () {
        var now = el.classList.contains('is-visible');
        if (now === shown) return;
        shown = now;
        if (now) M.animate(el, { y: [28, 0], opacity: [0, 1] }, rise);
        else M.animate(el, { y: 20, opacity: 0 }, sink);
      }).observe(el, { attributes: true, attributeFilter: ['class'] });
    });
  })();

  /* 特集を送ったとき、今表示している点をぷくっとさせる */
  Array.prototype.forEach.call(document.querySelectorAll('.feat-dots'), function (dots) {
    new MutationObserver(function (recs) {
      recs.forEach(function (r) {
        var d = r.target;
        if (d.classList && d.classList.contains('is-current')) {
          M.animate(d, { scale: [1, 1.45, 1.25] }, { duration: .32, ease: 'easeOut' });
        }
      });
    }).observe(dots, { subtree: true, attributes: true, attributeFilter: ['class'] });
  });

  /* New / Hot のバッジは、付いた瞬間に軽く跳ねる */
  if (M.inView) {
    Array.prototype.forEach.call(document.querySelectorAll('.card-flags'), function (f) {
      M.inView(f, function () {
        var b = f.children;
        Array.prototype.forEach.call(b, function (el, i) {
          M.animate(el, { scale: [.6, 1], opacity: [0, 1] },
                    { type: 'spring', stiffness: 600, damping: 18, delay: i * .06 });
        });
      }, { amount: .5 });
    });
  }

  /* ハンバーガーは開閉に合わせて回す */
  (function () {
    var t = document.getElementById('navToggle');
    if (!t || !window.MutationObserver) return;
    new MutationObserver(function () {
      var open = t.getAttribute('aria-expanded') === 'true';
      M.animate(t, { rotate: open ? 90 : 0 }, spring);
    }).observe(t, { attributes: true, attributeFilter: ['aria-expanded'] });
  })();

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

/* ============================================================
   ASPの広告：複数入れてあるときは、表示のたびに1つを選ぶ
   ------------------------------------------------------------
   選ばれなかったものは <template> の中に残るので、画像も計測用の
   画像も読み込まれない。1回の表示につき1件だけが数えられる。
   コードそのものには一切手を触れず、そのまま差し込む。
   ============================================================ */
(function () {
  'use strict';
  var slots = document.querySelectorAll('.promo-slot[data-rotate]');
  Array.prototype.forEach.call(slots, function (slot) {
    var list = slot.querySelectorAll('template.promo-item');
    var body = slot.querySelector('.promo-body');
    if (!list.length || !body) return;
    var pick = list[Math.floor(Math.random() * list.length)];
    body.appendChild(pick.content.cloneNode(true));
  });
})();

/* ============================================================
   「このサイトの読み方」：ページに重ねて開く
   ------------------------------------------------------------
   details のまま使い、開いているあいだだけ画面に重ねる。
   外側・×・Escape で閉じる。背面はスクロールさせない。
   ============================================================ */
(function () {
  'use strict';
  var d = document.querySelector('details.hero-policy');
  if (!d) return;
  var pop = d.querySelector('.policy-pop');

  function close() { if (d.open) d.open = false; }

  d.addEventListener('toggle', function () {
    window.mbLockScroll(d.open, 'is-policy-open');
    if (d.open && pop) pop.focus && pop.focus();
  });

  /* 背面（覆い）を押したら閉じる。板の中を押したときは閉じない。 */
  document.addEventListener('click', function (ev) {
    if (!d.open) return;
    if (ev.target.closest('.policy-close')) { close(); return; }
    if (ev.target.closest('.policy-pop')) return;
    if (ev.target.closest('details.hero-policy > summary')) return;
    close();
  });

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') close();
  });
})();

/* ============================================================
   見出しを1文字ずつ出す
   ------------------------------------------------------------
   文字を消して足し直すのではなく、最初から置いてある文字の
   「見える／見えない」を切り替える。理由は2つ。
     ・h1 は検索エンジンが読む見出し。中身を空にする時間を作らない
     ・幅を実測して1行に収める処理があるので、幅は最初から確定させる
   マーカー（accent）の入れ子は保ったまま、文字だけを包む。
   ============================================================ */
(function () {
  'use strict';
  var el = document.querySelector('.fit-line[data-typewriter]');
  if (!el) return;

  var reduce = window.matchMedia
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* 文字を1つずつ包む。要素の入れ子はそのまま残す。 */
  var chars = [];
  (function wrap(node) {
    Array.prototype.slice.call(node.childNodes).forEach(function (n) {
      if (n.nodeType === 3) {
        var frag = document.createDocumentFragment();
        n.nodeValue.split('').forEach(function (ch) {
          var s = document.createElement('span');
          s.className = 'tw-c';
          s.textContent = ch;
          frag.appendChild(s);
          chars.push(s);
        });
        node.replaceChild(frag, n);
      } else if (n.nodeType === 1) {
        wrap(n);
      }
    });
  })(el);
  if (!chars.length) return;

  if (reduce) {                       /* 動きを控える設定なら、すぐ全部出す */
    chars.forEach(function (s) { s.classList.add('is-on'); });
    return;
  }

  var SPEED = 55;                     /* 1文字あたりのミリ秒 */
  var i = 0, prev = null;
  (function step() {
    if (i >= chars.length) {
      /* 出し終わったあとも、最後の文字の右で点滅させたままにする。
         文字として「｜」を足すのではなく線を描いているだけなので、
         見出しの文言は最後まで元のままになる。 */
      return;
    }
    if (prev) prev.classList.remove('is-cur');
    chars[i].classList.add('is-on', 'is-cur');
    prev = chars[i];
    i++;
    setTimeout(step, SPEED);
  })();
})();
