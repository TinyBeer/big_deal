const { getScreenSize } = require("./utils");

let sc = null;

function initScreen() {
  if (!sc) {
    sc = getScreenSize();
  }
  return sc;
}

/**
 * 查找任务入口的"去完成"/"继续完成"按钮
 * @param {string} name - 任务名称
 * @param {object} opts - 可选配置
 * @param {boolean} opts.partial - 是否使用 textContains（部分匹配），默认 false
 * @param {number} opts.depth - 向上遍历的层数，默认 1
 * @param {number} opts.timeout - findOne 超时时间，默认 1000
 */
function findEntry(name, opts) {
  opts = opts || {};
  let screen = initScreen();
  let finder = opts.partial ? textContains(name) : text(name);
  let obj = finder.findOne(opts.timeout || 1000);
  if (!obj) {
    return;
  }

  let parent = obj;
  let levels = opts.depth || 1;
  for (let i = 0; i < levels; i++) {
    if (!parent.parent()) {
      return;
    }
    parent = parent.parent();
  }

  let entry = findGotoButton(parent);
  if (
    entry &&
    (entry.center().x < 0 ||
      entry.center().x > screen.width ||
      entry.center().y < 0 ||
      entry.center().y > screen.height)
  ) {
    return;
  }
  return entry;
}

function findGotoButton(parent) {
  for (let idx = 0; idx < parent.children().length; idx++) {
    let child = parent.children()[idx];
    if (child.text() === "去完成" || child.text() == "继续完成") {
      return child;
    }
    if (child.childCount != 0) {
      let ch = findGotoButton(child);
      if (ch) {
        return ch;
      }
    }
  }
  return;
}

module.exports = {
  findEntry,
  findGotoButton,
};
