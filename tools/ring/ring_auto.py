#!/usr/bin/env python3
"""环形岛接客自动点击。

流程：开局看广告解锁全部接驳位 -> 循环 {抓图 -> 关助力礼包弹窗 -> 识别接驳区车色
-> 一次选一批「可开出、颜色不在接驳区且互不重复」的车，按原坐标依次点击 -> 等稳定}。
接驳区已有颜色也算已占用；若全被占则随机出一辆车疏通。
规则全部来自用户确认，与停车场接客的差异：不看队首乘客、倾斜关不停手、弹窗主动关。

用法（统一入口见 quick.sh）：
  tools/ring/quick.sh --dry-run
  tools/ring/quick.sh --auto --batch-size 3 --batch-gap 0.35
"""
import argparse
import json
import os
import random
import sys
import time
from collections import Counter

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
import ring_vision as rv
from common.adb import dump_ui, find_text_node, key_back, tap
from common.notify import add_notify_args, send_notify

RETURN_TEXTS = ("立即返回", "返回游戏")
SECURITY_TEXTS = ("安全验证", "京东验证")
DISMISS_TEXTS = ("不了", "关闭", "下次再说", "跳过", "我知道了")

TOOL_NAME = "环形岛接客"

CN = {"red": "红", "brown": "深红", "yellow": "黄", "green": "绿",
      "cyan": "青", "blue": "蓝", "pink": "粉", "unknown": "障碍"}


