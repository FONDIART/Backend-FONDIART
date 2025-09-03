import json
from web3 import Web3

# Hardhat node URL
GANACHE_URL = "http://127.0.0.1:8545"
web3 = Web3(Web3.HTTPProvider(GANACHE_URL))

# Deployed contract address
CONTRACT_ADDRESS = "0x9A676e781A523b5d0C0e43731313A708CB607508"

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
    # The owner is the deployer of the contract, which is the first account in Hardhat
    owner = web3.eth.accounts[0]
    tx_hash = contract.functions.distribuirTokensIniciales().transact({'from': owner})
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def certificar_propiedad(nuevo_propietario, cantidad):
    contract = get_contract()
    owner = web3.eth.accounts[0]
    tx_hash = contract.functions.certificarPropiedad(nuevo_propietario, cantidad).transact({'from': owner})
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def get_balance(address):
    contract = get_contract()
    balance = contract.functions.balanceOf(address).call()
    return str(balance)
