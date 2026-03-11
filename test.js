const task_tag = "浏览10s";

console.log(getOneViewTask());

function getOneViewTask() {
  let obj = textMatch("再完成\\d+个任务").findOne(200);
  return obj;
}
