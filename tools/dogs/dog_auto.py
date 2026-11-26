#!/usr/bin/env python3
"""狗狗三消自动点击：识别廊道出口，先把狗送进匹配的大狗窝。

参考 tools/spool/spool_assist.py 的 adb 抓图 -> 决策 -> 点击 -> 等稳定循环。
有能进大狗窝的出口狗时，按已解锁大狗窝品种选出所有不重复的目标狗，不判断狗窝
已填数量、也不限制选择数量；按原坐标依次点击后统一等画面稳定。没有大狗窝目标时
改为随机选一只狗送小狗窝（单只点击）。
开局可看广告解锁锁定的大小狗窝与廊道；长时间不操作弹出的窗口会自动关闭。

用法（统一入口见 quick.sh）：
  tools/dogs/quick.sh --auto --max-clicks 80
  tools/dogs/quick.sh --auto --batch-gap 0.2
  tools/dogs/quick.sh --auto --dry-run
"""

import argparse
import json
import os
import random
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
import dog_annotate
import fixed_match
from common.adb import dump_ui, find_text_node, key_back
from common.adb import tap as adb_tap, tap_touch as adb_tap_touch
from common.notify import add_notify_args, send_notify, notify_phone  # noqa: E402

CORRIDOR_LOCKS = [
    {"x": 240, "y": 1770, "cx": 240, "cy": 1728,
     "template": os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "templates", "corridor", "locked.png")},
    {"x": 840, "y": 1770, "cx": 842, "cy": 1728,
     "template": os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "templates", "corridor", "locked_right.png")},
]
CORRIDOR_ROW_Y = 1743
CORRIDOR_ROW_X = {"左": 415, "右": 635}
RETURN_TEXTS = ("立即返回", "返回游戏")
DISMISS_TEXTS = ("不了", "关闭", "下次再说", "跳过", "我知道了")


def tap(x, y, serial=None):
    return adb_tap(x, y, serial, check=True)


def tap_touch(x, y, serial=None):
    return adb_tap_touch(x, y, serial, check=True)


TOOL_NAME = "狗狗三消"


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


def corridor_locked(img, spec):
    """用实机锁头模板判断，阈值 0.85；解锁画面分数接近 0。"""
    tpl = cv2.imread(spec["template"], cv2.IMREAD_COLOR)
    if tpl is None:
        return False
    patch = fixed_match.crop_at(img, (spec["cx"], spec["cy"]), tpl.shape[0])
    if patch.shape[:2] != tpl.shape[:2]:
        return False
    score = float(cv2.matchTemplate(patch, tpl, cv2.TM_CCOEFF_NORMED).max())
    return score >= 0.85


def corridor_has_dog(img, side):
    """第五行出口已有狗/蛋说明该侧廊道已解锁，不必点解锁位。"""
    patch = fixed_match.crop_at(img, (CORRIDOR_ROW_X[side], CORRIDOR_ROW_Y),
                                fixed_match.SIZES["exit"])
    if dog_annotate.egg_label(patch):
        return True
    return fixed_match.get_matcher("exit").match(patch) is not None


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


def pick_targets(exits, targets):
    """按已解锁大狗窝品种，从出口选出不重复的狗，不做数量限制。

    廊道出口互相独立，同一张图上选出的多只狗可按原坐标依次点击；同一品种只取
    一只，避免重复送同一品种。大狗窝已填几只不影响选择。
    """
    pool = sorted((d for d in exits if d["breed"] in targets),
                  key=lambda d: (-d["y"], -d["x"]))
    picked, used_breeds = [], set()
    for d in pool:
        breed = d["breed"]
        if breed in used_breeds:
            continue
        if any(abs(d["x"] - c["x"]) < 60 and abs(d["y"] - c["y"]) < 60
               for c, _ in picked):
            continue
        used_breeds.add(breed)
        picked.append((d, "house"))
    return picked


