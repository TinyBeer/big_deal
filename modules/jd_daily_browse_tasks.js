/*
 * 京东「每日福利」页 — 做任务赚更多京豆：自动完成所有「去浏览」任务
 *
 * 入口行为：和其他京东任务一样，先把京东 App 提到前台（保留用户上次停留的页面）。
 * 因此要求用户离开控制台前，京东 App 已停在「每日福利」的任务列表面板；
 * 本模块不负责从首页导航到该页面，提前台后若面板不可见会直接退出。
 * 与「国补」模块的差异：
 *   - 国补是「点击立即返回」按钮；这里点击「去浏览」后进入频道页/小游戏页，
 *     通常没有返回按钮，等满浏览时长后按返回键回任务列表即可自动结算。
 *   - 任务列表是 WebView，按钮和标题控件 clickable=false，必须按坐标点击。
 *   - 部分任务会弹「任务火爆，请稍后再试」，点击后页面不跳转，需要冷却后重试。
 *
 * 实测（2026-11-28）：
 *   - 点击「买车养车 一站服务」→ 京东汽车频道 + 能源工坊小游戏浮层；
 *     浏览 5 秒后连按 2 次返回 → 回任务列表，顶部 toast「恭喜您！获得1个京豆」，
 *     头部「已领4」变「已领5」，该任务变成（1/1）+ 已完成。
 *   - 「看视频赚现金（0/1）」按钮也是「去浏览」，必须按标题排除。
 *   - 任务列表会滚动，完成的任务会沉底/标记已完成，剩余任务会上移。
 */
