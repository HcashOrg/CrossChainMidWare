# -*- coding: utf-8 -*-

# from __future__ import print_function
import requests
import json
from config import config
import sys
import shutil
import os
from math import pow,floor
import time
from service import logger
import traceback

temp_config = config["development"]

def eth_request(method, args):
    url = "http://%s:%s" % (temp_config.ETH_URL, temp_config.ETH_PORT)
    request_template = '''{"id":"1","method":"%s","params":%s}'''
    args_str = json.dumps(args)
    data_to_send = request_template % (method, args_str)
    #print data_to_send

    payload = ""
    headers = {
        'Content-Type': "application/json"
    }
    response = requests.request("POST", url, data=data_to_send, headers=headers)
    test = response.text
    #print test
    response.close()
    return response.text


def eth_backup():
    # 只对Linux平台进行备份
    if sys.platform != 'linux2':
        return True
    backup_path = '/var/backup_keystore/'
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
    ret = eth_request("admin_datadir", [])
    json_data = json.loads(ret)
    if json_data.get("result") is None:
        return False
    source_path = json_data["result"]

    shutil.copytree(source_path, backup_path)
    return True


def eth_create_address():
    address = ''
    data = {}
    # 写入数据库待做
    result = eth_request("personal_newAccount", [temp_config.ETH_SECRET_KEY])
    json_result = json.loads(result)
    if json_result.has_key("result"):
        address = json_result["result"]
        return address
    return address


def eth_get_base_balance(address):
    result = eth_request("eth_getBalance", [address, "latest"])
    print result
    json_result = json.loads(result)
    if json_result.get("result") is None:
        return 0
    amount = long(json_result["result"], 16)
    return float(amount / pow(10, 18))
    # return


def eth_get_no_precision_balance(address,last_block_num):
    result = eth_request("eth_getBalance", [address,  "latest"])
    print result
    json_result = json.loads(result)
    if json_result.get("result") is None:
        return 0
    amount = long(json_result["result"], 16)
    return amount
    # return


def get_account_list_from_wallet():
    addressList = []
    result = eth_request("personal_listAccounts", [])
    print type(result)
    print result
    json_result = json.loads(result)
    if json_result.has_key("result"):
        addressList = json_result["result"]
        return addressList
    return addressList


def get_transaction_data(trx_id):
    # print "\ntrx_id:",trx_id
    ret = eth_request("Service.GetTrx", [str(trx_id)])
    # print ret
    json_data = json.loads(ret)
    if json_data.get("result") is None:
        return None, None
    resp_data = json_data.get("result")
    ret = eth_request("Service.GetTrxReceipt", [str(trx_id)])
    json_data = json.loads(ret)
    if json_data.get("result") is None:
        return None, None
    receipt_data = json_data.get("result")
    return resp_data, receipt_data


#创建转账交易 默认GasPrice 5Gwei
def eth_send_transaction(from_address,to_address,value,gasPrice="0x1dcd6500",gas="0x76c0"):
    ret = eth_request("personal_unlockAccount",[from_address,temp_config.ETH_SECRET_KEY,1000])
    json_data = json.loads(ret)
    print ret
    if json_data.get("result") is None:
        return ''
    elif not json_data["result"]:
        return ''
    ret = eth_request("eth_sendTransaction", [{"from": from_address, "to": to_address,
                                               "value": hex(long(floor(float(float(value) * pow(10,18))))).replace('L', ''),
                                               "gas": gas, "gasPrice": gasPrice}])
    json_data = json.loads(ret)
    print ret
    if json_data.get("result") is None:
        return ""
    else:
        return json_data.get("result")
