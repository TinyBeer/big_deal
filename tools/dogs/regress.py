#!/usr/bin/env python3
"""用已标注样本回归 dogs 识别。

默认跑 outputs/dogs_samples_20261125_114609/ground_truth.json 和第二批已验证样本。
未 verified 的样本仍会打分并标注 provisional，方便观察误判趋势。
"""

import argparse
import json
import os

import cv2

import dog_annotate

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_TRUTH = [
    os.path.join(ROOT, "outputs/dogs_samples_20261125_114609/ground_truth.json"),
    os.path.join(ROOT, "outputs/dogs_samples2_20261125_125549/ground_truth.json"),
]


def breed_key(label):
    if label in dog_annotate.BREED_CN:
        return label
    for key, cn in dog_annotate.BREED_CN.items():
        if label == cn:
            return key
    return label


def small_state(label):
    """旧真值里小窝可能写成品种名，现在只比较状态。"""
    if label in ("未解锁", "空", "有狗"):
        return label
    if label in dog_annotate.BREED_CN or label in dog_annotate.BREED_CN.values():
        return "有狗"
    return label


def compare(actual, expected):
    right = sum(a == b for a, b in zip(actual, expected))
    wrong = []
    for i, (a, b) in enumerate(zip(actual, expected)):
        if a != b:
            wrong.append("%d:%s->%s" % (i + 1, b, a))
    if len(actual) != len(expected):
        wrong.append("长度 %d!=%d" % (len(actual), len(expected)))
    return right, len(expected), wrong


def run(truth_paths, quiet=False):
    totals = {"houses": [0, 0], "smalls": [0, 0], "exit_dogs": [0, 0]}
    for truth_path in truth_paths:
        with open(truth_path, encoding="utf-8") as f:
            truth = json.load(f)
        sample_dir = truth.get("samples_dir") or os.path.dirname(truth_path)
        if not os.path.isabs(sample_dir):
            sample_dir = os.path.join(ROOT, sample_dir)
        print("\n== %s ==" % os.path.basename(sample_dir))
        for sample in truth["samples"]:
            img = cv2.imread(os.path.join(sample_dir, sample["image"]))
            if img is None:
                print("跳过（读图失败）:", sample["image"])
                continue
            result = dog_annotate.analyze(img)
            pred = {
                "houses": [breed_key(h["label"]) for h in result["houses"]],
                "smalls": [s["label"] for s in result["smalls"]],
                "exit_dogs": [breed_key(d["label"]) for d in result["dogs"]],
            }
            expected = {
                "houses": sample.get("houses", []),
                "smalls": [small_state(s) for s in sample.get("smalls", [])],
                "exit_dogs": sample.get("exit_dogs", []),
            }
            verified = all(sample.get("verified", {}).values())
            tag = "verified" if verified else "provisional"
            parts = []
            for key in totals:
                right, total, wrong = compare(pred[key], expected[key])
                totals[key][0] += right
                totals[key][1] += total
                parts.append("%s %d/%d" % (key, right, total))
                if wrong and not quiet:
                    parts.append("  %s 差异: %s" % (key, " ".join(wrong)))
            print("%s [%s] %s" % (sample["image"], tag, " | ".join(parts)))
    print("\n合计: " + " ".join(
        "%s %d/%d (%.1f%%)" % (k, v[0], v[1], 100.0 * v[0] / max(v[1], 1))
        for k, v in totals.items()))
    all_right = sum(v[0] for v in totals.values())
    all_total = sum(v[1] for v in totals.values())
    print("总准确率: %d/%d (%.1f%%)" %
          (all_right, all_total, 100.0 * all_right / max(all_total, 1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--truth", nargs="*", default=DEFAULT_TRUTH,
                    help="ground_truth.json 路径，默认两批样本")
    ap.add_argument("--quiet", action="store_true", help="只打印汇总")
    args = ap.parse_args()
    run(args.truth, quiet=args.quiet)


if __name__ == "__main__":
    main()
