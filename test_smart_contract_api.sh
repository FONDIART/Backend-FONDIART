#!/bin/bash

# Check for jq
if ! command -v jq &> /dev/null
then
    echo "jq could not be found. Please install it to run this script."
    exit
fi

# --- Configuration ---
DJANGO_SERVER_PORT=8000
HARDHAT_RPC_PORT=8545
CONTRACT_DEPLOY_SCRIPT="scripts/deploy_cuadro_token.cjs"
CUADRO_TOKEN_SERVICE_FILE="blockchain/cuadro_token_service.py"

# Hardhat default accounts (first one is the deployer/owner)
OWNER_ADDRESS="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
ARTIST_ADDRESS="0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
PLATFORM_ADDRESS="0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
CLIENT_1_ADDRESS="0x90F79bf6EB2c4f870365E785982E1f101E93b906"
CLIENT_2_ADDRESS="0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65"
CLIENT_3_ADDRESS="0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc"
TOKEN_AMOUNT_PER_CLIENT="1000000000000000000000" # 1000 tokens with 18 decimals

# --- Functions ---

start_hardhat_node() {
    echo "Starting Hardhat node..."
    npx hardhat node > /dev/null 2>&1 &
    HARDHAT_PID=$!
    echo "Hardhat node started with PID: $HARDHAT_PID"
    sleep 5 # Give it some time to start
}

deploy_contract() {
    echo "Deploying contract..."
    DEPLOY_OUTPUT=$(npx hardhat run "$CONTRACT_DEPLOY_SCRIPT" --network localhost 2>&1)
    CONTRACT_ADDRESS=$(echo "$DEPLOY_OUTPUT" | grep "CuadroToken deployed to:" | awk '{print $NF}')
    if [ -z "$CONTRACT_ADDRESS" ]; then
        echo "Error: Could not deploy contract or get address."
        echo "$DEPLOY_OUTPUT"
        exit 1
    fi
    echo "Contract deployed to: $CONTRACT_ADDRESS"
}

update_contract_address_in_service() {
    echo "Updating contract address in $CUADRO_TOKEN_SERVICE_FILE..."
    sed -i '' "s/CONTRACT_ADDRESS = ".*"/CONTRACT_ADDRESS = \"$CONTRACT_ADDRESS\"/" "$CUADRO_TOKEN_SERVICE_FILE"
    echo "Contract address updated."
}

start_django_server() {
    echo "Starting Django server..."
    python manage.py runserver > /dev/null 2>&1 &
    DJANGO_PID=$!
    echo "Django server started with PID: $DJANGO_PID"
    sleep 5 # Give it some time to start
}

register_and_login() {
    echo "Registering a new user and getting JWT token..."
    # Generate a random username and password
    USERNAME="testuser_$(date +%s)"
    EMAIL="$USERNAME@example.com"
    PASSWORD="password123"

    # Register the user
    REG_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d '{"email": "'$EMAIL'", "password": "'$PASSWORD'", "name": "Test User", "role": "buyer"}' "http://127.0.0.1:$DJANGO_SERVER_PORT/api/v1/auth/register/")
    
    # Extract the token
    JWT_TOKEN=$(echo "$REG_RESPONSE" | jq -r .token)

    if [ -z "$JWT_TOKEN" ] || [ "$JWT_TOKEN" == "null" ]; then
        echo "Error: Could not get JWT token."
        echo "Response: $REG_RESPONSE"
        exit 1
    fi
    echo "JWT token obtained."
}

stop_processes() {
    echo "Stopping processes..."
    if [ -n "$HARDHAT_PID" ]; then
        kill "$HARDHAT_PID" > /dev/null 2>&1
        echo "Hardhat node (PID $HARDHAT_PID) stopped."
    fi
    if [ -n "$DJANGO_PID" ]; then
        kill "$DJANGO_PID" > /dev/null 2>&1
        echo "Django server (PID $DJANGO_PID) stopped."
    fi
}

