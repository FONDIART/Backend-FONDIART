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

    constructor()
        // Valores hardcodeados para el token ERC20
        ERC20("Mi Obra de Arte", "ART")
    {
        // Dirección de prueba para el artista (puedes cambiarla por la tuya)
        address _artista = 0x000000000000000000000000000000000000dEaD;
        // Dirección de prueba para la plataforma (puedes cambiarla por la tuya)
        address _plataforma = 0x000000000000000000000000000000000000dEaD;
        
        artista = _artista;
        plataforma = _plataforma;
        nombreCuadro = "Cuadro de Prueba";
        autor = "Artista de Prueba";
        anioCreacion = "2025";
        
        uint256 _totalTokens = 1000; // Total de tokens a crear
        uint256 totalTokensWei = _totalTokens * 10 ** decimals();
        uint256 tokensArtista = (totalTokensWei * 90) / 100;
        uint256 tokensPlataforma = totalTokensWei - tokensArtista; // 10%

        _mint(artista, tokensArtista);
        _mint(plataforma, tokensPlataforma);
    }
}
