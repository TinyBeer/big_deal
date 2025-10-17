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
  jinxi_direct();
  interactive_game_sign();
  redeem_prize_tickets();
  daily_claim_pean();
  daily_claim_pean_goods();
  hardwar_city();
  ecard();
  jd_campus();
  big_brand();
  big_brand_streak();
  clothe_makup();
  clothe_makupsteak();
  //todo optimize
  luck_reward();
  // get_beans();
  home_appliances_and_household_items();
  online_doctor();
  mother_baby();
  mother_babystreak();
  dong_dong_farm();
  home_nurse();
  global_shopping();

  doubleBackN(1);
}

/* tasks */

function clothe_makupsteak() {
  let backCnt = 0;
  let bb = homePageGetEnter("服饰美妆");
  if (!bb) {
    console.log("missing 服饰美妆 enter, back");
    backN(backCnt);
    return false;
  }
  click(bb.center());
  mediumWait();
  back();
  backN(1);

  click(bb.center());
  mediumWait();
  backCnt++;

  let list = text("image").depth(24).indexInParent(1).find(1000);
  let signBtn = null;
  for (let idx = 0; idx < list.length; idx++) {
    let element = list[idx];
    if (element.center().x < 100) {
      signBtn = element;
      break;
    }
  }
  if (!signBtn) {
    console.log("missing sign entry, skip");
    backN(backCnt);
    return false;
  }

  click(signBtn.center());
  longWait();
  mediumWait();
  backCnt++;

  let streak = text("今日可领").findOne(1000);
  if (!streak) {
    console.log("missing claim button, skip");
    backN(backCnt);
    return false;
  }

  click(streak.center().x, streak.center().y - 100);
  shortWait();
  backN(backCnt);
  return true;
}

function clothe_makup() {
  let backCnt = 0;
  let bb = homePageGetEnter("服饰美妆");
  if (!bb) {
    console.log("missing 服饰美妆 enter, back");
    backN(backCnt);
    return false;
  }
  click(bb.center());
  longWait();
  doubleBackN(1);

  click(bb.center());
  mediumWait();
  backCnt++;

  let list = text("image").depth(24).indexInParent(1).find(1000);
  let signBtn = null;
  for (let idx = 0; idx < list.length; idx++) {
    let element = list[idx];
    if (element.center().x < 100) {
      signBtn = element;
      break;
    }
  }
  if (!signBtn) {
    console.log("missing sign entry, skip");
    backN(backCnt);
    return false;
  }

  click(signBtn.center());
  longWait();
  mediumWait();
  backCnt++;

  let obj = text("待领取").findOne(1000);
  if (!obj) {
    console.log("missing claim button, skip");
    backN(backCnt);
    return false;
  }

  click(888, obj.center().y);
  shortWait();
  backN(backCnt);
  return true;
}

function mother_babystreak() {
  let backCnt = 0;
  let bb = homePageGetEnter("母婴馆");
  if (!bb) {
    console.log("missing 母婴馆 enter, back");
    backN(backCnt);
    return false;
  }
  click(bb.center());
  mediumWait();
  doubleBackN(1);
  shortWait();
  click(bb.center());
  mediumWait();
  backCnt++;

  for (let i = 0; i < 5; i++) {
    scrollDown();
    shortWait();
  }
  longWait();

  let streak = text("今日可领").findOne(1000);
  if (!streak) {
    console.log("missing claim button, skip");
    backN(backCnt);
    return false;
  }

  click(streak.center().x, streak.center().y - 100);
  shortWait();
  backN(backCnt);
  return true;
}

function mother_baby() {
  let backCnt = 0;
  let bb = homePageGetEnter("母婴馆");
  if (!bb) {
    console.log("missing 母婴馆 enter, back");
    backN(backCnt);
    return false;
  }
  click(bb.center());
  mediumWait();
  doubleBackN(1);
  shortWait();
  click(bb.center());
  mediumWait();
  backCnt++;

  for (let i = 0; i < 5; i++) {
    scrollDown();
    shortWait();
  }
  longWait();

  let obj = text("今日签到").findOne(1000);
  if (!obj) {
    console.log("missing claim button, skip");
    backN(backCnt);
    return false;
  }

  click(888, obj.center().y);
  shortWait();
  backN(backCnt);
  return true;
}

function big_brand_streak() {
  let backCnt = 0;
  let bb = homePageGetEnter("大牌奥莱");
  if (!bb) {
    console.log("missing 大牌奥莱 enter, back");
    backN(backCnt);
    return false;
  }
  click(bb.center());
  mediumWait();
  backCnt++;

  let list = text("image").depth(24).indexInParent(0).find(1000);
  let signBtn = null;
  for (let idx = 0; idx < list.length; idx++) {
    let element = list[idx];
    if (element.center().x < 100) {
      signBtn = element;
      break;
    }
  }
  if (!signBtn) {
    console.log("missing sign entry, skip");
    backN(backCnt);
    return false;
  }

  click(signBtn.center());
  longWait();
  mediumWait();
  backCnt++;

  let streak = text("今日可领").findOne(1000);
  if (!streak) {
    console.log("missing claim button, skip");
    backN(backCnt);
    return false;
  }

  click(streak.center().x, streak.center().y - 100);
  shortWait();
  backN(backCnt);
  return true;
}

