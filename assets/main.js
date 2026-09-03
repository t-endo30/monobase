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

  /* ---- 動きを減らす設定の人には適用しない ---- */
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
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

  /* ---- カードに New / Hot を付ける ----
     公開から3日以内を「新着」とする。24時間だと、公開した翌日には
     もう札が消えてしまい、新着記事の枠に1つも札が出ない日が続く。 */
  var NEW_SPAN = 3 * 24 * 60 * 60 * 1000;
  function flags(root) {
    var cards = (root || document).querySelectorAll('.card[data-slug],.arow[data-slug]');
    Array.prototype.forEach.call(cards, function (card) {
      var box = card.querySelector('.card-flags');
      if (!box || box.dataset.done) return;
      box.dataset.done = '1';
      var d = card.getAttribute('data-date');
      if (d) {
        var t = new Date(d + 'T00:00:00').getTime();
        if (!isNaN(t) && Date.now() - t < NEW_SPAN) {
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

  function esc(t) {
    return String(t == null ? '' : t)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  /* 星は5つぶんの文字を切り出して作る（画像を足さずに済ませる） */
  function starStr(n) {
    n = Math.round(Number(n) || 0);
    return '★★★★★☆☆☆☆☆'.slice(5 - n, 10 - n);
  }

  /* 掲載日はタイルの右下に「2026.08.31」の形で置く */
  function dotDate(d) {
    d = String(d || '').slice(0, 10);
    return d.length === 10
      ? '<span class="arow-date">' + esc(d).replace(/-/g, '.') + '</span>' : '';
  }

  function rows(limit, badgeOnThumb) {
    return ranked.slice(0, limit).map(function (it, i) {
      var n = counts[it.slug] || 0;
      var sc = Number(it.score) || 0;
      var rate = sc > 0
        ? '<span class="arow-rating"><span class="rate-own">当サイト独自評価</span>' +
          '<span aria-hidden="true">' + starStr(sc) +
          '</span><b>' + (Math.round(sc * 10) / 10) + '</b></span>'
        : '';
      var catch_ = it.excerpt
        ? '<span class="arow-catch">' + esc(it.excerpt) + '</span>' : '';
      /* 札は build.py の article_row() と同じ出し分け。写真に乗せる枠
         （PCサイドの細い列）だけ thumb、それ以外は見出しの右／日付の左。 */
      var catBadge = '<span class="cat-badge">' + esc(it.cat) + '</span>';
      var headBadge = '<span class="cat-badge is-head-badge">' + esc(it.cat) + '</span>';
      var footBadge = '<span class="cat-badge is-foot-badge">' + esc(it.cat) + '</span>';
      /* 行の形は build.py の article_row() と同じ（.arow…）。
         こちらは閲覧回数から並べ替えるので JS 側で組み立てるが、
         クラス名をそろえてあるので見た目は一覧ページと一致する。
         順位はサムネイルの角に重ねる。横幅を食わずに済む。 */
      return '<li class="arow rank-item">' +
        '<a class="arow-link" href="' + it.url + '">' +
          '<span class="arow-thumb">' +
            '<img src="' + esc(it.thumb) + '" alt="" loading="lazy" decoding="async">' +
            '<span class="arow-no arow-no-' + (i + 1) + '">' + (i + 1) + '</span>' +
            (badgeOnThumb ? catBadge : '') +
          '</span>' +
          '<span class="arow-body">' +
            '<span class="arow-head">' +
              '<span class="arow-title">' + esc(it.title) + '</span>' +
              (badgeOnThumb ? '' : headBadge) +
            '</span>' +
            rate + catch_ +
            '<span class="arow-foot">' +
              (badgeOnThumb ? '' : footBadge) + dotDate(it.date) +
            '</span>' +
          '</span>' +
        '</a></li>';
    }).join('');
  }

  /* 枠ごとに出す件数を変えられるようにする（トップは5件、専用ページは10件）。
     札は、写真が小さいPCサイドの細い列だけ写真に乗せる。それ以外は
     新着記事など他の一覧と同じ（PCは見出しの右、スマホは日付の左）。 */
  Array.prototype.forEach.call(lists, function (el) {
    var box = el.closest('.rank-box');
    var limit = Number(box && box.getAttribute('data-rank-limit')) || 10;
    el.innerHTML = rows(limit, !!el.closest('.side-rank'));
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
  var reduce = !!(window.matchMedia
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

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
  var btns = document.querySelectorAll('.share-btn.is-copy, .fab-item.is-copy');
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
   右下の共有ボタン：外を押す・Escで閉じる
   ------------------------------------------------------------
   開閉そのものは <details> がやるので、ここは「閉じ忘れ」を
   拾うだけ。開いたまま記事を読み進めると、本文に重なるため。
   ============================================================ */
(function () {
  'use strict';
  var fab = document.getElementById('shareFab');
  if (!fab) return;
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
  if (window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (!('IntersectionObserver' in window)) return;

  var hero = document.querySelector('.hero');
  if (!hero) return;
  var parts = hero.querySelectorAll('.hero-title, .hero-figure');
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
