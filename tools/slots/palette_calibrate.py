#!/usr/bin/env python3
"""从马赛克拼图截图标定游戏调色板。

马赛克目标图的每个小格是纯色填充，是天然的颜色标定板。本脚本：
1) 从色彩密度带自动检测完整画板 ROI（不写死坐标，避免画面缩放/位移漏色）；
2) 用 Sobel 投影 + FFT 估计网格步长，饱和度最大准则对齐格心相位；
3) 逐格取内部众数色（避开描边与白色高光点）；
4) KMeans 聚成 K 类，输出每类的 RGB/HSV 中心、像素占比，
   并给出建议在 hue_name 中的归类。

输出 JSON 到 --output（默认 tools/slots/palette.json）。
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slots_vision as sv

# 马赛克目标图 ROI（1080x2400 基准，按比例缩放）。
# 已废弃写死坐标：画面缩放/位移会漏采边缘色（如玫红）。
# 现在默认自动检测完整画板；仅在 --image 为非全屏裁图时通过 --roi 手动指定。
LEGACY_MOSAIC_ROI = (70, 120, 466, 652)


def _longest_band(prof, thr, minlen):
    """投影曲线中连续超过阈值的最长区间 (start, end)。"""
    best = cur = None
    for i, v in enumerate(prof > thr):
        if v:
            cur = [i, i] if cur is None else [cur[0], i]
        else:
            if cur and cur[1] - cur[0] >= minlen and (best is None or cur[1] - cur[0] > best[1] - best[0]):
                best = cur
            cur = None
    if cur and cur[1] - cur[0] >= minlen and (best is None or cur[1] - cur[0] > best[1] - best[0]):
        best = cur
    return tuple(best) if best else None


def detect_board_roi(img):
    """自动检测完整马赛克画板 ROI，返回 (x0, y0, x1, y1)。

    画板是全图最大的高饱和/深色矩形区域。先按列投影确定左右边界，
    再在该列带内按行投影取最长连续带作为上下边界。
    已用关卡 93 全屏截图（1080x2400）验证：得到 (166,267,921,1297)，
    完整覆盖 38x51 格，而旧写死 ROI (70,120,466,652) 只框到左上角。
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = ((hsv[:, :, 1] > 90) | (hsv[:, :, 2] < 80)).astype(np.uint8)
    xr = _longest_band(mask.mean(axis=0), 0.15, 200)
    if xr is None:
        return None
    yr = _longest_band(mask[:, xr[0]:xr[1] + 1].mean(axis=1), 0.10, 300)
    if yr is None:
        return None
    return (int(xr[0]), int(yr[0]), int(xr[1]), int(yr[1]))


def _align_phase(img, x0, y0, x1, y1, step):
    """用格心饱和度和最大准则对齐 (x, y) 相位偏移（相对 ROI 左上角）。"""
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
    ox = max(range(step), key=score_x)
    oy = max(range(step), key=score_y)
    return ox, oy


def _mode_color(patch):
    """区域内量化众数色，再在该簇内取中位，抗描边/高光。"""
    q = (patch // 8).reshape(-1, 3)
    key = (q[:, 0].astype(np.int32) * 4096
           + q[:, 1].astype(np.int32) * 64 + q[:, 2].astype(np.int32))
    u, c = np.unique(key, return_counts=True)
    k = int(u[c.argmax()])
    b, g, r = (k // 4096) * 8, ((k // 64) % 64) * 8, (k % 64) * 8
    m = (q[:, 0] == b // 8) & (q[:, 1] == g // 8) & (q[:, 2] == r // 8)
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
        return float(len(sig) / k) if k > 0 else 20.0

    return period(sx), period(sy)


def calibrate(img, k=14, ox_off=None, oy_off=None):
    # 自动检测完整画板 ROI（含最左右列/最上下行），避免漏采边缘色。
    detected = detect_board_roi(img)
    if detected is None:
        return {"error": "未能自动检测马赛克画板 ROI"}
    x0, y0, x1, y1 = detected
    roi = img[y0:y1, x0:x1]
    px, py = _grid_period(roi)
    sx_step, sy_step = max(1, int(round(px))), max(1, int(round(py)))
    # 格心相位：未显式指定时用饱和度最大准则自动对齐，避免格线/高光采样。
    if ox_off is None or oy_off is None:
        aox, aoy = _align_phase(img, x0, y0, x1, y1, sx_step)
        ox_off = aox if ox_off is None else ox_off
        oy_off = aoy if oy_off is None else oy_off
    cx0 = x0 + ox_off
    cy0 = y0 + oy_off
    samples = []
    cy = cy0
    while cy + 4 < y1:
        cx = cx0
        while cx + 4 < x1:
            patch = img[cy - 4:cy + 5, cx - 4:cx + 5]
            if patch.shape[:2] == (9, 9):
                samples.append(_mode_color(patch))
            cx += sx_step
        cy += sy_step
    samples = np.array(samples, np.float32)
    if len(samples) < 20:
        return {"error": "采样格数不足", "cells": len(samples)}

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
            "current_class": sv.hue_name(int(hsv[0]), int(hsv[1]), int(hsv[2])),
        })
    return {
        "board_roi": [x0, y0, x1, y1],
        "cell_offset": [ox_off, oy_off],
        "cells": len(samples),
        "grid_step_px": [round(float(px), 2), round(float(py), 2)],
        "palette": palette,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", help="马赛克拼图截图；省略则实时抓图")
    ap.add_argument("--device")
    ap.add_argument("--k", type=int, default=14)
    ap.add_argument("--ox", type=int, default=None, help="格心相对 ROI 左边的 x 偏移；省略则自动对齐")
    ap.add_argument("--oy", type=int, default=None, help="格心相对 ROI 上边的 y 偏移；省略则自动对齐")
    ap.add_argument("--output", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "palette.json"))
    args = ap.parse_args()

    if args.image:
        img = cv2.imread(args.image)
    else:
        img = sv.grab(args.device)
    if img is None:
        print("抓图/读图失败")
        return

    result = calibrate(img, args.k, args.ox, args.oy)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print("saved", args.output)


if __name__ == "__main__":
    main()
