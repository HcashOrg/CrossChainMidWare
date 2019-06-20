# -*- coding: utf-8 -*-

from service import jsonrpc
from config import logger,App
from utils import eth_utils
from utils import etp_utils
from service import db
from service import sim_btc_plugin,sim_btc_utils_all
from service import hc_plugin
from service import usdt_plugin
from service import btm_plugin
from utils import error_utils
import pymongo
from datetime import datetime
from config.erc_conf import erc_chainId_map
import json
import leveldb
import time
import hashlib
last_clean_broadcast_cache_time = time.time()


def DeprecatedFunction(f):
    def func():
        pass
    return func


@DeprecatedFunction
@jsonrpc.method('Zchain.Crypt.Sign(chainId=str, addr=str, message=str)')
def zchain_crypt_sign(chainId, addr, message):
    logger.info('Zchain.Crypt.Sign')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    signed_message = ""
    if sim_btc_plugin.has_key(chainId):
        signed_message = sim_btc_plugin[chainId].sim_btc_sign_message(addr, message)
    elif chainId == "hc":
        signed_message = hc_plugin.hc_sign_message(addr, message)
    else:
        return error_utils.invalid_chainid_type(chainId)

    if signed_message == "":
        return error_utils.error_response("Cannot sign message.")

    return {
        'chainId': chainId,
        'data': signed_message
    }


@DeprecatedFunction
@jsonrpc.method('Zchain.Trans.Sign(chainId=str,addr=str, trx_hex=str, redeemScript=str)')
def zchain_Trans_sign(chainId,addr, trx_hex, redeemScript):
    logger.info('Zchain.Trans.Sign')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    signed_trx = ""
    if sim_btc_plugin.has_key(chainId):
        signed_trx = sim_btc_plugin[chainId].sim_btc_sign_transaction(addr, redeemScript,trx_hex)
    elif chainId == "hc":
        signed_trx = hc_plugin.hc_sign_transaction(addr, redeemScript,trx_hex)
    else:
        return error_utils.invalid_chainid_type(chainId)

    if signed_trx == "":
        return error_utils.error_response("Cannot sign trans.")

    return {
        'chainId': chainId,
        'data': signed_trx
    }

@jsonrpc.method('Zchain.Addr.GetAddErc(chainId=str)')
def zchain_Addr_GetAddErc(chainId,addr,precison):
    logger.info('Zchain.Addr.GetAddErc')

    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    asset = None
    if erc_chainId_map.has_key(chainId):
        asset = erc_chainId_map[chainId]

    if asset is None:
        return {}
    else:
        return{
            'chainId':asset['chainId'],
            'address':asset['address'],
            'precision':asset['precison']
        }

@jsonrpc.method('Zchain.Trans.broadcastTrx(chainId=str, trx=str)')
def zchain_trans_broadcastTrx(chainId, trx):
    logger.info('Zchain.Trans.broadcastTrx')
    global last_clean_broadcast_cache_time
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    md = hashlib.md5()
    md.update(trx)
    trxId = md.hexdigest()

    broad_cast_record = db.get_collection("b_broadcast_trans_cache").find_one({"chainId": chainId,"trx":trxId,"effectiveTime":{"$gt":int(time.time())-10}})
    if broad_cast_record is not None:
        if broad_cast_record['result'] == "":
            return error_utils.error_response("Cannot broadcast transactions.")
        return {
            'chainId': chainId,
            'data': broad_cast_record['result']
        }

    result = ""
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_broadcaset_trx(trx)
    elif chainId == "hc":
        result = hc_plugin.hc_broadcaset_trx(trx)
    elif chainId =="usdt":
        result = usdt_plugin.omni_broadcaset_trx(trx)
    elif chainId == "btm":
        result = btm_plugin.btm_broadcaset_trx(trx)
    elif chainId.lower() == "eth":
        result = eth_utils.eth_send_raw_transaction(trx)
    elif 'erc' in chainId.lower():
        result = eth_utils.eth_send_raw_transaction(trx)
    else:
        return error_utils.invalid_chainid_type(chainId)

    db.get_collection("b_broadcast_trans_cache").insert_one(
        {"chainId": chainId, "trx": trxId, "effectiveTime": int(time.time()), "result": result})
    if int(time.time())- last_clean_broadcast_cache_time>10*60:
        db.get_collection("b_broadcast_trans_cache").delete_many({"effectiveTime":{"$lt":int(time.time())-10}})
        last_clean_broadcast_cache_time = int(time.time())
    if result == "":
        return error_utils.error_response("Cannot broadcast transactions.")


    return {
        'chainId': chainId,
        'data': result
    }

