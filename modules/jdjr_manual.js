/* import */
const utils = require("./utils");

let gameTaskList = [];

function run(screen) {
  // launch app
  app.launchApp("京东金融");
  sleep(5000);

  double_sign();

  utils.backN(2);
  back();
  utils.backN(1);
}

function double_sign() {
  console.log("京东金融双签到 ...");
  let backCnt = 0;
  let signEntry = text("签到").findOne(1000);
  if (!signEntry) {
    console.log("missing sign entry, skip");
    return false;
  }
  click(signEntry.center());
  utils.shortWait();
  backCnt++;

  let doubleSign = text("领京豆").findOne(1000);
  if (!doubleSign) {
    console.log("missing double sign entry, skip");
    utils.backN(backCnt);
    return false;
  }
  click(doubleSign.center());
  utils.shortWait();
  backCnt++;

  let claimBtn = text("点击领奖").findOne(1000);
  if (!claimBtn) {
    console.log("missing claim button, skip");
    utils.backN(backCnt);
    return false;
  }
  click(claimBtn.center());
  utils.shortWait();

  utils.backN(backCnt);
  return true;
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
