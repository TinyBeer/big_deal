#!/usr/bin/env bash
# 环形岛接客辅助统一入口
#
# 用法:
#   tools/ring/quick.sh --once                 # 只识别一次，输出标注图
#   tools/ring/quick.sh --dry-run              # 演示第一步（关弹窗/解锁/选车，不真点）
#   tools/ring/quick.sh                        # 默认 --auto，自动打通单关
#   tools/ring/quick.sh --no-unlock            # 跳过开局解锁接驳位
#   tools/ring/quick.sh --batch-size 3         # 一次识别选多个不重色车依次点击（默认 3）
#   tools/ring/quick.sh --device <serial>      # 指定 adb 设备
#
# 输出: outputs/ring_annotated.png（--once）/ outputs/ring_dryrun.png（--dry-run）
#
# 解释器: 见 tools/common/python_env.sh（RING_PYTHON > 当前激活环境 > PATH）
# 依赖: 所选环境需安装 tools/requirements.txt（pip install -r tools/requirements.txt）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT/tools/common/shell_runtime.sh"
tool_init_env RING_PYTHON "$0" || exit 1

for a in "$@"; do
  case "$a" in
    -h|--help) tool_print_help 2 15 "$0"; exit 0 ;;
  esac
done

tool_ensure_outputs
tool_auto_device --device "$@"; set -- "${TOOL_ARGS[@]}"

if [[ " $* " == *" --once "* ]]; then
  echo "▶ 环形岛接客 · 识别一次"
  exec "$PY" "$TOOL_DIR/ring_vision.py" --output "$ROOT/outputs/ring_annotated.png" "$@"
fi

echo "▶ 环形岛接客 · 自动模式（默认打通单关）"
exec "$PY" "$TOOL_DIR/ring_auto.py" "$@"
