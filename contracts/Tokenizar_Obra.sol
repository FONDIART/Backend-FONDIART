// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract CuadroToken is ERC20, Ownable {
    // Direcciones del artista y la plataforma
    address public artista;
    address public plataforma;

    // Variables para almacenar los metadatos del cuadro
    string public nombreCuadro;
    string public autor;
    string public anioCreacion;

    event TokensMinted(address indexed to, uint256 amount);

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
        Ownable(msg.sender)
    {
        require(_artista != address(0), "CuadroToken: La direccion del artista no puede ser la direccion cero.");
        require(_plataforma != address(0), "CuadroToken: La direccion de la plataforma no puede ser la direccion cero.");

        artista = _artista;
        plataforma = _plataforma;
        nombreCuadro = _nombreCuadro;
        autor = _autor;
        anioCreacion = _anioCreacion;
        
        uint256 totalTokensWei = _totalTokens * 10 ** decimals();
        uint256 tokensArtista = (totalTokensWei * 60) / 100;
        uint256 tokensPlataforma = (totalTokensWei * 10) / 100;
        uint256 tokensContrato = totalTokensWei - tokensArtista - tokensPlataforma; // 30%

        _mint(artista, tokensArtista);
        emit TokensMinted(artista, tokensArtista);

        _mint(plataforma, tokensPlataforma);
        emit TokensMinted(plataforma, tokensPlataforma);

        _mint(address(this), tokensContrato);
        emit TokensMinted(address(this), tokensContrato);
    }

    /**
     * @dev Transfiere una cantidad de tokens desde el contrato a una dirección específica.
     * Solo puede ser llamado por el owner del contrato.
     * @param _to La dirección a la que se enviarán los tokens.
     * @param _amount La cantidad de tokens a enviar (en la unidad más pequeña, como wei).
     */
    function enviarTokens(address _to, uint256 _amount) public onlyOwner {
        require(balanceOf(address(this)) >= _amount, "El contrato no tiene suficientes tokens.");
        _transfer(address(this), _to, _amount);
    }
}
