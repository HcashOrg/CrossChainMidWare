package main

import (
	_"github.com/golang/protobuf/proto"
	_"io/ioutil"
	_"os"
	"fmt"
	_"strings"
	_"net/http"
	"util"
	"strconv"
	"runtime"
	"sync"
	"github.com/bitly/go-simplejson"
	"time"
	"encoding/json"
	"encoding/hex"
	"sync/atomic"
	"config"
	pro "protobuf"
	"crypto/sha256"
	"golang.org/x/crypto/ripemd160"
	"os"
	"os/signal"
	"syscall"
	"github.com/golang/protobuf/proto"
	_"github.com/stackimpact/stackimpact-go"
	"bytes"

	"github.com/syndtr/goleveldb/leveldb"
	"github.com/syndtr/goleveldb/leveldb/opt"
	"flag"
)

var(
	total_size             int64
	total_trx_size         int64
	global_start_height    int
	exit_count             int32
	wg                     sync.WaitGroup
	address_trx_db         *leveldb.DB
	unspent_utxo_db        *leveldb.DB
	addr_unspent_utxo_db        *leveldb.DB
	config_db              *leveldb.DB
	utxo_cache             map[string]interface{}
	addr_utxo_cache             map[string]interface{}
	utxo_spent_cache       []string
	addr_utxo_spent_cache       []string
	trxId_cache				[][]byte
	write_address_trx_data map[string]interface{}
	change_weight          int32
	last_height            int
	is_done                bool
	flush_count            int
	trxId_fs               util.LogicalFile
	trx_counts             int32
	old_chan_height		   int32
	wg_collect				sync.WaitGroup

)



var ChainType = "BTC_TEST"


func one_collect_data(data_chan chan map[int]simplejson.Json,height []int){
	defer wg_collect.Done()
	link_client := util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[ChainType],
		Port:config.RpcServerConfig.SourceDataPort[ChainType],
		User:config.RpcServerConfig.SourceDataUserName[ChainType],
		PassWord:config.RpcServerConfig.SourceDataPassword[ChainType],
	}

	for _,once_height := range height{
		param := make([]interface{},0)
		param = append(param,once_height)
		blockhash,_ := link_client.SafeLinkHttpFunc("getblockhash",&param ,config.RpcServerConfig.IsTls[ChainType]).Get("result").String()
		param_getblock := make([]interface{},0)
		param_getblock = append(param_getblock,blockhash)
		if config.RpcServerConfig.IsOldFunctionLevel[ChainType]{

			param_getblock = append(param_getblock,true)
		}else{

			param_getblock = append(param_getblock,2)
		}

		blockdata := link_client.SafeLinkHttpFunc("getblock",&param_getblock,config.RpcServerConfig.IsTls[ChainType] )
		if config.RpcServerConfig.IsOldFunctionLevel[ChainType]{
			tx_datas,_ := blockdata.Get("result").Get("tx").Array()
			stx_datas,_ := blockdata.Get("result").Get("stx").Array()
			tx_real_datas := make([]interface{},0,len(tx_datas)+len(stx_datas))
			for _,txids := range tx_datas{
				param_gettransaction := make([]interface{},0)
				param_gettransaction = append(param_gettransaction,txids.(string))
				param_gettransaction = append(param_gettransaction,2)
				tx_data := link_client.SafeLinkHttpFunc("getrawtransaction",&param_gettransaction ,config.RpcServerConfig.IsTls[ChainType])
				map_data,err := tx_data.Get("result").Map()
				if err!=nil{
					fmt.Println(err.Error())
				}
				tx_real_datas = append(tx_real_datas,map_data)
			}


			for _,txids := range stx_datas{
				param_gettransaction := make([]interface{},0)
				param_gettransaction = append(param_gettransaction,txids.(string))
				param_gettransaction = append(param_gettransaction,2)
				tx_data := link_client.LinkHttpFunc("getrawtransaction",&param_gettransaction,config.RpcServerConfig.IsTls[ChainType] )
				map_data,err := tx_data.Get("result").Map()
				if err!=nil{
					fmt.Println(err.Error())
				}
				tx_real_datas = append(tx_real_datas,map_data)
			}
			blockdata.Get("result").Set("tx",tx_real_datas)
		}
		data_chan <- map[int]simplejson.Json{once_height:*blockdata}
	}

}