def car_tap_point(car):
    if "tap" in car:
        return car["tap"]
    bx, by = int(car["bx"]), int(car["by"])
    bw, bh = int(car["bw"]), int(car["bh"])
    cx, cy = bx + bw // 2, by + bh // 2
    vec = car.get("vec")
    if vec:
        ux, uy = float(vec[0]), float(vec[1])
        off = max(10, min(bw, bh) // 5)
        return int(cx - ux*off), int(cy - uy*off)
    return cx, by + max(10, bh // 3)


def has_security_check(serial=None):
    return find_text_node(dump_ui(serial), SECURITY_TEXTS) is not None


def wait_for_user(serial, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(2)
        if has_security_check(serial):
            continue
        img = rv.grab(serial)
        if find_text_node(dump_ui(serial), RETURN_TEXTS):
            continue
        if img is not None and float(img.mean()) > 30:
            if rv.detect_gift_popup(img) is None:
                return True
    return False


def watch_ad_return(serial, wait, timeout):
    time.sleep(wait)
    start = time.time()
    while time.time() - start < max(0, timeout - wait):
        found = find_text_node(dump_ui(serial), RETURN_TEXTS)
        if found:
            pos, _ = found
            tap(pos[0], pos[1], serial, touch=True)
            time.sleep(1.5)
        img = rv.grab(serial)
        if img is not None and float(img.mean()) > 20:
            r = rv.analyze(img)
            if r["cars"]:
                return True
        time.sleep(1)
    key_back(serial)
    return False


def dismiss_gift_popup(img, serial, args):
    """关闭「助力礼包」弹窗。返回 (是否关闭, 新截图)。"""
    pos = rv.detect_gift_popup(img)
    if pos is None:
        return False, img
    print("检测到助力礼包弹窗，点 × (%d,%d)" % pos, flush=True)
    if not args.dry_run:
        tap(pos[0], pos[1], serial, touch=True)
        time.sleep(0.8)
    return True, wait_stable(serial, 0.2, 1.0, 0.15)


def dismiss_popup(serial):
    found = find_text_node(dump_ui(serial), DISMISS_TEXTS)
    if found:
        pos, _ = found
        tap(pos[0], pos[1], serial, touch=True)
        time.sleep(0.6)
        return True
    return False


def wait_stable(serial, min_wait=0.35, max_wait=1.6, interval=0.15):
    time.sleep(min_wait)
    prev = None
    start = time.time()
    img = None
    while time.time() - start < max_wait:
        img = rv.grab(serial)
        if img is None:
            time.sleep(interval); continue
        small = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (270, 600))
        if prev is not None and np.mean(cv2.absdiff(small, prev)) / 255.0 < 0.012:
            break
        prev = small
        time.sleep(interval)
    return img if img is not None else rv.grab(serial)



def unlock_all_docks(serial, args):
    """开局看广告解锁全部接驳位。返回解锁次数。"""
    unlocked = 0
    no_unlock_streak = 0
    for _ in range(args.max_unlock + 2):
        if has_security_check(serial):
            print("暂停: 安全验证，请手动完成 ...", flush=True)
            if not wait_for_user(serial, args.security_timeout):
                break
        img = rv.grab(serial)
        if img is None:
            time.sleep(1); continue
        # 若有助力礼包弹窗，先关
        if rv.detect_gift_popup(img) is not None:
            dismiss_gift_popup(img, serial, args)
            time.sleep(args.settle)
            continue
        slots = rv.detect_unlock_slots(img, threshold=args.unlock_threshold)
        if not slots:
            print("开局解锁: 未发现解锁位，完成（共解锁 %d）" % unlocked, flush=True)
            break
        x, y = slots[0]
        print("开局解锁 %d: 点 (%d,%d) 看广告 ..." % (unlocked+1, x, y), flush=True)
        if args.dry_run:
            print("[dry] 仅演示解锁 (%d,%d)" % (x, y), flush=True)
            return unlocked + 1
        tap(x, y, serial)
        time.sleep(1.2)
        # 关键：点解锁位后会弹「解锁一个车位」确认框，必须先点底部蓝色「使用」
        # 按钮才会真正跳广告。漏掉这步会误判为「解锁成功」但车位没变。
        confirm_img = rv.grab(serial)
        use_pos = rv.detect_unlock_confirm(confirm_img)
        if use_pos:
            print("  确认框「使用」按钮 (%d,%d)，点击开始广告 ..." % use_pos, flush=True)
            if not args.dry_run:
                tap(use_pos[0], use_pos[1], serial, touch=True)
                time.sleep(1.2)
        else:
            print("  未发现解锁确认框（可能无需确认），直接进入广告等待", flush=True)
        ok = watch_ad_return(serial, args.ad_wait, args.ad_timeout)
        unlocked += 1
        print("  解锁: " + ("成功" if ok else "未回到对局"), flush=True)
        time.sleep(args.settle)
        if not ok:
            no_unlock_streak += 1
            if no_unlock_streak >= 2:
                break
    return unlocked


def batch_limit(result, args, expected):
    """单批点击上限：用户配置 + 空接驳位安全余量双重约束。"""
    limit = expected if args.batch_size <= 0 else max(1, args.batch_size)
    n_empty = len(result.get("empty_slots", []))
    reserve = max(0, args.min_empty_slots)
    # 检测不到空位时也至少保留单次点击能力，避免完全停手。
    return max(1, min(limit, max(1, n_empty - reserve)))


def pick_batch(result, args, is_blocked=None):
    """一次识别选一批车：可开出、颜色不在接驳区、批内颜色互不重复。

    接驳区已有色视为已占用，且同一颜色最多选一辆；按「离接驳区近、方向朝上」
    排序。若没有可用颜色，退化为随机出一辆车疏通（与旧规则一致）。

    返回 (batch, mode)。mode: batch / match / random / none。
    """
    exitable = [c for c in result.get("cars", []) if c.get("can_exit")]
    if not exitable:
        return [], "none"
    blocked = is_blocked or (lambda c: False)
    # 灰障碍永远不可开出；近期点过/点过无响应的车本轮跳过。
    usable = [c for c in exitable if c.get("color") != "unknown" and not blocked(c)]
    if not usable:
        return [], "none"
    dock_colors = set(result.get("dock", {}).get("colors", []))
    fresh = [c for c in usable if c["color"] not in dock_colors]
    fresh.sort(key=lambda c: (c["y"], rv.DIR_PRIORITY.get(c.get("dir"), 5)))

    picked, used_colors = [], set(dock_colors)
    limit = batch_limit(result, args, len(fresh))
    for c in fresh:
        if len(picked) >= limit:
            break
        if c["color"] in used_colors:
            continue
        used_colors.add(c["color"])
        picked.append(c)
    if picked:
        return picked, ("batch" if len(picked) > 1 else "match")

    # 接驳区颜色全占用时随机出车，让局面流动（只出一辆，避免把接驳区占死）。
    pool = sorted(usable, key=lambda c: (c["y"], rv.DIR_PRIORITY.get(c.get("dir"), 5)))
    print("接驳区颜色已占满 (%s)，随机出车疏通" % "/".join(sorted(dock_colors)), flush=True)
    return [random.choice(pool)], "random"


def low_slot_stop(result, min_empty=1):
    """用户定稿：只剩 <=min_empty 个空接驳位，且无「颜色不在接驳区」的可开出车时结束。

    这样避免在最后 1 个空位还随机出车、把接驳区占死导致挑战失败。
    返回 (should_stop, info)。
    """
    cars = result.get("cars", [])
    n_empty = len(result.get("empty_slots", []))
    dock_set = set(result.get("dock", {}).get("colors", []))
    fresh = [c for c in cars
             if c.get("can_exit") and c.get("color") != "unknown"
             and c.get("color") not in dock_set]
    should = (n_empty <= min_empty) and not fresh
    return should, {"n_empty": n_empty, "dock": sorted(dock_set),
                    "fresh": len(fresh), "cars": len(cars)}


def auto_run(args):
    serial = args.device
    random.seed()
    start = time.time()
    clicks = 0
    stop_reason = ""

    # 开局解锁全部接驳位（用户强调不能漏）
    unlocked = 0
    if not args.no_unlock:
        unlocked = unlock_all_docks(serial, args)
        print("接驳位解锁完成，共 %d 个" % unlocked, flush=True)
        time.sleep(args.settle)

    no_effect_streak = 0
    low_slot_streak = 0
    ui_check_counter = 0
    recent_clicks = []
    failed_taps = []
    while (not stop_reason and clicks < args.max_clicks
           and time.time() - start < args.max_seconds):
        img = rv.grab(serial)
        if img is None or float(img.mean()) < 15:
            if has_security_check(serial):
                print("暂停: 安全验证，请手动完成 ...", flush=True)
                if not wait_for_user(serial, args.security_timeout):
                    print("安全验证等待超时，停止", flush=True)
                    break
                continue
            if find_text_node(dump_ui(serial), RETURN_TEXTS):
                print("广告页：等待返回 ...", flush=True)
                watch_ad_return(serial, args.ad_wait, args.ad_timeout)
                continue
            print("画面全黑/抓图失败，等待 ...", flush=True)
            time.sleep(1); continue

        # 最高优先级：复活弹窗 → 立即结束，不做任何操作（用户定稿）
        if rv.detect_revive_dialog(img):
            stop_reason = "检测到复活弹窗，立即结束（未做任何操作）"
            print(stop_reason, flush=True)
            break

        # 每轮优先关助力礼包弹窗（用户明确要求）
        closed, img = dismiss_gift_popup(img, serial, args)
        if closed:
            if args.dry_run:
                print("[dry] 关弹窗后演示结束", flush=True)
                break
            continue

        # 结算弹窗（挑战失败/成功）：立即停止，避免对着弹窗空点
        if rv.detect_end_dialog(img):
            stop_reason = "检测到结算弹窗（挑战失败/成功），已停止"
            print(stop_reason, flush=True)
            break

        # 周期性检查广告/验证/其它弹窗
        ui_check_counter += 1
        if ui_check_counter % args.ui_check_every == 0:
            if has_security_check(serial):
                print("暂停: 安全验证，请手动完成 ...", flush=True)
                if not wait_for_user(serial, args.security_timeout):
                    print("安全验证等待超时，停止", flush=True)
                    break
                ui_check_counter = 0
                continue
            if find_text_node(dump_ui(serial), RETURN_TEXTS):
                print("广告页：等待返回 ...", flush=True)
                watch_ad_return(serial, args.ad_wait, args.ad_timeout)
                ui_check_counter = 0
                continue
            if dismiss_popup(serial):
                print("已关闭其它弹窗", flush=True)
                ui_check_counter = 0
                continue

        result = rv.analyze(img)
        if not result["cars"]:
            print("未识别到棋盘，等待 1s 重试", flush=True)
            time.sleep(1); continue

        # 用户定稿：只剩 <=1 个空接驳位且无其它颜色车可出 -> 提前结束
        should_stop, info = low_slot_stop(result, args.min_empty_slots)
        if should_stop:
            low_slot_streak += 1
            print("仅剩 %d 空位且无其它颜色车可出（连续 %d/%d），接驳区=%s" % (
                info["n_empty"], low_slot_streak, args.slot_confirm,
                "/".join(CN.get(c, c) for c in info["dock"]) or "空"), flush=True)
            if low_slot_streak >= args.slot_confirm:
                stop_reason = ("仅剩 %d 个空接驳位且无其它颜色车可出，已停止" %
                               info["n_empty"])
                print(stop_reason, flush=True)
                break
        else:
            low_slot_streak = 0

        now = time.time()
        recent_clicks = [(x, y, t) for x, y, t in recent_clicks if now - t < args.recent_seconds]
        failed_taps = [(x, y, t) for x, y, t in failed_taps if now - t < args.failed_seconds]

        def is_blocked(c):
            return any((c["x"]-x)**2 + (c["y"]-y)**2 < 45**2
                       for x, y, _ in recent_clicks + failed_taps)

        batch, mode = pick_batch(result, args, is_blocked)
        if not batch:
            usable_any = [c for c in result["cars"]
                          if c.get("can_exit") and c.get("color") != "unknown"]
            if usable_any:
                print("所有可开车均无响应，重置失败记录重试", flush=True)
                failed_taps.clear()
                batch, mode = pick_batch(result, args)

        dock_colors = result["dock"]["colors"]
        picked_colors = "/".join(CN.get(c["color"], c["color"]) for c in batch) or "无"
        print("状态: 接驳区=%s 车=%d 可开出=%d 模式=%s 本批%d辆 [%s]" % (
            "/".join(CN.get(c, c) for c in dock_colors) or "空",
            len(result["cars"]),
            sum(1 for c in result["cars"] if c["can_exit"]),
            mode, len(batch), picked_colors), flush=True)

        if not batch:
            print("无可开出的车，停止", flush=True)
            break
        batch = batch[:max(0, args.max_clicks - clicks)]
        if not batch:
            break
        if args.dry_run:
            for i, cand in enumerate(batch, 1):
                print("[dry] %d/%d %s @(%d,%d) 方向=%s 模式=%s" % (
                    i, len(batch), CN.get(cand["color"], cand["color"]),
                    cand["x"], cand["y"], cand.get("dir", "?"), mode), flush=True)
            out = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), "outputs", "ring_dryrun.png")
            cv2.imwrite(out, rv.annotate(img, result, batch))
            print("[dry] 标注图: " + out, flush=True)
            break

        before_counts = Counter(c["color"] for c in result["cars"])
        before_dock = set(dock_colors)
        for i, cand in enumerate(batch):
            tx, ty = car_tap_point(cand)
            print("  点击 %d/%d: %s @(%d,%d) 方向=%s 模式=%s" % (
                i + 1, len(batch), CN.get(cand["color"], cand["color"]),
                tx, ty, cand.get("dir", "?"), mode), flush=True)
            tap(tx, ty, serial)
            clicks += 1
            recent_clicks.append((cand["x"], cand["y"], time.time()))
            if i < len(batch) - 1:
                time.sleep(args.batch_gap)

        after_img = wait_stable(serial, args.wait, args.max_wait)
        if after_img is not None and (rv.detect_revive_dialog(after_img) or
                                      rv.detect_end_dialog(after_img)):
            stop_reason = "批次后检测到复活/结算弹窗，已停止"
            print(stop_reason, flush=True)
            break

        failed_batch = []
        moved = False
        if after_img is not None:
            after = rv.analyze(after_img)
            after_counts = Counter(c["color"] for c in after["cars"])
            after_dock = set(after["dock"]["colors"])
            for cand in batch:
                color = cand["color"]
                ok = ((color in after_dock and color not in before_dock) or
                      after_counts.get(color, 0) < before_counts.get(color, 0))
                if ok:
                    moved = True
                else:
                    failed_batch.append(cand)
        else:
            failed_batch = list(batch)

        for cand in failed_batch:
            failed_taps.append((cand["x"], cand["y"], time.time()))
        if moved:
            no_effect_streak = 0
            if failed_batch:
                print("  其中 %d 辆未生效，记入失败列表" % len(failed_batch), flush=True)
        else:
            no_effect_streak += len(batch)
            print("  本批 %d 次点击均无响应（连续 %d 次）" % (
                len(batch), no_effect_streak), flush=True)
            if no_effect_streak >= args.max_no_effect:
                print("连续 %d 次点击无响应，停止" % no_effect_streak, flush=True)
                break
        time.sleep(args.gap)

    message = ("%s；" % stop_reason if stop_reason else "") + \
              "解锁 %d 位，点击 %d 次，耗时 %.0fs" % (unlocked, clicks, time.time() - start)
    print("done: " + message, flush=True)
    if args.notify and not args.dry_run:
        send_notify(message, args, TOOL_NAME, tool_slug="ring")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--dry-run", action="store_true", help="只演示第一步不点击")
    ap.add_argument("--no-unlock", action="store_true", help="跳过开局解锁接驳位")
    ap.add_argument("--max-unlock", type=int, default=6)
    # 改为匹配「看广告」播放图标后峰值 0.98+，空槽位仅 ~0.16，0.8 足够稳
    ap.add_argument("--unlock-threshold", type=float, default=0.8)
    ap.add_argument("--max-clicks", type=int, default=200)
    ap.add_argument("--batch-size", type=int, default=3,
                    help="一次识别最多点几个不重色且不在接驳区的车（默认 3；0=按空位不限）")
    ap.add_argument("--batch-gap", type=float, default=0.35,
                    help="批内相邻两次点击的间隔秒数（默认 0.35）")
    ap.add_argument("--max-seconds", type=int, default=900)
    ap.add_argument("--wait", type=float, default=0.35)
    ap.add_argument("--max-wait", type=float, default=1.6)
    ap.add_argument("--gap", type=float, default=0.15)
    ap.add_argument("--settle", type=float, default=1.2)
    ap.add_argument("--ad-wait", type=int, default=15, help="看广告等待秒数")
    ap.add_argument("--ad-timeout", type=int, default=40, help="等回到对局超时秒数")
    ap.add_argument("--security-timeout", type=int, default=300)
    ap.add_argument("--ui-check-every", type=int, default=5)
    ap.add_argument("--recent-seconds", type=float, default=4.0)
    ap.add_argument("--max-no-effect", type=int, default=6)
    ap.add_argument("--failed-seconds", type=float, default=25.0)
    ap.add_argument("--min-empty-slots", type=int, default=1,
                    help="保留的空接驳位数：空位<=此值且无新色车可出时结束，并限制单批点击数（默认 1）")
    ap.add_argument("--slot-confirm", type=int, default=2,
                    help="提前结束条件连续确认帧数，防抖动（默认 2）")
    add_notify_args(ap, "ring", TOOL_NAME, default_message='auto')
    args = ap.parse_args()
    auto_run(args)


if __name__ == "__main__":
    main()
