#!/usr/bin/env python
# encoding: utf-8

__author__ = 'ted'

from collector_conf import CollectorConfig
from collect_btc_block import BTCCoinTxCollector
from collect_ltc_block import LTCCoinTxCollecter
from collect_ub_block import UBCoinTxCollecter
from BKCoinTxCollector import BKCoinTxCollector
from collect_hc_block import HCCoinTxCollecter
from collect_btm_block import BTMCoinTxCollecter
from collect_bch_block import BCHCoinTxCollecter
from collect_doge_block import DOGECoinTxCollecter
import logging
import sys
import signal
import time
from pymongo import MongoClient

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
        print "Please indicate which type of coin tx to collect [btc|ltc]"
        exit(1)
    elif sys.argv[1] == "btc":
        collector = BTCCoinTxCollector(db)
    elif sys.argv[1] == "ltc":
        collector = LTCCoinTxCollecter(db)
    elif sys.argv[1] == "ub":
        collector = UBCoinTxCollecter(db)
    elif sys.argv[1] == "bk":
        time.sleep(3)
        collector = BKCoinTxCollector(db)
    elif sys.argv[1] == "hc":
        collector = HCCoinTxCollecter(db)
    elif sys.argv[1] == "btm":
        collector = BTMCoinTxCollecter(db)
    elif sys.argv[1] == "bch":
        collector = BCHCoinTxCollecter(db)
    elif sys.argv[1] == "doge":
        collector = DOGECoinTxCollecter(db)
    else:
        print "Please indicate correct type of coin tx to collect [btc|ltc]"
        exit(1)

    def signal_handler(signum, frame):
        collector.stop_flag = True


    signal.signal(signal.SIGINT, signal_handler)
    collector.do_collect_app()
