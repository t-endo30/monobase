
/* タイルの見出しは「主題｜補足」を必ず「｜」で折る。build.py の
   v2_title() と同じ扱い。成り行きに任せると語の途中で割れる。 */
function titleHtml(t) {
  t = String(t == null ? '' : t);
  var i = t.indexOf('｜');
  if (i < 0) return t;
  return '<span class="tt-main">' + t.slice(0, i).trim() + '</span>' +
         '<span class="tt-sub">' + t.slice(i + 1).trim() + '</span>';
}
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

/* ============================================================
   iPhone（iOS Safari）で押したときの動きを効かせる
   ------------------------------------------------------------
   iOS Safari は :active を、その要素かページのどこかに「触れたことを
   受け取る人」がいないと当てない。PCのスマホ表示（Chrome の端末
   エミュレータ）では当たるのに実機の iPhone だけ沈まない、という
   食い違いはこれが原因。空の touchstart をひとつ置くと当たるようになる。
   もうひとつ、iOS は body に cursor:pointer が無い要素を「押せるもの」と
   見なさないことがあるので、CSS 側でも指定してある。
   ============================================================ */
document.addEventListener('touchstart', function () {}, { passive: true });

(function () {
  'use strict';

  /* ---- ハンバーガーメニュー ----
     新デザインの引き出しは #drawer を data-open で開け閉めする。
     開いているあいだは背後の本文を動かさない（閉じたときに、読んでいた
     位置を見失わないようにするため）。 */
  var toggle = document.getElementById('navToggle');
  var drawer = document.getElementById('drawer');
  if (!toggle || !drawer) return;

  function setOpen(open) {
    drawer.setAttribute('data-open', String(open));
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
    document.body.style.overflow = open ? 'hidden' : '';
  }
  function isOpen() { return drawer.getAttribute('data-open') === 'true'; }

  toggle.addEventListener('click', function () { setOpen(!isOpen()); });

  /* 引き出しの中のリンクを押したら閉じる */
  drawer.addEventListener('click', function (ev) {
    if (ev.target.closest('a')) setOpen(false);
  });

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && isOpen()) setOpen(false);
  });

  /* PC幅に戻したときは閉じた状態に戻す */
  window.addEventListener('resize', function () {
    if (window.innerWidth >= 861 && isOpen()) setOpen(false);
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

  /* 端末の「動きを減らす」設定は見ない（サイト運営者の指定）。
     iOS の「視差効果を減らす」を入れている人が多く、その端末だけ
     何も動かなくなるため、設定にかかわらず動かす。 */
  var reduce = false;
  var targets = document.querySelectorAll('.reveal');

  /* アニメが終わったら reveal 関連のクラスを外す。
     こうしないと animation の fill が transform を保持し続け、
     :hover のリフトなど、ふだんの動きが効かなくなる。 */
  function settle(el) {
    el.classList.remove('reveal', 'is-in');
    el.style.transitionDelay = '';
    el.style.animationDelay = '';
  }

  if (reduce || !('IntersectionObserver' in window)) {
    Array.prototype.forEach.call(targets, function (el) { settle(el); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target;
        /* 同じ行のカードを少しずつ遅らせて、順に現れるようにする */
        var i = Array.prototype.indexOf.call(el.parentNode.children, el);
        el.style.animationDelay = Math.min(i % 3, 2) * 70 + 'ms';
        el.classList.add('is-in');
        el.addEventListener('animationend', function () { settle(el); }, { once: true });
        /* animationend が来ない場合の保険 */
        setTimeout(function () { settle(el); }, 900);
        io.unobserve(el);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });

    Array.prototype.forEach.call(targets, function (el) { io.observe(el); });

    /* 画面内・画面より上にある要素は、その場で表示してしまう。
       目次リンクやアンカー付きURLで一気にスクロールすると、
       IntersectionObserver が反応しないまま通り過ぎた要素が
       透明のまま残るため、スクロールのたびに取りこぼしを拾う。 */
    var pending = Array.prototype.slice.call(targets);
    var sweeping = false;
    function sweep() {
      sweeping = false;
      pending = pending.filter(function (el) {
        if (!el.classList.contains('reveal') || el.classList.contains('is-in')) return false;
        if (el.getBoundingClientRect().top < window.innerHeight) {
          el.classList.add('is-in');
          el.addEventListener('animationend', function () { settle(el); }, { once: true });
          setTimeout(function () { settle(el); }, 900);
          io.unobserve(el);
          return false;
        }
        return true;
      });
      /* 出すものが尽きたら、スクロールのたびの走査をやめる */
      if (!pending.length) {
        window.removeEventListener('scroll', queueSweep);
        window.removeEventListener('hashchange', queueSweep);
        window.removeEventListener('resize', queueSweep);
      }
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

  /* ---- ヘッダーの引き締め ----
     スマホはタブバーの位置がヘッダーの高さに連動しており、
     スクロールのたびに大きさが変わると画面がガクつく／指の位置が
     ずれる原因になるため、この演出はPC幅（900px以上）だけにする。 */
  var header = document.querySelector('.v2-header');
  if (!header) return;
  var ticking = false;
  function onScroll() {
    var isDesktop = window.matchMedia && window.matchMedia('(min-width:900px)').matches;
    header.classList.toggle('is-shrunk', isDesktop && (window.pageYOffset || 0) > 80);
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { window.requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });
  onScroll();
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
  /* リンク先はアフィリエイトタグ付きのAmazonなので、
     お知らせではなく広告だと分かる表示に切り替える（ステマ規制の対応）。
     リンクを持たない告知は、そのまま「お知らせ」で出す。 */
  if (s.url) {
    var lb = box.querySelector('.notice-label');
    if (lb) lb.textContent = 'PR';
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
  /* views は開設からの累計（タイルに出す VIEW）、
     recent は直近ぶん（並び順と Hot の札）。 */
  var siteViews = data.views || {};
  var recentViews = data.recent || {};
  var rankBase = Object.keys(recentViews).length ? recentViews : siteViews;
  var hasSiteViews = Object.keys(rankBase).length > 0;

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
  var counts = hasSiteViews ? rankBase : mine;
  var ranked = items.slice().sort(function (a, b) {
    var d = (counts[b.slug] || 0) - (counts[a.slug] || 0);
    if (d) return d;
    return (b.date || '').localeCompare(a.date || '');   /* 同数なら新しい順 */
  });
  var hot = {};
  ranked.slice(0, 10).forEach(function (it) {
    if ((counts[it.slug] || 0) > 0) hot[it.slug] = true;
  });

  /* ---- カードに New / Hot を付ける ----
     公開から3日以内を「新着」とする。24時間だと、公開した翌日には
     もう札が消えてしまい、新着記事の枠に1つも札が出ない日が続く。 */
  var NEW_SPAN = 3 * 24 * 60 * 60 * 1000;
  function flags(root) {
    var cards = (root || document).querySelectorAll(
      '.card[data-slug],.arow[data-slug],.row-item[data-slug]');
    Array.prototype.forEach.call(cards, function (card) {
      var box = card.querySelector('.card-flags');
      if (!box || box.dataset.done) return;
      box.dataset.done = '1';
      /* 順位の札が乗るタイル（ランキングの欄）は、その札だけを見せる。
         新着の欄（data-flags="new"）は New だけに絞る。 */
      if (card.querySelector('.row-no,.arow-no')) return;
      var only = card.getAttribute('data-flags') || '';
      var d = card.getAttribute('data-date');
      if (d) {
        var t = new Date(d + 'T00:00:00').getTime();
        if (!isNaN(t) && Date.now() - t < NEW_SPAN) {
          box.insertAdjacentHTML('beforeend', '<span class="flag flag-new">New</span>');
        }
      }
      if (only !== 'new' && hot[card.getAttribute('data-slug')]) {
        box.insertAdjacentHTML('beforeend', '<span class="flag flag-hot">Hot</span>');
      }
    });
  }
  /* ---- タイルの右下に閲覧数を出す ----
     出すのは content/ranking.json（GA4 の実数）があるときだけ。
     端末ごとの記録は、その人だけの回数なので出さない。 */
  function views(root) {
    /* content/ranking.json がまだ空でも、枠だけ消えると欠けて見えるので
       0 として出す。端末ごとの記録は「その人だけの回数」なので使わない。 */
    var t = (root || document).querySelectorAll('.card-views');
    Array.prototype.forEach.call(t, function (el) {
      var card = el.closest('[data-slug]');
      if (!card) return;
      /* GA4 は閲覧のあった記事しか返さないので、無い記事は 0 として出す */
      var n = siteViews[card.getAttribute('data-slug')] || 0;
      el.textContent = 'VIEW : ' + n.toLocaleString('en-US');
      el.hidden = false;
    });
  }
  views();

  flags();
  /* あとから組み直された枠（今日のピックアップなど）にも付け直す */
  document.addEventListener('mb:cards', function (ev) {
    var root = (ev && ev.detail) || document;
    flags(root); views(root);
  });
  /* 検索結果はあとから差し込まれるので、増えたぶんにも付ける */
  var results = document.getElementById('searchResults');
  if (results && 'MutationObserver' in window) {
    new MutationObserver(function () { flags(results); views(results); })
      .observe(results, { childList: true });
  }

  /* ---- ランキングを描く ---- */
  var lists = document.querySelectorAll('.rank-list');
  if (!lists.length) return;

  function esc(t) {
    return String(t == null ? '' : t)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  /* 星は5つぶんの文字を切り出して作る（画像を足さずに済ませる） */
  function starStr(n) {
    n = Math.round(Number(n) || 0);
    return '★★★★★☆☆☆☆☆'.slice(5 - n, 10 - n);
  }

  /* 行の形は build.py の v2_row() と同じ（.row-item）にそろえてある。
     こちらは閲覧回数から並べ替えるので JS で組み立てるが、クラス名を
     そろえてあるので、一覧ページやトップの並びと見た目が一致する。
     順位は写真の左上に重ねる（独立した列にすると、写真と見出しの
     位置がランキングのときだけずれるため）。 */
  function rows(limit) {
    return ranked.slice(0, limit).map(function (it, i) {
      var no = ('0' + (i + 1)).slice(-2);
      var d = String(it.date || '').slice(0, 10);
      return '<a class="row-item" href="' + it.url + '"' +
          ' data-cat="' + esc(it.catKey || '') + '"' +
          ' data-slug="' + esc(it.slug || '') + '"' +
          ' data-date="' + esc(it.date || '') + '">' +
          '<span class="thumb">' +
            '<img src="' + esc(it.thumb) + '" alt="" loading="lazy" decoding="async">' +
            '<span class="row-no is-n' + (i + 1) + '">' + no + '</span>' +
          '</span>' +
          '<span class="row-body">' +
            '<span class="row-meta">' +
              '<span class="meta">' + esc(d) + '</span>' +
              '<span class="row-cat">' + esc(it.cat) + '</span>' +
            '</span>' +
            '<h3>' + titleHtml(it.title) + '</h3>' +
            (it.excerpt ? '<p>' + esc(it.excerpt) + '</p>' : '') +
          '</span>' +
        '</a>';
    }).join('');
  }

  /* 枠ごとに出す件数を変えられるようにする（トップは5件、専用ページは10件）。
     札は、写真が小さいPCサイドの細い列だけ写真に乗せる。それ以外は
     新着記事など他の一覧と同じ（PCは見出しの右、スマホは日付の左）。 */
  Array.prototype.forEach.call(lists, function (el) {
    var box = el.closest('.rank-box');
    var limit = Number(box && box.getAttribute('data-rank-limit')) || 10;
    el.innerHTML = rows(limit);
  });

  /* 並び順の説明文は出さない（画面を説明で埋めない） */
})();











/* ============================================================
   スマホ：画面下に浮かぶ検索（廃止）
   ------------------------------------------------------------
   以前はここで .float-search を組み立てていたが、
   下部固定の検索欄は廃止した。SEARCH タブから search.html へ。
   ============================================================ */



/* ============================================================
   Motion（motion.dev）による、押した感触・ホバーの動き
   ------------------------------------------------------------
   CSSのtransitionだけだと、押したときの「戻り」が機械的になる。
   ばね（spring）を使うと、指を離したあとの戻り方が自然になる。
   ・ライブラリは assets/vendor に置いた必要最小限の版（約11KB）
   ・読み込めていない場合は何もしない（CSS側の見た目のまま動く）

   「動きを減らす」設定のときの扱い
   ------------------------------------------------------------
   以前はこの区画をまるごと諦めていた。だが、その設定で困るのは
   「大きく滑る・流れる・繰り返し動く」もので、押したときに数％
   沈む手応えではない。全部止めると、押せたのかどうかが分からない
   画面になる（iPhone は「視差効果を減らす」が既定で入っている
   ことがあり、実機だけ何も動かない、という食い違いが起きていた）。
   ここでは、手応えだけ残して、移動をともなう演出を止める。
   ============================================================ */
(function () {
  'use strict';
  var M = window.Motion;
  if (!M || !M.press) return;
  /* 「動きを減らす」設定は見ない（上と同じ理由） */
  var reduce = false;

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
  pressable('.card, .row-item, .cat-cell, .sitemap-list a', .985);
  pressable('.card-link, .btn-sub, .btn-line, .btn-solid, .chip, .sub-chip', .94);
  pressable('.share-btn, .fab-item, .sec-more a', .97);
  pressable('.to-top, .nav-toggle, .fab-main', .88);

  /* ここから下は、移動をともなう演出。「動きを減らす」設定では出さない。 */
  if (reduce) return;



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
      document.querySelectorAll('.card, .cat-cell'),
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
   ASPの広告：入れてあるものから、表示のたびに何件かを選ぶ
   ------------------------------------------------------------
   同じ広告が並ばないよう、重複なしで選ぶ（選んだものは候補から外す）。
   選ばれなかったものは <template> の中に残るので、画像も計測用の
   画像も読み込まれない。1回の表示につき、出したぶんだけが数えられる。
   コードそのものには一切手を触れず、そのまま差し込む。

   バナーが出せなかったときは、そのタイルごと引っ込める。広告を止める
   拡張機能を使っている人や、配信元に届かなかったときに、写真の位置が
   空いたまま日付と見出しだけが残るのを避けるため。
   ============================================================ */
(function () {
  'use strict';

  /* 差し込んだ広告のバナーを見張る。読めなかったらタイルを隠す */
  function watch(slot) {
    var imgs = slot.querySelectorAll('.card-thumb img');
    var banner = null;
    for (var i = 0; i < imgs.length; i++) {
      /* 1x1 は成果を数えるための画像。バナーではない */
      if (imgs[i].getAttribute('width') !== '1') { banner = imgs[i]; break; }
    }
    if (!banner) { slot.hidden = true; return; }
    function hide() { slot.hidden = true; }
    if (banner.complete) {
      if (!banner.naturalWidth) hide();   /* 読み込みに失敗している */
      return;
    }
    banner.addEventListener('error', hide);
  }

  var groups = document.querySelectorAll('.promo-group');
  Array.prototype.forEach.call(groups, function (group) {
    var bodies = group.querySelectorAll('.promo-body');
    if (group.hasAttribute('data-rotate')) {
      var pool = Array.prototype.slice.call(
        group.querySelectorAll('template.promo-item'));
      if (!pool.length || !bodies.length) return;
      Array.prototype.forEach.call(bodies, function (body) {
        if (!pool.length) return;
        var i = Math.floor(Math.random() * pool.length);
        body.appendChild(pool[i].content.cloneNode(true));
        pool.splice(i, 1);          /* 選んだものは候補から外す */
      });
    }
    Array.prototype.forEach.call(
      group.querySelectorAll('.promo-slot'), watch);
  });
})();



/* ------------------------------------------------ 注目のアイテムの価格
   価格と○%OFFは、Amazon の Product Advertising API から取った値しか
   出してはいけない（規約）。審査が通るまで data-deals-api は空のままで、
   そのあいだ この関数は何もしない＝商品名と写真だけが出る。

   審査後は content/site.json の features.deals_api に取得先（例 /api/deals）
   を入れるだけでよい。取得先は
     { "B0XXXXXXXX": {"price":"¥8,990","off":"10%OFF"}, ... , "_at":"18:53" }
   の形を返すこと。24時間以内に取り直した値だけを返す（規約の要件）。 */

/* ============================================================
   記事末尾のシェアボタン：「リンクをコピー」
   ------------------------------------------------------------
   クリップボードにページURLをコピーし、一瞬だけボタンの文字で
   結果を知らせる。対応していない環境（古いSafari等）では
   ボタンごと消す（押しても何も起きないボタンを残さないため）。
   ============================================================ */
(function () {
  'use strict';
  var btns = document.querySelectorAll('.share-btn.is-copy');
  if (!btns.length) return;
  if (!navigator.clipboard || !navigator.clipboard.writeText) {
    Array.prototype.forEach.call(btns, function (b) { b.hidden = true; });
    return;
  }
  Array.prototype.forEach.call(btns, function (btn) {
    /* 右下の丸いボタンは中身がアイコンなので、文字は差し替えず色だけ変える */
    var isIcon = btn.classList.contains('fab-item');
    var label = btn.textContent;
    btn.addEventListener('click', function () {
      var url = btn.getAttribute('data-copy-url') || location.href;
      navigator.clipboard.writeText(url).then(function () {
        if (!isIcon) btn.textContent = 'コピーしました';
        btn.classList.add('is-copied');
        btn.setAttribute('aria-label', 'リンクをコピーしました');
        window.setTimeout(function () {
          if (!isIcon) btn.textContent = label;
          btn.classList.remove('is-copied');
          btn.setAttribute('aria-label', 'リンクをコピー');
        }, 1800);
      }).catch(function () {});
    });
  });
})();


/* ============================================================
   右下の共有ボタン
   ------------------------------------------------------------
   中身（X・LINE・リンクのコピー）は、最初に開かれたときにここで作る。
   HTMLに置いたままにすると、閉じているあいだ、文字の無いリンクが
   透明のまま画面の隅に残り、隠しリンクを埋め込んでいるように見える。
   共有先のURLは data 属性で受け取る。
   ============================================================ */
(function () {
  'use strict';
  var fab = document.getElementById('shareFab');
  if (!fab) return;

  var IC_X = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">' +
    '<path d="M17.5 3h3.2l-7 8L22 21h-6.4l-5-6.6L4.8 21H1.6l7.5-8.6L2 3h6.6l4.6 6.1z"/></svg>';
  var IC_LINE = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">' +
    '<path d="M12 3C6.5 3 2 6.6 2 11c0 3.9 3.5 7.2 8.2 7.9.3.07.75.22.86.5.1.26.07.66.03.92' +
    'l-.14.83c-.4.25-.2.96.85.53 1.05-.44 5.65-3.33 7.7-5.7C20.9 14.5 22 12.9 22 11c0-4.4-4.5-8-10-8Z"/></svg>';
  var IC_LINK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" ' +
    'stroke-linecap="round" aria-hidden="true">' +
    '<path d="M10.5 13.5a3.5 3.5 0 0 0 5 0l3-3a3.5 3.5 0 1 0-5-5l-1.4 1.4"/>' +
    '<path d="M13.5 10.5a3.5 3.5 0 0 0-5 0l-3 3a3.5 3.5 0 1 0 5 5l1.4-1.4"/></svg>';

  var built = false;
  function build() {
    if (built) return;
    built = true;
    var x = fab.getAttribute('data-x') || '';
    var line = fab.getAttribute('data-line') || '';
    var url = fab.getAttribute('data-url') || location.href;

    function item(href, label, inner, cls) {
      var el = document.createElement(href ? 'a' : 'button');
      el.className = 'fab-item' + (cls ? ' ' + cls : '');
      if (href) {
        el.href = href;
        el.target = '_blank';
        el.rel = 'noopener';
      } else {
        el.type = 'button';
        el.setAttribute('data-copy-url', url);
      }
      el.setAttribute('aria-label', label);
      el.innerHTML = inner;
      fab.appendChild(el);
      return el;
    }

    item(x, 'Xでシェア', IC_X);
    item(line, 'LINEでシェア', '<span class="ic-sq">' + IC_LINE + '</span>', 'is-line');
    var copy = item('', 'リンクをコピー', IC_LINK, 'is-copy');

    copy.addEventListener('click', function () {
      if (!navigator.clipboard || !navigator.clipboard.writeText) return;
      navigator.clipboard.writeText(url).then(function () {
        copy.classList.add('is-copied');
        copy.setAttribute('aria-label', 'リンクをコピーしました');
        window.setTimeout(function () {
          copy.classList.remove('is-copied');
          copy.setAttribute('aria-label', 'リンクをコピー');
        }, 1800);
      }).catch(function () {});
    });

    /* 中身を足した直後に開くと、置いた位置から動かず飛び出さないので、
       一度描かせてから開いた状態の指定を当てる */
    void fab.offsetWidth;
  }

  fab.addEventListener('toggle', function () { if (fab.open) build(); });
  /* 押した時点で作っておく（toggle より前に用意できる） */
  fab.querySelector('.fab-main').addEventListener('click', build);

  /* 開いたまま記事を読み進めると本文に重なるので、外を押したら閉じる */
  document.addEventListener('click', function (ev) {
    if (fab.open && !fab.contains(ev.target)) fab.open = false;
  });
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && fab.open) fab.open = false;
  });
  /* 共有先へ飛んだあとに戻ってきたとき、開いたままにしない */
  fab.addEventListener('click', function (ev) {
    if (ev.target.closest('.fab-item')) window.setTimeout(function () { fab.open = false; }, 400);
  });
})();


/* ============================================================
   トップの見出しと箱の写真：画面に入るたび、もう一度動かす
   ------------------------------------------------------------
   CSSのアニメーションはページを開いたときに1回きり走る。
   スクロールで一度離れて戻ってきても、そのままでは動かない。
   ここでは画面から出たことを見張っておき、次に入ってきたときに
   animation を external に外して付け直す（＝最初から流し直す）。

   JSが動かない環境でも、開いたときの1回は CSS 側で動く。
   ============================================================ */
(function () {
  'use strict';
  if (!('IntersectionObserver' in window)) return;

  var hero = document.querySelector('.hero');
  if (!hero) return;
  var parts = hero.querySelectorAll('.hero-title .tw, .hero-figure');
  if (!parts.length) return;

  function replay() {
    Array.prototype.forEach.call(parts, function (el) {
      el.style.animation = 'none';
      /* 一度レイアウトを読ませて、付け直しを別の変化として扱わせる */
      void el.offsetWidth;
      el.style.animation = '';
    });
  }

  /* いま画面に入っているかどうか。出てから入り直したときだけ流し直す
     （入ったまま少し揺れただけで何度も動くと、うるさくなる） */
  var inside = true;
  new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) {
        if (!inside) replay();
        inside = true;
      } else {
        inside = false;
      }
    });
  }, { threshold: 0.25 }).observe(hero);

  /* 戻るボタンで戻ってきたときは、ブラウザが画面をそのまま復元するので
     アニメーションは走らない。そのときも流し直す */
  window.addEventListener('pageshow', function (ev) {
    if (ev.persisted) replay();
  });
})();


