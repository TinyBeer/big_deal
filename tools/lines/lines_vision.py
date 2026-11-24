#!/usr/bin/env python3
"""线条解放辅助 · 找出当前所有可点击线条并标注。

规则：每条折线只有一个箭头，点击后整条线朝箭头方向飞出；从箭头尖端沿方向
直到棋盘边缘的射线上不能有任何其它线条（包括自身回折），否则扣生命。

流程：抓图 -> 自动检测网格 -> 采样网格边 -> 连通域还原每条折线 -> 由端点
线宽渐宽特征识别箭头 -> 逐条做射线判定 -> 高亮所有当前可点击线条并编号。

默认只输出「当前可点击」集合，不做多步推演；可用 --steps 额外给出顺序规划。
坐标以实际截图像素为准，网格间距由图像自动检测，适配不同关卡尺寸。
"""
import argparse
import json
import os
import sys
from collections import Counter

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # tools/
from common.screen import grab  # noqa: E402

DIR_NAMES = {
    (-1, 0): "up",
    (1, 0): "down",
    (0, -1): "left",
    (0, 1): "right",
}
DIR_CN = {
    "up": "上", "down": "下", "left": "左", "right": "右",
}
DIR_VECTORS = {
    "up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1),
}
PALETTE = [
    (0, 210, 60),    # 绿
    (0, 210, 255),   # 黄
    (60, 160, 255),  # 橙
    (255, 80, 200),  # 粉
    (0, 255, 255),   # 青
    (170, 120, 255), # 紫
    (80, 255, 180),  # 薄荷
]
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def detect_revive(img, threshold=0.85):
    """复活页：先查绿色大按钮（便宜），再在下半屏做模板匹配确认。"""
    h, w = img.shape[:2]
    ry0, ry1 = int(0.55 * h), int(0.85 * h)
    rx0, rx1 = int(0.15 * w), int(0.85 * w)
    roi = img[ry0:ry1, rx0:rx1]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (35, 100, 100), (85, 255, 255))
    _, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    for x, y, bw, bh, area in stats[1:]:
        if area > 0.004 * h * w and bw > 2.2 * bh and bh > 0.03 * h:
            return True
    tpl = cv2.imread(os.path.join(TEMPLATE_DIR, "revive_button.png"))
    if tpl is not None and tpl.shape[0] <= roi.shape[0] and tpl.shape[1] <= roi.shape[1]:
        res = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED)
        if float(res.max()) >= threshold:
            return True
    return False


def count_hearts(img):
    """数顶部红色爱心；爱心减少即代表上一次点击扣了生命。"""
    h, w = img.shape[:2]
    roi = img[int(0.05 * h):int(0.13 * h), int(0.30 * w):int(0.70 * w)]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0, 120, 150), (10, 255, 255))
    mask |= cv2.inRange(hsv, (170, 120, 150), (180, 255, 255))
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask)
    min_area = max(300, int(0.0008 * h * w))
    return sum(1 for area in stats[1:, cv2.CC_STAT_AREA] if area >= min_area)


def _centers(score, frac=0.35, gap=3):
    """从投影分数里取峰值段中心（跳过没有横/竖线段的行列）。"""
    idx = np.flatnonzero(score > frac * float(score.max()))
    if len(idx) == 0:
        return []
    out = []
    start = prev = int(idx[0])
    for value in idx[1:]:
        value = int(value)
        if value > prev + gap:
            out.append((start + prev) / 2.0)
            start = value
        prev = value
    out.append((start + prev) / 2.0)
    return out


def _mod_origin(values, step):
    """用全部线条像素的坐标模步长，求网格的亚像素相位。"""
    mod = np.asarray(values, dtype=float) % step
    bins = np.arange(0, step, 0.5)
    hist, _ = np.histogram(mod, bins)
    ref = ((bins[:-1] + bins[1:]) / 2)[hist.argmax()]
    delta = ((mod - ref + step / 2) % step) - step / 2
    keep = np.abs(delta) < step * 0.25
    return (ref + float(delta[keep].mean())) % step


def _axis_fit(centers):
    """中位数定等距索引，拟合步长/原点，并还原缺失行列后的完整数量。"""
    values = np.asarray(centers, dtype=float)
    diffs = np.diff(values)
    diffs = diffs[diffs > 3]
    guess = float(np.median(diffs))
    index = np.rint((values - values[0]) / guess).astype(int)
    slope, origin = np.polyfit(index, values, 1)
    return float(slope), float(origin), int(index[-1]) + 1


