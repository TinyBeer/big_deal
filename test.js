auto();
const utils = require("./utils");
const screenSize = utils.getScreenSize();
// let str =
//   "逛逛中秋会场 逛逛中秋会场得抽盲盒机会 限1次(0/1) 去逛逛 种草新奇耳机 种草新奇耳机得抽盲盒机会 限3次(0/3) 去逛逛 种草迪士尼新奇月饼 种草迪士尼月饼得抽盲盒机会 限1次(0/1) 去逛逛 逛逛美心月饼 逛逛美心月饼得抽盲盒机会 限1次(0/1) 去逛逛";

blind_box();

function blind_box() {
  console.log("抽盲盒");

  switchTag("新品");

  let newGoodsShop = id("ea2").text("新奇集市").findOne(1000);
  if (!newGoodsShop) {
    console.log("missing 新奇集市 entry, skip");
    switchTag("首页");
    return false;
  }

  click(newGoodsShop.center());
  sleep(4000);

  let entry = id("novelBlindBoxEntry").findOne(1000);
  if (!entry) {
    console.log("missing 盲盒 entry, skip");
    switchTag("首页");
    return;
  }

  let taskPage = null;
  for (let i = 0; i < 2; i++) {
    click(entry.center());
    sleep(4000);
    taskPage = className("android.view.View")
      .textContains("抽盲盒机会")
      .depth(29)
      .findOne(1000);
    if (taskPage) {
      break;
    }
    click(1031, 1091);
    sleep(1000);
  }
  if (!taskPage) {
    console.log("missing taskpage skip");
    switchTag("首页");
    return false;
  }

  while (taskPage) {
    var arr = taskPage.text().split(" ");
    if (arr.length > 4) {
      console.log(arr[0], arr[1], arr[2], arr[3]);

      if (arr[3] === "去逛逛") {
        console.log("goto ");
        click(880, 1540);
        if (arr[0] === "逛逛新奇好物" || arr[0] === "逛逛指数频道") {
          sleep(25000);
        } else {
          sleep(6000);
        }
        back();
        sleep(4000);
      } else if (arr[3] === "拆盲盒") {
        console.log("claim...");
        click(880, 1540);
        sleep(7000);
      } else if (arr[3] === "去完成") {
        click(880, 1540);
        sleep(26000);
        click(entry.center());
        sleep(4000);
      } else {
        console.log("mission complete, back");
        break;
      }
    }
    taskPage = className("android.view.View")
      .textContains("抽盲盒机会")
      .depth(29)
      .findOne(1000);
  }

  click(1031, 1091);
  sleep(1000);
  switchTag("首页");
}

function switchTag(name) {
  let tag = className("android.widget.TextView")
    .depth(12)
    .text(name)
    .findOne(1000);
  if (!tag) {
    return false;
  }

  click(tag.center());
  sleep(5000);
}
