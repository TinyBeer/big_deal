#!/usr/bin/env python3
"""狗狗三消自动点击：识别廊道出口，先把狗送进匹配的大狗窝。

参考 tools/spool/spool_assist.py 的 adb 抓图 -> 决策 -> 点击 -> 等稳定循环。
开局可看广告解锁锁定的大小狗窝与廊道；长时间不操作弹出的窗口会自动关闭。

用法（统一入口见 quick.sh）：
  tools/dogs/quick.sh --auto --max-clicks 80
  tools/dogs/quick.sh --auto --dry-run
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dog_annotate
import exit_detect

HOUSE_CIRCLE_X = (-30, 17, 65)
HOUSE_CIRCLE_DY = 45
CORRIDOR_CENTERS = [(240, 1770), (840, 1770)]
RETURN_TEXTS = ("立即返回", "返回游戏")
DISMISS_TEXTS = ("不了", "关闭", "下次再说", "跳过", "我知道了")


def tap(x, y, serial=None):
    cmd = ["adb"] + (["-s", serial] if serial else []) + \
          ["shell", "input", "tap", str(int(round(x))), str(int(round(y)))]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def tap_touch(x, y, serial=None):
    cmd = ["adb"] + (["-s", serial] if serial else []) + \
          ["shell", "input", "touchscreen", "tap", str(int(round(x))), str(int(round(y)))]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def key_back(serial=None):
    cmd = ["adb"] + (["-s", serial] if serial else []) + ["shell", "input", "keyevent", "4"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


NOTIFY_SCRIPT = "/sdcard/Scripts/dog_notify.js"
RUN_INTENT_ACTIVITY = "org.autojs.autojs6/org.autojs.autojs.external.open.RunIntentActivity"


def notify_phone(message, serial=None, script_path=NOTIFY_SCRIPT):
    """和 spool 一样，用 AutoJS6 在手机状态栏发通知。"""
    adb = ["adb"] + (["-s", serial] if serial else [])
    js = "notice(%s, %s);\n" % (
        json.dumps("狗狗三消", ensure_ascii=False),
        json.dumps(message, ensure_ascii=False))
    fd, tmp = tempfile.mkstemp(prefix="dog_notify_", suffix=".js")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(js)
        subprocess.run(adb + ["push", tmp, script_path], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)
        subprocess.run(adb + ["shell", "am", "start", "-n", RUN_INTENT_ACTIVITY,
                              "-d", "file://" + script_path,
                              "-t", "text/javascript"],
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
    cmd = ["adb"] + (["-s", serial] if serial else [])
    subprocess.run(cmd + ["shell", "uiautomator", "dump", "/sdcard/window.xml"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    data = subprocess.run(cmd + ["exec-out", "cat", "/sdcard/window.xml"],
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


def watch_ad_return(serial, wait, timeout):
    time.sleep(wait)
    start = time.time()
    while time.time() - start < max(0, timeout - wait):
        found = find_text_node(dump_ui(serial), RETURN_TEXTS)
        if found:
            pos, _ = found
            tap(pos[0], pos[1], serial)
            time.sleep(1.5)
        img = dog_annotate.grab(serial)
        if float(img.mean()) < 12:
            time.sleep(1)
            continue
        result = dog_annotate.analyze(img)
        if result["houses"] or result["dogs"]:
            return True
        time.sleep(1)
    key_back(serial)
    return False


TPL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "popup")
POPUP_TEMPLATE = os.path.join(TPL_DIR, "no_thanks.png")
CLAIM_TEMPLATE = os.path.join(TPL_DIR, "claim_ad.png")
REVIVE_TEMPLATE = os.path.join(TPL_DIR, "revive_banner.png")


def detect_revive_dialog(img, threshold=0.80):
    """检测「复活」弹窗的橙色标题横幅。命中后由主循环立即结束，不做任何操作。

    复活弹窗上也有「不了，谢谢」，绝不能被 dismiss_popup 当成普通道具弹窗关掉。
    """
    tpl = cv2.imread(REVIVE_TEMPLATE)
    if tpl is None or tpl.shape[0] > img.shape[0] or tpl.shape[1] > img.shape[1]:
        return False
    res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
    return float(res.max()) >= threshold


def find_template(img, path, threshold=0.82):
    tpl = cv2.imread(path)
    if tpl is None or tpl.shape[0] > img.shape[0] or tpl.shape[1] > img.shape[1]:
        return None
    res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(res)
    if score < threshold:
        return None
    return (loc[0] + tpl.shape[1] // 2, loc[1] + tpl.shape[0] // 2)


def dismiss_popup(serial, img):
    """弹窗压暗画面；优先模板匹配「不了，谢谢」，不匹配再按返回。"""
    if detect_revive_dialog(img):
        return False  # 复活弹窗交给主循环结束，不能在这里点「不了，谢谢」
    if float(img.mean()) > 145 and not find_text_node(dump_ui(serial), DISMISS_TEXTS):
        return False
    tpl = cv2.imread(POPUP_TEMPLATE)
    if tpl is not None and tpl.shape[0] <= img.shape[0] and tpl.shape[1] <= img.shape[1]:
        res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(res)
        if score >= 0.82:
            tap_touch(loc[0] + tpl.shape[1] // 2, loc[1] + tpl.shape[0] // 2, serial)
            time.sleep(0.8)
            return True
    found = find_text_node(dump_ui(serial), DISMISS_TEXTS)
    if found:
        pos, _ = found
        tap_touch(pos[0], pos[1], serial)
    else:
        tap_touch(540, 1575, serial)
        key_back(serial)
    time.sleep(0.8)
    return True


def house_fill(img, house):
    """每个大狗窝下方三个圆点：深色为空，橙/彩色为已放入一只狗。"""
    x, y = house["x"], house["y"]
    filled = 0
    for dx in HOUSE_CIRCLE_X:
        cx, cy = x + dx, y + HOUSE_CIRCLE_DY
        patch = img[max(0, cy - 5):cy + 5, max(0, cx - 5):cx + 5]
        hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
        sat, val, hue = hsv[:, :, 1], hsv[:, :, 2], hsv[:, :, 0]
        if (float(np.median(val)) > 150 and float((sat > 70).mean()) > 0.5 and
                5 <= float(np.median(hue)) <= 35):
            filled += 1
    return filled


def corridor_locked(img, x, y):
    patch = img[max(0, y - 50):y + 50, max(0, x - 50):x + 50]
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    return float(((h >= 8) & (h <= 28) & (s > 100) & (v > 100)).mean()) > 0.12


def wait_stable(serial, min_wait=0.35, max_wait=1.6, interval=0.15):
    time.sleep(min_wait)
    prev, img = None, None
    start = time.time()
    while time.time() - start < max_wait:
        img = dog_annotate.grab(serial)
        small = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (270, 600))
        if prev is not None and np.mean(cv2.absdiff(small, prev)) / 255.0 < 0.012:
            break
        prev = small
        time.sleep(interval)
    return img if img is not None else dog_annotate.grab(serial)


def pick_target(exits, targets, house_fills, smalls, frequent):
    """优先送进差一只就消除的大狗窝；否则送当前数量最多的品种。"""
    cands = [d for d in exits if d["breed"] in targets]
    if cands:
        def rank(d):
            fills = [house_fills[i] for i, b in enumerate(targets[d["breed"]])]
            return (max(fills) if fills else 0, frequent.get(d["breed"], 0),
                    -d["y"], -d["x"])
        return max(cands, key=rank), "house"
    cands = [d for d in exits if d["breed"]]
    if not cands:
        return None, "none"
    in_basket = {s["label"] for s in smalls
                 if s["label"] in dog_annotate.BREED_CN.values()}
    def rank(d):
        name = dog_annotate.BREED_CN[d["breed"]]
        return (name in in_basket, frequent.get(d["breed"], 0), -d["y"], -d["x"])
    return max(cands, key=rank), "basket"


def auto_run(args):
    serial = args.device
    clicks = unlocks = 0
    tried_unlock = []
    stop_reason = ""
    start = time.time()

    while clicks < args.max_clicks and time.time() - start < args.max_seconds:
        img = dog_annotate.grab(serial)
        if float(img.mean()) < 12:
            print("画面全黑，等待 ...", flush=True)
            time.sleep(2)
            continue
        # 最高优先级：复活弹窗 → 立即结束，不做任何操作（与 ring 一致）
        if detect_revive_dialog(img):
            stop_reason = "检测到复活弹窗，立即结束（未做任何操作）"
            print(stop_reason, flush=True)
            break
        if find_text_node(dump_ui(serial), RETURN_TEXTS):
            print("广告页：等待并返回 ...", flush=True)
            watch_ad_return(serial, args.ad_wait, args.ad_timeout)
            continue
        if dismiss_popup(serial, img):
            print("已关闭弹窗", flush=True)
            continue

        result = dog_annotate.analyze(img)
        houses = [h for h in result["houses"] if h["label"] != "未知"]
        if not houses and not result["dogs"]:
            print("未识别到对局，暂停 1s 重试", flush=True)
            time.sleep(1)
            continue

        now = time.time()
        tried_unlock = [(x, y, t) for x, y, t in tried_unlock if now - t < 90]

        locked = [dict(h, kind="house") for h in result["houses"]
                  if h["label"] == "未解锁"]
        locked += [{"x": x, "y": y, "label": "廊道", "kind": "corridor"}
                   for x, y in CORRIDOR_CENTERS if corridor_locked(img, x, y)]
        locked = [r for r in locked if not any(
            (r["x"] - x) ** 2 + (r["y"] - y) ** 2 < (90 ** 2)
            for x, y, _ in tried_unlock)]
        if args.unlock and unlocks < args.max_unlock and locked:
            r = locked[0]
            unlocks += 1
            print("解锁 %d/%d %s (%d,%d) 看广告 ..." %
                  (unlocks, args.max_unlock, r["kind"], r["x"], r["y"]), flush=True)
            tap(r["x"], r["y"], serial)
            tried_unlock.append((r["x"], r["y"], now))
            if r["kind"] == "corridor":
                time.sleep(1.0)
                claim = find_template(dog_annotate.grab(serial), CLAIM_TEMPLATE)
                if claim:
                    tap_touch(claim[0], claim[1], serial)
                else:
                    print("  ! 未找到领取按钮，尝试固定位置", flush=True)
                    tap_touch(540, 1500, serial)
            ok = watch_ad_return(serial, args.ad_wait, args.ad_timeout)
            print("解锁: " + ("成功" if ok else "未回到对局，继续尝试"), flush=True)
            time.sleep(args.settle)
            continue

        exits = [d for d in result["dogs"] if d["breed"]]
        targets = {}
        house_fills = []
        for i, h in enumerate(result["houses"]):
            fill = house_fill(img, h)
            house_fills.append(fill)
            if h["label"] in dog_annotate.BREED_CN.values() and fill < 3:
                breed = next(k for k, v in dog_annotate.BREED_CN.items() if v == h["label"])
                targets.setdefault(breed, []).append(i)
        frequent = {}
        for d in exits:
            frequent[d["breed"]] = frequent.get(d["breed"], 0) + 1
        if not any(d["breed"] in targets for d in exits):
            empty_smalls = [s for s in result["smalls"] if s["label"] == "空"]
            if len(empty_smalls) <= 1:
                print("stop: 小狗窝只剩 %d 个空位，且出口狗无法进入大狗窝" %
                      len(empty_smalls), flush=True)
                break
        matching = [d for d in exits if d["breed"] in targets]
        available = [s for s in result["smalls"] if s["label"] != "未解锁"]
        empty_smalls = [s for s in available if s["label"] == "空"]
        print("状态: 狗窝=%s 目标=%s 小狗窝 空%d/可用%d 出口=%s 可入窝=%d" % (
            [h["label"] for h in result["houses"]],
            [dog_annotate.BREED_SHORT.get(b, b) for b in targets],
            len(empty_smalls), len(available),
            [dog_annotate.BREED_SHORT.get(d["breed"], d["label"]) for d in exits],
            len(matching)), flush=True)
        cand, mode = pick_target(exits, targets, house_fills, result["smalls"], frequent)
        if cand is None:
            print("无可点出口狗，停止", flush=True)
            break
        if args.dry_run:
            print("[dry] %s (%d,%d) -> %s" % (cand["label"], cand["x"], cand["y"], mode),
                  flush=True)
            break
        clicks += 1
        print("[%d] %s (%d,%d) -> %s" %
              (clicks, cand["label"], cand["x"], cand["y"], mode), flush=True)
        tap(cand["x"], cand["y"], serial)
        wait_stable(serial, args.wait, args.max_wait)
        time.sleep(args.gap)

    prefix = (stop_reason + "；") if stop_reason else "任务结束："
    message = prefix + "点击 %d 次，解锁 %d 次，耗时 %.0fs" % (
        clicks, unlocks, time.time() - start)
    print("done: " + message, flush=True)
    if args.notify and not args.dry_run:
        notify_phone(args.notify_message if args.notify_message != "auto" else message,
                     serial, args.notify_script)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--max-clicks", type=int, default=120)
    ap.add_argument("--max-seconds", type=float, default=600)
    ap.add_argument("--wait", type=float, default=0.35)
    ap.add_argument("--max-wait", type=float, default=1.6)
    ap.add_argument("--gap", type=float, default=0.15)
    ap.add_argument("--unlock", dest="unlock", action="store_true", default=True,
                    help="开局看广告解锁资源（默认开启）")
    ap.add_argument("--no-unlock", dest="unlock", action="store_false")
    ap.add_argument("--max-unlock", type=int, default=8)
    ap.add_argument("--ad-wait", type=float, default=14)
    ap.add_argument("--ad-timeout", type=float, default=35)
    ap.add_argument("--settle", type=float, default=2.0)
    ap.add_argument("--dry-run", action="store_true", help="只演示第一步决策，不点击")
    ap.add_argument("--notify", dest="notify", action="store_true", default=True,
                    help="结束后手机状态栏通知（默认开启）")
    ap.add_argument("--no-notify", dest="notify", action="store_false")
    ap.add_argument("--notify-message", default="auto",
                    help="通知内容，默认 auto 表示自动统计")
    ap.add_argument("--notify-script", default=NOTIFY_SCRIPT,
                    help="写到手机上供 AutoJS 运行的临时脚本路径")
    args = ap.parse_args()
    try:
        auto_run(args)
    except BaseException:
        if args.notify and not args.dry_run:
            notify_phone("狗狗三消异常中断", args.device, args.notify_script)
        raise


if __name__ == "__main__":
    main()
