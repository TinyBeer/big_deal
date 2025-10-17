/* import */

const { longWait, doubleBackN, shortWait, miniWait } = require("./utils");

function run() {
  let screen = utils.getScreenSize();
  /* launch app */
  app.launchApp("京东");
  longWait();

  /* run task */
  interactive_game(screen);

  doubleBackN(1);
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

  while (true) {
    let games = textContains("秒(0/1)").find(200);
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
    sleep(65000);
    doubleBackN(1);
    return;
  }
  // 递归遍历子节点
  var childCount = view.getChildCount();
  for (var i = 0; i < childCount; i++) {
    playGameTraverse(name, view.children()[i], depth + 1);
  }
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