def detect_grid(mask):
    """自动检测网格节点坐标。返回 (cols, rows, step)。"""
    h, w = mask.shape[:2]
    y0, y1 = int(0.15 * h), int(0.90 * h)
    x0, x1 = int(0.03 * w), int(0.97 * w)
    roi = mask[y0:y1, x0:x1]
    if roi.size == 0:
        raise RuntimeError("截图区域为空，无法检测棋盘")
    h_score = (roi[:, :-1] & roi[:, 1:]).sum(axis=1)
    v_score = (roi[:-1, :] & roi[1:, :]).sum(axis=0)
    rows = np.array(_centers(h_score)) + y0
    cols = np.array(_centers(v_score)) + x0
    if len(rows) < 2 or len(cols) < 2:
        raise RuntimeError("未检测到棋盘网格，请确认手机停在游戏关卡界面")
    step_row, _, _ = _axis_fit(rows)
    step_col, _, _ = _axis_fit(cols)
    step = (step_row + step_col) / 2.0
    if not 6.0 <= step <= 80.0:
        raise RuntimeError("网格间距异常（%.1fpx），请确认当前为游戏关卡界面" % step)
    dark_y, dark_x = np.where(roi)
    dark_x = dark_x.astype(float) + x0
    dark_y = dark_y.astype(float) + y0
    phase_x = _mod_origin(dark_x, step)
    phase_y = _mod_origin(dark_y, step)
    # 用投影到的中心锚定相位，再按线条像素范围向两侧补出稀疏/空的行列
    origin_x = phase_x + round((cols[0] - phase_x) / step) * step
    origin_y = phase_y + round((rows[0] - phase_y) / step) * step
    kx0 = int(np.floor((dark_x.min() - origin_x) / step)) - 1
    kx1 = int(np.floor((dark_x.max() - origin_x) / step)) + 1
    ky0 = int(np.floor((dark_y.min() - origin_y) / step)) - 1
    ky1 = int(np.floor((dark_y.max() - origin_y) / step)) + 1
    xs = origin_x + step * np.arange(kx0, kx1 + 1)
    ys = origin_y + step * np.arange(ky0, ky1 + 1)
    return xs, ys, step


def sample_edges(mask, xs, ys, step):
    """采样相邻节点之间的边，得到 H[行,列] / V[行,列] 占用矩阵。"""
    ny, nx = len(ys), len(xs)
    radius = max(2, int(round(step * 0.12)))
    h_edges = np.zeros((ny, nx - 1), np.uint8)
    v_edges = np.zeros((ny - 1, nx), np.uint8)

    def dark_frac(x, y):
        xi, yi = int(round(x)), int(round(y))
        patch = mask[max(0, yi - radius):yi + radius + 1,
                     max(0, xi - radius):xi + radius + 1]
        return float(patch.mean()) if patch.size else 0.0

    for j, y in enumerate(ys):
        for k in range(nx - 1):
            h_edges[j, k] = dark_frac((xs[k] + xs[k + 1]) / 2.0, y) > 0.5
    for j in range(ny - 1):
        y = (ys[j] + ys[j + 1]) / 2.0
        for k, x in enumerate(xs):
            v_edges[j, k] = dark_frac(x, y) > 0.5
    return h_edges, v_edges


def build_adjacency(h_edges, v_edges):
    """把占用边转成节点邻接表；每条折线在图中是度 <= 2 的链。"""
    ny, nx = h_edges.shape[0], v_edges.shape[1]
    adj = {}
    for j in range(ny):
        for k in range(nx - 1):
            if h_edges[j, k]:
                adj.setdefault((j, k), []).append((j, k + 1))
                adj.setdefault((j, k + 1), []).append((j, k))
    for j in range(ny - 1):
        for k in range(nx):
            if v_edges[j, k]:
                adj.setdefault((j, k), []).append((j + 1, k))
                adj.setdefault((j + 1, k), []).append((j, k))
    return adj


def _width_at(mask, xs, ys, x, y, dx, dy, radius):
    """沿 (dx,dy) 前进时，垂直方向的深色像素宽度。"""
    px, py = -dy, dx
    xi, yi = int(round(x)), int(round(y))
    total = 0
    for t in range(-radius, radius + 1):
        sx, sy = xi + px * t, yi + py * t
        if 0 <= sy < mask.shape[0] and 0 <= sx < mask.shape[1] and mask[sy, sx]:
            total += 1
    return total


def _is_arrow(profile, step):
    """箭头尖端线宽由窄渐宽，尖端之后恢复普通线宽；普通端点始终等宽。"""
    return (profile[2] - profile[0] >= 3
            and profile[5] <= max(10, int(round(step * 0.4))))