test_endpoint() {
    ENDPOINT=$1
    METHOD=$2
    DATA=$3
    AUTH_HEADER=$4
    DESCRIPTION=$5

    echo -e "\n--- $DESCRIPTION ($METHOD $ENDPOINT) ---"
    if [ -n "$DATA" ]; then
        if [ -n "$AUTH_HEADER" ]; then
            curl -s -X "$METHOD" -H "Content-Type: application/json" -H "$AUTH_HEADER" -d "$DATA" "http://127.0.0.1:$DJANGO_SERVER_PORT$ENDPOINT"
        else
            curl -s -X "$METHOD" -H "Content-Type: application/json" -d "$DATA" "http://127.0.0.1:$DJANGO_SERVER_PORT$ENDPOINT"
        fi
    else
        if [ -n "$AUTH_HEADER" ]; then
            curl -s -H "$AUTH_HEADER" "http://127.0.0.1:$DJANGO_SERVER_PORT$ENDPOINT"
        else
            curl -s "http://127.0.0.1:$DJANGO_SERVER_PORT$ENDPOINT"
        fi
    fi
    echo "" # Newline for cleaner output
}

# --- Main Script ---

# Trap to ensure processes are stopped on exit
trap stop_processes EXIT

# Start Hardhat node
start_hardhat_node

# Deploy contract
deploy_contract

# Update contract address in service file
update_contract_address_in_service

# Start Django server
start_django_server

# Register user and get token
register_and_login

# --- Token Distribution and Transfer ---

echo -e "\n--- Initial Token Balances ---"
test_endpoint "/api/contract/balance/?address=$OWNER_ADDRESS" "GET" "" "Authorization: Bearer $JWT_TOKEN" "Owner Balance"
test_endpoint "/api/contract/balance/?address=$ARTIST_ADDRESS" "GET" "" "Authorization: Bearer $JWT_TOKEN" "Artist Balance"
test_endpoint "/api/contract/balance/?address=$PLATFORM_ADDRESS" "GET" "" "Authorization: Bearer $JWT_TOKEN" "Platform Balance"

echo -e "\n--- Distributing Initial Tokens ---"
test_endpoint "/api/contract/distribuir/" "POST" "{}" "Authorization: Bearer $JWT_TOKEN" "Distribute Tokens"

echo -e "\n--- Balances After Distribution ---"
test_endpoint "/api/contract/balance/?address=$OWNER_ADDRESS" "GET" "" "Authorization: Bearer $JWT_TOKEN" "Owner Balance"
test_endpoint "/api/contract/balance/?address=$ARTIST_ADDRESS" "GET" "" "Authorization: Bearer $JWT_TOKEN" "Artist Balance"
test_endpoint "/api/contract/balance/?address=$PLATFORM_ADDRESS" "GET" "" "Authorization: Bearer $JWT_TOKEN" "Platform Balance"

echo -e "\n--- Certifying Ownership to 3 Clients ---"
test_endpoint "/api/contract/certificar/" "POST" '{"nuevo_propietario": "'$CLIENT_1_ADDRESS'", "cantidad": '$TOKEN_AMOUNT_PER_CLIENT'}' "Authorization: Bearer $JWT_TOKEN" "Certify Ownership to Client 1"
test_endpoint "/api/contract/certificar/" "POST" '{"nuevo_propietario": "'$CLIENT_2_ADDRESS'", "cantidad": '$TOKEN_AMOUNT_PER_CLIENT'}' "Authorization: Bearer $JWT_TOKEN" "Certify Ownership to Client 2"
test_endpoint "/api/contract/certificar/" "POST" '{"nuevo_propietario": "'$CLIENT_3_ADDRESS'", "cantidad": '$TOKEN_AMOUNT_PER_CLIENT'}' "Authorization: Bearer $JWT_TOKEN" "Certify Ownership to Client 3"

echo -e "\n--- Final Balances ---"
test_endpoint "/api/contract/balance/?address=$OWNER_ADDRESS" "GET" "" "Authorization: Bearer $JWT_TOKEN" "Owner Balance"
test_endpoint "/api/contract/balance/?address=$CLIENT_1_ADDRESS" "GET" "" "Authorization: Bearer $JWT_TOKEN" "Client 1 Balance"
test_endpoint "/api/contract/balance/?address=$CLIENT_2_ADDRESS" "GET" "" "Authorization: Bearer $JWT_TOKEN" "Client 2 Balance"
test_endpoint "/api/contract/balance/?address=$CLIENT_3_ADDRESS" "GET" "" "Authorization: Bearer $JWT_TOKEN" "Client 3 Balance"

echo -e "\n--- All operations completed. ---"