/*
 * 整个模块体包在 IIFE 里。
 *
 * AutoJs6 的 jvm-npm 会把模块代码求值到「调用方作用域」，模块顶层的 const / function
 * 会漏进调用方作用域（main.js 的 "ui"; 还会在此处声明全局 var ui），一旦重名就会报
 * 「变量 xxx 重复声明」，整个 require 链失败。包一层后内部命名完全封闭，导出照旧走 module.exports。
 */
(function () {
  /**
   * lib/storage —— 键值存储
   *
   * 只做读写，不关心存的是什么。存储名与键名由调用方决定。
   */

  const STORAGE_NAME = "autojs";

  /**
   * 写入一项配置
   * @param {string} name - 键名
   * @param {*} conf - 任意可序列化值
   */
  function storeConfig(name, conf) {
    let sto = storages.create(STORAGE_NAME);
    sto.put(name, conf);
  }

  /**
   * 读取一项配置
   * @param {string} name - 键名
   * @returns {*} 不存在时为 undefined
   */
  function loadConfig(name) {
    let sto = storages.create(STORAGE_NAME);
    return sto.get(name);
  }

  /**
   * 删除一项配置
   * @param {string} name - 键名
   */
  function removeConfig(name) {
    let sto = storages.create(STORAGE_NAME);
    sto.remove(name);
  }

  module.exports = {
    storeConfig,
    loadConfig,
    removeConfig,
  };
})();
