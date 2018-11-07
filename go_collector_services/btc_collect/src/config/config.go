package config



type ServerConfig struct{
	RpcListenEndPoint map[string]string
	RethinkDbEndPoint map[string]string
	RethinkDbName map[string]string
	AddressTrxDbPath map[string]string
	GetInfoFunctionName map[string]string  // such as getblockchaininfo getinfo choose which can use
	IsTls map[string]bool   // is  https
	IsOldFunctionLevel map[string]bool //is getblock can use second param 2
	SupportCoinType map[string]string
	SourceDataHost map[string]string
	SourceDataPort map[string]string
	SourceDataUserName map[string]string
	SourceDataPassword map[string]string
	DbPathConfig map[string]string
	SafeBlock map[string]int
	MULTISIGVERSION map[string]int
}
var RpcServerConfig = ServerConfig{RpcListenEndPoint:map[string]string{"BTC":"0.0.0.0:5444","BTC_TEST":"0.0.0.0:5446", "LTC":"0.0.0.0:5445","HC":"0.0.0.0:5447","HC_TEST":"0.0.0.0:5449"},
	GetInfoFunctionName:map[string]string{"BTC":"getblockchaininfo","BTC_TEST":"getblockchaininfo", "LTC":"getblockchaininfo","HC":"getinfo","HC_TEST":"getinfo"},
	IsTls:map[string]bool{"BTC":false,"BTC_TEST":false, "LTC":false,"HC":true,"HC_TEST":false},
	IsOldFunctionLevel:map[string]bool{"BTC":false,"BTC_TEST":false, "LTC":false,"HC":true,"HC_TEST":true},
	SourceDataHost:map[string]string{"BTC":"http://btc_wallet","BTC_TEST":"http://192.168.1.124", "LTC":"http://ltc_wallet","HC":"https://hc_wallet","HC_TEST":"http://127.0.0.1"},
	SourceDataPort:map[string]string{"BTC":"60011","BTC_TEST":"10001", "LTC":"60012","HC":"19020","HC_TEST":"19019"},
	SourceDataUserName:map[string]string{"BTC":"a","BTC_TEST":"test", "LTC":"a","HC":"a","HC_TEST":"a"},
	SourceDataPassword:map[string]string{"BTC":"b","BTC_TEST":"test", "LTC":"b","HC":"b","HC_TEST":"b"},
	DbPathConfig:map[string]string{"BTC":"/hx/btc_collect_data/","BTC_TEST":"h:/btc_collect_test/", "LTC":"/hx/ltc_collect_data/","HC":"/hx/hc_collect_data/","HC_TEST":"h:/hc_collect/"},
	SupportCoinType:map[string]string{"BTC":"","BTC_TEST":"", "LTC":"","HC":"","HC_TEST":""},
	SafeBlock:map[string]int{"BTC":6,"BTC_TEST":1, "LTC":6,"HC":6,"HC_TEST":6},
	MULTISIGVERSION:map[string]int{"BTC":5,"BTC_TEST":196,"LTC":5,"HC":5,"HC_TEST":5}}
