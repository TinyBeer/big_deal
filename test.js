let appName = "网上国网";
// info(`${appName}...`);

app.launchApp(appName);
sleep(4000);
// longWait();
let obj = text("签到").findOne(20000);
console.log(obj);
