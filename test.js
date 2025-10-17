
console.log(find_entry("浏览财富会员权益"));


function find_entry(name) {
  let obj = textContains(name).findOne(50);
  if (!obj || !obj.parent() || !obj.parent().parent()) {
    return;
  }
  let root = obj.parent().parent().parent();
  let entry = find_goto_button(root);
  // if (
  //   !entry ||
  //   (entry.center().x < 0 ||
  //     entry.center().x > sc.width ||
  //     entry.center().y < 0 ||
  //     entry.center().y > sc.height)
  // ) {
  //   return;
  // }
  return entry;
}

function find_goto_button(parent) {
  for (let idx = 0; idx < parent.children().length; idx++) {
    let child = parent.children()[idx];
    if (child.text() === "去完成" || child.text() == "继续完成") {
      return child;
    }
    if (child.childCount != 0) {
      let ch = find_goto_button(child);
      if (ch) {
        return ch;
      }
    }
  }
  return;
}
// const x = 500;
// const sy = 1000;
// const ey = 300;
// const dur = 300;
// for (let idx = 0; idx < 30; idx++) {
//   // let r = random();
//   // console.log(r);
//   // let flag = r > 0.5;
//   let flag = true;
//   while (flag) {
//     flag = false;
//     swipe(x, sy, x, ey, dur);
//     sleep(2000);
//     let btn = textContains("进入直播间").findOne(500);
//     flag = btn != null;
//   }
//   sleep(10000);
// }
