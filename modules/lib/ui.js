/**
 * lib/ui —— 元素查找、点击、图像匹配
 *
 * 只做「怎么找、怎么点」，不内含任何任务文案、页面结构或坐标。
 * 文案、区域、模板路径一律由调用方传入。
 */

/** 默认查找超时（毫秒），沿用旧实现的 500 */
const DEFAULT_TIMEOUT = 500;

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
  matchImage,
  captureAndMatch,
};
