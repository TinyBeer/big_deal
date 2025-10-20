const x = 500;
const sy = 1000;
const ey = 300;
const dur = 300;
for (let idx = 0; idx < 50; idx++) {
  let flag = true;
  while (flag) {
    flag = false;
    swipe(x, sy, x, ey, dur);
    sleep(5000);
    let btn = textContains("进入直播间").findOne(500);
    flag = btn != null;
  }

  let check = textContains("依次点击").findOne(500);
  if (check) {
    notice("支付宝浏览视频", "真人验证");
    confirm("真人验证提示", "确认");
  }
  sleep(10000);
  let r = random();
  console.log(r);
  if (r > 0.5) {
    sleep(2000 + r * 10000);
  }
}