func ceil(a int,b int)int{
	res := a/b
	if a%b > 0{
		return res+1
	}
	return res
}

func collect_block(height_chan chan int,blockdata_chan chan simplejson.Json,is_fast bool){
	defer wg.Done()

	back_time := time.Now()
	if is_fast{
		delta_size := 20
		one_batch_count :=delta_size/4


		for ;;{
			height_cache := make([]int,0,delta_size)

			data_chan := make(chan map[int]simplejson.Json,delta_size)


			for i:=0;i<delta_size;i++{
				once_height := <- height_chan
				if once_height == -1{

					handle_count := ceil(len(height_cache),one_batch_count)
					wg_collect.Add(handle_count)
					for j:=0;j<handle_count;j++{
						if j==handle_count-1{
							go one_collect_data(data_chan,height_cache[j*one_batch_count:])
						}else{
							go one_collect_data(data_chan,height_cache[j*one_batch_count:(j+1)*one_batch_count])
						}

					}
					wg_collect.Wait()
					cache_map := make(map[int]simplejson.Json)
					for j:=0;j<len(height_cache);j++{
						tmp_data:= <- data_chan
						for k,v := range tmp_data{
							cache_map[k] = v
						}
					}
					for _,height:= range height_cache{
						blockdata_chan <- cache_map[height]
					}
					fmt.Println("collect exit")

					json_data,_ :=simplejson.NewJson([]byte("{\"result\":\"exit\"}"))
					blockdata_chan <- *json_data
					return
				}
				height_cache = append(height_cache,once_height)

			}
			wg_collect.Add(4)
			for j:=0;j<4;j++{
				go one_collect_data(data_chan,height_cache[j*one_batch_count:(j+1)*one_batch_count])
			}

			wg_collect.Wait()
			cache_map := make(map[int]simplejson.Json)
			for j:=0;j<delta_size;j++{
				tmp_data:= <- data_chan
				for k,v := range tmp_data{
					cache_map[k] = v
				}
			}
			for _,height:= range height_cache{
				blockdata :=cache_map[height]
				blockdata_chan <- blockdata

				size,_ := blockdata.Get("result").Get("size").Int()
				atomic.AddInt64(&total_size,int64(size))
				tx_array,_ := blockdata.Get("result").Get("tx").Array()
				atomic.AddInt64(&total_trx_size,int64(len(tx_array)))
				if height % 1000 == 0{
					tmp_height,_ :=blockdata.Get("result").Get("height").Int()
					fmt.Println("block height",tmp_height)
					fmt.Println( "total size: ", total_size / 1024 / 1024, " MB")
					fmt.Println( "total trx count: ", total_trx_size)
					fmt.Println( "now :", time.Now() )
					fmt.Println( "cost time : ", time.Now().Sub(back_time))
					fmt.Println( "blocks per sec : ", float32(height-global_start_height) / float32(time.Now().Sub(back_time).Seconds()))
					fmt.Println( "trxs per sec: ", float32(total_trx_size) / float32(time.Now().Sub(back_time).Seconds()))
					fmt.Println("current change weight: ",change_weight/1024/1024,"m")
					var mStat runtime.MemStats
					runtime.ReadMemStats(&mStat)
					fmt.Println("HeapAlloc:", mStat.HeapAlloc/1024/1024,"m")
					fmt.Println("HeapIdle:", mStat.HeapIdle/1024/1024,"m")
					fmt.Println("chan size:",len(blockdata_chan))
				}
			}

		}
	}else{
		delta_size := 1
		one_batch_count :=1


		for ;;{
			height_cache := make([]int,0,delta_size)

			data_chan := make(chan map[int]simplejson.Json,delta_size)


			for i:=0;i<delta_size;i++{
				once_height := <- height_chan
				if once_height == -1{

					handle_count := ceil(len(height_cache),one_batch_count)
					wg_collect.Add(handle_count)
					for j:=0;j<handle_count;j++{
						if j==handle_count-1{
							go one_collect_data(data_chan,height_cache[j*one_batch_count:])
						}else{
							go one_collect_data(data_chan,height_cache[j*one_batch_count:(j+1)*one_batch_count])
						}

					}
					wg_collect.Wait()
					cache_map := make(map[int]simplejson.Json)
					for j:=0;j<len(height_cache);j++{
						tmp_data:= <- data_chan
						for k,v := range tmp_data{
							cache_map[k] = v
						}
					}
					for _,height:= range height_cache{
						blockdata_chan <- cache_map[height]
					}
					fmt.Println("collect exit")

					json_data,_ :=simplejson.NewJson([]byte("{\"result\":\"exit\"}"))
					blockdata_chan <- *json_data
					return
				}
				height_cache = append(height_cache,once_height)

			}
			wg_collect.Add(1)
			for j:=0;j<1;j++{
				go one_collect_data(data_chan,height_cache[j*one_batch_count:(j+1)*one_batch_count])
			}

			wg_collect.Wait()
			cache_map := make(map[int]simplejson.Json)
			for j:=0;j<delta_size;j++{
				tmp_data:= <- data_chan
				for k,v := range tmp_data{
					cache_map[k] = v
				}
			}
			for _,height:= range height_cache{
				blockdata :=cache_map[height]
				blockdata_chan <- blockdata

				size,_ := blockdata.Get("result").Get("size").Int()
				atomic.AddInt64(&total_size,int64(size))
				tx_array,_ := blockdata.Get("result").Get("tx").Array()
				atomic.AddInt64(&total_trx_size,int64(len(tx_array)))
				if height % 1000 == 0{
					tmp_height,_ :=blockdata.Get("result").Get("height").Int()
					fmt.Println("block height",tmp_height)
					fmt.Println( "total size: ", total_size / 1024 / 1024, " MB")
					fmt.Println( "total trx count: ", total_trx_size)
					fmt.Println( "now :", time.Now() )
					fmt.Println( "cost time : ", time.Now().Sub(back_time))
					fmt.Println( "blocks per sec : ", float32(height-global_start_height) / float32(time.Now().Sub(back_time).Seconds()))
					fmt.Println( "trxs per sec: ", float32(total_trx_size) / float32(time.Now().Sub(back_time).Seconds()))
					fmt.Println("current change weight: ",change_weight/1024/1024,"m")
					var mStat runtime.MemStats
					runtime.ReadMemStats(&mStat)
					fmt.Println("HeapAlloc:", mStat.HeapAlloc/1024/1024,"m")
					fmt.Println("HeapIdle:", mStat.HeapIdle/1024/1024,"m")
					fmt.Println("chan size:",len(blockdata_chan))
				}
			}

		}
	}

	fmt.Println("collect_block is done")
}

