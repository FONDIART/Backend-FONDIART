const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);

  const ArtworkNFT = await hre.ethers.getContractFactory("ArtworkNFT");
  const artworkNFT = await ArtworkNFT.deploy("ArtworkCertificate", "ARTC", deployer.address);

  await artworkNFT.waitForDeployment();

  console.log("ArtworkNFT deployed to:", artworkNFT.target);
  return artworkNFT.target;
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
