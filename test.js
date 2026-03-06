console.log(jdjriFindPlayButton(text("无尽战歌").findOne(500)));

function jdjriFindPlayButton(obj) {
  let ppp = obj.parent().parent().parent();
  if (ppp.childCount() !== 3) {
    return;
  }
  let btn = findTextInChildren(ppp, "去玩");
  if (btn && btn.depth() === 23) {
    return btn;
  }
}

function findTextInChildren(obj, name) {
  if (!obj) {
    return;
  }
  console.log(obj.text(), obj.childCount(), obj.depth());

  if (obj.text() === name) {
    return obj;
  }

  for (let idx = 0; idx < obj.children().length; idx++) {
    let btn = findTextInChildren(obj.children()[idx], name);
    if (btn) {
      return btn;
    }
  }
}
