#!/usr/bin/env python3
"""色块入槽自动点击。

流程：开局看广告解锁全部「解锁」位 -> 循环 {抓图 -> 复活弹窗/胜利界面最高优先级停手
-> 等稳定 -> 识别第一排色块与槽位颜色 -> 选一批颜色不在槽位、彼此不重复的第一排块
-> 按顺序点完这一轮（原坐标，不做响应判断/坐标屏蔽/列偏移预测）
-> 等稳定 -> 重新抓图进入下一轮决策}。

色块「点不动」是游戏内色块互相捆绑导致的正常现象，当前版本不处理该机制：
既不因无响应停止，也不屏蔽坐标，更不预测点掉一块后其余块的左移。

用法（统一入口见 quick.sh）：
  tools/slots/quick.sh --dry-run
  tools/slots/quick.sh --no-unlock --no-notify --max-clicks 5
"""
import argparse
import os
import random
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
import slots_vision as sv
from common.adb import dump_ui, find_text_node, key_back, tap
from common.notify import add_notify_args, send_notify

RETURN_TEXTS = ("立即返回", "返回游戏")
SECURITY_TEXTS = ("安全验证", "京东验证")
DISMISS_TEXTS = ("不了", "关闭", "下次再说", "跳过", "我知道了")

TOOL_NAME = "色块入槽"


class TerminalState(Exception):
    """命中即停的终止状态（复活弹窗 / 胜利界面）：不做任何操作。"""


def guard_terminal(img, threshold):
    """任一终止状态命中即抛异常；调用方捕获后停止任务。"""
    if sv.detect_victory_dialog(img, threshold=threshold):
        raise TerminalState("检测到胜利（挑战成功），立即结束（未做任何操作）")
    if sv.detect_revive_dialog(img, threshold=threshold):
        raise TerminalState("检测到复活弹窗，立即结束（未做任何操作）")


def has_security_check(serial=None):
    return find_text_node(dump_ui(serial), SECURITY_TEXTS) is not None


def wait_for_user(serial, timeout, args):
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(2)
        if has_security_check(serial):
            continue
        img = sv.grab(serial)
        if find_text_node(dump_ui(serial), RETURN_TEXTS):
            continue
        if img is not None and float(img.mean()) > 20:
            guard_terminal(img, args.revive_threshold)
            return True
    return False


def in_game(img, threshold):
    """回到对局的判据：第一排能识别到色块。"""
    return img is not None and len(sv.detect_first_row(img)) > 0


def watch_ad_return(serial, args):
    time.sleep(args.ad_wait)
    start = time.time()
    while time.time() - start < max(0, args.ad_timeout - args.ad_wait):
        found = find_text_node(dump_ui(serial), RETURN_TEXTS)
        if found:
            pos, _ = found
            tap(pos[0], pos[1], serial, touch=True)
            time.sleep(1.5)
        img = sv.grab(serial)
        if img is not None and float(img.mean()) > 20:
            guard_terminal(img, args.revive_threshold)
            if in_game(img, args.revive_threshold):
                return True
        time.sleep(1)
    key_back(serial)
    return False


def dismiss_popup(serial):
    found = find_text_node(dump_ui(serial), DISMISS_TEXTS)
    if found:
        pos, _ = found
        tap(pos[0], pos[1], serial, touch=True)
        time.sleep(0.6)
        return True
    return False


def wait_stable(serial, min_wait=0.6, max_wait=6.0, interval=0.2):
    time.sleep(min_wait)
    prev = None
    start = time.time()
    img = None
    while time.time() - start < max_wait:
        img = sv.grab(serial)
        if img is None:
            time.sleep(interval)
            continue
        small = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (270, 600))
        if prev is not None and np.mean(cv2.absdiff(small, prev)) / 255.0 < 0.012:
            break
        prev = small
        time.sleep(interval)
    return img if img is not None else sv.grab(serial)



