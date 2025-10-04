const hre = require("hardhat");
require("dotenv").config();

async function main() {
  const { CONTRACT_ADDRESS, TO_ADDRESS, AMOUNT } = process.env;

  if (!CONTRACT_ADDRESS || !TO_ADDRESS || !AMOUNT) {
    console.error("Error: Missing required environment variables: CONTRACT_ADDRESS, TO_ADDRESS, AMOUNT");
    process.exit(1);
  }

  console.log(`Attempting to transfer ${AMOUNT} tokens from contract ${CONTRACT_ADDRESS} to ${TO_ADDRESS}...`);

  const CuadroToken = await hre.ethers.getContractFactory("CuadroToken");
  const cuadroToken = await CuadroToken.attach(CONTRACT_ADDRESS);

  // The amount should be in the smallest unit (wei)
  // The service will handle the conversion, so we expect the correct unit here.
  const tx = await cuadroToken.enviarTokens(TO_ADDRESS, AMOUNT);
  
  console.log("Transaction sent. Waiting for confirmation...");
  await tx.wait();

  console.log("--- ✅ SUCCESS! ---");
  console.log(`Transaction successful. Hash: ${tx.hash}`);
  console.log(`Verify on Sepolia Etherscan: https://sepolia.etherscan.io/tx/${tx.hash}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("--- ❌ TRANSACTION FAILED ---");
    console.error(error);
    process.exit(1);
  });