@DeprecatedFunction
@jsonrpc.method('Zchain.Addr.importAddrs(chainId=str,addrs=list)')
def zchain_addr_import_addrs(chainId,addrs):
    logger.info('Zchain.Addr.importAddrs')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    for addr in addrs:
        if sim_btc_plugin.has_key(chainId):
            sim_btc_plugin[chainId].sim_btc_import_addr(addr)
        elif chainId == "hc":
            hc_plugin.hc_import_addr(addr)
        elif chainId =="usdt":
            usdt_plugin.omni_import_addr(addr)
        elif chainId.lower() == 'eth':
            if "erc" in addr:
                temp_chainId = chainId.lower()
                pos = addr.find("erc")
                handle_addr = addr[0:pos]
                asset = db.b_eths_address.find_one({'chainId': temp_chainId, 'address': handle_addr})
                if asset == None:
                    db.b_eths_address.insert({'chainId': temp_chainId, 'address': handle_addr, 'isContractAddress': True})
                else:
                    db.b_eths_address.update({'chainId': temp_chainId, 'address': handle_addr},
                                             {"$set": {'isContractAddress': True}})
            else:
                temp_chainId = chainId.lower()
                asset = db.b_eths_address.find_one({'chainId': temp_chainId, 'address': addr})
                if asset == None:
                    db.b_eths_address.insert({'chainId': temp_chainId, 'address': addr, 'isContractAddress': False})
                else:
                    db.b_eths_address.update({'chainId': temp_chainId, 'address': addr},
                                             {"$set": {'isContractAddress': False}})
            eth_utils.add_guard_address(addr)
        elif ('erc' in chainId.lower()):
            erc_asset = None
            if erc_chainId_map.has_key(chainId):
                erc_asset = erc_chainId_map[chainId]
            if erc_asset != None:
                if "erc" in addr:
                    pos = addr.find("erc")
                    handle_addr = addr[0:pos]
                    asset = db.b_eths_address.find_one({'chainId': chainId, 'address': handle_addr})
                    if asset == None:
                        db.b_eths_address.insert(
                            {'chainId': chainId, 'address': handle_addr, 'isContractAddress': True})
                    else:
                        db.b_eths_address.update({'chainId': chainId, 'address': handle_addr},
                                                 {"$set": {'isContractAddress': True}})
                else:
                    asset = db.b_eths_address.find_one({'chainId': chainId, 'address': addr})
                    if asset == None:
                        db.b_eths_address.insert(
                            {'chainId': chainId, 'address': addr, 'isContractAddress': False})
                    else:
                        db.b_eths_address.update({'chainId': chainId, 'address': addr},
                                                 {"$set": {'isContractAddress': False}})
                eth_utils.add_guard_address(addr)
        else:
            return error_utils.invalid_chainid_type(chainId)
    return {
        'chainId': chainId,
        'data': ""
    }

@DeprecatedFunction
@jsonrpc.method('Zchain.Addr.importAddr(chainId=str, addr=str)')
def zchain_addr_importaddr(chainId, addr):
    logger.info('Zchain.Addr.importAddr')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if sim_btc_plugin.has_key(chainId):
        sim_btc_plugin[chainId].sim_btc_import_addr(addr)
    elif chainId == "hc":
        hc_plugin.hc_import_addr(addr)
    elif chainId == "usdt":
        usdt_plugin.omni_import_addr(addr)
    elif chainId.lower() == 'eth':
        if "erc" in addr:
            temp_chainId = chainId.lower()
            pos = addr.find("erc")
            handle_addr = addr[0:pos]
            asset = db.b_eths_address.find_one({'chainId':temp_chainId,'address':handle_addr})
            if asset == None:
                db.b_eths_address.insert({'chainId': temp_chainId, 'address': handle_addr, 'isContractAddress': True})
            else:
                db.b_eths_address.update({'chainId':temp_chainId,'address':handle_addr},{"$set":{ 'isContractAddress': True}})
        else:
            temp_chainId = chainId.lower()
            asset = db.b_eths_address.find_one({'chainId': temp_chainId, 'address': addr})
            if asset == None:
                db.b_eths_address.insert({'chainId': temp_chainId, 'address': addr, 'isContractAddress': False})
            else:
                db.b_eths_address.update({'chainId':temp_chainId,'address':addr},{"$set":{ 'isContractAddress': False}})
        eth_utils.add_guard_address(addr)
    elif ('erc' in chainId.lower()):
        erc_asset = None
        if erc_chainId_map.has_key(chainId):
            erc_asset = erc_chainId_map[chainId]
        if erc_asset != None:
            if "erc" in addr:
                pos = addr.find("erc")
                handle_addr = addr[0:pos]
                asset = db.b_eths_address.find_one({'chainId': chainId, 'address': handle_addr})
                if asset == None:
                    db.b_eths_address.insert(
                        {'chainId': chainId, 'address': handle_addr, 'isContractAddress': True})
                else:
                    db.b_eths_address.update({'chainId': chainId, 'address': handle_addr},
                                             {"$set": {'isContractAddress': True}})
            else:
                asset = db.b_eths_address.find_one({'chainId': chainId, 'address': addr})
                if asset == None:
                    db.b_eths_address.insert(
                        {'chainId': chainId, 'address': addr, 'isContractAddress': False})
                else:
                    db.b_eths_address.update({'chainId': chainId, 'address': addr},
                                             {"$set": {'isContractAddress': False}})
            eth_utils.add_guard_address(addr)
    else:
        return error_utils.invalid_chainid_type(chainId)
    return {
        'chainId': chainId,
        'data': ""
    }


@jsonrpc.method('Zchain.Exchange.queryContracts(from_asset=str, to_asset=str, limit=int)')
def zchain_exchange_queryContracts(from_asset, to_asset, limit):
    logger.info('Zchain.Exchange.queryContracts')

    if type(limit) != int:
        return error_utils.mismatched_parameter_type('limit', 'INTEGER')
    if limit <= 0:
        limit = 10

    contracts = db.b_exchange_contracts.find(
        {
            "from_asset": from_asset,
            "to_asset": to_asset
        },
        {"_id": 0}
    ).sort("price").limit(limit)

    return {
        'data': list(contracts)
    }

