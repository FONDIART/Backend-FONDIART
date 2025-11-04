

import subprocess
import os
import re
from django.conf import settings
from fondiart_api.models import User, Wallet, Artwork

def deploy_and_tokenize(artwork, admin_wallet_address):
    """
    Executes the hardhat script to deploy a new CuadroToken contract.
    """
    try:
        artist_wallet = Wallet.objects.get(user_id=artwork.artist.id)
    except Wallet.DoesNotExist:
        raise Exception(f"Wallet for artist {artwork.artist.name} not found.")

    autor = artwork.artist.name
    
    artist_name_parts = autor.split()
    if len(artist_name_parts) > 1:
        symbol_base = artist_name_parts[-1][0] + artist_name_parts[0][0]
    else:
        symbol_base = autor[0:2] if len(autor) > 1 else autor + "X"
    
    artwork_count = Artwork.objects.filter(artist=artwork.artist).count()
    token_symbol = f"{symbol_base.upper()}{artwork_count}"

    script_env = os.environ.copy()
    node_path = "/Users/jorgeantoniosegovia/.nvm/versions/node/v24.4.0/bin"
    script_env["PATH"] = node_path + os.pathsep + script_env.get("PATH", "")
    script_env["NOMBRE_CUADRO"] = artwork.title
    script_env["AUTOR"] = autor
    script_env["ANIO_CREACION"] = str(artwork.createdAt.year)
    script_env["ARTISTA_ADDRESS"] = artist_wallet.address
    script_env["PLATAFORMA_ADDRESS"] = admin_wallet_address
    script_env["TOTAL_TOKENS"] = str(artwork.fractionsTotal)
    script_env["TOKEN_SYMBOL"] = token_symbol

    args = [
        "/Users/jorgeantoniosegovia/.nvm/versions/node/v24.4.0/bin/npx",
        "hardhat",
        "run",
        "scripts/deploy_cuadro_token.cjs",
        "--network",
        "sepolia"
    ]

    process = subprocess.run(
        args,
        capture_output=True,
        text=True,
        cwd=settings.BASE_DIR,
        check=True,
        env=script_env
    )

    # Buscar la dirección del contrato en la salida del script
    match = re.search(r"(0x[a-fA-F0-9]{40})", process.stdout)
    if not match:
        raise Exception(f"Could not find contract address in script output.\nStdout: {process.stdout}\nStderr: {process.stderr}")

    contract_address = match.group(1)
    return contract_address

def transfer_tokens(contract_address, to_address, amount):
    """
    Executes the hardhat script to transfer tokens from the contract's holdings.
    """
    script_env = os.environ.copy()
    node_path = "/Users/jorgeantoniosegovia/.nvm/versions/node/v24.4.0/bin"
    script_env["PATH"] = node_path + os.pathsep + script_env.get("PATH", "")
    script_env["CONTRACT_ADDRESS"] = contract_address
    script_env["TO_ADDRESS"] = to_address
    amount_in_wei = str(amount * (10**18))
    script_env["AMOUNT"] = amount_in_wei

    args = [
        "/Users/jorgeantoniosegovia/.nvm/versions/node/v24.4.0/bin/npx",
        "hardhat",
        "run",
        "scripts/transfer_tokens.cjs",
        "--network",
        "sepolia"
    ]

    process = subprocess.run(
        args,
        capture_output=True,
        text=True,
        cwd=settings.BASE_DIR,
        check=True,
        env=script_env
    )

    return process.stdout


