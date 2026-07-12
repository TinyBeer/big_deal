/* import */

const {
  longWait,
  backN,
  doubleBackN,
  // getScreenSize,
  preciseSleep,
  shortWait,
  miniWait,
  matchImage,
} = require("./utils");

// 分区定义
const SECTIONS = {
  HOT: "热门游戏",
  DAILY: "每日必玩",
  RECOMMEND: "好游推荐",
  GUESS: "猜你喜欢",
  DISCOVER: "发现更多",
  NEW: "游戏尝鲜",
};

// 按分区组织的游戏任务
const tasksBySection = {
  [SECTIONS.HOT]: [
    // { name: "拯救蜜蜂狗", dur_m: 15 },
    // { name: "螺丝大师", dur_m: 15 },
    { name: "雀神来也", dur_m: 60 },
    { name: "解压硬币", dur_m: 15 },
    { name: "货柜趣消除", dur_m: 15 },
    { name: "2048方块", dur_m: 30 },
    { name: "方块拼图", dur_m: 15 },
  ],

  [SECTIONS.DAILY]: [
    { name: "养猪猪", dur_m: 7 },
    { name: "财富庄园", dur_m: 7 },
    { name: "京豆捕鱼", dur_m: 7 },
    { name: "消灭小萌星", dur_m: 30 },
    { name: "无尽泡泡龙", dur_m: 20 },
    { name: "趣味叠叠乐", dur_m: 30 },
    { name: "数字喜加1", dur_m: 20 },
    { name: "排队上车", dur_m: 30 },
  ],

  [SECTIONS.RECOMMEND]: [
    { name: "百炼飞仙", dur_m: 20 },
    { name: "神域战纪", dur_m: 15 },
    { name: "麻将凑十", dur_m: 30 },
    { name: "点点2048", dur_m: 30 },
    { name: "毛线大师", dur_m: 30 },
    { name: "城堡消消乐", dur_m: 20 },
    { name: "淘沙大师", dur_m: 15 },
  ],

  [SECTIONS.GUESS]: [
    { name: "喵喵十消", dur_m: 15 },
    { name: "3D拆螺丝", dur_m: 15 },
    { name: "水果对对消", dur_m: 15 },
    { name: "超级连连看", dur_m: 20 },
  ],

  [SECTIONS.DISCOVER]: [
    { name: "无尽战歌", dur_m: 15 },
    { name: "麻将滑滑乐", dur_m: 15 },
    { name: "拼图接龙", dur_m: 15 },
    { name: "像素射手", dur_m: 15 },
    { name: "无尽水排序", dur_m: 15 },
    { name: "家园连连看", dur_m: 15 },
    { name: "川味消消乐", dur_m: 15 },
    { name: "鲜花泡泡", dur_m: 15 },
    { name: "箭头贪吃蛇", dur_m: 15 },
    { name: "水果消块块", dur_m: 15 },
    { name: "鲜花点点消", dur_m: 15 },
    { name: "疯狂的螺丝", dur_m: 15 },
    { name: "纸牌", dur_m: 15 },
    { name: "积木咖啡店", dur_m: 15 },
    { name: "我要开餐厅", dur_m: 15 },
    { name: "悟空超市", dur_m: 15 },
    { name: "纸牌接龙", dur_m: 15 },
    { name: "动物排排队", dur_m: 15 },
    { name: "战争之王", dur_m: 15 },
    { name: "打螺丝王者", dur_m: 15 },
    { name: "水果装盘盘", dur_m: 15 },
    { name: "麻将对对碰", dur_m: 15 },
    { name: "合成原始人", dur_m: 15 },
    { name: "超级消球球", dur_m: 15 },
    { name: "2248", dur_m: 15 },
    { name: "箭头小画家", dur_m: 15 },
    { name: "三连纸牌", dur_m: 15 },
    { name: "小小餐吧", dur_m: 15 },
    { name: "鲜花消消", dur_m: 15 },
    { name: "合成2048", dur_m: 15 },
    { name: "东方宝石合成", dur_m: 15 },
    { name: "连了个连", dur_m: 15 },
    { name: "连线消消乐", dur_m: 15 },
    { name: "养了个羊", dur_m: 15 },
    { name: "进化大作战", dur_m: 15 },
    { name: "丛林爱消除", dur_m: 15 },
    { name: "最强螺丝王", dur_m: 15 },
    { name: "JJ斗地主", dur_m: 15 },
    { name: "掼蛋", dur_m: 15 },
    { name: "象棋大师", dur_m: 15 },
    { name: "贪吃蛇", dur_m: 15 },
    { name: "高尔夫3D", dur_m: 15 },
    { name: "呆萌足球队", dur_m: 15 },
  ],

  [SECTIONS.NEW]: [
    // { name: "禅意五子棋", dur_m: 15 },
    // { name: "3D跳一跳", dur_m: 15 },
    // { name: "答案之书", dur_m: 15 },
    // { name: "超载战线", dur_m: 15 },
  ],
};

