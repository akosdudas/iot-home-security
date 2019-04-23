import sys, os, logging, time
import multiprocessing as mp

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from raspberry_sec.mqtt.mqtt_device import MQTTDevice, MQTTAlertMessage
from raspberry_sec.system.main import PCARuntime, LogRuntime
from raspberry_sec.system.util import ProcessReady, ProcessContext

def get_config_dir():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'config'))
    return config_dir

def configure_mqtt_session(config_folder):
    MQTTDevice().configure_session(
        config_path=os.path.join(config_folder, 'gcp', 'mqtt.json'),
        private_key_file=os.path.join(config_folder, 'gcp', 'keys', 'rsa_private.pem'), 
        ca_certs=os.path.join(config_folder, 'gcp', 'keys', 'roots.pem')
    )

def test_integration_with_pca_reference():
    mp.set_start_method('spawn')

    # Start logging process
    log_runtime = LogRuntime(level=logging.DEBUG)
    log_runtime.start()

    # Load PCA System
    config_dir = get_config_dir()
    config_file = os.path.abspath(os.path.join(config_dir, 'test', 'mqtt_send_state_test.json'))
    pca_runtime = PCARuntime(log_runtime.log_queue, PCARuntime.load_pca(config_file))

    # Configure MQTT device
    configure_mqtt_session(config_dir)
    MQTTDevice().register_pca_system(pca_runtime.pca_system)

    stop_event = mp.Event()
    stop_event.clear()

    # Start processes
    context = ProcessContext(log_runtime.log_queue, stop_event)
    MQTTDevice().up(context)
    pca_runtime.start()
    
    # Test functionality
    time.sleep(10)
    MQTTDevice().publish_state()
    time.sleep(10)

    # Stop processes
    pca_runtime.stop()
    MQTTDevice().down()
    log_runtime.stop()

def test_integration_with_no_pca_reference():
    mp.set_start_method('spawn')

    # Start logging process
    log_runtime = LogRuntime(level=logging.DEBUG)
    log_runtime.start()

    configure_mqtt_session()

    stop_event = mp.Event()
    stop_event.clear()

    context = ProcessContext(log_runtime.log_queue, stop_event)
    MQTTDevice().up(context)

    time.sleep(2)
    MQTTDevice().publish_alert(MQTTAlertMessage('Alert Title', 'Alert Body'))
    time.sleep(5)
    MQTTDevice().publish_state()
    time.sleep(10)

    MQTTDevice().down()
    log_runtime.stop()

if __name__ == "__main__":
    test_integration_with_pca_reference()
