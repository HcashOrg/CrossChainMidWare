db = db.getSiblingDB('admin')
if (db.auth("dbAdmin", "admin12#$%") != 1) {
    db.createUser(
        {
            user: "dbAdmin",
            pwd: "admin12#$%",
            roles: [{role: "root", db: "admin"}]
        }
    )
    db.auth("dbAdmin", "admin12#$%")
    db = db.getSiblingDB('chaindb')
    db.createUser(
        {
            user: "chaindb_user",
            pwd: "yqr.1010",
            roles: [{role: "readWrite", db: "chaindb"}]
        }
    )
    db.auth("chaindb_user", "yqr.1010")

    db.createCollection("s_user");
    db.createCollection("b_chain_info");
    db.createCollection("b_block");
    db.createCollection("b_raw_transaction");
    db.createCollection("b_raw_transaction_input");
    db.createCollection("b_raw_transaction_output");
    db.createCollection("b_chain_account");
    db.createCollection("b_btc_unspent");
    db.createCollection("b_btc_multisig_address");
    db.createCollection("b_deposit_transaction");
    db.createCollection("b_withdraw_transaction");
    db.createCollection("b_exchange_contracts");
    db.createCollection("b_fee_providers");
    db.createCollection("b_balance_unspent");
    db.createCollection("b_balance_spent");
    db.createCollection("b_eths_address");
    db.createCollection("b_guardcall_transaction");
    db.createCollection("b_erc_address");
    db.createCollection("b_verify_cache");
    db.createCollection("b_query_trans_cache");
    db.createCollection("b_broadcast_trans_cache");
    db.createCollection("b_usdt_multisig_address");
    db.createCollection("b_btm_multisig_address");
    db.b_eths_address.ensureIndex({"chainId": 1, "address": 1}, {"unique": true});
    db.b_chain_account.ensureIndex({"chainId": 1, "address": 1}, {"unique": true});
    db.b_balance_unspent.ensureIndex({"chainId": 1, "address": 2});
    db.b_balance_spent.ensureIndex({"chainId": 1, "address": 2});
    db.s_user.ensureIndex({'email': 1}, {"unique": true});
    db.s_user.ensureIndex({'username': 1}, {"unique": true});
    db.b_block.ensureIndex({'chainId': 1});
    db.b_block.ensureIndex({'blockHash': 1});
    db.b_block.ensureIndex({'blockNumber':1});
    db.b_block.ensureIndex({'blockNumber':1, "chainId": 1});
    db.b_raw_transaction.ensureIndex({'chainId': 1});
    db.b_raw_transaction.ensureIndex({'trxId': 1});
    db.b_raw_transaction_input.ensureIndex({'rawTransactionid': 1});
    db.b_raw_transaction_input.ensureIndex({'address': 1});
    db.b_raw_transaction_output.ensureIndex({'rawTransactionid': 1});
    db.b_raw_transaction_output.ensureIndex({'address': 1});
    db.b_chain_account.ensureIndex({'name': 1});
    db.b_chain_account.ensureIndex({'address': 1});
    db.b_chain_account.ensureIndex({'chainId': 1});
    db.b_chain_account.ensureIndex({'creatorUserId': 1});
    db.b_chain_account.ensureIndex({'chainId': 1, 'address': 1}, {'unique': true});
    db.b_deposit_transaction.ensureIndex({'chainId': 1});
    db.b_deposit_transaction.ensureIndex({'txid':1})
    db.b_deposit_transaction.ensureIndex({'fromAddress': 1});
    db.b_deposit_transaction.ensureIndex({"chainId": 1,'blockNum':-1});
    db.b_withdraw_transaction.ensureIndex({"chainId": 1,'blockNum':-1});
    db.b_guardcall_transaction.ensureIndex({"chainId": 1,'blockNum':-1});
    db.b_withdraw_transaction.ensureIndex({'chainId': 1});
    db.b_withdraw_transaction.ensureIndex({'toAddress': 1});

    db.b_config.ensureIndex({'key': 1}, {'unique': true});
    db.b_verify_cache.ensureIndex({'chainId':1,"addr":2,"message":3,"signature":4});
    db.b_query_trans_cache.ensureIndex({'chainId':1,'trxid':2})
    db.b_broadcast_trans_cache.ensureIndex({'chainId':1,'trx':2,'effectiveTime':3});

    db.b_config.insert({
        'key': 'syncblocknum',
        'value': '6700000'
    });
    db.b_config.insert({
        'key': 'safeblock',
        'value': '6'
    });
    db.b_config.insert({
        'key': 'syncstate',
        'value': 'false'
    });
    db.b_config.insert({
        'key': 'bksyncblocknum',
        'value': '0'
    });
    db.b_config.insert({
        'key': 'btcsyncblocknum',
        'value': '549480'
    });
    db.b_config.insert({
        'key': 'btcsafeblock',
        'value': '6'
    });
    db.b_config.insert({
        'key': 'btcsyncstate',
        'value': 'false'
    });
    db.b_config.insert({
        'key': 'ltcsyncblocknum',
        'value': '1524352'
    });
    db.b_config.insert({
        'key': 'ltcsafeblock',
        'value': '6'
    });
    db.b_config.insert({
        'key': 'ltcsyncstate',
        'value': 'false'
    });
     db.b_config.insert({
        'key': 'ubsyncblocknum',
        'value': '0'
    });
    db.b_config.insert({
        'key': 'ubsafeblock',
        'value': '2'
    });
    db.b_config.insert({
        'key': 'ubsyncstate',
        'value': 'false'
    });
     db.b_config.insert({
        'key': 'hcsyncblocknum',
        'value': '50000'
    });
    db.b_config.insert({
        'key': 'hcsafeblock',
        'value': '6'
    });
    db.b_config.insert({
        'key': 'hcsyncstate',
        'value': 'false'
    });
    db.b_config.insert({
        'key': 'etpsyncblocknum',
        'value': '0'
    });
    db.b_config.insert({
        'key': 'etpsafeblock',
        'value': '6'
    });
    db.b_config.insert({
        'key': 'usdtsafeblock',
        'value': '6'
    });
    db.b_config.insert({
        'key': 'usdtsyncblocknum',
        'value': '563600'
    });
    db.b_config.insert({
        'key': 'usdtsyncstate',
        'value': '0'
    });
    db.b_config.insert({
        'key': 'btmsafeblock',
        'value': '2'
    });
    db.b_config.insert({
        'key': 'btmsyncblocknum',
        'value': '1'
    });
    db.b_config.insert({
        'key': 'btmsyncstate',
        'value': '0'
    });
    db.b_config.insert({
        'key': 'bchsafeblock',
        'value': '4'
    });
    db.b_config.insert({
        'key': 'bchsyncblocknum',
        'value': '585400'
    });
    db.b_config.insert({
        'key': 'bchsyncstate',
        'value': '0'
    });
}

