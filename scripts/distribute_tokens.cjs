const hre = require("hardhat");

async function main() {
  const contractAddress = "0x5FbDB2315678afecb367f032d93F642f64180aa3";
  const cuadroToken = await hre.ethers.getContractAt("CuadroToken", contractAddress);

  console.log("Calling distribuirTokensIniciales...");
  const tx = await cuadroToken.distribuirTokensIniciales();
  await tx.wait();
  console.log("Tokens distributed successfully.");

  const [deployer, artista, plataforma] = await hre.ethers.getSigners();

  const deployerBalance = await cuadroToken.balanceOf(deployer.address);
  const artistaBalance = await cuadroToken.balanceOf(artista.address);
  const plataformaBalance = await cuadroToken.balanceOf(plataforma.address);

  console.log("Deployer balance:", hre.ethers.formatEther(deployerBalance));
  console.log("Artista balance:", hre.ethers.formatEther(artistaBalance));
  console.log("Plataforma balance:", hre.ethers.formatEther(plataformaBalance));
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
