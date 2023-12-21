const { Web3 } = require("web3");

// Loading the contract ABI and Bytecode
// (the results of a previous compilation step)
const fs = require("fs");
const { abi, bytecode } = JSON.parse(fs.readFileSync("bin/TicketBooking.json"));

async function main() {
  // Configuring the connection to an Ethereum node
    const web3 = new Web3(
    new Web3.providers.HttpProvider(
        "https://sepolia.infura.io/v3/709bd0e03e8a4dce8e43c33f3f17daea"
    )
    );


    const keyStore =
    '{"address":"40beddbaf612f1ec1db96329a7bb02860b4f614f","crypto":{"cipher":"aes-128-ctr","ciphertext":"1b9be33d02905e05ddd5fc3ce324882dabce44dc66061c78c84907e4b0f1ada2","cipherparams":{"iv":"cb6178a56cd6588bb131d43723513d6e"},"kdf":"scrypt","kdfparams":{"dklen":32,"n":262144,"p":1,"r":8,"salt":"e0e9f93344eeb29a0986622fa41658828bb57bb51a08c680a1bdc47a6a0a161b"},"mac":"7f010a2aa0a43845d329639b6cc2f63ff0414cb6e84a56e61fe5a05d3af04ec3"},"id":"20a5a4c0-3749-4977-bf58-4006c6a7c84d","version":3}';
    const decryptedKeyStore = await web3.eth.accounts.decrypt(
    keyStore,
    "blockchain"
    );

    // Using the signing account to deploy the contract
    const contract = new web3.eth.Contract(abi);
    const tx = {
    	from: decryptedKeyStore.address,
    	gasPrice: "70000",
    	data: contract.deploy({data: bytecode, arguments: [50, 1000]}).encodeABI(),
    	value: "0x0",
    };
    const signedDeployTx = await web3.eth.accounts.signTransaction(
        tx,
        decryptedKeyStore.privateKey
    );
    const receipt = await web3.eth
        .sendSignedTransaction(signedDeployTx.rawTransaction)
        .once("transactionHash", (txhash) => {
            console.log(`Mining transaction ...`);
            console.log(`https://sepolia.etherscan.io/tx/${txhash}`);
        });
}

main();
