"ui";

// 声明使用UI
auto();

const { runTask } = require("./modules/utils");

function startTask(taskFn, label) {
  threads.start(() => {
    runTask(taskFn, { label: label || "task" });
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
  return sections;
}

ui.layout(
  <vertical gravity="center_vertical">
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

ui.jd.click(() => startTask(require("./modules/jd").run, "京东"));
ui.jdbb.click(() => startTask(require("./modules/jd_bline_box").run, "抽盲盒"));
ui.jddddb.click(() =>
  startTask(require("./modules/jd_day_day_benefit").run, "国补"),
);
ui.jd121.click(() => startTask(require("./modules/jd_121pea").run, "121京豆"));
ui.jdst.click(() =>
  startTask(require("./modules/jd_scratch_task").run, "刮卡任务"),
);
ui.jdss.click(() =>
  startTask(require("./modules/jd_super_star").run, "超级明星"),
);
ui.jdig.click(() =>
  startTask(require("./modules/jd_interactive_games").run, "互动游戏"),
);
ui.ddep.click(() =>
  startTask(require("./modules/jdjr_earn_pea").run, "天天赚京豆"),
);
ui.save.click(() => startTask(require("./modules/jdjr_save_center").run, "省钱中心"));
ui.jdjrm.click(() =>
  startTask(require("./modules/jdjr_manual").run, "金融手动"),
);
ui.panda.click(() =>
  startTask(require("./modules/china_mobile").run, "熊猫乐园"),
);

ui.igrun.click(() => {
  startTask(() => {
    const ut = require("./modules/utils");
    const ig = require("./modules/jdjr_interactive_games");

    // 获取选中的分区
    let selectedSections = getSelectedSections();
    if (selectedSections.length === 0) {
      ut.info("未选择分区，已取消");
      return;
    }
    console.log(`selected sections: ${selectedSections.join("、")}`);

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
