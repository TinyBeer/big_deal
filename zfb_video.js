const x = 500;
const sy = 1000;
const ey = 300;
const dur = 300;
for (let idx = 0; idx < 150; idx++) {
  // let r = random();
  // console.log(r);
  // let flag = r > 0.5;
  let flag = true;
  while (flag) {
    flag = false;
    swipe(x, sy, x, ey, dur);
    sleep(5000);
    let btn = textContains("进入直播间").findOne(100);
    flag = btn != null;
  }

  if (
    textContains("依次点击").findOne(100) ||
    textContains("为保障您的正常访问请进行验证").findOne(100)
  ) {
    notice("支付宝浏览视频", "真人验证");
    confirm("真人验证提示", "确认");
  }

  if (text("已领完").findOne(100) || text("明日可领").findOne(100)) {
    notice("支付宝浏览视频", "任务完成");
    confirm("任务完成提示", "确认");
  }
  sleep(10000);
}
notice("支付宝", "mission complete");
