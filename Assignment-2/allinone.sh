./network.sh down
./network.sh up -ca
./network.sh createChannel -ca
./network.sh deployCC -ccn bru -ccp ${PWD}/chaincode -ccl go -ccep "OR('Org1MSP.peer','Org2MSP.peer')" -cccg collections-config.json
export PATH=${PWD}/../bin:$PATH                                        
export FABRIC_CFG_PATH=$PWD/../config/
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_TLS_ROOTCERT_FILE=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051
rm -rf wallet1 wallet2