/*
 * 整个模块体包在 IIFE 里。
 *
 * AutoJs6 的 jvm-npm 会把模块代码求值到「调用方作用域」，模块顶层的 const / function
 * 会漏进调用方作用域（main.js 的 "ui"; 还会在此处声明全局 var ui），一旦重名就会报
 * 「变量 xxx 重复声明」，整个 require 链失败。包一层后内部命名完全封闭，导出照旧走 module.exports。
 */
(function () {
  /**
   * lib/flow —— 条件等待与页面回退
   *
   * 只管「等到什么时候」「退几层」，不判断自己在哪个 App、哪个页面。
   * 判断依据一律由调用方的 isHere / untilFunc 提供。
   */

  const flowWait = require("./wait");

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
      flowWait.shortWait();
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
      flowWait.shortWait();
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

  /**
   * 任务包装器：屏幕常亮 + 异常兜底 + 一定收尾
   *
   * 不负责启动 App（各任务自己在 run 里 launchApp），只管「跑起来之后别把屏幕亮着忘了关」。
   *
   * @param {function} fn - 任务主体
   * @param {object} [opts]
   * @param {string} [opts.label] - 出错时日志里的任务名，默认 "task"
   * @param {boolean} [opts.keepAwake] - 是否管理屏幕常亮，默认 true
   * @returns {*} fn 的返回值；抛错时返回 undefined
   */
  function runTask(fn, opts) {
    opts = opts || {};
    const label = opts.label || "task";
    const keepAwake = opts.keepAwake !== false;

    if (keepAwake) {
      device.keepScreenOn();
      console.log("已开启屏幕常亮");
    }

    try {
      return fn();
    } catch (e) {
      console.log(label + " failed: " + e);
    } finally {
      if (keepAwake) {
        device.cancelKeepingAwake();
        console.log("已关闭屏幕常亮");
      }
    }
  }

  module.exports = {
    waitUntil,
    backN,
    doubleBackN,
    backUntil,
    runTask,
  };
})();
