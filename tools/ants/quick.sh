#!/usr/bin/env bash
# 搬砖大战（蚂蚁搬像素）辅助统一入口
#
# 用法:
#   tools/ants/quick.sh --once                       # 只识别一次，输出标注图
#   tools/ants/quick.sh --dry-run --max-clicks 3     # 试运行，不真点
#   tools/ants/quick.sh                              # 默认：看广告解锁 + 自动搬运
#   tools/ants/quick.sh --no-unlock                  # 跳过看广告解锁
#   tools/ants/quick.sh --max-clicks 20 --batch-size 4
#   tools/ants/quick.sh --idle-timeout 20             # 连续无法决策 20 秒后停止（默认）
#   tools/ants/quick.sh --repeat-delay 8              # 已点未入槽的颜色 8 秒内不重复点
#   tools/ants/quick.sh --no-notify                    # 结束时不发手机状态栏通知（默认发）
#   tools/ants/quick.sh --notify-message "搬完了"      # 自定义通知内容
#   tools/ants/quick.sh --device <serial>
#   tools/ants/palette_calibrate.py                   # 从上方像素画重新标定颜色池
#
# 输出: outputs/ants_annotated.png（覆盖更新）
set -euo pipefail

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$TOOL_DIR/../.." && pwd)"
PY="${ANTS_PYTHON:-/home/beer/.workbuddy/binaries/python/envs/default/bin/python}"
if [ ! -x "$PY" ]; then PY="$(command -v python3 || true)"; fi
if [ -z "$PY" ]; then
  echo "✗ 未找到 Python，请设置 ANTS_PYTHON" >&2
  exit 1
fi
export PYTHONPATH="$TOOL_DIR${PYTHONPATH:+:$PYTHONPATH}"

for a in "$@"; do
  case "$a" in
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
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
  echo "▶ 搬砖大战 · 识别一次"
  ARGS=()
  for a in "$@"; do [ "$a" = "--once" ] || ARGS+=("$a"); done
  exec "$PY" "$TOOL_DIR/ants_vision.py" --output "$ROOT/outputs/ants_annotated.png" "${ARGS[@]}"
fi

if [[ " $* " == *" --dry-run "* ]]; then
  echo "▶ 搬砖大战 · 试运行（不点击）"
else
  echo "▶ 搬砖大战 · 自动搬运（福利弹窗自动关闭）"
fi
exec "$PY" "$TOOL_DIR/ants_auto.py" "$@"
