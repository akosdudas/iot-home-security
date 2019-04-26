#!/bin/bash

env=""
config_file=""
register_device_url=""

while getopts "e:c:u:" opt; do
    case "$opt" in
    e)  env=$OPTARG
        ;;
    c)  config_file=$OPTARG
        ;;
    u)  register_device_url=$OPTARG
        ;;
    esac
done

if [ -z $env ] || [ -z $config_file ] || [ -z $register_device_url ]
then
    echo "Usage: register_device.sh -e <test|prod> -c <pca system config file> \ 
-u <register_device firebase endpoint URL>"
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

KEYS_FOLDER="$SCRIPT_DIR/../../../config/gcp/keys"
CONFIG_FILE="$SCRIPT_DIR/../../../config/$env/$config_file"

MQTT_SESSION_CONFIG=$(cat $CONFIG_FILE | jq -r .mqtt_session.session_config)

if [ "$(echo $MQTT_SESSION_CONFIG | tr -d '\n')" == "null" ]
then
    echo "Incorrect config. No mqtt session config specified"
    exit 1
fi

PROJECT_ID=$(echo $MQTT_SESSION_CONFIG | jq -r .project_id)
CLOUD_REGION=$(echo $MQTT_SESSION_CONFIG | jq -r .cloud_region)
REGISTRY_ID=$(echo $MQTT_SESSION_CONFIG | jq -r .registry_id)
DEVICE_ID=$(echo $MQTT_SESSION_CONFIG | jq -r .device_id)
VERIFICATION_CODE=$(echo $MQTT_SESSION_CONFIG | jq -r .verification_code)

if [ $PROJECT_ID == "null" ] || [ $CLOUD_REGION == "null" ] || [ $REGISTRY_ID == "null" ] || [ $DEVICE_ID == "null" ] || [ $VERIFICATION_CODE == "null" ]
then
    echo "Incorrect mqtt session config"
    exit 1
fi

# Functions
generate_keys() {
    output_folder="$0"
    openssl req -x509 -newkey rsa:2048 -days 3650 -keyout $KEYS_FOLDER/rsa_private.pem -nodes \
    -out $KEYS_FOLDER/rsa_cert.pem -subj "/CN=unused"
}

register_device_firebase() {
    response=$(curl --write-out %{http_code} --silent --output /dev/null --request POST --header "Content-Type: application/json" \
                --data '{ "device_id": "'$DEVICE_ID'", "verification_code": "'$VERIFICATION_CODE'", "registry": "'$REGISTRY_ID'" }' \
                $register_device_url)

    if [ $response == 201 ]
    then
        echo "Device registered to firebase"
    elif [ $response == 000 ]
    then
        echo "Error sending the request to the endpoint"
        exit 1
    elif [ $response == 409 ]
    then
        echo "Device with already exists with the id specified. Please choose a different id"
        exit 1
    else
        echo "Unexpected error. Please try again."
        exit 1
    fi

}

register_device_iot_core() {
    gcloud iot devices create $DEVICE_ID \
        --project=$PROJECT_ID \
        --region=$CLOUD_REGION \
        --registry=$REGISTRY_ID \
        --public-key path=$KEYS_FOLDER/rsa_cert.pem,type=rsa-x509-pem
}

main() {
    generate_keys "$KEYS_FOLDER"
    register_device_firebase
    register_device_iot_core
}

main
