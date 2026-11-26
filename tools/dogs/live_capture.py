#!/usr/bin/env python3
"""实机测试定时抓图：每 interval 秒抓一张，保存原图+标注图+识别摘要。"""

import argparse
import json
import os
import sys
import time

import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dog_annotate  # noqa: E402


def capture_once(outdir, idx):
    img = dog_annotate.grab(None)
    if img is None:
        return {"idx": idx, "error": "抓图失败"}
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    raw = os.path.join(outdir, "shot_%02d.png" % idx)
    annotated = os.path.join(outdir, "annotated_%02d.png" % idx)
    cv2.imwrite(raw, img)
    record = {"idx": idx, "time": ts, "raw": os.path.basename(raw),
              "annotated": os.path.basename(annotated)}
    try:
        result = dog_annotate.analyze(img)
        cv2.imwrite(annotated, dog_annotate.annotate(img, result))
        record["summary"] = {
            "houses": [h["label"] for h in result["houses"]],
            "smalls": [s["label"] for s in result["smalls"]],
            "exit_dogs": [d["label"] for d in result["dogs"]],
            "methods": [d.get("method") for d in result["dogs"]],
        }
    except Exception as exc:
        record["error"] = repr(exc)
    with open(os.path.join(outdir, "summary.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print("[%s] %d 已保存 %s" % (ts, idx, raw), flush=True)
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="outputs/dogs_live")
    ap.add_argument("--interval", type=float, default=60.0)
    ap.add_argument("--count", type=int, default=15)
    ap.add_argument("--first-delay", type=float, default=5.0)
    args = ap.parse_args()
    outdir = os.path.abspath(args.output)
    os.makedirs(outdir, exist_ok=True)
    print("实机采集目录: %s，间隔 %.0fs，最多 %d 张" %
          (outdir, args.interval, args.count), flush=True)
    time.sleep(max(0, args.first_delay))
    for idx in range(1, max(1, args.count) + 1):
        if idx > 1:
            time.sleep(max(0, args.interval))
        capture_once(outdir, idx)
    print("采集完成", flush=True)


if __name__ == "__main__":
    main()
