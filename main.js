"ui";

// 声明使用UI
auto();

ui.layout(
  <vertical gravity="center_vertical">
    <button id="sign" text="签到任务" margin="5" />
    <horizontal gravity="left">
      <button id="jd" text="京东" margin="5" />
      <button id="jdbb" text="京东-抽盲盒" margin="5" />
      <button id="jddddb" text="京东-天天抽福利" margin="5" />
    </horizontal>
    <horizontal>
      <button id="jd121" text="121京豆" margin="5" />
      <button id="jdst" text="刮卡任务" margin="5" />
      <button id="jdss" text="超级明星" margin="5" />
      <button id="jdig" text="互动游戏" margin="5" />
    </horizontal>
    <horizontal gravity="left">
      <button id="jdjrm" text="京东金融 手动" margin="5" />
      <button id="ddep" text="天天赚京豆" margin="5" />
      <button id="save" text="省钱中心" margin="5" />
    </horizontal>
    <horizontal gravity="left">
      <button id="igrun" text="互动游戏-运行" margin="5" />
      <checkbox id="igtimer" text="定时"></checkbox>
    </horizontal>
    <button id="panda" text="熊猫乐园" margin="5" />
    <button id="exit" text="退出" margin="5" />
  </vertical>,
);

ui.sign.click(() => {
  threads.start(() => {
    const sign = require("./modules/sign");
    // const smzdm = require("./modules/smzdm");
    // const ctcp = require("./modules/china_telecom_cloud_pan");
    // const sgo = require("./modules/state_grid_online");
    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    sign.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.igrun.click(() => {
  threads.start(() => {
    const ut = require("./modules/utils");
    const ig = require("./modules/jdjr_interactive_games");
    const jdn = require("./modules/jd_night");
    const { interactive_games: igConfig } = require("./modules/config");

    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    /* waiting until specific time */
    const waitTime = ut.getTimeToTarget(igConfig.houre, igConfig.minute);
    if (ui.igtimer.checked) {
      ut.preciseSleep(waitTime, true);
    }

    ig.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.jd.click(() => {
  threads.start(() => {
    const jd = require("./modules/jd");

    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jd.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.jdig.click(() => {
  threads.start(() => {
    const jdig = require("./modules/jd_interactive_games");

    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jdig.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.ddep.click(() => {
  threads.start(() => {
    const jdjr_ep = require("./modules/jdjr_earn_pea");
    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jdjr_ep.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.save.click(() => {
  threads.start(() => {
    const jdjr_sc = require("./modules/jdjr_save_center");

    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jdjr_sc.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.jdjrm.click(() => {
  threads.start(() => {
    const jdjrm = require("./modules/jdjr_manual");

    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jdjrm.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.panda.click(() => {
  threads.start(() => {
    const panda = require("./modules/china_mobile");

    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    panda.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.jdbb.click(() => {
  threads.start(() => {
    const jdbb = require("./modules/jd_bline_box");
    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jdbb.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.jddddb.click(() => {
  threads.start(() => {
    const jddddb = require("./modules/jd_day_day_benefit");
    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jddddb.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.jdss.click(() => {
  threads.start(() => {
    const jdss = require("./modules/jd_super_star");
    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jdss.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.jd121.click(() => {
  threads.start(() => {
    const jd121 = require("./modules/jd_121pea");
    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jd121.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.jdst.click(() => {
  threads.start(() => {
    const jdst = require("./modules/jd_scratch_task");
    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jdst.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.exit.click(() => {
  exit();
});
