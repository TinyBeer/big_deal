/* import */
const utils = require("./utils");

let gameTaskList = [];

function run(screen, nameList, moreGameTaskList) {
  // launch app
  app.launchApp("京东金融");
  sleep(5000);

  // enter interactive games
  enterInteractiveGames();
  console.log(nameList);
  let tasks = getGameTaskList(nameList);
  gameTaskList = tasks.concat(moreGameTaskList);
  console.log(gameTaskList);

  workWithName(screen, gameTaskList);
  // workWithName(hotGameTaskList);

  utils.backN(2);
  back();
  utils.backN(1);
}

function workWithName(screen, objList) {
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
      utils.preciseSleep(t, false);
      back();
      back();
      sleep(2000);

      if (!open_box(scorlled, screen)) {
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

    let update = text("立即查看").findOne(1000);
    if (update) {
      utils.backN(1);
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

function open_box(scrolld, screen) {
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

  let open = text("一键开启").findOne(1000);
  if (!open) {
    return false;
  }

  click(open.center());
  sleep(5000);
  let pean = textContains("京豆+").findOne(3000);
  if (!pean) {
    return false;
  }

  back();
  sleep(2000);

  let enter = text("互动游戏").findOne(1000);
  if (enter) {
    click(enter.center());
    sleep(8000);
  } else {
    console.log("missing 互动游戏");
    return false;
  }

  if (scrolld) {
    scrollDown();
    sleep(1000);
    scrollDown();
    sleep(1000);
  }
  return true;
}

// function open_box(scrolld, screen) {
//   if (scrolld) {
//     scrollUp();
//     sleep(1000);
//     scrollUp();
//     sleep(1000);
//   }
//   let box = textContains("个盲盒待开").findOne(1000);
//   if (!box) {
//     if (scrolld) {
//       scrollDown();
//       sleep(1000);
//       scrollDown();
//       sleep(1000);
//     }
//     return true;
//   }
//   console.log(box.text());

//   click(box.center());
//   sleep(2000);

//   while (true) {
//     let open = text("一键开启").findOne(1000);
//     if (!open) {
//       break;
//     }
//     click(open.center());
//     sleep(5000);

//     let pean = textContains("京豆+").findOne(3000);
//     if (!pean) {
//       return false;
//     }

//     if (box.text() === "1个盲盒待开") {
//       click(screenSize.width / 2, (screenSize.height * 2) / 3);
//       sleep(2000);
//     } else {
//       click(screenSize.width / 2, (screenSize.height * 3) / 4);
//       sleep(2000);
//     }
//   }

//   if (scrolld) {
//     scrollDown();
//     sleep(1000);
//     scrollDown();
//     sleep(1000);
//   }
//   return true;
// }

function getGameTaskList(gameNameList) {
  let taskList = [];
  for (let i = 0; i < gameNameList.length; i++) {
    let name = gameNameList[i];
    let tasks = getGameTaskListByName(name);
    if (!tasks) {
      tasks = getGameTaskListByName(name);
    }
    taskList = taskList.concat(tasks);
  }
  return taskList;
}

function getGameTaskListByName(name) {
  let taskList = [];
  let game = text(name).findOne(500);
  if (!game) {
    return;
  }
  click(game.center());
  utils.longWait();

  let taskEnter = textContains("10元还款券").findOne(1000);
  if (!taskEnter) {
    return;
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
        dur_m: min - mins[j - 1] + 1,
      });
    }
  }
  back();
  sleep(1000);
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
      !view.text().includes("+") &&
      !view.text().includes("blindBox") &&
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
