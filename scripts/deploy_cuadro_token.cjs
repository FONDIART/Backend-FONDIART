const hre = require("hardhat");

async function main() {
  const CuadroToken = await hre.ethers.getContractFactory("CuadroToken");
  
  // Desplegamos el contrato sin pasar argumentos
  const cuadroToken = await CuadroToken.deploy();

  await cuadroToken.waitForDeployment();

  // Imprimir solo la dirección del contrato
  console.log(cuadroToken.target);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });