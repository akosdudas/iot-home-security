#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
CONFIG_FILE="$SCRIPT_DIR/../../../config/gcp/mqtt.json"

PROJECT_ID=$(cat $CONFIG_FILE | jq -r .project_id)
CLOUD_REGION=$(cat $CONFIG_FILE | jq -r .cloud_region)
REGISTRY_ID=$(cat $CONFIG_FILE | jq -r .registry_id)

# Create pubsub topics - alerts and state
gcloud pubsub topics create alerts state

# Create registry
gcloud iot registries create $REGISTRY_ID \
    --project=$PROJECT_ID \
    --region=$CLOUD_REGION \
    --no-enable-http-config \
    --state-pubsub-topic=state \
    --event-notification-config=topic=alerts

