import sys
import os
import logging
import time
import multiprocessing as mp
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from raspberry_sec.system.main import LogRuntime
from raspberry_sec.system.util import ProcessContext
from raspberry_sec.module.pushnotification.action import PushnotificationAction
from raspberry_sec.interface.action import ActionMessage
from raspberry_sec.mqtt.mqtt_session import MQTTSession
from raspberry_sec.mqtt.test_mqtt import get_config_dir


def set_parameters():
    parameters = dict()
    return parameters


def integration_test():
    mp.set_start_method('spawn')

    # Start logging process
    log_runtime = LogRuntime(level=logging.DEBUG)
    log_runtime.start()

    config_folder = get_config_dir()
    mqtt_session = MQTTSession(
        config_path=os.path.join(config_folder, 'gcp', 'mqtt.json'),
        private_key_file=os.path.join(config_folder, 'gcp', 'keys', 'rsa_private.pem'), 
        ca_certs=os.path.join(config_folder, 'gcp', 'keys', 'roots.pem')
    )

    stop_event = mp.Event()
    stop_event.clear()

    mqtt_context = ProcessContext(log_runtime.log_queue, stop_event)
    proc = ProcessContext.create_process(
        target=mqtt_session.start,
        name=mqtt_session.get_name(),
        args=(mqtt_context, )
    )

    proc.start()

    time.sleep(10)
    
    # Given
    push_notification_action = PushnotificationAction(set_parameters())

    # When
    push_notification_action.fire(
        [ActionMessage('Test push notification')], 
        alert_queue=mqtt_session.alert_queue
    )

    time.sleep(10)

    stop_event.set()
    log_runtime.stop()

if __name__ == '__main__':
    integration_test()
