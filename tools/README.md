# 游戏辅助工具

本目录集中管理截图类游戏辅助工具，与 AutoJS 京东任务主体（`main.js` / `modules/`）分离。

| 目录 | 用途 | 入口 |
|------|------|------|
| `find-diff/` | 找不同（找茬）差异检测与标注 | `tools/find-diff/quick.sh` |
| `spool/` | 三消「线卷」识别、标注与自动点击 | `tools/spool/quick.sh` |
| `dogs/` | 狗狗三消识别、标注与自动点击 | `tools/dogs/quick.sh`（默认 `--auto`，`--once` 只标注） |
| `parking/` | 停车场接客：看广告解锁接驳位 + 自动接同色乘客；倾斜关卡只解锁不自动打，剩 1 空位停手 | `tools/parking/quick.sh`（见 `PLAN.md`） |
| `ring/` | 环形岛接客：按接驳区车色出车（全占用随机）；空位 ≤1 且无新色提前结束；复活弹窗立即停手 | `tools/ring/quick.sh` |
| `slots/` | 色块入槽：一批点第一排中颜色不在槽位且不重复的色块（全占用随机）；看广告解锁；复活/胜利界面立即停手 | `tools/slots/quick.sh` |

## 约定

- 所有产物统一写到项目根目录 `outputs/`，该目录已在 `.gitignore` 中忽略，不会污染仓库。
- 找不同标注图固定为 `outputs/mark.png`（覆盖旧文件），方便反复查看同一路径。
- `tools/` 内的脚本是本类工具的唯一来源，不依赖项目外的任何副本。

## 环境

各工具共用同一个 Python 环境和一份依赖清单，安装一次即可。先激活你要用的环境（如 miniconda 的 `conda activate <环境名>`）：

```bash
python -m pip install -r tools/requirements.txt
```

- 默认使用当前激活环境中的 Python（优先 `python`，找不到时回退 `python3`），可用 `FIND_DIFF_PYTHON` / `SPOOL_PYTHON` 覆盖
- 色块入槽的颜色池由马赛克拼图完整画板实机标定（14 色，含玫红/橙红、粉/玫红、浅紫/浅蓝灰/中灰/深灰等相近色细分）：`tools/slots/palette.json`；换关卡可用 `tools/slots/palette_calibrate.py` 重新标定（默认覆盖完整 20×26 网格；详见 `tools/slots/PLAN.md` 第十节）
- 停车场接客的模板（`arrow_right.png` / `p_slot.png` / `unlock.png`）位于 `tools/parking/templates/`；环形岛接客的模板（`unlock.png` / `p_slot.png` / `gift_x.png` / `use_button.png` / `revive_banner.png` / `fail_banner.png`）位于 `tools/ring/templates/`；色块入槽的模板（`unlock.png` / `revive_banner.png` / `victory_banner.png`）位于 `tools/slots/templates/`
- 手机抓图/点击依赖 adb 无线连接（停车场工具用 `--device <serial>` 指定设备；未指定时按 adb 默认设备连接）
- OpenCV 采用 headless 版；`spool --live` 在无 GUI 环境会自动改为每轮保存标注图
- `/tmp` 是小容量 tmpfs，涉及大临时文件的脚本统一使用 `/home/beer/tmp`