//func collect_block(height_chan chan int,blockdata_chan chan simplejson.Json){
//	defer wg.Done()
//	link_client := util.LinkClient{
//		IP:"http://127.0.0.1",
//		Port:"10888",
//		User:"a",
//		PassWord:"b",
//	}
//	//vin := &pro.TrxObject_VIN{}
//	//trx_object := pro.TrxObject{}
//	back_time := time.Now()
//	//block_cache := make([]simplejson.Json,0)
//	//block_num_cache :=  make([]int,0)
//	//cache_size := 100
//
//	for ;;{
//		param := make([]interface{},0)
//		once_height := <- height_chan
//		if once_height == -1{
//			fmt.Println("collect exit")
//
//			json_data,_ :=simplejson.NewJson([]byte("{\"result\":\"exit\"}"))
//			blockdata_chan <- *json_data
//			return
//		}
//		param = append(param,once_height)
//		blockhash,_ := link_client.LinkHttpFunc("getblockhash",&param ).Get("result").String()
//		param_getblock := make([]interface{},0)
//		param_getblock = append(param_getblock,blockhash)
//		param_getblock = append(param_getblock,2)
//		blockdata := link_client.LinkHttpFunc("getblock",&param_getblock )
//		blockdata_chan <- *blockdata
//
//
//
//		size,_ := blockdata.Get("result").Get("size").Int()
//		atomic.AddInt64(&total_size,int64(size))
//		tx_array,_ := blockdata.Get("result").Get("tx").Array()
//		atomic.AddInt64(&total_trx_size,int64(len(tx_array)))
//		if once_height % 1000 == 0{
//			tmp_height,_ :=blockdata.Get("result").Get("height").Int()
//			fmt.Println("block height",tmp_height)
//			fmt.Println( "total size: ", total_size / 1024 / 1024, " MB")
//			fmt.Println( "total trx count: ", total_trx_size)
//			fmt.Println( "now :", time.Now() )
//			fmt.Println( "cost time : ", time.Now().Sub(back_time))
//			fmt.Println( "blocks per sec : ", float32(once_height-global_start_height) / float32(time.Now().Sub(back_time).Seconds()))
//			fmt.Println( "trxs per sec: ", float32(total_trx_size) / float32(time.Now().Sub(back_time).Seconds()))
//			fmt.Println("current change weight: ",change_weight/1024/1024,"m")
//			var mStat runtime.MemStats
//			runtime.ReadMemStats(&mStat)
//			fmt.Println("HeapAlloc:", mStat.HeapAlloc/1024/1024,"m")
//			fmt.Println("HeapIdle:", mStat.HeapIdle/1024/1024,"m")
//			fmt.Println("chan size:",len(blockdata_chan))
//		}
//
//
//	}
//	fmt.Println("collect_block is done")
//}



