import logging
from raspberry_sec.interface.producer import Producer, ProducerDataManager, ProducerDataProxy, Type
from raspberry_sec.system.util import ProcessContext
from raspberry_sec.system.hw_util import is_gpio_floating, check_platform

import time

if check_platform():
    import RPi.GPIO as GPIO

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
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.parameters['GPIO_PIR'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def __teardown_hw(self):
        GPIO.cleanup()

    def __capture_data(self):
        return GPIO.input(self.parameters['GPIO_PIR'])

    def run(self, context: ProcessContext):
        try:
            PirsensorProducer.LOGGER.debug('Producer started')
            
            # Set up the HW for handling the motion sensor
            self.__setup_hw()

            # Get data proxy
            data_proxy = context.get_prop('shared_data_proxy')
            # Set initial data as None
            data_proxy.set_data(None)

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

            