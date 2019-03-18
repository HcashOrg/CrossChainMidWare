package main

import (
	"github.com/gorilla/mux"
	"github.com/gorilla/rpc"
	"github.com/gorilla/rpc/json"
	"net/http"
	"github.com/bytom/crypto/ed25519/chainkd"
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
	"github.com/kataras/iris/core/errors"
	vmutil "github.com/bytom/protocol/vm/vmutil"
	"github.com/bytom/crypto"
	"github.com/bytom/common"
	"github.com/bytom/consensus"
)

var (
	wg_server sync.WaitGroup
)


type Service struct {
}

func (s *Service) CreateMultiSig(r *http.Request, args *[]interface{}, reply *map[string]interface{}) error{
	strPubkeys := (*args)[0].([]interface{})
	quorum := int((*args)[1].(float64))

	pubs := make([]chainkd.XPub, 0)
	for _, strPubkey := range strPubkeys {
		strPubkeyStr := strPubkey.(string)
		var pub chainkd.XPub
		pub.UnmarshalText([]byte(strPubkeyStr))
		pubs = append(pubs, pub)
	}

	derivedPKs := chainkd.XPubKeys(pubs)
	signScript, err := vmutil.P2SPMultiSigProgram(derivedPKs, quorum)
	if err != nil {
		return errors.New("P2SPMultiSigProgram fail")
	}
	scriptHash := crypto.Sha256(signScript)

	address, err := common.NewAddressWitnessScriptHash(scriptHash, &consensus.ActiveNetParams)
	if err != nil {
		return errors.New("NewAddressWitnessScriptHash fail")
	}

	addressStr := address.EncodeAddress()
	redeemScriptStr := hex.EncodeToString(signScript)

	(*reply) = make(map[string]interface{})
	(*reply)["address"] = addressStr
	(*reply)["redeemScript"] = redeemScriptStr

	return nil
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

func (s *Service) GetTrxBlockHeight(r *http.Request, args *string, reply *int) error {
	if !is_chain_btm() {
		return errors.New("this function only support BTM")
	} else {
		tmp_height, err := trxid_blockheight_db.Get([]byte(*args), nil)
		if err != nil {
			tmp_height = []byte("0")
		}
		block_height,_ := strconv.Atoi(string(tmp_height))
		*reply = block_height
		return nil
	}
}

func (s *Service) GetTrx(r *http.Request, args *string, reply *map[string]interface{}) error {
	link_client := lnk_util.LinkClient{
		IP:       config.RpcServerConfig.SourceDataHost[ChainType],
		Port:     config.RpcServerConfig.SourceDataPort[ChainType],
		User:     config.RpcServerConfig.SourceDataUserName[ChainType],
		PassWord: config.RpcServerConfig.SourceDataPassword[ChainType],
	}
	if !is_chain_btm() {
		param := make([]interface{}, 0)
		param = append(param, *args)
		param = append(param, 1)
		trx_data, _ := link_client.LinkHttpFunc("getrawtransaction", &param, config.RpcServerConfig.IsTls[ChainType]).Get("result").Map()
		*reply = trx_data
	} else {
		blockHeight, trxId := lnk_util.SplitBlockHeightTrxId(*args)
		if blockHeight == -1 {
			return errors.New("invalid args")
		}
		param_getblock := make(map[string]interface{})
		param_getblock["block_height"] = blockHeight

		trxs_data, _ := link_client.SafeLinkHttpFuncForBTM("get-block", &param_getblock).Get("result").Get("transactions").Array()
		for _, trx_data := range trxs_data {
			if trx_data.(map[string]interface{})["id"].(string) == trxId {
				*reply = trx_data.(map[string]interface{})
				break
			}
		}
	}
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

	//bak_map := make([]map[string]interface{},len(list_unspent_datas))
	//index := 0
	bak_map := make([]map[string]interface{}, 0)
	for k,v := range list_unspent_datas{
		utxo_obj:= pro.UTXOObject{}
		err :=proto.Unmarshal([]byte(v),&utxo_obj)
		if err!=nil{
			fmt.Println(err)
			continue
		}
		if *utxo_obj.Address != *args{
			fmt.Println(utxo_obj.Address , *args)
			continue
		}

		if !is_chain_btm() {
			tmp_value, _ := strconv.ParseFloat(*utxo_obj.Value, 64)
			if tmp_value <= 0.0001 {
				continue
			}
		}
		tmp_map := make(map[string]interface{})
		txid,vout := "", 0
		if !is_chain_btm() {
			txid,vout = lnk_util.SplitAddrUtxoPrefix(k)
		}else {
			// For BTM, use utxoid
			txid = lnk_util.SplitAddrUtxoPrefixForBtm(k)
		}
		tmp_map["txid"] = txid
		tmp_map["vout"] = vout
		tmp_map["address"] = *utxo_obj.Address
		tmp_map["scriptPubKey"] = *utxo_obj.ScriptPubKey
		tmp_map["value"] = *utxo_obj.Value
		//bak_map[index] = tmp_map
		//index = index +1
		//if index>1500{
		//	break
		//}
		bak_map = append(bak_map, tmp_map)
		if len(bak_map) > 1500 {
			break
		}
	}

	*reply = bak_map

	return nil
}


// address
func (s *Service) GetBalance(r *http.Request, args *string, reply *interface{}) error {
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

	if !is_chain_btm() {
		balance := float64(0.0)
		for _, v := range list_unspent_datas {
			utxo_obj := pro.UTXOObject{}
			err := proto.Unmarshal([]byte(v), &utxo_obj)
			if err != nil {
				fmt.Println(err)
				continue
			}
			if *utxo_obj.Address != *args {
				fmt.Println(utxo_obj.Address, *args)
				continue
			}
			tmp_value, err := strconv.ParseFloat(*utxo_obj.Value, 64)
			balance += tmp_value
		}
		*reply = balance
	} else {
		balance := uint64(0)
		for _, v := range list_unspent_datas {
			utxo_obj := pro.UTXOObject{}
			err := proto.Unmarshal([]byte(v), &utxo_obj)
			if err != nil {
				fmt.Println(err)
				continue
			}
			if *utxo_obj.Address != *args {
				fmt.Println(utxo_obj.Address, *args)
				continue
			}
			tmp_value, _ := strconv.ParseUint(*utxo_obj.Value, 10, 64)
			balance += tmp_value
		}
		*reply = balance
	}

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
