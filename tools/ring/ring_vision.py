#!/usr/bin/env python3
"""环形岛接客辅助 · 视觉识别模块。

抓图 -> 按颜色连通域分离车辆 -> 识别每辆车(颜色/8 方向朝向/中心/可开出/点击点)
-> 识别接驳区已有车颜色 + 助力礼包弹窗 -> 输出标注图 + JSON 摘要。

坐标基于 1080x2400 竖屏，比例化以适配相近分辨率。
大部分识别逻辑与 parking_vision 一致；区域坐标按本游戏重新标定。
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
from common.screen import grab  # noqa: E402

# ---------- 颜色定义（与 parking_vision 一致） ----------
COLORS = {
    "red":    ((0, 10),   (0, 0, 235)),
    "brown":  ((170, 179), (70, 75, 140)),
    "yellow": ((16, 34),  (40, 215, 245)),
    "green":  ((40, 78),  (60, 215, 75)),
    "cyan":   ((80, 98),  (225, 215, 70)),
    "blue":   ((99, 125), (235, 100, 45)),
    "pink":   ((150, 169), (170, 70, 235)),
}
GRAY = "unknown"
CAR_HUE = {"red": 3, "brown": 176, "yellow": 25, "green": 56,
           "cyan": 89, "blue": 112, "pink": 159, "unknown": 0}

# 区域比例（1080x2400 图上重新标定）
BOARD = (0.037, 0.483, 0.963, 0.888)    # 车辆棋盘 x0,y0,x1,y1 (y≈1160~2130)
DOCK  = (0.12, 0.345, 0.98, 0.425)     # 接驳区行 (y≈830~1020, 左边界避开 X2 图标)
GIFT_X_SEARCH = (0.70, 0.19, 0.99, 0.32)  # 助力礼包弹窗右上角 × 搜索区
UNLOCK_ICON = os.path.join(os.path.dirname(__file__), "templates", "unlock_icon.png")
# 播放图标中心相对整枚「解锁」按钮中心的偏移（1080x2400 基准）
UNLOCK_ICON_TO_BUTTON = (36, -49)

# 标注 BGR
DRAW = {
    "red": (60, 60, 235), "brown": (70, 75, 140), "yellow": (40, 215, 245),
    "green": (60, 215, 75), "cyan": (225, 215, 70), "blue": (235, 100, 45),
    "pink": (170, 70, 235), "unknown": (150, 150, 150),
}
DIR_ARROW = {"left": "←", "right": "→", "up": "↑", "down": "↓",
             "up-left": "↖", "up-right": "↗", "down-left": "↙", "down-right": "↘"}

AXES_DEG = (0.0, 90.0, 26.565, 153.435)
TILT_AXES_DEG = (26.565, 153.435)
TILT_TOL_DEG = 8.0
DIAG_DIRS = ("up-left", "up-right", "down-left", "down-right")
DIR_VEC = {
    "right":      (1.0, 0.0),
    "down":       (0.0, 1.0),
    "left":       (-1.0, 0.0),
    "up":         (0.0, -1.0),
    "down-right": (np.cos(np.radians(26.565)), np.sin(np.radians(26.565))),
    "up-left":    (-np.cos(np.radians(26.565)), -np.sin(np.radians(26.565))),
    "down-left":  (-np.cos(np.radians(153.435)), np.sin(np.radians(153.435))),
    "up-right":   (np.cos(np.radians(153.435)), -np.sin(np.radians(153.435))),
}
DIR_PRIORITY = {"up": 0, "up-left": 1, "up-right": 1, "left": 2, "right": 2,
                "down": 3, "down-left": 4, "down-right": 4}


def hue_name(h, s=255, v=255):
    h = int(h) % 180
    if v < 90 or s < 60:
        return GRAY
    if h >= 168 or h <= 10:
        return "brown" if (v < 195 and s < 160) else "red"
    if 16 <= h <= 34:
        return "yellow"
    if 40 <= h <= 78:
        return "green"
    if 80 <= h <= 98:
        return "cyan"
    if 99 <= h <= 125:
        return "blue"
    if 150 <= h <= 167:
        return "pink"
    return None


def _region_px(img, box):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = box
    return (int(x0*w), int(y0*h), int(x1*w), int(y1*h))


def detect_cars(img):
    """逐颜色做连通域：同色车之间有深色描边可分离，比峰值/分水岭更稳。"""
    x0, y0, x1, y1 = _region_px(img, BOARD)
    H = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    hue, sat, val = H[:, :, 0], H[:, :, 1], H[:, :, 2]

    color_masks = {}
    for name, ((lo, hi), _bgr) in COLORS.items():
        if lo < hi:
            m = ((hue >= lo) & (hue <= hi) & (sat > 85) & (val > 85))
        else:
            m = (((hue >= lo) | (hue <= hi)) & (sat > 85) & (val > 85))
        color_masks[name] = m
    color_masks[GRAY] = (sat < 52) & (val > 90) & (val < 205)

    cars = []
    seen = set()
    for name, m in color_masks.items():
        mm = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE,
                              cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)))
        n, lab, stats, cents = cv2.connectedComponentsWithStats(mm)
        for i in range(1, n):
            xx, yy, ww, hh, area = stats[i]
            if area < 2200 or ww < 38 or hh < 38:
                continue
            if ww > 200 or hh > 210 or area > 42000:
                continue
            cx, cy = cents[i]
            gx, gy = int(cx) + x0, int(cy) + y0
            key = (gx // 20, gy // 20)
            if key in seen:
                continue
            seen.add(key)
            obb = None
            ys, xs = np.where(lab == i)
            if xs.size >= 200:
                (rcx, rcy), (rw, rh), rang = cv2.minAreaRect(
                    np.column_stack([xs, ys]).astype(np.float32))
                if rw >= rh:
                    L, W, la = rw, rh, rang % 180
                else:
                    L, W, la = rh, rw, (rang + 90) % 180
                obb = {"cx": float(rcx) + x0, "cy": float(rcy) + y0,
                       "L": float(L), "W": float(W), "angle": float(la)}
            cars.append({
                "x": gx, "y": gy,
                "bx": xx + x0, "by": yy + y0, "bw": ww, "bh": hh,
                "color": name,
                "area": int(area),
                "obb": obb,
            })
    return cars


def _axis_dir(angle_deg, sign):
    th = np.radians(angle_deg)
    ux, uy = np.cos(th) * sign, np.sin(th) * sign
    dx, dy = ux, uy
    ax, ay = abs(dx), abs(dy)
    if ax >= ay:
        name = "right" if dx > 0 else "left"
    else:
        name = "down" if dy > 0 else "up"
    dev = min(abs(angle_deg - 0), abs(angle_deg - 90), abs(angle_deg - 180))
    if dev > 10:
        v = "right" if dx > 0 else "left"
        h = "down" if dy > 0 else "up"
        name = h + "-" + v
        if name not in DIR_VEC:
            name = v if ax >= ay else h
    return name, (float(dx), float(dy))


def detect_arrows(img):
    """全图检测白色箭头，返回中心、8 方向名、单位向量、主轴角度。"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    white = ((hsv[:, :, 2] > 235) & (hsv[:, :, 1] < 50)).astype(np.uint8)
    x0, y0, x1, y1 = _region_px(img, BOARD)
    m = cv2.morphologyEx(white[y0:y1, x0:x1], cv2.MORPH_CLOSE,
                         np.ones((3, 3), np.uint8))
    n, lab, stats, cents = cv2.connectedComponentsWithStats(m)
    arrows = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if not (200 < area < 2500 and 15 < w < 110 and 10 < h < 110):
            continue
        ys, xs = np.where(lab == i)
        pts = np.column_stack([xs, ys]).astype(np.float32)
        (rcx, rcy), (rw, rh), rang = cv2.minAreaRect(pts)
        la = (rang if rw >= rh else rang + 90) % 180
        th = np.radians(la)
        X = xs * np.cos(-th) - ys * np.sin(-th)
        Y = xs * np.sin(-th) + ys * np.cos(-th)
        mid = (X.min() + X.max()) / 2.0
        lo = Y[X < mid]
        hi = Y[X >= mid]
        span_lo = float(np.ptp(lo)) if lo.size else 0.0
        span_hi = float(np.ptp(hi)) if hi.size else 0.0
        sign = 1 if span_hi > span_lo else -1
        name, vec = _axis_dir(la, sign)
        arrows.append({"x": float(cents[i][0]) + x0, "y": float(cents[i][1]) + y0,
                       "dir": name, "vec": vec, "axis": round(la, 2),
                       "w": int(w), "h": int(h)})
    return arrows


