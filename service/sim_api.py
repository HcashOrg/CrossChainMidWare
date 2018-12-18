# -*- coding: utf-8 -*-

from service import jsonrpc
from config import logger,App
from utils import eth_utils
from utils import etp_utils
from service import db
from service import sim_btc_plugin,sim_btc_utils_all
from service import hc_plugin
from utils import error_utils
import pymongo
from datetime import datetime
from config.erc_conf import erc_chainId_map
import json
import leveldb
import time
import hashlib
last_clean_broadcast_cache_time = time.time()


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
        return error_utils.invalid_chainid_type()

    if signed_message == "":
        return error_utils.error_response("Cannot sign message.")

    return {
        'chainId': chainId,
        'data': signed_message
    }


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
        return error_utils.invalid_chainid_type()

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

    if asset == None:
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
    elif chainId.lower() == "eth":
        result = eth_utils.eth_send_raw_transaction(trx)
    elif 'erc' in chainId.lower():
        result = eth_utils.eth_send_raw_transaction(trx)
    else:
        return error_utils.invalid_chainid_type()

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


@jsonrpc.method('Zchain.Addr.importAddr(chainId=str, addr=str)')
def zchain_addr_importaddr(chainId, addr):
    logger.info('Zchain.Addr.importAddr')
    if type(chainId) != unicode:
        return error_utils.mismatched_parameter_type('chainId', 'STRING')
    if sim_btc_plugin.has_key(chainId):
        sim_btc_plugin[chainId].sim_btc_import_addr(addr)
    elif chainId == "hc":
        hc_plugin.hc_import_addr(addr)
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
                db.b_eths_address.insert({'chainId': chainId, 'address': handle_addr, 'isContractAddress': True})
            else:
                db.b_eths_address.insert({'chainId': chainId, 'address': addr, 'isContractAddress': False})
            eth_utils.add_guard_address(addr)
    else:
        return error_utils.invalid_chainid_type()
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
        return error_utils.invalid_chainid_type()
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
    else:
        return error_utils.invalid_chainid_type()
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
        return error_utils.invalid_chainid_type()
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
        return error_utils.invalid_chainid_type()
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
    else:
        return error_utils.invalid_chainid_type()
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
        result = sim_btc_plugin[chainId].sim_btc_create_transaction(from_addr,dest_info)
    elif chainId == "hc":
        result = hc_plugin.hc_create_transaction(from_addr, dest_info)
    else:
        return error_utils.invalid_chainid_type()

    if result == {}:
        return error_utils.error_response("Cannot create transaction.")

    return {
        'chainId': chainId,
        'data': result
    }


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
    else:
        return error_utils.invalid_chainid_type()

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
    else:
        return error_utils.invalid_chainid_type()

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
    if trxid=="123456789":
        data ={ "vout" : [ { "scriptPubKey" : { "reqSigs" : 1, "hex" : "76a9149bac437aa393bbf35585c6294efc0fda284547e088ac", "addresses" : [ "HsRqTjo3QmmmuhojBeb86YSnQDn6jJdhge3" ], "asm" : "OP_DUP OP_HASH160 9bac437aa393bbf35585c6294efc0fda284547e0 OP_EQUALVERIFY OP_CHECKSIG", "type" : "pubkeyhash" }, "version" : 0, "value" : 0.0069778, "n" : 0 }, { "scriptPubKey" : { "reqSigs" : 1, "hex" : "a914347f35722b575a244798fb1ab0b03ea4584ca81487", "addresses" : [ "HcNvbjZ8fsRU1tWroHvUsbq8Xjaa8ZY56xr" ], "asm" : "OP_HASH160 347f35722b575a244798fb1ab0b03ea4584ca814 OP_EQUAL", "type" : "scripthash" }, "version" : 0, "value" : 105.29, "n" : 1 } ], "vin" : [ { "scriptSig" : { "hex" : "47304402200d4b97cf07d485c2e4e2863c788933b7abfcdee9409b699c336d59114d01b97002207c97e5f05a9c5651d6bc915156d237efb8f40def1d407a164d2c548ea7b64699012103afba90812c9c8f37b466ba0b866e6a0f3a847cc1c7474e21703da284f20135d9", "asm" : "304402200d4b97cf07d485c2e4e2863c788933b7abfcdee9409b699c336d59114d01b97002207c97e5f05a9c5651d6bc915156d237efb8f40def1d407a164d2c548ea7b6469901 03afba90812c9c8f37b466ba0b866e6a0f3a847cc1c7474e21703da284f20135d9" }, "vout" : 0, "sequence" : "4294967295", "blockindex" : 2, "tree" : 0, "txid" : "95ff3166e2cd5f65e21106bc5196bd9e4dc5df4e3e3904542bbd638694806432", "blockheight" : 60324, "amountin" : 0.0069778 }, { "scriptSig" : { "hex" : "473044022002c266733e3adc78eaa260c2eff22c75dcc4a7ceb4a89a5fef41cf3c0aedb034022076c2f2998c4576d8a1208beab27648dfc5fbfd8ed2bf98ca8a569912e901d5e9012103afba90812c9c8f37b466ba0b866e6a0f3a847cc1c7474e21703da284f20135d9", "asm" : "3044022002c266733e3adc78eaa260c2eff22c75dcc4a7ceb4a89a5fef41cf3c0aedb034022076c2f2998c4576d8a1208beab27648dfc5fbfd8ed2bf98ca8a569912e901d5e901 03afba90812c9c8f37b466ba0b866e6a0f3a847cc1c7474e21703da284f20135d9" }, "vout" : 1,  "blockindex" : 1, "tree" : 0, "txid" : "e7d6b55683903c87959fca43a9e7b4c2e177c1b61f9e2840cd1400ba049e3236", "blockheight" : 60477, "amountin" : 105.3 } ], "expiry" : 0, "version" : 1, "locktime" : 0, "txid" : "2abc967c3d85d5933eba69d4b3dddb3fd4319d22d5e95c1b4425ccb63cb7893a" }
        return {
            'chainId': chainId,
            'data': data
        }
    if sim_btc_plugin.has_key(chainId):
        result = sim_btc_plugin[chainId].sim_btc_get_transaction(trxid)
        if "vout" in result:
            is_cache = True
    elif chainId == "hc":
        result = hc_plugin.hc_get_transaction(trxid)
        if "vout" in result:
            is_cache = True

    elif chainId == "eth" or "erc" in chainId:
        source,respit = eth_utils.get_transaction_data(trxid)
        so_re_dic = {'source_trx':source,'respit_trx':respit}
        if "input" in source:
            is_cache = True
        if source != None and respit != None:
            result = so_re_dic
    else:
        return error_utils.invalid_chainid_type()

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
        elif chainId == "hc":
            result = hc_plugin.hc_get_transaction(one_txid)
            if "vout" in result:
                is_cache = True

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
    return {
        'chainId': chainId,
        'data': res_data
    }

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
        return error_utils.invalid_chainid_type()

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
        return error_utils.invalid_chainid_type()
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
    else:
        return error_utils.invalid_chainid_type()

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
    elif chainId == "eth" or 'erc'in chainId:
        result = eth_utils.eth_validate_address(addr)
        return {
            "chainId": chainId,
            "valid": result
        }
    else:
        return error_utils.invalid_chainid_type()

    return {
        "chainId":chainId,
        "valid"  : result.get("isvalid")
    }

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
        return error_utils.invalid_chainid_type()

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

@jsonrpc.method('Zchain.Plugin.QueryWhiteListSenatorId()')
def zchain_plugin_querywhitelistsenatorid():
    return App.config["WHITE_LIST_SENATOR_ID"]

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
    查询提现账户的信�?
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
    else:
        return error_utils.invalid_chainid_type(chainId)

    return {
        'chainId': chainId,
        'address': addr,
        'balance': balance
    }
