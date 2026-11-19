#!/usr/bin/env python3
# pyright: reportMissingParameterType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownLambdaType=false, reportUnusedCallResult=false
"""三消线卷辅助识别：截屏 -> 找目标大线卷 -> 圈出可点击的小线卷。

用法示例：
  /home/beer/.workbuddy/binaries/python/envs/default/bin/python tools/spool/spool_assist.py --image shot.png --once
  /home/beer/.workbuddy/binaries/python/envs/default/bin/python tools/spool/spool_assist.py --once --output result.png
  /home/beer/.workbuddy/binaries/python/envs/default/bin/python tools/spool/spool_assist.py --live
  /home/beer/.workbuddy/binaries/python/envs/default/bin/python tools/spool/spool_assist.py --live --targets yellow pink --interval 0.7
  /home/beer/.workbuddy/binaries/python/envs/default/bin/python tools/spool/spool_assist.py --auto

说明：
  --targets 可手动指定目标颜色；不传时自动从顶部彩色大线卷读取。
  置灰/锁定的大线卷无法读出颜色，会被单独列出并跳过。
  中间最长的白色线卷是暂存区，不作为目标；没有目标色可点时，自动模式会点其他
  顶层线卷把它送进暂存区。暂存区存满即失败，不会因同色自动消除；顶部刷新出
  对应颜色的空线卷时才会从暂存区移走 3 个。没有目标色可点时，优先清掉剩余
  线卷最少的挡板；释放挡板后下一轮会优先恢复消除。挡板按线卷周围的半透明
  底色分组，消除和释放都优先选所在挡板剩余线卷更少的位置。复活后会多等一会儿。
  消除之前先看广告解锁锁定的线卷槽；失败弹窗也会自动点「获得」看广告复活。
  两者都靠「点击立即返回」控件回游戏。遇到京东安全验证会暂停等用户手动完成，
  --security-timeout 控制最长等待时间，--no-revive 可关闭自动复活。
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

# HSV  hue 范围（OpenCV: 0~179）及标注用 BGR
COLORS = {
    "red":    ((0, 9),   (60, 60, 235)),
    "brown":  ((171, 179), (70, 75, 140)),
    "orange": ((10, 15), (40, 150, 255)),
    "yellow": ((16, 33), (40, 215, 245)),
    "green":  ((45, 75), (60, 220, 70)),
    "cyan":   ((80, 98), (225, 220, 70)),
    "blue":   ((99, 112), (230, 100, 45)),    # 浅天蓝
    "navy":   ((113, 125), (180, 55, 30)),    # 深宝蓝/靛蓝（与 blue 不同色，不可混点）
    "purple": ((126, 154), (190, 70, 220)),
    "pink":   ((155, 170), (170, 70, 235)),
}
# 区域按屏幕比例定义，便于适配不同分辨率
BIG_BAND = (0.00, 0.385, 1.00, 0.42)  # 顶部大线卷横条（避开下方连成一片的底座）
BOARD_BAND = (0.04, 0.50, 0.96, 0.93)  # 下方小线卷棋盘


def hue_name(h, v=255):
    h = int(h) % 180
    if h >= 171 or h <= 9:
        return "brown" if v < 190 else "red"
    for name, ((lo, hi), _) in COLORS.items():
        if name == "brown":
            continue
        if lo <= h <= hi:
            return name
    return None


def region(img, box):
    h, w = img.shape[:2]
    x1, y1, x2, y2 = box
    return img[int(y1 * h):int(y2 * h), int(x1 * w):int(x2 * w)]


def detect_big_spools(img, hsv):
    """返回顶部大线卷：彩色 -> 颜色名；置灰 -> locked。"""
    x0, y0, x1, y1 = BIG_BAND
    h, w = img.shape[:2]
    ry0, ry1 = int(y0 * h), int(y1 * h)
    rx0, rx1 = int(x0 * w), int(x1 * w)
    band = hsv[ry0:ry1, rx0:rx1]
    sat, val = band[:, :, 1], band[:, :, 2]

    found = []

    # 彩色大线卷：普通色用高饱和阈值；深棕色单独用中低饱和+偏暗阈值，避免相邻线卷连成一块
    masks = [
        ((sat > 140) & (val > 120), None),
        ((sat > 95) & (sat <= 140) & (val > 110) & (val < 190), "brown"),
    ]
    for raw, forced in masks:
        mask = cv2.morphologyEx(raw.astype(np.uint8) * 255, cv2.MORPH_CLOSE,
                                cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3)))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            x, y, cw, ch = cv2.boundingRect(c)
            area = cv2.contourArea(c)
            if cw < w * 0.08 or ch < h * 0.015 or area < 1500:
                continue
            local = band[y:y + ch, x:x + cw]
            m = raw[y:y + ch, x:x + cw]
            hues = local[:, :, 0][m]
            vals = local[:, :, 2][m]
            if hues.size == 0:
                continue
            name = forced or hue_name(int(np.median(hues)), float(np.median(vals)))
            if not name:
                continue
            found.append({
                "kind": "color", "color": name,
                "x": rx0 + x + cw // 2, "y": ry0 + y + ch // 2,
                "width": cw, "height": ch,
            })

    # 置灰/锁定的大线卷：低饱和的灰色横条
    gray = ((sat < 35) & (val > 110) & (val < 215)).astype(np.uint8) * 255
    gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (9, 3)))
    contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        if cw < w * 0.08 or ch < h * 0.015 or area < 1500:
            continue
        found.append({
            "kind": "locked", "color": None,
            "x": rx0 + x + cw // 2, "y": ry0 + y + ch // 2,
            "width": cw, "height": ch,
        })

    found.sort(key=lambda s: s["x"])
    unique = []
    for s in found:
        overlap = next((u for u in unique
                        if abs(u["x"] - s["x"]) < 100 * (w / 1080.0)
                        and abs(u["y"] - s["y"]) < 30 * (w / 1080.0)), None)
        if overlap is None:
            unique.append(s)
        elif s["width"] * s["height"] > overlap["width"] * overlap["height"]:
            unique[unique.index(overlap)] = s
    return sorted(unique, key=lambda s: s["x"])


def detect_small_spools(img, hsv):
    """找顶层（未被遮挡）小线卷：灰色圆心 + 外围高饱和色环。"""
    x0, y0, x1, y1 = BOARD_BAND
    h, w = img.shape[:2]
    ry0, ry1 = int(y0 * h), int(y1 * h)
    rx0, rx1 = int(x0 * w), int(x1 * w)
    board = hsv[ry0:ry1, rx0:rx1]
    sat, val = board[:, :, 1], board[:, :, 2]
    board_bgr = img[ry0:ry1, rx0:rx1]
    # 被白色箭头/线条压住的线卷：圆心边缘会出现大量近纯白像素，实际不可点
    bright = np.all(board_bgr > 240, axis=2)

    # 顶层线卷圆心：中性灰，且不是纯白/纯黑
    gray = ((sat < 32) & (val >= 120) & (val <= 235)).astype(np.uint8) * 255
    gray = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    # RETR_LIST：蓝色挡板可能把整片区域连成一大块，小圆心会成为内部轮廓
    contours, _ = cv2.findContours(gray, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    scale = w / 1080.0
    r_in, r_out = 30 * scale, 45 * scale
    results = []
    for c in contours:
        area = cv2.contourArea(c)
        _, _, cw, ch = cv2.boundingRect(c)
        if not (2300 * scale * scale <= area <= 4200 * scale * scale):
            continue
        if not (45 * scale <= cw <= 80 * scale and 45 * scale <= ch <= 80 * scale):
            continue
        if abs(cw - ch) > max(cw, ch) * 0.45:
            continue
        M = cv2.moments(c)
        if M["m00"] <= 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        # 圆心内暗外亮（顶层线卷的立体灰心），下层半透明线卷没有这个特征
        core = val[max(0, cy - 5):cy + 6, max(0, cx - 5):cx + 6]
        ring = val[max(0, cy - 18):cy + 19, max(0, cx - 18):cx + 19]
        if core.size == 0 or ring.size == 0:
            continue
        if float(np.median(core)) > 205 or float(np.median(ring)) - float(np.median(core)) < 12:
            continue

        # 圆心边缘若有白色线条压过，说明被遮挡，不能点
        yy, xx = np.ogrid[-cy:board.shape[0] - cy, -cx:board.shape[1] - cx]
        r2 = xx * xx + yy * yy
        core_edge = (r2 >= (15 * scale) ** 2) & (r2 <= (35 * scale) ** 2)
        if core_edge.sum() and bright[core_edge].mean() > 0.03:
            continue

        # 外围色环：棕色偏暗，亮度阈值不能卡太高
        ann = (r2 >= r_in * r_in) & (r2 <= r_out * r_out)
        sel = ann & (sat > 80) & (val > 100)
        if ann.sum() == 0 or sel.sum() / ann.sum() < 0.50:
            continue
        hues = board[:, :, 0][sel]
        vals = board[:, :, 2][sel]
        if hues.size < 40:
            continue
        name = hue_name(float(np.median(hues)), float(np.median(vals)))
        if not name:
            continue

        results.append({
            "color": name,
            "x": rx0 + cx, "y": ry0 + cy,
            "radius": max(cw, ch) / 2,
        })

    # 去掉重复圆心（同一线卷可能被切成多块）
    results.sort(key=lambda s: (s["x"], s["y"]))
    unique = []
    for s in results:
        if any(abs(s["x"] - u["x"]) < 20 * scale and abs(s["y"] - u["y"]) < 20 * scale
               for u in unique):
            continue
        unique.append(s)
    return unique


def analyze(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    big = detect_big_spools(img, hsv)
    small = detect_small_spools(img, hsv)
    targets = sorted({b["color"] for b in big if b["kind"] == "color"})
    return big, small, targets


def annotate(img, big, small, targets):
    out = img.copy()
    _, w = out.shape[:2]
    scale = w / 1080.0
    font = cv2.FONT_HERSHEY_SIMPLEX
    fs = 0.75 * scale
    thick = max(2, int(4 * scale))

    def pt(x, y):
        return (int(round(x)), int(round(y)))

    for b in big:
        x1, y1 = pt(b["x"] - b["width"] / 2, b["y"] - b["height"] / 2)
        x2, y2 = pt(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        if b["kind"] == "locked":
            cv2.rectangle(out, (x1, y1), (x2, y2), (110, 110, 110), 2, cv2.LINE_AA)
            cv2.putText(out, "LOCKED", pt(b["x"] - 55 * scale, b["y"] - b["height"] / 2 - 8 * scale),
                        font, fs * 0.8, (90, 90, 90), 2, cv2.LINE_AA)
        else:
            bgr = COLORS[b["color"]][1]
            cv2.rectangle(out, (x1, y1), (x2, y2), bgr, thick, cv2.LINE_AA)

    clickable = [s for s in small if s["color"] in targets]
    for i, s in enumerate(clickable, 1):
        bgr = COLORS[s["color"]][1]
        center = pt(s["x"], s["y"])
        r = int(max(s["radius"] + 8 * scale, 30 * scale))
        cv2.circle(out, center, r, bgr, thick, cv2.LINE_AA)
        cv2.circle(out, center, int(r + 6 * scale), (255, 255, 255),
                   max(1, thick // 2), cv2.LINE_AA)
        pos = pt(s["x"] - 10 * scale, s["y"] + 10 * scale)
        cv2.putText(out, str(i), pos, font, fs, (20, 20, 20), thick + 1, cv2.LINE_AA)
        cv2.putText(out, str(i), pos, font, fs, (255, 255, 255), thick - 1, cv2.LINE_AA)

    lines = [
        "TARGET: " + (",".join(targets) if targets else "unknown (all locked)"),
        "CLICKABLE: %d" % len(clickable),
    ]
    banner_w = int(430 * scale)
    banner_h = int((30 + 40 * len(lines)) * scale)
    cv2.rectangle(out, pt(10 * scale, 10 * scale),
                  pt(10 * scale + banner_w, 10 * scale + banner_h),
                  (25, 25, 25), -1, cv2.LINE_AA)
    for i, text in enumerate(lines):
        cv2.putText(out, text, pt(20 * scale, (48 + 40 * i) * scale),
                    font, 0.95 * scale, (255, 255, 255), max(1, thick - 1), cv2.LINE_AA)
    return out, clickable


def has_gui():
    """headless 构建不支持 imshow；探测一次，用于 --live 降级为写文件。"""
    try:
        cv2.imshow("__probe__", np.zeros((2, 2), np.uint8))
        cv2.destroyAllWindows()
        return True
    except Exception:
        return False


def grab(serial=None):
    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    cmd += ["exec-out", "screencap", "-p"]
    data = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=True).stdout
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError("截图解码失败")
    return img


def has_modal(img, threshold=150):
    """失败/复活/游戏中心等弹窗会压暗整屏，平均亮度明显低于正常对局。"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return float(hsv[:, :, 2].mean()) < threshold


