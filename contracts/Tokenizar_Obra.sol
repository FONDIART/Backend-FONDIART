// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract CuadroToken is ERC20 {
    // Direcciones del artista y la plataforma
    address public artista;
    address public plataforma;

    // Variables para almacenar los metadatos del cuadro
    string public nombreCuadro;
    string public autor;
    string public anioCreacion;

    constructor(
        string memory _nombreCuadro,
        string memory _autor,
        string memory _anioCreacion,
        address _artista,
        address _plataforma,
        uint256 _totalTokens,
        string memory _tokenSymbol
    )
        ERC20(_nombreCuadro, _tokenSymbol)
    {
        artista = _artista;
        plataforma = _plataforma;
        nombreCuadro = _nombreCuadro;
        autor = _autor;
        anioCreacion = _anioCreacion;
        
        uint256 totalTokensWei = _totalTokens * 10 ** decimals();
        uint256 tokensArtista = (totalTokensWei * 90) / 100;
        uint256 tokensPlataforma = totalTokensWei - tokensArtista; // 10%

        _mint(artista, tokensArtista);
        _mint(plataforma, tokensPlataforma);
    }
}
