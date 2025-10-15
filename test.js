// let obj = id("e_z").findOne(1000);
// console.log(obj);

// let obj = depth(25).childCount(1).indexInParent(2).findOne(500);
// console.log(obj.parent());

let container = id("super_star_collectible_card_feeds").findOne(1000);
for (let idx = 0; idx < container.childCount(); idx++) {
  let child = container.children()[idx];
  console.log(child.center(), child.clickable());
}

// let list = depth(25).childCount(1).find(500);

// for (let idx = 0; idx < list.length; idx++) {
//   let e = list[idx];
//   console.log(e.center());
// }
// daydayclaim();
// function daydayclaim() {
//   let btn = text("图片").findOne(1000);
//   if (!btn) {
//     console.log("missing target,skip");
//     return false;
//   }
//   scrollDown();
//   sleep(1000);
//   scrollDown();
//   sleep(1000);

//   let num = 6;
//   let cnt = 0;
//   let goods = depth(19).find(1000);
//   for (let idx = 0; idx < goods.length; idx++) {
//     let e = goods[idx];
//     if (e.center().y > 330) {
//       click(e.children()[0].center());
//       sleep(8000);
//       back();
//       back();
//       sleep(1000);
//       cnt++;
//     }
//     if (cnt >= num) {
//       break;
//     }
//   }
//   click(btn.center())
//   return true;
// }
