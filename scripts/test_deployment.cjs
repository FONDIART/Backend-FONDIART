const hre = require("hardhat");
require("dotenv").config();

async function main() {
  console.log("--- Starting Sepolia Deployment Test ---");

  // 1. Log network configuration
  const network = hre.config.networks[hre.network.name];
  console.log(`Network: ${hre.network.name}`);
  console.log(`URL: ${network.url}`);
  if (!network.url) {
    console.error("ERROR: RPC URL is not configured. Check your hardhat.config.js and .env file.");
    process.exit(1);
  }

  // 2. Get deployer and log balance
  const [deployer] = await hre.ethers.getSigners();
  console.log(`Deployer Address: ${deployer.address}`);
  
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  const balanceInEth = hre.ethers.formatEther(balance);
  console.log(`Deployer Balance: ${balanceInEth} ETH`);

  if (balance === 0n) {
    console.error("ERROR: Deployer account has no ETH. Please fund the account.");
    process.exit(1);
  }

  // 3. Attempt to deploy the contract
  console.log("Deploying CuadroToken contract...");
  const CuadroToken = await hre.ethers.getContractFactory("CuadroToken");
  const cuadroToken = await CuadroToken.deploy(
    "Test Artwork",
    "Test Artist",
    "2025",
    deployer.address, // Artist address
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8", // Platform address
    1000,
    "TEST"
  );

  await cuadroToken.waitForDeployment();

  console.log("--- ✅ SUCCESS! ---");
  console.log(`Contract deployed to: ${cuadroToken.target}`);
  console.log(`Verify on Sepolia Etherscan: https://sepolia.etherscan.io/address/${cuadroToken.target}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("--- ❌ DEPLOYMENT FAILED ---");
    console.error(error);
    process.exit(1);
  });
