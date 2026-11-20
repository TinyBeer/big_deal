#!/usr/bin/env python3
"""停车场接客辅助 · 视觉识别模块。

抓图 -> 分水岭分离车辆 -> 识别每辆车(颜色/朝向/中心/可开出) -> 识别队首乘客颜色
-> 输出标注图 + JSON 摘要。

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
DIR_ARROW = {"left": "←", "right": "→", "up": "↑", "down": "↓"}


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
            cars.append({
                "x": gx, "y": gy,
                "bx": xx + x0, "by": yy + y0, "bw": ww, "bh": hh,
                "color": name,
                "area": int(area),
            })
    return cars


def detect_arrows(img):
    """全图检测白色箭头（车身上唯一的纯白实心块），返回每个箭头的中心和朝向。

    箭头大小/颜色固定、只是方向不同：横箭头约 65x23、竖箭头约 26x55。
    朝向由「三角头那一端更宽」判定（箭杆细、三角粗），与箭头在车身上的位置无关，
    比白色质心法可靠得多。灰「?」障碍车没有箭头，天然被排除。
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
        if not (200 < area < 2000 and 15 < w < 100 and 10 < h < 100):
            continue
        ys, xs = np.where(lab == i)
        horizontal = w >= h
        if horizontal:
            mid = (xs.min() + xs.max()) / 2.0
            left = np.ptp(ys[xs < mid]) if (xs < mid).any() else 0
            right = np.ptp(ys[xs >= mid]) if (xs >= mid).any() else 0
            d = "right" if right > left else "left"
        else:
            mid = (ys.min() + ys.max()) / 2.0
            top = np.ptp(xs[ys < mid]) if (ys < mid).any() else 0
            bot = np.ptp(xs[ys >= mid]) if (ys >= mid).any() else 0
            d = "down" if bot > top else "up"
        arrows.append({"x": float(cents[i][0]) + x0, "y": float(cents[i][1]) + y0,
                       "dir": d, "w": int(w), "h": int(h)})
    return arrows


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
            return inside[0]["dir"], 0.0
    # 退化：车身 bbox 内白色质心（旧法，仅在箭头块漏检时用）
    bx, by, bw, bh = car["bx"], car["by"], car["bw"], car["bh"]
    roi = img[by:by+bh, bx:bx+bw]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    white = ((hsv[:, :, 1] < 60) & (hsv[:, :, 2] > 235)).astype(np.uint8)
    if bw >= bh:
        proj = white.sum(axis=0); mid = bw/2.0
        ws = proj[2:bw-2]; xs = np.arange(2, bw-2)
        c = float((xs*ws).sum()/ws.sum()) if ws.sum() else mid
        return ("right" if c >= mid else "left"), round(c, 1)
    else:
        proj = white.sum(axis=1); mid = bh/2.0
        ws = proj[2:bh-2]; ys = np.arange(2, bh-2)
        c = float((ys*ws).sum()/ws.sum()) if ws.sum() else mid
        return ("down" if c >= mid else "up"), round(c, 1)


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


def can_exit(car, cars, img_shape, docked=None):
    """沿箭头方向做全程射线扫描：路径上任一占用块（车/障碍/接驳车）都挡住。

    建立以车辆 bbox 为单元的二维占用坐标系。沿行进方向从车头前端一直扫到
    画面边界（而非只看邻近几格），检查是否有任何其它车/接驳位车辆的
    投影区间与该射线走廊相交。相交即不可开出。
    """
    h, w = img_shape[:2]
    bx, by, bw, bh = car["bx"], car["by"], car["bw"], car["bh"]
    d = car["dir"]
    # 射线走廊：横向车沿 x 方向扫(用 y 区间做投影)，竖向车沿 y 方向扫(用 x 区间)
    if d in ("left", "right"):
        lane_lo, lane_hi = by + 6, by + bh - 6   # 垂直于行进方向的占用区间
    else:
        lane_lo, lane_hi = bx + 6, bx + bw - 6

    # 所有占用块 = 棋盘车 + 接驳位停着的车
    blocks = [o for o in cars if o is not car] + [o for o in (docked or [])]

    for o in blocks:
        ox0, oy0 = o["bx"], o["by"]
        ox1, oy1 = ox0 + o["bw"], oy0 + o["bh"]
        if d == "left":
            # 占用块在车左侧、且投影区间重叠 => 挡住
            if ox1 <= bx + 4 and oy1 > lane_lo and oy0 < lane_hi:
                return False
        elif d == "right":
            if ox0 >= bx + bw - 4 and oy1 > lane_lo and oy0 < lane_hi:
                return False
        elif d == "up":
            if oy1 <= by + 4 and ox1 > lane_lo and ox0 < lane_hi:
                return False
        else:  # down
            if oy0 >= by + bh - 4 and ox1 > lane_lo and ox0 < lane_hi:
                return False
    return True


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
    for c in cars:
        c["can_exit"] = can_exit(c, cars, img.shape, docked)
    q = detect_queue(img)
    if q["colors"]:
        q["head"] = q["colors"][0] if head_side == "left" else q["colors"][-1]
        q["head_side"] = head_side
    return {"cars": cars, "queue": q, "docked": docked,
            "empty_slots": detect_empty_slots(img)}


def annotate(img, result, pick=None):
    vis = img.copy()
    for c in result["cars"]:
        col = DRAW.get(c["color"], (150,150,150))
        cv2.rectangle(vis, (c["bx"], c["by"]), (c["bx"]+c["bw"], c["by"]+c["bh"]), col, 2)
        label = DIR_ARROW.get(c["dir"], "?")
        cv2.putText(vis, label, (c["x"]-6, c["y"]+6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2)
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
    }, ensure_ascii=False))
    vis = annotate(img, res)
    cv2.imwrite(args.output, vis)
    print("saved", args.output)


if __name__ == "__main__":
    main()
