import sys, os, logging, time, json
import multiprocessing as mp

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from raspberry_sec.system.main import PCARuntime, LogRuntime
from raspberry_sec.system.util import ProcessReady, ProcessContext, get_config_dir, get_mqtt_keys_dir
from raspberry_sec.mqtt.mqtt_session import MQTTSession

def test_integration():
    mp.set_start_method('spawn')

    # Start logging process
    log_runtime = LogRuntime(level=logging.DEBUG)
    log_runtime.start()

    # Load PCA System
    config_dir = get_config_dir()
    config_file = os.path.abspath(os.path.join(config_dir, 'test', 'mqtt_integration_cam_test.json'))
    pca_runtime = PCARuntime(log_runtime.log_queue, PCARuntime.load_pca(config_file))

    pca_runtime.start()
    
    input('Press a button to stop listening')

    # Stop processes
    pca_runtime.stop()
    log_runtime.stop()


def test_mqtt_session(waiting_time=10):
    mp.set_start_method('spawn')

    # Start logging process
    log_runtime = LogRuntime(level=logging.DEBUG)
    log_runtime.start()

    config_folder = get_config_dir()
    config_file = os.path.join(config_folder, 'test', 'mqtt_session_test.json')
    with open(config_file) as f:
        config = json.load(f)

    mqtt_session = MQTTSession(
        config=config["mqtt_session"]["session_config"],
        private_key_file=os.path.join(get_mqtt_keys_dir(), 'rsa_private.pem'), 
        ca_certs=os.path.join(get_mqtt_keys_dir(), 'roots.pem')
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

    if waiting_time > 0:
        time.sleep(waiting_time)
    else:
        input('Press a button to stop listening')

    stop_event.set()
    log_runtime.stop()

if __name__ == "__main__":
    test_mqtt_session(waiting_time=0)
