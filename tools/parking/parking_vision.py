#!/usr/bin/env python3
"""停车场接客辅助 · 视觉识别模块。

抓图 -> 按颜色连通域分离车辆 -> 识别每辆车(颜色/8 方向朝向/中心/可开出/点击点)
-> 识别队首乘客颜色与接驳位状态 -> 判断是否倾斜关卡 -> 输出标注图 + JSON 摘要。

坐标基于 1080x2400 竖屏，比例化以适配相近分辨率。
"""
import argparse
import json
import os
import subprocess

import cv2
import numpy as np

# ---------- 颜色定义 ----------
# HSV hue 范围 (OpenCV 0~179)。停车场车常见色：红/黄/绿/青/蓝/粉/深红(brown)/灰(?)
COLORS = {
    "red":    ((0, 10),   (0, 0, 235)),
    "brown":  ((170, 179), (70, 75, 140)),   # 深红/酒红车
    "yellow": ((16, 34),  (40, 215, 245)),
    "green":  ((40, 78),  (60, 215, 75)),
    "cyan":   ((80, 98),  (225, 215, 70)),
    "blue":   ((99, 125), (235, 100, 45)),
    "pink":   ((150, 169), (170, 70, 235)),
}
GRAY = "unknown"  # 灰色?车
# 各车色的代表 hue（像素射线法用），与 COLORS 范围中心对应
CAR_HUE = {"red": 3, "brown": 176, "yellow": 25, "green": 56,
           "cyan": 89, "blue": 112, "pink": 159, "unknown": 0}

# 区域比例
BOARD = (0.037, 0.410, 0.963, 0.763)   # 棋盘 x0,y0,x1,y1
QUEUE = (0.31, 0.2265, 0.778, 0.229)   # 顶部乘客头部采样行（排除右侧竖列球区）
QUEUE_Y = None  # 运行时按段数自动定位，见 detect_queue
QUEUE_RIGHT = (0.74, 0.145, 0.83, 0.265)  # 右侧竖排球（备用/队尾?）

# 标注 BGR
DRAW = {
    "red": (60, 60, 235), "brown": (70, 75, 140), "yellow": (40, 215, 245),
    "green": (60, 215, 75), "cyan": (225, 215, 70), "blue": (235, 100, 45),
    "pink": (170, 70, 235), "unknown": (150, 150, 150),
}
DIR_ARROW = {"left": "←", "right": "→", "up": "↑", "down": "↓",
             "up-left": "↖", "up-right": "↗", "down-left": "↙", "down-right": "↘"}

# 屏幕上的 4 条标准轴向（度）。等距投影下世界 8 方向映射到这 4 轴 × 2 朝向：
#   水平 0° / 垂直 90° / 斜 26.565°(arctan 1/2) / 斜 153.435°
# 关卡按倾角分批出现（某关全是正交轴，某关全是斜轴），每关固定一种。
AXES_DEG = (0.0, 90.0, 26.565, 153.435)
# 斜关卡判定：世界 45° 经 2:1 等距投影后落在 26.565° / 153.435°。
# 旧正交关实测轴角约 10°/75°/168°，与这两个值相差 >=12°，容差 8° 不会误报。
TILT_AXES_DEG = (26.565, 153.435)
TILT_TOL_DEG = 8.0
DIAG_DIRS = ("up-left", "up-right", "down-left", "down-right")
# 8 方向名 -> 单位向量(屏幕坐标, y向下) + 用于排序的"朝上"优先级
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
# 排序优先级：越朝上越优先（车开向顶部接驳区）
DIR_PRIORITY = {"up": 0, "up-left": 1, "up-right": 1, "left": 2, "right": 2,
                "down": 3, "down-left": 4, "down-right": 4}


