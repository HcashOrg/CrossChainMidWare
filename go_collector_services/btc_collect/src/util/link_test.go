package util

import (
	"testing"
	"fmt"
)

func TestLinkClient_HttpRequestForBtm(t *testing.T) {
	var linkClient LinkClient
	linkClient.IP = "127.0.0.1"
	linkClient.Port = "9888"
	linkClient.User = ""
	linkClient.PassWord = ""

	param := make(map[string]interface{})
	param["block_height"] = 1
	res := linkClient.LinkHttpFuncForBTM("get-block", &param)
	if res!= nil {
		fmt.Println(res.Get("result"))
	}

	res = linkClient.LinkHttpFuncForBTM("get-block1", &param)
	if res!= nil {
		fmt.Println(res.Get("error"))
	}
}

func TestLinkClient_SafeHttpRequestForBtm(t *testing.T) {
	var linkClient LinkClient
	linkClient.IP = "127.0.0.1"
	linkClient.Port = "9888"
	linkClient.User = ""
	linkClient.PassWord = ""

	param := make(map[string]interface{})
	param["block_height"] = 1
	res := linkClient.SafeLinkHttpFuncForBTM("get-block", &param)
	if res!= nil {
		fmt.Println(res.Get("result"))
	}

	res = linkClient.LinkHttpFuncForBTM("get-block1", &param)
	if res!= nil {
		fmt.Println(res.Get("error"))
	}
}