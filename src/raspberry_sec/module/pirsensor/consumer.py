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
        PirsensorConsumer.LOGGER.info('Consumer called')

        data = context.data

        if data is not None and data == MOTION_DETECTED:
            alert = True
            alert_data = "Motion detected"
        else:
            alert = False
            alert_data = ""

        time.sleep(self.parameters['timeout'])

        PirsensorConsumer.LOGGER.info('Done')
        return ConsumerContext(_data=data, _alert=alert, _alert_data=alert_data)
