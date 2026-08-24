// このファイルを build.py が worker.js として書き出します。
// 編集するときは tools/worker.template.js のほうを直してください。
//
// この Worker の役割は2つ。
//   1. 管理画面の保護
//      /admin* は、パスワードを知っている人だけに通す。判定はサーバー側で
//      行うので、URLを直接叩かれても中身は返らない。
//   2. メンテナンス表示
//      有効なあいだ、全ページを 503 の「準備中」に差し替える。
//
// パスワードはリポジトリに置かない。Cloudflare の Worker 設定に
// シークレットとして登録した値を読む。
//   ADMIN_PASSWORD … 管理画面のパスワード
//   ADMIN_SECRET   … ログイン状態の署名に使うランダムな文字列
// 未設定のときは、設定手順を出したうえで通さない（開いたままにしない）。

const MAINTENANCE = __MAINTENANCE__;

const ADMIN_PATHS = ["/admin", "/admin.html"];
const MAINT_ALLOW = ["/assets/", "/maintenance.html", "/maintenance"];

const COOKIE = "mb_admin";
const SESSION_HOURS = 12;
const enc = new TextEncoder();

function isAdminPath(p) {
  return ADMIN_PATHS.includes(p) || p.startsWith("/admin/");
}

async function hmac(secret, data) {
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(data));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

// 応答時間から中身を推測されないよう、長さをそろえて比較する
function sameString(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

async function makeToken(secret) {
  const exp = Date.now() + SESSION_HOURS * 3600 * 1000;
  return exp + "." + (await hmac(secret, String(exp)));
}

async function validToken(secret, token) {
  if (!token) return false;
  const [exp, sig] = token.split(".");
  if (!exp || !sig) return false;
  if (Number(exp) < Date.now()) return false;
  return sameString(sig, await hmac(secret, exp));
}

function readCookie(request, name) {
  const raw = request.headers.get("cookie") || "";
  for (const part of raw.split(";")) {
    const [k, ...v] = part.trim().split("=");
    if (k === name) return decodeURIComponent(v.join("="));
  }
  return "";
}

function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function shell(title, body, status) {
  const html = '<!doctype html><html lang="ja"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<meta name="robots" content="noindex,nofollow">' +
    "<title>" + esc(title) + "</title><style>" +
    ":root{color-scheme:light}*{box-sizing:border-box}" +
    "body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;" +
    "padding:24px;background:#1F2430;color:#1F2430;" +
    'font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",sans-serif}' +
    ".box{width:100%;max-width:360px;background:#fff;border-radius:14px;padding:30px 26px;" +
    "box-shadow:0 18px 60px rgba(0,0,0,.4);text-align:center}" +
    ".mark{width:34px;height:34px;margin:0 auto 14px;border-radius:9px;background:#1F2430}" +
    "h1{font-size:18px;margin:0 0 6px}" +
    "p{font-size:13px;line-height:1.8;color:#6B7280;margin:0 0 16px}" +
    "label{display:block;text-align:left;font-size:11.5px;font-weight:700;color:#6B7280;margin:10px 0 4px}" +
    "input{width:100%;padding:11px 13px;font-size:15px;border:1px solid #DDDFE4;border-radius:9px}" +
    "input:focus{outline:none;border-color:#1F2430;box-shadow:0 0 0 3px rgba(31,36,48,.09)}" +
    "button{width:100%;margin-top:14px;padding:12px;font-size:15px;font-weight:700;color:#fff;" +
    "background:#1F2430;border:0;border-radius:999px;cursor:pointer}" +
    ".err{margin:14px 0 0;font-size:13px;font-weight:700;color:#C0392B}" +
    ".note{margin:18px 0 0;font-size:11.5px;line-height:1.9;color:#8A8D93;text-align:left}" +
    "code{background:#F1F2F5;padding:1px 5px;border-radius:4px;font-size:11px}" +
    "</style></head><body><div class=\"box\">" + body + "</div></body></html>";
  return new Response(html, {
    status: status || 200,
    headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" },
  });
}

function loginPage(err, next) {
  return shell("ログイン - モノベース 管理画面",
    '<p class="mark"></p>' +
    "<h1>モノベース 管理画面</h1>" +
    "<p>パスワードを入力してください。</p>" +
    '<form method="POST" action="/admin/login" autocomplete="on">' +
    '<input type="hidden" name="next" value="' + esc(next || "/admin") + '">' +
    '<label for="u">ユーザー名</label>' +
    '<input id="u" name="username" value="admin" autocomplete="username" readonly>' +
    '<label for="p">パスワード</label>' +
    '<input id="p" name="password" type="password" autocomplete="current-password" autofocus>' +
    "<button type=\"submit\">ログイン</button></form>" +
    (err ? '<p class="err">' + esc(err) + "</p>" : ""),
    err ? 401 : 200);
}

function setupPage() {
  return shell("設定が必要です - モノベース 管理画面",
    '<p class="mark"></p>' +
    "<h1>パスワードが未設定です</h1>" +
    "<p>安全のため、設定が終わるまで管理画面は開けません。</p>" +
    '<div class="note">Cloudflare ダッシュボード → ' +
    "<b>Workers &amp; Pages → monobase → 設定 → 変数とシークレット</b><br>" +
    "次の2つを<b>シークレット</b>として追加してください。<br><br>" +
    "<code>ADMIN_PASSWORD</code> … 管理画面で使うパスワード<br>" +
    "<code>ADMIN_SECRET</code> … ログイン状態の署名用。推測できない長い文字列<br><br>" +
    "保存すると再デプロイされ、この画面がログイン画面に変わります。</div>",
    503);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // ---- 管理画面 ----------------------------------------------
    if (isAdminPath(path)) {
      const pass = env.ADMIN_PASSWORD;
      const secret = env.ADMIN_SECRET;
      if (!pass || !secret) return setupPage();

      if (path === "/admin/logout") {
        return new Response(null, {
          status: 302,
          headers: {
            location: "/admin",
            "set-cookie": COOKIE + "=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax",
          },
        });
      }

      if (path === "/admin/login") {
        if (request.method !== "POST") return loginPage("", "/admin");
        const form = await request.formData();
        const given = String(form.get("password") || "");
        let next = String(form.get("next") || "/admin");
        if (!next.startsWith("/") || next.startsWith("//")) next = "/admin";
        if (!sameString(given, pass)) return loginPage("パスワードが違います。", next);
        const token = await makeToken(secret);
        return new Response(null, {
          status: 302,
          headers: {
            location: next,
            "set-cookie": COOKIE + "=" + token + "; Path=/; Max-Age=" +
              SESSION_HOURS * 3600 + "; HttpOnly; Secure; SameSite=Lax",
          },
        });
      }

      if (!(await validToken(secret, readCookie(request, COOKIE)))) {
        return loginPage("", path);
      }
      const res = await env.ASSETS.fetch(request);
      const out = new Response(res.body, res);
      out.headers.set("cache-control", "no-store");
      out.headers.set("x-robots-tag", "noindex, nofollow");
      return out;
    }

    // ---- メンテナンス表示 ---------------------------------------
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

    return env.ASSETS.fetch(request);
  },
};
