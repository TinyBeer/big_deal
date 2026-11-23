#!/usr/bin/env python3
"""沙画收集辅助 · 视觉识别模块。

抓图 -> 识别第一排桶的颜色、槽位中已有桶的颜色、加号、解锁弹窗、终止弹窗
-> 输出标注图 + JSON 摘要。坐标以 1080x2400 为基准，按比例适配。

游戏为 canvas 渲染，控件树内没有游戏文字，所有游戏内元素均用颜色/模板识别。
桶色取自「桶口内部」（第一排 y≈1420~1480），不是桶沿/桶身（桶沿统一青色）。
"""
import argparse
import json
import os
import subprocess

import cv2
import numpy as np

# 复用色块入槽工具经过实机标定的颜色分类（14 色 + 橙粉）
import sys
_SLOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "slots")
if _SLOTS_DIR not in sys.path:
    sys.path.insert(0, _SLOTS_DIR)
from slots_vision import hue_name as _base_hue_name, CN, DRAW  # noqa: E402

# 沙画收集实机出现的桶色（2026-11-23 全屏 25 桶扫描）：
#   蓝(H107 S208 V190) / 青(H96 S179 V198) / 紫(H138 S140 V195)
#   白(H0 S0 V255 或内壁 H0 S21 V216) / 黑(H0 S20 V38)
# 复用 slots 的 16 色表即可覆盖；以下为本项目专属的边界修正。
LOCKED_BUCKET_HSV = (109, 114, 179)   # 带问号的未解锁桶（深蓝灰），不算桶色
LOCKED_TOL = (5, 18, 18)   # 收紧：空槽底 (115,87,161) 的 S 差 27，不会误判


def is_locked_bucket(h, s, v):
    """是否带问号的锁定桶底 (H109 S114 V179)。"""
    return (abs(int(h) - LOCKED_BUCKET_HSV[0]) <= LOCKED_TOL[0]
            and abs(int(s) - LOCKED_BUCKET_HSV[1]) <= LOCKED_TOL[1]
            and abs(int(v) - LOCKED_BUCKET_HSV[2]) <= LOCKED_TOL[2])


def hue_name(h, s=255, v=255):
    """桶色分类：在通用色表上补两个本项目专属修正。

    1. 白桶内壁实测 (H0 S21 V216)，通用色表 S<20 V>210 差 1 落到 gray_light，
       统一归 white（另有纯白内壁 H0 S0 V255 本来就归 white）。
    2. 带问号的锁定桶底 (H109 S114 V179) 归 unknown，不参与颜色决策。
    """
    if is_locked_bucket(h, s, v):
        return "unknown"
    name = _base_hue_name(h, s, v)
    if name == "gray_light" and int(v) >= 205 and int(s) < 35:
        return "white"
    return name

# 区域比例（1080x2400）：第一排桶 y≈1390~1580；槽位行 y≈1160~1270
FIRST_ROW_X = (120, 330, 540, 750, 960)   # 第一排 5 列中心
BUCKET_INNER_Y = (1420, 1480)             # 桶口内部（颜色判定区）
BUCKET_BOX_Y = (1390, 1580)               # 桶整体（标注框）
BUCKET_HALF_W = 88
SLOT_ROI = (0.11, 0.483, 0.88, 0.515)     # 槽位行上半（桶口）；避开两侧箭头与底部橙边
PLUS_SEARCH = (0.10, 0.51, 0.28, 0.60)    # 加号搜索区（中部左侧）

# 米色背景/空槽底色：H≈22 S≈161 V≈255；空槽深蓝：H115 S87 V161
# 桶色可能是任意饱和度，必须是「非米色、非空槽深蓝」的可见色块
BEIGE_H = (14, 32)
EMPTY_SLOT_H = (104, 126)


def grab(serial=None):
    cmd = ["adb"] + (["-s", serial] if serial else []) + ["exec-out", "screencap", "-p"]
    data = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout
    return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)


def _region_px(img, box):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = box
    return (int(x0 * w), int(y0 * h), int(min(x1, 1.0) * w), int(min(y1, 1.0) * h))


def _is_bucket_pixel(h, s, v):
    """判定像素是否像桶色：非米色背景、非空槽深蓝、非纯黑描边。

    黑桶内壁实测 (H0 S20 V38)，不能被暗色过滤掉；只有 V<12 的纯黑描边才排除。
    """
    if v < 12:
        return False
    if BEIGE_H[0] <= h <= BEIGE_H[1] and s > 80 and v > 185:
        return False
    if EMPTY_SLOT_H[0] <= h <= EMPTY_SLOT_H[1] and 45 <= s <= 130 and 120 <= v <= 200:
        return False
    return True


