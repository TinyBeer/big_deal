/* import */

const {
  backN,
  shortWait,
  longWait,
  mediumWait,
  isPointInBounds,
  doubleBackN,
  miniWait,
} = require("./utils");

/* conf data */

function run() {
  /* launch app */
  app.launchApp("京东");
  longWait();

  /* run task */
  hardwar_city();
  ecard();

  backN(2);
  doubleBackN(1);
}

/* tasks */
function ecard() {
  console.log("京东E卡 ...");
  let backCnt = 0;
  search("京东礼品卡", 8000);
  backCnt += 3;

  let entry = text("持卡特权").findOne(1000);
  if (!entry) {
    console.log("missing entry, skip");
    backN(backCnt);
    return false;
  }
  click(entry.center());
  mediumWait();
  backCnt++;

  let obj = textMatches("天天抢\\d+京豆").findOne(1000);
  if (!obj) {
    console.log("missing claim button, skip");
    backN(backCnt);
    return false;
  }
  let par = obj.parent();
  for (let idx = 0; idx < par.childCount(); idx++) {
    let child = par.children()[idx];
    if (child.text() === "已领取") {
      console.log("already calimed, back");
      backN(backCnt);
      return false;
    } else if (child.text() === "去领取") {
      click(child.center());
      sleep(2000);
      backN(backCnt);
      return true;
    }
  }
  console.log("missing claim button, skip");
  backN(backCnt);
  return false;
}

function hardwar_city() {
  console.log("五金城");
  let backCnt = 0;
  search("五金城", 8000);
  backCnt += 3;

  let entry = text("进入").findOne(1000);
  if (!entry) {
    console.log("missing entry, skip");
    backN(backCnt);
    return false;
  }

  click(entry.center());
  backCnt++;
  sleep(8000);

  click(944, 2288);
  backCnt++;
  sleep(8000);

  let claimBtn = text("签到领京豆").findOne(1000);
  if (!claimBtn) {
    console.log("already claimed, skip");
    backN(backCnt);
    return false;
  }

  click(claimBtn.center());
  shortWait();

  backN(backCnt);
  return true;
}

function search(content, waitTime) {
  let searchBar = desc("搜索栏").findOne(1000);
  if (!searchBar) {
    console.log("missing search bar, skip");
    return false;
  }
  searchBar.click();
  sleep(500);
  setText(content);
  sleep(500);

  let searchBtn = text("搜索").findOne(1000);
  if (!searchBtn) {
    console.log("missing search button, skip");
    back();
    sleep(2000);
    return false;
  }

  searchBtn.click();
  sleep(waitTime);
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