func fs_update(){
	start :=0
	tmp_count,err:=config_db.Get([]byte("trx_counts"),nil)
	if err == nil {
		start,_ =strconv.Atoi(string(tmp_count))
	}

	all_data := make([]byte,len(trxId_cache)*32)
	for index,trxId := range trxId_cache{
		copy(all_data[index*32:],trxId)
	}
	fmt.Println("fs flush",start,"write file size",len(all_data))
	trxId_fs.WriteData(start*32,all_data)
}

func flush_db(){
	flush_count++
	bak_time := time.Now()
	index :=0

	batch_interval :=300
	tmp_batch := leveldb.Batch{}


	for k,v := range utxo_cache{
		index ++
		tmp_v := v.(pro.UTXOObject)
		write_data,_ := proto.Marshal(&tmp_v)
		tmp_batch.Put([]byte(k),write_data)
		if index %batch_interval == 0{
			unspent_utxo_db.Write(&tmp_batch,nil)
			tmp_batch.Reset()
		}
	}
	unspent_utxo_db.Write(&tmp_batch,nil)
	tmp_batch.Reset()
	index =0
	delete_batch := leveldb.Batch{}
	for _,utxoId := range utxo_spent_cache{
		index ++
		delete_batch.Delete([]byte(utxoId))
		if index %batch_interval == 0{
			unspent_utxo_db.Write(&delete_batch,nil)
			delete_batch.Reset()
		}
	}
	unspent_utxo_db.Write(&delete_batch,nil)
	delete_batch.Reset()
	//addr_unspent_utxo
	index =0

	batch_interval =300
	tmp_batch = leveldb.Batch{}


	for k,v := range addr_utxo_cache{
		index ++
		tmp_v := v.(pro.UTXOObject)
		write_data,_ := proto.Marshal(&tmp_v)
		tmp_batch.Put([]byte(k),write_data)
		if index %batch_interval == 0{
			addr_unspent_utxo_db.Write(&tmp_batch,nil)
			tmp_batch.Reset()
		}
	}
	addr_unspent_utxo_db.Write(&tmp_batch,nil)
	tmp_batch.Reset()
	index =0
	delete_batch = leveldb.Batch{}
	for _,utxoId := range addr_utxo_spent_cache{
		index ++
		delete_batch.Delete([]byte(utxoId))
		if index %batch_interval == 0{
			addr_unspent_utxo_db.Write(&delete_batch,nil)
			delete_batch.Reset()
		}
	}
	addr_unspent_utxo_db.Write(&delete_batch,nil)
	delete_batch.Reset()




	index =0
	for k,v:=range write_address_trx_data{
		index++
		write_buf := bytes.Buffer{}

		for addr,_ := range v.(map[int32]byte){
			write_buf.Write(util.Int32ToBytes(addr))
		}
		tmp_batch.Put([]byte(k+strconv.Itoa(flush_count)),write_buf.Bytes())
		write_buf.Reset()
		if index %batch_interval == 0{
			address_trx_db.Write(&tmp_batch,nil)
			tmp_batch.Reset()
		}
	}
	address_trx_db.Write(&tmp_batch,nil)
	tmp_batch.Reset()
	fs_update()
	fmt.Println(strconv.Itoa(last_height))
	wo :=opt.WriteOptions{}
	wo.Sync = true
	config_db.Put([]byte("height"), []byte(strconv.Itoa(last_height)),&wo)
	config_db.Put([]byte("trx_counts"), []byte(strconv.Itoa(int(trx_counts))),&wo)
	config_db.Put([]byte("flush_count"), []byte(strconv.Itoa(flush_count)),&wo)

	fmt.Println("flush db add utxo count",len(utxo_cache)," spent utxo count",len(utxo_spent_cache)," address_trx count: ",len(write_address_trx_data)," cost time:",time.Now().Sub(bak_time).Seconds())
	utxo_cache = make(map[string]interface{})
	addr_utxo_cache = make(map[string]interface{})
	utxo_spent_cache = make([]string,0,2000000)
	addr_utxo_spent_cache = make([]string,0,2000000)
	write_address_trx_data = make(map[string]interface{},0)
	trxId_cache	= make(	[][]byte,0,4000000)
	atomic.StoreInt32(&change_weight,int32(0))
}

