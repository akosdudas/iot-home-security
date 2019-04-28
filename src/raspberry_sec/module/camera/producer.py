import logging
import cv2
import time
from raspberry_sec.interface.producer import Producer, ProducerDataManager, ProducerDataProxy, Type
from raspberry_sec.system.util import ProcessContext


class CameraProducerDataProxy(ProducerDataProxy):
	"""
	For storing shared camera data
	"""
	pass


class CameraProducer(Producer):
	"""
	Class for producing camera sample data
	"""
	LOGGER = logging.getLogger('CameraProducer')

	def __init__(self, parameters: dict):
		"""
		Constructor
		:param parameters: see Producer constructor
		"""
		super().__init__(parameters)

	def register_shared_data_proxy(self):
		ProducerDataManager.register('CameraProducerDataProxy', CameraProducerDataProxy)

	def create_shared_data_proxy(self, manager: ProducerDataManager):
		return manager.CameraProducerDataProxy()

	def run(self, context: ProcessContext):
		try:
			cam = cv2.VideoCapture(self.parameters['device'])
			if not cam.isOpened():
				CameraProducer.LOGGER.error('Cannot capture device: ' + str(self.parameters['device']))
				return

			unsuccessful_images = 0
			data_proxy = context.get_prop('shared_data_proxy')

			while not context.stop_event.is_set():
				ret_val, img = cam.read()
				if ret_val:
					# timestamp of the image in milliseconds
					timestamp = time.time() * 1000
					data_proxy.set_data((img, timestamp))
				else:
					unsuccessful_images += 1
					CameraProducer.LOGGER.warning('Could not capture image')
					# if too many errors happen we better kill this process
					if unsuccessful_images == self.parameters['unsuccessful_limit']:
						break

				cv2.waitKey(self.parameters['wait_key_interval'])
		finally:
			CameraProducer.LOGGER.debug('Stopping capturing images')
			cam.release()

	def get_data(self, data_proxy: ProducerDataProxy):
		CameraProducer.LOGGER.debug('Producer called')
		return data_proxy.get_data()[0]
	
	def get_timestamp(self, data_proxy: ProducerDataProxy):
		return data_proxy.get_data()[1]

	def get_name(self):
		"""
		:return: name of the component
		"""
		return 'CameraProducer'

	def get_type(self):
		"""
		:return: Producer.Type of this component
		"""
		return Type.CAMERA
