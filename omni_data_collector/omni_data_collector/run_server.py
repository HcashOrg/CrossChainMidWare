#!/usr/bin/env python
# encoding: utf-8

__author__ = 'ted'

from collector_conf import CollectorConfig
from collect_usdt_block import USDTCoinTxCollector

import logging
import sys
import signal
import time
from pymongo import MongoClient
from gevent import monkey

if __name__ == '__main__':
    config = CollectorConfig()
    logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT, filename=config.LOG_FILENAME, filemode="a")
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    client = MongoClient(host=config.MONGO_HOST, port=config.MONGO_PORT)
    client[config.MONGO_NAME].authenticate(config.MONGO_USER, config.MONGO_PASS)
    db = client[config.MONGO_NAME]

    # collector = BTCCoinTxCollecter(db)
    if not len(sys.argv) == 2:
        print "Please indicate which type of coin tx to collect [usdt]"
        exit(1)
    elif sys.argv[1] == "usdt":
        collector = USDTCoinTxCollector(db)
    else:
        print "Please indicate correct type of coin tx to collect [btc|ltc]"
        exit(1)

    def signal_handler(signum, frame):
        collector.stop_flag = True


    monkey.patch_all()
    signal.signal(signal.SIGINT, signal_handler)
    collector.do_collect_app()