/* ============================================================
   トップの「今日のピックアップ」：全記事から4本を日替わりで選ぶ
   ------------------------------------------------------------
   ビルドは公開のたびにしか走らないので、選び直しはここで行う。
   その日の日付を種にして混ぜるので、同じ日に見た人には同じ4本が、
   日付が変われば別の4本が出る（読み込むたびに入れ替わると、
   さっき見た記事を探せなくなるため）。
   よく読まれている記事（RANKING）と同じ4列にそろえている。
   JSが動かないときは、build.py が入れておいた4本がそのまま残る。
   ============================================================ */
(function () {
  'use strict';
  var grid = document.getElementById('pickGrid');
  if (!grid) return;
  var pool = [];
  try { pool = JSON.parse(grid.getAttribute('data-pool') || '[]'); }
  catch (e) { return; }
  if (pool.length < 5) return;          /* 選ぶ意味がない本数なら触らない */

  /* 日付を種にした、同じ入力なら同じ結果になる混ぜ方 */
  var seed = Math.floor(Date.now() / 86400000);
  function rnd() {
    seed = (seed * 1103515245 + 12345) & 0x7fffffff;
    return seed / 0x7fffffff;
  }
  var pick = pool.slice();
  for (var i = pick.length - 1; i > 0; i--) {
    var j = Math.floor(rnd() * (i + 1));
    var t = pick[i]; pick[i] = pick[j]; pick[j] = t;
  }
  pick = pick.slice(0, 4);

  function esc(v) {
    return String(v == null ? '' : v)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  /* 形は build.py の v2_card() と同じ。ここだけ別の見た目にしない */
  grid.innerHTML = pick.map(function (a) {
    return '<a class="card" href="' + esc(a.u) + '"' +
      ' data-cat="' + esc(a.k) + '" data-slug="' + esc(a.s) + '"' +
      ' data-date="' + esc(a.d) + '">' +
      '<span class="card-thumb"><img src="' + esc(a.th) + '" alt="" loading="lazy">' +
        '<span class="card-flags" aria-hidden="true"></span></span>' +
      '<span class="card-meta">' +
        '<span class="card-date">' + esc(a.d) + '</span>' +
        '<span class="card-cat">' + esc(a.c) + '</span></span>' +
      '<span class="card-title">' + titleHtml(a.t) + '</span>' +
      '<span class="card-note">' + esc(a.x) + '</span>' +
      '<span class="card-views" hidden></span></a>';
  }).join('');
  /* 差し替えた札と閲覧数は、ここで組み直したぶんにも付ける */
  document.dispatchEvent(new CustomEvent('mb:cards', { detail: grid }));
})();


/* ============================================================
   背景の写真を、スクロールの半分の速さで動かす
   ------------------------------------------------------------
   CSS だけだと background-attachment は「止める（fixed）」か
   「本文と同じ速さで動かす（scroll）」の2つしか選べない。その中間に
   したいので、写真だけを別の層に分けて、スクロール量の半分だけずらす。

   ずらせる量には上限を置く。層を縦に伸ばすほど写真も引き伸ばされ、
   拡大されて粗くなるため。画面の高さの4割ぶんまで送ったら止める。
   最初の1〜2画面ぶんで効く演出なので、そこまであれば足りる。

   ・動かすのは transform だけなので、画面の描き直しが起きず、
     指で送っても引っかかりにくい
   ・JSが動かない環境では、CSS 側の背景（止めたまま）がそのまま残る
   ============================================================ */
(function () {
  'use strict';
  var body = document.body;
  if (!body) return;

  var cs = window.getComputedStyle(body);
  var image = cs.backgroundImage;
  if (!image || image === 'none') return;

  var layer = document.createElement('div');
  layer.className = 'bg-parallax';
  layer.setAttribute('aria-hidden', 'true');
  layer.style.backgroundImage = image;
  layer.style.backgroundSize = cs.backgroundSize;
  layer.style.backgroundPosition = cs.backgroundPosition;
  layer.style.backgroundRepeat = cs.backgroundRepeat;
  body.insertBefore(layer, body.firstChild);
  body.classList.add('has-bg-parallax');   /* body 側の写真は消す */

  var SPEED = 0.5;
  var MAX_RATIO = 0.4;          /* 送れるのは画面の高さの4割まで */
  var maxTravel = 0;
  var offset = 0;
  var ticking = false;

  function measure() {
    maxTravel = window.innerHeight * MAX_RATIO;
    /* 送るぶんだけ層を伸ばす。伸ばさないと下端が切れて地の色が出る */
    layer.style.height = 'calc(100vh + ' + Math.ceil(maxTravel) + 'px)';
  }

  function apply() {
    layer.style.transform = 'translate3d(0,' + (-offset).toFixed(1) + 'px,0)';
    ticking = false;
  }

  function onScroll() {
    var y = window.pageYOffset || document.documentElement.scrollTop || 0;
    offset = Math.min(y * SPEED, maxTravel);
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(apply);
    }
  }

  measure();
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', function () { measure(); onScroll(); });
  window.addEventListener('load', function () { measure(); onScroll(); });
})();


