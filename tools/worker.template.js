// このファイルを build.py が worker.js として書き出します。
// 編集するときは tools/worker.template.js のほうを直してください。
//
// この Worker の役割は2つ。
//   1. 管理画面の入口をそろえる
//      /admin.html を /admin に寄せる。保護そのものは Cloudflare Access
//      （Zero Trust）が担当していて、そちらは /admin を見張っている。
//      入口が2つあると片方だけ素通りしてしまうため、ここで1つにまとめる。
//   2. メンテナンス表示
//      有効なあいだ、全ページを 503 の「準備中」に差し替える。

const MAINTENANCE = __MAINTENANCE__;

// メンテナンス中でも通すもの（準備中の画面が崩れないように）
const MAINT_ALLOW = ["/assets/", "/maintenance.html", "/maintenance", "/admin"];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

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
