#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
KEYS_FOLDER="$SCRIPT_DIR/../../../config/gcp/keys"

CONFIG_FILE="$SCRIPT_DIR/../../../config/gcp/mqtt.json"

PROJECT_ID=$(cat $CONFIG_FILE | jq -r .project_id)
CLOUD_REGION=$(cat $CONFIG_FILE | jq -r .cloud_region)
REGISTRY_ID=$(cat $CONFIG_FILE | jq -r .registry_id)
DEVICE_ID=$(cat $CONFIG_FILE | jq -r .device_id)

# Functions
generate_keys() {
    output_folder="$0"
    openssl req -x509 -newkey rsa:2048 -days 3650 -keyout $KEYS_FOLDER/rsa_private.pem -nodes \
    -out $KEYS_FOLDER/rsa_cert.pem -subj "/CN=unused"
}

register_device_firebase() {
    echo ""
}

register_device_iot_core() {
    gcloud iot devices create $DEVICE_ID \
        --project=$PROJECT_ID \
        --region=$CLOUD_REGION \
        --registry=$REGISTRY_ID \
        --public-key path=$KEYS_FOLDER/rsa_cert.pem,type=rsa-x509-pem
}

main() {
    mkdir "$KEYS_FOLDER" 2>/dev/null
    generate_keys "$KEYS_FOLDER"
    register_device_firebase
    register_device_iot_core
}

main