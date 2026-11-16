# big_deal

基于 AutoJS6 的京东系 App 自动化任务脚本项目，主入口为 `main.js`。

## 环境

- Android 手机安装 AutoJS6 并开启无障碍服务
- 京东 App 已登录

## 使用

在 AutoJS6 中运行 `main.js`，点击主界面的「互动游戏」按钮即可启动京东互动游戏任务。

任务会自动：启动京东 → 我的 → 互动游戏 → 攒经验 → 依次完成屏幕内的「逛一逛」任务 → 返回首页。结束后 toast 提示结果。

点击任务后等待 15 秒，期间每 500ms 检查一次「点击立即返回」，出现即返回；屏幕外的任务不处理。

## 配置

在 `modules/jd_interactive_games.js` 顶部修改：

- `TASK_SKIP_KEYWORDS`：跳过的任务关键字数组，默认 `[]`
- `BROWSE_WAIT_SECONDS`：等待返回按钮秒数，默认 `15`
- `BROWSE_CHECK_INTERVAL_MS`：检查间隔毫秒，默认 `500`
