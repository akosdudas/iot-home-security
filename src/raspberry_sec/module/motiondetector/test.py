import cv2
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from raspberry_sec.module.motiondetector.consumer import MotiondetectorConsumer, ConsumerContext


def set_parameters():
	parameters = dict()
	parameters['area_threshold'] = 250
	parameters['dilate_iteration'] = 2
	parameters['resize_height'] = 360
	parameters['resize_width'] = 640
	parameters['threshold'] = 25
	parameters['threshold_max_val'] = 255
	return parameters


def integration_test():
	# Given
	consumer = MotiondetectorConsumer(set_parameters())
	context = ConsumerContext(None, False)
	cap = cv2.VideoCapture(0)

	# When
	try:
		count = 0
		while True:
			success, frame = cap.read()
			if success:
				context.data = frame
				consumer.run(context)
			if context.alert:
				print('Motion Detected: ' + str(count))
				count += 1
	finally:
		cap.release()
		cv2.destroyAllWindows()


if __name__ == '__main__':
	integration_test()
