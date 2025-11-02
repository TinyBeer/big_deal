/* import */

const { doubleBackN, mediumWait, longWait } = require("./utils");

function run() {
  /* launch app */
  app.launchApp("京东");
  longWait();

  /* run task */
  blind_box();
  doubleBackN(1);
}

/* tasks */
function blind_box() {
  console.log("抽盲盒");

  switchTag("新品");

  let newGoodsShop = id("ea2").text("新奇集市").findOne(1000);
  if (!newGoodsShop) {
    console.log("missing 新奇集市 entry, skip");
    switchTag("首页");
    return false;
  }

  click(newGoodsShop.center());
  mediumWait();

  let entry = id("novelBlindBoxEntry").findOne(1000);
  if (!entry) {
    console.log("missing 盲盒 entry, skip");
    switchTag("首页");
    return;
  }

  let taskPage = null;
  for (let i = 0; i < 3; i++) {
    click(entry.center());
    sleep(4000);
    taskPage = className("android.view.View")
      .textContains("抽盲盒机会")
      .depth(29)
      .findOne(1000);
    if (taskPage) {
      break;
    }
    click(1031, 1091);
    sleep(1000);
  }
  if (!taskPage) {
    console.log("missing taskpage skip");
    switchTag("首页");
    return false;
  }

  while (taskPage) {
    var arr = taskPage.text().split(" ");
    if (arr.length > 4) {
      console.log(arr[0], arr[1], arr[2], arr[3]);

      if (arr[3] === "去逛逛") {
        console.log("goto ");
        click(880, 1540);
        if (arr[0] === "逛逛精选新奇好物 ") {
          blineBoxSleep(30)
        } else if (arr[0] === "逛逛新奇好物" || arr[0] === "逛逛指数频道") {
          blineBoxSleep(25)
        } else {
          blineBoxSleep(18)
        }
        if (arr[0] === "逛逛买药频道") {
          click(540, 1897.5);
          sleep(1000);
        }
        doubleBackN(1);
      } else if (arr[3] === "拆盲盒") {
        console.log("claim...");
        click(880, 1540);
        sleep(7000);
      } else if (arr[3] === "去完成") {
        click(880, 1540);
        sleep(26000);
        click(entry.center());
        sleep(4000);
      } else {
        console.log("mission complete, back");
        break;
      }
    }
    taskPage = className("android.view.View")
      .textContains("抽盲盒机会")
      .depth(29)
      .findOne(1000);
  }

  click(1031, 1091);
  sleep(1000);
  back();
  sleep(1000);
  switchTag("首页");
}

function blineBoxSleep(seconds) {
  for (let sec = 0; sec < seconds; sec++) {
    sleep(1000);
    let fin = text("点击立即返回").findOne(100);
    if (fin) {
      break;
    }
  }
  return;
}

function switchTag(name) {
  let tag = className("android.widget.TextView")
    .depth(12)
    .text(name)
    .findOne(1000);
  if (!tag) {
    return false;
  }

  click(tag.center());
  sleep(5000);
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
