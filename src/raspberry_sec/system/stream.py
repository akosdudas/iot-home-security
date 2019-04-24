import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import groupby

from raspberry_sec.interface.action import ActionMessage
from raspberry_sec.interface.consumer import ConsumerContext
from raspberry_sec.system.util import ProcessContext, ProcessReady


class Stream(ProcessReady):
	"""
	Class for storing stream components.
	"""
	LOGGER = logging.getLogger('Stream')

	def __init__(self, _name: str):
		"""
		Constructor
		:param _name: uniquely identifies the Stream instance
		"""
		self.name = _name
		self.producer = None
		self.consumers = []

	def get_name(self):
		"""
		:return: the name of this stream
		"""
		return self.name

	def __eq__(self, other):
		"""
		Decides equality
		:param other: Stream instance
		:return: True or False
		"""
		return self.get_name() == other.get_name()

	def __hash__(self):
		"""
		:return: hash of the instance
		"""
		return hash(self.get_name())

	def validate(self):
		"""
		This method validates whether the stream is properly configured.
		Raises exception if not.
		:return True if it seems to be alright
		"""
		if self.producer is None:
			msg = 'No producer set for stream: ' + self.name
			Stream.LOGGER.error(msg)
			raise AttributeError(msg)

		prod_type = self.producer.get_type()
		for consumer in self.consumers:
			if consumer.get_type() is not prod_type:
				msg = 'Wrong consumer type in stream: ' + self.name
				Stream.LOGGER.error(msg)
				raise AttributeError(msg)

		return True

	def run(self, context: ProcessContext):
		"""
		This method runs the stream.
		:param context: Process context
		"""
		self.validate()

		# for inter-process communication
		data_proxy = context.get_prop('shared_data_proxy')
		sc_queue = context.get_prop('sc_queue')

		# stream main loop
		while True:
			try:
				Stream.LOGGER.debug(self.name + ' calling producer')
				data = self.producer.get_data(data_proxy)

				c_context = ConsumerContext(data, True)
				for consumer in self.consumers:
					if not c_context.alert:
						break
					Stream.LOGGER.debug(self.name + ' calling consumer: ' + consumer.get_name())
					c_context = consumer.run(c_context)

				if c_context.alert:
					Stream.LOGGER.debug(self.name + ' enqueueing controller message')
					sc_queue.put(StreamControllerMessage(
						_alert=c_context.alert,
						_msg=c_context.alert_data,
						_sender=self.name))
			except Exception as e:
				Stream.LOGGER.error('Something really bad happened: ' + e.__str__())


class StreamControllerMessage:
	"""
	Class for managing notifications in case of alerts.
	@see raspberry_sec.interface.action.Action
	"""
	def __init__(self, _alert: bool, _msg, _sender: str):
		"""
		Constructor
		:param _alert: True or False
		:param _msg: content of the alert
		:param _sender: name of the stream that sent this message
		"""
		self.alert = _alert
		self.msg = _msg
		self.sender = _sender


class StreamController(ProcessReady):
	"""
	Class for handling StreamControllerMessage-s
	"""
	LOGGER = logging.getLogger('StreamController')
	PLACEHOLDER_PATTERN = '@.*?@'

	def __init__(self):
		"""
		Constructor
		"""
		self.action = None
		self.query = 'False'
		self.polling_interval = 3
		self.message_limit = 100

	@staticmethod
	def evaluate_query(query: str):
		"""
		Evaluates the query and returns a logical value as a response
		:param query: logical expression
		:return: True or False
		"""
		try:
			StreamController.LOGGER.debug('Evaluating query: ' + query)
			return eval(query)
		except Exception:
			StreamController.LOGGER.error('Could not evaluate the query: ' + query)
			return False

	def decide_alert(self, messages: list):
		"""
		This method decides based on a list of messages
		whether to alert or not. For that it puts together a logical
		expression that it also evaluates afterwards.
		:param messages: list of StreamControllerMessage-s
		:return: decision (True/False) and list of ActionMessage-s
		"""
		query = self.query
		action_messages = []

		# iterating through every alert message
		for sender, msg_iter in groupby(messages, lambda m: m.sender):
			msg_list = list(msg_iter)
			StreamController.LOGGER.debug(sender + ' sent ' + str(len(msg_list)) + ' messages')

			sc_messages = [msg for msg in msg_list if msg.alert]
			if sc_messages:
				StreamController.LOGGER.debug(sender + ' reported ' + str(len(sc_messages)) + ' alerts')

				action_messages += [ActionMessage(scm.msg) for scm in sc_messages]
				query = query.replace('@' + sender.upper() + '@', 'True')
			else:
				query = query.replace('@' + sender.upper() + '@', 'False')

		# making sure no placeholder remains in query
		query = re.sub(pattern=StreamController.PLACEHOLDER_PATTERN, repl='False', string=query)

		return StreamController.evaluate_query(query), action_messages

	def run(self, context: ProcessContext):
		"""
		This method polls the queue for new messages
		and takes care of the action firing mechanism.
		:param context: Process context
		"""
		message_queue = context.get_prop('message_queue')
		alert_queue = context.get_prop('alert_queue')

		# iterate through messages in queue
		with ThreadPoolExecutor(max_workers=4) as executor:
			while True:
				StreamController.LOGGER.info('Checking message queue')
				messages = []
				count = 0

				# fetch messages
				while not message_queue.empty() and count <= self.message_limit:
					messages.append(message_queue.get(block=False))
					count += 1

				# process messages
				alert, action_messages = self.decide_alert(messages)

				# alert
				if alert:
					executor.submit(self.action.fire, action_messages, alert_queue=alert_queue)

				time.sleep(self.polling_interval)
