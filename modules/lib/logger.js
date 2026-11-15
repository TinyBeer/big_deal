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
