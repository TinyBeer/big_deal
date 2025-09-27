/* import */
const utils = require("./utils");

const closeButtonNameList = ["立即领取", "再领\\d+京豆"];

run();

function run(screen) {
  /* launch app */
  app.launchApp("京东金融");
  utils.longWait();
  if (!enter_daily_earn_pean()) {
    console.log("进入 天天赚京豆 失败");
    return false;
  }
  goto_selectedgoods();
  goto_headlinefast();
  goto_headlineapp();
  goto_qqreading();
  goto_chinamobile();
  goto_monkeyexpolorer();
  goto_baidufast();
  goto_baidumap();
  goto_mantisshrimp();
  goto_diantao();
  goto_ucfast();
  goto_takeaway();
  goto_seeadoctor();
  goto_flash();
  goto_jmt();
  
  back_from_daily_earn_pean();
}

function goto_jmt() {
  let name = "逛京民通，领京豆";
  console.log(name, "...");
  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();

  // utils.backN(2);
  // back();
  utils.backN(1);

  try_close_popup();
}

function goto_flash() {
  let name = "逛京东秒杀领京豆";
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
  utils.backN(2);

  try_close_popup();
}

function goto_ucfast() {
  let name = "去UC极速版领现金";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();
  utils.longWait();
  utils.longWait();

  utils.backN(3);
  back();
  back();
  utils.miniWait();
  let ex = text("退出").findOne(1000);
  if (ex) {
    click(ex.center());
    utils.shortWait();
  }
  utils.backN(1);

  try_close_popup();
}

function goto_mantisshrimp() {
  let name = "去皮皮虾看搞笑内容赚钱";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();
  utils.longWait();
  utils.longWait();

  utils.backN(2);
  back();
  utils.backN(2);

  try_close_popup();
}

function goto_baidumap() {
  let name = "去百度地图领现金";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();
  utils.longWait();
  utils.longWait();

  utils.backN(2);

  try_close_popup();
}

function goto_baidufast() {
  let name = "去百度极速版领现金";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();
  utils.longWait();

  utils.backN(3);
  back();
  utils.backN(2);

  try_close_popup();
}

function goto_monkeyexpolorer() {
  let name = "去悟空浏览器领福利";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();

  let open = text("打开").findOne(1000);
  if (open) {
    click(open.center());
    utils.miniWait();
  }
  utils.longWait();

  utils.backN(2);
  back();
  utils.backN(2);

  try_close_popup();
}

function goto_chinamobile() {
  let name = "去抽话费礼包";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();
  utils.longWait();

  utils.backN(2);
  back();
  utils.backN(2);

  try_close_popup();
}

function goto_qqreading() {
  let name = "去QQ阅读看庆余年";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();
  utils.longWait();

  utils.backN(3);

  let ex = text("退出").findOne(1000);
  if (ex) {
    click(ex.center());
    utils.shortWait();
  }
  utils.backN(1);

  try_close_popup();
}

function goto_headlineapp() {
  let name = "去头条App赚现金";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();
  utils.longWait();

  back();
  utils.backN(2);

  try_close_popup();
}

function goto_headlinefast() {
  let name = "去头条极速版赚钱";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();

  let cgc = desc("免费领取300金币").findOne(1000);
  if (cgc) {
    click(cgc.center().x, cgc.center().y + 250);
    utils.miniWait();
  }

  let claim = desc("翻倍领取").findOne(1000);
  if (claim) {
    click(claim.center().x - 400, claim.center().y);
    utils.miniWait();
  }

  let vcoin = descMatches("看视频领\\d+金币").findOne(1000);
  if (vcoin) {
    click(vcoin.center().x, vcoin.center().y + 400);
    utils.miniWait();
  }

  utils.backN(2);
  back();
  utils.backN(2);

  try_close_popup();
}

function goto_selectedgoods() {
  let name = "去看精选好物";
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
  utils.longWait();

  utils.backN(3);
  back();
  utils.backN(2);

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
    let obj = textMatches(name).findOne(1000);
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

// // 导出函数（供其他脚本调用）
// module.exports = {
//   run,
// };
