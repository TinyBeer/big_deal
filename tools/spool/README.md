# 线卷三消辅助

通过 adb 截屏并用 OpenCV 识别画面：自动从顶部彩色大线卷读取目标颜色，优先点击同色且未被遮挡的小线卷；没有目标时先解锁锁定槽，再尝试释放挡板。

## 运行

快速脚本（推荐）：

```bash
tools/spool/quick.sh              # 默认 --auto，自动点击直到无可操作线卷
tools/spool/quick.sh --once       # 只识别一次
tools/spool/quick.sh --live       # 实时循环标注
```

`quick.sh` 默认使用当前激活环境中的 Python（优先 `python`，找不到时回退 `python3`），可用 `SPOOL_PYTHON` 覆盖；输出路径固定，其余参数原样透传；输出默认 `outputs/spool_annotated.png`。

不使用快速脚本时，也可直接调用：

```bash
PY=python   # 当前激活环境中的解释器，也可用 SPOOL_PYTHON 指定
$PY tools/spool/spool_assist.py --auto --output outputs/spool_annotated.png
```

依赖由 `tools/requirements.txt` 统一管理，安装一次两个工具共用。OpenCV 为 headless 版，`--live` 在无 GUI 环境会自动改为每轮保存标注图。

## 常用示例

```bash
# 指定设备与目标颜色
$PY tools/spool/spool_assist.py --device <serial> --targets yellow pink

# 一次识别批量点 4 个目标色线卷（解锁挡板时仍只点 1 个）
$PY tools/spool/spool_assist.py --auto --batch-size 4 --batch-gap 0.3

# 调试本地截图
$PY tools/spool/spool_assist.py --image shot.png --once

# 只演示第一步，不实际点击
$PY tools/spool/spool_assist.py --auto --dry-run
```

## 参数

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--image` | 直接处理本地图片（调试用） | - |
| `--device` | adb 设备序列号 | - |
| `--once` | 只识别一次 | - |
| `--live` | 实时循环标注 | - |
| `--auto` | 自动点击直到没有可操作线卷 | - |
| `--interval` | 实时模式间隔秒 | `0.8` |
| `--output` | 标注结果保存路径 | `spool_annotated.png` |
| `--targets` | 手动指定目标颜色，覆盖自动识别 | 自动识别 |
| `--max-clicks` | 自动模式最大点击次数 | `200` |
| `--max-seconds` | 自动模式最长运行秒数 | `600` |
| `--dry-run` | 自动模式只演示第一步，不点击 | - |
| `--no-revive` | 失败时不看广告复活，直接停止 | - |
| `--security-timeout` | 等待用户手动完成安全验证的超时秒数 | `300` |
| `--board-min-area` | 顶层挡板检测的最小封闭区面积（过小易把空隙当挡板） | `8000` |
| `--notify` / `--no-notify` | 自动模式结束后是否让手机 AutoJS 发出状态栏通知提醒 | 默认提醒 |
| `--notify-message` | 通知内容（标题固定为「线卷三消」） | `线卷三消已完成` |
| `--notify-script` | 写到手机上供 AutoJS 运行的临时脚本路径 | `/sdcard/Scripts/spool_notify.js` |

<details>
<summary>更多参数（点击、复活与解锁微调）</summary>

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--wait` / `--max-wait` | 点击后最短 / 最长等待秒数 | `0.35` / `1.8` |
| `--gap` | 每轮之间的额外间隔秒数 | `0.15` |
| `--batch-size` | 一次识别最多批量点击几个目标色线卷（`0`=不限）；解锁挡板时强制为 `1` | `3` |
| `--batch-gap` | 批内相邻两次点击的间隔秒数 | `0.35` |
| `--recent-seconds` | 多久内不重复点击同一位置 | `4.0` |
| `--modal-v` | 画面平均亮度低于此值视为失败 / 弹窗 | `150` |
| `--revive-threshold` | 「复活」标题横幅模板匹配阈值，命中立即停止 | `0.80` |
| `--max-revive` | 自动看广告复活的最大次数（仅限非复活页面） | `3` |
| `--max-slot-unlock` | 看广告解锁锁定线卷槽的最大次数 | `4` |
| `--revive-x` / `--revive-y` | 「获得」按钮横向 / 纵向比例 | `0.50` / `0.738` |
| `--revive-wait` | 看广告等待秒数 | `15` |
| `--revive-timeout` | 等待回到对局的总超时秒数 | `30` |
| `--revive-settle` | 复活后额外等待秒数 | `3.0` |

</details>

## 行为说明

- 暂存区、挡板分组、复活广告等状态按规则处理。
- 有目标色可点时一次识别选最多 `--batch-size` 个候选，按原坐标依次点击（间隔 `--batch-gap`），整批结束后才重新截图识别；批内会避开本批已选和近期点过的位置。没有目标色、需要点其他线卷释放挡板时，**只允许单次点击**，等画面变化后重新决策。
- 顶层挡板靠外围白色描边是否闭合判断：闭合的区域是当前顶层（被线卷压出的细小缺口会由轻微膨胀补上）；嵌套时只保留最内层。没有目标色可点时，优先点顶层挡板里的线卷来释放它，因为点被遮挡的下层挡板通常无效。
- **检测到「复活」页面立即停止，不做任何点击**：每轮开头先按 `tools/spool/templates/revive_banner.png` 匹配紫底白字「复活」横幅；批量点击中途也会复查，避免后续点击误落到「获得」按钮上。
- 消除之前先看广告解锁锁定的线卷槽；其他暗色失败 / 弹窗页面仍会点「获得」看广告复活（`--no-revive` 可关）。
- 遇到京东安全验证会暂停，等待用户手动完成后继续。
- 自动模式结束（正常跑完或提前停止）后会通过 adb 把一条 `notice()` 脚本推送到手机，并调用 AutoJS6 的 `RunIntentActivity` 直接执行，在状态栏生成常驻通知（标题「线卷三消」），无需手机上常驻监听脚本；异常中断时也会提醒。需要 AutoJS6 的通知权限（POST_NOTIFICATIONS）。用 `--no-notify` 可关闭，`--notify-message` 改内容。