def unlock_all(serial, args):
    """开局看广告解锁全部「解锁」位，返回解锁次数。"""
    unlocked = 0
    no_progress = 0
    for _ in range(args.max_unlock + 2):
        if has_security_check(serial):
            print("暂停: 安全验证，请手动完成 ...", flush=True)
            if not wait_for_user(serial, args.security_timeout, args):
                break
        img = sv.grab(serial)
        if img is None or float(img.mean()) < 15:
            time.sleep(1)
            continue
        guard_terminal(img, args.revive_threshold)
        pts = sv.detect_unlock_buttons(img, threshold=args.unlock_threshold)
        if not pts:
            print("开局解锁: 未发现解锁位，完成（共解锁 %d）" % unlocked, flush=True)
            break
        x, y = pts[0]
        print("开局解锁 %d: 点 (%d,%d) 看广告 ..." % (unlocked + 1, x, y), flush=True)
        tap(x, y, serial)
        ok = watch_ad_return(serial, args)
        unlocked += 1
        print("  解锁: " + ("成功返回对局" if ok else "未确认回到对局"), flush=True)
        time.sleep(args.settle)
        after = sv.grab(serial)
        if after is not None:
            guard_terminal(after, args.revive_threshold)
            if len(sv.detect_unlock_buttons(after, threshold=args.unlock_threshold)) >= len(pts):
                no_progress += 1
                if no_progress >= 2:
                    print("解锁无进展，停止解锁继续游戏", flush=True)
                    break
            else:
                no_progress = 0
    return unlocked


def pick_batch(result, args):
    """一次决策选一批色块：颜色不在槽位中、彼此不重复、按第一排从左到右。

    只负责挑不重复的颜色，不预测补位/左移，也不记录点过哪些坐标——
    色块捆绑导致的「点不动」暂不处理，下一轮重新抓图再决策。
    """
    row = result["first_row"]
    if not row:
        return [], "none"
    slot_colors = set(result["slot_colors"])
    fresh, seen = [], set()
    for b in row:
        if b["color"] in slot_colors or b["color"] in seen:
            continue
        seen.add(b["color"])
        fresh.append(b)
    print("  候选: 第一排=%s 槽位=%s" % (
        "/".join(sv.CN.get(b["color"], b["color"]) for b in row),
        "/".join(sv.CN.get(c, c) for c in sorted(slot_colors)) or "空"), flush=True)
    if not fresh:
        print("  第一排颜色均已占用，随机点击一个", flush=True)
        return [random.choice(row)], "random"
    limit = len(fresh) if args.batch_size <= 0 else max(1, args.batch_size)
    batch = fresh[:limit]
    print("  本轮点击: %s" % "/".join(
        sv.CN.get(b["color"], b["color"]) for b in batch), flush=True)
    return batch, ("batch" if len(batch) > 1 else "match")


