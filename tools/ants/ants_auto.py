#!/usr/bin/env python3
"""搬砖大战 · 自动搬运主循环。

策略（按用户要求）：
- 只检查弹窗、槽位、第一排候选块，不检查像素画。
- 复活弹窗命中立即停手；福利弹窗只点右上角 X 关闭。
- 开局看广告解锁槽位（可 --no-unlock 跳过）。
- 一次抓图批量挑多个第一排候选块（默认 3 个，同色不重复），按从左到右的次序点击；
  不考虑队列前移。
- 不读块上数字、不数格子；达到 --max-clicks 后停止。
- 连续无法决策（槽位满 / 无可用块 / 识别不到槽位或候选块）超过 --idle-timeout
  （默认 20 秒，0=不限）就停止；点击或关弹窗后计时清零。
- 已点击但尚未在槽位里看到入槽的颜色，留一个 --repeat-delay（默认 8 秒）冷却，
  避免搬运动画期间槽位看起来还空着而重复投同色。
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ants_vision import analyze, annotate, grab, CN, detect_queue  # noqa: E402

ROOT = "/home/beer/workspace/big_deal"
ANNOTATED = os.path.join(ROOT, "outputs", "ants_annotated.png")
RETURN_TEXTS = ("点击立即返回", "返回游戏")
NOTIFY_SCRIPT = "/sdcard/Scripts/ants_notify.js"
RUN_INTENT_ACTIVITY = "org.autojs.autojs6/org.autojs.autojs.external.open.RunIntentActivity"
# 点击后最少保护多久才允许因“已在槽里看到”而解除冷却。太短会在入槽动画
# 造成的识别抖动窗口里重复投同色（曾连投 3 个 peach）。
MIN_PENDING = 1.5


def log(msg):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print("[%s] %s" % (now, msg), flush=True)


def tap(serial, x, y):
    cmd = ["adb"] + (["-s", serial] if serial else []) + \
          ["shell", "input", "tap", str(int(x)), str(int(y))]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def key_back(serial):
    cmd = ["adb"] + (["-s", serial] if serial else []) + \
          ["shell", "input", "keyevent", "4"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def notify_phone(message, serial=None, script_path=NOTIFY_SCRIPT):
    """和其他工具一样，用 AutoJS6 在手机状态栏发通知。"""
    adb = ["adb"] + (["-s", serial] if serial else [])
    js = "notice(%s, %s);\n" % (
        json.dumps("搬砖大战", ensure_ascii=False),
        json.dumps(message, ensure_ascii=False))
    fd, tmp = tempfile.mkstemp(prefix="ants_notify_", suffix=".js")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(js)
        subprocess.run(adb + ["shell", "mkdir", "-p", "/sdcard/Scripts"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(adb + ["push", tmp, script_path], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)
        subprocess.run(adb + ["shell", "am", "start", "-n", RUN_INTENT_ACTIVITY,
                              "-d", "file://" + script_path, "-t", "text/javascript"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("提醒: 已发送通知: %s" % message, flush=True)
        return True
    except (OSError, subprocess.CalledProcessError) as e:
        print("提醒: 发送失败: %s" % e, flush=True)
        return False
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def dump_ui(serial=None):
    adb = ["adb"] + (["-s", serial] if serial else [])
    subprocess.run(adb + ["shell", "uiautomator", "dump", "/sdcard/window.xml"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    data = subprocess.run(adb + ["exec-out", "cat", "/sdcard/window.xml"],
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        return None


def find_text_node(root, keywords):
    if root is None:
        return None
    for node in root.iter("node"):
        text = node.get("text", "")
        if any(k in text for k in keywords):
            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
            if m:
                x1, y1, x2, y2 = [int(v) for v in m.groups()]
                if x2 > x1 and y2 > y1:
                    return ((x1 + x2) // 2, (y1 + y2) // 2), text
    return None


def watch_ad_return(serial, args):
    """看完广告后等待回到对局；遇到「点击立即返回」就点。"""
    time.sleep(args.ad_wait)
    start = time.time()
    while time.time() - start < max(0, args.ad_timeout - args.ad_wait):
        found = find_text_node(dump_ui(serial), RETURN_TEXTS)
        if found:
            pos, _ = found
            tap(serial, pos[0], pos[1])
            time.sleep(1.5)
        img = grab(serial)
        if img is not None and float(img.mean()) > 20 and len(detect_queue(img)) > 0:
            return True
        time.sleep(1)
    key_back(serial)
    return False


def unlock_all(serial, args):
    """开局看广告解锁槽位，返回解锁次数。"""
    unlocked = 0
    no_progress = 0
    for _ in range(args.max_unlock + 2):
        img = grab(serial)
        if img is None or float(img.mean()) < 15:
            time.sleep(1)
            continue
        info = analyze(img)
        if info["revive"]["found"]:
            log("解锁阶段检测到复活弹窗，停止解锁。")
            break
        if info["popup"]["found"]:
            tap(serial, info["popup"]["x"], info["popup"]["y"])
            time.sleep(0.5)
            continue
        pts = info["unlock"]
        if not pts:
            break
        x, y = pts[0]
        log("看广告解锁 %d: 点 (%d,%d)" % (unlocked + 1, x, y))
        tap(serial, x, y)
        ok = watch_ad_return(serial, args)
        unlocked += 1
        log("  解锁: " + ("成功返回对局" if ok else "未确认回到对局"))
        time.sleep(args.settle)
        after = grab(serial)
        if after is None:
            continue
        after_info = analyze(after)
        if after_info["popup"]["found"]:
            tap(serial, after_info["popup"]["x"], after_info["popup"]["y"])
            time.sleep(0.5)
        if len(after_info["unlock"]) >= len(pts):
            no_progress += 1
            if no_progress >= 2:
                log("解锁无进展，停止解锁继续游戏。")
                break
        else:
            no_progress = 0
    return unlocked


def choose_queue(info, occupied_colors, limit):
    """一次抓图选出最多 limit 个第一排候选块，按从左到右返回。

    只看两件事：槽里已有哪些颜色、第一排候选块有哪些颜色。
    同色不重复；不考虑队列前移。
    """
    busy = set(occupied_colors.keys())
    picked = []
    seen = set()
    for b in sorted(info.get("queue", []), key=lambda x: x["x"]):
        if b["color"] in busy or b["color"] in seen:
            continue
        seen.add(b["color"])
        picked.append(b)
        if len(picked) >= limit:
            break
    return picked


def main():
    ap = argparse.ArgumentParser(description="搬砖大战自动搬运")
    ap.add_argument("--device", help="adb 设备序列号（不填自动探测）")
    ap.add_argument("--dry-run", action="store_true", help="只打印决策，不真点")
    ap.add_argument("--max-clicks", type=int, default=0, help="最多点击次数，0=不限")
    ap.add_argument("--batch-size", type=int, default=3,
                    help="一次识别选几个第一排块，0=按空槽数全选")
    ap.add_argument("--interval", type=float, default=0.8, help="每轮间隔秒数")
    ap.add_argument("--idle-timeout", type=float, default=20.0,
                    help="连续无法决策的等待上限秒数，0=不限（默认 20）")
    ap.add_argument("--repeat-delay", type=float, default=8.0,
                    help="已点但尚未入槽的颜色，多少秒内不再重复点击（默认 8）")
    ap.add_argument("--no-annotate", action="store_true", help="不保存标注图")
    ap.add_argument("--no-unlock", action="store_true", help="跳过开局看广告解锁")
    ap.add_argument("--max-unlock", type=int, default=4, help="最多解锁次数")
    ap.add_argument("--unlock-threshold", type=float, default=0.85)
    ap.add_argument("--ad-wait", type=int, default=12, help="看广告等待秒数")
    ap.add_argument("--ad-timeout", type=int, default=30, help="广告返回超时秒数")
    ap.add_argument("--settle", type=float, default=1.0, help="解锁后稳定等待秒数")
    ap.add_argument("--notify", dest="notify", action="store_true", default=True,
                    help="结束时发送手机状态栏通知（默认开启）")
    ap.add_argument("--no-notify", dest="notify", action="store_false",
                    help="结束时不发送通知")
    ap.add_argument("--notify-message", default="auto",
                    help="自定义通知内容，auto=自动生成")
    ap.add_argument("--notify-script", default=NOTIFY_SCRIPT,
                    help="手机上 AutoJS6 通知脚本路径")
    args = ap.parse_args()

    # 连续无法决策的等待上限。任何一次点击（含关弹窗）都视为有进展，计时清零。
    idle_since = None

    def reset_idle():
        nonlocal idle_since
        idle_since = None

    def wait_idle(reason, detail=""):
        """等待一轮；超过 --idle-timeout 就返回 False 让主循环停止。"""
        nonlocal idle_since, stop_reason
        now = time.monotonic()
        if idle_since is None:
            idle_since = now
        waited = now - idle_since
        limit = max(0.0, args.idle_timeout)
        if limit > 0 and waited >= limit:
            stop_reason = "等待超时：" + reason
            log("连续%s达 %.1fs（上限 %.0fs），停止。%s" %
                (reason, waited, limit, detail))
            return False
        shown = ("%.1fs/%.0fs" % (waited, limit)) if limit > 0 else ("%.1fs/不限" % waited)
        log("%s，等待…（%s）%s" % (reason, shown, detail))
        time.sleep(args.interval)
        return True

    serial = args.device
    if not serial:
        out = subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if line.strip().endswith("\tdevice"):
                serial = line.split()[0]
                break
    if serial:
        log("使用设备 %s" % serial)
    else:
        log("未找到 adb 设备，请检查连接")

    start = time.time()
    unlocked = 0
    if not args.dry_run and not args.no_unlock:
        unlocked = unlock_all(serial, args)
        log("解锁完成，共 %d 次" % unlocked)

    clicks = 0
    no_queue_rounds = 0
    stop_reason = ""
    # 颜色 -> 点击时刻。蚂蚁把块搬进槽位有动画延迟，期间槽位看起来还是空的，
    # 若只看槽位就会重复投同色。确认入槽或超过 --repeat-delay 后移除。
    pending = {}

    try:
        while True:
            img = grab(serial)
            info = analyze(img)

            # 0) 复活弹窗最高优先级
            revive = info.get("revive", {})
            if revive.get("found"):
                stop_reason = "检测到复活弹窗，立即停手"
                log("检测到复活弹窗(score=%.2f)，立即停止。" % revive["score"])
                break

            # 1) 福利弹窗：只点 X
            popup = info.get("popup", {})
            if popup.get("found"):
                log("检测到福利弹窗(score=%.2f)，点击关闭 (%d,%d)" %
                    (popup["score"], popup["x"], popup["y"]))
                if not args.dry_run:
                    tap(serial, popup["x"], popup["y"])
                reset_idle()
                time.sleep(0.5)
                continue

            # 2) 标注图
            if not args.no_annotate:
                os.makedirs(os.path.dirname(ANNOTATED), exist_ok=True)
                cv2.imwrite(ANNOTATED, annotate(img, info))

            slots = info.get("slots", [])
            queue = info.get("queue", [])
            empty = [s for s in slots if not s["occupied"]]

            if not slots or not queue:
                no_queue_rounds += 1
                if no_queue_rounds >= 5:
                    stop_reason = "连续5轮无候选块/槽位，可能关卡结束"
                    log("连续 5 轮没有候选块/槽位，可能关卡结束，停止。")
                    break
                if not wait_idle("未识别到槽位或第一排候选块"):
                    break
                continue
            no_queue_rounds = 0

            if not empty:
                detail = "占用=%s" % [s["color"] for s in slots if s["occupied"]]
                if not wait_idle("槽位已满，等待蚂蚁搬运", detail):
                    break
                continue

            occupied_colors = {}
            for s in slots:
                if s["occupied"] and s["color"]:
                    occupied_colors[s["color"]] = occupied_colors.get(s["color"], 0) + 1

            # 清掉已确认入槽或冷却超时的颜色，其余并入“禁止再点”集合
            # 最短保护期：入槽动画期间槽位识别可能短暂失败（该帧 occupied_colors
            # 里没有该颜色）。若一看到在槽里就立刻解除 pending，下一帧就可能
            # 重复投同色——曾因此连投 3 个 peach。故至少等 MIN_PENDING 秒。
            now_mono = time.monotonic()
            for c, t in list(pending.items()):
                age = now_mono - t
                if age >= args.repeat_delay or (age >= MIN_PENDING and
                                                c in occupied_colors):
                    del pending[c]
            blocked = dict(occupied_colors)
            for c in pending:
                blocked[c] = blocked.get(c, 0) + 1

            limit = args.batch_size if args.batch_size > 0 else len(empty)
            limit = min(limit, len(empty))
            batch = choose_queue(info, blocked, limit)
            if not batch:
                if not wait_idle("候选块颜色已在槽中或等待入槽",
                                 "占用=%s 待入槽=%s 候选=%s" %
                                 (occupied_colors, list(pending),
                                  [b["color"] for b in queue])):
                    break
                continue

            reset_idle()
            names = ",".join(CN.get(b["color"], b["color"]) for b in batch)
            log("槽位空 %d 个；占用=%s；待入槽=%s；本批 %d 个 [%s]" %
                (len(empty), occupied_colors, list(pending), len(batch), names))

            stop = False
            for b in batch:
                log("  点击 %s (%d,%d)" %
                    (CN.get(b["color"], b["color"]), b["x"], b["y"]))
                if not args.dry_run:
                    tap(serial, b["x"], b["y"])
                pending[b["color"]] = time.monotonic()
                clicks += 1
                if args.max_clicks and clicks >= args.max_clicks:
                    stop_reason = "达到 --max-clicks=%d" % args.max_clicks
                    log("达到 --max-clicks=%d，停止。" % args.max_clicks)
                    stop = True
                    break
                time.sleep(0.35 if not args.dry_run else args.interval)
            if stop:
                break
            time.sleep(0.8 if not args.dry_run else 0)
    except KeyboardInterrupt:
        stop_reason = "用户手动中断"
        log("用户中断，已停止。")

    # 结束通知：和其他工具一致，默认发到手机状态栏。
    message = ("%s；" % stop_reason if stop_reason else "") + \
              "解锁 %d 次，点击 %d 次，耗时 %.0fs" % (
                  unlocked, clicks, time.time() - start)
    print("done: " + message, flush=True)
    if args.notify and not args.dry_run:
        notify_phone(args.notify_message if args.notify_message != "auto" else message,
                     serial, args.notify_script)


if __name__ == "__main__":
    main()
