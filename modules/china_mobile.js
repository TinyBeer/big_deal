const {
  longWait,
  shortWait,
  mediumWait,
  backN,
  doubleBackN,
} = require("./utils");

function run() {
  app.launchApp("中国移动");
  longWait();

  panda();

  back();
  backN(1);
}

function panda() {
  let resultList = null;
  let backCnt = 0;
  let entry = text("熊猫乐园").findOne(1000);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }

  click(entry.center());
  mediumWait();
  // click(972, 2270);
  // mediumWait();

  // entry = id("float_window_img_bottom").findOne(1000);
  // if (!entry) {
  //   console.log("missing entry, skip");
  //   return false;
  // }
  // click(entry.center());
  // mediumWait();

  longWait();
  longWait();
  longWait();

  console.log("start task...");
  backCnt += 2;

  click(100, 2200);
  shortWait();

  let find = true;
  while (find) {
    find = false;
    resultList = ocr.rapid.detect([800, 1700, 280, 500]);
    for (let index = resultList.length - 1; index >= 0; index--) {
      let et = resultList[index];
      let bs = et.bounds;
      let x = (bs.left + bs.right) / 2;
      let y = (bs.top + bs.bottom) / 2;
      if (et.label.includes("去浏览")) {
        console.log(et);
        find = true;
        click(x, y);
        longWait();
        mediumWait();
        backN(1);
        break;
      }
    }
  }

  doubleBackN(backCnt);
}

module.exports = {
  run,
};
