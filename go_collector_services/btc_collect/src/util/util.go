package util

import (
	"encoding/binary"
	"strconv"
	"strings"
)

func Int64ToBytes(i int64) []byte {
	var buf = make([]byte, 8)
	binary.BigEndian.PutUint64(buf, uint64(i))
	return buf
}

func BytesToInt64(buf []byte) int64 {
	return int64(binary.BigEndian.Uint64(buf))
}


func Int32ToBytes(i int32) []byte {
	var buf = make([]byte, 4)
	binary.BigEndian.PutUint32(buf, uint32(i))
	return buf
}

func BytesToInt32(buf []byte) int32 {
	return int32(binary.BigEndian.Uint32(buf))
}
func SplitAddrUtxoPrefix(prefix string)(string,int){
	 start := strings.Index(prefix[20:],"O")
	 end := strings.Index(prefix[20:],"I")
	 txid := prefix[start+21:end+20]
	 vout_str := prefix[end+21:]
	 vout,_ := strconv.ParseInt(vout_str,10,32)
	 return txid,int(vout)
}
func SplitAddrUtxoPrefixForBtm(prefix string)(string){
	start := strings.Index(prefix,"O")
	utxoid := prefix[start+1:]
	return utxoid
}
func SplitBlockHeightTrxId(args string)(int,string) {
	argList := strings.Split(args,"|")
	if len(argList) != 2 {
		return -1, ""
	}
	blockHeight, err := strconv.Atoi(argList[0])
	if err != nil {
		return -1, ""
	}
	trxId := argList[1]
	return blockHeight,trxId
}
