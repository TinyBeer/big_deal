#!/usr/bin/env python3
"""
spot_diff.py — 找不同游戏的高效自动比对工具

相对"灰度分块求均值差"的四处关键改进：
  1. 边缘法切版面 : 用行/列梯度峰定位两幅图的边框，不靠方差（平板色区域方差低会误判）
  2. 抗混叠分层配准: 8x/2x/1x 块平均降采样 + 暴力搜索，确定亚像素级偏移
  3. ΔE + 最小位移差: CIELAB 色差，且每像素取 3x3 邻域 9 个位移下的最小值
     —— 抓得到"灰度相同"的纯色相变化，同时抹掉亚像素错位产生的细线假阳性
  4. 形状学筛选   : 开运算去细线 + 填充率/长宽比判据，只留真实物体差异

用法:
  python spot_diff.py <图片.png> [--count 15] [--thr 14] [--layout auto|v|h]
                      [--top y0,y1 --bot y0,y1] [--outdir outputs] [--quiet]
"""
import argparse
import json
import os
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------- 颜色
def srgb_to_lab(rgb):
    c = rgb.astype(np.float32) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]], dtype=np.float32)
    xyz = lin @ m.T
    wp = np.array([0.95047, 1.0, 1.08883], dtype=np.float32)
    t = xyz / wp
    d = 6.0 / 29.0
    f = np.where(t > d ** 3, np.cbrt(t), t / (3 * d * d) + 4.0 / 29.0)
    return np.stack([116.0 * f[..., 1] - 16.0,
                     500.0 * (f[..., 0] - f[..., 1]),
                     200.0 * (f[..., 1] - f[..., 2])], axis=-1)


def _blur1d(a, k, axis):
    if k <= 1:
        return a
    pad = k // 2
    padw = [(0, 0)] * a.ndim
    padw[axis] = (pad, pad + 1)
    ap = np.pad(a, padw, mode="edge")
    cs = np.cumsum(ap, axis=axis, dtype=np.float32)
    n = a.shape[axis]
    return (np.take(cs, np.arange(k, k + n), axis=axis)
            - np.take(cs, np.arange(0, n), axis=axis)) / float(k)


def blur2(a, k=3):
    return _blur1d(_blur1d(a, k, 0), k, 1)


# ---------------------------------------------------------------- 版面切分
def _edges(prof, min_gap=8, frac=0.45):
    """从梯度剖面里找边框位置：阈值取峰值的一定比例，再聚类防重"""
    prof = prof.copy()
    prof[:8] = 0
    prof[-8:] = 0
    thr = frac * float(prof.max())
    idx = np.where(prof > thr)[0]
    if len(idx) == 0:
        return []
    groups, cur = [], [int(idx[0])]
    for i in idx[1:]:
        if i - cur[-1] <= min_gap:
            cur.append(int(i))
        else:
            groups.append(cur); cur = [int(i)]
    groups.append(cur)
    return [g[int(np.argmax(prof[g]))] for g in groups]


def _block_down2(a, f):
    H, W = a.shape
    h, w = H // f, W // f
    return a[:h * f, :w * f].reshape(h, f, w, f).mean(axis=(1, 3))


