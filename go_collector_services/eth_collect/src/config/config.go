package config



type ServerConfig struct{
	RpcListenEndPoint map[string]string
	RethinkDbEndPoint map[string]string
	RethinkDbName map[string]string
	AddressTrxDbPath map[string]string
	SupportCoinType map[string]string
	SourceDataHost map[string]string
	SourceDataPort map[string]string
	PosgresqlConfig  map[string]interface{}
	SafeBlock map[string]int
}
var RpcServerConfig = ServerConfig{RpcListenEndPoint:map[string]string{"ETH":"0.0.0.0:5544","ETH_TEST":"0.0.0.0:5545"},
	SourceDataHost:map[string]string{"ETH":"http://eth_wallet","ETH_TEST":"http://eth_wallet"},
	SourceDataPort:map[string]string{"ETH":"60015","ETH_TEST":"39022"},
	PosgresqlConfig: map[string]interface{}{"ETH": map[string]string{"host":"localhost",
	"port":"5432","user": "postgres","password":"GkQuFTvzLxccdgVN","dbname":"eth_db"},"ETH_TEST": map[string]string{"host":"localhost",
		"port":"5432","user": "postgres","password":"GkQuFTvzLxccdgVN","dbname":"eth_test_db"}},
	SupportCoinType:map[string]string{"ETH":"","ETH_TEST":""},
	SafeBlock:map[string]int{"ETH":6,"ETH_TEST":5}}

