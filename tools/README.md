# 游戏辅助工具

本目录集中管理截图类游戏辅助工具，与 AutoJS 京东任务主体（`main.js` / `modules/`）分离。

| 目录 | 用途 | 入口 |
|------|------|------|
| `find-diff/` | 找不同（找茬）差异检测与标注 | `tools/find-diff/quick.sh` |
| `spool/` | 三消「线卷」识别、标注与自动点击：有目标色时一次识别批量点最多 3 个候选（`--batch-size`/`--batch-gap`）；解锁挡板时只点 1 个；检测到复活页面立即停止 | `tools/spool/quick.sh` |
| `lines/` | 线条解放：自动检测网格并还原每条折线箭头，找出**当前所有可点击**线条，在外围标注编号与识别出的方向（不遮挡箭头），输出 JSON；默认每轮等画面稳定后全量识别当前所有可移除线条（首轮锁定网格 lattice，避免逐轮漂移；误点时游戏闪红的线条也计入遮挡，图判定后再用当前截图逐像素复核射线），依次点击后重新识别循环；复活页与爱心在识别时检查，减少即停手；`--batch-size`/`--gap`/`--batch-wait` 控制每批条数与节奏，`--max-clicks`/`--max-seconds` 为上限；`--click-log` 可把每次点击写入 `outputs/lines_clicks.jsonl`（默认关闭），`--steps` 可额外输出顺序规划 | `tools/lines/quick.sh`（默认自动点击，`--once` 只标注） |
| `dogs/` | 狗狗三消识别、标注与自动点击：一次识别选最多 3 只能进大狗窝且不重复品种的出口狗依次点击（`--batch-size`/`--batch-gap`）；无大狗窝目标时随机单只送小狗窝 | `tools/dogs/quick.sh`（默认 `--auto`，`--once` 只标注） |
| `parking/` | 停车场接客：看广告解锁接驳位 + 自动接同色乘客；倾斜关卡只解锁不自动打，剩 1 空位停手 | `tools/parking/quick.sh`（见 `PLAN.md`） |
| `ring/` | 环形岛接客：一次识别批量选「颜色不在接驳区且批内不重色」的车依次点击（`--batch-size`/`--batch-gap`）；全占用随机出车；空位 ≤1 且无新色提前结束；复活弹窗立即停手 | `tools/ring/quick.sh` |
| `slots/` | 色块入槽：一批点第一排中颜色不在槽位且不重复的色块（全占用随机）；看广告解锁；复活/胜利界面立即停手 | `tools/slots/quick.sh` |
| `ants/` | 搬砖大战：开局看广告解锁；只检查槽位和第一排候选块，一次选一批不在槽中的颜色投放（同色最多一槽）；福利弹窗点 X 关闭；复活弹窗立即停手；连续无法决策超过 `--idle-timeout`（默认 20 秒）停止；已点未入槽的颜色在 `--repeat-delay`（默认 8 秒）内不重复点；结束时发手机状态栏通知（`--no-notify` 关闭） | `tools/ants/quick.sh`（见 `PLAN.md`） |
| `sand/` | 沙画收集：看广告解锁槽位到加号消失；批量选第一排不重复色桶依次点击（`--batch-size`/`--batch-gap`）；复活/通关弹窗立即停手 | `tools/sand/quick.sh`（见 `PLAN.md`） |
| `snacks/` | 本关零食/饮料 + 右上角退出按钮识别标注：只在商品最小外接矩形内用模板匹配找商品，排除顾客气泡里的同款图；被手势遮挡的商品也能识别；标注只输出图片、不输出位置日志/JSON。另有固定顺序自动点击（冰红茶→矿泉水→冰红茶→啤酒→矿泉水→啤酒→瓜子→花生→八宝粥→退出按钮，每步重新识别商品位置，退出按钮点固定坐标、点后等 2s，点击后等 1s / 八宝粥后 2s，开局按固定顺序循环处理中断（入口页「真香摆摊日记」页签点中心等 6s → 积分商店点红叉 → 游戏主界面点开始游戏并等 4s → 助力礼包点 No thanks → 广告页直接返回），直到进入关卡后直接跑点击序列、中途不再检测界面；`--rounds N` 重复完整流程 N 轮，结束发通知） | `tools/snacks/quick.sh`（默认自动点击，`--once` 只标注，见 `PLAN.md`） |
| `common/` | 共用模块：`notify.py` 统一通知；`adb.py` 统一 tap/key_back/控件树查找/设备探测；`screen.py` 统一 adb 抓图；`palette_calibrate_core.py` 统一调色板标定的投影/FFT/相位/众数色/KMeans 骨架；`shell_runtime.sh` 统一入口脚本的环境初始化、outputs 创建、设备探测与参数剔除；`python_env.sh` 统一解释器选择 | 被各 `*Auto.py` / `quick.sh` / `palette_calibrate.py` 引入，无独立入口 |

