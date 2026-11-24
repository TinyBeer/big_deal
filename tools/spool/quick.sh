#!/usr/bin/env bash
# 线卷三消快速执行：使用当前激活环境的 Python 与固定输出路径，其余参数原样透传给 spool_assist.py
#
# 用法:
#   tools/spool/quick.sh                        # 默认 --auto，自动点击直到无可操作线卷
#   tools/spool/quick.sh --once                 # 只识别一次
#   tools/spool/quick.sh --live                 # 实时循环（headless 下自动改为每轮写文件）
#   tools/spool/quick.sh --image shot.png --once  # 调试本地截图
#   tools/spool/quick.sh --targets yellow pink  # 指定目标颜色（仍默认 --auto）
#   tools/spool/quick.sh --device <serial>      # 指定 adb 设备
#   tools/spool/quick.sh --batch-size 4 --batch-gap 0.3  # 一次识别批量点 4 个目标色
#
# 输出: outputs/spool_annotated.png（传 --output 可覆盖）
# 解释器: 见 tools/common/python_env.sh（SPOOL_PYTHON > 当前激活环境 > PATH）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT/tools/common/shell_runtime.sh"
tool_init_env SPOOL_PYTHON "$0" || exit 1
OUT="$ROOT/outputs/spool_annotated.png"

for a in "$@"; do
  case "$a" in
    -h|--help) tool_print_help 2 14 "$0"; exit 0 ;;
  esac
done

has_mode=0
has_out=0
for a in "$@"; do
  case "$a" in
    --auto|--once|--live) has_mode=1 ;;
    --output) has_out=1 ;;
  esac
done

args=()
if [ "$has_out" -eq 0 ]; then args+=(--output "$OUT"); fi
if [ "$has_mode" -eq 0 ]; then args+=(--auto); fi

tool_ensure_outputs
echo "▶ 线卷三消"
echo "  输出: $OUT"
if [ "$has_mode" -eq 0 ]; then echo "  模式: --auto（默认，可用 --once / --live 覆盖）"; fi

exec "$PY" "$TOOL_DIR/spool_assist.py" "${args[@]}" "$@"