def auto_run(args):
    serial = args.device
    clicks = unlocks = 0
    tried_unlock = []
    started_clicking = False
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

        if not started_clicking:
            now = time.time()
            tried_unlock = [(x, y, t) for x, y, t in tried_unlock if now - t < 90]

            locked = [dict(h, kind="house") for h in result["houses"]
                      if h["label"] == "未解锁"]
            for spec in CORRIDOR_LOCKS:
                side = "左" if spec["x"] < 540 else "右"
                # 检查被锁住的第五行出口；有狗/蛋才算已解锁，不能用当前最后一行判断
                if corridor_has_dog(img, side):
                    continue
                if corridor_locked(img, spec):
                    locked.append({"x": spec["x"], "y": spec["y"],
                                   "label": "廊道", "kind": "corridor"})
            locked = [r for r in locked if not any(
                (r["x"] - x) ** 2 + (r["y"] - y) ** 2 < (90 ** 2)
                for x, y, _ in tried_unlock)]
            if args.unlock and unlocks < args.max_unlock and locked:
                r = locked[0]
                unlocks += 1
                if args.dry_run:
                    print("[dry] 解锁 %d/%d %s (%d,%d) 看广告 ..." %
                          (unlocks, args.max_unlock, r["kind"], r["x"], r["y"]),
                          flush=True)
                    break
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
        targets = set()
        for h in result["houses"]:
            if h["label"] in dog_annotate.BREED_CN.values():
                targets.add(next(k for k, v in dog_annotate.BREED_CN.items()
                                 if v == h["label"]))
        available = [s for s in result["smalls"] if s["label"] != "未解锁"]
        empty_smalls = [s for s in available if s["label"] == "空"]
        matching = [d for d in exits if d["breed"] in targets]
        print("状态: 狗窝=%s 目标=%s 小狗窝 空%d/可用%d 出口=%s 可入窝=%d" % (
            [h["label"] for h in result["houses"]],
            [dog_annotate.BREED_SHORT.get(b, b) for b in sorted(targets)],
            len(empty_smalls), len(available),
            [dog_annotate.BREED_SHORT.get(d["breed"], d["label"]) for d in exits],
            len(matching)), flush=True)
        if matching:
            picked = pick_targets(exits, targets)
            print("本轮选择 %d 个不重复大狗窝候选: %s" % (
                len(picked),
                " ".join("%s->%s" % (dog_annotate.BREED_SHORT.get(d["breed"], d["label"]),
                                     mode) for d, mode in picked)), flush=True)
        else:
            # 没有大狗窝目标：随机选一只送小狗窝，单只点击，不走批量逻辑
            if len(empty_smalls) <= 1:
                print("stop: 小狗窝只剩 %d 个空位，且无大狗窝目标" %
                      len(empty_smalls), flush=True)
                break
            if not exits:
                print("无可点出口狗，停止", flush=True)
                break
            cand = random.choice(exits)
            picked = [(cand, "basket")]
            print("无大狗窝目标，随机选 1 只送小狗窝: %s (%d,%d)" %
                  (cand["label"], cand["x"], cand["y"]), flush=True)
        picked = picked[:max(0, args.max_clicks - clicks)]
        if not picked:
            print("无可点出口狗，停止", flush=True)
            break
        if args.dry_run:
            for i, (d, mode) in enumerate(picked, 1):
                print("[dry] %d/%d %s (%d,%d) -> %s" % (
                    i, len(picked), d["label"], d["x"], d["y"], mode), flush=True)
            break
        for i, (cand, mode) in enumerate(picked):
            # 批内下一只点击前复查复活弹窗，命中立即停手
            if i > 0:
                mid = dog_annotate.grab(serial)
                if mid is not None and detect_revive_dialog(mid):
                    stop_reason = "批次内检测到复活弹窗，立即停手"
                    print(stop_reason, flush=True)
                    break
            clicks += 1
            print("[%d] 批内 %d/%d %s (%d,%d) -> %s" %
                  (clicks, i + 1, len(picked), cand["label"], cand["x"], cand["y"], mode),
                  flush=True)
            tap(cand["x"], cand["y"], serial)
            started_clicking = True
            if i < len(picked) - 1:
                time.sleep(args.batch_gap)
        if stop_reason:
            break
        wait_stable(serial, args.wait, args.max_wait)
        time.sleep(args.gap)

    prefix = (stop_reason + "；") if stop_reason else "任务结束："
    message = prefix + "点击 %d 次，解锁 %d 次，耗时 %.0fs" % (
        clicks, unlocks, time.time() - start)
    print("done: " + message, flush=True)
    if args.notify and not args.dry_run:
        send_notify(message, args, TOOL_NAME, tool_slug="dogs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--max-clicks", type=int, default=120)
    ap.add_argument("--max-seconds", type=float, default=600)
    ap.add_argument("--wait", type=float, default=0.35)
    ap.add_argument("--max-wait", type=float, default=1.6)
    ap.add_argument("--gap", type=float, default=0.15)
    ap.add_argument("--batch-size", type=int, default=0,
                    help="已废弃：现在按已解锁大狗窝品种全选不重复狗，保留参数仅为兼容")
    ap.add_argument("--batch-gap", type=float, default=0.2,
                    help="相邻两次点击的间隔秒数（默认 0.2）")
    ap.add_argument("--unlock", dest="unlock", action="store_true", default=True,
                    help="开局看广告解锁资源（默认开启）")
    ap.add_argument("--no-unlock", dest="unlock", action="store_false")
    ap.add_argument("--max-unlock", type=int, default=8)
    ap.add_argument("--ad-wait", type=float, default=14)
    ap.add_argument("--ad-timeout", type=float, default=35)
    ap.add_argument("--settle", type=float, default=2.0)
    ap.add_argument("--dry-run", action="store_true", help="只演示第一步决策，不点击")
    add_notify_args(ap, "dogs", TOOL_NAME)
    args = ap.parse_args()
    try:
        auto_run(args)
    except BaseException:
        if args.notify and not args.dry_run:
            notify_phone("狗狗三消异常中断", args.device,
                         tool_name=TOOL_NAME, tool_slug="dogs")
        raise


if __name__ == "__main__":
    main()
