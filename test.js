daydayclaim();
function daydayclaim() {
  let btn = text("图片").findOne(1000);
  if (!btn) {
    console.log("missing target,skip");
    return false;
  }
  scrollDown();
  sleep(1000);
  scrollDown();
  sleep(1000);

  let num = 6;
  let cnt = 0;
  let goods = depth(19).find(1000);
  for (let idx = 0; idx < goods.length; idx++) {
    let e = goods[idx];
    if (e.center().y > 330) {
      click(e.children()[0].center());
      sleep(8000);
      back();
      back();
      sleep(1000);
      cnt++;
    }
    if (cnt >= num) {
      break;
    }
  }
  click(btn.center())
  return true;
}
