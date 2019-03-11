import logging
from raspberry_sec.interface.producer import Producer, ProducerDataManager, ProducerDataProxy, Type
from raspberry_sec.system.util import ProcessContext

import time
import RPi.GPIO as GPIO

class PirsensorProducerDataProxy(ProducerDataProxy):
    pass

class PirsensorProducer(Producer):
    NAME = "PirsensorProducer"
    LOGGER = logging.getLogger(NAME)

    def __init__(self, parameters: dict):
        super().__init__(parameters)

    def register_shared_data_proxy(self):
        ProducerDataManager.register('PirsensorProducerDataProxy', PirsensorProducerDataProxy)

    def create_shared_data_proxy(self, manager: ProducerDataManager):
        return manager.PirsensorProducerDataProxy()
    
    def __setup_hw(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.parameters['GPIO_PIN'],GPIO.IN)

    def __teardown_hw(self):
        GPIO.cleanup()

    def __capture_data(self):
        return GPIO.input(self.parameters['GPIO_PIR'])

    def run(self, context: ProcessContext):
        try:
            PirsensorProducer.LOGGER.info('Producer started')
            self.__setup_hw()
            data_proxy = context.get_prop('shared_data_proxy')

            while not context.stop_event.is_set():
                data = self.__capture_data()
                if data:
                    data_proxy.set_data(data)

                time.sleep(self.parameters['wait_interval'])
        finally:
            self.__teardown_hw()
            PirsensorProducer.LOGGER.info('Producer teardown')
    
    def get_data(self, data_proxy: ProducerDataProxy):
        PirsensorProducer.LOGGER.debug('Producer called')
        return data_proxy.get_data()

    def get_name(self):
        return PirsensorProducer.NAME
    
    def get_type(self):
        return Type.MOTION_DETECTOR

            