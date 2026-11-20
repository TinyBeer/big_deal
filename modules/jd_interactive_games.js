/* import */

const {
  longWait,
  waitUntil,
  sleepTier,
  tap,
  getScreenSize,
} = require("./utils");
const { info, debug } = require("./lib/logger");

function run() {
  let ok = false;
  try {
    ok = launchAndEnterGame();
    if (ok) {
      browseTasks();
    } else {
      debug("进入互动游戏失败，跳过");
    }
  } finally {
    backToHome();
    info(ok ? "互动游戏任务完成" : "互动游戏任务未完成");
  }
}

/* 页面判断：依靠三个页面互不重叠的标志控件 */

function isHomePage() {
  return !!text("新品").findOne(300);
}

function isMinePage() {
  return !!desc("我的").findOne(300) && !!text("互动游戏").findOne(300);
}

function isGamePage() {
  return !!text("返回").findOne(300);
}

/* 进入互动游戏：启动京东 -> 我的 -> 互动游戏，每一步都等待并校验 */

function launchAndEnterGame() {
  debug("启动京东...");
  app.launchApp("京东");
  longWait();

  let ready = function () {
    return isHomePage() || isMinePage() || isGamePage();
  };
  if (!waitUntil(10000, ready)) {
    // 冷启动或被系统清理后 launchApp 可能不生效，直接拉起主 Activity
    app.startActivity({
      packageName: "com.jingdong.app.mall",
      className: "com.jingdong.app.mall.MainFrameActivity",
    });
    longWait();
    if (!waitUntil(15000, ready)) {
      debug("京东页面未就绪");
      return false;
    }
  }

  // 上次运行可能停在游戏页或"我的"页，先回到首页
  if (!ensureHomePage()) {
    debug("未能回到京东首页");
    return false;
  }
  sleepTier("short");

  debug("进入我的界面...");
  let mineTab = desc("我的").findOne(5000);
  if (!mineTab) {
    debug("未找到我的入口");
    return false;
  }
  tap(mineTab);
  if (!waitUntil(12000, isMinePage)) {
    debug("未进入我的界面");
    return false;
  }
  sleepTier("short");

  debug("进入互动游戏...");
  let gameEnter = text("互动游戏").findOne(5000);
  if (!gameEnter) {
    debug("未找到互动游戏入口");
    return false;
  }
  tap(gameEnter);
  if (!waitUntil(30000, isGamePage)) {
    debug("未进入互动游戏页面");
    return false;
  }
  // WebView 加载较慢，进入后再留出稳定时间
  sleepTier("medium");
  return true;
}

/* 返回主界面：互动游戏 -> 我的 -> 首页 */

function backToHome() {
  debug("返回主界面...");

  if (ensureHomePage()) {
    debug("已回到京东主界面");
    return true;
  }

  // 小游戏等页面可能拦截返回键，直接拉起主 Activity 兜底
  for (let retry = 0; retry < 2; retry++) {
    debug("返回键无效，重新拉起京东主界面");
    app.startActivity({
      packageName: "com.jingdong.app.mall",
      className: "com.jingdong.app.mall.MainFrameActivity",
    });
    longWait();
    if (ensureHomePage()) {
      debug("已回到京东主界面");
      return true;
    }
  }
  debug("未能回到主界面");
  return false;
}

/* 兜底回首页：识别到"我的"就切首页 tab，否则逐层返回 */

function ensureHomePage() {
  if (isHomePage()) {
    return true;
  }

  for (let i = 0; i < 5 && !isHomePage(); i++) {
    if (isGamePage()) {
      back();
      sleepTier("short");
      continue;
    }

    if (isMinePage()) {
      let homeTab = desc("首页").findOne(3000);
      if (homeTab) {
        tap(homeTab);
        sleepTier("short");
        continue;
      }
    }

    back();
    sleepTier("short");
  }
  return isHomePage();
}

/* 攒经验任务弹窗 */

const TASK_POPUP_TITLE = "做任务 攒经验";
const BROWSE_LOAD_BUFFER_MS = 8000; // 任务卡片写的浏览时长之外，额外预留的页面加载时间
const BROWSE_DEFAULT_SECONDS = 8; // 读不到"浏览X秒"时的兜底时长

/* 任务文本包含以下任意一项则跳过，按需填写 */
const TASK_SKIP_KEYWORDS = [];

function isTaskPopup() {
  return !!text(TASK_POPUP_TITLE).findOne(300);
}

function enterTaskPopup() {
  let entry = textContains("攒经验").findOne(5000);
  if (!entry) {
    entry = id("earn-jingdou-earn-experience-entry").findOne(2000);
  }
  if (!entry) {
    debug("未找到攒经验入口");
    return false;
  }
  tap(entry);
  if (!waitUntil(10000, isTaskPopup)) {
    debug("未进入攒经验任务弹窗");
    return false;
  }
  sleepTier("short");
  return true;
}

