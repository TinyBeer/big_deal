function sign() {
  console.log("网上国网签到...");
  app.launchApp("网上国网");
  var signBtn = text("签到").findOne();
  sleep(4000);
  click(540, 1552);
  sleep(8000);
  back();
  back();
}

module.exports = {
  sign,
};
