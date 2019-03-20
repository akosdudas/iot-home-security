import logging
from raspberry_sec.interface.producer import Producer, ProducerDataManager, ProducerDataProxy, Type
from raspberry_sec.system.util import ProcessContext
from raspberry_sec.system.hw_util import is_gpio_floating, check_platform

from importlib import import_module

import time

class PirsensorProducerDataProxy(ProducerDataProxy):
    pass

class PirsensorProducer(Producer):
    NAME = "PirsensorProducer"
    LOGGER = logging.getLogger(NAME)

    def __init__(self, parameters: dict):
        super().__init__(parameters)

        # Check if the software is running on a raspberry pi
        if not check_platform():
            raise OSError("Not running on a Raspberry Pi. The libraries handling the PIR sensor can only be used on a Raspberry Pi.")
        self.gpio = import_module('RPi.GPIO')

    def register_shared_data_proxy(self):
        ProducerDataManager.register('PirsensorProducerDataProxy', PirsensorProducerDataProxy)

    def create_shared_data_proxy(self, manager: ProducerDataManager):
        return manager.PirsensorProducerDataProxy()
    
    def __test_hw(self):

        # Check if the PIR sensor is properly connected according to the configuration
        if is_gpio_floating(self.parameters["GPIO_PIR"]):
            raise IOError("The configured pin of the PIR motion sensor is floating")

    def __setup_hw(self):
        self.__test_hw()
        # Set pulldown for GPIO pin
        self.gpio.setmode(GPIO.BCM)
        self.gpio.setup(self.parameters['GPIO_PIR'], self.gpio.IN, pull_up_down=self.gpio.PUD_DOWN)

    def __teardown_hw(self):
        self.gpio.cleanup()

    def __capture_data(self):
        return self.gpio.input(self.parameters['GPIO_PIR'])

    def run(self, context: ProcessContext):
        try:
            PirsensorProducer.LOGGER.debug('Producer started')
            
            # Set initial data as None
            data_proxy.set_data(None)
            
            # Set up the HW for handling the motion sensor
            self.__setup_hw()

            # Get data proxy
            data_proxy = context.get_prop('shared_data_proxy')

            # Read motion status
            while not context.stop_event.is_set():
                data = self.__capture_data()
                if data is not None:
                    data_proxy.set_data(data)

                time.sleep(self.parameters['wait_interval'])
        finally:
            # Tear down HW accessing the motion sensor
            self.__teardown_hw()
            PirsensorProducer.LOGGER.debug('Producer teardown')
    
    def get_data(self, data_proxy: ProducerDataProxy):
        PirsensorProducer.LOGGER.debug('Producer called')
        return data_proxy.get_data()

    def get_name(self):
        return PirsensorProducer.NAME
    
    def get_type(self):
        return Type.MOTION_DETECTOR

            