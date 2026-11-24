#!/usr/bin/env bash
# 色块入槽辅助统一入口
#
# 用法:
#   tools/slots/quick.sh --once                 # 只识别一次，输出标注图
#   tools/slots/quick.sh --dry-run              # 演示第一步（解锁/选块，不真点）
#   tools/slots/quick.sh                        # 默认 --auto：解锁 + 自动点击单关
#   tools/slots/quick.sh --no-unlock --no-notify --max-clicks 5
#   tools/slots/quick.sh --device <serial>      # 指定 adb 设备
#
# 输出: outputs/slots_annotated.png（--once）/ outputs/slots_dryrun.png（--dry-run）
#
# 解释器: 见 tools/common/python_env.sh（SLOTS_PYTHON > 当前激活环境 > PATH）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT/tools/common/shell_runtime.sh"
tool_init_env SLOTS_PYTHON "$0" || exit 1

for a in "$@"; do
  case "$a" in
    -h|--help) tool_print_help 2 13 "$0"; exit 0 ;;
  esac
done

tool_ensure_outputs
tool_auto_device --device "$@"; set -- "${TOOL_ARGS[@]}"

if [[ " $* " == *" --once "* ]]; then
  echo "▶ 色块入槽 · 识别一次"
  exec "$PY" "$TOOL_DIR/slots_vision.py" --output "$ROOT/outputs/slots_annotated.png" "$@"
fi

if [[ " $* " == *" --dry-run "* ]]; then
  echo "▶ 色块入槽 · 试运行（不点击）"
else
  echo "▶ 色块入槽 · 自动模式（复活/胜利立即停手）"
fi
exec "$PY" "$TOOL_DIR/slots_auto.py" "$@"
