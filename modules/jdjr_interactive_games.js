/* import */

const {
  longWait,
  backN,
  doubleBackN,
  // getScreenSize,
  preciseSleep,
  shortWait,
} = require("./utils");

const igtasks = [
  { name: "雀神来也", dur_m: 60 },
  { name: "货柜趣消除", dur_m: 15 },
  { name: "趣味叠叠乐", dur_m: 15 },
  { name: "排队上车", dur_m: 15 },
  { name: "方块拼图", dur_m: 15 },
  { name: "养猪猪", dur_m: 7 },
  { name: "京豆捕鱼", dur_m: 7 },
  { name: "财富庄园", dur_m: 7 },
  { name: "消灭小萌星", dur_m: 30 },
  { name: "麻将凑十", dur_m: 15 },
  { name: "解压硬币", dur_m: 15 },
  { name: "2048方块", dur_m: 30 },
  { name: "无尽战歌", dur_m: 15 },

  { scroll: true },
  { name: "百炼飞仙", dur_m: 15 },
  { name: "毛线大师", dur_m: 15 },
  { name: "点点2048", dur_m: 15 },
  { name: "合成原始人", dur_m: 15 },
  { name: "无尽泡泡龙", dur_m: 15 },
  { name: "数字喜加1", dur_m: 15 },
  { name: "战争之王", dur_m: 15 },

  { scroll: true },
  { name: "2048碰碰球", dur_m: 15 },
  { name: "动物排排队", dur_m: 15 },
  { name: "喵喵十消", dur_m: 15 },
  { name: "超级连连看", dur_m: 15 },
];

function run() {
  // let screen = getScreenSize();
  // launch app
  app.launchApp("京东金融");
  longWait();

  // enter interactive games
  enterInteractiveGames();

  workWithName(igtasks);

  backN(2);
  doubleBackN(1);
}

function workWithName(objList) {
  for (let i = 0; i < objList.length; i++) {
    let e = objList[i];
    shortWait();
    if (e.scroll) {
      scrollDown();
      sleep(1000);
      continue;
    }

    console.log(`play [${e.name}] ${e.dur_m} minute`);
    var dur = e.dur_m * 60 * 1000;
    if (dur == 0) {
      console.log("task time == " + dur + " skip task");
      continue;
    }
    let tmp = textContains(e.name).findOne(1000);
    if (!tmp) {
      console.log(`cant not found [${e.name}], skip`);
      continue;
    }

    for (; dur > 0; ) {
      let entry = textContains(e.name).findOne(1000);
      if (!entry) {
        console.log(`cant not found [${e.name}], skip`);
        break;
      }
      let entryPos = entry.parent().center();
      console.log(` get [${e.name}] pos[${entryPos}]`);
      var t = 30 * 60 * 1000;
      if (dur <= t) {
        t = dur;
        dur = 0;
      } else {
        dur = dur - t;
      }
      console.log(`act play [${e.name}] ${t / 60 / 1000}min`);
      click(entryPos);
      preciseSleep(t + 30 * 1000, false);
      back();
      back();
      sleep(2000);
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

    let update = text("立即查看").findOne(1000);
    if (update) {
      backN(1);
    }

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

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