function big_brand() {
  let backCnt = 0;
  let bb = homePageGetEnter("大牌奥莱");
  if (!bb) {
    console.log("missing 大牌奥莱 enter, back");
    backN(backCnt);
    return false;
  }
  click(bb.center());
  mediumWait();
  backCnt++;

  let list = text("image").depth(24).indexInParent(0).find(1000);
  let signBtn = null;
  for (let idx = 0; idx < list.length; idx++) {
    let element = list[idx];
    if (element.center().x < 100) {
      signBtn = element;
      break;
    }
  }
  if (!signBtn) {
    console.log("missing sign entry, skip");
    backN(backCnt);
    return false;
  }

  click(signBtn.center());
  longWait();
  mediumWait();
  backCnt++;

  let obj = text("连签奖励").findOne(1000);
  if (!obj) {
    console.log("missing claim button, skip");
    backN(backCnt);
    return false;
  }

  click(888, 767);
  shortWait();
  backN(backCnt);
  return true;
}

function home_nurse() {
  let backCnt = 0;
  let od = homePageGetEnter("护士到家");
  if (!od) {
    console.log("missing 护士到家 enter, back");
    backN(backCnt);
    return false;
  }
  click(od.center());
  backCnt++;
  mediumWait();

  backN(1);
  click(od.center());
  mediumWait();

  click(198, 493);
  backCnt++;
  mediumWait();

  let claim = text("签到领京豆").findOne(1000);
  if (!claim) {
    console.log("missing claim btn, back");
    backN(backCnt);
    return false;
  }
  click(claim.center());
  shortWait();
  backN(backCnt);
  return true;
}

function ecard() {
  console.log("京东E卡 ...");
  let backCnt = 0;
  search("京东礼品卡", 8000);
  backCnt += 3;

  let entry = text("持卡特权").findOne(1000);
  if (!entry) {
    console.log("missing entry, skip");
    backN(backCnt);
    return false;
  }
  click(entry.center());
  mediumWait();
  backCnt++;

  let obj = textMatches("天天抢\\d+京豆").findOne(1000);
  if (!obj) {
    console.log("missing claim button, skip");
    backN(backCnt);
    return false;
  }
  let par = obj.parent();
  for (let idx = 0; idx < par.childCount(); idx++) {
    let child = par.children()[idx];
    if (child.text() === "已领取") {
      console.log("already calimed, back");
      backN(backCnt);
      return false;
    } else if (child.text() === "去领取") {
      click(child.center());
      sleep(2000);
      backN(backCnt);
      return true;
    }
  }
  console.log("missing claim button, skip");
  backN(backCnt);
  return false;
}

function hardwar_city() {
  console.log("五金城");
  let backCnt = 0;
  search("五金城", 8000);
  backCnt += 3;

  let entry = text("进入").findOne(1000);
  if (!entry) {
    console.log("missing entry, skip");
    backN(backCnt);
    return false;
  }

  click(entry.center());
  backCnt++;
  sleep(8000);

  click(944, 2288);
  backCnt++;
  sleep(8000);

  let claimBtn = text("签到领京豆").findOne(1000);
  if (!claimBtn) {
    console.log("already claimed, skip");
    backN(backCnt);
    return false;
  }

  click(claimBtn.center());
  shortWait();

  backN(backCnt);
  return true;
}

function daily_claim_pean_goods() {
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

  let btn = text("图片").findOne(1000);
  if (!btn) {
    console.log("missing target,skip");
    return false;
  }
  scrollDown();
  sleep(1000);
  scrollDown();
  sleep(1000);

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

  let signBtn = id("signBtnId").findOne(1000);
  if (!signBtn) {
    console.log("missing sign bar, skip");
    backN(backCnt);
    return false;
  }

  click(signBtn.center());
  shortWait();

  backN(backCnt);
  return true;
}

function online_doctor() {
  let backCnt = 0;
  let od = homePageGetEnter("在线医生");
  if (!od) {
    console.log("missing 在线医生 enter, back");
    backN(backCnt);
    return false;
  }
  click(od.center());
  backCnt++;
  mediumWait();

  let closeBtn = className("android.widget.ImageView").depth(10).findOne(1000);
  if (closeBtn) {
    click(closeBtn.center());
    miniWait();
  }

  click(174, 430);
  backCnt++;
  mediumWait();

  let claim = text("签到领京豆").findOne(1000);
  if (!claim) {
    console.log("missing claim btn, back");
    backN(backCnt);
    return false;
  }
  click(claim.center());
  shortWait();
  backN(backCnt);
  return true;
}

