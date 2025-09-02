// 执行脚本
auto(); // 这行代码必须要有
// 获取屏幕尺寸并打印
var screenSize = getScreenSize();
toast("屏幕宽度: " + screenSize.width + "px, 屏幕高度: " + screenSize.height + "px");
app.launchApp("中国移动");
sleep(8000);
//text('熊猫乐园').findOne().click();
click(948,1057);
sleep(12000);
click(100, 2200);


for (var i = 0; i < 12; i++) {
    sleep(4000);
    click(920, 1950);
    sleep(12000);
    back();
}
// 获取屏幕尺寸
function getScreenSize() {
    var dm = context.getResources().getDisplayMetrics();
    var width = dm.widthPixels;
    var height = dm.heightPixels;
    return {
        width: width,
        height: height
    };
}