@jsonrpc.method('Zchain.Trans.getEthTrxCount(chainId=str,addr=str,indexFormat=str)')
def zchain_trans_getEthTrxCount(chainId, addr, indexFormat):
    logger.info('Zchain.Trans.getEthTrxCount')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    chainId = chainId.lower()
    result = {}
    if 'erc' in chainId:
        result = eth_utils.eth_get_trx_count(addr,indexFormat)
    elif 'eth' == chainId:
        result = eth_utils.eth_get_trx_count(addr, indexFormat)
    else:
        return error_utils.invalid_chainid_type(chainId)
    if result == {}:
        return error_utils.error_response("Cannot eth trx count.")
    #print result
    return result

@jsonrpc.method('Zchain.Query.getBlockHeight(chainId=str)')
def zchain_query_getBlockHeight(chainId):
    logger.info('Zchain.Query.getBlockHeight')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    chainId = chainId.lower()
    result = {}
    if 'erc' in chainId:
        result = eth_utils.eth_get_block_height()
    elif 'eth' == chainId:
        result = eth_utils.eth_get_block_height()
    elif 'btm' == chainId:
        result = btm_plugin.btm_get_block_height()
    elif 'hc' == chainId:
        cache_record = db.get_collection("b_config").find_one({"key" : "hcsyncblocknum"})
        if cache_record is not None:
            result = int(cache_record["value"])
        else:
            result=0
    else:
        return error_utils.invalid_chainid_type(chainId)
    if result == {}:
        return error_utils.error_response("Cannot eth trx count.")
    #print result
    return result


@jsonrpc.method('Zchain.Query.getTrxHistoryByAddress(chainId=str,address=str,startBlock=str,endBlock=str)')
def zchain_query_getTrxHistoryByAddress(chainId,address,startBlock,endBlock):
    logger.info('Zchain.Query.getTrxHistoryByAddress')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    chainId = chainId.lower()
    result = []
    if 'erc' in chainId:
        result = eth_utils.eth_get_trx_history_by_address(address,startBlock,endBlock)
    elif 'eth' == chainId:
        result = eth_utils.eth_get_trx_history_by_address(address,startBlock,endBlock)
    else:
        return error_utils.invalid_chainid_type(chainId)
    #print result
    return result


@jsonrpc.method('Zchain.Query.getEthTrx(chainId=str,trxid=str)')
def zchain_query_getEthTrx(chainId,trxid):
    logger.info('Zchain.Query.getEthTrx')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    chainId = chainId.lower()
    result = {}
    if 'erc' in chainId:
        result = eth_utils.eth_get_trx(trxid)
    elif 'eth' == chainId:
        result = eth_utils.eth_get_trx(trxid)
    else:
        return error_utils.invalid_chainid_type(chainId)
    #print result
    return result

@jsonrpc.method('Zchain.Query.getUtxoCount(chainId=str,address=str)')
def zchain_query_getUtxoCount(chainId,address):
    logger.info('Zchain.Query.getUtxoCount')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    chainId = chainId.lower()
    result = {}
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_get_trx_out(address)
    elif chainId == "hc":
        result = hc_plugin.hc_get_trx_out(address)
    elif chainId == "usdt":
        result = usdt_plugin.omni_get_trx_out(address)
    elif chainId == "btm":
        result = btm_plugin.btm_get_trx_out(address)
    else:
        return error_utils.invalid_chainid_type(chainId)
    #print result
    return len(result)



@jsonrpc.method('Zchain.Trans.createTrx(chainId=str, from_addr=str,dest_info=dict)')
def zchain_trans_createTrx(chainId, from_addr,dest_info):
    logger.info('Zchain.Trans.createTrx')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    chainId = chainId.lower()
    result = {}
    if sim_btc_plugin.has_key(chainId):
        is_fast_record = db.get_collection("b_config").find_one({"key": "is_fast"})
        is_fast = False
        if is_fast_record is not None:
            is_fast = bool(is_fast_record["value"])
        result = sim_btc_plugin[chainId].sim_btc_create_transaction(from_addr,dest_info,is_fast)
    elif chainId == "hc":
        result = hc_plugin.hc_create_transaction(from_addr, dest_info)
    elif chainId == "usdt":
        result = usdt_plugin.omni_create_transaction(from_addr,dest_info)
    elif chainId == "btm":
        result = btm_plugin.btm_create_transaction(from_addr, dest_info)
    else:
        return error_utils.invalid_chainid_type(chainId)

    if result == {}:
        return error_utils.error_response("Cannot create transaction.")

    return {
        'chainId': chainId,
        'data': result
    }


@DeprecatedFunction
@jsonrpc.method('Zchain.Trans.CombineTrx(chainId=str, transactions=list)')
def zchain_trans_CombineTrx(chainId, transactions):
    logger.info('Zchain.Trans.CombineTrx')
    chainId = chainId.lower()
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    result = ""
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_combine_trx(transactions)
    elif chainId == "hc":
        result = hc_plugin.hc_combine_trx(transactions)
    elif chainId == "usdt":
        result = sim_btc_plugin["btc"].sim_btc_combine_trx(transactions)
    else:
        return error_utils.invalid_chainid_type(chainId)

    if result == "":
        return error_utils.error_response("Cannot combine transaction.")

    return {
        'chainId': chainId,
        'data': result
    }


