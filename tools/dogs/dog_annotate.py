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

import exit_detect

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
from common.screen import grab as _adb_grab  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_TEMPLATES = os.path.join(HERE, "templates", "board")
HOUSE_TEMPLATES = os.path.join(HERE, "templates", "house")
SHOP_TEMPLATES = os.path.join(HERE, "templates", "shop")
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

BIG_CENTERS = [(165, 320), (420, 320), (675, 320), (930, 320)]
SMALL_CENTERS = [(85, 535), (220, 535), (365, 535), (510, 535),
                 (660, 535), (790, 535), (930, 535)]
BOARD_BAND = (0, 850, 1080, 1660)

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


def canon(breed):
    """<品种>_v2.png 等姿态变体归并回品种名。"""
    parts = breed.rsplit("_v", 1)
    return parts[0] if len(parts) == 2 and parts[1].isdigit() else breed


def load_templates(folder):
    out = {}
    if not os.path.isdir(folder):
        return out
    for fn in sorted(os.listdir(folder)):
        if fn.lower().endswith((".png", ".jpg", ".jpeg")):
            img = cv2.imread(os.path.join(folder, fn), cv2.IMREAD_COLOR)
            if img is not None:
                out[os.path.splitext(fn)[0]] = img
    return out


def grab(serial=None):
    return _adb_grab(serial, check=True)


def match_all(img, templates, threshold=0.85, min_dist=60, zone=None):
    """模板匹配 + 非极大值抑制，返回带全屏坐标的候选。"""
    x0, y0, x1, y1 = zone or (0, 0, img.shape[1], img.shape[0])
    crop = img[y0:y1, x0:x1]
    found = []
    for breed, tpl in templates.items():
        if tpl.shape[0] > crop.shape[0] or tpl.shape[1] > crop.shape[1]:
            continue
        res = cv2.matchTemplate(crop, tpl, cv2.TM_CCOEFF_NORMED)
        while True:
            _, score, _, loc = cv2.minMaxLoc(res)
            if score < threshold:
                break
            found.append({"breed": canon(breed), "score": round(float(score), 3),
                          "x": x0 + loc[0] + tpl.shape[1] // 2,
                          "y": y0 + loc[1] + tpl.shape[0] // 2,
                          "w": tpl.shape[1], "h": tpl.shape[0]})
            cv2.rectangle(res,
                          (max(0, loc[0] - min_dist), max(0, loc[1] - min_dist)),
                          (min(res.shape[1] - 1, loc[0] + min_dist),
                           min(res.shape[0] - 1, loc[1] + min_dist)), 0, -1)
    found.sort(key=lambda d: -d["score"])
    kept = []
    for d in found:
        if any(abs(d["x"] - k["x"]) < min_dist and abs(d["y"] - k["y"]) < min_dist
               for k in kept):
            continue
        kept.append(d)
    return sorted(kept, key=lambda d: (d["y"], d["x"]))


def classify_patch(patch, templates, threshold=0.65):
    best, score = None, 0.0
    for breed, tpl in templates.items():
        if tpl.shape[0] > patch.shape[0] or tpl.shape[1] > patch.shape[1]:
            continue
        s = float(cv2.matchTemplate(patch, tpl, cv2.TM_CCOEFF_NORMED).max())
        if s > score:
            best, score = canon(breed), s
    return (best, round(score, 3)) if score >= threshold else (None, round(score, 3))


def is_locked(patch, purple=False):
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    sat, val, hue = hsv[:, :, 1], hsv[:, :, 2], hsv[:, :, 0]
    if purple:
        sel = sat > 60
        return bool(sel.sum() and np.median(hue[sel]) > 70 and
                    float(val.mean()) < 220)
    gray = (sat < 35) & (val > 110) & (val < 215)
    return bool(float(gray.mean()) > 0.45)


