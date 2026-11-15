/* import */

const screen = require("./lib/screen");
const wait = require("./lib/wait");
const ui = require("./lib/ui");
const flow = require("./lib/flow");

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
  waitUntil: flow.waitUntil,
  backN: flow.backN,
  doubleBackN: flow.doubleBackN,
  backUntil: flow.backUntil,
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
