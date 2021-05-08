# -*- coding: utf-8 -*-

from gevent import monkey
monkey.patch_all()

import os
from config import logger
from config import App
from config import Db
from config import Client
from config import Jsonrpc
from utils.sim_btc_utils import sim_btc_utils
from utils.hc_utils import hc_utils
from utils.usdt_utils import usdt_utils
from utils.btm_utils import btm_utils
import time
logger.info('Start app...')
app = App
db = Db
client = Client
jsonrpc = Jsonrpc
sim_btc_utils_all = ["btc", "ltc", "ub","bch", "doge"]
sim_btc_plugin = {}
for value in sim_btc_utils_all:
    upper = value.upper()
    sim_btc_config = {}
    if app.config.has_key(upper+"_HOST") and app.config.has_key(upper+"_PORT") and app.config.has_key(upper + "_FEE"):
        sim_btc_config["host"] = app.config[upper+"_HOST"]
        sim_btc_config["port"] = app.config[upper+"_PORT"]
        sim_btc_config["collect_host"] = app.config[upper+"_COLLECT_HOST"]
        sim_btc_config["collect_port"] = app.config[upper+"_COLLECT_PORT"]
        sim_btc_config["fee"] = app.config[upper+"_FEE"]
        sim_btc_config["per_fee"] = app.config[upper+"_PER_FEE"]
        sim_btc_config["vin_size"] = app.config["VIN_SIZE"]
        sim_btc_config["vout_size"] = app.config["VOUT_SIZE"]
        sim_btc_plugin[value] = sim_btc_utils(value, sim_btc_config)
hc_config = {}
if app.config.has_key("HC_HOST") and app.config.has_key("HC_PORT") and app.config.has_key("HC_FEE"):
    hc_config["host"] = app.config["HC_HOST"]
    hc_config["port"] = app.config["HC_PORT"]
    hc_config["collect_host"] = app.config["HC_COLLECT_HOST"]
    hc_config["collect_port"] = app.config["HC_COLLECT_PORT"]
    hc_config["fee"] = app.config["HC_FEE"]
    hc_config["per_fee"] = app.config["HC_PER_FEE"]
    hc_config["vin_size"] = app.config["VIN_SIZE"]
    hc_config["vout_size"] = app.config["VOUT_SIZE"]
hc_plugin = hc_utils("hc", hc_config)


usdt_config = {}
if app.config.has_key("USDT_HOST") and app.config.has_key("USDT_PORT") and app.config.has_key("USDT_FEE"):
    usdt_config["host"] = app.config["USDT_HOST"]
    usdt_config["port"] = app.config["USDT_PORT"]
    usdt_config["collect_host"] = app.config["USDT_COLLECT_HOST"]
    usdt_config["collect_port"] = app.config["USDT_COLLECT_PORT"]
    usdt_config["fee"] = app.config["USDT_FEE"]
    usdt_config["per_fee"] = app.config["USDT_PER_FEE"]
    usdt_config["vin_size"] = app.config["VIN_SIZE"]
    usdt_config["vout_size"] = app.config["VOUT_SIZE"]
    usdt_config["property_id"] = app.config["USDT_PROPERTYID"]
usdt_plugin = usdt_utils("usdt", usdt_config)


btm_config = {}
# BTM_FEE 单笔BTM交易最大手续费配置
if app.config.has_key("BTM_HOST") and app.config.has_key("BTM_PORT") and app.config.has_key("BTM_FEE"):
    btm_config["host"] = app.config["BTM_HOST"]
    btm_config["port"] = app.config["BTM_PORT"]
    btm_config["collect_host"] = app.config["BTM_COLLECT_HOST"]
    btm_config["collect_port"] = app.config["BTM_COLLECT_PORT"]
    btm_config["fee"] = app.config["BTM_FEE"]
btm_plugin = btm_utils("btm", btm_config)


from service import sim_api
from service import client_api
