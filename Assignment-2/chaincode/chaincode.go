package main

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// Defining smart contract structure
type SmartContract struct {
	contractapi.Contract
}

// Organisation structure to store balance
type Organisation struct {
	Balance float64 `json:"balance"`
}

// Item structure to store inventory item benefits
type Item struct {
	Name   string  `json:"name"`
	Number int64   `json:"number"`
	Price  float64 `json:"price"`
}

// Marketplace structure to store details of the items enlisted in the market
type Marketplace struct {
	Item     string  `json:"item"`
	Seller   string  `json:"seller"`
	Quantity int64   `json:"quantity"`
	Price    float64 `json:"marketPrice"`
}

// SmartContract functions:

// 1. AddBalance: function to add money to organisation's balance
func (s *SmartContract) AddBalance(ctx contractapi.TransactionContextInterface) error {

	// Receiving amount to be added as transient data
	transientMap, err := ctx.GetStub().GetTransient()
	if err != nil {
		return fmt.Errorf("error getting transient: %v", err)
	}
	transientAssetJSON, ok := transientMap["value"]
	if !ok {
		return fmt.Errorf("asset not found in the transient map input")
	}

	balanceTransientInput := Organisation{}
	err = json.Unmarshal(transientAssetJSON, &balanceTransientInput)

	if err != nil {
		return fmt.Errorf("failed to unmarshal JSON: %v", err)
	}

	// Updating the balance using Organisation structure
	orgBalance := Organisation{}
	clientMSPID, err := ctx.GetClientIdentity().GetMSPID()
	orgBalanceKey := clientMSPID + "_balance"

	orgBalanceBytes, err := ctx.GetStub().GetState(orgBalanceKey)

	if err != nil {
		return fmt.Errorf("Failed to read: %v", err)
	}

	newBalance := balanceTransientInput.Balance

	if len(orgBalanceBytes) != 0 {
		err := json.Unmarshal(orgBalanceBytes, &orgBalance)
		if err != nil {
			return fmt.Errorf("Failed to convert: %v", err)
		}
		newBalance = newBalance + orgBalance.Balance
	}

	orgBalance = Organisation{newBalance}
	orgBalanceBytes, err = json.Marshal(orgBalance)

	if err != nil {
		return fmt.Errorf("Failed to convert: %v", err)
	}

	// Storing the new balance in public data
	err = ctx.GetStub().PutState(orgBalanceKey, orgBalanceBytes)
	if err != nil {
		return fmt.Errorf("Failed to add balance: %v", err)
	}
	return nil
}

// 2. GetBalance: function to query the smart contract to obtain organisation balance
func (s *SmartContract) GetBalance(ctx contractapi.TransactionContextInterface) (*Organisation, error) {

	// Obtaining organisation name through transient data
	transientMap, err := ctx.GetStub().GetTransient()
	if err != nil {
		return nil, fmt.Errorf("error getting transient: %v", err)
	}
	transientAssetByteArray, ok := transientMap["body"]
	if !ok {
		return nil, fmt.Errorf("asset not found in the transient map input")
	}

	orgIdTransientInput := string(transientAssetByteArray[:])

	// Reading organisation balance
	orgBalanceKey := orgIdTransientInput + "_balance"
	orgBalanceBytes, err := ctx.GetStub().GetState(orgBalanceKey)

	if err != nil {
		return nil, fmt.Errorf("Failed to read: %v", err)
	}

	organisation := Organisation{}
	err = json.Unmarshal(orgBalanceBytes, &organisation)

	if err != nil {
		return nil, fmt.Errorf("Failed to unmarshall: %v", err)
	}

	return &organisation, nil
}

