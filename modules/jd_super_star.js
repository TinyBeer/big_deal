const {
  switchTag,
  shortWait,
  longWait,
  backN,
  isPointInBounds,
  mediumWait,
  miniWait,
  doubleBackN,
} = require("./utils");

function run(screen) {
  /* launch app */
  app.launchApp("京东");
  longWait();

  console.log("超级明星...");

  switchTag("新品");

  let superStar = id("ea2").text("超级明星").findOne(1000);
  if (!superStar) {
    console.log("missing 超级明星 entry, skip");
    switchTag("首页");
    return false;
  }

  click(superStar.center());
  longWait();

  let resultList = null;
  let drawBtnList = null;
  let btn = null;
  let et = null;
  let loopCnt = 3;
  for (let i = 0; i < loopCnt; i++) {
    jd_star_scroll(true);
    drawBtnList = getDrawButtons();
    for (let idx = 0; idx < drawBtnList.length; idx++) {
      btn = drawBtnList[idx];
      click(btn.center());
      shortWait();
      let find = true;
      while (find) {
        find = false;
        resultList = ocr.rapid.detect([0, 1140, 1080, 1080]);
        for (let index = resultList.length - 1; index >= 0; index--) {
          et = resultList[index];
          let bs = et.bounds;
          let x = (bs.left + bs.right) / 2;
          let y = (bs.top + bs.bottom) / 2;
          if (et.label === "逛一逛") {
            click(x, y);
            longWait();
            mediumWait();
            backN(1);
            find = true;
            break;
          } else if (et.label === "去抽奖") {
            click(x, y);
            shortWait();
            find = true;
            break;
          }
        }
      }

      click(1031, 886);
      miniWait();
    }
  }

  for (let i = 0; i < loopCnt; i++) {
    jd_star_scroll(false);
  }

  switchTag("首页");

  doubleBackN(1);
}

function jd_star_scroll(up) {
  let x = 500;
  let sy = 2000;
  let ey = 1000;
  let dur = 500;
  if (up) {
    swipe(x, sy, x, ey, dur);
  } else {
    swipe(x, ey, x, sy, dur);
  }
  miniWait();
}

function getDrawButtons() {
  let btns = [];
  let list = text("去抽奖").find(1000);
  for (let idx = 0; idx < list.length; idx++) {
    let element = list[idx];
    if (isPointInBounds(element.center(), [0, 456, 1080, 2218])) {
      btns.push(element);
    }
  }
  return btns;
}
//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
