import logging
import time
import cv2

from raspberry_sec.interface.producer import Type
from raspberry_sec.interface.consumer import Consumer, ConsumerContext

from raspberry_sec.module.falldetector.detector.falldetector import FallDetector

class FalldetectorConsumer(Consumer):
    """
    Consumer class for detecting human falls in a video stream
    """

    LOGGER = logging.getLogger('FalldetectorConsumer')

    def __init__(self, parameters: dict):
        super().__init__(parameters)
        # ToDo
        self.initialized = False
        pass

    def get_name(self):
        return 'FalldetectorConsumer'

    def initialize(self):
        FalldetectorConsumer.LOGGER.info('Initializing component')
        
        self.fall_detector = FallDetector()
        self.initialized = True

    def run(self, context: ConsumerContext):
        if not self.initialized:
            self.initialize()

        img = context.data
        context.alert = False

        if img is not None:
            is_fall_detected = self.fall_detector.process_frame(img)
            if is_fall_detected:
                # TODO fire alert
                pass
            self.fall_detector.draw()
            cv2.imshow('frame', self.fall_detector.frame)
            cv2.imshow('mask', self.fall_detector.mask)
            cv2.waitKey(1)
        else:
            FalldetectorConsumer.LOGGER.warning('No image')
            time.sleep(self.parameters['timeout'])
        
        return context


    def get_type(self):
        return Type.CAMERA