def detect_first_row(img):
    """自适应检测第一排桶（列数/桶尺寸随关卡变化，不能固定列坐标）。

    用连通域找桶体：掩码 = 高饱和或暗色，排除米色背景与空槽底；
    用 bbox 顶部 y 限定在第一排（避开下面几排）。桶色取桶口内部中位色。
    已验证关卡 155（5 列小桶）与 156（4 列大桶）。
    """
    h, w = img.shape[:2]
    sx, sy = w / 1080.0, h / 2400.0
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

    mask = ((S > 60) | (V < 90)).astype(np.uint8)
    beige = ((H >= BEIGE_H[0]) & (H <= BEIGE_H[1]) & (S > 80) & (V > 185))
    empty = ((H >= EMPTY_SLOT_H[0]) & (H <= EMPTY_SLOT_H[1])
             & (S >= 45) & (S <= 130) & (V >= 120) & (V <= 200))
    mask[beige | empty] = 0
    mask[:int(1320 * sy), :] = 0
    mask[int(1600 * sy):, :] = 0
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)))

    n, lab, stats, cents = cv2.connectedComponentsWithStats(mask)
    blocks = []
    top_lo, top_hi = int(1330 * sy), int(1480 * sy)
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if not (top_lo <= y <= top_hi):
            continue
        if (area < 4000 * sx * sy or bw < 60 * sx or bw > 220 * sx
                or bh < 60 * sy or bh > 220 * sy):
            continue
        cx = x + bw // 2
        xa, xb = max(0, cx - int(18 * sx)), min(w, cx + int(18 * sx))
        ya, yb = int(y + 20 * sy), int(y + 70 * sy)
        if yb <= ya or xb <= xa:
            continue
        p = hsv[ya:yb, xa:xb].reshape(-1, 3)
        good = np.array([_is_bucket_pixel(hh, ss, vv) for hh, ss, vv in p])
        px = p[good] if 0.3 <= good.mean() else p
        color = hue_name(float(np.median(px[:, 0])),
                         float(np.median(px[:, 1])),
                         float(np.median(px[:, 2])))
        if color == "unknown":
            continue
        blocks.append({
            "x": int(round(cx)), "y": int(round(y + 0.6 * bh)),
            "bx": int(x), "by": int(y), "bw": int(bw), "bh": int(bh),
            "area": int(area), "color": color,
            "hsv": [int(t) for t in np.median(px, axis=0)],
        })
    blocks.sort(key=lambda b: b["x"])
    return blocks


def detect_slot_colors(img, min_area=900):
    """检测槽位行中已有桶的颜色集合。

    槽位里的桶是缩小版，位于 y≈1160~1260；空槽为深蓝底（H115 S87 V161）。
    用连通域找「非米色、非空槽底」的色块，再取中位色分类。
    """
    h, w = img.shape[:2]
    x0, y0, x1, y1 = _region_px(img, SLOT_ROI)
    crop = img[y0:y1, x0:x1]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    mask = np.zeros(H.shape, np.uint8)
    for yy in range(H.shape[0]):
        for xx in range(H.shape[1]):
            if _is_bucket_pixel(int(H[yy, xx]), int(S[yy, xx]), int(V[yy, xx])):
                mask[yy, xx] = 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)))
    n, lab, stats, cents = cv2.connectedComponentsWithStats(mask)
    buckets = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < min_area or bw < 24 or bh < 24 or bw > 200 or bh > 160:
            continue
        ys, xs = np.where(lab == i)
        px = hsv[ys, xs]
        color = hue_name(float(np.median(px[:, 0])),
                         float(np.median(px[:, 1])),
                         float(np.median(px[:, 2])))
        if color == "unknown":
            continue
        buckets.append({
            "x": int(round(cents[i][0] + x0)), "y": int(round(cents[i][1] + y0)),
            "bx": int(x + x0), "by": int(y + y0), "bw": int(bw), "bh": int(bh),
            "area": int(area), "color": color,
        })
    return buckets


def _template(name):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", name)


def detect_plus(img, threshold=0.85):
    """检测加号按钮，返回中心坐标列表。"""
    tpl = cv2.imread(_template("plus.png"))
    if tpl is None:
        return []
    x0, y0, x1, y1 = _region_px(img, PLUS_SEARCH)
    search = img[y0:y1, x0:x1]
    if tpl.shape[0] > search.shape[0] or tpl.shape[1] > search.shape[1]:
        return []
    res = cv2.matchTemplate(search, tpl, cv2.TM_CCOEFF_NORMED)
    _, mv, _, ml = cv2.minMaxLoc(res)
    if mv < threshold:
        return []
    return [(int(x0 + ml[0] + tpl.shape[1] / 2),
             int(y0 + ml[1] + tpl.shape[0] / 2))]


