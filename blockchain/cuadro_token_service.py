import json
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# Sepolia RPC URL from .env file
SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL")
web3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))

# Deployed contract address - IMPORTANT: This needs to be updated with the address of the contract deployed on Sepolia
CONTRACT_ADDRESS = "0xFD471836031dc5108809D173A067e8486B9047A3"

# Private key from .env file for signing transactions
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
owner = web3.eth.account.from_key(PRIVATE_KEY).address


# Absolute path to the contract ABI
ABI_PATH = "/Users/jorgeantoniosegovia/codigo/backend-Fondiart/artifacts/contracts/Tokenizar_Obra.sol/CuadroToken.json"

def get_contract():
    with open(ABI_PATH) as f:
        artifact = json.load(f)
        abi = artifact['abi']
    
    contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
    return contract

def get_info():
    contract = get_contract()
    info = {
        "nombre_cuadro": contract.functions.nombreCuadro().call(),
        "autor": contract.functions.autor().call(),
        "anio_creacion": contract.functions.anioCreacion().call(),
        "artista": str(contract.functions.artista().call()),
        "plataforma": str(contract.functions.plataforma().call()),
        "total_supply": str(contract.functions.totalSupply().call()),
    }
    return info

def distribuir_tokens():
    contract = get_contract()
    
    nonce = web3.eth.get_transaction_count(owner)
    tx = contract.functions.distribuirTokensIniciales().build_transaction({
        'from': owner,
        'nonce': nonce,
        'gas': 2000000,
        'gasPrice': web3.eth.gas_price,
    })
    
    signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def certificar_propiedad(nuevo_propietario, cantidad):
    contract = get_contract()

    nonce = web3.eth.get_transaction_count(owner)
    tx = contract.functions.certificarPropiedad(nuevo_propietario, cantidad).build_transaction({
        'from': owner,
        'nonce': nonce,
        'gas': 2000000,
        'gasPrice': web3.eth.gas_price,
    })

    signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def get_balance(address):
    contract = get_contract()
    balance = contract.functions.balanceOf(address).call()
    return str(balance)