func get_utxo(utxo_prefix string) interface{}{
	cache_data,exist:= utxo_cache[utxo_prefix]
	if exist{
		return cache_data.(pro.UTXOObject)
	}

	data,err := unspent_utxo_db.Get([]byte(utxo_prefix),nil)

	if err!=nil{
		fmt.Println("get utxo error",err.Error())
		return nil
	}
	utxo_obj:= pro.UTXOObject{}
	err =proto.Unmarshal(data,&utxo_obj)
	if err!=nil{
		fmt.Println(err.Error())
		return nil
	}
	return utxo_obj
}

func spent_utxo(utxo_prefix string,addr_utxo_prefix string){
	_,exist :=utxo_cache[utxo_prefix]
	if exist{
		delete(utxo_cache, utxo_prefix)
		atomic.AddInt32(&change_weight,int32(-180))
	}else{
		utxo_spent_cache =append(utxo_spent_cache, utxo_prefix)
		atomic.AddInt32(&change_weight,int32(68))
	}
	_,exist =addr_utxo_cache[addr_utxo_prefix]
	if exist{
		delete(addr_utxo_cache, addr_utxo_prefix)
		atomic.AddInt32(&change_weight,int32(-50))
	}else{
		addr_utxo_spent_cache =append(addr_utxo_spent_cache, addr_utxo_prefix)
		atomic.AddInt32(&change_weight,int32(68))
	}

	//_,exist = utxo_cache[utxo_prefix]
	//if exist{
	//	delete(utxo_cache, utxo_prefix)
	//}

	//unspent_utxo_db.GetAllByIndex("utxoId",utxo_prefix).Delete().Exec(session)

}


func add_utxo(utxo_prefix string,value interface{},address string,addr_utxo_prefix string,scriptPubkey string){
	data_value:=strconv.FormatFloat(value.(float64),'f',8,64)
	utxo_obj := pro.UTXOObject{}
	utxo_obj.Value = &data_value
	utxo_obj.Address = &address
	utxo_obj.ScriptPubKey = &scriptPubkey
	utxo_cache[utxo_prefix] = utxo_obj
	addr_utxo_cache[addr_utxo_prefix] = utxo_obj
	atomic.AddInt32(&change_weight,int32(230))

	//err:=unspent_utxo_db.Insert(utxo_query).Exec(session)
	//if err!=nil{
	//	fmt.Println(err.Error())
	//}

}

func cal_utxo_prefix(txid string, vout int)string{
	return ChainType+txid+ "I" +strconv.Itoa(vout)
}

func cal_addr_utxo_prefix(address string,txid string, vout int)string{
	if address == ""{
		return ChainType+"O"+txid+ "I" +strconv.Itoa(vout)
	}
	return ChainType+address[:20]+"O"+txid+ "I" +strconv.Itoa(vout)
}


