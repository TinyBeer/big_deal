let obj = text("点击立即返回").findOne(100);
console.log(obj);

// let list = text("image").depth(24).indexInParent(1).find(1000);
// let signBtn = null;
// for (let idx = 0; idx < list.length; idx++) {
//   let element = list[idx];
//   if (element.center().x < 100) {
//     signBtn = element;
//     break;
//   }
// }
// console.log(signBtn);
// click(signBtn.center());

// let obj = text("合成2048掉落碰撞畅快合成").findOne(500);
// console.log(click(obj.center()));

// console.log(isSuperStarPage());

// function isSuperStarPage() {
//   let star = text("超级明星").findOne(500);
//   let container = id("super_star_collectible_card_feeds").findOne(500);

//   if (star && container) {
//     return true;
//   }
//   return false;
// }