def get_contract_address(trxId):
    knowList = {"0x4abb8d65b85dc8f232716b878cae90a7ef38cab4c65073791c3f2c60ebff00d4":"0x2616cd11ef25abab62db430b6122d4d0f66f623d","0x581c14c049160ae2274c26a9770a449d592043f5876b9d20981eb21a479b38f7":"0xcf7f3d46977a8a00a52ed5671ff2a1c445092222"
                ,"0x5f9b3b7358a66e03e6255c00dc008d92ac3e6f1c22823640e6f17b3b02fe2559":"0x23279ce34aab30739eff2e099496d3194d691b1a","0x9e7f46c82bcfa32cbb59100e7f4f2a477521ce16152b3834276da3a1edc8c67f":"0x25eb43c56527e0b75083f563a3d61533001a1164",
                "0x2c41d83a3a44406c3778efd7a8b892393a09c50e12f855729779309ed2dfd553":"0x7352750a8ac7827dc2d40f4562c59b12e2519f97","0xcff7eee53ce78c220486f4309f65919451e408eeb3979e24d40b0d423b695af8":"0xd4307bfa82073e4812202c2978129c10358fe3ec",
                "0xd6aba1c716e5d0636ca22e9cb0199f3b8d047398cc0617a768a1f96e0f8ddf53":"0x3f44384c7e85481ab3b6557e059766ee26930be3","0xd0c19bc3d9d511518b129375ec1c96491de8bed56f43c474ce77bcea4c49f99c":"0x8e4bfd29615c0e58dacc6f6e469690f7a93c7d9c",
                "0x9c007041f6e970a99f356d0f0bfa7bc85b11594be574e54a1f27724d0ee7e728":"0x9df7948e0819265321b95dca513b545c630bb13d","0x274973046a09d18ecaff60446b3e292e4c639bcf04efdff04a654b8757d6131f":"0x5e0dfb923ced1096cee00a02d2640720c8dd3328",
                "0x84c25bb537914339906773602e3673243d5af14103e1cd20927e20cb093319de":"0x5c95397c2d7ca64187579034e423359ee50a803d","0xda0552641a08ac49ee36160a07fbc280401ff758b3876ef10ef8e35e8eb05110":"0x5421e62b1493174299b8064d941623e7613fc33f",
                "0xbbe510ff679f1dc3a93e7c9f60b0857b59a477a146ea5bde567e3dd7cfc17484":"0x9ac27c7333ccf0a1e4ad19973e6374fef86dec44","0xa865dae23ed2d1e15523ffabfea53227f56914223692e5197032d1e7d0b229d2":"0x12d7db49ece3551befcc85cfc99f77a05aeb8d3a",
                "0xb7c7f20d78521634d7f842925b2f7a879b355f1aba0fdda41fb33626b57f4abe": "0x843eb9777204fcdf47c74faba8dad4cde70cb500",
                "0x544a997d78cba0e1afba38f842c95ca5c3601b76329277430fa09897e22c8686": "0x99309914340a313216d80211fa89a9aec203afd8",
                "0x5df9b1aa988af4bed7527833d2be5247ff2536acd6a21d24332c3cd94935b10e": "0x897b551a4cc4a489347a1c5da5f5b98cfcf577e3",
                "0x2fec9b57fcb6357d720492743d697eafd1044a03dc6f9f1412ca4968ded091c9": "0x53568bdb1eddc1f0f2c876f126e662607481b264",
                "0x7acbff3b696b4f82891ef32588256f9192a0ade9c0490188cba4c64db4464fb1": "0xd680d60937ca87c4f0ed859292fd2c1b1291ba14",
                "0x7805ae3a6a76f1c2a2ac003aff72af89feef4203916e725f8ec6616230ed3ea3": "0x4f693df0a0089963f043b2e651e6549edb6a1d74",
                "0x578e8d9f20d96ed90a916d6c06c5e249802c55746cd39a624e83e6483047d0dc": "0xf37abbf11970db291009dd3d31a7696b4d8a77e5",
                "0x65658b217456fd31f7cfce933a6b6e38915f14e347ebde1dc0a8c8a98e0efb8b": "0x855d1a6f2633f112e02ecd3d899fda00066581f1",
                "0x4abb8d65b85dc8f232716b878cae90a7ef38cab4c65073791c3f2c60ebff00d4": "0x2616cd11ef25abab62db430b6122d4d0f66f623d",
                "0x581c14c049160ae2274c26a9770a449d592043f5876b9d20981eb21a479b38f7": "0xcf7f3d46977a8a00a52ed5671ff2a1c445092222",
                "0x23b427c07ebd98e53f35624f065a8f99152c65389e599f510dfdda58bd27a227": "0xe978b70c5467f444e1e7f6969e251dada866214a",
                "0x37380d5a978ef4c3f5e0e7cd7bce3df7c56f5a1ebb39237fc4d7c30906758a53": "0xa9f09df3c1949b2dcb72c18cbc488b4092c87e9b",
                "0xa9d58a5167759aa96965f48db3e5b8898a82d8907ea8df3c70048b1d3f5facb5": "0xcacb88b72fb177b00b4dbd1fb802d9ed05041e44",
                "0xda4f5af941f949d64d694bc49353df7ce55885d86f21a36a6fd0e01f573333a9": "0x03c37ce111fc1a80a305bb0b03edbd38d2ab6160",
                "0x18f07d2b7281803fb541a349a11415ab22654cd3626a6fbf0a0f00e9d606f982": "0x3f90b5ee60ef11e11d1a3e8ae2cae9763275f8d7",
                "0x427466b0d194e9b6988141759f06094d5858015df3d58a145886e40e8528899e": "0x54578fe13a61e8a758b34120aca9f8eb9472b440",
                "0xcc536c53c98d2539fd4060fa7ccaadc4c977e23e885d7b78aae81851ba415b2d": "0x86e2f060696ea0e7ce08f6cb07ec7f264e88542c",
                "0xc442dee2035b9561c93c859728eec3770af36d535ac72035f2747dde78d2ddc0": "0x445864a4a949b3ae06234070ce13b20bb898fd7c",
                "0x085d9baa755c9e6d72288a79a03e371c56b8463f0293926002cf893884862c86": "0x9eca111b37fdc9563562601d0667010cc0703add",
                "0x9f99d09ffa8dfc1a5e4949999208af1eae5d5b0ab16547f209d40405900275b0": "0xd1b7fb479db5946c8d1ce753e9824b9ad994f544",
                "0x7ce19551d6e02d869972fcb6b7686d0d5bc9ea56eb16113e5aa631dc959ef354": "0xcc194267f6e1a34b2f6edc50cb0a0a3fdd536b19",
                "0xd6c58a65a4db59f0e16df88c4e94e8fbfc33a3c27a4ef270d50c7d75af1e1167": "0x8857974df7386132317f3274d33484ae455bc593",
                "0x42a00cf71bee8c2e9eb5d6dac3d36d5abfa75c45fecc0ee4303fc4ca1a7e80cf": "0x5cdd963f558d8e1db5f6c65254c0ef8c0672759b",
                "0x21036ce6847a01d6e3cc461ef3755a514961c65a5c348ecb157374bc272a8cb7": "0x23e8f3f4383986d064fe5b5ea61a825c8d64cc13",
                "0x3cb9a9cf5538d6363073dce6db58c412c04e0e31fafaf3768d41089129acde6b": "0xad0482ce55623b432420baf026c7cf7c12a4413c",
                "0x4d51a999e48b45794aa09f0b2ca30023145647425d6c3ba03dda865e2871eb06": "0xe815e4f90ba7ac7bdab34b55584be32d8f015f44"}
    if knowList.has_key(trxId):
        return knowList[trxId]
    ret = eth_request("Service.GetTrxReceipt", [trxId])
    if json.loads(ret).get("result") != None:
        receipt = json.loads(ret).get("result")
        return receipt["contractAddress"]
    else:
        return ''
