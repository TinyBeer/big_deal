let enter = className("android.widget.ImageView")
  .depth(20)
  .indexInParent(0)
  .findOne();

console.log(enter);

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
