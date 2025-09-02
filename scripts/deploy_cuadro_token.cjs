const hre = require("hardhat");

async function main() {
  const [deployer, artista, plataforma] = await hre.ethers.getSigners();

  console.log("Deploying contracts with the account:", deployer.address);

  const CuadroToken = await hre.ethers.getContractFactory("CuadroToken");
  const cuadroToken = await CuadroToken.deploy(
    artista.address,
    plataforma.address,
    "Mona Lisa",
    "Leonardo da Vinci",
    "1503",
    "Mona Lisa Token",
    "MLT"
  );

  console.log("CuadroToken deployed to:", cuadroToken.target);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
