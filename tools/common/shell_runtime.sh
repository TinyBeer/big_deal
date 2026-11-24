#!/usr/bin/env bash
# 各工具 quick.sh 共用的环境与参数辅助函数。
#
# 用法：
#   source "$ROOT/tools/common/shell_runtime.sh"
#   tool_init_env ANTS_PYTHON "$0"
#   tool_ensure_outputs
#   tool_auto_device --device "$@"; set -- "${TOOL_ARGS[@]}"
#   tool_strip_flag --once "$@"; ARGS=("${STRIPPED_ARGS[@]}")
#   tool_print_help 2 19 "$0"

tool_init_env() {
  local override="$1" script_path="$2" extra_path="${3:-}"
  TOOL_DIR="$(cd "$(dirname "$script_path")" && pwd)"
  ROOT="$(cd "$TOOL_DIR/../.." && pwd)"
  # shellcheck source=python_env.sh
  source "$ROOT/tools/common/python_env.sh"
  PY="$(resolve_python "$override")" || return 1
  if [[ -n "$extra_path" ]]; then
    export PYTHONPATH="$TOOL_DIR:$extra_path${PYTHONPATH:+:$PYTHONPATH}"
  else
    export PYTHONPATH="$TOOL_DIR${PYTHONPATH:+:$PYTHONPATH}"
  fi
}

tool_ensure_outputs() {
  mkdir -p "$ROOT/outputs"
}

# 未显式指定设备时探测第一台 adb 设备，结果放到全局数组 TOOL_ARGS。
tool_auto_device() {
  local flag="$1"
  shift
  TOOL_ARGS=("$@")
  local arg found=0 dev
  for arg in "$@"; do
    if [[ "$arg" == "$flag" ]]; then
      found=1
      break
    fi
  done
  if [[ "$found" -eq 0 ]]; then
    dev="$(adb devices 2>/dev/null | awk '/device$/{print $1; exit}')"
    if [[ -n "$dev" ]]; then
      TOOL_ARGS+=("$flag" "$dev")
    fi
  fi
}

# 去掉指定标记（如 --once），结果放到全局数组 STRIPPED_ARGS。
tool_strip_flag() {
  local drop="$1"
  shift
  STRIPPED_ARGS=()
  local arg
  for arg in "$@"; do
    [[ "$arg" == "$drop" ]] || STRIPPED_ARGS+=("$arg")
  done
}

tool_print_help() {
  local start="$1" end="$2" script_path="$3"
  sed -n "${start},${end}p" "$script_path"
}
