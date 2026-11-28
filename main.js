"ui";

// 声明使用UI
auto();

const { runTask, storeConfig, loadConfig } = require("./modules/utils");
const logger = require("./modules/lib/logger");

const LOG_LEVEL_KEYS = ["debug", "info", "warn", "error"];
const LOG_LEVEL_LABELS = { debug: "调试", info: "信息", warn: "警告", error: "错误" };
const LOG_LEVEL_KEY = "logLevel";

let initialLevelIdx = LOG_LEVEL_KEYS.indexOf(loadConfig(LOG_LEVEL_KEY));
if (initialLevelIdx < 0) initialLevelIdx = 0;
logger.setLevel(LOG_LEVEL_KEYS[initialLevelIdx]);

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

/* ---- 主题样式 ---- */

const C = {
  bg: "#12151C",
  surface: "#1E2430",
  border: "#2B3342",
  primary: "#E1251B",
  primaryLight: "#F04335",
  primaryDark: "#C21810",
  text: "#F1F3F7",
  textDim: "#98A2B3",
  btn: "#2A3140",
  btnBorder: "#374154",
};

ui.layout(
  <vertical background={C.bg} padding="16 18 24 18">

      {/* 顶部标题 */}
      <vertical marginBottom="18">
        <horizontal gravity="center_vertical">
          <view w="4" h="24" background={C.primary} marginRight="10" />
          <text text="京东任务助手" textSize="22sp" textColor={C.text} textStyle="bold" />
        </horizontal>
        <text
          text="每日任务 · 一键控制台"
          textSize="12sp"
          textColor={C.textDim}
          marginLeft="14"
          marginTop="4"
        />
      </vertical>

      {/* 京东商城 */}
      <vertical id="cardShop" background={C.surface} padding="14 12 12 12">
        <horizontal gravity="center_vertical">
          <view w="3" h="14" background={C.primary} marginRight="8" />
          <text text="京东商城" textSize="14sp" textColor={C.text} textStyle="bold" />
        </horizontal>
        <horizontal marginTop="10" w="*">
          <button id="jd" text="京东" w="0" h="42" layout_weight="1" textSize="12sp" />
          <button id="jddddb" text="国补" w="0" h="42" layout_weight="1" textSize="12sp" marginLeft="8" />
          <button id="jd121" text="121京豆" w="0" h="42" layout_weight="1" textSize="12sp" marginLeft="8" />
          <button id="wujincheng" text="五金城" w="0" h="42" layout_weight="1" textSize="12sp" marginLeft="8" />
        </horizontal>
        <button id="jdmedical" text="看病买药任务" w="*" h="42" textSize="12sp" marginTop="8" />
      </vertical>

      {/* 互动游戏 */}
      <vertical id="cardGame" background={C.surface} padding="14 12 12 12" marginTop="14">
        <horizontal gravity="center_vertical">
          <view w="3" h="14" background={C.primary} marginRight="8" />
          <text text="互动游戏" textSize="14sp" textColor={C.text} textStyle="bold" />
        </horizontal>
        <button
          id="jdig"
          text="启动京东互动游戏"
          w="*"
          h="48"
          textSize="15sp"
          textStyle="bold"
          marginTop="10"
        />

        {/* 京东金融互动游戏控制 */}
        <text text="金融互动游戏 · 执行分区" textSize="12sp" textColor={C.textDim} marginTop="14" marginBottom="6" />
        <horizontal gravity="center_vertical" wrap="wrap">
          <checkbox id="igHot" text="热门游戏" textColor={C.text} />
          <checkbox id="igDaily" text="每日必玩" textColor={C.text} marginLeft="10" />
        </horizontal>
        <horizontal gravity="center_vertical" wrap="wrap" marginTop="2">
          <checkbox id="igRecommend" text="好游推荐" textColor={C.text} />
          <checkbox id="igGuess" text="猜你喜欢" textColor={C.text} marginLeft="10" />
        </horizontal>
        <horizontal gravity="center_vertical" wrap="wrap" marginTop="2">
          <checkbox id="igDiscover" text="发现更多" textColor={C.text} />
          <checkbox id="igNew" text="游戏尝鲜" textColor={C.text} marginLeft="10" />
        </horizontal>
        <horizontal gravity="center_vertical" marginTop="6">
          <checkbox id="igtest" text="测试模式" textColor={C.textDim} />
          <checkbox id="igtimer" text="定时执行" textColor={C.textDim} marginLeft="20" />
        </horizontal>
        <button id="igrun" text="运行金融互动游戏" w="*" h="42" textSize="13sp" marginTop="8" />
      </vertical>

      {/* 京东金融 */}
      <vertical id="cardJr" background={C.surface} padding="14 12 12 12" marginTop="14">
        <horizontal gravity="center_vertical">
          <view w="3" h="14" background={C.primary} marginRight="8" />
          <text text="京东金融" textSize="14sp" textColor={C.text} textStyle="bold" />
        </horizontal>
        <horizontal marginTop="10" w="*">
          <button id="jdjrm" text="手动签到" w="0" h="42" layout_weight="1" textSize="12sp" />
          <button id="ddep" text="天天赚京豆" w="0" h="42" layout_weight="1" textSize="12sp" marginLeft="8" />
          <button id="save" text="省钱中心" w="0" h="42" layout_weight="1" textSize="12sp" marginLeft="8" />
        </horizontal>
      </vertical>

      {/* 日志等级 */}
      <horizontal marginTop="14" w="*" gravity="center_vertical">
        <text text="日志等级" textSize="13sp" textColor={C.textDim} layout_weight="1" />
        <spinner id="logLevel" entries="调试|信息|警告|错误" w="150" />
      </horizontal>

      {/* 其他 */}
      <horizontal marginTop="14" w="*">
        <button id="exit" text="退出" w="*" h="42" textSize="12sp" />
      </horizontal>

  </vertical>,
);

