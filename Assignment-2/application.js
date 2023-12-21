const { Gateway, Wallets } = require("fabric-network");
const FabricCAServices = require("fabric-ca-client");

const fs = require("fs");
const path = require("path");
// Required for async input 
const readline = require("node:readline/promises");
const { stdin: input, stdout: output } = require("node:process");

async function main() {
  /* Org1 connection profile */
  console.log("Creating Org1 connection profile..");
  const ccpPath1 = path.resolve(
    "organizations/peerOrganizations/org1.example.com/connection-org1.json"
  );
  const ccp1 = JSON.parse(fs.readFileSync(ccpPath1, "utf8"));
  console.log("Created Org1 connection profile");

  /* Org2 connection profile */
  console.log("Creating Org2 connection profile..");
  const ccpPath2 = path.resolve(
    "organizations/peerOrganizations/org2.example.com/connection-org2.json"
  );
  const ccp2 = JSON.parse(fs.readFileSync(ccpPath2, "utf8"));
  console.log("Created Org2 connection profile");

  /* Org1 certificate authorities */
  console.log("Creating Org1 certificate authorities..");
  const caInfo1 = ccp1.certificateAuthorities["ca.org1.example.com"];
  const caTLSCACerts1 = caInfo1.tlsCACerts.pem;
  const ca1 = new FabricCAServices(
    caInfo1.url,
    {
      trustedRoots: caTLSCACerts1,
      verify: false,
    },
    caInfo1.caName
  );
  console.log("Created Org1 certificate authorities");

  /* Org2 certificate authorities */
  console.log("Creating Org2 certificate authorities..");
  const caInfo2 = ccp2.certificateAuthorities["ca.org2.example.com"];
  const caTLSCACerts2 = caInfo2.tlsCACerts.pem;
  const ca2 = new FabricCAServices(
    caInfo2.url,
    {
      trustedRoots: caTLSCACerts2,
      verify: false,
    },
    caInfo2.caName
  );
  console.log("Created Org2 certificate authorities");

  /* Creating wallet for Org1*/
  console.log("Creating wallet for Org1..");
  const walletPath1 = path.join(process.cwd(), "wallet1");
  const wallet1 = await Wallets.newFileSystemWallet(walletPath1);
  console.log("Created wallet for Org1");

  /* Creating wallet for Org2*/
  console.log("Creating wallet for Org2..");
  const walletPath2 = path.join(process.cwd(), "wallet2");
  const wallet2 = await Wallets.newFileSystemWallet(walletPath2);
  console.log("Created wallet for Org2");

  /* Get admin identity for Org1 */
  console.log("Creating admin for Org1..");
  var adminID1 = await wallet1.get("admin");
  const enrollment1 = await ca1.enroll({
    enrollmentID: "admin",
    enrollmentSecret: "adminpw",
  });
  const x509ID1 = {
    credentials: {
      certificate: enrollment1.certificate,
      privateKey: enrollment1.key.toBytes(),
    },
    mspId: "Org1MSP",
    type: "X.509",
  };
  await wallet1.put("admin", x509ID1);
  adminID1 = await wallet1.get("admin");
  console.log("Created admin for Org1");

  /* Get admin identity for Org2 */
  console.log("Creating admin for Org2..");
  var adminID2 = await wallet2.get("admin");
  const enrollment2 = await ca2.enroll({
    enrollmentID: "admin",
    enrollmentSecret: "adminpw",
  });
  const x509ID2 = {
    credentials: {
      certificate: enrollment2.certificate,
      privateKey: enrollment2.key.toBytes(),
    },
    mspId: "Org2MSP",
    type: "X.509",
  };
  await wallet2.put("admin", x509ID2);
  adminID2 = await wallet2.get("admin");
  console.log("Created admin for Org2");

  /* User registration for Org1 */
  var userID1 = await wallet1.get("appUser");
  if (!userID1) {
    console.log("Registering peer0 from Org1..");
    const provider1 = wallet1.getProviderRegistry().getProvider(adminID1.type);
    const adminUser1 = await provider1.getUserContext(adminID1, "admin");

    const secret1 = await ca1.register(
      {
        affiliation: "org1.department1",
        enrollmentID: "appUser",
        role: "client",
      },
      adminUser1
    );

    const enrollment1 = await ca1.enroll({
      enrollmentID: "appUser",
      enrollmentSecret: secret1,
    });

    const x509ID1 = {
      credentials: {
        certificate: enrollment1.certificate,
        privateKey: enrollment1.key.toBytes(),
      },
      mspId: "Org1MSP",
      type: "X.509",
    };

    await wallet1.put("appUser", x509ID1);
    userID1 = await wallet1.get("appUser");
    console.log("peer0 from Org1 registered");
  }

  /* User registration for Org2 */
  var userID2 = await wallet2.get("appUser");
  if (!userID2) {
    console.log("Registering peer0 from Org2..");
    const provider2 = wallet2.getProviderRegistry().getProvider(adminID2.type);
    const adminUser2 = await provider2.getUserContext(adminID2, "admin");

    const secret2 = await ca2.register(
      {
        affiliation: "org2.department1",
        enrollmentID: "appUser",
        role: "client",
      },
      adminUser2
    );

    const enrollment2 = await ca2.enroll({
      enrollmentID: "appUser",
      enrollmentSecret: secret2,
    });

    const x509ID2 = {
      credentials: {
        certificate: enrollment2.certificate,
        privateKey: enrollment2.key.toBytes(),
      },
      mspId: "Org2MSP",
      type: "X.509",
    };

    await wallet2.put("appUser", x509ID2);
    userID2 = await wallet2.get("appUser");
    console.log("peer0 from Org2 registered");
  }

  /* Connect to gateway for Org1 */
  console.log("Connecting to gateway for Org1");
  const gateway1 = new Gateway();
  await gateway1.connect(ccp1, {
    wallet: wallet1,
    identity: "appUser",
    discovery: {
      enabled: true,
      asLocalhost: true,
    },
  });
  console.log("Connected to gateway for Org1");

  /* Connect to gateway for Org2*/
  console.log("Connecting to gateway for Org2");
  const gateway2 = new Gateway();
  await gateway2.connect(ccp2, {
    wallet: wallet2,
    identity: "appUser",
    discovery: {
      enabled: true,
      asLocalhost: true,
    },
  });
  console.log("Connected to gateway for Org2");

  /* Connect to channel */
  const network1 = await gateway1.getNetwork("mychannel");
  const network2 = await gateway2.getNetwork("mychannel");

  const contract1 = network1.getContract("bru");
  const contract2 = network2.getContract("bru");
  contract1.addDiscoveryInterest({
    name: "bru",
    collectionNames: ["Org1MSPPrivateCollection"],
  });
  contract2.addDiscoveryInterest({
    name: "bru",
    collectionNames: ["Org2MSPPrivateCollection"],
  });

  const contracts = [contract1, contract2];

  const rl = readline.createInterface({ input, output });
  let org = await rl.question("Enter your organisation (1 or 2): ");
  org = parseInt(org);
  org -= 1;

  contracts[org].submitTransaction("Init");

  const wishlist = [];

  // If the item is present in the list of required items, trigger a smart contract to buy the item
  async function placeOrder(item, buyer) {
    const index = wishlist.indexOf(item);
    if (index > -1) {
      try {
        await contracts[buyer].submitTransaction(
          "BuyFromMarket",
          wishlist[index]
        );
        console.log(`Bought item: ${item}`);
        wishlist.splice(index, 1);
      } catch (err) {
        console.log(`Error: ${err.message}`);
      }
    }
  }

  /* Defining an event listener which gets triggered when a new item in enlisted in the marketplace */
  await contracts[org].addContractListener(async (event) => {
    if (event.eventName !== "item_added") return;
    console.log("New item added to market. Checking wishlists ...");
    const item = JSON.parse(event.payload.toString());
    await placeOrder(item.item, org);
    process.stdout.write(`[peer0.org${org + 1}] Enter command: `);
  });

  /* Commands:
    ADD_MONEY: AddBalance()
    ADD_ITEM: AddItem()
    QUERY_BALANCE: GetBalance()
    GET_ITEM: GetItem()
    EXIT: breaks the loop
  */

  let val, result;
  let run = true;
  while (run) {
    const cmd = await rl.question(`[peer0.org${org + 1}] Enter command: `);
    switch (cmd) {
      // Adding money to the organisation's balance
      case "ADD_MONEY":
        val = await rl.question("Enter amount: ");
        val = Number(val);
        try {
          if (val < 0) {
            throw new Error("Enter positive value");
          }
          // Sending the value as transient data
          let statefulTxn = contracts[org].createTransaction("AddBalance");
          let sendData = { balance: val };
          let tmapData = Buffer.from(JSON.stringify(sendData));
          statefulTxn.setTransient({
            value: tmapData,
          });
          await statefulTxn.submit();
        } catch (err) {
          console.log(`Error: ${err.message}`);
        }
        break;

      // Adding item to the organisation's inventory
      case "ADD_ITEM":
        console.log("Enter item details: ");
        let name = await rl.question("Name: ");
        let number = parseInt(await rl.question("Quantity: "));
        let price = parseFloat(await rl.question("Price: "));

        try {
          let statefulTxn = contracts[org].createTransaction("AddItem");
          let sendData = { name: name, number: number, price: price };
          let tmapData = Buffer.from(JSON.stringify(sendData));
          statefulTxn.setTransient({
            item: tmapData,
          });
          await statefulTxn.submit();
        } catch (err) {
          console.log(`Error: ${err.message}`);
        }
        break;

      // Querying organisation's balance
      case "QUERY_BALANCE":
        let orgId = await rl.question(
          "Enter organisation id (Org1MSP, Org2MSP): "
        );
        try {
          if (orgId !== "Org1MSP" && orgId !== "Org2MSP") {
            throw new Error("Invalid organisation name");
          }
          // Each organisation can view the other's balance
          let statefulTxn = contracts[org].createTransaction("GetBalance");
          let tmapData = Buffer.from(orgId);
          statefulTxn.setTransient({
            body: tmapData,
          });
          result = await statefulTxn.evaluate();
          console.log(`Balance of ${orgId}: ${result.toString()}`);
        } catch (err) {
          console.log(`Error: ${err.message}`);
        }
        break;

      // List items in the organisation's inventory
      case "GET_ITEM":
        try {
          result = await contracts[org].evaluateTransaction("GetItem");
          console.log(`Item info: ${result.toString()}`);
        } catch (err) {
          console.log(`Error: ${err.message}`);
        }
        break;

      // Add an item to the marketplace
      case "ENLIST_ITEM":
        try {
          let name = await rl.question("Enter name: ");
          let price = parseFloat(await rl.question("Enter price: "));
          await contracts[org].submitTransaction("AddToMarket", name, price);
          console.log("Successfully added to market");
          // Event listener waits for completion of this event and then calls placeOrder
        } catch (err) {
          console.log(`Error: ${err.message}`);
        }
        break;

      // Add an item to the local wishlist of the organisation
      case "WISHLIST":
        try {
          let name = await rl.question("Enter name: ");
          wishlist.push(name);
          console.log("Added to wishlist. Checking market for item ...");
          // Try to purchase the item if it exists already
          await placeOrder(name, org);
        } catch (err) {
          console.log(`Error: ${err.message}`);
        }
        break;

      // List all items in the marketplace
      case "ALL_ITEMS":
        try {
          result = await contracts[org].evaluateTransaction("GetItemsInMarket");
          console.log(`Item info: ${result.toString()}`);
        } catch (err) {
          console.log(`Error: ${err.message}`);
        }
        break;

      // Terminating the program
      case "EXIT":
        console.log("Closing..");
        rl.close();
        run = false;
        break;

      // Default case
      default:
        console.log("Invalid command!\n");
        break;
    }
  }

  gateway1.disconnect();
  gateway2.disconnect();
}

main();