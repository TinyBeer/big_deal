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