def _angle_dist(a, b):
    d = abs((float(a) - float(b)) % 180.0)
    return min(d, 180.0 - d)


def tilt_info(arrows, tol=TILT_TOL_DEG):
    tilted = [a for a in arrows
              if a.get("dir") in DIAG_DIRS
              and any(_angle_dist(a.get("axis", 0.0), t) <= tol
                      for t in TILT_AXES_DEG)]
    return {
        "tilted": bool(tilted),
        "count": len(tilted),
        "axes": sorted({round(float(a["axis"]), 1) for a in tilted}),
        "dirs": sorted({a["dir"] for a in tilted}),
    }


def detect_direction(car, img, arrows=None):
    """用箭头块中心归属到车身，返回朝向。优先用全图箭头检测结果。"""
    if arrows:
        bx0, by0 = car["bx"], car["by"]
        bx1, by1 = bx0 + car["bw"], by0 + car["bh"]
        inside = [a for a in arrows
                  if bx0-18 <= a["x"] <= bx1+18 and by0-18 <= a["y"] <= by1+18]
        if inside:
            inside.sort(key=lambda a: (a["x"]-(bx0+bx1)/2)**2 + (a["y"]-(by0+by1)/2)**2)
            a = inside[0]
            car["vec"] = a.get("vec", DIR_VEC.get(a["dir"], (0.0, -1.0)))
            car["axis"] = a.get("axis", 0.0)
            return a["dir"], 0.0
    bx, by, bw, bh = car["bx"], car["by"], car["bw"], car["bh"]
    roi = img[by:by+bh, bx:bx+bw]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    white = ((hsv[:, :, 1] < 60) & (hsv[:, :, 2] > 235)).astype(np.uint8)
    if bw >= bh:
        proj = white.sum(axis=0); mid = bw/2.0
        ws = proj[2:bw-2]; xs = np.arange(2, bw-2)
        c = float((xs*ws).sum()/ws.sum()) if ws.sum() else mid
        d = "right" if c >= mid else "left"
    else:
        proj = white.sum(axis=1); mid = bh/2.0
        ws = proj[2:bh-2]; ys = np.arange(2, bh-2)
        c = float((ys*ws).sum()/ws.sum()) if ws.sum() else mid
        d = "down" if c >= mid else "up"
    car["vec"] = DIR_VEC[d]
    car["axis"] = 0.0 if d in ("left", "right") else 90.0
    return d, round(c, 1)


