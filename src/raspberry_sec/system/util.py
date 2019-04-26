import importlib
import pkgutil
import logging
import os
from multiprocessing import Queue, Event, Process


class Loader:
	"""
	Base class for loading the common components
	"""
	def get_actions(self):
		"""
		:return list of Action classes
		"""
		pass

	def get_producers(self):
		"""
		:return list of Producer classes
		"""
		pass

	def get_consumers(self):
		"""
		:return list of Consumer classes
		"""
		pass


class DynamicLoader:
	"""
	Class for utility functionality
	"""
	LOGGER = logging.getLogger('DynamicLoader')

	@staticmethod
	def load_class(full_class_name: str):
		"""
		Loads a class dynamically
		:param full_class_name: e.g. xxx.yyy.Zzz
		:return: loaded class object
		"""
		class_name_parts = full_class_name.split('.')
		class_name = class_name_parts[-1]
		module_name = '.'.join(class_name_parts[:-1])

		_module = importlib.import_module(module_name)
		return getattr(_module, class_name)

	@staticmethod
	def list_modules(package_name: str):
		"""
		List modules in the package
		:param package_name: e.g. yyy.xxx
		:return: list of modules discovered
		"""
		package = importlib.import_module(package_name)
		modules = []
		for (path, name, is_package) in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
			if not is_package:
				modules.append(name)
		return modules


class ProcessContext:
	"""
	Container for tools that might be needed when running
	in a separate process.
	"""
	def __init__(self, log_queue: Queue, stop_event: Event, **kwargs):
		"""
		Constructor
		:param log_queue: queue for the new process to log into
		:param stop_event: Event object for being notified if needed
		:param other: anything else that might be needed (child specific data)
		"""
		self.logging_queue = log_queue
		self.stop_event = stop_event
		self.kwargs = kwargs

	def get_prop(self, name: str):
		"""
		Returns the property if exists among the key-word arguments
		:param name: name of the property
		:return: the property value
		"""
		return self.kwargs[name]

	@staticmethod
	def create_process(target, name, args):
		"""
		This method takes care of Process creation
		:param target: for the new process
		:param name: of the new process
		:param args: arguments
		:return: newly created Process
		"""
		return Process(
			target=target,
			name=name,
			args=args
		)


class ProcessReady:
	"""
	Base class for providing common interface for classes
	that are able to run on their own (in separate processes)
	"""
	@staticmethod
	def setup_logging(log_queue: Queue):
		handler = QueueHandler(log_queue)
		root = logging.getLogger()
		root.removeHandler(handler)
		root.addHandler(handler)
		root.setLevel(logging.DEBUG)

	def start(self, context: ProcessContext, *args):
		"""
		Common entry point for a new process
		:param context: containing the arguments when creating a new process
		"""
		ProcessReady.setup_logging(context.logging_queue)
		self.run(context, *args)

	def run(self, context: ProcessContext):
		"""
		Main functionality
		"""
		pass


class QueueHandler(logging.Handler):
	"""
	This is a logging handler which sends events to a multiprocessing queue.
	"""
	def __init__(self, queue: Queue):
		"""
		Constructor
		"""
		logging.Handler.__init__(self)
		self.queue = queue

	def emit(self, record):
		"""
		Writes the LogRecord into the queue.
		"""
		try:
			self.queue.put_nowait(record)
		except:
			self.handleError(record)

	def get_name(self):
		"""
		:return: name of the object
		"""
		return 'QueueHandler'

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


class LogQueueListener:
	"""
	Class representing a listener that should run in a separate process.
	This will listen to a queue (log-queue) and take care of the log records
	in a safe manner (inter-process communication).
	"""
	def __init__(self, _format: str, _level: int=logging.DEBUG):
		self.format = _format
		self.level = _level

	def run(self, context: ProcessContext):
		"""
		This method is a loop that listens for incoming records.
		:param context: log-record queue + stop event
		"""
		logging.basicConfig(format=self.format, level=self.level)
		logging_queue = context.logging_queue

		# Normal operation
		while True:
			try:
				record = logging_queue.get()
				if record is None:
					break
				logger = logging.getLogger(record.name)
				if logger.isEnabledFor(record.levelno):
					logger.handle(record)
			except:
				raise

def get_config_dir():
	current_dir = os.path.dirname(os.path.abspath(__file__))
	config_dir = os.path.abspath(os.path.join(current_dir, '..', '..', 'config'))
	return config_dir

def get_mqtt_keys_dir():
	keys_dir = os.path.abspath(os.path.join(get_config_dir(), 'gcp', 'keys'))
	return keys_dir