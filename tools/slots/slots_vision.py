#!/usr/bin/env python3
"""色块入槽辅助 · 视觉识别模块。

抓图 -> 识别底部第一排色块、中部槽位占用颜色、解锁按钮、复活弹窗
-> 输出标注图 + JSON 摘要。坐标以 1080x2400 为基准，按比例适配。

当前游戏（京东 Manto 小游戏）为 canvas 渲染，控件树内没有游戏文字，
因此所有游戏内元素均用颜色连通域 / 模板匹配识别。
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
from common.screen import grab  # noqa: E402

# 颜色池：由马赛克拼图实机标定（见 palette.json / palette_calibrate.py）。
# 14 色：白/青/深灰/中灰/浅蓝灰/浅紫(新)/黑/橙红/玫红(新)/蓝/粉/黄/紫/绿 + 橙粉。
# HSV(H) 基准：红~8 玫红~176 黄~29 绿~53 青~88 蓝~108 紫~134 粉~166。
# 相近色分辨要点：
#   - 玫红(H176 S210) vs 橙红(H8 S196)：色相跨 0 边界，用 H>=170 独立；
#   - 粉(H166 S126) vs 玫红(H176 S210)：靠饱和度 + 色相细分区分；
#   - 浅紫(H130 S59) vs 浅蓝灰(H106 S43) vs 中灰(H107 S24)：低饱和区按色相 + 亮度分档。
COLORS = {
    "red":     ((0, 10),    (0, 0, 235)),
    "crimson": ((170, 179), (30, 0, 220)),   # 玫红 H176 S210（跨 0 边界）
    "brown":   ((170, 179), (70, 75, 140)),
    "yellow":  ((26, 38),   (40, 215, 245)),
    "green":   ((39, 78),   (60, 215, 75)),
    "cyan":    ((79, 99),   (225, 215, 70)),
    "blue":    ((100, 124), (235, 100, 45)),
    "purple":  ((125, 149), (185, 70, 235)),
    "lavender": ((123, 147), (150, 130, 225)),  # 浅紫 H130 S59
    "pink":    ((150, 167), (170, 70, 235)),
}
UNKNOWN = "unknown"
# 灰阶三档：浅蓝灰 / 中灰 / 深灰（S<75，按 V 亮度区分，详见 hue_name）。
GRAYS = ("gray_light", "gray", "gray_dark")
DRAW = {
    "red": (60, 60, 235), "crimson": (60, 30, 235), "brown": (70, 75, 140),
    "yellow": (40, 215, 245), "green": (60, 215, 75), "cyan": (225, 215, 70),
    "blue": (235, 100, 45), "purple": (185, 70, 235),
    "lavender": (190, 160, 220), "pink": (170, 70, 235),
    "black": (90, 90, 90), "white": (235, 235, 235),
    "gray_light": (200, 205, 215), "gray": (160, 160, 160),
    "gray_dark": (105, 100, 115),
    "peach": (120, 170, 255), "unknown": (150, 150, 150),
}
CN = {"red": "红", "crimson": "玫红", "brown": "深红", "yellow": "黄",
      "green": "绿", "cyan": "青", "blue": "蓝", "purple": "紫",
      "lavender": "浅紫", "pink": "粉", "black": "黑", "white": "白",
      "gray_light": "浅灰", "gray": "灰", "gray_dark": "深灰",
      "peach": "橙粉", "unknown": "未知"}

# 区域比例（1080x2400）：第一排 y≈1810~2000；槽位 y≈1610~1765
FIRST_ROW = (0.0, 0.754, 1.0, 0.834)
SLOTS = (0.0, 0.671, 1.0, 0.735)
UNLOCK_SEARCH = ((0.0, 0.594, 0.24, 0.668), (0.76, 0.594, 1.0, 0.668))
SLOT_CENTERS = (103, 310, 517, 724, 931)  # 1080 宽基准
FIRST_ROW_CENTERS = (145, 340, 535, 730, 925)  # 第一排 5 列中心


def _region_px(img, box):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = box
    return (int(x0 * w), int(y0 * h), int(min(x1, 1.0) * w), int(min(y1, 1.0) * h))


def hue_name(h, s=255, v=255):
    """把像素 HSV 归入游戏调色板（14 色 + 橙粉，见 palette.json）。

    顺序很关键，先按明度/饱和分黑白灰阶，再按色相分彩色。相近色分辨：
    - 近黑 V<70：无论 S 多大（近黑实测 S 可达 180+）都归 black；
    - 白收紧到 S<20、V>210：第一排白块实测 S=0/V=221（非纯白 255），
      米色背景 S=31/V=197 不会误入；浅蓝灰(S≈43 V≈236)因 S>=20 也不会被抢走；
    - 低饱和 S<75：浅紫(H123~147 且 S>=40 且 V>180) 先从灰阶里独立，
      其余按 V 分浅蓝灰(>202)/中灰(>=140)/深灰；
    - 玫红 H>=170 且 S>=150（跨 0 边界，与橙红 H8 区分）；H>=170 低饱和为深红；
    - 橙粉 H<=25 且 S<170 且很亮，先于红挑出，避免与高饱和橙红(S≈200)混淆。
    """
    h, s, v = int(h) % 180, int(s), int(v)
    if v < 70:
        return "black"
    if s < 20 and v > 210:
        return "white"
    if s < 75:  # 低饱和：浅紫 + 灰阶三档
        if 123 <= h <= 147 and s >= 40 and v > 180:
            return "lavender"
        if v > 202:
            return "gray_light"
        if v >= 140:
            return "gray"
        return "gray_dark"
    if h <= 25 and s < 170 and v > 215:
        return "peach"
    if h >= 170:  # 玫红 / 深红（跨 0 边界）
        return "crimson" if s >= 150 else "brown"
    if h <= 10:
        return "brown" if (v < 195 and s < 160) else "red"
    if 11 <= h <= 25:
        return "red"
    if 26 <= h <= 38:
        return "yellow"
    if 39 <= h <= 78:
        return "green"
    if 79 <= h <= 99:
        return "cyan"
    if 100 <= h <= 122:
        return "blue"
    if 123 <= h <= 149:
        return "purple"
    if 150 <= h <= 167:
        return "pink"
    return UNKNOWN


def detect_color_blocks(img, roi, min_area=3000):
    """在指定 ROI 内按连通域找色块，支持高饱和彩色块与黑色块。

    黑色块 V<110、S<90，不能只靠高饱和掩码，否则整块会被漏掉。
    """
    x0, y0, x1, y1 = _region_px(img, roi)
    hsv = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    sat, val = hsv[:, :, 1], hsv[:, :, 2]
    mask = (((sat > 90) & (val > 90)) | ((val < 110) & (sat < 90))).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)))
    n, lab, stats, cents = cv2.connectedComponentsWithStats(mask)
    blocks = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < min_area or not (110 < w < 250) or not (80 < h < 200):
            continue
        ys, xs = np.where(lab == i)
        if xs.size < 200:
            continue
        pixels = hsv[ys, xs]
        good = ((pixels[:, 1] > 80) & (pixels[:, 2] > 80)) | \
               ((pixels[:, 2] < 110) & (pixels[:, 1] < 90))
        if good.sum() < 100:
            continue
        color = hue_name(float(np.median(pixels[good, 0])),
                         float(np.median(pixels[good, 1])),
                         float(np.median(pixels[good, 2])))
        blocks.append({
            "x": int(round(cents[i][0] + x0)),
            "y": int(round(cents[i][1] + y0)),
            "bx": int(x + x0), "by": int(y + y0),
            "bw": int(w), "bh": int(h), "area": int(area),
            "color": color,
        })
    return blocks


def detect_first_row(img):
    """固定列窗口检测第一排，避免连通域被相邻块/连接柄粘连后漏检。

    空列中心是米色背景（S≈31、V≈197），块中心则高饱和/很暗/很白，
    用中心小窗的「块像素占比 > 0.70」判定该列是否有块。
    """
    h, w = img.shape[:2]
    sx, sy = w / 1080.0, h / 2400.0
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    y0, y1 = int(1870 * sy), int(1940 * sy)
    blocks = []
    for cx in FIRST_ROW_CENTERS:
        x = int(round(cx * sx))
        xa, xb = max(0, x - int(12 * sx)), min(w, x + int(12 * sx))
        if xb <= xa or y1 <= y0:
            continue
        p = hsv[y0:y1, xa:xb]
        # 白块实测 S=0/V=221（非纯白 255）；浅灰紫块 S=58/V=205；
        # 米色背景缝隙 S=31/V=197。三个分支分别覆盖：高饱和彩色 / 深色 /
        # 白块 / 中低饱和彩色(灰紫)。灰色/灰紫块 S≈58 卡在 S>70 以下，
        # 必须靠 40<=S<=90 & V>170 收进来，同时不误检米色(S31)。
        s, v = p[:, :, 1], p[:, :, 2]
        like = ((s > 70) | (v < 150) | ((s < 10) & (v > 210)) |
                ((s >= 40) & (s <= 90) & (v > 170)))
        if float(like.mean()) < 0.70:
            continue
        px = p[like]
        if px.shape[0] < 50:
            continue
        color = hue_name(float(np.median(px[:, 0])),
                         float(np.median(px[:, 1])),
                         float(np.median(px[:, 2])))
        blocks.append({
            "x": x, "y": int(round(1905 * sy)),
            "bx": max(0, int((cx - 88) * sx)), "by": int(1820 * sy),
            "bw": int(176 * sx), "bh": int(160 * sy),
            "area": int(like.sum()), "color": color,
        })
    blocks.sort(key=lambda b: b["x"])
    return blocks


def detect_slots(img):
    """按固定槽位窗口判定占用，比连通域更稳（动画/白字分割也不漏）。

    空槽底色 S≈30；占用槽是高饱和色块，窗口内高饱和像素占比 >> 20%。
    """
    x0, y0, x1, y1 = _region_px(img, SLOTS)
    hsv = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    sat, val = hsv[:, :, 1], hsv[:, :, 2]
    mask = (((sat > 80) & (val > 80)) | ((val < 110) & (sat < 90)) |
            ((sat < 10) & (val > 210)))
    scale = img.shape[1] / 1080.0
    half_w = int(92 * scale)
    slots = []
    for idx, cx in enumerate([c * scale for c in SLOT_CENTERS]):
        xa, xb = max(0, int(cx - half_w) - x0), min(mask.shape[1], int(cx + half_w) - x0)
        if xb <= xa:
            continue
        sub = mask[:, xa:xb]
        if float(sub.mean()) < 0.20:
            continue
        px = hsv[:, xa:xb][sub]
        if px.shape[0] < 100:
            continue
        color = hue_name(float(np.median(px[:, 0])),
                         float(np.median(px[:, 1])),
                         float(np.median(px[:, 2])))
        slots.append({
            "slot": idx,
            "x": int(round(cx)), "y": int(round((y0 + y1) / 2)),
            "bx": x0 + xa, "by": y0,
            "bw": xb - xa, "bh": y1 - y0,
            "area": int(sub.sum()),
            "color": color,
            "fill": round(float(sub.mean()), 3),
        })
    return slots


def detect_slot_colors(img):
    slots = detect_slots(img)
    return {"colors": sorted(set(b["color"] for b in slots)), "slots": slots}


def _template(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "templates", name)


def detect_unlock_buttons(img, template_path=None, threshold=0.85):
    """模板匹配左右两个「解锁」按钮，返回中心坐标列表。"""
    if template_path is None:
        template_path = _template("unlock.png")
    tpl = cv2.imread(template_path)
    if tpl is None:
        return []
    pts = []
    for box in UNLOCK_SEARCH:
        x0, y0, x1, y1 = _region_px(img, box)
        search = img[y0:y1, x0:x1]
        if tpl.shape[0] > search.shape[0] or tpl.shape[1] > search.shape[1]:
            continue
        res = cv2.matchTemplate(search, tpl, cv2.TM_CCOEFF_NORMED)
        _, maxv, _, maxloc = cv2.minMaxLoc(res)
        if maxv < threshold:
            continue
        pts.append((int(x0 + maxloc[0] + tpl.shape[1] / 2),
                    int(y0 + maxloc[1] + tpl.shape[0] / 2)))
    return pts


def detect_revive_dialog(img, template_path=None, threshold=0.80):
    """实拍的橙底黄字「复活」标题；用户定稿：命中立即停手。"""
    if template_path is None:
        template_path = _template("revive_banner.png")
    tpl = cv2.imread(template_path)
    if tpl is None:
        return False
    return float(cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED).max()) >= threshold


def detect_victory_dialog(img, template_path=None, threshold=0.80):
    """实拍的橙底黄字「挑战成功」标题；用户定稿：命中立即停手。"""
    if template_path is None:
        template_path = _template("victory_banner.png")
    tpl = cv2.imread(template_path)
    if tpl is None:
        return False
    return float(cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED).max()) >= threshold


def analyze(img):
    return {
        "first_row": detect_first_row(img),
        "slots": detect_slots(img),
        "slot_colors": detect_slot_colors(img)["colors"],
        "unlocks": detect_unlock_buttons(img),
        "revive": detect_revive_dialog(img),
        "victory": detect_victory_dialog(img),
    }


def annotate(img, result, pick=None):
    vis = img.copy()
    for b in result["first_row"]:
        col = DRAW.get(b["color"], (150, 150, 150))
        cv2.rectangle(vis, (b["bx"], b["by"]), (b["bx"] + b["bw"], b["by"] + b["bh"]),
                      col, 2)
        cv2.putText(vis, CN.get(b["color"], b["color"])[:1], (b["x"] - 12, b["y"] + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)
    for b in result["slots"]:
        col = DRAW.get(b["color"], (150, 150, 150))
        cv2.rectangle(vis, (b["bx"], b["by"]), (b["bx"] + b["bw"], b["by"] + b["bh"]),
                      col, 2)
        cv2.putText(vis, "槽%d:%s" % (b["slot"] + 1, CN.get(b["color"], b["color"])),
                    (b["bx"], b["by"] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)
    for x, y in result["unlocks"]:
        cv2.rectangle(vis, (x - 92, y - 72), (x + 92, y + 72), (0, 165, 255), 3)
        cv2.putText(vis, "解锁", (x - 35, y + 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 165, 255), 2)
    if result.get("revive"):
        cv2.putText(vis, "REVIVE!", (420, 120), cv2.FONT_HERSHEY_SIMPLEX,
                    1.5, (0, 0, 255), 4)
    if result.get("victory"):
        cv2.putText(vis, "VICTORY!", (400, 120), cv2.FONT_HERSHEY_SIMPLEX,
                    1.5, (0, 200, 0), 4)
    picks = pick if isinstance(pick, list) else ([pick] if pick else [])
    for i, p in enumerate(picks, 1):
        cv2.rectangle(vis, (p["bx"] - 5, p["by"] - 5),
                      (p["bx"] + p["bw"] + 5, p["by"] + p["bh"] + 5),
                      (0, 255, 0), 5)
        cv2.putText(vis, str(i), (p["x"] - 10, p["y"] + 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 255), 4)
    return vis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="兼容 quick.sh 入口标记")
    ap.add_argument("--image")
    ap.add_argument("--device")
    ap.add_argument("--output", default="outputs/slots_annotated.png")
    args = ap.parse_args()

    img = cv2.imread(args.image) if args.image else grab(args.device)
    if img is None:
        print("抓图失败")
        return
    result = analyze(img)
    print(json.dumps({
        "first_row": [(CN.get(b["color"], b["color"]), b["x"], b["y"])
                      for b in result["first_row"]],
        "slot_colors": result["slot_colors"],
        "slots": [(b["slot"] + 1, CN.get(b["color"], b["color"])) for b in result["slots"]],
        "unlocks": result["unlocks"],
        "revive": result["revive"],
        "victory": result["victory"],
    }, ensure_ascii=False))
    cv2.imwrite(args.output, annotate(img, result))
    print("saved", args.output)


if __name__ == "__main__":
    main()