@jsonrpc.method('Zchain.Trans.DecodeTrx(chainId=str, trx_hex=str)')
def zchain_trans_decodeTrx(chainId, trx_hex):
    chainId = chainId.lower()
    logger.info('Zchain.Trans.DecodeTrx')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    result = ""
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_decode_hex_transaction(trx_hex)
    elif chainId == "hc":
        result = hc_plugin.hc_decode_hex_transaction(trx_hex)
    elif chainId == "usdt":
        result = usdt_plugin.omni_decode_hex_transaction(trx_hex)
    elif chainId == "btm":
        result = btm_plugin.btm_decode_hex_transaction(trx_hex)
    else:
        return error_utils.invalid_chainid_type(chainId)

    if result == "":
        return error_utils.error_response("Cannot create transaction.")

    return {
        'chainId': chainId,
        'data': result
    }


@jsonrpc.method('Zchain.Trans.queryTrans(chainId=str, trxid=str)')
def zchain_trans_queryTrx(chainId, trxid):
    chainId = chainId.lower()
    logger.info('Zchain.Trans.queryTrans')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    result = ""
    is_cache = False

    cache_record = db.get_collection("b_query_trans_cache").find_one({"chainId": chainId,"trxid":trxid})
    if cache_record is not None:
        return {
        'chainId': chainId,
        'data': cache_record["result"]
        }
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_get_transaction(trxid)
        if "vout" in result:
            is_cache = True
            try:
                if "confirmations" in result:
                    if result["confirmations"]<=7:
                        is_cache = False
                else:
                    is_cache = False
            except Exception,ex:
                print "query confirmation failed",ex

    elif chainId == "hc":
        result = hc_plugin.hc_get_transaction(trxid)
        if "vout" in result:
            is_cache = True
            try:
                if "vin" in result and len(result["vin"]) > 0:
                    if result["vin"][0]["blockheight"] <= 0:
                        is_cache = False
            except Exception,ex:
                print "query confirmation failed",ex
    elif chainId == "usdt":
        result = usdt_plugin.omni_get_transaction(trxid)
        if "vout" in result:
            is_cache = True
            try:
                if "confirmations" in result:
                    if result["confirmations"] <= 7:
                        is_cache = False
                else:
                    is_cache = False
            except Exception, ex:
                print "query confirmation failed", ex

    elif chainId == "btm":
        result = btm_plugin.btm_get_transaction(trxid)
        if "outputs" in result:
            is_cache = True

    elif chainId == "eth" or "erc" in chainId:
        source,respit = eth_utils.get_transaction_data(trxid)
        so_re_dic = {'source_trx':source,'respit_trx':respit}
        if "input" in source:
            is_cache = True
        if source != None and respit != None:
            result = so_re_dic
    else:
        return error_utils.invalid_chainid_type(chainId)

    if result == "":
        return error_utils.error_response("Cannot query transaction.")
    if result.has_key("vin"):
        for i in range(len(result["vin"])):
            result["vin"][i]["scriptSig"]={"asm":"","hex":""}
    if is_cache:
        db.get_collection("b_query_trans_cache").insert_one(
            {"chainId": chainId, "trxid": trxid,"result":result})
    return {
        'chainId': chainId,
        'data': result
    }

@jsonrpc.method('Zchain.Trans.queryTransBatch(chainId=str, trxids=list)')
def zchain_trans_queryTrx(chainId, trxids):
    chainId = chainId.lower()
    logger.info('Zchain.Trans.queryTransBatch')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(trxids) != list:
        return error_utils.mismatched_parameter_type('trxids', 'LIST')
    res_data = {}
    for one_txid in trxids:
        result = ""
        is_cache = False
        cache_record = db.get_collection("b_query_trans_cache").find_one({"chainId": chainId,"trxid":one_txid})
        if cache_record is not None:
            res_data[one_txid]=cache_record["result"]
            continue
        if sim_btc_plugin.has_key(chainId):
            result = sim_btc_plugin[chainId].sim_btc_get_transaction(one_txid)
            if "vout" in result:
                is_cache = True
                try:
                    if "confirmations" in result:
                        if result["confirmations"] <= 0:
                            is_cache = False
                except Exception, ex:
                    print "query confirmation failed", ex

        elif chainId == "hc":
            result = hc_plugin.hc_get_transaction(one_txid)
            if "vout" in result:
                is_cache = True
                try:
                    if "vin" in result and len(result["vin"]) > 0:
                        if result["vin"][0]["blockheight"] <= 0:
                            is_cache = False
                except Exception, ex:
                    print "query confirmation failed", ex
        elif chainId == "usdt":
            result = usdt_plugin.omni_get_transaction(one_txid)
            print result
        elif chainId == "btm":
            result = btm_plugin.btm_get_transaction(one_txid)
            print result
        elif chainId == "eth" or "erc" in chainId:
            source,respit = eth_utils.get_transaction_data(one_txid)
            so_re_dic = {'source_trx':source,'respit_trx':respit}
            if "input" in source:
                is_cache = True
            if source != None and respit != None:
                result = so_re_dic
        else:
            continue

        if result == "":
            continue
        if result.has_key("vin"):
            for i in range(len(result["vin"])):
                result["vin"][i]["scriptSig"] = {"asm": "", "hex": ""}
        if is_cache:
            db.get_collection("b_query_trans_cache").insert_one(
                {"chainId": chainId, "trxid": one_txid,"result":result})
        res_data[one_txid] = result
    if len(res_data)<len(trxids):
        for i in range(len(trxids)-len(res_data)):
            res_data["000000"+str(i)]=i
    return {
        'chainId': chainId,
        'data': res_data
    }

