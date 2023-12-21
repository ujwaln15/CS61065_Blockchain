var { Web3 } = require("web3");
var Contract = require("web3-eth-contract");
var fs = require('fs');

async function main() {

	const abi = JSON.parse(fs.readFileSync('bin/TicketBooking.abi'))
	const web3 = new Web3(
		new Web3.providers.HttpProvider("https://sepolia.infura.io/v3/709bd0e03e8a4dce8e43c33f3f17daea",
		),
	);

	const keyStore = '{"address":"cb28144dbe97b37e50e494adae483a1e68983a04","crypto":{"cipher":"aes-128-ctr","ciphertext":"29c19146375e01f5b407467e1c13fd2efec8d5840d4f6d75ba9bd32fb8e87dd7","cipherparams":{"iv":"4bbe25143d295832fb0661f33e5ad6e5"},"kdf":"scrypt","kdfparams":{"dklen":32,"n":262144,"p":1,"r":8,"salt":"b686d9809e07d68eb207db82bf46d9c8585a83aa007b54a34f86d84ca267fd17"},"mac":"f64097579488e44c90a19f95c5f6e632150a6962e5820d42b9994738ffed07b6"},"id":"88c82294-a03b-4b02-b2c8-35c4074a5f8e","version":3}';
	const ownerKeyStore =
    '{"address":"40beddbaf612f1ec1db96329a7bb02860b4f614f","crypto":{"cipher":"aes-128-ctr","ciphertext":"1b9be33d02905e05ddd5fc3ce324882dabce44dc66061c78c84907e4b0f1ada2","cipherparams":{"iv":"cb6178a56cd6588bb131d43723513d6e"},"kdf":"scrypt","kdfparams":{"dklen":32,"n":262144,"p":1,"r":8,"salt":"e0e9f93344eeb29a0986622fa41658828bb57bb51a08c680a1bdc47a6a0a161b"},"mac":"7f010a2aa0a43845d329639b6cc2f63ff0414cb6e84a56e61fe5a05d3af04ec3"},"id":"20a5a4c0-3749-4977-bf58-4006c6a7c84d","version":3}';
	const decryptedKeyStore = await web3.eth.accounts.decrypt(keyStore, "blockchain");
	const decryptedOwnerKeyStore = await web3.eth.accounts.decrypt(ownerKeyStore, "blockchain");

	const contractHash = "0x42d1feb8f019bd7ca2929400549b0119d1cefd95";

	const contract = new web3.eth.Contract(
		abi,
		contractHash,
	);

	// Buying tickets
	// let tx = {
	// 	from: decryptedKeyStore.address,
	// 	to: contractHash,
	// 	gasPrice: "7000",
	// 	data: contract.methods.buyTicket('bru@bru.com',60).encodeABI(),
	// 	value: "60005",
	// };
	// let signedTx = await web3.eth.accounts.signTransaction(tx,decryptedKeyStore.privateKey)
	// let receipt = await web3.eth
	// 			.sendSignedTransaction(signedTx.rawTransaction)
	// 			.once("transactionHash", (txhash) => {
	// 					console.log(`Mining transaction ...`);
	// 					console.log(`https://sepolia.etherscan.io/tx/${txhash}`);
	// 			});

	// contract.methods.getBuyerAmountPaid(decryptedKeyStore.address)
	// .call()
	// .then((x)=>{
	// 	console.log(`Buyer ${decryptedKeyStore.address} has paid ${x}`);
	// });

	// contract.methods.getNumTicketsSold()
	// .call()
	// .then((x)=>{
	// 	console.log(`Number of tickets sold: ${x}`);
	// });


	// Withdraw Funds
	tx = {
		from: decryptedOwnerKeyStore.address,
		to: contractHash,
		gasPrice: "7000",
		data: contract.methods.withdrawFunds().encodeABI(),
		value: "0x0",
	};
	signedTx = await web3.eth.accounts.signTransaction(tx,decryptedOwnerKeyStore.privateKey)
	receipt = await web3.eth
				.sendSignedTransaction(signedTx.rawTransaction)
				.once("transactionHash", (txhash) => {
						console.log(`Mining transaction ...`);
						console.log(`https://sepolia.etherscan.io/tx/${txhash}`);
				});


	// Buying tickets
	// tx = {
	// 	from: decryptedKeyStore.address,
	// 	to: contractHash,
	// 	gasPrice: "7000",
	// 	data: contract.methods.buyTicket('bru@bru.com',40).encodeABI(),
	// 	value: "40000",
	// };
	// signedTx = await web3.eth.accounts.signTransaction(tx,decryptedKeyStore.privateKey)
	// receipt = await web3.eth
	// 			.sendSignedTransaction(signedTx.rawTransaction)
	// 			.once("transactionHash", (txhash) => {
	// 					console.log(`Mining transaction ...`);
	// 					console.log(`https://sepolia.etherscan.io/tx/${txhash}`);
	// 			});
	
	// Attempting purchase in full theatre

	// tx = {
	// 	from: decryptedKeyStore.address,
	// 	to: contractHash,
	// 	gasPrice: "7000",
	// 	data: contract.methods.buyTicket('bru@bru.com',51).encodeABI(),
	// 	value: "51005",
	// };
	// signedTx = await web3.eth.accounts.signTransaction(tx,decryptedKeyStore.privateKey)
	// receipt = await web3.eth
	// 			.sendSignedTransaction(signedTx.rawTransaction)
	// 			.once("transactionHash", (txhash) => {
	// 					console.log(`Mining transaction ...`);
	// 					console.log(`https://sepolia.etherscan.io/tx/${txhash}`);
	// 			});

	// contract.methods.getBuyerAmountPaid(decryptedKeyStore.address)
	// .call()
	// .then((x)=>{
	// 	console.log(`Buyer ${decryptedKeyStore.address} has paid ${x}`);
	// });

	// contract.methods.getNumTicketsSold()
	// .call()
	// .then((x)=>{
	// 	console.log(`Number of tickets sold: ${x}`);
	// });

	// Refund tickets

	// tx = {
	// 	from: decryptedOwnerKeyStore.address,
	// 	to: contractHash,
	// 	gasPrice: "7000",
	// 	data: contract.methods.refundTicket(decryptedKeyStore.address).encodeABI(),
	// 	value: "0x0",
	// };
	// signedTx = await web3.eth.accounts.signTransaction(tx,decryptedOwnerKeyStore.privateKey)
	// receipt = await web3.eth
	// 			.sendSignedTransaction(signedTx.rawTransaction)
	// 			.once("transactionHash", (txhash) => {
	// 					console.log(`Mining transaction ...`);
	// 					console.log(`https://sepolia.etherscan.io/tx/${txhash}`);
	// 			});

	// contract.methods.getBuyerAmountPaid(decryptedKeyStore.address)
	// .call()
	// .then((x)=>{
	// 	console.log(`Buyer ${decryptedKeyStore.address} has paid ${x}`);
	// });

	// contract.methods.getNumTicketsSold()
	// .call()
	// .then((x)=>{
	// 	console.log(`Number of tickets sold: ${x}`);
	// });


	// Destroy the contract

	// tx = {
	// 	from: decryptedOwnerKeyStore.address,
	// 	to: contractHash,
	// 	gasPrice: "7000",
	// 	data: contract.methods.kill().encodeABI(),
	// 	value: "0x0",
	// };
	// signedTx = await web3.eth.accounts.signTransaction(tx,decryptedOwnerKeyStore.privateKey)
	// receipt = await web3.eth
	// 			.sendSignedTransaction(signedTx.rawTransaction)
	// 			.once("transactionHash", (txhash) => {
	// 					console.log(`Mining transaction ...`);
	// 					console.log(`https://sepolia.etherscan.io/tx/${txhash}`);
	// 			});

}

main();

