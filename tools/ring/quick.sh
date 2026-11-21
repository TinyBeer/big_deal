#!/usr/bin/env bash
# 环形岛接客辅助统一入口
#
# 用法:
#   tools/ring/quick.sh --once                 # 只识别一次，输出标注图
#   tools/ring/quick.sh --dry-run              # 演示第一步（关弹窗/解锁/选车，不真点）
#   tools/ring/quick.sh                        # 默认 --auto，自动打通单关
#   tools/ring/quick.sh --no-unlock            # 跳过开局解锁接驳位
#   tools/ring/quick.sh --device <serial>      # 指定 adb 设备
#
# 输出: outputs/ring_annotated.png（--once）/ outputs/ring_dryrun.png（--dry-run）
set -euo pipefail

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$TOOL_DIR/../.." && pwd)"
PY="${RING_PYTHON:-/home/beer/.workbuddy/binaries/python/envs/default/bin/python}"
if [ ! -x "$PY" ]; then PY="$(command -v python3 || true)"; fi
if [ -z "$PY" ]; then
  echo "✗ 未找到 Python，请设置 RING_PYTHON" >&2
  exit 1
fi
export PYTHONPATH="$TOOL_DIR${PYTHONPATH:+:$PYTHONPATH}"

for a in "$@"; do
  case "$a" in
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
  esac
done

mkdir -p "$ROOT/outputs"

# --device 未指定时自动探测已连接的 adb 设备
if [[ " $* " != *" --device "* ]]; then
  DEV="$(adb devices 2>/dev/null | awk '/device$/{print $1; exit}')"
  if [ -n "$DEV" ]; then
    set -- "$@" --device "$DEV"
  fi
fi

if [[ " $* " == *" --once "* ]]; then
  echo "▶ 环形岛接客 · 识别一次"
  exec "$PY" "$TOOL_DIR/ring_vision.py" --output "$ROOT/outputs/ring_annotated.png" "$@"
fi

echo "▶ 环形岛接客 · 自动模式（默认打通单关）"
exec "$PY" "$TOOL_DIR/ring_auto.py" "$@"
