#!/usr/bin/env python3
"""共用：从像素画/马赛克画板标定调色板的算法骨架。

只放无业务语义的纯算法：投影 band 检测、格距 FFT、相位对齐、格心众数色、
KMeans 与 JSON 组装。各游戏脚本负责自己的 ROI 策略、采样过滤、分类器、
K 的策略和诊断输出，通过参数注入进来。
"""
import json
import os

import cv2
import numpy as np

REF_W, REF_H = 1080, 2400
PATCH_HALF = 4
MIN_SAMPLES = 20


def longest_band(prof, thr, minlen):
    """投影曲线中连续超过阈值的最长区间 (start, end)。"""
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


def detect_color_band_roi(img, sat_thr, val_thr, x_thr, x_minlen,
                          y_thr, y_minlen, close_kernel=0, min_w=0, min_h=0):
    """按高饱和/深色掩膜的最大彩色带检测矩形 ROI，失败返回 None。

    sat_thr/val_thr : 掩膜条件 (S > sat_thr) | (V < val_thr)
    x/y_thr/minlen : 行列投影的阈值与最短带长度
    close_kernel   : >0 时先做同尺寸形态学闭运算
    min_w/min_h    : 找到的带还需满足的宽度/高度下限
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = ((hsv[:, :, 1] > sat_thr) | (hsv[:, :, 2] < val_thr)).astype(np.uint8)
    if close_kernel:
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                                np.ones((close_kernel, close_kernel), np.uint8))
    xr = longest_band(mask.mean(axis=0), x_thr, x_minlen)
    if xr is None:
        return None
    yr = longest_band(mask[:, xr[0]:xr[1] + 1].mean(axis=1), y_thr, y_minlen)
    if yr is None:
        return None
    if (xr[1] - xr[0]) <= min_w or (yr[1] - yr[0]) <= min_h:
        return None
    return (int(xr[0]), int(yr[0]), int(xr[1]), int(yr[1]))


def align_phase(img, x0, y0, x1, y1, step, inset=5):
    """用格心饱和度和最大准则对齐 (x, y) 相位偏移（相对 ROI 左上角）。"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    def score_x(p):
        vals = [int(hsv[cy, cx, 1])
                for cy in range(y0 + inset, y1 - inset, step)
                for cx in range(x0 + p, x1 - inset, step)]
        return float(np.mean(vals)) if vals else 0.0

    def score_y(p):
        vals = [int(hsv[cy, cx, 1])
                for cy in range(y0 + p, y1 - inset, step)
                for cx in range(x0 + inset, x1 - inset, step)]
        return float(np.mean(vals)) if vals else 0.0

    return max(range(step), key=score_x), max(range(step), key=score_y)


def mode_color(patch, quant=8):
    """量化众数色，再在该簇内取中位，抗描边/高光。quant=8 为历史口径。"""
    q = (patch // quant).reshape(-1, 3)
    key = (q[:, 0].astype(np.int32) * 4096
           + q[:, 1].astype(np.int32) * 64 + q[:, 2].astype(np.int32))
    u, c = np.unique(key, return_counts=True)
    k = int(u[c.argmax()])
    b, g, r = (k // 4096) * quant, ((k // 64) % 64) * quant, (k % 64) * quant
    m = ((q[:, 0] == b // quant) & (q[:, 1] == g // quant) & (q[:, 2] == r // quant))
    return np.median(patch.reshape(-1, 3)[m], axis=0).astype(np.uint8)


def grid_period(roi, fallback=20.0):
    """Sobel 投影 + FFT 估 x/y 格距，FFT 无峰时用 fallback。"""
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    sx = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)).mean(axis=0)
    sy = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)).mean(axis=1)

    def period(sig):
        s = sig - sig.mean()
        f = np.abs(np.fft.rfft(s))
        f[0] = 0
        k = int(np.argmax(f))
        return float(len(sig) / k) if k > 0 else fallback

    return period(sx), period(sy)


