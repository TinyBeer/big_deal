#!/usr/bin/env python3
"""停车场接客自动点击。

流程：开局看广告解锁全部接驳位 -> 若为倾斜(8 方向)关卡则停手交还用户 ->
循环 {抓图识别 -> 按队首颜色选可开出的车 -> 点击 -> 等稳定}；无同色车时点任意
可开出车疏通（愤怒无后果）。无可开车则结束并通知。倾斜关卡可用 --allow-tilted 强制执行。

用法（统一入口见 quick.sh）：
  tools/parking/quick.sh --dry-run
  tools/parking/quick.sh --auto --max-clicks 120
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
import parking_vision as pv
from common.notify import add_notify_args, send_notify

RETURN_TEXTS = ("立即返回", "返回游戏")
SECURITY_TEXTS = ("安全验证", "京东验证")
DISMISS_TEXTS = ("不了", "关闭", "下次再说", "跳过", "我知道了")

TOOL_NAME = "停车场接客"

CN = {"red": "红", "brown": "深红", "yellow": "黄", "green": "绿",
      "cyan": "青", "blue": "蓝", "pink": "粉", "unknown": "障碍"}


def car_tap_point(car):
    """取车身实心区点击：沿行进反方向(车尾)偏移一点，避开车窗/描边。

    正交车：车尾在行进反方向；斜向车(26.6°/153.4°)同样沿反方向偏移。
    质心/轴对齐 bbox 的"偏上"在斜车上会落到车外或相邻车，故用方向向量。
    """
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


def tap(x, y, serial=None, touch=False):
    cmd = ["adb"] + (["-s", serial] if serial else []) + ["shell", "input"]
    cmd += ["touchscreen"] if touch else []
    cmd += ["tap", str(int(round(x))), str(int(round(y)))]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def key_back(serial=None):
    cmd = ["adb"] + (["-s", serial] if serial else []) + ["shell", "input", "keyevent", "4"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


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
                    return ((x1+x2)//2, (y1+y2)//2), text
    return None


def has_security_check(serial=None):
    return find_text_node(dump_ui(serial), SECURITY_TEXTS) is not None


def wait_for_user(serial, timeout):
    """等用户手动完成安全验证。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(2)
        if has_security_check(serial):
            continue
        img = pv.grab(serial)
        if find_text_node(dump_ui(serial), RETURN_TEXTS):
            continue
        if img is not None and float(img.mean()) > 30:
            return True
    return False


def watch_ad_return(serial, wait, timeout):
    """等广告播完，点「点击立即返回」回游戏。"""
    time.sleep(wait)
    start = time.time()
    while time.time() - start < max(0, timeout - wait):
        found = find_text_node(dump_ui(serial), RETURN_TEXTS)
        if found:
            pos, _ = found
            tap(pos[0], pos[1], serial, touch=True)
            time.sleep(1.5)
        img = pv.grab(serial)
        if img is not None and float(img.mean()) > 20:
            r = pv.analyze(img)
            if r["cars"]:
                return True
        time.sleep(1)
    key_back(serial)
    return False


def dismiss_popup(serial):
    """关闭道具/公告弹窗（如有）。"""
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
        img = pv.grab(serial)
        if img is None:
            time.sleep(interval); continue
        small = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (270, 600))
        if prev is not None and np.mean(cv2.absdiff(small, prev)) / 255.0 < 0.012:
            break
        prev = small
        time.sleep(interval)
    return img if img is not None else pv.grab(serial)



def unlock_all_docks(serial, args):
    """开局看广告解锁全部接驳位。返回解锁次数。"""
    unlocked = 0
    no_unlock_streak = 0
    for _ in range(args.max_unlock + 2):
        if has_security_check(serial):
            print("暂停: 安全验证，请手动完成 ...", flush=True)
            if not wait_for_user(serial, args.security_timeout):
                break
        img = pv.grab(serial)
        if img is None:
            time.sleep(1); continue
        slots = pv.detect_unlock_slots(img, threshold=args.unlock_threshold)
        if not slots:
            print("开局解锁: 未发现解锁位，完成（共解锁 %d）" % unlocked, flush=True)
            break
        x, y = slots[0]
        print("开局解锁 %d: 点 (%d,%d) 看广告 ..." % (unlocked+1, x, y), flush=True)
        if args.dry_run:
            print("[dry] 仅演示解锁 (%d,%d)" % (x, y), flush=True)
            return unlocked + 1
        tap(x, y, serial)
        time.sleep(1.0)
        ok = watch_ad_return(serial, args.ad_wait, args.ad_timeout)
        unlocked += 1
        print("  解锁: " + ("成功" if ok else "未回到对局"), flush=True)
        time.sleep(args.settle)
        if not ok:
            no_unlock_streak += 1
            if no_unlock_streak >= 2:
                break
    return unlocked


