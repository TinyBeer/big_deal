#!/usr/bin/env bash
# 本关零食/饮料工具统一入口：默认自动点击（10 步）；--once 只标注。
#
# 用法：
#   tools/snacks/quick.sh                       # 默认执行固定顺序自动点击（1 轮）
#   tools/snacks/quick.sh --rounds 3            # 完整流程重复执行 3 轮
#   tools/snacks/quick.sh --dry-run             # 只打印点击顺序，不点击
#   tools/snacks/quick.sh --no-notify           # 不发通知
#   tools/snacks/quick.sh --device <serial>     # 指定 adb 设备
#   tools/snacks/quick.sh --once                # 实时抓图并标注（不点击）
#   tools/snacks/quick.sh --once --image <png>  # 处理本地截图并标注
#   tools/snacks/quick.sh --once --show-roi     # 标注图上画出商品搜索框
#   SNACKS_PYTHON=/path/to/python tools/snacks/quick.sh
set -euo pipefail

# shellcheck source=../common/shell_runtime.sh
source "$(cd "$(dirname "$0")" && pwd)/../common/shell_runtime.sh"
tool_init_env SNACKS_PYTHON "$0"
tool_ensure_outputs

mode="auto"
args=()
for arg in "$@"; do
  if [[ "$arg" == "--once" ]]; then
    mode="once"
  else
    args+=("$arg")
  fi
done
tool_auto_device --device "${args[@]}"; set -- "${TOOL_ARGS[@]}"

if [[ "$mode" == "once" ]]; then
  exec "$PY" "$TOOL_DIR/snacks_vision.py" "$@"
fi
exec "$PY" "$TOOL_DIR/snacks_auto.py" "$@"
