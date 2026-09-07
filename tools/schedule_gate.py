#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""今日が「記事を作る日」かどうかを判定する。

週に何回まわすか、1日に何本作るかは content/site.json の automation で決める。
GitHub Actions のワークフロー側に回数を書くと、変えるたびに
YAMLを編集してコミットすることになるため、設定はサイト側に置いて
管理画面から変えられるようにしている。

  automation.runs_per_week    1〜7（週に何回まわすか）
  automation.articles_per_run 1〜10（1日に合計何本作るか）
  automation.auto_publish     true なら公開まで自動で行う
  automation.enabled          false なら自動実行そのものを止める

判定の考え方
  週7日を runs_per_week 等分し、その日付に当たる曜日だけ実行する。
  例）2回 → 月曜と木曜。3回 → 月・水・金。7回 → 毎日。
  曜日は月曜を0とする（cron は毎日まわし、この判定で間引く）。

  1日の本数が多いと1回のジョブが長くなり、90分のタイムアウトに
  かかりやすくなる。そのため1回のジョブは最大 BATCH_SIZE 本までとし、
  それを超える分は同じ日の2回目・3回目の cron 実行（ワークフロー側の
  on.schedule に並べた時刻）に割り振る。何回目の実行かは
  github.event.schedule（実際にマッチした cron 式）で渡してもらう。
  例）1日10本・BATCH_SIZE=5 → 1回目5本・2回目5本。1日5本以下なら1回目だけ。

  $ python3 tools/schedule_gate.py                        # 判定結果を表示
  $ python3 tools/schedule_gate.py --force                # 曜日の判定を飛ばす（手動実行用）
  $ python3 tools/schedule_gate.py --schedule "0 4 * * *" # 何回目の枠かをcron式で渡す
"""
import argparse, io, json, os, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BATCH_SIZE = 5

# ワークフローの on.schedule に並んでいる cron 式と同じ順番で書く。
# 何番目に一致したかで「今日の何回目の枠か」を判定する。
SCHEDULE_SLOTS = [
    "0 20 * * *",  # 1回目 5:00 JST
    "0 4 * * *",   # 2回目 13:00 JST
]


def clamp(v, lo, hi, default):
    try:
        n = int(v)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def run_days(n):
    """週 n 回のとき、実行する曜日（月=0）の一覧。"""
    return sorted({round(i * 7 / n) % 7 for i in range(n)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="曜日の判定を飛ばす（自動作成が「停止中」なら、それでも実行しない）")
    ap.add_argument("--date", default="", help="判定する日付（YYYY-MM-DD／試験用）")
    ap.add_argument("--schedule", default="",
                    help="実際にマッチした cron 式（github.event.schedule）。"
                         "手動実行など空のときは1回目の枠として扱う")
    args = ap.parse_args()

    site = json.load(io.open(os.path.join(ROOT, "content", "site.json"),
                             encoding="utf-8"))
    a = site.get("automation") or {}
    n = clamp(a.get("runs_per_week"), 1, 7, 1)
    total = clamp(a.get("articles_per_run"), 1, 10, 5)
    auto_publish = a.get("auto_publish") is not False      # 既定は公開まで自動
    enabled = a.get("enabled") is not False

    today = date.fromisoformat(args.date) if args.date else date.today()
    days = run_days(n)
    # enabled は最後の元栓。手動で叩いたとき（--force）も、ここが切れていれば動かさない。
    # 管理画面でオフにしたつもりが裏で動いていた、という状態を作らないため。
    is_run_day = enabled and (args.force or today.weekday() in days)

    # 1日の合計本数を BATCH_SIZE 本ずつに割り、何回目の枠かで
    # 今回作る本数を決める。枠が余っている（総本数を使い切っている）
    # ときは、その回は何もしない。
    import math
    batches = max(1, math.ceil(total / BATCH_SIZE))
    try:
        slot = SCHEDULE_SLOTS.index(args.schedule) if args.schedule else 0
    except ValueError:
        slot = 0  # 知らない cron 式（手動実行など）は1回目扱い
    run = is_run_day and slot < batches
    count = min(BATCH_SIZE, total - slot * BATCH_SIZE) if run else 0

    names = "月火水木金土日"
    print(f"週 {n} 回（{'・'.join(names[d] for d in days)}）/ 1日合計 {total} 本"
          f"（1回最大 {BATCH_SIZE} 本・{batches} 回に分割）/ "
          f"公開まで自動：{'はい' if auto_publish else 'いいえ'} / "
          f"自動実行：{'有効' if enabled else '停止中'}")
    if not enabled:
        print("自動作成は管理画面で停止中です → 実行しません")
    elif not is_run_day:
        print(f"今日は {names[today.weekday()]}曜日 → 実行しません")
    elif not run:
        print(f"{slot + 1}回目の枠ですが、今日の分は前の枠で作り切っています → 実行しません")
    else:
        print(f"今日は {names[today.weekday()]}曜日、{slot + 1}回目の枠 → {count} 本作ります")

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with io.open(out, "a", encoding="utf-8") as f:
            f.write(f"run={'true' if run else 'false'}\n")
            f.write(f"count={count}\n")
            f.write(f"auto_publish={'true' if auto_publish else 'false'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