/* ============================================================
   3つの特長を押したときに開く板
   ------------------------------------------------------------
   ヒーローでは字数を絞っているので、具体的に何をしているのかは
   ここで読ませる。開いているあいだは背後の本文を動かさない。
   ============================================================ */
(function () {
  'use strict';
  var buttons = document.querySelectorAll('.hero-point[data-point]');
  if (!buttons.length) return;

  var opener = null;

  function close(dlg) {
    dlg.classList.remove('is-open');
    document.body.style.overflow = '';
    /* 消える動きが終わってから隠す。すぐ hidden にすると、
       ふっと消えるだけになってしまう（CSS の .5s に合わせる） */
    window.setTimeout(function () { dlg.hidden = true; }, 520);
    if (opener) { opener.focus(); opener = null; }
  }

  function open(dlg, btn) {
    opener = btn;
    dlg.hidden = false;
    document.body.style.overflow = 'hidden';
    /* 一度描かせてから印を付ける。そうしないと出る動きが省かれる */
    void dlg.offsetWidth;
    dlg.classList.add('is-open');
    var c = dlg.querySelector('.hp-close');
    if (c) c.focus();
  }

  Array.prototype.forEach.call(buttons, function (btn) {
    var dlg = document.getElementById(btn.getAttribute('data-point'));
    if (!dlg) return;
    btn.addEventListener('click', function () { open(dlg, btn); });

    /* 閉じる：×・板の外・Esc */
    dlg.querySelector('.hp-close').addEventListener('click', function () { close(dlg); });
    dlg.addEventListener('click', function (ev) {
      if (ev.target === dlg) close(dlg);
    });
    dlg.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape') close(dlg);
      /* 開いているあいだ、タブ移動は板の中だけを回す */
      if (ev.key !== 'Tab') return;
      var f = dlg.querySelectorAll('a[href],button');
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (ev.shiftKey && document.activeElement === first) {
        ev.preventDefault(); last.focus();
      } else if (!ev.shiftKey && document.activeElement === last) {
        ev.preventDefault(); first.focus();
      }
    });
  });
})();


