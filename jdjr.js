/* import */
const jutils = require("./utils");

/* config */

const matrix = [
  {
    origin: {
      x: 112,
      y: 1200,
    },
    height: 250,
    width: 1000,
    // delayList: [[1, 1, 1, 1, 1]],
    delayList: [[59, 34, 9, 14, 14]],
  },
  {
    origin: {
      x: 112,
      y: 1500,
    },
    height: 500,
    width: 1000,
    delayList: [
      // [1, 0, 0, 1],
      [9, 0, 0, 29],
      // [1, 1, 2, 1],
      [14, 14, 58, 14],
    ],
  },
  {
    origin: {
      x: 365,
      y: 790,
    },
    scroll: true,
    height: 1270,
    width: 500,
    delayList: [[15], [15], [15], [15], [15], [15], [15], [15], [15]],
  },
];

// const matrix = [
//   {
//     origin: {
//       x: 112,
//       y: 1200,
//     },
//     height: 250,
//     width: 1000,
//     delayList: [[1, 1, 1, 1, 1]],
//   },
//   {
//     origin: {
//       x: 112,
//       y: 1500,
//     },
//     height: 500,
//     width: 1000,
//     delayList: [
//       [1, 0, 0, 1],
//       [1, 1, 2, 1],
//     ],
//   },
// ];

function run() {
  // launch app
  app.launchApp("京东金融");
  sleep(5000);

  // enter interactive games
  enterInteractiveGames();

  for (let a = 0; a < matrix.length; a++) {
    var obj = matrix[a];
    var dy = 0;
    if (obj.delayList.length > 1) {
      dy = obj.height / (obj.delayList.length - 1);
    }
    if (obj.scroll) {
      scrollDown();
      sleep(2000);
      scrollDown();
      sleep(2000);
    }
    for (let i = 0; i < obj.delayList.length; i++) {
      var dx = 0;
      if (obj.delayList[i].length > 1) {
        dx = obj.width / (obj.delayList[i].length - 1);
      }
      for (let j = 0; j < obj.delayList[i].length; j++) {
        sleep(2000);
        var x = obj.origin.x + dx * j;
        var y = obj.origin.y + dy * i;
        var dur = obj.delayList[i][j] * 60 * 1000;
        if (dur == 0) {
          console.log("task time == " + dur + " skip task");
          continue;
        }
        console.log(
          "click task[" +
            i +
            "," +
            j +
            "] pos[" +
            x +
            "," +
            y +
            "] sleep[" +
            dur +
            "]"
        );
        for (; dur > 0; ) {
          var t = 8 * 60 * 1000;
          if (dur <= t) {
            t = dur;
            dur = 0;
          } else {
            dur = dur - t;
          }

          console.log("act click pos[" + x + "," + y + "] sleep[" + t + "]");
          click(x, y);
          jutils.preciseSleep(t, false);
          back();
          back();
          sleep(2000);
        }
      }
    }
  }
  back();
  back();
  sleep(2000);
}

/* enter interactive games */
function enterInteractiveGames() {
  let interactiveGame = text("互动游戏").findOne(1000);
  let sign = text("签到").findOne(1000);
  let taskCenter = text("任务中心").findOne(1000);

  if (!interactiveGame && sign && !taskCenter) {
    // home page
    click(900, 2250);
    sleep(2000);
    let enter = text("互动游戏").findOne(1000);
    if (!enter) {
      return false;
    }
    click(enter.center());
    sleep(5000);
  } else if (interactiveGame && !sign && !taskCenter) {
    click(interactiveGame.center());
    sleep(5000);
  }
}

//  导出函数（供其他脚本调用）
module.exports = {
  run,
};
