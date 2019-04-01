# -*- coding: utf-8 -*-

import requests
import json
from base64 import encodestring
# from config import Db
import math
# db =Db

class btm_utils:
    def __init__(self, name, conf):
        self.name = name
        self.config = conf

    # 请求中间件
    def collect_http_request(self, method, args):
        url = "http://%s:%s" % (self.config["collect_host"], self.config["collect_port"])
        return self.base_http_request(url, method, args)

    # 请求钱包
    def http_request(self, method, args):
        url = "http://%s:%s/%s" % (self.config["host"], self.config["port"], method)
        if args is not None:
            if not isinstance(args, dict):
                raise Exception("invalid args type, should be dict")
            payload = json.dumps(args)
            requests.packages.urllib3.disable_warnings()
            response = requests.request("POST", url, data=payload, verify=False)
            rep = response.json()
            return rep
        else:
            requests.packages.urllib3.disable_warnings()
            response = requests.request("GET", url, verify=False)
            rep = response.json()
            return rep

    def base_http_request(self, url, method, args):
        user = 'a'
        passwd = 'b'
        basestr = encodestring('%s:%s' % (user, passwd))[:-1]
        args_j = json.dumps(args)
        payload = "{\"jsonrpc\":\"1.0\",\r\n \"id\": 1,\r\n \"method\": \"%s\",\r\n \"params\": %s\r\n}" % (method, args_j)
        headers = {
            'content-type': "application/json",
            'authorization': "Basic %s" % (basestr),
            'cache-control': "no-cache",
        }

        requests.packages.urllib3.disable_warnings()
        response = requests.request("POST", url, data=payload, headers=headers, verify=False)
        rep = response.json()

        return rep

    def btm_get_trx_out(self, addr):
        result = []
        resp = self.collect_http_request("Service.ListUnSpent", [addr])
        if resp.get("result") is not None:
            trx_unspent = resp["result"]
            for tx in trx_unspent:
                if tx is None:
                    continue
                result.append({"amount":tx["value"],"txid":tx["txid"],"vout":tx["vout"],"scriptPubKey":tx["scriptPubKey"],"address":tx["address"]})
        return result

    def btm_get_balance(self, addr):
        resp = self.collect_http_request("Service.GetBalance", [addr])
        if "result" in resp and resp.get("result") is not None:
            s = "%d" % (resp["result"])
            balanceStr = ""
            if len(s) <= 8:
                balanceStr = "0." + "0" * (8 - len(s)) + s
            else:
                balanceStr = s[:-8] + "." + s[-8:]
            return balanceStr
        else:
            return "0"

    def btm_get_block_height(self):
        resp = self.collect_http_request("Service.GetBlockHeight", [])
        if "result" in resp and resp.get("result") is not None:
            return resp["result"]
        else:
            return 0

    def btm_get_transaction(self, trxid):
        resp = self.collect_http_request("Service.GetTrxBlockHeight", [trxid])
        block_height = 0

        if "result" in resp and resp.get("result") is not None:
            block_height = resp["result"]
        else:
            return ""

        args = "%d|%s" % (block_height,trxid)
        resp = self.collect_http_request("Service.GetTrx", [args])

        if "result" in resp and resp.get("result") is not None:
            return resp["result"]
        else:
            return ""

    def btm_create_multisig(self, pubs, count):
        resp = self.collect_http_request("Service.CreateMultiSig", [[pubs, count]])
        if "result" in resp and resp.get("result") is not None:
            return resp["result"]
        else:
            raise Exception(resp["error"])

    def btm_validate_address(self, addr):
        json_obj = {"address": addr}
        resp = self.http_request("validate-address", json_obj)
        if resp.get("status") is not None:
            if resp["status"] == "success":
                return resp["data"]["valid"]
            else:
                raise Exception(resp["msg"])

    def btm_broadcaset_trx(self, trx):
        json_obj = {"raw_transaction": trx}
        resp = self.http_request("submit-transaction", json_obj)
        if resp.get("status") is not None:
            if resp["status"] == "success":
                return resp["data"]["tx_id"]
            else:
                raise Exception(resp["msg"])

    def btm_decode_hex_transaction(self, trx_hex):
        json_obj = {"raw_transaction": trx_hex}
        resp = self.http_request("decode-raw-transaction", json_obj)
        if resp.get("status") is not None:
            if resp["status"] == "success":
                return resp["data"]
            else:
                raise Exception(resp["msg"])

    def btm_estimate_transaction_gas(self, trx_tpl):
        json_obj = {"transaction_template": trx_tpl}
        resp = self.http_request("estimate-transaction-gas", json_obj)
        if resp.get("status") is not None:
            if resp["status"] == "success":
                return resp["data"]["total_neu"]
            else:
                raise Exception(resp["msg"])

    def btm_build_spend_utxo_transaction(self, vins,vouts):
        resp = self.collect_http_request("Service.BuildTransaction", [[vins,vouts]])
        if "result" in resp and resp.get("result") is not None:
            return resp.get("result")
        else:
            return None

    def btm_get_amount_value(self, amount):
        amount_value = 0
        if isinstance(amount, str):
            amount_value = int(amount)
        elif isinstance(amount, unicode):
            amount_value = int(amount.encode("ascii"))
        elif isinstance(amount, int):
            amount_value = amount
        elif isinstance(amount, long):
            amount_value = amount
        else:
            raise Exception("invalid amount value")
        return amount_value


    def btm_create_transaction(self, from_addr, dest_info):
        txout = self.btm_get_trx_out(from_addr)

        if len(txout) == 0:
            return ""
        sum = 0
        vin_need = []
        fee = self.config["fee"]

        amount = 0
        vouts = {}
        for addr, num in dest_info.items():
            num_value = 0
            if isinstance(num, int) or isinstance(num, long):
                num_value = num * 100000000
            elif isinstance(num, float):
                num_value = int(math.floor(num * 100000000 + 0.5))
            elif isinstance(num, str):
                num_value = int(math.floor(float(num) * 100000000 + 0.5))
            elif isinstance(num, unicode):
                num_value = int(math.floor(float(num.encode("utf8")) * 100000000 + 0.5))
            else:
                return ""
            amount = amount + num_value
            vouts[addr] = num_value
        txout = sorted(txout, key=lambda d: self.btm_get_amount_value(d.get("amount")), reverse=True)
        all_need_amount = amount + fee
        bak_index = -1
        use_idx = []

        if len(txout) > 20:
            for i in range(len(txout)):
                if self.btm_get_amount_value(txout[i].get("amount")) >= all_need_amount:
                    bak_index = i
                elif self.btm_get_amount_value(txout[i].get("amount")) < all_need_amount and bak_index != -1:
                    sum = sum + self.btm_get_amount_value(txout[bak_index].get("amount"))
                    vin_need.append(txout[bak_index])
                    use_idx.append(bak_index)
                    break
                elif self.btm_get_amount_value(txout[i].get("amount")) < all_need_amount and bak_index == -1:
                    break

        if bak_index == -1:
            for i in range(len(txout)):
                if sum >= amount + fee:
                    break
                sum = sum + self.btm_get_amount_value(txout[i].get("amount"))
                vin_need.append(txout[i])
                use_idx.append(i)
        if len(txout) > 20 and len(vin_need) < 6:
            for i in range(6 - len(vin_need)):
                cur_idx = len(txout) - i - 1
                if cur_idx not in use_idx:
                    sum = sum + self.btm_get_amount_value(txout[cur_idx].get("amount"))
                    vin_need.append(txout[cur_idx])
                    use_idx.append(cur_idx)

        if len(vin_need) > 8:
            return ""

        if sum < all_need_amount:
            return ""
        vins = []
        script = []
        for need in vin_need:
            pubkey = need.get('scriptPubKey')
            script.append(pubkey)
            vin = {'txid': need.get('txid'), 'vout': int(need.get('vout')), 'scriptPubKey': pubkey,
                   'value': need.get("amount"), 'address': need.get('address')}
            vins.append(vin)

        # estimate fee
        needchange = sum - amount - fee
        if needchange == 0:
            if from_addr in vouts:
                pass
            else:
                # 找零1个NEU单位的BTM 先占用一个outputs的位置
                vouts[from_addr] = 1
        else:
            if from_addr in vouts:
                vouts[from_addr] = vouts[from_addr] + needchange
            else:
                vouts[from_addr] = needchange

        # 将金额转成string
        for k, v in vouts.iteritems():
            vouts[k] = str(v)

        trx_tpl = self.btm_build_spend_utxo_transaction(vins,vouts)

        estimate_fee = trx_tpl.get("est_fee")

        print "estimate_fee", estimate_fee

        # 使用预估手续费上浮10%作为手续费
        if float(estimate_fee * 1.1) >= float(fee):
            return ""

        # 手续费差额找零
        needchange2 = fee - int(estimate_fee * 1.1)
        vouts[from_addr] = str(int(vouts[from_addr]) + needchange2)

        trx_tpl = self.btm_build_spend_utxo_transaction(vins,vouts)

        print trx_tpl

        if trx_tpl.get("trx").get("raw_transaction") is not None:
            trx_hex = trx_tpl["trx"]['raw_transaction']

            trx = self.btm_decode_hex_transaction(trx_hex)
            return {"trx": trx, "hex": trx_hex, "scriptPubKey": script}
        return ""






