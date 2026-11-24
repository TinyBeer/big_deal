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
import os
import sys

import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))  # tools/
import slots_vision as sv  # noqa: E402
from common import palette_calibrate_core as core  # noqa: E402

# 马赛克目标图 ROI（1080x2400 基准，按比例缩放）。
# 已废弃写死坐标：画面缩放/位移会漏采边缘色（如玫红）。
# 现在默认自动检测完整画板；仅在 --image 为非全屏裁图时通过 --roi 手动指定。
LEGACY_MOSAIC_ROI = (70, 120, 466, 652)


def detect_board_roi(img):
    """完整马赛克画板 ROI（关卡 93 实测 166,267,921,1297），失败返回 None。"""
    return core.detect_color_band_roi(
        img, sat_thr=90, val_thr=80,
        x_thr=0.15, x_minlen=200,
        y_thr=0.10, y_minlen=300)


def calibrate(img, k=14, ox_off=None, oy_off=None):
    """马赛克格全部入池；K 与输出顺序保持历史口径。"""
    return core.calibrate_palette(
        img, detect_board_roi, sv.hue_name,
        k=k, ox_off=ox_off, oy_off=oy_off,
        step_min=1, step_max=None, period_fallback=20.0,
        sample_filter=None, clamp_k=False, issues=False,
        key_order=("board_roi", "cell_offset", "cells", "grid_step_px", "palette"),
        error_key_order=("error", "cells"),
        empty_roi_error="未能自动检测马赛克画板 ROI")


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
    print(core.write_palette(result, args.output))
    print("saved", args.output)


if __name__ == "__main__":
    main()