// 3. AddItem: Function to purchase item at cost price and store the item in the
// buying organisation's inventory
func (s *SmartContract) AddItem(ctx contractapi.TransactionContextInterface) error {

	transientMap, err := ctx.GetStub().GetTransient()
	if err != nil {
		return fmt.Errorf("error getting transient: %v", err)
	}
	transientAssetJSON, ok := transientMap["item"]
	if !ok {
		return fmt.Errorf("asset not found in the transient map input")
	}

	newItem := Item{}
	err = json.Unmarshal(transientAssetJSON, &newItem)

	if err != nil {
		return fmt.Errorf("failed to unmarshal JSON: %v", err)
	}

	clientMSPID, err := ctx.GetClientIdentity().GetMSPID()

	if err != nil {
		return fmt.Errorf("Failed to get client MSP ID: %v", err)
	}

	orgBalanceKey := clientMSPID + "_balance"
	orgBalanceBytes, err := ctx.GetStub().GetState(orgBalanceKey)

	if err != nil {
		return fmt.Errorf("Failed to read: %v", err)
	}

	organisation := Organisation{}
	err = json.Unmarshal(orgBalanceBytes, &organisation)

	if err != nil {
		return fmt.Errorf("Failed to unmarshall: %v", err)
	}

	// Checking if there is sufficient balance to add item to inventory
	if organisation.Balance < newItem.Price*float64(newItem.Number) {
		return fmt.Errorf("Insufficient balance. You can try reducing quantity")
	}

	// Deducting balance based on price and quantity of item purchased
	organisation.Balance -= newItem.Price * float64(newItem.Number)
	orgBalanceBytes, err = json.Marshal(organisation)

	err = ctx.GetStub().PutState(orgBalanceKey, orgBalanceBytes)
	if err != nil {
		return fmt.Errorf("Failed to add balance: %v", err)
	}

	oldItem := Item{}
	orgCollectionName := clientMSPID + "PrivateCollection"

	// Updating details of pre-existing item of the same name
	oldItemBytes, err := ctx.GetStub().GetPrivateData(orgCollectionName, newItem.Name)
	if err != nil {
		return fmt.Errorf("Failed to get items: %v", err)
	}
	if len(oldItemBytes) != 0 {
		err = json.Unmarshal(oldItemBytes, &oldItem)
		if err != nil {
			return fmt.Errorf("failed to unmarshal JSON: %v", err)
		}
		newItem.Number += oldItem.Number
	}

	// Adding the new item to the inventory
	newItemBytes, err := json.Marshal(newItem)
	if err != nil {
		return fmt.Errorf("Failed to convert: %v", err)
	}

	err = ctx.GetStub().PutPrivateData(orgCollectionName, newItem.Name, newItemBytes)

	if err != nil {
		return fmt.Errorf("Failed to put item in organisation: %v", err)
	}

	return nil
}

// 4. GetItem: function to list items in the calling organisation's inventory
func (s *SmartContract) GetItem(ctx contractapi.TransactionContextInterface) ([]*Item, error) {

	clientMSPID, err := ctx.GetClientIdentity().GetMSPID()

	if err != nil {
		return nil, fmt.Errorf("Failed to get client MSP ID: %v", err)
	}

	// Finding all items in calling organisation's collection
	orgCollectionName := clientMSPID + "PrivateCollection"
	itemsIterator, err := ctx.GetStub().GetPrivateDataByRange(orgCollectionName, "", "")

	if err != nil {
		return nil, fmt.Errorf("Failed to read: %v", err)
	}

	items := []*Item{}

	// Iterating over the items
	for itemsIterator.HasNext() {
		response, err := itemsIterator.Next()
		if err != nil {
			return nil, err
		}

		item := Item{}
		err = json.Unmarshal(response.Value, &item)
		if err != nil {
			return nil, fmt.Errorf("failed to unmarshal JSON: %v", err)
		}

		items = append(items, &item)
	}

	return items, nil
}

