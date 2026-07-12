"ui";

// 声明使用UI
auto();

function startTask(taskFn) {
  threads.start(() => {
    device.keepScreenOn();
    console.log("已开启屏幕常亮");
    taskFn();
    device.cancelKeepingAwake();
    console.log("已关闭屏幕常亮");
  });
}

ui.layout(
  <vertical gravity="center_vertical">
    <button id="sign" text="签到任务" margin="5" />
    <horizontal gravity="left">
      <button id="jd" text="京东" margin="5" />
      <button id="jdbb" text="京东-抽盲盒" margin="5" />
      <button id="jddddb" text="京东-国补" margin="5" />
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
      <checkbox id="igtest" text="测试"></checkbox>
    </horizontal>
    <button id="panda" text="熊猫乐园" margin="5" />
    <button id="exit" text="退出" margin="5" />
  </vertical>,
);

ui.sign.click(() => startTask(require("./modules/sign").run));
ui.jd.click(() => startTask(require("./modules/jd").run));
ui.jdbb.click(() => startTask(require("./modules/jd_bline_box").run));
ui.jddddb.click(() => startTask(require("./modules/jd_day_day_benefit").run));
ui.jd121.click(() => startTask(require("./modules/jd_121pea").run));
ui.jdst.click(() => startTask(require("./modules/jd_scratch_task").run));
ui.jdss.click(() => startTask(require("./modules/jd_super_star").run));
ui.jdig.click(() => startTask(require("./modules/jd_interactive_games").run));
ui.ddep.click(() => startTask(require("./modules/jdjr_earn_pea").run));
ui.save.click(() => startTask(require("./modules/jdjr_save_center").run));
ui.jdjrm.click(() => startTask(require("./modules/jdjr_manual").run));
ui.panda.click(() => startTask(require("./modules/china_mobile").run));

ui.igrun.click(() => {
  startTask(() => {
    const ut = require("./modules/utils");
    const ig = require("./modules/jdjr_interactive_games");
    const { interactive_games: igConfig } = require("./modules/config");

    const waitTime = ut.getTimeToTarget(igConfig.hour, igConfig.minute);
    if (ui.igtimer.checked) {
      ut.preciseSleep(waitTime, true);
    }

    ig.run(ui.igtest.checked);
  });
});

ui.exit.click(() => exit());
