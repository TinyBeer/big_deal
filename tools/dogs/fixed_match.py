#!/usr/bin/env python3
"""固定位置模板匹配（优先）+ 轮廓 Hu 矩二次校验。

模板从已标注样本截图中截取：
- 狗窝：狗窝中间的头像圆形区域，100x100，圆形 mask；
- 廊道出口：出口槽位的狗全身，120x120， GrabCut + 颜色先验去除草地/架子背景。

识别时先与同尺寸模板做带 mask 的归一化互相关，只在模板分数够高且轮廓 Hu
矩距离够小时才采纳；否则返回 None，由调用方回退到原有颜色规则/特征匹配。
"""

import functools
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FIXED_DIR = os.path.join(HERE, "templates", "fixed")
SPECS_PATH = os.path.join(FIXED_DIR, "specs.json")
SIZES = {"exit": 120, "house": 100}
DEFAULT_SCORE = {"exit": 0.75, "house": 0.83}
DEFAULT_HU = {"exit": 0.35, "house": 0.60}
MIN_MARGIN = 0.04  # 最优与次优品种的色差分数差，太小则标未知


def load_specs(path=SPECS_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def circle_mask(size, inset=3):
    mask = np.zeros((size, size), np.uint8)
    cv2.circle(mask, (size // 2, size // 2), size // 2 - inset, 255, -1)
    return mask


def foreground_mask(patch):
    """从 120x120 出口裁片里分离狗本体，去掉草地/紫架子/天空背景。

    实机截图背景颜色固定，颜色先验 + 连通域比 GrabCut 更稳，也更快。
    """
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    bg = (((hue >= 25) & (hue <= 95) & (sat > 45) & (val > 105)) |
          ((hue >= 100) & (hue <= 165) & (sat > 35) & (val > 70)) |
          ((hue >= 85) & (hue <= 115) & (sat > 25) & (val > 180)))
    fg = (~bg).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return _center_components(fg, min_area=80, rx=0.35, ry=0.45)


def head_mask(patch, threshold=30):
    """狗窝头像圆形区域里，按与外圈底色的差异提取狗头轮廓。"""
    h, w = patch.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    r2 = (xx - w / 2) ** 2 + (yy - h / 2) ** 2
    outer = (h // 2 - 3) ** 2
    annulus = (r2 > (h // 2 - 12) ** 2) & (r2 < outer)
    bg = np.median(patch[annulus], axis=0)
    dist = np.linalg.norm(patch.astype(np.float32) - bg, axis=2)
    gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    mask = (((dist > threshold) | (gray < 110)) & (r2 < outer)).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return _center_components(mask, min_area=40, rx=0.30, ry=0.35)


def _center_components(mask, min_area, rx, ry):
    """只保留画面中心附近、面积够大的连通域，并填平内部空洞。"""
    h, w = mask.shape
    count, labels, stats, cents = cv2.connectedComponentsWithStats(mask, 8)
    keep = np.zeros_like(mask)
    for i in range(1, count):
        if stats[i, cv2.CC_STAT_AREA] < min_area:
            continue
        cx, cy = cents[i]
        if (labels[h // 2, w // 2] == i or
                (abs(cx - w / 2) < w * rx and abs(cy - h / 2) < h * ry)):
            keep[labels == i] = 1
    if not keep.any():
        return mask
    contours, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        cv2.drawContours(keep, [max(contours, key=cv2.contourArea)], -1, 1, -1)
    return keep


def crop_at(img, center, size):
    x, y = center
    h, w = img.shape[:2]
    x0, y0 = int(x) - size // 2, int(y) - size // 2
    x1, y1 = x0 + size, y0 + size
    if x0 < 0 or y0 < 0 or x1 > w or y1 > h:
        canvas = np.zeros((size, size, 3), img.dtype)
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(w, x1), min(h, y1)
        canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = img[sy0:sy1, sx0:sx1]
        return canvas
    return img[y0:y1, x0:x1].copy()


def extract_template(image_path, spec):
    """按 spec 从样本截图裁出一张带 alpha mask 的模板。"""
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("样本截图读取失败: " + image_path)
    kind = spec["kind"]
    size = int(spec.get("size", SIZES[kind]))
    patch = crop_at(img, spec["center"], size)
    mask = circle_mask(size) if kind == "house" else foreground_mask(patch)
    rgba = cv2.cvtColor(patch, cv2.COLOR_BGR2BGRA)
    rgba[:, :, 3] = np.where(mask > 0, 255, 0).astype(np.uint8)
    return rgba


def _largest_contour(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return max(contours, key=cv2.contourArea) if contours else None


def _hu_distance(mask_a, mask_b):
    ca, cb = _largest_contour(mask_a), _largest_contour(mask_b)
    if ca is None or cb is None:
        return 9.0
    return float(cv2.matchShapes(ca, cb, cv2.CONTOURS_MATCH_I1, 0.0))


def _masked_color_score(patch, tpl, patch_mask, tpl_mask):
    """mask 内平均颜色相似度：1.0 为完全一致，对固定机位比互相关更可分。"""
    mask = (patch_mask > 0) & (tpl_mask > 0)
    if int(mask.sum()) < 150:
        return 0.0
    diff = np.abs(patch.astype(np.float32) - tpl.astype(np.float32)).mean(axis=2)
    return 1.0 - float(diff[mask].mean()) / 255.0


class FixedTemplate:
    __slots__ = ("breed", "kind", "image", "mask", "shape_mask", "shape_area",
                 "contour")

    def __init__(self, breed, kind, image, mask):
        self.breed, self.kind = breed, kind
        self.image, self.mask = image, mask
        # 狗窝的 alpha 是圆形区域；Hu 矩校验用头轮廓，避免所有模板都是同一个圆
        self.shape_mask = head_mask(image) if kind == "house" else mask
        self.shape_area = int(self.shape_mask.sum())
        self.contour = _largest_contour(self.shape_mask)


class FixedMatcher:
    """固定槽位模板匹配；模板颜色分数优先，Hu 矩只做二次校验。"""

    def __init__(self, kind, templates, score_threshold=None, hu_threshold=None):
        self.kind = kind
        self.templates = templates
        self.score_threshold = DEFAULT_SCORE[kind] if score_threshold is None else score_threshold
        self.hu_threshold = DEFAULT_HU[kind] if hu_threshold is None else hu_threshold

    def match(self, patch, score_threshold=None, hu_threshold=None):
        if not self.templates or patch is None or patch.shape[:2] != \
                self.templates[0].image.shape[:2]:
            return None
        score_min = self.score_threshold if score_threshold is None else score_threshold
        hu_max = self.hu_threshold if hu_threshold is None else hu_threshold
        if self.kind == "house":
            color_mask, shape_mask = circle_mask(patch.shape[0]), head_mask(patch)
        else:
            color_mask = shape_mask = foreground_mask(patch)
        candidate = _largest_contour(shape_mask)
        shape_area = int(shape_mask.sum())
        scored = []
        for tpl in self.templates:
            score = _masked_color_score(patch, tpl.image, color_mask, tpl.mask)
            if (candidate is None or tpl.contour is None or
                    shape_area < 2000 or tpl.shape_area < 2000):
                hu = 0.0
            else:
                hu = _hu_distance(shape_mask, tpl.shape_mask)
            scored.append({"breed": tpl.breed, "score": score, "hu": hu})
        if not scored:
            return None
        # 先按品种取最高分，再比较品种间差距；同一品种的多个姿态不应互相压低 margin
        per_breed = {}
        for d in scored:
            if d["breed"] not in per_breed or d["score"] > per_breed[d["breed"]]["score"]:
                per_breed[d["breed"]] = d
        ranked = sorted(per_breed.values(), key=lambda d: -d["score"])
        best, second = ranked[0], (ranked[1] if len(ranked) > 1 else None)
        if best["score"] < score_min:
            return None
        if second is not None and best["score"] - second["score"] < MIN_MARGIN:
            return None
        verified = [d for d in scored
                    if d["breed"] == best["breed"] and d["hu"] <= hu_max and
                    d["score"] >= best["score"] - 0.05]
        if not verified:
            return None
        chosen = min(verified, key=lambda d: (d["hu"], -d["score"]))
        return {"breed": chosen["breed"], "score": round(best["score"], 3),
                "hu": round(chosen["hu"], 3), "method": "fixed+hu",
                "best": best}


def load_templates(kind, folder=None):
    folder = folder or os.path.join(FIXED_DIR, kind)
    out = []
    if not os.path.isdir(folder):
        return out
    for fn in sorted(os.listdir(folder)):
        if not fn.lower().endswith(".png"):
            continue
        img = cv2.imread(os.path.join(folder, fn), cv2.IMREAD_UNCHANGED)
        if img is None:
            continue
        if img.shape[2] == 4:
            bgr, mask = img[:, :, :3], img[:, :, 3]
        else:
            bgr, mask = img, np.full(img.shape[:2], 255, np.uint8)
        breed = fn.split("__")[0].rsplit("_v", 1)[0]
        out.append(FixedTemplate(breed, kind, bgr, (mask > 0).astype(np.uint8)))
    return out


@functools.lru_cache(maxsize=None)
def get_matcher(kind):
    return FixedMatcher(kind, load_templates(kind))
