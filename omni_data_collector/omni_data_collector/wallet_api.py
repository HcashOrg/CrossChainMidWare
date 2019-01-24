# -*- coding: utf-8 -*-
import requests
import json
from base64 import encodestring
import logging

logging.getLogger("requests").setLevel(logging.WARNING)

class WalletApi:
    def __init__(self, name, conf):
        self.name = name
        self.config = conf
        if self.config.has_key("rpc_user"):
            self.rpc_user = self.config["rpc_user"]
        else:
            self.rpc_user ="a"
        if self.config.has_key("rpc_password"):
            self.rpc_password = self.config["rpc_password"]
        else:
            self.rpc_password ="b"

    def http_request(self, method, args):
        if self.name == 'HC':
            url = "http://%s:%s" % (self.config["host"], self.config["port"])
        else:
            url = "http://%s:%s" % (self.config["host"], self.config["port"])
        user = self.rpc_user
        passwd = self.rpc_password
        basestr = encodestring('%s:%s' % (user, passwd))[:-1]
        args_j = json.dumps(args)
        payload =  "{\r\n \"id\": 1,\r\n \"method\": \"%s\",\r\n \"params\": %s\r\n}" % (method, args_j)
        headers = {
            'content-type': "text/plain",
            'authorization': "Basic %s" % (basestr),
            'cache-control': "no-cache",
        }
        cache = ""
        while True:
            try:
                if self.name == "HC":
                    #requests.packages.urllib3.disable_warnings()
                    response = requests.request("POST", url, data=payload, headers=headers)
                else:
                    response = requests.request("POST", url, data=payload, headers=headers)
                cache = response.text
                rep = response.json()
                if "result" in rep:
                    return rep
                print response.text
            except Exception,ex:
                print ex
                print cache