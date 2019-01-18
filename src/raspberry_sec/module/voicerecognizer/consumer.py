import logging
import time
import importlib
import speech_recognition as sr
import builtins
import json
from raspberry_sec.system.zonemanager import ZoneManager
from raspberry_sec.system.pca import PCASystem
from raspberry_sec.interface.producer import Type
from raspberry_sec.interface.consumer import Consumer, ConsumerContext


class VoicerecognizerConsumer(Consumer):
	"""
	Base class for consuming sample data

	"""
	LOGGER = logging.getLogger('VoicerecognizerConsumer')

	def __init__(self, parameters: dict):
		"""
		Constructor
		:param parameters: see Consumer constructor
		"""
		super().__init__(parameters)
		self.initialized = False
		self.zone_manager = None
		self.VoiceRecognizer = None

	def initialize(self):
		"""
		Initialize variables
		"""
		self.VoiceRecognizer = sr.Recognizer()
		self.zone_manager = ZoneManager()
		self.initialized = True

	def get_name(self):
		return 'VoicerecognizerConsumer'

	def run(self, context: ConsumerContext):
		if not self.initialized:
			self.initialize()

		audio = None
		audio = context.data
		context.alert = False
		zones = self.zone_manager.get_zones()

		if audio:
			try:
				voice_recognition = self.VoiceRecognizer.recognize_google(audio)
				VoicerecognizerConsumer.LOGGER.info('You said: ' + voice_recognition)

				#Search in the zone dictionary the word that the user said
				for key, value in zones.items():
					if key in voice_recognition:
						#search for the value in the word, whether on or off
						if 'off' in voice_recognition:
							if zones[key] == False:
								VoicerecognizerConsumer.LOGGER.info(key + ' is already inactive')
								break
							else:
								self.zone_manager.toggle_zone(key)
								break
						if 'on' in voice_recognition:
							if zones[key] == True:
								VoicerecognizerConsumer.LOGGER.info(key + ' is already active')
								break
							else:
								self.zone_manager.toggle_zone(key)
								break	
			except sr.UnknownValueError: 
				VoicerecognizerConsumer.LOGGER.info('Voicerecognizer could not understand audio')
			except sr.RequestError as e:
				print("Could not request results from Speech Recognition service; {0}".format(e))
		time.sleep(3)
		return context

	def get_type(self):
		return Type.MICROPHONE
