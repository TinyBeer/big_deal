const { backHomePage, homePageGetEnter } = require("./jd_utils");
const {
  longWait,
  shortWait,
  doubleBackN,
  miniWait,
  mediumWait,
  info,
} = require("./utils");

function run() {
  /* launch app */
  app.launchApp("京东");
  longWait();

  /* run task */
  scratchTask();

  doubleBackN(1);
}

const sx = 800;
const ex = 400;
const dur = 1000;
function scratchTask() {
  console.log("刮卡任务");
  let backCnt = 0;
  let enter = text("我的").findOne(1000);
  if (!enter) {
    return false;
  }
  click(enter.center());
  shortWait();
  backCnt++;

  let peaPage = text("京豆").findOne(200);
  if (!peaPage) {
    console.log("missing 京豆 entry, skip");
    backHomePage(backCnt);
    return false;
  }
  click(peaPage.center());
  longWait();
  backCnt++;

  for (let i = 0; i < 3; i++) {
    let task = getCurScratchCardTask();
    if (
      task &&
      (task.text() === "飞行赢红包领福利" || task.text().includes("6s"))
    ) {
      info(task.text());
      let btn = textContains("做任务解锁刮卡").findOne(100);
      if (btn) {
        click(btn.center());
        shortWait();
        btn = text("立即刮卡").findOne(100);
        if (btn) {
          click(btn.center());
          longWait();
          i--;
          continue;
        }
        longWait();
        i--;
        doubleBackN(2, function () {
          let obj = text("京豆").findOne(100);
          if (obj) {
            return true;
          }
          return false;
        });
        mediumWait();
        continue;
      }
      btn = text("立即刮卡").findOne(100);
      if (btn) {
        click(btn.center());
        longWait();
        i--;
        continue;
      }
    }
    let y = task.center().y;
    swipe(sx, y, ex, y, dur);
    miniWait();
  }
  backHomePage(backCnt);
  return true;
}

function getCurScratchCardTask() {
  let list = depth(21).childCount(0).indexInParent(1).find(200);
  for (let idx = 0; idx < list.length; idx++) {
    let element = list[idx];
    let ex = element.center().x;
    if (ex > 400 && ex < 800 && element.text().includes("刮卡") ) {
      return element;
    }
  }
}

// 导出函数（供其他脚本调用）
module.exports = {
  run,
};
