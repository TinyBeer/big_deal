#!/usr/bin/env bash
# 各工具共用的 Python 解释器选择逻辑。
#
# 优先级：显式覆盖变量 > 当前激活的 venv/conda 环境 > PATH 中的 python/python3。
# 找不到，或激活环境里没有可执行的 python 时，打印提示并返回非零。
#
# 用法：
#   source "$ROOT/tools/common/python_env.sh"
#   PY="$(resolve_python ANTS_PYTHON)" || exit 1

resolve_python() {
  local override="${1:-PYTHON}" py="" src=""

  if [[ -n "${!override:-}" ]]; then
    py="${!override}"
    src="override"
  elif [[ -n "${VIRTUAL_ENV:-}" ]]; then
    py="$VIRTUAL_ENV/bin/python"
    src="venv"
  elif [[ -n "${CONDA_PREFIX:-}" ]]; then
    py="$CONDA_PREFIX/bin/python"
    src="conda"
  else
    py="$(command -v python || command -v python3 || true)"
    src="path"
  fi

  if [[ -n "$py" && "$py" != */* ]]; then
    py="$(command -v "$py" || true)"
  fi

  if [[ -z "$py" || ! -x "$py" ]]; then
    case "$src" in
      override)
        echo "✗ $override 指定的 Python 不可用: ${py:-<空>}" >&2
        ;;
      venv|conda)
        local env_name="${VIRTUAL_ENV:-${CONDA_PREFIX:-}}"
        echo "✗ 当前激活的环境没有可执行的 Python: $env_name/bin/python" >&2
        echo "  请修复或切换环境，或设置 $override 指定解释器" >&2
        ;;
      *)
        echo "✗ 未找到 Python：请先激活环境（conda activate xxx / source venv/bin/activate），或设置 $override" >&2
        ;;
    esac
    return 1
  fi

  printf '%s\n' "$py"
}