func bin_to_b58check(data []byte,magic_byte byte) string{
	/* See https://en.bitcoin.it/wiki/Technical_background_of_Bitcoin_addresses */
	sha256_h := sha256.New()
	sha256_h.Reset()
	sha256_h.Write(data)
	pub_hash_1 := sha256_h.Sum(nil)


	/* RIPEMD-160 Hash */
	//fmt.Println("3 - Perform RIPEMD-160 hashing on the result of SHA-256")
	ripemd160_h := ripemd160.New()
	ripemd160_h.Reset()
	ripemd160_h.Write(pub_hash_1)
	pub_hash_2 := ripemd160_h.Sum(nil)

	/* Convert hash bytes to base58 check encoded sequence */
	final_data := make([]byte,25)
	final_data[0] = magic_byte
	for i :=0;i<20;i++{
		final_data[i+1] = pub_hash_2[i]
	}
	sha256_h.Reset()
	sha256_h.Write(final_data[:21])
	pub_hash_check1 := sha256_h.Sum(nil)
	sha256_h.Reset()
	sha256_h.Write(pub_hash_check1)
	pub_hash_check2 := sha256_h.Sum(nil)
	for i :=0;i<4;i++{
		final_data[i+21] = pub_hash_check2[i]
	}
	address := util.Encode(final_data)

	return address
}

func get_vout_address(script map[string]interface{}) (string,string){

	script_type_json,exist :=script["type"]
	if exist{
		script_type := script_type_json.(string)
		if script_type =="multisig"{
			//改成直接获取
			hex_bytes,_:=hex.DecodeString(script["hex"].(string))
			return bin_to_b58check(hex_bytes, byte(config.RpcServerConfig.MULTISIGVERSION[ChainType])),script["hex"].(string)

		}else if script_type =="nonstandard" {
			hex_str,exist := script["hex"]
			if exist{
				return "",hex_str.(string)
			}
			return "",""
		}else{
			addresses,exist := script["addresses"]
			if exist{
				tmp_arr :=addresses.([]interface {})
				return tmp_arr[0].(string),script["hex"].(string)
			}else{
				hex_str,exist := script["hex"]
				if exist{
					return "",hex_str.(string)
				}
				return "",script["hex"].(string)
			}
		}
	}else{
		return "",""
	}
}
func add_addr_trx_releation(trx_num int32,address string){
	if address == ""{
		return
	}
	data,exist :=write_address_trx_data[address]
	if exist{
		data.(map[int32]byte)[trx_num] = 0
		atomic.AddInt32(&change_weight,int32(5))
	}else{
		tmp_map := make(map[int32]byte)
		tmp_map[trx_num] =0
		write_address_trx_data[address] = tmp_map
		atomic.AddInt32(&change_weight,int32(69))
	}

}

