import subprocess
import os
from django.conf import settings

def deploy_and_tokenize(artwork, admin_wallet_address):
    """
    Executes the simplified hardhat script to deploy a new CuadroToken contract.
    The contract now has hardcoded values for testing purposes.
    
    Args:
        artwork (Artwork): The artwork instance to tokenize (still required for context).
        admin_wallet_address (str): The wallet address of the admin user (no longer passed to the script).

    Returns:
        str: The address of the deployed smart contract.
        
    Raises:
        subprocess.CalledProcessError: If the script execution fails.
        Exception: If the contract address cannot be found in the script's output.
    """
    
    # --- Script Arguments ---
    # The script is now simplified and does not require arguments.
    args = [
        "npx",
        "hardhat",
        "run",
        "scripts/deploy_cuadro_token.cjs",
        "--network",
        "sepolia"
    ]

    # Execute the script
    process = subprocess.run(
        args,
        capture_output=True,
        text=True,
        cwd=settings.BASE_DIR,
        check=True  # Raises CalledProcessError on non-zero exit codes
    )

    # The script is designed to print ONLY the contract address to stdout.
    contract_address = process.stdout.strip()
    
    # A simple validation to ensure we got something that looks like an address
    if not contract_address.startswith("0x") or len(contract_address) != 42:
        raise Exception(
            "Script executed, but the output was not a valid contract address.\n"
            f"Stdout: {process.stdout}\n"
            f"Stderr: {process.stderr}"
        )

    return contract_address