@DeprecatedFunction
@jsonrpc.method('Zchain.Trans.getTrxOuts(chainId=str, addr=str)')
def zchain_trans_getTrxOuts(chainId, addr):
    chainId = chainId.lower()
    logger.info('Zchain.Trans.getTrxOuts')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    result = False
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_query_tx_out(addr)
    elif chainId == "hc":
        result = hc_plugin.hc_query_tx_out(addr)
    else:
        return error_utils.invalid_chainid_type(chainId)

    return {
        'chainId': chainId,
        'data': result
    }


@jsonrpc.method('Zchain.Crypt.VerifyMessage(chainId=str, addr=str, message=str, signature=str)')
def zchain_crypt_verify_message(chainId, addr, message, signature):
    chainId = chainId.lower()
    logger.info('Zchain.Crypt.VerifyMessage')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    result = False

    cache_record = db.get_collection("b_verify_cache").find_one({"chainId": chainId,"addr":addr, "message":message, "signature":signature})
    if cache_record is not None:
        result = True
        return {
        'chainId': chainId,
        'data': result
        }


    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_verify_signed_message(addr, message, signature)
    elif chainId == "hc":
        result = hc_plugin.hc_verify_signed_message(addr, message, signature)

    elif (chainId == 'eth') or ('erc' in chainId):
        #print 1
        result = eth_utils.eth_verify_signed_message(addr, message, signature)
    else:
        return error_utils.invalid_chainid_type(chainId)
    if result:
        db.get_collection("b_verify_cache").insert_one(
            {"chainId": chainId, "addr": addr, "message": message, "signature": signature})

    return {
        'chainId': chainId,
        'data': result
    }


@jsonrpc.method('Zchain.Multisig.Create(chainId=str, addrs=list, amount=int)')
def zchain_multisig_create(chainId, addrs, amount):
    chainId = chainId.lower()
    logger.info('Zchain.Multisig.Create')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(addrs) != list:
        return error_utils.mismatched_parameter_type('addrs', 'ARRAY')
    if type(amount) != int:
        return error_utils.mismatched_parameter_type('amount', 'INTEGER')

    address = ""
    redeemScript = ""
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_create_multisig(addrs, amount)
        if result is not None:
            address = result["address"]
            redeemScript = result["redeemScript"]
            mutisig_record = db.get_collection("b_"+chainId+"_multisig_address").find_one({"address": address})
            if mutisig_record is not None:
                db.get_collection("b_"+chainId+"_multisig_address").remove({"address": address})
            data = {"address": address, "redeemScript": redeemScript, "addr_type":0}
            db.get_collection("b_"+chainId+"_multisig_address").insert_one(data)
    elif chainId == "hc":
        result = hc_plugin.hc_create_multisig(addrs, amount)
        if result is not None:
            address = result["address"]
            redeemScript = result["redeemScript"]
            mutisig_record = db.get_collection("b_hc_multisig_address").find_one({"address": address})
            if mutisig_record is not None:
                db.get_collection("b_hc_multisig_address").remove({"address": address})
            data = {"address": address, "redeemScript": redeemScript, "addr_type":0}
            db.get_collection("b_hc_multisig_address").insert_one(data)
    elif chainId == "btm":
        result = btm_plugin.btm_create_multisig(addrs, amount)
        if result is not None:
            address = result["address"]
            redeemScript = result["redeemScript"]
            mutisig_record = db.get_collection("b_btm_multisig_address").find_one({"address": address})
            if mutisig_record is not None:
                db.get_collection("b_btm_multisig_address").remove({"address": address})
            data = {"address": address, "redeemScript": redeemScript, "addr_type":0}
            db.get_collection("b_btm_multisig_address").insert_one(data)
    elif chainId == "usdt":
        result = usdt_plugin.omni_create_multisig(addrs, amount)
        if result is not None:
            address = result["address"]
            redeemScript = result["redeemScript"]
            mutisig_record = db.get_collection("b_" + chainId + "_multisig_address").find_one({"address": address})
            if mutisig_record is not None:
                db.get_collection("b_" + chainId + "_multisig_address").remove({"address": address})
            data = {"address": address, "redeemScript": redeemScript, "addr_type": 0}
            db.get_collection("b_" + chainId + "_multisig_address").insert_one(data)
    else:
        return error_utils.invalid_chainid_type(chainId)

    return {
        'chainId': chainId,
        'address': address,
        'redeemScript': redeemScript
    }

@jsonrpc.method('Zchain.Address.validate(chainId=str, addr=str)')
def zchain_address_validate(chainId,addr):
    chainId = chainId.lower()
    logger.info("Zchain.Address.validate")
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(addr) != unicode:
        return error_utils.mismatched_parameter_type('addr', 'STRING')
    result = None
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_validate_address(addr)
    elif chainId == "hc":
        result = hc_plugin.hc_validate_address(addr)
    elif chainId == "usdt":
        result = usdt_plugin.omni_validate_address(addr)
    elif chainId == "btm":
        result = btm_plugin.btm_validate_address(addr)
        return {
            "chainId": chainId,
            "valid": result
        }
    elif chainId == "eth" or 'erc'in chainId:
        result = eth_utils.eth_validate_address(addr)
        return {
            "chainId": chainId,
            "valid": result
        }
    else:
        return error_utils.invalid_chainid_type(chainId)

    return {
        "chainId":chainId,
        "valid"  : result.get("isvalid")
    }

