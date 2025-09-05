/* import */
const jutils = require("./utils");

/* config */
const objList = [
  // round one
  { name: "雀神来也", dur_m: 60 },
  { name: "货柜趣消除", dur_m: 35 },
  { name: "趣味叠叠乐", dur_m: 15 },
  { name: "排队上车", dur_m: 15 },
  { name: "方块拼图", dur_m: 15 },
  { name: "养猪猪", dur_m: 4 },
  { name: "京豆捕鱼", dur_m: 8 },
  { name: "种菜领现金", dur_m: 0 },
  { name: "消灭小萌星", dur_m: 30 },
  { name: "麻将凑十", dur_m: 15 },
  { name: "解压硬币", dur_m: 15 },
  { name: "2048方块", dur_m: 60 },
  { name: "无尽战歌", dur_m: 15 },
  // round two
  { name: "雀神来也", dur_m: 2 },
  { name: "货柜趣消除", dur_m: 2 },
  { name: "趣味叠叠乐", dur_m: 2 },
  { name: "排队上车", dur_m: 2 },
  { name: "方块拼图", dur_m: 2 },
  { name: "养猪猪", dur_m: 5 },
  { name: "京豆捕鱼", dur_m: 0 },
  { name: "种菜领现金", dur_m: 0 },
  { name: "消灭小萌星", dur_m: 2 },
  { name: "麻将凑十", dur_m: 2 },
  { name: "解压硬币", dur_m: 2 },
  { name: "2048方块", dur_m: 2 },
  { name: "无尽战歌", dur_m: 15 },
  { name: "养猪猪", dur_m: 2 },

  { scroll: true },
  // round one
  { name: "毛线大师", dur_m: 15 }, //
  { name: "点点2048", dur_m: 15 },
  { name: "合成原始人", dur_m: 15 },
  { name: "无尽泡泡龙", dur_m: 15 },
  { name: "打螺丝王者", dur_m: 15 },
  { name: "数字喜加1", dur_m: 15 },
  { name: "纸牌接龙", dur_m: 15 },
  { name: "喵喵十消", dur_m: 15 },
  { name: "超级连连看", dur_m: 15 },
  // round two
  { name: "毛线大师", dur_m: 2 }, //
  { name: "点点2048", dur_m: 1 },
  { name: "合成原始人", dur_m: 1 },
  { name: "无尽泡泡龙", dur_m: 1 },
  { name: "打螺丝王者", dur_m: 1 },
  { name: "数字喜加1", dur_m: 1 },
  { name: "纸牌接龙", dur_m: 1 },
  { name: "喵喵十消", dur_m: 1 },
  // { name: "超级连连看", dur_m: 1 },
];

function run() {
  // launch app
  app.launchApp("京东金融");
  sleep(5000);

  // enter interactive games
  enterInteractiveGames();

  // workWithPos();
  workWithName();

  back();
  sleep(2000);
  back();
  sleep(2000);
}

function workWithName() {
  var scorlled = false;
  for (let i = 0; i < objList.length; i++) {
    let e = objList[i];
    if (e.scroll) {
      scrollDown();
      sleep(1000);
      scrollDown();
      sleep(1000);
      scorlled = true;
      continue;
    }

    console.log(`play [${e.name}] ${e.dur_m} minute`);
    var dur = e.dur_m * 60 * 1000;
    if (dur == 0) {
      console.log("task time == " + dur + " skip task");
      continue;
    }
    let tmp = text(e.name).findOne(1000);
    if (!tmp) {
      console.log(`cant not found [${e.name}], skip`);
      continue;
    }
    let obj = tmp.parent();
    console.log(` get [${e.name}] pos[${obj.center()}]`);
    for (; dur > 0; ) {
      var t = 8 * 60 * 1000;
      if (dur <= t) {
        t = dur;
        dur = 0;
      } else {
        dur = dur - t;
      }

      console.log(`act play [${e.name}] ${t / 60 / 1000}min`);
      click(obj.center());
      jutils.preciseSleep(t, false);
      back();
      back();
      sleep(2000);

      if (!open_box(scorlled)) {
        console.log("open box failed, break");
        break;
      }
    }
  }
}

/* enter interactive games */
function enterInteractiveGames() {
  let interactiveGame = text("互动游戏").findOne(1000);
  let sign = text("签到").findOne(1000);
  let taskCenter = text("任务中心").findOne(1000);

  if (!interactiveGame && sign && !taskCenter) {
    // home page
    click(900, 2250);
    sleep(2000);
    let enter = text("互动游戏").findOne(1000);
    if (!enter) {
      return false;
    }
    click(enter.center());
    sleep(5000);
  } else if (interactiveGame && !sign && !taskCenter) {
    click(interactiveGame.center());
    sleep(5000);
  }

  let pean = textContains("京豆+").findOne(3000);
  if (pean) {
    // first enter
    click(400, 1300);
    sleep(2000);
  }
}

function open_box(scrolld) {
  if (scrolld) {
    scrollUp();
    sleep(1000);
    scrollUp();
    sleep(1000);
  }
  let box = textContains("个盲盒待开").findOne(1000);
  if (!box) {
    if (scrolld) {
      scrollDown();
      sleep(1000);
      scrollDown();
      sleep(1000);
    }
    return true;
  }
  console.log(box.text());

  click(box.center());
  sleep(2000);

  while (true) {
    let open = text("一键开启").findOne(1000);
    if (!open) {
      break;
    }
    click(open.center());
    sleep(5000);

    let pean = textContains("京豆+").findOne(3000);
    if (!pean) {
      return false;
    }
    click(450, 1500);
    sleep(2000);
  }

  if (scrolld) {
    scrollDown();
    sleep(1000);
    scrollDown();
    sleep(1000);
  }
  return true;
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
