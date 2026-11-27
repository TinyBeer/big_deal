const { backHomePage, homePageGetEnter } = require("./jd_utils");
const { longWait, shortWait, doubleBackN } = require("./utils");
const pealog = require("./lib/logger");

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
      pealog.debug("领取京豆 ...");
      click(400, claimBtn.center().y);
      shortWait();
      return true;
    }
    pealog.debug("未找到领京豆入口，跳过");

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
          pealog.debug("任务: " + name + " " + desc + " " + act);
          if (act === "去完成") {
            pealog.debug("前往任务 ...");
            click(880, 1380);
            sleep(7000);
            back();
            sleep(4000);
          } else if (act === "去领取") {
            click(880, 1380);
            sleep(5000);
          } else {
            pealog.debug("任务完成，返回");
            break;
          }
        }
        task = task = textContains("浏览5s").findOne(100);
      }
    }
    pealog.debug("任务流程结束");
  };
  claim121();

  backHomePage(backCnt);
  return true;
}

// 导出函数（供其他脚本调用）
module.exports = {
  run,
};
