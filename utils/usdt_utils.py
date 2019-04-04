# -*- coding: utf-8 -*-

import requests
import json
from base64 import encodestring
from config import Db
from service import logger
import math
db =Db

class usdt_utils:
    def __init__(self, name, conf):
        self.name = name
        self.config = conf

    def collect_http_request(self, method, args):
        url = "http://%s:%s" % (self.config["collect_host"], self.config["collect_port"])
        return self.base_http_request(url, method, args)


    def http_request(self, method, args):
        url = "http://%s:%s" % (self.config["host"], self.config["port"])
        return self.base_http_request(url, method, args)

    def base_http_request(self, url, method, args):
        user = 'a'
        passwd = 'b'
        basestr = encodestring('%s:%s' % (user, passwd))[:-1]
        args_j = json.dumps(args)
        payload =  "{\"jsonrpc\":\"1.0\",\r\n \"id\": 1,\r\n \"method\": \"%s\",\r\n \"params\": %s\r\n}" % (method, args_j)
        headers = {
            'content-type': "application/json",
            'authorization': "Basic %s" % (basestr),
            'cache-control': "no-cache",
        }
        #print(payload)
        #response = requests.request("POST", url, data=payload, headers=headers)
        requests.packages.urllib3.disable_warnings()
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        rep = response.json()
        #print(rep)
        return rep

    def omni_create_multisig(self, addrs, amount):
        resp = self.http_request("createmultisig", [amount, addrs])
        if resp["result"] != None:
            try:
                self.http_request("importaddress", [resp["result"].get("address"), "", False])
            except:
                pass
            return resp["result"]
        else:
            return None

    def omni_validate_address(self, addr):
        resp = self.http_request("validateaddress", [addr])
        address = ""
        if resp["result"] != None:
            address = resp["result"]
        return address

    # def omni_validate_address(self, addr):
    #     resp = self.http_request("validateaddress", [addr])
    #     if resp["result"] != None:
    #         return resp["result"]
    #     else:
    #         return None

    def omni_create_address(self):
        resp = self.http_request("getnewaddress", [""])
        address = ""
        if resp["result"] != None:
            address = resp["result"]
        return address

    def omni_query_tx_out(self, addr):
        message = [addr]
        resp = self.http_request("listunspent", [0, 9999999, message])
        if resp["result"] != None:
            return resp["result"]
        else:
            return None

    def omni_broadcaset_trx(self, trx):
        resp = self.http_request("sendrawtransaction", [trx])
        result = ""
        if resp["result"] != None:
            result = resp["result"]
        return result

    def omni_sign_message(self, addr, message):
        resp = self.http_request("signmessage", [addr, message])
        signed_message = ""
        if resp["result"] != None:
            signed_message = resp["result"]
        return signed_message

    def omni_verify_signed_message(self, addr, message, signature):
        resp = self.http_request("verifymessage", [addr, signature, message])
        result = False
        if resp["result"] != None:
            result = resp["result"]
        return result

    def omni_decode_hex_transaction(self, trx_hex):
        resp = self.http_request("decoderawtransaction", [trx_hex])
        if resp["result"] is not None:
            return resp["result"]
        return ""

    def omni_get_transaction(self, trxid):
        resp = self.http_request("getrawtransaction", [trxid, 1])
        if resp["result"] != None:
            omni_resp = self.http_request("omni_gettransaction", [trxid])
            if omni_resp["result"] != None:
                resp["result"]["omni"] =omni_resp["result"]
                return resp["result"]
            else:
                return resp["result"]
        #print resp
        return ""


    def omni_import_addr(self, addr):
        self.http_request("importaddress", [addr, "", False])

    def omni_get_trx_out(self, addr):
        result = []
        resp = self.collect_http_request("Service.ListUnSpent", [addr])
        if resp.has_key("result") and resp["result"] != None:
            trx_unspent = resp["result"]
            for tx in trx_unspent:
                if tx is None:
                    continue
                result.append(
                    {"amount": tx["value"], "txid": tx["txid"], "vout": tx["vout"], "scriptPubKey": tx["scriptPubKey"]})
        return result

    def omni_get_balance(self, addr):
        resp = self.http_request("omni_getbalance", [addr,self.config["property_id"]])
        if resp.has_key("result") and resp["result"] is not None and resp["result"].has_key("balance"):
            return resp["result"]["balance"]
        else:
            return "0"

    def floatToInt(self,f):
        i = 0
        if f > 0:
            i = (f * 10 + 5) / 10
        elif f < 0:
            i = (f * 10 - 5) / 10
        else:
            i = 0
        return int(i)

    def omni_create_transaction(self, from_addr, dest_info):
        txout = self.omni_get_trx_out(from_addr)
        omni_balance = self.omni_get_balance(from_addr)
        if len(txout) == 0:
            return ""

        sum = 0.0
        vin_need = []
        fee = self.config["fee"]
        amount = 0.0
        vouts = {}
        for addr, num in dest_info.items():
            amount = round(amount + num, 8)
            vouts[addr] = round(0.00000546, 8)

        if len(vouts) != 1 :
            logger.error("dest info is invaild %v",dest_info)
            return ""
        if float(omni_balance<amount):
            logger.error("omni balance is insufficient")
            return ""
        txout = sorted(txout, key=lambda d: float(d["amount"]), reverse=True)
        # {"amount":tx["value"],"txid":tx["txid"],"vout":tx["vout"],"scriptPubKey":tx["scriptPubKey"]}
        all_need_amount = round(fee, 8)
        bak_index = -1

        for i in range(len(txout)):
            if sum >= round(fee, 8):
                break
            sum = round(sum + float(txout[i].get("amount")), 8)
            vin_need.append(txout[i])
        has_546 = False
        for i in range(len(txout)):
            if round(float(txout[i].get("amount")), 8) == 0.00000546:
                vin_need.append(txout[i])
                has_546 = True
                break


        if sum < round(fee, 8):
            return ""
        vins = []
        script = []
        for need in vin_need:
            pubkey = need.get('scriptPubKey')
            script.append(pubkey)
            vin = {'txid': need.get('txid'), 'vout': int(need.get('vout')), 'scriptPubKey': pubkey}
            vins.append(vin)
        # set a fee
        resp = ""
        trx_size = len(vin_need) * self.config["vin_size"] + (len(vouts) + 1) * self.config["vout_size"] +40
        cal_fee = math.ceil(trx_size / 1000.0) * self.config["per_fee"]
        cal_fee = round(cal_fee, 8)
        if cal_fee > fee:
            logger.error("cal fee large than max fee!")
            return ""
        #add usdt payload vout
        omni_payload = "%04x%04x%08x%016x"%(0,0,self.config["property_id"],self.floatToInt(amount*math.pow(10,8)))

        if not has_546:
            cal_fee +=0.00000546
        if round(fee, 8) == cal_fee:
            resp = self.http_request("createrawtransaction", [vins, vouts])

        else:
            if vouts.has_key(from_addr):

                vouts[from_addr] = round(sum - cal_fee + vouts[from_addr], 8)
            else:
                if round(fee - cal_fee, 8) > 0.00000546:
                    vouts[from_addr] = round(sum - cal_fee, 8)
            resp = self.http_request("createrawtransaction", [vins, vouts])
        if resp["result"] != None:
            trx_hex = resp['result']
            #use payload rebuild raw trx
            omni_rawtrx_res = self.http_request("omni_createrawtx_opreturn", [trx_hex, omni_payload])
            if omni_rawtrx_res["result"] != None:
                trx_hex = omni_rawtrx_res['result']
                trx = self.omni_decode_hex_transaction(trx_hex)
                return {"trx": trx, "hex": trx_hex, "scriptPubKey": script}

        return ""

    def omni_combine_trx(self, signatures):
        resp = self.http_request("combinerawtransaction", [signatures])
        if resp["result"] is None:
            return ""
        trx = self.omni_decode_hex_transaction(resp["result"])
        return {"hex": resp["result"], "trx": trx}

    def omni_sign_transaction(self, addr, redeemScript, trx_hex):
        resp = self.http_request("dumpprivkey", [addr])
        if resp["result"] is None:
            return ""
        prikey = resp["result"]
        resp = self.omni_decode_hex_transaction(trx_hex)
        vins = resp.get("vin")
        sign_vins = []
        for vin in vins:
            ret = self.http_request("gettxout", [vin.get('txid'), vin.get('vout')])
            if ret.get("result") is None:
                return ""
            ret = ret.get("result")
            sign_vins.append(
                {"txid": vin.get('txid'), "vout": vin.get('vout'), "scriptPubKey": ret.get("scriptPubKey").get("hex"),
                 "redeemScript": redeemScript})
            # "54210204cf519681cc19aa9a9fea60b641daecae99d48bce37570ec4a141eec1d16b87210376d1033db8ca28a837394f8280d8982620668c609aa1692baca1496a294271c42103bc770094d5fe4f2be6eeb7db1c7ee4c29315d75f9da15abea4d2f9dfee9578462102ca5209ff1d0cfbaeeb1ff7511a089110e0da3ea8f9e11f5a38c7a198b2c6d8f3210215e01b25a3d10919e335267f6b95ad5dab4589659cee33983e3cf97e80f13ad721030f610c3a4cad41c87eec4aa1dc40ab0ca8cd3cd8338156da076defa03ed057db2103065d0cd3c5f1f21394200597e4fa56ce676a91ad8c26f5fe8d87dd8afbea947b57ae"})
        resp = self.http_request("signrawtransaction", [trx_hex, sign_vins, [prikey]])
        trx_hex = ""
        if resp["result"] != None:
            trx_hex = resp["result"]
        return trx_hex

    def omni_backup_wallet(self):
        self.http_request("backupwallet", ["/var/backup_keystore/" + self.name + "_wallet.dat"])


'''
    #no
    def hc_backup_wallet(self):
        self.http_request("backupwallet", ["/var/backup_keystore/"+self.name+"_wallet.dat"])


    def hc_get_withdraw_balance(self):
        rep = self.http_request("getbalance", ["default"])
        balance = 0.0
        if rep["result"] != None:
            balance = rep["result"]
        return balance
'''
