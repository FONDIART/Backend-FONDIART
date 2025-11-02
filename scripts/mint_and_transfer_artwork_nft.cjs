const hre = require("hardhat");
require("dotenv").config();

async function main() {
  const contractAddress = process.argv[2];
  const adminPrivateKey = process.argv[3];
  const buyerAddress = process.argv[4];
  const tokenURI = process.argv[5];

  if (!contractAddress || !adminPrivateKey || !buyerAddress || !tokenURI) {
    console.error("Error: Missing arguments. Usage: node mint_and_transfer_artwork_nft.cjs <contractAddress> <adminPrivateKey> <buyerAddress> <tokenURI>");
    process.exit(1);
  }

  const adminWallet = new hre.ethers.Wallet(adminPrivateKey, hre.ethers.provider);

  const ArtworkNFT = await hre.ethers.getContractFactory("ArtworkNFT", adminWallet);
  const artworkNFT = ArtworkNFT.attach(contractAddress);

  console.log(`Minting NFT to admin wallet (${adminWallet.address}) with URI: ${tokenURI}...`);
  const mintTx = await artworkNFT.mint(adminWallet.address, tokenURI);
  await mintTx.wait();
  const tokenId = (await artworkNFT._tokenIdCounter()).toString(); // Assuming _tokenIdCounter is public or has a getter
  console.log(`NFT minted with ID: ${tokenId}`);

  console.log(`Transferring NFT ${tokenId} from admin wallet (${adminWallet.address}) to buyer wallet (${buyerAddress})...`);
  const transferTx = await artworkNFT.transferNFT(adminWallet.address, buyerAddress, tokenId);
  await transferTx.wait();
  console.log(`NFT ${tokenId} transferred to ${buyerAddress}. Transaction hash: ${transferTx.hash}`);

  console.log(`--- ✅ SUCCESS! ---`);
  console.log(`NFT ID: ${tokenId}`);
  console.log(`Transaction hash: ${transferTx.hash}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("--- ❌ NFT OPERATION FAILED ---");
    console.error(error);
    process.exit(1);
  });
