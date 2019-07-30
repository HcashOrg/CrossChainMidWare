package main

import (
	_ "github.com/golang/protobuf/proto"
	_ "io/ioutil"
	_ "os"
	"fmt"
	_ "strings"
	_ "net/http"
	"util"
	"strconv"
	"runtime"
	"sync"
	"github.com/bitly/go-simplejson"
	"time"
	"sync/atomic"
	"strings"
	_ "os"
	_ "runtime/pprof"
	"flag"
	"os"
	"os/signal"
	"syscall"
	"config"
	"database/sql"
	_ "github.com/lib/pq"
)

var(
	total_size int64
	total_trx_size int64
	global_start_height int
	exit_count int32
	wg sync.WaitGroup

	session *sql.DB

)
var collect_threads = 3
var handle_threads = runtime.NumCPU()+1
var ChainType = "ETH"
var WatchAddressList map[string]string

func get_int(int_str string)(int64){
	if strings.HasPrefix(int_str,"0x"){
		value,_ := strconv.ParseInt(int_str[2:],16,32)
		return value
	}else{
		value,_ := strconv.ParseInt(int_str,10,32)
		return value
	}
}

func collect_block(height_chan chan int,blockdata_chan chan simplejson.Json){
	defer wg.Done()
	link_client := util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[ChainType],
		Port:config.RpcServerConfig.SourceDataPort[ChainType],
		User:"",
		PassWord:"",
	}
	//vin := &pro.TrxObject_VIN{}
	//trx_object := pro.TrxObject{}
	back_time := time.Now()



	for ;;{
		param := make([]interface{},0,2)
		once_height := <- height_chan
		if once_height == -1{
			fmt.Println("collect exit")
			atomic.AddInt32(&exit_count,int32(1))
			json_data,_ :=simplejson.NewJson([]byte("{\"result\":\"exit\"}"))
			blockdata_chan <- *json_data
			return
		}
		param = append(param,"0x"+strconv.FormatInt(int64(once_height), 16))
		param = append(param,"true")
		blockdata := link_client.SafeLinkHttpFunc("eth_getBlockByNumber",&param )
		if once_height%1000 ==0{
			fmt.Println("height",once_height,"chan size",len(blockdata_chan))
		}

		blockdata_chan <- *blockdata
		res_size,_ := blockdata.Get("result").Get("size").String()

		size := get_int(res_size)
		atomic.AddInt64(&total_size,int64(size))
		tx_array,_ := blockdata.Get("result").Get("transactions").Array()
		atomic.AddInt64(&total_trx_size,int64(len(tx_array)))
		if once_height % 1000 == 0{
			res_tmp_height,_ :=blockdata.Get("result").Get("number").String()
			tmp_height,_ := strconv.ParseInt(res_tmp_height[2:],16,32)
			fmt.Println("block height",tmp_height)
			fmt.Println( "total size: ", total_size / 1024 / 1024, " MB")
			fmt.Println( "total trx count: ", total_trx_size)
			fmt.Println( "now :", time.Now() )
			fmt.Println( "cost time : ", time.Now().Sub(back_time))
			fmt.Println( "blocks per sec : ", float32(once_height-global_start_height) / float32(time.Now().Sub(back_time).Seconds()))
			fmt.Println( "trxs per sec: ", float32(total_trx_size) / float32(time.Now().Sub(back_time).Seconds()))
		}


	}
}


func flush_db_nosync(trx_cache []interface{},erc20_address_trx_cache []interface{}){
	//bak_time := time.Now()
	//session:=get_session()
	if len(trx_cache)>0{
		util.InsertManyTrxData(session,trx_cache)
	}

	if len(erc20_address_trx_cache)>0{
		util.InsertManyErc20TrxData(session,erc20_address_trx_cache)
	}
	//put_session(session)
	//fmt.Println("flush trx data ",len(trx_cache)," erc20 data ",len(erc20_address_trx_cache)," cost time:",time.Now().Sub(bak_time).Seconds())
}

func get_watch_address_list() bool{
	var err error
	WatchAddressList,err = util.GetRelationAddress(session,ChainType)
	if err!=nil{
		return false
	}
	return true
}


