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
        
        self.prev_timestamp = 0
        self.initialized = False
        

    def get_name(self):
        return 'FalldetectorConsumer'

    def initialize(self):
        FalldetectorConsumer.LOGGER.info('Initializing component')
        
        self.fall_detector = FallDetector(self.parameters)
        self.initialized = True

    def run(self, context: ConsumerContext):
        if not self.initialized:
            self.initialize()

        img = context.data
        timestamp = context.timestamp

        FalldetectorConsumer.LOGGER.debug(timestamp)

        # If no image or timestamp is sent, don't process
        if img is None or timestamp is None:
            FalldetectorConsumer.LOGGER.warning('Image or timestamp not received')
            time.sleep(self.parameters['timeout'])
            return context

        # Don't process the same frame twice
        if self.prev_timestamp == timestamp:
            FalldetectorConsumer.LOGGER.debug('Skipping frame')
            time.sleep(self.parameters['timeout'])
            return context

        # Process frame
        falls = self.fall_detector.process_frame(img, timestamp)
        if len(falls) > 0:
            context.alert = True
            context._alert_data = "Fall detected"
        
        self.prev_timestamp = timestamp

        return context


    def get_type(self):
        return Type.CAMERA