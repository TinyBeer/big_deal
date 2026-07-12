/* import */

const {
  longWait,
  doubleBackN,
  shortWait,
  miniWait,
  getScreenSize,
  backN,
  mediumWait,
} = require("./utils");

function run() {
  let screen = getScreenSize();
  /* launch app */
  app.launchApp("京东");
  longWait();

  /* run task */
  interactiveGame(screen);

  doubleBackN(1);
}

/* tasks */

function interactiveGame(screen) {
  console.log("互动游戏...");

  let backCnt = 0;
  let enter = desc("我的").findOne(1000);
  if (!enter) {
    console.log("missinge entry");
    return false;
  }
  click(enter.center());
  shortWait();
  backCnt++;

  let gameEnter = text("互动游戏").findOne(1000);
  if (!gameEnter) {
    backN(backCnt);
    return false;
  }
  click(gameEnter.center());
  longWait();
  backCnt++;

  viewTask();
}

const taskTag = "浏览10s";

function viewTask() {
  let singleBackTasks = [
    "种豆得豆",
    "东东农场",
    "赚红包",
    "欢乐挖宝",
    "单单反",
    "京东小游戏",
  ];

  while (hasViewTasks()) {
    let task = getOneViewTask();
    if (!task) {
      console.log("no task found!!!");
      break;
    }
    let taskName = getViewTaskName(task);
    let doubleBack = true;
    for (let idx = 0; idx < singleBackTasks.length; idx++) {
      let name = singleBackTasks[idx];
      if (name === taskName) {
        doubleBack = false;
        break;
      }
    }
    console.log(`view task[${taskName}]`);
    click(task.center());

    if (!viewTaskSleep(18)) {
      if (doubleBack) {
        doubleBackN(3, function () {
          return text("热门推荐").findOne(300);
        });
      } else {
        backN(3, function () {
          return text("热门推荐").findOne(300);
        });
      }
      mediumWait();
    }
  }
}

function viewTaskSleep(seconds) {
  for (let sec = 0; sec < seconds; sec++) {
    sleep(1000);
    let fin = text("点击立即返回").findOne(100);
    if (fin) {
      console.log("立即返回");
      click(fin.center());
      shortWait();
      return true;
    }
  }
  return false;
}

function getViewTaskName(obj) {
  if (!obj) {
    return;
  }

  if (obj.text().length != 0 && obj.text() !== txt) {
    return obj;
  }

  for (let idx = 0; idx < obj.children().length; idx++) {
    let child = obj.children()[idx];
    if (child.text() !== "" && child.text() !== taskTag) {
      return child.text();
    }
  }

  return;
}

function getOneViewTask() {
  let obj = text(taskTag).findOne(500);
  return obj.parent();
}

function hasViewTasks() {
  let obj = textMatch("再完成\\d+个任务").findOne(200);
  if (!obj) {
    console.log("no view task");
    return false;
  }
  return true;
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
