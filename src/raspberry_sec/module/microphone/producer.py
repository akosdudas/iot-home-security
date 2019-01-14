import logging
import speech_recognition as sr
from raspberry_sec.interface.producer import Producer, ProducerDataManager, ProducerDataProxy, Type
from raspberry_sec.system.util import ProcessContext


class MicrophoneProducerDataProxy(ProducerDataProxy):
	"""
	For storing shared microphone data
	"""
	pass


class MicrophoneProducer(Producer):
	"""
	Class for producing audio sample data
	"""
	LOGGER = logging.getLogger('MicrophoneProducer')

	def __init__(self, parameters: dict):
		"""
		Constructor
		:param parameters: see Producer constructor
		"""
		super().__init__(parameters)

	def register_shared_data_proxy(self):
		ProducerDataManager.register('MicrophoneProducerDataProxy', MicrophoneProducerDataProxy)

	def create_shared_data_proxy(self, manager: ProducerDataManager):
		return manager.MicrophoneProducerDataProxy()

	def run(self, context: ProcessContext):
		r = sr.Recognizer()

		with sr.Microphone() as source:
    			MicrophoneProducer.LOGGER.info('Microphone active')
    			audio = r.listen(source)	
		try:	
			if audio:
				data_proxy = context.get_prop('shared_data_proxy')
				data_proxy.set_data(audio)
				audio = None

		except sr.UnknownValueError:
			print("Google Speech Recognition could not understand audio")
		except sr.RequestError as e:
	    		print("Could not request results from Google Speech Recognition service; {0}".format(e))
					
	def get_data(self, data_proxy: ProducerDataProxy):
		MicrophoneProducer.LOGGER.debug('Producer called')
		return data_proxy.get_data()

	def get_name(self):
		"""
		:return: name of the component
		"""
		return 'MicrophoneProducer'

	def get_type(self):
		"""
		:return: Producer.Type of this component
		"""
		return Type.MICROPHONE
