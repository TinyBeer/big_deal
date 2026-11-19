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
- **游戏辅助工具（`tools/`）**：通过 adb 截屏 + 图像识别辅助游戏操作，目前包含「找不同」与「线卷三消」。

## 目录结构

```
big_deal/
├── main.js, modules/     # AutoJS6 京东任务
├── scripts/              # AutoJS 测试脚本
├── tools/                # 游戏辅助工具
│   ├── find-diff/        # 找不同：检测并标注差异点
│   ├── spool/            # 线卷三消：识别并自动点击
│   └── requirements.txt  # 两个工具共用的 Python 依赖
└── outputs/              # 工具运行产物（已 gitignore）
```

## 快速开始

### AutoJS6 任务

1. 手机安装 [AutoJS6](https://github.com/SuperMonster003/AutoJs6) 并开启无障碍服务。
2. 登录京东 / 京东金融 App。
3. 将仓库导入 AutoJS6，运行 `main.js`，在主界面点击对应任务按钮。

### 游戏辅助工具

两个工具共用同一个 Python 环境与依赖清单，安装一次即可（需 Python 3.9+、adb 已连接设备）。先激活你要用的环境（如 miniconda 的 `conda activate <环境名>`）：

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

完整参数与算法说明见各工具目录：

- `tools/find-diff/README.md` — 找不同
- `tools/spool/README.md` — 线卷三消
- `tools/README.md` — 工具总览与共用环境

## TODO

- [ ] 按 App 不同将代码拆分开，把各 App 内通用的功能封装起来复用。

## 免责声明

本项目仅供个人学习与技术研究使用。请遵守相关平台的用户协议与规则，合理使用；因使用本项目产生的任何后果由使用者自行承担。
