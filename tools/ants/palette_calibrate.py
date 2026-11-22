#!/usr/bin/env python3
"""从搬砖大战上方的像素画标定颜色池。

参考 tools/slots/palette_calibrate.py 的做法：
1) 自动检测上方像素画 ROI（只扫画面上半部分，不碰槽位/候选块）；
2) Sobel 投影 + FFT 估网格步长，按饱和度最大准则对齐格心相位；
3) 逐格取内部众数色，跳过米色空格；
4) KMeans 聚类，输出每色的 RGB/HSV/占比和 ants_vision.classify_hsv 的当前分类。

用途：发现 classify_hsv 漏掉或合并的颜色（比如暗红/亮红），再据此补规则。
标定结果写到 --output（默认 tools/ants/palette.json），只是参考数据；
运行时决策仍由 ants_vision.classify_hsv 完成，和 slots 工具保持一致。
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ants_vision import classify_hsv, grab  # noqa: E402

# 1080x2400 基准下像素画的大致范围，仅作 ROI 自动检测失败时的兜底
FALLBACK_BOARD = (86, 302, 1006, 1314)
UPPER_LIMIT = 1500  # 只扫上半屏，避免把槽位/候选块圈进来


def _longest_band(prof, thr, minlen):
    best = cur = None
    for i, v in enumerate(prof > thr):
        if v:
            cur = [i, i] if cur is None else [cur[0], i]
        elif cur:
            if cur[1] - cur[0] >= minlen and (best is None or cur[1] - cur[0] > best[1] - best[0]):
                best = cur
            cur = None
    if cur and cur[1] - cur[0] >= minlen and (best is None or cur[1] - cur[0] > best[1] - best[0]):
        best = cur
    return tuple(best) if best else None


def detect_board_roi(img):
    """返回像素画 ROI (x0,y0,x1,y1)。先用投影找最大彩色带，失败则回退固定坐标。"""
    h, w = img.shape[:2]
    sx, sy = w / 1080.0, h / 2400.0
    upper = img[:min(h, int(UPPER_LIMIT * sy))]
    hsv = cv2.cvtColor(upper, cv2.COLOR_BGR2HSV)
    mask = ((hsv[:, :, 1] > 85) | (hsv[:, :, 2] < 110)).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                            np.ones((11, 11), np.uint8))
    xr = _longest_band(mask.mean(axis=0), 0.15, int(250 * sx))
    if xr:
        yr = _longest_band(mask[:, xr[0]:xr[1] + 1].mean(axis=1),
                           0.12, int(300 * sy))
        if yr and xr[1] - xr[0] > 300 * sx and yr[1] - yr[0] > 300 * sy:
            return (int(xr[0]), int(yr[0]), int(xr[1]), int(yr[1]))
    return tuple(int(v * (sx if i % 2 == 0 else sy))
                 for i, v in enumerate(FALLBACK_BOARD))


def _align_phase(img, x0, y0, x1, y1, step):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    def score_x(p):
        vals = [int(hsv[cy, cx, 1])
                for cy in range(y0 + 5, y1 - 5, step)
                for cx in range(x0 + p, x1 - 5, step)]
        return float(np.mean(vals)) if vals else 0.0

    def score_y(p):
        vals = [int(hsv[cy, cx, 1])
                for cy in range(y0 + p, y1 - 5, step)
                for cx in range(x0 + 5, x1 - 5, step)]
        return float(np.mean(vals)) if vals else 0.0

    return max(range(step), key=score_x), max(range(step), key=score_y)


def _mode_color(patch):
    q = (patch // 8).reshape(-1, 3)
    key = (q[:, 0].astype(np.int32) * 4096
           + q[:, 1].astype(np.int32) * 64 + q[:, 2].astype(np.int32))
    u, c = np.unique(key, return_counts=True)
    k = int(u[c.argmax()])
    b, g, r = (k // 4096) * 8, ((k // 64) % 64) * 8, (k % 64) * 8
    m = ((q[:, 0] == b // 8) & (q[:, 1] == g // 8) & (q[:, 2] == r // 8))
    return np.median(patch.reshape(-1, 3)[m], axis=0).astype(np.uint8)


def _grid_period(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    sx = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)).mean(axis=0)
    sy = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)).mean(axis=1)

    def period(sig):
        s = sig - sig.mean()
        f = np.abs(np.fft.rfft(s))
        f[0] = 0
        k = int(np.argmax(f))
        return float(len(sig) / k) if k > 0 else 23.0

    return period(sx), period(sy)


def calibrate(img, k=14, ox_off=None, oy_off=None):
    x0, y0, x1, y1 = detect_board_roi(img)
    roi = img[y0:y1, x0:x1]
    if roi.size == 0:
        return {"error": "像素画 ROI 为空"}
    px, py = _grid_period(roi)
    # 格距实际约 23px；FFT 偶尔被纹理干扰，限制到合理范围
    step_x = max(8, min(40, int(round(px))))
    step_y = max(8, min(40, int(round(py))))
    if ox_off is None or oy_off is None:
        aox, aoy = _align_phase(img, x0, y0, x1, y1, step_x)
        ox_off = aox if ox_off is None else ox_off
        oy_off = aoy if oy_off is None else oy_off

    samples = []
    cy = y0 + oy_off
    while cy + 4 < y1:
        cx = x0 + ox_off
        while cx + 4 < x1:
            patch = img[cy - 4:cy + 5, cx - 4:cx + 5]
            if patch.shape[:2] == (9, 9):
                bgr = _mode_color(patch)
                hsv = cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2HSV)[0, 0]
                # 米色空格不进颜色池；其余（含白色高光/花瓣）都算真实颜色
                if classify_hsv(int(hsv[0]), int(hsv[1]), int(hsv[2])) is not None:
                    samples.append(bgr)
            cx += step_x
        cy += step_y

    if len(samples) < 20:
        return {"error": "采样格数不足", "cells": len(samples),
                "board_roi": [x0, y0, x1, y1]}

    samples = np.array(samples, np.float32)
    k = max(2, min(k, len(samples)))
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
    _, lab, cents = cv2.kmeans(samples, k, None, crit, 30, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(lab.ravel())
    order = np.argsort(-counts)
    palette = []
    for i in order:
        b, g, r = [int(v) for v in cents[i]]
        hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0, 0]
        palette.append({
            "rgb": [r, g, b],
            "hex": "#%02X%02X%02X" % (r, g, b),
            "hsv": [int(hsv[0]), int(hsv[1]), int(hsv[2])],
            "count": int(counts[i]),
            "ratio": round(float(counts[i]) / len(samples), 4),
            "current_class": classify_hsv(int(hsv[0]), int(hsv[1]), int(hsv[2])),
        })

    # 检出分类器的问题：unknown，或多个簇归到同一个类（颜色被合并）
    groups = {}
    for p in palette:
        groups.setdefault(p["current_class"], []).append(p["hex"])
    issues = {}
    for cls, hexes in groups.items():
        if cls == "unknown" or len(hexes) > 1:
            issues[str(cls)] = hexes

    return {
        "board_roi": [x0, y0, x1, y1],
        "cell_offset": [ox_off, oy_off],
        "grid_step_px": [round(float(px), 2), round(float(py), 2)],
        "cells": len(samples),
        "palette": palette,
        "issues": issues,
    }


def main():
    ap = argparse.ArgumentParser(description="搬砖大战 · 从上方像素画标定颜色池")
    ap.add_argument("--image", help="截图；省略则实时抓图")
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--k", type=int, default=14, help="KMeans 聚类数（默认 14）")
    ap.add_argument("--ox", type=int, default=None, help="格心相对 ROI 左边缘的 x 偏移")
    ap.add_argument("--oy", type=int, default=None, help="格心相对 ROI 上边缘的 y 偏移")
    ap.add_argument("--output", default=os.path.join(HERE, "palette.json"))
    args = ap.parse_args()

    img = cv2.imread(args.image) if args.image else grab(args.device)
    if img is None:
        raise SystemExit("抓图/读图失败")

    result = calibrate(img, args.k, args.ox, args.oy)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print("saved", args.output)


if __name__ == "__main__":
    main()