//修改db 为rethinkdb 增加utxo处理
func handle_block(blockdata_chan chan simplejson.Json,interval int){
	defer wg.Done()
	//link_client := util.LinkClient{
	//	IP:"http://127.0.0.1",
	//	Port:"10888",
	//	User:"a",
	//	PassWord:"b",
	//}
	for ;;{
		blockchain_data := <- blockdata_chan
		exit_code,err :=blockchain_data.Get("result").String()
		if err == nil{

			if exit_code == "exit"{
				atomic.AddInt32(&exit_count,int32(1))
				//if exit_count < int32(runtime.NumCPU() -3) {
				//
				//	json_data,_ :=simplejson.NewJson([]byte("{\"result\":\"exit\"}"))
				//	blockdata_chan <- *json_data
				//}
				flush_db()
				fmt.Println("check exit")

				return
			}
		}



		//trx_batch := &leveldb.Batch{}
		//trx_cache := make(map[string]pro.TrxObject)
		////trx_db.Write(trx_batch,&opt.WriteOptions{Sync:true})
		//address_batch := &leveldb.Batch{}
		//affect_addresses :=make(  map[string]interface{})

		tx_datas,_ := blockchain_data.Get("result").Get("tx").Array()
		//处理数据
		tmp_height,_ := blockchain_data.Get("result").Get("height").Int()

		for _,trx_data := range tx_datas{

			one_trx := trx_data.(map[string]interface{})

			trx_Id := one_trx["txid"].(string)

			tx_byte := make([]byte,32)
			hex.Decode(tx_byte,[]byte(trx_Id))
			trxId_cache = append(trxId_cache,tx_byte)
			atomic.AddInt32(&change_weight,int32(32))

			vins := one_trx["vin"].([]interface{})

			for _,vin_data := range vins{
				vin := vin_data.(map[string]interface{})
				_,exist := vin["coinbase"]
				if exist{
					continue
				}
				vin_txid,txid_exist := vin["txid"]
				if vin_txid.(string) =="0000000000000000000000000000000000000000000000000000000000000000"{
					continue
				}
				vout,vout_exist := vin["vout"]
				vout_data,_ := vout.(json.Number).Int64()

				if txid_exist && vout_exist{
					for ;;{
						//获取utxo记录
						utxo_prefix := cal_utxo_prefix(vin_txid.(string),int(vout_data))

						data := get_utxo(utxo_prefix)
						if data==nil{
							fmt.Println("UTXO not exist",utxo_prefix,trx_data)
							is_done = true
							return

							}
						//增加关系表内容
						addr_utxo_prefix := cal_addr_utxo_prefix(*data.(pro.UTXOObject).Address,vin_txid.(string),int(vout_data))
						add_addr_trx_releation(trx_counts,*data.(pro.UTXOObject).Address)

						//address_trx_db.Insert(tmp_map).Exec(session)
						//one_vin_map["value"] = data["value"]
						//one_vin_map["address"] = data["address"]
						//删除utxo记录
						spent_utxo(utxo_prefix,addr_utxo_prefix)
						break
						}
					}
				//vins_map = append(vins_map, one_vin_map)
			}
			//trx_map_obj["vins"] = vins_map

			vouts := one_trx["vout"].([]interface{})

			for _,vout_data := range vouts{
				vout := vout_data.(map[string]interface{})
				script := vout["scriptPubKey"].(map[string]interface{})
				value,exist := vout["value"]
				var value_data float64
				if exist{
					value_data,_ = value.(json.Number).Float64()
				}
				n,exist := vout["n"]
				var n_data int64
				if exist{
					n_data,_ = n.(json.Number).Int64()
				}
				//cal vout address
				affect_address,script_pubkey:= get_vout_address(script)
				//新增关系记录
				add_addr_trx_releation(trx_counts,affect_address)

				//插入utxo
				utxo_prefix := cal_utxo_prefix(trx_Id,int(n_data))
				addr_utxo_prefix := cal_addr_utxo_prefix(affect_address,trx_Id,int(n_data))
				add_utxo(utxo_prefix,value_data,affect_address,addr_utxo_prefix,script_pubkey)
			}
			//trx_map_obj["vouts"] = vouts_map
			//write_trx_data = append(write_trx_data,trx_map_obj)
			trx_counts ++
		}
		if last_height<tmp_height{
		last_height = tmp_height
		}
		if int32(interval) == 1{
			flush_db()
		} else if change_weight>int32(interval){
			flush_db()

			change_weight = 0
		}
	}
	fmt.Println("handle_block is done")

}

