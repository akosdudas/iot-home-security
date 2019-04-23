import logging
import time
from raspberry_sec.interface.action import Action


class DummyAction(Action):
	"""
	Action that does nothing on fire
    For testing purposes
	"""
	LOGGER = logging.getLogger('DummyAction')

	def __init__(self, parameters: dict):
		"""
		Constructor
		:param parameters: see Action constructor
		"""
		super().__init__(parameters)

	def get_name(self):
		return 'DummyAction'

	def fire(self, msg: list):
		DummyAction.LOGGER.info('Action fired')
		DummyAction.LOGGER.info('Action finished')
