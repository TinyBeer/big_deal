auto();
const utils = require("./utils");
const screenSize = utils.getScreenSize();

let obj = text("去点淘APP赚零花钱").findOne(1000);
console.log(obj);

const closeButtonNameList = ["立即领取", "再领5京豆"];

let taskNameList = [
  "去抽话费礼包",
  "去QQ阅读看庆余年",
  // "去哈啰签到领出行优惠",
  // "去百度地图领现金",
  // "去点淘APP赚零花钱",
  // "去酷狗免费听歌",
  // "逛频道抢50元补贴券包",
  // "浏览外卖频道页",
  // "逛看病买药,领京豆",
];

// daily_earn_pean();

function daily_earn_pean() {
  enter_daily_earn_pean();

  for (let i = 0; i < taskNameList.length; i++) {
    tryClosePopup();
    let name = taskNameList[i];
    console.log("do task:", name);
    do_task(name);
    sleep(5000);
  }
}

function enter_daily_earn_pean() {
  let searchBar = id("com.jd.jrapp:id/con_top_search").findOne(1000);
  if (!searchBar) {
    console.log("missing search bar, skip");
    return false;
  }
  searchBar.click();
  backCnt += 2;
  sleep(500);
  setText("天天赚京豆");
  sleep(500);

  let searchBtn = text("搜索").findOne();
  if (!searchBtn) {
    console.log("missing search button, skip");
    backN(backCnt);
    return false;
  }
  searchBtn.click();
  backCnt++;
  sleep(3000);

  let entry = text("天天赚京豆").depth(21).findOne(1000);
  if (!entry) {
    console.log("missing entry, skip");
    backN(backCnt);
    return false;
  }
  click(entry.center());
  sleep(8000);
}

function do_task(name) {
  let obj = text(name).findOne(1000);
  let gotoBtn = find_goto_button(obj.parent());
  if (
    !gotoBtn ||
    gotoBtn.center().y < 0 ||
    gotoBtn.center().y > screenSize.height
  ) {
    console.log("button out of screan, skip");
    return false;
  }
  click(gotoBtn);
  sleep(25000);
  back();
  sleep(2000);
  back();
  back();
  sleep(2000);
  back();
  sleep(2000);
  back();
  sleep(2000);
}

function find_goto_button(parent) {
  if (!parent) {
    return;
  }
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

function tryClosePopup() {
  for (let index = 0; index < closeButtonNameList.length; index++) {
    let name = closeButtonNameList[index];
    let obj = text(name).findOne(1000);
    if (obj) {
      click(obj.center().x, obj.center().y + 250);
      sleep(1000);
    }
  }
}

function show_child_text(parent) {
  if (!parent) {
    return;
  }
  for (let idx = 0; idx < parent.children().length; idx++) {
    let child = parent.children()[idx];
    console.log(idx, child.text());

    if (child.childCount != 0) {
      show_child_text(child);
    }
  }
}

// let str =
//   "逛逛中秋会场 逛逛中秋会场得抽盲盒机会 限1次(0/1) 去逛逛 种草新奇耳机 种草新奇耳机得抽盲盒机会 限3次(0/3) 去逛逛 种草迪士尼新奇月饼 种草迪士尼月饼得抽盲盒机会 限1次(0/1) 去逛逛 逛逛美心月饼 逛逛美心月饼得抽盲盒机会 限1次(0/1) 去逛逛";

function switchTag(name) {
  let tag = className("android.widget.TextView")
    .depth(12)
    .text(name)
    .findOne(1000);
  if (!tag) {
    return false;
  }

  click(tag.center());
  sleep(5000);
}