def _obb_of(car):
    o = car.get("obb")
    if o:
        return o["cx"], o["cy"], o["L"], o["W"], o["angle"]
    return (car["bx"] + car["bw"]/2.0, car["by"] + car["bh"]/2.0,
            max(car["bw"], car["bh"]), min(car["bw"], car["bh"]), 0.0)


def pick_tap_point(car, hsv_img):
    """在车身内选一个落在实心车漆上的可点击点（支持斜向车）。"""
    cx, cy = int(car["x"]), int(car["y"])
    bx, by, bw, bh = car["bx"], car["by"], car["bw"], car["bh"]
    my_hue = CAR_HUE.get(car["color"], 0)
    ux, uy = car.get("vec", (0.0, -1.0))
    short = max(10, min(bw, bh) // 5)
    cand = [(cx, cy)]
    for k in (0.5, 1.0):
        cand.append((int(cx - ux*short*k), int(cy - uy*short*k)))
        cand.append((int(cx + uy*short*k), int(cy + ux*short*k)))
        cand.append((int(cx - uy*short*k), int(cy - ux*short*k)))
    h, w = hsv_img.shape[:2]
    for x, y in cand:
        if not (0 <= x < w and 0 <= y < h):
            continue
        if not (bx <= x <= bx+bw and by <= y <= by+bh):
            continue
        hh, ss, vv = hsv_img[y, x]
        dh = min(abs(int(hh)-my_hue), 180-abs(int(hh)-my_hue))
        if ss > 70 and vv > 130 and dh <= 22:
            return x, y
    return cx, cy


def _can_exit_geom(car, cars, docked):
    """几何法：沿方向向量用 OBB 投影判断占用块是否挡路。"""
    vec = car.get("vec", DIR_VEC.get(car["dir"], (0.0, -1.0)))
    ux, uy = float(vec[0]), float(vec[1])
    px, py = -uy, ux
    ccx, ccy, cL, cW, _ = _obb_of(car)
    start_x = ccx + ux * (cL/2.0 - 4)
    start_y = ccy + uy * (cL/2.0 - 4)
    lane_half = cW/2.0 + 4
    for o in [o for o in cars if o is not car] + list(docked or []):
        ox, oy, oL, oW, _ = _obb_of(o)
        rx, ry = ox - start_x, oy - start_y
        along = rx*ux + ry*uy
        across = abs(rx*px + ry*py)
        if along < -oW/2.0:
            continue
        if along - oL/2.0 < 2600 and across < lane_half + oW/2.0:
            if along <= oL/2.0 + 6 and across < 3:
                continue
            return False
    return True


def _can_exit_pixels(img, car):
    """像素法：沿方向向量在棋盘内采样，检测前方是否有别的车漆/灰障碍。"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    x0, y0, x1, y1 = _region_px(img, BOARD)
    cx, cy = car["x"], car["y"]
    ux, uy = car.get("vec", DIR_VEC.get(car["dir"], (0.0, -1.0)))
    my_hue = CAR_HUE.get(car["color"], 0)
    step = 3
    t = 10
    while t < 210:
        x, y = int(cx+ux*t), int(cy+uy*t)
        if not (x0 <= x < x1 and y0 <= y < y1):
            return True
        h, s, v = hsv[y, x]
        dh = min(abs(int(h)-my_hue), 180-abs(int(h)-my_hue))
        if not (s > 55 and dh <= 22):
            break
        t += step
    run = 0
    while t < 430:
        x, y = int(cx+ux*t), int(cy+uy*t)
        if not (x0 <= x < x1 and y0 <= y < y1):
            return True
        h, s, v = hsv[y, x]
        gray_block = (s < 52 and 70 < v < 215)
        dh = min(abs(int(h)-my_hue), 180-abs(int(h)-my_hue))
        other_car = (s > 70 and v > 70 and dh > 20)
        run = run + 1 if (gray_block or other_car) else 0
        if run >= 10:
            return False
        t += step
    return True


def can_exit(car, cars, img_shape, docked=None, img=None):
    """可开出判定 = 几何法 AND 像素法（保守）。"""
    if img is None:
        return _can_exit_geom(car, cars, docked)
    return _can_exit_geom(car, cars, docked) and _can_exit_pixels(img, car)


def detect_unlock_slots(img, template_path=None, threshold=0.8):
    """在接驳区匹配「看广告」播放图标，返回整枚解锁按钮的可点击中心。

    旧版用两枚按钮的大模板 unlock.png，当前 UI 下峰值只有 ~0.60，阈值 0.65
    会全部漏掉；播放图标是独立 UI 元素，峰值 0.98+，空槽位只有 ~0.16。
    """
    if template_path is None:
        template_path = UNLOCK_ICON
    tpl = cv2.imread(template_path)
    if tpl is None:
        return []
    x0, y0, x1, y1 = _region_px(img, DOCK)
    search = img[y0:y1, x0:x1]
    if tpl.shape[0] > search.shape[0] or tpl.shape[1] > search.shape[1]:
        return []
    res = cv2.matchTemplate(search, tpl, cv2.TM_CCOEFF_NORMED)
    sx, sy = img.shape[1] / 1080.0, img.shape[0] / 2400.0
    dx = int(round(UNLOCK_ICON_TO_BUTTON[0] * sx))
    dy = int(round(UNLOCK_ICON_TO_BUTTON[1] * sy))
    min_dist = max(30, int(round(70 * sx)))
    pts = []
    for y, x in zip(*np.where(res >= threshold)):
        px = int(x + tpl.shape[1] // 2 + x0) + dx
        py = int(y + tpl.shape[0] // 2 + y0) + dy
        if all((px - a) ** 2 + (py - b) ** 2 > min_dist ** 2 for a, b in pts):
            pts.append((px, py))
    return pts


def detect_docked_cars(img):
    """检测停在接驳位上的车，返回 bbox + 颜色列表。"""
    x0, y0, x1, y1 = _region_px(img, DOCK)
    roi = img[y0:y1, x0:x1]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    sat, val = hsv[:, :, 1], hsv[:, :, 2]
    m = ((sat > 90) & (val > 85)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE,
                         cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)))
    n, lab, stats, cents = cv2.connectedComponentsWithStats(m)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < 1500 or w < 35 or h < 35 or w > 260 or h > 260:
            continue
        cx_abs = int(cents[i][0]) + x0
        if cx_abs < 160:      # 排除左侧 X2 倍数图标
            continue
        # 取连通域中位色判定颜色
        ys, xs = np.where(lab == i)
        if xs.size < 100:
            continue
        pixels = hsv[ys, xs]
        good = (pixels[:, 1] > 80) & (pixels[:, 2] > 80)
        if good.sum() < 50:
            continue
        color = hue_name(float(np.median(pixels[good, 0])),
                         float(np.median(pixels[good, 1])),
                         float(np.median(pixels[good, 2])))
        if color is None:
            color = "unknown"
        out.append({"bx": x + x0, "by": y + y0, "bw": w, "bh": h,
                    "x": int(cents[i][0]) + x0, "y": int(cents[i][1]) + y0,
                    "color": color, "area": int(area)})
    return out


def detect_dock_colors(img):
    """返回接驳区已有车辆的颜色集合（本游戏选车规则的核心依据）。"""
    cars = detect_docked_cars(img)
    colors = sorted(set(c["color"] for c in cars if c["color"] != GRAY))
    return {"colors": colors, "cars": cars}


def detect_empty_slots(img, template_path=None, threshold=0.72):
    """模板匹配接驳行里「空 P 位」数量，返回中心坐标列表。"""
    if template_path is None:
        template_path = os.path.join(os.path.dirname(__file__), "templates", "p_slot.png")
    tpl = cv2.imread(template_path)
    if tpl is None:
        return []
    x0, y0, x1, y1 = _region_px(img, DOCK)
    search = img[y0:y1, x0:x1]
    if tpl.shape[0] > search.shape[0] or tpl.shape[1] > search.shape[1]:
        return []
    res = cv2.matchTemplate(search, tpl, cv2.TM_CCOEFF_NORMED)
    locs = np.where(res >= threshold)
    pts = []
    for y, x in zip(*locs):
        px = int(x + tpl.shape[1] / 2 + x0)
        py = int(y + tpl.shape[0] / 2 + y0)
        if all((px-a)**2 + (py-b)**2 > 40**2 for a, b in pts):
            pts.append((px, py))
    return pts


def detect_end_dialog(img, template_path=None, threshold=0.75):
    """检测「挑战失败 / 挑战成功」结算弹窗的蓝色横幅，返回 True。"""
    if template_path is None:
        template_path = os.path.join(os.path.dirname(__file__), "templates", "fail_banner.png")
    tpl = cv2.imread(template_path)
    if tpl is None:
        return False
    res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
    return float(res.max()) >= threshold


def detect_unlock_confirm(img, template_path=None, threshold=0.72):
    """检测点「解锁」位后弹出的确认框中的蓝色「使用」按钮，返回中心坐标。

    该按钮是看广告解锁流程的必要一步；同时用于把「解锁确认框」与
    「助力礼包」弹窗区分开——两者右上角 × 的样式/位置几乎相同。
    """
    if template_path is None:
        template_path = os.path.join(os.path.dirname(__file__), "templates", "use_button.png")
    tpl = cv2.imread(template_path)
    if tpl is None:
        return None
    res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
    _, maxv, _, maxloc = cv2.minMaxLoc(res)
    if maxv < threshold:
        return None
    return (int(maxloc[0] + tpl.shape[1] / 2),
            int(maxloc[1] + tpl.shape[0] / 2))


def detect_revive_dialog(img, template_path=None, threshold=0.80):
    """检测「复活」弹窗（紫色标题横幅）。用户定稿：命中立即结束，不做任何操作。

    复活弹窗的 × 与助力礼包 × 几乎相同（模板匹配均 0.98+），极易误判成助力礼包
    而被点 × 关掉，必须用标题横幅单独识别并优先拦截。
    """
    if template_path is None:
        template_path = os.path.join(os.path.dirname(__file__), "templates", "revive_banner.png")
    tpl = cv2.imread(template_path)
    if tpl is None:
        return False
    res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
    return float(res.max()) >= threshold


def detect_gift_popup(img, template_path=None, threshold=0.72):
    """检测「助力礼包」弹窗，返回右上角 × 的中心坐标；非弹窗返回 None。

    快速判据：弹窗遮罩使全图灰度均值从 ~159 降到 ~106；再用 × 模板精确匹配。
    关键：先排除「解锁确认框」与「复活弹窗」——它们的 × 与助力礼包 ×
    几乎一模一样，绝不能当助力礼包关掉。
    """
    if detect_unlock_confirm(img) is not None or detect_revive_dialog(img):
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if float(gray.mean()) > 140:
        return None
    if template_path is None:
        template_path = os.path.join(os.path.dirname(__file__), "templates", "gift_x.png")
    tpl = cv2.imread(template_path)
    if tpl is None:
        # 模板缺失时退化为「暗屏即弹窗」+ 固定相对坐标
        h, w = img.shape[:2]
        return (int(w * 0.855), int(h * 0.238))
    x0, y0, x1, y1 = _region_px(img, GIFT_X_SEARCH)
    search = img[y0:y1, x0:x1]
    if tpl.shape[0] > search.shape[0] or tpl.shape[1] > search.shape[1]:
        return None
    res = cv2.matchTemplate(search, tpl, cv2.TM_CCOEFF_NORMED)
    _, maxv, _, maxloc = cv2.minMaxLoc(res)
    if maxv < threshold:
        return None
    return (int(x0 + maxloc[0] + tpl.shape[1] / 2),
            int(y0 + maxloc[1] + tpl.shape[0] / 2))


def analyze(img):
    cars = detect_cars(img)
    arrows = detect_arrows(img)
    for c in cars:
        d, off = detect_direction(c, img, arrows)
        c["dir"] = d
        c["arrow_off"] = off
    docked = detect_dock_colors(img)["cars"]
    hsv_full = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    for c in cars:
        c["can_exit"] = can_exit(c, cars, img.shape, docked, img)
        c["tap"] = pick_tap_point(c, hsv_full)
    return {"cars": cars, "dock": detect_dock_colors(img),
            "docked": docked, "empty_slots": detect_empty_slots(img),
            "gift_x": detect_gift_popup(img), "tilt": tilt_info(arrows)}


def annotate(img, result, pick=None):
    vis = img.copy()
    for c in result["cars"]:
        col = DRAW.get(c["color"], (150, 150, 150))
        cv2.rectangle(vis, (c["bx"], c["by"]), (c["bx"]+c["bw"], c["by"]+c["bh"]), col, 2)
        label = DIR_ARROW.get(c["dir"], "?")
        cv2.putText(vis, label, (c["x"]-6, c["y"]+6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        vec = c.get("vec")
        if vec:
            ex = int(c["x"] + vec[0]*22); ey = int(c["y"] + vec[1]*22)
            cv2.line(vis, (int(c["x"]), int(c["y"])), (ex, ey), (255, 0, 255), 2)
            cv2.circle(vis, (ex, ey), 3, (255, 0, 255), -1)
    # 接驳区已有车颜色：大号文字 + 圈
    for d in result["dock"]["cars"]:
        col = DRAW.get(d["color"], (150, 150, 150))
        cv2.circle(vis, (d["x"], d["y"]), 22, col, 3)
        cv2.putText(vis, d["color"][:3].upper(), (d["x"]-22, d["y"]-28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)
    if pick:
        picks = pick if isinstance(pick, (list, tuple)) else [pick]
        for i, p in enumerate(picks, 1):
            cv2.rectangle(vis, (p["bx"]-4, p["by"]-4),
                          (p["bx"]+p["bw"]+4, p["by"]+p["bh"]+4), (0, 255, 0), 4)
            cv2.putText(vis, str(i), (p["bx"]-4, max(0, p["by"]-10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    return vis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="兼容 quick.sh 入口标记")
    ap.add_argument("--image")
    ap.add_argument("--device")
    ap.add_argument("--output", default="outputs/ring_annotated.png")
    args = ap.parse_args()

    if args.image:
        img = cv2.imread(args.image)
    else:
        img = grab(args.device)
    if img is None:
        print("抓图失败"); return
    res = analyze(img)
    print(json.dumps({
        "cars": len(res["cars"]),
        "colors": {c: sum(1 for x in res["cars"] if x["color"] == c)
                   for c in set(x["color"] for x in res["cars"])},
        "exitable": sum(1 for c in res["cars"] if c["can_exit"]),
        "dock_colors": res["dock"]["colors"],
        "docked_cars": len(res["dock"]["cars"]),
        "empty_slots": len(res["empty_slots"]),
        "unlock_slots": len(detect_unlock_slots(img)),
        "gift_x": res["gift_x"],
        "tilt": res["tilt"],
    }, ensure_ascii=False))
    vis = annotate(img, res)
    cv2.imwrite(args.output, vis)
    print("saved", args.output)


if __name__ == "__main__":
    main()
