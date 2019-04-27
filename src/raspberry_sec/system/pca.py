import os
import json
import logging
from json import JSONDecoder
from json import JSONEncoder
from multiprocessing import Queue
from queue import Full as QueueFull
from queue import Empty as QueueEmpty
from raspberry_sec.system.util import Loader, DynamicLoader, ProcessContext, ProcessReady, get_mqtt_keys_dir
from raspberry_sec.interface.action import Action
from raspberry_sec.interface.consumer import Consumer
from raspberry_sec.interface.producer import Producer, ProducerDataManager
from raspberry_sec.system.stream import StreamController, Stream
from raspberry_sec.mqtt.mqtt_session import MQTTSession
from raspberry_sec.mqtt.mqtt_utils import encode_img_for_transport

class PCASystem(ProcessReady):
	"""
	Class for hosting the components. Serves as a container/coordinator.
	"""
	LOGGER = logging.getLogger('PCASystem')
	TIMEOUT = 2
	POLLING_INTERVAL = 2

	def __init__(self):
		"""
		Constructor
		"""
		self.streams = set()
		self.producer_set = set()
		self.stream_processes = []
		self.prod_to_proc = {}
		self.prod_to_proxy = {}

		self.manager = None
		self.stream_controller = None
		self.sc_queue = None
		self.sc_process = None

		self.mqtt_session = None
		self.mqtt_command_queue = None
		self.mqtt_alert_queue = None
		self.mqtt_command_queue = None

	def validate(self):
		"""
		Validates the system by checking its components.
		Raises exception if something is wrong.
		:return True if the system seems to be good, False otherwise
		"""
		if not self.stream_controller:
			msg = 'StreamController was not set'
			PCASystem.LOGGER.error(msg)
			raise AttributeError(msg)

		if not self.streams:
			PCASystem.LOGGER.warning('There are no streams configured')
			return False

		if not self.mqtt_session:
			PCASystem.LOGGER.info('There is no MQTT connection configured')

		return True

	def run(self, context: ProcessContext):
		"""
		This method starts the components in separate processes
		and then waits for the stop event. It then terminates the processes if necessary.
		:param context: contains tools needed for 'running alone'
		"""
		# 1 - Validate the components
		self.validate()
		self.producer_set = set([s.producer for s in self.streams])
		self.sc_queue = Queue()

		# 2 - setup shared data manager
		self.setup_shared_manager()

		# 3 - start producer processes
		self.start_producer_processes(context)

		# 4 - start stream controller process
		self.start_stream_controller_process(context)

		# 5 - start stream processes
		self.start_stream_processes(context)

		# 6 - start mqtt session
		self.start_mqtt_session(context)

		# 7 - wait for the stop event and periodically check the producers
		self.wait_for_completion(context)

		PCASystem.LOGGER.info('Finished')

	def create_producer_process(self, context: ProcessContext, producer: Producer):
		"""
		Creates a new process for the Producer instance.
		:param context: holds the necessary objects for creating a new process
		:param producer: Producer instance
		:return: newly created process object
		"""
		proc_context = ProcessContext(
			stop_event=context.stop_event,
			log_queue=context.logging_queue,
			shared_data_proxy=self.prod_to_proxy[producer]
		)
		return ProcessContext.create_process(
			target=producer.start,
			name=producer.get_name(),
			args=(proc_context, )
		)

	def resurrect_producers(self, context: ProcessContext):
		"""
		Restarts processes that are not running.
		:param context: holds process related stuff
		"""
		PCASystem.LOGGER.debug('Checking producer processes')
		for prod, proc in self.prod_to_proc.items():
			if not proc.is_alive():
				PCASystem.LOGGER.info(prod.get_name() + ' process will be resurrected')
				new_proc = self.create_producer_process(context, prod)

				self.prod_to_proc[prod] = new_proc
				new_proc.start()

	def setup_shared_manager(self):
		"""
		Prepares the shared data manager for use and also constructs the proxies (for producers)
		"""
		PCASystem.LOGGER.info('Number of different producers: ' + str(len(self.producer_set)))
		for producer in self.producer_set:
			producer.register_shared_data_proxy()

		PCASystem.LOGGER.info('Starting ProducerDataManager')
		self.manager = ProducerDataManager()
		self.manager.start()

		PCASystem.LOGGER.debug('Creating shared data proxies')
		for producer in self.producer_set:
			self.prod_to_proxy[producer] = producer.create_shared_data_proxy(self.manager)

	def start_producer_processes(self, context: ProcessContext):
		"""
		Creates and starts the producer processes.
		:param context: holds 'stop event' and logging queue
		"""
		for producer in self.producer_set:
			proc = self.create_producer_process(context, producer)

			PCASystem.LOGGER.info('Starting producer: ' + producer.get_name())
			self.prod_to_proc[producer] = proc
			proc.start()

	def start_stream_controller_process(self, context: ProcessContext):
		"""
		Creates and fires up the stream controller process
		:param context: holds the 'stop event' and the logging queue
		"""
		try:
			alert_queue = self.mqtt_session.alert_queue
		except:
			alert_queue = None

		sc_context = ProcessContext(
			log_queue=context.logging_queue,
			stop_event=context.stop_event,
			message_queue=self.sc_queue,
			alert_queue=alert_queue
		)
		self.sc_process = ProcessContext.create_process(
			target=self.stream_controller.start,
			name='SC process',
			args=(sc_context, )
		)

		PCASystem.LOGGER.info('Starting stream-controller')
		self.sc_process.start()

	def start_stream_processes(self, context: ProcessContext):
		"""
		Creates the stream processes and fires them up.
		:param context: holds the 'stop event' and the loggign queue as well
		"""
		for stream in self.streams:
			s_context = ProcessContext(
				stop_event=context.stop_event,
				log_queue=context.logging_queue,
				shared_data_proxy=self.prod_to_proxy[stream.producer],
				sc_queue=self.sc_queue
			)
			proc = ProcessContext.create_process(
				target=stream.start,
				name=stream.get_name(),
				args=(s_context, )
			)
			self.stream_processes.append(proc)

			PCASystem.LOGGER.info('Starting stream: ' + stream.name)
			proc.start()

	def start_mqtt_session(self, context: ProcessContext):
		"""
		Creates the mqtt session and fires it up. 
		:param: context: holds the 'stop event' and the logging queue
		"""
		mqtt_context = ProcessContext(
			stop_event=context.stop_event,
			log_queue=context.logging_queue
		)
		proc = ProcessContext.create_process(
			target=self.mqtt_session.start,
			name=self.mqtt_session.get_name(),
			args=(mqtt_context, )
		)

		PCASystem.LOGGER.info('Starting MQTT Session')
		proc.start()

	def wait_for_completion(self, context: ProcessContext):
		"""
		Waits for the stop event to be set and then initiates the shutdown
		of the system. Producers, streams and the stream controller will be terminated.
		While the system is up and an mqtt session is configured for the system,
		peridically check and handle incoming mqtt messages.
		:param context: holds the 'event' object
		"""
		while not context.stop_event.is_set():
			context.stop_event.wait(timeout=PCASystem.POLLING_INTERVAL)
			self.resurrect_producers(context)
			if not self.mqtt_session is None:
				self.process_commands()

		PCASystem.LOGGER.info('Stop event arrived')

		stream_proc_count = str(len(self.stream_processes))
		PCASystem.LOGGER.info('Number of stream processes to be stopped: ' + stream_proc_count)
		for process in self.stream_processes:
			process.terminate()

		PCASystem.LOGGER.info('Stopping stream controller')
		self.sc_process.terminate()

		PCASystem.LOGGER.info('Waiting for producers')
		for prod, proc in self.prod_to_proc.items():
			proc.join()
	
	def publish_state(self):
		"""
		Publish the state of the PCASystem's producers via mqtt. Currently, producers of 
		type CAMERA and MOTION_DETECTOR are supported. The camera images are sent in jpg 
		format. 
		"""
		data = { }

		for p in self.producer_set:
			if p.get_name() == 'CameraProducer':
				proxy = self.prod_to_proxy[p]
				camera_image = proxy.get_data()
				if camera_image is None:
					PCASystem.LOGGER.warning('Camera Image is None')
				else:
					data['camera_image'] = encode_img_for_transport(camera_image)

			elif p.get_name() == 'PirsensorProducer':
				proxy = self.prod_to_proxy[p]
				motion_sensor_status = proxy.get_data()
				if motion_sensor_status is None:
					PCASystem.LOGGER.warning('Motion sensor status None')
				else:
					data['motion_sensor_status'] = motion_sensor_status
			else:
				PCASystem.LOGGER.error('{} not supported'.format(p.get_name()))
				pass

		try:
			PCASystem.LOGGER.info('Publishing state outside')
			self.mqtt_state_queue.put(json.dumps(data), block=False)
		except QueueFull as e:
			PCASystem.LOGGER.error('State queue full')
			pass
	
	def process_commands(self):
		"""
		Process the commands received via the mqtt session.
		If a status update command is received, publish the status of the device
		via mqtt.
		"""
		PCASystem.LOGGER.debug('Processing MQTT Commands')
		try:
			command = self.mqtt_command_queue.get(block=False)
			if command == 'status_update_request':
				PCASystem.LOGGER.info('Status update request received')
				self.publish_state()
		except QueueEmpty as e:
			PCASystem.LOGGER.debug('MQTT Command queue Empty')
			pass