def pick_car(result, head_side):
    """选车：优先队首同色且可开出的车；否则任意可开出的车疏通。"""
    q = result["queue"]
    head = q["head"]
    cars = result["cars"]
    exitable = [c for c in cars if c["can_exit"]]
    match = [c for c in exitable if c["color"] == head]
    from parking_vision import DIR_PRIORITY
    if match:
        # 优先离顶部近(y 小)，其次方向越朝上越优先（兼容 8 方向）
        match.sort(key=lambda c: (c["y"], DIR_PRIORITY.get(c["dir"], 5)))
        return match[0], "match"
    if exitable:
        exitable.sort(key=lambda c: (c["y"], DIR_PRIORITY.get(c["dir"], 5)))
        return exitable[0], "clear"
    return None, "none"


def auto_run(args):
    serial = args.device
    start = time.time()
    clicks = 0
    stop_reason = ""

    # 开局解锁全部接驳位
    if not args.no_unlock:
        unlock_all_docks(serial, args)
        time.sleep(args.settle)

    # 倾斜（8 方向）关卡：用户确认只解锁、不自动接客，后续手动处理。
    # 判定用等距投影的标准斜轴 26.565°/153.435°，容差 8° 不会把旧正交关误判为斜关。
    if not args.allow_tilted:
        tilt_result = None
        for _ in range(3):
            check_img = wait_stable(serial, 0.2, 0.8, 0.1)
            if check_img is None or float(check_img.mean()) < 15:
                time.sleep(args.settle); continue
            tilt_result = pv.analyze(check_img, args.head_side)
            if tilt_result["cars"]:
                break
            time.sleep(args.settle)
        tilt = tilt_result.get("tilt", {}) if tilt_result else {}
        if tilt.get("tilted"):
            unlock_note = "已解锁全部接驳位" if not args.no_unlock else "本轮未执行解锁"
            stop_reason = ("检测到倾斜角度小车（斜向箭头 %d 个，轴向 %s），%s，"
                           "停止自动接客请手动处理" % (
                               tilt["count"], "/".join(str(x) for x in tilt["axes"]),
                               unlock_note))
            print(stop_reason, flush=True)
        elif not tilt_result or not tilt_result["cars"]:
            print("开局倾斜检测：未识别到棋盘，跳过检测（按原流程继续）", flush=True)
    else:
        print("已启用 --allow-tilted：倾斜关卡也会自动接客", flush=True)

    last_no_move = 0
    no_effect_streak = 0
    low_slot_streak = 0
    ui_check_counter = 0
    recent_clicks = []  # (x, y, timestamp) 短期内不重复点同一位置
    failed_taps = []    # 点过但车没动的位置，本轮内不再尝试
    while (not stop_reason and clicks < args.max_clicks
           and time.time() - start < args.max_seconds):
        img = pv.grab(serial)
        if img is None or float(img.mean()) < 15:
            # 画面异常（黑屏/广告/验证）才检查 UI
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

        # 周期性检查弹窗/验证/广告（每隔若干步，避免每步 uiautomator 拖慢速度）
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
                print("已关闭弹窗", flush=True)
                ui_check_counter = 0
                continue

        result = pv.analyze(img, args.head_side)
        if not result["cars"]:
            print("未识别到棋盘，等待 1s 重试", flush=True)
            time.sleep(1); continue

        # 接驳位只剩 <=1 个空位时停止，避免开出后无处停靠触发广告。
        # 需连续 N 帧确认，防止瞬时遮挡造成误停。
        n_empty = len(result.get("empty_slots", []))
        if n_empty <= args.min_empty_slots:
            low_slot_streak += 1
            print("接驳位仅剩 %d 个空位（连续 %d/%d）" % (
                n_empty, low_slot_streak, args.slot_confirm), flush=True)
            if low_slot_streak >= args.slot_confirm:
                stop_reason = "接驳位仅剩 %d 空位，已停止请手动处理" % n_empty
                print(stop_reason, flush=True)
                break
        else:
            low_slot_streak = 0

        # 清理过期的点击记录
        now = time.time()
        recent_clicks = [(x, y, t) for x, y, t in recent_clicks if now - t < args.recent_seconds]
        failed_taps = [(x, y, t) for x, y, t in failed_taps if now - t < args.failed_seconds]
        cand, mode = pick_car(result, args.head_side)

        def is_blocked(c):
            """该车是否近期点过或点过没反应。"""
            return any((c["x"]-x)**2 + (c["y"]-y)**2 < 45**2
                       for x, y, _ in recent_clicks + failed_taps)

        # 若首选被锁（刚点过/点过无效），换一辆没被锁的可开出车
        if cand and is_blocked(cand):
            exitable = [c for c in result["cars"] if c["can_exit"] and not is_blocked(c)]
            if exitable:
                exitable.sort(key=lambda c: (0 if c["color"] == result["queue"]["head"] else 1, c["y"]))
                cand, mode = exitable[0], ("match" if exitable[0]["color"] == result["queue"]["head"] else "clear")
            else:
                # 所有可开车都点过且无效：清空失败记录重试一轮（动画可能已结束）
                print("所有可开车均无响应，重置失败记录重试", flush=True)
                failed_taps.clear()
                cand, mode = pick_car(result, args.head_side)
        head = result["queue"]["head"]
        print("状态: 队首=%s 车=%d 可开出=%d 选=%s(%s) @(%d,%d)" % (
            CN.get(head, head), len(result["cars"]),
            sum(1 for c in result["cars"] if c["can_exit"]),
            CN.get(cand["color"], cand["color"]) if cand else "无",
            mode, cand["x"] if cand else -1, cand["y"] if cand else -1), flush=True)

        if cand is None:
            last_no_move += 1
            print("无可开出的车（连续 %d 次），停止" % last_no_move, flush=True)
            break
        if args.dry_run:
            print("[dry] 点 %s @(%d,%d) 方向=%s 模式=%s" % (
                CN.get(cand["color"], cand["color"]), cand["x"], cand["y"],
                cand["dir"], mode), flush=True)
            break

        clicks += 1
        before_n = len(result["cars"])
        tx, ty = car_tap_point(cand)
        tap(tx, ty, serial)
        recent_clicks.append((cand["x"], cand["y"], time.time()))
        after_img = wait_stable(serial, args.wait, args.max_wait)
        # 验证点击是否生效：车数减少或队首变化即视为成功
        moved = False
        if after_img is not None:
            after = pv.analyze(after_img, args.head_side)
            moved = (len(after["cars"]) < before_n or
                     after["queue"]["colors"] != result["queue"]["colors"])
        if moved:
            no_effect_streak = 0
        else:
            no_effect_streak += 1
            failed_taps.append((cand["x"], cand["y"], time.time()))
            print("  点击无响应，记入失败列表（连续 %d 次）" % no_effect_streak, flush=True)
            # 同一点连续无响应太多次，说明识别与游戏状态不符，停止避免死循环
            if no_effect_streak >= args.max_no_effect:
                print("连续 %d 次点击无响应，停止" % no_effect_streak, flush=True)
                break
        time.sleep(args.gap)

    message = ("%s；" % stop_reason if stop_reason else "") + \
              "任务结束：点击 %d 次，耗时 %.0fs" % (clicks, time.time() - start)
    print("done: " + message, flush=True)
    if args.notify and not args.dry_run:
        send_notify(message, args, TOOL_NAME, tool_slug="parking")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--dry-run", action="store_true", help="只演示第一步不点击")
    ap.add_argument("--no-unlock", action="store_true", help="跳过开局解锁接驳位")
    ap.add_argument("--allow-tilted", action="store_true",
                    help="倾斜关卡也自动接客（默认：解锁后停手交还用户）")
    ap.add_argument("--max-unlock", type=int, default=6)
    ap.add_argument("--unlock-threshold", type=float, default=0.72)
    ap.add_argument("--max-clicks", type=int, default=200)
    ap.add_argument("--max-seconds", type=int, default=900)
    ap.add_argument("--head-side", default="left", choices=["left", "right"])
    ap.add_argument("--wait", type=float, default=0.35)
    ap.add_argument("--max-wait", type=float, default=1.6)
    ap.add_argument("--gap", type=float, default=0.15)
    ap.add_argument("--settle", type=float, default=1.2)
    ap.add_argument("--ad-wait", type=int, default=15, help="看广告等待秒数")
    ap.add_argument("--ad-timeout", type=int, default=40, help="等回到对局超时秒数")
    ap.add_argument("--security-timeout", type=int, default=300)
    ap.add_argument("--ui-check-every", type=int, default=5, help="每隔多少步检查一次弹窗/验证")
    ap.add_argument("--recent-seconds", type=float, default=4.0, help="多久内不重复点同一位置")
    ap.add_argument("--max-no-effect", type=int, default=6, help="连续多少次点击无响应后停止")
    ap.add_argument("--failed-seconds", type=float, default=25.0, help="点过无效的坐标多久后允许重试")
    ap.add_argument("--min-empty-slots", type=int, default=1, help="接驳位空位<=此值时停止")
    ap.add_argument("--slot-confirm", type=int, default=1, help="空位不足连续确认帧数（剩1即停，避免误入广告）")
    add_notify_args(ap, "parking", TOOL_NAME, default_message='auto')
    args = ap.parse_args()
    auto_run(args)


if __name__ == "__main__":
    main()
