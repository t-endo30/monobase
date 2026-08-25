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
    return json({ error: "この入口は管理画面からのみ使えます" }, 403);
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
