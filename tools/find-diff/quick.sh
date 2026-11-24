#!/usr/bin/env bash
# 一条命令完成：抓手机截图 → 找不同检测 → 合并碎框重排编号 → 输出标记图
# 用法:
#   quick.sh                          # 输出 ./outputs/mark.png（仅标记图，默认）
#   quick.sh -o /path/out             # 指定输出目录
#   quick.sh -n mark                  # 固定文件名前缀（默认 mark，覆盖旧文件）
#   quick.sh -k 2                     # 输出数量：1=标记图 2=+预览 3=+对比表 4=+原始截图
#   quick.sh -f 已有图片.png          # 跳过抓图，直接处理本地图片
#   quick.sh -s 192.168.2.11:42559    # 指定设备（默认取第一台在线设备）
#   quick.sh -c 25 -t 14              # 候选上限 / 色差阈值（同 find_diff.sh）
# 解释器: 见 tools/common/python_env.sh（FIND_DIFF_PYTHON > 当前激活环境 > PATH）
set -euo pipefail

OUTDIR="./outputs"
NAME="mark"
NUM=1
SERIAL=""
COUNT=25
THR=14
SRCIMG=""

while [ $# -gt 0 ]; do
  case "$1" in
    -o|--outdir) OUTDIR="$2"; shift 2 ;;
    -n|--name)   NAME="$2"; shift 2 ;;
    -k|--num)    NUM="$2"; shift 2 ;;
    -f|--file)   SRCIMG="$2"; shift 2 ;;
    -s|--serial) SERIAL="$2"; shift 2 ;;
    -c|--count)  COUNT="$2"; shift 2 ;;
    -t|--thr)    THR="$2"; shift 2 ;;
    -h|--help)   sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "未知参数: $1" >&2; exit 2 ;;
  esac
done

case "$NUM" in 1|2|3|4) ;; *) echo "-k 只支持 1~4" >&2; exit 2 ;; esac

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$TOOL_DIR/../.." && pwd)"
source "$ROOT/tools/common/python_env.sh"
PY="$(resolve_python FIND_DIFF_PYTHON)" || exit 1
export FIND_DIFF_PYTHON="$PY"
export TMPDIR="${TMPDIR:-/home/beer/tmp}"
mkdir -p "$OUTDIR" "$TMPDIR"
WORK="$(mktemp -d "$TMPDIR/zc.XXXXXX")"
trap 'find "$WORK" -mindepth 1 -delete 2>/dev/null; rmdir "$WORK" 2>/dev/null' EXIT

# 1. 取图：本地文件，或从手机抓
SHOT="$WORK/shot.png"
if [ -n "$SRCIMG" ]; then
  [ -f "$SRCIMG" ] || { echo "✗ 文件不存在: $SRCIMG" >&2; exit 1; }
  cp "$SRCIMG" "$SHOT"
  echo "▶ 读图: $SRCIMG"
else
  if [ -z "$SERIAL" ]; then
    SERIAL="$(adb devices | awk 'NR>1 && $2=="device"{print $1; exit}')"
  fi
  [ -n "$SERIAL" ] || { echo "没有找到在线设备，先确认手机已连上 adb（adb devices）" >&2; exit 1; }
  echo "▶ 抓图: $SERIAL"
  adb -s "$SERIAL" exec-out screencap -p > "$SHOT"
  SIZE=$(stat -c %s "$SHOT")
  if [ "$SIZE" -lt 60000 ]; then
    echo "✗ 截图只有 ${SIZE}B，多半是锁屏/黑屏，请解锁手机后重试" >&2
    exit 1
  fi
fi

# 2. 检测
echo "▶ 检测可疑点..."
"$TOOL_DIR/find_diff.sh" "$SHOT" -o "$WORK" -c "$COUNT" -t "$THR" >/dev/null
JS="$WORK/shot_diffs.json"
[ -f "$JS" ] || { echo "✗ 检测失败：未生成 $JS" >&2; exit 1; }

# 3. 版面校验：竖排上下布局 + 残差够小，否则说明当前画面不是找不同游戏
IFO=$("$PY" - "$JS" <<'EOF'
import sys, json
d = json.load(open(sys.argv[1]))
i = d.get("info", {})
print(i.get("mode", "?"), round(float(i.get("resid", 999)), 1))
EOF
)
MODE=$(echo "$IFO" | awk '{print $1}')
RESID=$(echo "$IFO" | awk '{print $2}')
if [ "$MODE" != "auto-v" ] || awk "BEGIN{exit !($RESID > 22)}"; then
  echo "✗ 没识别到找不同的上下两幅画面（mode=$MODE resid=$RESID）" >&2
  echo "  请确认手机停在游戏关卡界面、两幅图完整可见，再重试" >&2
  exit 3
fi

# 4. 合并碎框 + 重排编号
echo "▶ 合并碎框并重排编号..."
"$PY" "$TOOL_DIR/merge_and_mark.py" "$SHOT" "$JS" "$WORK/marked.png" >/dev/null

# 5. 顶部"？"数（仅供参考）
QP=$("$PY" - "$SHOT" <<'EOF'
import sys, numpy as np
from PIL import Image
a=np.array(Image.open(sys.argv[1]).convert("RGB")).astype(np.float32)
strip=a[330:430,:]
prof=(strip.mean(axis=2)>175).mean(axis=0)
on=prof>0.12; n=0; s=None
for i,v in enumerate(on):
    if v and s is None: s=i
    elif not v and s is not None:
        if i-s>14: n+=1
        s=None
print(n)
EOF
) || QP="?"

# 6. 按 -k 复制固定命名的产物
cp "$WORK/marked.png" "$OUTDIR/$NAME.png"
OUTS=("$OUTDIR/$NAME.png")
if [ "$NUM" -ge 2 ]; then cp "$WORK/marked_preview.png" "$OUTDIR/${NAME}_preview.png"; OUTS+=("$OUTDIR/${NAME}_preview.png"); fi
if [ "$NUM" -ge 3 ]; then cp "$WORK/marked_contact.png" "$OUTDIR/${NAME}_contact.png"; OUTS+=("$OUTDIR/${NAME}_contact.png"); fi
if [ "$NUM" -ge 4 ]; then cp "$WORK/shot.png"            "$OUTDIR/${NAME}_shot.png";    OUTS+=("$OUTDIR/${NAME}_shot.png"); fi

echo
echo "✓ 完成（顶部\"？\"数: $QP）"
for f in "${OUTS[@]}"; do echo "  $f"; done
exit 0
