// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract ArtworkNFT is ERC721, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    // Mapping from token ID to metadata URI
    mapping(uint256 => string) private _tokenURIs;

    // Event emitted when an NFT is minted
    event ArtworkNFTMinted(uint256 indexed tokenId, address indexed to, string tokenURI);

    constructor(string memory name, string memory symbol, address initialOwner) 
        ERC721(name, symbol)
        Ownable(initialOwner)
    {}

    // Function to mint a new NFT
    function mint(address to, string memory tokenURI) public onlyOwner returns (uint256) {
        _tokenIdCounter.increment();
        uint256 newItemId = _tokenIdCounter.current();
        _safeMint(to, newItemId);
        _setTokenURI(newItemId, tokenURI);
        emit ArtworkNFTMinted(newItemId, to, tokenURI);
        return newItemId;
    }

    // Internal function to set token URI
    function _setTokenURI(uint256 tokenId, string memory _tokenURI) internal virtual {
        _tokenURIs[tokenId] = _tokenURI;
    }

    // Override base URI function to return the stored URI
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        _requireOwned(tokenId);
        return _tokenURIs[tokenId];
    }

    // Function to transfer ownership of the NFT
    function transferNFT(address from, address to, uint256 tokenId) public onlyOwner {
        _transfer(from, to, tokenId);
    }
}
