// このファイルは build.py が生成します。直接編集しないでください。
// メンテナンス表示の切り替えは、管理画面（サイト設定）から行います。
const MAINTENANCE = false;

// 停止中でも通すパス。管理画面から復旧の操作ができるようにしておく。
const ALLOW = ["/admin", "/admin.html", "/assets/", "/content/", "/maintenance.html"];

export default {
  async fetch(request, env) {
    if (!MAINTENANCE) return env.ASSETS.fetch(request);

    const url = new URL(request.url);
    if (ALLOW.some((p) => url.pathname === p || url.pathname.startsWith(p))) {
      return env.ASSETS.fetch(request);
    }

    const page = await env.ASSETS.fetch(new URL("/maintenance.html", url));
    return new Response(page.body, {
      status: 503,
      headers: {
        "content-type": "text/html; charset=utf-8",
        "cache-control": "no-store",
        "retry-after": "3600",
      },
    });
  },
};
