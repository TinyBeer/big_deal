/* import */

const { backN, shortWait, isPointInBounds } = require("./utils");

function getTag(name) {
  return className("android.widget.TextView")
    .depth(12)
    .text(name)
    .findOne(1000);
}

function isHomePage() {
  return getTag("新品") && getTag("首页");
}

function switchTag(name) {
  let tag = getTag(name);
  if (!tag) {
    return false;
  }
  click(tag.center());
  sleep(5000);
  return true;
}

function backHomePage(backCnt) {
  backN(backCnt, function () {
    let ex = text("退出").findOne(1000);
    if (ex) {
      click(ex.center());
      shortWait();
    }
    if (isHomePage()) {
      return true;
    }

    return false;
  });
}

let entryBar = null;
function getEntryBar() {
  if (entryBar) {
    return entryBar;
  }
  let list = className("android.view.ViewGroup")
    .depth(19)
    .childCount(5)
    .indexInParent(0)
    .find(500);
  for (let idx = 0; idx < list.length; idx++) {
    let e = list[idx];
    if (e.center().x < 800) {
      entryBar = e;
      break
    }
  }
  console.log("entry bar bounds", entryBar.bounds());

  return entryBar;
}

function homePageGetEnter(name) {
  console.log("enter", name);
  // swipe left
  let eb = getEntryBar()
  let y = eb.center().y;
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
      eb.bounds().top,
      1080,
      eb.bounds().bottom,
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

// 导出函数（供其他脚本调用）
module.exports = {
  backHomePage,
  homePageGetEnter,
  switchTag,
};
