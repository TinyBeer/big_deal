#!/usr/bin/env bash
# 线条解放辅助统一入口
#
# 用法:
#   tools/lines/quick.sh                         # 默认自动：循环点击直到无可点击线条/命中停止条件
#   tools/lines/quick.sh --once                  # 只识别标注，不点击
#   tools/lines/quick.sh --image shot.png        # 用本地截图（配合 --dry-run 离线验证）
#   tools/lines/quick.sh --steps 5               # 可选：额外输出 5 步顺序规划（--once 下）
#   tools/lines/quick.sh --dry-run               # 试运行，只打印坐标
#   tools/lines/quick.sh --max-clicks 3 --batch-size 4 --gap 0.45 --click-log --no-notify
#   tools/lines/quick.sh --device <serial>
#
# 输出: outputs/lines_annotated.png / outputs/lines_free.json
#
# 解释器: 见 tools/common/python_env.sh（LINES_PYTHON > 当前激活环境 > PATH）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT/tools/common/shell_runtime.sh"
tool_init_env LINES_PYTHON "$0" || exit 1

for a in "$@"; do
  case "$a" in
    -h|--help) tool_print_help 2 15 "$0"; exit 0 ;;
  esac
done

tool_ensure_outputs
tool_auto_device --device "$@"; set -- "${TOOL_ARGS[@]}"

if [[ " $* " == *" --once "* ]]; then
  tool_strip_flag --once "$@"; set -- "${STRIPPED_ARGS[@]}"
  echo "▶ 线条解放 · 只识别标注（不点击）"
  exec "$PY" "$TOOL_DIR/lines_vision.py" \
    --output "$ROOT/outputs/lines_annotated.png" \
    --json "$ROOT/outputs/lines_free.json" "$@"
fi

tool_strip_flag --auto "$@"; set -- "${STRIPPED_ARGS[@]}"
echo "▶ 线条解放 · 自动模式（默认：点击箭头中心，复活页/爱心减少停手）"
exec "$PY" "$TOOL_DIR/lines_auto.py" --output "$ROOT/outputs/lines_annotated.png" "$@"
