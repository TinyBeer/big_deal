/* import */

const {
  doubleBackN,
  longWait,
  mediumWait,
  backN,
  miniWait,
  waitForText,
  drag,
  info,
  shortWait,
} = require("./utils");

function run() {
  /* launch app */
  app.launchApp("京东");
  longWait();

  /* run task */
  dayDayDrawBenefit();

  doubleBackN(1);
}

/* tasks */
function dayDayDrawBenefit() {
  console.log("国补任务 ...");
  let entry = text("补贴价").findOne(500);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  longWait();

  let btn = text("手动点击翻转测试").findOne(100);
  if (!btn) {
    console.log("missing entry button, skip");
    backN(1);
    return false;
  }
  click(btn.center());
  mediumWait();

  // 向上滑一屏，让任务列表露出来
  drag({ x: 500, y: 2100 }, { x: 500, y: 1500 }, { duration: 1000, wait: "short" });

  while (true) {
    let order = text("去下单").findOne(100);
    if (order) {
      order
        .parent()
        .children()
        .forEach((element) => {
          if (element.clickable()) {
            element.click();
          }
        });

      shortWait();
      continue;
    }
    let close = text("开心收下").findOne(100);
    if (close) {
      click(close.center());
      shortWait();
      continue;
    }
    let claim = text("领取奖励").findOne(100);
    if (claim) {
      click(claim.center());
      shortWait();
      continue;
    }

    let task = textContains("浏览页面").findOne(100);
    if (!task) {
      backN(1);
      break;
    }
    click(task.center());

    let res = waitForText("点击立即返回", {
      seconds: 18,
      intervalMs: 500,
      click: true,
      afterClick: "short",
      log: "立即返回",
    });
    if (!res) {
      backN(3, function () {
        let kk = text("国家补贴").findOne(100);
        if (kk) {
          return true;
        }
        return false;
      });
      shortWait();
    }
  }

  info("国家补贴任务完成");
  backN(2);
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
