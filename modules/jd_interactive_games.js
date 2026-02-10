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

function view_task() {
  let obj = textMatch("再完成\\d个任务").findOne(200);
  if (!obj) {
    console.log("missing view task");
    return;
  }

  for (let idx = 0; idx < 8; idx++) {
    let task = textMatch("浏览10s").findOne(200);
    if (task) {
      click(task.center());
      longWait();
      longWait();
      mediumWait();
      backN(3, function () {
        return text("热门推荐").findOne(300);
      });
      mediumWait();
    }
  }
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
