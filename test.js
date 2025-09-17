auto();
const utils = require("./utils");
const screenSize = utils.getScreenSize();

// let obj = text("新品").findOne(1000);
// click(obj.center());
// sleep(2000);

// let newGoods = id("e_g").text("新奇集市").findOne(1000);
// click(newGoods.center());
// sleep(2000);

// let novelBlindBoxEntry = id("novelBlindBoxEntry").findOne(1000).parent();
// click(novelBlindBoxEntry.center());
// sleep(2000);

let comps = className("android.widget.TextView")
  .text("在线医生")
  .depth(23)
  .find(1000);

comps = text("在线医生").find(1000);
for (let index = 0; index < comps.length; index++) {
  let comp = comps[index];
  console.log(comp.center());
  console.log(comp.parent().center());
}
