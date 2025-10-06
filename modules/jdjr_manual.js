/* import */
const utils = require("./utils");

function run(screen) {
  // launch app
  app.launchApp("京东金融");
  utils.longWait();

  double_sign();
  claim_pea();
  save_more();

  utils.backN(2);
  back();
  utils.backN(1);
}

function claim_pea() {
  console.log("京东金融 赚钱更多京豆 ...");
  let backCnt = 0;
  let signEntry = text("签到").findOne(1000);
  if (!signEntry) {
    console.log("missing sign entry, skip");
    return false;
  }

  click(signEntry.center());
  utils.shortWait();
  backCnt++;

  let saveMore = textMatches("领\\d+京豆").findOne(1000);
  if (!saveMore) {
    console.log("missing entery, skip");
    utils.backN(backCnt);
    return false;
  }
  click(saveMore.center());
  backCnt++;
  utils.mediumWait();

  let oneKeyClaim = text("一键领京豆").findOne(1000);
  if (oneKeyClaim) {
    console.log("一键领京豆 ...");
    click(oneKeyClaim.center());
    utils.mediumWait();
  }

  utils.backN(backCnt);
  return true;
}

function save_more() {
  console.log("京东金融 赚钱更多京豆 ...");
  let backCnt = 0;
  let signEntry = text("签到").findOne(1000);
  if (!signEntry) {
    console.log("missing sign entry, skip");
    return false;
  }

  click(signEntry.center());
  utils.shortWait();
  backCnt++;

  let saveMore = text("每日省更多").findOne(1000);
  if (saveMore) {
    backCnt++;
    click(saveMore.center());
    utils.mediumWait();
  }

  utils.backN(backCnt);
}

function double_sign() {
  console.log("京东金融 双签 ...");
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

  let claimed = text("查看奖励").findOne(1000);
  if (claimed) {
    console.log("already claimed, skip");
    utils.backN(backCnt);
    return false;
  }

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
