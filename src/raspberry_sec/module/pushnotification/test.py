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
from raspberry_sec.mqtt.mqtt_device import MQTTDevice
from raspberry_sec.mqtt.test_mqtt import configure_mqtt_session, get_config_dir


def set_parameters():
    parameters = dict()
    return parameters


def integration_test():
    mp.set_start_method('spawn')

    # Start logging process
    log_runtime = LogRuntime(level=logging.DEBUG)
    log_runtime.start()

    # Configure mqtt device
    configure_mqtt_session(get_config_dir())

    stop_event = mp.Event()
    stop_event.clear()

    # Start mqtt process
    context = ProcessContext(log_runtime.log_queue, stop_event)
    MQTTDevice().up(context)

    time.sleep(10)
    
    # Given
    push_notification_action = PushnotificationAction(set_parameters())

    # When
    push_notification_action.fire([
        ActionMessage('Test push notification')
    ])

    time.sleep(10)

    MQTTDevice().down()
    log_runtime.stop()

if __name__ == '__main__':
    integration_test()