def clamp_step(value, lo, hi=None):
    v = int(round(value))
    if hi is not None:
        v = min(hi, v)
    return max(lo, v)


def _ordered(data, key_order):
    if not key_order:
        return data
    return {key: data[key] for key in key_order if key in data}


def calibrate_palette(img, detect_roi, classify_fn, *, k=14,
                      ox_off=None, oy_off=None, step_min=1, step_max=None,
                      period_fallback=20.0, sample_filter=None,
                      clamp_k=False, issues=False, key_order=None,
                      error_key_order=None, empty_roi_error="ROI 为空"):
    """标定主流程。detect_roi(img) 返回 (x0,y0,x1,y1) 或 None。

    sample_filter(bgr, hsv) 返回 True 才把该格纳入颜色池（ants 用来过滤米色空格）；
    classify_fn(h, s, v) 给每个聚类中心写 current_class；
    clamp_k / issues / key_order 控制各游戏原有的输出差异。
    """
    detected = detect_roi(img)
    if not detected:
        return _ordered({"error": empty_roi_error}, error_key_order)
    x0, y0, x1, y1 = detected
    roi = img[y0:y1, x0:x1]
    if roi.size == 0:
        return _ordered({"error": empty_roi_error}, error_key_order)

    px, py = grid_period(roi, period_fallback)
    sx_step = clamp_step(px, step_min, step_max)
    sy_step = clamp_step(py, step_min, step_max)
    if ox_off is None or oy_off is None:
        aox, aoy = align_phase(img, x0, y0, x1, y1, sx_step)
        ox_off = aox if ox_off is None else ox_off
        oy_off = aoy if oy_off is None else oy_off

    samples = []
    cy = y0 + oy_off
    while cy + PATCH_HALF < y1:
        cx = x0 + ox_off
        while cx + PATCH_HALF < x1:
            patch = img[cy - PATCH_HALF:cy + PATCH_HALF + 1,
                        cx - PATCH_HALF:cx + PATCH_HALF + 1]
            if patch.shape[:2] == (PATCH_HALF * 2 + 1, PATCH_HALF * 2 + 1):
                bgr = mode_color(patch)
                hsv = cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2HSV)[0, 0]
                if sample_filter is None or sample_filter(bgr, hsv):
                    samples.append(bgr)
            cx += sx_step
        cy += sy_step

    if len(samples) < MIN_SAMPLES:
        error = {"error": "采样格数不足", "cells": len(samples)}
        if error_key_order and "board_roi" in error_key_order:
            error["board_roi"] = [x0, y0, x1, y1]
        return _ordered(error, error_key_order)

    samples = np.array(samples, np.float32)
    kk = max(2, min(k, len(samples))) if clamp_k else k
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
    _, lab, cents = cv2.kmeans(samples, kk, None, crit, 30, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(lab.ravel())
    order = np.argsort(-counts)
    palette = []
    for i in order:
        b, g, r = [int(v) for v in cents[i]]
        hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0, 0]
        h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])
        palette.append({
            "rgb": [r, g, b],
            "hex": "#%02X%02X%02X" % (r, g, b),
            "hsv": [h, s, v],
            "count": int(counts[i]),
            "ratio": round(float(counts[i]) / len(samples), 4),
            "current_class": classify_fn(h, s, v),
        })

    result = {
        "board_roi": [x0, y0, x1, y1],
        "cell_offset": [ox_off, oy_off],
        "grid_step_px": [round(float(px), 2), round(float(py), 2)],
        "cells": len(samples),
        "palette": palette,
    }
    if issues:
        groups = {}
        for p in palette:
            groups.setdefault(p["current_class"], []).append(p["hex"])
        found = {}
        for cls, hexes in groups.items():
            if cls == "unknown" or len(hexes) > 1:
                found[str(cls)] = hexes
        result["issues"] = found
    return _ordered(result, key_order)


def write_palette(result, path):
    """写 JSON（自动建目录）并返回写出的文本。"""
    text = json.dumps(result, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return text
