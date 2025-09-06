auto();
let games = textContains("秒(0/1)").find(1000);
for (let i = 0; i < games.length; i++) {
  let game = games[i];
  let element = game.parent();
  traverseView(game.text(), element);
  //   for (let j = 0; j < element.childCount(); j++) {
  //     let child = element.children()[i];
  //     console.log(child.text());

  //     if (child.text() == "去完成") {
  //       console.log(game.text(), "去完成", child.center());
  //     } else if (child.text() == "去领取") {
  //       console.log(game.text(), "去领取", child.center());
  //     }
  //   }
}

function playGameTraverse(name, view, depth) {
  if (!view) return;
  //   var indent = "  ".repeat(depth);
  //   log(indent + "类名: " + view.getClassName());
  //   log(indent + "ID: " + view.id());
  //   log(indent + "文本: " + view.getText());
  //   log(indent + "-------------------");
  if (view.text() === "领奖励") {
    console.log(name, "领奖励", view.center());
  } else if (view.text() == "去完成") {
    console.log(name, "去完成", view.center());
  }
  // 递归遍历子节点
  var childCount = view.getChildCount();
  for (var i = 0; i < childCount; i++) {
    traverseView(name, view.children()[i], depth + 1);
  }
}

// let com = text("去完成").findOne(1000);
// console.log(com.text(), com.center());

// console.log(`find game[${game.text()}] pos[${game.center()}] play 60 sec...`);

// let obj = textContains("分钟").find(1000);

// var mins = [];
// for (let index = 0; index < obj.length; index++) {
//   let element = obj[index];
//   let nums = extractNumbersWithDecimal(element.text());
//   console.log(element.text(), nums);

//   if (nums.length == 1) {
//     mins.push(nums[0]);
//   }
// }
// console.log(mins);

// function extractNumbersWithDecimal(str) {
//   var numbers = [];
//   var currentNumber = "";
//   var hasDecimal = false; // 标记是否已经有小数点

//   for (var i = 0; i < str.length; i++) {
//     var char = str.charAt(i);
//     // 允许数字和一个小数点
//     if (!isNaN(char) && char !== " ") {
//       currentNumber += char;
//     } else if (char === "." && !hasDecimal) {
//       currentNumber += char;
//       hasDecimal = true;
//     } else {
//       if (currentNumber !== "") {
//         numbers.push(currentNumber);
//         currentNumber = "";
//         hasDecimal = false;
//       }
//     }
//   }

//   if (currentNumber !== "") {
//     numbers.push(currentNumber);
//   }

//   return numbers;
// }
