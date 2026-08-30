// このファイルを build.py が worker.js として書き出します。
// 編集するときは tools/worker.template.js のほうを直してください。
//
// この Worker の役割は3つ。
//   1. 管理画面の入口をそろえる
//      /admin.html を /admin に寄せる。保護そのものは Cloudflare Access
//      （Zero Trust）が担当していて、そちらは /admin を見張っている。
//      入口が2つあると片方だけ素通りしてしまうため、ここで1つにまとめる。
//   2. メンテナンス表示
//      有効なあいだ、全ページを 503 の「準備中」に差し替える。
//   3. Yahoo!ショッピングAPIの中継（/api/yahoo）
//      楽天のAPIはブラウザから直接呼べるが、Yahoo!のAPIは CORS を許して
//      いないため、ブラウザから直接は呼べない。ここで中継する。
//      中継先はYahoo!のAPIだけに固定し、Cloudflare Access を通った
//      リクエストしか受け付けない（誰でも使える踏み台にしないため）。
//   4. 商品ページの取得（/api/fetch-product）
//      「URLから記事を作る」タブが使う。Amazon・楽天・Yahoo!の商品ページは
//      ブラウザから直接fetchするとCORSで弾かれるため、ここで代わりに取得し、
//      タイトル・画像・価格などのメタ情報だけを抜き出して返す。
//      対象ドメインを固定し、Cloudflare Access を通ったリクエストしか
//      受け付けない（誰でも使える踏み台にしないため）。

const MAINTENANCE = __MAINTENANCE__;

// メンテナンス中でも通すもの（準備中の画面が崩れないように）
const MAINT_ALLOW = ["/assets/", "/maintenance.html", "/maintenance", "/admin"];

// 中継してよい問い合わせ先。ここに無いものは通さない。
const YAHOO_ENDPOINT =
  "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch";

// 中継で受け渡す検索条件。想定外の項目は落とす。
const YAHOO_PARAMS = [
  "appid", "query", "jan_code", "genre_category_id", "results", "start",
  "sort", "price_from", "price_to", "in_stock", "condition",
];

async function proxyYahoo(request, url) {
  // Cloudflare Access を通っていないリクエストは断る。
  // Access は /admin と /api/ を見張る設定にしておくこと。
  // この見出しが無いということは、認証を通っていないということ。
  if (!request.headers.get("Cf-Access-Jwt-Assertion")) {
    return json({
      error:
        "Cloudflare Access を通っていないため使えません。" +
        "Zero Trust → Access → アプリケーション → モノベース管理画面 を開き、" +
        "対象のパスに /api/ を追加してください（/admin だけでは、この入口は保護されません）。",
    }, 403);
  }

  const q = new URLSearchParams();
  for (const k of YAHOO_PARAMS) {
    const v = url.searchParams.get(k);
    if (v) q.set(k, v);
  }
  if (!q.get("appid")) {
    return json({ error: "Yahoo!のClient IDが設定されていません" }, 400);
  }

  try {
    const res = await fetch(YAHOO_ENDPOINT + "?" + q.toString(), {
      headers: { "User-Agent": "monobase-admin/1.0" },
      // 同じ検索を繰り返しても相手先を叩かないよう、10分だけ持たせる
      cf: { cacheTtl: 600, cacheEverything: true },
    });
    const body = await res.text();
    return new Response(body, {
      status: res.status,
      headers: {
        "content-type": "application/json; charset=utf-8",
        "cache-control": "no-store",
      },
    });
  } catch (e) {
    return json({ error: "Yahoo!のAPIに接続できません: " + e.message }, 502);
  }
}

// 商品ページの取得を許すドメイン。ここに無いものは通さない
// （任意のURLを取得できる踏み台にしないため）。
const PRODUCT_HOSTS = [
  "amazon.co.jp", "www.amazon.co.jp",
  "item.rakuten.co.jp",
  "store.shopping.yahoo.co.jp",
];

function hostAllowed(host) {
  return PRODUCT_HOSTS.some((h) => host === h || host.endsWith("." + h));
}

