# Fondiart Backend

Este es el backend para la aplicación Fondiart, una plataforma para tokenizar obras de arte. Incluye un backend de Django y un contrato inteligente en una blockchain compatible con Ethereum.

## Características

- Tokeniza obras de arte utilizando un contrato inteligente ERC20.
- Distribuye tokens al artista y a la plataforma.
- Certifica la propiedad de la obra de arte mediante la transferencia de tokens.
- Provee una API REST para interactuar con el contrato inteligente.

## Tecnologías Utilizadas

- **Backend:** Django, Django REST Framework
- **Blockchain:** Solidity, Hardhat, Ethers.js
- **Librerías de Python:** `web3.py`
- **Librerías de Node.js:** `@openzeppelin/contracts`, `ethers`

## Prerrequisitos

- Python 3.13 o superior
- Node.js y npm
- Pip (instalador de paquetes de Python)

## Instalación y Configuración

1. **Clona el repositorio:**
   ```bash
   git clone <url-del-repositorio>
   cd backend-Fondiart
   ```

2. **Crea y activa un entorno virtual de Python:**
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```

3. **Instala las dependencias de Python:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Instala las dependencias de Node.js:**
   ```bash
   npm install
   ```

## Ejecutando la Aplicación

1. **Inicia el nodo local de Hardhat:**
   En una terminal, ejecuta:
   ```bash
   npx hardhat node
   ```

2. **Despliega el contrato inteligente:**
   En una **nueva** terminal, ejecuta:
   ```bash
   npx hardhat run scripts/deploy_cuadro_token.cjs --network localhost
   ```
   **Importante:** Si vuelves a desplegar el contrato, obtendrás una nueva dirección. Deberás actualizar la variable `CONTRACT_ADDRESS` en el archivo `blockchain/cuadro_token_service.py` con la nueva dirección.

3. **Inicia el backend de Django:**
   En **otra nueva** terminal, ejecuta:
   ```bash
   python manage.py runserver
   ```

## Endpoints de la API

La API estará disponible en `http://127.0.0.1:8000/api/`.

- `GET /api/contract/info/`
  - Obtiene la información del contrato desplegado (nombre de la obra, autor, etc.).

- `POST /api/contract/distribuir/`
  - Ejecuta la distribución inicial de tokens al artista y a la plataforma.

- `POST /api/contract/certificar/`
  - Certifica la propiedad de la obra de arte transfiriendo los tokens a un nuevo dueño.
  - **Payload (JSON):**
    ```json
    {
      "nuevo_propietario": "<direccion-del-nuevo-propietario>",
      "cantidad": <cantidad-de-tokens>
    }
    ```

- `GET /api/contract/balance/?address=<direccion>`
  - Obtiene el balance de tokens de una dirección específica.
