/* import */

const {
  backN,
  shortWait,
  longWait,
  mediumWait,
  isPointInBounds,
  doubleBackN,
  miniWait,
} = require("./utils");

/* conf data */

let entryBar = null;

function run() {
  /* launch app */
  app.launchApp("京东");
  longWait();

  entryBar = getEntryBar();
  if (!entryBar) {
    console.log("missing entery bar, skip");
    doubleBackN(1);
    return;
  }

  /* run task */
  flash_sale();
  interactive_game();
  daily_claim_pean();
  global_shopping();

  doubleBackN(1);
}

/* tasks */
function daily_claim_pean() {
  console.log("天天领豆");
  let backCnt = 0;
  let searchBar = desc("搜索栏").findOne(1000);
  if (!searchBar) {
    console.log("missing search bar, skip");
    return false;
  }
  searchBar.click();
  backCnt++;
  sleep(500);
  setText("天天领豆");
  sleep(500);
  backCnt++;

  let searchBtn = text("搜索").findOne(1000);
  if (!searchBtn) {
    console.log("missing search button, skip");
    backN(backCnt);
    return false;
  }

  searchBtn.click();
  sleep(10000);
  backCnt++;

  let signBtn = text("立即刮卡").findOne(1000);
  if (signBtn) {
    click(signBtn.center());
    longWait();
  } else {
    console.log("missing target,skip");
    miniWait();
  }

  let claimed = textContains("已领取奖励").findOne(100);
  if (claimed) {
    console.log("already claimed explore goods,skip");
    backN(backCnt);
    return false;
  }
  let btn = text("图片").findOne(1000);
  if (!btn) {
    console.log("missing target,skip");
    backN(backCnt);
    return false;
  }
  scrollDown();
  sleep(1000);
  scrollDown();
  sleep(1000);

  let plus = textContains("限时开PLUS特惠").findOne(100);
  if (plus) {
    click(1006, 2183);
    shortWait();
  }

  let num = 6;
  let cnt = 0;
  let goods = text("").depth(19).childCount(4).find(1000);
  for (let idx = 0; idx < goods.length; idx++) {
    let e = goods[idx];
    if (e.center().y > 330) {
      click(e.children()[0].center());
      sleep(8000);
      doubleBackN(2, function () {
        let obj = text("图片").findOne(500);
        if (obj) {
          return true;
        }
        return false;
      });
      sleep(1000);
      cnt++;
    }
    if (cnt >= num) {
      break;
    }
  }
  click(btn.center());
  shortWait();

  backN(backCnt);
  return true;
}

function global_shopping() {
  let backCnt = 0;
  let gs = homePageGetEnter("全球购");
  if (!gs) {
    console.log("missing 全球购 enter, skip");
    shortWait();
    return false;
  }

  click(gs.center());
  backCnt++;
  longWait();

  let closeBtn = id("dolphin_float_close_btn").findOne(1000);
  if (closeBtn) {
    click(closeBtn.center());
    shortWait();
  }
  let enter = className("android.view.View")
    .depth(18)
    .indexInParent(1)
    .childCount(1)
    .findOne(1000);
  // let enter = id("bg").findOne(1000);
  if (!enter) {
    console.log("missing 做任务赚京豆 enter, skip");
    back();
    shortWait();
    return false;
  }

  click(enter.center());
  longWait();
  backCnt++;

  let claim = text("今日签到").findOne(1000);
  if (!claim) {
    console.log("miss claim item, skip");
    backN(backCnt);
    return false;
  }
  click(899, claim.center().y);
  shortWait();
  backN(backCnt);
  return true;
}

function flash_sale() {
  let enter = homePageGetEnter("秒杀");
  if (!enter) {
    return false;
  }
  click(enter.center());
  longWait();

  let signBtn = text("签到领豆").findOne(1000);
  if (signBtn) {
    click(signBtn.center());
    longWait();
  } else {
    console.log("missing sign button, skip");
  }
  let claimBtn = text("点击领取").findOne(1000);
  if (claimBtn) {
    click(claimBtn.center());
    shortWait();
  } else {
    console.log("missing claim button, skip");
  }

  back();
  shortWait();
}

function interactive_game() {
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

  // 签到
  let sign = text("签到").findOne(1000);
  if (sign) {
    click(sign.center());
    mediumWait();
  } else {
    console.log("missing sign button, skip...");
  }
  backN(backCnt);
}

function getEntryBar() {
  let list = className("android.view.ViewGroup")
    .depth(19)
    .childCount(5)
    .indexInParent(0)
    .find(500);
  for (let idx = 0; idx < list.length; idx++) {
    let e = list[idx];
    if (e.center().x < 800) {
      return e;
    }
  }
  return;
}

function homePageGetEnter(name) {
  console.log("enter", name);
  // swipe left
  let y = entryBar.center().y;
  let sx = 400;
  let ex = 900;
  let dur = 500;

  swipe(sx, y, ex, y, dur);
  shortWait();
  let enter = className("android.widget.TextView")
    .text(name)
    .depth(23)
    .findOne(1000);

  if (
    enter &&
    isPointInBounds(enter.center(), [
      0,
      entryBar.bounds().top,
      1080,
      entryBar.bounds().bottom,
    ])
  ) {
    return enter;
  }
  swipe(ex, y, sx, y, dur);
  shortWait();
  enter = className("android.widget.TextView")
    .text(name)
    .depth(23)
    .findOne(1000);

  return enter;
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

function search(content, waitTime) {
  let searchBar = desc("搜索栏").findOne(1000);
  if (!searchBar) {
    console.log("missing search bar, skip");
    return false;
  }
  searchBar.click();
  sleep(500);
  setText(content);
  sleep(500);

  let searchBtn = text("搜索").findOne(1000);
  if (!searchBtn) {
    console.log("missing search button, skip");
    back();
    sleep(2000);
    return false;
  }

  searchBtn.click();
  sleep(waitTime);
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
