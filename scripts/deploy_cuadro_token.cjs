const hre = require("hardhat");

async function main() {
  // Leer parámetros desde variables de entorno
  const {
    NOMBRE_CUADRO,
    AUTOR,
    ANIO_CREACION,
    ARTISTA_ADDRESS,
    PLATAFORMA_ADDRESS,
    TOTAL_TOKENS,
    TOKEN_SYMBOL
  } = process.env;

  if (!NOMBRE_CUADRO || !AUTOR || !ANIO_CREACION || !ARTISTA_ADDRESS || !PLATAFORMA_ADDRESS || !TOTAL_TOKENS || !TOKEN_SYMBOL) {
    console.error("Error: Missing one or more required environment variables.");
    console.error("Required: NOMBRE_CUADRO, AUTOR, ANIO_CREACION, ARTISTA_ADDRESS, PLATAFORMA_ADDRESS, TOTAL_TOKENS, TOKEN_SYMBOL");
    process.exit(1);
  }

  const CuadroToken = await hre.ethers.getContractFactory("CuadroToken");
  
  // Desplegamos el contrato con los datos del cuadro
  const cuadroToken = await CuadroToken.deploy(
    NOMBRE_CUADRO,
    AUTOR,
    ANIO_CREACION,
    ARTISTA_ADDRESS,
    PLATAFORMA_ADDRESS,
    parseInt(TOTAL_TOKENS),
    TOKEN_SYMBOL
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