console.log(get_jdblindboxtask());


function get_jdblindboxtask() {
  let btn = textMatch("(去逛逛|抽盲盒)").findOne(200)
  if (!btn) {
    return
  }

  let taskName = btn.parent().parent().children()[1].text()
  return {
    name: taskName,
    btnName: btn.text(),
    entry: btn.center(),
  }
}