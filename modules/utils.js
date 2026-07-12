/* import */

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
function miniWait() {
  sleep(500);
}

function shortWait() {
  sleep(3000);
}

function mediumWait() {
  sleep(5000);
}

function longWait() {
  sleep(8000);
}

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
    shortWait();
    if (untilFunc && untilFunc()) {
      break;
    }
  }
}

function doubleBackN(cnt, untilFunc) {
  for (let i = 0; i < cnt; i++) {
    back();
    back();
    shortWait();
    if (untilFunc && untilFunc()) {
      break;
    }
  }
}

/**
 * 获取屏幕尺寸
 */
function getScreenSize() {
  var dm = context.getResources().getDisplayMetrics();

  var width = dm.widthPixels;
  var height = dm.heightPixels;

  return {
    width: width,
    height: height,
  };
}

/**
 * 高精度延迟函数
 * @param {number} ms - 期望延迟的毫秒数
 * @param {boolean} showLog - display remaining sleep time
 */
function preciseSleep(ms, showLog) {
  const start = new Date().getTime();
  let remaining = ms;

  // 循环检查，补偿误差
  while (remaining > 0) {
    // 每次最多休眠remaining，避免过度休眠
    sleep(Math.min(remaining, 5000)); // 每次最多休眠5000ms，平衡精度和性能
    var now = new Date().getTime();
    remaining = ms - (now - start);
    if (showLog) {
      displayRemainTime(remaining);
    }
  }
}

/**
 * get escape to specific time
 * @param {number} hour
 * @param {number} minute
 */
function getTimeToTarget(hour, minute) {
  const now = new Date(); // 当前时间
  const target = new Date(now); // 初始化目标时间为当前日期

  // 设置目标时间为“当天的 hour:minute:00.000”
  target.setHours(hour, minute, 0, 0);

  // 若当前时间已过当天的目标时间，则将目标时间设为“次日的 hour:minute”
  if (target <= now) {
    target.setDate(now.getDate() + 1); // 日期 +1（到次日）
  }

  // 返回时间差（毫秒）：目标时间 - 当前时间
  return target - now;
}
/**
 * 高精度延迟函数
 * @param {number} waitTime - remaining time(ms)
 */
function displayRemainTime(waitTime) {
  // 转换等待时间为“小时+分钟”，便于日志查看
  const waitHours = Math.floor(waitTime / 3600000);
  const waitMinutes = Math.floor((waitTime % 3600000) / 60000);
  const waitSeconds = Math.floor((waitTime % 60000) / 1000);

  // 打印定时日志
  // console.log(`\n=== 已设置下次定时 ===`);
  // console.log(`当前时间：${new Date().toLocaleString()}`);
  console.log(
    `before ${new Date(
      Date.now() + waitTime,
    ).toLocaleString()} 还有：${waitHours} 小时 ${waitMinutes} 分钟 ${waitSeconds} s`,
  );
  // console.log(`下次执行时间：${new Date(Date.now() + waitTime).toLocaleString()}`);
}

/**
 * 判断点是否在区域内部
 * @param {object} point -  point: {x,y}
 * @param {Array<int>} bounds - bounds:[x1,y1,x2,y2]
 */
function isPointInBounds(point, bounds) {
  return (
    point.x > bounds[0] &&
    point.x < bounds[2] &&
    point.y > bounds[1] &&
    point.y < bounds[3]
  );
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
module.exports = {
  displayRemainTime,
  getTimeToTarget,
  preciseSleep,
  getScreenSize,
  miniWait,
  shortWait,
  mediumWait,
  longWait,
  waitUntil,
  backN,
  doubleBackN,
  isPointInBounds,
  info,
  storeConfig,
  loadConfig,
  findElementByText,
  matchImage,
  captureAndMatch,
};
