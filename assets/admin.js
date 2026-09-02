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
    /* t= はブラウザ／CDNのキャッシュ避け。これが無いと、直前に別端末や
       GitHub上で更新した内容が古いまま読まれることがある。 */
    return api('contents/' + path + '?ref=' + encodeURIComponent(cfg.branch)
               + '&t=' + Date.now(), { allow404: true });
  }

  /* ---- ファイルの中身を取り出す ----
     GitHubの contents API は、1MBを超えるファイルだと中身を返さない
     （encoding:"none" / content:"" で返ってくる）。そのまま JSON.parse
     すると「Unexpected end of JSON input」になる。中身が空のときは
     Git の blob API から取り直す（こちらは大きいファイルも返る）。 */
  function fileText(res) {
    if (!res) return Promise.resolve('');
    if (res.content && res.encoding !== 'none') {
      return Promise.resolve(b64decode(res.content));
    }
    if (!res.sha) return Promise.resolve('');
    log('  → 1MBを超えているので blob から取り直します');
    return api('git/blobs/' + res.sha).then(function (b) {
      if (!b || !b.content) {
        throw new Error('ファイルが大きすぎて読み取れませんでした（' + (res.path || '') + '）');
      }
      return b64decode(b.content);
    });
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
        shaArticles = res[0].sha;
        shaSite     = res[1].sha;
        return Promise.all([fileText(res[0]), fileText(res[1])]);
      })
      .then(function (txt) {
        articles = JSON.parse(txt[0]);
        site     = JSON.parse(txt[1]);
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
    if (typeof fillGmArticles === 'function') fillGmArticles();
    var ul = $('articleList');
    ul.innerHTML = '';
    var cats = {};
    (site.categories || []).forEach(function (c) { cats[c.key] = c.label; });

    articles.slice().sort(function (a, b) { return a.date < b.date ? 1 : -1; })
      .forEach(function (a) {
        var li = document.createElement('li');
        li.innerHTML =
          /* アイキャッチを設定していればサムネイル、無ければ絵文字 */
          (a.thumb
            ? '<span class="thumb"><img src="' + a.thumb + '" alt="" loading="lazy"></span>'
            : '<span class="ico">' + (a.icon || '📦') + '</span>') +
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
  /* pair を立てた枠は、1項目が {title, text} の組になる。
     結論の要点と「買わないほうがいい人」がこれにあたる。
     組のまま扱わないと、保存のときに文字列へ潰れて
     記事に [object Object] と出てしまう。 */
  function repeater(containerId, values, placeholder, multiline, pair) {
    var box = $(containerId);
    box.innerHTML = '';
    box.setAttribute('data-pair', pair ? '1' : '');
    (values || []).forEach(function (v) { addRow(box, v, placeholder, multiline, pair); });
    if (!values || !values.length) addRow(box, '', placeholder, multiline, pair);
  }
  function addRow(box, val, placeholder, multiline, pair) {
    if (pair === undefined) pair = box.getAttribute('data-pair') === '1';
    var d = document.createElement('div');
    d.className = 'repeat-item' + (pair ? ' is-pair' : '');
    var title = '', text = '';
    if (val && typeof val === 'object') {
      title = val.title || '';
      text = val.text || '';
    } else {
      text = val || '';
    }
    var field = pair
      ? '<div class="rp-pair">'
        + '<input type="text" class="rp-title" placeholder="見出し（空でも可）">'
        + '<textarea class="rp-text" rows="2" placeholder="' + (placeholder || '') + '"></textarea>'
        + '</div>'
      : (multiline
          ? '<textarea rows="2" placeholder="' + (placeholder || '') + '"></textarea>'
          : '<input type="text" placeholder="' + (placeholder || '') + '">');
    d.innerHTML = field + '<button type="button" class="rm" aria-label="削除">×</button>';
    if (pair) {
      d.querySelector('.rp-title').value = title;
      d.querySelector('.rp-text').value = text;
    } else {
      d.querySelector(multiline ? 'textarea' : 'input').value = text;
    }
    d.querySelector('.rm').addEventListener('click', function () { d.remove(); });
    box.appendChild(d);
  }
  /* 箇条書き1項目のHTML。build.py の li_html と同じ組み立て方にする。 */
  function liHtml(x) {
    if (x && typeof x === 'object') {
      var t = (x.title || '').trim(), b = (x.text || x.body || '').trim();
      if (t && b) return '<b class="li-t">' + t + '</b><span class="li-b">' + b + '</span>';
      return t || b;
    }
    return String(x == null ? '' : x);
  }

  function readRepeater(containerId) {
    var box = $(containerId);
    if (box.getAttribute('data-pair') === '1') {
      return Array.prototype.map.call(box.querySelectorAll('.repeat-item'),
        function (row) {
          var t = (row.querySelector('.rp-title') || {}).value || '';
          var b = (row.querySelector('.rp-text') || {}).value || '';
          t = t.trim(); b = b.trim();
          if (!t && !b) return null;
          return t ? { title: t, text: b } : b;   /* 見出しが無ければ文字列のまま */
        }).filter(Boolean);
    }
    return Array.prototype.map.call(
      box.querySelectorAll('input, textarea'),
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
      good_for: { intro: '', items: [] },
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

  /* ---- 段落まわりの変換 ----------------------------------------
     JSON側は「文字列 or 文字列の配列」を受け取る。編集画面では
     空行区切りのテキストとして扱い、保存時に配列へ戻す。 */
  function toText(v) {
    if (!v) return '';
    return (Array.isArray(v) ? v : [v]).join('\n\n');
  }
  function toParas(text) {
    var list = String(text || '').split(/\n\s*\n/)
      .map(function (s) { return s.trim(); })
      .filter(Boolean);
    if (!list.length) return '';
    return list.length === 1 ? list[0] : list;
  }

  /* 本文セクションを、編集しやすい一枚のテキストにする。
       ## 見出し
       段落…（空行区切り）
       > 分析コラム枠
  */
  function sectionsToText(list) {
    return (list || []).map(function (sec) {
      var out = '## ' + (sec.heading || '');
      var paras = (Array.isArray(sec.paras) ? sec.paras : [sec.paras || '']).filter(Boolean);
      if (paras.length) out += '\n\n' + paras.join('\n\n');
      if (sec.aside) out += '\n\n> ' + sec.aside;
      return out;
    }).join('\n\n');
  }
  function textToSections(text, prev) {
    var out = [];
    String(text || '').split(/^##\s*/m).forEach(function (chunk) {
      chunk = chunk.trim();
      if (!chunk) return;
      var lines = chunk.split(/\n\s*\n/).map(function (s) { return s.trim(); }).filter(Boolean);
      var heading = lines.shift() || '';
      var sec = { heading: heading, paras: [] };
      lines.forEach(function (l) {
        if (l.charAt(0) === '>') sec.aside = l.replace(/^>\s*/, '');
        else sec.paras.push(l);
      });
      /* コラム枠の見出し語は編集画面に出していないので、
         元の記事に付いていたものを引き継ぐ */
      var old = (prev || [])[out.length];
      if (sec.aside && old && old.aside_label) sec.aside_label = old.aside_label;
      out.push(sec);
    });
    return out;
  }

  /* 比較した商品。1行1商品を縦棒で区切って書く。
     商品名 | メーカー | 価格 | ASIN | 記事スラッグ | 一言 | イチオシ表記 */
  var PD_KEYS = ['name', 'maker', 'price', 'asin', 'slug', 'note', 'pick'];

  function pdToText(list) {
    return (list || []).map(function (it) {
      return PD_KEYS.map(function (k) { return it[k] || ''; })
        .join(' | ').replace(/(\s*\|\s*)+$/, '');
    }).join('\n');
  }
  function textToPd(text) {
    return String(text || '').split('\n')
      .map(function (line) { return line.trim(); })
      .filter(Boolean)
      .map(function (line) {
        var cols = line.split('|').map(function (c) { return c.trim(); });
        var o = {};
        PD_KEYS.forEach(function (k, i) { if (cols[i]) o[k] = cols[i]; });
        return o;
      })
      .filter(function (o) { return o.name; });
  }

  /* 「この商品の強み」は {title, text} の並び。編集画面では
     「## 見出し」＋続く段落、という同じ書き方で扱う。 */
  function hlToText(list) {
    return (list || []).map(function (it) {
      return '## ' + (it.title || '') + '\n' + (it.text || '');
    }).join('\n\n');
  }
  function textToHl(text) {
    var out = [];
    String(text || '').split(/^##\s*/m).forEach(function (c) {
      c = c.trim();
      if (!c) return;
      var nl = c.indexOf('\n');
      var title = nl < 0 ? c : c.slice(0, nl).trim();
      var body = nl < 0 ? '' : c.slice(nl + 1).replace(/\s*\n\s*/g, ' ').trim();
      out.push({ title: title, text: body });
    });
    return out;
  }

  /* 選んだカテゴリーに合わせてサブカテゴリーの選択肢を入れ替える。
     content/site.json の categories[].sub[] をそのまま並べる。 */
  function fillSub(want) {
    var sub = $('f-sub');
    if (!sub) return;
    var key = $('f-category').value;
    var cat = (site.categories || []).filter(function (c) { return c.key === key; })[0];
    var list = (cat && cat.sub) || [];
    sub.innerHTML = '<option value="">（指定なし）</option>' + list.map(function (sc) {
      return '<option value="' + sc.key + '">' + sc.label + '</option>';
    }).join('');
    /* 記事に付いていた値を選び直す。別カテゴリーへ移した場合は空に戻る。 */
    sub.value = want || '';
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
    $('f-kind').value = a.kind || (a.category === 'feature' ? 'roundup' : 'review');
    $('f-icon').value = a.icon || '';
    $('f-date').value = a.date || today();
    $('f-updated').value = a.updated || today();
    $('f-thumb').value = a.thumb || '';
    $('f-imageAi').checked = !!a.image_ai;
    ecPreview();
    $('f-published').checked = !!a.published;
    $('f-featured').checked = !!a.featured;
    $('f-description').value = a.description || '';
    $('f-excerpt').value = a.excerpt || '';
    $('f-tags').value = (a.tags || []).join(', ');
    $('f-amazon').value = a.amazon_url || '';
    $('f-rakuten').value = a.rakuten_url || '';
    $('f-yahoo').value = a.yahoo_url || '';
    $('f-ctapos').value = a.cta_position || 'spec';
    $('f-asin').value = a.asin || '';
    $('f-jan').value = a.jan || '';
    $('f-official').value = a.official_url || '';
    $('f-cta').value = a.cta_label || '';
    $('f-verdict').value = a.verdict_title || '';
    $('f-score').value = (a.rating && a.rating.score) || 0;
    $('f-breakdown').value = (a.rating && a.rating.breakdown) || '';
    $('f-lead').value = toText(a.lead);
    $('f-sections').value = sectionsToText(a.sections);
    $('f-products').value = pdToText(a.products);
    $('f-productsIntro').value = toText(a.products_intro);
    $('f-specIntro').value = (a.spec && a.spec.intro) || '';
    $('f-specRead').value = toText(a.spec && a.spec.read);
    $('f-specHeaders').value = ((a.spec && a.spec.headers) || []).join(', ');
    $('f-specRows').value = ((a.spec && a.spec.rows) || []).map(function (r) { return r.join(', '); }).join('\n');
    $('f-voicesIntro').value = a.voices_intro || '';
    $('f-highlights').value = hlToText(a.highlights && a.highlights.items);
    $('f-notforIntro').value = (a.not_for && a.not_for.intro) || '';
    $('f-notforAfter').value = toText(a.not_for && a.not_for.after);
    $('f-personalNote').value = a.personal_note || '';
    $('f-nextIntro').value = (a.next_problem && a.next_problem.intro) || '';
    $('f-conclTitle').value = a.conclusion_title || '';
    $('f-conclusion').value = toText(a.conclusion);

    repeater('r-summary', a.summary, '結論の要点', true, true);
    repeater('r-notfor', (a.not_for && a.not_for.items) || [],
             '〜な人には向いていません', true, true);
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
    /* 空欄なら商品名から作る。日本語だけのタイトルでも
       時刻の数字が並んだURLにならないよう draftSlug に任せる。 */
    var taken = {};
    articles.forEach(function (x) { if (x !== a && x.slug) taken[x.slug] = true; });
    a.slug = ($('f-slug').value.trim() || draftSlug(a.title, a.category, taken));
    a.category = $('f-category').value;
    a.sub = $('f-sub').value;
    a.kind = $('f-kind').value;
    a.icon = $('f-icon').value.trim() || '📦';
    a.date = $('f-date').value || today();
    a.updated = $('f-updated').value || today();
    a.thumb = $('f-thumb').value.trim();
    if ($('f-imageAi').checked && a.thumb) a.image_ai = true;
    else delete a.image_ai;
    a.published = $('f-published').checked;
    a.featured = $('f-featured').checked;
    a.description = $('f-description').value.trim();
    a.excerpt = $('f-excerpt').value.trim();
    a.tags = $('f-tags').value.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    a.amazon_url = $('f-amazon').value.trim();
    /* 空欄のショップは項目ごと消す（ボタンを出さないため） */
    var rk = $('f-rakuten').value.trim();
    var yh = $('f-yahoo').value.trim();
    if (rk) a.rakuten_url = rk; else delete a.rakuten_url;
    if (yh) a.yahoo_url = yh; else delete a.yahoo_url;
    /* 中間ボタンの位置。既定（spec）のときは項目を持たせない */
    var cp = $('f-ctapos').value;
    if (cp && cp !== 'spec') a.cta_position = cp; else delete a.cta_position;
    a.asin = $('f-asin').value.trim().toUpperCase();
    /* JANコード。数字だけ残す（ハイフンや空白を貼られても通す） */
    var jan = $('f-jan').value.replace(/[^0-9]/g, '');
    if (jan) a.jan = jan; else delete a.jan;
    var official = $('f-official').value.trim();
    if (official) a.official_url = official; else delete a.official_url;
    a.cta_label = $('f-cta').value.trim() || 'Amazonで価格を見る';
    a.verdict_title = $('f-verdict').value.trim();
    a.summary = readRepeater('r-summary');
    a.rating = { score: Number($('f-score').value || 0), breakdown: $('f-breakdown').value.trim() };
    a.lead = toParas($('f-lead').value);
    a.sections = textToSections($('f-sections').value, a.sections);
    a.pros = readRepeater('r-pros');
    a.cons = readRepeater('r-cons');
    var pd = textToPd($('f-products').value);
    if (pd.length) {
      a.products = pd;
      a.products_intro = toParas($('f-productsIntro').value);
    } else {
      delete a.products;
      delete a.products_intro;
    }
    a.spec = {
      intro: $('f-specIntro').value.trim(),
      read: toParas($('f-specRead').value),
      headers: $('f-specHeaders').value.split(',').map(function (s) { return s.trim(); }).filter(Boolean),
      rows: $('f-specRows').value.split('\n').map(function (line) {
        return line.split(',').map(function (s) { return s.trim(); });
      }).filter(function (r) { return r.length > 1 && r[0]; })
    };
    a.voices_intro = $('f-voicesIntro').value.trim();
    a.voices = readVoices();
    var hl = textToHl($('f-highlights').value);
    if (hl.length) {
      a.highlights = a.highlights || {};
      a.highlights.items = hl;
    } else {
      delete a.highlights;
    }
    a.not_for = { intro: $('f-notforIntro').value.trim(),
                  after: toParas($('f-notforAfter').value),
                  items: readRepeater('r-notfor') };
    a.scenes = readScenes();
    a.personal_note = $('f-personalNote').value.trim();
    a.next_problem = { intro: $('f-nextIntro').value.trim(), items: readNext() };
    a.conclusion_title = $('f-conclTitle').value.trim() || 'まとめ';
    a.conclusion = toParas($('f-conclusion').value);
    return a;
  }

  function validate(a) {
    if (!a.title) return '記事タイトルを入力してください。';
    if (!/^[a-z0-9\-]+$/.test(a.slug)) return 'スラッグは半角英小文字・数字・ハイフンのみで入力してください。';
    var dup = articles.filter(function (x) { return x.slug === a.slug && x !== a; });
    if (dup.length) return 'このスラッグは既に使われています：' + a.slug;
    if (a.asin && !/^[A-Z0-9]{10}$/.test(a.asin)) return 'ASINは10桁の英数字で入力してください。';
    /* 販売先は3モールのどれか1つでよい。楽天やYahoo!だけで買える商品もある
       （build.py の shop_links と同じ判定にそろえる） */
    if (a.published && !a.asin && !a.amazon_url && !a.rakuten_url && !a.yahoo_url)
      return '公開する記事には、販売先のリンク（ASIN・Amazon・楽天・Yahoo!のどれか1つ）が必要です。';
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
    toast('記事を保存しました。記事一覧の「変更をまとめて公開」でサイトに反映されます', 'ok');
    showPanel('p-articles');
    /* 画像がまだ無い記事は、その場でAIに作らせる（キーがあるときだけ） */
    if ($('f-autoImg') && $('f-autoImg').value === 'auto' && !a.thumb) autoImage(a);
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
        a.summary.map(function (s) { return '<li>' + liHtml(s) + '</li>'; }).join('') +
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

  /* ---------------------------------------------------- サイトプレビュー */
  /* 公開中のページを枠の中に読み込み、まだ公開していない内容を
     上から当てて見せる。ビルドを走らせずに見た目を確かめるための機能。
     ページの骨組みは公開時に作られるので、ここで差し替えられるのは
     articles.json 由来の部分（カードの見出し・抜粋・画像・バッジ）だけ。 */
  var pvReady = false;
  var pvWidth = 1440;

  function pvBase() { return location.pathname.replace(/admin(\.html)?$/, ''); }

  function pvFillPages() {
    var sel = $('pvPage');
    var opts = [['', 'トップページ'], ['new.html', '新着記事'], ['ranking.html', 'アクセスランキング']];
    (site.categories || []).forEach(function (c) {
      opts.push(['category-' + c.key + '.html', 'カテゴリー：' + c.label]);
    });
    articles.filter(function (a) { return a.published; })
      .sort(function (x, y) { return x.date < y.date ? 1 : -1; })
      .forEach(function (a) {
        opts.push(['articles/' + a.slug + '.html', '記事：' + (a.list_title || a.title)]);
      });
    sel.innerHTML = opts.map(function (o) {
      return '<option value="' + o[0] + '">' + o[1] + '</option>';
    }).join('');
  }

  var KIND_JA = { review: 'レビュー', roundup: '特集', guide: '選び方' };

  /* 未公開の内容をページへ当てる。iframe は同じドメインなので中を触れる。 */
  function pvPatch(doc) {
    var bySlug = {};
    articles.forEach(function (a) { bySlug[a.slug] = a; });
    var n = 0;

    Array.prototype.forEach.call(doc.querySelectorAll('.card[data-slug]'), function (card) {
      var a = bySlug[card.getAttribute('data-slug')];
      if (!a) return;
      n++;
      var t = card.querySelector('.card-title a');
      if (t) t.textContent = a.list_title || a.title || '';
      var d = card.querySelector('.card-desc');
      if (d) d.textContent = a.excerpt || '';
      var img = card.querySelector('.card-thumb img');
      if (img && a.thumb) img.src = pvBase() + a.thumb;
      var kind = card.querySelector('.tag-kind');
      var k = a.kind || (a.category === 'feature' ? 'roundup' : 'review');
      if (kind) {
        kind.textContent = KIND_JA[k] || 'レビュー';
        kind.className = 'tag tag-kind is-' + k;
      }
    });

    var slug = (doc.location.pathname.match(/articles\/([^/.]+)/) || [])[1];
    var cur = slug && bySlug[slug];
    if (cur) {
      var h1 = doc.querySelector('.article-title');
      if (h1) { h1.textContent = cur.title || ''; n++; }
    }
    return n;
  }

  function pvSay(msg, warn) {
    var el = $('pvStatus');
    el.innerHTML = msg;
    el.className = 'pv-status' + (warn ? ' is-warn' : '');
  }

  function pvLoad() {
    var frame = $('pvFrame');
    var rel = $('pvPage').value;
    var url = pvBase() + rel + '?pv=' + Date.now();
    $('btnPvOpen').href = pvBase() + rel;
    pvSay('読み込んでいます…');
    frame.onload = function () {
      var doc;
      try { doc = frame.contentDocument; } catch (e) { doc = null; }
      if (!doc) { pvSay('プレビューを読み込めませんでした。', true); return; }
      var n = pvPatch(doc);
      var label = $('pvPage').options[$('pvPage').selectedIndex].textContent;
      pvSay(n
        ? '<b>' + label + '</b> を ' + pvWidth + 'px 幅で表示しています。'
          + '未公開の内容を <b>' + n + ' か所</b> に当てました。'
        : '<b>' + label + '</b> を ' + pvWidth + 'px 幅で表示しています。'
          + 'このページに当てる変更はありませんでした。', !n);
    };
    frame.onerror = function () { pvSay('プレビューを読み込めませんでした。', true); };
    frame.src = url;
  }

  function pvResize() {
    var w = pvWidth;
    var h = w < 500 ? 800 : 720;
    var frame = $('pvFrame'), shrink = $('pvShrink'), stage = $('pvStage');
    frame.style.width = w + 'px';
    frame.style.height = h + 'px';
    /* 枠に収まらないぶんだけ縮める。iframe の中の画面幅は w のまま。 */
    var avail = stage.clientWidth - 32;
    var scale = Math.min(1, avail / w);
    shrink.style.transform = 'scale(' + scale + ')';
    shrink.style.width = w + 'px';
    shrink.style.height = (h * scale) + 'px';
  }

  Array.prototype.forEach.call(document.querySelectorAll('.pv-dev'), function (b) {
    b.addEventListener('click', function () {
      Array.prototype.forEach.call(document.querySelectorAll('.pv-dev'), function (x) {
        x.classList.toggle('is-on', x === b);
      });
      pvWidth = Number(b.getAttribute('data-w')) || 1440;
      pvResize();
      pvLoad();
    });
  });
  $('pvPage').addEventListener('change', pvLoad);
  $('btnPvReload').addEventListener('click', pvLoad);
  window.addEventListener('resize', function () { if (pvReady) pvResize(); });

  function pvOpen() {
    if (!pvReady) { pvFillPages(); pvResize(); pvReady = true; }
    pvResize();
    pvLoad();
  }

  /* ---------------------------------------------------- 保存 */
  function saveArticles() {
    if (!cfg.token) {
      log('保存できません：GitHubに未接続です', 'err');
      toast('GitHubに未接続です。「接続」タブで設定してください', 'err');
      showPanel('p-connect');
      return Promise.reject(new Error('GitHubに未接続です'));
    }
    var json = JSON.stringify(articles, null, 2) + '\n';
    log('記事を保存します: ' + articles.length + '件 / sha=' + (shaArticles ? shaArticles.slice(0, 7) : 'なし'));
    toast('保存中…');
    return putFile('content/articles.json', b64encode(json), shaArticles,
            '記事を更新（管理画面より）')
      .then(function (res) {
        shaArticles = res.content.sha;
        log('保存完了 commit=' + (res.commit && res.commit.sha ? res.commit.sha.slice(0, 7) : '?'), 'ok');
        toast('保存しました。1〜2分でサイトに反映されます', 'ok');
      })
      .catch(function (e) {
        log('保存失敗: ' + e.message, 'err');
        toast(e.message, 'err');
        throw e;
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

  /* ---------------------------------------------------- トップの並び */
  /* トップページに出す区画の順番と、出す・出さないを決める。
     つまんで動かす操作のほかに、上下ボタンでも動かせるようにする
     （タッチ端末やキーボードだけの人でも並べ替えられるように）。 */
  var TOP_LABEL = {
    hero:       ['見出しバナー', '固定文言のガラス風タイル（内容はbuild.pyで固定）'],
    feature:    ['特集', 'カルーセルで1本ずつ'],
    'new':      ['新着記事', '4件表示、5件目は下半分が見切れる'],
    ranking:    ['よく読まれている記事／本日のお勧めのモノ', 'スマホでのみ表示（PCは右サイドに出ている）'],
    categories: ['カテゴリーから探す', '記事のあるカテゴリーを件数つきで'],
  };
  var DEFAULT_TOP = ['hero', 'feature', 'new', 'ranking', 'categories'];
  var layout = [];

  function loadLayout() {
    var saved = ((site.layout || {}).top) || [];
    var seen = {};
    layout = [];
    saved.forEach(function (it) {
      if (TOP_LABEL[it.key] && !seen[it.key]) {
        layout.push({ key: it.key, on: it.on !== false });
        seen[it.key] = 1;
      }
    });
    DEFAULT_TOP.forEach(function (k) {
      if (!seen[k]) layout.push({ key: k, on: true });
    });
    renderLayout();
  }

  function renderLayout() {
    var ul = $('layoutList');
    if (!ul) return;
    ul.innerHTML = layout.map(function (it, i) {
      var L = TOP_LABEL[it.key] || [it.key, ''];
      return '<li draggable="true" data-key="' + it.key + '"' +
        (it.on ? '' : ' class="is-off"') + '>' +
        '<span class="sl-grip" aria-hidden="true">⠿</span>' +
        '<span class="sl-order">' + (i + 1) + '</span>' +
        '<span class="sl-name">' + L[0] +
          '<span class="sl-note">' + L[1] + '</span></span>' +
        '<span class="sl-move">' +
          '<button type="button" data-up="' + i + '" title="上へ"' +
            (i === 0 ? ' disabled' : '') + '>▲</button>' +
          '<button type="button" data-down="' + i + '" title="下へ"' +
            (i === layout.length - 1 ? ' disabled' : '') + '>▼</button>' +
        '</span>' +
        '<label class="sl-on"><input type="checkbox" data-on="' + i + '"' +
          (it.on ? ' checked' : '') + '>出す</label>' +
        '</li>';
    }).join('');
  }

  function moveItem(from, to) {
    if (to < 0 || to >= layout.length) return;
    var it = layout.splice(from, 1)[0];
    layout.splice(to, 0, it);
    renderLayout();
  }

  (function bindLayout() {
    var ul = $('layoutList');
    if (!ul) return;

    ul.addEventListener('click', function (ev) {
      var b = ev.target.closest('button');
      if (!b) return;
      if (b.hasAttribute('data-up')) moveItem(Number(b.getAttribute('data-up')), Number(b.getAttribute('data-up')) - 1);
      if (b.hasAttribute('data-down')) moveItem(Number(b.getAttribute('data-down')), Number(b.getAttribute('data-down')) + 1);
    });

    ul.addEventListener('change', function (ev) {
      var c = ev.target;
      if (!c.hasAttribute || !c.hasAttribute('data-on')) return;
      layout[Number(c.getAttribute('data-on'))].on = c.checked;
      renderLayout();
    });

    /* つまんで動かす。落とした先の前に差し込む。 */
    var dragKey = null;
    ul.addEventListener('dragstart', function (ev) {
      var li = ev.target.closest('li');
      if (!li) return;
      dragKey = li.getAttribute('data-key');
      li.classList.add('is-dragging');
      ev.dataTransfer.effectAllowed = 'move';
      try { ev.dataTransfer.setData('text/plain', dragKey); } catch (e) {}
    });
    ul.addEventListener('dragend', function () {
      dragKey = null;
      Array.prototype.forEach.call(ul.children, function (x) {
        x.classList.remove('is-dragging', 'is-over');
      });
    });
    ul.addEventListener('dragover', function (ev) {
      ev.preventDefault();
      var li = ev.target.closest('li');
      Array.prototype.forEach.call(ul.children, function (x) { x.classList.remove('is-over'); });
      if (li && li.getAttribute('data-key') !== dragKey) li.classList.add('is-over');
    });
    ul.addEventListener('drop', function (ev) {
      ev.preventDefault();
      var li = ev.target.closest('li');
      if (!li || !dragKey) return;
      var to = layout.findIndex(function (x) { return x.key === li.getAttribute('data-key'); });
      var from = layout.findIndex(function (x) { return x.key === dragKey; });
      if (from < 0 || to < 0 || from === to) return;
      moveItem(from, to);
    });
  })();

  if ($('btnSaveLayout')) {
    $('btnSaveLayout').addEventListener('click', function () {
      if (!layout.filter(function (x) { return x.on; }).length) {
        toast('すべて非表示にはできません。1つ以上は出してください', 'err');
        return;
      }
      site.layout = site.layout || {};
      site.layout.top = layout.map(function (x) { return { key: x.key, on: x.on }; });
      saveSite('トップページの並びを変更（管理画面より）');
    });
  }
  if ($('btnResetLayout')) {
    $('btnResetLayout').addEventListener('click', function () {
      if (!confirm('既定の並びに戻します。よろしいですか？')) return;
      layout = DEFAULT_TOP.map(function (k) { return { key: k, on: true }; });
      renderLayout();
      toast('既定の並びに戻しました（保存で確定）');
    });
  }

  /* ---------------------------------------------------- 公開状態 */
  /* メンテナンス表示の切り替え。ヘッダーのチップにも状態を出す。 */
  function renderMaint() {
    var on = !!(site.features && site.features.maintenance);
    var chip = $('chipMaint');
    $('maintState').textContent = on ? 'メンテナンス中' : '公開中';
    chip.className = 'hchip ' + (on ? 'is-maint' : 'is-live');
  }

  $('chipMaint').addEventListener('click', function (ev) {
    ev.preventDefault();
    showPanel('p-settings');
    $('maintCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  $('btnSaveMaint').addEventListener('click', function () {
    var on = $('s-maintenance').checked;
    if (on && !confirm('サイト全体を「準備中」画面に切り替えます。よろしいですか？')) return;
    site.features = site.features || {};
    site.features.maintenance = on;
    site.maintenance_message = $('s-maintMsg').value.trim();
    renderMaint();
    saveSite(on ? 'メンテナンス表示に切り替え（管理画面より）'
                : 'メンテナンス表示を解除（管理画面より）');
  });

  /* ---------------------------------------------------- ビルド回数 */
  /* 今月ビルドが走った回数の目安。GitHub のコミット数から数える。
     画像だけのコミットには [skip ci] が付いていて走らないので、それは除く。
     数え始めは毎月1日の 00:00（この端末の時刻）。
     Cloudflare 側の実際の上限と残量は、ダッシュボードで確認する。 */
  function countDeploys() {
    if (!cfg.token) return;
    var since = new Date();
    since = new Date(since.getFullYear(), since.getMonth(), 1).toISOString();
    var q = 'commits?sha=' + encodeURIComponent(cfg.branch || 'main') +
            '&since=' + encodeURIComponent(since) + '&per_page=100';
    var total = 0, capped = false;

    /* 1ページ100件までしか返らない。月の前半でもコミットが100を超えるので、
       次のページを読みに行く。ここを読まないと、新しい100件のうち
       [skip ci] が増えるぶんだけ表示が減っていき、数が減るように見える。 */
    function page(n) {
      return api(q + '&page=' + n).then(function (list) {
        if (!Array.isArray(list)) return;
        total += list.filter(function (c) {
          var m = (c.commit && c.commit.message) || '';
          return !/\[skip ci\]|\[ci skip\]/i.test(m);
        }).length;
        if (list.length < 100) return;
        if (n >= 10) { capped = true; return; }   /* 1000件で打ち切る */
        return page(n + 1);
      });
    }

    page(1).then(function () {
      var chip = $('chipDeploy');
      $('deployCount').textContent = total + (capped ? '回以上' : ' 回');
      chip.className = 'hchip' + (total >= 900 ? ' is-danger' : total >= 600 ? ' is-warn' : '');
      chip.title = '今月ビルドが走った回数の目安（' + total + ' 回）。毎月1日に0へ戻ります。\n'
                 + '画像だけのコミットはビルドを起こさないので数えていません。\n'
                 + '実際の残量は Cloudflare ダッシュボードで確認してください。';
    }).catch(function () {});
  }

  $('chipDeploy').addEventListener('click', function (ev) {
    ev.preventDefault();
    countDeploys();
    toast('ビルド回数を数え直しました');
  });

  /* ---------------------------------------------------- サイト設定 */
  function renderSettings() {
    renderMaint();
    loadLayout();
    $('s-name').value = site.site_name || '';
    $('s-tagline').value = site.tagline || '';
    $('s-desc').value = site.description || '';
    $('s-domain').value = site.domain || '';
    $('s-baseurl').value = site.base_url || '';
    $('s-email').value = site.email || '';
    $('s-author').value = site.author || '';
    $('s-founded').value = site.founded || '';
    var f = site.features || {};
    $('s-maintenance').checked = !!f.maintenance;
    $('s-maintMsg').value = site.maintenance_message || '';
    $('s-contact').checked = !!f.contact_form;
    $('s-contactEndpoint').value = f.contact_form_endpoint || '';
    $('s-sticky').checked = f.sticky_cta !== false;
    $('s-search').checked = f.search !== false;
    $('s-featureTh').value = String(f.feature_threshold || 5);
    renderPromos();
    var ad = site.ads || {};
    $('s-adsOn').checked = !!ad.enabled;
    $('s-adsClient').value = ad.client || '';
    $('s-adsMode').value = ad.mode || 'manual';
    var sl = ad.slots || {};
    $('s-adsMid').value = sl.article_mid || '';
    $('s-adsEnd').value = sl.article_end || '';
    $('s-adsSide').value = sl.side || '';
    var au = site.automation || {};
    $('s-autoOn').checked = au.enabled !== false;
    syncAutoState();
    $('s-autoRuns').value = String(au.runs_per_week || 1);
    $('s-autoCount').value = String(au.articles_per_run || 5);
    $('s-autoPublish').checked = au.auto_publish !== false;
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

  /* 自動作成が動いているかどうかは、見出しの横にはっきり出す。
     「オフにしたつもりで動いていた」を防ぐため。 */
  function syncAutoState() {
    var el = $('s-autoState');
    if (!el) return;
    var on = $('s-autoOn').checked;
    el.textContent = on ? '有効' : '停止中';
    el.style.background = on ? 'var(--a-ok)' : 'var(--a-bad)';
    el.style.color = '#fff';
  }
  if ($('s-autoOn')) $('s-autoOn').addEventListener('change', syncAutoState);

  /* ---- ASPの広告（A8.netなど） ----
     配られたコードはそのまま持つ。置き場所と対象カテゴリーだけを添える。 */
  function promoRow(v) {
    v = v || {};
    var box = $('r-promos');
    var d = document.createElement('div');
    d.className = 'card';
    d.style.background = '#FBFCFE';
    var cats = (site.categories || []).map(function (c) {
      var on = (v.cats || []).indexOf(c.key) !== -1 ? ' selected' : '';
      return '<option value="' + c.key + '"' + on + '>' + c.label + '</option>';
    }).join('');
    d.innerHTML =
      '<div class="row c2">' +
      '  <div><label>案件の名前<span class="opt">自分用のメモ</span></label>' +
      '    <input type="text" class="pm-name" placeholder="家電レンタル○○"></div>' +
      '  <div><label>出す場所</label><select class="pm-where">' +
      '    <option value="article_end">記事の下</option>' +
      '    <option value="side">PCサイド</option>' +
      '    <option value="none">出さない（下書き）</option>' +
      '  </select></div>' +
      '</div>' +
      '<label>対象カテゴリー<span class="opt">選ばなければ全記事に出る／Ctrlキーで複数選択</span></label>' +
      '<select class="pm-cats" multiple size="4">' + cats + '</select>' +
      '<label>広告リンクのコード<span class="opt">ASPからコピーしたまま貼る／複数入れるときは --- の行で区切る</span></label>' +
      '<textarea class="pm-html" rows="4" placeholder="&lt;a href=&quot;https://px.a8.net/svt/ejp?a8mat=…&quot;&gt;…&lt;/a&gt;"></textarea>' +
      '<div class="btn-bar"><button type="button" class="btn btn-danger pm-rm" style="min-height:34px;font-size:12px;">この広告を削除</button></div>';
    d.querySelector('.pm-name').value = v.name || '';
    d.querySelector('.pm-where').value = v.where || 'article_end';
    d.querySelector('.pm-html').value = v.html || '';
    d.querySelector('.pm-rm').addEventListener('click', function () { d.remove(); });
    box.appendChild(d);
  }

  function renderPromos() {
    var box = $('r-promos');
    if (!box) return;
    box.innerHTML = '';
    ((site.promos || {}).items || []).forEach(promoRow);
  }

  function readPromos() {
    var box = $('r-promos');
    if (!box) return [];
    return Array.prototype.map.call(box.querySelectorAll('.card'), function (d) {
      var html = d.querySelector('.pm-html').value.trim();
      if (!html) return null;
      return {
        name: d.querySelector('.pm-name').value.trim(),
        where: d.querySelector('.pm-where').value,
        cats: Array.prototype.filter.call(d.querySelectorAll('.pm-cats option'),
          function (o) { return o.selected; }).map(function (o) { return o.value; }),
        html: html
      };
    }).filter(Boolean);
  }

  if ($('btnAddPromo')) {
    $('btnAddPromo').addEventListener('click', function () { promoRow({}); });
  }

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
    /* ASPの広告。配られたコードはそのまま保つ。 */
    site.promos = site.promos || {};
    if (!site.promos.label) site.promos.label = 'PR';
    site.promos.items = readPromos();

    /* 広告の設定。コードそのものは触らず、出す・出さないと置き場所だけを持つ。 */
    site.ads = site.ads || {};
    site.ads.enabled = $('s-adsOn').checked;
    site.ads.client = $('s-adsClient').value.trim();
    site.ads.mode = $('s-adsMode').value;
    site.ads.slots = {
      article_mid: $('s-adsMid').value.trim(),
      article_end: $('s-adsEnd').value.trim(),
      side: $('s-adsSide').value.trim()
    };

    /* 自動作成の設定。ワークフローは毎日まわり、tools/schedule_gate.py が
       この値を読んで実行日と本数を決める。 */
    site.automation = site.automation || {};
    site.automation.enabled = $('s-autoOn').checked;
    site.automation.runs_per_week = parseInt($('s-autoRuns').value, 10) || 1;
    site.automation.articles_per_run = parseInt($('s-autoCount').value, 10) || 5;
    site.automation.auto_publish = $('s-autoPublish').checked;
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
            putFile('assets/img/' + img.name, b64, null, '画像を追加：' + img.name + ' [skip ci]')
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
    if (id === 'p-preview') pvOpen();
    if (id === 'p-quickpost' && typeof window.fillQpCategory === 'function') window.fillQpCategory();
  }
  Array.prototype.forEach.call(document.querySelectorAll('.tab'), function (t) {
    t.addEventListener('click', function () { showPanel(t.getAttribute('data-panel')); });
  });

  var findWired = false;

  function renderAll() {
    renderList();
    renderSettings();
    /* カテゴリーの一覧は site.json が読めてからでないと作れない */
    if (!findWired && site && site.categories) { wireFind(); findWired = true; }
    if (typeof window.fillQpCategory === 'function') window.fillQpCategory();
  }

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
  countDeploys();

  /* ==================================================== アクセス状況 */
  /* content/ranking.json（GA4から自動生成）を読んで一覧にする。 */
  function loadRanking() {
    var box = $('rankingBox');
    box.textContent = '読み込み中…';
    getFile('content/ranking.json').then(function (res) {
      if (!res || res.status === 404) { box.textContent = 'まだ ranking.json がありません。'; return; }
      return fileText(res).then(function (txt) {
      var data = JSON.parse(txt);
      var views = data.views || {};
      var keys = Object.keys(views).sort(function (a, b) { return views[b] - views[a]; });
      if (!keys.length) {
        box.innerHTML = '<b>まだデータがありません。</b><br>' +
          'GA4の計測が始まってから、GitHubのSecretsに GA4_PROPERTY_ID と GA4_SA_KEY を登録すると、' +
          '毎日5:00に取り込まれます。それまではサイト側は端末ごとの閲覧回数で並びます。';
        return;
      }
      var titles = {};
      articles.forEach(function (a) { titles[a.slug] = a.list_title || a.title; });
      box.innerHTML =
        '<div style="margin-bottom:6px;">更新日：<b>' + (data.updated || '不明') + '</b>' +
        '（直近' + (data.range_days || '?') + '日）</div>' +
        '<ol style="margin:0;padding-left:1.4em;line-height:1.9;">' +
        keys.slice(0, 20).map(function (k) {
          return '<li>' + (titles[k] || k) + ' — <b>' + views[k] + '</b></li>';
        }).join('') + '</ol>';
      });
    }).catch(function (e) { box.textContent = '読み込めませんでした：' + e.message; });
  }
  $('btnLoadRanking').addEventListener('click', loadRanking);

  /* ==================================================== 画像の自動生成 */
  var GM_KEY = 'mb.geminiKey';
  var gmBlob = null;
  try {
    var savedKey = localStorage.getItem(GM_KEY);
    if (savedKey && $('gmKey')) $('gmKey').value = savedKey;
  } catch (e) { /* 使えなくても入力欄が空になるだけ */ }

  /* サブカテゴリーごとの被写体。tools/make_images.py と同じ考え方。 */
  var GM_SUBJECT = {
    'pc/monitor': ['a widescreen computer monitor', 'a wooden desk in a tidy home office'],
    'pc/input': ['a computer mouse and a low-profile keyboard', 'a wooden desk beside a closed notebook'],
    'pc/peripheral': ['a compact aluminium USB-C docking hub with cables plugged in', 'a desk next to a laptop edge'],
    'pc/network': ['a white Wi-Fi router with upright antennas', 'a shelf beside a small plant'],
    'pc/tablet': ['an e-ink reading tablet lying flat', 'a linen bedside table with a mug'],
    'pc/laptop': ['a thin silver laptop, lid open at an angle', 'a bright desk near a window'],
    'pc/storage': ['a small external SSD drive and a short cable', 'a slate grey desk surface'],
    'av/mic': ['a small wireless lavalier microphone and its charging case', 'a matte grey table'],
    'av/headphone': ['a pair of over-ear headphones resting on their side', 'a wooden desk'],
    'av/speaker': ['a fabric-covered desktop speaker', 'a shelf against a plain wall'],
    'av/tv': ['a slim projector unit facing slightly away', 'a low sideboard in a dim living room'],
    'appliance/light': ['a slim LED light fixture switched on', 'a plain ceiling or a desk edge'],
    'appliance/aircon': ['a floor-standing fan or a steam humidifier, front three-quarter view', 'a bright living room floor beside a curtain'],
    'appliance/smart': ['a small square smart home hub with a status light', 'a shelf beside a remote control'],
    'appliance/clean': ['a cordless stick vacuum standing upright', 'a wooden floor in a bright room'],
    'furniture/desk': ['an adjustable footrest under a desk', 'a wooden floor beneath a desk'],
    'furniture/chair': ['an ergonomic office chair, three-quarter view', 'a bright room with a plain wall'],
    'furniture/shelf': ['a slim metal shelving rack holding a few objects', 'beside a desk against a plain wall'],
    'furniture/bed': ['a single pillow on a made bed', 'a bedroom with soft morning light'],
    'daily/clean': ['a tall slim rubbish bin', 'a narrow gap beside a kitchen counter'],
    'daily/safety': ['a small outdoor security camera on a wall mount', 'an exterior wall under an eave'],
    'health/measure': ['a smartwatch lying flat, screen facing up', 'a wooden table beside a notebook'],
    'feature/compare': ['three unbranded consumer gadgets lined up in a row', 'a clean light grey studio surface']
  };

  /* 画像生成に送る指示文。
     文面は運営者が決めたものをそのまま使う。末尾にだけ、
     その記事の被写体と、毎回変える撮影条件を足している。
     被写体を書かないと商品と無関係な写真になり、
     撮影条件を固定すると似た絵ばかり出てくるため。 */
  var GM_VARY = {
    room: ['朝の光が入る北向きの部屋', '午後の日差しが差し込むリビング',
           '曇り空の柔らかい光が回る書斎', '窓際に観葉植物がある落ち着いた部屋',
           '木の家具でまとめた静かな寝室', '白い壁のシンプルな作業部屋'],
    angle: ['やや上からの俯瞰', '目線の高さからの斜め前方', '低い位置からの水平',
            '真横に近い角度', '斜め後方からの引き'],
    light: ['左手の窓からの自然光', '右手からの柔らかい間接光',
            '正面やや上からの拡散光', '窓を背にした逆光ぎみの光']
  };

  function pickOne(list) {
    return list[Math.floor(Math.random() * list.length)];
  }

  function gmPromptFor(a) {
    var s = GM_SUBJECT[(a.category || '') + '/' + (a.sub || '')] ||
            ['a single unbranded consumer product', 'a clean light grey studio surface'];
    return [
      '以下の条件・テイストに厳格に従って毎回新しい単独の画像を1枚作成してください。',
      '',
      '1. スタイルと質感（絶対条件）',
      '',
      'イラストや3D CG、絵画調ではなく、一眼レフカメラで撮影したような**完全にリアルな実写写真（Photorealistic）**とすること。',
      '',
      '過度なレタッチやテカテカしたAI感（ツルツルした肌や不自然な光沢）を排除し、自然な素材の質感（木目、布の繊維、光の反射など）を再現すること。',
      '',
      '2. 被写体と構成',
      '',
      '人は一切登場させないこと（人物なし・物体のみ）。',
      '',
      '存在しない架空の要素や奇抜なデザインは避け、現実にある実物のみを描写すること。',
      '',
      '背景は自然で落ち着いた室内や背景とし、主題となる物に自然にスポットが当たる構図にすること。',
      '',
      '3. 前の画像からの独立（最重要）',
      '',
      '直前の会話や過去に生成した画像（部屋の背景、家具、色合いなど）との連続性・引き継ぎ（一貫性）は完全に断ち切ること。',
      '',
      '過去の画像を参考・参照せず、毎回新しいシチュエーション・新しい背景・新しい角度で一から生成すること。',
      '',
      '4. 今回の被写体（この記事のために追記）',
      '',
      '撮影する物：' + s[0],
      '置かれている場所の目安：' + s[1],
      'ロゴや読める文字は入れないこと。ブランドの分からない一般的な製品として描くこと。',
      '横長（16:9）で出力すること。',
      '',
      '5. 今回だけの撮影条件（3の指示にしたがい、毎回変える）',
      '',
      '場所：' + pickOne(GM_VARY.room),
      '角度：' + pickOne(GM_VARY.angle),
      '光：' + pickOne(GM_VARY.light)
    ].join('\n');
  }

  function fillGmArticles() {
    var sel = $('gmArticle');
    if (!sel) return;
    sel.innerHTML = articles.map(function (a, i) {
      return '<option value="' + i + '">' + (a.thumb ? '　' : '★ ') +
             (a.list_title || a.title || a.slug) + '</option>';
    }).join('');
    sel.onchange = function () {
      var a = articles[Number(sel.value)];
      if (a) $('gmPrompt').value = gmPromptFor(a);
    };
    sel.onchange();
  }

  function b64ToBlob(b64, mime) {
    var bin = atob(b64), len = bin.length, buf = new Uint8Array(len);
    for (var i = 0; i < len; i++) buf[i] = bin.charCodeAt(i);
    return new Blob([buf], { type: mime || 'image/jpeg' });
  }

  function pickImage(data) {
    /* 応答の形が版によって違うため、画像データのある場所を順に探す */
    if (data.output_image && data.output_image.data) return data.output_image.data;
    var out = data.output || [];
    for (var i = 0; i < out.length; i++) {
      if (out[i] && out[i].type === 'image' && out[i].data) return out[i].data;
      var cont = (out[i] && out[i].content) || [];
      for (var j = 0; j < cont.length; j++) if (cont[j].data) return cont[j].data;
    }
    var cands = data.candidates || [];
    for (var k = 0; k < cands.length; k++) {
      var parts = ((cands[k].content) || {}).parts || [];
      for (var m = 0; m < parts.length; m++) {
        var inl = parts[m].inline_data || parts[m].inlineData;
        if (inl && inl.data) return inl.data;
      }
    }
    return null;
  }

  function genImage(a, key, model, promptOverride) {
    return fetch('https://generativelanguage.googleapis.com/v1beta/interactions', {
      method: 'POST',
      headers: { 'x-goog-api-key': key, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: model,
        input: [{ type: 'text', text: promptOverride || gmPromptFor(a) }],
        response_format: { type: 'image', mime_type: 'image/jpeg',
                           aspect_ratio: '16:9', image_size: '1K' }
      })
    }).then(function (r) {
      return r.json().then(function (j) {
        if (!r.ok) throw new Error((j.error && j.error.message) || ('HTTP ' + r.status));
        return j;
      });
    }).then(function (data) {
      var b64 = pickImage(data);
      if (!b64) throw new Error('応答に画像が含まれていません');
      var blob = b64ToBlob(b64, 'image/jpeg');
      return compress(new File([blob], a.slug + '.jpg', { type: 'image/jpeg' }),
                      1200, 0.8, 'image/jpeg');
    });
  }

  function saveImage(a, img) {
    var path = 'assets/img/gen/' + a.slug + '.jpg';
    return blobToB64(img.blob).then(function (b64) {
      return getFile(path).then(function (res) {
        return putFile(path, b64, res && res.sha, '記事の画像を追加（管理画面より） [skip ci]');
      });
    }).then(function () {
      a.thumb = path;
      a.image_ai = true;
      return path;
    });
  }

  $('btnGenImage').addEventListener('click', function () {
    var key = ($('gmKey').value || '').trim();
    if (!key) { toast('Gemini APIキーを入力してください', 'err'); return; }
    try { localStorage.setItem(GM_KEY, key); } catch (e) {}
    var a = articles[Number($('gmArticle').value)];
    if (!a) return;
    var box = $('gmResult');
    box.textContent = '生成中…（10〜30秒かかります）';
    $('btnGenImage').disabled = true;
    $('btnUseImage').disabled = true;

    genImage(a, key, $('gmModel').value, $('gmPrompt').value).then(function (img) {
      gmBlob = { img: img, article: a };
      box.innerHTML = '<img src="' + img.preview + '" alt="" style="max-width:100%;border-radius:8px;">' +
        '<div style="margin-top:6px;">' + img.w + '×' + img.h + '／' + kb(img.after) + '</div>' +
        '<div>内容を確認して、問題なければ下のボタンで保存してください。</div>';
      $('btnUseImage').disabled = false;
    }).catch(function (e) {
      box.textContent = '失敗しました：' + e.message;
    }).then(function () { $('btnGenImage').disabled = false; });
  });

  $('btnUseImage').addEventListener('click', function () {
    if (!gmBlob) return;
    var a = gmBlob.article, img = gmBlob.img;
    $('btnUseImage').disabled = true;
    saveImage(a, img).then(function (path) {
      toast('画像を保存しました。記事を保存して公開すると反映されます', 'ok');
      $('gmResult').textContent = '保存しました：' + path;
      renderList();
    }).catch(function (e) {
      toast(e.message, 'err');
      $('btnUseImage').disabled = false;
    });
  });

  /* 記事の保存時に呼ばれる自動生成。失敗しても保存自体は妨げない。 */
  function autoImage(a) {
    var key = '';
    try { key = localStorage.getItem(GM_KEY) || ''; } catch (e) {}
    if (!key) {
      toast('画像は作りませんでした（「画像」タブでGemini APIキーを設定すると自動で作ります）');
      return;
    }
    toast('画像を作っています…', 'ok');
    genImage(a, key, ($('gmModel') && $('gmModel').value) || 'gemini-3.1-flash-image')
      .then(function (img) {
        return saveImage(a, img).then(function (path) {
          toast('画像を作って記事に設定しました：' + path, 'ok');
          renderList();
        });
      })
      .catch(function (e) {
        toast('画像は作れませんでした（' + e.message + '）。記事の保存は済んでいます', 'err');
      });
  }

  /* ---------------------------------------------------- アイキャッチ */
  /* 記事ごとのアイキャッチを、編集画面の一番上で差し替えられるようにする。
     圧縮とGitHubへの保存は「画像」タブと同じ処理を使う。 */
  function ecPreview() {
    var box = $('ecPreview');
    var path = ($('f-thumb').value || '').trim();
    if (!path) { box.innerHTML = '<span class="eyecatch-empty">画像なし</span>'; return; }
    /* 管理画面はサイト直下に置いてあるので、相対パスがそのまま使える */
    box.innerHTML = '<img src="' + path + '?t=' + Date.now() + '" alt="">';
    box.firstChild.onerror = function () {
      box.innerHTML = '<span class="eyecatch-empty">まだGitHubに反映されていません</span>';
    };
  }

  $('f-thumb').addEventListener('input', ecPreview);

  $('btnEcClear').addEventListener('click', function () {
    $('f-thumb').value = '';
    $('f-imageAi').checked = false;
    ecPreview();
    $('ecNote').textContent = 'アイキャッチを外しました。保存すると反映されます。';
  });

  $('btnEcPick').addEventListener('click', function () {
    if (!cfg.token) { toast('先に接続タブでGitHubを設定してください', 'err'); return; }
    $('ecFile').click();
  });

  $('ecFile').addEventListener('change', function () {
    var file = this.files && this.files[0];
    this.value = '';
    if (!file || !editing) return;
    var note = $('ecNote');
    note.textContent = '圧縮しています…';
    compress(file, 1200, 0.82, 'image/webp').then(function (img) {
      note.textContent = '保存しています…（' + img.w + '×' + img.h + '／' + kb(img.after) + '）';
      var path = 'assets/img/' + (editing.slug || 'article') + '-' +
                 Date.now().toString(36) + '.webp';
      return blobToB64(img.blob).then(function (b64) {
        return putFile(path, b64, null, 'アイキャッチを追加（管理画面より） [skip ci]');
      }).then(function () {
        $('f-thumb').value = path;
        $('f-imageAi').checked = false;   /* 自分で用意した画像なので断り書きは出さない */
        editing.thumb = path;
        delete editing.image_ai;
        ecPreview();
        note.innerHTML = '保存しました：<code>' + path + '</code><br>' +
          '<b>記事を保存し、記事一覧の「変更をまとめて公開」でサイトに反映されます。</b>';
        toast('アイキャッチを設定しました。記事を保存すると反映されます', 'ok');
      });
    }).catch(function (e) {
      note.textContent = '失敗しました：' + e.message;
      toast(e.message, 'err');
    });
  });

  $('btnEcGen').addEventListener('click', function () {
    if (!editing) return;
    if (!cfg.token) { toast('先に接続タブでGitHubを設定してください', 'err'); return; }
    var key = '';
    try { key = localStorage.getItem(GM_KEY) || ''; } catch (e) {}
    if (!key) { toast('「画像」タブでGemini APIキーを設定してください', 'err'); return; }
    var note = $('ecNote');
    note.textContent = '生成中…（10〜30秒かかります）';
    $('btnEcGen').disabled = true;
    genImage(editing, key, ($('gmModel') && $('gmModel').value) || 'gemini-3.1-flash-image')
      .then(function (img) { return saveImage(editing, img); })
      .then(function (path) {
        $('f-thumb').value = path;
        $('f-imageAi').checked = true;
        ecPreview();
        note.innerHTML = '作って保存しました：<code>' + path + '</code><br>' +
          '<b>記事を保存し、記事一覧の「変更をまとめて公開」でサイトに反映されます。</b>';
        toast('アイキャッチを作りました。記事を保存すると反映されます', 'ok');
      })
      .catch(function (e) {
        note.textContent = '失敗しました：' + e.message;
      })
      .then(function () { $('btnEcGen').disabled = false; });
  });

  /* タブから「編集」を外したので、一覧へ戻る手立てを用意する */
  if ($('btnBackTop')) {
    $('btnBackTop').addEventListener('click', function () { showPanel('p-articles'); });
  }

  /* エディタから、その記事1本ぶんの本文を作る */
  if ($('btnGenText')) {
    $('btnGenText').addEventListener('click', function () {
      if (!editing) { toast('先に記事を開いてください', 'err'); return; }
      /* 画面の入力を記事へ書き戻してから送る。
         そうしないと、いま直したタイトルが反映されない。 */
      collect();
      var btn = $('btnGenText');
      var label = btn.textContent;
      btn.disabled = true;
      btn.textContent = '作成中…';
      generateArticle(editing).then(function (warns) {
        if (editing.thumb) return warns;
        /* アイキャッチが無い記事は、あわせて画像も用意する */
        btn.textContent = '画像を作成中…';
        return ensureEyecatch(editing).then(function () { return warns; })
          .catch(function (err) { return warns.concat(['画像なし：' + err.message]); });
      }).then(function (warns) {
        openEditor(editing);          /* 生成結果を画面へ流し込む */
        if (warns.length) {
          toast('できましたが、確認してください：' + warns.join(' / '), 'err');
          warns.forEach(function (w) { log('  △ ' + w, 'err'); });
        } else {
          toast('本文を作りました。内容を読んでから保存してください');
        }
      }).catch(function (err) {
        toast(err.message, 'err');
      }).then(function () {
        btn.disabled = false;
        btn.textContent = label;
      });
    });
  }

  /* 編集画面の上下で同じ操作ができるようにする（長い記事で下まで行かなくて済む） */
  [['btnApplyTop', 'btnApply'],
   ['btnPreviewTop', 'btnPreview'],
   ['btnDeleteTop', 'btnDelete']].forEach(function (pair) {
    var top = $(pair[0]), bottom = $(pair[1]);
    if (top && bottom) top.addEventListener('click', function () { bottom.click(); });
  });


  /* ============================================================
     商品を探す
     ------------------------------------------------------------
     楽天市場とYahoo!ショッピングから、レビューが十分に集まっている
     商品を集めて並べる。「何を書くか」の下ごしらえまでを担当し、
     どれを書くかは人が選ぶ。APIには「読者の困りごとに答える商品か」
     が分からないため、そこは自動化しない。

     楽天のAPIはブラウザから直接呼べる（CORSを許している）。
     Yahoo!のAPIは許していないので、このサイトの /api/yahoo を通す。
     選別の考え方は tools/pick_products.py と揃えてある。
     ============================================================ */
  var FIND_KEYS = 'monobase.shopkeys';
  /* 楽天は2026年2月にAPIを刷新した。旧 app.rakuten.co.jp は停止済みで、
     認証も applicationId だけでは通らず、アクセスキーとの2点が要る。
     アクセスキーはURLに載せず、accessKey ヘッダで送る。 */
  var RAKUTEN_API =
    'https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701';
  var YAHOO_PROXY = '/api/yahoo';
  /* Amazon（PA-API v5）もブラウザからは呼べず、AWSの署名が要るので
     このサイトの /api/amazon を通す（署名は worker.js が行う）。 */
  var AMAZON_PROXY = '/api/amazon';

  /* サイトのカテゴリーと、楽天のジャンルID／Yahoo!の検索語の対応。
     tools/pick_products.py の CATEGORY_MAP と同じ内容にしておく。 */
  /* index は Amazon の SearchIndex（検索する売り場）。
     指定しないと本や食品まで混ざるので、カテゴリーごとに固定する。 */
  var CATEGORY_MAP = {
    pc:         { genre: 100026, word: 'PC周辺機器', index: 'Computers' },
    appliance:  { genre: 562637, word: '生活家電', index: 'Appliances' },
    furniture:  { genre: 100804, word: 'インテリア 収納', index: 'Furniture' },
    daily:      { genre: 215783, word: '日用品', index: 'HealthPersonalCare' },
    av:         { genre: 211742, word: 'オーディオ', index: 'Electronics' },
    camera:     { genre: 204040, word: 'カメラ', index: 'Electronics' },
    smartphone: { genre: 565004, word: 'スマートフォン アクセサリ', index: 'Electronics' },
    kitchen:    { genre: 100939, word: 'キッチン家電', index: 'KitchenAndHousewares' },
    health:     { genre: 100938, word: '健康計測', index: 'HealthPersonalCare' },
    beauty:     { genre: 100939, word: '美容家電', index: 'Beauty' },
    pet:        { genre: 101213, word: 'ペット用品', index: 'PetSupplies' }
  };
  /* travel（旅行・トラベル）は CATEGORY_MAP に入れていない。
     入れると「商品を探す」の自動ローテーションが、記事0本の旅行に
     張り付いてしまうため。旅行の記事は「URLから記事を作る」や
     手動で作る。カテゴリー判定は categoryFromContent() が
     ラベル・サブ名・説明文から拾うので CATEGORY_MAP は不要。 */

  var candidates = [];

  /* HTMLに差し込む前の逃がし。商品名は外部APIから来るので必ず通す。 */
  function esc(v) {
    return String(v == null ? '' : v)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function shopKeys() {
    try { return JSON.parse(localStorage.getItem(FIND_KEYS) || '{}'); }
    catch (e) { return {}; }
  }

  function saveShopKeys(k) {
    try { localStorage.setItem(FIND_KEYS, JSON.stringify(k)); } catch (e) {}
  }

  /* 検索用に商品名から飾りを落とす。【送料無料】【ポイント10倍】など。 */
  function cleanName(s) {
    return String(s || '')
      .replace(/[【\[（(][^】\]）)]{0,20}(送料無料|ポイント|クーポン|セール|限定|正規品|あす楽)[^】\]）)]{0,20}[】\]）)]/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  /* メーカー公式ストアらしいか。出品終了が起きにくく、保証も付く。 */
  function isOfficial(e) {
    return /公式|オフィシャル|official|direct|-shop|store\./i.test(
      (e.shop_name || '') + ' ' + (e.url || ''));
  }

  /* 同じ商品の中から1つ選ぶ。公式ストアを優先し、次に送料込みの安さ。
     価格だけで選ばないのは、最安店舗は入れ替わりが激しく、
     数週間で出品が消えてリンク切れになりやすいため。 */
  function pickCheapest(list) {
    var ok = (list || []).filter(function (e) { return e.price > 0; });
    if (!ok.length) return null;
    var official = ok.filter(isOfficial);
    var pool = official.length ? official : ok;
    pool.sort(function (a, b) {
      if (a.postage_included !== b.postage_included) return a.postage_included ? -1 : 1;
      return a.price - b.price;
    });
    return pool[0];
  }

  function rakutenImage(it) {
    var first = (it.mediumImageUrls || it.smallImageUrls || [])[0];
    if (!first) return '';
    return typeof first === 'string' ? first : (first.imageUrl || '');
  }

  function rakutenSearch(appId, opts, accessKey) {
    var q = new URLSearchParams({
      applicationId: appId, format: 'json', formatVersion: '2',
      hits: String(opts.hits || 30), sort: opts.sort || '-reviewCount',
      imageFlag: '1', availability: '1'
    });
    if (opts.genre) q.set('genreId', String(opts.genre));
    if (opts.jan || opts.keyword) q.set('keyword', opts.jan || opts.keyword);
    /* アフィリエイトIDは渡さない。渡すと商品URLが楽天直アフィリエイトの
       ものに変わり、もしも経由の成果として計上されなくなる。 */
    return fetch(RAKUTEN_API + '?' + q.toString(), {
      headers: accessKey ? { accessKey: accessKey } : {}
    })
      .then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (r.ok) return j;
          /* 楽天は理由を返してくれる。刷新の前後で入れ物が変わったので、
             どちらの形でも拾う。そのまま見せないと直しようがない。 */
          var er = j.errors || {};
          var why = er.errorMessage || j.error_description || j.error
                 || ('HTTP ' + r.status);
          if (/access\s*key/i.test(why)) {
            why = 'アクセスキーが違います（' + why + '）。'
                + '楽天ウェブサービスのアプリ詳細にある pk_ で始まる文字列を入れてください。';
          } else if (/application/i.test(why)) {
            why = 'アプリケーションIDが違います（' + why + '）。'
                + 'ハイフン区切りのUUID形式の値です。アフィリエイトIDではありません。';
          } else if (/genre/i.test(why)) {
            why = 'ジャンルIDが違います（' + why + '）。キーワード検索に切り替えます。';
          }
          throw new Error('楽天：' + why);
        });
      })
      .then(function (d) {
        /* 刷新で items（小文字・平たい配列）になったが、
           古い Items/Item の形で返る経路も残っている。両方を受ける。 */
        var list = d.items || d.Items || [];
        return list.map(function (w) {
          var it = w.Item || w.item || w;
          return {
            shop: 'rakuten',
            name: it.itemName || '',
            url: it.itemUrl || '',
            price: Number(it.itemPrice || 0),
            /* postageFlag は 0=送料込み 1=送料別 */
            postage_included: Number(it.postageFlag || 0) === 0,
            reviews: Number(it.reviewCount || 0),
            rating: Number(it.reviewAverage || 0),
            shop_name: it.shopName || '',
            /* formatVersion=2 は文字列の配列、旧形式は {imageUrl} の配列 */
            image: rakutenImage(it)
          };
        });
      });
  }

  /* Amazon（PA-API v5）で探す。/api/amazon が署名して中継する。
     PA-API はレビュー件数・評価を返さない（v5で廃止された）ので、
     件数は 0、評価も 0 で返す。「レビューが十分か」の判定は楽天・
     Yahoo! の数字で行い、Amazon の結果は主に ASIN と商品リンクを
     補うために使う（下限で切り落とさないよう findProducts 側で除外する）。
     1回に返せるのは10件までなので、必要なぶんだけページを繰る。 */
  function amazonSearch(keys, opts) {
    var want = Math.max(1, Number(opts.hits) || 10);
    var pages = Math.min(5, Math.ceil(want / 10));
    var all = [];

    function page(n) {
      return fetch(AMAZON_PROXY, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          accessKey: keys.azAccess, secretKey: keys.azSecret,
          partnerTag: keys.azTag,
          keywords: opts.keyword || '', searchIndex: opts.index || '',
          itemCount: 10, itemPage: n,
          minPrice: opts.pmin || 0, maxPrice: opts.pmax || 0
        })
      }).then(function (r) {
        return r.json().catch(function () { return {}; }).then(function (j) {
          if (!r.ok) throw new Error(j.error || ('Amazon：HTTP ' + r.status));
          return j;
        });
      }).then(function (d) {
        var items = (d.SearchResult && d.SearchResult.Items) || [];
        items.forEach(function (it) {
          var info = it.ItemInfo || {};
          var listing = ((it.Offers || {}).Listings || [])[0] || {};
          var price = ((listing.Price || {}).Amount) || 0;
          all.push({
            shop: 'amazon',
            name: ((info.Title || {}).DisplayValue) || '',
            url: it.DetailPageURL || '',
            asin: it.ASIN || '',
            price: Number(price),
            /* Amazonの配送は出品者ごとに変わる。Amazon発送なら実質送料込み。 */
            postage_included: !!((listing.DeliveryInfo || {}).IsAmazonFulfilled),
            reviews: 0,
            rating: 0,
            shop_name: (((info.ByLineInfo || {}).Manufacturer || {}).DisplayValue) || 'Amazon',
            jan: ((((info.ExternalIds || {}).EANs || {}).DisplayValues) || [])[0] || '',
            image: (((it.Images || {}).Primary || {}).Medium || {}).URL || ''
          });
        });
        if (n < pages && items.length) return page(n + 1);
        return all;
      });
    }
    return page(1);
  }

  function yahooSearch(appId, opts) {
    var q = new URLSearchParams({
      appid: appId, results: String(opts.hits || 30),
      sort: opts.sort || '-review_count', in_stock: 'true'
    });
    if (opts.jan) q.set('jan_code', opts.jan);
    else if (opts.query) q.set('query', opts.query);
    return fetch(YAHOO_PROXY + '?' + q.toString())
      .then(function (r) {
        return r.json().then(function (j) {
          if (!r.ok) throw new Error(j.error || ('Yahoo!API HTTP ' + r.status));
          return j;
        });
      })
      .then(function (d) {
        return (d.hits || []).map(function (it) {
          var rv = it.review || {}, sh = it.shipping || {};
          return {
            shop: 'yahoo',
            name: it.name || '',
            url: it.url || '',
            price: Number(it.price || 0),
            /* 1=送料無料 2=条件付き送料無料 */
            postage_included: ['1', '2'].indexOf(String(sh.code || '')) >= 0,
            reviews: Number(rv.count || 0),
            rating: Number(rv.rate || 0),
            shop_name: (it.seller || {}).name || '',
            jan: (it.janCode || '').trim(),
            image: (it.image || {}).medium || ''
          };
        });
      });
  }

  /* すでに記事にした商品。JANとASIN、それに商品名の頭で見分ける。 */
  function knownProducts() {
    var jans = {}, names = {}, asins = {};
    articles.forEach(function (a) {
      if (a.jan) jans[String(a.jan)] = true;
      if (a.asin) asins[String(a.asin).toUpperCase()] = true;
      if (a.title) names[cleanName(a.title).slice(0, 20)] = true;
    });
    return { jans: jans, names: names, asins: asins };
  }

  /* カテゴリーの選択欄を組み立てる。CATEGORY_MAP にあるものだけを
     並べる（対応表が無いカテゴリーは検索できないため）。 */
  function fillFindCategorySelect() {
    var sel = $('fd-catSelect');
    if (!sel) return;
    (site.categories || []).forEach(function (c) {
      if (!CATEGORY_MAP[c.key]) return;
      var opt = document.createElement('option');
      opt.value = c.key;
      opt.textContent = c.label;
      sel.appendChild(opt);
    });
  }

  /* 探すカテゴリーは「自動」のときだけこちらで選ぶ。選ぶ人の好みに
     寄ると同じジャンルばかり増えるため、記事が少ないカテゴリーを
     優先し、同数のものからは無作為に選ぶ。 */
  function pickCategory() {
    var keys = (site.categories || []).map(function (c) { return c.key; })
      .filter(function (k) { return CATEGORY_MAP[k]; });
    if (!keys.length) return '';
    var n = {};
    keys.forEach(function (k) { n[k] = 0; });
    articles.forEach(function (a) {
      if (n[a.category] !== undefined) n[a.category] += 1;
    });
    var min = Math.min.apply(null, keys.map(function (k) { return n[k]; }));
    var pool = keys.filter(function (k) { return n[k] === min; });
    return pool[Math.floor(Math.random() * pool.length)];
  }

  function findProducts() {
    var keys = shopKeys();
    var hasAmazon = !!(keys.azAccess && keys.azSecret && keys.azTag);
    if (!keys.rakuten && !keys.yahoo && !hasAmazon) {
      $('fd-nokey').hidden = false;
      toast('先に「接続」タブでAPIのIDを登録してください', 'err');
      return;
    }
    var chosen = $('fd-catSelect') ? $('fd-catSelect').value : '';
    var cat = chosen || pickCategory();
    var conf = CATEGORY_MAP[cat];
    if (!conf) { toast('探せるカテゴリーの対応表がありません', 'err'); return; }
    /* 「自動」で選んだときは、今回どれが選ばれたかを欄に反映する
       （手動で戻せるよう、選択肢自体は「自動」のまま残す）。 */
    if (!chosen && $('fd-catSelect')) $('fd-catSelect').value = cat;

    var hits = Number($('fd-count').value || 30);
    var minRev = Number($('fd-minrev').value || 0);
    var pmin = Number($('fd-pmin').value || 0);
    var pmax = Number($('fd-pmax').value || 999999);
    var known = knownProducts();

    $('fd-state').textContent = '検索中…';
    $('btnFind').disabled = true;

    /* 登録されているモールを両方とも検索して、結果を合わせる。
       片方だけを見ると、そのモールにしか無い商品を取りこぼす。
       片方が失敗しても、もう片方の結果は出す。 */
    var jobs = [];
    var failed = [];

    if (keys.rakuten) {
      /* ジャンルIDで絞るほうが精度は高いが、楽天のジャンルは改編される。
         弾かれたらキーワード検索に切り替えて、検索そのものは通す。 */
      jobs.push(
        rakutenSearch(keys.rakuten, { genre: conf.genre, hits: hits },
                      keys.rakutenKey)
          .catch(function (err) {
            if (!/ジャンルID/.test(err.message)) throw err;
            toast('ジャンルIDが使えないため、キーワードで探します');
            return rakutenSearch(keys.rakuten, { keyword: conf.word, hits: hits },
                                 keys.rakutenKey);
          })
          .catch(function (err) { failed.push(err.message); return []; })
      );
    }
    if (keys.yahoo) {
      jobs.push(
        yahooSearch(keys.yahoo, { query: conf.word, hits: hits })
          .catch(function (err) {
            failed.push('Yahoo!：' + err.message);
            return [];
          })
      );
    }
    if (hasAmazon) {
      jobs.push(
        amazonSearch(keys, {
          keyword: conf.word, index: conf.index, hits: hits,
          pmin: pmin, pmax: pmax
        }).catch(function (err) { failed.push(err.message); return []; })
      );
    }

    /* レビューの多い順に混ぜる。モールごとに固まらないようにするため、
       集め終わってからまとめて並べ替える。 */
    Promise.all(jobs).then(function (lists) {
      return lists.reduce(function (all, one) { return all.concat(one); }, [])
        .sort(function (a, b) { return b.reviews - a.reviews; });
    }).then(function (list) {
      var picked = [];
      var byKey = {};      /* 同じ商品を1件にまとめるための索引 */

      list.forEach(function (e) {
        /* Amazon はレビュー件数を返さないので、下限では切らない。
           切ると Amazon の結果が毎回すべて消え、ASINも拾えなくなる。 */
        if (e.shop !== 'amazon' && e.reviews < minRev) return;
        if (e.price < pmin || e.price > pmax) return;
        var name = cleanName(e.name);
        var jan = (e.jan || '').trim();
        if (jan && known.jans[jan]) return;
        if (e.asin && known.asins[String(e.asin).toUpperCase()]) return;

        /* 同一性の判断は商品名の頭でそろえる。JANを持つのはYahoo!側だけで、
           鍵を使い分けると、同じ商品が別々の鍵になって二重に並んでしまう。 */
        var key = name.slice(0, 20);
        if (known.names[name.slice(0, 20)] && !byKey[key]) return;

        var hit = byKey[key];
        if (hit) {
          /* 同じ商品が両方のモールで見つかった場合。URLを足し合わせて
             1件にまとめる。別々に並べると同じ商品が二重に出てしまう。 */
          if (e.shop === 'rakuten' && !hit.rakuten_url) hit.rakuten_url = e.url;
          if (e.shop === 'yahoo' && !hit.yahoo_url) hit.yahoo_url = e.url;
          if (e.shop === 'amazon' && !hit.amazon_url) hit.amazon_url = e.url;
          if (e.shop === 'amazon' && !hit.asin) hit.asin = e.asin || '';
          if (!hit.jan && jan) hit.jan = jan;
          if (e.reviews > hit.reviews) hit.reviews = e.reviews;
          if (e.price < hit.price) hit.price = e.price;
          if (!hit.image) hit.image = e.image;
          return;
        }

        known.names[name.slice(0, 20)] = true;
        var row = {
          name: name, jan: jan, category: cat,
          reviews: e.reviews, rating: e.rating, price: e.price,
          image: e.image,
          rakuten_url: e.shop === 'rakuten' ? e.url : '',
          yahoo_url: e.shop === 'yahoo' ? e.url : '',
          amazon_url: e.shop === 'amazon' ? e.url : '',
          asin: e.shop === 'amazon' ? (e.asin || '') : '',
          shop_name: e.shop_name,
          postage_included: e.postage_included
        };
        byKey[key] = row;
        picked.push(row);
      });
      picked.sort(function (a, b) { return b.reviews - a.reviews; });
      candidates = picked;
      renderCandidates();
      $('fd-state').textContent = picked.length + '件';
      if (failed.length) {
        toast(failed.join(' / '), 'err');
      } else if (!picked.length) {
        toast('条件に合う商品が見つかりませんでした。下限をゆるめてみてください', 'err');
      }
    }).catch(function (err) {
      $('fd-state').textContent = '失敗';
      toast(err.message, 'err');
    }).then(function () {
      $('btnFind').disabled = false;
    });
  }

  function renderCandidates() {
    var box = $('fd-list');
    $('fd-resultCard').hidden = !candidates.length;
    $('fd-count-badge').textContent = candidates.length + '件';
    box.innerHTML = candidates.map(function (c, i) {
      var shops = [];
      if (c.amazon_url || c.asin) shops.push('Amazon');
      if (c.rakuten_url) shops.push('楽天');
      if (c.yahoo_url) shops.push('Yahoo!');
      var img = c.image
        ? '<img src="' + esc(c.image) + '" alt="" loading="lazy">'
        : '<span class="find-noimg">画像なし</span>';
      return '<label class="find-item">' +
        '<input type="checkbox" data-i="' + i + '">' +
        '<span class="find-thumb">' + img + '</span>' +
        '<span class="find-body">' +
          '<b>' + esc(c.name.slice(0, 70)) + '</b>' +
          '<span class="find-meta">￥' + c.price.toLocaleString() +
            '（' + (c.postage_included ? '送料込み' : '送料別') + '）' +
            (c.reviews
              ? ' ・ レビュー' + c.reviews.toLocaleString() + '件 ★' + c.rating.toFixed(1)
              : ' ・ レビュー数不明') +
            ' ・ ' + (shops.join('／') || '—') +
            (c.jan ? ' ・ JAN ' + esc(c.jan) : ' ・ JANなし') +
          (c.asin ? ' ・ ASIN ' + esc(c.asin) : '') +
          '</span>' +
          '<span class="find-shop">' + esc(c.shop_name) + '</span>' +
        '</span>' +
      '</label>';
    }).join('');
  }

  /* 候補の商品名から、記事のスラッグを作る。
     商品名が日本語だけだと slugify() が空になり、時刻の数字が並んだ
     意味のないURLになってしまう。型番などの英数字を優先して拾い、
     それも無ければカテゴリー＋日付にして、あとで直せる形にする。 */
  function draftSlug(name, cat, taken) {
    var latin = String(name).toLowerCase().match(/[a-z0-9][a-z0-9\-]*/g) || [];
    var base = latin.join('-').replace(/-+/g, '-').replace(/^-|-$/g, '').slice(0, 50);
    if (base.length < 3) base = cat + '-' + today().replace(/-/g, '');
    var slug = base, n = 2;
    while (taken[slug]) { slug = base + '-' + n; n++; }
    taken[slug] = true;
    return slug;
  }

  /* 商品名からタグの候補を拾う。ブランド名（先頭の語）と、
     意味のありそうな語を数個。記号や数量表記は落とす。 */
  function draftTags(name, catLabel) {
    var words = String(name).split(/[\s　・／\/,、]+/)
      .map(function (w) { return w.replace(/[【】\[\]（）()「」]/g, '').trim(); })
      .filter(function (w) {
        return w.length >= 2 && w.length <= 14 && !/^[0-9,.]+$/.test(w);
      });
    var tags = words.slice(0, 3);
    if (catLabel && tags.indexOf(catLabel) < 0) tags.push(catLabel);
    return tags;
  }

  /* 選んだ候補から下書きを作る。
     機械的に決まる項目はここで埋めておく。埋めないままだと
     tools/check_articles.py が公開を止めるため、毎回手で入れることになる。
     本文と、ここで作った仮の文章は、記事作成プロンプトの出力で置き換える。 */
  function makeDrafts() {
    var picks = [].slice.call($('fd-list').querySelectorAll('input:checked'))
      .map(function (el) { return candidates[Number(el.dataset.i)]; });
    if (!picks.length) { toast('商品を選んでください', 'err'); return; }

    var taken = {};
    articles.forEach(function (a) { if (a.slug) taken[a.slug] = true; });

    var cats = {};
    (site.categories || []).forEach(function (c) { cats[c.key] = c; });

    var jpOnly = 0;
    picks.forEach(function (c) {
      var a = blank();
      var cat = cats[c.category] || {};
      var label = cat.label || '';

      a.category = c.category;
      a.title = c.name;
      a.list_title = c.name.slice(0, 30);
      a.slug = draftSlug(c.name, c.category, taken);
      if (/^[a-z]+-[0-9]{8}/.test(a.slug)) jpOnly++;

      /* 仮の文章。検査を通す最低限で、公開前に必ず書き換える前提。 */
      a.description = c.name + 'のレビュー。仕様と購入者の評価を突き合わせ、'
        + '結論・良い点・気になる点・向いている人を整理します。';
      a.excerpt = c.name.slice(0, 26) + 'の結論と、向き不向きを整理。';
      a.tags = draftTags(c.name, label);
      if (cat.icon) a.icon = cat.icon;
      a.verdict_title = '結論：';
      a.conclusion_title = 'まとめ';

      if (c.jan) a.jan = c.jan;
      if (c.asin) a.asin = c.asin;
      if (c.amazon_url) a.amazon_url = c.amazon_url;
      if (c.rakuten_url) a.rakuten_url = c.rakuten_url;
      if (c.yahoo_url) a.yahoo_url = c.yahoo_url;
      a.published = false;
      articles.unshift(a);
    });

    renderList();

    var made = articles.slice(0, picks.length);
    var withBody = $('fd-withbody') && $('fd-withbody').checked;

    if (!withBody) {
      showPanel('p-articles');
      var msg = picks.length + '件の下書きを作りました。'
        + '説明文と抜粋は仮の文章なので、本文とあわせて書き換えてください';
      if (jpOnly) {
        msg += '（' + jpOnly + '件はURLに使える英数字が商品名に無かったため、'
             + 'スラッグを仮のものにしています）';
      }
      toast(msg);
      return;
    }

    /* 本文まで作る。1件ずつ順に投げるので時間がかかる。
       途中経過を出さないと、止まっているのか進んでいるのか分からない。 */
    $('btnMakeDrafts').disabled = true;
    $('fd-state').textContent = '本文を作成中…';
    var withImage = $('fd-withimage') && $('fd-withimage').checked;
    generateMany(made, function (i, total, a) {
      $('fd-state').textContent = '本文を作成中… ' + i + '/' + total;
      toast('（' + i + '/' + total + '）' + (a.title || '').slice(0, 24) + ' を作成中');
    }, withImage).then(function (results) {
      $('fd-state').textContent = '完了';
      $('btnMakeDrafts').disabled = false;
      renderList();
      showPanel('p-articles');
      reportGenerated(results);
    });
  }

  function wireFind() {
    if (!$('btnFind')) return;

    fillFindCategorySelect();

    var keys = shopKeys();
    if ($('k-rakuten')) $('k-rakuten').value = keys.rakuten || '';
    if ($('k-rakutenKey')) $('k-rakutenKey').value = keys.rakutenKey || '';
    if ($('k-yahoo')) $('k-yahoo').value = keys.yahoo || '';
    if ($('k-azAccess')) $('k-azAccess').value = keys.azAccess || '';
    if ($('k-azSecret')) $('k-azSecret').value = keys.azSecret || '';
    if ($('k-azTag')) {
      $('k-azTag').value =
        keys.azTag || ((site.amazon || {}).associate_tag || '');
    }
    wireKeyState();

    $('btnFind').addEventListener('click', findProducts);
    $('btnMakeDrafts').addEventListener('click', makeDrafts);
    $('btnFindAll').addEventListener('click', function () {
      $('fd-list').querySelectorAll('input').forEach(function (el) { el.checked = true; });
    });
    $('btnFindNone').addEventListener('click', function () {
      $('fd-list').querySelectorAll('input').forEach(function (el) { el.checked = false; });
    });

    if ($('btnSaveKeys')) {
      $('btnSaveKeys').addEventListener('click', function () {
        /* 貼り付けたときに紛れ込む空白・改行を落とす。
           楽天のアプリIDは数字だけなので、それ以外が入っていたら知らせる。 */
        var rk = $('k-rakuten').value.replace(/\s/g, '');
        var rkey = $('k-rakutenKey').value.replace(/\s/g, '');
        var yh = $('k-yahoo').value.replace(/\s/g, '');
        /* 楽天のアプリケーションIDはUUID形式、アクセスキーは pk_ で始まる。
           取り違えが起きやすいので、形が違えば保存はしつつ知らせる。 */
        if (rk && !/^[0-9a-f-]{30,}$/i.test(rk)) {
          toast('楽天のアプリケーションIDはハイフン区切りのUUID形式です。アフィリエイトIDと取り違えていないか確認してください', 'err');
        } else if (rk && rkey && !/^pk_/.test(rkey)) {
          toast('楽天のアクセスキーは pk_ で始まる文字列です', 'err');
        } else if (rk && !rkey) {
          toast('楽天はアプリケーションIDとアクセスキーの両方が必要です', 'err');
        }
        var aza = $('k-azAccess') ? $('k-azAccess').value.replace(/\s/g, '') : '';
        var azs = $('k-azSecret') ? $('k-azSecret').value.replace(/\s/g, '') : '';
        var azt = $('k-azTag') ? $('k-azTag').value.replace(/\s/g, '') : '';
        /* Amazonは3つ揃って初めて使える。1つでも欠けると署名が通らない。 */
        if ((aza || azs || azt) && !(aza && azs && azt)) {
          toast('Amazonはアクセスキー・シークレットキー・アソシエイトタグの3つが必要です', 'err');
        }
        $('k-rakuten').value = rk;
        $('k-rakutenKey').value = rkey;
        $('k-yahoo').value = yh;
        if ($('k-azAccess')) $('k-azAccess').value = aza;
        if ($('k-azSecret')) $('k-azSecret').value = azs;
        if ($('k-azTag')) $('k-azTag').value = azt;
        saveShopKeys({ rakuten: rk, rakutenKey: rkey, yahoo: yh,
                       azAccess: aza, azSecret: azs, azTag: azt });
        wireKeyState();
        toast('APIのIDを保存しました');
      });
    }
    if ($('btnTestKeys')) {
      $('btnTestKeys').addEventListener('click', testKeys);
    }
  }

  /* Claudeのキーを保存する。Geminiのキーと同じ扱い（このブラウザだけ）。 */
  if ($('btnSaveClKey')) {
    $('btnSaveClKey').addEventListener('click', function () {
      var k = $('clKey').value.replace(/\s/g, '');
      try { localStorage.setItem(CL_KEY, k); } catch (e) {}
      $('cl-state').textContent = k ? '登録済み' : '未登録';
      toast(k ? 'ClaudeのAPIキーを保存しました' : 'ClaudeのAPIキーを消しました');
    });
    try {
      var saved = localStorage.getItem(CL_KEY) || '';
      $('clKey').value = saved;
      $('cl-state').textContent = saved ? '登録済み' : '未登録';
    } catch (e) { /* noop */ }
  }

  function wireKeyState() {
    var k = shopKeys();
    var names = [];
    if (k.rakuten) names.push('楽天');
    if (k.yahoo) names.push('Yahoo!');
    if (k.azAccess && k.azSecret && k.azTag) names.push('Amazon');
    if ($('k-state')) {
      $('k-state').textContent = names.length ? names.join('／') + ' 登録済み' : '未登録';
    }
    if ($('fd-nokey')) $('fd-nokey').hidden = !!names.length;
  }

  function testKeys() {
    var k = {
      rakuten: $('k-rakuten').value.trim(),
      rakutenKey: $('k-rakutenKey').value.trim(),
      yahoo: $('k-yahoo').value.trim(),
      azAccess: $('k-azAccess') ? $('k-azAccess').value.trim() : '',
      azSecret: $('k-azSecret') ? $('k-azSecret').value.trim() : '',
      azTag: $('k-azTag') ? $('k-azTag').value.trim() : ''
    };
    var msgs = [];
    var jobs = [];
    if (k.rakuten) {
      jobs.push(rakutenSearch(k.rakuten, { keyword: 'マウス', hits: 1 }, k.rakutenKey)
        .then(function (r) { msgs.push('楽天：OK（' + r.length + '件）'); })
        /* rakutenSearch 側で「楽天：」を付けているので、ここでは足さない */
        .catch(function (e) { msgs.push(e.message); }));
    }
    if (k.yahoo) {
      jobs.push(yahooSearch(k.yahoo, { query: 'マウス', hits: 1 })
        .then(function (r) { msgs.push('Yahoo!：OK（' + r.length + '件）'); })
        .catch(function (e) { msgs.push('Yahoo!：' + e.message); }));
    }
    if (k.azAccess && k.azSecret && k.azTag) {
      jobs.push(amazonSearch(k, { keyword: 'マウス', index: 'Computers', hits: 1 })
        .then(function (r) { msgs.push('Amazon：OK（' + r.length + '件）'); })
        /* amazonSearch 側で「Amazon：」を付けているので、ここでは足さない */
        .catch(function (e) { msgs.push(e.message); }));
    }
    if (!jobs.length) { toast('いずれかのIDを入力してください', 'err'); return; }
    $('k-state').textContent = '確認中…';
    Promise.all(jobs).then(function () {
      $('k-state').textContent = msgs.join(' / ');
      toast(msgs.join(' / '), /OK/.test(msgs.join('')) ? 'ok' : 'err');
    });
  }


  /* ============================================================
     記事作成プロンプトで本文を作る
     ------------------------------------------------------------
     docs/article-prompt.md をそのまま送り、商品の情報と
     articles.json の形をあとに付ける。プロンプトを2か所で管理すると
     必ず食い違うので、原本はリポジトリの1ファイルだけにしておく。

     出来上がった本文は、そのまま信じずここで検査する。
     禁止表現と文字数は tools/check_text.py と
     tools/check_articles.py が公開時に見ているものと同じ基準。
     先に弾いておかないと、書き上げてから公開できないと分かる。
     ============================================================ */
  var GM_TEXT_API = 'https://generativelanguage.googleapis.com/v1beta/models/';
  var CL_API = 'https://api.anthropic.com/v1/messages';
  var CL_KEY = 'mb.claudeKey';
  var promptCache = null;

  /* 景品表示法・薬機法・アソシエイト規約のリスクになる断定表現。
     tools/check_text.py の NG と同じ内容にしておく。 */
  var NG_WORDS = ['絶対', '必ず', '確実に', '保証します', '間違いなく', '100%',
                  '誰でも', '永久に', '完治', '業界No.1', '日本一'];
  var MIN_CHARS = 6000, MAX_CHARS = 12000;
  /* 公式仕様（facts）も official_url も無い記事は rating と spec をキーごと省く。
     省いたぶん短くなるのは正しい振る舞いなので、下限を下げて水増しを促さない。 */
  var MIN_CHARS_UNBACKED = 5000;

  function loadPrompt() {
    if (promptCache) return Promise.resolve(promptCache);
    if (!cfg.token) {
      return Promise.reject(new Error(
        '記事作成プロンプトを読むためにGitHubの接続が要ります。接続タブで設定してください。'));
    }
    return getFile('docs/article-prompt.md').then(function (res) {
      if (!res) throw new Error('docs/article-prompt.md が見つかりません');
      return fileText(res).then(function (txt) {
        promptCache = txt;
        return promptCache;
      });
    });
  }

  /* 生成させたい形。articles.json の項目名と揃える。
     ここに無い項目は触らせない（slug や published を書き換えられると困る）。 */
  function articleShape() {
    return [
      '{',
      '  "lead": ["段落", "段落"],',
      '  "verdict_title": "結論：…",',
      '  "summary": [{"title":"見出し","text":"本文"}],',
      '  "rating": {"score": 4.2, "breakdown": "評価の内訳を1文で"},',
      '  "good_for": {"intro":"", "items":[{"title":"読者像・使い方","text":"なぜ合うか"}]},',
      '  "highlights": {"intro":"", "items":[{"title":"","text":""}]},',
      '  "not_for": {"intro":"", "items":[{"title":"","text":""}]},',
      '  "scenes": [{"title":"場面","text":"説明"}],',
      '  "pros": ["良い点"], "cons": ["注意点"],',
      '  "spec": {"intro":"", "headers":["項目","本機","比較A","比較B"],',
      '           "rows":[["行名","値","値","値"]], "read":"表の読み方"},',
      '  "sections": [{"heading":"見出し","paras":["段落"],',
      '                "point":"青いポイント枠(任意)","warn":"黄色い注意枠(任意)",',
      '                "aside":"補足","aside_label":"レビューを読み込んで見えたこと"}],',
      '  "voices_intro": "",',
      '  "voices": [{"heading":"","who":"","stars":4,"text":"","negative":false,',
      '              "fix_title":"","fix":""}],',
      '  "voices_after": "",',
      '  "personal_note": "",',
      '  "next_problem": {"intro":"", "items":[{"title":"","text":""}]},',
      '  "faq": [{"q":"購入前に迷いやすい質問","a":"仕様と口コミから導いた回答（1〜3文）"}],',
      '  "conclusion_title": "まとめ", "conclusion": ["段落"],',
      '  "description": "メタディスクリプション（120字以内）",',
      '  "excerpt": "カード用の抜粋（60字以内）",',
      '  "list_title": "一覧用の短いタイトル（30字以内）",',
      '  "title": "記事タイトル",',
      '  "tags": ["タグ"],',
      '  "sub": "サブカテゴリーのkey（分からなければ空文字）",',
      '  "data_gaps": ["確認できなかったこと。無ければ空配列"],',
      '  "self_check": {"fact_accuracy": 0, "source_reliability": 0,',
      '                 "original_analysis": 0, "editorial_quality": 0,',
      '                 "template_avoidance": 0, "purchase_helpfulness": 0,',
      '                 "legal_safety": 0, "amazon_compliance": 0,',
      '                 "total": 0, "notes": "低い項目の理由を1〜2文"}',
      '}'
    ].join('\n');
  }

  /* 記事タイプごとに「使ってよい枠」。
     tools/write_article.py の KIND_FRAMES と同じ内容にしておく。
     2か所で持つのは避けたいが、こちらはブラウザから動くため
     Python を読めない。食い違ったら docs/article-prompt.md が原本。 */
  var KIND_FRAMES = {
    review: ['単一商品レビュー',
      'summary / rating / good_for / not_for / highlights / pros / cons / '
      + 'spec / sections / voices / faq / conclusion',
      'scenes は「想定される利用場面」として書ける場合だけ。書けないなら出さない。'],
    roundup: ['商品比較・ランキング特集',
      'summary / good_for / not_for / spec / sections / faq / conclusion',
      'highlights・scenes は使わない（単一商品レビュー用の枠のため）。'],
    guide: ['商品の選び方・商品解説',
      'summary / good_for / not_for / spec / sections / faq / conclusion',
      'rating・highlights・scenes・voices は使わない。'],
    sale: ['セール情報',
      'summary / sections / faq / conclusion',
      'rating・highlights・scenes・good_for・not_for・voices・pros/cons は使わない。'
      + '中身は「開催時期／セールの特徴／狙い目のカテゴリー／値下げされやすい商品の傾向／'
      + '買うタイミング／注意点／価格を見るときの見方」にする。'
      + '商品レビュー用の見出しを持ち込まない。'],
    howto: ['ハウツー', 'summary / sections / faq / conclusion',
      'rating・highlights・scenes・voices は使わない。']
  };

  /* 美容・ヘルスケアは表現のリスクが別格なので、そのカテゴリーだけ追加で渡す */
  var CARE_NOTE = {
    beauty: '・この記事は美容・コスメです。効果の断定を書かない'
      + '（シミを改善する／ニキビを治す／肌を再生する／肌の内部まで浸透する／'
      + '毛穴が消える／シワが改善する／老化を防ぐ／メイク崩れを防ぐ）。'
      + '使用感・テクスチャ・香り・保湿感・べたつき・成分表示・使用方法を中心にする。'
      + 'メーカーの説明は「メーカーは〇〇を特徴として説明しています」と出どころを明示する。',
    health: '・この記事はヘルスケアです。「病気を診断できる」「治療できる」「予防できる」'
      + 'と書かない。測定値は「健康管理の参考値」として扱い、'
      + '医療行為・診断と誤認される書き方をしない。'
  };

  function kindOf(a) {
    var k = a.kind;
    if (KIND_FRAMES[k]) return k;
    return a.category === 'feature' ? 'roundup' : 'review';
  }

  function kindBlock(a) {
    var k = kindOf(a), f = KIND_FRAMES[k];
    var out = ['【この記事の種類】' + k + '（' + f[0] + '）',
               '・使ってよい枠：' + f[1],
               '・' + f[2],
               '・ここに挙がっていないキーは出力しない。空で出すと空の見出しができる。',
               '・挙がっている枠でも、書くことが無ければ出さない。'
               + '枠を埋めるために内容を作らない（テンプレートの量産になる）。'];
    if (CARE_NOTE[a.category]) out.push(CARE_NOTE[a.category]);
    return out.join('\n');
  }

  function articleRequest(a, prompt) {
    var cat = ((site.categories || []).filter(function (c) {
      return c.key === a.category;
    })[0]) || {};
    var subs = (cat.sub || []).map(function (x) {
      return x.key + '（' + x.label + '）';
    }).join('、') || 'なし';

    var shops = [];
    if (a.asin || a.amazon_url) shops.push('Amazon');
    if (a.rakuten_url) shops.push('楽天市場');
    if (a.yahoo_url) shops.push('Yahoo!ショッピング');

    var facts = a.facts;
    if (typeof facts === 'string') facts = [facts];
    var factsBlock = (facts && facts.length)
      ? '【メーカー公式で確認済みの仕様】\n'
        + facts.map(function (f) { return '・' + f; }).join('\n')
        + '\nここに無い機能を「ある」と書かない。スペック表もこの範囲で作る。'
      /* 公式仕様が無いこと自体は異常ではない。公式サイトを持たない商品もあり、
         管理画面から手で入れる運用も取らない。だから「書けない」ではなく
         「rating と spec を省いて書く」を正しい動きとして指示する。
         tools/write_article.py の facts_block と同じ内容にそろえてある。 */
      : '【仕様について】メーカー公式で裏を取った仕様は渡されていません。'
        + 'これは異常ではなく、通常の状態です。次のとおりに書いてください。\n'
        + '・rating を出さない（キーごと省く）\n'
        + '・spec（比較表）を出さない（キーごと省く）\n'
        + '・数値・機能の有無を断定しない\n'
        + '・そのうえで、記事は書き上げる\n'
        + '公式仕様が無くても書けることを書きます。購入者レビューから読み取れる傾向と'
        + '評価が分かれる理由、購入前に確認しておくべきこと、向く用途と向かない用途、'
        + '販売ページで自分の目で確かめるべき項目（サイズ・付属品・保証・対応機種など）。'
        + '読者には「仕様は販売ページで確認してください」と促します。\n'
        + '公式仕様が無いことを self_check の減点理由にしないでください。'
        + '確認できないものを省き、data_gaps に挙げ、書けることを書けていれば、'
        + 'source_reliability は下げなくて構いません。'
        + '逆に、確認できていないのに rating や spec を出したら大きく減点します。';

    var officialBlock = '';
    if (a.official_url && /^https?:\/\//.test(a.official_url)) {
      officialBlock = '【メーカー公式ページ】' + a.official_url
        + '\n・この製品の一次情報。仕様・スペック表は公式の公表値を優先する。'
        + '\n・記事にはこのURLを本文へ書かない（サイト側が参照リンクとして表示する）。';
    }

    return [
      prompt,
      '',
      '---------------- ここから今回の商品 ----------------',
      '商品名：' + (a.title || ''),
      'カテゴリー：' + (cat.label || a.category),
      '選べるサブカテゴリーのkey：' + subs,
      'JANコード：' + (a.jan || '不明'),
      '買えるモール：' + (shops.join('、') || '不明'),
      kindBlock(a),
      factsBlock,
      officialBlock,
      '',
      '---------------- 出力の決まり ----------------',
      '・JSONだけを返す。前置きも、```などの囲みも付けない。',
      '・次の形に従う。項目を増やさない、減らさない。',
      articleShape(),
      '・本文の合計は ' + MIN_CHARS + '〜' + (MAX_CHARS - 500) + ' 文字。'
        + 'ただし公式仕様が確認できず rating と spec を省いた記事は、'
        + MIN_CHARS_UNBACKED + ' 文字まで短くてよい。'
        + 'うち4割以上は表や箇条書きでなく地の文にする。',
      '・HTMLは <strong> と <em> だけ。それ以外のタグは書かない。',
      '・「' + NG_WORDS.join('」「') + '」は使わない。',
      '・「〜と考えられます」「〜と言えるでしょう」「〜が期待できます」のような'
        + 'AIらしい定型のヘッジ表現を連発しない。「事実 → 判断」の順で書く。',
      '・実際に使った体験として書かない（「実際に使ってみると」等は禁止）。'
        + '「メーカー仕様から見ると」「購入者レビューでは」「公開情報から判断すると」に置き換える。'
        + 'タイトル・本文で「実機レビュー」と書かず「口コミ・評判」等と表記する。',
      '・情報の優先順位は ①メーカー公式サイト・仕様表 → ②Amazon等の販売ページ'
        + ' → ③購入者レビュー → ④メディア/SNS。一次情報と第三者情報が食い違うときは'
        + '一次情報を優先し、食い違いも本文に書く。'
        + '「メーカー公表の事実」「購入者の評価」「モノベースの独自判断」を区別する。',
      '・メーカー未公表の耐久性・防水性・内部構造などを断定しない。'
        + '触れるときは「公開情報から判断すると〜と考えられます」と推測だと明記する。',
      '・口コミの件数や割合を、確認できていないのに書かない。'
        + '数字がなければ「購入者レビューでは」「一部の口コミでは」とする。',
      '・spec とその read に、何を基準に比較したか（用途・価格帯・同クラス等）を書く。',
      '・faq は3〜6問。購入前に迷う具体点を仕様と口コミから答える（各1〜3文）。'
        + 'まとめの焼き直しにしない。答えられない質問は載せない。',
      '・conclusion の最後の段落に、使った主要な情報源と「最終確認日：YYYY年MM月DD日」、'
        + '「価格・在庫は変動するため最新情報はリンク先でご確認ください。」を書く。',
      '・next_problem の項目にリンクURLを入れない。',
      '・価格は書かない。変動するため。',
      '・比較対象は実在する商品にする。「一般的な商品」「同クラス製品」'
        + '「平均的なモデル」のような実在しない相手と比べない。'
        + '実在の比較対象を挙げられないなら spec を出さない。'
        + '比較表が無い記事は、それで完成。埋めるために架空の比較対象を作らない。',
      '・rating は商品ジャンルに合う評価軸で採点し、何を評価し何を減点したかを'
        + 'breakdown に書く。公式仕様を確認できていない商品では rating を出さない。'
        + 'rating が無い記事は、それで完成。無理に点数をひねり出さない。',
      '・pros / cons は商品固有の内容にする。「高性能」「使いやすい」「高い」のような'
        + 'どの商品にも書ける言葉を書かない。「仕様・事実 → 読者への影響」まで書く。',
      '・good_for / not_for は、どんな人・用途・環境・予算・重視点まで書く。'
        + 'おすすめしない側は理由も書く。',
      '・scenes は「実際の生活シーン」として書かない。架空の人物・体験談を作らない。'
        + '「想定される利用場面」「この環境でメリットが出やすい」として書く。',
      '・口コミは、何が評価されているかだけでなく、なぜ評価が分かれるのかを'
        + '仕様と結びつけて書く。口コミを取得できていないなら voices ごと出さない。',
      '・各記事に最低1つ、このサイトだから書ける分析を入れる（口コミと公式仕様の'
        + '食い違い／評価が分かれる理由／スペックから分かる用途上の制約／'
        + '購入前に見落としやすい点）。ただし独自性を作るために事実を作らない。',
      '・Amazon公式・Amazonの推薦や提携だと誤認させる書き方をしない。'
        + 'アソシエイトの開示文はサイト側が全ページに出しているので本文に重ねて書かない。',
      '・確認できないことは data_gaps に列挙する。本文で推測で埋めない。'
        + '書けない枠はキーごと省く。',
      '・書き終えたら self_check を自分で採点する。甘く付けない。',
      '',
      /* 長いプロンプトでは、途中の禁止事項ほど守られなくなる。
         いちばん後ろにもう一度置いて、書き終える直前に読ませる。
         tools/write_article.py の末尾と同じ内容にそろえてある。 */
      '---------------- 書き出す前に、もう一度確認する ----------------',
      '次の3つは、ほかのどの指示よりも優先して守る。',
      '1. 「' + NG_WORDS.join('」「') + '」を、どの項目にも1回も書かない。'
        + '「必ず確認してください」も不可。「事前に確認してください」と書く。',
      '2. 実機を使ったと読める書き方をしない。「使ってみた」「使ってみると」'
        + '「実際に感じた」「実測した（自分が測った意味で）」「装着してみた」'
        + '「開封した」は書かない。'
        + '読者への助言としての「購入前に実測してください」は書いてよい。',
      '3. 実在しない比較対象（「一般的な製品」「同クラス製品」「平均的なモデル」）'
        + 'と比べない。実在の商品名を挙げられないなら、比較そのものを書かない。',
      '書き終えたら、この3点で出力を読み返してから返すこと。'
    ].join('\n');
  }

  /* Claude（Anthropic API）で本文を作る。
     ブラウザから直接呼ぶには anthropic-dangerous-direct-browser-access が要る。
     この画面は Cloudflare Access の内側で、鍵もこのブラウザにしか無いため、
     中継を挟まず直接叩いている。 */
  /* 出力の上限。日本語は1文字あたり1トークン前後なので、
     8,000字の記事とJSONの記号を入れても16,000で足りる。
     モデルごとの上限を超えると、その時点で断られてしまう。 */
  var CL_MAX_TOKENS = 16000;

  function clText(key, model, text, maxTokens) {
    return fetch(CL_API, {
      method: 'POST',
      headers: {
        'x-api-key': key,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: model,
        max_tokens: maxTokens || CL_MAX_TOKENS,
        temperature: 1,
        system: 'あなたは日本語の商品レビュー記事を書くライターです。'
              + '指示された形のJSONだけを返し、前置きも囲みも付けません。',
        messages: [{ role: 'user', content: text }]
      })
    }).then(function (r) {
      return r.json().then(function (j) {
        if (r.ok) return j;
        var why = (j.error && j.error.message) || ('HTTP ' + r.status);
        /* 上限がモデルの許容を超えていた場合だけ、半分にして1度やり直す。
           モデルごとの上限をこちらで持つと、増えるたびに古くなる。 */
        if (/max_tokens/i.test(why) && (maxTokens || CL_MAX_TOKENS) > 4000) {
          log('  上限を下げて再試行します（' + why + '）', 'err');
          return clText(key, model, text,
                        Math.floor((maxTokens || CL_MAX_TOKENS) / 2))
            .then(function (parsed) { return { __parsed: parsed }; });
        }
        throw new Error(why);
      });
    }).then(function (j) {
      if (j.__parsed) return j.__parsed;      /* 再試行ぶんは読み取り済み */
      var out = (j.content || []).map(function (c) { return c.text || ''; }).join('');
      if (!out) throw new Error('応答が空でした');
      /* 上限に当たって途中で切れた場合。JSONとして読めないのは当然なので、
         「読めません」ではなく本当の理由を出す。 */
      if (j.stop_reason === 'max_tokens') {
        throw new Error('本文が長すぎて途中で切れました（' + out.length.toLocaleString()
          + '字で打ち切り）。もう一度試すか、モデルを変えてください');
      }
      return parseGenJson(out);
    });
  }

  /* 生成結果をJSONとして読む。囲みや前置きが付くことがあるので取り除く。
     読めなかったときは、返ってきた中身の頭を記録に残す。
     何が返ってきたか分からないままだと、直しようがない。 */
  function parseGenJson(out) {
    out = String(out).replace(/^\s*```(?:json)?\s*/, '').replace(/\s*```\s*$/, '');
    var i = out.indexOf('{'), k = out.lastIndexOf('}');
    if (i >= 0 && k > i) out = out.slice(i, k + 1);
    try {
      return JSON.parse(out);
    } catch (e) {
      log('  返ってきた内容の先頭：' + out.slice(0, 300), 'err');
      throw new Error('返ってきた内容がJSONとして読めませんでした（'
        + out.length.toLocaleString() + '字）。「操作の記録」に中身の先頭を出しています');
    }
  }

  function gmText(key, model, text) {
    return fetch(GM_TEXT_API + encodeURIComponent(model) + ':generateContent', {
      method: 'POST',
      headers: { 'x-goog-api-key': key, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ role: 'user', parts: [{ text: text }] }],
        generationConfig: { responseMimeType: 'application/json',
                            temperature: 0.8, maxOutputTokens: 32768 }
      })
    }).then(function (r) {
      return r.json().then(function (j) {
        if (!r.ok) throw new Error((j.error && j.error.message) || ('HTTP ' + r.status));
        return j;
      });
    }).then(function (j) {
      var parts = (((j.candidates || [])[0] || {}).content || {}).parts || [];
      var out = parts.map(function (p) { return p.text || ''; }).join('');
      if (!out) throw new Error('応答が空でした。モデルを変えて試してください');
      var fin = (((j.candidates || [])[0] || {}).finishReason) || '';
      if (fin === 'MAX_TOKENS') {
        throw new Error('本文が長すぎて途中で切れました（' + out.length.toLocaleString()
          + '字で打ち切り）。もう一度試すか、モデルを変えてください');
      }
      return parseGenJson(out);
    });
  }

  /* 本文の文字数。入れ子をたどって文字列だけ数える。
     tools/check_articles.py の body_chars と同じ考え方。 */
  function bodyChars(v) {
    if (typeof v === 'string') return v.replace(/<[^>]+>/g, '').length;
    if (Array.isArray(v)) {
      return v.reduce(function (n, x) { return n + bodyChars(x); }, 0);
    }
    if (v && typeof v === 'object') {
      return Object.keys(v).reduce(function (n, k) {
        return n + bodyChars(v[k]);
      }, 0);
    }
    return 0;
  }

  /* 統合した品質ルールの機械検査。
     tools/write_article.py の audit() と同じ正規表現にそろえてある。 */
  var FAKE_EXPERIENCE = /実際に使って(?:み|感じ|分かっ|わかっ)|使ってみ(?:た|ると|たら)|(?:私|筆者|編集部)(?:が|は)[^。]{0,8}?(?:使っ|試し|触っ|装着し|測っ)|使用して(?:分かっ|わかっ|感じ)|実際に感じ(?:た|られ)|実測(?:した|して[みま]|の結果)|撮影して確認|装着してみ|手に?とってみ|試してみたところ|開封(?:した|してみ)|実機レビュー/g;
  var FAKE_REVIEW_NUM = /\d+\s*件(?:の|を)?(?:レビュー|口コミ|評価)|(?:レビュー|口コミ|評価)(?:を)?\s*\d+\s*件|\d+\s*人(?:の|が)(?:購入者|レビュー|口コミ)|(?:平均|口コミ|レビュー)(?:評価|星)[^。]{0,6}?\d\.\d|星\s*\d\.\d/g;
  var AMAZON_MISLEAD = /Amazon(?:の)?公式(?:サイト|ストア|見解|推奨)|Amazonが(?:推薦|認定|保証|おすすめ)|Amazon(?:から)?(?:認定|推薦|公認)|Amazonと(?:の)?(?:提携|パートナー)/g;
  var VAGUE_RIVAL = /一般的な(?:商品|製品|モデル|美容液|クリーム)|同クラス(?:の)?(?:製品|商品)|平均的な(?:商品|製品|モデル)|標準的な(?:商品|製品|モデル)/g;
  var CARE_CLAIM = /シミが(?:消え|なくな)|シワが(?:消え|なくな|改善)|毛穴が(?:消え|なくな)|ニキビが治|肌が再生|老化を防|アンチエイジング効果|肌の(?:内側|奥|内部)(?:まで|から)(?:浸透|届|作用)|病気を(?:治|予防|発見)|診断でき|美白|痩せ(?:る|られ|ます)/g;
  var AI_PHRASE = /と言えるでしょう|と言えます|と考えられます|が期待できます|最大の魅力(?:です|は)|総合的に判断すると|非常に(?:優れ|魅力的|便利)|大きな(?:ポイント|メリット)です|バランスの取れた|ということが分かります/g;
  var AI_PHRASE_LIMIT = 6;
  /* 打ち消し・仮定・疑問の文脈は拾わない。
     「実測したわけではありません」「購入前に実測してください」「治りますか？」は問題ない。 */
  var NEGATION = /^[^。]{0,30}?(?:ませ[んぬ]|ないでください|わけでは|とは限|ような|か[？?]|かどうか|ものではあり|と(?:は)?書き)/;
  var PUBLISH_SCORE = 85;

  /* 打ち消し文脈をのぞいた一致だけを返す */
  function findHits(re, text) {
    var out = [], m;
    re.lastIndex = 0;
    while ((m = re.exec(text)) !== null) {
      if (!NEGATION.test(text.slice(m.index + m[0].length,
                                    m.index + m[0].length + 40))) out.push(m[0]);
      if (m.index === re.lastIndex) re.lastIndex++;   /* 空一致で止まらないように */
    }
    return out;
  }

  function auditArticle(a) {
    var warns = [];
    var blob = JSON.stringify(a);
    /* 読者が読む文だけを、タグを外して1本につなぐ */
    var text = JSON.stringify(GEN_FIELDS.reduce(function (o, k) {
      if (a[k] !== undefined) o[k] = a[k];
      return o;
    }, {})).replace(/<[^>]+>/g, '');

    [['実体験の捏造', FAKE_EXPERIENCE],
     ['確認できない口コミ数値', FAKE_REVIEW_NUM],
     ['Amazonとの関係の誤認', AMAZON_MISLEAD],
     ['実在しない比較対象', VAGUE_RIVAL]].forEach(function (pair) {
      findHits(pair[1], text).forEach(function (w) {
        warns.push(pair[0] + '「' + w + '」');
      });
    });
    if (a.category === 'beauty' || a.category === 'health') {
      findHits(CARE_CLAIM, text).forEach(function (w) {
        warns.push('効果の断定（薬機法）「' + w + '」');
      });
    }
    var nAi = findHits(AI_PHRASE, text).length;
    if (nAi > AI_PHRASE_LIMIT) {
      warns.push('AIらしい定型表現が ' + nAi + ' 回（上限 ' + AI_PHRASE_LIMIT + '）');
    }

    /* 記事タイプに合わない枠を使っていないか */
    var kind = kindOf(a);
    var allowed = KIND_FRAMES[kind][1].split(/[\s/]+/);
    ['rating', 'highlights', 'scenes', 'voices', 'good_for', 'not_for']
      .forEach(function (key) {
        var v = a[key];
        var has = (v && typeof v === 'object' && !Array.isArray(v))
          ? !!(v.items && v.items.length) : !!(v && v.length);
        if (!has || allowed.indexOf(key) >= 0) return;
        if (kind === 'review' && key === 'scenes') return;
        warns.push(kind + ' 記事に ' + key + ' が入っている（この型では使わない枠）');
      });

    NG_WORDS.forEach(function (w) {
      if (blob.indexOf(w) >= 0) warns.push('禁止表現「' + w + '」');
    });
    /* <strong> と <em> 以外のタグは、そのまま文字として出てしまう */
    /* 使ってよいのは <strong> <em> と、スペック表の丸印に使う
       <span class="mark-o"> <span class="mark-x"> だけ。
       丸印は既存記事の表にも入っているので、除かないと毎回警告が出る。 */
    var tags = blob.match(/<\/?([a-z]+)[^>]*>/gi) || [];
    tags.forEach(function (t) {
      if (/^<\/?(strong|em)\b/i.test(t)) return;
      if (/^<span class=\\?"mark-[ox]\\?">$/i.test(t) || /^<\/span>$/i.test(t)) return;
      warns.push('使えないタグ ' + t);
    });
    /* 裏づけが無いのに rating / spec を出していないか。
       公式情報が無いこと自体は問題ではない。無いのに数字を出すのが問題。 */
    var backed = !!(a.facts && a.facts.length) || !!(a.official_url || '').trim();
    if (!backed) {
      if (a.rating && a.rating.score) {
        warns.push('公式仕様の裏づけが無いのに rating がある（キーごと省くのが正しい）');
      }
      if (a.spec && a.spec.rows && a.spec.rows.length) {
        warns.push('公式仕様の裏づけが無いのに spec がある（キーごと省くのが正しい）');
      }
    }
    var n = bodyChars(a);
    var floor = backed ? MIN_CHARS : MIN_CHARS_UNBACKED;
    if (n < floor) warns.push('本文が ' + n.toLocaleString() + ' 字（下限 ' + floor.toLocaleString() + '）。水増しで埋めない');
    if (n > MAX_CHARS) warns.push('本文が ' + n.toLocaleString() + ' 字（上限 ' + MAX_CHARS.toLocaleString() + '）');
    /* 重複は1回だけ知らせる */
    return warns.filter(function (w, i) { return warns.indexOf(w) === i; });
  }

  /* 生成結果を記事へ移す。slug・published・販売先URLなど、
     こちらで決めた項目は上書きさせない。 */
  var GEN_FIELDS = ['lead', 'verdict_title', 'summary', 'rating', 'good_for',
                    'highlights', 'not_for', 'scenes', 'pros', 'cons', 'spec', 'sections',
                    'voices_intro', 'voices', 'voices_after', 'personal_note',
                    'next_problem', 'faq', 'conclusion_title', 'conclusion',
                    'description', 'excerpt', 'list_title', 'title', 'tags', 'sub'];

  function applyGenerated(a, gen) {
    GEN_FIELDS.forEach(function (k) {
      if (gen[k] !== undefined && gen[k] !== null && gen[k] !== '') a[k] = gen[k];
    });
    /* 書き直しでは、上書きだけでは足りない。
       公式仕様の裏づけが無い記事で生成AIが rating と spec を正しく省いても、
       前の版の値が残り、根拠のない点数と比較表が生き続ける。
       裏づけが無いなら、この2つはキーごと落とす。
       tools/write_article.py の apply_generated と同じ扱い。 */
    if (!((a.facts && a.facts.length) || (a.official_url || '').trim())) {
      delete a.rating;
      delete a.spec;
    }
    /* リンク切れ検査で止まるので、勝手に付いたリンクは落とす */
    ((a.next_problem || {}).items || []).forEach(function (it) {
      delete it.link_url; delete it.link_label;
    });
    a.updated = today();
    return a;
  }

  /* アイキャッチを用意する。
     楽天・Yahoo!のAPIは商品画像のURLを返すが、モールの商品画像は
     出品者・メーカーに権利があり、当サイトに転載してよいものではない。
     そのため商品写真は使わず、運営者が決めたプロンプトで作った
     イメージ画像を置き、記事側に「イメージ（AI生成）」と明示する。 */
  function ensureEyecatch(a) {
    if (a.thumb) return Promise.resolve(null);       /* すでにある */
    var key = '';
    try { key = localStorage.getItem(GM_KEY) || ''; } catch (e) {}
    if (!key) return Promise.reject(new Error('Gemini APIキーが未登録のため画像を作れません'));
    if (!cfg.token) return Promise.reject(new Error('GitHub未接続のため画像を保存できません'));
    var model = ($('gmModel') && $('gmModel').value) || 'gemini-3.1-flash-image';
    return genImage(a, key, model).then(function (img) {
      return saveImage(a, img);                       /* thumb と image_ai を立てる */
    });
  }

  /* 生成AIの自己申告（確認できなかったこと・自己採点）を、
     既存の警告欄にそのまま出す。記事には保存しない（applyGenerated が弾く）。 */
  function selfCheckWarns(gen) {
    var out = [];
    var gaps = gen.data_gaps || [];
    if (typeof gaps === 'string') gaps = [gaps];
    gaps.forEach(function (g) { out.push('確認できていない：' + g); });

    var sc = gen.self_check;
    if (!sc) { out.push('self_check が返っていません（自己採点なし）'); return out; }
    if (typeof sc.total === 'number' && sc.total < PUBLISH_SCORE) {
      out.push('自己採点 総合 ' + sc.total + '（' + PUBLISH_SCORE
               + '点未満は公開しない）' + (sc.notes ? '：' + sc.notes : ''));
    }
    return out;
  }

  function generateArticle(a) {
    var model = ($('gmTextModel') && $('gmTextModel').value) || 'gemini-3.6-flash';
    var useClaude = model.indexOf('claude') === 0;
    var key = '';
    try {
      key = localStorage.getItem(useClaude ? CL_KEY : GM_KEY) || '';
    } catch (e) {}
    if (!key) {
      return Promise.reject(new Error(useClaude
        ? 'Claudeを使うにはAnthropicのAPIキーが要ります。サブスクで書かせる場合は、手元で python3 tools/write_article.py --drafts を実行してください'
        : '画像タブでGemini APIキーを登録してください'));
    }
    return loadPrompt().then(function (prompt) {
      var req = articleRequest(a, prompt);
      return useClaude ? clText(key, model, req) : gmText(key, model, req);
    }).then(function (gen) {
      applyGenerated(a, gen);
      return auditArticle(a).concat(selfCheckWarns(gen));
    });
  }

  /* 本文がまだ無い下書きを、順番に埋める。
     まとめて投げると、どれで失敗したか分からなくなるので1件ずつ。 */
  function generateMany(list, onEach, withImage) {
    var results = [];
    return list.reduce(function (chain, a, i) {
      return chain.then(function () {
        if (onEach) onEach(i + 1, list.length, a);
        return generateArticle(a)
          .then(function (warns) {
            /* 本文ができたら画像も用意する。画像で失敗しても
               本文は残したいので、ここで受け止めて注意として扱う。 */
            if (!withImage) { results.push({ a: a, warns: warns }); return; }
            return ensureEyecatch(a).then(function () {
              results.push({ a: a, warns: warns });
            }).catch(function (err) {
              results.push({ a: a, warns: warns.concat(['画像なし：' + err.message]) });
            });
          })
          .catch(function (err) { results.push({ a: a, error: err.message }); });
      });
    }, Promise.resolve()).then(function () { return results; });
  }

  function reportGenerated(results) {
    var ng = results.filter(function (r) { return r.error; });
    var warned = results.filter(function (r) { return !r.error && r.warns.length; });
    var ok = results.length - ng.length - warned.length;
    var msg = '本文を作りました：問題なし ' + ok + '件';
    if (warned.length) msg += ' / 要確認 ' + warned.length + '件';
    if (ng.length) msg += ' / 失敗 ' + ng.length + '件';
    /* 件数だけ出しても直せない。最初の理由をそのまま添える。 */
    if (ng.length) msg += '｜' + ng[0].error;
    toast(msg, ng.length ? 'err' : 'ok');
    results.forEach(function (r) {
      var name = r.a.list_title || r.a.title || r.a.slug;
      if (r.error) log('  ✗ ' + name + '：' + r.error, 'err');
      else if (r.warns.length) log('  △ ' + name + '：' + r.warns.join(' / '), 'err');
      else log('  ✓ ' + name, 'ok');
    });
  }

  function blobToB64(blob) {
    return new Promise(function (resolve, reject) {
      var fr = new FileReader();
      fr.onload = function () { resolve(String(fr.result).split(',')[1]); };
      fr.onerror = reject;
      fr.readAsDataURL(blob);
    });
  }

  /* ==================================================== URLから記事を作る
     商品ページのURLを1つ渡すだけで、下書き作成→本文生成→画像生成→公開
     までを自動で行う。「記事」タブでの確認をはさまないため、
     間違った内容がそのまま公開される前提で、失敗はログに残す。 */
  var PRODUCT_PROXY = '/api/fetch-product';

  function detectShop(url) {
    var host = '';
    try { host = new URL(url).hostname; } catch (e) { return null; }
    if (/(^|\.)amazon\.co\.jp$/.test(host)) return 'amazon';
    if (/(^|\.)rakuten\.co\.jp$/.test(host)) return 'rakuten';
    if (/(^|\.)yahoo\.co\.jp$/.test(host)) return 'yahoo';
    return null;
  }

  function fetchProductPage(url) {
    return fetch(PRODUCT_PROXY + '?url=' + encodeURIComponent(url))
      .then(function (r) {
        return r.json().then(function (j) {
          if (!r.ok) throw new Error(j.error || ('商品ページの取得に失敗しました（HTTP ' + r.status + '）'));
          return j;
        });
      });
  }

  /* JSON-LDはサイトによって @graph に包まれていたり配列だったりするため、
     Productらしきノードを再帰でたどって拾う。 */
  function findProductLd(node, out) {
    if (!node || typeof node !== 'object') return;
    if (Array.isArray(node)) { node.forEach(function (n) { findProductLd(n, out); }); return; }
    var type = node['@type'];
    var isProduct = type === 'Product' || (Array.isArray(type) && type.indexOf('Product') >= 0);
    if (isProduct) {
      if (node.name && !out.name) out.name = String(node.name);
      var image = Array.isArray(node.image) ? node.image[0] : node.image;
      if (image && !out.image) out.image = String(image);
      if (node.gtin13 && !out.jan) out.jan = String(node.gtin13);
      if (node.gtin && !out.jan && /^\d{8}$|^\d{13}$/.test(node.gtin)) out.jan = String(node.gtin);
      var offers = Array.isArray(node.offers) ? node.offers[0] : node.offers;
      if (offers && offers.price && !out.price) out.price = Number(offers.price) || 0;
    }
    Object.keys(node).forEach(function (k) { findProductLd(node[k], out); });
  }

  function parseProductMeta(data) {
    var out = { name: '', image: '', price: 0, jan: '' };
    (data.jsonld || []).forEach(function (text) {
      try { findProductLd(JSON.parse(text), out); } catch (e) {}
    });
    if (!out.name) out.name = data.title || '';
    if (!out.image) out.image = data.image || '';
    if (!out.price && data.price) out.price = Number(data.price) || 0;
    return out;
  }

  /* タイトルもJSON-LDも取れなかったときの最後の砦。
     Amazonの商品URLは /商品名-キーワード/dp/ASIN/ の形なので、
     dp（または gp/product）の手前のスラッグを商品名として復元する。
     ハイフン区切りでノイズも混じるが、空で失敗するよりは足がかりになる。 */
  function nameFromUrl(raw) {
    var path = '';
    try { path = decodeURIComponent(new URL(raw).pathname); } catch (e) { return ''; }
    var m = path.match(/\/([^\/]+)\/(?:dp|gp\/product|gp\/aw\/d)\//);
    if (!m) return '';
    var s = m[1].replace(/-/g, ' ').replace(/\s{2,}/g, ' ').trim();
    if (/^b0[0-9a-z]{8}$/i.test(s)) return '';   // スラッグ無しでASINだけの短縮URL
    return s.length >= 4 ? s : '';
  }

  /* 楽天・Yahoo!のタイトルは「【楽天市場】商品名：店舗名」
     「商品名 : 店舗名 - 通販 - Yahoo!ショッピング」のように店名が
     くっついてくるため、末尾の店名部分を落とす。 */
  function cleanShopTitle(name, shop) {
    var s = String(name || '').replace(/^【楽天市場】\s*/, '');
    if (shop === 'rakuten') {
      var i = s.lastIndexOf('：');
      if (i > 0) s = s.slice(0, i);
    } else if (shop === 'yahoo') {
      var j = s.indexOf(' : ');
      if (j > 0) s = s.slice(0, j);
    }
    return s.trim();
  }

  function janValid(code) {
    if (!/^\d{8}$|^\d{13}$/.test(code)) return false;
    var ds = code.split('').map(Number);
    var check = ds.pop();
    var total = ds.reverse().reduce(function (sum, d, i) {
      return sum + d * (i % 2 === 0 ? 3 : 1);
    }, 0);
    return (10 - total % 10) % 10 === check;
  }

  /* 商品名から、当てはまりそうなカテゴリー・サブカテゴリーを推測する。
     完全な判定はできないので、外れていれば「記事」タブで直せばよい。 */
  function guessCategory(name) {
    var cats = site.categories || [];
    var best = null, bestScore = 0;
    cats.forEach(function (c) {
      var score = 0, sub = '';
      var conf = CATEGORY_MAP[c.key];
      var words = [c.label].concat(conf ? conf.word.split(/\s+/) : []);
      words.forEach(function (w) { if (w && name.indexOf(w) >= 0) score += 1; });
      (c.sub || []).forEach(function (s) {
        if (s.label && name.indexOf(s.label) >= 0) { score += 2; sub = s.key; }
      });
      if (score > bestScore) { bestScore = score; best = { category: c.key, sub: sub }; }
    });
    if (best) return best;
    return { category: pickCategory() || (cats[0] || {}).key || '', sub: '' };
  }

  /* 記事の中の文字列をぜんぶつなげる。カテゴリー判定の材料にする。 */
  function articleText(a) {
    var acc = [];
    (function walk(v) {
      if (typeof v === 'string') { acc.push(v); return; }
      if (Array.isArray(v)) { v.forEach(walk); return; }
      if (v && typeof v === 'object') { Object.keys(v).forEach(function (k) { walk(v[k]); }); }
    })(a);
    return acc.join(' ');
  }

  /* 生成された記事の中身と、サイト設定のカテゴリー定義（ラベル・
     サブカテゴリー名・説明文・キーワード）を突き合わせて、いちばん
     当てはまるカテゴリーを選ぶ。商品名だけで決めるより外しにくい。
     手動でジャンルを指定していない「URLから記事を作る」で使う。 */
  function categoryFromContent(a) {
    var cats = site.categories || [];
    var text = articleText(a);
    var tags = (a.tags || []).join(' ');
    function count(hay, needle) {
      if (!needle) return 0;
      return hay.split(needle).length - 1;
    }
    var best = null, bestScore = 0;
    cats.forEach(function (c) {
      if (c.key === 'feature') return;   /* 特集は自動では選ばない */
      var score = 0, sub = '', subScore = 0;
      var conf = CATEGORY_MAP[c.key];
      var words = [c.label]
        .concat(conf ? conf.word.split(/\s+/) : [])
        .concat(String(c.lead || '').split(/[\s、。・（）()「」]+/).filter(function (w) {
          return w.length >= 2;
        }));
      words.forEach(function (w) {
        if (!w) return;
        score += count(text, w);
        score += count(tags, w) * 3;      /* タグでの一致は重い */
      });
      (c.sub || []).forEach(function (s) {
        var sc = count(text, s.label) + count(tags, s.label) * 3;
        if (sc > subScore) { subScore = sc; sub = s.key; }
        score += sc;
      });
      if (score > bestScore) { bestScore = score; best = { category: c.key, sub: sub }; }
    });
    return best;
  }

  /* 禁止表現・使えないタグを取り除いて、公開できる形に直す。
     絶対／必ず／確実に…はどれも文中の修飾語なので、そのまま削っても
     文としては自然に読める。削った跡の記号の重なりだけ整える。
     配列・オブジェクトを含む記事全体を対象にするため、JSON文字列の
     まま置換する（値の途中にNGワードやタグが混ざっていても拾える）。 */
  function autoFixArticle(a) {
    var json = JSON.stringify(a);
    NG_WORDS.forEach(function (w) { json = json.split(w).join(''); });
    json = json.replace(/<\/?([a-z]+)[^>]*>/gi, function (tag, name) {
      name = name.toLowerCase();
      if (name === 'strong' || name === 'em') return tag;
      if (/^<span class=\\?"mark-[ox]\\?">$/i.test(tag) || /^<\/span>$/i.test(tag)) return tag;
      return '';
    });
    json = json
      .replace(/、、+/g, '、')
      .replace(/。。+/g, '。')
      .replace(/、。/g, '。')
      .replace(/[ 　]{2,}/g, ' ');
    return JSON.parse(json);
  }

  function qpLog(msg, kind) {
    var box = $('qpLog');
    if (!box) return;
    var line = document.createElement('div');
    line.textContent = msg;
    if (kind) line.className = kind;
    box.appendChild(line);
    box.scrollTop = box.scrollHeight;
  }

  function runQuickPost() {
    var raw = ($('qpUrl').value || '').trim();
    if (!raw) { toast('商品ページのURLを入力してください', 'err'); return; }
    if (!cfg.token) { toast('先に「接続」タブでGitHubを設定してください', 'err'); return; }

    var shop = detectShop(raw);
    if (!shop) {
      toast('Amazon・楽天市場・Yahoo!ショッピングの商品ページURLに対応しています', 'err');
      return;
    }
    var asin = shop === 'amazon' ? extractAsin(raw) : '';
    if (shop === 'amazon' && !asin) {
      toast('AmazonのURLからASINを取り出せませんでした。商品ページのURLを貼り付けてください', 'err');
      return;
    }

    var nameOverride = (($('qpName') && $('qpName').value) || '').trim();

    $('btnQpRun').disabled = true;
    $('qpLog').innerHTML = '';

    var a = null, warns = null, picked = '';
    var metaPromise;
    if (nameOverride) {
      qpLog('入力された商品名を使います：' + nameOverride);
      metaPromise = Promise.resolve({ name: nameOverride, jan: '' });
    } else {
      qpLog('商品ページを取得しています…');
      metaPromise = fetchProductPage(raw)
        .then(parseProductMeta)
        .catch(function (err) {
          /* ページ取得自体が弾かれた（Amazonのボット判定など）。
             URLのスラッグから商品名を復元できれば、それで続行する。 */
          var fromUrl = nameFromUrl(raw);
          if (!fromUrl) throw err;
          qpLog('ページを取得できなかったため、URLから商品名を推定します：' + fromUrl, 'warn');
          return { name: fromUrl, image: '', price: 0, jan: '' };
        });
    }

    metaPromise.then(function (meta) {
      if (!meta.name && !nameOverride) {
        var fromUrl = nameFromUrl(raw);
        if (fromUrl) {
          qpLog('商品名が取れなかったため、URLから推定します：' + fromUrl, 'warn');
          meta.name = fromUrl;
        }
      }
      if (!meta.name) throw new Error('商品名を取得できませんでした（ページの構造が対応していない可能性があります）');
      var name = cleanName(nameOverride ? meta.name : cleanShopTitle(meta.name, shop));
      /* Amazonがボット判定などで商品ページの代わりに案内ページを返すと、
         商品名の代わりに「Amazon.co.jp」のようなサイト名だけが取れてしまう。
         これに気づかず進めると、AIが実在しない商品の記事を書いてしまう。 */
      if (!nameOverride && (name.length < 4 ||
          /^(amazon(\.co\.jp)?|楽天市場|yahoo!?ショッピング)$/i.test(name))) {
        throw new Error('商品名を正しく取得できませんでした（「' + name +
          '」）。ページ取得がブロックされた可能性があります。上の「商品名」欄に手入力してからもう一度お試しください');
      }
      if (!nameOverride) qpLog('商品名：' + name);

      var taken = {};
      articles.forEach(function (x) { if (x.slug) taken[x.slug] = true; });
      picked = (($('qpCategory') && $('qpCategory').value) || '').trim();
      if (picked && !(site.categories || []).some(function (c) { return c.key === picked; })) picked = '';
      /* 手動指定があればそれで確定。無ければ本文ができてから
         categoryFromContent() で判定するので、ここでは仮に置くだけ。 */
      var guess = picked ? { category: picked, sub: '' } : guessCategory(name);
      var cat = (site.categories || []).filter(function (c) { return c.key === guess.category; })[0] || {};

      a = blank();
      a.category = guess.category;
      a.sub = guess.sub;
      a.title = name;
      a.list_title = name.slice(0, 30);
      a.slug = draftSlug(name, guess.category, taken);
      a.description = name + 'のレビュー。仕様と購入者の評価を突き合わせ、結論・良い点・気になる点・向いている人を整理します。';
      a.excerpt = name.slice(0, 26) + 'の結論と、向き不向きを整理。';
      a.tags = draftTags(name, cat.label || '');
      if (cat.icon) a.icon = cat.icon;
      a.verdict_title = '結論：';
      a.conclusion_title = 'まとめ';
      if (meta.jan && janValid(meta.jan)) a.jan = meta.jan;
      if (shop === 'amazon') a.asin = asin;
      if (shop === 'rakuten') a.rakuten_url = raw;
      if (shop === 'yahoo') a.yahoo_url = raw;
      a.published = false;

      if (picked) {
        qpLog('カテゴリー：' + (cat.label || guess.category) + '（手動で指定）');
      } else {
        qpLog('カテゴリー：本文ができてから内容に合わせて判定します');
      }
      qpLog('本文を作成しています…（1〜2分かかります）');

      articles.unshift(a);
      renderList();
      return generateArticle(a);
    }).then(function (w) {
      warns = w || [];

      /* 手動指定が無いときは、ここで初めてカテゴリーを決める。
         商品名ではなく、できあがった本文とタグから判定する。 */
      if (!picked) {
        var decided = categoryFromContent(a);
        if (decided && decided.category) {
          var dc = (site.categories || []).filter(function (c) {
            return c.key === decided.category;
          })[0] || {};
          a.category = decided.category;
          a.sub = decided.sub || '';
          if (dc.icon) a.icon = dc.icon;
          qpLog('カテゴリー：' + (dc.label || decided.category) +
                (a.sub ? '（' + a.sub + '）' : '') +
                '（本文の内容から判定・違っていれば「記事」タブで直せます）');
        }
      }

      if (warns.length) {
        qpLog('要確認点を取り除いて整えています：' + warns.join(' / '));
        var idx = articles.indexOf(a);
        a = autoFixArticle(a);
        if (idx >= 0) articles[idx] = a;
        warns = auditArticle(a);
        if (warns.length) qpLog('取り除いた後も残る要確認点：' + warns.join(' / '), 'err');
      }
      /* 禁止表現などが残ったまま自動公開すると、CI（tools/check_text.py 等）
         に引っかかってビルドが止まり、それ以降の全ての変更がサイトに
         反映されなくなる。取り除いた後も残るときだけ下書きに留める。 */
      a.published = !warns.length;
      a.updated = today();
      renderList();
      qpLog('GitHubに保存しています…');
      return saveArticles();
    }).then(function () {
      if (a.published) {
        qpLog('公開しました：' + a.title, 'ok');
        toast('記事を公開しました。ビルドが終わるとサイトに反映されます', 'ok');
      } else {
        qpLog('要確認点があるため、下書きのまま保存しました：' + a.title, 'ok');
        toast('要確認点があるため下書きのまま保存しました。「記事」タブで内容を直してから公開してください', 'err');
      }
    }).catch(function (e) {
      qpLog('失敗しました：' + e.message, 'err');
      toast(e.message, 'err');
    }).then(function () {
      $('btnQpRun').disabled = false;
    });
  }

  if ($('btnQpRun')) $('btnQpRun').addEventListener('click', runQuickPost);

  /* ジャンルの選択肢を content/site.json から入れる。site.json が
     読めてから呼ぶ必要があるため renderAll() 経由で実行する。 */
  function fillQpCategory() {
    var sel = $('qpCategory');
    if (!sel || !site || !site.categories) return;
    var keep = sel.value;
    sel.innerHTML = '<option value="">自動判定（商品名から推測）</option>' +
      site.categories.map(function (c) {
        return '<option value="' + c.key + '">' + (c.icon || '') + ' ' + c.label + '</option>';
      }).join('');
    sel.value = keep;
  }
  window.fillQpCategory = fillQpCategory;

  /* ==================================================== 他の端末へ接続設定を渡す
     GitHubトークン・APIキーは端末のlocalStorageにしか無いため、スマホで
     開くと空になる。QRコードにこの端末の設定を載せ、読み取った端末の
     URLハッシュ（#sync=...）から取り込む。サーバーには一切送らない。 */
  var SYNC_KEYS = [LS, GM_KEY, CL_KEY, FIND_KEYS];

  function buildSyncUrl() {
    var payload = {};
    SYNC_KEYS.forEach(function (k) {
      var v = null;
      try { v = localStorage.getItem(k); } catch (e) {}
      if (v) payload[k] = v;
    });
    if (!Object.keys(payload).length) return null;
    var enc = encodeURIComponent(b64encode(JSON.stringify(payload)));
    return location.origin + location.pathname + '#sync=' + enc;
  }

  function showSyncQr() {
    var url = buildSyncUrl();
    var box = $('syncQrBox');
    if (!url) { toast('渡せる接続情報がまだありません', 'err'); return; }
    if (!box || typeof QRCode === 'undefined') {
      toast('QRコードの部品を読み込めませんでした', 'err');
      return;
    }
    box.innerHTML = '';
    box.hidden = false;
    try {
      new QRCode(box, { text: url, width: 220, height: 220, correctLevel: QRCode.CorrectLevel.L });
    } catch (e) {
      toast('QRコードを作れませんでした：' + e.message, 'err');
    }
  }

  function hideSyncQr() {
    var box = $('syncQrBox');
    if (box) { box.hidden = true; box.innerHTML = ''; }
  }

  if ($('btnSyncQr')) $('btnSyncQr').addEventListener('click', showSyncQr);
  if ($('btnSyncQrHide')) $('btnSyncQrHide').addEventListener('click', hideSyncQr);

  /* 読み取った側：ページを開いた時点で #sync= が付いていれば取り込む */
  (function importSync() {
    var m = /#sync=([^&]+)/.exec(location.hash);
    if (!m) return;
    history.replaceState(null, '', location.pathname + location.search);
    var payload;
    try { payload = JSON.parse(b64decode(decodeURIComponent(m[1]))); } catch (e) {
      toast('接続情報の読み込みに失敗しました', 'err');
      return;
    }
    if (!confirm('読み取った接続情報を、この端末に設定します。よろしいですか？')) return;
    Object.keys(payload).forEach(function (k) {
      try { localStorage.setItem(k, payload[k]); } catch (e) {}
    });
    toast('接続情報を取り込みました。ページを再読み込みします', 'ok');
    setTimeout(function () { location.reload(); }, 900);
  })();

})();
