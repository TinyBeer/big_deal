/* import */
const utils = require("./utils");
const { findEntry } = require("./jdjr_utils");

const closeButtonNameList = ["立即领取", "再领\\d+京豆"];

// 通用浏览任务配置：{ name, longWaits?, backCount?, exitFn? }
const browseTasks = [
  { name: "去看精选好物", backCount: 1 },
  { name: "去头条极速版赚钱", backCount: 5, longWaits: 1, custom: "headlineFast" },
  { name: "去头条App赚现金", backCount: 5, longWaits: 2 },
  { name: "去七猫小说领金币", backCount: 5, longWaits: 2, extraClose: true },
  { name: "去QQ阅读看庆余年", backCount: 3, longWaits: 2, custom: "qqReading" },
  { name: "去抽话费礼包", backCount: 5, longWaits: 2, extraClose: true },
  { name: "去悟空浏览器领福利", backCount: 4, longWaits: 1, custom: "monkeyExplorer" },
  { name: "去皮皮虾看搞笑内容赚钱", backCount: 4, longWaits: 3, extraClose: true },
  { name: "去点淘APP赚零花钱", backCount: 5, longWaits: 3, extraClose: true },
  { name: "去UC极速版领现金", backCount: 4, longWaits: 3, custom: "ucFast" },
  { name: "浏览外卖频道页", backCount: 1, longWaits: 2, mediumWait: true, extraClose: true },
  { name: "逛看病买药,领京豆", backCount: 1 },
  { name: "逛京东秒杀领京豆", backCount: 3, extraClose: true },
  { name: "逛京民通，领京豆", backCount: 1, longWaits: 2, extraClose: true },
  { name: "去领取一张10元外卖券", backCount: 3 },
  { name: "每日补贴限时抢！", backCount: 3 },
  { name: "逛逛大家都在买什么", backCount: 3 },
  { name: "花小钱享品质生活", backCount: 3 },
  { name: "天天低价新发现", backCount: 3 },
  { name: "逛每日补贴好物", backCount: 3 },
  { name: "浏览白条频道10秒", backCount: 3, longWaits: 2, mediumWait: true, custom: "iou" },
];

function run() {
  /* launch app */
  app.launchApp("京东金融");
  utils.longWait();
  if (!enterDailyEarnPea()) {
    console.log("进入 天天赚京豆 失败");
    return false;
  }

  for (let i = 0; i < browseTasks.length; i++) {
    let task = browseTasks[i];
    if (task.custom) {
      gotoCustomTask(task);
    } else {
      gotoBrowseTask(task);
    }
  }

  backFromDailyEarnPea();
  utils.doubleBackN(1);
}

function gotoBrowseTask(task) {
  console.log(task.name, "...");
  let entry = findEntry(task.name);
  if (!entry) {
    console.log("missing entry, skip");
    return false;
  }
  click(entry.center());

  for (let i = 0; i < (task.longWaits || 1); i++) {
    utils.longWait();
  }
  if (task.mediumWait) {
    utils.mediumWait();
  }

  utils.doubleBackN(task.backCount || 3, tryClosePopup);
  if (task.extraClose) {
    tryClosePopup();
  }
  return true;
}

function gotoCustomTask(task) {
  console.log(task.name, "...");
  let entry = findEntry(task.name);
    case "headlineFast":
      utils.longWait();
      handleHeadlineFastClaim();
      utils.doubleBackN(5, tryClosePopup);
      tryClosePopup();
      break;

    case "qqReading":
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
      tryClosePopup();
      break;

    case "monkeyExplorer":
      utils.longWait();
      let open = text("打开").findOne(1000);
      if (open) {
        click(open.center());
        utils.miniWait();
      }
      utils.longWait();
      utils.doubleBackN(4, tryClosePopup);
      tryClosePopup();
      break;

    case "ucFast":
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
      tryClosePopup();
      break;

    case "iou":
      utils.longWait();
      utils.longWait();
      utils.mediumWait();
      utils.doubleBackN(3, function () {
        return tryClosePopup() || isDayDayEarnPeaPage();
      });
      break;
  }
  return true;
}

function handleHeadlineFastClaim() {
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
}

function enterDailyEarnPea() {
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

  tryClosePopup();

  scrollDown();
  utils.miniWait();
  scrollDown();
  utils.miniWait();

  return true;
}

function backFromDailyEarnPea() {
  utils.backN(5);
}

function tryClosePopup() {
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

function isDayDayEarnPeaPage() {
  let title = text("做任务开福袋").findOne(200);
  let subTitle = text("做任务赚京豆").findOne(200);
  return !!(title && subTitle);
}

module.exports = {
  run,
};
