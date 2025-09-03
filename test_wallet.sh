#!/bin/bash

# Check for jq
if ! command -v jq &> /dev/null
then
    echo "jq could not be found. Please install it to run this script."
    exit 1
fi

# --- Configuration ---
DJANGO_SERVER_PORT=8000
WALLET_ENDPOINT="/api/hardhat-wallet/" # Updated to match your final URL structure
JWT_TOKEN="" # This will be set dynamically

# --- Functions ---

# Function to stop the Django server if it's running
stop_processes() {
    if [ -n "$DJANGO_PID" ]; then
        kill "$DJANGO_PID" > /dev/null 2>&1
        echo "Django server (PID $DJANGO_PID) stopped."
    fi
}

# Function to start the Django server in the background
start_django_server() {
    echo "Starting Django server..."
    # Ensure you're running on the correct host and port
    python manage.py runserver 0:$DJANGO_SERVER_PORT > /dev/null 2>&1 &
    DJANGO_PID=$!
    echo "Django server started with PID: $DJANGO_PID"
    sleep 5 # Give it some time to start
}

# Function to register a user and get a JWT token
register_and_login() {
    echo "Registering a new user and getting JWT token..."
    # Generate a random username and password
    USERNAME="testuser_$(date +%s)"
    EMAIL="$USERNAME@example.com"
    PASSWORD="password123"

    # Register the user
    # Assumes the registration endpoint is correct
    REG_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d '{"email": "'$EMAIL'", "password": "'$PASSWORD'", "name": "Test User", "role": "buyer"}' "http://127.0.0.1:$DJANGO_SERVER_PORT/api/v1/auth/register/")
    
    # Extract the token from the response.
    # The JSON response is {"token": "...", "user": {...}}.
    # We use jq to get the value of the "token" key.
    JWT_TOKEN=$(echo "$REG_RESPONSE" | jq -r '.token')

    if [ -z "$JWT_TOKEN" ] || [ "$JWT_TOKEN" == "null" ]; then
        echo "Error: Could not get JWT token."
        echo "Response: $REG_RESPONSE"
        # Check for a specific error message from the API
        ERROR_DETAIL=$(echo "$REG_RESPONSE" | jq -r '.detail')
        if [ "$ERROR_DETAIL" != "null" ]; then
            echo "API Error Detail: $ERROR_DETAIL"
        fi
        exit 1
    fi
    echo "JWT token obtained: $JWT_TOKEN"
}
# Function to test the API endpoint






test_wallet_api() {
    AUTH_HEADER="Authorization: Bearer $JWT_TOKEN"
    ENDPOINT="http://127.0.0.1:$DJANGO_SERVER_PORT$WALLET_ENDPOINT"

    echo -e "\n--- Testing wallet generation API ($ENDPOINT) ---"
    
    if [ -z "$JWT_TOKEN" ]; then
        echo "Error: JWT_TOKEN is not set. Please run register_and_login first."
        exit 1
    fi

    # Using POST as it's a creation action
    # We add the Content-Type header to ensure Django receives the request correctly.
    # We also pass a JSON body, even if it's empty, to satisfy Django's parser.
    RESPONSE=$(curl -s -X POST -H "$AUTH_HEADER" -H "Content-Type: application/json" -d "{}" "$ENDPOINT")
    
    echo "Raw Response: $RESPONSE"
    echo ""
    
    # Check if the response is a valid JSON before parsing with jq
    if ! echo "$RESPONSE" | jq . > /dev/null 2>&1; then
        echo "Error: API did not return a valid JSON response."
        echo "Raw response was:"
        echo "$RESPONSE"
        exit 1
    fi
    
    # Check for errors in the response
    ERROR_DETAIL=$(echo "$RESPONSE" | jq -r .detail)
    if [ "$ERROR_DETAIL" != "null" ]; then
        echo "Error: API responded with an error."
        echo "Detail: $ERROR_DETAIL"
        exit 1
    fi

    # Extract wallet details from the JSON response
    WALLET_ADDRESS=$(echo "$RESPONSE" | jq -r .address)
    PRIVATE_KEY=$(echo "$RESPONSE" | jq -r .private_key)

    if [ -z "$WALLET_ADDRESS" ] || [ "$WALLET_ADDRESS" == "null" ]; then
        echo "Error: 'address' not found in response."
        exit 1
    fi

    echo "-------------------------------------"
    echo "Wallet Address: $WALLET_ADDRESS"
    echo "Private Key:    $PRIVATE_KEY"
    echo "-------------------------------------"
    echo "Wallet address successfully generated: $WALLET_ADDRESS"
}
# --- ... (resto del script) ... ---
# --- Main Script ---

# Ensure processes are stopped on exit
trap stop_processes EXIT

# Start Django server
start_django_server

# Register a user and get a token
register_and_login

# Test the wallet generation endpoint
test_wallet_api

echo -e "\n--- All operations completed. ---"