## 约定

- 所有产物统一写到项目根目录 `outputs/`，该目录已在 `.gitignore` 中忽略，不会污染仓库。
- 找不同标注图固定为 `outputs/mark.png`（覆盖旧文件），方便反复查看同一路径。
- `tools/` 内的脚本是本类工具的唯一来源，不依赖项目外的任何副本。

## 环境

各工具共用同一个 Python 环境和一份依赖清单，安装一次即可。先激活你要用的环境（如 miniconda 的 `conda activate <环境名>`）：

```bash
python -m pip install -r tools/requirements.txt
```

- 解释器由 `tools/common/python_env.sh` 统一选择：显式覆盖变量 > 当前激活的 venv（`VIRTUAL_ENV`）/conda（`CONDA_PREFIX`）环境 > PATH 中的 `python`/`python3`。激活环境里没有可执行的 Python 时会直接提示，不会静默改用其它环境
- 覆盖变量：`FIND_DIFF_PYTHON` / `SPOOL_PYTHON` / `DOG_PYTHON` / `PARKING_PYTHON` / `RING_PYTHON` / `SLOTS_PYTHON` / `ANTS_PYTHON` / `SAND_PYTHON` / `LINES_PYTHON` / `SNACKS_PYTHON`

### 限制

- 工具只使用当前激活环境（或显式 `XXX_PYTHON`）中的 Python。若已激活的 venv/conda 环境里没有可执行的 `python`，脚本会直接提示并退出，不会静默回退到系统 Python 或其它环境；请修复/切换环境，或显式设置对应覆盖变量
- 未激活任何环境时回退到 PATH 中的 `python`/`python3`；PATH 中也没有 Python 时同样提示并退出。运行前请确认所选环境已安装 `tools/requirements.txt` 依赖

- 色块入槽的颜色池由马赛克拼图完整画板实机标定（16 类，含玫红/橙红、粉/玫红、浅紫/浅蓝灰/中灰/深灰、浅蓝/蓝/宝蓝等相近色细分）：`tools/slots/palette.json`；换关卡可用 `tools/slots/palette_calibrate.py` 重新标定（默认覆盖完整 38×51 网格；新增关卡的独特色可手动补入色池，详见 `tools/slots/PLAN.md` 第十节及十·八补）
- 停车场接客的模板（`arrow_right.png` / `p_slot.png` / `unlock.png`）位于 `tools/parking/templates/`；环形岛接客的模板（`unlock.png` / `p_slot.png` / `gift_x.png` / `use_button.png` / `revive_banner.png` / `fail_banner.png`）位于 `tools/ring/templates/`；色块入槽的模板（`unlock.png` / `revive_banner.png` / `victory_banner.png`）位于 `tools/slots/templates/`；搬砖大战的模板（`popup_close.png` / `revive_close.png` / `unlock.png`）位于 `tools/ants/templates/`
- 搬砖大战的颜色池由 `tools/ants/palette_calibrate.py` 从上方像素画标定，结果存 `tools/ants/palette.json`；用法与 slots 的调色板标定一致（`--image` 指定截图或实时抓图，`--k` 控制聚类数）。
- 手机抓图/点击依赖 adb 无线连接（停车场工具用 `--device <serial>` 指定设备；未指定时按 adb 默认设备连接）
- 状态栏通知由 `tools/common/notify.py` 统一实现：各工具通过 `add_notify_args()` 注册 `--notify/--no-notify/--notify-message/--notify-script`，通过 `send_notify()` 发送（`--notify-message auto` 表示用运行时统计文案）；异常中断可用 `notify_phone()`。通知需要 AutoJS6 的 POST_NOTIFICATIONS 权限
- OpenCV 采用 headless 版；`spool --live` 在无 GUI 环境会自动改为每轮保存标注图
- `/tmp` 是小容量 tmpfs，涉及大临时文件的脚本统一使用 `/home/beer/tmp`
