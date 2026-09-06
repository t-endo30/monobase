#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""記事ごとの英文プロンプトを組み立て、Gemini に画像を作らせる。

  $ python3 tools/make_images.py --dry-run          # プロンプトだけ確認
  $ python3 tools/make_images.py --slug mx-master-3s-review
  $ python3 tools/make_images.py --all --limit 5    # まとめて生成
  $ python3 tools/make_images.py --all --force      # 既存画像も作り直す

APIキー
  環境変数 GEMINI_API_KEY を読む。GitHub Actions では Secrets から渡す。
  ※ 公開リポジトリなのでキーをファイルに書かないこと。

作られる画像
  assets/img/gen/<slug>.jpg に保存し、articles.json の thumb を差し替える。

プロンプトの方針
  ・写真であることを明示し、カメラとレンズを指定する
  ・存在しない要素を作らせない。配置・照明・被写界深度を具体的に指定する
  ・質感（素材の手触り、光の反射）を指示する
  ・人物は全身を写さない。商品が主役
  ・ブランド名やロゴは出さない（商標・実物との誤認を避けるため）
"""
import argparse, base64, io, json, os, re, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A_PATH = os.path.join(ROOT, "content", "articles.json")
S_PATH = os.path.join(ROOT, "content", "site.json")
OUT_DIR = os.path.join(ROOT, "assets", "img", "gen")
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"

# サブカテゴリーごとの被写体と置き場所。商品名から作るより破綻しにくい。
SUBJECT = {
    ("pc", "monitor"):     ("a widescreen computer monitor on a wooden desk",
                            "a tidy home office desk"),
    ("pc", "input"):       ("a computer mouse and a low-profile keyboard",
                            "a wooden desk beside a closed notebook"),
    ("pc", "peripheral"):  ("a compact aluminium USB-C docking hub with cables plugged in",
                            "a desk next to a laptop edge"),
    ("pc", "network"):     ("a white Wi-Fi router with upright antennas",
                            "a shelf beside a small plant"),
    ("pc", "tablet"):      ("an e-ink reading tablet lying flat",
                            "a linen bedside table with a mug"),
    ("pc", "laptop"):      ("a thin silver laptop, lid open at an angle",
                            "a bright desk near a window"),
    ("pc", "storage"):     ("a small external SSD drive and a short cable",
                            "a slate grey desk surface"),
    ("av", "mic"):         ("a small wireless lavalier microphone and its charging case",
                            "a matte grey table"),
    ("av", "headphone"):   ("a pair of over-ear headphones resting on their side",
                            "a wooden desk"),
    ("av", "speaker"):     ("a fabric-covered desktop speaker",
                            "a shelf against a plain wall"),
    ("av", "tv"):          ("a slim projector unit facing slightly away",
                            "a low sideboard in a dim living room"),
    ("appliance", "light"):    ("a slim LED light fixture switched on",
                                "a plain ceiling or a desk edge"),
    ("appliance", "aircon"):   ("a floor-standing fan or a steam humidifier, front three-quarter view",
                                "a bright living room floor beside a curtain"),
    ("appliance", "smart"):    ("a small square smart home hub with a status light",
                                "a shelf beside a remote control"),
    ("appliance", "clean"):    ("a cordless stick vacuum standing upright",
                                "a wooden floor in a bright room"),
    ("furniture", "desk"):     ("an adjustable footrest under a desk",
                                "a wooden floor beneath a desk"),
    ("furniture", "chair"):    ("an ergonomic office chair, three-quarter view",
                                "a bright room with a plain wall"),
    ("furniture", "shelf"):    ("a slim metal shelving rack holding a few objects",
                                "beside a desk against a plain wall"),
    ("furniture", "bed"):      ("a single pillow on a made bed",
                                "a bedroom with soft morning light"),
    ("daily", "clean"):        ("a tall slim rubbish bin",
                                "a narrow gap beside a kitchen counter"),
    ("daily", "safety"):       ("a small outdoor security camera on a wall mount",
                                "an exterior wall under an eave"),
    ("health", "measure"):     ("a smartwatch lying flat, screen facing up",
                                "a wooden table beside a notebook"),
    ("feature", "compare"):    ("three unbranded consumer gadgets lined up in a row",
                                "a clean light grey studio surface"),
}
DEFAULT_SUBJECT = ("a single unbranded consumer product",
                   "a clean light grey studio surface")

CAMERA = ("Shot on a full-frame mirrorless camera with an 85mm f/1.8 prime lens, "
          "ISO 200, 1/125s, shallow depth of field")
# 背景・光・角度は全記事で固定する。一覧に並んだときに紙面がそろわないと、
# 記事ごとに別のサイトのように見えるため。変えるのは被写体（SUBJECT）だけ。
SETTING = ("a flat light oak wood tabletop in front of a plain matte white wall, "
           "nothing else on the surface")
LIGHT = ("lit by soft diffused daylight from a large window on the left, "
         "a subtle fill from the right, gentle natural shadows that stay short")
QUALITY = ("photorealistic, natural material texture — visible plastic grain, brushed metal, "
           "woven fabric and wood grain, realistic specular highlights and soft reflections, "
           "accurate white balance, fine surface detail, no digital smoothing")
NEGATIVE = ("Do not produce: illustration, 3D render, CGI, cartoon or anime style, "
            "heavy retouching or plastic-looking surfaces, oversaturated colours, HDR glow, "
            "brand logos, readable text, watermarks, full human figures or faces, "
            "distorted or extra fingers, warped straight edges, duplicated objects, "
            "props or decorative objects, patterned or coloured walls, "
            "floating or physically impossible arrangements, cluttered background.")


def product_of(a):
    """記事が扱っている商品の名前。分野ごとの当たり障りない被写体だけを
       渡すと、記事と違う形の物が出てくるため、商品名も添える。"""
    t = str(a.get("product_name") or a.get("title") or "")
    t = re.split(r"[｜|]", t)[0]
    t = re.sub(r"[（(\[【][^）)\]】]*[）)\]】]", " ", t)
    t = re.sub(r"(の)?(口コミ|レビュー|評価|選び方|比較|仕様分析|徹底比較).*$", "", t)
    # 「◯◯の電気代と静音性」のような、記事の切り口までは被写体ではない
    t = re.sub(r"の(電気代|静音性|選び方|比較|違い|注意点|使い方|評判|実力|効果|設置条件|向き不向き).*$", "", t)
    return re.sub(r"\\s+", " ", t).strip()


def build_prompt(a, site):
    """記事1本ぶんの英文プロンプトを組み立てる。"""
    key = (a.get("category", ""), a.get("sub", ""))
    subject, _setting = SUBJECT.get(key, DEFAULT_SUBJECT)
    # 商品名が分かるときは、それだけを渡す。分野ごとの被写体を添えると
    # 食い違うことがある（Anker PowerConf S360 はスピーカーフォンなのに、
    # AV分野の被写体は「ラベリアマイク」だった）。
    prod = product_of(a)
    if prod:
        subject = prod
    # SUBJECT の置き場所（_setting）は使わない。背景は SETTING に固定する。
    return (
        f"A photograph of {subject}, placed on {SETTING}. "
        f"The product fills about 70 percent of the frame, positioned slightly off-centre "
        f"following the rule of thirds, seen from a natural eye-level three-quarter angle. "
        f"Use exactly this framing, background, and lighting for every image so that all "
        f"article thumbnails look like one consistent series; only the product changes. "
        f"No props, no decorations, no plants, no people. "
        f"{CAMERA}, background softly blurred so the product stays sharp. "
        f"{LIGHT}. "
        f"{QUALITY}. "
        # 商品の形は実物どおりに、ロゴだけを外す。
        # 「一般的な製品として描け」だけでは、モデルがそれらしいロゴを
        # 勝手に足す（ANKERの綴りが左右反転した絵が出ていた）。
        f"Render the product's real shape, proportions, colour, materials and the "
        f"placement of its buttons and ports faithfully. "
        f"Show NO logos, brand names, trademarks, model numbers, printed or embossed "
        f"lettering anywhere on the product — leave those surfaces completely blank. "
        f"Do not invent, distort or approximate any logo or lettering. "
        f"Landscape orientation, 16:9. "
        f"{NEGATIVE}"
    )


def generate(prompt, api_key, model, aspect="16:9"):
    """Gemini に画像を作らせ、バイト列で返す。"""
    body = json.dumps({
        "model": model,
        "input": [{"type": "text", "text": prompt}],
        "response_format": {"type": "image", "mime_type": "image/jpeg",
                            "aspect_ratio": aspect, "image_size": "1K"},
    }).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=180) as res:
        data = json.load(res)

    # 応答の形は版によって差があるため、画像データのある場所を順に探す
    b64 = None
    if isinstance(data.get("output_image"), dict):
        b64 = data["output_image"].get("data")
    if not b64:
        for out in (data.get("output") or []):
            if isinstance(out, dict):
                if out.get("type") == "image" and out.get("data"):
                    b64 = out["data"]; break
                for part in (out.get("content") or []):
                    if isinstance(part, dict) and part.get("data"):
                        b64 = part["data"]; break
    if not b64:
        for cand in (data.get("candidates") or []):
            for part in ((cand.get("content") or {}).get("parts") or []):
                inline = part.get("inline_data") or part.get("inlineData")
                if inline and inline.get("data"):
                    b64 = inline["data"]; break
    if not b64:
        raise RuntimeError("応答に画像が含まれていません: "
                           + json.dumps(data, ensure_ascii=False)[:400])
    return base64.b64decode(b64)


def compress(raw, max_w=1200, quality=78):
    """1枚あたりの上限（tools/check_images.py の 300KB）に収まるよう縮める。
       Pillow が無い環境では、そのまま返して警告する。"""
    try:
        from PIL import Image
    except ImportError:
        print("  ※ Pillow が無いため圧縮していません（pip install pillow）")
        return raw
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
    for q in (quality, 70, 62, 55):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        if buf.tell() <= 290 * 1024:
            return buf.getvalue()
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="対象の記事（未指定なら --all が必要）")
    ap.add_argument("--all", action="store_true", help="画像のない記事すべて")
    ap.add_argument("--limit", type=int, default=0, help="1回に作る枚数の上限")
    ap.add_argument("--force", action="store_true", help="既に画像がある記事も作り直す")
    ap.add_argument("--dry-run", action="store_true", help="プロンプトを表示するだけ")
    args = ap.parse_args()

    arts = json.load(io.open(A_PATH, encoding="utf-8"))
    site = json.load(io.open(S_PATH, encoding="utf-8"))
    conf = site.get("images") or {}
    model = conf.get("model") or "gemini-3.1-flash-image"

    if args.slug:
        targets = [a for a in arts if a["slug"] == args.slug]
        if not targets:
            print(f"::error::{args.slug} が見つかりません"); return 1
    elif args.all:
        targets = [a for a in arts if args.force or not a.get("thumb")]
    else:
        ap.print_help(); return 1
    if args.limit:
        targets = targets[:args.limit]

    if args.dry_run:
        for a in targets:
            print(f"── {a['slug']}（{a.get('category')}/{a.get('sub')}）")
            print(build_prompt(a, site)); print()
        print(f"{len(targets)} 件ぶんのプロンプトを表示しました（生成はしていません）")
        return 0

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("::error::GEMINI_API_KEY が設定されていません。"
              "ローカルでは export GEMINI_API_KEY=..., "
              "GitHub Actions では Secrets に登録してください。")
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)
    made, failed = 0, 0
    for a in targets:
        prompt = build_prompt(a, site)
        path = os.path.join(OUT_DIR, a["slug"] + ".jpg")
        print(f"生成中: {a['slug']} …", end="", flush=True)
        img = None
        # 429 は2通りある。混み合っているだけなら待てば通るが、
        # 利用枠を使い切っている場合は何回叩いても通らない。
        # 後者で32本ぶん叩き続けても意味がないので、そこで止める。
        for attempt in (1, 2, 3):
            try:
                img = generate(prompt, api_key, model)
                break
            except urllib.error.HTTPError as ex:
                body = ex.read().decode("utf-8", "replace")
                if ex.code == 429 and "exceeded your current quota" in body:
                    print(f" 失敗（利用枠の超過）\n  {body[:600]}")
                    print("\n::error::Geminiの利用枠を使い切っています。"
                          "枠が戻るまで待つか、課金の設定を確認してください。"
                          "ここで中断します（叩き続けても通らないため）。")
                    return 1
                if ex.code in (429, 500, 502, 503) and attempt < 3:
                    wait = 20 * attempt
                    print(f" 混み合い（HTTP {ex.code}）。{wait}秒待って再試行 …",
                          end="", flush=True)
                    time.sleep(wait)
                    continue
                print(f" 失敗（HTTP {ex.code}）\n  {body[:600]}")
                break
            except Exception as ex:                  # noqa: BLE001
                if attempt < 3:
                    print(f" 失敗（{ex}）。20秒待って再試行 …", end="", flush=True)
                    time.sleep(20)
                    continue
                print(f" 失敗（{ex}）")
        if img is None:
            failed += 1
            continue
        img = compress(img)
        with open(path, "wb") as f:
            f.write(img)
        a["thumb"] = f"assets/img/gen/{a['slug']}.jpg"
        a["image_prompt"] = prompt
        made += 1
        print(f" 完了（{len(img) // 1024} KB）")
        time.sleep(1)                                 # 連続実行を避ける

    if made:
        json.dump(arts, io.open(A_PATH, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"\n✅ {made} 枚を作成し、articles.json を更新しました")
        print("   画像は必ず目で確認してから公開してください。")
        print("   $ python3 tools/optimize-images.sh などで圧縮も忘れずに")
    if failed:
        print(f"\n::warning::{failed} 本は作れませんでした。")
    # 1枚も作れなかったときは、手順として失敗させる。
    # 0 を返すと GitHub Actions が緑で終わり、
    # 32本まるごと失敗していても気づけない（実際にそうなった）。
    if targets and not made:
        print("::error::1枚も作れませんでした。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
