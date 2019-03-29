package main

import (
	"encoding/hex"
	"fmt"
	"github.com/kataras/iris/core/errors"
	btm_types "github.com/bytom/protocol/bc/types"
	btm_txbuilder "github.com/bytom/blockchain/txbuilder"
	btm_common "github.com/bytom/common"
	btm_vmutil "github.com/bytom/protocol/vm/vmutil"
	btm_chainkd "github.com/bytom/crypto/ed25519/chainkd"
	btm_bc "github.com/bytom/protocol/bc"
)

type btmUTXO struct {
	address string
	srcID string
	program string
	amount uint64
	pos uint64
}

const (
	bcHashLen = 32
	btmPrecision = 100000000
	btmPrecisionBits = 8
	btmAssetID = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
	btmAssetName = "BTM"
)

func convertToBCHash(s string) (btm_bc.Hash, error) {
	bs, _ := hex.DecodeString(s)
	if len(bs) != bcHashLen {
		return btm_bc.Hash{}, fmt.Errorf("convertToBCHash: invalid param")
	}

	var b [bcHashLen]byte
	copy(b[:], bs)

	return btm_bc.NewHash(b), nil
}

func convertToBCAssetID(s string) (btm_bc.AssetID, error) {
	bs, _ := hex.DecodeString(s)
	if len(bs) != bcHashLen {
		return btm_bc.AssetID{}, fmt.Errorf("convertToBCHash: invalid param")
	}

	var b [bcHashLen]byte
	copy(b[:], bs)
	assetID := btm_bc.NewAssetID(b)
	return assetID, nil
}

func UTXO2Input(u btmUTXO) (*btm_types.TxInput, *btm_txbuilder.SigningInstruction, error) {
	hsrcID, err := convertToBCHash(u.srcID)
	if err != nil {
		return nil, nil, err
	}

	hassetID, err := convertToBCAssetID(btmAssetID)
	if err != nil {
		return nil, nil, err
	}

	bctrl, err := hex.DecodeString(u.program)
	if err != nil {
		return nil, nil, err
	}

	txInput := btm_types.NewSpendInput(nil, hsrcID, hassetID, u.amount, u.pos, bctrl)
	sigInst := &btm_txbuilder.SigningInstruction{}

	address, err := btm_common.DecodeAddress(u.address, btm_consensus_param)
	if err != nil {
		return nil, nil, err
	}

	switch address.(type) {
	case *btm_common.AddressWitnessPubKeyHash:
		xPub := btm_chainkd.XPub{}
		derivedPK := xPub.PublicKey()
		//fmt.Println("derivedPK:", hex.EncodeToString(derivedPK))
		sigInst.AddRawWitnessKeys([]btm_chainkd.XPub{xPub}, [][]byte{}, 1)
		sigInst.WitnessComponents = append(sigInst.WitnessComponents, btm_txbuilder.DataWitness([]byte(derivedPK)))

	case *btm_common.AddressWitnessScriptHash:
		derivedXPubs := make([]btm_chainkd.XPub, 0)
		for i:=0; i<15; i++ {
			derivedXPubs = append(derivedXPubs, btm_chainkd.XPub{})
		}
		derivedPKs := btm_chainkd.XPubKeys(derivedXPubs)
		script, err := btm_vmutil.P2SPMultiSigProgram(derivedPKs, 11)
		if err != nil {
			return nil, nil, err
		}
		sigInst.AddRawWitnessKeys(derivedXPubs, [][]byte{}, 11)
		sigInst.WitnessComponents = append(sigInst.WitnessComponents, btm_txbuilder.DataWitness(script))

	default:
		return nil, nil, fmt.Errorf("unsupport address type")
	}

	return txInput, sigInst, nil
}

func getProgramByAddress(address string) ([]byte, error) {
	addr, err := btm_common.DecodeAddress(address, btm_consensus_param)
	if err != nil {
		return nil, err
	}
	redeemContract := addr.ScriptAddress()
	program := []byte{}
	switch addr.(type) {
	case *btm_common.AddressWitnessPubKeyHash:
		program, err = btm_vmutil.P2WPKHProgram(redeemContract)
	case *btm_common.AddressWitnessScriptHash:
		program, err = btm_vmutil.P2WSHProgram(redeemContract)
	default:
		return nil, errors.New("invalid address")
	}
	if err != nil {
		return nil, err
	}
	return program, nil
}
