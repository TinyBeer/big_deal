/* import */
// const utils = require("./utils");

/* conif data */

const gameTimeTaskNum = 7;

function shortWait() {
  sleep(3000);
}

function longWait() {
  sleep(8000);
}

function run() {
  /* launch app */
  app.launchApp("京东");
  longWait();

  /* run task */
  flash_sale();
  luck_reward();
  get_beans();
  jinxi_direct();
  interactive_game_sign();
  interactive_game();
  redeem_prize_tickets();
  dong_dong_farm();
}

/* tasks */

function dong_dong_farm() {
  let enter = text("东东农场").findOne(1000);
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
  longWait();
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
  let enter = text("秒杀").findOne(1000);
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
  let enter = text("秒杀").findOne(1000);
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
  let enter = text("种豆得豆").findOne(1000);
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
  let enter = text("京喜自营").findOne(1000);
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
  let enter = text("家电家居").findOne(1000);
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
  longWait();
  backCnt++;

  let moreReward = text("玩游戏领京豆").findOne(1000);
  if (!moreReward) {
    backN(backCnt);
    return false;
  }
  click(910, 920);
  shortWait();

  for (var i = 0; i < gameTimeTaskNum; i++) {
    sleep(1000);
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

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
