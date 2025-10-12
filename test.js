let claim = desc("翻倍领取").findOne(1000);
if (claim) {
  click(claim.center().x - 400, claim.center().y);
}
