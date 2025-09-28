function run() {
  app.launchApp("中国移动");
  sleep(8000);
  //text('熊猫乐园').findOne().click();
  click(948, 1057);
  sleep(12000);
  click(100, 2200);

  for (var i = 0; i < 12; i++) {
    sleep(4000);
    click(920, 1950);
    sleep(12000);
    back();
  }
}

module.exports = {
  run,
};
