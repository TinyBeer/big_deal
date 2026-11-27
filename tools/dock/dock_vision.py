#!/usr/bin/env python3
"""螺丝接驳位解锁助手 · 视觉识别。

适用游戏：类似 ring / parking 的「停车接客」类消除，顶部有一排接驳位，
其中若干位带紫色「解锁」按钮（按钮内含白色螺丝图标 + 橙色螺丝头）。

识别策略（不依赖颜色抖动/背景）：
  1. 槽位行在画面中部、分隔条之上，先框定该横条 ROI；
  2. 「解锁」按钮的橙色螺丝头是整条 ROI 里唯一的高饱和橙色小块，
     且被白色圆角图标托底 —— 面积/尺寸/方形度 + 周围白色占比三重过滤，
     可排除叉车模型上的同类橙色螺丝（没有白色托底、尺寸不一）；
  3. 福利弹窗靠「领取」黄色按钮模板命中；游戏内靠底部「刷新」按钮模板确认。

坐标基于 1080x2400，其余分辨率按比例换算。
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
from common.screen import grab  # noqa: E402

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# 槽位横条 ROI（相对画面宽高）：上边界到分隔条上方
SLOT_BAND = (0.0, 0.33, 1.0, 0.50)

# 橙色螺丝头 HSV 范围
SCREW_HUE = (8, 30)
SCREW_SMIN = 150
SCREW_VMIN = 150
SCREW_AREA = (150, 900)
SCREW_SIDE = (13, 36)
SCREW_FILL = 0.45      # 连通域填充率下限(方形度)
WHITE_RING = 0.22      # 周围一圈白色占比下限


def _px(img, box):
    h, w = img.shape[:2]
    x0, y0, x1, y1 = box
    return int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)


def _load(name):
    p = os.path.join(TEMPLATE_DIR, name)
    img = cv2.imread(p)
    if img is None:
        raise RuntimeError("缺少模板: %s" % p)
    return img


def _match(img, tpl, threshold, region=None, scales=None):
    """模板匹配，返回 [(cx, cy, score)]，按分数降序、非极大抑制。"""
    if region:
        x0, y0, x1, y1 = region
        search = img[y0:y1, x0:x1]
    else:
        x0 = y0 = 0
        search = img
    if search is None or search.size == 0:
        return []
    if tpl.shape[0] > search.shape[0] or tpl.shape[1] > search.shape[1]:
        return []
    hits = []
    for s in (scales or [1.0]):
        t = tpl if s == 1.0 else cv2.resize(
            tpl, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        if t.shape[0] > search.shape[0] or t.shape[1] > search.shape[1]:
            continue
        res = cv2.matchTemplate(search, t, cv2.TM_CCOEFF_NORMED)
        for y, x in zip(*np.where(res >= threshold)):
            hits.append((float(x + t.shape[1] / 2 + x0),
                         float(y + t.shape[0] / 2 + y0),
                         float(res[y, x]), t.shape[1], t.shape[0]))
    hits.sort(key=lambda v: -v[2])
    out = []
    for cx, cy, sc, tw, th in hits:
        if all(abs(cx - a) > tw * 0.5 or abs(cy - b) > th * 0.5 for a, b, _ in out):
            out.append((cx, cy, sc))
    return out


def _ring_stats(hsv, cx, cy, r1, r2):
    """以 (cx,cy) 为中心、半径 r1~r2 的圆环内各颜色占比。"""
    pad = int(r2) + 2
    patch = hsv[max(0, cy - pad):cy + pad + 1, max(0, cx - pad):cx + pad + 1]
    hh, ww = patch.shape[:2]
    if hh != 2 * pad + 1 or ww != 2 * pad + 1:
        return None
    ys, xs = np.mgrid[-pad:pad + 1, -pad:pad + 1]
    rr = np.sqrt(xs ** 2 + ys ** 2)
    m = (rr >= r1) & (rr <= r2)
    if not m.any():
        return None
    px = patch[m]
    hue, sat, val = px[:, 0], px[:, 1], px[:, 2]
    return {
        "white": float(((sat < 60) & (val > 215)).mean()),
        "orange": float(((hue >= SCREW_HUE[0]) & (hue <= SCREW_HUE[1])
                         & (sat > 150) & (val > 150)).mean()),
        "purple": float(((hue >= 100) & (hue <= 145) & (sat < 90)
                         & (val > 105) & (val < 235)).mean()),
    }


def detect_unlock_buttons(img, debug=None):
    """返回待解锁接驳位按钮的点击点（按 x 从左到右）。

    「解锁」按钮 = 白螺丝图标（橙色螺丝头 + 白色圆角托底）+ 灰紫底按钮。
    车顶也有同尺寸的橙色小圆点（实测面积/边长完全一致），因此不能只看橙色块，
    必须做两层环形校验：
      r1(13~20px)：应为白色托底（白 ≥0.75、橙 ≤0.12）—— 车顶圆点外圈是橙色车身；
      r2(21~30px)：应为灰紫按钮底（紫 ≥0.25、橙 ≤0.15）。
    """
    h, w = img.shape[:2]
    x0, y0, x1, y1 = _px(img, SLOT_BAND)
    roi = img[y0:y1, x0:x1]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    m = ((hue >= SCREW_HUE[0]) & (hue <= SCREW_HUE[1])
         & (sat > SCREW_SMIN) & (val > SCREW_VMIN)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, cents = cv2.connectedComponentsWithStats(m)

    pts = []
    rejected = []
    for i in range(1, n):
        bx, by, bw, bh, area = stats[i]
        if not (SCREW_AREA[0] <= area <= SCREW_AREA[1]):
            continue
        if not (SCREW_SIDE[0] <= bw <= SCREW_SIDE[1] and
                SCREW_SIDE[0] <= bh <= SCREW_SIDE[1]):
            continue
        if not (0.6 <= bw / float(bh) <= 1.7):
            continue
        if area / float(bw * bh) < SCREW_FILL:
            continue
        cx, cy = int(cents[i][0]), int(cents[i][1])
        inner = _ring_stats(hsv, cx, cy, 13, 20)
        outer = _ring_stats(hsv, cx, cy, 21, 30)
        if not inner or not outer:
            continue
        # 螺丝图标是白色圆角方块(~60px)套橙色螺丝头(~22px)：
        #   r13~20 已完全落在白块内 -> 白≈1.0、橙≈0（车顶圆点外圈仍是橙色车身）
        #   r21~30 仍是白块或其外的灰紫按钮底 -> 白或紫占多数，几乎没有橙色
        ok = (inner["white"] >= 0.85 and inner["orange"] <= 0.05 and
              outer["orange"] <= 0.10 and outer["white"] >= 0.55)
        if not ok:
            rejected.append({"x": cx + x0, "y": cy + y0,
                             "inner": {k: round(v, 2) for k, v in inner.items()},
                             "outer": {k: round(v, 2) for k, v in outer.items()}})
            continue
        pts.append({"x": cx + x0, "y": cy + y0, "w": int(bw), "h": int(bh),
                    "score": round(inner["white"], 3)})
    pts.sort(key=lambda p: p["x"])
    # 同排按钮间距 ~120px，做一次最小间距去重
    dedup = []
    for p in pts:
        if all(abs(p["x"] - q["x"]) > 60 for q in dedup):
            dedup.append(p)
    if debug is not None:
        debug["unlock_rejected"] = rejected
    return dedup


def find_claim(img, threshold=0.70):
    """福利弹窗的「领取（视频）」按钮，返回 (x, y, score) 或 None。"""
    hits = _match(img, _load("claim.png"), threshold,
                  region=(0, int(0.50 * img.shape[0]), img.shape[1], int(0.82 * img.shape[0])))
    return hits[0] if hits else None


def find_close(img, threshold=0.70):
    """福利/奖励弹窗右上角蓝色 X 按钮。"""
    h, w = img.shape[:2]
    hits = _match(img, _load("close_x.png"), threshold,
                  region=(int(0.75 * w), int(0.18 * h), w, int(0.42 * h)))
    return hits[0] if hits else None


def is_game(img, threshold=0.75, dim_ratio=0.75):
    """用底部「刷新」按钮判断是否已回到对局。

    弹窗会在整屏盖一层半透明黑幕，而 TM_CCOEFF_NORMED 对整体线性压暗不敏感
    （暗化后仍能匹配到 1.0），所以额外比较命中块与模板的平均亮度，
    明显偏暗即判定处于弹窗遮罩下、不算「回到对局」。
    """
    h, w = img.shape[:2]
    tpl = _load("game_mark.png")
    tpl_v = float(cv2.cvtColor(tpl, cv2.COLOR_BGR2HSV)[:, :, 2].mean())
    hits = _match(img, tpl, threshold,
                  region=(0, int(0.88 * h), int(0.5 * w), h))
    for cx, cy, _sc in hits:
        bx = int(cx - tpl.shape[1] / 2)
        by = int(cy - tpl.shape[0] / 2)
        patch = img[by:by + tpl.shape[0], bx:bx + tpl.shape[1]]
        if patch.shape[:2] != tpl.shape[:2]:
            continue
        v = float(cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)[:, :, 2].mean())
        if v >= tpl_v * dim_ratio:
            return True
    return False


def find_return(img, threshold=0.70):
    """广告落地页的「点击立即返回」红袋按钮。"""
    h, w = img.shape[:2]
    hits = _match(img, _load("return_tag.png"), threshold,
                  region=(int(0.70 * w), int(0.15 * h), w, int(0.40 * h)))
    return hits[0] if hits else None


def analyze(img):
    """一次抓图的完整判断：弹窗优先，其次游戏内的解锁按钮。"""
    claim = find_claim(img)
    close = find_close(img)
    popup = bool(claim or close)
    buttons = [] if popup else detect_unlock_buttons(img)
    return {"unlock": buttons, "count": len(buttons),
            "game": False if popup else is_game(img),
            "popup": popup, "claim": claim, "close": close}


def annotate(img, res):
    vis = img.copy()
    for i, b in enumerate(res["unlock"], 1):
        cv2.rectangle(vis, (b["x"] - 40, b["y"] - 40), (b["x"] + 40, b["y"] + 40),
                      (0, 0, 255), 3)
        cv2.putText(vis, str(i), (b["x"] - 14, b["y"] + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 5)
        cv2.putText(vis, str(i), (b["x"] - 14, b["y"] + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 2)
    if res["claim"]:
        cx, cy, sc = res["claim"]
        cv2.rectangle(vis, (int(cx) - 200, int(cy) - 60), (int(cx) + 200, int(cy) + 60),
                      (0, 200, 0), 3)
        cv2.putText(vis, "claim %.2f" % sc, (int(cx) - 190, int(cy) - 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 120, 0), 2)
    cv2.putText(vis, "unlock=%d game=%s popup=%s" % (
        res["count"], res["game"], res.get("popup")),
                (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    return vis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    ap.add_argument("--device")
    ap.add_argument("--output", default="outputs/dock_annotated.png")
    args = ap.parse_args()

    img = cv2.imread(args.image) if args.image else grab(args.device)
    if img is None:
        print("抓图失败")
        return
    res = analyze(img)
    print(json.dumps({"unlock": [(b["x"], b["y"]) for b in res["unlock"]],
                      "count": res["count"], "game": res["game"],
                      "claim": bool(res["claim"])}, ensure_ascii=False))
    out = annotate(img, res)
    cv2.imwrite(args.output, out)
    print("saved", args.output)


if __name__ == "__main__":
    main()
