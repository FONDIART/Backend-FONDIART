require('dotenv').config({ path: '../.env' });
const { ethers } = require("ethers");

function generateWallet() {
  let provider;
  if (process.env.SEPOLIA_RPC_URL) {
    provider = new ethers.JsonRpcProvider(process.env.SEPOLIA_RPC_URL);
  }

  let wallet = ethers.Wallet.createRandom();
  if (provider) {
    wallet = wallet.connect(provider);
  }

  return {
    privateKey: wallet.privateKey,
    address: wallet.address,
  };
}

// Check if this script is being run directly from the command line
if (require.main === module) {
  const wallet = generateWallet();
  console.log(JSON.stringify(wallet));
}

module.exports = { generateWallet };