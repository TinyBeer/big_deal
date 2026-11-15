/**
 * 兼容垫片
 *
 * 所有实现均已迁入 lib/，此处只做旧名称转发。
 * 老代码 require("./utils") 无需任何改动；新代码建议直接引用具体模块：
 *   const flowLib = require("./lib/flow");
 *
 * 显式逐个 require 而非 require("./lib")：不依赖模块加载器的目录 index 解析行为。
 */

const screenLib = require("./lib/screen");
const waitLib = require("./lib/wait");
const uiLib = require("./lib/ui");
const flowLib = require("./lib/flow");
const loggerLib = require("./lib/logger");
const storageLib = require("./lib/storage");

module.exports = {
  /* wait */
  displayRemainTime: waitLib.displayRemainTime,
  getTimeToTarget: waitLib.getTimeToTarget,
  preciseSleep: waitLib.preciseSleep,
  miniWait: waitLib.miniWait,
  shortWait: waitLib.shortWait,
  mediumWait: waitLib.mediumWait,
  longWait: waitLib.longWait,
  sleepTier: waitLib.sleepTier,
  /* flow */
  waitUntil: flowLib.waitUntil,
  backN: flowLib.backN,
  doubleBackN: flowLib.doubleBackN,
  backUntil: flowLib.backUntil,
  runTask: flowLib.runTask,
  /* screen */
  getScreenSize: screenLib.size,
  isPointInBounds: screenLib.inBounds,
  /* logger */
  info: loggerLib.info,
  debug: loggerLib.debug,
  /* storage */
  storeConfig: storageLib.storeConfig,
  loadConfig: storageLib.loadConfig,
  removeConfig: storageLib.removeConfig,
  /* ui */
  findElementByText: uiLib.findElementByText,
  findText: uiLib.findText,
  tap: uiLib.tap,
  tapText: uiLib.tapText,
  waitForText: uiLib.waitForText,
  drag: uiLib.drag,
  matchImage: uiLib.matchImage,
  captureAndMatch: uiLib.captureAndMatch,
};
