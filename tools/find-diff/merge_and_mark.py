import json, sys
from PIL import Image, ImageDraw, ImageFont

SRC = sys.argv[1]
JS = sys.argv[2]
OUT = sys.argv[3]

d = json.load(open(JS))
top0 = d["info"]["top"][0]
off = d["info"]["bottom"][0] - d["info"]["top"][0]

boxes = []
for c in d["diffs"]:
    x, y, w, h = c["bbox"]
    boxes.append([x, y + top0, w, h])

# 合并眼睛区域的三个碎框（面积小 + 彼此邻近）
def merge_small(boxes):
    small = [b for b in boxes if b[2] * b[3] < 120]
    big = [b for b in boxes if b[2] * b[3] >= 120]
    used, merged = set(), []
    for i, b in enumerate(small):
        if i in used:
            continue
        g = b[:]
        for j in range(i + 1, len(small)):
            if j in used:
                continue
            c = small[j]
            if not (g[0] > c[0] + c[2] + 40 or c[0] > g[0] + g[2] + 40 or
                    g[1] > c[1] + c[3] + 40 or c[1] > g[1] + g[3] + 40):
                x0 = min(g[0], c[0]); y0 = min(g[1], c[1])
                x1 = max(g[0] + g[2], c[0] + c[2]); y1 = max(g[1] + g[3], c[1] + c[3])
                g = [x0, y0, x1 - x0, y1 - y0]
                used.add(j)
        merged.append(g)
    return big + merged

boxes = merge_small(boxes)
# 排序：从上到下、从左到右
boxes.sort(key=lambda b: (b[1] // 60, b[0]))

img = Image.open(SRC).convert("RGB")
dr = ImageDraw.Draw(img)
font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 26)
RED = (255, 32, 32)

for i, (x, y, w, h) in enumerate(boxes, 1):
    for by in (y, y + off):
        dr.rectangle([x - 3, by - 3, x + w + 3, by + h + 3], outline=RED, width=4)
        label = str(i)
        tb = dr.textbbox((0, 0), label, font=font)
        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        lx, ly = x - 3, by - 3 - th - 10
        if ly < 0:
            ly = by + h + 6
        dr.rectangle([lx, ly, lx + tw + 10, ly + th + 10], fill=RED)
        dr.text((lx + 5, ly + 4), label, font=font, fill=(255, 255, 255))

img.save(OUT)
img.resize((img.width // 2, img.height // 2), Image.LANCZOS).save(OUT.replace(".png", "_preview.png"))

# 生成合并后的对比清单
PAD = 70
cols, rows = 2, (len(boxes) + 1) // 2
cw, ch = 300, 230
sheet = Image.new("RGB", (cols * (cw * 2 + 20) + 30, rows * (ch + 40) + 20), (250, 250, 250))
sdr = ImageDraw.Draw(sheet)
f2 = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 18)
for i, (x, y, w, h) in enumerate(boxes, 1):
    r, c = (i - 1) // cols, (i - 1) % cols
    ox = 20 + c * (cw * 2 + 20)
    oy = 20 + r * (ch + 40)
    x0 = max(0, x - PAD); y0 = max(top0, y - PAD)
    x1 = min(img.width, x + w + PAD); y1 = min(top0 + off, y + h + PAD)
    # 防御：布局误判/贴边时保证裁剪框有效
    if x1 - x0 < 12: x1 = min(img.width, x0 + 12)
    if y1 - y0 < 12: y1 = min(top0 + off, y0 + 12)
    if x1 - x0 < 2 or y1 - y0 < 2: continue
    tc = img.crop((x0, y0, x1, y1 + 0))
    bc = Image.open(SRC).convert("RGB").crop((x0, y0 + off, x1, y1 + off))
    tc.thumbnail((cw, ch), Image.LANCZOS); bc.thumbnail((cw, ch), Image.LANCZOS)
    sheet.paste(tc, (ox, oy + 22)); sheet.paste(bc, (ox + cw + 10, oy + 22))
    sdr.text((ox, oy), f"#{i} ({x},{y})", font=f2, fill=(200, 0, 0))
    sdr.rectangle([ox, oy + 22, ox + cw, oy + 22 + ch], outline=(180, 180, 180))
    sdr.rectangle([ox + cw + 10, oy + 22, ox + cw + 10 + cw, oy + 22 + ch], outline=(180, 180, 180))
sheet.save(OUT.replace(".png", "_contact.png"))
print("boxes:", len(boxes))
for i, b in enumerate(boxes, 1):
    print(i, b)