class PCALoader(Loader):
	"""
	Implementation of Loader, that is capable of loading a PCASystem from the package system.
	"""
	LOGGER = logging.getLogger('PCALoader')
	module_package = 'raspberry_sec.module'
	allowed_modules = {'action', 'consumer', 'producer'}
	loaded_classes = {Action: {}, Consumer: {}, Producer: {}}

	@staticmethod
	def filter_for_allowed_modules(modules: list):
		"""
		This method filters the input based on preconfigured settings.
		Only Action, Producer, Consumer classes can be loaded from specific modules.
		:param modules: modules to be used by the system
		:return: filtered list
		"""
		filtered_modules = []
		for _module in modules:
			module_name = _module.split('.')[-1]
			if module_name in PCALoader.allowed_modules:
				filtered_modules.append(_module)

		PCALoader.LOGGER.debug('These modules were filtered out: ' + str(set(modules) - set(filtered_modules)))
		return filtered_modules

	@staticmethod
	def generate_class_names(modules: list):
		"""
		Based on predefined rules it generates class names to be loaded.
		E.g. xxx.yyy.test.consumer --> xxx.yyy.test.consumer.TestConsumer
		:param modules: list of modules
		:return: list of class names generated from the input
		"""
		class_names = []
		for _module in modules:
			_module_parts = _module.split('.')
			module_name = _module_parts[-1]
			package_name = _module_parts[-2]
			class_names.append('.'.join([_module, package_name.capitalize() + module_name.capitalize()]))
		return class_names

	def load(self):
		"""
		Loads and stores the newly loaded class objects
		"""
		modules = DynamicLoader.list_modules(PCALoader.module_package)
		modules = PCALoader.filter_for_allowed_modules(modules)
		classes = PCALoader.generate_class_names(modules)

		for _class in classes:
			try:
				loaded_class = DynamicLoader.load_class(_class)
				PCALoader.LOGGER.info('Loaded: ' + _class)
				for key in self.loaded_classes.keys():
					if issubclass(loaded_class, key):
						self.loaded_classes[key][loaded_class.__name__] = loaded_class
						break
			except ImportError:
				PCALoader.LOGGER.error(_class + ' - Cannot be imported')

	def get_actions(self):
		"""
		:return: Action class dictionary
		"""
		return self.loaded_classes[Action]

	def get_producers(self):
		"""
		:return: Producer class dictionary
		"""
		return self.loaded_classes[Producer]

	def get_consumers(self):
		"""
		:return: Consumer class dictionary
		"""
		return self.loaded_classes[Consumer]


