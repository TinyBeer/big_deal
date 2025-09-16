auto();
const utils = require("./utils");
const screenSize = utils.getScreenSize();

// click(screenSize.width / 2, (screenSize.height * 2) / 3);
open_box(false);

function open_box(scrolld, screen) {
  if (scrolld) {
    scrollUp();
    sleep(1000);
    scrollUp();
    sleep(1000);
  }
  let box = textContains("个盲盒待开").findOne(1000);
  if (!box) {
    if (scrolld) {
      scrollDown();
      sleep(1000);
      scrollDown();
      sleep(1000);
    }
    return true;
  }
  console.log(box.text());

  click(box.center());
  sleep(2000);

  let open = text("一键开启").findOne(1000);
  if (!open) {
    return false;
  }

  click(open.center());
  sleep(5000);
  let pean = textContains("京豆+").findOne(3000);
  if (!pean) {
    return false;
  }

  back();
  sleep(2000);

  let enter = text("互动游戏").findOne(1000);
  if (enter) {
    click(enter.center());
    sleep(8000);
  } else {
    console.log("missing 互动游戏");
    return false;
  }

  if (scrolld) {
    scrollDown();
    sleep(1000);
    scrollDown();
    sleep(1000);
  }
  return true;
}