/* ============================================================
   トップのカテゴリー：横に送る並び
   ------------------------------------------------------------
   ・左右のボタンで1枠ずつ送る
   ・指やマウスでそのまま引ける
   ・端まで来たらボタンを隠す（押しても動かないボタンを残さない）
   スマホでは横に送らない組みにしているので、ここも何もしない。
   ============================================================ */
(function () {
  'use strict';
  var rails = document.querySelectorAll('[data-rail]');
  if (!rails.length) return;

  Array.prototype.forEach.call(rails, function (rail) {
    var track = rail.querySelector('.cat-grid');
    var prev = rail.querySelector('.rail-btn.is-prev');
    var next = rail.querySelector('.rail-btn.is-next');
    if (!track || !prev || !next) return;

    function step() {
      var cell = track.querySelector('.cat-cell');
      if (!cell) return track.clientWidth * 0.8;
      var gap = parseFloat(getComputedStyle(track).columnGap) || 16;
      return cell.getBoundingClientRect().width + gap;
    }

    function sync() {
      /* 横に送らない組み（スマホ）のときは、ボタンを出さない */
      if (getComputedStyle(track).overflowX !== 'auto') {
        prev.hidden = next.hidden = true;
        return;
      }
      var max = track.scrollWidth - track.clientWidth;
      var x = track.scrollLeft;
      /* 端の判定には少し余裕を持たせる。枠を吸い付かせている関係で、
         いちばん左でも数pxずれた値になることがある */
      prev.hidden = x <= 4;
      next.hidden = x >= max - 4;
      /* 右端まで来たら、続きがある合図のぼかしを消す */
      track.classList.toggle('is-end', x >= max - 4);
    }

    /* 送ったあとは、動きが終わるのを待たずにボタンの出し分けも見直す。
       scroll の通知だけに頼ると、環境によっては更新が遅れる */
    function go(dir) {
      track.scrollBy({ left: dir * step(), behavior: 'smooth' });
      window.setTimeout(sync, 60);
      window.setTimeout(sync, 420);
    }
    prev.addEventListener('click', function () { go(-1); });
    next.addEventListener('click', function () { go(1); });

    track.addEventListener('scroll', sync, { passive: true });
    window.addEventListener('resize', sync);
    sync();

    /* ---- 指やマウスで引く ----
       押した位置からの動きぶんだけ横に送る。少しでも動かしたときは
       クリックとして扱わない（引いた先の記事へ飛ばさないため）。 */
    var down = false, moved = false, startX = 0, startLeft = 0;

    track.addEventListener('pointerdown', function (ev) {
      if (ev.pointerType === 'touch') return;   /* 指は端末の慣性に任せる */
      down = true; moved = false;
      startX = ev.clientX; startLeft = track.scrollLeft;
      /* ここで pointer を捕まえてはいけない。捕まえたままだと、離したときの
         click が捕まえた側（この帯）に届き、タイルのリンクには届かなくなる
         ＝押しても分野のページへ飛べなくなる。引き始めてから捕まえる。 */
    });
    track.addEventListener('pointermove', function (ev) {
      if (!down) return;
      var dx = ev.clientX - startX;
      if (!moved && Math.abs(dx) > 4) {
        moved = true;
        track.classList.add('is-dragging');
        /* 引くと決まった時点で捕まえる。ここから先は、枠の外に
           出てもついてくる。クリックはもとより打ち消す */
        try { track.setPointerCapture(ev.pointerId); } catch (e) {}
      }
      if (moved) { track.scrollLeft = startLeft - dx; sync(); }
    });
    function release(ev) {
      if (!down) return;
      down = false;
      track.classList.remove('is-dragging');
      sync();
      if (ev && ev.pointerId != null) {
        try { track.releasePointerCapture(ev.pointerId); } catch (e) {}
      }
    }
    track.addEventListener('pointerup', release);
    track.addEventListener('pointercancel', release);
    track.addEventListener('click', function (ev) {
      if (moved) { ev.preventDefault(); ev.stopPropagation(); moved = false; }
    }, true);
  });
})();

