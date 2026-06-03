#!/bin/bash
# Registers the Debezium PostgreSQL connector with the Connect REST API.
# Run this once after docker-compose up.

CONNECT_URL="${DEBEZIUM_URL:-http://localhost:8083}"

echo "Waiting for Kafka Connect to be ready..."
until curl -sf "$CONNECT_URL/connectors" > /dev/null; do
  sleep 2
done

echo "Registering connector..."
curl -X POST "$CONNECT_URL/connectors" \
  -H "Content-Type: application/json" \
  -d @connector-config.json

echo ""
echo "Connector registered. Status:"
curl -sf "$CONNECT_URL/connectors/otto-postgres-connector/status" | python3 -m json.tool