def _axis_split(g):
    """假设两幅图沿轴 0 堆叠，用自相似周期法求 (起点, 周期, 残差)。

    原理：整幅图与自身平移 ph 后最相似，ph 即面板高度（含内容错位）；
    再在轴上滑动起点 y0，使 [y0, y0+ph) 与 [y0+ph, y0+2ph) 最匹配。
    不依赖边框峰，即使边框梯度弱也能切对。
    """
    f = 4
    gs = _block_down2(g, f)
    H4 = gs.shape[0]
    if H4 < 40:
        return None
    # 1) 周期：整图自差曲线的全局最小
    best = (1e18, 0)
    for dy4 in range(H4 // 6, H4 // 2):
        d = float(np.abs(gs[:H4 - dy4] - gs[dy4:]).mean())
        if d < best[0]:
            best = (d, dy4)
    ph = best[1] * f
    if ph < H4 // 8:
        return None
    # 2) 起点：滑动窗口自匹配（保证 y0+2*ph 不越界）
    p4 = ph // f
    n0 = max(1, g.shape[0] - 2 * ph) // f
    best2 = (1e18, 0)
    for y04 in range(n0):
        s1 = gs[y04:y04 + p4]
        s2 = gs[y04 + p4:y04 + 2 * p4]
        if s1.shape != s2.shape or s1.size == 0:
            continue
        d = float(np.abs(s1 - s2).mean())
        if d < best2[0]:
            best2 = (d, y04)
    y0 = best2[1] * f
    # 3) 起点精修 ±3（1x，列抽样加速）
    g1 = g[:, ::8]
    b = (1e18, y0)
    for dy in range(-3, 4):
        yy = y0 + dy
        if yy < 0 or yy + 2 * ph > g.shape[0]:
            continue
        d = float(np.abs(g1[yy:yy + ph] - g1[yy + ph:yy + 2 * ph]).mean())
        if d < b[0]:
            b = (d, yy)
    return int(b[1]), int(ph), float(b[0])


def split_panels(img, layout="auto", manual=None):
    a = np.asarray(img)
    H, W = a.shape[:2]
    g = a.astype(np.float32).mean(axis=2)

    if manual:
        (ty0, ty1), (by0, by1) = manual
        return a[ty0:ty1], a[by0:by1], {
            "mode": "manual", "top": [ty0, ty1], "bottom": [by0, by1]}

    if layout == "auto":
        rv = _axis_split(g)
        rh = _axis_split(g.T)
        cv = rv if rv else (0, 0, 1e18)
        ch = rh if rh else (0, 0, 1e18)
        layout = "v" if cv[2] <= ch[2] else "h"
        res = rv if layout == "v" else rh
    else:
        res = _axis_split(g if layout == "v" else g.T)

    if res is None:                      # 兜底：等分
        if layout == "v":
            mid = H // 2
            info = {"mode": "fallback-v", "top": [0, mid], "bottom": [mid, H]}
            return a[:mid], a[mid:], info
        mid = W // 2
        info = {"mode": "fallback-h", "top": [0, mid], "bottom": [mid, W]}
        return a[:, :mid], a[:, mid:], info

    y0, ph, resid = res
    if layout == "v":
        info = {"mode": "auto-v", "top": [y0, y0 + ph],
                "bottom": [y0 + ph, y0 + 2 * ph], "resid": round(resid, 2)}
        return a[y0:y0 + ph], a[y0 + ph:y0 + 2 * ph], info
    x0, ph = y0, ph
    info = {"mode": "auto-h", "top": [x0, x0 + ph],
            "bottom": [x0 + ph, x0 + 2 * ph], "resid": round(resid, 2)}
    return a[:, x0:x0 + ph], a[:, x0 + ph:x0 + 2 * ph], info


# ---------------------------------------------------------------- 配准
def _down(a, f):
    """块平均降采样（抗混叠，比 stride 切片可靠）"""
    if f == 1:
        return a
    H, W = a.shape
    h, w = H // f, W // f
    return a[:h * f, :w * f].reshape(h, f, w, f).mean(axis=(1, 3))


def _score(tg, bg, dy, dx):
    H, W = tg.shape
    y0, y1 = max(0, dy), min(H, H + dy)
    x0, x1 = max(0, dx), min(W, W + dx)
    if y1 - y0 < 8 or x1 - x0 < 8:
        return 1e18
    return float(np.abs(tg[y0:y1, x0:x1] - bg[y0 - dy:y1 - dy, x0 - dx:x1 - dx]).mean())


def estimate_shift(top, bot, max_shift=40):
    """返回 (dy, dx, 残差)，语义：bot[y+dy, x+dx] ≈ top[y, x]"""
    tg = top.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
    bg = bot.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)

    def search(f, cy, cx, rad):
        t, b = _down(tg, f), _down(bg, f)
        best = (1e18, cy, cx)
        for dy in range(cy - rad, cy + rad + 1):
            for dx in range(cx - rad, cx + rad + 1):
                s = _score(t, b, dy, dx)
                if s < best[0]:
                    best = (s, dy, dx)
        return best

    s, dy, dx = search(8, 0, 0, max(1, max_shift // 8))
    s, dy, dx = search(4, dy * 2, dx * 2, 3)
    s, dy, dx = search(2, dy * 2, dx * 2, 3)
    s, dy, dx = search(1, dy * 2, dx * 2, 2)
    return dy, dx, s


# ---------------------------------------------------------------- 差异
def shift_tolerant_diff(tl, bl, rad=1):
    """每像素取 (2r+1)^2 个位移下的最小 ΔE，抗局部错位/轻微缩放"""
    H, W = tl.shape[:2]
    best = np.full((H, W), 1e9, dtype=np.float32)
    for dy in range(-rad, rad + 1):
        for dx in range(-rad, rad + 1):
            y0, y1 = max(0, -dy), min(H, H - dy)
            x0, x1 = max(0, -dx), min(W, W - dx)
            de = np.sqrt(((tl[y0:y1, x0:x1] - bl[y0 + dy:y1 + dy,
                                              x0 + dx:x1 + dx]) ** 2).sum(axis=2))
            np.minimum(best[y0:y1, x0:x1], de, out=best[y0:y1, x0:x1])
    return best


def detect(diff, thr=14.0, min_area=45, min_side=6, min_fill=0.30,
           merge_px=6, join_px=0):
    from scipy import ndimage as ndi

    H, W = diff.shape
    mask = diff > thr
    st = np.ones((3, 3), bool)
    mask = ndi.binary_dilation(ndi.binary_erosion(mask, st), st)   # 开运算去细线
    mask = ndi.binary_closing(mask, st, iterations=1)
    if not mask.any():
        return []

    # 预清理：直接从掩码中删除全宽/全高的细条纹（面板拼接边界、渲染横纹）。
    # 若留到组件阶段再过滤，邻近的真实差异会经 grown 膨胀与条纹连成一体，
    # 导致整个组件（含真差异）被误杀（如紧贴底边的植物叶片漏检）
    def strip_seams(m, axis):
        prof = m.mean(axis=axis)          # 每行(axis=1)/列(axis=0)覆盖率
        full = prof > 0.80
        # 连续满覆盖段的厚度 ≤ 20 才视为接缝
        idx = np.where(full)[0]
        if len(idx) == 0:
            return m
        bands, s = [], idx[0]
        for a, b in zip(idx, idx[1:]):
            if b != a + 1:
                bands.append((s, a)); s = b
        bands.append((s, idx[-1]))
        for s, e in bands:
            if e - s + 1 <= 20:
                if axis == 1:
                    m[s:e + 1, :] = False
                else:
                    m[:, s:e + 1] = False
        return m

    mask = strip_seams(mask, axis=1)      # 水平条纹
    mask = strip_seams(mask, axis=0)      # 垂直条纹

    grown = ndi.binary_dilation(mask, st, iterations=max(1, merge_px // 2))
    lab, _ = ndi.label(grown)

    boxes = []
    for sl in ndi.find_objects(lab):
        if sl is None:
            continue
        m = mask[sl]
        if not m.any():
            continue
        ys, xs = np.where(m)
        y0, y1 = sl[0].start + ys.min(), sl[0].start + ys.max() + 1
        x0, x1 = sl[1].start + xs.min(), sl[1].start + xs.max() + 1
        # 孔洞填充：弱对比物体（如白枕贴白帘）内部差异低，掩码呈空心环，
        # 填洞后再算面积/填充率，避免被 min_fill 误杀；噪声细线无封闭孔洞不受影响
        m_filled = ndi.binary_fill_holes(m)
        area = int(m_filled.sum())
        w, h = int(x1 - x0), int(y1 - y0)
        if area < min_area or w < min_side or h < min_side:
            continue
        fill = area / float(w * h)
        de = diff[sl][m]
        mean_de, max_de = float(de.mean()), float(de.max())
        # 强信号救援：弱对比物体（白枕贴白帘等）差异只出现在轮廓散点上，
        # 填充率天然低；若掩码面积和平均ΔE都足够强，仍视为真实差异。
        # 尺寸上限防止把全图散布的渲染噪声场救进来
        strong = (200 <= area <= 8000 and w <= 150 and h <= 150
                  and fill >= 0.12 and mean_de >= 25 and max_de >= 40)
        if fill < min_fill and not strong:
            continue
        # 全宽/全高的细接缝伪影（两幅图拼接边界、渲染横纹）
        if (w >= 0.9 * W and h <= 15) or (h >= 0.9 * H and w <= 15):
            continue
        boxes.append({"bbox": [int(x0), int(y0), w, h], "area": area,
                      "fill": round(float(fill), 2),
                      "mean_de": round(mean_de, 1),
                      "max_de": round(max_de, 1),
                      "score": round(mean_de * np.sqrt(area), 1)})

    # 同一物体的多个碎片：并集包围盒
    changed = True
    while changed:
        changed = False
        out = []
        while boxes:
            cur = boxes.pop()
            cx0, cy0, cw, ch = cur["bbox"]
            i = 0
            while i < len(boxes):
                ox0, oy0, ow, oh = boxes[i]["bbox"]
                if not (ox0 > cx0 + cw + join_px // 2 or ox0 + ow < cx0 - join_px // 2
                        or oy0 > cy0 + ch + join_px // 2 or oy0 + oh < cy0 - join_px // 2):
                    nx0, ny0 = min(cx0, ox0), min(cy0, oy0)
                    nx1, ny1 = max(cx0 + cw, ox0 + ow), max(cy0 + ch, oy0 + oh)
                    cur["bbox"] = [nx0, ny0, nx1 - nx0, ny1 - ny0]
                    cur["area"] += boxes[i]["area"]
                    cur["mean_de"] = max(cur["mean_de"], boxes[i]["mean_de"])
                    cur["max_de"] = max(cur["max_de"], boxes[i]["max_de"])
                    cur["score"] = round(cur["mean_de"] * np.sqrt(cur["area"]), 1)
                    boxes.pop(i); changed = True
                    cx0, cy0, cw, ch = cur["bbox"]
                else:
                    i += 1
            out.append(cur)
        boxes = out

    boxes.sort(key=lambda b: -b["score"])
    return boxes


# ---------------------------------------------------------------- 输出
def _font(size):
    for p in ("/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_annotated(img, info, results):
    im = img.copy()
    dr = ImageDraw.Draw(im)
    f = _font(30)
    v = info["mode"].endswith("v")
    t0, b0 = info["top"][0], info["bottom"][0]
    for i, r in enumerate(results, 1):
        x, y, w, h = r["bbox"]
        rects = ([(x, t0 + y, x + w, t0 + y + h), (x, b0 + y, x + w, b0 + y + h)]
                 if v else
                 [(t0 + x, y, t0 + x + w, y + h), (b0 + x, y, b0 + x + w, y + h)])
        for bx0, by0, bx1, by1 in rects:
            dr.rectangle([bx0 - 5, by0 - 5, bx1 + 5, by1 + 5],
                         outline=(232, 30, 30), width=5)
            cx, cy = bx0 + 16, by0 + 16
            dr.ellipse([cx - 19, cy - 19, cx + 19, cy + 19],
                       fill=(232, 30, 30), outline=(255, 255, 255), width=3)
            tw = dr.textlength(str(i), font=f)
            dr.text((cx - tw / 2, cy - 16), str(i), fill=(255, 255, 255), font=f)
    return im


def draw_contact_sheet(img, info, results, pad=70, per_row=2, cw=400):
    v = info["mode"].endswith("v")
    t0, b0 = info["top"][0], info["bottom"][0]
    pw = info["top"][1] - info["top"][0]
    W, H = img.size
    rows = (len(results) + per_row - 1) // per_row
    cell = int(cw * 0.78) + 32
    sheet = Image.new("RGB", (per_row * (cw * 2 + 20) + 12, rows * cell + 12),
                      (246, 246, 246))
    dr = ImageDraw.Draw(sheet)
    f = _font(19)
    for i, r in enumerate(results):
        x, y, w, h = r["bbox"]
        cxm, cym = x + w // 2, y + h // 2
        half = max(w, h) // 2 + pad
        if v:
            ax0, ay0 = max(0, cxm - half), max(0, cym - half)
            ax1, ay1 = min(W, cxm + half), min(pw, cym + half)
            tc = img.crop((ax0, t0 + ay0, ax1, t0 + ay1))
            bc = img.crop((ax0, b0 + ay0, ax1, b0 + ay1))
        else:
            ax0, ay0 = max(0, cxm - half), max(0, cym - half)
            ax1, ay1 = min(pw, cxm + half), min(H, cym + half)
            tc = img.crop((t0 + ax0, ay0, t0 + ax1, ay1))
            bc = img.crop((b0 + ax0, ay0, b0 + ax1, ay1))
        th = max(1, int(cw * tc.size[1] / max(1, tc.size[0])))
        tc = tc.resize((cw, th), Image.LANCZOS)
        bc = bc.resize((cw, th), Image.LANCZOS)
        rx = (i % per_row) * (cw * 2 + 20) + 8
        ry = (i // per_row) * cell + 28
        sheet.paste(tc, (rx, ry)); sheet.paste(bc, (rx + cw + 4, ry))
        dr.rectangle([rx - 1, ry - 1, rx + cw * 2 + 3, ry + th],
                     outline=(200, 60, 60), width=2)
        dr.text((rx, ry - 22),
                f"#{i + 1}  score={r['score']}  dE={r['mean_de']}  pos=({x},{y})",
                fill=(20, 20, 20), font=f)
    return sheet


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--count", type=int, default=0)
    ap.add_argument("--thr", type=float, default=14.0)
    ap.add_argument("--layout", default="auto", choices=["auto", "v", "h"])
    ap.add_argument("--top", default=None)
    ap.add_argument("--bot", default=None)
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    T = time.time()

    def log(*s):
        if not args.quiet:
            print(*s, flush=True)

    img = Image.open(args.image).convert("RGB")
    manual = None
    if args.top and args.bot:
        manual = [tuple(int(v) for v in args.top.split(",")),
                  tuple(int(v) for v in args.bot.split(","))]
    top, bot, info = split_panels(img, args.layout, manual)
    log(f"[1] 版面 {info['mode']} 上幅{info['top']} 下幅{info['bottom']} "
        f"-> {top.shape[1]}x{top.shape[0]}  ({time.time()-T:.2f}s)")

    dy, dx, sc = estimate_shift(top, bot)
    log(f"[2] 配准 dy={dy} dx={dx} 残差={sc:.2f}  ({time.time()-T:.2f}s)")

    h, w = top.shape[:2]
    y0, y1 = max(0, dy), min(h, h + dy)
    x0, x1 = max(0, dx), min(w, w + dx)
    t_al, b_al = top[y0:y1, x0:x1], bot[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
    log(f"    重叠区 {t_al.shape[1]}x{t_al.shape[0]}")

    tl, bl = srgb_to_lab(t_al), srgb_to_lab(b_al)
    tl = np.stack([blur2(tl[..., i]) for i in range(3)], -1)
    bl = np.stack([blur2(bl[..., i]) for i in range(3)], -1)
    log(f"[3] Lab + 去噪  ({time.time()-T:.2f}s)")

    diff = shift_tolerant_diff(tl, bl, 1)
    log(f"[4] 抗错位 ΔE 图  p99={np.percentile(diff,99):.1f} "
        f"({time.time()-T:.2f}s)")

    boxes = detect(diff, thr=args.thr)
    n = args.count if args.count > 0 else len(boxes)
    res = boxes[:n]
    for b in res:
        b["bbox"] = [b["bbox"][0] + x0, b["bbox"][1] + y0,
                     b["bbox"][2], b["bbox"][3]]
    log(f"[5] 候选 {len(boxes)} 个，输出 top{len(res)}  ({time.time()-T:.2f}s)")
    for i, b in enumerate(res, 1):
        log(f"    #{i:2d} score={b['score']:8.1f} dE={b['mean_de']:5.1f} "
            f"fill={b['fill']:.2f} bbox={b['bbox']}")

    base = os.path.splitext(os.path.basename(args.image))[0]
    ann = draw_annotated(img, info, res)
    p1 = os.path.join(args.outdir, f"{base}_annotated.png")
    ann.save(p1)
    W, H = ann.size
    ann.resize((W // 2, H // 2), Image.LANCZOS).save(
        os.path.join(args.outdir, f"{base}_annotated_preview.png"))
    p2 = os.path.join(args.outdir, f"{base}_contact.png")
    draw_contact_sheet(img, info, res).save(p2)
    with open(os.path.join(args.outdir, f"{base}_diffs.json"), "w") as fh:
        json.dump({"info": info, "offset": [dy, dx], "diffs": res},
                  fh, ensure_ascii=False, indent=1)
    log(f"[6] {p1}\n    {p2}\n总计 {time.time()-T:.2f}s")


if __name__ == "__main__":
    main()
