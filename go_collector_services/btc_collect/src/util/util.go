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
	 start := strings.Index(prefix,"O")
	 end := strings.Index(prefix,"I")
	 txid := prefix[start+1:end]
	 vout_str := prefix[end+1:]
	 vout,_ := strconv.ParseInt(vout_str,10,32)
	 return txid,int(vout)
}