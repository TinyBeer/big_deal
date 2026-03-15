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

  let entry = id("novelBlindBoxEntry").findOne(200);
  if (!entry) {
    console.log("missing 盲盒 entry, skip");
    switchTag("首页");
    return;
  }

  let taskInfo = null;
  for (let i = 0; i < 3; i++) {
    click(entry.center());
    sleep(4000);
    taskInfo = get_jdblindboxtask();
    if (taskInfo) {
      break;
    }
    click(1021, 989.5);
    sleep(1000);
  }
  if (!taskInfo) {
    console.log("missing taskpage skip");
    switchTag("首页");
    return false;
  }

  while (taskInfo) {
    console.log(`find bline box task: ${taskInfo.name}`);
    if (taskInfo.btnName === "去逛逛") {
      console.log("goto ");
      click(taskInfo.entry);
      blineBoxSleep(15);
      doubleBackN(3, function () {
        return id("novelBlindBoxEntry").findOne(1000);
      });
    } else if (taskInfo.btnName === "拆盲盒") {
      console.log("claim...");
      click(taskInfo.entry);
      sleep(7000);
    } else {
      console.log("mission complete, back");
      break;
    }
    taskInfo = get_jdblindboxtask();
  }

  click(1031, 1091);
  sleep(1000);
  back();
  sleep(1000);
  switchTag("首页");
}

function blineBoxGetTask() {
  return className("android.view.View")
    .textContains("抽盲盒机会")
    .findOne(100);
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


function get_jdblindboxtask() {
  let btn = textMatch("(去逛逛|拆盲盒)").findOne(200)
  if (!btn) {
    return
  }

  let taskName = btn.parent().parent().children()[1].text()
  return {
    name: taskName,
    btnName: btn.text(),
    entry: btn.center(),
  }
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
