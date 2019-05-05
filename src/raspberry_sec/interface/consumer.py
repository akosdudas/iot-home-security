class ConsumerContext:
	"""
	Class for storing data when transitioning between Consumer-s
	"""
	def __init__(self, _data, _alert: bool, _alert_data=None, _timestamp=None):
		"""
		Constructor
		:param _data: sample data the consumers work on
		:param _alert: True or False
		:param _alert_data: data to be reported in case of an alert
		:param _timestamp: the timestamp of the _data field
		"""
		self.data = _data
		self.alert = _alert
		self.alert_data = _alert_data
		self.timestamp = _timestamp


class Consumer:
	"""
	Base class for consuming sample data
	"""
	def __init__(self, parameters: dict = dict()):
		"""
		Constructor
		:param parameters: configurations coming from the JSON file
		"""
		self.parameters = parameters

	def get_name(self):
		"""
		:return: name of the component
		"""
		pass

	def run(self, context: ConsumerContext):
		"""
		:param context: contains session data
		:return: modified/new context
		"""
		pass

	def get_type(self):
		"""
		:return: Producer.Type
		"""
		pass

	def __eq__(self, other):
		"""
		:param other: other object
		:return: True or False depending on the name
		"""
		return self.get_name() == other.get_name()

	def __hash__(self):
		"""
		:return: hash code
		"""
		return hash(self.get_name())
