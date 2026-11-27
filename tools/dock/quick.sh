#!/usr/bin/env bash
# 螺丝接驳位解锁统一入口
#
# 用法:
#   tools/dock/quick.sh --once        # 只识别一次，输出标注图
#   tools/dock/quick.sh --dry-run     # 只演示第一步（不点击）
#   tools/dock/quick.sh               # 默认自动解锁，直到没有「解锁」按钮
#   tools/dock/quick.sh --max-unlock 3 --ad-wait 18
#   tools/dock/quick.sh --device <serial>
#
# 输出: outputs/dock_annotated.png（--once）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT/tools/common/shell_runtime.sh"
tool_init_env DOCK_PYTHON "$0" || exit 1

for a in "$@"; do
  case "$a" in
    -h|--help) tool_print_help 2 11 "$0"; exit 0 ;;
  esac
done

tool_ensure_outputs

if [[ " $* " == *" --once "* ]]; then
  echo "▶ 接驳位解锁 · 识别一次"
  tool_strip_flag --once "$@"
  exec "$PY" "$TOOL_DIR/dock_vision.py" --output "$ROOT/outputs/dock_annotated.png" "${STRIPPED_ARGS[@]}"
fi

echo "▶ 接驳位解锁 · 自动模式"
exec "$PY" "$TOOL_DIR/dock_auto.py" "$@"
