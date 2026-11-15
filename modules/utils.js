/**
 * 兼容垫片
 *
 * 所有实现均已迁入 lib/，此处只做旧名称转发。
 * 老代码 require("./utils") 无需任何改动；新代码建议直接引用具体模块：
 *   const flow = require("./lib/flow");
 *   const ui   = require("./lib/ui");
 *
 * 显式逐个 require 而非 require("./lib")：不依赖模块加载器的目录 index 解析行为。
 */

const screen = require("./lib/screen");
const wait = require("./lib/wait");
const ui = require("./lib/ui");
const flow = require("./lib/flow");
const logger = require("./lib/logger");
const storage = require("./lib/storage");

module.exports = {
  /* wait */
  displayRemainTime: wait.displayRemainTime,
  getTimeToTarget: wait.getTimeToTarget,
  preciseSleep: wait.preciseSleep,
  miniWait: wait.miniWait,
  shortWait: wait.shortWait,
  mediumWait: wait.mediumWait,
  longWait: wait.longWait,
  sleepTier: wait.sleepTier,
  /* flow */
  waitUntil: flow.waitUntil,
  backN: flow.backN,
  doubleBackN: flow.doubleBackN,
  backUntil: flow.backUntil,
  runTask: flow.runTask,
  /* screen */
  getScreenSize: screen.size,
  isPointInBounds: screen.inBounds,
  /* logger */
  info: logger.info,
  debug: logger.debug,
  /* storage */
  storeConfig: storage.storeConfig,
  loadConfig: storage.loadConfig,
  removeConfig: storage.removeConfig,
  /* ui */
  findElementByText: ui.findElementByText,
  findText: ui.findText,
  tap: ui.tap,
  tapText: ui.tapText,
  waitForText: ui.waitForText,
  drag: ui.drag,
  matchImage: ui.matchImage,
  captureAndMatch: ui.captureAndMatch,
};
