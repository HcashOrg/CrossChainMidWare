package main

import (
	"errors"
	"github.com/gorilla/mux"
	"github.com/gorilla/rpc"
	"github.com/gorilla/rpc/json"
	"net/http"

	"sync"
	"fmt"
	"config"
	"strconv"
	"util"
	"github.com/bitly/go-simplejson"
)

var (
	wg_server sync.WaitGroup
)


type Service struct {
}

//
//func (s *Service) GetAddressHistory(r *http.Request, args *string, reply *map[string]interface{}) error {
//	addr_cursor,err:=address_trx_db.GetAllByIndex("address",*args).Run(session)
//
//	if err!=nil {
//		return errors.New("address not found"+err.Error())
//	}
//
//	bak_map := make(map[string]interface{})
//	var data map[string]interface{}
//	for; addr_cursor.Next(&data);{
//		trx_data,err := trx_db.GetAllByIndex("trxId",data["trxId"].(string)).Run(session)
//		if err!=nil {
//			return errors.New("address not found"+err.Error())
//		}
//		var self_trx_data map[string]interface{}
//		trx_data.One(&self_trx_data)
//		bak_map[data["trxId"].(string)] = self_trx_data
//	}
//	*reply = bak_map
//
//	return nil
//}
//

/*
param: 0 cointype 1 address
 */


// param: 1 startblocknum 2 endblocknumber
func  (s *Service) GetErc20HistoryRange(r *http.Request, args *[]int, reply *[]string) error {
	if len(*args)<2{
		return errors.New("args format is error.must be [startBlockNumber,endBlockNumber]")
	}
	start_height:=(*args)[0]
	end_height:=(*args)[1]
	db_datas:=util.GetErc20HistoryRange(session,start_height,end_height)

	*reply = db_datas
	return nil
}

// param: 0 blocknum
func  (s *Service) GetErc20History(r *http.Request, args *int, reply *[]string) error {
	if *args==0{
		return errors.New("args format is error.must be blockNumber")
	}
	db_datas:=util.GetErc20History(session,*args)

	*reply = db_datas
	return nil
}


// param: 1 startblocknum 2 endblocknumber
func  (s *Service) GetNormalHistoryRange(r *http.Request, args *[]int, reply *[]string) error {
	if len(*args)<2{
		return errors.New("args format is error.must be [startBlockNumber,endBlockNumber]")
	}
	start_height:=(*args)[0]
	end_height:=(*args)[1]
	db_datas,err:=util.GetNormalHistoryRange(session,start_height,end_height)
	if err!=nil{
		return errors.New("query database failed "+err.Error())
	}
	*reply = db_datas
	return nil
}

// param: 1 blocknum
func  (s *Service) GetNormalHistory(r *http.Request, args *int, reply *[]string) error {
	if *args==0{
		return errors.New("args format is error.must be blockNumber")
	}

	db_datas,err:=util.GetNormalHistory(session,*args)
	if err!=nil{
		return errors.New("query database failed "+err.Error())
	}
	*reply = db_datas
	return nil
}


// param: 1 address 2 from block number 3 to block number
func  (s *Service) GetTrxHistoryByAddress(r *http.Request, args *[]string, reply *[]string) error {
	if len(*args)<2{
		return errors.New("args format is error.must be [address,startBlockNumber,endBlockNumber]")
	}
	query_address := (*args)[0]
	start_num_str := (*args)[1]
	end_num_str := (*args)[2]
	start_num,err := strconv.ParseInt(start_num_str,10,32)
	if err!=nil{
		return errors.New("invalid startBlockNumber")
	}
	end_num,err := strconv.ParseInt(end_num_str,10,32)
	if err!=nil{
		return errors.New("invalid endBlockNumber")
	}


	db_datas,err:=util.GetTrxHistoryByAddress(session,query_address,int(start_num),int(end_num))
	if err!=nil{
		return errors.New("query database failed "+err.Error())
	}
	*reply = db_datas
	return nil
}


