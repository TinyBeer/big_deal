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

- **AutoJS6 任务助手**：以 `main.js` 为入口，提供京东商城、京东金融、互动游戏等日常任务的图形化控制台。
- **游戏辅助工具（`tools/`）**：通过 adb 截屏 + 图像识别辅助游戏操作，目前包含「找不同」「线卷三消」「狗狗三消」「搬砖大战」「停车场接客」「环形岛接客」「色块入槽」与「沙画收集」。

## 目录结构

```
big_deal/
├── main.js, modules/     # AutoJS6 京东任务
├── scripts/              # AutoJS 测试脚本
├── tools/                # 游戏辅助工具
│   ├── find-diff/        # 找不同：检测并标注差异点
│   ├── spool/            # 线卷三消：识别并自动点击
│   ├── dogs/             # 狗狗三消：识别并自动点击
│   ├── ants/             # 搬砖大战：像素画前沿识别与自动投放
│   ├── parking/          # 停车场接客：识别、解锁接驳位并自动接客
│   ├── ring/             # 环形岛接客：识别接驳区车色并自动接客
│   ├── slots/            # 色块入槽：第一排选色块、看广告解锁、自动点击
│   ├── sand/             # 沙画收集：看广告解锁槽位、批量选不重复色桶打通单关
│   ├── common/           # 共用模块：notify.py 统一各工具的手机状态栏通知
│   └── requirements.txt  # 各工具共用的 Python 依赖
└── outputs/              # 工具运行产物（已 gitignore）
```

## 快速开始

### AutoJS6 任务

1. 手机安装 [AutoJS6](https://github.com/SuperMonster003/AutoJs6) 并开启无障碍服务。
2. 登录京东 / 京东金融 App。
3. 将仓库导入 AutoJS6，运行 `main.js`，在主界面点击对应任务按钮。

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

**线卷三消**：

```bash
tools/spool/quick.sh                # 默认自动点击，输出 outputs/spool_annotated.png
tools/spool/quick.sh --once         # 只识别一次
```

**狗狗三消**：

```bash
tools/dogs/quick.sh                 # 默认自动点击（--once 只标注）
```

**停车场接客**（先看广告解锁全部接驳位，再自动接客；遇倾斜/8 方向关卡只解锁不自动打，剩 1 空位也停手交还）：

```bash
tools/parking/quick.sh --dry-run                              # 试运行，只演示一步决策
tools/parking/quick.sh --no-unlock --no-notify --max-clicks N # 续跑：不解锁、不通知、限 N 步
tools/parking/quick.sh --allow-tilted                         # 显式开启：倾斜关卡也自动接客
tools/parking/quick.sh                                        # 默认：解锁全部 + 打通单关 + 通知
```

**环形岛接客**（与停车场接客类似，但乘客在环形岛上旋转；只看接驳区车色出车，全占用时随机出车；空位 ≤1 且无新颜色车时提前结束）：

```bash
tools/ring/quick.sh --once                                    # 只识别一次，输出 outputs/ring_annotated.png
tools/ring/quick.sh --dry-run                                 # 试运行，演示解锁与选车但不真点
tools/ring/quick.sh --no-unlock --no-notify --max-clicks N     # 续跑：不解锁、不通知、限 N 步
tools/ring/quick.sh                                           # 默认：解锁全部 + 自动接客 + 通知
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

弹窗处理：助力礼包自动点 × 关闭；**复活/通关弹窗最高优先级立即结束、不做任何操作**；解锁确认框自动点「使用」看广告；结算弹窗（挑战失败/成功）立即停止。完整参数见 `tools/ring/quick.sh --help` / `tools/slots/quick.sh --help` / `tools/sand/quick.sh --help`。

完整参数与算法说明见各工具目录：

- `tools/find-diff/README.md` — 找不同
- `tools/spool/README.md` — 线卷三消
- `tools/dogs/README.md` — 狗狗三消
- `tools/parking/PLAN.md` — 停车场接客（方案、规则与实现说明）
- `tools/ring/` — 环形岛接客（`ring_vision.py` 识别、`ring_auto.py` 决策，参数见 `quick.sh --help`）
- `tools/slots/PLAN.md` — 色块入槽（方案、实机结论与识别参数）
- `tools/sand/PLAN.md` — 沙画收集（方案、关卡差异、批量选桶规则与终止弹窗模板）
- `tools/common/notify.py` — 共用的手机状态栏通知模块（各工具统一调用，支持 `--no-notify` 关闭）
- `tools/README.md` — 工具总览与共用环境

## TODO

- [ ] 按 App 不同将代码拆分开，把各 App 内通用的功能封装起来复用。

## 免责声明

本项目仅供个人学习与技术研究使用。请遵守相关平台的用户协议与规则，合理使用；因使用本项目产生的任何后果由使用者自行承担。
