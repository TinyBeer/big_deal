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
#
# 解释器: 见 tools/common/python_env.sh（ANTS_PYTHON > 当前激活环境 > PATH）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT/tools/common/shell_runtime.sh"
tool_init_env ANTS_PYTHON "$0" || exit 1

for a in "$@"; do
  case "$a" in
    -h|--help) tool_print_help 2 19 "$0"; exit 0 ;;
  esac
done

tool_ensure_outputs
tool_auto_device --device "$@"; set -- "${TOOL_ARGS[@]}"

if [[ " $* " == *" --once "* ]]; then
  echo "▶ 搬砖大战 · 识别一次"
  tool_strip_flag --once "$@"
  ARGS=("${STRIPPED_ARGS[@]}")
  exec "$PY" "$TOOL_DIR/ants_vision.py" --output "$ROOT/outputs/ants_annotated.png" "${ARGS[@]}"
fi

if [[ " $* " == *" --dry-run "* ]]; then
  echo "▶ 搬砖大战 · 试运行（不点击）"
else
  echo "▶ 搬砖大战 · 自动搬运（福利弹窗自动关闭）"
fi
exec "$PY" "$TOOL_DIR/ants_auto.py" "$@"
