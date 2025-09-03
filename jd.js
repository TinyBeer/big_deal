/* import */
// const utils = require("./utils");

/* conif data */

const gameTimeTaskNum = 7;

function shortWait() {
  sleep(3000);
}

function mediumWait() {
  sleep(5000);
}

function longWait() {
  sleep(8000);
}

function run() {
  /* launch app */
  app.launchApp("京东");
  longWait();

  /* run task */
  // flash_sale();
  // luck_reward();
  // get_beans();
  // jinxi_direct();
  // interactive_game_sign();
  // interactive_game();
  // redeem_prize_tickets();
  // dong_dong_farm();
  // global_shopping();
  home_appliances_and_household_items();
}

/* tasks */

function home_appliances_and_household_items() {
  let backCnt = 0;
  let hh = homePageGetEnter("家电家居");
  if (!hh) {
    console.log("missing 家电家居 enter, skip");
    shortWait();
    return false;
  }
  click(hh.center());
  mediumWait();
  backCnt++;

  let tmp = className("android.view.View")
    .clickable(true)
    .depth(22)
    .findOne(1000);
  if (!tmp || !tmp.parent()) {
    console.log("missing 家电家居 float enter, back");
    backN(backCnt);
    shortWait();
    return false;
  }
  let enter = tmp.parent();
  click(enter.center());
  longWait();
  longWait();
  backCnt++;

  let claim = textContains("领奖励").findOne(1000);
  if (!claim) {
    console.log("missing claim btn, back");
    backN(backCnt);
    return false;
  }
  click(960, 1400);
  shortWait();
  backN(backCnt);
  return true;
}

function global_shopping() {
  let gs = homePageGetEnter("全球购");
  if (!gs) {
    console.log("missing 全球购 enter, skip");
    shortWait();
    return false;
  }

  click(gs.center());
  shortWait();

  let closeBtn = id("dolphin_float_close_btn").findOne(1000);
  if (closeBtn) {
    click(closeBtn.center());
    shortWait();
  }

  let enter = id("bg").findOne(1000);
  if (!enter) {
    console.log("missing 做任务赚京豆 enter, skip");
    back();
    shortWait();
    return false;
  }
  click(enter.center());
  shortWait();

  let sign = text("签到").findOne(1000);
  if (sign) {
    click(sign.center());
    shortWait();
  }

  while (true) {
    let explore = text("去浏览").findOne(1000);
    if (!explore) {
      break;
    }
    let parent = explore.parent();
    for (let i = 0; i < parent.childCount(); i++) {
      let child = parent.children()[i];
      if (!child) {
        continue;
      }
      let nums = extractNumbersWithDecimal(child.text());
      if (nums && nums.length === 3) {
        let num = nums[2] - nums[1];
        if (child.text().includes("商品")) {
          console.log(child.text());
          click(explore.center());
          mediumWait();
          for (let i = 0; i < num; i++) {
            let x = 270 + 540 * (i % 2);
            let y = 550 + Math.floor(i / 2) * 700;
            console.log("click", x, y);
            click(x, y);
            mediumWait();
            back();
            shortWait();
          }
          back();
          shortWait();
        } else {
          console.log(child.text(), nums, "其他");
          for (let i = 0; i < num; i++) {
            click(explore.center());
            shortWait();
            back();
            shortWait();
          }
        }
      }
    }
  }
  back();
  shortWait();
}

function dong_dong_farm() {
  let enter = homePageGetEnter("东东农场");
  if (!enter) {
    console.log("missing 东东农场, skip");
    return false;
  }
  click(enter.center());
  longWait();

  //todo spinning wheel

  back();
  shortWait();
}