func (s *Service) AddErc20Address(r *http.Request, args *string, reply *bool) error {
	if *args ==""{
		return errors.New("args format is error.must be address")
	}
	coin_type := ChainType
	_,exist := config.RpcServerConfig.SupportCoinType[coin_type]
	if !exist{
		keys_string:=""
		for k,_ := range config.RpcServerConfig.SupportCoinType{
			keys_string += k+","
		}
		return errors.New("please select correct coin type,such as "+keys_string)
	}
	address:= (*args)
	err := util.InsertRelationAddress(session,coin_type,address,true)


	if err!=nil{
		return errors.New("insert posgresql error:"+err.Error())
	}
	*reply = true
	return nil
}


func (s *Service) AddNormalAddress(r *http.Request, args *string, reply *bool) error {
	if *args ==""{
		return errors.New("args format is error.must be address")
	}
	coin_type := ChainType
	_,exist := config.RpcServerConfig.SupportCoinType[coin_type]
	if !exist{
		keys_string:=""
		for k,_ := range config.RpcServerConfig.SupportCoinType{
			keys_string += k+","
		}
		return errors.New("please select correct coin type,such as "+keys_string)
	}
	address:= (*args)
	err := util.InsertRelationAddress(session,coin_type,address,false)


	if err!=nil{
		return errors.New("insert posgresql error:"+err.Error())
	}
	*reply = true
	return nil
}


func (s *Service) GetBlockHeight(r *http.Request, args *string, reply *uint32) error {

	start_height := util.GetConfigHeight(session)

	*reply = uint32(start_height)
	return nil
}

func (s *Service) GetTrx(r *http.Request, args *string, reply *simplejson.Json) error {
	coinType := ChainType
	link_client := util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[coinType],
		Port:config.RpcServerConfig.SourceDataPort[coinType],
		User:"",
		PassWord:"",
	}
	param := make([]interface{},0,2)
	param = append(param,*args)


	blockdata := link_client.LinkHttpFunc("eth_getTransactionByHash",&param )
	balance_str := blockdata.Get("result")

	*reply = *balance_str
	return nil
}

func (s *Service) GetTrxReceipt(r *http.Request, args *string, reply *simplejson.Json) error {
	coinType := ChainType
	link_client := util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[coinType],
		Port:config.RpcServerConfig.SourceDataPort[coinType],
		User:"",
		PassWord:"",
	}
	param := make([]interface{},0,2)
	param = append(param,*args)


	blockdata := link_client.LinkHttpFunc("eth_getTransactionReceipt",&param )
	balance_str := blockdata.Get("result")

	*reply = *balance_str
	return nil

}


func (s *Service) GetErc20Trx(r *http.Request, args *string, reply *[]map[string]interface{}) error {

	trx_data := util.GetErc20TransactionById(session,*args)
	if len(trx_data)==0 {
		return errors.New("Transaction Id not found "+*args)
	}

	*reply = trx_data
	return nil
}


func (s *Service) GetNormalBalance(r *http.Request, args *string, reply *string) error {
	if (*args)==""{
		return errors.New("args format is error.must be address")
	}
	coinType := ChainType
	address := (*args)


	start_height := util.GetConfigHeight(session)

	link_client := util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[coinType],
		Port:config.RpcServerConfig.SourceDataPort[coinType],
		User:"",
		PassWord:"",
	}
	param := make([]interface{},0,2)
	param = append(param,address)
	param = append(param,"0x"+strconv.FormatInt(int64(start_height), 16))
	blockdata := link_client.LinkHttpFunc("eth_getBalance",&param )
	balance_str,_ := blockdata.Get("result").String()

	*reply = balance_str
	return nil
}


func (s *Service) GetTransactionCount(r *http.Request, args *[]string, reply *string) error {
	if len(*args)<2{
		return errors.New("args format is error.must be address,format")
	}
	coinType := ChainType
	address := (*args)[0]
	format := (*args)[1]


	link_client := util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[coinType],
		Port:config.RpcServerConfig.SourceDataPort[coinType],
		User:"",
		PassWord:"",
	}
	param := make([]interface{},0,2)
	param = append(param,address)
	param = append(param,format)
	blockdata := link_client.LinkHttpFunc("eth_getTransactionCount",&param )
	count_str,_ := blockdata.Get("result").String()

	*reply = count_str
	return nil
}


