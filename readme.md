# big_deal

基于 AutoJS6 的京东系 App 自动化脚本，主入口为 `main.js`。

## 线卷三消辅助

通过 adb 截取手机画面，自动识别大线卷目标颜色，点击同色且未被遮挡的小线卷；没有可消除目标时会先解锁锁定槽、再尝试释放挡板。遇到广告、失败和京东验证会按规则处理或暂停等待。

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/spool_assist.py --auto
```

默认最长自动运行 10 分钟。更多参数（设备、超时、次数、调试等）查看：

```bash
.venv/bin/python scripts/spool_assist.py --help
```

## 原有 AutoJS 任务

手机安装 AutoJS6 并开启无障碍、京东已登录后，运行 `main.js`，在主界面选择对应任务即可。
