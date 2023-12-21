"""
    CS61065: Theory and Applications of Blockchain
    Assignment 3: Hyperledger Indy

    19EC39007: Bbiswabasu Roy
    19EC39044: Ujwal Nitin Nayak
    19EC39045: Rishi Suman
"""


import asyncio
import json
import time

from indy import pool, wallet, did, ledger, anoncreds, blob_storage
from indy.error import ErrorCode, IndyError
from indy.pairwise import get_pairwise

from os.path import dirname


async def verifier_get_entities_from_ledger(
    pool_handle, _did, identifiers, actor, timestamp=None
):
    schemas = {}
    cred_defs = {}
    rev_reg_defs = {}
    rev_regs = {}
    for item in identifiers:
        print('"{}" -> Get Schema from Ledger'.format(actor))
        (received_schema_id, received_schema) = await get_schema(
            pool_handle, _did, item["schema_id"]
        )
        schemas[received_schema_id] = json.loads(received_schema)

        print('"{}" -> Get Claim Definition from Ledger'.format(actor))
        (received_cred_def_id, received_cred_def) = await get_cred_def(
            pool_handle, _did, item["cred_def_id"]
        )
        cred_defs[received_cred_def_id] = json.loads(received_cred_def)

        if "rev_reg_id" in item and item["rev_reg_id"] is not None:
            # Get Revocation Definitions and Revocation Registries
            print('"{}" -> Get Revocation Definition from Ledger'.format(actor))
            get_revoc_reg_def_request = await ledger.build_get_revoc_reg_def_request(
                _did, item["rev_reg_id"]
            )

            get_revoc_reg_def_response = await ensure_previous_request_applied(
                pool_handle,
                get_revoc_reg_def_request,
                lambda response: response["result"]["data"] is not None,
            )
            (
                rev_reg_id,
                revoc_reg_def_json,
            ) = await ledger.parse_get_revoc_reg_def_response(
                get_revoc_reg_def_response
            )

            print('"{}" -> Get Revocation Registry from Ledger'.format(actor))
            if not timestamp:
                timestamp = item["timestamp"]
            get_revoc_reg_request = await ledger.build_get_revoc_reg_request(
                _did, item["rev_reg_id"], timestamp
            )
            get_revoc_reg_response = await ensure_previous_request_applied(
                pool_handle,
                get_revoc_reg_request,
                lambda response: response["result"]["data"] is not None,
            )
            (
                rev_reg_id,
                rev_reg_json,
                timestamp2,
            ) = await ledger.parse_get_revoc_reg_response(get_revoc_reg_response)

            rev_regs[rev_reg_id] = {timestamp2: json.loads(rev_reg_json)}
            rev_reg_defs[rev_reg_id] = json.loads(revoc_reg_def_json)

    return (
        json.dumps(schemas),
        json.dumps(cred_defs),
        json.dumps(rev_reg_defs),
        json.dumps(rev_regs),
    )


async def get_schema(pool_handle, _did, schema_id):
    get_schema_request = await ledger.build_get_schema_request(_did, schema_id)
    get_schema_response = await ensure_previous_request_applied(
        pool_handle,
        get_schema_request,
        lambda response: response["result"]["data"] is not None,
    )
    return await ledger.parse_get_schema_response(get_schema_response)


async def get_cred_def(pool_handle, _did, cred_def_id):
    get_cred_def_request = await ledger.build_get_cred_def_request(_did, cred_def_id)
    get_cred_def_response = await ensure_previous_request_applied(
        pool_handle,
        get_cred_def_request,
        lambda response: response["result"]["data"] is not None,
    )
    return await ledger.parse_get_cred_def_response(get_cred_def_response)


async def ensure_previous_request_applied(pool_handle, checker_request, checker):
    for _ in range(3):
        response = json.loads(await ledger.submit_request(pool_handle, checker_request))
        try:
            if checker(response):
                return json.dumps(response)
        except TypeError:
            pass
        time.sleep(5)


async def create_wallet(identity):
    print('"{}" -> Create wallet'.format(identity["name"]))
    try:
        await wallet.create_wallet(
            identity["wallet_config"], identity["wallet_credentials"]
        )
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            pass
    identity["wallet"] = await wallet.open_wallet(
        identity["wallet_config"], identity["wallet_credentials"]
    )


