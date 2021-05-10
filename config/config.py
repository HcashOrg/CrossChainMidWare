# -*- coding: utf-8 -*-

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')

    DOWNLOAD_PATH = 'download'
    ETH_SECRET_KEY = 'Q!wert123@'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MONGO_HOST = 'localhost'
    MONGO_PORT = 27017
    MONGO_NAME = 'chaindb'
    MONGO_USER = 'chaindb_user'
    MONGO_PASS = 'yqr.1010'
    ETH_SECRET_KEY = 'Q!wert123@'
    ETH_URL = '127.0.0.1'
    ETH_PORT = 5544
    ETH_FEE = 0.002
    ETH_Minimum = 0.5
    VIN_SIZE = 1600
    VOUT_SIZE = 80
    BTC_HOST = 'btc_wallet'
    BTC_PORT = 60011
    BTC_COLLECT_HOST = 'localhost'
    BTC_COLLECT_PORT = 5444
    BTC_FEE =0.001
    BTC_PER_FEE = 0.0001
    ETP_PORT = 8820
    ETP_URL = 'etp_wallet'
    LTC_HOST = 'ltc_wallet'
    LTC_PORT = 60012
    LTC_COLLECT_HOST = 'localhost'
    LTC_COLLECT_PORT = 5445
    LTC_FEE =0.001
    LTC_PER_FEE = 0.00005
    DOGE_HOST="192.168.1.121"
    DOGE_PORT=18899
    DOGE_FEE=0.001
    DOGE_PER_FEE=0.00005
    DOGE_COLLECT_HOST = 'localhost'
    DOGE_COLLECT_PORT = 5455
    HC_HOST = "hc_wallet"
    HC_PORT = 19021
    HC_COLLECT_HOST = "localhost"
    HC_COLLECT_PORT = 5447
    HC_FEE = 0.05
    HC_PER_FEE = 0.001
    USDT_HOST="usdt_wallet"
    USDT_PORT = 60013
    USDT_COLLECT_HOST = 'localhost'
    USDT_COLLECT_PORT = 5444
    USDT_FEE = 0.001
    USDT_PER_FEE = 0.00005
    USDT_PROPERTYID = 31

    BCH_PORT = 60018
    BCH_COLLECT_HOST = 'localhost'
    BCH_COLLECT_PORT = 5452
    BCH_FEE = 0.001
    BCH_PER_FEE = 0.0001
    BCH_HOST="bch_wallet"
    # QUERY_SERVICE_HOST = "192.168.1.142"
    # QUERY_SERVICE_PORT = 5444

    # BTM_HOST = "btm_wallet"
    BTM_HOST = "192.168.1.107"
    BTM_PORT = 9888
    BTM_FEE = 100000000    #1btm
    # BTM_COLLECT_HOST = 'localhost'
    BTM_COLLECT_HOST = "192.168.1.107"
    BTM_COLLECT_PORT = 5451
    SUPPORT_MIDWARE_PLUGIN_SYMBOL=["HC","ETH","BTC","LTC","ERCPAX","ERCELF","USDT","BTM","BCH","ERCTITAN"]
    WHITE_LIST_SENATOR_ID = ["1.2.290","1.2.1294","1.2.1165","1.2.1124","1.2.1561","1.2.1237"]
    WHITE_LIST_FILE_PATH = "/hx/crosschain_midware/config/white_list_ids.json"


class DaConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MONGO_USER = 'chaindb_user'
    BTC_HOST = '192.168.1.124'
    BTC_PORT = 60011
    BTC_FEE = 0.001
    MONGO_HOST = '127.0.0.1'
    MONGO_PORT = 27017
    MONGO_PASS = 'yqr.1010'
    MONGO_NAME = 'chaindb'
    HC_HOST = "127.0.0.1"
    HC_PORT = 19012
    HC_FEE = 0.001



class SunnyConfig(Config):
    DEBUG = True

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MONGO_HOST = '192.168.1.121'
    MONGO_PORT = 27017
    MONGO_NAME = 'chaindb'
    MONGO_USER = 'chaindb_user'
    MONGO_PASS = 'yqr.1010'
    ETH_SECRET_KEY = 'Q!wert123@'
    ETH_URL = '192.168.1.121'
    ETH_PORT = 8546
    ETH_Minimum = 1
    BTC_HOST = '192.168.1.104'
    BTC_PORT = 60011


class TestingConfig(Config):
    TESTING = True
    MONGO_HOST = 'chaindb'
    MONGO_PORT = 27017
    MONGO_NAME = 'chaindb'


class ProductionConfig(Config):
    MONGO_HOST = 'chaindb'
    MONGO_PORT = 27017
    MONGO_NAME = 'chaindb'


class hzkConfig(Config) :
    DEBUG = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MONGO_HOST = '192.168.1.121'
    MONGO_PORT = 27017
    MONGO_NAME = 'chaindb'
    MONGO_USER = 'chaindb_user'
    MONGO_PASS = 'yqr.1010'
    ETP_URL = '192.168.1.123'
    ETP_PORT = 8820
    ETH_Minimum = 1


class MuConfig(Config):
    MONGO_HOST = 'localhost'
    MONGO_PORT = 27017
    MONGO_NAME = 'chaindb'
    MONGO_USER = 'chaindb_user'
    MONGO_PASS = 'yqr.1010'
    BTM_HOST = "192.168.1.107"
    BTM_PORT = 9888
    BTM_FEE = 100000000
    BTM_COLLECT_HOST = "192.168.1.107"
    BTM_COLLECT_PORT = 5451


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
    'Sunny': SunnyConfig,
    'Da': DaConfig,
    'hzk':hzkConfig,
    'mutalisk': MuConfig
}