@DeprecatedFunction
@jsonrpc.method('Zchain.Multisig.Add(chainId=str, addrs=list, amount=int, addrType=int)')
def zchain_multisig_add(chainId, addrs, amount, addrType):
    logger.info('Zchain.Multisig.Add')
    chainId = chainId.lower()
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(addrs) != list:
        return error_utils.mismatched_parameter_type('addrs', 'ARRAY')
    if type(amount) != int:
        return error_utils.mismatched_parameter_type('amount', 'INTEGER')
    if type(addrType) != int:
        return error_utils.mismatched_parameter_type('addrType', 'INTEGER')

    address = ""
    if sim_btc_plugin.has_key(chainId):
        multisig_addr = sim_btc_plugin[chainId].sim_btc_add_multisig(addrs, amount)
        if multisig_addr is not None:
            addr_info = sim_btc_plugin[chainId].sim_btc_validate_address(multisig_addr)
            if addr_info == "":
                multisig_record = db.get_collection("b_"+chainId+"_multisig_address").find_one({"address": multisig_addr})
                if multisig_record is not None:
                    db.get_collection("b_"+chainId+"_multisig_address").remove({"address": multisig_addr})
                data = {"address": addr_info["address"], "redeemScript": addr_info["hex"], "addr_type": addrType}
                db.get_collection("b_"+chainId+"_multisig_address").insert_one(data)
                address = addr_info["address"]
    elif chainId == "hc":
        multisig_addr = hc_plugin.hc_add_multisig(addrs, amount)
        if multisig_addr is not None:
            addr_info = hc_plugin.hc_validate_address(multisig_addr)
            if addr_info is not None:
                multisig_record = db.get_collection("b_hc_multisig_address").find_one({"address": multisig_addr})
                if multisig_record is not None:
                    db.get_collection("b_hc_multisig_address").remove({"address": multisig_addr})
                data = {"address": addr_info["address"], "redeemScript": addr_info["hex"], "addr_type": addrType}
                db.get_collection("b_hc_multisig_address").insert_one(data)

    else:
        return error_utils.invalid_chainid_type(chainId)

    return {
        'chainId': chainId,
        'data': address
    }

@jsonrpc.method('Zchain.Transaction.GuardCall.History(chainId=str, account=str, blockNum=int, limit=int)')
def zchain_transaction_guardcall_history(chainId,account ,blockNum, limit):
    chainId = chainId.lower()
    logger.info('Zchain.Transaction.GuardCall.History')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(account) != unicode:
        return error_utils.mismatched_parameter_type('account', 'STRING')
    if type(blockNum) != int:
        return error_utils.mismatched_parameter_type('blockNum', 'INTEGER')
    if type(limit) != int:
        return error_utils.mismatched_parameter_type('limit', 'INTEGER')

    guardcallTrxs = db.b_guardcall_transaction.find({"chainId": chainId, "blockNum": {"$gte": blockNum}}, {"_id": 0}).sort(
        "blockNum", pymongo.DESCENDING)
    trxs = list(guardcallTrxs)
    if len(trxs) == 0:
        blockNum = 0
    else:
        blockNum = trxs[0]['blockNum']
    return {
        'chainId': chainId,
        'blockNum': blockNum,
        'data': trxs
    }

@jsonrpc.method('Zchain.Trans.getContractAddress(trxId=str)')
def zchain_trans_get_contract_address(trxId):
    logger.info('Zchain.Trans.getContractAddress')
    return eth_utils.get_contract_address(trxId)

#TODO, call btc_collect service
@jsonrpc.method('Zchain.Transaction.Withdraw.History(chainId=str, account=str, blockNum=int, limit=int)')
def zchain_transaction_withdraw_history(chainId,account ,blockNum, limit):
    chainId = chainId.lower()
    logger.info('Zchain.Transaction.Withdraw.History')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(account) != unicode:
        return error_utils.mismatched_parameter_type('account', 'STRING')
    if type(blockNum) != int:
        return error_utils.mismatched_parameter_type('blockNum', 'INTEGER')
    if type(limit) != int:
        return error_utils.mismatched_parameter_type('limit', 'INTEGER')

    withdrawTrxs = db.b_withdraw_transaction.find({"chainId": chainId, "blockNum": {"$gte": blockNum}}, {"_id": 0}).sort(
        "blockNum", pymongo.DESCENDING)
    trxs = list(withdrawTrxs)
    if len(trxs) == 0:
        blockNum = 0
    else:
        blockNum = trxs[0]['blockNum']
    return {
        'chainId': chainId,
        'blockNum': blockNum,
        'data': trxs
    }

#TODO, call btc_collect service
@jsonrpc.method('Zchain.Transaction.Deposit.History(chainId=str, account=str, blockNum=int, limit=int)')
def zchain_transaction_deposit_history(chainId,account ,blockNum, limit):
    chainId = chainId.lower()
    logger.info('Zchain.Transaction.Deposit.History')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(account) != unicode:
        return error_utils.mismatched_parameter_type('account', 'STRING')
    if type(blockNum) != int:
        return error_utils.mismatched_parameter_type('blockNum', 'INTEGER')
    if type(limit) != int:
        return error_utils.mismatched_parameter_type('limit', 'INTEGER')

    depositTrxs = db.b_deposit_transaction.find({"chainId": chainId, "blockNum": {"$gte": blockNum}}, {"_id": 0}).sort(
        "blockNum", pymongo.DESCENDING)
    trxs = list(depositTrxs)
    if len(trxs) == 0:
        blockNum = 0
    else:
        blockNum = trxs[0]['blockNum']

    return {
        'chainId': chainId,
        'blockNum': blockNum,
        'data': trxs
    }


