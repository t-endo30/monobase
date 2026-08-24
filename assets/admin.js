/* ============================================================
   モノベース 管理画面
   - 記事データ(content/articles.json) と サイト設定(content/site.json) を
     GitHub Contents API 経由で読み書きする
   - 画像はブラウザ内で圧縮してからアップロード
   - トークンは localStorage にのみ保存（送信先は api.github.com のみ）
   ============================================================ */
(function () {
  'use strict';

  var LS = 'kp_admin_v1';
  var cfg = { owner: '', repo: '', branch: 'main', token: '' };
  var articles = [];
  var site = null;
  var shaArticles = null, shaSite = null;
  var editing = null;      // 編集中の記事オブジェクト
  var pendingImages = [];  // 圧縮済みアップロード待ち

  /* ---------------------------------------------------- utils */
  var $ = function (id) { return document.getElementById(id); };

  /* ---- 診断ログ ---- */
  function log(msg, kind) {
    var box = document.getElementById('logBox');
    if (!box) return;
    if (box.textContent.indexOf('まだ通信していません') === 0) box.textContent = '';
    var t = new Date().toTimeString().slice(0, 8);
    var span = document.createElement('span');
    span.className = kind || 'dim';
    span.textContent = '[' + t + '] ' + msg + '\n';
    box.appendChild(span);
    box.scrollTop = box.scrollHeight;
  }

  /* JSエラーを画面に出す（原因が見えないまま止まるのを防ぐ） */
  window.addEventListener('error', function (ev) {
    log('JSエラー: ' + ev.message + ' (' + (ev.filename || '').split('/').pop() + ':' + ev.lineno + ')', 'err');
    toast('エラーが発生しました。接続タブの診断ログを確認してください', 'err');
  });
  window.addEventListener('unhandledrejection', function (ev) {
    log('未処理エラー: ' + (ev.reason && ev.reason.message ? ev.reason.message : ev.reason), 'err');
  });

  function toast(msg, kind) {
    var t = $('toast');
    t.textContent = msg;
    t.className = 'toast show' + (kind ? ' ' + kind : '');
    clearTimeout(t._timer);
    t._timer = setTimeout(function () { t.className = 'toast'; }, 3600);
  }

  function b64encode(str) {
    var bytes = new TextEncoder().encode(str), bin = '';
    for (var i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
    return btoa(bin);
  }
  function b64decode(b64) {
    var bin = atob(b64.replace(/\s/g, ''));
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new TextDecoder('utf-8').decode(bytes);
  }
  function today() { return new Date().toISOString().slice(0, 10); }

  /* ---- Amazon URL から ASIN を抽出する ----
     商品ページ・モバイル版・短縮リンク展開後など、主要な形式に対応 */
  function extractAsin(str) {
    if (!str) return '';
    var t = String(str).trim();

    /* すでにASINそのものが入力されている場合 */
    if (/^[A-Z0-9]{10}$/i.test(t)) return t.toUpperCase();

    var patterns = [
      /\/dp\/([A-Z0-9]{10})/i,          /* /dp/B0XXXXXXXX          */
      /\/gp\/product\/([A-Z0-9]{10})/i, /* /gp/product/B0XXXXXXXX  */
      /\/gp\/aw\/d\/([A-Z0-9]{10})/i,   /* モバイル版               */
      /\/product\/([A-Z0-9]{10})/i,     /* /product/B0XXXXXXXX     */
      /[?&]asin=([A-Z0-9]{10})/i,       /* ?asin=B0XXXXXXXX        */
      /\/([A-Z0-9]{10})(?:[/?#]|$)/i     /* 末尾がASINのパターン     */
    ];
    for (var i = 0; i < patterns.length; i++) {
      var m = t.match(patterns[i]);
      if (m) return m[1].toUpperCase();
    }
    return '';
  }

  function slugify(s) {
    return String(s).toLowerCase()
      .replace(/[^a-z0-9\-\s]/g, '').trim()
      .replace(/\s+/g, '-').slice(0, 60) || 'article-' + Date.now();
  }

  function download(name, text, type) {
    var blob = new Blob([text], { type: type || 'application/json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }

  /* ---------------------------------------------------- GitHub API */
  function api(path, opts) {
    opts = opts || {};
    var url = 'https://api.github.com/repos/' + cfg.owner + '/' + cfg.repo + '/' + path;
    log((opts.method || 'GET') + ' ' + url.replace('https://api.github.com/repos/', ''));
    return fetch(url, {
      method: opts.method || 'GET',
      headers: {
        'Authorization': 'Bearer ' + cfg.token,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
      },
      body: opts.body ? JSON.stringify(opts.body) : undefined
    }).then(function (r) {
      log('  → HTTP ' + r.status, r.ok ? 'ok' : 'err');
      if (r.status === 404 && opts.allow404) return null;
      if (!r.ok) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          var detail = j.message || '';
          if (j.errors) { try { detail += ' / ' + JSON.stringify(j.errors); } catch (e) {} }
          log('  → ' + detail, 'err');
          throw new Error(
            r.status === 401 ? 'トークンが無効か期限切れです（401）。接続タブで作り直してください。' :
            r.status === 403 ? 'アクセスが拒否されました（403）。トークンに Contents の書き込み権限がありません。' :
            r.status === 404 ? 'リポジトリまたはファイルが見つかりません（404）。ユーザー名・リポジトリ名・ブランチ名を確認してください。' :
            r.status === 409 ? 'リポジトリ側が更新されています（409）。「再読み込み」を押してからやり直してください。' :
            r.status === 422 ? 'ファイルの状態が合いません（422）。「再読み込み」を押してからやり直してください。' :
            (detail || ('APIエラー: ' + r.status))
          );
        });
      }
      return r.json();
    });
  }

  function getFile(path) {
    return api('contents/' + path + '?ref=' + encodeURIComponent(cfg.branch), { allow404: true });
  }

  function putFile(path, contentB64, sha, message) {
    var body = { message: message, content: contentB64, branch: cfg.branch };
    if (sha) body.sha = sha;
    return api('contents/' + path, { method: 'PUT', body: body });
  }

  function setConn(state, text) {
    $('connDot').className = 'dot' + (state ? ' ' + state : '');
    $('connText').textContent = text;
  }

  /* ---------------------------------------------------- 読み込み */
  function loadAll() {
    if (!cfg.token || !cfg.owner || !cfg.repo) {
      // 未接続時はローカルの静的ファイルを読む（閲覧のみ）
      return Promise.all([
        fetch('./content/articles.json').then(function (r) { return r.json(); }),
        fetch('./content/site.json').then(function (r) { return r.json(); })
      ]).then(function (res) {
        articles = res[0]; site = res[1];
        shaArticles = shaSite = null;
        setConn('', '未接続（閲覧のみ）');
        renderAll();
        toast('未接続です。保存するには接続タブでGitHubを設定してください。');
      }).catch(function () {
        toast('データを読み込めませんでした', 'err');
      });
    }
    setConn('', '読み込み中…');
    return Promise.all([getFile('content/articles.json'), getFile('content/site.json')])
      .then(function (res) {
        if (!res[0] || !res[1]) throw new Error('content/ 内のJSONが見つかりません。リポジトリ名とブランチを確認してください。');
        articles = JSON.parse(b64decode(res[0].content)); shaArticles = res[0].sha;
        site     = JSON.parse(b64decode(res[1].content)); shaSite     = res[1].sha;
        setConn('on', cfg.owner + '/' + cfg.repo + ' @' + cfg.branch);
        renderAll();
        toast('読み込みました', 'ok');
      })
      .catch(function (err) {
        setConn('err', '接続エラー');
        toast(err.message, 'err');
      });
  }

  /* ---------------------------------------------------- 記事一覧 */
  function renderList() {
    var ul = $('articleList');
    ul.innerHTML = '';
    var cats = {};
    (site.categories || []).forEach(function (c) { cats[c.key] = c.label; });

    articles.slice().sort(function (a, b) { return a.date < b.date ? 1 : -1; })
      .forEach(function (a) {
        var li = document.createElement('li');
        li.innerHTML =
          '<span class="ico">' + (a.icon || '📦') + '</span>' +
          '<span class="meta">' +
            '<span class="ttl">' + (a.list_title || a.title || '(無題)') + '</span>' +
            '<span class="sub">' +
              '<span class="pill ' + (a.published ? 'pub">公開中' : 'draft">下書き') + '</span>' +
              (a.featured ? '<span class="pill feat">注目</span>' : '') +
              (cats[a.category] || a.category) + ' / ' + a.date + ' / ' + a.slug +
            '</span>' +
          '</span>' +
          '<span class="acts">' +
            '<button class="btn btn-ghost" data-edit="' + a.slug + '">編集</button>' +
            '<button class="btn btn-ghost" data-toggle="' + a.slug + '">' + (a.published ? '下書きに' : '公開に') + '</button>' +
            '<button class="btn btn-danger" data-del="' + a.slug + '">削除</button>' +
          '</span>';
        ul.appendChild(li);
      });

    $('statAll').textContent = articles.length;
    $('statPub').textContent = articles.filter(function (a) { return a.published; }).length;
    $('statDraft').textContent = articles.filter(function (a) { return !a.published; }).length;
  }

  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('button'); if (!b) return;
    var slug;
    if ((slug = b.getAttribute('data-edit'))) { openEditor(find(slug)); }
    else if ((slug = b.getAttribute('data-toggle'))) {
      var a = find(slug);
      if (!a.published) {
        /* 公開へ切り替えるときだけ中身を検査する */
        var blocks = ['summary', 'pros', 'cons', 'scenes', 'voices']
          .reduce(function (n, k) { return n + ((a[k] || []).length); }, 0)
          + (((a.not_for || {}).items) || []).length;
        var lack = [];
        if (blocks === 0) lack.push('本文が空です');
        if (!a.description) lack.push('メタディスクリプションが未設定');
        if (!a.excerpt) lack.push('カード用の抜粋が未設定');
        if (lack.length) {
          toast('公開できません：' + lack.join(' / '), 'err');
          log('公開を中止: ' + slug + ' → ' + lack.join(' / '), 'err');
          openEditor(a);
          return;
        }
      }
      a.published = !a.published; renderList();
      toast(a.published ? '公開に変更しました（未保存）' : '下書きに変更しました（未保存）');
    }
    else if ((slug = b.getAttribute('data-del'))) {
      var t = find(slug);
      if (confirm('「' + (t.list_title || t.title) + '」を削除します。\n保存するとサイトからも記事ページが削除されます。よろしいですか？')) {
        articles = articles.filter(function (x) { return x.slug !== slug; });
        if (editing && editing.slug === slug) editing = null;
        renderList(); toast('削除しました（保存で確定）');
      }
    }
  });

  function find(slug) {
    return articles.filter(function (a) { return a.slug === slug; })[0];
  }

  /* ---------------------------------------------------- 繰り返しフィールド */
  function repeater(containerId, values, placeholder, multiline) {
    var box = $(containerId);
    box.innerHTML = '';
    (values || []).forEach(function (v) { addRow(box, v, placeholder, multiline); });
    if (!values || !values.length) addRow(box, '', placeholder, multiline);
  }
  function addRow(box, val, placeholder, multiline) {
    var d = document.createElement('div');
    d.className = 'repeat-item';
    var field = multiline
      ? '<textarea rows="2" placeholder="' + (placeholder || '') + '"></textarea>'
      : '<input type="text" placeholder="' + (placeholder || '') + '">';
    d.innerHTML = field + '<button type="button" class="rm" aria-label="削除">×</button>';
    d.querySelector(multiline ? 'textarea' : 'input').value = val || '';
    d.querySelector('.rm').addEventListener('click', function () { d.remove(); });
    box.appendChild(d);
  }
  function readRepeater(containerId) {
    return Array.prototype.map.call(
      $(containerId).querySelectorAll('input, textarea'),
      function (el) { return el.value.trim(); }
    ).filter(Boolean);
  }

  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-add]'); if (!b) return;
    var k = b.getAttribute('data-add');
    if (k === 'voices') addVoice({});
    else if (k === 'scenes') addScene({});
    else if (k === 'next') addNext({});
    else addRow($('r-' + k), '', '', false);
  });

  /* ---- 生活シーン ---- */
  function addScene(v) {
    var d = document.createElement('div');
    d.className = 'card';
    d.style.background = '#FBFCFE';
    d.innerHTML =
      '<label>シーンの見出し</label>' +
      '<input type="text" data-s="title" placeholder="満員電車で、音量を上げずに音楽が聴けるようになる">' +
      '<label>説明<span class="opt">購入前後で何が変わるかを具体的に</span></label>' +
      '<textarea rows="3" data-s="text"></textarea>' +
      '<div class="btn-bar"><button type="button" class="btn btn-danger rms" style="min-height:36px;font-size:12.5px;">このシーンを削除</button></div>';
    $('r-scenes').appendChild(d);
    Object.keys(v || {}).forEach(function (k) {
      var el = d.querySelector('[data-s="' + k + '"]');
      if (el) el.value = v[k];
    });
    d.querySelector('.rms').addEventListener('click', function () { d.remove(); });
  }
  function readScenes() {
    return Array.prototype.map.call($('r-scenes').children, function (d) {
      var o = {};
      Array.prototype.forEach.call(d.querySelectorAll('[data-s]'), function (el) {
        o[el.getAttribute('data-s')] = el.value.trim();
      });
      return o;
    }).filter(function (o) { return o.title || o.text; });
  }

  /* ---- 次に困りそうなこと ---- */
  function addNext(v) {
    var d = document.createElement('div');
    d.className = 'card';
    d.style.background = '#FBFCFE';
    d.innerHTML =
      '<label>次に起きる問題</label>' +
      '<input type="text" data-n="title" placeholder="付属イヤーピースが耳に合わない">' +
      '<label>説明</label>' +
      '<textarea rows="3" data-n="text"></textarea>' +
      '<div class="row c2">' +
        '<div><label>リンクの文言<span class="opt">任意</span></label><input type="text" data-n="link_label" placeholder="イヤーピースの選び方を見る"></div>' +
        '<div><label>リンク先<span class="opt">実在する記事のみ</span></label><input type="text" data-n="link_url" placeholder="articles/xxx.html"></div>' +
      '</div>' +
      '<div class="btn-bar"><button type="button" class="btn btn-danger rmn" style="min-height:36px;font-size:12.5px;">この項目を削除</button></div>';
    $('r-next').appendChild(d);
    Object.keys(v || {}).forEach(function (k) {
      var el = d.querySelector('[data-n="' + k + '"]');
      if (el) el.value = v[k];
    });
    d.querySelector('.rmn').addEventListener('click', function () { d.remove(); });
  }
  function readNext() {
    return Array.prototype.map.call($('r-next').children, function (d) {
      var o = {};
      Array.prototype.forEach.call(d.querySelectorAll('[data-n]'), function (el) {
        o[el.getAttribute('data-n')] = el.value.trim();
      });
      return o;
    }).filter(function (o) { return o.title || o.text; });
  }

  /* ---- 口コミ＋対策 ---- */
  function addVoice(v) {
    var box = $('r-voices');
    var d = document.createElement('div');
    d.className = 'card';
    d.style.background = '#FBFCFE';
    d.innerHTML =
      '<div class="row c2">' +
        '<div><label>見出し</label><input type="text" data-v="heading" placeholder="不満①「〜」"></div>' +
        '<div><label>投稿者</label><input type="text" data-v="who" placeholder="30代・男性"></div>' +
      '</div>' +
      '<div class="row c2">' +
        '<div><label>星の数<span class="opt">0で非表示</span></label><input type="number" data-v="stars" min="0" max="5" step="1"></div>' +
        '<div><label>&nbsp;</label><div class="check"><input type="checkbox" data-v="negative"><label>ネガティブな口コミとして表示</label></div></div>' +
      '</div>' +
      '<label>口コミ本文</label><textarea rows="2" data-v="text"></textarea>' +
      '<label>対策の見出し</label><input type="text" data-v="fix_title" placeholder="対策：〜する">' +
      '<label>対策の本文</label><textarea rows="3" data-v="fix"></textarea>' +
      '<div class="btn-bar"><button type="button" class="btn btn-danger rmv" style="min-height:36px;font-size:12.5px;">この口コミを削除</button></div>';
    box.appendChild(d);
    Object.keys(v || {}).forEach(function (k) {
      var el = d.querySelector('[data-v="' + k + '"]');
      if (!el) return;
      if (el.type === 'checkbox') el.checked = !!v[k]; else el.value = v[k];
    });
    d.querySelector('.rmv').addEventListener('click', function () { d.remove(); });
  }
  function readVoices() {
    return Array.prototype.map.call($('r-voices').children, function (d) {
      var o = {};
      Array.prototype.forEach.call(d.querySelectorAll('[data-v]'), function (el) {
        var k = el.getAttribute('data-v');
        o[k] = el.type === 'checkbox' ? el.checked
             : el.type === 'number' ? Number(el.value || 0)
             : el.value.trim();
      });
      return o;
    }).filter(function (o) { return o.heading || o.text; });
  }

  /* ---------------------------------------------------- エディタ */
  function blank() {
    return {
      slug: '', category: (site.categories[0] || {}).key || 'feature', sub: '',
      published: false, featured: false,
      title: '', list_title: '', description: '', excerpt: '',
      date: today(), updated: today(), tags: [], icon: '📦', thumb: '',
      asin: '', amazon_url: '', cta_label: 'Amazonで価格と詳細を確認する',
      verdict_title: '結論：', summary: [], rating: { score: 0, breakdown: '' },
      lead: '',
      not_for: { intro: '', items: [] },
      scenes: [],
      personal_note: '',
      next_problem: { intro: '', items: [] },
      pros: [], cons: [],
      spec: { intro: '', headers: [], rows: [] },
      voices_intro: '', voices: [],
      conclusion_title: 'まとめ', conclusion: ''
    };
  }

  function openEditor(a) {
    editing = a;
    $('editTitle').textContent = a.slug ? '記事を編集：' + (a.list_title || a.title) : '新しい記事を作成';

    var sel = $('f-category');
    sel.onchange = function () { fillSub(); };
    sel.innerHTML = (site.categories || []).map(function (c) {
      return '<option value="' + c.key + '">' + c.icon + ' ' + c.label + '</option>';
    }).join('');

    $('f-title').value = a.title || '';
    $('f-listTitle').value = a.list_title || '';
    $('f-slug').value = a.slug || '';
    sel.value = a.category;
    fillSub(a.sub);
    $('f-icon').value = a.icon || '';
    $('f-date').value = a.date || today();
    $('f-updated').value = a.updated || today();
    $('f-thumb').value = a.thumb || '';
    $('f-published').checked = !!a.published;
    $('f-featured').checked = !!a.featured;
    $('f-description').value = a.description || '';
    $('f-excerpt').value = a.excerpt || '';
    $('f-tags').value = (a.tags || []).join(', ');
    $('f-amazon').value = a.amazon_url || '';
    $('f-asin').value = a.asin || '';
    $('f-cta').value = a.cta_label || '';
    $('f-verdict').value = a.verdict_title || '';
    $('f-score').value = (a.rating && a.rating.score) || 0;
    $('f-breakdown').value = (a.rating && a.rating.breakdown) || '';
    $('f-lead').value = a.lead || '';
    $('f-specIntro').value = (a.spec && a.spec.intro) || '';
    $('f-specHeaders').value = ((a.spec && a.spec.headers) || []).join(', ');
    $('f-specRows').value = ((a.spec && a.spec.rows) || []).map(function (r) { return r.join(', '); }).join('\n');
    $('f-voicesIntro').value = a.voices_intro || '';
    $('f-notforIntro').value = (a.not_for && a.not_for.intro) || '';
    $('f-personalNote').value = a.personal_note || '';
    $('f-nextIntro').value = (a.next_problem && a.next_problem.intro) || '';
    $('f-conclTitle').value = a.conclusion_title || '';
    $('f-conclusion').value = a.conclusion || '';

    repeater('r-summary', a.summary, '結論の要点');
    repeater('r-notfor', (a.not_for && a.not_for.items) || [], '〜な人には向いていません');
    $('r-scenes').innerHTML = '';
    ((a.scenes) || []).forEach(addScene);
    $('r-next').innerHTML = '';
    ((a.next_problem && a.next_problem.items) || []).forEach(addNext);
    repeater('r-pros', a.pros, 'よかった点');
    repeater('r-cons', a.cons, '気になった点');
    $('r-voices').innerHTML = '';
    (a.voices || []).forEach(addVoice);

    showPanel('p-edit');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function collect() {
    var a = editing;
    a.title = $('f-title').value.trim();
    a.list_title = $('f-listTitle').value.trim() || a.title;
    a.slug = ($('f-slug').value.trim() || slugify(a.title));
    a.category = $('f-category').value;
    a.sub = $('f-sub').value;
    a.icon = $('f-icon').value.trim() || '📦';
    a.date = $('f-date').value || today();
    a.updated = $('f-updated').value || today();
    a.thumb = $('f-thumb').value.trim();
    a.published = $('f-published').checked;
    a.featured = $('f-featured').checked;
    a.description = $('f-description').value.trim();
    a.excerpt = $('f-excerpt').value.trim();
    a.tags = $('f-tags').value.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    a.amazon_url = $('f-amazon').value.trim();
    a.asin = $('f-asin').value.trim().toUpperCase();
    a.cta_label = $('f-cta').value.trim() || 'Amazonで価格を見る';
    a.verdict_title = $('f-verdict').value.trim();
    a.summary = readRepeater('r-summary');
    a.rating = { score: Number($('f-score').value || 0), breakdown: $('f-breakdown').value.trim() };
    a.lead = $('f-lead').value.trim();
    a.pros = readRepeater('r-pros');
    a.cons = readRepeater('r-cons');
    a.spec = {
      intro: $('f-specIntro').value.trim(),
      headers: $('f-specHeaders').value.split(',').map(function (s) { return s.trim(); }).filter(Boolean),
      rows: $('f-specRows').value.split('\n').map(function (line) {
        return line.split(',').map(function (s) { return s.trim(); });
      }).filter(function (r) { return r.length > 1 && r[0]; })
    };
    a.voices_intro = $('f-voicesIntro').value.trim();
    a.voices = readVoices();
    a.not_for = { intro: $('f-notforIntro').value.trim(), items: readRepeater('r-notfor') };
    a.scenes = readScenes();
    a.personal_note = $('f-personalNote').value.trim();
    a.next_problem = { intro: $('f-nextIntro').value.trim(), items: readNext() };
    a.conclusion_title = $('f-conclTitle').value.trim() || 'まとめ';
    a.conclusion = $('f-conclusion').value.trim();
    return a;
  }

  function validate(a) {
    if (!a.title) return '記事タイトルを入力してください。';
    if (!/^[a-z0-9\-]+$/.test(a.slug)) return 'スラッグは半角英小文字・数字・ハイフンのみで入力してください。';
    var dup = articles.filter(function (x) { return x.slug === a.slug && x !== a; });
    if (dup.length) return 'このスラッグは既に使われています：' + a.slug;
    if (a.asin && !/^[A-Z0-9]{10}$/.test(a.asin)) return 'ASINは10桁の英数字で入力してください。';
    if (a.published && !a.asin && !a.amazon_url) return '公開する記事にはASINかリンクのどちらかが必要です。';
    if (a.published && !a.excerpt) return '公開する記事にはカード用の抜粋が必要です。';
    if (a.published && !a.description) return '公開する記事にはメタディスクリプションが必要です。';
    return null;
  }

  /* ASIN欄にAmazonのURLを貼り付けたら、自動でASINだけ取り出す */
  (function () {
    var el = $('f-asin');
    if (!el) return;
    function convert() {
      var raw = el.value.trim();
      if (!raw || /^[A-Z0-9]{10}$/.test(raw)) return;
      var asin = extractAsin(raw);
      if (asin) {
        el.value = asin;
        toast('URLからASIN「' + asin + '」を取り出しました', 'ok');
      } else if (raw.length > 12) {
        toast('このURLからASINを取り出せませんでした', 'err');
      }
    }
    el.addEventListener('paste', function () { setTimeout(convert, 0); });
    el.addEventListener('blur', convert);
  })();

  $('btnNew').addEventListener('click', function () { openEditor(blank()); });

  $('btnApply').addEventListener('click', function () {
    if (!editing) return;
    var a = collect();
    var err = validate(a);
    if (err) { toast(err, 'err'); return; }
    if (articles.indexOf(a) === -1) articles.push(a);
    renderList();
    toast('記事を保存しました。サイトに反映するには「記事」タブで GitHubに保存 を押してください', 'ok');
    showPanel('p-articles');
  });

  $('btnDelete').addEventListener('click', function () {
    if (!editing) return;
    if (!confirm('この記事を削除します。よろしいですか？')) return;
    articles = articles.filter(function (x) { return x !== editing; });
    editing = null; renderList(); showPanel('p-articles');
    toast('削除しました（保存で確定）');
  });

  $('btnPreview').addEventListener('click', function () {
    if (!editing) return;
    var a = collect();
    var w = window.open('', '_blank');
    var rows = (a.spec.rows || []).map(function (r) {
      return '<tr><th>' + r[0] + '</th>' + r.slice(1).map(function (v) { return '<td>' + v + '</td>'; }).join('') + '</tr>';
    }).join('');
    w.document.write(
      '<!doctype html><html lang="ja"><head><meta charset="utf-8">' +
      '<meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<title>プレビュー</title><link rel="stylesheet" href="' + location.origin +
        location.pathname.replace(/admin\.html$/, '') + 'assets/style.css"></head><body>' +
      '<main class="layout"><div class="container"><article class="card-surface">' +
      '<h1 class="article-title">' + (a.title || '(無題)') + '</h1>' +
      '<section class="summary-box"><div class="summary-head">' + (a.verdict_title || '結論') + '</div>' +
      '<div class="summary-body"><ul class="summary-list">' +
        a.summary.map(function (s) { return '<li>' + s + '</li>'; }).join('') +
      '</ul></div></section>' +
      '<div class="cta-wrap"><a class="btn-amazon" href="#"><span class="cart">🛒</span>' + a.cta_label + '</a></div>' +
      '<div class="article-body"><p>' + a.lead + '</p>' +
      '<div class="proscons"><div class="pc-box pc-good"><div class="pc-head">👍 良かった点</div><ul>' +
        a.pros.map(function (s) { return '<li>' + s + '</li>'; }).join('') +
      '</ul></div><div class="pc-box pc-bad"><div class="pc-head">👎 気になった点</div><ul>' +
        a.cons.map(function (s) { return '<li>' + s + '</li>'; }).join('') +
      '</ul></div></div>' +
      (rows ? '<div class="table-scroll"><table><thead><tr>' +
        a.spec.headers.map(function (h) { return '<th>' + h + '</th>'; }).join('') +
        '</tr></thead><tbody>' + rows + '</tbody></table></div>' : '') +
      '<h2>' + a.conclusion_title + '</h2><p>' + a.conclusion + '</p>' +
      '</div></article></div></main></body></html>');
    w.document.close();
  });

  /* ---------------------------------------------------- 保存 */
  function saveArticles() {
    if (!cfg.token) {
      log('保存できません：GitHubに未接続です', 'err');
      toast('GitHubに未接続です。「接続」タブで設定してください', 'err');
      showPanel('p-connect');
      return;
    }
    var json = JSON.stringify(articles, null, 2) + '\n';
    log('記事を保存します: ' + articles.length + '件 / sha=' + (shaArticles ? shaArticles.slice(0, 7) : 'なし'));
    toast('保存中…');
    putFile('content/articles.json', b64encode(json), shaArticles,
            '記事を更新（管理画面より）')
      .then(function (res) {
        shaArticles = res.content.sha;
        log('保存完了 commit=' + (res.commit && res.commit.sha ? res.commit.sha.slice(0, 7) : '?'), 'ok');
        toast('保存しました。1〜2分でサイトに反映されます', 'ok');
      })
      .catch(function (e) {
        log('保存失敗: ' + e.message, 'err');
        toast(e.message, 'err');
      });
  }

  function saveSite(msg) {
    if (!cfg.token) { toast('先に接続タブでGitHubを設定してください', 'err'); return; }
    var json = JSON.stringify(site, null, 2) + '\n';
    toast('保存中…');
    putFile('content/site.json', b64encode(json), shaSite, msg || 'サイト設定を更新（管理画面より）')
      .then(function (res) {
        shaSite = res.content.sha;
        toast('保存しました。1〜2分でサイトに反映されます', 'ok');
      })
      .catch(function (e) { toast(e.message, 'err'); });
  }

  $('btnSaveArticles').addEventListener('click', saveArticles);
  $('btnReload').addEventListener('click', loadAll);

  /* ---------------------------------------------------- サイト設定 */
  function renderSettings() {
    $('s-name').value = site.site_name || '';
    $('s-tagline').value = site.tagline || '';
    $('s-desc').value = site.description || '';
    $('s-domain').value = site.domain || '';
    $('s-baseurl').value = site.base_url || '';
    $('s-email').value = site.email || '';
    $('s-author').value = site.author || '';
    $('s-founded').value = site.founded || '';
    var f = site.features || {};
    $('s-contact').checked = !!f.contact_form;
    $('s-contactEndpoint').value = f.contact_form_endpoint || '';
    $('s-sticky').checked = f.sticky_cta !== false;
    $('s-search').checked = f.search !== false;
    $('s-featureTh').value = String(f.feature_threshold || 5);
    $('s-imgModel').value = (site.images || {}).model || 'gemini-3.1-flash-image';
    $('s-sales').value = (((site.sales || {}).items) || []).map(function (x) {
      return [x.name, x.start, x.end, x.url || ''].join(' | ');
    }).join('\n');
    $('contactWrap').classList.toggle('hidden', !f.contact_form);
    $('s-assoc').value = (site.amazon || {}).associate_tag || '';
    var an = site.analytics || {};
    $('s-ga').value = an.ga_measurement_id || '';
    $('s-gsc').value = an.gsc_verification || '';
  }

  $('s-contact').addEventListener('change', function () {
    $('contactWrap').classList.toggle('hidden', !this.checked);
  });

  function collectSettings() {
    site.site_name = $('s-name').value.trim();
    site.tagline = $('s-tagline').value.trim();
    site.description = $('s-desc').value.trim();
    site.domain = $('s-domain').value.trim().replace(/^https?:\/\//, '').replace(/\/$/, '');
    site.base_url = ($('s-baseurl').value.trim() || 'https://' + site.domain).replace(/\/$/, '');
    site.email = $('s-email').value.trim();
    site.author = $('s-author').value.trim();
    site.founded = $('s-founded').value.trim();
    site.features = site.features || {};
    site.features.contact_form = $('s-contact').checked;
    site.features.contact_form_endpoint = $('s-contactEndpoint').value.trim();
    site.features.sticky_cta = $('s-sticky').checked;
    site.features.search = $('s-search').checked;
    site.features.feature_threshold = parseInt($('s-featureTh').value, 10) || 5;
    site.images = site.images || {};
    site.images.model = $('s-imgModel').value;
    site.sales = site.sales || {};
    site.sales.items = $('s-sales').value.split('\n').map(function (line) {
      var c = line.split('|').map(function (v) { return v.trim(); });
      if (!c[0] || !c[1] || !c[2]) return null;
      return { name: c[0], start: c[1], end: c[2], url: c[3] || '', note: '' };
    }).filter(Boolean);
  }

  $('btnSaveSettings').addEventListener('click', function () {
    collectSettings();
    if (site.features.contact_form && !site.features.contact_form_endpoint) {
      toast('フォームを有効にするには送信先URLが必要です', 'err'); return;
    }
    saveSite('サイト設定を更新（管理画面より）');
  });

  $('btnSaveAmazon').addEventListener('click', function () {
    var tag = $('s-assoc').value.trim();
    if (tag && !/^[A-Za-z0-9_-]{3,30}$/.test(tag)) { toast('アソシエイトIDの形式が正しくありません', 'err'); return; }
    site.amazon = site.amazon || {};
    site.amazon.associate_tag = tag;
    saveSite('アソシエイトIDを更新（管理画面より）');
  });

  $('btnSaveAnalytics').addEventListener('click', function () {
    var ga = $('s-ga').value.trim();
    if (ga && !/^G-[A-Z0-9]+$/i.test(ga)) { toast('測定IDは G- から始まる形式です', 'err'); return; }
    site.analytics = site.analytics || {};
    site.analytics.ga_measurement_id = ga;
    site.analytics.gsc_verification = $('s-gsc').value.trim().replace(/^.*content=["']?/, '').replace(/["'].*$/, '');
    saveSite('解析タグを更新（管理画面より）');
  });

  /* ---------------------------------------------------- 画像圧縮 */
  function compress(file, maxW, quality, mime) {
    return new Promise(function (resolve, reject) {
      var img = new Image();
      var url = URL.createObjectURL(file);
      img.onload = function () {
        var scale = Math.min(1, maxW / img.naturalWidth);
        var w = Math.round(img.naturalWidth * scale);
        var h = Math.round(img.naturalHeight * scale);
        var cv = document.createElement('canvas');
        cv.width = w; cv.height = h;
        var ctx = cv.getContext('2d');
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(img, 0, 0, w, h);
        cv.toBlob(function (blob) {
          URL.revokeObjectURL(url);
          if (!blob) { reject(new Error('変換に失敗しました')); return; }
          var ext = mime === 'image/webp' ? 'webp' : 'jpg';
          var name = file.name.replace(/\.[^.]+$/, '').toLowerCase()
                      .replace(/[^a-z0-9\-]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '')
                      || 'image';
          resolve({
            name: name + '-' + Date.now().toString(36) + '.' + ext,
            blob: blob, w: w, h: h,
            before: file.size, after: blob.size,
            preview: URL.createObjectURL(blob)
          });
        }, mime, quality);
      };
      img.onerror = function () { URL.revokeObjectURL(url); reject(new Error('画像を読み込めません')); };
      img.src = url;
    });
  }

  function kb(n) { return (n / 1024).toFixed(0) + 'KB'; }

  function handleFiles(files) {
    var maxW = Number($('imgMaxW').value) || 1200;
    var q = Number($('imgQuality').value) || 0.82;
    var mime = $('imgFormat').value;
    var jobs = Array.prototype.map.call(files, function (f) {
      return compress(f, maxW, q, mime);
    });
    Promise.all(jobs).then(function (list) {
      pendingImages = pendingImages.concat(list);
      renderPreviews();
      var saved = list.reduce(function (s, i) { return s + (i.before - i.after); }, 0);
      toast(list.length + '枚を圧縮しました（合計 ' + kb(saved) + ' 削減）', 'ok');
    }).catch(function (e) { toast(e.message, 'err'); });
  }

  function renderPreviews() {
    var box = $('imgPreview');
    box.innerHTML = pendingImages.map(function (i) {
      return '<figure><img src="' + i.preview + '" alt="">' +
             i.w + '×' + i.h + '<br>' + kb(i.before) + ' → <b>' + kb(i.after) + '</b></figure>';
    }).join('');
    $('btnUploadImages').disabled = pendingImages.length === 0;
  }

  $('imgDrop').addEventListener('click', function () { $('imgInput').click(); });
  $('imgInput').addEventListener('change', function () { handleFiles(this.files); this.value = ''; });
  ['dragenter', 'dragover'].forEach(function (ev) {
    $('imgDrop').addEventListener(ev, function (e) { e.preventDefault(); this.classList.add('over'); });
  });
  ['dragleave', 'drop'].forEach(function (ev) {
    $('imgDrop').addEventListener(ev, function (e) { e.preventDefault(); this.classList.remove('over'); });
  });
  $('imgDrop').addEventListener('drop', function (e) {
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
  });
  $('btnClearImages').addEventListener('click', function () {
    pendingImages = []; renderPreviews();
  });

  $('btnUploadImages').addEventListener('click', function () {
    if (!cfg.token) { toast('先に接続タブでGitHubを設定してください', 'err'); return; }
    toast('アップロード中…');
    var paths = [];
    var chain = Promise.resolve();
    pendingImages.forEach(function (img) {
      chain = chain.then(function () {
        return new Promise(function (res, rej) {
          var fr = new FileReader();
          fr.onload = function () {
            var b64 = fr.result.split(',')[1];
            putFile('assets/img/' + img.name, b64, null, '画像を追加：' + img.name)
              .then(function () { paths.push('assets/img/' + img.name); res(); })
              .catch(rej);
          };
          fr.onerror = rej;
          fr.readAsDataURL(img.blob);
        });
      });
    });
    chain.then(function () {
      pendingImages = []; renderPreviews();
      $('imgPreview').innerHTML =
        '<div class="note"><b>アップロード完了。以下のパスをアイキャッチ欄に貼り付けてください：</b><br>' +
        paths.map(function (p) { return '<code>' + p + '</code>'; }).join('<br>') + '</div>';
      toast('アップロードしました', 'ok');
    }).catch(function (e) { toast(e.message, 'err'); });
  });

  /* ---------------------------------------------------- 接続 */
  function loadCfg() {
    try {
      var s = JSON.parse(localStorage.getItem(LS) || '{}');
      cfg.owner = s.owner || ''; cfg.repo = s.repo || '';
      cfg.branch = s.branch || 'main'; cfg.token = s.token || '';
    } catch (e) { /* noop */ }
    $('g-owner').value = cfg.owner; $('g-repo').value = cfg.repo;
    $('g-branch').value = cfg.branch; $('g-token').value = cfg.token;
  }

  $('btnConnect').addEventListener('click', function () {
    cfg.owner = $('g-owner').value.trim();
    cfg.repo = $('g-repo').value.trim();
    cfg.branch = $('g-branch').value.trim() || 'main';
    cfg.token = $('g-token').value.trim();
    if (!cfg.owner || !cfg.repo || !cfg.token) { toast('すべての項目を入力してください', 'err'); return; }
    try { localStorage.setItem(LS, JSON.stringify(cfg)); } catch (e) { /* noop */ }
    loadAll().then(function () { showPanel('p-articles'); });
  });

  $('btnTest').addEventListener('click', function () {
    var owner = $('g-owner').value.trim();
    var repo = $('g-repo').value.trim();
    var branch = $('g-branch').value.trim() || 'main';
    var token = $('g-token').value.trim();
    if (!owner || !repo || !token) { toast('ユーザー名・リポジトリ名・トークンを入力してください', 'err'); return; }

    log('---- 接続テスト開始 ----');
    log('owner=' + owner + ' repo=' + repo + ' branch=' + branch + ' token=' + token.slice(0, 8) + '…');

    fetch('https://api.github.com/user', {
      headers: { 'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json' }
    }).then(function (r) {
      log('1. トークン確認 → HTTP ' + r.status, r.ok ? 'ok' : 'err');
      if (!r.ok) throw new Error('トークンが無効です（HTTP ' + r.status + '）');
      return r.json();
    }).then(function (u) {
      log('   ログイン中: ' + u.login, 'ok');
      return fetch('https://api.github.com/repos/' + owner + '/' + repo, {
        headers: { 'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json' }
      });
    }).then(function (r) {
      log('2. リポジトリ確認 → HTTP ' + r.status, r.ok ? 'ok' : 'err');
      if (!r.ok) throw new Error('リポジトリが見つかりません（HTTP ' + r.status + '）');
      return r.json();
    }).then(function (repoInfo) {
      log('   ' + repoInfo.full_name + ' / 既定ブランチ=' + repoInfo.default_branch, 'ok');
      if (repoInfo.default_branch !== branch) {
        log('   ⚠ 入力したブランチ(' + branch + ')が既定(' + repoInfo.default_branch + ')と異なります', 'err');
      }
      if (repoInfo.permissions && !repoInfo.permissions.push) {
        log('   ⚠ 書き込み権限がありません。トークンのスコープを確認してください', 'err');
      }
      return fetch('https://api.github.com/repos/' + owner + '/' + repo +
                   '/contents/content/articles.json?ref=' + encodeURIComponent(branch), {
        headers: { 'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json' }
      });
    }).then(function (r) {
      log('3. articles.json 確認 → HTTP ' + r.status, r.ok ? 'ok' : 'err');
      if (!r.ok) throw new Error('content/articles.json が見つかりません（HTTP ' + r.status + '）');
      return r.json();
    }).then(function (f) {
      log('   sha=' + f.sha.slice(0, 7) + ' size=' + f.size + 'バイト', 'ok');
      log('---- ✅ すべて正常。「接続する」を押してください ----', 'ok');
      toast('接続テスト成功', 'ok');
    }).catch(function (e) {
      log('---- ❌ ' + e.message + ' ----', 'err');
      toast(e.message, 'err');
    });
  });

  $('btnClearLog').addEventListener('click', function () {
    document.getElementById('logBox').textContent = 'まだ通信していません。';
  });

  $('btnDisconnect').addEventListener('click', function () {
    try { localStorage.removeItem(LS); } catch (e) { /* noop */ }
    cfg = { owner: '', repo: '', branch: 'main', token: '' };
    $('g-token').value = '';
    setConn('', '未接続');
    toast('接続を解除しました');
  });

  /* ---------------------------------------------------- 書き出し / 読み込み */
  $('btnExportArticles').addEventListener('click', function () {
    download('articles.json', JSON.stringify(articles, null, 2) + '\n');
  });
  $('btnExportSite').addEventListener('click', function () {
    collectSettings();
    download('site.json', JSON.stringify(site, null, 2) + '\n');
  });
  $('btnImport').addEventListener('click', function () { $('importInput').click(); });
  $('importInput').addEventListener('change', function () {
    var f = this.files[0]; if (!f) return;
    var fr = new FileReader();
    fr.onload = function () {
      try {
        var data = JSON.parse(fr.result);
        if (Array.isArray(data)) { articles = data; renderList(); toast('記事を読み込みました', 'ok'); }
        else { site = data; renderSettings(); toast('サイト設定を読み込みました', 'ok'); }
      } catch (e) { toast('JSONの形式が不正です', 'err'); }
    };
    fr.readAsText(f);
    this.value = '';
  });

  /* ---------------------------------------------------- タブ */
  function showPanel(id) {
    Array.prototype.forEach.call(document.querySelectorAll('.panel'), function (p) {
      p.classList.toggle('is-active', p.id === id);
    });
    Array.prototype.forEach.call(document.querySelectorAll('.tab'), function (t) {
      t.classList.toggle('is-active', t.getAttribute('data-panel') === id);
    });
  }
  Array.prototype.forEach.call(document.querySelectorAll('.tab'), function (t) {
    t.addEventListener('click', function () { showPanel(t.getAttribute('data-panel')); });
  });

  function renderAll() { renderList(); renderSettings(); }

  /* ---------------------------------------------------- 離脱ガード */
  window.addEventListener('beforeunload', function (e) {
    if (!articles.length) return;
    e.preventDefault();
    e.returnValue = '';
  });

  /* ---------------------------------------------------- 起動 */
  loadCfg();
  log('管理画面を起動しました' + (cfg.token ? '（保存済みの接続情報あり）' : '（未接続）'));
  loadAll();
})();
