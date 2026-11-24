#!/usr/bin/env python3
"""沙画收集自动点击。

流程：开局反复点「+」→ 免费使用 → 看广告返回，直到加号消失
→ 循环 {抓图 → 复活/通关弹窗最高优先级停手 → 等稳定 → 识别第一排桶与槽位颜色
→ 批量选桶（每种颜色最多一个，优先不在槽位中的颜色；同一槽色连续 N 轮则随机）
→ 依次快速点击（第一排位置固定，点一个只在原位补位，其他桶坐标不变）
→ 等稳定}。

目标是单关打通：命中复活/通关弹窗立即结束，不做任何操作。
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
import sand_vision as sv
from common.adb import dump_ui, find_text_node, key_back, tap
from common.notify import add_notify_args, send_notify

RETURN_TEXTS = ("立即返回", "返回游戏")
SECURITY_TEXTS = ("安全验证", "京东验证")

TOOL_NAME = "沙画收集"


class TerminalState(Exception):
    """命中即停的终止状态（复活弹窗 / 通关界面）：不做任何操作。"""


def guard_terminal(img, threshold):
    if sv.detect_victory_dialog(img, threshold=threshold):
        raise TerminalState("检测到通关界面，立即结束（未做任何操作）")
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


def in_game(img):
    """回到对局的判据：第一排能识别到桶，或加号仍在。"""
    if img is None:
        return False
    return len(sv.detect_first_row(img)) > 0 or len(sv.detect_plus(img)) > 0


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
            if in_game(img):
                return True
        time.sleep(1)
    key_back(serial)
    return False


def wait_stable(serial, min_wait=0.6, max_wait=6.0, interval=0.2):
    time.sleep(min_wait)
    prev, img, start = None, None, time.time()
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
    """开局反复点加号 → 免费使用 → 看广告，直到加号消失。"""
    unlocked = 0
    for _ in range(args.max_unlock):
        if has_security_check(serial):
            print("暂停: 安全验证，请手动完成 ...", flush=True)
            if not wait_for_user(serial, args.security_timeout, args):
                break
        img = sv.grab(serial)
        if img is None or float(img.mean()) < 15:
            time.sleep(1)
            continue
        guard_terminal(img, args.revive_threshold)
        plus = sv.detect_plus(img)
        if not plus:
            print("开局解锁: 加号已消失，完成（共解锁 %d）" % unlocked, flush=True)
            break
        x, y = plus[0]
        print("开局解锁 %d: 点加号 (%d,%d)" % (unlocked + 1, x, y), flush=True)
        tap(x, y, serial)
        time.sleep(args.dialog_wait)

        dlg = sv.grab(serial)
        if dlg is None:
            break
        guard_terminal(dlg, args.revive_threshold)
        # 弹窗没出来（可能点空了）→ 回到循环重新找加号
        if not sv.detect_unlock_dialog(dlg):
            print("  未出现解锁弹窗，重试", flush=True)
            time.sleep(0.6)
            continue
        btn = sv.detect_free_button(dlg)
        if not btn:
            print("  未找到「免费使用」按钮，停止解锁", flush=True)
            break
        bx, by = btn
        print("  点免费使用 (%d,%d) 看广告 ..." % (bx, by), flush=True)
        tap(bx, by, serial)
        ok = watch_ad_return(serial, args)
        unlocked += 1
        print("  解锁: " + ("成功返回对局" if ok else "未确认回到对局"), flush=True)
        time.sleep(args.settle)
        after = sv.grab(serial)
        if after is not None:
            guard_terminal(after, args.revive_threshold)
    else:
        print("解锁达到上限 %d 次" % args.max_unlock, flush=True)
    return unlocked


def pick_bucket(result, streak_color, streak_count, args):
    """批量选桶：第一排每种颜色最多选一个（不重复），优先不在槽位中的颜色。

    第一排位置固定，点某个桶只在该位置补位、其他桶坐标不变，因此同一张图上
    选出的多个桶可以依次快速点击，无需每点一次重新抓图。
    槽色连续出现 N 轮则整批随机（退化为单桶），保持卡死兜底。

    返回 (桶列表, 模式, 新的streak_color, 新的streak_count)。
    """
    row = result["first_row"]
    if not row:
        return [], "none", streak_color, streak_count
    slot_colors = set(result["slot_colors"])

    # 槽位颜色连续性：只要某一槽色和上一轮相同就累加，否则重置为 1
    new_streak_color, new_streak_count = streak_color, streak_count
    if slot_colors and slot_colors == getattr(pick_bucket, "_prev_slots", set()):
        common = sorted(slot_colors)[0]
        if common == streak_color:
            new_streak_count = streak_count + 1
        else:
            new_streak_color, new_streak_count = common, 1
    elif slot_colors:
        new_streak_color, new_streak_count = sorted(slot_colors)[0], 1
    else:
        new_streak_color, new_streak_count = None, 0
    pick_bucket._prev_slots = set(slot_colors)

    print("  候选: 第一排=%s 槽位=%s 同槽色连续=%d" % (
        "/".join(sv.CN.get(b["color"], b["color"]) for b in row),
        "/".join(sv.CN.get(c, c) for c in sorted(slot_colors)) or "空",
        new_streak_count if new_streak_color else 0), flush=True)

    if new_streak_color and new_streak_count >= args.repeat_limit:
        print("  槽色连续 %d 轮为 %s，随机选择一个" % (
            new_streak_count, sv.CN.get(new_streak_color, new_streak_color)), flush=True)
        return [random.choice(row)], "random", new_streak_color, new_streak_count

    # 每种颜色只取一个，按第一排从左到右；优先槽位里没有的颜色
    def unique_colors(buckets):
        seen, out = set(), []
        for b in buckets:
            if b["color"] not in seen:
                seen.add(b["color"])
                out.append(b)
        return out

    limit = args.batch_size if args.batch_size > 0 else len(row)
    fresh = unique_colors([b for b in row if b["color"] not in slot_colors])
    if fresh:
        batch = fresh[:limit]
        print("  本轮批量点击 %d 个不重复色: %s" % (
            len(batch), "/".join(sv.CN.get(b["color"], b["color"]) for b in batch)),
            flush=True)
        return batch, "fresh", new_streak_color, new_streak_count

    # 第一排颜色都已在槽位中：随机起点后按去色顺序取一批，避免每轮都点同一个
    pool = unique_colors(row)
    if len(pool) > 1:
        random.shuffle(pool)
    batch = pool[:limit]
    print("  第一排颜色均已在槽位中，随机批量 %d 个: %s" % (
        len(batch), "/".join(sv.CN.get(b["color"], b["color"]) for b in batch)),
        flush=True)
    return batch, "random", new_streak_color, new_streak_count


def auto_run(args):
    serial = args.device
    random.seed()
    start = time.time()
    clicks, unlocked = 0, 0
    stop_reason = ""
    streak_color, streak_count = None, 0

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
                stop_reason = "连续未识别到第一排桶，可能已通关或界面异常"
                break
            time.sleep(1)
            continue
        no_view = 0

        batch, mode, streak_color, streak_count = pick_bucket(
            result, streak_color, streak_count, args)
        print("状态: 槽位=%s 第一排=%d 模式=%s" % (
            "/".join(sv.CN.get(c, c) for c in result["slot_colors"]) or "空",
            len(result["first_row"]), mode), flush=True)

        if args.dry_run:
            out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), "outputs", "sand_dryrun.png")
            cv2.imwrite(out, sv.annotate(stable, result, batch))
            print("[dry] 标注图: " + out, flush=True)
            break

        for i, b in enumerate(batch):
            # 批次内每个桶点前都检查一次终止弹窗，命中立即停手不做操作
            if i > 0:
                mid = sv.grab(serial)
                if mid is not None:
                    try:
                        guard_terminal(mid, args.revive_threshold)
                    except TerminalState as e:
                        stop_reason = str(e)
                        print(stop_reason, flush=True)
                        break
            if stop_reason:
                break
            print("  点击 %d/%d: %s (%d,%d)" % (
                i + 1, len(batch), sv.CN.get(b["color"], b["color"]),
                b["x"], b["y"]), flush=True)
            tap(b["x"], b["y"], serial)
            clicks += 1
            if i < len(batch) - 1:
                time.sleep(args.batch_gap)

        if stop_reason:
            break
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
    if not args.dry_run:
        send_notify(message, args, TOOL_NAME, tool_slug="sand")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--dry-run", action="store_true", help="只演示第一步不点击")
    ap.add_argument("--no-unlock", action="store_true", help="跳过开局解锁")
    ap.add_argument("--max-unlock", type=int, default=12, help="解锁次数上限（防死循环）")
    ap.add_argument("--repeat-limit", type=int, default=5,
                    help="同一槽色连续多少轮后随机选桶（默认 5）")
    ap.add_argument("--batch-size", type=int, default=0,
                    help="每批最多点几个不重复颜色（0=不限，取第一排全部不同色；建议 2~4）")
    ap.add_argument("--batch-gap", type=float, default=0.15,
                    help="批次内相邻两次点击的间隔秒数（默认 0.15）")
    ap.add_argument("--revive-threshold", type=float, default=0.80)
    ap.add_argument("--max-clicks", type=int, default=200)
    ap.add_argument("--max-seconds", type=int, default=600)
    ap.add_argument("--wait", type=float, default=0.6)
    ap.add_argument("--max-wait", type=float, default=6.0)
    ap.add_argument("--gap", type=float, default=0.2)
    ap.add_argument("--settle", type=float, default=1.0)
    ap.add_argument("--dialog-wait", type=float, default=1.0)
    ap.add_argument("--ad-wait", type=int, default=12, help="看广告等待秒数")
    ap.add_argument("--ad-timeout", type=int, default=45, help="等回到对局超时秒数")
    ap.add_argument("--security-timeout", type=int, default=300)
    ap.add_argument("--ui-check-every", type=int, default=5)
    ap.add_argument("--max-no-view", type=int, default=3)
    add_notify_args(ap, "sand", TOOL_NAME)
    args = ap.parse_args()
    auto_run(args)


if __name__ == "__main__":
    main()
