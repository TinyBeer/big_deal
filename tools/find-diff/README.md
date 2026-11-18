# 找不同（找茬）辅助工具

输入一张上下（或左右）并排两幅图的找不同截图，自动定位差异点并输出红框编号标注图。
核心算法：CIELAB ΔE 色差 + 抗亚像素错位 + 连通域形态筛选，单关 2–3 秒。

本目录的脚本是找不同工具的唯一来源。

## 一键命令

在项目根目录执行：

```bash
tools/find-diff/quick.sh                       # 抓手机截图 → 检测 → 标注 → outputs/mark.png
tools/find-diff/quick.sh -o outputs            # 指定输出目录（默认 ./outputs）
tools/find-diff/quick.sh -f 已有图片.png        # 跳过抓图，直接处理本地图片
```

默认只输出标记图 `mark.png`，覆盖同名旧文件，便于反复查看同一路径。

| 参数 | 作用 |
|------|------|
| `-n/--name` | 文件名前缀，默认 `mark` → `mark.png` |
| `-k/--num` | 输出数量：`1`=仅标记图（默认）`2`=+预览 `3`=+对比表 `4`=+原始截图 |
| `-f/--file` | 跳过抓图，直接处理本地图片 |
| `-o/--outdir` | 输出目录，默认 `./outputs` |
| `-s/--serial` | 指定 adb 设备，默认取第一台在线设备 |
| `-c/--count` | 候选数上限，默认 25 |
| `-t/--thr` | ΔE 阈值，默认 14（漏检降到 10–11，误报多升到 16–18） |

脚本末尾打印 `顶部"？"数`（仅供参考）。若版面校验失败（`mode≠auto-v` 或 `resid>22`），说明当前画面不是找不同游戏，脚本以退出码 3 中止并提示，不会产出垃圾标注。

## 单独检测已有图片

不需要手机、不需要抓图时，直接对已有图片检测：

```bash
tools/find-diff/find_diff.sh <图片路径> -o outputs
# 等价写法
tools/find-diff/find_diff.sh -f <图片路径> -o outputs
# 调参
tools/find-diff/find_diff.sh <图片路径> -c 25 -t 14
```

产出四个文件：`<BASE>_annotated.png`（原尺寸红框标注）、`<BASE>_annotated_preview.png`（半尺寸预览）、`<BASE>_contact.png`（上下并排对比清单）、`<BASE>_diffs.json`（坐标/面积/ΔE/score）。

碎框过多时（同一物体出多个框），可合并重排编号：

```bash
/home/beer/.workbuddy/binaries/python/envs/default/bin/python \
  tools/find-diff/merge_and_mark.py <原图> <BASE>_diffs.json <输出前缀>.png
```

规则：面积 < 120px² 且彼此间距 < 40px 的碎框合并为一个（典型：左右眼、上下睫毛线各出一框，实为一处"眼睛变了"）；再按"从上到下、从左到右"重排 1..N。

## 关键判读规则

- **坐标**：`_diffs.json` 的 bbox 是**面板相对坐标**，绝对 y = `bbox_y + info.top[0]`。人工裁剪时务必加这个偏移——这是最常犯的错。
- **数"？"个数**：裁出问号所在横条（1080×2400 竖屏取 y=340~430），按亮色圆点做列剖面，连续 `>0.12` 且宽度 `>14` 的段数即为答数。阈值取 0.20 会因问号笔画空心而断开，不要盲用更高阈值。
- **候选数 > 答数**：同一物体上有多个框（两只眼睛、两段横梁）→ 共用一个点击点，报点时合并说明。典型：16 框 / 15 个"？"，多出的是左右眼。
- **候选数 < 答数**：可疑漏检 → 用 `-t 10` 重跑，并检查该区域是否存在"低填充率 + 贴边"的差异。

## 算法原理与已知坑

详见 `references/pitfalls.md`（灰度比对丢颜色差异、块内均值稀释小目标、弱对比物体被填充率过滤、接缝伪影连坐误杀、过度合并/拆分）。

环境注意：`/tmp` 是 10M tmpfs，脚本已统一把 `TMPDIR` 指向 `/home/beer/tmp`。

## 依赖

- Python + `numpy` / `Pillow` / `scipy`（检测本身不需要 adb，只有 `quick.sh` 抓图环节需要）
- 与 spool 共用一份依赖清单：在项目根目录执行 `pip install -r tools/requirements.txt`
- 默认解释器 `/home/beer/.workbuddy/binaries/python/envs/default/bin/python`，可用环境变量 `FIND_DIFF_PYTHON` 覆盖