func handle_block(blockdata_chan chan simplejson.Json,interval int64){
	defer wg.Done()
	link_client := util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[ChainType],
		Port:config.RpcServerConfig.SourceDataPort[ChainType],
		User:"",
		PassWord:"",
	}

	for ;;{
		blockchain_data := <- blockdata_chan


		trx_cache := make([]interface{},0,1200)
		erc20_address_trx_cache:=make([]interface{},0,1000)
		//address_batch := &leveldb.Batch{}
		//erc20_address_batch := &leveldb.Batch{}
		exit_code,err :=blockchain_data.Get("result").String()
		if err == nil{

			if exit_code == "exit"{
				for exit_count<int32(collect_threads){
					time.Sleep(1*time.Second)
				}
				if exit_count < int32(handle_threads) {
					atomic.AddInt32(&exit_count,int32(1))
					json_data,_ :=simplejson.NewJson([]byte("{\"result\":\"exit\"}"))
					blockdata_chan <- *json_data
				}
				flush_db_nosync(trx_cache,erc20_address_trx_cache)



				fmt.Println("check exit")

				return
			}
		}
		tx_datas,_ := blockchain_data.Get("result").Get("transactions").Array()
		tmp_height_str,_ :=blockchain_data.Get("result").Get("number").String()
		tmp_height,_ := strconv.ParseInt(tmp_height_str[2:],16,32)
		if tmp_height%interval ==0{
			get_watch_address_list()
		}
		for _,trx_data := range tx_datas{
			trx_map_obj :=make(map[string]interface{})
			var trx_simple_data map[string]interface {}
			trx_simple_data = trx_data.(map[string]interface{})
			txid:= trx_simple_data["hash"].(string)

			//trx_object := &pro.TrxObject{}
			trx_map_obj["id"] = txid
			trx_map_obj["blockNumber"] = tmp_height
			to_str,exist := trx_simple_data["to"]
			trx_map_obj["to"] = to_str
			//logs

			//from
			trx_map_obj["from"] = trx_simple_data["from"]
			if trx_simple_data["input"].(string) == "0x" && exist && trx_simple_data["to"]!=nil {
				_,exist := WatchAddressList[trx_simple_data["to"].(string)]
				if exist{
					param := make([]interface{},0,20)
					param = append(param,txid)
					trxReceiptData,_ := link_client.SafeLinkHttpFunc("eth_getTransactionReceipt",&param ).Get("result").Map()
					logs_data :=trxReceiptData["logs"]
					if len(logs_data.([]interface{}))==0{
						continue
					}
				}
			}

			if trx_simple_data["input"].(string) != "0x"{
				//logs
				//if strings.HasPrefix(trx_simple_data["input"].(string),"0xa9059cbb") ||strings.HasPrefix(trx_simple_data["input"].(string),"0x23b872dd")||
				//	strings.HasPrefix(trx_simple_data["input"].(string),"0xa9059cbb"){
				if true{
					param := make([]interface{},0,20)
					param = append(param,txid)
					trxReceiptData,_ := link_client.SafeLinkHttpFunc("eth_getTransactionReceipt",&param ).Get("result").Map()
					logs_data :=trxReceiptData["logs"]
					for _,data := range logs_data.([]interface{}){
						var log_json_data map[string]interface{}
						log_json_data = data.(map[string]interface{})
						topics_ori,exist :=log_json_data["topics"]
						topics := topics_ori.([]interface{})
						if !exist {
							continue
						}else{
							if len(topics)>2{
								if topics[0].(string) == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"{
									tmp_map :=make(map[string]interface{})
									tmp_map["blockNumber"] =tmp_height
									tmp_map["from"] = "0x"+topics[1].(string)[26:]
									tmp_map["to"] = "0x"+topics[2].(string)[26:]
									tmp_value:=strings.TrimLeft(log_json_data["data"].(string)[2:],"0")
									tmp_map["value"] = "0x"+tmp_value
									tmp_map["txid"] = txid
									tmp_map["contractAddress"] = trx_map_obj["to"]
									logindex,_ := strconv.ParseInt(log_json_data["logIndex"].(string)[2:],16,32)
									tmp_map["logIndex"] = logindex
									erc20_address_trx_cache = append(erc20_address_trx_cache, tmp_map)
								}
							}
						}
					}
				}
			}
			trx_cache = append(trx_cache, trx_map_obj)
		}
		flush_db_nosync(trx_cache,erc20_address_trx_cache)

		if tmp_height%interval ==0{

			//session:=get_session()
			util.SetConfigHeight(session,int(tmp_height))
			//put_session(session)
		}


	}

}






