const hre = require("hardhat");

async function main() {
  try {
    console.log("Attempting to connect to Sepolia...");
    
    // Get the provider as configured for Sepolia in hardhat.config.js
    const provider = hre.ethers.provider;
    
    const network = await provider.getNetwork();
    console.log("Successfully connected to network:", network.name);
    console.log("Chain ID:", network.chainId.toString());
    
    const blockNumber = await provider.getBlockNumber();
    console.log("Current block number:", blockNumber);
    
    const signer = new hre.ethers.Wallet(process.env.PRIVATE_KEY, provider);
    console.log("Signer address:", signer.address);

    const balance = await provider.getBalance(signer.address);
    console.log("Account balance:", hre.ethers.formatEther(balance), "ETH");

    if (hre.ethers.formatEther(balance) === "0.0") {
        console.warn("\nWarning: The wallet associated with your PRIVATE_KEY has 0 ETH. You will not be able to pay for gas to deploy contracts.");
    }

    console.log("\n✅ Sepolia connection test successful!");

  } catch (error) {
    console.error("\n❌ Sepolia connection test failed.");
    if (error.message.includes("invalid api key")) {
        console.error("Error Details: Your SEPOLIA_RPC_URL is likely incorrect or your API key for the RPC service (Infura, Alchemy) is invalid.");
    } else if (error.message.includes("bad response")) {
        console.error("Error Details: The RPC server at SEPOLIA_RPC_URL is not responding correctly. The URL might be wrong or the service could be down.");
    } else if (error.message.includes("invalid private key")) {
        console.error("Error Details: The PRIVATE_KEY in your .env file is invalid. It should be a 64-character hexadecimal string, without the '0x' prefix.");
    } else {
        console.error("An unexpected error occurred:", error.message);
    }
    process.exit(1);
  }
}

main()
  .then(() => process.exit(0))
  .catch(() => process.exit(1));
