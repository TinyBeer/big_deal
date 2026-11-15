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

  /**
   * 控制台 + 弹窗同时提示（适合需要用户当场看见的关键信息）
   * @param {string} mes
   */
  function info(mes) {
    console.log(mes);
    toast(mes);
  }

  /**
   * 仅控制台输出（适合刷屏的流程日志）
   * @param {string} mes
   */
  function debug(mes) {
    console.log(mes);
  }

  module.exports = {
    info,
    debug,
  };
})();
