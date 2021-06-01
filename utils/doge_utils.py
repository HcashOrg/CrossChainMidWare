# -*- coding: utf-8 -*-
import requests
from base64 import encodestring
import json
from service import logger, app
import traceback


def doge_request(method, args):
    url = "http://%s:%s" % (app.config['DOGE_HOST'], app.config['DOGE_PORT'])
    user = 'a'
    passwd = 'b'
    basestr = encodestring('%s:%s' % (user, passwd))[:-1]
    '''x = []
    for arg in args:
        x.append(arg)'''
    args_j = json.dumps(args)
    payload = "{\r\n \"id\": 1,\r\n \"method\": \"%s\",\r\n \"params\": %s\r\n}" % (method, args_j)
    headers = {
        'content-type': "text/plain",
        'authorization': "Basic %s" % (basestr),
        'cache-control': "no-cache",
    }
    logger.info(payload)
    response = requests.request("POST", url, data=payload, headers=headers)
    rep = response.json()
    logger.info(rep)
    return rep


def doge_create_multisig(addrs, amount):
    resp = doge_request("createmultisig", [amount, addrs])
    if resp["result"] != None:
        try:
            doge_request("importaddress", [resp["result"].get("address"),"",False])
        except:
            pass
        return resp["result"]
    else:
        return None


def doge_add_multisig(addrs, amount):
    resp = doge_request("addmultisigaddress", [amount, addrs])
    if resp["result"] != None:
        return resp["result"]
    else:
        return None


def doge_validate_address(addr):
    resp = doge_request("validateaddress", [addr])
    if resp["result"] != None:
        return resp["result"]
    else:
        return None


def doge_create_address():
    resp = doge_request("getnewaddress", [""])
    address = ""
    if resp["result"] != None:
        address = resp["result"]
    return address


def doge_query_tx_out(addr):
    message = [addr]
    resp = doge_request("listunspent",[0,9999999,message])
    if resp["result"] != None:
        return resp["result"]
    else:
        return None


def doge_broadcaset_trx(trx):
    resp = doge_request("sendrawtransaction", [trx])
    result = ""
    if resp["result"] != None:
        result = resp["result"]
    return result


def doge_sign_message(addr, message):
    resp = doge_request("signmessage", [addr, message])
    signed_message = ""
    if resp["result"] != None:
        signed_message = resp["result"]
    return signed_message


def doge_verify_signed_message(addr, message, signature):
    resp = doge_request("verifymessage", [addr, signature, message])
    result = False
    if resp["result"] != None:
        result = resp["result"]
    return result


def doge_decode_hex_transaction(trx_hex):
    resp = doge_request("decoderawtransaction",[trx_hex])
    if resp["result"] is not None :
        return resp["result"]
    return ""
def doge_validate_address(addr):
    resp = doge_request("validateaddress", [addr])
    address = ""
    if resp["result"] != None:
        address = resp["result"]
    return address


def doge_get_transaction(trxid):
    resp = doge_request("getrawtransaction", [trxid])
    if resp["result"] != None:
        return doge_decode_hex_transaction(resp["result"])
    return ""
def doge_import_addr(addr):
    doge_request("importaddress",[addr,"",False])

def doge_create_transaction(from_addr,dest_info):
    txout = doge_query_tx_out(from_addr)
    if txout == None :
        return ""
    sum = 0.0
    vin_need =[]
    fee = 0.001
    amount=0.0
    vouts ={}
    for addr, num in dest_info.items():
        amount += num
        vouts[addr] = num

    for out in txout :
        if sum >= amount+fee:
            break
        sum+=float(out.get("amount"))
        vin_need.append(out)
    if sum < amount+fee:
        return ""
    vins=[]
    script =[]
    for need in vin_need :
        pubkey=need.get('scriptPubKey')
        script.append(pubkey)
        vin={'txid':need.get('txid'),'vout':need.get('vout'),'scriptPubKey':pubkey}
        vins.append(vin)
    #set a fee
    resp = ""
    if sum-amount == fee:
        resp = doge_request("createrawtransaction", [vins, vouts])
    else:
        vouts[from_addr] = round(sum - amount - fee,8)
        resp = doge_request("createrawtransaction", [vins, vouts])
    if resp["result"] != None:
        trx_hex = resp['result']
        trx = doge_decode_hex_transaction(trx_hex)
        return {"trx":trx,"hex":trx_hex,"scriptPubKey":script}
    return ""


def doge_combineTrx(signatures) :
    resp = doge_request("combinerawtransaction",[signatures])
    if resp["result"] is None:
        return ""
    trx = doge_decode_hex_transaction(resp["result"])
    return {"hex":resp["result"], "trx":trx}


def doge_sign_transaction(addr,redeemScript,trx_hex):
    resp = doge_request("dumpprivkey",[addr])
    if resp["result"] is None :
        return ""
    prikey = resp["result"]
    resp = doge_decode_hex_transaction(trx_hex)
    vins = resp.get("vin")
    sign_vins=[]
    for vin in vins:
        ret = doge_request("gettxout",[vin.get('txid'),vin.get('vout')])
        if ret.get("result") is None:
            return ""
        ret = ret.get("result")
        sign_vins.append({"txid":vin.get('txid'),"vout":vin.get('vout'),"scriptPubKey":ret.get("scriptPubKey").get("hex"),"redeemScript": redeemScript})
            #"54210204cf519681cc19aa9a9fea60b641daecae99d48bce37570ec4a141eec1d16b87210376d1033db8ca28a837394f8280d8982620668c609aa1692baca1496a294271c42103bc770094d5fe4f2be6eeb7db1c7ee4c29315d75f9da15abea4d2f9dfee9578462102ca5209ff1d0cfbaeeb1ff7511a089110e0da3ea8f9e11f5a38c7a198b2c6d8f3210215e01b25a3d10919e335267f6b95ad5dab4589659cee33983e3cf97e80f13ad721030f610c3a4cad41c87eec4aa1dc40ab0ca8cd3cd8338156da076defa03ed057db2103065d0cd3c5f1f21394200597e4fa56ce676a91ad8c26f5fe8d87dd8afbea947b57ae"})
    resp = doge_request("signrawtransaction", [trx_hex,sign_vins,[prikey]])
    trx_hex = ""
    if resp["result"] != None:
        trx_hex = resp["result"]
    return trx_hex


def doge_backup_wallet():
    doge_request("backupwallet", ["/var/backup_keystore/doge_wallet.dat"])


def doge_get_withdraw_balance():
    rep = doge_request("getbalance", ["doge_withdraw_test"])
    balance = 0.0
    if rep["result"] != None:
        balance = rep["result"]
    return balance
    # btc_collect_money("1ERjyPUWpDH7mLmAHZzwCJ6jsn4tyHfj2Y")
