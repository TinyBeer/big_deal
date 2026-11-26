#!/usr/bin/env python3
"""从已标注样本截图生成固定匹配模板（带 alpha mask）。

用法：
  tools/dogs/quick.sh --make-templates       # 也可直接运行本脚本
  python tools/dogs/make_templates.py
"""

import argparse
import json
import os

import cv2

import fixed_match

ROOT = fixed_match.ROOT


def build(spec_path=fixed_match.SPECS_PATH, out_dir=fixed_match.FIXED_DIR, force=False):
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    aliases = {k: v for k, v in spec.items() if isinstance(v, str)}
    manifest = []
    for kind in ("exit", "house"):
        kind_dir = os.path.join(out_dir, kind)
        os.makedirs(kind_dir, exist_ok=True)
        if force:
            for old in os.listdir(kind_dir):
                if old.lower().endswith(".png"):
                    os.remove(os.path.join(kind_dir, old))
    for idx, entry in enumerate(spec["entries"], 1):
        kind = entry["kind"]
        breed = entry["breed"]
        rel = aliases.get(entry["image"], entry["image"])
        image_path = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
        rgba = fixed_match.extract_template(image_path, entry)
        name = "%s__%s_%02d.png" % (breed, entry["image"], idx)
        out_path = os.path.join(out_dir, kind, name)
        if not force and os.path.exists(out_path):
            continue
        cv2.imwrite(out_path, rgba)
        manifest.append({"file": "%s/%s" % (kind, name), "breed": breed,
                         "kind": kind, "source": rel, "center": entry["center"],
                         "size": int(entry.get("size", fixed_match.SIZES[kind]))})
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("生成模板 %d 张: %s" % (len(manifest), out_dir))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=fixed_match.SPECS_PATH)
    ap.add_argument("--output-dir", default=fixed_match.FIXED_DIR)
    ap.add_argument("--force", action="store_true", help="覆盖已有模板")
    args = ap.parse_args()
    build(args.spec, args.output_dir, args.force)


if __name__ == "__main__":
    main()
