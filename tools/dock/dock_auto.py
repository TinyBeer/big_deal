#!/usr/bin/env python3
"""螺丝接驳位解锁 · 自动点击。

对局顶部有一排接驳位，未解锁的位上是紫色「解锁」按钮（白螺丝图标 + 橙色螺丝头）。
点它会直接跳到广告页（有时先弹「获得福利」，点「领取/视频」才进广告）；广告看完
点「点击立即返回」回到对局，该接驳位即解锁。本工具循环做这件事，直到没有解锁按钮。

用法（统一入口见 quick.sh）：
  tools/dock/quick.sh --dry-run     # 只识别、只演示第一步
  tools/dock/quick.sh --once        # 只识别一次，输出标注图
  tools/dock/quick.sh               # 默认自动解锁到没有按钮为止
"""
import argparse
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
import dock_vision as dv
from common.adb import dump_ui, find_text_node, key_back, tap
from common.notify import add_notify_args, send_notify

RETURN_TEXTS = ("点击立即返回", "立即返回", "返回游戏")
SECURITY_TEXTS = ("安全验证", "京东验证")
TOOL_NAME = "接驳位解锁"


def has_security_check(serial=None):
    return find_text_node(dump_ui(serial), SECURITY_TEXTS) is not None


def dismiss(serial, res):
    """关闭当前弹窗：优先点右上角 X（不领视频奖励）。"""
    if res.get("close"):
        cx, cy, _ = res["close"]
    elif res.get("claim"):
        # 没识别到 X 时退化为点「领取」所在弹窗的右上角
        cx, cy, _ = res["claim"]
        cx, cy = min(cx + 430, 1010), cy - 480
    else:
        return False
    tap(cx, cy, serial)
    time.sleep(0.8)
    return True


def click_claim(serial, res):
    """点「领取（视频）」进广告 —— 解锁需要看完这条视频。"""
    cx, cy, _ = res["claim"]
    tap(cx, cy, serial)
    time.sleep(1.0)
    return True


def return_to_game(serial, args):
    """等广告走完并回到对局。返回 True 表示已在对局里。"""
    deadline = time.time() + args.ad_timeout
    time.sleep(max(0.0, args.ad_wait))
    back_pressed = 0
    while time.time() < deadline:
        img = dv.grab(serial)
        if img is not None:
            if dv.is_game(img):
                return True
            hit = dv.find_return(img)
            if hit:
                tap(hit[0], hit[1], serial)
                time.sleep(1.5)
                continue
        # 文本兜底（广告页的“点击立即返回”是可控控件）
        found = find_text_node(dump_ui(serial), RETURN_TEXTS)
        if found:
            tap(found[0][0], found[0][1], serial, touch=True)
            time.sleep(1.5)
            continue
        if back_pressed < args.max_back:
            key_back(serial)
            back_pressed += 1
        time.sleep(1.5)
    return False


def wait_state(serial, args, timeout=12.0):
    """点完解锁后轮询，返回首个可判断的状态快照。"""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        img = dv.grab(serial)
        if img is not None:
            last = dv.analyze(img)
            if last["popup"] or not last["game"] or last["count"]:
                return img, last
        time.sleep(0.7)
    return None, last


