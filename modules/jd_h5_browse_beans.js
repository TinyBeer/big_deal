/*
 * 京东「看病买药」浏览领京豆任务自动化
 *
 * 完整流程：启动京东 App -> 首页进入「看病买药」->「签到领京豆」->「领更多京豆」
 * -> 扫描「做任务赚更多京豆」列表 -> 完成同行含「浏览Xs」和「京豆」的任务
 * -> 结束后返回京东首页。关注、领券、健康能量以及会跳外部应用的任务一律跳过。
 */
(function () {
  const logger = require("./lib/logger");

  const CFG = {
    appName: "京东",
    homeEntry: "看病买药",
    signText: "签到领京豆",
    moreText: "领更多京豆",
    listTitle: "做任务赚更多京豆",

    goButtons: ["去完成", "去领取"],
    browseRe: /^浏览(\d+)s$/,
    beanText: "京豆",
    skipNames: ["新用户有好礼", "加营养师得200京豆", "去养猪猪免费领好物"],

    maxTasks: 30,
    maxRounds: 120,
    bufferMs: 1500,
    pollMs: 500,
    returnWaitMs: 10000,
    navTimeoutMs: 15000,
  };

  function log(msg) {
    logger.debug("[看病买药] " + msg);
  }

  function visible(n) {
    return n.right > n.left && n.bottom > n.top && n.bottom > 0 && n.top < 2400;
  }

  function centerX(n) {
    return (n.left + n.right) / 2;
  }

  function centerY(n) {
    return (n.top + n.bottom) / 2;
  }

  function collectNodes() {
    let out = [];
    let all = textMatches(".+").find();
    for (let i = 0; i < all.length; i++) {
      let o = all[i];
      let t = o.text();
      if (!t) continue;
      let b = o.bounds();
      if (!b) continue;
      out.push({
        text: String(t).trim(),
        left: b.left,
        top: b.top,
        right: b.right,
        bottom: b.bottom,
        clickable: !!o.clickable(),
      });
    }
    return out;
  }

  /* 任务行定位：右侧按钮 + 同行左侧「浏览Xs」+「京豆」 */
  function findCandidates() {
    let ns = collectNodes();
    let res = [];
    for (let i = 0; i < ns.length; i++) {
      let btn = ns[i];
      if (!visible(btn) || !btn.clickable) continue;
      if (CFG.goButtons.indexOf(btn.text) < 0) continue;
      if (centerX(btn) < 800) continue;

      let cy = centerY(btn);
      let name = null;
      let browse = null;
      let bean = false;

      for (let j = 0; j < ns.length; j++) {
        let n = ns[j];
        if (!visible(n) || n.left >= 800) continue;
        if (Math.abs(centerY(n) - cy) > 70) continue;

        let m = CFG.browseRe.exec(n.text);
        if (m) {
          browse = parseInt(m[1], 10);
          continue;
        }
        if (n.text === CFG.beanText) {
          bean = true;
          continue;
        }
        // 任务名固定在左侧 x≈181；商品标题等从 x≈407 开始，排除掉
        if (!name && n.left >= 150 && n.left <= 260 && n.text.length > 1 &&
            n.text.indexOf("浏览") < 0 &&
            CFG.goButtons.indexOf(n.text) < 0 && n.text.indexOf(".") < 0 && !/^\d+$/.test(n.text)) {
          name = n.text;
        }
      }

      if (name && browse && bean) {
        let skip = false;
        for (let k = 0; k < CFG.skipNames.length; k++) {
          if (name.indexOf(CFG.skipNames[k]) >= 0) skip = true;
        }
        if (skip) continue;
        res.push({ name: name, seconds: browse, btn: btn, key: name + "|" + browse });
      }
    }
    return res;
  }

  function tapNode(n) {
    click(Math.round(centerX(n)), Math.round(centerY(n)));
  }

  /* 浏览页返回控件：clickable=false 的 TextView 也直接按坐标点 */
  function tryReturn() {
    let ns = collectNodes();
    for (let i = 0; i < ns.length; i++) {
      let n = ns[i];
      if (!visible(n)) continue;
      if (n.text.indexOf("点击立即返回") >= 0) {
        tapNode(n);
        log("点击「点击立即返回」");
        return true;
      }
      if (n.text === "返回按钮") {
        tapNode(n);
        log("点击「返回按钮」");
        return true;
      }
    }
    return false;
  }

  function isListVisible() {
    let ns = collectNodes();
    for (let j = 0; j < ns.length; j++) {
      if (ns[j].text.indexOf(CFG.listTitle) >= 0) return true;
    }
    return false;
  }

  function waitListVisible() {
    for (let i = 0; i < 20; i++) {
      if (isListVisible()) return true;
      sleep(CFG.pollMs);
    }
    return false;
  }

  function clickTextNode(o) {
    if (!o) return false;
    let b = o.bounds();
    if (!b) return false;
    click(Math.round((b.left + b.right) / 2), Math.round((b.top + b.bottom) / 2));
    return true;
  }

  function waitText(tx, timeout) {
    let deadline = Date.now() + (timeout || 3000);
    while (Date.now() < deadline) {
      let o = text(tx).findOne(300);
      if (o) return o;
      sleep(300);
    }
    return null;
  }

  function waitContains(tx, timeout) {
    let deadline = Date.now() + (timeout || 3000);
    while (Date.now() < deadline) {
      let o = textContains(tx).findOne(300);
      if (o) return o;
      sleep(300);
    }
    return null;
  }

  /* 「领更多京豆」按钮在右上角；顶部「做任务 领更多京豆」不是按钮 */
  function findMoreButton() {
    let list = text(CFG.moreText).find();
    for (let i = 0; i < list.length; i++) {
      let b = list[i].bounds();
      if (b && b.top > 400 && b.left > 600) return list[i];
    }
    return null;
  }

  function waitHomeEntry() {
    let deadline = Date.now() + CFG.navTimeoutMs;
    while (Date.now() < deadline) {
      let homeTab = desc("首页").findOne(200) || text("首页").findOne(200);
      let entry = text(CFG.homeEntry).findOne(200);
      if (homeTab && entry) return true;
      sleep(300);
    }
    return false;
  }

  /* 启动京东并回到首页 */
  function bringToFront() {
    log("启动京东");
    app.launchApp(CFG.appName);
    if (waitHomeEntry()) return true;

    log("首页未就绪，拉起主 Activity");
    app.startActivity({
      packageName: "com.jingdong.app.mall",
      className: "com.jingdong.app.mall.MainFrameActivity",
    });
    return waitHomeEntry();
  }

  function waitMoreButton(timeout) {
    let deadline = Date.now() + (timeout || 5000);
    while (Date.now() < deadline) {
      let o = text(CFG.moreText).findOne(200);
      if (o) {
        let b = o.bounds();
        if (b && b.top > 400 && b.left > 600) return o;
      }
      let found = findMoreButton();
      if (found) return found;
      sleep(300);
    }
    return null;
  }

  /* 首页 -> 看病买药 -> 签到领京豆 -> 领更多京豆 */
  function openTaskList() {
    let med = waitText(CFG.homeEntry, 5000);
    if (!med) {
      log("未找到看病买药入口");
      return false;
    }
    log("进入看病买药");
    clickTextNode(med);
    sleep(2000);

    let sign = waitContains(CFG.signText, 5000);
    if (!sign) {
      log("未找到签到领京豆入口");
      return false;
    }
    // 页面刚加载完会重排，等稳定后重新取一次控件坐标
    sleep(1000);
    sign = waitContains(CFG.signText, 2000);
    if (!sign) {
      log("签到领京豆节点已失效");
      return false;
    }
    let sb = sign.bounds();
    log("点击签到领京豆 " + (sb ? sb.left + "," + sb.top + "," + sb.right + "," + sb.bottom : ""));
    clickTextNode(sign);
    sleep(1500);

    let more = waitMoreButton(6000);
    if (!more) {
      log("二次点击签到领京豆");
      sign = waitContains(CFG.signText, 2000);
      if (sign) clickTextNode(sign);
      more = waitMoreButton(6000);
    }
    if (!more) {
      log("未找到领更多京豆按钮");
      return false;
    }
    log("点击领更多京豆");
    clickTextNode(more);
    return waitListVisible();
  }

  /* 任务页丢了时，优先点秒杀页的领更多京豆；否则从首页重新走一遍 */
  function ensureTaskList() {
    if (isListVisible()) return true;
    log("重新进入任务列表");
    let more = findMoreButton();
    if (more) {
      clickTextNode(more);
      return waitListVisible();
    }
    if (text(CFG.homeEntry).findOne(1000)) return openTaskList();
    return false;
  }

  function runOne(c) {
    log("执行: " + c.name + "，浏览" + c.seconds + "s，按钮「" + c.btn.text + "」");
    tapNode(c.btn);

    // 浏览时长未到时不要提前点返回，否则不计任务
    sleep(c.seconds * 1000 + CFG.bufferMs);

    let returned = false;
    let deadline = Date.now() + CFG.returnWaitMs;
    while (Date.now() < deadline) {
      if (tryReturn()) {
        returned = true;
        break;
      }
      sleep(CFG.pollMs);
    }
    if (!returned) {
      log("未找到返回控件，连续按返回键");
      for (let k = 0; k < 4; k++) {
        back();
        sleep(1000);
        if (isListVisible()) {
          returned = true;
          break;
        }
      }
    }
    if (!ensureTaskList()) {
      log("未回到任务列表，结束");
      return false;
    }
    sleep(500);
    return true;
  }

  function isHomePage() {
    let homeTab = desc("首页").findOne(200) || text("首页").findOne(200);
    return !!homeTab && !!text(CFG.homeEntry).findOne(200);
  }

  /* 结束时逐级返回：任务浮层 -> 秒杀页 -> 看病买药 -> 首页；失败则拉主 Activity */
  function backToHome() {
    log("返回京东首页");
    if (isHomePage()) return true;

    for (let i = 0; i < 6 && !isHomePage(); i++) {
      back();
      sleep(800);
    }
    if (isHomePage()) return true;

    log("返回键未生效，拉起主 Activity");
    app.startActivity({
      packageName: "com.jingdong.app.mall",
      className: "com.jingdong.app.mall.MainFrameActivity",
    });
    let deadline = Date.now() + CFG.navTimeoutMs;
    while (Date.now() < deadline) {
      if (isHomePage()) return true;
      sleep(300);
    }
    return false;
  }

  function finish(done, msg) {
    log(msg);
    backToHome();
    try {
      notice("京东任务助手", msg);
    } catch (e) {
      toast(msg);
    }
    return done;
  }

  function run() {
    let processed = {};
    let done = 0;

    if (isListVisible()) {
      log("任务列表已打开，直接执行");
    } else {
      if (!bringToFront()) {
        return finish(0, "京东未回到首页，退出");
      }
      if (!openTaskList()) {
        return finish(0, "未打开任务列表，退出");
      }
    }
    if (!ensureTaskList()) {
      return finish(0, "未找到任务列表，退出");
    }

    let initial = findCandidates();
    let names = [];
    for (let i = 0; i < initial.length; i++) names.push(initial[i].name);
    log("识别到 " + initial.length + " 个候选: " + names.join("、"));

    // 未完成的任务会自动排到列表上方，不做上滑；只处理当前可见候选。
    for (let round = 0; round < CFG.maxRounds && done < CFG.maxTasks; round++) {
      let cands = findCandidates();
      let picked = null;
      for (let i = 0; i < cands.length; i++) {
        if (!processed[cands[i].key]) {
          picked = cands[i];
          break;
        }
      }
      if (!picked) break;

      processed[picked.key] = true;
      if (!runOne(picked)) break;
      done++;
    }

    return finish(done, "看病买药浏览领豆结束，完成 " + done + " 个任务");
  }

  module.exports = { run };
})();
