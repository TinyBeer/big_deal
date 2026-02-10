console.log(getCurScratchCardTask());

function getCurScratchCardTask() {
  let list = textMatch(".*浏览\\ds 刮卡\\+\\d").find(200);
  for (let idx = 0; idx < list.length; idx++) {
    let element = list[idx];
    let ex = element.center().x;
    if (ex > 400 && ex < 800 && element.text().includes("刮卡+")) {
      return element;
    }
  }
}
