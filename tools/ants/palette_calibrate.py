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
import os
import sys

import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))  # tools/
from ants_vision import classify_hsv, grab  # noqa: E402
from common import palette_calibrate_core as core  # noqa: E402

# 1080x2400 基准下像素画的大致范围，仅作 ROI 自动检测失败时的兜底
FALLBACK_BOARD = (86, 302, 1006, 1314)
UPPER_LIMIT = 1500  # 只扫上半屏，避免把槽位/候选块圈进来


def detect_board_roi(img):
    """像素画 ROI：只扫上半屏，失败回退到 1080x2400 基准坐标。"""
    h, w = img.shape[:2]
    sx, sy = w / core.REF_W, h / core.REF_H
    upper = img[:min(h, int(UPPER_LIMIT * sy))]
    found = core.detect_color_band_roi(
        upper, sat_thr=85, val_thr=110,
        x_thr=0.15, x_minlen=int(250 * sx),
        y_thr=0.12, y_minlen=int(300 * sy),
        close_kernel=11,
        min_w=300 * sx, min_h=300 * sy)
    if found:
        return found
    return tuple(int(v * (sx if i % 2 == 0 else sy))
                 for i, v in enumerate(FALLBACK_BOARD))


def calibrate(img, k=14, ox_off=None, oy_off=None):
    """颜色池策略：米色空格不入池，K 收敛到样本数，输出分类器问题诊断。"""
    return core.calibrate_palette(
        img, detect_board_roi, classify_hsv,
        k=k, ox_off=ox_off, oy_off=oy_off,
        step_min=8, step_max=40, period_fallback=23.0,
        sample_filter=lambda bgr, hsv: classify_hsv(
            int(hsv[0]), int(hsv[1]), int(hsv[2])) is not None,
        clamp_k=True, issues=True,
        key_order=("board_roi", "cell_offset", "grid_step_px", "cells",
                   "palette", "issues"),
        error_key_order=("error", "cells", "board_roi"),
        empty_roi_error="像素画 ROI 为空")


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
    print(core.write_palette(result, args.output))
    print("saved", args.output)


if __name__ == "__main__":
    main()
