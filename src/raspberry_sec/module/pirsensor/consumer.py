from raspberry_sec.interface.consumer import Consumer, ConsumerContext
from raspberry_sec.interface.producer import Type
from raspberry_sec.module.pirsensor.constants import NO_MOTION, MOTION_DETECTED

import logging
import time

class PirsensorConsumer(Consumer):
    NAME = 'PirsensorConsumer'
    LOGGER = logging.getLogger(NAME)

    def __init__(self, parameters: dict):
        super().__init__(parameters)

    def get_name(self):
        return PirsensorConsumer.NAME

    def get_type(self):
        return Type.MOTION_DETECTOR

    def run(self, context: ConsumerContext):
        PirsensorConsumer.LOGGER.debug('Consumer called')

        data = context.data
        context.alert = False

        if data is not None: 
            if data == MOTION_DETECTED:
                context.alert = True
                context.alert_data = "Motion detected"
        else:
            time.sleep(self.parameters['timeout'])

        PirsensorConsumer.LOGGER.debug('Done')
        return context
        
