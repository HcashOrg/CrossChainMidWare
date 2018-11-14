package util

import (
	"fmt"
	"encoding/json"
	"strings"
	"net/http"
	"io/ioutil"
	"encoding/base64"
	"github.com/bitly/go-simplejson"
	"reflect"
	"strconv"
	"time"
)

type LinkClient struct{
	IP string
	Port string
	User string
	PassWord string
}
func NewBtsClient(ip,port,user,password string)*LinkClient{
	return &LinkClient{ip,port,user,password}
}

type HttpRequest struct{
	Id string `json:"id"`
	Method string `json:"method"`
	Params []interface{} `json:"params"`
}

var substr = []string{"key_approvals_to_add","true","false"}


func notUseQuote(value string) bool{
	contain := false
	for _,subStr := range substr{
		if strings.Contains(value,subStr){
			contain = true
			break
		}
	}
	return contain
}
func turnInterface(ina *[]interface{})string{
	message := "["
	for _,value := range *ina{
		if reflect.TypeOf(value) == reflect.TypeOf(1){
			if message == "[" {
				message = message + strconv.Itoa(value.(int))
			}else{
				message = message +","+ strconv.Itoa(value.(int))
			}
		}else if value == "true"{
			if message == "[" {
				message = message + value.(string)
			}else{
				message = message +","+ value.(string)
			}
		}else if reflect.TypeOf(value) == reflect.TypeOf(make(map[string]string)){
			bak_str:="{"
			for k,v := range value.(map[string]string){
				bak_str += "\""+k+"\":\""+v+"\","
			}
			bak_str = bak_str[:len(bak_str)-1]
			bak_str+="}"
			if message == "["{

				message = message +bak_str
			}else{
				message = message + "," +bak_str
			}
		}else {
			if message == "["{
				message = message + "\"" +value.(string)+"\""
			}else{
				message = message + ",\"" +value.(string)+"\""
			}
		}

	}
	message = message + "]"
	return message
}


func (client *LinkClient)SafeLinkHttpFunc(function string,params *[]interface{})(*simplejson.Json) {
	sleepInterval :=[]int{5,10,20,30,40,60,120,240,480,960,1920,3840}
	index :=0
	for;;{
		return_value:=client.LinkHttpFunc(function,params)
		if return_value != nil{
			_,exist:=return_value.CheckGet("result")
			if exist{
				return return_value
			}
		}
		{

			if index>=12{
				fmt.Println("http request is error,please wait to retry,current sleep time is ",time.Second*time.Duration(sleepInterval[11]),time.Now())
				time.Sleep(time.Second*time.Duration(sleepInterval[11]))
			}else{
				fmt.Println("http request is error,please wait to retry,current sleep time is ",time.Second*time.Duration(sleepInterval[index]),time.Now())
				time.Sleep(time.Second*time.Duration(sleepInterval[index]))
			}
		}
		index++
	}
}


func (client * LinkClient)LinkHttpFunc(function string,params *[]interface{})(*simplejson.Json) {
	strParams := turnInterface(params)
	transport := http.Transport{
		DisableKeepAlives:              true,
	}
	clienta := http.Client{Transport: &transport,}

	message :="{ \"id\": 1, \"method\": \""+function+"\", \"params\": "+strParams+"}"
	payload := strings.NewReader(message)
	//fmt.Println(payload)
	req, err := http.NewRequest("POST", client.IP+":"+client.Port, payload)

	if err != nil{
		fmt.Println("x")
		fmt.Println(err.Error())
		return nil
	}
	req.Header.Add("content-type", "application/json")
	if client.User != "" && client.PassWord != ""{
		encodeUser := base64.StdEncoding.EncodeToString([]byte((*client).User+":"+(*client).PassWord))
		req.Header.Add("authorization", "Basic "+ encodeUser)
	}
	res, err := clienta.Do(req)
	if err != nil{
		fmt.Println("1")
		fmt.Println(err.Error())
		return nil
	}

	defer res.Body.Close()
	body, err := ioutil.ReadAll(res.Body)
	if res.StatusCode!=200 {
		fmt.Println("error status code " + strconv.Itoa(res.StatusCode))
		return nil
	}
	if err != nil{
		fmt.Println("2")
		fmt.Println(err.Error())
		return nil
	}
	js,err:= simplejson.NewJson(body)
	if err != nil{
		fmt.Println("3")
		fmt.Println(err.Error())
		return nil
	}
	//fmt.Println(js)
	return js
}
func (client * LinkClient)HttpRpcFunction(function string,param *[]interface{})string{
	url:="http://"+(*client).IP+":"+(*client).Port
	a := HttpRequest{"1",function,*param}
	fmt.Println(a)
	b,_:= json.Marshal(a)
	payload := strings.NewReader(string(b))
	encodeUser := base64.StdEncoding.EncodeToString([]byte((*client).User+":"+(*client).PassWord))
	req, _ := http.NewRequest("POST", url, payload)
	req.Header.Add("content-type", "application/json")
	req.Header.Add("authorization", "Basic "+ encodeUser)
	req.Header.Add("cache-control", "no-cache")
	res, err := http.DefaultClient.Do(req)
	if err != nil{
		fmt.Println(err.Error())
		return ""
	}
	defer res.Body.Close()
	body, err := ioutil.ReadAll(res.Body)
	if err != nil{
		fmt.Println(err.Error())
		return ""
	}
	tempparam := make(map[string]interface{})
	json.Unmarshal([]byte(string(body)),&tempparam)
	fmt.Println(string(body))
	return string(body)
}