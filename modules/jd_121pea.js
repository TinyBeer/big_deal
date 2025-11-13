const { backHomePage, homePageGetEnter } = require("./jd_utils");
const { longWait, shortWait, doubleBackN } = require("./utils");

function run() {
  /* launch app */
  app.launchApp("京东");
  longWait();

  /* run task */
  _121pean();

  doubleBackN(1);
}

function _121pean() {
  let backCnt = 0;
  let enter = homePageGetEnter("京喜自营");
  if (!enter) {
    return false;
  }
  backCnt++;
  click(enter.center());
  longWait();
  longWait();

  let claimPean = function () {
    let claimBtn = className("android.view.View")
      .textContains("领京豆")
      .findOne(500);
    if (claimBtn) {
      console.log("claim pean ...", claimBtn.center());
      click(400, claimBtn.center().y);
      shortWait();
      return true;
    }
    console.log("missing claim button, skip");

    return false;
  };

  claimPean();

  let claim121 = function () {
    let obj = textContains("领121京豆").findOne(100);
    if (obj) {
      click(400, obj.center().y);
      sleep(3000);
      let task = textContains("浏览5s").findOne(100);
      while (task) {
        var arr = task.text().split("浏览5s可领");
        if (arr.length >= 2) {
          let arr2 = arr[1].split(" ")
          if (arr2.length >= 3) {
          }
          let name = arr[5];
          let desc = arr[7];
          let act = arr[9];
          console.log(name, desc, act);
          if (act === "去完成") {
            console.log("goto ");
            click(880, 1380);
            sleep(7000);
            back();
            sleep(4000);
          } else if (act === "去领取") {
            click(880, 1380);
            sleep(5000);
          } else {
            console.log("mission complete, back");
            break;
          }
        }
        task = task = textContains("浏览5s").findOne(100);
      }
    }
    console.log("mission complete, back");
  };
  // claim121();

  backHomePage(backCnt);
  return true;
}

// 导出函数（供其他脚本调用）
module.exports = {
  run,
};
