const hre = require("hardhat");

async function main() {
  const [nombreCuadro, autor, anioCreacion, artistaAddress, plataformaAddress, totalTokens, tokenSymbol] = process.argv.slice(2);

  if (!nombreCuadro || !autor || !anioCreacion || !artistaAddress || !plataformaAddress || !totalTokens || !tokenSymbol) {
    console.error("Usage: node scripts/deploy_cuadro_token.cjs <nombreCuadro> <autor> <anioCreacion> <artistaAddress> <plataformaAddress> <totalTokens> <tokenSymbol>");
    process.exit(1);
  }

  const CuadroToken = await hre.ethers.getContractFactory("CuadroToken");
  
  // Desplegamos el contrato con los datos del cuadro
  const cuadroToken = await CuadroToken.deploy(
    nombreCuadro,
    autor,
    anioCreacion,
    artistaAddress,
    plataformaAddress,
    parseInt(totalTokens),
    tokenSymbol
  );

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