def checkHex(ch):
    if ch >='0'and ch<='9':
        return True
    if ch >='A'and ch<='F':
        return True
    if ch >='a'and ch<='f':
        return True
    return False
def eth_validate_address(addr):
    if len(addr) != 42:
        return False
    ret = True
    i = 0
    for item in addr:
        if i == 0:
            if item != '0':
                ret = False
                break
        if i == 1:
            if item != 'x':
                ret = False
                break
        if i > 1:
            if checkHex(item) == False:
                ret = False
                break
        i = i+1
    return ret
def TurnAmountFromEth(source,precision):
    ret = ''
    precision = int(precision)
    if len(source) <= int(precision):
        ret += '0.'
        temp_precision = '0' * (precision - len(source))
        ret += temp_precision
        amount = source.rstrip('0')
        if amount == '':
            amount = source
        ret += amount
    else:
        ret += source[0: (len(source) - precision)]
        amountFloat = source[len(source) - precision:]
        amount = amountFloat.rstrip('0')
        if amount != '':
            ret += '.'
        ret += amount
    return ret
def eth_get_address_balance(address,chainId):
    if chainId == "eth":
        real_precision = 18
        ret = eth_request("Service.GetNormalBalance", [address])
    elif 'erc' in chainId:
        contract_addr = address['contract_addr']
        addr = address['addr']
        real_precision = address['precison']
        ret = eth_request("Service.GetErc20Balance", [[contract_addr,addr]])
        #print ret
    json_data = json.loads(ret)
    if json_data.get("result") is None:
        return '0'
    else:
        return TurnAmountFromEth(str(int(json_data.get("result"), 16)),real_precision)
        #return str(float(int(json_data.get("result"), 16)) / pow(10, int(real_precision)))


def eth_call(call_data,blockheight):


    ret = eth_request("Service.EthCall",[[call_data,blockheight]])

    json_data = json.loads(ret)

    return json_data.get("result")
        # return str(float(int(json_data.get("result"), 16)) / pow(10, int(real_precision)))


def eth_get_trx_count(address,indexFormat):
    ret = eth_request("Service.GetTransactionCount",[[address,indexFormat]])
    json_data = json.loads(ret)
    if json_data.get("result") is None:
        return {}
    else:
        return json_data.get("result")

