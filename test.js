auto();

const utils = require("./utils");
const smzdm = require("./smzdm");
const ctcp = require("./china_telecom_cloud_pan");
const sgo = require("./state_grid_online");

ctcp.sign();
sgo.sign();
smzdm.sign();
