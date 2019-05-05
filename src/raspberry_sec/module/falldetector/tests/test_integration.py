import cv2
import sys
import os
import time
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
from raspberry_sec.interface.consumer import ConsumerContext
from raspberry_sec.module.falldetector.consumer import FalldetectorConsumer


def get_parameters():
    current_folder = os.path.dirname(__file__)
    config_file = os.path.join(current_folder, 'test_parameters.json')

    with open(config_file) as f:
        config = json.load(f)
    return config


def integration_test():
    # Given
    parameters = get_parameters()
    consumer = FalldetectorConsumer(parameters)
    context = ConsumerContext(None, False)
    cap = cv2.VideoCapture(0)

    # When
    try:
        # Test with 24 fps
        while cv2.waitKey(40) == -1:
            success, frame = cap.read()
            if success:
                timestamp = time.time() * 1000
                context.data = frame
                context.timestamp = timestamp
                consumer.run(context)
            if context.alert:
                cv2.imshow('Frame', context.data)
                print('Detected: ' + str(context.alert_data))
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    integration_test()
