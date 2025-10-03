"ui"; // 声明使用UI
auto();

ui.layout(
  <vertical>
    <button id="sign" text="签到任务" />
    <horizontal>
      <button id="jdjr" text="京东金融-互动游戏" />
      <checkbox id="jdjrtimer">定时</checkbox>
    </horizontal>
    <button id="jd" text="京东" />
    <button id="jdm" text="京东 手动" />
    <button id="ddep" text="天天赚京豆" />
    <button id="test" text="test" />
    <button id="exit" text="退出" />
  </vertical>
);

ui.sign.click(() => {
  threads.start(() => {
    const smzdm = require("./modules/smzdm");
    const ctcp = require("./modules/china_telecom_cloud_pan");
    const sgo = require("./modules/state_grid_online");
    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    ctcp.run();
    sgo.run();
    smzdm.run();

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.jdjr.click(() => {
  threads.start(() => {
    const ut = require("./modules/utils");
    const jdjr = require("./modules/jdjr");
    const screenSize = ut.getScreenSize();
    const targetHour = 0; // 目标小时（24小时制，如 20 代表晚上 8 点）
    const targetMinute = 5; // 目标分钟
    /* config */
    let nameList = [
      // "雀神来也",
      // "货柜趣消除",
      // "趣味叠叠乐",
      // "排队上车",
      // "方块拼图",
      // "养猪猪",
      // "消灭小萌星",
      // "麻将凑十",
      // "解压硬币",
      // "2048方块",
      // "无尽战歌",
    ];
    let moreGameTaskList = [
      { scroll: true },
      // // round one
      { name: "百炼飞仙", dur_m: 15 },
      { name: "毛线大师", dur_m: 15 },
      { name: "点点2048", dur_m: 15 },
      { name: "合成原始人", dur_m: 15 },
      { name: "无尽泡泡龙", dur_m: 15 },
      { name: "打螺丝王者", dur_m: 15 },
      { name: "数字喜加1", dur_m: 15 },
      // { name: "纸牌接龙", dur_m: 15 },
      { name: "战争之王", dur_m: 15 },
      // { name: "喵喵十消", dur_m: 15 },
      // { name: "超级连连看", dur_m: 15 },
      // round two
      { name: "百炼飞仙", dur_m: 2 },
      { name: "毛线大师", dur_m: 2 },
      { name: "点点2048", dur_m: 1 },
      { name: "合成原始人", dur_m: 1 },
      { name: "无尽泡泡龙", dur_m: 1 },
      { name: "打螺丝王者", dur_m: 1 },
      { name: "数字喜加1", dur_m: 1 },
      // { name: "纸牌接龙", dur_m: 1 },
      { name: "战争之王", dur_m: 1 },
      // { name: "喵喵十消", dur_m: 1 },
      // { name: "超级连连看", dur_m: 1 },
    ];
    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");
    /* waiting until specific time */
    const waitTime = ut.getTimeToTarget(targetHour, targetMinute);
    if (ui.jdjrtimer.checked) {
      ut.preciseSleep(waitTime, true);
    }
    jdjr.run(screenSize, nameList, moreGameTaskList);
    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.jd.click(() => {
  threads.start(() => {
    const ut = require("./modules/utils");
    const screenSize = ut.getScreenSize();
    const jd = require("./modules/jd");

    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jd.run(screenSize);

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.jdm.click(() => {
  threads.start(() => {
    const ut = require("./modules/utils");
    const screenSize = ut.getScreenSize();

    const jd_manual = require("./modules/jd_manual");
    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jd_manual.run(screenSize);

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.ddep.click(() => {
  threads.start(() => {
    const jdjr_ep = require("./modules/jdjr_earn_pea");
    const ut = require("./modules/utils");
    const screenSize = ut.getScreenSize();
    /* keep screen on */
    device.keepScreenOn();
    console.log("已开启屏幕常亮");

    jdjr_ep.run(screenSize);

    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
});

ui.test.click(() => {
  threads.start(() => {
    console.log("test");
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
