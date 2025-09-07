auto();
const utils = require("./utils");
const smzdm = require("./smzdm");
const ctcp = require("./china_telecom_cloud_pan");
const sgo = require("./state_grid_online");

const targetHour = 0; // 目标小时（24小时制，如 20 代表晚上 8 点）
const targetMinute = 5; // 目标分钟

const screenSize = utils.getScreenSize();
console.log(
  "屏幕宽度: " + screenSize.width + "px, 屏幕高度: " + screenSize.height + "px"
);

/* keep screen on */
device.keepScreenOn();
console.log("已开启屏幕常亮");

/* waiting until specific time */
const waitTime = utils.getTimeToTarget(targetHour, targetMinute);
// utils.preciseSleep(waitTime, true);

ctcp.sign();
sgo.sign();
smzdm.sign();

device.cancelKeepingAwake();
console.log("已关闭屏幕常亮");
