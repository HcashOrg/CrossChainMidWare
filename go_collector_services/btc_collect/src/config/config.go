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
var RpcServerConfig = ServerConfig{RpcListenEndPoint:map[string]string{"BTC":"0.0.0.0:5444","BTC_TEST":"0.0.0.0:5446"},
	SourceDataHost:map[string]string{"BTC":"http://127.0.0.1","BTC_TEST":"http://192.168.1.124"},
	SourceDataPort:map[string]string{"BTC":"10888","BTC_TEST":"10001"},
	SourceDataUserName:map[string]string{"BTC":"a","BTC_TEST":"test"},
	SourceDataPassword:map[string]string{"BTC":"b","BTC_TEST":"test"},
	DbPathConfig:map[string]string{"BTC":"h:/btc_collect/","BTC_TEST":"h:/btc_collect_test/"},
	SupportCoinType:map[string]string{"BTC":"","BTC_TEST":""},
	SafeBlock:map[string]int{"BTC":6,"BTC_TEST":1},
	MULTISIGVERSION:map[string]int{"BTC":5,"BTC_TEST":196}}