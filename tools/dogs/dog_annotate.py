#!/usr/bin/env python3
"""狗狗三消画面标注：识别大/小狗窝、廊道出口的狗品种。

用法：
  python tools/dogs/dog_annotate.py                       # adb 抓当前画面
  python tools/dogs/dog_annotate.py --image shot.png      # 标注本地截图
  python tools/dogs/dog_annotate.py --once --output outputs/dog_annotated.png

只做识别与标注，不点击。紫蛋/冰蛋按规则忽略（紫蛋到出口会变狗，冰蛋消除后会变狗）。
"""

import argparse
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import fixed_match

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
from common.screen import grab as _adb_grab  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LOCKED_TEMPLATE = os.path.join(HERE, "templates", "house", "locked.png")
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

BIG_CENTERS = [(165, 320), (420, 320), (675, 320), (930, 320)]
# 用 Hough 圆检测确定的头像圆心，裁片恰好包裹圆形区域（半径约 50）
HOUSE_AVATAR_CENTERS = [(185, 294), (429, 294), (673, 294), (917, 294)]
SMALL_CENTERS = [(85, 535), (220, 535), (365, 535), (510, 535),
                 (660, 535), (790, 535), (930, 535)]

BREED_CN = {
    "shiba_orange": "橙白柴犬",
    "husky_black": "黑白哈士奇",
    "samoyed_white": "白色小狗",
    "collie_blackwhite": "黑白边牧",
    "pug_beige": "巴哥",
    "beagle_orangewhite": "橙白比格",
    "boston_blackwhite": "黑白波士顿梗",
    "poodle_brown": "棕色泰迪",
    "terrier_gray": "灰白梗",
}
BREED_SHORT = {
    "shiba_orange": "橙柴", "husky_black": "哈士奇", "samoyed_white": "白狗",
    "collie_blackwhite": "边牧", "pug_beige": "巴哥", "beagle_orangewhite": "比格",
    "boston_blackwhite": "波士顿梗", "poodle_brown": "泰迪", "terrier_gray": "灰梗",
}
PALETTE = [(60, 200, 120), (255, 160, 40), (80, 180, 255), (255, 100, 160),
           (180, 130, 255), (60, 210, 210), (255, 220, 80), (140, 200, 90),
           (230, 120, 90)]


ROWS = (930, 1132, 1324, 1534, 1740)
LEFT_CENTERS = (415, 285, 170, 55)
RIGHT_CENTERS = (635, 765, 895, 1020)


def grab(serial=None):
    return _adb_grab(serial, check=True)