def unlock_round(serial, args, before):
    """执行一次解锁：点按钮 -> 处理弹窗/广告 -> 回到对局。返回是否成功。

    按用户口径：福利弹窗一律点 X 关掉，不领视频奖励；解锁的广告是点按钮后
    自动跳转的。关掉弹窗后可能接着跳广告，所以继续轮询而不是立刻判定失败。
    """
    hit = before["unlock"][0]
    tap(hit["x"], hit["y"], serial)
    print("  点解锁按钮 @(%d,%d)" % (hit["x"], hit["y"]), flush=True)
    time.sleep(args.settle)

    for _ in range(6):
        img, res = wait_state(serial, args)
        if res is None:
            print("  抓图失败，跳过", flush=True)
            return False
        if res["popup"]:
            if args.claim and res.get("claim"):
                print("  福利弹窗：点「领取(视频)」", flush=True)
                click_claim(serial, res)
            else:
                print("  福利弹窗：点 X 关闭", flush=True)
                dismiss(serial, res)
            time.sleep(0.8)
            continue
        if not res["game"]:
            print("  进入广告页，等待看完 ...", flush=True)
            if not return_to_game(serial, args):
                print("  广告页未返回对局", flush=True)
                return False
            continue
        # 已在对局：确认解锁按钮是否减少
        if res["count"] < before["count"]:
            return True
        # 关弹窗后没跳广告、按钮数没变 => 这次点击没生效，交给主循环重试
        print("  回到对局但仍剩 %d 个解锁按钮" % res["count"], flush=True)
        return False
    return False


def auto_run(args):
    serial = args.device
    start = time.time()
    unlocked = 0
    stop_reason = ""
    fails = 0

    while unlocked < args.max_unlock and time.time() - start < args.max_seconds:
        img = dv.grab(serial)
        if img is None:
            time.sleep(1)
            continue
        res = dv.analyze(img)

        if has_security_check(serial):
            stop_reason = "遇到安全验证，请手动完成后重跑"
            print(stop_reason, flush=True)
            break

        if res["popup"]:
            # 非解锁流程中的弹窗：只关不领
            print("弹窗：点 X 关闭", flush=True)
            dismiss(serial, res)
            time.sleep(0.8)
            continue
        if not res["game"]:
            print("不在对局（广告/加载页），尝试返回 ...", flush=True)
            if not return_to_game(serial, args):
                stop_reason = "无法回到对局"
                break
            continue
        if not res["count"]:
            stop_reason = "已无待解锁接驳位，完成"
            print(stop_reason, flush=True)
            break

        if args.dry_run:
            print("[dry] 待解锁 %d 个，第一个 @(%d,%d)" % (
                res["count"], res["unlock"][0]["x"], res["unlock"][0]["y"]), flush=True)
            break

        if unlock_round(serial, args, res):
            unlocked += 1
            fails = 0
            print("解锁成功 %d 个（剩余待解锁 %d）" % (unlocked, max(0, res["count"] - 1)), flush=True)
        else:
            fails += 1
            print("解锁未成功（连续 %d/%d）" % (fails, args.max_fails), flush=True)
            if fails >= args.max_fails:
                stop_reason = "连续 %d 次解锁未成功，停止" % fails
                print(stop_reason, flush=True)
                break
            key_back(serial)
            time.sleep(args.settle)
        time.sleep(args.gap)

    message = ("%s；" % stop_reason if stop_reason else "") + \
              "解锁 %d 个接驳位，耗时 %.0fs" % (unlocked, time.time() - start)
    print("done: " + message, flush=True)
    if args.notify and not args.dry_run:
        send_notify(message, args, TOOL_NAME, tool_slug="dock")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--dry-run", action="store_true", help="只识别并演示第一步，不点击")
    ap.add_argument("--max-unlock", type=int, default=6, help="本轮到多解锁几个")
    ap.add_argument("--max-seconds", type=int, default=420)
    ap.add_argument("--ad-wait", type=float, default=16.0,
                    help="点完领取后先等多久（广告落地页倒计时）")
    ap.add_argument("--ad-timeout", type=float, default=50.0, help="等广告结束的总超时")
    ap.add_argument("--max-back", type=int, default=3, help="广告页最多按几次返回")
    ap.add_argument("--claim", action="store_true",
                    help="福利弹窗点「领取(视频)」而不是 X（默认只关弹窗）")
    ap.add_argument("--settle", type=float, default=1.2)
    ap.add_argument("--gap", type=float, default=0.8)
    ap.add_argument("--max-fails", type=int, default=3)
    add_notify_args(ap, "dock", TOOL_NAME, default_message="auto")
    args = ap.parse_args()
    auto_run(args)


if __name__ == "__main__":
    main()