def _ordered_path(tip, adj):
    """从箭头尖端沿链走到另一端，得到完整有序节点列表。"""
    path = [tip]
    prev = None
    cur = tip
    while len(path) <= len(adj):
        nxts = [node for node in adj.get(cur, []) if node != prev]
        if not nxts or nxts[0] in path:
            break
        prev, cur = cur, nxts[0]
        path.append(cur)
    return path


def arrow_center(mask, step, x, y, direction):
    """箭头三角形深色像素的质心，作为点击位置。direction 为 (行,列) 偏移。"""
    dj, dk = direction
    in_x, in_y = -dk, -dj  # 从尖端朝线条内部的像素方向
    span = int(round(step * 0.39))
    points = []
    for d in range(0, int(round(step * 0.7)) + 1):
        px0 = int(round(x + in_x * d))
        py0 = int(round(y + in_y * d))
        for t in range(-span, span + 1):
            px, py = px0 + in_y * t, py0 - in_x * t
            h, w = mask.shape[:2]
            if 0 <= py < h and 0 <= px < w and mask[py, px]:
                points.append((px, py))
    if len(points) >= 3:
        arr = np.asarray(points, dtype=float)
        cx, cy = arr.mean(axis=0)
        offset = (cx - x) * in_x + (cy - y) * in_y
        if 0.2 * step <= offset <= 0.55 * step:
            return int(round(cx)), int(round(cy))
    return int(round(x + in_x * step * 0.38)), int(round(y + in_y * step * 0.38))