def detect_rows(img):
    """从紫蓝色廊道架子的水平投影定位所有行，包含新解锁的廊道。"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    shelf = (h >= 110) & (h <= 145) & (s > 60) & (v > 100)
    h_img, w_img = shelf.shape
    proj = shelf[:, 40:min(480, w_img)].mean(axis=1) + \
           shelf[:, 600:min(1040, w_img)].mean(axis=1)
    ys = [y for y in range(850, min(2100, h_img)) if proj[y] > 0.9]
    groups = []
    for y in ys:
        if groups and y - groups[-1][-1] <= 4:
            groups[-1].append(y)
        else:
            groups.append([y])
    rows = [int((g[0] + g[-1]) / 2 - 100) for g in groups
            if 850 <= (g[0] + g[-1]) / 2 <= 2050]
    merged = []
    for row in rows:
        if merged and row - merged[-1] < 80:
            continue
        merged.append(row)
    return merged if len(merged) >= 4 else list(ROWS)


def color_fractions(patch):
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    white = (v > 200) & (s < 45)
    black = v < 75
    orange = (h >= 5) & (h <= 25) & (s > 100) & (v > 120)
    brown = (h >= 8) & (h <= 28) & (s > 70) & (v > 60) & (v < 170)
    gray = (s < 45) & (v >= 80) & (v <= 200)
    blue = (h >= 85) & (h <= 115) & (s > 70) & (v > 100)
    return {"white": float(white.mean()), "black": float(black.mean()),
            "orange": float(orange.mean()), "brown": float(brown.mean()),
            "gray": float(gray.mean()), "blue": float(blue.mean())}


def egg_label(patch):
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    sat, val, hue = hsv[:, :, 1], hsv[:, :, 2], hsv[:, :, 0]
    sel = (sat > 55) & (val > 90)
    if sel.sum() < patch.shape[0] * patch.shape[1] * 0.12:
        return None
    med = float(np.median(hue[sel]))
    if 125 <= med <= 175:
        return "紫蛋"
    ice = (hue >= 85) & (hue <= 115) & (sat >= 25) & (sat <= 120) & (val > 150)
    if ice.mean() > 0.18:
        return "冰蛋"
    return None


def occupied(patch):
    if egg_label(patch):
        return True
    f = color_fractions(patch)
    return (f["white"] + f["black"] + f["orange"] + f["brown"] + f["gray"]) > 0.28


def find_exit_slots(img):
    """从中间往外扫描候选槽位，第一个有狗/蛋的槽位就是廊道出口。"""
    h, w = img.shape[:2]
    slots = []
    for row, cy in enumerate(detect_rows(img)):
        for side, centers in (("左", LEFT_CENTERS), ("右", RIGHT_CENTERS)):
            chosen = None
            for cx in centers:
                x0, x1 = max(0, cx - 55), min(w, cx + 55)
                y0, y1 = max(0, cy - 55), min(h, cy + 55)
                if occupied(img[y0:y1, x0:x1]):
                    chosen = {"x": cx, "y": cy, "w": 110, "h": 110}
                    break
            if chosen is None:
                chosen = {"x": centers[0], "y": cy, "w": 110, "h": 110}
            chosen.update({"row": row + 1, "side": side})
            slots.append(chosen)
    return slots


def is_locked(patch, purple=False):
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    sat, val, hue = hsv[:, :, 1], hsv[:, :, 2], hsv[:, :, 0]
    if purple:
        sel = sat > 60
        return bool(sel.sum() and np.median(hue[sel]) > 70 and
                    float(val.mean()) < 220)
    gray = (sat < 35) & (val > 110) & (val < 215)
    return bool(float(gray.mean()) > 0.45)


def classify_exit(slot, img, matcher):
    """固定模板 + Hu 校验；未命中就标未知，不再使用旧的颜色规则。"""
    size = fixed_match.SIZES["exit"]
    patch = fixed_match.crop_at(img, (slot["x"], slot["y"]), size)
    egg = egg_label(patch)
    if egg:
        return {"breed": None, "label": egg, "score": 0.0, "method": "egg"}
    hit = matcher.match(patch)
    if hit:
        return {"breed": hit["breed"], "label": hit["breed"],
                "score": hit["score"], "method": hit["method"]}
    return {"breed": None, "label": "未知", "score": 0.0, "method": "unknown"}


def analyze(img):
    locked_tpl = cv2.imread(LOCKED_TEMPLATE, cv2.IMREAD_COLOR)
    exit_matcher = fixed_match.get_matcher("exit")
    house_matcher = fixed_match.get_matcher("house")

    dogs = []
    for slot in find_exit_slots(img):
        result = classify_exit(slot, img, exit_matcher)
        dogs.append({"breed": result["breed"], "label": result["label"],
                     "score": result["score"], "method": result["method"],
                     "x": slot["x"], "y": slot["y"], "w": slot["w"], "h": slot["h"],
                     "row": slot["row"], "side": slot["side"], "exit": True})

    houses = []
    for i, (x, y) in enumerate(BIG_CENTERS, 1):
        patch = img[max(0, y - 95):y + 95, max(0, x - 95):x + 95]
        locked = False
        if locked_tpl is not None and locked_tpl.shape[0] <= patch.shape[0] \
                and locked_tpl.shape[1] <= patch.shape[1]:
            locked = float(cv2.matchTemplate(
                patch, locked_tpl, cv2.TM_CCOEFF_NORMED).max()) >= 0.72
        if locked:
            houses.append({"idx": i, "x": x, "y": y, "label": "未解锁", "score": None})
            continue
        avatar = fixed_match.crop_at(img, HOUSE_AVATAR_CENTERS[i - 1],
                                     fixed_match.SIZES["house"])
        hit = house_matcher.match(avatar)
        breed, score = (hit["breed"], hit["score"]) if hit else (None, 0.0)
        houses.append({"idx": i, "x": x, "y": y,
                       "label": BREED_CN.get(breed, breed or "未知"), "score": score})

    smalls = []
    for i, (x, y) in enumerate(SMALL_CENTERS, 1):
        patch = img[y - 48:y + 48, max(0, x - 48):x + 48]
        if is_locked(patch, purple=True):
            smalls.append({"idx": i, "x": x, "y": y, "label": "未解锁", "score": None})
            continue
        # 小狗窝只判状态，不识别品种：白/黑/灰是狗，橙色筐本身不算有狗
        inner = img[y - 30:y + 30, max(0, x - 30):x + 30]
        frac = color_fractions(inner)
        filled = (frac["white"] > 0.42 or frac["black"] > 0.12 or
                  frac["gray"] > 0.25)
        smalls.append({"idx": i, "x": x, "y": y,
                       "label": "有狗" if filled else "空", "score": None})
    return {"houses": houses, "smalls": smalls, "dogs": dogs}


def annotate(img, result):
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    canvas = Image.fromarray(rgb)
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT_PATH, 24)
    small_font = ImageFont.truetype(FONT_PATH, 20)

    def text(x, y, s, color=(255, 255, 255), f=font):
        draw.text((x + 1, y + 1), s, font=f, fill=(0, 0, 0))
        draw.text((x, y), s, font=f, fill=color)

    for h in result["houses"]:
        color = (150, 150, 150) if h["label"] == "未解锁" else (255, 120, 40)
        draw.rectangle((h["x"] - 70, h["y"] - 75, h["x"] + 70, h["y"] + 75),
                       outline=color, width=4)
        hlabel = h["label"] if h["label"] == "未解锁" else BREED_SHORT.get(
            next((k for k, v in BREED_CN.items() if v == h["label"]), ""), h["label"])
        text(h["x"] - 60, h["y"] - 105, "窝%d:%s" % (h["idx"], hlabel), color, small_font)
    for s in result["smalls"]:
        color = (150, 150, 150) if s["label"] == "未解锁" else (255, 200, 40)
        draw.rectangle((s["x"] - 48, s["y"] - 48, s["x"] + 48, s["y"] + 48),
                       outline=color, width=3)
        slabel = s["label"] if s["label"] in ("未解锁", "空", "有狗") else BREED_SHORT.get(
            next((k for k, v in BREED_CN.items() if v == s["label"]), ""), s["label"])
        text(s["x"] - 30, s["y"] - 82, slabel, color, small_font)
    for i, d in enumerate(result["dogs"], 1):
        color = PALETTE[list(BREED_CN).index(d["breed"]) % len(PALETTE)] if d["breed"] in BREED_CN else (200, 200, 200)
        if d["label"] in ("紫蛋", "冰蛋", "未知"):
            color = (200, 200, 200)
        draw.rectangle((d["x"] - 55, d["y"] - 55, d["x"] + 55, d["y"] + 55),
                       outline=color, width=3)
        label = BREED_SHORT.get(d["breed"], d["label"])
        text(d["x"] - 40, d["y"] - 88, "%d★%s" % (i, label), color, small_font)
    draw.rectangle((520, 820, 560, 1660), outline=(255, 60, 60), width=2)
    text(520, 780, "中部出口", (255, 80, 80), small_font)
    return cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", help="本地截图路径；不传则 adb 抓图")
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--output", default="outputs/dog_annotated.png")
    args = ap.parse_args()
    img = cv2.imread(args.image) if args.image else grab(args.device)
    if img is None:
        raise SystemExit("图片读取失败: " + args.image)
    if float(img.mean()) < 12:
        raise SystemExit("画面几乎全黑（可能锁屏或广告），请先回到游戏界面")
    result = analyze(img)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    cv2.imwrite(args.output, annotate(img, result))
    summary = {
        "houses": [h["label"] for h in result["houses"]],
        "smalls": [s["label"] for s in result["smalls"]],
        "exit_dogs": [d["label"] for d in result["dogs"]],
        "dogs": len(result["dogs"]),
    }
    print(json.dumps(summary, ensure_ascii=False))
    print("saved:", args.output)


if __name__ == "__main__":
    main()
