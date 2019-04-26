#!/bin/bash

env=""
config_file=""

while getopts "e:c:" opt; do
    case "$opt" in
    e)  env=$OPTARG
        ;;
    c)  config_file=$OPTARG
        ;;
    esac
done

if [ -z $env ] || [ -z $config_file ]
then
    echo "Usage: create_registry.sh -e <test|prod> -c <pca system config file>"
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

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

if [ $PROJECT_ID == "null" ] || [ $CLOUD_REGION == "null" ] || [ $REGISTRY_ID == "null" ]
then
    echo "Incorrect mqtt session config"
    exit 1
fi

# Create pubsub topics - alerts and state
gcloud pubsub topics create alerts state

# Create registry
gcloud iot registries create $REGISTRY_ID \
    --project=$PROJECT_ID \
    --region=$CLOUD_REGION \
    --no-enable-http-config \
    --state-pubsub-topic=state \
    --event-notification-config=topic=alerts

