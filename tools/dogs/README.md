# 狗狗三消画面标注

参考 `tools/spool/` 的截图识别思路，提供**识别标注**和**自动点击**（`--auto`）两种模式。

只识别画面中部的廊道出口（每行左右各一），远离出口的狗先不识别。廊道行数由紫蓝架子水平投影自动检测，新解锁的廊道会自动纳入。

## 运行

先激活Python环境（与 `tools/spool/` 一致），再运行：

```bash
tools/dogs/quick.sh --once
tools/dogs/quick.sh --once --image shot.png
```

输出 `outputs/dog_annotated.png`，并在终端打印 JSON 摘要（大狗窝、小狗窝、廊道出口品种）。

## 标注内容

- 大狗窝（4 个）：框出完整狗窝，用中央头像圆形区域做固定模板 + Hu 校验识别品种；用 `templates/house/locked.png`（视频图标 + 「解锁」）模板匹配判断是否未解锁。
- 小狗窝（7 个）：只标状态「未解锁 / 空 / 有狗」，不识别狗的品种。
- 廊道出口狗：从中间往外扫描候选槽位，取每行左右两侧最靠中间的狗/蛋，用固定位置模板（颜色相似度）匹配 + 轮廓 Hu 矩二次校验标 `★`；未命中标「未知」，不再使用旧的颜色规则兜底。
- 紫蛋 / 冰蛋：灰框标出但**忽略品种**（紫蛋到出口变狗，冰蛋在消除后变狗）。

## 品种对照

| 模板名 | 标注 |
| --- | --- |
| `shiba_orange` | 橙白柴犬 |
| `husky_black` | 黑白哈士奇 |
| `samoyed_white` | 白色小狗 |
| `collie_blackwhite` | 黑白边牧 |
| `pug_beige` | 巴哥 |
| `beagle_orangewhite` | 橙白比格 |
| `boston_blackwhite` | 黑白波士顿梗 |
| `poodle_brown` | 棕色泰迪 |
| `terrier_gray` | 灰白梗 |

## 模板

- `templates/fixed/`：固定机位模板，见下节；旧的 `board/` 和 `shop/` 目录已废弃删除。
- `templates/house/locked.png`：**必需**，锁定狗窝的「解锁」文字 + 广告图标模板。
- `templates/corridor/`：`locked.png`、`locked_right.png` 是实机截取的廊道锁头模板，替代原来的颜色阈值判定。
- `templates/popup/`：**必需**，`claim_ad.png`（廊道解锁领取）和 `no_thanks.png`（关闭道具弹窗）。

新增模板时，在 `templates/fixed/specs.json` 的 `entries` 里追加来源截图、品种和裁切中心，再执行 `make_templates.py --force` 生成；同一品种可放多个姿态模板，无需特殊命名。旧的 `--threshold` 参数已移除。

## 固定模板 + Hu 矩校验

`templates/fixed/` 是从已标注样本截图裁出的固定机位模板（带 alpha mask）：

- `exit/`：廊道出口狗全身，120×120。按颜色先验去掉草地/紫架子背景后保存。
- `house/`：狗窝中央头像圆形区域，100×100，圆形 mask。
- `specs.json`：每个模板的来源截图、品种和裁切中心；`manifest.json`：生成结果清单。

识别流程（`fixed_match.py`）：先在固定裁片上算 mask 内平均颜色相似度，按品种取最高分；只有分数够高、与次优品种差距够大，且轮廓 Hu 矩距离够小时才采纳（`score >= 0.75/0.83`，Hu `<= 0.35/0.60`，品种间差距 `>= 0.04`）。大狗窝头像与廊道出口都做 Hu 校验；头像裁片按 Hough 检测到的圆心精确包裹圆形区域，避免像素偏移。未命中直接标「未知」，不再回退旧算法。

重新生成模板（修改 `specs.json` 后执行，用 `big_deal` 环境）：

```bash
/home/beer/miniconda3/envs/big_deal/bin/python3.12 tools/dogs/make_templates.py --force
```

回归测试（默认跑两批已标记样本）：

```bash
/home/beer/miniconda3/envs/big_deal/bin/python3.12 tools/dogs/regress.py
```

当前样本回归：狗窝 36/36、廊道出口 90/90、小狗窝 63/63，总计 189/189。回归脚本会把旧真值里的小窝品种名归一为「有狗」。

## 自动点击

```bash
tools/dogs/quick.sh --auto --dry-run
tools/dogs/quick.sh                 # 默认 --auto
tools/dogs/quick.sh --auto --max-clicks 80
tools/dogs/quick.sh --auto --batch-gap 0.2  # 按已解锁大狗窝品种选全部不重复候选狗
```

`dog_auto.py` 参考 `tools/spool/spool_assist.py`：抓图 → 识别 → **选目标** → 依次 `adb input tap` → 统一等画面稳定。

- **有能进大狗窝的出口狗时**：按已解锁大狗窝品种，选出所有不重复的目标狗；不判断大狗窝已填数量，也不限制选择数量（`--batch-size` 已废弃，仅为兼容保留）。按原坐标依次点击，间隔 `--batch-gap`（默认 0.2s）；下一只点击前复查复活弹窗，命中立即停手。廊道出口互相独立，同一张图上选出的多只狗可连点
- **没有任何大狗窝目标时**：随机选 1 只出口狗送小狗窝，单只点击，**不走批量选狗逻辑**；小狗窝只剩 1 个空位时停止，避免填满输掉
- `--dry-run` 会打印本轮候选狗及去向（不实际点击）
- 大狗窝三个圆点仅用于人工观察；自动点击不读取已填数量，只按已解锁的大狗窝品种选狗
- 开局默认看广告解锁**大狗窝和廊道**；一旦开始点击廊道出口的狗，就不再检查/解锁资源。小狗窝暂不解锁，可用 `--no-unlock` 关闭
- 大狗窝点锁定窝直达广告；廊道锁定用 `templates/corridor/` 的锁头模板匹配判定，解锁仍是固定坐标点击；若第 5 行该侧出口已识别到狗/蛋，就认为廊道已解锁，不再点击。开始点击出口狗后完全停止解锁检查
- 长时间不操作弹出的道具窗口会自动点「不了，谢谢」（模板匹配 + 固定坐标兜底）
- **检测到「复活」弹窗立即结束任务**（`templates/popup/revive_banner.png` 标题横幅匹配，和 `ring` 一致；复活弹窗上也有「不了，谢谢」，优先级最高，绝不会被误关）
- 广告页通过「点击立即返回」控件返回游戏
- 每轮决策打印状态日志：`狗窝=... 目标=... 小狗窝 空N/可用M 出口=... 可入窝=K`，便于核对识别是否正确
- 游戏内点击用 `input tap`，弹窗点击用 `input touchscreen tap`（两者对 canvas / 浮层的有效性不同）
- 任务结束（或异常中断）会通过 AutoJS6 发手机状态栏通知，和 `spool` 一样；`--no-notify` 关闭，`--notify-message` 自定义内容

## TODO

- [x] 提高狗的品种识别精度：已改为固定模板 + Hu 矩校验优先，颜色规则/特征兜底；样本回归中狗窝和廊道出口均达到 100%。
- [ ] 继续扩充新姿态/新品种的 `templates/fixed/` 模板，并收集更多已验证样本回测。
