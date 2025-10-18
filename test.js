// let obj = text("合成2048掉落碰撞畅快合成").findOne(500);
// console.log(click(obj.center()));

console.log(isSuperStarPage());

function isSuperStarPage() {
  let star = text("超级明星").findOne(500);
  let container = id("super_star_collectible_card_feeds").findOne(500);

  if (star && container) {
    return true;
  }
  return false;
}