// 5. AddToMarket: Adding item from inventory to the market with a certain selling price
func (s *SmartContract) AddToMarket(ctx contractapi.TransactionContextInterface, _item string, _price float64) error {
	clientMSPID, err := ctx.GetClientIdentity().GetMSPID()

	if err != nil {
		return fmt.Errorf("Failed to get client MSP ID: %v", err)
	}

	orgCollectionName := clientMSPID + "PrivateCollection"
	itemBytes, err := ctx.GetStub().GetPrivateData(orgCollectionName, _item)
	if err != nil {
		return fmt.Errorf("Failed to get items: %v", err)
	}
	if len(itemBytes) == 0 {
		return fmt.Errorf("Item not found in inventory")
	}
	item := Item{}
	err = json.Unmarshal(itemBytes, &item)
	if err != nil {
		return fmt.Errorf("failed to unmarshal JSON: %v", err)
	}

	marketItem := Marketplace{}
	marketItemBytes, err := ctx.GetStub().GetState(clientMSPID + "_" + _item)
	if err != nil {
		return fmt.Errorf("Failed to get items: %v", err)
	}

	// Either increasing the quantity (and/or changing selling price) or creating
	// a new entry in the marketplace
	marketItem.Quantity = 0
	marketItem.Item = item.Name
	marketItem.Seller, err = ctx.GetClientIdentity().GetMSPID()
	if err != nil {
		return fmt.Errorf("Failed to get client MSP ID: %v", err)
	}
	if len(marketItemBytes) != 0 {
		err = json.Unmarshal(marketItemBytes, &marketItem)
		if err != nil {
			return fmt.Errorf("failed to unmarshal JSON: %v", err)
		}
	}
	marketItem.Quantity = marketItem.Quantity + 1
	marketItem.Price = _price

	marketItemBytes, err = json.Marshal(marketItem)

	if err != nil {
		return fmt.Errorf("Failed to convert: %v", err)
	}

	err = ctx.GetStub().PutState(clientMSPID+"_"+_item, marketItemBytes)
	if err != nil {
		return fmt.Errorf("Failed to add balance: %v", err)
	}

	err = ctx.GetStub().DelPrivateData(orgCollectionName, _item)
	if err != nil {
		return fmt.Errorf("Couldn't delete: %v", err)
	}
	item.Number -= 1
	if item.Number > 0 {
		itemBytes, err = json.Marshal(item)
		if err != nil {
			return fmt.Errorf("Failed to convert: %v", err)
		}
		err = ctx.GetStub().PutPrivateData(orgCollectionName, item.Name, itemBytes)
		if err != nil {
			return fmt.Errorf("Failed to put item in market: %v", err)
		}
	}

	// Creating an event which can be listened to from the application side
	ctx.GetStub().SetEvent("item_added", marketItemBytes)
	return nil
}

// 6. BuyFromMarket: function to buy item from the market
func (s *SmartContract) BuyFromMarket(ctx contractapi.TransactionContextInterface, _item string) error {
	sellerOrg := ""
	clientMSPID, err := ctx.GetClientIdentity().GetMSPID()

	if err != nil {
		return fmt.Errorf("Failed to get client MSP ID: %v", err)
	}

	// Ensuring that an organisation does not buy from itself
	if clientMSPID == "Org1MSP" {
		sellerOrg = "Org2MSP"
	} else {
		sellerOrg = "Org1MSP"
	}

	marketItemBytes, err := ctx.GetStub().GetState(sellerOrg + "_" + _item)
	if err != nil {
		return fmt.Errorf("Failed to get items: %v", err)
	}

	// If item doesn't exist in market
	if len(marketItemBytes) == 0 {
		return fmt.Errorf("Item currently not available in market. Once available, it will be bought")
	}

	marketItem := Marketplace{}
	err = json.Unmarshal(marketItemBytes, &marketItem)
	if err != nil {
		return fmt.Errorf("failed to unmarshal JSON: %v", err)
	}

	seller := marketItem.Seller
	buyer, err := ctx.GetClientIdentity().GetMSPID()
	price := marketItem.Price

	if err != nil {
		return fmt.Errorf("Failed to get client MSP ID: %v", err)
	}

	// Updating balance of the buyer
	orgBalance := Organisation{}
	orgBalanceKey := buyer + "_balance"
	orgBalanceBytes, err := ctx.GetStub().GetState(orgBalanceKey)
	if err != nil {
		return fmt.Errorf("Failed to read: %v", err)
	}

	err = json.Unmarshal(orgBalanceBytes, &orgBalance)

	if err != nil {
		return fmt.Errorf("Failed to unmarshall: %v", err)
	}
	if price > orgBalance.Balance {
		return fmt.Errorf("Insufficient balance")
	}

	orgBalance.Balance -= price
	orgBalanceBytes, err = json.Marshal(orgBalance)

	if err != nil {
		return fmt.Errorf("Failed to convert: %v", err)
	}

	err = ctx.GetStub().PutState(orgBalanceKey, orgBalanceBytes)
	if err != nil {
		return fmt.Errorf("Failed to deduct balance: %v", err)
	}

	// Updating balance of the seller
	orgBalance = Organisation{}
	orgBalanceKey = seller + "_balance"
	orgBalanceBytes, err = ctx.GetStub().GetState(orgBalanceKey)
	if err != nil {
		return fmt.Errorf("Failed to read: %v", err)
	}

	err = json.Unmarshal(orgBalanceBytes, &orgBalance)

	if err != nil {
		return fmt.Errorf("Failed to unmarshall: %v", err)
	}

	orgBalance.Balance += price
	orgBalanceBytes, err = json.Marshal(orgBalance)

	if err != nil {
		return fmt.Errorf("Failed to convert: %v", err)
	}

	err = ctx.GetStub().PutState(orgBalanceKey, orgBalanceBytes)
	if err != nil {
		return fmt.Errorf("Failed to add balance: %v", err)
	}

	// Decrementing the quantity of the item in the market, deleting if quantity becomes 0
	err = ctx.GetStub().DelState(sellerOrg + "_" + _item)
	if err != nil {
		return fmt.Errorf("Could not delete from marketplace: %v", err)
	}

	marketItem.Quantity -= 1
	if marketItem.Quantity > 0 {
		marketItemBytes, err = json.Marshal(marketItem)
		if err != nil {
			return fmt.Errorf("Failed to convert: %v", err)
		}
		ctx.GetStub().PutState(sellerOrg+"_"+_item, marketItemBytes)
	}

	return nil
}

