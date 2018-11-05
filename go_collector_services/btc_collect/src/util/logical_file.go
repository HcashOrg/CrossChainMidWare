package util

import (
	"bytes"
	"os"
	"fmt"
	"strconv"
)

type LogicalFile struct {
	StrFmt string
	FileSize int
}

func (this *LogicalFile) ReadData(start int,size int)[]byte{
	res_buf :=bytes.Buffer{}
	for ;size>0;{
		file,err :=this.OpenFile(start,false)
		if err!=nil{
			break
		}
		tmp_read_data:=make([]byte,size)
		count,_:=file.Read(tmp_read_data)
		res_buf.Write(tmp_read_data[:count])
		start += count
		if size>0{
			size -= count
		}
		file.Close()
	}
	return res_buf.Bytes()
}

func (this *LogicalFile) Init(prefix string,digits int,size int){
	this.StrFmt = prefix+"%0"+strconv.Itoa(digits)+"d"
	this.FileSize = size
}



func Min(x, y int) int {
	if x < y {
		return x
	}
	return y
}


func (this *LogicalFile) WriteData(start int,data []byte){
	for ;len(data)>0;{
		size := Min(len(data),this.FileSize-(start%this.FileSize))
		file,err :=this.OpenFile(start,true)
		if err!=nil{
			fmt.Println(err.Error())
			return
		}
		if size == len(data){
			file.Write(data)
		}else{
		file.Write(data[:size])
		}
		data = data[size:]
		start+=size
		file.Close()
	}
}



func open_system_file(filename string,create bool)(*os.File,error){
	file,err:=os.OpenFile(filename,os.O_RDWR,0666)
	if create && err!=nil && os.IsNotExist(err){

		file,err = os.Create(filename)
	}
	return file,err
}

func divmod(amount int,interval int)(int,int){
	count:= amount/interval
	offset:= amount%interval
	fmt.Println(amount,interval,count,offset)
	return count,offset
}

func  (this *LogicalFile)  OpenFile(start int,create bool) (*os.File,error){
	file_num,offset := divmod(start,this.FileSize)
	filename := fmt.Sprintf(this.StrFmt,file_num)
	file,err := open_system_file(filename,create)
	if err==nil{
		file.Seek(int64(offset),0)
	}else{
		fmt.Println("openfile err",err.Error())
	}

	return file,err
}