def detect_unlock_dialog(img, threshold=0.85):
    """检测「解锁槽位」弹窗（标题模板）。"""
    tpl = cv2.imread(_template("unlock_title.png"))
    if tpl is None:
        return False
    return float(cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED).max()) >= threshold


def detect_free_button(img, threshold=0.85):
    """检测弹窗内绿色「免费使用」按钮，返回中心坐标。"""
    tpl = cv2.imread(_template("free_use.png"))
    if tpl is None:
        return None
    res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
    _, mv, _, ml = cv2.minMaxLoc(res)
    if mv < threshold:
        return None
    return (int(ml[0] + tpl.shape[1] / 2), int(ml[1] + tpl.shape[0] / 2))


def _template_image(name):
    """读模板；文件不存在时静默返回 None（复活/通关模板待实机抓取）。"""
    path = _template(name)
    if not os.path.exists(path):
        return None
    return cv2.imread(path)


def _detect_banner(img, name, threshold):
    tpl = _template_image(name)
    if tpl is None:
        return False
    return float(cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED).max()) >= threshold


def detect_revive_dialog(img, threshold=0.80):
    """复活弹窗：模板存在才检测（用户遇到时实拍后放入 templates/）。"""
    return _detect_banner(img, "revive_banner.png", threshold)


def detect_victory_dialog(img, threshold=0.80):
    """通关弹窗：模板存在才检测。"""
    return _detect_banner(img, "victory_banner.png", threshold)


def analyze(img):
    return {
        "first_row": detect_first_row(img),
        "slot_buckets": detect_slot_colors(img),
        "slot_colors": sorted(set(b["color"] for b in detect_slot_colors(img))),
        "plus": detect_plus(img),
        "unlock_dialog": detect_unlock_dialog(img),
        "free_button": detect_free_button(img),
        "revive": detect_revive_dialog(img),
        "victory": detect_victory_dialog(img),
    }


def annotate(img, result, pick=None):
    vis = img.copy()
    for b in result["first_row"]:
        col = DRAW.get(b["color"], (150, 150, 150))
        cv2.rectangle(vis, (b["bx"], b["by"]), (b["bx"] + b["bw"], b["by"] + b["bh"]),
                      col, 2)
        cv2.putText(vis, CN.get(b["color"], b["color"]), (b["bx"] + 4, b["by"] + 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, col, 2)
    for b in result["slot_buckets"]:
        col = DRAW.get(b["color"], (150, 150, 150))
        cv2.rectangle(vis, (b["bx"], b["by"]), (b["bx"] + b["bw"], b["by"] + b["bh"]),
                      col, 2)
        cv2.putText(vis, "槽:" + CN.get(b["color"], b["color"]),
                    (b["bx"], max(20, b["by"] - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)
    for x, y in result["plus"]:
        cv2.circle(vis, (x, y), 34, (0, 165, 255), 3)
        cv2.putText(vis, "+", (x - 18, y + 14), cv2.FONT_HERSHEY_SIMPLEX,
                    1.2, (0, 165, 255), 3)
    if result["free_button"]:
        x, y = result["free_button"]
        cv2.circle(vis, (x, y), 24, (0, 255, 0), 3)
        cv2.putText(vis, "免费", (x - 40, y - 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)
    if result["revive"]:
        cv2.putText(vis, "REVIVE!", (420, 120), cv2.FONT_HERSHEY_SIMPLEX,
                    1.5, (0, 0, 255), 4)
    if result["victory"]:
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
    ap.add_argument("--output", default="outputs/sand_annotated.png")
    args = ap.parse_args()

    img = cv2.imread(args.image) if args.image else grab(args.device)
    if img is None:
        print("抓图失败")
        return
    result = analyze(img)
    print(json.dumps({
        "first_row": [(CN.get(b["color"], b["color"]), b["x"], b["y"], b["hsv"])
                      for b in result["first_row"]],
        "slot_colors": result["slot_colors"],
        "slot_buckets": [(CN.get(b["color"], b["color"]), b["x"], b["y"])
                         for b in result["slot_buckets"]],
        "plus": result["plus"],
        "unlock_dialog": result["unlock_dialog"],
        "free_button": result["free_button"],
        "revive": result["revive"], "victory": result["victory"],
    }, ensure_ascii=False))
    cv2.imwrite(args.output, annotate(img, result))
    print("saved", args.output)


if __name__ == "__main__":
    main()
