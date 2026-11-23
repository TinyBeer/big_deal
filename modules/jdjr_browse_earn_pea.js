/*
 * 京东金融 - 浏览领赚豆
 *
 * 流程：提到前台 -> 找"浏览赚豆"入口 -> 引导弹窗"去完成" -> 任务页浮窗驱动
 * 浮窗文案驱动：正在浏览 -> 奖励已到账 继续浏览下一个 -> 返回
 *
 * 注意：文案与超时集中在 CFG，返回文案待真机确认后替换。
 * 一天仅执行一次，成功完成后记录当天日期。
 */
(function () {
  const utils = require("./utils");

  /* -------- 文案与参数（返回文案待确认） -------- */
  const CFG = {
    appName: "京东金融",

    entryText: "浏览赚豆", // 首页入口，clickable=false，点祖先
    popupText: "浏览页面得", // 引导弹窗标题（包含匹配），可为空跳过
    goButtonText: "去完成", // 引导弹窗按钮

    // 浮窗状态文案（真机已确认）
    browseText: "正在浏览", // 浏览中，包含匹配
    nextText: "继续浏览下一个", // 当前任务已完成，包含匹配（浮窗全句："奖励已到账 继续浏览下一个"）
    returnText: "返回", // TODO: 待真机确认；若页面有多个返回，改包含匹配+区域

    findTimeout: 500, // 单次查找超时 ms
    pollMs: 1000, // 任务循环轮询间隔 ms
    nextCooldownMs: 3000, // 点"下一个"后的冷却，避免重复点
    taskTimeoutMs: 45000, // 单个任务最长等待 ms
    totalTimeoutMs: 30 * 60 * 1000, // 整轮最长 ms
    maxTasks: 30, // 任务数上限，防死循环

    dailyKey: "jdjr_browse_earn_pea_last_date",
  };

  /* -------- 通知与每日限制 -------- */

  function notify(msg) {
    console.log(msg);
    try {
      notice("浏览领赚豆", msg);
    } catch (e) {
      try {
        toast(msg);
      } catch (e2) {}
    }
  }

  function today() {
    let d = new Date();
    return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
  }

  function doneToday() {
    return utils.loadConfig(CFG.dailyKey) === today();
  }

  function markDone() {
    utils.storeConfig(CFG.dailyKey, today());
  }

  /* -------- 控件查找与点击 -------- */

  /** 找到控件且中心点落在屏幕内才返回，避免点到屏外壳节点 */
  function findVisible(tx, opts) {
    opts = opts || {};
    let obj = utils.findText(tx, {
      timeout: opts.timeout === undefined ? CFG.findTimeout : opts.timeout,
      partial: !!opts.partial,
      regex: !!opts.regex,
    });
    if (!obj) return null;

    let b = obj.bounds();
    if (!b || b.width() <= 0 || b.height() <= 0) return null;
    let x = (b.left + b.right) / 2;
    let y = (b.top + b.bottom) / 2;
    let s = utils.getScreenSize();
    if (x < 0 || y < 0 || x > s.width || y > s.height) return null;
    return obj;
  }

  /** 优先点可点击祖先的中心；没有就点自身中心（TextView 也可以坐标点击） */
  function tapTarget(obj) {
    if (!obj) return false;
    let o = obj;
    for (let d = 0; o && d < 8; d++) {
      if (o.clickable()) {
        let b = o.bounds();
        if (b && b.width() > 0 && b.height() > 0) {
          click((b.left + b.right) / 2, (b.top + b.bottom) / 2);
          return true;
        }
      }
      o = o.parent();
    }
    let b = obj.bounds();
    if (!b || b.width() <= 0 || b.height() <= 0) return false;
    click((b.left + b.right) / 2, (b.top + b.bottom) / 2);
    return true;
  }

  /* -------- 流程 -------- */

  function bringToFront() {
    console.log("提到前台: " + CFG.appName);
    app.launchApp(CFG.appName);
    utils.longWait();
    return !!findVisible(CFG.entryText, { partial: true });
  }

  function enterTaskPage() {
    let entry = findVisible(CFG.entryText, { partial: true });
    if (!entry) {
      notify("未找到浏览赚豆入口，退出");
      return false;
    }
    tapTarget(entry);
    sleep(2500);

    // 引导弹窗：有"去完成"就点；没有则说明直接进了任务页
    let go = findVisible(CFG.goButtonText);
    if (go) {
      tapTarget(go);
      sleep(4000);
    } else {
      sleep(2000);
    }

    // 浮窗可能晚几秒才出现，给几次机会再判定失败
    for (let i = 0; i < 5 && !isTaskPage(); i++) {
      sleep(CFG.pollMs);
    }
    if (!isTaskPage()) {
      notify("未进入浏览任务页，退出");
      return false;
    }
    return true;
  }

  /** 三种浮窗文案任一命中即认为在任务页 */
  function isTaskPage() {
    return !!findFloating();
  }

  function findFloating() {
    // 顺序：返回 > 下一个 > 浏览中。
    // "继续浏览下一个"文字块可能常驻，故必须先判"返回"，避免提前结束。
    let f = findVisible(CFG.returnText, { timeout: 200 });
    if (f) return { kind: "return", obj: f };

    f = findVisible(CFG.nextText, { partial: true, timeout: 200 });
    if (f) return { kind: "next", obj: f };

    f = findVisible(CFG.browseText, { partial: true, timeout: 200 });
    if (f) return { kind: "browse", obj: f };

    return null;
  }

  /** 浮窗状态机：浏览中继续等，下一个点掉，返回则结束 */
  function watchTasks() {
    const started = Date.now();
    let perTaskStarted = Date.now();
    let lastNextClick = 0;
    let doneCount = 0;

    while (Date.now() - started < CFG.totalTimeoutMs && doneCount < CFG.maxTasks) {
      let f = findFloating();

      if (f && f.kind === "return") {
        console.log("浮窗出现[返回]，结束任务");
        tapTarget(f.obj);
        return true;
      }

      if (f && f.kind === "next") {
        if (Date.now() - lastNextClick >= CFG.nextCooldownMs) {
          console.log("浮窗出现[下一个]，点击进入下一个任务");
          tapTarget(f.obj);
          lastNextClick = Date.now();
          perTaskStarted = Date.now();
          doneCount++;
        }
        sleep(CFG.pollMs);
        continue;
      }

      if (f && f.kind === "browse") {
        perTaskStarted = Date.now();
        sleep(CFG.pollMs);
        continue;
      }

      // 浮窗文案短暂消失（加载中）时容忍一会儿，单任务超时则放弃
      if (Date.now() - perTaskStarted > CFG.taskTimeoutMs) {
        console.log("单任务等待超时，结束");
        return false;
      }
      sleep(CFG.pollMs);
    }
    return false;
  }

  function run() {
    if (doneToday()) {
      notify("今日浏览领赚豆已完成，跳过");
      return false;
    }

    let ok = false;
    try {
      if (!bringToFront()) {
        notify("未找到入口，退出");
      } else if (enterTaskPage()) {
        ok = watchTasks();
      }
    } catch (e) {
      console.log("浏览领赚豆异常: " + e);
      notify("浏览领赚豆异常: " + e);
    }

    if (ok) markDone();
    notify(ok ? "浏览领赚豆任务完成" : "浏览领赚豆任务未完成");
    return ok;
  }

  module.exports = { run };
})();
