package util

import (
	"database/sql"
	_ "github.com/lib/pq"
	"fmt"
	"config"
	"github.com/axgle/mahonia"
)

func GetDB(cointype string) *sql.DB {

	config := config.RpcServerConfig.PosgresqlConfig[cointype].(map[string]string)


	psqlInfo := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable", config["host"], config["port"], config["user"], config["password"],config["dbname"])
	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		fmt.Printf(err.Error())
		return nil
	}
	err = db.Ping()
	if err != nil {
		fmt.Printf(err.Error())
		return nil
	}
	fmt.Println("successfull connected!")
	db.SetMaxOpenConns(9)
	return db
}


func GetConfigHeight(db *sql.DB) int{
	sqlStatement := `SELECT * FROM public.config;`
	row := db.QueryRow(sqlStatement)
	var height int
	err := row.Scan(&height)
	switch err {
	case sql.ErrNoRows:
		sqlStatement := `INSERT INTO public.config(trx_height) VALUES ($1);`
		_,err=db.Exec(sqlStatement,0)
		return 0
	case nil:
		return height
	default:
		panic(err)
	}
}

func ConvertToString(src string, srcCode string, tagCode string) string {
	srcCoder := mahonia.NewDecoder(srcCode)
	srcResult := srcCoder.ConvertString(src)
	tagCoder := mahonia.NewDecoder(tagCode)
	_, cdata, _ := tagCoder.Translate([]byte(srcResult), true)
	result := string(cdata)
	return result
}

func SetConfigHeight(db *sql.DB,new_height int){

	sqlStatement := `UPDATE public.config SET trx_height=$1;`
	_,err:=db.Exec(sqlStatement,new_height)
	if err!=nil{
		err_str := err.Error()
		err_str  = ConvertToString(err_str, "gbk", "utf-8")
		fmt.Println("SetConfigHeight",err_str)
		panic(err)
	}
}

func InsertManyTrxData(db *sql.DB,datas []interface{}){
	insert,err := db.Prepare(`INSERT INTO public.trx_data(trxid,"from","to",blocknumber) VALUES ($1,$2,$3,$4)`)
	if err != nil {
		fmt.Println(err)
		return
	}
	begin,err:=db.Begin()

	for _,data := range datas{
		one_data := data.(map[string]interface{})
		_,err = begin.Stmt(insert).Exec(one_data["id"],one_data["from"],one_data["to"],one_data["blockNumber"])
		if err != nil {
			fmt.Println(err)
			begin.Rollback()
			return
		}
	}

	err = begin.Commit()
	if err != nil {
		fmt.Println(err)
		return
	}
}

func InsertOneTrxData(db sql.DB,data map[string]interface{}){
	sqlStatement := `INSERT INTO public.trx_data(trxid,"from","to",blocknumber) VALUES ($1,$2,$3,$4);`
	_,err := db.Exec(sqlStatement,data["id"],data["from"],data["to"],data["blockNumber"])
	if err!=nil{
		fmt.Println("InsertOneTrxData",err.Error())
	}
}

func InsertOneErc20TrxData(db sql.DB,data map[string]interface{}){
	sqlStatement := `INSERT INTO public.erc20_address_relation(txid,"from","to",blocknumber,contractAddress,"value","logIndex") VALUES ($1,$2,$3,$4,$5,$6,$7);`
	_,err := db.Exec(sqlStatement,data["id"],data["from"],data["to"],data["blockNumber"],data["contractAddress"],data["value"],data["logIndex"])
	if err!=nil{
		fmt.Println("InsertOneTrxData",err.Error())
	}
}

func InsertManyErc20TrxData(db *sql.DB,datas []interface{}){
	insert,err := db.Prepare(`INSERT INTO public.erc20_address_relation(txid,"from","to",blocknumber,contractAddress,"value","logIndex") VALUES ($1,$2,$3,$4,$5,$6,$7)`)
	if err != nil {
		fmt.Println(err)
		return
	}
	begin,err:=db.Begin()

	for _,data := range datas{
		one_data := data.(map[string]interface{})
		_,err = begin.Stmt(insert).Exec(one_data["txid"],one_data["from"],one_data["to"],one_data["blockNumber"],one_data["contractAddress"],one_data["value"],one_data["logIndex"])
		if err != nil {
			fmt.Println(err)
			begin.Rollback()
			return
		}
	}

	err = begin.Commit()
	if err != nil {
		fmt.Println(err)
		return
	}
}

func GetErc20TransactionById(db *sql.DB,trxid string) []map[string]interface{}{
	sqlStatement := `SELECT * FROM public.erc20_address_relation where txid=$1;`
	rows,err := db.Query(sqlStatement,trxid)
	if err!=nil{
		return make([]map[string]interface{},0)
	}
	res_datas := make([]map[string]interface{},0)



	for rows.Next(){
		var height int
		var contractaddress string
		var from string
		var to string
		var txid string
		var value string
		var logIndex int
		err := rows.Scan(&height,&contractaddress,&from,&to,&txid,&value,&logIndex)
		switch err {
		case sql.ErrNoRows:
			return make([]map[string]interface{},0)
		case nil:
			res_data := make( map[string]interface{})
			res_data["blockNumber"] = height
			res_data["contractAddress"] = contractaddress
			res_data["from"] = from
			res_data["to"] = to
			res_data["txid"] = txid
			res_data["value"] = value
			res_data["logIndex"] = logIndex
			res_datas = append(res_datas,res_data)
		default:
			panic(err)
		}
		if err!=nil{
			fmt.Println(err.Error())

			return res_datas
		}
	}
	return res_datas








}


