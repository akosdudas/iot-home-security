import logging
import time
from raspberry_sec.interface.action import Action


class TestAction(Action):
	"""
	Action class for testing purposes
	"""
	LOGGER = logging.getLogger('TestAction')

	def __init__(self, parameters: dict):
		"""
		Constructor
		:param parameters: see Action constructor
		"""
		super().__init__(parameters)

	def get_name(self):
		return 'TestAction'

	def fire(self, msg: list, **kwargs):
		TestAction.LOGGER.info('Action fired: ' + '; '.join([m.data for m in msg]))
		time.sleep(5)
		TestAction.LOGGER.info('Action finished')
