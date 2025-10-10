const { longWait, shortWait, mediumWait, backN } = require("./utils");

function run() {
  app.launchApp("中国移动");
  longWait();

  panda();

  back();
  backN(1);
}

function panda() {
  let backCnt = 0;
  let entry = text("熊猫乐园").findOne(1000);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  mediumWait();

  // click(300, 300);
  longWait();
  longWait();
  longWait();
  console.log("start task...");

  backCnt += 2;

  click(100, 2200);
  shortWait();

  for (var i = 0; i < 12; i++) {
    sleep(4000);
    click(920, 1950);
    sleep(12000);
    back();
  }

  backN(backCnt);
}

module.exports = {
  run,
};
