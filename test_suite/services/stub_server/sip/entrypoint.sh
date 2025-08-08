#!/bin/bash

set -e

if [ -z "$ROLE" ] || [ -z "$IP" ] || [ -z "$PORT" ]; then
  echo "ROLE, IP, and PORT must be set."
  exit 1
fi

SCENARIO_PATH=""
if [ "$ROLE" = "sender" ]; then
  if [ -z "$SCENARIO_FILE" ]; then
    echo "SCENARIO_FILE required for sender."
    exit 1
  fi
  SCENARIO_PATH="/app/scenarios/$SCENARIO_FILE"
  if [ ! -f "$SCENARIO_PATH" ]; then
    echo "Scenario file $SCENARIO_PATH not found."
    exit 1
  fi
fi

python sip_stub_server_service.py --role "$ROLE" --ip "$IP" --port "$PORT" --scenario "$SCENARIO_PATH"