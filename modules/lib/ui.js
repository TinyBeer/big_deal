/**
 * lib/ui —— 元素查找、点击、图像匹配
 *
 * 只做「怎么找、怎么点」，不内含任何任务文案、页面结构或坐标。
 * 文案、区域、模板路径一律由调用方传入。
 */

/** 默认查找超时（毫秒），沿用旧实现的 500 */
const DEFAULT_TIMEOUT = 500;

const wait = require("./wait");

/* ------------- 文本查找 ------------- */

/**
 * 按文本查找控件
 * @param {string|RegExp} tx - 精确文本；opts.regex 为 true 时按正则处理
 * @param {object} [opts]
 * @param {number} [opts.timeout] - findOne 超时，默认 500
 * @param {boolean} [opts.partial] - 包含匹配（textContains）
 * @param {boolean} [opts.regex] - 正则匹配（textMatches）
 * @returns {object|null} UiObject
 */
function findText(tx, opts) {
  opts = opts || {};
  const timeout = typeof opts.timeout === "number" ? opts.timeout : DEFAULT_TIMEOUT;

  let finder;
  if (opts.regex) {
    finder = textMatches(tx);
  } else if (opts.partial) {
    finder = textContains(tx);
  } else {
    finder = text(tx);
  }
  return finder.findOne(timeout);
}

/**
 * 兼容旧签名：按文本查找，第二个参数直接是超时
 * @param {string} tx
 * @param {number} [dur]
 */
function findElementByText(tx, dur) {
  let d = DEFAULT_TIMEOUT;
  if (dur) {
    d = dur;
  }
  return text(tx).findOne(d);
}

/* ------------- 点击 ------------- */

/**
 * 空安全点击：控件、点对象、null 都能接
 * @param {object|null} target - UiObject / {x,y} / null
 * @returns {boolean} 是否真的点了
 */
function tap(target) {
  if (!target) {
    return false;
  }

  // 已经是坐标点
  if (typeof target.x === "number" && typeof target.y === "number" && !target.bounds) {
    click(target.x, target.y);
    return true;
  }

  if (typeof target.bounds !== "function") {
    return false;
  }

  const b = target.bounds();
  if (!b || b.width() <= 0 || b.height() <= 0) {
    return false;
  }

  click(b.center());
  return true;
}

/**
 * 找到就点，一步到位
 * @param {string|RegExp} tx - 目标文本
 * @param {object} [opts] - 透传给 findText，额外支持 opts.log 输出未找到日志
 * @returns {boolean} 是否点了
 */
function tapText(tx, opts) {
  const obj = findText(tx, opts);
  if (!obj) {
    if (opts && opts.log) {
      console.log("not found: " + tx);
    }
    return false;
  }
  return tap(obj);
}

/* ------------- 轮询等待 ------------- */

/**
 * 边等边找：按固定步进反复查找某个文本，可配置找到后是否点击
 *
 * 覆盖的典型场景是「限时浏览页 → 等『立即返回』按钮出现 → 点掉再继续」，
 * 但文案、步进、点不点、点完等多久全部由调用方决定。
 *
 * @param {string|RegExp} tx - 要等的文本
 * @param {object} [opts]
 * @param {number} [opts.seconds] - 最多等多少秒，默认 10
 * @param {number} [opts.intervalMs] - 每次步进毫秒数，默认 1000（先睡再找）
 * @param {number} [opts.findTimeout] - 单次查找超时，默认 100
 * @param {boolean} [opts.click] - 找到后是否点击，默认 false
 * @param {string} [opts.afterClick] - 点击后额外等待的档位，如 "short"；不传则不等
 * @param {string} [opts.log] - 找到时打印的文案，不传则不打印
 * @returns {boolean} 是否等到了
 */
function waitForText(tx, opts) {
  opts = opts || {};
  const seconds = typeof opts.seconds === "number" ? opts.seconds : 10;
  const intervalMs = typeof opts.intervalMs === "number" ? opts.intervalMs : 1000;
  const findTimeout = typeof opts.findTimeout === "number" ? opts.findTimeout : 100;
  const rounds = Math.max(1, Math.round((seconds * 1000) / intervalMs));

  for (let i = 0; i < rounds; i++) {
    sleep(intervalMs);
    const obj = findText(tx, { timeout: findTimeout });
    if (!obj) {
      continue;
    }
    if (opts.log) {
      console.log(opts.log);
    }
    if (opts.click) {
      tap(obj);
      if (opts.afterClick) {
        wait.sleepTier(opts.afterClick);
      }
    }
    return true;
  }
  return false;
}

/* ------------- 手势 ------------- */

/**
 * 拖拽/滑动，并保证滑完该等的那一下不会漏
 *
 * 起止点由调用方给（各页面锚点不同，不进库），等待档位也可选。
 *
 * @param {{x:number,y:number}} from - 起点
 * @param {{x:number,y:number}} to - 终点
 * @param {object} [opts]
 * @param {number} [opts.duration] - 滑动耗时，默认 500
 * @param {string} [opts.wait] - 滑动后等待的档位（"mini"/"short"/…），不传则不等
 * @returns {boolean} 是否执行了滑动
 */
function drag(from, to, opts) {
  opts = opts || {};
  if (!from || !to) {
    return false;
  }
  const duration = typeof opts.duration === "number" ? opts.duration : 500;
  swipe(from.x, from.y, to.x, to.y, duration);
  if (opts.wait) {
    wait.sleepTier(opts.wait);
  }
  return true;
}

/* ------------- 图像匹配 ------------- */
/**
 * 在指定区域内匹配模板图片
 * @param {Image} screenImg - 屏幕截图
 * @param {string} templatePath - 模板图片路径（相对路径）
 * @param {Array} region - [x1, y1, x2, y2]
 * @param {number} threshold - 匹配阈值 0-1，默认 0.7
 * @returns {Object|null} 匹配结果 {x, y, similarity}
 */
function matchImage(screenImg, templatePath, region, threshold) {
  threshold = threshold || 0.7;
  var tpl = images.read(templatePath);
  if (!tpl) {
    log("模板加载失败: " + templatePath);
    return null;
  }

  var findRegion = [region[0], region[1], region[2] - region[0], region[3] - region[1]];
  var result = images.findImage(screenImg, tpl, {
    region: findRegion,
    threshold: threshold,
  });

  tpl.recycle();
  return result;
}

/**
 * 截屏并检测区域内是否有指定模板图片
 * @param {string} templatePath - 模板图片路径（相对路径）
 * @param {Array} region - [x1, y1, x2, y2]
 * @param {number} threshold - 匹配阈值 0-1，默认 0.7
 * @returns {Object|null} 匹配结果 {x, y, similarity}
 */
function captureAndMatch(templatePath, region, threshold) {
  var screenImg = images.captureScreen();
  if (!screenImg) {
    log("截图失败");
    return null;
  }
  var result = matchImage(screenImg, templatePath, region, threshold);
  screenImg.recycle();
  return result;
}

module.exports = {
  findText,
  findElementByText,
  tap,
  tapText,
  waitForText,
  drag,
  matchImage,
  captureAndMatch,
};
