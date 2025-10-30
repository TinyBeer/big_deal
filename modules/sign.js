const {
  longWait,
  miniWait,
  shortWait,
  mediumWait,
  info,
  doubleBackN,
} = require("./utils");

function run() {
  info("每日签到任务 开始...");
  mediumWait();

  chaina_telecom_cloud_pan();
  state_grid_online();
  smzdm();

  info("每日签到任务 结束");
}

function smzdm() {
  let appName = "什么值得买";
  info(`${appName}...`);

  app.launchApp(appName);
  longWait();

  if (id("dialog_home_close").exists()) {
    id("dialog_home_close").findOne().click();
  }
  sleep(1000);

  let mine = text("我的").findOne(100);
  if (!mine) {
    console.log("missing mine entry, skip");
    return false;
  }
  click(mine.center());
  mediumWait();

  let signEntry = text("签到领奖").findOne(100);
  if (!signEntry) {
    console.log("missing sign entry, skip");
    return false;
  }
  click(signEntry.center());
  mediumWait()

  doubleBackN(2);
}

function state_grid_online() {
  let appName = "网上国网";
  info(`${appName}...`);

  app.launchApp(appName);
  longWait();

  var signBtn = text("签到").findOne(10000);
  if (!signBtn) {
    info("missing sign button, skip...");
  }
  click(signBtn.center());
  mediumWait();

  doubleBackN(2);
  shortWait();
}

function chaina_telecom_cloud_pan() {
  let appName = "天翼云盘";
  info(`${appName}...`);

  app.launchApp(appName);
  longWait();

  if (id("ivCancel").exists()) {
    id("ivCancel").findOne().click();
  }

  //className("android.view.View").desc("我的服务").waitFor();
  var imageViews = className("android.widget.ImageView")
    .clickable(true)
    .depth(13)
    .find();
  if (imageViews.length === 1) {
    className("android.widget.ImageView")
      .clickable(true)
      .depth(13)
      .findOne()
      .click();
    shortWait();
  }

  click(970, 2270);
  className("android.view.View").desc("每日签到\n最高领500M").findOne().click();
  shortWait();

  id("close_icon").waitFor();
  id("close_icon").findOne().click();
  miniWait();
  back();
  back();
  mediumWait();
}

module.exports = {
  run,
};