//
//func get_session() sql.DB{
//	tmp_session:=<- session_chan
//	return tmp_session
//}
//func put_session(session sql.DB){
//	session_chan<-session
//}

func main(){
	runtime.GOMAXPROCS(runtime.NumCPU())
	//
	//f,_ := os. Create("cpu.prof")
	//
	//pprof.StartCPUProfile(f)
	//defer pprof.StopCPUProfile()


	wg.Add(handle_threads+collect_threads)


	//session_chan = make(chan sql.DB,runtime.NumCPU())
	//for i:=0;i<runtime.NumCPU();i++{
	//	session:=util.GetDB(ChainType)
	//	session_chan <-*session
	//}

	paramChainType := flag.String("ChainType","ETH","start which chain collect")
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
	is_done:=false
	go func (){
		sig:=<-sigs
		fmt.Println("exit code get",sig)
		fmt.Println("please wait for quit",sig)
		is_done = true
	}()

	total_size =0
	total_trx_size =0
	exit_count =0
	start_height := 0
	//session:=get_session()
	session=util.GetDB(ChainType)

	start_height = util.GetConfigHeight(session)

	//put_session(session)
	fmt.Println(start_height)
	//if err != nil {
	//	start_height = []byte("0")
	//}
	height :=start_height
	//获取链上块高度
	link_client := util.LinkClient{
		IP:config.RpcServerConfig.SourceDataHost[ChainType],
		Port:config.RpcServerConfig.SourceDataPort[ChainType],
		User:"",
		PassWord:"",
	}
	//vin := &pro.TrxObject_VIN{}
	param := make([]interface{},0)

	var count int64
	for ;;{
        json_data := link_client.SafeLinkHttpFunc("eth_blockNumber",&param )
        fmt.Println("json_data",json_data)
        res_count,_ := json_data.Get("result").String()
        fmt.Println(height)
        res_count = res_count[2:]
		count, _ = strconv.ParseInt(res_count, 16, 32)
        count = count - int64(config.RpcServerConfig.SafeBlock[ChainType])
        fmt.Println(count)
		if count>=int64(height){
			break
		}
		time.Sleep(5 * time.Second)

	}



	global_start_height  = height
	blockdata_chan := make(chan simplejson.Json,40)
	height_chan := make(chan int,40)
	for i:=0;i<collect_threads;i++{
		go collect_block(height_chan,blockdata_chan)
	}
	//for i:=0;i<runtime.NumCPU();i++{
	//	go handle_block(blockdata_chan,trx_db,address_trx_db)
	//}
	//
	//
	for i:=0;i<handle_threads;i++{
		go handle_block(blockdata_chan,1000)
	}

	//agent := stackimpact.Start(stackimpact.Options{
	//	AgentKey: "5c2e1b71892defcc6dcdfc1c8e7b716078232676",
	//	AppName: "eth_collect",
	//})
	//
	//http.HandleFunc(agent.ProfileHandlerFunc("/", handler))
	//go http.ListenAndServe(":18080", nil)

	for i:=height;i<int(count)&&!is_done;i++{
		height_chan <- i
	}
	for i:=0;i<collect_threads;i++{
		height_chan <- -1
	}
	wg.Wait()
	fmt.Println("end")

	if !is_done{
		wg.Add(2)
		for len(blockdata_chan)>0{
			<- blockdata_chan
		}
		go collect_block(height_chan,blockdata_chan)


		go handle_block(blockdata_chan,1)

		go startRpcServer()
		old_count := int(count)
		for ;!is_done;{

			param := make([]interface{},0)
			json_data := link_client.SafeLinkHttpFunc("eth_blockNumber",&param )
			res_count,_ := json_data.Get("result").String()
			count64, _ := strconv.ParseInt(res_count[2:], 16, 32)
			count := int(count64) - config.RpcServerConfig.SafeBlock[ChainType]
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


}