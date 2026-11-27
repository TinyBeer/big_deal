<div align="center">

# big_deal

一套基于 **AutoJS6** 的京东系 App 自动化任务集合，附带截图类游戏辅助工具。

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Android-3DDC84?logo=android&logoColor=white)
![License](https://img.shields.io/badge/license-ISC-blue)

[项目简介](#项目简介) · [目录结构](#目录结构) · [快速开始](#快速开始) · [TODO](#todo) · [免责声明](#免责声明)

</div>

---

## 项目简介

仓库包含两部分能力：

- **AutoJS6 任务助手**：以 `main.js` 为入口，提供京东商城、京东金融（含金融互动游戏）等日常任务的图形化控制台。
- **游戏辅助工具（`tools/`）**：通过 adb 截屏 + 图像识别辅助游戏操作，目前包含「找不同」「线卷三消」「狗狗三消」「搬砖大战」「停车场接客」「环形岛接客」「色块入槽」「沙画收集」「线条解放」「接驳位解锁」与「零食/饮料识别」。

目前控制台提供：京东商城（京东、国补、121京豆、看病买药）与京东金融（手动签到、天天赚京豆、省钱中心、浏览领赚豆、金融互动游戏）任务。

## 目录结构

```
big_deal/
├── main.js, modules/     # AutoJS6 任务助手
├── scripts/              # AutoJS 测试脚本
├── tools/                # 游戏辅助工具
│   ├── find-diff/        # 找不同：检测并标注差异点
│   ├── lines/            # 线条解放：找出所有当前可点击线条并标注
│   ├── spool/            # 线卷三消：识别并自动点击
│   ├── dogs/             # 狗狗三消：识别并自动点击
│   ├── ants/             # 搬砖大战：像素画前沿识别与自动投放
│   ├── parking/          # 停车场接客：识别、解锁接驳位并自动接客
│   ├── ring/             # 环形岛接客：识别接驳区车色并自动接客
│   ├── slots/            # 色块入槽：第一排选色块、看广告解锁、自动点击
│   ├── sand/             # 沙画收集：看广告解锁槽位、批量选不重复色桶打通单关
│   ├── snacks/           # 零食/饮料识别标注 + 固定顺序自动点击（支持多轮）
│   ├── dock/             # 接驳位解锁：识别「解锁」按钮 → 看广告 → 回对局解锁
│   ├── common/           # 共用模块：notify.py 统一各工具的手机状态栏通知
│   └── requirements.txt  # 各工具共用的 Python 依赖
└── outputs/              # 工具运行产物（已 gitignore）
```

## 快速开始

### AutoJS6 任务

1. 手机安装 [AutoJS6](https://github.com/SuperMonster003/AutoJs6) 并开启无障碍服务。
2. 登录京东 / 京东金融 App。
3. 将仓库导入 AutoJS6，运行 `main.js`，在主界面点击对应任务按钮。

### 浏览领赚豆（京东金融）

`main.js` 京东金融分区的「浏览领赚豆」按钮对应 `modules/jdjr_browse_earn_pea.js`：

1. 将京东金融切到前台，查找首页「浏览赚豆」入口，找不到则通知并退出；
2. 点击引导弹窗的「去完成」进入浏览任务页；
3. 根据浮窗文案驱动流程：「正在浏览」时等待，「奖励已到账 继续浏览下一个」时进入下一任务，出现「返回」时结束任务；
4. 任务结束后不再回退页面，直接通过状态栏通知提示结果；
5. 每天仅执行一次，执行记录保存在本地存储中。

浮窗「返回」文案与超时等参数集中在模块顶部 `CFG`，真机确认后可直接调整。

### 游戏辅助工具

各工具共用同一个 Python 环境与依赖清单，安装一次即可（需 Python 3.9+、adb 已连接设备）。先激活你要用的环境（如 miniconda 的 `conda activate <环境名>`）：

```bash
python -m pip install -r tools/requirements.txt
```

**找不同**（手机停在关卡界面）：

```bash
tools/find-diff/quick.sh                   # 抓图 → 检测 → outputs/mark.png
tools/find-diff/quick.sh -f 某张图.png      # 跳过抓图，处理本地图片
```

**线条解放**（手机停在关卡界面：自动检测网格并还原每条折线箭头，找出当前可点击的线条；编号与识别出的方向标注在箭头外侧，不遮挡箭头；编号只是标识，不代表点击顺序；**默认自动点击**）。识别会等画面稳定后进行，首轮锁定网格避免漂移，误点时游戏闪红的线条也计入遮挡；每轮识别时检查复活页与爱心，减少立即停手：

```bash
tools/lines/quick.sh                       # 默认：每轮全量识别 → 批量点击 → 循环到无可点击线或命中停止条件
tools/lines/quick.sh --once                # 只识别标注，不点击 → outputs/lines_annotated.png + lines_free.json
tools/lines/quick.sh --image shot.png --dry-run  # 离线试运行：只打印要点击的坐标
tools/lines/quick.sh --max-clicks 3 --no-notify  # 限制点击步数 / 关闭状态栏通知
tools/lines/quick.sh --batch-size 4 --gap 0.45   # 每批最多 4 条、批内间隔 0.45s（默认）
tools/lines/quick.sh --click-log            # 可选：每次点击写入 outputs/lines_clicks.jsonl（默认关闭）
```

停止条件：已无可点击线条、复活页、爱心减少、`--max-clicks`、`--max-seconds`。调试用参数还有 `--batch-wait`、`--dry-run`、`--once`、`--steps`（额外顺序规划，仅 `--once` 下有意义）。

**线卷三消**：

```bash
tools/spool/quick.sh                # 默认自动点击，输出 outputs/spool_annotated.png
tools/spool/quick.sh --once         # 只识别一次
```

**狗狗三消**：

```bash
tools/dogs/quick.sh                 # 默认自动点击（--once 只标注）
tools/dogs/quick.sh --auto --batch-size 3 --batch-gap 0.35  # 每批最多 3 只可入大狗窝的不重复候选狗，依次点击
```

**停车场接客**（先看广告解锁全部接驳位，再自动接客；遇倾斜/8 方向关卡只解锁不自动打，剩 1 空位也停手交还）：

```bash
tools/parking/quick.sh --dry-run                              # 试运行，只演示一步决策
tools/parking/quick.sh --no-unlock --no-notify --max-clicks N # 续跑：不解锁、不通知、限 N 步
tools/parking/quick.sh --allow-tilted                         # 显式开启：倾斜关卡也自动接客
tools/parking/quick.sh                                        # 默认：解锁全部 + 打通单关 + 通知
```

**环形岛接客**（与停车场接客类似，但乘客在环形岛上旋转；一次识别选一批「颜色不在接驳区且批内不重色」的车依次点击，全占用时随机出车；空位 ≤1 且无新颜色车时提前结束）：

```bash
tools/ring/quick.sh --once                                    # 只识别一次，输出 outputs/ring_annotated.png
tools/ring/quick.sh --dry-run                                 # 试运行，演示解锁与批量选车但不真点
tools/ring/quick.sh --batch-size 3 --batch-gap 0.35            # 每批最多 3 辆不重色车，批内间隔 0.35s（默认）
tools/ring/quick.sh --no-unlock --no-notify --max-clicks N     # 续跑：不解锁、不通知、限 N 步
tools/ring/quick.sh                                           # 默认：解锁全部 + 自动接客 + 通知
```

**接驳位解锁**（螺丝/叉车类消除：顶部槽位带「解锁」按钮，点它看广告后该位解锁；福利弹窗点 X 关掉）：

```bash
tools/dock/quick.sh --once            # 只识别一次，输出 outputs/dock_annotated.png
tools/dock/quick.sh --dry-run         # 试运行，只演示第一步
tools/dock/quick.sh --max-unlock 3    # 默认自动解锁，直到没有「解锁」按钮
tools/dock/quick.sh --ad-wait 18      # 广告落地页倒计时更长时调大
```

**色块入槽**（点底部第一排中颜色不在槽位的色块，全占用则随机点一个；看广告解锁左右槽位）：

```bash
tools/slots/quick.sh --once                                   # 只识别一次，输出 outputs/slots_annotated.png
tools/slots/quick.sh --dry-run                                # 试运行，只演示第一步决策
tools/slots/quick.sh --no-unlock --no-notify --max-clicks 5    # 续跑：不解锁、不通知、限 5 步
tools/slots/quick.sh                                          # 默认：解锁 + 自动点击 + 通知
```

**沙画收集**（开局看广告解锁槽位到加号消失；每批选第一排中**颜色不重复**的桶依次点击；复活/通关弹窗立即停手）：

```bash
tools/sand/quick.sh --once                                    # 只识别一次，输出 outputs/sand_annotated.png
tools/sand/quick.sh --dry-run                                 # 试运行，演示批量选桶但不真点
tools/sand/quick.sh --no-unlock --no-notify --max-clicks 6     # 续跑：不解锁、不通知、限 6 次点击
tools/sand/quick.sh --batch-size 3 --batch-gap 0.15            # 每批最多 3 个不重复色、点击间隔 0.15s
tools/sand/quick.sh                                           # 默认：解锁 + 批量自动点击 + 通知，打通单关即停
```

**零食/饮料识别**（本关专用：在商品最小外接矩形内用模板匹配标注棋盘上所有零食/饮料，并标出右上角退出按钮；顾客气泡里的同款图不算，被手势遮挡的商品也能识别）：

```bash
tools/snacks/quick.sh --once                                  # 只标注 → outputs/snacks_annotated.png
tools/snacks/quick.sh --once --image outputs/shot.png         # 处理本地截图
tools/snacks/quick.sh --dry-run                               # 打印点击顺序与轮数，不点击
tools/snacks/quick.sh --rounds 3                              # 完整流程重复 3 轮（默认 1 轮）
tools/snacks/quick.sh                                         # 默认：开局状态处理 + 10 步固定顺序点击 + 通知
```

启动时要求当前页面有游戏入口：入口页页签或「玩游戏领京豆」任务页卡片两个模板任一命中才继续，都没匹配到直接退出。之后每轮按固定顺序处理开局状态（入口 → 积分商店红叉 → 开始游戏 → 助力礼包 No thanks → 广告页返回），进入关卡后依次点击冰红茶、矿泉水、冰红茶、啤酒、矿泉水、啤酒、瓜子、花生、八宝粥、退出按钮；每步重新抓图定位，退出按钮点固定坐标，点后等 2s 再进入下一轮。

弹窗处理：助力礼包自动点 × 关闭；**复活/通关弹窗最高优先级立即结束、不做任何操作**；解锁确认框自动点「使用」看广告；结算弹窗（挑战失败/成功）立即停止。完整参数见 `tools/ring/quick.sh --help` / `tools/slots/quick.sh --help` / `tools/sand/quick.sh --help`。

完整参数与算法说明见各工具目录：

- `tools/find-diff/README.md` — 找不同
- `tools/lines/quick.sh --help` — 线条解放（网格识别、箭头判定、当前可点击集合与自动点击参数）
- `tools/spool/README.md` — 线卷三消
- `tools/dogs/README.md` — 狗狗三消
- `tools/parking/PLAN.md` — 停车场接客（方案、规则与实现说明）
- `tools/ring/` — 环形岛接客（`ring_vision.py` 识别、`ring_auto.py` 决策，参数见 `quick.sh --help`）
- `tools/slots/PLAN.md` — 色块入槽（方案、实机结论与识别参数）
- `tools/sand/PLAN.md` — 沙画收集（方案、关卡差异、批量选桶规则与终止弹窗模板）
- `tools/snacks/PLAN.md` — 零食/饮料识别标注、固定顺序自动点击与多轮参数（`--rounds`）
- `tools/common/notify.py` — 共用的手机状态栏通知模块（各工具统一调用，支持 `--no-notify` 关闭）
- `tools/README.md` — 工具总览与共用环境

## TODO

- [ ] 按 App 不同将代码拆分开，把各 App 内通用的功能封装起来复用。
- [ ] 修复 121 京豆功能：`modules/jd_121pea.js`。当前页面文案在 H5 中被拆成多个 TextView（`领`/`121`/`京豆`，任务行「浏览10s可领」与「去完成」分属不同节点），整串 `textContains` 匹配不到；任务列表首次打开时行高为零，需滑动触发重新渲染；Auto.js 把多行 bounds 报成相同坐标，难以按位置区分任务行。业务流程已回退到原始版本，仅保留分级日志改造。

## 免责声明

本项目仅供个人学习与技术研究使用。请遵守相关平台的用户协议与规则，合理使用；因使用本项目产生的任何后果由使用者自行承担。
