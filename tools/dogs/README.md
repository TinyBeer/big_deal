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

- 大狗窝（4 个）：框出完整狗窝，标注其中狗的品种；用 `templates/house/locked.png`（视频图标 + 「解锁」）模板匹配判断是否未解锁。
- 小狗窝（7 个）：框出并标注品种或「未解锁 / 空」。
- 廊道出口狗：从中间往外扫描候选槽位，取每行左右两侧最靠中间的狗/蛋，用 `exit_detect.py` 的「颜色布局规则 + 模板匹配 + 颜色直方图」三级判定标 `★`，不再对整块棋盘做容易漏检的全局匹配。
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

- `templates/board/`：从对局画面截取的棋盘狗样本及姿态变体，用于模板匹配和颜色特征兜底；首选识别来自 `exit_detect.py` 的颜色规则。
- `templates/house/locked.png`：**必需**，锁定狗窝的「解锁」文字 + 广告图标模板；同目录的品种狗头样本只是可选兜底。
- `templates/shop/`：从「皮肤商店」截取的 9 种狗样本，可选兜底，整组约 0.5 MB。
- `templates/popup/`：**必需**，`claim_ad.png`（廊道解锁领取）和 `no_thanks.png`（关闭道具弹窗）。

模板总量约 1.1 MB。颜色规则已覆盖大部分情况，模板主要用于规则失效时兜底；删除 `shop/` 和 `house/` 的品种图虽可瘦身，但会降低极端姿态的识别率。

新增品种时，把 110×110 左右的狗样本按 `<模板名>.png` 放进对应目录，并在 `dog_annotate.py` 的 `BREED_CN` / `BREED_SHORT` 里补名称即可。同一品种不同姿态可放多个模板，命名为 `<模板名>_v2.png`、`<模板名>_v3.png`，识别时会自动归并到同一品种。若匹配不准，可用 `--threshold` 调整置信度（默认 0.88）。

## 自动点击

```bash
tools/dogs/quick.sh --auto --dry-run
tools/dogs/quick.sh                 # 默认 --auto
tools/dogs/quick.sh --auto --max-clicks 80
```

`dog_auto.py` 参考 `tools/spool/spool_assist.py`：抓图 → 识别 → 决策 → `adb input tap` → 等画面稳定。

- 优先点击能进入匹配大狗窝的出口狗，优先差一只就消除的窝；没有匹配目标时，才把狗送进小狗窝，优先与已有小狗同品种
- 小狗窝只剩 1 个空位且出口狗都无法进入大狗窝时自动结束，避免输掉
- 大狗窝三个圆点按橙色/深色识别已填数量；集满三只会自动刷新新狗窝
- 开局默认看广告解锁**大狗窝和廊道**；小狗窝暂不解锁，可用 `--no-unlock` 关闭
- 大狗窝点锁定窝直达广告；廊道点锁定处会先弹「领取」广告按钮，自动点它后再进广告
- 长时间不操作弹出的道具窗口会自动点「不了，谢谢」（模板匹配 + 固定坐标兜底）
- **检测到「复活」弹窗立即结束任务**（`templates/popup/revive_banner.png` 标题横幅匹配，和 `ring` 一致；复活弹窗上也有「不了，谢谢」，优先级最高，绝不会被误关）
- 广告页通过「点击立即返回」控件返回游戏
- 每轮决策打印状态日志：`狗窝=... 目标=... 小狗窝 空N/可用M 出口=... 可入窝=K`，便于核对识别是否正确
- 游戏内点击用 `input tap`，弹窗点击用 `input touchscreen tap`（两者对 canvas / 浮层的有效性不同）
- 任务结束（或异常中断）会通过 AutoJS6 发手机状态栏通知，和 `spool` 一样；`--no-notify` 关闭，`--notify-message` 自定义内容
