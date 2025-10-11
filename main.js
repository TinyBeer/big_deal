"ui";

// 声明使用UI
auto();

ui.layout(
  <vertical gravity="center_vertical">
    <button id="sign" text="签到任务" margin="5" />
    <horizontal gravity="left">
      <button id="jd" text="京东" margin="5" />
      <button id="jdm" text="京东 手动" margin="5" />
      <button id="star" text="超级明星" margin="5" />
    </horizontal>
    <horizontal gravity="left">
      <button id="jdjrm" text="京东金融 手动" margin="5" />
      <button id="ddep" text="天天赚京豆" margin="5" />
      <button id="save" text="省钱中心" margin="5" />
    </horizontal>
    <horizontal gravity="left">
      <button id="igtask" text="互动游戏-任务" margin="5" />
      <button id="igrun" text="互动游戏-运行" margin="5" />
      <checkbox id="igtimer" text="定时"></checkbox>
    </horizontal>
    <button id="panda" text="熊猫乐园" margin="5" />
    <button id="exit" text="退出" margin="5" />
  </vertical>
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
    // ctcp.run();
    // sgo.run();
    // smzdm.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.igtask.click(() => {
  threads.start(() => {
    const ig = require("./modules/jdjr_interactive_games");
    const { interactive_games: igConfig } = require("./modules/config");
    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    ig.task(igConfig.name_list, igConfig.more_task_list);

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.igrun.click(() => {
  threads.start(() => {
    const ut = require("./modules/utils");
    const ig = require("./modules/jdjr_interactive_games");
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

ui.jdm.click(() => {
  threads.start(() => {
    const jd_manual = require("./modules/jd_manual");

    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jd_manual.run();

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

ui.star.click(() => {
  threads.start(() => {
    const star = require("./modules/jd_super_star");
    star.run();
  });
});

ui.exit.click(() => {
  exit();
});

let hotGameTaskList = [
  // round one
  { name: "雀神来也", dur_m: 60 },
  { name: "货柜趣消除", dur_m: 35 },
  { name: "趣味叠叠乐", dur_m: 15 },
  { name: "排队上车", dur_m: 15 },
  { name: "方块拼图", dur_m: 15 },
  { name: "养猪猪", dur_m: 4 },
  { name: "京豆捕鱼", dur_m: 8 },
  { name: "种菜领现金", dur_m: 0 },
  { name: "消灭小萌星", dur_m: 30 },
  { name: "麻将凑十", dur_m: 15 },
  { name: "解压硬币", dur_m: 15 },
  { name: "2048方块", dur_m: 60 },
  { name: "无尽战歌", dur_m: 15 },
  // round two
  { name: "雀神来也", dur_m: 2 },
  { name: "货柜趣消除", dur_m: 2 },
  { name: "趣味叠叠乐", dur_m: 2 },
  { name: "排队上车", dur_m: 2 },
  { name: "方块拼图", dur_m: 2 },
  { name: "养猪猪", dur_m: 5 },
  { name: "京豆捕鱼", dur_m: 0 },
  { name: "种菜领现金", dur_m: 0 },
  { name: "消灭小萌星", dur_m: 2 },
  { name: "麻将凑十", dur_m: 2 },
  { name: "解压硬币", dur_m: 2 },
  { name: "2048方块", dur_m: 2 },
  { name: "无尽战歌", dur_m: 2 },
  { name: "养猪猪", dur_m: 2 },
];
