/**
 * lib/flow —— 条件等待与页面回退
 *
 * 只管「等到什么时候」「退几层」，不判断自己在哪个 App、哪个页面。
 * 判断依据一律由调用方的 isHere / untilFunc 提供。
 */

const wait = require("./wait");

/**
 * 条件等待
 * @param {number} ms - longest waiting ms
 * @param {function () boolean } uf - wait until function return true
 * @returns {boolean} 是否在超时前满足
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

/**
 * 连退 N 次，每退一次检查一次是否已到目标页
 * @param {number} cnt - 最多退几次
 * @param {function () boolean } [untilFunc] - 返回 true 时提前结束
 */
function backN(cnt, untilFunc) {
  for (let i = 0; i < cnt; i++) {
    back();
    wait.shortWait();
    if (untilFunc && untilFunc()) {
      break;
    }
  }
}

/**
 * 每次退两层（用于弹窗 + 页面叠加的情况）
 * @param {number} cnt
 * @param {function () boolean } [untilFunc]
 */
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

/**
 * 退到某个页面为止
 * @param {function () boolean} isHere - 判断「已经到了目标页」
 * @param {object} [opts]
 * @param {number} [opts.max] - 最多退几次，默认 3
 * @param {boolean} [opts.double] - 每次退两层，默认 false
 * @returns {boolean} 是否退到了目标页
 */
function backUntil(isHere, opts) {
  opts = opts || {};
  if (typeof isHere !== "function") {
    return false;
  }

  // 已经在目标页就别乱退
  if (isHere()) {
    return true;
  }

  const max = typeof opts.max === "number" ? opts.max : 3;
  const step = opts.double ? doubleBackN : backN;

  let reached = false;
  step(max, () => {
    reached = !!isHere();
    return reached;
  });
  return reached;
}

module.exports = {
  waitUntil,
  backN,
  doubleBackN,
  backUntil,
};