/* ---- 应用圆角/配色 ---- */

const density = context.getResources().getDisplayMetrics().density;
function dp(v) {
  return Math.round(v * density);
}
function color(hex) {
  return android.graphics.Color.parseColor(hex);
}
function rounded(id, fill, radius, stroke, strokeWidth) {
  let v = ui[id];
  if (!v) return;
  let gd = new android.graphics.drawable.GradientDrawable();
  gd.setColor(color(fill));
  gd.setCornerRadius(dp(radius));
  if (stroke) gd.setStroke(dp(strokeWidth || 1), color(stroke));
  v.setBackground(gd);
}
function gradient(id, from, to, radius) {
  let v = ui[id];
  if (!v) return;
  let gd = new android.graphics.drawable.GradientDrawable();
  gd.setOrientation(android.graphics.drawable.GradientDrawable.Orientation.LEFT_RIGHT);
  gd.setColors([color(from), color(to)]);
  gd.setCornerRadius(dp(radius));
  v.setBackground(gd);
}
function tintCheck(id) {
  let v = ui[id];
  if (!v || !v.setButtonTintList) return;
  try {
    v.setButtonTintList(android.content.res.ColorStateList.valueOf(color(C.primary)));
  } catch (e) {}
}

["cardShop", "cardGame", "cardJr"].forEach((id) => rounded(id, C.surface, 14, C.border, 1));

[
  "jd", "jddddb", "jd121", "wujincheng", "jdmedical",
  "jdjrm", "ddep", "save", "exit", "igrun",
].forEach((id) => {
  rounded(id, id === "igrun" ? C.primaryDark : C.btn, 10, id === "igrun" ? null : C.btnBorder, 1);
  ui[id].setTextColor(color(C.text));
});

gradient("jdig", C.primaryLight, C.primaryDark, 12);
ui.jdig.setTextColor(color("#FFFFFF"));

[
  "igHot", "igDaily", "igRecommend", "igGuess", "igDiscover", "igNew", "igtest", "igtimer",
].forEach(tintCheck);

/* ---- 日志等级选择 ---- */
let logLevelSyncing = true;
ui.logLevel.setOnItemSelectedListener(
  new android.widget.AdapterView.OnItemSelectedListener({
    onItemSelected: function (parent, view, position, id) {
      if (logLevelSyncing) return;
      let level = LOG_LEVEL_KEYS[position];
      logger.setLevel(level);
      storeConfig(LOG_LEVEL_KEY, level);
      toast("日志等级：" + LOG_LEVEL_LABELS[level]);
    },
    onNothingSelected: function () {},
  }),
);
ui.logLevel.setSelection(initialLevelIdx);
ui.post(() => {
  logLevelSyncing = false;
});

ui.jd.click(() => startTask(require("./modules/jd").run, "京东"));
ui.jddddb.click(() =>
  startTask(require("./modules/jd_day_day_benefit").run, "国补"),
);
ui.jd121.click(() => startTask(require("./modules/jd_121pea").run, "121京豆"));
ui.wujincheng.click(() =>
  startTask(require("./modules/jd_daily_browse_tasks").run, "五金城"),
);
ui.jdmedical.click(() =>
  startTask(require("./modules/jd_h5_browse_beans").run, "看病买药"),
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
