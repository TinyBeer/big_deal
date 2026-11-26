#!/usr/bin/env python3
"""本关专用：识别并标注棋盘上所有零食/饮料，以及右上角退出按钮（气泡内的商品不算）。

方案：只在「当前商品最小外接矩形」内搜索，用本关商品模板做彩色模板匹配；
匹配不到的彩色前景块作为「未知商品」兜底标注，避免漏标。
被手指/手势图标遮挡的商品只要可见部分足够，仍能靠模板匹配找到。
右上角带中心点的圆圈单独用模板识别，不计入商品数量。

只输出标注图，日志不给坐标、不写 JSON。坐标以 1080x2400 为基准按比例适配。
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(DIR))
sys.path.insert(0, os.path.dirname(DIR))  # tools/
from common.screen import grab  # noqa: E402

BASE_W, BASE_H = 1080, 2400
BG_SAMPLE_Y = (1040, 1150)   # 商品区上方的米色空白，用于估计背景色
BAND_Y = (1150, 1700)        # 本关商品所在大带；顾客气泡在 y>1800，天然排除
BG_DIFF = 28                 # 前景色差阈值
PAD = 20                     # 最小外接矩形外扩
MIN_AREA = 500               # 前景连通域最小面积（基准分辨率）
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
COLORS = {
    "零食": (255, 145, 0),
    "饮料": (0, 150, 255),
    "未知": (235, 60, 70),
    "退出": (190, 70, 255),
}
OCCLUDED_SCORE = 0.92        # 低于此匹配分认为有遮挡
EXIT_TEMPLATE = "exit_button.png"   # 右上角带中心点的圆圈（退出按钮）
EXIT_ROI = (880, 110, 1080, 240)    # 退出按钮搜索区（基准坐标）
SHOP_CLOSE_TEMPLATE = "shop_close.png"  # 积分兑换商店右上角的红色叉号
SHOP_CLOSE_ROI = (850, 0, 1080, 800)    # 叉号搜索区（基准坐标）
START_GAME_TEMPLATE = "start_game.png"  # 游戏主界面的「开始游戏」按钮
GIFT_NO_THANKS_TEMPLATE = "gift_no_thanks.png"  # 助力礼包弹窗的「No thanks」
ENTRY_TAB_TEMPLATE = "entry_tab.png"            # 游戏入口页「真香摆摊日记」页签


def default_output(name):
    return os.path.join(ROOT, "outputs", name)


def load_catalog():
    path = os.path.join(DIR, "catalog.json")
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    out = []
    for e in entries:
        tpl = cv2.imread(os.path.join(DIR, "templates", e["file"]))
        if tpl is None:
            print("警告：模板读取失败 %s" % e["file"], file=sys.stderr)
            continue
        out.append({"name": e["name"], "category": e["category"], "tpl": tpl})
    return out


def detect_exit(img, sx, sy, threshold=0.85):
    """右上角「同心圆 + 中心点」退出按钮，返回 bbox 或 None。"""
    tpl = cv2.imread(os.path.join(DIR, "templates", EXIT_TEMPLATE))
    if tpl is None:
        return None
    tw, th = max(10, int(round(tpl.shape[1] * sx))), max(10, int(round(tpl.shape[0] * sy)))
    tpl = cv2.resize(tpl, (tw, th), interpolation=cv2.INTER_AREA) \
        if (tw, th) != (tpl.shape[1], tpl.shape[0]) else tpl
    x0, y0, x1, y1 = [int(v * s) for v, s in zip(EXIT_ROI, (sx, sy, sx, sy))]
    roi = img[y0:y1, x0:x1]
    if roi.shape[0] < th or roi.shape[1] < tw:
        return None
    _, score, _, loc = cv2.minMaxLoc(cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED))
    if score < threshold:
        return None
    bx, by = x0 + loc[0], y0 + loc[1]
    return {"bx": bx, "by": by, "bw": tw, "bh": th,
            "center": [bx + tw // 2, by + th // 2],
            "score": round(float(score), 4)}


def detect_shop_close(img, sx, sy, threshold=0.85):
    """积分兑换商店右上角的红色叉号，返回 bbox/center 或 None。"""
    tpl = cv2.imread(os.path.join(DIR, "templates", SHOP_CLOSE_TEMPLATE))
    if tpl is None:
        return None
    tw = max(10, int(round(tpl.shape[1] * sx)))
    th = max(10, int(round(tpl.shape[0] * sy)))
    tpl = cv2.resize(tpl, (tw, th), interpolation=cv2.INTER_AREA) \
        if (tw, th) != (tpl.shape[1], tpl.shape[0]) else tpl
    x0, y0, x1, y1 = [int(v * s) for v, s in
                      zip(SHOP_CLOSE_ROI, (sx, sy, sx, sy))]
    x1, y1 = min(x1, img.shape[1]), min(y1, img.shape[0])
    roi = img[y0:y1, x0:x1]
    if roi.shape[0] < th or roi.shape[1] < tw:
        return None
    _, score, _, loc = cv2.minMaxLoc(cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED))
    if score < threshold:
        return None
    bx, by = x0 + loc[0], y0 + loc[1]
    return {"bx": bx, "by": by, "bw": tw, "bh": th,
            "center": [bx + tw // 2, by + th // 2],
            "score": round(float(score), 4)}


def detect_start_game(img, sx, sy, threshold=0.6):
    """游戏主界面的橙色「开始游戏」按钮，返回 bbox/center 或 None。"""
    tpl = cv2.imread(os.path.join(DIR, "templates", START_GAME_TEMPLATE))
    if tpl is None:
        return None
    tw = max(10, int(round(tpl.shape[1] * sx)))
    th = max(10, int(round(tpl.shape[0] * sy)))
    tpl = cv2.resize(tpl, (tw, th), interpolation=cv2.INTER_AREA) \
        if (tw, th) != (tpl.shape[1], tpl.shape[0]) else tpl
    if img.shape[0] < th or img.shape[1] < tw:
        return None
    _, score, _, loc = cv2.minMaxLoc(cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED))
    if score < threshold:
        return None
    bx, by = loc
    return {"bx": bx, "by": by, "bw": tw, "bh": th,
            "center": [bx + tw // 2, by + th // 2],
            "score": round(float(score), 4)}


def detect_entry_tab(img, sx, sy, threshold=0.85):
    """游戏入口页「真香摆摊日记」页签，返回 bbox/center 或 None。"""
    tpl = cv2.imread(os.path.join(DIR, "templates", ENTRY_TAB_TEMPLATE))
    if tpl is None:
        return None
    tw = max(10, int(round(tpl.shape[1] * sx)))
    th = max(10, int(round(tpl.shape[0] * sy)))
    tpl = cv2.resize(tpl, (tw, th), interpolation=cv2.INTER_AREA) \
        if (tw, th) != (tpl.shape[1], tpl.shape[0]) else tpl
    if img.shape[0] < th or img.shape[1] < tw:
        return None
    _, score, _, loc = cv2.minMaxLoc(cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED))
    if score < threshold:
        return None
    bx, by = loc
    return {"bx": bx, "by": by, "bw": tw, "bh": th,
            "center": [bx + tw // 2, by + th // 2],
            "score": round(float(score), 4)}


def detect_gift_no_thanks(img, sx, sy, threshold=0.85):
    """助力礼包弹窗上的「No thanks」按钮，返回 bbox/center 或 None。"""
    tpl = cv2.imread(os.path.join(DIR, "templates", GIFT_NO_THANKS_TEMPLATE))
    if tpl is None:
        return None
    tw = max(10, int(round(tpl.shape[1] * sx)))
    th = max(10, int(round(tpl.shape[0] * sy)))
    tpl = cv2.resize(tpl, (tw, th), interpolation=cv2.INTER_AREA) \
        if (tw, th) != (tpl.shape[1], tpl.shape[0]) else tpl
    if img.shape[0] < th or img.shape[1] < tw:
        return None
    _, score, _, loc = cv2.minMaxLoc(cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED))
    if score < threshold:
        return None
    bx, by = loc
    return {"bx": bx, "by": by, "bw": tw, "bh": th,
            "center": [bx + tw // 2, by + th // 2],
            "score": round(float(score), 4)}


def ad_white_ratio(img):
    """广告加载页几乎整屏纯白；游戏/弹窗页面该比例很低。"""
    white = ((img[:, :, 0] > 240) & (img[:, :, 1] > 240) &
             (img[:, :, 2] > 240))
    return float(white.mean())


def estimate_bg(img, sx, sy):
    """取商品区上方米色背景的中位色（只留低饱和亮像素）。"""
    y0, y1 = int(BG_SAMPLE_Y[0] * sy), min(img.shape[0], int(BG_SAMPLE_Y[1] * sy))
    crop = img[y0:y1]
    if crop.size == 0:
        return np.median(img.reshape(-1, 3), axis=0)
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    keep = (hsv[:, :, 1] < 60) & (hsv[:, :, 2] > 170)
    px = crop[keep] if int(keep.sum()) > 200 else crop.reshape(-1, 3)
    return np.median(px, axis=0)


def play_area(img, sx, sy):
    """返回 (最小外接矩形, 商品带前景 mask, 连通域列表)。"""
    bg = estimate_bg(img, sx, sy)
    diff = np.max(np.abs(img.astype(np.int16) - bg.astype(np.int16)), axis=2)
    band = np.zeros(img.shape[:2], np.uint8)
    y0, y1 = int(BAND_Y[0] * sy), min(img.shape[0], int(BAND_Y[1] * sy))
    band[y0:y1] = (diff[y0:y1] > BG_DIFF).astype(np.uint8) * 255
    ksize = (max(7, int(15 * sx)) | 1, max(7, int(15 * sy)) | 1)
    band = cv2.morphologyEx(band, cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, ksize))
    n, _, stats, _ = cv2.connectedComponentsWithStats(band)
    boxes = []
    for x, y, w, h, area in stats[1:]:
        if (area >= MIN_AREA * sx * sy and w >= 25 * sx and h >= 40 * sy):
            boxes.append((int(x), int(y), int(w), int(h)))
    if not boxes:
        return (0, y0, img.shape[1], y1), band, []
    px = int(PAD * sx)
    py = int(PAD * sy)
    rect = (max(0, min(b[0] for b in boxes) - px),
            max(y0, min(b[1] for b in boxes) - py),
            min(img.shape[1], max(b[0] + b[2] for b in boxes) + px),
            min(y1, max(b[1] + b[3] for b in boxes) + py))
    return rect, band, boxes


def _overlap(a, b):
    """两个 bbox 的 IoU。"""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    union = aw * ah + bw * bh - inter
    return inter / union if union else 0.0


def match_templates(img, rect, catalog, sx, sy, threshold):
    x0, y0, x1, y1 = rect
    roi = img[y0:y1, x0:x1]
    hits = []
    for e in catalog:
        tw = max(10, int(round(e["tpl"].shape[1] * sx)))
        th = max(10, int(round(e["tpl"].shape[0] * sy)))
        tpl = e["tpl"] if (tw, th) == (e["tpl"].shape[1], e["tpl"].shape[0]) \
            else cv2.resize(e["tpl"], (tw, th), interpolation=cv2.INTER_AREA)
        if roi.shape[0] < th or roi.shape[1] < tw:
            continue
        work = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED)
        for _ in range(24):
            _, score, _, loc = cv2.minMaxLoc(work)
            if score < threshold:
                break
            x, y = loc
            hits.append({
                "name": e["name"], "category": e["category"],
                "score": round(float(score), 4),
                "bx": x0 + x, "by": y0 + y, "bw": tw, "bh": th,
            })
            rx, ry = max(6, int(tw * 0.35)), max(8, int(th * 0.30))
            work[max(0, y - ry):min(work.shape[0], y + ry + 1),
                 max(0, x - rx):min(work.shape[1], x + rx + 1)] = -1

    # 跨模板 NMS：保留高分，压掉同一商品的重复命中
    hits.sort(key=lambda h: -h["score"])
    kept = []
    for h in hits:
        b = (h["bx"], h["by"], h["bw"], h["bh"])
        dup = False
        for k in kept:
            c = (k["bx"], k["by"], k["bw"], k["bh"])
            cx = abs((h["bx"] + h["bw"] / 2) - (k["bx"] + k["bw"] / 2))
            cy = abs((h["by"] + h["bh"] / 2) - (k["by"] + k["bh"] / 2))
            if (_overlap(b, c) > 0.35 or
                    (cx < 0.45 * min(h["bw"], k["bw"]) and
                     cy < 0.45 * min(h["bh"], k["bh"]))):
                dup = True
                break
        if not dup:
            kept.append(h)
    return kept


def find_unknown(img, rect, hits, boxes, sx, sy):
    """未被模板命中的彩色前景块兜底标注（新手势图标靠低饱和度排除）。"""
    x0, y0, x1, y1 = rect
    out = []
    for bx, by, bw, bh in boxes:
        b = (bx, by, bw, bh)
        if any(_overlap(b, (h["bx"], h["by"], h["bw"], h["bh"])) > 0.15 for h in hits):
            continue
        if bx < x0 or by < y0 or bx + bw > x1 or by + bh > y1:
            continue
        hsv = cv2.cvtColor(img[by:by + bh, bx:bx + bw], cv2.COLOR_BGR2HSV)
        if float(hsv[:, :, 1].mean()) < 35:  # 手部/手势是白灰色
            continue
        out.append({
            "name": "未知商品",
            "category": "零食" if bw / max(1, bh) > 0.55 else "饮料",
            "score": None, "bx": bx, "by": by, "bw": bw, "bh": bh,
        })
    return out


def analyze(img, threshold=0.75, use_unknown=True):
    h, w = img.shape[:2]
    sx, sy = w / BASE_W, h / BASE_H
    rect, band, boxes = play_area(img, sx, sy)
    items = match_templates(img, rect, load_catalog(), sx, sy, threshold)
    if use_unknown:
        items += find_unknown(img, rect, items, boxes, sx, sy)
    # 按大致行分组再按 x 排序，避免上下排只差几像素时编号跳来跳去
    items.sort(key=lambda it: (it["by"] // max(1, int(60 * sy)), it["bx"]))
    for i, item in enumerate(items, 1):
        item["index"] = i
        item["occluded"] = (item["score"] is not None and
                            item["score"] < OCCLUDED_SCORE)
        item["center"] = [item["bx"] + item["bw"] // 2,
                          item["by"] + item["bh"] // 2]
    exit_btn = detect_exit(img, sx, sy)
    return {
        "width": w, "height": h, "roi": rect,
        "counts": {
            "total": len(items),
            "零食": sum(1 for it in items if it["category"] == "零食"),
            "饮料": sum(1 for it in items if it["category"] == "饮料"),
            "occluded": sum(1 for it in items if it["occluded"]),
            "exit": exit_btn is not None,
        },
        "items": items,
        "exit": exit_btn,
    }


def _font(size):
    try:
        return ImageFont.truetype(FONT_PATH, max(14, int(size)))
    except OSError:
        return ImageFont.load_default()


def annotate(img, result, show_roi=False):
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil, "RGBA")
    sx = img.shape[1] / BASE_W
    font = _font(25 * sx)
    if show_roi:
        x0, y0, x1, y1 = result["roi"]
        for x in range(x0, x1, 24):
            d.line((x, y0, min(x + 12, x1), y0), fill=(90, 90, 90, 180), width=2)
            d.line((x, y1, min(x + 12, x1), y1), fill=(90, 90, 90, 180), width=2)
        for y in range(y0, y1, 24):
            d.line((x0, y, x0, min(y + 12, y1)), fill=(90, 90, 90, 180), width=2)
            d.line((x1, y, x1, min(y + 12, y1)), fill=(90, 90, 90, 180), width=2)

    placed = []
    for h in result["items"]:
        col = COLORS.get(h["category"], COLORS["未知"])
        d.rectangle((h["bx"], h["by"], h["bx"] + h["bw"], h["by"] + h["bh"]),
                    outline=col, width=max(2, int(3 * sx)))
        label = "%d. %s" % (h["index"], h["name"])
        if h["occluded"]:
            label += "（遮挡）"
        box = d.textbbox((0, 0), label, font=font)
        tw, th = box[2] - box[0], box[3] - box[1]
        # 先放商品上方，与已有标签重叠则改放下方，再重叠则左右挪
        candidates = []
        for shift in (0, -24, 24, -48, 48):
            candidates.append((h["bx"] + shift, max(0, h["by"] - th - 14)))
            candidates.append((max(0, h["bx"] + shift), h["by"] + h["bh"] + 6))
        lx, ly = candidates[0]
        for cx, cy in candidates:
            r = (cx, cy, cx + tw + 14, cy + th + 10)
            if not any(r[0] < p[2] and r[2] > p[0] and r[1] < p[3] and r[3] > p[1]
                       for p in placed):
                lx, ly = cx, cy
                placed.append(r)
                break
        d.rectangle((lx, ly, lx + tw + 14, ly + th + 10), fill=(*col, 220))
        d.text((lx + 7, ly + 2), label, font=font, fill=(255, 255, 255))

    if result["exit"]:
        e = result["exit"]
        col = COLORS["退出"]
        d.rectangle((e["bx"], e["by"], e["bx"] + e["bw"], e["by"] + e["bh"]),
                    outline=col, width=max(2, int(3 * sx)))
        label = "退出按钮"
        bb = d.textbbox((0, 0), label, font=font)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        lx = max(0, min(e["bx"] - 20, pil.width - tw - 24))
        ly = e["by"] + e["bh"] + 6
        d.rectangle((lx, ly, lx + tw + 14, ly + th + 10), fill=(*col, 220))
        d.text((lx + 7, ly + 2), label, font=font, fill=(255, 255, 255))

    c = result["counts"]
    banner = "零食 %d · 饮料 %d · 共 %d · 退出按钮%s（气泡已排除）" % (
        c["零食"], c["饮料"], c["total"], "✓" if c["exit"] else "未找到")
    bb = d.textbbox((0, 0), banner, font=font)
    bw, bh = bb[2] - bb[0], bb[3] - bb[1]
    d.rectangle((10, 10, 10 + bw + 24, 10 + bh + 16), fill=(255, 255, 255, 220))
    d.text((22, 12), banner, font=font, fill=(30, 30, 30))
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)


def main():
    ap = argparse.ArgumentParser(description="本关零食/饮料识别标注（不做点击）")
    ap.add_argument("--image", help="直接处理本地截图；不给则实时 adb 抓图")
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--output", default=default_output("snacks_annotated.png"))
    ap.add_argument("--threshold", type=float, default=0.75, help="模板匹配分阈值")
    ap.add_argument("--no-unknown", action="store_true", help="不标注未命中模板的彩色块")
    ap.add_argument("--show-roi", action="store_true", help="标注图上画出商品搜索框")
    args = ap.parse_args()

    img = cv2.imread(args.image) if args.image else grab(args.device, check=True)
    if img is None:
        print("抓图/读图失败", file=sys.stderr)
        return 1
    result = analyze(img, args.threshold, not args.no_unknown)
    cv2.imwrite(args.output, annotate(img, result, args.show_roi))
    c = result["counts"]
    print("识别完成：零食 %d · 饮料 %d · 共 %d（遮挡 %d） · 退出按钮 %s" % (
        c["零食"], c["饮料"], c["total"], c["occluded"],
        "已识别" if c["exit"] else "未找到"))
    print("标注图：%s" % args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
