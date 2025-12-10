const {
  longWait,
  backN,
  mediumWait,
  shortWait,
  tinyWait,
  doubleBackN,
  getScreenSize,
} = require("./utils");

let sc = null;

function run(screen) {
  let screen = getScreenSize();
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

  let saveMoreEntry = text("每日省更多").findOne(1000);
  if (!saveMoreEntry) {
    console.log("missing save more entery, skip...");
    backN(backCnt);
    return false;
  }

  backCnt++;
  click(saveMoreEntry.center());
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
    { name: "逛京东秒杀领京豆", jd: true },
    { name: "逛月黑风高频道", jd: true },
    { name: "浏览外卖频道页", jd: false },
    { name: "去玩雀神来也", jd: false, delay: 15 },
    { name: "浏览充值页10秒", jd: false, delay: 15 },
    { name: "浏览外卖频道页", jd: false, delay: 15 },
    { name: "浏览财富会员权益", jd: false, delay: 15 },
    { name: "浏览视频30秒", jd: false, delay: 35 },
    { name: "浏览看病买药频道", jd: true },
    { name: "逛双11大促活动", jd: false },
    { name: "领10元外卖券", jd: false, delay: 15 },
    { name: "浏览签到领金币" },
    { name: "浏览少数派夺京豆", delay: 15 },
    { name: "浏览集5鹅10秒", delay: 15 },
    { name: "参与白条活动提额" },
    { name: "逛白条频道10秒", delay: 15 },
    { name: "赢2025元红包" },
    { name: "查看国民养老页" },
    { name: "浏览股票学堂", delay: 15 },
    { name: "浏览养大鹅10秒", delay: 15 },
    { name: "百亿补贴抽8元", delay: 15 },
    { name: "9.9频道抽红包"},
    { name: "查看稳稳盈爆品"},
    { name: "京东健康天天得金"},
  ];

  let find = true;
  while (find) {
    find = false;
    let obj = textMatch(".*(\\d/\\d)").findOne(500);
    if (!obj) {
      break;
    }
    console.log("found", obj.text());

    for (let idx = 0; idx < taskList.length; idx++) {
      let task = taskList[idx];
      if (obj.text().includes(task.name)) {
        find = true;
        console.log(task.name, "...");
        let entry = find_entry(task.name);
        click(entry.center());
        shortWait();
        if (task.delay && task.delay !== 0) {
          sleep(task.delay * 1000);
        } else {
          mediumWait();
        }

        doubleBackN(4, function () {
          if (isInSaveMoney()) {
            return true;
          }
          let entry = text("每日省更多").findOne(200);
          if (entry) {
            click(entry.center());
            shortWait();
            return true;
          }
          return false;
        });
        mediumWait();
      }
    }
  }
}

function isInSaveMoney() {
  let earn = text("赚京豆当钱花").findOne(1000);
  let browse = text("浏览App赚豆").findOne(1000);
  if (earn && browse) {
    return true;
  }
  return false;
}

function find_entry(name) {
  let obj = textContains(name).findOne(50);
  if (!obj || !obj.parent() || !obj.parent().parent()) {
    return;
  }
  let root = obj.parent().parent().parent();
  let entry = find_goto_button(root);
  if (
    !entry ||
    entry.center().x < 0 ||
    entry.center().x > sc.width ||
    entry.center().y < 0 ||
    entry.center().y > sc.height
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
