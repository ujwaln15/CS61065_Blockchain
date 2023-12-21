var { Web3 } = require("web3");
var Contract = require("web3-eth-contract");
var fs = require('fs');

async function main() {

	const abi = JSON.parse(fs.readFileSync('bin/AddressRollMap.abi'))
	const web3 = new Web3(
		new Web3.providers.HttpProvider("https://sepolia.infura.io/v3/709bd0e03e8a4dce8e43c33f3f17daea",
		),
	);

	const keyStore = '{"address":"cb28144dbe97b37e50e494adae483a1e68983a04","crypto":{"cipher":"aes-128-ctr","ciphertext":"29c19146375e01f5b407467e1c13fd2efec8d5840d4f6d75ba9bd32fb8e87dd7","cipherparams":{"iv":"4bbe25143d295832fb0661f33e5ad6e5"},"kdf":"scrypt","kdfparams":{"dklen":32,"n":262144,"p":1,"r":8,"salt":"b686d9809e07d68eb207db82bf46d9c8585a83aa007b54a34f86d84ca267fd17"},"mac":"f64097579488e44c90a19f95c5f6e632150a6962e5820d42b9994738ffed07b6"},"id":"88c82294-a03b-4b02-b2c8-35c4074a5f8e","version":3}'
	const decryptedKeyStore = await web3.eth.accounts.decrypt(keyStore, "blockchain")

	const contract = new web3.eth.Contract(
		abi,
		"0xF98bFe8bf2FfFAa32652fF8823Bba6714c79eDd4",
	);

	contract.methods.get("0x328Ff6652cc4E79f69B165fC570e3A0F468fc903")
	.call(
		{
			from: "0xcb28144dbe97b37e50e494adae483a1e68983a04"
		}
	)
	.then((x)=>{
		console.log(x);
	});

	// const tx = {
	// 	from: decryptedKeyStore.address,
	// 	to: "0xF98bFe8bf2FfFAa32652fF8823Bba6714c79eDd4",
	// 	gasPrice: "70000000",
	// 	data: contract.methods.update("19EC39044").encodeABI(),
	// 	value: "0x0",
	// };
	// // console.log(tx)
	// const signedTx = await web3.eth.accounts.signTransaction(tx,decryptedKeyStore.privateKey)
	// console.log(signedTx)
	// const receipt = await web3.eth
	// 			.sendSignedTransaction(signedTx.rawTransaction)
	// 			.once("transactionHash", (txhash) => {
	// 					console.log(`Mining transaction ...`);
	// 					console.log(`https://sepolia.etherscan.io/tx/${txhash}`);
	// 			});

}

main();

