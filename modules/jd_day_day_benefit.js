/* import */

const {
  doubleBackN,
  longWait,
  mediumWait,
  backN,
  miniWait,
} = require("./utils");

function run() {
  /* launch app */
  app.launchApp("京东");
  longWait();

  /* run task */
  day_day_draw_benefit();

  doubleBackN(1);
}

/* tasks */
let dddbDetectRes = [];
function day_day_draw_benefit() {
  console.log("天天抽福利 ...");
  let entry = text("补贴价").findOne(500);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  longWait();

  click(105, 660);
  mediumWait();

  let x = 500;
  let sy = 2100;
  let ey = 1500;
  let dur = 1000;
  swipe(x, sy, x, ey, dur);
  sleep(500);

  let find = true;
  while (find) {
    find = false;
    dddbDetectRes = ocr.rapid.detect([0, 1024, 1080, 1200]);
    for (let index = 0; index < dddbDetectRes.length; index++) {
      let et = dddbDetectRes[index];
      if (et.label.includes("浏览页面")) {
        console.log(et);
        find = true;
        click(950, et.bounds.top);
        for (let idx = 0; idx < 50; idx++) {
          miniWait();
          if (text("点击立即返回").findOne(100)) {
            break;
          }
        }
        backN(1);
        break;
      }
    }
  }

  console.log("complete, back");
  click(1011, 884);
  sleep(500);
  backN(1);
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