func main(){
	runtime.GOMAXPROCS(runtime.NumCPU())
	//wg.Add(runtime.NumCPU()+4)
	wg.Add(2)
	total_size =0
	total_trx_size =0
	exit_count =0
	flush_count =0
	utxo_cache = make(map[string]interface{},0)
	addr_utxo_cache = make(map[string]interface{},0)
	trxId_cache	= make(	[][]byte,0,4000000)
	utxo_spent_cache = make([]string,0,2000000)
	addr_utxo_spent_cache = make([]string,0,2000000)
	write_address_trx_data =  make(map[string]interface{},0)
	is_done = false


	paramChainType := flag.String("ChainType","BTC_TEST","start which chain collect")
	flag.Parse()

	if *paramChainType!=""{
		fmt.Println("select chain ",*paramChainType)
		ChainType = *paramChainType
		_,exist := config.RpcServerConfig.SupportCoinType[ChainType]
		if !exist{
			fmt.Println("not Support chain type",ChainType)
			return
		}
	}


	//检测推出信号
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, os.Interrupt, os.Kill,  syscall.SIGINT, syscall.SIGTERM)

	go func (){
		sig:=<-sigs
		fmt.Println("exit code get",sig)
		is_done = true
	}()
	var err error
	address_trx_db,err = leveldb.OpenFile(config.RpcServerConfig.DbPathConfig[ChainType]+"address_trx_db",nil)
	if err != nil { panic(err) }

	unspent_utxo_db,err =leveldb.OpenFile(config.RpcServerConfig.DbPathConfig[ChainType]+"unspent_utxo_db",nil)
	if err != nil { panic(err) }
	addr_unspent_utxo_db,err =leveldb.OpenFile(config.RpcServerConfig.DbPathConfig[ChainType]+"addr_unspent_utxo_db",nil)
	if err != nil { panic(err) }
	config_db,err =leveldb.OpenFile(config.RpcServerConfig.DbPathConfig[ChainType]+"config_db",nil)
	if err != nil { panic(err) }

	//init fs
	os.Mkdir(config.RpcServerConfig.DbPathConfig[ChainType]+"meta",os.ModeDir)
	trxId_fs = util.LogicalFile{}
	trxId_fs.Init(config.RpcServerConfig.DbPathConfig[ChainType]+"trxdata",2,32000000)

	tmp_height,err:=config_db.Get([]byte("height"),nil)
	fmt.Println(tmp_height)
	if err != nil {
		tmp_height = []byte("0")
	}
	height,_ :=strconv.Atoi(string(tmp_height))
	old_chan_height=int32(height)
	last_height = height

	tmp_count,err:=config_db.Get([]byte("trx_counts"),nil)
	if err != nil {
		tmp_count = []byte("0")
	}
	mid_count,_ := strconv.Atoi(string(tmp_count))
	trx_counts = int32(mid_count)
	tmp_flush_count,err:=config_db.Get([]byte("flush_count"),nil)
	if err != nil {
		tmp_flush_count = []byte("0")
	}
	flush_count,_ =strconv.Atoi(string(tmp_flush_count))

	//统计代码
	//agent := stackimpact.Start(stackimpact.Options{
	//	AgentKey: "5c2e1b71892defcc6dcdfc1c8e7b716078232676",
	//	AppName: "eth_collect",
	//})

	//获取链上块高度
	link_client := util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[ChainType],
		Port:config.RpcServerConfig.SourceDataPort[ChainType],
		User:config.RpcServerConfig.SourceDataUserName[ChainType],
		PassWord:config.RpcServerConfig.SourceDataPassword[ChainType],
	}
	//vin := &pro.TrxObject_VIN{}
	param := make([]interface{},0)

	var count int
	for ;;{
	json_data := link_client.SafeLinkHttpFunc(config.RpcServerConfig.GetInfoFunctionName[ChainType],&param ,config.RpcServerConfig.IsTls[ChainType])
	count,_ := json_data.Get("result").Get("blocks").Int()
	count = count - config.RpcServerConfig.SafeBlock[ChainType]
		if count >= height{
			break
		}
		fmt.Println("invalid chain height",count)
	}


	fmt.Println("chain height",count)
	global_start_height  = height
	blockdata_chan := make(chan simplejson.Json,40)
	height_chan := make(chan int,40)
	go collect_block(height_chan,blockdata_chan,true)
	//go collect_block(height_chan,blockdata_chan)
	//go collect_block(height_chan,blockdata_chan)
	//go collect_block(height_chan,blockdata_chan)
	go handle_block(blockdata_chan,50000000)
	//for i:=0;i<1;i++{
	//	go handle_block(blockdata_chan)
	//}

	for i:=height+1;i<count&&!is_done;i++{
		height_chan <- i
	}

	for i:=0;i<1;i++{
		height_chan <- -1
	}

	wg.Wait()
	fmt.Println("fast sync end")
	//写db
	flush_db()
	write_address_trx_data =  make(map[string]interface{},0)

	//退出快速同步进入持续同步流程

	if !is_done{

		wg.Add(2)
		go collect_block(height_chan,blockdata_chan,false)
		go handle_block(blockdata_chan,1)

		go startRpcServer()
		old_count := count
		last_height = old_count-1
		for ;!is_done;{

			param := make([]interface{},0)
			json_data := link_client.SafeLinkHttpFunc(config.RpcServerConfig.GetInfoFunctionName[ChainType],&param ,config.RpcServerConfig.IsTls[ChainType])
			//fmt.Println(json_data)
			count,_ := json_data.Get("result").Get("blocks").Int()
			count = count - config.RpcServerConfig.SafeBlock[ChainType]
			if old_count <count{
				fmt.Println("current height:",old_count,"target height",count,"time",time.Now())
				for i:=old_count;i<count;i++{
					height_chan <- i
				}
				old_count = count
			}else{
				time.Sleep(5*time.Second)
			}
		}
		height_chan <- -1
		wg.Wait()
		fmt.Println("low sync end")
	}

	//compress_db()
	address_trx_db.Close()
	unspent_utxo_db.Close()
	addr_unspent_utxo_db.Close()
	config_db.Close()




}