@jsonrpc.method('Zchain.Configuration.Set(chainId=str, key=str, value=str)')
def zchain_configuration_set(chainId, key, value):
    chainId = chainId.lower()
    logger.info('Zchain.Configure')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if type(key) != unicode:
        return error_utils.mismatched_parameter_type('key', 'STRING')
    if type(value) != unicode:
        return error_utils.mismatched_parameter_type('value', 'STRING')

    data = {"chainId": chainId, "key": key, "value": value}
    result = True
    try:
        db.b_config.insert_one(data)
    except Exception as e:
        logger.error(str(e))
        result = False
    finally:
        return {
            "result": result
        }

@jsonrpc.method('Zchain.Plugin.QuerySymbol()')
def zchain_plugin_querysymbol():
    return App.config["SUPPORT_MIDWARE_PLUGIN_SYMBOL"]

bak_white_list_time = 0
bak_white_list_datas= []

@jsonrpc.method('Zchain.Plugin.QueryWhiteListSenatorId()')
def zchain_plugin_querywhitelistsenatorid():
    global  bak_white_list_time,bak_white_list_datas
    if time.time()-bak_white_list_time>60:
        bak_white_list_time=time.time()
        file = open(App.config["WHITE_LIST_FILE_PATH"],"r")

        data_strs= file.readlines()
        file.close()
        for one_line in data_strs:
            if len(one_line) ==0:
                continue
            if one_line[0]=="#" or one_line =="":
                continue
            datas = json.loads(one_line)
            break
        bak_white_list_datas = datas
    return bak_white_list_datas

# TODO, 备份私钥功能暂时注释，正式上线要加回
'''
@jsonrpc.method('Zchain.Address.Create(chainId=String)')
def zchain_address_create(chainId):
    chainId = chainId.lower()
    logger.info('Create_address coin: %s' % (chainId))
    if chainId == 'eth':
        address = eth_utils.eth_create_address()
    elif sim_btc_plugin.has_key(chainId):
        address = sim_btc_plugin[chainId].sim_btc_create_address()
    elif chainId == "hc":
        address = hc_plugin.hc_create_address()
    else:
        return error_utils.invalid_chainid_type(chainId)
    if address != "":
        if chainId == 'eth':
            pass
            # eth_utils.eth_backup()
        else:
            pass
            # btc_utils.btc_backup_wallet()
        data = db.b_chain_account.find_one({"chainId": chainId, "address": address})
        if data != None:
            return {'chainId': chainId, 'error': '创建地址失败'}
        d = {"chainId": chainId, "address": address, "name": "", "pubKey": "", "securedPrivateKey": "",
             "creatorUserId": "", "balance": {}, "memo": "", "createTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        db.b_chain_account.insert(d)
        return {'chainId': chainId, 'address': address}
    else:
        return {'chainId': chainId, 'error': '创建地址失败'}
'''



'''
@jsonrpc.method('Zchain.Withdraw.GetInfo(chainId=str)')
def zchain_withdraw_getinfo(chainId):
    """
    查询提现账户的信息
    :param chainId:
    :return:
    """
    chainId = chainId.lower()
    logger.info('Zchain.Withdraw.GetInfo')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')

    records = db.b_config.find_one({'key': 'withdrawaddress'}, {'_id': 0})
    address = ""
    if records == None:
        db.b_config.insert_one({"key": "withdrawaddress", "value": []})
        records = db.b_config.find_one({'key': 'withdrawaddress'}, {'_id': 0})
    for r in records["value"]:
        if r['chainId'] == chainId:
            address = r['address']

    if address == "":
        if chainId == "eth":
            address = eth_utils.eth_create_address()
            # eth_utils.eth_backup()
            records["value"].append({"chainId": "eth", "address": address})
        elif sim_btc_plugin.has_key(chainId):
            address = sim_btc_plugin[chainId].sim_btc_create_withdraw_address()
            sim_btc_plugin.sim_btc_backup_wallet()
            records["value"].append({"chainId": chainId, "address": address})
        elif chainId == "hc":
            address = hc_plugin.hc_create_withdraw_address()
            hc_plugin.hc_backup_wallet()
            records["value"].append({"chainId": chainId, "address": address})
        elif chainId == "etp":
            address = etp_utils.etp_create_withdraw_address()
            records["value"].append({"chainId": "etp", "address": address})
    db.b_config.update({"key": "withdrawaddress"}, {"$set": {"value": records["value"]}})
    balance = 0.0
    if chainId == "eth":
        balance = eth_utils.eth_get_base_balance(address)
    elif sim_btc_plugin.has_key(chainId):
        balance = sim_btc_plugin.sim_btc_get_withdraw_balance()
    elif chainId == "hc":
         balance = hc_plugin.hc_get_withdraw_balance()
    elif chainId == "etp":
        balance = etp_utils.etp_get_addr_balance(address)
    else:
        return error_utils.invalid_chainid_type(chainId)

    return {
        'chainId': chainId,
        'address': address,
        'balance': balance
    }
'''

@jsonrpc.method('Zchain.Address.GetBalance(chainId=str, addr=str)')
def zchain_address_get_balance(chainId, addr):
    logger.info('Zchain.Address.GetBalance')
    ercchainId = chainId
    chainId = chainId.lower()
    balance = "0"
    if chainId == 'eth':
        balance = eth_utils.eth_get_address_balance(addr, chainId)
    elif 'erc' in chainId:
       #print ercchainId
       asser = None
       if erc_chainId_map.has_key(ercchainId):
           asset = erc_chainId_map[ercchainId]
       if asset == None:
           return error_utils.invalid_chainid_type(chainId)

       temp = {
           'precison':asset['precison'],
           'addr':addr,
           'contract_addr':asset['address']
       }
       balance = eth_utils.eth_get_address_balance(temp,chainId)
    elif chainId == "hc":
        balance = hc_plugin.hc_get_balance(addr)
    elif chainId in sim_btc_utils_all:
        balance = sim_btc_plugin[chainId].sim_btc_get_balance(addr)
    elif chainId =="usdt":
        balance = usdt_plugin.omni_get_balance(addr)
    elif chainId == "btm":
        balance = btm_plugin.btm_get_balance(addr)
    else:
        return error_utils.invalid_chainid_type(chainId)

    return {
        'chainId': chainId,
        'address': addr,
        'balance': balance
    }
