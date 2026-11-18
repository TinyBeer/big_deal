<div align="center">

# big_deal

一套基于 **AutoJS6** 的京东系 App 自动化任务集合，并附带一个由 OpenCV 驱动的线卷三消辅助脚本。

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Android-3DDC84?logo=android&logoColor=white)
![License](https://img.shields.io/badge/license-ISC-blue)

[项目简介](#项目简介) · [功能一览](#功能一览) · [快速开始](#快速开始) · [参数说明](#参数说明) · [TODO](#todo)

</div>

---

## 项目简介

仓库包含两部分能力：

- **AutoJS6 任务助手**：以 `main.js` 为入口，提供京东商城、京东金融、互动游戏等日常任务的图形化控制台。
- **线卷三消辅助**：通过 adb 截屏并用 OpenCV 识别画面，自动寻找目标大线卷并点击同色小线卷，可处理挡板、广告、失败弹窗与安全验证。

## 功能一览

### AutoJS6 任务

运行 `main.js` 后，在主界面选择对应任务即可启动（任务在独立线程中执行）。

| 分类 | 可用任务 | 对应模块 |
| --- | --- | --- |
| 京东商城 | 京东、抽盲盒、国补、121京豆、刮卡任务、超级明星 | `modules/jd*.js` |
| 互动游戏 | 启动京东互动游戏 | `modules/jd_interactive_games.js` |
| 京东金融 | 手动签到、天天赚京豆、省钱中心 | `modules/jdjr_manual.js`、`modules/jdjr_earn_pea.js`、`modules/jdjr_save_center.js` |
| 金融互动游戏 | 热门游戏、每日必玩、好游推荐、猜你喜欢、发现更多、游戏尝鲜，支持分区勾选、测试模式与定时执行 | `modules/jdjr_interactive_games.js` |
| 其他 | 熊猫乐园 | `modules/china_mobile.js` |

### 线卷三消辅助

- 自动从顶部彩色大线卷读取目标颜色，也可用 `--targets` 手动指定。
- 优先点击同色且未被遮挡的小线卷；没有目标时先解锁锁定槽，再尝试释放挡板。
- 暂存区、挡板分组、复活广告等状态按规则处理。
- 遇到京东安全验证会暂停等待用户手动完成，超时由 `--security-timeout` 控制。

## 快速开始

### 运行 AutoJS6 任务

1. 手机安装 [AutoJS6](https://github.com/SuperMonster003/AutoJs6) 并开启无障碍服务。
2. 登录京东 / 京东金融 App。
3. 将仓库导入 AutoJS6，运行 `main.js`，在主界面点击对应任务按钮。

### 运行线卷三消辅助

依赖 Python 3.9+ 与 adb（需开启 USB 调试并连接设备）。

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
```

常用运行方式：

```bash
# 自动点击（默认最长运行 10 分钟）
.venv/bin/python scripts/spool_assist.py --auto

# 只识别一次并保存标注图
.venv/bin/python scripts/spool_assist.py --once --output result.png

# 实时循环标注
.venv/bin/python scripts/spool_assist.py --live

# 指定设备 / 目标颜色 / 调试本地截图
.venv/bin/python scripts/spool_assist.py --device <serial> --targets yellow pink
.venv/bin/python scripts/spool_assist.py --image shot.png --once
```

查看全部参数：

```bash
.venv/bin/python scripts/spool_assist.py --help
```

## 参数说明

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

<details>
<summary>更多参数（点击、复活与解锁微调）</summary>

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--wait` / `--max-wait` | 点击后最短 / 最长等待秒数 | `0.35` / `1.8` |
| `--gap` | 每轮之间的额外间隔秒数 | `0.15` |
| `--recent-seconds` | 多久内不重复点击同一位置 | `4.0` |
| `--modal-v` | 画面平均亮度低于此值视为失败 / 弹窗 | `150` |
| `--max-revive` | 自动看广告复活的最大次数 | `3` |
| `--max-slot-unlock` | 看广告解锁锁定线卷槽的最大次数 | `4` |
| `--revive-x` / `--revive-y` | 「获得」按钮横向 / 纵向比例 | `0.50` / `0.738` |
| `--revive-wait` | 看广告等待秒数 | `15` |
| `--revive-timeout` | 等待回到对局的总超时秒数 | `30` |
| `--revive-settle` | 复活后额外等待秒数 | `3.0` |

</details>

## TODO

- [ ] 按 App 不同将代码拆分开，把各 App 内通用的功能封装起来复用。

## 免责声明

本项目仅供个人学习与技术研究使用。请遵守相关平台的用户协议与规则，合理使用；因使用本项目产生的任何后果由使用者自行承担。