class PCASystemJSONEncoder(JSONEncoder):
	"""
	Encodes objects to JSON
	"""
	LOGGER = logging.getLogger('PCASystemJSONEncoder')
	TYPE = '__type__'
	PARAMETERS = 'parameters'

	@staticmethod
	def save_config(pca_system: PCASystem, config_path: str):
		"""
		Using JSON serialization this method saves the system into a file
		:param pca_system: to be serialized
		:param config_path: file path to save it to
		"""
		if not config_path:
			config_path = 'config/pca_system.json'
			PCASystemJSONEncoder.LOGGER.info('Config-path was not set, defaults to ' + config_path)

		parsed = json.loads(json.dumps(pca_system, cls=PCASystemJSONEncoder))
		with open(config_path, 'w+') as configfile:
			json.dump(fp=configfile, obj=parsed, indent=4, sort_keys=True)

	@staticmethod
	def stream_to_dict(obj: Stream):
		"""
		:param obj: Stream object
		:return: dict version of the input
		"""
		obj_dict = dict()

		obj_dict['producer'] = dict()
		obj_dict['producer'][PCASystemJSONEncoder.TYPE] = type(obj.producer).__name__
		obj_dict['producer'][PCASystemJSONEncoder.PARAMETERS] = obj.producer.parameters

		obj_dict['consumers'] = list()
		for consumer in obj.consumers:
			c = dict()
			c[PCASystemJSONEncoder.TYPE] = type(consumer).__name__
			c[PCASystemJSONEncoder.PARAMETERS] = consumer.parameters
			obj_dict['consumers'].append(c)

		obj_dict['name'] = obj.name

		obj_dict[PCASystemJSONEncoder.TYPE] = Stream.__name__
		return obj_dict

	@staticmethod
	def pcasystem_to_dict(obj: PCASystem):
		"""
		:param obj: PCASystem object
		:return: dict version of the input
		"""
		obj_dict = dict()
		if  obj.mqtt_session is None:
			obj_dict['connect_mqtt'] = False
		else:
			obj_dict['connect_mqtt'] = True
			obj_dict['mqtt_session'] = obj.mqtt_session
		obj_dict['streams'] = list(obj.streams)
		obj_dict['stream_controller'] = obj.stream_controller
		obj_dict[PCASystemJSONEncoder.TYPE] = PCASystem.__name__
		return obj_dict

	@staticmethod
	def streamcontroller_to_dict(obj: StreamController):
		"""
		:param obj: StreamController object
		:return: dict version of the input
		"""
		obj_dict = dict()
		obj_dict['msg_limit'] = obj.message_limit
		obj_dict['polling_interval'] = obj.polling_interval
		obj_dict['query'] = obj.query
		obj_dict['action'] = dict()

		obj_dict['action'][PCASystemJSONEncoder.TYPE] = type(obj.action).__name__
		obj_dict['action'][PCASystemJSONEncoder.PARAMETERS] = obj.action.parameters

		obj_dict[PCASystemJSONEncoder.TYPE] = StreamController.__name__
		return obj_dict

	@staticmethod
	def mqtt_session_to_dict(obj: MQTTSession):
		"""
		:param obj: MQTTSession object
		:return: dict version of the output
		"""
		obj_dict = dict()
		obj_dict['session_config'] = obj.config.__dict__
		obj_dict.pop('private_key_file', None)
		obj_dict.pop('ca_certs', None)

		obj_dict[PCASystemJSONEncoder.TYPE] = MQTTSession.__name__
		return obj_dict

	def default(self, obj):
		"""
		:param obj: to be serialized
		:return: dictionary
		"""
		if isinstance(obj, Stream):
			return PCASystemJSONEncoder.stream_to_dict(obj)
		elif isinstance(obj, PCASystem):
			return PCASystemJSONEncoder.pcasystem_to_dict(obj)
		elif isinstance(obj, StreamController):
			return PCASystemJSONEncoder.streamcontroller_to_dict(obj)
		elif isinstance(obj, MQTTSession):
			return PCASystemJSONEncoder.mqtt_session_to_dict(obj)
		else:
			return json.JSONEncoder.default(self, obj)