function leaveTaskPopup() {
  for (let i = 0; i < 3 && isTaskPopup(); i++) {
    back();
    sleepTier("short");
  }
}

/* 所有"逛一逛"按钮，只保留屏幕范围内、有实际高度的 */
function getBrowseButtons(onlyVisible) {
  let all = text("逛一逛").find(500);
  let screen = getScreenSize();
  let result = [];
  for (let i = 0; i < all.length; i++) {
    let obj = all[i];
    let b = obj.bounds();
    if (!b || b.height() <= 0) {
      continue;
    }
    if (onlyVisible) {
      let c = obj.center();
      if (c.y <= 0 || c.y >= screen.height) {
        continue;
      }
    }
    result.push(obj);
  }
  return result;
}

/* 用同行左侧的任务名标识任务，列表重排后仍能找到同一个按钮 */
function getTaskName(btn) {
  let b = btn.bounds();
  if (!b) {
    return "";
  }
  let names = textMatches(".*\\(\\d+/\\d+\\).*").find(500);
  for (let i = 0; i < names.length; i++) {
    let nb = names[i].bounds();
    if (!nb) {
      continue;
    }
    let ny = (nb.top + nb.bottom) / 2;
    if (ny >= b.top - 20 && ny <= b.bottom + 20 && nb.right <= b.left + 10) {
      return names[i].text().replace(/\(\d+\/\d+\).*/, "");
    }
  }
  return "";
}

/* 从任务卡片中"浏览X秒"的描述读出所需浏览秒数；读不到返回 0 */
function getBrowseSeconds(btn) {
  let b = btn.bounds();
  if (!b) {
    return 0;
  }
  let descs = textMatches("浏览\\d+秒").find(500);
  for (let i = 0; i < descs.length; i++) {
    let db = descs[i].bounds();
    if (!db) {
      continue;
    }
    let dy = (db.top + db.bottom) / 2;
    if (dy >= b.top - 20 && dy <= b.bottom + 20 && db.right <= b.left + 10) {
      let m = /(\d+)/.exec(descs[i].text());
      return m ? parseInt(m[1], 10) : 0;
    }
  }
  return 0;
}

/* 任务描述命中任意关键字就跳过 */
function isTaskSkipped(name) {
  if (!name) {
    return false;
  }
  for (let i = 0; i < TASK_SKIP_KEYWORDS.length; i++) {
    if (name.indexOf(TASK_SKIP_KEYWORDS[i]) !== -1) {
      return true;
    }
  }
  return false;
}

/* 每轮从当前界面重新选取一个未处理过的可见逛一逛按钮 */
function pickVisibleBrowseTask(processed) {
  let btns = getBrowseButtons(true);
  for (let i = 0; i < btns.length; i++) {
    let n = getTaskName(btns[i]);
    // 名称取不到时用位置兜底，避免空 key 把其它任务一起屏蔽
    let key = n || "pos-" + btns[i].bounds().top;
    if (processed[key]) {
      continue;
    }
    if (isTaskSkipped(n)) {
      debug("跳过任务: " + n);
      processed[key] = true;
      continue;
    }
    return { btn: btns[i], name: n, key: key, seconds: getBrowseSeconds(btns[i]) };
  }
  return null;
}

function browseTasks() {
  if (!enterTaskPopup()) {
    return;
  }

  let processed = {};
  let maxTasks = 30;
  for (let i = 0; i < maxTasks; i++) {
    if (!isTaskPopup()) {
      debug("任务弹窗已关闭");
      break;
    }

    let picked = pickVisibleBrowseTask(processed);
    if (!picked) {
      debug("屏幕内没有可执行的逛一逛任务");
      break;
    }
    processed[picked.key] = true;

    // 时长直接取任务卡片上的"浏览X秒"，再加加载缓冲；不观测返回控件，到时间自动返回。
    let browseMs = (picked.seconds || BROWSE_DEFAULT_SECONDS) * 1000 + BROWSE_LOAD_BUFFER_MS;
    debug("逛一逛任务: " + (picked.name || "未知") + "，浏览" + (picked.seconds || BROWSE_DEFAULT_SECONDS) + "秒，等待" + (browseMs / 1000) + "秒");
    tap(picked.btn);

    sleep(browseMs);
    // 先退一次；绝大多数任务一次就回到弹窗。
    back();
    // 少数（如掼蛋游戏）一次退不回弹窗，3 秒内没回来就再补一次返回。
    if (!waitUntil(3000, isTaskPopup)) {
      debug("一次返回未回到弹窗，再返回一次");
      back();
    }
    if (!waitUntil(5000, isTaskPopup)) {
      debug("未回到任务弹窗，结束后续任务");
      break;
    }
    sleepTier("mini");
  }

  leaveTaskPopup();
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
