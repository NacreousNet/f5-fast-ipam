#!/bin/bash
# Example: register this adapter in FAST as an external IPAM provider
# Adjust hostname/port, and use appropriate credentials for BIG-IP management
BIGIP="https://<bigip>"
FAST_USER="admin"
FAST_PASS="password"
PROVIDER_NAME="infoblox"
ENDPOINT="https://infoblox-adapter.local:8443/ipam"

curl -sku "$FAST_USER:$FAST_PASS" \
  -X POST "$BIGIP/mgmt/shared/fast/ipam/providers" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "'"${PROVIDER_NAME}"'",
    "providerType": "rest",
    "endpoint": "'"${ENDPOINT}"'"
  }'
