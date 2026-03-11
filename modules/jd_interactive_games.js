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
  interactive_game(screen);

  doubleBackN(1);
}

/* tasks */

function interactive_game(screen) {
  console.log("互动游戏...");

  let backCnt = 0;
  let enter = text("我的").findOne(1000);
  if (!enter) {
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

  view_task();
}

const task_tag = "浏览10s";

function view_task() {
  let singleBackTasks = [
    "种豆得豆",
    "东东农场",
    "赚红包",
    "欢乐挖宝",
    "单单反",
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
    longWait();
    longWait();
    mediumWait();
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

function getViewTaskName(obj) {
  if (!obj) {
    return;
  }

  if (obj.text().length != 0 && obj.text() !== txt) {
    return obj;
  }

  for (let idx = 0; idx < obj.children().length; idx++) {
    let child = obj.children()[idx];
    if (child.text() !== "" && child.text() !== task_tag) {
      return child.text();
    }
  }

  return;
}

function getOneViewTask() {
  let obj = text(task_tag).findOne(500);
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