@jsonrpc.method('Zchain.Transaction.All.History( param=list )')
def zchain_transaction_all_history(param):
    ret = []
    for item in param:
        try:
            ret_list = []
            ret_temp = {}
            chainId = item.get('chainId')
            account = item.get('account')
            blockNum = item.get('blockNum')
            limit = item.get('limit')
            if chainId == None:
               continue
            if account == None:
                continue
            if blockNum == None:
                continue
            if limit == None:
                continue
            chainIdLower = chainId.lower()
            if type(chainIdLower) != unicode:
                continue
            ret_temp['chainId'] = chainId
            current_block_info = {
                "eth": "syncblocknum",
                "btc": "btcsyncblocknum",
                "ltc": "ltcsyncblocknum",
                "hc": "hcsyncblocknum",
                "usdt": "usdtsyncblocknum",
                "bch":"bchsyncblocknum"
            }
            if type(chainIdLower) != unicode:
                return error_utils.mismatched_parameter_type('chainId', 'STRING')
            if type(account) != unicode:
                return error_utils.mismatched_parameter_type('account', 'STRING')
            if type(blockNum) != int:
                return error_utils.mismatched_parameter_type('blockNum', 'INTEGER')
            if type(limit) != int:
                return error_utils.mismatched_parameter_type('limit', 'INTEGER')
            current_block_num = 0
            dep_num = 1000
            if chainIdLower == "eth" or "erc" in chainIdLower:
                current_block_num = int(db.b_config.find_one({"key": current_block_info["eth"]})["value"])
                dep_num = 10000
                if blockNum == 0:
                    blockNum = 6500000
            elif current_block_info.has_key(chainIdLower):
                current_block_num = int(db.b_config.find_one({"key": current_block_info[chainIdLower]})["value"])
            trxs = []
            deposit_trxs = []
            withdraw_trxs = []
            guardcall_trxs = []
            deposit_blocknum = 0
            withdraw_blocknum = 0
            guardcall_blocknum = 0
            withdraw_count = db.b_withdraw_transaction.find_one({"chainId": chainIdLower,"blockNum":{"$gt":blockNum}})
            deposit_count =  db.b_deposit_transaction.find_one({"chainId": chainIdLower,"blockNum":{"$gt":blockNum}})
            guardcall_count = None
            if ('eth' == chainIdLower) or ('erc' in chainIdLower):
                guardcall_count = db.b_guardcall_transaction.find_one(
                    {"chainId": chainIdLower,
                     "blockNum": {"$gt": blockNum}})
            if deposit_count ==None and withdraw_count ==None and guardcall_count==None:
                ret_temp['blockNum'] = max(deposit_blocknum, withdraw_blocknum, guardcall_blocknum, blockNum)
                ret_temp['data'] = ret_list
                ret.append(ret_temp)
                continue
            for i in range(((current_block_num - blockNum) / dep_num) + 1):
                depositTrxs = db.b_deposit_transaction.find(
					{"chainId": chainIdLower, "blockNum": {"$gt": blockNum + i * dep_num, "$lte": blockNum + (i + 1) * dep_num}},
                    {"_id": 0}).sort(
                    "blockNum", pymongo.DESCENDING)
                withdrawTrxs = db.b_withdraw_transaction.find(
					{"chainId": chainIdLower, "blockNum": {"$gt": blockNum + i * dep_num, "$lte": blockNum + (i + 1) * dep_num}},
                    {"_id": 0}).sort(
                    "blockNum", pymongo.DESCENDING)
                deposit_trxs.extend(list(depositTrxs))
                if len(deposit_trxs)>0:
                    deposit_blocknum = deposit_trxs[0]['blockNum']
                withdraw_trxs.extend(list(withdrawTrxs))
                if len(withdraw_trxs)>0:
                    withdraw_blocknum = withdraw_trxs[0]['blockNum']
                trxs.extend(deposit_trxs)
                trxs.extend(withdraw_trxs)
                if ('eth' == chainIdLower) or ('erc' in chainIdLower):
                    guardcallTrxs = db.b_guardcall_transaction.find(
                        {"chainId": chainIdLower, "blockNum": {"$gt": blockNum + i * dep_num, "$lte": blockNum + (i + 1) * dep_num}}, {"_id": 0}).sort(
                        "blockNum", pymongo.DESCENDING)
                    guardcall_trxs.extend(list(guardcallTrxs))
                    if len(guardcall_trxs)>0:
                        guardcall_blocknum = guardcall_trxs[0]['blockNum']
                    trxs.extend(guardcall_trxs)
                ret_temp['blockNum'] = max(deposit_blocknum, withdraw_blocknum, guardcall_blocknum,blockNum)
                if len(trxs) > 0:
                    break
            ret_list.extend(trxs)
            ret_temp['data'] = ret_list
            ret.append(ret_temp)
        except Exception, ex:
            print ex
            continue
    return ret