let interactiveGame = text("互动游戏").findOne(200);
let sign = text("签到").findOne(200);
let hotGame = text("热门游戏").findOne(200);

console.log(interactiveGame !==null);
console.log(sign !==null);
console.log(hotGame !==null);


// let name = "淘沙大师"
// let root = text(name).findOne(100);
// console.log(root);
// displayArchitecture(root.parent().parent().parent().parent(), 0)
// function Person(name) {
//     this.name = name;
// }

// Person.prototype.say = function() {
//     console.log(this.name);
// }

// let p = new Person("测试");
// p.say();



// displayArchitecture(obj, 1)

function displayArchitecture_Name(name) {
  let root = text(name).findOne(100);
  console.log(root);

  if (root == null) {
    return;
  }

  displayArchitecture(root, 1);
}

function displayArchitecture(root, depth) {
  // console.log("->".repeat(depth), "id:", root.id(), "text:", root.text(), "desc:", root.desc(), "ccount:", root.childCount(), "bounds:", root.bounds(), "className", root.className());
  console.log(root);
  for (let idx = 0; idx < root.children().length; idx++) {
    let child = root.children()[idx];
    displayArchitecture(child, depth + 1);
  }
}
