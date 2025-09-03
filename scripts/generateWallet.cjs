const { ethers } = require("ethers");

function generateWallet() {
  const wallet = ethers.Wallet.createRandom();
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