/**
 * 公共库 · 屏幕与坐标
 *
 * 只提供"怎么算"，不关心"算什么"：
 * 不出现任何 App 名、控件文案、具体坐标常量。
 */

let cached = null;

/**
 * 屏幕尺寸（首次读取后缓存）
 * @param {boolean} refresh - 强制重新读取，默认 false
 * @returns {{width: number, height: number}} 每次返回新对象，避免调用方互相污染
 */
function size(refresh) {
  if (!cached || refresh) {
    var dm = context.getResources().getDisplayMetrics();
    cached = { width: dm.widthPixels, height: dm.heightPixels };
  }
  return { width: cached.width, height: cached.height };
}

/**
 * 按屏幕比例取像素点，用于替代硬编码坐标
 * @param {number} ratioX - 横向比例 0~1
 * @param {number} ratioY - 纵向比例 0~1
 * @returns {{x: number, y: number}} 可直接传给 click()
 * @example px(0.5, 0.9) // 屏幕水平居中、纵向 90% 处
 */
function px(ratioX, ratioY) {
  var s = size(false);
  return {
    x: Math.round(s.width * ratioX),
    y: Math.round(s.height * ratioY),
  };
}

/**
 * 判断点是否落在矩形区域内
 * @param {{x: number, y: number}} point
 * @param {number[]} bounds - [left, top, right, bottom]
 * @returns {boolean}
 */
function inBounds(point, bounds) {
  return (
    point.x > bounds[0] &&
    point.x < bounds[2] &&
    point.y > bounds[1] &&
    point.y < bounds[3]
  );
}

module.exports = {
  size,
  px,
  inBounds,
};