func (s *Service) EthCall(r *http.Request, args *[]interface{}, reply *simplejson.Json) error {
	coinType := ChainType
	reques_data := (*args)[0].(map[string]interface{})
	state :=(*args)[1]

	link_client := util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[coinType],
		Port:config.RpcServerConfig.SourceDataPort[coinType],
		User:"",
		PassWord:"",
	}

	eth_call_obj := map[string]string{"to":reques_data["to"].(string),"data":reques_data["data"].(string)}
	param := make([]interface{},0,2)
	param = append(param,eth_call_obj)
	param = append(param,state)
	blockdata := link_client.LinkHttpFunc("eth_call",&param )
	res_str := blockdata.Get("result")

	*reply = *res_str

	return nil
}


//cointype contractaddress address
// balanceof  70a08231
func (s *Service) GetErc20Balance(r *http.Request, args *[]string, reply *string) error {
	if len(*args)<2{
		return errors.New("args format is error.must be [contractaddress,address]")
	}
	coinType := ChainType
	contract_address := (*args)[0]
	address :=(*args)[1]



	start_height := util.GetConfigHeight(session)


	link_client := util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[coinType],
		Port:config.RpcServerConfig.SourceDataPort[coinType],
		User:"",
		PassWord:"",
	}
	input:="0x70a08231"+"000000000000000000000000"+address[2:]
	eth_call_obj := map[string]string{"to":contract_address,"data":input}
	param := make([]interface{},0,2)
	param = append(param,eth_call_obj)
	param = append(param,"0x"+strconv.FormatInt(int64(start_height), 16))
	blockdata := link_client.LinkHttpFunc("eth_call",&param )
	balance_str,_ := blockdata.Get("result").String()

	*reply = balance_str
	return nil
}


func (s *Service)Personal_ecRecover(r *http.Request, args *[]string, reply *interface{}) error {
	if len(*args)<2{
		return errors.New("args format is error.must be [dataThatWasSigned,signature]")
	}
	coinType := ChainType
	link_client := util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[coinType],
		Port:config.RpcServerConfig.SourceDataPort[coinType],
		User:"",
		PassWord:"",
	}
	param := make([]interface{},0,2)
	param = append(param,(*args)[0])
	param = append(param,(*args)[1])
	blockdata := link_client.LinkHttpFunc("personal_ecRecover",&param )
	res_err,exist := blockdata.CheckGet("error")
	if exist{
		fmt.Println(blockdata)
		error_str,_ := res_err.Get("message").String()
		*reply = error_str
		return nil
	}
	balance_str := blockdata.Get("result")

	*reply = balance_str
	return nil
}

func (s *Service) BroadcastRawTransaction(r *http.Request, args *string, reply *string) error {
	if len(*args)<2{
		return errors.New("args format is error.must be [contractaddress,address]")
	}
	coinType := ChainType
	raw_trx := (*args)



	link_client := util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[coinType],
		Port:config.RpcServerConfig.SourceDataPort[coinType],
		User:"",
		PassWord:"",
	}
	param := make([]interface{},0,1)
	param = append(param,raw_trx)
	blockdata := link_client.LinkHttpFunc("eth_sendRawTransaction",&param )
	fmt.Println(blockdata)
	res_err,exist := blockdata.CheckGet("error")
	if exist{
		error_str,_ := res_err.Get("message").String()
		*reply = error_str
		return nil
	}
	balance_str,_ := blockdata.Get("result").String()

	*reply = balance_str
	return nil
}



func rpcServer(args ...interface{}) {
	coinType := ChainType
	defer wg_server.Done()
	rpcServer := rpc.NewServer()
	rpcServer.RegisterCodec(json.NewCodec(), "application/json")
	rpcServer.RegisterCodec(json.NewCodec(), "application/json;charset=UTF-8")

	rpcService := new(Service)
	rpcServer.RegisterService(rpcService, "")

	urlRouter := mux.NewRouter()
	urlRouter.Handle("/", rpcServer)
	http.ListenAndServe(config.RpcServerConfig.RpcListenEndPoint[coinType], urlRouter)
}

func startRpcServer() {
	fmt.Println("start go server")
	wg_server.Add(1)
	rpcServer()
	wg_server.Wait()
	fmt.Println("start server end")
}
