import os
import base64
import json
import cv2
from raspberry_sec.mqtt.mqtt_session import MQTTSession

def get_mqtt_session():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'config'))
    mqtt_session = MQTTSession(
        config_path=os.path.join(config_dir, 'gcp', 'mqtt.json'),
        private_key_file=os.path.join(config_dir, 'gcp', 'keys', 'rsa_private.pem'), 
        ca_certs=os.path.join(config_dir, 'gcp', 'keys', 'roots.pem')
    )
    return mqtt_session

def encode_img_for_transport(img, quality=5):
    resized = cv2.resize(img, (640, 480))
    ret, jpeg = cv2.imencode(
        '.jpg',
        resized,
        (int(cv2.IMWRITE_JPEG_QUALITY), quality)
    )

    encoded_image = base64.b64encode(jpeg).decode('ascii')

    return encoded_image

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