import json
import base64
from multiprocessing import Event, Queue
from queue import Full as QueueFull
import cv2

from raspberry_sec.system.util import ProcessContext
from raspberry_sec.mqtt.mqtt_session import MQTTSession
from raspberry_sec.system.pca import PCASystem

class MQTTAlertMessage:
    def __init__(self, title, body):
        self.title = title
        self.body = body

    def __str__(self):
        data = {
            "title": self.title,
            "body": self.body
        }
        return json.dumps(data)

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class MQTTDevice(metaclass=Singleton):

    PRODUCERS_SUPPORTED = [
        'CameraProducer',
        'PirsensorProducer'
    ]

    def __init__(self):
        self.alert_queue = Queue(maxsize=2)
        self.state_queue = Queue(maxsize=1)
        self.stop_event = Event()
        self.session = None
        self.pca_system = None

    def configure_session(self, config_path, private_key_file, ca_certs):
        self.session = MQTTSession(
            config_path,
            private_key_file, 
            ca_certs,
            on_message_callback=on_message
        )

    def register_pca_system(self, pca_system: PCASystem):
        self.pca_system = pca_system

    def is_connected(self):
        if not self.session:
            return False
        return True

    def publish_alert(self, alert_message: MQTTAlertMessage):
        try:
            print('Publishing alert outside')
            self.alert_queue.put(alert_message, block=False)
        except QueueFull as e:
            print('Queue full')
            pass

    @staticmethod
    def encode_img_for_transport(img, quality=5):
        resized = cv2.resize(img, (640, 480))
        ret, jpeg = cv2.imencode(
            '.jpg',
            resized,
            (int(cv2.IMWRITE_JPEG_QUALITY), quality)
        )

        encoded_image = base64.b64encode(jpeg).decode('ascii')

        return encoded_image

    def publish_state(self):
        if not self.pca_system:
            print('No PCA System registered')
            return

        data = { }

        for p in self.pca_system.producer_set:
            if p.get_name() == 'CameraProducer':
                proxy = self.pca_system.prod_to_proxy[p]
                camera_image = proxy.get_data()
                if camera_image is None:
                    print('Camera image None')
                else:
                    data['camera_image'] = MQTTDevice.encode_img_for_transport(camera_image)
            
            elif p.get_name() == 'PirsensorProducer':
                proxy = self.pca_system.prod_to_proxy[p]
                motion_sensor_status = proxy.get_data()
                if motion_sensor_status is None:
                    print('Motion sensor status None')
                else:
                    data['motion_sensor_status'] = motion_sensor_status
            else:
                print('{} not supported'.format(p.get_name()))
                pass

        try:
            print('Publishing state outside')
            self.state_queue.put(json.dumps(data), block=False)
        except QueueFull as e:
            print('State queue full')
            pass

    def up(self, context: ProcessContext):
        if context.stop_event:
            self.stop_event = context.stop_event

        self.stop_event.clear()

        proc = ProcessContext.create_process(
            target=self.session.start,
            name='MQTTSession',
            args=(context, self.alert_queue, self.state_queue, )
        )
        
        proc.start()

    def down(self):
        self.stop_event.set()

def on_message(unused_client, unused_userdata, message):
    """Callback when the device receives a message on a subscription."""
    payload = str(message.payload)
    print('Received message \'{}\' on topic \'{}\' with Qos {}'.format(
            payload, message.topic, str(message.qos)))
    