class PCASystemJSONDecoder(JSONDecoder):
	"""
	Decodes JSON to objects
	"""
	LOGGER = logging.getLogger('PCASystemJSONDecoder')

	def __init__(self, *args, **kwargs):
		"""
		Constructor
		:param args:
		:param kwargs:
		"""
		pca_loader = PCALoader()
		pca_loader.load()
		self.loaded_producers = pca_loader.get_producers()
		self.loaded_consumers = pca_loader.get_consumers()
		self.loaded_actions = pca_loader.get_actions()

		json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

	@staticmethod
	def load_from_config(config_path: str):
		"""
		This method loads a PCASystem from a JSON file
		:param config_path: file path
		:return: read system object
		"""
		if config_path:
			with open(config_path, 'r') as configfile:
				return json.load(fp=configfile, cls=PCASystemJSONDecoder)
		else:
			PCASystemJSONDecoder.LOGGER.warning('Config-path was not given, returning empty system')
			return PCASystem()

	def stream_from_dict(self, obj_dict: dict):
		"""
		:param obj_dict: JSON structure
		:return: Stream object
		"""
		try:
			new_stream = Stream(_name=obj_dict['name'])

			producer_class_name = obj_dict['producer'][PCASystemJSONEncoder.TYPE]
			parameters_dict = obj_dict['producer'][PCASystemJSONEncoder.PARAMETERS]
			new_stream.producer = self.loaded_producers[producer_class_name](parameters_dict)

			new_stream.consumers = list()
			for consumer in obj_dict['consumers']:
				consumer_class_name = consumer[PCASystemJSONEncoder.TYPE]
				parameters_dict = consumer[PCASystemJSONEncoder.PARAMETERS]
				new_stream.consumers.append(self.loaded_consumers[consumer_class_name](parameters_dict))

			return new_stream
		except KeyError:
			PCASystemJSONDecoder.LOGGER.error('Cannot load Stream-s from JSON')
			raise

	def streamcontroller_from_dict(self, obj_dict: dict):
		"""
		:param obj_dict: JSON structure
		:return: StreamController object
		"""
		try:
			stream_controller = StreamController()
			stream_controller.query = obj_dict['query']
			stream_controller.msg_limit = int(obj_dict['msg_limit'])
			stream_controller.polling_interval = int(obj_dict['polling_interval'])

			action_class_name = obj_dict['action'][PCASystemJSONEncoder.TYPE]
			parameters_dict = obj_dict['action'][PCASystemJSONEncoder.PARAMETERS]

			stream_controller.action = self.loaded_actions[action_class_name](parameters_dict)
			return stream_controller
		except KeyError:
			PCASystemJSONDecoder.LOGGER.error('Cannot load StreamController from JSON')
			raise

	def mqtt_session_from_dict(self, obj_dict: dict):
		"""
		:param obj_dict: JSON structure
		:return: MQTTSession object
		"""
		try:
			keys_dir = get_mqtt_keys_dir()
			session_config = obj_dict["session_config"]
			return MQTTSession(
				config=session_config,
				private_key_file=os.path.join(keys_dir, 'rsa_private.pem'),
				ca_certs=os.path.join(keys_dir, 'roots.pem')
			)
		except KeyError:
			PCASystemJSONDecoder.LOGGER.error('Cannot load StreamController from JSON')
			raise

	def pcasystem_from_dict(self, obj_dict: dict):
		"""
		:param obj_dict: JSON structure
		:return: PCASystem object
		"""
		try:
			pca_system = PCASystem()
			pca_system.stream_controller = obj_dict['stream_controller']
			pca_system.streams = obj_dict['streams']
			try:
				if obj_dict['connect_mqtt'] == True:
					mqtt_session = obj_dict['mqtt_session']
					pca_system.mqtt_alert_queue = mqtt_session.alert_queue
					pca_system.mqtt_command_queue = mqtt_session.command_queue
					pca_system.mqtt_state_queue = mqtt_session.state_queue
					pca_system.mqtt_session = mqtt_session
			except:
				pass
			return pca_system
		except KeyError:
			PCASystemJSONDecoder.LOGGER.error('Cannot load PCASystem from JSON')
			raise

	def object_hook(self, obj_dict):
		"""
		:param obj_dict: JSON structure
		:return: object equivalent
		"""
		# Unfamiliar object
		if PCASystemJSONEncoder.TYPE not in obj_dict:
			return obj_dict
		# Stream object
		elif obj_dict[PCASystemJSONEncoder.TYPE] == Stream.__name__:
			return self.stream_from_dict(obj_dict)
		# PCASystem object
		elif obj_dict[PCASystemJSONEncoder.TYPE] == PCASystem.__name__:
			return self.pcasystem_from_dict(obj_dict)
		# StreamController object
		elif obj_dict[PCASystemJSONEncoder.TYPE] == StreamController.__name__:
			return self.streamcontroller_from_dict(obj_dict)
		# MQTTSession object
		elif obj_dict[PCASystemJSONEncoder.TYPE] == MQTTSession.__name__:
			return self.mqtt_session_from_dict(obj_dict)
		# Default
		else:
			return obj_dict
