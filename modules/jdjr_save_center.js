const { longWait, backN, mediumWait, shortWait, tinyWait } = require("./utils");

let sc = null;

function run(screen) {
  // launch app
  app.launchApp("京东金融");
  longWait();
  sc = screen;
  saveMore();

  backN(2);
  back();
  backN(1);
}

function saveMore() {
  console.log("京东金融 赚钱更多京豆 ...");
  let backCnt = 0;
  let signEntry = text("签到").findOne(1000);
  if (!signEntry) {
    console.log("missing sign entry, skip");
    return false;
  }

  click(signEntry.center());
  shortWait();
  backCnt++;

  let saveMore = text("每日省更多").findOne(1000);
  if (!saveMore) {
    console.log("missing save more entery, skip...");
    backN(backCnt);
    return false;
  }

  backCnt++;
  click(saveMore.center());
  mediumWait();

  goto_seeadoctor();
  goto_watchvideo();
  goto_viewwealthmember();
  goto_viewtakeaway();
  goto_playmahjomaster();
  goto_viewchargepage();
  goto_viewjdappvideo();
  goto_newproduction();
  goto_dailysubsidary();
  goto_dailyrecommand();
  goto_bestseller();
  goto_lowprice();
  goto_bestsellinghits();
  goto_lowpricegoods();

  longWait();
  backN(backCnt);
  return true;
}

function goto_lowpricegoods() {
  let name = "浏览低价好物";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  shortWait();
  back();
  backN(1);
  mediumWait();
}

function goto_bestsellinghits() {
  let name = "浏览热销爆品";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  shortWait();
  back();
  backN(1);
  mediumWait();
}

function goto_lowprice() {
  let name = "逛品质低价好物";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  shortWait();
  back();
  backN(1);
  mediumWait();
}

function goto_bestseller() {
  let name = "逛每日热销好物";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  shortWait();
  back();
  backN(1);
  mediumWait();
}

function goto_dailyrecommand() {
  let name = "逛每日推荐好物";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  shortWait();
  back();
  backN(1);
  mediumWait();
}

function goto_dailysubsidary() {
  let name = "逛每日补贴好物";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  shortWait();
  back();
  backN(1);
  mediumWait();
}

function goto_newproduction() {
  let name = "去新奇频道领京豆";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  shortWait();
  back();
  backN(1);
  mediumWait();
}

function goto_viewjdappvideo() {
  let name = "看京东App视频";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  shortWait();
  back();
  backN(1);
  mediumWait();
}

function goto_viewchargepage() {
  let name = "浏览充值页10秒";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  longWait();
  longWait();
  backN(1);
}

function goto_playmahjomaster() {
  let name = "去玩雀神来也";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  longWait();
  longWait();
  backN(1);
}

function goto_viewtakeaway() {
  let name = "浏览外卖频道页";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  longWait();
  longWait();
  backN(1);
  shortWait();
}

function goto_viewwealthmember() {
  let name = "浏览财富会员权益";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  longWait();
  longWait();
  backN(1);
}

function goto_watchvideo() {
  let name = "浏览视频30秒";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  longWait();
  longWait();
  longWait();
  longWait();
  mediumWait();
  backN(1);
  return true;
}

function goto_seeadoctor() {
  let name = "浏览看病买药频道";
  console.log(name, "...");

  let entry = find_entry(name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());
  longWait();
  backN(1);
}

function find_entry(name) {
  let obj = textContains(name).findOne(1000);
  if (!obj || !obj.parent() || !obj.parent().parent()) {
    return;
  }
  let root = obj.parent().parent().parent();
  let entry = find_goto_button(root);
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

module.exports = {
  run,
};
