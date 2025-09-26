/* import */
const utils = require("./utils");

const closeButtonNameList = ["立即领取", "再领5京豆"];

// "去抽话费礼包",
// "去QQ阅读看庆余年",
// "去哈啰签到领出行优惠",
// "去百度地图领现金",
// "去酷狗免费听歌",
// "逛频道抢50元补贴券包",

function run(screen) {
  /* launch app */
  app.launchApp("京东金融");
  utils.longWait();
  if (!enter_daily_earn_pean()) {
    console.log("进入 天天赚京豆 失败");
    return false;
  }
  goto_diantao();
  goto_takeaway();
  goto_seeadoctor();

  back_from_daily_earn_pean();

  utils.backN(2);
}

function goto_seeadoctor() {
  let name = "逛看病买药,领京豆";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();
  utils.backN(1);
  try_close_popup();
}

function goto_takeaway() {
  let name = "浏览外卖频道页";
  console.log(name, "...");
  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();
  sleep(15000);
  utils.backN(1);
  try_close_popup();
}

function goto_diantao() {
  let name = "去点淘APP赚零花钱";
  console.log(name, "...");
  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();

  utils.backN(2);
  back();
  back();
  utils.shortWait();
  utils.backN(1);

  try_close_popup();
}

function enter_daily_earn_pean() {
  let backCnt = 0;
  let searchBar = id("com.jd.jrapp:id/con_top_search").findOne(1000);
  if (!searchBar) {
    console.log("missing search bar, skip");
    return false;
  }
  searchBar.click();
  backCnt += 2;
  utils.miniWait();
  setText("天天赚京豆");
  utils.miniWait();

  let searchBtn = text("搜索").findOne();
  if (!searchBtn) {
    console.log("missing search button, skip");
    utils.backN(backCnt);
    return false;
  }
  searchBtn.click();
  backCnt++;
  utils.mediumWait();

  let entry = text("天天赚京豆").depth(21).findOne(1000);
  if (!entry) {
    console.log("missing entry, skip");
    utils.backN(backCnt);
    return false;
  }
  click(entry.center());
  utils.longWait();

  try_close_popup();

  scrollDown();
  utils.miniWait();
  scrollDown();
  utils.miniWait();

  return true;
}

function back_from_daily_earn_pean() {
  utils.backN(5);
}

function try_close_popup() {
  for (let index = 0; index < closeButtonNameList.length; index++) {
    let name = closeButtonNameList[index];
    let obj = text(name).findOne(1000);
    if (obj) {
      click(obj.center().x, obj.center().y + 250);
      sleep(1000);
    }
  }
}

function find_entry(name) {
  let obj = text(name).findOne(1000);
  if (!obj || !obj.parent()) {
    return;
  }
  let parent = obj.parent();
  return find_goto_button(parent);
}

function find_goto_button(parent) {
  for (let idx = 0; idx < parent.children().length; idx++) {
    let child = parent.children()[idx];
    if (child.text() === "去完成" || child.text() == "继续完成") {
      return child;
    }
    if (child.childCount != 0) {
      let ch = find_goto_button(child);
      if (ch) {
        return ch;
      }
    }
  }
  return;
}

// 导出函数（供其他脚本调用）
module.exports = {
  run,
};
