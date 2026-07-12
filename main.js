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

function getSelectedSections() {
  let sections = [];
  if (ui.igHot.isChecked()) sections.push("热门游戏");
  if (ui.igDaily.isChecked()) sections.push("每日必玩");
  if (ui.igRecommend.isChecked()) sections.push("好游推荐");
  if (ui.igGuess.isChecked()) sections.push("猜你喜欢");
  if (ui.igDiscover.isChecked()) sections.push("发现更多");
  if (ui.igNew.isChecked()) sections.push("游戏尝鲜");
  return sections.length > 0 ? sections : null;
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

    {/* 互动游戏控制区域 */}
    <card margin="5" cardCornerRadius="8" cardElevation="2">
      <vertical padding="10">
        <text text="互动游戏" textSize="16sp" textStyle="bold" marginBottom="5" />
        <text text="执行分区:" textSize="14sp" marginBottom="5" />
        <horizontal gravity="center_vertical" wrap="wrap">
          <checkbox id="igHot" text="热门游戏" />
          <checkbox id="igDaily" text="每日必玩" marginLeft="10" />
        </horizontal>
        <horizontal gravity="center_vertical" wrap="wrap">
          <checkbox id="igRecommend" text="好游推荐" />
          <checkbox id="igGuess" text="猜你喜欢" marginLeft="10" />
        </horizontal>
        <horizontal gravity="center_vertical" wrap="wrap">
          <checkbox id="igDiscover" text="发现更多" />
          <checkbox id="igNew" text="游戏尝鲜" marginLeft="10" />
        </horizontal>
        <horizontal gravity="center_vertical" marginTop="5">
          <checkbox id="igtest" text="测试模式" />
          <checkbox id="igtimer" text="定时执行" marginLeft="20" />
        </horizontal>
        <button id="igrun" text="运行互动游戏" margin="0 5 0 0" />
      </vertical>
    </card>

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

    // 获取选中的分区
    let selectedSections = getSelectedSections();
    console.log(`selected sections: ${selectedSections || "全部分区"}`);

    // 定时执行
    if (ui.igtimer.checked) {
      const { interactive_games: igConfig } = require("./modules/config");
      const waitTime = ut.getTimeToTarget(igConfig.hour, igConfig.minute);
      ut.preciseSleep(waitTime, true);
    }

    // 执行游戏
    ig.run(ui.igtest.checked, selectedSections);
  });
});

ui.exit.click(() => exit());
