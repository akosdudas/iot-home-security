# Created by adapting iot/api-client/mqtt_example/cloudiot_mqtt_example.py
# in the https://github.com/GoogleCloudPlatform/python-docs-samples
# repository
# Commit id #1d4e988

# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from types import SimpleNamespace
import json
import datetime
import json
import ssl
import time
import logging
import random
import os
import jwt
from multiprocessing import Event, Queue
from queue import Empty as QueueEmpty

import paho.mqtt.client as mqtt

from raspberry_sec.system.util import ProcessReady, ProcessContext

class MQTTSession(ProcessReady):
    """
    Class for managing and MQTT connection
    """

    NAME = "MQTTSession"
    LOGGER = logging.getLogger('MQTTSession')
    MAXIMUM_BACKOFF_TIME = 32

    def __init__(self, config, private_key_file, ca_certs):
        """
        Constructor
        :param config: MQTT Session config
        :param private_key_file: RSA private key file of the device for creating a jwt
        :ca_certs: Google's cerfifications for creating a jwt
        """
        self.config = MQTTSession.parse_config(config)
        self.config.private_key_file = private_key_file
        self.config.ca_certs = ca_certs
        self.minimum_backoff_time = 1
        self.should_backoff = False
        self.jwt_iat = None
        self.client = None
        self.connected = False
        self.alert_queue = Queue()
        self.state_queue = Queue()
        self.command_queue = Queue()

    @staticmethod
    def parse_config(config_dict):
        config = SimpleNamespace(**config_dict)
        return config

    def get_name(self):
        return MQTTSession.NAME

    def on_connect(on_connect, unused_client, unused_userdata, unused_flags, rc):
        """Paho callback for when a device connects."""
        MQTTSession.LOGGER.debug('on_connect {}'.format(error_str(rc)))
        self.should_backoff = False
        self.minimum_backoff_time = 1
        self.connected = True
    
    def on_disconnect(self, unused_client, unused_userdata, rc):
        """Paho callback for when a device disconnects."""
        MQTTSession.LOGGER.debug('on_disconnect {}'.format(error_str(rc)))

        # Since a disconnect occurred, the next loop iteration will wait with
        # exponential backoff.
        self.should_backoff = True
        self.connected = False
    
    def on_publish(self, unused_client, unused_userdata, unused_mid):
        """Paho callback when a message is sent to the broker."""
        MQTTSession.LOGGER.debug('on_publish')


    def on_message(self, unused_client, unused_userdata, message):
        """Callback when the device receives a message on a subscription."""
        payload = str(message.payload)
        MQTTSession.LOGGER.debug('Received message \'{}\' on topic \'{}\' with Qos {}'.format(
                payload, message.topic, str(message.qos)))
        
        topic_name = message.topic.split('/')[-1]
        command = message.payload.decode('ascii')

        if topic_name == 'commands':
            self.command_queue.put(command, block=False)

    def publish_message(self, topic_name, payload, qos=0):
        """
        Publish an mqtt message to the topic specified with the specified qos value
        """
        device_topic = '/devices/{}/{}'.format(self.config.device_id, topic_name)
        MQTTSession.LOGGER.debug("Publishing to topic {}".format(device_topic))
        self.client.publish(device_topic, payload=payload, qos=qos)

    def get_client(self):
        """
        Tries to connect to the mqtt server with the credentials of the device
        """
        client_id = 'projects/{}/locations/{}/registries/{}/devices/{}'.format(
            self.config.project_id, self.config.cloud_region, 
            self.config.registry_id, self.config.device_id
        )

        MQTTSession.LOGGER.debug('Device client_id is \'{}\''.format(client_id))

        self.client = mqtt.Client(client_id=client_id)

        self.jwt_iat = datetime.datetime.utcnow()

        # With Google Cloud IoT Core, the username field is ignored, and the
        # password field is used to transmit a JWT to authorize the device.
        self.client.username_pw_set(
                username='unused',
                password=create_jwt(
                    self.config.project_id, 
                    self.config.private_key_file, 
                    self.config.algorithm,
                    self.config.jwt_expires_minutes
                )
        )

        # Enable SSL/TLS support.
        self.client.tls_set(
            ca_certs=self.config.ca_certs, 
            tls_version=ssl.PROTOCOL_TLSv1_2
        )

        # Register message callbacks. https://eclipse.org/paho/clients/python/docs/
        # describes additional callbacks that Paho supports. In this example, the
        # callbacks just print to standard out.
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        # Connect to the Google MQTT bridge.
        self.client.connect(self.config.mqtt_bridge_hostname, self.config.mqtt_bridge_port, keepalive=self.config.keep_alive_minutes*60)

        # The topic that the device will receive commands on.
        mqtt_command_topic = '/devices/{}/commands/#'.format(self.config.device_id)

        # Subscribe to the commands topic, QoS 1 enables message acknowledgement.
        MQTTSession.LOGGER.info('Subscribing to {}'.format(mqtt_command_topic))
        self.client.subscribe(mqtt_command_topic, qos=1)

    def run_client_loop(self):
        """
        Run the mqtt client loop to send and receive messages. Try to reconnect or
        refresh jwt if necessary.
        :return: False if the client should give up connecting, True otherwise
        """
        jwt_exp_mins = self.config.jwt_expires_minutes
        
        # Process network events.
        self.client.loop()

        # Wait if backoff is required.
        if self.should_backoff:
            # If backoff time is too large, give up.
            if self.minimum_backoff_time > MQTTSession.MAXIMUM_BACKOFF_TIME:
                MQTTSession.LOGGER.error('Exceeded maximum backoff time. Giving up.')
                return False

            # Otherwise, wait and connect again.
            delay = self.minimum_backoff_time + random.randint(0, 1000) / 1000.0
            MQTTSession.LOGGER.debug('Waiting for {} before reconnecting.'.format(delay))
            time.sleep(delay)
            self.minimum_backoff_time *= 2
            self.client.connect(self.config.mqtt_bridge_hostname, self.config.mqtt_bridge_port)


        seconds_since_issue = (datetime.datetime.utcnow() - self.jwt_iat).seconds
        if seconds_since_issue > 60 * jwt_exp_mins:
            MQTTSession.LOGGER.debug('Refreshing token after {}s').format(seconds_since_issue)
            self.get_client()

        return True

    def publish_alert(self):
        """
        Publish alert message
        """
        try:
            alert_message = self.alert_queue.get(block=False)
            MQTTSession.LOGGER.info("Publishing alert - {}".format(str(alert_message)[:80]))
            self.publish_message('events', str(alert_message), qos=1)
        except QueueEmpty as e:
            MQTTSession.LOGGER.info("Alert Queue empty - passing")
            pass

    def publish_state(self):
        """
        Publish device status
        """
        try:
            state_message = self.state_queue.get(block=False)
            MQTTSession.LOGGER.info("Publishing state - {}".format(str(state_message)[:80]))
            self.publish_message('state', str(state_message))
        except QueueEmpty as e:
            MQTTSession.LOGGER.info("State Queue empty - passing")
            pass


    def run(self, context: ProcessContext):
        MQTTSession.LOGGER.debug('Starting')
        stop_event = context.stop_event

        self.get_client()

        while not stop_event.is_set():
            MQTTSession.LOGGER.info('Start loop')
            if not self.run_client_loop(): 
                break
            self.publish_alert()
            self.publish_state()
            time.sleep(5)

        self.client.disconnect()
        self.client = None

def create_jwt(project_id, private_key_file, algorithm, expires_minutes):
    """Creates a JWT (https://jwt.io) to establish an MQTT connection.
        Args:
         project_id: The cloud project ID this device belongs to
         private_key_file: A path to a file containing either an RSA256 or
                 ES256 private key.
         algorithm: The encryption algorithm to use. Either 'RS256' or 'ES256'
        Returns:
            An MQTT generated from the given project_id and private key, which
            expires in 20 minutes. After 20 minutes, your client will be
            disconnected, and a new JWT will have to be generated.
        Raises:
            ValueError: If the private_key_file does not contain a known key.
        """

    token = {
            # The time that the token was issued at
            'iat': datetime.datetime.utcnow(),
            # The time the token expires.
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_minutes),
            # The audience field should always be set to the GCP project id.
            'aud': project_id
    }

    # Read the private key file.
    with open(private_key_file, 'r') as f:
        private_key = f.read()

    return jwt.encode(token, private_key, algorithm=algorithm)

def error_str(rc):
    """Convert a Paho error to a human readable string."""
    return '{}: {}'.format(rc, mqtt.error_string(rc))