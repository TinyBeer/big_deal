sign();

function sign() {
  console.log("什么值得买签到...");

  app.launchApp("什么值得买");
  sleep(8000);

  if (id("dialog_home_close").exists()) {
    id("dialog_home_close").findOne().click();
  }
  sleep(1000);

  const signBtn = id("pag_left").findOne(1000);
  if (!signBtn) {
    console.log("not found sign button, skip");
    return;
  }
  click(signBtn.center());
  sleep(1000);

  const closeBtn = id("iv_close").findOne(1000);
  if (!closeBtn) {
    console.log("smzdm sign failed!!!");
    back();
    back();
    sleep(1000);
    return;
  }

  click(closeBtn.center());
  sleep(1000);

  back();
  back();
  sleep(1000);
}
