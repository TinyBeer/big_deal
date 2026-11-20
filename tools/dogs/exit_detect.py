"""廊道出口槽位检测与狗品种分类。

只关注画面中部 8 个出口（每行左右各一），不对整块棋盘做模板匹配。
出口位置随剩余狗数量变化，所以先按颜色/形状找每行最靠中间的狗或蛋，
再用「模板匹配 + 颜色布局特征」识别品种。
"""

import os

import cv2
import numpy as np

ROWS = (930, 1132, 1324, 1534)
BREEDS = ("shiba_orange", "husky_black", "samoyed_white", "collie_blackwhite",
          "pug_beige", "beagle_orangewhite", "boston_blackwhite",
          "poodle_brown", "terrier_gray")


def load_templates(folder):
    out = {}
    if not os.path.isdir(folder):
        return out
    for fn in sorted(os.listdir(folder)):
        if fn.lower().endswith((".png", ".jpg", ".jpeg")):
            img = cv2.imread(os.path.join(folder, fn), cv2.IMREAD_COLOR)
            if img is not None:
                name = os.path.splitext(fn)[0].rsplit("_v", 1)[0]
                out.setdefault(name, []).append(img)
    return out


def featurize(patch):
    """颜色布局 + 颜色直方图，对姿态变化比纯模板匹配稳。"""
    p = cv2.resize(patch, (48, 48), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(p, cv2.COLOR_BGR2HSV)
    grid = cv2.resize(p, (4, 4), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    h = np.histogram(hsv[:, :, 0], bins=16, range=(0, 180))[0].astype(np.float32)
    s = np.histogram(hsv[:, :, 1], bins=4, range=(0, 256))[0].astype(np.float32)
    v = np.histogram(hsv[:, :, 2], bins=4, range=(0, 256))[0].astype(np.float32)
    h /= max(h.sum(), 1)
    s /= max(s.sum(), 1)
    v /= max(v.sum(), 1)
    return np.concatenate([grid.ravel(), h * 0.8, s * 0.5, v * 0.5])


def feature_score(patch, templates):
    fp = featurize(patch)
    best, best_s = None, 0.0
    for breed, imgs in templates.items():
        for t in imgs:
            ft = featurize(t)
            d = float(np.linalg.norm(fp - ft))
            s = 1.0 / (1.0 + d * 1.6)
            if s > best_s:
                best, best_s = breed, s
    return best, best_s


def template_score(patch, templates):
    best, best_s = None, 0.0
    for breed, imgs in templates.items():
        for t in imgs:
            if t.shape[0] > patch.shape[0] or t.shape[1] > patch.shape[1]:
                t = cv2.resize(t, (min(100, patch.shape[1]), min(100, patch.shape[0])))
            s = float(cv2.matchTemplate(patch, t, cv2.TM_CCOEFF_NORMED).max())
            if s > best_s:
                best, best_s = breed, s
    return best, best_s


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


ROWS = (930, 1132, 1324, 1534, 1740)
LEFT_CENTERS = (415, 285, 170, 55)
RIGHT_CENTERS = (635, 765, 895, 1020)


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


def rule_classify(patch):
    """按颜色布局直接判定大类，对未收录姿态比最近邻稳。"""
    f = color_fractions(patch)
    w, b, o, br, g, blue = (f["white"], f["black"], f["orange"], f["brown"],
                            f["gray"], f["blue"])
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    white = (v > 200) & (s < 45)
    dark = v < 85
    def safe_mean(a):
        return float(a.mean()) if a.size else 0.0

    mid_white = safe_mean(white[10:55, 45:65])
    both_eye_dark = (safe_mean(dark[20:45, 15:40]) > 0.40 and
                     safe_mean(dark[20:45, 70:95]) > 0.40)
    muzzle = ((v < 140) & (s < 90))[45:80, 30:80]
    cream = (h >= 8) & (h <= 30) & (s >= 20) & (s <= 90) & (v > 170)
    if safe_mean(muzzle) > 0.22 and safe_mean(cream) > 0.30:
        return "pug_beige"
    if mid_white > 0.50 and both_eye_dark:
        return "boston_blackwhite"
    if w > 0.62 and b < 0.10 and o < 0.14:
        return "samoyed_white"
    if o > 0.35:
        return "shiba_orange"
    if w > 0.28 and (o + br) > 0.10 and b < 0.15:
        return "beagle_orangewhite"
    if br > 0.25 and w > 0.25:
        return "beagle_orangewhite"
    if blue > 0.015 and b > 0.22:
        return "husky_black"
    if b > 0.45 and blue > 0.002:
        return "husky_black"
    if b > 0.30 and blue > 0.004:
        return "husky_black"
    if b > 0.30 and w > 0.22:
        return "collie_blackwhite"
    if b > 0.14 and w > 0.25:
        return "boston_blackwhite"
    if br > 0.35:
        return "poodle_brown"
    if g > 0.35:
        return "terrier_gray"
    if w > 0.40 and br < 0.15 and o < 0.25:
        return "samoyed_white"
    return None


def classify_exit(slot, img, templates, shop_templates):
    h, w = img.shape[:2]
    x, y = slot["x"], slot["y"]
    r = 55
    patch = img[max(0, y - r):min(h, y + r), max(0, x - r):min(w, x + r)]
    if patch.shape[0] < 40 or patch.shape[1] < 40:
        return {"breed": None, "label": "未知", "score": 0.0, "method": "empty"}
    if patch.shape[0] < 110 or patch.shape[1] < 110:
        patch = cv2.resize(patch, (max(110, patch.shape[1]), max(110, patch.shape[0])))
    egg = egg_label(patch)
    if egg:
        return {"breed": None, "label": egg, "score": 0.0, "method": "egg"}
    rule = rule_classify(patch)
    tb, ts = template_score(patch, templates)
    fb, fs = feature_score(patch, {**templates, **shop_templates})
    if rule:
        breed, score, method = rule, max(0.82, ts, fs), "rule"
    elif ts >= 0.88:
        breed, score, method = tb, ts, "template"
    elif fs >= 0.42:
        breed, score, method = fb, fs, "feature"
    else:
        breed, score, method = (tb if ts >= fs else fb), max(ts, fs), "weak"
        if score < 0.45:
            breed = None
    return {"breed": breed, "label": breed or "未知", "score": round(float(score), 3),
            "method": method}