function jd_campus() {
  let backCnt = 0;
  console.log("京东校园 task start...");

  let jce = homePageGetEnter("京东校园");
  if (!jce) {
    console.log("missing 京东校园 enter, skip");
    shortWait();
    return false;
  }
  click(jce.center());
  backCnt++;
  mediumWait();

  let obj = text("学生授权协议").findOne(1000);
  if (obj) {
    click(obj.center().x, obj.center().y - 100);
    shortWait();
  }

  let enter = textContains("签到领豆").findOne(1000);
  if (!enter) {
    console.log("missing sign enter, skip");
    backN(backCnt);
    shortWait();
    return false;
  }
  backCnt++;
  click(133, enter.center().y);
  longWait();
  longWait();

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

function home_appliances_and_household_items() {
  let backCnt = 0;
  let hh = homePageGetEnter("家电家居");
  if (!hh) {
    console.log("missing 家电家居 enter, skip");
    shortWait();
    return false;
  }
  click(hh.center());
  longWait();
  backCnt++;

  let close = className("android.widget.Image").text("close").findOne(1000);
  if (close) {
    click(close.center());
    miniWait();
  }

  let entry = null;
  let list = className("android.view.View").depth(21).find(1000);
  for (let idx = 0; idx < list.length; idx++) {
    let el = list[idx];
    if (el.center().x > 950) {
      entry = el;
    }
  }
  if (!entry) {
    console.log("missing 家电家居 float enter, back");
    backN(backCnt);
    shortWait();
    return false;
  }
  click(entry.center());
  longWait();
  longWait();
  backCnt++;

  let claim = textContains("领奖励").findOne(1000);
  if (!claim) {
    console.log("missing claim btn, back");
    backN(backCnt);
    return false;
  }
  // todo do not use act axis
  click(935, 1590);
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

  // let sign = text("签到").findOne(1000);
  // if (sign) {
  //   click(sign.center());
  //   shortWait();
  // }

  // while (true) {
  //   let explore = text("去浏览").findOne(1000);
  //   if (!explore) {
  //     break;
  //   }
  //   let parent = explore.parent();
  //   for (let i = 0; i < parent.childCount(); i++) {
  //     let child = parent.children()[i];
  //     if (!child) {
  //       continue;
  //     }
  //     let nums = extractNumbersWithDecimal(child.text());
  //     if (nums && nums.length === 3) {
  //       let num = nums[2] - nums[1];
  //       if (child.text().includes("商品")) {
  //         console.log(child.text());
  //         click(explore.center());
  //         mediumWait();
  //         for (let i = 0; i < num; i++) {
  //           // todo do not use act axis
  //           let x = 270 + 540 * (i % 2);
  //           let y = 550 + Math.floor(i / 2) * 700;
  //           console.log("click", x, y);
  //           click(x, y);
  //           mediumWait();
  //           back();
  //           shortWait();
  //         }
  //         back();
  //         shortWait();
  //       } else {
  //         console.log(child.text(), nums, "其他");
  //         for (let i = 0; i < num; i++) {
  //           click(explore.center());
  //           shortWait();
  //           back();
  //           shortWait();
  //         }
  //       }
  //     }
  //   }
  // }
  // back();
  // shortWait();
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
  console.log("奖票兑换...");
  let backCnt = 0;
  let enter = text("我的").findOne(1000);
  if (!enter) {
    return false;
  }
  click(enter.center());
  shortWait();
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
  mediumWait();

  let claimBtn = text("签到领豆").findOne(1000);
  if (!claimBtn) {
    console.log("missing claim button, skip");
    back();
    shortWait();
    return false;
  }
  click(claimBtn.center());
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

  let claimBtn = text("点击领取").findOne(1000);
  if (!claimBtn) {
    console.log("missing claim button, skip");
    back();
    shortWait();
    return false;
  }
  click(claimBtn.center());
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
    .findOne(6000);
  if (!obj) {
    console.log("missing claim button, back");
    back();
    shortWait();

    let ex = text("退出").findOne(1000);
    if (ex) {
      click(ex.center());
      sleep(1000);
      back();
      shortWait();
    }

    return false;
  }
  if (obj.text().includes("订阅提醒")) {
    console.log("already claimed, back");
    back();
    shortWait();

    let ex = text("退出").findOne(1000);
    if (ex) {
      click(ex.center());
      sleep(1000);
      back();
      shortWait();
    }
    return true;
  }

  shortWait();
  if (obj) {
    click(400, obj.center().y);
    shortWait();
  }

  back();
  shortWait();
  let ex = text("退出").findOne(1000);
  if (ex) {
    click(ex.center());
    sleep(1000);
    back();
    shortWait();
  }
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
  console.log("互动游戏签到...");
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