func InsertRelationAddress(db *sql.DB,cointype,address string ,isErc20 bool)error{
	sqlStatement := `SELECT count(1) FROM public.relation_address where "CoinType"=$1 and "Address"=$2 and "Erc20Type"=$3;`
	row := db.QueryRow(sqlStatement,cointype,address,isErc20)
	var count int
	row.Scan(&count)
	if count == 0{
		sqlStatement = `INSERT INTO public.relation_address("CoinType","Address","Erc20Type") VALUES ($1,$2,$3);`
		_,err := db.Exec(sqlStatement,cointype,address,isErc20)
		return err
	}
	return nil

}


func GetRelationAddress(db *sql.DB,cointype string) (map[string]string,error){
	sqlStatement := `SELECT DISTINCT "Address" FROM public.relation_address where "CoinType"=$1;`
	rows,err := db.Query(sqlStatement,cointype)
	defer rows.Close()
	if err!=nil{
		return make(map[string]string),err
	}
	res_datas := make(map[string]string)

	for rows.Next(){
		var one_address string
		err = rows.Scan(&one_address)
		if err!=nil{
			fmt.Println(err.Error())
			return res_datas,err
		}
		res_datas[one_address] = ""
	}
	return res_datas,nil

}

func ConvertMapToArray(input map[string]string) []string{
	res_data := make([]string,len(input))
	index := 0
	for k,_ :=range input{
		res_data[index] = k
		index++
	}
	return res_data
}

func GetNormalHistory(db * sql.DB,blocknumber int) ([]string,error){
	sqlStatement := `select trxid from trx_data where blocknumber=$1 and ("from" in (select "Address" from relation_address where "Erc20Type"=false)  or "to" in (select "Address" from relation_address where "Erc20Type"=false))`
	rows,err := db.Query(sqlStatement,blocknumber)
	defer rows.Close()
	if err!=nil{
		return make([]string,0),err
	}
	res_datas := make(map[string]string)

	for rows.Next(){
		var one_trx_id string
		err = rows.Scan(&one_trx_id)
		if err!=nil{
			fmt.Println(err.Error())

			return ConvertMapToArray(res_datas),nil
		}
		res_datas[one_trx_id] = ""
	}
	return ConvertMapToArray(res_datas),nil

}
func GetTrxHistoryByAddress(db * sql.DB,address string,start_blocknumber int,end_blocknumber int) ([]string,error){
	sqlStatement := `select trxid from trx_data where blocknumber BETWEEN $1 and $2 and ("from" = $3  or "to" = $3)`
	rows,err := db.Query(sqlStatement,start_blocknumber,end_blocknumber,address)
	defer rows.Close()
	if err!=nil{
		return make([]string,0),err
	}
	res_datas := make(map[string]string)
	for rows.Next(){
		var one_trx_id string
		err = rows.Scan(&one_trx_id)
		if err!=nil{
			fmt.Println(err.Error())

			return ConvertMapToArray(res_datas),nil
		}
		res_datas[one_trx_id] = ""
	}
	return ConvertMapToArray(res_datas),nil

}



func GetNormalHistoryRange(db * sql.DB,start_blocknumber,end_blocknumber int) ([]string,error){
	sqlStatement := `select trxid from trx_data where blocknumber BETWEEN $1 and $2 and ("from" in (select "Address" from relation_address where "Erc20Type"=false)  or "to" in (select "Address" from relation_address where "Erc20Type"=false))`
	rows,err := db.Query(sqlStatement,start_blocknumber,end_blocknumber)
	defer rows.Close()
	if err!=nil{
		return make([]string,0),err
	}
	res_datas := make(map[string]string)
	for rows.Next(){
		var one_trx_id string
		err = rows.Scan(&one_trx_id)
		if err!=nil{
			fmt.Println(err.Error())

			return ConvertMapToArray(res_datas),nil
		}
		res_datas[one_trx_id] = ""
	}
	return ConvertMapToArray(res_datas),nil

}

func GetErc20History(db * sql.DB,blocknumber int) []string{
	sqlStatement := `select txid from erc20_address_relation where blocknumber =$1 and ("from" in (select "Address" from relation_address where "Erc20Type"=true)  or "to" in (select "Address" from relation_address where "Erc20Type"=true))`
	rows,err := db.Query(sqlStatement,blocknumber)
	if err!=nil{
		return make([]string,0)
	}
	defer rows.Close()

	res_datas := make(map[string]string)
	for rows.Next(){
		var one_trx_id string
		err = rows.Scan(&one_trx_id)
		if err!=nil{
			fmt.Println(err.Error())

			return ConvertMapToArray(res_datas)
		}
		res_datas[one_trx_id] = ""
	}
	return ConvertMapToArray(res_datas)

}



func GetErc20HistoryRange(db * sql.DB,start_blocknumber,end_blocknumber int) []string{
	sqlStatement := `select txid from erc20_address_relation where blocknumber BETWEEN $1 AND $2 and ("from" in (select "Address" from relation_address where "Erc20Type"=true)  or "to" in (select "Address" from relation_address where "Erc20Type"=true))`
	rows,err := db.Query(sqlStatement,start_blocknumber,end_blocknumber)
	if err!=nil{
		return make([]string,0)
	}
	defer rows.Close()


	res_datas := make(map[string]string)
	for rows.Next(){
		var one_trx_id string
		err = rows.Scan(&one_trx_id)
		if err!=nil{
			fmt.Println(err.Error())

			return ConvertMapToArray(res_datas)
		}
		res_datas[one_trx_id] = ""
	}
	return ConvertMapToArray(res_datas)
}