def auto_run(args):
    serial = args.device
    random.seed()
    start = time.time()
    clicks = 0
    unlocked = 0
    stop_reason = ""

    if args.dry_run:
        print("[dry] 跳过实际解锁与点击，只演示第一步决策", flush=True)
    elif not args.no_unlock:
        try:
            unlocked = unlock_all(serial, args)
            print("解锁完成，共 %d 次" % unlocked, flush=True)
            time.sleep(args.settle)
        except TerminalState as e:
            stop_reason = str(e)
            print(stop_reason, flush=True)

    no_view = 0
    ui_counter = 0
    while (not stop_reason and clicks < args.max_clicks
           and time.time() - start < args.max_seconds):
        img = sv.grab(serial)
        if img is None or float(img.mean()) < 15:
            if has_security_check(serial):
                print("暂停: 安全验证，请手动完成 ...", flush=True)
                try:
                    ok = wait_for_user(serial, args.security_timeout, args)
                except TerminalState as e:
                    stop_reason = str(e)
                    break
                if not ok:
                    stop_reason = "安全验证等待超时"
                    break
                continue
            if find_text_node(dump_ui(serial), RETURN_TEXTS):
                print("广告页：等待返回 ...", flush=True)
                try:
                    watch_ad_return(serial, args)
                except TerminalState as e:
                    stop_reason = str(e)
                    break
                continue
            print("画面全黑/抓图失败，等待 ...", flush=True)
            time.sleep(1)
            continue

        # 最高优先级：复活弹窗 -> 立即结束，不做任何操作
        try:
            guard_terminal(img, args.revive_threshold)
        except TerminalState as e:
            stop_reason = str(e)
            print(stop_reason, flush=True)
            break

        ui_counter += 1
        if ui_counter % args.ui_check_every == 0:
            if has_security_check(serial):
                print("暂停: 安全验证，请手动完成 ...", flush=True)
                try:
                    ok = wait_for_user(serial, args.security_timeout, args)
                except TerminalState as e:
                    stop_reason = str(e)
                    break
                if not ok:
                    stop_reason = "安全验证等待超时"
                    break
                continue
            if find_text_node(dump_ui(serial), RETURN_TEXTS):
                print("广告页：等待返回 ...", flush=True)
                try:
                    watch_ad_return(serial, args)
                except TerminalState as e:
                    stop_reason = str(e)
                    break
                continue
            if in_game(img, args.revive_threshold) and dismiss_popup(serial):
                print("已关闭其它弹窗", flush=True)
                continue

        stable = wait_stable(serial, args.wait, args.max_wait)
        if stable is None:
            time.sleep(0.5)
            continue
        try:
            guard_terminal(stable, args.revive_threshold)
        except TerminalState as e:
            stop_reason = str(e)
            print(stop_reason, flush=True)
            break

        result = sv.analyze(stable)
        if not result["first_row"]:
            no_view += 1
            print("未识别到第一排（连续 %d/%d）" % (no_view, args.max_no_view), flush=True)
            if no_view >= args.max_no_view:
                stop_reason = "连续未识别到第一排色块，可能已通关或界面异常"
                break
            time.sleep(1)
            continue
        no_view = 0

        batch, mode = pick_batch(result, args)
        print("状态: 槽位=%s 第一排=%d 模式=%s 本轮=%d" % (
            "/".join(sv.CN.get(c, c) for c in result["slot_colors"]) or "空",
            len(result["first_row"]), mode, len(batch)), flush=True)

        if args.dry_run:
            out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), "outputs", "slots_dryrun.png")
            cv2.imwrite(out, sv.annotate(stable, result, batch))
            print("[dry] 标注图: " + out, flush=True)
            break

        # 按顺序点完这一轮：用决策时的原坐标，不预测补位左移、不判断是否有响应。
        # 色块捆绑导致点不动属正常现象，点完一轮后重新抓图再做下一次决策。
        for i, b in enumerate(batch):
            print("  点击 %d: %s (%d,%d)" % (
                i + 1, sv.CN.get(b["color"], b["color"]), b["x"], b["y"]), flush=True)
            tap(b["x"], b["y"], serial)
            clicks += 1
            time.sleep(args.batch_gap)

        after_img = wait_stable(serial, args.wait, args.max_wait)
        if after_img is not None:
            try:
                guard_terminal(after_img, args.revive_threshold)
            except TerminalState as e:
                stop_reason = str(e)
                print(stop_reason, flush=True)
                break
        time.sleep(args.gap)

    message = ("%s；" % stop_reason if stop_reason else "") + \
              "解锁 %d 次，点击 %d 次，耗时 %.0fs" % (unlocked, clicks, time.time() - start)
    print("done: " + message, flush=True)
    if args.notify and not args.dry_run:
        send_notify(message, args, TOOL_NAME, tool_slug="slots")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--dry-run", action="store_true", help="只演示第一步不点击")
    ap.add_argument("--no-unlock", action="store_true", help="跳过开局解锁")
    ap.add_argument("--max-unlock", type=int, default=4)
    ap.add_argument("--unlock-threshold", type=float, default=0.85)
    ap.add_argument("--revive-threshold", type=float, default=0.80)
    ap.add_argument("--max-clicks", type=int, default=200)
    ap.add_argument("--max-seconds", type=int, default=600)
    ap.add_argument("--batch-size", type=int, default=3,
                    help="单次决策点几个不同色块，按第一排从左到右（默认 3；0=全部）")
    ap.add_argument("--batch-gap", type=float, default=0.45,
                    help="批内两次点击间隔秒数（默认 0.45）")
    ap.add_argument("--wait", type=float, default=0.6)
    ap.add_argument("--max-wait", type=float, default=6.0)
    ap.add_argument("--gap", type=float, default=0.2)
    ap.add_argument("--settle", type=float, default=1.0)
    ap.add_argument("--ad-wait", type=int, default=12, help="看广告等待秒数")
    ap.add_argument("--ad-timeout", type=int, default=45, help="等回到对局超时秒数")
    ap.add_argument("--security-timeout", type=int, default=300)
    ap.add_argument("--ui-check-every", type=int, default=5)
    ap.add_argument("--max-no-view", type=int, default=3)
    add_notify_args(ap, "slots", TOOL_NAME, default_message='auto')
    args = ap.parse_args()
    auto_run(args)


if __name__ == "__main__":
    main()
