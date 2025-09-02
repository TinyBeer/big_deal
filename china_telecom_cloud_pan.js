function run() {
  app.launchApp("天翼云盘");
  sleep(9000);

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
  }

  sleep(1000);
  click(970, 2270);
  className("android.view.View").desc("每日签到\n最高领500M").findOne().click();
  sleep(500);
  id("close_icon").waitFor();
  id("close_icon").findOne().click();
  sleep(1000);
  back();
  back();
  sleep(1000);
}

module.exports = {
  run,
};
