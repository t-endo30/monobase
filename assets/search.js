/* ============================================================
   サイト内検索（クライアントサイド）
   search.json を読み込み、キーワード + カテゴリ + タグで絞り込む。
   入力内容はサーバーに送信されない。
   ============================================================ */
(function () {
  'use strict';

  var input   = document.getElementById('searchInput');
  var clear   = document.getElementById('searchClear');
  var results = document.getElementById('searchResults');
  var empty   = document.getElementById('searchEmpty');
  var status  = document.getElementById('searchStatus');
  var catBox  = document.getElementById('catChips');
  var tagBox  = document.getElementById('tagChips');
  if (!input || !results) return;

  var DATA = [];
  var activeCats = [];
  var activeTags = [];

  /* ---- 正規化：全角→半角、カタカナ→ひらがな、大文字→小文字 ---- */
  function norm(s) {
    return String(s || '')
      .toLowerCase()
      .replace(/[Ａ-Ｚａ-ｚ０-９]/g, function (c) {
        return String.fromCharCode(c.charCodeAt(0) - 0xFEE0);
      })
      .replace(/[ァ-ン]/g, function (c) {
        return String.fromCharCode(c.charCodeAt(0) - 0x60);
      })
      .replace(/[　\s]+/g, ' ')
      .trim();
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* ---- スコアリング：タイトル一致を最優先 ---- */
  function score(item, terms) {
    if (!terms.length) return 1;
    var title = norm(item.title);
    var text  = norm(item.title + ' ' + item.excerpt + ' ' + item.desc + ' ' +
                     item.tags.join(' ') + ' ' + item.catLabel);
    var total = 0;
    for (var i = 0; i < terms.length; i++) {
      var t = terms[i];
      if (text.indexOf(t) === -1) return 0;      /* AND 検索 */
      total += 1;
      if (title.indexOf(t) !== -1) total += 3;
      if (item.tags.some(function (x) { return norm(x).indexOf(t) !== -1; })) total += 2;
    }
    return total;
  }

  function highlight(text, terms) {
    var out = esc(text);
    terms.forEach(function (t) {
      if (!t) return;
      try {
        var re = new RegExp('(' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
        out = out.replace(re, '<mark class="hit">$1</mark>');
      } catch (e) { /* 無効な正規表現は無視 */ }
    });
    return out;
  }

  function cardHtml(item, terms) {
    var thumb = '<img src="./' + esc(item.thumb) + '" alt="" loading="lazy" width="1200" height="430">';
    var tags = item.tags.slice(0, 2).map(function (t) {
      return '<span class="tag">' + esc(t) + '</span>';
    }).join('');
    tags += '<span class="tag tag-hot">' + esc(item.catLabel) + '</span>';
    return '' +
      '<article class="card" data-slug="' + esc(item.slug || '') + '" data-date="' + esc(item.date || '') + '">' +
        '<div class="card-thumb is-auto"><span class="card-flags" aria-hidden="true"></span>' + thumb + '</div>' +
        '<div class="card-body">' +
          '<div class="card-tags">' + tags + '</div>' +
          '<h3 class="card-title"><a class="card-stretch" href="./' + esc(item.url) + '">' + highlight(item.title, terms) + '</a></h3>' +
          '<p class="card-desc">' + highlight(item.excerpt, terms) + '</p>' +
          '<span class="card-link" aria-hidden="true">詳細を見る</span>' +
        '</div>' +
      '</article>';
  }

  function render() {
    var q = norm(input.value);
    var terms = q ? q.split(' ').filter(Boolean) : [];

    var hits = DATA
      .filter(function (it) {
        if (activeCats.length && activeCats.indexOf(it.cat) === -1) return false;
        if (activeTags.length && !activeTags.every(function (t) { return it.tags.indexOf(t) !== -1; })) return false;
        return true;
      })
      .map(function (it) { return { it: it, s: score(it, terms) }; })
      .filter(function (r) { return r.s > 0; })
      .sort(function (a, b) {
        if (b.s !== a.s) return b.s - a.s;
        return a.it.date < b.it.date ? 1 : -1;
      });

    var cond = [];
    if (terms.length) cond.push('「' + input.value.trim() + '」');
    if (activeCats.length) cond.push('カテゴリー' + activeCats.length + '件');
    if (activeTags.length) cond.push('タグ：' + activeTags.join('・'));

    /* 条件を入れていないうちは、記事を並べない。
       検索の画面に全記事が出ていると、一覧との違いが分からなくなるため。 */
    if (!cond.length) {
      results.innerHTML = '';
      empty.hidden = true;
      status.textContent = 'キーワードを入れるか、下のカテゴリー・タグを選んでください。';
      history.replaceState(null, '', location.pathname);
      return;
    }

    results.innerHTML = hits.map(function (r) { return cardHtml(r.it, terms); }).join('');
    empty.hidden = hits.length > 0;
    status.textContent = cond.join(' / ') + ' の検索結果：' + hits.length + '件';

    /* URL に検索条件を反映（リロード・共有できるように） */
    var params = new URLSearchParams();
    if (input.value.trim()) params.set('q', input.value.trim());
    if (activeCats.length) params.set('cat', activeCats.join(','));
    if (activeTags.length) params.set('tag', activeTags.join(','));
    var qs = params.toString();
    history.replaceState(null, '', qs ? '?' + qs : location.pathname);
  }

  function bindChips(box, list, key) {
    if (!box) return;
    box.addEventListener('click', function (ev) {
      var btn = ev.target.closest('.chip');
      if (!btn) return;
      var val = btn.getAttribute(key);
      var i = list.indexOf(val);
      if (i === -1) { list.push(val); btn.classList.add('is-active'); }
      else { list.splice(i, 1); btn.classList.remove('is-active'); }
      render();
    });
  }
  bindChips(catBox, activeCats, 'data-cat');
  bindChips(tagBox, activeTags, 'data-tag');

  /* ---- 入力（デバウンス） ---- */
  var timer = null;
  input.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(render, 150);
  });

  if (clear) {
    clear.addEventListener('click', function () {
      input.value = '';
      activeCats.length = 0;
      activeTags.length = 0;
      Array.prototype.forEach.call(document.querySelectorAll('.chip.is-active'), function (c) {
        c.classList.remove('is-active');
      });
      render();
      input.focus();
    });
  }

  /* ---- 起動：URLパラメータを復元 ---- */
  fetch('./search.json')
    .then(function (r) { return r.json(); })
    .then(function (json) {
      DATA = json;
      var params = new URLSearchParams(location.search);
      if (params.get('q')) input.value = params.get('q');
      (params.get('cat') || '').split(',').filter(Boolean).forEach(function (c) {
        var btn = catBox && catBox.querySelector('[data-cat="' + c + '"]');
        if (btn) { btn.classList.add('is-active'); activeCats.push(c); }
      });
      (params.get('tag') || '').split(',').filter(Boolean).forEach(function (t) {
        var btn = tagBox && tagBox.querySelector('[data-tag="' + CSS.escape(t) + '"]');
        if (btn) { btn.classList.add('is-active'); activeTags.push(t); }
      });
      render();
    })
    .catch(function () {
      status.textContent = '検索インデックスを読み込めませんでした。ページを再読み込みしてください。';
    });
})();
