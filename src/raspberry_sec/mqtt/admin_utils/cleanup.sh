#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

CONFIG_FILE="$SCRIPT_DIR/../../../config/gcp/mqtt.json"

PROJECT_ID=$(cat $CONFIG_FILE | jq -r .project_id)
CLOUD_REGION=$(cat $CONFIG_FILE | jq -r .cloud_region)
REGISTRY_ID=$(cat $CONFIG_FILE | jq -r .registry_id)
DEVICE_ID=$(cat $CONFIG_FILE | jq -r .device_id)

# Delete device
gcloud iot devices delete $DEVICE_ID \
    --project=$PROJECT_ID \
    --registry=$REGISTRY_ID \
    --region=$CLOUD_REGION

# Delete registry
gcloud iot registries delete $REGISTRY_ID \
    --project=$PROJECT_ID \
    --region=$CLOUD_REGION

# Delete pubsub topics
 gcloud pubsub topics delete alerts state