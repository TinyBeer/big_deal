#!/usr/bin/env bash
# 沙画收集辅助统一入口
#
# 用法:
#   tools/sand/quick.sh --once                      # 只识别一次，输出标注图
#   tools/sand/quick.sh --dry-run                   # 演示第一步（不真点）
#   tools/sand/quick.sh                             # 默认 --auto：解锁到加号消失 + 自动打通单关
#   tools/sand/quick.sh --no-unlock --no-notify --max-clicks 5
#   tools/sand/quick.sh --device <serial>           # 指定 adb 设备
#   tools/sand/quick.sh --repeat-limit 5            # 同槽色连续 5 轮后随机选桶
#   tools/sand/quick.sh --batch-size 3              # 每批最多点 3 个不重复色（0=不限）
#   tools/sand/quick.sh --batch-gap 0.15            # 批次内点击间隔秒数
#
# 输出: outputs/sand_annotated.png（--once）/ outputs/sand_dryrun.png（--dry-run）
set -euo pipefail

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$TOOL_DIR/../.." && pwd)"
PY="${SAND_PYTHON:-/home/beer/.workbuddy/binaries/python/envs/default/bin/python}"
if [ ! -x "$PY" ]; then PY="$(command -v python3 || true)"; fi
if [ -z "$PY" ]; then
  echo "✗ 未找到 Python，请设置 SAND_PYTHON" >&2
  exit 1
fi
export PYTHONPATH="$TOOL_DIR${PYTHONPATH:+:$PYTHONPATH}"

for a in "$@"; do
  case "$a" in
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
  esac
done

mkdir -p "$ROOT/outputs"

if [[ " $* " != *" --device "* ]]; then
  DEV="$(adb devices 2>/dev/null | awk '/device$/{print $1; exit}')"
  if [ -n "$DEV" ]; then
    set -- "$@" --device "$DEV"
  fi
fi

if [[ " $* " == *" --once "* ]]; then
  echo "▶ 沙画收集 · 识别一次"
  exec "$PY" "$TOOL_DIR/sand_vision.py" --output "$ROOT/outputs/sand_annotated.png" "$@"
fi

if [[ " $* " == *" --dry-run "* ]]; then
  echo "▶ 沙画收集 · 试运行（不点击）"
else
  echo "▶ 沙画收集 · 自动模式（复活/通关立即停手）"
fi
exec "$PY" "$TOOL_DIR/sand_auto.py" "$@"
