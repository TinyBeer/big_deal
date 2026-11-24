#!/usr/bin/env python3
"""线条解放辅助 · 每轮全量识别后批量点击。

流程：抓图 → 复活页检测 + 爱心计数 → 全量识别找出当前所有可移除线条
→ 依次点击这批线条 → 重新抓图进入下一轮，直到无可点击线条或命中停止条件。
"""
import argparse
import json
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
import lines_vision as lv  # noqa: E402
from common.adb import tap  # noqa: E402
from common.notify import add_notify_args, send_notify  # noqa: E402
from common.screen import grab  # noqa: E402

TOOL_NAME = "线条解放"


def grab_stable(serial, min_wait=0.20, max_wait=1.2, interval=0.10):
    """每轮识别前等画面稳定，避免线条飞行途中被识别成空位。"""
    time.sleep(min_wait)
    prev, img, start = None, None, time.time()
    while time.time() - start < max_wait:
        img = grab(serial)
        if img is None:
            return None
        small = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (270, 600))
        if prev is not None and np.mean(cv2.absdiff(small, prev)) / 255.0 < 0.008:
            return img
        prev = small
        time.sleep(interval)
    return img


def _finish(args, message, done):
    print(message, flush=True)
    if args.notify:
        send_notify(message, args, TOOL_NAME, tool_slug="lines", serial=args.device)
    return done


def _limit_reached(args, done, started):
    if args.max_clicks > 0 and done >= args.max_clicks:
        return "达到 --max-clicks=%d 上限，停手" % args.max_clicks
    if args.max_seconds > 0 and time.time() - started >= args.max_seconds:
        return "达到 --max-seconds=%d 秒上限，停手" % args.max_seconds
    return None


def auto_run(args):
    if args.image and not args.dry_run:
        print("提示: --image 仅用于离线试运行，已自动按试运行处理", flush=True)
        args.dry_run = True

    if args.click_log and args.output and not args.dry_run:
        log_path = os.path.join(os.path.dirname(os.path.abspath(args.output)),
                                "lines_clicks.jsonl")
        open(log_path, "w", encoding="utf-8").close()

    done = 0
    started = time.time()
    hearts = None
    saved = False
    locked_grid = None
    while True:
        limit = _limit_reached(args, done, started)
        if limit:
            return _finish(args, limit, done)

        # 每轮都做一次完整识别；识别时顺便检查复活页和爱心
        img = items = info = None
        for attempt in range(2):
            img = cv2.imread(args.image) if args.image else grab_stable(args.device)
            if img is None:
                return _finish(args, "抓图失败，停手", done)
            if lv.detect_revive(img):
                return _finish(args, "检测到复活页面，立即停手", done)
            now = lv.count_hearts(img)
            if now <= 0:
                return _finish(args, "检测到复活/弹窗页面（顶部爱心不可见），立即停手", done)
            if args.verify and hearts is not None and now < hearts:
                return _finish(args, "爱心 %d → %d，上一批点击有误，停手" %
                               (hearts, now), done)
            hearts = now
            try:
                info = lv.analyze(img, steps=0, grid=locked_grid)
            except (RuntimeError, cv2.error):
                if locked_grid is not None:
                    locked_grid = None
                    continue
                if attempt:
                    return _finish(args, "画面无棋盘网格，停手（可能已通关）", done)
                time.sleep(0.3)
                continue
            if locked_grid is None:
                locked_grid = (info["xs"], info["ys"], info["step"])
            items = lv.free_lines(info)
            if items or attempt:
                break
            time.sleep(0.3)  # 动画未落定时重抓一次，避免误判为清空

        if not items:
            return _finish(args, "已无可点击线条，完成（共点击 %d 条）" % done, done)

        if not saved and args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            cv2.imwrite(args.output, lv.annotate(img, info))
            print("saved", args.output, flush=True)
            saved = True
        print(json.dumps({
            "clickable": len(items),
            "clicks": [item["click"] for item in items],
            "hearts": hearts,
            "done": done,
        }, ensure_ascii=False), flush=True)
        if args.dry_run:
            print("试运行结束，未点击", flush=True)
            return 0

        batch = items if args.batch_size <= 0 else items[:args.batch_size]
        for item in batch:
            limit = _limit_reached(args, done, started)
            if limit:
                return _finish(args, limit, done)
            x, y = item["click"]
            tap(x, y, args.device, touch=args.touch)
            done += 1
            if args.click_log:
                print("点击 #%d: (%d, %d) 方向=%s 线#%d 节点%d" %
                      (done, x, y, item["direction"], item["id"],
                       len(item["nodes"])), flush=True)
            else:
                print("点击 #%d: (%d, %d) 方向=%s" %
                      (done, x, y, item["direction"]), flush=True)
            if args.click_log and args.output:
                log_path = os.path.join(os.path.dirname(os.path.abspath(args.output)),
                                        "lines_clicks.jsonl")
                with open(log_path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({
                        "time": round(time.time(), 2),
                        "seq": done,
                        "line_id": item["id"],
                        "click": item["click"],
                        "tip": item["tip"],
                        "direction": item["direction"],
                        "nodes": item["nodes"],
                    }, ensure_ascii=False) + "\n")
            time.sleep(args.gap)
        time.sleep(args.batch_wait)


def main():
    ap = argparse.ArgumentParser(description="每轮全量识别并批量点击可解放线条")
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--image", help="本地截图（仅用于离线试运行）")
    ap.add_argument("--output", default="outputs/lines_annotated.png")
    ap.add_argument("--steps", type=int, default=0, help="兼容参数，自动模式忽略")
    ap.add_argument("--max-clicks", type=int, default=0, help="最多点击条数（0=不限）")
    ap.add_argument("--max-seconds", type=int, default=600, help="最长运行时长秒数（0=不限）")
    ap.add_argument("--rescan", type=int, default=0, help="兼容参数，当前每轮均全量识别")
    ap.add_argument("--batch-size", type=int, default=4, help="每批最多点击条数（0=不限）")
    ap.add_argument("--gap", type=float, default=0.45, help="同一批内点击间隔秒数")
    ap.add_argument("--batch-wait", type=float, default=0.80, help="两轮识别之间等待秒数")
    ap.add_argument("--touch", action="store_true", help="使用 input touchscreen tap")
    ap.add_argument("--no-verify", dest="verify", action="store_false",
                    help="不按爱心数逐批复核（复活页检测仍生效）")
    ap.set_defaults(verify=True)
    ap.add_argument("--dry-run", action="store_true", help="只识别当前可点击线条，不真点")
    ap.add_argument("--click-log", action="store_true",
                    help="逐次写入 outputs/lines_clicks.jsonl 并打印线号（默认关闭）")
    add_notify_args(ap, "lines", TOOL_NAME)
    args = ap.parse_args()
    auto_run(args)


if __name__ == "__main__":
    main()
