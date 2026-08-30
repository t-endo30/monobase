# assets/vendor

外部ライブラリを置く場所。CDNからではなく、ここに置いたものを読み込む。
サイトの表示が外部サービスの可用性に左右されないようにするため。

## motion-mini.min.js

- Motion（motion.dev / framer-motion）の DOM 版から、使う機能だけを取り出したもの
- 含まれるのは `animate` / `hover` / `press` / `inView` の4つ
- 11KB（gzip 約4.4KB）。フル版は約137KBあるため、それは使わない
- ライセンス：MIT（Framer B.V.）
- 作り直す手順：

```bash
npm i motion@13.1.1
cat > entry.mjs <<'JS'
export { animate } from 'framer-motion/dom/mini';
export { hover, press, inView } from 'framer-motion/dom';
JS
npx esbuild entry.mjs --bundle --format=iife --global-name=Motion --minify \
  --outfile=assets/vendor/motion-mini.min.js
```

## qrcode.min.js

- 管理画面の「接続」タブで、接続設定を他の端末（スマホ等）にQRコードで渡すために使う
- davidshimjs/qrcodejs（`QRCode` というグローバル変数を作る）
- 約19KB。ライセンス：MIT
