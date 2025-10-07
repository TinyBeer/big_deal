ocr.mode = "paddle"; /* 切换到 Paddle 工作模式. */
// let resultList = ocr.detect([0, 1140, 1080, 1080]);
// console.log(resultList);
let resultList = null;
let loopCnt = 3;
for (let i = 0; i < loopCnt; i++) {
  jd_star_scroll(true);
  let drawBtnList = getDrawButtons();
  for (let idx = 0; idx < drawBtnList.length; idx++) {
    let btn = drawBtnList[idx];
    click(btn.center());
    sleep(2000);

    resultList = ocr.detect([0, 1140, 1080, 1080]);
    for (let index = resultList.length - 1; index >= 0; index--) {
      let et = resultList[index];
      let bs = et.bounds;
      let x = (bs.left + bs.right) / 2;
      let y = (bs.top + bs.bottom) / 2;
      if (et.label === "逛一逛") {
        click(x, y);
        sleep(15000);
        backN();
        sleep(2000);
      } else if (et.label === "去抽奖") {
        click(x, y);
        sleep(4000);
      }
    }

    click(1031, 886);
    sleep(2000);
  }
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
  sleep(2000);
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

function isPointInBounds(point, bounds) {
  return (
    point.x > bounds[0] &&
    point.x < bounds[2] &&
    point.y > bounds[1] &&
    point.y < bounds[3]
  );
}
