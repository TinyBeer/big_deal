/* import */
// const utils = require("./utils");

/* conif data */

function miniWait() {
  sleep(500);
}

function shortWait() {
  sleep(3000);
}

function mediumWait() {
  sleep(5000);
}

function longWait() {
  sleep(8000);
}

function run(screen) {
  /* launch app */
  app.launchApp("京东");
  longWait();

  interactive_game(screen);
  /* run task */
  blind_box();
  blind_box();
  blind_box();
}

/* tasks */


function interactive_game(screen) {
  console.log("互动游戏...");

  let backCnt = 0;
  let enter = text("我的").findOne(1000);
  if (!enter) {
    return false;
  }
  click(enter.center());
  shortWait();
  backCnt++;

  let gameEnter = text("互动游戏").findOne(1000);
  if (!gameEnter) {
    backN(backCnt);
    return false;
  }
  click(gameEnter.center());
  longWait();
  backCnt++;

  scrollDown();
  shortWait();

  let moreEnter = text("玩更多").findOne(1000);
  if (!moreEnter) {
    backN(backCnt);
    return false;
  }
  click(moreEnter.center());
  longWait();
  backCnt++;

  // let moreReward = text("玩游戏领京豆").findOne(1000);
  // if (!moreReward) {
  //   backN(backCnt);
  //   return false;
  // }
  // click(900, moreReward.center().y);
  // longWait();

  while (true) {
    let games = textContains("秒(0/1)").find(1000);
    if (!games || games.length === 0) {
      break;
    }
    for (let i = 0; i < games.length; i++) {
      let game = games[i];
      if (game.center().x < 0 || game.center().x > screen.width) {
        continue;
      }
      console.log(`find game[${game.text()}] pos[${game.center()}] act`);
      playGameTraverse(game.text(), game.parent(), 0);
    }
    miniWait();
  }

  backN(backCnt);
}



function playGameTraverse(name, view, depth) {
  if (!view) return;
  //   var indent = "  ".repeat(depth);
  //   log(indent + "类名: " + view.getClassName());
  //   log(indent + "ID: " + view.id());
  //   log(indent + "文本: " + view.getText());
  //   log(indent + "-------------------");
  if (view.text() === "领奖励") {
    console.log(name, "领奖励", view.center());
    click(866, view.center().y);
    shortWait();
    return;
  } else if (view.text() == "去完成") {
    console.log(name, "去完成 60 s", view.center());
    click(866, view.center().y);
    sleep(63000);
    back();
    back();
    shortWait();
    return;
  }
  // 递归遍历子节点
  var childCount = view.getChildCount();
  for (var i = 0; i < childCount; i++) {
    playGameTraverse(name, view.children()[i], depth + 1);
  }
}


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
        } else if (arr[0] === "逛逛权益中心") {
          sleep(15000);
        } else {
          sleep(10000);
        }
        if (arr[0] === "逛逛买药频道") {
          back();
          sleep(1000);
        }
        back();
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
  back();
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

function backN(cnt) {
  for (let i = 0; i < cnt; i++) {
    back();
    shortWait();
  }
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
