auto();

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