async def getting_verinym(from_, to):
    await create_wallet(to)

    (to["did"], to["key"]) = await did.create_and_store_my_did(to["wallet"], "{}")

    from_["info"] = {"did": to["did"], "verkey": to["key"], "role": to["role"] or None}

    await send_nym(
        from_["pool"],
        from_["wallet"],
        from_["did"],
        from_["info"]["did"],
        from_["info"]["verkey"],
        from_["info"]["role"],
    )


async def send_nym(pool_handle, wallet_handle, _did, new_did, new_key, role):
    nym_request = await ledger.build_nym_request(_did, new_did, new_key, None, role)
    print(nym_request)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, nym_request)


async def get_credential_for_referent(search_handle, referent):
    credentials = json.loads(
        await anoncreds.prover_fetch_credentials_for_proof_req(
            search_handle, referent, 10
        )
    )
    return credentials[0]["cred_info"]


async def prover_get_entities_from_ledger(
    pool_handle, _did, identifiers, actor, timestamp_from=None, timestamp_to=None
):
    schemas = {}
    cred_defs = {}
    rev_states = {}
    for item in identifiers.values():
        print('"{}" -> Get Schema from Ledger'.format(actor))
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.", item["schema_id"])
        (received_schema_id, received_schema) = await get_schema(
            pool_handle, _did, item["schema_id"]
        )
        schemas[received_schema_id] = json.loads(received_schema)

        print('"{}" -> Get Claim Definition from Ledger'.format(actor))
        (received_cred_def_id, received_cred_def) = await get_cred_def(
            pool_handle, _did, item["cred_def_id"]
        )
        cred_defs[received_cred_def_id] = json.loads(received_cred_def)

        if "rev_reg_id" in item and item["rev_reg_id"] is not None:
            # Create Revocations States
            print(
                '"{}" -> Get Revocation Registry Definition from Ledger'.format(actor)
            )
            get_revoc_reg_def_request = await ledger.build_get_revoc_reg_def_request(
                _did, item["rev_reg_id"]
            )

            get_revoc_reg_def_response = await ensure_previous_request_applied(
                pool_handle,
                get_revoc_reg_def_request,
                lambda response: response["result"]["data"] is not None,
            )
            (
                rev_reg_id,
                revoc_reg_def_json,
            ) = await ledger.parse_get_revoc_reg_def_response(
                get_revoc_reg_def_response
            )

            print('"{}" -> Get Revocation Registry Delta from Ledger'.format(actor))
            if not timestamp_to:
                timestamp_to = int(time.time())
            get_revoc_reg_delta_request = (
                await ledger.build_get_revoc_reg_delta_request(
                    _did, item["rev_reg_id"], timestamp_from, timestamp_to
                )
            )
            get_revoc_reg_delta_response = await ensure_previous_request_applied(
                pool_handle,
                get_revoc_reg_delta_request,
                lambda response: response["result"]["data"] is not None,
            )
            (
                rev_reg_id,
                revoc_reg_delta_json,
                t,
            ) = await ledger.parse_get_revoc_reg_delta_response(
                get_revoc_reg_delta_response
            )

            tails_reader_config = json.dumps(
                {
                    "base_dir": dirname(
                        json.loads(revoc_reg_def_json)["value"]["tailsLocation"]
                    ),
                    "uri_pattern": "",
                }
            )
            blob_storage_reader_cfg_handle = await blob_storage.open_reader(
                "default", tails_reader_config
            )

            print("%s - Create Revocation State", actor)
            rev_state_json = await anoncreds.create_revocation_state(
                blob_storage_reader_cfg_handle,
                revoc_reg_def_json,
                revoc_reg_delta_json,
                t,
                item["cred_rev_id"],
            )
            rev_states[rev_reg_id] = {t: json.loads(rev_state_json)}

    return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_states)


