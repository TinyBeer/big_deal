const { longWait, backN, mediumWait, shortWait, tinyWait } = require("./utils");

let sc = null;

function run(screen) {
  // launch app
  app.launchApp("京东金融");
  longWait();
  sc = screen;
  saveMore();

  backN(2);
  back();
  backN(1);
}

function saveMore() {
  console.log("京东金融 赚钱更多京豆 ...");
  let backCnt = 0;
  let signEntry = text("签到").findOne(1000);
  if (!signEntry) {
    console.log("missing sign entry, skip");
    return false;
  }

  click(signEntry.center());
  shortWait();
  backCnt++;

  let saveMore = text("每日省更多").findOne(1000);
  if (!saveMore) {
    console.log("missing save more entery, skip...");
    backN(backCnt);
    return false;
  }

  backCnt++;
  click(saveMore.center());
  mediumWait();

  goto_tasklist();

  longWait();
  backN(backCnt);
  return true;
}

function goto_tasklist() {
  let taskList = [
    { name: "浏览低价好物", jd: false },
    { name: "浏览热销爆品", jd: false },
    { name: "逛品质低价好物", jd: false },
    { name: "逛每日热销好物", jd: false },
    { name: "逛每日推荐好物", jd: false },
    { name: "逛每日补贴好物", jd: false },
    { name: "去新奇频道领京豆", jd: true },
    { name: "看京东App视频", jd: true },
    { name: "逛月黑风高频道", jd: false },
    { name: "浏览外卖频道页", jd: false },
    { name: "去玩雀神来也", jd: false },
    { name: "浏览充值页10秒", jd: false ,delay:15},
    { name: "浏览外卖频道页", jd: false },
    { name: "浏览财富会员权益", jd: false , delay:15 },
    { name: "浏览视频30秒", jd: false, delay: 35 },
    { name: "浏览看病买药频道", jd: false },
    { name: "看京东App视频", jd: false },
  ];
  let find = true;
  while (find) {
    find = false;
    for (let idx = 0; idx < taskList.length; idx++) {
      let task = taskList[idx];
      let entry = find_entry(task.name);
      if (!entry) {
        continue;
      }
      console.log(task.name, "...");
      find = true;
      click(entry.center());
      shortWait();
      if (task.delay !== 0) {
        sleep(task.delay);
      } else {
        mediumWait();
      }

      if (task.jd) {
        back();
        backN(1);
      }
      back();
      backN(1);
      mediumWait();
    }
  }
}

function find_entry(name) {
  let obj = textContains(name).findOne(200);
  if (!obj || !obj.parent() || !obj.parent().parent()) {
    return;
  }
  let root = obj.parent().parent().parent();
  let entry = find_goto_button(root);
  if (
    entry &&
    (entry.center().x < 0 ||
      entry.center().x > sc.width ||
      entry.center().y < 0 ||
      entry.center().y > sc.height)
  ) {
    return;
  }
  return entry;
}

function find_goto_button(parent) {
  for (let idx = 0; idx < parent.children().length; idx++) {
    let child = parent.children()[idx];
    if (child.text() === "去完成" || child.text() == "继续完成") {
      return child;
    }
    if (child.childCount != 0) {
      let ch = find_goto_button(child);
      if (ch) {
        return ch;
      }
    }
  }
  return;
}

module.exports = {
  run,
};
