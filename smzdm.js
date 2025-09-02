function run() {
  app.launchApp("什么值得买");
  sleep(8000);

  if (id("dialog_home_close").exists()) {
    id("dialog_home_close").findOne().click();
  }

  id("iv_left").findOne().click();
  sleep(1000);
  id("ll_login_sign").findOne().click();

  sleep(3000);
  if (id("iv_close").exists()) {
    id("iv_close").findOne().click();
  }
  sleep(1000);
  back();
  back();
}

module.exports = {
  run,
};
