#!/usr/bin/env bash
# 狗狗三消统一入口：默认 --auto 自动点击；--once 只标注一次。
# 与 tools/spool/quick.sh 一致，使用当前激活环境中的 Python。
set -euo pipefail
TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$TOOL_DIR/../.." && pwd)"
PY="${DOG_PYTHON:-$(command -v python || command -v python3 || true)}"
if [ -z "$PY" ]; then
  echo "✗ 未找到 Python，请先激活环境（如 conda activate xxx）或设置 DOG_PYTHON" >&2
  exit 1
fi

for a in "$@"; do
  case "$a" in
    -h|--help)
      sed -n '2,12p' "$0"
      echo "  tools/dogs/quick.sh                  # 默认 --auto，自动点击"
      echo "  tools/dogs/quick.sh --once           # 只识别标注一次"
      echo "  tools/dogs/quick.sh --auto --dry-run # 只演示决策，不点击"
      exit 0 ;;
  esac
done

mode="auto"
args=()
for a in "$@"; do
  case "$a" in
    --auto|--once) mode="${a#--}" ;;
    *) args+=("$a") ;;
  esac
done

mkdir -p "$ROOT/outputs"
if [ "$mode" = "once" ]; then
  has_out=0
  for a in "${args[@]}"; do [ "$a" = "--output" ] && has_out=1; done
  if [ "$has_out" -eq 0 ]; then args=(--output "$ROOT/outputs/dog_annotated.png" "${args[@]}"); fi
  echo "▶ 狗狗三消（标注一次）"
  exec "$PY" "$TOOL_DIR/dog_annotate.py" "${args[@]}"
fi

echo "▶ 狗狗三消（自动点击）"
exec "$PY" "$TOOL_DIR/dog_auto.py" "${args[@]}"
