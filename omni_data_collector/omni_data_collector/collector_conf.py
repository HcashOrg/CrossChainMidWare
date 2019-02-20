#!/usr/bin/env python 
# encoding: utf-8

__author__ = 'hasee'

import logging

class CollectorConfig(object):
    # DB configure
    DB_POOL_SIZE = 10
    CONNECT_TIMEOUT = 50
    MONGO_HOST = 'localhost'
    MONGO_PORT = 27017
    MONGO_NAME = 'chaindb'
    MONGO_USER = 'chaindb_user'
    MONGO_PASS = 'yqr.1010'

    # LOG configure
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)-15s %(levelname)s %(funcName)s %(message)s'
    LOG_FILENAME = "btc_data_collector.log"

    # SYNC configure
    SYNC_BLOCK_PER_ROUND = 10000

class USDTCollectorConfig(CollectorConfig):
    ASSET_SYMBOL = "USDT"
    RPC_HOST = 'usdt_wallet'
    RPC_PORT = 60013
    SYNC_STATE_FIELD = "usdtsyncstate"
    SYNC_BLOCK_NUM = "usdtsyncblocknum"
    SAFE_BLOCK_FIELD = "usdtsafeblock"
    RPC_USER ="a"
    RPC_PASSWORD="b"
    MULTISIG_VERSION = 196
    COLLECT_THREAD = 1
    PROPERTYID = 31





