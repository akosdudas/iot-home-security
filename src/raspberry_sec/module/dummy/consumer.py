import time
import logging
from raspberry_sec.interface.producer import Type
from raspberry_sec.interface.consumer import Consumer, ConsumerContext


class DummyConsumer(Consumer):
	"""
	Consumer class that does nothing with the data passed to it
    For testing purposes
    Can be configured to support CAMERA and PIRSENSOR type producers
	"""
	LOGGER = logging.getLogger('DummyConsumer')

	def __init__(self, parameters: dict):
		"""
		Constructor
		:param parameters: see Consumer constructor
		"""
		super().__init__(parameters)

	def get_name(self):
		return 'DummyConsumer'

	def run(self, context: ConsumerContext):
		DummyConsumer.LOGGER.info('Working...')
		if self.parameters['send_alert']:
			context.alert = True
			context.alert_data = 'Dummy alert'
		time.sleep(self.parameters['timeout'])
		DummyConsumer.LOGGER.info('Done...')
		return context

	def get_type(self):
		producer_type = self.parameters['producer_type']
		if producer_type == 'Camera':
			return Type.CAMERA
		elif producer_type == 'Pirsensor':
			return Type.MOTION_DETECTOR
		else:
			return Type.CAMERA
