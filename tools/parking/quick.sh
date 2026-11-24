#!/usr/bin/env bash
# 停车场接客辅助统一入口
#
# 用法:
#   tools/parking/quick.sh --dry-run              # 演示第一步（不点击）
#   tools/parking/quick.sh                        # 默认 --auto，自动打通单关
#   tools/parking/quick.sh --once                 # 只识别一次，输出标注图
#   tools/parking/quick.sh --no-unlock            # 跳过开局解锁
#   tools/parking/quick.sh --device <serial>      # 指定 adb 设备
#
# 输出: outputs/parking_annotated.png（--once）
#
# 解释器: 见 tools/common/python_env.sh（PARKING_PYTHON > 当前激活环境 > PATH）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT/tools/common/shell_runtime.sh"
tool_init_env PARKING_PYTHON "$0" || exit 1

for a in "$@"; do
  case "$a" in
    -h|--help) tool_print_help 2 13 "$0"; exit 0 ;;
  esac
done

tool_ensure_outputs

if [[ " $* " == *" --once "* ]]; then
  echo "▶ 停车场接客 · 识别一次"
  tool_strip_flag --once "$@"
  exec "$PY" "$TOOL_DIR/parking_vision.py" --output "$ROOT/outputs/parking_annotated.png" "${STRIPPED_ARGS[@]}"
fi

echo "▶ 停车场接客 · 自动模式（默认打通单关）"
exec "$PY" "$TOOL_DIR/parking_auto.py" "$@"