(function () {
  const { waitForText, longWait } = require("./utils");

  const CFG = {
    listTitle: "做任务赚更多京豆",
    goText: "去浏览",
    excludeTitles: ["看视频赚现金"],
    titleRe: /（\d+\/\d+）/,
    browseRe: /浏览(\d+)秒/,
    claimedRe: /已领(\d+)/,

    defaultBrowseSec: 6,
    bufferMs: 1200,
    afterClickWaitMs: 1200,
    backWaitMs: 900,
    maxBack: 5,
    cooldownMs: 30000,
    maxTasks: 20,
    maxRounds: 100,
    maxScrollPages: 5,

    // 任务列表面板范围（1080×2400 机型实测；只做粗过滤，不写死行坐标）
    panelTop: 1200,
    panelBottom: 2358,
    buttonLeftMin: 800,
    titleLeftMin: 170,
    titleLeftMax: 820,
    rowTolerance: 70,
  };

  function log(msg) {
    console.log("[浏览任务] " + msg);
  }

  /* ---------- 控件采集 ---------- */

  function collectNodes() {
    const out = [];
    const all = textMatches(".+").find();
    for (let i = 0; i < all.length; i++) {
      const o = all[i];
      const t = (o.text() || "").trim();
      if (!t) continue;
      const b = o.bounds();
      if (!b) continue;
      const x1 = b.left;
      const y1 = b.top;
      const x2 = b.right;
      const y2 = b.bottom;
      if (x2 <= x1 || y2 <= y1) continue; // 屏幕外节点常返回零高度
      out.push({
        node: o,
        text: t,
        left: x1,
        top: y1,
        right: x2,
        bottom: y2,
        cx: (x1 + x2) / 2,
        cy: (y1 + y2) / 2,
      });
    }
    return out;
  }

  function isPanelVisible() {
    const ns = collectNodes();
    for (let i = 0; i < ns.length; i++) {
      if (ns[i].text.indexOf(CFG.listTitle) >= 0 && ns[i].top > 1000) return true;
    }
    return false;
  }

  function claimedCount() {
    const ns = collectNodes();
    for (let i = 0; i < ns.length; i++) {
      const m = CFG.claimedRe.exec(ns[i].text);
      if (m) return parseInt(m[1], 10);
    }
    return -1;
  }

  /* ---------- 候选任务识别 ---------- */

  function findCandidates() {
    const nodes = collectNodes();
    const res = [];

    for (let i = 0; i < nodes.length; i++) {
      const btn = nodes[i];
      if (btn.text !== CFG.goText) continue;
      if (btn.left < CFG.buttonLeftMin) continue;
      if (btn.top < CFG.panelTop || btn.bottom > CFG.panelBottom) continue;

      // 同一行左侧的标题 / 说明文字
      let title = null;
      let seconds = CFG.defaultBrowseSec;
      for (let j = 0; j < nodes.length; j++) {
        const n = nodes[j];
        if (n.left < CFG.titleLeftMin || n.left > CFG.titleLeftMax) continue;
        if (Math.abs(n.cy - btn.cy) > CFG.rowTolerance) continue;

        if (!title && CFG.titleRe.test(n.text)) title = n.text;
        const m = CFG.browseRe.exec(n.text);
        if (m) seconds = parseInt(m[1], 10);
      }
      if (!title) continue;

      const key = title.replace(CFG.titleRe, "").trim();
      let excluded = false;
      for (let k = 0; k < CFG.excludeTitles.length; k++) {
        if (key.indexOf(CFG.excludeTitles[k]) >= 0) {
          excluded = true;
          break;
        }
      }
      if (excluded) continue;

      res.push({ key: key, title: title, seconds: seconds, btn: btn });
    }
    return res;
  }

  /* ---------- 返回与结算 ---------- */

  function tapNode(n) {
    if (!n) return false;
    click(Math.round(n.cx), Math.round(n.cy));
    return true;
  }

  function tryQuickReturn() {
    const opts = { seconds: 3, intervalMs: 500, click: true, afterClick: "short" };
    if (text("点击立即返回").findOne(200) && waitForText("点击立即返回", opts)) return true;
    if (text("开心收下").findOne(200) && waitForText("开心收下", opts)) return true;
    if (text("领取奖励").findOne(200) && waitForText("领取奖励", opts)) return true;
    return false;
  }

  function backToPanel() {
    for (let i = 0; i < CFG.maxBack; i++) {
      back();
      sleep(CFG.backWaitMs);
      if (isPanelVisible()) return true;
    }
    return isPanelVisible();
  }

  function scrollDown() {
    swipe(540, 2050, 540, 1450, 500);
    sleep(700);
  }

  function scrollToTop() {
    for (let i = 0; i < 6; i++) {
      swipe(540, 1500, 540, 2100, 400);
      sleep(200);
    }
    sleep(500);
  }

  /* ---------- 单个任务 ---------- */

  function runOne(c) {
    log("执行: " + c.title + "（浏览 " + c.seconds + " 秒）");
    const before = claimedCount();

    tapNode(c.btn);
    sleep(CFG.afterClickWaitMs);

    // 点击后仍停在任务面板：多半是「任务火爆，请稍后再试」限流
    if (isPanelVisible()) {
      log("未跳转，疑似任务火爆/限流，稍后重试");
      return false;
    }

    sleep(Math.max(c.seconds, 1) * 1000 + CFG.bufferMs);

    // 少数落地页有显式的「点击立即返回」；没有就靠返回键
    tryQuickReturn();
    if (!isPanelVisible() && !backToPanel()) {
      log("未能返回任务列表");
      return false;
    }

    sleep(600);

    // 结算判定：头部「已领N」自增最可靠（toast 在控件树里不一定可读）
    const after = claimedCount();
    if (before >= 0 && after > before) {
      log("完成，已领 " + before + " → " + after);
      return true;
    }

    // 兜底：任务行变成（1/1）或按钮变成「已完成」
    const ns = collectNodes();
    for (let i = 0; i < ns.length; i++) {
      if (ns[i].text.indexOf(c.key) >= 0 &&
          (ns[i].text.indexOf("（1/1）") >= 0 || ns[i].text.indexOf("已完成") >= 0)) {
        log("完成（任务行状态已变更）");
        return true;
      }
    }

    log("未确认到账，按失败处理");
    return false;
  }

  /* ---------- 主流程 ---------- */

  function run() {
    log("启动京东");
    app.launchApp("京东");
    longWait();

    if (!isPanelVisible()) {
      log("京东未停在任务列表面板，退出（请先手动打开每日福利任务列表）");
      toast("请先打开每日福利任务列表");
      return 0;
    }

    const failedAt = {};
    let done = 0;
    let scrollPage = 0;
    let emptyRounds = 0;

    for (let round = 0; round < CFG.maxRounds && done < CFG.maxTasks; round++) {
      scrollToTop();
      for (let p = 0; p < scrollPage; p++) scrollDown();

      const cands = findCandidates();
      let picked = null;
      for (let i = 0; i < cands.length; i++) {
        const last = failedAt[cands[i].key];
        if (last && Date.now() - last < CFG.cooldownMs) continue;
        picked = cands[i];
        break;
      }

      if (!picked) {
        emptyRounds++;
        if (scrollPage < CFG.maxScrollPages) {
          scrollPage++;
          continue;
        }
        if (emptyRounds >= 3) break;
        // 冷却期都还没过，等一轮再看
        sleep(5000);
        scrollPage = 0;
        continue;
      }

      emptyRounds = 0;
      if (runOne(picked)) {
        done++;
        delete failedAt[picked.key];
        // 完成后列表会重排，回到顶部重新扫
        scrollPage = 0;
      } else {
        failedAt[picked.key] = Date.now();
      }
    }

    const msg = "浏览任务结束，完成 " + done + " 个";
    log(msg);
    toast(msg);
    return done;
  }

  module.exports = { run };
})();