// 7. GetItemsInMarket: function to list all the items in the marketplace
func (s *SmartContract) GetItemsInMarket(ctx contractapi.TransactionContextInterface) ([]*Marketplace, error) {

	// Creating an iterator on the public data
	itemsIterator, err := ctx.GetStub().GetStateByRange("", "")

	if err != nil {
		return nil, fmt.Errorf("Failed to read: %v", err)
	}

	items := []*Marketplace{}

	// Iterating over public data
	for itemsIterator.HasNext() {
		response, err := itemsIterator.Next()
		if err != nil {
			return nil, err
		}

		item := Marketplace{}
		err = json.Unmarshal(response.Value, &item)
		if err != nil {
			return nil, fmt.Errorf("failed to unmarshal JSON: %v", err)
		}

		if item.Item != "" {
			items = append(items, &item)
		}
	}

	return items, nil
}

// 8. Init: function to initialise the balance of both the organisations to zero
func (s *SmartContract) Init(ctx contractapi.TransactionContextInterface) error {

	orgBalanceKey := "Org1MSP" + "_balance"
	orgBalanceBytes, err := ctx.GetStub().GetState(orgBalanceKey)

	if err != nil {
		return fmt.Errorf("Could not read balance")
	}
	if len(orgBalanceBytes) == 0 {
		orgBalance := Organisation{0}
		orgBalanceBytes, err := json.Marshal(orgBalance)

		if err != nil {
			return fmt.Errorf("Failed to convert")
		}

		err = ctx.GetStub().PutState(orgBalanceKey, orgBalanceBytes)
		if err != nil {
			return fmt.Errorf("Failed to add balance")
		}

	}

	orgBalanceKey = "Org2MSP" + "_balance"
	orgBalanceBytes, err = ctx.GetStub().GetState(orgBalanceKey)

	if err != nil {
		return fmt.Errorf("Could not read balance")
	}
	if len(orgBalanceBytes) == 0 {
		orgBalance := Organisation{0}
		orgBalanceBytes, err := json.Marshal(orgBalance)

		if err != nil {
			return fmt.Errorf("Failed to convert")
		}

		err = ctx.GetStub().PutState(orgBalanceKey, orgBalanceBytes)
		if err != nil {
			return fmt.Errorf("Failed to add balance")
		}

	}
	return nil
}

// Driver function
func main() {
	// Registering chaincode (smart contract) along with above described functionality
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		fmt.Printf("Error creating chaincode: %s", err)
		return
	}

	// Starting the chaincode
	err = chaincode.Start()

	if err != nil {
		fmt.Printf("Error starting chaincode: %s", err)
	}

}
