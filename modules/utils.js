/* import */

const screen = require("./lib/screen");
const wait = require("./lib/wait");
const ui = require("./lib/ui");

/* storage */
const storageName = "autojs";
function storeConfig(name, conf) {
  let sto = storages.create(storageName);
  sto.put(name, conf);
}

function loadConfig(name) {
  let sto = storages.create(storageName);
  return sto.get(name);
}

/* message */
function info(mes) {
  console.log(mes);
  toast(mes);
}

/* delay */
/**
 * 条件等待
 * @param {number} ms - longest waiting ms
 * @param {function () boolean } uf - wait until function return true
 */
function waitUntil(ms, uf) {
  let remaining = ms;
  const eachMs = 500;
  if (!remaining || remaining <= 0) {
    remaining = eachMs;
  }

  // 循环检查，补偿误差
  while (remaining > 0) {
    // 每次最多休眠remaining，避免过度休眠
    sleep(Math.min(remaining, eachMs)); // 每次最多休眠 eachMs ms，平衡精度和性能
    remaining -= eachMs;
    if (uf && uf()) {
      return true;
    }
  }
  return false;
}

/* back */
function backN(cnt, untilFunc) {
  for (let i = 0; i < cnt; i++) {
    back();
    wait.shortWait();
    if (untilFunc && untilFunc()) {
      break;
    }
  }
}

function doubleBackN(cnt, untilFunc) {
  for (let i = 0; i < cnt; i++) {
    back();
    back();
    wait.shortWait();
    if (untilFunc && untilFunc()) {
      break;
    }
  }
}

// 导出函数（供其他脚本调用）
// 由 lib/ 逐步接管，此处保留旧名称做兼容转发
module.exports = {
  displayRemainTime: wait.displayRemainTime,
  getTimeToTarget: wait.getTimeToTarget,
  preciseSleep: wait.preciseSleep,
  getScreenSize: screen.size,
  miniWait: wait.miniWait,
  shortWait: wait.shortWait,
  mediumWait: wait.mediumWait,
  longWait: wait.longWait,
  sleepTier: wait.sleepTier,
  waitUntil,
  backN,
  doubleBackN,
  isPointInBounds: screen.inBounds,
  info,
  storeConfig,
  loadConfig,
  findElementByText: ui.findElementByText,
  matchImage: ui.matchImage,
  captureAndMatch: ui.captureAndMatch,
  findText: ui.findText,
  tap: ui.tap,
  tapText: ui.tapText,
};
