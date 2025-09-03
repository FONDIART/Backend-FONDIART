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

    constructor(
        address _artista,
        address _plataforma,
        string memory _nombreCuadro,
        string memory _autor,
        string memory _anioCreacion,
        string memory _nombreToken,
        string memory _simboloToken
    )
        ERC20(_nombreToken, _simboloToken)
        Ownable(msg.sender)
    {
        artista = _artista;
        plataforma = _plataforma;
        nombreCuadro = _nombreCuadro;
        autor = _autor;
        anioCreacion = _anioCreacion;
        
        // Acuña el 100% de los tokens a la dirección del propietario (deployer)
        uint256 totalTokensWei = 10000 * 10 ** decimals();
        _mint(owner(), totalTokensWei);
    }

    /**
     * @dev Permite al propietario distribuir el 50% de los tokens entre el artista y la plataforma.
     * El resto queda en la cuenta del propietario para futuras ventas.
     */
    function distribuirTokensIniciales() external onlyOwner {
        require(balanceOf(artista) == 0 && balanceOf(plataforma) == 0, "Los tokens ya han sido distribuidos.");
        
        uint256 totalTokens = balanceOf(owner());
        uint256 tokensArtista = (totalTokens * 60) / 100;
        uint256 tokensPlataforma = (totalTokens * 10) / 100;

        _transfer(owner(), artista, tokensArtista);
        _transfer(owner(), plataforma, tokensPlataforma);
    }

    /**
     * @dev Función para certificar la propiedad de la obra transfiriendo los tokens
     * al nuevo dueño. Esta transacción sirve como el certificado de propiedad.
     * Los datos de la subasta (fecha, monto, etc.) se gestionan fuera de la cadena de bloques
     * y se asocian a esta transacción.
     * @param _nuevoPropietario La dirección de la persona que compró la obra.
     * @param _cantidadTokens La cantidad de tokens que se le transfieren (por ejemplo, 10000).
     */
    function certificarPropiedad(address _nuevoPropietario, uint256 _cantidadTokens) external onlyOwner {
        require(_cantidadTokens > 0, "No se puede transferir 0 tokens");
        _transfer(owner(), _nuevoPropietario, _cantidadTokens);
    }
}