async def run():
    # Loading .txn file
    pool_ = {"name": "bru"}
    print("Open Pool Ledger: {}".format(pool_["name"]))
    pool_["genesis_txn_path"] = "bru.txn"
    pool_["config"] = json.dumps({"genesis_txn": str(pool_["genesis_txn_path"])})

    print(pool_)

    # Set protocol version 2 to work with Indy Node 1.4
    await pool.set_protocol_version(2)

    try:
        await pool.create_pool_ledger_config(pool_["name"], pool_["config"])
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            pass
    pool_["handle"] = await pool.open_pool_ledger(pool_["name"], None)

    print(pool_["handle"])
    #    --------------------------------------------------------------------------
    #  Accessing a steward.

    steward = {
        "name": "StewardSandip",
        "wallet_config": json.dumps({"id": "steward_sandip_wallet"}),
        "wallet_credentials": json.dumps({"key": "steward_sandip_wallet_key"}),
        "pool": pool_["handle"],
        "seed": "000000000000000000000000Steward1",
    }
    print(steward)

    await create_wallet(steward)

    print(steward["wallet"])

    steward["did_info"] = json.dumps({"seed": steward["seed"]})
    print(steward["did_info"])

    steward["did"], steward["key"] = await did.create_and_store_my_did(
        steward["wallet"], steward["did_info"]
    )

    # ----------------------------------------------------------------------
    # Create and register dids for Government, NAA and CBDC bank
    #
    print("\n\n\n==============================")
    print("==  Government registering Verinym  ==")
    print("------------------------------")

    government = {
        "name": "Government",
        "wallet_config": json.dumps({"id": "government_wallet"}),
        "wallet_credentials": json.dumps({"key": "government_wallet_key"}),
        "pool": pool_["handle"],
        "role": "TRUST_ANCHOR",
    }

    await getting_verinym(steward, government)

    print("==============================")
    print("==== NAA getting Verinym  ====")
    print("------------------------------")

    naa = {
        "name": "naa",
        "wallet_config": json.dumps({"id": "naa_wallet"}),
        "wallet_credentials": json.dumps({"key": "naa_wallet_key"}),
        "pool": pool_["handle"],
        "role": "TRUST_ANCHOR",
    }

    await getting_verinym(steward, naa)

    print("================================")
    print("== CBDC Bank getting Verinym  ==")
    print("--------------------------------")

    cbdcBank = {
        "name": "cbdcBank",
        "wallet_config": json.dumps({"id": "cbdcBank_wallet"}),
        "wallet_credentials": json.dumps({"key": "cbdcBank_wallet_key"}),
        "pool": pool_["handle"],
        "role": "TRUST_ANCHOR",
    }

    await getting_verinym(steward, cbdcBank)

    # -----------------------------------------------------
    # Government creates bonafideStudent schema

    print('"Government" -> Create "BonafideStudent" Schema')
    bonafideStudent = {
        "name": "BonafideStudent",
        "version": "1.2",
        "attributes": [
            "student_first_name",
            "student_last_name",
            "degree_name",
            "student_since_year",
            "cgpa",
        ],
    }
    (
        government["bonafideStudent_schema_id"],
        government["bonafideStudent_schema"],
    ) = await anoncreds.issuer_create_schema(
        government["did"],
        bonafideStudent["name"],
        bonafideStudent["version"],
        json.dumps(bonafideStudent["attributes"]),
    )

    print(government["bonafideStudent_schema"])
    bonafideStudent_schema_id = government["bonafideStudent_schema_id"]

    print(government["bonafideStudent_schema_id"], government["bonafideStudent_schema"])

    print('"Government" -> Send "BonafideStudent" Schema to Ledger')

    schema_request = await ledger.build_schema_request(
        government["did"], government["bonafideStudent_schema"]
    )
    await ledger.sign_and_submit_request(
        government["pool"], government["wallet"], government["did"], schema_request
    )

    # -----------------------------------------------------
    # NAA will create a credential definition

    print("\n\n==============================")
    print("=== naa Credential Definition Setup ==")
    print("------------------------------")

    print('"naa" -> Get "BonafideStudent" Schema from Ledger')

    # Get Schema from Ledger
    get_schema_request = await ledger.build_get_schema_request(
        naa["did"], bonafideStudent_schema_id
    )
    get_schema_response = await ensure_previous_request_applied(
        naa["pool"],
        get_schema_request,
        lambda response: response["result"]["data"] is not None,
    )
    (
        naa["bonafideStudent_schema_id"],
        naa["bonafideStudent_schema"],
    ) = await ledger.parse_get_schema_response(get_schema_response)

    # BonafideStudent credential definition
    print(
        '"naa" -> Create and store in Wallet "naa BonafideStudent" Credential Definition'
    )
    bonafideStudent_cred_def = {
        "tag": "TAG1",
        "type": "CL",
        "config": {"support_revocation": False},
    }
    (
        naa["bonafideStudent_cred_def_id"],
        naa["bonafideStudent_cred_def"],
    ) = await anoncreds.issuer_create_and_store_credential_def(
        naa["wallet"],
        naa["did"],
        naa["bonafideStudent_schema"],
        bonafideStudent_cred_def["tag"],
        bonafideStudent_cred_def["type"],
        json.dumps(bonafideStudent_cred_def["config"]),
    )

    print('"naa" -> Send  "naa BonafideStudent" Credential Definition to Ledger')

    cred_def_request = await ledger.build_cred_def_request(
        naa["did"], naa["bonafideStudent_cred_def"]
    )
    await ledger.sign_and_submit_request(
        naa["pool"], naa["wallet"], naa["did"], cred_def_request
    )
    print("\n\n>>>>>>>>>>>>>>>>>>>>>>.\n\n", naa["bonafideStudent_cred_def_id"])

    # -----------------------------------------------------
    # Government creates PropertyDetails schema

    print('"Government" -> Create "PropertyDetails" Schema')
    propertyDetails = {
        "name": "PropertyDetails",
        "version": "1.2",
        "attributes": [
            "owner_first_name",
            "owner_last_name",
            "address_of_property",
            "residing_since_year",
            "property_value_estimate",
        ],
    }
    (
        government["propertyDetails_schema_id"],
        government["propertyDetails_schema"],
    ) = await anoncreds.issuer_create_schema(
        government["did"],
        propertyDetails["name"],
        propertyDetails["version"],
        json.dumps(propertyDetails["attributes"]),
    )

    print(government["propertyDetails_schema"])
    propertyDetails_schema_id = government["propertyDetails_schema_id"]

    print(government["propertyDetails_schema_id"], government["propertyDetails_schema"])

    print('"Government" -> Send "PropertyDetails" Schema to Ledger')

    schema_request = await ledger.build_schema_request(
        government["did"], government["propertyDetails_schema"]
    )
    await ledger.sign_and_submit_request(
        government["pool"], government["wallet"], government["did"], schema_request
    )

    # -----------------------------------------------------
    # Government will create a credential definition

    print("\n\n==============================")
    print("=== Government Credential Definition Setup ==")
    print("------------------------------")

    print('"Government" -> Get "PropertyDetails" Schema from Ledger')

    # Get Schema from Ledger
    get_schema_request = await ledger.build_get_schema_request(
        government["did"], propertyDetails_schema_id
    )
    get_schema_response = await ensure_previous_request_applied(
        government["pool"],
        get_schema_request,
        lambda response: response["result"]["data"] is not None,
    )
    (
        government["propertyDetails_schema_id"],
        government["propertyDetails_schema"],
    ) = await ledger.parse_get_schema_response(get_schema_response)

    # PropertyDetails credential definition
    print(
        '"government" -> Create and store in Wallet "government PropertyDetails" Credential Definition'
    )
    propertyDetails_cred_def = {
        "tag": "TAG1",
        "type": "CL",
        "config": {"support_revocation": False},
    }
    (
        government["propertyDetails_cred_def_id"],
        government["propertyDetails_cred_def"],
    ) = await anoncreds.issuer_create_and_store_credential_def(
        government["wallet"],
        government["did"],
        government["propertyDetails_schema"],
        propertyDetails_cred_def["tag"],
        propertyDetails_cred_def["type"],
        json.dumps(propertyDetails_cred_def["config"]),
    )

    print(
        '"Government" -> Send  "government PropertyDetails" Credential Definition to Ledger'
    )

    cred_def_request = await ledger.build_cred_def_request(
        government["did"], government["propertyDetails_cred_def"]
    )
    await ledger.sign_and_submit_request(
        government["pool"], government["wallet"], government["did"], cred_def_request
    )
    print("\n\n>>>>>>>>>>>>>>>>>>>>>>.\n\n", government["propertyDetails_cred_def_id"])

    # ------------------------------------------------------------
    #  Rajesh getting BonafideStudent from NAA

    print("=======================================")
    print("=== Getting BonafideStudent with NAA ==")
    print("=======================================")

    print("======= Rajesh setup =========")
    print("------------------------------")

    rajesh = {
        "name": "Rajesh",
        "wallet_config": json.dumps({"id": "rajesh_wallet"}),
        "wallet_credentials": json.dumps({"key": "rajesh_wallet_key"}),
        "pool": pool_["handle"],
    }
    await create_wallet(rajesh)
    (rajesh["did"], rajesh["key"]) = await did.create_and_store_my_did(
        rajesh["wallet"], "{}"
    )

    # NAA creates bonafideStudent credential offer

    print('"naa" -> Create "BonafideStudent" Credential Offer for Rajesh')
    naa["bonafideStudent_cred_offer"] = await anoncreds.issuer_create_credential_offer(
        naa["wallet"], naa["bonafideStudent_cred_def_id"]
    )

    print('"naa" -> Send "BonafideStudent" Credential Offer to Rajesh')

    # Over Network
    rajesh["bonafideStudent_cred_offer"] = naa["bonafideStudent_cred_offer"]

    print(rajesh["bonafideStudent_cred_offer"])

    # Rajesh prepares a BonafideStudent credential request

    bonafideStudent_cred_offer_object = json.loads(rajesh["bonafideStudent_cred_offer"])

    rajesh["bonafideStudent_schema_id"] = bonafideStudent_cred_offer_object["schema_id"]
    rajesh["bonafideStudent_cred_def_id"] = bonafideStudent_cred_offer_object[
        "cred_def_id"
    ]

    print('"Rajesh" -> Create and store "Rajesh" Master Secret in Wallet')
    rajesh["master_secret_id"] = await anoncreds.prover_create_master_secret(
        rajesh["wallet"], None
    )

    print('"Rajesh" -> Get "naa BonafideStudent" Credential Definition from Ledger')
    (
        rajesh["naa_bonafideStudent_cred_def_id"],
        rajesh["naa_bonafideStudent_cred_def"],
    ) = await get_cred_def(
        rajesh["pool"], rajesh["did"], rajesh["bonafideStudent_cred_def_id"]
    )

    print('"Rajesh" -> Create "BonafideStudent" Credential Request for naa')
    (
        rajesh["bonafideStudent_cred_request"],
        rajesh["bonafideStudent_cred_request_metadata"],
    ) = await anoncreds.prover_create_credential_req(
        rajesh["wallet"],
        rajesh["did"],
        rajesh["bonafideStudent_cred_offer"],
        rajesh["naa_bonafideStudent_cred_def"],
        rajesh["master_secret_id"],
    )

    print('"Rajesh" -> Send "BonafideStudent" Credential Request to naa')

    # Over Network
    naa["bonafideStudent_cred_request"] = rajesh["bonafideStudent_cred_request"]

    # NAA issues credential to rajesh ----------------
    print('"naa" -> Create "BonafideStudent" Credential for Rajesh')
    naa["rajesh_bonafideStudent_cred_values"] = json.dumps(
        {
            "student_first_name": {
                "raw": "Rajesh",
                "encoded": "1139481716457488690172217916278103335",
            },
            "student_last_name": {
                "raw": "Kumar",
                "encoded": "5321642780241790123587902456789123452",
            },
            "degree_name": {
                "raw": "Pilot Training Programme",
                "encoded": "12434523576212321",
            },
            "student_since_year": {"raw": "2022", "encoded": "2022"},
            "cgpa": {"raw": "8", "encoded": "8"},
        }
    )
    naa["bonafideStudent_cred"], _, _ = await anoncreds.issuer_create_credential(
        naa["wallet"],
        naa["bonafideStudent_cred_offer"],
        naa["bonafideStudent_cred_request"],
        naa["rajesh_bonafideStudent_cred_values"],
        None,
        None,
    )

    print('"NAA" -> Send "BonafideStudent" Credential to Rajesh')
    print(naa["bonafideStudent_cred"])
    # Over the network
    rajesh["bonafideStudent_cred"] = naa["bonafideStudent_cred"]

    print('"Rajesh" -> Store "BonafideStudent" Credential from naa')
    _, rajesh["bonafideStudent_cred_def"] = await get_cred_def(
        rajesh["pool"], rajesh["did"], rajesh["bonafideStudent_cred_def_id"]
    )

    await anoncreds.prover_store_credential(
        rajesh["wallet"],
        None,
        rajesh["bonafideStudent_cred_request_metadata"],
        rajesh["bonafideStudent_cred"],
        rajesh["bonafideStudent_cred_def"],
        None,
    )

    print("\n\n>>>>>>>>>>>>>>>>>>>>>>.\n\n", rajesh["bonafideStudent_cred_def"])

    # ------------------------------------------------------------
    #  Rajesh getting PropertyDetails from naa

    print("==============================")
    print("=== Getting PropertyDetails with naa ==")
    print("==============================")

    # NAA creates PropertyDetails credential offer

    print('"Government" -> Create "PropertyDetails" Credential Offer for Rajesh')
    government[
        "propertyDetails_cred_offer"
    ] = await anoncreds.issuer_create_credential_offer(
        government["wallet"], government["propertyDetails_cred_def_id"]
    )

    print('"Government" -> Send "PropertyDetails" Credential Offer to Rajesh')

    # Over Network
    rajesh["propertyDetails_cred_offer"] = government["propertyDetails_cred_offer"]

    print(rajesh["propertyDetails_cred_offer"])

    # Rajesh prepares a PropertyDetails credential request

    propertyDetails_cred_offer_object = json.loads(rajesh["propertyDetails_cred_offer"])

    rajesh["propertyDetails_schema_id"] = propertyDetails_cred_offer_object["schema_id"]
    rajesh["propertyDetails_cred_def_id"] = propertyDetails_cred_offer_object[
        "cred_def_id"
    ]

    print(
        '"Rajesh" -> Get "government PropertyDetails" Credential Definition from Ledger'
    )
    (
        rajesh["government_propertyDetails_cred_def_id"],
        rajesh["government_propertyDetails_cred_def"],
    ) = await get_cred_def(
        rajesh["pool"], rajesh["did"], rajesh["propertyDetails_cred_def_id"]
    )

    print('"Rajesh" -> Create "PropertyDetails" Credential Request for government')
    (
        rajesh["propertyDetails_cred_request"],
        rajesh["propertyDetails_cred_request_metadata"],
    ) = await anoncreds.prover_create_credential_req(
        rajesh["wallet"],
        rajesh["did"],
        rajesh["propertyDetails_cred_offer"],
        rajesh["government_propertyDetails_cred_def"],
        rajesh["master_secret_id"],
    )

    print('"Rajesh" -> Send "PropertyDetails" Credential Request to government')

    # Over Network
    government["propertyDetails_cred_request"] = rajesh["propertyDetails_cred_request"]

    # Government issues credential to Rajesh ----------------
    print('"government" -> Create "PropertyDetails" Credential for Rajesh')
    government["rajesh_propertyDetails_cred_values"] = json.dumps(
        {
            "owner_first_name": {
                "raw": "Rajesh",
                "encoded": "1139481716457488690172217916278103335",
            },
            "owner_last_name": {
                "raw": "Kumar",
                "encoded": "5321642780241790123587902456789123452",
            },
            "address_of_property": {
                "raw": "“Malancha Road, Kharagpur",
                "encoded": "12434523576212321",
            },
            "residing_since_year": {"raw": "2010", "encoded": "2010"},
            "property_value_estimate": {"raw": "2000000", "encoded": "2000000"},
        }
    )
    government["propertyDetails_cred"], _, _ = await anoncreds.issuer_create_credential(
        government["wallet"],
        government["propertyDetails_cred_offer"],
        government["propertyDetails_cred_request"],
        government["rajesh_propertyDetails_cred_values"],
        None,
        None,
    )

    print('"government" -> Send "PropertyDetails" Credential to Rajesh')
    print(government["propertyDetails_cred"])
    # Over the network
    rajesh["propertyDetails_cred"] = government["propertyDetails_cred"]

    print('"Rajesh" -> Store "PropertyDetails" Credential from government')
    _, rajesh["propertyDetails_cred_def"] = await get_cred_def(
        rajesh["pool"], rajesh["did"], rajesh["propertyDetails_cred_def_id"]
    )

    await anoncreds.prover_store_credential(
        rajesh["wallet"],
        None,
        rajesh["propertyDetails_cred_request_metadata"],
        rajesh["propertyDetails_cred"],
        rajesh["propertyDetails_cred_def"],
        None,
    )

    print("\n\n>>>>>>>>>>>>>>>>>>>>>>.\n\n", rajesh["propertyDetails_cred_def"])

    # Verifiable Presentation

    # Creating application request (presentation request) --- validator - CBDCBank
    print('"CBDCBank" -> Create "Loan-Application" Proof Request')
    nonce = await anoncreds.generate_nonce()
    cbdcBank["loan_application_proof_request"] = json.dumps(
        {
            "nonce": nonce,
            "name": "Loan-Application",
            "version": "0.1",
            "requested_attributes": {
                "attr1_referent": {"name": "student_first_name"},
                "attr2_referent": {"name": "student_last_name"},
                "attr3_referent": {
                    "name": "degree_name",
                    "restrictions": [
                        {"cred_def_id": naa["bonafideStudent_cred_def_id"]}
                    ],
                },
                "attr4_referent": {
                    "name": "address_of_property",
                    "restrictions": [
                        {"cred_def_id": government["propertyDetails_cred_def_id"]}
                    ],
                },
                "attr5_referent": {
                    "name": "residing_since_year",
                    "restrictions": [
                        {"cred_def_id": government["propertyDetails_cred_def_id"]}
                    ],
                },
            },
            "requested_predicates": {
                "predicate1_referent": {
                    "name": "cgpa",
                    "p_type": ">",
                    "p_value": 6,
                    "restrictions": [
                        {"cred_def_id": naa["bonafideStudent_cred_def_id"]}
                    ],
                },
                "predicate2_referent": {
                    "name": "student_since_year",
                    "p_type": ">=",
                    "p_value": 2019,
                    "restrictions": [
                        {"cred_def_id": naa["bonafideStudent_cred_def_id"]}
                    ],
                },
                "predicate3_referent": {
                    "name": "student_since_year",
                    "p_type": "<=",
                    "p_value": 2023,
                    "restrictions": [
                        {"cred_def_id": naa["bonafideStudent_cred_def_id"]}
                    ],
                },
                "predicate4_referent": {
                    "name": "property_value_estimate",
                    "p_type": ">",
                    "p_value": 800000,
                    "restrictions": [
                        {"cred_def_id": government["propertyDetails_cred_def_id"]}
                    ],
                },
            },
        }
    )

    print('"CBDCBank" -> Send "Loan-Application" Proof Request to Rajesh')

    # Over Network
    rajesh["loan_application_proof_request"] = cbdcBank[
        "loan_application_proof_request"
    ]

    print(rajesh["loan_application_proof_request"])

    # Rajesh prepares the presentation ===================================

    print("\n\n>>>>>>>>>>>>>>>>>>>>>>.\n\n", rajesh["loan_application_proof_request"])

    print('"Rajesh" -> Get credentials for "Loan-Application" Proof Request')

    search_for_loan_application_proof_request = (
        await anoncreds.prover_search_credentials_for_proof_req(
            rajesh["wallet"], rajesh["loan_application_proof_request"], None
        )
    )

    print("---------------------------")
    print(search_for_loan_application_proof_request)
    print("---------------------------")

    cred_for_attr1 = await get_credential_for_referent(
        search_for_loan_application_proof_request, "attr1_referent"
    )
    cred_for_attr2 = await get_credential_for_referent(
        search_for_loan_application_proof_request, "attr2_referent"
    )
    cred_for_attr3 = await get_credential_for_referent(
        search_for_loan_application_proof_request, "attr3_referent"
    )
    cred_for_attr4 = await get_credential_for_referent(
        search_for_loan_application_proof_request, "attr4_referent"
    )
    cred_for_attr5 = await get_credential_for_referent(
        search_for_loan_application_proof_request, "attr5_referent"
    )
    cred_for_predicate1 = await get_credential_for_referent(
        search_for_loan_application_proof_request, "predicate1_referent"
    )
    cred_for_predicate2 = await get_credential_for_referent(
        search_for_loan_application_proof_request, "predicate2_referent"
    )
    cred_for_predicate3 = await get_credential_for_referent(
        search_for_loan_application_proof_request, "predicate3_referent"
    )
    cred_for_predicate4 = await get_credential_for_referent(
        search_for_loan_application_proof_request, "predicate4_referent"
    )

    print("---------------------------")
    print(cred_for_attr1)
    print("---------------------------")

    await anoncreds.prover_close_credentials_search_for_proof_req(
        search_for_loan_application_proof_request
    )

    rajesh["creds_for_loan_application_proof"] = {
        cred_for_attr1["referent"]: cred_for_attr1,
        cred_for_attr2["referent"]: cred_for_attr2,
        cred_for_attr3["referent"]: cred_for_attr3,
        cred_for_attr4["referent"]: cred_for_attr4,
        cred_for_attr5["referent"]: cred_for_attr5,
        cred_for_predicate1["referent"]: cred_for_predicate1,
        cred_for_predicate2["referent"]: cred_for_predicate2,
        cred_for_predicate3["referent"]: cred_for_predicate3,
        cred_for_predicate4["referent"]: cred_for_predicate4,
    }

    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(rajesh["creds_for_loan_application_proof"])

    (
        rajesh["schemas_for_loan_application"],
        rajesh["cred_defs_for_loan_application"],
        rajesh["revoc_states_for_loan_application"],
    ) = await prover_get_entities_from_ledger(
        rajesh["pool"],
        rajesh["did"],
        rajesh["creds_for_loan_application_proof"],
        rajesh["name"],
    )

    print('"Rajesh" -> Create "Loan-Application" Proof')
    rajesh["loan_application_requested_creds"] = json.dumps(
        {
            "self_attested_attributes": {
                "attr1_referent": "Rajesh",
                "attr2_referent": "Kumar",
            },
            "requested_attributes": {
                "attr3_referent": {
                    "cred_id": cred_for_attr3["referent"],
                    "revealed": True,
                },
                "attr4_referent": {
                    "cred_id": cred_for_attr4["referent"],
                    "revealed": True,
                },
                "attr5_referent": {
                    "cred_id": cred_for_attr5["referent"],
                    "revealed": True,
                },
            },
            "requested_predicates": {
                "predicate1_referent": {"cred_id": cred_for_predicate1["referent"]},
                "predicate2_referent": {"cred_id": cred_for_predicate2["referent"]},
                "predicate3_referent": {"cred_id": cred_for_predicate3["referent"]},
                "predicate4_referent": {"cred_id": cred_for_predicate4["referent"]},
            },
        }
    )

    rajesh["loan_application_proof"] = await anoncreds.prover_create_proof(
        rajesh["wallet"],
        rajesh["loan_application_proof_request"],
        rajesh["loan_application_requested_creds"],
        rajesh["master_secret_id"],
        rajesh["schemas_for_loan_application"],
        rajesh["cred_defs_for_loan_application"],
        rajesh["revoc_states_for_loan_application"],
    )
    print(rajesh["loan_application_proof"])

    print('"Rajesh" -> Send "Loan-Application" Proof to cbdcBank')

    # Over Network
    cbdcBank["loan_application_proof"] = rajesh["loan_application_proof"]

    # Validating the verifiable presentation
    loan_application_proof_object = json.loads(cbdcBank["loan_application_proof"])

    (
        cbdcBank["schemas_for_loan_application"],
        cbdcBank["cred_defs_for_loan_application"],
        cbdcBank["revoc_ref_defs_for_loan_application"],
        cbdcBank["revoc_regs_for_loan_application"],
    ) = await verifier_get_entities_from_ledger(
        cbdcBank["pool"],
        cbdcBank["did"],
        loan_application_proof_object["identifiers"],
        cbdcBank["name"],
    )

    print('"CBDCBank" -> Verify "Loan-Application" Proof from Rajesh')

    assert await anoncreds.verifier_verify_proof(
        cbdcBank["loan_application_proof_request"],
        cbdcBank["loan_application_proof"],
        cbdcBank["schemas_for_loan_application"],
        cbdcBank["cred_defs_for_loan_application"],
        cbdcBank["revoc_ref_defs_for_loan_application"],
        cbdcBank["revoc_regs_for_loan_application"],
    )


loop = asyncio.get_event_loop()
loop.run_until_complete(run())
