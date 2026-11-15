/**
 * lib/wait —— 延迟与定时原语
 *
 * 只做两件事：睡多久、算到某个时刻还有多久。
 * 不含任何业务语义（不认识页面、不点击、不判断任务）。
 */

/* 语义档位：把散落各处的魔法数字收敛成可调的一处 */

const TIERS = {
  mini: 500,
  short: 3000,
  medium: 5000,
  long: 8000,
};

/**
 * 按档位等待
 * @param {"mini"|"short"|"medium"|"long"} name - 档位名
 * @param {number} [offset] - 在档位基础上增减的毫秒数，可为负
 */
function sleepTier(name, offset) {
  const base = TIERS[name];
  if (typeof base !== "number") {
    throw new Error("unknown wait tier: " + name);
  }
  const ms = Math.max(0, base + (offset || 0));
  if (ms > 0) {
    sleep(ms);
  }
  return ms;
}

/**
 * 覆盖某个档位的时长（运行期调整节奏用，例如低端机整体放慢）
 * @param {"mini"|"short"|"medium"|"long"} name
 * @param {number} ms
 */
function setTier(name, ms) {
  if (typeof TIERS[name] !== "number") {
    throw new Error("unknown wait tier: " + name);
  }
  TIERS[name] = ms;
}

function tierOf(name) {
  return TIERS[name];
}

/* 固定档位的便捷包装（保留旧名，业务侧大量在用） */

function miniWait() {
  sleep(TIERS.mini);
}

function shortWait() {
  sleep(TIERS.short);
}

function mediumWait() {
  sleep(TIERS.medium);
}

function longWait() {
  sleep(TIERS.long);
}

/* 高精度等待与定时 */

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
 * 打印剩余等待时间
 * @param {number} waitTime - remaining time(ms)
 */
function displayRemainTime(waitTime) {
  // 转换等待时间为“小时+分钟”，便于日志查看
  const waitHours = Math.floor(waitTime / 3600000);
  const waitMinutes = Math.floor((waitTime % 3600000) / 60000);
  const waitSeconds = Math.floor((waitTime % 60000) / 1000);

  // 打印定时日志
  console.log(
    `before ${new Date(
      Date.now() + waitTime,
    ).toLocaleString()} 还有：${waitHours} 小时 ${waitMinutes} 分钟 ${waitSeconds} s`,
  );
}

module.exports = {
  /* 档位 */
  sleepTier,
  setTier,
  tierOf,
  miniWait,
  shortWait,
  mediumWait,
  longWait,
  /* 定时 */
  preciseSleep,
  getTimeToTarget,
  displayRemainTime,
};
