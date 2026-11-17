/*
 * 整个模块体包在 IIFE 里。
 *
 * AutoJs6 的 jvm-npm 会把模块代码求值到「调用方作用域」，模块顶层的 const / function
 * 会漏进调用方作用域（main.js 的 "ui"; 还会在此处声明全局 var ui），一旦重名就会报
 * 「变量 xxx 重复声明」，整个 require 链失败。包一层后内部命名完全封闭，导出照旧走 module.exports。
 */
(function () {
  /**
   * lib/ui —— 元素查找、点击、图像匹配
   *
   * 只做「怎么找、怎么点」，不内含任何任务文案、页面结构或坐标。
   * 文案、区域、模板路径一律由调用方传入。
   */

  /** 默认查找超时（毫秒），沿用旧实现的 500 */
  const DEFAULT_TIMEOUT = 500;

  const uiWait = require("./wait");
  const uiScreen = require("./screen");

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

  /* ------------- 几何 ------------- */

  /**
   * 取控件的中心点与尺寸
   *
   * 注意 AutoJs 的两个对象不一样：UiObject 有 center()，而 bounds() 返回的 Rect 没有，
   * Rect 只有 left/top/right/bottom（属性）和 width()/height()（方法）。
   * 这里统一成 {x, y, width, height}，调用方不用再关心是哪种对象。
   *
   * @param {object|null} obj - UiObject 或 Rect
   * @returns {{x:number,y:number,width:number,height:number}|null}
   */
  function rectInfo(obj) {
    if (!obj) {
      return null;
    }

    const b = typeof obj.bounds === "function" ? obj.bounds() : obj;
    if (!b) {
      return null;
    }

    const read = (name) => {
      if (typeof b[name] === "function") {
        return b[name]();
      }
      return typeof b[name] === "number" ? b[name] : null;
    };

    const left = read("left");
    const top = read("top");
    const right = read("right");
    const bottom = read("bottom");
    if (left === null || top === null || right === null || bottom === null) {
      return null;
    }

    // 优先用 Rect.center() 取中心点（AutoJs 里 UiObject 没有 center()，是 bounds() 才有）
    let c = null;
    if (typeof b.center === "function") {
      try {
        c = b.center();
      } catch (e) {
        c = null;
      }
    }

    return {
      x: c && typeof c.x === "number" ? c.x : Math.round((left + right) / 2),
      y: c && typeof c.y === "number" ? c.y : Math.round((top + bottom) / 2),
      width: right - left,
      height: bottom - top,
    };
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

    const info = rectInfo(target);
    // 找不到元素时常常返回 bounds 全 0 的壳，点了会落到屏幕左上角
    if (!info || !(info.width > 0) || !(info.height > 0)) {
      return false;
    }

    click(info.x, info.y);
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
   * @param {boolean} [opts.partial] - 使用包含匹配（textContains），默认 false
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
      const obj = findText(tx, { timeout: findTimeout, partial: opts.partial });
      if (!obj) {
        continue;
      }
      let clicked = true;
      if (opts.click) {
        // 取控件 center 模拟点击；clickable=false 的 TextView 也照样能点
        clicked = tap(obj);
        if (clicked && opts.afterClick) {
          uiWait.sleepTier(opts.afterClick);
        }
      }
      if (clicked && opts.log) {
        console.log(opts.log);
      }
      return clicked;
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
      uiWait.sleepTier(opts.wait);
    }
    return true;
  }

  /**
   * 反复滑动，直到目标控件真正出现在屏幕（或指定区域）上
   *
   * 和 drag 的区别：drag 是盲滑固定次数；这里每次滑完都重新探测，
   * 已经在可见区就一次都不滑，滑进来就立刻停 —— 屏幕宽窄、轮播位置不同都不会滑过头或滑不够。
   *
   * 「可见」的判定是：probe() 拿到控件，且控件中心落在 region 内。
   * 已存在但在屏幕外的控件（横向轮播里很常见）会被视为不可见，继续滑。
   *
   * @param {function(): object|null} probe - 探测函数，返回 UiObject 或 null
   * @param {object} opts
   * @param {{x:number,y:number}} opts.from - 滑动起点
   * @param {{x:number,y:number}} opts.to - 滑动终点
   * @param {number} [opts.max=3] - 最多滑几次
   * @param {number} [opts.duration=500] - 单次滑动耗时
   * @param {string} [opts.wait="mini"] - 每次滑动后的等待档位
   * @param {number[]} [opts.region] - [left, top, right, bottom]，默认整屏
   * @returns {object|null} 可见的控件；滑完仍不可见返回 null
   */
  function dragUntilVisible(probe, opts) {
    opts = opts || {};
    const max = typeof opts.max === "number" ? opts.max : 3;

    function visible() {
      let obj;
      try {
        obj = probe();
      } catch (e) {
        return null;
      }
      if (!obj) {
        return null;
      }
      const info = rectInfo(obj);
      // 全 0 / 取不到尺寸的壳一律当不可见
      if (!info || !(info.width > 0) || !(info.height > 0)) {
        return null;
      }
      const s = uiScreen.size();
      const area = opts.region || [0, 0, s.width, s.height];
      return uiScreen.inBounds(info, area) ? obj : null;
    }

    let obj = visible();
    if (obj) {
      return obj;
    }
    for (let i = 0; i < max; i++) {
      drag(opts.from, opts.to, {
        duration: opts.duration,
        wait: opts.wait === undefined ? "mini" : opts.wait,
      });
      obj = visible();
      if (obj) {
        return obj;
      }
    }
    return null;
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
    dragUntilVisible,
    matchImage,
    captureAndMatch,
  };
})();