// 所有游戏任务（扁平化）
const igtasks = Object.values(tasksBySection).flat();

/**
 * 运行游戏任务
 * @param {boolean} isTest - 是否为测试模式（缩短游戏时间）
 * @param {string|Array<string>} sections - 要执行的分区名称或分区名称数组
 *                                        不传则执行所有分区
 *                                        可用分区: SECTIONS 中的值
 *                                        例如: "热门游戏" 或 ["热门游戏", "发现更多"]
 */
function run(isTest, sections) {
  app.launchApp("京东金融");
  longWait();

  // enter interactive games
  let entered = enterInteractiveGames();
  if (!entered) {
    console.log("failed to enter interactive games, retrying...");
    backN(2);
    shortWait();
    entered = enterInteractiveGames();
    if (!entered) {
      console.log("still cannot enter interactive games, exit");
      return;
    }
  }

  // 根据分区筛选任务
  let tasksToRun = filterTasksBySection(sections);
  console.log(`running ${tasksToRun.length} tasks from section: ${sections || "all"}`);

  workWithName(tasksToRun, isTest);

  backN(2);
  doubleBackN(1);
}

/**
 * 根据分区名称筛选任务
 * @param {string|Array<string>} sections - 分区名称或分区名称数组
 * @returns {Array} 筛选后的任务列表
 */
function filterTasksBySection(sections) {
  // 如果没有指定分区，返回所有任务
  if (!sections) {
    return igtasks;
  }

  // 将单个分区名称转换为数组
  let sectionList = Array.isArray(sections) ? sections : [sections];

  // 收集指定分区的所有任务
  let filteredTasks = [];
  for (let section of sectionList) {
    if (tasksBySection[section]) {
      filteredTasks = filteredTasks.concat(tasksBySection[section]);
    } else {
      console.log(`unknown section: ${section}`);
    }
  }

  return filteredTasks;
}

/**
 * 检测发现更多分区中指定游戏是否有雷电标记
 * 雷电标记位于游戏图标的右上角
 * @param {string} gameName - 游戏名称
 * @returns {boolean} 是否有雷电标记
 */
function hasLightningMark(gameName) {
  let entry = textContains(gameName).findOne(1000);
  if (!entry) {
    return false;
  }

  // 获取游戏图标区域（游戏名称的父级容器中的第一个图片元素）
  let parent = entry.parent();
  if (!parent) {
    return false;
  }

  // 尝试找到游戏图标（通常是父容器中的 ImageView）
  let icon = null;
  for (let i = 0; i < parent.childCount(); i++) {
    let child = parent.child(i);
    if (child && child.className() === "android.widget.ImageView") {
      icon = child;
      break;
    }
  }

  if (!icon) {
    // 如果找不到图标，使用文本位置的左上方区域
    let bounds = entry.bounds();
    let iconRegion = [
      Math.max(0, bounds.left - 120),
      Math.max(0, bounds.top - 30),
      bounds.left,
      bounds.bottom + 30
    ];
    return checkLightningInRegion(iconRegion);
  }

  // 雷电标记位于图标的右上角
  let iconBounds = icon.bounds();
  let lightningRegion = [
    iconBounds.right - 40,
    iconBounds.top,
    iconBounds.right,
    iconBounds.top + 40
  ];

  return checkLightningInRegion(lightningRegion);
}

/**
 * 在指定区域内检测雷电标记
 * @param {Array} region - [x1, y1, x2, y2]
 * @returns {boolean} 是否检测到雷电标记
 */
function checkLightningInRegion(region) {
  let screenImg = images.captureScreen();
  if (!screenImg) {
    console.log("screenshot failed");
    return false;
  }

  let result = matchImage(screenImg, "templates/lightning.png", region, 0.7);
  screenImg.recycle();

  return result !== null;
}

