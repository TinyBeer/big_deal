console.log(find_entery("浏览看病买药频道"));


// let list = text("去抽奖").find(1000);
// for (let idx = 0; idx < list.length; idx++) {
//   let element = list[idx];
//   if (isPointInBounds(element.center(), [0, 456, 1080, 2218])) {
//     click(element.center());
//     sleep(3000);
//     click(1031, 886);
//     sleep(1000);
//   }
// }

// function isPointInBounds(point, bounds) {
//   return (
//     point.x > bounds[0] &&
//     point.x < bounds[2] &&
//     point.y > bounds[1] &&
//     point.y < bounds[3]
//   );
// }

// let loopCnt = 2;
// for (let i = 0; i < loopCnt; i++) {
//   jd_star_scroll(true);
//   let drawBtnList = text("去抽奖").find(1000);
//   for (let index = 0; index < drawBtnList.length; index++) {
//     let drawBtn = drawBtnList[index];
//     if (!isInScreen([0,456,1080,2218], drawBtn.center())) {
//       continue;
//     }
//     click(drawBtn.center());
//     sleep(2000);

//     let close = depth(28).indexInParent(3).findOne(1000);
//     if (!close) {
//       break;
//     }
//     click(close.center());
//     sleep(1000);
//   }
// }

// for (let i = 0; i < loopCnt; i++) {
//   jd_star_scroll(false);
// }

// function jd_star_scroll(up) {
//   let x = 500;
//   let sy = 2000;
//   let ey = 1000;
//   let dur = 500;
//   if (up) {
//     swipe(x, sy, x, ey, dur);
//   } else {
//     swipe(x, ey, x, sy, dur);
//   }
// }

// function isInBounds(bounds, point) {
//   if (
//     point.x > 0 &&
//     point.x < screen.width &&
//     point.y > 0 &&
//     point.y < screen.height
//   ) {
//     return true;
//   }
//   return false;
// }
