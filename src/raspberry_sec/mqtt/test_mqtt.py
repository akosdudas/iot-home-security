import sys, os, logging, time
import multiprocessing as mp

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from raspberry_sec.system.main import PCARuntime, LogRuntime
from raspberry_sec.system.util import ProcessReady, ProcessContext
from raspberry_sec.mqtt.mqtt_session import MQTTSession

def get_config_dir():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'config'))
    return config_dir

def test_integration():
    mp.set_start_method('spawn')

    # Start logging process
    log_runtime = LogRuntime(level=logging.DEBUG)
    log_runtime.start()

    # Load PCA System
    config_dir = get_config_dir()
    config_file = os.path.abspath(os.path.join(config_dir, 'test', 'mqtt_send_state_test.json'))
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

    if waiting_time > 0:
        time.sleep(waiting_time)
    else:
        input('Press a button to stop listening')

    stop_event.set()
    log_runtime.stop()

if __name__ == "__main__":
    test_integration()
