#!/bin/bash

echo "Starting Hardhat node..."
npx hardhat node > hardhat.log 2>&1 &
HARDHAT_PID=$!

echo "Starting Django development server..."
python manage.py runserver 0:8000> django.log 2>&1 &
DJANGO_PID=$!

echo "Hardhat node and Django server are starting in the background."
echo "Hardhat PID: $HARDHAT_PID"
echo "Django PID: $DJANGO_PID"
echo "Logs are being written to hardhat.log and django.log"