def grab(serial=None):
    cmd = ["adb"] + (["-s", serial] if serial else []) + ["exec-out", "screencap", "-p"]
    data = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
    arr = np.frombuffer(data, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def hue_name(h, s=255, v=255):
    h = int(h) % 180
    if v < 90 or s < 60:
        return GRAY
    # 红色跨 0/179：高亮高饱和=红，暗红(酒红)才归 brown
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


def region(img, box):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = box
    return img[int(y0*h):int(y1*h), int(x0*w):int(x1*w)]


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
    # 灰色?车：低饱和、中高亮（深灰车身）
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
            # 过滤过宽/过高的误检（相邻车粘连或接驳区）
            if ww > 200 or hh > 210 or area > 42000:
                continue
            cx, cy = cents[i]
            gx, gy = int(cx) + x0, int(cy) + y0
            # 跨颜色去重（同一车可能被两个色mask都捕获）
            key = (gx // 20, gy // 20)
            if key in seen:
                continue
            seen.add(key)
            # 车身 OBB：用连通域原始像素做 minAreaRect，拿到真实长轴角度和长宽。
            # 轴对齐 bbox(ww,hh) 在斜车上会膨胀，不能直接用来判方向/算射线走廊。
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
    """把「主轴角度(0~180) + 正反符号」映射到 8 方向名和屏幕单位向量。

    sign=+1 表示沿角度正向(cos,sin)，=-1 表示反向。图像 y 向下。
    """
    # 用主轴方向向量判定落在哪条轴
    th = np.radians(angle_deg)
    ux, uy = np.cos(th) * sign, np.sin(th) * sign
    dx, dy = ux, uy
    ax, ay = abs(dx), abs(dy)
    if ax >= ay:
        name = "right" if dx > 0 else "left"
    else:
        name = "down" if dy > 0 else "up"
    # 斜向：角度偏离水平/垂直超过 ~10° 时，用组合名
    dev = min(abs(angle_deg - 0), abs(angle_deg - 90), abs(angle_deg - 180))
    if dev > 10:
        v = "right" if dx > 0 else "left"
        h = "down" if dy > 0 else "up"
        name = h + "-" + v          # 统一「上下-左右」，如 down-right / up-left
        if name not in DIR_VEC:
            name = v if ax >= ay else h
    return name, (float(dx), float(dy))


def detect_arrows(img):
    """全图检测白色箭头，返回中心、8 方向名、单位向量、主轴角度。

    箭头是车身上唯一的纯白实心块（灰「?」车没有，天然排除）。大小/颜色固定、
    仅朝向不同。判向分两步，与箭头在车身上的位置和 bbox 宽高比无关：
      1) minAreaRect 取主轴角度 -> 量化到 4 条标准轴之一；
      2) 把点旋转到主轴水平，比较两端横向跨度 -> 三角头(宽)端为箭头指向。
    这样即使棋盘倾斜 26.6°（45° 经 2:1 等距投影）也能正确判 8 方向。
    """
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
        # 长轴角度归一到 [0,180)
        la = (rang if rw >= rh else rang + 90) % 180
        # 旋转到主轴水平，比较两端横向(垂直轴)跨度，三角头端更宽
        th = np.radians(la)
        X = xs * np.cos(-th) - ys * np.sin(-th)
        Y = xs * np.sin(-th) + ys * np.cos(-th)
        mid = (X.min() + X.max()) / 2.0
        lo = Y[X < mid]
        hi = Y[X >= mid]
        span_lo = float(np.ptp(lo)) if lo.size else 0.0
        span_hi = float(np.ptp(hi)) if hi.size else 0.0
        sign = 1 if span_hi > span_lo else -1   # 尖端在 +主轴 方向
        name, vec = _axis_dir(la, sign)
        arrows.append({"x": float(cents[i][0]) + x0, "y": float(cents[i][1]) + y0,
                       "dir": name, "vec": vec, "axis": round(la, 2),
                       "w": int(w), "h": int(h)})
    return arrows


def _angle_dist(a, b):
    """主轴角(0~180 等价)的最小夹角。"""
    d = abs((float(a) - float(b)) % 180.0)
    return min(d, 180.0 - d)


def tilt_info(arrows, tol=TILT_TOL_DEG):
    """判断当前关卡是否为倾斜（8 方向）关卡。

    只把「方向名为斜向」且「主轴角贴近等距投影标准斜轴」的箭头算进来，
    避免旧正交关里 15°/165° 这类轻微偏转箭头被误判成斜向。
    """
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
        # 找落在车 bbox 内的箭头（允许少量外扩）
        inside = [a for a in arrows
                  if bx0-18 <= a["x"] <= bx1+18 and by0-18 <= a["y"] <= by1+18]
        if inside:
            # 取最近的一个
            inside.sort(key=lambda a: (a["x"]-(bx0+bx1)/2)**2 + (a["y"]-(by0+by1)/2)**2)
            a = inside[0]
            car["vec"] = a.get("vec", DIR_VEC.get(a["dir"], (0.0, -1.0)))
            car["axis"] = a.get("axis", 0.0)
            return a["dir"], 0.0
    # 退化：车身 bbox 内白色质心（旧法，仅在箭头块漏检时用）
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


def detect_queue(img):
    """识别顶部乘客队列：在头部上缘窄条按颜色段切分，逐段取颜色。"""
    qx0, qy0, qx1, qy1 = _region_px(img, QUEUE)
    hsv_full = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # 逐行尝试：把彩色像素切成段，只留宽度像"一个头"(14~48px)的段，
    # 选合格段最多的行，避免右侧竖列球/描边干扰
    def head_segs(valid):
        xs = np.where(valid)[0]
        if xs.size == 0:
            return []
        segs = []
        s = int(xs[0]); prev = int(xs[0])
        for xv in xs[1:]:
            xv = int(xv)
            if xv - prev > 3:
                segs.append((s, prev)); s = xv
            prev = xv
        segs.append((s, prev))
        return [(a, b) for a, b in segs if 14 <= (b - a + 1) <= 48]

    best = None
    for yy in range(qy0, qy1):
        row = hsv_full[yy, qx0:qx1]
        valid = (row[:, 1] > 85) & (row[:, 2] > 85)
        segs = head_segs(valid)
        if best is None or len(segs) > best[0]:
            best = (len(segs), yy, valid, segs)
    if best is None:
        return {"seq": [], "colors": [], "head": None, "head_side": "left"}
    _, yy, valid, segs = best
    if not segs:
        return {"seq": [], "colors": [], "head": None, "head_side": "left"}

    seq = []
    for a, b in segs:
        cx = (a + b) // 2 + qx0
        # 在头部中心稍下方取一列像素的中位色（避开描边）
        patch = hsv_full[max(0, yy-2):yy+6, max(0, cx-3):cx+4]
        pm = (patch[:, :, 1] > 80) & (patch[:, :, 2] > 80)
        if pm.sum() < 3:
            continue
        hs, ss, vs = (float(np.median(patch[:, :, i][pm])) for i in range(3))
        color = hue_name(hs, ss, vs)
        if color:
            seq.append({"x": cx, "y": yy, "color": color})
    colors = [s["color"] for s in seq]
    return {"seq": seq, "colors": colors, "head": None, "head_side": "left"}


def _obb_of(car):
    """取车的 OBB(cx,cy,L,W,angle)。缺失时退回轴对齐 bbox 估算。"""
    o = car.get("obb")
    if o:
        return o["cx"], o["cy"], o["L"], o["W"], o["angle"]
    return (car["bx"] + car["bw"]/2.0, car["by"] + car["bh"]/2.0,
            max(car["bw"], car["bh"]), min(car["bw"], car["bh"]), 0.0)


def pick_tap_point(car, hsv_img):
    """在车身内选一个落在实心车漆上的可点击点（支持斜向车）。

    车中心通常就是车漆；正交车有时中心落在下半车窗，故准备多个候选：
    中心 -> 沿行进反方向小偏移 -> 垂直方向偏移。选第一个 HSV 匹配本车色的点。
    """
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
        if ss > 70 and vv > 130 and dh <= 22:   # 实心车漆
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
    """像素法：沿方向向量在棋盘内采样，检测前方是否有别的车漆/灰障碍。

    从车中心先走完本车颜色，再向前扫：连续出现异色车漆或灰车块即判被挡；
    走出棋盘边界即判可开出。能发现未被识别的遮挡车，弥补几何法依赖检测的短板。
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    x0, y0, x1, y1 = _region_px(img, BOARD)
    cx, cy = car["x"], car["y"]
    ux, uy = car.get("vec", DIR_VEC.get(car["dir"], (0.0, -1.0)))
    my_hue = CAR_HUE.get(car["color"], 0)
    step = 3
    # 跳过本车：走到脱离本车颜色为止
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
    # 向前扫占用像素
    run = 0
    while t < 430:
        x, y = int(cx+ux*t), int(cy+uy*t)
        if not (x0 <= x < x1 and y0 <= y < y1):
            return True                       # 出棋盘 => 可开出
        h, s, v = hsv[y, x]
        gray_block = (s < 52 and 70 < v < 215)
        dh = min(abs(int(h)-my_hue), 180-abs(int(h)-my_hue))
        other_car = (s > 70 and v > 70 and dh > 20)
        run = run + 1 if (gray_block or other_car) else 0
        if run >= 10:                          # 连续 ~30px 占用 => 挡住
            return False
        t += step
    return True


def can_exit(car, cars, img_shape, docked=None, img=None):
    """可开出判定 = 几何法 AND 像素法（支持 8 方向）。

    两法取交集：几何法依赖车辆检测（可能漏检遮挡车），像素法直接看画面（可能
    误判车身装饰/棋盘外深灰区）。交集偏保守——宁可漏掉一两辆可开车，也不把
    被挡的车判成可开出导致反复点击卡死（用户核心痛点）。
    """
    if img is None:
        return _can_exit_geom(car, cars, docked)
    return _can_exit_geom(car, cars, docked) and _can_exit_pixels(img, car)


def detect_unlock_slots(img, template_path=None, threshold=0.72):
    """模板匹配接驳行的「解锁」位，返回可点击中心坐标列表。"""
    if template_path is None:
        template_path = os.path.join(os.path.dirname(__file__), "templates", "unlock.png")
    tpl = cv2.imread(template_path)
    if tpl is None:
        return []
    # 只在接驳行区域搜索
    x0, y0, x1, y1 = _region_px(img, (0.12, 0.29, 0.99, 0.37))
    search = img[y0:y1, x0:x1]
    if tpl.shape[0] > search.shape[0] or tpl.shape[1] > search.shape[1]:
        return []
    res = cv2.matchTemplate(search, tpl, cv2.TM_CCOEFF_NORMED)
    locs = np.where(res >= threshold)
    pts = []
    for y, x in zip(*locs):
        px, py = int(x + tpl.shape[1]//2 + x0), int(y + tpl.shape[0]//2 + y0)
        # 非极大抑制
        if all((px-a)**2 + (py-b)**2 > 60**2 for a, b in pts):
            pts.append((px, py))
    return pts


def detect_docked_cars(img):
    """检测停在接驳位上的车（会挡住 up 方向开出），返回 bbox 列表。"""
    x0, y0, x1, y1 = _region_px(img, (0.10, 0.285, 1.0, 0.375))
    roi = img[y0:y1, x0:x1]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    sat, val = hsv[:, :, 1], hsv[:, :, 2]
    # 彩色车身（排除浅灰 P 位底、白虚线）
    m = ((sat > 90) & (val > 85)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE,
                         cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)))
    n, lab, stats, cents = cv2.connectedComponentsWithStats(m)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < 1800 or w < 40 or h < 40 or w > 260 or h > 260:
            continue
        out.append({"bx": x + x0, "by": y + y0, "bw": w, "bh": h})
    return out


def detect_empty_slots(img, template_path=None, threshold=0.72):
    """模板匹配接驳行里「空 P 位」数量，返回中心坐标列表。"""
    if template_path is None:
        template_path = os.path.join(os.path.dirname(__file__), "templates", "p_slot.png")
    tpl = cv2.imread(template_path)
    if tpl is None:
        return []
    x0, y0, x1, y1 = _region_px(img, (0.09, 0.285, 0.99, 0.375))
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


def analyze(img, head_side="left"):
    cars = detect_cars(img)
    arrows = detect_arrows(img)
    for c in cars:
        d, off = detect_direction(c, img, arrows)
        c["dir"] = d
        c["arrow_off"] = off
    # 阻挡判定：棋盘内所有车 + 接驳位停着的车（后者挡住 up 方向）
    docked = detect_docked_cars(img)
    hsv_full = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    for c in cars:
        c["can_exit"] = can_exit(c, cars, img.shape, docked, img)
        c["tap"] = pick_tap_point(c, hsv_full)
    q = detect_queue(img)
    if q["colors"]:
        q["head"] = q["colors"][0] if head_side == "left" else q["colors"][-1]
        q["head_side"] = head_side
    return {"cars": cars, "queue": q, "docked": docked,
            "empty_slots": detect_empty_slots(img), "tilt": tilt_info(arrows)}


def annotate(img, result, pick=None):
    vis = img.copy()
    for c in result["cars"]:
        col = DRAW.get(c["color"], (150,150,150))
        cv2.rectangle(vis, (c["bx"], c["by"]), (c["bx"]+c["bw"], c["by"]+c["bh"]), col, 2)
        label = DIR_ARROW.get(c["dir"], "?")
        cv2.putText(vis, label, (c["x"]-6, c["y"]+6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2)
        vec = c.get("vec")
        if vec:
            ex = int(c["x"] + vec[0]*22); ey = int(c["y"] + vec[1]*22)
            cv2.line(vis, (int(c["x"]), int(c["y"])), (ex, ey), (255, 0, 255), 2)
            cv2.circle(vis, (ex, ey), 3, (255, 0, 255), -1)
    q = result["queue"]
    for s in q["seq"]:
        col = DRAW.get(s["color"], (150,150,150))
        cv2.circle(vis, (s["x"], s["y"]), 8, col, -1)
    if q["seq"]:
        head = q["seq"][0] if q["head_side"] == "left" else q["seq"][-1]
        cv2.circle(vis, (head["x"], head["y"]), 16, (0,0,255), 3)
    if pick:
        cv2.rectangle(vis, (pick["bx"]-4, pick["by"]-4),
                      (pick["bx"]+pick["bw"]+4, pick["by"]+pick["bh"]+4), (0,255,0), 4)
    return vis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    ap.add_argument("--device")
    ap.add_argument("--output", default="outputs/parking_annotated.png")
    ap.add_argument("--head-side", default="left", choices=["left", "right"])
    args = ap.parse_args()

    if args.image:
        img = cv2.imread(args.image)
    else:
        img = grab(args.device)
    if img is None:
        print("抓图失败"); return
    res = analyze(img, args.head_side)
    print(json.dumps({
        "cars": len(res["cars"]),
        "colors": {c: sum(1 for x in res["cars"] if x["color"] == c)
                   for c in set(x["color"] for x in res["cars"])},
        "queue_seq": res["queue"]["colors"],
        "head": res["queue"]["head"],
        "tilt": res["tilt"],
    }, ensure_ascii=False))
    vis = annotate(img, res)
    cv2.imwrite(args.output, vis)
    print("saved", args.output)


if __name__ == "__main__":
    main()
