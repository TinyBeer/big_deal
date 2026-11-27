/*
 * 整个模块体包在 IIFE 里。
 *
 * AutoJs6 的 jvm-npm 会把模块代码求值到「调用方作用域」，模块顶层的 const / function
 * 会漏进调用方作用域（main.js 的 "ui"; 还会在此处声明全局 var ui），一旦重名就会报
 * 「变量 xxx 重复声明」，整个 require 链失败。包一层后内部命名完全封闭，导出照旧走 module.exports。
 */
(function () {
  /**
   * lib/logger —— 日志输出
   *
   * 唯一职责是「把消息送出去」，不拼接业务文案、不判断任务状态。
   */

  /* 等级数值越小越详细，阈值可由后续配置注入 */
  const LEVELS = {
    debug: 10,
    info: 20,
    warn: 30,
    error: 40,
  };

  let threshold = LEVELS.debug;
  const GLOBAL_KEY = "__autojsLoggerThreshold";

  /* Auto.js 子线程可能拿到独立的模块实例，阈值放全局让各线程共享 */
  function currentThreshold() {
    if (typeof global !== "undefined" && typeof global[GLOBAL_KEY] === "number") {
      return global[GLOBAL_KEY];
    }
    return threshold;
  }

  /**
   * 设置最低输出等级，供日志等级配置接入
   * @param {"debug"|"info"|"warn"|"error"|number} level
   * @returns {boolean} 是否设置成功
   */
  function setLevel(level) {
    const value = typeof level === "number" ? level : LEVELS[String(level).toLowerCase()];
    if (typeof value !== "number" || isNaN(value)) {
      return false;
    }
    threshold = value;
    if (typeof global !== "undefined") {
      global[GLOBAL_KEY] = value;
    }
    return true;
  }

  /** @returns {string|number} 当前最低输出等级 */
  function getLevel() {
    const cur = currentThreshold();
    const names = Object.keys(LEVELS);
    for (let i = 0; i < names.length; i++) {
      if (LEVELS[names[i]] === cur) {
        return names[i];
      }
    }
    return cur;
  }

  function enabled(level) {
    return LEVELS[level] >= currentThreshold();
  }

  /** 控制台 + 弹窗同时提示（适合需要用户当场看见的关键信息） */
  function info(mes) {
    if (!enabled("info")) return;
    console.log(mes);
    toast(mes);
  }

  /** 仅控制台输出（适合刷屏的流程日志） */
  function debug(mes) {
    if (!enabled("debug")) return;
    console.log(mes);
  }

  /** 预期之外但可继续的情况 */
  function warn(mes) {
    if (!enabled("warn")) return;
    console.log("[WARN] " + mes);
  }

  /** 异常或失败，通常意味着任务没完成 */
  function error(mes) {
    if (!enabled("error")) return;
    console.log("[ERROR] " + mes);
    toast(mes);
  }

  module.exports = {
    debug,
    info,
    warn,
    error,
    setLevel,
    getLevel,
    LEVELS,
  };
})();
