from types import SimpleNamespace
import json
import datetime
import json
import ssl
import time
import logging
import random
from multiprocessing import Event, Queue
from queue import Empty as QueueEmpty

import paho.mqtt.client as mqtt

from raspberry_sec.mqtt.mqtt_utils import create_jwt, error_str
from raspberry_sec.system.util import ProcessReady, ProcessContext

class MQTTSession(ProcessReady):
    LOGGER = logging.getLogger('MQTTSession')
    MAXIMUM_BACKOFF_TIME = 32
    
    def __init__(self, config_path, private_key_file, ca_certs, on_message_callback):
        self.config = MQTTSession.load_config(config_path)
        self.config.private_key_file = private_key_file
        self.config.ca_certs = ca_certs
        self.minimum_backoff_time = 1
        self.should_backoff = False
        self.on_message = on_message_callback
        self.jwt_iat = None
        self.client = None
        self.connected = False

    @staticmethod
    def load_config(config_path):
        config = None
        with open(config_path) as config_file:
            config = json.load(config_file, object_hook=lambda d: SimpleNamespace(**d))
        return config

    def on_connect(on_connect, unused_client, unused_userdata, unused_flags, rc):
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

    def publish_message(self, topic_name, payload, qos=0):
        device_topic = '/devices/{}/{}'.format(self.config.device_id, topic_name)
        MQTTSession.LOGGER.debug("Publishing to topic {}".format(device_topic))
        self.client.publish(device_topic, payload=payload, qos=qos)

    def get_client(self):
        
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
                    self.config.algorithm
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
        self.client.connect(self.config.mqtt_bridge_hostname, self.config.mqtt_bridge_port)

        # The topic that the device will receive commands on.
        mqtt_command_topic = '/devices/{}/commands/#'.format(self.config.device_id)

        # Subscribe to the commands topic, QoS 1 enables message acknowledgement.
        print('Subscribing to {}'.format(mqtt_command_topic))
        self.client.subscribe(mqtt_command_topic, qos=0)

    def run_client_loop(self):
        '''
            Returns false if the client should give up connecting
        '''
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

    def publish_alert(self, alert_queue: Queue):
        try:
            alert_message = alert_queue.get(block=False)
            MQTTSession.LOGGER.info("Publishing alert - {}".format(str(alert_message)[:80]))
            self.publish_message('events', str(alert_message))
        except QueueEmpty as e:
            MQTTSession.LOGGER.info("Alert Queue empty - passing")
            pass

    def publish_state(self, state_queue: Queue):
        try:
            state_message = state_queue.get(block=False)
            MQTTSession.LOGGER.info("Publishing state - {}".format(str(state_message)[:80]))
            self.publish_message('state', str(state_message))
        except QueueEmpty as e:
            MQTTSession.LOGGER.info("State Queue empty - passing")
            pass


    def run(self, context: ProcessContext, alert_queue: Queue, state_queue: Queue):
        MQTTSession.LOGGER.debug('Starting')
        stop_event = context.stop_event

        self.get_client()

        while not stop_event.is_set():
            MQTTSession.LOGGER.info('Start loop')
            if not self.run_client_loop(): 
                break
            self.publish_alert(alert_queue)
            self.publish_state(state_queue)
            time.sleep(5)

        self.client.disconnect()
        self.client = None
