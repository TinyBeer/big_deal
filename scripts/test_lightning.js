sleep(5000);
/**
 * 测试脚本：使用图片匹配检测区域内是否有雷电标记
 *
 * 原理：
 * 1. 截取屏幕截图
 * 2. 将雷电图标作为模板，在指定区域内进行匹配
 * 3. 返回匹配结果和位置
 *
 * 使用方式：
 * 1. 在 AutoJS 中导入此脚本
 * 2. 确保当前屏幕在京东金融的互动游戏页面
 * 3. 运行脚本
 */

// ====== 配置区 ======
var TEMPLATE_PATH = "./templates/lightning_template2.png";
var SCREENSHOT_PATH = "./test_screenshot.png";
var THRESHOLD = 0.7;  // 匹配阈值，0-1之间，越高越严格

// ====== 测试区域定义 ======
// 每个区域格式: { name: "游戏名", bounds: [x1, y1, x2, y2] }
// 模板来自"发现更多"区游戏图标左上角的⚡
var TEST_REGIONS = [
    // 有雷电标记的游戏（发现更多区）
    { name: "无尽战歌(有⚡)", bounds: [60, 1570, 220, 1710] },
    { name: "麻将滑滑乐(有⚡)", bounds: [60, 1740, 220, 1880] },
    { name: "拼图接龙(有⚡)", bounds: [60, 1915, 220, 2055] },
    { name: "像素射手(有⚡)", bounds: [60, 2090, 220, 2225] },
    // 无雷电标记的区域（对照组 - 猜你喜欢区的游戏卡片）
    { name: "喵喵十消(无⚡)", bounds: [60, 140, 530, 490] },
    { name: "超级连连看(无⚡)", bounds: [550, 500, 1020, 850] },
];

// ====== 核心函数 ======

/**
 * 截取屏幕截图
 */
function takeScreenshot() {
    return images.captureScreen();
}

/**
 * 在指定区域内匹配模板
 * @param {Image} screenImg - 屏幕截图
 * @param {Image} templateImg - 模板图片
 * @param {Array} region - [x1, y1, x2, y2]
 * @returns {Object|null} 匹配结果 {point: {x, y}, similarity: number}
 */
function matchInRegion(screenImg, templateImg, region) {
    var regionImg = images.clip(screenImg, region[0], region[1],
        region[2] - region[0], region[3] - region[1]);

    var result = images.matchTemplate(regionImg, templateImg, 1);

    var bestMatch = null;
    var maxSim = 0;

    if (result && result.matches) {
        for (var i = 0; i < result.matches.length; i++) {
            var match = result.matches[i];
            if (match.similarity > maxSim && match.similarity >= THRESHOLD) {
                maxSim = match.similarity;
                bestMatch = {
                    x: match.point.x + region[0],
                    y: match.point.y + region[1],
                    similarity: match.similarity
                };
            }
        }
    }

    regionImg.recycle();
    return bestMatch;
}

/**
 * 使用 findImage 方式匹配（更简单的API）
 * @param {Image} screenImg - 屏幕截图
 * @param {Image} templateImg - 模板图片
 * @param {Array} region - [x1, y1, x2, y2]
 * @returns {Object|null} 匹配结果 {x, y, similarity}
 */
function findImageInRegion(screenImg, templateImg, region) {
    // findImage 的 region 格式是 [x, y, width, height]，需要转换
    var findRegion = [region[0], region[1], region[2] - region[0], region[3] - region[1]];
    var options = {
        region: findRegion,
        threshold: THRESHOLD
    };
    var result = images.findImage(screenImg, templateImg, options);
    return result;
}

// ====== 主测试流程 ======

// 1. 加载模板
log("模板路径: " + TEMPLATE_PATH);
log("文件存在: " + files.exists(TEMPLATE_PATH));

var templateImg = images.read(TEMPLATE_PATH);
if (!templateImg) {
    toast("模板文件读取失败");
    log("错误: 无法读取模板文件");
    exit();
}
log("模板加载成功, 尺寸: " + templateImg.getWidth() + "x" + templateImg.getHeight());

// 2. 截取屏幕
log("正在截取屏幕...");
var screenImg = takeScreenshot();
if (!screenImg) {
    toast("截图失败");
    log("错误: 无法截取屏幕");
    exit();
}
log("截图成功, 尺寸: " + screenImg.getWidth() + "x" + screenImg.getHeight());

// 3. 逐个区域测试
log("\n========== 开始检测 ==========");
log("匹配阈值: " + THRESHOLD);
log("");

var results = [];

TEST_REGIONS.forEach(function (region) {
    log("--- 检测: " + region.name + " ---");
    log("区域: [" + region.bounds.join(", ") + "]");

    var match1 = matchInRegion(screenImg, templateImg, region.bounds);
    var match2 = findImageInRegion(screenImg, templateImg, region.bounds);

    var found = false;
    var similarity = 0;
    var position = null;

    if (match1) {
        found = true;
        similarity = match1.similarity;
        position = match1;
        log("✓ matchTemplate 匹配成功!");
        log("  相似度: " + (match1.similarity * 100).toFixed(1) + "%");
        log("  位置: (" + match1.x + ", " + match1.y + ")");
    }

    if (match2) {
        found = true;
        similarity = Math.max(similarity, match2.similarity);
        position = position || match2;
        log("✓ findImage 匹配成功!");
        log("  相似度: " + (match2.similarity * 100).toFixed(1) + "%");
        log("  位置: (" + match2.x + ", " + match2.y + ")");
    }

    if (!found) {
        log("✗ 未检测到雷电标记");
    }

    results.push({
        name: region.name,
        found: found,
        similarity: similarity,
        position: position
    });

    log("");
});

// 4. 输出汇总
log("\n========== 检测结果汇总 ==========");
results.forEach(function (r) {
    var icon = r.found ? "⚡" : "  ";
    var sim = r.found ? " (" + (r.similarity * 100).toFixed(1) + "%)" : "";
    log(icon + " " + r.name + sim);
});

// 5. 释放资源
screenImg.recycle();
templateImg.recycle();

log("\n测试完成!");
