package config



type ServerConfig struct{
	RpcListenEndPoint map[string]string
	RethinkDbEndPoint map[string]string
	RethinkDbName map[string]string
	AddressTrxDbPath map[string]string
	SupportCoinType map[string]string
	SourceDataHost map[string]string
	SourceDataPort map[string]string
	SourceDataUserName map[string]string
	SourceDataPassword map[string]string
	DbPathConfig map[string]string
	SafeBlock map[string]int
	MULTISIGVERSION map[string]int
}
var RpcServerConfig = ServerConfig{RpcListenEndPoint:map[string]string{"BTC":"0.0.0.0:5444","BTC_TEST":"0.0.0.0:5446", "LTC":"0.0.0.0:5445"},
	SourceDataHost:map[string]string{"BTC":"http://btc_wallet","BTC_TEST":"http://192.168.1.124", "LTC":"http://ltc_wallet"},
	SourceDataPort:map[string]string{"BTC":"60011","BTC_TEST":"10001", "LTC":"60012"},
	SourceDataUserName:map[string]string{"BTC":"a","BTC_TEST":"test", "LTC":"a"},
	SourceDataPassword:map[string]string{"BTC":"b","BTC_TEST":"test", "LTC":"b"},
	DbPathConfig:map[string]string{"BTC":"/hx/btc_collect_data/","BTC_TEST":"h:/btc_collect_test/", "LTC":"/hx/ltc_collect_data/"},
	SupportCoinType:map[string]string{"BTC":"","BTC_TEST":"", "LTC":""},
	SafeBlock:map[string]int{"BTC":6,"BTC_TEST":1, "LTC":6},
	MULTISIGVERSION:map[string]int{"BTC":5,"BTC_TEST":196,"LTC":5}}