// ページ内の meta / title / JSON-LD だけを抜き出す。
// HTMLRewriter はストリームを流しながら書き換えられるAPIで、
// ページ全体を文字列に持たずに済む（大きなページでもメモリを圧迫しない）。
class MetaCollector {
  constructor(out) { this.out = out; }
  element(el) {
    const prop = el.getAttribute("property") || el.getAttribute("name");
    const content = el.getAttribute("content");
    if (prop && content) {
      if (prop === "og:title" || prop === "twitter:title") this.out.ogTitle = this.out.ogTitle || content;
      if (prop === "og:image" || prop === "twitter:image") this.out.ogImage = this.out.ogImage || content;
      if (prop === "product:price:amount") this.out.ogPrice = this.out.ogPrice || content;
    }
  }
}

class TitleCollector {
  constructor(out) { this.out = out; this.buf = ""; }
  text(chunk) {
    this.buf += chunk.text;
    if (chunk.lastInTextNode) this.out.title = this.buf.trim();
  }
}

class JsonLdCollector {
  constructor(out) { this.out = out; this.out.jsonld = []; this.buf = ""; }
  text(chunk) {
    this.buf += chunk.text;
    if (chunk.lastInTextNode) { this.out.jsonld.push(this.buf); this.buf = ""; }
  }
}

// Amazonのページには og:title も JSON-LD も無く、<title> はSEO用の
// 長い文字列（ブランド名やキーワードの寄せ集め）なので使えない。
// 商品名がそのまま入る #productTitle を専用に拾う。
class ProductTitleCollector {
  constructor(out) { this.out = out; this.buf = ""; }
  text(chunk) {
    this.buf += chunk.text;
    if (chunk.lastInTextNode) this.out.productTitle = this.buf.trim();
  }
}

async function proxyFetchProduct(request, url) {
  if (!request.headers.get("Cf-Access-Jwt-Assertion")) {
    return json({
      error:
        "Cloudflare Access を通っていないため使えません。" +
        "Zero Trust → Access → アプリケーション → モノベース管理画面 を開き、" +
        "対象のパスに /api/ を追加してください。",
    }, 403);
  }

  const target = url.searchParams.get("url") || "";
  let parsed;
  try { parsed = new URL(target); } catch (e) {
    return json({ error: "URLの形が正しくありません" }, 400);
  }
  if (!hostAllowed(parsed.hostname)) {
    return json({ error: "対応していないサイトのURLです（Amazon・楽天市場・Yahoo!ショッピングのみ）" }, 400);
  }

  try {
    const res = await fetch(parsed.toString(), {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "ja-JP,ja;q=0.9",
      },
      cf: { cacheTtl: 0 },
    });
    if (!res.ok) return json({ error: "商品ページの取得に失敗しました（HTTP " + res.status + "）" }, 502);

    const out = {};
    const rewriter = new HTMLRewriter()
      .on('meta[property], meta[name]', new MetaCollector(out))
      .on('title', new TitleCollector(out))
      .on('#productTitle', new ProductTitleCollector(out))
      .on('script[type="application/ld+json"]', new JsonLdCollector(out));
    await rewriter.transform(res).arrayBuffer();

    return json({
      title: out.productTitle || out.ogTitle || out.title || "",
      image: out.ogImage || "",
      price: out.ogPrice || "",
      jsonld: out.jsonld || [],
    });
  } catch (e) {
    return json({ error: "商品ページに接続できません: " + e.message }, 502);
  }
}

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Yahoo!ショッピングAPIの中継
    if (path === "/api/yahoo") {
      return proxyYahoo(request, url);
    }

    // 商品ページの取得（URLから記事を作るタブが使う）
    if (path === "/api/fetch-product") {
      return proxyFetchProduct(request, url);
    }

    // 管理画面の入口は /admin だけにする。
    // Access は /admin を見張っているので、ここへ寄せれば必ず認証を通る。
    if (path === "/admin.html" || path === "/admin/") {
      return Response.redirect(new URL("/admin", url).toString(), 301);
    }

    // メンテナンス表示
    if (MAINTENANCE && !MAINT_ALLOW.some((p) => path === p || path.startsWith(p))) {
      const res = await env.ASSETS.fetch(new URL("/maintenance.html", url));
      return new Response(res.body, {
        status: 503,
        headers: {
          "content-type": "text/html; charset=utf-8",
          "cache-control": "no-store",
          "retry-after": "3600",
        },
      });
    }

    const res = await env.ASSETS.fetch(request);
    if (path === "/admin" || path.startsWith("/admin/")) {
      const out = new Response(res.body, res);
      out.headers.set("cache-control", "no-store");
      out.headers.set("x-robots-tag", "noindex, nofollow");
      return out;
    }
    return res;
  },
};
