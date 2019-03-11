from enum import Enum
from multiprocessing.managers import BaseManager

from raspberry_sec.system.util import ProcessContext, ProcessReady


class Type(Enum):
	"""
	Producer types
	"""
	CAMERA = 1
	MOTION_DETECTOR = 2


class ProducerDataManager(BaseManager):
	"""
	For sharing data between different processes
	"""
	pass


class ProducerDataProxy(object):
	"""
	Data proxy for shared data
	"""
	def __init__(self):
		"""
		Constructor
		"""
		self.data = None

	def set_data(self, new):
		"""
		Sets shared data
		:param new: new data
		"""
		self.data = new

	def get_data(self):
		"""
		:return: shared data
		"""
		return self.data


class Producer(ProcessReady):
	"""
	Base class for producing sample data
	"""
	def __init__(self, parameters: dict = dict()):
		"""
		Constructor
		:param parameters: configurations coming from the JSON file
		"""
		self.parameters = parameters

	def register_shared_data_proxy(self):
		"""
		Registers shared data proxy for inter-process communication (with other Producer instances)
		"""
		pass

	def create_shared_data_proxy(self, manager: ProducerDataManager):
		"""
		This method should only be called once!
		:param manager: BaseManager child for inter-process data sharing
		:return: instance of shared data proxy
		"""
		pass

	def run(self, context: ProcessContext):
		"""
		Generates data for the other producers of the same class.
		This method finishes only in case of errors or if told explicitly.
		:param context: Process context
		"""
		pass

	def get_data(self, data_proxy: ProducerDataProxy):
		"""
		:param data_proxy: the producing Producer process stores the sample here
		:return: sample data
		"""
		pass

	def get_type(self):
		"""
		:return: Producer.Type
		"""
		pass

	def get_name(self):
		"""
		:return: name of the component
		"""
		pass

	def __eq__(self, other):
		"""
		:param other object
		:return: True or False depending on the name
		"""
		return self.get_name() == other.get_name()

	def __hash__(self):
		"""
		:return: hash code
		"""
		return hash(self.get_name())