def tap(x, y, serial=None):
    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    cmd += ["shell", "input", "tap", str(int(round(x))), str(int(round(y)))]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


NOTIFY_SCRIPT = "/sdcard/Scripts/spool_notify.js"
RUN_INTENT_ACTIVITY = "org.autojs.autojs6/org.autojs.autojs.external.open.RunIntentActivity"


def notify_phone(message, serial=None, script_path=NOTIFY_SCRIPT):
    """通过 adb 让手机上的 AutoJS6 直接运行一个 notice 脚本，无需常驻监听。

    先把带标题和内容的 JS 写到手机，再用 AutoJS6 的 RunIntentActivity 执行它。
    notice() 会在状态栏生成常驻通知，需要 AutoJS6 的 POST_NOTIFICATIONS 权限。
    """
    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    js = "notice(%s, %s);\n" % (
        json.dumps("线卷三消", ensure_ascii=False),
        json.dumps(message, ensure_ascii=False),
    )
    fd, tmp = tempfile.mkstemp(prefix="spool_notify_", suffix=".js")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(js)
        subprocess.run(cmd + ["push", tmp, script_path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(
            cmd + ["shell", "am", "start",
                   "-n", RUN_INTENT_ACTIVITY,
                   "-d", "file://" + script_path,
                   "-t", "text/javascript"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("提醒: 已让 AutoJS 发出通知: %s" % message, flush=True)
        return True
    except (OSError, subprocess.CalledProcessError) as e:
        print("提醒: 发送失败: %s" % e, flush=True)
        return False
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def wait_stable(serial=None, min_wait=0.35, max_wait=1.8, interval=0.15):
    """点击后等画面稳定：最短等待 + 连续两帧差异小于阈值即返回。"""
    time.sleep(min_wait)
    prev = None
    img = None
    start = time.time()
    while time.time() - start < max_wait:
        img = grab(serial)
        small = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (270, 600))
        if prev is not None and np.mean(cv2.absdiff(small, prev)) / 255.0 < 0.012:
            break
        prev = small
        time.sleep(interval)
    return img if img is not None else grab(serial)


def pick_next(clickable, recent, scale):
    """优先点当前可选数量最多的颜色，避开刚点过的位置。"""
    cands = [
        s for s in clickable
        if not any((s["x"] - x) ** 2 + (s["y"] - y) ** 2 < (28 * scale) ** 2
                   for x, y in recent)
    ]
    if not cands:
        return None
    counts = {}
    for s in cands:
        counts[s["color"]] = counts.get(s["color"], 0) + 1
    best = max(counts, key=lambda c: (counts[c], c))
    pool = [s for s in cands if s["color"] == best]
    pool.sort(key=lambda s: (s["y"], s["x"]))
    return pool[0]


def detect_top_boards(img, small=None, min_area=8000):
    """检测顶层挡板：挡板外围白色描边完整闭合的区域即顶层。

    原理：顶层挡板没被别的挡板/线卷压住，白色描边围成封闭环；下层挡板被
    遮挡，描边断开并与背景连通。做法是在棋盘区提取纯白像素、轻微膨胀补上
    被线卷压出的细小缺口，再找不与边界连通的封闭区域。若一个封闭区套在
    另一个里（嵌套挡板），只保留最内层作为当前顶层。

    @param min_area: 封闭区最小像素面积（按 1080 宽归一化的量级），过滤小空隙
    @returns: 顶层挡板列表，每项含 bbox(x,y,w,h)、cx/cy(全屏坐标)、area、spools
    """
    h, w = img.shape[:2]
    scale = w / 1080.0
    x0, y0, x1, y1 = BOARD_BAND
    rx0, ry0, rx1, ry1 = int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)
    crop = img[ry0:ry1, rx0:rx1]

    # 挡板描边是接近纯白的实线（背景浅蓝 G/B 通道明显低于 R，不会命中）
    white = ((crop[:, :, 0] > 235) & (crop[:, :, 1] > 235) &
             (crop[:, :, 2] > 235)).astype(np.uint8)
    wall = cv2.dilate(white, np.ones((3, 3), np.uint8), iterations=1)
    free = (1 - wall).astype(np.uint8)
    n, labels, stats, cents = cv2.connectedComponentsWithStats(free, 4)
    ch, cw = free.shape

    regions = []
    min_px = min_area * scale * scale
    for i in range(1, n):
        x, y, ww, hh, area = stats[i]
        # 与裁剪边界连通 = 背景，不是封闭挡板
        if x == 0 or y == 0 or x + ww == cw or y + hh == ch:
            continue
        if area < min_px:
            continue
        mask = (labels == i).astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            continue
        hull = cv2.convexHull(max(contours, key=cv2.contourArea))
        regions.append({
            "i": i, "area": int(area),
            "bbox": (rx0 + x, ry0 + y, ww, hh),
            "cx": rx0 + cents[i][0], "cy": ry0 + cents[i][1],
            "hull": [(rx0 + p[0][0], ry0 + p[0][1]) for p in hull],
        })

    # 嵌套：若区域 a 的中心落在区域 b 的凸包内，说明 b 套在 a 外面（b 是外层）。
    # 只保留没有子层的最内层封闭区作为顶层挡板——嵌套时内层压在外层上面。
    top = []
    for a in regions:
        has_inner = any(
            b is not a and b["area"] < a["area"] and
            cv2.pointPolygonTest(np.array(a["hull"], np.float32),
                                 (b["cx"], b["cy"]), False) >= 0
            for b in regions
        )
        if not has_inner:
            top.append(a)

    # 把线卷归到所属顶层挡板（判断线卷中心是否落在封闭区内）
    if small:
        for b in top:
            b["spools"] = []
        for sp in small:
            lx, ly = int(sp["x"] - rx0), int(sp["y"] - ry0)
            if 0 <= lx < cw and 0 <= ly < ch:
                lab = labels[ly, lx]
                for b in top:
                    if lab == b["i"]:
                        b["spools"].append(sp)
    else:
        for b in top:
            b["spools"] = []

    return top


def group_by_board(spools, img):
    """按线卷周围的挡板底色分组：挡板是半透明色块，色相可区分。"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    scale = img.shape[1] / 1080.0
    yy, xx = np.ogrid[:img.shape[0], :img.shape[1]]
    groups = {}
    for s in spools:
        x, y = s["x"], s["y"]
        r2 = (xx - x) ** 2 + (yy - y) ** 2
        ring = ((r2 >= (44 * scale) ** 2) & (r2 <= (58 * scale) ** 2) &
                (hsv[:, :, 1] > 10) & (hsv[:, :, 2] > 120))
        hues = hsv[:, :, 0][ring]
        key = int(np.median(hues) // 15) * 15 if hues.size else -1
        groups.setdefault(key, []).append(s)

    # 同色挡板可能并排多块，用横坐标间隔再切分
    split = {}
    for key, members in groups.items():
        members = sorted(members, key=lambda s: s["x"])
        parts = [[members[0]]] if members else []
        for s in members[1:]:
            if s["x"] - parts[-1][-1]["x"] > 120 * scale:
                parts.append([s])
            else:
                parts[-1].append(s)
        for i, part in enumerate(parts):
            split[(key, i)] = part
    return split


def pick_by_board(candidates, small, excluded, scale, img):
    """在候选线卷里优先选「所在挡板剩余线卷最少」的。"""
    if not candidates:
        return None, "empty"
    groups = group_by_board(small, img)
    ranked = []
    for members in groups.values():
        subset = [s for s in candidates if s in members]
        if subset:
            ranked.append((len(members), subset))
    ranked.sort(key=lambda t: t[0])
    for count, subset in ranked:
        cand = pick_next(subset, excluded, scale)
        if cand is not None:
            return cand, "board(%d spools)" % count
    cand = pick_next(candidates, excluded, scale)
    return cand, "fallback"


def pick_unlock(small, targets, excluded, scale, img, top_boards=None):
    """没有目标色可点时，优先清掉顶层挡板（白色描边完整）里剩余线卷少的。

    顶层挡板才可能被释放；点下层挡板往往被遮挡而无效。若顶层挡板没有可点
    线卷，回退到原有「按挡板线卷数最少」策略。
    """
    pool = [s for s in small if s["color"] not in targets]
    if top_boards:
        top_spools = [sp for b in top_boards for sp in b.get("spools", [])]
        top_pool = [s for s in pool if s in top_spools]
        if top_pool:
            cand, reason = pick_by_board(top_pool, small, excluded, scale, img)
            if cand is not None:
                return cand, "top-board|" + reason
    return pick_by_board(pool, small, excluded, scale, img)


def dump_ui(serial):
    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    subprocess.run(cmd + ["shell", "uiautomator", "dump", "/sdcard/window.xml"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    xml = subprocess.run(cmd + ["exec-out", "cat", "/sdcard/window.xml"],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
    if not xml:
        return None
    try:
        return ET.fromstring(xml)
    except ET.ParseError:
        return None


def find_return_button(serial):
    """从控件树里找「点击立即返回」，返回中心坐标。"""
    root = dump_ui(serial)
    if root is None:
        return None
    for node in root.iter("node"):
        text = node.get("text", "")
        if "立即返回" not in text:
            continue
        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", node.get("bounds", ""))
        if not m:
            continue
        x1, y1, x2, y2 = [int(v) for v in m.groups()]
        if x2 > x1 and y2 > y1:
            return (int((x1 + x2) / 2), int((y1 + y2) / 2))
    return None


def has_security_check(serial):
    """京东验证等安全验证页：命中后应暂停，等用户自己操作。"""
    root = dump_ui(serial)
    if root is None:
        return False
    for node in root.iter("node"):
        text = node.get("text", "")
        if "安全验证" in text or "京东验证" in text:
            return True
    return False


def wait_for_user(serial, timeout):
    """等用户手动处理安全验证，直到回到游戏画面或超时。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(2)
        if has_security_check(serial):
            continue
        img = grab(serial)
        if has_modal(img):
            continue
        big, small, _ = analyze(img)
        if big or small:
            return True
    return False


def watch_ad_return(serial, wait, timeout):
    """等广告播完，点「点击立即返回」回到游戏。"""
    time.sleep(wait)
    start = time.time()
    while time.time() - start < max(0, timeout - wait):
        pos = find_return_button(serial)
        if pos:
            tap(pos[0], pos[1], serial)
            time.sleep(1.5)
        after = grab(serial)
        big, small, _ = analyze(after)
        if not has_modal(after) and (big or small):
            return True
        time.sleep(1)
    return False


def revive_by_ad(serial, x_ratio, y_ratio, wait, timeout):
    """失败页点底部「获得」，看完广告后点「点击立即返回」回到对局。"""
    img = grab(serial)
    tap(img.shape[1] * x_ratio, img.shape[0] * y_ratio, serial)
    return watch_ad_return(serial, wait, timeout)


def auto_run(args):
    serial = args.device
    scale = 1.0
    recent = []
    failed = []
    clicks = 0
    unlocks = 0
    revives = 0
    slot_unlocks = 0
    tried_slots = []
    started = time.time()

    while clicks < args.max_clicks and time.time() - started < args.max_seconds:
        img = grab(serial)
        if has_security_check(serial):
            print("暂停: 检测到安全验证，请手动完成，脚本不会点击 ...", flush=True)
            ok = wait_for_user(serial, args.security_timeout)
            print("安全验证: " + ("已结束，继续对局" if ok else "等待超时，停止"), flush=True)
            if not ok:
                break
            continue
        if has_modal(img, args.modal_v):
            if args.no_revive or revives >= args.max_revive:
                print("stop: 检测到失败/弹窗页面，已停止（保留现场）")
                break
            revives += 1
            print("revive %d/%d: 点「获得」看广告 %.0fs ..." %
                  (revives, args.max_revive, args.revive_wait), flush=True)
            ok = revive_by_ad(serial, args.revive_x, args.revive_y,
                              args.revive_wait, args.revive_timeout)
            print("revive: " + ("成功，继续对局" if ok else "未回到对局，停止"), flush=True)
            if not ok:
                break
            time.sleep(args.revive_settle)
            continue
        scale = img.shape[1] / 1080.0
        big, small, targets = analyze(img)
        if args.targets:
            targets = args.targets
        annotated, clickable = annotate(img, big, small, targets)
        cv2.imwrite(args.output, annotated)
        now = time.time()
        recent = [(x, y, t) for x, y, t in recent if now - t < args.recent_seconds]
        failed = [(x, y, t) for x, y, t in failed if now - t < 30]
        excluded = [(x, y) for x, y, _ in recent + failed]

        # 消除之前先把锁定的线卷槽看广告解锁
        tried_slots = [(x, y, t) for x, y, t in tried_slots if now - t < 60]
        slots = [b for b in big if b["kind"] == "locked" and
                 not any((b["x"] - x) ** 2 + (b["y"] - y) ** 2 < (100 * scale) ** 2
                         for x, y, _ in tried_slots)]
        if slots and slot_unlocks < args.max_slot_unlock:
            slot = slots[0]
            slot_unlocks += 1
            print("slot %d/%d: 点锁定槽 (%d,%d) 看广告 %.0fs ..." %
                  (slot_unlocks, args.max_slot_unlock,
                   slot["x"], slot["y"], args.revive_wait), flush=True)
            tap(slot["x"], slot["y"], serial)
            ok = watch_ad_return(serial, args.revive_wait, args.revive_timeout)
            tried_slots.append((slot["x"], slot["y"], time.time()))
            print("slot: " + ("已解锁，继续对局" if ok else "未回到对局，停止"), flush=True)
            if not ok:
                break
            time.sleep(args.revive_settle)
            continue

        if not targets:
            print("stop: 没有可用的目标颜色（大线卷锁定或页面已变化）")
            break

        mode = "target"
        cand, reason = pick_by_board(clickable, small, excluded, scale, img)
        if cand is None:
            # 没有目标色：优先清空剩余线卷最少的挡板，释放它露出下层
            if unlocks >= args.max_unlock:
                print("stop: 已尝试 %d 次解放挡板，仍未出现目标线卷" % unlocks)
                break
            top_boards = detect_top_boards(img, small, args.board_min_area)
            cand, reason = pick_unlock(small, targets, excluded, scale, img, top_boards)
            if cand is None:
                print("stop: 没有可操作的线卷，也无法通过点击其他线卷解放挡板")
                break
            mode = "unlock"
            unlocks += 1

        clicks += 1
        if mode == "unlock":
            print("[%d] unlock %s (%d, %d)  释放挡板 %d/%d [%s]" %
                  (clicks, cand["color"], cand["x"], cand["y"],
                   unlocks, args.max_unlock, reason), flush=True)
        else:
            print("[%d] tap %s (%d, %d)  剩余可点 %d [%s]" %
                  (clicks, cand["color"], cand["x"], cand["y"],
                   len(clickable), reason), flush=True)

        if args.dry_run:
            print("dry-run: 未实际点击")
            break

        tap(cand["x"], cand["y"], serial)
        recent.append((cand["x"], cand["y"], time.time()))
        after = wait_stable(serial, args.wait, args.max_wait)
        big2, small2, targets2 = analyze(after)
        if args.targets:
            targets2 = args.targets
        clickable2 = [s for s in small2 if s["color"] in targets2]
        if any((s["x"] - cand["x"]) ** 2 + (s["y"] - cand["y"]) ** 2 < (28 * scale) ** 2
               for s in clickable2):
            print("  ! 点击后线卷仍在，暂时跳过该位置")
            failed.append((cand["x"], cand["y"], time.time()))
        if not targets2:
            print("页面变化：目标颜色消失，下一轮重新识别")
        time.sleep(args.gap)

    print("done: 共点击 %d 次（其中解放挡板 %d 次），耗时 %.1fs，最后结果 -> %s" %
          (clicks, unlocks, time.time() - started, args.output))
    if args.notify:
        notify_phone(args.notify_message, serial, args.notify_script)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", help="直接处理本地图片（调试用）")
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--once", action="store_true", help="只识别一次")
    ap.add_argument("--live", action="store_true", help="实时循环标注")
    ap.add_argument("--auto", action="store_true", help="自动点击直到没有可操作线卷")
    ap.add_argument("--interval", type=float, default=0.8, help="实时模式间隔秒")
    ap.add_argument("--output", default="spool_annotated.png", help="标注结果保存路径")
    ap.add_argument("--targets", nargs="*", choices=list(COLORS),
                    help="手动指定目标颜色，覆盖自动识别")
    ap.add_argument("--max-clicks", type=int, default=200, help="自动模式最大点击次数")
    ap.add_argument("--max-unlock", type=int, default=20,
                    help="没有目标线卷时，最多尝试多少次点击其他线卷来解放挡板")
    ap.add_argument("--max-seconds", type=float, default=600, help="自动模式最长运行秒数")
    ap.add_argument("--wait", type=float, default=0.35, help="点击后最短等待秒数")
    ap.add_argument("--max-wait", type=float, default=1.8, help="点击后最长等待秒数")
    ap.add_argument("--gap", type=float, default=0.15, help="每轮之间的额外间隔秒数")
    ap.add_argument("--recent-seconds", type=float, default=4.0,
                    help="多久内不重复点击同一位置")
    ap.add_argument("--dry-run", action="store_true", help="自动模式只演示第一步，不点击")
    ap.add_argument("--modal-v", type=float, default=150,
                    help="画面平均亮度低于此值视为失败/弹窗")
    ap.add_argument("--no-revive", action="store_true", help="失败时不看广告复活，直接停止")
    ap.add_argument("--max-revive", type=int, default=3, help="自动看广告复活的最大次数")
    ap.add_argument("--max-slot-unlock", type=int, default=4,
                    help="看广告解锁锁定线卷槽的最大次数")
    ap.add_argument("--revive-x", type=float, default=0.50, help="「获得」按钮横向比例")
    ap.add_argument("--revive-y", type=float, default=0.738, help="「获得」按钮纵向比例")
    ap.add_argument("--revive-wait", type=float, default=15, help="看广告等待秒数")
    ap.add_argument("--revive-timeout", type=float, default=30, help="等待回到对局的总超时秒数")
    ap.add_argument("--revive-settle", type=float, default=3.0,
                    help="复活后额外等待秒数，等暂存区收集动画结束")
    ap.add_argument("--security-timeout", type=float, default=300,
                    help="遇到安全验证时等待用户手动处理的超时秒数")
    ap.add_argument("--board-min-area", type=float, default=8000,
                    help="顶层挡板检测的最小封闭区面积（1080 宽量级，过小易把空隙当挡板）")
    ap.add_argument("--notify", dest="notify", action="store_true", default=True,
                    help="自动运行结束后让手机 AutoJS 发出状态栏通知提醒（默认开启）")
    ap.add_argument("--no-notify", dest="notify", action="store_false",
                    help="不发送提醒")
    ap.add_argument("--notify-message", default="线卷三消已完成",
                    help="提醒内容")
    ap.add_argument("--notify-script", default=NOTIFY_SCRIPT,
                    help="写到手机上供 AutoJS 运行的临时脚本路径")
    args = ap.parse_args()

    def step(img):
        big, small, targets = analyze(img)
        if args.targets:
            targets = args.targets
        annotated, clickable = annotate(img, big, small, targets)
        cv2.imwrite(args.output, annotated)
        return annotated, clickable, big, small, targets

    if args.auto:
        try:
            auto_run(args)
        except BaseException:
            if args.notify:
                notify_phone("线卷三消异常中断", args.device, args.notify_script)
            raise
        return

    if args.image:
        img = cv2.imread(args.image)
        if img is None:
            sys.exit("图片读取失败: " + args.image)
        annotated, clickable, big, small, targets = step(img)
        print("big spools:", big)
        print("top-layer small spools:", len(small), small)
        print("targets:", targets, "clickable:", len(clickable), clickable)
        print("saved:", args.output)
        return

    if args.live:
        gui = has_gui()
        if not gui:
            print("提示: 当前 OpenCV 为 headless 构建，--live 每轮保存标注图、不弹窗；"
                  "按 Ctrl+C 退出", flush=True)
        try:
            while True:
                img = grab(args.device)
                annotated, clickable, big, small, targets = step(img)
                if gui:
                    cv2.imshow("spool assist", annotated)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                else:
                    print("已保存 %s  可点击 %d" % (args.output, len(clickable)), flush=True)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            pass
        finally:
            if gui:
                cv2.destroyAllWindows()
        return

    img = grab(args.device)
    annotated, clickable, big, small, targets = step(img)
    print("big spools:", big)
    print("top-layer small spools:", len(small), small)
    print("targets:", targets, "clickable:", len(clickable), clickable)
    print("saved:", args.output)


if __name__ == "__main__":
    main()