function redeem_prize_tickets() {
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
  mediumWait();
  backCnt++;

  let redeemEnter = text("兑换").findOne(1000);
  if (!redeemEnter) {
    backN(backCnt);
    return false;
  }
  click(redeemEnter.center());
  backCnt++;
  shortWait();

  let fifteenTickets = text("15").findOne(1000);
  if (!fifteenTickets) {
    console.log("fifteen tickets not found");
    backN(backCnt);
    return false;
  }
  let tParent = fifteenTickets.parent();
  if (!tParent || tParent.childCount() != 3) {
    console.log("get wrong target");
    backN(backCnt);
    return false;
  }
  for (let i = 0; i < tParent.childCount(); i++) {
    if (
      tParent.children()[i].text() === "15" ||
      tParent.children()[i].text() === "奖票"
    ) {
      continue;
    }
    click(tParent.children()[i].center());
    shortWait();
    var obj = text("确认兑换").findOne(1000);
    if (!obj) {
      console.log("sth wrong, break");
      break;
    }
    var redeemBtn = text("确认兑换").findOne(1000);
    click(redeemBtn.center());
    shortWait();
    break;
  }

  backN(backCnt);
}

function flash_sale() {
  let enter = homePageGetEnter("秒杀");
  if (!enter) {
    return false;
  }
  click(enter.center());
  shortWait();

  click(500, 620);
  shortWait();
  back();
  shortWait();
}

function luck_reward() {
  let enter = homePageGetEnter("秒杀");
  if (!enter) {
    return false;
  }
  click(enter.center());
  shortWait();

  click(900, 620);
  shortWait();
  back();
  shortWait();
}

function get_beans() {
  let enter = homePageGetEnter("种豆得豆");
  if (!enter) {
    return false;
  }
  click(enter.center());
  shortWait();

  while (true) {
    let obj = text("点击领取").findOne(2000);
    if (!obj) {
      break;
    }
    click(obj.center());
    shortWait();
  }

  back();
  shortWait();
}

function jinxi_direct() {
  let enter = homePageGetEnter("京喜自营");
  if (!enter) {
    return false;
  }
  click(enter.center());
  longWait();

  //   let obj = text("领京豆").findOne(1000);
  let obj = className("android.view.View")
    .textContains(
      // "领京豆 签到 大牌同厂 满1元5折 万人团 拼团价更低 零食代工厂 品质零食 地标美食 正宗好味"
      "领京豆"
    )
    .findOne(6000)
    .parent();
  shortWait();
  if (obj) {
    click(400, 890);
    shortWait();
  }

  back();
  shortWait();
}

function appliance_and_furniture() {
  let enter = homePageGetEnter("家电家居");
  if (!enter) {
    return false;
  }
  click(enter.center());
  shortWait();
  //todo
  back();
  shortWait();
}

function interactive_game_sign() {
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

  let sign = text("签到").findOne(1000);
  if (!sign) {
    backN(backCnt);
    return false;
  }
  click(sign.center());
  shortWait();
  backN(backCnt);
}

function interactive_game() {
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
  mediumWait();
  backCnt++;

  let moreReward = text("玩游戏领京豆").findOne(1000);
  if (!moreReward) {
    backN(backCnt);
    return false;
  }
  click(910, 920);
  longWait();

  for (var i = 0; i < gameTimeTaskNum; i++) {
    click(866, 1200);
    sleep(63000);
    back();
    back();
    sleep(4000);
    click(866, 1200);
    sleep(2000);
  }

  backN(backCnt);
}

function backN(cnt) {
  for (let i = 0; i < cnt; i++) {
    back();
    shortWait();
  }
}

function homePageGetEnter(name) {
  // swipe lefe
  let y = 550;
  let sx = 400;
  let ex = 900;
  let dur = 500;

  swipe(sx, y, ex, y, dur);
  shortWait();
  let enter = text(name).findOne(1000);

  if (enter && enter.center().x > 0 && enter.center().x < 1080) {
    return enter;
  }
  swipe(ex, y, sx, y, dur);
  shortWait();
  return text(name).findOne(1000);
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

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
