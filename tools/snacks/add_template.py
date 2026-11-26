#!/usr/bin/env python3
"""给本关商品目录补一个新模板：从截图裁 bbox 并写入 catalog.json。

用法示例：
  python add_template.py --image outputs/shot.png --file chips.png \
      --name 薯片 --category 零食 --box 100 1220 180 1360
"""
import argparse
import json
import os
import sys

import cv2

DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG = os.path.join(DIR, "catalog.json")


def main():
    ap = argparse.ArgumentParser(description="新增本关商品模板")
    ap.add_argument("--image", required=True)
    ap.add_argument("--file", required=True, help="模板文件名，如 chips.png")
    ap.add_argument("--name", required=True, help="中文名，如 薯片")
    ap.add_argument("--category", required=True, choices=["零食", "饮料"])
    ap.add_argument("--box", required=True, nargs=4, type=int,
                    metavar=("X1", "Y1", "X2", "Y2"))
    ap.add_argument("--force", action="store_true", help="同名模板允许覆盖")
    args = ap.parse_args()

    img = cv2.imread(args.image)
    if img is None:
        print("读图失败：%s" % args.image, file=sys.stderr)
        return 1
    x1, y1, x2, y2 = args.box
    if not (0 <= x1 < x2 <= img.shape[1] and 0 <= y1 < y2 <= img.shape[0]):
        print("box 越界", file=sys.stderr)
        return 1
    path = os.path.join(DIR, "templates", args.file)
    if os.path.exists(path) and not args.force:
        print("模板已存在，加 --force 覆盖：%s" % path, file=sys.stderr)
        return 1
    cv2.imwrite(path, img[y1:y2, x1:x2])

    with open(CATALOG, encoding="utf-8") as f:
        entries = json.load(f)
    entries = [e for e in entries if e["file"] != args.file]
    entries.append({"file": args.file, "name": args.name, "category": args.category})
    with open(CATALOG, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("已保存模板 %s（%s/%s）" % (path, args.category, args.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
