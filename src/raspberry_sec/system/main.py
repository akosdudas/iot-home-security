import logging
import multiprocessing as mp
from multiprocessing import Event, Queue
from threading import Thread
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from raspberry_sec.system.pca import PCASystemJSONDecoder, PCASystem
from raspberry_sec.system.util import LogQueueListener, ProcessContext, ProcessReady


class PCARuntime:
	"""
	Container class for the environment
	"""
	def __init__(self, log_queue: Queue, pca_system: PCASystem):
		"""
		Constructor
		:param log_queue: loggin Queue
		:param pca_system: PCASystem instance
		"""
		self.log_queue = log_queue
		self.pca_system = pca_system
		self.pca_thread = None
		self.stop_event = None

	@staticmethod
	def load_pca(config_path: str):
		"""
		Loads the PCASystem using the given config file
		:param config_path: file
		:return: PCASystem object
		"""
		print(config_path)
		return PCASystemJSONDecoder.load_from_config(config_path)

	def start(self):
		"""
		Starts the components
		"""
		self.stop_event = Event()
		self.stop_event.clear()

		# PCA
		pca_context = ProcessContext(log_queue=self.log_queue, stop_event=self.stop_event)
		self.pca_thread = Thread(target=self.pca_system.run, name='PCA', args=(pca_context,))

		# START
		self.pca_thread.start()

	def stop(self):
		"""
		Stops the components
		"""
		# PCA
		self.stop_event.set()
		self.pca_thread.join()


class LogRuntime:
	"""
	Container class for the logging facility
	"""

	FORMAT = '[%(levelname)s]:[%(asctime)s]:[%(processName)s,%(threadName)s]:%(name)s - %(message)s'

	def __init__(self, level: int):
		"""
		Constructor
		:param level: logging level
		"""
		self.log_queue = Queue()
		self.process = None
		self.level = level

	def start(self):
		"""
		Creates and starts the logging process
		"""
		log_listener = LogQueueListener(_format=LogRuntime.FORMAT, _level=self.level)
		ctx = ProcessContext(log_queue=self.log_queue, stop_event=None)
		# Process
		self.process = ProcessContext.create_process(target=log_listener.run, name='LogListener', args=(ctx,))
		self.process.start()

	def stop(self):
		"""
		Stops the logging process
		"""
		self.log_queue.put(None)
		self.process.join()


def run_pcasystem(env: str, log_queue: Queue):
	"""
	Loads the PCASystem specified from the configuration and starts it
	:param env: test/prod
	:param log_queue: logging queue to use
	"""
	# PCA
	current_dir = os.path.dirname(os.path.abspath(__file__))
	config_file = os.path.abspath(os.path.join(current_dir, '../../config', env, 'pirsensor.json'))
	pca_runtime = PCARuntime(log_queue, PCARuntime.load_pca(config_file))
	pca_runtime.start()

	input('Please press enter to exit...')
	pca_runtime.stop()


if __name__ == '__main__':
	mp.set_start_method('spawn')

	# Start logging process
	log_runtime = LogRuntime(level=logging.INFO)
	log_runtime.start()

	# Setup logging for current process
	ProcessReady.setup_logging(log_runtime.log_queue)

	# PCA
	run_pcasystem('test', log_runtime.log_queue)

	# Stop logging process
	log_runtime.stop()
