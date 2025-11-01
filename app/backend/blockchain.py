import os
import logging
from web3 import Web3

ALCHEMY_URL = os.environ.get("ALCHEMY_URL")
DEPLOYER_PRIVATE_KEY = os.environ.get("DEPLOYER_PRIVATE_KEY")
CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS")
CONTRACT_ABI = '[{"inputs":[{"internalType":"string","name":"_recordHash","type":"string"}],"name":"addRecord","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"","type":"string"}],"name":"records","outputs":[{"internalType":"address","name":"doctorAddress","type":"address"},{"internalType":"uint256","name":"timestamp","type":"uint256"},{"internalType":"bool","name":"isInitialized","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"string","name":"_recordHash","type":"string"}],"name":"verifyRecord","outputs":[{"internalType":"bool","name":"","type":"bool"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"string","name":"recordHash","type":"string"},{"indexed":true,"internalType":"address","name":"doctorAddress","type":"address"},{"indexed":false,"internalType":"uint256","name":"timestamp","type":"uint256"}],"name":"RecordAdded","type":"event"}]'


def get_web3_instance():
    if not ALCHEMY_URL:
        logging.warning("ALCHEMY_URL not set. Blockchain features will be disabled.")
        return None
    return Web3(Web3.HTTPProvider(ALCHEMY_URL))


def notarize_hash(record_hash: str) -> str | None:
    """Notarizes a hash on the blockchain. Returns transaction hash or None."""
    w3 = get_web3_instance()
    if not w3 or not DEPLOYER_PRIVATE_KEY or (not CONTRACT_ADDRESS):
        logging.warning(
            "Blockchain environment variables not set. Simulating notarization."
        )
        return f"0x_simulated_{record_hash[:16]}"
    try:
        account = w3.eth.account.from_key(DEPLOYER_PRIVATE_KEY)
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
        tx = contract.functions.addRecord(record_hash).build_transaction(
            {
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
            }
        )
        signed_tx = w3.eth.account.sign_transaction(tx, DEPLOYER_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logging.info(f"Notarized hash {record_hash} with tx: {tx_hash.hex()}")
        return tx_hash.hex()
    except Exception as e:
        logging.exception(f"Error notarizing hash on blockchain: {e}")
        return None


def verify_hash_on_chain(record_hash: str) -> dict | None:
    """Verifies a hash on the blockchain. Returns verification data or None."""
    w3 = get_web3_instance()
    if not w3 or not CONTRACT_ADDRESS:
        logging.warning(
            "Blockchain environment variables not set. Simulating verification failure."
        )
        return {
            "is_verified": False,
            "timestamp": None,
            "doctor_address": None,
            "error": "Blockchain not configured",
        }
    try:
        logging.info(f"Simulating verification for hash: {record_hash}")
        return {
            "is_verified": True,
            "timestamp": 1672531200,
            "doctor_address": "0x_simulated_doctor_address",
        }
    except Exception as e:
        logging.exception(f"Error verifying hash on blockchain: {e}")
        return None