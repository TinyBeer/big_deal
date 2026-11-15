/* import */

const screen = require("./lib/screen");
const wait = require("./lib/wait");

/* element */
const defaultDuration = 500;
function findElementByText(tx, dur) {
  let d = defaultDuration;
  if (dur) {
    d = dur;
  }
  return text(tx).findOne(d);
}

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

/* 图片匹配 */

/**
 * 在指定区域内匹配模板图片
 * @param {Image} screenImg - 屏幕截图
 * @param {string} templatePath - 模板图片路径（相对路径）
 * @param {Array} region - [x1, y1, x2, y2]
 * @param {number} threshold - 匹配阈值 0-1，默认 0.7
 * @returns {Object|null} 匹配结果 {x, y, similarity}
 */
function matchImage(screenImg, templatePath, region, threshold) {
  threshold = threshold || 0.7;
  var tpl = images.read(templatePath);
  if (!tpl) {
    log("模板加载失败: " + templatePath);
    return null;
  }

  var findRegion = [region[0], region[1], region[2] - region[0], region[3] - region[1]];
  var result = images.findImage(screenImg, tpl, {
    region: findRegion,
    threshold: threshold
  });

  tpl.recycle();
  return result;
}

/**
 * 截屏并检测区域内是否有指定模板图片
 * @param {string} templatePath - 模板图片路径（相对路径）
 * @param {Array} region - [x1, y1, x2, y2]
 * @param {number} threshold - 匹配阈值 0-1，默认 0.7
 * @returns {Object|null} 匹配结果 {x, y, similarity}
 */
function captureAndMatch(templatePath, region, threshold) {
  var screenImg = images.captureScreen();
  if (!screenImg) {
    log("截图失败");
    return null;
  }
  var result = matchImage(screenImg, templatePath, region, threshold);
  screenImg.recycle();
  return result;
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
  findElementByText,
  matchImage,
  captureAndMatch,
};