def add_guard_address(addr):
    if "erc" in addr:
        pos = addr.find("erc")
        handle_addr = addr[0:pos]
        eth_request("Service.AddNormalAddress",[handle_addr])
        eth_request("Service.AddErc20Address",[handle_addr])
    else:
        eth_request("Service.AddNormalAddress", [addr])
def eth_send_raw_transaction(param):
    ret = eth_request("Service.BroadcastRawTransaction",[param])
    json_data = json.loads(ret)
    print ret
    if json_data.get("result") is None:
        return ''
    else:
        return json_data.get("result")
def eth_verify_signed_message(addr, message, signature):
    ret = eth_request("Service.Personal_ecRecover",[[message,signature]])
    json_data = json.loads(ret)
    if json_data.get("result") != None:
        return json_data['result'].upper() == addr.upper()

    else:
        return False
def get_latest_block_num():
    ret = eth_request("eth_blockNumber",[])
    json_data = json.loads(ret)
    return int(json_data["result"],16)

def eth_collect_money(cash_sweep_account, accountList, safeBlock):
    try:
        result_data = {}
        result_data["errdata"] = []
        result_data["data"] = []
        print accountList
        last_block_num = get_latest_block_num() - int(safeBlock)
        # 存储创建成功的交易单号
        for account in accountList:
            amount = eth_get_no_precision_balance(account,last_block_num)

            print (float(amount) / pow(10, 18))
            print float(float(amount) / pow(10, 18)) > float(temp_config.ETH_Minimum)
            if float(float(amount) / pow(10, 18)) > float(temp_config.ETH_Minimum):
                print hex(long((amount - pow(10, 15)))).replace('L', '')
                # 转账给目标账户
                result = eth_request("personal_unlockAccount", [account, temp_config.ETH_SECRET_KEY, 10000])
                if json.loads(result).get("result") is None:
                    result_data["errdata"].append(
                        {"from_addr": account, "to_addr": cash_sweep_account, "amount": float(amount) / pow(10, 18),
                         "error_reason": u"账户解锁失败"})
                    # 写入归账失败的列表
                    continue

                ret = eth_request("eth_sendTransaction",[{"from": account, "to": cash_sweep_account,
                                                          "value": hex(long((amount - pow(10,15)))).replace('L',''),
                                                          "gas": "0x76c0", "gasPrice": "0x1dcd6500"}])
                if json.loads(result).get("result") is None:
                    result_data["errdata"].append(
                        {"from_addr": account, "to_addr": cash_sweep_account, "amount": float(amount) / pow(10, 18),
                         "error_reason": u"账户创建交易失败"})
                    # 写入归账失败的列表
                    continue
                else:
                    result_data["data"].append(
                        {"from_addr": account, "to_addr": cash_sweep_account, "amount": float(amount) / pow(10, 18),
                         "trx_id": json.loads(ret).get("result")})
                    # 获取交易详情按笔计入details
                    # 写入归账成功返回
        return result_data, None
    except Exception, ex:
        logger.info(traceback.format_exc())
        return None, ex.message


def eth_get_collect_money(accountList):
    # 从钱包获取归账地址列表
    result_data = dict()
    result_data["details"] = []

    total_amount = 0.0
    for account in accountList:
        amount = eth_get_base_balance(account)
        one_data = {}
        one_data["address"] = account
        one_data["amount"] = float(amount) / pow(10, 18)
        result_data["details"].append(one_data)
        total_amount += float(amount) / pow(10, 18)

    result_data["total_amount"] = total_amount
    return result_data

def eth_get_block_height():
    ret = eth_request("Service.GetBlockHeight",[])
    json_data = json.loads(ret)
    if json_data.get("result") != None:
        return int(json_data['result'])

    else:
        return 0

def eth_get_trx_history_by_address(addr,startblock,endblock):
    ret = eth_request("Service.GetTrxHistoryByAddress",[[addr,startblock,endblock]])
    json_data = json.loads(ret)
    if json_data.get("result") != None:
        return json_data['result']

    else:
        return []


def eth_get_trx(trxid):
    ret = eth_request("Service.GetTrx",[trxid])
    json_data = json.loads(ret)
    if json_data.get("result") != None:
        return json_data['result']

    else:
        return {}


if __name__ == '__main__':
    add_guard_address("0x66c69ce0515edbd2ed7f299fb05a25065c3608d7erc")
    # get_account_list_from_wallet()
    # eth_create_address()
    # get_account_list_from_db()
    # eth_collect_money(2,"0x085aa94b764316d5e608335d13d926c6c6911e56")