def extract_lines(mask, xs, ys, step, adj):
    """还原每条折线：节点、箭头尖端、方向、箭头中心点击坐标。"""
    distances = [max(2, int(round(step * f)))
                 for f in (0.117, 0.234, 0.351, 0.467, 0.584, 0.70)]
    radius = max(8, int(round(step * 0.39)))
    seen = set()
    lines = []
    for node in adj:
        if node in seen:
            continue
        queue, comp = [node], []
        seen.add(node)
        while queue:
            cur = queue.pop()
            comp.append(cur)
            for nxt in adj[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        tip = direction = None
        for end in comp:
            if len(adj[end]) != 1:
                continue
            nxt = adj[end][0]
            dj, dk = nxt[0] - end[0], nxt[1] - end[1]
            profile = [
                _width_at(mask, xs, ys,
                          xs[end[1]] + dk * d, ys[end[0]] + dj * d, dk, dj, radius)
                for d in distances
            ]
            if _is_arrow(profile, step):
                tip = end
                direction = (-dj, -dk)
                break
        if tip is None:
            continue  # 截到棋盘外的残缺线条，忽略
        path = _ordered_path(tip, adj)
        x, y = xs[tip[1]], ys[tip[0]]
        click_x, click_y = arrow_center(mask, step, x, y, direction)
        lines.append({
            "id": len(lines),
            "tip": tip,
            "dir": direction,
            "direction": DIR_NAMES[direction],
            "nodes": path,
            "node_set": set(comp),
            "x": x, "y": y,
            "click_x": click_x, "click_y": click_y,
        })
    return lines


def is_free(line, occupied, ny, nx):
    """箭头前方直到棋盘边缘无占用节点 => 可安全点击。"""
    j, k = line["tip"]
    dj, dk = line["dir"]
    t = 1
    while 0 <= j + dj * t < ny and 0 <= k + dk * t < nx:
        if (j + dj * t, k + dk * t) in occupied:
            return False
        t += 1
    return True


def ray_clear_pixels(mask, line, xs, ys, step):
    """在当前截图上沿箭头射线逐像素复核，避免网格采样漏掉遮挡。"""
    dj, dk = line["dir"]
    x0, y0 = line["x"], line["y"]
    min_x, max_x = xs[0] - step, xs[-1] + step
    min_y, max_y = ys[0] - step, ys[-1] + step
    h, w = mask.shape[:2]
    d = 4
    while True:
        x = int(round(x0 + dk * d))
        y = int(round(y0 + dj * d))
        if not (min_x <= x <= max_x and min_y <= y <= max_y):
            return True
        if 0 <= x < w and 0 <= y < h:
            patch = mask[max(0, y - 3):y + 4, max(0, x - 3):x + 4]
            if float(patch.mean()) > 0.12:
                return False
        d += 2


def _free_items(info, ids):
    by_id = {line["id"]: line for line in info["lines"]}
    items = []
    for line_id in ids:
        line = by_id[line_id]
        items.append({
            "id": line_id,
            "click": [line["click_x"], line["click_y"]],
            "tip": [int(round(line["x"])), int(round(line["y"]))],
            "direction": line["direction"],
            "nodes": [[j, k] for j, k in line["nodes"]],
        })
    items.sort(key=lambda item: (item["tip"][1], item["tip"][0]))
    for label, item in enumerate(items, 1):
        item["label"] = label
    return items


def free_lines(info):
    """当前可点击线条的完整清单，按从上到下、从左到右编号（不是点击顺序）。"""
    return _free_items(info, info["free_ids"])


def plan_steps(lines, ny, nx, steps=5):
    """模拟逐条移除，规划安全的点击顺序；优先选择能解锁最多新线条的一支。"""
    remaining = set(line["id"] for line in lines)
    by_id = {line["id"]: line for line in lines}
    result = []
    while len(result) < steps and remaining:
        occupied = set()
        for line_id in remaining:
            occupied |= by_id[line_id]["node_set"]
        candidates = [i for i in remaining if is_free(by_id[i], occupied, ny, nx)]
        if not candidates:
            break
        free_before = set(candidates)

        def gain(line_id):
            freed = occupied - by_id[line_id]["node_set"]
            return sum(1 for other in remaining
                       if other != line_id and other not in free_before
                       and is_free(by_id[other], freed, ny, nx))

        best = max(candidates, key=lambda i: (gain(i), -len(by_id[i]["nodes"])))
        line = by_id[best]
        result.append({
            "step": len(result) + 1,
            "line_id": best,
            "click": [line["click_x"], line["click_y"]],
            "tip": [int(round(line["x"])), int(round(line["y"]))],
            "direction": line["direction"],
            "nodes": [[j, k] for j, k in line["nodes"]],
            "free_before": len(candidates),
            "new_free": gain(best),
        })
        remaining.remove(best)
    return result


def analyze(img, steps=0, grid=None):
    """完整识别 + 可点击判定；grid 可传入已锁定的 (xs, ys, step)。"""
    if img is None:
        raise RuntimeError("截图为空，请检查 adb 连接和当前界面")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blue, green, red = cv2.split(img)
    # 点错时游戏会把受阻线条闪红；这类红色像素同样要当作线条，否则会从棋盘里消失
    red_flash = (red > 170) & (green < 130) & (blue < 130)
    mask = ((gray < 100) | red_flash).astype(np.uint8)
    if grid is None:
        xs, ys, step = detect_grid(mask)
    else:
        xs, ys, step = grid
    h_edges, v_edges = sample_edges(mask, xs, ys, step)
    adj = build_adjacency(h_edges, v_edges)
    lines = extract_lines(mask, xs, ys, step, adj)
    ny, nx = len(ys), len(xs)
    occupied = set()
    for line in lines:
        occupied |= line["node_set"]
    free_ids = [line["id"] for line in lines
                if is_free(line, occupied, ny, nx)
                and ray_clear_pixels(mask, line, xs, ys, step)]
    plan = plan_steps(lines, ny, nx, steps=steps) if steps > 0 else []
    return {
        "grid": {
            "cols": nx, "rows": ny,
            "step": round(float(step), 2),
            "x0": round(float(xs[0]), 2),
            "y0": round(float(ys[0]), 2),
        },
        "xs": xs, "ys": ys, "step": step,
        "lines": lines,
        "free_ids": free_ids,
        "plan": plan,
    }


def _draw_cn(img, count, badges):
    """顶部说明 + 外围标记上的中文方向；字体缺失时退回英文。"""
    try:
        pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)
        font = ImageFont.truetype(FONT_PATH, 30)
        badge_font = ImageFont.truetype(FONT_PATH, 21)
        draw.rectangle([0, 0, img.shape[1], 58], fill=(24, 26, 34))
        draw.text((24, 12), "当前可点击线条：%d 条（编号+方向在外围，不遮挡箭头）" % count,
                  font=font, fill=(255, 255, 255))
        for badge in badges:
            label = "%d%s" % (badge["label"], DIR_CN[badge["direction"]])
            box = draw.textbbox((0, 0), label, font=badge_font)
            tw, th = box[2] - box[0], box[3] - box[1]
            draw.text((badge["x"] - tw / 2 - box[0], badge["y"] - th / 2 - box[1]),
                      label, font=badge_font, fill=(255, 255, 255))
        return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    except (OSError, ValueError):
        cv2.rectangle(img, (0, 0), (img.shape[1], 58), (24, 26, 34), -1)
        cv2.putText(img, "CLICKABLE LINES: %d (labels outside arrows)" % count,
                    (24, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        for badge in badges:
            label = "%d%s" % (badge["label"], badge["direction"][0].upper())
            cv2.putText(img, label, (badge["x"] - 16, badge["y"] + 7),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return img


def _badge_center(img, xs, ys, step, tip, direction, radius, placed):
    """把标记放到箭头尖端外侧的空白区，并与已放好的标记错开。"""
    dj, dk = DIR_VECTORS[direction]
    x, y = xs[tip[1]], ys[tip[0]]
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    px_dir, py_dir = -dj, dk  # 与箭头方向垂直的像素方向
    min_gap = 2 * radius + 6
    fallback = None
    for mult in (1.3, 1.8, 2.3, 2.8):
        for perp in (0, 1, -1, 2, -2, 3, -3):
            cx = int(round(x + dk * step * mult + px_dir * step * perp))
            cy = int(round(y + dj * step * mult + py_dir * step * perp))
            if not (radius + 4 <= cx < w - radius - 4
                    and radius + 4 <= cy < h - radius - 4):
                continue
            if fallback is None:
                fallback = (cx, cy)
            if any((cx - ox) ** 2 + (cy - oy) ** 2 < min_gap ** 2
                   for ox, oy in placed):
                continue
            patch = gray[cy - 6:cy + 7, cx - 6:cx + 7]
            if float((patch < 100).mean()) < 0.15:
                return cx, cy
    return fallback if fallback is not None else (int(x), int(y))


def annotate(img, info):
    """高亮当前可点击线条；编号与方向标记放在箭头外侧，避免遮挡箭头。"""
    vis = img.copy()
    overlay = vis.copy()
    xs, ys, step = info["xs"], info["ys"], info["step"]
    by_id = {line["id"]: line for line in info["lines"]}
    items = free_lines(info)
    radius = max(23, int(round(step * 0.95)))
    for item in items:
        line = by_id[item["id"]]
        color = PALETTE[(item["label"] - 1) % len(PALETTE)]
        # 跳过箭头尖端所在的第一段，彩色路径不覆盖箭头本体
        pts = np.array([[int(round(xs[k])), int(round(ys[j]))]
                        for j, k in line["nodes"][1:]], np.int32)
        if len(pts) >= 2:
            cv2.polylines(overlay, [pts], False, color,
                          max(5, int(round(step * 0.34))), cv2.LINE_AA)
    vis = cv2.addWeighted(overlay, 0.42, vis, 0.58, 0)

    badges = []
    placed = []
    for item in items:
        line = by_id[item["id"]]
        color = PALETTE[(item["label"] - 1) % len(PALETTE)]
        bx, by = _badge_center(img, xs, ys, step,
                               line["tip"], item["direction"], radius, placed)
        placed.append((bx, by))
        tx, ty = int(round(line["x"])), int(round(line["y"]))
        vx, vy = bx - tx, by - ty
        dist = (vx * vx + vy * vy) ** 0.5
        if dist > radius + 6:
            ex = int(round(bx - vx / dist * (radius + 2)))
            ey = int(round(by - vy / dist * (radius + 2)))
            cv2.arrowedLine(vis, (tx, ty), (ex, ey), color, 2,
                            cv2.LINE_AA, tipLength=0.35)
        cv2.circle(vis, (bx, by), radius, (20, 22, 30), -1, cv2.LINE_AA)
        cv2.circle(vis, (bx, by), radius, color, 4, cv2.LINE_AA)
        badges.append({
            "x": bx, "y": by,
            "label": item["label"], "direction": item["direction"],
        })
    return _draw_cn(vis, len(items), badges)


def main():
    ap = argparse.ArgumentParser(description="找出当前所有可点击线条并标注")
    ap.add_argument("--image", help="本地截图；不传则通过 adb 抓图")
    ap.add_argument("--device", help="adb 设备序列号")
    ap.add_argument("--output", default="outputs/lines_annotated.png")
    ap.add_argument("--json", default="outputs/lines_free.json")
    ap.add_argument("--steps", type=int, default=0,
                    help="可选：额外输出 N 步顺序规划（默认 0，只找当前可点击线条）")
    args = ap.parse_args()

    img = cv2.imread(args.image) if args.image else grab(args.device, check=True)
    info = analyze(img, steps=max(0, args.steps))
    items = free_lines(info)
    summary = {
        "grid": info["grid"],
        "line_count": len(info["lines"]),
        "free_now": len(items),
        "free_lines": items,
    }
    if info["plan"]:
        summary["plan"] = info["plan"]
    print(json.dumps(summary, ensure_ascii=False))
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        cv2.imwrite(args.output, annotate(img, info))
        print("saved", args.output, flush=True)
    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)
        print("saved", args.json, flush=True)
    print("当前可点击 %d 条" % len(items), flush=True)


if __name__ == "__main__":
    main()
