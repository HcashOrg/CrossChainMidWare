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
var RpcServerConfig = ServerConfig{RpcListenEndPoint:map[string]string{"ETH":"0.0.0.0:5444","ETH_TEST":"0.0.0.0:5445"},
	SourceDataHost:map[string]string{"ETH":"http://192.168.1.122","ETH_TEST":"http://192.168.1.164"},
	SourceDataPort:map[string]string{"ETH":"8588","ETH_TEST":"28000"},
	PosgresqlConfig: map[string]interface{}{"ETH": map[string]string{"host":"localhost",
	"port":"5432","user": "postgres","password":"12345678","dbname":"eth_db"},"ETH_TEST": map[string]string{"host":"localhost",
		"port":"5432","user": "postgres","password":"12345678","dbname":"eth_test_db"}},
	SupportCoinType:map[string]string{"ETH":"","ETH_TEST":""},
	SafeBlock:map[string]int{"ETH":6,"ETH_TEST":1}}

