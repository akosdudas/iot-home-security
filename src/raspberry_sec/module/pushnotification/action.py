import logging
import time
from raspberry_sec.interface.action import Action
from raspberry_sec.mqtt.mqtt_utils import MQTTAlertMessage


class PushnotificationAction(Action):
	"""
	Action for sending Push Notifications
	"""
	LOGGER = logging.getLogger('PushnotificationAction')

	def __init__(self, parameters: dict):
		"""
		Constructor
		:param parameters: see Action constructor
		"""
		super().__init__(parameters)

	def get_name(self):
		return 'PushnotificationAction'

	def fire(self, msg: list, **kwargs):
		PushnotificationAction.LOGGER.info('Action fired: ' + '; '.join([m.data for m in msg]))
		
		alert_queue = kwargs['alert_queue']

		if not alert_queue:
			PushnotificationAction.LOGGER.error('MQTT Session not connected - Cannot send Push Notification')
		else:
			message = MQTTAlertMessage(
				title="Alert",
				body=" ;".join([m.data for m in msg])
			)
			alert_queue.put(str(message), block=False)
		
		PushnotificationAction.LOGGER.info('Action finished')