# 游戏辅助工具

本目录集中管理截图类游戏辅助工具，与 AutoJS 京东任务主体（`main.js` / `modules/`）分离。

| 目录 | 用途 | 入口 |
|------|------|------|
| `find-diff/` | 找不同（找茬）差异检测与标注 | `tools/find-diff/quick.sh` |
| `spool/` | 三消「线卷」识别、标注与自动点击 | `tools/spool/quick.sh` |

## 约定

- 所有产物统一写到项目根目录 `outputs/`，该目录已在 `.gitignore` 中忽略，不会污染仓库。
- 找不同标注图固定为 `outputs/mark.png`（覆盖旧文件），方便反复查看同一路径。
- `tools/` 内的脚本是本类工具的唯一来源，不依赖项目外的任何副本。

## 环境

两个工具共用同一个 Python 环境和一份依赖清单，安装一次即可：

```bash
pip install -r tools/requirements.txt
```

- 默认解释器：`/home/beer/.workbuddy/binaries/python/envs/default/bin/python`
- 手机抓图/点击依赖 adb 无线连接（设备号可用 `-s` 指定，缺省取第一台在线设备）
- OpenCV 采用 headless 版；`spool --live` 在无 GUI 环境会自动改为每轮保存标注图
- `/tmp` 是小容量 tmpfs，涉及大临时文件的脚本统一使用 `/home/beer/tmp`
