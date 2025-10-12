/* import */
const utils = require("./utils");

const closeButtonNameList = ["立即领取", "再领\\d+京豆"];

let sc = null;

function run() {
  let screen = utils.getScreenSize();
  sc = screen;
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
  goto_sevencat();
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
  goto_takeawayticket();
  goto_dailysubsidary();
  goto_whateveryonebuying();
  goto_qualitylife();
  goto_daydaylowprice();
  goto_dailysubsidarygood();

  back_from_daily_earn_pean();

  utils.doubleBackN(1);
}

function goto_dailysubsidarygood() {
  let name = "逛每日补贴好物";
  console.log(name, "...");
  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();

  utils.doubleBackN(3, try_close_popup);
}

function goto_daydaylowprice() {
  let name = "天天低价新发现";
  console.log(name, "...");
  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();

  utils.doubleBackN(3, try_close_popup);
}

function goto_qualitylife() {
  let name = "花小钱享品质生活";
  console.log(name, "...");
  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();

  utils.doubleBackN(3, try_close_popup);
}

function goto_whateveryonebuying() {
  let name = "逛逛大家都在买什么";
  console.log(name, "...");
  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();

  utils.doubleBackN(3, try_close_popup);
}

function goto_dailysubsidary() {
  let name = "每日补贴限时抢！";
  console.log(name, "...");
  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();

  utils.doubleBackN(3, try_close_popup);
}

function goto_takeawayticket() {
  let name = "去领取一张10元外卖券";
  console.log(name, "...");
  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();

  utils.doubleBackN(3, try_close_popup);
}

function goto_sevencat() {
  let name = "去七猫小说领金币";
  console.log(name, "...");
  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  utils.longWait();
  utils.longWait();

  utils.doubleBackN(5, try_close_popup);

  try_close_popup();
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
  utils.longWait();

  utils.doubleBackN(1);

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

  utils.doubleBackN(3, try_close_popup);

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

  utils.doubleBackN(4);
  utils.shortWait();
  let ex = text("退出").findOne(1000);
  if (ex) {
    click(ex.center());
    utils.shortWait();
  }
  utils.doubleBackN(2);

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

  utils.doubleBackN(4, try_close_popup);

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
  utils.doubleBackN(1);
  utils.longWait();
  utils.longWait();
  let closeBtn = text("关闭").findOne(1000);
  if (closeBtn) {
    click(closeBtn.center());
    utils.miniWait();
  }

  utils.doubleBackN(3, try_close_popup);

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

  utils.doubleBackN(5, try_close_popup);

  let closeBtn = desc("关闭").findOne(1000);
  if (closeBtn) {
    click(closeBtn.center());
    utils.miniWait();
  }

  let quitBtn = text("残忍离开").findOne(1000);
  if (quitBtn) {
    click(quitBtn.center());
    utils.shortWait();
    utils.doubleBackN(2, try_close_popup);
  }

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

  utils.doubleBackN(4, try_close_popup);

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

  utils.doubleBackN(5, try_close_popup);

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

  utils.doubleBackN(3);
  for (let i = 0; i < 4; i++) {
    back();
    utils.doubleBackN(1);
    let ex = text("退出").findOne(1000);
    if (ex) {
      click(ex.center());
      utils.shortWait();
      break;
    }
  }

  utils.doubleBackN(1);

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

  utils.doubleBackN(5, try_close_popup);

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

  utils.doubleBackN(5, try_close_popup);

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
  utils.doubleBackN(1, try_close_popup);
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
  utils.doubleBackN(1);
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
  utils.longWait();
  utils.doubleBackN(1);
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
  utils.longWait();

  utils.doubleBackN(5, try_close_popup);

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
    utils.doubleBackN(backCnt);
    return false;
  }
  searchBtn.click();
  backCnt++;
  utils.mediumWait();

  let entry = text("天天赚京豆").depth(21).findOne(1000);
  if (!entry) {
    console.log("missing entry, skip");
    utils.doubleBackN(backCnt);
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
      return true;
    }
  }
  return false;
}

function find_entry(name) {
  let obj = text(name).findOne(1000);
  if (!obj || !obj.parent()) {
    return;
  }
  let parent = obj.parent();
  let entry = find_goto_button(parent);
  if (
    entry &&
    (entry.center().x < 0 ||
      entry.center().x > sc.width ||
      entry.center().y < 0 ||
      entry.center().y > sc.height)
  ) {
    return;
  }
  return entry;
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