/* ============================================================
   指で押したときの、記事タイルの面を最後まで見せる
   ------------------------------------------------------------
   :active だけだと、指を離した瞬間に遷移が始まるので、斜めの面が
   渡りきる前に次のページへ移ってしまう。押した時点でしるし（クラス）
   を付け、面が渡りきるまでの残り時間だけ遷移を待たせる。
   待っているあいだは手ぶらではなく、遷移先の HTML を裏で読みに行く
   ので、待った時間はそのぶん次のページの表示が早くなる方に使われる。
   カーソルのある機器と、動きを控える設定の人には掛けない。
   ============================================================ */
(function () {
  if (!window.matchMedia) return;

  /* 遷移を待たせるのはスマホだけ。指で触る機器でも、タイルが4列で並ぶ
     幅（861px以上／タブレットなど）では待たせず、そのまま飛ばす。
     幅は向きを変えると変わるので、そのつど見る */
  function phone() {
    return matchMedia('(hover:none)').matches
        && matchMedia('(max-width:860px)').matches
        && !matchMedia('(prefers-reduced-motion:reduce)').matches;
  }
  if (!matchMedia('(hover:none)').matches) return;
  if (matchMedia('(prefers-reduced-motion:reduce)').matches) return;

  /* 面が渡る .2s と、そのあと文字が白へ変わり終わるまで（.14s 待って .08s）。
     動きが終わりきる .22s に、描き始めの1フレームぶんを足して待つ */
  var HOLD = 240;
  /* 指はタップでも数px動く。少し動いたくらいでは押したことを取り消さない */
  var SLOP = 12;
  var warmed = {};
  var target = null, startedAt = 0, startX = 0, startY = 0;

  /* 遷移先を先に読みに行く。同じ場所の HTML だけ、1回だけ */
  function warm(href) {
    if (!href || warmed[href]) return;
    var u;
    try { u = new URL(href, location.href); } catch (e) { return; }
    if (u.origin !== location.origin) return;
    warmed[href] = 1;
    try {
      fetch(u.href, { credentials: 'same-origin' }).catch(function () {});
    } catch (e) {}
  }

  function card(ev) {
    var t = ev.target;
    return t && t.closest ? t.closest('a.card,a.row-item,a.cat-cell') : null;
  }
  function clear() {
    if (!target) return;
    target.classList.remove('is-tapping');
    target = null;
  }

  document.addEventListener('touchstart', function (ev) {
    var a = card(ev);
    if (!a) return;
    clear();
    target = a; startedAt = Date.now();
    var t0 = ev.touches && ev.touches[0];
    startX = t0 ? t0.clientX : 0;
    startY = t0 ? t0.clientY : 0;
    a.classList.add('is-tapping');
    if (phone()) warm(a.getAttribute('href'));
  }, { passive: true });

  /* はっきり動かしたときだけスクロールとみなし、押したことを取り消す */
  document.addEventListener('touchmove', function (ev) {
    if (!target) return;
    var t0 = ev.touches && ev.touches[0];
    if (!t0) { clear(); return; }
    if (Math.abs(t0.clientX - startX) > SLOP
     || Math.abs(t0.clientY - startY) > SLOP) clear();
  }, { passive: true });
  document.addEventListener('touchcancel', clear, { passive: true });
  /* 戻ってきたときにしるしが残らないようにする（bfcache） */
  window.addEventListener('pageshow', clear);

  document.addEventListener('click', function (ev) {
    var a = card(ev);
    if (!a || a !== target) return;
    if (ev.defaultPrevented || ev.metaKey || ev.ctrlKey || ev.shiftKey) return;
    if (a.target && a.target !== '_self') return;
    if (!phone()) return;

    /* 押した先と、いま押されたものが食い違うことがある（指が少し動いて
       取り消していた、touchstart を取りこぼした、など）。その場合は
       ここを動きの始まりとして数え直す。数えられないまま素通しすると、
       動きが出ないまま遷移してしまう */
    if (a !== target) {
      if (target) target.classList.remove('is-tapping');
      target = a; startedAt = Date.now();
      a.classList.add('is-tapping');
      warm(a.getAttribute('href'));
    }
    var wait = HOLD - (Date.now() - startedAt);
    if (wait <= 0) return;         /* 長押しなどで、もう終わりきっている */
    ev.preventDefault();
    var href = a.href, gone = false;
    function go() { if (gone) return; gone = true; location.href = href; }
    /* 動きが終わったことは、最後に終わる「文字の色」で見る。端末が
       transitionend を返さない場合に備えて、時間でも必ず飛ばす */
    var cap = setTimeout(go, wait + 180);
    a.addEventListener('transitionend', function h(te) {
      if (te.propertyName !== 'color') return;
      /* 戻る向きの色の変化（しるしが外れたあと）では飛ばさない */
      if (!a.classList.contains('is-tapping')) return;
      a.removeEventListener('transitionend', h);
      clearTimeout(cap); go();
    });
  });
})();
