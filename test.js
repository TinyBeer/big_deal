let obj = textContains("鲜花消消").findOne(100)
console.log(obj);


// console.log(findHotGames());

function findHotGames() {
  let names = [];
  let obj = text("热门游戏").findOne(500);
  if (obj) {
    findText(obj.parent(), 0, function (e) {
      if (isPlusNumText(e)) {
        findText(e.parent(), 0, function (em) {
          if (!isPlusNumText(em) && em.text() != "去玩") {
            names.push(em.text());
          }
        });
      }
    });
  }
  return names;
}

function isPlusNumText(str) {
  let reg = /\+\d+/;
  return reg.test(str);
}

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

function findText(root, depth, f) {
  for (let index = 0; index < root.children().length; index++) {
    let element = root.children()[index];
    if (element.text() !== "") {
      // console.log(element.text(), depth);
      if (f) {
        f(element);
      }
    }
    findText(element, depth + 1, f);
  }
}
