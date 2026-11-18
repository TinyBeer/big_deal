#!/usr/bin/env bash
# 找不同图片检测：一张已有图片 -> 差异检测 -> 标注输出（不含手机截图）
#
# 用法:
#   ./find_diff.sh <图片路径> [选项]
#   ./find_diff.sh -f <图片路径> [选项]
#
# 选项:
#   -o <目录>  输出目录，默认 ./outputs
#   -c <数量>  候选数上限，默认 25
#   -t <阈值>  ΔE 阈值，默认 14（漏检降到 10-11，误报多升到 16-18）
#   -h         显示帮助
#
# 依赖: python + numpy/Pillow/scipy（不需要 adb）
set -euo pipefail

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${FIND_DIFF_PYTHON:-/home/beer/.workbuddy/binaries/python/envs/default/bin/python}"
# /tmp 常是小容量 tmpfs，pip/matplotlib 之类会失败，统一改用大目录
export TMPDIR="${TMPDIR_OVERRIDE:-/home/beer/tmp}"
mkdir -p "$TMPDIR"

OUTDIR="./outputs"
COUNT=25
THR=14
SRC=""

usage() { sed -n '2,14p' "$0"; exit 0; }

# 手写解析：图片路径可以放在任意位置，和选项混排都行
while [ $# -gt 0 ]; do
  case "$1" in
    -o|--outdir) OUTDIR="$2"; shift 2 ;;
    -c|--count)  COUNT="$2";  shift 2 ;;
    -t|--thr)    THR="$2";    shift 2 ;;
    -f|--file)   SRC="$2";    shift 2 ;;
    -h|--help)   usage ;;
    -*) echo "错误: 未知选项 $1" >&2; usage ;;
    *)
      if [ -z "$SRC" ]; then SRC="$1"; else echo "错误: 多余参数 $1" >&2; usage; fi
      shift ;;
  esac
done

if [ -z "$SRC" ]; then
  echo "错误: 需要指定找不同图片路径（本脚本不负责手机截图，请先准备好图片）" >&2
  usage
fi

[ -f "$SRC" ] || { echo "错误: 文件不存在: $SRC" >&2; exit 1; }

# 纯色/全黑图（如误传锁屏截图）算出来全是噪声，提前拦掉
IMG_INFO=$("$PY" - "$SRC" <<'PY'
import sys
import numpy as np
from PIL import Image
im = Image.open(sys.argv[1])
a = np.asarray(im.convert("L"), dtype=np.float32)
print(im.width, im.height, round(float(a.std()), 1))
PY
)
read -r IMG_W IMG_H IMG_STD <<< "$IMG_INFO"
if [ "$(printf '%.0f' "$IMG_STD")" -lt 5 ]; then
  echo "错误: 图片几乎为纯色（${IMG_W}x${IMG_H}, std=${IMG_STD}），不是有效的找不同截图。" >&2
  exit 2
fi

mkdir -p "$OUTDIR"

echo "[1] 检测差异: $SRC (${IMG_W}x${IMG_H})"
"$PY" "$TOOL_DIR/spot_diff.py" "$SRC" --count "$COUNT" --thr "$THR" --outdir "$OUTDIR"

BASE="$(basename "$SRC")"
BASE="${BASE%.*}"
echo
echo "产物:"
echo "  标注图(preview): $OUTDIR/${BASE}_annotated_preview.png"
echo "  标注图(原尺寸): $OUTDIR/${BASE}_annotated.png"
echo "  对比清单:        $OUTDIR/${BASE}_contact.png"
echo "  坐标数据:        $OUTDIR/${BASE}_diffs.json"
