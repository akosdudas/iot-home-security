import os
import base64
import json
import cv2
from raspberry_sec.mqtt.mqtt_session import MQTTSession

def encode_img_for_transport(img, quality=10):
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