function workWithName(objList, isTest) {
  // 获取发现更多分区的游戏名称列表
  const discoverGames = tasksBySection[SECTIONS.DISCOVER].map(t => t.name);

  for (let i = 0; i < objList.length; i++) {
    let e = objList[i];

    console.log(`play [${e.name}] ${e.dur_m} minute`);
    var dur = e.dur_m * 60 * 1000;
    if (dur == 0) {
      console.log("task time == " + dur + " skip task");
      continue;
    }
    let tmp = textContains(e.name).findOne(1000);
    if (!tmp) {
      console.log(`can not found [${e.name}], skip`);
      continue;
    }
    let scrollAttempts = 0;
    const maxScrollAttempts = 20;
    while (tmp && (tmp.center().y > 2200 || tmp.center().y < 200) && scrollAttempts < maxScrollAttempts) {
      if (tmp.center().y > 2200) {
        scrollDown();
      } else {
        scrollUp();
      }
      shortWait();
      tmp = textContains(e.name).findOne(1000);
      scrollAttempts++;
    }
    if (!tmp) {
      console.log(`can not found [${e.name}] after scroll, skip`);
      continue;
    }

    // 发现更多分区的游戏需要动态检测雷电标记（滚动到可见区域后再检测）
    if (discoverGames.includes(e.name)) {
      console.log(`checking lightning mark for [${e.name}]...`);
      if (!hasLightningMark(e.name)) {
        console.log(`[${e.name}] no lightning mark, skip`);
        continue;
      }
      console.log(`[${e.name}] has lightning mark, proceeding`);
    }

    if (isTest) {
      dur = 10 * 1000;
    }

    for (; dur > 0;) {
      let entry = textContains(e.name).findOne(1000);
      if (!entry) {
        console.log(`can not found [${e.name}], skip`);
        break;
      }
      let entryPos = entry.parent().center();
      let playBtn = jdjriFindPlayButton(entry);
      if (playBtn) {
        entryPos = playBtn.center();
      }
      console.log(` get [${e.name}] pos[${entryPos}]`);
      var t = 30 * 60 * 1000;
      if (dur <= t) {
        t = dur;
        dur = 0;
      } else {
        dur = dur - t;
      }
      if (!isTest) {
        t += 30 * 1000;
      }
      console.log(`act play [${e.name}] ${t / 1000} s`);
      // if (e.left_entry) {
      //   click(900, entryPos.y);
      // } else {
      click(entryPos);
      // }
      preciseSleep(t, false);
      back();
      back();
      sleep(2000);
    }
  }
}

/* enter interactive games */
function enterInteractiveGames() {
  let interactiveGame = text("互动游戏").findOne(1000);
  let sign = text("签到").findOne(1000);
  let taskCenter = text("任务中心").findOne(1000);

  // Already on interactive games page
  if (interactiveGame) {
    // If on sub-page (no sign, no taskCenter), go back to main list
    if (!sign && !taskCenter) {
      click(interactiveGame.center());
      sleep(3000);
    }
    return true;
  }

  // On home page (has sign button)
  if (sign && !taskCenter) {
    click(900, 2250);
    sleep(2000);

    let update = text("立即查看").findOne(1000);
    if (update) {
      backN(1);
    }

    let enter = text("互动游戏").findOne(1000);
    if (!enter) {
      console.log("cannot find 互动游戏 entry");
      return false;
    }
    click(enter.center());
    sleep(5000);
    return true;
  }

  // On task center or other page, try back to find entry
  backN(2);
  sleep(2000);
  let enter = text("互动游戏").findOne(1000);
  if (enter) {
    click(enter.center());
    sleep(5000);
    return true;
  }

  console.log("cannot determine current state, skip");
  return false;
}

function jdjriFindPlayButton(obj) {
  let ppp = obj.parent().parent().parent();
  let btn = findTextInChildren(ppp, "去玩");
  if (btn) {
    return btn;
  }
}

function findTextInChildren(obj, name) {
  if (!obj) {
    return;
  }
  if (obj.text() === name) {
    return obj;
  }

  for (let idx = 0; idx < obj.children().length; idx++) {
    let btn = findTextInChildren(obj.children()[idx], name);
    if (btn) {
      return btn;
    }
  }
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
  SECTIONS,
  tasksBySection,
  filterTasksBySection,
  hasLightningMark,
  checkLightningInRegion,
};
