#!/usr/bin/env python
# encoding=utf8

import logging
import sys
import traceback
from collect_btc_block import CacheManager
from collector_conf import BCHCollectorConfig
from wallet_api import WalletApi
# import time
# from block_btc import BlockInfoBtc
# from datetime import datetime
from collect_btc_block import BTCCoinTxCollector


class BCHCoinTxCollecter(BTCCoinTxCollector):
    def __init__(self, db):
        super(BCHCoinTxCollecter, self).__init__(db)
        self.t_multisig_address = self.db.b_bch_multisig_address
        self.config = BCHCollectorConfig()
        conf = {"host": self.config.RPC_HOST, "port": self.config.RPC_PORT}
        self.wallet_api = WalletApi(self.config.ASSET_SYMBOL, conf)
        self.cache = CacheManager(self.config.SYNC_BLOCK_NUM, self.config.ASSET_SYMBOL)
