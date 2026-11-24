#!/usr/bin/env python3
"""搬砖大战（蚂蚁搬像素）辅助 · 视觉识别模块。

抓图 -> 识别福利弹窗、复活弹窗、槽位、候选色块 -> 输出标注图 + JSON。

按用户要求：不检查像素画，不做前沿/剩余数量识别，只认槽位和候选块。

坐标以 1080x2400 为基准，按比例适配。
游戏画面为 canvas 渲染，控件树内没有游戏文字，因此全部用颜色/模板识别。
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
from common.screen import grab as _adb_grab  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(HERE, "templates")

# 参考分辨率 1080x2400 下的固定几何
REF_W, REF_H = 1080, 2400
SLOT_CENTERS = (161, 350, 539, 729, 918)
SLOT_Y = 1709
# 广告解锁的第 6 个槽：在第 5 槽正上方。未解锁时这里是蓝色「解锁」按钮，
# 解锁后变成米色空槽。检测时必须区分，否则会把解锁按钮当成一个已占用槽。
EXTRA_SLOT_X, EXTRA_SLOT_Y = 918, 1514
QUEUE_XS = (209, 375, 540, 705, 871)
QUEUE_YS = (1897, 2062)

CN = {
    "yellow": "黄", "green": "绿", "light_brown": "浅棕",
    "olive": "橄榄", "dark_brown": "深棕", "dark_green": "深绿",
    "mint": "薄荷", "pink": "粉", "pink_light": "浅粉", "red": "红", "dark_red": "暗红",
    "coral": "橙红", "orange": "橙", "peach": "浅橙", "cyan": "青",
    "gray": "深灰", "slate": "蓝灰",
    "white": "白", "black": "黑", "unknown": "未知",
}
DRAW = {
    "yellow": (40, 220, 250), "green": (60, 200, 90),
    "light_brown": (150, 120, 200), "olive": (100, 130, 170),
    "dark_brown": (90, 70, 130), "dark_green": (90, 150, 40),
    "mint": (140, 220, 160), "pink": (220, 80, 240), "pink_light": (240, 180, 255),
    "red": (60, 60, 240), "dark_red": (120, 40, 150),
    "coral": (80, 100, 240), "orange": (30, 140, 255),
    "peach": (130, 180, 255), "cyan": (255, 220, 60),
    "gray": (105, 100, 115), "slate": (200, 150, 110),
    "white": (255, 255, 255),
    "black": (30, 30, 30), "unknown": (150, 150, 150),
}


def grab(serial=None):
    return _adb_grab(serial, check=True)


def scale_of(img):
    h, w = img.shape[:2]
    return w / REF_W, h / REF_H


def _scaled_pt(pt, sx, sy):
    return (int(round(pt[0] * sx)), int(round(pt[1] * sy)))


def main_color(px):
    """从一块像素里提取「块主体色」。

    块上有白色数字和深色描边/阴影，直接取全体中位数会把亮色拉暗：
    peach 实测全体中位 [11,99,233] 会被判成 light_brown，但高亮主体是
    [12,82,255]。做法是先用 V 的高 60% 分层再取中位，避开描边阴影。
    """
    px = np.asarray(px)
    if px.size == 0:
        return np.array([0, 0, 0])
    v = px[:, 2]
    cut = np.percentile(v, 40)
    bright = px[v >= cut]
    if len(bright) < 30:
        bright = px
    return np.median(bright, axis=0)


def classify_hsv(h, s, v):
    """把像素归入游戏调色板。None 表示像素画背景（已被搬走）。

    颜色池由 tools/ants/palette_calibrate.py 从上方像素画标定补全；相近色
    （暗红/亮红、浅橙/棕/珊瑚红）必须按饱和度+亮度拆开，否则同色去重会误跳过。
    """
    h, s, v = int(h) % 180, int(s), int(v)
    # 背景：米色，H≈21 S≈60 V≈160~255；浅橙格 S≈97 能区分。
    if 18 <= h <= 28 and s < 85 and v > 130:
        return None
    if s < 25 and v > 200:
        return "white"
    if v < 60:
        return "black"
    # 低饱和中暗灰：槽位里的深灰 H104 S54 V≈86，第一排的蓝灰块
    # H108 S55 V≈120。旧判据把两者都归 gray，导致槽里有深灰时第一排
    # 蓝灰块被当成同色跳过。按 V=105 拆开，实测两档间隔 >15。
    if 90 <= h <= 120 and s < 80 and v < 130:
        return "gray" if v < 105 else "slate"
    # 标定新增色：橙 H19 S242 V255、青 H97 S228 V255
    if 16 <= h <= 24 and s > 180 and v > 200:
        return "orange"
    if 88 <= h <= 108 and s > 150:
        return "cyan"
    # 珊瑚红 H≈8 S≈155 V≈220，介于亮红和浅棕之间
    if h <= 8 and 120 <= s <= 180 and 190 <= v <= 240:
        return "coral"
    # 红色系：高饱和的两档红按亮度拆开（暗红 V≈156 / 亮红 V≈239）
    if h >= 160 and s >= 140:
        return "dark_red" if v < 190 else "red"
    if h >= 160:
        # 两种粉色都是 H≈163，只能靠饱和度拆：槽内浅粉 S≈68，第一排
        # 粉块 S≈118。旧版统一归 pink，槽内浅粉会误挡第一排粉块。
        return "pink" if s >= 100 else "pink_light"
    if h <= 8:
        return "red"
    if 8 <= h <= 18:
        if v < 110:
            return "dark_brown"
        if v < 155:
            return "olive"
        if 130 <= s <= 180 and 195 <= v <= 235:
            return "coral"
        # peach 与 light_brown 色相几乎相同（H≈11），只靠明度分：
        #   标定值 peach=[11,97,255] V255，light_brown=[11,137,182] V182。
        # 旧判据 `s<115 且 v>235` 太脆：数字描边阴影把 V 拉到 233 就误判浅棕，
        # 导致槽里已有 peach 却没进 occupied，工具继续投 peach（重复色根因）。
        # 改用 V>=225 判 peach：中间无其他色，采样漂移也不跨界。
        if v >= 225:
            return "peach"
        return "light_brown"
    if 25 <= h <= 35:
        return "yellow"
    if 40 <= h <= 55:
        return "green"
    if 70 <= h <= 85:
        return "dark_green" if v < 150 else "mint"
    return "unknown"


def detect_popup(img, serial=None):
    """检测福利弹窗的红色 X 关闭按钮，返回 {'found', 'x', 'y', 'score'}。"""
    path = os.path.join(TEMPLATE_DIR, "popup_close.png")
    if not os.path.exists(path):
        return {"found": False, "x": 0, "y": 0, "score": 0.0}
    tpl = cv2.imread(path, cv2.IMREAD_COLOR)
    sx, sy = scale_of(img)
    if abs(sx - 1.0) > 0.01 or abs(sy - 1.0) > 0.01:
        tpl = cv2.resize(tpl, None, fx=sx, fy=sy, interpolation=cv2.INTER_LINEAR)
    if tpl.shape[0] > img.shape[0] or tpl.shape[1] > img.shape[1]:
        return {"found": False, "x": 0, "y": 0, "score": 0.0}
    res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
    _, maxv, _, maxloc = cv2.minMaxLoc(res)
    x = maxloc[0] + tpl.shape[1] // 2
    y = maxloc[1] + tpl.shape[0] // 2
    # 福利弹窗 X 周围是暗色遮罩；复活弹窗 X 周围是亮黄色，靠亮度排除误匹配。
    sx1 = max(0, min(img.shape[1] - 1, x - int(45 * sx)))
    sy1 = max(0, min(img.shape[0] - 1, y))
    patch = hsv_of(img)[max(0, sy1 - 5):sy1 + 6, max(0, sx1 - 5):sx1 + 6]
    bg_v = float(np.median(patch[:, :, 2])) if patch.size else 255
    found = bool(maxv >= 0.72 and bg_v < 130)
    return {"found": found, "x": int(x), "y": int(y),
            "score": round(float(maxv), 3), "bg_v": int(bg_v)}


def hsv_of(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2HSV)


def detect_revive(img):
    """检测「复活」弹窗（槽位不足）。按用户约定：命中立即停手，不做任何操作。"""
    path = os.path.join(TEMPLATE_DIR, "revive_close.png")
    if not os.path.exists(path):
        return {"found": False, "x": 0, "y": 0, "score": 0.0}
    tpl = cv2.imread(path, cv2.IMREAD_COLOR)
    sx, sy = scale_of(img)
    if abs(sx - 1.0) > 0.01 or abs(sy - 1.0) > 0.01:
        tpl = cv2.resize(tpl, None, fx=sx, fy=sy, interpolation=cv2.INTER_LINEAR)
    if tpl.shape[0] > img.shape[0] or tpl.shape[1] > img.shape[1]:
        return {"found": False, "x": 0, "y": 0, "score": 0.0}
    res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
    _, maxv, _, maxloc = cv2.minMaxLoc(res)
    x = maxloc[0] + tpl.shape[1] // 2
    y = maxloc[1] + tpl.shape[0] // 2
    sx1 = max(0, min(img.shape[1] - 1, x - int(45 * sx)))
    sy1 = max(0, min(img.shape[0] - 1, y))
    patch = hsv_of(img)[max(0, sy1 - 5):sy1 + 6, max(0, sx1 - 5):sx1 + 6]
    bg_v = float(np.median(patch[:, :, 2])) if patch.size else 0
    found = bool(maxv >= 0.78 and bg_v > 170)
    return {"found": found, "x": int(x), "y": int(y),
            "score": round(float(maxv), 3), "bg_v": int(bg_v)}


def detect_unlock(img, threshold=0.85):
    """检测「解锁」按钮（看广告增加槽位），返回中心点列表。"""
    path = os.path.join(TEMPLATE_DIR, "unlock.png")
    if not os.path.exists(path):
        return []
    tpl = cv2.imread(path, cv2.IMREAD_COLOR)
    sx, sy = scale_of(img)
    if abs(sx - 1.0) > 0.01 or abs(sy - 1.0) > 0.01:
        tpl = cv2.resize(tpl, None, fx=sx, fy=sy, interpolation=cv2.INTER_LINEAR)
    if tpl.shape[0] > img.shape[0] or tpl.shape[1] > img.shape[1]:
        return []
    res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
    locs = np.where(res >= threshold)
    pts = []
    for y, x in zip(*locs):
        cx = int(x + tpl.shape[1] // 2)
        cy = int(y + tpl.shape[0] // 2)
        if all(abs(cx - p[0]) > 40 or abs(cy - p[1]) > 40 for p in pts):
            pts.append((cx, cy))
    pts.sort(key=lambda p: (p[1], p[0]))
    return pts


def detect_slots(img):
    """检测下排 5 个槽 + 广告解锁的第 6 槽，判断哪些槽已被占用。

    关键：槽位坐标固定，必须用固定窗口逐个判断。早期版本只对「米色空槽」
    做连通域，导致被占用的槽整块消失、occupied_colors 永远漏算同色块，
    同色槽位上限形同虚设。第 6 槽在解锁前是蓝色按钮，必须识别并跳过，
    否则会被当成已占用槽，导致「槽位已满」误判、黑块选不出来。
    """
    sx, sy = scale_of(img)
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    def read_slot(ref_x, ref_y, idx):
        cx = int(round(ref_x * sx))
        cy = int(round(ref_y * sy))
        bx = int(round((ref_x - 79) * sx))
        by = int(round((ref_y - 73) * sy))
        bw = int(round(159 * sx))
        bh = int(round(146 * sy))
        x0 = max(0, int(cx - 50 * sx))
        x1 = min(w, int(cx + 50 * sx))
        y0 = max(0, int(cy - 45 * sy))
        y1 = min(h, int(cy + 45 * sy))
        patch = hsv[y0:y1, x0:x1].reshape(-1, 3) if x1 > x0 and y1 > y0 else np.empty((0, 3))
        colored = patch[((patch[:, 1] > 70) & (patch[:, 2] > 70)) |
                        ((patch[:, 2] < 100) & (patch[:, 1] > 100))]
        dark = patch[patch[:, 2] < 115]
        block_px = colored if len(colored) >= len(dark) else dark
        ratio = max(len(colored), len(dark)) / max(1, len(patch))
        occupied = bool(ratio > 0.20)
        color = None
        if occupied:
            color = classify_hsv(*main_color(block_px))
        return {"index": idx, "x": cx, "y": cy,
                "occupied": occupied, "color": color,
                "ratio": round(float(ratio), 3),
                "bx": bx, "by": by, "bw": bw, "bh": bh}

    slots = [read_slot(x, SLOT_Y, i) for i, x in enumerate(SLOT_CENTERS)]

    # 第 6 槽：先判断是否已解锁。未解锁时是蓝色按钮（H≈100、占比高），
    # 解锁后是米色空槽或被占用块（bluish 很低）。
    ex = int(round(EXTRA_SLOT_X * sx))
    ey = int(round(EXTRA_SLOT_Y * sy))
    x0 = max(0, int(ex - 50 * sx))
    x1 = min(w, int(ex + 50 * sx))
    y0 = max(0, int(ey - 45 * sy))
    y1 = min(h, int(ey + 45 * sy))
    epatch = hsv[y0:y1, x0:x1].reshape(-1, 3) if x1 > x0 and y1 > y0 else np.empty((0, 3))
    if epatch.size:
        bluish = np.mean((epatch[:, 0] >= 90) & (epatch[:, 0] <= 120))
        beige = np.mean((epatch[:, 0] >= 18) & (epatch[:, 0] <= 28) &
                        (epatch[:, 1] < 85) & (epatch[:, 2] > 130))
        colored = np.mean((epatch[:, 1] > 70) & (epatch[:, 2] > 70))
        dark = np.mean(epatch[:, 2] < 115)
        # 已解锁的槽 = 不是蓝色按钮，且该位置有内容（米色空槽 / 彩色块 / 暗块）。
        # 纯背景（三者都接近 0，如未解锁阶段的米色斜纹底）不算槽。
        if bluish < 0.5 and max(beige, colored, dark) > 0.30:
            slots.append(read_slot(EXTRA_SLOT_X, EXTRA_SLOT_Y, len(SLOT_CENTERS)))
    return slots


def detect_queue(img):
    """检测候选色块（两排），返回颜色与中心坐标。

    不依赖数字识别：只需要颜色即可决策。
    """
    sx, sy = scale_of(img)
    h, w = img.shape[:2]
    # 只识别第一排：按用户要求不处理第二排，也不用考虑队列前移
    y0 = max(0, int(1810 * sy))
    y1 = min(h, int(1990 * sy))
    roi = img[y0:y1]
    if roi.size == 0:
        return []
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    # 五类块都要覆盖：高饱和彩色 / 深色黑块 / 粉色（S低但H高） / 中低饱和灰紫 /
    # 白色块（S<25 V>200）。米色背景 H≈13~21 S≈57~68 V>130，S 远高于白色，
    # 不会被白色分支吃掉；旧版漏掉白色分支，白块只剩描边暗像素被判成 red。
    mask = (((sat > 95) & (val > 90)) |
            ((val < 120) & (sat > 130)) |
            ((hue >= 150) & (sat > 45) & (val > 150)) |
            ((hue >= 100) & (hue < 150) & (sat > 40) & (val > 170)) |
            ((val < 75) & (sat < 110) & ~((hue >= 18) & (hue <= 28))) |
            ((sat < 25) & (val > 200))).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                            np.ones((9, 9), np.uint8))
    n, lab, stats, cents = cv2.connectedComponentsWithStats(mask)
    blocks = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if not (105 * sx < bw < 200 * sx and 95 * sy < bh < 200 * sy):
            continue
        if area < 5500 * sx * sy:
            continue
        px = hsv[lab == i]
        if px.shape[0] < 1000:
            continue
        color = classify_hsv(*main_color(px))
        if color is None:
            continue
        cx = int(round(cents[i][0]))
        cy = int(round(cents[i][1])) + y0
        blocks.append({"x": cx, "y": cy, "color": color,
                       "bx": int(x), "by": int(y) + y0,
                       "bw": int(bw), "bh": int(bh), "area": int(area)})
    # 兜底：候选块位置固定为 5 个。若某位置因掩码未覆盖新颜色而漏检，
    # 直接按固定窗口采样该位置；classify_hsv 能分类就补上，不必再改掩码。
    full_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    covered = set()
    for b in blocks:
        qx = min(QUEUE_XS, key=lambda t: abs(t - b["x"]))
        if abs(qx - b["x"]) < 30 * sx:
            covered.add(qx)
    qy = int(QUEUE_YS[0] * sy)
    for qx in QUEUE_XS:
        if qx in covered:
            continue
        x = int(qx * sx)
        rx0 = max(0, x - int(55 * sx))
        rx1 = min(w, x + int(55 * sx))
        ry0 = max(0, qy - int(45 * sy))
        ry1 = min(h, qy + int(45 * sy))
        if rx1 <= rx0 or ry1 <= ry0:
            continue
        p = full_hsv[ry0:ry1, rx0:rx1].reshape(-1, 3)
        white_px = (p[:, 1] < 25) & (p[:, 2] > 200)  # 块上的白色数字
        # 必须看到白色数字，否则只是弹窗/结算/其他游戏的背景色，不是候选块。
        # 实测真实块白字 262~1551 像素，误检位置 0~26。
        if int(white_px.sum()) < 150 * sx * sy:
            continue
        # 白块本体就是白色（实测白像素占窗口 83%），不能再把白像素剔除，
        # 否则只剩描边暗像素被判成 red。白色占多数时直接用白像素判色。
        if float(white_px.mean()) > 0.5:
            q = p[white_px]
        else:
            # 排除白字与米色空背景；剩下的即块主体
            q = p[~(((p[:, 1] < 25) & (p[:, 2] > 200)) |
                    ((p[:, 0] >= 18) & (p[:, 0] <= 28) &
                     (p[:, 1] < 85) & (p[:, 2] > 130)))]
        if len(q) < 500 * sx * sy:
            continue
        color = classify_hsv(*main_color(q))
        # unknown 一律不补：避免新游戏/过渡动画里把未知色当候选块点下去
        if color is None or color == "unknown":
            continue
        blocks.append({"x": x, "y": qy, "color": color,
                       "bx": rx0, "by": ry0,
                       "bw": rx1 - rx0, "bh": ry1 - ry0,
                       "area": int(len(q)), "fallback": True})
    blocks.sort(key=lambda b: (b["y"], b["x"]))
    return blocks


def annotate(img, info):
    """在截图上画出识别结果，便于人工核对。"""
    out = img.copy()
    sx, sy = scale_of(img)
    # 槽位
    for slot in info.get("slots", []):
        color = (60, 60, 240) if slot["occupied"] else (60, 200, 60)
        cv2.rectangle(out, (slot["bx"], slot["by"]),
                      (slot["bx"] + slot["bw"], slot["by"] + slot["bh"]),
                      color, max(2, int(3 * sx)))
        cv2.putText(out, str(slot["index"] + 1),
                    (slot["x"] - int(10 * sx), slot["y"] + int(10 * sy)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8 * sx, color, 2)
    # 队列块
    for b in info.get("queue", []):
        color = DRAW.get(b["color"], (150, 150, 150))
        cv2.rectangle(out, (b["bx"], b["by"]),
                      (b["bx"] + b["bw"], b["by"] + b["bh"]),
                      color, max(2, int(3 * sx)))
        cv2.putText(out, CN.get(b["color"], b["color"]),
                    (b["x"] - int(35 * sx), b["y"] + int(8 * sy)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8 * sx, color, 2)
    revive = info.get("revive", {})
    if revive.get("found"):
        cv2.circle(out, (revive["x"], revive["y"]), int(35 * sx), (0, 0, 255), 3)
        cv2.putText(out, "REVIVE", (revive["x"] - int(60 * sx), revive["y"] - int(45 * sy)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9 * sx, (0, 0, 255), 2)
    popup = info.get("popup", {})
    if popup.get("found"):
        cv2.circle(out, (popup["x"], popup["y"]), int(30 * sx), (0, 0, 240), 3)
        cv2.putText(out, "POPUP", (popup["x"] - int(45 * sx), popup["y"] - int(40 * sy)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9 * sx, (0, 0, 240), 2)
    return out


def analyze(img):
    return {
        "popup": detect_popup(img),
        "revive": detect_revive(img),
        "unlock": detect_unlock(img),
        "slots": detect_slots(img),
        "queue": detect_queue(img),
    }


def main():
    ap = argparse.ArgumentParser(description="搬砖大战 · 识别一次并输出标注图")
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--input", help="从本地图片读取（调试用）")
    ap.add_argument("--output", default="/home/beer/workspace/big_deal/outputs/ants_annotated.png")
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    img = cv2.imread(args.input) if args.input else grab(args.device)
    if img is None:
        raise SystemExit("无法读取输入图片: %s" % args.input)
    info = analyze(img)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    cv2.imwrite(args.output, annotate(img, info))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
    print(json.dumps({
        "popup": info["popup"],
        "revive": info["revive"],
        "unlock": info["unlock"],
        "slots": [{"index": s["index"], "occupied": s["occupied"],
                   "color": s["color"]} for s in info["slots"]],
        "queue": [{"x": b["x"], "y": b["y"], "color": b["color"]}
                  for b in info["queue"]],
        "output": args.output,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
