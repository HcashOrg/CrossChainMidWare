#!/usr/bin/env python
# encoding=utf8

from collect_btc_block import CacheManager
from collector_conf import BTMCollectorConfig
from wallet_api import WalletApi
from collect_btc_block import BTCCoinTxCollector


class BTMCoinTxCollecter(BTCCoinTxCollector):
    def __init__(self, db):
        super(BTMCoinTxCollecter, self).__init__(db)
        self.t_multisig_address = self.db.b_btm_multisig_address
        self.config = BTMCollectorConfig()
        conf = {"host": self.config.RPC_HOST, "port": self.config.RPC_PORT}
        self.wallet_api = WalletApi(self.config.ASSET_SYMBOL, conf)
        self.cache = CacheManager(self.config.SYNC_BLOCK_NUM, self.config.ASSET_SYMBOL)
