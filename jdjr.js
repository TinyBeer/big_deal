/* import */
const jutils = require("./utils");

/* config */

let gameTaskList = [];

let hotGameTaskList = [
  // round one
  { name: "雀神来也", dur_m: 60 },
  { name: "货柜趣消除", dur_m: 35 },
  { name: "趣味叠叠乐", dur_m: 15 },
  { name: "排队上车", dur_m: 15 },
  { name: "方块拼图", dur_m: 15 },
  // { name: "养猪猪", dur_m: 4 },
  // { name: "京豆捕鱼", dur_m: 8 },
  // { name: "种菜领现金", dur_m: 0 },
  // { name: "消灭小萌星", dur_m: 30 },
  // { name: "麻将凑十", dur_m: 15 },
  // { name: "解压硬币", dur_m: 15 },
  // { name: "2048方块", dur_m: 60 },
  // { name: "无尽战歌", dur_m: 15 },
  // round two
  { name: "雀神来也", dur_m: 2 },
  { name: "货柜趣消除", dur_m: 2 },
  { name: "趣味叠叠乐", dur_m: 2 },
  { name: "排队上车", dur_m: 2 },
  { name: "方块拼图", dur_m: 2 },
  // { name: "养猪猪", dur_m: 5 },
  // { name: "京豆捕鱼", dur_m: 0 },
  // { name: "种菜领现金", dur_m: 0 },
  // { name: "消灭小萌星", dur_m: 2 },
  // { name: "麻将凑十", dur_m: 2 },
  // { name: "解压硬币", dur_m: 2 },
  // { name: "2048方块", dur_m: 2 },
  // { name: "无尽战歌", dur_m: 15 },
  // { name: "养猪猪", dur_m: 2 },
];

let moreGameTaskList = [
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
  // { name: "超级连连看", dur_m: 15 },
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
  let tasks = getGameTaskList(getGameNameList("精品推荐", true));
  gameTaskList = hotGameTaskList.concat(tasks, moreGameTaskList);
  console.log(gameTaskList);
  // // workWithPos();
  workWithName(gameTaskList);

  back();
  sleep(2000);
  back();
  sleep(2000);
}

function workWithName(objList) {
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

function getGameTaskList(gameNameList) {
  let taskList = [];
  for (let i = 0; i < gameNameList.length; i++) {
    let name = gameNameList[i];
    let game = text(name).findOne(500);
    if (!game) {
      continue;
    }
    click(game.center());
    sleep(8000);
    let taskEnter = textContains("10元还款券").findOne(1000);
    if (!taskEnter) {
      continue;
    }
    click(taskEnter.center());
    sleep(2000);
    let mins = getGameMins();
    for (let j = 0; j < mins.length; j++) {
      let min = mins[j];
      if (j == 0) {
        taskList.push({
          name: name,
          dur_m: min,
        });
      } else {
        taskList.push({
          name: name,
          dur_m: min - mins[j - 1],
        });
      }
    }
    back();
    sleep(1000);
  }
  return taskList;
}

function getGameMins() {
  let obj = textContains("分钟").find(1000);
  let mins = [];
  for (let index = 0; index < obj.length; index++) {
    let element = obj[index];
    let nums = extractNumbersWithDecimal(element.text());
    // console.log(element.text(), nums);

    if (nums.length == 1) {
      mins.push(nums[0]);
    }
  }
  return mins;
}

function extractNumbersWithDecimal(str) {
  var numbers = [];
  var currentNumber = "";
  var hasDecimal = false; // 标记是否已经有小数点

  for (var i = 0; i < str.length; i++) {
    var char = str.charAt(i);
    // 允许数字和一个小数点
    if (!isNaN(char) && char !== " ") {
      currentNumber += char;
    } else if (char === "." && !hasDecimal) {
      currentNumber += char;
      hasDecimal = true;
    } else {
      if (currentNumber !== "") {
        numbers.push(currentNumber);
        currentNumber = "";
        hasDecimal = false;
      }
    }
  }

  if (currentNumber !== "") {
    numbers.push(currentNumber);
  }

  return numbers;
}

function getGameNameList(pivotName, ignorePivot) {
  let pivot = textContains(pivotName).findOne(1000);
  let container = pivot.parent();
  let gameNameList = [];

  traverse(container, function (view) {
    if (
      view.text().length !== 0 &&
      !view.text().includes("q70") &&
      !(view.text() === pivotName && ignorePivot) &&
      view.text() !== "种菜领现金"
    ) {
      gameNameList.push(view.text());
      return;
    }
  });
  return gameNameList;
}

function traverse(view, visit) {
  if (!view) return;
  //   var indent = "  ".repeat(depth);
  //   log(indent + "类名: " + view.getClassName());
  //   log(indent + "ID: " + view.id());
  //   log(indent + "文本: " + view.getText());
  //   log(indent + "-------------------");
  visit(view);
  // 递归遍历子节点
  var childCount = view.getChildCount();
  for (var i = 0; i < childCount; i++) {
    traverse(view.children()[i], visit);
  }
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
