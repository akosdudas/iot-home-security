import os, sys
import logging
import argparse
import cv2
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras.layers.advanced_activations import LeakyReLU
from keras.utils import to_categorical
from keras.optimizers import Adam
import keras.losses as loss
from sklearn.model_selection import train_test_split
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from raspberry_sec.module.facedetector.consumer import FacedetectorConsumer, ConsumerContext
from raspberry_sec.module.nnrecognizer.consumer import NnrecognizerConsumer


logging.basicConfig(format='%(asctime)s:%(name)s:%(levelname)s - %(message)s', level=logging.DEBUG)


class Context:
	"""
	Data/parameter context for the NN
	"""
	DATA_ROOT = 'resources/train'

	def __init__(self,
				img_size: int=128,
				test_split: float=0.25,
				model_path: str='resources/model.h5py',
				batch_size: int=1,
				epochs: int=10,
				lr: float=0.001,
				loss_func: str=loss.mean_squared_error):
		# Data
		self.train_data = None
		self.train_label = None
		self.test_data = None
		self.test_label = None
		self.num_of_classes = -1

		# Parameters
		self.img_size = img_size
		self.test_split = test_split
		self.model_path = model_path
		self.batch_size = batch_size
		self.epochs = epochs
		self.loss_func = loss_func
		self.lr = lr

	def load_data(self, dirs: list):
		"""
		Loads training/test data
		:param dirs: list of directories containing the classes (e.g. neg, pos)
		:return: newly created object
		"""
		self.num_of_classes = 0
		faces = list()
		classes = list()

		for dir in dirs:
			# Read from dir
			dir = os.sep.join([Context.DATA_ROOT, dir])
			img_list = [value for _, value in Context.get_images(dir).items()]
			label_list = [self.num_of_classes for _ in img_list]
			print('Class: ' + str(self.num_of_classes) + ' --> ' + str(dir))

			# Update
			self.num_of_classes += 1
			faces += img_list
			classes += label_list

		# NumPy + size + color conversion
		faces = [Context.convert_img(img, self.img_size) for img in faces]
		faces = np.asarray(faces)
		classes = np.asarray(classes)

		# Reshape -> convert -> normalize (0-1)
		faces = faces.reshape(-1, self.img_size, self.img_size, 1).astype('float64') / 255

		# Train/Test split
		(train_faces, test_faces, train_classes, test_classes) = train_test_split(
			faces, classes, test_size=self.test_split, random_state=561)

		# To one-hot
		self.test_label = to_categorical(test_classes)
		self.train_label = to_categorical(train_classes)
		self.test_data = test_faces
		self.train_data = train_faces

	def pre_process_data(self, detect=False, update=False):
		"""
		Does some pre-processing on the images
		(e.g. image resizing, color conversion, face detection)
		:param detect: should detect face
		:param update: should update images
		"""
		from raspberry_sec.module.facedetector.consumer import FacedetectorConsumer
		from raspberry_sec.interface.consumer import ConsumerContext
		detector_consumer = FacedetectorConsumer(Context.get_detector_parameters())
		context = ConsumerContext(None, False)

		images = Context.get_images(Context.DATA_ROOT)

		# Process and potentially save them
		try:
			counter = 0
			for path, image in images.items():
				# Detect face in image
				if detect:
					context.data = image
					detector_consumer.run(context)
					face = context.data
				else:
					face = image

				# If detection is off or face was successfully detected
				if not detect or (face is not None and context.alert):
					face = cv2.resize(face, (self.img_size, self.img_size))
					counter += 1
					# If face should be overridden
					if update:
						cv2.imwrite(path, face)
					# Show
					cv2.putText(face, str(counter), (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
					cv2.imshow('Size of training set', face)
					cv2.waitKey(50)
		except Exception as e:
			print('Error: ' + str(e))
		finally:
			cv2.destroyAllWindows()

	@staticmethod
	def convert_img(img: np.ndarray, size: int, color: int=cv2.COLOR_BGR2GRAY):
		"""
		Converts the image
		:param img: to be converted
		:param size: (X, X)
		:param color: color space code
		:return: image after conversion
		"""
		return cv2.resize(cv2.cvtColor(img, color), (size, size))

	@staticmethod
	def get_detector_parameters():
		parameters = dict()
		parameters['cascade_file'] = 'resources/haarcascade_frontalface_default.xml'
		parameters['min_neighbors'] = 5
		parameters['scale_factor'] = 1.3
		parameters['timeout'] = 1
		return parameters

	@staticmethod
	def get_recognizer_parameters():
		parameters = dict()
		parameters['model'] = 'resources/model.h5py'
		parameters['size'] = 128
		return parameters

	@staticmethod
	def get_images(dir: str):
		"""
		Reads and returns images from a directory (recursively)
		:param dir: directory path
		:return: dict of (path --> image) entries
		"""
		images = dict()
		for dir_name, dir_list, file_list in os.walk(dir):
			paths = [os.sep.join([dir_name, f]) for f in file_list if f.endswith('.png')]
			for path in paths:
				images[path] = cv2.imread(path)
		return images


class NeuralNetwork:
	"""
	Container
	"""
	def __init__(self, ctx: Context):
		"""
		Constructor
		:param ctx: contains the parameters as well as the training data
		"""
		self.model = None
		self.ctx = ctx

	def initialize(self):
		"""
		Builds the model and stores it
		"""
		num_classes = self.ctx.num_of_classes
		size = self.ctx.img_size
		m = Sequential()

		m.add(Conv2D(filters=128, kernel_size=(3, 3), activation='linear', padding='same', input_shape=(size, size, 1)))
		m.add(LeakyReLU(alpha=0.1))
		m.add(MaxPooling2D(pool_size=(2, 2), padding='same'))
		m.add(Dropout(rate=0.25))

		m.add(Conv2D(filters=256, kernel_size=(3, 3), activation='linear', padding='same'))
		m.add(LeakyReLU(alpha=0.1))
		m.add(MaxPooling2D(pool_size=(2, 2), padding='same'))
		m.add(Dropout(rate=0.25))

		m.add(Conv2D(filters=256, kernel_size=(3, 3), activation='linear', padding='same'))
		m.add(LeakyReLU(alpha=0.1))
		m.add(MaxPooling2D(pool_size=(2, 2), padding='same'))
		m.add(Dropout(rate=0.25))

		m.add(Flatten())
		m.add(Dense(units=128, activation='linear'))
		m.add(LeakyReLU(alpha=0.1))
		m.add(Dropout(rate=0.25))

		m.add(Dense(units=num_classes, activation='softmax'))

		# Compile
		m.compile(loss=self.ctx.loss_func, optimizer=Adam(self.ctx.lr), metrics=['accuracy'])
		m.summary()
		self.model = m

	def save(self):
		"""
		Saves the computed model into a file
		"""
		self.model.save(self.ctx.model_path)

	def train_model(self):
		"""
		Trains and tests the Neural Network
		"""
		batch_size = self.ctx.batch_size
		epochs = self.ctx.epochs

		self.model.fit(
			self.ctx.train_data,
			self.ctx.train_label,
			batch_size=batch_size,
			epochs=epochs,
			verbose=1,
			validation_data=(self.ctx.test_data, self.ctx.test_label))

		# Saves the model
		self.save()

	def evaluate_model(self):
		"""
		Evaluates the model
		"""
		# Test model
		test_eval = self.model.evaluate(self.ctx.test_data, self.ctx.test_label, batch_size=1, verbose=1)
		print('Test loss:', test_eval[0])
		print('Test accuracy:', test_eval[1])

		test_eval = self.model.evaluate(self.ctx.train_data, self.ctx.train_label, batch_size=1, verbose=1)
		print('Train loss:', test_eval[0])
		print('Train accuracy:', test_eval[1])


def test():
	# Given
	recognizer_consumer = NnrecognizerConsumer(Context.get_recognizer_parameters())
	detector_consumer = FacedetectorConsumer(Context.get_detector_parameters())
	context = ConsumerContext(None, False)
	cap = cv2.VideoCapture(0)

	# When
	try:
		while cv2.waitKey(50) == -1:
			success, frame = cap.read()
			# Detection
			if success:
				context.data = frame
				detector_consumer.run(context)
				face = context.data
			# Recognition
			if context.alert:
				context = recognizer_consumer.run(context)
				data = str(context.alert_data)
				cv2.putText(face, data, (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
				cv2.imshow('Testing recognition model', face)
	finally:
		cap.release()
		cv2.destroyAllWindows()


def train(detect: bool, update: bool):
	"""
	Pre-processing (input parameters) + NN training
	:param detect: if input images should undergo face-detection
	:param update: if the detected face should override the original image
	"""
	ctx = Context(
		img_size=128,
		batch_size=64,
		epochs=15,
		lr=0.00005,
		loss_func=loss.mean_absolute_error)
	ctx.pre_process_data(detect=detect, update=update)
	ctx.load_data(['neg', 'pos'])

	nn = NeuralNetwork(ctx)
	nn.initialize()
	nn.train_model()
	nn.evaluate_model()


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='== NN Face Recognizer (testing/training module) ==')
	parser.add_argument('-tr', '--training',
						help='If training should be conducted before testing',
						action='store_true')
	parser.add_argument('-d', '--detect',
						help='If the input should go under face-detection (only with -tr)',
						action='store_true')
	parser.add_argument('-u', '--update',
						help='If the input should be updated with the face that has been detected (only with -d)',
						action='store_true')
	args = parser.parse_args()

	# If training is enabled
	if args.training:
		train(args.detect, args.update)

	test()
