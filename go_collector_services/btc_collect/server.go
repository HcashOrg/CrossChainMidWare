package main

import (
	"github.com/gorilla/mux"
	"github.com/gorilla/rpc"
	"github.com/gorilla/rpc/json"
	"net/http"

	"config"
	"sync"
	"fmt"
	"github.com/syndtr/goleveldb/leveldb/util"
	"bytes"
	"encoding/binary"
	"encoding/hex"
	"strconv"
	"github.com/golang/protobuf/proto"
	pro "protobuf"
	lnk_util "util"
)

var (
	wg_server sync.WaitGroup
)


type Service struct {
}


func (s *Service) GetAddressHistory(r *http.Request, args *string, reply *[]string) error {
	query_range := util.BytesPrefix([]byte(*args))
	iter := address_trx_db.NewIterator(query_range,nil)
	datas := make([]byte,0)
	if iter.First(){

		datas = append(iter.Value())
		for ;iter.Next();{
			datas = append(datas,iter.Value()...)
		}

	}

	bak_map := make([]string,len(datas)/4)
	for i :=0 ;i<len(datas)/4;i++{
		one_data := datas[i*4:(i+1)*4]
		bytesBuffer := bytes.NewBuffer(one_data)
		var tmp int32
		binary.Read(bytesBuffer, binary.BigEndian, &tmp)
		fmt.Println(int(tmp))
		tmp_trx_data := trxId_fs.ReadData(int(tmp)*32,32)
		tx_byte := make([]byte,64)
		hex.Encode(tx_byte,tmp_trx_data)
		bak_map[i] = string(tx_byte)
		fmt.Println(string(tx_byte))

	}



	*reply = bak_map

	return nil
}

func (s *Service) GetBlockHeight(r *http.Request, args *string, reply *uint64) error {

	tmp_height,err:=config_db.Get([]byte("height"),nil)
	fmt.Println(string(tmp_height))
	fmt.Println(err)
	if err != nil {
		tmp_height = []byte("0")
	}
	height,_ :=strconv.Atoi(string(tmp_height))

	*reply = uint64(height)
	return nil
}


func (s *Service) GetTrxHeight(r *http.Request, args *string, reply *uint32) error {
	tmp_count,err:=config_db.Get([]byte("trx_counts"),nil)
	if err != nil {
		tmp_count = []byte("0")
	}
	mid_count,_ := strconv.Atoi(string(tmp_count))
	*reply = uint32(mid_count)
	return nil
}

func (s *Service) GetTrxCountTrxId(r *http.Request, args *int, reply *string) error {

	tmp_trx_data := trxId_fs.ReadData(*args*32,32)
	tx_byte := make([]byte,64)
	hex.Encode(tx_byte,tmp_trx_data)
	trx_id_str := string(tx_byte)
	*reply = trx_id_str
	return nil
}



func (s *Service) GetTrx(r *http.Request, args *string, reply *map[string]interface{}) error {
	link_client := lnk_util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[ChainType],
		Port:config.RpcServerConfig.SourceDataPort[ChainType],
		User:config.RpcServerConfig.SourceDataUserName[ChainType],
		PassWord:config.RpcServerConfig.SourceDataPassword[ChainType],
	}
	param := make([]interface{},0)
	param = append(param, *args)
	param = append(param, 1)
	trx_data,_ := link_client.LinkHttpFunc("getrawtransaction",&param ).Get("result").Map()
	*reply = trx_data
	return nil
}



// address
func (s *Service) ListUnSpent(r *http.Request, args *string, reply *[]map[string]interface{}) error {
	prefix := ChainType+(*args)[:20]+"O"
	query_range := util.BytesPrefix([]byte(prefix))
	iter := addr_unspent_utxo_db.NewIterator(query_range,nil)
	list_unspent_datas := make(map[string]string)
	if iter.First(){
		data := iter.Value()
		list_unspent_datas[string(iter.Key())] = string(data)
		for ;iter.Next();{
			data := iter.Value()
			list_unspent_datas[string(iter.Key())] = string(data)
			data = make([]byte,0)
		}

	}

	bak_map := make([]map[string]interface{},len(list_unspent_datas))
	index := 0
	for k,v := range list_unspent_datas{
		utxo_obj:= pro.UTXOObject{}
		err :=proto.Unmarshal([]byte(v),&utxo_obj)
		if err!=nil{
			fmt.Println(err)
			continue
		}
		tmp_map := make(map[string]interface{})
		txid,vout := lnk_util.SplitAddrUtxoPrefix(k)
		tmp_map["txid"] = txid
		tmp_map["vout"] = vout
		tmp_map["address"] = *utxo_obj.Address
		tmp_map["value"] = *utxo_obj.Value
		bak_map[index] = tmp_map
		index = index +1
	}

	*reply = bak_map

	return nil
}


func rpcServer(args ...interface{}) {
	defer wg_server.Done()
	rpcServer := rpc.NewServer()
	rpcServer.RegisterCodec(json.NewCodec(), "application/json")
	rpcServer.RegisterCodec(json.NewCodec(), "application/json;charset=UTF-8")

	rpcService := new(Service)
	rpcServer.RegisterService(rpcService, "")

	urlRouter := mux.NewRouter()
	urlRouter.Handle("/", rpcServer)
	http.ListenAndServe(config.RpcServerConfig.RpcListenEndPoint[ChainType], urlRouter)
}

func startRpcServer() {
	fmt.Println("start go server")
	wg_server.Add(1)
	rpcServer()
	wg_server.Wait()
	fmt.Println("start server end")
}