def detect_eggs(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    x0, y0, x1, y1 = BOARD_BAND
    sub = hsv[y0:y1, x0:x1]
    masks = [((sub[:, :, 0] >= 125) & (sub[:, :, 0] <= 170) &
              (sub[:, :, 1] > 70) & (sub[:, :, 2] > 90), "紫蛋"),
             ((sub[:, :, 0] >= 85) & (sub[:, :, 0] <= 110) &
              (sub[:, :, 1] > 35) & (sub[:, :, 1] < 120) &
              (sub[:, :, 2] > 150), "冰蛋")]
    out = []
    for mask, label in masks:
        m = cv2.morphologyEx(mask.astype(np.uint8) * 255, cv2.MORPH_CLOSE,
                             np.ones((9, 9), np.uint8))
        contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if 55 <= w <= 150 and 55 <= h <= 150 and 4000 <= cv2.contourArea(c) <= 18000:
                out.append({"label": label, "x": x0 + x + w // 2,
                            "y": y0 + y + h // 2, "w": w, "h": h})
    return out


def mark_exits(dogs):
    """出口在画面中部：左侧廊道取最右的狗，右侧廊道取最左的狗。"""
    for d in dogs:
        d["exit"] = False
    rows = {}
    for d in dogs:
        row = min(range(4), key=lambda i: abs(d["y"] - (930, 1132, 1324, 1534)[i]))
        rows.setdefault(row, []).append(d)
    for row in rows.values():
        left = [d for d in row if d["x"] < 540]
        right = [d for d in row if d["x"] >= 540]
        if left:
            max(left, key=lambda d: d["x"])["exit"] = True
        if right:
            min(right, key=lambda d: d["x"])["exit"] = True
    return dogs


def analyze(img, threshold=0.85):
    board_tpl = exit_detect.load_templates(BOARD_TEMPLATES)
    house_tpl = load_templates(HOUSE_TEMPLATES)
    locked_tpl = house_tpl.pop("locked", None)
    shop_tpl = {k: [v] for k, v in load_templates(SHOP_TEMPLATES).items()}

    dogs = []
    for slot in exit_detect.find_exit_slots(img):
        result = exit_detect.classify_exit(slot, img, board_tpl, shop_tpl)
        dogs.append({"breed": result["breed"], "label": result["label"],
                     "score": result["score"], "method": result["method"],
                     "x": slot["x"], "y": slot["y"], "w": slot["w"], "h": slot["h"],
                     "row": slot["row"], "side": slot["side"], "exit": True})
    tpl_feats = []
    for name, imgs in {**board_tpl, **shop_tpl}.items():
        for t in imgs:
            tpl_feats.append((name, exit_detect.featurize(t)))

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
        breed, score = classify_patch(patch, house_tpl, 0.72)
        if breed is None:
            flat = {k: imgs[0] for k, imgs in board_tpl.items()}
            breed, score = classify_patch(patch, flat, 0.55)
        inner = patch[40:150, 40:150]
        for dx, dy in ((0, 0), (-30, 0), (30, 0), (0, 25), (0, -25),
                           (-30, 25), (30, 25)):
                crop = patch[40 + dy:150 + dy, 40 + dx:150 + dx]
                if crop.shape[0] < 60 or crop.shape[1] < 60:
                    continue
                breed = exit_detect.rule_classify(crop)
                if breed:
                    score = 0.75
                    break
        if breed is None and tpl_feats:
            hf = exit_detect.featurize(inner)
            nearest = min(tpl_feats,
                          key=lambda t: float(np.linalg.norm(hf - t[1])))
            dist = float(np.linalg.norm(hf - nearest[1]))
            if dist < 2.8:
                breed, score = nearest[0], round(1.0 / (1.0 + dist), 3)
        houses.append({"idx": i, "x": x, "y": y,
                       "label": BREED_CN.get(breed, breed or "未知"), "score": score})
    smalls = []
    for i, (x, y) in enumerate(SMALL_CENTERS, 1):
        patch = img[y - 48:y + 48, max(0, x - 48):x + 48]
        if is_locked(patch, purple=True):
            smalls.append({"idx": i, "x": x, "y": y, "label": "未解锁", "score": None})
            continue
        flat = {k: imgs[0] for k, imgs in board_tpl.items()}
        inner = img[y - 30:y + 30, max(0, x - 30):x + 30]
        frac = exit_detect.color_fractions(inner)
        if frac["white"] > 0.42 or frac["black"] > 0.12 or frac["gray"] > 0.25:
            breed = exit_detect.rule_classify(inner)
            score = 0.75
        else:
            breed, score = None, 0.0
        if breed is None:
            breed, score = classify_patch(
                patch, {**flat, **{k: v[0] for k, v in shop_tpl.items()}}, 0.62)
        smalls.append({"idx": i, "x": x, "y": y,
                       "label": BREED_CN.get(breed, breed or "空"), "score": score})
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
        slabel = s["label"] if s["label"] in ("未解锁", "空") else BREED_SHORT.get(
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
    ap.add_argument("--threshold", type=float, default=0.88, help="模板匹配置信度")
    args = ap.parse_args()
    img = cv2.imread(args.image) if args.image else grab(args.device)
    if img is None:
        raise SystemExit("图片读取失败: " + args.image)
    if float(img.mean()) < 12:
        raise SystemExit("画面几乎全黑（可能锁屏或广告），请先回到游戏界面")
    result = analyze(img, args.threshold)
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
